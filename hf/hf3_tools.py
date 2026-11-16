"""Household Finance suite part 3: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf3_lists import *
from hf3_tables import R, MS, DAYN, DIM, YES, G_FIX, G_VAR, G_WANT, G_SAV, G_DEBT, C_GRO, C_EAT, C_FUEL, C_SHOP, C_KIDS, C_OTHER
import hf3_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
TX = lambda c: R('transactions', c)
TM = lambda c: R('this_month', c)
SR = lambda c: R('savings_rate', c)
SPENT = lambda c, m: 'SUMIFS(%s,%s,%s,%s,%s,%s,"")' % (TX('amount'), TX('category'), c, TX('month'), m, TX('from_goal'))
LASTM = 'EDATE(%s,-1)' % MS
def LK(t, col, kcol, v): return 'INDEX(%s,MATCH(%s,%s,0))' % (R(t, col), v, R(t, kcol))
tools = []
WEEK_GRO = D.envelopes_d()[0]['weekly']

# 1 planned against actual -------------------------------------------------------------
PL1 = 'SUMIFS(%s,%s,1)' % (TM('base'), TM('counts')); AC1 = 'SUMIFS(%s,%s,1)' % (TM('actual'), TM('counts'))
tools.append(TOOL('planned_actual', 'Planned vs Actual Check', 'Is spending on plan this month',
    'Every spending category this month to date against the plan: variable spending against the plan pro-rated by days, bills against the full month.', [
    I('tol', 'Within this share of the plan counts as on plan', 0.05, 'pct')], [
    O('Plan to date, spending categories', 'money', PL1), O('Actual to date', 'money', AC1), O('Over (+) or under (-) the plan', 'money', '%s-%s' % (AC1, PL1)),
    O('Share of the plan used', 'pct', 'IFERROR(%s/%s,0)' % (AC1, PL1)),
    O('Categories over plan by more than the share', 'int', 'COUNTIFS(%s,1,%s,">"&{in:tol})' % (TM('counts'), TM('vs_plan'))),
    O('Category furthest over plan', 'text', 'IF(MAX(%s)>0,INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (TM('over_amt'), TM('category'), TM('over_amt'), TM('over_amt'))),
    O('Over by in that category', 'money', 'MAX(%s)' % TM('over_amt')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,1,%s,">"&{in:tol})>0,%s,%s)' % (TM('counts'), TM('vs_plan'), va('Over plan'), va('On plan')))],
    GR('What if the share is', ('No tolerance', {'tol': 0}), ('2%', {'tol': 0.02}), ('5%', {'tol': 0.05}), ('10%', {'tol': 0.1}), ('20%', {'tol': 0.2}))))
# 2 over-budget ranker ---------------------------------------------------------------------
RK = TM('rank_key')
def RKN(k, what):
    if what == 'cat': return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (TM('category'), RK, k, RK)
    return 'IFERROR(ROUND(LARGE(%s,%d),2),0)' % (RK, k)
tools.append(TOOL('overbudget_ranker', 'Over-budget Ranker', 'Which category do we fix first',
    'Categories over plan this month ranked by amount, with the share of all overspending in the top three.', [
    I('min_over', 'Ignore overspending under this amount', 10)], [
    O('First: category', 'text', RKN(1, 'cat')), O('First: over by', 'money', RKN(1, 'amt')), O('Second: category', 'text', RKN(2, 'cat')), O('Second: over by', 'money', RKN(2, 'amt')),
    O('Third: category', 'text', RKN(3, 'cat')), O('Third: over by', 'money', RKN(3, 'amt')),
    O('Overspending in the top three', 'money', '%s+%s+%s' % (RKN(1, 'amt'), RKN(2, 'amt'), RKN(3, 'amt'))),
    O('Share of all overspending in the top three', 'pct', 'IFERROR((%s+%s+%s)/SUMIFS(%s,%s,%s),0)' % (RKN(1, 'amt'), RKN(2, 'amt'), RKN(3, 'amt'), TM('over_amt'), TM('flag'), pace('Over pace'))),
    O('Categories over by at least the minimum', 'int', 'COUNTIFS(%s,">="&{in:min_over})' % RK),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">="&{in:min_over})=0,%s,%s)' % (RK, va('Nothing is over plan'), va('Fix the top category first')))],
    GR('What if the minimum is', ('0', {'min_over': 0}), ('25', {'min_over': 25}), ('50', {'min_over': 50}), ('100', {'min_over': 100}), ('200', {'min_over': 200}))))
# 3 month-end pace -------------------------------------------------------------------------------
PE3 = 'SUMIFS(%s,%s,1)+{in:coming}' % (TM('pace_end'), TM('counts')); PM3 = 'SUMIFS(%s,%s,1)' % (TM('planned'), TM('counts'))
VAR3 = 'SUMIFS(%s,%s,1)-SUMIFS(%s,%s,1)-{in:coming}' % (TM('planned'), TM('var'), TM('actual'), TM('var'))
tools.append(TOOL('month_pace', 'Month-end Pace', 'Will we overspend by month end',
    'Spending to date divided by days gone times days in the month against the plan; add a payment you know is still to come.', [
    I('coming', 'A payment still to come this month', 0)], [
    O('Spent so far, counted spending', 'money', AC1), O('Plan for the whole month', 'money', PM3), O('Days gone', 'int', DAYN), O('Days left', 'int', '%s-%s' % (DIM, DAYN)),
    O('Pace at month end', 'money', PE3), O('Over (+) or under (-) the plan at month end', 'money', '%s-%s' % (PE3, PM3)),
    O('Variable spending you can still afford a day', 'money', 'IF(%s-%s>0,MAX(0,%s)/(%s-%s),0)' % (DIM, DAYN, VAR3, DIM, DAYN)),
    O('Verdict', 'text', 'IF(%s-%s>{set:pace_tol}*%s,%s,%s)' % (PE3, PM3, PM3, va('Overspend at month end'), va('On pace')))],
    GR('What if a payment is still to come', ('Nothing', {'coming': 0}), ('100', {'coming': 100}), ('250', {'coming': 250}), ('500', {'coming': 500}), ('1000', {'coming': 1000}))))
# 4 groceries envelope ---------------------------------------------------------------------------
MA4 = '{in:allow}*52/12'; SP4 = SPENT(C_GRO, MS)
tools.append(TOOL('groceries_envelope', 'Groceries Envelope', 'What can we spend a day on groceries',
    'The weekly groceries allowance, spent so far this month, days left and what you can spend a day; the story of the month in one place.', [
    I('allow', 'Weekly groceries allowance', WEEK_GRO)], [
    O('Allowance for the month', 'money', MA4), O('Allowance to date', 'money', '%s*%s/%s' % (MA4, DAYN, DIM)), O('Spent so far', 'money', SP4),
    O('Over (+) or under (-) the allowance to date', 'money', '%s-%s*%s/%s' % (SP4, MA4, DAYN, DIM)), O('Days left', 'int', '%s-%s' % (DIM, DAYN)),
    O('Can spend a day for the days left', 'money', 'IF(%s-%s>0,MAX(0,%s-%s)/(%s-%s),MAX(0,%s-%s))' % (DIM, DAYN, MA4, SP4, DIM, DAYN, MA4, SP4)),
    O('Pace at month end', 'money', '%s*%s/%s' % (SP4, DIM, DAYN)),
    O('Grocery payments this month', 'int', 'COUNTIFS(%s,%s,%s,%s,%s,"")' % (TX('category'), C_GRO, TX('month'), MS, TX('from_goal'))),
    O('Average grocery payment', 'money', 'IFERROR(%s/COUNTIFS(%s,%s,%s,%s,%s,""),0)' % (SP4, TX('category'), C_GRO, TX('month'), MS, TX('from_goal'))),
    O('Verdict', 'text', 'IF(%s>=%s,%s,IF(%s>%s*%s/%s*(1+{set:pace_tol}),%s,%s))' % (SP4, MA4, va('Plan used up'), SP4, MA4, DAYN, DIM, va('Over the envelope'), va('Can spend the daily amount')))],
    GR('What if the weekly allowance is', ('180', {'allow': 180}), ('200', {'allow': 200}), (str(WEEK_GRO), {'allow': WEEK_GRO}), ('240', {'allow': 240}), ('260', {'allow': 260}))))
# 5 variable envelopes -----------------------------------------------------------------------------
PV = TM('counts')
def PVS(c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('env_status', 'pace_vs'), c, R('env_status', 'category'))
EV = R('env_status', 'pace_vs')
tools.append(TOOL('envelopes_pace', 'Variable Envelopes Pace', 'How many envelopes are over pace',
    'Each variable envelope at the pace of the month so far: how many are over, on pace and under, and fuel, eating out, kids and shopping one by one.', [
    I('tol', 'Within this share counts as on pace', 0.05, 'pct')], [
    O('Envelopes over pace', 'int', 'COUNTIFS(%s,">"&{in:tol})' % EV), O('Envelopes on pace', 'int', 'COUNTIFS(%s,"<="&{in:tol},%s,">="&-{in:tol})' % (EV, EV)),
    O('Envelopes under pace', 'int', 'COUNTIFS(%s,"<"&-{in:tol})' % EV),
    O('Fuel and transport against its allowance at month end', 'pct', PVS(C_FUEL)), O('Eating out against its allowance at month end', 'pct', PVS(C_EAT)),
    O('Kids and family against its allowance at month end', 'pct', PVS(C_KIDS)), O('Shopping against its allowance at month end', 'pct', PVS(C_SHOP)),
    O('Money over the allowance at month end, envelopes over pace', 'money', 'SUMIFS(%s,%s,">"&{in:tol})-SUMIFS(%s,%s,">"&{in:tol})' % (R('env_status', 'month_end'), EV, R('env_status', 'allowance'), EV)),
    O('Envelope furthest over pace', 'text', 'IF(MAX(%s)>{in:tol},INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (EV, R('env_status', 'envelope'), EV, EV)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">"&{in:tol})=0,%s,%s)' % (EV, va('All envelopes on pace'), va('Envelopes over pace')))],
    GR('What if the share is', ('No tolerance', {'tol': 0}), ('5%', {'tol': 0.05}), ('10%', {'tol': 0.1}), ('20%', {'tol': 0.2}), ('30%', {'tol': 0.3}))))
# 6 weekly allowance setter ---------------------------------------------------------------------------
PL6 = 'IF({in:plan}>0,{in:plan},SUMIFS(%s,%s,%s,%s,{in:category}))' % (R('budget', 'planned'), R('budget', 'month'), MS, R('budget', 'category'))
SP6 = SPENT('{in:category}', MS); DL6 = '(%s-%s)' % (DIM, DAYN)
tools.append(TOOL('allowance_setter', 'Weekly Allowance Setter', 'What weekly allowance fits the plan',
    'The weekly allowance that spreads what is left of the monthly plan over the days left (a closed-form answer), against the standard allowance.', [
    IL('category', 'Category', 'category', 'Groceries'), I('plan', 'Monthly plan, 0 uses your Budget plan', 0)], [
    O('Plan for the month', 'money', PL6), O('Spent so far', 'money', SP6), O('Left to spend', 'money', '%s-%s' % (PL6, SP6)), O('Days left', 'int', DL6),
    O('Allowance a week for the days left', 'money', 'IF(%s>0,MAX(0,%s-%s)/%s*7,0)' % (DL6, PL6, SP6, DL6)), O('Allowance a day for the days left', 'money', 'IF(%s>0,MAX(0,%s-%s)/%s,0)' % (DL6, PL6, SP6, DL6)),
    O('Standard weekly allowance from the plan', 'money', '%s*12/52' % PL6),
    O('Difference from the standard week', 'money', 'IF(%s>0,MAX(0,%s-%s)/%s*7,0)-%s*12/52' % (DL6, PL6, SP6, DL6, PL6)),
    O('Verdict', 'text', 'IF(%s-%s<=0,%s,%s)' % (PL6, SP6, va('Plan used up'), va('Allow the weekly amount shown')))],
    GR('What if the monthly plan is', ('700', {'plan': 700}), ('800', {'plan': 800}), ('945', {'plan': 945}), ('1050', {'plan': 1050}), ('1200', {'plan': 1200}))))
# 7 compare with my own history ------------------------------------------------------------------------
CM = lambda c: 'INDEX(%s,MATCH({in:category},%s,0))' % (R('compare', c), R('compare', 'category'))
tools.append(TOOL('compare_history', 'Compare with My History', 'Is this category higher than usual',
    'One category this month to date against the same days of the last 3 months and the same days a year ago: your own history, no national figure.', [
    IL('category', 'Category', 'category', 'Eating out'), I('tol', 'Within this share counts as the same', 0.1, 'pct')], [
    O('This month to date', 'money', CM('this_month')), O('Last 3 months, same days (average)', 'money', CM('avg3')), O('Same days last year', 'money', CM('last_year')),
    O('Change on the 3-month average', 'money', '%s-%s' % (CM('this_month'), CM('avg3'))),
    O('Change on the 3-month average, share', 'pct', 'IFERROR(%s/%s-1,0)' % (CM('this_month'), CM('avg3'))),
    O('Change on last year', 'money', '%s-%s' % (CM('this_month'), CM('last_year'))), O('Change on last year, share', 'pct', 'IFERROR(%s/%s-1,0)' % (CM('this_month'), CM('last_year'))),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:tol}),%s,IF(%s<%s*(1-{in:tol}),%s,%s))' % (CM('this_month'), CM('avg3'), vb('Higher than your history'), CM('this_month'), CM('avg3'), vb('Lower than your history'), vb('Same as your history')))],
    GR('What if the share is', ('No tolerance', {'tol': 0}), ('5%', {'tol': 0.05}), ('10%', {'tol': 0.1}), ('20%', {'tol': 0.2}), ('30%', {'tol': 0.3}))))
# 8 biggest category changes ------------------------------------------------------------------------
UK, DK = R('compare', 'up_key'), R('compare', 'down_key')
def UP(k, what):
    if what == 'cat': return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (R('compare', 'category'), UK, k, UK)
    return 'IFERROR(ROUND(LARGE(%s,%d),2),0)' % (UK, k)
tools.append(TOOL('biggest_changes', 'Biggest Category Changes', 'Which categories rose most on last year',
    'Spending categories ranked by the change against the same days last year, with the biggest fall and the net change.', [
    I('min_change', 'Count a rise only from this amount', 20)], [
    O('Biggest rise: category', 'text', UP(1, 'cat')), O('Biggest rise: amount', 'money', UP(1, 'amt')), O('Second rise: category', 'text', UP(2, 'cat')), O('Second rise: amount', 'money', UP(2, 'amt')),
    O('Third rise: category', 'text', UP(3, 'cat')), O('Third rise: amount', 'money', UP(3, 'amt')),
    O('Biggest fall: category', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),"")' % (R('compare', 'category'), DK, DK)), O('Biggest fall: amount', 'money', 'IFERROR(ROUND(LARGE(%s,1),2),0)' % DK),
    O('Categories up by at least the minimum', 'int', 'COUNTIFS(%s,">="&{in:min_change})' % UK),
    O('Net change on last year, spending categories', 'money', 'SUMIFS(%s,%s,1)' % (R('compare', 'change_ly'), R('compare', 'counts'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">="&{in:min_change})>0,%s,%s)' % (UK, vb('Rising categories found'), vb('No category is up')))],
    GR('What if the minimum is', ('0', {'min_change': 0}), ('20', {'min_change': 20}), ('50', {'min_change': 50}), ('100', {'min_change': 100}), ('200', {'min_change': 200}))))
# 9 savings rate ----------------------------------------------------------------------------------------
LAST3 = '%s,">="&EDATE(%s,-3),%s,"<"&%s' % (SR('month'), MS, SR('month'), MS)
def SRL(c, m): return 'INDEX(%s,MATCH(%s,%s,0))' % (SR(c), m, SR('month'))
tools.append(TOOL('savings_rate_tool', 'Savings Rate Check', 'What is our savings rate',
    'Savings into goals, extra debt payments and retirement over take-home pay plus retirement: last complete month, this month so far, the 3-month rate and your best month.', [
    I('target', 'Savings rate you want', 0.2, 'pct')], [
    O('Savings rate, last complete month', 'pct', SRL('savings_rate', LASTM)), O('Saved last month: goals, extra debt and retirement', 'money', SRL('total_saved', LASTM)),
    O('Take-home plus retirement last month', 'money', SRL('basis', LASTM)), O('Savings rate this month so far', 'pct', SRL('savings_rate', MS)),
    O('Savings rate, last 3 complete months', 'pct', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (SR('total_saved'), LAST3, SR('basis'), LAST3)),
    O('Best month rate, last 12 complete months', 'pct', 'MAX(%s)' % SR('rate_12m')), O('Best month', 'date', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (SR('month'), SR('rate_12m'), SR('rate_12m'))),
    O('Last month against your best', 'pct', 'IFERROR(%s/MAX(%s),0)' % (SRL('savings_rate', LASTM), SR('rate_12m'))),
    O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (SRL('savings_rate', LASTM), vb('At or above your target'), vb('Below your target')))],
    GR('What if the target is', ('10%', {'target': 0.1}), ('15%', {'target': 0.15}), ('20%', {'target': 0.2}), ('25%', {'target': 0.25}), ('30%', {'target': 0.3}))))
# 10 savings rate solver -------------------------------------------------------------------------------
INC10 = 'IF({in:income}>0,{in:income},SUMIFS(%s,%s)/3)' % (SR('basis'), LAST3); SAV10 = 'IF({in:saved}>0,{in:saved},SUMIFS(%s,%s)/3)' % (SR('total_saved'), LAST3)
MORE10 = 'MAX(0,{in:target}*%s-%s)' % (INC10, SAV10)
tools.append(TOOL('savings_solver', 'Savings Rate Solver', 'How much more must we save for the target',
    'The monthly saving needed for your savings rate target, worked out from your own last 3 months (or typed amounts): per month, per week and per paycheck.', [
    I('target', 'Savings rate you want to reach', 0.25, 'pct'), I('income', 'Take-home plus retirement a month, 0 uses your history', 0), I('saved', 'Saved a month, 0 uses your history', 0)], [
    O('Take-home plus retirement a month used', 'money', INC10), O('Saved a month used', 'money', SAV10), O('Savings rate now', 'pct', 'IFERROR(%s/%s,0)' % (SAV10, INC10)),
    O('Saving needed for the target', 'money', '{in:target}*%s' % INC10), O('Save more each month', 'money', MORE10), O('Save more each week', 'money', '%s*12/52' % MORE10),
    O('Save more each paycheck, paid every two weeks', 'money', '%s*12/26' % MORE10),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (MORE10, vb('Save more each month'), vb('On target')))],
    GR('What if the target is', ('15%', {'target': 0.15}), ('20%', {'target': 0.2}), ('25%', {'target': 0.25}), ('30%', {'target': 0.3}), ('35%', {'target': 0.35}))))
# 11 no-spend days ---------------------------------------------------------------------------------------
NS = '(%s-COUNTIFS(%s,%s,%s,1))' % (DAYN, TX('month'), MS, TX('var_day'))
NSL = '(DAY(EDATE({today},-1))-COUNTIFS(%s,%s,%s,1,%s,"<="&EDATE({today},-1)))' % (TX('month'), LASTM, TX('var_day'), TX('date'))
tools.append(TOOL('no_spend_days', 'No-spend Days', 'How many no-spend days have we had',
    'Days with no variable spending (nothing in variable needs or wants) this month against the same days of last month, and the days still needed for your own goal.', [
    I('goal', 'No-spend days you want this month', 8, 'int')], [
    O('Days gone', 'int', DAYN), O('Days with variable spending', 'int', 'COUNTIFS(%s,%s,%s,1)' % (TX('month'), MS, TX('var_day'))), O('No-spend days this month', 'int', NS),
    O('No-spend days in the same days of last month', 'int', NSL), O('Share of days with no variable spending', 'pct', '%s/%s' % (NS, DAYN)),
    O('No-spend days still needed for your goal', 'int', 'MAX(0,{in:goal}-%s)' % NS), O('Days left in the month', 'int', '%s-%s' % (DIM, DAYN)),
    O('Verdict', 'text', 'IF(%s>%s,%s,IF(%s<%s,%s,%s))' % (NS, NSL, vb('More no-spend days than last month'), NS, NSL, vb('Fewer no-spend days than last month'), vb('Same no-spend days as last month')))],
    GR('What if the goal is', ('4 days', {'goal': 4}), ('6 days', {'goal': 6}), ('8 days', {'goal': 8}), ('10 days', {'goal': 10}), ('12 days', {'goal': 12}))))
# 12 eating out watch -------------------------------------------------------------------------------------
EO = SPENT(C_EAT, MS); EN = 'COUNTIFS(%s,%s,%s,%s,%s,"")' % (TX('category'), C_EAT, TX('month'), MS, TX('from_goal'))
def EONK(k): return 'COUNTIFS(%s,%s,%s,">="&EDATE(%s,-%d),%s,"<="&EDATE({today},-%d),%s,"")' % (TX('category'), C_EAT, TX('date'), MS, k, TX('date'), k, TX('from_goal'))
EN3 = '((%s+%s+%s)/3)' % (EONK(1), EONK(2), EONK(3))
EA3 = 'INDEX(%s,MATCH(%s,%s,0))' % (R('compare', 'avg3'), C_EAT, R('compare', 'category'))
tools.append(TOOL('eating_out_watch', 'Eating Out Watch', 'Is eating out creeping up',
    'Eating out this month to date: amount, number of payments and the average payment against the same days of the last 3 months.', [
    I('tol', 'Within this share counts as steady', 0.1, 'pct')], [
    O('Eating out this month to date', 'money', EO), O('Payments this month', 'int', EN), O('Average payment this month', 'money', 'IFERROR(%s/%s,0)' % (EO, EN)),
    O('Last 3 months, same days (average)', 'money', EA3), O('Payments in the last 3 months, same days (average)', 'num', EN3),
    O('Average payment, last 3 months', 'money', 'IFERROR(%s/%s,0)' % (EA3, EN3)), O('Amount against the 3-month average', 'pct', 'IFERROR(%s/%s-1,0)' % (EO, EA3)),
    O('Average payment against the 3-month average', 'pct', 'IFERROR((%s/%s)/(%s/%s)-1,0)' % (EO, EN, EA3, EN3)),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:tol}),%s,IF(%s<%s*(1-{in:tol}),%s,%s))' % (EO, EA3, vb('Eating out is up'), EO, EA3, vb('Eating out is down'), vb('Eating out is steady')))],
    GR('What if the share is', ('No tolerance', {'tol': 0}), ('5%', {'tol': 0.05}), ('10%', {'tol': 0.1}), ('20%', {'tol': 0.2}), ('30%', {'tol': 0.3}))))
# 13 fuel and transport watch -----------------------------------------------------------------------------
def FW(a, b): return 'SUMIFS(%s,%s,%s,%s,">="&EDATE(%s,%d),%s,"<"&EDATE(%s,%d),%s,"")' % (TX('amount'), TX('category'), C_FUEL, TX('month'), MS, a, TX('month'), MS, b, TX('from_goal'))
F12, F24 = FW(-12, 0), FW(-24, -12)
tools.append(TOOL('fuel_watch', 'Fuel and Transport Watch', 'Is fuel and transport higher than last year',
    'The last 12 complete months of fuel and transport against the 12 months before, and last month against the same month a year earlier.', [
    I('tol', 'Within this share counts as normal', 0.05, 'pct')], [
    O('Last 12 complete months', 'money', F12), O('The 12 months before that', 'money', F24), O('Change on the year before', 'money', '%s-%s' % (F12, F24)),
    O('Change on the year before, share', 'pct', 'IFERROR(%s/%s-1,0)' % (F12, F24)), O('Monthly average, last 12 months', 'money', '%s/12' % F12),
    O('Cost a day, last 12 months', 'money', '%s/365' % F12), O('Last complete month', 'money', FW(-1, 0)), O('Same month a year earlier', 'money', FW(-13, -12)),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:tol}),%s,IF(%s<%s*(1-{in:tol}),%s,%s))' % (F12, F24, vc('Fuel is up'), F12, F24, vc('Fuel is down'), vc('Fuel is normal')))],
    GR('What if the share is', ('No tolerance', {'tol': 0}), ('3%', {'tol': 0.03}), ('5%', {'tol': 0.05}), ('10%', {'tol': 0.1}), ('20%', {'tol': 0.2}))))
# 14 seasonal spike planner ----------------------------------------------------------------------------------
SEA = {'H': tok('season', 'Holidays'), 'B': tok('season', 'Back to school'), 'W': tok('season', 'Winter utilities')}
SM = 'IF({in:season}=%s,11,IF({in:season}=%s,8,12))' % (SEA['H'], SEA['B']); NM = 'IF({in:season}=%s,3,2)' % SEA['W']
SD = 'DATE(YEAR({today})-1,%s,1)' % SM
def S1(c, a, b): return 'SUMIFS(%s,%s,%s,%s,">="&%s,%s,"<"&%s)' % (TX('amount'), TX('category'), c, TX('date'), a, TX('date'), b)
def SEAS(a, b):
    return 'IF({in:season}=%s,%s+%s,IF({in:season}=%s,%s+%s+%s,%s))' % (
        SEA['H'], S1(cat('Gifts'), a, b), S1(cat('Holidays and trips'), a, b), SEA['B'], S1(cat('Childcare and school'), a, b), S1(cat('Kids and family'), a, b), S1(C_SHOP, a, b), S1(cat('Utilities'), a, b))
SEASON_T = SEAS(SD, 'EDATE(%s,%s)' % (SD, NM)); NORMAL = '(%s/6*%s)' % (SEAS('EDATE(%s,-6)' % SD, SD), NM)
EXTRA = 'MAX(0,%s-%s)' % (SEASON_T, NORMAL)
tools.append(TOOL('season_planner', 'Seasonal Spike Planner', 'What do we set aside for the season',
    'Last year\'s holiday, back-to-school or winter utilities spending above a normal month, spread over the months you have to save.', [
    IL('season', 'Season', 'season', 'Holidays'), I('months', 'Months you have before the season starts', 6, 'int')], [
    O('Season', 'text', '{in:season}'), O('Months in the season', 'int', NM), O('Spent in the same season last year', 'money', SEASON_T),
    O('Normal spending for the same months', 'money', NORMAL), O('Extra above a normal month', 'money', EXTRA),
    O('Set aside each month', 'money', '%s/MAX(1,{in:months})' % EXTRA), O('Set aside each paycheck, paid every two weeks', 'money', '%s/MAX(1,{in:months})*12/26' % EXTRA),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (EXTRA, vc('Set aside the monthly amount'), vc('No extra needed for the season')))],
    GR('What if you have', ('3 months', {'months': 3}), ('4 months', {'months': 4}), ('6 months', {'months': 6}), ('9 months', {'months': 9}), ('12 months', {'months': 12}))))
# 15 plan reset -------------------------------------------------------------------------------------------------
P3 = '%s,">="&EDATE(%s,-3),%s,"<"&%s' % (R('pva', 'month'), MS, R('pva', 'month'), MS)
AVG15 = 'SUMIFS(%s,%s,{in:category},%s)/3' % (R('pva', 'actual'), R('pva', 'category'), P3)
NEW15 = 'ROUND(%s*(1+{in:trend})/5,0)*5' % AVG15
CUR15 = 'SUMIFS(%s,%s,%s,%s,{in:category})' % (R('budget', 'planned'), R('budget', 'month'), MS, R('budget', 'category'))
ALL15 = 'SUMIFS(%s,%s,%s,"<>"&%s,%s,"<>"&%s)/3*(1+{in:trend})' % (R('pva', 'actual'), P3, R('pva', 'group'), G_SAV, R('pva', 'group'), G_DEBT)
tools.append(TOOL('plan_reset', 'Plan Reset', 'What should the plan be from now on',
    'A new plan for a category from the last 3 complete months times a trend factor, rounded to the nearest 5, with the plan for all spending beside it.', [
    IL('category', 'Category', 'category', 'Groceries'), I('trend', 'Trend added to the 3-month average', 0.03, 'pct')], [
    O('Plan this month', 'money', CUR15), O('Average of the last 3 complete months', 'money', AVG15), O('New plan', 'money', NEW15), O('Change in the plan', 'money', '%s-%s' % (NEW15, CUR15)),
    O('Change in the plan, share', 'pct', 'IFERROR(%s/%s-1,0)' % (NEW15, CUR15)),
    O('Plan for all spending now', 'money', 'SUMIFS(%s,%s,%s,%s,"<>"&%s,%s,"<>"&%s)' % (R('budget', 'planned'), R('budget', 'month'), MS, R('budget', 'group'), G_SAV, R('budget', 'group'), G_DEBT)),
    O('All spending from the last 3 months plus the trend', 'money', ALL15),
    O('Verdict', 'text', 'IF(%s>%s*(1+{set:pace_tol}),%s,IF(%s<%s*(1-{set:pace_tol}),%s,%s))' % (NEW15, CUR15, vc('Raise the plan'), NEW15, CUR15, vc('Lower the plan'), vc('Keep the plan')))],
    GR('What if the trend is', ('None', {'trend': 0}), ('2%', {'trend': 0.02}), ('3%', {'trend': 0.03}), ('5%', {'trend': 0.05}), ('8%', {'trend': 0.08}))))
# 16 small leaks finder ----------------------------------------------------------------------------------------------
LK_ = R('payees', 'leak_cost')
def LKN_(k, what):
    if what == 'p': return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (R('payees', 'payee'), LK_, k, LK_)
    return 'IFERROR(LARGE(%s,%d),0)' % (LK_, k)
tools.append(TOOL('small_leaks', 'Small Leaks Finder', 'Which small payments add up',
    'Frequent small payments by payee over the last 90 days (limits in Settings), the biggest leaks and what you keep if you stop a share of them.', [
    I('cut', 'Share of these payments you would stop', 0.5, 'pct'), I('months', 'Months to look ahead', 12, 'int')], [
    O('Small leaks found', 'int', 'COUNTIFS(%s,">0")' % LK_), O('Cost a month, all small leaks', 'money', 'SUM(%s)' % LK_),
    O('Biggest leak: payee', 'text', LKN_(1, 'p')), O('Biggest leak: a month', 'money', LKN_(1, 'a')), O('Second: payee', 'text', LKN_(2, 'p')), O('Second: a month', 'money', LKN_(2, 'a')),
    O('Third: payee', 'text', LKN_(3, 'p')), O('Third: a month', 'money', LKN_(3, 'a')),
    O('You keep over the months ahead if you stop that share', 'money', 'SUM(%s)*{in:cut}*{in:months}' % LK_),
    O('Share of counted spending, last 90 days', 'pct', 'IFERROR(SUM(%s)*3/SUMIFS(%s,%s,">="&({today}-90)),0)' % (LK_, TX('counted'), TX('date'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">0")>0,%s,%s)' % (LK_, vc('Small leaks found'), vc('No small leaks')))],
    GR('What if you stop', ('A quarter', {'cut': 0.25}), ('Half', {'cut': 0.5}), ('Three quarters', {'cut': 0.75}), ('All of them', {'cut': 1}), ('Half, for 6 months', {'cut': 0.5, 'months': 6}))))
# 17 duplicate payment finder ------------------------------------------------------------------------------------------
DD = TX('dup_date'); LATEST = 'LARGE(%s,1)' % DD
tools.append(TOOL('dup_finder', 'Duplicate Payment Finder', 'Did we pay anything twice',
    'Payments to the same payee for the same amount within the days set in Settings: the latest one, how many are flagged and how much money sits in them.', [
    I('lookback', 'Look back this many days', 365, 'int')], [
    O('Latest flagged payment: ID', 'text', 'IFERROR(IF(%s>={today}-{in:lookback},INDEX(%s,MATCH(%s,%s,0)),""),"")' % (LATEST, TX('tx_id'), LATEST, DD)),
    O('Latest flagged payment: date', 'date', 'IFERROR(IF(%s>={today}-{in:lookback},%s,""),"")' % (LATEST, LATEST)),
    O('Latest flagged payment: payee', 'text', 'IFERROR(IF(%s>={today}-{in:lookback},INDEX(%s,MATCH(%s,%s,0)),""),"")' % (LATEST, TX('payee'), LATEST, DD)),
    O('Latest flagged payment: amount', 'money', 'IFERROR(IF(%s>={today}-{in:lookback},INDEX(%s,MATCH(%s,%s,0)),0),0)' % (LATEST, TX('amount'), LATEST, DD)),
    O('Flagged payments in the period', 'int', 'COUNTIFS(%s,">="&({today}-{in:lookback}))' % DD), O('Money in the flagged payments', 'money', 'SUMIFS(%s,%s,">="&({today}-{in:lookback}))' % (TX('amount'), DD)),
    O('Likely second payments, about half of it', 'money', 'SUMIFS(%s,%s,">="&({today}-{in:lookback}))/2' % (TX('amount'), DD)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">="&({today}-{in:lookback}))>0,%s,%s)' % (DD, vc('Possible duplicate found'), vc('No duplicate found')))],
    GR('What if you look back', ('120 days', {'lookback': 120}), ('180 days', {'lookback': 180}), ('One year', {'lookback': 365}), ('18 months', {'lookback': 548}), ('Two years', {'lookback': 730}))))
# 18 category check -----------------------------------------------------------------------------------------------------
LB = '%s,">="&({today}-{in:lookback})' % TX('date')
tools.append(TOOL('category_check', 'Category Check', 'Is every payment in the right category',
    'Payments in the category Other and large variable payments in the period you choose, with the share of counted spending that sits in Other.', [
    I('lookback', 'Look back this many days', 90, 'int'), I('large', 'A large payment is this amount or more', 400)], [
    O('Payments in the category Other', 'int', 'COUNTIFS(%s,%s,%s)' % (TX('category'), C_OTHER, LB)), O('Amount in the category Other', 'money', 'SUMIFS(%s,%s,%s,%s)' % (TX('amount'), TX('category'), C_OTHER, LB)),
    O('Share of counted spending in Other', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,%s)/SUMIFS(%s,%s),0)' % (TX('amount'), TX('category'), C_OTHER, LB, TX('counted'), LB)),
    O('Large variable payments', 'int', 'COUNTIFS(%s,">="&{in:large},%s,"<>"&%s,%s,"<>"&%s,%s,"<>"&%s,%s,"",%s)' % (TX('amount'), TX('group'), G_FIX, TX('group'), G_DEBT, TX('group'), G_SAV, TX('from_goal'), LB)),
    O('Money in large variable payments', 'money', 'SUMIFS(%s,%s,">="&{in:large},%s,"<>"&%s,%s,"<>"&%s,%s,"<>"&%s,%s,"",%s)' % (TX('amount'), TX('amount'), TX('group'), G_FIX, TX('group'), G_DEBT, TX('group'), G_SAV, TX('from_goal'), LB)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,%s)>0,%s,%s)' % (TX('category'), C_OTHER, LB, vc('Re-categorise the listed items'), vc('Clean')))],
    GR('What if you look back', ('30 days', {'lookback': 30}), ('60 days', {'lookback': 60}), ('90 days', {'lookback': 90}), ('180 days', {'lookback': 180}), ('One year', {'lookback': 365}))))
assert len(tools) == 18, len(tools)
