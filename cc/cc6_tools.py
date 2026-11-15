"""Childcare center suite part 6: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc6_lists import *
import cc6_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, default_label): return IN(k, label, 'list', key(lst, default_label), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def R(t, c): return '{range:%s.%s}' % (t, c)
def SF(t, c, *cr): return 'SUMIFS(%s,%s)' % (R(t, c), ','.join('%s,%s' % (R(t, k), v) for k, v in cr))
def CF(t, *cr): return 'COUNTIFS(%s)' % ','.join('%s,%s' % (R(t, k), v) for k, v in cr)
def RT(x): return '=' + tok('room', x)
def MT(x): return '=' + tok('meal', x)
def KT(x): return '=' + tok('drill', x)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
ONF, DUE, MISS = tok('hstatus', 'On file'), tok('hstatus', 'Due'), tok('hstatus', 'Missing')
DONE, MISSED = tok('checkstatus', 'Done'), tok('checkstatus', 'Missed')
MB, ML_, MS_ = tok('meal', 'Breakfast'), tok('meal', 'Lunch'), tok('meal', 'Afternoon snack')
ENR = tok('cstatus', 'Enrolled'); OPEN = tok('fup', 'Open'); NO = '{list:yesno.no}'
def DICE(room_expr, parts):
    """IF chain over the five rooms: parts(room) gives the expression for that room"""
    f = '0'
    for r in reversed(ROOMS): f = 'IF(%s=%s,%s,%s)' % (room_expr, tok('room', r), parts(r), f)
    return f
FAIL = tuple(int(x) for x in max(m['date'] for m in D.ML if m['served'] > m['children_present']).split('-'))

tools = []

# 1 meal and menu planner with cost
def DISH(m, col='dish'): return 'IFERROR(INDEX(%s,MATCH({in:cycle}&"|"&{in:day}&"|"&%s,%s,0)),0)' % (R('menu', col), m, R('menu', 'mkey'))
def TAKE(c): return 'IFERROR(SUM(%s)/SUMIFS(%s,%s,">"&({today}-84)),0)' % ('SUMIFS(%s,%s,">"&({today}-84))' % (R('menu_week', c), R('menu_week', 'week')), R('menu_week', 'child_days'), R('menu_week', 'week'))
TB, TL, TS = TAKE('served_b'), TAKE('served_l'), TAKE('served_s')
EXP1 = '(%s*%s+%s*%s+%s*%s)' % (DISH(MB, 'cost_child'), TB, DISH(ML_, 'cost_child'), TL, DISH(MS_, 'cost_child'), TS)
USUAL1 = 'IFERROR(SUMIFS(%s,%s,">"&({today}-84))/SUMIFS(%s,%s,">"&({today}-84)),0)' % (R('menu_week', 'meals_cost'), R('menu_week', 'week'), R('menu_week', 'child_days'), R('menu_week', 'week'))
tools.append(TOOL('meal_planner', 'Meal and Menu Planner', 'Meal and menu planner with cost',
    'Pick a cycle week, a weekday and the children expected: see the dishes, the meals to prepare, the cost per child-day and whether it is within your usual cost.', [
    I('cycle', 'Menu cycle week', 2), IN('day', 'Weekday', 'list', key('wday', 'Wednesday'), list='wday'), I('children', 'Children expected that day', 36)], [
    O('Breakfast dish', 'text', DISH(MB)), O('Lunch dish', 'text', DISH(ML_)), O('Afternoon snack dish', 'text', DISH(MS_)),
    O('Menu cost of the three meals per child', 'money', '%s+%s+%s' % (DISH(MB, 'cost_child'), DISH(ML_, 'cost_child'), DISH(MS_, 'cost_child'))),
    O('Share of children who take breakfast, your last 12 weeks', 'pct', TB), O('Share who take lunch', 'pct', TL), O('Share who take the afternoon snack', 'pct', TS),
    O('Breakfasts to prepare', 'int', 'ROUND({in:children}*%s,0)' % TB), O('Lunches to prepare', 'int', 'ROUND({in:children}*%s,0)' % TL), O('Snacks to prepare', 'int', 'ROUND({in:children}*%s,0)' % TS),
    O('Expected cost per child-day', 'money', EXP1), O('Expected food cost of the day', 'money', '{in:children}*%s' % EXP1), O('Your usual cost per child-day, last 12 weeks', 'money', USUAL1),
    O('Against your usual', 'pct', 'IFERROR(%s/%s-1,0)' % (EXP1, USUAL1)),
    O('Verdict', 'text', 'IF(%s<=%s*(1+{set:cost_band}),%s,%s)' % (EXP1, USUAL1, vd('Within your usual cost'), vd('Above your usual cost')))],
    GR('What if', ('Cycle week 1, Monday', {'cycle': 1, 'day': '=' + tok('wday', 'Monday')}), ('Cycle week 3, Friday', {'cycle': 3, 'day': '=' + tok('wday', 'Friday')}), ('Cycle week 4, Tuesday', {'cycle': 4, 'day': '=' + tok('wday', 'Tuesday')}),
       ('A full house of 44 children', {'children': 44}), ('A quiet day of 28 children', {'children': 28}))))

# 2 meal-program claim sheet
def CL(col, meal=None): return SF('claim', col, ('month', '{in:month}')) if meal is None else SF('claim', col, ('month', '{in:month}'), ('meal', meal))
PREV3 = 'IFERROR(SUMIFS(%s,%s,">="&EDATE({in:month},-3),%s,"<"&{in:month})/3,0)' % (R('claim', 'claim_amount'), R('claim', 'month'), R('claim', 'month'))
tools.append(TOOL('claim_sheet', 'Meal-Program Claim Sheet', 'Meal-program claim by month and meal type',
    'Pick a month: see meals served and eligible by type, the claim at your own rates and the days where meals served exceed children present. A claim is made to a food program.', [
    I('month', 'First day of the month', iso(month_start(1)), 'date')], [
    O('Breakfasts served', 'int', CL('served', MB)), O('Breakfasts eligible', 'int', CL('eligible', MB)), O('Lunches served', 'int', CL('served', ML_)), O('Lunches eligible', 'int', CL('eligible', ML_)),
    O('Snacks served', 'int', CL('served', MS_)), O('Snacks eligible', 'int', CL('eligible', MS_)), O('Meals served in total', 'int', CL('served')), O('Meals eligible in total', 'int', CL('eligible')),
    O('Children present at those meals', 'int', CL('children_present')), O('Claim at your rates', 'money', CL('claim_amount')), O('Claim of the three months before', 'money', '%s*3' % PREV3),
    O('Change against your 3-month average', 'pct', 'IFERROR(%s/%s-1,0)' % (CL('claim_amount'), PREV3)), O('Days failing the count check', 'int', CL('days_failing')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (CL('days_failing'), vd('Claim ready'), CL('days_failing'), vd('day(s) to fix')))],
    GR('What if', ('Two months back', {'month': '=EDATE(%s,-2)' % MS}), ('Three months back', {'month': '=EDATE(%s,-3)' % MS}), ('The month with an over-count', {'month': '=DATE(%s,%s,1)' % (FAIL[0], FAIL[1])}),
       ('A year ago', {'month': '=EDATE(%s,-12)' % MS}), ('This month so far', {'month': '=' + MS}))))

# 3 allergy and medical-permission status board
TOT3 = lambda st: SF('board', st, ('room', '{in:room}'), ('record', '{in:record}'))
NXT3 = SF('board', 'next_due', ('room', '{in:room}'), ('record', '{in:record}'))
tools.append(TOOL('status_board', 'Status Board', 'Allergy and permission status board',
    'Pick a room and a record type: see how many children have the record on file, due or missing, the nearest due date and the records past due in the room. Status only, no health detail is stored.', [
    IL('room', 'Room', 'room', 'Preschool'), IL('record', 'Record', 'hrecord', 'Allergy status')], [
    O('Children with the record on file', 'int', TOT3('on_file')), O('Children with the record due', 'int', TOT3('due')), O('Children with the record missing', 'int', TOT3('missing')),
    O('Share on file', 'pct', 'IFERROR(%s/(%s+%s+%s),0)' % (TOT3('on_file'), TOT3('on_file'), TOT3('due'), TOT3('missing'))),
    O('Nearest due date', 'date', 'IF(%s=0,"",%s)' % (NXT3, NXT3)), O('Days to that date', 'int', 'IF(%s=0,"",%s-{today})' % (NXT3, NXT3)),
    O('Records of all types not on file in the room', 'int', CF('health', ('room', '{in:room}'), ('status', '"<>"&' + ONF))),
    O('Records past their due date in the room', 'int', CF('health', ('room', '{in:room}'), ('days_past', '">0"'))), O('Share on file, all rooms and records', 'pct', 'IFERROR(%s/COUNTIFS(%s,"<>"),0)' % (CF('health', ('status', ONF)), R('health', 'record_id'))),
    O('Verdict', 'text', 'IF(AND(%s=0,%s=0),%s,%s&" "&%s&", "&%s&" "&%s)' % (TOT3('due'), TOT3('missing'), vd('All on file'), TOT3('due'), vd('due'), TOT3('missing'), vd('missing')))],
    GR('What if', ('Infants, allergy status', {'room': RT('Infants')}), ('Toddlers, medical permission', {'room': RT('Toddlers'), 'record': '=' + tok('hrecord', 'Medical permission')}), ('Twos, immunisation record', {'room': RT('Twos'), 'record': '=' + tok('hrecord', 'Immunisation record')}),
       ('Preschool, immunisation record', {'record': '=' + tok('hrecord', 'Immunisation record')}), ('School-age, emergency contacts', {'room': RT('School-age'), 'record': '=' + tok('hrecord', 'Emergency contacts')}))))

# 4 incident pattern finder
def RCOL(c): return DICE('{in:room}', lambda r: c(r))
CR = lambda r: R('inc_hour', 'c_' + r.lower().replace('-', ''))
MX4 = DICE('{in:room}', lambda r: 'MAX(%s)' % CR(r))
BH4 = DICE('{in:room}', lambda r: 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('inc_hour', 'hour'), CR(r), CR(r)))
tools.append(TOOL('incident_pattern', 'Incident Pattern Finder', 'Which hour of the day and which room need a closer look',
    'Pick a room: incidents are counted by hour and type to find the busiest hour; a count at or above your minimum is a pattern to watch. No medical wording.', [
    IL('room', 'Room', 'room', 'Preschool'), I('minimum', 'Incidents at one hour that make a pattern', 3)], [
    O('Incidents of the room in your log', 'int', CF('incidents', ('room', '{in:room}'))), O('Busiest hour of the room', 'text', BH4), O('Incidents at that hour', 'int', MX4),
    O('Share of the room\'s incidents at that hour', 'pct', 'IFERROR((%s)/%s,0)' % (MX4, CF('incidents', ('room', '{in:room}')))),
    O('Falls', 'int', CF('incidents', ('room', '{in:room}'), ('type', tok('itype', 'Fall')))), O('Bites', 'int', CF('incidents', ('room', '{in:room}'), ('type', tok('itype', 'Bite')))),
    O('Collisions', 'int', CF('incidents', ('room', '{in:room}'), ('type', tok('itype', 'Collision')))), O('Other', 'int', CF('incidents', ('room', '{in:room}'), ('type', tok('itype', 'Other')))),
    O('Busiest hour of all rooms', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('inc_hour', 'hour'), R('inc_hour', 'incidents'), R('inc_hour', 'incidents'))), O('Incidents at that hour, all rooms', 'int', 'MAX(%s)' % R('inc_hour', 'incidents')),
    O('Verdict', 'text', 'IF((%s)>={in:minimum},%s,%s)' % (MX4, vd('Watch this hour'), vd('No pattern')))],
    GR('What if', ('Infants', {'room': RT('Infants')}), ('Toddlers', {'room': RT('Toddlers')}), ('Twos', {'room': RT('Twos')}), ('School-age', {'room': RT('School-age')}), ('Pattern from 5 incidents', {'minimum': 5}))))

# 5 emergency drill planner
def LASTK(k): return 'SUMPRODUCT(MAX((%s=%s)*%s))' % (R('drills', 'kind'), k, R('drills', 'date'))
LK5 = LASTK('{in:kind}')
tools.append(TOOL('drill_planner', 'Emergency Drill Planner', 'Drills needed a year, done and overdue',
    'Pick a drill kind and the months between drills: see the drills a year needs, those done, the next due date and the minutes a year; the verdict counts overdue drills.', [
    IL('kind', 'Drill kind', 'drill', 'Shelter drill'), I('plan', 'Months between drills, your plan', 3)], [
    O('Drills needed in a year', 'int', 'ROUNDUP(12/{in:plan},0)'), O('Drills done in the last 12 months', 'int', CF('drills', ('kind', '{in:kind}'), ('date', '">"&EDATE({today},-12)'))),
    O('Drills short in the year', 'int', 'MAX(0,ROUNDUP(12/{in:plan},0)-%s)' % CF('drills', ('kind', '{in:kind}'), ('date', '">"&EDATE({today},-12)'))),
    O('Last drill of this kind', 'date', 'IF(%s=0,"",%s)' % (LK5, LK5)), O('Next due date', 'date', 'IF(%s=0,{today},EDATE(%s,{in:plan}))' % (LK5, LK5)), O('Days to the due date, negative when overdue', 'int', 'IF(%s=0,0,EDATE(%s,{in:plan})-{today})' % (LK5, LK5)),
    O('Average minutes of a drill', 'num', 'IFERROR(AVERAGEIFS(%s,%s,{in:kind}),0)' % (R('drills', 'minutes'), R('drills', 'kind'))), O('Minutes a year at this plan', 'num', 'ROUNDUP(12/{in:plan},0)*IFERROR(AVERAGEIFS(%s,%s,{in:kind}),0)' % (R('drills', 'minutes'), R('drills', 'kind'))),
    O('Average children present at this kind', 'num', 'IFERROR(AVERAGEIFS(%s,%s,{in:kind}),0)' % (R('drills', 'children_present'), R('drills', 'kind'))),
    O('Drills overdue under your settings', 'int', 'COUNTIFS(%s,1)' % R('drill_plan', 'overdue')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,1)=0,%s,COUNTIFS(%s,1)&" "&%s)' % (R('drill_plan', 'overdue'), vd('All drills current'), R('drill_plan', 'overdue'), vd('overdue')))],
    GR('What if', ('Fire drill every month', {'kind': KT('Fire drill'), 'plan': 1}), ('Evacuation drill every 3 months', {'kind': KT('Evacuation drill')}), ('Lockdown drill every 4 months', {'kind': KT('Lockdown drill'), 'plan': 4}),
       ('Shelter drill every 6 months', {'plan': 6}), ('Fire drill every 2 months', {'kind': KT('Fire drill'), 'plan': 2}))))

# 6 cleaning and safety completion tracker
WIN6 = '">"&({today}-7*{in:weeks})'
CT6 = lambda st, extra=(): CF('checks', ('room', '{in:room}'), ('status', st), ('date', WIN6), *extra)
TOT6 = CF('checks', ('room', '{in:room}'), ('date', WIN6))
tools.append(TOOL('clean_tracker', 'Cleaning and Safety Tracker', 'Cleaning and safety check completion for a room',
    'Pick a room and the weeks to look back: see checks done and missed by kind and the completion share against your target. It helps you keep track; it is not a safety guarantee.', [
    IL('room', 'Room', 'room', 'Toddlers'), I('weeks', 'Weeks to look back', 13), I('target', 'Completion share you want', 0.95, 'pct')], [
    O('Checks logged', 'int', TOT6), O('Checks done', 'int', CT6(DONE)), O('Checks missed', 'int', CT6(MISSED)), O('Completion share', 'pct', 'IFERROR(%s/(%s),0)' % (CT6(DONE), TOT6)),
    O('Deep cleans missed', 'int', CT6(MISSED, [('kind', tok('ckind', 'Deep clean'))])), O('Safety checks missed', 'int', CT6(MISSED, [('kind', tok('ckind', 'Safety check'))])), O('Equipment checks missed', 'int', CT6(MISSED, [('kind', tok('ckind', 'Equipment check'))])),
    O('Minutes spent on checks of the room', 'int', 'SUMIFS(%s,%s,{in:room},%s,%s)' % (R('checks', 'minutes'), R('checks', 'room'), R('checks', 'date'), WIN6)),
    O('Completion share, all rooms', 'pct', 'IFERROR(COUNTIFS(%s,%s,%s,%s)/COUNTIFS(%s,%s),0)' % (R('checks', 'status'), DONE, R('checks', 'date'), WIN6, R('checks', 'date'), WIN6)),
    O('Last check done in the room', 'date', 'SUMPRODUCT(MAX((%s={in:room})*(%s=%s)*%s))' % (R('checks', 'room'), R('checks', 'status'), DONE, R('checks', 'date'))),
    O('Verdict', 'text', 'IF(IFERROR(%s/(%s),0)>={in:target},%s,%s)' % (CT6(DONE), TOT6, vd('On track'), vd('Missing checks')))],
    GR('What if', ('Infants', {'room': RT('Infants')}), ('School-age', {'room': RT('School-age')}), ('Preschool', {'room': RT('Preschool')}), ('Toddlers, last 4 weeks', {'weeks': 4}), ('Toddlers, target 99 percent', {'target': 0.99}))))

# 7 shopping list builder
KG7 = lambda m: '{in:children}*SUMIFS(%s,%s,{in:cycle},%s,%s)' % (R('menu', 'kg_per_child'), R('menu', 'cycle_week'), R('menu', 'meal'), m)
TOTKG7 = '(%s+%s+%s)' % (KG7(MB), KG7(ML_), KG7(MS_))
tools.append(TOOL('shopping_list', 'Shopping List Builder', 'Shopping list for a menu week',
    'Pick a menu cycle week and the children eating each meal: portions divided by portions a kilogram give the kilograms to buy, with the cost, the supplier and the order date.', [
    I('cycle', 'Menu cycle week', 2), I('children', 'Children eating each meal', 40), I('delivery', 'Delivery date', ahead(1), 'date'), I('lead', 'Days the supplier needs', 2)], [
    O('Kilograms for breakfasts', 'num', 'ROUND(%s,1)' % KG7(MB)), O('Kilograms for lunches', 'num', 'ROUND(%s,1)' % KG7(ML_)), O('Kilograms for afternoon snacks', 'num', 'ROUND(%s,1)' % KG7(MS_)),
    O('Kilograms to order for the week', 'num', 'ROUND(%s,1)' % TOTKG7), O('Cost of the week at menu prices', 'money', '{in:children}*SUMIFS(%s,%s,{in:cycle})' % (R('menu', 'cost_child'), R('menu', 'cycle_week'))),
    O('Cost per child for the week', 'money', 'SUMIFS(%s,%s,{in:cycle})' % (R('menu', 'cost_child'), R('menu', 'cycle_week'))), O('Dishes in the week', 'int', 'COUNTIFS(%s,{in:cycle})' % R('menu', 'cycle_week')),
    O('Food supplier', 'text', 'INDEX(%s,1)&""' % R('food', 'paid_to')), O('Supplier phone', 'text', 'INDEX(%s,1)&""' % R('food', 'supplier_phone')),
    O('Place the order by', 'date', 'WORKDAY({in:delivery},-{in:lead})'), O('Your last weekly purchase', 'money', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('food', 'amount'), R('food', 'date'), R('food', 'date'))),
    O('Verdict', 'text', 'ROUND(%s,0)&" "&%s' % (TOTKG7, vd('kg to order by the date shown')))],
    GR('What if', ('Menu week 1', {'cycle': 1}), ('Menu week 3', {'cycle': 3}), ('Menu week 4', {'cycle': 4}), ('Only 30 children', {'children': 30}), ('A 3-day lead time', {'lead': 3}))))

# 8 food cost per child-day
WK8 = '">"&({today}-7*{in:weeks})'
SP8 = 'SUMIFS(%s,%s,%s)' % (R('food', 'amount'), R('food', 'date'), WK8); CD8 = 'SUMIFS(%s,%s,%s)' % (R('menu_week', 'child_days'), R('menu_week', 'week'), WK8)
SP12 = 'SUMIFS(%s,%s,">"&({today}-364))' % (R('food', 'amount'), R('food', 'date')); CD12 = 'SUMIFS(%s,%s,">"&({today}-364))' % (R('menu_week', 'child_days'), R('menu_week', 'week'))
MC8 = 'SUMIFS(%s,%s,%s)' % (R('menu_week', 'meals_cost'), R('menu_week', 'week'), WK8)
tools.append(TOOL('food_cost_day', 'Food Cost per Child-Day', 'Food spend over child-days against your own last 12 months',
    'Pick the weeks to look back: food purchases are divided by the child-days present and set against your own last 12 months; the gap to the cost of the meals served shows what is bought but not served.', [
    I('weeks', 'Weeks to look back', 4), I('band', 'Share around your usual that counts as near', 0.05, 'pct')], [
    O('Food spent in the weeks', 'money', SP8), O('Child-days present in the weeks', 'int', CD8), O('Cost per child-day', 'money', 'IFERROR(%s/%s,0)' % (SP8, CD8)),
    O('Your usual cost per child-day, last 12 months', 'money', 'IFERROR(%s/%s,0)' % (SP12, CD12)), O('Against your usual', 'pct', 'IFERROR((%s/%s)/(%s/%s)-1,0)' % (SP8, CD8, SP12, CD12)),
    O('Spend above your usual in the weeks', 'money', '%s-%s*IFERROR(%s/%s,0)' % (SP8, CD8, SP12, CD12)), O('That gap over a year', 'money', '(%s-%s*IFERROR(%s/%s,0))*52/{in:weeks}' % (SP8, CD8, SP12, CD12)),
    O('Cost of the meals served per child-day', 'money', 'IFERROR(%s/%s,0)' % (MC8, CD8)), O('Bought but not served, per child-day', 'money', 'IFERROR((%s-%s)/%s,0)' % (SP8, MC8, CD8)),
    O('Verdict', 'text', 'IF(IFERROR((%s/%s)/(%s/%s)-1,0)>{in:band},%s,IF(IFERROR((%s/%s)/(%s/%s)-1,0)<-{in:band},%s,%s))' % (SP8, CD8, SP12, CD12, v2('Above your usual'), SP8, CD8, SP12, CD12, v2('Below your usual'), v2('Near your usual')))],
    GR('What if', ('Last 8 weeks', {'weeks': 8}), ('Last 12 weeks', {'weeks': 12}), ('Last 26 weeks', {'weeks': 26}), ('Last 2 weeks', {'weeks': 2}), ('Near means 10 percent', {'band': 0.1}))))

# 9 meal count check
tools.append(TOOL('meal_count', 'Meal Count Check', 'Meals served against children present',
    'Pick a day and the months to look back: see meals served and children present, any over-count that day and the days that failed. Served must not exceed present.', [
    I('date', 'Day to check', D.LAST_MEAL, 'date'), I('months', 'Months to look back', 12)], [
    O('Breakfasts served that day', 'int', SF('meals', 'served', ('date', '{in:date}'), ('meal', MB))), O('Lunches served that day', 'int', SF('meals', 'served', ('date', '{in:date}'), ('meal', ML_))),
    O('Snacks served that day', 'int', SF('meals', 'served', ('date', '{in:date}'), ('meal', MS_))), O('Children present at the three meals, added up', 'int', SF('meals', 'children_present', ('date', '{in:date}'))),
    O('Meals served that day', 'int', SF('meals', 'served', ('date', '{in:date}'))), O('Meal rows over the present count that day', 'int', CF('meals', ('date', '{in:date}'), ('over_by', '">0"'))),
    O('Meals served over the present count that day', 'int', SF('meals', 'over_by', ('date', '{in:date}'))), O('Meal rows at the limit that day', 'int', CF('meals', ('date', '{in:date}'), ('check_flag', fl('At the limit')))),
    O('Days failing the check in the months', 'int', 'SUMIFS(%s,%s,">"&EDATE(%s,-{in:months}))' % (R('claim', 'days_failing'), R('claim', 'month'), MS)),
    O('Last day with an over-count', 'date', 'IF(INDEX(%s,1)>0,INDEX(%s,1),"")' % (R('exceptions', 'margin'), R('exceptions', 'date'))),
    O('Verdict', 'text', 'IF(SUMIFS(%s,%s,">"&EDATE(%s,-{in:months}))=0,%s,SUMIFS(%s,%s,">"&EDATE(%s,-{in:months}))&" "&%s)' % (R('claim', 'days_failing'), R('claim', 'month'), MS, v2('Counts are consistent'), R('claim', 'days_failing'), R('claim', 'month'), MS, v2('day(s) over')))],
    GR('What if', ('The day of the last over-count', {'date': '=DATE(%s,%s,%s)' % FAIL}), ('Look back 6 months', {'months': 6}), ('Look back 24 months', {'months': 24}), ('Look back 3 months', {'months': 3}), ('Look back 18 months', {'months': 18}))))

# 10 menu rotation cost ranker
RK = lambda n: 'MATCH({in:meal}&"|%s",%s,0)' % (n, R('menu', 'rank_key2'))
def DSH(n, col): return 'IFERROR(INDEX(%s,%s),0)' % (R('menu', col), RK(n))
AVG10 = 'AVERAGEIFS(%s,%s,{in:meal})' % (R('menu', 'cost_child'), R('menu', 'meal')); LAST10 = 'COUNTIFS(%s,{in:meal})' % R('menu', 'meal')
LASTK10 = 'IFERROR(INDEX(%s,MATCH({in:meal}&"|"&%s,%s,0)),0)'
tools.append(TOOL('menu_ranker', 'Menu Rotation Cost Ranker', 'Dishes ranked by cost per child',
    'Pick a meal: its dishes are ranked by cost per child; see the three dearest, the cheapest, the saving a year if the dearest is swapped and whether a swap pays.', [
    IL('meal', 'Meal', 'meal', 'Lunch'), I('margin', 'Share above the meal average that counts as dear', 0.15, 'pct'), I('children', 'Children eating the meal', 36), I('days', 'Days a year the meal is served', 250)], [
    O('Dearest dish', 'text', DSH(1, 'dish')), O('Its cost per child', 'money', DSH(1, 'cost_child')), O('Second dearest dish', 'text', DSH(2, 'dish')), O('Its cost per child', 'money', DSH(2, 'cost_child')),
    O('Third dearest dish', 'text', DSH(3, 'dish')), O('Its cost per child', 'money', DSH(3, 'cost_child')), O('Average cost of the meal', 'money', AVG10),
    O('Cheapest dish', 'text', 'IFERROR(INDEX(%s,MATCH({in:meal}&"|"&%s,%s,0)),0)' % (R('menu', 'dish'), LAST10, R('menu', 'rank_key2'))),
    O('Its cost per child', 'money', 'IFERROR(INDEX(%s,MATCH({in:meal}&"|"&%s,%s,0)),0)' % (R('menu', 'cost_child'), LAST10, R('menu', 'rank_key2'))),
    O('Dearest dish above the average', 'pct', 'IFERROR(%s/%s-1,0)' % (DSH(1, 'cost_child'), AVG10)),
    O('Saving per child if the dearest is swapped for the cheapest', 'money', '%s-IFERROR(INDEX(%s,MATCH({in:meal}&"|"&%s,%s,0)),0)' % (DSH(1, 'cost_child'), R('menu', 'cost_child'), LAST10, R('menu', 'rank_key2'))),
    O('Saving a year', 'money', '(%s-IFERROR(INDEX(%s,MATCH({in:meal}&"|"&%s,%s,0)),0))*{in:children}*{in:days}/4/5' % (DSH(1, 'cost_child'), R('menu', 'cost_child'), LAST10, R('menu', 'rank_key2'))),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s-1,0)>{in:margin},%s,%s)' % (DSH(1, 'cost_child'), AVG10, vd('Swap this dish'), vd('Menu cost is fine')))],
    GR('What if', ('Breakfast', {'meal': MT('Breakfast')}), ('Afternoon snack', {'meal': MT('Afternoon snack')}), ('Dear means 5 percent above', {'margin': 0.05}), ('Dear means 40 percent above', {'margin': 0.4}), ('44 children', {'children': 44}))))

# 11 missing records chaser
FP = lambda c: 'IFERROR(INDEX(%s,{in:place}),0)' % R('follow', c)
OPEN11 = '(%s+%s)' % (CF('health', ('status', DUE)), CF('health', ('status', MISS)))
tools.append(TOOL('missing_chaser', 'Missing Records Chaser', 'Which family to chase first for a record',
    'Type the place in the chase list (1 is the record longest past its due date): see the child, the record, the days past due, the phone and the next step. Status and dates only.', [
    I('place', 'Place in the chase list', 1)], [
    O('Child', 'text', FP('child')), O('Family', 'text', FP('family')), O('Room', 'text', FP('room')), O('Record', 'text', FP('record')), O('Status', 'text', FP('status')), O('Due date', 'date', FP('due_date')),
    O('Days past due', 'int', FP('days_overdue')), O('Family phone', 'text', FP('phone')), O('Records due or missing in total', 'int', OPEN11),
    O('Records to escalate to the owner-director', 'int', CF('health', ('days_past', '">="&{set:escalate_days}'))), O('Records to call about', 'int', '%s-%s' % (CF('health', ('days_past', '">="&{set:call_days}')), CF('health', ('days_past', '">="&{set:escalate_days}')))),
    O('Records to remind', 'int', '%s-%s' % (OPEN11, CF('health', ('days_past', '">="&{set:call_days}')))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (OPEN11, v2('No records to chase'), FP('action')))],
    GR('What if', ('Second on the list', {'place': 2}), ('Fifth on the list', {'place': 5}), ('Tenth on the list', {'place': 10}), ('Fifteenth on the list', {'place': 15}), ('Last on the list', {'place': D.follow_n()}))))

# 12 incident follow-up chaser
INC = lambda c: 'IFERROR(INDEX(%s,MATCH(LARGE(%s,{in:place}),%s,0)),0)' % (R('incidents', c), R('incidents', 'open_key'), R('incidents', 'open_key'))
tools.append(TOOL('followup_chaser', 'Incident Follow-up Chaser', 'Which incident follow-up to close first',
    'Type the place in the list (1 is the oldest open item): incidents with the family not told or the follow-up open are ranked by age, with date, room, type and phone.', [
    I('place', 'Place in the list', 1)], [
    O('Incident', 'text', INC('incident_id')), O('Date', 'date', INC('date')), O('Room', 'text', INC('room')), O('Type', 'text', INC('type')), O('Family told', 'text', INC('parent_informed')),
    O('Follow-up done', 'text', INC('follow_up_done')), O('Days since the incident', 'int', 'IFERROR(INT(LARGE(%s,{in:place})),0)-1' % R('incidents', 'open_key')), O('Family phone', 'text', INC('phone')),
    O('Follow-ups not done', 'int', CF('incidents', ('follow_up_done', OPEN))), O('Families not told', 'int', CF('incidents', ('parent_informed', NO))),
    O('Open for longer than your allowed days', 'int', CF('incidents', ('open_days', '">"&{set:followup_days}'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (CF('incidents', ('follow_up_done', OPEN)), vd('Nothing open'), CF('incidents', ('follow_up_done', OPEN)), vd('follow-ups to close today')))],
    GR('What if', ('Second on the list', {'place': 2}), ('Third on the list', {'place': 3}), ('Fourth on the list', {'place': 4}), ('Fifth on the list', {'place': 5}), ('Sixth on the list', {'place': 6}))))

# 13 drill gap finder
GAP = {k: '({today}-%s)' % LASTK('{list:drill.%s}' % key('drill', k)) for k in DRILL_KINDS}
FREQD = {'Fire drill': 'drill_fire', 'Evacuation drill': 'drill_evac', 'Lockdown drill': 'drill_lockdown', 'Shelter drill': 'drill_shelter'}
LATE13 = {k: '(%s>{set:%s}*30+{in:grace})' % (GAP[k], FREQD[k]) for k in DRILL_KINDS}
MXG = 'MAX(%s)' % ','.join(GAP[k] for k in DRILL_KINDS)
WORST = '0'
for k in reversed(DRILL_KINDS): WORST = 'IF(%s=%s,%s,%s)' % (GAP[k], MXG, tok('drill', k), WORST)
tools.append(TOOL('drill_gap', 'Drill Gap Finder', 'Days since the last drill of each kind',
    'The days since each kind of drill are set against the months between drills in your settings, plus a grace of days you choose; the kind with the longest gap is named so you schedule it this month.', [
    I('grace', 'Grace days after the plan', 7)], [
    O('Days since the last fire drill', 'int', GAP['Fire drill']), O('Days since the last evacuation drill', 'int', GAP['Evacuation drill']), O('Days since the last lockdown drill', 'int', GAP['Lockdown drill']),
    O('Days since the last shelter drill', 'int', GAP['Shelter drill']), O('Longest gap in days', 'int', MXG), O('Kind with the longest gap', 'text', WORST),
    O('Kinds past their plan plus the grace', 'int', '+'.join(LATE13[k] for k in DRILL_KINDS)), O('Days since the latest drill of any kind', 'int', '{today}-MAX(%s)' % R('drills', 'date')),
    O('Drills in the last 12 months', 'int', CF('drills', ('date', '">"&EDATE({today},-12)'))), O('Minutes of drills in the last 12 months', 'int', SF('drills', 'minutes', ('date', '">"&EDATE({today},-12)'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % ('+'.join(LATE13[k] for k in DRILL_KINDS), vd('Drill is current'), vd('Schedule this drill this month')))],
    GR('What if', ('No grace', {'grace': 0}), ('A 14-day grace', {'grace': 14}), ('A 30-day grace', {'grace': 30}), ('A 3-day grace', {'grace': 3}), ('A 60-day grace', {'grace': 60}))))

# 14 missed checks ranker
MW = lambda r: 'SUMIFS(%s,%s,%s,%s,">"&({today}-7*{in:weeks}))' % (R('check_week', 'missed'), R('check_week', 'room'), tok('room', r), R('check_week', 'week'))
MXM = 'MAX(%s)' % ','.join(MW(r) for r in ROOMS)
WORSTR = '0'
for r in reversed(ROOMS): WORSTR = 'IF(%s=%s,%s,%s)' % (MW(r), MXM, tok('room', r), WORSTR)
tools.append(TOOL('missed_ranker', 'Missed Checks Ranker', 'Rooms ranked by missed checks over the weeks you choose',
    'Type the weeks to look back (up to 13): the missed checks of each room are counted and the room with the most is named, so the owner-director knows which team to talk to.', [
    I('weeks', 'Weeks to look back, up to 13', 13)], [
    O('Missed in Infants', 'int', MW('Infants')), O('Missed in Toddlers', 'int', MW('Toddlers')), O('Missed in Twos', 'int', MW('Twos')), O('Missed in Preschool', 'int', MW('Preschool')), O('Missed in School-age', 'int', MW('School-age')),
    O('Most missed in one room', 'int', MXM), O('Room with the most missed', 'text', WORSTR), O('Rooms with at least one missed check', 'int', '+'.join('(%s>0)' % MW(r) for r in ROOMS)),
    O('Missed in all rooms', 'int', 'SUMIFS(%s,%s,">"&({today}-7*{in:weeks}))' % (R('check_week', 'missed'), R('check_week', 'week'))),
    O('Completion share, all rooms', 'pct', 'IFERROR(SUMIFS(%s,%s,">"&({today}-7*{in:weeks}))/SUMIFS(%s,%s,">"&({today}-7*{in:weeks})),0)' % (R('check_week', 'done'), R('check_week', 'week'), R('check_week', 'total'), R('check_week', 'week'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (MXM, vd('No room is missing checks'), vd('Talk to this team')))],
    GR('What if', ('Last 4 weeks', {'weeks': 4}), ('Last 8 weeks', {'weeks': 8}), ('Last 6 weeks', {'weeks': 6}), ('Last 10 weeks', {'weeks': 10}), ('Last 2 weeks', {'weeks': 2}))))

# 15 meal over-order check
MW15 = lambda c: SF('menu_week', c, ('week', '{in:week}'))
tools.append(TOOL('over_order', 'Meal Over-Order Check', 'Ordered meals against meals served in a week',
    'Type the week and the meals you ordered: the meals served that week give the over-order, its cost, the share against the tolerance you accept and an order for next week from your own recent average.', [
    I('week', 'Week (Monday)', D.LAST_WEEK, 'date'), I('ordered', 'Meals ordered for the week', 360), I('tol', 'Over-order you accept', 0.05, 'pct')], [
    O('Meals served that week', 'int', MW15('meals_served')), O('Open days that week', 'int', MW15('open_days')), O('Over-order, meals', 'int', '{in:ordered}-%s' % MW15('meals_served')),
    O('Over-order share of the meals served', 'pct', 'IFERROR({in:ordered}/%s-1,0)' % MW15('meals_served')), O('Cost per meal served that week', 'money', 'IFERROR(%s/%s,0)' % (MW15('meals_cost'), MW15('meals_served'))),
    O('Cost of the over-order', 'money', '({in:ordered}-%s)*IFERROR(%s/%s,0)' % (MW15('meals_served'), MW15('meals_cost'), MW15('meals_served'))),
    O('Average meals served, the 4 weeks to that week', 'num', 'IFERROR(AVERAGEIFS(%s,%s,">="&({in:week}-21),%s,"<="&{in:week}),0)' % (R('menu_week', 'meals_served'), R('menu_week', 'week'), R('menu_week', 'week'))),
    O('Order for next week at your tolerance', 'int', 'ROUNDUP(IFERROR(AVERAGEIFS(%s,%s,">="&({in:week}-21),%s,"<="&{in:week}),0)*(1+{in:tol}),0)' % (R('menu_week', 'meals_served'), R('menu_week', 'week'), R('menu_week', 'week'))),
    O('Saving a year if next week\'s order is followed', 'money', '({in:ordered}-ROUNDUP(IFERROR(AVERAGEIFS(%s,%s,">="&({in:week}-21),%s,"<="&{in:week}),0)*(1+{in:tol}),0))*IFERROR(%s/%s,0)*52' % (R('menu_week', 'meals_served'), R('menu_week', 'week'), R('menu_week', 'week'), MW15('meals_cost'), MW15('meals_served'))),
    O('Verdict', 'text', 'IF(IFERROR({in:ordered}/%s-1,0)>{in:tol},%s,%s)' % (MW15('meals_served'), vd('Order less'), vd('Order is right')))],
    GR('What if', ('Ordered 340 meals', {'ordered': 340}), ('Ordered 330 meals', {'ordered': 330}), ('Ordered 400 meals', {'ordered': 400}), ('Accept 10 percent', {'tol': 0.1}), ('Two weeks earlier', {'week': '=%s-14' % ("DATE(%s,%s,%s)" % tuple(int(x) for x in D.LAST_WEEK.split('-')))}))))

# 16 incident rate per 1,000 child-days
WIN16 = '">="&EDATE(%s,-({in:months}-1))' % MS
INC16 = SF('inc_month', 'incidents', ('room', '{in:room}'), ('month', WIN16)); CD16 = SF('inc_month', 'child_days', ('room', '{in:room}'), ('month', WIN16))
USU16 = 'IFERROR(SUMIFS(%s,%s,{in:room})/SUMIFS(%s,%s,{in:room})*1000,0)' % (R('inc_month', 'incidents'), R('inc_month', 'room'), R('inc_month', 'child_days'), R('inc_month', 'room'))
RATE16 = 'IFERROR(%s/%s*1000,0)' % (INC16, CD16)
tools.append(TOOL('incident_rate', 'Incident Rate per 1,000 Days', 'Incident rate of a room against your usual',
    'Pick a room and the months to look back: incidents are divided by child-days present and set against the room\'s own 12-month rate and the center rate, so a busy room is not confused with a risky one.', [
    IL('room', 'Room', 'room', 'Preschool'), I('months', 'Months to look back', 3), I('band', 'Share around your usual that counts as near', 0.25, 'pct')], [
    O('Incidents in the months', 'int', INC16), O('Child-days present in the months', 'int', CD16), O('Rate per 1,000 child-days', 'num', RATE16), O('Your usual rate for the room, 12 months', 'num', USU16),
    O('Against your usual', 'pct', 'IFERROR(%s/%s-1,0)' % (RATE16, USU16)), O('Center rate, all rooms, in the months', 'num', 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s)*1000,0)' % (R('inc_month', 'incidents'), R('inc_month', 'month'), WIN16, R('inc_month', 'child_days'), R('inc_month', 'month'), WIN16)),
    O('Incidents a month in the room', 'num', 'IFERROR(%s/{in:months},0)' % INC16), O('Incidents the room would have at your usual rate', 'num', 'IFERROR(%s*%s/1000,0)' % (USU16, CD16)),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:band}),%s,IF(%s<%s*(1-{in:band}),%s,%s))' % (RATE16, USU16, v2('Above your usual'), RATE16, USU16, v2('Below your usual'), v2('Near your usual')))],
    GR('What if', ('Infants', {'room': RT('Infants')}), ('Toddlers', {'room': RT('Toddlers')}), ('Twos, 6 months', {'room': RT('Twos'), 'months': 6}), ('School-age, 6 months', {'room': RT('School-age'), 'months': 6}), ('Preschool, 1 month', {'months': 1}))))

# 17 supplier price rise test
WK17 = '">"&({today}-84)'
WSP17 = 'SUMIFS(%s,%s,%s)/12' % (R('food', 'amount'), R('food', 'date'), WK17)
EXTRA17 = '%s*{in:share}*{in:rise}' % WSP17
PERW = '(%s/COUNTIFS(%s,%s))' % (EXTRA17, R('children', 'status'), ENR)
tools.append(TOOL('price_rise', 'Supplier Price Rise Test', 'A food price rise: absorb or raise the fee',
    'Type the price rise and the share of your food bill it touches: see the extra cost a week and a year, the fee rise per child that covers it and a verdict.', [
    I('rise', 'Supplier price rise', 0.12, 'pct'), I('share', 'Share of the food bill it touches', 0.8, 'pct'), I('tuition', 'Average weekly tuition per child', 340, 'money'),
    I('absorb', 'Fee rise per child you will absorb, share of tuition', 0.003, 'pct'), I('limit', 'Fee rise per child that needs a fee change, share of tuition', 0.01, 'pct')], [
    O('Food bought a week, last 12 weeks', 'money', WSP17), O('Extra cost a week', 'money', EXTRA17), O('Extra cost a month', 'money', '%s*52/12' % EXTRA17), O('Extra cost a year', 'money', '%s*52' % EXTRA17),
    O('Extra cost per child-day', 'money', 'IFERROR(%s/(SUMIFS(%s,%s,%s)/12),0)' % (EXTRA17, R('menu_week', 'child_days'), R('menu_week', 'week'), WK17)), O('Children enrolled', 'int', 'COUNTIFS(%s,%s)' % (R('children', 'status'), ENR)),
    O('Fee rise per child a week to cover it', 'money', PERW), O('That rise as a share of tuition', 'pct', 'IFERROR(%s/{in:tuition},0)' % PERW),
    O('Price rise that would need a fee change', 'pct', 'IFERROR({in:limit}*{in:tuition}*COUNTIFS(%s,%s)/(%s*{in:share}),0)' % (R('children', 'status'), ENR, WSP17)),
    O('Verdict', 'text', 'IF(IFERROR(%s/{in:tuition},0)<={in:absorb},%s,IF(IFERROR(%s/{in:tuition},0)<={in:limit},%s,%s))' % (PERW, vd('Absorb the rise'), PERW, vd('Renegotiate'), vd('Raise the fee')))],
    GR('What if', ('A 5 percent rise', {'rise': 0.05}), ('A 25 percent rise', {'rise': 0.25}), ('A 60 percent rise', {'rise': 0.6}), ('The whole bill is touched', {'share': 1}), ('Absorb only 0.1 percent', {'absorb': 0.001}))))

# 18 special diet counts for the cook
FNEED = lambda n: 'IFERROR(INDEX(%s,MATCH({in:room}&"|%s",%s,0)),"-")' % (R('cook', 'child'), n, R('cook', 'need_key'))
NEED18 = 'COUNTIFS(%s,{in:room},%s,1)' % (R('cook', 'room'), R('cook', 'needs_update'))
tools.append(TOOL('diet_counts', 'Special Diet Counts', 'Allergy-status counts per room for the cook',
    'Pick a room: see how many children have the allergy status on file, due or missing and who needs an update before the next meal. Counts and names of status only, no health detail.', [
    IL('room', 'Room', 'room', 'Preschool')], [
    O('Children in the room', 'int', CF('cook', ('room', '{in:room}'))), O('Allergy status on file', 'int', CF('cook', ('room', '{in:room}'), ('allergy', ONF))), O('Allergy status due', 'int', CF('cook', ('room', '{in:room}'), ('allergy', DUE))),
    O('Allergy status missing', 'int', CF('cook', ('room', '{in:room}'), ('allergy', MISS))), O('Medical permission on file', 'int', CF('cook', ('room', '{in:room}'), ('permission', ONF))),
    O('Children needing an update', 'int', NEED18), O('First child to update', 'text', FNEED(1)), O('Second child to update', 'text', FNEED(2)), O('Third child to update', 'text', FNEED(3)),
    O('Children needing an update, all rooms', 'int', 'SUM(%s)' % R('cook', 'needs_update')), O('Share of the room that is current', 'pct', 'IFERROR(1-%s/%s,0)' % (NEED18, CF('cook', ('room', '{in:room}')))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (NEED18, v2('Diet list is current'), v2('Needs an update')))],
    GR('What if', ('Infants', {'room': RT('Infants')}), ('Toddlers', {'room': RT('Toddlers')}), ('Twos', {'room': RT('Twos')}), ('School-age', {'room': RT('School-age')}), ('Preschool', {'room': RT('Preschool')}))))
assert len(tools) == 18, len(tools)
