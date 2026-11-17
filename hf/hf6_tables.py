"""Household Finance suite part 6: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf6_lists import *
import hf6_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
LM = 'MAX(%s)' % R('networth', 'month')
def NWM(expr): return 'SUMIFS(%s,%s,%s)' % (R('nwm', 'net_worth'), R('nwm', 'month'), expr)
NWNOW = NWM(LM)
A_, L_ = tok('side', 'Asset'), tok('side', 'Liability')
CHKG, SAV, CARD, LOAN, RET, BRK = (tok('atype', t) for t in ('Checking', 'Savings', 'Credit card', 'Loan', 'Retirement', 'Brokerage'))
PJ = tok('person', 'Joint'); PP1 = tok('person', 'Partner 1'); PP2 = tok('person', 'Partner 2')
def TL(col, role): return 'IFERROR(INDEX(%s,MATCH({list:role.%s},%s,0))&"","")' % (R('team', col), key('role', role), R('team', 'role'))
def PH(role, k, label): return CA(k, label, 'text', TL('phone', role), 18)
def HH(): return CA('household', 'Household', 'text', '{set:household}', 22)
def N1(): return CA('partner1', 'Partner 1 name', 'text', '{set:partner1}', 14)
def N2(): return CA('partner2', 'Partner 2 name', 'text', '{set:partner2}', 14)
def POT(): return '(SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s))' % (R('bnow', 'balance'), R('bnow', 'type'), SAV, R('bnow', 'balance'), R('bnow', 'type'), RET, R('bnow', 'balance'), R('bnow', 'type'), BRK)
def PIV(item): return 'SUMIFS(%s,%s,%s)' % (R('proj_inputs', 'value'), R('proj_inputs', 'item'), tok('pitem', item))
START = 'IF(%s>0,%s,%s)' % (PIV(PITEMS[1]), PIV(PITEMS[1]), POT())
GAP = PIV(PITEMS[0])
NWB = R('networth', 'balance')

settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('partner1', 'Partner 1 name, shown in messages', 'text', 'Partner 1'), S('partner2', 'Partner 2 name, shown in messages', 'text', 'Partner 2'),
    S('next_payday', 'Next pay date of partner 1', 'date', D.ST['payday']),
    S('cash_floor', 'Cash floor on the joint account, your own number', 'money', CASH_FLOOR),
    S('emergency_low', 'Emergency fund months, low end, a typical range', 'int', EMERGENCY_MONTHS_LOW), S('emergency_high', 'Emergency fund months, high end, a typical range', 'int', EMERGENCY_MONTHS_HIGH),
    S('growth_rate', 'Yearly growth for the projection, an example, not a forecast', 'pct', GROWTH_RATE), S('monthly_contribution', 'Monthly amount you add to savings and investments', 'money', 900),
    S('agreed_p1_share', 'Partner 1 agreed share of shared costs', 'pct', AGREED_P1_SHARE), S('joint_monthly', 'Monthly amount the joint account needs from the partners', 'money', 4800),
    S('p1_takehome', 'Partner 1 take-home a month', 'money', 4680), S('p2_takehome', 'Partner 2 average take-home a month', 'money', 3400),
    S('essential_monthly', 'Essential spending a month, type it', 'money', 4200), S('daily_spend', 'Spending a day outside bills, your estimate', 'money', 15), S('balance_tol', 'A difference up to this amount counts as matching', 'money', 1),
    S('joint_account', 'Account ID of the joint checking account', 'text', 'AC-01'), S('emergency_account', 'Name of your emergency savings account', 'text', 'Emergency savings')]
assert 3 <= len(settings) <= 20

tables = []
# 1 team
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact: role, phone and e-mail; the messages in this workbook use these phone numbers.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('group', 'Group', 'tgroup', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11)], D.team_d(), 50))
# 2 accounts
tables.append(T('accounts', 'Accounts', 'Accounts with Owner and Type',
    'Every account you own or owe: type, owner, opening balance and balance now; a card or loan balance is the amount owed. A single adult lists fewer accounts.', [
    C('account_id', 'Account ID', 'text', 10, required=True), C('account', 'Account', 'text', 26), LST('type', 'Type', 'atype', 13), LST('owner', 'Owner', 'person', 11),
    C('opening_balance', 'Opening balance', 'money', 14), C('balance_now', 'Balance now', 'money', 13), LST('side', 'Asset or liability', 'side', 12), C('opened', 'Opened', 'date', 11),
    CA('date', 'Reply by', 'date', '{today}+7', 11), CA('month', 'Statement month', 'date', 'EDATE(%s,-1)' % MS, 12), CA('year', 'Tax year', 'int', 'YEAR({today})-1', 9),
    CA('joint_name', 'Joint account', 'text', 'IFERROR(INDEX(%s,MATCH({set:joint_account},%s,0)),"")' % (R('accounts', 'account'), R('accounts', 'account_id')), 20),
    HH(), PH('Bank branch', 'bank_phone', 'Bank branch phone'), PH('Payroll office', 'payroll_phone', 'Payroll office phone'), PH('Tax preparer', 'tax_phone', 'Tax preparer phone')],
    D.accounts_d(), 40))
# 3 net worth rows
tables.append(T('networth', 'Net worth', 'Balances Typed Each Month',
    'One row per account per month: the balance as the account holds it (a card or loan is the amount owed); every net worth page reads from here.', [
    C('nw_id', 'NW ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), C('as_of', 'As of', 'date', 11), REF('account_id', 'Account ID', 'accounts.account_id', 10),
    REF('account', 'Account', 'accounts.account', 24), LST('type', 'Type', 'atype', 13), LST('side', 'Asset or liability', 'side', 12), C('balance', 'Balance', 'money', 13),
    CA('signed', 'Net worth effect', 'money', 'IF({col:side}=%s,{col:balance},-{col:balance})' % A_, 13),
    CA('owner', 'Owner', 'text', 'IFERROR(INDEX(%s,MATCH({col:account_id},%s,0))&"","")' % (R('accounts', 'owner'), R('accounts', 'account_id')), 11)], D.networth_d(), 700))
# 4 net worth by month
_NM = '%s,{col:month}' % R('networth', 'month')
def PRV(col, n): return 'IF(COUNTIFS(%s,EDATE({col:month},-%d))=0,"",{col:%s}-SUMIFS(%s,%s,EDATE({col:month},-%d)))' % (R('nwm', 'month'), n, col, R('nwm', col), R('nwm', 'month'), n)
tables.append(T('nwm', 'Net worth by month', 'Net Worth by Month',
    'Each month: assets, liabilities and net worth, the change on last month and on last year, and how many accounts were typed.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('assets', 'Assets', 'money', 'SUMIFS(%s,%s,%s)' % (NWB, _NM, '%s,%s' % (R('networth', 'side'), A_)), 13),
    CA('liabilities', 'Liabilities', 'money', 'SUMIFS(%s,%s,%s)' % (NWB, _NM, '%s,%s' % (R('networth', 'side'), L_)), 13),
    CA('net_worth', 'Net worth', 'money', '{col:assets}-{col:liabilities}', 13), CA('chg_month', 'Change on last month', 'money', PRV('net_worth', 1), 14),
    CA('chg_year', 'Change on last year', 'money', PRV('net_worth', 12), 14), CA('accounts_typed', 'Accounts typed', 'int', 'COUNTIFS(%s)' % _NM, 10),
    CA('year', 'Year', 'int', 'YEAR({col:month})', 8), CA('date', 'Review date', 'date', '{today}+14', 11), HH(), N1(), N2(),
    PH('Partner 1', 'p1_phone', 'Partner 1 phone'), PH('Partner 2', 'p2_phone', 'Partner 2 phone'), PH('Grandparent', 'member_phone', 'Household member phone'), PH('Tax preparer', 'tax_phone', 'Tax preparer phone')],
    D.nwm_d(), 60, [A('chg_month', '< 0', 'warn')]))
# 5 net worth by group (month x group)
_GM = '%s,{col:month},%s,{col:group}' % (R('networth', 'month'), R('networth', 'type'))
tables.append(T('nwg', 'Balance by group and month', 'Balance by Account Group and Month',
    'Each month and account group: the balance, which side it is on and its share of its side and of net worth.', [
    C('month', 'Month', 'date', 11, required=True), LST('group', 'Account group', 'atype', 14),
    CA('balance', 'Balance', 'money', 'SUMIFS(%s,%s)' % (NWB, _GM), 13),
    CA('side', 'Asset or liability', 'text', 'IFERROR(INDEX(%s,MATCH({col:group},%s,0)),"")' % (R('networth', 'side'), R('networth', 'type')), 14),
    CA('share_side', 'Share of its side', 'pct', 'IFERROR({col:balance}/SUMIFS(%s,%s,{col:month},%s,{col:side}),0)' % (NWB, R('networth', 'month'), R('networth', 'side')), 12),
    CA('share_nw', 'Share of net worth', 'pct', 'IFERROR(IF({col:side}=%s,1,-1)*{col:balance}/%s,0)' % (A_, NWM('{col:month}')), 12)], D.nwg_d(), 220))
# 6 balances now
_AC = '{col:account}'
_NA = '%s,%s' % (R('networth', 'account'), _AC)
def LKA(c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (R('accounts', c), _AC, R('accounts', 'account'))
def CHG(n): return 'IF(COUNTIFS(%s,%s,EDATE({col:last_month},-%d))=0,"",{col:balance}-SUMIFS(%s,%s,%s,EDATE({col:last_month},-%d)))' % (
    _NA.replace(',', ',', 1) if False else R('networth', 'account'), _AC, n, NWB, R('networth', 'account'), _AC, n) if False else \
    'IF(COUNTIFS(%s,%s,%s,EDATE({col:last_month},-%d))=0,"",{col:balance}-SUMIFS(%s,%s,%s,%s,EDATE({col:last_month},-%d)))' % (
        R('networth', 'account'), _AC, R('networth', 'month'), n, NWB, R('networth', 'account'), _AC, R('networth', 'month'), n)
_BB = 'SUMIFS(%s,%s,{col:account_id},%s,">="&{today},%s,"<"&{set:next_payday})' % (R('bills', 'amount'), R('bills', 'account_id'), R('bills', 'next_due'), R('bills', 'next_due'))
tables.append(T('bnow', 'Balances now', 'Balances Now by Account',
    'Each account at its latest typed month: balance, change on last month and last year, share of its group and side, and the bills that leave it.', [
    REF('account', 'Account', 'accounts.account', 26, required=True),
    CA('account_id', 'Account ID', 'text', LKA('account_id'), 10), CA('type', 'Type', 'text', LKA('type'), 13), CA('owner', 'Owner', 'text', LKA('owner'), 11), CA('side', 'Asset or liability', 'text', LKA('side'), 12),
    CA('last_month', 'Latest month typed', 'date', 'SUMPRODUCT(MAX((%s=%s)*%s))' % (R('networth', 'account'), _AC, R('networth', 'month')), 12),
    CA('as_of', 'As of', 'date', 'SUMPRODUCT(MAX((%s=%s)*%s))' % (R('networth', 'account'), _AC, R('networth', 'as_of')), 11),
    CA('balance', 'Balance', 'money', 'SUMIFS(%s,%s,%s,%s,{col:last_month})' % (NWB, R('networth', 'account'), _AC, R('networth', 'month')), 13),
    CA('chg_month', 'Change on last month', 'money', CHG(1), 14), CA('chg_year', 'Change on last year', 'money', CHG(12), 14),
    CA('nw_effect', 'Effect on net worth, month', 'money', 'IF({col:chg_month}="","",IF({col:side}=%s,{col:chg_month},-{col:chg_month}))' % A_, 14),
    CA('share_group', 'Share of its group', 'pct', 'IFERROR({col:balance}/SUMIFS(%s,%s,{col:type}),0)' % (R('bnow', 'balance'), R('bnow', 'type')), 11),
    CA('share_side', 'Share of assets or liabilities', 'pct', 'IFERROR({col:balance}/SUMIFS(%s,%s,{col:side}),0)' % (R('bnow', 'balance'), R('bnow', 'side')), 13),
    CA('asset_balance', 'Asset balance', 'money', 'IF({col:side}=%s,{col:balance},"")' % A_, 13),
    CA('bills_amount', 'Bills a month from it', 'money', 'SUMIFS(%s,%s,{col:account_id})' % (R('bills', 'monthly_cost'), R('bills', 'account_id')), 13),
    CA('bills_count', 'Bills from it', 'int', 'COUNTIFS(%s,{col:account_id})' % R('bills', 'account_id'), 9),
    CA('typed_now', 'Typed this month', 'int', 'IF({col:last_month}>=%s,1,0)' % MS, 10),
    CA('liquid_part', 'Liquid net worth part', 'money', 'IF(OR({col:type}=%s,{col:type}=%s),{col:balance},IF({col:type}=%s,-{col:balance},0))' % (CHKG, SAV, CARD), 13),
    CA('liquid_need', 'Liquid need, low months', 'money', '{set:emergency_low}*{set:essential_monthly}/COUNTA(%s)' % R('accounts', 'account_id'), 12),
    CA('emerg_part', 'Emergency fund part', 'money', 'IF({col:account}={set:emergency_account},{col:balance},0)', 12),
    CA('emerg_need', 'Emergency need, high months', 'money', '{set:emergency_high}*{set:essential_monthly}/COUNTA(%s)' % R('accounts', 'account_id'), 12),
    CA('cover_need', 'Move to joint before payday', 'money', 'IF({col:account_id}={set:joint_account},MAX(0,{set:cash_floor}-({col:balance}-%s-{set:daily_spend}*MAX(0,{set:next_payday}-{today}))),0)' % _BB, 13),
    CA('date', 'Reply by', 'date', '{today}+7', 11), HH(), N1(), N2(), PH('Partner 1', 'p1_phone', 'Partner 1 phone'), PH('Partner 2', 'p2_phone', 'Partner 2 phone'),
    PH('Grandparent', 'member_phone', 'Household member phone'), PH('Payroll office', 'payroll_phone', 'Payroll office phone')], D.bnow_d(), 40, [A('chg_month', '< 0', 'warn')]))
# 7 share by account group (group x now / a year ago)
_GB = 'EDATE(%s,-{col:months_back})' % LM
tables.append(T('grp', 'Group shares', 'Share by Account Group',
    'Each account group now and a year ago: balance, side, share of assets and share of net worth.', [
    C('grp_id', 'Row ID', 'text', 9, required=True), LST('group', 'Account group', 'atype', 14), C('months_back', 'Months back', 'int', 9),
    CA('side', 'Asset or liability', 'text', 'IFERROR(INDEX(%s,MATCH({col:group},%s,0)),"")' % (R('networth', 'side'), R('networth', 'type')), 14),
    CA('balance', 'Balance', 'money', 'SUMIFS(%s,%s,{col:group},%s,%s)' % (NWB, R('networth', 'type'), R('networth', 'month'), _GB), 13),
    CA('asset_balance', 'Asset balance', 'money', 'IF({col:side}=%s,{col:balance},0)' % A_, 13), CA('liab_balance', 'Liability balance', 'money', 'IF({col:side}=%s,{col:balance},0)' % L_, 13),
    CA('share_assets', 'Share of assets', 'pct', 'IF({col:side}=%s,IFERROR({col:balance}/SUMIFS(%s,%s,%s,%s,%s),0),0)' % (A_, NWB, R('networth', 'month'), _GB, R('networth', 'side'), A_), 12),
    CA('share_nw', 'Share of net worth', 'pct', 'IFERROR(IF({col:side}=%s,1,-1)*{col:balance}/%s,0)' % (A_, NWM(_GB)), 12),
    CA('change', 'Change since then', 'money', 'IF({col:months_back}=0,{col:balance}-SUMIFS(%s,%s,{col:group},%s,EDATE(%s,-12)),"")' % (NWB, R('networth', 'type'), R('networth', 'month'), LM), 13)],
    D.grp_d(), 30))
# 8 assets and liabilities by month (with the liquid and long-term split)
_AM = '%s,{col:month},%s,' % (R('networth', 'month'), R('networth', 'type'))
def AT(t): return 'SUMIFS(%s,%s%s)' % (NWB, _AM, t)
tables.append(T('alm', 'Assets and liabilities', 'Assets and Liabilities by Type and Month',
    'Each month: cash, savings, retirement, brokerage, cards and loans, then cash and savings, long-term money, debts and liquid net worth.', [
    C('month', 'Month', 'date', 11, required=True), CA('cash', 'Cash', 'money', AT(CHKG), 12), CA('savings', 'Savings', 'money', AT(SAV), 12), CA('retirement', 'Retirement', 'money', AT(RET), 12),
    CA('brokerage', 'Brokerage', 'money', AT(BRK), 12), CA('cards', 'Cards', 'money', AT(CARD), 12), CA('loans', 'Loans', 'money', AT(LOAN), 12),
    CA('cash_savings', 'Cash and savings', 'money', '{col:cash}+{col:savings}', 13), CA('long_term', 'Retirement and brokerage', 'money', '{col:retirement}+{col:brokerage}', 14),
    CA('debts', 'Debts', 'money', '{col:cards}+{col:loans}', 12), CA('liquid_net', 'Liquid net worth', 'money', '{col:cash_savings}-{col:cards}', 13)], D.alm_d(), 60))
# 9 milestones
_LB = 'SUMPRODUCT(MAX((%s<{col:amount})*%s))' % (R('nwm', 'net_worth'), R('nwm', 'month'))
tables.append(T('milestones', 'Net worth milestones', 'Net Worth Milestones',
    'Round net worth levels you want to reach: the month each was reached and, for the rest, the months to go at your monthly amount and example growth.', [
    C('milestone', 'Milestone', 'text', 22, required=True), C('amount', 'Amount', 'money', 12),
    CA('reached_on', 'Reached or expected on', 'date', 'IF(%s>={col:amount},IF(%s=0,MIN(%s),EDATE(%s,1)),IF({col:months_to_go}="","",EDATE(%s,{col:months_to_go})))' % (NWNOW, _LB, R('nwm', 'month'), _LB, MS), 14),
    CA('months_to_go', 'Months to go', 'int', 'IF(%s>={col:amount},0,IFERROR(ROUNDUP(NPER(MAX({set:growth_rate},0.000000001)/12,{set:monthly_contribution},%s,-{col:amount}),0),""))' % (NWNOW, NWNOW), 11)],
    D.milestones_d(), 30))
# 10 projection inputs
tables.append(T('proj_inputs', 'Projection inputs', 'Projection Inputs',
    'The numbers behind the projection and the target tools; growth and the monthly amount sit in Settings. An example, not a forecast.', [
    LST('item', 'Input', 'pitem', 44, required=True), C('value', 'Value', 'num', 12), C('note', 'Note', 'text', 40)], D.proj_inputs_d(), 12))
# 11 projection
tables.append(T('projection', 'Projection', 'Net Worth Projection, an Example',
    'Sixty months ahead from your monthly amount and the example growth in Settings: contributions, growth, the balance and net worth at three growth rates. An example, not a forecast.', [
    C('month', 'Month', 'date', 11, required=True), LST('year_no', 'Projection year', 'pyear', 12),
    CA('ahead', 'Months ahead', 'int', '(YEAR({col:month})-YEAR(%s))*12+MONTH({col:month})-MONTH(%s)' % (MS, MS), 10),
    CA('contribution', 'Contributed so far', 'money', '{set:monthly_contribution}*{col:ahead}', 13),
    CA('balance', 'Savings and investments', 'money', 'FV({set:growth_rate}/12,{col:ahead},-{set:monthly_contribution},-%s)' % START, 14),
    CA('growth', 'Growth earned so far', 'money', '{col:balance}-%s-{col:contribution}' % START, 13),
    CA('low', 'Balance at lower growth', 'money', 'FV(MAX({set:growth_rate}-%s,0)/12,{col:ahead},-{set:monthly_contribution},-%s)' % (GAP, START), 14),
    CA('high', 'Balance at higher growth', 'money', 'FV(({set:growth_rate}+%s)/12,{col:ahead},-{set:monthly_contribution},-%s)' % (GAP, START), 14),
    CA('nw_example', 'Net worth, an example', 'money', '{col:balance}+%s-(%s)' % (NWNOW, POT()), 14), CA('years', 'Years ahead', 'num', 'ROUND({col:ahead}/12,1)', 9),
    HH(), N2(), PH('Partner 2', 'p2_phone', 'Partner 2 phone')], D.projection_d(), 80))
# 12 bills
tables.append(T('bills', 'Bills', 'Bills and the Account They Leave From',
    'Every recurring bill with the account it leaves from; the next due date and the monthly cost fill in by themselves.', [
    C('bill_id', 'Bill ID', 'text', 9, required=True), C('bill', 'Bill', 'text', 26), LST('category', 'Category', 'category', 20), C('amount', 'Amount', 'money', 11), C('due_day', 'Due day', 'int', 8),
    LST('cycle', 'Cycle', 'cycle', 10), C('due_month', 'Due month, yearly', 'int', 10), REF('account_id', 'Account ID', 'accounts.account_id', 10), C('autopay', 'Autopay', 'bool', 9),
    CA('account', 'Account', 'text', LOOK('accounts.account', 'accounts.account_id', 'account_id'), 24), CA('owner', 'Owner', 'text', LOOK('accounts.owner', 'accounts.account_id', 'account_id'), 11),
    CA('monthly_cost', 'Cost a month', 'money', 'IF({col:cycle}=%s,{col:amount},{col:amount}/12)' % tok('cycle', 'Monthly'), 12),
    CA('next_due', 'Next due', 'date', 'IF({col:cycle}=%s,IF(DAY({today})<={col:due_day},DATE(YEAR({today}),MONTH({today}),{col:due_day}),DATE(YEAR({today}),MONTH({today})+1,{col:due_day})),'
       'IF(DATE(YEAR({today}),{col:due_month},{col:due_day})>={today},DATE(YEAR({today}),{col:due_month},{col:due_day}),DATE(YEAR({today})+1,{col:due_month},{col:due_day})))' % tok('cycle', 'Monthly'), 11)],
    D.bills_d(), 60))
# 13 joint and separate map
def BL(c): return LOOK('bills.%s' % c, 'bills.bill', 'bill')
tables.append(T('map', 'Joint and separate map', 'Joint and Separate Accounts Map',
    'Every bill by the account it leaves from: owner, amount, due date and who pays; read it before each payday to see what the joint account must cover.', [
    REF('bill', 'Bill', 'bills.bill', 26, required=True), CA('account_id', 'Account ID', 'text', BL('account_id'), 10), CA('account', 'Account', 'text', BL('account'), 24),
    CA('owner', 'Owner', 'text', BL('owner'), 11), CA('amount', 'Amount', 'money', BL('amount'), 11), CA('due_day', 'Due day', 'int', BL('due_day'), 8),
    CA('due_date', 'Next due', 'date', BL('next_due'), 11),
    CA('who_pays', 'Who pays', 'text', 'IF({col:owner}=%s,%s,IF({col:owner}=%s,{set:partner1},{set:partner2}))' % (PJ, V('Both partners'), PP1), 16),
    CA('from_joint', 'From joint', 'int', 'IF({col:owner}=%s,1,0)' % PJ, 9), CA('date', 'Updated on', 'date', '{today}', 11), HH(),
    PH('Grandparent', 'member_phone', 'Household member phone'), PH('Insurance agent', 'insurance_phone', 'Insurance agent phone'), PH('Landlord', 'landlord_phone', 'Landlord phone'),
    PH('Utility company', 'utility_phone', 'Utility company phone')], D.map_d(), 40))
# 14 transfers
tables.append(T('transfers', 'Transfers', 'Transfers Between Your Accounts',
    'Each transfer between your own accounts: personal spending money to the partners and settle up payments; the account names and the month fill in by themselves.', [
    C('transfer_id', 'Transfer ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    REF('from_account', 'From account ID', 'accounts.account_id', 12), REF('to_account', 'To account ID', 'accounts.account_id', 12), C('amount', 'Amount', 'money', 11), LST('purpose', 'Purpose', 'purpose', 22),
    CA('from_name', 'From account', 'text', LOOK('accounts.account', 'accounts.account_id', 'from_account'), 22), CA('to_name', 'To account', 'text', LOOK('accounts.account', 'accounts.account_id', 'to_account'), 22),
    HH(), PH('Bank branch', 'bank_phone', 'Bank branch phone')], D.transfers_d(), 300))
# 15 payday transfers plan
_TH = 'IF({col:partner}=%s,{set:p1_takehome},{set:p2_takehome})' % P1
tables.append(T('payplan', 'Payday transfers plan', 'Payday Transfers Plan',
    'What each partner moves to the joint account each payday, on the agreed split or an income share, and what is left to spend after the transfer and their own bills.', [
    C('plan_id', 'Plan ID', 'text', 9, required=True), LST('partner', 'Partner', 'payer', 11), LST('basis', 'Basis', 'basis', 14), LST('rhythm', 'Pay rhythm', 'payfreq', 16),
    CA('share', 'Share of the joint need', 'pct', 'IF({col:basis}=%s,IF({col:partner}=%s,{set:agreed_p1_share},1-{set:agreed_p1_share}),%s/({set:p1_takehome}+{set:p2_takehome}))' % (tok('basis', 'Agreed split'), P1, _TH), 12),
    CA('transfer_month', 'Transfer a month', 'money', '{set:joint_monthly}*{col:share}', 12),
    CA('paydays', 'Paydays a month', 'num', 'IF({col:rhythm}=%s,52/12,IF({col:rhythm}=%s,26/12,IF({col:rhythm}=%s,2,1)))' % (tok('payfreq', 'Weekly'), tok('payfreq', 'Every two weeks'), tok('payfreq', 'Twice a month')), 10),
    CA('transfer_payday', 'Transfer each payday', 'money', 'ROUND({col:transfer_month}/{col:paydays},2)', 12), CA('takehome', 'Take-home a month', 'money', _TH, 12),
    CA('keeps', 'Kept after the transfer', 'money', '{col:takehome}-{col:transfer_month}', 12),
    CA('own_bills', 'Own bills a month', 'money', 'SUMIFS(%s,%s,IF({col:partner}=%s,%s,%s))' % (R('bills', 'monthly_cost'), R('bills', 'owner'), P1, PP1, PP2), 12),
    CA('left', 'Left to spend', 'money', '{col:keeps}-{col:own_bills}', 12), CA('day', 'Next payday, day', 'int', 'DAY({set:next_payday})', 9), CA('date', 'Next payday', 'date', '{set:next_payday}', 11),
    HH(), N1(), N2(), PH('Partner 1', 'p1_phone', 'Partner 1 phone'), PH('Partner 2', 'p2_phone', 'Partner 2 phone'), PH('Bank branch', 'bank_phone', 'Bank branch phone')], D.payplan_d(), 30))
# 16 personal spending money
tables.append(T('pspend', 'Personal spending money', 'Personal Spending Money by Month',
    'Each month and partner: the personal spending money transferred in, what the partner spent from their own account and what is left.', [
    C('ps_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('partner', 'Partner', 'payer', 11), REF('account_id', 'Account ID', 'accounts.account_id', 10), C('other_in', 'Other money in', 'money', 12),
    CA('transfer_in', 'Transferred in', 'money', 'SUMIFS(%s,%s,{col:month},%s,{col:account_id},%s,%s)' % (R('transfers', 'amount'), R('transfers', 'month'), R('transfers', 'to_account'), R('transfers', 'purpose'), tok('purpose', 'Personal spending money')), 12),
    CA('spent', 'Spent', 'money', 'SUMIFS(%s,%s,{col:account_id},%s,">="&{col:month},%s,"<"&EDATE({col:month},1))' % (R('tx', 'amount'), R('tx', 'account_id'), R('tx', 'date'), R('tx', 'date')), 12),
    CA('left', 'Left', 'money', '{col:transfer_in}+{col:other_in}-{col:spent}', 12),
    CA('status', 'Status', 'text', 'IF({col:left}<0,%s,%s)' % (V('Over the money'), V('Within the money')), 16),
    HH(), N1(), N2(), PH('Partner 1', 'p1_phone', 'Partner 1 phone'), PH('Partner 2', 'p2_phone', 'Partner 2 phone')], D.pspend_d(), 80, [A('status', '= ' + V('Over the money'), 'warn')]))
# 17 account activity
_T90 = '%s,">="&({today}-90)'
def _E(tbl, acc, dcol): return 'COUNTIFS(%s,{col:account_id},%s,">="&({today}-90))' % (R(tbl, acc), R(tbl, dcol))
def _LU(tbl, acc): return 'SUMPRODUCT(MAX((%s={col:account_id})*%s))' % (R(tbl, acc), R(tbl, 'date'))
_LUX = 'MAX(%s,%s,%s)' % (_LU('tx', 'account_id'), _LU('transfers', 'from_account'), _LU('transfers', 'to_account'))
tables.append(T('activity', 'Account activity', 'Account Activity, Last 90 Days',
    'Each account: payments and transfers in the last 90 days, money in and out, the last day it was used and how its balance moved; a quiet account is flagged to review.', [
    REF('account', 'Account', 'accounts.account', 26, required=True), CA('account_id', 'Account ID', 'text', LKA('account_id'), 10),
    CA('events_90', 'Payments and transfers, 90 days', 'int', '%s+%s+%s' % (_E('tx', 'account_id', 'date'), _E('transfers', 'from_account', 'date'), _E('transfers', 'to_account', 'date')), 14),
    CA('money_in', 'Money in, 90 days', 'money', 'SUMIFS(%s,%s,{col:account_id},%s,">="&({today}-90))' % (R('transfers', 'amount'), R('transfers', 'to_account'), R('transfers', 'date')), 13),
    CA('money_out', 'Money out, 90 days', 'money', 'SUMIFS(%s,%s,{col:account_id},%s,">="&({today}-90))+SUMIFS(%s,%s,{col:account_id},%s,">="&({today}-90))' % (
        R('tx', 'amount'), R('tx', 'account_id'), R('tx', 'date'), R('transfers', 'amount'), R('transfers', 'from_account'), R('transfers', 'date')), 13),
    CA('last_used', 'Last used', 'date', 'IF(%s=0,"",%s)' % (_LUX, _LUX), 11),
    CA('balance_move', 'Balance move, 3 months', 'money', 'SUMIFS(%s,%s,{col:account})-SUMIFS(%s,%s,{col:account},%s,EDATE(%s,-3))' % (R('bnow', 'balance'), R('bnow', 'account'), NWB, R('networth', 'account'), R('networth', 'month'), LM), 14),
    CA('idle', 'Quiet', 'int', 'IF(AND({col:events_90}=0,ABS({col:balance_move})<{set:balance_tol}),1,0)', 8),
    CA('flag', 'Review or keep', 'text', 'IF({col:idle}=1,%s,%s)' % (V('Review'), V('Keep')), 12)], D.activity_d(), 30, [A('flag', '= ' + V('Review'), 'warn')]))
# 18 balance check
tables.append(T('bcheck', 'Balance check', 'Balance Check Against Statements',
    'Type each statement balance: the difference from the balance the workbook holds and a flag; a blank statement shows as missing.', [
    REF('account_id', 'Account ID', 'accounts.account_id', 10, required=True), C('statement', 'Statement balance', 'money', 14), C('statement_date', 'Statement date', 'date', 12),
    CA('account', 'Account', 'text', LOOK('accounts.account', 'accounts.account_id', 'account_id'), 24),
    CA('calculated', 'Balance in the workbook', 'money', 'SUMIFS(%s,%s,{col:account_id})' % (R('bnow', 'balance'), R('bnow', 'account_id')), 14),
    CA('difference', 'Difference', 'money', 'IF({col:statement}="","",{col:statement}-{col:calculated})', 12),
    CA('flag', 'Check', 'text', 'IF({col:statement}="",%s,IF(ABS({col:difference})<={set:balance_tol},%s,%s))' % (V('Missing'), V('Matches'), V('Check')), 11),
    HH(), PH('Bank branch', 'bank_phone', 'Bank branch phone')], D.bcheck_d(), 30, [A('flag', '= ' + V('Check'), 'bad'), A('flag', '= ' + V('Matches'), 'good'), A('flag', '= ' + V('Missing'), 'warn')]))
# 19 account owners (owner x now / 3 / 6 / 12 months back)
_OB = 'EDATE(%s,-{col:months_back})' % LM
def OS(side): return 'SUMIFS(%s,%s,{col:owner},%s,%s,%s,%s)' % (NWB, R('networth', 'owner'), R('networth', 'month'), _OB, R('networth', 'side'), side)
tables.append(T('owners', 'Account owners', 'Net Worth by Account Owner',
    'Assets, liabilities and net worth of each owner (partner 1, partner 2, joint) now and 3, 6 and 12 months back.', [
    C('own_id', 'Row ID', 'text', 9, required=True), LST('owner', 'Owner', 'person', 11), C('months_back', 'Months back', 'int', 9), CA('assets', 'Assets', 'money', OS(A_), 13),
    CA('liabilities', 'Liabilities', 'money', OS(L_), 13), CA('net', 'Net worth', 'money', '{col:assets}-{col:liabilities}', 13),
    CA('bills_amount', 'Bills a month from its accounts', 'money', 'SUMIFS(%s,%s,{col:owner})' % (R('bills', 'monthly_cost'), R('bills', 'owner')), 14)], D.owners_d(), 30))
# 20 transactions
tables.append(T('tx', 'Transactions', 'Payments from Your Accounts',
    'The payments paid from each account, one row each; the personal spending money pages and the account activity read from it.', [
    C('tx_id', 'Payment ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    REF('account_id', 'Account ID', 'accounts.account_id', 10), C('payee', 'Payee', 'text', 22), LST('category', 'Category', 'category', 20), C('amount', 'Amount', 'money', 11),
    LST('paid_by', 'Paid by', 'payer', 11)], D.tx_d(), 900))
assert len(tables) == 20
