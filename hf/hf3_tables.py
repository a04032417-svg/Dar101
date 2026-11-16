"""Household Finance suite part 3: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf3_lists import *
import hf3_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
DAYN = 'DAY({today})'
DIM = 'DAY(EOMONTH({today},0))'
YES = '{list:yesno.yes}'
G_FIX, G_VAR, G_WANT, G_SAV, G_DEBT = grp('Fixed bills'), grp('Variable needs'), grp('Wants'), grp('Savings'), grp('Debt payments')
DEP = tok('ctkind', 'Deposit')
C_RET, C_GRO, C_EAT, C_FUEL, C_SHOP, C_KIDS, C_OTHER = cat('Retirement'), cat('Groceries'), cat('Eating out'), cat('Fuel and transport'), cat('Shopping'), cat('Kids and family'), cat('Other')


def _sub(t, **kw):
    for k, v in kw.items(): t = t.replace('<%s>' % k, v)
    return t


def ACTM(c, m):
    """what the household did in a category and month: spending (not from a goal) + savings deposits + retirement paid through payroll"""
    return _sub('(SUMIFS(<a>,<c>,<X>,<m>,<M>,<g>,"")+SUMIFS(<ca>,<cc>,<X>,<cm>,<M>,<ck>,<DEP>)+IF(<X>=<RET>,SUMIFS(<ir>,<im>,<M>),0))'.replace('<X>', c).replace('<M>', m).replace('<DEP>', DEP).replace('<RET>', C_RET),
        a=R('transactions', 'amount'), c=R('transactions', 'category'), m=R('transactions', 'month'), g=R('transactions', 'from_goal'),
        ca=R('contributions', 'amount'), cc=R('contributions', 'category'), cm=R('contributions', 'month'), ck=R('contributions', 'kind'), ir=R('income', 'retirement'), im=R('income', 'month'))


def ACTW(c, d0, d1):
    """the same over a date window (both ends included)"""
    return _sub('(SUMIFS(<a>,<c>,<X>,<d>,">="&<D0>,<d>,"<="&<D1>,<g>,"")+SUMIFS(<ca>,<cc>,<X>,<cd>,">="&<D0>,<cd>,"<="&<D1>,<ck>,<DEP>)+IF(<X>=<RET>,SUMIFS(<ir>,<id>,">="&<D0>,<id>,"<="&<D1>),0))'.replace('<X>', c).replace('<D0>', d0).replace('<D1>', d1).replace('<DEP>', DEP).replace('<RET>', C_RET),
        a=R('transactions', 'amount'), c=R('transactions', 'category'), d=R('transactions', 'date'), g=R('transactions', 'from_goal'),
        ca=R('contributions', 'amount'), cc=R('contributions', 'category'), cd=R('contributions', 'date'), ck=R('contributions', 'kind'), ir=R('income', 'retirement'), id=R('income', 'date'))


def WINDOWS(k):
    """first and last day of the same days of the month, k months back (this month to date when k=0)"""
    return 'EDATE(%s,-%d)' % (MS, k), 'EDATE({today},-%d)' % k


def PERIOD_FROM(p):
    return ('IF(%s=%s,%s,IF(%s=%s,EDATE(%s,-1),IF(%s=%s,EDATE(%s,-3),IF(%s=%s,EDATE(%s,-12),IF(%s=%s,DATE(YEAR({today}),1,1),DATE(YEAR({today})-1,1,1))))))' % (
        p, per('This month'), MS, p, per('Last month'), MS, p, per('Last 3 months'), MS, p, per('Last 12 months'), MS, p, per('This year')))


def PERIOD_TO(p):
    return ('IF(OR(%s=%s,%s=%s),{today},IF(%s=%s,DATE(YEAR({today})-1,12,31),%s-1))' % (p, per('This month'), p, per('This year'), p, per('Last year'), MS))


def WDNO(sd):
    return 'IF(%s={list:wday.monday},1,IF(%s={list:wday.tuesday},2,IF(%s={list:wday.wednesday},3,IF(%s={list:wday.thursday},4,IF(%s={list:wday.friday},5,IF(%s={list:wday.saturday},6,7))))))' % ((sd,) * 6)


TEAM = {t['role']: t for t in team}
PHONE = {'p1': TEAM['Partner 1']['phone'], 'p2': TEAM['Partner 2']['phone'], 'member': TEAM['Grandparent']['phone'], 'noa': [t for t in team if t['member_id'] == 'HF-03'][0]['phone'],
         'ike': [t for t in team if t['member_id'] == 'HF-04'][0]['phone'], 'bank': TEAM['Bank branch']['phone'], 'school': TEAM['School office']['phone'], 'mech': TEAM['Car mechanic']['phone'],
         'util': TEAM['Utility company']['phone'], 'ins': TEAM['Insurance agent']['phone'], 'tax': TEAM['Tax preparer']['phone']}
def HH(): return CA('household', 'Household', 'text', '{set:household}', 22)
def N1(): return CA('partner1', 'Partner 1 name', 'text', '{set:partner1}', 14)
def N2(): return CA('partner2', 'Partner 2 name', 'text', '{set:partner2}', 14)
def PH(who, label): return CA(who + '_phone', label, 'text', '"%s"' % PHONE[who], 18)

settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('partner1', 'Partner 1 name, shown in messages', 'text', 'Partner 1'), S('partner2', 'Partner 2 name, shown in messages', 'text', 'Partner 2'),
    S('needs_share', 'Needs share, the 50/30/20 rule of thumb', 'pct', NEEDS_SHARE), S('wants_share', 'Wants share, a typical range, check your own numbers', 'pct', WANTS_SHARE),
    S('savings_share', 'Savings share, a popular rule of thumb', 'pct', SAVINGS_SHARE), S('savings_rate_target', 'Savings rate you want, your own number', 'pct', SAVINGS_RATE_TARGET),
    S('plan_trend', 'Trend added when you reset a plan from the last 3 months', 'pct', 0.03), S('pace_tol', 'Within this share of the plan counts as on pace', 'pct', 0.05),
    S('large_payment', 'A payment of this amount or more is a large payment', 'money', 400), S('dup_days', 'Days apart for a possible duplicate payment', 'int', 2),
    S('dup_min', 'Smallest payment checked for duplicates', 'money', 20), S('leak_max', 'A payment up to this amount counts as a small payment', 'money', 25),
    S('leak_times', 'Small payments in 90 days that make a small leak', 'int', 3), S('allowance_noa', 'Weekly allowance of the older child', 'money', 10), S('allowance_ike', 'Weekly allowance of the younger child', 'money', 5),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 transactions --------------------------------------------------------------
tables.append(T('transactions', 'Transactions', 'Transaction Log',
    'Every payment out, one row each: type or paste date, payee, category, amount and who paid; the month, group, week and the flag for a possible duplicate fill in by themselves.', [
    C('tx_id', 'Transaction ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    C('account_id', 'Account ID', 'text', 9), LST('account', 'Account', 'spendacct', 20), C('payee', 'Payee', 'text', 24), LST('category', 'Category', 'category', 20),
    CA('group', 'Group', 'text', LKT('categories.group', 'categories.category', 'category'), 14), C('amount', 'Amount', 'money', 11), LST('paid_by', 'Paid by', 'payer', 11),
    C('from_goal', 'From goal', 'text', 9), CA('week_start', 'Week start', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 11),
    CA('weekday', 'Weekday', 'text', 'CHOOSE(WEEKDAY({col:date},2),{list:wday.monday},{list:wday.tuesday},{list:wday.wednesday},{list:wday.thursday},{list:wday.friday},{list:wday.saturday},{list:wday.sunday})', 11),
    CA('counted', 'Counted spending', 'money', 'IF(AND({col:from_goal}="",{col:group}<>%s,{col:group}<>%s),{col:amount},0)' % (G_DEBT, G_SAV), 12),
    CA('var_day', 'First variable payment of its day', 'int',
       'IF(AND({col:from_goal}="",OR({col:group}=%s,{col:group}=%s)),IF(COUNTIFS(%s,{col:date},%s,%s,%s,"",%s,"<"&{col:tx_id})+COUNTIFS(%s,{col:date},%s,%s,%s,"",%s,"<"&{col:tx_id})=0,1,0),0)' % (
           G_VAR, G_WANT, R('transactions', 'date'), R('transactions', 'group'), G_VAR, R('transactions', 'from_goal'), R('transactions', 'tx_id'),
           R('transactions', 'date'), R('transactions', 'group'), G_WANT, R('transactions', 'from_goal'), R('transactions', 'tx_id')), 11),
    CA('dup_date', 'Possible duplicate on', 'date', 'IF(AND({col:amount}>={set:dup_min},COUNTIFS(%s,{col:payee},%s,{col:amount},%s,">="&({col:date}-{set:dup_days}),%s,"<="&({col:date}+{set:dup_days}))>1),{col:date},"")' % (
        R('transactions', 'payee'), R('transactions', 'amount'), R('transactions', 'date'), R('transactions', 'date')), 12)],
    D.tx_d(), 2500, [A('dup_date', '> 0', 'warn'), A('amount', '>= {set:large_payment}', 'warn'), A('category', '= ' + C_OTHER, 'warn')]))
# 2 categories ----------------------------------------------------------------
_SEAS = 'SUMIFS(%s,%s,{col:category},%s,">="&DATE(YEAR({today})-1,11,1),%s,"<"&DATE(YEAR({today}),1,1))' % (R('transactions', 'amount'), R('transactions', 'category'), R('transactions', 'date'), R('transactions', 'date'))
_NM = 'IF(MOD(11-MONTH({today}),12)=0,12,MOD(11-MONTH({today}),12))'
tables.append(T('categories', 'Categories', 'Categories and Groups',
    'The 28 spending categories and the group each belongs to; last holiday season, year to date against the plan and the monthly set-aside for the next season fill in by themselves.', [
    LST('category', 'Category', 'category', 24, required=True), LST('group', 'Group', 'group', 15),
    CA('season_total', 'Spent in the last Nov and Dec', 'money', _SEAS, 13), CA('season_month', 'Set aside a month for the next season', 'money', 'ROUND({col:season_total}/%s,2)' % _NM, 14),
    CA('ytd', 'Year to date, complete months', 'money', 'SUMIFS(%s,%s,{col:category},%s,">="&DATE(YEAR({today}),1,1))' % (R('pva', 'actual'), R('pva', 'category'), R('pva', 'month')), 13),
    CA('ytd_plan', 'Plan year to date', 'money', 'SUMIFS(%s,%s,{col:category},%s,">="&DATE(YEAR({today}),1,1))' % (R('pva', 'planned'), R('pva', 'category'), R('pva', 'month')), 12),
    CA('ytd_diff', 'Over or under plan', 'money', '{col:ytd}-{col:ytd_plan}', 12), HH(), PH('member', 'Household member phone')],
    D.categories_d(), 50, [A('ytd_diff', '> 0', 'warn')]))
# 3 accounts ------------------------------------------------------------------
tables.append(T('accounts', 'Accounts', 'Accounts',
    'The 14 accounts, cards and loans with opening and current balances (a card or loan balance is the amount owed); money out of each account in the last 30 days fills in by itself.', [
    C('account_id', 'Account ID', 'text', 9, required=True), C('account', 'Account', 'text', 26), LST('type', 'Type', 'atype', 12), LST('owner', 'Owner', 'person', 11),
    C('opening_balance', 'Opening balance', 'money', 14), C('balance_now', 'Balance now', 'money', 14),
    CA('spent_30d', 'Money out, last 30 days', 'money', 'SUMIFS(%s,%s,{col:account},%s,">="&({today}-30))' % (R('transactions', 'amount'), R('transactions', 'account'), R('transactions', 'date')), 14)],
    D.accounts_d(), 50))
# 4 budget --------------------------------------------------------------------
tables.append(T('budget', 'Budget plan', 'Budget Plan',
    'The plan: one row for each category and month with the amount you plan to spend, save or pay; the group fills in. Add next month before it starts.', [
    C('plan_id', 'Plan ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('category', 'Category', 'category', 20),
    CA('group', 'Group', 'text', LKT('categories.group', 'categories.category', 'category'), 14), C('planned', 'Planned a month', 'money', 13)],
    D.budget_d(), 1100))
# 5 income --------------------------------------------------------------------
tables.append(T('income', 'Income', 'Income Received',
    'Each paycheck, invoice payment or side income as received: take-home amount, the part moved to the tax set-aside and the retirement amount taken before pay.', [
    C('income_id', 'Income ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    LST('person', 'Person', 'payer', 11), LST('source', 'Source', 'isource', 13), C('net', 'Take-home', 'money', 12), C('set_aside', 'Set aside', 'money', 12), C('retirement', 'Retirement', 'money', 12)],
    D.income_d(), 200))
# 6 contributions -------------------------------------------------------------
tables.append(T('contributions', 'Contributions', 'Savings Contributions',
    'Money moved into savings goals and sinking funds, and money spent from them; the category tells the plan which savings line it belongs to.', [
    C('contribution_id', 'Contribution ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    C('goal_id', 'Goal ID', 'text', 9), LST('category', 'Category', 'category', 18), LST('kind', 'Kind', 'ctkind', 10), C('amount', 'Amount', 'money', 12)],
    D.contributions_d(), 400))
# 7 debt payments -------------------------------------------------------------
tables.append(T('debt_payments', 'Debt payments', 'Debt Payments',
    'Every payment on a card or loan with the minimum and the extra; the extra counts toward your savings rate.', [
    C('payment_id', 'Payment ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    C('debt_id', 'Debt ID', 'text', 9), C('minimum', 'Minimum', 'money', 12), C('extra', 'Extra', 'money', 12), C('amount', 'Amount', 'money', 12)],
    D.debt_payments_d(), 200))
# 8 pva -----------------------------------------------------------------------
tables.append(T('pva', 'Planned against actual', 'Planned against Actual by Month',
    'Each complete month and category: the plan, what happened, the difference (over plan is positive), the share of the plan used and the year to date. Spending from a goal is left out.', [
    C('pa_id', 'Line ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('category', 'Category', 'category', 20),
    CA('group', 'Group', 'text', LKT('categories.group', 'categories.category', 'category'), 14),
    CA('planned', 'Planned', 'money', 'SUMIFS(%s,%s,{col:month},%s,{col:category})' % (R('budget', 'planned'), R('budget', 'month'), R('budget', 'category')), 12),
    CA('actual', 'Actual', 'money', ACTM('{col:category}', '{col:month}'), 12), CA('variance', 'Over or under plan', 'money', '{col:actual}-{col:planned}', 13),
    CA('share_used', 'Share of plan used', 'pct', 'IF({col:planned}>0,{col:actual}/{col:planned},0)', 11),
    CA('ytd', 'Year to date', 'money', 'SUMIFS(%s,%s,{col:category},%s,">="&DATE(YEAR({col:month}),1,1),%s,"<="&{col:month})' % (R('pva', 'actual'), R('pva', 'category'), R('pva', 'month'), R('pva', 'month')), 12),
    HH(), PH('member', 'Household member phone'), PH('school', 'School office phone'), PH('mech', 'Car mechanic phone'), PH('util', 'Utility company phone'),
    PH('ins', 'Insurance agent phone'), PH('tax', 'Tax preparer phone')],
    D.pva_d(), 400, [A('variance', '> 0', 'warn')]))
# 9 this month ----------------------------------------------------------------
tables.append(T('this_month', 'This month by category', 'This Month by Category',
    'Every category this month to date against the plan: variable spending against the plan pro-rated by days, bills and savings against the full month; pace at month end and the flag fill in.', [
    LST('category', 'Category', 'category', 22, required=True), CA('group', 'Group', 'text', LKT('categories.group', 'categories.category', 'category'), 14),
    CA('planned', 'Planned this month', 'money', 'SUMIFS(%s,%s,%s,%s,{col:category})' % (R('budget', 'planned'), R('budget', 'month'), MS, R('budget', 'category')), 12),
    CA('var', 'Variable spending', 'int', 'IF(OR({col:group}=%s,{col:group}=%s),1,0)' % (G_VAR, G_WANT), 9),
    CA('counts', 'Counts as spending', 'int', 'IF(OR({col:group}=%s,{col:group}=%s),0,1)' % (G_SAV, G_DEBT), 9),
    CA('base', 'Plan to date', 'money', 'IF({col:var}=1,{col:planned}*%s/%s,{col:planned})' % (DAYN, DIM), 12),
    CA('actual', 'Actual to date', 'money', ACTM('{col:category}', MS), 12), CA('variance', 'Over or under plan', 'money', '{col:actual}-{col:base}', 13),
    CA('over_amt', 'Over by', 'money', 'MAX(0,{col:variance})', 11), CA('vs_plan', 'Against plan to date', 'pct', 'IF({col:base}>0,{col:actual}/{col:base}-1,0)', 11),
    CA('pace_end', 'Pace at month end', 'money', 'IF({col:var}=1,{col:actual}*%s/%s,MAX({col:actual},{col:planned}))' % (DIM, DAYN), 12),
    CA('flag', 'Pace flag', 'text', 'IF({col:planned}=0,IF({col:actual}>0,%s,%s),IF({col:actual}>{col:base}*(1+{set:pace_tol}),%s,IF({col:actual}<{col:base}*(1-{set:pace_tol}),%s,%s)))' % (
        pace('Over pace'), pace('No plan'), pace('Over pace'), pace('Under pace'), pace('On pace')), 11),
    CA('watch_key', 'Watch-list key', 'num', 'IF({col:counts}=1,{col:variance}+(100-MATCH({col:category},%s,0))/100000,"")' % R('categories', 'category'), 10),
    CA('rank_key', 'Ranking key', 'num', 'IF({col:flag}=%s,{col:over_amt}+(100-MATCH({col:category},%s,0))/100000,"")' % (pace('Over pace'), R('categories', 'category')), 10),
    CA('month_end', 'Month-end review date', 'date', 'EOMONTH({today},0)', 11), HH(), N2(), PH('p2', 'Partner 2 phone')],
    D.this_month_d(), 50, [A('flag', '= ' + pace('Over pace'), 'bad'), A('flag', '= ' + pace('Under pace'), 'good')]))
# 10 over budget list ---------------------------------------------------------
def _rk(c): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,{col:rank}),%s,0)),"")' % (R('this_month', c), R('this_month', 'watch_key'), R('this_month', 'watch_key'))
tables.append(T('overbudget', 'Over-budget list', 'Over-budget List, Biggest First',
    'The 12 spending categories furthest over plan this month, biggest first (a minus is still under plan), with how often each was over in the last 3 complete months and what to do.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('category', 'Category', 'text', _rk('category'), 22), CA('over_by', 'Over (+) or under (-) plan', 'money', _rk('variance'), 13),
    CA('share_over', 'Share over plan to date', 'pct', _rk('vs_plan'), 12),
    CA('months_over', 'Last 3 months over', 'int', 'IF({col:category}="","",COUNTIFS(%s,{col:category},%s,">="&EDATE(%s,-3),%s,">0"))' % (R('pva', 'category'), R('pva', 'month'), MS, R('pva', 'variance')), 11),
    CA('action', 'What to do', 'text', 'IF({col:category}="","",IF({col:over_by}>0,IF({col:months_over}>=2,%s,%s),%s))' % (va('Raise the plan or cut spending'), va('Watch it this month'), va('On track this month')), 26)],
    D.overbudget_d(), 50, [A('months_over', '>= 2', 'bad')]))
# 11 compare with own history -------------------------------------------------
_W0 = WINDOWS(0)
_AVG3 = '(%s+%s+%s)/3' % tuple(ACTW('{col:category}', *WINDOWS(k)) for k in (1, 2, 3))
tables.append(T('compare', 'Compare with own history', 'Compare with Your Own History',
    'Each category this month to date against the same days of the last 3 months (average) and the same days a year ago; no national figure, only your own history.', [
    LST('category', 'Category', 'category', 22, required=True), CA('this_month', 'This month to date', 'money', ACTW('{col:category}', _W0[0], _W0[1]), 12),
    CA('avg3', 'Last 3 months, same days', 'money', _AVG3, 12), CA('last_year', 'Same days last year', 'money', ACTW('{col:category}', 'EDATE(%s,-12)' % MS, 'EDATE({today},-12)'), 12),
    CA('change_avg', 'Change on the 3-month average', 'money', '{col:this_month}-{col:avg3}', 13), CA('change_ly', 'Change on last year', 'money', '{col:this_month}-{col:last_year}', 13),
    CA('trend', 'Against 3 months', 'text', 'IF({col:avg3}=0,IF({col:this_month}>0,%s,%s),IF({col:this_month}>{col:avg3}*(1+{set:pace_tol}),%s,IF({col:this_month}<{col:avg3}*(1-{set:pace_tol}),%s,%s)))' % (
        tok('chg', 'Higher'), tok('chg', 'Same'), tok('chg', 'Higher'), tok('chg', 'Lower'), tok('chg', 'Same')), 11),
    CA('group', 'Group', 'text', LKT('categories.group', 'categories.category', 'category'), 14), CA('counts', 'Counts as spending', 'int', 'IF(OR({col:group}=%s,{col:group}=%s),0,1)' % (G_SAV, G_DEBT), 9),
    CA('up_key', 'Rise ranking key', 'num', 'IF(AND({col:counts}=1,{col:change_ly}>0),{col:change_ly}+(100-MATCH({col:category},%s,0))/100000,"")' % R('categories', 'category'), 10),
    CA('down_key', 'Fall ranking key', 'num', 'IF(AND({col:counts}=1,{col:change_ly}<0),-{col:change_ly}+(100-MATCH({col:category},%s,0))/100000,"")' % R('categories', 'category'), 10),
    HH(), N1(), PH('p1', 'Partner 1 phone')],
    D.compare_d(), 50, [A('change_ly', '> 0', 'warn'), A('change_ly', '< 0', 'good')]))
# 12 envelopes ----------------------------------------------------------------
tables.append(T('envelopes', 'Envelopes', 'Spending Envelopes',
    'A weekly allowance for each variable category and the weekday its week starts; the monthly allowance fills in. Change an allowance and every status page follows.', [
    C('envelope', 'Envelope', 'text', 22, required=True), LST('category', 'Category', 'category', 20), C('weekly', 'Weekly allowance', 'money', 13), LST('start_day', 'Week starts on', 'wday', 12),
    CA('monthly', 'Monthly allowance', 'money', 'ROUND({col:weekly}*52/12,2)', 13)],
    D.envelopes_d(), 50))
# 13 envelope status ----------------------------------------------------------
_EN = lambda c: LKT('envelopes.' + c, 'envelopes.envelope', 'envelope')
_WSTART = '({today}-MOD(WEEKDAY({today},2)-%s,7))' % WDNO(LKT('envelopes.start_day', 'envelopes.envelope', 'envelope'))
tables.append(T('env_status', 'Envelope status', 'Envelope Status Today',
    'Each envelope today: the month allowance, spent so far, money left, days left, what you can spend a day, the pace at month end and the week against its allowance.', [
    REF('envelope', 'Envelope', 'envelopes.envelope', 22, required=True), CA('category', 'Category', 'text', _EN('category'), 20),
    CA('allowance', 'Monthly allowance', 'money', LKN('envelopes.monthly', 'envelopes.envelope', 'envelope'), 12),
    CA('to_date', 'Allowance to date', 'money', '{col:allowance}*%s/%s' % (DAYN, DIM), 12),
    CA('spent', 'Spent so far', 'money', 'SUMIFS(%s,%s,{col:category},%s,%s,%s,"")' % (R('transactions', 'amount'), R('transactions', 'category'), R('transactions', 'month'), MS, R('transactions', 'from_goal')), 12),
    CA('over_share', 'Over allowance to date', 'pct', 'IF({col:to_date}>0,{col:spent}/{col:to_date}-1,0)', 12),
    CA('left', 'Left this month', 'money', '{col:allowance}-{col:spent}', 12), CA('days_left', 'Days left', 'int', '%s-%s' % (DIM, DAYN), 8),
    CA('per_day', 'Can spend a day', 'money', 'IF({col:days_left}>0,MAX(0,{col:left})/{col:days_left},MAX(0,{col:left}))', 12),
    CA('month_end', 'Pace at month end', 'money', '{col:spent}*%s/%s' % (DIM, DAYN), 12), CA('pace_vs', 'Pace against allowance', 'pct', 'IF({col:allowance}>0,{col:month_end}/{col:allowance}-1,0)', 11),
    CA('flag', 'Pace flag', 'text', 'IF({col:allowance}=0,%s,IF({col:month_end}>{col:allowance}*(1+{set:pace_tol}),%s,IF({col:month_end}<{col:allowance}*(1-{set:pace_tol}),%s,%s)))' % (
        pace('No plan'), pace('Over pace'), pace('Under pace'), pace('On pace')), 11),
    CA('week_allow', 'Weekly allowance', 'money', LKN('envelopes.weekly', 'envelopes.envelope', 'envelope'), 11),
    CA('week_spent', 'Spent this envelope week', 'money', 'SUMIFS(%s,%s,{col:category},%s,">="&%s,%s,"<="&{today},%s,"")' % (R('transactions', 'amount'), R('transactions', 'category'), R('transactions', 'date'), _WSTART, R('transactions', 'date'), R('transactions', 'from_goal')), 12),
    CA('week_left', 'Left this week', 'money', '{col:week_allow}-{col:week_spent}', 11), CA('date', 'Today', 'date', '{today}', 11), HH(), N2(), PH('p2', 'Partner 2 phone'), PH('member', 'Household member phone')],
    D.env_status_d(), 50, [A('flag', '= ' + pace('Over pace'), 'bad'), A('flag', '= ' + pace('Under pace'), 'good')]))
# 14 groceries by week --------------------------------------------------------
_GA = 'SUMIFS(%s,%s,%s)' % (R('envelopes', 'weekly'), R('envelopes', 'category'), C_GRO)
tables.append(T('grocery_week', 'Groceries by week', 'Groceries by Week',
    'Groceries week by week against the weekly allowance: spent, over or under and the running total of the last 8 weeks; the trips and the whole week of spending fill in.', [
    C('week_start', 'Week start', 'date', 11, required=True), LST('wom', 'Week of the month', 'wom', 11),
    CA('spent', 'Groceries spent', 'money', 'SUMIFS(%s,%s,%s,%s,{col:week_start},%s,"")' % (R('transactions', 'amount'), R('transactions', 'category'), C_GRO, R('transactions', 'week_start'), R('transactions', 'from_goal')), 12),
    CA('allowance', 'Weekly allowance', 'money', _GA, 12), CA('over_under', 'Over or under', 'money', '{col:spent}-{col:allowance}', 12),
    CA('running', 'Running total, 8 weeks', 'money', 'SUMIFS(%s,%s,"<="&{col:week_start},%s,">"&({col:week_start}-56))' % (R('grocery_week', 'over_under'), R('grocery_week', 'week_start'), R('grocery_week', 'week_start')), 13),
    CA('trips', 'Grocery payments', 'int', 'COUNTIFS(%s,%s,%s,{col:week_start},%s,"")' % (R('transactions', 'category'), C_GRO, R('transactions', 'week_start'), R('transactions', 'from_goal')), 9),
    CA('week_total', 'All spending that week', 'money', 'SUMIFS(%s,%s,{col:week_start})' % (R('transactions', 'counted'), R('transactions', 'week_start')), 13),
    CA('week_tx', 'Payments that week', 'int', 'COUNTIFS(%s,{col:week_start},%s,">0")' % (R('transactions', 'week_start'), R('transactions', 'counted')), 9),
    CA('noa_allow', 'Allowance, older child', 'money', '{set:allowance_noa}', 11), CA('ike_allow', 'Allowance, younger child', 'money', '{set:allowance_ike}', 11),
    HH(), N1(), N2(), PH('p1', 'Partner 1 phone'), PH('p2', 'Partner 2 phone'), PH('member', 'Household member phone'), PH('noa', 'Older child phone'), PH('ike', 'Younger child phone')],
    D.grocery_week_d(), 70, [A('over_under', '> 0', 'warn'), A('over_under', '< 0', 'good')]))
# 15 spending by month and group ---------------------------------------------
tables.append(T('monthgroup', 'Spending by month and group', 'Spending by Month and Group',
    'For each month and group: the money out, or for Savings the deposits and retirement; the share of the month fills in. Debt payments are shown on their own because card purchases are counted already.', [
    C('mg_id', 'Line ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('group', 'Group', 'group', 15),
    CA('amount', 'Amount', 'money', 'SUMIFS(%s,%s,{col:month},%s,{col:group},%s,"")+IF({col:group}=%s,SUMIFS(%s,%s,{col:month},%s,%s)+SUMIFS(%s,%s,{col:month}),0)' % (
        R('transactions', 'amount'), R('transactions', 'month'), R('transactions', 'group'), R('transactions', 'from_goal'), G_SAV,
        R('contributions', 'amount'), R('contributions', 'month'), R('contributions', 'kind'), DEP, R('income', 'retirement'), R('income', 'month')), 12),
    CA('share', 'Share of the month', 'pct', 'IFERROR({col:amount}/SUMIFS(%s,%s,{col:month}),0)' % (R('monthgroup', 'amount'), R('monthgroup', 'month')), 11)],
    D.monthgroup_d(), 150))
# 16 spending by payee ---------------------------------------------------------
_L12 = '">="&({today}-365)'
tables.append(T('payees', 'Spending by payee', 'Spending by Payee',
    'The payees you paid in the last 12 months, biggest first: payments, amount, average and share; the last 90 days show the small leaks. Mark planned payments so they are not leaks.', [
    REF('payee', 'Payee', 'payees.payee', 24, required=True), C('planned', 'Planned payment', 'bool', 9),
    CA('count12', 'Payments, 12 months', 'int', 'COUNTIFS(%s,{col:payee},%s,%s,%s,">0")' % (R('transactions', 'payee'), R('transactions', 'date'), _L12, R('transactions', 'counted')), 10),
    CA('amount12', 'Spent, 12 months', 'money', 'SUMIFS(%s,%s,{col:payee},%s,%s)' % (R('transactions', 'counted'), R('transactions', 'payee'), R('transactions', 'date'), _L12), 12),
    CA('average', 'Average payment', 'money', 'IF({col:count12}>0,{col:amount12}/{col:count12},0)', 12),
    CA('share', 'Share of spending', 'pct', 'IFERROR({col:amount12}/SUMIFS(%s,%s,%s),0)' % (R('transactions', 'counted'), R('transactions', 'date'), _L12), 10),
    CA('count90', 'Payments, 90 days', 'int', 'COUNTIFS(%s,{col:payee},%s,">="&({today}-90),%s,">0")' % (R('transactions', 'payee'), R('transactions', 'date'), R('transactions', 'counted')), 10),
    CA('amount90', 'Spent, 90 days', 'money', 'SUMIFS(%s,%s,{col:payee},%s,">="&({today}-90))' % (R('transactions', 'counted'), R('transactions', 'payee'), R('transactions', 'date')), 12),
    CA('leak_cost', 'Small leak, a month', 'money', 'IF(AND({col:planned}<>%s,{col:count90}>={set:leak_times},{col:count90}>0),IF({col:amount90}/MAX({col:count90},1)<={set:leak_max},{col:amount90}/3,0),0)' % YES, 12),
    HH(), PH('noa', 'Older child phone'), PH('ike', 'Younger child phone')],
    D.payees_d(), 80, [A('leak_cost', '> 0', 'warn')]))
# 17 spending by person ---------------------------------------------------------
tables.append(T('by_person', 'Spending by person', 'Spending by Person',
    'What each partner paid in a period and its share of all counted spending, so you can see who carries what; settling shared costs is in Partners, Kids and Shared Costs.', [
    C('bp_id', 'Line ID', 'text', 9, required=True), LST('paid_by', 'Paid by', 'payer', 11), LST('period', 'Period', 'period', 14),
    CA('from_date', 'From', 'date', PERIOD_FROM('{col:period}'), 11), CA('to_date', 'To', 'date', PERIOD_TO('{col:period}'), 11),
    CA('count', 'Payments', 'int', 'COUNTIFS(%s,{col:paid_by},%s,">="&{col:from_date},%s,"<="&{col:to_date},%s,">0")' % (R('transactions', 'paid_by'), R('transactions', 'date'), R('transactions', 'date'), R('transactions', 'counted')), 9),
    CA('amount', 'Amount', 'money', 'SUMIFS(%s,%s,{col:paid_by},%s,">="&{col:from_date},%s,"<="&{col:to_date})' % (R('transactions', 'counted'), R('transactions', 'paid_by'), R('transactions', 'date'), R('transactions', 'date')), 12),
    CA('share', 'Share of spending', 'pct', 'IFERROR({col:amount}/SUMIFS(%s,%s,">="&{col:from_date},%s,"<="&{col:to_date}),0)' % (R('transactions', 'counted'), R('transactions', 'date'), R('transactions', 'date')), 11)],
    D.by_person_d(), 50))
# 18 weekday pattern ------------------------------------------------------------
tables.append(T('weekday', 'Weekday pattern', 'Weekday Pattern',
    'Spending by weekday over three windows: payments, amount and the average payment, to see which days money leaves.', [
    C('wd_id', 'Line ID', 'text', 9, required=True), LST('weekday', 'Weekday', 'wday', 12), LST('period', 'Period', 'period', 14),
    CA('from_date', 'From', 'date', PERIOD_FROM('{col:period}'), 11), CA('to_date', 'To', 'date', PERIOD_TO('{col:period}'), 11),
    CA('count', 'Payments', 'int', 'COUNTIFS(%s,{col:weekday},%s,">="&{col:from_date},%s,"<="&{col:to_date},%s,">0")' % (R('transactions', 'weekday'), R('transactions', 'date'), R('transactions', 'date'), R('transactions', 'counted')), 9),
    CA('amount', 'Amount', 'money', 'SUMIFS(%s,%s,{col:weekday},%s,">="&{col:from_date},%s,"<="&{col:to_date})' % (R('transactions', 'counted'), R('transactions', 'weekday'), R('transactions', 'date'), R('transactions', 'date')), 12),
    CA('average', 'Average payment', 'money', 'IF({col:count}>0,{col:amount}/{col:count},0)', 12)],
    D.weekday_d(), 50))
# 19 savings rate by month ------------------------------------------------------
_M = '{col:month}'
def _SUMM(t, c, extra=''): return 'SUMIFS(%s,%s,%s%s)' % (R(t, c), R(t, 'month'), _M, extra)
_PLAN = '%s-SUMIFS(%s,%s,{col:month},%s,%s)-SUMIFS(%s,%s,{col:month},%s,%s)' % (_SUMM('budget', 'planned'), R('budget', 'planned'), R('budget', 'month'), R('budget', 'group'), G_SAV, R('budget', 'planned'), R('budget', 'month'), R('budget', 'group'), G_DEBT)
def _MG(g): return 'SUMIFS(%s,%s,{col:month},%s,%s)' % (R('monthgroup', 'amount'), R('monthgroup', 'month'), R('monthgroup', 'group'), g)
tables.append(T('savings_rate', 'Savings rate by month', 'Savings Rate by Month',
    'Each month: take-home pay, savings, extra debt payments and retirement, the savings rate against your own best month, and spending against plan and against the same month last year.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('take_home', 'Take-home after set-aside', 'money', '%s-%s' % (_SUMM('income', 'net'), _SUMM('income', 'set_aside')), 13), CA('retirement', 'Retirement', 'money', _SUMM('income', 'retirement'), 11),
    CA('saved', 'Saved into goals', 'money', _SUMM('contributions', 'amount', ',%s,%s,%s,"<>"&%s' % (R('contributions', 'kind'), DEP, R('contributions', 'category'), cat('Tax set-aside'))), 12),
    CA('debt_extra', 'Extra debt payments', 'money', _SUMM('debt_payments', 'extra'), 12), CA('total_saved', 'Total saved', 'money', '{col:saved}+{col:debt_extra}+{col:retirement}', 12),
    CA('basis', 'Take-home plus retirement', 'money', '{col:take_home}+{col:retirement}', 13), CA('savings_rate', 'Savings rate', 'pct', 'IF({col:basis}>0,{col:total_saved}/{col:basis},0)', 10),
    CA('rate_12m', 'Rate, last 12 complete months', 'pct', 'IF(AND({col:month}>=EDATE(%s,-12),{col:month}<%s),{col:savings_rate},"")' % (MS, MS), 11),
    CA('flag', 'Against your best', 'text', 'IF({col:savings_rate}=MAX(%s),%s,IF({col:savings_rate}>={set:savings_rate_target},%s,%s))' % (R('savings_rate', 'rate_12m'), tok('sflag', 'Best month'), tok('sflag', 'At or above target'), tok('sflag', 'Below target')), 17),
    CA('spent', 'Counted spending', 'money', _SUMM('transactions', 'counted'), 12), CA('planned', 'Planned spending', 'money', _PLAN, 12),
    CA('plan_left', 'Left of the plan', 'money', '{col:planned}-{col:spent}', 12),
    CA('spent_ly', 'Same month last year', 'money', 'SUMIFS(%s,%s,EDATE({col:month},-12))' % (R('savings_rate', 'spent'), R('savings_rate', 'month')), 12),
    CA('needs', 'Needs', 'money', '%s+%s' % (_MG(G_FIX), _MG(G_VAR)), 11), CA('wants', 'Wants', 'money', _MG(G_WANT), 11),
    CA('days', 'Days counted', 'int', 'IF({col:month}=%s,%s,DAY(EOMONTH({col:month},0)))' % (MS, DAYN), 8),
    CA('spend_days', 'Days with variable spending', 'int', 'COUNTIFS(%s,{col:month},%s,1)' % (R('transactions', 'month'), R('transactions', 'var_day')), 10),
    CA('no_spend_days', 'No-spend days', 'int', '{col:days}-{col:spend_days}', 9), CA('month_end', 'Month-end review date', 'date', 'EOMONTH({col:month},0)', 11),
    HH(), N1(), N2(), PH('p1', 'Partner 1 phone'), PH('p2', 'Partner 2 phone'), PH('member', 'Household member phone'), PH('bank', 'Bank branch phone')],
    D.savings_rate_d(), 60, [A('flag', '= ' + tok('sflag', 'Best month'), 'good'), A('flag', '= ' + tok('sflag', 'Below target'), 'warn')]))
# 20 large and duplicate checks -------------------------------------------------
_TX = lambda c: LKT('transactions.' + c, 'transactions.tx_id', 'tx_id')
_GRPOF = 'IFERROR(INDEX(%s,MATCH({col:category},%s,0)),"")' % (R('categories', 'group'), R('categories', 'category'))
tables.append(T('checks', 'Large and duplicate checks', 'Large and Duplicate Payment Checks',
    'Payments worth a second look: possible duplicates, large variable payments and the category Other; type a transaction ID and the check and the fix fill in.', [
    REF('tx_id', 'Transaction ID', 'transactions.tx_id', 12, required=True), CA('date', 'Date', 'date', LKD('transactions.date', 'transactions.tx_id', 'tx_id'), 11), CA('payee', 'Payee', 'text', _TX('payee'), 22),
    CA('category', 'Category', 'text', _TX('category'), 20), CA('amount', 'Amount', 'money', LKN('transactions.amount', 'transactions.tx_id', 'tx_id'), 12),
    CA('check_kind', 'Check', 'text', 'IF(IFERROR(INDEX(%s,MATCH({col:tx_id},%s,0)),"")<>"",%s,IF({col:category}=%s,%s,IF(AND({col:amount}>={set:large_payment},%s<>%s,%s<>%s),%s,%s)))' % (
        R('transactions', 'dup_date'), R('transactions', 'tx_id'), ck('Possible duplicate'), C_OTHER, ck('Category Other'), _GRPOF, G_FIX, _GRPOF, G_DEBT, ck('Large payment'), ck('No issue')), 17),
    CA('fix', 'Fix', 'text', 'IF({col:check_kind}=%s,%s,IF({col:check_kind}=%s,%s,IF({col:check_kind}=%s,%s,%s)))' % (
        ck('Possible duplicate'), ck('Ask your bank about the second payment'), ck('Category Other'), ck('Choose a real category'), ck('Large payment'), ck('Check the receipt'), ck('Nothing to do')), 30),
    HH(), N1(), PH('p1', 'Partner 1 phone'), PH('bank', 'Bank branch phone')],
    D.checks_d(), 80, [A('check_kind', '= ' + ck('Possible duplicate'), 'bad'), A('check_kind', '= ' + ck('Large payment'), 'warn')]))
assert len(tables) == 20, len(tables)
TB = {t['key']: t for t in tables}
