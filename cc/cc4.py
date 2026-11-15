"""Home Daycare and Childcare Center suite - part 4: Tuition, Fees and Invoices."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc4_lists import *
from cc4_tables import settings, tables, ENR, LEFT, WK, MO, HELD, MS
from cc4_tools import tools
import cc4_data as D

SUITE = 'fx-20261115-childcare-center'
NOTE = "Sample wording: adapt it to your own center and check your local rules."
YES = '{list:yesno.yes}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)

# extra columns that carry whole-sheet totals for the messages
def add(tkey, *cols):
    for t in tables:
        if t['key'] == tkey: t['columns'].extend(cols)
add('weekly_run', CALC('run_n', 'Weekly invoices in the run', 'int', 'COUNTIFS({range:weekly_run.children},">0")', 9), CALC('run_total', 'Weekly run amount', 'money', 'SUM({range:weekly_run.amount})', 11),
    CALC('monthly_n', 'Monthly invoices in the run', 'int', 'COUNTIFS({range:monthly_run.children},">0")', 9), CALC('monthly_total', 'Monthly run amount', 'money', 'SUM({range:monthly_run.amount})', 11))
add('inv_check', CALC('differ_n', 'Invoices that differ', 'int', 'COUNTIFS({range:inv_check.verdict},%s)' % ca('Differs'), 9))
add('deposits', CALC('refund_n', 'Deposits to refund, 30 days', 'int', 'COUNTIFS({range:deposits.refund_date},">="&{today},{range:deposits.refund_date},"<="&({today}+30))', 9),
    CALC('refund_amount', 'Amount to refund, 30 days', 'money', 'SUMIFS({range:deposits.amount},{range:deposits.refund_date},">="&{today},{range:deposits.refund_date},"<="&({today}+30))', 11))
add('statements', CALC('year_parent', 'Parent paid, all families, year', 'money', 'SUMIFS({range:statements.parent_paid},{range:statements.year},{col:year})', 12),
    CALC('year_gov', 'Government paid, all families, year', 'money', 'SUMIFS({range:statements.government_paid},{range:statements.year},{col:year})', 12))

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('rate_change_sheet', 'Rate Change Notice Sheet', 'Rate change for one room and schedule', 'rates.rate_id', F(
        ('Room', 'rates.room'), ('Schedule', 'rates.schedule'), ('Weekly rate now', 'rates.weekly_rate'), ('Weekly rate last year', 'rates.last_year_rate'), ('Rise this year', 'rates.rise_pct'), ('Day rate now', 'rates.day_rate'), ('Rate per hour now', 'rates.hour_rate')) + [
        FF('New weekly rate after the planned rise', 'ROUND(%s*(1+{set:planned_rise}),0)' % LK('rates', 'rate_id', 'weekly_rate'), 'money'),
        FF('Extra a week for a family', 'ROUND(%s*{set:planned_rise},0)' % LK('rates', 'rate_id', 'weekly_rate'), 'money'),
        FF('New monthly rate', 'ROUND(ROUND(%s*(1+{set:planned_rise}),0)*52/12,0)' % LK('rates', 'rate_id', 'weekly_rate'), 'money'),
        FF('New rate starts on', '{set:rise_start}', 'date'), FF('Send the notice by', '{set:rise_start}-{set:notice_days}', 'date')]),
    FORM('invoice_adjust_sheet', 'Invoice Adjustment Sheet', 'Invoice with the lines to correct', 'invoices.invoice_id', F(
        ('Family', 'invoices.family'), ('Cycle', 'invoices.cycle'), ('Period start', 'invoices.period_start'), ('Period end', 'invoices.period_end'), ('Issued on', 'invoices.issued_on'), ('Due date', 'invoices.due_date'),
        ('Tuition', 'invoices.tuition'), ('Discount', 'invoices.discount'), ('Extras', 'invoices.extras'), ('Amount', 'invoices.amount'), ('Government expected', 'invoices.gov_expected'), ('Parent due', 'invoices.parent_due'), ('Status', 'invoices.status')) + [
        FF('Amount worked out from the lines', '%s-%s+%s' % (LK('invoices', 'invoice_id', 'tuition'), LK('invoices', 'invoice_id', 'discount'), LK('invoices', 'invoice_id', 'extras')), 'money'),
        FF('Discount share of tuition', 'IFERROR(%s/%s,0)' % (LK('invoices', 'invoice_id', 'discount'), LK('invoices', 'invoice_id', 'tuition')), 'pct'),
        FF('Days from issue to the due date', '%s-%s' % (LK('invoices', 'invoice_id', 'due_date'), LK('invoices', 'invoice_id', 'issued_on')), 'int')]),
    FORM('discount_request', 'Discount Request Sheet', 'Discount for a child and what it costs', 'discounted.child', F(
        ('Family', 'discounted.family'), ('Room', 'discounted.room'), ('Schedule', 'discounted.schedule'), ('Discount', 'discounted.discount'), ('Discount share', 'discounted.discount_pct'), ('Discount from', 'discounted.from_date'),
        ('Weekly rate', 'discounted.weekly_rate'), ('Cost per week', 'discounted.weekly_cost'), ('Cost per month', 'discounted.monthly_cost'), ('Cost per year', 'discounted.yearly_cost')) + [
        FF('Share of all tuition each month', 'IFERROR(%s/(SUMIFS({range:children.weekly_rate},{range:children.status},%s)*52/12),0)' % (LK('discounted', 'child', 'monthly_cost'), ENR), 'pct'),
        FF('Most discounts you give', '{set:discount_limit}', 'pct'), FF('Weekly rate with the discount', '%s-%s' % (LK('discounted', 'child', 'weekly_rate'), LK('discounted', 'child', 'weekly_cost')), 'money')]),
    FORM('registration_sheet', 'Registration Fee Sheet', 'Registration fee of a new starter', 'starters.child', F(
        ('Family', 'starters.family'), ('Room', 'starters.room'), ('Start date', 'starters.start_date'), ('Weekly rate', 'starters.weekly_rate'), ('Registration charged', 'starters.registration'), ('Registration fee due', 'starters.reg_due'),
        ('Fee check', 'starters.fee_flag'), ('First invoice', 'starters.first_invoice')) + [
        FF('Registration still to charge', 'MAX(0,%s-%s)' % (LK('starters', 'child', 'reg_due'), LK('starters', 'child', 'registration')), 'money'),
        FF('Days from today to the start date', '%s-{today}' % LK('starters', 'child', 'start_date'), 'int'), FF('Starters in the last 12 months', 'COUNTIFS({range:starters.start_date},">="&({today}-365))', 'int')]),
    FORM('supply_fee_sheet', 'Supply Fee Sheet', 'Supply fee of a child', 'children.child_id', F(
        ('Child', 'children.child'), ('Family', 'children.family'), ('Room', 'children.room'), ('Schedule', 'children.schedule'), ('Start date', 'children.start_date'), ('Status', 'children.status'), ('Supply fee', 'children.supply_due')) + [
        FF('Supply fees charged to the family', 'SUMIFS({range:invoices.supply_fee},{range:invoices.family},%s)' % LK('children', 'child_id', 'family'), 'money'),
        FF('Supply fee left to charge', 'IF(%s=%s,MAX(0,{set:supply_fee}-SUMIFS({range:invoices.supply_fee},{range:invoices.family},%s)),0)' % (LK('children', 'child_id', 'status'), ENR, LK('children', 'child_id', 'family')), 'money'),
        FF('Supply fee last year', '{set:supply_fee}-10', 'money')]),
    FORM('deposit_receipt_sheet', 'Deposit Receipt Sheet', 'Receipt for a deposit', 'deposits.deposit_id', F(
        ('Child', 'deposits.child'), ('Family', 'deposits.family'), ('Amount', 'deposits.amount'), ('Received on', 'deposits.received_on'), ('Status', 'deposits.status')) + [
        FF('Weekly rate of the child', 'IFERROR(INDEX({range:children.weekly_rate},MATCH(%s,{range:children.child},0)),0)' % LK('deposits', 'deposit_id', 'child'), 'money'),
        FF('Weeks of tuition held', 'IFERROR(%s/INDEX({range:children.weekly_rate},MATCH(%s,{range:children.child},0)),0)' % (LK('deposits', 'deposit_id', 'amount'), LK('deposits', 'deposit_id', 'child')), 'num'),
        FF('Deposits held for this family', 'SUMIFS({range:deposits.amount},{range:deposits.family},%s,{range:deposits.status},%s)' % (LK('deposits', 'deposit_id', 'family'), HELD), 'money')]),
    FORM('deposit_refund_sheet', 'Deposit Refund Sheet', 'Refund or use of a deposit when a child leaves', 'deposits.deposit_id', F(
        ('Child', 'deposits.child'), ('Family', 'deposits.family'), ('Amount held', 'deposits.amount'), ('Status', 'deposits.status'), ('Settled on', 'deposits.settled_on'), ('Notice days given', 'deposits.notice_days'), ('Notice check', 'deposits.notice_check')) + [
        FF('Notice days you require', '{set:notice_days}', 'int'),
        FF('Amount to refund or apply', 'IF(%s>={set:notice_days},%s,0)' % (LK('deposits', 'deposit_id', 'notice_days'), LK('deposits', 'deposit_id', 'amount')), 'money'),
        FF('Amount kept after short notice', 'IF(%s>={set:notice_days},0,%s)' % (LK('deposits', 'deposit_id', 'notice_days'), LK('deposits', 'deposit_id', 'amount')), 'money')]),
    FORM('dropin_sheet', 'Drop-in Day Charge Sheet', 'Charge for a drop-in day', 'drop_in.drop_id', F(
        ('Date', 'drop_in.date'), ('Child', 'drop_in.child'), ('Family', 'drop_in.family'), ('Room', 'drop_in.room'), ('Hours', 'drop_in.hours'), ('Day rate', 'drop_in.day_rate'), ('Surcharge', 'drop_in.surcharge'), ('Charge', 'drop_in.charge')) + [
        FF('Surcharge share', '{set:drop_in_surcharge}', 'pct'), FF('Charge for each hour', 'IFERROR(%s/%s,0)' % (LK('drop_in', 'drop_id', 'charge'), LK('drop_in', 'drop_id', 'hours')), 'money'),
        FF('Drop-in days of this family', 'COUNTIFS({range:drop_in.family},%s)' % LK('drop_in', 'drop_id', 'family'), 'int')]),
    FORM('late_fee_sheet', 'Late Pickup Fee Sheet', 'Late pickup and its fee', 'late_fees.fee_id', F(
        ('Date', 'late_fees.date'), ('Child', 'late_fees.child'), ('Family', 'late_fees.family'), ('Room', 'late_fees.room'), ('Late minutes', 'late_fees.late_minutes'), ('Fee', 'late_fees.fee'), ('Waived', 'late_fees.waived'), ('Charged', 'late_fees.charged'), ('Overtime cost', 'late_fees.overtime_cost')) + [
        FF('Grace minutes', '{set:late_grace_min}', 'int'), FF('Minutes past the grace', 'MAX(0,%s-{set:late_grace_min})' % LK('late_fees', 'fee_id', 'late_minutes'), 'int'),
        FF('Late pickups, last 180 days', 'COUNTIFS({range:late_fees.family},%s,{range:late_fees.date},">="&({today}-180))' % LK('late_fees', 'fee_id', 'family'), 'int')]),
    FORM('fee_waiver_sheet', 'Fee Waiver Sheet', 'Waiver decision for a family that collects late', 'repeat_late.family', F(
        ('Late pickups, 6 months', 'repeat_late.events'), ('Late minutes', 'repeat_late.minutes'), ('Fees charged', 'repeat_late.fees'), ('Waived', 'repeat_late.waived_n'), ('Share waived', 'repeat_late.share_waived'), ('Overtime cost', 'repeat_late.overtime'), ('Status', 'repeat_late.status')) + [
        FF('Fees waived in money', 'SUMIFS({range:late_fees.fee},{range:late_fees.family},{pick},{range:late_fees.waived},%s,{range:late_fees.date},">="&({today}-180))' % YES, 'money'),
        FF('Pickups that make a family repeat-late', '{set:repeat_events}', 'int'), FF('Pickups left before the repeat-late flag', 'MAX(0,{set:repeat_events}-%s)' % LK('repeat_late', 'family', 'events'), 'int')]),
    FORM('cycle_change_sheet', 'Billing Cycle Change Sheet', 'Change of billing cycle for a family', 'families.family_id', F(
        ('Family', 'families.family'), ('Parent or guardian', 'families.guardian'), ('Billing cycle now', 'families.cycle'), ('New billing cycle', 'families.next_cycle'), ('Children enrolled', 'families.kids_now'), ('Weekly tuition after discounts', 'families.weekly_tuition'),
        ('Next invoice date', 'families.next_invoice'), ('Payment method', 'families.pay_method')) + [
        FF('Weekly invoice amount', 'ROUND(%s,2)' % LK('families', 'family_id', 'weekly_tuition'), 'money'), FF('Monthly invoice amount', 'ROUND(%s*52/12,2)' % LK('families', 'family_id', 'weekly_tuition'), 'money'),
        FF('Invoices a year now', 'IF(%s=%s,52,12)' % (LK('families', 'family_id', 'cycle'), WK), 'int'), FF('Invoices a year after the change', 'IF(%s=%s,12,52)' % (LK('families', 'family_id', 'cycle'), WK), 'int')]),
    FORM('statement_request', 'Statement Request Sheet', 'Yearly payment statement for a family', 'statements.statement_id', F(
        ('Family', 'statements.family'), ('Year', 'statements.year'), ('Parent paid', 'statements.parent_paid'), ('Government paid', 'statements.government_paid'), ('Total paid', 'statements.total_paid'), ('Payments', 'statements.payments'),
        ('Ledger parent paid', 'statements.ledger_paid'), ('Difference to the ledger', 'statements.difference'), ('Ledger check', 'statements.check'), ('Sent check', 'statements.sent_flag')) + [
        FF('Share paid by the government', 'IFERROR(%s/%s,0)' % (LK('statements', 'statement_id', 'government_paid'), LK('statements', 'statement_id', 'total_paid')), 'pct'),
        FF('Statements of this family', 'COUNTIFS({range:statements.family},%s)' % LK('statements', 'statement_id', 'family'), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('weekly_invoice_doc', 'Weekly Invoice', 'Weekly invoice for a family', 'weekly_run.family', [
        'Weekly invoice of {set:company}, dated {col:weekly_run.run_date}. Family: {col:weekly_run.family}. Children: {col:weekly_run.children}.',
        'Tuition: {col:weekly_run.tuition}. Discount: {col:weekly_run.discount}. Extras from last week (drop-in days and late pickup fees): {col:weekly_run.extras}. Amount: {col:weekly_run.amount}. Fees are before any tax.',
        'Government childcare payment expected: {col:weekly_run.gov_expected}. Amount due from you: {col:weekly_run.parent_due}. Please pay by {col:weekly_run.due_date}.',
        'Questions about this invoice are welcome. Please tell us within a few days so that we can correct it.'], ['Assistant director', 'Family'], NOTE),
    DOC('monthly_invoice_doc', 'Monthly Invoice', 'Monthly invoice for a family', 'monthly_run.family', [
        'Monthly invoice of {set:company}, dated {col:monthly_run.run_date}. Family: {col:monthly_run.family}. Children: {col:monthly_run.children}.',
        'Tuition for the month: {col:monthly_run.tuition}. Discount: {col:monthly_run.discount}. Extras from last month (drop-in days and late pickup fees): {col:monthly_run.extras}. Amount: {col:monthly_run.amount}. Fees are before any tax.',
        'Government childcare payment expected: {col:monthly_run.gov_expected}. Amount due from you: {col:monthly_run.parent_due}. Please pay by {col:monthly_run.due_date}.',
        'The monthly amount spreads 52 weeks of tuition over 12 months, so closure days are already included.'], ['Assistant director', 'Family'], NOTE),
    DOC('rate_card_doc', 'Rate Card for Families', 'Rate card for a room and schedule', 'rates.rate_id', [
        'Rate card of {set:company}, dated {today}. Room: {col:rates.room}. Schedule: {col:rates.schedule}, {col:rates.days} days a week, {col:rates.hours_day} hours a day.',
        'Weekly rate: {col:rates.weekly_rate}. Monthly rate: {col:rates.monthly_rate}. Day rate: {col:rates.day_rate}. Rate per hour: {col:rates.hour_rate}.',
        'A lower fee for a second child in the same family: {col:rates.sibling_rate} a week. Staff child rate: {col:rates.staff_rate} a week.',
        'Registration fee: {set:reg_fee}. Supply fee each September: {set:supply_fee}. Drop-in day: day rate plus {set:drop_in_surcharge}. Fees are before any tax.'], ['Owner-director', 'Family'], NOTE),
    DOC('rise_notice_doc', 'Fee Rise Notice', 'Notice of a fee rise', 'rates.rate_id', [
        'Notice of {set:company}, dated {today}. Dear family, our rates change from {set:rise_start}.',
        'For {col:rates.room}, {col:rates.schedule}: the weekly rate is now {col:rates.weekly_rate}. From {set:rise_start} the rate rises by {set:planned_rise}.',
        'We give {set:notice_days} days of notice. If you want to change your days or leave, please tell us in writing before the new rates start.',
        'We review the rates once a year. Thank you for trusting us with your child.'], ['Owner-director', 'Family'], NOTE),
    DOC('deposit_receipt_doc', 'Deposit Receipt', 'Receipt for a deposit', 'deposits.deposit_id', [
        'Deposit receipt of {set:company}, dated {today}. Receipt for {col:deposits.deposit_id}.',
        'We received {col:deposits.amount} from {col:deposits.family} for {col:deposits.child} on {col:deposits.received_on}.',
        'A deposit is a payment held to keep a place. It is not income until the child leaves: it is applied to the last invoice or refunded when the notice period of {set:notice_days} days was kept.',
        'Check the contract terms for how a deposit is applied or refunded.'], ['Assistant director', 'Family'], NOTE),
    DOC('deposit_refund_doc', 'Deposit Refund Note', 'Note on the refund of a deposit', 'deposits.deposit_id', [
        'Deposit note of {set:company}, dated {today}. Family: {col:deposits.family}. Child: {col:deposits.child}.',
        'Deposit held: {col:deposits.amount}, received on {col:deposits.received_on}. Notice days given: {col:deposits.notice_days}. Notice check: {col:deposits.notice_check}. Notice days required: {set:notice_days}.',
        'When the notice was kept the deposit is applied to the last invoice or refunded. When the notice was short the deposit is kept as agreed in the contract terms.',
        'Status of the deposit: {col:deposits.status}. Settled on: {col:deposits.settled_on}.'], ['Assistant director', 'Family'], NOTE),
    DOC('reg_supply_doc', 'Registration Supply Fee Notice', 'Notice of registration and supply fees', 'starters.child', [
        'Fee notice of {set:company}, dated {today}. Child: {col:starters.child}, family {col:starters.family}, room {col:starters.room}. Start date: {col:starters.start_date}.',
        'Registration fee: {col:starters.reg_due} (charged: {col:starters.registration}). Supply fee: {col:starters.supply_fee} charged. Deposit paid: {col:starters.deposit}.',
        'Your first invoice is {col:starters.first_invoice}, with the tuition of the first period worked out from the start date. Fees are before any tax.',
        'The supply fee is charged each September for the books, art supplies and everyday items of the room.'], ['Assistant director', 'Family'], NOTE),
    DOC('late_policy_doc', 'Late Pickup Fee Policy', 'Late pickup fee policy', 'fees.fee', [
        'Policy of {set:company}, dated {today}. Fee: {col:fees.fee}. Amount: {col:fees.amount}. Rule: {col:fees.rule}.',
        'A fee for collecting a child after closing time plus a grace of {set:late_grace_min} minutes is charged for every late minute at {set:late_fee_per_min}. The fee covers the staff who stay with your child.',
        'The fee is added to the next invoice. The owner-director may waive a fee for a real emergency. Please call us as soon as you know you will be late.',
        'Check your local rules and your contract terms about fees and notice.'], ['Owner-director', 'Family'], NOTE),
    DOC('discount_policy_doc', 'Sibling Staff Discount Policy', 'Sibling and staff discount policy', 'discount_rules.rule', [
        'Policy of {set:company}, dated {today}. Rule: {col:discount_rules.rule}. Share: {col:discount_rules.share}. Yearly cost to the center: {col:discount_rules.yearly_cost}.',
        'A sibling discount is a lower fee for a second child in the same family: {set:sibling_pct} of tuition. A staff discount for the child of a staff member is {set:staff_pct}. Only one discount applies to a child.',
        'Discounts start on the first day of the month after they are agreed and apply to tuition, not to registration, supply or late fees.',
        'The center keeps total discounts under {set:discount_limit} of tuition. Check the contract terms for the details.'], ['Owner-director', 'Family'], NOTE),
    DOC('statement_doc', 'Family Payment Statement', 'Yearly payment statement for a family', 'statements.statement_id', [
        'Yearly payment statement of {set:company}, dated {today}. Family: {col:statements.family}. Year: {col:statements.year}.',
        'Paid by the family: {col:statements.parent_paid}. Paid by a government childcare payment: {col:statements.government_paid}. Total paid for childcare: {col:statements.total_paid}. Number of payments: {col:statements.payments}.',
        'Amounts are tuition and fees before any tax and cover childcare only. Deposits are not included.',
        'This statement is sample wording to help you keep track of your costs. Please confirm with your adviser how to use it.'], ['Assistant director', 'Family'], NOTE),
    DOC('billing_terms_doc', 'Billing Terms Sheet', 'Billing terms for a family', 'families.family_id', [
        'Billing terms of {set:company}, dated {today}. Family: {col:families.family}. Guardian: {col:families.guardian}. Billing cycle: {col:families.cycle}. Payment method: {col:families.pay_method}.',
        'Weekly invoices are issued on Monday and are due {set:weekly_due_days} days later on Friday. Monthly invoices are issued on the 1st and are due {set:invoice_days} days later. Next invoice: {col:families.next_invoice}.',
        'A fee rise needs {set:notice_days} days of written notice. Next closure day: {col:families.next_closure}. Closure days follow the rule in your contract terms.',
        'Late pickup, drop-in days and discounts are described in our policies. Check your local rules and the contract terms.'], ['Owner-director', 'Guardian'], NOTE),
    DOC('fee_history_doc', 'Fee Schedule History', 'Fee schedule, last year and this year', 'rates.rate_id', [
        'Fee schedule history of {set:company}, dated {today}. Room: {col:rates.room}. Schedule: {col:rates.schedule}.',
        'Weekly rate last year: {col:rates.last_year_rate}. Weekly rate this year: {col:rates.weekly_rate}. Rise: {col:rates.rise_pct}. Rate per hour this year: {col:rates.hour_rate}.',
        'Registration fee this year: {set:reg_fee}. Supply fee: {set:supply_fee}. Sibling discount: {set:sibling_pct}. Staff discount: {set:staff_pct}.',
        'Keep this page in your records so that you can show how the rates changed from year to year.'], ['Owner-director', 'Assistant director'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('weekly_run_chk', 'Weekly Invoice Run Steps', 'invoices', 'invoices.issued_on', [('Check last week attendance and drop-in days', -1), ('Check closure days and camp weeks', -1), ('Open the Weekly Invoice Run sheet', 0), ('Check children, tuition and discounts', 0), ('Add late fees and drop-in charges', 0), ('Issue the invoices on Monday', 0), ('Send the invoice messages', 0), ('Note the due date on Friday', 4)]),
    CHK('monthly_run_chk', 'Monthly Invoice Run Steps', 'invoice_status', 'invoice_status.month', [('Check enrolment changes of the month', -3), ('Check starters and leavers for proration', -2), ('Open the Monthly Invoice Run sheet', -1), ('Check government shares', -1), ('Issue the invoices on the 1st', 0), ('Send the invoice messages', 0), ('Note the due date', 14)]),
    CHK('check_invoice_chk', 'Checking an Invoice Steps', 'invoices', 'invoices.issued_on', [('Check the period and the children', 0), ('Check the rate of each room and schedule', 0), ('Check the discounts', 0), ('Check registration and supply fees', 0), ('Check drop-in days and late fees', 0), ('Check the government share', 0), ('Run the Invoice Check', 0), ('Send the invoice', 0)]),
    CHK('new_starter_chk', 'New Starter Fees Steps', 'starters', 'starters.start_date', [('Receive the deposit', -14), ('Charge the registration fee', -7), ('Work out the first invoice with proration', -5), ('Explain the fees and the rates to the family', -3), ('Add the child to the invoice run', 0), ('Check the first invoice after one week', 7), ('Check the supply fee in September', 30)]),
    CHK('sept_supply_chk', 'September Supply Fee Steps', 'invoice_status', 'invoice_status.month', [('Count the children enrolled on 1 September', -14), ('Tell families about the supply fee', -10), ('Add the fee to the first September invoices', -1), ('Run the Registration and Supply Fee Check', 7), ('Chase any missing supply fee', 14)]),
    CHK('deposit_in_chk', 'Deposit Received Steps', 'deposits', 'deposits.received_on', [('Record the deposit in the ledger', 0), ('Send the deposit receipt', 1), ('Keep the deposit apart from income', 1), ('Check the ledger against the account at month end', 30)]),
    CHK('deposit_out_chk', 'Deposit Refund at Leaving Steps', 'children', 'children.end_date', [('Check the notice days given', -30), ('Work out the amount to apply or refund', -7), ('Apply the deposit to the last invoice', 0), ('Refund any amount left', 5), ('Send the deposit note', 5), ('Mark the deposit settled', 5)]),
    CHK('rise_steps_chk', 'Fee Rise Steps', 'fee_rise', 'fee_rise.announce_on', [('Choose the rise in the Fee Rise Planner', -14), ('Check the staff cost share after the rise', -7), ('Send the notice with the new rate card', 0), ('Answer questions from families', 7), ('Count the families who leave', 21), ('Update the rates', 30), ('Check the first invoices at the new rates', 37)]),
    CHK('late_review_chk', 'Late Pickup Fee Review Steps', 'late_fees', 'late_fees.date', [('Record the late minutes', 0), ('Decide on a waiver', 1), ('Add the fee to the next invoice', 7), ('Talk to families who are often late', 14), ('Review the fee against the overtime cost', 30)]),
    CHK('add_discount_chk', 'Adding a Discount Steps', 'discounted', 'discounted.from_date', [('Check the rule for the discount', -7), ('Check the discount limit', -5), ('Record the discount on the child', -3), ('Tell the family in writing', -2), ('Check the first invoice with the discount', 14)]),
    CHK('year_end_chk', 'Year-End Statement Steps', 'invoice_status', 'invoice_status.month', [('Check that every payment is in the ledger', 30), ('Work out the statements', 31), ('Check statements against the ledger', 35), ('Send each family a statement', 50), ('Send the totals to the accountant', 52)]),
    CHK('month_close_chk', 'Month-End Billing Close Steps', 'invoice_status', 'invoice_status.month', [('Check that every invoice of the month is issued', 30), ('Check unpaid invoices and part payments', 31), ('Match the deposit ledger to the account', 31), ('Review discounts and waived fees', 32), ('Write the billed revenue for the owner', 33), ('Send the totals to the accountant', 34)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
OWN = first_name(OWNER); ADIR = first_name(ASSISTANT_DIRECTOR); ACC = first_name([t for t in team if t['role'] == 'Accountant'][0]['name'])
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('inv_notice', 'Family: your invoice', 'invoices', 'invoices.phone', 'Hello {family}, your invoice {invoice_id} for {period_start} to {period_end} is {amount}, due {due_date}. Thank you, {center}'),
    M('wk_ready', 'Family: weekly invoice is ready', 'weekly_run', 'weekly_run.phone', 'Hello {family}, your weekly invoice of {amount} is ready. Please pay {parent_due} by Friday {due_date}. {center}'),
    M('mo_ready', 'Family: monthly invoice is ready', 'monthly_run', 'monthly_run.phone', 'Hello {family}, your monthly invoice of {amount} is ready. Please pay {parent_due} by {due_date}. {center}'),
    M('corrected', 'Family: invoice corrected', 'invoices', 'invoices.phone', 'Hello {family}, we corrected invoice {invoice_id}. The new amount is {amount}, due {due_date}. Sorry for the change. {center}'),
    M('disc_added', 'Family: a discount was added', 'discounted', 'discounted.phone', 'Hello {family}, a discount of {discount_pct} for {child} starts from {from_date}. It saves {monthly_cost} a month. {center}'),
    M('rates_change', 'Family: our rates change', 'families', 'families.phone', 'Hello {guardian}, our rates change on {new_date}. Your weekly tuition will be {new_weekly}. The new rate card is on its way. {center}'),
    M('rise_by', 'Family: your fee will rise', 'families', 'families.phone', 'Hello {guardian}, your fee will rise by {rise_share} from {new_date}. Please ask us if you have any question. {center}'),
    M('notice_remind', 'Family: notice period of the rise', 'families', 'families.phone', 'Hello {guardian}, a reminder: the new rates start on {new_date}. If you want to change your days, tell us in writing before then. {center}'),
    M('reg_fee', 'Family: your registration fee', 'starters', 'starters.phone', 'Hello {family}, the registration fee for {child} is {reg_due}. {child} starts on {start_date}. {center}'),
    M('supply_fee', 'Family: your supply fee', 'children', 'children.phone', 'Hello {guardian}, the supply fee for {child} for September is {supply_due}. It is added to the first invoice of the month. {center}'),
    M('dep_received', 'Family: deposit received', 'deposits', 'deposits.phone', 'Hello {family}, we received your deposit of {amount} for {child} on {received_on}. Thank you. {center}'),
    M('dep_applied', 'Family: deposit applied to last invoice', 'deposits', 'deposits.phone', 'Hello {family}, your deposit of {amount} for {child} will be applied to your last invoice. {center}'),
    M('dep_refund', 'Family: deposit refunded', 'deposits', 'deposits.phone', 'Hello {family}, your deposit of {amount} for {child} is refunded on {refund_date}. {center}'),
    M('dropin', 'Family: drop-in day charge', 'drop_in', 'drop_in.phone', 'Hello {family}, your drop-in day for {child} on {date} costs {charge}. It is added to your next invoice. {center}'),
    M('late_fee', 'Family: late pickup fee', 'late_fees', 'late_fees.phone', 'Hello {family}, {child} was collected {late_minutes} minutes after closing time on {date}. The late pickup fee is {fee}. {center}'),
    M('late_waived', 'Family: late fee waived', 'late_fees', 'late_fees.phone', 'Hello {family}, we waived the late pickup fee of {fee} for {date}. Thank you for letting us know. {center}'),
    M('late_policy', 'Family: late pickups add up', 'repeat_late', 'repeat_late.phone', 'Hello {family}, there were {events} late pickups in the last 6 months, {minutes} minutes in total. Please see our late pickup policy. {center}'),
    M('camp_week', 'Family: camp week replaces tuition', 'invoices', 'invoices.phone', 'Hello {family}, the camp fee of {camp_fee} on invoice {invoice_id} replaces the tuition of the camp weeks. {center}'),
    M('closure_credit', 'Family: closure day credit', 'families', 'families.phone', 'Hello {guardian}, we are closed on {next_closure}. The day is credited on your next invoice as agreed in your contract terms. {center}'),
    M('cycle_change', 'Family: billing cycle changes', 'families', 'families.phone', 'Hello {guardian}, your billing cycle changes from {cycle} to {next_cycle}. Your next invoice date is {next_invoice}. {center}'),
    M('stmt_ready', 'Family: yearly statement ready', 'statements', 'statements.phone', 'Hello {family}, your yearly payment statement for {year} is ready. Total paid for childcare: {total_paid}. Please confirm with your adviser how to use it. {center}'),
    M('stmt_diff', 'Family: difference on the statement', 'statements', 'statements.phone', 'Hello {family}, we found a difference of {difference} on your {year} statement. Please check your own records and tell us. {center}'),
    M('first_invoice', 'Family: your first invoice', 'starters', 'starters.phone', 'Hello {family}, your first invoice for {child} is {first_invoice} from {start_date}. {center}'),
    M('gov_share', 'Family: government payment share', 'invoices', 'invoices.phone', 'Hello {family}, on invoice {invoice_id} a government childcare payment covers {gov_expected}, so you pay {parent_due}. Please check the amounts. {center}'),
    M('ad_issue', 'Assistant director: invoices to issue', 'weekly_run', 'weekly_run.director_phone', 'Hello %s, %s' % (ADIR, '{run_n} weekly invoices ({run_total}) and {monthly_n} monthly invoices ({monthly_total}) are ready for the next runs. Next weekly run: {run_date}. {center}')),
    M('ad_differ', 'Assistant director: invoices that differ', 'inv_check', 'inv_check.director_phone', 'Hello %s, %s' % (ADIR, '{differ_n} invoices differ from booked days. Open {invoice_id} of {family}: difference {difference}. {center}')),
    M('ad_deposits', 'Assistant director: deposits to refund', 'deposits', 'deposits.director_phone', 'Hello %s, %s' % (ADIR, '{refund_n} deposits totalling {refund_amount} are due to refund in the next 30 days. {center}')),
    M('ad_statements', 'Assistant director: statements to send', 'statements', 'statements.director_phone', 'Hello %s, %s' % (ADIR, '{unsent_n} yearly statements are not sent yet. {center}')),
    M('ow_revenue', 'Owner: billed revenue of the month', 'invoice_status', 'invoice_status.owner_phone', 'Hello %s, %s' % (OWN, 'billed revenue for {month} is {billed} from {invoices} invoices. {unpaid} of it is still unpaid. {center}')),
    M('ow_rise', 'Owner: fee rise result and target', 'fee_rise', 'fee_rise.owner_phone', 'Hello %s, %s' % (OWN, 'a rise of {rise_pct} with {leavers} leavers gives {net_revenue} a month and a staff cost share of {share_after}: {holds}. {center}')),
    M('ow_late', 'Owner: late fees against overtime cost', 'invoice_status', 'invoice_status.owner_phone', 'Hello %s, %s' % (OWN, 'for {month} late fees charged were {late_charged} against an overtime cost of {overtime_cost}. {center}')),
    M('ow_discounts', 'Owner: discounts given', 'invoice_status', 'invoice_status.owner_phone', 'Hello %s, %s' % (OWN, 'discounts given for {month} were {discounts} on {billed} billed. {center}')),
    M('acc_month', 'Accountant: billed revenue and deposits', 'invoice_status', 'invoice_status.accountant_phone', 'Hello %s, %s' % (ACC, 'billed revenue for {month} is {billed}, of which {government} is a government childcare payment. Deposits held now: {deposits_held}. {center}')),
    M('acc_stmts', 'Accountant: yearly statement totals', 'statements', 'statements.accountant_phone', 'Hello %s, %s' % (ACC, 'yearly statement totals for {year}: parents paid {year_parent}, government childcare payments {year_gov}. {center}')),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def AMT(c): return 'SUMIFS({range:invoices.%s},{range:invoices.month},%s)' % (c, MS)
D90 = '{range:invoices.issued_on},">="&({today}-90)'
BASE3 = 'SUMIFS({range:rev_room.revenue},{range:rev_room.month},">="&EDATE(%s,-3),{range:rev_room.month},"<"&%s)/3' % (MS, MS)
kpis = [
    KPI('Invoices issued this month', 'COUNTIFS({range:invoices.month},%s)' % MS, 'int'),
    KPI('Billed revenue this month', AMT('amount'), 'money'),
    KPI('Tuition billed this month', AMT('tuition'), 'money'),
    KPI('Discounts given this month', AMT('discount'), 'money'),
    KPI('Discount share of tuition, this year', 'IFERROR(SUM({range:invoices.discount})/SUM({range:invoices.tuition}),0)', 'pct'),
    KPI('Registration fees this month', AMT('registration'), 'money'),
    KPI('Supply fees this year', 'SUM({range:invoices.supply_fee})', 'money'),
    KPI('Drop-in charges this month', AMT('drop_in'), 'money'),
    KPI('Camp fees, last 90 days', 'SUMIFS({range:invoices.camp_fee},%s)' % D90, 'money'),
    KPI('Late fees charged this month', 'SUMIFS({range:late_fees.charged},{range:late_fees.month},%s)' % MS, 'money'),
    KPI('Late fees waived this month', 'SUMIFS({range:late_fees.fee},{range:late_fees.month},%s,{range:late_fees.waived},%s)' % (MS, YES), 'money'),
    KPI('Late fees charged, last 30 days', 'SUMIFS({range:late_fees.charged},{range:late_fees.date},">="&({today}-30))', 'money'),
    KPI('Repeat-late families, last 6 months', 'COUNTIFS({range:repeat_late.status},%s)' % ca('Repeat late'), 'int'),
    KPI('Invoices differing from booked days', 'COUNTIFS({range:inv_check.verdict},%s)' % ca('Differs'), 'int'),
    KPI('Weekly invoices in the next run', 'COUNTIFS({range:weekly_run.children},">0")', 'int'),
    KPI('Monthly invoices in the next run', 'COUNTIFS({range:monthly_run.children},">0")', 'int'),
    KPI('Average invoice amount, this year', 'IFERROR(AVERAGE({range:invoices.amount}),0)', 'money'),
    KPI('Average weekly rate paid', 'IFERROR(AVERAGEIFS({range:children.weekly_rate},{range:children.status},%s),0)' % ENR, 'money'),
    KPI('Average weekly rate paid, Infants', 'IFERROR(AVERAGEIFS({range:children.weekly_rate},{range:children.status},%s,{range:children.room},%s),0)' % (ENR, tok('room', 'Infants')), 'money'),
    KPI('Deposits held now', 'SUMIFS({range:deposits.amount},{range:deposits.status},%s)' % HELD, 'money'),
    KPI('Deposits to refund, next 30 days', 'SUMIFS({range:deposits.amount},{range:deposits.refund_date},">="&{today},{range:deposits.refund_date},"<="&({today}+30))', 'money'),
    KPI('Deposits applied this year', 'SUMIFS({range:deposits.amount},{range:deposits.status},%s,{range:deposits.settled_on},">="&DATE(YEAR({today}),1,1))' % tok('depstatus', 'Applied'), 'money'),
    KPI('Rate rise this year', 'SUM({range:rates.weekly_rate})/SUM({range:rates.last_year_rate})-1', 'pct'),
    KPI('Staff cost share if rates stay', 'IFERROR({set:staff_pay_month}/(%s),0)' % BASE3, 'pct'),
    KPI('Rise needed to hold the staff cost share', 'MAX(0,IFERROR({set:staff_pay_month}/({set:staff_share_target}*(%s))-1,0))' % BASE3, 'pct'),
    KPI('Families on weekly billing', 'COUNTIFS({range:families.cycle},%s,{range:families.kids_now},">0")' % WK, 'int'),
    KPI('Families on monthly billing', 'COUNTIFS({range:families.cycle},%s,{range:families.kids_now},">0")' % MO, 'int'),
    KPI('Government share of tuition billed', 'IFERROR(SUM({range:invoices.gov_expected})/(SUM({range:invoices.tuition})-SUM({range:invoices.discount})),0)', 'pct'),
    KPI('Parent share of tuition billed', 'IFERROR(1-SUM({range:invoices.gov_expected})/(SUM({range:invoices.tuition})-SUM({range:invoices.discount})),0)', 'pct'),
    KPI('Statements sent this year', 'COUNTIFS({range:statements.sent_on},">="&DATE(YEAR({today}),1,1))', 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Billing Dashboard", "kpis": kpis,
    "monthly": {"title": "Billed revenue, tuition, discounts and extras", "date": "invoices.month", "series": [
        {"label": "Billed revenue", "sum": "invoices.amount", "date": "invoices.month"}, {"label": "Tuition", "sum": "invoices.tuition", "date": "invoices.month"},
        {"label": "Discounts", "sum": "invoices.discount", "date": "invoices.month"}, {"label": "Extras", "sum": "invoices.extras", "date": "invoices.month"}]},
    "breakdowns": [{"title": "Billed amount by invoice status", "by": "invoices.status", "value": "invoices.amount", "agg": "sum"}, {"title": "Late fees charged by room", "by": "late_fees.room", "value": "late_fees.charged", "agg": "sum"},
                   {"title": "Deposits by status", "by": "deposits.status", "value": "deposits.amount", "agg": "sum"}, {"title": "Invoices by billing cycle", "by": "invoices.cycle", "value": "invoices.amount", "agg": "count"}]}
S_ = lambda t: tok('istatus', t)
insights = {"filters": [{"label": "Room", "list": "room"}, {"label": "Billing cycle", "list": "cycle"}, {"label": "Invoice status", "list": "istatus"}],
    "gauges": [
        {"title": "Invoices matching booked days", "num": AGG('count', 'inv_check', where=[('verdict', '=', ca('Matches'))]), "den": AGG('count', 'inv_check')},
        {"title": "Overtime cost against late fees", "num": AGG('sum', 'late_fees', 'late_fees.overtime_cost'), "den": AGG('sum', 'late_fees', 'late_fees.charged')},
        {"title": "Discount share of tuition billed", "num": AGG('sum', 'invoices', 'invoices.discount'), "den": AGG('sum', 'invoices', 'invoices.tuition')},
        {"title": "Deposits held against deposits paid", "num": AGG('sum', 'deposits', 'deposits.amount', where=[('status', '=', HELD)]), "den": AGG('sum', 'deposits', 'deposits.amount')},
        {"title": "Statements sent", "num": AGG('count', 'statements', where=[('sent_flag', '=', ca('Sent'))]), "den": AGG('count', 'statements')},
        {"title": "Fee rise scenarios that hold the target", "num": AGG('count', 'fee_rise', where=[('holds', '=', ca('Holds target'))]), "den": AGG('count', 'fee_rise')}],
    "charts": [
        CHART('Billed revenue per month', 'column', 'month', [AGG('sum', 'invoices', 'invoices.amount', date='invoices.month', label='Billed revenue')]),
        CHART('Tuition per month', 'column', 'month', [AGG('sum', 'invoices', 'invoices.tuition', date='invoices.month', label='Tuition')]),
        CHART('Discounts per month', 'column', 'month', [AGG('sum', 'invoices', 'invoices.discount', date='invoices.month', label='Discounts')]),
        CHART('Revenue by room, last 12 months', 'bar', 'rev_room.room', [AGG('sum', 'rev_room', 'rev_room.revenue', label='Revenue')]),
        CHART('Weekly tuition by schedule, enrolled children', 'bar', 'children.schedule', [AGG('sum', 'children', 'children.weekly_rate', where=[('status', '=', ENR)], label='Weekly tuition')]),
        CHART('Billed revenue by billing cycle', 'bar', 'invoices.cycle', [AGG('sum', 'invoices', 'invoices.amount', label='Billed revenue')]),
        CHART('Extras per month', 'column', 'month', [AGG('sum', 'invoices', 'invoices.extras', date='invoices.month', label='Extras')]),
        CHART('Registration and supply fees per month', 'column', 'month', [AGG('sum', 'invoices', 'invoices.registration', date='invoices.month', label='Registration'), AGG('sum', 'invoices', 'invoices.supply_fee', date='invoices.month', label='Supply fee')]),
        CHART('Drop-in charges per month', 'column', 'month', [AGG('sum', 'invoices', 'invoices.drop_in', date='invoices.month', label='Drop-in charges')]),
        CHART('Camp fees per month', 'column', 'month', [AGG('sum', 'invoices', 'invoices.camp_fee', date='invoices.month', label='Camp fees')]),
        CHART('Late pickups per month', 'column', 'month', [AGG('count', 'late_fees', date='late_fees.date', label='Late pickups')]),
        CHART('Late fees charged and waived per month', 'stacked', 'month', [AGG('sum', 'late_fees', 'late_fees.charged', date='late_fees.date', label='Charged'), AGG('sum', 'late_fees', 'late_fees.fee', date='late_fees.date', where=[('waived', '=', YES)], label='Waived')]),
        CHART('Late minutes by room', 'bar', 'late_fees.room', [AGG('sum', 'late_fees', 'late_fees.late_minutes', label='Late minutes')]),
        CHART('Invoices by status', 'bar', 'invoices.status', [AGG('count', 'invoices', label='Invoices')]),
        CHART('Invoices by billing cycle', 'bar', 'invoices.cycle', [AGG('count', 'invoices', label='Invoices')]),
        CHART('Deposits by status', 'bar', 'deposits.status', [AGG('sum', 'deposits', 'deposits.amount', label='Deposits')]),
        CHART('Deposits received per month', 'column', 'month', [AGG('sum', 'deposits', 'deposits.amount', date='deposits.received_on', label='Deposits received')]),
        CHART('Children by discount', 'bar', 'children.discount', [AGG('count', 'children', label='Children')]),
        CHART('Weekly discount cost by type, enrolled children', 'bar', 'children.discount', [AGG('sum', 'children', 'children.weekly_discount', where=[('status', '=', ENR)], label='Weekly discount cost')]),
        CHART('Weekly rate by room', 'bar', 'rates.room', [AGG('avg', 'rates', 'rates.weekly_rate', label='Weekly rate')]),
        CHART('Weekly rate by schedule', 'bar', 'rates.schedule', [AGG('avg', 'rates', 'rates.weekly_rate', label='Weekly rate')]),
        CHART('Statements by year', 'bar', 'statements.year', [AGG('sum', 'statements', 'statements.total_paid', label='Total paid')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Rate card and invoice builder", "why": "pick a room, schedule and cycle and see weekly, monthly, daily and hourly rates and every invoice line, with the lines that need a second look", "where": "Rate Card and Invoice Builder"},
    {"name": "Invoice check against booked days", "why": "every invoice compared with the children booked and the rate card, so a wrong amount is found before the family finds it", "where": "Invoice Check Tool"},
    {"name": "Sibling discount tester", "why": "a percent, a flat amount or no discount compared by the tuition you keep, with the cheapest rule named", "where": "Sibling Discount Tester"},
    {"name": "Fee rise planner", "why": "a rise with leavers set against the staff cost share you want to hold and the rise needed, with the latest day to announce it", "where": "Fee Rise Planner"},
    {"name": "Late pickup fee tool", "why": "fees under your grace and block rule against the overtime they cause, with repeat-late families ranked", "where": "Late Pickup Fee Tool"},
    {"name": "Deposit ledger", "why": "deposits held, applied, refunded and kept at any month end as a liability, matched to the account", "where": "Deposit and Registration Ledger"},
    {"name": "Yearly payment statement", "why": "one statement per family and year with parent and government payments checked against the ledger", "where": "Yearly Payment Statement"},
    {"name": "Weekly or monthly billing effect", "why": "late share, days to cash and chasing hours of each cycle from your own invoices, with a verdict on moving families", "where": "Weekly or Monthly Billing"},
    {"name": "Mid-month start proration", "why": "the first invoice of a child who starts mid-period from weekdays billed, fees and deposit", "where": "Mid-Month Start Proration"},
    {"name": "Closure day credit rule", "why": "credit every closure, credit the days you choose, offer a make-up day or give no credit, each costed from your closure list", "where": "Closure Day Credit Rule"},
    {"name": "Hourly rate by schedule", "why": "weekly rates turned into rates per hour so the schedule that pays least is repriced first", "where": "Hourly Rate by Schedule"}]
competitors = [
    {"what": "generic invoice spreadsheets", "lacks": "list amounts but know nothing of rooms, schedules, siblings, drop-in days, late pickup fees or a government share on the invoice"},
    {"what": "subscription childcare-management software", "lacks": "charge every month for billing you cannot see into and cannot test a fee rise, a discount rule or a closure credit before you use it"},
    {"what": "free fee tables", "lacks": "give a rate list but no invoice check, no deposit ledger and no yearly statements for parents"},
    {"what": "single-sheet rate cards", "lacks": "show one weekly price and never the monthly, daily and hourly rates, the sibling rate or the rise against last year"},
    {"what": "paper receipt books", "lacks": "record payments but never show deposits held, late fees against overtime or discounts as a share of tuition"}]
guide = [
    'Open Start and type your center name, your fees, your discount limit, the staff pay you plan and the date of the next fee rise in the yellow cells.',
    'Check Rates and Fees. They hold the weekly rate of every room and schedule and the registration, supply, late pickup and drop-in fees that the invoices use.',
    'Keep Families and Children up to date: billing cycle, government share, room, schedule, days, start and end dates and discount.',
    'Open Weekly Invoice Run on Monday and Monthly Invoice Run before the 1st: tuition, discounts, extras and the amount for every family fill in.',
    'Write each issued invoice in Invoices. The amount, parent due, days late and message fields fill in by themselves.',
    'Run the Invoice Check Tool to see which invoices differ from booked days times the rate, and open the largest differences first.',
    'Record late pickups in Late Fees and drop-in days in Drop-in Days; Repeat-Late Families shows who collects late again and again.',
    'Record each deposit in Deposits and match the ledger to your account at every month end with the Deposit and Registration Ledger.',
    'Use New Starters Fees and the Mid-Month Start Proration for every new child: registration, supply fee, deposit and first invoice.',
    'Plan a rise in Fee Rise Planner and Fee Rise Scenarios, then use the Fee Rise Notice Calculator for the latest day to send the notice.',
    'Fill Statements each year and send each family a yearly payment statement.',
    f'Use the {len(tools)} calculators for billing decisions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Billing Dashboard and the charts every week: billed revenue, discounts, extras, late fees, deposits and the staff cost share.']
listing = {"title": "Childcare Center Tuition, Fees and Invoices Excel Template: Weekly and Monthly Invoices, Rates, Deposits, Late Pickup Fees",
    "headline": "Create the right invoice for every family and keep every fee in view",
    "tags": ["childcare", "daycare", "daycare invoice", "tuition tracker", "childcare center", "excel template", "late pickup fee", "sibling discount", "deposit ledger", "fee rise", "home daycare", "rate card", "billing template"],
    "description": ("Run the billing side of a home daycare or childcare center in one Excel workbook. Built for an owner-director and an assistant director who create weekly and monthly invoices, set the rates by room and schedule, give sibling and staff discounts and keep deposits and fees in order. "
        "Rates holds the weekly, monthly, daily and hourly rate of every room and schedule against last year. Invoices holds each invoice with tuition, discount, registration, supply fee, camp fee, drop-in days, late fees and the part paid by a government childcare payment. "
        "Weekly Invoice Run and Monthly Invoice Run work out the next invoice of every family, and Invoice Check compares each invoice with the children booked times the rate.\n\n"
        "Late Fees shows every late pickup with the fee, the waiver and the overtime cost of the staff who stayed. Deposits tracks each deposit (a payment held to keep a place, applied to the last invoice), Statements prepares the yearly payment statement of each family, and Fee Rise Scenarios shows what a rise does to your staff cost share after leavers. "
        "Discounted Children, Drop-in Days, Revenue by Room, Invoice Status by Month and Closures round out the sheets.\n\n"
        f"{len(tools)} calculators cover the invoice builder, the invoice check, a sibling discount tester, the fee-rise planner, the late pickup fee, the deposit ledger, yearly statements, weekly or monthly billing, drop-in day price, camp fee against tuition, discount cost, the notice calculator, rate history, fee checks, mid-month proration, closure day credit, hourly rates and the invoice run. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to families, the assistant director, the owner-director and the accountant.\n\n"
        "This is part four of the Home Daycare and Childcare Center suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Children appear by name, room and dates only. It helps you keep track of your billing and does not promise results. Check your local rules for fees, notice, records and tax; confirm tax questions with your adviser."),
    "features": ["Weekly and monthly invoice runs", "Invoice check against booked days", "Rate card by room and schedule", "Sibling and staff discount cost", "Late pickup fees against overtime",
                 "Deposit ledger held as a liability", "Yearly payment statements", "Fee rise planner with staff cost share", f"{len(tools)} calculators for billing decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p4', slug='childcare-center-tuition', profession='Home Daycare and Childcare Center', name='Tuition, Fees and Invoices',
         tagline='Create the right invoice for every family and keep every fee in view', price_usd=29,
         colors={"primary": "#33658A", "accent": "#F6AE2D"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 4, "of": 8, "focus": "Tuition, fees and invoices"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc4.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
