"""Home care agency suite part 5: settings and the 20 tables (Client Invoices, Deposits and Payers)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc5_lists import *
import hc5_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF_PH(idx, k): return CA(k, 'Phone to message', 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % idx, 18)
def COMPANY_COL(): return CA('company', 'Agency', 'text', '{set:company}&""', 22)
YES = '{list:yesno.yes}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
OPEN_INV = 'OR({col:status}=%s,{col:status}=%s)' % (tok('invst', 'Unpaid'), tok('invst', 'Part paid'))
OPEN_CLM = 'OR({col:status}=%s,{col:status}=%s,{col:status}=%s,{col:status}=%s)' % (tok('clmst', 'Submitted'), tok('clmst', 'Accepted'), tok('clmst', 'Resubmitted'), tok('clmst', 'Rejected'))
PRIV = tok('payer', 'Private pay')

settings = [
    S('company', 'Your agency name', 'text', COMPANY),
    S('invoice_days', 'Payment terms in days (private pay, self-funded)', 'int', INVOICE_DAYS), S('deposit_weeks', 'Weeks of hours held as a deposit', 'int', DEPOSIT_WEEKS),
    S('buffer_weeks', 'Weeks of hours a prepaid balance should cover', 'int', 3), S('hours_tolerance', 'Accepted gap, billed vs agreed hours (example)', 'pct', 0.12),
    S('rate_tolerance', 'Accepted gap to the rate card (example)', 'pct', 0.06),
    S('days_to_pay_private', 'Target days to be paid, private pay', 'int', 14), S('days_to_pay_payer', 'Target days to be paid, payers', 'int', 45), S('payer_red_days', 'Days to be paid above which payers are red', 'int', 60),
    S('collection_target', 'Wanted collection rate', 'pct', 0.95), S('over60_target', 'Wanted share of A/R over 60 days (example)', 'pct', 0.10),
    S('reminder_weeks', 'Unpaid weeks (after the deposit) that call for a reminder', 'int', 1), S('pause_weeks', 'Unpaid weeks (after the deposit) at which care is paused', 'int', 3),
    S('writeoff_limit', 'Write-offs above this amount need the owner (example)', 'money', 500), S('collect_cost', 'Staff cost of one collection attempt (example)', 'money', 35),
    S('claim_window_days', 'Days after the period ends within which a claim is submitted', 'int', 30), S('short_pay_accept', 'Short payment share you accept without a resubmission', 'pct', 0.02),
    S('mileage_rate', 'Mileage rate per km (or per mile, your own)', 'money', MILEAGE_RATE), S('target_margin', 'Wanted gross margin per client hour (example, use your own)', 'pct', TARGET_MARGIN),
    S('payroll_burden', 'Payroll burden on pay (example, confirm with adviser)', 'pct', PAYROLL_BURDEN)]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 invoices
def SEG(b):
    h = 'SUMIFS({range:invoice_lines.hours},{range:invoice_lines.invoice_id},{col:invoice_id},{range:invoice_lines.band},%s)' % tok('band', b)
    a = 'SUMIFS({range:invoice_lines.amount},{range:invoice_lines.invoice_id},{col:invoice_id},{range:invoice_lines.band},%s)' % tok('band', b)
    return 'IF(%s>0,%s&" "&ROUND(%s,2)&"*"&ROUND(%s/%s,2)&" | ","")' % (h, tok('band', b), h, a, h)
BAND_SUM = 'IF(COUNTIFS({range:invoice_lines.invoice_id},{col:invoice_id})=0,%s,%s)' % (ck('Lines not kept'), '&'.join(SEG(b) for b in BANDS))
tables.append(T('invoices', 'Invoices', 'Invoices with balance, age band and rank',
    'One row per invoice (a one-person agency can start here): period, hours, amount, deposit and payment; balance, days past due, age band, hours check and rank fill in.', [
    C('invoice_id', 'Invoice ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), LST('payer', 'Payer', 'payer', 20), LST('cycle', 'Billing cycle', 'cycle', 11),
    C('period_start', 'Period start', 'date', 11), C('period_end', 'Period end', 'date', 11), C('issued_on', 'Issued on', 'date', 11), C('due_date', 'Due date', 'date', 11), C('hours', 'Hours billed', 'num', 9),
    C('amount', 'Amount', 'money', 12), C('deposit_applied', 'Deposit applied', 'num', 11), C('paid_amount', 'Paid amount', 'money', 12), C('paid_on', 'Paid on', 'date', 11), LST('paid_by', 'Paid by', 'paidby', 15),
    C('written_off', 'Written off', 'num', 11), LST('status', 'Status', 'invst', 12),
    CA('balance', 'Balance', 'money', 'IF(%s,MAX(0,{col:amount}-{col:deposit_applied}-{col:paid_amount}-{col:written_off}),0)' % OPEN_INV, 12),
    CA('days_past_due', 'Days past due', 'int', 'IF({col:balance}>0,MAX(0,{today}-{col:due_date}),"")', 10),
    CA('days_since', 'Days since issued', 'int', 'IF({col:balance}>0,{today}-{col:issued_on},"")', 10),
    CA('age_band', 'Age band', 'text', 'IF({col:balance}>0,IF({col:days_since}<=30,%s,IF({col:days_since}<=60,%s,IF({col:days_since}<=90,%s,%s))),"")' % (tok('ageband', 'Days 0-30'), tok('ageband', 'Days 31-60'), tok('ageband', 'Days 61-90'), tok('ageband', 'Days over 90')), 14),
    CA('days_to_pay', 'Days to be paid', 'int', 'IF({col:paid_on}="","",{col:paid_on}-{col:issued_on})', 10),
    CA('terms_flag', 'Terms check', 'text', 'IF({col:status}=%s,%s,IF({col:balance}>0,IF({today}>{col:due_date},%s,%s),IF({col:days_to_pay}<=({col:due_date}-{col:issued_on}),%s,%s)))' % (
        tok('invst', 'Written off'), ck('Closed'), ck('Past due'), ck('Not due yet'), ck('Within terms'), ck('Over terms')), 13),
    CA('agreed_hours', 'Agreed hours for the period', 'num', 'IFERROR(INDEX({range:clients.weekly_hours},MATCH({col:client_id},{range:clients.client_id},0))*({col:period_end}-{col:period_start}+1)/7,"")', 11),
    CA('hours_flag', 'Hours check', 'text', 'IF({col:agreed_hours}="","",IF(ABS({col:hours}-{col:agreed_hours})<={set:hours_tolerance}*{col:agreed_hours},%s,%s))' % (ck('Matches agreement'), ck('Query hours')), 16),
    CA('priority_score', 'Collection score', 'num', 'IF(AND({col:balance}>0,{col:days_past_due}>0),{col:balance}*(1+{col:days_past_due}/30)+VALUE(RIGHT({col:invoice_id},4))/100000,"")', 11),
    CA('collect_rank', 'Phone first rank', 'int', 'IF({col:priority_score}="","",1+COUNTIF({range:invoices.priority_score},">"&{col:priority_score}))', 9),
    CA('band_summary', 'Hours by band and rate', 'text', BAND_SUM, 30),
    CA('same_day_count', 'Invoices issued that day', 'int', 'COUNTIFS({range:invoices.issued_on},{col:issued_on})', 10),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), COMPANY_COL(), STAFF_PH(3, 'office_phone'), STAFF_PH(2, 'scheduler_phone'), STAFF_PH(1, 'owner_phone')], D.invoices_d(), 800,
    [A('days_past_due', '> 30', 'bad'), A('terms_flag', '= ' + ck('Past due'), 'warn'), A('hours_flag', '= ' + ck('Query hours'), 'warn'), A('status', '= ' + tok('invst', 'Paid'), 'good')]))
# ---------------------------------------------------------------- 2 invoice lines
tables.append(T('invoice_lines', 'Invoice Lines', 'Invoice lines by time band with a rate card check',
    'One row per time band on an invoice: hours, rate and amount; the rate card rate, the gap and the line check fill in by themselves.', [
    C('line_id', 'Line ID', 'text', 9, required=True), C('invoice_id', 'Invoice ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), LST('service', 'Service', 'svc', 18), LST('band', 'Time band', 'band', 11),
    C('hours', 'Hours', 'num', 9), C('rate', 'Rate', 'money', 11), C('amount', 'Amount', 'money', 12),
    CA('payer', 'Payer', 'text', LKT('invoices.payer', 'invoices.invoice_id', 'invoice_id'), 20),
    CA('card_rate', 'Rate card rate for the payer', 'money', 'SUMIFS({range:rate_card.bill_rate},{range:rate_card.service},{col:service},{range:rate_card.band},{col:band})*SUMIFS({range:payers.rate_share},{range:payers.payer},{col:payer})', 12),
    CA('rate_gap', 'Gap to the card, %', 'pct', 'IF({col:card_rate}>0,{col:rate}/{col:card_rate}-1,0)', 10),
    CA('line_check', 'Rate check', 'text', 'IF(ABS({col:rate_gap})<={set:rate_tolerance},%s,%s)' % (ck('On the card'), ck('Off the card')), 12)], D.lines_d(), 800,
    [A('line_check', '= ' + ck('Off the card'), 'warn')]))
# ---------------------------------------------------------------- 3 hours check
tables.append(T('hours_check', 'Agreement Hours Check', 'Agreed, delivered and billed hours per client and month',
    'One row per client and month: agreed hours from the service agreement, delivered hours from the visits and billed hours; the difference and the mismatch flag fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), C('month', 'Month', 'date', 11), C('agreed_hours', 'Agreed hours', 'num', 10),
    C('delivered_hours', 'Delivered hours', 'num', 10), C('billed_hours', 'Billed hours', 'num', 10),
    CA('difference', 'Billed minus agreed hours', 'num', '{col:billed_hours}-{col:agreed_hours}', 11),
    CA('diff_pct', 'Difference, %', 'pct', 'IF({col:agreed_hours}>0,{col:difference}/{col:agreed_hours},0)', 10),
    CA('billed_vs_delivered', 'Billed minus delivered hours', 'num', '{col:billed_hours}-{col:delivered_hours}', 11),
    CA('flag', 'Mismatch check', 'text', 'IF(ABS({col:diff_pct})<={set:hours_tolerance},%s,%s)' % (ck('Matches agreement'), ck('Query hours')), 16),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), COMPANY_COL()], D.hours_d(), 600,
    [A('flag', '= ' + ck('Query hours'), 'warn')]))
# ---------------------------------------------------------------- 4 payments
tables.append(T('payments', 'Payments', 'Payments received by client, kind and method',
    'One row per payment (a one-person agency can start here): date, client, kind, method and amount; the month and the client phone fill in by themselves.', [
    C('payment_id', 'Payment ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), LST('kind', 'Kind', 'payk', 15),
    LST('method', 'Method', 'paym', 14), C('amount', 'Amount', 'money', 12), C('invoice_id', 'Invoice ID', 'text', 10),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), COMPANY_COL()], D.payments_d(), 900))
# ---------------------------------------------------------------- 5 deposits
tables.append(T('deposits', 'Deposits and Prepayments', 'Deposits and prepaid balances with weeks of hours left',
    'One row per deposit or prepayment: amount, used, balance and the weekly bill; the weeks of hours left, the low-balance flag and the top-up to the buffer fill in by themselves.', [
    C('deposit_id', 'Deposit ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), LST('kind', 'Kind', 'depk', 12), C('received_on', 'Received on', 'date', 11),
    C('amount', 'Amount', 'money', 12), C('used', 'Used', 'num', 12), C('balance', 'Balance', 'money', 12), C('weekly_bill', 'Weekly bill', 'money', 11), LST('status', 'Status', 'depst', 11),
    CA('weeks_left', 'Weeks of hours left', 'num', 'IF(AND({col:status}=%s,{col:weekly_bill}>0),{col:balance}/{col:weekly_bill},"")' % tok('depst', 'Held'), 10),
    CA('low_flag', 'Balance check', 'text', 'IF({col:weeks_left}="","",IF({col:weeks_left}<0.95*{set:deposit_weeks},%s,%s))' % (ck('Low balance'), ck('Enough')), 13),
    CA('top_up', 'Top-up to the buffer', 'money', 'IF({col:weeks_left}="",0,MAX(0,{set:buffer_weeks}*{col:weekly_bill}-{col:balance}))', 11),
    CA('days_held', 'Days held', 'int', 'IF({col:status}=%s,{today}-{col:received_on},"")' % tok('depst', 'Held'), 9),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), COMPANY_COL(), STAFF_PH(3, 'office_phone')], D.deposits_d(), 200,
    [A('low_flag', '= ' + ck('Low balance'), 'bad'), A('status', '= ' + tok('depst', 'Refunded'), 'warn')]))
# ---------------------------------------------------------------- 6 prepaid ledger
tables.append(T('prepaid', 'Prepaid Ledger', 'Prepaid balance ledger with the balance after each entry',
    'One row per top-up or invoice paid from a prepaid balance: the amount (a payment out is negative) and the balance after; the weeks of hours left and the low-balance flag fill in by themselves.', [
    C('ledger_id', 'Ledger ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), C('date', 'Date', 'date', 11), C('top_up', 'Top-up', 'bool', 9),
    C('amount', 'Amount', 'money', 12), C('balance_after', 'Balance after', 'money', 12), C('invoice_id', 'Invoice ID', 'text', 10),
    CA('weekly_bill', 'Weekly bill', 'money', 'IFERROR(INDEX({range:deposits.weekly_bill},MATCH({col:client_id},{range:deposits.client_id},0)),0)', 11),
    CA('weeks_left', 'Weeks of hours left', 'num', 'IF({col:weekly_bill}>0,{col:balance_after}/{col:weekly_bill},"")', 10),
    CA('low_flag', 'Balance check', 'text', 'IF({col:weeks_left}="","",IF({col:weeks_left}<0.95*{set:deposit_weeks},%s,%s))' % (ck('Low balance'), ck('Enough')), 13),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), COMPANY_COL()], D.ledger_d(), 400,
    [A('low_flag', '= ' + ck('Low balance'), 'bad')]))
# ---------------------------------------------------------------- 7 ageing by client
def BUCKET(b): return 'SUMIFS({range:invoices.balance},{range:invoices.client_id},{col:client_id},{range:invoices.age_band},%s)' % tok('ageband', b)
tables.append(T('ageing_client', 'Ageing by Client', 'A/R ageing by client in four buckets',
    'One row per active client: the open balance in four age buckets (days since the invoice date) comes from the invoices; the total and the oldest bucket fill in.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('reviewed_on', 'Balance reviewed on', 'date', 12),
    CA('client', 'Client', 'text', LKT('clients.client', 'clients.client_id', 'client_id'), 24), CA('payer', 'Payer', 'text', LKT('clients.payer', 'clients.client_id', 'client_id'), 20),
    CA('age_0_30', '0-30 days', 'money', BUCKET('Days 0-30'), 11), CA('age_31_60', '31-60 days', 'money', BUCKET('Days 31-60'), 11), CA('age_61_90', '61-90 days', 'money', BUCKET('Days 61-90'), 11),
    CA('age_90_plus', 'Over 90 days', 'money', BUCKET('Days over 90'), 11), CA('total', 'Total owed', 'money', '{col:age_0_30}+{col:age_31_60}+{col:age_61_90}+{col:age_90_plus}', 12),
    CA('oldest', 'Oldest bucket', 'text', 'IF({col:age_90_plus}>0,%s,IF({col:age_61_90}>0,%s,IF({col:age_31_60}>0,%s,IF({col:age_0_30}>0,%s,%s))))' % (
        tok('ageband', 'Days over 90'), tok('ageband', 'Days 61-90'), tok('ageband', 'Days 31-60'), tok('ageband', 'Days 0-30'), ck('No open balance')), 14),
    CA('review_days', 'Days since review', 'int', 'IF({col:reviewed_on}="","",{today}-{col:reviewed_on})', 10),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), COMPANY_COL()], D.ageing_client_d(), 100,
    [A('age_61_90', '> 0', 'bad'), A('age_90_plus', '> 0', 'bad'), A('age_31_60', '> 0', 'warn')]))
# ---------------------------------------------------------------- 8 ageing by month
tables.append(T('ageing_month', 'Ageing by Month', 'A/R ageing at each month end with the share over 60 days',
    'One row per month end: the open balance in four age buckets; the total, the amount over 60 days and its share fill in by themselves (A/R means money owed to the agency).', [
    C('as_of', 'As of', 'date', 11, required=True), C('age_0_30', '0-30 days', 'money', 12), C('age_31_60', '31-60 days', 'money', 12), C('age_61_90', '61-90 days', 'num', 12), C('age_90_plus', 'Over 90 days', 'num', 12),
    CA('total', 'Total A/R', 'money', '{col:age_0_30}+{col:age_31_60}+{col:age_61_90}+{col:age_90_plus}', 12),
    CA('over60', 'Over 60 days', 'money', '{col:age_61_90}+{col:age_90_plus}', 11),
    CA('over60_share', 'Share over 60 days', 'pct', 'IF({col:total}>0,{col:over60}/{col:total},0)', 11),
    CA('share_flag', 'Share check', 'text', 'IF({col:over60_share}>{set:over60_target},%s,%s)' % (vd('Over target'), vd('Within target')), 13)], D.ageing_month_d(), 50,
    [A('over60_share', '> {set:over60_target}', 'warn')]))
# ---------------------------------------------------------------- 9 statements
tables.append(T('statements', 'Client Statements', 'Monthly client statements',
    'One row per client statement: opening balance, invoiced, paid and closing balance for the month and the date sent; the movement fills in by itself.', [
    C('statement_id', 'Statement ID', 'text', 11, required=True), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), C('month', 'Month', 'date', 11), C('opening', 'Opening', 'money', 12),
    C('invoiced', 'Invoiced', 'money', 12), C('paid', 'Paid', 'money', 12), C('closing', 'Closing', 'money', 12), C('sent_on', 'Sent on', 'date', 11),
    CA('movement', 'Movement', 'money', '{col:closing}-{col:opening}', 11),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), COMPANY_COL()], D.statements_d(), 200,
    [A('closing', '> 2000', 'warn')]))
# ---------------------------------------------------------------- 10 collections
tables.append(T('collections', 'Collections Log', 'Collection calls and promises by invoice',
    'One row per collection action: date, client, invoice, action, outcome, promised date and whether it was kept; days since due and the promise check fill in.', [
    C('call_id', 'Call ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), C('invoice_id', 'Invoice ID', 'text', 10),
    LST('action', 'Action', 'colact', 20), LST('outcome', 'Outcome', 'colout', 16), C('promised_on', 'Promised for', 'date', 11), C('kept', 'Promise kept', 'bool', 9),
    CA('due_date', 'Invoice due date', 'date', LKD('invoices.due_date', 'invoices.invoice_id', 'invoice_id'), 11),
    CA('days_since_due', 'Days since due date', 'int', 'IF({col:due_date}="","",{col:date}-{col:due_date})', 10),
    CA('balance', 'Invoice balance now', 'money', LKN('invoices.balance', 'invoices.invoice_id', 'invoice_id'), 11),
    CA('promise_flag', 'Promise check', 'text', 'IF({col:promised_on}="","",IF({col:kept}=%s,%s,IF({col:promised_on}<{today},%s,%s)))' % (YES, ck('Promise kept'), ck('Promise broken'), ck('Open')), 14),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), COMPANY_COL()], D.collections_d(), 400,
    [A('promise_flag', '= ' + ck('Promise broken'), 'bad'), A('outcome', '= ' + tok('colout', 'Paid'), 'good')]))
# ---------------------------------------------------------------- 11 claims
tables.append(T('claims', 'Payer Claims', 'Payer claims with status and days to be paid',
    'One row per claim to a third-party payer (an insurer, a public body or an employer scheme in your area), status and amounts only; days outstanding and chase rank fill in.', [
    C('claim_id', 'Claim ID', 'text', 10, required=True), C('invoice_id', 'Invoice ID', 'text', 10), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), LST('payer', 'Payer', 'cpayer', 20),
    C('month', 'Month', 'date', 11), C('hours', 'Hours', 'num', 9), C('billed_amount', 'Billed amount', 'money', 12), C('submitted_on', 'Submitted on', 'date', 11), LST('status', 'Status', 'clmst', 13),
    LST('reason', 'Reason', 'clmrsn', 20), C('resubmitted_on', 'Resubmitted on', 'date', 12), C('paid_on', 'Paid on', 'date', 11), C('paid_amount', 'Paid amount', 'money', 12), C('short_amount', 'Short amount', 'num', 11),
    C('payer_phone', 'Payer phone', 'text', 18),
    CA('payer_days', 'Usual days to be paid', 'int', 'SUMIFS({range:payers.pay_days},{range:payers.payer},{col:payer})', 10),
    CA('outstanding_amount', 'Outstanding amount', 'money', 'IF(%s,{col:billed_amount},0)' % OPEN_CLM, 12),
    CA('days_outstanding', 'Days outstanding', 'int', 'IF({col:outstanding_amount}>0,{today}-{col:submitted_on},"")', 10),
    CA('days_to_pay', 'Days to be paid', 'int', 'IF({col:paid_on}="","",{col:paid_on}-{col:submitted_on})', 10),
    CA('pay_flag', 'Days check', 'text', 'IF({col:paid_on}<>"",IF({col:days_to_pay}<={col:payer_days},%s,%s),IF({col:outstanding_amount}>0,IF({col:days_outstanding}>{col:payer_days},%s,%s),%s))' % (
        ck('Within usual days'), ck('Paid late'), ck('Past due'), ck('Open'), ck('Closed')), 15),
    CA('expected_pay', 'Expected payment date', 'date', 'IF(AND({col:outstanding_amount}>0,{col:status}<>%s),{col:submitted_on}+{col:payer_days},"")' % tok('clmst', 'Rejected'), 12),
    CA('chase_score', 'Chase score', 'num', 'IF(AND({col:outstanding_amount}>0,{col:status}<>%s),{col:outstanding_amount}*{col:days_outstanding}/{col:payer_days}+VALUE(RIGHT({col:claim_id},4))/100000,"")' % tok('clmst', 'Rejected'), 10),
    CA('chase_rank', 'Chase rank', 'int', 'IF({col:chase_score}="","",1+COUNTIF({range:claims.chase_score},">"&{col:chase_score}))', 9),
    CA('chase_flag', 'Chase check', 'text', 'IF({col:chase_rank}="",IF({col:status}=%s,%s,%s),IF({col:days_outstanding}>={col:payer_days}-7,%s,%s))' % (tok('clmst', 'Rejected'), ck('Resubmit now'), ck('Closed'), ck('Chase now'), ck('Wait')), 13),
    COMPANY_COL(), STAFF_PH(3, 'office_phone')], D.claims_d(), 400,
    [A('pay_flag', '= ' + ck('Past due'), 'bad'), A('pay_flag', '= ' + ck('Paid late'), 'warn'), A('status', '= ' + tok('clmst', 'Rejected'), 'bad'), A('status', '= ' + tok('clmst', 'Paid'), 'good')]))
# ---------------------------------------------------------------- 12 claim status by payer
tables.append(T('claim_status', 'Claim Status by Payer', 'Claim status by payer and month',
    'One row per payer and month: claims submitted, paid, short-paid and rejected, the amount still outstanding and the short amount; the paid share fills in by itself.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('payer', 'Payer', 'cpayer', 20), C('month', 'Month', 'date', 11), C('submitted', 'Submitted', 'int', 10), C('paid', 'Paid', 'int', 9), C('short_paid', 'Short-paid', 'int', 10),
    C('rejected', 'Rejected', 'int', 9), C('outstanding', 'Amount outstanding', 'num', 12), C('short_amount', 'Short amount', 'num', 11), C('billed', 'Billed amount', 'money', 12),
    CA('paid_share', 'Paid share', 'pct', 'IF({col:submitted}>0,{col:paid}/{col:submitted},0)', 10)], D.claim_status_d(), 120))
# ---------------------------------------------------------------- 13 resubmissions
tables.append(T('resubmit', 'Resubmission List', 'Claims to resubmit or recover with the action due',
    'One row per rejected, resubmitted or short-paid claim: who handles it, resubmit-by date and next step; client, payer, amount, days since submission and action due fill in.', [
    C('claim_id', 'Claim ID', 'text', 10, required=True), REF('handled_by', 'Handled by', 'team.name', 20), C('resubmit_by', 'Resubmit by', 'date', 11), C('next_step', 'Next step', 'text', 30),
    CA('client', 'Client', 'text', LKT('claims.client', 'claims.claim_id', 'claim_id'), 24), CA('payer', 'Payer', 'text', LKT('claims.payer', 'claims.claim_id', 'claim_id'), 20),
    CA('status', 'Claim status', 'text', LKT('claims.status', 'claims.claim_id', 'claim_id'), 13), CA('reason', 'Reason', 'text', LKT('claims.reason', 'claims.claim_id', 'claim_id'), 20),
    CA('amount', 'Amount at stake', 'money', 'IF({col:status}=%s,%s,%s)' % (tok('clmst', 'Short-paid'), LKN('claims.short_amount', 'claims.claim_id', 'claim_id'), LKN('claims.billed_amount', 'claims.claim_id', 'claim_id')), 11),
    CA('submitted_on', 'Submitted on', 'date', LKD('claims.submitted_on', 'claims.claim_id', 'claim_id'), 11),
    CA('days_since', 'Days since submission', 'int', '{today}-{col:submitted_on}', 10),
    CA('resubmitted_on', 'Resubmitted on', 'date', LKD('claims.resubmitted_on', 'claims.claim_id', 'claim_id'), 12),
    CA('paid_on', 'Paid on', 'date', LKD('claims.paid_on', 'claims.claim_id', 'claim_id'), 11),
    CA('action_flag', 'Action due', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,IF({col:resubmit_by}<{today},%s,%s),IF(AND({col:status}=%s,{col:paid_on}<>"",{col:paid_on}>={today}-90),%s,%s)))' % (
        tok('clmst', 'Resubmitted'), ck('Wait'), tok('clmst', 'Rejected'), ck('Resubmit now'), ck('Resubmit soon'), tok('clmst', 'Short-paid'), ck('Resubmit soon'), ck('Closed')), 14),
    CA('payer_phone', 'Payer phone', 'text', LKT('claims.payer_phone', 'claims.claim_id', 'claim_id'), 18), COMPANY_COL(), STAFF_PH(3, 'office_phone')], D.resubmit_d(), 120,
    [A('action_flag', '= ' + ck('Resubmit now'), 'bad'), A('action_flag', '= ' + ck('Resubmit soon'), 'warn')]))
# ---------------------------------------------------------------- 14 payer payments
tables.append(T('payer_payments', 'Payer Payments', 'Payments received from payers with claims paid',
    'One row per payer payment (a remittance): date, claims paid and the amount; the average per claim fills in by itself.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('payer', 'Payer', 'cpayer', 20), C('date', 'Date', 'date', 11), C('claims_paid', 'Claims paid', 'int', 10), C('amount', 'Amount', 'money', 12),
    CA('per_claim', 'Average per claim', 'money', 'IF({col:claims_paid}>0,{col:amount}/{col:claims_paid},0)', 11)], D.payer_payments_d(), 250))
# ---------------------------------------------------------------- 15 write-offs
tables.append(T('writeoffs', 'Write-offs', 'Write-offs with reason and approval',
    'One row per write-off: invoice, client, amount, reason and who approved it; the share of that year\'s billing fills in by itself.', [
    C('writeoff_id', 'Write-off ID', 'text', 10, required=True), C('invoice_id', 'Invoice ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), C('date', 'Date', 'date', 11), C('amount', 'Amount', 'money', 11),
    LST('reason', 'Reason', 'wrsn', 20), REF('approved_by', 'Approved by', 'team.name', 20),
    CA('share_year', 'Share of the year\'s billing', 'pct', 'IFERROR({col:amount}/SUMIFS({range:days_to_pay.invoiced},{range:days_to_pay.month},">="&DATE(YEAR({col:date}),1,1),{range:days_to_pay.month},"<="&DATE(YEAR({col:date}),12,1)),0)', 11),
    CA('approval_flag', 'Approval check', 'text', 'IF({col:amount}>{set:writeoff_limit},%s,%s)' % (ck('Owner approval'), ck('Office approval')), 12), COMPANY_COL(), STAFF_PH(1, 'owner_phone')], D.writeoffs_d(), 100))
# ---------------------------------------------------------------- 16 days to pay by month
def AVG3(col): return 'IFERROR(AVERAGEIFS({range:days_to_pay.%s},{range:days_to_pay.month},">="&DATE(YEAR({col:month}),MONTH({col:month})-3,1),{range:days_to_pay.month},"<"&{col:month}),"")' % col
tables.append(T('days_to_pay', 'Days to Pay by Month', 'Billing, receipts and days to be paid by month',
    'One row per month: invoiced, received, days to be paid for private pay and payers, collected share and prepaid balance; the comparison with your 3-month average fills in.', [
    C('month', 'Month', 'date', 11, required=True), C('invoices', 'Invoices', 'int', 9), C('invoiced', 'Invoiced', 'money', 12), C('received', 'Received', 'money', 12), C('private_days', 'Private pay days to be paid', 'num', 11),
    C('payer_days', 'Payer days to be paid', 'num', 11), C('collected_share', 'Collected share', 'pct', 10), C('prepaid_balance', 'Prepaid balance', 'money', 12),
    CA('private_avg3', 'Private pay, 3-month average', 'num', AVG3('private_days'), 11), CA('private_change', 'Private pay vs average, days', 'num', 'IF({col:private_avg3}="",0,{col:private_days}-{col:private_avg3})', 11),
    CA('payer_avg3', 'Payers, 3-month average', 'num', AVG3('payer_days'), 11), CA('payer_change', 'Payers vs average, days', 'num', 'IF({col:payer_avg3}="",0,{col:payer_days}-{col:payer_avg3})', 11),
    CA('pay_flag', 'Pace check', 'text', 'IF({col:private_change}>1,%s,IF({col:private_change}<-1,%s,%s))' % (vd('Slower than usual'), vd('Faster than usual'), vd('As usual')), 15)], D.days_to_pay_d(), 50,
    [A('pay_flag', '= ' + vd('Slower than usual'), 'warn'), A('collected_share', '< {set:collection_target}', 'warn')]))
# ---------------------------------------------------------------- 17 clients
tables.append(T('clients', 'Clients', 'Clients with payer, billing cycle, rate and open balance',
    'One row per client (private pay means self-funded): payer, billing cycle, weekly hours, bill rate, deposit and prepay; the weekly bill, open balance and weeks of deposit fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26), LST('payer', 'Payer', 'payer', 20), LST('service', 'Service', 'svc', 18),
    LST('billing_cycle', 'Billing cycle', 'cycle', 11), C('weekly_hours', 'Weekly hours', 'num', 9), C('bill_rate', 'Weekday bill rate', 'money', 11), C('deposit', 'Deposit', 'money', 11), C('prepay', 'Prepay', 'bool', 8),
    C('status', 'Status', 'text', 10), C('start_date', 'Start date', 'date', 11),
    CA('weekly_bill', 'Weekly bill', 'money', '{col:weekly_hours}*{col:bill_rate}', 11), CA('open_balance', 'Open balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.client_id},{col:client_id})', 11),
    CA('deposit_cover', 'Weeks of deposit', 'num', 'IF({col:weekly_bill}>0,{col:deposit}/{col:weekly_bill},0)', 10), COMPANY_COL()], D.clients_d(), 150,
    [A('open_balance', '> 2000', 'warn')]))
# ---------------------------------------------------------------- 18-20 reference
tables.append(T('payers', 'Payers', 'Payers with rate share and days to be paid',
    'Private pay (self-funded), three payers and the prepaid balance: share of the rate card and usual days to be paid. A third-party payer is an insurer, a public body or an employer scheme in your area.', [
    C('payer', 'Payer', 'text', 24, required=True), C('rate_share', 'Rate share', 'pct', 10), C('pay_days', 'Usual days to be paid', 'int', 12)], D.payers_d(), 50))
tables.append(T('rate_card', 'Rate Card', 'Rate card by service and time band',
    'Thirty bill rates per hour (before any tax): six services in five time bands. Read by the invoice line check. Use your own rates.', [
    LST('service', 'Service', 'svc', 20, required=True), LST('band', 'Time band', 'band', 12), C('bill_rate', 'Bill rate per hour', 'money', 12)], D.rate_card_d(), 50))
tables.append(T('team', 'Team', 'Team and outside contacts',
    'The owner-director, the scheduler, the office manager, the recruiter, two field supervisors and ten outside contacts with phone and e-mail (messages use these phones).', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 18), C('team', 'Team', 'text', 11), C('pay_type', 'Pay type', 'text', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'Email', 'text', 26), C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'int', 11), C('hourly_rate', 'Hourly rate', 'int', 9), C('speciality', 'Speciality', 'text', 30),
    C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11)], D.team_d(), 50))
assert len(tables) == 20, len(tables)
