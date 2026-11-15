"""Childcare center suite part 6: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc6_lists import *
import cc6_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def RG(t, c): return '{range:%s.%s}' % (t, c)
def PHONE_BY_ROOM(room_col, mp, default):
    f = '"%s"' % default
    for r in reversed(ROOMS): f = 'IF({col:%s}=%s,"%s",%s)' % (room_col, tok('room', r), mp[r], f)
    return f
def PH(p): return '"%s"' % p
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
ONF, DUE, MISS = tok('hstatus', 'On file'), tok('hstatus', 'Due'), tok('hstatus', 'Missing')
DONE, MISSED = tok('checkstatus', 'Done'), tok('checkstatus', 'Missed')
MB, ML_, MS_ = tok('meal', 'Breakfast'), tok('meal', 'Lunch'), tok('meal', 'Afternoon snack')
OPEN = tok('fup', 'Open')
ALLERGY, PERMIT = tok('hrecord', 'Allergy status'), tok('hrecord', 'Medical permission')

settings = [
    S('company', 'Your center name', 'text', COMPANY),
    S('claim_breakfast', 'Claim per eligible breakfast, your own rate', 'money', 1.3), S('claim_lunch', 'Claim per eligible lunch, your own rate', 'money', 2.6),
    S('claim_snack', 'Claim per eligible snack, your own rate', 'money', 0.8), S('cost_band', 'Share around your usual food cost that counts as near', 'pct', 0.05),
    S('rate_band', 'Share around your usual incident rate that counts as near', 'pct', 0.25), S('record_warn_days', 'Days ahead that a record due date counts as due soon', 'int', 30),
    S('call_days', 'Days past due when you call the family', 'int', 7), S('escalate_days', 'Days past due when the owner-director steps in', 'int', 21),
    S('followup_days', 'Days an incident follow-up may stay open', 'int', 3), S('pattern_min', 'Incidents at one hour in one room that make a pattern', 'int', 3),
    S('drill_fire', 'Months between fire drills, your own plan', 'int', 1), S('drill_evac', 'Months between evacuation drills, your own plan', 'int', 3),
    S('drill_lockdown', 'Months between lockdown drills, your own plan', 'int', 4), S('drill_shelter', 'Months between shelter drills, your own plan', 'int', 3),
    S('check_deep', 'Days between deep cleans of a room', 'int', 7), S('check_safety', 'Days between safety checks of a room', 'int', 7), S('check_equip', 'Days between equipment checks of a room', 'int', 14),
    S('completion_target', 'Share of checks you want done', 'pct', 0.95), S('order_children', 'Children counted for a food order', 'int', 40),
]
assert 3 <= len(settings) <= 20

tables = []

# 1 meals
tables.append(T('meals', 'Meals', 'Meal counts by day, meal and room',
    'One row per day, meal and room: type the children present, the meals served and the eligible meals; the cost, the over-count check and the week fill in. Older months show sample days.', [
    C('meal_id', 'Meal ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), LST('meal', 'Meal', 'meal', 15), LST('room', 'Room', 'room', 12), C('children_present', 'Children present', 'int', 10),
    C('served', 'Meals served', 'int', 9), C('eligible', 'Eligible meals', 'int', 9), C('unit_cost', 'Unit cost', 'money', 9),
    CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('cost', 'Cost', 'money', 'ROUND({col:served}*{col:unit_cost},2)', 9), CA('over_by', 'Over by', 'int', 'MAX(0,{col:served}-{col:children_present})', 8),
    CA('margin_key', 'Margin ranking key', 'num', '({col:served}-{col:children_present})*100000+{col:date}+IF({col:meal}=%s,1,IF({col:meal}=%s,2,3))/10+MATCH({col:room},%s,0)/100' % (MB, ML_, RG('rooms', 'room')), 11),
    CA('check_flag', 'Meal check', 'text', 'IF({col:over_by}>0,%s,IF({col:served}={col:children_present},%s,%s))' % (fl('Over the children present'), fl('At the limit'), fl('Counts consistent')), 20),
    CA('cook_phone', 'Cook phone', 'text', PH(D.COOK_PHONE), 18)],
    D.meals_d(), 1500, [A('check_flag', '= ' + fl('Over the children present'), 'bad'), A('check_flag', '= ' + fl('At the limit'), 'warn')]))

# 2 menu
tables.append(T('menu', 'Menu', 'Menu cycle by week, weekday and meal',
    'The menu cycle: one row per weekday and meal with the dish, cost per child and portions a kilogram; day cost, kilograms, cost rank and the dishes of the day fill in.', [
    C('menu_id', 'Menu ID', 'text', 9, required=True), C('cycle_week', 'Cycle week', 'int', 9), LST('weekday', 'Weekday', 'wday', 11), LST('meal', 'Meal', 'meal', 15), C('dish', 'Dish', 'text', 28),
    C('cost_child', 'Cost per child', 'money', 10), C('portions_per_kg', 'Portions per kg', 'num', 10),
    CA('dkey', 'Day key', 'text', '{col:cycle_week}&"|"&{col:weekday}', 14), CA('mkey', 'Meal key', 'text', '{col:cycle_week}&"|"&{col:weekday}&"|"&{col:meal}', 22),
    CA('day_cost', 'Cost of the day per child', 'money', 'SUMIFS(%s,%s,{col:cycle_week},%s,{col:weekday})' % (RG('menu', 'cost_child'), RG('menu', 'cycle_week'), RG('menu', 'weekday')), 12),
    CA('kg_per_child', 'Kilograms per child', 'num', 'ROUND(1/{col:portions_per_kg},4)', 10), CA('kg_order', 'Kilograms for your order', 'num', 'ROUND({set:order_children}/{col:portions_per_kg},1)', 11),
    CA('rank_key2', 'Meal and rank', 'text', '{col:meal}&"|"&{col:meal_rank}', 20), CA('cost_order', 'Cost for your order', 'money', 'ROUND({col:cost_child}*{set:order_children},2)', 11),
    CA('meal_avg', 'Average cost of the meal', 'money', 'AVERAGEIFS(%s,%s,{col:meal})' % (RG('menu', 'cost_child'), RG('menu', 'meal')), 11),
    CA('rank_key', 'Rank key', 'num', '{col:cost_child}+VALUE(RIGHT({col:menu_id},3))/1000000', 10),
    CA('meal_rank', 'Cost rank in the meal', 'int', 'COUNTIFS(%s,{col:meal},%s,">"&{col:rank_key})+1' % (RG('menu', 'meal'), RG('menu', 'rank_key')), 10),
    CA('save_vs_avg', 'Saving per child if swapped', 'money', 'MAX(0,{col:cost_child}-{col:meal_avg})', 11)] + [
    CA(k, 'Dish at ' + lab.lower(), 'text', 'IFERROR(INDEX(%s,MATCH({col:dkey}&"|"&%s,%s,0))&"","")' % (RG('menu', 'dish'), t, RG('menu', 'mkey')), 26)
    for k, lab, t in (('dish_b', 'Breakfast', MB), ('dish_l', 'Lunch', ML_), ('dish_s', 'Afternoon snack', MS_))],
    D.menu_d(), 80, [A('meal_rank', '<= 2', 'warn'), A('meal_rank', '>= 14', 'good')]))

# 3 menu cost by week
tables.append(T('menu_week', 'Menu Cost by Week', 'Meals, child-days and food cost by week',
    'One row per week: type the open days, the child-days present, the meals served by type and the cost of the meals; the cost per child-day, your own 12-week average and the above or below check fill in.', [
    C('mw_id', 'Week ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), C('open_days', 'Open days', 'int', 8), C('child_days', 'Child-days present', 'int', 10),
    C('served_b', 'Breakfasts served', 'int', 10), C('served_l', 'Lunches served', 'int', 9), C('served_s', 'Snacks served', 'int', 9), C('meals_cost', 'Cost of meals', 'money', 11),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:week}),MONTH({col:week}),1)', 11), CA('meals_served', 'Meals served', 'int', '{col:served_b}+{col:served_l}+{col:served_s}', 9),
    CA('meals_per_day', 'Meals per open day', 'num', 'IF({col:open_days}>0,ROUND({col:meals_served}/{col:open_days},1),0)', 10),
    CA('cost_child_day', 'Cost per child-day', 'money', 'IF({col:child_days}>0,ROUND({col:meals_cost}/{col:child_days},3),0)', 10),
    CA('avg12', 'Your 12-week average', 'money', 'AVERAGEIFS(%s,%s,">="&({col:week}-77),%s,"<="&{col:week})' % (RG('menu_week', 'cost_child_day'), RG('menu_week', 'week'), RG('menu_week', 'week')), 10),
    CA('vs_usual', 'Against your usual', 'pct', 'IF({col:avg12}>0,{col:cost_child_day}/{col:avg12}-1,0)', 10),
    CA('cost_flag', 'Cost check', 'text', 'IF({col:vs_usual}>{set:cost_band},%s,IF({col:vs_usual}<-{set:cost_band},%s,%s))' % (fl('Above your usual'), fl('Below your usual'), fl('Near your usual')), 17),
    CA('at_or_below', 'At or below usual', 'int', 'IF({col:vs_usual}<={set:cost_band},1,0)', 9), CA('cook_phone', 'Cook phone', 'text', PH(D.COOK_PHONE), 18)],
    D.menu_week_d(), 80, [A('cost_flag', '= ' + fl('Above your usual'), 'warn'), A('cost_flag', '= ' + fl('Below your usual'), 'good')]))

# 4 meal claim by month
CLAIM_RATE = 'IF({col:meal}=%s,{set:claim_breakfast},IF({col:meal}=%s,{set:claim_lunch},{set:claim_snack}))' % (MB, ML_)
tables.append(T('claim', 'Meal Claim by Month', 'Meal-program claim by month and meal',
    'One row per month and meal: type the children present, the meals served, the eligible meals and the days that failed the count check; the claim amount at your rates and the ready or fix check fill in.', [
    C('claim_id', 'Claim ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('meal', 'Meal', 'meal', 15), C('children_present', 'Children present, meals', 'int', 11), C('served', 'Meals served', 'int', 9),
    C('eligible', 'Eligible meals', 'int', 9), C('days_failing', 'Days failing the check', 'int', 10),
    CA('claim_rate', 'Claim rate', 'money', CLAIM_RATE, 9), CA('claim_amount', 'Claim amount', 'money', 'ROUND({col:eligible}*%s,2)' % CLAIM_RATE, 11),
    CA('served_share', 'Served share of present', 'pct', 'IF({col:children_present}>0,{col:served}/{col:children_present},0)', 10),
    CA('eligible_share', 'Eligible share of served', 'pct', 'IF({col:served}>0,{col:eligible}/{col:served},0)', 10),
    CA('check_flag', 'Claim check', 'text', 'IF({col:days_failing}>0,%s,%s)' % (fl('Days to fix'), fl('Ready to claim')), 14), CA('owner_phone', 'Owner-director phone', 'text', PH(D.OWNER_PHONE), 18),
    CA('cook_phone', 'Cook phone', 'text', PH(D.COOK_PHONE), 18)],
    D.claim_d(), 100, [A('check_flag', '= ' + fl('Days to fix'), 'bad'), A('check_flag', '= ' + fl('Ready to claim'), 'good')]))

# 5 claim exceptions
def EXI(col): return 'IF({col:row_no}="","",INDEX(%s,{col:row_no}))' % RG('meals', col)
tables.append(T('exceptions', 'Claim Exceptions', 'The 12 tightest meal counts, over-counts first',
    'Type 1 to 12: the meal rows are ranked by served minus children present, so any meal served to more children than were present comes first; the day, meal, room and margin fill in.', [
    C('ex_id', 'Row ID', 'text', 9, required=True), C('place', 'Place in the ranking', 'int', 10),
    CA('row_no', 'Row in Meals', 'int', 'IFERROR(MATCH(LARGE(%s,{col:place}),%s,0),"")' % (RG('meals', 'margin_key'), RG('meals', 'margin_key')), 9),
    CA('date', 'Date', 'date', EXI('date'), 12), CA('meal', 'Meal', 'text', 'IF({col:row_no}="","",INDEX(%s,{col:row_no})&"")' % RG('meals', 'meal'), 15),
    CA('room', 'Room', 'text', 'IF({col:row_no}="","",INDEX(%s,{col:row_no})&"")' % RG('meals', 'room'), 12), CA('children_present', 'Children present', 'int', EXI('children_present'), 10), CA('served', 'Meals served', 'int', EXI('served'), 9),
    CA('margin', 'Served minus present', 'int', 'IF({col:row_no}="","",{col:served}-{col:children_present})', 10),
    CA('flag', 'Check', 'text', 'IF({col:margin}="","",IF({col:margin}>0,%s,IF({col:margin}=0,%s,%s)))' % (fl('Over the children present'), fl('At the limit'), fl('Counts consistent')), 20),
    CA('owner_phone', 'Owner-director phone', 'text', PH(D.OWNER_PHONE), 18)],
    D.exceptions_d(), 50, [A('flag', '= ' + fl('Over the children present'), 'bad'), A('flag', '= ' + fl('At the limit'), 'warn')]))

# 6 health records
tables.append(T('health', 'Health Records', 'Record status by child: status and due date only',
    'One row per child and record: type the status (on file, due, missing), due date and last checked; days past due and the family fill in. Status and dates only.', [
    C('record_id', 'Record ID', 'text', 9, required=True), C('child_id', 'Child ID', 'text', 9), REF('child', 'Child', 'children.child', 24), LST('room', 'Room', 'room', 12), LST('record', 'Record', 'hrecord', 20),
    LST('status', 'Status', 'hstatus', 10), C('due_date', 'Due date', 'date', 12), C('last_checked', 'Last checked', 'date', 12),
    CA('hkey', 'Record key', 'text', '{col:child_id}&"|"&{col:record}', 28), CA('id_no', 'Row number', 'int', 'VALUE(RIGHT({col:record_id},3))', 8),
    CA('family', 'Family', 'text', LKT('children.family', 'children.child_id', 'child_id'), 18),
    CA('days_past', 'Days past due', 'int', 'IF(AND({col:status}<>%s,{col:due_date}<{today}),{today}-{col:due_date},0)' % ONF, 9),
    CA('days_left', 'Days to the due date', 'int', '{col:due_date}-{today}', 9), CA('due_month', 'Due month', 'date', 'DATE(YEAR({col:due_date}),MONTH({col:due_date}),1)', 11),
    CA('record_flag', 'Record check', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:days_past}>0,%s,%s)))' % (ONF, fl('Record on file'), MISS, fl('Missing'), fl('Past due'), fl('Due soon')), 14),
    CA('chase_key', 'Chase ranking key', 'num', 'IF({col:status}=%s,"",100000+{today}-{col:due_date}+{col:id_no}/1000000)' % ONF, 11),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child_id', 'child_id'), 18), CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18),
    CA('ad_phone', 'Assistant director phone', 'text', PH(D.AD_PHONE), 18)],
    D.health_d(), 400, [A('record_flag', '= ' + fl('Past due'), 'bad'), A('record_flag', '= ' + fl('Missing'), 'warn'), A('record_flag', '= ' + fl('Record on file'), 'good')]))

# 7 status board by room
def HC(st): return 'COUNTIFS(%s,{col:room},%s,{col:record},%s,%s)' % (RG('health', 'room'), RG('health', 'record'), RG('health', 'status'), st)
tables.append(T('board', 'Status Board by Room', 'Records on file, due and missing by room and record',
    'One row per room and record type: the children with the record on file, due and missing, the share on file and the nearest due date are counted from Health Records.', [
    C('board_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), LST('record', 'Record', 'hrecord', 20),
    CA('on_file', 'On file', 'int', HC(ONF), 8), CA('due', 'Due', 'int', HC(DUE), 8), CA('missing', 'Missing', 'int', HC(MISS), 8), CA('total', 'Records', 'int', '{col:on_file}+{col:due}+{col:missing}', 8),
    CA('share_on_file', 'Share on file', 'pct', 'IF({col:total}>0,{col:on_file}/{col:total},0)', 10),
    CA('next_due', 'Nearest due date', 'date', 'IF({col:total}=0,"",SUMPRODUCT(MIN((%s<>{col:room})*1000000+(%s<>{col:record})*1000000+%s)))' % (
        RG('health', 'room'), RG('health', 'record'), RG('health', 'due_date')), 12),
    CA('board_flag', 'Board check', 'text', 'IF({col:missing}>0,%s,IF({col:due}>0,%s,%s))' % (fl('Records missing'), fl('Records due'), fl('All on file')), 15),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('ad_phone', 'Assistant director phone', 'text', PH(D.AD_PHONE), 18), CA('cook_phone', 'Cook phone', 'text', PH(D.COOK_PHONE), 18)],
    D.board_d(), 50, [A('board_flag', '= ' + fl('Records missing'), 'bad'), A('board_flag', '= ' + fl('Records due'), 'warn'), A('board_flag', '= ' + fl('All on file'), 'good')]))

# 8 cook's daily list
def HSTAT(rec): return 'IFERROR(INDEX(%s,MATCH({col:child_id}&"|"&%s,%s,0))&"","")' % (RG('health', 'status'), rec, RG('health', 'hkey'))
tables.append(T('cook', "Cook's Daily List", 'Allergy and medical-permission status for the cook',
    "One row per enrolled child: type the child ID; the room, the allergy status and the medical-permission status come from Health Records, status only. The cook sees who needs an update before a meal.", [
    C('child_id', 'Child ID', 'text', 9, required=True), CA('child', 'Child', 'text', LKT('children.child', 'children.child_id', 'child_id'), 22), CA('room', 'Room', 'text', LKT('children.room', 'children.child_id', 'child_id'), 12),
    CA('allergy', 'Allergy status', 'text', HSTAT(ALLERGY), 13), CA('permission', 'Medical permission', 'text', HSTAT(PERMIT), 13),
    CA('allergy_due', 'Allergy status due', 'date', 'IFERROR(INDEX(%s,MATCH({col:child_id}&"|"&%s,%s,0)),"")' % (RG('health', 'due_date'), ALLERGY, RG('health', 'hkey')), 12),
    CA('open_records', 'Records not on file', 'int', 'COUNTIFS(%s,{col:child_id},%s,"<>"&%s)' % (RG('health', 'child_id'), RG('health', 'status'), ONF), 10),
    CA('needs_update', 'Needs update', 'int', 'IF({col:allergy}<>%s,1,0)' % ONF, 9), CA('diet_flag', 'Diet list check', 'text', 'IF({col:needs_update}=1,%s,%s)' % (fl('Update needed'), fl('Current')), 14),
    CA('id_no', 'Row number', 'int', 'VALUE(RIGHT({col:child_id},3))', 8), CA('need_seq', 'Order in the room', 'int', 'IF({col:needs_update}=1,COUNTIFS(%s,{col:room},%s,1,%s,"<="&{col:id_no}),0)' % (RG('cook', 'room'), RG('cook', 'needs_update'), RG('cook', 'id_no')), 9),
    CA('need_key', 'Update key', 'text', 'IF({col:needs_update}=1,{col:room}&"|"&{col:need_seq},"")', 14),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child_id', 'child_id'), 18), CA('cook_phone', 'Cook phone', 'text', PH(D.COOK_PHONE), 18)],
    D.cook_d(), 100, [A('diet_flag', '= ' + fl('Update needed'), 'bad'), A('allergy', '= ' + ONF, 'good'), A('permission', '= ' + MISS, 'warn')]))

# 9 missing records follow-up
def FUI(col): return 'IF({col:row_no}="","",INDEX(%s,{col:row_no})&"")' % RG('health', col)
tables.append(T('follow', 'Missing Records Follow-up', 'Records not on file, oldest due date first',
    'Type 1, 2, 3 ...: the records that are due or missing are ranked by how long they are past their due date; the child, family, record, days past due, phone and the next step fill in.', [
    C('fu_id', 'Row ID', 'text', 9, required=True), C('place', 'Place in the list', 'int', 9),
    CA('row_no', 'Row in Health Records', 'int', 'IFERROR(MATCH(LARGE(%s,{col:place}),%s,0),"")' % (RG('health', 'chase_key'), RG('health', 'chase_key')), 10),
    CA('child', 'Child', 'text', FUI('child'), 22), CA('family', 'Family', 'text', FUI('family'), 18), CA('room', 'Room', 'text', FUI('room'), 12), CA('record', 'Record', 'text', FUI('record'), 20), CA('status', 'Status', 'text', FUI('status'), 10),
    CA('due_date', 'Due date', 'date', 'IF({col:row_no}="","",INDEX(%s,{col:row_no}))' % RG('health', 'due_date'), 12),
    CA('days_overdue', 'Days past due', 'int', 'IF({col:row_no}="","",INDEX(%s,{col:row_no}))' % RG('health', 'days_past'), 9),
    CA('phone', 'Family phone', 'text', FUI('phone'), 18),
    CA('action', 'Next step', 'text', 'IF({col:row_no}="","",IF({col:days_overdue}>={set:escalate_days},%s,IF({col:days_overdue}>={set:call_days},%s,%s)))' % (vd('Escalate to the owner'), vd('Call today'), vd('Send a reminder')), 20),
    CA('ad_phone', 'Assistant director phone', 'text', PH(D.AD_PHONE), 18)],
    D.follow_d(), 60, [A('action', '= ' + vd('Escalate to the owner'), 'bad'), A('action', '= ' + vd('Call today'), 'warn')]))

# 10 incidents
HRS = ','.join(tok('hourl', h) for h in HOURS_L)
tables.append(T('incidents', 'Incidents', 'Incident log: date, room, type and follow-up status',
    'One row per incident: date, time, child, room, type, whether the family was told and whether the follow-up is done; the hour and open days fill in. No medical wording.', [
    C('incident_id', 'Incident ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), C('incident_time', 'Time', 'time', 8), C('child_id', 'Child ID', 'text', 9), REF('child', 'Child', 'children.child', 22),
    LST('room', 'Room', 'room', 12), LST('type', 'Type', 'itype', 11), C('parent_informed', 'Family told', 'bool', 9), LST('staff', 'Staff member', 'staff', 18), LST('follow_up_done', 'Follow-up', 'fup', 10),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('hour_slot', 'Hour of the day', 'text', 'IFERROR(CHOOSE(INT(ROUND({col:incident_time}*1440,0)/60)-6,%s),"")' % HRS, 10),
    CA('open_days', 'Follow-up open days', 'int', 'IF({col:follow_up_done}=%s,{today}-{col:date},0)' % OPEN, 9), CA('id_no', 'Row number', 'int', 'VALUE(RIGHT({col:incident_id},3))', 8),
    CA('follow_flag', 'Follow-up check', 'text', 'IF({col:parent_informed}=%s,%s,IF({col:follow_up_done}=%s,%s,%s))' % (NO, fl('Parent not informed'), OPEN, fl('Follow-up open'), fl('Follow-up done')), 18),
    CA('open_key', 'Chase key', 'num', 'IF(OR({col:follow_up_done}=%s,{col:parent_informed}=%s),{today}-{col:date}+1+{col:id_no}/1000000,"")' % (OPEN, NO), 10),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child_id', 'child_id'), 18), CA('family', 'Family', 'text', LKT('children.family', 'children.child_id', 'child_id'), 18),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('ad_phone', 'Assistant director phone', 'text', PH(D.AD_PHONE), 18),
    CA('maint_phone', 'Maintenance phone', 'text', PH(D.MAINT_PHONE), 18)],
    D.incidents_d(), 400, [A('follow_flag', '= ' + fl('Follow-up open'), 'warn'), A('follow_flag', '= ' + fl('Parent not informed'), 'bad')]))

# 11 incidents by hour
def IHR(room): return 'COUNTIFS(%s,{col:hour},%s,%s)' % (RG('incidents', 'hour_slot'), RG('incidents', 'room'), tok('room', room))
tables.append(T('inc_hour', 'Incidents by Hour', 'Incidents by hour of the day, all rooms and by room',
    'One row per hour of the day: the incidents at that hour in all rooms and in each room are counted from the log, to show the hours when more happens.', [
    LST('hour', 'Hour of the day', 'hourl', 12, required=True), CA('incidents', 'Incidents', 'int', 'COUNTIFS(%s,{col:hour})' % RG('incidents', 'hour_slot'), 9),
    CA('share', 'Share of incidents', 'pct', 'IF(SUM(%s)>0,{col:incidents}/SUM(%s),0)' % (RG('inc_hour', 'incidents'), RG('inc_hour', 'incidents')), 10)] + [
    CA('c_' + r.lower().replace('-', ''), r, 'int', IHR(r), 10) for r in ROOMS],
    D.inc_hour_d(), 50, [A('incidents', '>= 15', 'warn')]))

# 12 incidents by room and month
tables.append(T('inc_month', 'Incidents by Room and Month', 'Incidents per 1,000 child-days by room and month',
    'One row per room and month: type the child-days present; the incidents come from the log and the rate per 1,000 child-days, your own usual rate for the room and the above or below check fill in.', [
    C('im_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), C('month', 'Month', 'date', 11), C('child_days', 'Child-days present', 'int', 10),
    CA('incidents', 'Incidents', 'int', 'COUNTIFS(%s,{col:room},%s,{col:month})' % (RG('incidents', 'room'), RG('incidents', 'month')), 9),
    CA('per1000', 'Per 1,000 child-days', 'num', 'IF({col:child_days}>0,ROUND({col:incidents}/{col:child_days}*1000,2),0)', 10),
    CA('usual', 'Your usual rate for the room', 'num', 'IFERROR(ROUND(SUMIFS(%s,%s,{col:room})/SUMIFS(%s,%s,{col:room})*1000,2),0)' % (RG('inc_month', 'incidents'), RG('inc_month', 'room'), RG('inc_month', 'child_days'), RG('inc_month', 'room')), 11),
    CA('rate_flag', 'Rate check', 'text', 'IF({col:per1000}>{col:usual}*(1+{set:rate_band}),%s,IF({col:per1000}<{col:usual}*(1-{set:rate_band}),%s,%s))' % (fl('Above your usual'), fl('Below your usual'), fl('Near your usual')), 17),
    CA('room_90', 'Incidents, last 3 months', 'int', 'SUMIFS(%s,%s,{col:room},%s,">="&EDATE(%s,-2))' % (RG('inc_month', 'incidents'), RG('inc_month', 'room'), RG('inc_month', 'month'), MS), 10),
    CA('owner_phone', 'Owner-director phone', 'text', PH(D.OWNER_PHONE), 18)],
    D.inc_month_d(), 100, [A('rate_flag', '= ' + fl('Above your usual'), 'warn'), A('rate_flag', '= ' + fl('Below your usual'), 'good')]))

# 13 drills
tables.append(T('drills', 'Drills', 'Emergency drills held',
    'One row per drill: date, kind, minutes, children present, the staff member who ran it and its status; the month fills in. The plan on Drill Schedule by Month reads from here.', [
    C('drill_id', 'Drill ID', 'text', 9, required=True), C('date', 'Date', 'date', 12), LST('kind', 'Kind', 'drill', 17), C('minutes', 'Minutes', 'int', 8), C('children_present', 'Children present', 'int', 10),
    LST('staff', 'Run by', 'staff', 18), LST('status', 'Status', 'dstatus', 9), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('children_per_minute', 'Children per minute', 'num', 'IF({col:minutes}>0,ROUND({col:children_present}/{col:minutes},1),0)', 10), CA('owner_phone', 'Owner-director phone', 'text', PH(D.OWNER_PHONE), 18)],
    D.drills_d(), 100, [A('minutes', '>= 9', 'warn')]))

# 14 drill schedule by month
def DK(k): return '{col:kind}=%s' % tok('drill', k)
FREQ = 'IF(%s,{set:drill_fire},IF(%s,{set:drill_evac},IF(%s,{set:drill_lockdown},{set:drill_shelter})))' % (DK('Fire drill'), DK('Evacuation drill'), DK('Lockdown drill'))
tables.append(T('drill_plan', 'Drill Schedule by Month', 'Drill plan by month and kind with the done date',
    'One row per month and drill kind: the months between drills come from your settings; the last drill before the month, the due date, the done date and the status are worked out from Drills.', [
    C('dp_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'drill', 17),
    CA('freq', 'Months between drills', 'int', FREQ, 9),
    CA('last_prior', 'Last drill before the month', 'date', 'IF(SUMPRODUCT(MAX((%s={col:kind})*(%s<{col:month})*%s))=0,"",SUMPRODUCT(MAX((%s={col:kind})*(%s<{col:month})*%s)))' % (
        RG('drills', 'kind'), RG('drills', 'date'), RG('drills', 'date'), RG('drills', 'kind'), RG('drills', 'date'), RG('drills', 'date')), 12),
    CA('due_date', 'Due date', 'date', 'IF({col:last_prior}="",{col:month},EDATE({col:last_prior},{col:freq}))', 12),
    CA('done_on', 'Done on', 'date', 'IF(SUMPRODUCT(MAX((%s={col:kind})*(%s>={col:month})*(%s<=EOMONTH({col:month},0))*%s))=0,"",SUMPRODUCT(MAX((%s={col:kind})*(%s>={col:month})*(%s<=EOMONTH({col:month},0))*%s)))' % (
        RG('drills', 'kind'), RG('drills', 'date'), RG('drills', 'date'), RG('drills', 'date'), RG('drills', 'kind'), RG('drills', 'date'), RG('drills', 'date'), RG('drills', 'date')), 12),
    CA('due', 'Due in the month', 'int', 'IF({col:month}>%s,IF(AND({col:due_date}>={col:month},{col:due_date}<=EOMONTH({col:month},0)),1,0),IF({col:due_date}<=EOMONTH({col:month},0),1,0))' % MS, 9),
    CA('flag', 'Status', 'text', 'IF({col:done_on}<>"",%s,IF({col:due}=0,%s,IF({col:month}>%s,%s,IF({col:month}<%s,%s,IF({col:due_date}<{today},%s,%s)))))' % (
        fl('Done'), fl('Not due'), MS, fl('Planned'), MS, fl('Missed in month'), fl('Overdue'), fl('Due this month')), 15),
    CA('overdue', 'Overdue', 'int', 'IF({col:flag}=%s,1,0)' % fl('Overdue'), 8), CA('is_now', 'This month', 'int', 'IF({col:month}=%s,1,0)' % MS, 8),
    CA('ok_now', 'This month and not overdue', 'int', 'IF(AND({col:is_now}=1,{col:overdue}=0),1,0)', 9),
    CA('ad_phone', 'Assistant director phone', 'text', PH(D.AD_PHONE), 18), CA('owner_phone', 'Owner-director phone', 'text', PH(D.OWNER_PHONE), 18),
    CA('lead_phone', 'Lead teacher phone', 'text', PH(D.TEACHER_PHONE['Infants']), 18)],
    D.drill_plan_d(), 80, [A('flag', '= ' + fl('Overdue'), 'bad'), A('flag', '= ' + fl('Due this month'), 'warn'), A('flag', '= ' + fl('Done'), 'good')]))

# 15 checks
tables.append(T('checks', 'Checks', 'Cleaning and safety checks by room',
    'One row per room check: date, room, kind (deep clean, safety check, equipment check), done or missed, who did it and the minutes; the week and month fill in.', [
    C('check_id', 'Check ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), LST('room', 'Room', 'room', 12), LST('kind', 'Kind', 'ckind', 16), LST('status', 'Status', 'checkstatus', 9),
    C('done_by', 'Done by', 'text', 20), C('minutes', 'Minutes', 'int', 8),
    CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18)],
    D.checks_d(), 1500, [A('status', '= ' + MISSED, 'bad')]))

# 16 check completion by room and week
def CW(st): return 'COUNTIFS(%s,{col:room},%s,{col:week},%s,%s)' % (RG('checks', 'room'), RG('checks', 'week'), RG('checks', 'status'), st)
tables.append(T('check_week', 'Check Completion by Week', 'Check completion by room and week',
    'One row per room and week: the checks done and missed are counted from the Checks log, with the completion share against your target.', [
    C('cw_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), C('week', 'Week (Monday)', 'date', 12),
    CA('done', 'Done', 'int', CW(DONE), 8), CA('missed', 'Missed', 'int', CW(MISSED), 8), CA('total', 'Checks', 'int', '{col:done}+{col:missed}', 8),
    CA('completion', 'Completion share', 'pct', 'IF({col:total}>0,{col:done}/{col:total},0)', 10),
    CA('target_flag', 'Target check', 'text', 'IF({col:completion}>={set:completion_target},%s,%s)' % (fl('On target'), fl('Below target')), 13),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('ad_phone', 'Assistant director phone', 'text', PH(D.AD_PHONE), 18), CA('cleaner_phone', 'Cleaner phone', 'text', PH(D.CLEANER_PHONE), 18)],
    D.check_week_d(), 100, [A('target_flag', '= ' + fl('Below target'), 'warn'), A('target_flag', '= ' + fl('On target'), 'good')]))

# 17 cleaning and safety schedule
CSF = 'IF({col:kind}=%s,{set:check_deep},IF({col:kind}=%s,{set:check_safety},{set:check_equip}))' % (tok('ckind', 'Deep clean'), tok('ckind', 'Safety check'))
LASTD = 'SUMPRODUCT(MAX((%s={col:room})*(%s={col:kind})*(%s=%s)*%s))' % (RG('checks', 'room'), RG('checks', 'kind'), RG('checks', 'status'), DONE, RG('checks', 'date'))
tables.append(T('clean_sched', 'Cleaning and Safety Schedule', 'Cleaning and safety schedule by room and kind',
    'One row per room and check kind: the days between checks come from your settings; the last done date, the next due date and the overdue check are worked out from the Checks log.', [
    C('cs_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), LST('kind', 'Kind', 'ckind', 16),
    CA('freq_days', 'Days between checks', 'int', CSF, 9), CA('last_done', 'Last done', 'date', 'IF(%s=0,"",%s)' % (LASTD, LASTD), 12),
    CA('next_due', 'Next due', 'date', 'IF({col:last_done}="","",{col:last_done}+{col:freq_days})', 12),
    CA('days_overdue', 'Days overdue', 'int', 'IF({col:next_due}="",0,MAX(0,{today}-{col:next_due}))', 9),
    CA('sched_flag', 'Schedule check', 'text', 'IF({col:days_overdue}>0,%s,IF({col:next_due}-{today}<=2,%s,%s))' % (fl('Overdue'), fl('Due soon'), fl('On time')), 13),
    CA('room_missed', 'Missed in the room, last 90 days', 'int', 'COUNTIFS(%s,{col:room},%s,%s,%s,">"&({today}-90))' % (RG('checks', 'room'), RG('checks', 'status'), MISSED, RG('checks', 'date')), 11),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('cleaner_phone', 'Cleaner phone', 'text', PH(D.CLEANER_PHONE), 18),
    CA('maint_phone', 'Maintenance phone', 'text', PH(D.MAINT_PHONE), 18), CA('assistant_phone', 'Assistant phone', 'text', PH(D.ASSIST_PHONE), 18)],
    D.clean_sched_d(), 50, [A('sched_flag', '= ' + fl('Overdue'), 'bad'), A('sched_flag', '= ' + fl('Due soon'), 'warn')]))

# 18 food purchases
tables.append(T('food', 'Food Purchases', 'Weekly food purchases and cost per child-day',
    'One row per food order paid: date, category, description, amount and who was paid; the week, the child-days of that week, the cost per child-day and the above or below check fill in.', [
    C('exp_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), C('category', 'Category', 'text', 18), C('description', 'Description', 'text', 28), C('amount', 'Amount', 'money', 11), C('paid_to', 'Paid to', 'text', 18),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12),
    CA('child_days', 'Child-days that week', 'int', 'SUMIFS(%s,%s,{col:week})' % (RG('menu_week', 'child_days'), RG('menu_week', 'week')), 10),
    CA('per_child_day', 'Cost per child-day', 'money', 'IF({col:child_days}>0,ROUND({col:amount}/{col:child_days},3),0)', 10),
    CA('cost_flag', 'Cost check', 'text', 'IF({col:per_child_day}>AVERAGE(%s)*(1+{set:cost_band}),%s,IF({col:per_child_day}<AVERAGE(%s)*(1-{set:cost_band}),%s,%s))' % (
        RG('food', 'per_child_day'), fl('Above your usual'), RG('food', 'per_child_day'), fl('Below your usual'), fl('Near your usual')), 17),
    CA('supplier_phone', 'Food supplier phone', 'text', PH(D.SUPPLIER_PHONE), 18), CA('cook_phone', 'Cook phone', 'text', PH(D.COOK_PHONE), 18)],
    D.food_d(), 120, [A('cost_flag', '= ' + fl('Above your usual'), 'warn'), A('cost_flag', '= ' + fl('Below your usual'), 'good')]))

# 19 children
tables.append(T('children', 'Children', 'Children with room, status and schedule',
    'One row per child, current and past: room, status, start date and schedule, with the parent or guardian and phone for messages. Names, rooms, statuses and dates only.', [
    C('child_id', 'Child ID', 'text', 9, required=True), C('child', 'Child', 'text', 24), C('family', 'Family', 'text', 20), LST('room', 'Room', 'room', 12), LST('status', 'Status', 'cstatus', 13),
    C('start_date', 'Start date', 'date', 12), LST('schedule', 'Schedule', 'schedule', 13), C('guardian', 'Parent or guardian', 'text', 22), C('phone', 'Phone', 'text', 18),
    CA('next_day', 'Next working day', 'date', 'WORKDAY({today},1)', 12), CA('last_drill', 'Last drill', 'date', 'MAX(%s)' % RG('drills', 'date'), 12)],
    D.children_d(), 150, [A('status', '= ' + tok('cstatus', 'Left'), 'bad'), A('status', '= ' + tok('cstatus', 'Starting soon'), 'warn'), A('status', '= ' + tok('cstatus', 'Enrolled'), 'good')]))

# 20 rooms
tables.append(T('rooms', 'Rooms', 'Rooms with licensed places and ratio',
    'One row per room: the licensed places and the ratio, the number of children each staff member may care for, check your local rules. Room is an age group, in a home daycare the one space you use.', [
    C('room', 'Room', 'text', 24, required=True), C('capacity', 'Licensed places', 'int', 11), C('ratio', 'Children per staff', 'int', 11)], D.rooms_d(), 50))
assert len(tables) == 20
