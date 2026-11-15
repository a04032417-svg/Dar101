"""Home care agency suite - part 5: Client Invoices, Deposits and Payers."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from hc5_lists import *
from hc5_tables import settings, tables, CA, STAFF_PH, COMPANY_COL
from hc5_tools import tools

NOTE = "Sample wording: adapt it to your own agency and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
def cnt(tb, col, pick): return 'COUNTIFS({range:%s.%s},INDEX({range:%s.%s},MATCH({pick},{range:%s},0)))' % (tb, col, tb, col, pick)
def TB(k): return next(t for t in tables if t['key'] == k)
def addcol(tk, col):
    t = TB(tk)
    if not any(c['key'] == col['key'] for c in t['columns']): t['columns'].append(col)

# extra phone and company columns used by messages
for tk, k, idx in (('collections', 'office_phone', 3), ('collections', 'owner_phone', 1), ('ageing_client', 'owner_phone', 1), ('ageing_client', 'office_phone', 3), ('claim_status', 'office_phone', 3), ('claim_status', 'owner_phone', 1),
                   ('days_to_pay', 'owner_phone', 1), ('ageing_month', 'owner_phone', 1), ('ageing_month', 'accountant_phone', 7), ('writeoffs', 'accountant_phone', 7), ('payer_payments', 'office_phone', 3)):
    addcol(tk, STAFF_PH(idx, k))
for tk in ('claim_status', 'days_to_pay', 'ageing_month', 'payer_payments'): addcol(tk, COMPANY_COL())

forms = [
 FORM('invoice_sheet', 'Invoice Sheet', 'Invoice with hours by band, balance and checks', 'invoices.invoice_id', F(
  ('Client', 'invoices.client'), ('Client ID', 'invoices.client_id'), ('Payer', 'invoices.payer'), ('Billing cycle', 'invoices.cycle'), ('Period start', 'invoices.period_start'), ('Period end', 'invoices.period_end'),
  ('Issued on', 'invoices.issued_on'), ('Due date', 'invoices.due_date'), ('Hours billed', 'invoices.hours'), ('Hours by band and rate', 'invoices.band_summary'), ('Amount', 'invoices.amount'), ('Deposit applied', 'invoices.deposit_applied'),
  ('Balance', 'invoices.balance'), ('Days past due', 'invoices.days_past_due'), ('Age band', 'invoices.age_band'), ('Agreed hours for the period', 'invoices.agreed_hours'), ('Hours check', 'invoices.hours_flag'), ('Terms check', 'invoices.terms_flag'))),
 FORM('receipt_sheet', 'Payment Receipt Sheet', 'Payment receipt', 'payments.payment_id', F(
  ('Date', 'payments.date'), ('Client ID', 'payments.client_id'), ('Client', 'payments.client'), ('Kind', 'payments.kind'), ('Method', 'payments.method'), ('Amount', 'payments.amount'), ('Month', 'payments.month'), ('Client phone', 'payments.phone')) + [
  FF('Payments from this client in the list', cnt('payments', 'client_id', 'payments.payment_id'), 'int'), FF('Received from this client in the list', 'SUMIFS({range:payments.amount},{range:payments.client_id},INDEX({range:payments.client_id},MATCH({pick},{range:payments.payment_id},0)))', 'money')]),
 FORM('deposit_sheet', 'Deposit Sheet', 'Deposit or prepayment with weeks of hours left', 'deposits.deposit_id', F(
  ('Client ID', 'deposits.client_id'), ('Client', 'deposits.client'), ('Kind', 'deposits.kind'), ('Received on', 'deposits.received_on'), ('Amount', 'deposits.amount'), ('Used', 'deposits.used'), ('Balance', 'deposits.balance'),
  ('Weekly bill', 'deposits.weekly_bill'), ('Status', 'deposits.status'), ('Weeks of hours left', 'deposits.weeks_left'), ('Balance check', 'deposits.low_flag'), ('Top-up to the buffer', 'deposits.top_up'), ('Days held', 'deposits.days_held'), ('Client phone', 'deposits.phone'))),
 FORM('topup_sheet', 'Prepayment Top-up Sheet', 'Prepaid ledger entry with balance after', 'prepaid.ledger_id', F(
  ('Client ID', 'prepaid.client_id'), ('Client', 'prepaid.client'), ('Date', 'prepaid.date'), ('Top-up entry', 'prepaid.top_up'), ('Amount', 'prepaid.amount'), ('Balance after', 'prepaid.balance_after'), ('Weekly bill', 'prepaid.weekly_bill'),
  ('Weeks of hours left', 'prepaid.weeks_left'), ('Balance check', 'prepaid.low_flag'), ('Client phone', 'prepaid.phone')) + [FF('Entries for this client in the ledger', cnt('prepaid', 'client_id', 'prepaid.ledger_id'), 'int')]),
 FORM('statement_sheet', 'Statement Request Sheet', 'Client statement for one month', 'statements.statement_id', F(
  ('Client ID', 'statements.client_id'), ('Client', 'statements.client'), ('Month', 'statements.month'), ('Opening balance', 'statements.opening'), ('Invoiced', 'statements.invoiced'), ('Paid', 'statements.paid'), ('Closing balance', 'statements.closing'),
  ('Movement', 'statements.movement'), ('Sent on', 'statements.sent_on'), ('Client phone', 'statements.phone')) + [FF('Statements for this client in the list', cnt('statements', 'client_id', 'statements.statement_id'), 'int')]),
 FORM('call_sheet', 'Collection Call Sheet', 'Collection call with outcome', 'collections.call_id', F(
  ('Date', 'collections.date'), ('Client', 'collections.client'), ('Client phone', 'collections.phone'), ('Invoice ID', 'collections.invoice_id'), ('Action', 'collections.action'), ('Outcome', 'collections.outcome'),
  ('Invoice due date', 'collections.due_date'), ('Days since the due date', 'collections.days_since_due'), ('Invoice balance now', 'collections.balance')) + [FF('Collection actions on this invoice', cnt('collections', 'invoice_id', 'collections.call_id'), 'int')]),
 FORM('promise_sheet', 'Payment Promise Sheet', 'Payment promise and whether it was kept', 'collections.call_id', F(
  ('Client', 'collections.client'), ('Client phone', 'collections.phone'), ('Invoice ID', 'collections.invoice_id'), ('Promised for', 'collections.promised_on'), ('Promise kept', 'collections.kept'), ('Promise check', 'collections.promise_flag'),
  ('Invoice balance now', 'collections.balance')) + [FF('Promises recorded for this client', 'COUNTIFS({range:collections.client},INDEX({range:collections.client},MATCH({pick},{range:collections.call_id},0)),{range:collections.promised_on},">0")', 'int')]),
 FORM('claim_sheet', 'Claim Submission Sheet', 'Claim to a payer (status and amounts only)', 'claims.claim_id', F(
  ('Invoice ID', 'claims.invoice_id'), ('Client', 'claims.client'), ('Payer', 'claims.payer'), ('Month', 'claims.month'), ('Hours', 'claims.hours'), ('Billed amount', 'claims.billed_amount'), ('Submitted on', 'claims.submitted_on'),
  ('Status', 'claims.status'), ('Usual days to be paid', 'claims.payer_days'), ('Payer phone', 'claims.payer_phone')) + [FF('Billed per hour', 'INDEX({range:claims.billed_amount},MATCH({pick},{range:claims.claim_id},0))/INDEX({range:claims.hours},MATCH({pick},{range:claims.claim_id},0))', 'money')]),
 FORM('claimfollow_sheet', 'Claim Follow-up Sheet', 'Claim follow-up with days to be paid', 'claims.claim_id', F(
  ('Client', 'claims.client'), ('Payer', 'claims.payer'), ('Status', 'claims.status'), ('Reason', 'claims.reason'), ('Submitted on', 'claims.submitted_on'), ('Paid on', 'claims.paid_on'), ('Billed amount', 'claims.billed_amount'),
  ('Paid amount', 'claims.paid_amount'), ('Short amount', 'claims.short_amount'), ('Days to be paid', 'claims.days_to_pay'), ('Usual days to be paid', 'claims.payer_days'), ('Days check', 'claims.pay_flag')) + [
  FF('Claims from this payer in the list', cnt('claims', 'payer', 'claims.claim_id'), 'int')]),
 FORM('resubmit_sheet', 'Resubmission Sheet', 'Claim resubmission with the action due', 'resubmit.claim_id', F(
  ('Client', 'resubmit.client'), ('Payer', 'resubmit.payer'), ('Claim status', 'resubmit.status'), ('Reason', 'resubmit.reason'), ('Amount at stake', 'resubmit.amount'), ('Submitted on', 'resubmit.submitted_on'), ('Days since submission', 'resubmit.days_since'),
  ('Resubmitted on', 'resubmit.resubmitted_on'), ('Resubmit by', 'resubmit.resubmit_by'), ('Handled by', 'resubmit.handled_by'), ('Next step', 'resubmit.next_step'), ('Action due', 'resubmit.action_flag'))),
 FORM('writeoff_sheet', 'Write-off Sheet', 'Write-off with approval', 'writeoffs.writeoff_id', F(
  ('Invoice ID', 'writeoffs.invoice_id'), ('Client', 'writeoffs.client'), ('Date', 'writeoffs.date'), ('Amount', 'writeoffs.amount'), ('Reason', 'writeoffs.reason'), ('Approved by', 'writeoffs.approved_by'),
  ('Share of the year\'s billing', 'writeoffs.share_year'), ('Approval check', 'writeoffs.approval_flag')) + [FF('Written off this year in the list', 'SUMIFS({range:writeoffs.amount},{range:writeoffs.date},">="&DATE(YEAR({today}),1,1))', 'money')]),
 FORM('billing_sheet', 'Billing Change Sheet', 'Billing change for one client', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Phone', 'clients.phone'), ('Email', 'clients.email'), ('Payer', 'clients.payer'), ('Service', 'clients.service'), ('Billing cycle', 'clients.billing_cycle'), ('Weekly hours', 'clients.weekly_hours'),
  ('Weekday bill rate', 'clients.bill_rate'), ('Weekly bill', 'clients.weekly_bill'), ('Deposit', 'clients.deposit'), ('Weeks of deposit', 'clients.deposit_cover'), ('Prepay', 'clients.prepay'), ('Open balance', 'clients.open_balance'), ('Status', 'clients.status'))),
]
assert len(forms) == 12

def D_(k, sheet, title, pick, paras, sign): return DOC(k, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('invoice_doc', 'Client Invoice', 'Client invoice with hours by band', 'invoices.invoice_id', [
  'Invoice {col:invoices.invoice_id} of {set:company}, dated {today}. Client: {col:invoices.client} ({col:invoices.client_id}). Payer: {col:invoices.payer}.',
  'Period: {col:invoices.period_start} to {col:invoices.period_end} ({col:invoices.cycle} billing). Hours billed: {col:invoices.hours}. By band: {col:invoices.band_summary}',
  'Amount: {col:invoices.amount}. Deposit applied: {col:invoices.deposit_applied}. Balance due: {col:invoices.balance}. Due date: {col:invoices.due_date}. Rates are before any tax.',
  'Please pay by the due date and quote the invoice number. Questions about the hours: contact the office.'], ['Office manager']),
 D_('statement_doc', 'Client Statement', 'Client statement for one month', 'statements.statement_id', [
  'Statement of {set:company}, dated {today}. Client: {col:statements.client} ({col:statements.client_id}). Month: {col:statements.month}.',
  'Opening balance: {col:statements.opening}. Invoiced: {col:statements.invoiced}. Paid: {col:statements.paid}. Closing balance: {col:statements.closing}. Sent on {col:statements.sent_on}.',
  'If anything does not match your records, please tell us within 7 days.'], ['Office manager']),
 D_('reminder1_doc', 'First Payment Reminder', 'First payment reminder', 'invoices.invoice_id', [
  'Payment reminder of {set:company}, dated {today}. Dear {col:invoices.client},',
  'Invoice {col:invoices.invoice_id} for {col:invoices.amount} was due on {col:invoices.due_date}. The balance of {col:invoices.balance} is {col:invoices.days_past_due} days past due.',
  'This may have crossed with your payment. If so, thank you; if not, please pay or call us.'], ['Office manager']),
 D_('reminder2_doc', 'Final Payment Reminder', 'Final payment reminder', 'invoices.invoice_id', [
  'Final reminder of {set:company}, dated {today}. Dear {col:invoices.client},',
  'Invoice {col:invoices.invoice_id} (balance {col:invoices.balance}) is now {col:invoices.days_past_due} days past due after earlier reminders.',
  'Please pay in full or call us within 7 days to agree a payment plan. Without a reply we may pause new visits; see your service agreement and check your own local rules.'], ['Office manager', 'Owner-director']),
 D_('receipt_doc', 'Payment Receipt', 'Payment receipt', 'payments.payment_id', [
  'Receipt {col:payments.payment_id} of {set:company}, dated {today}.', 'Received on {col:payments.date} from {col:payments.client} ({col:payments.client_id}): {col:payments.amount} ({col:payments.kind}, by {col:payments.method}).',
  'Thank you.'], ['Office manager']),
 D_('deposit_doc', 'Deposit Receipt', 'Deposit receipt', 'deposits.deposit_id', [
  'Deposit receipt {col:deposits.deposit_id} of {set:company}, dated {today}.', 'Received on {col:deposits.received_on} from {col:deposits.client}: {col:deposits.amount} ({col:deposits.kind}). Balance now: {col:deposits.balance}. Status: {col:deposits.status}.',
  'The deposit equals about {col:deposits.weeks_left} weeks of hours at the weekly bill of {col:deposits.weekly_bill}. It is applied to your final invoice or refunded when care ends, as in your agreement.'], ['Office manager']),
 D_('prepaid_doc', 'Prepaid Balance Statement', 'Prepaid balance statement', 'prepaid.ledger_id', [
  'Prepaid balance statement of {set:company}, dated {today}. Client: {col:prepaid.client} ({col:prepaid.client_id}).',
  'Latest entry on {col:prepaid.date}: {col:prepaid.amount} (top-up entry: {col:prepaid.top_up}). Balance after the entry: {col:prepaid.balance_after}.',
  'At the weekly bill of {col:prepaid.weekly_bill} the balance covers {col:prepaid.weeks_left} weeks of visits. Balance check: {col:prepaid.low_flag}.'], ['Office manager']),
 D_('plan_doc', 'Payment Plan Agreement', 'Payment plan agreement for a late balance', 'ageing_client.client_id', [
  'Payment plan agreement of {set:company}, dated {today}. Client: {col:ageing_client.client}.',
  'The open balance is {col:ageing_client.total} (0-30 days {col:ageing_client.age_0_30}, 31-60 days {col:ageing_client.age_31_60}, 61-90 days {col:ageing_client.age_61_90}, over 90 days {col:ageing_client.age_90_plus}).',
  'We agree to clear it in equal instalments on the dates written below. Current invoices are paid on time. If an instalment is missed, the plan ends and the full balance is due.',
  'Instalments and dates: ______________________________'], ['Client', 'Office manager']),
 D_('claim_doc', 'Claim Cover Sheet', 'Claim cover sheet (status and amounts only)', 'claims.claim_id', [
  'Claim cover sheet of {set:company}, dated {today}. Claim {col:claims.claim_id} for invoice {col:claims.invoice_id}.', 'Payer: {col:claims.payer}. Client: {col:claims.client}. Month: {col:claims.month}. Hours: {col:claims.hours}. Billed amount: {col:claims.billed_amount}.',
  'Submitted on {col:claims.submitted_on}. Status: {col:claims.status}. Paid amount: {col:claims.paid_amount}. Short amount: {col:claims.short_amount}.', 'Please confirm receipt and the expected payment date.'], ['Office manager']),
 D_('ageing_doc', 'Ageing Report', 'Ageing report at a month end', 'ageing_month.as_of', [
  'Ageing report of {set:company} at {col:ageing_month.as_of}, dated {today}.', 'A/R (money owed to the agency): 0-30 days {col:ageing_month.age_0_30}, 31-60 days {col:ageing_month.age_31_60}, 61-90 days {col:ageing_month.age_61_90}, over 90 days {col:ageing_month.age_90_plus}.',
  'Total: {col:ageing_month.total}. Over 60 days: {col:ageing_month.over60} ({col:ageing_month.over60_share} of the total, target {set:over60_target}). Check: {col:ageing_month.share_flag}.'], ['Office manager', 'Owner-director']),
 D_('collections_doc', 'Collections Report', 'Collections report for one month', 'days_to_pay.month', [
  'Collections report of {set:company} for {col:days_to_pay.month}, dated {today}.', 'Invoices issued: {col:days_to_pay.invoices}. Invoiced: {col:days_to_pay.invoiced}. Received: {col:days_to_pay.received}. Collected share: {col:days_to_pay.collected_share} (wanted {set:collection_target}).',
  'Days to be paid: private pay {col:days_to_pay.private_days} (3-month average {col:days_to_pay.private_avg3}), payers {col:days_to_pay.payer_days} (3-month average {col:days_to_pay.payer_avg3}). Pace: {col:days_to_pay.pay_flag}.',
  'Prepaid balance held at the end of the month: {col:days_to_pay.prepaid_balance}.'], ['Office manager']),
 D_('writeoff_doc', 'Write-off Record', 'Write-off record', 'writeoffs.writeoff_id', [
  'Write-off record {col:writeoffs.writeoff_id} of {set:company}, dated {today}.', 'Invoice {col:writeoffs.invoice_id}, client {col:writeoffs.client}. Date: {col:writeoffs.date}. Amount: {col:writeoffs.amount}. Reason: {col:writeoffs.reason}.',
  'Approved by {col:writeoffs.approved_by}. Share of the year\'s billing: {col:writeoffs.share_year}. Approval check: {col:writeoffs.approval_flag}. Confirm the tax treatment with your adviser.'], ['Approver', 'Office manager']),
]
assert len(documents) == 12

def CS(k, title, table, start, steps): return _lib.CHK(k, title, table, start, steps)
checklists = [
 CS('c_monday', 'Monday Invoice Run', 'invoices', 'invoices.issued_on', [('Check last week\'s visits are all closed', -1), ('Draft each invoice from delivered hours', 0), ('Run the hours check against the agreement', 0), ('Apply deposits and agreed travel charges', 0), ('Send the invoices', 0), ('Post the send date on the invoice', 1)]),
 CS('c_month', 'Month-end Invoice Close', 'days_to_pay', 'days_to_pay.month', [('Bill every client with hours in the month', 1), ('Issue the monthly and payer invoices', 1), ('Send the client statements', 2), ('Update the ageing by month', 2), ('Review days to be paid', 3), ('Send the month-end report to the owner', 4)]),
 CS('c_hours', 'Invoice Hours Check', 'hours_check', 'hours_check.month', [('Compare agreed, delivered and billed hours', 1), ('List the clients with a mismatch', 1), ('Query the visits behind each mismatch', 2), ('Credit hours billed but not delivered', 3), ('Tell the client about any difference', 3)]),
 CS('c_post', 'Payment Posting', 'payments', 'payments.date', [('Match the payment to the invoice', 0), ('Record the method and the amount', 0), ('Send the receipt', 1), ('Update the balance and the statement', 1), ('Stop reminders for a paid invoice', 1)]),
 CS('c_call', 'Overdue Balance Call', 'collections', 'collections.date', [('Check the balance and the invoice date', 0), ('Call and record the outcome', 0), ('Agree a date and write the promise', 0), ('Send a message that confirms the promise', 1), ('Check the promise on the date', 7), ('Tell the scheduler if care may be paused', 8)]),
 CS('c_prepaid', 'Prepaid Balance Review', 'prepaid', 'prepaid.date', [('List prepaid balances', 0), ('Check the weeks of hours left', 0), ('Ask for a top-up under the minimum', 1), ('Send the prepaid statement', 2), ('Record the top-up', 7)]),
 CS('c_depret', 'Deposit Return Steps', 'deposits', 'deposits.received_on', [('Issue the final invoice', 0), ('Apply the deposit to what is owed', 1), ('Work out the refund or the balance', 1), ('Send the refund or the last invoice', 3), ('Mark the deposit as applied or refunded', 4)]),
 CS('c_claim', 'Claim Submission', 'claims', 'claims.submitted_on', [('Check hours against the visits', -3), ('Check the authorisation reference', -2), ('Check the amount against the rate card', -2), ('Submit within the claim window', 0), ('Record the submission date', 0), ('Set the follow-up date', 1)]),
 CS('c_follow', 'Weekly Claim Follow-up', 'payer_payments', 'payer_payments.date', [('List open claims by age', 0), ('Chase claims near the usual days', 1), ('Record payer answers', 1), ('Match payer payments to claims', 2), ('Flag short payments', 2)]),
 CS('c_resub', 'Rejected Claim Resubmission', 'resubmit', 'resubmit.resubmit_by', [('Read the reason', -14), ('Fix the hours, details or authorisation', -10), ('Resubmit the claim', -7), ('Record the resubmission date', -7), ('Chase after the usual days', 0)]),
 CS('c_wo', 'Write-off Review', 'writeoffs', 'writeoffs.date', [('List balances over the age you set', -7), ('Estimate the chance of payment', -5), ('Compare it with the cost to collect', -3), ('Get approval above the limit', 0), ('Record the write-off and the reason', 0), ('Tell the accountant', 7)]),
 CS('c_year', 'Year-end Receivables Check', 'ageing_month', 'ageing_month.as_of', [('Print the ageing report', 0), ('Check each balance over 60 days', 1), ('List write-offs for the year', 2), ('List deposits and prepaid balances held', 2), ('Send the files and confirm with your adviser', 5)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('c_due', 'Client: your invoice is due', 'invoices', 'invoices.phone', 'Hello {client}, your invoice {invoice_id} of {amount} is due on {due_date}. Thank you, {company}'),
 M('c_remind', 'Client: a friendly reminder', 'invoices', 'invoices.phone', 'Hello {client}, a friendly reminder: invoice {invoice_id} is {days_past_due} days past due (balance {balance}). {company}'),
 M('c_weeks6', 'Client: over 6 weeks past due', 'invoices', 'invoices.phone', 'Hello {client}, your balance of {balance} on invoice {invoice_id} is now {days_past_due} days past due. Please call us today. {company}'),
 M('c_thanks', 'Client: payment received', 'payments', 'payments.phone', 'Hello {client}, thank you, your payment of {amount} on {date} is received. {company}'),
 M('c_statement', 'Client: your statement', 'statements', 'statements.phone', 'Hello {client}, your statement for {month} is ready: closing balance {closing}. {company}'),
 M('c_deposit', 'Client: deposit received', 'deposits', 'deposits.phone', 'Hello {client}, your deposit of {amount} received on {received_on} is held for you. {company}'),
 M('c_weeksleft', 'Client: prepaid balance covers weeks', 'prepaid', 'prepaid.phone', 'Hello {client}, your prepaid balance of {balance_after} covers {weeks_left} weeks of visits. {company}'),
 M('c_topup', 'Client: please top up', 'deposits', 'deposits.phone', 'Hello {client}, please top up your prepaid balance by {top_up} so it covers your visits. {company}'),
 M('c_final', 'Client: final invoice and deposit refund', 'deposits', 'deposits.phone', 'Hello {client}, your final invoice and the refund of your deposit balance of {balance} are attached. {company}'),
 M('c_plan', 'Client: payment plan reminder', 'collections', 'collections.phone', 'Hello {client}, as we agreed, we expect your payment for invoice {invoice_id} on {promised_on} (balance {balance}). {company}'),
 M('c_hours', 'Client: hours differ from the agreement', 'hours_check', 'hours_check.phone', 'Hello {client}, your hours billed for {month} differ from the agreement by {difference} hours. Please call us if you have questions. {company}'),
 M('c_credit', 'Client: a credit is applied', 'hours_check', 'hours_check.phone', 'Hello {client}, for {month} we billed {billed_vs_delivered} hours more than delivered; a credit for those hours is applied to your next invoice. {company}'),
 M('c_cycle', 'Client: invoice period changes', 'clients', 'clients.phone', 'Hello {client}, your invoice period is {billing_cycle} from your next invoice. Your weekly bill is about {weekly_bill}. {company}'),
 M('c_method', 'Client: payment method change', 'clients', 'clients.phone', 'Hello {client}, please tell us if your payment method changes, so your invoices stay on time. {company}'),
 M('c_family', 'Family contact: payment reminder', 'invoices', 'invoices.phone', 'Hello, a payment reminder for {client}\'s invoice {invoice_id} (balance {balance}, due {due_date}) is attached. Please pass it to the person who handles the payments. {company}'),
 M('s_check', 'Scheduler: check before adding visits', 'invoices', 'invoices.scheduler_phone', 'Hello, {client} has an unpaid balance of {balance} on invoice {invoice_id}. Please check with the office before adding visits.'),
 M('s_pause', 'Scheduler: care is paused', 'invoices', 'invoices.scheduler_phone', 'Hello, care for {client} is paused until the balance of {balance} is cleared (invoice {invoice_id}, {days_past_due} days past due).'),
 M('o_send', 'Office manager: invoices to send', 'invoices', 'invoices.office_phone', 'Hello, {same_day_count} invoices are issued on {issued_on}. Please run the hours check before you send them.'),
 M('o_promise', 'Office manager: client promised to pay', 'collections', 'collections.office_phone', 'Hello, {client} promised to pay on {promised_on} (invoice {invoice_id}, balance {balance}). Please check that day.'),
 M('o_reject', 'Office manager: claim rejected', 'resubmit', 'resubmit.office_phone', 'Hello, the claim {claim_id} for {client} ({payer}, {amount}) is {status}; resubmit by {resubmit_by}.'),
 M('o_short', 'Office manager: payer paid less', 'claims', 'claims.office_phone', 'Hello, the payer paid {paid_amount} on claim {claim_id} against {billed_amount} billed (short by {short_amount}). Please check the reason.'),
 M('o_out', 'Office manager: claims outstanding', 'claim_status', 'claim_status.office_phone', 'Hello, claims for {month} still outstanding are worth {outstanding} ({submitted} submitted). Please chase the payer.'),
 M('o_dep', 'Office manager: deposit below one week', 'deposits', 'deposits.office_phone', 'Hello, the deposit of {client} covers {weeks_left} weeks of hours ({balance} against a weekly bill of {weekly_bill}). Please ask for a top-up.'),
 M('w_over60', 'Owner: A/R over 60 days', 'ageing_month', 'ageing_month.owner_phone', 'Hello, A/R over 60 days at {as_of} is {over60}, {over60_share} of the total of {total}.'),
 M('w_oldest', 'Owner: oldest balance', 'invoices', 'invoices.owner_phone', 'Hello, the oldest balance is {client}: {balance} on invoice {invoice_id}, {days_past_due} days past due.'),
 M('w_rate', 'Owner: collection rate', 'days_to_pay', 'days_to_pay.owner_phone', 'Hello, the collection rate for {month} is {collected_share}: {received} received against {invoiced} invoiced.'),
 M('w_claims', 'Owner: payer claims outstanding', 'claim_status', 'claim_status.owner_phone', 'Hello, payer claims outstanding for {month} are {outstanding}; {rejected} were rejected.'),
 M('w_writeoff', 'Owner: write-off needs approval', 'writeoffs', 'writeoffs.owner_phone', 'Hello, a write-off of {amount} for invoice {invoice_id} ({client}) needs approval. Check: {approval_flag}.'),
 M('w_days', 'Owner: days to be paid rose', 'days_to_pay', 'days_to_pay.owner_phone', 'Hello, private pay days to be paid for {month} are {private_days} against a 3-month average of {private_avg3}; payers {payer_days}.'),
 M('p_confirm', 'Payer: please confirm payment', 'claims', 'claims.payer_phone', 'Hello, please confirm payment of claim {claim_id} submitted on {submitted_on} for {billed_amount}. {company}'),
 M('p_corrected', 'Payer: corrected claim attached', 'resubmit', 'resubmit.payer_phone', 'Hello, the corrected claim {claim_id} for {amount} is attached (first submitted on {submitted_on}). {company}'),
 M('p_remit', 'Payer: send the remittance', 'claims', 'claims.payer_phone', 'Hello, please send the remittance for {month} (claim {claim_id}, {billed_amount}). {company}'),
 M('a_ageing', 'Accountant: ageing report attached', 'ageing_month', 'ageing_month.accountant_phone', 'Hello, the ageing report at {as_of} is attached: total A/R {total}, over 60 days {over60}. {company}'),
 M('a_writeoff', 'Accountant: write-off list attached', 'writeoffs', 'writeoffs.accountant_phone', 'Hello, the write-off list is attached, including {writeoff_id}: {amount} on {date}. {company}'),
]
assert len(messages) == 34

YES_ = '{list:yesno.yes}'
MS_ = 'DATE(YEAR({today}),MONTH({today}),1)'; NX_ = 'DATE(YEAR({today}),MONTH({today})+1,1)'
def DR(c, a, b): return '{range:%s},">="&%s,{range:%s},"<"&%s' % (c, a, c, b)
def D30(c): return '{range:%s},">="&({today}-29),{range:%s},"<="&{today}' % (c, c)
def D90(c): return '{range:%s},">="&({today}-89),{range:%s},"<="&{today}' % (c, c)
def BAL(b): return 'SUMIFS({range:invoices.balance},{range:invoices.age_band},%s)' % tok('ageband', b)
kpis = [
 KPI('Invoices issued this month', 'COUNTIFS(%s)' % DR('invoices.issued_on', MS_, NX_), 'int'),
 KPI('Invoiced this month', 'SUMIFS({range:invoices.amount},%s)' % DR('invoices.issued_on', MS_, NX_), 'money'),
 KPI('Payments received this month', 'SUMIFS({range:payments.amount},%s)' % DR('payments.date', MS_, NX_), 'money'),
 KPI('Payments received last 30 days', 'SUMIFS({range:payments.amount},%s)' % D30('payments.date'), 'money'),
 KPI('A/R total now', 'SUM({range:invoices.balance})', 'money'),
 KPI('A/R 0-30 days', BAL('Days 0-30'), 'money'), KPI('A/R 31-60 days', BAL('Days 31-60'), 'money'), KPI('A/R 61-90 days', BAL('Days 61-90'), 'money', alert={"when": "> 0", "style": "warn"}),
 KPI('A/R over 90 days', BAL('Days over 90'), 'money', alert={"when": "> 0", "style": "bad"}),
 KPI('Share of A/R over 60 days', 'IFERROR((%s+%s)/SUM({range:invoices.balance}),0)' % (BAL('Days 61-90'), BAL('Days over 90')), 'pct', alert={"when": "> {set:over60_target}", "style": "bad"}),
 KPI('Invoices past due now', 'COUNTIFS({range:invoices.days_past_due},">0")', 'int', alert={"when": "> 10", "style": "warn"}),
 KPI('Oldest unpaid invoice, days past due', 'MAX({range:invoices.days_past_due})', 'int', alert={"when": "> 42", "style": "bad"}),
 KPI('Private pay balance past 42 days', 'SUMIFS({range:invoices.balance},{range:invoices.payer},%s,{range:invoices.days_past_due},">42")' % tok('payer', 'Private pay'), 'money', alert={"when": "> 0", "style": "bad"}),
 KPI('Collection rate last 90 days', 'IFERROR((SUMIFS({range:invoices.paid_amount},%s)+SUMIFS({range:invoices.deposit_applied},%s))/SUMIFS({range:invoices.amount},%s),0)' % (D90('invoices.due_date'), D90('invoices.due_date'), D90('invoices.due_date')), 'pct', alert={"when": "< {set:collection_target}", "style": "warn"}),
 KPI('Days to be paid, private, 90 days', 'IFERROR(AVERAGEIFS({range:invoices.days_to_pay},{range:invoices.payer},%s,%s),0)' % (tok('payer', 'Private pay'), D90('invoices.paid_on')), 'num', alert={"when": "> {set:days_to_pay_private}", "style": "warn"}),
 KPI('Days to be paid, payers, 90 days', 'IFERROR(AVERAGEIFS({range:invoices.days_to_pay},{range:invoices.payer},"<>"&%s,%s),0)' % (tok('payer', 'Private pay'), D90('invoices.paid_on')), 'num', alert={"when": "> {set:days_to_pay_payer}", "style": "warn"}),
 KPI('Hours mismatch invoices, last 30 days', 'COUNTIFS({range:invoices.hours_flag},%s,%s)' % (ck('Query hours'), D30('invoices.issued_on')), 'int'),
 KPI('Billed vs agreed hours, last 4 weeks', 'IFERROR(SUMIFS({range:invoices.hours},{range:invoices.issued_on},">="&({today}-27))/SUMIFS({range:invoices.agreed_hours},{range:invoices.issued_on},">="&({today}-27)),0)', 'pct'),
 KPI('Deposits held now', 'COUNTIFS({range:deposits.status},%s,{range:deposits.kind},%s)' % (tok('depst', 'Held'), tok('depk', 'Deposit')), 'int'),
 KPI('Deposit value held', 'SUMIFS({range:deposits.balance},{range:deposits.status},%s,{range:deposits.kind},%s)' % (tok('depst', 'Held'), tok('depk', 'Deposit')), 'money'),
 KPI('Prepaid balances held', 'SUMIFS({range:deposits.balance},{range:deposits.status},%s,{range:deposits.kind},%s)' % (tok('depst', 'Held'), tok('depk', 'Prepayment')), 'money'),
 KPI('Prepaid clients with under one week left', 'COUNTIFS({range:deposits.kind},%s,{range:deposits.low_flag},%s)' % (tok('depk', 'Prepayment'), ck('Low balance')), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Prepaid top-ups this month', 'COUNTIFS({range:prepaid.top_up},%s,%s)' % (YES_, DR('prepaid.date', MS_, NX_)), 'int'),
 KPI('Claims submitted this month', 'COUNTIFS(%s)' % DR('claims.submitted_on', MS_, NX_), 'int'),
 KPI('Claims outstanding amount', 'SUM({range:claims.outstanding_amount})', 'money'),
 KPI('Claims past the payer\'s usual days', 'COUNTIFS({range:claims.pay_flag},%s)' % ck('Past due'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Claims rejected, not resubmitted', 'COUNTIFS({range:claims.status},%s)' % tok('clmst', 'Rejected'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Short-paid amount last 90 days', 'SUMIFS({range:claims.short_amount},%s)' % D90('claims.paid_on'), 'money'),
 KPI('Written off this year', 'SUMIFS({range:writeoffs.amount},{range:writeoffs.date},">="&DATE(YEAR({today}),1,1))', 'money'),
 KPI('Collection calls last 30 days', 'COUNTIFS({range:collections.action},%s,%s)' % (tok('colact', 'Phone call'), D30('collections.date')), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Invoices and Payers Dashboard", "kpis": kpis,
 "monthly": {"title": "Invoiced and received by month", "date": "days_to_pay.month", "series": [
   {"label": "Invoiced", "sum": "days_to_pay.invoiced", "date": "days_to_pay.month"}, {"label": "Received", "sum": "days_to_pay.received", "date": "days_to_pay.month"}]},
 "breakdowns": [{"title": "Invoices by status", "by": "invoices.status", "agg": "count"}, {"title": "Claims by status", "by": "claims.status", "agg": "count"},
                {"title": "Payments by method", "by": "payments.method", "agg": "count"}, {"title": "Invoices by payer", "by": "invoices.payer", "agg": "count"}]}
def GA(title, num, den): return {"title": title, "num": num, "den": den}
insights = {"filters": [{"label": "Payer", "list": "payer"}, {"label": "Billing cycle", "list": "cycle"}],
 "gauges": [
  GA('Collection rate', AGG('sum', 'invoices', 'invoices.paid_amount'), AGG('sum', 'invoices', 'invoices.amount', where=[('status', '<>', tok('invst', 'Unpaid'))])),
  GA('A/R under 60 days', AGG('sum', 'invoices', 'invoices.balance', where=[('days_since', '<=', 60)]), AGG('sum', 'invoices', 'invoices.balance', where=[('balance', '>', 0)])),
  GA('Private pay invoices paid within terms', AGG('count', 'invoices', where=[('payer', '=', tok('payer', 'Private pay')), ('terms_flag', '=', ck('Within terms'))]), AGG('count', 'invoices', where=[('payer', '=', tok('payer', 'Private pay')), ('days_to_pay', '>=', 0)])),
  GA('Claims paid within usual days', AGG('count', 'claims', where=[('pay_flag', '=', ck('Within usual days'))]), AGG('count', 'claims', where=[('days_to_pay', '>=', 0)])),
  GA('Prepaid clients with a healthy balance', AGG('count', 'deposits', where=[('kind', '=', tok('depk', 'Prepayment')), ('low_flag', '=', ck('Enough'))]), AGG('count', 'deposits', where=[('kind', '=', tok('depk', 'Prepayment')), ('status', '=', tok('depst', 'Held'))])),
  GA('Invoices that match the agreed hours', AGG('count', 'invoices', where=[('hours_flag', '=', ck('Matches agreement'))]), AGG('count', 'invoices', where=[('agreed_hours', '>', 0)]))],
 "charts": [
  CHART('Invoiced per month', 'column', 'month', [AGG('sum', 'days_to_pay', 'days_to_pay.invoiced', date='days_to_pay.month', label='Invoiced')]),
  CHART('Payments per month', 'column', 'month', [AGG('sum', 'days_to_pay', 'days_to_pay.received', date='days_to_pay.month', label='Received')]),
  CHART('A/R by age band at month end', 'column', 'month', [AGG('sum', 'ageing_month', 'ageing_month.' + c, date='ageing_month.as_of', label=l) for c, l in (('age_0_30', '0-30 days'), ('age_31_60', '31-60 days'), ('age_61_90', '61-90 days'), ('age_90_plus', 'Over 90 days'))]),
  CHART('A/R by payer', 'bar', 'invoices.payer', [AGG('sum', 'invoices', 'invoices.balance', label='A/R')]),
  CHART('Share of A/R over 60 days per month', 'line', 'month', [AGG('avg', 'ageing_month', 'ageing_month.over60_share', date='ageing_month.as_of', label='Share over 60 days')]),
  CHART('Days to be paid per month', 'line', 'month', [AGG('avg', 'days_to_pay', 'days_to_pay.private_days', date='days_to_pay.month', label='Private pay'), AGG('avg', 'days_to_pay', 'days_to_pay.payer_days', date='days_to_pay.month', label='Payers')]),
  CHART('Collection rate per month', 'line', 'month', [AGG('avg', 'days_to_pay', 'days_to_pay.collected_share', date='days_to_pay.month', label='Collected share')]),
  CHART('Invoices by status', 'bar', 'invoices.status', [AGG('count', 'invoices', label='Invoices')]),
  CHART('Invoices by billing cycle', 'bar', 'invoices.cycle', [AGG('count', 'invoices', label='Invoices')]),
  CHART('Invoices by payer', 'bar', 'invoices.payer', [AGG('count', 'invoices', label='Invoices')]),
  CHART('Payments by method', 'bar', 'payments.method', [AGG('count', 'payments', label='Payments')]),
  CHART('Payments by kind', 'bar', 'payments.kind', [AGG('sum', 'payments', 'payments.amount', label='Amount')]),
  CHART('Deposits by status', 'bar', 'deposits.status', [AGG('count', 'deposits', label='Deposits')]),
  CHART('Prepaid balance by month', 'line', 'month', [AGG('avg', 'days_to_pay', 'days_to_pay.prepaid_balance', date='days_to_pay.month', label='Prepaid balance')]),
  CHART('Claims by status', 'bar', 'claims.status', [AGG('count', 'claims', label='Claims')]),
  CHART('Claims per month', 'column', 'month', [AGG('sum', 'claim_status', 'claim_status.submitted', date='claim_status.month', label='Claims submitted')]),
  CHART('Claims outstanding by payer', 'bar', 'claims.payer', [AGG('sum', 'claims', 'claims.outstanding_amount', label='Outstanding')]),
  CHART('Days to be paid by payer', 'bar', 'claims.payer', [AGG('avg', 'claims', 'claims.days_to_pay', label='Days to be paid')]),
  CHART('Claim reasons for rejection and short payment', 'bar', 'claims.reason', [AGG('count', 'claims', label='Claims')]),
  CHART('Short-paid amount per month', 'column', 'month', [AGG('sum', 'claim_status', 'claim_status.short_amount', date='claim_status.month', label='Short amount')]),
  CHART('Write-offs per month', 'column', 'month', [AGG('sum', 'writeoffs', 'writeoffs.amount', date='writeoffs.date', label='Written off')]),
  CHART('Hours mismatches per month', 'column', 'month', [AGG('count', 'hours_check', date='hours_check.month', where=[('flag', '=', ck('Query hours'))], label='Mismatches')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Invoice draft with the agreement check", "why": "hours by time band, deposit and agreed travel give the total and say Send or Check hours against the agreed weekly hours", "where": "Invoice Draft Builder"},
 {"name": "Deposit and prepaid balance ledger", "why": "every deposit and prepayment shows the weeks of hours left, a low-balance flag and the top-up to your buffer", "where": "Deposits and Prepayments"},
 {"name": "A/R ageing and the phone-first list", "why": "open balances in 0-30, 31-60, 61-90 and over 90 days, and the five balances to phone first ranked by amount and age", "where": "Collection Priority List"},
 {"name": "Days to be paid against your own history", "why": "private pay and payer days compared with targets, the last 3 months and the same month last year", "where": "Days to Be Paid"},
 {"name": "Pause-care decision", "why": "unpaid weeks, weekly bill and deposit give your exposure and Continue, Reminder or Pause", "where": "Pause-care Decision"},
 {"name": "Payer claim tracker with the resubmission list", "why": "status and amounts only: submitted, accepted, paid, short-paid, rejected and resubmitted, with days outstanding against the payer's usual days", "where": "Payer Claims"},
 {"name": "Short-pay recovery", "why": "shortfall, expected recovery and your cost give Resubmit, Accept or Write off", "where": "Short-pay Recovery"},
 {"name": "Payer cash forecast", "why": "open claims become expected cash for each of the next 8 weeks, in a base, best or worst case", "where": "Payer Cash Forecast"},
 {"name": "Write-off decision", "why": "balance, age, cost to collect and your own chance of payment give Pursue or Write off and who must approve", "where": "Write-off Decision"},
 {"name": "Payer mix sensitivity", "why": "10 to 50 percent of hours paid by payers shows the effect on days to be paid, cash tied up and margin", "where": "Payer Mix Sensitivity"},
 {"name": "Agreement hours mismatch check", "why": "agreed, delivered and billed hours per client and month flag what to bill, query or credit", "where": "Agreement Hours Check"}]
competitors = [
 {"what": "free invoice templates", "lacks": "total an invoice but never compare billed hours with the agreement, apply deposits or age your balances"},
 {"what": "subscription home care software with a per-client fee", "lacks": "charge more as you grow and keep your data in their system, with no editable targets for days to be paid or write-offs"},
 {"what": "single-sheet payment logs", "lacks": "record payments only, so there is no ageing, phone-first list, prepaid ledger or payer claim tracking"},
 {"what": "generic accounting spreadsheets", "lacks": "hold totals but not weeks of deposit left, payer days to be paid or the resubmission list"},
 {"what": "payer portals and remittance emails", "lacks": "show one payer at a time, so you cannot see claims outstanding, short payments and expected cash across all payers"}]
guide = [
 'Open Start and type your agency name and your targets in the yellow cells: payment terms, target days to be paid, collection rate wanted and the write-off limit. A one-person agency can start with Invoices, Payments and Ageing.',
 'Check Clients, Payers and Rate Card. Private pay means self-funded; a third-party payer is an insurer, a public body or an employer scheme in your area. Rates are before any tax.',
 'Draft each invoice with the Invoice Draft Builder, then enter it on Invoices. The balance, days past due, age band, hours check and phone-first rank fill in by themselves.',
 'Enter payments on Payments, deposits and prepayments on Deposits and Prepayments and each top-up or draw on Prepaid Ledger. Weeks of hours left and the low-balance flag fill in.',
 'Use Ageing by Client and Ageing by Month. A/R means money owed to the agency; the share over 60 days is compared with your target.',
 'Log every collection call on Collections Log with the promise and whether it was kept. Use Collection Priority List to see the five balances to phone first.',
 'Enter payer claims on Payer Claims (status and amounts only). Claim Status by Payer, Resubmission List and Payer Payments follow them; the claim follow-up ranking says which to chase.',
 'Use Agreement Hours Check to compare agreed, delivered and billed hours before you send invoices. Type the delivered hours from whatever you use to check visits; the workbook has no app and no GPS.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Replace the demo data: delete the sample rows on each page, keep the formulas, type your own rows. A blank copy ships with the sample copy.',
 'Why a workbook: one flat price, no per-client or per-caregiver fee, no price rise when hours grow, and your data stays with you. No macros, works in Excel and Google Sheets. Confirm tax and pay questions with your adviser.']
listing = {"title": "Home Care Agency Invoicing Excel Template: Client Invoices, Deposits, A/R Ageing, Payer Claims, Collections, Cash Forecast",
 "headline": "Get paid faster for every care hour in one Excel file",
 "tags": ["home care agency", "invoice template", "ar ageing", "accounts receivable", "caregiver agency", "excel template", "deposit tracker", "claims tracker", "collections log", "billing spreadsheet", "private pay", "payer claims", "home care billing"],
 "description": ("Run client billing for a home care agency in one Excel workbook. It is built for a small non-medical agency with an owner-director, a scheduler, an office manager who does billing, caregivers and clients who pay privately (self-funded) or through a care insurer or third-party payer.\n\n"
  "Invoices holds every invoice with its period, hours, amount, deposit applied and payment, and works out the balance, days past due, age band, an hours check against the agreed weekly hours and a phone-first rank. Invoice Lines checks each time band against your rate card. "
  "Agreement Hours Check compares agreed, delivered and billed hours per client and month. Payments, Deposits and Prepayments, Prepaid Ledger, Client Statements, Collections Log, Write-offs and Days to Pay by Month follow the money to the bank. "
  "Ageing by Client and Ageing by Month show A/R (money owed to the agency) in four buckets and the share over 60 days. Payer Claims, Claim Status by Payer, Resubmission List and Payer Payments track claims by status and amount only, with days to be paid against each payer's usual days.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: invoice draft, hours mismatch, travel and mileage charge, deposit balance, prepayment top-up, collection priority list, pause-care decision, claim check, claim follow-up ranking, short-pay recovery, payer cash forecast, write-off decision and payer mix sensitivity. "
  f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.\n\n"
  "This is part five of the Home Care Agency Business suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-client or per-caregiver fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. "
  "It holds service types, hours, dates, rates and amounts only, never care notes, and it does not give legal, tax or employment advice. Confirm tax and pay questions with your adviser."),
 "features": ["Invoices with balance, age band and hours check", "Deposit and prepaid ledger with weeks of hours left", "A/R ageing and a phone-first list", "Payer claim tracker with resubmission list", "Days to be paid against your own history",
              "Write-off and pause-care decisions", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts",
              f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
s = _lib.spec(id=f'{SUITE}-p5', slug='home-care-invoices', profession='Home Care Agency Business', name='Client Invoices, Deposits and Payers',
         tagline='Get paid faster for every care hour you deliver', price_usd=29, colors={"primary": "#3A506B", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Client invoices, deposits and payers"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hc5.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis),
          'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
