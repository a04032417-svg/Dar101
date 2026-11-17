"""Household Finance suite part 6: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf6_lists import *
from hf6_tables import R, MS, LM, NWM, NWNOW, POT, A_, L_, CHKG, SAV, CARD, RET, BRK, PJ, PP1, PP2
import hf6_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, lab): return IN(k, label, 'list', key(lst, lab), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
BN = lambda c: R('bnow', c)
SP = '&" "&'
def BACK(n): return 'EDATE(%s,-%s)' % (LM, n)
def ASS(m): return 'SUMIFS(%s,%s,%s)' % (R('nwm', 'assets'), R('nwm', 'month'), m)
def LIA(m): return 'SUMIFS(%s,%s,%s)' % (R('nwm', 'liabilities'), R('nwm', 'month'), m)
def RATIO(m): return 'IFERROR(%s/%s,0)' % (LIA(m), ASS(m))
def S_(*parts): return SP.join(parts)
tools = []

# 1 net worth now
PREV = NWM(BACK('{in:months_back}')); CH1 = '(%s-%s)' % (NWNOW, PREV)
tools.append(TOOL('nw_now', 'Net Worth Now', 'Where does net worth stand against an earlier month',
    'Assets less liabilities at your latest typed month, with the change since the month you pick and since a year ago.', [I('months_back', 'Months back to compare with', 1, 'int')], [
    O('Net worth now', 'money', NWNOW), O('Total assets', 'money', ASS(LM)), O('Total liabilities', 'money', LIA(LM)), O('Net worth in the month compared', 'money', PREV), O('Change since then', 'money', CH1),
    O('Change since then, share', 'pct', 'IFERROR(%s/ABS(%s),0)' % (CH1, PREV)), O('Net worth a year ago', 'money', NWM(BACK(12))), O('Change on last year', 'money', '%s-%s' % (NWNOW, NWM(BACK(12)))),
    O('Verdict', 'text', 'IF(%s>=0,%s,%s)&" "&%s&" "&%s&" "&%s' % (CH1, S_(V('Up'), 'ROUND(%s,0)' % CH1), S_(V('Down'), 'ROUND(-%s,0)' % CH1), V('since'), '{in:months_back}', V('month(s) ago')))],
    GR('What if you compare with', ('1 month ago', {'months_back': 1}), ('3 months ago', {'months_back': 3}), ('6 months ago', {'months_back': 6}), ('12 months ago', {'months_back': 12}), ('24 months ago', {'months_back': 24}))))
# 2 by account group
GBAL = lambda mb: 'SUMIFS(%s,%s,{in:group},%s,%s)' % (R('grp', 'balance'), R('grp', 'group'), R('grp', 'months_back'), mb)
GSH = 'SUMIFS(%s,%s,{in:group},%s,0)' % (R('grp', 'share_nw'), R('grp', 'group'), R('grp', 'months_back'))
tools.append(TOOL('nw_group', 'Net Worth by Group', 'Which account group carries net worth',
    'Pick an account group: its balance now and a year ago, its share of assets and its share of net worth.', [IL('group', 'Account group', 'atype', 'Savings')], [
    O('Balance now', 'money', GBAL('0')), O('Balance a year ago', 'money', GBAL('12')), O('Change on last year', 'money', '%s-%s' % (GBAL('0'), GBAL('12'))),
    O('Share of assets, 0 for debts', 'pct', 'SUMIFS(%s,%s,{in:group},%s,0)' % (R('grp', 'share_assets'), R('grp', 'group'), R('grp', 'months_back'))), O('Share of net worth', 'pct', GSH),
    O('Share of net worth a year ago', 'pct', 'SUMIFS(%s,%s,{in:group},%s,12)' % (R('grp', 'share_nw'), R('grp', 'group'), R('grp', 'months_back'))),
    O('Net worth now', 'money', NWNOW), O('Verdict', 'text', '{in:group}&" "&%s&" "&ROUND(%s*100,0)&"%% "&%s' % (V('is'), GSH, V('of net worth')))]))
# 3 change explainer
EF = BN('nw_effect')
UP = 'INDEX(%s,MATCH(LARGE(%s,1),%s,0))' % (BN('account'), EF, EF); DN = 'INDEX(%s,MATCH(SMALL(%s,1),%s,0))' % (BN('account'), EF, EF)
DRV = 'IF(LARGE(%s,1)>=-SMALL(%s,1),%s,%s)' % (EF, EF, UP, DN)
tools.append(TOOL('nw_explain', 'Net Worth Change Explainer', 'Which accounts moved net worth this month',
    'The accounts that pushed net worth up or down against last month, so a jump is explained in one line.', [I('ignore_below', 'Ignore moves smaller than', 0)], [
    O('Net worth change on last month', 'money', 'SUM(%s)' % EF), O('Biggest rise: account', 'text', UP), O('Biggest rise: amount', 'money', 'LARGE(%s,1)' % EF),
    O('Biggest fall: account', 'text', DN), O('Biggest fall: amount', 'money', 'SMALL(%s,1)' % EF), O('Second rise: account', 'text', 'INDEX(%s,MATCH(LARGE(%s,2),%s,0))' % (BN('account'), EF, EF)),
    O('Accounts that moved more than that', 'int', 'COUNTIFS(%s,">"&{in:ignore_below})+COUNTIFS(%s,"<"&-{in:ignore_below})' % (EF, EF)),
    O('Biggest mover as a share of all moves', 'pct', 'IFERROR(MAX(LARGE(%s,1),-SMALL(%s,1))/(SUMIF(%s,">0")-SUMIF(%s,"<0")),0)' % (EF, EF, EF, EF)),
    O('Verdict', 'text', '%s&" "&%s' % (DRV, V('drove the change')))],
    GR('What if you ignore moves under', ('0', {'ignore_below': 0}), ('50', {'ignore_below': 50}), ('100', {'ignore_below': 100}), ('250', {'ignore_below': 250}), ('500', {'ignore_below': 500}))))
# 4 snapshot check
TYPED = 'COUNTIFS(%s,EDATE(%s,-{in:months_back}))' % (R('networth', 'month'), MS)
MISS = 'MAX(0,COUNTA(%s)-%s)' % (R('accounts', 'account_id'), TYPED)
tools.append(TOOL('snapshot', 'Month-end Snapshot Check', 'Is every account typed for the month',
    'Counts the accounts that have a balance row for the month and names the account typed longest ago; a missing balance understates net worth.', [I('months_back', 'Months back, 0 = this month', 0, 'int')], [
    O('Accounts in the list', 'int', 'COUNTA(%s)' % R('accounts', 'account_id')), O('Accounts typed for the month', 'int', TYPED), O('Accounts missing', 'int', MISS),
    O('Account typed longest ago', 'text', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (BN('account'), BN('last_month'), BN('last_month'))), O('Its latest month typed', 'date', 'MIN(%s)' % BN('last_month')),
    O('Latest month typed overall', 'date', LM), O('Days since the latest balance date', 'int', '{today}-MAX(%s)' % R('networth', 'as_of')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (MISS, V('Complete'), MISS, V('accounts missing')))],
    GR('What if you check', ('This month', {'months_back': 0}), ('Last month', {'months_back': 1}), ('2 months back', {'months_back': 2}), ('3 months back', {'months_back': 3}), ('6 months back', {'months_back': 6}))))
# 5 projection
ST_T = 'IF({in:start}>0,{in:start},%s)' % POT()
FVT = 'FV({in:growth}/12,{in:years}*12,-{in:contribution},-%s)' % ST_T
NWEX = '(%s+%s-(%s))' % (FVT, NWNOW, POT())
tools.append(TOOL('projection_tool', 'Net Worth Projection', 'What could net worth be in a few years, as an example',
    'Your monthly amount and an assumed yearly growth, both typed by you, projected forward; an example from your numbers, not a forecast.', [
    I('contribution', 'Monthly amount you add', 900), I('growth', 'Assumed yearly growth, an example', 0.05, 'pct'), I('years', 'Years ahead', 5, 'int'), I('start', 'Starting amount, 0 = savings and investments now', 0)], [
    O('Starting amount', 'money', ST_T), O('Added over the years', 'money', '{in:contribution}*12*{in:years}'), O('Balance after the years', 'money', FVT),
    O('Growth earned, an example', 'money', '%s-%s-{in:contribution}*12*{in:years}' % (FVT, ST_T)), O('Net worth now', 'money', NWNOW), O('Net worth after the years, an example', 'money', NWEX),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&" "&%s&" "&{in:years}&" "&%s' % (V('An example:'), NWEX, V('in'), V('years, not a forecast')))],
    GR('What if the years are', ('1 year', {'years': 1}), ('3 years', {'years': 3}), ('5 years', {'years': 5}), ('10 years', {'years': 10}), ('20 years', {'years': 20}))))
# 6 sensitivity
def FVG(g): return 'FV(MAX(%s,0)/12,{in:years}*12,-{in:contribution},-%s)' % (g, POT())
tools.append(TOOL('sensitivity', 'Projection Sensitivity', 'How much does the assumed growth change the example',
    'The same projection at growth minus and plus the gap you type: a range, an example and not a forecast.', [
    I('contribution', 'Monthly amount you add', 900), I('growth', 'Assumed yearly growth, an example', 0.05, 'pct'), I('years', 'Years ahead', 10, 'int'), I('gap', 'Growth gap either side', 0.02, 'pct')], [
    O('Balance at lower growth', 'money', FVG('{in:growth}-{in:gap}')), O('Balance at the growth you typed', 'money', FVG('{in:growth}')), O('Balance at higher growth', 'money', FVG('{in:growth}+{in:gap}')),
    O('Spread between low and high', 'money', '%s-%s' % (FVG('{in:growth}+{in:gap}'), FVG('{in:growth}-{in:gap}'))), O('Added with no growth', 'money', '%s+{in:contribution}*12*{in:years}' % POT()),
    O('Growth share of the example balance', 'pct', 'IFERROR(1-(%s+{in:contribution}*12*{in:years})/%s,0)' % (POT(), FVG('{in:growth}'))),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&" "&%s&" "&ROUND(%s,0)&", "&%s' % (V('Range'), FVG('{in:growth}-{in:gap}'), V('to'), FVG('{in:growth}+{in:gap}'), V('an example')))],
    GR('What if the gap is', ('1 point', {'gap': 0.01}), ('2 points', {'gap': 0.02}), ('3 points', {'gap': 0.03}), ('4 points', {'gap': 0.04}), ('5 points', {'gap': 0.05}))))
# 7 years to target
NP = 'IFERROR(NPER(MAX({in:growth},0.000000001)/12,{in:contribution},%s,-{in:target}),"")' % NWNOW
tools.append(TOOL('years_target', 'Years to a Net Worth Target', 'How long to reach a net worth level, as an example',
    'A closed-form estimate with the monthly amount and growth you type; an example from your numbers, not a forecast.', [
    I('target', 'Net worth target', 100000), I('contribution', 'Monthly amount you add', 900), I('growth', 'Assumed yearly growth, an example', 0.05, 'pct')], [
    O('Net worth now', 'money', NWNOW), O('Still to reach', 'money', 'MAX(0,{in:target}-%s)' % NWNOW), O('Months to the target', 'int', 'IF(%s="","",ROUNDUP(MAX(%s,0),0))' % (NP, NP)),
    O('Years to the target', 'num', 'IF(%s="","",ROUND(MAX(%s,0)/12,1))' % (NP, NP)), O('Month it could be reached', 'date', 'IF(%s="","",EDATE(%s,ROUNDUP(MAX(%s,0),0)))' % (NP, MS, NP)),
    O('Months with no growth', 'int', 'IF({in:contribution}>0,ROUNDUP(MAX(0,{in:target}-%s)/{in:contribution},0),"")' % NWNOW),
    O('Verdict', 'text', 'IF(%s>={in:target},%s,IF(%s="",%s,%s&" "&ROUND(MAX(%s,0)/12,1)&" "&%s))' % (NWNOW, V('Reached already'), NP, V('Not reachable at these numbers'), V('About'), NP, V('years at these numbers, an example')))],
    GR('What if you add a month', ('300', {'contribution': 300}), ('600', {'contribution': 600}), ('900', {'contribution': 900}), ('1200', {'contribution': 1200}), ('2000', {'contribution': 2000}))))
# 8 contribution for a target
PM = 'MAX(0,PMT(MAX({in:growth},0.000000001)/12,{in:years}*12,%s,-{in:target}))' % NWNOW
tools.append(TOOL('contribution_target', 'Contribution for a Target', 'How much to add each month to reach a level by a date',
    'The monthly amount that reaches the net worth you type within the years you give, at an example growth; an estimate from your numbers.', [
    I('target', 'Net worth target', 100000), I('years', 'Years to reach it', 8, 'int'), I('growth', 'Assumed yearly growth, an example', 0.05, 'pct'), I('max_monthly', 'Most you could add a month', 2500)], [
    O('Net worth now', 'money', NWNOW), O('Net worth if you add nothing', 'money', 'FV({in:growth}/12,{in:years}*12,0,-%s)' % NWNOW), O('Shortfall to the target', 'money', 'MAX(0,{in:target}-FV({in:growth}/12,{in:years}*12,0,-%s))' % NWNOW),
    O('Amount to add a month', 'money', PM), O('Added over the years', 'money', '%s*{in:years}*12' % PM), O('Share of your most a month', 'pct', 'IFERROR(%s/{in:max_monthly},0)' % PM),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s>{in:max_monthly},%s,%s&" "&ROUND(%s,0)&" "&%s))' % (PM, V('Covered'), PM, V('Date too soon'), V('Save'), PM, V('a month')))],
    GR('What if the years are', ('3 years', {'years': 3}), ('5 years', {'years': 5}), ('8 years', {'years': 8}), ('10 years', {'years': 10}), ('15 years', {'years': 15}))))
# 9 liquid net worth
LIQ = 'SUMIFS(%s,%s,%s)' % (R('alm', 'liquid_net'), R('alm', 'month'), LM)
CSH = 'SUMIFS(%s,%s,%s)' % (R('alm', 'cash_savings'), R('alm', 'month'), LM)
tools.append(TOOL('liquid_nw', 'Liquid Net Worth', 'How much could you reach without selling long-term money',
    'Cash and savings less card balances, against months of essential spending; a typical range, check your own numbers.', [I('months', 'Months of essential spending to cover', 3, 'int')], [
    O('Cash and savings', 'money', CSH), O('Card balances', 'money', 'SUMIFS(%s,%s,%s)' % (R('alm', 'cards'), R('alm', 'month'), LM)), O('Liquid net worth', 'money', LIQ),
    O('Essential spending a month', 'money', '{set:essential_monthly}'), O('Months of essentials covered', 'num', 'IFERROR(%s/{set:essential_monthly},0)' % LIQ),
    O('Needed for the months you pick', 'money', '{in:months}*{set:essential_monthly}'), O('Gap to that cover', 'money', 'MAX(0,{in:months}*{set:essential_monthly}-%s)' % LIQ),
    O('Liquid net worth a year ago', 'money', 'SUMIFS(%s,%s,%s)' % (R('alm', 'liquid_net'), R('alm', 'month'), BACK(12))),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)' % (V('Liquid net'), LIQ))],
    GR('What if you cover', ('1 month', {'months': 1}), ('3 months', {'months': 3}), ('6 months', {'months': 6}), ('9 months', {'months': 9}), ('12 months', {'months': 12}))))
# 10 debt against assets
DIFF = '(%s-%s)' % (RATIO(LM), RATIO(BACK(12)))
tools.append(TOOL('debt_assets', 'Debt Against Assets', 'Are debts growing faster than what you own',
    'Liabilities over assets now, 6 months ago and a year ago, so the trend is your own history, not a national figure.', [I('tolerance', 'Change under this counts as steady, points', 0.02, 'pct')], [
    O('Liabilities over assets now', 'pct', RATIO(LM)), O('Six months ago', 'pct', RATIO(BACK(6))), O('A year ago', 'pct', RATIO(BACK(12))), O('Change on last year, points', 'num', '%s*100' % DIFF),
    O('Total liabilities', 'money', LIA(LM)), O('Total assets', 'money', ASS(LM)), O('Liabilities a year ago', 'money', LIA(BACK(12))),
    O('Verdict', 'text', 'IF(%s<-{in:tolerance},%s,IF(%s>{in:tolerance},%s,%s))' % (DIFF, V('Falling'), DIFF, V('Rising'), V('Steady')))],
    GR('What if steady means under', ('1 point', {'tolerance': 0.01}), ('2 points', {'tolerance': 0.02}), ('5 points', {'tolerance': 0.05}), ('10 points', {'tolerance': 0.10}), ('15 points', {'tolerance': 0.15}))))
# 11 joint against separate
MJ = lambda f: 'COUNTIFS(%s,%s,%s,">="&{in:min_amount})' % (R('map', 'from_joint'), f, R('map', 'amount'))
tools.append(TOOL('joint_sep', 'Joint Against Separate Map', 'Which account does each bill leave from',
    'Counts and adds up the bills by the account they leave from, the joint account or a partner account.', [I('min_amount', 'Count bills of at least', 0)], [
    O('Bills from the joint account', 'int', MJ('1')), O('Bills from partner accounts', 'int', MJ('0')), O('A month from the joint account', 'money', 'SUMIFS(%s,%s,%s)' % (R('bills', 'monthly_cost'), R('bills', 'owner'), PJ)),
    O('A month from partner 1 accounts', 'money', 'SUMIFS(%s,%s,%s)' % (R('bills', 'monthly_cost'), R('bills', 'owner'), PP1)), O('A month from partner 2 accounts', 'money', 'SUMIFS(%s,%s,%s)' % (R('bills', 'monthly_cost'), R('bills', 'owner'), PP2)),
    O('Share of bills from the joint account', 'pct', 'IFERROR(SUMIFS(%s,%s,%s)/SUM(%s),0)' % (R('bills', 'monthly_cost'), R('bills', 'owner'), PJ, R('bills', 'monthly_cost'))),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&%s' % (MJ('1'), V('bills from joint'), MJ('0'), V('from partner accounts')))],
    GR('What if you count bills of at least', ('0', {'min_amount': 0}), ('50', {'min_amount': 50}), ('100', {'min_amount': 100}), ('500', {'min_amount': 500}), ('1000', {'min_amount': 1000}))))
# 12 payday transfer plan
TH12 = 'IF({in:partner}=%s,{set:p1_takehome},{set:p2_takehome})' % P1
SH12 = 'IF({in:basis}=%s,IF({in:partner}=%s,{set:agreed_p1_share},1-{set:agreed_p1_share}),%s/({set:p1_takehome}+{set:p2_takehome}))' % (tok('basis', 'Agreed split'), P1, TH12)
PD12 = 'IF({in:rhythm}=%s,52/12,IF({in:rhythm}=%s,26/12,IF({in:rhythm}=%s,2,1)))' % (tok('payfreq', 'Weekly'), tok('payfreq', 'Every two weeks'), tok('payfreq', 'Twice a month'))
OB12 = 'SUMIFS(%s,%s,IF({in:partner}=%s,%s,%s))' % (R('bills', 'monthly_cost'), R('bills', 'owner'), P1, PP1, PP2)
PP12 = 'ROUND({set:joint_monthly}*%s/%s,2)' % (SH12, PD12)
tools.append(TOOL('payday_plan', 'Payday Transfer Plan', 'How much goes to the joint account on each payday',
    'Each partner\'s share of what the joint account needs, split over the paydays of the pay rhythm, and what is left after their own bills.', [
    IL('partner', 'Partner', 'payer', 'Partner 2'), IL('basis', 'Basis', 'basis', 'Agreed split'), IL('rhythm', 'Pay rhythm', 'payfreq', 'Every two weeks')], [
    O('Share of the joint need', 'pct', SH12), O('Transfer a month', 'money', '{set:joint_monthly}*%s' % SH12), O('Paydays a month', 'num', PD12), O('Transfer each payday', 'money', PP12),
    O('Take-home a month', 'money', TH12), O('Own bills a month', 'money', OB12), O('Left to spend after the transfer and own bills', 'money', '%s-{set:joint_monthly}*%s-%s' % (TH12, SH12, OB12)),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&" "&%s' % (V('Transfer'), PP12, V('on payday')))]))
# 13 personal spending left
PSM = lambda c: 'SUMIFS(%s,%s,{in:partner},%s,EDATE(%s,-{in:months_back}))' % (R('pspend', c), R('pspend', 'partner'), R('pspend', 'month'), MS)
PSL = PSM('left')
tools.append(TOOL('personal_left', 'Personal Spending Money Left', 'How much of their own money does each partner have left',
    'The personal spending money transferred in for the month, what the partner spent from their own account and what is left, with the average of the last 3 months.', [
    IL('partner', 'Partner', 'payer', 'Partner 2'), I('months_back', 'Months back, 0 = this month', 0, 'int')], [
    O('Transferred in', 'money', PSM('transfer_in')), O('Spent', 'money', PSM('spent')), O('Left', 'money', PSL), O('Spent as a share of the transfer', 'pct', 'IFERROR(%s/%s,0)' % (PSM('spent'), PSM('transfer_in'))),
    O('Average left, last 3 months', 'money', 'SUMIFS(%s,%s,{in:partner},%s,">="&EDATE(%s,-3),%s,"<"&%s)/3' % (R('pspend', 'left'), R('pspend', 'partner'), R('pspend', 'month'), MS, R('pspend', 'month'), MS)),
    O('Spent in the last 3 months', 'money', 'SUMIFS(%s,%s,{in:partner},%s,">="&EDATE(%s,-3),%s,"<"&%s)' % (R('pspend', 'spent'), R('pspend', 'partner'), R('pspend', 'month'), MS, R('pspend', 'month'), MS)),
    O('Verdict', 'text', 'IF({in:partner}=%s,{set:partner1},{set:partner2})&" "&%s&" "&ROUND(%s,0)&" "&%s' % (P1, V('has'), PSL, V('left')))],
    GR('What if you look at', ('This month', {'months_back': 0}), ('Last month', {'months_back': 1}), ('2 months back', {'months_back': 2}), ('3 months back', {'months_back': 3}), ('6 months back', {'months_back': 6}))))
# 14 joint account cover
JB = 'SUMIFS(%s,%s,{set:joint_account})' % (BN('balance'), BN('account_id'))
BILLS_J = 'SUMIFS(%s,%s,{set:joint_account},%s,">="&{today},%s,"<"&{set:next_payday})' % (R('bills', 'amount'), R('bills', 'account_id'), R('bills', 'next_due'), R('bills', 'next_due'))
LOW = '(%s-%s-{in:daily_spend}*MAX(0,{set:next_payday}-{today})-{in:one_off})' % (JB, BILLS_J)
NEED = 'MAX(0,{set:cash_floor}-%s)' % LOW
FB = 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (R('bills', 'next_due'), R('bills', 'next_due'))
tools.append(TOOL('joint_cover', 'Joint Account Cover', 'Will the joint account stay above the floor until payday',
    'The joint balance less the bills due before the next payday and what you spend outside bills; the amount to move in and how soon is the verdict.', [
    I('daily_spend', 'Spending a day outside bills, your estimate', 15), I('one_off', 'One-off cost before payday', 0)], [
    O('Joint account balance now', 'money', JB), O('Next payday', 'date', '{set:next_payday}'), O('Days to payday', 'int', 'MAX(0,{set:next_payday}-{today})'), O('Bills due before payday', 'money', BILLS_J),
    O('Spending outside bills until payday', 'money', '{in:daily_spend}*MAX(0,{set:next_payday}-{today})'), O('Balance at payday, an estimate', 'money', LOW), O('Your cash floor', 'money', '{set:cash_floor}'),
    O('Amount to move to the joint account', 'money', NEED), O('First bill due', 'date', FB), O('Days to the first bill', 'int', 'IF(%s="","",%s-{today})' % (FB, FB)),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&ROUND(%s,0)&" "&%s&" "&MAX(0,IF(%s="",0,%s-{today}))&" "&%s,IF(%s<{set:cash_floor}*1.2,%s,%s))' % (NEED, V('Move'), NEED, V('to joint within'), FB, FB, V('days'), LOW, V('Tight'), V('Safe')))],
    GR('What if you spend a day', ('0', {'daily_spend': 0}), ('10', {'daily_spend': 10}), ('15', {'daily_spend': 15}), ('30', {'daily_spend': 30}), ('50', {'daily_spend': 50}))))
# 15 balance reconcile
DF = R('bcheck', 'difference')
BIGPOS = 'MAX(%s)' % DF; BIGNEG = 'MIN(%s)' % DF
BIGACC = 'IF(%s>=-%s,INDEX(%s,MATCH(%s,%s,0)),INDEX(%s,MATCH(%s,%s,0)))' % (BIGPOS, BIGNEG, R('bcheck', 'account'), BIGPOS, DF, R('bcheck', 'account'), BIGNEG, DF)
BIGAMT = 'IF(%s>=-%s,%s,%s)' % (BIGPOS, BIGNEG, BIGPOS, BIGNEG)
MATCHES = 'COUNTIFS(%s,"<="&{in:tolerance},%s,">="&-{in:tolerance})' % (DF, DF)
tools.append(TOOL('reconcile', 'Balance Reconcile', 'Does each statement match the balance in the workbook',
    'The statement balances you typed against the balances held here; the account with the largest difference is named.', [I('tolerance', 'A difference up to this amount matches', 1)], [
    O('Statements typed', 'int', 'COUNT(%s)' % R('bcheck', 'statement')), O('Statements missing', 'int', 'COUNTA(%s)-COUNT(%s)' % (R('bcheck', 'account_id'), R('bcheck', 'statement'))), O('Matching', 'int', MATCHES),
    O('To check', 'int', 'COUNT(%s)-%s' % (R('bcheck', 'statement'), MATCHES)), O('Largest difference: account', 'text', BIGACC), O('Largest difference: amount', 'money', BIGAMT),
    O('Total of the differences', 'money', 'SUM(%s)' % DF),
    O('Verdict', 'text', 'IF(COUNT(%s)-%s=0,%s,%s&" "&%s&" "&%s&" "&ROUND(%s,0))' % (R('bcheck', 'statement'), MATCHES, V('Matches'), V('Check'), BIGACC, V('by'), BIGAMT))],
    GR('What if a match is within', ('0.5', {'tolerance': 0.5}), ('1', {'tolerance': 1}), ('5', {'tolerance': 5}), ('15', {'tolerance': 15}), ('30', {'tolerance': 30}))))
# 16 account tidy
EV = R('activity', 'events_90')
FIRSTQ = 'INDEX(%s,MATCH(1,%s,0))' % (R('activity', 'account'), R('activity', 'idle'))
tools.append(TOOL('tidy', 'Account Tidy', 'Which accounts have gone quiet',
    'Accounts with no payment or transfer in 90 days and a flat balance are flagged to review or close; the rest are kept.', [I('min_events', 'Count accounts with fewer payments and transfers than', 1, 'int')], [
    O('Quiet accounts', 'int', 'SUM(%s)' % R('activity', 'idle')), O('Accounts with fewer than that', 'int', 'COUNTIFS(%s,"<"&{in:min_events})' % EV),
    O('Account with the fewest', 'text', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (R('activity', 'account'), EV, EV)), O('Its payments and transfers', 'int', 'MIN(%s)' % EV),
    O('Its balance move, 3 months', 'money', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (R('activity', 'balance_move'), EV, EV)), O('Accounts in the list', 'int', 'COUNTA(%s)' % R('activity', 'account')),
    O('Verdict', 'text', 'IF(SUM(%s)=0,%s,%s&" "&%s)' % (R('activity', 'idle'), V('Keep'), V('Review'), FIRSTQ))],
    GR('What if fewer than', ('1', {'min_events': 1}), ('2', {'min_events': 2}), ('5', {'min_events': 5}), ('10', {'min_events': 10}), ('20', {'min_events': 20}))))
# 17 compared with own history
PCT = lambda a, b: 'IFERROR((%s-%s)/ABS(%s),0)' % (a, b, b)
PCTY = PCT(NWNOW, NWM(BACK(12)))
AVG3 = '(%s+%s+%s)/3' % (NWM(LM), NWM(BACK(1)), NWM(BACK(2)))
tools.append(TOOL('own_history', 'Net Worth Against Own History', 'How does net worth compare with your own past',
    'Net worth now against the average of the last 3 months, the month you pick and a year ago; your own history is the benchmark.', [I('compare_months', 'Months back to compare with', 3, 'int')], [
    O('Net worth now', 'money', NWNOW), O('Average of the last 3 months', 'money', AVG3), O('Net worth in the month compared', 'money', NWM(BACK('{in:compare_months}'))),
    O('Change on that month, share', 'pct', PCT(NWNOW, NWM(BACK('{in:compare_months}')))), O('Net worth a year ago', 'money', NWM(BACK(12))), O('Change on last year', 'money', '%s-%s' % (NWNOW, NWM(BACK(12)))),
    O('Change on last year, share', 'pct', PCT(NWNOW, NWM(BACK(12)))),
    O('Verdict', 'text', 'IF(%s>=0,%s&" "&ROUND(%s*100,0),%s&" "&ROUND(-%s*100,0))&"%%"&" "&%s' % (PCTY, V('Up'), PCTY, V('Down'), PCTY, V('on last year')))],
    GR('What if you compare with', ('1 month ago', {'compare_months': 1}), ('2 months ago', {'compare_months': 2}), ('3 months ago', {'compare_months': 3}), ('6 months ago', {'compare_months': 6}), ('9 months ago', {'compare_months': 9}))))
# 18 savings spread
EMG = 'SUMIFS(%s,%s,{set:emergency_account})' % (BN('balance'), BN('account'))
SAVS = 'SUMIFS(%s,%s,%s)' % (BN('balance'), BN('type'), SAV)
RETB = 'SUMIFS(%s,%s,%s)' % (BN('balance'), BN('type'), RET)
BRKB = 'SUMIFS(%s,%s,%s)' % (BN('balance'), BN('type'), BRK)
SHE = 'IFERROR(%s/(%s),0)' % (EMG, POT())
tools.append(TOOL('savings_spread', 'Savings Spread', 'How do emergency, goals and retirement share what you hold',
    'The emergency fund, other savings, retirement and brokerage balances as shares of all savings and investments, and the emergency fund against months of essentials.', [
    I('months_target', 'Months of essentials you want in the emergency fund', 6, 'int')], [
    O('Emergency fund balance', 'money', EMG), O('Other savings', 'money', '%s-%s' % (SAVS, EMG)), O('Retirement', 'money', RETB), O('Brokerage', 'money', BRKB), O('All savings and investments', 'money', POT()),
    O('Emergency fund share of savings', 'pct', SHE), O('Months of essentials in the emergency fund', 'num', 'IFERROR(%s/{set:essential_monthly},0)' % EMG),
    O('Emergency fund against your target', 'pct', 'IFERROR(%s/({in:months_target}*{set:essential_monthly}),0)' % EMG),
    O('Verdict', 'text', '%s&" "&ROUND(%s*100,0)&"%% "&%s' % (V('Emergency fund is'), SHE, V('of savings')))],
    GR('What if you want', ('1 month', {'months_target': 1}), ('3 months', {'months_target': 3}), ('4 months', {'months_target': 4}), ('6 months', {'months_target': 6}), ('9 months', {'months_target': 9}))))
assert len(tools) == 18
