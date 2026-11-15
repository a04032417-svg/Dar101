"""Car Rental Business suite - part 8: Finance, Replace-or-Sell and Owner Pay."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr8_lists import *
from cr8_tables import settings, tables, SOLD, YES, MS, WIN, PS, CASH_NOW, KNOWN, REPAIRS
from cr8_tools import tools
import cr8_data as D

SUITE = 'fx-20261115-car-rental'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def LKV(t, kc, c, key): return 'IFERROR(INDEX({range:%s.%s},MATCH(%s,{range:%s.%s},0)),0)' % (t, c, key, t, kc)
def PV(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)

# ------------------------------------------------------------------ forms (12)
def VBY(col, vcol='purchases', idc='event_id'): return 'IFERROR(INDEX({range:vehicles.%s},MATCH(%s,{range:vehicles.vehicle},0)),0)' % (col, PV(vcol, idc, 'vehicle'))
forms = [
    FORM('purchase_sheet', 'Vehicle Purchase Sheet', 'Vehicle purchase and its loan', 'purchases.event_id', F(
        ('Vehicle', 'purchases.vehicle'), ('Event', 'purchases.event'), ('Date', 'purchases.date'), ('Purchase price', 'purchases.amount'), ('Loan taken', 'purchases.loan'), ('Cash effect', 'purchases.cash_effect')) + [
        FF('Cash put in', '%s-%s' % (PV('purchases', 'event_id', 'amount'), PV('purchases', 'event_id', 'loan')), 'money'), FF('Loan share of the price', 'IFERROR(%s/%s,0)' % (PV('purchases', 'event_id', 'loan'), PV('purchases', 'event_id', 'amount')), 'pct'),
        FF('Monthly loan payment', VBY('monthly_payment'), 'money'), FF('Depreciation a month at your setting', '%s*{set:dep_pct}' % PV('purchases', 'event_id', 'amount'), 'money'), FF('Insurance a year', VBY('insurance_year'), 'money'),
        FF('Book value today', VBY('book_value'), 'money')]),
    FORM('sale_sheet', 'Vehicle Sale Sheet', 'Vehicle sale and the loan to pay off', 'vehicles.vehicle_id', F(
        ('Vehicle', 'vehicles.vehicle'), ('Class', 'vehicles.class'), ('Purchase date', 'vehicles.purchase_date'), ('Purchase price', 'vehicles.purchase_price'), ('Odometer, miles', 'vehicles.odometer'), ('Age in months', 'vehicles.age_months'),
        ('Resale estimate', 'vehicles.resale_estimate'), ('Book value', 'vehicles.book_value'), ('Loan balance', 'vehicles.loan_balance'), ('Equity', 'vehicles.equity')) + [
        FF('Cost of sale at your setting', '%s*{set:sell_cost_pct}' % PV('vehicles', 'vehicle_id', 'resale_estimate'), 'money'),
        FF('Net proceeds at the resale estimate', '%s*(1-{set:sell_cost_pct})' % PV('vehicles', 'vehicle_id', 'resale_estimate'), 'money'),
        FF('Cash freed after the loan is paid off', '%s*(1-{set:sell_cost_pct})-%s' % (PV('vehicles', 'vehicle_id', 'resale_estimate'), PV('vehicles', 'vehicle_id', 'loan_balance')), 'money')]),
    FORM('loan_payment_sheet', 'Loan Payment Sheet', 'Loan payment split into interest and principal', 'financing.fin_id', F(
        ('Vehicle', 'financing.vehicle'), ('Class', 'financing.class'), ('Date', 'financing.date'), ('Payment', 'financing.payment'), ('Interest', 'financing.interest'), ('Principal', 'financing.principal'), ('Balance after', 'financing.balance_after'),
        ('Interest share of the payment', 'financing.interest_share')) + [
        FF('Principal share of the payment', 'IFERROR(%s/%s,0)' % (PV('financing', 'fin_id', 'principal'), PV('financing', 'fin_id', 'payment')), 'pct'),
        FF('Loan balance now', 'IFERROR(INDEX({range:vehicles.loan_balance},MATCH(%s,{range:vehicles.vehicle},0)),0)' % PV('financing', 'fin_id', 'vehicle'), 'money'),
        FF('Loan months left now', 'IFERROR(INDEX({range:vehicles.months_left},MATCH(%s,{range:vehicles.vehicle},0)),0)' % PV('financing', 'fin_id', 'vehicle'), 'int')]),
    FORM('loan_payoff_sheet', 'Loan Payoff Sheet', 'Payoff of one loan against the equity', 'loan_view.vehicle', F(
        ('Class', 'loan_view.class'), ('Monthly payment', 'loan_view.payment'), ('Loan balance', 'loan_view.balance'), ('Loan rate', 'loan_view.rate'), ('Months left', 'loan_view.months_left'), ('Resale estimate', 'loan_view.resale'),
        ('Equity', 'loan_view.equity'), ('Equity share of resale', 'loan_view.equity_share')) + [
        FF('Interest left if paid to the end', '%s*%s-%s' % (PV('loan_view', 'vehicle', 'payment'), PV('loan_view', 'vehicle', 'months_left'), PV('loan_view', 'vehicle', 'balance')), 'money'),
        FF('Sale price that covers balance and costs', '%s/(1-{set:sell_cost_pct})' % PV('loan_view', 'vehicle', 'balance'), 'money'),
        FF('Cash left if paid from cash now', '%s-%s' % (CASH_NOW, PV('loan_view', 'vehicle', 'balance')), 'money')]),
    FORM('owner_draw_sheet', 'Owner Draw Sheet', 'Owner draw of one month', 'draw.draw_id', F(
        ('Month', 'draw.month'), ('Regular draw', 'draw.regular_draw'), ('Extra draw', 'draw.extra_draw'), ('Total draw', 'draw.total'), ('Status', 'draw.status'), ('Draw total of the year', 'draw.year_total')) + [
        FF('Profit of the month', 'SUMIFS({range:pnl.profit},{range:pnl.month},%s)' % PV('draw', 'draw_id', 'month'), 'money'),
        FF('Tax set-aside of the month', 'SUMIFS({range:tax.set_aside},{range:tax.month},%s)' % PV('draw', 'draw_id', 'month'), 'money'),
        FF('Closing cash of the month', 'SUMIFS({range:cash.closing},{range:cash.month},%s)' % PV('draw', 'draw_id', 'month'), 'money'), FF('Regular draw in your settings', '{set:owner_draw}', 'money')]),
    FORM('tax_setaside_sheet', 'Tax Set-aside Sheet', 'Tax set-aside of one month', 'tax.row_id', F(
        ('Month', 'tax.month'), ('Profit of the month', 'tax.profit'), ('Set aside', 'tax.set_aside'), ('Paid to tax', 'tax.paid_to_tax'), ('Set-aside needed', 'tax.needed'), ('Set aside minus needed', 'tax.gap'), ('Balance held', 'tax.balance')) + [
        FF('Set-aside share of profit', 'IFERROR(%s/%s,0)' % (PV('tax', 'row_id', 'set_aside'), PV('tax', 'row_id', 'profit')), 'pct'), FF('Set-aside share, confirm with adviser', '{set:tax_pct}', 'pct')]),
    FORM('scenario_sheet', 'Scenario Sheet', 'One scenario for the next 12 months', 'scenarios.scenario', F(('What changes', 'scenarios.change'), ('Profit, next 12 months', 'scenarios.profit_12m')) + [
        FF('Revenue, next 12 months', 'SUMIFS({range:scenario_months.revenue},{range:scenario_months.scenario},{pick})', 'money'), FF('Cash costs, next 12 months', 'SUMIFS({range:scenario_months.cash_costs},{range:scenario_months.scenario},{pick})', 'money'),
        FF('Depreciation, next 12 months', 'SUMIFS({range:scenario_months.depreciation},{range:scenario_months.scenario},{pick})', 'money'),
        FF('Cash at month 12', 'SUMIFS({range:scenario_months.cash},{range:scenario_months.scenario},{pick},{range:scenario_months.ahead},12)', 'money'),
        FF('Profit minus the Base case', '%s-SUMIFS({range:scenario_months.profit},{range:scenario_months.scenario},%s)' % (PV('scenarios', 'scenario', 'profit_12m'), tok('scen', 'Base case')), 'money'), FF('Cash floor', '{set:cash_floor}', 'money')]),
    FORM('expense_sheet', 'Expense Sheet', 'One expense with its category and vendor', 'expenses.expense_id', F(
        ('Date', 'expenses.date'), ('Category', 'expenses.category'), ('Vendor', 'expenses.vendor'), ('Vehicle ID', 'expenses.vehicle_id'), ('Amount', 'expenses.amount')) + [
        FF('Spent in this category, all rows', 'SUMIFS({range:expenses.amount},{range:expenses.category},%s)' % PV('expenses', 'expense_id', 'category'), 'money'),
        FF('Share of the category', 'IFERROR(%s/SUMIFS({range:expenses.amount},{range:expenses.category},%s),0)' % (PV('expenses', 'expense_id', 'amount'), PV('expenses', 'expense_id', 'category')), 'pct'),
        FF('Spent with this vendor, last 12 months', 'SUMIFS({range:expenses.amount},{range:expenses.vendor},%s,{range:expenses.date},">="&({today}-365))' % PV('expenses', 'expense_id', 'vendor'), 'money'),
        FF('Expenses with this vendor, 12 months', 'COUNTIFS({range:expenses.vendor},%s,{range:expenses.date},">="&({today}-365))' % PV('expenses', 'expense_id', 'vendor'), 'int')]),
    FORM('budget_sheet', 'Budget Sheet', 'Budget for the same month next year', 'pnl.row_id', F(
        ('Month', 'pnl.month'), ('Revenue this month of the year', 'pnl.revenue'), ('Total costs', 'pnl.costs'), ('Profit', 'pnl.profit'), ('Profit margin', 'pnl.margin'), ('Revenue budget next year', 'pnl.budget')) + [
        FF('Cost budget next year', '%s*(1+{set:budget_growth})' % PV('pnl', 'row_id', 'costs'), 'money'), FF('Profit budget next year', '%s-%s*(1+{set:budget_growth})' % (PV('pnl', 'row_id', 'budget'), PV('pnl', 'row_id', 'costs')), 'money'),
        FF('Growth in your settings', '{set:budget_growth}', 'pct'), FF('Margin minus the margin you want', '%s-{set:margin_target}' % PV('pnl', 'row_id', 'margin'), 'pct')]),
    FORM('replace_sell_sheet', 'Replace or Sell Sheet', 'Replace-or-sell decision for one vehicle', 'keep_replace.vehicle', F(
        ('Keep cost a day', 'keep_replace.keep_cost'), ('Replace cost a day', 'keep_replace.replace_cost'), ('Keep minus replace a day', 'keep_replace.difference'), ('Profit, 12 months', 'keep_replace.profit_12m'),
        ('Age in months', 'keep_replace.age_months'), ('Miles', 'keep_replace.miles'), ('Verdict', 'keep_replace.verdict')) + [
        FF('Keep minus replace, a year', '%s*365' % PV('keep_replace', 'vehicle', 'difference'), 'money'), FF('Replacement age in your settings, months', '{set:replace_months}', 'int'), FF('Replacement miles in your settings', '{set:replace_miles}', 'int'),
        FF('Monthly profit or loss', '%s/12' % PV('keep_replace', 'vehicle', 'profit_12m'), 'money')]),
    FORM('business_case_sheet', 'Business Case Sheet', 'Business case for a new vehicle', 'cases.case_id', F(
        ('Class', 'cases.class'), ('Price', 'cases.price'), ('Financing share', 'cases.financing_share'), ('Average utilisation', 'cases.avg_util'), ('Revenue a month', 'cases.revenue_month'), ('Cash profit a month', 'cases.cash_profit'),
        ('Profit a month', 'cases.profit'), ('Payback months', 'cases.payback'), ('Break-even utilisation', 'cases.breakeven_util'), ('Verdict', 'cases.verdict')) + [
        FF('Margin of safety, points', '%s-%s' % (PV('cases', 'case_id', 'avg_util'), PV('cases', 'case_id', 'breakeven_util')), 'pct'), FF('Profit a year', '%s*12' % PV('cases', 'case_id', 'profit'), 'money'),
        FF('Cash you put in', PV('cases', 'case_id', 'down_payment'), 'money')]),
    FORM('month_close_sheet', 'Month-end Close Sheet', 'Month-end close of one month', 'pnl.row_id', F(
        ('Month', 'pnl.month'), ('Revenue', 'pnl.revenue'), ('Vehicle costs', 'pnl.vehicle_costs'), ('Staff', 'pnl.staff'), ('Overhead', 'pnl.overhead'), ('Profit', 'pnl.profit'), ('Utilisation', 'pnl.utilisation')) + [
        FF('Closing cash of the month', 'SUMIFS({range:cash.closing},{range:cash.month},%s)' % PV('pnl', 'row_id', 'month'), 'money'),
        FF('Tax set-aside of the month', 'SUMIFS({range:tax.set_aside},{range:tax.month},%s)' % PV('pnl', 'row_id', 'month'), 'money'),
        FF('Owner draw of the month', 'SUMIFS({range:draw.total},{range:draw.month},%s)' % PV('pnl', 'row_id', 'month'), 'money'),
        FF('Loan payments of the month', 'SUMIFS({range:financing.payment},{range:financing.month},%s)' % PV('pnl', 'row_id', 'month'), 'money'),
        FF('Break-even revenue of the month', PV('pnl', 'row_id', 'breakeven'), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
def DD(key, sheet, title, pick, paras, sign): return DOC(key, sheet, title, pick, paras, sign, NOTE)
documents = [
    DD('pl_doc', 'Profit and Loss Statement', 'Profit and loss statement of a month', 'pnl.row_id', [
        'Profit and loss statement of {set:company}, dated {today}. Month: {col:pnl.month}. Vehicles in the fleet: {col:pnl.vehicles}. Rented days: {col:pnl.rented_days}. Utilisation (rented days as a share of available days): {col:pnl.utilisation}.',
        'Revenue: {col:pnl.revenue}. Channel fees: {col:pnl.channel_fees}. Financing: {col:pnl.financing}. Insurance: {col:pnl.insurance}. Maintenance: {col:pnl.maintenance}. Fuel or charge: {col:pnl.fuel_charge}. Depreciation: {col:pnl.depreciation}. Vehicle costs: {col:pnl.vehicle_costs}.',
        'Staff: {col:pnl.staff}. Overhead: {col:pnl.overhead}. Total costs: {col:pnl.costs}. Profit: {col:pnl.profit}. Profit margin: {col:pnl.margin}. Amounts are before any sales tax.',
        'Average daily rate (revenue per rented day): {col:pnl.adr}. Revenue per available car-day: {col:pnl.revpac}. Break-even revenue of the month: {col:pnl.breakeven}. Add the twelve monthly pages for a 12-month statement.'], ['Owner-operator', 'Bookkeeper']),
    DD('cash_doc', 'Cash Flow Summary', 'Cash flow summary of a month', 'cash.row_id', [
        'Cash flow summary of {set:company}, dated {today}. Month: {col:cash.month}. Opening cash: {col:cash.opening}.',
        'Receipts: {col:cash.receipts}. Operating costs: {col:cash.operating_costs}. Vehicle purchases (down payments): {col:cash.vehicle_purchases}. Vehicle sales: {col:cash.vehicle_sales}. Owner draw: {col:cash.owner_draw}. Tax set-aside: {col:cash.tax_set_aside}.',
        'Closing cash: {col:cash.closing}. Net flow of the month: {col:cash.net_flow}. Closing cash above your cash floor of {set:cash_floor}: {col:cash.floor_gap}.',
        'This summary helps you keep track of cash. Confirm tax and accounting questions with your adviser.'], ['Owner-operator', 'Bookkeeper']),
    DD('draw_doc', 'Owner Draw Note', 'Note on the owner draw of a month', 'draw.draw_id', [
        'Owner draw note of {set:company}, dated {today}. Month: {col:draw.month}. Status: {col:draw.status}.',
        'Regular draw: {col:draw.regular_draw}. Extra draw: {col:draw.extra_draw}. Total draw: {col:draw.total}. Draw total of the year {col:draw.year}: {col:draw.year_total}.',
        'The regular draw in your settings is {set:owner_draw} a month. A draw is money the owner takes out of the business, it is not a cost in the profit and loss statement.',
        'Keep cash above the cash floor of {set:cash_floor} after the draw. Confirm tax questions with your adviser.'], ['Owner-operator', 'Bookkeeper']),
    DD('replace_doc', 'Replace-or-Sell Report', 'Replace-or-sell report for a vehicle', 'keep_replace.vehicle', [
        'Replace-or-sell report of {set:company}, dated {today}. Vehicle: {col:keep_replace.vehicle}. Age in months: {col:keep_replace.age_months}. Miles: {col:keep_replace.miles}.',
        'Cost per day of keeping the vehicle one more year: {col:keep_replace.keep_cost}. Cost per day of replacing it: {col:keep_replace.replace_cost}. Keep minus replace: {col:keep_replace.difference} a day.',
        'Profit of the last 12 months: {col:keep_replace.profit_12m}. Verdict: {col:keep_replace.verdict}.',
        'The replacement age of {set:replace_months} months and {set:replace_miles} miles are example settings, set your own. Miles are the demo unit.'], ['Owner-operator', 'Manager']),
    DD('loan_doc', 'Loan Summary for Your Lender', 'Loan summary for your lender', 'loan_view.vehicle', [
        'Loan summary of {set:company}, dated {today}. Vehicle: {col:loan_view.vehicle}. Class: {col:loan_view.class}.',
        'Monthly payment: {col:loan_view.payment}. Loan balance: {col:loan_view.balance}. Loan rate: {col:loan_view.rate}. Months left: {col:loan_view.months_left}.',
        'Resale estimate: {col:loan_view.resale}. Equity (resale estimate minus the balance): {col:loan_view.equity}, {col:loan_view.equity_share} of the resale estimate.',
        'The resale estimate is our own figure, not a valuation. Please send the payoff figure and the terms in writing.'], ['Owner-operator', 'Lender']),
    DD('case_doc', 'Business Case for a New Vehicle', 'Business case for a new vehicle', 'cases.case_id', [
        'Business case of {set:company}, dated {today}. Case: {col:cases.case_id}. Class: {col:cases.class}. Price: {col:cases.price}. Financing share: {col:cases.financing_share}.',
        'Expected utilisation: peak {col:cases.util_peak}, shoulder {col:cases.util_shoulder}, off-peak {col:cases.util_off}, average {col:cases.avg_util}. Daily rate: {col:cases.day_rate}.',
        'Revenue a month: {col:cases.revenue_month}. Cash profit a month: {col:cases.cash_profit}. Profit a month after depreciation: {col:cases.profit}. Cash put in: {col:cases.down_payment}.',
        'Payback: {col:cases.payback} months. Break-even utilisation (the utilisation at which a vehicle covers its cost): {col:cases.breakeven_util}. Verdict: {col:cases.verdict}.'], ['Owner-operator', 'Lender']),
    DD('scenario_doc', 'Scenario Report', 'Scenario report for the next 12 months', 'scenarios.scenario', [
        'Scenario report of {set:company}, dated {today}. Scenario: {col:scenarios.scenario}. What changes: {col:scenarios.change}.',
        'Profit of the next 12 months in this scenario: {col:scenarios.profit_12m}.',
        'The scenario takes the same months of last year, your recent trend and the changes in your settings: utilisation points {set:sc_util_drop}, cars added {set:sc_cars}, financing rate points {set:sc_fin_pts}, channel fee rise {set:sc_fee_up}, rate rise {set:sc_rate_up}.',
        'A scenario is a what-if, not a forecast. It helps you keep track of risk against your cash floor of {set:cash_floor}.'], ['Owner-operator', 'Bookkeeper']),
    DD('yearend_doc', 'Year-End Pack Page', 'Year-end pack page for your accountant', 'pnl.row_id', [
        'Year-end pack page of {set:company}, dated {today}. Month: {col:pnl.month}, year {col:pnl.year}.',
        'Revenue: {col:pnl.revenue}. Costs: {col:pnl.costs}. Depreciation: {col:pnl.depreciation} at a setting of {col:pnl.dep_pct} a month. Financing: {col:pnl.financing}. Profit: {col:pnl.profit}.',
        'Print one page for each month of the year and add the Year-End Pack Check totals for tax set-aside, loan interest and owner draw.',
        'This pack helps you keep track of the figures. Please confirm every tax question with your adviser.'], ['Owner-operator', 'Accountant']),
    DD('fleet_value_doc', 'Fleet Value Summary', 'Fleet value summary by class', 'fleet_value.class', [
        'Fleet value summary of {set:company}, dated {today}. Class: {col:fleet_value.class}.',
        'Book value of the vehicles in this class: {col:fleet_value.book_value}. Financing balance of the class: {col:fleet_value.loan_balance}.',
        'Book value follows your depreciation setting of {set:dep_pct} a month of the purchase price, never below {set:dep_floor} of the price. It is an example setting, set your own.',
        'Resale estimates on the Vehicles sheet may differ. Use the Depreciation Check to see which vehicles to write down.'], ['Owner-operator', 'Lender']),
    DD('tax_doc', 'Tax Set-Aside Note', 'Tax set-aside note of a month', 'tax.row_id', [
        'Tax set-aside note of {set:company}, dated {today}. Month: {col:tax.month}.',
        'Profit of the month: {col:tax.profit}. Set aside: {col:tax.set_aside}. Set-aside needed at {set:tax_pct}: {col:tax.needed}. Difference: {col:tax.gap}. Paid to tax: {col:tax.paid_to_tax}. Balance held: {col:tax.balance}.',
        'The share is your own setting, income tax set-aside (confirm with your adviser). It names no tax form and gives no tax advice.',
        'Keep the balance in a separate account so that it is there when a payment is due.'], ['Owner-operator', 'Bookkeeper']),
    DD('budget_doc', 'Budget Against Actual', 'Budget against actual for a month', 'pnl.row_id', [
        'Budget against actual of {set:company}, dated {today}. Month: {col:pnl.month}.',
        'Actual revenue: {col:pnl.revenue}. Actual costs: {col:pnl.costs}. Actual profit: {col:pnl.profit}. Actual profit margin: {col:pnl.margin}.',
        'Revenue budget for the same month next year at a growth of {set:budget_growth}: {col:pnl.budget}. Margin you want to hold: {set:margin_target}.',
        'Compare each month with its budget at the month-end close and change the growth in your settings when the year turns out different.'], ['Owner-operator', 'Manager']),
    DD('sale_doc', 'Vehicle Sale Record', 'Vehicle sale record', 'vehicles.vehicle_id', [
        'Vehicle sale record of {set:company}, dated {today}. Vehicle: {col:vehicles.vehicle}. Class: {col:vehicles.class}. Status: {col:vehicles.status}. Sold date: {col:vehicles.sold_date}.',
        'Purchase date: {col:vehicles.purchase_date}. Purchase price: {col:vehicles.purchase_price}. Odometer: {col:vehicles.odometer} miles. Age in months: {col:vehicles.age_months}.',
        'Resale estimate: {col:vehicles.resale_estimate}. Book value: {col:vehicles.book_value}. Loan balance: {col:vehicles.loan_balance}. Equity: {col:vehicles.equity}.',
        'Status and amounts only. Remove the vehicle from the booking calendar and tell your insurer on the date of sale.'], ['Owner-operator', 'Buyer']),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('month_close_chk', 'Month-End Close', 'pnl', 'pnl.month', [('Record every expense of the month', 28), ('Record the loan payments', 28), ('Check the bank balance against Cash', 30), ('Post the owner draw', 30), ('Move the tax set-aside', 31), ('Read the Profit and Loss and the margin', 32), ('Send the figures to the bookkeeper and accountant', 33)]),
    CHK('draw_chk', 'Owner Draw Check', 'draw', 'draw.month', [('Open the Owner Draw and Tax Set-Aside tool', -2), ('Check cash after known costs', -2), ('Check the cash floor', -1), ('Draw the safe amount', 0), ('Record the draw', 1)]),
    CHK('tax_chk', 'Tax Set-Aside Transfer', 'tax', 'tax.month', [('Read the profit of the month', 30), ('Work out the set-aside at your setting', 31), ('Transfer it to the tax account', 32), ('Record the transfer', 32), ('Confirm the share with your adviser each year', 60)]),
    CHK('loan_chk', 'Quarterly Loan Review', 'financing', 'financing.date', [('Open the Financing and Loan View', 85), ('Check the balance of every loan', 86), ('Check equity against the balance', 87), ('Check the financing share of revenue', 88), ('Ask your lender about any rate', 90)]),
    CHK('replace_chk', 'Replace-or-Sell Review', 'replace_in', 'replace_in.review_on', [('Open the Replace-or-Sell Tool', 0), ('Check miles, age and repair cost', 0), ('Check the Best Month to Sell', 1), ('Check the sale proceeds against the payoff', 2), ('Decide: keep, sell this season or replace', 3), ('Tell the manager', 4)]),
    CHK('buy_chk', 'Buying a Vehicle', 'purchases', 'purchases.date', [('Run the Add-a-Vehicle Business Case', -21), ('Check cash against the cash floor', -14), ('Agree the loan with your lender', -10), ('Ask your insurance broker for cover', -7), ('Buy the vehicle and record the purchase', 0), ('Add it to the booking calendar', 1)]),
    CHK('sell_chk', 'Selling a Vehicle', 'purchases', 'purchases.date', [('Run the Sale Proceeds vs Payoff check', -14), ('Ask your lender for the payoff figure', -10), ('Ask the mechanic to inspect the vehicle', -7), ('List the vehicle for sale', -5), ('Sell, pay off the loan and record the sale', 0), ('Remove it from the calendar and tell your insurance broker', 1)]),
    CHK('yearend_chk', 'Year-End Pack', 'cash', 'cash.month', [('Check that every month is in Profit and Loss and Cash', 20), ('Run the Year-End Pack Check', 25), ('Check depreciation against the resale estimates', 28), ('Add tax set-aside, loan interest and owner draw', 30), ('Send the pack to your accountant, confirm with your adviser', 35)]),
    CHK('budget_chk', 'Budget Review', 'draw_plan', 'draw_plan.month', [('Compare each month with its budget', 0), ('Change the budget growth in your settings', 1), ('Check the next 12 months in the Draw Plan', 2), ('Share the budget with the manager', 3)]),
    CHK('scenario_chk', 'Scenario Review', 'cost_cat', 'cost_cat.month', [('Set the scenario numbers on the Start sheet', 0), ('Read the Scenario Test', 1), ('Check the lowest cash against the floor', 2), ('Write down one action for the worst case', 3)]),
    CHK('floor_chk', 'Cash Floor Check', 'known_costs', 'known_costs.date', [('Read cash now', -7), ('List the known costs of the next 30 days', -7), ('Check cash after known costs against the floor', -3), ('Move money in if cash falls below the floor', 0)]),
    CHK('host_chk', 'One-Car Host Finances', 'cases', 'cases.plan_date', [('Fill the One-Car Host Start-Up Case', 0), ('Open a separate account for the car', 2), ('Record every cost and payment', 7), ('Set aside tax each month, confirm with your adviser', 30), ('Review profit and break-even days after a month', 35)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, role, text): return MSG(k, moment, table, '%s.%s_phone' % (table, role), text)
messages = [
    M('own_profit', 'Owner: profit and utilisation', 'pnl', 'owner', 'Hello {owner}, profit for {month} was {profit}, utilisation {utilisation}. {company}'),
    M('own_fin', 'Owner: financing share', 'pnl', 'owner', 'Hello {owner}, financing took {financing_share} of revenue in {month}. {company}'),
    M('own_be', 'Owner: break-even revenue', 'pnl', 'owner', 'Hello {owner}, break-even revenue for {month} is {breakeven} and revenue was {revenue}. {company}'),
    M('own_close', 'Owner: month-end close ready', 'pnl', 'owner', 'Hello {owner}, the month-end close for {month} is ready: revenue {revenue}, profit {profit}. {company}'),
    M('mgr_budget', 'Manager: the budget', 'pnl', 'manager', 'Hello {manager}, the budget for {month} next year is {budget}. {company}'),
    M('bk_figures', 'Bookkeeper: month-end figures', 'pnl', 'bookkeeper', 'Hello {bookkeeper}, the month-end figures for {month} are ready: revenue {revenue}, profit {profit}. {company}'),
    M('acc_pl', 'Accountant: profit and loss attached', 'pnl', 'accountant', 'Hello {accountant}, the profit and loss for {month} is attached: revenue {revenue}, profit {profit}. {company}'),
    M('acc_dep', 'Accountant: depreciation setting', 'pnl', 'accountant', 'Hello {accountant}, our depreciation setting is {dep_pct} a month. Please confirm it. {company}'),
    M('acc_pack', 'Accountant: year-end pack', 'pnl', 'accountant', 'Hello {accountant}, the year-end pack for {year} is ready for your review. {company}'),
    M('lend_fleet', 'Lender: fleet summary', 'pnl', 'lender', 'Hello {lender}, the fleet summary for {month} is attached. {company}'),
    M('own_class', 'Owner: class margin', 'class_month', 'owner', 'Hello {owner}, {class} earned a margin of {margin12} over the last 12 months. {company}'),
    M('own_safe', 'Owner: safe draw', 'draw_plan', 'owner', 'Hello {owner}, for {month} you can safely draw {safe_draw}. {company}'),
    M('own_cash_after', 'Owner: cash after the draw', 'draw_plan', 'owner', 'Hello {owner}, cash after the planned draw in {month} is {cash_after}. {company}'),
    M('own_tax', 'Owner: tax set-aside balance', 'tax', 'owner', 'Hello {owner}, the tax set-aside balance after {month} is {balance}, confirm with your adviser. {company}'),
    M('bk_tax', 'Bookkeeper: transfer to tax account', 'tax', 'bookkeeper', 'Hello {bookkeeper}, please transfer {set_aside} to the tax account for {month}. {company}'),
    M('acc_tax', 'Accountant: tax set-aside balance', 'tax', 'accountant', 'Hello {accountant}, the tax set-aside balance is {balance} after {month}. {company}'),
    M('bk_draw', 'Bookkeeper: record the owner draw', 'draw', 'bookkeeper', 'Hello {bookkeeper}, please record the owner draw of {total} for {month}. {company}'),
    M('acc_draw', 'Accountant: owner draw total', 'draw', 'accountant', 'Hello {accountant}, the owner draw total for {year} is {year_total}. {company}'),
    M('own_equity', 'Owner: equity on a loan', 'loan_view', 'owner', 'Hello {owner}, {vehicle} has equity of {equity} on its loan. {company}'),
    M('lend_payoff', 'Lender: payoff figure', 'loan_view', 'lender', 'Hello {lender}, please send the payoff figure for {vehicle}. {company}'),
    M('lend_rate', 'Lender: discuss the rate', 'loan_view', 'lender', 'Hello {lender}, we would like to discuss the rate on {vehicle}, now {rate}. {company}'),
    M('own_keep', 'Owner: keep or replace cost', 'keep_replace', 'owner', 'Hello {owner}, {vehicle} costs {keep_cost} a day to keep and {replace_cost} to replace. {company}'),
    M('own_worst', 'Owner: scenario cash', 'scenario_months', 'owner', 'Hello {owner}, the {scenario} scenario ends month {ahead} with cash of {cash}. {company}'),
    M('own_payback', 'Owner: payback of a new vehicle', 'cases', 'owner', 'Hello {owner}, the new {class} pays back in {payback} months. {company}'),
    M('bk_loan', 'Bookkeeper: record a loan payment', 'financing', 'bookkeeper', 'Hello {bookkeeper}, please record the loan payment of {payment} for {vehicle} on {date}. {company}'),
    M('mgr_add', 'Manager: add a vehicle to the calendar', 'purchases', 'manager', 'Hello {manager}, please add {vehicle} to the calendar from {date}. {company}'),
    M('mgr_sold', 'Manager: vehicle sold', 'purchases', 'manager', 'Hello {manager}, {vehicle} is sold on {date}, please remove it from the calendar. {company}'),
    M('lend_new', 'Lender: a new loan', 'purchases', 'lender', 'Hello {lender}, a new loan for {vehicle} of {loan}. {company}'),
    M('brk_sold', 'Insurance broker: vehicle sold', 'purchases', 'broker', 'Hello {broker}, {vehicle} was sold on {date}. {company}'),
    M('brk_quote', 'Insurance broker: cover for a vehicle', 'purchases', 'broker', 'Hello {broker}, please quote cover for the new {vehicle}. {company}'),
    M('bk_sale', 'Bookkeeper: post a sale', 'purchases', 'bookkeeper', 'Hello {bookkeeper}, please post the sale of {vehicle} for {amount}. {company}'),
    M('mech_inspect', 'Mechanic: inspect before a sale', 'purchases', 'mechanic', 'Hello {mechanic}, please inspect {vehicle} before the sale on {date}. {company}'),
    M('mgr_list', 'Manager: list a vehicle for sale', 'vehicles', 'manager', 'Hello {manager}, please list {vehicle} for sale, the target price is {resale_estimate}. {company}'),
    M('tyre_quote', 'Tyre supplier: tyres for a sale', 'vehicles', 'tyres', 'Hello {tyres}, please quote tyres for {vehicle}, the vehicle we are selling. {company}'),
]
assert len(messages) == 34

# ------------------------------------------------------------------ dashboard
def S1(t, c, n): return 'SUMIFS({range:%s.%s},%s)' % (t, c, WIN(t, n))
def PM(col, k=0): return 'SUMIFS({range:pnl.%s},{range:pnl.month},EDATE(%s,%d))' % (col, MS, -k)
PROFIT12 = PS('profit', 12); REV12 = PS('revenue', 12)
ACT = 'COUNTIFS({range:vehicles.status},"<>"&%s,{range:vehicles.vehicle_id},"<>")' % SOLD
FIXED3 = '((%s-%s-%s)/3)' % (PS('costs', 3), PS('channel_fees', 3), PS('fuel_charge', 3))
BE3 = '(%s/(1-(%s+%s)/%s))' % (FIXED3, PS('channel_fees', 3), PS('fuel_charge', 3), PS('revenue', 3))
kpis = [
    KPI('Revenue this month', PM('revenue'), 'money'), KPI('Revenue last month', PM('revenue', 1), 'money'), KPI('Revenue last 12 months', REV12, 'money'), KPI('Vehicle costs this month', PM('vehicle_costs'), 'money'),
    KPI('Staff pay this month', PM('staff'), 'money'), KPI('Overhead this month', PM('overhead'), 'money'), KPI('Profit this month', PM('profit'), 'money', alert={"when": "< 0", "style": "bad"}),
    KPI('Profit last month', PM('profit', 1), 'money', alert={"when": "< 0", "style": "bad"}), KPI('Profit last 12 months', PROFIT12, 'money'), KPI('Profit margin last 12 months', 'IFERROR(%s/%s,0)' % (PROFIT12, REV12), 'pct'),
    KPI('Profit per vehicle last 12 months', 'IFERROR(%s/%s,0)' % (PROFIT12, ACT), 'money'), KPI('Depreciation last 12 months', PS('depreciation', 12), 'money'),
    KPI('Financing payments this month', 'SUMIFS({range:financing.payment},{range:financing.month},%s)' % MS, 'money'), KPI('Interest paid last 12 months', S1('financing', 'interest', 12), 'money'),
    KPI('Loan balance now', 'SUM({range:vehicles.loan_balance})', 'money'), KPI('Equity in financed vehicles', 'SUM({range:loan_view.equity})', 'money'),
    KPI('Financing share of revenue last 3 months', 'IFERROR(%s/%s,0)' % (PS('financing', 3), PS('revenue', 3)), 'pct'), KPI('Fleet book value', 'SUM({range:vehicles.book_value})', 'money'),
    KPI('Fleet resale estimate', 'SUMIFS({range:vehicles.resale_estimate},{range:vehicles.status},"<>"&%s)' % SOLD, 'money'),
    KPI('Vehicles at or past the replacement age', 'COUNTIFS({range:vehicles.age_months},">="&{set:replace_months},{range:vehicles.status},"<>"&%s)' % SOLD, 'int'),
    KPI('Vehicles flagged sell or replace', 'COUNTIFS({range:keep_replace.verdict},%s)+COUNTIFS({range:keep_replace.verdict},%s)' % (va('Sell this season'), va('Replace')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Cash now', CASH_NOW, 'money'), KPI('Cash after 30 days of known costs', '%s-%s' % (CASH_NOW, KNOWN), 'money', alert={"when": "< {set:cash_floor}", "style": "warn"}), KPI('Cash floor', '{set:cash_floor}', 'money'),
    KPI('Owner draw this month', 'SUMIFS({range:draw.total},{range:draw.month},%s)' % MS, 'money'), KPI('Owner draw last 12 months', S1('draw', 'total', 12), 'money'),
    KPI('Tax set-aside balance', 'SUM({range:tax.set_aside})-SUM({range:tax.paid_to_tax})', 'money'), KPI('Tax set-aside last 12 months', S1('tax', 'set_aside', 12), 'money'),
    KPI('Break-even revenue per month', BE3, 'money'), KPI('Months of financing covered by cash', 'IFERROR(%s/SUMIFS({range:vehicles.monthly_payment},{range:vehicles.status},"<>"&%s),0)' % (CASH_NOW, SOLD), 'num'),
]
assert len(kpis) == 30
dashboard = {"title": "Finance Dashboard", "kpis": kpis,
    "monthly": {"title": "Revenue, costs and profit by month", "date": "pnl.month", "series": [
        {"label": "Revenue", "sum": "pnl.revenue", "date": "pnl.month"}, {"label": "Total costs", "sum": "pnl.costs", "date": "pnl.month"}, {"label": "Profit", "sum": "pnl.profit", "date": "pnl.month"}]},
    "breakdowns": [{"title": "Profit by class, last 12 months", "by": "class_profit.class", "value": "class_profit.profit_12m", "agg": "sum"}, {"title": "Expenses by category", "by": "expenses.category", "value": "expenses.amount", "agg": "sum"},
                   {"title": "Loan balance by class", "by": "loan_view.class", "value": "loan_view.balance", "agg": "sum"}, {"title": "Fleet book value by class", "by": "fleet_value.class", "value": "fleet_value.book_value", "agg": "sum"}]}
def MC(title, t, col, typ='column', label=None, date=None):
    return CHART(title, typ, 'month', [AGG('sum', t, '%s.%s' % (t, col), date='%s.%s' % (t, date or 'month'), label=label or title.split(' per ')[0])])
def BC(title, t, by, col, agg='sum', label=None, where=None):
    return CHART(title, 'bar', '%s.%s' % (t, by), [AGG(agg, t, ('%s.%s' % (t, col)) if agg != 'count' else None, label=label or title, where=where)])
insights = {"filters": [{"label": "Vehicle class", "list": "class"}, {"label": "Expense category", "list": "expcat"}, {"label": "Vehicle status", "list": "vstatus"}],
    "gauges": [
        {"title": "Profit margin, 24 months", "num": AGG('sum', 'pnl', 'pnl.profit'), "den": AGG('sum', 'pnl', 'pnl.revenue')},
        {"title": "Months with cash above the floor", "num": AGG('count', 'cash', where=[('closing', '>=', '{set:cash_floor}')]), "den": AGG('count', 'cash')},
        {"title": "Financing share of revenue", "num": AGG('sum', 'pnl', 'pnl.financing'), "den": AGG('sum', 'pnl', 'pnl.revenue')},
        {"title": "Tax set-aside against profit", "num": AGG('sum', 'tax', 'tax.set_aside'), "den": AGG('sum', 'tax', 'tax.profit', where=[('profit', '>', 0)])},
        {"title": "Owner draw against cash profit", "num": AGG('sum', 'draw', 'draw.total'), "den": AGG('sum', 'pnl', 'pnl.profit_cash')},
        {"title": "Fleet within the replacement age", "num": AGG('count', 'vehicles', where=[('age_months', '<', '{set:replace_months}'), ('status', '<>', SOLD)]), "den": AGG('count', 'vehicles', where=[('status', '<>', SOLD)])}],
    "charts": [
        CHART('Revenue and profit per month', 'line', 'month', [AGG('sum', 'pnl', 'pnl.revenue', date='pnl.month', label='Revenue'), AGG('sum', 'pnl', 'pnl.profit', date='pnl.month', label='Profit')]),
        MC('Profit per month', 'pnl', 'profit', label='Profit'), BC('Profit by class, last 12 months', 'class_profit', 'class', 'profit_12m', label='Profit'),
        BC('Revenue by class, 24 months', 'class_month', 'class', 'revenue', label='Revenue'), BC('Costs by category, last 12 months', 'cost_cat', 'category', 'amount', label='Costs'),
        MC('Costs per month', 'pnl', 'costs', label='Total costs'), MC('Staff pay per month', 'pnl', 'staff', label='Staff pay'), MC('Financing per month', 'pnl', 'financing', label='Financing'),
        MC('Interest per month', 'financing', 'interest', label='Interest'), MC('Loan balance per month', 'financing', 'balance_after', 'line', label='Loan balance'),
        BC('Loan balance by class', 'loan_view', 'class', 'balance', label='Loan balance'), BC('Equity by class', 'loan_view', 'class', 'equity', label='Equity'),
        MC('Cash per month', 'cash', 'closing', 'line', label='Closing cash'), MC('Receipts per month', 'cash', 'receipts', label='Receipts'), MC('Owner draw per month', 'draw', 'total', label='Owner draw'),
        MC('Tax set-aside per month', 'tax', 'set_aside', label='Set aside'), MC('Vehicle purchases per month', 'cash', 'vehicle_purchases', label='Purchases'), MC('Vehicle sales per month', 'cash', 'vehicle_sales', label='Sales'),
        BC('Expenses by category', 'expenses', 'category', 'amount', label='Expenses'), BC('Expenses by vendor', 'expenses', 'vendor', 'amount', label='Expenses'),
        MC('Depreciation per month', 'pnl', 'depreciation', label='Depreciation'), BC('Fleet book value by class', 'fleet_value', 'class', 'book_value', label='Book value')]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Replace-or-sell tool", "why": "cost per day of keeping one more year against replacing, with equity, repairs and 12-month profit, ending in keep, sell this season or replace", "where": "Replace-or-Sell Tool"},
    {"name": "Best month to sell", "why": "resale value lost each month against the revenue still earned in that season, so you sell before the car costs more than it earns", "where": "Best Month to Sell"},
    {"name": "Financing and loan view", "why": "payment, balance, rate, months left and equity per car, with the financing share of revenue and the months of payments cash covers", "where": "Financing and Loan View"},
    {"name": "Owner draw and tax set-aside", "why": "cash after known costs and the cash floor give the draw that is safe this month, with the tax set-aside taken first", "where": "Owner Draw and Tax Set-Aside"},
    {"name": "Scenario test", "why": "a Base case and five what-ifs run 12 months ahead on your own history, with the lowest cash point against your floor", "where": "Scenario Test"},
    {"name": "Add-a-vehicle business case", "why": "price, loan, utilisation by season and daily rate give profit, payback months and the utilisation that covers the cost before you buy", "where": "Add-a-Vehicle Business Case"},
    {"name": "One-car host start-up case", "why": "one car with its own cost and rental days a month: profit, payback and the days a month needed to break even", "where": "One-Car Host Start-Up Case"},
    {"name": "Break-even revenue", "why": "the monthly revenue that covers every cost including depreciation, with the margin of safety and the rented days needed", "where": "Break-Even Revenue"},
    {"name": "Refinance check", "why": "a new rate and term against the loan left, with the monthly saving and the months to earn back any fee", "where": "Refinance Check"},
    {"name": "Sale proceeds against payoff", "why": "the expected sale price less the cost of sale and the loan balance shows the cash a sale frees or needs", "where": "Sale Proceeds vs Payoff"}]
competitors = [
    {"what": "generic profit and loss templates", "lacks": "know nothing of vehicles: no loan view per car, no equity, no replace-or-sell and no break-even utilisation"},
    {"what": "subscription rental-management software", "lacks": "charge every month and rarely let you test a scenario, a refinance or a new vehicle before you commit"},
    {"what": "single-sheet vehicle expense logs", "lacks": "add up costs but never show profit per class, cash after known costs or a safe owner draw"},
    {"what": "budget-model templates", "lacks": "plan a year of revenue but have no depreciation check, no tax set-aside tracker and no year-end pack check"},
    {"what": "loan calculators", "lacks": "work on one loan at a time and never set the payments against revenue, equity and your cash floor"}]
guide = [
    'Open Start and type your business name, your cash floor, the regular owner draw and the share you set aside for income tax (confirm with your adviser).',
    'Keep Profit and Loss, Cash, Tax Set-Aside and Owner Draw up to date each month: the month-end close takes minutes.',
    'Keep Vehicles current: purchase date, price, loan, odometer, status and resale estimate. Age, book value, loan balance and equity fill in.',
    'Add every loan payment to Financing; Loan View shows each financed car with its equity.',
    'Record expenses with a category, vendor and vehicle; Costs by Category adds them up by month.',
    'List the costs you already know for the next 30 days in Known Costs, then open the Owner Draw and Tax Set-Aside tool for the safe draw.',
    'Use the Replace-or-Sell Tool and Best Month to Sell for any vehicle that loses money or is past your replacement age.',
    'Run the Scenario Test after changing the scenario numbers on the Start sheet; read the lowest cash point.',
    'Before you buy, fill Add-a-Vehicle Cases and run the Add-a-Vehicle Business Case; a one-car host also uses the One-Car Host Start-Up Case.',
    'Use the Refinance Check, Early Payoff Test and Sale Proceeds vs Payoff for any loan decision.',
    'At year end run the Year-End Pack Check and send the figures to your accountant.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Finance Dashboard and the charts every week. Miles are the demo unit, set your own.']
listing = {"title": "Car Rental Finance Excel Template: Profit and Loss, Loans, Replace-or-Sell, Owner Draw, Tax Set-Aside, Scenarios",
    "headline": "Know your profit, your loans and your safe owner draw",
    "tags": ["car rental", "fleet finance", "rental profit", "excel template", "vehicle loan", "replace or sell", "owner draw", "tax set aside", "cash flow", "break even", "scenario test", "fleet planning", "small business"],
    "description": ("Run the money side of a small car and van rental or a car-sharing host fleet in one Excel workbook. Built for an owner-operator, a manager and a part-time bookkeeper who need one clear view of profit, loans, cash and the owner draw. "
        "Profit and Loss shows 24 months of revenue and every cost line, with margin, average daily rate (revenue per rented day) and break-even revenue. Profit by Class and Month shows which class earns and which does not. Vehicles keeps price, loan, resale estimate, book value and equity of every car, and Loan View shows each financed car.\n\n"
        "Cash, Tax Set-Aside and Owner Draw follow every month, Known Costs lists what you must pay in the next 30 days, and the Draw Plan shows the safe draw for the next 12 months. Replace or Sell Inputs and Keep or Replace give the cost per day of keeping a vehicle against replacing it. Scenarios and Scenario Months test utilisation down, more cars, a higher financing rate, higher marketplace fees and rates up.\n\n"
        f"{len(tools)} tools answer the weekly questions: replace, sell or keep; the best month to sell; the loan view; a refinance; an early payoff; profit by class; a safe owner draw; the tax set-aside; the scenario test; a sensitivity row; the business case for a new vehicle; a one-car host start-up case; the depreciation check; fleet cost per day; break-even revenue; the financing mix; sale proceeds against payoff; and the year-end pack check. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the owner, manager, bookkeeper, accountant, lender and others.\n\n"
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data. Depreciation, replacement age, tax set-aside and every target are example settings, set your own. Amounts are plain numbers in one currency of your choice. It helps you keep track of your numbers and promises no result; check your local rules and confirm tax questions with your adviser."),
    "features": ["24-month profit and loss with margin and break-even", "Profit by vehicle class and month", "Loan view with equity of every financed car", "Replace-or-sell tool with cost per day", "Safe owner draw above your cash floor",
                 "Tax set-aside tracker, confirm with your adviser", "Scenario test: utilisation, cars, rates, fees", "Add-a-vehicle business case with payback", "One-car host start-up case", f"{len(tools)} decision tools",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p8', slug='car-rental-finance', profession='Car Rental Business', name='Finance, Replace-or-Sell and Owner Pay',
         tagline='Know your profit, your loans and your safe owner draw', price_usd=29, colors={"primary": "#1D3557", "accent": "#E63946"},
         settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
         suite={"key": SUITE, "part": 8, "of": 8, "focus": "Finance, replace-or-sell and owner pay"}, signature=signature, competitors=competitors, tools=tools,
         messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cr8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
