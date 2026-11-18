"""Home Management suite part 6: settings and the 20 tables with their calculated columns (calendar, conflicts, work pattern, terms, gifts, pets, vehicles)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho6_lists import *
import ho6_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def G(idc, expr): return 'IF({col:%s}="","",%s)' % (idc, expr)


YES = '{list:yesno.yes}'
MON, TUE, WED, THU, FRI, SAT, SUN = (tok('wday', d) for d in WEEKDAYS)
D_A1, D_A2, D_GP, D_CP, D_WB = (tok('driver', d) for d in DRIVERS)
PA1, PA2, PC1, PC2, PWH = (tok('epeople', d) for d in EVENT_PEOPLE)
K_SCH, K_ACT, K_BDAY, K_VIS, K_HOL, K_APPT, K_HOUSE, K_TRIP = (tok('ekind', k) for k in EVENT_KINDS)
SH_E, SH_L, SH_O = (tok('shift', s) for s in SHIFTS)
T_TERM, T_BREAK = tok('tkind', 'Term'), tok('tkind', 'Break')
G_IDEA, G_BOUGHT, G_WRAP, G_GIVEN = (tok('gstatus', s) for s in GIFT_STATUS)
PT_GROOM, PT_VET, PT_VAC, PT_NAIL, PT_FOOD, PT_BATH = (tok('ptask', s) for s in PET_TASKS)
VK_SERVICE, VK_TYRES, VK_TEST, VK_INS, VK_REG, VK_REPAIR, VK_MR = (tok('vkind', s) for s in VEH_KINDS)
TN_SUMMER = tok('tname', 'Summer term')
W_OK, W_SOON, W_OVD, W_NODATE = (lbl(w) for w in ('OK', 'Due soon', 'Overdue', 'No date typed'))

ER = lambda c: R('events', c)
SR = lambda c: R('shifts', c)
TR = lambda c: R('terms', c)
GR_ = lambda c: R('gifts', c)
PR = lambda c: R('pets', c)
PCR = lambda c: R('pet_care', c)
VR = lambda c: R('vehicles', c)
VLR = lambda c: R('vehicle_log', c)
MR = lambda c: R('tasks', c)
CFR = lambda c: R('conflicts', c)
BR = lambda c: R('busy', c)
DR = lambda c: R('driving', c)
SVR = lambda c: R('school_view', c)
GPR = lambda c: R('gift_plan', c)
VSR = lambda c: R('visitors', c)
PSR = lambda c: R('pet_sched', c)
PFR = lambda c: R('pet_food', c)
VDR = lambda c: R('vehicle_dates', c)
VER = lambda c: R('vehicle_est', c)

# first day of the week from Settings
WKK = '(' + '+'.join('({set:week_start}=%s)*%d' % (tok('wday', d), i + 1) for i, d in enumerate(WEEKDAYS[1:])) + ')'
WS = '({today}-MOD(WEEKDAY({today},2)-1-%s,7))' % WKK
def WSD(x): return '(%s-MOD(WEEKDAY(%s,2)-1-%s,7))' % (x, x, WKK)
WDAYS7 = ','.join(tok('wday', d) for d in WEEKDAYS)


def TLR(role, col): return 'IFERROR(INDEX({range:team.%s},MATCH({list:role.%s},{range:team.role},0))&"","")' % (col, key('role', role))
def TLC(n, col): return 'IFERROR(INDEX({range:team.%s},MATCH({set:child%d},{range:team.short},0))&"","")' % (col, n)
def NAME(role, k, label=None): return CA(k, label or (role + ' name'), 'text', TLR(role, 'short'), 14)
def PHONE(role, k, label=None): return CA(k, label or (role + ' phone'), 'text', TLR(role, 'phone'), 18)
def CNAME(n, k): return CA(k, 'Child %d name' % n, 'text', TLC(n, 'short'), 14)
def CPHONE(n, k): return CA(k, 'Child %d phone' % n, 'text', TLC(n, 'phone'), 18)
def HOUSE(): return CA('household', 'Household', 'text', '{set:household}', 24)
def CT(role, p): return [NAME(role, p + 'n'), PHONE(role, p + 'p')]


settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('adult1', 'Adult 1 shown as', 'text', 'Adult 1'), S('adult2', 'Adult 2 shown as', 'text', 'Adult 2'),
    S('child1', 'Child 1, first name only', 'text', 'Jo'), S('child2', 'Child 2, first name only', 'text', 'Kit'),
    S('week_start', 'Week starts on', 'list', key('wday', WEEK_START), list='wday'),
    S('soon_days', 'Due soon: within this many days', 'int', SOON_DAYS),
    S('trip_date', 'Family trip: first day', 'date', next(e['date'] for e in D.EV if e['event_id'] == D.ST['trip'])), S('trip_days', 'Family trip: days away', 'int', 8),
    S('beds_total', 'Beds for visitors (typed)', 'int', 4),
    S('agreed_drive_share', 'Adult 2 agreed share of trips', 'pct', 0.5), S('fair_margin', 'A share is even within this margin', 'pct', 0.10),
    S('reorder_days', 'Reorder pet food this many days before it runs out', 'int', 10),
    S('renew_days', 'Renewals window, days (typical 90)', 'int', 90), S('gift_days', 'Gift window, days', 'int', 60),
    S('service_km', 'Vehicle service every, km (typical)', 'int', 12000), S('service_days', 'Vehicle service every, days (typical)', 'int', 365),
    S('daily_g_1', 'Pet 1 daily food, grams (first row of Pets)', 'int', 320), S('daily_g_2', 'Pet 2 daily food, grams (second row of Pets)', 'int', 70),
    S('evening_hour', 'An evening starts at this hour, 24-hour clock', 'int', 17),
]
assert 3 <= len(settings) <= 20, len(settings)

tables = []
# 1 team ------------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact: role, phone and e-mail; the texts use these numbers. Children are listed by first name. Renters read a trade as the landlord.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 16), C('group', 'Group', 'text', 10), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11), C('short', 'Short name', 'text', 12), HOUSE()], D.team_d(), 50))

# 2 events ----------------------------------------------------------------------
def EG(x): return G('event_id', x)
DCL = 'IF(OR({col:driver}=%s,{col:driver}=%s,{col:driver}=%s),COUNTIFS(%s,{col:date},%s,{col:driver},%s,"<"&{col:em},%s,">"&{col:sm},%s,"%s"&{col:event_id}),0)'
def CNT_D(op): return DCL % (D_A1, D_A2, D_GP, ER('date'), ER('driver'), ER('sm'), ER('em'), ER('event_id'), op)
def CNT_P(op): return 'IF({col:person}=%s,0,COUNTIFS(%s,{col:date},%s,{col:person},%s,"<"&{col:em},%s,">"&{col:sm},%s,"%s"&{col:event_id}))' % (PWH, ER('date'), ER('person'), ER('sm'), ER('em'), ER('event_id'), op)
tables.append(T('events', 'Family calendar', 'Family calendar: events, drivers and conflicts',
    'One row per event: date, person, kind, title, times, place, driver and carpool. Minutes, the work pattern, adults free and the double-booking checks fill in.', [
    C('event_id', 'Event ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('end_date', 'End date', 'date', 11), LST('person', 'Person', 'epeople', 15), LST('kind', 'Kind', 'ekind', 12),
    C('title', 'Title', 'text', 28), C('start', 'Start', 'time', 8), C('end', 'End', 'time', 8), C('place', 'Place', 'text', 18), LST('driver', 'Driver', 'driver', 15), C('carpool', 'Carpool', 'bool', 8),
    CA('minutes', 'Minutes', 'int', EG('ROUND(({col:end}-{col:start})*1440,0)'), 8), CA('sm', 'Start minute of the day', 'int', EG('ROUND({col:start}*1440,0)'), 9), CA('em', 'End minute of the day', 'int', EG('ROUND({col:end}*1440,0)'), 9),
    CA('dclash', 'Driver double-booked with a later event', 'int', EG(CNT_D('>')), 10), CA('pclash', 'Person double-booked with a later event', 'int', EG(CNT_P('>')), 10),
    CA('conf', 'First event of a conflict, 1 or 0', 'int', EG('IF({col:dclash}+{col:pclash}>0,1,0)'), 9),
    CA('bk', 'Key of the second event', 'text', EG('IF(%s>0,{col:date}&"|1|"&{col:driver},IF(%s>0,{col:date}&"|2|"&{col:person},""))' % (CNT_D('<'), CNT_P('<'))), 16),
    CA('ckey', 'Conflict order key', 'int', EG('IF(AND({col:conf}=1,{col:date}>={today}),({col:date}-{today})*10000000+{col:sm}*2000+MATCH({col:event_id},%s,0),"")' % ER('event_id')), 14),
    CA('free', 'Adults free that evening', 'int', EG('IFERROR(INDEX(%s,MATCH({col:date},%s,0)),"")' % (SR('adults_free'), SR('date'))), 9),
    CA('shift', 'Adult 2 shift', 'text', EG('IFERROR(INDEX(%s,MATCH({col:date},%s,0))&"","")' % (SR('adult2_shift'), SR('date'))), 9),
    CA('lift', 'Driver set, next 14 days, 1 or 0', 'int', EG('IF(AND(OR({col:kind}=%s,{col:kind}=%s,{col:kind}=%s),{col:date}>={today},{col:date}<={today}+13),IF({col:driver}="",0,1),"")' % (K_ACT, K_APPT, K_TRIP)), 10),
    CA('next_date', 'Same day next week', 'date', EG('{col:date}+7'), 11)] +
    CT('Adult 1', 'a1_') + CT('Adult 2', 'a2_') + [CNAME(1, 'c1_name'), CPHONE(1, 'c1_phone'), CNAME(2, 'c2_name'), CPHONE(2, 'c2_phone')] + CT('Grandparent', 'gp_') + CT('Babysitter', 'bs_') + CT('Carpool family', 'cp_') + CT('Dog walker', 'dw_') + [HOUSE()],
    D.events_d(), 1000, [A('conf', '= 1', 'bad'), A('driver', '= ' + D_CP, 'warn')]))
for _c in tables[-1]['columns']:
    if _c['key'] in ('a1_n', 'a2_n', 'gp_n', 'bs_n', 'cp_n', 'dw_n'): _c['key'] = _c['key'][:-2] + '_name'
    if _c['key'] in ('a1_p', 'a2_p', 'gp_p', 'bs_p', 'cp_p', 'dw_p'): _c['key'] = _c['key'][:-2] + '_phone'

# 3 work pattern ----------------------------------------------------------------
def SG(x): return G('shift_id', x)
tables.append(T('shifts', 'Work pattern', 'Work pattern: adult 1 late days and adult 2 shifts',
    'One row per day: adult 1 late (Tuesday and Thursday), adult 2 shift (Early, Late or Off) and the adults free for the evening; events, evening events and child-care gaps fill in.', [
    C('shift_id', 'Shift ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('weekday', 'Weekday', 'wday', 11), C('adult1_late', 'Adult 1 late', 'bool', 8), LST('adult2_shift', 'Adult 2 shift', 'shift', 10),
    C('adults_free', 'Adults free for the evening', 'int', 9),
    CA('wk', 'Week starting', 'date', SG(WSD('{col:date}')), 11), CA('events_n', 'Events starting that day', 'int', SG('COUNTIFS(%s,{col:date})' % ER('date')), 9),
    CA('busy_n', 'Events covering that day', 'int', SG('COUNTIFS(%s,"<="&{col:date},%s,">="&{col:date})' % (ER('date'), ER('end_date'))), 9),
    CA('evening_n', 'Evening events', 'int', SG('COUNTIFS(%s,{col:date},%s,">="&{set:evening_hour}*60)' % (ER('date'), ER('sm'))), 9),
    CA('in_break', 'In a school break, 1 or 0', 'int', SG('IF(COUNTIFS(%s,%s,%s,"<="&{col:date},%s,">="&{col:date})>0,1,0)' % (TR('kind'), T_BREAK, TR('start'), TR('end'))), 9),
    CA('gap', 'Child-care gap day, 1 or 0', 'int', SG('IF(AND({col:in_break}=1,{col:busy_n}=0,{col:weekday}<>%s,{col:weekday}<>%s),1,0)' % (SAT, SUN)), 9),
    CA('free_label', 'Evening', 'text', SG('IF({col:adults_free}=2,%s,IF({col:adults_free}=1,%s,%s))' % (lbl('Both adults free'), lbl('One adult free'), lbl('No adult free'))), 16),
    CA('both_date', 'Date when both adults are free', 'date', SG('IF({col:adults_free}=2,{col:date},"")'), 11),
    CA('m_events', 'Events in the month', 'int', SG('COUNTIFS(%s,">="&DATE(YEAR({col:date}),MONTH({col:date}),1),%s,"<"&EDATE(DATE(YEAR({col:date}),MONTH({col:date}),1),1))' % (ER('date'), ER('date'))), 9),
    NAME('Babysitter', 'bs_name'), PHONE('Babysitter', 'bs_phone'), HOUSE()], D.shifts_d(), 800, [A('adults_free', '= 0', 'warn'), A('gap', '= 1', 'warn')]))

# 4 school terms ----------------------------------------------------------------
def TG(x): return G('term_id', x)
LEFT = ('IF({col:kind}<>%s,0,IF({col:end}<{today},0,MAX(0,NETWORKDAYS(MAX({today},{col:start}),{col:end})-SUMIFS(%s,%s,%s,%s,">="&MAX({today},{col:start}),%s,"<="&{col:end}))))'
        % (T_TERM, TR('wdays'), TR('kind'), T_BREAK, TR('start'), TR('end')))
tables.append(T('terms', 'School terms', 'School terms and breaks',
    'One row per term or break: name, kind, start, end and days. Weekdays, school days (term weekdays less breaks inside it), school days left and the child-care gap days fill in.', [
    C('term_id', 'Term ID', 'text', 9, required=True), LST('term', 'Term', 'tname', 16), LST('kind', 'Term or break', 'tkind', 12), C('start', 'Start', 'date', 11), C('end', 'End', 'date', 11), C('days', 'Days', 'int', 8),
    CA('wdays', 'Weekdays', 'int', TG('NETWORKDAYS({col:start},{col:end})'), 9),
    CA('school_days', 'School days', 'int', TG('IF({col:kind}=%s,{col:wdays}-SUMIFS(%s,%s,%s,%s,">="&{col:start},%s,"<="&{col:end}),0)' % (T_TERM, TR('wdays'), TR('kind'), T_BREAK, TR('start'), TR('end'))), 9),
    CA('cur', 'Current term, 1 or 0', 'int', TG('IF(AND({col:kind}=%s,{col:start}<={today},{col:end}>={today}),1,0)' % T_TERM), 9),
    CA('left_days', 'School days left', 'int', TG(LEFT), 9), CA('bk', 'Start of a future break', 'date', TG('IF(AND({col:kind}=%s,{col:start}>{today}),{col:start},"")' % T_BREAK), 11),
    CA('upc', 'Start if not over', 'date', TG('IF({col:end}>={today},{col:start},"")'), 11),
    CA('gap_days', 'Child-care gap days', 'int', TG('IF({col:kind}=%s,SUMIFS(%s,%s,">="&{col:start},%s,"<="&{col:end}),"")' % (T_BREAK, SR('gap'), SR('date'), SR('date'))), 9),
    CA('sumend', 'End of the summer term', 'date', TG('IF(AND({col:term}=%s,{col:end}>={today}),{col:end},"")' % TN_SUMMER), 11),
    CA('to_start', 'Days to the start', 'int', TG('MAX(0,{col:start}-{today})'), 9)], D.terms_d(), 60, [A('cur', '= 1', 'good')]))

# 5 gifts -----------------------------------------------------------------------
def GG(x): return G('gift_id', x)
tables.append(T('gifts', 'Birthdays and gifts', 'Birthdays and gift list',
    'One row per birthday or gift date: first name, relation, the next date, age turning, gift idea, status (idea, bought, wrapped, given) and a cost line. Days left and the gift window fill in.', [
    C('gift_id', 'Gift ID', 'text', 9, required=True), C('name', 'Name', 'text', 20), C('relation', 'Relation', 'text', 13), C('date', 'Date', 'date', 11), C('age_turning', 'Age turning', 'int', 8),
    C('gift_idea', 'Gift idea', 'text', 22), LST('status', 'Status', 'gstatus', 10), C('cost', 'Cost line', 'money', 11),
    CA('days_left', 'Days left', 'int', GG('{col:date}-{today}'), 8), CA('in_win', 'In the gift window, 1 or 0', 'int', GG('IF(AND({col:date}>={today},{col:date}<={today}+{set:gift_days}),1,0)'), 9),
    CA('rk', 'Order key, date then row number', 'int', GG('IF({col:in_win}=1,{col:date}*100+MATCH({col:gift_id},%s,0),"")' % GR_('gift_id')), 12),
    CA('bw', 'Bought, wrapped or given, 1 or 0', 'int', GG('IF({col:status}=%s,0,1)' % G_IDEA), 9), CA('buy_by', 'Buy by', 'date', GG('{col:date}-{set:soon_days}'), 11)], D.gifts_d(), 60, [A('status', '= ' + G_IDEA, 'warn'), A('status', '= ' + G_WRAP, 'good')]))

# 6 pets and 7 pet care ---------------------------------------------------------
tables.append(T('pets', 'Pets', 'Pets: name and species',
    'One row per pet: a name and the species. Pet food and the care schedule read these rows; a household without pets leaves them empty. Dates only, no health details.', [
    C('pet_id', 'Pet ID', 'text', 9, required=True), C('pet', 'Pet', 'text', 14), C('species', 'Species', 'text', 12)], D.pets_d(), 50))
LASTBAG = ('IF({col:task}=%s,IF({col:date}<={today},IF({col:date}=SUMPRODUCT(MAX((%s={col:pet})*(%s=%s)*(%s<={today})*%s)),1,0),0),0)' % (PT_FOOD, PCR('pet'), PCR('task'), PT_FOOD, PCR('date'), PCR('date')))
tables.append(T('pet_care', 'Pet care log', 'Pet care log: grooming, vet dates, food bags',
    'One row per care date: pet, date, task, bag size, cost line and whether it is booked in the future; dates only, no treatments. The latest food bag of each pet is found.', [
    C('care_id', 'Care ID', 'text', 10, required=True), REF('pet_id', 'Pet ID', 'pets.pet_id', 9), REF('pet', 'Pet', 'pets.pet', 12), C('date', 'Date', 'date', 11), LST('task', 'Task', 'ptask', 17),
    C('qty_kg', 'Bag size, kg', 'num', 9), C('cost', 'Cost line', 'money', 10), C('booked', 'Booked', 'bool', 8), CA('last_bag', 'Latest food bag, 1 or 0', 'int', G('care_id', LASTBAG), 9)],
    D.pet_care_d(), 300, [A('booked', '= ' + YES, 'good'), A('last_bag', '= 1', 'warn')]))

# 8 vehicles and 9 vehicle log --------------------------------------------------
tables.append(T('vehicles', 'Vehicles', 'Vehicles: name and year',
    'One row per vehicle: a name and the year. Vehicle dates and the service estimate read these rows; a household without a vehicle leaves them empty.', [
    C('vehicle_id', 'Vehicle ID', 'text', 10, required=True), C('vehicle', 'Vehicle', 'text', 20), C('year', 'Year', 'int', 8)], D.vehicles_d(), 50))
def LATEST(kind, upto='{today}'):
    return 'SUMPRODUCT(MAX((%s={col:vehicle})*(%s=%s)*(%s<=%s)*%s))' % (VLR('vehicle'), VLR('kind'), kind, VLR('date'), upto, VLR('date'))
OLDD = LATEST(VK_MR, '{col:date}-150')
OLDK = 'SUMPRODUCT(MAX((%s={col:vehicle})*(%s=%s)*(%s=%s)*%s))' % (VLR('vehicle'), VLR('kind'), VK_MR, VLR('date'), OLDD, VLR('km'))
tables.append(T('vehicle_log', 'Vehicle log', 'Vehicle log: service, tyres, tests, renewals, mileage',
    'One row per entry: vehicle, date, kind (service, tyres, annual test, insurance, registration, repair, mileage reading), odometer km, cost line and who. The latest reading and service are found.', [
    C('log_id', 'Log ID', 'text', 10, required=True), REF('vehicle_id', 'Vehicle ID', 'vehicles.vehicle_id', 10), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 18), C('date', 'Date', 'date', 11), LST('kind', 'Kind', 'vkind', 18),
    C('km', 'Odometer, km', 'int', 10), C('cost', 'Cost line', 'money', 10), C('who', 'Who', 'text', 14),
    CA('lm', 'Latest mileage reading, 1 or 0', 'int', G('log_id', 'IF({col:kind}=%s,IF({col:date}=%s,1,0),0)' % (VK_MR, LATEST(VK_MR))), 9),
    CA('ls', 'Latest service, 1 or 0', 'int', G('log_id', 'IF({col:kind}=%s,IF({col:date}=%s,1,0),0)' % (VK_SERVICE, LATEST(VK_SERVICE))), 9),
    CA('rate', 'Km per day since a reading 150 days ago', 'num', G('log_id', 'IF({col:lm}=1,IF(%s=0,"",ROUND(({col:km}-%s)/({col:date}-%s),1)),"")' % (OLDD, OLDK, OLDD)), 10)], D.vehicle_log_d(), 200, [A('lm', '= 1', 'good')]))

# 10 maintenance due dates ------------------------------------------------------
def MG(x): return G('task_id', x)
tables.append(T('tasks', 'Maintenance due dates', 'Maintenance tasks with the next due date',
    'One row per maintenance task: area, who does it, the interval (typical, check the manual) and when it was last done; next due, days left and the status fill in. The busiest-week check counts them.', [
    C('task_id', 'Task ID', 'text', 9, required=True), C('task', 'Task', 'text', 32), C('area', 'Area', 'text', 20), C('assigned', 'Assigned to', 'text', 14), C('interval_days', 'Interval, days', 'int', 9), C('last_done', 'Last done', 'date', 11),
    CA('next_due', 'Next due', 'date', MG('IF({col:last_done}="","",{col:last_done}+{col:interval_days})'), 11), CA('days_left', 'Days left', 'int', MG('IF({col:next_due}="","",{col:next_due}-{today})'), 8),
    CA('status', 'Status', 'text', MG('IF({col:days_left}="","",IF({col:days_left}<0,%s,IF({col:days_left}<={set:soon_days},%s,%s)))' % (W_OVD, W_SOON, W_OK)), 10)], D.tasks_d(), 100,
    [A('status', '= ' + W_OVD, 'bad'), A('status', '= ' + W_SOON, 'warn'), A('status', '= ' + W_OK, 'good')]))

# 11 conflict finder ------------------------------------------------------------
def CF(c): return 'INDEX(%s,{col:pos})' % ER(c)
def CB(c): return 'INDEX(%s,{col:bpos})' % ER(c)
def KG(x): return 'IF({col:pos}="","",%s)' % x
tables.append(T('conflicts', 'Conflict finder', 'Conflict finder: double-booked drivers and people',
    'Type 1 to 40 once. Upcoming events that overlap for the same driver or the same person fall in date order with both events, the overlap in minutes and the adults free from the work pattern.', [
    C('no', 'Rank', 'int', 7, required=True), CA('pos', 'First event row', 'int', 'IFERROR(MATCH(SMALL(%s,{col:no}),%s,0),"")' % (ER('ckey'), ER('ckey')), 8),
    CA('bpos', 'Second event row', 'int', KG('IFERROR(MATCH(IF(%s>0,%s&"|1|"&%s,%s&"|2|"&%s),%s,0),"")' % (CF('dclash'), CF('date'), CF('driver'), CF('date'), CF('person'), ER('bk'))), 8),
    CA('date', 'Date', 'date', KG(CF('date')), 11), CA('days_to', 'Days to it', 'int', KG('{col:date}-{today}'), 8), CA('weekday', 'Weekday', 'text', KG('CHOOSE(WEEKDAY({col:date},2),%s)' % WDAYS7), 11),
    CA('type', 'Kind of conflict', 'text', KG('IF(%s>0,%s,%s)' % (CF('dclash'), lbl('Driver double-booked'), lbl('Person double-booked'))), 20),
    CA('who', 'Driver or person', 'text', KG('IF(%s>0,%s,%s)&""' % (CF('dclash'), CF('driver'), CF('person'))), 15),
    CA('event_a', 'First event', 'text', KG(CF('title')), 24), CA('a_start', 'Starts', 'time', KG(CF('start')), 8), CA('event_b', 'Second event', 'text', KG('IF({col:bpos}="","",%s)' % CB('title')), 24), CA('b_start', 'Starts', 'time', KG('IF({col:bpos}="","",%s)' % CB('start')), 8),
    CA('overlap', 'Overlap, minutes', 'int', KG('IF({col:bpos}="","",MIN(%s,%s)-MAX(%s,%s))' % (CF('em'), CB('em'), CF('sm'), CB('sm'))), 9), CA('free', 'Adults free', 'int', KG(CF('free')), 8),
    CA('advice', 'What to do', 'text', KG('IF({col:free}>=2,%s,IF({col:free}=1,%s,%s))' % (lbl('Share the lifts'), lbl('Find a second driver'), lbl('No adult free, ask for help'))), 24)] +
    CT('Adult 2', 'a2_') + CT('Carpool family', 'cp_') + [HOUSE()], D.nums(40), 60, [A('free', '= 1', 'warn'), A('free', '= 0', 'bad')]))
for _c in tables[-1]['columns']:
    if _c['key'] in ('a2_n', 'cp_n'): _c['key'] = _c['key'][:-2] + '_name'
    if _c['key'] in ('a2_p', 'cp_p'): _c['key'] = _c['key'][:-2] + '_phone'

# 12 busiest week ahead ---------------------------------------------------------
BWS = '({col:week_start})'
ESUM = 'COUNTIFS(%s,">="&{col:week_start},%s,"<"&({col:week_start}+7))' % (ER('date'), ER('date'))
TSUM = 'IF({col:no}=1,COUNTIFS(%s,"<"&({col:week_start}+7)),COUNTIFS(%s,">="&{col:week_start},%s,"<"&({col:week_start}+7)))' % (MR('next_due'), MR('next_due'), MR('next_due'))
def BG(x): return G('no', x)
tables.append(T('busy', 'Busiest week ahead', 'Busiest week ahead: events and tasks per week',
    'Type 1 to 12 once with the week label. Events and maintenance tasks due are counted for each of the next 12 weeks (week 1 also holds overdue tasks), with the busiest and quietest week ranked.', [
    C('no', 'Week number', 'int', 8, required=True), LST('wk', 'Week', 'wk12', 10), CA('week_start', 'Week starting', 'date', BG(WS + '+7*({col:no}-1)'), 11), CA('events', 'Events', 'int', BG(ESUM), 8),
    CA('tasks', 'Maintenance tasks due', 'int', BG(TSUM), 9), CA('total', 'Total items', 'int', BG('{col:events}+{col:tasks}'), 8),
    CA('rank', 'Rank, 1 is the busiest', 'int', BG('1+COUNTIFS(%s,">"&{col:total})+COUNTIFS(%s,{col:total},%s,"<"&{col:no})' % (BR('total'), BR('total'), BR('no'))), 9),
    CA('evenings', 'Evening events', 'int', BG('COUNTIFS(%s,">="&{col:week_start},%s,"<"&({col:week_start}+7),%s,">="&{set:evening_hour}*60)' % (ER('date'), ER('date'), ER('sm'))), 9),
    CA('carpools', 'Carpool lifts', 'int', BG('COUNTIFS(%s,">="&{col:week_start},%s,"<"&({col:week_start}+7),%s,%s)' % (ER('date'), ER('date'), ER('carpool'), YES)), 9),
    CA('level', 'Level against the 12-week average', 'text', BG('IF({col:total}>=1.25*AVERAGE(%s),%s,IF({col:total}<=0.75*AVERAGE(%s),%s,%s))' % (BR('total'), lbl('Busy'), BR('total'), lbl('Quiet'), lbl('Normal'))), 14)] +
    CT('Adult 1', 'a1_') + CT('Adult 2', 'a2_') + CT('Babysitter', 'bs_') + CT('Neighbour', 'nb_') + [CNAME(1, 'c1_name'), CNAME(2, 'c2_name'), HOUSE()], D.busy_d(), 50,
    [A('level', '= ' + lbl('Busy'), 'warn'), A('level', '= ' + lbl('Quiet'), 'good')]))
for _c in tables[-1]['columns']:
    if _c['key'].endswith('_n') and _c['key'][:3] in ('a1_', 'a2_', 'bs_', 'nb_'): _c['key'] = _c['key'][:-2] + '_name'
    elif _c['key'].endswith('_p') and _c['key'][:3] in ('a1_', 'a2_', 'bs_', 'nb_'): _c['key'] = _c['key'][:-2] + '_phone'

# 13 driving load by adult ------------------------------------------------------
def DG(x): return G('no', x)
TRIPS = 'COUNTIFS(%s,{col:adult},%s,">="&{col:week_start},%s,"<"&({col:week_start}+7))' % (ER('driver'), ER('date'), ER('date'))
AG = 'IF({col:adult}=%s,{set:agreed_drive_share},1-{set:agreed_drive_share})' % tok('adult', 'Adult 2')
T4 = 'SUMIFS(%s,%s,{col:adult},%s,">="&{col:weeks_ago},%s,"<"&({col:weeks_ago}+4))' % (DR('trips'), DR('adult'), DR('weeks_ago'), DR('weeks_ago'))
A4 = 'SUMIFS(%s,%s,">="&{col:weeks_ago},%s,"<"&({col:weeks_ago}+4))' % (DR('trips'), DR('weeks_ago'), DR('weeks_ago'))
tables.append(T('driving', 'Driving load by adult', 'Driving load by adult: trips and minutes per week',
    'Type 1 to 24 once with the weeks ago and the adult. Trips and event minutes driven, the share of the week and a rolling 4-week share fill in; a view for a talk, not a score.', [
    C('no', 'Row', 'int', 6, required=True), C('weeks_ago', 'Weeks ago, 1 to 12', 'int', 9), LST('adult', 'Adult', 'adult', 10),
    CA('week_start', 'Week starting', 'date', DG(WS + '-7*{col:weeks_ago}'), 11), CA('trips', 'Trips driven', 'int', DG(TRIPS), 8),
    CA('minutes', 'Event minutes driven', 'int', DG('SUMIFS(%s,%s,{col:adult},%s,">="&{col:week_start},%s,"<"&({col:week_start}+7))' % (ER('minutes'), ER('driver'), ER('date'), ER('date'))), 10),
    CA('all', 'Trips driven by both adults', 'int', DG('SUMIFS(%s,%s,{col:weeks_ago})' % (DR('trips'), DR('weeks_ago'))), 9),
    CA('share', 'Share of the week trips', 'pct', DG('IF({col:all}=0,"",{col:trips}/{col:all})'), 9),
    CA('within', 'Within the agreed margin, 1 or 0', 'int', DG('IF({col:share}="","",IF(ABS({col:share}-%s)<={set:fair_margin},1,0))' % AG), 10),
    CA('wk_conf', 'Driver conflicts that week', 'int', DG('COUNTIFS(%s,">0",%s,">="&{col:week_start},%s,"<"&({col:week_start}+7))' % (ER('dclash'), ER('date'), ER('date'))), 9),
    CA('share4', 'Share of the 4 weeks to this one', 'pct', DG('IF(%s=0,"",%s/%s)' % (A4, T4, A4)), 10),
    CA('share4_txt', 'Share of the 4 weeks, in words', 'text', DG('IF({col:share4}="","",ROUND({col:share4}*100,0)&"%")'), 10)] + CT('Adult 1', 'a1_') + [HOUSE()], D.driving_d(), 50,
    [A('within', '= 0', 'warn')]))
for _c in tables[-1]['columns']:
    if _c['key'] == 'a1_n': _c['key'] = 'a1_name'
    if _c['key'] == 'a1_p': _c['key'] = 'a1_phone'

# 14 school days and breaks -----------------------------------------------------
def VG(c): return 'IF({col:pos}="","",INDEX(%s,{col:pos}))' % TR(c)
tables.append(T('school_view', 'School days and breaks', 'School days and breaks: what is next',
    'Type 1 to 14 once. The terms and breaks not yet over appear in date order with the days to the start, the school days left and the child-care gap days of each break.', [
    C('no', 'Row', 'int', 6, required=True), CA('pos', 'Row in School terms', 'int', 'IFERROR(MATCH(SMALL(%s,{col:no}),%s,0),"")' % (TR('upc'), TR('upc')), 8),
    CA('term', 'Term', 'text', VG('term') + '&""' if False else 'IF({col:pos}="","",INDEX(%s,{col:pos})&"")' % TR('term'), 16), CA('kind', 'Term or break', 'text', 'IF({col:pos}="","",INDEX(%s,{col:pos})&"")' % TR('kind'), 12),
    CA('start', 'Start', 'date', VG('start'), 11), CA('end', 'End', 'date', VG('end'), 11), CA('to_start', 'Days to the start', 'int', VG('to_start'), 9),
    CA('left_days', 'School days left', 'int', 'IF({col:pos}="","",IF({col:kind}=%s,INDEX(%s,{col:pos}),""))' % (T_TERM, TR('left_days')), 9),
    CA('gap_days', 'Child-care gap days', 'int', 'IF({col:pos}="","",IF({col:kind}=%s,INDEX(%s,{col:pos}),""))' % (T_BREAK, TR('gap_days')), 9),
    CA('trip_date', 'Family trip', 'date', 'IF({col:pos}="","",{set:trip_date})', 11), CA('trip_end', 'Back from the trip', 'date', 'IF({col:pos}="","",{set:trip_date}+{set:trip_days}-1)', 11),
    CA('check_by', 'Check travel documents by', 'date', 'IF({col:pos}="","",{set:trip_date}-60)', 11)] +
    CT('School office', 'so_') + CT('Adult 2', 'a2_') + CT('Neighbour', 'nb_') + [CNAME(1, 'c1_name'), CNAME(2, 'c2_name'), HOUSE()], D.nums(14), 50, [A('gap_days', '> 0', 'warn')]))
for _c in tables[-1]['columns']:
    if _c['key'].endswith('_n') and _c['key'][:3] in ('so_', 'a2_', 'nb_'): _c['key'] = _c['key'][:-2] + '_name'
    elif _c['key'].endswith('_p') and _c['key'][:3] in ('so_', 'a2_', 'nb_'): _c['key'] = _c['key'][:-2] + '_phone'

# 15 gift planner ---------------------------------------------------------------
def PG(c): return 'IF({col:pos}="","",INDEX(%s,{col:pos}))' % GR_(c)
tables.append(T('gift_plan', 'Gift planner next 60 days', 'Gift planner: the dates of the next 60 days',
    'Type 1 to 16 once. Birthdays and gift dates inside the gift window appear in date order with days left, the idea, the status, the cost line, the buy-by date and the next step.', [
    C('no', 'Row', 'int', 6, required=True), CA('pos', 'Row in Birthdays and gifts', 'int', 'IFERROR(MATCH(SMALL(%s,{col:no}),%s,0),"")' % (GR_('rk'), GR_('rk')), 8),
    CA('name', 'Name', 'text', 'IF({col:pos}="","",INDEX(%s,{col:pos})&"")' % GR_('name'), 20), CA('date', 'Date', 'date', PG('date'), 11), CA('days_left', 'Days left', 'int', PG('days_left'), 8),
    CA('gift_idea', 'Gift idea', 'text', 'IF({col:pos}="","",INDEX(%s,{col:pos})&"")' % GR_('gift_idea'), 22), CA('status', 'Status', 'text', 'IF({col:pos}="","",INDEX(%s,{col:pos})&"")' % GR_('status'), 10),
    CA('cost', 'Cost line', 'money', PG('cost'), 10), CA('buy_by', 'Buy by', 'date', PG('buy_by'), 11),
    CA('step', 'Next step', 'text', 'IF({col:pos}="","",IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:status}=%s,%s,%s))))' % (G_GIVEN, lbl('Done'), G_WRAP, lbl('Give it on the day'), G_BOUGHT, lbl('Wrap it'), lbl('Choose and buy')), 18)] +
    [CNAME(1, 'c1_name'), CPHONE(1, 'c1_phone')] + CT('Adult 1', 'a1_') + [HOUSE()], D.nums(16), 50, [A('step', '= ' + lbl('Choose and buy'), 'warn')]))
for _c in tables[-1]['columns']:
    if _c['key'] == 'a1_n': _c['key'] = 'a1_name'
    if _c['key'] == 'a1_p': _c['key'] = 'a1_phone'

# 16 visitors and stays ---------------------------------------------------------
def VS(x): return G('visitor', x)
ATARR = 'SUMIFS(%s,%s,"<="&{col:arrive},%s,">"&{col:arrive})' % (VSR('beds'), VSR('arrive'), VSR('leave'))
tables.append(T('visitors', 'Visitors and stays', 'Visitors and stays: dates, beds and clashes',
    'One row per stay: visitor, arrive, leave, beds, room and phone. Nights, dinners to add, beds in use on arrival against the beds typed, and overlapping stays fill in.', [
    C('visitor', 'Visitor', 'text', 20, required=True), C('arrive', 'Arrive', 'date', 11), C('leave', 'Leave', 'date', 11), C('beds', 'Beds needed', 'int', 8), LST('room', 'Room', 'stayroom', 22), C('phone', 'Phone', 'text', 18),
    CA('nights', 'Nights', 'int', VS('{col:leave}-{col:arrive}'), 7), CA('dinners', 'Dinners to add', 'int', VS('{col:beds}*{col:nights}'), 9), CA('at_arr', 'Beds in use on arrival', 'int', VS(ATARR), 9),
    CA('over_by', 'Over the beds typed by', 'int', VS('MAX(0,{col:at_arr}-{set:beds_total})'), 9),
    CA('clash_n', 'Other stays overlapping', 'int', VS('COUNTIFS(%s,"<"&{col:leave},%s,">"&{col:arrive})-1' % (VSR('arrive'), VSR('leave'))), 9),
    CA('status', 'Beds check', 'text', VS('IF({col:over_by}>0,%s,IF({col:clash_n}>0,%s,%s))' % (lbl('Over the beds typed'), lbl('Dates overlap, beds fit'), lbl('Fits'))), 20),
    CA('to_arrive', 'Days to the arrival', 'int', VS('{col:arrive}-{today}'), 9)] + CT('Grandparent', 'gp_') + [HOUSE()], D.visitors_d(), 60,
    [A('status', '= ' + lbl('Over the beds typed'), 'bad'), A('status', '= ' + lbl('Dates overlap, beds fit'), 'warn')]))
for _c in tables[-1]['columns']:
    if _c['key'] == 'gp_n': _c['key'] = 'gp_name'
    if _c['key'] == 'gp_p': _c['key'] = 'gp_phone'

# 17 pet care schedule ----------------------------------------------------------
def PS(x): return G('ps_id', x)
SPL = 'SUMPRODUCT(MAX((%s={col:pet})*(%s={col:task})*(%s<={today})*%s))' % (PCR('pet'), PCR('task'), PCR('date'), PCR('date'))
SPB = 'SUMPRODUCT(MAX((%s={col:pet})*(%s={col:task})*(%s>={today})*(100000-%s)))' % (PCR('pet'), PCR('task'), PCR('date'), PCR('date'))
tables.append(T('pet_sched', 'Pet care schedule', 'Pet care schedule: next dates, dates only',
    'One row per pet and task: the interval you type (typical), the last date from the Pet care log, a booked future date and the next due with days left. Dates only, no health details.', [
    C('ps_id', 'Row ID', 'text', 9, required=True), REF('pet', 'Pet', 'pets.pet', 12), LST('task', 'Task', 'ptask', 17), C('interval_days', 'Interval, days', 'int', 9), C('at', 'Visit time', 'time', 8),
    CA('last_done', 'Last done', 'date', PS('IF(%s=0,"",%s)' % (SPL, SPL)), 11), CA('booked', 'Booked date', 'date', PS('IF(%s=0,"",100000-%s)' % (SPB, SPB)), 11),
    CA('next_due', 'Next due', 'date', PS('IF({col:booked}<>"",{col:booked},IF({col:last_done}<>"",{col:last_done}+{col:interval_days},""))'), 11),
    CA('days_left', 'Days left', 'int', PS('IF({col:next_due}="","",{col:next_due}-{today})'), 8),
    CA('status', 'Status', 'text', PS('IF({col:days_left}="",%s,IF({col:days_left}<0,%s,IF({col:days_left}<={set:soon_days},%s,%s)))' % (W_NODATE, W_OVD, W_SOON, W_OK)), 12),
    CA('vetd', 'Vet visit, days left', 'int', PS('IF({col:task}=%s,{col:days_left},"")' % PT_VET), 9),
    CA('pk', 'Pet and task', 'text', PS('{col:pet}&"|"&{col:task}'), 18),
    CA('nk', 'Order key, date then row number', 'int', PS('IF({col:next_due}="","",{col:next_due}*100+MATCH({col:ps_id},%s,0))' % PSR('ps_id')), 12)] + CT('Vet clinic', 'vet_') + [HOUSE()], D.pet_sched_d(), 50,
    [A('status', '= ' + W_OVD, 'bad'), A('status', '= ' + W_SOON, 'warn')]))
for _c in tables[-1]['columns']:
    if _c['key'] == 'vet_n': _c['key'] = 'vet_name'
    if _c['key'] == 'vet_p': _c['key'] = 'vet_phone'

# 18 pet food stock -------------------------------------------------------------
PN = 'IFERROR(INDEX(%s,MATCH({col:pet_id},%s,0))&"","")' % (PR('pet'), PR('pet_id'))
DAILY = 'CHOOSE(MATCH({col:pet_id},%s,0),{set:daily_g_1},{set:daily_g_2},0,0,0)' % PR('pet_id')
BAGKG = 'SUMIFS(%s,%s,%s,%s,1)' % (PCR('qty_kg'), PCR('pet'), PN, PCR('last_bag'))
BAGD = 'SUMIFS(%s,%s,%s,%s,1)' % (PCR('date'), PCR('pet'), PN, PCR('last_bag'))
STOCKDAYS = 'IF(OR(%s="",%s=0,%s=0),"",INT(MAX(0,%s-({today}-%s)*%s/1000)*1000/%s))' % (PN, DAILY, BAGKG, BAGKG, BAGD, DAILY, DAILY)
tables.append(T('pet_food', 'Pet food stock', 'Pet food stock: days left and reorder date',
    'Type the pet IDs once. From the latest food bag in the Pet care log and the daily grams in Settings, the days left and the date to reorder fill in; an empty pet row stays blank.', [
    REF('pet_id', 'Pet ID', 'pets.pet_id', 10, required=True), CA('days_left', 'Days of food left', 'int', STOCKDAYS, 10),
    CA('reorder_date', 'Reorder by', 'date', 'IF({col:days_left}="","",{today}+{col:days_left}-{set:reorder_days})', 11)], D.pet_food_d(), 50, [A('days_left', '<= {set:reorder_days}', 'warn')]))

# 19 vehicle dates --------------------------------------------------------------
def VG2(x): return G('vd_id', x)
SPV = 'SUMPRODUCT(MAX((%s={col:vehicle})*(%s={col:kind})*(%s<={today})*%s))' % (VLR('vehicle'), VLR('kind'), VLR('date'), VLR('date'))
tables.append(T('vehicle_dates', 'Vehicle dates', 'Vehicle dates: service, tyres, test, insurance, registration',
    'One row per vehicle and kind: the interval you type (typical, check the manual); the last date from the Vehicle log, the next date, days left and the status fill in, ranked for the next 90 days.', [
    C('vd_id', 'Row ID', 'text', 9, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 18), LST('kind', 'Kind', 'vkind', 18), C('interval_days', 'Interval, days', 'int', 9),
    CA('last_done', 'Last done', 'date', VG2('IF(%s=0,"",%s)' % (SPV, SPV)), 11), CA('date', 'Next date', 'date', VG2('IF({col:last_done}="","",{col:last_done}+{col:interval_days})'), 11),
    CA('days_left', 'Days left', 'int', VG2('IF({col:date}="","",{col:date}-{today})'), 8),
    CA('status', 'Status', 'text', VG2('IF({col:days_left}="","",IF({col:days_left}<0,%s,IF({col:days_left}<={set:soon_days},%s,%s)))' % (W_OVD, W_SOON, W_OK)), 10),
    CA('rk', 'Order key, days then row number', 'int', VG2('IF({col:days_left}="","",IF({col:days_left}>=0,{col:days_left}*1000+MATCH({col:vd_id},%s,0),""))' % VDR('vd_id')), 10),
    CA('rank', 'Rank, 1 is the soonest', 'int', VG2('IF({col:rk}="","",1+COUNTIFS(%s,"<"&{col:rk}))' % VDR('rk')), 9),
    CA('adt', 'Annual test, days left', 'int', VG2('IF({col:kind}=%s,{col:days_left},"")' % VK_TEST), 9), CA('ins', 'Insurance, days left', 'int', VG2('IF({col:kind}=%s,{col:days_left},"")' % VK_INS), 9),
    CA('reg', 'Registration, days left', 'int', VG2('IF({col:kind}=%s,{col:days_left},"")' % VK_REG), 9),
    CA('km_now', 'Latest reading, km', 'int', VG2('SUMIFS(%s,%s,{col:vehicle},%s,1)' % (VLR('km'), VLR('vehicle'), VLR('lm'))), 9)] + CT('Car mechanic', 'cm_') + [HOUSE()], D.vehicle_dates_d(), 50,
    [A('status', '= ' + W_OVD, 'bad'), A('status', '= ' + W_SOON, 'warn')]))
for _c in tables[-1]['columns']:
    if _c['key'] == 'cm_n': _c['key'] = 'cm_name'
    if _c['key'] == 'cm_p': _c['key'] = 'cm_phone'

# 20 vehicle service estimate ---------------------------------------------------
VN = 'IFERROR(INDEX(%s,MATCH({col:vehicle_id},%s,0))&"","")' % (VR('vehicle'), VR('vehicle_id'))
KNOW = 'SUMIFS(%s,%s,%s,%s,1)' % (VLR('km'), VLR('vehicle'), VN, VLR('lm'))
KSV = 'SUMIFS(%s,%s,%s,%s,1)' % (VLR('km'), VLR('vehicle'), VN, VLR('ls'))
DSV = 'SUMIFS(%s,%s,%s,%s,1)' % (VLR('date'), VLR('vehicle'), VN, VLR('ls'))
RATE = 'SUMIFS(%s,%s,%s,%s,1)' % (VLR('rate'), VLR('vehicle'), VN, VLR('lm'))
tables.append(T('vehicle_est', 'Vehicle service estimate', 'Vehicle service estimate: km left and the date',
    'Type the vehicle IDs once. From the latest service and reading in the Vehicle log, the km to the next service and the estimated date (km or days, whichever comes first; typical, check the manual).', [
    REF('vehicle_id', 'Vehicle ID', 'vehicles.vehicle_id', 10, required=True),
    CA('km_left', 'Km to the next service', 'int', 'IF(OR(%s="",%s=0),"",%s+{set:service_km}-%s)' % (VN, KSV, KSV, KNOW), 11),
    CA('est_date', 'Estimated service date', 'date', 'IF({col:km_left}="","",MIN({today}+IF(%s>0,MAX(0,{col:km_left})/%s,{set:service_days}),%s+{set:service_days}))' % (RATE, RATE, DSV), 12)], D.veh_est_d(), 50, [A('km_left', '< 1500', 'warn')]))
assert len(tables) == 20, len(tables)
