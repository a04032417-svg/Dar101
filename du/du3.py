"""Doula Business suite - part 3: Contracts, Deposits and Payment Plans."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du3_lists import *
from du3_tables import settings, tables
from du3_tools import tools

SUITE = 'fx-20261116-doula-business'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
YR = '{range:cancels.date},">="&({today}-365)'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('contract_review', 'Contract Review Sheet', 'Contract review with price, deposit and balance', 'contracts.contract_id', F(
        ('Client', 'contracts.client'), ('Package', 'contracts.package'), ('Kind', 'contracts.kind'), ('Signed on', 'contracts.signed_on'), ('Payment plan', 'contracts.plan'), ('Status', 'contracts.status'),
        ('Price', 'contracts.price'), ('Deposit', 'contracts.deposit'), ('Paid to date', 'contracts.paid_to_date'), ('Balance outstanding', 'contracts.balance'), ('Next payment due', 'contracts.next_due')) + [
        FF('Share of the price paid', 'IFERROR(%s/%s,0)' % (LK('contracts', 'contract_id', 'paid_to_date'), LK('contracts', 'contract_id', 'price')), 'pct')]),
    FORM('deposit_receipt_sheet', 'Deposit Receipt Sheet', 'Deposit receipt with days to pay', 'deposits.contract_id', F(
        ('Client', 'deposits.client'), ('Signed on', 'deposits.signed_on'), ('Deposit', 'deposits.deposit'), ('Deposit due on', 'deposits.due_on'), ('Paid on', 'deposits.paid_on'), ('Days to pay', 'deposits.days_to_pay'), ('Status', 'deposits.status')) + [
        FF('Days since signing', '{today}-%s' % LK('deposits', 'contract_id', 'signed_on'), 'int')]),
    FORM('balance_reminder', 'Balance Reminder Sheet', 'Balance reminder with the amount still owed', 'balances.contract_id', F(
        ('Client', 'balances.client'), ('Balance due date', 'balances.balance_due'), ('Price', 'balances.price'), ('Paid so far', 'balances.paid'), ('Outstanding', 'balances.outstanding'), ('Status', 'balances.status')) + [
        FF('Days to the due date', '%s-{today}' % LK('balances', 'contract_id', 'balance_due'), 'int')]),
    FORM('payment_plan_sheet', 'Payment Plan Sheet', 'Payment plan against the on-call start', 'inst_window.client_id', F(
        ('Client', 'inst_window.client'), ('Instalments', 'inst_window.n_inst'), ('First due', 'inst_window.first_due'), ('Last due', 'inst_window.last_due'), ('On-call start', 'inst_window.oncall_start'),
        ('Days before the window', 'inst_window.days_before'), ('Unpaid amount', 'inst_window.unpaid_amount'), ('Plan check', 'inst_window.plan_flag')) + [
        FF('Days first to last instalment', '%s-%s' % (LK('inst_window', 'client_id', 'last_due'), LK('inst_window', 'client_id', 'first_due')), 'int')]),
    FORM('instalment_receipt', 'Instalment Receipt Sheet', 'Instalment receipt with days late', 'instalments.inst_id', F(
        ('Client', 'instalments.client'), ('Instalment no', 'instalments.no'), ('Of', 'instalments.of'), ('Due date', 'instalments.due_date'), ('Amount', 'instalments.amount'), ('Paid on', 'instalments.paid_on'), ('Status', 'instalments.status'), ('Days late', 'instalments.days_late'))),
    FORM('payment_received', 'Payment Received Sheet', 'Payment received with method and fee', 'payments.payment_id', F(
        ('Date', 'payments.date'), ('Client', 'payments.client'), ('Kind', 'payments.kind'), ('Amount', 'payments.amount'), ('Method', 'payments.method'), ('Card fee cost', 'payments.fee_cost')) + [
        FF('Net amount after the fee', '%s-%s' % (LK('payments', 'payment_id', 'amount'), LK('payments', 'payment_id', 'fee_cost')), 'money')]),
    FORM('overdue_account_sheet', 'Overdue Account Sheet', 'Overdue account with the chase rank', 'balances.contract_id', F(
        ('Client', 'balances.client'), ('Outstanding', 'balances.outstanding'), ('Overdue amount', 'balances.overdue_amount'), ('Days overdue', 'balances.overdue_days'), ('Ageing band', 'balances.band'), ('Chase score', 'balances.chase_score'), ('Chase rank', 'balances.rank')) + [
        FF('Share of the balance overdue', 'IFERROR(%s/%s,0)' % (LK('balances', 'contract_id', 'overdue_amount'), LK('balances', 'contract_id', 'outstanding')), 'pct')]),
    FORM('refund_request_sheet', 'Refund Request Sheet', 'Refund request with cash kept', 'cancels.cancel_id', F(
        ('Date', 'cancels.date'), ('Client', 'cancels.client'), ('Kind', 'cancels.kind'), ('Reason', 'cancels.reason'), ('Paid', 'cancels.paid'), ('Kept', 'cancels.kept'), ('Refunded', 'cancels.refunded'), ('Refund share', 'cancels.refund_share'))),
    FORM('cancel_settlement', 'Cancellation Settlement Sheet', 'Cancellation settlement from the contract', 'contracts.contract_id', F(
        ('Client', 'contracts.client'), ('Package', 'contracts.package'), ('Price', 'contracts.price'), ('Deposit', 'contracts.deposit'), ('Paid to date', 'contracts.paid_to_date'), ('On-call start', 'contracts.window_start')) + [
        FF('Days to the on-call start', '%s-{today}' % LK('contracts', 'contract_id', 'window_start'), 'int'),
        FF('Cash paid beyond the deposit', 'MAX(0,%s-%s)' % (LK('contracts', 'contract_id', 'paid_to_date'), LK('contracts', 'contract_id', 'deposit')), 'money')]),
    FORM('package_change_sheet', 'Package Change Sheet', 'Package change with price and deposit', 'contracts.contract_id', F(
        ('Client', 'contracts.client'), ('Package now', 'contracts.package'), ('List price', 'contracts.list_price'), ('Discount', 'contracts.discount'), ('Price', 'contracts.price'), ('Deposit', 'contracts.deposit'),
        ('Payment plan', 'contracts.plan'), ('Instalments', 'contracts.instalments')) + [
        FF('Deposit share of the price', 'IFERROR(%s/%s,0)' % (LK('contracts', 'contract_id', 'deposit'), LK('contracts', 'contract_id', 'price')), 'pct')]),
    FORM('hour_pack_sheet', 'Hour Pack Purchase Sheet', 'Hour pack with hours left and expiry', 'packs.pack_id', F(
        ('Client', 'packs.client'), ('Doula', 'packs.doula'), ('Package', 'packs.package'), ('Hours bought', 'packs.hours_bought'), ('Price', 'packs.price'), ('Bought on', 'packs.bought_on'), ('Expires on', 'packs.expires_on'),
        ('Hours used', 'packs.hours_used'), ('Hours left', 'packs.hours_left'), ('Earned', 'packs.earned'), ('Unearned', 'packs.unearned'), ('Days to expiry', 'packs.days_to_expiry'))),
    FORM('date_hold_sheet', 'Date Hold Sheet', 'Date hold for the on-call window', 'clients.client_id', F(
        ('Client', 'clients.client'), ('Kind', 'clients.kind'), ('Package', 'clients.package'), ('Estimated due date', 'clients.edd'), ('Doula', 'clients.doula'), ('Signed on', 'clients.signed_on'),
        ('On-call start', 'clients.oncall_start'), ('On-call end', 'clients.oncall_end'), ('Status', 'clients.status')) + [
        FF('Days from signing to the on-call start', '%s-%s' % (LK('clients', 'client_id', 'oncall_start'), LK('clients', 'client_id', 'signed_on')), 'int')]),
]

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('agreement_doc', 'Service Agreement Summary', 'Service agreement summary', 'contracts.contract_id', [
        'Service agreement summary of {set:company}, dated {today}. Client: {col:contracts.client}, signed on {col:contracts.signed_on}.',
        'Package: {col:contracts.package}. Price {col:contracts.price} after a discount of {col:contracts.discount}. Deposit {col:contracts.deposit}; the balance is due on {col:contracts.balance_due}.',
        'The on-call window starts on {col:contracts.window_start}, a date set from the estimated due date. Payment plan: {col:contracts.plan}, {col:contracts.instalments} instalments.',
        'Changes and cancellations follow the contract terms that you both signed. Please keep this summary with your copy.'], ['Owner-doula', 'Client'], NOTE),
    DOC('deposit_doc', 'Deposit Receipt', 'Deposit receipt', 'deposits.contract_id', [
        'Deposit receipt of {set:company}, dated {today}. Client: {col:deposits.client}.',
        'We received a deposit of {col:deposits.deposit} on {col:deposits.paid_on}. The contract was signed on {col:deposits.signed_on} and the deposit was due on {col:deposits.due_on}.',
        'The deposit keeps your dates held. The rest of the price follows the plan in your contract.'], ['Owner-doula', 'Client'], NOTE),
    DOC('balance_notice_doc', 'Balance Due Notice', 'Balance due notice', 'balances.contract_id', [
        'Balance due notice of {set:company}, dated {today}. Client: {col:balances.client}.',
        'The price of your package is {col:balances.price}. You have paid {col:balances.paid}. The balance of {col:balances.outstanding} is due on {col:balances.balance_due}.',
        'Please pay by the due date. If a different date suits you better, tell us before it passes and we will agree a new one.'], ['Owner-doula', 'Client'], NOTE),
    DOC('schedule_doc', 'Instalment Schedule', 'Instalment schedule', 'inst_window.client_id', [
        'Instalment schedule of {set:company}, dated {today}. Client: {col:inst_window.client}.',
        'Your plan has {col:inst_window.n_inst} instalments. The first is due on {col:inst_window.first_due} and the last on {col:inst_window.last_due}.',
        'Your on-call window starts on {col:inst_window.oncall_start}. The plan ends {col:inst_window.days_before} days before it. The amount still unpaid is {col:inst_window.unpaid_amount}.',
        'Please keep to the dates. Tell us early if one date does not suit you.'], ['Owner-doula', 'Client'], NOTE),
    DOC('receipt_doc', 'Payment Receipt', 'Payment receipt', 'payments.payment_id', [
        'Payment receipt of {set:company}, dated {today}. Received from {col:payments.client}.',
        'We received {col:payments.amount} on {col:payments.date} as a {col:payments.kind} payment by {col:payments.method}.',
        'Thank you. Please keep this receipt with your records.'], ['Owner-doula', 'Client'], NOTE),
    DOC('overdue_letter_doc', 'Overdue Reminder Letter', 'Overdue reminder letter', 'balances.contract_id', [
        'Reminder letter of {set:company}, dated {today}. Client: {col:balances.client}.',
        'Our records show that {col:balances.overdue_amount} is overdue by {col:balances.overdue_days} days. The balance still open is {col:balances.outstanding}.',
        'If you have already paid, thank you and please tell us the date. If not, please pay this week or contact us to agree a new date.'], ['Owner-doula', 'Client'], NOTE),
    DOC('refund_doc', 'Refund Confirmation', 'Refund confirmation', 'cancels.cancel_id', [
        'Refund confirmation of {set:company}, dated {today}. Client: {col:cancels.client}.',
        'Your request of {col:cancels.date} is settled. You paid {col:cancels.paid}. We keep {col:cancels.kept} under the contract terms and refund {col:cancels.refunded}.',
        'The refund goes back by the method you paid with. Please allow a few days for it to arrive.'], ['Owner-doula', 'Client'], NOTE),
    DOC('settlement_doc', 'Cancellation Settlement Letter', 'Cancellation settlement letter', 'cancels.cancel_id', [
        'Cancellation settlement letter of {set:company}, dated {today}. Client: {col:cancels.client}.',
        'We confirm your {col:cancels.kind} of {col:cancels.date}. The reason noted is {col:cancels.reason}.',
        'Cash paid {col:cancels.paid}; amount kept {col:cancels.kept}; amount refunded {col:cancels.refunded}. This follows the terms of your contract.'], ['Owner-doula', 'Client'], NOTE),
    DOC('change_doc', 'Package Change Addendum', 'Package change addendum', 'contracts.contract_id', [
        'Package change addendum of {set:company}, dated {today}. Client: {col:contracts.client}.',
        'Your package now is {col:contracts.package}. The price is {col:contracts.price} and the deposit is {col:contracts.deposit}. You have paid {col:contracts.paid_to_date}.',
        'The balance outstanding is {col:contracts.balance}. Payment plan: {col:contracts.plan}. All other terms of your contract stay the same.'], ['Owner-doula', 'Client'], NOTE),
    DOC('pack_doc', 'Hour Pack Statement', 'Hour pack statement', 'packs.pack_id', [
        'Hour pack statement of {set:company}, dated {today}. Client: {col:packs.client}.',
        'Package: {col:packs.package}. Hours bought {col:packs.hours_bought}, used {col:packs.hours_used}, left {col:packs.hours_left}. The pack was bought on {col:packs.bought_on} and ends on {col:packs.expires_on}.',
        'Unused hours end with the pack, so please book your hours before the end date.'], ['Owner-doula', 'Client'], NOTE),
    DOC('unearned_doc', 'Unearned Balance Statement', 'Unearned balance statement for the owner', 'unearned_month.month', [
        'Unearned balance statement of {set:company}, dated {today}, for the month starting {col:unearned_month.month}.',
        'Cash received in the month was {col:unearned_month.cash_received}. Revenue earned was {col:unearned_month.earned}. The change in unearned cash was {col:unearned_month.unearned_change}.',
        'Unearned cash at the end of the month is {col:unearned_month.unearned_now}. This is money held for work not yet done: keep it aside.'], ['Owner-doula', 'Accountant'], NOTE),
    DOC('statement_doc', 'Account Statement', 'Account statement for a client', 'contracts.contract_id', [
        'Account statement of {set:company}, dated {today}. Client: {col:contracts.client}.',
        'Package {col:contracts.package}, price {col:contracts.price}. Deposit {col:contracts.deposit} signed on {col:contracts.signed_on}. Paid to date {col:contracts.paid_to_date}.',
        'Balance outstanding: {col:contracts.balance}. Overdue now: {col:contracts.overdue_amount}.', 'Please contact us if anything here looks wrong.'], ['Owner-doula', 'Client'], NOTE),
]

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_contract', 'New Contract Signed Steps', 'contracts', 'contracts.signed_on', [('Send the signed copy to the client', 0), ('Write the contract in the Contracts sheet', 0), ('Send the deposit request', 1), ('Hold the on-call dates', 1), ('Set the balance due date', 2), ('Choose the payment plan', 3), ('Check the deposit is paid', 7)]),
    CHK('deposit_in', 'Deposit Received Steps', 'contracts', 'contracts.signed_on', [('Write the payment in the Payments sheet', 0), ('Send the deposit receipt', 1), ('Confirm the held dates in writing', 1), ('Check the deposit paid on date', 2), ('Update the cash received total', 3)]),
    CHK('balance_week', 'Balance Due Week Steps', 'contracts', 'contracts.balance_due', [('Send the balance reminder', -7), ('Check the balance against the price', -7), ('Send the day-before reminder', -1), ('Record the payment on the due date', 0), ('Call if nothing is paid', 2), ('Offer a new date if needed', 3)]),
    CHK('plan_setup', 'Payment Plan Set-Up Steps', 'instalments', 'instalments.due_date', [('Check the last instalment ends before the window', -7), ('Send the instalment schedule', -5), ('Offer autopay', -5), ('Remind the client two days before', -2), ('Record the instalment received', 0), ('Chase if unpaid', 3)]),
    CHK('inst_missed', 'Instalment Missed Steps', 'instalments', 'instalments.due_date', [('Check the payment was not missed in the sheet', 1), ('Send a friendly reminder', 1), ('Call the client', 4), ('Agree a new date in writing', 5), ('Send the overdue letter', 15), ('Review the plan with the owner', 30)]),
    CHK('before_window', 'Before the Window Opens Steps', 'clients', 'clients.oncall_start', [('Check the balance is paid', -14), ('Collect any unpaid amount', -10), ('Confirm the on-call dates', -7), ('Check the backup doula is set', -7), ('Send the final reminder', -3), ('Record the window start', 0)]),
    CHK('refund_req', 'Refund Request Steps', 'cancels', 'cancels.date', [('Write the request in the Refunds and Changes sheet', 0), ('Read the contract terms', 0), ('Work out the cash kept and refunded', 1), ('Send the settlement', 2), ('Pay the refund', 5), ('Note the reason', 5)]),
    CHK('cancel_steps', 'Cancellation Steps', 'cancels', 'cancels.date', [('Confirm the cancellation in writing', 0), ('Release the held dates', 0), ('Work out the amount kept', 1), ('Send the settlement letter', 2), ('Refund what is due', 5), ('Update the unearned cash', 7)]),
    CHK('package_change_steps', 'Package Change Steps', 'cancels', 'cancels.date', [('Write down the new package', 0), ('Work out the price difference', 0), ('Send the change addendum', 1), ('Collect or refund the difference', 3), ('Reset the balance date and plan', 3), ('Update the contract sheet', 5)]),
    CHK('pack_expiry', 'Hour Pack Expiry Steps', 'packs', 'packs.expires_on', [('Check the hours left', -45), ('Send the 45-day reminder', -45), ('Send the 30-day reminder', -30), ('Offer dates for the unused hours', -21), ('Send the pack statement', 0), ('Release the unearned cash', 1)]),
    CHK('month_end', 'Month-End Receipts Steps', 'receipts', 'receipts.month', [('Match every payment to a contract', 25), ('Send all receipts', 26), ('Check unpaid balances', 27), ('Update the unearned balance', 28), ('Send the statement to the accountant', 30)]),
    CHK('yearly_review', 'Yearly Contract Review Steps', 'contracts', 'contracts.signed_on', [('Review the deposit share', 0), ('Review the cancellation terms', 0), ('Check the change rate against your setting', 7), ('Review the payment plans that ran late', 14), ('Update the package prices', 21), ('Update the contract wording', 30)]),
]

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, table + '.' + phone, text)
messages = [
    M('c_dep_in', 'Client: your deposit is received', 'deposits', 'phone', 'Hello {client}, your deposit of {deposit} is received, thank you. Your dates are held. {company}'),
    M('c_dep_due', 'Client: your deposit is due', 'deposits', 'phone', 'Hello {client}, your deposit of {deposit} is due on {due_on}. It keeps your dates held. {company}'),
    M('c_bal_due', 'Client: your balance is due', 'balances', 'phone', 'Hello {client}, your balance of {outstanding} is due on {balance_due}. Please tell us if a different date suits you. {company}'),
    M('c_bal_7', 'Client: balance due in 7 days', 'balances', 'phone', 'Hello {client}, a reminder: your balance of {outstanding} is due in 7 days, on {balance_due}. {company}'),
    M('c_bal_1', 'Client: balance due tomorrow', 'balances', 'phone', 'Hello {client}, your balance of {outstanding} is due tomorrow. Thank you. {company}'),
    M('c_bal_in', 'Client: balance received', 'contracts', 'phone', 'Hello {client}, your balance was received, thank you. Your price of {price} is now paid in full. {company}'),
    M('c_plan_start', 'Client: your payment plan starts', 'instalments', 'phone', 'Hello {client}, your payment plan starts on {due_date}. Instalment {no} of {of} is {amount}. {company}'),
    M('c_inst_due', 'Client: instalment due', 'instalments', 'phone', 'Hello {client}, instalment {no} of {of} is due on {due_date}. The amount is {amount}. {company}'),
    M('c_inst_in', 'Client: instalment received', 'instalments', 'phone', 'Hello {client}, instalment {no} of {of} was received on {paid_on}, thank you. {company}'),
    M('c_inst_late', 'Client: instalment is late', 'instalments', 'phone', 'Hello {client}, your instalment {no} of {of} is {days_late} days late. Please pay or contact us to agree a date. {company}'),
    M('c_contact', 'Client: please contact us', 'balances', 'phone', 'Hello {client}, please contact us about your balance of {outstanding}. We would like to find a plan that works for you. {company}'),
    M('c_final', 'Client: final reminder before window', 'clients', 'phone', 'Hello {client}, a final reminder before your on-call window opens on {oncall_start}: a balance of {outstanding} is still open. {company}'),
    M('c_plan_end', 'Client: your plan ends before window', 'inst_window', 'phone', 'Hello {client}, your plan ends on {last_due}, which is {days_before} days before your window opens on {oncall_start}. {company}'),
    M('c_move', 'Client: we can move your instalment date', 'instalments', 'phone', 'Hello {client}, we can move the date of instalment {no} of {of}, now {due_date}. Tell us what suits you. {company}'),
    M('c_refund', 'Client: your refund is on its way', 'cancels', 'phone', 'Hello {client}, your refund of {refunded} is on its way. Please allow a few days. {company}'),
    M('c_cancel', 'Client: your cancellation settlement', 'cancels', 'phone', 'Hello {client}, we have your request of {date}. You paid {paid}; we keep {kept} under the contract and refund {refunded}. {company}'),
    M('c_change', 'Client: your package change is confirmed', 'cancels', 'phone', 'Hello {client}, your package change of {date} is confirmed. Cash paid {paid}, kept {kept}, refunded {refunded}. {company}'),
    M('c_pack_left', 'Client: your hour pack has hours left', 'packs', 'phone', 'Hello {client}, your hour pack has {hours_left} hours left and ends on {expires_on}. Shall we book your hours? {company}'),
    M('c_pack_30', 'Client: your hour pack ends in 30 days', 'packs', 'phone', 'Hello {client}, your hour pack ends in 30 days, on {expires_on}, with {hours_left} hours left. {company}'),
    M('c_pack_end', 'Client: your hour pack ended', 'packs', 'phone', 'Hello {client}, your hour pack ended on {expires_on}. Your statement shows {hours_used} hours used. {company}'),
    M('c_receipt', 'Client: your payment receipt', 'payments', 'phone', 'Hello {client}, we received {amount} on {date}. Your receipt is ready. {company}'),
    M('c_statement', 'Client: your account statement is ready', 'contracts', 'phone', 'Hello {client}, your account statement is ready. Paid to date {paid_to_date}, balance {balance}. {company}'),
    M('c_how_pay', 'Client: confirm how you will pay', 'payments', 'phone', 'Hello {client}, please confirm how you would like to pay your next payment. Your last one was by {method}. {company}'),
    M('c_autopay', 'Client: autopay is available', 'instalments', 'phone', 'Hello {client}, autopay is available for your instalments. Instalment {no} of {of} is due on {due_date}. Reply yes to set it up. {company}'),
    M('o_unpaid', 'Owner: a client has an unpaid balance', 'balances', 'owner_phone', 'Hello, {client} has an unpaid balance of {overdue_amount}, {overdue_days} days overdue. {company}'),
    M('o_inst_4', 'Owner: an instalment is due in 4 days', 'instalments', 'owner_phone', 'Hello, the instalment of {client} is due in 4 days, on {due_date}, for {amount}. {company}'),
    M('o_unearned', 'Owner: unearned cash this month', 'unearned_month', 'owner_phone', 'Hello, unearned cash is {unearned_now} this month. Keep it aside until the work is done. {company}'),
    M('o_rate', 'Owner: change rate and your setting', 'change_rate', 'owner_phone', 'Hello, the change rate is {rate} in the month of {month}: {rate_flag}. {company}'),
    M('o_window', 'Owner: window entered, balance unpaid', 'clients', 'owner_phone', 'Hello, {client} enters the on-call window on {oncall_start} with {outstanding} unpaid. {company}'),
    M('o_next_week', 'Owner: cash receipts expected next week', 'receipts', 'owner_phone', 'Hello, cash receipts expected next week are {due_next_7}. {company}'),
    M('a_chase', 'Admin: balances to chase today', 'balances', 'admin_phone', 'Hello, please chase {client} today: {outstanding} outstanding, status {status}. {company}'),
    M('a_receipts', 'Admin: receipts to send this week', 'payments', 'admin_phone', 'Hello, please send the receipt for {client}: {amount} received on {date}. {company}'),
    M('a_packs', 'Admin: hour packs ending this month', 'packs', 'admin_phone', 'Hello, the pack of {client} ends on {expires_on} with {hours_left} hours left. Please remind the client. {company}'),
    M('acc_month', 'Accountant: month-end unearned balance', 'unearned_month', 'accountant_phone', 'Hello, month of {month}: cash received {cash_received}, earned {earned}, unearned balance {unearned_now}. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
D30 = '{range:payments.date},">="&({today}-30),{range:payments.date},"<="&{today}'
DM = '{range:payments.date},">="&%s,{range:payments.date},"<="&{today}' % MS
INSD = lambda lo, hi: '{range:instalments.status},%s,{range:instalments.due_date},">="&%s,{range:instalments.due_date},"<="&%s' % (tok('istatus', 'Unpaid'), lo, hi)
NEAR = ca('Near expiry')
kpis = [
    KPI('Contracts signed this month', 'COUNTIFS({range:contracts.signed_on},">="&%s,{range:contracts.signed_on},"<="&{today})' % MS, 'int'),
    KPI('Deposits received this month', 'SUMIFS({range:payments.amount},%s,{range:payments.kind},%s)' % (DM, tok('paykind', 'Deposit')), 'money'),
    KPI('Deposits due and unpaid', 'COUNTIFS({range:deposits.status},%s)+COUNTIFS({range:deposits.status},%s)' % (ca('Deposit due'), ca('Deposit overdue')), 'int'),
    KPI('Balances due next 30 days', 'SUM({range:contracts.due_30})', 'money'),
    KPI('Balances overdue', 'SUM({range:contracts.overdue_amount})', 'money'),
    KPI('Number of clients overdue', 'COUNTIFS({range:contracts.overdue_amount},">0")', 'int'),
    KPI('Oldest overdue in days', 'MAX({range:contracts.overdue_days})', 'int'),
    KPI('Overdue 0 to 30 days', 'SUMIFS({range:contracts.overdue_amount},{range:contracts.ageing_band},%s)' % tok('band', AGE[1]), 'money'),
    KPI('Overdue 31 to 60 days', 'SUMIFS({range:contracts.overdue_amount},{range:contracts.ageing_band},%s)' % tok('band', AGE[2]), 'money'),
    KPI('Overdue 61 days and over', 'SUMIFS({range:contracts.overdue_amount},{range:contracts.ageing_band},%s)' % tok('band', AGE[3]), 'money'),
    KPI('Instalments due next 7 days', 'COUNTIFS(%s)' % INSD('{today}', '({today}+7)'), 'int'),
    KPI('Instalments overdue', 'COUNTIFS({range:instalments.status},%s,{range:instalments.due_date},"<"&{today})' % tok('istatus', 'Unpaid'), 'int'),
    KPI('Clients on instalments', 'COUNTIFS({range:contracts.plan},%s,{range:contracts.status},"<>"&%s)' % (tok('plan', 'Instalments'), tok('ctstatus', 'Cancelled')), 'int'),
    KPI('Plans ending after the on-call start', 'COUNTIFS({range:inst_window.plan_flag},%s)' % ca('Ends after the window'), 'int'),
    KPI('Cash received this month', 'SUMIFS({range:payments.amount},%s)' % DM, 'money'),
    KPI('Cash received last 30 days', 'SUMIFS({range:payments.amount},%s)' % D30, 'money'),
    KPI('Cash expected next 30 days', 'ROUND(SUM({range:contracts.due_30})*{set:on_time_share},0)', 'money'),
    KPI('Collection rate last 90 days', 'IFERROR(SUMIFS({range:instalments.amount},{range:instalments.status},%s,{range:instalments.due_date},">="&({today}-90),{range:instalments.due_date},"<="&{today})/SUMIFS({range:instalments.amount},{range:instalments.due_date},">="&({today}-90),{range:instalments.due_date},"<="&{today}),0)' % tok('istatus', 'Paid'), 'pct'),
    KPI('Average days to pay a deposit', 'IFERROR(AVERAGE({range:deposits.days_to_pay}),0)', 'num'),
    KPI('Average days late on balances', 'IFERROR(AVERAGE({range:contracts.days_late_balance}),0)', 'num'),
    KPI('Unearned cash now', 'SUM({range:unearned_client.unearned})', 'money'),
    KPI('Unearned share of cash received', 'IFERROR(SUM({range:unearned_client.unearned})/SUM({range:unearned_client.paid}),0)', 'pct'),
    KPI('Earned this month', 'SUMIFS({range:pnl.earned},{range:pnl.month},%s)' % MS, 'money'),
    KPI('Hour packs near expiry', 'COUNTIFS({range:packs.pack_flag},%s)' % NEAR, 'int'),
    KPI('Unused hours in packs near expiry', 'SUMIFS({range:packs.hours_left},{range:packs.pack_flag},%s)' % NEAR, 'num'),
    KPI('Refunded last 12 months', 'SUMIFS({range:cancels.refunded},%s)' % YR, 'money'),
    KPI('Kept deposits last 12 months', 'SUMIFS({range:cancels.kept},%s)' % YR, 'money'),
    KPI('Change and cancel rate, 12 months', 'IFERROR(COUNTIFS(%s)/COUNTIFS({range:contracts.signed_on},">="&({today}-365),{range:contracts.signed_on},"<="&{today}),0)' % YR, 'pct'),
    KPI('Cancellations last 90 days', 'COUNTIFS({range:cancels.date},">="&({today}-90),{range:cancels.kind},%s)' % tok('cxkind', 'Cancelled'), 'int'),
    KPI('Top refund reason', 'IFERROR(INDEX({range:refund_reasons.reason},MATCH(MAX({range:refund_reasons.count}),{range:refund_reasons.count},0)),"")', 'text'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Contracts and Payments", "kpis": kpis,
    "monthly": {"title": "Cash received, refunded and earned per month", "date": "payments.date", "series": [
        {"label": "Cash received", "sum": "payments.amount", "date": "payments.date"}, {"label": "Refunded", "sum": "cancels.refunded", "date": "cancels.date"}, {"label": "Earned revenue", "sum": "pnl.earned", "date": "pnl.month"}]},
    "breakdowns": [{"title": "Cash received by kind", "by": "payments.kind", "value": "payments.amount", "agg": "sum"}, {"title": "Contracts by payment plan", "by": "contracts.plan", "value": "contracts.price", "agg": "count"},
                   {"title": "Unpaid amount by ageing band", "by": "ageing.band", "value": "ageing.unpaid_amount", "agg": "sum"}, {"title": "Refunded by reason", "by": "cancels.reason", "value": "cancels.refunded", "agg": "sum"}]}
KD, KB = tok('paykind', 'Deposit'), tok('paykind', 'Balance')
insights = {"filters": [{"label": "Package", "list": "package"}, {"label": "Payment plan", "list": "plan"}, {"label": "Payment method", "list": "method"}],
    "gauges": [
        {"title": "Balances collected on time", "num": AGG('count', 'contracts', where=[('balance_paid_on', '>', 0), ('days_late_balance', '<=', 0)]), "den": AGG('count', 'contracts', where=[('balance_paid_on', '>', 0)])},
        {"title": "Instalments paid on time", "num": AGG('count', 'instalments', where=[('status', '=', tok('istatus', 'Paid')), ('days_late', '<=', 0)]), "den": AGG('count', 'instalments', where=[('status', '=', tok('istatus', 'Paid'))])},
        {"title": "Collection rate, instalments due so far", "num": AGG('count', 'instalments', where=[('status', '=', tok('istatus', 'Paid'))]), "den": AGG('count', 'instalments', where=[('due_date', '<=', '{today}')])},
        {"title": "Open clients paid up to date", "num": AGG('count', 'clients', where=[('status', '<>', tok('cstatus', 'Completed')), ('status', '<>', tok('cstatus', 'Cancelled')), ('outstanding', '<=', 0)]),
         "den": AGG('count', 'clients', where=[('status', '<>', tok('cstatus', 'Completed')), ('status', '<>', tok('cstatus', 'Cancelled'))])},
        {"title": "Change and cancellation rate, all months", "num": AGG('sum', 'change_rate', 'change_rate.changes'), "den": AGG('sum', 'change_rate', 'change_rate.contracts_signed')},
        {"title": "Plans ending before the on-call window", "num": AGG('count', 'inst_window', where=[('plan_flag', '=', ca('Ends before the window'))]), "den": AGG('count', 'inst_window')}],
    "charts": [
        CHART('Cash received per month', 'column', 'month', [AGG('sum', 'payments', 'payments.amount', date='payments.date', label='Cash received')]),
        CHART('Cash received by kind', 'bar', 'payments.kind', [AGG('sum', 'payments', 'payments.amount', label='Cash received')]),
        CHART('Cash received by method', 'bar', 'payments.method', [AGG('sum', 'payments', 'payments.amount', label='Cash received')]),
        CHART('Deposits per month', 'column', 'month', [AGG('sum', 'payments', 'payments.amount', date='payments.date', where=[('kind', '=', KD)], label='Deposits')]),
        CHART('Balances received per month', 'column', 'month', [AGG('sum', 'payments', 'payments.amount', date='payments.date', where=[('kind', '=', KB)], label='Balances')]),
        CHART('Instalments by status', 'bar', 'instalments.status', [AGG('count', 'instalments', label='Instalments')]),
        CHART('Instalments due per month', 'column', 'month', [AGG('sum', 'instalments', 'instalments.amount', date='instalments.due_date', label='Instalments due')]),
        CHART('Clients by status', 'bar', 'clients.status', [AGG('count', 'clients', label='Clients')]),
        CHART('Contracts per month', 'column', 'month', [AGG('count', 'contracts', date='contracts.signed_on', label='Contracts')]),
        CHART('Contracts by plan', 'bar', 'contracts.plan', [AGG('count', 'contracts', label='Contracts')]),
        CHART('Contracts by status', 'bar', 'contracts.status', [AGG('count', 'contracts', label='Contracts')]),
        CHART('Contracts by package', 'bar', 'contracts.package', [AGG('count', 'contracts', label='Contracts')]),
        CHART('Unpaid amount by ageing band', 'bar', 'ageing.band', [AGG('sum', 'ageing', 'ageing.unpaid_amount', label='Unpaid amount')]),
        CHART('Refunds per month', 'column', 'month', [AGG('sum', 'cancels', 'cancels.refunded', date='cancels.date', label='Refunded')]),
        CHART('Refunded by reason', 'bar', 'cancels.reason', [AGG('sum', 'cancels', 'cancels.refunded', label='Refunded')]),
        CHART('Changes by kind', 'bar', 'cancels.kind', [AGG('count', 'cancels', label='Changes')]),
        CHART('Cancellations per month', 'column', 'month', [AGG('count', 'cancels', date='cancels.date', where=[('kind', '=', tok('cxkind', 'Cancelled'))], label='Cancellations')]),
        CHART('Earned revenue per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.earned', date='pnl.month', label='Earned revenue')]),
        CHART('Postpartum income per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.postpartum_income', date='pnl.month', label='Postpartum income')]),
        CHART('Hour packs bought per month', 'column', 'month', [AGG('count', 'packs', date='packs.bought_on', label='Hour packs')]),
        CHART('Hour packs by package', 'bar', 'packs.package', [AGG('count', 'packs', label='Hour packs')]),
        CHART('Payments per month', 'column', 'month', [AGG('count', 'payments', date='payments.date', label='Payments')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Deposit and balance tracker", "why": "deposits unpaid, balances overdue in the 0 to 30, 31 to 60 and 61 or more day bands, and the client to chase first", "where": "Deposit and Balance Tracker"},
    {"name": "Payment plan builder", "why": "split a balance into 2 to 6 instalments and see if the plan ends before the on-call window and what is still unpaid when it opens", "where": "Payment Plan Builder"},
    {"name": "Prepaid earned vs unearned", "why": "cash held for work not yet done, per client and in total, earned by phase at shares you set", "where": "Prepaid Earned vs Unearned"},
    {"name": "Refund and change analyser", "why": "the change and cancellation rate set against your own setting, the cash kept and refunded and the top reason", "where": "Refund and Change Analyser"},
    {"name": "Cancellation settlement", "why": "type a client and a date to see the cash kept, the refund and the unearned cash released", "where": "Cancellation Settlement"},
    {"name": "Cash receipts forecast", "why": "instalments and balances due in the next 12 weeks times your own on-time share, in Base, Best and Worst", "where": "Cash Receipts Forecast"},
    {"name": "Window-entry balance check", "why": "clients who enter the on-call window soon with money still owed, and who to chase first", "where": "Window-Entry Balance Check"},
    {"name": "Overdue chase ranking", "why": "unpaid balances ranked by amount times days overdue, so the call list is never a guess", "where": "Overdue Chase Ranking"},
    {"name": "Payment plan risk check", "why": "plans that end after the on-call start and plans with a late instalment, named before the window opens", "where": "Payment Plan Risk Check"}]
competitors = [
    {"what": "free invoice and payment trackers", "lacks": "list what was paid but never split a balance over instalments that end before the on-call window or age what is unpaid"},
    {"what": "subscription booking and billing software", "lacks": "charge every month and do not show unearned cash, hour pack expiry or the change rate against your own setting"},
    {"what": "single-sheet client ledgers", "lacks": "hold one total per client with no deposit check, no ageing bands and no chase order"},
    {"what": "general bookkeeping spreadsheets", "lacks": "record cash in and out but not prepaid packages, earned against unearned cash or the settlement of a cancellation"},
    {"what": "paper contract folders", "lacks": "keep the signed pages but never warn that a balance is due, an instalment is late or a pack is about to end"}]
guide = [
    'Open Start and type your business name and your own limits in the yellow cells: days before the estimated due date that the on-call window opens, balance weeks, days between instalments, your on-time share and your cash floor.',
    'Check Packages and Team. They hold the prices and deposit shares that the contract sheets look up.',
    'Write every client in Clients and every contract in Contracts: package, price, deposit, signed on, balance due date, payment plan and status. The balance, the next due date and the ageing band fill in.',
    'Add each instalment in Instalments and each payment in Payments. Overdue days, days late and card fees are calculated.',
    'Write each hour pack in Hour Packs. Hours left, earned and unearned cash and the near-expiry check fill in.',
    'Log every refund, package change and cancellation in Refunds and Changes with the date, reason, cash kept and refunded.',
    'Read Deposit Tracker, Balance Due List and Ageing Buckets each week to see who to remind and who to call.',
    'Use Instalments Before the Window to see plans that end after the on-call start, and Unearned by Client and Unearned by Month for cash held for work not yet done.',
    f'Use the {len(tools)} calculators to build a plan, settle a cancellation, rank overdue balances, forecast 12 weeks of cash and test your deposit share.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Contracts and Payments and the charts every week: cash received, overdue amounts, unearned cash and the change rate.']
listing = {"title": "Doula Contracts, Deposits and Payment Plans Excel Template: Balance Ageing, Unearned Cash, Refund Tracker, Cash Forecast",
    "headline": "Know what is paid, late and unearned, from signing to the birth",
    "tags": ["doula", "doula contract", "deposit tracker", "payment plan", "accounts receivable", "deferred revenue", "unearned revenue", "doula business", "excel template", "cash forecast", "refund tracker", "client payments", "doula agency"],
    "description": ("Run the money between signing and the birth for a doula practice or agency in one Excel workbook. Built for an owner-doula and an admin who track deposits, balances, payment plans and refunds. "
        "Contracts records every client with the package, price, deposit, balance due date and payment plan, and works out the balance, the next due date, the overdue amount and the ageing band. Instalments, Payments and Hour Packs keep every payment, every instalment and every prepaid pack.\n\n"
        "Deposit Tracker, Balance Due List and Ageing Buckets show who owes what in bands of 0 to 30, 31 to 60 and 61 or more days. Instalments Before the Window shows plans that end after the on-call start. Unearned by Client and Unearned by Month show cash received for work not yet done (unearned cash, also called deferred revenue). "
        "Refunds and Changes and the change rate by month show cancellations, package changes and the cash kept and refunded against a rate you set.\n\n"
        f"{len(tools)} calculators cover the deposit and balance tracker, a payment plan builder, prepaid earned against unearned, the refund analyser, a cancellation settlement, overdue ranking, reminder timing, plan risk, a 12-week cash forecast, deposit share, a prepay discount, contract changes, hour pack release, late payers, card fees, window entry and reconciliation. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to clients, the owner-doula, the admin and the accountant.\n\n"
        "This is part three of the Doula Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Clients appear by name, package, dates and money only, with no medical detail. It helps you keep track of your money and does not promise results. Check your local rules for contract terms."),
    "features": ["Deposit and balance tracker with ageing bands", "Payment plan builder that checks the on-call start", "Unearned cash by client and by month", "Cancellation settlement in one step", "12-week cash receipts forecast", "Overdue chase ranking",
                 "Hour pack expiry and revenue release", "Refund and change rate against your setting", f"{len(tools)} calculators for payment decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
HINTS = {
 'packs': 'One row per prepaid hour pack: package, hours, price and dates; hours left, earned and unearned cash, days to expiry and the pack check fill in by themselves.',
 'unearned_client': 'One row per open client: cash paid, the part earned by phase and pack hours, and the unearned cash with its release month; all fill in from the other sheets.',
 'receipts': 'One row per month: deposits, balances, instalments, hour invoices and add-ons received, with the due in 7 days and the unearned cash; all fill in by themselves.',
 'deposit_track': 'Type the days that count as due soon and the smallest overdue amount worth a call; see unpaid deposits, overdue bands and who to chase first.',
 'prepaid': 'Type a client and the hours you will deliver next month; see cash paid, earned and unearned (cash for work not yet done) for the client and in total.',
 'refund_tool': 'Type the highest change rate you accept and the contracts you expect; see 12 months of changes, cash kept and refunded, the top reason and expected refunds.',
 'cancel_settle': 'Type a client, a cancellation date and the shares you keep; see the cash kept, the refund and the unearned cash released.',
 'plan_risk': 'Type how many days before the on-call start a plan should end and what counts as late; see plans that end late and the share paid late.',
 'cash_forecast': 'Pick Base, Best or Worst and the lowest weekly receipts you accept; see 12 weeks of expected cash from your own on-time share and the first thin week.',
 'deposit_share': 'Type a package price and the largest loss you accept if a client cancels; see deposits of 20 to 50 percent, the price left unsecured and the share you need.',
 'prepay_discount': 'Type the price, the discount, the months the cash arrives earlier and what money costs you; see the break-even discount and the yearly effect.',
 'late_payer': 'Type a client and the days that count as late; see instalments paid and unpaid, late ones, average and worst days late and whether to offer autopay.',
 'window_entry': 'Type the days ahead to look and the smallest unpaid balance; see who enters the on-call window owing money and who to chase first.',
 'deposit_track_': '',
}
for _t in tables + tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
s = spec(id=f'{SUITE}-p3', slug='doula-business-contracts', profession='Doula Business', name='Contracts, Deposits and Payment Plans',
         tagline='Know what is paid, what is late and what is still unearned', price_usd=29,
         colors={"primary": "#4A3F6B", "accent": "#E8A87C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Contracts, deposits and payment plans"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'du3.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
