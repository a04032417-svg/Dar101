"""Car Rental Business suite - part 4: Deposits, Payments and Payouts."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr4_lists import *
from cr4_tables import settings, tables, HELD, SHORT, LATE, EXP, CARD, CASH, PAYO, MS
from cr4_tools import tools
import cr4_data as D

SUITE = 'fx-20261115-car-rental'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def LKS(t, idc, c): return 'IFERROR(%s&"","")' % LK(t, idc, c)
PAYOUT = tok('paykind', 'Payout')

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('deposit_receipt_sheet', 'Deposit Receipt Sheet', 'Receipt for a deposit or card hold', 'deposits.deposit_id', F(
        ('Booking', 'deposits.booking_id'), ('Vehicle', 'deposits.vehicle_id'), ('Renter', 'deposits.renter'), ('Class', 'deposits.class'), ('Amount', 'deposits.amount'), ('Held on', 'deposits.held_on'),
        ('Release due', 'deposits.release_due'), ('Status', 'deposits.status')) + [
        FF('Days allowed before release', '{set:deposit_release_days}', 'int'), FF('Days from held date to release date', LK('deposits', 'deposit_id', 'release_due') + '-' + LK('deposits', 'deposit_id', 'held_on'), 'int'),
        FF('Deposits held for this renter', 'SUMIFS({range:deposits.amount},{range:deposits.renter},%s,{range:deposits.status},%s)' % (LK('deposits', 'deposit_id', 'renter'), HELD), 'money')]),
    FORM('deposit_release_sheet', 'Deposit Release Sheet', 'Release of a deposit after the return', 'deposits.deposit_id', F(
        ('Booking', 'deposits.booking_id'), ('Renter', 'deposits.renter'), ('Amount held', 'deposits.amount'), ('Release due', 'deposits.release_due'), ('Released on', 'deposits.released_on'),
        ('Refunded amount', 'deposits.refunded_amount'), ('Kept amount', 'deposits.kept_amount'), ('Release timing', 'deposits.on_time')) + [
        FF('Amount to refund', LK('deposits', 'deposit_id', 'amount') + '-' + LK('deposits', 'deposit_id', 'kept_amount'), 'money'),
        FF('Days from release date to release', 'IF(%s>0,%s-%s,0)' % (LK('deposits', 'deposit_id', 'released_on'), LK('deposits', 'deposit_id', 'released_on'), LK('deposits', 'deposit_id', 'release_due')), 'int')]),
    FORM('deposit_kept_sheet', 'Deposit Kept Sheet', 'Amount kept from a deposit with its support', 'kept.deposit_id', F(
        ('Booking', 'kept.booking_id'), ('Kept for', 'kept.reason'), ('Kept amount', 'kept.kept_amount'), ('Claim', 'kept.claim_id'), ('Claim amount', 'kept.claim_amount'), ('Fees collected', 'kept.fees_collected'),
        ('Fees plus claim', 'kept.supported'), ('Amount to explain', 'kept.unexplained'), ('Support check', 'kept.check')) + [
        FF('Amount refunded to the renter', 'IFERROR(INDEX({range:deposits.refunded_amount},MATCH({pick},{range:deposits.deposit_id},0)),0)', 'money'),
        FF('Share of the deposit kept', 'IFERROR(%s/INDEX({range:deposits.amount},MATCH({pick},{range:deposits.deposit_id},0)),0)' % LK('kept', 'deposit_id', 'kept_amount'), 'pct')]),
    FORM('payment_receipt_sheet', 'Payment Receipt Sheet', 'Receipt for a payment', 'payments.payment_id', F(
        ('Date', 'payments.date'), ('Booking', 'payments.booking_id'), ('Renter', 'payments.renter'), ('Channel', 'payments.channel'), ('Kind', 'payments.kind'), ('Method', 'payments.method'), ('Amount', 'payments.amount'),
        ('Card fee', 'payments.card_fee')) + [
        FF('Amount after the card fee', LK('payments', 'payment_id', 'amount') + '-' + LK('payments', 'payment_id', 'card_fee'), 'money'),
        FF('Payments on this booking', 'COUNTIFS({range:payments.booking_id},%s)' % LK('payments', 'payment_id', 'booking_id'), 'int'),
        FF('Paid on this booking so far', 'SUMIFS({range:payments.amount},{range:payments.booking_id},%s)' % LK('payments', 'payment_id', 'booking_id'), 'money')]),
    FORM('payout_check_sheet', 'Payout Check Sheet', 'Payout checked against the booking', 'payouts.payout_id', F(
        ('Booking', 'payouts.booking_id'), ('Marketplace', 'payouts.channel'), ('Returned on', 'payouts.returned_on'), ('Booking value', 'payouts.booking_value'), ('Fee', 'payouts.fee'), ('Fee share charged', 'payouts.fee_share'),
        ('Expected payout', 'payouts.expected_payout'), ('Expected on', 'payouts.expected_on'), ('Received', 'payouts.received'), ('Status', 'payouts.status')) + [
        FF('Fee share agreed', 'IFERROR(INDEX({range:channels.fee_pct},MATCH(%s,{range:channels.channel},0)),0)' % LK('payouts', 'payout_id', 'channel'), 'pct'),
        FF('Booking value less fee', LK('payouts', 'payout_id', 'booking_value') + '-' + LK('payouts', 'payout_id', 'fee'), 'money'),
        FF('Days promised by the marketplace', 'IFERROR(INDEX({range:channels.payout_days},MATCH(%s,{range:channels.channel},0)),0)' % LK('payouts', 'payout_id', 'channel'), 'int')]),
    FORM('short_paid_sheet', 'Short-paid Payout Sheet', 'Payout that was short or late, with the gap', 'payouts.payout_id', F(
        ('Booking', 'payouts.booking_id'), ('Marketplace', 'payouts.channel'), ('Expected payout', 'payouts.expected_payout'), ('Expected on', 'payouts.expected_on'), ('Received', 'payouts.received'),
        ('Paid on', 'payouts.paid_on'), ('Status', 'payouts.status'), ('Gap to chase', 'payouts.gap'), ('Days late', 'payouts.days_late')) + [
        FF('Days since the expected date', '{today}-' + LK('payouts', 'payout_id', 'expected_on'), 'int'),
        FF('Gap as a share of the expected payout', 'IFERROR(%s/%s,0)' % (LK('payouts', 'payout_id', 'gap'), LK('payouts', 'payout_id', 'expected_payout')), 'pct'),
        FF('Days you allow before chasing', '{set:payout_grace_days}', 'int')]),
    FORM('invoice_sheet', 'Invoice Sheet', 'Invoice with balance and age', 'invoices.invoice_id', F(
        ('Account', 'invoices.account'), ('Booking', 'invoices.booking_id'), ('Issued on', 'invoices.issued_on'), ('Due date', 'invoices.due_date'), ('Amount', 'invoices.amount'), ('Credit note amount', 'invoices.credit_amount'),
        ('Paid amount', 'invoices.paid_amount'), ('Balance', 'invoices.balance'), ('Days overdue', 'invoices.days_overdue'), ('Age band', 'invoices.age_band'), ('Status', 'invoices.status')) + [
        FF('Days allowed to pay', LK('invoices', 'invoice_id', 'due_date') + '-' + LK('invoices', 'invoice_id', 'issued_on'), 'int'), FF('Days you set for corporate invoices', '{set:invoice_terms_days}', 'int'),
        FF('Share of the invoice paid', 'IFERROR(%s/%s,0)' % (LK('invoices', 'invoice_id', 'paid_amount'), LK('invoices', 'invoice_id', 'amount')), 'pct')]),
    FORM('invoice_split_sheet', 'Invoice Split Sheet', 'Invoice split into rental, fees and damage', 'inv_lines.invoice_id', F(
        ('Account', 'inv_lines.account'), ('Rental', 'inv_lines.rental'), ('Add-ons and fees', 'inv_lines.addons_fees'), ('Damage', 'inv_lines.damage'), ('Total of lines', 'inv_lines.total'), ('Invoice amount', 'inv_lines.invoice_amount'),
        ('Lines check', 'inv_lines.check'), ('Invoice balance', 'inv_lines.balance')) + [
        FF('Payable now without damage', LK('inv_lines', 'invoice_id', 'rental') + '+' + LK('inv_lines', 'invoice_id', 'addons_fees'), 'money'),
        FF('Share of the invoice that is damage', 'IFERROR(%s/%s,0)' % (LK('inv_lines', 'invoice_id', 'damage'), LK('inv_lines', 'invoice_id', 'total')), 'pct'),
        FF('Lines on the split invoice', 'IF(%s>0,1,0)+IF(%s>0,1,0)+IF(%s>0,1,0)' % (LK('inv_lines', 'invoice_id', 'rental'), LK('inv_lines', 'invoice_id', 'addons_fees'), LK('inv_lines', 'invoice_id', 'damage')), 'int')]),
    FORM('promise_sheet', 'Promise to Pay Sheet', 'Payment promise and its next step', 'promises.invoice_id', F(
        ('Account', 'promises.account'), ('Promised on', 'promises.promised_on'), ('Promised amount', 'promises.amount'), ('Outcome', 'promises.outcome'), ('Last contact', 'promises.last_contact'),
        ('Invoice balance', 'promises.balance'), ('Days to the promised date', 'promises.days_to_go'), ('Next step', 'promises.verdict')) + [
        FF('Balance not covered by the promise', LK('promises', 'invoice_id', 'balance') + '-' + LK('promises', 'invoice_id', 'amount'), 'money'),
        FF('Days since the last contact', '{today}-' + LK('promises', 'invoice_id', 'last_contact'), 'int'), FF('Days you allow after the promised date', '{set:promise_grace_days}', 'int')]),
    FORM('credit_note_sheet', 'Credit Note Sheet', 'Credit note against an invoice', 'invoices.invoice_id', F(
        ('Account', 'invoices.account'), ('Issued on', 'invoices.issued_on'), ('Amount', 'invoices.amount'), ('Credit note amount', 'invoices.credit_amount'), ('Amount after credit', 'invoices.net_amount'),
        ('Paid amount', 'invoices.paid_amount'), ('Balance', 'invoices.balance')) + [
        FF('Credit as a share of the invoice', 'IFERROR(%s/%s,0)' % (LK('invoices', 'invoice_id', 'credit_amount'), LK('invoices', 'invoice_id', 'amount')), 'pct'),
        FF('Credit notes on this account', 'COUNTIFS({range:invoices.account},%s,{range:invoices.credit_amount},">0")' % LK('invoices', 'invoice_id', 'account'), 'int'),
        FF('Credit given on this account', 'SUMIFS({range:invoices.credit_amount},{range:invoices.account},%s)' % LK('invoices', 'invoice_id', 'account'), 'money')]),
    FORM('daily_till_sheet', 'Daily Till Sheet', 'Cash counted against cash expected for one day', 'till.till_id', F(
        ('Date', 'till.date'), ('Cash counted', 'till.counted'), ('Cash expected', 'till.expected'), ('Difference', 'till.difference'), ('Verdict', 'till.verdict')) + [
        FF('Difference as a share of cash expected', 'IFERROR(%s/%s,0)' % (LK('till', 'till_id', 'difference'), LK('till', 'till_id', 'expected')), 'pct'),
        FF('Tills balanced, last 30 days', 'COUNTIFS({range:till.date},">="&({today}-30),{range:till.verdict},%s)' % c1('Balanced'), 'int'),
        FF('Difference you accept', '{set:till_tolerance}', 'money')]),
    FORM('corp_account_sheet', 'Corporate Account Sheet', 'Corporate account with balance and credit', 'corporate.account', F(
        ('Open balance', 'corporate.balance'), ('Average days to pay', 'corporate.avg_days')) + [
        FF('Credit limit', '{set:credit_limit}', 'money'), FF('Room left under the limit', '{set:credit_limit}-' + LK('corporate', 'account', 'balance'), 'money'),
        FF('Open invoices', 'COUNTIFS({range:invoices.account},{pick},{range:invoices.balance},">0")', 'int'),
        FF('Overdue balance', 'SUMIFS({range:invoices.balance},{range:invoices.account},{pick},{range:invoices.days_overdue},">0")', 'money'),
        FF('Promises pending', 'COUNTIFS({range:promises.account},{pick},{range:promises.outcome},%s)' % tok('outcome', 'Pending'), 'int'),
        FF('Days you allow to pay', '{set:invoice_terms_days}', 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('deposit_receipt_doc', 'Deposit Receipt', 'Receipt for a deposit', 'deposits.deposit_id', [
        'Deposit receipt of {set:company}, dated {today}. Receipt for {col:deposits.deposit_id}, booking {col:deposits.booking_id}.',
        'We hold {col:deposits.amount} for {col:deposits.renter} from {col:deposits.held_on}. A deposit is an amount held on a card or kept until the car is back.',
        'We plan to release it by {col:deposits.release_due}, within {set:deposit_release_days} days of the return. Check your hire terms for how a deposit is released or kept.'], ['Manager', 'Renter'], NOTE),
    DOC('deposit_release_doc', 'Deposit Release Note', 'Note on the release of a deposit', 'deposits.deposit_id', [
        'Deposit release note of {set:company}, dated {today}. Deposit {col:deposits.deposit_id}, booking {col:deposits.booking_id}, renter {col:deposits.renter}.',
        'Amount held: {col:deposits.amount}. Released on: {col:deposits.released_on}. Refunded: {col:deposits.refunded_amount}. Kept: {col:deposits.kept_amount}.',
        'Release due date: {col:deposits.release_due}. Timing: {col:deposits.on_time}.'], ['Manager', 'Renter'], NOTE),
    DOC('deposit_kept_doc', 'Deposit Kept Statement', 'Statement of an amount kept from a deposit', 'deposits.deposit_id', [
        'Statement of {set:company}, dated {today}. Deposit {col:deposits.deposit_id}, booking {col:deposits.booking_id}.',
        'Deposit amount: {col:deposits.amount}. Kept: {col:deposits.kept_amount} for {col:deposits.reason}. Refunded: {col:deposits.refunded_amount}. Status: {col:deposits.status}.',
        'Claim: {col:deposits.claim_id}, claim amount {col:deposits.claim_amount}. This statement gives status and amounts only. Check your hire terms and your insurance terms.'], ['Manager', 'Renter'], NOTE),
    DOC('invoice_doc', 'Rental Invoice', 'Rental invoice for a corporate account', 'invoices.invoice_id', [
        'Invoice {col:invoices.invoice_id} of {set:company}, issued on {col:invoices.issued_on}. Account: {col:invoices.account}. Booking: {col:invoices.booking_id}.',
        'Amount: {col:invoices.amount}. Credit note amount: {col:invoices.credit_amount}. Paid so far: {col:invoices.paid_amount}. Balance: {col:invoices.balance}. Amounts are before any sales tax (confirm with your adviser).',
        'Please pay by {col:invoices.due_date}. Payment terms are {set:invoice_terms_days} days unless agreed otherwise.'], ['Bookkeeper', 'Account'], NOTE),
    DOC('split_invoice_doc', 'Split Invoice', 'Invoice split into rental, fees and damage', 'inv_lines.invoice_id', [
        'Split invoice {col:inv_lines.invoice_id} of {set:company}, dated {today}. Account: {col:inv_lines.account}.',
        'Rental: {col:inv_lines.rental}. Add-ons and fees: {col:inv_lines.addons_fees}. Damage: {col:inv_lines.damage}. Total: {col:inv_lines.total}.',
        'You can pay the rental and the fees now: {col:inv_lines.payable_now}. The damage line shows status and amount only and can be questioned on its own. Check your hire terms.'], ['Bookkeeper', 'Account'], NOTE),
    DOC('reminder_doc', 'Payment Reminder', 'Reminder for an unpaid invoice', 'invoices.invoice_id', [
        'Payment reminder of {set:company}, dated {today}. Invoice {col:invoices.invoice_id} for {col:invoices.account}.',
        'The balance of {col:invoices.balance} was due on {col:invoices.due_date} and is {col:invoices.days_overdue} days overdue.',
        'Please pay it or tell us the date you will pay. If you already paid, thank you, and please tell us the date.'], ['Manager', 'Account'], NOTE),
    DOC('final_reminder_doc', 'Final Payment Reminder', 'Final reminder for an overdue invoice', 'invoices.invoice_id', [
        'Final payment reminder of {set:company}, dated {today}. Invoice {col:invoices.invoice_id}, account {col:invoices.account}.',
        'The balance of {col:invoices.balance} is {col:invoices.days_overdue} days overdue (age band {col:invoices.age_band}). The balance of the whole account is {col:invoices.account_balance}.',
        'Please pay within {set:promise_grace_days} days or call us to agree a date. After that we may stop new bookings on the account.'], ['Owner', 'Account'], NOTE),
    DOC('statement_doc', 'Account Statement', 'Statement of account for a corporate account', 'invoices.invoice_id', [
        'Statement of account of {set:company}, dated {today}. Account: {col:invoices.account}.',
        'Balance of the account: {col:invoices.account_balance}. Of this overdue: {col:invoices.account_overdue}. Credit limit: {set:credit_limit}.',
        'This statement lists the invoice {col:invoices.invoice_id} of {col:invoices.amount} issued on {col:invoices.issued_on}, due {col:invoices.due_date}, balance {col:invoices.balance}. Amounts are before any sales tax.'], ['Bookkeeper', 'Account'], NOTE),
    DOC('payout_report_doc', 'Payout Report', 'Marketplace payout report for one payout', 'payouts.payout_id', [
        'Payout report of {set:company}, dated {today}. Payout {col:payouts.payout_id}, booking {col:payouts.booking_id}, {col:payouts.channel}.',
        'Booking value: {col:payouts.booking_value}. Marketplace fee: {col:payouts.fee} ({col:payouts.fee_share} of the value). Expected payout: {col:payouts.expected_payout} on {col:payouts.expected_on}.',
        'Received: {col:payouts.received}. Paid on: {col:payouts.paid_on}. Difference: {col:payouts.difference}. Days late: {col:payouts.days_late}. Status: {col:payouts.status}.'], ['Bookkeeper', 'Manager'], NOTE),
    DOC('daily_cash_doc', 'Daily Cash Sheet', 'Cash sheet for one day', 'till.till_id', [
        'Daily cash sheet of {set:company}, dated {today}. Day: {col:till.date}.',
        'Cash expected from payments: {col:till.expected}. Cash counted: {col:till.counted}. Difference: {col:till.difference}. Result: {col:till.verdict}.',
        'A difference above {set:till_tolerance} should be written down with the reason before the cash is banked.'], ['Counted by', 'Checked by'], NOTE),
    DOC('weekly_cash_doc', 'Weekly Cash View', 'Cash view of one forecast week', 'forecast.weekno', [
        'Weekly cash view of {set:company}, dated {today}. Week {col:forecast.weekno}, starting {col:forecast.week_start}.',
        'Payouts expected: {col:forecast.payouts}. Invoice receipts: {col:forecast.invoices_in}. Rental receipts: {col:forecast.rentals_in}. Deposits to release: {col:forecast.deposits_out}. Costs due: {col:forecast.costs_out}.',
        'Net: {col:forecast.net}. Cash at the end of the week: {col:forecast.cash_end} against a floor of {col:forecast.floor}. Result: {col:forecast.verdict}.'], ['Owner', 'Bookkeeper'], NOTE),
    DOC('credit_note_doc', 'Credit Note', 'Credit note against an invoice', 'invoices.invoice_id', [
        'Credit note of {set:company}, dated {today}. Invoice {col:invoices.invoice_id}, account {col:invoices.account}.',
        'Invoice amount: {col:invoices.amount}. Credit note amount: {col:invoices.credit_amount}. Amount after credit: {col:invoices.net_amount}.',
        'Paid so far: {col:invoices.paid_amount}. Balance after the credit: {col:invoices.balance}. Amounts are before any sales tax.'], ['Bookkeeper', 'Account'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('take_deposit_chk', 'Taking a Deposit Steps', 'deposits', 'deposits.held_on', [('Check the deposit set for the class', -1), ('Place the hold or take the deposit', 0), ('Record it in Deposits', 0), ('Send the deposit message', 0), ('Note the release date', 0), ('Check it again after the return', 5)]),
    CHK('release_deposit_chk', 'Releasing a Deposit Steps', 'deposits', 'deposits.release_due', [('Check the car is back and the check-in is done', -2), ('Check fees and any open claim', -1), ('Release the hold or refund the amount', 0), ('Record the release date and amounts', 0), ('Send the release message', 0), ('Check the next statement', 7)]),
    CHK('till_chk', 'Daily Till Check Steps', 'till', 'till.date', [('Count the cash in the drawer', 0), ('Take out the float', 0), ('Write the amount in Daily Till Log', 0), ('Check the difference', 0), ('Write the reason for any difference', 0), ('Bank the cash', 1)]),
    CHK('weekly_dep_chk', 'Weekly Deposit Review Steps', 'card_cal', 'card_cal.date', [('Open Holds to Release', 0), ('Release every hold that is due', 0), ('Check holds past the release date', 0), ('Check holds kept for a claim', 1), ('Match the held total to the card report', 1), ('Tell the owner the amount held', 2)]),
    CHK('payout_check_chk', 'Marketplace Payout Check Steps', 'payouts', 'payouts.expected_on', [('Find the payout in Payouts', 0), ('Check the booking value and the fee', 0), ('Check the amount received against the expected payout', 1), ('Mark it paid, short or late', 1), ('Write to the marketplace about any gap', 3), ('Check again after the grace days', 5)]),
    CHK('monthly_recon_chk', 'Monthly Payout Reconciliation', 'recon', 'recon.month', [('Wait for the last payout of the month', 7), ('Open Payout Reconciliation', 8), ('Check every month and marketplace for a gap', 8), ('Chase every gap', 9), ('Check the fee share against the agreed share', 10), ('Send the totals to the bookkeeper', 12)]),
    CHK('weekly_chase_chk', 'Weekly Invoice Chase Steps', 'invoices', 'invoices.due_date', [('Open Invoice and Balance Chase', 1), ('Send the reminder for new overdue invoices', 1), ('Call the accounts in the 8-30 and 31-60 buckets', 3), ('Write each promise to pay', 3), ('Check the promises that fell due', 7), ('Send the final reminder or escalate', 14)]),
    CHK('month_end_chk', 'Month-End Invoicing Steps', 'liability', 'liability.month', [('Check that every rental is invoiced', 28), ('Send the statements to the accounts', 30), ('Record the deposits held at month end', 30), ('Record payouts received in the month', 31), ('Send the totals to the bookkeeper', 32), ('Send the marketplace fees to the accountant', 33)]),
    CHK('short_follow_chk', 'Short-Paid Payout Follow-Up', 'payouts', 'payouts.expected_on', [('Write down the expected amount and the amount received', 1), ('Send the short-paid message to the marketplace', 1), ('Keep the booking and fee details at hand', 2), ('Check the reply after three days', 4), ('Chase again with the gap amount', 7), ('Record the correction when it arrives', 14)]),
    CHK('account_review_chk', 'Corporate Account Review Steps', 'invoices', 'invoices.issued_on', [('Check the open balance against the credit limit', 30), ('Check the average days to pay', 30), ('Check missed promises', 31), ('Decide to extend credit, hold or ask for payment', 32), ('Tell the account the decision', 33)]),
    CHK('weekly_forecast_chk', 'Weekly Cash Forecast Steps', 'cash_day', 'cash_day.date', [('Type the cash at the bank in Settings', 0), ('Check payouts expected this week', 0), ('Check deposits to release', 0), ('Check invoice receipts and promises', 1), ('Run the Four-Week Cash Forecast', 1), ('Tell the owner if cash dips below the floor', 1)]),
    CHK('host_money_chk', 'One-Car Host Money Check Steps', 'bookings', 'bookings.start_date', [('Take the deposit or hold', -1), ('Record the payment', -1), ('Check the balance before pickup', 0), ('Release the deposit after the return', 5), ('Record the marketplace payout when it arrives', 7), ('Check that the payout matches the expected amount', 8)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def fn(name): return first_name(name)
OWN = fn(OWNER); MGR = fn(MANAGER); BKP = fn(D.BOOKKEEPER['name']); ACC = fn(D.ACCOUNTANT['name']); LEN = fn([t for t in team if t['role'] == 'Lender'][0]['name'])
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
def TO(name, body): return 'Hello %s, %s' % (name, body)
messages = [
    M('dep_held', 'Renter: a deposit is held on your card', 'deposits', 'deposits.phone', 'Hello {renter}, a deposit of {amount} is held on your card from {held_on}. We release it after the car is back. {company}'),
    M('dep_released', 'Renter: your deposit was released', 'deposits', 'deposits.phone', 'Hello {renter}, your deposit of {amount} was released on {released_on}. Thank you. {company}'),
    M('dep_due', 'Renter: your deposit will be released', 'deposits', 'deposits.phone', 'Hello {renter}, your deposit of {amount} will be released by {release_due}. {company}'),
    M('dep_kept', 'Renter: part of the deposit was kept', 'deposits', 'deposits.phone', 'Hello {renter}, we kept {kept_amount} of your deposit for {reason}, the rest is returned. {company}'),
    M('pay_ok', 'Renter: your payment was received', 'payments', 'payments.phone', 'Hello {renter}, your payment of {amount} for {booking_id} was received on {date}, thank you. {company}'),
    M('pay_balance', 'Renter: please pay the balance', 'bookings', 'bookings.phone', 'Hello {renter}, please pay the balance of {balance} for {booking_id} before the pickup on {start_date}. {company}'),
    M('pay_receipt', 'Renter: your receipt', 'payments', 'payments.phone', 'Hello {renter}, your receipt for {booking_id}: {amount} paid by {method} on {date}. {company}'),
    M('dep_refund', 'Renter: a refund is on its way', 'deposits', 'deposits.phone', 'Hello {renter}, a refund of {refunded_amount} is on its way to your card. {company}'),
    M('inv_due', 'Account: your invoice is due', 'invoices', 'invoices.phone', 'Hello, invoice {invoice_id} for {amount} is due on {due_date}. Thank you. {company}'),
    M('inv_overdue', 'Account: your invoice is overdue', 'invoices', 'invoices.phone', 'Hello, invoice {invoice_id} is {days_overdue} days overdue, balance {balance}. Please pay or tell us the date. {company}'),
    M('acc_statement', 'Account: your statement', 'invoices', 'invoices.phone', 'Hello, your statement for {month} shows a balance of {account_balance} for {account}. {company}'),
    M('promise_ack', 'Account: your payment promise', 'promises', 'promises.phone', 'Hello, thank you: we agreed to your payment of {amount} on {promised_on} for {invoice_id}. {company}'),
    M('split_note', 'Account: we split your invoice', 'invoices', 'invoices.phone', 'Hello, we split {invoice_id} into rental, fees and damage so each part can be paid or questioned alone. {company}'),
    M('confirm_date', 'Account: confirm the payment date', 'invoices', 'invoices.phone', 'Hello, please confirm the payment date for {invoice_id}, balance {balance}. {company}'),
    M('mp_expected', 'Marketplace support: payout expected', 'payouts', 'payouts.support_phone', 'Hello, payout {payout_id} for booking {booking_id} was expected on {expected_on}, amount {expected_payout}. Please confirm. {company}'),
    M('mp_short', 'Marketplace support: payout was short', 'payouts', 'payouts.support_phone', 'Hello, payout {payout_id} was short by {gap}: expected {expected_payout}, received {received}. Please explain. {company}'),
    M('mp_fee', 'Marketplace support: explain the fee', 'payouts', 'payouts.support_phone', 'Hello, please explain the fee of {fee} on booking {booking_id}, booking value {booking_value}. {company}'),
    M('mp_late', 'Marketplace support: payout is late', 'payouts', 'payouts.support_phone', 'Hello, payout {payout_id} is {days_late} days late, amount {expected_payout}. {company}'),
    M('hotel_comm', 'Hotel partner: the commission', 'feeshare', 'feeshare.hotel_phone', 'Hello, the commission for {month} is {hotel_commission}. Thank you. {company}'),
    M('ow_late', 'Owner: payouts late or short', 'payouts', 'payouts.owner_phone', TO(OWN, '{late_n} payouts are late or short, {gap_total} in total. {company}')),
    M('ow_held', 'Owner: deposits held now', 'deposits', 'deposits.owner_phone', TO(OWN, '{held_now} in deposits is held now. {company}')),
    M('ow_overdue', 'Owner: holds past the release date', 'deposits', 'deposits.owner_phone', TO(OWN, '{overdue_n} holds are past their release date. {company}')),
    M('ow_cash', 'Owner: the cash forecast', 'forecast', 'forecast.owner_phone', TO(OWN, 'the cash forecast is lowest in week {lowest_week} at {lowest_cash}, against a floor of {floor}. {company}')),
    M('ow_payouts', 'Owner: payouts expected this week', 'forecast', 'forecast.owner_phone', TO(OWN, 'payouts expected in the week starting {week_start} are {payouts}. {company}')),
    M('mg_release', 'Manager: release these deposits today', 'deposits', 'deposits.manager_phone', TO(MGR, '{release_n} deposits are due to release today, {release_amount} in all. {company}')),
    M('mg_chase', 'Manager: chase these invoices today', 'invoices', 'invoices.manager_phone', TO(MGR, '{chase_n} invoices are overdue, {chase_amount} in all. Please chase them today. {company}')),
    M('mg_till', 'Manager: the till is off', 'till', 'till.manager_phone', TO(MGR, 'the till is {difference} off for {date}. Please write down the reason. {company}')),
    M('mg_recon', 'Manager: reconcile the payouts', 'recon', 'recon.manager_phone', TO(MGR, 'please reconcile the marketplace payouts for {month}. {company}')),
    M('bk_held', 'Bookkeeper: deposits held at month end', 'liability', 'liability.bookkeeper_phone', TO(BKP, 'deposits held at the end of {month} are {held_end}. {company}')),
    M('bk_payouts', 'Bookkeeper: payouts received', 'feeshare', 'feeshare.bookkeeper_phone', TO(BKP, 'payouts received in {month} are {pay_payout}. {company}')),
    M('bk_invoices', 'Bookkeeper: invoices outstanding', 'liability', 'liability.bookkeeper_phone', TO(BKP, 'invoices unpaid at the end of {month} are {invoices_open_end}. {company}')),
    M('ac_methods', 'Accountant: payment methods summary', 'feeshare', 'feeshare.accountant_phone', TO(ACC, 'payments for {month}: card {pay_card}, mobile wallet {pay_wallet}, cash {pay_cash}, bank transfer {pay_transfer}, payouts {pay_payout}. {company}')),
    M('ac_fees', 'Accountant: fees for the year', 'feeshare', 'feeshare.accountant_phone', TO(ACC, 'the marketplace fees for {year} are {year_fees}. {company}')),
    M('lender_date', 'Lender: our payment date', 'feeshare', 'feeshare.lender_phone', TO(LEN, 'please confirm our loan payment date for {month}. {company}')),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def R(t, c): return '{range:%s.%s}' % (t, c)
D90 = '%s,">="&({today}-90)'
kpis = [
    KPI('Deposits held now', 'COUNTIFS(%s,%s)' % (R('deposits', 'status'), HELD), 'int'),
    KPI('Deposit liability held now', 'SUMIFS(%s,%s,%s)' % (R('deposits', 'amount'), R('deposits', 'status'), HELD), 'money'),
    KPI('Deposits to release, next 7 days', 'COUNTIFS(%s,%s,%s,">"&{today},%s,"<="&({today}+7))' % (R('deposits', 'status'), HELD, R('deposits', 'release_due'), R('deposits', 'release_due')), 'int'),
    KPI('Deposits past the release date', 'COUNTIFS(%s,">0")' % R('deposits', 'days_over'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Oldest held deposit, days past due', 'MAX(%s)' % R('deposits', 'days_over'), 'int'),
    KPI('Deposits kept, last 90 days', 'SUMIFS(%s,%s)' % (R('deposits', 'kept_amount'), D90 % R('deposits', 'released_on')), 'money'),
    KPI('Share of deposits kept, last 90 days', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (R('deposits', 'kept_amount'), D90 % R('deposits', 'released_on'), R('deposits', 'amount'), D90 % R('deposits', 'released_on')), 'pct'),
    KPI('Payments received this month', 'SUMIFS(%s,%s,%s)' % (R('payments', 'amount'), R('payments', 'month'), MS), 'money'),
    KPI('Payments received, last 30 days', 'SUMIFS(%s,%s)' % (R('payments', 'amount'), R('payments', 'date') + ',">="&({today}-30)'), 'money'),
    KPI('Cash in, last 7 days', 'SUMIFS(%s,%s)' % (R('payments', 'amount'), R('payments', 'date') + ',">="&({today}-7)'), 'money'),
    KPI('Card share of payments, last 90 days', 'IFERROR(SUMIFS(%s,%s,%s,%s)/SUMIFS(%s,%s),0)' % (R('payments', 'amount'), R('payments', 'method'), CARD, D90 % R('payments', 'date'), R('payments', 'amount'), D90 % R('payments', 'date')), 'pct'),
    KPI('Cash share of payments, last 90 days', 'IFERROR(SUMIFS(%s,%s,%s,%s)/SUMIFS(%s,%s),0)' % (R('payments', 'amount'), R('payments', 'method'), CASH, D90 % R('payments', 'date'), R('payments', 'amount'), D90 % R('payments', 'date')), 'pct'),
    KPI('Marketplace payouts received this month', 'SUMIFS(%s,%s,">="&%s,%s,"<="&{today})' % (R('payouts', 'received'), R('payouts', 'paid_on'), MS, R('payouts', 'paid_on')), 'money'),
    KPI('Payouts expected, next 14 days', 'SUMIFS(%s,%s,%s,%s,">"&{today},%s,"<="&({today}+14))' % (R('payouts', 'expected_payout'), R('payouts', 'status'), EXP, R('payouts', 'expected_on'), R('payouts', 'expected_on')), 'money'),
    KPI('Payouts late or short now', 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (R('payouts', 'status'), SHORT, R('payouts', 'status'), LATE), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Amount short or late now', 'SUM(%s)' % R('payouts', 'gap'), 'money'),
    KPI('Oldest late payout, days', 'SUMPRODUCT(MAX(((%s=%s)+(%s=%s))*({today}-%s)))' % (R('payouts', 'status'), SHORT, R('payouts', 'status'), LATE, R('payouts', 'expected_on')), 'int'),
    KPI('Average days to payout, last 90 days', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (R('payouts', 'days_to_pay'), D90 % R('payouts', 'paid_on')), 'num'),
    KPI('Marketplace fees this month', 'SUMIFS(%s,%s,%s)' % (R('payouts', 'fee'), R('payouts', 'month'), MS), 'money'),
    KPI('Marketplace fee share, last 3 months', 'IFERROR(SUMIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)/SUMIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s),0)' % (
        R('feeshare', 'marketplace_fees'), R('feeshare', 'month'), MS, R('feeshare', 'month'), MS, R('feeshare', 'revenue'), R('feeshare', 'month'), MS, R('feeshare', 'month'), MS), 'pct'),
    KPI('Invoices open now', 'COUNTIFS(%s,">0")' % R('invoices', 'balance'), 'int'),
    KPI('Balance owed by corporate accounts', 'SUM(%s)' % R('invoices', 'balance'), 'money'),
    KPI('Balance over 30 days overdue', 'SUMIFS(%s,%s,">30")' % (R('invoices', 'balance'), R('invoices', 'days_overdue')), 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Balance over 60 days overdue', 'SUMIFS(%s,%s,">60")' % (R('invoices', 'balance'), R('invoices', 'days_overdue')), 'money', alert={"when": "> 0", "style": "bad"}),
    KPI('Collection rate, due last 90 days', 'IFERROR((SUMIFS(%s,%s,">="&({today}-90),%s,"<"&{today})+SUMIFS(%s,%s,">="&({today}-90),%s,"<"&{today}))/SUMIFS(%s,%s,">="&({today}-90),%s,"<"&{today}),0)' % (
        R('invoices', 'paid_amount'), R('invoices', 'due_date'), R('invoices', 'due_date'), R('invoices', 'credit_amount'), R('invoices', 'due_date'), R('invoices', 'due_date'), R('invoices', 'amount'), R('invoices', 'due_date'), R('invoices', 'due_date')), 'pct'),
    KPI('Average days to pay, last 90 days', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (R('invoices', 'days_to_pay'), D90 % R('invoices', 'paid_on')), 'num'),
    KPI('Promises to pay due this week', 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<="&({today}+7))' % (R('promises', 'outcome'), tok('outcome', 'Pending'), R('promises', 'promised_on'), R('promises', 'promised_on')), 'int'),
    KPI('Daily till difference, last 30 days', 'SUMIFS(%s,%s,">="&({today}-30))' % (R('till', 'difference'), R('till', 'date')), 'money'),
    KPI('Cash forecast, lowest week', 'INDEX(%s,1)' % R('forecast', 'lowest_cash'), 'money'),
    KPI('Card fees, last 30 days', 'SUMIFS(%s,%s)' % (R('payments', 'card_fee'), R('payments', 'date') + ',">="&({today}-30)'), 'money'),
]
assert len(kpis) == 30
dashboard = {"title": "Payments Dashboard", "kpis": kpis,
    "monthly": {"title": "Payments, payouts, deposits and invoices", "date": "payments.date", "series": [
        {"label": "Payments received", "sum": "payments.amount", "date": "payments.date"}, {"label": "Marketplace payouts", "sum": "payouts.received", "date": "payouts.paid_on"},
        {"label": "Deposits taken", "sum": "deposits.amount", "date": "deposits.held_on"}, {"label": "Invoices issued", "sum": "invoices.amount", "date": "invoices.issued_on"}]},
    "breakdowns": [{"title": "Payments by method", "by": "payments.method", "value": "payments.amount", "agg": "sum"}, {"title": "Deposits by status", "by": "deposits.status", "value": "deposits.amount", "agg": "sum"},
                   {"title": "Payouts by status", "by": "payouts.status", "agg": "count"}, {"title": "Invoice amount by status", "by": "invoices.status", "value": "invoices.amount", "agg": "sum"}]}
insights = {"filters": [{"label": "Channel", "list": "channel"}, {"label": "Payment method", "list": "method"}, {"label": "Deposit status", "list": "depstatus"}],
    "gauges": [
        {"title": "Deposits released on time", "num": AGG('count', 'deposits', where=[('on_time', '=', c1('On time'))]), "den": AGG('count', 'deposits', where=[('on_time', '<>', c1('Still held'))])},
        {"title": "Payouts received against expected", "num": AGG('sum', 'payouts', 'payouts.received', where=[('status', '<>', EXP)]), "den": AGG('sum', 'payouts', 'payouts.expected_payout', where=[('status', '<>', EXP)])},
        {"title": "Invoices collected within terms", "num": AGG('count', 'invoices', where=[('terms', '=', c1('Paid within terms'))]), "den": AGG('count', 'invoices', where=[('terms', '<>', c1('Open'))])},
        {"title": "Collection rate, last 12 months", "num": AGG('sum', 'invoices', 'invoices.paid_amount', where=[('age_days', '<=', 365)]), "den": AGG('sum', 'invoices', 'invoices.net_amount', where=[('age_days', '<=', 365)])},
        {"title": "Daily till checks balanced", "num": AGG('count', 'till', where=[('verdict', '=', c1('Balanced'))]), "den": AGG('count', 'till')},
        {"title": "Forecast weeks above the floor", "num": AGG('count', 'forecast', where=[('verdict', '=', c1('Cash holds'))]), "den": AGG('count', 'forecast')}],
    "charts": [
        CHART('Payments per month', 'column', 'month', [AGG('sum', 'payments', 'payments.amount', date='payments.date', label='Payments')]),
        CHART('Payments by method', 'bar', 'payments.method', [AGG('sum', 'payments', 'payments.amount', label='Payments')]),
        CHART('Payments by kind', 'bar', 'payments.kind', [AGG('sum', 'payments', 'payments.amount', label='Payments')]),
        CHART('Payments by channel', 'bar', 'payments.channel', [AGG('sum', 'payments', 'payments.amount', label='Payments')]),
        CHART('Cash in per month by source', 'stacked', 'month', [AGG('sum', 'payments', 'payments.amount', date='payments.date', where=[('kind', '<>', PAYOUT), ('channel', '<>', tok('channel', 'Corporate account'))], label='Renters'),
              AGG('sum', 'payments', 'payments.amount', date='payments.date', where=[('channel', '=', tok('channel', 'Corporate account'))], label='Corporate accounts'),
              AGG('sum', 'payments', 'payments.amount', date='payments.date', where=[('kind', '=', PAYOUT)], label='Marketplace payouts')]),
        CHART('Deposits held per month', 'column', 'month', [AGG('sum', 'deposits', 'deposits.amount', date='deposits.held_on', label='Deposits taken')]),
        CHART('Deposits by status', 'bar', 'deposits.status', [AGG('sum', 'deposits', 'deposits.amount', label='Deposits')]),
        CHART('Deposits kept per month', 'column', 'month', [AGG('sum', 'deposits', 'deposits.kept_amount', date='deposits.released_on', label='Kept')]),
        CHART('Deposits by class', 'bar', 'deposits.class', [AGG('sum', 'deposits', 'deposits.amount', label='Deposits')]),
        CHART('Payouts per month', 'column', 'month', [AGG('sum', 'payouts', 'payouts.received', date='payouts.month', label='Received')]),
        CHART('Payout difference per month', 'column', 'month', [AGG('sum', 'payouts', 'payouts.difference', date='payouts.month', label='Difference')]),
        CHART('Payouts by status', 'bar', 'payouts.status', [AGG('count', 'payouts', label='Payouts')]),
        CHART('Expected payouts by marketplace', 'bar', 'payouts.channel', [AGG('sum', 'payouts', 'payouts.expected_payout', label='Expected payout')]),
        CHART('Marketplace fees per month', 'column', 'month', [AGG('sum', 'payouts', 'payouts.fee', date='payouts.month', label='Fees')]),
        CHART('Fee share per month', 'line', 'month', [AGG('avg', 'feeshare', 'feeshare.fee_share', date='feeshare.month', label='Fee share')]),
        CHART('Days to payout per month', 'line', 'month', [AGG('avg', 'payouts', 'payouts.days_to_pay', date='payouts.month', label='Days to payout')]),
        CHART('Invoices issued per month', 'column', 'month', [AGG('count', 'invoices', date='invoices.issued_on', label='Invoices')]),
        CHART('Invoices by status', 'bar', 'invoices.status', [AGG('count', 'invoices', label='Invoices')]),
        CHART('Balance by ageing bucket', 'bar', 'ageing.bucket', [AGG('sum', 'ageing', 'ageing.balance', label='Balance')]),
        CHART('Balance by account', 'bar', 'corporate.account', [AGG('sum', 'corporate', 'corporate.balance', label='Balance')]),
        CHART('Collected share per month', 'line', 'month', [AGG('avg', 'invoices', 'invoices.collected_pct', date='invoices.issued_on', label='Collected share')]),
        CHART('Card fees per month', 'column', 'month', [AGG('sum', 'payments', 'payments.card_fee', date='payments.date', label='Card fees')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Deposit and hold tracker", "why": "every hold with its release date, the liability held now and the holds to release today", "where": "Deposit and Hold Tracker"},
    {"name": "Past-release holds", "why": "holds past their release date ranked by days and amount, each marked release now or keep for a claim", "where": "Past-Release Holds"},
    {"name": "Holds to release list", "why": "a ranked list of held deposits built by formula, earliest release date first", "where": "Holds to Release"},
    {"name": "Marketplace payout reconciliation", "why": "booking value, fee, expected and received payout per payout and month, with the short or late amount to chase", "where": "Payout Reconciliation Tool"},
    {"name": "Payout lateness", "why": "real days from return to payout against the days each marketplace promises", "where": "Payout Lateness"},
    {"name": "Invoice and balance chase", "why": "open balances in ageing buckets with the oldest account named, its promised date and last contact", "where": "Invoice and Balance Chase"},
    {"name": "Invoice splitter", "why": "an invoice split into rental, fees and damage so each part can be paid or questioned alone", "where": "Invoice Splitter"},
    {"name": "Four-week cash forecast", "why": "payouts, deposits to release, invoices and costs week by week, Base, Best and Worst, against your cash floor", "where": "Four-Week Cash Forecast"},
    {"name": "Daily till check", "why": "cash counted against the cash expected from the day's payments, with the difference and a 30-day record", "where": "Daily Till Check"},
    {"name": "Deposit liability against cash", "why": "the money held for renters set against your cash floor and the lowest week of the forecast", "where": "Deposit Liability Against Cash"}]
competitors = [
    {"what": "subscription rental-management software", "lacks": "charges every month and keeps deposits, payouts and balances in screens you cannot test or change"},
    {"what": "generic booking calendar template", "lacks": "lists bookings but has no deposit release dates, payout reconciliation or ageing of unpaid invoices"},
    {"what": "single-sheet vehicle expense log", "lacks": "records costs only, with nothing about holds, marketplace fees, short-paid payouts or cash"},
    {"what": "budget-model template", "lacks": "shows a plan but not the daily till, the card fees or a cash forecast from your own payments"},
    {"what": "paper receipt books", "lacks": "record a payment but never show the liability held, late payouts or overdue accounts"}]
guide = [
    'Open Start and type your business name, the cash at the bank, your cash floor, the days to release a deposit and your credit limit in the yellow cells.',
    'Record each deposit or card hold in Deposits with its release due date; Holds to Release then ranks the held ones by date.',
    'Record every payment in Payments with its date, booking, channel, kind and method; Cash In by Day and Payment Methods fill in by themselves.',
    'Record each marketplace payout in Payouts with the booking value, fee, expected payout and date; the difference and days late fill in.',
    'Use Payout Reconciliation each month to see every gap, and the Marketplace Payout Reconciliation tool to name what to chase.',
    'Record each corporate invoice in Invoices; the balance, days overdue and age band fill in, and Ageing Buckets adds them up.',
    'Write each promise to pay in Promises to Pay and follow the next step it shows.',
    'Count the cash each day in Daily Till Log; the cash expected comes from the cash payments of the day.',
    'Check Deposit Liability each month end and the Four-Week Cash Forecast each week against your cash floor.',
    'Use Kept Deposits to check that every amount kept is backed by fees or a claim amount.',
    f'Use the {len(tools)} tools for the weekly decisions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Payments Dashboard and the charts every week. A one-car host uses the same sheets with one vehicle and one channel.']
listing = {"title": "Car Rental Deposits, Payments and Payouts Excel Template: Deposit Tracker, Payout Reconciliation, Invoice Chase, Cash Forecast",
    "headline": "See every hold, payout and unpaid invoice of your car rental in one place",
    "tags": ["car rental", "rental deposits", "payout tracker", "excel template", "invoice tracker", "cash forecast", "car sharing host", "deposit tracker", "payment log", "fleet owner", "till check", "rental business", "accounts receivable"],
    "description": ("Run the money side of a small car and van rental in one Excel workbook. Built for an owner-operator, a manager who also does billing and a part-time bookkeeper, and useful to a one-car host. "
        "Deposits holds every deposit or card hold with its release date, the amount kept or refunded and the liability held now. Payments records every payment by method, kind and channel, and Payouts compares each marketplace payout with the expected amount.\n\n"
        "Invoices tracks corporate account invoices with balance, days overdue and an ageing band, Promises to Pay records what accounts promised, and Invoice Lines splits an invoice into rental, fees and damage. "
        "Deposit Liability, Payout Reconciliation, Fee Share by Month, Cash In by Day, Daily Till Log, Cash Forecast and Card Hold Calendar are worked out for you from the ledgers.\n\n"
        f"{len(tools)} tools answer the weekly questions: which holds to release, which payouts are short or late, which account to chase first, whether cash holds above your floor and whether the till balances. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to renters, accounts, a marketplace, the manager, the bookkeeper and the accountant.\n\n"
        "This is part four of the Car Rental Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Renters appear by first name and initial, a booking reference and dates only. "
        "It helps you keep track of your money and does not promise results. Check your local rules for deposits, records and tax; confirm tax questions with your adviser."),
    "features": ["Deposit and card hold tracker", "Holds ranked by release date", "Marketplace payout reconciliation", "Invoice ageing and promises to pay", "Four-week cash forecast", "Daily till check",
                 f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p4', slug='car-rental-payments', profession='Car Rental Business', name='Deposits, Payments and Payouts',
         tagline='See every hold, payout and unpaid invoice of your car rental in one place', price_usd=29,
         colors={"primary": "#1D3557", "accent": "#E63946"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 4, "of": 8, "focus": "Deposits, payments and payouts"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cr4.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
