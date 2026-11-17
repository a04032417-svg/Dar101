"""Household Finance suite part 5: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf5_lists import *
from hf5_tables import R, MS, DEP, SPEND, EMERG, SINK, HIGH, MED, GL, CT, AC, RT, IC, CG, EAVG, EBAL, PPY
import hf5_data as D
import datetime as _dt


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, LITX(f))
def IL(k, label, lst, default): return IN(k, label, 'list', key(lst, default), list=lst)
AM = lambda c: R('annual_months', c)
RK = lambda c: R('goal_ranking', c)
def MONEY(x): return 'ROUND(%s,0)&""' % x
def PPYI(f): return 'IF(%s=%s,52,IF(%s=%s,26,IF(%s=%s,24,12)))' % (f, tok('payfreq', 'Weekly'), f, tok('payfreq', 'Every two weeks'), f, tok('payfreq', 'Twice a month'))
MONTHS = '"January","February","March","April","May","June","July","August","September","October","November","December"'
def MN(d): return 'CHOOSE(MONTH(%s),%s)' % (d, MONTHS)
def DT(months): return '{today}+ROUND((%s)*30.4375,0)' % months
G_ = {g['goal_id']: g for g in D.ALLGOALS}
INSG = G_['SG-02']
INS_DAYS = (_dt.date.fromisoformat(INSG['target_date']) - D.T0).days
tools = []

# 1 goals status
BN = 'COUNTIFS(%s,">0",%s,">="&{in:tol})' % (GL('behind_by'), GL('behind_by'))
BS = 'SUMIFS(%s,%s,">0",%s,">="&{in:tol})' % (GL('behind_by'), GL('behind_by'), GL('behind_by'))
tools.append(TOOL('goals_status', 'Goals Status', 'Which goals are behind and by how much',
    'Every goal with what is saved, what is left and the shortfall at its date if you keep the planned monthly amount: how many goals are behind and the total short. Estimates from your numbers.', [
    I('tol', 'Count a goal as behind when short by at least', 25)], [
    O('Goals tracked', 'int', 'COUNTIFS(%s,"<>")' % GL('goal_id')), O('Saved in goals', 'money', 'SUM(%s)' % GL('saved')), O('Targets', 'money', 'SUM(%s)' % GL('target')),
    O('Left to save', 'money', 'SUM(%s)' % GL('left')), O('Goals reached', 'int', 'SUM(%s)' % GL('is_reached')), O('Goals behind', 'int', BN), O('Short in total at the dates', 'money', BS),
    O('Goal with the biggest shortfall', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (GL('goal'), GL('behind_by'), GL('behind_by'))),
    O('Verdict', 'text', 'IF(%s=0,"All goals on track",%s&" goals behind, "&%s&" short")' % (BN, BN, MONEY(BS)))],
    GR('What if the limit for behind is', ('0', {'tol': 0}), ('25', {'tol': 25}), ('100', {'tol': 100}), ('250', {'tol': 250}), ('500', {'tol': 500}))))
# 2 goal set-aside per paycheck
PP2 = PPYI('{in:freq}')
tools.append(TOOL('goal_setaside', 'Goal Set-aside per Paycheck', 'How much to set aside each paycheck for a monthly amount',
    'A monthly goal amount turned into an amount for each paycheck, each week and each year for your pay rhythm, with all your goals together and the months that have an extra paycheck.', [
    I('monthly', 'Monthly amount for the goal', 400), IL('freq', 'Pay rhythm', 'payfreq', PAYDAY1_FREQ)], [
    O('Paychecks a year', 'int', PP2), O('Set aside per paycheck', 'money', 'ROUND({in:monthly}*12/%s,2)' % PP2), O('Set aside per week', 'money', 'ROUND({in:monthly}*12/52,2)'),
    O('Set aside per year', 'money', '{in:monthly}*12'), O('All planned goals together per paycheck', 'money', 'ROUND(SUMIFS(%s,%s,0)*12/%s,2)' % (GL('monthly_amount'), GL('is_reached'), PP2)),
    O('All needed amounts together per paycheck', 'money', 'ROUND(SUM(%s)*12/%s,2)' % (GL('needed_month'), PP2)),
    O('Months a year with an extra paycheck', 'int', 'IF(%s=52,4,IF(%s=26,2,0))' % (PP2, PP2)),
    O('Verdict', 'text', '"Set aside "&ROUND({in:monthly}*12/%s,2)&" per paycheck"' % PP2)],
    GR('What if you are paid', ('Weekly', {'freq': '=' + tok('payfreq', 'Weekly')}), ('Every two weeks', {'freq': '=' + tok('payfreq', 'Every two weeks')}), ('Twice a month', {'freq': '=' + tok('payfreq', 'Twice a month')}),
       ('Monthly', {'freq': '=' + tok('payfreq', 'Monthly')}))))
# 3 monthly amount solver
LEFT3 = 'MAX(0,{in:target}-{in:saved})'
GROW = 'POWER(1+{in:rate}/12,{in:months})'
WITHI = 'IF(%s=0,0,IF({in:months}<1,%s,IF({in:rate}=0,%s/{in:months},MAX(0,({in:target}-{in:saved}*%s)*({in:rate}/12)/(%s-1)))))' % (LEFT3, LEFT3, LEFT3, GROW, GROW)
tools.append(TOOL('amount_solver', 'Monthly Amount Solver', 'What monthly amount reaches the target by the date',
    'The monthly amount that reaches a target in a number of months, with and without a typed interest rate, set against what you can save a month. Estimates from your numbers, not a promise.', [
    I('target', 'Target', 9000), I('saved', 'Saved so far', 4750), I('months', 'Months until the date', 23, 'int'), I('rate', 'Yearly interest you expect, a typed number', 0.02, 'pct'), I('can', 'What you can save a month', 200)], [
    O('Left to save', 'money', LEFT3), O('Date of the goal', 'date', DT('{in:months}')), O('Monthly amount without interest', 'money', 'IF({in:months}<1,%s,%s/{in:months})' % (LEFT3, LEFT3)),
    O('Monthly amount with the interest', 'money', WITHI), O('Per paycheck with the interest', 'money', 'ROUND(%s*12/%s,2)' % (WITHI, PPY)),
    O('Over (+) or under (-) what you can save', 'money', '%s-{in:can}' % WITHI),
    O('Verdict', 'text', 'IF(%s=0,"Already saved",IF(%s<={in:can},"Save "&%s&" a month","Date too soon, needs "&%s&" a month"))' % (LEFT3, WITHI, MONEY(WITHI), MONEY(WITHI)))],
    GR('What if the date is', ('6 months', {'months': 6}), ('12 months', {'months': 12}), ('23 months', {'months': 23}), ('36 months', {'months': 36}), ('48 months', {'months': 48}))))
# 4 goal date finder
NM4 = 'IF(MAX(0,{in:target}-{in:saved})=0,0,IF({in:monthly}<=0,"",IF({in:rate}=0,(MAX(0,{in:target}-{in:saved}))/{in:monthly},NPER({in:rate}/12,-{in:monthly},-{in:saved},{in:target}))))'
tools.append(TOOL('goal_date', 'Goal Date Finder', 'When is the goal reached at this monthly amount',
    'The date a goal is reached at a typed monthly amount, with and without a typed interest rate. Estimates from your numbers.', [
    I('target', 'Target', 2400), I('saved', 'Saved so far', 1500), I('monthly', 'Monthly amount', 160), I('rate', 'Yearly interest you expect, a typed number', 0.02, 'pct')], [
    O('Left to save', 'money', 'MAX(0,{in:target}-{in:saved})'), O('Months without interest', 'int', 'IF({in:monthly}<=0,"",ROUNDUP(MAX(0,{in:target}-{in:saved})/{in:monthly},0))'),
    O('Months with the interest', 'int', 'IF(%s="","",ROUNDUP(%s,0))' % (NM4, NM4)), O('Date reached', 'date', 'IF(%s="","",%s)' % (NM4, DT('ROUNDUP(%s,0)' % NM4))),
    O('Saved each year at this amount', 'money', '{in:monthly}*12'), O('Verdict', 'text', 'IF(MAX(0,{in:target}-{in:saved})=0,"Already reached",IF(%s="","Add a monthly amount","Reached in "&ROUNDUP(%s,0)&" months"))' % (NM4, NM4))],
    GR('What if the monthly amount is', ('80', {'monthly': 80}), ('120', {'monthly': 120}), ('160', {'monthly': 160}), ('240', {'monthly': 240}), ('320', {'monthly': 320}))))
# 5 behind-by check
PLAN5 = '{in:target}*MIN(1,MAX(0,{today}-{in:start})/MAX(1,{in:end}-{in:start}))'
tools.append(TOOL('behind_check', 'Behind-by Check', 'Are we behind the straight-line plan to the date',
    'The amount you should have saved by today if you save evenly from the start date to the target date, against what you have: behind by, ahead by or on track.', [
    I('target', 'Target', INSG['target']), I('saved', 'Saved so far', INSG['saved']), I('start', 'Start date', INSG['start_date'], 'date'), I('end', 'Target date', INSG['target_date'], 'date')], [
    O('Days in the plan', 'int', '{in:end}-{in:start}'), O('Days passed', 'int', 'MAX(0,{today}-{in:start})'), O('Share of the time passed', 'pct', 'MIN(1,MAX(0,{today}-{in:start})/MAX(1,{in:end}-{in:start}))'),
    O('Straight-line plan so far', 'money', 'ROUND(%s,2)' % PLAN5), O('Behind by', 'money', 'ROUND(MAX(0,%s-{in:saved}),2)' % PLAN5), O('Ahead by', 'money', 'ROUND(MAX(0,{in:saved}-%s),2)' % PLAN5),
    O('Share of the plan saved', 'pct', 'IFERROR({in:saved}/(%s),0)' % PLAN5), O('Days left', 'int', 'MAX(0,{in:end}-{today})'),
    O('Verdict', 'text', 'IF(%s-{in:saved}>=1,"Behind by "&%s,"On track")' % (PLAN5, MONEY('%s-{in:saved}' % PLAN5)))],
    GR('What if you have saved', ('400', {'saved': 400}), ('600', {'saved': 600}), ('900', {'saved': 900}), ('1200', {'saved': 1200}), ('1260', {'saved': 1260}))))
# 6 goal ranking
tools.append(TOOL('goal_rank', 'Goal Ranking', 'Which goal do we fund first',
    'Goals ranked behind first, then by priority and days left: the first three to fund, their shortfalls and how many goals fall due soon. Estimates from your numbers.', [
    I('window', 'Goals due within this many days count as soon', 90, 'int')], [
    O('Fund first', 'text', 'IFERROR(INDEX(%s,1)&"","")' % RK('goal')), O('Left to save on the first', 'money', 'IFERROR(INDEX(%s,1),0)' % RK('left')), O('Behind by on the first', 'money', 'IFERROR(INDEX(%s,1),0)' % RK('behind_by')),
    O('Fund second', 'text', 'IFERROR(INDEX(%s,2)&"","")' % RK('goal')), O('Fund third', 'text', 'IFERROR(INDEX(%s,3)&"","")' % RK('goal')),
    O('Goals due within the window', 'int', 'COUNTIFS(%s,">="&{today},%s,"<="&{today}+{in:window})' % (GL('open_date'), GL('open_date'))),
    O('Short on those goals', 'money', 'SUMIFS(%s,%s,">="&{today},%s,"<="&{today}+{in:window})' % (GL('behind_by'), GL('open_date'), GL('open_date'))),
    O('Verdict', 'text', '"Fund "&IFERROR(INDEX(%s,1)&"","")&" first"' % RK('goal'))],
    GR('What if soon means', ('30 days', {'window': 30}), ('60 days', {'window': 60}), ('90 days', {'window': 90}), ('180 days', {'window': 180}), ('365 days', {'window': 365}))))
# 7 sinking fund top-up
DEP7 = 'ROUNDDOWN({in:days}/30.4375,0)'
SH7 = 'MAX(0,MAX(0,{in:target}-{in:saved})-{in:monthly}*%s)' % DEP7
tools.append(TOOL('fund_topup', 'Sinking Fund Top-up', 'How much do we add once to close the shortfall',
    'The one-off amount that closes a sinking fund shortfall before its date, after the planned monthly deposits, and the monthly amount that would close it instead.', [
    I('target', 'Amount due', INSG['target']), I('saved', 'Saved so far', INSG['saved']), I('monthly', 'Planned monthly deposit', INSG['monthly_amount']), I('days', 'Days until it is due', INS_DAYS, 'int')], [
    O('Left to save', 'money', 'MAX(0,{in:target}-{in:saved})'), O('Deposits before the date', 'int', DEP7), O('Planned deposits before the date', 'money', '{in:monthly}*%s' % DEP7),
    O('Shortfall after the planned deposits', 'money', SH7), O('Add once by', 'date', '{today}+{in:days}'), O('Monthly amount that closes it without a top-up', 'money', 'MAX(0,{in:target}-{in:saved})/MAX(1,%s)' % DEP7),
    O('Verdict', 'text', 'IF(MAX(0,{in:target}-{in:saved})=0,"Fund is full",IF(%s=0,"Covered by the planned deposits","Add "&%s&" by the due date"))' % (SH7, MONEY(SH7)))],
    GR('What if the days until due are', ('14 days', {'days': 14}), ('30 days', {'days': 30}), ('49 days', {'days': 49}), ('90 days', {'days': 90}), ('180 days', {'days': 180}))))
# 8 annual costs to monthly
tools.append(TOOL('annual_monthly', 'Annual Costs to Monthly', 'What do the yearly costs mean each month and each paycheck',
    'Every yearly cost from the Annual costs sheet turned into an amount per month and per paycheck, with what is due in the next 90 days and what the funds already hold; add a cost to test it.', [
    I('add', 'A yearly cost to add and test', 360)], [
    O('Yearly costs listed', 'int', 'COUNTIFS(%s,"<>")' % AC('item_id')), O('Yearly total', 'money', 'SUM(%s)' % AC('amount')), O('Set aside per month', 'money', 'ROUND(SUM(%s)/12,2)' % AC('amount')),
    O('Set aside per paycheck', 'money', 'ROUND(SUM(%s)/%s,2)' % (AC('amount'), PPY)), O('Due in the next 90 days', 'money', 'SUMIFS(%s,%s,"<="&{today}+90)' % (AC('amount'), AC('next_due'))),
    O('Held in the funds now', 'money', 'SUM(%s)' % AC('fund_saved')), O('Costs with no fund', 'int', 'COUNTIFS(%s,%s)' % (AC('state'), tok('fstate', 'No fund set up'))),
    O('Per month with the added cost', 'money', 'ROUND((SUM(%s)+{in:add})/12,2)' % AC('amount')), O('Per paycheck with the added cost', 'money', 'ROUND((SUM(%s)+{in:add})/%s,2)' % (AC('amount'), PPY)),
    O('Verdict', 'text', '"Set aside "&ROUND(SUM(%s)/12,0)&" a month for "&COUNTIFS(%s,"<>")&" costs"' % (AC('amount'), AC('item_id')))],
    GR('What if the added cost is', ('Nothing', {'add': 0}), ('120', {'add': 120}), ('360', {'add': 360}), ('720', {'add': 720}), ('1200', {'add': 1200}))))
# 9 annual costs calendar
FM = 'IF(COUNT(%s)=0,"",MIN(%s))' % (AM('short_key'), AM('short_key'))
SHF = 'IF(%s="",0,SUMIFS(%s,%s,%s))' % (FM, AM('gap'), AM('month'), FM)
KF = 'IF(%s="",0,IFERROR(INDEX(%s,MATCH(%s,%s,0)),0))' % (FM, AM('months_out'), FM, AM('month'))
tools.append(TOOL('annual_calendar', 'Annual Costs Calendar', 'Which month do the yearly costs outrun the funds',
    'The next 12 months of yearly costs against what their funds will hold on each due date: the first month that is short, by how much, and what an extra monthly amount changes.', [
    I('extra', 'Extra you add a month to the short funds', 40)], [
    O('Costs due in the next 12 months', 'money', 'SUM(%s)' % AM('costs_due')), O('Months with a shortfall', 'int', 'COUNTIFS(%s,">0")' % AM('gap')), O('Short in total at the due dates', 'money', 'SUM(%s)' % AM('gap')),
    O('First month that is short', 'date', FM), O('Short in that month', 'money', SHF), O('Months from now', 'int', KF), O('Short in that month after the extra', 'money', 'MAX(0,%s-{in:extra}*%s)' % (SHF, KF)),
    O('Month with the biggest costs', 'text', 'IFERROR(%s&"","")' % MN('INDEX(%s,MATCH(MAX(%s),%s,0))' % (AM('month'), AM('costs_due'), AM('costs_due')))),
    O('Verdict', 'text', 'IF(%s="","Covered for the next 12 months","Short in "&%s&" by "&%s)' % (FM, MN(FM), MONEY(SHF)))],
    GR('What if you add a month', ('Nothing', {'extra': 0}), ('25', {'extra': 25}), ('50', {'extra': 50}), ('100', {'extra': 100}), ('200', {'extra': 200}))))
# 10 insurance premium fund
M10 = 'MATCH({in:goal},%s,0)' % GL('goal')
def X10(c): return 'IFERROR(INDEX(%s,%s),0)' % (GL(c), M10)
SH10 = 'MAX(0,%s-({in:extra}+%s)*%s)' % (X10('left'), X10('monthly_amount'), X10('months_left'))
NEED10 = '%s/MAX(1,%s)' % (X10('left'), X10('months_left'))
tools.append(TOOL('insurance_fund', 'Insurance Premium Fund', 'Will the premium fund be full by the due date',
    'The yearly car insurance premium against its fund and the days left: what is short at the date if you keep the planned monthly amount and what to add each month. Estimates from your numbers.', [
    I('goal', 'Fund (type the goal name)', D.INSURANCE, 'text'), I('extra', 'Extra you add a month', 0)], [
    O('Premium due', 'money', X10('target')), O('Saved in the fund', 'money', X10('saved')), O('Left to save', 'money', X10('left')), O('Due date', 'date', 'IFERROR(INDEX(%s,%s),"")' % (GL('target_date'), M10)),
    O('Days left', 'int', X10('days_left')), O('Planned monthly amount', 'money', X10('monthly_amount')), O('Short at the due date', 'money', 'ROUND(%s,2)' % SH10),
    O('Monthly amount needed to be full', 'money', 'ROUND(%s,2)' % NEED10), O('Add to the planned amount a month', 'money', 'ROUND(MAX(0,%s-%s-{in:extra}),2)' % (NEED10, X10('monthly_amount'))),
    O('Verdict', 'text', 'IF(%s=0,"Left to save is 0, fund is full",IF(%s<0.5,"Covered by the planned amount","Short by "&%s&", add "&%s&" a month"))' % (X10('left'), SH10, MONEY(SH10), MONEY('MAX(0,%s-%s-{in:extra})' % (NEED10, X10('monthly_amount')))))],
    GR('What if you add a month', ('Nothing', {'extra': 0}), ('100', {'extra': 100}), ('200', {'extra': 200}), ('300', {'extra': 300}), ('400', {'extra': 400}))))
# 11 emergency fund in months
BAL11 = '(%s+{in:add})' % EBAL
ESS11 = '(%s*(1-{in:cut}))' % EAVG
MON11 = 'IF(%s>0,%s/%s,0)' % (ESS11, BAL11, ESS11)
tools.append(TOOL('emergency_months', 'Emergency Fund in Months', 'How many months of spending does the fund cover',
    'The emergency fund divided by essential spending, set against the typical range of months in Settings (a typical range, check your own numbers); add money or cut spending to test.', [
    I('add', 'Money you add to the fund', 0), I('cut', 'Cut in essential spending you could make', 0, 'pct')], [
    O('Emergency fund balance', 'money', BAL11), O('Essential spending a month', 'money', 'ROUND(%s,0)' % ESS11), O('Months of essential spending covered', 'num', 'ROUND(%s,1)' % MON11),
    O('Low end of the typical range, months', 'int', '{set:emergency_low}'), O('High end of the typical range, months', 'int', '{set:emergency_high}'),
    O('Short of the low end', 'money', 'ROUND(MAX(0,{set:emergency_low}*%s-%s),0)' % (ESS11, BAL11)), O('Short of the high end', 'money', 'ROUND(MAX(0,{set:emergency_high}*%s-%s),0)' % (ESS11, BAL11)),
    O('Verdict', 'text', 'ROUND(%s,1)&" months, "&IF(%s<{set:emergency_low},"below",IF(%s<={set:emergency_high},"within","above"))&" the typical range of "&{set:emergency_low}&" to "&{set:emergency_high}' % (MON11, MON11, MON11))],
    GR('What if you add', ('Nothing', {'add': 0}), ('1000', {'add': 1000}), ('2500', {'add': 2500}), ('5000', {'add': 5000}), ('9000', {'add': 9000}))))
# 12 emergency fund target
GAP12 = 'MAX(0,{in:months}*%s-%s)' % (EAVG, EBAL)
MT12 = 'IF(%s=0,0,IF({in:monthly}<=0,"",ROUNDUP(%s/{in:monthly},0)))' % (GAP12, GAP12)
tools.append(TOOL('emergency_target', 'Emergency Fund Target', 'How long until the emergency fund reaches the target',
    'The target you choose in months of essential spending, what is missing and the months and date to reach it at a monthly amount you type.', [
    I('months', 'Target in months of essential spending', 3, 'num'), I('monthly', 'Monthly amount into the fund', 400)], [
    O('Essential spending a month', 'money', 'ROUND(%s,0)' % EAVG), O('Target amount', 'money', 'ROUND({in:months}*%s,0)' % EAVG), O('Saved in the emergency fund', 'money', EBAL),
    O('Gap to the target', 'money', 'ROUND(%s,0)' % GAP12), O('Months to reach the target', 'int', MT12), O('Date reached', 'date', 'IF(%s="","",%s)' % (MT12, DT(MT12))),
    O('Monthly amount to reach it in 12 months', 'money', 'ROUND(%s/12,0)' % GAP12), O('Verdict', 'text', 'IF(%s=0,"Target already reached",IF(%s="","Add a monthly amount","Reach target in "&%s&" months"))' % (GAP12, MT12, MT12))],
    GR('What if the monthly amount is', ('400', {'monthly': 400}), ('600', {'monthly': 600}), ('800', {'monthly': 800}), ('1000', {'monthly': 1000}), ('1500', {'monthly': 1500}))))
# 13 emergency fund shock test
BURN = 'MAX(0,%s*(1-{in:cut})-{in:left})' % EAVG
tools.append(TOOL('emergency_shock', 'Emergency Fund Shock Test', 'How many months does the fund cover if an income stops',
    'If one income stops, the monthly drain on the emergency fund after the income that continues and a spending cut, and the months it lasts. An estimate from your numbers, not advice.', [
    I('left', 'Income that continues a month', 4680), I('cut', 'Cut in essential spending you could make', 0.15, 'pct')], [
    O('Emergency fund balance', 'money', EBAL), O('Essential spending a month', 'money', 'ROUND(%s,0)' % EAVG), O('Spending after the cut', 'money', 'ROUND(%s*(1-{in:cut}),0)' % EAVG),
    O('Monthly drain on the fund', 'money', 'ROUND(%s,0)' % BURN), O('Months of cover', 'num', 'IF(%s<=0,"",ROUND(%s/%s,1))' % (BURN, EBAL, BURN)),
    O('Months of cover with no cut', 'num', 'IF(%s-{in:left}<=0,"",ROUND(%s/(%s-{in:left}),1))' % (EAVG, EBAL, EAVG)),
    O('Verdict', 'text', 'IF(%s<=0,"Income covers essential spending",ROUND(%s/%s,1)&" months of cover")' % (BURN, EBAL, BURN))],
    GR('What if the income that continues is', ('Nothing', {'left': 0}), ('1500', {'left': 1500}), ('3000', {'left': 3000}), ('4000', {'left': 4000}), ('4680', {'left': 4680}))))
# 14 windfall to goals
AV14 = '({in:windfall}*(1-{in:keep}))'
P1 = 'MIN(%s,IFERROR(INDEX(%s,1),0))' % (AV14, RK('left'))
P2 = 'MIN(%s-%s,IFERROR(INDEX(%s,2),0))' % (AV14, P1, RK('left'))
P3 = 'MIN(%s-%s-%s,IFERROR(INDEX(%s,3),0))' % (AV14, P1, P2, RK('left'))
tools.append(TOOL('windfall', 'Windfall to Goals', 'Where should a windfall go',
    'A windfall split between the goals in rank order (behind goals first, then priority and days left), after the share you keep for spending; each goal gets at most what it still needs.', [
    I('windfall', 'Windfall amount', 1500), I('keep', 'Share you keep for spending', 0.2, 'pct')], [
    O('Amount for goals', 'money', 'ROUND(%s,2)' % AV14), O('First goal', 'text', 'IFERROR(INDEX(%s,1)&"","")' % RK('goal')), O('Put in the first goal', 'money', 'ROUND(%s,2)' % P1),
    O('Second goal', 'text', 'IFERROR(INDEX(%s,2)&"","")' % RK('goal')), O('Put in the second goal', 'money', 'ROUND(%s,2)' % P2),
    O('Third goal', 'text', 'IFERROR(INDEX(%s,3)&"","")' % RK('goal')), O('Put in the third goal', 'money', 'ROUND(%s,2)' % P3),
    O('Not yet placed', 'money', 'ROUND(%s-%s-%s-%s,2)' % (AV14, P1, P2, P3)),
    O('Verdict', 'text', 'IF(%s<=0,"No goal needs money",IF(%s>=0.5,"Put "&%s&" in "&IFERROR(INDEX(%s,1)&"",""),"Nothing to place"))' % (P1, P1, MONEY(P1), RK('goal')))],
    GR('What if the windfall is', ('500', {'windfall': 500}), ('1000', {'windfall': 1000}), ('1500', {'windfall': 1500}), ('3000', {'windfall': 3000}), ('6000', {'windfall': 6000}))))
# 15 goals pause test
LOW, MEDT = tok('priority', 'Low'), tok('priority', 'Medium')
def PS(t, col): return 'SUMIFS(%s,%s,%s,%s,0)' % (GL(col), GL('priority'), t, GL('is_reached'))
PAU = '(%s+IF({in:level}>=2,%s,0))' % (PS(LOW, 'monthly_amount'), PS(MEDT, 'monthly_amount'))
tools.append(TOOL('goal_pause', 'Goals Pause Test', 'What do we free up if some goals pause',
    'The monthly total of your goals if the low-priority goals (level 1) or the low and medium goals (level 2) pause, how much that frees a month and for each paycheck, and what is left to save on them.', [
    I('level', 'Pause level: 0 none, 1 low priority, 2 low and medium', 1, 'int')], [
    O('Monthly total of open goals', 'money', 'SUMIFS(%s,%s,0)' % (GL('monthly_amount'), GL('is_reached'))), O('Paused amount a month', 'money', PAU),
    O('Monthly total after the pause', 'money', 'SUMIFS(%s,%s,0)-%s' % (GL('monthly_amount'), GL('is_reached'), PAU)), O('Freed per paycheck', 'money', 'ROUND(%s*12/%s,2)' % (PAU, PPY)),
    O('Goals paused', 'int', 'IF({in:level}<=0,0,COUNTIFS(%s,%s,%s,0)+IF({in:level}>=2,COUNTIFS(%s,%s,%s,0),0))' % (GL('priority'), LOW, GL('is_reached'), GL('priority'), MEDT, GL('is_reached'))),
    O('Left to save on the paused goals', 'money', 'IF({in:level}<=0,0,%s+IF({in:level}>=2,%s,0))' % (PS(LOW, 'left'), PS(MEDT, 'left'))),
    O('Verdict', 'text', 'IF({in:level}<=0,"Nothing paused","Frees "&%s&" a month")' % MONEY(PAU))],
    GR('What if the pause level is', ('0, none', {'level': 0}), ('1, low priority', {'level': 1}), ('2, low and medium', {'level': 2}))))
# 16 retirement contributions
YTD16 = 'SUMIFS(%s,%s,%s,%s,">="&DATE(YEAR({today}),1,1))' % (RT('employee_amount'), RT('person'), tok('person', 'Partner 1'), RT('date'))
tools.append(TOOL('retirement', 'Retirement Contributions', 'How much goes in and what share of take-home pay is it',
    'Your amount and the employer amount you type per paycheck: yearly total, share of take-home against a typical range in Settings and year to date. Amounts only, never advice.', [
    I('employee', 'Your amount per paycheck', 142.5), I('employer', 'Employer amount per paycheck, typed', 71.25), I('net', 'Take-home pay per paycheck', 2160)], [
    O('Total per paycheck', 'money', '{in:employee}+{in:employer}'), O('Paychecks a year', 'int', PPY), O('Yearly total', 'money', '({in:employee}+{in:employer})*%s' % PPY), O('Your yearly amount', 'money', '{in:employee}*%s' % PPY),
    O('Share of take-home', 'pct', 'IFERROR({in:employee}/{in:net},0)'), O('Your share plus the employer amount', 'pct', 'IFERROR(({in:employee}+{in:employer})/{in:net},0)'),
    O('Your amount this year so far, partner 1', 'money', YTD16), O('Employer amount this year so far, partner 1', 'money', 'SUMIFS(%s,%s,%s,%s,">="&DATE(YEAR({today}),1,1))' % (RT('employer_amount'), RT('person'), tok('person', 'Partner 1'), RT('date'))),
    O('Verdict', 'text', 'ROUND(IFERROR({in:employee}/{in:net},0)*100,1)&"% of take-home, typical range "&ROUND({set:retirement_min}*100,0)&"% to "&ROUND({set:retirement_good}*100,0)&"%, check your own numbers"')],
    GR('What if your amount per paycheck is', ('100', {'employee': 100}), ('142.5', {'employee': 142.5}), ('200', {'employee': 200}), ('260', {'employee': 260}), ('325', {'employee': 325}))))
# 17 contribution step test
tools.append(TOOL('contribution_step', 'Contribution Step Test', 'What does one point of pay change in what we pay in',
    'The same contribution moved up and down by a number of points of take-home pay: what each point costs a paycheck, a month and a year. Amounts only, never advice.', [
    I('net', 'Take-home pay per paycheck', 2160), I('amount', 'Your amount per paycheck', 142.5), I('points', 'Step in points of take-home pay', 1, 'num')], [
    O('Your share now', 'pct', 'IFERROR({in:amount}/{in:net},0)'), O('One step costs per paycheck', 'money', 'ROUND({in:net}*{in:points}/100,2)'), O('One step costs a month', 'money', 'ROUND({in:net}*{in:points}/100*%s/12,2)' % PPY),
    O('One step costs a year', 'money', 'ROUND({in:net}*{in:points}/100*%s,2)' % PPY), O('One step lower, per paycheck', 'money', 'MAX(0,{in:amount}-{in:net}*{in:points}/100)'), O('One step higher, per paycheck', 'money', '{in:amount}+{in:net}*{in:points}/100'),
    O('Two steps higher, per paycheck', 'money', '{in:amount}+2*{in:net}*{in:points}/100'), O('Share two steps higher', 'pct', 'IFERROR(({in:amount}+2*{in:net}*{in:points}/100)/{in:net},0)'),
    O('Verdict', 'text', '"Each step costs "&ROUND({in:net}*{in:points}/100*%s/12,0)&" a month"' % PPY)],
    GR('What if the step is', ('0.5 point', {'points': 0.5}), ('1 point', {'points': 1}), ('2 points', {'points': 2}), ('3 points', {'points': 3}), ('5 points', {'points': 5}))))
# 18 goal funding check
SHARE18 = 'IF(SUM(%s)>0,SUM(%s)/SUM(%s),1)' % (CG('planned3'), CG('dep3'), CG('planned3'))
SHORT18 = 'SUMIFS(%s,%s,">0")' % (CG('short3'), CG('short3'))
tools.append(TOOL('funding_check', 'Goal Funding Check', 'Did we put in what we planned over the last 3 months',
    'Deposits made against the plan over the last 3 complete months for every goal: the share funded, the shortfall, how many goals fall under your share and the goal furthest behind.', [
    I('tol', 'Counts as funded at or above this share', 0.95, 'pct')], [
    O('Planned, last 3 months', 'money', 'SUM(%s)' % CG('planned3')), O('Deposited, last 3 months', 'money', 'SUM(%s)' % CG('dep3')), O('Share funded', 'pct', SHARE18), O('Under-funded by in total', 'money', SHORT18),
    O('Goals under your share', 'int', 'COUNTIFS(%s,"<"&{in:tol})' % CG('share3')), O('Goal furthest behind', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (CG('goal'), CG('short3'), CG('short3'))),
    O('Its shortfall', 'money', 'MAX(%s)' % CG('short3')),
    O('Verdict', 'text', 'IF(%s>={in:tol},"Funded "&ROUND(%s*100,0)&"%%","Under-funded by "&%s)' % (SHARE18, SHARE18, MONEY(SHORT18)))],
    GR('What if funded means', ('80%', {'tol': 0.8}), ('90%', {'tol': 0.9}), ('95%', {'tol': 0.95}), ('100%', {'tol': 1}))))
assert len(tools) == 18, len(tools)
