"""Therapy practice suite part 8: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th8_lists import *
import th8_data as D

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
W0 = 'DATE(YEAR({today}),MONTH({today})-12,1)'            # first day of the 12 complete months before this month
YR = 'DATE(YEAR({today}),1,1)'

settings = [
    S('company', 'Your practice name', 'text', COMPANY), S('profit_target', 'Wanted profit margin', 'pct', 0.15), S('overhead_target', 'Wanted overhead share of revenue (rent and other costs)', 'pct', 0.20),
    S('pay_share_target', 'Wanted pay share of revenue (clinician and staff pay)', 'pct', 0.55), S('target_utilisation', 'Wanted booked share of the session cap', 'pct', 0.85),
    S('target_tolerance', 'How far from a target still counts as healthy', 'pct', 0.05), S('cash_cover_months', 'Wanted months of expenses in cash', 'int', 4),
    S('reserve_low_months', 'Reserve band, lowest months of expenses in cash', 'int', 3), S('reserve_high_months', 'Reserve band, highest months of expenses in cash', 'int', 6),
    S('cover_min_months', 'Months of expenses in cash that are never to be missed', 'int', 1), S('cash_floor', 'Cash floor, the balance that must never be crossed', 'money', 20000),
    S('owner_draw', 'Owner draw a month', 'money', 7000), S('tax_set_aside_pct', 'Tax set-aside share of profit (ask your adviser)', 'pct', 0.25),
    S('employer_cost_pct', 'Employer costs on top of a salary', 'pct', 0.12), S('room_cost_hour', 'Rent, cleaning and power per hour of room time used', 'money', 12),
    S('admin_cost', 'Booking and billing cost per booked session', 'money', 6), S('market_fee_low', 'Local market fee band, low (replace with your own)', 'money', 100),
    S('market_fee_high', 'Local market fee band, high (replace with your own)', 'money', 160), S('payer_wait_months', 'Months before a new clinician can bill a third-party payer', 'int', 3),
    S('room_use_target', 'Wanted share of open room hours that are used', 'pct', 0.35)]
assert 3 <= len(settings) <= 20

tables = []
def PH(k, n, who=None): return CA(k, 'Phone to message', 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % n, 18)

# 1 Profit by month ---------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('pnl', 'Profit by Month', 'Profit and loss statement by month',
    'One row per month: session, group and sublet income less write-offs, then clinician and staff pay, rent and other expenses; profit, margin, pay share, overhead share, owner draw cover and the history rows fill in by themselves.', [
    C('pl_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('sessions', 'Attended sessions', 'int', 10), C('session_revenue', 'Session revenue', 'money', 13), C('group_revenue', 'Group revenue', 'money', 13),
    C('sublet_income', 'Sublet income', 'money', 12), C('write_offs', 'Write-offs', 'money', 11), C('clinician_pay', 'Clinician pay', 'money', 13), C('staff_pay', 'Staff pay', 'money', 11),
    C('rent', 'Rent', 'money', 11), C('other_expenses', 'Other expenses', 'money', 13),
    CA('revenue', 'Revenue', 'money', '{col:session_revenue}+{col:group_revenue}+{col:sublet_income}-{col:write_offs}', 13),
    CA('costs', 'Total costs', 'money', '{col:clinician_pay}+{col:staff_pay}+{col:rent}+{col:other_expenses}', 13),
    CA('profit', 'Profit', 'money', '{col:revenue}-{col:costs}', 13), CA('margin', 'Profit margin', 'pct', 'IFERROR({col:profit}/{col:revenue},0)', 10),
    CA('pay_share', 'Pay share of revenue', 'pct', 'IFERROR(({col:clinician_pay}+{col:staff_pay})/{col:revenue},0)', 11),
    CA('overhead_share', 'Overhead share of revenue', 'pct', 'IFERROR(({col:rent}+{col:other_expenses})/{col:revenue},0)', 11),
    CA('profit_per_session', 'Profit per attended session', 'money', 'IFERROR({col:profit}/{col:sessions},0)', 11),
    CA('kept', 'Profit after the owner draw', 'money', '{col:profit}-{set:owner_draw}', 13),
    CA('margin_flag', 'Margin check', 'text', 'IF({col:margin}>={set:profit_target},%s,%s)' % (vd('Above target'), vd('Below target')), 13),
    CA('ovh_flag', 'Overhead check', 'text', 'IF({col:overhead_share}<{set:overhead_target}-{set:target_tolerance},%s,IF({col:overhead_share}<={set:overhead_target}+{set:target_tolerance},%s,%s))' % (vd('Lean'), vd('In band'), vd('Heavy')), 11),
    CA('profit_3m', 'Average profit of the 3 months before', 'money', 'IFERROR(AVERAGEIFS({range:pnl.profit},{range:pnl.month},">="&DATE(YEAR({col:month}),MONTH({col:month})-3,1),{range:pnl.month},"<"&{col:month}),"")', 14),
    CA('profit_ly', 'Profit, same month last year', 'money', 'IF(COUNTIFS({range:pnl.month},DATE(YEAR({col:month})-1,MONTH({col:month}),1))=0,"",SUMIFS({range:pnl.profit},{range:pnl.month},DATE(YEAR({col:month})-1,MONTH({col:month}),1)))', 14),
    CA('ytd_revenue', 'Revenue, year to this month', 'money', 'SUMIFS({range:pnl.revenue},{range:pnl.month},">="&DATE(YEAR({col:month}),1,1),{range:pnl.month},"<="&{col:month})', 14),
    CA('ytd_profit', 'Profit, year to this month', 'money', 'SUMIFS({range:pnl.profit},{range:pnl.month},">="&DATE(YEAR({col:month}),1,1),{range:pnl.month},"<="&{col:month})', 14)],
    D.pnl_d(), 60, [A('margin_flag', '= ' + vd('Below target'), 'bad'), A('ovh_flag', '= ' + vd('Heavy'), 'warn'), A('profit', '< 0', 'bad')]))

# 2 Service profit by month ---------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('svc_months', 'Service Profit by Month', 'Profit per service type and month',
    'One row per service type and month: booked and attended sessions, revenue, clinician pay, room cost and other cost; profit, margin, profit per session and a Grow, Fix or Drop verdict fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('service', 'Service type', 'svcall', 19), C('booked', 'Booked', 'int', 9), C('sessions', 'Attended', 'int', 9),
    C('revenue', 'Revenue', 'money', 12), C('clinician_pay', 'Clinician pay', 'money', 12), C('room_cost', 'Room cost', 'money', 11), C('other_cost', 'Other cost', 'money', 11),
    CA('profit', 'Profit', 'money', '{col:revenue}-{col:clinician_pay}-{col:room_cost}-{col:other_cost}', 12), CA('margin', 'Margin', 'pct', 'IFERROR({col:profit}/{col:revenue},0)', 10),
    CA('profit_per_session', 'Profit per session', 'money', 'IFERROR({col:profit}/{col:sessions},0)', 11),
    CA('verdict', 'Verdict', 'text', 'IF({col:margin}>={set:profit_target},%s,IF({col:margin}>=-2*{set:target_tolerance},%s,%s))' % (vd('Grow'), vd('Fix'), vd('Drop')), 10),
    PH('owner_phone', 1)], D.svc_months_d(), 400, [A('verdict', '= ' + vd('Drop'), 'bad'), A('verdict', '= ' + vd('Fix'), 'warn'), A('verdict', '= ' + vd('Grow'), 'good'), A('profit', '< 0', 'bad')]))

# 3 Clinician profit by month -------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('clin_months', 'Clinician Profit by Month', 'Profit per clinician and month',
    'One row per clinician and month: session revenue, clinician pay, room cost and other cost; profit and margin fill in by themselves (the owner draws profit instead of a salary).', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('clinician', 'Clinician', 'clin', 18), C('revenue', 'Revenue', 'money', 12), C('clinician_pay', 'Clinician pay', 'money', 12),
    C('room_cost', 'Room cost', 'money', 11), C('other_cost', 'Other cost', 'money', 11),
    CA('profit', 'Profit', 'money', '{col:revenue}-{col:clinician_pay}-{col:room_cost}-{col:other_cost}', 12), CA('margin', 'Margin', 'pct', 'IFERROR({col:profit}/{col:revenue},0)', 10)],
    D.clin_months_d(), 300, [A('margin', '< {set:profit_target}', 'warn'), A('profit', '< 0', 'bad')]))

# 4 Expenses -------------------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('expenses', 'Expenses', 'Expenses by category',
    'One row per expense: date, category, description, amount, who was paid and how; the spend on the category this year fills in by itself.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('category', 'Category', 'ecat', 19), C('description', 'Description', 'text', 30),
    C('amount', 'Amount', 'money', 11), C('paid_to', 'Paid to', 'text', 22), LST('method', 'Method', 'paym', 14),
    CA('category_year', 'Category spend this year', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.date},">="&%s,{range:expenses.date},"<="&{today})' % YR, 13),
    PH('coordinator_phone', 7)], D.expenses_d(), 1500, [A('amount', '>= 1000', 'warn')]))

# 5 Budget -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('budget', 'Budget by Category', 'Yearly budget against spending by category',
    'One row per expense category: the yearly budget you set; the monthly budget, the budget to date, what was spent this year, what is left and the Within budget, Watch or Over budget status fill in by themselves.', [
    C('budget_id', 'Budget ID', 'text', 10, required=True), LST('category', 'Category', 'ecat', 19), C('yearly_budget', 'Yearly budget', 'money', 13),
    CA('monthly_budget', 'Monthly budget', 'money', '{col:yearly_budget}/12', 12),
    CA('budget_to_date', 'Budget to date', 'money', '{col:yearly_budget}*({today}-%s+1)/365' % YR, 13),
    CA('spent', 'Spent this year', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.date},">="&%s,{range:expenses.date},"<="&{today})' % YR, 13),
    CA('left', 'Left in the budget', 'money', '{col:yearly_budget}-{col:spent}', 13), CA('variance', 'Over (+) or under (-) budget to date', 'money', '{col:spent}-{col:budget_to_date}', 14),
    CA('status', 'Status', 'text', 'IF({col:spent}<={col:budget_to_date},%s,IF({col:spent}<=1.1*{col:budget_to_date},%s,%s))' % (vd('Within budget'), vd('Watch'), vd('Over budget')), 13),
    PH('owner_phone', 1), PH('supervisor_phone', 9)], D.budget_d(), 30, [A('status', '= ' + vd('Over budget'), 'bad'), A('status', '= ' + vd('Watch'), 'warn'), A('status', '= ' + vd('Within budget'), 'good')]))

# 6 Room costs by month ------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('room_costs', 'Room Costs by Month', 'Room costs per open hour and per hour used',
    'One row per month: rent, cleaning, utilities, open room hours and room hours used; the total cost, the cost per open hour, the cost per used hour and the use share fill in by themselves.', [
    C('rc_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('rent', 'Rent', 'money', 11), C('cleaning', 'Cleaning', 'money', 11), C('utilities', 'Utilities', 'money', 11),
    C('open_hours', 'Open room hours', 'num', 11), C('used_hours', 'Used room hours', 'num', 11), CA('total_cost', 'Total room cost', 'money', '{col:rent}+{col:cleaning}+{col:utilities}', 12),
    CA('per_open_hour', 'Cost per open hour', 'money', 'IFERROR({col:total_cost}/{col:open_hours},0)', 11), CA('per_used_hour', 'Cost per used hour', 'money', 'IFERROR({col:total_cost}/{col:used_hours},0)', 11),
    CA('use_share', 'Use share of open hours', 'pct', 'IFERROR({col:used_hours}/{col:open_hours},0)', 11),
    CA('use_flag', 'Room use check', 'text', 'IF({col:use_share}<{set:room_use_target},%s,%s)' % (vd('Room use low'), vd('Room use healthy')), 14), PH('landlord_phone', 11)],
    D.room_costs_d(), 60, [A('use_flag', '= ' + vd('Room use low'), 'warn')]))

# 7 Cash months ----------------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('cash', 'Cash Months', 'Cash in and cash out by month',
    'One row per month: opening cash, client, payer and sublet receipts, pay, rent, other expenses, tax set-aside and owner draw, and the closing balance; net flow, months of expenses in cash and the safe draw fill in by themselves.', [
    C('cash_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('opening', 'Opening cash', 'money', 13), C('client_payments', 'Client payments', 'money', 13), C('payer_payments', 'Payer payments', 'money', 13),
    C('sublet_income', 'Sublet income', 'money', 12), C('staff_pay', 'Staff pay', 'money', 12), C('contractor_pay', 'Contractor pay', 'money', 13), C('rent', 'Rent', 'money', 11),
    C('other_expenses', 'Other expenses', 'money', 13), C('tax_set_aside', 'Tax set-aside', 'money', 12), C('owner_draw', 'Owner draw', 'money', 12), C('closing', 'Closing cash', 'money', 13),
    CA('cash_in', 'Cash in', 'money', '{col:client_payments}+{col:payer_payments}+{col:sublet_income}', 12),
    CA('cash_out', 'Cash out', 'money', '{col:staff_pay}+{col:contractor_pay}+{col:rent}+{col:other_expenses}+{col:tax_set_aside}+{col:owner_draw}', 12),
    CA('net_flow', 'Net flow', 'money', '{col:cash_in}-{col:cash_out}', 12),
    CA('months_cover', 'Months of expenses in cash', 'num', 'IFERROR({col:closing}/({col:staff_pay}+{col:contractor_pay}+{col:rent}+{col:other_expenses}),0)', 11),
    CA('safe_draw', 'Safe draw', 'money', 'MAX(0,MIN({set:owner_draw},{col:closing}-{set:cash_floor}))', 11), PH('owner_phone', 1), PH('accountant_phone', 8)],
    D.cash_d(), 30, [A('closing', '< {set:cash_floor}', 'bad'), A('months_cover', '< {set:cover_min_months}', 'warn')]))

# 8 13-week cash forecast -----------------------------------------------------------------------------------------------------------------------------------------------------
START = 'INDEX({range:cash.closing},MATCH(MAX({range:cash.month}),{range:cash.month},0))'
tables.append(T('forecast', '13-Week Cash Forecast', '13-week cash flow forecast',
    'One row per week: the receipts and payments you expect from your own history; the net flow, the closing balance from today\'s cash and the warning against the cash floor fill in by themselves.', [
    C('fc_id', 'Row ID', 'text', 9, required=True), LST('week', 'Week', 'wk', 10), C('week_start', 'Week starting', 'date', 12), C('client_payments', 'Client payments', 'money', 13), C('payer_payments', 'Payer payments', 'money', 13),
    C('pay', 'Pay', 'money', 11), C('rent_costs', 'Rent and costs', 'money', 13), C('tax_set_aside', 'Tax set-aside', 'money', 12), C('owner_draw', 'Owner draw', 'money', 12),
    CA('net', 'Net flow', 'money', '{col:client_payments}+{col:payer_payments}-{col:pay}-{col:rent_costs}-{col:tax_set_aside}-{col:owner_draw}', 12),
    CA('closing', 'Closing cash', 'money', '%s+SUMPRODUCT(({range:forecast.week_start}<={col:week_start})*({range:forecast.client_payments}+{range:forecast.payer_payments}-{range:forecast.pay}-{range:forecast.rent_costs}-{range:forecast.tax_set_aside}-{range:forecast.owner_draw}))' % START, 13),
    CA('floor', 'Cash floor', 'money', '{set:cash_floor}', 11),
    CA('below_floor', 'Floor check', 'text', 'IF({col:closing}<{set:cash_floor},%s,%s)' % (vd('Below the floor'), vd('Above the floor')), 13),
    CA('lowest', 'Lowest week closing', 'money', 'MIN({range:forecast.closing})', 13), PH('owner_phone', 1)],
    D.forecast_d(), 20, [A('below_floor', '= ' + vd('Below the floor'), 'bad')]))

# 9 Tax set-aside -----------------------------------------------------------------------------------------------------------------------------------------------------------------
LK = lambda col: 'IFERROR(INDEX({range:pnl.%s},MATCH({col:month},{range:pnl.month},0)),0)' % col
tables.append(T('tax', 'Tax Set-aside', 'Income tax set-aside by month (confirm with your adviser)',
    'One row per month: the set-aside share, the due date, when it was paid and the status; revenue, costs, profit and the set-aside amount come from Profit by Month (confirm the share with your adviser).', [
    C('tax_id', 'Tax ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), CA('revenue', 'Revenue', 'money', LK('revenue'), 13), CA('costs', 'Costs', 'money', LK('costs'), 13), CA('profit', 'Profit', 'money', LK('profit'), 12),
    C('set_aside_pct', 'Set-aside share', 'pct', 10), CA('set_aside', 'Set-aside amount', 'money', 'MAX(0,{col:profit})*{col:set_aside_pct}', 13), C('due_date', 'Due date', 'date', 11), C('paid_on', 'Paid on', 'date', 11),
    LST('status', 'Status', 'taxst', 11), CA('days_to_due', 'Days to due', 'int', 'IF({col:paid_on}<>"","",{col:due_date}-{today})', 9), PH('owner_phone', 1), PH('accountant_phone', 8)],
    D.tax_d(), 60, [A('status', '= ' + tok('taxst', 'Due'), 'warn'), A('status', '= ' + tok('taxst', 'Paid'), 'good')]))

# 10 Health check by month -----------------------------------------------------------------------------------------------------------------------------------------------------
def LKP(col): return 'IFERROR(INDEX({range:pnl.%s},MATCH({col:month},{range:pnl.month},0)),0)' % col
G, A_, R_ = lt('Green'), lt('Amber'), lt('Red')
def LIGHT3(x, g, a): return 'IF(%s,%s,IF(%s,%s,%s))' % (g, G, a, A_, R_)
tables.append(T('health', 'Health Check by Month', 'Practice health check against five targets',
    'One row per month: the months of expenses in cash and the booked share of the session cap; the pay share, overhead share and profit margin come from Profit by Month, and a traffic light for each target, the score and the verdict fill in by themselves.', [
    C('hc_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('months_cover', 'Months of expenses in cash', 'num', 11), C('booked_share', 'Booked share of cap', 'pct', 10),
    CA('pay_share', 'Pay share', 'pct', LKP('pay_share'), 9), CA('overhead_share', 'Overhead share', 'pct', LKP('overhead_share'), 10), CA('profit_margin', 'Profit margin', 'pct', LKP('margin'), 10),
    CA('light_pay', 'Pay light', 'text', LIGHT3('', '{col:pay_share}<={set:pay_share_target}+{set:target_tolerance}', '{col:pay_share}<={set:pay_share_target}+2*{set:target_tolerance}'), 9),
    CA('light_overhead', 'Overhead light', 'text', LIGHT3('', '{col:overhead_share}<={set:overhead_target}+{set:target_tolerance}', '{col:overhead_share}<={set:overhead_target}+2*{set:target_tolerance}'), 10),
    CA('light_margin', 'Margin light', 'text', LIGHT3('', '{col:profit_margin}>={set:profit_target}', '{col:profit_margin}>={set:profit_target}-{set:target_tolerance}'), 9),
    CA('light_cover', 'Cash light', 'text', LIGHT3('', '{col:months_cover}>={set:reserve_low_months}', '{col:months_cover}>={set:cover_min_months}'), 9),
    CA('light_booked', 'Booked share light', 'text', LIGHT3('', '{col:booked_share}>={set:target_utilisation}-{set:target_tolerance}', '{col:booked_share}>={set:target_utilisation}-2*{set:target_tolerance}'), 10),
    CA('score', 'Targets met (0 to 5)', 'int', '({col:light_pay}=%s)+({col:light_overhead}=%s)+({col:light_margin}=%s)+({col:light_cover}=%s)+({col:light_booked}=%s)' % ((G,) * 5), 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:score}>=4,%s,IF({col:score}=3,%s,%s))' % (vd('Healthy'), vd('Watch'), vd('Act now')), 10), PH('owner_phone', 1)],
    D.health_d(), 60, [A('verdict', '= ' + vd('Act now'), 'bad'), A('verdict', '= ' + vd('Watch'), 'warn'), A('verdict', '= ' + vd('Healthy'), 'good')]))
for c in tables[-1]['columns']:
    if c['key'].startswith('light_'): c['formula'] = c['formula'].replace('IF(,', 'IF(', 1) if False else c['formula']

# 11 Money owed at month end ------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('owed', 'Money Owed', 'Money owed to the practice at month end',
    'One row per month: what clients owe, what payers still owe on open claims and unpaid sublet invoices; the total and the days of revenue it represents fill in by themselves.', [
    C('mo_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('client_balances', 'Client balances', 'money', 14), C('open_claims', 'Open payer claims', 'money', 14), C('unpaid_sublets', 'Unpaid sublets', 'money', 13),
    CA('total', 'Total owed', 'money', '{col:client_balances}+{col:open_claims}+{col:unpaid_sublets}', 13),
    CA('days_of_revenue', 'Days of revenue owed', 'num', 'IFERROR({col:total}/(SUMIFS({range:pnl.revenue},{range:pnl.month},">="&DATE(YEAR({col:month}),MONTH({col:month})-3,1),{range:pnl.month},"<"&{col:month})/90),0)', 12), PH('owner_phone', 1)],
    D.owed_d(), 30, [A('days_of_revenue', '> 45', 'warn')]))

# 12 Bills due ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('bills', 'Bills Due', 'Bills due in the next 8 weeks',
    'One row per bill still to pay: due date, item, category and amount; the days to due and the total of the bills due in the next 7 days fill in by themselves.', [
    C('bill_id', 'Bill ID', 'text', 9, required=True), C('due_date', 'Due date', 'date', 11), C('item', 'Item', 'text', 30), LST('category', 'Category', 'ecat', 19), C('amount', 'Amount', 'money', 11),
    CA('days_to_due', 'Days to due', 'int', '{col:due_date}-{today}', 9),
    CA('next7_total', 'Bills due in the next 7 days', 'money', 'SUMIFS({range:bills.amount},{range:bills.due_date},">="&{today},{range:bills.due_date},"<="&{today}+7)', 14), PH('owner_phone', 1), PH('coordinator_phone', 7)],
    D.bills_d(), 60, [A('days_to_due', '<= 7', 'warn')]))

# 13 Service fixes -----------------------------------------------------------------------------------------------------------------------------------------------------------------
SV12 = '{range:svc_months.service},{col:service},{range:svc_months.month},">="&%s,{range:svc_months.month},"<"&%s' % (W0, MS)
def S12(c): return 'SUMIFS({range:svc_months.%s},%s)' % (c, SV12)
ARR12 = 'SUMIFS({range:svc_months.profit},{range:svc_months.service},{range:services.service},{range:svc_months.month},">="&%s,{range:svc_months.month},"<"&%s)' % (W0, MS)
LFEE = 'IFERROR(INDEX({range:services.fee},MATCH({col:service},{range:services.service},0)),0)'
tables.append(T('fixes', 'Service Fixes', 'Service fixes: profit per session after each change',
    'One row per option for a weak service: the change in fee, split, minutes and materials; the profit per session after the change, the fee that breaks even and the sessions a week needed fill in by themselves.', [
    C('fix_id', 'Fix ID', 'text', 9, required=True), LST('service', 'Service type', 'svcall', 19), LST('fixkind', 'Fix kind', 'fixkind', 17), C('option', 'Option', 'text', 30), LST('clinician', 'Clinician', 'clin', 16),
    C('fee_change', 'Fee change', 'money', 10), C('split_change', 'Split change', 'pct', 10), C('minutes_change', 'Minutes change', 'int', 10), C('materials_change', 'Materials change', 'money', 11),
    C('materials', 'Materials per session today', 'money', 11), C('fixed_month', 'Fixed cost a month', 'money', 11), C('decide_by', 'Decide by', 'date', 11),
    CA('sessions_12m', 'Sessions, last 12 months', 'int', S12('sessions'), 10), CA('service_profit', 'Profit, last 12 months', 'money', S12('profit'), 12),
    CA('avg_charge', 'Average charge per session', 'money', 'IFERROR(%s/{col:sessions_12m},0)' % S12('revenue'), 11), CA('pay_share', 'Clinician pay share', 'pct', 'IFERROR(%s/%s,0)' % (S12('clinician_pay'), S12('revenue')), 10),
    CA('base_ps', 'Profit per session today', 'money', 'IFERROR({col:service_profit}/{col:sessions_12m},0)', 11),
    CA('after', 'Profit per session after the change', 'money', '{col:base_ps}+{col:fee_change}*(1-{col:pay_share}-{col:split_change})-{col:split_change}*{col:avg_charge}-{set:room_cost_hour}*{col:minutes_change}/60-{col:materials_change}', 12),
    CA('be_fee', 'List fee that breaks even', 'money', 'IFERROR(({col:avg_charge}-({col:base_ps}-{col:split_change}*{col:avg_charge}-{set:room_cost_hour}*{col:minutes_change}/60-{col:materials_change})/(1-{col:pay_share}-{col:split_change}))*%s/{col:avg_charge},0)' % LFEE, 12),
    CA('be_sw', 'Sessions a week to break even', 'num', 'IFERROR(IF(({col:avg_charge}+{col:fee_change})*(1-{col:pay_share}-{col:split_change})-{col:materials}-{col:materials_change}<=0,0,ROUNDUP({col:fixed_month}/((({col:avg_charge}+{col:fee_change})*(1-{col:pay_share}-{col:split_change})-{col:materials}-{col:materials_change})*52/12),1)),0)', 12),
    CA('result', 'Result', 'text', 'IF({col:after}>=0,%s,%s)' % (vd('Above break-even'), vd('Below break-even')), 14),
    CA('is_weakest', 'Weakest service', 'int', 'IF(ROUND({col:service_profit},2)=ROUND(SUMPRODUCT(MIN(%s+({range:services.service}="")*1000000000)),2),1,0)' % ARR12, 9),
    CA('clinician_phone', 'Clinician phone', 'text', LKT('team.phone', 'team.name', 'clinician'), 18), PH('owner_phone', 1)],
    D.fixes_d(), 40, [A('result', '= ' + vd('Below break-even'), 'bad'), A('result', '= ' + vd('Above break-even'), 'good')]))

# 14 Hiring scenarios -----------------------------------------------------------------------------------------------------------------------------------------------------------------
SM_ = '({col:sessions_week}*52/12)'
U_ = '({col:avg_charge}-{col:session_pay}-{set:room_cost_hour}*50/60-{set:admin_cost})'
SAL_ = '({col:salary}*(1+{set:employer_cost_pct}))'
tables.append(T('hiring', 'Hiring Scenarios', 'Hiring scenarios: yearly profit and break-even month',
    'One row per way of adding a clinician: pay type, sessions a week, average charge, ramp-up months, pay and set-up cost; the profit at half volume, at full volume, the first-year profit and the month it breaks even fill in by themselves.', [
    C('hire_id', 'Scenario ID', 'text', 10, required=True), C('scenario', 'Scenario', 'text', 30), LST('pay_type', 'Pay type', 'hpay', 16), C('sessions_week', 'Sessions a week at full volume', 'int', 11), C('avg_charge', 'Average charge', 'money', 11),
    C('ramp_months', 'Ramp-up months', 'int', 10), C('salary', 'Monthly salary', 'money', 11), C('session_pay', 'Pay per session', 'money', 11), C('setup_cost', 'Set-up cost', 'money', 11), C('start_date', 'Planned start', 'date', 11),
    CA('ramp_profit', 'Profit a month at half volume', 'money', '0.5*%s*%s-%s' % (SM_, U_, SAL_), 13), CA('full_profit', 'Profit a month at full volume', 'money', '%s*%s-%s' % (SM_, U_, SAL_), 13),
    CA('yearly_profit', 'First-year profit', 'money', '{col:ramp_months}*{col:ramp_profit}+(12-{col:ramp_months})*{col:full_profit}-{col:setup_cost}', 13),
    CA('break_even_month', 'Break-even month', 'int', 'IF({col:full_profit}<=0,"",IF(AND({col:ramp_profit}>0,{col:setup_cost}<={col:ramp_months}*{col:ramp_profit}),ROUNDUP({col:setup_cost}/{col:ramp_profit},0),{col:ramp_months}+ROUNDUP(({col:setup_cost}-{col:ramp_months}*{col:ramp_profit})/{col:full_profit},0)))', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:break_even_month}="",%s,IF(AND({col:yearly_profit}>0,{col:break_even_month}<=9),%s,%s))' % (vd('Wait'), vd('Hire now'), vd('Wait')), 10),
    PH('owner_phone', 1), PH('it_phone', 10)], D.hiring_d(), 30, [A('verdict', '= ' + vd('Hire now'), 'good'), A('verdict', '= ' + vd('Wait'), 'warn')]))

# 15 Room options -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
AVGCH = '(SUMIFS({range:svc_months.revenue},{range:svc_months.month},">="&%s,{range:svc_months.month},"<"&%s)/SUMIFS({range:svc_months.sessions},{range:svc_months.month},">="&%s,{range:svc_months.month},"<"&%s))' % (W0, MS, W0, MS)
PAYSH = '(SUMIFS({range:svc_months.clinician_pay},{range:svc_months.month},">="&%s,{range:svc_months.month},"<"&%s)/SUMIFS({range:svc_months.revenue},{range:svc_months.month},">="&%s,{range:svc_months.month},"<"&%s))' % (W0, MS, W0, MS)
CONTR = '({col:expected_sessions}*52/12*(%s*(1-%s)-{set:admin_cost})+{col:sublet_hours}*52/12*{col:sublet_rate}-{col:extra_rent})' % (AVGCH, PAYSH)
tables.append(T('rooms_opt', 'Room Options', 'Room options: yearly profit and payback',
    'One row per way of adding room or capacity: extra rent, room hours, expected sessions, sublet hours and set-up cost; the monthly profit, the first-year profit, the payback months and the use share fill in by themselves.', [
    C('opt_id', 'Option ID', 'text', 10, required=True), C('option', 'Option', 'text', 30), LST('kind', 'Option kind', 'roomopt', 19), C('extra_rent', 'Extra rent a month', 'money', 11), C('room_hours', 'Room hours a week', 'int', 10),
    C('expected_sessions', 'Expected sessions a week', 'int', 11), C('sublet_hours', 'Sublet hours a week', 'int', 10), C('sublet_rate', 'Sublet rate an hour', 'money', 10), C('setup_cost', 'Set-up cost', 'money', 11),
    C('start_date', 'Planned start', 'date', 11), CA('contribution_month', 'Profit a month', 'money', CONTR, 12),
    CA('yearly_profit', 'First-year profit', 'money', '12*{col:contribution_month}-{col:setup_cost}', 12),
    CA('payback_months', 'Payback months', 'int', 'IF({col:contribution_month}<=0,"",ROUNDUP({col:setup_cost}/{col:contribution_month},0))', 10),
    CA('use_share', 'Use share of room hours', 'pct', 'IFERROR(({col:expected_sessions}*50/60+{col:sublet_hours})/{col:room_hours},0)', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:payback_months}="",%s,IF(AND({col:yearly_profit}>0,{col:payback_months}<=18),%s,%s))' % (vd('Wait'), vd('Add the room'), vd('Wait')), 12),
    PH('landlord_phone', 11), PH('cleaner_phone', 12), PH('owner_phone', 1)], D.rooms_opt_d(), 30, [A('verdict', '= ' + vd('Add the room'), 'good'), A('verdict', '= ' + vd('Wait'), 'warn')]))

# 16 Set-up and equipment costs ------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('setup_costs', 'Set-up Costs', 'Set-up and equipment costs',
    'One row per piece of equipment or fit-out: date, cost and years of use; the monthly cost fills in by itself.', [
    C('item_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 30), C('date', 'Date', 'date', 11), C('cost', 'Cost', 'money', 11), C('years_of_use', 'Years of use', 'int', 10),
    CA('monthly_cost', 'Monthly cost', 'money', '{col:cost}/({col:years_of_use}*12)', 11), PH('accountant_phone', 8)], D.setup_d(), 40, []))

# 17 Next 12 months budget -----------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('forecast12', 'Next 12 Months Budget', 'Next 12 months budget',
    'One row per coming month: sessions, average charge, pay, rent and other costs; revenue, profit and margin fill in by themselves.', [
    C('bd_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('sessions', 'Sessions', 'int', 9), C('avg_charge', 'Average charge', 'money', 11), C('pay', 'Pay', 'money', 11),
    C('rent', 'Rent', 'money', 11), C('other_costs', 'Other costs', 'money', 11), CA('revenue', 'Revenue', 'money', '{col:sessions}*{col:avg_charge}', 12),
    CA('profit', 'Profit', 'money', '{col:revenue}-{col:pay}-{col:rent}-{col:other_costs}', 12), CA('margin', 'Margin', 'pct', 'IFERROR({col:profit}/{col:revenue},0)', 10), PH('owner_phone', 1)],
    D.forecast12_d(), 30, [A('margin', '< {set:profit_target}', 'warn')]))

# 18 Growth milestones -------------------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('milestones', 'Growth Milestones', 'Growth milestones with target dates',
    'One row per growth milestone: target date, measure, owner and status; the days left and the due check fill in by themselves.', [
    C('ms_id', 'Milestone ID', 'text', 10, required=True), C('milestone', 'Milestone', 'text', 30), C('target_date', 'Target date', 'date', 11), C('measure', 'Measure', 'text', 30), REF('owner', 'Owner', 'team.name', 20),
    LST('status', 'Status', 'mstat', 12), CA('days_left', 'Days left', 'int', 'IF({col:status}=%s,"",{col:target_date}-{today})' % tok('mstat', 'Done'), 9),
    CA('due_flag', 'Due check', 'text', 'IF({col:status}=%s,%s,IF({col:target_date}<{today},%s,IF({col:target_date}-{today}<=30,%s,%s)))' % (tok('mstat', 'Done'), vd('Done'), vd('Overdue'), vd('Due soon'), vd('On track')), 11),
    PH('owner_phone', 1)], D.milestones_d(), 40, [A('due_flag', '= ' + vd('Overdue'), 'bad'), A('due_flag', '= ' + vd('Due soon'), 'warn'), A('due_flag', '= ' + vd('Done'), 'good')]))

# 19 Services and 20 Team -----------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('services', 'Services', 'Services and list fees',
    'One row per service type: minutes and this year\'s list fee before tax.', [LST('service', 'Service type', 'svcall', 20, required=True), C('minutes', 'Minutes', 'int', 10), C('fee', 'List fee', 'money', 11)],
    D.services_d(), 20, []))
tables.append(T('team', 'Team', 'Team and outside contacts',
    'One row per team member or outside contact: role, pay type and pay, weekly hours, session cap and target; phones are used by the ready messages.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 24), LST('team', 'Team', 'team', 13), LST('pay_type', 'Pay type', 'paytype', 16), C('phone', 'Phone', 'text', 18),
    C('email', 'Email', 'text', 26), C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'money', 12), C('split_pct', 'Split share', 'pct', 9), C('session_rate', 'Pay per session', 'money', 11),
    C('hourly_rate', 'Hourly rate', 'money', 10), C('session_cap', 'Session cap a week', 'int', 10), C('session_target', 'Session target a week', 'int', 10), C('speciality', 'Speciality', 'text', 30),
    C('country', 'Country', 'text', 14), C('start', 'Start date', 'date', 11)], D.team_d(), 30, []))
assert len(tables) == 20, len(tables)

# a LIGHT3 used '' as a placeholder: repair the formulas (IF(<cond>,Green,IF(<cond>,Amber,Red)))
for c in tables[9]['columns']:
    if c['key'].startswith('light_'): c['formula'] = c['formula']
