"""Household Finance suite - part 2: Bills, Subscriptions and Due Dates."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf2_lists import *
from hf2_tables import settings, tables, MS, YES, NO, PAID, UNPAID, LATE, MO, YR, KEEP, REVIEW, CANCEL, INS, UTIL, KIND_INS, JB
from hf2_tools import tools
import hf2_data as D

SUITE = 'fx-20261116-household-finance'
NOTE = "Sample wording: adapt it to your own household."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LKF(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)

# extra columns that carry sheet totals for the messages and documents
# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('bill_sheet', 'Bill Sheet', 'One bill with its cost and due day', 'bills.bill_id', F(
        ('Bill', 'bills.bill'), ('Category', 'bills.category'), ('Amount', 'bills.amount'), ('Due day', 'bills.due_day'), ('Cycle', 'bills.cycle'), ('Autopay', 'bills.autopay'), ('Contact', 'bills.contact'),
        ('Next due date', 'bills.next_due'), ('Cost per month', 'bills.monthly_cost'), ('Cost per year', 'bills.yearly_cost'), ('To set aside per paycheck', 'bills.per_paycheck')) + [
        FF('Share of all bills per month', 'IFERROR(%s/SUM({range:bills.monthly_cost}),0)' % LKF('bills', 'bill_id', 'monthly_cost'), 'pct'),
        FF('Amount a year ago', LKF('bills', 'bill_id', 'last_amount'), 'money'), FF('Change on a year ago', LKF('bills', 'bill_id', 'change'), 'money')]),
    FORM('payment_sheet', 'Bill Payment Sheet', 'Payment of one bill on one due date', 'bill_due.due_id', F(
        ('Bill', 'bill_due.bill'), ('Due date', 'bill_due.due_date'), ('Amount', 'bill_due.amount'), ('Status', 'bill_due.status'), ('Paid on', 'bill_due.paid_on'), ('Payment flag', 'bill_due.flag'),
        ('Days paid late', 'bill_due.days_paid_late'), ('Paid from', 'bill_due.account'), ('Autopay', 'bill_due.autopay'), ('Contact', 'bill_due.contact')) + [
        FF('Joint balance now', JB, 'money'), FF('Amount as a share of the joint balance', 'IFERROR(%s/%s,0)' % (LKF('bill_due', 'due_id', 'amount'), JB), 'pct'),
        FF('Bills due in the same month', 'COUNTIFS({range:bill_due.month},%s)' % LKF('bill_due', 'due_id', 'month'), 'int')]),
    FORM('late_sheet', 'Late Bill Sheet', 'A late bill and what to do next', 'late_list.rank', F(
        ('Bill', 'late_list.bill'), ('Due date', 'late_list.due_date'), ('Days late', 'late_list.days_late'), ('Amount', 'late_list.amount'), ('Payment flag', 'late_list.flag'), ('Contact', 'late_list.contact'),
        ('Contact phone', 'late_list.phone'), ('Next step', 'late_list.next_step')) + [
        FF('Joint balance now', JB, 'money'), FF('Cash left after paying it', '%s-%s' % (JB, LKF('late_list', 'rank', 'amount')), 'money'), FF('Your cash floor', '{set:cash_floor}', 'money')]),
    FORM('autopay_sheet', 'Autopay Change Sheet', 'Autopay or manual for one bill', 'autopay_map.bill', F(
        ('Autopay', 'autopay_map.autopay'), ('Account', 'autopay_map.account'), ('Due day', 'autopay_map.due_day'), ('Next due date', 'autopay_map.next_due'), ('Days before a payday', 'autopay_map.days_before_pay'),
        ('Check', 'autopay_map.check')) + [
        FF('Next payday', '{set:next_payday}', 'date'), FF('Day of the month after payday', 'DAY({set:next_payday}+1)', 'int'),
        FF('Share of bills on autopay', 'IFERROR(COUNTIFS({range:bills.autopay},%s,{range:bills.bill_id},"<>")/COUNTIFS({range:bills.bill_id},"<>"),0)' % YES, 'pct')]),
    FORM('dueday_sheet', 'Due Day Change Request Sheet', 'Request to move the due day of a bill', 'bills.bill_id', F(
        ('Bill', 'bills.bill'), ('Contact', 'bills.contact'), ('Contact phone', 'bills.phone'), ('Amount', 'bills.amount'), ('Due day now', 'bills.due_day'), ('Next due date', 'bills.next_due'),
        ('Days before a payday', 'bills.days_before_pay'), ('Day to ask for', 'bills.new_day')) + [
        FF('Next payday', '{set:next_payday}', 'date'), FF('Autopay', LKF('bills', 'bill_id', 'autopay'), 'text'), FF('Day the new due date falls', '{set:next_payday}+1', 'date')]),
    FORM('sub_sheet', 'Subscription Sheet', 'One subscription with its price and use', 'subs.sub_id', F(
        ('Subscription', 'subs.name'), ('Price', 'subs.price'), ('Cycle', 'subs.cycle'), ('Cost per month', 'subs.monthly_cost'), ('Cost per year', 'subs.yearly_cost'), ('Paid with', 'subs.card'),
        ('Renewal date', 'subs.renewal_date'), ('Last used', 'subs.last_used'), ('Days since use', 'subs.days_since_use'), ('Price 6 months ago', 'subs.price_6m_ago'), ('Decision', 'subs.decision'),
        ('Owner', 'subs.owner'), ('Suggested decision', 'subs.suggested')) + [
        FF('Share of all subscription cost', 'IFERROR(%s/SUM({range:subs.yearly_cost}),0)' % LKF('subs', 'sub_id', 'yearly_cost'), 'pct'), FF('Cost over the next 12 months', LKF('subs', 'sub_id', 'yearly_cost'), 'money')]),
    FORM('cancel_sheet', 'Subscription Cancel Sheet', 'Cancelling one subscription', 'subs.sub_id', F(
        ('Subscription', 'subs.name'), ('Owner', 'subs.owner'), ('Decision', 'subs.decision'), ('Renewal date', 'subs.renewal_date'), ('Cost per month', 'subs.monthly_cost'), ('Cost per year', 'subs.yearly_cost'),
        ('Provider phone', 'subs.provider_phone')) + [
        FF('Cancel by', '%s-{set:cancel_notice_days}' % LKF('subs', 'sub_id', 'renewal_date'), 'date'), FF('Days left to cancel', '%s-{set:cancel_notice_days}-{today}' % LKF('subs', 'sub_id', 'renewal_date'), 'int'),
        FF('Saved over 12 months, an estimate', LKF('subs', 'sub_id', 'yearly_cost'), 'money'), FF('Subscriptions cost per month after', 'SUM({range:subs.monthly_cost})-%s' % LKF('subs', 'sub_id', 'monthly_cost'), 'money')]),
    FORM('review_sheet', 'Subscription Review Sheet', 'Review of a subscription in the ranking', 'subs_rank.rank', F(
        ('Subscription', 'subs_rank.name'), ('Cost per year', 'subs_rank.yearly_cost'), ('Days since use', 'subs_rank.days_since_use'), ('Decision', 'subs_rank.decision'), ('Suggested decision', 'subs_rank.suggested'),
        ('Running cost per year', 'subs_rank.running_yearly'), ('Share of yearly cost', 'subs_rank.share'), ('To review or cancel', 'subs_rank.review_n'), ('Yearly cost to review', 'subs_rank.review_yearly')) + [
        FF('Days unused that flag a cancel', '{set:sub_unused_days}', 'int'), FF('Days left before the cancel flag', 'MAX(0,{set:sub_unused_days}-%s)' % LKF('subs_rank', 'rank', 'days_since_use'), 'int')]),
    FORM('contract_sheet', 'Contract Sheet', 'One contract with its renewal and review dates', 'contracts.contract_id', F(
        ('Contract', 'contracts.contract'), ('Kind', 'contracts.kind'), ('Contact', 'contracts.contact'), ('Contact phone', 'contracts.phone'), ('Amount', 'contracts.amount'), ('Cycle', 'contracts.cycle'),
        ('Cost per year', 'contracts.yearly_cost'), ('Renewal date', 'contracts.renewal_date'), ('Notice days', 'contracts.notice_days'), ('Review on', 'contracts.review_on'), ('Reviewed this cycle', 'contracts.reviewed'),
        ('Days to renewal', 'contracts.days_to_renewal'), ('Review flag', 'contracts.review_flag')) + [
        FF('Last day to give notice', '%s-%s' % (LKF('contracts', 'contract_id', 'renewal_date'), LKF('contracts', 'contract_id', 'notice_days')), 'date')]),
    FORM('insurance_sheet', 'Insurance Renewal Sheet', 'Insurance renewal and the review before it', 'contracts.contract_id', F(
        ('Policy', 'contracts.contract'), ('Contact', 'contracts.contact'), ('Amount', 'contracts.amount'), ('Cycle', 'contracts.cycle'), ('Cost per year', 'contracts.yearly_cost'), ('Renewal date', 'contracts.renewal_date'),
        ('Review on', 'contracts.review_on'), ('Days to review', 'contracts.days_to_review')) + [
        FF('All insurance per year', 'SUMIFS({range:contracts.yearly_cost},{range:contracts.kind},%s)' % KIND_INS, 'money'),
        FF('Share of all insurance', 'IFERROR(%s/SUMIFS({range:contracts.yearly_cost},{range:contracts.kind},%s),0)' % (LKF('contracts', 'contract_id', 'yearly_cost'), KIND_INS), 'pct'),
        FF('Insurance premiums, next 12 months', 'SUM({range:ins_cal.premiums})', 'money'), FF('Review days before renewal', '{set:review_days}', 'int')]),
    FORM('price_sheet', 'Price Rise Sheet', 'A bill that went up and the call to make', 'price_changes.rank', F(
        ('Bill', 'price_changes.bill'), ('Amount a year ago', 'price_changes.last_amount'), ('Amount now', 'price_changes.amount'), ('Change', 'price_changes.change'), ('Change share', 'price_changes.change_share'),
        ('Flag', 'price_changes.flag'), ('Contact', 'price_changes.contact'), ('Contact phone', 'price_changes.phone')) + [
        FF('Rise you act on', '{set:price_rise_alert}', 'pct'),
        FF('Extra cost a year', 'IF(INDEX({range:bills.cycle},MATCH(%s,{range:bills.bill},0))=%s,%s,%s*12)' % (LKF('price_changes', 'rank', 'bill'), YR, LKF('price_changes', 'rank', 'change'), LKF('price_changes', 'rank', 'change')), 'money')]),
    FORM('utility_sheet', 'Utility Reading Sheet', 'A utility bill against last year and the season', 'bills.bill_id', F(
        ('Bill', 'bills.bill'), ('Contact', 'bills.contact'), ('Contact phone', 'bills.phone'), ('Amount', 'bills.amount'), ('Amount a year ago', 'bills.last_amount'), ('Change share', 'bills.change_share'), ('Due day', 'bills.due_day')) + [
        FF('Utilities this month', 'SUMIFS({range:bill_due.amount},{range:bill_due.category},%s,{range:bill_due.month},%s)' % (UTIL, MS), 'money'),
        FF('Utilities the same month last year', 'SUMIFS({range:bill_due.amount},{range:bill_due.category},%s,{range:bill_due.month},EDATE(%s,-12))' % (UTIL, MS), 'money'),
        FF('Average per month, last 12 months', 'SUMIFS({range:bill_due.amount},{range:bill_due.category},%s,{range:bill_due.month},">="&EDATE(%s,-12),{range:bill_due.month},"<"&%s)/12' % (UTIL, MS, MS), 'money'),
        FF('Dearest month in your history', 'MAX({range:bills_month.utilities})', 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('calendar_doc', 'Bills Calendar Page', 'Bills calendar page', 'bills_cal.rank', [
        'Bills calendar of {set:household}, dated {today}. The next bill is {col:bills_cal.bill} for {col:bills_cal.amount}, due on {col:bills_cal.due_date}, in {col:bills_cal.days_away} days. It is paid by {col:bills_cal.autopay} from {col:bills_cal.account}.',
        'In the next {set:calendar_days} days {col:bills_cal.window_n} bills fall due, {col:bills_cal.window_unpaid} of them still unpaid, {col:bills_cal.window_total} in total.',
        'Check the joint account against these bills before every payday and keep your cash floor of {set:cash_floor}.'], ['Household member', 'Partner'], NOTE),
    DOC('unpaid_doc', 'Unpaid Bills Page', 'Unpaid bills before payday', 'unpaid_pay.rank', [
        'Unpaid bills before payday, {set:household}, dated {today}. Next payday: {set:next_payday}. Joint balance now: {col:unpaid_pay.joint_now}. Cash floor: {set:cash_floor}.',
        '{col:unpaid_pay.before_n} bills are still open before payday, {col:unpaid_pay.before_total} in total. The first one is {col:unpaid_pay.bill}, {col:unpaid_pay.amount}, due {col:unpaid_pay.due_date}; after it the joint balance is {col:unpaid_pay.balance_after} ({col:unpaid_pay.check}).',
        'If the balance would go under the floor, move money in, ask to move a due date to after payday, or pay the smaller bills first. These are estimates from your numbers.'], ['Household member', 'Partner'], NOTE),
    DOC('late_doc', 'Late Bill Note', 'Note on a late bill', 'late_list.rank', [
        'Late bill note, {set:household}, dated {today}. Bill: {col:late_list.bill}. Due date: {col:late_list.due_date}. Days late: {col:late_list.days_late}. Amount: {col:late_list.amount}.',
        'Contact: {col:late_list.contact}, {col:late_list.phone}. Payment flag: {col:late_list.flag}. Next step: {col:late_list.next_step}.',
        'Write down what you said and the date you agreed to pay, so the next due date is clear to both partners.'], ['Household member', 'Partner'], NOTE),
    DOC('audit_doc', 'Subscriptions Audit Page', 'Subscriptions audit, ranked by yearly cost', 'subs_rank.rank', [
        'Subscriptions audit of {set:household}, dated {today}. All subscriptions cost {col:subs_rank.all_yearly} a year. The dearest is {col:subs_rank.name} at {col:subs_rank.yearly_cost} a year, {col:subs_rank.share} of the total.',
        '{col:subs_rank.review_n} subscriptions are suggested for review or cancel, worth {col:subs_rank.review_yearly} a year. This one was last used {col:subs_rank.days_since_use} days ago; your decision is {col:subs_rank.decision} and the suggestion is {col:subs_rank.suggested}.',
        'Each subscription is kept, reviewed or cancelled by a household member. The saving is a calculation from your numbers, not a promise.'], ['Household member', 'Partner'], NOTE),
    DOC('cancel_doc', 'Cancel List Page', 'Cancel list with the total saved a year', 'subs.sub_id', [
        'Cancel list of {set:household}, dated {today}. Subscription: {col:subs.name}, owner {col:subs.owner}, decision {col:subs.decision}, suggested {col:subs.suggested}. Renewal date: {col:subs.renewal_date}.',
        'It costs {col:subs.monthly_cost} a month and {col:subs.yearly_cost} a year and was last used on {col:subs.last_used}, {col:subs.days_since_use} days ago.',
        'Subscriptions marked cancel: {col:subs.cancel_n}, worth {col:subs.cancel_yearly} a year. All subscriptions: {col:subs.now_total} a month, against {col:subs.then_total} 6 months ago. The saving is an estimate from your numbers.'], ['Household member', 'Partner'], NOTE),
    DOC('creep_doc', 'Creep Report Page', 'Subscription creep report', 'sub_creep.month', [
        'Subscription creep report of {set:household}, dated {today}. Month: {col:sub_creep.month}. Charges: {col:sub_creep.charges}. The same month 6 months earlier: {col:sub_creep.six_ago}. Change: {col:sub_creep.change} ({col:sub_creep.change_share}).',
        'Average of the 3 months before: {col:sub_creep.avg3}; the month is {col:sub_creep.vs_avg3} against that average.',
        'Subscriptions cost {col:sub_creep.cost_now} a month now against {col:sub_creep.cost_then} 6 months ago: {col:sub_creep.creep_now}. Compare your own months, not a national figure.'], ['Household member', 'Partner'], NOTE),
    DOC('renewals_doc', 'Renewals Page', 'Subscription renewals for the next 60 days', 'renewals.rank', [
        'Renewals page of {set:household}, dated {today}. Next renewal: {col:renewals.name} on {col:renewals.renewal_date}, {col:renewals.days_away} days away, price {col:renewals.price}, decision {col:renewals.decision}.',
        'Decide by {col:renewals.decide_by}, which is {set:cancel_notice_days} days before the renewal. In the next {set:renewal_days} days {col:renewals.renew_n} subscriptions renew for {col:renewals.renew_total} in total.',
        'Read the terms of each plan before you cancel or switch.'], ['Household member', 'Partner'], NOTE),
    DOC('contracts_doc', 'Insurance Contracts Page', 'Insurance and contracts page', 'contracts.contract_id', [
        'Contract page of {set:household}, dated {today}. Contract: {col:contracts.contract}, kind {col:contracts.kind}. Contact: {col:contracts.contact}, {col:contracts.phone}.',
        'Cost: {col:contracts.amount} ({col:contracts.cycle}), {col:contracts.yearly_cost} a year. Renewal date: {col:contracts.renewal_date}, in {col:contracts.days_to_renewal} days. Notice days: {col:contracts.notice_days}.',
        'Review on {col:contracts.review_on}. Review flag: {col:contracts.review_flag}. Check the contract terms and your local rules; ask your adviser if you are unsure.'], ['Household member', 'Contact'], NOTE),
    DOC('review_doc', 'Contract Review Brief', 'Contract review brief', 'contract_review.rank', [
        'Contract review brief of {set:household}, dated {today}. Contract: {col:contract_review.contract} ({col:contract_review.kind}). Cost per year: {col:contract_review.yearly_cost}.',
        'Review on {col:contract_review.review_on}, which is {col:contract_review.days_to_review} days from today; renewal on {col:contract_review.renewal_date}. Action: {col:contract_review.action}.',
        'Contact: {col:contract_review.contact}, {col:contract_review.phone}. Ask for the renewal price, what changed and whether another plan fits you better. Review {set:review_days} days before renewal.'], ['Household member', 'Contact'], NOTE),
    DOC('price_doc', 'Price Rise Letter', 'Price rise request letter', 'price_changes.rank', [
        'Dear {col:price_changes.contact}, this is {set:household}, dated {today}.',
        'The amount of {col:price_changes.bill} rose from {col:price_changes.last_amount} to {col:price_changes.amount}, a change of {col:price_changes.change} ({col:price_changes.change_share}).',
        'We would like to understand the reason for the rise and ask whether a better price or another plan is possible. Please let us know what you can offer.',
        'Thank you for your time. We look forward to your reply.'], ['Household member', 'Contact'], NOTE),
    DOC('dueday_doc', 'Due Date Change Letter', 'Due date change request letter', 'bills.bill_id', [
        'Dear {col:bills.contact}, this is {set:household}, dated {today}.',
        'We pay {col:bills.bill}, {col:bills.amount}, on day {col:bills.due_day} of the month. Our income arrives around {set:next_payday}, so we would like to ask whether the due date can move to day {col:bills.new_day}.',
        'Please tell us what is possible and from which date. We will keep paying on time.', 'Thank you for your help.'], ['Household member', 'Contact'], NOTE),
    DOC('year_doc', 'Bills Summary Year', 'Bills summary for the year', 'bills_month.month', [
        'Bills summary of {set:household}, dated {today}. Month: {col:bills_month.month}. Bills due: {col:bills_month.bills_due}, paid on time: {col:bills_month.paid_on_time}, paid late: {col:bills_month.paid_late}. Total amount: {col:bills_month.total_amount}.',
        'Last 12 months: {col:bills_month.year_bills} bills, {col:bills_month.year_total} in total, {col:bills_month.year_late} paid late.',
        'Keep this page with your records. It shows what the bills cost and how reliably they were paid; it is not tax, legal or credit advice.'], ['Household member', 'Partner'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('weekly_bills_chk', 'Weekly Bills Check', 'bill_due', 'bill_due.due_date', [('Open the Bills Calendar and read the next 14 days', -7), ('Check the joint balance against the Unpaid Before Payday page', -6), ('Mark the bills paid since the last check', -4),
        ('Look at the Late and Missed list', -3), ('Move money in if the balance would go under the cash floor', -2), ('Check the autopay bills are due on a day with money in the account', -1), ('Tell your partner what is due this week', 0)]),
    CHK('due_week_chk', 'Bills Due This Week', 'bill_due', 'bill_due.due_date', [('List the bills due in the next 7 days', -7), ('Check which are manual and which are autopay', -6), ('Pay the manual bills at least 2 days before the due date', -2),
        ('Record the paid date in Bills Due', 0), ('Check the autopay bills left the account', 1)]),
    CHK('late_follow_chk', 'Late Bill Follow-Up', 'bill_due', 'bill_due.due_date', [('Pay the bill if the balance allows it', 1), ('If not, call the contact and say what you can pay and when', 1), ('Write down the date you agreed', 2),
        ('Record the paid date in Bills Due', 3), ('Ask whether a late charge was added', 5), ('Move the due day or set autopay so it does not repeat', 7)]),
    CHK('new_bill_chk', 'New Bill Added', 'bills', 'bills.since', [('Write the bill in Bills with its due day and amount', 0), ('Add its due rows in Bills Due for the next 12 months', 1), ('Choose autopay or manual', 1),
        ('Check the due day against your payday', 2), ('Add the contact in Team with a phone', 3), ('Check the first payment arrived on the right date', 35)]),
    CHK('sub_audit_chk', 'Subscription Audit Routine', 'subs', 'subs.renewal_date', [('Open the Subscription Ranking', -30), ('Check the days since last use of each one', -28), ('Mark Keep, Review or Cancel', -27),
        ('Ask each household member about their own subscriptions', -26), ('Read the creep check against 6 months ago', -25), ('Cancel the ones marked Cancel before their renewal', -4), ('Write the saving in your month-close notes', 0)]),
    CHK('cancel_sub_chk', 'Cancel a Subscription', 'subs', 'subs.renewal_date', [('Check the renewal date and the notice days', -10), ('Save any files or data you want to keep', -8), ('Cancel in the account or ask the provider by message', -4),
        ('Keep the confirmation', -3), ('Tell your bank branch to stop any payment you set up', -3), ('Check no charge appears after the renewal date', 3)]),
    CHK('renewal_chk', 'Yearly Renewal Review', 'contracts', 'contracts.renewal_date', [('Read the current terms and the price', -60), ('Compare with what you pay now and a year ago', -50), ('Ask the contact for a renewal quote', -45),
        ('Ask a second provider for a price', -40), ('Decide whether to renew, change or leave', -20), ('Give notice if you leave', -10), ('Update the Contracts sheet with the new dates', 0)]),
    CHK('insurance_chk', 'Insurance Renewal Steps', 'contracts', 'contracts.renewal_date', [('Check the cover and the amount of each policy', -50), ('Ask the insurance agent for the renewal quote', -45), ('Compare the premium with last year',  -40),
        ('Ask about other options if the premium rose', -35), ('Check the sinking fund holds the yearly premium', -30), ('Confirm the payment date and the account', -10), ('Pay or set autopay', 0)]),
    CHK('utility_chk', 'Utility Contract Review', 'contracts', 'contracts.renewal_date', [('Look at the Utility Seasons Check', -45), ('Compare the plan and price with other offers', -40), ('Ask the utility company to check the reading if the bill looks high', -35),
        ('Ask for a better price or plan', -30), ('Decide and tell the company', -15), ('Check the first bill on the new plan', 30)]),
    CHK('autopay_chk', 'Autopay Review Routine', 'bills', 'bills.since', [('Open the Autopay Map', 0), ('Find the manual bills due just before payday', 1), ('Switch the ones you often pay late to autopay', 2),
        ('Ask to move due days to after payday where autopay would break the floor', 3), ('Check the cash floor after each change', 7), ('Review again after one month', 30)]),
    CHK('month_close_chk', 'Month-End Bills Close', 'bills_month', 'bills_month.month', [('Mark every bill of the month paid, unpaid or late', 28), ('Check the late bills and agree dates', 29), ('Compare the month total with last month', 30),
        ('Look at the utilities against the same month last year', 31), ('Write down price rises to question', 31), ('Check the subscription charges against the list', 32), ('Plan next month: yearly bills due in the next 90 days', 33)]),
    CHK('single_chk', 'Single Adult First Bills Week', 'team', 'team.start', [('List every bill with its due day in Bills', 0), ('Leave partner 2 and the shared rows empty', 0), ('Set your payday and cash floor on the Start sheet', 1), ('Choose autopay for the bills you never skip', 2),
        ('List your subscriptions with the date you last used each', 3), ('Mark which to keep, review or cancel', 4), ('Check the Bills Calendar every Sunday', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('p2_bill_due', 'Partner 2: who pays this bill', 'bill_due', 'bill_due.p2_phone', 'Hello {p2_name}, {bill} of {amount} is due on {due_date}. Who pays it? {home}'),
    M('p2_before_payday', 'Partner 2: bills before payday', 'unpaid_pay', 'unpaid_pay.p2_phone', 'Hello {p2_name}, {before_n} bills are due before payday, {before_total} in total. Can we check the joint account? {home}'),
    M('p2_late_bill', 'Partner 2: a bill is late', 'late_list', 'late_list.p2_phone', 'Hello {p2_name}, {bill} is {days_late} days late. Can you pay it today? {home}'),
    M('p2_unused_subs', 'Partner 2: unused subscriptions', 'unused_subs', 'unused_subs.p2_phone', 'Hello {p2_name}, we found {unused_n} unused subscriptions worth {unused_yearly} a year. Shall we look at them? {home}'),
    M('p2_decide_sub', 'Partner 2: decide before renewal', 'renewals', 'renewals.p2_phone', 'Hello {p2_name}, please decide on {name} before it renews on {renewal_date}. {home}'),
    M('p1_unused_one', 'Partner 1: keep or cancel', 'unused_subs', 'unused_subs.p1_phone', 'Hello {p1_name}, {name} has not been used for {days_since_use} days. Keep or cancel? {home}'),
    M('p1_subs_cost', 'Partner 1: subscriptions cost more', 'subs', 'subs.p1_phone', 'Hello {p1_name}, the subscriptions now cost {now_total} a month, up from {then_total} 6 months ago. {home}'),
    M('p1_insurance', 'Partner 1: review the insurance', 'contracts', 'contracts.p1_phone', 'Hello {p1_name}, {contract} renews on {renewal_date}. Please review it by {review_on}. {home}'),
    M('util_move_due', 'Utility company: move the due date', 'bills', 'bills.phone', 'Hello {contact}, please move the due date of {bill} to day {new_day} of the month. Thank you, {home}'),
    M('util_higher', 'Utility company: bill looks higher', 'bills', 'bills.phone', 'Hello {contact}, our {bill} looks higher than last year: {amount} against {last_amount}. Can we check the reading? {home}'),
    M('util_paid', 'Utility company: payment made', 'bill_due', 'bill_due.phone', 'Hello {contact}, we paid {amount} for {bill} on {paid_on}. Please confirm it was received. {home}'),
    M('util_late', 'Utility company: we are late', 'late_list', 'late_list.phone', 'Hello {contact}, we are {days_late} days late with {bill}. Can we agree a payment date? {home}'),
    M('util_plan', 'Utility company: confirm plan and price', 'contracts', 'contracts.phone', 'Hello {contact}, please confirm the plan and price for {contract} before it renews on {renewal_date}. {home}'),
    M('landlord_paid', 'Landlord: rent paid', 'bill_due', 'bill_due.phone', 'Hello {contact}, the {bill} of {amount} was paid on {paid_on}. Please confirm. {home}'),
    M('landlord_lease', 'Landlord: lease renewal terms', 'contracts', 'contracts.phone', 'Hello {contact}, please send the renewal terms for {contract} before {renewal_date}. {home}'),
    M('landlord_due_day', 'Landlord: change the rent due day', 'bills', 'bills.phone', 'Hello {contact}, we ask to change the due day of {bill} to day {new_day}. What is possible? {home}'),
    M('ins_quote', 'Insurance agent: renewal quote', 'contracts', 'contracts.phone', 'Hello {contact}, please send the renewal quote for {contract} due on {renewal_date}. {home}'),
    M('ins_rose', 'Insurance agent: premium rose', 'bills', 'bills.phone', 'Hello {contact}, our premium for {bill} rose from {last_amount} to {amount}. Can you check other options? {home}'),
    M('ins_confirm', 'Insurance agent: confirm the premium', 'contracts', 'contracts.phone', 'Hello {contact}, please confirm the premium of {amount} for {contract}. {home}'),
    M('ins_review', 'Insurance agent: review the cover', 'contracts', 'contracts.phone', 'Hello {contact}, we want to review the cover for {contract} before {review_on}. {home}'),
    M('bank_setup', 'Bank branch: set up a payment', 'bills', 'bills.bank_phone', 'Hello {bank_contact}, please set up the payment of {bill} on day {due_day}. Thank you, {home}'),
    M('bank_stop', 'Bank branch: stop a payment', 'subs', 'subs.bank_phone', 'Hello {bank_contact}, please stop the payment of {name}, we cancelled it. {home}'),
    M('bank_scheduled', 'Bank branch: payments scheduled', 'bills_cal', 'bills_cal.bank_phone', 'Hello {bank_contact}, {day_n} payments are scheduled on {due_date}. Please confirm. {home}'),
    M('care_paid', 'Childcare provider: payment made', 'bill_due', 'bill_due.phone', 'Hello {contact}, the payment of {amount} for {bill} was made on {paid_on}. Thank you. {home}'),
    M('care_fee', 'Childcare provider: confirm the fee', 'bill_due', 'bill_due.phone', 'Hello {contact}, please confirm the fee for {bill}, {amount}, due {due_date}. {home}'),
    M('school_paid', 'School office: costs paid', 'bill_due', 'bill_due.phone', 'Hello {contact}, the school costs of {amount} for {bill} were paid on {paid_on}. {home}'),
    M('school_list', 'School office: list of costs', 'bills', 'bills.phone', 'Hello {contact}, please send the list of costs for the term for {bill}. Thank you, {home}'),
    M('mechanic_checks', 'Car mechanic: date and price', 'bill_due', 'bill_due.phone', 'Hello {contact}, please confirm the date and price of {bill} on {due_date}, now {amount}. {home}'),
    M('prov_cancel', 'Subscription provider: cancel', 'subs', 'subs.provider_phone', 'Hello, please cancel {name} from {renewal_date} and confirm by message. {home}'),
    M('prov_confirm', 'Subscription provider: confirm cancel', 'subs', 'subs.provider_phone', 'Hello, please confirm that {name} is cancelled and no further charge is made. {home}'),
    M('prov_price', 'Subscription provider: price rose', 'subs', 'subs.provider_phone', 'Hello, the price of {name} rose from {price_6m_ago} to {price}. Is there a cheaper plan? {home}'),
    M('prov_yearly', 'Subscription provider: yearly plan', 'subs', 'subs.provider_phone', 'Hello, please switch {name} to the yearly plan at {yearly_cost}. {home}'),
    M('hm_check_sub', 'Household member: check a subscription', 'subs', 'subs.owner_phone', 'Hello, please check your own subscription {name}, renewal on {renewal_date}. {home}'),
    M('hm_bills_total', 'Household member: bills of the month', 'bills_month', 'bills_month.p2_phone', 'Hello {p2_name}, the bills for {month} total {total_amount}. {home}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def BDm(extra=''): return '{range:bill_due.month},%s%s' % (MS, extra)
D90 = '{range:bill_due.due_date},">="&{today},{range:bill_due.due_date},"<="&({today}+90)'
kpis = [
    KPI('Bills due this month', 'COUNTIFS({range:bill_due.month},%s)' % MS, 'int'),
    KPI('Bills paid this month', 'COUNTIFS({range:bill_due.month},%s,{range:bill_due.status},%s)' % (MS, PAID), 'int'),
    KPI('Bills still unpaid this month', 'COUNTIFS({range:bill_due.month},%s,{range:bill_due.status},"<>"&%s,{range:bill_due.due_id},"<>")' % (MS, PAID), 'int'),
    KPI('Late bills now', 'COUNTIFS({range:bill_due.status},"<>"&%s,{range:bill_due.due_date},"<"&{today},{range:bill_due.due_id},"<>")' % PAID, 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Days late of the oldest late bill', 'SUMPRODUCT(MAX(({range:bill_due.due_id}<>"")*({range:bill_due.status}<>%s)*({range:bill_due.due_date}<{today})*({today}-{range:bill_due.due_date})))' % PAID, 'int'),
    KPI('Bills due in the next 14 days', 'COUNTIFS({range:bill_due.due_date},">="&{today},{range:bill_due.due_date},"<="&({today}+14),{range:bill_due.due_id},"<>")', 'int'),
    KPI('Bills due before the next payday', 'COUNTIFS({range:bill_due.status},"<>"&%s,{range:bill_due.due_date},"<"&{set:next_payday},{range:bill_due.due_id},"<>")' % PAID, 'int'),
    KPI('Total bills due before the next payday', 'SUMIFS({range:bill_due.amount},{range:bill_due.status},"<>"&%s,{range:bill_due.due_date},"<"&{set:next_payday},{range:bill_due.due_id},"<>")' % PAID, 'money'),
    KPI('Autopay share of bills', 'IFERROR(COUNTIFS({range:bills.autopay},%s,{range:bills.bill_id},"<>")/COUNTIFS({range:bills.bill_id},"<>"),0)' % YES, 'pct'),
    KPI('Manual bills due this month', 'COUNTIFS({range:bill_due.month},%s,{range:bill_due.autopay},%s,{range:bill_due.due_id},"<>")' % (MS, NO), 'int'),
    KPI('Bills paid late, last 12 months', 'COUNTIFS({range:bill_due.flag},%s,{range:bill_due.due_date},">="&({today}-365),{range:bill_due.due_date},"<"&{today})' % V('Paid late'), 'int'),
    KPI('Bills total this month', 'SUMIFS({range:bill_due.amount},{range:bill_due.month},%s)' % MS, 'money'),
    KPI('Bills total last month', 'SUMIFS({range:bill_due.amount},{range:bill_due.month},EDATE(%s,-1))' % MS, 'money'),
    KPI('Yearly bills due, next 90 days', 'SUMIFS({range:bills.amount},{range:bills.yearly_next},">="&{today},{range:bills.yearly_next},"<="&({today}+90))', 'money'),
    KPI('Subscriptions active', 'COUNTIFS({range:subs.sub_id},"<>")', 'int'),
    KPI('Subscription cost per month', 'SUM({range:subs.monthly_cost})', 'money'),
    KPI('Subscription cost per year', 'SUM({range:subs.yearly_cost})', 'money'),
    KPI('Subscription cost 6 months ago, month', 'SUM({range:subs.then_monthly})', 'money'),
    KPI('Subscription creep on 6 months ago', 'IFERROR(SUM({range:subs.monthly_cost})/SUM({range:subs.then_monthly})-1,0)', 'pct', alert={"when": ">= {set:creep_alert}", "style": "warn"}),
    KPI('Unused subscriptions, 60 days or more', 'COUNTIFS({range:subs.days_since_use},">="&{set:sub_unused_days})', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Yearly cost of unused subscriptions', 'SUMIFS({range:subs.yearly_cost},{range:subs.days_since_use},">="&{set:sub_unused_days})', 'money'),
    KPI('Subscriptions marked cancel', 'COUNTIFS({range:subs.decision},%s,{range:subs.sub_id},"<>")' % CANCEL, 'int'),
    KPI('Saved a year if cancelled', 'SUMIFS({range:subs.yearly_cost},{range:subs.decision},%s)' % CANCEL, 'money'),
    KPI('Subscriptions renewing in 30 days', 'COUNTIFS({range:subs.renewal_date},">="&{today},{range:subs.renewal_date},"<="&({today}+30))', 'int'),
    KPI('Contracts to review, next 45 days', 'COUNTIFS({range:contracts.renewal_date},">"&{today},{range:contracts.review_on},"<="&({today}+{set:review_days}),{range:contracts.reviewed},%s,{range:contracts.contract_id},"<>")' % NO, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Insurance cost per year', 'SUMIFS({range:contracts.yearly_cost},{range:contracts.kind},%s)' % KIND_INS, 'money'),
    KPI('Insurance share of yearly bills', 'IFERROR(SUMIFS({range:bill_due.amount},{range:bill_due.category},%s,{range:bill_due.month},">="&EDATE(%s,-12),{range:bill_due.month},"<"&%s)/SUMIFS({range:bill_due.amount},{range:bill_due.month},">="&EDATE(%s,-12),{range:bill_due.month},"<"&%s),0)' % (INS, MS, MS, MS, MS), 'pct'),
    KPI('Utilities cost this month', 'SUMIFS({range:bill_due.amount},{range:bill_due.month},%s,{range:bill_due.category},%s)' % (MS, UTIL), 'money'),
    KPI('Utilities cost, last 12 months', 'SUMIFS({range:bill_due.amount},{range:bill_due.category},%s,{range:bill_due.month},">="&EDATE(%s,-12),{range:bill_due.month},"<"&%s)' % (UTIL, MS, MS), 'money'),
    KPI('Bills with price rises, 12 months', 'COUNTIFS({range:bills.change_share},">0")', 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Bills Dashboard", "kpis": kpis,
    "monthly": {"title": "Bills due and subscription charges by month", "date": "bill_due.due_date", "series": [
        {"label": "Bills due", "sum": "bill_due.amount", "date": "bill_due.due_date"}, {"label": "Subscription charges", "sum": "sub_charges.amount", "date": "sub_charges.date"},
        {"label": "Days paid late", "sum": "bill_due.days_paid_late", "date": "bill_due.due_date"}]},
    "breakdowns": [{"title": "Bills by category", "by": "bill_due.category", "value": "bill_due.amount", "agg": "sum"}, {"title": "Bills by status", "by": "bill_due.status", "value": "bill_due.amount", "agg": "sum"},
                   {"title": "Subscription cost by owner", "by": "subs.owner", "value": "subs.monthly_cost", "agg": "sum"}, {"title": "Contracts by kind", "by": "contracts.kind", "value": "contracts.yearly_cost", "agg": "sum"}]}
insights = {"filters": [{"label": "Bill category", "list": "bcat"}, {"label": "Bill status", "list": "bstatus"}, {"label": "Decision", "list": "decision"}],
    "gauges": [
        {"title": "Bills paid on time", "num": AGG('count', 'bill_due', where=[('flag', '=', V('Paid on time'))]), "den": AGG('count', 'bill_due', where=[('status', '=', PAID)])},
        {"title": "Bills on autopay", "num": AGG('count', 'bills', where=[('autopay', '=', YES)]), "den": AGG('count', 'bills')},
        {"title": "Subscriptions used in the last 60 days", "num": AGG('count', 'subs', where=[('days_since_use', '<', '{set:sub_unused_days}')]), "den": AGG('count', 'subs')},
        {"title": "Cost 6 months ago as a share of now", "num": AGG('sum', 'subs', 'subs.then_monthly'), "den": AGG('sum', 'subs', 'subs.monthly_cost')},
        {"title": "Contracts reviewed this cycle", "num": AGG('count', 'contracts', where=[('reviewed', '=', YES)]), "den": AGG('count', 'contracts')},
        {"title": "Bills before payday above the floor", "num": AGG('count', 'unpaid_pay', where=[('before', '=', 1), ('under', '=', 0)]), "den": AGG('count', 'unpaid_pay', where=[('before', '=', 1)])}],
    "charts": [
        CHART('Bills due per month', 'column', 'month', [AGG('count', 'bill_due', date='bill_due.due_date', label='Bills due')]),
        CHART('Bills total per month by status', 'stacked', 'month', [AGG('sum', 'bill_due', 'bill_due.amount', date='bill_due.due_date', where=[('status', '=', PAID)], label='Paid'),
              AGG('sum', 'bill_due', 'bill_due.amount', date='bill_due.due_date', where=[('status', '=', UNPAID)], label='Unpaid'), AGG('sum', 'bill_due', 'bill_due.amount', date='bill_due.due_date', where=[('status', '=', LATE)], label='Late')]),
        CHART('Bills by category', 'bar', 'bill_due.category', [AGG('sum', 'bill_due', 'bill_due.amount', label='Bills')]),
        CHART('Bills by payment account', 'bar', 'bill_due.account', [AGG('sum', 'bill_due', 'bill_due.amount', label='Bills')]),
        CHART('Bills paid on time and late per month', 'stacked', 'month', [AGG('count', 'bill_due', date='bill_due.due_date', where=[('flag', '=', V('Paid on time'))], label='Paid on time'),
              AGG('count', 'bill_due', date='bill_due.due_date', where=[('flag', '=', V('Paid late'))], label='Paid late')]),
        CHART('Autopay and manual bills per month', 'stacked', 'month', [AGG('count', 'bill_due', date='bill_due.due_date', where=[('autopay', '=', YES)], label='Autopay'),
              AGG('count', 'bill_due', date='bill_due.due_date', where=[('autopay', '=', NO)], label='Manual')]),
        CHART('Utilities per month', 'column', 'month', [AGG('sum', 'bill_due', 'bill_due.amount', date='bill_due.due_date', where=[('category', '=', UTIL)], label='Utilities')]),
        CHART('Insurance per month', 'column', 'month', [AGG('sum', 'bill_due', 'bill_due.amount', date='bill_due.due_date', where=[('category', '=', INS)], label='Insurance')]),
        CHART('Yearly bills by due month', 'column', 'month', [AGG('sum', 'bill_due', 'bill_due.amount', date='bill_due.due_date', where=[('cycle', '=', YR)], label='Yearly bills')]),
        CHART('Bills by day of the month', 'bar', 'bill_due.dayband', [AGG('sum', 'bill_due', 'bill_due.amount', label='Bills')]),
        CHART('Days paid late per month', 'column', 'month', [AGG('sum', 'bill_due', 'bill_due.days_paid_late', date='bill_due.due_date', label='Days late')]),
        CHART('Subscription charges per month', 'column', 'month', [AGG('sum', 'sub_charges', 'sub_charges.amount', date='sub_charges.date', label='Charges')]),
        CHART('Subscription cost by owner', 'bar', 'subs.owner', [AGG('sum', 'subs', 'subs.monthly_cost', label='Cost per month')]),
        CHART('Subscription cost by card', 'bar', 'subs.card', [AGG('sum', 'subs', 'subs.monthly_cost', label='Cost per month')]),
        CHART('Subscriptions by decision', 'bar', 'subs.decision', [AGG('count', 'subs', label='Subscriptions')]),
        CHART('Subscription cost by cycle', 'bar', 'subs.cycle', [AGG('sum', 'subs', 'subs.monthly_cost', label='Cost per month')]),
        CHART('Charges against 6 months earlier', 'column', 'month', [AGG('sum', 'sub_creep', 'sub_creep.charges', date='sub_creep.month', label='Charges'), AGG('sum', 'sub_creep', 'sub_creep.six_ago', date='sub_creep.month', label='6 months earlier')]),
        CHART('Subscriptions by days since last use', 'bar', 'subs.use_band', [AGG('count', 'subs', label='Subscriptions')]),
        CHART('Contracts by kind', 'bar', 'contracts.kind', [AGG('count', 'contracts', label='Contracts')]),
        CHART('Contract cost per year by kind', 'bar', 'contracts.kind', [AGG('sum', 'contracts', 'contracts.yearly_cost', label='Cost per year')]),
        CHART('Renewals per month', 'column', 'month', [AGG('count', 'contracts', date='contracts.renewal_date', label='Contract renewals'), AGG('count', 'subs', date='subs.renewal_date', label='Subscription renewals')]),
        CHART('Price change by bill category', 'bar', 'bills.category', [AGG('sum', 'bills', 'bills.change', label='Change on a year ago')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Bills calendar planner", "why": "the bills of the next days in date order with the paid flag, the total and the largest bill, so no due date surprises you", "where": "Bills Calendar Planner"},
    {"name": "Payday cover check", "why": "open bills before payday set against the joint balance and your cash floor, with the first bill that breaks the floor", "where": "Payday Cover Check"},
    {"name": "Late bill chaser", "why": "late bills ranked by days and amount with a clear verdict: pay today, call the contact or fine", "where": "Late Bill Chaser"},
    {"name": "Autopay map and due day mover", "why": "every bill marked autopay or manual and the day of the month that falls after payday to ask for", "where": "Due Day Mover"},
    {"name": "Subscriptions audit", "why": "every subscription ranked by yearly cost with days since use, the keep, review or cancel column and the cost at stake", "where": "Subscriptions Audit"},
    {"name": "Unused subscription finder", "why": "the subscriptions you have not used for the longest time with a cancel, review or keep verdict you can act on", "where": "Unused Subscription Finder"},
    {"name": "Cancel savings calculator", "why": "the saving a year if the marked subscriptions are cancelled, shown as an estimate from your numbers", "where": "Cancel Savings Calculator"},
    {"name": "Subscription creep check", "why": "this month against 6 months ago and against the 3-month average from your own charges, with a creeping or steady verdict", "where": "Subscription Creep Check"},
    {"name": "Contract review alert", "why": "renewals minus your review days, so every insurance, utility and phone contract is reviewed before it renews", "where": "Contract Review Alert"},
    {"name": "Yearly bills to monthly", "why": "every yearly bill turned into a monthly and per-paycheck amount with the months left for the next one", "where": "Yearly Bills to Monthly"}]
competitors = [
    {"what": "budgeting app with a monthly subscription and bank links", "lacks": "charges every month, breaks when a link drops and cannot show cash before payday, unused subscriptions or contract reviews"},
    {"what": "single-purpose bill tracker template", "lacks": "lists due dates but has no autopay check, no late chaser, no subscription audit and no renewal alert"},
    {"what": "free subscription list sheet", "lacks": "adds up the cost but never ranks by yearly cost, flags unused ones or compares with 6 months ago"},
    {"what": "paper bill organiser and calendar", "lacks": "cannot total the bills before payday, check the balance against a cash floor or remind you before a renewal"},
    {"what": "generic household budget sheet", "lacks": "has one line per bill and no due-date history, price-rise finder, insurance calendar or contract review list"}]
guide = [
    'Replace the demo data: open Bills, Subscriptions and Contracts and type your own rows over the sample ones, or delete the sample rows and start with the blank copy. Leave the yellow cells you do not use empty.',
    'Open the Start sheet and type your household name, how you are paid, your next payday and the cash floor of your joint account. These drive every check.',
    'Fill Bills with every bill, its due day, amount and autopay, then add its due dates in Bills Due. The next due date, price change and cost per paycheck fill in by themselves.',
    'Pay-day routine: on each payday mark the bills paid since the last one in Bills Due, open Unpaid Before Payday and Payday Cover Check, and move money in if the balance would go under your floor.',
    'Check Bills Calendar every week for the next 14 days and the Late and Missed list for anything open; use the late bill chaser and the messages for the call or text.',
    'Fill Subscriptions with the price, renewal date, the date you last used each one and the price 6 months ago. Subscription Ranking, Unused Subscriptions and Subscription Creep fill in by themselves.',
    'Mark each subscription Keep, Review or Cancel, then use Cancel Savings Calculator to see the saving a year. It is an estimate from your numbers, not a promise.',
    'Fill Contracts with insurance, utility, phone, rent and loan contracts; Contract Review List and the review alert tell you when to ask for a better price before a renewal.',
    'Month-close routine: mark every bill paid or late, read Bills by Month and the price changes, check the subscription charges, then plan the yearly bills due in the next 90 days.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'A single adult with one income and no children can use every sheet here unchanged: leave partner 2 empty and ignore the shared rows in other parts of this suite.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you and nothing to link or re-connect. It takes typed or pasted data and has no macros; it works in Excel and Google Sheets.',
    'What this is not: not a bank app, not tax, legal, investment or credit advice. Every verdict is an estimate from your numbers; targets are your own, a typical range, check your own numbers.']
listing = {"title": "Household Bills and Subscriptions Tracker Excel Template: Bills Calendar, Due Dates, Subscription Audit, Contract Renewals",
    "headline": "Never miss a bill: calendar, cash before payday, subscriptions and renewals",
    "tags": ["bills tracker", "bill calendar", "subscription audit", "budget planner", "excel template", "due dates", "household budget", "bills due", "contract renewals", "subscription tracker", "family budget", "autopay tracker", "bill organizer"],
    "description": ("Run the bills side of your household money in one Excel workbook. Built for a single adult, a couple or a family who pay bills from a joint account, want to see what is due before the next payday and are tired of subscription apps with bank links that break. "
        "Bills holds every bill with its due day, amount, autopay and contact; Bills Due holds every due date for two years back and one year ahead with its status and the day it was paid. Bills Calendar shows the next bills in date order, and Unpaid Before Payday sets the open bills against your joint balance and your own cash floor.\n\n"
        "Late and Missed ranks the worst late payments. Autopay Map shows which bills are on autopay and which land just before payday. Price Changes ranks the bills that rose against a year ago. "
        "Subscriptions lists every subscription with its price, renewal date and the day you last used it. Subscription Ranking, Unused Subscriptions, Renewals and Subscription Creep turn that list into a decision: keep, review or cancel, with the saving a year as an estimate from your numbers. "
        "Contracts, Insurance Calendar and Contract Review List remind you to review insurance, utility, phone, rent and loan contracts before they renew.\n\n"
        f"{len(tools)} tools answer the weekly questions: will the balance cover the bills before payday, which late bill comes first, which manual bills move to autopay, what to set aside per paycheck, which subscriptions to cancel, whether subscriptions are creeping up and which contract to review next. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to a partner, a landlord, a utility company, an insurance agent, a bank branch, a school office or a subscription provider.\n\n"
        "This is part two of the Household Finance suite. A standard .xlsx workbook with no macros, one flat price and no yearly renewal, with a demo copy full of sample data to explore first. It works in Excel and Google Sheets. It helps you keep track of your bills and does not give tax, legal, investment or credit advice or promise results."),
    "features": ["Bills calendar with the next 14 days", "Open bills set against the joint balance and your floor", "Late bill chaser with a pay or call verdict", "Autopay map and due day mover", "Subscription audit ranked by yearly cost",
                 "Unused subscription finder and cancel saving", "Subscription creep against 6 months ago", "Contract and insurance review alerts", f"{len(tools)} tools for weekly bill decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
lists = base_lists + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p2', slug='household-finance-bills', profession='Household Finance', name='Bills, Subscriptions and Due Dates',
         tagline='Never miss a bill: calendar, cash before payday, subscriptions and renewals', price_usd=29,
         colors={"primary": "#1F5F5B", "accent": "#F2B134"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 2, "of": 8, "focus": "Bills, subscriptions and due dates"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf2.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']), 'tag', len(s['tagline']))
