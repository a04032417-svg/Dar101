"""Therapy private practice suite - part 3: Client Fees, Accounts and Packages."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from th3_lists import *
from th3_tables import settings, tables
from th3_tools import tools

SUITE = 'fx-20261115-therapy-practice'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
YES = '{list:yesno.yes}'
def F(*p): return [FV(a, b) for a, b in p]
def IDX(tb, col, pk): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s},0))' % (tb, col, pk)
def cnt(tb, col, pk): return 'COUNTIFS({range:%s.%s},%s)' % (tb, col, IDX(tb, col, pk))
def sm(tb, val, col, pk, extra=''): return 'SUMIFS({range:%s.%s},{range:%s.%s},%s%s)' % (tb, val, tb, col, IDX(tb, col, pk), extra)

# ---------------------------------------------------------------- demo record order: the first row is the record every form and document shows
TB = {t['key']: t for t in tables}
def first(tk, pred, rank=None):
    rows = TB[tk]['demo']; c = [i for i, r in enumerate(rows) if pred(r)]
    if not c: print('NO FIRST ROW for', tk); return
    if rank: c.sort(key=lambda i: rank(rows[i]))
    rows.insert(0, rows.pop(c[0]))
INV = {r['invoice_id']: r for r in TB['invoices']['demo']}
CLN = {r['client'] for r in TB['clients']['demo']}
T0 = TODAY.isoformat()
def age(r): return (TODAY - dt.date.fromisoformat(r['issued_on'])).days
def bands(client):
    b = [0, 0, 0, 0]; v = 0.0
    for r in TB['invoices']['demo']:
        if r['client'] != client or r['status'] in ('paid', 'written_off'): continue
        bal = r['amount'] - r.get('deposit_applied', 0) - r.get('paid_amount', 0)
        if bal <= 0: continue
        a = age(r); b[0 if a <= 30 else 1 if a <= 60 else 2 if a <= 90 else 3] += bal
    return b
first('invoices', lambda r: r['status'] == 'part_paid' and r.get('paid_on') and r.get('deposit_applied', 0) > 0 and r['due_date'] < T0 and r['client'] in CLN) \
    if any(r['status'] == 'part_paid' and r.get('paid_on') and r.get('deposit_applied', 0) > 0 and r['due_date'] < T0 for r in TB['invoices']['demo']) else \
    first('invoices', lambda r: r['status'] == 'part_paid' and r.get('paid_on') and r['client'] in CLN)
first('payments', lambda r: r['method'] == 'card' and r['kind'] == 'invoice' and r['card_fee'] > 0 and r['client'] in CLN, rank=lambda r: r['date'])
first('clients', lambda r: sum(1 for x in bands(r['client']) if x > 0) >= 3, rank=lambda r: -sum(bands(r['client'])))
first('plans', lambda r: r['status'] == 'late')
LATEP = next((p['plan_id'] for p in TB['plans']['demo'] if p['status'] == 'late'), None)
first('instalments', lambda r: r.get('paid_on') and r['paid_on'] > r['due_date'])
first('promises', lambda r: r['outcome'] == 'broken' and r['invoice_id'] in INV and r['client'] in CLN, rank=lambda r: r['logged_on'])
first('reminders', lambda r: r['invoice_id'] in INV and r['reminder_no'] == 2)
first('assessments', lambda r: r['review_date'] > ahead(60))
first('fees', lambda r: r['year'] == TODAY.year and r['service'] == 'intake_assessment')
first('billing', lambda r: r['month'] == iso(month_start(1)))
first('packages', lambda r: r['status'] == 'active' and 0 < r['used'] < r['sessions'])

# ---------------------------------------------------------------- forms
forms = [
 FORM('invoice_sheet', 'Invoice Sheet', 'Invoice with balance and aging band', 'invoices.invoice_id', F(
  ('Service month', 'invoices.month'), ('Client', 'invoices.client'), ('Fee type', 'invoices.fee_type'), ('Clinician', 'invoices.clinician'), ('Sessions', 'invoices.sessions'),
  ('Amount', 'invoices.amount'), ('Deposit applied', 'invoices.deposit_applied'), ('Amount due', 'invoices.amount_due'), ('Issued on', 'invoices.issued_on'), ('Due date', 'invoices.due_date'), ('Paid amount', 'invoices.paid_amount'),
  ('Paid on', 'invoices.paid_on'), ('Pay method', 'invoices.method'), ('Status', 'invoices.status'), ('Balance', 'invoices.balance'), ('Days overdue', 'invoices.days_overdue'), ('A/R aging band', 'invoices.age_band'), ('Payment timing', 'invoices.timing')) + [
  FF('Invoices of this client', cnt('invoices', 'client', 'invoices.invoice_id'), 'int'), FF('Balance of this client', sm('invoices', 'balance', 'client', 'invoices.invoice_id'), 'money')]),
 FORM('receipt_sheet', 'Payment Receipt Sheet', 'Payment receipt with card fee and amount received', 'payments.payment_id', F(
  ('Date', 'payments.date'), ('Client', 'payments.client'), ('Kind', 'payments.kind'), ('Reference', 'payments.ref'), ('Method', 'payments.method'), ('Amount', 'payments.amount'), ('Card fee', 'payments.card_fee'),
  ('Net received', 'payments.net_received'), ('Month', 'payments.month'), ('Client phone', 'payments.phone')) + [
  FF('Payments from this client', cnt('payments', 'client', 'payments.payment_id'), 'int'), FF('Paid by this client in total', sm('payments', 'amount', 'client', 'payments.payment_id'), 'money')]),
 FORM('statement_sheet', 'Account Statement Sheet', 'Account statement with A/R aging buckets', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Phone', 'clients.phone'), ('Client type', 'clients.client_type'), ('Usual service', 'clients.service'), ('Clinician', 'clients.clinician'), ('Fee type', 'clients.fee_type'), ('Sliding share of fee', 'clients.sliding_pct'),
  ('Pay method', 'clients.pay_method'), ('Status', 'clients.status'), ('Invoices', 'clients.invoices_n'), ('Invoiced to date', 'clients.invoiced'), ('Paid on invoices', 'clients.paid_to_date'), ('Balance', 'clients.balance'),
  ('Overdue balance', 'clients.overdue'), ('Balance 0-30 days', 'clients.bal_0_30'), ('Balance 31-60 days', 'clients.bal_31_60'), ('Balance 61-90 days', 'clients.bal_61_90'), ('Balance 90+ days', 'clients.bal_90p'), ('Account check', 'clients.account_flag')) + [
  FF('Overdue share of the balance', 'IFERROR(%s/%s,0)' % (IDX('clients', 'overdue', 'clients.client_id'), IDX('clients', 'balance', 'clients.client_id')), 'pct')]),
 FORM('reminder_sheet', 'Payment Reminder Sheet', 'Payment reminder with days after the due date', 'reminders.reminder_id', F(
  ('Invoice ID', 'reminders.invoice_id'), ('Client', 'reminders.client'), ('Reminder number', 'reminders.reminder_no'), ('Sent on', 'reminders.sent_on'), ('Method', 'reminders.method'), ('Paid after it', 'reminders.paid_after'),
  ('Invoice due date', 'reminders.due_date'), ('Days after the due date', 'reminders.days_after_due')) + [
  FF('Reminders sent for this invoice', cnt('reminders', 'invoice_id', 'reminders.reminder_id'), 'int'),
  FF('Amount due on the invoice', 'IFERROR(INDEX({range:invoices.amount_due},MATCH(%s,{range:invoices.invoice_id},0)),0)' % IDX('reminders', 'invoice_id', 'reminders.reminder_id'), 'money')]),
 FORM('plan_sheet', 'Payment Plan Sheet', 'Payment plan with instalments and balance left', 'plans.plan_id', F(
  ('Client', 'plans.client'), ('Start date', 'plans.start_date'), ('Balance', 'plans.balance'), ('Instalments', 'plans.instalments'), ('Instalment', 'plans.instalment'), ('Paid instalments', 'plans.paid_instalments'),
  ('Next due', 'plans.next_due'), ('Invoices', 'plans.invoices'), ('Status', 'plans.status'), ('Balance left', 'plans.balance_left'), ('Last instalment due', 'plans.end_date'), ('Late instalments', 'plans.late_instalments')) + [
  FF('Share of the plan paid', 'IFERROR(%s/%s,0)' % (IDX('plans', 'paid_instalments', 'plans.plan_id'), IDX('plans', 'instalments', 'plans.plan_id')), 'pct')]),
 FORM('instalment_sheet', 'Instalment Record Sheet', 'Instalment record with payment check and days late', 'instalments.inst_id', F(
  ('Plan', 'instalments.plan_id'), ('Client', 'instalments.client'), ('Due date', 'instalments.due_date'), ('Amount', 'instalments.amount'), ('Paid on', 'instalments.paid_on'), ('Payment check', 'instalments.late_flag'),
  ('Days late', 'instalments.days_late'), ('Client phone', 'instalments.phone')) + [
  FF('Instalments on this plan', cnt('instalments', 'plan_id', 'instalments.inst_id'), 'int'), FF('Paid on this plan so far', sm('instalments', 'amount', 'plan_id', 'instalments.inst_id', ',{range:instalments.paid_on},">0"'), 'money')]),
 FORM('package_sheet', 'Package Sale Sheet', 'Package sale with sessions and value left', 'packages.package_id', F(
  ('Client', 'packages.client'), ('Kind', 'packages.kind'), ('Sessions', 'packages.sessions'), ('Price', 'packages.price'), ('Bought on', 'packages.bought_on'), ('Sessions used', 'packages.used'), ('Expires on', 'packages.expires_on'),
  ('Status', 'packages.status'), ('Sessions left', 'packages.sessions_left'), ('Value left', 'packages.value_left'), ('Days to expiry', 'packages.days_to_expiry'), ('Expiry check', 'packages.expiry_check')) + [
  FF('Price per session', 'IFERROR(%s/%s,0)' % (IDX('packages', 'price', 'packages.package_id'), IDX('packages', 'sessions', 'packages.package_id')), 'money'),
  FF('Share of the package used', 'IFERROR(%s/%s,0)' % (IDX('packages', 'used', 'packages.package_id'), IDX('packages', 'sessions', 'packages.package_id')), 'pct')]),
 FORM('card_sheet', 'Card on File Sheet', 'Card on file with pay method and card payments', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Phone', 'clients.phone'), ('Fee type', 'clients.fee_type'), ('Pay method', 'clients.pay_method'), ('Card on file', 'clients.card_on_file'), ('Autopay', 'clients.autopay'),
  ('Pays by instalment', 'clients.pays_by_instalment'), ('Status', 'clients.status'), ('Balance', 'clients.balance'), ('Account check', 'clients.account_flag')) + [
  FF('Card payments in the last 12 months', 'COUNTIFS({range:payments.client},%s,{range:payments.method},%s,{range:payments.date},">"&({today}-365))' % (IDX('clients', 'client', 'clients.client_id'), tok('paym', 'Card')), 'int'),
  FF('Card fees on this client\'s payments', 'SUMIFS({range:payments.card_fee},{range:payments.client},%s)' % IDX('clients', 'client', 'clients.client_id'), 'money')]),
 FORM('sliding_sheet', 'Sliding Scale Assessment Sheet', 'Sliding scale assessment and review check', 'assessments.assess_id', F(
  ('Client', 'assessments.client'), ('Assessed on', 'assessments.date'), ('Household size', 'assessments.household_size'), ('Income band', 'assessments.income_band'), ('Share agreed', 'assessments.share_agreed'),
  ('Review date', 'assessments.review_date'), ('Usual service', 'assessments.service'), ('Fee per session', 'assessments.fee_per_session'), ('Review check', 'assessments.review_check')) + [
  FF('List fee for the usual service', 'SUMIFS({range:fees.fee},{range:fees.service},%s,{range:fees.year},YEAR({today}))' % IDX('assessments', 'service', 'assessments.assess_id'), 'money'),
  FF('Concession per session', 'SUMIFS({range:fees.fee},{range:fees.service},%s,{range:fees.year},YEAR({today}))-%s' % (IDX('assessments', 'service', 'assessments.assess_id'), IDX('assessments', 'fee_per_session', 'assessments.assess_id')), 'money')]),
 FORM('rise_sheet', 'Fee Rise Notice Sheet', 'Fee rise notice with the notice period check', 'fee_notices.notice_id', F(
  ('Client', 'fee_notices.client'), ('Service', 'fee_notices.service'), ('Old fee', 'fee_notices.old_fee'), ('New fee', 'fee_notices.new_fee'), ('Notice sent on', 'fee_notices.sent_on'), ('Effective date', 'fee_notices.effective_date'),
  ('Rise', 'fee_notices.rise_share'), ('Notice, days', 'fee_notices.notice_days'), ('Notice check', 'fee_notices.notice_check')) + [
  FF('Extra per session', '%s-%s' % (IDX('fee_notices', 'new_fee', 'fee_notices.notice_id'), IDX('fee_notices', 'old_fee', 'fee_notices.notice_id')), 'money'),
  FF('Extra per year at 30 sessions', '30*(%s-%s)' % (IDX('fee_notices', 'new_fee', 'fee_notices.notice_id'), IDX('fee_notices', 'old_fee', 'fee_notices.notice_id')), 'money')]),
 FORM('writeoff_sheet', 'Write-off Sheet', 'Write-off with reason and approval', 'writeoffs.writeoff_id', F(
  ('Invoice ID', 'writeoffs.invoice_id'), ('Client', 'writeoffs.client'), ('Written off on', 'writeoffs.date'), ('Amount', 'writeoffs.amount'), ('Reason', 'writeoffs.reason'), ('Approved by', 'writeoffs.approved_by'), ('Owner phone', 'writeoffs.owner_phone')) + [
  FF('Written off for this client in total', sm('writeoffs', 'amount', 'client', 'writeoffs.writeoff_id'), 'money'),
  FF('Amount against the owner limit', 'IFERROR(%s/{set:writeoff_limit},0)' % IDX('writeoffs', 'amount', 'writeoffs.writeoff_id'), 'pct')]),
 FORM('promise_sheet', 'Payment Promise Sheet', 'Payment promise with outcome', 'promises.promise_id', F(
  ('Invoice ID', 'promises.invoice_id'), ('Client', 'promises.client'), ('Logged on', 'promises.logged_on'), ('Promised for', 'promises.promised_on'), ('Logged by', 'promises.method'), ('Outcome', 'promises.outcome'),
  ('Invoice due date', 'promises.due_date'), ('Days from the due date to the promise', 'promises.days_to_promise'), ('Promise check', 'promises.promise_flag')) + [
  FF('Promises logged for this invoice', cnt('promises', 'invoice_id', 'promises.promise_id'), 'int'),
  FF('Broken promises by this client', 'COUNTIFS({range:promises.client},%s,{range:promises.outcome},%s)' % (IDX('promises', 'client', 'promises.promise_id'), tok('promise', 'Broken')), 'int')]),
]
assert len(forms) == 12

# ---------------------------------------------------------------- documents
def D_(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('invoice_doc', 'Monthly Invoice', 'Monthly invoice for the client\'s share', 'invoices.invoice_id', [
  'Invoice {col:invoices.invoice_id} of {set:company}, issued on {col:invoices.issued_on}. Client: {col:invoices.client} (client {col:invoices.client_id}).',
  'Sessions in {col:invoices.month}: {col:invoices.sessions} with {col:invoices.clinician}. Fee type: {col:invoices.fee_type}. Amount for the sessions and any late-cancel fees: {col:invoices.amount}. Deposit applied: {col:invoices.deposit_applied}.',
  'Amount due: {col:invoices.amount_due}. Please pay by {col:invoices.due_date} by {col:invoices.method}. Paid so far: {col:invoices.paid_amount}. Balance: {col:invoices.balance}.',
  'Questions about this invoice? Contact us and quote the invoice number. A cancellation with less than {set:late_cancel_hours} hours\' notice is charged {set:late_fee_pct} of the session fee.'], ['Coordinator']),
 D_('receipt_doc', 'Payment Receipt', 'Payment receipt', 'payments.payment_id', [
  'Receipt {col:payments.payment_id} of {set:company}, dated {today}.',
  'Received on {col:payments.date} from {col:payments.client}: {col:payments.amount} by {col:payments.method}, for {col:payments.kind} {col:payments.ref}.',
  'Card fee on this payment: {col:payments.card_fee}. Amount received after the card fee: {col:payments.net_received}. Thank you for your payment.'], ['Coordinator']),
 D_('statement_doc', 'Account Statement', 'Account statement with A/R aging buckets', 'clients.client_id', [
  'Account statement of {set:company}, dated {today}. Client: {col:clients.client} (client {col:clients.client_id}). Fee type: {col:clients.fee_type}.',
  'Invoices to date: {col:clients.invoices_n}. Invoiced: {col:clients.invoiced}. Paid: {col:clients.paid_to_date}. Balance: {col:clients.balance}, of which overdue {col:clients.overdue}.',
  'Balance by age since the invoice was issued: 0 to 30 days {col:clients.bal_0_30}; 31 to 60 days {col:clients.bal_31_60}; 61 to 90 days {col:clients.bal_61_90}; over 90 days {col:clients.bal_90p}.',
  'Account check: {col:clients.account_flag}. If you cannot pay in full, contact us before the due date and we will agree a payment plan.'], ['Coordinator']),
 D_('reminder1_doc', 'First Payment Reminder', 'First payment reminder', 'invoices.invoice_id', [
  'Payment reminder of {set:company}, dated {today}. Dear {col:invoices.client},',
  'Our records show that invoice {col:invoices.invoice_id} of {col:invoices.amount_due} was due on {col:invoices.due_date}. The balance is {col:invoices.balance}, now {col:invoices.days_overdue} days past the due date.',
  'If you have already paid, thank you and please ignore this reminder. If not, please pay within {set:reminder_gap_days} days or tell us a date when you will pay.'], ['Coordinator']),
 D_('reminder2_doc', 'Final Payment Reminder', 'Final payment reminder before bookings are paused', 'invoices.invoice_id', [
  'Final payment reminder of {set:company}, dated {today}. Dear {col:invoices.client},',
  'Invoice {col:invoices.invoice_id} of {col:invoices.amount_due} was due on {col:invoices.due_date} and the balance of {col:invoices.balance} is still open. We have sent earlier reminders.',
  'Please pay within {set:reminder_gap_days} days, or contact us to agree a payment plan. Without a payment or a plan we may pause new bookings until the balance is settled.'], ['Coordinator', 'Owner']),
 D_('plan_doc', 'Payment Plan Agreement', 'Payment plan agreement (generic: adapt to your own terms)', 'plans.plan_id', [
  'Payment plan agreement of {set:company}, dated {today}. Plan {col:plans.plan_id}. Client: {col:plans.client}.',
  'The client agrees to pay a balance of {col:plans.balance} in {col:plans.instalments} instalments of {col:plans.instalment}, the first on {col:plans.start_date} and the last on {col:plans.end_date}. Invoices covered: {col:plans.invoices}.',
  'Instalments paid so far: {col:plans.paid_instalments}. Balance left: {col:plans.balance_left}. Status: {col:plans.status}. If an instalment is missed, we will contact you and may ask you to bring the plan up to date before new bookings.',
  'These are sample terms; adapt them to your own practice and check your own local rules.'], ['Client', 'Coordinator']),
 D_('package_doc', 'Package Terms and Receipt', 'Package terms and receipt', 'packages.package_id', [
  'Package receipt {col:packages.package_id} of {set:company}, dated {today}. Client: {col:packages.client}.',
  'Package: {col:packages.kind}, price {col:packages.price}, paid for on {col:packages.bought_on}. Valid until {col:packages.expires_on}.',
  'Sessions used: {col:packages.used}. Sessions left: {col:packages.sessions_left}, worth {col:packages.value_left}. Status: {col:packages.status}.',
  'A late cancel (less than {set:late_cancel_hours} hours\' notice) uses a session of the package. Sessions not used by the expiry date lapse unless we agree otherwise in writing.'], ['Client', 'Coordinator']),
 D_('sliding_doc', 'Sliding Scale Agreement', 'Sliding scale agreement', 'assessments.assess_id', [
  'Sliding scale agreement of {set:company}, dated {today}. Client: {col:assessments.client}. Reference {col:assessments.assess_id}.',
  'A sliding scale is a lower fee agreed from the client\'s means. Assessed on {col:assessments.date} for a household of {col:assessments.household_size}, income band {col:assessments.income_band}.',
  'Share of the fee agreed: {col:assessments.share_agreed}. Fee per session for {col:assessments.service}: {col:assessments.fee_per_session}. The fee will be reviewed on {col:assessments.review_date}. Review check: {col:assessments.review_check}.',
  'The client agrees to tell us if their means change and to give the details we ask for at each review.'], ['Client', 'Owner']),
 D_('feesched_doc', 'Fee Schedule for Clients', 'Fee schedule for clients', 'fees.fee_id', [
  'Fee schedule of {set:company}, year {col:fees.year}, dated {today}. Fees are per session and before any tax.',
  'Intake assessment {col:fees.fee_intake}. Individual session {col:fees.fee_individual}. Extended individual {col:fees.fee_extended}. Couples session {col:fees.fee_couples}. Family session {col:fees.fee_family}.',
  'Child session {col:fees.fee_child}. Speech therapy {col:fees.fee_speech}. Behaviour therapy {col:fees.fee_behaviour}. Review session {col:fees.fee_review}.',
  'A cancellation with less than {set:late_cancel_hours} hours\' notice (a late cancel) is charged {set:late_fee_pct} of the session fee. Invoices are due {set:invoice_days} days after they are issued. Ask us about a sliding scale or a package of sessions.'], ['Owner']),
 D_('riseletter_doc', 'Fee Rise Letter', 'Fee rise letter with the notice period', 'fee_notices.notice_id', [
  'Fee notice of {set:company}, dated {today}. Dear {col:fee_notices.client},',
  'From {col:fee_notices.effective_date} the fee for {col:fee_notices.service} will change from {col:fee_notices.old_fee} to {col:fee_notices.new_fee}, a rise of {col:fee_notices.rise_share}. We sent this notice on {col:fee_notices.sent_on}, {col:fee_notices.notice_days} days before the change.',
  'Fees are reviewed once a year to cover our costs. If the new fee is a problem, please talk to us about a sliding scale or a package. Reference {col:fee_notices.notice_id}.'], ['Owner']),
 D_('writeoff_doc', 'Write-off Note', 'Write-off note for the records', 'writeoffs.writeoff_id', [
  'Write-off note {col:writeoffs.writeoff_id} of {set:company}, dated {today}.',
  'On {col:writeoffs.date} the balance of {col:writeoffs.amount} on invoice {col:writeoffs.invoice_id} of {col:writeoffs.client} was written off. Reason: {col:writeoffs.reason}.',
  'Approved by {col:writeoffs.approved_by}. Balances above {set:writeoff_limit} need the owner. Keep this note with the account records; check your own local rules for how long.'], ['Owner', 'Accountant']),
 D_('billing_doc', 'Billing and AR Aging Report', 'Monthly billing and A/R aging report', 'billing.bill_id', [
  'Billing report of {set:company} for invoices issued in {col:billing.month}, dated {today}.',
  'Sessions charged: {col:billing.sessions_charged}. Invoiced: {col:billing.invoiced}. Concessions given: {col:billing.concessions}. Collected: {col:billing.collected}. Written off: {col:billing.written_off}. Owed at month end: {col:billing.outstanding_end}.',
  'Client payment collection rate: {col:billing.collection_rate}. Net collection rate: {col:billing.net_rate} (target {set:net_collection_target}). Days in A/R: {col:billing.days_in_ar} (maximum {set:max_days_ar}).',
  'A/R aging at the month end by days since the invoice was issued: 0 to 30 days {col:billing.ar_0_30}; 31 to 60 days {col:billing.ar_31_60}; 61 to 90 days {col:billing.ar_61_90}; over 90 days {col:billing.ar_90p}.'], ['Coordinator', 'Owner']),
]
assert len(documents) == 12

# ---------------------------------------------------------------- checklists
def CS(key_, title, table, start, steps): return _lib.CHK(key_, title, table, start, steps)
checklists = [
 CS('c_month', 'Month-end Invoicing', 'billing', 'billing.month', [('Check that every attended session has a fee', 0), ('Add late-cancel fees and take off waived ones', 0), ('Apply deposits and package sessions', 1), ('Build the invoices for the client\'s share', 1), ('Review invoices with no fee or a large change', 2), ('Send the invoices and the ready messages', 2), ('Record the billing summary for the month', 4)]),
 CS('c_payment', 'Recording a Payment', 'payments', 'payments.date', [('Record the amount, method and reference', 0), ('Record the card fee if paid by card', 0), ('Match the payment to the invoice, package or deposit', 0), ('Update the invoice status', 1), ('Send the receipt message', 1)]),
 CS('c_late', 'Late Payment Follow-up', 'invoices', 'invoices.due_date', [('Check the invoice and any promise logged', 1), ('Send the first reminder', 3), ('Phone the client and log the promised date', 7), ('Send the second reminder', 10), ('Offer a payment plan', 14), ('Send the final notice', 21), ('Decide: chase, plan or write off', 28)]),
 CS('c_plan', 'Setting up a Payment Plan', 'plans', 'plans.start_date', [('Check the balance and the invoices it covers', -7), ('Check the instalment against a month of fees', -5), ('Agree the dates and the amount with the client', -3), ('Send the plan agreement', -2), ('Ask for a card on file for the instalments', -1), ('Record the first instalment', 0)]),
 CS('c_missed', 'Missed Instalment', 'instalments', 'instalments.due_date', [('Check the bank and card records', 1), ('Send the missed-instalment message', 2), ('Phone the client', 5), ('Agree a new date or change the plan', 7), ('Tell the owner if two instalments are missed', 14)]),
 CS('c_package', 'Selling a Package', 'packages', 'packages.bought_on', [('Agree the size and the price', 0), ('Take the payment and record it', 0), ('Send the package terms and receipt', 0), ('Tell the clinician how many sessions are prepaid', 1), ('Check the sessions left after the third session', 28), ('Remind the client 30 days before expiry', 150)]),
 CS('c_card', 'Card on File at Booking', 'clients', 'clients.first_session', [('Explain the fee and late-cancel rule', -7), ('Ask for a card on file and the agreement to charge fees', -7), ('Record the card on file in the account', -5), ('Take the deposit if no card is on file', -3), ('Confirm the first session by message', -1)]),
 CS('c_sliding', 'Sliding Scale Assessment', 'assessments', 'assessments.date', [('Ask for the household income and size', 0), ('Find the band and the share of the fee', 0), ('Agree the fee per session', 0), ('Send the sliding scale agreement', 1), ('Set the review date', 1), ('Record the assessment', 1)]),
 CS('c_review', 'Sliding Scale Yearly Review', 'assessments', 'assessments.review_date', [('Send the review message 30 days before', -30), ('Ask for the new household income and size', -14), ('Find the band again', -7), ('Agree the new share', 0), ('Record the new assessment and review date', 1)]),
 CS('c_rise', 'Yearly Fee Rise', 'fee_notices', 'fee_notices.effective_date', [('Check the fee rise impact and the break-even share', -120), ('Update the fee schedule', -90), ('Send the notice with the days of notice you promise', -60), ('Answer questions and offer a sliding scale where needed', -30), ('Start the new fee on the effective date', 0), ('Check the first invoices at the new fee', 30)]),
 CS('c_writeoff', 'Writing off a Balance', 'writeoffs', 'writeoffs.date', [('Check the chase history and promises', -7), ('Run the write-off decision', -5), ('Get the owner\'s approval above the limit', -3), ('Record the write-off and the reason', 0), ('Send the account note to the client if agreed', 1), ('Tell the accountant', 7)]),
 CS('c_weekly', 'Weekly Card and Bank Check', 'cardfees', 'cardfees.month', [('Match card payments to the provider report', 2), ('Match transfers to the bank statement', 2), ('Check the card fees against the fee share', 3), ('Record cash received', 3), ('Update the chase-first list', 4)]),
]
assert len(checklists) == 12

# ---------------------------------------------------------------- messages
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
CP = 'clients.phone'
messages = [
 M('c_invoice', 'Client: your invoice is ready', 'invoices', CP, 'Hello {client}, your invoice {invoice_id} for {month} is ready: {amount_due} is due on {due_date}. Thank you, {practice}'),
 M('c_paid', 'Client: your payment is received', 'payments', 'payments.phone', 'Hello {client}, thank you: your payment of {amount} on {date} is received. {practice}'),
 M('c_due', 'Client: your invoice is due soon', 'invoices', CP, 'Hello {client}, a reminder that your invoice {invoice_id} of {balance} is due on {due_date}. {practice}'),
 M('c_balance', 'Client: a reminder of your balance', 'ar_clients', CP, 'Hello {client}, a reminder: your balance is {balance}, of which {overdue} is overdue. Please pay or tell us a date. {practice}'),
 M('c_promise', 'Client: thank you for your promise', 'promises', CP, 'Hello {client}, thank you for agreeing to pay on {promised_on}. We have noted it against invoice {invoice_id}. {practice}'),
 M('c_final', 'Client: final reminder before a pause', 'invoices', CP, 'Hello {client}, final reminder: invoice {invoice_id} of {balance} is {days_overdue} days overdue. We may pause bookings until it is paid. {practice}'),
 M('c_planoffer', 'Client: can we agree a payment plan', 'ar_clients', CP, 'Hello {client}, can we agree a payment plan for your balance of {balance}? Reply and we will suggest the instalments. {practice}'),
 M('c_planstart', 'Client: your payment plan starts', 'plans', CP, 'Hello {client}, your payment plan of {balance} starts on {start_date}: {instalments} instalments of {instalment}. {practice}'),
 M('c_instdue', 'Client: your instalment is due', 'plans', CP, 'Hello {client}, your instalment of {instalment} is due on {next_due}. Thank you, {practice}'),
 M('c_instmissed', 'Client: an instalment was missed', 'instalments', 'instalments.phone', 'Hello {client}, your instalment of {amount} due on {due_date} was missed. Please pay or contact us. {practice}'),
 M('c_plandone', 'Client: your payment plan is complete', 'plans', CP, 'Hello {client}, your payment plan is complete: thank you for paying {balance} in {instalments} instalments. {practice}'),
 M('c_pkgready', 'Client: your package is ready to use', 'packages', CP, 'Hello {client}, your package of {sessions} sessions is ready to use until {expires_on}. {practice}'),
 M('c_pkgleft', 'Client: package sessions are left', 'packages', CP, 'Hello {client}, you have {sessions_left} package sessions left, valid until {expires_on}. {practice}'),
 M('c_pkgexp', 'Client: your package expires soon', 'packages', CP, 'Hello {client}, your package expires on {expires_on} with {sessions_left} sessions left. Please book soon. {practice}'),
 M('c_newfee', 'Client: your new fee from a date', 'fee_notices', CP, 'Hello {client}, from {effective_date} your fee for {service} will be {new_fee} (now {old_fee}). {practice}'),
 M('c_slidefee', 'Client: your sliding-scale fee', 'assessments', CP, 'Hello {client}, your sliding-scale fee is {fee_per_session} per session, agreed on {date}. {practice}'),
 M('c_slidereview', 'Client: review your sliding-scale fee', 'assessments', CP, 'Hello {client}, it is time to review your sliding-scale fee. Your review date is {review_date}. Please contact us. {practice}'),
 M('c_latefee', 'Client: a late-cancel fee was added', 'sessions', CP, 'Hello {client}, a late-cancel fee of {client_amount} for your session on {date} was added to your invoice. {practice}'),
 M('c_uptodate', 'Client: your account is up to date', 'clients', CP, 'Hello {client}, your account is up to date: balance {balance}. Thank you, {practice}'),
 M('c_writeoff', 'Client: a small balance was written off', 'writeoffs', CP, 'Hello {client}, the small balance of {amount} on your account was written off on {date}. Nothing more is due. {practice}'),
 M('k_overdue', 'Clinician: a client is overdue', 'invoices', 'invoices.clinician_phone', 'Hello {clinician}, {client} has an overdue balance of {balance} ({days_overdue} days). Please mention it kindly at the next session. {practice}'),
 M('k_fee', 'Clinician: please confirm the fee', 'sessions', 'sessions.clinician_phone', 'Hello {clinician}, please confirm the fee for {client} on {date}: the list fee is {fee}. {practice}'),
 M('o_ready', 'Coordinator: invoices are ready to send', 'billing', 'billing.coordinator_phone', 'Hello {coordinator_name}, invoices for {month} are ready to send: {invoiced} for {sessions_charged} sessions. {practice}'),
 M('o_chase', 'Coordinator: today\'s chase-first list', 'ar_clients', 'ar_clients.coordinator_phone', 'Hello {coordinator_name}, chase {client} today: {overdue} overdue, {days_overdue} days past due, rank {chase_rank} on the list. {practice}'),
 M('o_missed', 'Coordinator: an instalment was missed', 'instalments', 'instalments.coordinator_phone', 'Hello {coordinator_name}, {client} missed the instalment of {amount} due on {due_date} ({days_late} days). {practice}'),
 M('o_pkgexp', 'Coordinator: a package expires soon', 'packages', 'packages.coordinator_phone', 'Hello {coordinator_name}, package {package_id} of {client} expires on {expires_on} with {sessions_left} sessions left. {practice}'),
 M('w_overdue', 'Owner: overdue balances total', 'billing', 'billing.owner_phone', 'Hello {owner_name}, from the invoices of {month}, {unpaid} is unpaid and {outstanding_end} was owed at month end. {practice}'),
 M('w_net', 'Owner: net collection rate of a month', 'billing', 'billing.owner_phone', 'Hello {owner_name}, the Net collection rate for the invoices of {month} is {net_rate}; collected {collected} of {invoiced}. {practice}'),
 M('w_rise', 'Owner: the yearly fee rise plan is ready', 'fees', 'fees.owner_phone', 'Hello {owner_name}, the {year} fee for {service} is {fee} ({vs_last_year} on last year). The fee rise plan is ready for review. {practice}'),
 M('w_writeoff', 'Owner: a write-off needs approval', 'writeoffs', 'writeoffs.owner_phone', 'Hello {owner_name}, a write-off of {amount} for {client} (invoice {invoice_id}) needs your approval. Reason: {reason}. {practice}'),
 M('w_nocard', 'Owner: overdue client, no card on file', 'ar_clients', 'ar_clients.owner_phone', 'Hello {owner_name}, {client} has an overdue balance of {overdue} and no card on file. Ask for one at the next booking. {practice}'),
 M('a_report', 'Accountant: the monthly billing report', 'billing', 'billing.accountant_phone', 'Hello {accountant_name}, the billing report for {month}: invoiced {invoiced}, collected {collected}, owed at month end {outstanding_end}. {practice}'),
 M('a_writeoff', 'Accountant: write-offs booked', 'writeoffs', 'writeoffs.accountant_phone', 'Hello {accountant_name}, a write-off of {amount} was booked on {date} for invoice {invoice_id}, approved by {approved_by}. {practice}'),
 M('a_prepaid', 'Accountant: prepaid package balances', 'packages', 'packages.accountant_phone', 'Hello {accountant_name}, package {package_id} has {value_left} of prepaid value left ({sessions_left} sessions). {practice}'),
]
assert len(messages) == 34

# ---------------------------------------------------------------- KPIs
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; LM = 'DATE(YEAR({today}),MONTH({today})-1,1)'
def D90(c): return '{range:%s},">="&({today}-90),{range:%s},"<="&{today}' % (c, c)
def D30(c): return '{range:%s},">="&({today}-29),{range:%s},"<="&{today}' % (c, c)
def BL(c, m): return 'SUMIFS({range:billing.%s},{range:billing.month},%s)' % (c, m)
kpis = [
 KPI('Invoiced this month', BL('invoiced', MS), 'money'),
 KPI('Net collection rate last month', 'IFERROR(%s/%s,0)' % (BL('collected', LM), BL('invoiced', LM)), 'pct', alert={"when": "< {set:net_collection_target}", "style": "bad"}),
 KPI('Collected this month', 'SUMIFS({range:payments.amount},{range:payments.date},">="&%s,{range:payments.date},"<="&{today})' % MS, 'money'),
 KPI('Broken payment promises last 30 days', 'COUNTIFS({range:promises.outcome},%s,%s)' % (tok('promise', 'Broken'), D30('promises.promised_on')), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Outstanding balance now', 'SUM({range:invoices.balance})', 'money'),
 KPI('Overdue balance now', 'SUMIFS({range:invoices.balance},{range:invoices.days_overdue},">0")', 'money', alert={"when": "> 0", "style": "warn"}),
 KPI('Overdue invoices', 'COUNTIFS({range:invoices.days_overdue},">0")', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Balance over 30 days overdue', 'SUMIFS({range:invoices.balance},{range:invoices.days_overdue},">30")', 'money', alert={"when": "> 0", "style": "bad"}),
 KPI('Balance over 90 days, last month end', 'SUMIFS({range:ar_months.balance},{range:ar_months.month},%s,{range:ar_months.band},%s)' % (LM, ab('90+')), 'money', alert={"when": "> 0", "style": "warn"}),
 KPI('Oldest overdue, days', 'MAX({range:invoices.days_overdue})', 'int', alert={"when": "> 30", "style": "bad"}),
 KPI('Client collection rate last month', 'IFERROR(%s/(%s+%s),0)' % (BL('collected', LM), BL('invoiced', LM), BL('concessions', LM)), 'pct'),
 KPI('Days in A/R now', 'IFERROR(SUM({range:invoices.balance})/SUMIFS({range:invoices.amount_due},%s)*90,0)' % D90('invoices.issued_on'), 'num', alert={"when": "> {set:max_days_ar}", "style": "bad"}),
 KPI('Invoices paid within terms, last 90 days', 'IFERROR(COUNTIFS({range:invoices.timing},%s,%s)/(COUNTIFS(%s)-COUNTIFS({range:invoices.timing},%s,%s)),0)' % (ca('Paid on time'), D90('invoices.issued_on'), D90('invoices.issued_on'), ca('Not yet due'), D90('invoices.issued_on')), 'pct', alert={"when": "< 0.8", "style": "warn"}),
 KPI('Unbilled charges this month', 'SUMIFS({range:sessions.client_amount},{range:sessions.billing_flag},%s)' % ca('On next invoice'), 'money'),
 KPI('Payment plans active', 'COUNTIFS({range:plans.status},%s)+COUNTIFS({range:plans.status},%s)' % (tok('planst', 'On track'), tok('planst', 'Late')), 'int'),
 KPI('Plan balance left', 'SUM({range:plans.balance_left})', 'money'),
 KPI('Instalments late', 'COUNTIFS({range:instalments.late_flag},%s)' % ca('Late'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Packages active', 'COUNTIFS({range:packages.status},%s)' % tok('pkst', 'Active'), 'int'),
 KPI('Package sessions left', 'SUMIFS({range:packages.sessions_left},{range:packages.status},%s)' % tok('pkst', 'Active'), 'int'),
 KPI('Prepaid value left', 'SUMIFS({range:packages.value_left},{range:packages.status},%s)' % tok('pkst', 'Active'), 'money'),
 KPI('Packages expiring next 30 days', 'COUNTIFS({range:packages.expiry_check},%s)' % ca('Expires in 30 days'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Clients with a card on file', 'COUNTIFS({range:clients.card_on_file},%s)' % YES, 'int'),
 KPI('Sliding scale clients', 'COUNTIFS({range:clients.fee_type},%s)' % tok('feetype', 'Sliding scale'), 'int'),
 KPI('Average sliding share of the fee', 'IFERROR(AVERAGEIFS({range:clients.sliding_pct},{range:clients.fee_type},%s),0)' % tok('feetype', 'Sliding scale'), 'pct'),
 KPI('Concession given this year', 'SUMIFS({range:billing.concessions},{range:billing.month},">="&DATE(YEAR({today}),1,1))', 'money'),
 KPI('Card fees this month', 'SUMIFS({range:cardfees.card_fees},{range:cardfees.month},%s)' % MS, 'money'),
 KPI('Card share of payments, last 30 days', 'IFERROR(SUMIFS({range:payments.amount},{range:payments.method},%s,%s)/SUMIFS({range:payments.amount},%s),0)' % (tok('paym', 'Card'), D30('payments.date'), D30('payments.date')), 'pct'),
 KPI('Write-offs, last 12 months', 'SUMIFS({range:writeoffs.amount},{range:writeoffs.date},">"&({today}-365))', 'money'),
 KPI('Clients with an overdue balance', 'COUNTIFS({range:clients.overdue},">0")', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Share of clients paying by instalment', 'IFERROR(COUNTIFS({range:clients.pays_by_instalment},%s)/COUNTA({range:clients.client}),0)' % YES, 'pct'),
]
assert len(kpis) == 30
dashboard = {"title": "Accounts KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Invoiced, collected, concessions given and package sales", "date": "billing.month", "series": [
   {"label": "Invoiced", "sum": "billing.invoiced", "date": "billing.month"}, {"label": "Collected", "sum": "billing.collected", "date": "billing.month"},
   {"label": "Concessions given", "sum": "billing.concessions", "date": "billing.month"}, {"label": "Package sales", "sum": "packages.price", "date": "packages.bought_on"}]},
 "breakdowns": [{"title": "Outstanding balance by fee type", "by": "invoices.fee_type", "value": "invoices.balance", "agg": "sum"}, {"title": "Payments by method", "by": "payments.method", "value": "payments.amount", "agg": "sum"},
                {"title": "Packages sold by kind", "by": "packages.kind", "agg": "count"}, {"title": "Collection gap by cause", "by": "gap.cause", "value": "gap.amount", "agg": "sum"}]}

# ---------------------------------------------------------------- charts and gauges
def W(c, o, v): return (c, o, v)
def GAPS(c, label): return AGG('sum', 'gap', 'gap.amount', date='gap.month', where=[('cause', '=', tok('gapcause', c))], label=label)
def ARS(b, label): return AGG('sum', 'ar_months', 'ar_months.balance', date='ar_months.month', where=[('band', '=', ab(b))], label=label)
def INS(ft, label): return AGG('sum', 'invoices', 'invoices.amount_due', date='invoices.issued_on', where=[('fee_type', '=', tok('feetype', ft))], label=label)
insights = {"filters": [{"label": "Clinician", "list": "clin"}, {"label": "Fee type", "list": "feetype"}, {"label": "Payment method", "list": "paym"}],
 "gauges": [
  {"title": "Client payment collection rate", "num": AGG('sum', 'billing', 'billing.collected'), "den": AGG('sum', 'billing', 'billing.gross_value')},
  {"title": "Invoices paid within terms", "num": AGG('count', 'invoices', where=[('timing', '=', ca('Paid on time'))]), "den": AGG('count', 'invoices', where=[('status', '=', tok('invst', 'Paid'))])},
  {"title": "Balance not overdue", "num": AGG('sum', 'invoices', 'invoices.current_balance'), "den": AGG('sum', 'invoices', 'invoices.balance')},
  {"title": "Instalments on time", "num": AGG('count', 'instalments', where=[('late_flag', '=', ca('Paid on time'))]), "den": AGG('count', 'instalments', where=[('late_flag', '<>', ca('Due later'))])},
  {"title": "Net collection rate against the target", "num": AGG('sum', 'billing', 'billing.collected'), "den": AGG('sum', 'billing', 'billing.invoiced')},
  {"title": "Clients with a card on file", "num": AGG('count', 'clients', where=[('card_on_file', '=', YES)]), "den": AGG('count', 'clients')}],
 "charts": [
  CHART('Invoiced per month', 'column', 'month', [AGG('sum', 'billing', 'billing.invoiced', date='billing.month', label='Invoiced')]),
  CHART('Cash received per month', 'column', 'month', [AGG('sum', 'cardfees', 'cardfees.all_payments', date='cardfees.month', label='Cash received')]),
  CHART('Invoiced against collected per month', 'column', 'month', [AGG('sum', 'billing', 'billing.invoiced', date='billing.month', label='Invoiced'), AGG('sum', 'billing', 'billing.collected', date='billing.month', label='Collected')]),
  CHART('Payments by method', 'bar', 'payments.method', [AGG('sum', 'payments', 'payments.amount', label='Amount')]),
  CHART('Payments by kind', 'bar', 'payments.kind', [AGG('sum', 'payments', 'payments.amount', label='Amount')]),
  CHART('Card fees per month', 'column', 'month', [AGG('sum', 'cardfees', 'cardfees.card_fees', date='cardfees.month', label='Card fees')]),
  CHART('Invoices by status', 'bar', 'invoices.status', [AGG('count', 'invoices', label='Invoices')]),
  CHART('Overdue balance by fee type', 'bar', 'invoices.fee_type', [AGG('sum', 'invoices', 'invoices.balance', where=[('days_overdue', '>', 0)], label='Overdue balance')]),
  CHART('Payment promises by outcome', 'bar', 'promises.outcome', [AGG('count', 'promises', label='Promises')]),
  CHART('Average days to pay per month', 'line', 'month', [AGG('avg', 'invoices', 'invoices.days_to_pay', date='invoices.issued_on', label='Days to pay')]),
  CHART('Packages sold per month', 'column', 'month', [AGG('count', 'packages', date='packages.bought_on', label='Packages sold')]),
  CHART('Collection gap per month by cause', 'stacked', 'month', [GAPS('Sliding scale', 'Sliding scale'), GAPS('Waived late fee', 'Waived late fee'), GAPS('Written off', 'Written off'), GAPS('Unpaid', 'Unpaid')]),
  CHART('Collection gap by cause', 'bar', 'gap.cause', [AGG('sum', 'gap', 'gap.amount', label='Amount not collected')]),
  CHART('A/R balance by age band per month', 'stacked', 'month', [ARS('0-30', '0-30 days'), ARS('31-60', '31-60 days'), ARS('61-90', '61-90 days'), ARS('90+', '90+ days')]),
  CHART('Plan instalments paid per month', 'column', 'month', [AGG('sum', 'instalments', 'instalments.amount', date='instalments.paid_on', where=[('paid_on', '>', 0)], label='Instalments paid')]),
  CHART('Payment plans by status', 'bar', 'plans.status', [AGG('count', 'plans', label='Plans')]),
  CHART('Charge by fee type', 'bar', 'sessions.fee_type', [AGG('sum', 'sessions', 'sessions.charge', label='Charge')]),
  CHART('Invoiced per month by fee type', 'stacked', 'month', [INS('Standard', 'Standard'), INS('Sliding scale', 'Sliding scale'), INS('Package', 'Package'), INS('Third-party payer', 'Third-party payer')]),
  CHART('Fee rise on last year by service', 'bar', 'fees.service', [AGG('avg', 'fees', 'fees.vs_last_year', label='Rise on last year')]),
  CHART('Write-offs per month', 'column', 'month', [AGG('sum', 'writeoffs', 'writeoffs.amount', date='writeoffs.date', label='Written off')]),
  CHART('Reminders sent per month', 'column', 'month', [AGG('count', 'reminders', date='reminders.sent_on', label='Reminders')]),
  CHART('Average charge per session by service', 'bar', 'sessions.service', [AGG('avg', 'sessions', 'sessions.charge', label='Average charge')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Monthly invoices with deposits and late fees", "why": "the client's share, late-cancel fees and the deposit applied give the amount due, the due date and a send-or-check verdict", "where": "Invoices"},
 {"name": "A/R aging and chase-first list", "why": "balance by age band, Days in A/R against your maximum and the five clients to chase first, ranked by overdue balance times days past due", "where": "AR Aging and Chase-first List"},
 {"name": "Payment reminder schedule", "why": "three reminder dates, the final notice date and today's action from the due date and any promised date", "where": "Payment Reminder Schedule"},
 {"name": "Payment plan builder with instalments", "why": "the instalment, the last date and a fit check against a quarter of a month of the client's fees", "where": "Payment Plan Builder"},
 {"name": "Package sales, use and expiry", "why": "sessions left, prepaid value left and the packages expiring in 30 days, with a deliverability check", "where": "Packages"},
 {"name": "Sliding scale calculator and assessments", "why": "income per person finds the band, the share of the fee and the review date a year later", "where": "Sliding Scale Calculator"},
 {"name": "Fee schedule and fee rise impact", "why": "the yearly revenue change and the break-even share of clients you can lose, solved in closed form", "where": "Fee Rise Impact"},
 {"name": "Write-off decision", "why": "balance, days overdue, client status and broken promises give the chance of recovery and a chase, plan or write-off verdict", "where": "Write-off Decision"},
 {"name": "Collection forecast with Base, Best, Worst", "why": "your own prompt, normal and slow payers turn the invoices into money expected each week against the pay run", "where": "Collection Forecast"},
 {"name": "Net collection rate check with the gap by cause", "why": "Net collection rate, Client payment collection rate and the gap to target in money against last month, the 3-month average and last year", "where": "Net Collection Rate Check"},
 {"name": "Card on file effect and payment method cost", "why": "what a card on file saves in chasing against the card fee, and what moving payments to bank transfer saves a year", "where": "Card on File Effect"},
 {"name": "Month-end billing close", "why": "sessions charged, invoiced, collected and owed each month, with Days in A/R and the aging buckets", "where": "Monthly Billing Summary"}]
assert 8 <= len(signature) <= 12
competitors = [
 {"what": "free invoice templates", "lacks": "print one invoice but have no balances, A/R aging, Days in A/R, deposits or late-cancel fees"},
 {"what": "subscription practice-management software", "lacks": "charge per clinician and keep your data in their system, with no editable collection targets, chase-first rank or what-if tools"},
 {"what": "single-sheet payment logs", "lacks": "record money in but cannot age balances, log payment promises, run payment plans or forecast collections"},
 {"what": "generic accounting spreadsheets", "lacks": "know nothing of sliding scale, packages, late-cancel fees or the Net collection rate and its gap by cause"},
 {"what": "generic invoice spreadsheets", "lacks": "bill a fee but never compare Client payment collection rate with Net collection rate or warn when a package discount is too deep"}]
guide = [
 'Open Start and type your practice name and your targets in the yellow cells: Net collection target (95% by default), most Days in A/R, days to pay an invoice, late-cancel fee share, deposit, card fee and write-off limit.',
 'Check Team, Fee Schedule and Sliding Scale Bands. List fees are per session and before any tax. A sliding scale is a lower fee agreed from the client\'s means. A late cancel is a cancellation with less than 24 hours\' notice. A third-party payer is an organisation that pays part of a client\'s fee; the co-pay is the part the client still pays.',
 'Record each month\'s invoices on Invoices and each payment on Payments. Balance, days overdue, A/R aging band and payment timing fill in by themselves.',
 'Open AR Aging by Client and AR Aging and Chase-first List every week: the five clients to chase first are ranked by overdue balance times days past due.',
 'Log every promise to pay on Payment Promises and every reminder on Payment Reminders. Use the Payment Reminder Schedule to see which reminder is due.',
 'Set up payment plans on Payment Plans and record each instalment on Plan Instalments. A late instalment shows red.',
 'Sell prepaid packages on Packages: sessions left, value left and the 30-day expiry check fill in. Prepaid Balance Check says whether the sessions can still be delivered.',
 'Use Sliding Scale Assessments and the Sliding Scale Calculator to agree a fee and a review date; Concession Budget shows what the sliding scale costs a year.',
 'Close each month on Monthly Billing Summary: Client payment collection rate, Net collection rate and Days in A/R. Collection Gap by Cause shows where the money went.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Why a workbook: one flat price, no per-clinician fee, and your data stays with you in your own file. The workbook holds status and amounts only, never note content. Check your own local rules for records and tax.']
listing = {"title": "Therapy Practice Client Accounts Excel Template: A/R Aging, Invoices, Payment Plans, Packages, Sliding Scale, KPI Dashboard",
 "headline": "Know who owes what, chase the right clients first and close each month in Excel",
 "tags": ["therapy practice", "accounts receivable", "ar aging", "invoice tracker", "payment plans", "sliding scale", "practice management", "excel template", "collection rate", "private practice", "counselling practice", "billing tracker", "days in ar"],
 "description": ("Run client fees, invoices, payments and balances in one Excel workbook. Built for a small group practice of talking therapists and counsellors: an owner-clinician, employed clinicians, contract (self-employed) clinicians, an associate who works under supervision and a billing coordinator.\n\n"
  "Invoices record the client's share, the deposit applied and late-cancel fees, and work out the balance, days overdue, A/R aging band (0-30, 31-60, 61-90, 90+) and whether each invoice was paid on time. "
  "AR Aging by Client ranks the clients to chase first by overdue balance times days past due; Payment Promises, Payment Reminders, Payment Plans and Plan Instalments follow every balance to the money. "
  "Packages track prepaid sessions, value left and expiry; Sliding Scale Bands and Assessments set a lower fee agreed from the client's means with a yearly review; Fee Schedule and Fee Rise Notices carry the yearly rise; Write-offs and Card Fees by Month complete the accounts. "
  "Monthly Billing Summary gives the Client payment collection rate, the Net collection rate and Days in A/R, and Collection Gap by Cause shows where the money went.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: session fee quote, sliding scale calculator, package price builder, chase-first list, payment plan builder, reminder schedule, card on file effect, fee rise impact with the break-even share of clients lost, write-off decision, collection forecast with a Base / Best / Worst switch, net collection rate check and more. "
  f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
  "This is part three of the Therapy Private Practice suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-clinician fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. The workbook holds status and amounts only, never session notes, and it does not promise results."),
 "features": ["Invoices with deposits, late-cancel fees and A/R aging bands", "Chase-first list ranked by balance times days past due", "Payment promises, reminders and a reminder schedule", "Payment plans with instalments and a fit check",
              "Packages with sessions left, value left and expiry", "Sliding scale bands, assessments and yearly review", "Fee schedule and fee rise impact with break-even", "Client payment collection rate, Net collection rate and Days in A/R",
              f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
s = _lib.spec(id=f'{SUITE}-p3', slug='therapy-practice-accounts', profession='Therapy Private Practice', name='Client Fees, Accounts and Packages',
         tagline='Know who owes what and close each month with confidence', price_usd=29, colors={"primary": "#2F5D62", "accent": "#A7C4BC"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Client fees, accounts and packages"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'th3.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
