"""Childcare center suite - part 5: Payments, Balances and Cash."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc5_lists import *
from cc5_lists import _VN
from cc5_tables import settings, tables, MS, R, UNPAID, PART, SHORT, EXPECTED, KEPT, BROKEN, PENDING, HELD, UPC, PAYROLL, CASH_NOW
from cc5_tools import tools, DSO

SUITE = 'fx-20261115-childcare-center'
NOTE = "Sample wording: adapt it to your own center and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
SIGN = 'Willow Lane Early Learning'
def LOOKF(t_pick, pick_col, t, col, key_col, key_pick_col=None):
    """value of t.col for the family of the picked row"""
    return 'IFERROR(INDEX({range:%s},MATCH(INDEX({range:%s.family},MATCH({pick},{range:%s},0)),{range:%s.family},0)),0)' % ((t + '.' + col), t_pick, t_pick + '.' + pick_col, t)

forms = [
    FORM('payment_received', 'Payment Received Sheet', 'Payment received: family, invoice, amount', 'payments.payment_id', F(
        ('Date', 'payments.date'), ('Family', 'payments.family'), ('Invoice ID', 'payments.invoice_id'), ('Amount', 'payments.amount'), ('Method', 'payments.method'), ('Kind', 'payments.kind'),
        ('Month', 'payments.month'), ('Card processing cost', 'payments.card_cost'), ('Family phone', 'payments.phone')) + [
        FF('Open balance of this family now', 'IFERROR(INDEX({range:families.open_balance},MATCH(INDEX({range:payments.family},MATCH({pick},{range:payments.payment_id},0)),{range:families.family},0)),0)', 'money'),
        FF('Payments from this family in the table', 'COUNTIFS({range:payments.family},INDEX({range:payments.family},MATCH({pick},{range:payments.payment_id},0)))', 'int')]),
    FORM('promise_sheet', 'Payment Promise Sheet', 'Payment promise: family, amount, date and method', 'promises.promise_id', F(
        ('Promised on', 'promises.promised_on'), ('Family', 'promises.family'), ('Invoice ID', 'promises.invoice_id'), ('Promised amount', 'promises.promised_amount'), ('Method', 'promises.method'),
        ('Outcome', 'promises.outcome'), ('Days to the promise', 'promises.due_in'), ('Promise check', 'promises.promise_flag'), ('Billing phone', 'promises.ad_phone')) + [
        FF('Promises of this family in the table', 'COUNTIFS({range:promises.family},INDEX({range:promises.family},MATCH({pick},{range:promises.promise_id},0)))', 'int'),
        FF('Balance of this family now', 'IFERROR(INDEX({range:aging.balance},MATCH(INDEX({range:promises.family},MATCH({pick},{range:promises.promise_id},0)),{range:aging.family},0)),0)', 'money')]),
    FORM('plan_sheet', 'Payment Plan Agreement Sheet', 'Payment plan: instalment, due date and status', 'instalments.inst_id', F(
        ('Plan', 'instalments.plan'), ('Family', 'instalments.family'), ('Instalment number', 'instalments.number'), ('First due', 'instalments.first_due'), ('Due date', 'instalments.due_date'),
        ('Instalments in the plan', 'instalments.plan_instalments'), ('Instalment', 'instalments.amount'), ('Paid', 'instalments.paid_amount'), ('Status', 'instalments.status'), ('Family phone', 'instalments.phone')) + [
        FF('Plan balance', 'IFERROR(INDEX({range:plans.balance},MATCH(INDEX({range:instalments.plan},MATCH({pick},{range:instalments.inst_id},0)),{range:plans.plan_id},0)),0)', 'money')]),
    FORM('reminder_log', 'Reminder Log Sheet', 'Reminder log: invoice, step and next date', 'reminder.rs_id', F(
        ('Rank', 'reminder.rank'), ('Invoice ID', 'reminder.invoice_id'), ('Family', 'reminder.family'), ('Balance', 'reminder.balance'), ('Due date', 'reminder.due_date'), ('Days overdue', 'reminder.days_overdue'),
        ('Promises broken', 'reminder.broken'), ('Step', 'reminder.step'), ('Next step on', 'reminder.next_date'), ('Pause care after', 'reminder.pause_on'), ('Please pay by', 'reminder.pay_by'),
        ('Who acts', 'reminder.owner'), ('Family phone', 'reminder.phone'))),
    FORM('gov_check_sheet', 'Government Payment Check Sheet', 'Government payment check for one month', 'gov_month.gm_id', F(
        ('Month', 'gov_month.month'), ('Expected', 'gov_month.expected'), ('Expected, already resolved', 'gov_month.matched'), ('Received', 'gov_month.received'), ('Gap', 'gov_month.gap'),
        ('Items short', 'gov_month.items_short'), ('Items waiting for the payer', 'gov_month.items_waiting'), ('Share of resolved items received', 'gov_month.match_share'), ('Month check', 'gov_month.flag'))),
    FORM('short_query_sheet', 'Short Payment Query Sheet', 'Short payment query: expected and received', 'gov.gov_id', F(
        ('Month', 'gov.month'), ('Family', 'gov.family'), ('Expected', 'gov.expected'), ('Received', 'gov.received'), ('Gap', 'gov.gap'), ('Paid on', 'gov.paid_on'), ('Days since', 'gov.days_since'),
        ('Family share', 'gov.family_share'), ('Next step', 'gov.step'), ('Billing phone', 'gov.ad_phone'), ('Family phone', 'gov.phone'))),
    FORM('writeoff_sheet', 'Write-off Approval Sheet', 'Write-off approval for one invoice', 'invoices.invoice_id', F(
        ('Family', 'invoices.family'), ('Issued on', 'invoices.issued_on'), ('Due date', 'invoices.due_date'), ('Parent due', 'invoices.parent_due'), ('Status', 'invoices.status'),
        ('Open balance', 'invoices.open_balance'), ('Days overdue', 'invoices.days_overdue'), ('Aging band', 'invoices.band'), ('Family phone', 'invoices.phone')) + [
        FF('Open balance of the family in all', 'IFERROR(INDEX({range:families.open_balance},MATCH(INDEX({range:invoices.family},MATCH({pick},{range:invoices.invoice_id},0)),{range:families.family},0)),0)', 'money')]),
    FORM('autopay_signup', 'Autopay Sign-up Sheet', 'Autopay sign-up for a family on manual payment', 'families.family_id', F(
        ('Family', 'families.family'), ('Guardian', 'families.guardian'), ('Phone', 'families.phone'), ('Billing cycle', 'families.cycle'), ('Pay method now', 'families.pay_method'), ('How they usually pay', 'families.habit'),
        ('Late prone', 'families.late_prone'), ('Open balance', 'families.open_balance'), ('Days late on average', 'families.avg_days_late'), ('Card fee share', 'families.card_fee'))),
    FORM('autopay_change', 'Autopay Change Sheet', 'Autopay change: method, paid and card cost', 'families.family_id', F(
        ('Family', 'families.family'), ('E-mail', 'families.email'), ('Pay method now', 'families.pay_method'), ('Autopay', 'families.autopay'), ('Paid this year', 'families.paid_year'), ('Open balance', 'families.open_balance')) + [
        FF('Card processing cost this year', 'SUMIFS({range:payments.card_cost},{range:payments.family},INDEX({range:families.family},MATCH({pick},{range:families.family_id},0)),{range:payments.date},">="&DATE(YEAR({today}),1,1))', 'money'),
        FF('Payments from the family, 12 months', 'COUNTIFS({range:payments.family},INDEX({range:families.family},MATCH({pick},{range:families.family_id},0)),{range:payments.date},">"&({today}-365))', 'int')]),
    FORM('bill_sheet', 'Bill Payment Sheet', 'Bill payment: supplier, amount and due date', 'bills.bill_id', F(
        ('Due date', 'bills.due_date'), ('Category', 'bills.category'), ('Paid to', 'bills.paid_to'), ('Amount', 'bills.amount'), ('Status', 'bills.status'), ('Days to the due date', 'bills.days_to_due'),
        ('Bill check', 'bills.due_flag'), ('Supplier phone', 'bills.phone'))),
    FORM('cash_count_sheet', 'Cash Count Sheet', 'Cash count for one month', 'cash.cash_id', F(
        ('Month', 'cash.month'), ('Opening cash', 'cash.opening'), ('Parent payments', 'cash.parent_payments'), ('Government payments', 'cash.government_payments'), ('Cash in', 'cash.cash_in'), ('Cash out', 'cash.cash_out'),
        ('Closing cash', 'cash.closing'), ('Cash payments counted', 'cash.cash_taken'), ('Above the floor', 'cash.above_floor'), ('Floor check', 'cash.floor_flag'))),
    FORM('weekly_cash_review', 'Weekly Cash Review Sheet', 'Weekly cash review for one forecast week', 'forecast.fc_id', F(
        ('Week number', 'forecast.week_no'), ('Week (Monday)', 'forecast.week_start'), ('Opening cash', 'forecast.opening'), ('Tuition in', 'forecast.tuition_in'), ('Government in', 'forecast.government_in'),
        ('Payroll out', 'forecast.payroll_out'), ('Rent and bills out', 'forecast.rent_bills_out'), ('Routine costs out', 'forecast.other_out'), ('Tax and extra draw out', 'forecast.draw_tax_out'), ('Net', 'forecast.net'),
        ('Closing cash', 'forecast.closing'), ('Floor check', 'forecast.floor_flag'))),
]
assert len(forms) == 12

documents = [
    DOC('reminder_letter', 'Payment Reminder Letter', 'Payment reminder letter (first, second or final step)', 'reminder.rs_id', [
        'Letter of {set:company}, dated {today}. To the {col:reminder.family}.',
        'Invoice {col:reminder.invoice_id} was due on {col:reminder.due_date} and {col:reminder.balance} is still open, {col:reminder.days_overdue} days overdue. Our step: {col:reminder.step}.',
        'Please pay by {col:reminder.pay_by}, or call us today if you want to agree a plan. If nothing is agreed we may pause care after {col:reminder.pause_on}.'], ['Billing contact', 'Parent or guardian'], NOTE),
    DOC('balance_statement', 'Balance Statement for a Family', 'Balance statement for a family, with the aging bands', 'aging.ageing_id', [
        'Statement of {set:company}, dated {today}. Family: {col:aging.family}.',
        'Balance {col:aging.balance}. Days 0-30: {col:aging.d0_30}. Days 31-60: {col:aging.d31_60}. Days 61-90: {col:aging.d61_90}. Days 90+: {col:aging.d90_plus}. Open invoices: {col:aging.open_invoices}; the oldest is {col:aging.oldest_days} days overdue.',
        'Next step: {col:aging.step}. Please tell us if anything on this statement looks wrong.'], ['Billing contact', 'Parent or guardian'], NOTE),
    DOC('plan_agreement', 'Payment Plan Agreement', 'Payment plan agreement, one instalment line', 'instalments.inst_id', [
        'Payment plan of {set:company}, dated {today}. Family: {col:instalments.family}, plan {col:instalments.plan}.',
        'The balance is paid in {col:instalments.plan_instalments} instalments. Instalment {col:instalments.number} is {col:instalments.amount} and is due on {col:instalments.due_date}. Status: {col:instalments.status}.',
        'If an instalment is missed the plan ends and the full balance falls due. Both sides sign below to agree.'], ['Billing contact', 'Parent or guardian'], NOTE),
    DOC('receipt', 'Receipt for a Payment', 'Receipt for a payment', 'payments.payment_id', [
        'Receipt of {set:company}, dated {today}. Received from the {col:payments.family}.',
        'Payment {col:payments.payment_id}, received on {col:payments.date}: {col:payments.amount}, by {col:payments.method}, kind {col:payments.kind}. Invoice: {col:payments.invoice_id}.',
        'Thank you. Please keep this receipt for your records.'], ['Billing contact'], NOTE),
    DOC('autopay_agreement', 'Autopay Agreement', 'Autopay agreement for a family', 'families.family_id', [
        'Autopay agreement of {set:company}, dated {today}. Family: {col:families.family}, guardian {col:families.guardian}.',
        'The family agrees that invoices are paid automatically on the due date by {col:families.pay_method}. A card payment carries a fee share of {col:families.card_fee}. The family may stop autopay by telling us in writing before the next invoice.',
        'If a payment fails we tell the family the same day and ask for new details.'], ['Billing contact', 'Parent or guardian'], NOTE),
    DOC('gov_query', 'Government Short-pay Query', 'Short-pay query to the payer', 'gov.gov_id', [
        'Query of {set:company}, dated {today}. Family: {col:gov.family}, month {col:gov.month}.',
        'We expected {col:gov.expected} and received {col:gov.received}, a gap of {col:gov.gap}, {col:gov.days_since} days ago. Our next step: {col:gov.step}.',
        'Please tell us why the payment was lower and when the rest will arrive.'], ['Billing contact', 'Owner-director'], NOTE),
    DOC('pause_notice', 'Overdue Notice Before Pause', 'Overdue notice before care is paused', 'overdue.of_id', [
        'Notice of {set:company}, dated {today}. To the {col:overdue.family}.',
        'Your balance is {col:overdue.balance} across {col:overdue.open_invoices} invoices, the oldest {col:overdue.oldest_days} days overdue. Promises broken: {col:overdue.promises_broken}. Next step: {col:overdue.step}.',
        'Please call {col:overdue.owner} to agree a payment or a plan. Check your contract terms for what happens if the balance stays open.'], ['Owner-director', 'Parent or guardian'], NOTE),
    DOC('writeoff_note', 'Write-off Note Accountant', 'Write-off note for the accountant', 'invoices.invoice_id', [
        'Note of {set:company}, dated {today}. Invoice {col:invoices.invoice_id}, family {col:invoices.family}.',
        'Parent due {col:invoices.parent_due}, paid {col:invoices.paid_amount}, open balance {col:invoices.open_balance}, written off {col:invoices.written_off}. Due date {col:invoices.due_date}; days overdue {col:invoices.days_overdue}.',
        'Please record the write-off in your books. Check your local rules for how it is treated.'], ['Owner-director', 'Accountant'], NOTE),
    DOC('weekly_cash_summary', 'Weekly Cash Summary', 'Cash summary for the owner-director, one month', 'cash.cash_id', [
        'Cash summary of {set:company}, dated {today}. Month of {col:cash.month}.',
        'Opening {col:cash.opening}. In: parents {col:cash.parent_payments}, government {col:cash.government_payments}. Out in all {col:cash.cash_out}. Closing {col:cash.closing}, which is {col:cash.above_floor} above your floor. Check: {col:cash.floor_flag}.',
        'Cash payments counted in the month: {col:cash.cash_taken}.'], ['Billing contact', 'Owner-director'], NOTE),
    DOC('forecast_report', '13 Week Cash Forecast Report', '13-week cash forecast report, one week', 'forecast.fc_id', [
        'Forecast of {set:company}, dated {today}. Week {col:forecast.week_no}, from {col:forecast.week_start}.',
        'Opening cash {col:forecast.opening}. In: tuition {col:forecast.tuition_in}, government {col:forecast.government_in}. Out: payroll {col:forecast.payroll_out}, rent and bills {col:forecast.rent_bills_out}, routine costs {col:forecast.other_out}, tax and extra draw {col:forecast.draw_tax_out}.',
        'Closing cash {col:forecast.closing} against your floor of {col:forecast.floor}. Check: {col:forecast.floor_flag}. This is a forecast from your own history, not a promise.'], ['Billing contact', 'Owner-director'], NOTE),
    DOC('collections_report', 'Monthly Collections Report', 'Monthly collections report by aging band', 'aging_month.row_id', [
        'Collections report of {set:company}, dated {today}. Month of {col:aging_month.month}, band {col:aging_month.band}.',
        'The band holds {col:aging_month.amount}, which is {col:aging_month.share} of the month total of {col:aging_month.month_total}.',
        'Read the bands together: a growing 61-90 or 90+ band means older balances need a call or a plan.'], ['Billing contact', 'Owner-director'], NOTE),
    DOC('bank_card_summary', 'Bank and Card Payments Summary', 'Bank and card payments summary for the accountant, one month', 'collect.col_id', [
        'Payments summary of {set:company}, dated {today}. Month of {col:collect.month}.',
        'Paid in the month {col:collect.total_paid}: autopay card {col:collect.card_paid}, autopay bank {col:collect.bank_auto}, bank transfer {col:collect.transfer_paid}, cash {col:collect.cash_paid}. Card processing cost {col:collect.card_cost}.',
        'Due {col:collect.due}, collected {col:collect.collected}, collection rate {col:collect.rate}. Late amount on autopay {col:collect.late_autopay}, on manual payers {col:collect.late_manual}.'], ['Billing contact', 'Accountant'], NOTE),
]
assert len(documents) == 12

checklists = [
    CHK('record_payments', 'Recording Payments Steps', 'payments', 'payments.date', [('Match the payment to the invoice', 0), ('Type the amount, method and date', 0), ('Check the invoice shows paid or part paid', 0), ('Send a thank-you to the family', 1), ('Count cash and card receipts at the end of the day', 1)]),
    CHK('weekly_aging', 'Weekly Aging Review Steps', 'invoices', 'invoices.issued_on', [('Open Aging by Family', 0), ('List families over 30 days', 0), ('Check promises due this week', 1), ('Pick the next step for each family', 1), ('Tell the owner-director about balances over your days limit', 2)]),
    CHK('send_reminders', 'Sending Reminders Steps', 'invoices', 'invoices.due_date', [('Open the Reminder Schedule', 1), ('Send friendly reminders for day 1', 1), ('Send second reminders', 3), ('Log each message and the answer', 3), ('Write any promise to pay', 4)]),
    CHK('call_late_family', 'Calling a Late Family Steps', 'promises', 'promises.promised_on', [('Check the balance and invoice numbers', -1), ('Be kind and clear about the amount', 0), ('Ask for a date to pay', 0), ('Offer a payment plan if needed', 0), ('Write the promise and the date', 0), ('Check the promise on the day', 1)]),
    CHK('plan_setup', 'Setting Up a Payment Plan Steps', 'instalments', 'instalments.first_due', [('Check the balance and the family situation', -7), ('Ask for a first payment', -5), ('Agree the number and the dates', -4), ('Print and sign the agreement', -3), ('Enter the plan and the instalments', -3), ('Check each instalment on its date', 0)]),
    CHK('autopay_setup', 'Autopay Set-up Steps', 'families', 'families.first_start', [('Explain autopay and the card fee', 0), ('Print the autopay sign-up sheet', 0), ('Collect the payment details safely', 3), ('Run a first payment', 14), ('Tell the family the first autopay date', 14)]),
    CHK('gov_check', 'Government Payment Check Steps', 'gov', 'gov.due_on', [('List the payments expected this month', -3), ('Match each payment to a family', 0), ('Mark any short payment', 1), ('Write the gap and the date', 1), ('Tell the owner-director about gaps', 2)]),
    CHK('short_followup', 'Short Payment Follow-up Steps', 'gov', 'gov.due_on', [('Ask the payer why it was short', 1), ('Write the answer and the date', 2), ('Wait for the days you set', 14), ('Bill the family share if the payer does not pay', 30), ('Tell the family in writing', 31)]),
    CHK('weekly_cash', 'Weekly Cash Review Steps', 'cash', 'cash.month', [('Update the opening cash', 0), ('Check the next 13 weeks', 1), ('Find the lowest week', 1), ('Chase balances or delay a bill if needed', 2), ('Tell the owner-director', 2)]),
    CHK('monthly_bills', 'Paying the Monthly Bills Steps', 'bills', 'bills.due_date', [('Open the Bill Calendar', -7), ('Check cash against the bills', -5), ('Pay the bills in due-date order', -2), ('Mark each bill paid', 0), ('Tell the supplier payment is on its way', 0)]),
    CHK('month_end_close', 'Month-End Close Steps', 'aging_month', 'aging_month.month', [('Enter the month-end amount of each band', 28), ('Check the collection rate', 29), ('Send the last reminders', 30), ('Tell the accountant about write-offs', 31), ('Save the month report', 32)]),
    CHK('quarter_tax', 'Quarter Tax Check Steps', 'tax', 'tax.due_date', [('Add up revenue and costs for the quarter', -21), ('Work out your share with your adviser', -18), ('Move the amount to your set-aside account', -14), ('Write the date paid', -14), ('File the check', -7)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text + ' ' + SIGN)
messages = [
    M('f_reminder', 'Family: a friendly reminder', 'invoices', 'invoices.phone', 'Hello {family}, a friendly reminder: invoice {invoice_id} of {parent_due} was due on {due_date}. Thank you.'),
    M('f_balance', 'Family: your balance and its age', 'aging', 'aging.phone', 'Hello {family}, your balance is {balance} and the oldest invoice is {oldest_days} days overdue. Please pay or call us.'),
    M('f_second', 'Family: second reminder', 'reminder', 'reminder.phone', 'Hello {family}, second reminder for invoice {invoice_id}: {balance} is {days_overdue} days overdue. Please pay by {pay_by}.'),
    M('f_final', 'Family: final reminder', 'reminder', 'reminder.phone', 'Hello {family}, final reminder for invoice {invoice_id}: please pay {balance} today or call us to agree a plan.'),
    M('f_thanks', 'Family: thank you for the payment', 'payments', 'payments.phone', 'Thank you {family}, we received {amount} on {date}.'),
    M('f_part', 'Family: part of the payment received', 'invoices', 'invoices.phone', 'Hello {family}, we received part of the payment for invoice {invoice_id}; {open_balance} remains.'),
    M('f_promise', 'Family: please confirm your promise', 'promises', 'promises.phone', 'Hello {family}, you promised {promised_amount} on {promised_on}. Please confirm it.'),
    M('f_missed', 'Family: a missed promise', 'promises', 'promises.phone', 'Hello {family}, the payment of {promised_amount} promised for {promised_on} did not arrive. Can we agree a plan?'),
    M('f_plan', 'Family: your payment plan', 'instalments', 'instalments.phone', 'Hello {family}, your payment plan is {plan_instalments} payments of {amount} from {first_due}.'),
    M('f_next', 'Family: your next instalment', 'instalments', 'instalments.phone', 'Hello {family}, your next instalment of {amount} is due on {due_date}.'),
    M('f_plandone', 'Family: your plan is complete', 'instalments', 'instalments.phone', 'Hello {family}, your payment plan {plan} is complete after {plan_instalments} payments. Thank you.'),
    M('f_autopay', 'Family: would you like autopay', 'families', 'families.phone', 'Hello {family}, would you like autopay? It saves late reminders. Your balance now is {open_balance}.'),
    M('f_autofail', 'Family: your autopay payment failed', 'invoices', 'invoices.phone', 'Hello {family}, the autopay payment for invoice {invoice_id} ({parent_due}) failed. Please update your details.'),
    M('f_cardfee', 'Family: a card fee applies', 'families', 'families.phone', 'Hello {family}, a small card fee applies to card payments. You paid {paid_year} this year; a bank transfer has no fee.'),
    M('f_cleared', 'Family: your balance is cleared', 'families', 'families.phone', 'Hello {family}, your balance is cleared. Thank you. You have paid {paid_year} this year.'),
    M('f_govshort', 'Family: the government payment was short', 'gov', 'gov.phone', 'Hello {family}, the government childcare payment for {month} was short by {gap}. We are asking the payer and will tell you if the family share is due.'),
    M('f_govshare', 'Family: your share of the tuition', 'gov', 'gov.phone', 'Hello {family}, beside the government payment of {expected}, your share this month is {family_share}.'),
    M('f_depref', 'Family: your deposit refund', 'deposits', 'deposits.phone', 'Hello {family}, your deposit of {amount} is refunded on {refund_on}.'),
    M('f_statement', 'Family: your statement is ready', 'families', 'families.phone', 'Hello {family}, your statement of payments is ready. You have paid {paid_year} this year.'),
    M('f_pause', 'Family: care may be paused', 'reminder', 'reminder.phone', 'Hello {family}, we may pause care from {pause_on} if {balance} stays open. Please call us.'),
    M('f_continue', 'Family: care continues with the plan', 'instalments', 'instalments.phone', 'Hello {family}, care continues, thank you for the plan of {plan_instalments} instalments.'),
    M('ad_over60', 'Assistant director: long balances', 'aging', 'aging.ad_phone', 'Hello Tobias, {family} owes {balance}; {over_limit} is over your days limit. Please call today.'),
    M('ad_promises', 'Assistant director: promises due', 'promises', 'promises.ad_phone', 'Hello Tobias, {family} promised {promised_amount} on {promised_on}. Please check it that day.'),
    M('ad_reminders', 'Assistant director: reminders to send', 'reminder', 'reminder.ad_phone', 'Hello Tobias, please send the step for {family}, invoice {invoice_id}, balance {balance}, by {next_date}.'),
    M('ad_gov', 'Assistant director: government chase', 'gov', 'gov.ad_phone', 'Hello Tobias, please chase the government payment of {family} for {month}: expected {expected}, received {received}.'),
    M('o_lowest', 'Owner: the cash of a forecast week', 'forecast', 'forecast.owner_phone', 'Hello Marisol, cash at the end of the week of {week_start} is {closing}, against your floor of {floor}.'),
    M('o_below', 'Owner: cash against the floor', 'cash', 'cash.owner_phone', 'Hello Marisol, closing cash for {month} is {closing}; the gap to the floor is {above_floor}.'),
    M('o_long', 'Owner: a long balance', 'overdue', 'overdue.owner_phone', 'Hello Marisol, {family} has {over_60} over your days limit and {balance} open in all.'),
    M('o_autopay', 'Owner: autopay in the month', 'collect', 'collect.owner_phone', 'Hello Marisol, autopay paid {autopay_paid} of {total_paid} in {month}; card processing cost {card_cost}.'),
    M('o_tax', 'Owner: tax set aside', 'tax', 'tax.owner_phone', 'Hello Marisol, for {month} your share requires {required} and {set_aside} is set aside. Confirm with your adviser.'),
    M('acc_cash', 'Accountant: payments and cash by month', 'cash', 'cash.acc_phone', 'Hello Eleni, for {month}: money in {cash_in}, money out {cash_out}, closing cash {closing}.'),
    M('acc_writeoff', 'Accountant: a balance written off', 'invoices', 'invoices.acc_phone', 'Hello Eleni, invoice {invoice_id} of {family}: {written_off} is written off.'),
    M('sup_pay', 'Food supplier: payment is on its way', 'bills', 'bills.phone', 'Hello {paid_to}, the payment of {amount} for the bill due on {due_date} is on its way.'),
    M('maint_pay', 'Maintenance: payment is on its way', 'expenses', 'expenses.phone', 'Hello Dae-ho, the payment of {amount} for {description} is on its way.'),
]
assert len(messages) == 34, len(messages)

def CNT(*w): return 'COUNTIFS(%s)' % ','.join(w)
def SM(t, c): return 'SUM(%s)' % R(t, c)
def SI(t, c, *cr): return 'SUMIFS(%s,%s)' % (R(t, c), ','.join('%s,%s' % (R(t, k), v) for k, v in cr))
CM = lambda c: 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('collect', c), MS, R('collect', 'month'))
kpis = [
    KPI('Payments received this month', CNT(R('payments', 'date') + ',">="&' + MS), 'int'),
    KPI('Parent payments this month', SI('payments', 'amount', ('date', '">="&' + MS)), 'money'),
    KPI('Government payments this month', SI('cash', 'government_payments', ('month', MS)), 'money'),
    KPI('Collection rate this month', CM('rate'), 'pct'),
    KPI('Collection rate, last 12 months', 'IFERROR(%s/%s,0)' % (SM('collect', 'collected'), SM('collect', 'due')), 'pct'),
    KPI('Open balance now', SM('aging', 'balance'), 'money'),
    KPI('Balance 0-30 days', SM('aging', 'd0_30'), 'money'), KPI('Balance 31-60 days', SM('aging', 'd31_60'), 'money'), KPI('Balance 61-90 days', SM('aging', 'd61_90'), 'money'), KPI('Balance over 90 days', SM('aging', 'd90_plus'), 'money'),
    KPI('Families with an open balance', CNT(R('aging', 'balance') + ',">0"'), 'int'),
    KPI('Families over 60 days', CNT(R('aging', 'over_limit') + ',">0"'), 'int'),
    KPI('Days outstanding, last 90 days', DSO, 'num'),
    KPI('Oldest balance in days', 'MAX(%s)' % R('aging', 'oldest_days'), 'int'),
    KPI('Promises due this week', CNT(R('promises', 'outcome') + ',' + PENDING, R('promises', 'promised_on') + ',">="&{today}', R('promises', 'promised_on') + ',"<="&({today}+7)'), 'int'),
    KPI('Promises kept, last 90 days', 'IFERROR(%s/%s,0)' % (CNT(R('promises', 'outcome') + ',' + KEPT, R('promises', 'promised_on') + ',">"&({today}-90)', R('promises', 'promised_on') + ',"<="&{today}'),
                                                              CNT(R('promises', 'settled') + ',1', R('promises', 'promised_on') + ',">"&({today}-90)', R('promises', 'promised_on') + ',"<="&{today}')), 'pct'),
    KPI('Payment plans open', SM('instalments', 'closes_plan'), 'int'),
    KPI('Plan instalments due next 30 days', SI('instalments', 'amount', ('due_date', '">="&{today}'), ('due_date', '"<="&({today}+30)'), ('paid_amount', '0')), 'money'),
    KPI('Autopay share of tuition, last 3 months', 'IFERROR(%s/%s,0)' % (SI('collect', 'autopay_paid', ('month', '">="&EDATE(%s,-2)' % MS)), SI('collect', 'total_paid', ('month', '">="&EDATE(%s,-2)' % MS))), 'pct'),
    KPI('Late balance on manual payers', SI('invoices', 'open_balance', ('autopay', '0'), ('days_overdue', '">0"')), 'money'),
    KPI('Card processing cost this month', SI('payments', 'card_cost', ('date', '">="&' + MS)), 'money'),
    KPI('Government payments expected this month', SI('gov', 'expected', ('due_on', '">="&' + MS), ('due_on', '"<"&EDATE(%s,1)' % MS)), 'money'),
    KPI('Government payments short, last 90 days', CNT(R('gov', 'status') + ',' + SHORT, R('gov', 'paid_on') + ',">"&({today}-90)'), 'int'),
    KPI('Family share still owed', SI('gov', 'gap', ('status', SHORT)), 'money'),
    KPI('Deposits held now', SM('deposits', 'held'), 'money'),
    KPI('Cash balance now', CASH_NOW, 'money'),
    KPI('Lowest cash week in the next 13 weeks', 'MIN(%s)' % R('forecast', 'closing'), 'money'),
    KPI('Bills due next 30 days', SI('bills', 'amount', ('status', UPC), ('due_date', '"<="&({today}+30)')), 'money'),
    KPI('Payroll next month', SI('bills', 'amount', ('category', PAYROLL), ('status', UPC), ('due_date', '"<="&({today}+35)')), 'money'),
    KPI('Tax set aside this year', SI('tax', 'set_aside', ('month', '">="&DATE(YEAR({today}),1,1)')), 'money'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Payments and Cash Dashboard", "kpis": kpis,
    "monthly": {"title": "Parent payments and government payments", "date": "cash.month", "series": [
        {"label": "Parent payments", "sum": "cash.parent_payments", "date": "cash.month"}, {"label": "Government payments", "sum": "cash.government_payments", "date": "cash.month"}]},
    "breakdowns": [{"title": "Payments by method", "by": "payments.method", "value": "payments.amount", "agg": "sum"}, {"title": "Invoices by status", "by": "invoices.status", "value": "invoices.open_balance", "agg": "count"},
                   {"title": "Open balance by billing cycle", "by": "invoices.cycle", "value": "invoices.open_balance", "agg": "sum"}, {"title": "Bills by category", "by": "bills.category", "value": "bills.amount", "agg": "sum"}]}
def WH(*c): return [(a, b, d) for a, b, d in c]
insights = {"filters": [{"label": "Billing cycle", "list": "cycle"}],
    "gauges": [{"title": "Collection rate", "num": AGG('sum', 'collect', 'collect.collected'), "den": AGG('sum', 'collect', 'collect.due')},
               {"title": "Balance not over your days limit", "num": AGG('sum', 'aging', 'aging.under_limit'), "den": AGG('sum', 'aging', 'aging.balance')},
               {"title": "Promises kept", "num": AGG('sum', 'promises', 'promises.kept_n'), "den": AGG('sum', 'promises', 'promises.settled')},
               {"title": "Autopay share of tuition", "num": AGG('sum', 'collect', 'collect.autopay_paid'), "den": AGG('sum', 'collect', 'collect.total_paid')},
               {"title": "Government payments received as expected", "num": AGG('sum', 'gov_month', 'gov_month.received'), "den": AGG('sum', 'gov_month', 'gov_month.matched')},
               {"title": "Forecast weeks above the cash floor", "num": AGG('count', 'forecast', where=[('below_floor', '=', 0)]), "den": AGG('count', 'forecast')}],
    "charts": [
        CHART('Payments per month', 'bar', 'month', [AGG('sum', 'payments', 'payments.amount', date='payments.date', label='Payments')]),
        CHART('Payments by method', 'bar', 'payments.method', [AGG('sum', 'payments', 'payments.amount', label='Payments')]),
        CHART('Payments by kind', 'bar', 'payments.kind', [AGG('count', 'payments', label='Payments')]),
        CHART('Parent against government payments per month', 'bar', 'month', [AGG('sum', 'cash', 'cash.parent_payments', date='cash.month', label='Parent payments'), AGG('sum', 'cash', 'cash.government_payments', date='cash.month', label='Government payments')]),
        CHART('Collection rate per month', 'column', 'month', [AGG('avg', 'collect', 'collect.rate', date='collect.month', label='Collection rate')]),
        CHART('Balance by aging band, latest month', 'bar', 'aging_month.band', [AGG('sum', 'aging_month', 'aging_month.amount', where=[('is_latest', '=', 1)], label='Balance')]),
        CHART('Aging by month', 'bar', 'month', [AGG('sum', 'aging_month', 'aging_month.amount', date='aging_month.month', where=[('band', '=', tok('band', b))], label='Days ' + b) for b in AGE_BANDS]),
        CHART('Open balance by billing cycle', 'bar', 'invoices.cycle', [AGG('sum', 'invoices', 'invoices.open_balance', label='Open balance')]),
        CHART('Invoices by status', 'bar', 'invoices.status', [AGG('count', 'invoices', label='Invoices')]),
        CHART('Promises by outcome', 'bar', 'promises.outcome', [AGG('count', 'promises', label='Promises')]),
        CHART('Promises by method', 'bar', 'promises.method', [AGG('count', 'promises', label='Promises')]),
        CHART('Government payments by status', 'bar', 'gov.status', [AGG('count', 'gov', label='Payments')]),
        CHART('Government expected against received per month', 'column', 'month', [AGG('sum', 'gov', 'gov.expected', date='gov.month', label='Expected'), AGG('sum', 'gov', 'gov.received', date='gov.month', label='Received')]),
        CHART('Government gap per month', 'bar', 'month', [AGG('sum', 'gov_month', 'gov_month.gap', date='gov_month.month', label='Gap')]),
        CHART('Deposits by status', 'bar', 'deposits.status', [AGG('sum', 'deposits', 'deposits.amount', label='Deposits')]),
        CHART('Cash balance per month', 'column', 'month', [AGG('sum', 'cash', 'cash.closing', date='cash.month', label='Closing cash')]),
        CHART('Cash in against out per month', 'bar', 'month', [AGG('sum', 'cash', 'cash.cash_in', date='cash.month', label='Cash in'), AGG('sum', 'cash', 'cash.cash_out', date='cash.month', label='Cash out')]),
        CHART('Expenses by category', 'bar', 'expenses.category', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
        CHART('Expenses per month', 'bar', 'month', [AGG('sum', 'expenses', 'expenses.amount', date='expenses.date', label='Expenses')]),
        CHART('Bills by category', 'bar', 'bills.category', [AGG('sum', 'bills', 'bills.amount', label='Bills')]),
        CHART('Payroll per month', 'bar', 'month', [AGG('sum', 'payroll', 'payroll.total', date='payroll.month', label='Payroll')]),
        CHART('Tax set aside per month', 'bar', 'month', [AGG('sum', 'tax', 'tax.set_aside', date='tax.month', label='Set aside')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6
signature = [
    {"name": "A/R aging of balances", "why": "every unpaid invoice grouped 0-30, 31-60, 61-90 and 90+ days past due by family, with days outstanding and the next step named", "where": "Aging by Family"},
    {"name": "Reminder ladder", "why": "days overdue and broken promises pick the step: friendly reminder, call, payment plan or notice to pause care, with the date of the next step", "where": "Reminder Ladder"},
    {"name": "13-week cash forecast", "why": "your own tuition history, government payments due, payroll, rent and bills turned into 13 weekly balances against your cash floor, with a families-leave test", "where": "Cash Forecast 13 Weeks"},
    {"name": "Autopay and card-on-file effect", "why": "late invoices of autopay and manual payers side by side, with the chasing time saved set against the card fee", "where": "Autopay and Card on File"},
    {"name": "Government payment reconciliation", "why": "expected against received by month, the gap and the family share still owed, with the day the payer's wait ends", "where": "Government Reconciliation"},
    {"name": "Payment plan builder", "why": "a first payment, instalments and dates turned into money in within 13 weeks and a smaller 90+ tail", "where": "Payment Plan Builder"},
    {"name": "Late payer risk ranking", "why": "habit, days paid late and open balance scored for every family so you call the three at risk first", "where": "Late Payer Risk Ranking"},
    {"name": "Write-off decision", "why": "balance, chance of payment and the cost of chasing give keep chasing, agree a plan or write off", "where": "Write-off Decision"},
    {"name": "Cash floor warning and bill calendar", "why": "the lowest forecast week, what closes the gap and the order to pay the next bills", "where": "Cash Floor Warning"},
    {"name": "Collection rate against your own history", "why": "money collected over money due each month against your last 3 months, with a band you set", "where": "Collection Rate by Month"}]
competitors = [
    {"what": "free invoice template", "lacks": "lists invoices but never groups unpaid ones by days overdue, ranks who to call or tracks promises"},
    {"what": "subscription childcare management software", "lacks": "charges every month or per child and hides the cash forecast and the collection reports behind paid add-ons"},
    {"what": "generic bookkeeping spreadsheet", "lacks": "records money in and out but knows nothing of government payments, deposits or payment plans for families"},
    {"what": "bank statement export", "lacks": "shows what arrived but not which family or invoice is behind, nor the next 13 weeks"},
    {"what": "paper ledger and sticky notes", "lacks": "keeps promises on notes with no check on whether they were kept and no reminder ladder"}]
guide = [
    'Open Start and type your center name, your cash floor, the days that set each step of the reminder ladder and your card fee in the yellow cells.',
    'Fill Families: one row per family with the billing cycle, pay method, autopay, how they usually pay and any government share.',
    'Type each invoice on Invoices and each payment on Payments. The family share, open balance, days overdue and aging band fill in.',
    'Read Aging by Family and Overdue Families every week: they show who owes what and who to act on first. Reminder Schedule lists the 20 oldest overdue invoices with the next step.',
    'Write every payment promise on Promises and mark it kept or broken; Payment Plans and Plan Instalments hold the plans you agree.',
    'Type each government childcare payment on Government Payments; Government Reconciliation shows expected against received by month and the family share still owed.',
    'Keep Deposits, Cash by Month, Bills, Expenses, Payroll and Tax Set-aside up to date: they feed the Cash Forecast 13 Weeks and the bill, payroll and tax tools.',
    'Read Collections and Autopay for the collection rate and the autopay effect by month.',
    f'Use the {len(tools)} tools for aging, autopay, government payments, the 13-week forecast, plans, the reminder ladder, promises, risk, write-offs, the cash floor, bills, deposits, tax, payment mix, chasing time, payroll dates and the collection rate.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Payments, Balances and Cash Dashboard and Charts every week.']
listing = {"title": "Childcare Center Payments, Balances and Cash Excel Template: A/R Aging, Reminder Ladder, 13-Week Cash Forecast, Autopay",
    "headline": "Collect tuition on time and see your cash 13 weeks ahead",
    "tags": ["childcare center", "daycare template", "home daycare", "ar aging", "cash forecast", "payment plan", "tuition billing", "late payments", "autopay", "daycare excel", "cash flow", "collection rate", "daycare owner"],
    "description": ("Chase tuition and watch your cash in one Excel workbook for a home daycare or childcare center. Built for an owner-director or the assistant director who does the billing. "
        "Invoices and payments sit on two sheets; the open balance, days overdue and aging band of each invoice fill in. Aging by Family groups what is owed into 0-30, 31-60, 61-90 and 90+ days past due, "
        "shows days outstanding and names the next step for each family: friendly reminder, call, payment plan or notice to pause care.\n\n"
        "Promises record whether each family kept its word; Late Payer Risk Ranking scores every family so you call the three at risk first; the Write-off Decision tool weighs the chance of payment against the cost of chasing. "
        "Government Payments and Government Reconciliation compare what a government childcare payment should have paid with what arrived, month by month, with the family share still owed. "
        "Cash by Month, Bills, Payroll, Expenses and Tax Set-aside feed a 13-week cash forecast built from your own history, with a Base, Best and Worst case and an if-families-leave test against your cash floor.\n\n"
        f"{len(tools)} tools answer one weekly question each, with a verdict and a what-if row. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to families, the assistant director, the owner, the accountant and suppliers. "
        "Children's data is names, dates and status only.\n\n"
        "This is part five of the Home Daycare and Childcare Center suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. It helps you keep track of payments and cash; it does not promise results, and tax figures are estimates to confirm with your adviser."),
    "features": ["A/R aging of balances by family: 0-30, 31-60, 61-90 and 90+ days", "Reminder ladder with the date of the next step", "13-week cash forecast with Base, Best, Worst and families-leave cases",
                 "Payment plan builder with effect on cash and the 90+ balance", "Government payment reconciliation by month", "Autopay effect: late invoices, chasing time and card fee",
                 "Late payer risk ranking and write-off decision", f"{len(tools)} decision tools with a verdict and what-if rows", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p5', slug='childcare-center-payments', profession='Home Daycare and Childcare Center', name='Payments, Balances and Cash',
         tagline='Collect tuition on time and see your cash 13 weeks ahead', price_usd=29,
         colors={"primary": "#33658A", "accent": "#F6AE2D"}, settings=settings, lists=base_lists() + verdict_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Payments, balances and cash"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']), 'words', sum(len(v) for v in _VN.values()))
