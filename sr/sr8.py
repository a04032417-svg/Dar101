"""Short-term rental host suite - part 8: Unit Profit, Cash Flow and Growth."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr8_lists import *
from sr8_tables import settings, tables, MS, NXT, Y1, CASHNOW, VARN
from sr8_tools import tools

SUITE = 'fx-20261113-short-term-rental'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
forms = [
    FORM('expense_sheet', 'Expense Sheet', 'Expense with category and share of all costs', 'expenses.expense_id', F(
        ('Date', 'expenses.date'), ('Unit', 'expenses.unit'), ('Category', 'expenses.category'), ('Description', 'expenses.description'), ('Amount', 'expenses.amount'), ('Paid to', 'expenses.paid_to'), ('Month', 'expenses.month'),
        ('Accountant phone', 'expenses.accountant_phone')) + [
        FF('Expenses listed in this category', 'SUMIFS({range:expenses.amount},{range:expenses.category},INDEX({range:expenses.category},MATCH({pick},{range:expenses.expense_id},0)))', 'money'),
        FF('Share of all expenses listed', 'IFERROR(SUMIFS({range:expenses.amount},{range:expenses.category},INDEX({range:expenses.category},MATCH({pick},{range:expenses.expense_id},0)))/SUM({range:expenses.amount}),0)', 'pct')]),
    FORM('draw_sheet', 'Owner Draw Sheet', 'Owner draw with the safe limit of the month', 'draws.draw_id', F(
        ('Month', 'draws.month'), ('Amount drawn', 'draws.amount'), ('Reason', 'draws.reason'), ('Against the planned draw', 'draws.vs_plan'), ('Safe draw of the month', 'draws.safe'), ('Draw check', 'draws.draw_flag'), ('Host phone', 'draws.host_phone')) + [
        FF('Drawn this year', 'SUMIFS({range:draws.amount},{range:draws.month},">="&DATE(YEAR({today}),1,1),{range:draws.month},"<="&{today})', 'money'),
        FF('Planned draw per month', '{set:owner_draw}', 'money')]),
    FORM('taxset_sheet', 'Tax Set-aside Sheet', 'Income tax set-aside of one month', 'taxset.ts_id', F(
        ('Month', 'taxset.month'), ('Profit for tax', 'taxset.profit'), ('Set aside', 'taxset.set_aside'), ('Target set-aside', 'taxset.target'), ('Shortfall', 'taxset.shortfall'), ('Paid', 'taxset.paid_amount'), ('Balance held', 'taxset.balance'),
        ('Funding check', 'taxset.fund_flag'), ('Accountant phone', 'taxset.accountant_phone')) + [
        FF('Set aside, all months listed', 'SUM({range:taxset.set_aside})', 'money'), FF('Set-aside share of profit', '{set:tax_set_aside_pct}', 'pct')]),
    FORM('cash_sheet', 'Cash Check Sheet', 'Cash of one month with the floor check', 'cash.cash_id', F(
        ('Month', 'cash.month'), ('Opening cash', 'cash.opening'), ('Cash in', 'cash.cash_in'), ('Total cash out', 'cash.total_out'), ('Net cash flow', 'cash.net_flow'), ('Closing cash', 'cash.closing'), ('Months of cover', 'cash.cover'),
        ('Cash check', 'cash.cash_flag'), ('Profit of the month', 'cash.pl_profit'), ('Safe owner draw', 'cash.safe_draw')) + [
        FF('Cash floor', '{set:cash_floor}', 'money'), FF('Closing cash above the floor', 'INDEX({range:cash.closing},MATCH({pick},{range:cash.cash_id},0))-{set:cash_floor}', 'money')]),
    FORM('unit_sheet', 'Unit Review Sheet', 'Unit review with profit, margin and break-even', 'units.unit_id', F(
        ('Unit', 'units.name'), ('City', 'units.city'), ('Owner', 'units.owner'), ('Revenue, 12 months', 'units.revenue_12m'), ('Total costs, 12 months', 'units.costs_12m'), ('Profit, 12 months', 'units.profit_12m'), ('Margin', 'units.margin_12m'),
        ('Occupancy', 'units.occ_12m'), ('Break-even occupancy', 'units.be_occ'), ('Break-even check', 'units.be_flag'), ('Profit check', 'units.unit_flag')) + [
        FF('Wanted margin', '{set:target_margin}', 'pct'), FF('Profit of all units, 12 months', 'SUM({range:units.profit_12m})', 'money')]),
    FORM('loan_sheet', 'Loan Sheet', 'Loan or lease with months left and payments', 'loans.loan_id', F(
        ('Item', 'loans.item'), ('Kind', 'loans.kind'), ('Lender', 'loans.lender'), ('Monthly payment', 'loans.monthly_payment'), ('Balance', 'loans.balance'), ('End date', 'loans.end_date'), ('Months left', 'loans.months_left'),
        ('Payments still to make', 'loans.payments_left'), ('End check', 'loans.end_flag'), ('Host phone', 'loans.host_phone')) + [
        FF('All monthly loan and lease payments', 'SUM({range:loans.monthly_payment})', 'money')]),
    FORM('idea_sheet', 'New Unit Idea Sheet', 'Unit idea with yearly profit and payback', 'pipeline.idea_id', F(
        ('Unit idea', 'pipeline.idea'), ('City', 'pipeline.city'), ('Bedrooms', 'pipeline.bedrooms'), ('Expected earning per night', 'pipeline.expected_rate'), ('Expected occupancy', 'pipeline.expected_occ'), ('Set-up cost', 'pipeline.setup_cost'),
        ('Rent per month', 'pipeline.rent'), ('Revenue per year', 'pipeline.revenue_year'), ('Profit per year', 'pipeline.yearly_profit'), ('Payback in months', 'pipeline.payback'), ('Payback check', 'pipeline.pipe_flag'), ('Decide by', 'pipeline.decide_on'))),
    FORM('scenario_sheet', 'Scenario Sheet', 'Growth scenario with the extra yearly profit', 'growth.scn_id', F(
        ('Scenario', 'growth.scenario'), ('Units added', 'growth.units_added'), ('Rate change', 'growth.rate_change'), ('Occupancy change', 'growth.occupancy_change'), ('Cost change', 'growth.cost_change'), ('Profit from rates', 'growth.rate_gain'),
        ('Profit from occupancy', 'growth.occ_gain'), ('Profit from units', 'growth.unit_gain'), ('Profit from costs', 'growth.cost_effect'), ('Extra yearly profit', 'growth.extra_profit'), ('Scenario check', 'growth.scn_flag'))),
    FORM('close_sheet', 'Monthly Close Sheet', 'Month-end close with profit, cash and open items', 'cash.cash_id', F(
        ('Month', 'cash.month'), ('Revenue of the month', 'cash.pl_revenue'), ('Costs of the month', 'cash.pl_costs'), ('Profit of the month', 'cash.pl_profit'), ('Closing cash', 'cash.closing'), ('Owner draw', 'cash.owner_draw'), ('Cash check', 'cash.cash_flag')) + [
        FF('Platform fees of the month', 'SUMIFS({range:pl.platform_fees},{range:pl.month},INDEX({range:cash.month},MATCH({pick},{range:cash.cash_id},0)))', 'money'),
        FF('Margin of the month', 'IFERROR(INDEX({range:cash.pl_profit},MATCH({pick},{range:cash.cash_id},0))/INDEX({range:cash.pl_revenue},MATCH({pick},{range:cash.cash_id},0)),0)', 'pct'),
        FF('Payouts still late or missing', 'COUNTIFS({range:payouts.pay_flag},%s)+COUNTIFS({range:payouts.pay_flag},%s)' % (cf('Payout late'), cf('Payout missing')), 'int'),
        FF('Owner statements not yet paid', 'COUNTIFS({range:statements.status},"<>"&%s)' % tok('stmst', 'Paid'), 'int')]),
    FORM('budget_sheet', 'Budget Sheet', 'Yearly budget of one unit', 'units.unit_id', F(
        ('Unit', 'units.name'), ('Revenue, last 12 months', 'units.revenue_12m'), ('Revenue budget', 'units.rev_budget'), ('Costs, last 12 months', 'units.costs_12m'), ('Cost budget', 'units.cost_budget'), ('Profit, last 12 months', 'units.profit_12m'),
        ('Profit budget', 'units.profit_budget')) + [FF('Revenue growth planned', '{set:budget_growth}', 'pct'), FF('Cost growth planned', '{set:cost_growth}', 'pct'), FF('Profit budget of all units', 'SUM({range:units.profit_budget})', 'money')]),
]
assert len(forms) == 10
documents = [
    DOC('pl_doc', 'Profit and Loss Report', 'Profit and loss of the business for one month', 'cash.cash_id', [
        'Profit and loss report of {set:company}, dated {today}. Month: {col:cash.month}.', 'Revenue of all units: {col:cash.pl_revenue}. Costs of all units, which include platform fees, cleaning, supplies, repairs, rent and bills: {col:cash.pl_costs}. Profit: {col:cash.pl_profit}.',
        'Cash at the start of the month: {col:cash.opening}. Cash in: {col:cash.cash_in}. Cash out: {col:cash.total_out}. Cash at the end: {col:cash.closing}. Check: {col:cash.cash_flag}.', 'Safe owner draw for the month: {col:cash.safe_draw}. Planned draw: {set:owner_draw}.',
        'Figures come from the Unit Profit by Month and Cash Months sheets. The month in progress shows rent and bills so far.'], ['Host', 'Accountant'], NOTE),
    DOC('unit_doc', 'Unit Profit Statement', 'Unit profit statement for the last 12 months', 'units.unit_id', [
        'Unit profit statement of {set:company}, dated {today}. Unit {col:units.unit_id}: {col:units.name} in {col:units.city}. Owner: {col:units.owner}.', 'Revenue over 12 months: {col:units.revenue_12m}. Platform fees: {col:units.fees_12m}. Total costs: {col:units.costs_12m}. Profit: {col:units.profit_12m}, a margin of {col:units.margin_12m}.',
        'Occupancy: {col:units.occ_12m}. Profit per night booked: {col:units.profit_per_night}. Break-even occupancy: {col:units.be_occ}. Break-even check: {col:units.be_flag}.', 'Profit check against the wanted margin of {set:target_margin}: {col:units.unit_flag}.',
        'Platform fees against the year before: {col:units.fees_change}.'], ['Host', 'Owner'], NOTE),
    DOC('cash_doc', 'Cash Flow Report', 'Cash flow report for one month', 'cash.cash_id', [
        'Cash flow report of {set:company}, dated {today}. Month: {col:cash.month}.', 'Opening cash: {col:cash.opening}. Cash in from payouts and other receipts: {col:cash.cash_in}.',
        'Cash out: expenses {col:cash.expenses}, cleaners {col:cash.cleaners}, supplies {col:cash.supplies}, maintenance {col:cash.maintenance}, co-host fees {col:cash.cohost_fees}, owner payouts {col:cash.owner_payouts}, local taxes {col:cash.local_taxes}, owner draw {col:cash.owner_draw}.',
        'Total cash out: {col:cash.total_out}. Net cash flow: {col:cash.net_flow}. Closing cash: {col:cash.closing}. Months of cover: {col:cash.cover}. Cash floor: {set:cash_floor}. Check: {col:cash.cash_flag}.'], ['Host', 'Accountant'], NOTE),
    DOC('plan_doc', '13-Week Cash Plan', '13-week cash plan for one week', 'forecast.fc_id', [
        'Cash plan of {set:company}, dated {today}. Week starting {col:forecast.week}.', 'Expected payouts: {col:forecast.expected_payouts}. Expected costs: {col:forecast.expected_costs}. Owner payments: {col:forecast.owner_payments}. Local tax: {col:forecast.local_tax}. Owner draw: {col:forecast.owner_draw}.',
        'Net for the week: {col:forecast.net}. Opening balance: {col:forecast.opening}. Closing balance: {col:forecast.closing}.', 'Cash floor: {col:forecast.floor}. Gap to the floor: {col:forecast.gap_to_floor}. Check: {col:forecast.floor_flag}.',
        'The plan is updated every week from payouts that are due and the costs you expect.'], ['Host', 'Accountant'], NOTE),
    DOC('tax_doc', 'Tax Set-Aside Summary', 'Income tax set-aside summary for one month', 'taxset.ts_id', [
        'Income tax set-aside summary of {set:company}, dated {today}. Month: {col:taxset.month}.', 'Profit for tax: {col:taxset.profit}. Set-aside share: {set:tax_set_aside_pct}. Target set-aside: {col:taxset.target}. Amount set aside: {col:taxset.set_aside}. Shortfall: {col:taxset.shortfall}.',
        'Paid to the tax office this month: {col:taxset.paid_amount}. Balance held: {col:taxset.balance}. Funding check: {col:taxset.fund_flag}.', 'The share is your own planning figure. Check your own local rules and ask your accountant for the amount due.'], ['Host', 'Accountant'], NOTE),
    DOC('idea_doc', 'New Unit Business Case', 'Business case for a new unit', 'pipeline.idea_id', [
        'Business case of {set:company}, dated {today}. Unit idea: {col:pipeline.idea} in {col:pipeline.city}, {col:pipeline.bedrooms} bedrooms.', 'Expected earning per night: {col:pipeline.expected_rate}. Expected occupancy: {col:pipeline.expected_occ}. Revenue per year: {col:pipeline.revenue_year}.',
        'Set-up cost: {col:pipeline.setup_cost}. Rent per month: {col:pipeline.rent}. Bills per month: {col:pipeline.running_cost}. Profit per year: {col:pipeline.yearly_profit}, a margin of {col:pipeline.margin}.',
        'Payback: {col:pipeline.payback} months. Longest payback accepted: {set:max_payback} months. Check: {col:pipeline.pipe_flag}. Decision due on {col:pipeline.decide_on}.'], ['Host', 'Owner'], NOTE),
    DOC('growth_doc', 'Growth Plan', 'Growth plan for one scenario', 'growth.scn_id', [
        'Growth plan of {set:company}, dated {today}. Scenario: {col:growth.scenario}.', 'Units added: {col:growth.units_added}. Rate change: {col:growth.rate_change}. Occupancy change: {col:growth.occupancy_change}. Cost change: {col:growth.cost_change}.',
        'Profit from rates: {col:growth.rate_gain}. Profit from occupancy: {col:growth.occ_gain}. Profit from units: {col:growth.unit_gain}. Profit from costs: {col:growth.cost_effect}.', 'Extra yearly profit: {col:growth.extra_profit}. Check: {col:growth.scn_flag}. Review on {col:growth.review_on}.'], ['Host', 'Accountant'], NOTE),
    DOC('keep_doc', 'Keep or Drop Review', 'Keep or drop review for one unit', 'units.unit_id', [
        'Keep or drop review of {set:company}, dated {today}. Unit {col:units.unit_id}: {col:units.name} in {col:units.city}.', 'Revenue over 12 months: {col:units.revenue_12m}. Profit: {col:units.profit_12m}. Margin: {col:units.margin_12m}. Wanted margin: {set:target_margin}.',
        'Occupancy: {col:units.occ_12m}. Break-even occupancy: {col:units.be_occ}. Break-even check: {col:units.be_flag}. Profit check: {col:units.unit_flag}.', 'Decision: keep the unit, change the rate or end the lease. Reason and date are written below.'], ['Host', 'Owner'], NOTE),
    DOC('budget_doc', 'Yearly Budget', 'Yearly budget for one unit', 'units.unit_id', [
        'Yearly budget of {set:company}, dated {today}. Unit {col:units.unit_id}: {col:units.name}.', 'Last 12 months: revenue {col:units.revenue_12m}, costs {col:units.costs_12m}, profit {col:units.profit_12m}.',
        'Budget for the next 12 months with revenue growth of {set:budget_growth} and cost growth of {set:cost_growth}: revenue {col:units.rev_budget}, costs {col:units.cost_budget}, profit {col:units.profit_budget}.', 'The budget is reviewed every quarter against the Unit Profit by Month sheet.'], ['Host', 'Owner'], NOTE),
    DOC('pack_doc', 'Accountant Year-End Pack', 'Accountant pack for the year end', 'taxset.ts_id', [
        'Year-end pack of {set:company}, dated {today}, for the accountant. Month on file: {col:taxset.month}.', 'Profit for tax: {col:taxset.profit}. Amount set aside: {col:taxset.set_aside}. Paid: {col:taxset.paid_amount}. Balance held: {col:taxset.balance}.',
        'The pack also lists the monthly profit and loss, the cash report, the owner statements, the co-host fees, the local tax rows and the loans and leases from this workbook.', 'Please check the figures and tell us the business tax instalment to hold, using your own local rules.'], ['Host', 'Accountant'], NOTE),
]
assert len(documents) == 10
checklists = [
    CHK('close_run', 'Month-End Close Steps', 'cash', 'cash.month', [('Check every payout of the month against the bank', 31), ('Chase late and missing payouts', 32), ('Enter the expenses, supplies and repairs', 33), ('Check the cleaner pay and the co-host fee', 34), ('Send the owner statements', 36), ('Read the Unit Profit by Month sheet', 37), ('Set aside the tax share', 38), ('Take the owner draw if it is safe', 39)]),
    CHK('cash_run', 'Weekly Cash Check Steps', 'forecast', 'forecast.week', [('Update the expected payouts for the week', 0), ('Update the costs due this week', 0), ('Check the closing balance against the floor', 1), ('Chase any payout that is late', 2), ('Delay a cost if the week is tight', 3), ('Write the lowest week in the notes', 4)]),
    CHK('unit_run', 'Unit Profit Review Steps', 'units', 'units.review_on', [('Read profit, margin and occupancy of the unit', 0), ('Compare the break-even occupancy with today', 0), ('Look at platform fees against last year', 1), ('Check cleaning, supplies and repairs', 2), ('Decide on a rate change', 3), ('Write the decision for the owner', 5)]),
    CHK('tax_run', 'Quarterly Tax Set-Aside Steps', 'taxset', 'taxset.month', [('Add up the profit of the quarter', 31), ('Compare the amount set aside with the target', 32), ('Move the shortfall into the tax account', 33), ('Ask the accountant for the amount due', 35), ('Pay the instalment', 45), ('Write the payment in the sheet', 46)]),
    CHK('idea_run', 'New Unit Assessment Steps', 'pipeline', 'pipeline.decide_on', [('Check the rent and the bills with the owner', -21), ('Compare the rate with similar units', -18), ('Work out the yearly profit and payback', -14), ('Check the break-even occupancy', -12), ('Check your cash after the set-up cost', -9), ('Ask the co-host and the cleaners about capacity', -7), ('Decide and write the reason', 0)]),
    CHK('keep_run', 'Keep or Drop Review Steps', 'loans', 'loans.end_date', [('Read the profit and margin of the unit', -120), ('Test a rate rise on the Rate Rise Impact sheet', -110), ('Talk to the landlord about the rent', -100), ('Decide whether to renew or end the lease', -90), ('Tell the landlord in writing', -80), ('Plan the end of bookings for the unit', -60)]),
    CHK('budget_run', 'Yearly Budget Steps', 'growth', 'growth.review_on', [('Read the last 12 months of each unit', -28), ('Set revenue and cost growth in Start', -24), ('Check the budget of each unit', -21), ('Add new units and the leases that end', -17), ('Compare the profit budget with the owner draw', -12), ('Send the budget to the accountant', -7), ('Review the budget every quarter', 90)]),
    CHK('rate_run', 'Rate Review Before Season Steps', 'breakeven', 'breakeven.review_on', [('List the break-even rate of every unit', -30), ('Compare it with last season rates', -26), ('Raise units that sold out last season', -21), ('Check units priced under break-even', -18), ('Test a rate rise on the calculator', -14), ('Tell the owners of the new rates', -10), ('Update the listings', -7)]),
    CHK('loan_run', 'Loan and Lease Review Steps', 'loans', 'loans.review_on', [('List every loan and lease with its end date', 0), ('Check the balance against the lender statement', 2), ('Compare the payment with the unit profit', 4), ('Ask for a better rate or a longer term', 7), ('Plan the cash for payments ending soon', 10), ('Note the decision', 12)]),
    CHK('year_run', 'Year-End Close Steps', 'taxset', 'taxset.review_on', [('Check every month of the Unit Profit by Month sheet', 0), ('Reconcile the owner statements', 3), ('Check the local tax rows and the remitted amounts', 5), ('Fill the tax set-aside to the full share', 7), ('Send the accountant pack', 10), ('Write next year targets for margin and cash', 14), ('Plan the owner draw for the new year', 17)]),
]
assert len(checklists) == 10
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('h_floor', 'Host: cash is below the floor', 'forecast', 'forecast.host_phone', 'Hello, the cash forecast shows {closing} in the week of {week}, against your floor of {floor}. Gap: {gap_to_floor}.'),
    M('h_profit', 'Host: the profit of the month', 'cash', 'cash.host_phone', 'Hello, the profit of {month} is {pl_profit} on revenue of {pl_revenue}. Cash at the end: {closing}.'),
    M('h_loss', 'Host: a unit lost money', 'units', 'units.host_phone', 'Hello, {name} made {profit_12m} in 12 months on revenue of {revenue_12m}. Its break-even occupancy is {be_occ}.'),
    M('h_draw', 'Host: the safe owner draw', 'cash', 'cash.host_phone', 'Hello, the safe owner draw for {month} is {safe_draw}. Cash is {closing} and the profit of the month is {pl_profit}.'),
    M('h_tax', 'Host: the tax set-aside is due', 'taxset', 'taxset.host_phone', 'Hello, the tax set-aside balance is {balance}. For {month} you set aside {set_aside} against a target of {target}.'),
    M('h_close', 'Host: the month-end close is ready', 'cash', 'cash.host_phone', 'Hello, the month-end close for {month} is ready: revenue {pl_revenue}, costs {pl_costs}, profit {pl_profit}.'),
    M('h_late', 'Host: a payout is late', 'payouts', 'payouts.host_phone', 'Hello, payout {payout_id} for booking {booking_id} in {unit} was expected on {expected_date}. {gap} is still missing.'),
    M('h_budget', 'Host: the yearly budget is ready', 'units', 'units.host_phone', 'Hello, the yearly budget for {name} is ready: revenue {rev_budget}, costs {cost_budget}, profit {profit_budget}.'),
    M('h_best', 'Host: the most profitable unit', 'units', 'units.host_phone', 'Hello, {name} earned a profit of {profit_12m} over 12 months, a margin of {margin_12m}.'),
    M('h_growth', 'Host: a growth scenario beats the plan', 'growth', 'growth.host_phone', 'Hello, the scenario {scenario} adds {extra_profit} a year. Check: {scn_flag}.'),
    M('h_lease', 'Host: a lease ends in 90 days', 'loans', 'loans.host_phone', 'Hello, {item} ends on {end_date}, {months_left} months left. Payments still to make: {payments_left}.'),
    M('h_fees', 'Host: platform fees rose', 'units', 'units.host_phone', 'Hello, platform fees for {name} were {fees_12m} over 12 months, {fees_change} against the year before.'),
    M('h_fc', 'Host: the 13-week forecast is updated', 'forecast', 'forecast.host_phone', 'Hello, the cash forecast is updated. Week of {week}: closing balance {closing}, net for the week {net}.'),
    M('h_util', 'Host: utilities rose in a unit', 'units', 'units.host_phone', 'Hello, utilities for {name} are {utilities} a month and internet {internet}. Please check the bills.'),
    M('a_pl', 'Accountant: the monthly profit and loss', 'cash', 'cash.accountant_phone', 'Hello, the profit and loss for {month} is attached: revenue {pl_revenue}, costs {pl_costs}, profit {pl_profit}.'),
    M('a_cash', 'Accountant: the cash report', 'cash', 'cash.accountant_phone', 'Hello, the cash report for {month}: opening {opening}, cash in {cash_in}, cash out {total_out}, closing {closing}.'),
    M('a_tax', 'Accountant: the tax set-aside', 'taxset', 'taxset.accountant_phone', 'Hello, the tax set-aside for {month} is {set_aside}. The balance held is {balance}.'),
    M('a_exp', 'Accountant: expenses to review', 'expenses', 'expenses.accountant_phone', 'Hello, please review expense {expense_id}: {description}, {amount}, paid to {paid_to} on {date}.'),
    M('a_year', 'Accountant: the year-end pack is ready', 'taxset', 'taxset.accountant_phone', 'Hello, the year-end pack is ready. Profit for tax in {month}: {profit}. Balance held: {balance}.'),
    M('a_stmt', 'Accountant: owner statements and fees', 'statements', 'statements.accountant_phone', 'Hello, owner statement {statement_id} for {owner}, {month}: revenue {revenue}, management fee {mgmt_fee}, net to owner {net_to_owner}.'),
    M('c_budget', 'Co-host: the fee budget', 'cohost', 'cohost.cohost_phone', 'Hello, your fee for {month} is {fee_amount} on net revenue of {net_revenue}. Next quarter keeps the same share, {fee_pct}.'),
    M('c_costs', 'Co-host: costs to watch in a unit', 'units', 'units.cohost_phone', 'Hello, costs to watch in {name}: utilities {utilities} and internet {internet} a month, platform fees {fees_change} against last year.'),
    M('cl_budget', 'Cleaner: the cleaning budget', 'cleaner_pay', 'cleaner_pay.cleaner_phone', 'Hello {cleaner}, the cleaning budget for next month follows {month}: {turnovers} turnovers, {hours} hours, {amount}.'),
    M('hp_budget', 'Handyperson: the maintenance budget', 'maint', 'maint.handyperson_phone', 'Hello {handyperson}, the repair budget for next month follows {unit} on {done_on}: {cost} for {kind}.'),
    M('o_profit', 'Owner: the profit of your unit', 'units', 'units.owner_phone', 'Hello {owner}, {name} made a profit of {profit_12m} over the last 12 months, a margin of {margin_12m}.'),
    M('o_plan', 'Owner: a plan to raise your unit profit', 'breakeven', 'breakeven.owner_phone', 'Hello, plan for {unit}: it earns {rate} a night and breaks even at {be_rate}. Let us look at the rate and the costs together.'),
    M('o_be', 'Owner: your break-even occupancy', 'breakeven', 'breakeven.owner_phone', 'Hello, {unit} breaks even at an occupancy of {be_occ}. Today it runs at {occ_now}.'),
    M('o_rate', 'Owner: a rate rise for next season', 'breakeven', 'breakeven.owner_phone', 'Hello, a rate rise for next season: {unit} earns {rate} a night against a break-even rate of {be_rate} at the wanted occupancy.'),
]
assert len(messages) == 28, len(messages)

def PLM(col, a, b): return 'SUMIFS({range:pl.%s},{range:pl.month},">="&%s,{range:pl.month},"<"&%s)' % (col, a, b)
def PM(col): return PLM(col, MS, NXT)
def P12(col): return PLM(col, Y1, MS)
DIR = tok('chan', 'Direct'); DONE = tok('bstatus', 'Completed')
B12 = '{range:bookings.check_out},">="&%s,{range:bookings.check_out},"<"&%s,{range:bookings.status},%s' % (Y1, MS, DONE)
BEO = 'IFERROR(SUM({range:breakeven.fixed_cost})/(30.4*SUM({range:breakeven.margin_night})),0)'
DSUM = 'SUMIFS({range:bookings.earned},{range:bookings.channel},%s,%s)' % (DIR, B12)
NPCT = 'SUMIFS({range:bookings.platform_fee},{range:bookings.channel},"<>"&%s,%s)/SUMIFS({range:bookings.earned},{range:bookings.channel},"<>"&%s,%s)' % (DIR, B12, DIR, B12)
DPCT = 'SUMIFS({range:bookings.platform_fee},{range:bookings.channel},%s,%s)/%s' % (DIR, B12, DSUM)
kpis = [
    KPI('Revenue this month', PM('revenue'), 'money'), KPI('Revenue, last 12 months', P12('revenue'), 'money'), KPI('Platform fees this month', PM('platform_fees'), 'money'),
    KPI('Cleaning cost this month', PM('cleaning'), 'money'), KPI('Supplies cost this month', PM('supplies'), 'money'), KPI('Maintenance cost this month', PM('maintenance'), 'money'),
    KPI('Rent and loan payments this month', PM('rent'), 'money'), KPI('Utilities this month', PM('utilities'), 'money'), KPI('Total costs this month', PM('total_costs'), 'money'),
    KPI('Profit this month', PM('profit'), 'money'), KPI('Profit, last 12 months', P12('profit'), 'money'), KPI('Profit margin this month', 'IFERROR(%s/%s,0)' % (PM('profit'), PM('revenue')), 'pct'),
    KPI('Profit margin, last 12 months', 'IFERROR(%s/%s,0)' % (P12('profit'), P12('revenue')), 'pct'), KPI('Profit per available night, 12 months', 'IFERROR(%s/%s,0)' % (P12('profit'), P12('available_nights')), 'money'),
    KPI('Profit per occupied night, 12 months', 'IFERROR(%s/%s,0)' % (P12('profit'), P12('nights')), 'money'), KPI('Units with a loss, last 12 months', 'COUNTIFS({range:units.profit_12m},"<0")', 'int'),
    KPI('Loss on the weakest unit, 12 months', 'MIN({range:units.profit_12m})', 'money'), KPI('Best unit profit, last 12 months', 'MAX({range:units.profit_12m})', 'money'),
    KPI('Break-even occupancy overall', BEO, 'pct'), KPI('Occupancy against break-even', 'IFERROR(SUM({range:units.nights_12m})/SUM({range:units.avail_12m})-%s,0)' % BEO, 'pct'),
    KPI('Cash balance now', CASHNOW, 'money'),
    KPI('Months of cost cover', 'IFERROR(%s/AVERAGEIFS({range:cash.total_out},{range:cash.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:cash.month},"<"&%s),0)' % (CASHNOW, MS), 'num'),
    KPI('Lowest cash week, next 13 weeks', 'MIN({range:forecast.closing})', 'money'), KPI('Weeks below the cash floor', 'COUNTIFS({range:forecast.floor_flag},%s)' % cf('Below the floor'), 'int'),
    KPI('Owner draw this year', 'SUMIFS({range:draws.amount},{range:draws.month},">="&DATE(YEAR({today}),1,1),{range:draws.month},"<="&{today})', 'money'),
    KPI('Safe owner draw now', 'SUMIFS({range:cash.safe_draw},{range:cash.month},%s)' % MS, 'money'), KPI('Tax set-aside balance', 'SUM({range:taxset.set_aside})-SUM({range:taxset.paid_amount})', 'money'),
    KPI('Fee saving from direct, listed bookings', 'IFERROR(%s*(%s-%s),0)' % (DSUM, NPCT, DPCT), 'money'), KPI('Cost per occupied night, 12 months', 'IFERROR(%s/%s,0)' % (P12('total_costs'), P12('nights')), 'money'),
]
assert len(kpis) == 29, len(kpis)
dashboard = {"title": "Profit and Cash Dashboard", "kpis": kpis,
    "monthly": {"title": "Revenue, costs and profit by month", "date": "pl.month", "series": [
        {"label": "Revenue", "sum": "pl.revenue", "date": "pl.month"}, {"label": "Total costs", "sum": "pl.total_costs", "date": "pl.month"}, {"label": "Profit", "sum": "pl.profit", "date": "pl.month"},
        {"label": "Closing cash", "sum": "cash.closing", "date": "cash.month"}]},
    "breakdowns": [{"title": "Profit by unit", "by": "pl.unit", "value": "pl.profit", "agg": "sum"}, {"title": "Revenue by city", "by": "pl.city", "value": "pl.revenue", "agg": "sum"},
                   {"title": "Overheads by category", "by": "expenses.category", "value": "expenses.amount", "agg": "sum"}, {"title": "Local tax collected by city", "by": "localtax.city", "value": "localtax.tax_collected", "agg": "sum"}]}
COMPL = ('status', '=', DONE)
insights = {"filters": [{"label": "Unit", "ref": "units.name"}, {"label": "City", "list": "city"}],
    "gauges": [{"title": "Profit margin", "num": AGG('sum', 'pl', 'pl.profit'), "den": AGG('sum', 'pl', 'pl.revenue')},
               {"title": "Units above break-even occupancy", "num": AGG('count', 'breakeven', where=[('be_flag', '=', cf('Above break-even'))]), "den": AGG('count', 'breakeven')},
               {"title": "Forecast weeks above the cash floor", "num": AGG('count', 'forecast', where=[('floor_flag', '=', cf('Above the floor'))]), "den": AGG('count', 'forecast')},
               {"title": "Units with a profit", "num": AGG('count', 'units', where=[('profit_12m', '>', 0)]), "den": AGG('count', 'units')},
               {"title": "Months with a month of cost cover", "num": AGG('count', 'cash', where=[('cover', '>=', 1)]), "den": AGG('count', 'cash')},
               {"title": "Tax set-aside funded", "num": AGG('sum', 'taxset', 'taxset.set_aside'), "den": AGG('sum', 'taxset', 'taxset.target')}],
    "charts": [
        CHART('Revenue per month', 'column', 'month', [AGG('sum', 'pl', 'pl.revenue', date='pl.month', label='Revenue')]),
        CHART('Profit per month', 'column', 'month', [AGG('sum', 'pl', 'pl.profit', date='pl.month', label='Profit')]),
        CHART('Costs by type per month', 'column', 'month', [AGG('sum', 'pl', 'pl.platform_fees', date='pl.month', label='Platform fees'), AGG('sum', 'pl', 'pl.cleaning', date='pl.month', label='Cleaning'),
            AGG('sum', 'pl', 'pl.rent', date='pl.month', label='Rent or loan'), AGG('sum', 'pl', 'pl.bills_other', date='pl.month', label='Bills, supplies, repairs and other')]),
        CHART('Overheads and unit costs by category', 'bar', 'expenses.category', [AGG('sum', 'expenses', 'expenses.amount', label='Amount')]),
        CHART('Profit by unit', 'bar', 'pl.unit', [AGG('sum', 'pl', 'pl.profit', label='Profit')]),
        CHART('Margin by unit', 'bar', 'pl.unit', [AGG('avg', 'pl', 'pl.margin', label='Margin')]),
        CHART('Profit by city', 'bar', 'pl.city', [AGG('sum', 'pl', 'pl.profit', label='Profit')]),
        CHART('Profit by unit type', 'bar', 'pl.unit_type', [AGG('sum', 'pl', 'pl.profit', label='Profit')]),
        CHART('Platform fees per month', 'column', 'month', [AGG('sum', 'pl', 'pl.platform_fees', date='pl.month', label='Platform fees')]),
        CHART('Cash closing balance per month', 'line', 'month', [AGG('sum', 'cash', 'cash.closing', date='cash.month', label='Closing cash')]),
        CHART('Cash in against cash out per month', 'column', 'month', [AGG('sum', 'cash', 'cash.cash_in', date='cash.month', label='Cash in'), AGG('sum', 'cash', 'cash.total_out', date='cash.month', label='Cash out')]),
        CHART('Cash forecast, closing balance by month', 'line', 'month', [AGG('avg', 'forecast', 'forecast.closing', date='forecast.week', label='Closing balance')]),
        CHART('Owner draw per month', 'column', 'month', [AGG('sum', 'draws', 'draws.amount', date='draws.month', label='Owner draw')]),
        CHART('Tax set-aside per month', 'column', 'month', [AGG('sum', 'taxset', 'taxset.set_aside', date='taxset.month', label='Set aside')]),
        CHART('Revenue by channel per month, listed bookings', 'column', 'month', [AGG('sum', 'bookings', 'bookings.earned', date='bookings.check_out', where=[COMPL, ('channel', '=', tok('chan', c))], label=c) for c in CHANNELS]),
        CHART('Cost per occupied night per month', 'line', 'month', [AGG('avg', 'pl', 'pl.cost_per_night', date='pl.month', where=[('nights', '>', 0)], label='Cost per night')]),
        CHART('Break-even occupancy against occupancy per month', 'line', 'month', [AGG('avg', 'pl', 'pl.occupancy', date='pl.month', label='Occupancy'), AGG('avg', 'pl', 'pl.be_occ', date='pl.month', where=[('be_occ', '<', 2)], label='Break-even occupancy')]),
        CHART('Growth scenarios by extra profit', 'bar', 'growth.scenario', [AGG('sum', 'growth', 'growth.extra_profit', label='Extra yearly profit')])]}
assert len(insights['charts']) == 18 and len(insights['gauges']) == 6
signature = [
    {"name": "Unit profit and loss after fees and cleaning", "why": "every unit and month shows revenue, platform fees, cleaning, supplies, repairs, rent and bills, with profit, margin and profit per night", "where": "Unit Profit by Month"},
    {"name": "Break-even occupancy and rate by unit", "why": "fixed cost, cost per night and platform fee give the occupancy and the rate at which each unit stops losing money", "where": "Break-Even Rows"},
    {"name": "Losing unit alert", "why": "units with a loss or a thin margin turn red with their break-even check, so the weakest unit is never a surprise", "where": "Units"},
    {"name": "13-week cash forecast with floor warning", "why": "expected payouts, costs, owner payments, local tax and draws give the balance of every week and flag the weeks near your cash floor", "where": "Cash Forecast"},
    {"name": "Safe owner draw", "why": "profit after the tax set-aside and cash above the floor give the amount the host can take out this month", "where": "Safe Owner Draw"},
    {"name": "Income tax set-aside planner", "why": "profit by month, the share you hold back, payments made and the balance held, with the shortfall against your target", "where": "Income Tax Set-Aside"},
    {"name": "Payout timing gap", "why": "costs due before payouts arrive and the days of delay give the cash needed to bridge the wait", "where": "Payout Timing Gap"},
    {"name": "New unit return and payback", "why": "set-up cost, rent, rate and occupancy give the yearly profit, margin and months to pay back, checked against your longest payback", "where": "New Unit Return"},
    {"name": "Keep or drop a unit", "why": "profit, margin, lease end and a possible rate rise give a decision and the reason for each unit", "where": "Keep or Drop a Unit"},
    {"name": "Growth scenario planner", "why": "extra units, rate changes, occupancy and cost changes show the extra yearly profit of each plan from your own last 12 months", "where": "Growth Scenarios"}]
competitors = [
    {"what": "free occupancy templates", "lacks": "count nights and revenue but never subtract platform fees, cleaning, rent and bills, so you cannot see the profit or the break-even occupancy of a unit"},
    {"what": "subscription property-management software", "lacks": "charge every month and show profit in fixed reports, with no 13-week cash forecast, safe owner draw or tax set-aside you can change"},
    {"what": "single-sheet booking trackers", "lacks": "list bookings but have no unit profit and loss, no payouts check and no cash floor warning"},
    {"what": "generic expense spreadsheets", "lacks": "add up costs but know nothing about turnovers, platform fees, owner statements, co-host fees or local occupancy tax"},
    {"what": "general small-business cash flow templates", "lacks": "forecast cash with generic lines and ignore payout timing, owner payments and the growth question of adding, keeping or dropping a unit"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: wanted occupancy and margin, cash floor, owner draw, tax set-aside share and the longest payback you accept for a new unit.',
    'Check Units, Break-Even Rows and Team. They hold your units, their fixed costs and the people the other sheets look up.',
    'Fill Unit Profit by Month: one row for each unit and month with revenue and each cost. Total costs, profit, margin, profit per night and occupancy calculate themselves.',
    'Log bookings on Bookings and each payout on Payouts. Late, short and missing payouts turn red with the amount still missing.',
    'Enter every cost on Expenses, Cleaner Pay, Supply Purchases and Maintenance Costs. Rent and bills sit in Unit Profit by Month.',
    'Keep Cash Months up to date at the end of each month. It gives closing cash, months of cover, the floor check and the safe owner draw. Owner Draws records what you took.',
    'Update Cash Forecast every week with the payouts you expect and the costs you must pay. It shows the balance of each of the next 13 weeks against your cash floor.',
    'Record owner statements, co-host fees and local occupancy tax (a tax on each night, collected from the guest) on their own sheets. The amount left to remit is flagged.',
    'Use Income Tax Set-Aside to hold back your share of profit each month and see the balance. Check your own local rules and ask your accountant for the amount due.',
    'List your leases and loans on Loans and Leases. A lease that ends within the warning days turns amber.',
    'Plan growth on Unit Pipeline and Growth Scenarios: set-up cost, rent, rate and occupancy give the yearly profit and payback; each scenario shows the extra yearly profit.',
    f'Use the {len(tools)} calculators for profit, break-even, cash, the safe draw, tax set-aside, payout gaps, a new unit, keep or drop, rate rises and direct bookings.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Profit and Cash Dashboard and Charts every month: revenue, profit, margin, cash, break-even and growth.']
listing = {"title": "Short-Term Rental Profit and Cash Flow Excel Template: Unit P&L, Break-Even, 13-Week Cash Forecast, Safe Owner Draw, Tax Set-Aside",
    "headline": "Know which unit makes money, how much cash you have and when to grow",
    "tags": ["short term rental", "vacation rental", "rental host", "unit profit", "cash flow forecast", "excel template", "break even", "owner draw", "tax set aside", "rental finance", "profit and loss", "holiday let", "property host"],
    "description": ("Run the money side of a short-term or vacation rental business in one Excel workbook. Built for a host or co-host with 3 to 15 furnished units rented by the night through booking platforms and direct bookings. "
        "Unit Profit by Month shows every unit and every month with revenue, platform fees, cleaning, supplies, repairs, rent, bills and the rest, and works out the profit, the margin, the profit per night and the occupancy. Units flags the unit that loses money, "
        "and Break-Even Rows finds the occupancy and the nightly rate at which each unit stops losing money after fees and cleaning.\n\n"
        "Cash Months gives the closing cash, months of cover, the floor check and the safe owner draw of every month. Cash Forecast looks 13 weeks ahead with expected payouts (the money a booking platform sends the host after a stay starts), costs, owner payments, local tax and draws, and warns when a week gets near your cash floor. "
        "Payouts, Expenses, Cleaner Pay, Supply Purchases and Maintenance Costs feed the figures. Owner Statements, Co-host Fees (a co-host is a helper who handles guests for a fee) and Local Tax track what you owe and what you keep. Income Tax Set-Aside holds back a share of profit and shows the balance. "
        "Loans and Leases lists what ends and when. Unit Pipeline and Growth Scenarios answer when to add a unit, keep one, drop one or raise rates.\n\n"
        f"{len(tools)} calculators cover unit profit, break-even occupancy and rate, a 13-week cash forecast, the cash floor warning, the safe owner draw, income tax set-aside, the payout timing gap, a new unit, keep or drop, a rate rise, direct booking savings, cost per night and a rate and occupancy grid. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the host, the accountant, the co-host, the cleaners, the handypeople and the owners.\n\n"
        "This is part eight of the Short-Term Rental Host suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data for a small portfolio to explore first. It helps you plan your money and does not give tax or legal advice."),
    "features": ["Profit and loss by unit and month", "Break-even occupancy and rate by unit", "Losing unit alert", "13-week cash forecast with floor warning", "Safe owner draw and tax set-aside",
                 "Payouts, expenses, cleaner pay and repairs", "Owner statements, co-host fees and local tax", "Unit pipeline and growth scenarios", f"{len(tools)} calculators for profit, cash and growth", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p8', slug='short-term-rental-finance', profession='Short-Term Rental Host', name='Unit Profit, Cash Flow and Growth',
         tagline='Know which unit makes money, how much cash you have and when to grow', price_usd=29,
         colors={"primary": "#264653", "accent": "#E9C46A"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Unit profit, cash flow and growth"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sr8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
