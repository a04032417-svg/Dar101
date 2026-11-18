"""Home Management suite part 4: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho4_lists import *
import ho4_data as DD


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def HOUSE(): return CA('household', 'Household', 'text', '{set:household}', 24)


YES = '{list:yesno.yes}'
OKS, DUES, OVD = (tok('mstat', s) for s in STATUS)
A1w, A2w, TRw = (tok('mwho', s) for s in MWHO)
OPEN, WAITING, FIXED = (tok("rstatus", s) for s in REPAIR_STATUS)
P1, P2, P3, P4 = (tok('person', s) for s in PERSONS4)
MSD = 'DATE(YEAR({today}),MONTH({today}),1)'
MT = lambda c: R('maintenance', c)
LG = lambda c: R('maintenance_log', c)
RP = lambda c: R('repairs', c)
CT = lambda c: R('contacts', c)
TM = lambda c: R('team', c)
AP = lambda c: R('appliances', c)
CS = lambda c: R('consumables', c)
RO = lambda c: R('reorder', c)
AS = lambda c: R('app_service', c)
OR_ = lambda c: R('open_repairs', c)
N12 = lambda c: R('next12', c)
LL_TOK = tok('ctrade', 'Landlord or agent')


def PHR(role): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (TM('phone'), tok('role', role), TM('role'))
def PHP(person): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (TM('phone'), tok('person', person), TM('person'))
def FNP(person): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (TM('first_name'), tok('person', person), TM('person'))
def CPH(token): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (CT('phone'), token, CT('trade'))


settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('adult1', 'Adult 1 shown as', 'text', 'Adult 1'), S('adult2', 'Adult 2 shown as', 'text', 'Adult 2'),
    S('child1', 'Child 1, first name only', 'text', 'Jo'), S('child2', 'Child 2, first name only', 'text', 'Kit'),
    S('soon_days', 'Due soon window, days (typical, your own)', 'int', SOON_DAYS), S('filter_days', 'Filter change every, days (typical, check the manual and your local rules)', 'int', 90),
    S('alarm_test_days', 'Alarm test every, days (typical, check the manual and your local rules)', 'int', 30),
    S('alarm_battery_days', 'Alarm batteries every, days (typical, check the manual and your local rules)', 'int', 182),
    S('service_months', 'Boiler or furnace service every, months (typical, check the manual and your local rules)', 'int', 12),
    S('lead_days', 'Order consumables this many days before the change', 'int', 10), S('catchup_min', 'Minutes a day you can give to catching up', 'int', 45),
    S('repeat_days', 'A repeat repair is another in the same room within, days', 'int', 365), S('wait_days', 'Ask a trade or the landlord again after, days', 'int', 14),
    S('grace_days', 'A task done within this many days after the due date counts as on time', 'int', 7), S('in_line', 'In line with your own history when within', 'pct', 0.10),
    S('trade_days', 'Look this many days ahead for trade visits', 'int', 60),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 team ------------------------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact; the texts in this workbook use these phones and dates. The week, open repairs and year counts fill in from the other sheets.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 17), LST('group', 'Group', 'tgroup', 11), C('phone', 'Phone', 'text', 18),
    C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11), C('first_name', 'First name', 'text', 12), LST('person', 'Person in the sheets', 'person', 12),
    C('next_date', 'Next visit date', 'date', 11), C('at_time', 'Visit from', 'time', 8), C('end_time', 'Visit until', 'time', 8),
    CA('eng_phone', 'Phone of the heating engineer', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Heating engineer'), 16),
    CA('elec_phone', 'Phone of the electrician', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Electrician'), 16),
    CA('mech_phone', 'Phone of the car mechanic', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Car mechanic'), 16),
    CA('nb_phone', 'Phone of the neighbour', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Neighbour'), 16),
    CA('ll_phone', 'Phone of the landlord or agent', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Landlord or agent'), 16),
    CA('gp_phone', 'Phone of the grandparent', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Grandparent'), 16),
    CA('a2_phone', 'Phone of adult 2', 'text', 'IF({col:person}=%s,{col:phone},"")' % P2, 16),
    CA('hm_phone', 'Phone of an adult', 'text', 'IF(OR({col:person}=%s,{col:person}=%s),{col:phone},"")' % (P1, P2), 16),
    CA('from_date', 'List from', 'date', 'IF({col:member_id}="","",{today})', 11),
    CA('due_n', 'Tasks due in the next 7 days', 'int', 'IF({col:member_id}="","",COUNTIFS(%s,">="&{today},%s,"<="&({today}+6)))' % (MT('next_due'), MT('next_due')), 9),
    CA('open_n', 'Repairs open', 'int', 'IF({col:member_id}="","",COUNTIFS(%s,"<>",%s,1))' % (RP('repair_id'), RP('open')), 9),
    CA('oldest_issue', 'Oldest open repair', 'text', 'IF({col:member_id}="","",IFERROR(INDEX(%s,1)&"",""))' % OR_('issue'), 26),
    CA('oldest_days', 'Days the oldest has been open', 'int', 'IF({col:member_id}="","",IFERROR(INDEX(%s,1),""))' % OR_('days_open'), 9),
    CA('sat_date', 'Next Saturday', 'date', 'IF({col:member_id}="","",{today}+MOD(6-WEEKDAY({today},2),7))', 11),
    CA('autumn_n', 'Autumn tasks in the plan', 'int', 'IF({col:member_id}="","",COUNTIFS(%s,%s,%s,"<>"))' % (MT('season'), tok('season', 'Autumn'), MT('task_id')), 9),
    CA('year', 'Year', 'int', 'IF({col:member_id}="","",YEAR({today}))', 7),
    CA('done_year', 'Tasks done this year', 'int', 'IF({col:member_id}="","",COUNTIFS(%s,1))' % LG('this_year'), 9),
    CA('repairs_year', 'Repairs this year', 'int', 'IF({col:member_id}="","",COUNTIFS(%s,{col:year}))' % RP('year'), 9), HOUSE()],
    DD.team_d(), 50))

# 2 maintenance -----------------------------------------------------------------------------
def G(x): return 'IF({col:task_id}="","",%s)' % x
tables.append(T('maintenance', 'Maintenance', 'Every maintenance task with its interval, last done and next due',
    'One row per task: area, season, interval in days (typical, check the manual), who does it, the typical cost line and when it was last done; next due, days to due and status fill in.', [
    C('task_id', 'Task ID', 'text', 9, required=True), C('task', 'Task', 'text', 32), LST('area', 'Area', 'area', 18), LST('season', 'Season', 'season', 12), C('interval_days', 'Interval, days', 'int', 9),
    LST('assigned', 'Assigned to', 'mwho', 12), C('typical_cost', 'Typical cost', 'money', 11), LST('trade', 'Trade', 'trade', 16), C('last_done', 'Last done', 'date', 11),
    C('minutes', 'Minutes', 'int', 8), C('safety', 'Safety check', 'bool', 9),
    CA('next_due', 'Next due', 'date', G('IF({col:last_done}>0,{col:last_done}+{col:interval_days},{today})'), 11),
    CA('days_to_due', 'Days to due', 'int', G('{col:next_due}-{today}'), 8), CA('overdue_days', 'Overdue days', 'int', G('MAX(0,{today}-{col:next_due})'), 8),
    CA('status', 'Status', 'text', G('IF({col:next_due}<{today},%s,IF({col:next_due}-{today}<=MIN({set:soon_days},ROUNDDOWN({col:interval_days}/2,0)),%s,%s))' % (OVD, DUES, OKS)), 10),
    CA('seq', 'Number', 'int', G('IFERROR(VALUE(RIGHT({col:task_id},2)),0)'), 7),
    CA('orank', 'Overdue rank, 1 is most overdue', 'int', 'IF({col:status}<>%s,"",COUNTIFS(%s,%s,%s,">"&{col:overdue_days})+COUNTIFS(%s,%s,%s,{col:overdue_days},%s,"<"&{col:seq})+1)' % (
        OVD, MT('status'), OVD, MT('overdue_days'), MT('status'), OVD, MT('overdue_days'), MT('seq')), 9),
    CA('drank', 'Rank by next due', 'int', G('COUNTIFS(%s,"<"&{col:next_due})+COUNTIFS(%s,{col:next_due},%s,"<"&{col:seq})+1' % (MT('next_due'), MT('next_due'), MT('seq'))), 8),
    CA('trade_task', 'Needs a trade, 1 or 0', 'int', G('IF({col:assigned}=%s,1,0)' % TRw), 8),
    CA('trade_due', 'Trade task next due', 'date', 'IF({col:trade_task}=1,{col:next_due},"")', 11),
    CA('safety_next', 'Safety check next due', 'date', 'IF({col:safety}=%s,{col:next_due},"")' % YES, 11),
    CA('safety_int', 'Safety check interval', 'int', 'IF({col:safety}=%s,{col:interval_days},"")' % YES, 9),
    CA('heat_phone', 'Phone, heating engineer task', 'text', 'IF({col:trade}=%s,%s,"")' % (tok('trade', 'Heating engineer'), CPH(tok('ctrade', 'Heating engineer'))), 16),
    CA('a1_od_phone', 'Phone, adult 1 task overdue', 'text', 'IF(AND({col:assigned}=%s,{col:status}=%s),%s,"")' % (A1w, OVD, PHP('Adult 1')), 16),
    CA('a1_alarm_phone', 'Phone, adult 1 monthly safety test', 'text', 'IF(AND({col:assigned}=%s,{col:safety}=%s,{col:interval_days}<=31),%s,"")' % (A1w, YES, PHP('Adult 1')), 16),
    CA('a2_due_phone', 'Phone, adult 2 task due', 'text', 'IF(AND({col:assigned}=%s,OR({col:status}=%s,{col:status}=%s)),%s,"")' % (A2w, DUES, OVD, PHP('Adult 2')), 16),
    CA('c1_phone', 'Phone of child 1, monthly safety test', 'text', 'IF(AND({col:safety}=%s,{col:interval_days}<=31),%s,"")' % (YES, PHP('Child 1')), 16),
    CA('c2_phone', 'Phone of child 2, monthly safety test', 'text', 'IF(AND({col:safety}=%s,{col:interval_days}<=31),%s,"")' % (YES, PHP('Child 2')), 16),
    CA('c1_first', 'Child 1 first name', 'text', '{set:child1}', 11), CA('c2_first', 'Child 2 first name', 'text', '{set:child2}', 11),
    CA('agree_by', 'Agree who by', 'date', G('{today}+3'), 11), HOUSE()],
    DD.maintenance_d(), 80, [A('status', '= ' + OVD, 'bad'), A('status', '= ' + DUES, 'warn'), A('status', '= ' + OKS, 'good')]))

# 3 maintenance log -------------------------------------------------------------------------
def GL(x): return 'IF({col:log_id}="","",%s)' % x
PREV = 'SUMPRODUCT(MAX((%s={col:task_id})*(%s<{col:done})*(%s)))' % (LG('task_id'), LG('done'), LG('done'))
tables.append(T('maintenance_log', 'Maintenance log', 'Every task done, who did it and what it cost',
    'One row per task done: date, task, who did it, the cost line and a short note; year, on time and filter or appliance service flags fill in.', [
    C('log_id', 'Log ID', 'text', 9, required=True), REF('task_id', 'Task ID', 'maintenance.task_id', 9), C('task', 'Task', 'text', 32), C('done', 'Done on', 'date', 11), LST('who', 'Done by', 'mwho', 12),
    C('cost', 'Cost', 'money', 11), C('note', 'Note', 'text', 26),
    CA('year', 'Year', 'int', GL('YEAR({col:done})'), 7), CA('last30', 'Last 30 days, 1 or 0', 'int', GL('IF(AND({col:done}>={today}-29,{col:done}<={today}),1,0)'), 8),
    CA('this_year', 'This year, 1 or 0', 'int', GL('IF(AND({col:done}<={today},YEAR({col:done})=YEAR({today})),1,0)'), 8),
    CA('prev', 'Previous time done', 'date', GL('IF(%s=0,"",%s)' % (PREV, PREV)), 11),
    CA('interval', 'Interval, days', 'int', GL('IFERROR(INDEX(%s,MATCH({col:task_id},%s,0)),"")' % (MT('interval_days'), MT('task_id'))), 8),
    CA('on_time', 'On time, 1 or 0', 'int', GL('IF(OR({col:prev}="",{col:interval}=""),1,IF({col:done}<={col:prev}+{col:interval}+{set:grace_days},1,0))'), 8),
    CA('svc', 'Appliance service, 1 or 0', 'int', GL('IF(COUNTIFS(%s,{col:task_id})>0,1,0)' % AP('service_task_id')), 8),
    CA('is_filter', 'Filter or consumable, 1 or 0', 'int', GL('IF(COUNTIFS(%s,{col:task_id})>0,1,0)' % CS('task_id')), 8)],
    DD.log_d(), 400))

# 4 repairs ---------------------------------------------------------------------------------
def GRP(x): return 'IF({col:repair_id}="","",%s)' % x
def TPH(): return 'IFERROR(INDEX(%s,MATCH({col:trade},%s,0))&"","")' % (CT('phone'), CT('trade'))
def TRP(token, extra=''): return 'IF(AND({col:trade}=%s%s),{col:tphone},"")' % (token, extra)
tables.append(T('repairs', 'Repairs', 'Every repair: what, where, which trade, the quote and the cost',
    'One row per repair: date, room, issue, the trade called, quote, cost, status and the date it was fixed; days open, repeat flag and the phone of the trade fill in.', [
    C('repair_id', 'Repair ID', 'text', 9, required=True), C('date', 'Reported on', 'date', 11), LST('room', 'Room', 'room', 13), C('issue', 'Issue', 'text', 32), LST('trade', 'Trade', 'trade', 16),
    C('quote', 'Quote', 'money', 11), C('cost', 'Cost', 'money', 11), LST('status', 'Status', 'rstatus', 10), C('fixed_on', 'Fixed on', 'date', 11), C('warranty_used', 'Warranty used', 'bool', 9),
    REF('item_id', 'Item ID', 'appliances.item_id', 9),
    CA('days_open', 'Days open', 'int', GRP('IF({col:fixed_on}>0,{col:fixed_on}-{col:date},{today}-{col:date})'), 8),
    CA('open', 'Open, 1 or 0', 'int', GRP('IF({col:status}<>%s,1,0)' % FIXED), 8), CA('year', 'Year', 'int', GRP('YEAR({col:date})'), 7),
    CA('seq', 'Number', 'int', GRP('IFERROR(VALUE(RIGHT({col:repair_id},3)),0)'), 7),
    CA('orank', 'Open rank, 1 is oldest', 'int', 'IF({col:open}<>1,"",COUNTIFS(%s,1,%s,">"&{col:days_open})+COUNTIFS(%s,1,%s,{col:days_open},%s,"<"&{col:seq})+1)' % (RP('open'), RP('days_open'), RP('open'), RP('days_open'), RP('seq')), 9),
    CA('repeat', 'Repeat in the room, 1 or 0', 'int', GRP('IF(COUNTIFS(%s,{col:room},%s,">="&({col:date}-{set:repeat_days}),%s,"<="&({col:date}+{set:repeat_days}),%s,"<>"&{col:repair_id})>0,1,0)' % (RP('room'), RP('date'), RP('date'), RP('repair_id'))), 8),
    CA('rkey', 'Room and date', 'text', GRP('{col:room}&"-"&{col:date}'), 14),
    CA('item', 'Item', 'text', 'IF({col:item_id}="","",IFERROR(INDEX(%s,MATCH({col:item_id},%s,0))&"",""))' % (AP('item'), AP('item_id')), 20),
    CA('warranty_end', 'Warranty end of the item', 'date', 'IF({col:item_id}="","",IFERROR(IF(INDEX(%s,MATCH({col:item_id},%s,0))=0,"",INDEX(%s,MATCH({col:item_id},%s,0))),""))' % (AP('warranty_end'), AP('item_id'), AP('warranty_end'), AP('item_id')), 11),
    CA('tphone', 'Phone of the trade', 'text', GRP(TPH()), 16),
    CA('tfirst', 'First name of the trade', 'text', GRP('IFERROR(INDEX(%s,MATCH({col:trade},%s,0))&"","")' % (CT('first_name'), CT('trade'))), 12),
    CA('pl_open', 'Phone, plumber, open', 'text', TRP(tok('trade', 'Plumber'), ',{col:open}=1'), 16), CA('pl_done', 'Phone, plumber, fixed', 'text', TRP(tok('trade', 'Plumber'), ',{col:open}=0'), 16),
    CA('el_phone', 'Phone, electrician', 'text', TRP(tok('trade', 'Electrician')), 16), CA('he_phone', 'Phone, heating engineer', 'text', TRP(tok('trade', 'Heating engineer')), 16),
    CA('ap_open', 'Phone, appliance repairer, open', 'text', TRP(tok('trade', 'Appliance repairer'), ',{col:open}=1'), 16),
    CA('ap_done', 'Phone, appliance repairer, fixed', 'text', TRP(tok('trade', 'Appliance repairer'), ',{col:open}=0'), 16),
    CA('ro_phone', 'Phone, roofer', 'text', TRP(tok('trade', 'Roofer')), 16), CA('ha_phone', 'Phone, handyman', 'text', TRP(tok('trade', 'Handyman')), 16),
    CA('pe_phone', 'Phone, pest controller', 'text', TRP(tok('trade', 'Pest controller')), 16),
    CA('ll_open', 'Phone, landlord, open request', 'text', 'IF({col:open}=1,%s,"")' % CPH(LL_TOK), 16), CA('ll_done', 'Phone, landlord, fixed', 'text', 'IF(AND({col:repair_id}<>"",{col:open}=0),%s,"")' % CPH(LL_TOK), 16),
    HOUSE()], DD.repairs_d(), 120, [A('status', '= ' + OPEN, 'bad'), A('status', '= ' + WAITING, 'warn'), A('status', '= ' + FIXED, 'good')]))

# 5 appliances and systems ------------------------------------------------------------------
tables.append(T('appliances', 'Appliances and systems', 'Appliances and systems with the maintenance task that services them',
    'One row per appliance or system: room, purchase date, warranty end (typed from your paperwork) and the task of the Maintenance sheet that services it.', [
    C('item_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 26), LST('room', 'Room', 'room', 13), C('purchase_date', 'Purchase date', 'date', 11), C('warranty_end', 'Warranty end', 'date', 11),
    REF('service_task_id', 'Service task ID', 'maintenance.task_id', 10)], DD.appliances_d(), 40))

# 6 trades directory ------------------------------------------------------------------------
tables.append(T('contacts', 'Trades directory', 'Trades and other contacts: who, last used, cost last time, would use again',
    'One row per contact: kind, type of trade, phone, last used, the cost line last time and whether you would use them again; days since last use fills in.', [
    C('contact_id', 'Contact ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('kind', 'Kind', 'ckind', 11), LST('trade', 'Trade', 'ctrade', 20), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('last_used', 'Last used', 'date', 11), C('cost_last', 'Cost last time', 'money', 12), C('would_use_again', 'Would use again', 'bool', 9),
    C('member_id', 'Member ID', 'text', 9), C('first_name', 'First name', 'text', 12),
    CA('days_since', 'Days since last use', 'int', 'IF(OR({col:contact_id}="",{col:last_used}=""),"",{today}-{col:last_used})', 9),
    CA('is_trade', 'Trade, 1 or 0', 'int', 'IF({col:contact_id}="","",IF({col:kind}=%s,1,0))' % tok('ckind', 'Trade'), 8),
    CA('idle', 'Not used for 12 months, 1 or 0', 'int', 'IF({col:days_since}="","",IF(AND({col:is_trade}=1,{col:days_since}>=365),1,0))', 9)],
    DD.contacts_d(), 60))

# 7 filters and consumables -----------------------------------------------------------------
tables.append(T('consumables', 'Filters and consumables', 'Filters, batteries and other consumables with change interval and stock',
    'One row per consumable: where it is used, how often it is changed (typical, check the manual), when it was last changed, the units in stock and the task it belongs to.', [
    C('item', 'Item', 'text', 28, required=True), C('code', 'Size or code', 'text', 18), C('where_used', 'Where used', 'text', 22), C('interval_days', 'Change every, days', 'int', 10),
    C('last_changed', 'Last changed', 'date', 11), C('units', 'Units in stock', 'int', 9), REF('task_id', 'Task ID', 'maintenance.task_id', 9), C('stored', 'Kept in', 'text', 28)],
    DD.consumables_d(), 20))

# 8 master schedule -------------------------------------------------------------------------
def PIX(col): return 'IF({col:pos}="","",INDEX(%s,{col:pos}))' % MT(col)
def PID(col): return 'IF({col:pos}="","",IF(INDEX(%s,{col:pos})=0,"",INDEX(%s,{col:pos})))' % (MT(col), MT(col))
tables.append(T('schedule', 'Master schedule', 'Every task in the order it falls due',
    'Type the ranks 1 to 50 once; the tasks fill in soonest due first with area, season, last done, next due, days to due and status.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('pos', 'Row in Maintenance', 'int', 'IFERROR(MATCH({col:rank},%s,0),"")' % MT('drank'), 8),
    CA('task_id', 'Task ID', 'text', PIX('task_id'), 9), CA('task', 'Task', 'text', PIX('task'), 32), CA('area', 'Area', 'text', PIX('area'), 18), CA('season', 'Season', 'text', PIX('season'), 12),
    CA('last_done', 'Last done', 'date', PID('last_done'), 11), CA('next_due', 'Next due', 'date', PIX('next_due'), 11), CA('days_to_due', 'Days to due', 'int', PIX('days_to_due'), 8),
    CA('status', 'Status', 'text', PIX('status'), 10), CA('assigned', 'Assigned to', 'text', PIX('assigned'), 12)],
    DD.schedule_d(), 60, [A('status', '= ' + OVD, 'bad'), A('status', '= ' + DUES, 'warn'), A('status', '= ' + OKS, 'good')]))

# 9 most overdue first ----------------------------------------------------------------------
tables.append(T('overdue', 'Most overdue first', 'Overdue tasks, the most overdue at the top',
    'Type the ranks 1 to 20 once; the overdue tasks fill in with the days overdue, who does them, the typical cost line and the minutes, with the minutes so far down the list.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('pos', 'Row in Maintenance', 'int', 'IFERROR(MATCH({col:rank},%s,0),"")' % MT('orank'), 8),
    CA('task_id', 'Task ID', 'text', PIX('task_id'), 9), CA('task', 'Task', 'text', PIX('task'), 32), CA('area', 'Area', 'text', PIX('area'), 18),
    CA('overdue_days', 'Overdue days', 'int', PIX('overdue_days'), 8), CA('assigned', 'Assigned to', 'text', PIX('assigned'), 12), CA('typical_cost', 'Typical cost', 'money', PIX('typical_cost'), 11),
    CA('minutes', 'Minutes', 'int', PIX('minutes'), 8),
    CA('cum_min', 'Minutes so far', 'int', 'IF({col:pos}="","",SUMIFS(%s,%s,"<="&{col:rank}))' % (R('overdue', 'minutes'), R('overdue', 'rank')), 9)],
    DD.overdue_d(), 30, [A('overdue_days', '> 14', 'bad'), A('overdue_days', '> 0', 'warn')]))

# 10 next 12 months -------------------------------------------------------------------------
def FOCC(x): return 'IF(%s<={col:first},0,INT((%s-1-{col:first})/{col:interval})+1)' % (x, x)
def NM(k): return 'IF(OR({col:first}="",{col:interval}=""),"",(%s)-(%s))' % (FOCC('EDATE(%s,%d)' % (MSD, k)), FOCC('EDATE(%s,%d)' % (MSD, k - 1)))
def NC(k): return 'IF({col:m%d}="","",{col:m%d}*{col:typical})' % (k, k)
def NL(col): return 'IF({col:task_id}="","",IFERROR(INDEX(%s,MATCH({col:task_id},%s,0)),""))' % (MT(col), MT('task_id'))
tables.append(T('next12', 'Next 12 months', 'Every task and its repeat dates counted over the next 12 months',
    'One row per task: the interval and next due from the Maintenance sheet, then how many times the task falls due in each of the next 12 months (month 1 is this month) and its cost lines.', [
    REF('task_id', 'Task ID', 'maintenance.task_id', 9, required=True), CA('task', 'Task', 'text', NL('task'), 32), CA('interval', 'Interval, days', 'int', NL('interval_days'), 8),
    CA('next_due', 'Next due', 'date', NL('next_due'), 11), CA('typical', 'Typical cost', 'money', NL('typical_cost'), 11),
    CA('first', 'First date in the window', 'date', 'IF({col:next_due}="","",MAX({col:next_due},{today}))', 11)] +
    [CA('m%d' % k, 'Month %d' % k, 'int', NM(k), 7) for k in range(1, 13)] +
    [CA('total', 'Times in 12 months', 'int', 'IF({col:first}="","",SUM(%s)' % ','.join('{col:m%d}' % k for k in range(1, 13)) + ')', 9), CA('cost12', 'Cost lines in 12 months', 'money', 'IF({col:total}="","",{col:total}*{col:typical})', 12)] +
    [CA('c%d' % k, 'Cost month %d' % k, 'money', NC(k), 7) for k in range(1, 13)],
    DD.next12_d(), 80))

# 11 month by month load --------------------------------------------------------------------
MCH = lambda pref: 'CHOOSE({col:mk},%s)' % ','.join('SUM(%s)' % R('next12', '%s%d' % (pref, k)) for k in range(1, 13))
tables.append(T('month_load', 'Month by month load', 'Tasks and cost lines due in each of the next 12 months',
    'Type the month numbers 1 to 12 once with the month label; the month, the tasks due, the typical cost lines and the busiest month fill in from the Next 12 months sheet.', [
    C('mk', 'Month number', 'int', 8, required=True), LST('ahead', 'Month ahead', 'ahead12', 13), CA('month', 'Month', 'date', 'IF({col:mk}="","",EDATE(%s,{col:mk}-1))' % MSD, 11),
    CA('tasks_due', 'Tasks due', 'int', 'IF({col:mk}="","",%s)' % MCH('m'), 9, visual='bar'), CA('cost_lines', 'Typical cost lines', 'money', 'IF({col:mk}="","",%s)' % MCH('c'), 12),
    CA('busiest', 'Busiest month, 1 or 0', 'int', 'IF({col:mk}="","",IF({col:tasks_due}=MAX(%s),1,0))' % R('month_load', 'tasks_due'), 9)],
    DD.month_load_d(), 12))

# 12 season view ----------------------------------------------------------------------------
tables.append(T('season_view', 'Season view', 'Tasks by season and what falls due in the next 90 days',
    'One row per season: the tasks in the plan and how many are due or overdue within the next 90 days.', [
    LST('season', 'Season', 'season', 14, required=True),
    CA('tasks', 'Tasks in the plan', 'int', 'IF({col:season}="","",COUNTIFS(%s,{col:season},%s,"<>"))' % (MT('season'), MT('task_id')), 10),
    CA('due_90', 'Due or overdue in 90 days', 'int', 'IF({col:season}="","",COUNTIFS(%s,{col:season},%s,"<="&({today}+89)))' % (MT('season'), MT('next_due')), 12)],
    DD.season_d(), 5))

# 13 consumables reorder list ---------------------------------------------------------------
def RC(col): return 'IF({col:pos}="","",INDEX(%s,{col:pos}))' % CS(col)
tables.append(T('reorder', 'Consumables reorder list', 'When each filter or consumable changes and when to order the next one',
    'One row per consumable: next change, the date to order before, units in stock and a stock flag; the order lead time is in Settings.', [
    REF('item', 'Item', 'consumables.item', 28, required=True), CA('pos', 'Row in Filters and consumables', 'int', 'IFERROR(MATCH({col:item},%s,0),"")' % CS('item'), 8),
    CA('next_change', 'Next change', 'date', 'IF({col:pos}="","",IF(INDEX(%s,{col:pos})=0,"",INDEX(%s,{col:pos})+INDEX(%s,{col:pos})))' % (CS('last_changed'), CS('last_changed'), CS('interval_days')), 11),
    CA('reorder_before', 'Order before', 'date', 'IF({col:next_change}="","",{col:next_change}-{set:lead_days})', 11), CA('units', 'Units in stock', 'int', RC('units'), 9),
    CA('flag', 'Stock flag', 'text', 'IF({col:pos}="","",IF({col:units}>=1,%s,IF({col:reorder_before}<={today},%s,%s)))' % (lbl('In stock'), lbl('Order now'), lbl('Order soon')), 11),
    CA('days_to', 'Days to the change', 'int', 'IF({col:next_change}="","",{col:next_change}-{today})', 9),
    CA('change_status', 'Change status', 'text', 'IF({col:next_change}="","",IF({col:days_to}<0,%s,IF({col:days_to}<={set:soon_days},%s,%s)))' % (OVD, DUES, OKS), 10),
    CA('need_change', 'Change date when out of stock', 'date', 'IF({col:next_change}="","",IF({col:units}<1,{col:next_change},""))', 11),
    CA('stored', 'Kept in', 'text', RC('stored'), 28), CA('task_id', 'Task ID', 'text', RC('task_id'), 9),
    CA('a2_phone', 'Phone, adult 2, change overdue', 'text', 'IF({col:change_status}=%s,%s,"")' % (OVD, PHP('Adult 2')), 16),
    CA('hm_phone', 'Phone, adult 1', 'text', 'IF({col:pos}="","",%s)' % PHP('Adult 1'), 16), HOUSE()],
    DD.reorder_d(), 20, [A('flag', '= ' + lbl('Order now'), 'bad'), A('flag', '= ' + lbl('Order soon'), 'warn'), A('flag', '= ' + lbl('In stock'), 'good')]))

# 14 appliance service history --------------------------------------------------------------
def AL(col): return 'IFERROR(INDEX(%s,MATCH({col:item_id},%s,0))&"","")' % (AP(col), AP('item_id'))
def GA(x): return 'IF({col:task_id}="","",%s)' % x
def ML(col): return 'IFERROR(INDEX(%s,MATCH({col:task_id},%s,0)),"")' % (MT(col), MT('task_id'))
tables.append(T('app_service', 'Appliance service history', 'Last and next service of every appliance, with services and cost lines',
    'Type the appliance IDs once; the item, the task that services it, the last and next service, the services logged and the cost lines per year of age fill in.', [
    REF('item_id', 'Item ID', 'appliances.item_id', 9, required=True), CA('item', 'Item', 'text', AL('item'), 24), CA('task_id', 'Service task ID', 'text', AL('service_task_id'), 10),
    CA('ld0', 'Last done, raw', 'int', GA(ML('last_done')), 8), CA('last_service', 'Last service', 'date', GA('IF({col:ld0}="","",IF({col:ld0}=0,"",{col:ld0}))'), 11),
    CA('interval', 'Interval, days', 'int', GA(ML('interval_days')), 8), CA('next_service', 'Next service', 'date', 'IF(OR({col:last_service}="",{col:interval}=""),"",{col:last_service}+{col:interval})', 11),
    CA('days_to', 'Days to service', 'int', 'IF({col:next_service}="","",{col:next_service}-{today})', 8),
    CA('overdue_days', 'Overdue days', 'int', 'IF({col:next_service}="","",MAX(0,{today}-{col:next_service}))', 8),
    CA('status', 'Status', 'text', 'IF({col:next_service}="","",IF({col:next_service}<{today},%s,IF({col:next_service}-{today}<=MIN({set:soon_days},ROUNDDOWN({col:interval}/2,0)),%s,%s)))' % (OVD, DUES, OKS), 10),
    CA('who', 'Done by', 'text', GA('IF(%s<>"",%s,%s)' % (ML('trade'), ML('trade'), ML('assigned'))), 16),
    CA('services', 'Services logged', 'int', GA('COUNTIFS(%s,{col:task_id})' % LG('task_id')), 8),
    CA('cost12', 'Service cost lines, 12 months', 'money', GA('SUMIFS(%s,%s,{col:task_id},%s,">="&({today}-364))' % (LG('cost'), LG('task_id'), LG('done'))), 12),
    CA('purchase', 'Purchase date', 'date', 'IF({col:item}="","",IFERROR(INDEX(%s,MATCH({col:item_id},%s,0)),""))' % (AP('purchase_date'), AP('item_id')), 11),
    CA('age_years', 'Age, years', 'num', 'IF({col:purchase}="","",ROUND(({today}-{col:purchase})/365,1))', 8),
    CA('svc_cost', 'Service cost lines since purchase', 'money', GA('SUMIFS(%s,%s,{col:task_id},%s,">="&{col:purchase})' % (LG('cost'), LG('task_id'), LG('done'))), 12),
    CA('rep_cost', 'Repair cost lines of the item', 'money', 'IF({col:item}="","",SUMIFS(%s,%s,{col:item_id}))' % (RP('cost'), RP('item_id')), 12),
    CA('repairs', 'Repairs of the item', 'int', 'IF({col:item}="","",COUNTIFS(%s,{col:item_id}))' % RP('item_id'), 8),
    CA('life_cost', 'Cost lines in all', 'money', 'IF({col:item}="","",{col:svc_cost}+{col:rep_cost})', 11),
    CA('yearly_cost', 'Cost lines per year of age', 'money', 'IF({col:age_years}="","",IF({col:age_years}>0,{col:life_cost}/{col:age_years},{col:life_cost}))', 12),
    CA('no', 'Number', 'int', 'IF({col:item}="","",IFERROR(VALUE(RIGHT({col:item_id},3)),0))', 7),
    CA('srank', 'Rank by next service', 'int', 'IF({col:next_service}="","",COUNTIFS(%s,"<"&{col:next_service})+COUNTIFS(%s,{col:next_service},%s,"<"&{col:no})+1)' % (AS('next_service'), AS('next_service'), AS('no')), 8),
    CA('orank', 'Overdue rank', 'int', 'IF({col:status}<>%s,"",COUNTIFS(%s,%s,%s,">"&{col:overdue_days})+COUNTIFS(%s,%s,%s,{col:overdue_days},%s,"<"&{col:no})+1)' % (OVD, AS('status'), OVD, AS('overdue_days'), AS('status'), OVD, AS('overdue_days'), AS('no')), 8)],
    DD.app_service_d(), 40, [A('status', '= ' + OVD, 'bad'), A('status', '= ' + DUES, 'warn'), A('status', '= ' + OKS, 'good')]))

# 15 service overdue list -------------------------------------------------------------------
def SX(col): return 'IF({col:pos}="","",INDEX(%s,{col:pos}))' % AS(col)
tables.append(T('svc_overdue', 'Service overdue list', 'Appliance services that are overdue, the most overdue first',
    'Type the ranks 1 to 15 once; the appliances with an overdue service fill in with the next service date, the days overdue and who does it.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('pos', 'Row in the service history', 'int', 'IFERROR(MATCH({col:rank},%s,0),"")' % AS('orank'), 8),
    CA('item', 'Item', 'text', SX('item'), 24), CA('task_id', 'Service task ID', 'text', SX('task_id'), 10), CA('next_service', 'Next service', 'date', SX('next_service'), 11),
    CA('overdue_days', 'Overdue days', 'int', SX('overdue_days'), 8), CA('who', 'Done by', 'text', SX('who'), 16)],
    DD.svc_overdue_d(), 20, [A('overdue_days', '> 0', 'warn')]))

# 16 open repairs by days open --------------------------------------------------------------
def OX(col): return 'IF({col:pos}="","",INDEX(%s,{col:pos}))' % RP(col)
tables.append(T('open_repairs', 'Open repairs by days open', 'Open and waiting repairs, the oldest first',
    'Type the ranks 1 to 15 once; the open and waiting repairs fill in with the room, the trade, the days open, the status and the quote.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('pos', 'Row in Repairs', 'int', 'IFERROR(MATCH({col:rank},%s,0),"")' % RP('orank'), 8),
    CA('repair_id', 'Repair ID', 'text', OX('repair_id'), 9), CA('room', 'Room', 'text', OX('room'), 13), CA('issue', 'Issue', 'text', OX('issue'), 32), CA('trade', 'Trade', 'text', OX('trade'), 16),
    CA('date', 'Reported on', 'date', OX('date'), 11), CA('days_open', 'Days open', 'int', OX('days_open'), 8), CA('status', 'Status', 'text', OX('status'), 10),
    CA('quote', 'Quote', 'money', OX('quote'), 11), CA('chase', 'Days past the chase date', 'int', 'IF({col:pos}="","",MAX(0,{col:days_open}-{set:wait_days}))', 9)],
    DD.open_repairs_d(), 20, [A('days_open', '> 28', 'bad'), A('days_open', '> 14', 'warn')]))

# 17 repairs by room and year ---------------------------------------------------------------
def RY(): return '%s,{col:room},%s,{col:year}' % (RP('room'), RP('year'))
tables.append(T('repair_room_year', 'Repairs by room and year', 'Repairs, cost lines and days open for each room and year',
    'One row per room and year: type the room and pick the year from the cost sheet; the repairs, the cost lines, the repairs with the warranty used and the days open fill in.', [
    LST('room', 'Room', 'room', 14, required=True), REF('year', 'Year', 'cost_year.year', 8),
    CA('repairs', 'Repairs', 'int', 'IF({col:room}="","",COUNTIFS(%s))' % RY(), 9), CA('cost_lines', 'Cost lines', 'money', 'IF({col:room}="","",SUMIFS(%s,%s))' % (RP('cost'), RY()), 11),
    CA('warranty_n', 'Warranty used', 'int', 'IF({col:room}="","",COUNTIFS(%s,%s))' % (RY(), RP('warranty_used') + ',' + YES), 9),
    CA('days_open', 'Days open, all repairs', 'int', 'IF({col:room}="","",SUMIFS(%s,%s))' % (RP('days_open'), RY()), 10)],
    DD.room_year_d(), 40))

# 18 repeat repairs -------------------------------------------------------------------------
tables.append(T('repeat_repairs', 'Repeat repairs', 'Rooms with more than one repair in the repeat window',
    'One row per room: the repairs in the window set in Settings and a flag when the room has two or more.', [
    LST('room', 'Room', 'room', 14, required=True),
    CA('repairs12', 'Repairs in the window', 'int', 'IF({col:room}="","",COUNTIFS(%s,{col:room},%s,">="&({today}-{set:repeat_days}),%s,"<="&{today}))' % (RP('room'), RP('date'), RP('date')), 10),
    CA('flag', 'Repeat flag', 'text', 'IF({col:room}="","",IF({col:repairs12}>=2,%s,IF({col:repairs12}=1,%s,%s)))' % (lbl('Repeat'), lbl('One repair'), lbl('None')), 12)],
    DD.repeat_d(), 10, [A('flag', '= ' + lbl('Repeat'), 'bad'), A('flag', '= ' + lbl('One repair'), 'warn')]))

# 19 trades used ----------------------------------------------------------------------------
def TY(): return '%s,{col:trade},%s,{col:year}' % (RP('trade'), RP('year'))
tables.append(T('trades_used', 'Trades used', 'Calls and cost lines of each trade by year',
    'One row per trade and year: pick the trade and the year; the calls and the cost lines fill in from the Repairs sheet.', [
    LST('trade', 'Trade', 'trade', 18, required=True), REF('year', 'Year', 'cost_year.year', 8),
    CA('calls', 'Calls', 'int', 'IF({col:trade}="","",COUNTIFS(%s))' % TY(), 8), CA('cost_lines', 'Cost lines', 'money', 'IF({col:trade}="","",SUMIFS(%s,%s))' % (RP('cost'), TY()), 11)],
    DD.trades_used_d(), 40))

# 20 maintenance and repair cost by year ----------------------------------------------------
tables.append(T('cost_year', 'Cost by year', 'Maintenance and repair cost lines by year',
    'Type the years once; the cost lines of the Maintenance log and of the Repairs sheet fill in for each year.', [
    C('year', 'Year', 'int', 8, required=True),
    CA('maint_cost', 'Maintenance cost lines', 'money', 'IF({col:year}="","",SUMIFS(%s,%s,{col:year}))' % (LG('cost'), LG('year')), 14),
    CA('repair_cost', 'Repair cost lines', 'money', 'IF({col:year}="","",SUMIFS(%s,%s,{col:year}))' % (RP('cost'), RP('year')), 14)],
    DD.cost_year_d(), 6))

assert len(tables) == 20, len(tables)
