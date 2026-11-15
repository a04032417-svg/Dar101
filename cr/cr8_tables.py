"""Car rental suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr8_lists import *
import cr8_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def R(t, c): return '{range:%s.%s}' % (t, c)
YES = '{list:yesno.yes}'
SOLD = tok('vstatus', 'Sold'); REPAIRS = tok('expcat', 'Maintenance and repairs'); PURCH = tok('vevent', 'Purchase')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def WIN(t, n, col='month'): return '%s,">="&EDATE(%s,-%d),%s,"<"&%s' % (R(t, col), MS, n, R(t, col), MS)
def PS(col, n, t='pnl'): return 'SUMIFS(%s,%s)' % (R(t, col), WIN(t, n))
def A3(col): return 'AVERAGEIFS(%s,%s)' % (R('pnl', col), WIN('pnl', 3))
CASH_NOW = 'INDEX(%s,MATCH(%s,%s,0))' % (R('cash', 'closing'), MS, R('cash', 'month'))
KNOWN = 'SUM(%s)' % R('known_costs', 'amount')

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('dep_pct', 'Depreciation a month, share of price (example)', 'pct', DEP_PCT),
    S('dep_floor', 'Book value never falls below this share of price', 'pct', DEP_FLOOR), S('margin_target', 'Profit margin you want to hold (example, set your own)', 'pct', 0.12),
    S('fin_limit', 'Most financing payments, share of revenue (example)', 'pct', 0.20), S('cash_floor', 'Cash floor you never go below', 'money', CASH_FLOOR),
    S('owner_draw', 'Regular owner draw a month', 'money', OWNER_DRAW), S('tax_pct', 'Tax set-aside share of profit (confirm with adviser)', 'pct', TAX_SET_ASIDE_PCT),
    S('replace_miles', 'Replacement miles (example, set your own)', 'int', 90000), S('replace_months', 'Replacement age in months (example, set your own)', 'int', 36),
    S('new_loan_rate', 'Rate of a new vehicle loan (example)', 'pct', 0.075), S('repair_new', 'Repairs a year on a new vehicle (example)', 'money', 350),
    S('sell_cost_pct', 'Cost of selling a vehicle, share of the price', 'pct', 0.03), S('util_target', 'Utilisation you plan for (example, set your own)', 'pct', 0.75),
    S('sc_util_drop', 'Scenario: utilisation falls by (points)', 'pct', 0.10), S('sc_cars', 'Scenario: cars added', 'int', 2), S('sc_fin_pts', 'Scenario: financing rate rises by (points)', 'pct', 0.01),
    S('sc_fee_up', 'Scenario: marketplace fees rise by (share of fees)', 'pct', 0.20), S('sc_rate_up', 'Scenario: rates rise by', 'pct', 0.05), S('budget_growth', 'Budget growth on the same month last year', 'pct', 0.05),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 profit and loss --------------------------------------------------------
tables.append(T('pnl', 'Profit and Loss', 'Profit and loss statement by month',
    'One row per month: revenue and every cost line; costs, profit, margin, average daily rate (revenue per rented day), revenue per available car-day, break-even revenue and a budget fill in.', [
    C('row_id', 'Row', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('vehicles', 'Vehicles', 'int', 9), C('rented_days', 'Rented days', 'int', 10), C('utilisation', 'Utilisation', 'pct', 10),
    C('revenue', 'Revenue', 'money', 12), C('channel_fees', 'Channel fees', 'money', 12), C('financing', 'Financing', 'money', 12), C('insurance', 'Insurance', 'money', 12), C('maintenance', 'Maintenance', 'money', 12),
    C('fuel_charge', 'Fuel or charge', 'money', 12), C('staff', 'Staff', 'money', 12), C('overhead', 'Overhead', 'money', 12), C('depreciation', 'Depreciation', 'money', 12),
    CA('vehicle_costs', 'Vehicle costs', 'money', '{col:channel_fees}+{col:financing}+{col:insurance}+{col:maintenance}+{col:fuel_charge}+{col:depreciation}', 12),
    CA('costs', 'Total costs', 'money', '{col:vehicle_costs}+{col:staff}+{col:overhead}', 12), CA('profit', 'Profit', 'money', '{col:revenue}-{col:costs}', 12),
    CA('margin', 'Profit margin', 'pct', 'IF({col:revenue}>0,{col:profit}/{col:revenue},0)', 10), CA('adr', 'Average daily rate', 'money', 'IF({col:rented_days}>0,{col:revenue}/{col:rented_days},0)', 11),
    CA('revpac', 'Revenue per available car-day', 'money', 'IF({col:rented_days}>0,{col:revenue}*{col:utilisation}/{col:rented_days},0)', 11),
    CA('financing_share', 'Financing share of revenue', 'pct', 'IF({col:revenue}>0,{col:financing}/{col:revenue},0)', 10),
    CA('breakeven', 'Break-even revenue', 'money', 'IF({col:revenue}>0,({col:costs}-{col:channel_fees}-{col:fuel_charge})/(1-({col:channel_fees}+{col:fuel_charge})/{col:revenue}),0)', 12),
    CA('profit_cash', 'Profit before depreciation', 'money', '{col:profit}+{col:depreciation}', 12),
    CA('season_index', 'Season index', 'num', '{col:revenue}/AVERAGE({range:pnl.revenue})', 9), CA('year', 'Year', 'int', 'YEAR({col:month})', 7), CA('dep_pct', 'Depreciation setting a month', 'pct', '{set:dep_pct}', 10),
    CA('budget', 'Budget, same month next year', 'money', 'ROUND({col:revenue}*(1+{set:budget_growth}),0)', 12)],
    D.pnl_d(), 40, [A('profit', '< 0', 'bad'), A('margin', '>= {set:margin_target}', 'good')]))
# 2 profit by class and month -----------------------------------------------
tables.append(T('class_month', 'Profit by Class and Month', 'Profit by vehicle class and month',
    'One row per class and month from your vehicle months: available and rented days, revenue and vehicle costs; profit, utilisation, average daily rate and the 12-month margin fill in.', [
    LST('class', 'Class', 'class', 12, required=True), C('month', 'Month', 'date', 11), C('available_days', 'Available days', 'int', 10), C('rented_days', 'Rented days', 'int', 10), C('revenue', 'Revenue', 'money', 12), C('costs', 'Vehicle costs', 'money', 12),
    CA('profit', 'Profit', 'money', '{col:revenue}-{col:costs}', 12), CA('utilisation', 'Utilisation', 'pct', 'IF({col:available_days}>0,{col:rented_days}/{col:available_days},0)', 10),
    CA('adr', 'Average daily rate', 'money', 'IF({col:rented_days}>0,{col:revenue}/{col:rented_days},0)', 11),
    CA('margin12', 'Class margin, 12 months', 'pct', 'IFERROR(SUMIFS({range:class_month.profit},{range:class_month.class},{col:class},%s)/SUMIFS({range:class_month.revenue},{range:class_month.class},{col:class},%s),0)' % (WIN('class_month', 12), WIN('class_month', 12)), 10)],
    D.class_month_d(), 200, [A('profit', '< 0', 'bad')]))
# 3 class profit -------------------------------------------------------------
tables.append(T('class_profit', 'Class Profit', 'Profit of each class, last 12 months',
    'One row per class: profit of the last 12 full months and profit per vehicle fill in from the class months and the Vehicles sheet.', [
    LST('class', 'Class', 'class', 14, required=True),
    CA('profit_12m', 'Profit, 12 months', 'money', 'SUMIFS({range:class_month.profit},{range:class_month.class},{col:class},%s)' % WIN('class_month', 12), 13),
    CA('per_vehicle', 'Profit per vehicle', 'money', 'IFERROR({col:profit_12m}/COUNTIFS({range:vehicles.class},{col:class},{range:vehicles.status},"<>"&%s),0)' % SOLD, 13)], D.class_profit_d(), 50))
# 4 vehicles -----------------------------------------------------------------
tables.append(T('vehicles', 'Vehicles', 'Fleet register with price, loan, book value and equity',
    'One row per vehicle: purchase, loan and resale estimate; age, book value (your depreciation setting), loan balance, equity, months left and write-down fill in by themselves.', [
    C('vehicle_id', 'Vehicle ID', 'text', 10, required=True), C('vehicle', 'Vehicle', 'text', 22), LST('class', 'Class', 'class', 12), C('purchase_date', 'Purchase date', 'date', 11), C('purchase_price', 'Purchase price', 'money', 12),
    C('financed', 'Financed', 'bool', 8), C('loan_amount', 'Loan amount', 'money', 11), C('loan_rate', 'Loan rate', 'pct', 9), C('loan_months', 'Loan months', 'int', 9), C('monthly_payment', 'Monthly payment', 'money', 11),
    C('odometer', 'Odometer, miles', 'int', 11), LST('status', 'Status', 'vstatus', 12), C('sold_date', 'Sold date', 'date', 11), C('resale_estimate', 'Resale estimate', 'money', 12), C('insurance_year', 'Insurance a year', 'money', 11),
    CA('age_months', 'Age in months', 'int', 'IF({col:sold_date}>0,DATEDIF({col:purchase_date},{col:sold_date},"M"),DATEDIF({col:purchase_date},{today},"M"))', 9),
    CA('book_value', 'Book value', 'money', 'IF({col:status}=%s,0,ROUND({col:purchase_price}*MAX({set:dep_floor},1-{set:dep_pct}*{col:age_months}),0))' % SOLD, 12),
    CA('loan_balance', 'Loan balance', 'money', 'IF(AND({col:financed}=%s,{col:status}<>%s),SUMIFS({range:financing.balance_after},{range:financing.vehicle},{col:vehicle},{range:financing.date},SUMPRODUCT(MAX(({range:financing.vehicle}={col:vehicle})*{range:financing.date}))),0)' % (YES, SOLD), 12),
    CA('equity', 'Equity', 'money', 'IF({col:status}=%s,0,{col:resale_estimate}-{col:loan_balance})' % SOLD, 12),
    CA('months_left', 'Loan months left', 'int', 'IF({col:loan_balance}>0,IFERROR(ROUNDUP(NPER({col:loan_rate}/12,-{col:monthly_payment},{col:loan_balance}),0),0),0)', 9),
    CA('write_down', 'Write-down needed', 'money', 'IF({col:status}=%s,0,MAX(0,{col:book_value}-{col:resale_estimate}))' % SOLD, 12),
    CA('interest_year', 'Interest a year', 'money', 'ROUND({col:loan_balance}*{col:loan_rate},2)', 11)],
    D.vehicles_d(), 60, [A('equity', '< 0', 'bad'), A('write_down', '> 0', 'warn'), A('status', '= ' + SOLD, 'warn')]))
# 5 financing ----------------------------------------------------------------
tables.append(T('financing', 'Financing', 'Loan payments with interest, principal and balance',
    'One row per loan payment: date, vehicle, payment, interest, principal and the balance after; the interest share of each payment fills in.', [
    C('fin_id', 'Payment ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), LST('class', 'Class', 'class', 12),
    C('payment', 'Payment', 'money', 11), C('interest', 'Interest', 'money', 11), C('principal', 'Principal', 'money', 11), C('balance_after', 'Balance after', 'money', 12),
    CA('interest_share', 'Interest share of payment', 'pct', 'IF({col:payment}>0,{col:interest}/{col:payment},0)', 10)],
    D.financing_d(), 400))
# 6 loan view ----------------------------------------------------------------
def VL(col): return LKN('vehicles.' + col, 'vehicles.vehicle', 'vehicle')
tables.append(T('loan_view', 'Loan View', 'Loans of the financed cars in the fleet',
    'One row per financed car in the fleet: payment, balance, rate, months left, resale estimate and equity (resale minus balance) fill in from the Vehicles sheet.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22, required=True), LST('class', 'Class', 'class', 12),
    CA('payment', 'Monthly payment', 'money', VL('monthly_payment'), 11), CA('balance', 'Loan balance', 'money', VL('loan_balance'), 12), CA('rate', 'Loan rate', 'pct', VL('loan_rate'), 9),
    CA('months_left', 'Months left', 'int', VL('months_left'), 8), CA('resale', 'Resale estimate', 'money', VL('resale_estimate'), 12), CA('equity', 'Equity', 'money', '{col:resale}-{col:balance}', 12),
    CA('equity_share', 'Equity share of resale', 'pct', 'IF({col:resale}>0,{col:equity}/{col:resale},0)', 10)], D.loan_view_d(), 40, [A('equity_share', '< 0.1', 'warn'), A('equity', '< 0', 'bad')]))
# 7 expenses -----------------------------------------------------------------
tables.append(T('expenses', 'Expenses', 'Expenses by category, vendor and vehicle',
    'One row per expense: date, category, vendor, vehicle and amount; the vehicle name fills in from the vehicle ID.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('category', 'Category', 'expcat', 24), LST('vendor', 'Vendor', 'vendor', 24),
    C('vehicle_id', 'Vehicle ID', 'text', 10), C('amount', 'Amount', 'money', 11),
    CA('vehicle', 'Vehicle', 'text', LKT('vehicles.vehicle', 'vehicles.vehicle_id', 'vehicle_id'), 22)], D.expenses_d(), 1000))
# 8 costs by category and month ----------------------------------------------
tables.append(T('cost_cat', 'Costs by Category', 'Costs by category and month',
    'One row per category and month, added up from every expense of the month; use it to see which cost grows.', [
    LST('category', 'Category', 'expcat', 26, required=True), C('month', 'Month', 'date', 11), C('amount', 'Amount', 'money', 12)], D.cost_cat_d(), 250))
# 9 cash ---------------------------------------------------------------------
tables.append(T('cash', 'Cash', 'Cash by month',
    'One row per month: opening cash, receipts, operating costs, vehicle purchases (down payments) and sales, owner draw and tax set-aside; closing cash and the net flow fill in.', [
    C('row_id', 'Row', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('opening', 'Opening cash', 'money', 12), C('receipts', 'Receipts', 'money', 12), C('operating_costs', 'Operating costs', 'money', 12),
    C('vehicle_purchases', 'Vehicle purchases', 'money', 12), C('vehicle_sales', 'Vehicle sales', 'num', 12), C('owner_draw', 'Owner draw', 'num', 11), C('tax_set_aside', 'Tax set-aside', 'money', 11),
    CA('closing', 'Closing cash', 'money', '{col:opening}+{col:receipts}-{col:operating_costs}-{col:vehicle_purchases}+{col:vehicle_sales}-{col:owner_draw}-{col:tax_set_aside}', 12),
    CA('net_flow', 'Net flow', 'money', '{col:closing}-{col:opening}', 12), CA('floor_gap', 'Closing above the floor', 'money', '{col:closing}-{set:cash_floor}', 12)],
    D.cash_d(), 40, [A('floor_gap', '< 0', 'bad')]))
# 10 tax ---------------------------------------------------------------------
tables.append(T('tax', 'Tax Set-Aside', 'Income tax set-aside by month (confirm with your adviser)',
    'One row per month: the amount set aside and the amount paid to tax; profit, the set-aside you need at your setting, the gap and the running balance fill in. Confirm with your adviser.', [
    C('row_id', 'Row', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('set_aside', 'Set aside', 'money', 11), C('paid_to_tax', 'Paid to tax', 'num', 11),
    CA('profit', 'Profit of the month', 'money', 'SUMIFS({range:pnl.profit},{range:pnl.month},{col:month})', 12),
    CA('needed', 'Set-aside needed', 'money', 'ROUND(MAX(0,{col:profit})*{set:tax_pct},2)', 11), CA('gap', 'Set aside minus needed', 'money', '{col:set_aside}-{col:needed}', 11),
    CA('balance', 'Balance held', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.month},"<="&{col:month})-SUMIFS({range:tax.paid_to_tax},{range:tax.month},"<="&{col:month})', 12)],
    D.tax_d(), 40, [A('gap', '< 0', 'warn')]))
# 11 owner draw --------------------------------------------------------------
tables.append(T('draw', 'Owner Draw', 'Owner draw by month',
    'One row per month: the regular draw and any extra draw; the total, the year and the total of the year fill in.', [
    C('draw_id', 'Draw ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('regular_draw', 'Regular draw', 'num', 11), C('extra_draw', 'Extra draw', 'num', 11), LST('status', 'Status', 'paystatus', 10),
    CA('total', 'Total draw', 'money', '{col:regular_draw}+{col:extra_draw}', 11), CA('year', 'Year', 'int', 'YEAR({col:month})', 7),
    CA('year_total', 'Draw total of the year', 'money', 'SUMIFS({range:draw.total},{range:draw.year},{col:year})', 12)], D.draw_d(), 40, [A('extra_draw', '> 0', 'warn')]))
# 12 draw plan ---------------------------------------------------------------
AVGNET = '((SUMIFS(%s,%s)-SUMIFS(%s,%s)-SUMIFS(%s,%s))/6)' % (R('cash', 'receipts'), WIN('cash', 6), R('cash', 'operating_costs'), WIN('cash', 6), R('cash', 'tax_set_aside'), WIN('cash', 6))
tables.append(T('draw_plan', 'Draw Plan', 'Safe owner draw for the next 12 months',
    'One row per month ahead: your last 6 months of net cash carried forward with the planned draw; cash before the draw, the safe draw above the cash floor, cash after and a status fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('ahead', 'Months ahead', 'int', 9),
    CA('cash_before', 'Cash before the draw', 'money', 'ROUND(%s+{col:ahead}*%s-({col:ahead}-1)*{set:owner_draw},0)' % (CASH_NOW, AVGNET), 12),
    CA('safe_draw', 'Safe draw', 'money', 'MAX(0,MIN({set:owner_draw},{col:cash_before}-{set:cash_floor}))', 11),
    CA('cash_after', 'Cash after the planned draw', 'money', '{col:cash_before}-{set:owner_draw}', 12),
    CA('status', 'Status', 'text', 'IF({col:cash_after}>={set:cash_floor},%s,%s)' % (vb('Safe to draw'), vb('Draw less')), 12)], D.draw_plan_d(), 20, [A('status', '= ' + vb('Draw less'), 'warn'), A('status', '= ' + vb('Safe to draw'), 'good')]))
# 13 known costs -------------------------------------------------------------
tables.append(T('known_costs', 'Known Costs', 'Known costs in the next 30 days',
    'One row per cost you already know: loan payments, renewals, payroll, rent and bills with the date and amount; the days away fill in. The Owner Draw tool takes the total.', [
    C('cost_id', 'Cost ID', 'text', 9, required=True), C('item', 'Item', 'text', 36), LST('kind', 'Kind', 'costkind', 14), C('date', 'Date', 'date', 11), C('amount', 'Amount', 'money', 11),
    CA('days_away', 'Days away', 'int', '{col:date}-{today}', 9)], D.known_costs_d(), 60))
# 14 replace or sell inputs --------------------------------------------------
REP12 = 'SUMIFS({range:expenses.amount},{range:expenses.vehicle_id},{col:vehicle_id},{range:expenses.category},%s,{range:expenses.date},">="&({today}-365))' % REPAIRS
tables.append(T('replace_in', 'Replace or Sell Inputs', 'Replace-or-sell inputs per vehicle',
    'One row per vehicle in the fleet: age, miles, resale estimate, repair cost of 12 months, loan balance and new vehicle cost; 12-month profit and the yearly cost of keeping or replacing fill in.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22, required=True), C('new_cost', 'New vehicle cost', 'money', 12), C('profit_12m', 'Profit, 12 months', 'money', 12), C('rev_12m', 'Revenue, 12 months', 'money', 12),
    C('review_on', 'Review on', 'date', 11),
    CA('vehicle_id', 'Vehicle ID', 'text', LKT('vehicles.vehicle_id', 'vehicles.vehicle', 'vehicle'), 10), CA('class', 'Class', 'text', LKT('vehicles.class', 'vehicles.vehicle', 'vehicle'), 12),
    CA('age_months', 'Age in months', 'int', VL('age_months'), 9), CA('miles', 'Odometer miles', 'int', VL('odometer'), 10), CA('resale', 'Resale estimate', 'money', VL('resale_estimate'), 12),
    CA('repair_12m', 'Repair cost, 12 months', 'money', REP12, 12), CA('balance', 'Financing balance', 'money', VL('loan_balance'), 12), CA('equity', 'Equity', 'money', '{col:resale}-{col:balance}', 11),
    CA('price', 'Purchase price', 'money', VL('purchase_price'), 11), CA('book_value', 'Book value', 'money', VL('book_value'), 11), CA('rate', 'Loan rate', 'pct', VL('loan_rate'), 9), CA('insurance', 'Insurance a year', 'money', VL('insurance_year'), 11),
    CA('keep_year', 'Cost of keeping one more year', 'money', '{col:repair_12m}+MIN({col:price}*{set:dep_pct}*12,MAX(0,{col:book_value}-{col:price}*{set:dep_floor}))+{col:balance}*{col:rate}+{col:insurance}', 13),
    CA('replace_year', 'Cost of replacing, first year', 'money', '{col:new_cost}*{set:dep_pct}*12+{col:new_cost}*0.8*{set:new_loan_rate}+{col:insurance}+{set:repair_new}+{col:resale}*{set:sell_cost_pct}', 13)],
    D.replace_d(), 60))
# 15 keep or replace ---------------------------------------------------------
def RP(col): return LKN('replace_in.' + col, 'replace_in.vehicle', 'vehicle')
tables.append(T('keep_replace', 'Keep or Replace', 'Cost per day of keeping against replacing',
    'One row per vehicle: cost per day of keeping one more year, cost per day of replacing, the difference, 12-month profit and a verdict (keep, sell this season or replace).', [
    REF('vehicle', 'Vehicle', 'replace_in.vehicle', 22, required=True),
    CA('keep_cost', 'Keep cost a day', 'money', 'ROUND(%s/365,2)' % RP('keep_year'), 11), CA('replace_cost', 'Replace cost a day', 'money', 'ROUND(%s/365,2)' % RP('replace_year'), 11),
    CA('difference', 'Keep minus replace a day', 'money', '{col:keep_cost}-{col:replace_cost}', 11), CA('profit_12m', 'Profit, 12 months', 'money', RP('profit_12m'), 12),
    CA('age_months', 'Age in months', 'int', RP('age_months'), 9), CA('miles', 'Odometer miles', 'int', RP('miles'), 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:profit_12m}<0,%s,IF(AND({col:keep_cost}>{col:replace_cost},OR({col:age_months}>={set:replace_months},{col:miles}>={set:replace_miles})),%s,%s))' % (va('Sell this season'), va('Replace'), va('Keep')), 14)],
    D.keep_replace_d(), 60, [A('verdict', '= ' + va('Sell this season'), 'bad'), A('verdict', '= ' + va('Replace'), 'warn'), A('verdict', '= ' + va('Keep'), 'good')]))
# 16 scenarios ---------------------------------------------------------------
tables.append(T('scenarios', 'Scenarios', 'Scenarios for the next 12 months',
    'One row per scenario with what changes (the numbers are your settings); profit of the next 12 months fills in from the Scenario Months sheet.', [
    LST('scenario', 'Scenario', 'scen', 20, required=True), C('change', 'What changes', 'text', 44),
    CA('profit_12m', 'Profit, next 12 months', 'money', 'SUMIFS({range:scenario_months.profit},{range:scenario_months.scenario},{col:scenario})', 14)], D.scenarios_d(), 20))
# 17 scenario months ---------------------------------------------------------
SC = lambda i: '{col:scenario}=' + tok('scen', SCENARIOS[i])
IDX = 'IF(%s,1,IF(%s,2,IF(%s,3,IF(%s,4,IF(%s,5,6)))))' % tuple(SC(i) for i in range(5))
def LY(*cols): return '+'.join('SUMIFS(%s,%s,{col:ref_month})' % (R('pnl', c), R('pnl', 'month')) for c in cols)
TREND = 'MIN(1.15,MAX(0.85,1+0.5*(IFERROR(%s/SUMIFS(%s,%s,">="&EDATE(%s,-15),%s,"<"&EDATE(%s,-12)),1)-1)))' % (PS('revenue', 3), R('pnl', 'revenue'), R('pnl', 'month'), MS, R('pnl', 'month'), MS)
tables.append(T('scenario_months', 'Scenario Months', 'Scenario by month ahead: revenue, costs, profit and cash',
    'One row per scenario and month ahead: last year the same month times your recent trend, with the scenario change applied; revenue, costs, profit and cash fill in. Set the changes on the Start sheet.', [
    LST('scenario', 'Scenario', 'scen', 20, required=True), C('ahead', 'Month ahead', 'int', 9),
    CA('idx', 'Scenario number', 'int', IDX, 8), CA('month', 'Month', 'date', 'EDATE(%s,{col:ahead})' % MS, 11),
    CA('ref_month', 'Same month last year', 'date', 'IF(EDATE({col:month},-12)<%s,EDATE({col:month},-12),EDATE({col:month},-24))' % MS, 11),
    CA('trend', 'Trend', 'num', TREND, 8), CA('util_now', 'Utilisation, last 3 months', 'pct', A3('utilisation'), 9), CA('veh_now', 'Vehicles, last 3 months', 'num', A3('vehicles'), 9),
    CA('fleetf', 'Fleet size factor', 'num', 'MIN(1.5,MAX(0.8,IFERROR({col:veh_now}/SUMIFS(%s,%s,{col:ref_month}),1)))' % (R('pnl', 'vehicles'), R('pnl', 'month')), 8),
    CA('ly_revenue', 'Revenue, same month last year', 'money', LY('revenue'), 12), CA('ly_var', 'Channel fees and fuel, last year', 'money', LY('channel_fees', 'fuel_charge'), 12),
    CA('ly_fleet', 'Financing, insurance, repairs, last year', 'money', LY('financing', 'insurance', 'maintenance'), 12), CA('ly_dep', 'Depreciation, last year', 'money', LY('depreciation'), 12),
    CA('ly_staff', 'Staff and overhead, last year', 'money', LY('staff', 'overhead'), 12),
    CA('per_car', 'Cash cost of one more car a month', 'money', 'IF({col:veh_now}>0,(%s+%s+%s)/{col:veh_now},0)' % (A3('financing'), A3('insurance'), A3('maintenance')), 12),
    CA('per_car_dep', 'Depreciation of one more car', 'money', 'IF({col:veh_now}>0,%s/{col:veh_now},0)' % A3('depreciation'), 12),
    CA('rev_factor', 'Revenue factor', 'num', 'CHOOSE({col:idx},1,1-{set:sc_util_drop}/{col:util_now},1+{set:sc_cars}/{col:veh_now},1,1,1+{set:sc_rate_up})', 8),
    CA('revenue', 'Revenue', 'money', 'ROUND({col:ly_revenue}*{col:trend}*{col:rev_factor},0)', 12),
    CA('cash_costs', 'Cash costs', 'money', 'ROUND({col:ly_var}*{col:trend}*{col:rev_factor}*IF({col:idx}=5,1+{set:sc_fee_up},1)+{col:ly_fleet}*{col:fleetf}+IF({col:idx}=3,{set:sc_cars}*{col:per_car},0)+IF({col:idx}=4,SUM(%s)*{set:sc_fin_pts}/12,0)+{col:ly_staff},0)' % R('vehicles', 'loan_balance'), 12),
    CA('depreciation', 'Depreciation', 'money', 'ROUND({col:ly_dep}*{col:fleetf}+IF({col:idx}=3,{set:sc_cars}*{col:per_car_dep},0),0)', 12),
    CA('profit', 'Profit', 'money', '{col:revenue}-{col:cash_costs}-{col:depreciation}', 12),
    CA('cash_flow', 'Cash flow', 'money', 'ROUND({col:revenue}-{col:cash_costs}-MAX(0,{col:profit})*{set:tax_pct}-{set:owner_draw}-IF(AND({col:idx}=3,{col:ahead}=1),{set:sc_cars}*AVERAGEIFS(%s,%s,"<>"&%s)*0.2,0),0)' % (R('vehicles', 'purchase_price'), R('vehicles', 'status'), SOLD), 12),
    CA('cash', 'Cash at month end', 'money', 'ROUND(%s+SUMIFS({range:scenario_months.cash_flow},{range:scenario_months.scenario},{col:scenario},{range:scenario_months.ahead},"<="&{col:ahead}),0)' % CASH_NOW, 12)],
    D.scenario_months_d(), 100, [A('cash', '< {set:cash_floor}', 'bad')]))
# 18 add-a-vehicle cases -----------------------------------------------------
FEESH = '(SUMIFS(%s,%s)/SUMIFS(%s,%s))' % (R('pnl', 'channel_fees'), WIN('pnl', 12), R('pnl', 'revenue'), WIN('pnl', 12))
FUELD = '(SUMIFS(%s,%s)/SUMIFS(%s,%s))' % (R('pnl', 'fuel_charge'), WIN('pnl', 12), R('pnl', 'rented_days'), WIN('pnl', 12))
VMON = 'SUMIFS(%s,%s)' % (R('pnl', 'vehicles'), WIN('pnl', 12))
tables.append(T('cases', 'Add-a-Vehicle Cases', 'Business cases for a new vehicle',
    'One row per case: class, price, financing share, expected utilisation by season and daily rate; monthly profit, payback months, break-even utilisation and a verdict fill in from your own cost history.', [
    C('case_id', 'Case', 'text', 9, required=True), LST('class', 'Class', 'class', 12), C('price', 'Price', 'money', 11), C('financing_share', 'Financing share', 'pct', 10), C('util_peak', 'Utilisation, peak', 'pct', 10),
    C('util_shoulder', 'Utilisation, shoulder', 'pct', 10), C('util_off', 'Utilisation, off-peak', 'pct', 10), C('day_rate', 'Daily rate', 'money', 10), C('overhead_load', 'Share of staff and overhead added', 'pct', 10),
    C('plan_date', 'Plan date', 'date', 11),
    CA('avg_util', 'Average utilisation', 'pct', 'ROUND((3*{col:util_peak}+5*{col:util_shoulder}+4*{col:util_off})/12,3)', 10), CA('rented_days', 'Rented days a month', 'num', 'ROUND(30.4*{col:avg_util},1)', 9),
    CA('revenue_month', 'Revenue a month', 'money', 'ROUND({col:rented_days}*{col:day_rate},0)', 11), CA('fee_month', 'Channel fees', 'money', 'ROUND({col:revenue_month}*%s,0)' % FEESH, 10),
    CA('run_month', 'Fuel or charge', 'money', 'ROUND({col:rented_days}*%s,0)' % FUELD, 10),
    CA('insurance_month', 'Insurance a month', 'money', 'ROUND(IFERROR(AVERAGEIFS(%s,%s,{col:class},%s,"<>"&%s),1400)/12,0)' % (R('vehicles', 'insurance_year'), R('vehicles', 'class'), R('vehicles', 'status'), SOLD), 10),
    CA('maint_month', 'Maintenance a month', 'money', 'ROUND(SUMIFS(%s,%s)/%s,0)' % (R('pnl', 'maintenance'), WIN('pnl', 12), VMON), 10),
    CA('overhead_month', 'Staff and overhead share', 'money', 'ROUND((SUMIFS(%s,%s)+SUMIFS(%s,%s))/%s*{col:overhead_load},0)' % (R('pnl', 'staff'), WIN('pnl', 12), R('pnl', 'overhead'), WIN('pnl', 12), VMON), 10),
    CA('loan_payment', 'Loan payment', 'money', 'ROUND(IF({col:financing_share}>0,-PMT({set:new_loan_rate}/12,60,{col:price}*{col:financing_share}),0),0)', 10),
    CA('dep_month', 'Depreciation a month', 'money', 'ROUND({col:price}*{set:dep_pct},0)', 10),
    CA('cash_profit', 'Cash profit a month', 'money', '{col:revenue_month}-{col:fee_month}-{col:run_month}-{col:insurance_month}-{col:maint_month}-{col:overhead_month}-{col:loan_payment}', 11),
    CA('profit', 'Profit a month', 'money', '{col:cash_profit}-{col:dep_month}', 11), CA('down_payment', 'Cash put in', 'money', 'ROUND({col:price}*(1-{col:financing_share}),0)', 11),
    CA('payback', 'Payback months', 'num', 'IF({col:cash_profit}>0,ROUND({col:down_payment}/{col:cash_profit},1),999)', 9),
    CA('breakeven_util', 'Break-even utilisation', 'pct', 'IFERROR(({col:insurance_month}+{col:maint_month}+{col:overhead_month}+{col:loan_payment}+{col:dep_month})/(({col:day_rate}*(1-%s)-%s)*30.4),0)' % (FEESH, FUELD), 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:profit}<=0,%s,IF(AND({col:payback}<=36,{col:avg_util}>={col:breakeven_util}+0.1),%s,%s))' % (va('Do not buy'), va('Buy'), va('Wait')), 12)],
    D.cases_d(), 30, [A('verdict', '= ' + va('Buy'), 'good'), A('verdict', '= ' + va('Do not buy'), 'bad')]))
# 19 fleet value -------------------------------------------------------------
tables.append(T('fleet_value', 'Fleet Value', 'Fleet value by class',
    'One row per class: book value (your depreciation setting) and the loan balance of the vehicles in the fleet fill in from the Vehicles sheet.', [
    LST('class', 'Class', 'class', 14, required=True),
    CA('book_value', 'Book value', 'money', 'SUMIFS({range:vehicles.book_value},{range:vehicles.class},{col:class})', 13), CA('loan_balance', 'Financing balance', 'money', 'SUMIFS({range:vehicles.loan_balance},{range:vehicles.class},{col:class})', 13)],
    D.fleet_value_d(), 20))
# 20 purchases and sales -----------------------------------------------------
tables.append(T('purchases', 'Purchases and Sales', 'Vehicle purchases and sales',
    'One row per purchase or sale: date, amount and the loan taken or paid off; the cash effect fills in. Remove a sold vehicle from the booking calendar.', [
    C('event_id', 'Event', 'text', 9, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), LST('event', 'Event kind', 'vevent', 10), C('date', 'Date', 'date', 11), C('amount', 'Amount', 'money', 12),
    C('loan', 'Loan taken or paid off', 'num', 12),
    CA('cash_effect', 'Cash effect', 'money', 'IF({col:event}=%s,-({col:amount}-{col:loan}),{col:amount}-{col:loan})' % PURCH, 12)], D.purchases_d(), 40, [A('event', '= ' + PURCH, 'good')]))

# message columns: names, phones and the business name -----------------------
def add_msg(tkey, *roles):
    t = next(x for x in tables if x['key'] == tkey)
    have = {c['key'] for c in t['columns']}
    if 'company' not in have: t['columns'].append(CA('company', 'Business name', 'text', '{set:company}', 22))
    for r in roles:
        t['columns'].append(CA(r, r.capitalize() + ' name', 'text', '{list:people.%s}' % r, 10))
        t['columns'].append(CA(r + '_phone', r.capitalize() + ' phone', 'text', '"%s"' % D.PHONES[r], 18))
add_msg('pnl', 'owner', 'manager', 'bookkeeper', 'accountant', 'lender'); add_msg('class_month', 'owner'); add_msg('draw_plan', 'owner'); add_msg('tax', 'owner', 'bookkeeper', 'accountant')
add_msg('draw', 'bookkeeper', 'accountant'); add_msg('loan_view', 'owner', 'lender'); add_msg('keep_replace', 'owner'); add_msg('scenario_months', 'owner'); add_msg('cases', 'owner')
add_msg('financing', 'bookkeeper'); add_msg('purchases', 'manager', 'lender', 'broker', 'bookkeeper', 'mechanic'); add_msg('vehicles', 'manager', 'tyres')

for _t in tables: _t['rows'] = max(50, _t['rows'])
