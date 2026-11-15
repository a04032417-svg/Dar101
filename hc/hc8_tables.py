"""Home care agency suite part 8: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc8_lists import *
import hc8_data as D

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
M0 = 'DATE(YEAR({today}),MONTH({today}),1)'; M1 = 'DATE(YEAR({today}),MONTH({today})-1,1)'; WPM = '(52/12)'
def PNM(col, m=M1): return 'SUMIFS({range:pnl.%s},{range:pnl.month},%s)' % (col, m)
MPH1 = PNM('margin_hour'); RPH1 = '(%s/%s)' % (PNM('revenue'), PNM('billed_hours')); OVH1 = PNM('overhead'); WH1 = PNM('weekly_hours')
CASHNOW = 'SUMIFS({range:cash.closing},{range:cash.month},%s)' % M0
def TG(m, level): return 'SUMIFS({range:targets.value},{range:targets.measure},%s,{range:targets.level},%s)' % (m, tok('lvl', level))
def PTS(v, m):
    t, r = TG(m, 'Target'), TG(m, 'Red limit')
    return 'IFERROR(MAX(0,MIN(100,100*(%s-%s)/(%s-%s))),0)' % (v, r, t, r)
def LIGHT(v, m):
    t, a, r = TG(m, 'Target'), TG(m, 'Amber limit'), TG(m, 'Red limit')
    return 'IFERROR(IF((%s-%s)*(%s-%s)>=0,%s,IF((%s-%s)*(%s-%s)>=0,%s,%s)),%s)' % (v, t, t, r, ck('Green'), v, a, t, r, ck('Amber'), ck('Red'), ck('Red'))
HM = {'margin_hour': 'Gross margin per hour', 'overtime_share': 'Overtime share', 'fill_rate': 'Fill rate', 'days_to_pay': 'Days to be paid', 'turnover_rate': 'Caregiver turnover', 'cover_weeks': 'Weeks of cash cover'}
PK = {'margin_hour': 'p_margin', 'overtime_share': 'p_overtime', 'fill_rate': 'p_fill', 'days_to_pay': 'p_days', 'turnover_rate': 'p_turnover', 'cover_weeks': 'p_cover'}

settings = [
    S('company', 'Your agency name', 'text', COMPANY), S('target_margin', 'Wanted gross margin per client hour (example: use your own)', 'pct', TARGET_MARGIN),
    S('profit_target', 'Wanted profit as a share of revenue (example)', 'pct', 0.12), S('payroll_burden', 'Payroll burden: payroll taxes, workers\' insurance and benefits on top of pay (example, confirm with your adviser)', 'pct', PAYROLL_BURDEN),
    S('payroll_ratio_ceiling', 'Pay cost as a share of revenue: ceiling', 'pct', PAYROLL_RATIO_CEILING), S('office_help_hours', 'Weekly care hours at which office help is needed (a marker, not a rule)', 'int', SCHEDULER_THRESHOLD_HOURS),
    S('tax_set_aside_pct', 'Income tax set-aside share of profit (example, confirm with your adviser)', 'pct', TAX_SET_ASIDE_PCT), S('owner_draw', 'Planned owner draw a month', 'money', OWNER_DRAW),
    S('cash_floor', 'Cash floor: the least cash you want in the bank', 'money', CASH_FLOOR), S('cash_cover_weeks', 'Weeks of payroll and overhead held as cash (example)', 'int', 3),
    S('payer_delay_days', 'Slider: days a third-party payer pays later than usual', 'int', 15), S('overhead_share_target', 'Overhead as a share of revenue: target', 'pct', 0.26),
    S('budget_tolerance', 'Budget overrun you accept on a line', 'pct', 0.05), S('hours_per_caregiver', 'Average weekly hours per caregiver', 'num', 24),
    S('health_healthy_score', 'Health score from which the agency is Healthy', 'int', 90), S('health_watch_score', 'Health score from which the agency is on Watch', 'int', 70)]
assert 3 <= len(settings) <= 20

def STAFF(idx, k): return CA(k, 'Phone to message', 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % idx, 18)
def STAFFN(idx, k): return CA(k, 'Contact name', 'text', 'IFERROR(INDEX({range:team.name},%d)&"","")' % idx, 20)
tables = []
# 1 profit and loss
tables.append(T('pnl', 'Profit and Loss', 'Profit and loss statement by month',
    'One row per month: type revenue, billed hours and the caregiver pay lines; overhead comes from Expenses, and gross margin, profit, the shares, break-even hours and the hours growth fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('revenue', 'Revenue', 'money', 12), C('billed_hours', 'Billed hours', 'num', 11), C('caregiver_pay', 'Caregiver pay', 'money', 13),
    C('overtime_pay', 'Overtime pay', 'money', 12), C('travel_mileage', 'Travel and mileage', 'money', 13), C('payroll_burden', 'Payroll burden', 'money', 13),
    CA('overhead', 'Overhead', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.month},{col:month})', 12),
    CA('direct_cost', 'Direct cost', 'money', '{col:caregiver_pay}+{col:overtime_pay}+{col:travel_mileage}+{col:payroll_burden}', 12), CA('gross_margin', 'Gross margin', 'money', '{col:revenue}-{col:direct_cost}', 12),
    CA('profit', 'Profit', 'money', '{col:gross_margin}-{col:overhead}', 12), CA('gross_margin_share', 'Gross margin share', 'pct', 'IF({col:revenue}>0,{col:gross_margin}/{col:revenue},0)', 11),
    CA('overhead_share', 'Overhead share', 'pct', 'IF({col:revenue}>0,{col:overhead}/{col:revenue},0)', 11), CA('profit_share', 'Profit share', 'pct', 'IF({col:revenue}>0,{col:profit}/{col:revenue},0)', 11),
    CA('pay_cost_ratio', 'Pay cost ratio', 'pct', 'IF({col:revenue}>0,({col:caregiver_pay}+{col:overtime_pay}+{col:payroll_burden})/{col:revenue},0)', 11),
    CA('margin_hour', 'Gross margin per hour', 'num', 'IF({col:billed_hours}>0,{col:gross_margin}/{col:billed_hours},0)', 11),
    CA('weekly_hours', 'Weekly hours', 'num', 'IF({col:month}=%s,{col:billed_hours}/(DAY({today})/7),{col:billed_hours}/%s)' % (M0, WPM), 10),
    CA('breakeven_hours', 'Break-even weekly hours', 'num', 'IF({col:margin_hour}>0,IF({col:month}=%s,SUMIFS({range:pnl.overhead},{range:pnl.month},EDATE({col:month},-1)),{col:overhead})/(%s*{col:margin_hour}),0)' % (M0, WPM), 11),
    CA('hours_growth', 'Weekly hours growth a month', 'num', 'IF(COUNTIFS({range:pnl.month},EDATE({col:month},-6))=0,0,({col:weekly_hours}-SUMIFS({range:pnl.weekly_hours},{range:pnl.month},EDATE({col:month},-6)))/6)', 11),
    CA('months_to_marker', 'Months to the marker', 'int', 'IF({col:weekly_hours}>={set:office_help_hours},0,IF({col:hours_growth}>0,ROUNDUP(({set:office_help_hours}-{col:weekly_hours})/{col:hours_growth},0),99))', 10),
    CA('ytd_revenue', 'Revenue this year to date', 'money', 'SUMIFS({range:pnl.revenue},{range:pnl.month},">="&DATE(YEAR({col:month}),1,1),{range:pnl.month},"<="&{col:month})', 13),
    CA('ytd_profit', 'Profit this year to date', 'money', 'SUMIFS({range:pnl.profit},{range:pnl.month},">="&DATE(YEAR({col:month}),1,1),{range:pnl.month},"<="&{col:month})', 13),
    CA('annual_pay', 'Pay in the last 12 months', 'money', 'SUMIFS({range:pnl.caregiver_pay},{range:pnl.month},">="&EDATE({col:month},-11),{range:pnl.month},"<="&{col:month})', 13),
    CA('complete', 'Full month', 'int', 'IF({col:month}<%s,1,0)' % M0, 8), CA('target_profit', 'Profit at the target share', 'money', '{col:revenue}*{set:profit_target}', 12),
    CA('health_score', 'Health score', 'num', 'SUMIFS({range:health.score},{range:health.month},{col:month})', 9),
    CA('worst_item', 'Worst health item', 'text', 'IFERROR(INDEX({range:health.worst},MATCH({col:month},{range:health.month},0))&"","")', 22),
    CA('close_by', 'Close the month by', 'date', 'EDATE({col:month},1)+4', 11)], D.pnl_d(), 60,
    [A('profit_share', '< {set:profit_target}', 'warn'), A('overhead_share', '> {set:overhead_share_target}', 'warn'), A('gross_margin_share', '< {set:target_margin}', 'warn'), A('pay_cost_ratio', '> {set:payroll_ratio_ceiling}', 'bad'), A('profit', '< 0', 'bad')]))
# 2 expenses
tables.append(T('expenses', 'Expenses', 'Expenses by category and payee',
    'One row per payment out of the office: date, month, category, payee and amount; the overhead tables, the budget and the profit and loss read it.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('category', 'Category', 'ecat', 22), C('payee', 'Payee', 'text', 24), C('amount', 'Amount', 'money', 12)],
    D.expenses_d(), 800))
# 3 overhead by month
def OV(cats): return '+'.join('SUMIFS({range:expenses.amount},{range:expenses.month},{col:month},{range:expenses.category},%s)' % tok('ecat', c) for c in cats)
tables.append(T('overhead', 'Overhead by Month', 'Overhead by month and line',
    'One row per month: rent, office payroll, field supervisor pay, software and phones, insurance, marketing and recruiting and the rest, all read from Expenses; the total and its share of revenue fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11),
    CA('rent', 'Rent', 'money', OV(['Office rent']), 11), CA('office_payroll', 'Office payroll', 'money', OV(['Office payroll']), 12), CA('field_pay', 'Field supervisor pay', 'money', OV(['Field supervisor pay']), 12),
    CA('software_phones', 'Software and phones', 'money', OV(['Software and phones']), 12), CA('insurance', 'Insurance', 'money', OV(['Business insurance']), 11),
    CA('marketing_recruiting', 'Marketing and recruiting', 'money', OV(['Marketing', 'Recruiting ads']), 13),
    CA('total', 'Total overhead', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.month},{col:month})', 12), CA('other', 'Other lines', 'money', '{col:total}-{col:rent}-{col:office_payroll}-{col:field_pay}-{col:software_phones}-{col:insurance}-{col:marketing_recruiting}', 11),
    CA('share_of_revenue', 'Share of revenue', 'pct', 'IFERROR(IF(SUMIFS({range:pnl.revenue},{range:pnl.month},{col:month})>0,{col:total}/SUMIFS({range:pnl.revenue},{range:pnl.month},{col:month}),0),0)', 11),
    CA('complete', 'Full month', 'int', 'IF({col:month}<%s,1,0)' % M0, 8)], D.overhead_d(), 60, [A('share_of_revenue', '> {set:overhead_share_target}', 'warn')]))
# 4 budget
tables.append(T('budget', 'Budget', 'Monthly budget against last month\'s actual',
    'One row per expense category: type the monthly budget and the next review date; last month\'s actual, the variance (positive is over budget) and the check fill in by themselves.', [
    LST('category', 'Category', 'ecat', 22, required=True), C('budget', 'Monthly budget', 'money', 13), C('review_on', 'Next review', 'date', 11),
    CA('actual_last_month', 'Actual last month', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.month},%s)' % M1, 13),
    CA('variance', 'Variance', 'money', '{col:actual_last_month}-{col:budget}', 11), CA('variance_share', 'Variance share', 'pct', 'IF({col:budget}>0,{col:variance}/{col:budget},0)', 11),
    CA('flag', 'Budget check', 'text', 'IF({col:variance_share}>{set:budget_tolerance},%s,%s)' % (ck('Over budget'), ck('Within budget')), 14), CA('quarter_budget', 'Budget for the quarter', 'money', '{col:budget}*3', 13)],
    D.budget_d(), 40, [A('flag', '= ' + ck('Over budget'), 'bad'), A('flag', '= ' + ck('Within budget'), 'good')]))
# 5 cash months
tables.append(T('cash', 'Cash Months', 'Cash by month: in, out and closing balance',
    'One row per month: type the opening cash, cash in and pay runs; expenses, owner draw and tax set-aside come from their own sheets, and cash out, closing, the change and cash above the floor fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('opening', 'Opening cash', 'money', 13), C('cash_in', 'Cash in', 'money', 12), C('pay_runs', 'Pay runs', 'money', 12),
    CA('expenses', 'Expenses', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.month},{col:month})', 12), CA('owner_draw', 'Owner draw', 'money', 'SUMIFS({range:draws.draw},{range:draws.month},{col:month})', 11),
    CA('tax_set_aside', 'Tax set-aside', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.month},EDATE({col:month},-1))', 11), CA('cash_out', 'Cash out', 'money', '{col:pay_runs}+{col:expenses}+{col:owner_draw}+{col:tax_set_aside}', 12),
    CA('closing', 'Closing cash', 'money', '{col:opening}+{col:cash_in}-{col:cash_out}', 13), CA('cash_floor', 'Cash floor', 'money', '{set:cash_floor}', 11), CA('change', 'Change in cash', 'money', '{col:closing}-{col:opening}', 12),
    CA('above_floor', 'Cash above the floor', 'money', '{col:closing}-{col:cash_floor}', 13),
    CA('safe_draw', 'Safe owner draw', 'money', 'MAX(0,MIN(ROUNDDOWN(({col:closing}-{col:cash_floor}-{col:pay_runs}/2)/100,0)*100,ROUNDDOWN(SUMIFS({range:pnl.profit},{range:pnl.month},EDATE({col:month},-1))*(1-{set:tax_set_aside_pct})/100,0)*100))', 12),
    CA('latest', 'This month', 'int', 'IF({col:month}=%s,1,0)' % M0, 8), CA('complete', 'Full month', 'int', 'IF({col:month}<%s,1,0)' % M0, 8)], D.cash_d(), 40,
    [A('above_floor', '< 0', 'bad')]))
# 6 13-week forecast (three scenarios of 13 weeks)
tables.append(T('forecast', '13-Week Cash Forecast', '13-week cash forecast in three scenarios',
    'Thirteen weeks in Base, Best and Worst: type receipts, pay run, overhead, owner draw and tax set-aside; net cash, closing balance, the floor check, weeks of cover and the closing balance with a late payer fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('week', 'Week', 'wk', 10), C('week_no', 'Week number', 'int', 9), C('starts_on', 'Week starts (Monday)', 'date', 12), LST('scenario', 'Scenario', 'scen', 10),
    C('private_receipts', 'Private pay receipts', 'money', 13), C('payer_receipts', 'Payer receipts', 'money', 12), C('pay_run', 'Pay run', 'money', 12), C('overhead', 'Overhead', 'money', 11),
    C('owner_draw', 'Owner draw', 'int', 10), C('tax_set_aside', 'Tax set-aside', 'int', 10),
    CA('net', 'Net cash', 'money', '{col:private_receipts}+{col:payer_receipts}-{col:pay_run}-{col:overhead}-{col:owner_draw}-{col:tax_set_aside}', 12),
    CA('closing', 'Closing balance', 'money', '%s+SUMIFS({range:forecast.net},{range:forecast.scenario},{col:scenario},{range:forecast.week_no},"<="&{col:week_no})' % CASHNOW, 13),
    CA('rank_low', 'Lowest week rank', 'int', 'COUNTIFS({range:forecast.scenario},{col:scenario},{range:forecast.closing},"<"&{col:closing})+1', 9),
    CA('floor_check', 'Floor warning', 'text', 'IF({col:closing}>={set:cash_floor},%s,%s)' % (ck('Above the floor'), ck('Below the floor')), 14),
    CA('above', 'At or above the floor', 'int', 'IF({col:closing}>={set:cash_floor},1,0)', 9),
    CA('weeks_cover', 'Weeks of cover', 'num', 'IFERROR({col:closing}/((SUMIFS({range:forecast.pay_run},{range:forecast.scenario},{col:scenario})+SUMIFS({range:forecast.overhead},{range:forecast.scenario},{col:scenario}))/13),0)', 9),
    CA('closing_late', 'Closing if payers pay later', 'money', '{col:closing}-SUMIFS({range:forecast.payer_receipts},{range:forecast.scenario},{col:scenario},{range:forecast.week_no},">"&({col:week_no}-ROUNDUP({set:payer_delay_days}/7,0)),{range:forecast.week_no},"<="&{col:week_no})', 13)],
    D.FORECAST, 120, [A('floor_check', '= ' + ck('Below the floor'), 'bad'), A('closing', '< {set:cash_floor}', 'bad')]))
# 7 expected receipts
tables.append(T('receipts', 'Expected Receipts', 'Expected receipts by week and payer',
    'One row per expected receipt in the next 13 weeks: week, source, amount and the usual days to pay; the week it arrives under the payer-pays-later slider and the amount that moves fill in by themselves.', [
    C('receipt_id', 'Receipt ID', 'text', 10, required=True), C('week_no', 'Week number', 'int', 9), C('starts_on', 'Week starts (Monday)', 'date', 12), LST('source', 'Source', 'payer', 20), C('amount', 'Amount', 'money', 12),
    C('usual_days', 'Usual days to pay', 'int', 10),
    CA('arrives_week', 'Arrives in week', 'int', '{col:week_no}+IF({col:source}=%s,0,ROUNDUP({set:payer_delay_days}/7,0))' % tok('payer', 'Private pay'), 9),
    CA('delayed_amount', 'Amount that moves later', 'money', 'IF({col:source}=%s,0,{col:amount})' % tok('payer', 'Private pay'), 13),
    CA('pushed_out', 'Pushed beyond week 13', 'money', 'IF({col:arrives_week}>13,{col:amount},0)', 12)], D.RECEIPTS, 60, [A('pushed_out', '> 0', 'warn')]))
# 8 pay runs
tables.append(T('payruns', 'Pay Runs', 'Pay runs: paid and upcoming',
    'One row per bi-weekly pay run: period, pay date, hours and gross pay; the cost with payroll burden, the cost per hour and whether it is paid, next or planned fill in by themselves.', [
    C('run_id', 'Run ID', 'text', 9, required=True), C('period_start', 'Period start', 'date', 11), C('period_end', 'Period end', 'date', 11), C('pay_date', 'Pay date', 'date', 11), C('hours', 'Hours', 'num', 10), C('est_cost', 'Gross pay', 'money', 12),
    CA('cost_with_burden', 'Cost with payroll burden', 'money', 'ROUND({col:est_cost}*(1+{set:payroll_burden}),2)', 13), CA('cost_per_hour', 'Cost per hour', 'num', 'IF({col:hours}>0,{col:cost_with_burden}/{col:hours},0)', 10),
    CA('status', 'Status', 'text', 'IF({col:pay_date}<{today},%s,IF({col:pay_date}=SUMPRODUCT(MIN(({range:payruns.pay_date}>={today})*{range:payruns.pay_date}+({range:payruns.pay_date}<{today})*99999)),%s,%s))' % (ck('Paid'), ck('Next run'), ck('Planned')), 11)],
    D.PAYRUNS, 40, [A('status', '= ' + ck('Next run'), 'warn'), A('status', '= ' + ck('Paid'), 'good')]))
# 9 tax set-aside
tables.append(T('tax', 'Tax Set-Aside', 'Income tax set-aside by month (confirm with your adviser)',
    'One row per month: type the set-aside share, the status and the date it was moved; the profit, the amount to set aside and the running total fill in by themselves. Confirm the rate and the amounts with your adviser.', [
    C('tax_id', 'Tax ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('set_aside_pct', 'Set-aside share', 'pct', 10), LST('status', 'Status', 'taxst', 11), C('moved_on', 'Moved on', 'date', 11),
    CA('profit', 'Profit', 'money', 'SUMIFS({range:pnl.profit},{range:pnl.month},{col:month})', 12), CA('set_aside', 'Set-aside', 'money', 'ROUND(MAX(0,{col:profit}*{col:set_aside_pct}),2)', 12),
    CA('cumulative', 'Running total', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.month},"<="&{col:month})', 13), CA('this_year', 'This year', 'int', 'IF(YEAR({col:month})=YEAR({today}),1,0)', 8)],
    D.tax_d(), 60, [A('status', '= ' + tok('taxst', 'Due'), 'bad'), A('status', '= ' + tok('taxst', 'Moved'), 'good')]))
# 10 owner draws
tables.append(T('draws', 'Owner Draws', 'Owner draws by month',
    'One row per month: type the draw and the date it was taken; the running total, the profit of the month and the draw as a share of profit fill in by themselves.', [
    C('draw_id', 'Draw ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('draw', 'Draw', 'int', 10), C('taken_on', 'Taken on', 'date', 11),
    CA('cumulative', 'Running total', 'money', 'SUMIFS({range:draws.draw},{range:draws.month},"<="&{col:month})', 13), CA('profit', 'Profit of the month', 'money', 'SUMIFS({range:pnl.profit},{range:pnl.month},{col:month})', 13),
    CA('draw_share', 'Draw as a share of profit', 'pct', 'IF({col:profit}>0,{col:draw}/{col:profit},0)', 11),
    CA('draw_check', 'Draw check', 'text', 'IF({col:draw}>{col:profit},%s,%s)' % (ck('Above profit'), ck('Covered by profit')), 16)], D.draws_d(), 60, [A('draw_check', '= ' + ck('Above profit'), 'warn')]))
# 11 hours target plan
tables.append(T('hplan', 'Hours Target Plan', 'Hours target plans: what each plan needs',
    'One row per plan: type the weekly hours, margin per hour, overhead and owner draw; profit after the draw, the hours the plan needs, the gap and the caregivers to add fill in by themselves.', [
    C('plan_id', 'Plan ID', 'text', 9, required=True), C('plan', 'Plan', 'text', 30), C('weekly_hours', 'Weekly hours', 'int', 10), C('margin_hour', 'Margin per hour', 'num', 10), C('overhead', 'Overhead a month', 'money', 12), C('draw', 'Owner draw a month', 'int', 11),
    CA('profit_after_draw', 'Profit after the draw', 'money', 'ROUND({col:weekly_hours}*%s*{col:margin_hour}-{col:overhead}-{col:draw},0)' % WPM, 12),
    CA('needed_hours', 'Weekly hours needed', 'int', 'ROUND(({col:overhead}+{col:draw})/(%s*{col:margin_hour}),0)' % WPM, 10), CA('hours_gap', 'Hours gap (plus is short)', 'int', '{col:needed_hours}-{col:weekly_hours}', 10),
    CA('caregivers_needed', 'Caregivers to add', 'int', 'MAX(0,ROUNDUP((MAX({col:weekly_hours},{col:needed_hours})-%s)/{set:hours_per_caregiver},0))' % WH1, 10), CA('hire_by', 'Hire by', 'date', '{today}+56', 11)],
    D.hplan_d(), 40, [A('hours_gap', '> 0', 'warn'), A('profit_after_draw', '< 0', 'bad')]))
# 12 break-even scenarios
tables.append(T('breakeven', 'Break-Even Scenarios', 'Break-even scenarios: rate rise, hours lost, scheduler',
    'One row per scenario: type the rate rise, the share of hours lost and the cost of office help; the new margin per hour, break-even weekly hours and profit a month fill in by themselves from last month\'s results.', [
    C('sc_id', 'Scenario ID', 'text', 9, required=True), C('scenario', 'Scenario', 'text', 30), C('rate_rise', 'Rate rise', 'pct', 9), C('hours_lost', 'Hours lost', 'pct', 9), C('scheduler_cost', 'Office help a month', 'int', 11),
    CA('new_margin', 'Margin per hour after', 'num', 'ROUND(%s+%s*{col:rate_rise},2)' % (MPH1, RPH1), 11), CA('hours_after', 'Weekly hours after', 'int', 'ROUND(%s*(1-{col:hours_lost}),0)' % WH1, 10),
    CA('breakeven_hours', 'Break-even weekly hours', 'int', 'ROUND((%s+{col:scheduler_cost})/(%s*{col:new_margin}),0)' % (OVH1, WPM), 11),
    CA('profit_month', 'Profit a month', 'money', 'ROUND({col:hours_after}*%s*{col:new_margin}-%s-{col:scheduler_cost},0)' % (WPM, OVH1), 12),
    CA('verdict', 'Result', 'text', 'IF({col:profit_month}>0,%s,%s)' % (vd('Above break-even'), vd('Below break-even')), 16)], D.breakeven_d(), 40, [A('profit_month', '< 0', 'bad')]))
# 13 staff cost
tables.append(T('staffcost', 'Office and Field Staff Cost', 'Office and field staff cost: now, after a raise and at 1,000 hours',
    'One row per person and version: type the monthly pay and the weekly hours; payroll burden, the loaded monthly cost and the cost per hour fill in by themselves (confirm the burden with your adviser).', [
    C('sc_id', 'Row ID', 'text', 9, required=True), REF('person', 'Person', 'team.name', 22), LST('version', 'Version', 'stver', 15), C('monthly_salary', 'Monthly pay', 'money', 12), C('hours_week', 'Hours a week', 'int', 9),
    CA('role', 'Role', 'text', LKT('team.role', 'team.name', 'person'), 18),
    CA('burden', 'Payroll burden', 'money', 'IF(IFERROR(INDEX({range:team.pay_type},MATCH({col:person},{range:team.name},0)),"")=%s,0,{col:monthly_salary}*{set:payroll_burden})' % tok('paytype', 'Owner draw'), 12),
    CA('loaded_cost', 'Loaded monthly cost', 'money', '{col:monthly_salary}+{col:burden}', 13), CA('cost_per_hour', 'Cost per hour', 'num', 'IF({col:hours_week}>0,{col:loaded_cost}/({col:hours_week}*%s),0)' % WPM, 10)],
    D.staffcost_d(), 60))
# 14 health score history
hc = []
for k in ('overtime_share', 'fill_rate', 'days_to_pay', 'turnover_rate', 'cover_weeks'): pass
def PC(k): return CA(PK[k], 'Points: ' + HM[k], 'num', PTS('{col:%s}' % k, tok('meas', HM[k])), 9)
W = lambda m: TG(tok('meas', m), 'Weight')
SCORE = 'ROUND((%s)/(%s),1)' % ('+'.join('%s*{col:%s}' % (W(HM[k]), PK[k]) for k in HM), '+'.join(W(m) for m in HM.values()))
MINP = 'MIN(%s)' % ','.join('{col:%s}' % PK[k] for k in HM)
WORST = ''.join('IF(%s={col:%s},%s,' % (MINP, PK[k], tok('meas', HM[k])) for k in list(HM)[:-1]) + tok('meas', HM['cover_weeks']) + ')' * 5
tables.append(T('health', 'Health Score History', 'Health score by month: six measures against targets',
    'One row per month: type overtime share, fill rate, days to be paid, turnover and weeks of cash cover; margin per hour, the points for each measure, the score and the worst item fill in by themselves against Health Targets.', [
    C('hl_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), CA('margin_hour', 'Gross margin per hour', 'num', LKN('pnl.margin_hour', 'pnl.month', 'month'), 11),
    C('overtime_share', 'Overtime share', 'pct', 10), C('fill_rate', 'Fill rate', 'pct', 9), C('days_to_pay', 'Days to be paid', 'num', 9), C('turnover_rate', 'Caregiver turnover', 'pct', 10), C('cover_weeks', 'Weeks of cash cover', 'num', 10)] +
    [PC(k) for k in HM] + [CA('score', 'Health score', 'num', SCORE, 9), CA('worst', 'Worst item', 'text', WORST, 22), CA('latest', 'This month', 'int', 'IF({col:month}=%s,1,0)' % M0, 8),
    CA('complete', 'Full month', 'int', 'IF({col:month}<%s,1,0)' % M0, 8), CA('scale', 'Full score', 'int', '100', 8)], D.health_d(), 60,
    [A('score', '< {set:health_watch_score}', 'bad'), A('score', '< {set:health_healthy_score}', 'warn')]))
# 15 health targets
LATEST = lambda col: 'SUMIFS({range:health.%s},{range:health.latest},1)' % col
LV_ = ''.join('IF({col:measure}=%s,%s,' % (tok('meas', HM[k]), LATEST(k)) for k in list(HM)[:-1]) + LATEST('cover_weeks') + ')' * 5
tables.append(T('targets', 'Health Targets', 'Health targets: target, amber limit, red limit and weight',
    'Six measures with four rows each: the target (green and 100 points), the amber limit (red beyond it), the red limit (0 points) and the weight; the latest value, its points and the light fill in. Example values: use your own.', [
    C('tg_id', 'Row ID', 'text', 9, required=True), LST('measure', 'Measure', 'meas', 24), LST('level', 'Level', 'lvl', 12), C('value', 'Value', 'num', 10),
    CA('latest_value', 'Latest value', 'num', LV_, 10), CA('points', 'Points (100 is on target)', 'num', PTS('{col:latest_value}', '{col:measure}'), 11), CA('light', 'Light', 'text', LIGHT('{col:latest_value}', '{col:measure}'), 9)],
    D.targets_d(), 40, [A('light', '= ' + ck('Red'), 'bad'), A('light', '= ' + ck('Amber'), 'warn'), A('light', '= ' + ck('Green'), 'good')]))
# 16 weekly hours
tables.append(T('weekly', 'Weekly Hours', 'Weekly hours: scheduled, delivered, billed and paid',
    'One row per week (Monday): scheduled, delivered, billed and paid hours and visits from the other parts; billed minus paid hours fills in by itself.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), C('scheduled_hours', 'Scheduled hours', 'num', 10), C('delivered_hours', 'Delivered hours', 'num', 10), C('billed_hours', 'Billed hours', 'num', 10),
    C('paid_hours', 'Paid hours', 'num', 10), C('visits', 'Visits', 'int', 9), CA('billed_minus_paid', 'Billed minus paid hours', 'num', '{col:billed_hours}-{col:paid_hours}', 11)], D.weekly_d(), 260, [A('billed_minus_paid', '< 0', 'warn')]))
# 17 service revenue
tables.append(T('svcrev', 'Revenue by Service', 'Revenue, cost and margin by service and month',
    'One row per month and service: billed hours, revenue and cost; the margin and the margin share fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('service', 'Service', 'svc', 18), C('billed_hours', 'Billed hours', 'num', 10), C('revenue', 'Revenue', 'money', 12), C('cost', 'Cost', 'money', 12),
    CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 11), CA('margin_share', 'Margin share', 'pct', 'IF({col:revenue}>0,({col:revenue}-{col:cost})/{col:revenue},0)', 10)], D.svcrev_d(), 400, [A('margin_share', '< {set:target_margin}', 'warn')]))
# 18 start-up pages
tables.append(T('startup', 'Start-up Pages', 'Start-up pages: what a one-person agency uses',
    'One row per page of the suite: whether a one-person agency uses it and from how many caregivers it pays to switch it on; hide the rest until you grow. A one-person agency can start with Enquiries, Quotes, Schedule, Visits, Payroll, Invoices and Cash.', [
    C('page_id', 'Row ID', 'text', 9, required=True), C('page', 'Page', 'text', 24), C('part', 'Part', 'text', 9), C('one_person', 'Used by a one-person agency', 'bool', 12), C('from_caregivers', 'Used from caregivers', 'int', 11), C('note', 'Note', 'text', 30)],
    D.startup_d(), 40))
# 19 marketing
tables.append(T('marketing', 'Marketing Spend', 'Marketing spend by month, kind and result',
    'One row per campaign and month: kind, whether it recruits caregivers, cost, results and starts; the cost per start fills in by itself.', [
    C('campaign_id', 'Campaign ID', 'text', 11, required=True), C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'mkind', 18), C('for_recruiting', 'For recruiting', 'bool', 10), C('cost', 'Cost', 'money', 11), C('results', 'Results', 'int', 9), C('started', 'Started', 'int', 9),
    CA('cost_per_start', 'Cost per start', 'money', 'IF({col:started}>0,ROUND({col:cost}/{col:started},2),0)', 11)], D.marketing_d(), 250))
# 20 team
tables.append(T('team', 'Team', 'Team: office, field and outside contacts',
    'One row per person: the owner-director, the care coordinator (scheduler), the office manager, the recruiter, two field supervisors and ten outside contacts; messages use the phone numbers.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 20), LST('team', 'Team', 'team', 11), LST('pay_type', 'Pay type', 'paytype', 12), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26),
    C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly pay', 'int', 11), C('hourly_rate', 'Hourly rate', 'int', 9), C('speciality', 'Speciality', 'text', 30), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11)],
    D.team_d(), 50))
assert len(tables) == 20
