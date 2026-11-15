"""Car rental suite part 6: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr6_lists import *
import cr6_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def CENTER(): return CA('company', 'Business', 'text', '{set:company}', 22)
def PH(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
CNC = tok('bstatus', 'Cancelled'); NSH = tok('bstatus', 'No-show')
OWND = tok('paytype', 'Owner draw'); HRLY = tok('paytype', 'Hourly')
W = lambda d: '{today}-%s' % d

settings = [
    S('company', 'Your business name', 'text', COMPANY),
    S('buffer_min', 'Buffer: minutes a car should be ready within (set your own)', 'int', 90),
    S('tight_min', 'Tight: spare minutes wanted before the next pickup', 'int', 60),
    S('detailer_rate', 'Detailer pay for one hour', 'money', 17.0),
    S('driver_rate', 'Driver pay for one hour', 'money', 16.0),
    S('run_mile_cost', 'Fuel or charge cost of one run mile', 'money', 0.2),
    S('hours_limit', 'Longest shift in hours before overtime, set your own', 'num', 5.5),
    S('max_days_week', 'Most days one person works in a week', 'int', 6),
    S('clash_min', 'Minutes a driver needs between two runs', 'int', 15),
    S('manager_hours', 'Manager hours counted as cover on a weekday', 'num', 3),
    S('counter_min', 'Counter minutes for one pickup or return', 'int', 20),
    S('employer_cost_pct', 'Employer costs on top of pay', 'pct', 0.10),
    S('cost_target', 'Hours cost per rental you want to stay under, set your own', 'money', 55),
    S('cleaning_fee', 'Cleaning fee charged for a very dirty car', 'money', 45),
    S('window_days', 'Days of runs used for zone and cost figures', 'int', 90),
    S('task_days', 'Days of the task log used for scores', 'int', 7),
    S('pay_tolerance', 'Pay difference allowed before a line is checked', 'money', 1.0),
    S('gap_tol', 'Hours short before a day counts as short of staff', 'num', 0.5),
]
assert 3 <= len(settings) <= 20

tables = []
SL = lambda c: R('turnaround', c)
# 1 turnaround ---------------------------------------------------------------
tables.append(T('turnaround', 'Turnaround Board', 'Turnaround and cleaning board',
    'One row per returned car: return and cleaning times, detailer, cost and next pickup; slack, verdict (ready, tight or late) and clean-by time fill in. Turnaround: time from a return to the next pickup.', [
    C('turn_id', 'Turn ID', 'text', 10, required=True), C('booking_id', 'Booking', 'text', 10), C('vehicle', 'Vehicle', 'text', 22), LST('class', 'Class', 'class', 12), C('return_date', 'Return date', 'date', 11),
    LST('weekday', 'Weekday', 'wday', 11), C('returned_time', 'Returned', 'time', 9), C('clean_date', 'Clean date', 'date', 11), C('clean_start', 'Clean start', 'time', 9), C('clean_end', 'Clean end', 'time', 9),
    LST('cleaner', 'Detailer', 'cleaner', 16), C('clean_minutes', 'Clean minutes', 'int', 9), C('clean_cost', 'Clean cost', 'money', 11), C('dirty', 'Very dirty', 'bool', 8),
    C('next_pickup', 'Next pickup', 'date', 11), C('next_pickup_time', 'Pickup time', 'time', 9),
    CA('slack_minutes', 'Slack minutes', 'int', 'IF({col:next_pickup}>0,ROUND((({col:next_pickup}+{col:next_pickup_time})-({col:clean_date}+{col:clean_end}))*1440,0),"")', 9),
    CA('turn_minutes', 'Return to ready, minutes', 'int', 'ROUND((({col:clean_date}+{col:clean_end})-({col:return_date}+{col:returned_time}))*1440,0)', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:slack_minutes}="",%s,IF({col:slack_minutes}<0,%s,IF({col:slack_minutes}<{set:tight_min},%s,%s)))' % (va('No pickup booked'), va('Late, clean first'), va('Tight, under the minimum'), va('Ready on time')), 24),
    CA('ready_by', 'Clean by', 'time', 'IF({col:next_pickup}>0,MOD({col:next_pickup_time}-{set:tight_min}/1440,1),"")', 9),
    CA('risk_key', 'Risk rank key', 'num', 'IF(AND({col:next_pickup}>={today},ISNUMBER({col:slack_minutes})),{col:slack_minutes}+COUNTIFS(%s,"<"&{col:turn_id})/100000,"")' % SL('turn_id'), 10),
    CA('queue_key', 'Queue key', 'num', 'IF({col:next_pickup}>0,{col:next_pickup}+{col:next_pickup_time},"")', 10),
    CA('day_pos', 'Queue position key', 'num', 'IF({col:next_pickup}>0,{col:return_date}*100+COUNTIFS(%s,{col:return_date},%s,"<"&{col:queue_key})+COUNTIFS(%s,{col:return_date},%s,{col:queue_key},%s,"<"&{col:turn_id})+1,"")'
       % (SL('return_date'), SL('queue_key'), SL('return_date'), SL('queue_key'), SL('turn_id')), 10),
    CA('cars_today', 'Cars cleaned that day', 'int', 'COUNTIFS(%s,{col:cleaner},%s,{col:clean_date})' % (SL('cleaner'), SL('clean_date')), 9),
    CA('risk_now', 'Cars at risk, today and tomorrow', 'int', 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+1),%s,"<"&{set:tight_min})' % (SL('next_pickup'), SL('next_pickup'), SL('slack_minutes')), 9),
    CA('tight_share_lm', 'Tight or late share, last month', 'pct',
       'IFERROR(COUNTIFS(%s,">="&EDATE(%s,-1),%s,"<"&%s,%s,"<"&{set:tight_min})/COUNTIFS(%s,">="&EDATE(%s,-1),%s,"<"&%s,%s,">=-100000"),0)' % (SL('return_date'), MS, SL('return_date'), MS, SL('slack_minutes'), SL('return_date'), MS, SL('return_date'), MS, SL('slack_minutes')), 10),
    CA('detailer_phone', 'Detailer phone', 'text', LKT('team.phone', 'team.name', 'cleaner'), 18), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), PH('owner_phone', 'Owner phone', D.OWNER_PHONE),
    PH('mechanic_phone', 'Mechanic phone', D.MECHANIC_PHONE), CENTER()],
    D.turnaround_rows_d(), 1500, [A('verdict', '= ' + va('Late, clean first'), 'bad'), A('verdict', '= ' + va('Tight, under the minimum'), 'warn'), A('verdict', '= ' + va('Ready on time'), 'good')]))
# 2 delivery runs ---------------------------------------------------------------
DR = lambda c: R('delivery_runs', c)
def GAPN(): return '{set:clash_min}/1440'
CL = lambda drv: 'COUNTIFS(%s,%s,%s,{col:date},%s,"<"&({col:end_time}+%s),%s,">"&({col:start_time}-%s))' % (DR('driver'), drv, DR('date'), DR('start_time'), GAPN(), DR('end_time'), GAPN())
JUN = '{list:driver.jun_park}'; RAV = '{list:driver.ravi_chandran}'
ZP = lambda: 'IFERROR((SUMIFS(%s,%s,{col:location},%s,">="&({today}-{set:window_days}),%s,"<="&{today})-SUMIFS(%s,%s,{col:location},%s,">="&({today}-{set:window_days}),%s,"<="&{today}))/COUNTIFS(%s,{col:location},%s,">="&({today}-{set:window_days}),%s,"<="&{today}),0)' % (
    DR('fee_charged'), DR('location'), DR('date'), DR('date'), DR('driver_cost'), DR('location'), DR('date'), DR('date'), DR('location'), DR('date'), DR('date'))
tables.append(T('delivery_runs', 'Delivery Runs', 'Delivery and collection runs',
    'One row per run: date, booking, vehicle, kind, zone, driver, start time, minutes, miles, fee and driver cost; profit, end time, clashes, the other driver and the zone profit fill in.', [
    C('run_id', 'Run ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('booking_id', 'Booking', 'text', 10), C('vehicle', 'Vehicle', 'text', 22), C('renter', 'Renter', 'text', 14), C('phone', 'Renter phone', 'text', 18),
    LST('kind', 'Kind', 'runkind', 11), LST('location', 'Zone', 'zone', 16), LST('driver', 'Driver', 'driver', 16), C('start_time', 'Start', 'time', 9), C('minutes', 'Minutes', 'int', 9), C('miles', 'Miles', 'int', 8),
    C('fee_charged', 'Fee charged', 'money', 11), C('driver_cost', 'Driver cost', 'money', 11), C('delay_min', 'Minutes late', 'int', 9), LST('status', 'Status', 'runstatus', 10),
    CA('profit', 'Profit', 'money', '{col:fee_charged}-{col:driver_cost}', 10), CA('end_time', 'End', 'time', '{col:start_time}+{col:minutes}/1440', 9),
    CA('order_key', 'Order key', 'num', 'IF(AND({col:date}>={today},{col:date}<={today}+1),({col:date}-{today})*1440+ROUND({col:start_time}*1440,0)+COUNTIFS(%s,"<"&{col:run_id})/100000,"")' % DR('run_id'), 10),
    CA('clash', 'Clashing runs', 'int', CL('{col:driver}') + '-1', 8),
    CA('other_driver', 'Other driver', 'text', 'IF({col:driver}=%s,%s,%s)' % (JUN, RAV, JUN), 16),
    CA('other_free', 'Other driver free', 'int', 'IF(%s=0,1,0)' % CL('{col:other_driver}'), 8),
    CA('fix_key', 'Fix key', 'num', 'IF(AND({col:clash}>0,{col:date}>={today}),{col:date}+{col:start_time}+COUNTIFS(%s,"<"&{col:run_id})/10000000,"")' % DR('run_id'), 10),
    CA('drv_key', 'Driver fix key', 'num', 'IF(AND({col:clash}>0,{col:date}>={today}),IF({col:driver}=%s,1,2)*100000+{col:date}+{col:start_time}+COUNTIFS(%s,"<"&{col:run_id})/10000000,"")' % (JUN, DR('run_id')), 10),
    CA('runs_day', 'Runs of the driver that day', 'int', 'COUNTIFS(%s,{col:driver},%s,{col:date})' % (DR('driver'), DR('date')), 9),
    CA('zone_cover', 'Zone fees against cost', 'pct', 'IFERROR(SUMIFS(%s,%s,{col:location},%s,">="&({today}-{set:window_days}),%s,"<="&{today})/SUMIFS(%s,%s,{col:location},%s,">="&({today}-{set:window_days}),%s,"<="&{today}),0)'
       % (DR('fee_charged'), DR('location'), DR('date'), DR('date'), DR('driver_cost'), DR('location'), DR('date'), DR('date')), 10),
    CA('zone_profit', 'Zone profit per run', 'money', ZP(), 10),
    CA('driver_phone', 'Driver phone', 'text', LKT('team.phone', 'team.name', 'driver'), 18), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), PH('owner_phone', 'Owner phone', D.OWNER_PHONE), CENTER()],
    D.RUNS, 2000, [A('status', '= ' + tok('runstatus', 'Planned'), 'warn'), A('clash', '> 0', 'bad'), A('profit', '< 0', 'bad')]))
# 3 zones ---------------------------------------------------------------------
tables.append(T('zones', 'Delivery Zones', 'Delivery zones with the fee for one leg',
    'One row per location: the fee for one leg and the minutes a run takes; fees are before any sales tax and the settings drive the cost checks.', [
    LST('location', 'Location', 'location', 18, required=True), C('fee_leg', 'Fee per leg', 'money', 11), C('run_minutes', 'Run minutes', 'int', 10)], D.zones_d(), 50))
# 4 zone profit -----------------------------------------------------------------
tables.append(T('zone_profit', 'Zone Profit', 'Profit per run by zone',
    'One row per delivery zone: runs and profit per run (fees minus driver time and fuel) over the days set on the Start sheet; they fill in by themselves.', [
    LST('zone', 'Zone', 'location', 18, required=True),
    CA('runs', 'Runs', 'int', 'COUNTIFS(%s,{col:zone},%s,">="&({today}-{set:window_days}),%s,"<="&{today})' % (DR('location'), DR('date'), DR('date')), 9),
    CA('profit_run', 'Profit per run', 'money', 'IF({col:runs}=0,"",(SUMIFS(%s,%s,{col:zone},%s,">="&({today}-{set:window_days}),%s,"<="&{today})-SUMIFS(%s,%s,{col:zone},%s,">="&({today}-{set:window_days}),%s,"<="&{today}))/{col:runs})'
       % (DR('fee_charged'), DR('location'), DR('date'), DR('date'), DR('driver_cost'), DR('location'), DR('date'), DR('date')), 12)],
    [dict(zone=key('location', z)) for z in LOCATIONS], 50))
# 5 shifts -----------------------------------------------------------------------
SH = lambda c: R('shifts', c)
tables.append(T('shifts', 'Shifts', 'Shifts by staff member',
    'One row per shift: date, staff member, role, task, start, end, hours and rate; cost, overtime, days worked that week and the week totals fill in. Planned shifts are the roster.', [
    C('shift_id', 'Shift ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('week', 'Week of', 'date', 11), C('month', 'Month', 'date', 11), LST('weekday', 'Weekday', 'wday', 11),
    LST('staff', 'Staff member', 'shiftstaff', 16), LST('role', 'Role', 'payrole', 16), LST('task', 'Task', 'task', 20), C('start', 'Start', 'time', 9), C('end', 'End', 'time', 9), C('hours', 'Hours', 'num', 8), C('rate', 'Rate', 'num', 9),
    CA('cost', 'Cost', 'money', '{col:hours}*{col:rate}', 10), CA('overtime', 'Overtime hours', 'num', 'MAX(0,{col:hours}-{set:hours_limit})', 9),
    CA('days_week', 'Days worked that week', 'int', 'COUNTIFS(%s,{col:staff},%s,{col:week})' % (SH('staff'), SH('week')), 9),
    CA('week_hours', 'Hours of the week', 'num', 'SUMIFS(%s,%s,{col:staff},%s,{col:week})' % (SH('hours'), SH('staff'), SH('week')), 9),
    CA('week_total', 'All staff hours of the week', 'num', 'SUMIFS(%s,%s,{col:week})' % (SH('hours'), SH('week')), 10),
    CA('staff_phone', 'Staff phone', 'text', LKT('team.phone', 'team.name', 'staff'), 18), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), CENTER()],
    D.shifts_d(), 1500, [A('overtime', '> 0', 'warn')]))
# 6 pay ----------------------------------------------------------------------------
PY = lambda c: R('pay', c)
tables.append(T('pay', 'Pay', 'Pay by staff member and month',
    'One row per staff member and month: hours, gross pay and employer costs; the total, the pay run of the month and the contact phones fill in. Owner draw is shown but left out of staff pay.', [
    C('pay_id', 'Pay ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('staff', 'Staff member', 'staff', 16), LST('role', 'Role', 'payrole', 16), LST('pay_type', 'Pay type', 'paytype', 11),
    C('hours', 'Hours', 'num', 8), C('gross', 'Gross pay', 'money', 11), C('employer_cost', 'Employer cost', 'money', 11), LST('status', 'Status', 'paystatus', 10),
    CA('total', 'Total', 'money', '{col:gross}+{col:employer_cost}', 11),
    CA('month_total', 'Staff pay run of the month', 'money', 'SUMIFS(%s,%s,{col:month},%s,"<>"&%s)' % (PY('total'), PY('month'), PY('pay_type'), OWND), 12),
    CA('month_gross', 'Gross of the month', 'money', 'SUMIFS(%s,%s,{col:month},%s,"<>"&%s)' % (PY('gross'), PY('month'), PY('pay_type'), OWND), 12),
    CA('month_employer', 'Employer cost of the month', 'money', 'SUMIFS(%s,%s,{col:month},%s,"<>"&%s)' % (PY('employer_cost'), PY('month'), PY('pay_type'), OWND), 12),
    CA('month_hours', 'Hours of the month', 'num', 'SUMIFS(%s,%s,{col:month})' % (PY('hours'), PY('month')), 9),
    CA('staff_phone', 'Staff phone', 'text', LKT('team.phone', 'team.name', 'staff'), 18), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), PH('owner_phone', 'Owner phone', D.OWNER_PHONE),
    PH('bookkeeper_phone', 'Bookkeeper phone', D.BOOKKEEPER_PHONE), PH('accountant_phone', 'Accountant phone', D.ACCOUNTANT_PHONE), CENTER()],
    D.pay_d(), 400, [A('status', '= ' + tok('paystatus', 'Accruing'), 'warn')]))
# 7 team ----------------------------------------------------------------------------
tables.append(T('team', 'Team', 'Staff and outside contacts',
    'One row per staff member or outside contact: role, pay type, phone, e-mail, hours a week, salary or hourly rate and area; hours of the last 30 days fill in.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 18), C('team', 'Team', 'text', 12), LST('pay_type', 'Pay type', 'paytype', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'int', 11), C('hourly_rate', 'Hourly rate', 'num', 10), C('area', 'Area', 'text', 30),
    CA('hours_30d', 'Shift hours, last 30 days', 'num', 'SUMIFS(%s,%s,{col:name},%s,">="&({today}-30),%s,"<="&{today})' % (SH('hours'), SH('staff'), SH('date'), SH('date')), 11)], D.team_d(), 50))
# 8 roster by day ----------------------------------------------------------------------
BK = lambda c: R('bookings', c)
NOTX = lambda d: 'COUNTIFS(%s,%s,%s,"<>"&%s,%s,"<>"&%s)' % (BK(d), '{col:date}', BK('status'), CNC, BK('status'), NSH)
WKD = 'WEEKDAY({col:date},2)'
HRS = lambda role: 'SUMIFS(%s,%s,{col:date},%s,%s)' % (SH('hours'), SH('date'), SH('role'), tok('payrole', role))
tables.append(T('roster_day', 'Roster by Day', 'Roster by day',
    'One row per day, three weeks back and five weeks ahead: pickups, returns and runs against the hours rostered for detailers, drivers and the counter; type the first date and copy the dates down.', [
    C('date', 'Date', 'date', 11, required=True),
    CA('weekday', 'Weekday', 'text', 'CHOOSE(%s,%s)' % (WKD, ','.join(tok('wday', w) for w in WEEKDAYS)), 11),
    CA('pickups', 'Pickups', 'int', NOTX('start_date'), 8), CA('returns', 'Returns', 'int', NOTX('end_date'), 8), CA('runs', 'Runs', 'int', 'COUNTIFS(%s,{col:date})' % DR('date'), 8),
    CA('clean_hours', 'Detailer hours', 'num', HRS('Detailer'), 9), CA('drive_hours', 'Driver hours', 'num', HRS('Delivery driver'), 9),
    CA('counter_hours', 'Counter hours', 'num', '%s+IF(%s<=5,{set:manager_hours},0)' % (HRS('Booking assistant'), WKD), 9),
    CA('hours_rostered', 'Hours rostered', 'num', 'SUMIFS(%s,%s,{col:date})+IF(%s<=5,{set:manager_hours},0)' % (SH('hours'), SH('date'), WKD), 10),
    CA('staff_on', 'Staff on', 'int', 'COUNTIFS(%s,{col:date})+IF(%s<=5,1,0)' % (SH('date'), WKD), 8), PH('assistant_phone', 'Assistant phone', D.ASSISTANT_PHONE), CENTER()],
    [dict(date=x) for x in D.dates_range(-21, 34)], 120))
# 9 staff needed ----------------------------------------------------------------------
SN = lambda c: R('staff_need', c)
AVGC = 'IFERROR(AVERAGEIFS(%s,%s,">="&({today}-90)),55)' % (SL('clean_minutes'), SL('return_date'))
tables.append(T('staff_need', 'Staff Needed by Day', 'Staff needed by day',
    'One row per day: pickups, returns and runs turned into the hours needed for cleaning, delivery and the counter, against the hours rostered; the gap and the status show the days short of staff.', [
    C('date', 'Date', 'date', 11, required=True),
    CA('pickups', 'Pickups', 'int', NOTX('start_date'), 8), CA('returns', 'Returns', 'int', NOTX('end_date'), 8), CA('runs', 'Runs', 'int', 'COUNTIFS(%s,{col:date})' % DR('date'), 8),
    CA('clean_need', 'Cleaning hours needed', 'num', '{col:returns}*%s/60' % AVGC, 10),
    CA('delivery_need', 'Delivery hours needed', 'num', 'IF({col:runs}>0,MAX(2,(SUMIFS(%s,%s,{col:date})+5*{col:runs})/60+0.5),0)' % (DR('minutes'), DR('date')), 10),
    CA('counter_need', 'Counter hours needed', 'num', '({col:pickups}+{col:returns})*{set:counter_min}/60', 10),
    CA('hours_needed', 'Hours needed', 'num', '{col:clean_need}+{col:delivery_need}+{col:counter_need}', 9),
    CA('hours_rostered', 'Hours rostered', 'num', 'SUMIFS(%s,%s,{col:date})+IF(WEEKDAY({col:date},2)<=5,{set:manager_hours},0)' % (SH('hours'), SH('date')), 10),
    CA('gap', 'Gap, hours', 'num', '{col:hours_needed}-{col:hours_rostered}', 9),
    CA('status', 'Status', 'text', 'IF({col:gap}>{set:gap_tol},%s,%s)' % (vb('Short'), vb('Covered')), 10),
    CA('short_key', 'Short day key', 'num', 'IF({col:gap}>{set:gap_tol},{col:date},"")', 10),
    CA('short_days', 'Short days, next 7 days', 'int', 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<"&({today}+7))' % (SN('status'), vb('Short'), SN('date'), SN('date')), 9),
    PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), CENTER()],
    [dict(date=x) for x in D.dates_range(-21, 34)], 120, [A('status', '= ' + vb('Short'), 'bad'), A('status', '= ' + vb('Covered'), 'good')]))
# 10 task log -------------------------------------------------------------------------
TK = lambda c: R('task_log', c)
tables.append(T('task_log', 'Task Log', 'Task log by role',
    'One row per task: date, role, task, who did it and done or missed; the missed count of the role in the last days and the manager phone fill in.', [
    C('log_id', 'Log ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('role', 'Role', 'payrole', 16), LST('task', 'Task', 'taskitem', 30), C('staff', 'Staff member', 'text', 18), C('done', 'Done', 'bool', 8),
    CA('role_missed', 'Missed by the role', 'int', 'COUNTIFS(%s,{col:role},%s,%s,%s,">="&({today}-{set:task_days}))' % (TK('role'), TK('done'), NO, TK('date')), 9),
    PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), CENTER()], D.task_log_d(), 400, [A('done', '= ' + NO, 'warn')]))
# 11 tasks by role -------------------------------------------------------------------------
tables.append(T('tasks_role', 'Tasks by Role', 'Tasks done and missed by role',
    'One row per role: tasks done and tasks missed in the days set on the Start sheet; they fill in from the Task Log.', [
    LST('role', 'Role', 'payrole', 18, required=True),
    CA('tasks_done', 'Tasks done', 'int', 'COUNTIFS(%s,{col:role},%s,%s,%s,">="&({today}-{set:task_days}))' % (TK('role'), TK('done'), YES, TK('date')), 10),
    CA('tasks_missed', 'Tasks missed', 'int', 'COUNTIFS(%s,{col:role},%s,%s,%s,">="&({today}-{set:task_days}))' % (TK('role'), TK('done'), NO, TK('date')), 10)],
    [dict(role=key('payrole', r)) for r in PAY_ROLES], 50))
# 12 cleaning cost by class ---------------------------------------------------------------------
tables.append(T('clean_class', 'Cleaning Cost by Class', 'Cleaning minutes and cost by vehicle class',
    'One row per vehicle class: average clean minutes and cleaning cost per rental from the Turnaround Board.', [
    LST('class', 'Class', 'class', 14, required=True),
    CA('avg_minutes', 'Average clean minutes', 'num', 'IFERROR(AVERAGEIFS(%s,%s,{col:class}),0)' % (SL('clean_minutes'), SL('class')), 11),
    CA('cost_rental', 'Cleaning cost per rental', 'money', 'IFERROR(AVERAGEIFS(%s,%s,{col:class}),0)' % (SL('clean_cost'), SL('class')), 12)],
    [dict(**{'class': key('class', c)}) for c in CLASSES], 50))
# 13 turnaround by class ---------------------------------------------------------------------------
tables.append(T('turn_class', 'Turnaround by Class', 'Turnaround time by vehicle class',
    'One row per vehicle class: average minutes from return to ready and the share of cars not ready within the buffer on the Start sheet.', [
    LST('class', 'Class', 'class', 14, required=True),
    CA('avg_turn', 'Average minutes to ready', 'num', 'IFERROR(AVERAGEIFS(%s,%s,{col:class}),0)' % (SL('turn_minutes'), SL('class')), 11),
    CA('over_buffer', 'Share over the buffer', 'pct', 'IFERROR(COUNTIFS(%s,{col:class},%s,">"&{set:buffer_min})/COUNTIFS(%s,{col:class}),0)' % (SL('class'), SL('turn_minutes'), SL('class')), 11)],
    [dict(**{'class': key('class', c)}) for c in CLASSES], 50))
# 14 runs today and tomorrow -------------------------------------------------------------------------
K1 = 'SMALL(%s,{col:order_no})' % DR('order_key')
def RT(c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (DR(c), K1, DR('order_key'))
tables.append(T('runs_today', 'Runs Today and Tomorrow', 'Runs today and tomorrow in time order',
    'The first runs of today and tomorrow in time order; type 1, 2, 3 ... in the order column and the run, time, driver, zone and minutes fill in.', [
    C('order_no', 'Order', 'int', 8, required=True), CA('run_id', 'Run', 'text', RT('run_id'), 10), CA('day', 'Day', 'date', RT('date'), 11), CA('start_time', 'Start', 'time', RT('start_time'), 9),
    CA('driver', 'Driver', 'text', RT('driver'), 16), CA('location', 'Zone', 'text', RT('location'), 16), CA('minutes', 'Minutes', 'int', RT('minutes'), 9)],
    [dict(order_no=i) for i in range(1, D.N_TODAY_TOMORROW + 1)], 50))
# 15 run load by hour -----------------------------------------------------------------------------
HH = lambda: '%s,">="&({col:hour}/24),%s,"<"&(({col:hour}+1)/24),%s,">="&({today}-{set:window_days}),%s,"<="&{today}' % (DR('start_time'), DR('start_time'), DR('date'), DR('date'))
tables.append(T('run_hours', 'Run Load by Hour', 'Run load by hour of the day',
    'One row per hour: runs and run minutes that start in the hour over the days set on the Start sheet, and the share of all runs; they show when a second driver is needed.', [
    C('hour', 'Hour', 'int', 8, required=True), CA('runs', 'Runs', 'int', 'COUNTIFS(%s)' % HH(), 9), CA('minutes', 'Run minutes', 'int', 'SUMIFS(%s,%s)' % (DR('minutes'), HH()), 10),
    CA('share', 'Share of runs', 'pct', 'IFERROR({col:runs}/COUNTIFS(%s,">="&({today}-{set:window_days}),%s,"<="&{today}),0)' % (DR('date'), DR('date')), 10)],
    [dict(hour=h) for h in range(6, 19)], 50))
# 16 hours cost by month -----------------------------------------------------------------------------
HMN = lambda c: R('hours_month', c)
tables.append(T('hours_month', 'Hours Cost by Month', 'Hours cost per rental by month',
    'One row per month: shift hours, shift pay and rentals started; cost per rental, hours per rental, pay per hour and cleaning supplies per rental fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('hours', 'Shift hours', 'num', 10), C('pay', 'Shift pay', 'money', 11), C('rentals', 'Rentals started', 'int', 10),
    CA('supplies', 'Cleaning supplies', 'money', 'SUMIFS(%s,%s,{col:month})' % (R('supplies', 'cost'), R('supplies', 'month')), 11),
    CA('cost_rental', 'Hours cost per rental', 'money', 'IFERROR({col:pay}/{col:rentals},0)', 11), CA('hours_rental', 'Hours per rental', 'num', 'IFERROR({col:hours}/{col:rentals},0)', 10),
    CA('pay_hour', 'Pay per hour', 'money', 'IFERROR({col:pay}/{col:hours},0)', 10), CA('supplies_rental', 'Supplies per rental', 'money', 'IFERROR({col:supplies}/{col:rentals},0)', 11),
    PH('owner_phone', 'Owner phone', D.OWNER_PHONE), CENTER()], D.hours_month_d(), 60, [A('cost_rental', '> {set:cost_target}', 'warn')]))
# 17 bookings -----------------------------------------------------------------------------------------
tables.append(T('bookings', 'Bookings', 'Bookings for the roster',
    'One row per booking: dates, vehicle, class, pickup and return times, pickup location and status; the roster and the staff needed read the pickups and returns from here.', [
    C('booking_id', 'Booking', 'text', 10, required=True), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), C('vehicle', 'Vehicle', 'text', 22), LST('class', 'Class', 'class', 12),
    C('pickup_time', 'Pickup time', 'time', 9), C('return_time', 'Return time', 'time', 9), LST('pickup_location', 'Pickup location', 'location', 16), LST('status', 'Status', 'bstatus', 11)],
    D.bookings_d(), 800))
# 18 supplies -----------------------------------------------------------------------------------------
tables.append(T('supplies', 'Supplies Orders', 'Cleaning supplies orders',
    'One row per order of cleaning supplies: date, product, quantity and unit cost; the cost, the date it is needed by and the spend of the month fill in.', [
    C('order_id', 'Order ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('product', 'Product', 'text', 24), C('quantity', 'Quantity', 'int', 9), C('unit_cost', 'Unit cost', 'money', 10),
    CA('cost', 'Cost', 'money', '{col:quantity}*{col:unit_cost}', 10), CA('need_by', 'Needed by', 'date', '{col:date}+7', 11),
    CA('month_cost', 'Supplies of the month', 'money', 'SUMIFS(%s,%s,{col:month})' % (R('supplies', 'cost'), R('supplies', 'month')), 12), PH('vendor_phone', 'Supplier phone', D.SUPPLIER_PHONE), CENTER()],
    D.supplies_d(), 200))
# 19 cleaner workload -------------------------------------------------------------------------------------
tables.append(T('clean_load', 'Cleaner Workload', 'Cars cleaned by detailer and day',
    'One row per detailer and day: cars cleaned, minutes and hours of cleaning from the Turnaround Board; they show how evenly the two detailers share the work.', [
    C('date', 'Date', 'date', 11, required=True), LST('cleaner', 'Detailer', 'cleaner', 16),
    CA('cars', 'Cars cleaned', 'int', 'COUNTIFS(%s,{col:cleaner},%s,{col:date})' % (SL('cleaner'), SL('clean_date')), 9),
    CA('minutes', 'Clean minutes', 'int', 'SUMIFS(%s,%s,{col:cleaner},%s,{col:date})' % (SL('clean_minutes'), SL('cleaner'), SL('clean_date')), 9),
    CA('hours', 'Clean hours', 'num', '{col:minutes}/60', 9), CA('cleaner_phone', 'Detailer phone', 'text', LKT('team.phone', 'team.name', 'cleaner'), 18), CENTER()], D.clean_load_d(), 120))
# 20 runs by week -----------------------------------------------------------------------------------------
tables.append(T('runs_week', 'Delivery Runs by Week', 'Delivery runs by week',
    'One row per week: runs, run minutes, driver cost and fees charged; profit and profit per run fill in so you can see which weeks lose money.', [
    C('week', 'Week of', 'date', 11, required=True), C('runs', 'Runs', 'int', 8), C('minutes', 'Run minutes', 'int', 10), C('driver_cost', 'Driver cost', 'money', 11), C('fees_charged', 'Fees charged', 'money', 11),
    CA('profit', 'Profit', 'money', '{col:fees_charged}-{col:driver_cost}', 10), CA('profit_run', 'Profit per run', 'money', 'IFERROR({col:profit}/{col:runs},0)', 10)], D.runs_week_d(), 80))
assert len(tables) == 20
