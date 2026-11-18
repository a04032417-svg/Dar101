"""Home Management suite part 4: the 18 decision tools (a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho4_lists import *
import ho4_data as DD
from ho4_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dflt): return IN(k, label, 'list', key(lst, dflt), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def V(*parts):
    """a verdict: words (list labels) and numbers or names joined with spaces; a tuple ('f', formula) is a value"""
    out = []
    for p in parts:
        if isinstance(p, tuple): out.append('(' + p[1] + ')')
        else: out.append(lbl(p))
    return '&" "&'.join(out)
def F(x): return ('f', x)
def MNAMES(expr): return 'CHOOSE(%s,%s)' % (expr, ','.join(tok('mname', m) for m in MONTH_NAMES))
def DT(x): return '%s&" "&DAY(%s)' % (MNAMES('MONTH(%s)' % x), x)
def PCT(x): return 'ROUND((%s)*100,0)&"%%"' % x


tools = []
NOW = '{today}'
TASKS_ALL = 'COUNTIFS(%s,"<>")' % MT('task_id')
OVN = 'COUNTIFS(%s,%s)' % (MT('status'), OVD)


def WIN(col, days, extra=''):
    return '%s,">="&{today},%s,"<="&({today}+%s-1)%s' % (MT(col), MT(col), days, extra)


# 1 most overdue task ---------------------------------------------------------------------
def O1(col): return 'IFERROR(INDEX(%s,MATCH({in:rank},%s,0))&"","")' % (R('overdue', col), R('overdue', 'rank'))
def O1N(col): return 'IFERROR(INDEX(%s,MATCH({in:rank},%s,0)),"")' % (R('overdue', col), R('overdue', 'rank'))
tools.append(TOOL('overdue_tool', 'Most Overdue Task', 'Which task do we do first',
    'Tasks ranked by days overdue from the Most overdue first sheet: type a position to look at the first, second or third task; the verdict names the task to do first.', [
    I('rank', 'Position in the list, 1 is the most overdue', 1)], [
    O('Task', 'text', O1('task')), O('Area', 'text', O1('area')), O('Days overdue', 'int', O1N('overdue_days')), O('Assigned to', 'text', O1('assigned')),
    O('Typical cost line', 'money', O1N('typical_cost')), O('Minutes it takes', 'int', O1N('minutes')),
    O('Tasks overdue now', 'int', OVN), O('Overdue minutes, all tasks', 'int', 'SUMIFS(%s,%s,%s)' % (MT('minutes'), MT('status'), OVD)),
    O('Overdue typical cost lines, all tasks', 'money', 'SUMIFS(%s,%s,%s)' % (MT('typical_cost'), MT('status'), OVD)),
    O('Average days overdue', 'int', 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (MT('overdue_days'), MT('status'), OVD)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s="",%s,%s))' % (OVN, lbl('Nothing is overdue'), O1('task'), lbl('No task at that position'), V('Do', F(O1('task')), 'first,', F(O1N('overdue_days')), 'days overdue')))],
    GR('What if', ('First task', {'rank': 1}), ('Second task', {'rank': 2}), ('Third task', {'rank': 3}))))

# 2 next due date of every task ----------------------------------------------------------
NXP = '(COUNTIFS(%s,"<0")+1)' % R('schedule', 'days_to_due')
tools.append(TOOL('nextdue_tool', 'Next Due Date Of Every Task', 'What falls due in the days ahead',
    'A forecast from the last done date and the interval of every task: type how many days to look ahead and read the count, the cost lines, the minutes and the next task.', [
    I('days', 'Days ahead to look, 1 to 365', 30)], [
    O('Tasks due in the window', 'int', 'COUNTIFS(%s)' % WIN('next_due', '{in:days}')), O('Tasks overdue now', 'int', OVN),
    O('Tasks due in the next 7 days', 'int', 'COUNTIFS(%s)' % WIN('next_due', '7')),
    O('Next task due', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (R('schedule', 'task'), NXP)), O('Its date', 'date', 'IFERROR(INDEX(%s,%s),"")' % (R('schedule', 'next_due'), NXP)),
    O('Days to it', 'int', 'IFERROR(INDEX(%s,%s),"")' % (R('schedule', 'days_to_due'), NXP)),
    O('Typical cost lines in the window', 'money', 'SUMIFS(%s,%s)' % (MT('typical_cost'), WIN('next_due', '{in:days}'))),
    O('Minutes of those tasks', 'int', 'SUMIFS(%s,%s)' % (MT('minutes'), WIN('next_due', '{in:days}'))),
    O('Tasks that need a trade', 'int', 'COUNTIFS(%s,%s,1)' % (WIN('next_due', '{in:days}'), MT('trade_task'))),
    O('Verdict', 'text', V(F('COUNTIFS(%s)' % WIN('next_due', '{in:days}')), 'tasks due in the next', F('{in:days}'), 'days'))],
    GR('What if', ('Next 7 days', {'days': 7}), ('Next 14 days', {'days': 14}), ('Next 60 days', {'days': 60}), ('Next 90 days', {'days': 90}), ('Next 180 days', {'days': 180}))))

# 3 busiest month ahead -------------------------------------------------------------------
MLR = lambda c: R('month_load', c)
TD3 = MLR('tasks_due')
MX3 = 'IF(COUNT(%s)=0,"",MAX(%s))' % (TD3, TD3)
PS3 = 'MATCH(MAX(%s),%s,0)' % (TD3, TD3)
BN3 = MNAMES('MONTH(INDEX(%s,%s))' % (MLR('month'), PS3))
CH3 = 'IFERROR(INDEX(%s,{in:month}),"")' % TD3
tools.append(TOOL('busiest_tool', 'Busiest Month Ahead', 'Which month is the busiest for maintenance',
    'The repeat dates of every task are counted for 12 months on the Next 12 months sheet: read the busiest month, then type a month to see how it compares with the busiest and the average.', [
    I('month', 'Month to look at, 1 is this month, 12 is eleven months ahead', 1)], [
    O('Busiest month', 'text', 'IFERROR(%s,"")' % BN3), O('Tasks in the busiest month', 'int', MX3),
    O('Typical cost lines in it', 'money', 'IFERROR(INDEX(%s,%s),"")' % (MLR('cost_lines'), PS3)),
    O('Tasks in the quietest month', 'int', 'IF(COUNT(%s)=0,"",MIN(%s))' % (TD3, TD3)), O('Average tasks a month', 'num', 'IFERROR(ROUND(AVERAGE(%s),1),"")' % TD3),
    O('Tasks in the month you typed', 'int', CH3), O('Typical cost lines in that month', 'money', 'IFERROR(INDEX(%s,{in:month}),"")' % MLR('cost_lines')),
    O('That month against the average', 'pct', 'IFERROR(%s/AVERAGE(%s),"")' % (CH3, TD3)), O('Months busier than that month', 'int', 'IFERROR(COUNTIFS(%s,">"&%s),"")' % (TD3, CH3)),
    O('Verdict', 'text', 'IF(%s="","",%s)' % (MX3, V('Busiest month', F(BN3 + '&","'), F(MX3), 'tasks')))],
    GR('What if', ('Next month', {'month': 2}), ('In 3 months', {'month': 4}), ('In 6 months', {'month': 7}), ('In 9 months', {'month': 10}), ('In 12 months', {'month': 12}))))

# 4 consumables reorder -------------------------------------------------------------------
FN4 = 'IFERROR(SMALL(%s,1),"")' % RO('need_change')
tools.append(TOOL('reorder_tool', 'Consumables Reorder Tool', 'What do we order before the next change',
    'From the change dates and the units in stock of the Filters and consumables sheet: type the days to order before a change and read which item to order first.', [
    I('lead', 'Order this many days before the change', 10), I('window', 'Look this many days ahead', 90)], [
    O('Items out of stock', 'int', 'COUNTIFS(%s,"<1",%s,"<>")' % (RO('units'), RO('item'))), O('First item to order', 'text', 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0)))' % (FN4, RO('item'), FN4, RO('need_change'))),
    O('Its change date', 'date', FN4), O('Order before', 'date', 'IF(%s="","",%s-{in:lead})' % (FN4, FN4)), O('Days to the order-by date', 'int', 'IF(%s="","",%s-{in:lead}-{today})' % (FN4, FN4)),
    O('Out-of-stock items to order in the window', 'int', 'COUNTIFS(%s,"<="&({today}+{in:window}+{in:lead}))' % RO('need_change')),
    O('Changes due in the window, all items', 'int', 'COUNTIFS(%s,"<="&({today}+{in:window}))' % RO('next_change')), O('Changes overdue now', 'int', 'COUNTIFS(%s,%s)' % (RO('change_status'), OVD)),
    O('Items in stock', 'int', 'COUNTIFS(%s,">=1")' % RO('units')),
    O('Verdict', 'text', 'IF(%s="",%s,%s)' % (FN4, lbl('Stock covers the next changes'), V('Reorder', F('INDEX(%s,MATCH(%s,%s,0))' % (RO('item'), FN4, RO('need_change'))), 'by', F(DT('(%s-{in:lead})' % FN4)))))],
    GR('What if', ('Order 5 days ahead', {'lead': 5}), ('Order 14 days ahead', {'lead': 14}), ('Order 21 days ahead', {'lead': 21}), ('Order 30 days ahead', {'lead': 30}), ('Look 30 days ahead', {'window': 30}))))

# 5 safety checks due ---------------------------------------------------------------------
SN5 = 'IFERROR(SMALL(%s,COUNTIFS(%s,"<"&{today})+1),"")' % (MT('safety_next'), MT('safety_next'))
SW = '%s,%s,%s' % (WIN('next_due', '{in:window}'), MT('safety'), YES)
SOVD = 'COUNTIFS(%s,%s,%s,%s)' % (MT('safety'), YES, MT('status'), OVD)
SNAME = 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0)))' % (SN5, MT('task'), SN5, MT('safety_next'))
tools.append(TOOL('safety_tool', 'Safety Checks Due', 'Which safety checks are due, typical intervals',
    'Alarm tests, alarm batteries, the escape plan and the shut-off valve check from their typed intervals; intervals are typical, check the manufacturer\'s instructions and your local rules.', [
    I('window', 'Days ahead to look', 30)], [
    O('Safety checks in the plan', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (MT('safety'), YES, MT('task_id'))), O('Safety checks overdue', 'int', SOVD), O('Safety checks due in the window', 'int', 'COUNTIFS(%s)' % SW),
    O('Next safety check', 'text', SNAME), O('Its date', 'date', SN5), O('Days to it', 'int', 'IF(%s="","",%s-{today})' % (SN5, SN5)),
    O('Minutes of the checks in the window', 'int', 'SUMIFS(%s,%s)' % (MT('minutes'), SW)),
    O('Shortest interval in the plan, days', 'int', 'IFERROR(SMALL(%s,1),"")' % MT('safety_int')), O('Typical alarm test interval, days, from Settings', 'int', '{set:alarm_test_days}'),
    O('Typical alarm battery interval, days, from Settings', 'int', '{set:alarm_battery_days}'),
    O('Verdict', 'text', 'IF(%s>0,%s,IF(%s="",%s,%s))' % (SOVD, V(F(SOVD), 'safety checks overdue'), SN5, lbl('No safety check ahead'), V(F(SNAME), 'due in', F('%s-{today}' % SN5), 'days')))],
    GR('What if', ('Look 14 days ahead', {'window': 14}), ('Look 60 days ahead', {'window': 60}), ('Look 90 days ahead', {'window': 90}), ('Look 180 days ahead', {'window': 180}), ('Look 365 days ahead', {'window': 365}))))

# 6 appliance service due -----------------------------------------------------------------
P6 = 'MATCH({in:rank},%s,0)' % AS('srank')
def A6(col): return 'IFERROR(INDEX(%s,%s)&"","")' % (AS(col), P6)
def A6N(col): return 'IFERROR(INDEX(%s,%s),"")' % (AS(col), P6)
tools.append(TOOL('appsvc_tool', 'Appliance Service Due', 'Which appliance or system is serviced next',
    'Appliances and systems ranked by their next service date: type a position to look at the first, second or third; the dates come from the service task of each appliance.', [
    I('rank', 'Position in the list, 1 is the soonest', 1)], [
    O('Item', 'text', A6('item')), O('Service task ID', 'text', A6('task_id')), O('Last service', 'date', A6N('last_service')), O('Next service', 'date', A6N('next_service')),
    O('Days to the service', 'int', A6N('days_to')), O('Done by', 'text', A6('who')), O('Services logged', 'int', A6N('services')),
    O('Services overdue now', 'int', 'COUNTIFS(%s,%s)' % (AS('status'), OVD)), O('Services due in the next 60 days', 'int', 'COUNTIFS(%s,">=0",%s,"<=59")' % (AS('days_to'), AS('days_to'))),
    O('Verdict', 'text', 'IF(%s="",%s,IF(%s<0,%s,%s))' % (A6('item'), lbl('No appliance at that position'), A6N('days_to'),
        V('Service', F(A6('item')), 'now, overdue', F('-' + A6N('days_to')), 'days'), V('Service', F(A6('item')), 'by', F(DT(A6N('next_service'))))))],
    GR('What if', ('Second appliance', {'rank': 2}), ('Third appliance', {'rank': 3}), ('Fourth appliance', {'rank': 4}), ('Fifth appliance', {'rank': 5}), ('Back to the first', {'rank': 1}))))

# 7 yearly cost of an item ----------------------------------------------------------------
def A7(col): return 'IFERROR(INDEX(%s,{in:row}),"")' % AS(col)
YC7 = A7('yearly_cost')
tools.append(TOOL('itemcost_tool', 'Yearly Cost Of An Item', 'What does an appliance cost us each year to keep going',
    'Service and repair cost lines of one appliance per year of age: type its row number in the Appliance service history; the projection repeats the same pace for the years you type.', [
    I('row', 'Row in the Appliance service history, 1 to 22', 6), I('years', 'Years to project', 5)], [
    O('Item', 'text', 'IFERROR(INDEX(%s,{in:row})&"","")' % AS('item')), O('Age in years', 'num', A7('age_years')), O('Service cost lines since purchase', 'money', A7('svc_cost')),
    O('Repair cost lines', 'money', A7('rep_cost')), O('Repairs logged', 'int', A7('repairs')), O('Services logged', 'int', A7('services')), O('Cost lines in all', 'money', A7('life_cost')),
    O('Cost lines per year of age', 'money', YC7), O('Projected over the years you typed', 'money', 'IFERROR(%s*{in:years},"")' % YC7),
    O('Share of the cost lines that are repairs', 'pct', 'IFERROR(%s/%s,0)' % (A7('rep_cost'), A7('life_cost'))),
    O('Verdict', 'text', 'IF(%s="","",%s)' % (YC7, V(F('ROUND(%s,0)' % YC7), 'a year in cost lines')))],
    GR('What if', ('Boiler or furnace', {'row': 1}), ('Fridge freezer', {'row': 3}), ('Washing machine', {'row': 5}), ('Oven', {'row': 8}), ('Lawn mower', {'row': 11}))))

# 8 quote comparison ----------------------------------------------------------------------
MN8 = 'MIN({in:qa},{in:qb},{in:qc})'
MXQ = 'MAX({in:qa},{in:qb},{in:qc})'
WHO8 = 'IF({in:qa}=%s,{in:name_a},IF({in:qb}=%s,{in:name_b},{in:name_c}))' % (MN8, MN8)
tools.append(TOOL('quote_tool', 'Quote Comparison', 'Which of the three quotes is the lowest',
    'Type up to three quotes for the same job and who gave them; the lowest, the highest and the spread are calculated. Compare what is included, not only the price.', [
    I('name_a', 'Who quoted, first quote', 'Plumber A', 'text'), I('qa', 'First quote', 240, 'money'), I('name_b', 'Who quoted, second quote', 'Plumber B', 'text'), I('qb', 'Second quote', 195, 'money'),
    I('name_c', 'Who quoted, third quote', 'Handyman', 'text'), I('qc', 'Third quote', 215, 'money')], [
    O('Lowest quote', 'money', MN8), O('Highest quote', 'money', MXQ), O('Middle quote', 'money', '{in:qa}+{in:qb}+{in:qc}-%s-%s' % (MN8, MXQ)), O('Average quote', 'money', 'ROUND(({in:qa}+{in:qb}+{in:qc})/3,0)'),
    O('Spread, highest minus lowest', 'money', '%s-%s' % (MXQ, MN8)), O('Lowest quoted by', 'text', WHO8), O('Lowest quote below the highest', 'pct', 'IFERROR(1-%s/%s,0)' % (MN8, MXQ)),
    O('Lowest quote below the average', 'pct', 'IFERROR(1-%s/(({in:qa}+{in:qb}+{in:qc})/3),0)' % MN8),
    O('Verdict', 'text', V('Lowest quote', F(WHO8 + '&","'), F(PCT('IFERROR(1-%s/%s,0)' % (MN8, MXQ))), 'below the highest'))],
    GR('What if', ('First quote at 200', {'qa': 200}), ('First quote at 180', {'qa': 180}), ('Second quote at 250', {'qb': 250}), ('Third quote at 150', {'qc': 150}), ('All three at 220', {'qa': 220, 'qb': 220, 'qc': 220}))))

# 9 repeat repair finder ------------------------------------------------------------------
RR = lambda c: R('repeat_repairs', c)
LN9 = 'IFERROR(LARGE(%s,{in:rank}),"")' % RR('repairs12')
RM9 = 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (RR('room'), LN9, RR('repairs12'))
LD9 = 'SUMPRODUCT(MAX((%s=%s)*(%s)))' % (RP('room'), RM9, RP('date'))
tools.append(TOOL('repeat_tool', 'Repeat Repair Finder', 'Which room keeps needing repairs',
    'Rooms ranked by the repairs in the repeat window set in Settings; type a position and the number of repairs that counts as a repeat to see the room, its latest issue and its cost lines.', [
    I('rank', 'Position in the list, 1 is the most repairs', 1), I('min', 'Repairs that count as a repeat', 2)], [
    O('Room', 'text', RM9), O('Repairs in the window', 'int', LN9), O('Window, days', 'int', '{set:repeat_days}'),
    O('Rooms with a repeat', 'int', 'COUNTIFS(%s,">="&{in:min})' % RR('repairs12')), O('Repairs in the window, all rooms', 'int', 'SUM(%s)' % RR('repairs12')),
    O('Latest issue in that room', 'text', 'IFERROR(INDEX(%s,MATCH(%s&"-"&%s,%s,0))&"","")' % (RP('issue'), RM9, LD9, RP('rkey'))),
    O('Its date', 'date', 'IFERROR(IF(%s=0,"",%s),"")' % (LD9, LD9)),
    O('Cost lines in that room, in the window', 'money', 'IFERROR(SUMIFS(%s,%s,%s,%s,">="&({today}-{set:repeat_days})),"")' % (RP('cost'), RP('room'), RM9, RP('date'))),
    O('Verdict', 'text', 'IF(%s="","",IF(%s>={in:min},%s,%s))' % (LN9, LN9, V('Repeat:', F(RM9 + '&","'), F(LN9), 'repairs in the last', F('{set:repeat_days}'), 'days'), lbl('No repeat repair in the window')))],
    GR('What if', ('Second room', {'rank': 2}), ('Third room', {'rank': 3}), ('A repeat is 3 repairs', {'min': 3}), ('A repeat is 4 repairs', {'min': 4}), ('Second room, 3 repairs', {'rank': 2, 'min': 3}))))

# 10 open repairs chase list --------------------------------------------------------------
P10 = 'MATCH({in:rank},%s,0)' % OR_('rank')
def C10(col): return 'IFERROR(INDEX(%s,%s)&"","")' % (OR_(col), P10)
def C10N(col): return 'IFERROR(INDEX(%s,%s),"")' % (OR_(col), P10)
OPN = 'COUNTIFS(%s,"<>",%s,1)' % (RP('repair_id'), RP('open'))
tools.append(TOOL('chase_tool', 'Open Repairs Chase List', 'Which open repair do we chase first',
    'Open and waiting repairs ranked by days open: type a position and the days after which you chase; the verdict names the repair to chase and how long it has been open.', [
    I('rank', 'Position in the list, 1 is the oldest', 1), I('chase', 'Chase after this many days open', 14)], [
    O('Repair', 'text', C10('issue')), O('Room', 'text', C10('room')), O('Trade', 'text', C10('trade')), O('Days open', 'int', C10N('days_open')), O('Status', 'text', C10('status')), O('Quote', 'money', C10N('quote')),
    O('Phone of the trade', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (RP('tphone'), C10('repair_id'), RP('repair_id'))),
    O('Open repairs', 'int', OPN), O('Waiting for a trade', 'int', 'COUNTIFS(%s,"<>",%s,%s)' % (RP('repair_id'), RP('status'), WAITING)),
    O('Open longer than the chase days', 'int', 'COUNTIFS(%s,1,%s,">"&{in:chase})' % (RP('open'), RP('days_open'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s="",%s,%s))' % (OPN, lbl('No open repair'), C10('issue'), lbl('No repair at that position'), V('Chase', F(C10('issue') + '&","'), 'open', F(C10N('days_open')), 'days')))],
    GR('What if', ('Second repair', {'rank': 2}), ('Third repair', {'rank': 3}), ('Chase after 7 days', {'chase': 7}), ('Chase after 28 days', {'chase': 28}), ('Chase after 35 days', {'chase': 35}))))

# 11 which trade to call ------------------------------------------------------------------
def TX11():
    pairs_ = [('Leak or blocked drain', 'Plumber'), ('Heating or hot water', 'Heating engineer'), ('Socket, light or wiring', 'Electrician'), ('Appliance stopped', 'Appliance repairer'),
              ('Roof or gutter', 'Roofer'), ('Door or lock', 'Locksmith'), ('Pests', 'Pest controller'), ('Fence, gate or shelf', 'Handyman'), ('Window or glass', 'Glazier')]
    f = tok('ctrade', 'Tiler')
    for iss, tr in reversed(pairs_): f = 'IF({in:issue}=%s,%s,%s)' % (tok('issue', iss), tok('ctrade', tr), f)
    return f
TX = TX11()
PS11 = 'MATCH(%s,%s,0)' % (TX, CT('trade'))
def W11(col): return 'IFERROR(INDEX(%s,%s)&"","")' % (CT(col), PS11)
def W11N(col): return 'IFERROR(INDEX(%s,%s),"")' % (CT(col), PS11)
tools.append(TOOL('whichtrade_tool', 'Which Trade To Call', 'Who do we call for this issue',
    'Pick the kind of issue: the trade is chosen, then the name, phone, last used date, cost last time and whether you would use them again come from the Trades directory.', [
    IL('issue', 'Kind of issue', 'issue', 'Leak or blocked drain')], [
    O('Trade to call', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (CT('trade'), PS11)), O('Name', 'text', W11('name')), O('Phone', 'text', W11('phone')), O('Last used', 'date', W11N('last_used')),
    O('Days since last used', 'int', W11N('days_since')), O('Cost last time', 'money', W11N('cost_last')),
    O('Would use again', 'text', 'IFERROR(IF(INDEX(%s,%s)=%s,%s,%s),"")' % (CT('would_use_again'), PS11, YES, lbl('Yes'), lbl('No'))),
    O('Repairs by this trade in the Repairs sheet', 'int', 'COUNTIFS(%s,%s)' % (RP('trade'), TX)), O('Cost lines of those repairs', 'money', 'SUMIFS(%s,%s,%s)' % (RP('cost'), RP('trade'), TX)),
    O('Verdict', 'text', 'IF(%s="","",%s)' % (W11('name'), V('Call', F(W11('name') + '&","'), 'last used', F(DT(W11N('last_used'))))))],
    GR('What if', ('Heating or hot water', {'issue': '=' + tok('issue', 'Heating or hot water')}), ('Socket, light or wiring', {'issue': '=' + tok('issue', 'Socket, light or wiring')}),
       ('Appliance stopped', {'issue': '=' + tok('issue', 'Appliance stopped')}), ('Roof or gutter', {'issue': '=' + tok('issue', 'Roof or gutter')}), ('Pests', {'issue': '=' + tok('issue', 'Pests')}))))

# 12 landlord request tracker -------------------------------------------------------------
P12 = 'MATCH({in:rank},%s,0)' % OR_('rank')
def L12(col): return 'IFERROR(INDEX(%s,%s)&"","")' % (OR_(col), P12)
def L12N(col): return 'IFERROR(INDEX(%s,%s),"")' % (OR_(col), P12)
tools.append(TOOL('landlord_tool', 'Landlord Request Tracker', 'For renters: when to ask again and when to escalate',
    'Open requests ranked by days waiting: type the days after which you ask again and the days after which you escalate; renters read a trade as the landlord.', [
    I('rank', 'Position in the list, 1 is the longest waiting', 1), I('wait', 'Ask again after, days', 14), I('esc', 'Escalate after, days', 28)], [
    O('Request', 'text', L12('issue')), O('Room', 'text', L12('room')), O('First reported', 'date', L12N('date')), O('Days waiting', 'int', L12N('days_open')), O('Status', 'text', L12('status')),
    O('Open requests', 'int', OPN), O('Requests past the ask-again days', 'int', 'COUNTIFS(%s,1,%s,">="&{in:wait})' % (RP('open'), RP('days_open'))),
    O('Requests past the escalate days', 'int', 'COUNTIFS(%s,1,%s,">="&{in:esc})' % (RP('open'), RP('days_open'))),
    O('Days until you ask again', 'int', 'IFERROR(MAX(0,{in:wait}-%s),"")' % L12N('days_open')),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s="",%s,IF(%s>={in:esc},%s,IF(%s>={in:wait},%s,%s))))' % (
        OPN, lbl('No open request'), L12('issue'), lbl('No request at that position'), L12N('days_open'), V('Escalate', F(L12('issue'))), L12N('days_open'),
        V('Ask again now about', F(L12('issue'))), V('Ask again after', F('{in:wait}-%s' % L12N('days_open')), 'more days')))],
    GR('What if', ('Second request', {'rank': 2}), ('Third request', {'rank': 3}), ('Ask again after 7 days', {'wait': 7}), ('Escalate after 21 days', {'esc': 21}), ('Escalate after 42 days', {'esc': 42}))))

# 13 season prep planner ------------------------------------------------------------------
S13 = '%s,{in:season}' % MT('season')
tools.append(TOOL('season_tool', 'Season Prep Planner', 'What do we prepare for a season and who does it',
    'Pick a season: the tasks of that season, the minutes, the typical cost lines and how the tasks are shared between the two adults and a trade.', [
    IL('season', 'Season', 'season', 'Autumn')], [
    O('Tasks in the season', 'int', 'COUNTIFS(%s,%s,"<>")' % (S13, MT('task_id'))), O('Due or overdue in the next 90 days', 'int', 'COUNTIFS(%s,%s,"<="&({today}+89))' % (S13, MT('next_due'))),
    O('Overdue now', 'int', 'COUNTIFS(%s,%s,%s)' % (S13, MT('status'), OVD)), O('Typical cost lines', 'money', 'SUMIFS(%s,%s)' % (MT('typical_cost'), S13)),
    O('Minutes of the tasks', 'int', 'SUMIFS(%s,%s)' % (MT('minutes'), S13)), O('Adult 1 tasks', 'int', 'COUNTIFS(%s,%s,%s)' % (S13, MT('assigned'), A1w)),
    O('Adult 2 tasks', 'int', 'COUNTIFS(%s,%s,%s)' % (S13, MT('assigned'), A2w)), O('Tasks for a trade', 'int', 'COUNTIFS(%s,%s,%s)' % (S13, MT('assigned'), TRw)),
    O('Verdict', 'text', V(F('{in:season}&":"'), F('COUNTIFS(%s,%s,"<>")' % (S13, MT('task_id'))), 'tasks, about', F('ROUND(SUMIFS(%s,%s),0)' % (MT('typical_cost'), S13)), 'in typical cost lines'))],
    GR('What if', ('Spring', {'season': '=' + tok('season', 'Spring')}), ('Summer', {'season': '=' + tok('season', 'Summer')}), ('Autumn', {'season': '=' + tok('season', 'Autumn')}),
       ('Any season', {'season': '=' + tok('season', 'Any season')}), ('Winter', {'season': '=' + tok('season', 'Winter')}))))

# 14 interval what-if ---------------------------------------------------------------------
def M14(col): return 'IFERROR(INDEX(%s,{in:row}),"")' % MT(col)
LD14 = 'IFERROR(IF(INDEX(%s,{in:row})=0,"",INDEX(%s,{in:row})),"")' % (MT('last_done'), MT('last_done'))
ND14 = 'IF(%s="","",%s+{in:new})' % (LD14, LD14)
tools.append(TOOL('interval_tool', 'Interval What-If', 'What happens if we change how often a task is done',
    'Type a task row and a new interval in days (typical, check the manual): the next due date moves and the number of times a year and the yearly cost line change.', [
    I('row', 'Row in the Maintenance sheet, 1 to 50', 1), I('new', 'New interval, days', 60)], [
    O('Task', 'text', 'IFERROR(INDEX(%s,{in:row})&"","")' % MT('task')), O('Interval now, days', 'int', M14('interval_days')), O('Last done', 'date', LD14), O('Next due now', 'date', M14('next_due')),
    O('Next due with the new interval', 'date', ND14), O('Moves by, days', 'int', 'IF(%s="","",%s-%s)' % (ND14, ND14, M14('next_due'))),
    O('Times a year now', 'num', 'IFERROR(ROUND(365/%s,1),"")' % M14('interval_days')), O('Times a year with the new interval', 'num', 'ROUND(365/{in:new},1)'),
    O('Typical cost lines a year now', 'money', 'IFERROR(ROUND(365/%s*%s,0),"")' % (M14('interval_days'), M14('typical_cost'))),
    O('Typical cost lines a year, new interval', 'money', 'IFERROR(ROUND(365/{in:new}*%s,0),"")' % M14('typical_cost')),
    O('Verdict', 'text', 'IF(%s="","",%s)' % (ND14, V('Next due moves to', F(DT(ND14) + '&","'), F('ROUND(365/{in:new},1)'), 'times a year')))],
    GR('What if', ('Every 30 days', {'new': 30}), ('Every 120 days', {'new': 120}), ('Every 182 days', {'new': 182}), ('Every 365 days', {'new': 365}), ('Every 45 days', {'new': 45}))))

# 15 overdue catch-up plan ----------------------------------------------------------------
OVM = 'SUMIFS(%s,%s,%s)' % (MT('minutes'), MT('status'), OVD)
tools.append(TOOL('catchup_tool', 'Overdue Catch-Up Plan', 'How many days to clear the overdue list',
    'The minutes of the overdue tasks spread over the minutes a day you can give: type your minutes a day and read the days to clear, the date and what needs a trade.', [
    I('mins', 'Minutes a day you can give', 45)], [
    O('Tasks overdue now', 'int', OVN), O('Overdue minutes', 'int', OVM), O('Days to clear at those minutes', 'int', 'IF(%s=0,0,ROUNDUP(%s/{in:mins},0))' % (OVM, OVM)),
    O('Cleared by', 'date', 'IF(%s=0,{today},{today}+ROUNDUP(%s/{in:mins},0)-1)' % (OVM, OVM)),
    O('Overdue tasks that need a trade', 'int', 'COUNTIFS(%s,%s,%s,1)' % (MT('status'), OVD, MT('trade_task'))),
    O('Overdue typical cost lines', 'money', 'SUMIFS(%s,%s,%s)' % (MT('typical_cost'), MT('status'), OVD)),
    O('First task to do', 'text', 'IFERROR(INDEX(%s,1)&"","")' % R('overdue', 'task')), O('Minutes of the first three tasks', 'int', 'IFERROR(INDEX(%s,3),SUM(%s))' % (R('overdue', 'cum_min'), R('overdue', 'minutes'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (OVN, lbl('Nothing is overdue'), V('Clear in', F('ROUNDUP(%s/{in:mins},0)' % OVM), 'days at', F('{in:mins}'), 'minutes a day')))],
    GR('What if', ('15 minutes a day', {'mins': 15}), ('20 minutes a day', {'mins': 20}), ('30 minutes a day', {'mins': 30}), ('60 minutes a day', {'mins': 60}), ('90 minutes a day', {'mins': 90}))))

# 16 done against planned -----------------------------------------------------------------
EL16 = '({today}-DATE(YEAR({today}),1,1)+1)'
EXP16 = 'SUMPRODUCT((%s>0)*INT(%s/(%s+(%s=0))+1-{in:share}))' % (MT('interval_days'), EL16, MT('interval_days'), MT('interval_days'))
DN16 = 'COUNTIFS(%s,1)' % LG('this_year')
tools.append(TOOL('ontrack_tool', 'Done Against Planned', 'Are we keeping up with the plan this year',
    'The tasks done this year in the Maintenance log against the repeats expected by now from every interval: type the share of an interval that must pass before a repeat is expected.', [
    I('share', 'Share of an interval before a repeat is due', 0.5, 'pct')], [
    O('Days of the year so far', 'int', EL16), O('Tasks done this year', 'int', DN16), O('Repeats expected by now', 'int', EXP16), O('Done against expected', 'pct', 'IFERROR(%s/%s,0)' % (DN16, EXP16)),
    O('Behind by', 'int', 'MAX(0,%s-%s)' % (EXP16, DN16)), O('Done on time this year', 'int', 'COUNTIFS(%s,1,%s,1)' % (LG('this_year'), LG('on_time'))),
    O('Done late this year', 'int', 'COUNTIFS(%s,1,%s,0)' % (LG('this_year'), LG('on_time'))), O('Share done on time', 'pct', 'IFERROR(COUNTIFS(%s,1,%s,1)/%s,0)' % (LG('this_year'), LG('on_time'), DN16)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (DN16, EXP16, V('On track,', F(PCT('IFERROR(%s/%s,0)' % (DN16, EXP16))), 'of the repeats expected'),
                                              V(F('%s-%s' % (EXP16, DN16)), 'behind,', F(PCT('IFERROR(%s/%s,0)' % (DN16, EXP16))), 'of the plan done')))],
    GR('What if', ('Expected from 25% of an interval', {'share': 0.25}), ('Expected from 75% of an interval', {'share': 0.75}), ('Expected from a full interval', {'share': 1.0}),
       ('Expected from 10% of an interval', {'share': 0.1}), ('Expected from half an interval', {'share': 0.5}))))

# 17 trade visit planner ------------------------------------------------------------------
TW = '%s,%s,%s' % (WIN('trade_due', '{in:days}'), MT('trade_task'), '1')
FD17 = 'IFERROR(SMALL(%s,COUNTIFS(%s,"<"&{today})+1),"")' % (MT('trade_due'), MT('trade_due'))
TR17 = 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0)))' % (FD17, MT('trade'), FD17, MT('trade_due'))
def TC(name): return 'COUNTIFS(%s,%s,%s)' % (WIN('trade_due', '{in:days}'), MT('trade'), tok('trade', name))
tools.append(TOOL('tradevisit_tool', 'Trade Visit Planner', 'Which trades do we book in the days ahead',
    'Tasks that need a trade and fall due in the days you type, grouped by trade; renters read the trade as a maintenance request to the landlord.', [
    I('days', 'Days ahead to look, 1 to 365', 60)], [
    O('Trade tasks in the window', 'int', 'COUNTIFS(%s,%s)' % (WIN('trade_due', '{in:days}'), MT('trade_task') + ',1')), O('Trade tasks overdue now', 'int', 'COUNTIFS(%s,%s,%s,1)' % (MT('status'), OVD, MT('trade_task'))),
    O('Plumber tasks', 'int', TC('Plumber')), O('Electrician tasks', 'int', TC('Electrician')), O('Roofer tasks', 'int', TC('Roofer')),
    O('Heating engineer tasks, next 365 days', 'int', 'COUNTIFS(%s,%s,%s)' % (WIN('trade_due', 365), MT('trade'), tok('trade', 'Heating engineer'))), O('Handyman tasks, next 365 days', 'int', 'COUNTIFS(%s,%s,%s)' % (WIN('trade_due', 365), MT('trade'), tok('trade', 'Handyman'))), O('First trade task due', 'date', FD17), O('Typical cost lines of the trade tasks in the window', 'money', 'SUMIFS(%s,%s)' % (MT('typical_cost'), TW)),
    O('Verdict', 'text', 'IF(%s="",%s,%s)' % (FD17, lbl('No trade visit in the window'), V('Book', F(TR17), 'first, due in', F('%s-{today}' % FD17), 'days,', F('COUNTIFS(%s,%s,1)' % (WIN('trade_due', '{in:days}'), MT('trade_task'))), 'trade tasks in the window')))],
    GR('What if', ('Next 30 days', {'days': 30}), ('Next 45 days', {'days': 45}), ('Next 90 days', {'days': 90}), ('Next 180 days', {'days': 180}), ('Next 365 days', {'days': 365}))))

# 18 cost against own history -------------------------------------------------------------
JAN = 'DATE(YEAR({today}),1,1)'
def CW(tbl, vcol, dcol, lo, hi): return 'SUMIFS(%s,%s,">="&%s,%s,"<="&%s)' % (R(tbl, vcol), R(tbl, dcol), lo, R(tbl, dcol), hi)
MY = CW('maintenance_log', 'cost', 'done', JAN, '{today}')
ML_ = CW('maintenance_log', 'cost', 'done', 'EDATE(%s,-12)' % JAN, 'EDATE({today},-12)')
RY_ = CW('repairs', 'cost', 'date', JAN, '{today}')
RL_ = CW('repairs', 'cost', 'date', 'EDATE(%s,-12)' % JAN, 'EDATE({today},-12)')
TY18 = '(%s+{in:repairs}*(%s))' % (MY, RY_)
TL18 = '(%s+{in:repairs}*(%s))' % (ML_, RL_)
CH18 = 'IFERROR(%s/%s-1,"")' % (TY18, TL18)
tools.append(TOOL('history_tool', 'Cost Against Own History', 'Are we spending more on the house than usual',
    'Maintenance and repair cost lines from 1 January to today against the same dates last year, from your own log; type 1 to include the repair cost lines or 0 for maintenance only.', [
    I('repairs', 'Include repair cost lines, 1 yes or 0 no', 1)], [
    O('Cost lines this year to date', 'money', TY18), O('Cost lines, same dates last year', 'money', TL18), O('Difference', 'money', '%s-%s' % (TY18, TL18)),
    O('Change on last year', 'pct', 'IFERROR(%s,0)' % CH18), O('Maintenance cost lines this year', 'money', MY), O('Maintenance cost lines last year, same dates', 'money', ML_),
    O('Repair cost lines this year', 'money', RY_), O('Repair cost lines last year, same dates', 'money', RL_),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(ABS(%s)<={set:in_line},%s,IF(%s>0,%s,%s)))' % (TL18, lbl('No cost lines last year'), 'IFERROR(%s,0)' % CH18, lbl('In line with your own history'), 'IFERROR(%s,0)' % CH18,
                                                                          V('Above your own history by', F(PCT('IFERROR(%s,0)' % CH18))), V('Below your own history by', F(PCT('-IFERROR(%s,0)' % CH18)))))],
    GR('What if', ('Maintenance only', {'repairs': 0}), ('With repairs', {'repairs': 1}))))

assert len(tools) == 18, len(tools)
