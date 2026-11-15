"""Childcare center suite part 3: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc3_lists import *
import cc3_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKP(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))="","%s",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"%s")' % (src, my, kc, D.OWNER_PHONE, src, my, kc, D.OWNER_PHONE)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def RG(t, c): return '{range:%s.%s}' % (t, c)
def PHONE_BY_ROOM(room_col, mp, default):
    f = '"%s"' % default
    for r in reversed(ROOMS): f = 'IF({col:%s}=%s,"%s",%s)' % (room_col, tok('room', r), mp[r], f)
    return f
INF = tok('room', 'Infants'); HOURLY = tok('paytype', 'Hourly'); RELIEF = tok('shiftkind', 'Relief'); BCOVER = tok('shiftkind', 'Break cover')
ROLE_AD = tok('payrole', 'Assistant director'); ROLE_OWN = tok('payrole', 'Owner-director')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
NEEDF = lambda n, r: 'IF(%s<=0,0,MAX(ROUNDUP(%s/%s,0),IF(AND(%s=%s,%s>=3),{set:infants_min_staff},1)))' % (n, n, '%s', r, INF, n)

settings = [
    S('company', 'Your center name', 'text', COMPANY), S('infants_min_staff', 'Staff the Infants room keeps while 3 or more children are in, check your local rules', 'int', 2),
    S('break_minutes', 'Minutes in a staff break', 'int', 30), S('break_after_hours', 'Shift hours after which a break should be planned', 'num', 6),
    S('employer_cost_pct', 'Employer on-costs on top of wages', 'pct', EMPLOYER_COST_PCT), S('staff_share_target', 'Staff cost as a share of revenue, set your own target', 'pct', STAFF_SHARE_TARGET),
    S('cpd_target_hours', 'Training hours a year per staff member, set your own target', 'int', CPD_TARGET_HOURS), S('hours_cap_week', 'Most paid hours one person works in a week, check your local rules', 'num', 45),
    S('contract_tolerance', 'Share rostered hours may differ from contract hours', 'pct', 0.10), S('relief_wage', 'Relief wage per hour', 'money', 15.5),
    S('mgmt_rate', 'Imputed hourly rate when the assistant director covers a room', 'money', 20.8), S('renewal_warn_days', 'Days ahead a renewal counts as due soon', 'int', 45),
    S('turnover_target', 'Yearly turnover you want to stay at or below, set your own', 'pct', 0.30), S('extra_children', 'Children added in the Rota with More Children scenario', 'int', 3), S('pay_tolerance', 'Amount a pay row may differ from the shifts before it is flagged', 'money', 1.0),
]

tables = []
# 1 team
def RW(n): return 'SUMIFS(%s,%s,{col:name},%s,%d)' % (RG('rota', 'hours'), RG('rota', 'staff'), RG('rota', 'day_no'), n)
tables.append(T('team', 'Team', 'Team with roles, contract hours and next week', 'One row per staff member and outside contact; hours rostered next week, training hours this year, open renewals and break clashes fill in by themselves from the other sheets.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('team', 'Team', 'team', 12), LST('pay_type', 'Pay type', 'paytype', 11),
    C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26), C('hours_week', 'Contract hours a week', 'int', 11), C('monthly_salary', 'Monthly salary', 'int', 12), C('hourly_rate', 'Hourly rate', 'money', 11),
    C('room', 'Room led', 'text', 22), C('start', 'Start date', 'date', 12),
    CA('months_here', 'Months here', 'int', 'IFERROR(DATEDIF({col:start},{today},"M"),0)', 9),
    CA('mon', 'Mon hours', 'num', RW(1), 8), CA('tue', 'Tue hours', 'num', RW(2), 8), CA('wed', 'Wed hours', 'num', RW(3), 8), CA('thu', 'Thu hours', 'num', RW(4), 8), CA('fri', 'Fri hours', 'num', RW(5), 8),
    CA('hours_next', 'Hours next week', 'num', '{col:mon}+{col:tue}+{col:wed}+{col:thu}+{col:fri}', 10), CA('shifts_next', 'Shifts next week', 'int', 'COUNTIFS(%s,{col:name})' % RG('rota', 'staff'), 9),
    CA('rota_room', 'Room next week', 'text', 'IFERROR(INDEX(%s,MATCH({col:name},%s,0))&"","")' % (RG('rota', 'room'), RG('rota', 'staff')), 12),
    CA('hours_diff', 'Next week against contract', 'num', 'IF({col:hours_week}=0,0,{col:hours_next}-{col:hours_week})', 11),
    CA('train_hours', 'Training hours this year', 'num', 'SUMIFS(%s,%s,{col:name},%s,YEAR({today}))' % (RG('training', 'hours'), RG('training', 'staff'), RG('training', 'year')), 10),
    CA('train_gap', 'Training hours still needed', 'num', 'IF({col:hours_week}=0,0,MAX(0,{set:cpd_target_hours}-{col:train_hours}))', 10),
    CA('renewals_open', 'Renewals open', 'int', 'COUNTIFS(%s,{col:name},%s,1)' % (RG('renewals', 'holder'), RG('renewals', 'open_flag')), 9),
    CA('next_due', 'Next renewal due', 'date', 'IF({col:renewals_open}=0,"",SUMIFS(%s,%s,{col:name},%s,1))' % (RG('renewals', 'due_date'), RG('renewals', 'holder'), RG('renewals', 'person_rank')), 12),
    CA('breaks_next', 'Breaks next week', 'int', 'COUNTIFS(%s,{col:name},%s,1)' % (RG('break_plan', 'staff'), RG('break_plan', 'has_break')), 9),
    CA('clashes_next', 'Break clashes next week', 'int', 'COUNTIFS(%s,{col:name},%s,1)' % (RG('break_plan', 'staff'), RG('break_plan', 'clash')), 10),
    CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18), CA('ad_phone', 'Assistant director phone', 'text', '"%s"' % D.AD_PHONE, 18)],
    D.team_d(), 50, [A('clashes_next', '> 0', 'warn'), A('train_gap', '> 6', 'warn')]))

# 2 shifts
tables.append(T('shifts', 'Shifts', 'Shifts worked, with hours and cost', 'One row per shift: type the date, staff member, room, start, end, break and rate; hours, cost, week and month calculate. Keep recent months here.', [
    C('shift_id', 'Shift ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), LST('staff', 'Staff member', 'shiftstaff', 20), LST('role', 'Role', 'payrole', 17), LST('room', 'Room', 'shiftroom', 12),
    C('start', 'Start', 'time', 8), C('end', 'End', 'time', 8), C('break_start', 'Break start', 'time', 9), C('break_minutes', 'Break minutes', 'int', 9), LST('kind', 'Kind', 'shiftkind', 12), C('rate', 'Hourly rate', 'money', 10),
    CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('hours', 'Paid hours', 'num', 'IF(OR({col:start}="",{col:end}=""),"",ROUND(({col:end}-{col:start})*24-{col:break_minutes}/60,2))', 9),
    CA('cost', 'Wages and on-costs', 'money', 'IF({col:hours}="","",ROUND({col:hours}*{col:rate}*(1+{set:employer_cost_pct}),2))', 12)],
    D.shifts_d(), 3000, [A('kind', '= ' + RELIEF, 'warn'), A('kind', '= ' + BCOVER, 'good')]))

# 3 ratio
tables.append(T('ratio', 'Ratio by Hour', 'Staff-to-child ratio by room and hour', 'One row per room and hour with children: type the children counted at half past and the staff present; ratio, staff needed, the gap and the check fill in. Short means fewer staff than the ratio asks, check your local rules.', [
    C('slot_id', 'Slot ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), LST('weekday', 'Weekday', 'wday', 11), LST('hour', 'Hour', 'hourl', 8), LST('room', 'Room', 'room', 12),
    C('children', 'Children', 'int', 9), C('present', 'Staff present', 'int', 9),
    CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('hour_no', 'Hour number', 'int', 'VALUE(LEFT({col:hour},2))', 8), CA('ratio', 'Children per staff', 'int', 'SUMIFS(%s,%s,{col:room})' % (RG('rooms', 'ratio'), RG('rooms', 'room')), 9),
    CA('needed', 'Staff needed', 'int', NEEDF('{col:children}', '{col:room}') % '{col:ratio}', 9), CA('gap', 'Gap', 'int', '{col:needed}-{col:present}', 7),
    CA('short_flag', 'Short', 'int', 'IF({col:gap}>0,1,0)', 7), CA('over_flag', 'Over-staffed', 'int', 'IF({col:gap}<0,1,0)', 8), CA('tight_flag', 'No spare staff', 'int', 'IF(AND({col:gap}=0,{col:children}>0),1,0)', 8),
    CA('cover_flag', 'Check', 'text', 'IF({col:gap}>0,%s,IF({col:gap}<0,%s,%s))' % (fl('Short'), fl('Over-staffed'), fl('Covered')), 13)],
    D.ratio_d(), 3000, [A('cover_flag', '= ' + fl('Short'), 'bad'), A('cover_flag', '= ' + fl('Over-staffed'), 'warn')]))

# 4 rooms
tables.append(T('rooms', 'Rooms', 'Rooms with licensed places and ratio', 'One row per room: licensed places and the ratio, the number of children each staff member may care for, check your local rules. Room is an age group, in a home daycare the one space you use.', [
    C('room', 'Room', 'text', 24, required=True), C('capacity', 'Licensed places', 'int', 11), C('ratio', 'Children per staff', 'int', 11)], [dict(room=r['room'], capacity=r['capacity'], ratio=r['ratio']) for r in rooms], 50))

# 5 payroll
tables.append(T('payroll', 'Payroll', 'Payroll by person and month', 'One row per person and month: hours, gross pay and on-costs; the total, the hours and cost the shifts give and the pay check fill in so a pay run can be compared with the rota.', [
    C('pay_id', 'Pay ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('person', 'Person', 'shiftstaff', 20), LST('role', 'Role', 'payrole', 17), LST('pay_type', 'Pay type', 'paytype', 11),
    C('hours', 'Hours', 'num', 9), C('gross', 'Gross pay', 'money', 11), C('on_costs', 'On-costs', 'money', 11), C('pay_date', 'Pay date', 'date', 12), LST('status', 'Status', 'paystatus', 10),
    CA('total', 'Total cost', 'money', '{col:gross}+{col:on_costs}', 11), CA('shift_hours', 'Hours in the shifts', 'num', 'SUMIFS(%s,%s,{col:person},%s,{col:month})' % (RG('shifts', 'hours'), RG('shifts', 'staff'), RG('shifts', 'month')), 10),
    CA('shift_cost', 'Cost in the shifts', 'money', 'SUMIFS(%s,%s,{col:person},%s,{col:month})' % (RG('shifts', 'cost'), RG('shifts', 'staff'), RG('shifts', 'month')), 11),
    CA('check_flag', 'Pay check', 'text', 'IF({col:pay_type}<>%s,%s,IF(ABS({col:total}-{col:shift_cost})<={set:pay_tolerance},%s,%s))' % (HOURLY, fl('Matches'), fl('Matches'), fl('Differs')), 12),
    CA('phone', 'Phone', 'text', LKP('team.phone', 'team.name', 'person'), 18), CA('ad_phone', 'Assistant director phone', 'text', '"%s"' % D.AD_PHONE, 18), CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACC_PHONE, 18)],
    D.payroll_d(), 300, [A('check_flag', '= ' + fl('Differs'), 'bad')]))

# 6 renewals
tables.append(T('renewals', 'Renewals', 'Renewals register by person, status and dates only', 'One row per renewal: type the holder, item, due date and the date it was renewed; days left and the 30, 45 and 60 day band fill in. Status and dates only, nothing else is stored.', [
    C('renewal_id', 'Renewal ID', 'text', 10, required=True), C('holder', 'Holder', 'text', 22), LST('item', 'Item', 'renewal', 20), C('due_date', 'Due date', 'date', 12), C('renewed_on', 'Renewed on', 'date', 12), C('cost', 'Cost', 'money', 10),
    CA('open_flag', 'Open', 'int', 'IF({col:renewed_on}="",1,0)', 7), CA('days_left', 'Days left', 'int', 'IF({col:open_flag}=1,{col:due_date}-{today},"")', 9),
    CA('band', 'Band', 'text', 'IF({col:open_flag}=0,%s,IF({col:days_left}<0,%s,IF({col:days_left}<=30,%s,IF({col:days_left}<=45,%s,IF({col:days_left}<=60,%s,%s)))))' % (
        fl('Done'), fl('Overdue'), fl('Due in 30 days'), fl('Due in 45 days'), fl('Due in 60 days'), fl('Later')), 15),
    CA('warn_flag', 'Due soon', 'int', 'IF(AND({col:open_flag}=1,{col:days_left}<={set:renewal_warn_days}),1,0)', 8),
    CA('person_rank', 'Order for the holder', 'int', 'IF({col:open_flag}=1,COUNTIFS(%s,{col:holder},%s,1,%s,"<"&{col:due_date})+1,"")' % (RG('renewals', 'holder'), RG('renewals', 'open_flag'), RG('renewals', 'due_date')), 9),
    CA('phone', 'Holder phone', 'text', LKP('team.phone', 'team.name', 'holder'), 18), CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)],
    D.renewals_d(), 200, [A('band', '= ' + fl('Overdue'), 'bad'), A('band', '= ' + fl('Due in 30 days'), 'warn'), A('band', '= ' + fl('Done'), 'good')]))

# 7 training
tables.append(T('training', 'Training', 'Training hours and cost by person', 'One row per training session: date, staff member, kind, title, hours and cost; month and year fill in so hours can be set against the yearly target.', [
    C('training_id', 'Training ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), LST('staff', 'Staff member', 'staff', 20), LST('kind', 'Kind', 'cpd', 16), C('title', 'Title', 'text', 28),
    C('hours', 'Hours', 'num', 8), C('cost', 'Cost', 'money', 10),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('year', 'Year', 'int', 'YEAR({col:date})', 7), CA('phone', 'Staff phone', 'text', LKT('team.phone', 'team.name', 'staff'), 18)], D.training_d(), 300))

# 8 leavers
tables.append(T('leavers', 'Leavers', 'Leavers with replacement cost', 'One row per staff member who left: name, last day and what replacing them cost in advert, training and relief.', [
    C('name', 'Name', 'text', 24, required=True), C('left_on', 'Left on', 'date', 12), C('replacement_cost', 'Replacement cost', 'money', 13)], D.leavers_d(), 50))

# 9 turnover
def TRL(a, b): return 'COUNTIFS(%s,">="&%s,%s,"<="&%s)' % (RG('leavers', 'left_on'), a, RG('leavers', 'left_on'), b)
tables.append(T('turnover', 'Turnover by Month', 'Turnover and staff cost share by month', 'One row per month: headcount, revenue, staff cost and vacancy days are typed; leavers, replacement cost, yearly turnover and the staff cost share against your target fill in.', [
    C('tm_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('headcount', 'Headcount', 'int', 10), C('revenue', 'Revenue', 'money', 12), C('staff_cost', 'Staff cost', 'money', 12), C('vacancy_days', 'Vacancy days', 'int', 10),
    CA('leavers', 'Leavers', 'int', TRL('{col:month}', 'EOMONTH({col:month},0)'), 8),
    CA('replacement_cost', 'Replacement cost', 'money', 'SUMIFS(%s,%s,">="&{col:month},%s,"<="&EOMONTH({col:month},0))' % (RG('leavers', 'replacement_cost'), RG('leavers', 'left_on'), RG('leavers', 'left_on')), 12),
    CA('leavers_12m', 'Leavers in 12 months', 'int', TRL('EDATE({col:month},-11)', 'EOMONTH({col:month},0)'), 10),
    CA('avg_head', 'Average headcount, 12 months', 'num', 'IFERROR(AVERAGEIFS(%s,%s,">="&EDATE({col:month},-11),%s,"<="&{col:month}),0)' % (RG('turnover', 'headcount'), RG('turnover', 'month'), RG('turnover', 'month')), 11),
    CA('turnover_share', 'Yearly turnover', 'pct', 'IF({col:avg_head}>0,{col:leavers_12m}/{col:avg_head},0)', 10), CA('cost_share', 'Staff cost share', 'pct', 'IF({col:revenue}>0,{col:staff_cost}/{col:revenue},0)', 10),
    CA('share_ok', 'At or below target', 'int', 'IF({col:cost_share}<={set:staff_share_target},1,0)', 9),
    CA('has_ly', 'Last year in the table', 'int', 'IF(COUNTIFS(%s,EDATE({col:month},-12))>0,1,0)' % RG('turnover', 'month'), 9),
    CA('ly_turnover', 'Turnover a year earlier', 'pct', 'SUMIFS(%s,%s,EDATE({col:month},-12))' % (RG('turnover', 'turnover_share'), RG('turnover', 'month')), 10),
    CA('better_flag', 'Not above last year', 'int', 'IF(AND({col:has_ly}=1,{col:turnover_share}<={col:ly_turnover}),1,0)', 9), CA('turnover_ok', 'At or below turnover target', 'int', 'IF({col:turnover_share}<={set:turnover_target},1,0)', 9),
    CA('hours', 'Paid hours', 'num', 'SUMIFS(%s,%s,{col:month})' % (RG('shifts', 'hours'), RG('shifts', 'month')), 9),
    CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACC_PHONE, 18), CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)],
    D.turnover_d(), 60, [A('cost_share', '> {set:staff_share_target}', 'warn')]))

# 10 rota
tables.append(T('rota', 'Rota Next Week', 'Rota for next week', 'One row per planned shift next week: date, staff member, room, start, end and break; paid hours, the weekday number and the staff phone fill in. The sample repeats last week as a starting pattern.', [
    C('rota_id', 'Rota ID', 'text', 9, required=True), C('date', 'Date', 'date', 12), LST('staff', 'Staff member', 'shiftstaff', 20), LST('room', 'Room', 'shiftroom', 12), C('start', 'Start', 'time', 8), C('end', 'End', 'time', 8),
    C('break_start', 'Break start', 'time', 9),
    CA('day_no', 'Weekday number', 'int', 'WEEKDAY({col:date},2)', 8), CA('hours', 'Paid hours', 'num', 'IF(OR({col:start}="",{col:end}=""),"",ROUND(({col:end}-{col:start})*24-IF({col:break_start}="",0,{set:break_minutes}/60),2))', 9),
    CA('phone', 'Staff phone', 'text', LKT('team.phone', 'team.name', 'staff'), 18), CA('cook_phone', 'Cook phone', 'text', '"%s"' % D.COOK_PHONE, 18), CA('cleaner_phone', 'Cleaner phone', 'text', '"%s"' % D.CLEAN_PHONE, 18)], D.rota_d(), 150))

# 11 weeks
WK = lambda c, extra='': 'SUMIFS(%s,%s,{col:week}%s)' % (RG('ratio', c), RG('ratio', 'week'), extra)
tables.append(T('weeks', 'Short Hours by Week', 'Short room-hours by week', 'One row per week: short room-hours, hours with no spare staff, the share covered, children in the short hours and the relief and management cover hours used that week, all calculated from the ratio sheet.', [
    C('wk_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), LST('wk', 'Week', 'weekn', 9),
    CA('room_hours', 'Room-hours counted', 'int', 'COUNTIFS(%s,{col:week})' % RG('ratio', 'week'), 10), CA('short_hours', 'Short room-hours', 'int', WK('short_flag'), 9),
    CA('tight_hours', 'Hours with no spare staff', 'int', WK('tight_flag'), 10), CA('covered_share', 'Covered share', 'pct', 'IF({col:room_hours}>0,1-{col:short_hours}/{col:room_hours},0)', 9),
    CA('children_short', 'Children in short hours', 'int', WK('children', ',%s,1' % RG('ratio', 'short_flag')), 10), CA('staff_missing', 'Staff missing', 'int', WK('gap', ',%s,1' % RG('ratio', 'short_flag')), 8),
    CA('relief_hours', 'Relief hours', 'num', 'SUMIFS(%s,%s,{col:week},%s,%s)' % (RG('shifts', 'hours'), RG('shifts', 'week'), RG('shifts', 'kind'), RELIEF), 9),
    CA('break_cover_hours', 'Break cover hours', 'num', 'SUMIFS(%s,%s,{col:week},%s,%s)' % (RG('shifts', 'hours'), RG('shifts', 'week'), RG('shifts', 'kind'), BCOVER), 9),
    CA('mgmt_hours', 'Management cover hours', 'num', 'SUMIFS(%s,%s,{col:week},%s,%s)+SUMIFS(%s,%s,{col:week},%s,%s)' % (RG('shifts', 'hours'), RG('shifts', 'week'), RG('shifts', 'role'), ROLE_AD, RG('shifts', 'hours'), RG('shifts', 'week'), RG('shifts', 'role'), ROLE_OWN), 10),
    CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18), CA('ad_phone', 'Assistant director phone', 'text', '"%s"' % D.AD_PHONE, 18)], D.weeks_d(), 50,
    [A('short_hours', '> 0', 'bad')]))

# 12 heat map
HM = lambda c: 'SUMIFS(%s,%s,{col:room},%s,{col:week})' % (RG('ratio', c), RG('ratio', 'room'), RG('ratio', 'week'))
tables.append(T('heat', 'Cover Heat Map', 'Cover heat map by room and week', 'One row per room and week: room-hours counted, short and tight slots and the share covered; the rank puts the room-week that needs relief first.', [
    C('hm_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), C('week', 'Week (Monday)', 'date', 12), LST('wk', 'Week', 'weekn', 9),
    CA('slots', 'Room-hours counted', 'int', 'COUNTIFS(%s,{col:room},%s,{col:week})' % (RG('ratio', 'room'), RG('ratio', 'week')), 10), CA('slots_short', 'Slots short', 'int', HM('short_flag'), 8),
    CA('slots_tight', 'Slots with no spare staff', 'int', HM('tight_flag'), 10), CA('covered_share', 'Covered share', 'pct', 'IF({col:slots}>0,1-{col:slots_short}/{col:slots},0)', 9),
    CA('ratio', 'Children per staff', 'int', 'SUMIFS(%s,%s,{col:room})' % (RG('rooms', 'ratio'), RG('rooms', 'room')), 9),
    CA('score', 'Rank score', 'num', '{col:slots_short}+IF({col:slots}>0,{col:slots_tight}/{col:slots},0)/10+MATCH({col:room},%s,0)/10000+{col:week}/10000000000' % RG('rooms', 'room'), 10),
    CA('rank', 'Rank', 'int', '1+COUNTIFS(%s,">"&{col:score})' % RG('heat', 'score'), 7),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)], D.heat_d(), 100,
    [A('slots_short', '> 0', 'bad')]))

# 13 staff on duty by hour
SD = lambda c: 'IFERROR(AVERAGEIFS(%s,%s,{col:room},%s,{col:hour}),0)' % (RG('ratio', c), RG('ratio', 'room'), RG('ratio', 'hour'))
SDS = lambda c: 'IFERROR(SUMIFS(%s,%s,{col:room},%s,{col:hour})/COUNTIFS(%s,{col:room},%s,{col:hour}),0)' % (RG('ratio', c), RG('ratio', 'room'), RG('ratio', 'hour'), RG('ratio', 'room'), RG('ratio', 'hour'))
def NEEDX(x): return 'IF({col:avg_children}<=0,0,MAX(ROUNDUP(({col:avg_children}+%s)/{col:ratio},0),IF(AND({col:room}=%s,{col:avg_children}+%s>=3),{set:infants_min_staff},1)))' % (x, INF, x)
tables.append(T('staff_hour', 'Staff on Duty by Hour', 'Average staff and children by room and hour', 'One row per room and hour: the average children and staff present from the ratio sheet, the staff needed on average, the share of days short or tight, and the rank where one more floater hour helps most.', [
    C('sd_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), LST('hour', 'Hour', 'hourl', 8),
    CA('hour_no', 'Hour number', 'int', 'VALUE(LEFT({col:hour},2))', 8), CA('ratio', 'Children per staff', 'int', 'SUMIFS(%s,%s,{col:room})' % (RG('rooms', 'ratio'), RG('rooms', 'room')), 9),
    CA('avg_children', 'Average children', 'num', 'ROUND(%s,1)' % SD('children'), 9), CA('avg_present', 'Average staff present', 'num', 'ROUND(%s,1)' % SD('present'), 9),
    CA('needed_avg', 'Staff needed on average', 'int', NEEDF('{col:avg_children}', '{col:room}') % '{col:ratio}', 9), CA('spare_avg', 'Spare staff on average', 'num', '{col:avg_present}-{col:needed_avg}', 9),
    CA('short_share', 'Share of days short', 'pct', SDS('short_flag'), 9), CA('tight_share', 'Share of days with no spare staff', 'pct', SDS('tight_flag'), 10),
    CA('place_score', 'Placement score', 'num', '{col:short_share}*100+{col:tight_share}+MATCH({col:room},%s,0)/100000+{col:hour_no}/10000000' % RG('rooms', 'room'), 10),
    CA('place_rank', 'Placement rank', 'int', '1+COUNTIFS(%s,">"&{col:place_score})' % RG('staff_hour', 'place_score'), 8),
    CA('flag', 'Check', 'text', 'IF({col:short_share}>0,%s,IF({col:tight_share}>=0.5,%s,%s))' % (fl('Short'), fl('Tight'), fl('Covered')), 12),
    CA('need_base', 'Needed with the extra children', 'int', NEEDX('{set:extra_children}'), 9), CA('need_best', 'Needed, best case', 'int', NEEDX('ROUND({set:extra_children}*0.67,0)'), 9), CA('need_worst', 'Needed, worst case', 'int', NEEDX('ROUND({set:extra_children}*1.67,0)'), 9),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('cook_phone', 'Cook phone', 'text', '"%s"' % D.COOK_PHONE, 18)], D.staff_hour_d(), 80,
    [A('flag', '= ' + fl('Short'), 'bad'), A('flag', '= ' + fl('Tight'), 'warn')]))

# 14 break plan
def RSUM(h, extra=''): return 'SUMPRODUCT((%s={col:room})*(%s={col:date})*(ROUND(%s*24,2)<=%s)*(ROUND(%s*24,2)>%s))' % (RG('rota', 'room'), RG('rota', 'date'), RG('rota', 'start'), h, RG('rota', 'end'), h)
def BSUM(h): return 'SUMPRODUCT((%s={col:room})*(%s={col:date})*(ROUND(%s*24,2)=%s))' % (RG('rota', 'room'), RG('rota', 'date'), RG('rota', 'break_start'), h)
def NEEDH(h): return 'SUMIFS(%s,%s,{col:room},%s,ROUND(%s,0))' % (RG('staff_hour', 'needed_avg'), RG('staff_hour', 'room'), RG('staff_hour', 'hour_no'), h)
def MOVEOK(d): h = '({col:break_h}%+d)' % d; return 'AND(%s>={col:start_h}+1,%s<={col:end_h}-1,%s-%s-1>=%s)' % (h, h, RSUM(h), BSUM(h), NEEDH(h))
def HT(x): return 'RIGHT("0"&ROUND(%s,0),2)&":00"' % x
MOVE = 'IF({col:has_break}=0,"-",IF({col:clash}=0,%s,IF(%s,%s,IF(%s,%s,IF(%s,%s,%s)))))' % (fl('Keep the time'), MOVEOK(1), HT('{col:break_h}+1'), MOVEOK(2), HT('{col:break_h}+2'), MOVEOK(-1), HT('{col:break_h}-1'), fl('Add break cover'))
tables.append(T('break_plan', 'Break Plan', 'Break plan with room cover check', 'One row per rota shift: the break, the staff needed in that hour from your average children, the staff left without the break, the clash check and a better break time when there is a clash.', [
    C('rota_id', 'Rota ID', 'text', 9, required=True),
    CA('date', 'Date', 'date', LKN('rota.date', 'rota.rota_id', 'rota_id'), 12), CA('staff', 'Staff member', 'text', LKT('rota.staff', 'rota.rota_id', 'rota_id'), 20), CA('room', 'Room', 'text', LKT('rota.room', 'rota.rota_id', 'rota_id'), 12),
    CA('start_h', 'Start hour', 'num', 'ROUND(%s*24,2)' % LKN('rota.start', 'rota.rota_id', 'rota_id'), 8), CA('end_h', 'End hour', 'num', 'ROUND(%s*24,2)' % LKN('rota.end', 'rota.rota_id', 'rota_id'), 8),
    CA('break_time', 'Break start', 'time', LKN('rota.break_start', 'rota.rota_id', 'rota_id'), 9), CA('break_h', 'Break hour', 'num', 'ROUND({col:break_time}*24,2)', 8),
    CA('has_break', 'Has a break', 'int', 'IF({col:break_h}>0,1,0)', 7), CA('shift_hours', 'Paid hours', 'num', LKN('rota.hours', 'rota.rota_id', 'rota_id'), 8),
    CA('needed', 'Staff needed in that hour', 'int', 'IF({col:has_break}=1,%s,0)' % NEEDH('{col:break_h}'), 10),
    CA('present_after', 'Staff left without the break', 'int', 'IF({col:has_break}=1,%s-%s,0)' % (RSUM('{col:break_h}'), BSUM('{col:break_h}')), 10),
    CA('clash', 'Clash', 'int', 'IF(AND({col:has_break}=1,{col:present_after}<{col:needed}),1,0)', 7),
    CA('break_flag', 'Break check', 'text', 'IF({col:has_break}=1,IF({col:clash}=1,%s,%s),IF({col:shift_hours}>={set:break_after_hours},%s,%s))' % (fl('Clash'), fl('No clash'), fl('Add a break'), fl('No break needed')), 14),
    CA('clash_key', 'Clash key', 'text', 'IF({col:clash}=1,{col:date}&"|"&{col:room}&"|"&COUNTIFS(%s,{col:date},%s,{col:room},%s,1,%s,"<="&{col:rota_id}),"")' % (RG('break_plan', 'date'), RG('break_plan', 'room'), RG('break_plan', 'clash'), RG('break_plan', 'rota_id')), 12),
    CA('move_to', 'Move break to', 'text', MOVE, 15), CA('phone', 'Staff phone', 'text', LKT('team.phone', 'team.name', 'staff'), 18)], D.break_plan_d(), 150,
    [A('break_flag', '= ' + fl('Clash'), 'bad'), A('break_flag', '= ' + fl('Add a break'), 'warn'), A('break_flag', '= ' + fl('No clash'), 'good')]))

# 15 cost per child-hour
tables.append(T('cph', 'Cost per Child-Hour', 'Staff cost per child-hour by room and month', 'One row per room and month: paid hours, wages with on-costs and child-hours attended are typed from the shifts and attendance totals; cost per child-hour, the center figure and the dearest-room rank are calculated.', [
    C('cp_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), C('month', 'Month', 'date', 11), C('paid_hours', 'Paid hours', 'num', 9), C('wages', 'Wages and on-costs', 'money', 12), C('child_hours', 'Child-hours attended', 'num', 11),
    CA('cost_ch', 'Cost per child-hour', 'money', 'IF({col:child_hours}>0,ROUND({col:wages}/{col:child_hours},2),0)', 10), CA('per_hour', 'Children per paid hour', 'num', 'IF({col:paid_hours}>0,ROUND({col:child_hours}/{col:paid_hours},2),0)', 10),
    CA('center_cost', 'Center cost per child-hour', 'money', 'IFERROR(ROUND(SUMIFS(%s,%s,{col:month})/SUMIFS(%s,%s,{col:month}),2),0)' % (RG('cph', 'wages'), RG('cph', 'month'), RG('cph', 'child_hours'), RG('cph', 'month')), 11),
    CA('gap_center', 'Against the center', 'money', '{col:cost_ch}-{col:center_cost}', 10),
    CA('rank_month', 'Rank in the month, 1 is dearest', 'int', '1+COUNTIFS(%s,{col:month},%s,">"&{col:cost_ch})' % (RG('cph', 'month'), RG('cph', 'cost_ch')), 10),
    CA('rank_key', 'Rank key', 'text', '{col:month}&"|"&{col:rank_month}', 10),
    CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)], D.cph_d(), 100, [A('rank_month', '= 1', 'warn')]))

# 16 hours by person and week
tables.append(T('hours_week', 'Hours by Person and Week', 'Rostered hours by person and week', 'One row per person and week: rostered hours come from the shifts; the contract hours, the difference and the cap and contract checks fill in so overtime shows early.', [
    C('hw_id', 'Row ID', 'text', 9, required=True), LST('staff', 'Staff member', 'staff', 20), C('week', 'Week (Monday)', 'date', 12), LST('wk', 'Week', 'weekn', 9),
    CA('rostered', 'Rostered hours', 'num', 'SUMIFS(%s,%s,{col:staff},%s,{col:week})' % (RG('shifts', 'hours'), RG('shifts', 'staff'), RG('shifts', 'week')), 10),
    CA('contract', 'Contract hours', 'num', 'SUMIFS(%s,%s,{col:staff})' % (RG('team', 'hours_week'), RG('team', 'name')), 9), CA('diff', 'Against contract', 'num', '{col:rostered}-{col:contract}', 9),
    CA('over_hours', 'Hours over contract', 'num', 'MAX(0,{col:diff})', 9), CA('over_cap', 'Over the cap', 'int', 'IF({col:rostered}>{set:hours_cap_week},1,0)', 8),
    CA('cap_flag', 'Cap check', 'text', 'IF({col:over_cap}=1,%s,%s)' % (fl('Over the cap'), fl('Within the cap')), 13),
    CA('fit_flag', 'Contract check', 'text', 'IF({col:rostered}>{col:contract}*(1+{set:contract_tolerance}),%s,IF({col:rostered}<{col:contract}*(1-{set:contract_tolerance}),%s,%s))' % (fl('Over contract'), fl('Under contract'), fl('On contract')), 14),
    CA('phone', 'Staff phone', 'text', LKT('team.phone', 'team.name', 'staff'), 18)], D.hours_week_d(), 200, [A('cap_flag', '= ' + fl('Over the cap'), 'bad'), A('fit_flag', '= ' + fl('Over contract'), 'warn')]))

# 17 training by person and year
tables.append(T('train_year', 'Training by Person and Year', 'Training hours by person and year', 'One row per person and year: hours done come from the training sheet; hours still needed against your yearly target, the cost and an on-track check fill in.', [
    C('ty_id', 'Row ID', 'text', 9, required=True), LST('staff', 'Staff member', 'staff', 20), C('year', 'Year', 'int', 7),
    CA('done', 'Hours done', 'num', 'SUMIFS(%s,%s,{col:staff},%s,{col:year})' % (RG('training', 'hours'), RG('training', 'staff'), RG('training', 'year')), 9), CA('target', 'Yearly target hours', 'int', '{set:cpd_target_hours}', 9),
    CA('needed', 'Hours still needed', 'num', 'MAX(0,{col:target}-{col:done})', 9), CA('cost', 'Training cost', 'money', 'SUMIFS(%s,%s,{col:staff},%s,{col:year})' % (RG('training', 'cost'), RG('training', 'staff'), RG('training', 'year')), 10),
    CA('this_year', 'This year', 'int', 'IF({col:year}=YEAR({today}),1,0)', 8), CA('year_label', 'Year label', 'text', '{col:year}&""', 8), CA('status_flag', 'Target check', 'text', 'IF({col:needed}>0,%s,%s)' % (fl('Behind'), fl('On track')), 11),
    CA('phone', 'Staff phone', 'text', LKT('team.phone', 'team.name', 'staff'), 18)], D.train_year_d(), 60, [A('status_flag', '= ' + fl('Behind'), 'warn'), A('status_flag', '= ' + fl('On track'), 'good')]))

# 18 relief ledger
tables.append(T('relief', 'Relief and Cover Shifts', 'Relief and break cover shifts', 'One row per relief or break-cover shift: date, who covered, room, hour, kind, hours and cost; the cost per hour, week and month fill in.', [
    C('cover_id', 'Cover ID', 'text', 9, required=True), C('date', 'Date', 'date', 12), LST('staff', 'Staff member', 'shiftstaff', 20), LST('room', 'Room', 'shiftroom', 12), LST('hour', 'Hour', 'hourl', 8), C('kind', 'Kind', 'text', 12),
    C('hours', 'Hours', 'num', 8), C('cost', 'Cost', 'money', 10),
    CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('cost_hour', 'Cost per hour', 'money', 'IF({col:hours}>0,ROUND({col:cost}/{col:hours},2),0)', 9), CA('phone', 'Staff phone', 'text', LKT('team.phone', 'team.name', 'staff'), 18)], D.relief_d(), 600))

# 19 pay rates
tables.append(T('pay_rates', 'Pay Rates by Role', 'Pay rates by role', 'One row per role: the hourly rate and the on-cost share used for relief and cover sums. The owner-director and assistant director rates are imputed for cover only.', [
    LST('role', 'Role', 'payrole', 20, required=True), C('hourly_rate', 'Hourly rate', 'money', 11), C('on_cost_share', 'On-cost share', 'pct', 11)], D.pay_rates_d(), 50))

# 20 cover requests
tables.append(T('cover_req', 'Cover Requests', 'Cover requests and who filled them', 'One row per request for cover: date, room, hour, how many staff short, who filled it and the status; days to go and the phone to call fill in.', [
    C('request_id', 'Request ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), LST('room', 'Room', 'room', 12), LST('hour', 'Hour', 'hourl', 8), C('short_by', 'Short by', 'int', 8),
    LST('filled_by', 'Filled by', 'shiftstaff', 20), LST('status', 'Status', 'reqstatus', 11),
    CA('days_to_go', 'Days to go', 'int', '{col:date}-{today}', 8),
    CA('phone', 'Phone to call', 'text', 'IF({col:filled_by}="","%s",IFERROR(INDEX(%s,MATCH({col:filled_by},%s,0)),"%s"))' % (D.FLOAT_PHONE, RG('team', 'phone'), RG('team', 'name'), D.FLOAT_PHONE), 18),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)], D.cover_req_d(), 60,
    [A('status', '= ' + tok('reqstatus', 'Open'), 'warn'), A('status', '= ' + tok('reqstatus', 'Not filled'), 'bad'), A('status', '= ' + tok('reqstatus', 'Filled'), 'good')]))
assert len(tables) == 20, len(tables)
