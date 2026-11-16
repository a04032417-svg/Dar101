"""Doula business suite part 6: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du6_lists import *
import du6_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def CO(): return CA('company', 'Business', 'text', '{set:company}', 24)
def OWN(): return CA('owner_phone', 'Owner-doula phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def ADM(): return CA('admin_phone', 'Admin phone', 'text', '"%s"' % D.ADMIN_PHONE, 18)
def ACC(): return CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCOUNTANT_PHONE, 18)
def DPH(c='doula'): return CA('doula_phone', 'Doula phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:%s},{range:team.name},0))&"","")' % c, 18)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PC = tok('basis', 'Per client'); PH = tok('basis', 'Per hour'); MIL = tok('basis', 'Mileage'); STI = tok('basis', 'Backup stipend'); CALL = tok('basis', 'Backup call-out')
PAID = tok('paystatus', 'Paid'); DUE = tok('paystatus', 'Due')
RATE = 'IF({col:area}=%s,{set:mileage_rate_north},{set:mileage_rate_south})' % tok('area', 'Northgate')
def S2(col, crit_col, crit, extra=''):  # SUMIFS on pay with a doula-like and month-like row key
    return 'SUMIFS({range:pay.%s},%s%s)' % (col, crit, extra)
def PAYM(col, basis, extra=''): return 'SUMIFS({range:pay.%s},{range:pay.doula},{col:doula},{range:pay.month},{col:month},{range:pay.basis},%s%s)' % (col, basis, extra)
W12 = '{range:pay.month},">="&EDATE(%s,-12),{range:pay.month},"<"&%s' % (MS, MS)
def PAY12(basis): return 'SUMIFS({range:pay.pay_due},{range:pay.doula},{col:name},{range:pay.basis},%s,%s)' % (basis, W12)

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('agency_cost_client', 'Agency overhead per client', 'money', AGENCY_COST_CLIENT),
    S('target_margin_client', 'Margin per client you want after pay, mileage and overhead', 'money', 250), S('backup_flat_pay', 'Flat call-out pay for a backup doula who attends', 'money', BACKUP_FLAT_PAY),
    S('backup_stipend_week', 'Weekly stipend for a backup doula on the rota', 'money', BACKUP_STIPEND_WEEK), S('diff_tolerance', 'Difference between paid and due that is ignored', 'money', 1),
    S('cap_births_month', 'Most due dates of one doula in a month', 'int', CAP_BIRTHS), S('pp_clients_month', 'Most postpartum clients of one doula starting in a month', 'int', 4),
    S('max_oncall_overlap', 'Most on-call windows of one doula at the same time', 'int', MAX_OVERLAP), S('weekly_hours_cap', 'Most postpartum and birth hours for one doula in a week', 'int', WEEKLY_HOURS_CAP),
    S('owner_draw', 'Owner draw a month', 'money', OWNER_DRAW), S('target_income_hour', 'Pay per hour worked that you want for yourself', 'money', 30),
    S('min_pay_hour', 'Lowest pay per hour worked you think is fair for a doula', 'money', 20), S('mileage_rate_north', 'Mileage rate per mile, Northgate', 'money', 0.58),
    S('mileage_rate_south', 'Mileage rate per mile, Southbank', 'money', 0.62), S('statement_days', 'Days after month end for sending a statement', 'int', 5),
    S('admin_rate', 'Admin pay per hour', 'money', ADMIN_RATE), S('admin_hours_week', 'Admin hours a week', 'int', ADMIN_HOURS_WEEK),
    S('admin_client_share', 'Share of admin time spent on client work', 'pct', 0.5), S('over_plan_share', 'Share over the planned hours that flags a client', 'pct', 0.15)]
assert 3 <= len(settings) <= 20

tables = []
# 1 pay lines
tables.append(T('pay', 'Pay Lines', 'Pay Lines: what each doula is due and what was paid',
    'One row per pay line: month, doula, client, basis, hours, miles, gross, agency share, pay due, paid amount and paid on; the difference, the differs check and what the agency keeps fill in by themselves.', [
    C('pay_id', 'Pay ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('doula', 'Doula', 'payee', 17), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 22), LST('basis', 'Basis', 'basis', 15),
    C('hours', 'Hours', 'num', 8), C('miles', 'Miles', 'num', 8), C('gross', 'Gross', 'money', 11), C('agency_share', 'Agency share', 'pct', 9), C('pay_due', 'Pay due', 'money', 11), C('paid_amount', 'Paid amount', 'money', 11),
    C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'paystatus', 9),
    CA('difference', 'Difference', 'money', 'IF({col:status}=%s,ROUND({col:paid_amount}-{col:pay_due},2),0)' % PAID, 11),
    CA('differs', 'Differs', 'int', 'IF(AND({col:status}=%s,ABS({col:difference})>{set:diff_tolerance}),1,0)' % PAID, 8),
    CA('agency_keeps', 'Agency keeps', 'money', 'IF(OR({col:basis}=%s,{col:basis}=%s),ROUND({col:gross}-{col:pay_due},2),0)' % (PC, PH), 11), DPH(), OWN(), CO()],
    D.pay_d(), 900, [A('differs', '= 1', 'warn'), A('status', '= ' + DUE, 'bad')]))
# 2 doulas
tables.append(T('doulas', 'Doulas', 'Doulas with the agency share and the hourly pay',
    'One row per doula: the agency share of the birth part (per-client pay) and the hourly pay (per-hour pay); a solo doula keeps one row with no share.', [
    LST('doula', 'Doula', 'doula', 22, required=True), C('agency_share', 'Agency share', 'pct', 11), C('hourly_pay', 'Hourly pay', 'money', 11)], D.doulas_d(), 50))
# 3 clients
tables.append(T('clients', 'Clients', 'Clients with package, doula and estimated due date',
    'One row per client (first name and family name only): kind, package, doula, backup doula, status, signed on and the estimated due date (a date the client gives); the price, the margin and phones fill in.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 22), C('phone', 'Phone', 'text', 18), LST('kind', 'Kind', 'ckind', 11), REF('package', 'Package', 'packages.package', 22), LST('doula', 'Doula', 'doula', 17),
    LST('backup', 'Backup doula', 'backup', 15), LST('status', 'Status', 'cstatus', 15), C('signed_on', 'Signed on', 'date', 11), C('edd', 'Estimated due date', 'date', 11),
    CA('price', 'List price', 'money', LKN('packages.price', 'packages.package', 'package'), 11), CA('margin', 'Agency margin', 'money', LKN('margin.margin', 'margin.client_id', 'client_id'), 11), DPH(), OWN(), CO()],
    D.clients_d(), 600, [A('status', '= ' + tok('cstatus', 'On call'), 'good'), A('status', '= ' + tok('cstatus', 'Cancelled'), 'warn')]))
# 4 packages
tables.append(T('packages', 'Packages', 'Packages with the birth part and the planned hours',
    'One row per package: list price, the birth part and the postpartum part, planned birth hours, postpartum hours and all planned hours; pay and margin tools read these.', [
    C('package', 'Package', 'text', 24, required=True), LST('kind', 'Kind', 'pkind', 13), C('price', 'Price', 'money', 11), C('birth_value', 'Birth part', 'money', 11), C('pp_value', 'Postpartum part', 'money', 11),
    C('birth_hours', 'Birth hours', 'num', 9), C('postpartum_hours', 'Postpartum hours', 'num', 9), C('plan_hours', 'Planned hours', 'num', 9)], D.packages_d(), 50))
# 5 visits
tables.append(T('visits', 'Visits', 'Visits with hours, miles and mileage cost',
    'One row per visit: date, client, doula, kind, hours, miles and area; the month and the mileage cost at the rate of the area fill in by themselves.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('client', 'Client', 'clients.client', 22), LST('doula', 'Doula', 'doula', 17), LST('kind', 'Kind', 'vkind', 16), C('hours', 'Hours', 'num', 8),
    C('miles', 'Miles', 'num', 8), LST('area', 'Area', 'area', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('mileage_cost', 'Mileage cost', 'money', 'ROUND({col:miles}*%s,2)' % RATE, 11)],
    D.visits_d(), 2400))
# 6 births
tables.append(T('births', 'Births Attended', 'Births attended with hours and miles',
    'One row per birth attended: date, client, the doula who attended, the assigned doula, whether a backup doula attended, hours, miles and area (no detail of any birth); month and mileage cost fill in.', [
    C('birth_id', 'Birth ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('client', 'Client', 'clients.client', 22), LST('doula', 'Doula who attended', 'attender', 17), LST('assigned', 'Assigned doula', 'doula', 17),
    C('backup_used', 'Backup used', 'bool', 8), C('hours', 'Hours', 'num', 8), C('miles', 'Miles', 'num', 8), LST('area', 'Area', 'area', 11),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('mileage_cost', 'Mileage cost', 'money', 'ROUND({col:miles}*%s,2)' % RATE, 11)], D.births_d(), 400))
# 7 on-call windows
tables.append(T('oncall', 'On-call Windows', 'On-call windows with the doula and the backup doula',
    'One row per on-call window (the days around the estimated due date when the doula keeps themselves free): client, doula, backup doula, start, end and contact hours; the days in the window fill in.', [
    C('window_id', 'Window ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 22), LST('doula', 'Doula', 'doula', 17), LST('backup', 'Backup doula', 'backup', 15), C('oncall_start', 'On-call start', 'date', 11),
    C('oncall_end', 'On-call end', 'date', 11), C('contact_hours', 'Contact hours', 'num', 9), CA('days', 'Days in window', 'int', 'IF({col:oncall_end}>0,{col:oncall_end}-{col:oncall_start}+1,"")', 9)], D.oncall_d(), 400))
# 8 backup rota
tables.append(T('rota', 'Backup Rota', 'Backup rota with the weekly stipend',
    'One row per backup doula and week: the weekly stipend; the month fills in so that the stipend run can be checked against the pay lines.', [
    C('rota_id', 'Rota ID', 'text', 10, required=True), C('week', 'Week', 'date', 11), LST('backup', 'Backup doula', 'backup', 15), C('stipend', 'Stipend', 'int', 9),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:week}),MONTH({col:week}),1)', 11)], D.rota_d(), 300))
# 9 owner time
tables.append(T('owner_time', 'Owner Time Log', 'Owner time log: own clients, management and admin hours',
    'One row per week: hours the owner-doula spent on own clients, on managing the agency and on office tasks; the month and the total fill in.', [
    C('log_id', 'Log ID', 'text', 10, required=True), C('week', 'Week', 'date', 11), C('own_client_hours', 'Own client hours', 'num', 10), C('management_hours', 'Management hours', 'num', 10), C('admin_hours', 'Admin hours', 'num', 10),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:week}),MONTH({col:week}),1)', 11), CA('total_hours', 'Total hours', 'num', '{col:own_client_hours}+{col:management_hours}+{col:admin_hours}', 9)], D.owner_time_d(), 300))
# 10 team
H12 = 'SUMIFS({range:visits.hours},{range:visits.doula},{col:name},{range:visits.date},">"&EDATE({today},-12))+SUMIFS({range:births.hours},{range:births.doula},{col:name},{range:births.date},">"&EDATE({today},-12))'
tables.append(T('team', 'Team', 'Team: doulas, backup doulas, admin and outside contacts',
    'One row per person: role, pay type, phone, email, hourly rate, caps and review date; for a doula the agency share, the margin, the last 12 months of pay and hours fill in by themselves.', [
    C('staff_id', 'Staff ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('pay_type', 'Pay type', 'paytype', 18), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26),
    C('hourly_rate', 'Hourly rate', 'money', 11), C('hours_week', 'Hours a week', 'int', 9), LST('service', 'Service', 'service', 12), C('cap_births', 'Most due dates a month', 'int', 9), C('weekly_hours_cap', 'Weekly hours cap', 'int', 9),
    C('start', 'Start', 'date', 11), C('review_on', 'Review on', 'date', 11),
    CA('agency_share', 'Agency share', 'pct', LKN('doulas.agency_share', 'doulas.doula', 'name'), 9), CA('clients', 'Clients with pay lines', 'int', LKN('margin_doula.clients', 'margin_doula.doula', 'name'), 9),
    CA('margin', 'Margin after costs', 'money', LKN('margin_doula.margin', 'margin_doula.doula', 'name'), 11), CA('margin_pc', 'Margin per client', 'money', 'IF({col:clients}>0,ROUND({col:margin}/{col:clients},2),0)', 11),
    CA('loss', 'Loss to the agency', 'money', 'MAX(0,-{col:margin})', 11),
    CA('over_share', 'Clients over plan share', 'pct', 'IF({col:clients}>0,COUNTIFS({range:margin.doula},{col:name},{range:margin.over_plan},1)/{col:clients},0)', 9),
    CA('pay_12', 'Doula pay, 12 months', 'money', '%s+%s' % (PAY12(PC), PAY12(PH)), 11), CA('mileage_12', 'Mileage paid, 12 months', 'money', PAY12(MIL), 11), CA('backup_12', 'Backup pay, 12 months', 'money', '%s+%s' % (PAY12(STI), PAY12(CALL)), 11),
    CA('hours_12', 'Hours worked, 12 months', 'num', H12, 9), CA('pay_hour_12', 'Pay per hour worked, 12 months', 'money', 'IF({col:hours_12}>0,ROUND(({col:pay_12})/{col:hours_12},2),0)', 11), OWN(), ACC(), CO()],
    D.team_d(), 60))
# 11 margin by client
tables.append(T('margin', 'Agency Margin by Client', 'Agency margin by client after pay, mileage and overhead',
    'One row per client with pay lines: revenue, doula pay, mileage and overhead per client and the margin after costs, with the hours against the plan; only the client ID is typed.', [
    C('client_id', 'Client ID', 'text', 10, required=True),
    CA('client', 'Client', 'text', LKT('clients.client', 'clients.client_id', 'client_id'), 22), CA('doula', 'Doula', 'text', LKT('clients.doula', 'clients.client_id', 'client_id'), 17),
    CA('package', 'Package', 'text', LKT('clients.package', 'clients.client_id', 'client_id'), 22), CA('edd', 'Estimated due date', 'date', LKD('clients.edd', 'clients.client_id', 'client_id'), 11),
    CA('revenue', 'Revenue', 'money', 'SUMIFS({range:pay.gross},{range:pay.client_id},{col:client_id},{range:pay.basis},%s)+SUMIFS({range:pay.gross},{range:pay.client_id},{col:client_id},{range:pay.basis},%s)' % (PC, PH), 11),
    CA('doula_pay', 'Doula pay', 'money', 'SUMIFS({range:pay.pay_due},{range:pay.client_id},{col:client_id},{range:pay.basis},%s)+SUMIFS({range:pay.pay_due},{range:pay.client_id},{col:client_id},{range:pay.basis},%s)+SUMIFS({range:pay.pay_due},{range:pay.client_id},{col:client_id},{range:pay.basis},%s)' % (PC, PH, CALL), 11),
    CA('mileage', 'Mileage', 'money', 'ROUND(SUMIFS({range:visits.mileage_cost},{range:visits.client},{col:client})+SUMIFS({range:births.mileage_cost},{range:births.client},{col:client}),2)', 11),
    CA('overhead', 'Overhead', 'money', '{set:agency_cost_client}', 11), CA('margin', 'Margin after costs', 'money', 'ROUND({col:revenue}-{col:doula_pay}-{col:mileage}-{col:overhead},2)', 11),
    CA('hours', 'Hours worked', 'num', 'SUMIFS({range:visits.hours},{range:visits.client},{col:client})+SUMIFS({range:births.hours},{range:births.client},{col:client})', 9),
    CA('plan_hours', 'Planned hours', 'num', LKN('packages.plan_hours', 'packages.package', 'package'), 9),
    CA('over_plan', 'Over plan', 'int', 'IF({col:hours}>{col:plan_hours}*(1+{set:over_plan_share}),1,0)', 8), CA('meets', 'Meets target', 'int', 'IF({col:margin}>={set:target_margin_client},1,0)', 8)],
    D.margin_d(), 400, [A('margin', '< 0', 'bad')]))
# 12 margin by doula
tables.append(T('margin_doula', 'Margin by Doula', 'Margin by doula after costs',
    'One row per contracted doula: clients with pay lines and the margin the agency keeps after pay, mileage and overhead (a negative margin means the split loses money).', [
    LST('doula', 'Doula', 'cdoula', 22, required=True), CA('clients', 'Clients', 'int', 'COUNTIFS({range:margin.doula},{col:doula})', 9),
    CA('margin', 'Margin after costs', 'money', 'ROUND(SUMIFS({range:margin.margin},{range:margin.doula},{col:doula}),2)', 12)], D.margin_doula_d(), 50, [A('margin', '< 0', 'bad')]))
# 13 pay run statement
PR = lambda b: PAYM('pay_due', b)
tables.append(T('payrun', 'Pay Run Statement', 'Pay run statement per doula and month, checked against what was paid',
    'One row per doula and month: per-client pay, per-hour pay, mileage and backup pay due, the paid amount and the difference; type the date the statement was sent to see if it was on time.', [
    C('run_id', 'Run ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('doula', 'Doula', 'payee', 17), C('sent_on', 'Statement sent on', 'date', 11),
    CA('per_client', 'Per-client pay', 'money', PR(PC), 11), CA('per_hour', 'Per-hour pay', 'money', PR(PH), 11), CA('mileage', 'Mileage', 'money', PR(MIL), 11), CA('miles', 'Miles', 'num', PAYM('miles', MIL), 8), CA('backup', 'Backup pay', 'money', '%s+%s' % (PR(STI), PR(CALL)), 11),
    CA('total_due', 'Total due', 'money', 'ROUND({col:per_client}+{col:per_hour}+{col:mileage}+{col:backup},2)', 11),
    CA('paid', 'Paid', 'money', 'SUMIFS({range:pay.paid_amount},{range:pay.doula},{col:doula},{range:pay.month},{col:month})', 11),
    CA('unpaid', 'Not paid yet', 'money', 'SUMIFS({range:pay.pay_due},{range:pay.doula},{col:doula},{range:pay.month},{col:month},{range:pay.status},%s)' % DUE, 11),
    CA('difference', 'Difference', 'money', 'SUMIFS({range:pay.difference},{range:pay.doula},{col:doula},{range:pay.month},{col:month})', 11),
    CA('diff_n', 'Lines that differ', 'int', 'SUMIFS({range:pay.differs},{range:pay.doula},{col:doula},{range:pay.month},{col:month})', 8),
    CA('check', 'Check', 'text', 'IF({col:unpaid}>0,%s,IF({col:diff_n}>0,%s,%s))' % (ck('Not all paid yet'), ck('Paid differently'), ck('Balanced')), 15),
    CA('sent', 'Sent', 'int', 'IF({col:sent_on}>0,1,0)', 6), CA('on_time', 'Sent on time', 'int', 'IF({col:sent_on}>0,IF({col:sent_on}-(EDATE({col:month},1)-1)<={set:statement_days},1,0),0)', 8),
    CA('rota_weeks', 'Rota weeks', 'int', 'COUNTIFS({range:rota.backup},{col:doula},{range:rota.month},{col:month})', 8),
    CA('month_due_all', 'Month total due', 'money', 'SUMIFS({range:payrun.total_due},{range:payrun.month},{col:month})', 12), CA('month_open_due', 'Month not paid yet', 'money', 'SUMIFS({range:payrun.unpaid},{range:payrun.month},{col:month})', 12),
    CA('month_diff_lines', 'Month lines that differ', 'int', 'SUMIFS({range:payrun.diff_n},{range:payrun.month},{col:month})', 8), DPH(), OWN(), ADM(), ACC(), CO()],
    D.payrun_d(), 300, [A('diff_n', '> 0', 'warn'), A('unpaid', '> 0', 'bad')]))
# 14 differences
tables.append(T('diffs', 'Paid vs Due Differences', 'Paid vs due differences to check',
    'Type a pay ID of a line that was paid differently from what was due, or of a line still unpaid: the doula, the month, the amounts and the check fill in.', [
    C('pay_id', 'Pay ID', 'text', 10, required=True), CA('doula', 'Doula', 'text', LKT('pay.doula', 'pay.pay_id', 'pay_id'), 17), CA('client', 'Client', 'text', LKT('pay.client', 'pay.pay_id', 'pay_id'), 22),
    CA('month', 'Month', 'date', LKD('pay.month', 'pay.pay_id', 'pay_id'), 11), CA('pay_due', 'Pay due', 'money', LKN('pay.pay_due', 'pay.pay_id', 'pay_id'), 11), CA('paid_amount', 'Paid amount', 'money', LKN('pay.paid_amount', 'pay.pay_id', 'pay_id'), 11),
    CA('difference', 'Difference', 'money', 'ROUND({col:paid_amount}-{col:pay_due},2)', 11), CA('status', 'Status', 'text', LKT('pay.status', 'pay.pay_id', 'pay_id'), 9),
    CA('adjust', 'Adjustment to make', 'money', 'IF({col:status}=%s,0,-{col:difference})' % DUE, 11),
    CA('check', 'Check', 'text', 'IF({col:status}=%s,%s,IF(ABS({col:difference})>{set:diff_tolerance},%s,%s))' % (DUE, ck('Not paid yet'), ck('Paid differently'), ck('Paid as due')), 15), DPH(), OWN(), CO()],
    D.diffs_d(), 60, [A('adjust', '<> 0', 'warn')]))
# 15 capacity
OV = lambda: ('SUMPRODUCT(({range:oncall.doula}={col:doula})*(({range:oncall.oncall_end}+ME-ABS({range:oncall.oncall_end}-ME))/2-({range:oncall.oncall_start}+MB+ABS({range:oncall.oncall_start}-MB))/2+1>0)*'
              '(({range:oncall.oncall_end}+ME-ABS({range:oncall.oncall_end}-ME))/2-({range:oncall.oncall_start}+MB+ABS({range:oncall.oncall_start}-MB))/2+1))').replace('ME', '(EDATE({col:month},1)-1)').replace('MB', '{col:month}')
BOTH = tok('service', 'Both')
tables.append(T('cap', 'Capacity by Doula', 'Capacity by doula and month against each doula cap',
    'One row per doula and month: clients with a due date, on-call windows and days, the most due dates a month and the places left, with a check and a share used; the next months show who can take a client.', [
    C('cap_id', 'Cap ID', 'text', 10, required=True), LST('doula', 'Doula', 'doula', 17), C('month', 'Month', 'date', 11),
    CA('clients', 'Clients due', 'int', 'COUNTIFS({range:clients.doula},{col:doula},{range:clients.edd},">="&{col:month},{range:clients.edd},"<"&EDATE({col:month},1),{range:clients.status},"<>"&%s)' % tok('cstatus', 'Cancelled'), 8),
    CA('windows', 'On-call windows', 'int', 'COUNTIFS({range:oncall.doula},{col:doula},{range:oncall.oncall_start},"<"&EDATE({col:month},1),{range:oncall.oncall_end},">="&{col:month})', 8),
    CA('oncall_days', 'On-call days', 'int', OV(), 8),
    CA('cap', 'Most due dates', 'int', 'IF(IFERROR(INDEX({range:team.cap_births},MATCH({col:doula},{range:team.name},0)),0)>0,IFERROR(INDEX({range:team.cap_births},MATCH({col:doula},{range:team.name},0)),0),{set:pp_clients_month})', 8),
    CA('free', 'Places left', 'int', 'MAX(0,{col:cap}-{col:clients})', 8), CA('share_used', 'Share used', 'pct', 'IF({col:cap}>0,{col:clients}/{col:cap},0)', 8),
    CA('flag', 'Check', 'text', 'IF({col:clients}>{col:cap},%s,IF({col:clients}={col:cap},%s,%s))' % (ck('Over capacity'), ck('At capacity'), ck('Room for more')), 15),
    CA('service', 'Service', 'text', LKT('team.service', 'team.name', 'doula'), 11),
    CA('free_birth', 'Places left, birth', 'int', 'IF(OR({col:service}=%s,{col:service}=%s),{col:free},0)' % (BOTH, tok('service', 'Birth')), 8),
    CA('free_pp', 'Places left, postpartum', 'int', 'IF(OR({col:service}=%s,{col:service}=%s),{col:free},0)' % (BOTH, tok('service', 'Postpartum')), 8),
    CA('free_both', 'Places left, both', 'int', 'IF({col:service}=%s,{col:free},0)' % BOTH, 8),
    CA('next_month', 'Next month', 'int', 'IF({col:month}=EDATE(%s,1),1,0)' % MS, 6), DPH(), OWN(), CO()],
    D.cap_d(), 200, [A('flag', '= ' + ck('Over capacity'), 'bad')]))
# 16 hours by doula
tables.append(T('hrs', 'Hours by Doula', 'Hours by doula and month with pay per hour worked',
    'One row per doula and month: visit hours, birth hours and the pay for them; the pay per hour worked fills in (the owner-doula is paid by owner draw, so pay shows 0).', [
    LST('doula', 'Doula', 'doula', 17, required=True), C('month', 'Month', 'date', 11),
    CA('visit_hours', 'Visit hours', 'num', 'SUMIFS({range:visits.hours},{range:visits.doula},{col:doula},{range:visits.month},{col:month})', 9),
    CA('birth_hours', 'Birth hours', 'num', 'SUMIFS({range:births.hours},{range:births.doula},{col:doula},{range:births.month},{col:month})', 9),
    CA('total_hours', 'Total hours', 'num', '{col:visit_hours}+{col:birth_hours}', 9), CA('pay', 'Pay for client work', 'money', '%s+%s' % (PAYM('pay_due', PC), PAYM('pay_due', PH)), 11),
    CA('pay_hour', 'Pay per hour worked', 'money', 'IF({col:total_hours}>0,ROUND({col:pay}/{col:total_hours},2),0)', 11)], D.hrs_d(), 150))
# 17 split proposals
tables.append(T('splits', 'Split Proposals', 'Split proposals with the effect on the agency margin',
    'One row per proposed share: doula, proposed agency share, clients a year and the average birth part of a package; the margin change, the margin per client after and the verdict fill in.', [
    C('split_id', 'Split ID', 'text', 10, required=True), LST('doula', 'Doula', 'cdoula', 17), C('proposed_on', 'Proposed on', 'date', 11), C('new_share', 'New agency share', 'pct', 9), C('clients_year', 'Clients a year', 'int', 8),
    C('avg_package', 'Average birth part', 'money', 11),
    CA('current_share', 'Current share', 'pct', LKN('doulas.agency_share', 'doulas.doula', 'doula'), 9), CA('margin_change', 'Owner margin change a year', 'money', 'ROUND({col:clients_year}*{col:avg_package}*({col:new_share}-{col:current_share}),0)', 12),
    CA('mpc_now', 'Margin per client now', 'money', 'IFERROR(ROUND(INDEX({range:margin_doula.margin},MATCH({col:doula},{range:margin_doula.doula},0))/INDEX({range:margin_doula.clients},MATCH({col:doula},{range:margin_doula.doula},0)),2),0)', 11),
    CA('mpc_after', 'Margin per client after', 'money', 'ROUND({col:mpc_now}+{col:avg_package}*({col:new_share}-{col:current_share}),2)', 11),
    CA('counter_share', 'Share that keeps your target', 'pct', 'MAX(0,ROUND({col:current_share}+({set:target_margin_client}-{col:mpc_now})/{col:avg_package},3))', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:mpc_after}>={set:target_margin_client},%s,%s)' % (ck('Accept'), ck('Counter')), 12), DPH(), OWN(), CO()], D.splits_d(), 60, [A('margin_change', '< 0', 'warn')]))
# 18 profit by doula and month
tables.append(T('profit', 'Doula Profit by Month', 'Profit by doula and month',
    'One row per contracted doula and month: revenue (gross), doula pay, mileage paid and the margin before overhead.', [
    LST('doula', 'Doula', 'cdoula', 17, required=True), C('month', 'Month', 'date', 11),
    CA('revenue', 'Revenue', 'money', '%s+%s' % (PAYM('gross', PC), PAYM('gross', PH)), 11), CA('pay', 'Doula pay', 'money', '%s+%s' % (PAYM('pay_due', PC), PAYM('pay_due', PH)), 11),
    CA('mileage', 'Mileage paid', 'money', PAYM('pay_due', MIL), 11), CA('margin', 'Margin before overhead', 'money', '{col:revenue}-{col:pay}-{col:mileage}', 12)], D.profit_d(), 150))
# 19 owner load
ONW = lambda c: 'SUMIFS({range:owner_time.%s},{range:owner_time.month},{col:month})' % c
tables.append(T('owner_load', 'Owner Load by Month', 'Owner load as a doula and a manager, by month',
    'One row per month: own-client, management and admin hours from the Owner Time Log, the owner draw per hour worked and the admin cost per new client against your overhead setting.', [
    C('month', 'Month', 'date', 11, required=True), CA('own_hours', 'Own client hours', 'num', ONW('own_client_hours'), 9), CA('mgmt_hours', 'Management hours', 'num', ONW('management_hours'), 9),
    CA('admin_hours', 'Admin hours', 'num', ONW('admin_hours'), 9), CA('total_hours', 'Total hours', 'num', '{col:own_hours}+{col:mgmt_hours}+{col:admin_hours}', 9),
    CA('pay_hour', 'Owner pay per hour worked', 'money', 'IF({col:total_hours}>0,ROUND({set:owner_draw}/{col:total_hours},2),0)', 11),
    CA('new_clients', 'Clients signed', 'int', 'COUNTIFS({range:clients.signed_on},">="&{col:month},{range:clients.signed_on},"<"&EDATE({col:month},1))', 8),
    CA('admin_cost_client', 'Admin cost per new client', 'money', 'IF({col:new_clients}>0,ROUND({set:admin_rate}*{set:admin_hours_week}*{set:admin_client_share}*52/12/{col:new_clients},2),0)', 11),
    CA('overhead_client', 'Overhead setting per client', 'money', '{set:agency_cost_client}', 11), OWN(), ADM(), ACC(), CO()], D.owner_load_d(), 60))
# 20 backup pay by month
tables.append(T('backup_month', 'Backup Pay by Month', 'Backup pay by month: stipends and call-outs',
    'One row per month: backup stipends and call-out pay from the Pay Lines, the call-outs, and the rota weeks and stipend from the Backup Rota to check them.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('stipend', 'Stipends', 'money', 'SUMIFS({range:pay.pay_due},{range:pay.month},{col:month},{range:pay.basis},%s)' % STI, 11),
    CA('call_outs', 'Call-out pay', 'money', 'SUMIFS({range:pay.pay_due},{range:pay.month},{col:month},{range:pay.basis},%s)' % CALL, 11), CA('total', 'Total backup pay', 'money', '{col:stipend}+{col:call_outs}', 11),
    CA('call_out_n', 'Call-outs', 'int', 'COUNTIFS({range:pay.month},{col:month},{range:pay.basis},%s)' % CALL, 8), CA('rota_weeks', 'Rota weeks', 'int', 'COUNTIFS({range:rota.month},{col:month})', 8),
    CA('rota_stipend', 'Stipend on the rota', 'money', 'SUMIFS({range:rota.stipend},{range:rota.month},{col:month})', 11), CA('stipend_diff', 'Stipends paid less rota', 'money', '{col:stipend}-{col:rota_stipend}', 11), OWN(), ACC(), CO()],
    D.backup_month_d(), 60))
assert len(tables) == 20
