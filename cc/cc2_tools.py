"""Childcare center suite part 2: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc2_lists import *
import cc2_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, default_label): return IN(k, label, 'list', key(lst, default_label), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def RG(t, c): return '{range:%s.%s}' % (t, c)
def RDV(col, room, day): return 'SUMIFS(%s,%s,%s,%s,%s)' % (RG('room_day', col), RG('room_day', 'room'), room, RG('room_day', 'weekday'), day)
def CAP(room): return 'SUMIFS(%s,%s,%s)' % (RG('rooms', 'capacity'), RG('rooms', 'room'), room)
def RAT(room): return 'SUMIFS(%s,%s,%s)' % (RG('rooms', 'ratio'), RG('rooms', 'room'), room)
def RT(x): return '=' + tok('room', x)
def WT(x): return '=' + tok('wday', x)
ENR = tok('cstatus', 'Enrolled')
DAYS = [('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'), ('thu', 'Thursday'), ('fri', 'Friday')]
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
S5F = tok('schedule', '5 full days')


def absent_default(room):
    return sum(1 for a in D.AT if a['room'] == room and a['booked'] and a['status'] != 'Present' and a['date'] > ago(30))

tools = []

# 1 occupancy by room and day
FR1 = RDV('free_places', '{in:room}', '{in:day}'); BK1 = RDV('booked_places', '{in:room}', '{in:day}'); HD1 = RDV('held_places', '{in:room}', '{in:day}')
tools.append(TOOL('occ_day', 'Occupancy by Room and Day', 'Occupancy by room and weekday with the revenue left unfilled',
    'Pick a room and weekday: see booked places, free places, the paid-but-absent share and the weekly revenue unfilled, the places to fill to reach your target and the emptiest room-day of the center.', [
    IL('room', 'Room', 'room', 'Twos'), IL('day', 'Weekday', 'wday', 'Monday'), I('target', 'Wanted occupancy', OCC_TARGET, 'pct')], [
    O('Licensed places', 'int', CAP('{in:room}')), O('Children booked that day', 'int', BK1), O('Places held for families', 'int', HD1), O('Occupancy', 'pct', 'IFERROR(%s/%s,0)' % (BK1, CAP('{in:room}'))),
    O('Free places', 'int', FR1), O('Paid but absent share', 'pct', RDV('absent_share', '{in:room}', '{in:day}')), O('Weekly revenue unfilled', 'money', RDV('unfilled_revenue', '{in:room}', '{in:day}')),
    O('Children to add to reach the target', 'int', 'MAX(0,ROUNDUP({in:target}*%s-%s,0))' % (CAP('{in:room}'), BK1)),
    O('Revenue a week if those places fill', 'money', 'MIN(%s,MAX(0,ROUNDUP({in:target}*%s-%s,0)))*%s' % (FR1, CAP('{in:room}'), BK1, RDV('day_rate', '{in:room}', '{in:day}'))),
    O('Rank of this room-day by revenue unfilled, 1 is the emptiest', 'int', '1+COUNTIFS(%s,">"&%s)' % (RG('room_day', 'rank_score'), RDV('rank_score', '{in:room}', '{in:day}'))),
    O('Emptiest room-day of the center', 'text', 'INDEX(%s,MATCH(LARGE(%s,1),%s,0))&" "&INDEX(%s,MATCH(LARGE(%s,1),%s,0))' % (RG('room_day', 'room'), RG('room_day', 'rank_score'), RG('room_day', 'rank_score'), RG('room_day', 'weekday'), RG('room_day', 'rank_score'), RG('room_day', 'rank_score'))),
    O('Its weekly revenue unfilled', 'money', 'MAX(%s)' % RG('room_day', 'unfilled_revenue')),
    O('Verdict', 'text', 'IF(AND(%s>=2,IFERROR(%s/%s,0)<{in:target}),%s,%s)' % (FR1, BK1, CAP('{in:room}'), vd('Market this day'), vd('Day is fine')))],
    GR('What if', ('Infants on Monday', {'room': RT('Infants'), 'day': WT('Monday')}), ('Toddlers on Friday', {'room': RT('Toddlers'), 'day': WT('Friday')}), ('Preschool on Monday', {'room': RT('Preschool'), 'day': WT('Monday')}),
       ('School-age on Wednesday', {'room': RT('School-age'), 'day': WT('Wednesday')}), ('Target 70 percent', {'target': 0.7}))))

# 2 part-time puzzle
def P_FREE(w): return RDV('free_places', '{in:room}', tok('wday', w))
def P_BOOK(w): return '(%s+%s)' % (RDV('booked_places', '{in:room}', tok('wday', w)), RDV('held_places', '{in:room}', tok('wday', w)))
P_WANT = '+'.join('{in:%s}' % k for k, _ in DAYS)
P_BLOCK = '+'.join('{in:%s}*(%s<1)' % (k, P_FREE(w)) for k, w in DAYS)
P_SWAP = '"-"'
for k, w in reversed(DAYS): P_SWAP = 'IF(AND({in:%s}=0,%s>=1),%s,%s)' % (k, P_FREE(w), tok('wday', w), P_SWAP)
P_STEP = '+'.join('{in:%s}*(ROUNDUP((%s+1)/%s,0)>ROUNDUP(%s/%s,0))' % (k, P_BOOK(w), RAT('{in:room}'), P_BOOK(w), RAT('{in:room}')) for k, w in DAYS)
P_HRS = 'IF({in:half}=%s,SUMIFS(%s,%s,%s),SUMIFS(%s,%s,%s))' % (tok('daytype', 'Half day'), RG('schedules', 'hours_day'), RG('schedules', 'schedule'), tok('schedule', '5 half days'), RG('schedules', 'hours_day'), RG('schedules', 'schedule'), S5F)
P_RATE = 'IF(SUMIFS(%s,%s,{in:room},%s,%s,%s,%s)>0,SUMIFS(%s,%s,{in:room},%s,%s,%s,%s),(%s)*IFERROR(AVERAGEIFS(%s,%s,{in:room},%s,%s),0))' % (
    RG('rates', 'weekly_rate'), RG('rates', 'room'), RG('rates', 'days'), P_WANT, RG('rates', 'hours_day'), P_HRS, RG('rates', 'weekly_rate'), RG('rates', 'room'), RG('rates', 'days'), P_WANT, RG('rates', 'hours_day'), P_HRS,
    P_WANT, RG('rates', 'day_rate'), RG('rates', 'room'), RG('rates', 'hours_day'), P_HRS)
tools.append(TOOL('puzzle', 'Part-Time Schedule Puzzle', 'Which part-time days fit without breaking capacity or ratio',
    'Tick the days a family wants (1 yes, 0 no): each day is checked against the free places and the ratio of that room; the verdict names the day swap when exactly one day is full.', [
    IL('room', 'Room', 'room', 'Preschool')] + [I(k, w, 1 if k in ('mon', 'wed', 'fri') else 0) for k, w in DAYS] + [IL('half', 'Day type', 'daytype', 'Full day')], [
    O('Days wanted', 'int', P_WANT)] + [O('Free places on ' + w, 'int', P_FREE(w)) for k, w in DAYS] + [
    O('Days with a free place', 'int', '+'.join('{in:%s}*(%s>=1)' % (k, P_FREE(w)) for k, w in DAYS)), O('Days with no free place', 'int', P_BLOCK),
    O('Day to swap to', 'text', P_SWAP), O('Wanted days that need one more staff member at the ratio', 'int', P_STEP), O('Weekly price for these days', 'money', P_RATE),
    O('Verdict', 'text', 'IF((%s)=0,%s,IF(AND((%s)=1,%s<>"-"),%s,%s))' % (P_BLOCK, vd('Accept'), P_BLOCK, P_SWAP, vd('Accept with a day swap'), vd('Decline')))],
    GR('What if', ('All five days', {'mon': 1, 'tue': 1, 'wed': 1, 'thu': 1, 'fri': 1}), ('Tuesday and Thursday', {'mon': 0, 'tue': 1, 'wed': 0, 'thu': 1, 'fri': 0}), ('Monday and Tuesday', {'mon': 1, 'tue': 1, 'wed': 0, 'thu': 0, 'fri': 0}),
       ('Toddlers, Monday Wednesday Friday', {'room': RT('Toddlers')}), ('Infants, all five days', {'room': RT('Infants'), 'mon': 1, 'tue': 1, 'wed': 1, 'thu': 1, 'fri': 1}))))

# 3 aging-up planner
NR3 = 'IFERROR(IF({in:room}=%s,"",INDEX(%s,MATCH({in:room},%s,0)+1)&""),"")' % (tok('room', 'School-age'), RG('rooms', 'room'), RG('rooms', 'room'))
MV3 = 'COUNTIFS(%s,{in:room},%s,"<="&{in:months})' % (RG('aging_up', 'room'), RG('aging_up', 'months_to_move'))
FREE3 = '(%s-COUNTIFS(%s,%s,%s,%s))' % (CAP(NR3), RG('children', 'room'), NR3, RG('children', 'status'), ENR)
LV3 = 'COUNTIFS(%s,%s,%s,"<="&{in:months})' % (RG('aging_up', 'room'), NR3, RG('aging_up', 'months_to_move'))
SHORT3 = 'MAX(0,%s-%s-%s)' % (MV3, FREE3, LV3)
tools.append(TOOL('aging_planner', 'Aging-Up Planner', 'Children reaching the next room, and when a room runs out',
    'Pick a room and a window in months: see how many children reach the moving age, the places the next room has and gives up, and the month the next room runs out of places.', [
    IL('room', 'Room', 'room', 'Toddlers'), I('months', 'Months ahead', 6)], [
    O('Children in the room now', 'int', 'COUNTIFS(%s,{in:room},%s,%s)' % (RG('children', 'room'), RG('children', 'status'), ENR)), O('Next room', 'text', NR3),
    O('Children reaching the moving age in the window', 'int', MV3), O('Of them due now', 'int', 'COUNTIFS(%s,{in:room},%s,"<=0")' % (RG('aging_up', 'room'), RG('aging_up', 'months_to_move'))),
    O('Next room licensed places', 'int', CAP(NR3)), O('Free places in the next room now', 'int', FREE3), O('Children leaving the next room in the window', 'int', LV3),
    O('Places short after the moves', 'int', SHORT3),
    O('First move date in this room', 'date', 'IFERROR(SUMIFS(%s,%s,{in:room},%s,1)/COUNTIFS(%s,{in:room},%s,1),"")' % (RG('aging_up', 'move_date'), RG('aging_up', 'room'), RG('aging_up', 'room_rank'), RG('aging_up', 'room'), RG('aging_up', 'room_rank'))),
    O('Month the next room fills', 'date', 'IF(SUMIFS(%s,%s,%s,%s,1)=0,"-",SUMIFS(%s,%s,%s,%s,1))' % (RG('capacity6', 'month'), RG('capacity6', 'room'), NR3, RG('capacity6', 'full_rank'), RG('capacity6', 'month'), RG('capacity6', 'room'), NR3, RG('capacity6', 'full_rank'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>0,%s,%s))' % (MV3, vd('Hold'), SHORT3, vd('Open a place'), vd('Move on the date')))],
    GR('What if', ('Infants', {'room': RT('Infants')}), ('Twos', {'room': RT('Twos')}), ('Preschool', {'room': RT('Preschool')}), ('Toddlers, 3 months', {'months': 3}), ('Toddlers, 12 months', {'months': 12}))))

# 4 booked vs attended drift
tools.append(TOOL('drift_tool', 'Booked vs Attended Drift', 'Booked hours against attended hours and the money gap',
    'Type a child\'s booked and attended hours in a week and the price per hour: see the drift, the money gap if billing used attended hours, and how many child-weeks of your log are over your tolerance.', [
    I('booked', 'Booked hours a week', 45, 'num'), I('attended', 'Attended hours a week', 39.5, 'num'), I('price', 'Price per hour', 8.13, 'money'), I('tol', 'Tolerance', 0.10, 'pct'), I('weeks', 'Weeks', 4)], [
    O('Drift in hours', 'num', '{in:attended}-{in:booked}'), O('Drift share', 'pct', 'IFERROR(({in:attended}-{in:booked})/{in:booked},0)'), O('Billed on booked hours, a week', 'money', '{in:booked}*{in:price}'),
    O('Billed on attended hours, a week', 'money', '{in:attended}*{in:price}'), O('Money gap a week', 'money', '({in:booked}-{in:attended})*{in:price}'), O('Money gap over the weeks', 'money', '({in:booked}-{in:attended})*{in:price}*{in:weeks}'),
    O('Child-weeks over tolerance in your log', 'int', 'COUNTIFS(%s,%s)' % (RG('bva', 'drift_flag'), fl('Over tolerance'))), O('Share of child-weeks over tolerance', 'pct', 'IFERROR(COUNTIFS(%s,%s)/COUNTIFS(%s,"<>"),0)' % (RG('bva', 'drift_flag'), fl('Over tolerance'), RG('bva', 'bva_id'))),
    O('Money gap in the whole log', 'money', 'SUM(%s)' % RG('bva', 'money_gap')),
    O('Verdict', 'text', 'IF(ABS(IFERROR(({in:attended}-{in:booked})/{in:booked},0))>{in:tol},%s,%s)' % (vd('Review the schedule'), vd('Keep booked billing')))],
    GR('What if', ('Attended 44 hours', {'attended': 44}), ('Attended 30 hours', {'attended': 30}), ('Tolerance 20 percent', {'tol': 0.2}), ('Half-day child, 25 booked', {'booked': 25, 'attended': 22, 'price': 9.2}), ('Price 10 an hour', {'price': 10}))))

# 5 sign-in and sign-out hours
PAST5 = 'MAX(0,ROUND((VALUE({in:t_out})-VALUE({set:closing_time}))*1440,0))'
BILL5 = 'IF(%s>{set:late_grace_min},%s,0)' % (PAST5, PAST5)
tools.append(TOOL('signin_hours', 'Sign-in and Sign-out Hours', 'Hours attended, minutes past closing and the late fee',
    'Type the sign-in and sign-out times as hours and minutes: see the hours attended, the minutes past closing, the minutes billed after the grace time and the late pickup fee passed to the invoice.', [
    I('t_in', 'Sign in time', '08:10', 'text'), I('t_out', 'Sign out time', '17:48', 'text'), I('booked', 'Booked hours', 9, 'num')], [
    O('Hours attended', 'num', 'ROUND((VALUE({in:t_out})-VALUE({in:t_in}))*24,2)'), O('Hours against booked', 'num', 'ROUND((VALUE({in:t_out})-VALUE({in:t_in}))*24,2)-{in:booked}'),
    O('Minutes past closing', 'int', PAST5), O('Grace minutes', 'int', '{set:late_grace_min}'), O('Minutes billed', 'int', BILL5), O('Late pickup fee', 'money', '(%s)*{set:late_fee_per_min}' % BILL5),
    O('Fee if there were no grace time', 'money', '(%s)*{set:late_fee_per_min}' % PAST5),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (BILL5, v2('Charge the late fee'), v2('No fee inside the grace time')))],
    GR('What if', ('Out at 17:34, inside the grace time', {'t_out': '="17:34"'}), ('Out at 17:36', {'t_out': '="17:36"'}), ('Out at 18:05', {'t_out': '="18:05"'}), ('Out at 16:50', {'t_out': '="16:50"'}), ('In at 07:05, out at 17:30', {'t_in': '="07:05"', 't_out': '="17:30"'}))))

# 6 school-age afternoon load
AF6 = 'MAX(%s)' % ','.join('SUMIFS(%s,%s,%s,%s,%s)' % (RG('by_hour', 'avg_children'), RG('by_hour', 'room'), tok('room', 'School-age'), RG('by_hour', 'hour'), tok('hour', h)) for h in ('3 pm', '4 pm', '5 pm'))
TOT6 = '({in:children}+{in:extra})'
tools.append(TOOL('afternoon_load', 'School-Age Afternoon Load', 'Children signed in after school against places and ratio',
    'Type the children signed in, staff present and extra children: see the School-age places, ratio, staff gap and your busiest afternoon hour; a second group needs its own space and staff.', [
    I('children', 'Children signed in', 11), I('staff', 'Staff present', 1), I('extra', 'Extra children expected', 0)], [
    O('School-age licensed places', 'int', CAP(tok('room', 'School-age'))), O('Children per staff allowed, check your local rules', 'int', RAT(tok('room', 'School-age'))), O('Children in the group', 'int', TOT6),
    O('Share of places', 'pct', 'IFERROR(%s/%s,0)' % (TOT6, CAP(tok('room', 'School-age')))), O('Places left', 'int', '%s-%s' % (CAP(tok('room', 'School-age')), TOT6)),
    O('Staff needed at the ratio', 'int', 'ROUNDUP(%s/%s,0)' % (TOT6, RAT(tok('room', 'School-age')))), O('Staff gap', 'int', 'MAX(0,ROUNDUP(%s/%s,0)-{in:staff})' % (TOT6, RAT(tok('room', 'School-age')))),
    O('Busiest afternoon hour in your log, children', 'num', AF6), O('Share of places at that hour', 'pct', 'IFERROR((%s)/%s,0)' % (AF6, CAP(tok('room', 'School-age')))),
    O('Verdict', 'text', 'IF(OR(%s>%s,ROUNDUP(%s/%s,0)>{in:staff}),%s,%s)' % (TOT6, CAP(tok('room', 'School-age')), TOT6, RAT(tok('room', 'School-age')), vd('Add a second group'), vd('Enough room')))],
    GR('What if', ('13 children, 1 staff member', {'children': 13}), ('13 children, 2 staff members', {'children': 13, 'staff': 2}), ('Full room of 16', {'children': 16, 'staff': 2}), ('Two extra children', {'extra': 2}), ('Quiet day, 6 children', {'children': 6}))))

# 7 free place finder
PN7 = 'SUMIFS(%s,%s,{in:schedule})' % (RG('schedules', 'days'), RG('schedules', 'schedule'))
FD7 = {k: RDV('free_places', '{in:room}', tok('wday', w)) for k, w in DAYS}
OK7 = 'IF(%s=5,%s,IF(%s=3,%s,IF(%s=2,%s,%s)))' % (PN7, '+'.join('(%s>=1)' % FD7[k] for k, _ in DAYS), PN7, '+'.join('(%s>=1)' % FD7[k] for k in ('mon', 'wed', 'fri')), PN7, '+'.join('(%s>=1)' % FD7[k] for k in ('tue', 'thu')), '+'.join('(%s>=1)' % FD7[k] for k, _ in DAYS))
tools.append(TOOL('place_finder', 'Free Place Finder', 'Which room-days have a free place for a schedule',
    'Pick a room and a schedule (five days: every weekday, three: Monday Wednesday Friday, two: Tuesday Thursday): see free places each day and whether a place is available or the family waits.', [
    IL('room', 'Room', 'room', 'Toddlers'), IL('schedule', 'Schedule', 'schedule', '3 full days')], [
    O('Days in the schedule', 'int', PN7)] + [O('Free places on ' + w, 'int', FD7[k]) for k, w in DAYS] + [
    O('Schedule days with a free place', 'int', OK7), O('Free places in this room in three months', 'int', 'SUMIFS(%s,%s,{in:room},%s,EDATE(%s,3))' % (RG('capacity6', 'free_places'), RG('capacity6', 'room'), RG('capacity6', 'month'), MS)),
    O('Families waiting for this room', 'int', 'COUNTIFS(%s,{in:room},%s,%s)' % (RG('requests', 'room'), RG('requests', 'status'), tok('reqstatus', 'Waiting for answer'))),
    O('Verdict', 'text', 'IF(%s=%s,%s,%s)' % (OK7, PN7, vd('Place available'), vd('Waiting list')))],
    GR('What if', ('Preschool, five full days', {'room': RT('Preschool'), 'schedule': '=' + tok('schedule', '5 full days')}), ('Infants, two full days', {'room': RT('Infants'), 'schedule': '=' + tok('schedule', '2 full days')}),
       ('Twos, five full days', {'room': RT('Twos'), 'schedule': '=' + tok('schedule', '5 full days')}), ('School-age, three half days', {'room': RT('School-age'), 'schedule': '=' + tok('schedule', '3 half days')}), ('Preschool, three full days', {'room': RT('Preschool')}))))

# 8 room move date planner
AGE8 = 'DATEDIF({in:dob},{today},"M")'
MA8 = 'IFERROR(CHOOSE(MATCH({in:room},%s,0),{set:moveup_infants},{set:moveup_toddlers},{set:moveup_twos},{set:moveup_preschool}),0)' % RG('rooms', 'room')
MD8 = 'EDATE({in:dob},%s)' % MA8
NR8 = NR3.replace('{in:room}', '{in:room}')
FREE8 = '(%s-COUNTIFS(%s,%s,%s,%s))' % (CAP(NR8), RG('children', 'room'), NR8, RG('children', 'status'), ENR)
OUT8 = 'COUNTIFS(%s,%s,%s,"<="&%s)' % (RG('aging_up', 'room'), NR8, RG('aging_up', 'move_date'), MD8)
IN8 = 'COUNTIFS(%s,%s,%s,"<="&%s)' % (RG('aging_up', 'next_room'), NR8, RG('aging_up', 'move_date'), MD8)
PL8 = '(%s+%s-%s)' % (FREE8, OUT8, IN8)
tools.append(TOOL('move_date', 'Room Move Date Planner', 'Move date for one child from birthday and next-room places',
    'Type the date of birth and the current room: see the age, the move date, the places free in the next room on that date and whether to move now, move on the date or hold.', [
    I('dob', 'Date of birth', ago(790), 'date'), IL('room', 'Room', 'room', 'Toddlers')], [
    O('Age in months', 'int', AGE8), O('Moving age in months', 'int', MA8), O('Months to the moving age', 'int', MA8 + '-' + AGE8), O('Move date', 'date', MD8), O('Days to the move date', 'int', MD8 + '-{today}'),
    O('Next room', 'text', NR8), O('Free places in the next room now', 'int', FREE8), O('Children leaving the next room by that date', 'int', OUT8), O('Children already waiting to move in by that date', 'int', IN8),
    O('Places left for this child on that date', 'int', PL8), O('Effective date', 'date', 'MAX(%s,{today})' % MD8),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s<={today},%s,%s))' % (PL8, vd('Hold'), MD8, vd('Move now'), vd('Move on the date')))],
    GR('What if', ('Born 20 months ago', {'dob': '={today}-610'}), ('Born 30 months ago', {'dob': '={today}-915'}), ('Infants room, born 14 months ago', {'dob': '={today}-425', 'room': RT('Infants')}),
       ('Twos room, born 36 months ago', {'dob': '={today}-1095', 'room': RT('Twos')}), ('Preschool room, born 55 months ago', {'dob': '={today}-1675', 'room': RT('Preschool')}))))

# 9 paid-but-absent revenue
DR9 = 'SUMIFS(%s,%s,{in:room},%s,%s)' % (RG('rates', 'day_rate'), RG('rates', 'room'), RG('rates', 'schedule'), S5F)
MT9 = 'SUMIFS(%s,%s,{in:room},%s,%s)*52/12' % (RG('children', 'weekly_rate'), RG('children', 'room'), RG('children', 'status'), ENR)
tools.append(TOOL('paid_absent', 'Paid-but-Absent Revenue', 'What absent booked days are worth and the share of tuition',
    'Type the absent booked days of a month and the share you credit: see the revenue billed for days children did not come, its share of the room\'s monthly tuition and the cost of a credit rule.', [
    IL('room', 'Room', 'room', 'Twos'), I('days', 'Absent booked days in a month', absent_default('Twos')), I('credit', 'Share of an absent day credited', 0.0, 'pct'), I('tol', 'Share of tuition you accept', 0.05, 'pct')], [
    O('Day rate, five full days', 'money', DR9), O('Revenue billed for absent days', 'money', '{in:days}*%s*(1-{in:credit})' % DR9), O('Monthly tuition of the room', 'money', MT9),
    O('Share of the monthly tuition', 'pct', 'IFERROR({in:days}*%s*(1-{in:credit})/(%s),0)' % (DR9, MT9)), O('Absent booked days in your log, last 30 days', 'int', 'SUMIFS(%s,%s,{in:room},%s,">"&({today}-30))' % (RG('attendance', 'absent_flag'), RG('attendance', 'room'), RG('attendance', 'date'))),
    O('Share of booked days absent, last 30 days', 'pct', 'IFERROR(SUMIFS(%s,%s,{in:room},%s,">"&({today}-30))/COUNTIFS(%s,{in:room},%s,">"&({today}-30),%s,%s),0)' % (RG('attendance', 'absent_flag'), RG('attendance', 'room'), RG('attendance', 'date'), RG('attendance', 'room'), RG('attendance', 'date'), RG('attendance', 'booked'), YES)),
    O('Cost of a 50 percent credit rule', 'money', '{in:days}*%s*0.5' % DR9),
    O('Verdict', 'text', 'IF(IFERROR({in:days}*%s*(1-{in:credit})/(%s),0)>{in:tol},%s,%s)' % (DR9, MT9, vd('Review the absence rule'), vd('Absence rule is fine')))],
    GR('What if', ('Half credited', {'credit': 0.5}), ('Infants room', {'room': RT('Infants'), 'days': absent_default('Infants')}), ('Preschool room', {'room': RT('Preschool'), 'days': absent_default('Preschool')}),
       ('Few absences, 6 days', {'days': 6}), ('Accept 15 percent', {'tol': 0.15}))))

# 10 peak-hour pressure
AV10 = lambda h: 'SUMIFS(%s,%s,{in:room},%s,%s)' % (RG('by_hour', 'avg_children'), RG('by_hour', 'room'), RG('by_hour', 'hour'), h)
MX10 = 'SUMPRODUCT(MAX((%s={in:room})*%s))' % (RG('by_hour', 'room'), RG('by_hour', 'avg_children'))
BH10 = 'INDEX(%s,MATCH({in:room},%s,0))' % (RG('by_hour', 'hour'), RG('by_hour', 'peak_key'))
tools.append(TOOL('peak_hour', 'Peak-Hour Pressure', 'Children present by hour against places and the ratio',
    'Pick a room and an hour: see the average children present, the share of places, staff needed at the ratio, the busiest hours of the room and center, and whether to stagger arrivals.', [
    IL('room', 'Room', 'room', 'Preschool'), IL('hour', 'Hour of the day', 'hour', '9 am'), I('limit', 'Share of places that counts as a peak', 0.8, 'pct')], [
    O('Average children at that hour', 'num', AV10('{in:hour}')), O('Licensed places', 'int', CAP('{in:room}')), O('Share of places', 'pct', 'IFERROR(%s/%s,0)' % (AV10('{in:hour}'), CAP('{in:room}'))),
    O('Staff needed at the ratio', 'int', 'ROUNDUP(%s/%s,0)' % (AV10('{in:hour}'), RAT('{in:room}'))), O('Busiest hour of the room', 'text', BH10), O('Children at the busiest hour', 'num', MX10),
    O('Hours of the day at or above the peak share', 'int', 'COUNTIFS(%s,{in:room},%s,">="&{in:limit})' % (RG('by_hour', 'room'), RG('by_hour', 'share'))),
    O('All rooms together at that hour', 'num', 'SUMIFS(%s,%s,{in:hour})' % (RG('by_hour', 'avg_children'), RG('by_hour', 'hour'))), O('Busiest hour of the center', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (RG('by_hour', 'hour'), RG('by_hour', 'hour_total'), RG('by_hour', 'hour_total'))),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>={in:limit},%s,%s)' % (AV10('{in:hour}'), CAP('{in:room}'), vd('Stagger arrivals'), vd('Fine as it is')))],
    GR('What if', ('Toddlers at 10 am', {'room': RT('Toddlers'), 'hour': '=' + tok('hour', '10 am')}), ('Infants at 8 am', {'room': RT('Infants'), 'hour': '=' + tok('hour', '8 am')}), ('Preschool at 4 pm', {'hour': '=' + tok('hour', '4 pm')}),
       ('School-age at 4 pm', {'room': RT('School-age'), 'hour': '=' + tok('hour', '4 pm')}), ('Peak share 60 percent', {'limit': 0.6}))))

# 11 drop-in day check
FR11 = RDV('free_places', '{in:room}', '{in:day}'); BK11 = '(%s+%s)' % (RDV('booked_places', '{in:room}', '{in:day}'), RDV('held_places', '{in:room}', '{in:day}'))
DR11 = RDV('day_rate', '{in:room}', '{in:day}')
STEP11 = '(ROUNDUP((%s+{in:asked})/%s,0)-ROUNDUP(%s/%s,0))' % (BK11, RAT('{in:room}'), BK11, RAT('{in:room}'))
NET11 = '({in:asked}*%s*(1+{set:drop_in_surcharge})-%s*{in:hours}*{in:staff_cost})' % (DR11, STEP11)
tools.append(TOOL('dropin_check', 'Drop-in Day Check', 'Free places on a day, the price and the staff step',
    'A drop-in day is an extra day booked at short notice. Pick room and day: see free places, the price with surcharge, whether another staff member is needed and the net result.', [
    IL('room', 'Room', 'room', 'Toddlers'), IL('day', 'Weekday', 'wday', 'Wednesday'), I('asked', 'Children asking', 1), I('hours', 'Hours of the day', 9, 'num'), I('staff_cost', 'Staff cost per hour', 18.5, 'money')], [
    O('Free places that day', 'int', FR11), O('Children booked and held', 'int', BK11), O('Day rate', 'money', DR11), O('Surcharge', 'money', DR11 + '*{set:drop_in_surcharge}'), O('Price for one child', 'money', DR11 + '*(1+{set:drop_in_surcharge})'),
    O('Extra staff members needed at the ratio', 'int', STEP11), O('Extra staff cost', 'money', STEP11 + '*{in:hours}*{in:staff_cost}'), O('Net result of the drop-in day', 'money', NET11),
    O('Drop-in days in your log, last 90 days', 'int', 'COUNTIFS(%s,">"&({today}-90))' % RG('dropins', 'date')),
    O('Verdict', 'text', 'IF(AND(%s>={in:asked},%s>0),%s,%s)' % (FR11, NET11, vd('Accept the drop-in'), vd('Decline the drop-in')))],
    GR('What if', ('Preschool on Monday', {'room': RT('Preschool'), 'day': WT('Monday')}), ('Infants on Friday', {'room': RT('Infants'), 'day': WT('Friday')}), ('Twos on Tuesday, two children', {'room': RT('Twos'), 'day': WT('Tuesday'), 'asked': 2}),
       ('Half day, 5 hours', {'hours': 5}), ('Staff cost 25 an hour', {'staff_cost': 25}))))

# 12 closure calendar impact
M12 = '{in:month}'; E12 = 'EOMONTH({in:month},0)'
CL12 = 'COUNTIFS(%s,">="&%s,%s,"<="&%s)' % (RG('closures', 'date'), M12, RG('closures', 'date'), E12)
AT12 = 'SUMIFS(%s,%s,">="&%s,%s,"<="&%s)' % (RG('closures', 'tuition_at_stake'), RG('closures', 'date'), M12, RG('closures', 'date'), E12)
tools.append(TOOL('closure_impact', 'Closure Calendar Impact', 'Open days in a month and the days owed as a credit',
    'Pick a month and the share of a closure day you credit: see the weekdays, the closure days, the open days, the day tuition at stake and the credit owed, with a verdict under the rule you set.', [
    I('month', 'First day of the month', '%s-12-01' % TODAY.year, 'date'), I('credit', 'Share of a closure day credited', 0.5, 'pct')], [
    O('Weekdays in the month', 'int', 'NETWORKDAYS(%s,%s)' % (M12, E12)), O('Closure days in the month', 'int', CL12), O('Open days', 'int', 'NETWORKDAYS(%s,%s)-%s' % (M12, E12, CL12)),
    O('Share of weekdays closed', 'pct', 'IFERROR(%s/NETWORKDAYS(%s,%s),0)' % (CL12, M12, E12)), O('Day tuition at stake on closure days', 'money', AT12), O('Credit owed under your rule', 'money', AT12 + '*{in:credit}'),
    O('Credit per enrolled child', 'money', 'IFERROR(%s*{in:credit}/COUNTIFS(%s,%s),0)' % (AT12, RG('children', 'status'), ENR)),
    O('Closure days this year', 'int', 'COUNTIFS(%s,">="&DATE(YEAR({today}),1,1),%s,"<="&DATE(YEAR({today}),12,31))' % (RG('closures', 'date'), RG('closures', 'date'))),
    O('Verdict', 'text', 'IF(AND(%s>0,{in:credit}>0),%s,%s)' % (CL12, vd('Credit the days'), vd('No credit')))],
    GR('What if', ('No credit', {'credit': 0}), ('Full credit', {'credit': 1}), ('January', {'month': '=DATE(YEAR({today})+1,1,1)'}), ('A month with no closure', {'month': '=DATE(YEAR({today}),11,1)'}), ('Next September', {'month': '=DATE(YEAR({today})+1,9,1)'}))))

# 13 room capacity forecast
EX13 = lambda k: 'SUMIFS(%s,%s,{in:room},%s,EDATE(%s,%d))' % (RG('capacity6', 'expected'), RG('capacity6', 'room'), RG('capacity6', 'month'), MS, k)
ADJ13 = 'IF({in:scenario}=%s,{in:starters},IF({in:scenario}=%s,-{in:leavers},0))' % (tok('scenario', 'Best'), tok('scenario', 'Worst'))
EK13 = lambda k: 'MAX(0,%s+%d*%s)' % (EX13(k), k + 1, ADJ13)
FIRST13 = '"-"'
for k in reversed(range(6)): FIRST13 = 'IF(%s>={set:occupancy_target}*%s,EDATE(%s,%d),%s)' % (EK13(k), CAP('{in:room}'), MS, k, FIRST13)
tools.append(TOOL('capacity_forecast', 'Room Capacity Forecast', 'Six months of expected children by room, Base, Best or Worst',
    'Pick a room and a scenario: moves, starters and notices give the expected children each month; Best adds starters, Worst leavers; see the month the room reaches your target.', [
    IL('room', 'Room', 'room', 'Twos'), IL('scenario', 'Scenario', 'scenario', 'Base'), I('starters', 'Extra starters a month in Best', 0.5, 'num'), I('leavers', 'Extra leavers a month in Worst', 0.5, 'num')], [
    O('Licensed places', 'int', CAP('{in:room}'))] + [O('Expected children in month %d' % (k + 1), 'num', EK13(k)) for k in range(6)] + [
    O('Expected occupancy in month 6', 'pct', 'IFERROR(%s/%s,0)' % (EK13(5), CAP('{in:room}'))), O('Free places in month 6', 'num', 'MAX(0,%s-%s)' % (CAP('{in:room}'), EK13(5))), O('First month at the wanted occupancy', 'date', FIRST13),
    O('Verdict', 'text', 'IF(%s<>"-",%s,%s)' % (FIRST13, vd('Fills within six months'), vd('Stays below target')))],
    GR('What if', ('Toddlers', {'room': RT('Toddlers')}), ('Preschool, Best', {'room': RT('Preschool'), 'scenario': '=' + tok('scenario', 'Best')}), ('Twos, Worst', {'scenario': '=' + tok('scenario', 'Worst')}), ('Infants, Best', {'room': RT('Infants'), 'scenario': '=' + tok('scenario', 'Best')}), ('School-age', {'room': RT('School-age')}))))

# 14 attendance pattern finder
def RATE14(w): return 'SUMIFS(%s,%s,{in:room},%s,%s)' % (RG('room_day', 'attend_rate'), RG('room_day', 'room'), RG('room_day', 'weekday'), tok('wday', w))
MN14 = 'AVERAGEIFS(%s,%s,{in:room})' % (RG('room_day', 'room_low'), RG('room_day', 'room')); MX14 = 'AVERAGEIFS(%s,%s,{in:room})' % (RG('room_day', 'room_high'), RG('room_day', 'room'))
LOW14 = 'INDEX(%s,MATCH({in:room}&"|"&ROUND(%s,5),%s,0))' % (RG('room_day', 'weekday'), MN14, RG('room_day', 'rate_key'))
tools.append(TOOL('pattern_finder', 'Attendance Pattern Finder', 'Which weekday has the lowest attendance in a room',
    'Pick a room: see the share of booked days attended on each weekday, the lowest and the highest day and the gap; a wide gap means days could be reshuffled.', [
    IL('room', 'Room', 'room', 'Preschool'), I('gap', 'Gap between weekdays that starts a review', 0.03, 'pct')], [
    O('Attendance rate on ' + w, 'pct', RATE14(w)) for k, w in DAYS] + [
    O('Lowest weekday', 'text', LOW14), O('Lowest rate', 'pct', MN14), O('Highest rate', 'pct', MX14), O('Gap between the best and the worst day', 'pct', '%s-%s' % (MX14, MN14)),
    O('Booked places on the lowest weekday', 'int', 'SUMIFS(%s,%s,{in:room},%s,%s)' % (RG('room_day', 'booked_places'), RG('room_day', 'room'), RG('room_day', 'weekday'), LOW14)),
    O('Verdict', 'text', 'IF(%s-%s>={in:gap},%s,%s)' % (MX14, MN14, vd('Reshuffle days'), vd('Keep the days')))],
    GR('What if', ('Infants', {'room': RT('Infants')}), ('Toddlers', {'room': RT('Toddlers')}), ('Twos', {'room': RT('Twos')}), ('School-age', {'room': RT('School-age')}), ('Review from a 1 point gap', {'gap': 0.01}))))

# 15 licensed capacity check
TOT15 = '({in:children}+{in:extra})'
BUSY15 = 'MAX(%s)' % ','.join(RDV('booked_places', '{in:room}', tok('wday', w)) for _, w in DAYS)
CTR15 = 'MAX(%s)' % ','.join('SUMIFS(%s,%s,%d)' % (RG('room_day', 'booked_places'), RG('room_day', 'day_no'), n) for n in range(1, 6))
tools.append(TOOL('capacity_check', 'Licensed Capacity Check', 'Children on a day against licensed places, check local rules',
    'Type the children expected on a day and any extra: see the licensed places, how many places are over or left and the staff needed at the ratio; always check your local rules for your own limits.', [
    IL('room', 'Room', 'room', 'Twos'), I('children', 'Children expected', 12), I('extra', 'Extra children', 1)], [
    O('Licensed places', 'int', CAP('{in:room}')), O('Children in the room', 'int', TOT15), O('Over by', 'int', 'MAX(0,%s-%s)' % (TOT15, CAP('{in:room}'))), O('Places left', 'int', 'MAX(0,%s-%s)' % (CAP('{in:room}'), TOT15)),
    O('Children per staff allowed', 'int', RAT('{in:room}')), O('Staff needed at the ratio', 'int', 'ROUNDUP(%s/%s,0)' % (TOT15, RAT('{in:room}'))), O('Busiest weekday booking in your table', 'int', BUSY15),
    O('Free places on the busiest weekday', 'int', 'MAX(0,%s-%s)' % (CAP('{in:room}'), BUSY15)), O('Licensed places of the whole center', 'int', 'SUM(%s)' % RG('rooms', 'capacity')), O('Booked on the busiest weekday, whole center', 'int', CTR15),
    O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (TOT15, CAP('{in:room}'), vd('Over the limit'), vd('Within limit')))],
    GR('What if', ('Two extra children', {'extra': 2}), ('Infants room, 8 children', {'room': RT('Infants'), 'children': 8, 'extra': 0}), ('Preschool room, 19 children', {'room': RT('Preschool'), 'children': 19, 'extra': 1}),
       ('School-age room, 15 children', {'room': RT('School-age'), 'children': 15, 'extra': 2}), ('Toddlers room, 12 children', {'room': RT('Toddlers'), 'children': 12, 'extra': 0}))))

# 16 absence flag
tools.append(TOOL('absence_flag', 'Absence Flag', 'Which children to check in on, status only',
    'Type a child\'s absent days and booked days in a month: see the absent share and whether it reaches your check-in rule; the log shows how many children are flagged now. Counts only, no reasons.', [
    I('absent', 'Days absent in the month', 4), I('booked', 'Booked days in the month', 16), I('sick', 'Sick absence days among them', 2), I('rate', 'Day rate', 67, 'money')], [
    O('Share of booked days absent', 'pct', 'IFERROR({in:absent}/{in:booked},0)'), O('Sick absence share of the absent days', 'pct', 'IFERROR({in:sick}/{in:absent},0)'), O('Absent days that start a check-in', 'int', '{set:absence_alert_days}'),
    O('Paid but absent value', 'money', '{in:absent}*{in:rate}'), O('Children flagged this month in your log', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (RG('absences', 'abs_flag'), fl('Check in with the family'), RG('absences', 'month'), MS)),
    O('Absent days this month in your log', 'int', 'SUMIFS(%s,%s,%s)' % (RG('absences', 'days_absent'), RG('absences', 'month'), MS)), O('Share of all booked days absent this month', 'pct', 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (RG('absences', 'days_absent'), RG('absences', 'month'), MS, RG('absences', 'booked_days'), RG('absences', 'month'), MS)),
    O('Verdict', 'text', 'IF({in:absent}>={set:absence_alert_days},%s,%s)' % (vd('Check in with the family'), v2('No concern')))],
    GR('What if', ('Two absent days', {'absent': 2, 'sick': 1}), ('Six absent days', {'absent': 6, 'sick': 3}), ('Part-time child, 8 booked days', {'booked': 8, 'absent': 3}), ('Day rate 90', {'rate': 90}), ('No sick days', {'sick': 0}))))

# 17 weekly occupancy trend
A4 = 'AVERAGEIFS(%s,%s,{in:room},%s,">="&({today}-28))' % (RG('weekly_hours', 'occupancy'), RG('weekly_hours', 'room'), RG('weekly_hours', 'week'))
A12 = 'AVERAGEIFS(%s,%s,{in:room},%s,">="&({today}-84))' % (RG('weekly_hours', 'occupancy'), RG('weekly_hours', 'room'), RG('weekly_hours', 'week'))
FC17 = '(%s*POWER(%s/%s,{in:weeks}/4)+IF({in:scenario}=%s,{in:nudge}*{in:weeks},IF({in:scenario}=%s,-{in:nudge}*{in:weeks},0)))' % (A4, A4, A12, tok('scenario', 'Best'), tok('scenario', 'Worst'))
tools.append(TOOL('weekly_trend', 'Weekly Occupancy Trend', 'Your last 12 weeks of booked hours and where they head',
    'Pick a room: booked share of room hours over 4 and 12 weeks gives a trend factor and forecast; Best and Worst add a weekly step; the verdict compares it with your target.', [
    IL('room', 'Room', 'room', 'Twos'), IL('scenario', 'Scenario', 'scenario', 'Base'), I('weeks', 'Weeks ahead', 4), I('nudge', 'Change a week in Best or Worst', 0.01, 'pct'), I('target', 'Target share of room hours booked', 0.60, 'pct')], [
    O('Booked share of room hours, last 4 weeks', 'pct', 'IFERROR(%s,0)' % A4), O('Booked share of room hours, last 12 weeks', 'pct', 'IFERROR(%s,0)' % A12), O('Trend factor', 'num', 'IFERROR(%s/%s,0)' % (A4, A12)),
    O('Booked hours in the last full week', 'num', 'SUMIFS(%s,%s,{in:room},%s,">"&({today}-14),%s,"<="&({today}-7))' % (RG('weekly_hours', 'booked_hours'), RG('weekly_hours', 'room'), RG('weekly_hours', 'week'), RG('weekly_hours', 'week'))),
    O('Forecast share of room hours booked', 'pct', 'IFERROR(%s,0)' % FC17), O('Against the target, points', 'pct', 'IFERROR(%s,0)-{in:target}' % FC17), O('Same share for the whole center, last 4 weeks', 'pct', 'IFERROR(AVERAGEIFS(%s,%s,">="&({today}-28)),0)' % (RG('weekly_hours', 'occupancy'), RG('weekly_hours', 'week'))),
    O('Verdict', 'text', 'IF(IFERROR(%s,0)>={in:target},%s,IF(IFERROR(%s,0)>={in:target}-0.05,%s,%s))' % (FC17, v2('Above target'), FC17, v2('Near target'), v2('Below target')))],
    GR('What if', ('Best case', {'scenario': '=' + tok('scenario', 'Best')}), ('Worst case', {'scenario': '=' + tok('scenario', 'Worst')}), ('Preschool', {'room': RT('Preschool')}), ('Infants', {'room': RT('Infants')}), ('Eight weeks ahead', {'weeks': 8}))))

# 18 notice and leaving date planner
LAST18 = 'WORKDAY({in:notice}+{in:days}+1,-1)'
tools.append(TOOL('notice_planner', 'Notice and Leaving Planner', 'Last day, the place that opens and when to advertise it',
    'Type the date a family gave notice and your notice days: see the last day, the first day the place is free, the date to start advertising and the tuition lost if the place stays empty.', [
    I('notice', 'Notice given on', ago(3), 'date'), I('days', 'Days of notice', NOTICE_DAYS), IL('room', 'Room', 'room', 'Toddlers'), I('lead', 'Days before the last day to advertise', 21), I('empty', 'Weeks the place stays empty', 2), I('rate', 'Weekly rate of the place', 366, 'money')], [
    O('Last day', 'date', LAST18), O('Place free from', 'date', 'WORKDAY(%s,1)' % LAST18), O('Days until the last day', 'int', '%s-{today}' % LAST18), O('Advertise from', 'date', '%s-{in:lead}' % LAST18),
    O('Days until advertising starts', 'int', '%s-{in:lead}-{today}' % LAST18), O('Families waiting for this room', 'int', 'COUNTIFS(%s,{in:room},%s,%s)' % (RG('requests', 'room'), RG('requests', 'status'), tok('reqstatus', 'Waiting for answer'))),
    O('Tuition lost while the place is empty', 'money', '{in:empty}*{in:rate}'), O('Typical days of notice in your log', 'int', 'IFERROR(AVERAGE(%s),0)' % RG('leavers', 'days_notice')),
    O('Notices shorter than your rule in the log', 'int', 'COUNTIFS(%s,%s)' % (RG('leavers', 'notice_flag'), fl('Short notice'))),
    O('Verdict', 'text', 'IF(%s-{in:lead}<={today},%s,%s)' % (LAST18, v2('Advertise the place now'), v2('Advertise the place later')))],
    GR('What if', ('Notice given today', {'notice': '={today}'}), ('Notice 60 days ago', {'notice': '={today}-60'}), ('Notice period 60 days', {'days': 60}), ('Place empty 6 weeks', {'empty': 6}), ('Advertise 45 days ahead', {'lead': 45}))))

assert len(tools) == 18, len(tools)
