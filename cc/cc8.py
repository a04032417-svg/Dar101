"""Home Daycare and Childcare Center suite - part 8: Business Health and Planning."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc8_lists import *
from cc8_tables import settings, tables, MS, WN, SN, BYM, RT
from cc8_tools import tools
import cc8_data as D

SUITE = 'fx-20261115-childcare-center'
NOTE = "Sample wording: adapt it to your own center and check your local rules."
YES = '{list:yesno.yes}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)


# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('budget_month', 'Monthly Budget Sheet', 'Budget against actual for one category and month', 'budget.budget_id', F(
        ('Category', 'budget.category'), ('Month', 'budget.month'), ('Budget', 'budget.budget'), ('Actual', 'budget.actual'), ('Variance, over is positive', 'budget.variance'), ('Variance share of budget', 'budget.var_pct'),
        ('Budget check', 'budget.flag'), ('Accountant phone', 'budget.accountant_phone')) + [
        FF('Variance that needs a look', '{set:variance_pct}*%s' % LK('budget', 'budget_id', 'budget'), 'money'),
        FF('Category actual, 12 months', LK('budget', 'budget_id', 'cat_actual'), 'money'), FF('Category rank by overspend', LK('budget', 'budget_id', 'rank_over'), 'int')]),
    FORM('budget_year', 'Annual Budget Sheet', 'Annual budget for one expense category', 'budget.budget_id', F(
        ('Category', 'budget.category'), ('Category budget, 12 months', 'budget.cat_budget'), ('Category actual, 12 months', 'budget.cat_actual'), ('Category variance, 12 months', 'budget.cat_var'),
        ('Category last year, same months', 'budget.cat_last'), ('Rank by overspend', 'budget.rank_over'), ('Rank by spend', 'budget.rank_spend')) + [
        FF('Monthly budget at this spend', '%s/12' % LK('budget', 'budget_id', 'cat_actual'), 'money'),
        FF('Change against last year, same months', 'IFERROR(%s/%s-1,0)' % (LK('budget', 'budget_id', 'cat_actual_11'), LK('budget', 'budget_id', 'cat_last')), 'pct')]),
    FORM('fee_review', 'Fee Review Sheet', 'Fee review for one room and schedule', 'rates.rate_id', F(
        ('Room', 'rates.room'), ('Schedule', 'rates.schedule'), ('Weekly rate', 'rates.weekly_rate'), ('Last year rate', 'rates.last_year_rate'), ('Rise this year', 'rates.rise_pct'), ('Rate per child-hour', 'rates.child_hour_rate'),
        ('Cost per child-hour of the room', 'rates.cost_per_hour'), ('Weekly rate for your wanted margin', 'rates.needed_rate'), ('Rise needed', 'rates.rise_needed'), ('Fee check', 'rates.fee_flag'), ('Fee review date', 'rates.review_date')) + [
        FF('Needed weekly rate, whole amount', 'ROUND(%s,0)' % LK('rates', 'rate_id', 'needed_rate'), 'money'), FF('Needed monthly rate, whole amount', 'ROUND(%s*52/12,0)' % LK('rates', 'rate_id', 'needed_rate'), 'money')]),
    FORM('scenario_request', 'Scenario Request Sheet', 'Scenario with the profit change a month', 'scenarios.scenario', F(
        ('Scenario', 'scenarios.scenario'), ('Room', 'scenarios.room'), ('Children change', 'scenarios.children_change'), ('Staff hours change a month', 'scenarios.staff_hours_change'), ('Revenue change', 'scenarios.revenue_change'),
        ('Staff cost change', 'scenarios.staff_change'), ('Food cost change', 'scenarios.food_change'), ('Profit change a month', 'scenarios.profit_change'), ('Profit a month after', 'scenarios.profit_after'), ('Scenario check', 'scenarios.flag')) + [
        FF('Profit change a year', '12*%s' % LK('scenarios', 'scenario', 'profit_change'), 'money'),
        FF('Share of your profit a month now', 'IFERROR(%s/(%s-%s),0)' % (LK('scenarios', 'scenario', 'profit_change'), LK('scenarios', 'scenario', 'profit_after'), LK('scenarios', 'scenario', 'profit_change')), 'pct')]),
    FORM('draw_sheet', 'Owner Draw Sheet', 'Owner draw and cash left for one month', 'draw_plan.no', F(
        ('Month', 'draw_plan.month'), ('Profit before the draw', 'draw_plan.forecast'), ('Owner draw', 'draw_plan.draw'), ('Profit after the draw', 'draw_plan.profit_after'), ('Tax set-aside', 'draw_plan.set_aside'),
        ('Extra draw', 'draw_plan.extra_draw'), ('Cash change', 'draw_plan.net_cash'), ('Cash left', 'draw_plan.cash_left'), ('Cash check', 'draw_plan.floor_flag')) + [
        FF('Cash left above your floor', '%s-{set:cash_floor}' % LK('draw_plan', 'no', 'cash_left'), 'money'), FF('Months of draw the cash left covers', 'IFERROR(%s/{set:owner_draw},0)' % LK('draw_plan', 'no', 'cash_left'), 'num')]),
    FORM('tax_sheet', 'Tax Set-aside Sheet', 'Income tax set-aside for one month', 'tax.month', F(
        ('Month', 'tax.month'), ('Revenue', 'tax.revenue'), ('Costs', 'tax.costs'), ('Profit', 'tax.profit'), ('Set-aside share', 'tax.set_aside_pct'), ('Set aside', 'tax.set_aside'), ('Due date', 'tax.due_date'), ('Status', 'tax.status'),
        ('Accountant phone', 'tax.accountant_phone')) + [
        FF('Set aside so far this year', 'SUMIFS({range:tax.set_aside},{range:tax.month},">="&DATE(YEAR({pick}),1,1),{range:tax.month},"<="&{pick})', 'money'),
        FF('Still to pay, all months', 'SUM({range:tax.open_amount})', 'money')]),
    FORM('home_share', 'Home-use Share Sheet', 'Home-use share of one cost line', 'home_lines.line', F(
        ('Cost line', 'home_lines.line'), ('Whole-house amount a month', 'home_lines.amount'), ('Rule', 'home_lines.rule'), ('Set on', 'home_lines.set_on'), ('Adviser confirmed', 'home_lines.confirmed'), ('Business share', 'home_lines.share'),
        ('Business amount a month', 'home_lines.business_amount'), ('Business amount a year', 'home_lines.yearly_amount'), ('To confirm with your adviser', 'home_lines.status')) + [
        FF('Rooms share of the home', 'IFERROR({set:home_rooms_used}/{set:home_rooms_total},0)', 'pct'), FF('Hours share of the week', 'IFERROR({set:home_hours_used}/{set:home_hours_week},0)', 'pct')]),
    FORM('home_lines_sheet', 'Home-use Cost Lines Sheet', 'Home-use cost lines under one rule', 'home_lines.rule', F(
        ('Rule', 'home_lines.rule'), ('Business share under this rule', 'home_lines.share')) + [
        FF('Whole-house amount of these lines', 'SUMIFS({range:home_lines.amount},{range:home_lines.rule},%s)' % LK('home_lines', 'rule', 'rule'), 'money'),
        FF('Business amount a month of these lines', 'SUMIFS({range:home_lines.business_amount},{range:home_lines.rule},%s)' % LK('home_lines', 'rule', 'rule'), 'money'),
        FF('Lines confirmed with your adviser', 'COUNTIFS({range:home_lines.rule},%s,{range:home_lines.confirmed},%s)' % (LK('home_lines', 'rule', 'rule'), YES), 'int'),
        FF('All lines, business amount a month', 'SUM({range:home_lines.business_amount})', 'money')],
        {"from": "home_lines", "match": "home_lines.rule", "columns": ["line", "amount", "share", "business_amount", "status"], "max": 12}),
    FORM('equipment_sheet', 'Equipment Purchase Sheet', 'Equipment purchase against cash and budget', 'expenses.expense_id', F(
        ('Date', 'expenses.date'), ('Category', 'expenses.category'), ('Description', 'expenses.description'), ('Amount', 'expenses.amount'), ('Paid to', 'expenses.paid_to'), ('Share of the category, 12 months', 'expenses.share_of_category')) + [
        FF('Cash at the end of last month', 'IFERROR(INDEX({range:cash.closing},MATCH(EDATE(%s,-1),{range:cash.month},0)),0)' % MS, 'money'),
        FF('Cash after this purchase', 'IFERROR(INDEX({range:cash.closing},MATCH(EDATE(%s,-1),{range:cash.month},0)),0)-%s' % (MS, LK('expenses', 'expense_id', 'amount')), 'money'),
        FF('Cash after the purchase above your floor', 'IFERROR(INDEX({range:cash.closing},MATCH(EDATE(%s,-1),{range:cash.month},0)),0)-%s-{set:cash_floor}' % (MS, LK('expenses', 'expense_id', 'amount')), 'money'),
        FF('Months of the category budget it uses', 'IFERROR(%s/AVERAGEIFS({range:budget.budget},{range:budget.category},%s),0)' % (LK('expenses', 'expense_id', 'amount'), LK('expenses', 'expense_id', 'category')), 'num')]),
    FORM('expense_review', 'Expense Review Sheet', 'Expense against the category budget', 'expenses.expense_id', F(
        ('Date', 'expenses.date'), ('Category', 'expenses.category'), ('Description', 'expenses.description'), ('Amount', 'expenses.amount'), ('Category check', 'expenses.category_flag'), ('Accountant phone', 'expenses.accountant_phone')) + [
        FF('Spend in this category, 12 months', 'SUMIFS({range:expenses.amount},{range:expenses.category},%s,{range:expenses.month},">="&EDATE(%s,-12))' % (LK('expenses', 'expense_id', 'category'), MS), 'money'),
        FF('Budget of this category, 12 months', 'SUMIFS({range:budget.budget},{range:budget.category},%s)' % LK('expenses', 'expense_id', 'category'), 'money'),
        FF('Entries in this category, 12 months', 'COUNTIFS({range:expenses.category},%s,{range:expenses.month},">="&EDATE(%s,-12))' % (LK('expenses', 'expense_id', 'category'), MS), 'int'),
        FF('Expenses without a category, all rows', 'COUNTIFS({range:expenses.category_flag},%s)' % V('No category'), 'int')]),
    FORM('room_review', 'Room Profit Review Sheet', 'Profit review for one room and month', 'room_months.row_id', F(
        ('Room', 'room_months.room'), ('Month', 'room_months.month'), ('Children enrolled', 'room_months.enrolled'), ('Licensed places', 'room_months.capacity'), ('Occupancy', 'room_months.occupancy'), ('Revenue', 'room_months.revenue'),
        ('Staff cost', 'room_months.staff_cost'), ('Food cost', 'room_months.food_cost'), ('Overhead share', 'room_months.overhead_share'), ('Profit', 'room_months.profit'), ('Children still needed to break even', 'room_months.to_break_even'),
        ('Room profit, 12 months', 'room_months.room_profit_12m'), ('Room result', 'room_months.result')) + [
        FF('Profit under the capacity rule', LK('room_months', 'row_id', 'profit_cap'), 'money'), FF('Profit under the children rule', LK('room_months', 'row_id', 'profit_child'), 'money')]),
    FORM('year_end_sheet', 'Year-End Review Sheet', 'Year-end review of one measure', 'year_review.review_id', F(
        ('Review period', 'year_review.basis'), ('Measure', 'year_review.measure'), ('This period', 'year_review.this_period'), ('Period before', 'year_review.last_period'), ('Change', 'year_review.change'), ('Change, share', 'year_review.change_pct'),
        ('Verdict', 'year_review.verdict')) + [
        FF('Measures stronger in this review period', 'COUNTIFS({range:year_review.basis},%s,{range:year_review.verdict},%s)' % (LK('year_review', 'review_id', 'basis'), V('Stronger')), 'int'),
        FF('Measures weaker in this review period', 'COUNTIFS({range:year_review.basis},%s,{range:year_review.verdict},%s)' % (LK('year_review', 'review_id', 'basis'), V('Weaker')), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('owner_summary', 'Monthly Owner Summary', 'Monthly owner summary of profit and cash', 'pnl.month', [
        'Monthly owner summary of {set:company}, dated {today}. Month: {col:pnl.month}.',
        'Revenue {col:pnl.revenue} (tuition {col:pnl.tuition_revenue}, fees {col:pnl.fee_revenue}). Costs {col:pnl.costs}: staff pay {col:pnl.staff_pay}, owner pay {col:pnl.owner_pay}, food {col:pnl.food}, rent {col:pnl.rent}, other costs {col:pnl.other_costs}.',
        'Profit {col:pnl.profit}, a margin of {col:pnl.margin}. Month result: {col:pnl.result}. Staff pay is {col:pnl.staff_share} of revenue against your limit of {set:staff_share_target}. Rent is {col:pnl.rent_share} of revenue and food is {col:pnl.food_share}.',
        'Paid staff hours {col:pnl.staff_hours}, child-days attended {col:pnl.child_days}, food cost per child-day {col:pnl.food_per_day}. Write what you will change next month below.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('room_report', 'Room Profit Report', 'Profit report for one room and month', 'room_months.row_id', [
        'Room profit report of {set:company}, dated {today}. Room: {col:room_months.room}. Month: {col:room_months.month}.',
        'Children enrolled {col:room_months.enrolled} of {col:room_months.capacity} places, an occupancy of {col:room_months.occupancy}. Revenue {col:room_months.revenue}.',
        'Staff cost {col:room_months.staff_cost}, food cost {col:room_months.food_cost}, overhead share {col:room_months.overhead_share}. Cost {col:room_months.cost}. Profit {col:room_months.profit}, a margin of {col:room_months.margin}.',
        'Room profit over the last 12 months: {col:room_months.room_profit_12m}. Result: {col:room_months.result}. Children still needed to break even this month: {col:room_months.to_break_even}. Profit under the capacity rule {col:room_months.profit_cap} and under the children rule {col:room_months.profit_child}.'], ['Owner-director', 'Lead teacher'], NOTE),
    DOC('scenario_summary', 'Break-even and Scenario Summary', 'Break-even and scenario summary', 'scenarios.scenario', [
        'Scenario summary of {set:company}, dated {today}. Scenario: {col:scenarios.scenario}, room {col:scenarios.room}.',
        'Children change {col:scenarios.children_change}, staff hours change a month {col:scenarios.staff_hours_change}. Revenue change {col:scenarios.revenue_change}, food cost change {col:scenarios.food_change}, staff cost change {col:scenarios.staff_change}.',
        'Profit change a month {col:scenarios.profit_change}. Profit a month after the change {col:scenarios.profit_after}. Scenario check: {col:scenarios.flag}.', 'The figures use your own last 3 months and are a planning aid, not a promise. Write your decision below.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('fee_report', 'Fee Check Report', 'Fee check report for one room and schedule', 'rates.rate_id', [
        'Fee check report of {set:company}, dated {today}. Room {col:rates.room}, schedule {col:rates.schedule}, {col:rates.days} days of {col:rates.hours_day} hours.',
        'Weekly rate {col:rates.weekly_rate}, last year {col:rates.last_year_rate}, a rise of {col:rates.rise_pct}. Rate per child-hour {col:rates.child_hour_rate}. Cost per child-hour of the room {col:rates.cost_per_hour}.',
        'Weekly rate that earns your wanted margin of {set:margin_target}: {col:rates.needed_rate}. Rise needed: {col:rates.rise_needed}. Fee check: {col:rates.fee_flag}.',
        'Fee review date {col:rates.review_date}. Fees are before any tax. Write the rate you decide below.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('budget_report', 'Budget against Actual Report', 'Budget against actual for one category', 'budget.budget_id', [
        'Budget against actual of {set:company}, dated {today}. Category {col:budget.category}, month {col:budget.month}.',
        'Budget {col:budget.budget}, actual {col:budget.actual}, variance {col:budget.variance}, which is {col:budget.var_pct} of the budget. Budget check: {col:budget.flag}.',
        'Over the last 12 months this category had a budget of {col:budget.cat_budget} and an actual of {col:budget.cat_actual}, a variance of {col:budget.cat_var}. It ranks {col:budget.rank_over} for overspend and {col:budget.rank_spend} for spend.',
        'Write below what you will check or change.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('draw_plan_doc', 'Owner Draw and Set-aside Plan', 'Owner draw and tax set-aside plan for one month', 'draw_plan.no', [
        'Owner draw and set-aside plan of {set:company}, dated {today}. Month: {col:draw_plan.month}.',
        'Profit before the draw {col:draw_plan.forecast}. Owner draw {col:draw_plan.draw}. Profit after the draw {col:draw_plan.profit_after}. Income tax set-aside {col:draw_plan.set_aside}. Extra draw {col:draw_plan.extra_draw}.',
        'Cash change {col:draw_plan.net_cash}. Cash left {col:draw_plan.cash_left}, against your floor of {set:cash_floor}. Cash check: {col:draw_plan.floor_flag}.',
        'The set-aside is a planning figure. Please confirm tax amounts and dates with your adviser. Check your local rules.'], ['Owner-director', 'Accountant'], NOTE),
    DOC('home_doc', 'Home-use Share Worksheet', 'Home-use share worksheet for one cost line', 'home_lines.line', [
        'Home-use share worksheet of {set:company}, dated {today}. Cost line: {col:home_lines.line}.',
        'Whole-house amount a month {col:home_lines.amount}. Rule: {col:home_lines.rule}. Business share {col:home_lines.share}. Business amount a month {col:home_lines.business_amount}, a year {col:home_lines.yearly_amount}.',
        'The rooms used for the business are {set:home_rooms_used} of {set:home_rooms_total}, used {set:home_hours_used} hours of {set:home_hours_week} hours a week. Set on {col:home_lines.set_on}. Status: {col:home_lines.status}.',
        'This worksheet turns rooms or hours into cost lines. It does not decide what you may claim: please confirm every line with your adviser and check your local rules.'], ['Provider', 'Adviser'], NOTE),
    DOC('year_doc', 'Year in Review Report', 'Year in review for one measure', 'year_review.review_id', [
        'Year in review of {set:company}, dated {today}. Review period: {col:year_review.basis}.',
        'Measure: {col:year_review.measure}. This period {col:year_review.this_period}. Period before {col:year_review.last_period}. Change {col:year_review.change}, which is {col:year_review.change_pct} of the period before.',
        'Verdict: {col:year_review.verdict}. A change within {set:steady_band} counts as steady. Costs and staff pay share are better when they fall.', 'Write below what you keep, what you change and what you plan for the next period.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('accountant_pack', 'Accountant Pack', 'Accountant pack with profit and loss and cash for one month', 'cash.month', [
        'Accountant pack of {set:company}, dated {today}. Month: {col:cash.month}. Prepared for {col:cash.accountant}.',
        'Cash: opening {col:cash.opening}, parent payments {col:cash.parent_payments}, government payments {col:cash.government_payments}, pay out {col:cash.pay_out}, expenses out {col:cash.expenses_out}, income tax set aside {col:cash.tax_set_aside}, deposit refunds {col:cash.deposit_refunds}, owner extra draw {col:cash.owner_extra}.',
        'Closing cash {col:cash.closing}, a change of {col:cash.net_change} in the month and {col:cash.above_floor} above your floor. Cash check: {col:cash.floor_flag}.',
        'Attach the monthly profit and loss, the expense list and the bills due. Please confirm tax treatment and dates with your adviser.'], ['Owner-director', 'Accountant'], NOTE),
    DOC('equipment_case', 'Equipment Purchase Case', 'Equipment purchase case for one expense', 'expenses.expense_id', [
        'Equipment purchase case of {set:company}, dated {today}. Expense {col:expenses.expense_id} on {col:expenses.date}.',
        'Item: {col:expenses.description}. Category: {col:expenses.category}. Amount: {col:expenses.amount}. Paid to: {col:expenses.paid_to}. This is {col:expenses.share_of_category} of the spend in this category over 12 months.',
        'Reason for the purchase, the extra places or the saving it brings, and the months to pay back: write them below. Cash must stay above your floor of {set:cash_floor}.', 'Decision: buy now, wait or decline.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('annual_plan', 'Annual Plan for the Next Year', 'Annual plan with break-even and occupancy by month', 'breakeven.month', [
        'Annual plan of {set:company}, dated {today}. Month used as the base: {col:breakeven.month}.',
        'Children enrolled {col:breakeven.children} of {col:breakeven.places} places, an occupancy of {col:breakeven.occupancy}. Fixed costs {col:breakeven.fixed_costs}. Revenue per child {col:breakeven.revenue_child}. Food cost per child {col:breakeven.variable_child}.',
        'Break-even children {col:breakeven.be_children}, a break-even occupancy of {col:breakeven.be_occupancy}. Cushion over break-even {col:breakeven.cushion}. Check: {col:breakeven.position}.',
        'Write below the occupancy you plan, the fee changes, the budget and the owner draw for the next year.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('fee_note', 'Fee Setting Note', 'Fee setting note for a room and schedule', 'rates.rate_id', [
        'Fee note of {set:company}, dated {today}. Room {col:rates.room}, schedule {col:rates.schedule}.',
        'The weekly rate is {col:rates.weekly_rate} and the weekly rate for your wanted margin is {col:rates.needed_rate}. A rise of {col:rates.rise_needed} would reach it. Last year the rate rose by {col:rates.rise_pct}.',
        'Notice of a fee rise is given to families in writing before it starts: check your contract terms and your local rules. The yearly fee review is on {col:rates.review_date}.', 'Fees are before any tax. Write the new rate and the date it starts below.'], ['Owner-director', 'Family'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('owner_review', 'Monthly Owner Review Steps', 'pnl', 'pnl.month', [('Open Profit and Loss and read the month result', 1), ('Compare occupancy with the target', 2), ('Check the staff pay share against your limit', 2), ('Read the room with the lowest profit', 3), ('Check cash against your floor', 3), ('Write the three actions for next month', 5)]),
    CHK('month_end', 'Month-End Figures Check Steps', 'pnl', 'pnl.month', [('Enter tuition and fee revenue', 1), ('Enter staff pay, owner pay and paid hours', 2), ('Enter food, rent and other costs', 3), ('Categorise every expense', 3), ('Check that bills due are listed', 4), ('Compare the totals with the bank balance', 5), ('Send the figures to the accountant', 6)]),
    CHK('room_review_chk', 'Room Profit Review Steps', 'room_months', 'room_months.month', [('List profit by room for the month', 3), ('Mark any room with a loss', 3), ('Count the children needed to break even', 4), ('Check the overhead rule with another rule', 5), ('Decide: fill, reprice or change staffing', 7), ('Tell the lead teacher the room result', 8)]),
    CHK('fee_review_chk', 'Fee Review Steps', 'rates', 'rates.reviewed_on', [('Compare each weekly rate with the rate for your wanted margin', 30), ('Check the cost per child-hour of each room', 30), ('Decide the new rates', 45), ('Check the notice families need: your contract and local rules', 45), ('Write to families with the notice', 60), ('Update the Rates sheet from the start date', 90)]),
    CHK('annual_budget_chk', 'Annual Budget Steps', 'budget', 'budget.month', [('Copy the actual of each category', 0), ('Add known changes such as rent or insurance', 7), ('Set the budget of each category', 10), ('Check the total against expected revenue', 12), ('Review with the accountant', 14), ('Fix the budget for the year', 20)]),
    CHK('tax_check', 'Tax Set-aside Check Steps', 'tax', 'tax.due_date', [('Add the set-aside of each month in the quarter', -30), ('Check profit with the accountant', -21), ('Confirm the amount with your adviser', -14), ('Move the amount to a separate account', -7), ('Pay on the due date', 0), ('Write the date paid in the sheet', 1)]),
    CHK('draw_decision', 'Owner Draw Decision Steps', 'cash', 'cash.month', [('Read the closing cash and the cash floor', 5), ('Read profit after set-aside', 5), ('Test the extra quarterly draw', 6), ('Check that cash stays above the floor', 6), ('Decide the draw for the next quarter', 8), ('Write the decision in the notes', 9)]),
    CHK('home_setup', 'Home-use Share Set-up Steps', 'home_lines', 'home_lines.set_on', [('List the rooms used for the business', 0), ('Count the hours a week they are used', 0), ('Choose a rule for each cost line', 3), ('Enter the whole-house amounts', 5), ('Ask your adviser to confirm each line', 14), ('Mark the lines as confirmed', 21)]),
    CHK('year_end_chk', 'Year-End Review Steps', 'breakeven', 'breakeven.month', [('Open Year in Review', 1), ('Read each measure and its verdict', 2), ('Note the three strongest and the three weakest measures', 3), ('Compare occupancy with break-even occupancy', 4), ('Write what you keep and what you change', 7), ('Share the review with the assistant director', 8)]),
    CHK('equip_chk', 'Equipment Decision Steps', 'expenses', 'expenses.date', [('Get two quotes', -14), ('Enter the cost and the extra places or the saving', -10), ('Check the payback in months', -10), ('Check cash after the purchase against the floor', -7), ('Decide: buy or wait', -5), ('Record the purchase in Expenses', 0)]),
    CHK('accountant_meeting', 'Accountant Meeting Steps', 'bills', 'bills.due_date', [('Print the profit and loss and the cash sheet', -7), ('List the expenses without a category and fix them', -6), ('Print the home-use share lines', -5), ('Write your questions about spend and set-aside', -3), ('Bring the bills still unpaid', -1), ('Write the answers after the meeting', 1)]),
    CHK('annual_plan_chk', 'Annual Plan Steps', 'staff_share', 'staff_share.month', [('Read the year in review', 1), ('Set the wanted occupancy and margin', 5), ('Set the fee changes', 10), ('Set the budget by category', 14), ('Plan the owner draw and the set-aside', 20), ('Write the plan and share it with the team', 25)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('o_profit', 'Owner: this month profit', 'pnl', 'pnl.owner_phone', 'Hello {owner}, profit for {month} is {profit} on revenue of {revenue}, a margin of {margin}. {center}'),
    M('o_occ', 'Owner: occupancy against the target', 'occupancy', 'occupancy.owner_phone', 'Hello {owner}, occupancy for {month} is {occupancy} against your target of {target}. Children needed to reach it: {children_to_target}. {center}'),
    M('o_staff', 'Owner: staff pay share against the limit', 'staff_share', 'staff_share.owner_phone', 'Hello {owner}, staff pay is {share} of revenue for {month} against your limit of {target}. Check: {flag}. {center}'),
    M('o_roomloss', 'Owner: a room result', 'room_months', 'room_months.owner_phone', 'Hello {owner}, the {room} room made {profit} in {month} on revenue of {revenue}. Result: {result}. {center}'),
    M('o_infants', 'Owner: children needed to break even', 'room_months', 'room_months.owner_phone', 'Hello {owner}, the {room} room needs {to_break_even} more children to break even, with {enrolled} children in {capacity} places in {month}. {center}'),
    M('o_be', 'Owner: break-even occupancy', 'breakeven', 'breakeven.owner_phone', 'Hello {owner}, break-even occupancy for {month} is {be_occupancy}, about {be_children} children. Your occupancy was {occupancy}. {center}'),
    M('o_fee', 'Owner: fee check by room', 'cost_hour', 'cost_hour.owner_phone', 'Hello {owner}, fee check for {room} in {month}: fee {fee_per_hour} and cost {cost_per_hour} per child-hour, short by {low_by}. {center}'),
    M('o_budget', 'Owner: budget variance', 'budget', 'budget.owner_phone', 'Hello {owner}, {category} in {month}: budget {budget}, actual {actual}, variance {variance}. Check: {flag}. {center}'),
    M('o_cash', 'Owner: cash against the floor', 'cash', 'cash.owner_phone', 'Hello {owner}, cash at the end of {month} is {closing}, {above_floor} above your floor. Check: {floor_flag}. {center}'),
    M('o_setaside', 'Owner: monthly tax set-aside', 'tax', 'tax.owner_phone', 'Hello {owner}, the income tax set-aside for {month} is {set_aside}, due {due_date}. Please confirm with your adviser. Status: {status}. {center}'),
    M('o_draw', 'Owner: your draw this month', 'draw_plan', 'draw_plan.owner_phone', 'Hello {owner}, your draw for {month} is {draw}. Profit after the draw is {profit_after} and cash left is {cash_left}. {center}'),
    M('o_year', 'Owner: your year in review is ready', 'year_review', 'year_review.owner_phone', 'Hello {owner}, your year in review is ready: {measure} was {this_period} against {last_period}. Verdict: {verdict}. {center}'),
    M('o_fee_due', 'Owner: fee review is due', 'rates', 'rates.owner_phone', 'Hello {owner}, your fee review is due on {review_date}. {room} {schedule} is {weekly_rate} a week; the rate for your wanted margin is {needed_rate}. {center}'),
    M('o_scn', 'Owner: a scenario result', 'scenarios', 'scenarios.owner_phone', 'Hello {owner}, the scenario "{scenario}" changes profit by {profit_change} a month, to {profit_after}. Check: {flag}. {center}'),
    M('o_extra', 'Owner: the extra quarterly draw', 'draw_plan', 'draw_plan.owner_phone', 'Hello {owner}, the extra draw of {extra_draw} in {month} leaves cash at {cash_left}. Check: {floor_flag}. {center}'),
    M('o_home', 'Owner: home-use share', 'home_lines', 'home_lines.owner_phone', 'Hello {owner}, the business share of {line} is {share}, which is {business_amount} a month. Status: {status}. {center}'),
    M('o_rent', 'Owner: rent against revenue', 'pnl', 'pnl.owner_phone', 'Hello {owner}, rent is {rent} in {month}, {rent_share} of revenue of {revenue}. {center}'),
    M('o_food', 'Owner: food cost per child-day', 'pnl', 'pnl.owner_phone', 'Hello {owner}, food cost per child-day in {month} is {food_per_day} on {child_days} child-days. {center}'),
    M('ad_figures', 'Assistant director: figures to check', 'pnl', 'pnl.director_phone', 'Hello {director}, please check the figures for {month} before month end: revenue {revenue}, costs {costs}, profit {profit}. {center}'),
    M('ad_pay', 'Assistant director: payments to check', 'cash', 'cash.director_phone', 'Hello {director}, for the owner summary of {month}: parent payments {parent_payments}, government payments {government_payments}, closing cash {closing}. {center}'),
    M('ad_nocat', 'Assistant director: categorise expense', 'expenses', 'expenses.director_phone', 'Hello {director}, the expense {description} of {amount} on {date} needs a category. Check: {category_flag}. {center}'),
    M('ad_bills', 'Assistant director: bills due', 'bills', 'bills.director_phone', 'Hello {director}, bill {bill_id} for {category} of {amount} to {paid_to} is due {due_date}. Status: {status}. {center}'),
    M('ac_pnl', 'Accountant: monthly profit and loss', 'pnl', 'pnl.accountant_phone', 'Hello {accountant}, the profit and loss for {month}: revenue {revenue}, costs {costs}, profit {profit}. {center}'),
    M('ac_cash', 'Accountant: cash and set-aside', 'cash', 'cash.accountant_phone', 'Hello {accountant}, cash for {month}: closing {closing}, income tax set aside {tax_set_aside}. Please confirm the treatment. {center}'),
    M('ac_year', 'Accountant: year-end pack is ready', 'year_review', 'year_review.accountant_phone', 'Hello {accountant}, the year-end pack is ready: {measure} was {this_period} against {last_period}. {center}'),
    M('ac_cat', 'Accountant: question about a category', 'expenses', 'expenses.accountant_phone', 'Hello {accountant}, a question about {category} spend: {description}, {amount} on {date}. {center}'),
    M('ac_home', 'Accountant: home-use share figures', 'home_lines', 'home_lines.accountant_phone', 'Hello {accountant}, please review the home-use share of {line}: {business_amount} a month at a share of {share}. {center}'),
    M('ac_equip', 'Accountant: equipment purchase', 'expenses', 'expenses.accountant_phone', 'Hello {accountant}, an equipment purchase of {amount} on {date}: {description}. Please advise on how to book it. {center}'),
    M('fs_fees', 'Food supplier: fees under review', 'bills', 'bills.supplier_phone', 'Hello {paid_to}, our fees for next year are under review. Your bill {bill_id} of {amount} is due {due_date}. Please send your price list. {center}'),
    M('cl_cost', 'Cleaner: cleaning cost under review', 'bills', 'bills.supplier_phone', 'Hello {paid_to}, the cleaning cost for next year is under review. Your bill {bill_id} of {amount} is due {due_date}. Please send a quote. {center}'),
    M('mt_repair', 'Maintenance contact: repair estimate', 'expenses', 'expenses.maint_phone', 'Hello {maintenance}, please send a repair estimate for {description}, last paid {amount} on {date}. {center}'),
    M('mt_equip', 'Maintenance contact: equipment purchase', 'expenses', 'expenses.maint_phone', 'Hello {maintenance}, an equipment purchase was recorded on {date}: {description}. Can you check the fit? {center}'),
    M('lt_room', 'Lead teacher: your room results', 'room_months', 'room_months.teacher_phone', 'Hello {lead_teacher}, your room {room} in {month}: {enrolled} children, occupancy {occupancy}, profit {profit}. {center}'),
    M('lt_supplies', 'Lead teacher: your supplies budget', 'room_months', 'room_months.teacher_phone', 'Hello {lead_teacher}, the supplies budget of your room {room} is {supplies_budget} a month. {center}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
PLACES = 'SUM({range:rooms.capacity})'
def PW(c, n): return SN('pnl', c, n)
FIX3 = '(%s+%s+%s+%s)/3' % (PW('staff_pay', 3), PW('owner_pay', 3), PW('rent', 3), PW('other_costs', 3))
BE3 = '(%s)*%s/(%s-%s)' % (FIX3, SN('room_months', 'enrolled', 3), PW('revenue', 3), PW('food', 3))
YD = 'YEAR(EDATE(%s,-1))' % MS
def YTDW(t, c, last=False):
    a, b = ('DATE(%s,1,1)' % YD, MS) if not last else ('DATE(%s-1,1,1)' % YD, 'EDATE(%s,-12)' % MS)
    return 'SUMIFS({range:%s.%s},{range:%s.month},">="&%s,{range:%s.month},"<"&%s)' % (t, c, t, a, t, b)
def THISM(t, c): return 'SUMIFS({range:%s.%s},{range:%s.month},%s)' % (t, c, t, MS)
kpis = [
    KPI('Revenue this month', THISM('pnl', 'revenue'), 'money'),
    KPI('Revenue last 12 months', PW('revenue', 12), 'money'),
    KPI('Costs this month', THISM('pnl', 'costs'), 'money'),
    KPI('Profit this month', THISM('pnl', 'profit'), 'money'),
    KPI('Profit last 12 months', PW('profit', 12), 'money'),
    KPI('Profit margin this month', 'IFERROR(%s/%s,0)' % (THISM('pnl', 'profit'), THISM('pnl', 'revenue')), 'pct'),
    KPI('Profit margin last 12 months', 'IFERROR(%s/%s,0)' % (PW('profit', 12), PW('revenue', 12)), 'pct'),
    KPI('Occupancy this month', THISM('occupancy', 'occupancy'), 'pct'),
    KPI('Occupancy last 12 months', 'IFERROR(%s/%s,0)' % (SN('room_months', 'enrolled', 12), SN('room_months', 'capacity', 12)), 'pct'),
    KPI('Break-even occupancy, last 3 months', 'IFERROR((%s)/%s,0)' % (BE3, PLACES), 'pct'),
    KPI('Break-even children, last 3 months', 'IFERROR(%s,0)' % BE3, 'num'),
    KPI('Months above break-even, last 12', 'COUNTIFS(%s,{range:breakeven.above},1)' % WN('breakeven', 12), 'int'),
    KPI('Staff pay share this month', THISM('staff_share', 'share'), 'pct'),
    KPI('Staff pay share last 12 months', 'IFERROR(%s/%s,0)' % (PW('staff_pay', 12), PW('revenue', 12)), 'pct'),
    KPI('Staff share gap to your limit, 12 months', 'IFERROR(%s/%s,0)-{set:staff_share_target}' % (PW('staff_pay', 12), PW('revenue', 12)), 'pct'),
    KPI('Cost per child-hour this month', 'IFERROR(%s/%s,0)' % (THISM('cost_hour', 'total_cost'), THISM('cost_hour', 'child_hours')), 'money'),
    KPI('Fee per child-hour this month', 'IFERROR(%s/%s,0)' % (THISM('cost_hour', 'revenue'), THISM('cost_hour', 'child_hours')), 'money'),
    KPI('Room with the best margin, 12 months', 'IFERROR(INDEX({range:room_months.room},MATCH(MAX({range:room_months.room_margin_12m}),{range:room_months.room_margin_12m},0)),"")', 'text'),
    KPI('Room with the worst margin, 12 months', 'IFERROR(INDEX({range:room_months.room},MATCH(MIN({range:room_months.room_margin_12m}),{range:room_months.room_margin_12m},0)),"")', 'text'),
    KPI('Costs last 12 months', 'SUMIFS({range:pnl.costs},%s)' % WN('pnl', 12), 'money'),
    KPI('Rent share of revenue, 12 months', 'IFERROR(%s/%s,0)' % (PW('rent', 12), PW('revenue', 12)), 'pct'),
    KPI('Food share of revenue, 12 months', 'IFERROR(%s/%s,0)' % (PW('food', 12), PW('revenue', 12)), 'pct'),
    KPI('Cash balance now', THISM('cash', 'closing'), 'money'),
    KPI('Months of cash at current costs', 'IFERROR(%s/((%s)/3),0)' % (THISM('cash', 'closing'), PW('costs', 3)), 'num'),
    KPI('Tax set aside this year', 'SUMIFS({range:tax.set_aside},{range:tax.month},">="&DATE(YEAR({today}),1,1),{range:tax.month},"<="&%s)' % MS, 'money'),
    KPI('Owner draw this year, with extra draws', 'SUMIFS({range:pnl.owner_pay},{range:pnl.month},">="&DATE(YEAR({today}),1,1),{range:pnl.month},"<="&%s)+SUMIFS({range:cash.owner_extra},{range:cash.month},">="&DATE(YEAR({today}),1,1),{range:cash.month},"<="&%s)' % (MS, MS), 'money'),
    KPI('Budget variance, last month', 'SUMIFS({range:budget.variance},{range:budget.month},EDATE(%s,-1))' % MS, 'money'),
    KPI('Biggest overspend category, 12 months', 'IFERROR(INDEX({range:budget.category},MATCH(1,{range:budget.rank_over},0)),"")', 'text'),
    KPI('Profit this year against last year', 'IFERROR(%s/%s-1,0)' % (YTDW('pnl', 'profit'), YTDW('pnl', 'profit', True)), 'pct'),
    KPI('Revenue this year against last year', 'IFERROR(%s/%s-1,0)' % (YTDW('pnl', 'revenue'), YTDW('pnl', 'revenue', True)), 'pct'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Owner Dashboard", "kpis": kpis,
    "monthly": {"title": "Revenue, costs and profit by month", "date": "pnl.month", "series": [
        {"label": "Revenue", "sum": "pnl.revenue", "date": "pnl.month"}, {"label": "Costs", "sum": "pnl.costs", "date": "pnl.month"}, {"label": "Profit", "sum": "pnl.profit", "date": "pnl.month"}]},
    "breakdowns": [{"title": "Revenue by room, last 12 months", "by": "rev_room.room", "value": "rev_room.revenue", "agg": "sum"}, {"title": "Profit by room, 2 years", "by": "room_months.room", "value": "room_months.profit", "agg": "sum"},
                   {"title": "Expenses by category", "by": "expenses.category", "value": "expenses.amount", "agg": "sum"}, {"title": "Pay by role", "by": "payroll.role", "value": "payroll.total", "agg": "sum"}]}
insights = {"filters": [{"label": "Room", "list": "room"}, {"label": "Expense category", "list": "expcat"}],
    "gauges": [
        {"title": "Occupancy of licensed places", "num": AGG('sum', 'occupancy', 'occupancy.children'), "den": AGG('sum', 'occupancy', 'occupancy.places')},
        {"title": "Months with staff pay within your limit", "num": AGG('count', 'staff_share', where=[('flag', '=', V('Staff share on target'))]), "den": AGG('count', 'staff_share')},
        {"title": "Profit margin, all months shown", "num": AGG('sum', 'pnl', 'pnl.profit'), "den": AGG('sum', 'pnl', 'pnl.revenue')},
        {"title": "Months with the wanted profit margin", "num": AGG('count', 'pnl', where=[('result', '=', V('On margin target'))]), "den": AGG('count', 'pnl')},
        {"title": "Months with cash above the floor", "num": AGG('count', 'cash', where=[('floor_flag', '=', V('Above the floor'))]), "den": AGG('count', 'cash')},
        {"title": "Room-months with a profit", "num": AGG('count', 'room_months', where=[('result', '=', V('Room earns'))]), "den": AGG('count', 'room_months')}],
    "charts": [
        CHART('Revenue per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.revenue', date='pnl.month', label='Revenue')]),
        CHART('Costs per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.costs', date='pnl.month', label='Costs')]),
        CHART('Profit per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.profit', date='pnl.month', label='Profit')]),
        CHART('Profit margin per month', 'line', 'month', [AGG('avg', 'pnl', 'pnl.margin', date='pnl.month', label='Profit margin')]),
        CHART('Revenue by room, last 12 months', 'bar', 'rev_room.room', [AGG('sum', 'rev_room', 'rev_room.revenue', label='Revenue')]),
        CHART('Profit by room, 2 years', 'bar', 'room_months.room', [AGG('sum', 'room_months', 'room_months.profit', label='Profit')]),
        CHART('Occupancy by room, 2 years', 'bar', 'room_months.room', [AGG('avg', 'room_months', 'room_months.occupancy', label='Occupancy')]),
        CHART('Occupancy per month against the target', 'line', 'month', [AGG('avg', 'occupancy', 'occupancy.occupancy', date='occupancy.month', label='Occupancy'), AGG('avg', 'occupancy', 'occupancy.target', date='occupancy.month', label='Target')]),
        CHART('Staff pay share per month against your limit', 'line', 'month', [AGG('avg', 'staff_share', 'staff_share.share', date='staff_share.month', label='Staff pay share'), AGG('avg', 'staff_share', 'staff_share.target', date='staff_share.month', label='Your limit')]),
        CHART('Cost per child-hour by room', 'bar', 'cost_hour.room', [AGG('avg', 'cost_hour', 'cost_hour.cost_per_hour', label='Cost per child-hour')]),
        CHART('Fee per child-hour by room', 'bar', 'cost_hour.room', [AGG('avg', 'cost_hour', 'cost_hour.fee_per_hour', label='Fee per child-hour')]),
        CHART('Budget and actual by category', 'bar', 'budget.category', [AGG('sum', 'budget', 'budget.budget', label='Budget'), AGG('sum', 'budget', 'budget.actual', label='Actual')]),
        CHART('Expenses by category', 'bar', 'expenses.category', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
        CHART('Food cost per child-day per month', 'line', 'month', [AGG('avg', 'pnl', 'pnl.food_per_day', date='pnl.month', label='Food per child-day')]),
        CHART('Staff pay per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.staff_pay', date='pnl.month', label='Staff pay')]),
        CHART('Break-even occupancy per month', 'line', 'month', [AGG('avg', 'breakeven', 'breakeven.be_occupancy', date='breakeven.month', label='Break-even occupancy'), AGG('avg', 'breakeven', 'breakeven.occupancy', date='breakeven.month', label='Occupancy')]),
        CHART('Scenarios by profit change a month', 'bar', 'scenarios.scenario', [AGG('sum', 'scenarios', 'scenarios.profit_change', label='Profit change a month')]),
        CHART('Cash balance per month', 'line', 'month', [AGG('sum', 'cash', 'cash.closing', date='cash.month', label='Closing cash')]),
        CHART('Tax set aside per month', 'column', 'month', [AGG('sum', 'tax', 'tax.set_aside', date='tax.month', label='Set aside')]),
        CHART('Child-days attended per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.child_days', date='pnl.month', label='Child-days')]),
        CHART('Owner pay per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.owner_pay', date='pnl.month', label='Owner pay')]),
        CHART('Government part of tuition per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.government_part', date='pnl.month', label='Government part')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

# ------------------------------------------------------------------ signature, competitors, guide, listing
def W(i): return tools[i]['sheet']
signature = [
    {"name": "Break-even and occupancy scenario", "why": "enrol two more infants, lose a family or open a part-time day and see the break-even children, the occupancy and the first month above break-even", "where": W(0)},
    {"name": "Cost per child-hour and fee check", "why": "the cost and the fee of every child-hour by room, the staff pay share against your own limit and a verdict on each fee", "where": W(1)},
    {"name": "Loss-making room finder", "why": "profit by room under the overhead rule you choose, the room that loses money and the children that would turn it positive", "where": W(2)},
    {"name": "Home-daycare mode and owner pay", "why": "turn rooms or hours into business cost lines, test one-room capacity and see if your draw is affordable after the set-aside", "where": W(3)},
    {"name": "Owner draw and tax set-aside planner", "why": "profit less set-aside less draw for the next 12 months with the quarterly extra draw and the lowest cash point against your floor", "where": W(4)},
    {"name": "Year in review against your own history", "why": "revenue, costs, profit, occupancy, staff pay share and cash this period against the one before, each marked stronger, steady or weaker", "where": W(5)},
    {"name": "Staff cost share gap solver", "why": "the revenue to add or the staff cost to cut that closes the gap to your own staff pay limit", "where": W(7)},
    {"name": "Budget variance ranker", "why": "categories ranked from the biggest overspend down, with the one to investigate first", "where": W(8)},
    {"name": "Fee needed to hold the margin", "why": "the weekly rate of each room that earns your wanted margin, worked out in closed form from the cost of a child-hour", "where": W(12)},
    {"name": "Sensitivity table", "why": "occupancy, wages and fee each moved up and down, with the input that moves profit most", "where": W(13)},
    {"name": "Cash runway", "why": "months the cash lasts if revenue drops by a share you choose, with a safe, watch or act-now verdict", "where": W(14)}]
competitors = [
    {"what": "free budget templates", "lacks": "list income and costs but never turn them into break-even children, cost per child-hour or a profit figure for each room"},
    {"what": "subscription childcare-management software", "lacks": "charge every month for reports that hide the overhead rule, so you cannot test whether a room really loses money"},
    {"what": "generic profit and loss spreadsheets", "lacks": "know revenue and costs but not rooms, places, ratios, child-hours, the staff pay share or a quarterly owner draw"},
    {"what": "accountant year-end reports", "lacks": "arrive months late and show last year, with no scenario for enrolling two more infants or losing a family"},
    {"what": "paper cash books", "lacks": "record what came in and out but give no cash floor, no runway and no set-aside plan for the next 12 months"}]
guide = [
    'Open Start and type your center name, your wanted occupancy, your staff pay limit, your wanted margin, your cash floor and your owner draw in the yellow cells. These are your own targets: check your local rules for anything the law sets.',
    'Check Rooms and Rates. They hold the licensed places, the ratio and the weekly rate of each room and schedule that the other sheets look up.',
    'Each month enter one row in Profit and Loss: tuition and fee revenue, staff pay, owner pay, food, rent, other costs, paid staff hours and child-days. Revenue, costs, profit and the shares fill in by themselves.',
    'Enter one row per room and month in Room Profit by Month: children, revenue, staff cost, food cost and the overhead share. Profit, occupancy and the children still needed to break even fill in.',
    'Enter the cash in and out each month in Cash by Month. The closing balance and the margin over your cash floor fill in by themselves.',
    'Enter every expense in Expenses with a category and every bill in Bills. Budget against Actual compares them with your budget; rows without a category show in the category check.',
    'Add the child-hours attended in Cost per Child-Hour. Fee Check by Room then shows the cost and the fee of a child-hour in each room.',
    'Use Break-even by Month, Occupancy by Month and Staff Cost Share to see where the center stands against your own targets.',
    'Read Tax Set-aside and Owner Draw Plan for the next 12 months. The set-aside is a planning figure: confirm tax amounts and dates with your adviser.',
    'A single home daycare provider fills Home-use Share Lines: choose rooms, hours or both for each cost line and ask your adviser to confirm. Keep one row in Rooms.',
    'Open Year in Review to see this period against the period before, with a verdict for each measure.',
    f'Use the {len(tools)} calculators to test break-even, fees, the loss-making room, your draw, the budget, sensitivity, cash runway and a new group of children.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the figures already written in.',
    'Read the Owner Dashboard and the charts every month: revenue, costs, profit, occupancy, staff pay share, cash and the room that loses money.']
listing = {"title": "Childcare Center Business Health Excel Template: Profit and Loss, Break-Even Occupancy, Room Profit, Cost per Child-Hour, Cash Flow",
    "headline": "Know which room earns, what break-even is and what you can draw",
    "tags": ["childcare", "daycare", "profit and loss", "break-even", "childcare finance", "excel template", "home daycare", "cash flow", "occupancy rate", "room profit", "owner draw", "budget tracker", "cost per child"],
    "description": ("Run the money side of a home daycare or childcare center in one Excel workbook. Built for an owner-director and an assistant director who want one clear view of profit, break-even and cash. "
        "Profit and Loss holds the month: tuition and fee revenue, staff pay, owner pay, food, rent and other costs, with profit, margin and the staff pay share worked out for you. Room Profit by Month shows revenue, staff cost, food cost and the overhead share of every room, so the room that loses money is easy to see and so are the children it needs to break even.\n\n"
        "Cost per Child-Hour and Fee Check by Room set the fee of a child-hour against its cost. Break-even by Month gives the break-even children and the break-even occupancy (children booked as a share of licensed places). Budget against Actual compares your budget with your expenses by category. Cash by Month, Tax Set-aside and the Owner Draw Plan show the cash, the income tax set-aside and your draw for the next 12 months, with a floor you choose. Year in Review sets this period against the one before and marks each measure stronger, steady or weaker.\n\n"
        f"{len(tools)} calculators answer the questions an owner asks: enrol two more infants or lose a family, is a fee right, which room loses, is the draw affordable, how long does cash last, is a new group worth opening. Home-use Share Lines help a single home daycare provider turn rooms or hours into cost lines. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the owner-director, the assistant director, the accountant, lead teachers and suppliers.\n\n"
        "This is part eight of the Home Daycare and Childcare Center suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Children appear by name, room and dates only, with no medical detail. It helps you keep track of your business and does not promise results. Confirm tax and set-aside figures with your adviser and check your local rules."),
    "features": ["Monthly profit and loss with margin and staff pay share", "Profit by room and the loss-making room finder", "Break-even children and occupancy by month", "Cost and fee per child-hour by room", "Budget against actual by category",
                 "Cash by month with your own floor", "Owner draw and tax set-aside plan", "Home-use share lines for a home daycare", "Year in review against your own history", f"{len(tools)} calculators with a verdict each",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
HINTS = {
 'pnl': 'One row per month: revenue and cost lines, paid staff hours and child-days; revenue, costs, profit, margin and the shares fill in by themselves.',
 'room_months': 'One row per room and month: children, revenue, staff, food and overhead share; occupancy, profit, children needed to break even and profit under 3 overhead rules fill in.',
 'cash': 'One row per month: opening balance, money in, pay and expenses out, tax set-aside and extra draws; the closing balance and the margin over your cash floor fill in.',
 'tax': 'One row per month: due date and date paid; revenue, costs and profit come from Profit and Loss, the set-aside (confirm with your adviser) and status fill in.',
 'expenses': 'One row per expense of the last 12 months: date, category, description, amount and who was paid; the category check shows rows still without a category.',
 'rates': 'One row per room and schedule: weekly rate this year and last, days and hours; the rate and cost per child-hour, the rate for your wanted margin and the rise needed fill in.',
 'occupancy': 'One row per month: places and children come from Room Profit by Month; occupancy, the gap to your target and the children needed to reach it fill in.',
 'scenarios': 'One row per scenario: room, children and staff hours added or cut; revenue, food and staff cost change and the profit change a month fill in from your last 3 months.',
 'breakeven': 'One row per month: fixed costs, food, revenue and children come from other sheets; break-even children and occupancy and the cushion fill in by themselves.',
 'budget': 'One row per category and month: your budget and last year; the actual comes from Expenses, the variance and the 12-month ranks fill in by themselves.',
 'home_lines': 'One row per home cost line for a home daycare: amount, rule (rooms, hours, both) and adviser confirmed; the business share and amount fill in.',
 'draw_plan': 'One row per month ahead: profit forecast from your own last 6 months; draw, set-aside (confirm with your adviser), extra draw and cash left fill in.',
 'year_review': 'One row per measure and review period: this period against the period before, the change and a stronger, steady or weaker verdict fill in.',
 'break_even': 'Pick a room, type children added or lost, a fee change, staff hours and fixed costs: see break-even children and occupancy and the first month above break-even.',
 'home_mode': 'For a home daycare: pick rooms, hours or both for the house share, type fee, staff and draw; see capacity (check your local rules) and if the draw is affordable.',
 'draw_tool': 'Pick Base, Best or Worst and type draw, extra draw and set-aside (confirm with your adviser): see the lowest cash in 12 months against your floor.',
 'new_group': 'Type places, fill, fee, ratio (check your local rules) and extra fixed costs of a new group: see children to break even, profit at your fill and a verdict.',
}
for _t in tables + tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
s = spec(id=f'{SUITE}-p8', slug='childcare-center-business', profession='Home Daycare and Childcare Center', name='Business Health and Planning',
         tagline='See which room earns, where break-even is and what you can safely draw', price_usd=29,
         colors={"primary": "#33658A", "accent": "#F6AE2D"}, settings=settings, lists=base_lists() + verdict_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Business health and planning"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']))
