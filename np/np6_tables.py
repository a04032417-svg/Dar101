"""Nonprofit suite part 6: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np6_lists import *
import np6_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def ORG(): return CA('org', 'Organization', 'text', '{set:org}', 22)
def CPH(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def R(t, c): return '{range:%s.%s}' % (t, c)
YS = 'DATE(YEAR({today}),1,1)'
YSL = 'DATE(YEAR({today})-1,1,1)'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
WORKED = tok('shstatus', 'Worked'); ACTIVE = tok('vstatus', 'Active'); LAPSED = tok('vstatus', 'Lapsed')
SAT = tok('wday', 'Saturday')
def MSW(label): return 'INDEX({range:member_switch.setting},MATCH(%s,{range:member_switch.item},0))' % tok('mitem', label)


settings = [
    S('org', 'Your organization name', 'text', COMPANY), S('volunteer_hour_value', 'Value of one volunteer hour, your setting', 'money', VOLUNTEER_HOUR_VALUE),
    S('new_days', 'Days a volunteer counts as new', 'int', 60), S('new_min_shifts', 'Shifts a new volunteer should have worked by now', 'int', 2),
    S('call_hours', 'Hours given for a call to a lapsed volunteer', 'num', 50), S('write_hours', 'Hours given for a letter to a lapsed volunteer', 'num', 10),
    S('reply_rate', 'Share of people you ask who say yes, your estimate', 'pct', 0.35), S('noshow_rate', 'Share of people who say yes and do not come, your estimate', 'pct', 0.06),
    S('fte_hours', 'Hours in one full-time year, your setting', 'int', 1800), S('thank_days', 'Days a gift counts as recent for a thank-you', 'int', 90),
    S('renew_grace_days', 'Days after a due date that still count as renewed on time', 'int', 60), S('retention_band', 'Points that count as the same retention', 'pct', 0.02),
    S('retention_own', "Last year's retention, your own figure (0 = sheet)", 'pct', 0.78),
    S('morning_start', 'Morning shift starts at', 'text', '09:00'), S('afternoon_start', 'Afternoon shift starts at', 'text', '14:00'),
    S('training_on', 'Date of the next volunteer training', 'date', 'today+12'), S('thanks_on', 'Date of the next volunteer thank-you event', 'date', 'today+20'),
    S('members_event_on', 'Date of the next members event', 'date', 'today+25'),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 volunteers --------------------------------------------------------------
tables.append(T('volunteers', 'Volunteers', 'Volunteer roster with role, availability and status',
    'One row per volunteer: contact, role, joined date, status and availability; the hours worked, last shift, days since and the follow-up rank for new volunteers fill in from the shift log.', [
    C('volunteer_id', 'Volunteer ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26), LST('role', 'Role', 'vrole', 14),
    C('joined', 'Joined', 'date', 11), LST('status', 'Status', 'vstatus', 10), LST('availability', 'Availability', 'avail', 11), C('donor_id', 'Donor ID', 'text', 10),
    CA('program', 'Program or area', 'text', LKT('volunteer_roles.program', 'volunteer_roles.role', 'role'), 22),
    CA('hours_worked', 'Hours worked', 'hours', LKN('hours_by_volunteer.hours_total', 'hours_by_volunteer.volunteer_id', 'volunteer_id'), 9),
    CA('hours_year', 'Hours this year', 'hours', LKN('hours_by_volunteer.hours_year', 'hours_by_volunteer.volunteer_id', 'volunteer_id'), 9),
    CA('shifts_n', 'Shifts worked', 'int', LKN('hours_by_volunteer.shifts_n', 'hours_by_volunteer.volunteer_id', 'volunteer_id'), 8),
    CA('last_shift', 'Last shift', 'date', LKD('hours_by_volunteer.last_shift', 'hours_by_volunteer.volunteer_id', 'volunteer_id'), 11),
    CA('days_since', 'Days since last shift', 'int', 'IF(ISNUMBER({col:last_shift}),{today}-{col:last_shift},"")', 9),
    CA('follow', 'New and few shifts', 'int', 'IF(AND({col:joined}>={today}-{set:new_days},{col:joined}<={today},{col:shifts_n}<{set:new_min_shifts},{col:status}<>%s),1,0)' % LAPSED, 8),
    CA('follow_score', 'Follow-up score', 'int', 'IF({col:follow}=1,ROUND({col:joined},0)*1000+VALUE(RIGHT({col:volunteer_id},3)),0)', 10),
    CA('follow_rank', 'Follow-up order', 'int', 'IF({col:follow}=1,COUNTIFS({range:volunteers.follow_score},">"&{col:follow_score})+1,"")', 8),
    CA('gives', 'Also a donor', 'int', 'IF(LEN({col:donor_id})>0,1,0)', 7),
    CPH('coord_phone', 'Volunteer coordinator phone', D.COORD_PHONE), CA('training_on', 'Next training', 'date', '{set:training_on}', 11), CA('thanks_on', 'Next thank-you event', 'date', '{set:thanks_on}', 11), ORG()],
    D.volunteers_d(), 500, [A('status', '= ' + LAPSED, 'warn'), A('status', '= ' + ACTIVE, 'good')]))
# 2 volunteer roles ---------------------------------------------------------
tables.append(T('volunteer_roles', 'Volunteer Roles', 'Roles with their program and hours per shift',
    'One row per volunteer role: the program or area it serves and the usual hours of one shift.', [
    LST('role', 'Role', 'vrole', 18, required=True), LST('program', 'Program or area', 'sprog', 22), C('hours', 'Hours per shift', 'num', 10)], D.roles_d(), 50))
# 3 shift slots -------------------------------------------------------------
tables.append(T('slots', 'Shift Slots', 'Shifts planned: people needed against signed up',
    'One row per planned shift slot: date, program, shift, role, people needed and signed up; the gap and the week fill in by themselves.', [
    C('slot_id', 'Slot ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('weekday', 'Weekday', 'wday', 11), LST('program', 'Program or area', 'sprog', 22), LST('shift', 'Shift', 'shift', 10),
    LST('role', 'Role', 'srole', 14), C('needed', 'Needed', 'int', 8), C('signed_up', 'Signed up', 'int', 8), C('hours', 'Hours', 'num', 8),
    CA('gap', 'Gap', 'int', 'MAX(0,{col:needed}-{col:signed_up})', 7), CA('week_start', 'Week of', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 11)],
    D.slots_d(), 2200, [A('gap', '> 0', 'warn')]))
# 4 shifts worked -----------------------------------------------------------
tables.append(T('shifts', 'Shifts Worked', 'Every shift booked, worked or missed',
    'One row per shift of one volunteer: date, program, shift, hours and status (worked, no-show or booked); the worked hours fill in by themselves.', [
    C('shift_id', 'Shift ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('week', 'Week of', 'date', 11), C('month', 'Month', 'date', 11), LST('weekday', 'Weekday', 'wday', 11),
    C('volunteer_id', 'Volunteer ID', 'text', 10), C('volunteer', 'Volunteer', 'text', 24), LST('role', 'Role', 'srole', 14), LST('program', 'Program or area', 'sprog', 22), LST('shift', 'Shift', 'shift', 10),
    C('hours', 'Hours', 'num', 8), LST('status', 'Status', 'shstatus', 10), CA('worked_hours', 'Worked hours', 'hours', 'IF({col:status}=%s,{col:hours},0)' % WORKED, 9)],
    D.shifts_d(), 3000, [A('status', '= ' + tok('shstatus', 'No-show'), 'bad')]))
# 5 tomorrow's shifts -------------------------------------------------------
def SH(col, kind='T'): return {'T': LKT, 'N': LKN, 'D': LKD}[kind]('shifts.' + col, 'shifts.shift_id', 'shift_id')
tables.append(T('tomorrow', "Tomorrow's Shifts", 'Booked shifts of the next days with the volunteer phone',
    "One row per booked shift: type the shift ID; the date, volunteer, phone, role, program, start time and a flag (first shift, tomorrow) fill in, and the reminder order is set for tomorrow's rows.", [
    C('shift_id', 'Shift ID', 'text', 10, required=True), CA('date', 'Date', 'date', SH('date', 'D'), 11), CA('volunteer_id', 'Volunteer ID', 'text', SH('volunteer_id'), 10), CA('volunteer', 'Volunteer', 'text', SH('volunteer'), 24),
    CA('phone', 'Phone', 'text', 'IFERROR(INDEX({range:volunteers.phone},MATCH({col:volunteer_id},{range:volunteers.volunteer_id},0))&"","")', 18),
    CA('role', 'Role', 'text', SH('role'), 14), CA('program', 'Program or area', 'text', SH('program'), 22), CA('shift', 'Shift', 'text', SH('shift'), 10), CA('hours', 'Hours', 'hours', SH('hours', 'N'), 8),
    CA('starts', 'Starts at', 'text', 'IF({col:shift}=%s,{set:morning_start},{set:afternoon_start})' % tok('shift', 'Morning'), 9),
    CA('days_away', 'Days away', 'int', 'IF(ISNUMBER({col:date}),{col:date}-{today},"")', 8),
    CA('before', 'Shifts worked before', 'int', LKN('hours_by_volunteer.shifts_n', 'hours_by_volunteer.volunteer_id', 'volunteer_id'), 9),
    CA('flag', 'Flag', 'text', 'IF({col:before}=0,%s,IF({col:days_away}=1,%s,%s))' % (ck('First shift'), ck('Tomorrow'), ck('Later this week')), 15),
    CA('sortkey', 'Sort key', 'int', 'VALUE(RIGHT({col:shift_id},5))', 8),
    CA('dseq', 'Order that day', 'int', 'IF(ISNUMBER({col:days_away}),COUNTIFS({range:tomorrow.days_away},{col:days_away},{range:tomorrow.sortkey},"<"&{col:sortkey})+1,"")', 8),
    CA('dkey', 'Day and order', 'int', 'IF(ISNUMBER({col:dseq}),{col:days_away}*1000+{col:dseq},"")', 8),
    CA('tomorrow_n', 'Volunteers tomorrow', 'int', 'COUNTIFS({range:tomorrow.days_away},1)', 8), CPH('coord_phone', 'Volunteer coordinator phone', D.COORD_PHONE), ORG()],
    D.tomorrow_d(), 80, [A('flag', '= ' + ck('First shift'), 'warn'), A('flag', '= ' + ck('Tomorrow'), 'good')]))
# 6 gaps by date ------------------------------------------------------------
def SL(col, kind='T'): return {'T': LKT, 'N': LKN, 'D': LKD}[kind]('slots.' + col, 'slots.slot_id', 'slot_id')
def ASK(col, k):  # k-th best eligible volunteer for the weekday group
    return 'IF({col:is_we}=1,IFERROR(INDEX({range:hours_by_volunteer.%s},MATCH(LARGE({range:hours_by_volunteer.ask_we},%s),{range:hours_by_volunteer.ask_we},0)),""),IFERROR(INDEX({range:hours_by_volunteer.%s},MATCH(LARGE({range:hours_by_volunteer.ask_wd},%s),{range:hours_by_volunteer.ask_wd},0)),""))' % (col, k, col, k)
tables.append(T('gaps', 'Gaps by Date', 'Open shifts ranked by date with the next person to ask',
    'One row per future slot with a gap: type the slot ID; the date, program, gap, rank by date, the busy week and a volunteer to ask first fill in by themselves.', [
    C('slot_id', 'Slot ID', 'text', 10, required=True), CA('date', 'Date', 'date', SL('date', 'D'), 11), CA('weekday', 'Weekday', 'text', SL('weekday'), 11), CA('program', 'Program or area', 'text', SL('program'), 22),
    CA('shift', 'Shift', 'text', SL('shift'), 10), CA('role', 'Role', 'text', SL('role'), 14), CA('needed', 'Needed', 'int', SL('needed', 'N'), 8), CA('signed_up', 'Signed up', 'int', SL('signed_up', 'N'), 8),
    CA('gap', 'Gap', 'int', 'MAX(0,{col:needed}-{col:signed_up})', 7), CA('days_away', 'Days away', 'int', 'IF(ISNUMBER({col:date}),{col:date}-{today},"")', 8),
    CA('week_start', 'Week of', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 11), CA('week_gap', 'People short that week', 'int', 'SUMIFS({range:gaps.gap},{range:gaps.week_start},{col:week_start})', 9),
    CA('score', 'Sort score: date, then gap, then slot', 'int', 'ROUND({col:date},0)*10000000+(99-MIN(99,{col:gap}))*100000+VALUE(RIGHT({col:slot_id},5))', 14), CA('rank', 'Rank by date', 'int', 'COUNTIFS({range:gaps.score},"<"&{col:score})+1', 8),
    CA('state', 'Action', 'text', 'IF({col:days_away}<=7,%s,IF({col:days_away}<=14,%s,%s))' % (ck('Fill this week'), ck('Fill next week'), ck('Later')), 15),
    CA('busy', 'Busiest week', 'int', 'IF({col:week_gap}>=LARGE({range:gaps.week_gap},1),1,0)', 8),
    CA('is_we', 'Weekend', 'int', 'IF({col:weekday}=%s,1,0)' % SAT, 7), CA('ask_k', 'Ask order', 'int', 'COUNTIFS({range:gaps.is_we},{col:is_we},{range:gaps.score},"<"&{col:score})+1', 7),
    CA('ask_id', 'Ask first, ID', 'text', ASK('volunteer_id', '{col:ask_k}'), 10), CA('ask_name', 'Ask first', 'text', 'IFERROR(INDEX({range:volunteers.name},MATCH({col:ask_id},{range:volunteers.volunteer_id},0))&"","")', 24),
    CA('ask_phone', 'Ask first, phone', 'text', 'IFERROR(INDEX({range:volunteers.phone},MATCH({col:ask_id},{range:volunteers.volunteer_id},0))&"","")', 18),
    CA('n7', 'Open shifts, next 7 days', 'int', 'COUNTIFS({range:gaps.days_away},">=1",{range:gaps.days_away},"<=7")', 8), CA('g7', 'People short, next 7 days', 'int', 'SUMIFS({range:gaps.gap},{range:gaps.days_away},"<=7")', 8),
    CPH('coord_phone', 'Volunteer coordinator phone', D.COORD_PHONE), CPH('pm_phone', 'Program manager phone', D.PM_PHONE), ORG()],
    D.gaps_d(), 80, [A('state', '= ' + ck('Fill this week'), 'bad'), A('state', '= ' + ck('Fill next week'), 'warn'), A('busy', '= 1', 'warn')]))
# 7 hours by volunteer ------------------------------------------------------
def SHS(extra=''): return 'SUMIFS({range:shifts.worked_hours},{range:shifts.volunteer_id},{col:volunteer_id}%s)' % extra
VL = lambda c: LKT('volunteers.' + c, 'volunteers.volunteer_id', 'volunteer_id')
tables.append(T('hours_by_volunteer', 'Hours by Volunteer', 'Hours of every volunteer this year, last year and in all',
    'One row per volunteer: type the volunteer ID and the hours from before the log starts; hours this year, last year and in all, shifts, last shift and who to ask first fill in.', [
    C('volunteer_id', 'Volunteer ID', 'text', 10, required=True), C('arch_year', 'Hours this year before the log', 'num', 10), C('arch_last', 'Hours last year before the log', 'num', 10), C('arch_prev', 'Hours earlier before the log', 'num', 10),
    C('arch_shifts', 'Shifts before the log', 'int', 8), C('arch_last_shift', 'Last shift before the log', 'date', 11),
    CA('volunteer', 'Volunteer', 'text', VL('name'), 24),
    CA('hours_year', 'Hours this year', 'hours', '{col:arch_year}+' + SHS(',{range:shifts.date},">="&%s' % YS), 9), CA('hours_last', 'Hours last year', 'hours', '{col:arch_last}+' + SHS(',{range:shifts.date},">="&%s,{range:shifts.date},"<"&%s' % (YSL, YS)), 9),
    CA('hours_prev', 'Hours before last year', 'hours', '{col:arch_prev}+' + SHS(',{range:shifts.date},"<"&%s' % YSL), 9), CA('hours_total', 'Hours in all', 'hours', '{col:hours_year}+{col:hours_last}+{col:hours_prev}', 9),
    CA('shifts_log', 'Shifts in the log', 'int', 'COUNTIFS({range:shifts.volunteer_id},{col:volunteer_id},{range:shifts.status},%s)' % WORKED, 8), CA('shifts_n', 'Shifts worked', 'int', '{col:arch_shifts}+{col:shifts_log}', 8),
    CA('last_log', 'Last shift in the log', 'date', 'IF({col:shifts_log}=0,"",SUMPRODUCT(MAX(({range:shifts.volunteer_id}={col:volunteer_id})*({range:shifts.status}=%s)*{range:shifts.date})))' % WORKED, 11),
    CA('last_shift', 'Last shift', 'date', 'IF(ISNUMBER({col:last_log}),{col:last_log},IF({col:arch_last_shift}>0,{col:arch_last_shift},""))', 11),
    CA('status', 'Status', 'text', VL('status'), 10), CA('availability', 'Availability', 'text', VL('availability'), 11),
    CA('ask_wd', 'Weekday ask score', 'int', 'IF(AND({col:status}=%s,OR({col:availability}=%s,{col:availability}=%s)),ROUND({col:hours_year}*2,0)*1000+(1000-VALUE(RIGHT({col:volunteer_id},3))),0)' % (ACTIVE, tok('avail', 'Weekdays'), tok('avail', 'Flexible')), 10),
    CA('ask_we', 'Weekend ask score', 'int', 'IF(AND({col:status}=%s,OR({col:availability}=%s,{col:availability}=%s)),ROUND({col:hours_year}*2,0)*1000+(1000-VALUE(RIGHT({col:volunteer_id},3))),0)' % (ACTIVE, tok('avail', 'Weekends'), tok('avail', 'Flexible')), 10),
    CA('rank_year', 'Rank this year', 'int', 'IF({col:hours_year}>0,COUNTIFS({range:hours_by_volunteer.hours_year},">"&{col:hours_year})+1,"")', 8),
    CA('phone', 'Phone', 'text', VL('phone'), 18), CA('role', 'Role', 'text', VL('role'), 14),
    CA('value_year', 'Value this year', 'money', '{col:hours_year}*{set:volunteer_hour_value}', 11), CA('value_total', 'Value in all', 'money', '{col:hours_total}*{set:volunteer_hour_value}', 11), ORG()],
    D.hours_vol_d(), 500, [A('hours_year', '>= 100', 'good')]))
# 8 hours by program and month ----------------------------------------------
tables.append(T('hours_program_month', 'Hours by Program and Month', 'Hours, shifts and value by program and month',
    'One row per month and program: the hours worked and the shifts come from the shift log plus the totals carried in from before the log starts; the value at your own hour value fills in.', [
    C('month', 'Month', 'date', 11, required=True), LST('program', 'Program or area', 'sprog', 22), C('arch_hours', 'Hours before the log', 'num', 10), C('arch_shifts', 'Shifts before the log', 'int', 9),
    CA('hours', 'Hours', 'hours', '{col:arch_hours}+SUMIFS({range:shifts.worked_hours},{range:shifts.program},{col:program},{range:shifts.month},{col:month})', 9),
    CA('shifts_n', 'Shifts worked', 'int', '{col:arch_shifts}+COUNTIFS({range:shifts.program},{col:program},{range:shifts.month},{col:month},{range:shifts.status},%s)' % WORKED, 8),
    CA('value', 'Value, your setting', 'money', '{col:hours}*{set:volunteer_hour_value}', 12),
    CA('year_hours', 'Hours this year, this program', 'hours', 'SUMIFS({range:hours_program_month.hours},{range:hours_program_month.program},{col:program},{range:hours_program_month.month},">="&%s)' % YS, 10)], D.hours_pm_d(), 200))
# 9 hours value --------------------------------------------------------------
tables.append(T('hours_value', 'Hours Value', 'Hours and their value month by month',
    'One row per month: type the hours from before the log starts; the hours worked, their value at your own hour value, the same month last year and the active volunteers fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('arch_hours', 'Hours before the log', 'num', 10), C('arch_shifts', 'Shifts before the log', 'int', 9),
    CA('hours', 'Hours', 'hours', '{col:arch_hours}+SUMIFS({range:shifts.worked_hours},{range:shifts.month},{col:month})', 9),
    CA('value', 'Value, your setting', 'money', '{col:hours}*{set:volunteer_hour_value}', 12), CA('shifts_n', 'Shifts worked', 'int', '{col:arch_shifts}+COUNTIFS({range:shifts.month},{col:month},{range:shifts.status},%s)' % WORKED, 8),
    CA('hours_ly', 'Same month last year', 'hours', 'SUMIFS({range:hours_value.hours},{range:hours_value.month},EDATE({col:month},-12))', 9),
    CA('change', 'Change on last year', 'pct', 'IF({col:hours_ly}>0,{col:hours}/{col:hours_ly}-1,"")', 9),
    CA('active_n', 'Active volunteers', 'int', 'COUNTIFS({range:volunteers.status},%s,{range:volunteers.volunteer_id},"<>")' % ACTIVE, 8),
    CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('chair_phone', 'Board chair phone', D.CHAIR_PHONE), ORG()], D.hours_value_d(), 50))
# 10 volunteer retention by role -------------------------------------------------
def RC(col): return 'IF({col:year}=YEAR({today}),COUNTIFS({range:hours_by_volunteer.role},{col:role},{range:hours_by_volunteer.hours_year},">0"%s),IF({col:year}=YEAR({today})-1,COUNTIFS({range:hours_by_volunteer.role},{col:role},{range:hours_by_volunteer.hours_last},">0"%s),COUNTIFS({range:hours_by_volunteer.role},{col:role},{range:hours_by_volunteer.hours_prev},">0"%s)))' % ((col,) * 3 if False else ('', '', ''))
tables.append(T('vol_retention', 'Volunteer Retention', 'Active and kept volunteers by year and role',
    'One row per year and role: volunteers with hours in that year and how many of them also worked the year before; both fill in from Hours by Volunteer.', [
    C('year', 'Year', 'int', 8, required=True), LST('role', 'Role', 'vrole', 16),
    CA('active', 'Active', 'int', RC(''), 9),
    CA('kept', 'Kept from last year', 'int', 'IF({col:year}=YEAR({today}),COUNTIFS({range:hours_by_volunteer.role},{col:role},{range:hours_by_volunteer.hours_year},">0",{range:hours_by_volunteer.hours_last},">0"),IF({col:year}=YEAR({today})-1,COUNTIFS({range:hours_by_volunteer.role},{col:role},{range:hours_by_volunteer.hours_last},">0",{range:hours_by_volunteer.hours_prev},">0"),0))', 9)],
    D.retention_d(), 60))
# 11 lapsed volunteers -----------------------------------------------------
HV = lambda c: LKN('hours_by_volunteer.' + c, 'hours_by_volunteer.volunteer_id', 'volunteer_id')
tables.append(T('lapsed', 'Lapsed Volunteers', 'Lapsed volunteers ranked by hours given with a next step',
    'One row per lapsed volunteer: type the volunteer ID; the last shift, hours given, days since, rank and the next step (call, write or let go) fill in by themselves.', [
    C('volunteer_id', 'Volunteer ID', 'text', 10, required=True), CA('volunteer', 'Volunteer', 'text', LKT('volunteers.name', 'volunteers.volunteer_id', 'volunteer_id'), 24),
    CA('phone', 'Phone', 'text', LKT('volunteers.phone', 'volunteers.volunteer_id', 'volunteer_id'), 18), CA('role', 'Role', 'text', LKT('volunteers.role', 'volunteers.volunteer_id', 'volunteer_id'), 14),
    CA('last_shift', 'Last shift', 'date', LKD('hours_by_volunteer.last_shift', 'hours_by_volunteer.volunteer_id', 'volunteer_id'), 11), CA('hours_given', 'Hours given', 'hours', HV('hours_total'), 9),
    CA('days_since', 'Days since', 'int', 'IF(ISNUMBER({col:last_shift}),{today}-{col:last_shift},"")', 8),
    CA('score', 'Rank score (hours given)', 'int', 'ROUND({col:hours_given}*2,0)*1000+(1000-VALUE(RIGHT({col:volunteer_id},3)))', 10), CA('rank', 'Rank', 'int', 'COUNTIFS({range:lapsed.score},">"&{col:score})+1', 7),
    CA('next_step', 'Next step', 'text', 'IF({col:hours_given}>={set:call_hours},%s,IF({col:hours_given}>={set:write_hours},%s,%s))' % (ck('Call'), ck('Write'), ck('Let go')), 10),
    CA('lapsed_n', 'Lapsed volunteers', 'int', 'COUNTIFS({range:lapsed.volunteer_id},"<>")', 8), CA('lapsed_hours', 'Hours they gave', 'hours', 'SUM({range:lapsed.hours_given})', 9),
    CPH('coord_phone', 'Volunteer coordinator phone', D.COORD_PHONE), ORG()],
    D.lapsed_d(), 250, [A('next_step', '= ' + ck('Call'), 'bad'), A('next_step', '= ' + ck('Write'), 'warn')]))
# 12 volunteers who also give ------------------------------------------------
tables.append(T('givers', 'Volunteer Givers', 'Volunteers who are also donors, with the money given',
    'One row per volunteer who is also a donor: type the volunteer ID and copy the total given, the gifts and the last gift from your donor book; the name, phone and hours fill in.', [
    C('volunteer_id', 'Volunteer ID', 'text', 10, required=True), CA('volunteer', 'Volunteer', 'text', LKT('volunteers.name', 'volunteers.volunteer_id', 'volunteer_id'), 24),
    CA('phone', 'Phone', 'text', LKT('volunteers.phone', 'volunteers.volunteer_id', 'volunteer_id'), 18), CA('donor_id', 'Donor ID', 'text', LKT('volunteers.donor_id', 'volunteers.volunteer_id', 'volunteer_id'), 10),
    C('total_given', 'Total given', 'money', 12), C('gifts', 'Gifts', 'int', 7), C('last_gift', 'Last gift', 'date', 11),
    CA('hours_given', 'Hours worked', 'hours', LKN('volunteers.hours_worked', 'volunteers.volunteer_id', 'volunteer_id'), 9),
    CA('recent', 'Gave recently', 'int', 'IF(AND(ISNUMBER({col:last_gift}),{col:last_gift}>={today}-{set:thank_days}),1,0)', 8),
    CA('givers_n', 'Volunteers who give', 'int', 'COUNTIFS({range:givers.volunteer_id},"<>")', 8), CA('givers_total', 'Money they gave', 'money', 'SUM({range:givers.total_given})', 12),
    CPH('dev_phone', 'Development manager phone', D.DEV_PHONE), ORG()], D.givers_d(), 200))
# 13 new volunteers by month ---------------------------------------------------
tables.append(T('new_by_month', 'New Volunteers by Month', 'New volunteers each month and how many are still active',
    'One row per month: the volunteers who joined and how many of them are still active fill in from the roster.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('joined', 'Joined', 'int', 'COUNTIFS({range:volunteers.joined},">="&{col:month},{range:volunteers.joined},"<"&EDATE({col:month},1))', 8),
    CA('still_active', 'Still active', 'int', 'COUNTIFS({range:volunteers.joined},">="&{col:month},{range:volunteers.joined},"<"&EDATE({col:month},1),{range:volunteers.status},%s)' % ACTIVE, 8),
    CA('kept_share', 'Share still active', 'pct', 'IF({col:joined}>0,{col:still_active}/{col:joined},0)', 9)], D.new_by_month_d(), 50))
# 14 availability by weekday ---------------------------------------------------
WE = lambda: 'OR({col:weekday}=%s)' % SAT
tables.append(T('availability_view', 'Availability by Weekday', 'Volunteers available against the gap by weekday and shift',
    'One row per weekday and shift: the active volunteers available, the slots held in the last 90 days, the average gap and the gap ahead fill in; the cover shows whether you have enough people to ask.', [
    LST('weekday', 'Weekday', 'wday', 12, required=True), LST('shift', 'Shift', 'shift', 10),
    CA('available', 'Volunteers available', 'int', 'COUNTIFS({range:volunteers.status},%s,{range:volunteers.availability},%s)+COUNTIFS({range:volunteers.status},%s,{range:volunteers.availability},IF(%s,%s,%s))' % (ACTIVE, tok('avail', 'Flexible'), ACTIVE, WE(), tok('avail', 'Weekends'), tok('avail', 'Weekdays')), 9),
    CA('slots_held', 'Slots, last 90 days', 'int', 'COUNTIFS({range:slots.weekday},{col:weekday},{range:slots.shift},{col:shift},{range:slots.date},">="&({today}-90),{range:slots.date},"<="&{today})', 9),
    CA('avg_gap', 'Average gap a slot', 'num', 'IF({col:slots_held}>0,SUMIFS({range:slots.gap},{range:slots.weekday},{col:weekday},{range:slots.shift},{col:shift},{range:slots.date},">="&({today}-90),{range:slots.date},"<="&{today})/{col:slots_held},0)', 9),
    CA('gap_ahead', 'Gap ahead', 'int', 'SUMIFS({range:slots.gap},{range:slots.weekday},{col:weekday},{range:slots.shift},{col:shift},{range:slots.date},">"&{today})', 8),
    CA('cover', 'People available for each person short', 'num', 'IF({col:gap_ahead}>0,ROUND({col:available}/{col:gap_ahead},1),"")', 10),
    CA('state', 'Cover', 'text', 'IF({col:gap_ahead}=0,%s,IF({col:available}>={col:gap_ahead}*3,%s,%s))' % (ck('No gap'), ck('Enough people'), ck('Recruit')), 14)], D.availability_d(), 50,
    [A('state', '= ' + ck('Recruit'), 'warn')]))
# 15 members -------------------------------------------------------------------
def DP(extra=''): return 'COUNTIFS({range:dues_payments.member_id},{col:member_id}%s)' % extra
tables.append(T('members', 'Members', 'Members with level, due date and status',
    'One row per member: contact, level, joined date, due date, last payment, status and yearly dues; the days to due, the level totals and the overdue count fill in by themselves.', [
    C('member_id', 'Member ID', 'text', 10, required=True), C('donor_id', 'Donor ID', 'text', 10), C('member', 'Member', 'text', 24), C('phone', 'Phone', 'text', 18), LST('level', 'Level', 'mlevel', 11),
    C('joined', 'Joined', 'date', 11), C('due_date', 'Due date', 'date', 11), C('last_paid', 'Last paid', 'date', 11), LST('status', 'Status', 'dues', 10), C('annual_dues', 'Annual dues', 'money', 12),
    CA('days_to_due', 'Days to due', 'int', 'IF(ISNUMBER({col:due_date}),{col:due_date}-{today},"")', 8),
    CA('payments_n', 'Payments recorded', 'int', DP(), 8), CA('level_n', 'Members at this level', 'int', 'COUNTIFS({range:members.level},{col:level},{range:members.status},"<>"&%s)' % tok('dues', 'Lapsed'), 9),
    CA('level_dues', 'Dues of this level', 'money', 'SUMIFS({range:members.annual_dues},{range:members.level},{col:level},{range:members.status},"<>"&%s)' % tok('dues', 'Lapsed'), 12),
    CA('dues_this', 'Dues paid this year', 'money', 'SUMIFS({range:dues_payments.amount},{range:dues_payments.member_id},{col:member_id},{range:dues_payments.year},YEAR({today}))', 12),
    CA('dues_last', 'Dues paid last year', 'money', 'SUMIFS({range:dues_payments.amount},{range:dues_payments.member_id},{col:member_id},{range:dues_payments.year},YEAR({today})-1)', 12),
    CA('dues_prev', 'Dues paid the year before', 'money', 'SUMIFS({range:dues_payments.amount},{range:dues_payments.member_id},{col:member_id},{range:dues_payments.year},YEAR({today})-2)', 12),
    CA('overdue_n', 'Members overdue', 'int', 'COUNTIFS({range:members.status},%s,{range:members.member_id},"<>")' % tok('dues', 'Overdue'), 8), CA('event_on', 'Next members event', 'date', '{set:members_event_on}', 11),
    CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), CPH('dev_phone', 'Development manager phone', D.DEV_PHONE), ORG()],
    D.members_d(), 300, [A('status', '= ' + tok('dues', 'Overdue'), 'bad'), A('status', '= ' + tok('dues', 'Lapsed'), 'warn'), A('status', '= ' + tok('dues', 'Paid'), 'good')]))
# 16 dues payments ---------------------------------------------------------------
RN = 'COUNTIFS({range:dues_payments.member_id},{col:member_id},{range:dues_payments.date},">"&{col:date},{range:dues_payments.date},"<="&({col:due_again}+{set:renew_grace_days}))'
tables.append(T('dues_payments', 'Dues Payments', 'Every dues payment and the renewal that followed',
    'One row per dues payment: member, date, amount, year, method and level; the date it falls due again and whether the member renewed on time fill in by themselves.', [
    C('dues_id', 'Dues ID', 'text', 10, required=True), C('member_id', 'Member ID', 'text', 10), C('member', 'Member', 'text', 24), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('amount', 'Amount', 'money', 11),
    C('year', 'Year', 'int', 8), LST('method', 'Method', 'dmethod', 16), LST('level', 'Level', 'mlevel', 11),
    CA('due_again', 'Due again on', 'date', 'EDATE({col:date},12)', 11), CA('due_year', 'Due again in', 'int', 'YEAR({col:due_again})', 8),
    CA('due_n', 'Renewal now due', 'int', 'IF({col:due_again}+{set:renew_grace_days}<={today},1,0)', 8),
    CA('renewed', 'Renewed on time', 'int', 'IF({col:due_n}=1,IF(%s>0,1,0),0)' % RN, 8)], D.dues_d(), 400, [A('renewed', '= 1', 'good')]))
# 17 member levels ----------------------------------------------------------------
tables.append(T('member_levels', 'Member Levels', 'Levels with the yearly dues and the benefits',
    'One row per member level: the yearly dues and what a member at this level gets; the demo members use Friend, Supporter and Patron.', [
    C('level', 'Level', 'text', 14, required=True), C('annual_dues', 'Annual dues', 'money', 12), C('benefits', 'Benefits', 'text', 40)], D.levels_d(), 50))
# 18 renewals due ---------------------------------------------------------------------
MB = lambda c: LKT('members.' + c, 'members.member_id', 'member_id')
tables.append(T('renewals', 'Renewals Due', 'Members to renew, ranked by dues with the action to take',
    'One row per member whose dues are due, overdue or lapsed: type the member ID; the level, phone, due date, days to due, rank and the action (send notice, call or win back) fill in by themselves.', [
    C('member_id', 'Member ID', 'text', 10, required=True), CA('member', 'Member', 'text', MB('member'), 24), CA('phone', 'Phone', 'text', MB('phone'), 18), CA('level', 'Level', 'text', MB('level'), 11),
    CA('due_date', 'Due date', 'date', LKD('members.due_date', 'members.member_id', 'member_id'), 11), CA('days_to_due', 'Days to due', 'int', 'IF(ISNUMBER({col:due_date}),{col:due_date}-{today},"")', 8),
    CA('status', 'Status', 'text', MB('status'), 10), CA('annual_dues', 'Annual dues', 'money', LKN('members.annual_dues', 'members.member_id', 'member_id'), 12),
    CA('score', 'Rank score (dues amount)', 'int', 'ROUND({col:annual_dues},0)*1000+(500-VALUE(RIGHT({col:member_id},3)))', 10), CA('rank', 'Rank by dues', 'int', 'COUNTIFS({range:renewals.score},">"&{col:score})+1', 8),
    CA('action', 'Action', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,%s,%s))' % (tok('dues', 'Lapsed'), ck('Lapsing'), tok('dues', 'Overdue'), ck('Call'), ck('Send notice')), 12),
    CA('due30_n', 'Renewals due in 30 days', 'int', 'COUNTIFS({range:renewals.days_to_due},">=0",{range:renewals.days_to_due},"<=30")', 8),
    CA('due30_money', 'Dues due in 30 days', 'money', 'SUMIFS({range:renewals.annual_dues},{range:renewals.days_to_due},">=0",{range:renewals.days_to_due},"<=30")', 12),
    CPH('dev_phone', 'Development manager phone', D.DEV_PHONE), ORG()], D.renewals_d(), 120,
    [A('action', '= ' + ck('Call'), 'bad'), A('action', '= ' + ck('Lapsing'), 'warn')]))
# 19 dues forecast ---------------------------------------------------------------------
tables.append(T('dues_forecast', 'Dues by Month', 'Dues falling due each month for the next 12 months',
    'One row per month: renewals falling due, their dues, your estimate at the renewal rate you set on Membership Switch, the same month last year and the dues received so far.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('renewals_due', 'Renewals due', 'int', 'COUNTIFS({range:members.due_date},">="&{col:month},{range:members.due_date},"<"&EDATE({col:month},1))', 8),
    CA('expected_dues', 'Dues falling due', 'money', 'SUMIFS({range:members.annual_dues},{range:members.due_date},">="&{col:month},{range:members.due_date},"<"&EDATE({col:month},1))', 12),
    CA('your_estimate', 'Your estimate', 'money', 'ROUND({col:expected_dues}*%s*%s,0)' % (MSW('Share of due members who renew'), MSW('Use membership pages')), 12),
    CA('last_year', 'Dues received, same month last year', 'money', 'SUMIFS({range:dues_payments.amount},{range:dues_payments.date},">="&EDATE({col:month},-12),{range:dues_payments.date},"<"&EDATE({col:month},-11))', 12),
    CA('received', 'Dues received this month', 'money', 'SUMIFS({range:dues_payments.amount},{range:dues_payments.date},">="&{col:month},{range:dues_payments.date},"<"&EDATE({col:month},1))', 12),
    CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), CPH('dev_phone', 'Development manager phone', D.DEV_PHONE), ORG()], D.forecast_d(), 50))
# 20 membership switch ------------------------------------------------------------------
tables.append(T('member_switch', 'Membership Switch', 'Membership pages on or off, renewal rate and notice days',
    'Five settings for the membership side: 1 or 0 to show it, notice days, the share who renew (your estimate), days before a member counts as lapsed and your member goal.', [
    LST('item', 'Item', 'mitem', 34, required=True), C('setting', 'Setting', 'num', 10), C('note', 'Note', 'text', 50)], D.switch_d(), 50))
assert len(tables) == 20, len(tables)
