"""Doula business suite - part 8: Money, Owner Pay, Renewals, Year Plan."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du8_lists import *
from du8_tables import settings, tables
from du8_tools import tools

SUITE = 'fx-20261115-doula-business'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
LM = 'EDATE(%s,-1)' % MS
BM = 'IFERROR(INDEX({range:budget.monthly_budget},MATCH({pick},{range:budget.category},0)),0)'
SP12 = 'SUMIFS({range:expvar.amount},{range:expvar.category},{pick})'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('monthly_budget', 'Monthly Budget Sheet', 'Monthly budget of one expense category against spending', 'budget.category', F(('Category', 'budget.category'), ('Monthly budget', 'budget.monthly_budget')) + [
        FF('Spent in the last full month', 'SUMIFS({range:expenses.amount},{range:expenses.category},{pick},{range:expenses.month},%s)' % LM, 'money'),
        FF('Over or under the budget', 'SUMIFS({range:expenses.amount},{range:expenses.category},{pick},{range:expenses.month},%s)-%s' % (LM, BM), 'money'),
        FF('Average of the 3 months before', 'SUMIFS({range:expenses.amount},{range:expenses.category},{pick},{range:expenses.month},">="&EDATE(%s,-3),{range:expenses.month},"<"&%s)/3' % (LM, LM), 'money'),
        FF('Same month last year', 'SUMIFS({range:expenses.amount},{range:expenses.category},{pick},{range:expenses.month},EDATE(%s,-12))' % LM, 'money'),
        FF('Months over budget, last 12 months', 'COUNTIFS({range:expvar.category},{pick},{range:expvar.within},0)', 'int'),
        FF('Share of all spending, last full month', 'IFERROR(SUMIFS({range:expenses.amount},{range:expenses.category},{pick},{range:expenses.month},%s)/SUMIFS({range:expenses.amount},{range:expenses.month},%s),0)' % (LM, LM), 'pct')]),
    FORM('yearly_budget', 'Yearly Budget Sheet', 'Yearly budget of one expense category against 12 months of spending', 'budget.category', F(('Category', 'budget.category'), ('Monthly budget', 'budget.monthly_budget')) + [
        FF('Budget for 12 months', '12*%s' % BM, 'money'), FF('Spent in the last 12 months', SP12, 'money'), FF('Over or under the yearly budget', '%s-12*%s' % (SP12, BM), 'money'),
        FF('Share of all spending, 12 months', 'IFERROR(%s/SUM({range:expvar.amount}),0)' % SP12, 'pct'), FF('Average spending a month', '%s/12' % SP12, 'money'),
        FF('Suggested monthly budget', 'ROUND(%s/12*(1+{set:budget_tolerance}),0)' % SP12, 'money'), FF('Months over budget', 'COUNTIFS({range:expvar.category},{pick},{range:expvar.within},0)', 'int')]),
    FORM('expense_review', 'Expense Review Sheet', 'One expense with its category and month totals', 'expenses.expense_id', F(
        ('Date', 'expenses.date'), ('Category', 'expenses.category'), ('Description', 'expenses.description'), ('Amount', 'expenses.amount'), ('Paid to', 'expenses.paid_to'), ('Month', 'expenses.month'),
        ('Category total of the month', 'expenses.cat_month'), ('Category total, last 12 months', 'expenses.cat_12m'), ('All expenses of the month', 'expenses.month_all'), ('Share of the month', 'expenses.cat_share')) + [
        FF('Monthly budget of the category', 'IFERROR(INDEX({range:budget.monthly_budget},MATCH(%s,{range:budget.category},0)),0)' % LK('expenses', 'expense_id', 'category'), 'money'),
        FF('Share of the category total', 'IFERROR(%s/%s,0)' % (LK('expenses', 'expense_id', 'amount'), LK('expenses', 'expense_id', 'cat_month')), 'pct'),
        FF('Paid to this payee, last 12 months', 'SUMIFS({range:expenses.amount},{range:expenses.paid_to},%s,{range:expenses.date},">"&EDATE({today},-12))' % LK('expenses', 'expense_id', 'paid_to'), 'money')]),
    FORM('cash_sheet', 'Cash Forecast Sheet', 'Expected cash in and out for one coming month', 'forecast.month', F(
        ('Months ahead', 'forecast.ahead'), ('Births due', 'forecast.due_dates'), ('Cash from balances and instalments', 'forecast.scheduled_in'), ('Cash from new bookings', 'forecast.new_in'), ('Cash from births not yet booked', 'forecast.unbooked_in'),
        ('Expected cash in', 'forecast.expected_in'), ('Expected costs', 'forecast.expected_costs'), ('Owner pay', 'forecast.owner_pay'), ('Set-aside', 'forecast.set_aside'), ('Net cash change', 'forecast.net'),
        ('Closing cash', 'forecast.closing'), ('Months of cover', 'forecast.cover'), ('Cash check', 'forecast.status'), ('Closing cash, best case', 'forecast.closing_best'), ('Closing cash, worst case', 'forecast.closing_worst')) + [
        FF('Cash above the floor', '%s-{set:cash_floor}' % LK('forecast', 'month', 'closing'), 'money'), FF('Lowest closing cash in the 12 months', 'SMALL({range:forecast.closing},1)', 'money')]),
    FORM('owner_draw_sheet', 'Owner Draw Sheet', 'Owner draw of one month against profit and cash', 'cash.cash_id', F(
        ('Month', 'cash.month'), ('Opening cash', 'cash.opening'), ('Cash in', 'cash.cash_in'), ('Pay out', 'cash.pay_out'), ('Expenses out', 'cash.expenses_out'), ('Refunds', 'cash.refunds'), ('Set-aside moved', 'cash.set_aside'),
        ('Owner draw', 'cash.owner_draw'), ('Closing cash', 'cash.closing'), ('Months of cover', 'cash.cover'), ('Your floor', 'cash.floor')) + [
        FF('Profit of the month', 'SUMIFS({range:pnl.profit},{range:pnl.month},%s)' % LK('cash', 'cash_id', 'month'), 'money'),
        FF('Draw as a share of the profit', 'IFERROR(%s/SUMIFS({range:pnl.profit},{range:pnl.month},%s),0)' % (LK('cash', 'cash_id', 'owner_draw'), LK('cash', 'cash_id', 'month')), 'pct'),
        FF('Cash above the floor', '%s-{set:cash_floor}' % LK('cash', 'cash_id', 'closing'), 'money'),
        FF('Draw taken in the last 12 months', 'SUMIFS({range:cash.owner_draw},{range:cash.month},">"&EDATE(%s,-12),{range:cash.month},"<="&%s)' % (MS, MS), 'money')]),
    FORM('tax_sheet', 'Tax Set-aside Sheet', 'Set-aside of one month (confirm with your adviser)', 'tax.tax_id', F(
        ('Month', 'tax.month'), ('Profit', 'tax.profit'), ('Set-aside share', 'tax.set_aside_pct'), ('Set-aside', 'tax.set_aside'), ('Move by', 'tax.due_by'), ('Moved on', 'tax.moved_on'), ('Status', 'tax.status'),
        ('Moved on time', 'tax.on_time'), ('Late', 'tax.late'), ('Set-aside of the quarter', 'tax.quarter_set_aside')) + [
        FF('Days to the transfer date', '%s-{today}' % LK('tax', 'tax_id', 'due_by'), 'int'),
        FF('Set-aside of the same year', 'SUMIFS({range:tax.set_aside},{range:tax.month},">="&DATE(YEAR(%s),1,1),{range:tax.month},"<"&DATE(YEAR(%s)+1,1,1))' % (LK('tax', 'tax_id', 'month'), LK('tax', 'tax_id', 'month')), 'money'),
        FF('Set-aside still planned, all months', 'SUMIFS({range:tax.set_aside},{range:tax.status},%s)' % tok('taxstatus', 'Planned'), 'money')]),
    FORM('renewal_sheet', 'Renewal Record Sheet', 'One renewal with its due date, cost and holder', 'renewals.renewal_id', F(
        ('Holder', 'renewals.holder'), ('Item', 'renewals.item'), ('Due date', 'renewals.due_date'), ('Cost', 'renewals.cost'), ('Open', 'renewals.is_open'),
        ('Days left', 'renewals.days_left'), ('Status', 'renewals.status'), ('Holder phone', 'renewals.phone')) + [
        FF('Usual cost of this item', 'IFERROR(INDEX({range:renewal_items.cost},MATCH(%s,{range:renewal_items.item},0)),0)' % LK('renewals', 'renewal_id', 'item'), 'money'),
        FF('Days one renewal lasts', 'IFERROR(INDEX({range:renewal_items.cycle_days},MATCH(%s,{range:renewal_items.item},0)),0)' % LK('renewals', 'renewal_id', 'item'), 'int'),
        FF('Next due date after renewing', '%s+IFERROR(INDEX({range:renewal_items.cycle_days},MATCH(%s,{range:renewal_items.item},0)),0)' % (LK('renewals', 'renewal_id', 'due_date'), LK('renewals', 'renewal_id', 'item')), 'date'),
        FF('Open renewals of this holder', 'COUNTIFS({range:renewals.holder},%s,{range:renewals.is_open},1)' % LK('renewals', 'renewal_id', 'holder'), 'int')]),
    FORM('training_sheet', 'Training Record Sheet', 'One training with hours, cost and the yearly total of the holder', 'training.training_id', F(
        ('Holder', 'training.holder'), ('Kind', 'training.kind'), ('Title', 'training.title'), ('Date', 'training.date'), ('Hours', 'training.hours'), ('Cost', 'training.cost'), ('Done', 'training.done'), ('Days to the training', 'training.days_to')) + [
        FF('Holder hours, last 12 months', 'SUMIFS({range:training.hours},{range:training.holder},%s,{range:training.date},">"&EDATE({today},-12),{range:training.date},"<="&{today})' % LK('training', 'training_id', 'holder'), 'num'),
        FF('Hours short of the yearly target', 'MAX(0,{set:cpd_target_hours}-SUMIFS({range:training.hours},{range:training.holder},%s,{range:training.date},">"&EDATE({today},-12),{range:training.date},"<="&{today}))' % LK('training', 'training_id', 'holder'), 'num'),
        FF('Cost per hour', 'IFERROR(%s/%s,0)' % (LK('training', 'training_id', 'cost'), LK('training', 'training_id', 'hours')), 'money')]),
    FORM('timeoff_sheet', 'Time-off Plan Sheet', 'Cash in one coming month if you take time off', 'ownerplan.month', F(
        ('Expected profit', 'ownerplan.profit'), ('Set-aside', 'ownerplan.set_aside'), ('Owner draw', 'ownerplan.owner_draw'), ('Profit after set-aside and draw', 'ownerplan.surplus'), ('Cash left', 'ownerplan.cash_left'),
        ('Draw you can afford', 'ownerplan.can_pay'), ('Draw check', 'ownerplan.plan_check'), ('Cash lost by the time off', 'ownerplan.timeoff_hit'), ('Months of cover after the time off', 'ownerplan.cover_after')) + [
        FF('Weeks of time off tested', '{set:timeoff_weeks}', 'int'), FF('Share of income that stops', '{set:timeoff_stop_share}', 'pct'),
        FF('Cash left after the time off', '%s-%s' % (LK('ownerplan', 'month', 'cash_left'), LK('ownerplan', 'month', 'timeoff_hit')), 'money')]),
    FORM('year_end_sheet', 'Year-End Review Sheet', 'One yearly figure against the 12 months before', 'yearrev.measure', F(
        ('Last 12 months', 'yearrev.this_year'), ('The 12 months before', 'yearrev.last_year'), ('Change', 'yearrev.change'), ('Verdict', 'yearrev.verdict'), ('Revenue, last 12 months', 'yearrev.rev_12'), ('Profit, last 12 months', 'yearrev.profit_12'),
        ('Births, last 12 months', 'yearrev.births_12')) + [
        FF('Difference', '%s-%s' % (LK('yearrev', 'measure', 'this_year'), LK('yearrev', 'measure', 'last_year')), 'num'), FF('Average a month', '%s/12' % LK('yearrev', 'measure', 'this_year'), 'num'),
        FF('Change you count as a rise or a drop', '{set:drop_flag_pct}', 'pct')]),
    FORM('next_year_sheet', 'Next-Year Plan Sheet', 'Income and profit of one next-year scenario', 'yearplan.scenario', F(
        ('Births a month, change', 'yearplan.delta'), ('Births a month', 'yearplan.births_month'), ('Income for the year', 'yearplan.income'), ('Costs for the year', 'yearplan.costs'), ('Profit for the year', 'yearplan.profit'),
        ('Profit after your draw', 'yearplan.after_pay'), ('Income against your target', 'yearplan.gap_target'), ('Births a month to reach the target', 'yearplan.need_births')) + [
        FF('Income a month', '%s/12' % LK('yearplan', 'scenario', 'income'), 'money'), FF('Profit a month', '%s/12' % LK('yearplan', 'scenario', 'profit'), 'money'),
        FF('Profit per birth', 'IFERROR(%s/(12*%s),0)' % (LK('yearplan', 'scenario', 'profit'), LK('yearplan', 'scenario', 'births_month')), 'money'), FF('Income target', '{set:income_target}', 'money')]),
    FORM('accountant_sheet', 'Accountant Request Sheet', 'Figures to send to your accountant for one month', 'pnl.pnl_id', F(
        ('Month', 'pnl.month'), ('Revenue', 'pnl.revenue'), ('Total costs', 'pnl.costs'), ('Profit', 'pnl.profit'), ('Births', 'pnl.births'), ('Other costs', 'pnl.other_costs'), ('Expenses sheet total', 'pnl.expenses_total'),
        ('Other costs less Expenses sheet', 'pnl.expenses_diff'), ('Set-aside', 'pnl.tax_aside'), ('Closing cash', 'pnl.closing_cash')) + [
        FF('Cash in of the month', 'SUMIFS({range:cash.cash_in},{range:cash.month},%s)' % LK('pnl', 'pnl_id', 'month'), 'money'), FF('Pay out of the month', 'SUMIFS({range:cash.pay_out},{range:cash.month},%s)' % LK('pnl', 'pnl_id', 'month'), 'money'),
        FF('Roll-forward difference of the month', 'SUMIFS({range:cash.roll_diff},{range:cash.month},%s)' % LK('pnl', 'pnl_id', 'month'), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('owner_summary_doc', 'Monthly Owner Summary', 'Monthly owner summary: profit, cash, births and set-aside', 'pnl.pnl_id', [
        'Monthly owner summary of {set:company}, dated {today}. Month: {col:pnl.month}.',
        'Revenue: {col:pnl.revenue}. Total costs: {col:pnl.costs}. Profit before owner pay: {col:pnl.profit}. Profit margin: {col:pnl.margin}. Births: {col:pnl.births}.',
        'Closing cash: {col:pnl.closing_cash}. Set-aside for the month (confirm with your adviser): {col:pnl.tax_aside}. Doula pay share of revenue: {col:pnl.doula_share}.',
        'The margin of the 3 months before was {col:pnl.margin_avg3}. This page holds money, dates and counts only.'], ['Owner-doula'], NOTE),
    DOC('pnl_doc', 'Profit and Loss Statement', 'Profit and loss statement for one month', 'pnl.pnl_id', [
        'Profit and loss statement of {set:company} for {col:pnl.month}, dated {today}.',
        'Income: birth {col:pnl.birth_income}, postpartum {col:pnl.postpartum_income}, add-ons {col:pnl.addon_income}, classes {col:pnl.class_income}, other {col:pnl.other_income}. Revenue: {col:pnl.revenue}.',
        'Costs: doula pay {col:pnl.doula_pay}, backup pay {col:pnl.backup_pay}, mileage {col:pnl.mileage}, admin pay {col:pnl.admin_pay}, other costs {col:pnl.other_costs}. Total costs: {col:pnl.costs}.',
        'Profit before owner pay: {col:pnl.profit}. Profit margin: {col:pnl.margin}. Cost per birth: {col:pnl.cost_birth}. Prices and amounts are before any tax.'], ['Owner-doula', 'Accountant'], NOTE),
    DOC('cash_summary_doc', 'Cash Forecast Summary', 'Cash forecast summary for one coming month', 'forecast.month', [
        'Cash forecast summary of {set:company}, dated {today}. Month: {col:forecast.month}.',
        'Births due: {col:forecast.due_dates}. Cash from balances and instalments: {col:forecast.scheduled_in}. Cash from new bookings: {col:forecast.new_in}. Cash from births not yet booked: {col:forecast.unbooked_in}. Expected cash in: {col:forecast.expected_in}.',
        'Expected costs: {col:forecast.expected_costs}. Owner pay: {col:forecast.owner_pay}. Set-aside: {col:forecast.set_aside}. Closing cash: {col:forecast.closing}, which is {col:forecast.cover} months of cover. Cash check: {col:forecast.status}.',
        'The lowest closing cash in the next 12 months is {col:forecast.lowest_amount}. The forecast is built from your own dates and history and is not a promise.'], ['Owner-doula'], NOTE),
    DOC('budget_report_doc', 'Budget Against Actual Report', 'Budget against actual report for one expense category', 'expvar.category', [
        'Budget against actual report of {set:company}, dated {today}. Category: {col:expvar.category}.',
        'Monthly budget: {col:expvar.budget}. Spent in the last full month: {col:expvar.cat_last_amount}. Spent in the last 12 months: {col:expvar.cat_year_amount} against a budget of {col:expvar.cat_year_budget}.',
        'Months over budget in the last 12 months: {col:expvar.cat_over_months}. Variance of the last full month: {col:expvar.v_last}.',
        'Review the budget of a category that is over in many months.'], ['Owner-doula'], NOTE),
    DOC('pay_plan_doc', 'Owner Pay and Set-aside Plan', 'Owner pay and set-aside plan for one month', 'ownerplan.month', [
        'Owner pay and set-aside plan of {set:company}, dated {today}. Month: {col:ownerplan.month}.',
        'Expected profit: {col:ownerplan.profit}. Set-aside: {col:ownerplan.set_aside}. Owner draw: {col:ownerplan.owner_draw}. Profit after the set-aside and the draw: {col:ownerplan.surplus}.',
        'Cash left after this month: {col:ownerplan.cash_left}, which is {col:ownerplan.headroom} above your floor. The draw you can afford is {col:ownerplan.can_pay}. Draw check: {col:ownerplan.plan_check}.',
        'The set-aside share is an example. Please confirm it with your adviser and check your local rules.'], ['Owner-doula', 'Accountant'], NOTE),
    DOC('renewal_calendar_doc', 'Renewals and Training Calendar', 'Renewals calendar entry with the red and amber count', 'renewcal.renewal_id', [
        'Renewals and training calendar of {set:company}, dated {today}.',
        'Renewal {col:renewcal.renewal_id}: {col:renewcal.item} for {col:renewcal.holder}, due on {col:renewcal.due_date}, which is {col:renewcal.days_left} days from today. Status: {col:renewcal.status}. Cost: {col:renewcal.cost}.',
        'Renewals that are red now: {col:renewcal.red_total}. Renewals that are red or amber now: {col:renewcal.soon_total}.',
        'Please renew early and send the new date to the owner-doula. Check your local rules for the dates that apply to you.'], ['Owner-doula', 'Admin'], NOTE),
    DOC('expense_report_doc', 'Expense Report by Category', 'Expense report for one expense and its category', 'expenses.expense_id', [
        'Expense report of {set:company}, dated {today}. Expense {col:expenses.expense_id} on {col:expenses.date}.',
        'Category: {col:expenses.category}. Description: {col:expenses.description}. Amount: {col:expenses.amount}. Paid to: {col:expenses.paid_to}.',
        'Total of the category in the month: {col:expenses.cat_month}. Total of the category in the last 12 months: {col:expenses.cat_12m}. All expenses of the month: {col:expenses.month_all}. Share of the month: {col:expenses.cat_share}.',
        'Keep the receipt with your records and check your local rules for how long to keep it.'], ['Owner-doula', 'Admin'], NOTE),
    DOC('year_review_doc', 'Year in Review Report', 'Year in review for one yearly figure', 'yearrev.measure', [
        'Year in review of {set:company}, dated {today}. Figure: {col:yearrev.measure}.',
        'Last 12 months: {col:yearrev.this_year}. The 12 months before: {col:yearrev.last_year}. Change: {col:yearrev.change}. Verdict: {col:yearrev.verdict}.',
        'Revenue of the last 12 months: {col:yearrev.rev_12}. Profit of the last 12 months: {col:yearrev.profit_12}. Births of the last 12 months: {col:yearrev.births_12}.',
        'The last 12 months include the month so far. Compare each figure with your own plan.'], ['Owner-doula'], NOTE),
    DOC('accountant_doc', 'Accountant Pack', 'Accountant pack for one month (confirm with your adviser)', 'pnl.pnl_id', [
        'Accountant pack of {set:company} for {col:pnl.month}, dated {today}.',
        'Revenue: {col:pnl.revenue}. Total costs: {col:pnl.costs}. Profit before owner pay: {col:pnl.profit}. Other costs on the profit and loss: {col:pnl.other_costs}. Expenses sheet total: {col:pnl.expenses_total}. Difference: {col:pnl.expenses_diff}.',
        'Closing cash: {col:pnl.closing_cash}. Set-aside for the month: {col:pnl.tax_aside}. Births: {col:pnl.births}.',
        'Please confirm the set-aside and the treatment of every item with your adviser and check your local rules. Amounts are before any tax.'], ['Owner-doula', 'Accountant'], NOTE),
    DOC('next_year_doc', 'Next-Year Plan', 'Next-year plan for one scenario', 'yearplan.scenario', [
        'Next-year plan of {set:company}, dated {today}. Scenario: {col:yearplan.scenario}.',
        'Births a month: {col:yearplan.births_month}. Income for the year: {col:yearplan.income}. Costs for the year: {col:yearplan.costs}. Profit for the year: {col:yearplan.profit}. Profit after your draw: {col:yearplan.after_pay}.',
        'Income against your target: {col:yearplan.gap_target}. Births a month needed to reach the target: {col:yearplan.need_births}.',
        'The plan uses your own revenue and cost per birth of the last 12 months. It is an estimate, not a promise.'], ['Owner-doula'], NOTE),
    DOC('timeoff_doc', 'Time-off Plan Note', 'Time-off plan note with the cash left', 'ownerplan.month', [
        'Time-off plan note of {set:company}, dated {today}. Month: {col:ownerplan.month}.',
        'Cash left before the time off: {col:ownerplan.cash_left}. Cash lost by the time off: {col:ownerplan.timeoff_hit}. Months of cover after the time off: {col:ownerplan.cover_after}.',
        'Owner draw: {col:ownerplan.owner_draw}. Draw check: {col:ownerplan.plan_check}. Name a backup doula for every on-call window that falls in the time off.',
        'This note holds dates and amounts only.'], ['Owner-doula'], NOTE),
    DOC('renewal_letter_doc', 'Renewal Reminder Letter', 'Renewal reminder letter for a doula', 'renewals.renewal_id', [
        'Renewal reminder of {set:company}, dated {today}. Dear {col:renewals.holder},',
        'Your {col:renewals.item} is due on {col:renewals.due_date}. Status: {col:renewals.status}. The usual cost is {col:renewals.cost}.',
        'Please renew it before the due date and send the new date to the owner-doula. If it is already done, please send us the date.',
        'Check your local rules for the dates that apply to you. Thank you.'], ['Owner-doula', 'Doula'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('monthly_close', 'Monthly Close Steps', 'pnl', 'pnl.month', [('Log every expense of the month in Expenses', 28), ('Check that every payment and instalment is recorded', 29), ('Update the cash balance in Cash by Month', 30), ('Review the profit and loss', 31), ('Compare the month with your own history', 32), ('Send the totals to your accountant', 34)]),
    CHK('quarterly_setaside', 'Quarterly Set-aside Steps', 'tax', 'tax.month', [('Check the profit of the quarter', 31), ('Work out the set-aside at your share', 32), ('Confirm the share with your adviser', 34), ('Move the set-aside by the transfer date', 35), ('Write the date in Tax Set-aside', 36)]),
    CHK('draw_decision', 'Owner Draw Decision Steps', 'cash', 'cash.month', [('Check the closing cash and your floor', 30), ('Check the set-aside still to move', 31), ('Check the unearned cash held', 31), ('Run the Owner Pay and Tax Set-Aside tool', 32), ('Decide the draw and write it down', 33)]),
    CHK('budget_review', 'Budget Review Steps', 'pnl', 'pnl.month', [('List the categories over budget', 31), ('Find the payee behind each overspend', 32), ('Decide what to cut or to budget higher', 34), ('Update the monthly budget', 35), ('Check again next month', 62)]),
    CHK('renewal_due', 'Renewal Due Steps', 'renewals', 'renewals.due_date', [('Find the renewal steps and the cost', -60), ('Book the renewal or the course', -45), ('Pay the renewal', -30), ('Send the new date to the owner-doula', 0), ('Update Renewals with the date renewed', 7)]),
    CHK('training_plan', 'Training Plan Steps', 'training', 'training.date', [('Choose the training and book the place', -30), ('Block the date in the on-call plan', -21), ('Name a backup doula for that day', -14), ('Attend and note the hours', 0), ('Add the hours to the training log', 3)]),
    CHK('cash_review', 'Cash Forecast Review Steps', 'forecast', 'forecast.month', [('Update instalments and balances', -30), ('Check the lowest cash month', -28), ('Check the months below the floor', -27), ('Move the draw or a cost if needed', -25), ('Write down what changed', -21)]),
    CHK('year_close', 'Year-End Close Steps', 'pnl', 'pnl.month', [('Close the last month of the year', 30), ('Check that the set-aside is moved', 35), ('Review the year in Year in Review', 40), ('Collect the records for your accountant', 45), ('Send the year-end pack', 50)]),
    CHK('next_year', 'Next-Year Plan Steps', 'forecast', 'forecast.month', [('Review the births a month you did', 0), ('Set the income target for the year', 7), ('Test one more and one fewer birth a month', 14), ('Update the budget for each category', 21), ('Write the plan and share it with your adviser', 28)]),
    CHK('accountant_meeting', 'Accountant Meeting Steps', 'pnl', 'pnl.month', [('Send the profit and loss and the cash sheet', 30), ('List your questions about each category', 32), ('Ask about the set-aside share', 34), ('Hold the meeting', 36), ('Write down what was agreed', 37)]),
    CHK('timeoff_plan', 'Time-off Plan Steps', 'forecast', 'forecast.month', [('Choose the weeks off', -60), ('Run the Time-Off Cash Test', -55), ('Name a backup doula for every window', -45), ('Tell the clients with a window in those weeks', -30), ('Check the cash before you leave', -3)]),
    CHK('insurance_renewal', 'Insurance Renewal Steps', 'renewals', 'renewals.due_date', [('Ask the insurer for the renewal terms', -60), ('Compare the cost with last year', -50), ('Check that the cover matches your work', -45), ('Pay the renewal', -14), ('File the new document and the date', 0)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('o_profit', 'Owner: this month\'s profit', 'pnl', 'pnl.owner_phone', 'Hello {owner_name}, your profit for {month} is {profit} on revenue of {revenue}. {company}'),
    M('o_margin', 'Owner: your margin against 3 months', 'pnl', 'pnl.owner_phone', 'Hello {owner_name}, your profit margin for {month} is {margin} against {margin_avg3} for the 3 months before. {company}'),
    M('o_cash', 'Owner: cash and your floor', 'cash', 'cash.owner_phone', 'Hello {owner_name}, your closing cash for {month} is {closing} and your floor is {floor}. {company}'),
    M('o_lowest', 'Owner: your lowest cash month ahead', 'forecast', 'forecast.owner_phone', 'Hello {owner_name}, your lowest cash month ahead is {lowest_month} at {lowest_amount}. {company}'),
    M('o_cover', 'Owner: months of cover', 'cash', 'cash.owner_phone', 'Hello {owner_name}, you have {cover} months of cover at current fixed costs for {month}. {company}'),
    M('o_setaside', 'Owner: your set-aside for the quarter', 'tax', 'tax.owner_phone', 'Hello {owner_name}, your set-aside for the quarter of {month} is {quarter_set_aside}. Please confirm it with your adviser. {company}'),
    M('o_draw', 'Owner: your draw this month', 'cash', 'cash.owner_phone', 'Hello {owner_name}, your owner draw for {month} is {owner_draw}. {company}'),
    M('o_paymyself', 'Owner: you can pay yourself', 'ownerplan', 'ownerplan.owner_phone', 'Hello {owner_name}, you can pay yourself {can_pay} for {month}. {company}'),
    M('o_reduce', 'Owner: reduce your draw', 'ownerplan', 'ownerplan.owner_phone', 'Hello {owner_name}, to stay above your floor, reduce your draw for {month} to {can_pay}. Cash left after the month: {cash_left}. {company}'),
    M('o_unearned', 'Owner: unearned cash', 'ownerplan', 'ownerplan.owner_phone', 'Hello {owner_name}, unearned cash is {unearned}. It is cash received for work not yet done. {company}'),
    M('o_variance', 'Owner: your largest budget variance', 'expvar', 'expvar.owner_phone', 'Hello {owner_name}, your budget variance for {category} in {month} is {variance}. {company}'),
    M('o_catshare', 'Owner: a category against revenue', 'expvar', 'expvar.owner_phone', 'Hello {owner_name}, {category} spending in {month} is {share_rev} of revenue. {company}'),
    M('o_insurance', 'Owner: your renewal is due', 'renewcal', 'renewcal.owner_phone', 'Hello {owner_name}, your {item} renewal is due on {due_date}, in {days_left} days. {company}'),
    M('o_red', 'Owner: renewals that are red', 'renewcal', 'renewcal.owner_phone', 'Hello {owner_name}, {red_total} renewals are red now. The next is {item} on {due_date}. {company}'),
    M('o_holder', 'Owner: a renewal of a holder is due', 'renewcal', 'renewcal.owner_phone', 'Hello {owner_name}, {holder} has a {item} renewal due on {due_date}. {company}'),
    M('o_year', 'Owner: your year in review is ready', 'yearrev', 'yearrev.owner_phone', 'Hello {owner_name}, your year in review is ready: {measure} was {this_year} against {last_year}. {company}'),
    M('o_births', 'Owner: births a month for your target', 'yearplan', 'yearplan.owner_phone', 'Hello {owner_name}, you need {need_births} births a month to reach your income target. {company}'),
    M('o_nextyear', 'Owner: your next-year plan', 'yearplan', 'yearplan.owner_phone', 'Hello {owner_name}, your next-year plan is ready for review: {scenario} gives income of {income} and profit of {profit}. {company}'),
    M('o_timeoff', 'Owner: time off and months of cover', 'ownerplan', 'ownerplan.owner_phone', 'Hello {owner_name}, your time off in {month} leaves {cover_after} months of cover. {company}'),
    M('o_fixed', 'Owner: your fixed costs against revenue', 'pnl', 'pnl.owner_phone', 'Hello {owner_name}, your fixed costs for {month} are {fixed_share} of revenue. {company}'),
    M('d_due', 'Doula: your renewal is due', 'renewals', 'renewals.phone', 'Hello {holder}, your {item} is due on {due_date}. {company}'),
    M('d_overdue', 'Doula: your renewal is overdue', 'renewals', 'renewals.phone', 'Hello {holder}, your {item} was due on {due_date}. Please send us the new date. {company}'),
    M('d_cpd', 'Doula: your training hours this year', 'team', 'team.phone', 'Hello {name}, your training hours in the last 12 months are {cpd_hours}. {company}'),
    M('d_short', 'Doula: hours short of the yearly target', 'team', 'team.phone', 'Hello {name}, you are {cpd_gap} hours short of the yearly training target. {company}'),
    M('d_train', 'Doula: a training day is planned', 'training', 'training.phone', 'Hello {holder}, a training day is planned for {date}: {title}. {company}'),
    M('b_due', 'Backup doula: your renewal is due', 'renewals', 'renewals.phone', 'Hello {holder}, as a backup doula your {item} is due on {due_date}. Please send us the new date once it is done. {company}'),
    M('a_60', 'Admin: renewals due in the next 60 days', 'renewcal', 'renewcal.admin_phone', 'Hello {admin_name}, {soon_total} renewals are red or amber now. The next is {item} on {due_date}. {company}'),
    M('a_nocat', 'Admin: an expense without a category', 'expenses', 'expenses.admin_phone', 'Hello {admin_name}, expense {expense_id} of {amount} on {date} needs a category. Please check it. {company}'),
    M('a_week', 'Admin: bills and renewals due this week', 'renewcal', 'renewcal.admin_phone', 'Hello {admin_name}, please check the {item} of {holder}, due on {due_date}, cost {cost}. {company}'),
    M('x_pnl', 'Accountant: monthly profit and loss', 'pnl', 'pnl.accountant_phone', 'Hello {accountant_name}, the profit and loss for {month}: revenue {revenue}, costs {costs}, profit {profit}. {company}'),
    M('x_cash', 'Accountant: set-aside for the quarter', 'tax', 'tax.accountant_phone', 'Hello {accountant_name}, the set-aside for the quarter of {month} is {quarter_set_aside}. Please confirm it. {company}'),
    M('x_year', 'Accountant: the year-end pack is ready', 'yearrev', 'yearrev.accountant_phone', 'Hello {accountant_name}, the year-end pack is ready. {measure}: {this_year} against {last_year}. {company}'),
    M('x_question', 'Accountant: a question about spending', 'expvar', 'expvar.accountant_phone', 'Hello {accountant_name}, a question about {category} spending in {month}: the amount is {amount} against a budget of {budget}. {company}'),
    M('i_renew', 'Insurer: our renewal date', 'renewcal', 'renewcal.insurer_phone', 'Hello {insurer_name}, our renewal date is {due_date}. Please send the terms for {item}. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
def T12(col, t='pnl'): return 'SUMIFS({range:%s.%s},{range:%s.month},">"&EDATE(%s,-12),{range:%s.month},"<="&%s)' % (t, col, t, MS, t, MS)
def TM(col): return 'SUMIFS({range:pnl.%s},{range:pnl.month},%s)' % (col, MS)
REV12, PROF12, BIR12 = T12('revenue'), T12('profit'), T12('births')
YRK = lambda k, c: 'IFERROR(INDEX({range:yearrev.%s},MATCH(%d,{range:yearrev.no},0)),0)' % (c, k)
JAN = 'DATE(YEAR({today}),1,1)'
RC = 'SUMIFS({range:renewals.cost},{range:renewals.is_open},1,{range:renewals.due_date},">"&{today},{range:renewals.due_date},"<="&EDATE({today},12))'
TCOST = 'SUMIFS({range:training.cost},{range:training.date},">"&{today},{range:training.date},"<="&EDATE({today},12))'
kpis = [
    KPI('Revenue this month', TM('revenue'), 'money'), KPI('Revenue, last 12 months', REV12, 'money'), KPI('Costs this month', TM('costs'), 'money'), KPI('Profit this month', TM('profit'), 'money'),
    KPI('Profit, last 12 months', PROF12, 'money'), KPI('Profit margin this month', 'IFERROR(%s/%s,0)' % (TM('profit'), TM('revenue')), 'pct'), KPI('Profit margin, last 12 months', 'IFERROR(%s/%s,0)' % (PROF12, REV12), 'pct'),
    KPI('Births this month', TM('births'), 'int'), KPI('Births, last 12 months', BIR12, 'int'), KPI('Profit per birth, last 12 months', 'IFERROR(%s/%s,0)' % (PROF12, BIR12), 'money'),
    KPI('Doula pay share of revenue, 12 months', 'IFERROR((%s+%s)/%s,0)' % (T12('doula_pay'), T12('backup_pay'), REV12), 'pct'), KPI('Cost share of revenue, 12 months', 'IFERROR(%s/%s,0)' % (T12('costs'), REV12), 'pct'),
    KPI('Cash balance now', 'SUMIFS({range:cash.closing},{range:cash.month},%s)' % MS, 'money', alert={"when": "< {set:cash_floor}", "style": "bad"}),
    KPI('Months of cash at current fixed costs', 'IFERROR(SUMIFS({range:cash.closing},{range:cash.month},%s)/(AVERAGEIFS({range:pnl.fixed_costs},{range:pnl.month},">="&EDATE(%s,-3),{range:pnl.month},"<"&%s)+{set:owner_draw}),0)' % (MS, MS, MS), 'num'),
    KPI('Lowest cash month, next 12 months', 'SMALL({range:forecast.closing},1)', 'money'), KPI('Months below the floor, next 12', 'SUM({range:forecast.below_floor})', 'int'),
    KPI('Unearned cash now', 'SUM({range:contracts.unearned})', 'money'), KPI('Set-aside this year', 'SUMIFS({range:tax.set_aside},{range:tax.month},">="&%s)' % JAN, 'money'),
    KPI('Set-aside still to move', 'SUMIFS({range:tax.set_aside},{range:tax.status},%s)' % tok('taxstatus', 'Planned'), 'money'), KPI('Owner draw this year', 'SUMIFS({range:cash.owner_draw},{range:cash.month},">="&%s)' % JAN, 'money'),
    KPI('Budget variance this month', 'SUMIFS({range:expvar.variance},{range:expvar.month},%s)' % MS, 'money'),
    KPI('Biggest budget variance, last full month', 'IFERROR(INDEX({range:expvar.category},MATCH(LARGE({range:expvar.v_last},1),{range:expvar.v_last},0))&"","")', 'text'),
    KPI('Expenses, last 12 months', 'SUMIFS({range:expenses.amount},{range:expenses.date},">"&EDATE({today},-12),{range:expenses.date},"<="&{today})', 'money'),
    KPI('Expenses share of revenue, 12 months', 'IFERROR(SUMIFS({range:expenses.amount},{range:expenses.date},">"&EDATE({today},-12),{range:expenses.date},"<="&{today})/%s,0)' % REV12, 'pct'),
    KPI('Renewals red now', 'SUM({range:renewals.is_red})', 'int', alert={"when": "> 0", "style": "bad"}), KPI('Renewals amber now', 'SUM({range:renewals.is_amber})', 'int'),
    KPI('Renewal and training cost, 12 months', '%s+%s' % (RC, TCOST), 'money'),
    KPI('Training hours, last 12 months', 'SUMIFS({range:training.hours},{range:training.date},">"&EDATE({today},-12),{range:training.date},"<="&{today})', 'num'),
    KPI('Profit against last year', YRK(12, 'change'), 'pct'), KPI('Revenue against last year', YRK(1, 'change'), 'pct'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Money Dashboard", "kpis": kpis,
    "monthly": {"title": "Revenue, costs, profit and closing cash", "date": "pnl.month", "series": [
        {"label": "Revenue", "sum": "pnl.revenue", "date": "pnl.month"}, {"label": "Costs", "sum": "pnl.costs", "date": "pnl.month"}, {"label": "Profit", "sum": "pnl.profit", "date": "pnl.month"},
        {"label": "Closing cash", "sum": "cash.closing", "date": "cash.month"}]},
    "breakdowns": [{"title": "Expenses by category", "by": "expenses.category", "value": "expenses.amount", "agg": "sum"}, {"title": "Expenses by payee", "by": "expenses.paid_to", "value": "expenses.amount", "agg": "sum"},
                   {"title": "Renewal cost by item", "by": "renewals.item", "value": "renewals.cost", "agg": "sum"}, {"title": "Training hours by kind", "by": "training.kind", "value": "training.hours", "agg": "sum"}]}
def MC(title, typ, t, col, dcol, label): return CHART(title, typ, 'month', [AGG('sum', t, col, date=dcol, label=label)])
insights = {"filters": [{"label": "Expense category", "list": "expcat"}, {"label": "Renewal item", "list": "renewal"}, {"label": "Training kind", "list": "cpd"}],
    "gauges": [
        {"title": "Cash above the floor", "num": AGG('count', 'cash', where=[('above_floor', '=', 1)]), "den": AGG('count', 'cash')},
        {"title": "Months of cover against the setting", "num": AGG('count', 'cash', where=[('cover_ok', '=', 1)]), "den": AGG('count', 'cash')},
        {"title": "Margin against your last 12 months", "num": AGG('count', 'pnl', where=[('in12', '=', 1), ('above_avg', '=', 1)]), "den": AGG('count', 'pnl', where=[('in12', '=', 1)])},
        {"title": "Budget kept", "num": AGG('count', 'expvar', where=[('within', '=', 1)]), "den": AGG('count', 'expvar')},
        {"title": "Renewals not red", "num": AGG('count', 'renewals', where=[('is_open', '=', 1), ('is_red', '=', 0)]), "den": AGG('count', 'renewals', where=[('is_open', '=', 1)])},
        {"title": "Set-aside moved on time", "num": AGG('count', 'tax', where=[('on_time', '=', 1)]), "den": AGG('count', 'tax', where=[('due_passed', '=', 1)])}],
    "charts": [
        MC('Revenue per month', 'column', 'pnl', 'pnl.revenue', 'pnl.month', 'Revenue'), MC('Costs per month', 'column', 'pnl', 'pnl.costs', 'pnl.month', 'Costs'), MC('Profit per month', 'column', 'pnl', 'pnl.profit', 'pnl.month', 'Profit'),
        CHART('Profit margin per month', 'line', 'month', [AGG('avg', 'pnl', 'pnl.margin', date='pnl.month', label='Profit margin')]),
        CHART('Revenue by source of income per month', 'stacked', 'month', [AGG('sum', 'pnl', 'pnl.birth_income', date='pnl.month', label='Birth'), AGG('sum', 'pnl', 'pnl.postpartum_income', date='pnl.month', label='Postpartum'),
                                                                          AGG('sum', 'pnl', 'pnl.addon_income', date='pnl.month', label='Add-ons'), AGG('sum', 'pnl', 'pnl.class_income', date='pnl.month', label='Classes')]),
        MC('Doula pay per month', 'column', 'pnl', 'pnl.doula_pay', 'pnl.month', 'Doula pay'), MC('Births per month', 'column', 'pnl', 'pnl.births', 'pnl.month', 'Births'),
        CHART('Visit hours per month', 'line', 'month', [AGG('sum', 'pnl', 'pnl.visit_hours', date='pnl.month', label='Visit hours')]),
        CHART('Cash balance per month', 'line', 'month', [AGG('sum', 'cash', 'cash.closing', date='cash.month', label='Closing cash')]),
        CHART('Cash in and out per month', 'column', 'month', [AGG('sum', 'cash', 'cash.cash_in', date='cash.month', label='Cash in'), AGG('sum', 'cash', 'cash.pay_out', date='cash.month', label='Pay out'),
                                                              AGG('sum', 'cash', 'cash.expenses_out', date='cash.month', label='Expenses out'), AGG('sum', 'cash', 'cash.owner_draw', date='cash.month', label='Owner draw')]),
        MC('Tax set-aside per month', 'column', 'tax', 'tax.set_aside', 'tax.month', 'Set-aside'), MC('Owner draw per month', 'column', 'cash', 'cash.owner_draw', 'cash.month', 'Owner draw'),
        MC('Expenses per month', 'column', 'expenses', 'expenses.amount', 'expenses.date', 'Expenses'), CHART('Expenses by category', 'bar', 'expenses.category', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
        CHART('Marketing and class venue costs per month', 'column', 'month', [AGG('sum', 'expenses', 'expenses.amount', date='expenses.date', where=[('category', '=', tok('expcat', 'Marketing'))], label='Marketing'),
                                                                            AGG('sum', 'expenses', 'expenses.amount', date='expenses.date', where=[('category', '=', tok('expcat', 'Class venue'))], label='Class venue')]),
        CHART('Expenses by paid to', 'bar', 'expenses.paid_to', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
        MC('Training hours per month', 'column', 'training', 'training.hours', 'training.date', 'Training hours'), CHART('Training cost by kind', 'bar', 'training.kind', [AGG('sum', 'training', 'training.cost', label='Training cost')]),
        CHART('Renewals by item', 'bar', 'renewals.item', [AGG('count', 'renewals', label='Renewals')]), CHART('Renewal cost by item', 'bar', 'renewals.item', [AGG('sum', 'renewals', 'renewals.cost', label='Renewal cost')]),
        CHART('Renewals due per month', 'column', 'month', [AGG('count', 'renewals', date='renewals.due_date', label='Renewals due')]),
        CHART('Instalments due per month', 'column', 'month', [AGG('sum', 'instalments', 'instalments.amount', date='instalments.due_date', label='Instalments due')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Uneven-month cash forecast", "why": "cash in from due dates, payment plans and unbooked births for 12 months, with the lowest month and the cover against your floor", "where": "Uneven-Month Cash Forecast"},
    {"name": "Owner pay and tax set-aside", "why": "answers can I pay myself this month, with the set-aside to move and a draw your cash allows (confirm with your adviser)", "where": "Owner Pay and Tax Set-Aside"},
    {"name": "Training and renewal dates", "why": "red within 30 days and amber within 60 for every certification, insurance, registration and check, with the cost of the year", "where": "Training and Renewal Dates"},
    {"name": "Profit ratios by month", "why": "margin, doula pay share and cost per birth against your own last 3 months and the same month last year", "where": "Profit Ratios by Month"},
    {"name": "Compare with own history", "why": "every monthly figure against its 3-month average and last year, with the drops over your set share flagged", "where": "Compare With Own History"},
    {"name": "Year-end summary and next-year plan", "why": "births, income and profit of the year, then the births a month you need for your income target at your own prices", "where": "Year-End Summary and Plan"},
    {"name": "Break-even births a month", "why": "fixed costs plus your draw over the margin per birth, solved in closed form with a price what-if", "where": "Break-Even Births a Month"},
    {"name": "Unearned cash on every contract", "why": "cash received for work not yet done, contract by contract, set against the cash you hold", "where": "Contracts"},
    {"name": "Budget against actual ranking", "why": "every expense category ranked by overspend against the monthly budget and the same month last year", "where": "Budget Variance Ranker"},
    {"name": "Time-off cash test", "why": "weeks without new births attended against the cash you hold and the months of cover that fixed costs and your draw still need", "where": "Time-Off Cash Test"}]
competitors = [
    {"what": "free client-tracker templates", "lacks": "list clients and dates but never forecast cash from payment plans, set aside tax or show the unearned balance"},
    {"what": "subscription practice-management software", "lacks": "charge every month and give no cash floor, owner draw check or renewal calendar built for a small doula agency"},
    {"what": "generic invoice and expense spreadsheets", "lacks": "add up costs but know nothing of births, packages, doula pay or the months of cover that a doula business needs"},
    {"what": "single-sheet budget templates", "lacks": "compare spending with a budget but never compare each month with your own history or last year"},
    {"what": "paper diaries for renewals and training", "lacks": "record dates but never turn them into red and amber warnings, a cost plan or a yearly training total per doula"}]
guide = [
    'Open Start and type your business name and your own limits in the yellow cells: the owner draw, the set-aside share, the cash floor, the months of cover, the red and amber days for renewals and the training hours you want.',
    'A doula is a non-medical support person who helps a client before, during or after a birth. A solo doula keeps one row per person and no backup doula.',
    'Write each month in Profit and Loss and Cash by Month. The revenue, profit, margin, cost per birth and months of cover fill in by themselves.',
    'Keep Expenses up to date and set a monthly Budget for each category. Budget vs Actual then shows every category and month against the budget and last year.',
    'Check Contracts, Instalments and Clients. They give the cash expected from balances and payment plans and the unearned balance (cash received for work not yet done). An hour pack is a set number of postpartum hours bought together.',
    'Read Cash Forecast for the next 12 months: expected cash in, costs, owner pay, set-aside, the lowest month and the best and worst cases.',
    'Use Owner Pay Plan and Tax Set-aside to decide your draw. The set-aside share is an example: confirm it with your adviser.',
    'Record every renewal in Renewals and every training in Training. Renewal Calendar shows the next ones with red and amber status and Training Hours by Holder shows the hours of each doula.',
    'Open Own History Compare, Year in Review and Year Plan at month end and year end to compare with your own history and set next year\'s births a month.',
    f'Use the {len(tools)} tools to answer the weekly money questions: cash, draw, set-aside, break-even, time off and the accountant pack.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Money Dashboard and the charts every month. A solo doula uses the same sheets as a one-person money sheet with one doula and no backup rota.']
listing = {"title": "Doula Business Money Excel Template: Profit and Loss, Cash Flow Forecast, Owner Pay, Tax Set-Aside, Renewals Tracker, Budget vs Actual",
    "headline": "Know your cash, your pay and your renewal dates before they surprise you",
    "tags": ["doula", "doula business", "doula template", "cash flow forecast", "profit and loss", "owner draw", "tax set aside", "budget vs actual", "renewals tracker", "expense tracker", "excel template", "year end summary", "small business"],
    "description": ("Run the money side of your doula business in one Excel workbook. Built for an owner-doula who also takes clients, contracted doulas, backup doulas and a part-time admin, and just as useful for a solo doula who wants a one-person money sheet. "
        "Profit and Loss and Cash by Month turn your monthly figures into revenue, profit, margin, cost per birth, doula pay share and months of cover. Expenses, Budget and Budget vs Actual rank every category against the monthly budget and the same month last year. Contracts show the cash received and the unearned balance (cash received for work not yet done) for every package.\n\n"
        "Cash Forecast builds an uneven-month forecast for the next 12 months from due dates, balances and payment plans, with the lowest month, the months of cover and a best and worst case. Owner Pay Plan and Tax Set-aside show whether you can pay yourself this month and what to move aside (confirm the share with your adviser). Renewals, Training, Renewal Calendar and Training Hours by Holder give red and amber warnings, the cost of the year and the training hours of each doula.\n\n"
        f"{len(tools)} tools answer the weekly questions: training and renewal dates, expense tracker, cash forecast, owner pay, profit ratios, compare with your own history, year-end summary and next-year plan, cash runway, budget ranking, break-even births a month, draw scenario, set-aside check, free cash, renewal costs, time-off test, cash cushion, fixed costs and an accountant pack check. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the owner-doula, doulas, backup doulas, the admin, the accountant and the insurer.\n\n"
        "This is part eight of the Doula Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Clients appear by name only and no medical detail is recorded. It helps you keep track of hours, dates, money and capacity and does not promise any result. Check your local rules for records, insurance and tax."),
    "features": ["Uneven-month cash forecast with best and worst case", "Owner pay and tax set-aside check", "Profit and loss with margin and cost per birth", "Budget vs actual by category and month", "Unearned cash on every contract",
                 "Renewals and training with red and amber dates", "Compare every figure with your own history", "Year-end summary and next-year plan", f"{len(tools)} decision tools with a verdict",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
def _cut(x, n):
    if len(x) <= n: return x
    y = x[:n - 1]
    for sep in ('. ', '; ', ': ', ', '):
        i = y.rfind(sep)
        if i > n * 0.55: return y[:i].rstrip() + '.'
    return y[:y.rfind(' ')].rstrip(' ,;:') + '.'
for _t in tables + tools:
    _t['hint'] = _cut(_t['hint'], 200); _t['title'] = _cut(_t['title'], 60).rstrip('.')
for _f in forms: _f['title'] = _cut(_f['title'], 50).rstrip('.')
s = spec(id=f'{SUITE}-p8', slug='doula-business-money', profession='Doula Business', name='Money, Owner Pay and Renewals',
         tagline='Cash forecast, owner pay, set-aside and renewals for your doula business', price_usd=29,
         colors={"primary": "#4A3F6B", "accent": "#E8A87C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Money, owner pay, renewals and year plan"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'du8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
