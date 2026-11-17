"""Household Finance suite - part 4: Debt Payoff Planner."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf4_lists import *
from hf4_tables import *
from hf4_tools import tools
import hf4_data as D

SUITE = 'fx-20261116-household-finance'
NOTE = "Sample wording: adapt it to your own household."
def F(*pairs): return [FV(a, b) for a, b in pairs]
IDCOL = {'debts': 'debt_id', 'debt_payments': 'payment_id', 'extra_plan': 'debt', 'aval_order': 'slot', 'snow_order': 'slot', 'min_only': 'debt', 'due_map': 'debt', 'windfall': 'wfa', 'ratios': 'ratio',
         'extra_test': 'step', 'pay_by_debt': 'debt', 'mins_pay': 'month'}
def LK(t, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, IDCOL[t])

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('debt_sheet', 'Debt Sheet', 'One debt and where it stands', 'debts.debt_id', F(
        ('Debt', 'debts.debt'), ('Kind', 'debts.kind'), ('Owner', 'debts.owner'), ('Balance', 'debts.balance'), ('Yearly rate', 'debts.rate'), ('Minimum payment', 'debts.min_payment'), ('Due day', 'debts.due_day'),
        ('Extra planned a month', 'debts.extra_planned'), ('Interest a month', 'debts.monthly_interest'), ('Minimum against interest', 'debts.covers'), ('Months at the minimum', 'debts.months_min'),
        ('Months in the current plan', 'debts.plan_months'), ('Months by avalanche', 'debts.aval_months'), ('Payoff date by avalanche', 'debts.payoff_date')) + [
        FF('Share of total debt', 'IFERROR(%s/SUM({range:debts.balance}),0)' % LK('debts', 'balance'), 'pct'), FF('Minimum share of take-home', 'IFERROR(%s/(%s),0)' % (LK('debts', 'min_payment'), TH12), 'pct')]),
    FORM('payment_sheet', 'Debt Payment Sheet', 'One payment on a card or loan', 'debt_payments.payment_id', F(
        ('Date', 'debt_payments.date'), ('Debt', 'debt_payments.debt'), ('Kind', 'debt_payments.kind'), ('Minimum', 'debt_payments.minimum'), ('Extra', 'debt_payments.extra'), ('Amount', 'debt_payments.amount'),
        ('Interest', 'debt_payments.interest'), ('Principal', 'debt_payments.principal'), ('Balance after', 'debt_payments.balance_after'), ('Interest share of the payment', 'debt_payments.interest_share')) + [
        FF('Payments recorded on this debt', 'COUNTIFS({range:debt_payments.debt_id},%s)' % LK('debt_payments', 'debt_id'), 'int'),
        FF('Interest recorded on this debt', 'SUMIFS({range:debt_payments.interest},{range:debt_payments.debt_id},%s)' % LK('debt_payments', 'debt_id'), 'money')]),
    FORM('extra_plan_sheet', 'Extra Payment Plan Sheet', 'One debt, extra now and by avalanche', 'extra_plan.debt', F(
        ('Balance', 'extra_plan.balance'), ('Yearly rate', 'extra_plan.rate'), ('Extra now', 'extra_plan.extra_now'), ('Extra by avalanche', 'extra_plan.extra_aval'), ('Move (+) or take away (-)', 'extra_plan.difference'),
        ('Interest in 12 months now', 'extra_plan.int12_now'), ('Interest in 12 months by avalanche', 'extra_plan.int12_aval'), ('Interest lost in a year', 'extra_plan.interest_lost_year'),
        ('Months, current plan', 'extra_plan.months_now'), ('Months, avalanche', 'extra_plan.months_aval'), ('Months, snowball', 'extra_plan.months_snow'), ('Rate order', 'extra_plan.status')) + [
        FF('Share of all the extra now', 'IFERROR(%s/(%s),0)' % (LK('extra_plan', 'extra_now'), EXTRAS), 'pct')]),
    FORM('order_sheet', 'Debt Order Choice Sheet', 'One debt in the avalanche order', 'aval_order.slot', F(
        ('Debt', 'aval_order.debt'), ('Balance', 'aval_order.bal'), ('Yearly rate', 'aval_order.rate'), ('Minimum payment', 'aval_order.mnp'), ('Payment while it gets the extra', 'aval_order.pay'),
        ('Payoff month number', 'aval_order.payoff_month'), ('Payoff date', 'aval_order.payoff_date'), ('Interest to payoff', 'aval_order.interest'), ('Months to debt-free, avalanche', 'aval_order.months_all'),
        ('Total interest, avalanche', 'aval_order.interest_all'), ('Months to debt-free, snowball', 'aval_order.other_months'), ('Total interest, snowball', 'aval_order.other_interest'),
        ('Interest less than snowball', 'aval_order.saved_interest')) + [FF('Share of the debt', 'IFERROR(%s/SUM({range:aval_order.bal}),0)' % LK('aval_order', 'bal'), 'pct')]),
    FORM('min_change_sheet', 'Minimum Payment Change Sheet', 'One debt at its minimum', 'min_only.debt', F(
        ('Yearly rate', 'min_only.rate'), ('Minimum payment', 'min_only.min_payment'), ('Balance', 'min_only.balance'), ('Interest a month', 'min_only.monthly_interest'), ('Months at the minimum', 'min_only.months'),
        ('Payoff date at the minimum', 'min_only.payoff_date'), ('Interest at the minimum', 'min_only.interest'), ('Minimum against interest', 'min_only.covers'), ('Months in the current plan', 'min_only.plan_months')) + [
        FF('Payment to finish in 36 months', 'IFERROR(-PMT(%s/12,36,%s),0)' % (LK('min_only', 'rate'), LK('min_only', 'balance')), 'money'),
        FF('Interest share of the minimum', 'IFERROR(%s/%s,0)' % (LK('min_only', 'monthly_interest'), LK('min_only', 'min_payment')), 'pct')]),
    FORM('new_debt_sheet', 'New Debt Sheet', 'A new card or loan and what it adds', 'debts.debt_id', F(
        ('Debt', 'debts.debt'), ('Kind', 'debts.kind'), ('Balance', 'debts.balance'), ('Yearly rate', 'debts.rate'), ('Minimum payment', 'debts.min_payment'), ('Interest a month', 'debts.monthly_interest'),
        ('Months at the minimum', 'debts.months_min'), ('Order by avalanche', 'debts.aval_rank'), ('Order by snowball', 'debts.snow_rank')) + [
        FF('Total debt with it', 'SUM({range:debts.balance})', 'money'), FF('Share of total debt', 'IFERROR(%s/SUM({range:debts.balance}),0)' % LK('debts', 'balance'), 'pct'),
        FF('Minimum share of take-home', 'IFERROR(%s/(%s),0)' % (LK('debts', 'min_payment'), TH12), 'pct'), FF('Debt payments over gross, all debts', 'IFERROR(%s/(%s),0)' % (PAYTOT, GR12), 'pct')]),
    FORM('paid_off_sheet', 'Debt Paid Off Sheet', 'One debt: what it cost and when it was paid', 'debts.debt_id', F(
        ('Debt', 'debts.debt'), ('Kind', 'debts.kind'), ('Original amount', 'debts.original_amount'), ('Opened', 'debts.opened'), ('Balance now', 'debts.balance'), ('Status', 'debts.status')) + [
        FF('Payments recorded', 'COUNTIFS({range:debt_payments.debt_id},{pick})', 'int'), FF('Interest recorded', 'SUMIFS({range:debt_payments.interest},{range:debt_payments.debt_id},{pick})', 'money'),
        FF('Principal recorded', 'SUMIFS({range:debt_payments.principal},{range:debt_payments.debt_id},{pick})', 'money'),
        FF('Last payment', 'IF(SUMPRODUCT(MAX(({range:debt_payments.debt_id}={pick})*({range:debt_payments.date})))=0,"",SUMPRODUCT(MAX(({range:debt_payments.debt_id}={pick})*({range:debt_payments.date}))))', 'date')]),
    FORM('rate_sheet', 'Rate Change Sheet', 'One debt: what a higher or lower rate would cost', 'debts.debt_id', F(
        ('Debt', 'debts.debt'), ('Balance', 'debts.balance'), ('Yearly rate', 'debts.rate'), ('Interest a month', 'debts.monthly_interest'), ('Minimum payment', 'debts.min_payment'), ('Months at the minimum', 'debts.months_min')) + [
        FF('Interest a month at 1 point higher', '%s*(%s+0.01)/12' % (LK('debts', 'balance'), LK('debts', 'rate')), 'money'), FF('Interest a month at 2 points higher', '%s*(%s+0.02)/12' % (LK('debts', 'balance'), LK('debts', 'rate')), 'money'),
        FF('Extra interest a year per point', '%s*0.01' % LK('debts', 'balance'), 'money'), FF('Interest a month at 2 points lower', 'MAX(0,%s*(%s-0.02)/12)' % (LK('debts', 'balance'), LK('debts', 'rate')), 'money')]),
    FORM('hardship_sheet', 'Hardship Request Sheet', 'One debt and the facts to give your lender', 'debts.debt_id', F(
        ('Debt', 'debts.debt'), ('Owner', 'debts.owner'), ('Balance', 'debts.balance'), ('Yearly rate', 'debts.rate'), ('Minimum payment', 'debts.min_payment'), ('Due day', 'debts.due_day'),
        ('Months at the minimum', 'debts.months_min')) + [
        FF('Half of the minimum payment', '%s/2' % LK('debts', 'min_payment'), 'money'), FF('All minimum payments each month', MINS, 'money'), FF('Minimum payments over take-home', 'IFERROR(%s/(%s),0)' % (MINS, TH12), 'pct'),
        FF('Take-home a month, last 12 months', TH12, 'money')]),
    FORM('due_day_sheet', 'Due Day Change Sheet', 'One debt: the due date against payday', 'due_map.debt', F(
        ('Due day', 'due_map.due_day'), ('Next due date', 'due_map.next_due'), ('Days to due', 'due_map.days_to_due'), ('Payday before', 'due_map.prev_payday'), ('Payday after', 'due_map.next_payday'),
        ('Days before payday', 'due_map.days_before'), ('Due date against payday', 'due_map.flag'), ('Pay on', 'due_map.pay_on'), ('Suggested due day', 'due_map.new_day')) + [
        FF('Days between paydays in Settings', '{set:pay_gap_days}', 'int'), FF('Tight margin in Settings, days', '{set:margin_days}', 'int')]),
    FORM('windfall_sheet', 'Windfall to Debt Sheet', 'One windfall and what it does to the plan', 'windfall.wfa', F(
        ('Windfall amount', 'windfall.wfa'), ('First debt it goes to', 'windfall.target'), ('Applied to debts', 'windfall.applied'), ('New debt-free date', 'windfall.debt_free'), ('Months to debt-free', 'windfall.months'),
        ('Months saved', 'windfall.months_saved'), ('Total interest', 'windfall.interest'), ('Interest saved', 'windfall.interest_saved'), ('Left after all debts', 'windfall.left_over')) + [
        FF('Debt-free date without it', 'INDEX({range:aval_order.free_date},1)', 'date'), FF('Interest saved per 100 of the windfall', 'IFERROR(%s/%s*100,0)' % (LK('windfall', 'interest_saved'), LK('windfall', 'wfa')), 'money')]),
    FORM('review_sheet', 'Debt Review Sheet', 'One debt ratio against its typical range', 'ratios.ratio', F(
        ('Value', 'ratios.value'), ('Typical range', 'ratios.range'), ('Above (+) or below (-) the range', 'ratios.diff'), ('Status', 'ratios.flag')) + [
        FF('Ratios within their range', 'COUNTIFS({range:ratios.in_range},1,{range:ratios.has_range},1)', 'int'), FF('Ratios that have a range', 'SUM({range:ratios.has_range})', 'int'),
        FF('Total debt', BAL(), 'money'), FF('Total monthly payments', PAYTOT, 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('overview_doc', 'Debt Overview Page', 'Debt overview, one debt', 'debts.debt_id', [
        'Debt overview of {set:household}, dated {today}. Debt: {col:debts.debt} ({col:debts.kind}), owner {col:debts.owner}.',
        'Balance {col:debts.balance}, yearly rate {col:debts.rate}, minimum payment {col:debts.min_payment}, due on day {col:debts.due_day}, extra planned {col:debts.extra_planned} a month. Interest each month: {col:debts.monthly_interest}.',
        'At the minimum this debt takes {col:debts.months_min} months. In the avalanche plan it is cleared in month {col:debts.aval_months}, on {col:debts.payoff_date}.',
        'All debts together: {col:debts.total_debt}. Estimates from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('snowball_doc', 'Snowball Plan Page', 'Snowball plan, smallest balance first', 'snow_order.slot', [
        'Snowball plan of {set:household}, dated {today}. Order {col:snow_order.slot}: {col:snow_order.debt}.',
        'Balance {col:snow_order.bal}, yearly rate {col:snow_order.rate}, minimum {col:snow_order.mnp}. While it gets the extra payment it is paid {col:snow_order.pay} a month. Cleared in month {col:snow_order.payoff_month} on {col:snow_order.payoff_date}; interest to payoff {col:snow_order.interest}.',
        'The whole plan pays {col:snow_order.budget} a month and ends on {col:snow_order.free_date}, {col:snow_order.months_all} months from now, with {col:snow_order.interest_all} of interest in total.',
        'When a debt is cleared its payment rolls to the next one. An estimate from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('avalanche_doc', 'Avalanche Plan Page', 'Avalanche plan, highest rate first', 'aval_order.slot', [
        'Avalanche plan of {set:household}, dated {today}. Order {col:aval_order.slot}: {col:aval_order.debt}.',
        'Balance {col:aval_order.bal}, yearly rate {col:aval_order.rate}, minimum {col:aval_order.mnp}. While it gets the extra payment it is paid {col:aval_order.pay} a month. Cleared in month {col:aval_order.payoff_month} on {col:aval_order.payoff_date}; interest to payoff {col:aval_order.interest}.',
        'The whole plan pays {col:aval_order.budget} a month and ends on {col:aval_order.free_date}, {col:aval_order.months_all} months from now, with {col:aval_order.interest_all} of interest in total.',
        'When a debt is cleared its payment rolls to the next one. An estimate from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('compare_doc', 'Snowball Against Avalanche Page', 'Snowball against avalanche comparison', 'aval_order.slot', [
        'Comparison of {set:household}, dated {today}. Same payment each month, two orders.',
        'Avalanche (highest rate first): debt-free in {col:aval_order.months_all} months on {col:aval_order.free_date}, interest {col:aval_order.interest_all}.',
        'Snowball (smallest balance first): debt-free in {col:aval_order.other_months} months, interest {col:aval_order.other_interest}. Avalanche costs {col:aval_order.saved_interest} less interest and {col:aval_order.saved_months} fewer months.',
        'A plan you keep is worth more than a perfect plan you drop. Estimates from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('extra_doc', 'Extra Payment Plan Page', 'Extra payment plan, one debt', 'extra_plan.debt', [
        'Extra payment plan of {set:household}, dated {today}. Debt: {col:extra_plan.debt}, yearly rate {col:extra_plan.rate} ({col:extra_plan.status}).',
        'Balance {col:extra_plan.balance}. Extra now {col:extra_plan.extra_now} a month; if all the extra went to the highest rate this debt would get {col:extra_plan.extra_aval}, a change of {col:extra_plan.difference}.',
        'Interest over the next 12 months: {col:extra_plan.int12_now} now against {col:extra_plan.int12_aval} by avalanche. Interest lost in a year by the current split: {col:extra_plan.interest_lost_year}.',
        'Months to clear it: {col:extra_plan.months_now} now, {col:extra_plan.months_aval} by avalanche. An estimate from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('minimums_doc', 'Minimum Payments Report', 'Minimum payments report, one month', 'mins_pay.month', [
        'Minimum payments report of {set:household}, dated {today}. Month: {col:mins_pay.month}.',
        'Minimum payments made: {col:mins_pay.minimums}. Take-home pay received: {col:mins_pay.take_home}. Share of take-home: {col:mins_pay.share}.',
        'Against your own limit in Settings this month is: {col:mins_pay.flag}.',
        'The limit is your own number: a typical range, check your own numbers. Not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('ratios_doc', 'Debt Ratios Page', 'Debt ratios, one ratio', 'ratios.ratio', [
        'Debt ratios of {set:household}, dated {today}. Ratio: {col:ratios.ratio}.',
        'Value {col:ratios.value}. Typical range {col:ratios.range}. Against the range: {col:ratios.diff}. Status: {col:ratios.flag}.',
        'Ratios within their range: see the Debt ratios sheet. Every range is a typical range, check your own numbers.',
        'These ratios say nothing about what you can borrow. Ask your adviser.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('calendar_doc', 'Payoff Calendar Page', 'Payoff calendar, one debt', 'due_map.debt', [
        'Payoff calendar of {set:household}, dated {today}. Debt: {col:due_map.debt}.',
        'Due on day {col:due_map.due_day}; next due date {col:due_map.next_due}, {col:due_map.days_to_due} days from today. Payday before: {col:due_map.prev_payday}; payday after: {col:due_map.next_payday}; {col:due_map.days_before} days before payday.',
        'Due date against payday: {col:due_map.flag}. Pay on {col:due_map.pay_on}.',
        'If you ask your lender to move the due date, a day soon after payday is day {col:due_map.new_day}. Ask what is possible.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('free_doc', 'Debt-free Date Note', 'Debt-free date at one extra payment step', 'extra_test.step', [
        'Debt-free note of {set:household}, dated {today}. Step tested: {col:extra_test.step}, an extra payment of {col:extra_test.xtr} a month.',
        'Debt-free on {col:extra_test.debt_free}, {col:extra_test.months} months from now, with {col:extra_test.interest} of interest in total.',
        'Against paying only the minimums this saves {col:extra_test.months_saved} months and {col:extra_test.interest_saved} of interest.',
        'These are estimates from your numbers, not promises.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('hardship_doc', 'Hardship Request Letter', 'Request for help with a payment', 'debts.debt_id', [
        'Date: {today}. To: {col:debts.bank_name}, your lender. From: {set:household}.',
        'We write about {col:debts.debt}. The balance is {col:debts.balance} and the minimum payment is {col:debts.min_payment}, due on day {col:debts.due_day}.',
        'We face a temporary gap in income. Please tell us what options exist, for example a lower or paused payment for a few months or a payment plan, and what each would mean for the balance.',
        'Thank you for your help. We are glad to talk by phone.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('dueletter_doc', 'Due Date Change Letter', 'Request to move a due date', 'due_map.debt', [
        'Date: {today}. To: {col:due_map.bank_name}, your lender. From: {set:household}.',
        'We write about {col:due_map.debt}, now due on day {col:due_map.due_day}. The next due date is {col:due_map.next_due}, {col:due_map.days_before} days before our payday.',
        'Please tell us whether the due date can move to around day {col:due_map.new_day} of each month, and whether any fee applies.',
        'Thank you for your help.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('year_doc', 'Year Debt Summary', 'Year debt summary, one debt', 'pay_by_debt.debt', [
        'Debt summary of {set:household} for the last 12 complete months, dated {today}. Debt: {col:pay_by_debt.debt}.',
        'Paid {col:pay_by_debt.paid12} in {col:pay_by_debt.count12} payments: interest {col:pay_by_debt.interest12}, principal {col:pay_by_debt.principal12}, of which extra {col:pay_by_debt.extra12}.',
        'Balance a year ago {col:pay_by_debt.balance_ago}, balance now {col:pay_by_debt.balance_now}, change {col:pay_by_debt.change}. Interest was {col:pay_by_debt.interest_share} of what was paid.',
        'Ask your adviser how to record interest paid. This page says nothing about what can be claimed.'], ['Partner 1', 'Partner 2'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('monthly_chk', 'Monthly Debt Payments Steps', 'debt_payments', 'debt_payments.date', [('Check the Due days map for tight dates', -7), ('Move the money for the minimums into the paying account', -3), ('Pay every minimum', 0), ('Type each payment in Debt payments', 0), ('Update each balance in Debts', 1), ('Read the Minimum Payments Check', 3)]),
    CHK('extra_chk', 'Extra Payment Day Steps', 'debt_payments', 'debt_payments.date', [('Look at the Extra payment plan', -3), ('Check the extra goes to the highest rate', -2), ('Pay the extra on the right debt', 0), ('Record it in the Extra column', 0), ('Run the Extra Payment Test', 7)]),
    CHK('choose_chk', 'Snowball or Avalanche Steps', 'interest_month', 'interest_month.month', [('Read the Snowball Against Avalanche tool', 28), ('Talk it through with your partner', 29), ('Choose the order in Settings', 30), ('Move the extra payment to the first debt', 31), ('Print the plan page', 32)]),
    CHK('balances_chk', 'Update Balances Steps', 'history', 'history.month', [('Get each statement balance', 28), ('Type the balances in Debts', 29), ('Add the month to Net worth', 30), ('Read the Balance Trend tool', 31)]),
    CHK('celebrate_chk', 'Debt Payoff Celebration Steps', 'debt_payments', 'debt_payments.date', [('Ask for the final payment amount', -7), ('Make the final payment', 0), ('Ask for written confirmation of a zero balance', 3), ('Set the balance to zero in Debts', 4), ('Move the payment to the next debt', 7), ('Mark the day with the household', 10)]),
    CHK('newdebt_chk', 'New Card or Loan Steps', 'debts', 'debts.opened', [('Type the debt in Debts', 0), ('Set the due day against your payday', 1), ('Check the Debt Ratios', 2), ('Check the plan order', 3), ('Add the account in Accounts', 7)]),
    CHK('hardship_chk', 'Hardship Request Steps', 'debt_payments', 'debt_payments.date', [('Print the Hardship Request Sheet', 0), ('List the facts: balance, minimum, due day', 0), ('Phone or write to the lender', 1), ('Note what options are offered', 2), ('Decide with your partner', 5), ('Update the minimum in Debts if it changes', 7)]),
    CHK('dueday_chk', 'Payment Due Day Change Steps', 'debt_payments', 'debt_payments.date', [('Read the Due days map', 0), ('Pick the day after payday', 0), ('Ask the lender for the new day', 1), ('Get the answer in writing', 7), ('Update the due day in Debts', 8)]),
    CHK('quarterly_chk', 'Quarterly Debt Review Steps', 'interest_month', 'interest_month.month', [('Read the Balance History', 30), ('Read the Interest Paid by month', 31), ('Check the Debt Ratios', 32), ('Check the extra payment against the plan', 33), ('Write down one change', 34)]),
    CHK('windfall_chk', 'Windfall to Debt Steps', 'income', 'income.date', [('Run the Windfall to Debt tool', 0), ('Check the emergency fund with Debt or Savings Balance', 1), ('Agree the split with your partner', 2), ('Make the payment to the first debt', 3), ('Update the balance in Debts', 4)]),
    CHK('ratios_chk', 'Debt Ratios Review Steps', 'mins_pay', 'mins_pay.month', [('Update income and balances', 28), ('Read each ratio on the Debt ratios sheet', 29), ('Note any ratio above its range', 30), ('Run the Minimum Payments Check', 31)]),
    CHK('single_chk', 'Single Adult Debt Plan Steps', 'debts', 'debts.opened', [('Type your debts in Debts and clear the demo rows', 0), ('Leave Partner 2 and the joint account empty', 0), ('Set the extra payment in Settings', 1), ('Read the Avalanche Payoff tool', 2), ('Add your payments as you make them', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, ph, text): return MSG(k, moment, table, '%s.%s' % (table, ph), text)
messages = [
    M('p2_top', 'Partner 2: highest rate gets less extra', 'extra_plan', 'p2_phone', 'Hello {partner2}, {debt} has the highest rate at {rate} and gets {extra_now} extra a month. Shall we move {difference} to it? {household}'),
    M('p2_save', 'Partner 2: moving the extra saves', 'extra_plan', 'p2_phone', 'Hello {partner2}, moving {move_total} a month to the highest-rate debt would save about {lost_total} in a year, our estimate. {household}'),
    M('p2_free', 'Partner 2: the debt-free date', 'aval_order', 'p2_phone', 'Hello {partner2}, at this plan we are debt-free on {free_date}, {months_all} months from now, an estimate. {household}'),
    M('p2_extra', 'Partner 2: this month extra is paid', 'interest_month', 'p2_phone', 'Hello {partner2}, the extra payment of {extra_paid} for {month} is made. {household}'),
    M('p2_mins', 'Partner 2: minimums share of take-home', 'mins_pay', 'p2_phone', 'Hello {partner2}, the minimum payments in {month} were {minimums}, {share} of take-home. {household}'),
    M('p2_windfall', 'Partner 2: a windfall for the debts', 'windfall', 'p2_phone', 'Hello {partner2}, the windfall of {wfa} could go to {target} and save about {interest_saved} of interest, an estimate. What do you think? {household}'),
    M('p2_ratio', 'Partner 2: a debt ratio', 'ratios', 'p2_phone', 'Hello {partner2}, {ratio} is {value} against a typical range of {range}, check our own numbers. {household}'),
    M('p1_card', 'Partner 1: a debt is paid down', 'debts', 'p1_phone', 'Hello {partner1}, {debt} is paid down to {balance}, {aval_months} months to go at our plan, an estimate. {household}'),
    M('p1_interest', 'Partner 1: the interest paid in a month', 'interest_month', 'p1_phone', 'Hello {partner1}, the interest we paid in {month} was {interest}. {household}'),
    M('p1_calendar', 'Partner 1: the next due date', 'due_map', 'p1_phone', 'Hello {partner1}, {debt} is due on {next_due}. Please pay it on {pay_on}. {household}'),
    M('p1_choose', 'Partner 1: snowball or avalanche', 'aval_order', 'p1_phone', 'Hello {partner1}, shall we choose snowball or avalanche? Avalanche costs {saved_interest} less interest in our numbers. {household}'),
    M('hm_total', 'Household member: total debt', 'history', 'gp_phone', 'Hello {gp_name}, our total debt is {total_debt}, a change of {change} on last month. {household}'),
    M('hm_due', 'Household member: a payment date', 'due_map', 'gp_phone', 'Hello {gp_name}, the payment on {debt} is due on {next_due}. {household}'),
    M('bk_confirm', 'Bank branch: confirm balance and rate', 'debts', 'bank_phone', 'Hello {bank_name}, please confirm the balance and the rate of {debt} on {asof}. {household}'),
    M('bk_due', 'Bank branch: move the due date', 'debts', 'bank_phone', 'Hello {bank_name}, we ask to move the due date of {debt} to day {new_day}. Is that possible? {household}'),
    M('bk_extra', 'Bank branch: an extra payment', 'debts', 'bank_phone', 'Hello {bank_name}, we want to pay {extra_planned} extra on {debt} each month. Please confirm it reduces the balance. {household}'),
    M('bk_payoff', 'Bank branch: the payoff amount', 'debts', 'bank_phone', 'Hello {bank_name}, please send the payoff amount for {debt} on {asof}. {household}'),
    M('bk_rate', 'Bank branch: a rate review', 'debts', 'bank_phone', 'Hello {bank_name}, we ask whether the rate of {debt}, now {rate}, can be reviewed. {household}'),
    M('bk_final', 'Bank branch: the final payment', 'debts', 'bank_phone', 'Hello {bank_name}, we want to pay off {debt}. Please confirm the final amount and date. {household}'),
    M('bk_closed', 'Bank branch: confirm it is closed', 'debts', 'bank_phone', 'Hello {bank_name}, please confirm that {debt} is closed and the balance is zero. {household}'),
    M('bk_hardship', 'Bank branch: a temporary income gap', 'debts', 'bank_phone', 'Hello {bank_name}, we face a temporary income gap. What hardship options exist for {debt}? {household}'),
    M('bk_pause', 'Bank branch: pause or lower a payment', 'debts', 'bank_phone', 'Hello {bank_name}, we ask to pause or lower the payment on {debt} for a few months. What is possible? {household}'),
    M('bk_plan', 'Bank branch: a payment plan', 'debts', 'bank_phone', 'Hello {bank_name}, we ask for a payment plan for {debt}, balance {balance}. What can you offer? {household}'),
    M('bk_statement', 'Bank branch: the statement', 'debts', 'bank_phone', 'Hello {bank_name}, please send the latest statement for {debt}. {household}'),
    M('bk_check', 'Bank branch: check the interest charged', 'debts', 'bank_phone', 'Hello {bank_name}, please check the interest of about {monthly_interest} charged on {debt} this month. {household}'),
    M('bk_received', 'Bank branch: the extra was received', 'debt_payments', 'bank_phone', 'Hello {bank_name}, please confirm the extra payment of {extra} on {debt} made on {date} was received. {household}'),
    M('bk_paid', 'Bank branch: a payment was made', 'debt_payments', 'bank_phone', 'Hello {bank_name}, our payment of {amount} on {debt} was made on {date}. Please confirm. {household}'),
    M('bk_min', 'Bank branch: the minimum payment', 'debts', 'bank_phone', 'Hello {bank_name}, please confirm the minimum payment for {debt}, now {min_payment}, from next month. {household}'),
    M('bk_end', 'Bank branch: the loan end date', 'debts', 'bank_phone', 'Hello {bank_name}, please send the end date and the remaining balance of {debt}. {household}'),
    M('bk_late', 'Bank branch: a payment a few days late', 'debts', 'bank_phone', 'Hello {bank_name}, we will pay {min_payment} on {debt} a few days after the due date. Please tell us whether a late fee applies. {household}'),
    M('pr_split', 'Payroll office: a separate debt payment', 'min_only', 'payroll_phone', 'Hello {payroll_name}, can part of our pay be sent to a separate account for debt payments? Please tell us what is possible. {household}'),
    M('tx_interest', 'Tax preparer: how to record interest', 'pay_by_debt', 'tax_phone', 'Hello {tax_name}, please tell us how to record the {interest12} of interest paid on {debt} in the last 12 months. {household}'),
    M('in_loan', 'Insurance agent: a loan payoff', 'min_only', 'ins_phone', 'Hello {ins_name}, please confirm that paying off {debt} does not change our cover. {household}'),
    M('gp_car', 'Grandparent: the payments left', 'extra_plan', 'gp_phone', 'Hello {gp_name}, thank you for your help. {debt} has {months_aval} payments left at our plan. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def DBR(c): return DB(c)
HIR = lambda c: R('history', c)
KPLUS = lambda c, n: 'SUMIFS(%s,%s,EDATE(%s,-%s))' % (HIR(c), HIR('month'), MS, n)
TOPEX = 'IFERROR(INDEX(%s,MATCH(1,%s,0)),0)' % (DB('extra_planned'), DB('aval_rank'))
AVR = lambda c: R('aval_order', c)
SNR = lambda c: R('snow_order', c)
kpis = [
    KPI('Total debt now', 'SUM(%s)' % DB('balance'), 'money'), KPI('Total debt 3 months ago', KPLUS('total_debt', 3), 'money'), KPI('Total debt a year ago', KPLUS('total_debt', 12), 'money'),
    KPI('Debt paid down, last 12 months', '%s-SUM(%s)' % (KPLUS('total_debt', 12), DB('balance')), 'money'), KPI('Card balances total', 'SUMIFS(%s,%s,%s)' % (DB('balance'), DB('kind'), CARD), 'money'),
    KPI('Instalment loan balances', 'SUMIFS(%s,%s,%s)' % (DB('balance'), DB('kind'), LOAN_K), 'money'), KPI('Largest single balance', 'MAX(%s)' % DB('balance'), 'money'),
    KPI('Highest rate', 'SUMPRODUCT(MAX((%s>0)*%s))' % (DB('balance'), DB('rate')), 'pct'), KPI('Average rate weighted by balance', 'SUMPRODUCT(%s,%s)/SUM(%s)' % (DB('balance'), DB('rate'), DB('balance')), 'pct'),
    KPI('Interest charged per month', 'SUM(%s)' % DB('monthly_interest'), 'money'),
    KPI('Interest paid, last 12 months', 'SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)' % (R('interest_month', 'interest'), R('interest_month', 'month'), MS, R('interest_month', 'month'), MS), 'money'),
    KPI('Monthly minimum payments', MINS, 'money'), KPI('Monthly extra payments planned', EXTRAS, 'money'), KPI('Total monthly debt payments', PAYTOT, 'money'),
    KPI('Minimums share of take-home', '%s/(%s)' % (MINS, TH12), 'pct'), KPI('Debt payments over gross income', '%s/(%s)' % (PAYTOT, GR12), 'pct'), KPI('Consumer debt over take-home', '%s/(%s)' % (CARDPAY, TH12), 'pct'),
    KPI('Cards with extra payment', 'COUNTIFS(%s,%s,%s,">0",%s,">0")' % (DB('kind'), CARD, DB('extra_planned'), DB('balance')), 'int'), KPI('Extra on the highest-rate debt', TOPEX, 'money'),
    KPI('Extra on lower-rate debts', '%s-%s' % (EXTRAS, TOPEX), 'money'), KPI('Interest lost a year by current order', 'SUM(%s)' % R('extra_plan', 'interest_lost_year'), 'money'),
    KPI('Debt-free date at minimums', 'IF(MAX(%s)>=999,"",EOMONTH(%s,MAX(%s)))' % (DB('months_min'), MS, DB('months_min')), 'date'),
    KPI('Debt-free date at the current plan', 'IF(MAX(%s)>=999,"",EOMONTH(%s,MAX(%s)))' % (DB('plan_months'), MS, DB('plan_months')), 'date'),
    KPI('Debt-free date by avalanche', 'INDEX(%s,1)' % AVR('free_date'), 'date'), KPI('Debt-free date by snowball', 'INDEX(%s,1)' % SNR('free_date'), 'date'),
    KPI('Months saved, avalanche vs current plan', 'MAX(%s)-INDEX(%s,1)' % (DB('plan_months'), AVR('months_all')), 'int'),
    KPI('Interest saved, avalanche vs snowball', 'INDEX(%s,1)-INDEX(%s,1)' % (SNR('interest_all'), AVR('interest_all')), 'money'),
    KPI('Debts that clear in the next 24 months', 'COUNTIFS(%s,">0",%s,"<=24")' % (AVR('payoff_month'), AVR('payoff_month')), 'int'),
    KPI('Minimums that do not cover interest', 'COUNTIFS(%s,%s)' % (DB('covers'), st('Below interest')), 'int'),
    KPI('Payments made, last 30 days', 'COUNTIFS(%s,">="&({today}-30),%s,"<="&{today})' % (R('debt_payments', 'date'), R('debt_payments', 'date')), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Debt Payoff Dashboard", "kpis": kpis,
    "monthly": {"title": "Payments by month: minimum, extra and interest", "date": "debt_payments.date", "series": [
        {"label": "Minimum", "sum": "debt_payments.minimum", "date": "debt_payments.date"}, {"label": "Extra", "sum": "debt_payments.extra", "date": "debt_payments.date"},
        {"label": "Interest", "sum": "debt_payments.interest", "date": "debt_payments.date"}]},
    "breakdowns": [{"title": "Interest paid by debt", "by": "debt_payments.debt_id", "value": "debt_payments.interest", "agg": "sum"}, {"title": "Amount paid by debt", "by": "debt_payments.debt_id", "value": "debt_payments.amount", "agg": "sum"},
                   {"title": "Take-home by source", "by": "income.source", "value": "income.net", "agg": "sum"}]}

def AM(t, c, date=None, label=None, where=None, agg='sum'): return AGG(agg, t, '%s.%s' % (t, c), date=('%s.%s' % (t, date)) if date else None, where=where, label=label)
insights = {"filters": [{"label": "Person", "list": "person"}, {"label": "Debt kind", "list": "dkind"}],
    "gauges": [
        {"title": "Debt paid down against a year ago", "num": AM('pay_by_debt', 'principal12'), "den": AM('history', 'total_debt', where=[('ago12', '=', 1)])},
        {"title": "Months with minimums within your limit", "num": AGG('count', 'mins_pay', where=[('ok', '=', 1)]), "den": AGG('count', 'mins_pay')},
        {"title": "Debt ratios within the typical range", "num": AGG('count', 'ratios', where=[('in_range', '=', 1)]), "den": AGG('count', 'ratios', where=[('has_range', '=', 1)])},
        {"title": "Extra payment on the highest rate", "num": AM('extra_plan', 'extra_now', where=[('top', '=', 1)]), "den": AM('extra_plan', 'extra_now')},
        {"title": "Debts paid on time", "num": AGG('count', 'debt_payments', where=[('ontime', '=', 1)]), "den": AGG('count', 'debt_payments')},
        {"title": "Months at or above the planned extra", "num": AGG('count', 'interest_month', where=[('extra_met', '=', 1)]), "den": AGG('count', 'interest_month')}],
    "charts": [
        CHART('Total debt per month', 'column', 'month', [AM('history', 'total_debt', 'month', 'Total debt')]),
        CHART('Debt by type per month', 'stacked', 'month', [AM('history', 'cards', 'month', 'Card balances'), AM('history', 'loans', 'month', 'Loan balances')]),
        CHART('Balance by debt', 'bar', 'extra_plan.debt', [AM('extra_plan', 'balance', label='Balance')]),
        CHART('Interest each month by debt', 'bar', 'min_only.debt', [AM('min_only', 'monthly_interest', label='Interest a month')]),
        CHART('Interest paid per month', 'column', 'month', [AM('interest_month', 'interest', 'month', 'Interest paid')]),
        CHART('Principal paid per month', 'column', 'month', [AM('interest_month', 'principal', 'month', 'Principal paid')]),
        CHART('Extra payments per month', 'column', 'month', [AM('interest_month', 'extra_paid', 'month', 'Extra paid')]),
        CHART('Payments by debt, last 12 months', 'bar', 'pay_by_debt.debt', [AM('pay_by_debt', 'interest12', label='Interest'), AM('pay_by_debt', 'principal12', label='Principal')]),
        CHART('Rate by debt', 'bar', 'min_only.debt', [AM('min_only', 'rate', label='Yearly rate', agg='avg')]),
        CHART('Minimum payment by debt', 'bar', 'min_only.debt', [AM('min_only', 'min_payment', label='Minimum payment')]),
        CHART('Minimums share of take-home per month', 'column', 'month', [AM('mins_pay', 'share', 'month', 'Share of take-home', agg='avg')]),
        CHART('Snowball balance by plan year', 'bar', 'sched_snow.planyear', [AM('sched_snow', 'balance', label='Average balance', agg='avg')]),
        CHART('Avalanche balance by plan year', 'bar', 'sched_aval.planyear', [AM('sched_aval', 'balance', label='Average balance', agg='avg')]),
        CHART('Interest by payoff plan', 'bar', 'compare.plan', [AM('compare', 'interest', label='Total interest')]),
        CHART('Payoff months by debt', 'bar', 'extra_plan.debt', [AM('extra_plan', 'months_now', label='Current plan'), AM('extra_plan', 'months_aval', label='Avalanche'), AM('extra_plan', 'months_snow', label='Snowball')]),
        CHART('Extra on each debt, plan against avalanche', 'bar', 'extra_plan.debt', [AM('extra_plan', 'extra_now', label='Extra now'), AM('extra_plan', 'extra_aval', label='Extra by avalanche')]),
        CHART('Debt by owner', 'bar', 'debts.owner', [AM('debts', 'balance', label='Balance')]),
        CHART('Payments by month, cards and loans', 'stacked', 'month', [AM('debt_payments', 'amount', 'date', 'Card payments', where=[('kind', '=', tok('dkind', 'Credit card'))]),
                                                                      AM('debt_payments', 'amount', 'date', 'Loan payments', where=[('kind', '=', tok('dkind', 'Instalment loan'))])]),
        CHART('Months to debt-free by payoff plan', 'bar', 'compare.plan', [AM('compare', 'months', label='Months')]),
        CHART('Interest saved by extra payment step', 'bar', 'extra_test.step', [AM('extra_test', 'interest_saved', label='Interest saved')]),
        CHART('Debt balance by kind', 'bar', 'debts.kind', [AM('debts', 'balance', label='Balance')]),
        CHART('Net worth and total debt per month', 'column', 'month', [AM('history', 'net_worth', 'month', 'Net worth'), AM('history', 'total_debt', 'month', 'Total debt')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Snowball against avalanche", "why": "both orders side by side with the same monthly payment: months, debt-free date and interest, so the household picks with its own numbers", "where": "Snowball Against Avalanche"},
    {"name": "Extra payment test", "why": "what each step of extra payment saves in months and interest, against paying only the minimums", "where": "Extra Payment Test"},
    {"name": "Extra payment solver", "why": "the smallest extra a month that clears every debt by the date you want, with a second pooled estimate", "where": "Extra Payment Solver"},
    {"name": "Avalanche order check", "why": "finds the debt with the highest rate, the extra it gets now and the interest lost each year by a different split", "where": "Avalanche Order Check"},
    {"name": "Minimum payments check", "why": "total minimums against take-home pay and against your own limit, with what happens if income falls", "where": "Minimum Payments Check"},
    {"name": "Debt ratios", "why": "debt payments over gross and card payments over take-home against typical ranges you can edit: a typical range, check your own numbers", "where": "Debt Ratios"},
    {"name": "Windfall to debt", "why": "a bonus or refund applied to the highest rate first, with the new debt-free date and the interest saved", "where": "Windfall to Debt"},
    {"name": "Month-by-month payoff schedules", "why": "60 months of payment, interest, principal and balance for snowball and for avalanche, built from closed-form formulas, no macros", "where": "Avalanche schedule"},
    {"name": "Due days map against payday", "why": "shows which due dates fall just before payday and suggests a day to ask your lender for", "where": "Due days map"},
    {"name": "Debt or savings balance", "why": "the emergency fund in months against the typical range before extra money goes to debt", "where": "Debt or Savings Balance"}]
competitors = [
    {"what": "budgeting app with a monthly subscription and bank links", "lacks": "has a debt screen but no snowball against avalanche on your own numbers, no extra payment solver and a yearly or monthly fee, and bank links break"},
    {"what": "debt snowball calculator sheet", "lacks": "orders by balance only: no avalanche comparison, no windfall test, no due days against payday and no ratios against typical ranges"},
    {"what": "single-purpose debt payoff template", "lacks": "stops at one payoff date: no minimum payments check, no interest lost by the current split and no history of balances and interest"},
    {"what": "free loan calculator sheet", "lacks": "handles one loan at a time: no rolling payments from a cleared debt to the next, no schedule for all debts together"}]
guide = [
    'Start here: open Start and type the household name, the two partner names, the extra payment a month and the date of the next payday in the yellow cells.',
    'Replace demo data, step 1: clear the demo rows of Debts and type your own debts with balance, yearly rate, minimum payment and due day; keep the header row and leave paid-off debts at balance zero.',
    'Replace demo data, step 2: clear Debt payments, Income and Net worth and paste your own rows; the schedules, the orders and the ratios fill in by themselves.',
    'Pay-day routine: pay every minimum, pay the extra on the debt first in the order of your method, then type each payment in Debt payments with its minimum, extra, interest and balance after.',
    'Month-close routine, in this order: update each balance in Debts, add the month to Net worth, read Minimums against pay, read the Extra payment plan and run the Avalanche Order Check.',
    'Run Snowball Against Avalanche when you choose a method and the Extra Payment Test when you can pay more; every date and saving is an estimate from your numbers, never a promise.',
    'Debt ratios compare with typical ranges you can edit in Settings: a typical range, check your own numbers. They are not advice and not a lending decision.',
    'A single adult with one income and no children can use every sheet: type your own debts, leave Partner 2 and the joint account empty, and use Partner 1 as the owner.',
    f'Use the {len(tools)} tools for the big questions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Read the dashboard and the Charts page each month: total debt, interest, extra payments and the debt-free dates.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you and there is nothing to link or re-connect; you type or paste your own data. It works in Excel and Google Sheets with no macros.',
    'What this is not: it is not a bank app, and not tax, legal, investment or credit advice; check your local rules and ask your adviser. Every verdict is an estimate from your numbers.']
listing = {"title": "Debt Payoff Planner Excel Template: Snowball vs Avalanche, Extra Payment Calculator, Debt Free Date, Minimum Payments, Debt Ratios",
    "headline": "Pay off cards and loans: snowball or avalanche, with your own numbers",
    "tags": ["debt payoff planner", "debt snowball", "debt avalanche", "debt free date", "extra payment", "credit card payoff", "loan payoff", "minimum payments", "debt ratios", "household budget", "excel template", "no subscription", "family finance"],
    "description": ("Plan how your household pays off cards and loans in one Excel workbook, for a single adult, a couple or a family. Type your debts with balance, yearly rate, minimum payment and due day, and the workbook builds the snowball order (smallest balance first) and the avalanche order (highest rate first), "
        "with a 60-month schedule for each, the debt-free date and the total interest. When a debt is cleared, its payment rolls to the next one.\n\n"
        "Snowball Against Avalanche shows both orders side by side. The Extra Payment Test shows what each step of extra payment saves in months and interest against paying only the minimums, and the Extra Payment Solver finds the extra a month that clears every debt by the date you want. "
        "The Avalanche Order Check finds the debt with the highest rate and the interest lost each year if the extra payment goes elsewhere. Windfall to Debt applies a bonus or refund to the highest rate first.\n\n"
        "The Minimum Payments Check compares your minimums with take-home pay and with a limit you set, and tests what happens if income falls. Debt Ratios compares your debt payments with typical ranges that you edit in Settings: a typical range, check your own numbers, never advice. "
        "A Due Days Map shows which due dates fall just before payday and suggests a day to ask your lender for. Balance history, interest paid by month and payments by debt show the year.\n\n"
        f"{len(tools)} decision tools, {len(forms)} printable sheets, {len(documents)} documents, {len(checklists)} checklists and {len(messages)} ready text messages come with it. This is part four of the Household Finance suite. A standard .xlsx workbook that works in Excel and Google Sheets, with no macros, no subscription and no bank links: you type or paste your own data. The demo copy is full of sample data. "
        "All dates and savings are estimates from your numbers, never promises. It is a household money kit, not a bank app, and not tax, legal, investment or credit advice."),
    "features": ["Snowball and avalanche schedules for up to ten debts", "Rolling payments from a cleared debt to the next", "Snowball against avalanche in months and interest", "Extra payment test and extra payment solver", "Avalanche order check for the highest rate",
                 "Minimum payments check against take-home pay", "Debt ratios against typical ranges you edit", "Windfall to debt with interest saved", "Due days map against payday", f"{len(tools)} decision tools and {len(forms)} printable sheets",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, no subscription, no bank links"]}
s = spec(id=f'{SUITE}-p4', slug='household-finance-debt', profession='Household Finance', name='Debt Payoff Planner',
         tagline='Pay off cards and loans: snowball or avalanche, with your own numbers', price_usd=29, colors={"primary": "#1F5F5B", "accent": "#F2B134"},
         settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
         suite={"key": SUITE, "part": 4, "of": 8, "focus": "Debt payoff planner: snowball, avalanche, extra payments and debt ratios"}, signature=signature, competitors=competitors, tools=tools,
         messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf4.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
