"""Household Finance suite part 5: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf5_lists import *
import hf5_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def G(idc, body): return 'IF({col:%s}="","",%s)' % (idc, body)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
DEP, SPEND = tok('ctkind', 'Deposit'), tok('ctkind', 'Spend')
EMERG, SINK = tok('gkind', 'Emergency fund'), tok('gkind', 'Sinking fund')
HIGH, MED = tok('priority', 'High'), tok('priority', 'Medium')
PAYROLL = tok('rtsource', 'Payroll')
JOINT = tok('person', 'Joint')
PPY = 'IF({set:pay_freq}=%s,52,IF({set:pay_freq}=%s,26,IF({set:pay_freq}=%s,24,12)))' % (tok('payfreq', 'Weekly'), tok('payfreq', 'Every two weeks'), tok('payfreq', 'Twice a month'))
GL = lambda c: R('goals', c)
CT = lambda c: R('contributions', c)
AC = lambda c: R('annual_costs', c)
RT = lambda c: R('retirement', c)
IC = lambda c: R('income', c)
TXR = lambda c: R('transactions', c)
ES = lambda c: R('essential_months', c)
CM = lambda c: R('contrib_months', c)
CG = lambda c: R('contrib_goals', c)
EAVG = 'IFERROR(AVERAGEIFS(%s,%s,">="&EDATE(%s,-{set:essential_months}),%s,"<"&%s),0)' % (ES('essential'), ES('month'), MS, ES('month'), MS)
EBAL = 'SUMIFS(%s,%s,%s)' % (GL('saved'), GL('kind'), EMERG)
P = D.PH
def PHC(who, label): return CA(who + '_phone', label, 'text', '"%s"' % P[who], 18)
def HH(): return CA('household', 'Household', 'text', '{set:household}', 22)
def N1(): return CA('partner1', 'Partner 1 name', 'text', '{set:partner1}', 14)
def N2(): return CA('partner2', 'Partner 2 name', 'text', '{set:partner2}', 14)
def GLK(c): return 'INDEX(%s,MATCH({col:goal},%s,0))' % (GL(c), GL('goal'))

settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('partner1', 'Partner 1 name, shown in messages', 'text', 'Partner 1'), S('partner2', 'Partner 2 name, shown in messages', 'text', 'Partner 2'),
    S('pay_freq', 'Pay rhythm of partner 1', 'list', key('payfreq', PAYDAY1_FREQ), list='payfreq'),
    S('emergency_low', 'Emergency low, months: typical range, check your own numbers', 'int', EMERGENCY_MONTHS_LOW),
    S('emergency_high', 'Emergency high months: typical range, check your own numbers', 'int', EMERGENCY_MONTHS_HIGH),
    S('essential_months', 'Months of essential spending averaged', 'int', 6),
    S('retirement_min', 'Retirement low: typical range, check your own numbers', 'pct', RETIREMENT_MIN),
    S('retirement_good', 'Retirement high: typical range, check your own numbers', 'pct', RETIREMENT_GOOD),
    S('insurance_goal', 'Name of the car insurance goal', 'text', D.INSURANCE), S('behind_tol', 'A goal counts as behind when it is short by at least', 'money', 25),
    S('funded_share', 'Counts as funded at or above this share of the plan', 'pct', 0.95),
    S('due_soon_days', 'A goal due within this many days is due soon', 'int', 60)]

tables = []
# 1 goals
tables.append(T('goals', 'Goals', 'Savings Goals and Sinking Funds',
    'Every goal and sinking fund with target, date, monthly amount and saved so far; what is left, days left, the amount needed a month and per paycheck and the shortfall fill in.', [
    C('goal_id', 'Goal ID', 'text', 9, required=True), C('goal', 'Goal', 'text', 28), LST('kind', 'Kind', 'gkind', 13), REF('account', 'Account', 'accounts.account', 22), C('target', 'Target', 'money', 11),
    C('target_date', 'Target date', 'date', 12), C('monthly_amount', 'Monthly amount', 'money', 11), C('saved', 'Saved so far', 'money', 12), LST('priority', 'Priority', 'priority', 10),
    C('start_date', 'Start date', 'date', 12), C('transfer_day', 'Transfer day of month', 'int', 10),
    CA('account_id', 'Account ID', 'text', LKT('accounts.account_id', 'accounts.account', 'account'), 10),
    CA('left', 'Left to save', 'money', G('goal_id', 'IF({col:saved}>={col:target},0,{col:target}-{col:saved})'), 12),
    CA('days_left', 'Days left', 'int', G('goal_id', 'IF({col:target_date}="","",{col:target_date}-{today})'), 9),
    CA('months_left', 'Months left', 'num', G('goal_id', 'IF({col:days_left}="","",ROUND(MAX(0,{col:days_left})/30.4375,1))'), 9),
    CA('is_reached', 'Reached', 'int', G('goal_id', 'IF(AND({col:target}>0,{col:saved}>={col:target}),1,0)'), 9),
    CA('needed_month', 'Needed a month', 'money', G('goal_id', 'IF({col:left}=0,0,IF({col:months_left}="",{col:left},ROUND({col:left}/MAX(1,{col:months_left}),2)))'), 12),
    CA('per_paycheck', 'Set aside per paycheck', 'money', G('goal_id', 'ROUND({col:needed_month}*12/%s,2)' % PPY), 12),
    CA('behind_by', 'Behind by at the date', 'money', G('goal_id', 'IF({col:left}=0,0,IF({col:months_left}="",0,ROUND(MAX(0,{col:left}-{col:monthly_amount}*{col:months_left}),2)))'), 12),
    CA('is_behind', 'Behind plan', 'int', G('goal_id', 'IF({col:behind_by}>=MAX(0.01,{set:behind_tol}),1,0)'), 9),
    CA('status', 'Status', 'text', G('goal_id', 'IF({col:is_reached}=1,%s,IF(AND({col:days_left}<>"",{col:days_left}<0),%s,IF({col:is_behind}=1,%s,%s)))' % (
        tok('gstate', 'Reached'), tok('gstate', 'Past the date'), tok('gstate', 'Behind'), tok('gstate', 'On track'))), 13),
    CA('plan_so_far', 'Straight-line plan so far', 'money', G('goal_id', 'IF(OR({col:target_date}="",{col:start_date}=""),0,ROUND({col:target}*MIN(1,MAX(0,{today}-{col:start_date})/MAX(1,{col:target_date}-{col:start_date})),2))'), 13),
    CA('rank_key', 'Ranking key', 'num', G('goal_id', 'IF({col:is_reached}=1,50000,IF({col:is_behind}=1,0,20000)+IF({col:priority}=%s,0,IF({col:priority}=%s,5000,10000)))+IF({col:days_left}="",0,{col:days_left})+MATCH({col:goal_id},%s,0)/100' % (HIGH, MED, GL('goal_id'))), 13),
    CA('open_date', 'Open target date', 'date', G('goal_id', 'IF({col:is_reached}=1,"",{col:target_date})'), 12),
    CA('reach_date', 'Reached at this pace on', 'date', G('goal_id', 'IF(OR({col:is_reached}=1,{col:monthly_amount}<=0),"",{today}+ROUND(ROUNDUP({col:left}/{col:monthly_amount},0)*30.4375,0))'), 13),
    CA('reached_on', 'Reached on', 'date', G('goal_id', 'IF({col:is_reached}=1,IF(SUMPRODUCT(MAX((%s={col:goal})*(%s=%s)*(%s)))=0,"",SUMPRODUCT(MAX((%s={col:goal})*(%s=%s)*(%s)))),"")' % (
        CT('goal'), CT('kind'), DEP, CT('date'), CT('goal'), CT('kind'), DEP, CT('date'))), 12),
    CA('instalments', 'Instalments before the date', 'int', G('goal_id', 'IF({col:months_left}="",2,MAX(2,MIN(6,ROUNDUP({col:months_left},0))))'), 11),
    CA('review_date', 'Next goals review', 'date', 'EOMONTH({today},0)+1', 12),
    CA('total_behind', 'All goals behind by', 'money', 'SUMIFS(%s,%s,1)' % (GL('behind_by'), GL('is_behind')), 12), HH(), N1(), N2(),
    PHC('p1', 'Partner 1 phone'), PHC('p2', 'Partner 2 phone'), PHC('member', 'Household member phone'), PHC('gp', 'Grandparent phone'), PHC('ins', 'Insurance agent phone'), PHC('tax', 'Tax preparer phone'), PHC('bank', 'Bank branch phone')],
    D.goals_d(), 40, [A('status', '= ' + tok('gstate', 'Behind'), 'bad'), A('status', '= ' + tok('gstate', 'Reached'), 'good'), A('status', '= ' + tok('gstate', 'Past the date'), 'warn')]))
# 2 contributions
tables.append(T('contributions', 'Contributions', 'Contributions and Spends',
    'Money put into a goal (a deposit) and money spent from it; the month, the goal ID, a signed amount and the sinking fund balance effects fill in by themselves.', [
    C('contribution_id', 'Contribution ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), REF('goal', 'Goal', 'goals.goal', 26), LST('kind', 'Kind', 'ctkind', 10), C('amount', 'Amount', 'money', 11),
    REF('account', 'Goal account', 'accounts.account', 22), REF('from_account', 'From account', 'accounts.account', 22),
    CA('month', 'Month', 'date', 'IF({col:date}="","",DATE(YEAR({col:date}),MONTH({col:date}),1))', 11),
    CA('goal_id', 'Goal ID', 'text', G('contribution_id', LKT('goals.goal_id', 'goals.goal', 'goal')), 9),
    CA('gkind', 'Goal kind', 'text', G('contribution_id', LKT('goals.kind', 'goals.goal', 'goal')), 13),
    CA('signed', 'Signed amount', 'money', G('contribution_id', 'IF({col:kind}=%s,{col:amount},-{col:amount})' % DEP), 12),
    CA('spend_key', 'Spend key', 'num', G('contribution_id', 'IF({col:kind}=%s,{col:date}+MATCH({col:contribution_id},%s,0)/100000,"")' % (SPEND, CT('contribution_id'))), 12),
    HH(), N2(), PHC('p2', 'Partner 2 phone'), PHC('bank', 'Bank branch phone')],
    D.contributions_d(), 700, [A('kind', '= ' + SPEND, 'warn')]))
# 3 accounts
tables.append(T('accounts', 'Accounts', 'Accounts Holding Your Goals',
    'The accounts you hold money in and the goals each one carries; the number of goals and the amount saved for them fill in.', [
    C('account_id', 'Account ID', 'text', 9, required=True), C('account', 'Account', 'text', 26), LST('type', 'Type', 'atype', 13), LST('owner', 'Owner', 'person', 11), C('opening_balance', 'Opening balance', 'money', 13),
    C('balance_now', 'Balance now', 'money', 13),
    CA('goal_count', 'Goals held', 'int', G('account_id', 'COUNTIFS(%s,{col:account})' % GL('account')), 9),
    CA('goals_saved', 'Saved for goals', 'money', G('account_id', 'SUMIFS(%s,%s,{col:account})' % (GL('saved'), GL('account'))), 12),
    CA('today_date', 'Today', 'date', '{today}', 11), CA('year', 'Last year', 'text', '(YEAR({today})-1)&""', 9), HH(), PHC('bank', 'Bank branch phone')],
    D.accounts_d(), 30))
# 4 income
tables.append(T('income', 'Income', 'Income Received',
    'Take-home pay and other income received; the month fills in. Windfalls feed the Windfall to Goals tool and take-home feeds the retirement share.', [
    C('income_id', 'Income ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('person', 'Person', 'person', 11), LST('source', 'Source', 'isource', 12), C('net', 'Take-home amount', 'money', 13),
    C('gross', 'Gross amount', 'money', 13),
    CA('month', 'Month', 'date', 'IF({col:date}="","",DATE(YEAR({col:date}),MONTH({col:date}),1))', 11),
    CA('fund_first', 'Goal to fund first', 'text', G('income_id', 'IFERROR(INDEX(%s,1)&"","")' % R('goal_ranking', 'goal')), 26),
    CA('is_windfall', 'Windfall', 'int', G('income_id', 'IF({col:source}=%s,1,0)' % tok('isource', 'Windfall')), 9), HH(), N2(), PHC('p2', 'Partner 2 phone')],
    D.income_d(), 300))
# 5 bills
tables.append(T('bills', 'Bills', 'Bills',
    'The regular bills with amount, due day and cycle; the monthly cost and the yearly cost fill in, so yearly bills show their share of every month.', [
    C('bill_id', 'Bill ID', 'text', 9, required=True), C('bill', 'Bill', 'text', 28), LST('category', 'Category', 'category', 20), C('amount', 'Amount', 'money', 11), C('due_day', 'Due day', 'int', 9),
    LST('cycle', 'Cycle', 'cycle', 10), C('due_month', 'Due month (yearly bills)', 'int', 11),
    CA('monthly_cost', 'Monthly cost', 'money', G('bill_id', 'IF({col:cycle}=%s,ROUND({col:amount}/12,2),{col:amount})' % tok('cycle', 'Yearly')), 12),
    CA('yearly_cost', 'Yearly cost', 'money', G('bill_id', 'IF({col:cycle}=%s,{col:amount},{col:amount}*12)' % tok('cycle', 'Yearly')), 12)],
    D.bills_d(), 40))
# 6 transactions
tables.append(T('transactions', 'Transactions', 'Transactions',
    'Recent spending; a row paid from a goal carries the goal ID in From goal, which links it to the sinking fund spending list.', [
    C('tx_id', 'Transaction ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), C('payee', 'Payee', 'text', 22), REF('account_id', 'Account ID', 'accounts.account_id', 9), LST('category', 'Category', 'category', 20),
    C('amount', 'Amount', 'money', 11), C('from_goal', 'From goal ID', 'text', 10),
    CA('month', 'Month', 'date', 'IF({col:date}="","",DATE(YEAR({col:date}),MONTH({col:date}),1))', 11),
    CA('tx_key', 'Goal match key', 'text', G('tx_id', 'IF({col:from_goal}="","",{col:date}&"|"&{col:from_goal})'), 14)],
    D.tx_d(), 1200))
# 7 retirement
tables.append(T('retirement', 'Retirement', 'Retirement Contributions',
    'Amounts put into a tax-advantaged retirement or other long-term account: yours and the employer amount you type; total and share of take-home fill in. Never advice.', [
    C('rt_id', 'Row ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('person', 'Person', 'person', 11), LST('source', 'Source', 'rtsource', 10), REF('account', 'Account', 'accounts.account', 30),
    C('employee_amount', 'Your amount', 'money', 11), C('employer_amount', 'Employer amount typed', 'money', 12),
    CA('month', 'Month', 'date', 'IF({col:date}="","",DATE(YEAR({col:date}),MONTH({col:date}),1))', 11),
    CA('total', 'Total', 'money', G('rt_id', '{col:employee_amount}+{col:employer_amount}'), 11),
    CA('pay_base', 'Take-home it is measured against', 'money', G('rt_id', 'IF({col:person}=%s,SUMIFS(%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1)),IF({col:source}=%s,SUMIFS(%s,%s,{col:person},%s,{col:date}),SUMIFS(%s,%s,{col:person},%s,">="&{col:month},%s,"<"&EDATE({col:month},1))))' % (
        JOINT, IC('net'), IC('date'), IC('date'), PAYROLL, IC('net'), IC('person'), IC('date'), IC('net'), IC('person'), IC('date'), IC('date'))), 13),
    CA('share', 'Share of take-home', 'pct', G('rt_id', 'IF({col:pay_base}>0,ROUND({col:employee_amount}/{col:pay_base},4),0)'), 11),
    CA('change_from', 'Change takes effect from', 'date', 'EOMONTH({today},0)+1', 12), HH(), N1(), PHC('p1', 'Partner 1 phone'), PHC('payroll', 'Payroll office phone')],
    D.retirement_d(), 300))
# 8 goal ranking
def GRK(c): return 'IF({col:rkey}="","",INDEX(%s,MATCH({col:rkey},%s,0)))' % (GL(c), GL('rank_key'))
def GRT(c): return 'IF({col:rkey}="","",INDEX(%s,MATCH({col:rkey},%s,0))&"")' % (GL(c), GL('rank_key'))
tables.append(T('goal_ranking', 'Ranking of goals', 'Goal Ranking, Fund This First',
    'Goals ranked: behind goals first, then by priority and days left, reached goals last; it fills in from the Goals sheet.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('rkey', 'Ranking key', 'num', 'IFERROR(SMALL(%s,{col:rank}),"")' % GL('rank_key'), 13),
    CA('goal_id', 'Goal ID', 'text', GRT('goal_id'), 9), CA('goal', 'Goal', 'text', GRT('goal'), 28), CA('priority', 'Priority', 'text', GRT('priority'), 10),
    CA('days_left', 'Days left', 'int', GRK('days_left'), 9), CA('left', 'Left to save', 'money', GRK('left'), 12), CA('behind_by', 'Behind by at the date', 'money', GRK('behind_by'), 12),
    CA('per_paycheck', 'Set aside per paycheck', 'money', GRK('per_paycheck'), 12), CA('status', 'Status', 'text', GRT('status'), 13), HH(), N2()],
    D.rank_d(12), 40, [A('status', '= ' + tok('gstate', 'Behind'), 'bad'), A('status', '= ' + tok('gstate', 'Reached'), 'good')]))
# 9 goal funding
tables.append(T('goal_funding', 'Goal funding', 'Goal Funding per Month, Week and Paycheck',
    'Each goal broken down for your pay rhythm: the planned monthly amount and what is needed, per month, per week and per paycheck; the gap per paycheck fills in.', [
    REF('goal', 'Goal', 'goals.goal', 28, required=True),
    CA('monthly', 'Planned a month', 'money', G('goal', 'IFERROR(%s,0)' % GLK('monthly_amount')), 12), CA('needed_month', 'Needed a month', 'money', G('goal', 'IFERROR(%s,0)' % GLK('needed_month')), 12),
    CA('per_week', 'Planned a week', 'money', G('goal', 'ROUND({col:monthly}*12/52,2)'), 11),
    CA('plan_paycheck', 'Planned per paycheck', 'money', G('goal', 'ROUND({col:monthly}*12/%s,2)' % PPY), 12), CA('need_paycheck', 'Needed per paycheck', 'money', G('goal', 'ROUND({col:needed_month}*12/%s,2)' % PPY), 12),
    CA('gap_paycheck', 'Extra needed per paycheck', 'money', G('goal', 'MAX(0,{col:need_paycheck}-{col:plan_paycheck})'), 12),
    CA('rhythm', 'Pay rhythm', 'text', G('goal', '{set:pay_freq}'), 15), HH(), N2()],
    D.goal_names_d(), 40))
# 10 contributions by month
def CMW(kind): return 'SUMIFS(%s,%s,%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1))' % (CT('amount'), CT('kind'), kind, CT('date'), CT('date'))
tables.append(T('contrib_months', 'Deposits by month', 'Deposits and Spends by Month',
    'Month by month: deposits, spends, net saved and the planned deposits of the goals active that month, with the sinking fund balance; the current month is to date.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('deposits', 'Deposits', 'money', G('month', CMW(DEP)), 12), CA('spends', 'Spends', 'money', G('month', CMW(SPEND)), 12), CA('net', 'Net saved', 'money', G('month', '{col:deposits}-{col:spends}'), 12),
    CA('planned', 'Planned deposits', 'money', G('month', 'SUMIFS(%s,%s,"<"&EDATE({col:month},1),%s,">="&{col:month})' % (GL('monthly_amount'), GL('start_date'), GL('target_date'))), 13),
    CA('diff', 'Deposits against plan', 'money', G('month', '{col:deposits}-{col:planned}'), 13),
    CA('sink_balance', 'Sinking fund balance at month end', 'money', G('month', 'SUMIFS(%s,%s,%s)-SUMIFS(%s,%s,%s,%s,">"&EOMONTH({col:month},0))' % (GL('saved'), GL('kind'), SINK, CT('signed'), CT('gkind'), SINK, CT('date'))), 14),
    CA('last12', 'In the last 12 complete months', 'int', G('month', 'IF(AND({col:month}>=EDATE(%s,-12),{col:month}<%s),1,0)' % (MS, MS)), 10),
    CA('funded', 'Funding', 'text', G('month', 'IF({col:planned}=0,%s,IF({col:deposits}>={col:planned}*{set:funded_share},%s,%s))' % (tok('funded', 'Funded'), tok('funded', 'Funded'), tok('funded', 'Under-funded'))), 12), HH(), N2(), PHC('p2', 'Partner 2 phone')],
    D.months_d(25), 40, [A('funded', '= ' + tok('funded', 'Under-funded'), 'warn')]))
# 11 contributions by goal
def ACT(back):
    return 'IF(OR({col:startm}="",{col:endm}=""),0,MAX(0,(YEAR(MIN(%s,{col:endm}))-YEAR(MAX({col:startm},EDATE(%s,-%d))))*12+MONTH(MIN(%s,{col:endm}))-MONTH(MAX({col:startm},EDATE(%s,-%d)))))' % (MS, MS, back, MS, MS, back)
def CGW(kind, a, b): return 'SUMIFS(%s,%s,{col:goal},%s,%s,%s,">="&EDATE(%s,%d),%s,"<"&%s)' % (CT('amount'), CT('goal'), CT('kind'), kind, CT('date'), MS, a, CT('date'), MS)
tables.append(T('contrib_goals', 'Deposits by goal', 'Deposits and Spends by Goal',
    'For each goal over the last 12 and the last 3 complete months: deposits, spends and the planned amount, with the difference and whether the goal is funded.', [
    REF('goal', 'Goal', 'goals.goal', 28, required=True),
    CA('goal_id', 'Goal ID', 'text', G('goal', 'IFERROR(%s&"","")' % GLK('goal_id')), 9), CA('monthly', 'Monthly amount', 'money', G('goal', 'IFERROR(%s,0)' % GLK('monthly_amount')), 11),
    CA('saved', 'Saved so far', 'money', G('goal', 'IFERROR(%s,0)' % GLK('saved')), 11), CA('target', 'Target', 'money', G('goal', 'IFERROR(%s,0)' % GLK('target')), 11),
    CA('left', 'Left to save', 'money', G('goal', 'IFERROR(%s,0)' % GLK('left')), 11), CA('days_left', 'Days left', 'int', G('goal', 'IFERROR(%s,0)' % GLK('days_left')), 9),
    CA('reached', 'Reached', 'int', G('goal', 'IFERROR(%s,0)' % GLK('is_reached')), 9),
    CA('startm', 'Plan starts', 'date', G('goal', 'IFERROR(DATE(YEAR(%s),MONTH(%s),1),"")' % (GLK('start_date'), GLK('start_date'))), 11),
    CA('endm', 'Plan ends', 'date', G('goal', 'IFERROR(EDATE(DATE(YEAR(%s),MONTH(%s),1),1),"")' % (GLK('target_date'), GLK('target_date'))), 11),
    CA('act12', 'Months planned, last 12', 'int', G('goal', ACT(12)), 10), CA('act3', 'Months planned, last 3', 'int', G('goal', ACT(3)), 10),
    CA('dep12', 'Deposits, last 12 months', 'money', G('goal', CGW(DEP, -12, 0)), 13), CA('spend12', 'Spends, last 12 months', 'money', G('goal', CGW(SPEND, -12, 0)), 13),
    CA('planned12', 'Planned, last 12 months', 'money', G('goal', 'IF({col:reached}=1,{col:dep12},ROUND({col:monthly}*{col:act12},2))'), 13), CA('diff12', 'Deposits against plan', 'money', G('goal', '{col:dep12}-{col:planned12}'), 13),
    CA('dep3', 'Deposits, last 3 months', 'money', G('goal', CGW(DEP, -3, 0)), 12), CA('planned3', 'Planned, last 3 months', 'money', G('goal', 'IF({col:reached}=1,{col:dep3},ROUND({col:monthly}*{col:act3},2))'), 12),
    CA('short3', 'Under-funded by, last 3 months', 'money', G('goal', 'MAX(0,{col:planned3}-{col:dep3})'), 13),
    CA('share3', 'Share of plan funded, last 3 months', 'pct', G('goal', 'IF({col:planned3}>0,ROUND({col:dep3}/{col:planned3},4),1)'), 12),
    CA('last_dep', 'Deposit last month', 'int', G('goal', 'IF(COUNTIFS(%s,{col:goal},%s,%s,%s,">="&EDATE(%s,-1),%s,"<"&%s)>0,1,0)' % (CT('goal'), CT('kind'), DEP, CT('date'), MS, CT('date'), MS)), 10),
    CA('funded', 'Funding', 'text', G('goal', 'IF({col:share3}>={set:funded_share},%s,%s)' % (tok('funded', 'Funded'), tok('funded', 'Under-funded'))), 12), HH(), N2()],
    D.goal_names_d(), 40, [A('funded', '= ' + tok('funded', 'Under-funded'), 'warn')]))
# 12 sinking fund spending
def SSP(c): return 'IF({col:skey}="","",INDEX(%s,MATCH({col:skey},%s,0)))' % (CT(c), CT('spend_key'))
tables.append(T('sinking_spend', 'Sinking fund spending', 'Spending from Goals and Sinking Funds',
    'The latest spends from goals, newest first, with what was bought and the fund balance after each spend; it fills in from Contributions and Transactions.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('skey', 'Spend key', 'num', 'IFERROR(LARGE(%s,{col:rank}),"")' % CT('spend_key'), 11),
    CA('date', 'Date', 'date', SSP('date'), 11), CA('goal', 'Goal', 'text', 'IF({col:skey}="","",INDEX(%s,MATCH({col:skey},%s,0))&"")' % (CT('goal'), CT('spend_key')), 28), CA('amount', 'Amount', 'money', SSP('amount'), 11),
    CA('goal_id', 'Goal ID', 'text', 'IF({col:skey}="","",IFERROR(INDEX(%s,MATCH({col:goal},%s,0))&"",""))' % (GL('goal_id'), GL('goal')), 9),
    CA('payee', 'Bought from', 'text', 'IF({col:skey}="","",IFERROR(INDEX(%s,MATCH({col:date}&"|"&{col:goal_id},%s,0))&"",%s))' % (TXR('payee'), TXR('tx_key'), lit('Not listed')), 22),
    CA('balance_after', 'Fund balance after', 'money', 'IF({col:skey}="","",ROUND(SUMIFS(%s,%s,{col:goal})-SUMIFS(%s,%s,{col:goal},%s,">"&{col:date}),2))' % (GL('saved'), GL('goal'), CT('signed'), CT('goal'), CT('date')), 13),
    CA('days_ago', 'Days ago', 'int', 'IF({col:skey}="","",{today}-{col:date})', 9), HH(), PHC('member', 'Household member phone')],
    D.rank_d(25), 40))
# 13 annual costs
tables.append(T('annual_costs', 'Annual costs', 'Annual Costs to Monthly and per Paycheck',
    'The costs that come once a year with the month each falls due; the amount per month and per paycheck, the next due date and the shortfall of its fund fill in.', [
    C('item_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 28), LST('category', 'Category', 'acat', 19), C('amount', 'Amount', 'money', 11), C('due_month', 'Due month', 'int', 9), C('due_day', 'Due day', 'int', 8),
    REF('goal', 'Fund (goal)', 'goals.goal', 26),
    CA('per_month', 'Set aside a month', 'money', G('item_id', 'ROUND({col:amount}/12,2)'), 12), CA('per_paycheck', 'Set aside per paycheck', 'money', G('item_id', 'ROUND({col:amount}/%s,2)' % PPY), 12),
    CA('next_due', 'Next due date', 'date', G('item_id', 'IF(OR({col:due_month}="",{col:due_day}=""),"",IF(DATE(YEAR({today}),{col:due_month},{col:due_day})<{today},DATE(YEAR({today})+1,{col:due_month},{col:due_day}),DATE(YEAR({today}),{col:due_month},{col:due_day})))'), 12),
    CA('days_to_due', 'Days to due', 'int', G('item_id', 'IF({col:next_due}="","",{col:next_due}-{today})'), 9), CA('months_to_due', 'Months to due', 'num', G('item_id', 'IF({col:days_to_due}="","",ROUND({col:days_to_due}/30.4375,1))'), 9),
    CA('fund_saved', 'Saved in its fund', 'money', G('item_id', 'IF({col:goal}="",0,IFERROR(INDEX(%s,MATCH({col:goal},%s,0)),0))' % (GL('saved'), GL('goal'))), 12),
    CA('plan_month', 'Fund monthly amount', 'money', G('item_id', 'IF({col:goal}="",0,IFERROR(INDEX(%s,MATCH({col:goal},%s,0)),0))' % (GL('monthly_amount'), GL('goal'))), 12),
    CA('short_at_due', 'Short at the due date', 'money', G('item_id', 'IF({col:months_to_due}="",{col:amount},ROUND(MAX(0,{col:amount}-{col:fund_saved}-{col:plan_month}*{col:months_to_due}),2))'), 12),
    CA('add_month', 'Add a month to close the gap', 'money', G('item_id', 'IF({col:short_at_due}=0,0,ROUND({col:short_at_due}/IF({col:months_to_due}="",1,MAX(1,{col:months_to_due})),2))'), 13),
    CA('state', 'Fund status', 'text', G('item_id', 'IF({col:goal}="",%s,IF({col:short_at_due}=0,%s,%s))' % (tok('fstate', 'No fund set up'), tok('fstate', 'Covered'), tok('fstate', 'Short'))), 13),
    HH(), PHC('member', 'Household member phone'), PHC('mech', 'Car mechanic phone'), PHC('school', 'School office phone'), PHC('child', 'Childcare provider phone')],
    D.annual_d(), 40, [A('state', '= ' + tok('fstate', 'Short'), 'bad'), A('state', '= ' + tok('fstate', 'No fund set up'), 'warn'), A('state', '= ' + tok('fstate', 'Covered'), 'good')]))
# 14 annual costs by month
def ACW(c): return 'SUMIFS(%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1))' % (AC(c), AC('next_due'), AC('next_due'))
tables.append(T('annual_months', 'Annual costs by month', 'Annual Costs Calendar, Next 12 Months',
    'The next 12 months: the yearly costs falling due, what their funds hold by then and the gap; it fills in from the Annual costs sheet.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('costs_due', 'Costs due', 'money', G('month', ACW('amount')), 12), CA('items', 'Costs falling due', 'int', G('month', 'COUNTIFS(%s,">="&{col:month},%s,"<"&EDATE({col:month},1))' % (AC('next_due'), AC('next_due'))), 10),
    CA('gap', 'Short at the due dates', 'money', G('month', ACW('short_at_due')), 13), CA('covered', 'Covered by the funds', 'money', G('month', '{col:costs_due}-{col:gap}'), 13),
    CA('state', 'Status', 'text', G('month', 'IF({col:gap}>0,%s,%s)' % (tok('fstate', 'Short'), tok('fstate', 'Covered'))), 10),
    CA('short_key', 'Short month', 'date', G('month', 'IF({col:gap}>0,{col:month},"")'), 11),
    CA('months_out', 'Months from now', 'int', G('month', '(YEAR({col:month})-YEAR(%s))*12+MONTH({col:month})-MONTH(%s)' % (MS, MS)), 9), HH(), PHC('member', 'Household member phone')],
    D.months_ahead_d(), 24, [A('state', '= ' + tok('fstate', 'Short'), 'bad'), A('state', '= ' + tok('fstate', 'Covered'), 'good')]))
# 15 essential spending
tables.append(T('essential_months', 'Essential spending', 'Essential Spending by Month',
    'One row a month of fixed bills, variable needs and debt payments (paste totals from your own records); the essential total and the average of the months before fill in. The current month is to date.', [
    C('month', 'Month', 'date', 11, required=True), C('fixed', 'Fixed bills', 'money', 12), C('variable', 'Variable needs', 'money', 12), C('debt', 'Debt payments', 'money', 12),
    CA('essential', 'Essential total', 'money', G('month', '{col:fixed}+{col:variable}+{col:debt}'), 12),
    CA('avg_before', 'Average of the months before', 'money', G('month', 'IFERROR(AVERAGEIFS(%s,%s,">="&EDATE({col:month},-{set:essential_months}),%s,"<"&{col:month}),{col:essential})' % (ES('essential'), ES('month'), ES('month'))), 14),
    CA('last12', 'In the last 12 complete months', 'int', G('month', 'IF(AND({col:month}>=EDATE(%s,-12),{col:month}<%s),1,0)' % (MS, MS)), 10)],
    D.essential_d(), 40))
# 16 emergency fund by month
tables.append(T('emergency_months', 'Emergency fund by month', 'Emergency Fund in Months, Month by Month',
    'The emergency fund at each month end against essential spending: months covered, the typical range (check your own numbers) and the gap; it fills in by itself.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('essential', 'Essential spending a month', 'money', G('month', LKN('essential_months.avg_before', 'essential_months.month', 'month')), 13),
    CA('balance', 'Emergency fund balance', 'money', G('month', 'ROUND(%s-SUMIFS(%s,%s,%s,%s,">"&EOMONTH({col:month},0)),2)' % (EBAL, CT('signed'), CT('gkind'), EMERG, CT('date'))), 13),
    CA('months_covered', 'Months covered', 'num', G('month', 'IF({col:essential}>0,ROUND({col:balance}/{col:essential},2),0)'), 10), CA('target_months', 'Target months, low end', 'int', G('month', '{set:emergency_low}'), 10),
    CA('target_amount', 'Target amount, low end', 'money', G('month', 'ROUND({col:target_months}*{col:essential},0)'), 12), CA('gap', 'Gap to the target', 'money', G('month', 'MAX(0,{col:target_amount}-{col:balance})'), 12),
    CA('range', 'Against the typical range', 'text', G('month', 'IF({col:months_covered}<{set:emergency_low},%s,IF({col:months_covered}<={set:emergency_high},%s,%s))' % (tok('estate', 'Below the typical range'), tok('estate', 'Within the typical range'), tok('estate', 'Above the typical range'))), 20),
    HH(), N2(), PHC('p2', 'Partner 2 phone'), PHC('member', 'Household member phone')],
    D.months_d(25), 40, [A('range', '= ' + tok('estate', 'Below the typical range'), 'warn'), A('range', '= ' + tok('estate', 'Within the typical range'), 'good')]))
# 17 emergency fund plan
tables.append(T('emergency_plan', 'Emergency fund plan', 'Emergency Fund Plan, 1 to 12 Months',
    'Targets for 1 to 12 months of essential spending, what is saved, the gap and the months to reach each at the monthly amount; the typical range is from Settings.', [
    C('months', 'Months of cover', 'int', 9, required=True),
    CA('essential', 'Essential spending a month', 'money', G('months', EAVG), 13), CA('target_amount', 'Target amount', 'money', G('months', 'ROUND({col:months}*{col:essential},0)'), 12),
    CA('saved', 'Saved', 'money', G('months', EBAL), 11), CA('gap', 'Gap', 'money', G('months', 'MAX(0,{col:target_amount}-{col:saved})'), 11),
    CA('monthly', 'Monthly amount into the fund', 'money', G('months', 'SUMIFS(%s,%s,%s)' % (GL('monthly_amount'), GL('kind'), EMERG)), 13),
    CA('months_to_reach', 'Months to reach', 'int', G('months', 'IF({col:gap}=0,0,IF({col:monthly}<=0,"",ROUNDUP({col:gap}/{col:monthly},0)))'), 10),
    CA('reach_date', 'Reached at this pace on', 'date', G('months', 'IF({col:months_to_reach}="","",{today}+ROUND({col:months_to_reach}*30.4375,0))'), 13),
    CA('months_now', 'Months covered now', 'num', G('months', 'IF({col:essential}>0,ROUND({col:saved}/{col:essential},1),0)'), 10),
    CA('position', 'Position in the typical range', 'text', G('months', 'IF({col:months}={set:emergency_low},%s,IF({col:months}={set:emergency_high},%s,IF({col:months}<{set:emergency_low},%s,IF({col:months}>{set:emergency_high},%s,%s))))' % (
        tok('rlabel', 'Low end of the typical range'), tok('rlabel', 'High end of the typical range'), tok('rlabel', 'Short of the range'), tok('rlabel', 'Beyond the range'), tok('rlabel', 'In between'))), 24),
    HH(), N2(), PHC('p2', 'Partner 2 phone'), PHC('member', 'Household member phone')],
    D.plan_d(), 24))
# 18 retirement by month
def RTW(c): return 'SUMIFS(%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1))' % (RT(c), RT('date'), RT('date'))
tables.append(T('retirement_months', 'Retirement by month', 'Retirement Contributions by Month',
    'Month by month: your amount, the employer amount typed, the total and your share of take-home pay against the typical range in Settings (check your own numbers).', [
    C('month', 'Month', 'date', 11, required=True),
    CA('employee', 'Your amount', 'money', G('month', RTW('employee_amount')), 11), CA('employer', 'Employer amount', 'money', G('month', RTW('employer_amount')), 12), CA('total', 'Total', 'money', G('month', '{col:employee}+{col:employer}'), 11),
    CA('take_home', 'Take-home pay', 'money', G('month', 'SUMIFS(%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1))' % (IC('net'), IC('date'), IC('date'))), 12),
    CA('share', 'Share of take-home', 'pct', G('month', 'IF({col:take_home}>0,ROUND({col:employee}/{col:take_home},4),0)'), 11),
    CA('at_min', 'At or above the low end of the range', 'int', G('month', 'IF({col:share}>={set:retirement_min},1,0)'), 11),
    CA('last12', 'In the last 12 complete months', 'int', G('month', 'IF(AND({col:month}>=EDATE(%s,-12),{col:month}<%s),1,0)' % (MS, MS)), 10), HH(), N1(), PHC('p1', 'Partner 1 phone')],
    D.months_d(25), 40))
# 19 retirement summary
WF = 'IF({col:window}=%s,DATE(YEAR({today}),1,1),IF({col:window}=%s,EDATE(%s,-12),IF({col:window}=%s,EDATE(%s,-24),MIN(%s))))' % (
    tok('rwindow', 'Year to date'), tok('rwindow', 'Last 12 months'), MS, tok('rwindow', 'Previous 12 months'), MS, RT('date'))
WT = 'IF({col:window}=%s,{today}+1,IF({col:window}=%s,%s,IF({col:window}=%s,EDATE(%s,-12),{today}+1)))' % (tok('rwindow', 'Year to date'), tok('rwindow', 'Last 12 months'), MS, tok('rwindow', 'Previous 12 months'), MS)
def RSW(c): return 'SUMIFS(%s,%s,{col:account},%s,">="&{col:w_from},%s,"<"&{col:w_to})' % (RT(c), RT('account'), RT('date'), RT('date'))
OWN = 'IFERROR(INDEX(%s,MATCH({col:account},%s,0)),"")' % (R('accounts', 'owner'), R('accounts', 'account'))
tables.append(T('retirement_summary', 'Retirement summary', 'Retirement Summary by Account and Period',
    'Each retirement or long-term account over four periods: your amount, the employer amount, the total, the share of take-home and the yearly total at that pace.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('window', 'Period', 'rwindow', 17), REF('account', 'Account', 'accounts.account', 30),
    CA('w_from', 'From', 'date', G('row_id', WF), 11), CA('w_to', 'Up to', 'date', G('row_id', WT), 11),
    CA('employee', 'Your amount', 'money', G('row_id', RSW('employee_amount')), 11), CA('employer', 'Employer amount', 'money', G('row_id', RSW('employer_amount')), 12), CA('total', 'Total', 'money', G('row_id', '{col:employee}+{col:employer}'), 11),
    CA('take_home', 'Take-home in the period', 'money', G('row_id', 'IF(%s=%s,SUMIFS(%s,%s,">="&{col:w_from},%s,"<"&{col:w_to}),SUMIFS(%s,%s,%s,%s,">="&{col:w_from},%s,"<"&{col:w_to}))' % (
        OWN, JOINT, IC('net'), IC('date'), IC('date'), IC('net'), IC('person'), OWN, IC('date'), IC('date'))), 13),
    CA('share', 'Share of take-home', 'pct', G('row_id', 'IF({col:take_home}>0,ROUND({col:employee}/{col:take_home},4),0)'), 11),
    CA('yearly', 'Yearly total at this pace', 'money', G('row_id', 'IF({col:w_to}>{col:w_from},ROUND({col:total}/({col:w_to}-{col:w_from})*365,2),0)'), 13), HH(), PHC('tax', 'Tax preparer phone')],
    D.summary_d(), 24))
# 20 goal changes
tables.append(T('goal_changes', 'Goal changes', 'Goal Changes Log',
    'Each time a monthly amount changed and why; the change a month and over a year fill in, so the plan keeps its history.', [
    C('change_id', 'Change ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('goal', 'Goal', 'goals.goal', 28), C('old_monthly', 'Old monthly amount', 'money', 12), C('new_monthly', 'New monthly amount', 'money', 12),
    LST('reason', 'Reason', 'reason', 16),
    CA('change', 'Change a month', 'money', G('change_id', '{col:new_monthly}-{col:old_monthly}'), 12), CA('change_year', 'Change over a year', 'money', G('change_id', '({col:new_monthly}-{col:old_monthly})*12'), 12),
    CA('month', 'Month', 'date', 'IF({col:date}="","",DATE(YEAR({col:date}),MONTH({col:date}),1))', 11)],
    D.changes_d(), 40))
assert len(tables) == 20, len(tables)
