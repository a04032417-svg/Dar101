"""Nonprofit suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np8_lists import *
import np8_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def ORG(): return CA('org', 'Organization', 'text', '{set:org}', 22)
def CPH(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def R(t, c): return '{range:%s.%s}' % (t, c)
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
JAN1 = 'DATE(YEAR({today}),1,1)'
CURM = 'DATE(YEAR({today}),MONTH({today}),1)'
THIS = tok('yr', 'This year'); LAST = tok('yr', 'Last year')
def FI(name): return 'SUMIFS(%s,%s,%s)' % (R('forecast_inputs', 'value'), R('forecast_inputs', 'item'), tok('finput', name))
def NOWROW(col): return 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('cash', col), R('cash', 'month'), R('cash', 'month'))
def FN(f): return tok('function', f)
def AR(a): return tok('area', a)
EX = lambda c: R('expenses', c)
def SHD(share, month='{col:month}'):
    return 'SUMPRODUCT(SUMIFS(%s,%s,%s,%s,%s,%s,%s)*%s)' % (EX('amount'), EX('month'), month, EX('function'), FN('Shared'), EX('category'), R('expense_categories', 'category'), R('expense_categories', share))
def MONC(col): return MONTXT('{col:%s}' % col)

settings = [
    S('org', 'Your organization name', 'text', COMPANY), S('reserve_months', 'Months of reserve, starting point, set your own', 'num', RESERVE_MONTHS),
    S('cost_per_dollar', 'Cost to raise one dollar, starting point, set your own', 'num', COST_PER_DOLLAR), S('volunteer_hour_value', 'Value of one volunteer hour, your setting', 'money', VOLUNTEER_HOUR_VALUE),
    S('employer_cost_pct', 'Employer costs on top of gross pay', 'pct', EMPLOYER_COST_PCT), S('card_fee_pct', 'Card fees on online gifts', 'pct', CARD_FEE_PCT),
    S('area_program', 'Floor area used by programs', 'pct', 0.70), S('area_management', 'Floor area used by management', 'pct', 0.22),
    S('w_learning', 'Share of shared program cost, After-School Learning', 'pct', 0.30), S('w_pantry', 'Share of shared program cost, Family Food Pantry', 'pct', 0.30),
    S('w_senior', 'Share of shared program cost, Senior Meals and Visits', 'pct', 0.25), S('w_camp', 'Share of shared program cost, Summer Youth Camp', 'pct', 0.15),
    S('trend', 'Trend factor for next year, your estimate', 'pct', 0.04), S('tolerance', 'Share over or under budget that still counts as on budget', 'pct', 0.05),
    S('protect_months', 'Months of a new cost the reserve must cover (1 to 4)', 'int', 3), S('full_hours', 'Hours in a full-time month', 'int', 160),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 budget -----------------------------------------------------------------
tables.append(T('budget', 'Budget', 'Monthly budget by area',
    'One row per month and area (four programs, management and fundraising): type the budget; the year fills in by itself.', [
    C('budget_id', 'Budget ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('area', 'Area', 'area', 24), C('budget', 'Budget', 'money', 12), CA('year', 'Year', 'int', 'YEAR({col:month})', 8)],
    D.budget_d(), 260))
# 2 income budget ----------------------------------------------------------
tables.append(T('income_budget', 'Income Budget', 'Monthly income budget by line',
    'One row per month and income line: type the planned money in; the year fills in by itself.', [
    C('income_id', 'Budget ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('line', 'Income line', 'iline', 22), C('budget', 'Budget', 'money', 12), CA('year', 'Year', 'int', 'YEAR({col:month})', 8)],
    D.ibudget_d(), 220))
# 3 expenses ---------------------------------------------------------------
tables.append(T('expenses', 'Expenses', 'Every expense with category, program, function and fund',
    'One row per expense: date, month, category, vendor, program, function, fund and amount; the budget against actual, the functional split and the cash pages read from here.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('category', 'Category', 'category', 22), C('vendor', 'Vendor', 'text', 24),
    LST('program', 'Program', 'eprogram', 22), LST('function', 'Function', 'function', 12), LST('fund', 'Fund', 'fund', 22), C('amount', 'Amount', 'money', 12), C('grant_id', 'Grant ID', 'text', 9), C('event_id', 'Event ID', 'text', 9)],
    D.expenses_d(), 3000))
# 4 expense categories -----------------------------------------------------
tables.append(T('expense_categories', 'Expense Categories', 'Shares of each category by function',
    'One row per expense category: the share charged to programs, management and fundraising when the cost is shared, and the rule behind it (your choice); the check and shared cost fill in.', [
    LST('category', 'Category', 'category', 22, required=True), C('program_share', 'Program share', 'pct', 9), C('management_share', 'Management share', 'pct', 11), C('fundraising_share', 'Fundraising share', 'pct', 11),
    LST('rule', 'Rule', 'rule', 12), C('basis', 'Basis of the rule', 'text', 30),
    CA('check', 'Shares add to 100%', 'text', 'IF(ABS({col:program_share}+{col:management_share}+{col:fundraising_share}-1)<0.001,%s,%s)' % (v('OK'), v('Check')), 10),
    CA('shared_year', 'Shared cost this year', 'money', 'SUMIFS(%s,%s,{col:category},%s,%s,%s,">="&%s)' % (EX('amount'), EX('category'), EX('function'), FN('Shared'), EX('date'), JAN1), 12),
    CA('change_on', 'Rule changes on', 'date', 'DATE(YEAR({today})+1,1,1)', 11), CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), ORG()],
    D.cats_d(), 40, [A('check', '= ' + v('Check'), 'bad')]))
# 5 budget against actual --------------------------------------------------
def AREAW(): return 'IF({col:area}=%s,{set:w_learning},IF({col:area}=%s,{set:w_pantry},IF({col:area}=%s,{set:w_senior},IF({col:area}=%s,{set:w_camp},1))))' % (
    AR('After-School Learning'), AR('Family Food Pantry'), AR('Senior Meals and Visits'), AR('Summer Youth Camp'))
DIRECT = ('IF({col:area}=%s,SUMIFS(%s,%s,{col:month},%s,%s),IF({col:area}=%s,SUMIFS(%s,%s,{col:month},%s,%s),SUMIFS(%s,%s,{col:month},%s,{col:area},%s,%s)+0.25*SUMIFS(%s,%s,{col:month},%s,%s,%s,%s)))' % (
    AR('Management'), EX('amount'), EX('month'), EX('function'), FN('Management'), AR('Fundraising'), EX('amount'), EX('month'), EX('function'), FN('Fundraising'),
    EX('amount'), EX('month'), EX('program'), EX('function'), FN('Program'), EX('amount'), EX('month'), EX('program'), tok('eprogram', 'Shared'), EX('function'), FN('Program')))
SHARED_PART = 'IF({col:area}=%s,%s,IF({col:area}=%s,%s,%s*{col:weight}))' % (AR('Management'), SHD('management_share'), AR('Fundraising'), SHD('fundraising_share'), SHD('program_share'))
tables.append(T('budget_actual', 'Budget vs Actual', 'Budget against actual by area and month',
    'One row per month and area: pick the month and area; the budget, the actual cost with each shared cost allocated by its rule, the difference, the share used and the status fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('area', 'Area', 'area', 24),
    CA('budget', 'Budget', 'money', 'SUMIFS(%s,%s,{col:month},%s,{col:area})' % (R('budget', 'budget'), R('budget', 'month'), R('budget', 'area')), 12),
    CA('weight', 'Share of shared program cost', 'pct', AREAW(), 9), CA('direct', 'Direct cost', 'money', DIRECT, 12), CA('shared_part', 'Allocated shared cost', 'money', SHARED_PART, 12),
    CA('actual', 'Actual', 'money', '{col:direct}+{col:shared_part}', 12), CA('difference', 'Difference', 'money', '{col:actual}-{col:budget}', 12),
    CA('share_used', 'Share used', 'pct', 'IF({col:budget}>0,{col:actual}/{col:budget},0)', 9), CA('over_by', 'Over by', 'money', 'MAX(0,{col:difference})', 11),
    CA('status', 'Status', 'text', 'IF({col:share_used}>1+{set:tolerance},%s,IF({col:share_used}<1-{set:tolerance},%s,%s))' % (v('Over'), v('Under'), v('On budget')), 11),
    CA('month_name', 'Month name', 'text', MONC('month'), 16), CA('confirm_by', 'Confirm lines by', 'date', 'EOMONTH({today},1)', 11),
    CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('pm_phone', 'Program manager phone', D.PM_PHONE), CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), ORG()],
    D.bact_d(), 120, [A('status', '= ' + v('Over'), 'bad'), A('status', '= ' + v('Under'), 'warn'), A('status', '= ' + v('On budget'), 'good')]))
# 6 functional split -------------------------------------------------------
def FSUM(col, p): return 'SUMIFS(%s,%s,%s)' % (R('functional', col), R('functional', 'period'), p)
tables.append(T('functional', 'Functional Split', 'Program, management and fundraising cost by month',
    'One row per month: direct cost by function plus each shared cost split by the shares on Expense Categories; the shares of program and fundraising fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), LST('period', 'Year', 'yr', 14),
    CA('program', 'Program cost', 'money', 'SUMIFS(%s,%s,{col:month},%s,%s)+%s' % (EX('amount'), EX('month'), EX('function'), FN('Program'), SHD('program_share')), 12),
    CA('management', 'Management cost', 'money', 'SUMIFS(%s,%s,{col:month},%s,%s)+%s' % (EX('amount'), EX('month'), EX('function'), FN('Management'), SHD('management_share')), 12),
    CA('fundraising', 'Fundraising cost', 'money', 'SUMIFS(%s,%s,{col:month},%s,%s)+%s' % (EX('amount'), EX('month'), EX('function'), FN('Fundraising'), SHD('fundraising_share')), 12),
    CA('total', 'Total cost', 'money', '{col:program}+{col:management}+{col:fundraising}', 12),
    CA('program_share', 'Program share', 'pct', 'IF({col:total}>0,{col:program}/{col:total},0)', 9), CA('management_share', 'Management share', 'pct', 'IF({col:total}>0,{col:management}/{col:total},0)', 9),
    CA('fundraising_share', 'Fundraising share', 'pct', 'IF({col:total}>0,{col:fundraising}/{col:total},0)', 9),
    CA('budget', 'Budget', 'money', 'SUMIFS(%s,%s,{col:month})' % (R('budget', 'budget'), R('budget', 'month')), 12), CA('complete', 'Complete month', 'int', 'IF({col:month}<%s,1,0)' % CURM, 8),
    CA('fr_share_year', 'Fundraising share this year', 'pct', 'IFERROR(%s/%s,0)' % (FSUM('fundraising', THIS), FSUM('total', THIS)), 10),
    CA('fr_share_last', 'Fundraising share last year', 'pct', 'IFERROR(%s/%s,0)' % (FSUM('fundraising', LAST), FSUM('total', LAST)), 10),
    CA('next_budget', 'Next year budget, your estimate', 'money', 'SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)*(1+{set:trend})' % (R('functional', 'total'), R('functional', 'month'), CURM, R('functional', 'month'), CURM), 12),
    CA('month_name', 'Month name', 'text', MONC('month'), 16), CPH('fin_phone', 'Finance chair phone', D.FIN_PHONE), ORG()],
    D.functional_d(), 60))
# 7 allocation rules -------------------------------------------------------
def AC(col): return 'IFERROR(INDEX(%s,MATCH({col:category},%s,0)),0)' % (R('expense_categories', col), R('expense_categories', 'category'))
tables.append(T('allocation_rules', 'Allocation Rules', 'Each shared cost, its rule and who carries it this year',
    'One row per expense category: the rule and basis from Expense Categories, the shared cost this year and the part charged to programs, management and fundraising.', [
    LST('category', 'Category', 'category', 22, required=True), LKT('expense_categories.rule', 'expense_categories.category', 'category') and CA('rule', 'Rule', 'text', LKT('expense_categories.rule', 'expense_categories.category', 'category'), 12),
    CA('basis', 'Basis of the rule', 'text', LKT('expense_categories.basis', 'expense_categories.category', 'category'), 30),
    CA('shared_year', 'Shared cost this year', 'money', AC('shared_year'), 12), CA('program', 'Charged to programs', 'money', '{col:shared_year}*' + AC('program_share'), 12),
    CA('management', 'Charged to management', 'money', '{col:shared_year}*' + AC('management_share'), 12), CA('fundraising', 'Charged to fundraising', 'money', '{col:shared_year}*' + AC('fundraising_share'), 12),
    CA('share_program', 'Program share', 'pct', AC('program_share'), 9)], D.alloc_d(), 40))
# 8 pay --------------------------------------------------------------------
tables.append(T('pay', 'Pay and Staff Cost', 'Monthly pay of each staff member with employer cost',
    'One row per staff member and month: hours, gross pay and employer cost; the total, the function and the share of a full-time month fill in by themselves.', [
    C('pay_id', 'Pay ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('staff', 'Staff', 'staff', 22), LST('role', 'Role', 'payrole', 22), C('pay_type', 'Pay type', 'text', 9), C('hours', 'Hours', 'num', 8),
    C('gross', 'Gross pay', 'money', 12), C('employer_cost', 'Employer cost', 'money', 12), C('paid', 'Paid', 'bool', 7), C('phone', 'Phone', 'text', 18),
    CA('total', 'Total cost', 'money', '{col:gross}+{col:employer_cost}', 12),
    CA('function', 'Function', 'text', 'IF(OR({col:role}=%s,{col:role}=%s),%s,IF({col:role}=%s,%s,%s))' % (tok('payrole', 'Executive director'), tok('payrole', 'Bookkeeper'), FN('Management'), tok('payrole', 'Development manager'), FN('Fundraising'), FN('Program')), 12),
    CA('time_pct', 'Share of a full month', 'pct', 'IF({set:full_hours}>0,{col:hours}/{set:full_hours},0)', 9), CA('month_name', 'Month name', 'text', MONC('month'), 16), ORG()],
    D.pay_d(), 320))
# 9 income by source -------------------------------------------------------
def IBL(*lines): return '+'.join('SUMIFS(%s,%s,{col:month},%s,%s)' % (R('income_budget', 'budget'), R('income_budget', 'month'), R('income_budget', 'line'), tok('iline', l)) for l in lines)
tables.append(T('income_source', 'Income by Source', 'Money in by month: gifts, grants, events and dues',
    'One row per month: type the gifts, grants, events and dues from your gift log, grant payments and event sheets (and the in-kind value as a memo); the total, the budget, money out and net fill in.', [
    C('month', 'Month', 'date', 11, required=True), LST('period', 'Year', 'yr', 14), C('gifts', 'Gifts', 'money', 12), C('grants', 'Grants', 'money', 12), C('events', 'Events', 'money', 12), C('dues', 'Dues', 'money', 11),
    C('inkind', 'In-kind value, not cash', 'money', 12),
    CA('total', 'Total money in', 'money', '{col:gifts}+{col:grants}+{col:events}+{col:dues}', 12),
    CA('bud_gifts', 'Gifts budget', 'money', IBL('Individuals', 'Business and groups'), 11), CA('bud_grants', 'Grants budget', 'money', IBL('Grants'), 11), CA('bud_events', 'Events budget', 'money', IBL('Events'), 11),
    CA('bud_dues', 'Dues budget', 'money', IBL('Dues and other'), 11), CA('budget', 'Total budget', 'money', '{col:bud_gifts}+{col:bud_grants}+{col:bud_events}+{col:bud_dues}', 12),
    CA('difference', 'Against budget', 'money', '{col:total}-{col:budget}', 12), CA('money_out', 'Money out', 'money', 'SUMIFS(%s,%s,{col:month})' % (EX('amount'), EX('month')), 12),
    CA('net', 'Net', 'money', '{col:total}-{col:money_out}', 12), CA('complete', 'Complete month', 'int', 'IF({col:month}<%s,1,0)' % CURM, 8),
    CA('money_in_year', 'Money in this year', 'money', 'SUMIFS(%s,%s,">="&%s)' % (R('income_source', 'total'), R('income_source', 'month'), JAN1), 12),
    CA('money_out_year', 'Money out this year', 'money', 'SUMIFS(%s,%s,">="&%s)' % (EX('amount'), EX('date'), JAN1), 12),
    CA('behind_by', 'Behind plan by', 'money', 'MAX(0,SUMIFS(%s,%s,">="&%s,%s,"<"&%s)-SUMIFS(%s,%s,">="&%s,%s,"<"&%s))' % (
        R('income_source', 'budget'), R('income_source', 'month'), JAN1, R('income_source', 'month'), CURM, R('income_source', 'total'), R('income_source', 'month'), JAN1, R('income_source', 'month'), CURM), 12),
    CA('month_name', 'Month name', 'text', MONC('month'), 16), CPH('bm_phone', 'Board member phone', D.BM_PHONE), CPH('dev_phone', 'Development manager phone', D.DEV_PHONE), ORG()],
    D.income_d(), 60))
# 10 cash by month ---------------------------------------------------------
tables.append(T('cash', 'Cash by Month', 'Cash, restricted and designated money and months of reserve',
    'One row per month: opening cash, receipts, payments, restricted and designated money; the closing cash, free money, the average monthly expense and the months of reserve fill in by themselves.', [
    C('cash_id', 'Cash ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('opening', 'Opening cash', 'money', 13), C('receipts', 'Receipts', 'money', 12), C('payments', 'Payments', 'money', 12),
    C('restricted', 'Restricted money', 'money', 13), C('designated', 'Designated money', 'money', 13),
    CA('closing', 'Closing cash', 'money', '{col:opening}+{col:receipts}-{col:payments}', 13), CA('free_money', 'Free money', 'money', '{col:closing}-{col:restricted}-{col:designated}', 13),
    CA('avg_monthly_expense', 'Average monthly expense', 'money', 'IFERROR(AVERAGEIFS(%s,%s,"<"&{col:month},%s,">="&EDATE({col:month},-12)),SUMIFS(%s,%s,{col:month}))' % (
        R('functional', 'total'), R('functional', 'month'), R('functional', 'month'), R('functional', 'total'), R('functional', 'month')), 13),
    CA('reserve_months', 'Months of reserve', 'num', 'IF({col:avg_monthly_expense}>0,ROUND({col:free_money}/{col:avg_monthly_expense},2),0)', 9),
    CA('now_flag', 'Latest month', 'int', 'IF({col:month}=MAX(%s),1,0)' % R('cash', 'month'), 7), CA('reserve_now', 'Reserve months now', 'num', 'IF({col:now_flag}=1,{col:reserve_months},0)', 9),
    CA('setting_now', 'Setting now', 'num', 'IF({col:now_flag}=1,{set:reserve_months},0)', 9), CA('setting', 'Reserve months setting', 'num', '{set:reserve_months}', 9),
    CA('month_name', 'Month name', 'text', MONC('month'), 16), CA('close_by', 'Close the month by', 'date', 'EOMONTH({col:month},0)+10', 11), CA('balance_date', 'Balance date', 'date', 'MIN(EOMONTH({col:month},0),{today})', 11),
    CA('unrec_n', 'Bank lines not reconciled', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (R('bank', 'reconciled'), NO, R('bank', 'bank_id')), 9),
    CA('pay_year', 'Pay cost this year', 'money', 'SUMIFS(%s,%s,">="&DATE(YEAR({col:month}),1,1),%s,"<="&{col:month})' % (R('pay', 'total'), R('pay', 'month'), R('pay', 'month')), 12),
    CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('bm_phone', 'Board member phone', D.BM_PHONE), CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), CPH('acc_phone', 'Accountant phone', D.ACC_PHONE),
    CPH('bank_phone', 'Bank contact phone', D.BANK_PHONE), CPH('broker_phone', 'Insurance broker phone', D.BROKER_PHONE), CPH('vol_phone', 'Volunteer treasurer phone', D.VOL_PHONE), ORG()],
    D.cash_d(), 60, [A('reserve_months', '< {set:reserve_months}', 'warn')]))
# 11 bank ------------------------------------------------------------------
tables.append(T('bank', 'Bank Lines', 'Bank lines with money in, money out and the reconciled flag',
    'One row per bank line: date, kind, description, money in or out and the balance; tick reconciled when you have matched the line; the net and the open date fill in.', [
    C('bank_id', 'Bank ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'bkind', 18), C('description', 'Description', 'text', 30),
    C('money_in', 'Money in', 'money', 12), C('money_out', 'Money out', 'money', 12), C('balance', 'Balance', 'money', 13), C('reconciled', 'Reconciled', 'bool', 9),
    CA('net', 'Net', 'money', '{col:money_in}-{col:money_out}', 12), CA('open_date', 'Open since', 'date', 'IF({col:reconciled}=%s,{col:date},"")' % NO, 11)],
    D.bank_d(), 1000, [A('reconciled', '= ' + NO, 'warn')]))
# 12 cash forecast ---------------------------------------------------------
NET = ('{col:gifts}*(1+%s)+{col:recurring}*(1+%s)+{col:pledges_due}*%s+{col:grants}*%s+{col:event_net}*(1+%s)+{col:dues}*(1+%s)-{col:expenses}*(1+%s)-{col:one_off}' % (
    FI('Gifts change'), FI('Recurring change'), FI('Pledges collected share'), FI('Grants received share'), FI('Event net change'), FI('Dues change'), FI('Expenses change')))
FC = lambda c: R('forecast', c)
tables.append(T('forecast', 'Cash Forecast', 'Twelve months of cash',
    'One row per future month: type the plan for each source and any one-off cost; the net, the closing cash, free money, months of reserve and the first month under your setting fill in by themselves.', [
    C('forecast_id', 'Forecast ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('step', 'Step', 'step', 11), C('gifts', 'Gifts', 'money', 12), C('recurring', 'Recurring gifts', 'num', 11),
    C('pledges_due', 'Pledges due', 'money', 11), C('grants', 'Grants', 'num', 11), C('event_net', 'Event net', 'num', 11), C('dues', 'Dues', 'money', 10), C('expenses', 'Expenses', 'money', 12),
    C('one_off', 'One-off cost', 'num', 11), C('one_off_note', 'One-off note', 'text', 30), C('event', 'Event', 'text', 14),
    CA('net', 'Net for the month', 'money', NET, 12),
    CA('closing', 'Closing cash', 'money', '%s+%s+SUMIFS(%s,%s,"<="&{col:month})' % (NOWROW('closing'), FI('Opening cash change'), FC('net'), FC('month')), 13),
    CA('free_money', 'Free money', 'money', '{col:closing}-%s-%s' % (NOWROW('restricted'), NOWROW('designated')), 13),
    CA('avg_expense', 'Average monthly expense', 'money', '%s*(1+%s)' % (NOWROW('avg_monthly_expense'), FI('Expense growth for reserve months')), 13),
    CA('reserve_months', 'Months of reserve', 'num', 'IF({col:avg_expense}>0,ROUND({col:free_money}/{col:avg_expense},2),0)', 9),
    CA('headroom', 'Free money above the setting', 'money', '{col:free_money}-{set:reserve_months}*{col:avg_expense}', 13),
    CA('gap', 'Gap to the setting', 'money', 'MAX(0,{set:reserve_months}*{col:avg_expense}-{col:free_money})', 12),
    CA('cum_gifts', 'Gifts to date', 'money', 'SUMIFS(%s,%s,"<="&{col:month})' % (FC('gifts'), FC('month')), 12), CA('cum_exp', 'Expenses to date', 'money', 'SUMIFS(%s,%s,"<="&{col:month})' % (FC('expenses'), FC('month')), 12),
    CA('dip_key', 'Month under the setting', 'date', 'IF({col:reserve_months}<{set:reserve_months},{col:month},"")', 11),
    CA('first_dip', 'First month under the setting', 'date', 'IFERROR(SMALL(%s,1),"")' % FC('dip_key'), 11), CA('first_dip_name', 'First month under, name', 'text', 'IFERROR(%s,"")' % MONTXT('{col:first_dip}'), 16),
    CA('low_month_name', 'Lowest cash month', 'text', MONTXT('INDEX(%s,MATCH(MIN(%s),%s,0))' % (FC('month'), FC('closing'), FC('closing'))), 16), CA('low_amount', 'Lowest closing cash', 'money', 'MIN(%s)' % FC('closing'), 13),
    CA('setting', 'Reserve months setting', 'num', '{set:reserve_months}', 9), CA('month_name', 'Month name', 'text', MONC('month'), 16),
    CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('fin_phone', 'Finance chair phone', D.FIN_PHONE), CPH('dev_phone', 'Development manager phone', D.DEV_PHONE), CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), ORG()],
    D.forecast_d(), 30, [A('reserve_months', '< {set:reserve_months}', 'bad')]))
# 13 forecast inputs -------------------------------------------------------
tables.append(T('forecast_inputs', 'Forecast Inputs', 'Changes and holdings the cash forecast uses',
    'One row per input: type the change or the share; the forecast reads it. Leave 0 for no change and 1 for all received.', [
    LST('item', 'Input', 'finput', 30, required=True), C('value', 'Value', 'num', 12), C('note', 'Note', 'text', 60)], D.finputs_d(), 30))
# 14 lowest cash month -----------------------------------------------------
LOWITEMS = [('Lowest closing cash', 'MIN', 'closing'), ('Lowest free money', 'MIN', 'free_money'), ('Lowest reserve months', 'MIN', 'reserve_months'), ('Highest closing cash', 'MAX', 'closing'), ('Highest reserve months', 'MAX', 'reserve_months')]
def LOWPICK(kind):
    f = 'MIN(%s)' % FC('closing')
    for name, fnc, col in reversed(LOWITEMS):
        val = '%s(%s)' % (fnc, FC(col)) if kind == 'amount' else 'INDEX(%s,MATCH(%s(%s),%s,0))' % (FC('month'), fnc, FC(col), FC(col))
        f = 'IF({col:item}=%s,%s,%s)' % (v(name), val, f)
    return f
tables.append(T('lowest_cash', 'Lowest Cash Month', 'Lowest cash, free money and reserve',
    'One row per measure: the lowest or highest closing cash, free money or months of reserve in the forecast, with the month it falls in.', [
    LST('item', 'Item', 'ck2', 26, required=True), CA('month', 'Month', 'date', 'IFERROR(%s,"")' % LOWPICK('month'), 12), CA('amount', 'Amount or months', 'num', LOWPICK('amount'), 14)], D.lowest_d(), 10))
# 15 scenarios -------------------------------------------------------------
FCNOW = 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (FC('closing'), FC('month'), FC('month'))
tables.append(T('scenarios', 'Scenarios', 'Scenario tests',
    'One row per scenario: type the change in gifts, recurring gifts and costs and whether the biggest donor or one grant is lost; the year-end cash, months of reserve and a verdict fill in by themselves.', [
    LST('scenario', 'Scenario', 'scen', 26, required=True), C('gifts_pct', 'Gifts change', 'pct', 9), C('recurring_pct', 'Recurring change', 'pct', 10), C('cost_pct', 'Cost change', 'pct', 9),
    C('lose_donor', 'Lose biggest donor', 'bool', 9), C('lose_grant', 'Lose one grant', 'bool', 9),
    CA('income_change', 'Income change', 'money', '{col:gifts_pct}*SUM(%s)+{col:recurring_pct}*SUM(%s)-IF({col:lose_donor}=%s,%s,0)-IF({col:lose_grant}=%s,MAX(%s),0)' % (FC('gifts'), FC('recurring'), YES, FI('Biggest donor giving a year'), YES, FC('grants')), 12),
    CA('cost_change', 'Cost change amount', 'money', '{col:cost_pct}*SUM(%s)' % FC('expenses'), 12),
    CA('year_end_cash', 'Year-end cash', 'money', '%s+{col:income_change}-{col:cost_change}' % FCNOW, 13),
    CA('reserve_months', 'Months of reserve', 'num', 'IFERROR(ROUND(({col:year_end_cash}-%s-%s)/INDEX(%s,1),2),0)' % (NOWROW('restricted'), NOWROW('designated'), FC('avg_expense')), 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:reserve_months}>={set:reserve_months}+0.25,%s,IF({col:reserve_months}>={set:reserve_months},%s,%s))' % (v('Holds'), v('Thin'), v('Below')), 10),
    CA('setting', 'Reserve months setting', 'num', '{set:reserve_months}', 9), CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('acc_phone', 'Accountant phone', D.ACC_PHONE), ORG()],
    D.scen_d(), 30, [A('verdict', '= ' + v('Below'), 'bad'), A('verdict', '= ' + v('Thin'), 'warn'), A('verdict', '= ' + v('Holds'), 'good')]))
# 16 afford this -----------------------------------------------------------
HR, FR_, MO = FC('headroom'), FC('free_money'), FC('month')
AVG1 = 'INDEX(%s,1)' % FC('avg_expense')
def BADTERM(s, k): return 'IF({set:protect_months}>%d,IF(INDEX(%s,%s)<{col:setup_cost}+{col:monthly_cost}*%d,1,0),0)' % (k, HR, s, k + 1) if False else 'IF({set:protect_months}>%d,IF(INDEX(%s,%s+%d)<{col:setup_cost}+{col:monthly_cost}*%d,1,0),0)' % (k, HR, s, k, k + 1)
SHORT = '+'.join(BADTERM('{col:start_no}', k) for k in range(4))
def BADLIT(s): return '+'.join(BADTERM(str(s), k) for k in range(4) if s + k <= 12)
FIRST = '0'
for _s in range(12, 0, -1): FIRST = 'IF(AND(%d>={col:start_no},%s=0),%d,%s)' % (_s, BADLIT(_s), _s, FIRST)
RAFTER = 'MIN(%s)' % ','.join('IFERROR(IF({set:protect_months}>%d,(INDEX(%s,{col:start_no}+%d)-{col:monthly_cost}*%d-{col:setup_cost})/%s,1E9),1E9)' % (k, FR_, k, k + 1, AVG1) for k in range(4))
tables.append(T('afford', 'Afford This', 'New hires and programs against the forecast',
    'One row per idea: type the monthly cost, set-up cost and start month number (1 is next month); months funded, reserve after, earliest start and a verdict fill in.', [
    C('item', 'Hire or program', 'text', 30, required=True), C('monthly_cost', 'Monthly cost', 'money', 11), C('setup_cost', 'Set-up cost', 'money', 11), C('start_no', 'Start month number', 'int', 9), C('decide_on', 'Decide by', 'date', 11),
    CA('yearly_cost', 'Cost for a full year', 'money', '{col:monthly_cost}*12+{col:setup_cost}', 12),
    CA('months_funded', 'Months funded above the setting', 'int', 'IFERROR(MAX(0,ROUNDDOWN((MIN(%s)-{set:reserve_months}*%s-{col:setup_cost})/{col:monthly_cost},0)),0)' % (','.join('IF(%d>={col:start_no},INDEX(%s,%d),1E9)' % (k, FR_, k) for k in range(1, 13)), AVG1), 11),
    CA('reserve_after', 'Lowest months of reserve after', 'num', 'IFERROR(ROUND(%s,2),0)' % RAFTER, 10), CA('short_months', 'Months under the setting', 'int', SHORT, 9),
    CA('first_ok', 'Earliest start number', 'int', FIRST, 9), CA('first_start', 'Earliest start', 'date', 'IF({col:first_ok}=0,"",INDEX(%s,{col:first_ok}))' % MO, 11),
    CA('verdict', 'Verdict', 'text', 'IF({col:short_months}=0,%s,IF({col:first_ok}=0,%s,%s&" "&%s))' % (v('Yes'), v('Not yet'), v('Yes after'), MONTXT('INDEX(%s,{col:first_ok}-1)' % MO)), 22),
    CPH('ed_phone', 'Executive director phone', D.ED_PHONE), ORG()], D.afford_d(), 30, [A('verdict', '= ' + v('Not yet'), 'bad'), A('verdict', '= ' + v('Yes'), 'good')]))
# 17 annual report numbers -------------------------------------------------
def PERIOD(this):
    if this: a, b, be, ya = JAN1, CURM, '{today}', 'DATE(YEAR({today}),12,1)'
    else: a, b, be, ya = 'DATE(YEAR({today})-1,1,1)', 'DATE(YEAR({today})-1,12,1)', 'DATE(YEAR({today})-1,12,31)', 'DATE(YEAR({today})-1,12,1)'
    INC = lambda c: 'SUMIFS(%s,%s,">="&%s,%s,"<="&%s)' % (R('income_source', c), R('income_source', 'month'), a, R('income_source', 'month'), b)
    FUNC = lambda c: 'SUMIFS(%s,%s,">="&%s,%s,"<="&%s)' % (R('functional', c), R('functional', 'month'), a, R('functional', 'month'), b)
    OUT = 'SUMIFS(%s,%s,">="&%s,%s,"<="&%s)' % (EX('amount'), EX('date'), a, EX('date'), be)
    PAYS = 'SUMIFS(%s,%s,">="&%s,%s,"<="&%s)' % (R('pay', 'total'), R('pay', 'month'), a, R('pay', 'month'), b)
    typed = '{col:typed_this}' if this else '{col:typed_last}'
    T_ = lambda: 'IF(%s="","",%s)' % (typed, typed)
    hours = 'INDEX(%s,MATCH(17,%s,0))' % (R('annual_report', 'typed_this' if this else 'typed_last'), R('annual_report', 'no'))
    res = 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('cash', 'reserve_months'), R('cash', 'month'), R('cash', 'month')) if this else 'SUMIFS(%s,%s,%s)' % (R('cash', 'reserve_months'), R('cash', 'month'), ya)
    return [INC('total'), INC('gifts'), INC('grants'), INC('events'), INC('dues'), INC('inkind'), OUT, FUNC('program'), FUNC('management'), FUNC('fundraising'), '%s-%s' % (INC('total'), OUT),
            'IFERROR(%s/%s,0)' % (FUNC('program'), FUNC('total')), 'IFERROR(%s/%s,0)' % (FUNC('fundraising'), INC('total')), PAYS, res, T_(), T_(), 'IF(%s="","",%s*{set:volunteer_hour_value})' % (hours, hours), T_(), T_()]
def CHOOSEROW(this): return 'IFERROR(CHOOSE({col:no},%s),"")' % ','.join(PERIOD(this))
NUMTXT = lambda c: 'IF(OR({col:no}=12,{col:no}=20),ROUND({col:%s}*100,1)&"%%",ROUND({col:%s},2))' % (c, c)
ARR = lambda c: R('annual_report', c)
tables.append(T('annual_report', 'Annual Report Numbers', 'The numbers for the annual report in plain sentences',
    'One row per number: type people served, volunteer hours, donors and retention; money, shares and reserve fill in from this workbook, with a sentence for each.', [
    C('item', 'Item', 'text', 30, required=True), C('no', 'Number', 'int', 8), C('typed_this', 'Typed, this year', 'num', 12), C('typed_last', 'Typed, last year', 'num', 12),
    CA('this_year', 'Number this year', 'num', CHOOSEROW(True), 14), CA('last_year', 'Number last year', 'num', CHOOSEROW(False), 14),
    CA('status', 'Status', 'text', 'IF(AND(ISNUMBER({col:this_year}),ISNUMBER({col:last_year})),%s,%s)' % (v('Ready'), v('Missing')), 9),
    CA('sentence', 'Sentence', 'text', 'IF({col:status}=%s,{col:item}&": "&%s&" "&%s&", "&%s&" "&%s,"")' % (v('Ready'), NUMTXT('this_year'), v('this year'), NUMTXT('last_year'), v('last year')), 60),
    CA('items_ready', 'Items ready', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (ARR('status'), v('Ready'), ARR('item')), 8), CA('missing_n', 'Items missing', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (ARR('status'), v('Missing'), ARR('item')), 8),
    CA('first_missing', 'First item missing', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (ARR('item'), v('Missing'), ARR('status')), 26),
    CA('money_in', 'Money in this year', 'money', 'INDEX(%s,MATCH(1,%s,0))' % (ARR('this_year'), ARR('no')), 13), CA('people', 'People served this year', 'int', 'INDEX(%s,MATCH(16,%s,0))' % (ARR('this_year'), ARR('no')), 9),
    C('grant_id', 'Grant ID', 'text', 9), CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('acc_phone', 'Accountant phone', D.ACC_PHONE),
    CPH('funder_phone', 'Program officer phone', D.FUNDER_PHONE), CPH('donor_phone', 'Donor phone', D.DONOR_PHONE), ORG()],
    D.annual_d(), 40, [A('status', '= ' + v('Missing'), 'bad')]))
# 18 money in by source ----------------------------------------------------
SRC = lambda c: 'SUMIFS(%s,%s,{col:period})' % (R('income_source', c), R('income_source', 'period'))
tables.append(T('money_by_source', 'Money in by Source', 'Money in by source and year',
    'One row per source and year: the amount from Income by Source, its share of money in and the amount last year.', [
    LST('source', 'Source', 'source', 14, required=True), LST('period', 'Year', 'yr', 14),
    CA('amount', 'Amount', 'money', 'IF({col:source}=%s,%s,IF({col:source}=%s,%s,IF({col:source}=%s,%s,IF({col:source}=%s,%s,%s))))' % (
        tok('source', 'Gifts'), SRC('gifts'), tok('source', 'Grants'), SRC('grants'), tok('source', 'Events'), SRC('events'), tok('source', 'Dues'), SRC('dues'), SRC('inkind')), 13),
    CA('share', 'Share of money in', 'pct', 'IF({col:source}=%s,"",IFERROR({col:amount}/%s,0))' % (tok('source', 'In-kind'), SRC('total')), 9),
    CA('last_year', 'Same source last year', 'money', 'SUMIFS(%s,%s,{col:source},%s,%s)' % (R('money_by_source', 'amount'), R('money_by_source', 'source'), R('money_by_source', 'period'), LAST), 13)],
    D.mbs_d(), 30))
# 19 money out by function -------------------------------------------------
tables.append(T('money_out_function', 'Money out by Function', 'Money out this year by function',
    'One row per function and year: program, management and fundraising cost after every shared cost is split by its rule; shared cost not yet split is zero when every category has a rule.', [
    LST('function', 'Function', 'function', 14, required=True), LST('period', 'Year', 'yr', 14),
    CA('amount', 'Amount', 'money', 'IF({col:function}=%s,%s,IF({col:function}=%s,%s,IF({col:function}=%s,%s,0)))' % (
        FN('Program'), FSUM('program', '{col:period}'), FN('Management'), FSUM('management', '{col:period}'), FN('Fundraising'), FSUM('fundraising', '{col:period}')), 13),
    CA('share', 'Share of money out', 'pct', 'IFERROR({col:amount}/%s,0)' % FSUM('total', '{col:period}'), 9)], D.mof_d(), 30))
# 20 transfers -------------------------------------------------------------
tables.append(T('transfers', 'Transfers and Reserve', 'Board transfers and releases from restriction',
    'One row per move between funds: type the date, the funds, the amount and a note; the part added to the Facilities Reserve fills in by itself.', [
    C('transfer_id', 'Transfer ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), LST('from_fund', 'From fund', 'fund', 22), C('to_fund', 'To fund', 'text', 22), C('amount', 'Amount', 'money', 12),
    C('note', 'Note', 'text', 40), CA('to_reserve', 'Added to Facilities Reserve', 'money', 'IF({col:to_fund}=%s,{col:amount},0)' % tok('fund', 'Facilities Reserve'), 12), CA('year', 'Year', 'int', 'YEAR({col:date})', 8)],
    D.transfers_d(), 40))
assert len(tables) == 20
