"""Childcare center suite part 2: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc2_lists import *
import cc2_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def RG(t, c): return '{range:%s.%s}' % (t, c)
ENR, SOON, LEFT = tok('cstatus', 'Enrolled'), tok('cstatus', 'Starting soon'), tok('cstatus', 'Left')
PRES, SICK, HOLI = tok('attstatus', 'Present'), tok('attstatus', 'Sick absence'), tok('attstatus', 'Family holiday')
ACTIVE = tok('holdstatus', 'Active')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
WD5 = [('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'), ('thu', 'Thursday'), ('fri', 'Friday')]
S5F = tok('schedule', '5 full days')


def PHONE_BY_ROOM(room_col, mp, default):
    """a constant phone number chosen by the room in a column (digits and plus signs only)"""
    f = '"%s"' % default
    for r in reversed(ROOMS): f = 'IF({col:%s}=%s,"%s",%s)' % (room_col, tok('room', r), mp[r], f)
    return f

settings = [
    S('company', 'Your center name', 'text', COMPANY), S('closing_time', 'Closing time, hours and minutes', 'text', CLOSING_TIME), S('late_grace_min', 'Grace minutes after closing before a late pickup fee', 'int', LATE_GRACE_MIN),
    S('late_fee_per_min', 'Late pickup fee per minute', 'money', LATE_FEE_PER_MIN), S('drop_in_surcharge', 'Drop-in day surcharge on the day rate', 'pct', DROP_IN_SURCHARGE),
    S('occupancy_target', 'Wanted occupancy, booked share of licensed places', 'pct', OCC_TARGET), S('notice_days', 'Days of notice a family gives before leaving', 'int', NOTICE_DAYS),
    S('moveup_infants', 'Age in months when a child leaves the Infants room', 'int', 15), S('moveup_toddlers', 'Age in months when a child leaves the Toddlers room', 'int', 27),
    S('moveup_twos', 'Age in months when a child leaves the Twos room', 'int', 39), S('moveup_preschool', 'Age in months when a child leaves the Preschool room', 'int', 60),
    S('lookahead_months', 'Months ahead to plan moving up', 'int', 6), S('drift_tolerance', 'Share booked and attended hours may differ', 'pct', 0.10),
    S('absence_alert_days', 'Absent days in a month that start a check-in with the family', 'int', 3), S('hold_warn_days', 'Days left on a place hold that count as ending soon', 'int', 5),
    S('closure_credit_pct', 'Share of a closure day credited, your rule', 'pct', 0.5), S('sheet_date', 'Day shown on the sign-in sheet', 'date', D.SHEET_DATE),
]
assert 3 <= len(settings) <= 20

tables = []

# 1 children
tables.append(T('children', 'Children', 'Children, rooms and schedules',
    'One row per child, current and past: room, schedule, status and dates, with age in months, weekly rate and the next closure filled in. Names and statuses only, never health detail.', [
    C('child_id', 'Child ID', 'text', 9, required=True), C('child', 'Child', 'text', 24), C('family', 'Family', 'text', 20), C('family_id', 'Family ID', 'text', 10), C('dob', 'Date of birth', 'date', 12),
    LST('room', 'Room', 'room', 12), LST('schedule', 'Schedule', 'schedule', 13), C('days', 'Days a week', 'int', 9), C('start_date', 'Start date', 'date', 12), C('end_date', 'End date', 'date', 12),
    LST('status', 'Status', 'cstatus', 13), LST('discount', 'Discount', 'discount', 10), C('notice_on', 'Notice given on', 'date', 12), C('guardian', 'Parent or guardian', 'text', 22), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26),
    CA('age_months', 'Age in months', 'int', 'IFERROR(DATEDIF({col:dob},{today},"M"),0)', 10),
    CA('weekly_rate', 'Weekly rate', 'money', 'SUMIFS(%s,%s,{col:room},%s,{col:schedule})' % (RG('rates', 'weekly_rate'), RG('rates', 'room'), RG('rates', 'schedule')), 11),
    CA('months_enrolled', 'Months enrolled', 'int', 'IFERROR(DATEDIF({col:start_date},IF({col:end_date}="",{today},{col:end_date}),"M"),0)', 11),
    CA('next_closure', 'Next closure day', 'date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<="&{today})+1),"")' % (RG('closures', 'date'), RG('closures', 'date')), 12),
    CA('closure_reason', 'Next closure reason', 'text', 'IF({col:next_closure}="","",IFERROR(INDEX(%s,MATCH({col:next_closure},%s,0))&"",""))' % (RG('closures', 'reason'), RG('closures', 'date')), 16),
    CA('closures_year', 'Closure days this year', 'int', 'COUNTIFS(%s,">="&DATE(YEAR({today}),1,1),%s,"<="&DATE(YEAR({today}),12,31))' % (RG('closures', 'date'), RG('closures', 'date')), 11)],
    D.children_d(), 150, [A('status', '= ' + SOON, 'warn'), A('status', '= ' + LEFT, 'bad'), A('status', '= ' + ENR, 'good')]))

# 2 bookings
tables.append(T('bookings', 'Bookings', 'Booked weekdays by child',
    'One row per child and booked weekday with the room, day type, hours and the date it starts; the child status, the day rate and the family phone fill in by themselves.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), C('child_id', 'Child ID', 'text', 9), REF('child', 'Child', 'children.child', 24), LST('room', 'Room', 'room', 12), LST('weekday', 'Weekday', 'wday', 11),
    LST('schedule', 'Schedule', 'schedule', 13), LST('day_type', 'Day type', 'daytype', 10), C('hours', 'Hours', 'num', 8), C('from_date', 'From date', 'date', 12),
    CA('child_status', 'Child status', 'text', LKT('children.status', 'children.child_id', 'child_id'), 13),
    CA('day_rate', 'Day rate', 'money', 'SUMIFS(%s,%s,{col:room},%s,{col:schedule})' % (RG('rates', 'day_rate'), RG('rates', 'room'), RG('rates', 'schedule')), 10),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child_id', 'child_id'), 18)],
    D.bookings_d(), 400, [A('child_status', '= ' + LEFT, 'bad'), A('child_status', '= ' + SOON, 'warn')]))

# 3 attendance
AT_COLS = [C('attendance_id', 'Attendance ID', 'text', 11, required=True), C('date', 'Date', 'date', 12), LST('weekday', 'Weekday', 'wday', 11), C('child_id', 'Child ID', 'text', 9), C('child', 'Child', 'text', 22),
           LST('room', 'Room', 'room', 12), LST('schedule', 'Schedule', 'schedule', 13), C('booked', 'Booked day', 'bool', 9), C('booked_hours', 'Booked hours', 'num', 9), LST('status', 'Status', 'attstatus', 14),
           C('sign_in', 'Sign in', 'time', 9), C('sign_out', 'Sign out', 'time', 9), C('extra_day', 'Drop-in day', 'bool', 9)]
tables.append(T('attendance', 'Attendance Log', 'Attendance log with sign-in and sign-out',
    'One row per child and day: type the sign-in and sign-out times; hours attended, minutes past closing and the absence flags fill in. Keep the recent weeks here; older months can stay as a sample.', AT_COLS + [
    CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('hours', 'Hours attended', 'num', 'IF({col:sign_out}="",0,ROUND(({col:sign_out}-{col:sign_in})*24,2))', 10),
    CA('late_minutes', 'Minutes past closing', 'int', 'IF({col:sign_out}="",0,MAX(0,ROUND(({col:sign_out}-VALUE({set:closing_time}))*1440,0)))', 11),
    CA('present_flag', 'Present', 'int', 'IF({col:status}=%s,1,0)' % PRES, 8), CA('absent_flag', 'Paid but absent', 'int', 'IF(AND({col:booked}=%s,{col:status}<>%s),1,0)' % (YES, PRES), 10),
    CA('sick_flag', 'Sick absence', 'int', 'IF({col:status}=%s,1,0)' % SICK, 8), CA('holiday_flag', 'Family holiday', 'int', 'IF({col:status}=%s,1,0)' % HOLI, 8)],
    D.attendance_d(), 3000, [A('late_minutes', '> {set:late_grace_min}', 'bad'), A('status', '= ' + SICK, 'warn'), A('status', '= ' + HOLI, 'warn')]))

# 4 rooms, 5 rates, 6 schedules
tables.append(T('rooms', 'Rooms', 'Rooms with licensed places and ratio',
    'One row per room: the licensed places and the ratio, the number of children each staff member may care for, check your local rules. Room is an age group, in a home daycare the one space you use.', [
    C('room', 'Room', 'text', 24, required=True), C('capacity', 'Licensed places', 'int', 11), C('ratio', 'Children per staff', 'int', 11)], D.rooms_d(), 50))
tables.append(T('rates', 'Rates', 'Tuition rates by room and schedule',
    'The rate card: the weekly rate this year and last year, days and hours a day, and the day rate used for drop-in days and closure credits.', [
    C('rate_id', 'Rate ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), LST('schedule', 'Schedule', 'schedule', 13), C('weekly_rate', 'Weekly rate', 'money', 12), C('days', 'Days', 'int', 7),
    C('hours_day', 'Hours a day', 'num', 9), C('day_rate', 'Day rate', 'money', 11), C('last_year_rate', 'Last year weekly rate', 'money', 12)], D.rates_d(), 60))
tables.append(T('schedules', 'Schedules', 'Schedules with days and hours',
    'The five schedules families can book, with the days a week and the hours a day; the hourly price and the weekly hours come from them.', [
    C('schedule', 'Schedule', 'text', 18, required=True), C('days', 'Days a week', 'int', 10), C('hours_day', 'Hours a day', 'num', 10)], D.schedules_d(), 50))

# 7 room-day occupancy
def HELD():
    f = '0'
    for k, w in reversed(WD5):
        f = 'IF({col:weekday}=%s,COUNTIFS(%s,{col:room},%s,%s,%s,%s),%s)' % (tok('wday', w), RG('holds', 'room'), RG('holds', k), YES, RG('holds', 'status'), ACTIVE, f)
    return f
tables.append(T('room_day', 'Room-Day Occupancy', 'Occupancy by room and weekday',
    'One row per room and weekday: licensed, booked, held and free places, the paid-but-absent share and the weekly revenue left unfilled, all calculated.', [
    C('rd_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), LST('weekday', 'Weekday', 'wday', 11), C('day_no', 'Day number', 'int', 9),
    CA('capacity', 'Licensed places', 'int', 'SUMIFS(%s,%s,{col:room})' % (RG('rooms', 'capacity'), RG('rooms', 'room')), 10),
    CA('booked_places', 'Booked places', 'int', 'COUNTIFS(%s,{col:room},%s,{col:weekday},%s,%s)' % (RG('bookings', 'room'), RG('bookings', 'weekday'), RG('bookings', 'child_status'), ENR), 10),
    CA('held_places', 'Places held', 'int', HELD(), 9), CA('occupancy', 'Occupancy', 'pct', 'IF({col:capacity}>0,{col:booked_places}/{col:capacity},0)', 10),
    CA('free_places', 'Free places', 'int', 'MAX(0,{col:capacity}-{col:booked_places}-{col:held_places})', 9),
    CA('absent_share', 'Paid but absent share', 'pct', 'IFERROR(SUMIFS(%s,%s,{col:room},%s,{col:weekday})/COUNTIFS(%s,{col:room},%s,{col:weekday},%s,%s),0)' % (
        RG('attendance', 'absent_flag'), RG('attendance', 'room'), RG('attendance', 'weekday'), RG('attendance', 'room'), RG('attendance', 'weekday'), RG('attendance', 'booked'), YES), 11),
    CA('day_rate', 'Day rate', 'money', 'SUMIFS(%s,%s,{col:room},%s,%s)' % (RG('rates', 'day_rate'), RG('rates', 'room'), RG('rates', 'schedule'), S5F), 10),
    CA('unfilled_revenue', 'Weekly revenue unfilled', 'money', '{col:free_places}*{col:day_rate}', 12),
    CA('rank_score', 'Rank score', 'num', '{col:unfilled_revenue}+MATCH({col:room},%s,0)/100+{col:day_no}/10000' % RG('rooms', 'room'), 10),
    CA('day_flag', 'Day check', 'text', 'IF({col:occupancy}>={set:occupancy_target}-0.05,%s,IF({col:occupancy}>={set:occupancy_target}-0.3,%s,%s))' % (fl('Busy day'), fl('Normal day'), fl('Quiet day')), 12),
    CA('attend_rate', 'Attendance rate', 'pct', 'IFERROR(SUMIFS(%s,%s,{col:room},%s,{col:weekday},%s,%s)/COUNTIFS(%s,{col:room},%s,{col:weekday},%s,%s),0)' % (
        RG('attendance', 'present_flag'), RG('attendance', 'room'), RG('attendance', 'weekday'), RG('attendance', 'booked'), YES, RG('attendance', 'room'), RG('attendance', 'weekday'), RG('attendance', 'booked'), YES), 10),
    CA('rate_key', 'Rate key', 'text', '{col:room}&"|"&ROUND({col:attend_rate},5)', 12),
    CA('room_low', 'Lowest rate of the room', 'pct', 'MIN(%s)' % ','.join('SUMIFS(%s,%s,{col:room},%s,%s)' % (RG('room_day', 'attend_rate'), RG('room_day', 'room'), RG('room_day', 'weekday'), tok('wday', w)) for _, w in WD5), 10),
    CA('room_high', 'Highest rate of the room', 'pct', 'MAX(%s)' % ','.join('SUMIFS(%s,%s,{col:room},%s,%s)' % (RG('room_day', 'attend_rate'), RG('room_day', 'room'), RG('room_day', 'weekday'), tok('wday', w)) for _, w in WD5), 10),
    CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18), CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18),
    CA('cook_phone', 'Cook phone', 'text', '"%s"' % D.COOK_PHONE, 18)],
    D.room_day_d(), 50, [A('day_flag', '= ' + fl('Quiet day'), 'warn'), A('day_flag', '= ' + fl('Busy day'), 'good'), A('free_places', '= 0', 'bad')]))

# 8 booked vs attended
tables.append(T('bva', 'Booked vs Attended', 'Booked hours against attended hours by child and week',
    'One row per child and week: type the booked and attended hours; the drift, the share, the money gap if billing used attended hours and the tolerance check fill in. Hours only, no reasons.', [
    C('bva_id', 'Row ID', 'text', 9, required=True), REF('child', 'Child', 'children.child', 24), C('week', 'Week (Monday)', 'date', 12), C('booked_hours', 'Booked hours', 'num', 9), C('attended_hours', 'Attended hours', 'num', 9),
    CA('room', 'Room', 'text', LKT('children.room', 'children.child', 'child'), 12), CA('schedule', 'Schedule', 'text', LKT('children.schedule', 'children.child', 'child'), 13),
    CA('hour_price', 'Price per hour', 'money', 'IFERROR(INDEX(%s,MATCH({col:child},%s,0))/(SUMIFS(%s,%s,{col:schedule})*SUMIFS(%s,%s,{col:schedule})),0)' % (
        RG('children', 'weekly_rate'), RG('children', 'child'), RG('schedules', 'days'), RG('schedules', 'schedule'), RG('schedules', 'hours_day'), RG('schedules', 'schedule')), 10),
    CA('drift', 'Drift in hours', 'num', '{col:attended_hours}-{col:booked_hours}', 9), CA('drift_pct', 'Drift share', 'pct', 'IF({col:booked_hours}>0,{col:drift}/{col:booked_hours},0)', 9),
    CA('money_gap', 'Money gap', 'money', '({col:booked_hours}-{col:attended_hours})*{col:hour_price}', 11),
    CA('drift_flag', 'Tolerance check', 'text', 'IF(ABS({col:drift_pct})>{set:drift_tolerance},%s,%s)' % (fl('Over tolerance'), fl('Within tolerance')), 14),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child', 'child'), 18)],
    D.bva_d(), 200, [A('drift_flag', '= ' + fl('Over tolerance'), 'warn'), A('drift_flag', '= ' + fl('Within tolerance'), 'good')]))

# 9 part-time requests
def FREE(day, room='room'): return 'SUMIFS(%s,%s,{col:%s},%s,%s)' % (RG('room_day', 'free_places'), RG('room_day', 'room'), room, RG('room_day', 'weekday'), tok('wday', day))
WANT = lambda k: '({col:%s}=%s)' % (k, YES)
SWAP = '""'
for k, w in reversed(WD5): SWAP = 'IF(AND({col:%s}<>%s,%s>=1),%s,%s)' % (k, YES, FREE(w), tok('wday', w), SWAP)
BLOCK = '+'.join('%s*(%s<1)' % (WANT(k), FREE(w)) for k, w in WD5)
tables.append(T('requests', 'Part-Time Requests', 'Part-time requests and whether the days fit',
    'One row per request for days: tick the days wanted; each day is checked against the free places of that room and weekday, and the verdict names a day swap when one day is full.', [
    C('request_id', 'Request ID', 'text', 10, required=True), C('family', 'Family contact', 'text', 24), C('phone', 'Phone', 'text', 18), LST('room', 'Room', 'room', 12)] +
    [C(k, w[:3], 'bool', 6) for k, w in WD5] + [LST('day_type', 'Day type', 'daytype', 10), C('start_date', 'Wanted start', 'date', 12), LST('status', 'Request status', 'reqstatus', 17),
    CA('days_wanted', 'Days wanted', 'int', '+'.join(WANT(k) for k, _ in WD5), 9), CA('days_blocked', 'Days with no free place', 'int', BLOCK, 11),
    CA('swap_day', 'Day to swap to', 'text', SWAP, 12),
    CA('fit', 'Fit verdict', 'text', 'IF({col:days_blocked}=0,%s,IF(AND({col:days_blocked}=1,{col:swap_day}<>""),%s,%s))' % (tok('fit', 'Accept'), tok('fit', 'Accept with a day swap'), tok('fit', 'Decline, keep on the list')), 20),
    CA('hours_day', 'Hours a day', 'num', 'IF({col:day_type}=%s,SUMIFS(%s,%s,%s),SUMIFS(%s,%s,%s))' % (tok('daytype', 'Half day'), RG('schedules', 'hours_day'), RG('schedules', 'schedule'), tok('schedule', '5 half days'), RG('schedules', 'hours_day'), RG('schedules', 'schedule'), S5F), 9),
    CA('weekly_rate', 'Weekly price', 'money', 'IF(SUMIFS(%s,%s,{col:room},%s,{col:days_wanted},%s,{col:hours_day})>0,SUMIFS(%s,%s,{col:room},%s,{col:days_wanted},%s,{col:hours_day}),{col:days_wanted}*IFERROR(AVERAGEIFS(%s,%s,{col:room},%s,{col:hours_day}),0))' % (
        RG('rates', 'weekly_rate'), RG('rates', 'room'), RG('rates', 'days'), RG('rates', 'hours_day'), RG('rates', 'weekly_rate'), RG('rates', 'room'), RG('rates', 'days'), RG('rates', 'hours_day'),
        RG('rates', 'day_rate'), RG('rates', 'room'), RG('rates', 'hours_day')), 12),
    CA('ad_phone', 'Assistant director phone', 'text', '"%s"' % D.AD_PHONE, 18)],
    D.requests_d(), 100, [A('fit', '= ' + tok('fit', 'Accept'), 'good'), A('fit', '= ' + tok('fit', 'Accept with a day swap'), 'warn'), A('fit', '= ' + tok('fit', 'Decline, keep on the list'), 'bad')]))
# (the weekly price formula carries its rate lookup twice: shortened below if it grows too long)

# 10 aging-up list
SCH = tok('room', 'School-age')
tables.append(T('aging_up', 'Aging-Up List', 'Aging-up list: who moves to the next room and when',
    'One row per enrolled child: type the child ID (and an agreed move date if any); the age, next room, move month and places free in the next room fill in.', [
    C('child_id', 'Child ID', 'text', 9, required=True), C('agreed_move', 'Agreed move date', 'date', 12),
    CA('child', 'Child', 'text', LKT('children.child', 'children.child_id', 'child_id'), 22), CA('room', 'Room', 'text', LKT('children.room', 'children.child_id', 'child_id'), 12),
    CA('dob', 'Date of birth', 'date', LKN('children.dob', 'children.child_id', 'child_id'), 12), CA('age_months', 'Age in months', 'int', 'IFERROR(DATEDIF({col:dob},{today},"M"),0)', 9),
    CA('next_room', 'Next room', 'text', 'IFERROR(IF({col:room}=%s,"",INDEX(%s,MATCH({col:room},%s,0)+1)&""),"")' % (SCH, RG('rooms', 'room'), RG('rooms', 'room')), 12),
    CA('move_age', 'Moving age in months', 'int', 'IF({col:next_room}="","",CHOOSE(MATCH({col:room},%s,0),{set:moveup_infants},{set:moveup_toddlers},{set:moveup_twos},{set:moveup_preschool}))' % RG('rooms', 'room'), 10),
    CA('months_to_move', 'Months to move', 'int', 'IF({col:move_age}="","",{col:move_age}-{col:age_months})', 9),
    CA('move_date', 'Move date', 'date', 'IF({col:move_age}="","",EDATE({col:dob},{col:move_age}))', 12),
    CA('move_month', 'Move month', 'date', 'IF({col:move_date}="","",DATE(YEAR({col:move_date}),MONTH({col:move_date}),1))', 11),
    CA('room_rank', 'Order in the room', 'int', 'IF({col:move_date}="","",COUNTIFS(%s,{col:room},%s,"<"&{col:move_date})+1)' % (RG('aging_up', 'room'), RG('aging_up', 'move_date')), 9),
    CA('next_free', 'Free places in the next room', 'int', 'IF({col:next_room}="","",SUMIFS(%s,%s,{col:next_room})-COUNTIFS(%s,{col:next_room},%s,%s))' % (RG('rooms', 'capacity'), RG('rooms', 'room'), RG('children', 'room'), RG('children', 'status'), ENR), 12),
    CA('move_flag', 'Move check', 'text', 'IF({col:next_room}="",%s,IF({col:months_to_move}<=0,%s,IF({col:months_to_move}<={set:lookahead_months},%s,%s)))' % (fl('No next room'), fl('Move now'), fl('Move within window'), fl('Move later')), 16),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child_id', 'child_id'), 18),
    CA('teacher_phone', 'Next room teacher phone', 'text', PHONE_BY_ROOM('next_room', D.TEACHER_PHONE, D.OWNER_PHONE), 18)],
    D.aging_up_d(), 100, [A('move_flag', '= ' + fl('Move now'), 'bad'), A('move_flag', '= ' + fl('Move within window'), 'warn'), A('next_free', '= 0', 'bad')]))

# 11 capacity next 6 months
def CUM(col, rm): return 'COUNTIFS(%s,{col:room},%s,"<="&EOMONTH({col:month},0))' % (RG('aging_up', rm), RG('aging_up', col))
LB = 'IF({col:month}<=%s,0,{col:month})' % MS
def PER(roomcol, datecol): return 'COUNTIFS(%s,{col:room},%s,">="&%s,%s,"<="&EOMONTH({col:month},0))' % (RG('aging_up', roomcol), RG('aging_up', datecol), LB, RG('aging_up', datecol))
STARTERS = 'COUNTIFS(%s,{col:room},%s,%s,%s,"<="&EOMONTH({col:month},0))' % (RG('children', 'room'), RG('children', 'status'), SOON, RG('children', 'start_date'))
LEAVING = 'COUNTIFS(%s,{col:room},%s,">"&{today},%s,"<="&EOMONTH({col:month},0))' % (RG('leavers', 'room'), RG('leavers', 'end_date'), RG('leavers', 'end_date'))
tables.append(T('capacity6', 'Capacity Next 6 Months', 'Room capacity for the next six months',
    'One row per room and month: children expected after moving up, starters and notices, against the licensed places; the free places and the month a room fills are calculated.', [
    C('cap_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), C('month', 'Month', 'date', 11),
    CA('capacity', 'Licensed places', 'int', 'SUMIFS(%s,%s,{col:room})' % (RG('rooms', 'capacity'), RG('rooms', 'room')), 10),
    CA('enrolled_now', 'Enrolled now', 'int', 'COUNTIFS(%s,{col:room},%s,%s)' % (RG('children', 'room'), RG('children', 'status'), ENR), 9),
    CA('moving_in', 'Moving in', 'int', PER('next_room', 'move_date'), 9), CA('moving_out', 'Moving out', 'int', PER('room', 'move_date'), 9),
    CA('starters', 'Starters', 'int', STARTERS, 9), CA('leaving', 'Leaving on notice', 'int', LEAVING, 10),
    CA('expected', 'Expected children', 'int', '{col:enrolled_now}+%s-%s+%s-%s' % (CUM('move_date', 'next_room'), CUM('move_date', 'room'), STARTERS, LEAVING), 10),
    CA('free_places', 'Free places', 'int', 'MAX(0,{col:capacity}-{col:expected})', 9), CA('over_by', 'Over by', 'int', 'MAX(0,{col:expected}-{col:capacity})', 8),
    CA('occupancy', 'Expected occupancy', 'pct', 'IF({col:capacity}>0,{col:expected}/{col:capacity},0)', 10), CA('out_flag', 'Room full', 'int', 'IF({col:expected}>={col:capacity},1,0)', 8),
    CA('cap_flag', 'Capacity check', 'text', 'IF({col:over_by}>0,%s,IF({col:out_flag}=1,%s,%s))' % (fl('Over capacity'), fl('Full'), fl('Has free places')), 15),
    CA('full_rank', 'Order of full months', 'int', 'IF({col:out_flag}=1,COUNTIFS(%s,{col:room},%s,"<"&{col:month},%s,1)+1,"")' % (RG('capacity6', 'room'), RG('capacity6', 'month'), RG('capacity6', 'out_flag')), 9),
    CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)],
    D.capacity6_d(), 80, [A('cap_flag', '= ' + fl('Over capacity'), 'bad'), A('cap_flag', '= ' + fl('Full'), 'warn'), A('cap_flag', '= ' + fl('Has free places'), 'good')]))

# 12 leavers and notices
tables.append(T('leavers', 'Leavers and Notices', 'Leavers and notices with days of notice',
    'One row per child who gave notice or left: notice date, last day and reason; the days of notice, the notice check against your rule and the first working day the place is free fill in.', [
    C('child_id', 'Child ID', 'text', 9, required=True), REF('child', 'Child', 'children.child', 24), C('family', 'Family', 'text', 20), LST('room', 'Room', 'room', 12), C('notice_on', 'Notice given on', 'date', 12),
    C('end_date', 'Last day', 'date', 12), LST('leave_reason', 'Reason', 'leavereason', 13),
    CA('days_notice', 'Days of notice', 'int', 'IF(OR({col:notice_on}="",{col:end_date}=""),"",{col:end_date}-{col:notice_on})', 9),
    CA('notice_flag', 'Notice check', 'text', 'IF({col:days_notice}="","",IF({col:days_notice}>={set:notice_days},%s,%s))' % (fl('Notice met'), fl('Short notice')), 13),
    CA('place_open', 'Place free from', 'date', 'IF({col:end_date}="","",WORKDAY({col:end_date},1))', 12)],
    D.leavers_d(), 100, [A('notice_flag', '= ' + fl('Short notice'), 'warn'), A('notice_flag', '= ' + fl('Notice met'), 'good')]))

# 13 place holds
tables.append(T('holds', 'Place Holds', 'Place holds with days and end date',
    'One row per held place: the family, room and days held, from and until dates and the status; days left and the ending-soon check fill in, and active holds take free places off the room days.', [
    C('hold_id', 'Hold ID', 'text', 9, required=True), C('family', 'Family contact', 'text', 24), C('phone', 'Phone', 'text', 18), LST('room', 'Room', 'room', 12)] + [C(k, w[:3], 'bool', 6) for k, w in WD5] + [
    C('hold_from', 'Hold from', 'date', 12), C('hold_until', 'Hold until', 'date', 12), LST('status', 'Status', 'holdstatus', 18),
    CA('days_left', 'Days left', 'int', 'IF({col:status}=%s,{col:hold_until}-{today},"")' % ACTIVE, 9),
    CA('hold_flag', 'Hold check', 'text', 'IF({col:status}<>%s,%s,IF({col:hold_until}-{today}<={set:hold_warn_days},%s,%s))' % (ACTIVE, fl('Hold ended'), fl('Hold ending soon'), fl('Hold active')), 15),
    CA('days_held', 'Days held a week', 'int', '+'.join(WANT(k) for k, _ in WD5), 9)],
    D.holds_d(), 60, [A('hold_flag', '= ' + fl('Hold ending soon'), 'warn'), A('hold_flag', '= ' + fl('Hold active'), 'good')]))

# 14 closures
tables.append(T('closures', 'Closures', 'Closure days with children affected',
    'One row per closed day: the date, weekday and reason; days to go, the children booked that day, the tuition at stake and the credit under your rule fill in.', [
    C('closure_id', 'Closure ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), LST('weekday', 'Weekday', 'wday', 11), LST('reason', 'Reason', 'closereason', 18),
    CA('days_to_go', 'Days to go', 'int', '{col:date}-{today}', 9), CA('when', 'When', 'text', 'IF({col:date}<{today},%s,%s)' % (fl('Past'), fl('Coming up')), 11),
    CA('children_affected', 'Children booked that day', 'int', 'COUNTIFS(%s,{col:weekday},%s,%s)' % (RG('bookings', 'weekday'), RG('bookings', 'child_status'), ENR), 11),
    CA('tuition_at_stake', 'Day tuition at stake', 'money', 'SUMIFS(%s,%s,{col:weekday},%s,%s)' % (RG('bookings', 'day_rate'), RG('bookings', 'weekday'), RG('bookings', 'child_status'), ENR), 12),
    CA('credit_value', 'Credit under your rule', 'money', '{col:tuition_at_stake}*{set:closure_credit_pct}', 12)],
    D.closures_d(), 60, [A('when', '= ' + fl('Coming up'), 'warn')]))

# 15 late pickups
tables.append(T('late_pickups', 'Late Pickups', 'Late pickups with fee and waiver',
    'One row per late pickup: type the minutes past closing and the fee; the fee the rule gives, the match check, the pickups of the last 30 days for that child and the family phone fill in.', [
    C('fee_id', 'Fee ID', 'text', 9, required=True), C('date', 'Date', 'date', 12), C('child_id', 'Child ID', 'text', 9), REF('child', 'Child', 'children.child', 24), LST('room', 'Room', 'room', 12),
    C('late_minutes', 'Minutes past closing', 'int', 10), C('fee', 'Fee', 'money', 10), C('waived', 'Waived', 'bool', 8), C('charged', 'Charged', 'money', 10),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child', 'child'), 18),
    CA('expected_fee', 'Fee by the rule', 'money', 'IF({col:late_minutes}>{set:late_grace_min},{col:late_minutes}*{set:late_fee_per_min},0)', 11),
    CA('fee_flag', 'Fee check', 'text', 'IF(ABS({col:fee}-{col:expected_fee})<0.01,%s,%s)' % (fl('Fee matches the rule'), fl('Fee differs')), 17),
    CA('late_30d', 'Late pickups in 30 days', 'int', 'COUNTIFS(%s,{col:child_id},%s,">"&({today}-30))' % (RG('late_pickups', 'child_id'), RG('late_pickups', 'date')), 11)],
    D.late_pickups_d(), 500, [A('fee_flag', '= ' + fl('Fee differs'), 'warn'), A('late_minutes', '> 20', 'bad')]))

# 16 sign-in sheet
def SIF(col, fmt_zero=True):
    s = 'SUMIFS(%s,%s,{set:sheet_date},%s,{col:child_id})' % (RG('attendance', col), RG('attendance', 'date'), RG('attendance', 'child_id'))
    return s
ROWS_N = 'COUNTIFS(%s,{set:sheet_date},%s,{col:child_id})' % (RG('attendance', 'date'), RG('attendance', 'child_id'))
tables.append(T('signin', 'Sign-in Sheet', 'Sign-in sheet for the day you choose',
    'One row per enrolled child: pick the day in the start settings; booked hours, sign in, sign out, hours, minutes past closing and the status of each child fill in from the attendance log.', [
    C('child_id', 'Child ID', 'text', 9, required=True),
    CA('child', 'Child', 'text', LKT('children.child', 'children.child_id', 'child_id'), 22), CA('room', 'Room', 'text', LKT('children.room', 'children.child_id', 'child_id'), 12),
    CA('booked_hours', 'Booked hours', 'num', SIF('booked_hours'), 9),
    CA('sign_in', 'Sign in', 'time', 'IF(%s=0,"",%s)' % (SIF('sign_in'), SIF('sign_in')), 9), CA('sign_out', 'Sign out', 'time', 'IF(%s=0,"",%s)' % (SIF('sign_out'), SIF('sign_out')), 9),
    CA('hours', 'Hours', 'num', SIF('hours'), 8), CA('late_minutes', 'Minutes past closing', 'int', SIF('late_minutes'), 10),
    CA('status', 'Status', 'text', 'IF(%s=0,%s,IF(%s>0,IF(%s=0,%s,%s),%s))' % (ROWS_N, fl('Not booked'), SIF('present_flag'), SIF('sign_out'), fl('Still signed in'), fl('Signed out'), fl('Absent')), 15),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child_id', 'child_id'), 18), CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)],
    D.signin_d(), 100, [A('status', '= ' + fl('Still signed in'), 'bad'), A('status', '= ' + fl('Absent'), 'warn'), A('late_minutes', '> 0', 'warn')]))

# 17 absences
tables.append(T('absences', 'Absences by Child', 'Absent days by child and month',
    'One row per child and month: type the absent days, the sick days among them and the booked days; the absent share and the check-in flag against your rule fill in. Counts only, no reasons.', [
    C('abs_id', 'Row ID', 'text', 9, required=True), REF('child', 'Child', 'children.child', 24), C('month', 'Month', 'date', 11), LST('room', 'Room', 'room', 12), C('days_absent', 'Days absent', 'int', 9),
    C('booked_days', 'Booked days', 'int', 9), C('sick_days', 'Sick absence days', 'int', 10),
    CA('share', 'Share of booked days', 'pct', 'IF({col:booked_days}>0,{col:days_absent}/{col:booked_days},0)', 10),
    CA('abs_flag', 'Check-in flag', 'text', 'IF({col:days_absent}>={set:absence_alert_days},%s,%s)' % (fl('Check in with the family'), fl('No concern')), 18),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child', 'child'), 18)],
    D.absences_d(), 200, [A('abs_flag', '= ' + fl('Check in with the family'), 'warn')]))

# 18 weekly hours by room
tables.append(T('weekly_hours', 'Weekly Hours by Room', 'Booked and attended hours by room and week',
    'One row per room and week: type the booked and attended hours; the difference, the attended share and the share of the room hours that were booked fill in.', [
    C('wh_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), C('week', 'Week (Monday)', 'date', 12), C('booked_hours', 'Booked hours', 'num', 10), C('attended_hours', 'Attended hours', 'num', 10),
    CA('difference', 'Difference', 'num', '{col:attended_hours}-{col:booked_hours}', 10), CA('attended_share', 'Attended share', 'pct', 'IF({col:booked_hours}>0,{col:attended_hours}/{col:booked_hours},0)', 10),
    CA('capacity_hours', 'Room hours a week', 'num', 'SUMIFS(%s,%s,{col:room})*SUMIFS(%s,%s,%s)*SUMIFS(%s,%s,%s)' % (RG('rooms', 'capacity'), RG('rooms', 'room'), RG('schedules', 'days'), RG('schedules', 'schedule'), S5F, RG('schedules', 'hours_day'), RG('schedules', 'schedule'), S5F), 11),
    CA('occupancy', 'Hours occupancy', 'pct', 'IF({col:capacity_hours}>0,{col:booked_hours}/{col:capacity_hours},0)', 10)],
    D.weekly_hours_d(), 120, []))

# 19 children by hour
tables.append(T('by_hour', 'Children by Hour', 'Children present by hour and room',
    'One row per room and hour: type the average children present at half past the hour; the share of licensed places, the staff needed at the ratio and the busiest hour of the day fill in.', [
    C('bh_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), LST('hour', 'Hour', 'hour', 9), C('avg_children', 'Average children', 'num', 10),
    CA('capacity', 'Licensed places', 'int', 'SUMIFS(%s,%s,{col:room})' % (RG('rooms', 'capacity'), RG('rooms', 'room')), 10),
    CA('share', 'Share of places', 'pct', 'IF({col:capacity}>0,{col:avg_children}/{col:capacity},0)', 10),
    CA('staff_needed', 'Staff needed at the ratio', 'int', 'IFERROR(ROUNDUP({col:avg_children}/SUMIFS(%s,%s,{col:room}),0),0)' % (RG('rooms', 'ratio'), RG('rooms', 'room')), 11),
    CA('hour_total', 'All rooms at this hour', 'num', 'SUMPRODUCT((%s={col:hour})*%s)' % (RG('by_hour', 'hour'), RG('by_hour', 'avg_children')), 11),
    CA('peak_key', 'Room peak key', 'text', 'IF({col:avg_children}=SUMPRODUCT(MAX((%s={col:room})*%s)),{col:room},"")' % (RG('by_hour', 'room'), RG('by_hour', 'avg_children')), 12),
    CA('pressure', 'Pressure check', 'text', 'IF({col:share}>=0.8,%s,%s)' % (fl('Above 80 percent'), fl('No concern')), 15),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('assistant_phone', 'Assistant phone', 'text', PHONE_BY_ROOM('room', D.ASSIST_PHONE, D.OWNER_PHONE), 18)],
    D.by_hour_d(), 100, [A('pressure', '= ' + fl('Above 80 percent'), 'warn')]))

# 20 drop-in days
tables.append(T('dropins', 'Drop-in Days', 'Drop-in days with surcharge and charge',
    'One row per drop-in day, an extra day booked at short notice at a surcharge: type the date, child and hours; the day rate, the surcharge and the charge fill in for the next invoice.', [
    C('dropin_id', 'Drop-in ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), REF('child', 'Child', 'children.child', 24), C('family', 'Family', 'text', 20), LST('room', 'Room', 'room', 12), C('hours', 'Hours', 'num', 8),
    CA('schedule', 'Booked schedule', 'text', LKT('children.schedule', 'children.child', 'child'), 13),
    CA('day_rate', 'Day rate', 'money', 'SUMIFS(%s,%s,{col:room},%s,{col:schedule})' % (RG('rates', 'day_rate'), RG('rates', 'room'), RG('rates', 'schedule')), 10),
    CA('surcharge', 'Surcharge', 'money', '{col:day_rate}*{set:drop_in_surcharge}', 10), CA('charge', 'Charge', 'money', '{col:day_rate}+{col:surcharge}', 10),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child', 'child'), 18), CA('ad_phone', 'Assistant director phone', 'text', '"%s"' % D.AD_PHONE, 18),
    CA('floater_phone', 'Floater phone', 'text', '"%s"' % D.FLOAT_PHONE, 18)],
    D.dropins_d(), 80, []))

assert len(tables) == 20, len(tables)
