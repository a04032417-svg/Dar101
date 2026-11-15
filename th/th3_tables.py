"""Therapy part 3: settings and the 20 tables with calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th3_lists import *
import th3_data as D

YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
IS = lambda x: tok('invst', x)
IDSET = {'TH-01': '{set:owner_id}', 'TH-07': '{set:coordinator_id}', 'TH-08': '{set:accountant_id}'}
TEAMNM = lambda sid: 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.staff_id},0))&"","")' % IDSET[sid]
TEAMPH = lambda sid: 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.staff_id},0))&"","")' % IDSET[sid]
PRACTICE = CA('practice', 'Practice', 'text', '{set:company}&""', 24)

settings = [
    S('company', 'Your practice name', 'text', COMPANY), S('late_fee_pct', 'Share of the fee charged for a late cancel or no-show', 'pct', 0.5),
    S('late_cancel_hours', 'Hours of notice that avoid a late-cancel fee', 'int', 24), S('invoice_days', 'Days to pay an invoice (payment terms)', 'int', 14),
    S('card_fee_pct', 'Card fee, share of a card payment', 'pct', 0.025), S('deposit', 'Deposit for a new self-pay client', 'money', 50),
    S('net_collection_target', 'Target Net collection rate', 'pct', 0.95), S('max_days_ar', 'Most Days in A/R you accept', 'int', 40),
    S('reminder_gap_days', 'Days between payment reminders', 'int', 7), S('final_notice_days', 'Days after the due date for the final notice', 'int', 21),
    S('writeoff_limit', 'Balance above which a write-off needs the owner', 'money', 100), S('chase_cost', 'Cost of one chase attempt (time and message)', 'money', 8),
    S('rise_notice_days', 'Days of notice before a fee rise', 'int', 60), S('package_margin', 'Margin you want on a package', 'pct', 0.30),
    S('owner_id', 'Staff ID of the owner on the Team sheet', 'text', 'TH-01'), S('plan_max_share', 'Largest instalment, share of a month of fees', 'pct', 0.25),
    S('sliding_review_months', 'Months between sliding-scale reviews', 'int', 12), S('coordinator_id', 'Staff ID of the coordinator on the Team sheet', 'text', 'TH-07'),
    S('accountant_id', 'Staff ID of the accountant on the Team sheet', 'text', 'TH-08')]
assert 3 <= len(settings) <= 20

def T_(key, sheet, title, hint, cols, demo, rows, alerts=None):
    assert len(hint) <= 200, (key, len(hint))
    return T(key, sheet, title, hint, cols, demo, rows, alerts)

# ---------------------------------------------------------------- invoices
AGE = '{col:age_days}'
inv_cols = [C('invoice_id', 'Invoice ID', 'text', 10, required=True), C('month', 'Service month', 'date', 11), REF('client', 'Client', 'clients.client', 24), LST('fee_type', 'Fee type', 'feetype', 16),
    LST('clinician', 'Clinician', 'clin', 16), C('sessions', 'Sessions', 'int', 9), C('amount', 'Amount', 'money', 12), C('deposit_applied', 'Deposit applied', 'num', 11), C('issued_on', 'Issued on', 'date', 11),
    C('due_date', 'Due date', 'date', 11), C('paid_amount', 'Paid amount', 'money', 12), C('paid_on', 'Paid on', 'date', 11), LST('method', 'Pay method', 'paym', 13), LST('status', 'Status', 'invst', 12),
    CA('amount_due', 'Amount due', 'money', 'ROUND({col:amount}-{col:deposit_applied},2)', 12),
    CA('balance', 'Balance', 'money', 'IF({col:status}=%s,0,MAX(0,ROUND({col:amount}-{col:deposit_applied}-{col:paid_amount},2)))' % IS('Written off'), 11),
    CA('days_overdue', 'Days overdue', 'int', 'IF(AND({col:balance}>0,{col:status}<>%s),MAX(0,{today}-{col:due_date}),0)' % IS('On plan'), 10),
    CA('age_days', 'Age, days', 'int', 'IF({col:balance}>0,{today}-{col:issued_on},0)', 9),
    CA('age_band', 'A/R aging band', 'text', 'IF({col:balance}<=0,%s,IF(%s<=30,%s,IF(%s<=60,%s,IF(%s<=90,%s,%s))))' % (ca('Settled'), AGE, ab('0-30'), AGE, ab('31-60'), AGE, ab('61-90'), ab('90+')), 13),
    CA('timing', 'Payment timing', 'text', 'IF({col:status}=%s,%s,IF({col:balance}<=0,IF({col:paid_on}<={col:due_date},%s,%s),IF({col:status}=%s,%s,IF({col:due_date}<{today},%s,%s))))' % (
        IS('Written off'), ca('Written off'), ca('Paid on time'), ca('Paid late'), IS('On plan'), ca('On plan'), ca('Overdue'), ca('Not yet due')), 14),
    CA('current_balance', 'Balance not overdue', 'money', 'IF({col:days_overdue}=0,{col:balance},0)', 12),
    CA('days_to_pay', 'Days to pay', 'int', 'IF({col:paid_on}>0,{col:paid_on}-{col:issued_on},"")', 9),
    CA('client_id', 'Client ID', 'text', LKT('clients.client_id', 'clients.client', 'client'), 10),
    CA('clinician_phone', 'Clinician phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:clinician},{range:team.name},0))&"","")', 18), PRACTICE]

# ---------------------------------------------------------------- payments
pay_cols = [C('payment_id', 'Payment ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('client', 'Client', 'text', 24), LST('kind', 'Kind', 'payk', 14), C('ref', 'Reference', 'text', 10),
    LST('method', 'Method', 'paym', 13), C('amount', 'Amount', 'money', 12), C('card_fee', 'Card fee', 'money', 10),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('net_received', 'Net received', 'money', '{col:amount}-{col:card_fee}', 12),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18), PRACTICE]

# ---------------------------------------------------------------- A/R aging by client
SCORE = '{range:ar_clients.chase_score}'
OPEN2 = '(({range:invoices.status}=%s)+({range:invoices.status}=%s))' % (IS('Unpaid'), IS('Part paid'))
OLD = 'SUMPRODUCT(MAX(({range:invoices.client}={col:client})*%s*(100000-{range:invoices.due_date})))' % OPEN2
PRM = 'SUMPRODUCT(MAX(({range:promises.client}={col:client})*({range:promises.outcome}=%s)*(100000-{range:promises.promised_on})))' % tok('promise', 'Pending')
LASTL = 'SUMPRODUCT(MAX(({range:promises.client}={col:client})*{range:promises.logged_on}))'
ar_cols = [C('ar_id', 'Row ID', 'text', 9, required=True), REF('client', 'Client', 'clients.client', 24), REF('chased_by', 'Chased by', 'team.name', 16),
    CA('fee_type', 'Fee type', 'text', LKT('clients.fee_type', 'clients.client', 'client'), 16),
    CA('invoiced', 'Invoiced', 'money', 'SUMIFS({range:invoices.amount_due},{range:invoices.client},{col:client})', 12),
    CA('paid', 'Paid', 'money', 'SUMIFS({range:invoices.paid_amount},{range:invoices.client},{col:client})', 12),
    CA('balance', 'Balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.client},{col:client})', 11),
    CA('overdue', 'Overdue balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.client},{col:client},{range:invoices.days_overdue},">0")', 12),
    CA('oldest_due', 'Oldest unpaid due date', 'date', 'IF(%s=0,"",100000-%s)' % (OLD, OLD), 12),
    CA('days_overdue', 'Days past due', 'int', 'IF({col:oldest_due}="","",MAX(0,{today}-{col:oldest_due}))', 10),
    CA('age_band', 'A/R aging band', 'text', 'IF({col:balance}<=0,%s,IF({col:oldest_due}="",%s,IF({col:days_overdue}+{set:invoice_days}<=30,%s,IF({col:days_overdue}+{set:invoice_days}<=60,%s,IF({col:days_overdue}+{set:invoice_days}<=90,%s,%s)))))' % (
        ca('Settled'), ab('0-30'), ab('0-30'), ab('31-60'), ab('61-90'), ab('90+')), 13),
    CA('next_promised', 'Next promised date', 'date', 'IF(%s=0,"",100000-%s)' % (PRM, PRM), 12),
    CA('last_outcome', 'Last promise outcome', 'text', 'IF(%s=0,%s,IF(COUNTIFS({range:promises.client},{col:client},{range:promises.logged_on},%s,{range:promises.outcome},%s)>0,%s,IF(COUNTIFS({range:promises.client},{col:client},{range:promises.logged_on},%s,{range:promises.outcome},%s)>0,%s,%s)))' % (
        LASTL, ca('No promise logged'), LASTL, tok('promise', 'Broken'), tok('promise', 'Broken'), LASTL, tok('promise', 'Kept'), tok('promise', 'Kept'), tok('promise', 'Pending')), 14),
    CA('broken', 'Broken promises', 'int', 'COUNTIFS({range:promises.client},{col:client},{range:promises.outcome},%s)' % tok('promise', 'Broken'), 9),
    CA('chase_score', 'Chase score', 'num', 'IF({col:overdue}>0,{col:overdue}*MAX(1,IF(ISNUMBER({col:days_overdue}),{col:days_overdue},0))+VALUE(RIGHT({col:ar_id},3))/100000,0)', 11),
    CA('chase_rank', 'Chase rank', 'int', 'IF({col:chase_score}>0,1+SUMPRODUCT(ISNUMBER(%s)*(%s>{col:chase_score})),"")' % (SCORE, SCORE), 9),
    CA('chase_flag', 'Chase flag', 'text', 'IF({col:balance}<=0,%s,IF({col:chase_score}=0,%s,IF({col:chase_rank}<=5,%s,%s)))' % (ca('Settled'), ca('Not yet due'), vb('Chase first'), vc('Chase next')), 12),
    CA('card_on_file', 'Card on file', 'text', LKT('clients.card_on_file', 'clients.client', 'client'), 10),
    CA('coordinator_phone', 'Coordinator phone', 'text', TEAMPH('TH-07'), 18), CA('coordinator_name', 'Coordinator', 'text', TEAMNM('TH-07'), 22), CA('owner_phone', 'Owner phone', 'text', TEAMPH('TH-01'), 18), CA('owner_name', 'Owner', 'text', TEAMNM('TH-01'), 22), PRACTICE]

# ---------------------------------------------------------------- clients
def BAL(band): return 'SUMIFS({range:invoices.balance},{range:invoices.client},{col:client},{range:invoices.age_band},%s)' % ab(band)
cli_cols = [C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18), C('client_type', 'Client type', 'text', 12),
    LST('service', 'Usual service', 'svc', 18), LST('clinician', 'Clinician', 'clin', 16), LST('fee_type', 'Fee type', 'feetype', 16), C('sliding_pct', 'Sliding share of fee', 'pct', 10),
    LST('pay_method', 'Pay method', 'paym', 13), C('claim_back', 'Claim back', 'bool', 9), C('card_on_file', 'Card on file', 'bool', 9), C('autopay', 'Autopay', 'bool', 9),
    C('pays_by_instalment', 'Pays by instalment', 'bool', 11), LST('status', 'Status', 'cstatus', 12), C('first_session', 'First session', 'date', 11),
    CA('invoices_n', 'Invoices', 'int', 'COUNTIFS({range:invoices.client},{col:client})', 9),
    CA('invoiced', 'Invoiced to date', 'money', 'SUMIFS({range:invoices.amount_due},{range:invoices.client},{col:client})', 13),
    CA('paid_to_date', 'Paid on invoices', 'money', 'SUMIFS({range:invoices.paid_amount},{range:invoices.client},{col:client})', 13),
    CA('balance', 'Balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.client},{col:client})', 11),
    CA('overdue', 'Overdue balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.client},{col:client},{range:invoices.days_overdue},">0")', 12),
    CA('bal_0_30', 'Balance 0-30 days', 'money', BAL('0-30'), 12), CA('bal_31_60', 'Balance 31-60 days', 'money', BAL('31-60'), 12), CA('bal_61_90', 'Balance 61-90 days', 'money', BAL('61-90'), 12),
    CA('bal_90p', 'Balance 90+ days', 'money', BAL('90+'), 12),
    CA('account_flag', 'Account check', 'text', 'IF({col:balance}<=0,%s,IF({col:overdue}>0,%s,%s))' % (ca('Up to date'), ca('Overdue'), ca('Balance due')), 12), PRACTICE]

# ---------------------------------------------------------------- chargeable sessions
ses_cols = [C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('time', 'Time', 'time', 8), REF('client', 'Client', 'clients.client', 24), LST('service', 'Service', 'svc', 18),
    LST('clinician', 'Clinician', 'clin', 16), LST('status', 'Status', 'sstatus', 12), LST('fee_type', 'Fee type', 'feetype', 16), C('fee', 'List fee', 'money', 10), C('charge', 'Charge', 'money', 10),
    C('client_amount', 'Client amount', 'money', 12), C('package_id', 'Package ID', 'text', 10), C('fee_waived', 'Fee waived', 'bool', 9),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('billing_flag', 'Billing check', 'text', 'IF({col:fee}=0,%s,IF({col:fee_waived}=%s,%s,IF({col:client_amount}=0,%s,IF({col:date}>=%s,%s,%s))))' % (ca('No fee'), YES, ca('Fee waived'), ca('Nothing to bill'), MS, ca('On next invoice'), ca('Invoiced')), 14),
    CA('clinician_phone', 'Clinician phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:clinician},{range:team.name},0))&"","")', 18), PRACTICE]

# ---------------------------------------------------------------- promises, reminders
pro_cols = [C('promise_id', 'Promise ID', 'text', 10, required=True), C('invoice_id', 'Invoice ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), C('logged_on', 'Logged on', 'date', 11),
    C('promised_on', 'Promised for', 'date', 11), LST('method', 'Logged by', 'pmeth', 10), LST('outcome', 'Outcome', 'promise', 10),
    CA('due_date', 'Invoice due date', 'date', LKD('invoices.due_date', 'invoices.invoice_id', 'invoice_id'), 12),
    CA('days_to_promise', 'Days from due date to promise', 'int', 'IF({col:due_date}="","",{col:promised_on}-{col:due_date})', 12),
    CA('promise_flag', 'Promise check', 'text', 'IF({col:outcome}=%s,IF({col:promised_on}<{today},%s,%s),%s)' % (tok('promise', 'Pending'), ca('Chase now'), ca('Waiting'), ca('Closed')), 12), PRACTICE]
rem_cols = [C('reminder_id', 'Reminder ID', 'text', 10, required=True), C('invoice_id', 'Invoice ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), C('reminder_no', 'Reminder number', 'int', 9),
    C('sent_on', 'Sent on', 'date', 11), LST('method', 'Method', 'pmeth', 10), C('paid_after', 'Paid after it', 'bool', 9),
    CA('due_date', 'Invoice due date', 'date', LKD('invoices.due_date', 'invoices.invoice_id', 'invoice_id'), 12),
    CA('days_after_due', 'Days after due date', 'int', 'IF({col:due_date}="","",{col:sent_on}-{col:due_date})', 11), PRACTICE]

# ---------------------------------------------------------------- plans, instalments
plan_cols = [C('plan_id', 'Plan ID', 'text', 9, required=True), REF('client', 'Client', 'clients.client', 24), C('start_date', 'Start date', 'date', 11), C('balance', 'Balance', 'money', 11),
    C('instalments', 'Instalments', 'int', 10), C('instalment', 'Instalment', 'money', 11), C('paid_instalments', 'Paid instalments', 'int', 10), C('next_due', 'Next due', 'date', 11),
    C('invoices', 'Invoices', 'text', 26), LST('status', 'Status', 'planst', 11),
    CA('balance_left', 'Balance left', 'money', 'IF({col:status}=%s,0,MAX(0,ROUND({col:balance}-{col:instalment}*{col:paid_instalments},2)))' % tok('planst', 'Completed'), 12),
    CA('end_date', 'Last instalment due', 'date', 'EDATE({col:start_date},{col:instalments}-1)', 12),
    CA('late_instalments', 'Late instalments', 'int', 'COUNTIFS({range:instalments.plan_id},{col:plan_id},{range:instalments.late_flag},%s)' % ca('Late'), 10), PRACTICE]
ins_cols = [C('inst_id', 'Instalment ID', 'text', 10, required=True), REF('plan_id', 'Plan', 'plans.plan_id', 9), C('due_date', 'Due date', 'date', 11), C('amount', 'Amount', 'money', 11), C('paid_on', 'Paid on', 'date', 11),
    CA('client', 'Client', 'text', LKT('plans.client', 'plans.plan_id', 'plan_id'), 24),
    CA('late_flag', 'Payment check', 'text', 'IF({col:paid_on}>0,IF({col:paid_on}<={col:due_date},%s,%s),IF({col:due_date}<{today},%s,%s))' % (ca('Paid on time'), ca('Paid late'), ca('Late'), ca('Due later')), 12),
    CA('days_late', 'Days late', 'int', 'IF({col:paid_on}>0,MAX(0,{col:paid_on}-{col:due_date}),MAX(0,{today}-{col:due_date}))', 9),
    CA('phone', 'Client phone', 'text', 'IFERROR(INDEX({range:clients.phone},MATCH({col:client},{range:clients.client},0))&"","")', 18),
    CA('coordinator_phone', 'Coordinator phone', 'text', TEAMPH('TH-07'), 18), CA('coordinator_name', 'Coordinator', 'text', TEAMNM('TH-07'), 22), PRACTICE]

# ---------------------------------------------------------------- packages
pkg_cols = [C('package_id', 'Package ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 24), LST('kind', 'Kind', 'pkkind', 12), C('sessions', 'Sessions', 'int', 9), C('price', 'Price', 'money', 11),
    C('bought_on', 'Bought on', 'date', 11), C('used', 'Sessions used', 'int', 9), C('expires_on', 'Expires on', 'date', 11), LST('status', 'Status', 'pkst', 10),
    CA('sessions_left', 'Sessions left', 'int', 'MAX(0,{col:sessions}-{col:used})', 9), CA('value_left', 'Value left', 'money', 'ROUND({col:price}*MAX(0,{col:sessions}-{col:used})/{col:sessions},2)', 11),
    CA('days_to_expiry', 'Days to expiry', 'int', '{col:expires_on}-{today}', 10),
    CA('expiry_check', 'Expiry check', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:days_to_expiry}<=30,%s,%s)))' % (tok('pkst', 'Used up'), ca('Used up'), tok('pkst', 'Expired'), ca('Expired'), ca('Expires in 30 days'), ca('Active')), 14),
    CA('coordinator_phone', 'Coordinator phone', 'text', TEAMPH('TH-07'), 18), CA('coordinator_name', 'Coordinator', 'text', TEAMNM('TH-07'), 22), CA('accountant_phone', 'Accountant phone', 'text', TEAMPH('TH-08'), 18), CA('accountant_name', 'Accountant', 'text', TEAMNM('TH-08'), 22), PRACTICE]

# ---------------------------------------------------------------- aging by month, fees, notices, bands, assessments, write-offs
arm_cols = [C('ageing_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('as_of', 'As of', 'date', 11), LST('band', 'Age band, days', 'ageband', 12), C('invoices', 'Open invoices', 'int', 10),
    C('balance', 'Balance', 'money', 12), CA('share_of_balance', 'Share of the month balance', 'pct', 'IFERROR({col:balance}/SUMIFS({range:ar_months.balance},{range:ar_months.month},{col:month}),0)', 12)]
FEE9 = [('fee_intake', 'Intake assessment'), ('fee_individual', 'Individual session'), ('fee_extended', 'Extended individual'), ('fee_couples', 'Couples session'), ('fee_family', 'Family session'),
        ('fee_child', 'Child session'), ('fee_speech', 'Speech therapy'), ('fee_behaviour', 'Behaviour therapy'), ('fee_review', 'Review session')]
fee_cols = [C('fee_id', 'Fee ID', 'text', 9, required=True), C('year', 'Year', 'int', 8), LST('service', 'Service', 'svcall', 18), C('fee', 'Fee', 'money', 10), C('minutes', 'Minutes', 'int', 9),
    CA('fee_per_hour', 'Fee per hour', 'money', 'ROUND({col:fee}/{col:minutes}*60,2)', 11),
    CA('vs_last_year', 'Change on last year', 'pct', 'IFERROR({col:fee}/SUMIFS({range:fees.fee},{range:fees.service},{col:service},{range:fees.year},{col:year}-1)-1,"")', 11)] + [
    CA(k, l, 'money', 'SUMIFS({range:fees.fee},{range:fees.service},%s,{range:fees.year},{col:year})' % tok('svcall', l), 11) for k, l in FEE9] + [CA('owner_phone', 'Owner phone', 'text', TEAMPH('TH-01'), 18), CA('owner_name', 'Owner', 'text', TEAMNM('TH-01'), 22), PRACTICE]
not_cols = [C('notice_id', 'Notice ID', 'text', 9, required=True), REF('client', 'Client', 'clients.client', 24), LST('service', 'Service', 'svc', 18), C('old_fee', 'Old fee', 'money', 10), C('new_fee', 'New fee', 'money', 10),
    C('sent_on', 'Notice sent on', 'date', 11), C('effective_date', 'Effective date', 'date', 11), CA('rise_share', 'Rise', 'pct', '{col:new_fee}/{col:old_fee}-1', 8),
    CA('notice_days', 'Notice, days', 'int', '{col:effective_date}-{col:sent_on}', 9),
    CA('notice_check', 'Notice check', 'text', 'IF({col:notice_days}>={set:rise_notice_days},%s,%s)' % (ca('Notice given'), ca('Short notice')), 12), PRACTICE]
band_cols = [C('band', 'Band', 'text', 9, required=True), C('income_from', 'Income per person from', 'money', 13), C('income_to', 'Income per person to', 'money', 13), C('share', 'Share of the fee', 'pct', 10),
    CA('example_fee', 'Individual session fee', 'money', 'ROUND({col:share}*SUMIFS({range:fees.fee},{range:fees.service},%s,{range:fees.year},YEAR({today})),2)' % tok('svcall', 'Individual session'), 12)]
asm_cols = [C('assess_id', 'Assessment ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 24), C('date', 'Assessed on', 'date', 11), C('household_size', 'Household size', 'int', 9),
    REF('income_band', 'Income band', 'bands.band', 10), C('share_agreed', 'Share agreed', 'pct', 9), C('review_date', 'Review date', 'date', 11),
    CA('service', 'Usual service', 'text', LKT('clients.service', 'clients.client', 'client'), 18),
    CA('fee_per_session', 'Fee per session', 'money', 'ROUND({col:share_agreed}*SUMIFS({range:fees.fee},{range:fees.service},{col:service},{range:fees.year},YEAR({today})),2)', 11),
    CA('review_check', 'Review check', 'text', 'IF(COUNTIFS({range:assessments.client},{col:client},{range:assessments.date},">"&{col:date})>0,%s,IF({col:review_date}<{today},%s,IF({col:review_date}<{today}+60,%s,%s)))' % (
        ca('Superseded'), ca('Review due'), ca('Review within 60 days'), ca('Current')), 14), PRACTICE]
wo_cols = [C('writeoff_id', 'Write-off ID', 'text', 10, required=True), C('invoice_id', 'Invoice ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), C('date', 'Written off on', 'date', 11),
    C('amount', 'Amount', 'money', 11), C('reason', 'Reason', 'text', 24), C('approved_by', 'Approved by', 'text', 16),
    CA('owner_phone', 'Owner phone', 'text', TEAMPH('TH-01'), 18), CA('owner_name', 'Owner', 'text', TEAMNM('TH-01'), 22), CA('accountant_phone', 'Accountant phone', 'text', TEAMPH('TH-08'), 18), CA('accountant_name', 'Accountant', 'text', TEAMNM('TH-08'), 22), PRACTICE]

# ---------------------------------------------------------------- billing summary, collection gap, card fees, team
def ARB(band): return 'SUMIFS({range:ar_months.balance},{range:ar_months.month},{col:month},{range:ar_months.band},%s)' % ab(band)
SUM3 = 'SUMIFS({range:billing.invoiced},{range:billing.month},">="&EDATE({col:month},-2),{range:billing.month},"<="&{col:month})'
CNT3 = 'COUNTIFS({range:billing.month},">="&EDATE({col:month},-2),{range:billing.month},"<="&{col:month})'
bill_cols = [C('bill_id', 'Row ID', 'text', 8, required=True), C('month', 'Issue month', 'date', 11), C('sessions_charged', 'Sessions charged', 'int', 10), C('invoiced', 'Invoiced', 'money', 12),
    C('concessions', 'Concessions given', 'money', 12), C('collected', 'Collected', 'money', 12), C('written_off', 'Written off', 'num', 11), C('outstanding_end', 'Owed at month end', 'money', 12),
    CA('gross_value', 'Value at list fees', 'money', '{col:invoiced}+{col:concessions}', 12),
    CA('collection_rate', 'Client payment collection rate', 'pct', 'IFERROR({col:collected}/{col:gross_value},0)', 12),
    CA('net_rate', 'Net collection rate', 'pct', 'IFERROR({col:collected}/{col:invoiced},0)', 11),
    CA('unpaid', 'Unpaid', 'money', 'MAX(0,{col:invoiced}-{col:collected}-{col:written_off})', 11),
    CA('days_in_ar', 'Days in A/R', 'num', 'IFERROR({col:outstanding_end}/%s*30.4*%s,0)' % (SUM3, CNT3), 10),
    CA('net_flag', 'Net rate check', 'text', 'IF({col:net_rate}>={set:net_collection_target},%s,%s)' % (vc('On target'), vc('Below target')), 11),
    CA('ar_0_30', 'A/R 0-30 days', 'money', ARB('0-30'), 11), CA('ar_31_60', 'A/R 31-60 days', 'money', ARB('31-60'), 11), CA('ar_61_90', 'A/R 61-90 days', 'money', ARB('61-90'), 11),
    CA('ar_90p', 'A/R 90+ days', 'money', ARB('90+'), 11),
    CA('owner_phone', 'Owner phone', 'text', TEAMPH('TH-01'), 18), CA('owner_name', 'Owner', 'text', TEAMNM('TH-01'), 22), CA('coordinator_phone', 'Coordinator phone', 'text', TEAMPH('TH-07'), 18), CA('coordinator_name', 'Coordinator', 'text', TEAMNM('TH-07'), 22), CA('accountant_phone', 'Accountant phone', 'text', TEAMPH('TH-08'), 18), CA('accountant_name', 'Accountant', 'text', TEAMNM('TH-08'), 22), PRACTICE]
gap_cols = [C('gap_id', 'Row ID', 'text', 9, required=True), C('month', 'Month of service', 'date', 11), LST('cause', 'Cause', 'gapcause', 16), C('amount', 'Amount not collected', 'money', 13),
    CA('share_of_month', 'Share of the month gap', 'pct', 'IFERROR({col:amount}/SUMIFS({range:gap.amount},{range:gap.month},{col:month}),0)', 12)]
cf_cols = [C('month', 'Month', 'date', 11, required=True), C('all_payments', 'All client payments', 'money', 13), C('card_payments', 'Card payments', 'money', 12), C('card_fees', 'Card fees', 'money', 10),
    CA('card_share', 'Card share of payments', 'pct', 'IFERROR({col:card_payments}/{col:all_payments},0)', 11), CA('fee_rate', 'Fee share of card payments', 'pct', 'IFERROR({col:card_fees}/{col:card_payments},0)', 11),
    CA('net_after_fees', 'Received after card fees', 'money', '{col:all_payments}-{col:card_fees}', 13)]
team_cols = [C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 22), C('team', 'Team', 'text', 12), C('pay_type', 'Pay type', 'text', 16), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'num', 11), C('split_pct', 'Split share', 'pct', 9), C('session_rate', 'Pay per session', 'num', 11),
    C('hourly_rate', 'Hourly rate', 'num', 10), C('session_cap', 'Session cap a week', 'int', 10), C('session_target', 'Session target a week', 'int', 10), C('speciality', 'Speciality', 'text', 30),
    C('country', 'Country', 'text', 14), C('start', 'Start date', 'date', 11)]

tables = [
 T_('invoices', 'Invoices', 'Client invoices with balance, aging band and payment timing',
    'One row per monthly client invoice (the client\'s share, late-cancel fees and deposit applied); amount due, balance, days overdue, A/R aging band and payment timing fill in by themselves.', inv_cols, D.invoices_d(), 2400,
    [A('days_overdue', '> 30', 'bad'), A('days_overdue', '> 0', 'warn'), A('timing', '= ' + ca('Paid late'), 'warn'), A('status', '= ' + IS('Written off'), 'bad')]),
 T_('payments', 'Payments', 'Client payments by card, transfer and cash with card fees',
    'One row per payment received (invoice, package, deposit, plan instalment or group fee); month, the amount after the card fee and the client phone fill in by themselves.', pay_cols, D.payments_d(), 2800,
    [A('card_fee', '> 0', 'warn')]),
 T_('ar_clients', 'AR Aging by Client', 'A/R (money owed) by client with the chase-first rank',
    'One row per client followed: invoiced, paid, balance, oldest unpaid due date, next promised date, last promise outcome and and a chase rank (overdue balance times days past due) fill in by themselves.',
    ar_cols, D.ar_clients_d(), 500, [A('chase_rank', '<= 5', 'bad'), A('days_overdue', '> 30', 'bad'), A('days_overdue', '> 0', 'warn')]),
 T_('clients', 'Client Accounts', 'Client accounts: fee type, card on file and balance',
    'One row per client: sliding share, pay method, card on file, autopay and instalments are typed; invoices, paid, balance, overdue balance, aging buckets and an account check fill in by themselves.',
    cli_cols, D.clients_d(), 700, [A('account_flag', '= ' + ca('Overdue'), 'bad'), A('account_flag', '= ' + ca('Balance due'), 'warn')]),
 T_('sessions', 'Chargeable Sessions', 'Chargeable sessions and what goes on the next invoice',
    'One row per attended, late-cancelled or no-show session of the last 45 days with its list fee, charge and client amount; a billing check shows what is on the next invoice.', ses_cols, D.sessions_d(), 1200,
    [A('billing_flag', '= ' + ca('No fee'), 'bad'), A('billing_flag', '= ' + ca('On next invoice'), 'good'), A('status', '= ' + tok('sstatus', 'Late cancel'), 'warn'), A('status', '= ' + tok('sstatus', 'No-show'), 'bad')]),
 T_('promises', 'Payment Promises', 'Payment promises with promised date and outcome',
    'One row per promise to pay: the invoice, when it was logged, the promised date and the outcome; days from the due date to the promise and a promise check fill in by themselves.', pro_cols, D.promises_d(), 400,
    [A('outcome', '= ' + tok('promise', 'Broken'), 'bad'), A('promise_flag', '= ' + ca('Chase now'), 'bad')]),
 T_('reminders', 'Payment Reminders', 'Payment reminders sent and whether the invoice was paid',
    'One row per reminder sent (number 1 to 3) with the method and whether the invoice was paid afterwards; the invoice due date and the days after it fill in by themselves.', rem_cols, D.reminders_d(), 500,
    [A('reminder_no', '>= 3', 'bad')]),
 T_('plans', 'Payment Plans', 'Payment plans with instalments and balance left',
    'One row per payment plan: the balance agreed, instalments, amount and paid instalments; balance left, last instalment date and late instalments fill in by themselves.', plan_cols, D.plans_d(), 100,
    [A('status', '= ' + tok('planst', 'Late'), 'bad'), A('late_instalments', '> 0', 'bad'), A('status', '= ' + tok('planst', 'Completed'), 'good')]),
 T_('instalments', 'Plan Instalments', 'Plan instalments due and paid',
    'One row per plan instalment: the plan, due date, amount and the date paid; the client, a payment check (paid on time, paid late, late, due later) and days late fill in by themselves.', ins_cols, D.instalments_d(), 200,
    [A('late_flag', '= ' + ca('Late'), 'bad'), A('late_flag', '= ' + ca('Paid late'), 'warn')]),
 T_('packages', 'Packages', 'Prepaid packages sold, used and expiring',
    'One row per package of 6 or 10 prepaid sessions: price, sessions used and expiry; sessions left, the value still owed as sessions and an expiry check fill in by themselves.', pkg_cols, D.packages_d(), 300,
    [A('expiry_check', '= ' + ca('Expires in 30 days'), 'warn'), A('expiry_check', '= ' + ca('Expired'), 'bad')]),
 T_('ar_months', 'AR Aging by Month', 'A/R aging buckets at each month end',
    'One row per month end and age band (0-30, 31-60, 61-90, 90+ days since the invoice was issued): open invoices and balance, with each band\'s share of the month balance filled in.', arm_cols, D.ar_months_d(), 100,
    [A('band', '= ' + ab('90+'), 'warn')]),
 T_('fees', 'Fee Schedule', 'Fee schedule by service type and year',
    'One row per service and year: list fee and minutes; fee per hour, the change on last year and this year\'s fee for each service fill in by themselves for the client fee schedule.', fee_cols, D.fees_d(), 100,
    [A('vs_last_year', '> 0', 'good')]),
 T_('fee_notices', 'Fee Rise Notices', 'Fee rise notices to clients with the old and new fee',
    'One row per client and service that received a fee notice: old fee, new fee, date sent and effective date; the rise, days of notice and a notice check fill in by themselves.', not_cols, D.fee_notices_d(), 400,
    [A('notice_check', '= ' + ca('Short notice'), 'warn')]),
 T_('bands', 'Sliding Scale Bands', 'Sliding scale bands: income and share of the fee',
    'Twelve bands of yearly income per person with the share of the list fee each one pays; the fee of an individual session at that share fills in by itself.', band_cols, D.bands_d(), 50, None),
 T_('assessments', 'Sliding Scale Assessments', 'Sliding scale assessments with agreed share and review date',
    'One row per assessment: household size, income band, share agreed and review date; the usual service, the fee per session and a review check (current, due soon, due, superseded) fill in by themselves.',
    asm_cols, D.assessments_d(), 250, [A('review_check', '= ' + ca('Review due'), 'bad'), A('review_check', '= ' + ca('Review within 60 days'), 'warn')]),
 T_('writeoffs', 'Write-offs', 'Write-offs with reason and approval',
    'One row per balance written off: invoice, client, date, amount, reason and who approved it; the owner and accountant phones fill in by themselves for the messages.', wo_cols, D.writeoffs_d(), 100,
    [A('amount', '>= {set:writeoff_limit}', 'warn')]),
 T_('billing', 'Monthly Billing Summary', 'Monthly billing summary: collection rates, Days in A/R',
    'One row per issue month: sessions charged, invoiced, concessions, collected and owed at month end; Client payment collection rate, Net collection rate, Days in A/R and A/R buckets fill in.',
    bill_cols, D.billing_d(), 60, [A('net_flag', '= ' + vc('Below target'), 'warn'), A('days_in_ar', '> {set:max_days_ar}', 'bad')]),
 T_('gap', 'Collection Gap by Cause', 'Money not collected by month and cause',
    'One row per month of service and cause: sliding-scale concessions, waived late fees, write-offs and unpaid balances; each cause\'s share of the month\'s gap fills in by itself.', gap_cols, D.gap_d(), 200, None),
 T_('cardfees', 'Card Fees by Month', 'Card payments and card fees by month',
    'One row per month: all client payments, card payments and card fees; the card share of payments, the fee share and the amount received after card fees fill in by themselves.', cf_cols, D.cardfees_d(), 60,
    [A('fee_rate', '> {set:card_fee_pct}', 'warn')]),
 T_('team', 'Team', 'Team and outside contacts',
    'The 12 people and outside contacts the other sheets look up: clinicians, associate, coordinator, accountant, supervisor, IT support, landlord and cleaner, with phone and pay terms.', team_cols, D.team_d(), 60, None),
]
assert len(tables) == 20
