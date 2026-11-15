"""Doula business suite part 5: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du5_lists import *
import du5_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def CO(): return CA('company', 'Business', 'text', '{set:company}', 24)
def OWN(): return CA('owner_phone', 'Owner-doula phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def DPH(): return CA('doula_phone', 'Doula phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:doula},{range:team.name},0))&"","")', 18)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
PRE = tok('vkind', 'Prenatal visit'); PPV = tok('vkind', 'Postpartum visit'); NIGHT = tok('vkind', 'Night shift'); DEB = tok('vkind', 'Debrief visit')
THISMON = '({today}-WEEKDAY({today},2)+1)'
RATE_OF = 'SUMIFS({range:areas.mileage_rate},{range:areas.area},{col:area},{range:areas.in_use},1)'
QTR = lambda c: 'DATE(YEAR(%s),3*INT((MONTH(%s)-1)/3)+1,1)' % (c, c)

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('weekly_hours_cap', 'Most postpartum and birth hours for one doula in a week', 'int', WEEKLY_HOURS_CAP),
    S('weeks_over_warn', 'Weeks over the hours cap in a row before a rest week', 'int', 3), S('min_booking_hours', 'Minimum booking for a postpartum visit, hours', 'int', MIN_BOOKING_HOURS),
    S('over_plan_share', 'Share over the planned hours that flags a client', 'pct', 0.15), S('rest_days_min', 'Fewest rest days a doula needs between two births', 'int', 3),
    S('births_quarter_max', 'Most births the agency attends in a quarter', 'int', 18), S('extra_hour_rate', 'Rate for extra hours beyond a pack, per hour', 'money', 40),
    S('mileage_share_max', 'Highest mileage cost as a share of the package price', 'pct', 0.05), S('call_arrival_max', 'Longest wanted time from the call to arrival, minutes', 'int', 75),
    S('night_max', 'Most night calls and night shifts for one doula in 30 days', 'int', 3), S('pack_warn_days', 'Days before a pack ends that count as ending soon', 'int', 30),
    S('short_share_max', 'Highest share of postpartum visits below the minimum', 'pct', 0.10),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 visits
tables.append(T('visits', 'Visits', 'Visit Log: prenatal, postpartum, night and debrief visits',
    'One row per visit: date, start time, client, doula, kind, hours, miles and area; the week, month, mileage cost and the short and complete checks fill in by themselves.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('time', 'Start time', 'time', 8), REF('client', 'Client', 'clients.client', 22), LST('doula', 'Doula', 'doula', 17), LST('kind', 'Kind', 'vkind', 16),
    C('hours', 'Hours', 'num', 8), C('miles', 'Miles', 'num', 8), LST('area', 'Area', 'area', 11),
    CA('week', 'Week', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('weekday', 'Weekday', 'int', 'WEEKDAY({col:date},2)', 8), CA('mileage_cost', 'Mileage cost', 'money', 'ROUND({col:miles}*%s,2)' % RATE_OF, 11),
    CA('short', 'Below minimum', 'int', 'IF(AND({col:kind}=%s,{col:hours}<{set:min_booking_hours}),1,0)' % PPV, 9),
    CA('complete', 'Log complete', 'int', 'IF(AND({col:hours}>0,{col:miles}>0),1,0)', 9), CA('this_month', 'This month', 'int', 'IF({col:month}=%s,1,0)' % MS, 8)],
    D.visits_d(), 2400, [A('short', '= 1', 'warn'), A('complete', '= 0', 'bad')]))
# ---------------------------------------------------------------- 2 births
tables.append(T('births', 'Births Attended', 'Birth Log: call, arrival and leave times, hours and miles',
    'One row per birth attended: date, client, the doula who attended and the assigned doula, call, arrival and leave times, hours, miles and area (times and hours only, no detail); the minutes to arrive, night call and mileage fill in.', [
    C('birth_id', 'Birth ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('client', 'Client', 'clients.client', 22), LST('doula', 'Doula who attended', 'attender', 17), LST('assigned', 'Assigned doula', 'doula', 17),
    C('backup_used', 'Backup used', 'bool', 8), C('call_time', 'Call time', 'time', 8), C('arrive_time', 'Arrival time', 'time', 8), C('leave_time', 'Leave time', 'time', 8), C('hours', 'Hours', 'num', 8),
    C('miles', 'Miles', 'num', 8), LST('area', 'Area', 'area', 11), C('on_call_day', 'On-call day', 'int', 8),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('week', 'Week', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 11), CA('qtr', 'Quarter starting', 'date', QTR('{col:date}'), 11),
    CA('package', 'Package', 'text', LKT('clients.package', 'clients.client', 'client'), 22), CA('plan_hours', 'Planned birth hours', 'num', LKN('packages.birth_hours', 'packages.package', 'package'), 10),
    CA('call_hour', 'Call hour', 'int', 'INT(ROUND({col:call_time}*1440,0)/60)', 8), CA('arrive_min', 'Minutes to arrive', 'int', 'ROUND(MOD({col:arrive_time}-{col:call_time},1)*1440,0)', 9),
    CA('night_call', 'Night call', 'int', 'IF(OR({col:call_hour}>=22,{col:call_hour}<6),1,0)', 8), CA('mileage_cost', 'Mileage cost', 'money', 'ROUND({col:miles}*%s,2)' % RATE_OF, 11), DPH(), CO()],
    D.births_d(), 400, [A('backup_used', '= ' + YES, 'warn')]))
# ---------------------------------------------------------------- 3 hour packs
tables.append(T('packs', 'Hour Packs', 'Hour packs bought: hours, price, expiry and hours used',
    'One row per postpartum hour pack (a set number of postpartum hours bought together): client, doula, package, hours bought, price, bought on, expires on, hours used, extra hours and the date the extra hours were invoiced.', [
    C('pack_id', 'Pack ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 22), LST('doula', 'Doula', 'doula', 17), LST('package', 'Package', 'hpack', 22), C('hours_bought', 'Hours bought', 'num', 9),
    C('price', 'Price', 'money', 11), C('bought_on', 'Bought on', 'date', 11), C('expires_on', 'Expires on', 'date', 11), C('hours_used', 'Hours used', 'num', 9), C('extra_hours', 'Extra hours', 'num', 9),
    C('invoiced_on', 'Extra hours invoiced on', 'date', 11),
    CA('hours_left', 'Hours left', 'num', 'MAX(0,{col:hours_bought}-{col:hours_used})', 9), CA('extra_amount', 'Extra hours amount', 'money', 'ROUND({col:extra_hours}*{set:extra_hour_rate},2)', 11),
    CA('price_hour', 'Price per hour', 'money', 'IF({col:hours_bought}>0,ROUND({col:price}/{col:hours_bought},2),0)', 10)],
    D.packs_d(), 300, [A('extra_hours', '> 0', 'warn')]))
# ---------------------------------------------------------------- 4 clients
tables.append(T('clients', 'Clients', 'Clients with package, estimated due date and next visit',
    'One row per client (first name and family name, area only): package, estimated due date (a date the client gives), on-call start, doula, status and the next visit; the hours so far, prenatal visits left and message fields fill in.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 22), C('phone', 'Phone', 'text', 18), LST('area', 'Area', 'area', 11), LST('kind', 'Kind', 'ckind', 11), REF('package', 'Package', 'packages.package', 22),
    C('signed_on', 'Signed on', 'date', 11), C('edd', 'Estimated due date', 'date', 11), C('oncall_start', 'On-call start', 'date', 11), LST('doula', 'Doula', 'doula', 17), LST('status', 'Status', 'cstatus', 15),
    C('next_visit', 'Next visit', 'date', 11), LST('next_kind', 'Next visit kind', 'vkind', 16), C('visit_time', 'Next visit time', 'time', 8),
    CA('price', 'List price', 'money', LKN('packages.price', 'packages.package', 'package'), 11), CA('visits_n', 'Visits so far', 'int', 'COUNTIFS({range:visits.client},{col:client})', 8),
    CA('visit_hours', 'Visit hours so far', 'num', 'SUMIFS({range:visits.hours},{range:visits.client},{col:client})', 9),
    CA('prenatal_n', 'Prenatal visits done', 'int', 'COUNTIFS({range:visits.client},{col:client},{range:visits.kind},%s)' % PRE, 9),
    CA('pp_hours', 'Postpartum hours so far', 'num', 'SUMIFS({range:visits.hours},{range:visits.client},{col:client},{range:visits.kind},"<>"&%s)' % PRE, 9),
    CA('prenatal_plan', 'Prenatal visits planned', 'int', LKN('packages.prenatal_visits', 'packages.package', 'package'), 9), CA('prenatal_left', 'Prenatal visits left', 'int', 'MAX(0,{col:prenatal_plan}-{col:prenatal_n})', 9),
    CA('prenatal_no', 'Next prenatal visit number', 'int', '{col:prenatal_n}+1', 9), CA('days_to_oncall', 'Days to on-call start', 'int', 'IF({col:oncall_start}>0,{col:oncall_start}-{today},"")', 9),
    CA('last_visit', 'Last visit', 'date', 'IF(SUMPRODUCT(MAX(({range:visits.client}={col:client})*{range:visits.date}))=0,"",SUMPRODUCT(MAX(({range:visits.client}={col:client})*{range:visits.date})))', 11),
    CA('min_hours', 'Minimum booking, hours', 'int', '{set:min_booking_hours}', 9), DPH(), CO()],
    D.clients_d(), 600, [A('status', '= ' + tok('cstatus', 'On call'), 'good'), A('status', '= ' + tok('cstatus', 'Cancelled'), 'warn')]))
# ---------------------------------------------------------------- 5 packages
tables.append(T('packages', 'Packages', 'Packages with the planned visits and hours',
    'One row per package: list price, planned prenatal and postpartum visits, birth hours, on-call contact hours, postpartum hours and all planned hours; the other sheets compare actual hours with these.', [
    C('package', 'Package', 'text', 24, required=True), LST('kind', 'Kind', 'pkind', 13), C('price', 'Price', 'money', 11), C('prenatal_visits', 'Prenatal visits', 'int', 9), C('postpartum_visits', 'Postpartum visits', 'int', 9),
    C('birth_hours', 'Birth hours', 'num', 9), C('oncall_hours', 'On-call hours', 'num', 9), C('postpartum_hours', 'Postpartum hours', 'num', 9), C('plan_hours', 'Planned hours', 'num', 9)],
    D.packages_d(), 50))
# ---------------------------------------------------------------- 6 areas
tables.append(T('areas', 'Areas', 'Service areas with the mileage rate',
    'One row per area and rate: the mileage rate per mile and 1 in In use for the rate that counts now; older rates stay as history. Mileage cost uses the rate in use.', [
    LST('area', 'Area', 'area', 14, required=True), C('mileage_rate', 'Mileage rate per mile', 'money', 12), C('in_use', 'In use (1 yes, 0 history)', 'int', 12)], D.areas_d(), 50))
# ---------------------------------------------------------------- 7 doulas
tables.append(T('doulas', 'Doulas', 'Doulas with the weekly hours cap',
    'One row per doula: the service and the weekly hours cap (0 means use the cap in Settings); a solo doula keeps one row.', [
    LST('doula', 'Doula', 'doula', 22, required=True), LST('service', 'Service', 'service', 13), C('weekly_hours_cap', 'Weekly hours cap', 'int', 11)], D.doulas_d(), 50))
# ---------------------------------------------------------------- 8 on-call windows
tables.append(T('oncall', 'On-call Windows', 'On-call windows with contact hours',
    'One row per on-call window (the days around the estimated due date when the doula keeps themselves free): client, doula, start, end, the date the birth was attended and the calls and texts in hours.', [
    C('window_id', 'Window ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 22), LST('doula', 'Doula', 'doula', 17), C('oncall_start', 'On-call start', 'date', 11), C('oncall_end', 'On-call end', 'date', 11),
    C('attended_on', 'Attended on', 'date', 11), C('contact_hours', 'Contact hours', 'num', 9)],
    D.oncall_d(), 400))
# ---------------------------------------------------------------- 9 hours by phase
OVER = ca('Over plan'); WITHIN = ca('Within plan'); NOH = ca('No hours logged')
tables.append(T('phase', 'Hours by Phase', 'Hours by phase for every client against the package plan',
    'One row per client: prenatal, on-call contact, birth and postpartum hours from the other sheets, set against the planned hours of the package; the share over plan and the flag fill in by themselves.', [
    REF('client', 'Client', 'clients.client', 22, required=True), CA('kind', 'Kind', 'text', LKT('clients.kind', 'clients.client', 'client'), 11), CA('package', 'Package', 'text', LKT('clients.package', 'clients.client', 'client'), 22),
    CA('prenatal_hours', 'Prenatal hours', 'num', 'SUMIFS({range:visits.hours},{range:visits.client},{col:client},{range:visits.kind},%s)' % PRE, 9),
    CA('oncall_hours', 'On-call contact hours', 'num', 'SUMIFS({range:oncall.contact_hours},{range:oncall.client},{col:client})', 9),
    CA('birth_hours', 'Birth hours', 'num', 'SUMIFS({range:births.hours},{range:births.client},{col:client})', 9),
    CA('postpartum_hours', 'Postpartum hours', 'num', 'SUMIFS({range:visits.hours},{range:visits.client},{col:client})-{col:prenatal_hours}', 9),
    CA('total_hours', 'Total hours', 'num', '{col:prenatal_hours}+{col:oncall_hours}+{col:birth_hours}+{col:postpartum_hours}', 9),
    CA('plan_hours', 'Planned hours', 'num', LKN('packages.plan_hours', 'packages.package', 'package'), 9), CA('excess_hours', 'Hours over plan', 'num', 'MAX(0,{col:total_hours}-{col:plan_hours})', 9),
    CA('over_share', 'Share over plan', 'pct', 'IF(AND({col:plan_hours}>0,{col:total_hours}>0),{col:total_hours}/{col:plan_hours}-1,0)', 9),
    CA('flag', 'Plan check', 'text', 'IF({col:total_hours}=0,%s,IF({col:over_share}>{set:over_plan_share},%s,%s))' % (NOH, OVER, WITHIN), 14), OWN(), CO()],
    D.phase_d(), 400, [A('flag', '= ' + OVER, 'bad'), A('flag', '= ' + NOH, 'warn'), A('flag', '= ' + WITHIN, 'good')]))
# ---------------------------------------------------------------- 10 hour pack ledger
def PK(col): return 'IFERROR(INDEX({range:packs.%s},MATCH({col:pack_id},{range:packs.pack_id},0)),0)' % col
EXPL, EXPU, FULL, OVRP, END30, END60, ACT = ca('Expired with hours left'), ca('Expired and used'), ca('Used in full'), ca('Over the pack'), ca('Ending in 30 days'), ca('Ending in 60 days'), ca('Active')
tables.append(T('ledger', 'Hour Pack Ledger', 'Hour pack ledger: bought, used, left, expiry and invoice-ready extra hours',
    'One row per hour pack: hours bought, used and left, the expiry date, the extra hours beyond the pack and their invoice-ready amount, all read from Hour Packs; the pack check shows packs ending soon.', [
    REF('pack_id', 'Pack', 'packs.pack_id', 10, required=True), CA('client', 'Client', 'text', LKT('packs.client', 'packs.pack_id', 'pack_id'), 22),
    CA('phone', 'Client phone', 'text', 'IFERROR(INDEX({range:clients.phone},MATCH({col:client},{range:clients.client},0))&"","")', 18), CA('doula', 'Doula', 'text', LKT('packs.doula', 'packs.pack_id', 'pack_id'), 17),
    CA('package', 'Package', 'text', LKT('packs.package', 'packs.pack_id', 'pack_id'), 22), CA('hours_bought', 'Hours bought', 'num', PK('hours_bought'), 9), CA('hours_used', 'Hours used', 'num', PK('hours_used'), 9),
    CA('hours_left', 'Hours left', 'num', 'MAX(0,{col:hours_bought}-{col:hours_used})', 9), CA('used_in_pack', 'Hours used inside the pack', 'num', 'MIN({col:hours_bought},{col:hours_used})', 9),
    CA('price', 'Pack price', 'money', PK('price'), 11), CA('value_left', 'Value of hours left', 'money', 'IF({col:hours_bought}>0,ROUND({col:hours_left}*{col:price}/{col:hours_bought},2),0)', 11),
    CA('expires_on', 'Expires on', 'date', PK('expires_on'), 11), CA('days_to_expiry', 'Days to expiry', 'int', '{col:expires_on}-{today}', 9),
    CA('extra_hours', 'Extra hours', 'num', PK('extra_hours'), 9), CA('extra_amount', 'Invoice-ready amount', 'money', 'ROUND({col:extra_hours}*{set:extra_hour_rate},2)', 11),
    CA('invoiced_on', 'Invoiced on', 'date', LKD('packs.invoiced_on', 'packs.pack_id', 'pack_id'), 11), CA('to_invoice', 'To invoice', 'int', 'IF(AND({col:extra_hours}>0,{col:invoiced_on}=""),1,0)', 8),
    CA('pace_week', 'Hours a week to finish', 'num', 'IF({col:days_to_expiry}>0,{col:hours_left}/MAX(1,{col:days_to_expiry}/7),0)', 9),
    CA('soon_hours', 'Hours left, ending soon', 'num', 'IF(AND({col:days_to_expiry}>=0,{col:days_to_expiry}<={set:pack_warn_days}),{col:hours_left},0)', 9),
    CA('pack_flag', 'Pack check', 'text', 'IF({col:days_to_expiry}<0,IF({col:hours_left}>0,%s,%s),IF({col:hours_left}=0,IF({col:extra_hours}>0,%s,%s),IF({col:days_to_expiry}<={set:pack_warn_days},%s,IF({col:days_to_expiry}<=2*{set:pack_warn_days},%s,%s))))' % (EXPL, EXPU, OVRP, FULL, END30, END60, ACT), 22),
    DPH(), OWN(), CA('admin_phone', 'Admin phone', 'text', '"%s"' % D.ADMIN_PHONE, 18), CO()],
    D.ledger_d(), 300, [A('pack_flag', '= ' + EXPL, 'bad'), A('pack_flag', '= ' + END30, 'warn'), A('pack_flag', '= ' + OVRP, 'warn'), A('to_invoice', '= 1', 'warn')]))
# ---------------------------------------------------------------- 11 weekly hours by doula
def TW(k): return 'SUMIFS({range:visits.hours},{range:visits.doula},{col:doula},{range:visits.week},{col:week}-%d)+SUMIFS({range:births.hours},{range:births.doula},{col:doula},{range:births.week},{col:week}-%d)' % (7 * k, 7 * k)
OV, OVR = ca('Over cap'), ca('Over cap in a row')
tables.append(T('wk_doula', 'Weekly Hours by Doula', 'Weekly hours load by doula against the cap',
    'One row per doula and week: visit hours and birth hours counted from the other sheets against the weekly cap, and how many weeks in a row the doula was over it.', [
    LST('doula', 'Doula', 'doula', 17, required=True), C('week', 'Week starting', 'date', 11),
    CA('visit_hours', 'Visit hours', 'num', 'SUMIFS({range:visits.hours},{range:visits.doula},{col:doula},{range:visits.week},{col:week})', 9),
    CA('birth_hours', 'Birth hours', 'num', 'SUMIFS({range:births.hours},{range:births.doula},{col:doula},{range:births.week},{col:week})', 9),
    CA('total_hours', 'Total hours', 'num', '{col:visit_hours}+{col:birth_hours}', 9),
    CA('cap', 'Weekly cap', 'num', 'IF(SUMIFS({range:doulas.weekly_hours_cap},{range:doulas.doula},{col:doula})>0,SUMIFS({range:doulas.weekly_hours_cap},{range:doulas.doula},{col:doula}),{set:weekly_hours_cap})', 9),
    CA('pct_cap', 'Share of cap', 'pct', 'IF({col:cap}>0,{col:total_hours}/{col:cap},0)', 9),
    CA('weeks_over', 'Weeks over in a row', 'int', 'IF({col:total_hours}>{col:cap},1+IF(%s>{col:cap},1+IF(%s>{col:cap},1+IF(%s>{col:cap},1,0),0),0),0)' % (TW(1), TW(2), TW(3)), 9),
    CA('hours_last4', 'Hours, last 4 weeks only', 'num', 'IF({col:week}>={today}-28,{col:total_hours},0)', 9),
    CA('flag', 'Cap check', 'text', 'IF({col:total_hours}<={col:cap},%s,IF({col:weeks_over}>={set:weeks_over_warn},%s,%s))' % (ca('Within cap'), OVR, OV), 17), DPH(), OWN(), CO()],
    D.wk_doula_d(), 200, [A('flag', '= ' + OV, 'warn'), A('flag', '= ' + OVR, 'bad')]))
# ---------------------------------------------------------------- 12 weekly hours by week
tables.append(T('wk_all', 'Weekly Hours by Week', 'Weekly hours for the whole team, last 26 weeks',
    'One row per week (Week 26 is this week): visits, visit hours, birth hours and births counted from the other sheets.', [
    C('week', 'Week starting', 'date', 11, required=True), LST('week_no', 'Week number', 'wkno', 10),
    CA('visits', 'Visits', 'int', 'COUNTIFS({range:visits.week},{col:week})', 8), CA('visit_hours', 'Visit hours', 'num', 'SUMIFS({range:visits.hours},{range:visits.week},{col:week})', 9),
    CA('birth_hours', 'Birth hours', 'num', 'SUMIFS({range:births.hours},{range:births.week},{col:week})', 9), CA('total_hours', 'Total hours', 'num', '{col:visit_hours}+{col:birth_hours}', 9),
    CA('births', 'Births', 'int', 'COUNTIFS({range:births.week},{col:week})', 8)],
    D.wk_all_d(), 60))
# ---------------------------------------------------------------- 13 mileage by month
tables.append(T('mil_month', 'Mileage by Month', 'Hours and mileage by month',
    'One row per month: visits, births, hours, miles and mileage cost counted from the other sheets, the visits shorter than the minimum and the extra hours still to invoice.', [
    C('month', 'Month', 'date', 11, required=True), CA('visits', 'Visits', 'int', 'COUNTIFS({range:visits.month},{col:month})', 8), CA('births', 'Births', 'int', 'COUNTIFS({range:births.month},{col:month})', 8),
    CA('trips', 'Trips', 'int', '{col:visits}+{col:births}', 8), CA('visit_hours', 'Visit hours', 'num', 'SUMIFS({range:visits.hours},{range:visits.month},{col:month})', 9),
    CA('birth_hours', 'Birth hours', 'num', 'SUMIFS({range:births.hours},{range:births.month},{col:month})', 9),
    CA('miles', 'Miles', 'num', 'SUMIFS({range:visits.miles},{range:visits.month},{col:month})+SUMIFS({range:births.miles},{range:births.month},{col:month})', 9),
    CA('mileage_cost', 'Mileage cost', 'money', 'SUMIFS({range:visits.mileage_cost},{range:visits.month},{col:month})+SUMIFS({range:births.mileage_cost},{range:births.month},{col:month})', 11),
    CA('cost_per_trip', 'Cost per trip', 'money', 'IF({col:trips}>0,{col:mileage_cost}/{col:trips},0)', 10), CA('short_visits', 'Visits below minimum', 'int', 'COUNTIFS({range:visits.month},{col:month},{range:visits.short},1)', 9),
    CA('extra_hours', 'Extra hours, packs ending', 'num', 'SUMIFS({range:ledger.extra_hours},{range:ledger.expires_on},">="&{col:month},{range:ledger.expires_on},"<"&EDATE({col:month},1))', 9),
    CA('to_invoice', 'Extra hours still to invoice', 'money', 'SUMIFS({range:ledger.extra_amount},{range:ledger.to_invoice},1,{range:ledger.expires_on},"<"&EDATE({col:month},1))', 11),
    OWN(), CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCOUNTANT_PHONE, 18), CO()],
    D.months_d(), 60))
# ---------------------------------------------------------------- 14 mileage by client
HIGH, NORM = ca('High mileage share'), ca('Normal mileage share')
tables.append(T('mil_client', 'Mileage by Client', 'Mileage by client against the package price',
    'One row per client with the highest mileage: trips, miles and mileage cost from visits and births, and the share of the list price; clients above the limit in Settings are flagged.', [
    REF('client', 'Client', 'clients.client', 22, required=True), CA('package', 'Package', 'text', LKT('clients.package', 'clients.client', 'client'), 22),
    CA('trips', 'Trips', 'int', 'COUNTIFS({range:visits.client},{col:client})+COUNTIFS({range:births.client},{col:client})', 8),
    CA('miles', 'Miles', 'num', 'SUMIFS({range:visits.miles},{range:visits.client},{col:client})+SUMIFS({range:births.miles},{range:births.client},{col:client})', 9),
    CA('mileage_cost', 'Mileage cost', 'money', 'SUMIFS({range:visits.mileage_cost},{range:visits.client},{col:client})+SUMIFS({range:births.mileage_cost},{range:births.client},{col:client})', 11),
    CA('price', 'List price', 'money', LKN('packages.price', 'packages.package', 'package'), 11), CA('share', 'Share of price', 'pct', 'IF({col:price}>0,{col:mileage_cost}/{col:price},0)', 9),
    CA('flag', 'Mileage check', 'text', 'IF({col:share}>{set:mileage_share_max},%s,%s)' % (HIGH, NORM), 20)],
    D.mil_client_d(), 150, [A('flag', '= ' + HIGH, 'warn')]))
# ---------------------------------------------------------------- 15 mileage by doula and area
tables.append(T('mil_doula', 'Mileage by Doula and Area', 'Mileage by doula and area',
    'One row per doula and area: trips, miles and mileage cost from visits and births attended; see who drives most and where.', [
    LST('doula', 'Doula', 'doula', 17, required=True), LST('area', 'Area', 'area', 11),
    CA('trips', 'Trips', 'int', 'COUNTIFS({range:visits.doula},{col:doula},{range:visits.area},{col:area})+COUNTIFS({range:births.doula},{col:doula},{range:births.area},{col:area})', 8),
    CA('miles', 'Miles', 'num', 'SUMIFS({range:visits.miles},{range:visits.doula},{col:doula},{range:visits.area},{col:area})+SUMIFS({range:births.miles},{range:births.doula},{col:doula},{range:births.area},{col:area})', 9),
    CA('mileage_cost', 'Mileage cost', 'money', 'SUMIFS({range:visits.mileage_cost},{range:visits.doula},{col:doula},{range:visits.area},{col:area})+SUMIFS({range:births.mileage_cost},{range:births.doula},{col:doula},{range:births.area},{col:area})', 11),
    CA('cost_per_trip', 'Cost per trip', 'money', 'IF({col:trips}>0,{col:mileage_cost}/{col:trips},0)', 10)],
    D.mil_doula_d(), 50))
# ---------------------------------------------------------------- 16 births per month
tables.append(T('births_month', 'Births per Month', 'Births attended per month',
    'One row per month: births attended, hours attended, the average, births with a backup doula, night calls and the births of the quarter against the maximum in Settings.', [
    C('month', 'Month', 'date', 11, required=True), CA('births', 'Births', 'int', 'COUNTIFS({range:births.month},{col:month})', 8), CA('hours', 'Hours attended', 'num', 'SUMIFS({range:births.hours},{range:births.month},{col:month})', 9),
    CA('avg_hours', 'Average hours', 'num', 'IF({col:births}>0,{col:hours}/{col:births},0)', 9), CA('backup_births', 'Births with a backup doula', 'int', 'COUNTIFS({range:births.month},{col:month},{range:births.backup_used},%s)' % YES, 9),
    CA('night_calls', 'Night calls', 'int', 'COUNTIFS({range:births.month},{col:month},{range:births.night_call},1)', 8),
    CA('births_quarter', 'Births in the quarter', 'int', 'COUNTIFS({range:births.qtr},%s)' % QTR('{col:month}'), 9), CA('quarter_max', 'Quarter maximum', 'int', '{set:births_quarter_max}', 9), OWN(), CO()],
    D.months_d(), 60, [A('births_quarter', '> {set:births_quarter_max}', 'warn')]))
# ---------------------------------------------------------------- 17 rest days between births
TOO, ENOUGH = ca('Too little rest'), ca('Enough rest')
tables.append(T('rest', 'Rest Days Between Births', 'Rest days between two births of the same doula',
    'One row per birth that follows an earlier birth of the same doula: the previous birth and the full days between the two; births with fewer days than the minimum in Settings are flagged.', [
    REF('birth_id', 'Birth', 'births.birth_id', 10, required=True), CA('doula', 'Doula', 'text', LKT('births.doula', 'births.birth_id', 'birth_id'), 17),
    CA('date', 'Birth date', 'date', 'IFERROR(INDEX({range:births.date},MATCH({col:birth_id},{range:births.birth_id},0)),"")', 11),
    CA('previous_birth', 'Previous birth', 'date', 'IF(SUMPRODUCT(MAX(({range:births.doula}={col:doula})*({range:births.date}<{col:date})*{range:births.date}))=0,"",SUMPRODUCT(MAX(({range:births.doula}={col:doula})*({range:births.date}<{col:date})*{range:births.date})))', 11),
    CA('rest_days', 'Rest days between', 'int', '{col:date}-{col:previous_birth}-1', 9), CA('flag', 'Rest check', 'text', 'IF({col:rest_days}<{set:rest_days_min},%s,%s)' % (TOO, ENOUGH), 14),
    CA('min_rest', 'Minimum rest days', 'int', '{set:rest_days_min}', 9), DPH(), OWN(), CO()],
    D.rest_d(), 300, [A('flag', '= ' + TOO, 'bad')]))
# ---------------------------------------------------------------- 18 birth hours bands
BH = [(None, 8), (8, 12), (12, 16), (16, 20), (20, 24), (24, None)]
def band_count(i):
    lo, hi = BH[i]; parts = []
    if lo is not None: parts.append('{range:births.hours},">%d"' % lo)
    if hi is not None: parts.append('{range:births.hours},"<=%d"' % hi)
    return 'COUNTIFS(%s)' % ','.join(parts)
BF = ''
for i in range(6): BF += 'IF({col:band}=%s,%s,' % (tok('hband', HBAND[i]), band_count(i))
BF += '0' + ')' * 6
tables.append(T('birth_bands', 'Birth Hours Bands', 'Births attended by length in hours',
    'One row per band of attended hours: the births and their share of all births attended.', [
    LST('band', 'Hours band', 'hband', 18, required=True), CA('births', 'Births', 'int', BF, 9), CA('share', 'Share of births', 'pct', 'IF(COUNT({range:births.hours})>0,{col:births}/COUNT({range:births.hours}),0)', 10)],
    D.bands_d(), 50))
# ---------------------------------------------------------------- 19 call time bands
def call_filter(i): return '{range:births.call_hour},">=%d",{range:births.call_hour},"<%d"' % (4 * i, 4 * i + 4)
CF = ''; AF = ''
for i in range(6):
    CF += 'IF({col:band}=%s,COUNTIFS(%s),' % (tok('cband', CBAND[i]), call_filter(i)); AF += 'IF({col:band}=%s,IFERROR(AVERAGEIFS({range:births.hours},%s),0),' % (tok('cband', CBAND[i]), call_filter(i))
CF += '0' + ')' * 6; AF += '0' + ')' * 6
tables.append(T('call_bands', 'Call Time Bands', 'Birth calls by time of day',
    'One row per four-hour band of the day: the calls received and the average hours attended after a call in that band.', [
    LST('band', 'Call time band', 'cband', 18, required=True), CA('calls', 'Calls', 'int', CF, 9), CA('avg_hours', 'Average hours attended', 'num', AF, 11)],
    D.calls_d(), 50))
# ---------------------------------------------------------------- 20 team
def VS(extra): return 'SUMIFS({range:visits.hours},{range:visits.doula},{col:name}%s)' % extra
def BS(extra): return 'SUMIFS({range:births.hours},{range:births.doula},{col:name}%s)' % extra
D12 = ',{range:visits.date},">="&EDATE({today},-12)'; B12 = ',{range:births.date},">="&EDATE({today},-12)'
D28 = ',{range:visits.date},">="&({today}-28),{range:visits.date},"<="&{today}'; B28 = ',{range:births.date},">="&({today}-28),{range:births.date},"<="&{today}'
tables.append(T('team', 'Team', 'Team with roles, phones and hours',
    'One row per person: staff, doulas, backup doulas, the admin and outside contacts; for doulas the hours this week, the cap, night work, miles and yearly hours fill in from the other sheets, and the message links read these phones.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 20), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    CA('hours_week', 'Hours this week', 'num', '%s+%s' % (VS(',{range:visits.week},%s' % THISMON), BS(',{range:births.week},%s' % THISMON)), 9),
    CA('cap', 'Weekly cap', 'num', 'IF(SUMIFS({range:doulas.weekly_hours_cap},{range:doulas.doula},{col:name})>0,SUMIFS({range:doulas.weekly_hours_cap},{range:doulas.doula},{col:name}),IF(COUNTIFS({range:doulas.doula},{col:name})>0,{set:weekly_hours_cap},0))', 9),
    CA('hours_4wk', 'Weekly hours, last 4 weeks', 'num', '(%s+%s)/4' % (VS(D28), BS(B28)), 9),
    CA('weeks_over_12', 'Weeks over the cap, last 12 weeks', 'int', 'COUNTIFS({range:wk_doula.doula},{col:name},{range:wk_doula.week},">="&({today}-84),{range:wk_doula.flag},%s)+COUNTIFS({range:wk_doula.doula},{col:name},{range:wk_doula.week},">="&({today}-84),{range:wk_doula.flag},%s)' % (OV, OVR), 9),
    CA('nights_30', 'Night calls and shifts, 30 days', 'int', 'COUNTIFS({range:visits.doula},{col:name},{range:visits.kind},%s,{range:visits.date},">="&({today}-30))+COUNTIFS({range:births.doula},{col:name},{range:births.night_call},1,{range:births.date},">="&({today}-30))' % NIGHT, 9),
    CA('report_month', 'Report month', 'date', MS, 11),
    CA('miles_month', 'Miles this month', 'num', 'SUMIFS({range:visits.miles},{range:visits.doula},{col:name},{range:visits.month},%s)+SUMIFS({range:births.miles},{range:births.doula},{col:name},{range:births.month},%s)' % (MS, MS), 9),
    CA('cost_month', 'Mileage cost this month', 'money', 'SUMIFS({range:visits.mileage_cost},{range:visits.doula},{col:name},{range:visits.month},%s)+SUMIFS({range:births.mileage_cost},{range:births.doula},{col:name},{range:births.month},%s)' % (MS, MS), 11),
    CA('miles_12', 'Miles, 12 months', 'num', 'SUMIFS({range:visits.miles},{range:visits.doula},{col:name}%s)+SUMIFS({range:births.miles},{range:births.doula},{col:name}%s)' % (D12, B12), 9),
    CA('cost_12', 'Mileage cost, 12 months', 'money', 'SUMIFS({range:visits.mileage_cost},{range:visits.doula},{col:name}%s)+SUMIFS({range:births.mileage_cost},{range:births.doula},{col:name}%s)' % (D12, B12), 11),
    CA('yr_visit_hours', 'Visit hours, 12 months', 'num', VS(D12), 9), CA('yr_birth_hours', 'Birth hours, 12 months', 'num', BS(B12), 9),
    CA('yr_capacity', 'Capacity, hours a year', 'num', '{col:cap}*52', 9), CA('yr_share', 'Share of yearly capacity', 'pct', 'IF({col:yr_capacity}>0,({col:yr_visit_hours}+{col:yr_birth_hours})/{col:yr_capacity},0)', 9),
    CA('missing_logs', 'Visit logs missing miles, 7 days', 'int', 'COUNTIFS({range:visits.date},">="&({today}-7),{range:visits.complete},0)', 9),
    CA('packs_ending', 'Packs ending this month', 'int', 'COUNTIFS({range:ledger.expires_on},">="&%s,{range:ledger.expires_on},"<"&EDATE(%s,1),{range:ledger.hours_left},">0")' % (MS, MS), 9), CO()],
    D.team_d(), 50))
assert len(tables) == 20, len(tables)
