"""Household Finance suite part 7: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf7_lists import *
from hf7_tables import R, MS, G_FIX, G_VAR, NOA, IKE, BOTH, NEED, INC, INCALL, SHARE, SCV
import hf7_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, lab): return IN(k, label, 'list', key(lst, lab), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
SH = lambda c: R('shared', c)
KC = lambda c: R('kids_costs', c)
AL = lambda c: R('allowances', c)
LO = lambda c: R('lose', c)
SE = lambda c: R('settle', c)
OV = lambda c: R('overpaid', c)
FS = lambda c: R('fair_split', c)
N = '{set:share_months}'
tools = []
P1N, P2N = '{set:partner1}', '{set:partner2}'
SP = '&" "&'


def WIN(n): return '%s,">="&EDATE(%s,-%s),%s,"<"&%s' % (SH('date'), MS, n, SH('date'), MS)


# 1 fair split ---------------------------------------------------------------------------------
P1I = 'IF({in:p1_income}>0,{in:p1_income},%s/%s)' % (INC(P1, 'EDATE(%s,-%s)' % (MS, N), MS), N)
P2I = 'IF({in:p2_income}>0,{in:p2_income},%s/%s)' % (INC(P2, 'EDATE(%s,-%s)' % (MS, N), MS), N)
RT1 = 'IF({in:rule}=%s,0.5,IF({in:rule}=%s,{in:custom},%s/(%s+%s)))' % (tok('split', 'Equal'), tok('split', 'Custom'), P1I, P1I, P2I)
tools.append(TOOL('fair_split_calc', 'Fair-split Calculator', 'Who pays what of the shared costs',
    'Split shared costs equally, by take-home share or by a custom share; leave an income at 0 to read the last months of Income.', [
    I('costs', 'Shared costs to split', 420), IL('rule', 'Split rule', 'split', 'Income share'), I('p1_income', 'Partner 1 take-home a month, 0 = from Income', 0),
    I('p2_income', 'Partner 2 take-home a month, 0 = from Income', 0), I('custom', 'Partner 1 share in a custom split', 0.55, 'pct')], [
    O('Partner 1 take-home a month', 'money', P1I), O('Partner 2 take-home a month', 'money', P2I), O('Partner 1 share of the costs', 'pct', RT1),
    O('Partner 1 pays', 'money', '{in:costs}*%s' % RT1), O('Partner 2 pays', 'money', '{in:costs}*(1-%s)' % RT1),
    O('Partner 1 pays on the agreed split', 'money', '{in:costs}*{set:agreed_p1_share}'),
    O('Partner 2 difference to the agreed split', 'money', '{in:costs}*(1-%s)-{in:costs}*(1-{set:agreed_p1_share})' % RT1),
    O('Verdict', 'text', '%s%s%s%sROUND({in:costs}*%s,0)&", "&%s%s%s%sROUND({in:costs}*(1-%s),0)' % (P1N, SP, V('pays'), SP, RT1, P2N, SP, V('pays'), SP, RT1))],
    GR('What if the costs are', ('200', {'costs': 200}), ('420', {'costs': 420}), ('800', {'costs': 800}), ('1500', {'costs': 1500}), ('3000', {'costs': 3000}))))
# 2 income share ---------------------------------------------------------------------------------
W2 = ('EDATE(%s,-{in:months})' % MS)
S2 = SHARE(W2, MS)
tools.append(TOOL('income_share', 'Income Share', 'How do take-home pay and the split compare',
    'Each partner\'s share of take-home pay over the last complete months against the agreed share, with the last 3 months to show the drift.', [
    I('months', 'Months of take-home to use', 6, 'int')], [
    O('Partner 1 take-home', 'money', INC(P1, W2, MS)), O('Partner 2 take-home', 'money', INC(P2, W2, MS)), O('Partner 1 share', 'pct', S2), O('Partner 2 share', 'pct', '1-%s' % S2),
    O('Agreed share of partner 1', 'pct', '{set:agreed_p1_share}'), O('Points between income share and agreement', 'num', '(%s-{set:agreed_p1_share})*100' % S2),
    O('Partner 1 share, last 3 months', 'pct', SHARE('EDATE(%s,-3)' % MS, MS)),
    O('Verdict', 'text', '%s%sROUND(%s*100,0)&" / "&ROUND((1-%s)*100,0)' % (V('Split'), SP, S2, S2))],
    GR('What if the months are', ('3 months', {'months': 3}), ('6 months', {'months': 6}), ('9 months', {'months': 9}), ('12 months', {'months': 12}), ('24 months', {'months': 24}))))
# 3 monthly transfer ---------------------------------------------------------------------------------
RT3 = 'IF({in:rule}=%s,{set:agreed_p1_share},IF({in:rule}=%s,%s,IF({in:rule}=%s,0.5,{set:custom_p1_share})))' % (
    tok('tbasis', 'Agreed split'), tok('tbasis', 'Income share'), SHARE('EDATE(%s,-%s)' % (MS, N), MS), tok('tbasis', 'Equal'))
T1M = '(%s/%s)' % (INC(P1, 'EDATE(%s,-%s)' % (MS, N), MS), N)
T2M = '(%s/%s)' % (INC(P2, 'EDATE(%s,-%s)' % (MS, N), MS), N)
tools.append(TOOL('transfer_calc', 'Transfer to Joint', 'What does each partner move to the joint account',
    'Each partner\'s monthly transfer from the agreed split, an income share, an equal split or a custom share, and the amount for each payday of partner 1.', [
    I('need', 'Monthly amount the joint account needs', 4800), IL('rule', 'Basis', 'tbasis', 'Agreed split'), I('paychecks', 'Paychecks of partner 1 a year', 26, 'int')], [
    O('Partner 1 share', 'pct', RT3), O('Partner 1 transfer a month', 'money', '{in:need}*%s' % RT3), O('Partner 2 transfer a month', 'money', '{in:need}*(1-%s)' % RT3),
    O('Partner 1 transfer each payday', 'money', '{in:need}*%s*12/{in:paychecks}' % RT3),
    O('Partner 1 transfer, share of own take-home', 'pct', 'IFERROR({in:need}*%s/%s,0)' % (RT3, T1M)), O('Partner 2 transfer, share of own take-home', 'pct', 'IFERROR({in:need}*(1-%s)/%s,0)' % (RT3, T2M)),
    O('Verdict', 'text', '%s%sROUND({in:need}*%s*12/{in:paychecks},0)%s%s' % (V('Transfer'), SP, RT3, SP, V('each payday')))],
    GR('What if the joint account needs', ('3600', {'need': 3600}), ('4200', {'need': 4200}), ('4800', {'need': 4800}), ('5400', {'need': 5400}), ('6000', {'need': 6000}))))
# 4 settle up ---------------------------------------------------------------------------------------------
D0 = 'EDATE(%s,-{in:back})' % MS
D1 = 'IF({in:back}=0,{today}+1,%s)' % MS
W4 = '%s,">="&%s,%s,"<"&%s' % (SH('date'), D0, SH('date'), D1)
P2PD = 'SUMIFS(%s,%s,%s,%s)' % (SH('amount'), W4, SH('paid_by'), P2)
P2SH = '(SUMIFS(%s,%s)-SUMIFS(%s,%s))' % (SH('amount'), W4, SH('p1_share'), W4)
DF4 = '(%s-%s)' % (P2PD, P2SH)
tools.append(TOOL('settle_calc', 'Settle Up', 'Who owes whom, with the fewest payments',
    'Compares what each partner paid with the agreed share over the months you choose and gives the one payment that squares it.', [
    I('back', 'Complete months back, 0 = this month so far', 1, 'int')], [
    O('Shared costs', 'money', 'SUMIFS(%s,%s)' % (SH('amount'), W4)), O('Partner 1 paid', 'money', 'SUMIFS(%s,%s,%s,%s)' % (SH('amount'), W4, SH('paid_by'), P1)), O('Partner 2 paid', 'money', P2PD),
    O('Partner 1 share', 'money', 'SUMIFS(%s,%s)' % (SH('p1_share'), W4)), O('Partner 2 share', 'money', P2SH), O('Partner 2 over (+) or under (-)', 'money', DF4),
    O('Pays', 'text', 'IF(ROUND(%s,0)>0,%s,IF(ROUND(%s,0)<0,%s,""))' % (DF4, P1N, DF4, P2N)), O('Receives', 'text', 'IF(ROUND(%s,0)>0,%s,IF(ROUND(%s,0)<0,%s,""))' % (DF4, P2N, DF4, P1N)),
    O('One payment', 'money', 'ROUND(ABS(%s),2)' % DF4),
    O('Verdict', 'text', 'IF(ROUND(%s,0)=0,%s,IF(%s>0,%s,%s)%s%s%sROUND(ABS(%s),0)%s%s%sIF(%s>0,%s,%s))' % (
        DF4, V('Nothing to settle'), DF4, P1N, P2N, SP, V('pays'), SP, DF4, SP, V('to'), SP, DF4, P2N, P1N))],
    GR('What if you look back', ('This month so far', {'back': 0}), ('1 month', {'back': 1}), ('2 months', {'back': 2}), ('3 months', {'back': 3}), ('6 months', {'back': 6}))))
# 5 running balance ------------------------------------------------------------------------------------------
BAL = 'SUM(%s)' % SE('open_diff')
OPENM = '(COUNTIFS(%s,">0.5")+COUNTIFS(%s,"<-0.5"))' % (SE('open_diff'), SE('open_diff'))
OLD = 'SUMPRODUCT(MIN(%s+((%s=0)+(%s=0)>0)*1000000000))' % (SE('month'), SE('open_diff'), SE('month'))
DRIFT = 'AVERAGEIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)' % (FS('difference'), FS('month'), MS, FS('month'), MS)
tools.append(TOOL('running_balance', 'Running Settle Balance', 'How much is carried from month to month',
    'The balance still open across unsettled months, since when, how fast it grows at the last 3 months\' drift and what it would be in a few months.', [
    I('ahead', 'Months ahead to look, nothing settled', 3, 'int')], [
    O('Balance owed to partner 2 (negative: to partner 1)', 'money', BAL), O('Open months', 'int', OPENM), O('Oldest open month', 'date', 'IF(%s>=1000000000,"",%s)' % (OLD, OLD)),
    O('Months since the oldest open month', 'int', 'IF(%s>=1000000000,0,(YEAR(%s)-YEAR(%s))*12+MONTH(%s)-MONTH(%s))' % (OLD, MS, OLD, MS, OLD)),
    O('Drift a month, last 3 months', 'money', DRIFT), O('Balance in the months ahead', 'money', '%s+{in:ahead}*%s' % (BAL, DRIFT)),
    O('Is owed', 'text', 'IF(%s>0,%s,IF(%s<0,%s,""))' % (BAL, P2N, BAL, P1N)),
    O('Verdict', 'text', 'IF(ABS(%s)<1,%s,IF(%s>0,%s,%s)%s%s%sROUND(ABS(%s),0))' % (BAL, V('Balance is square'), BAL, P2N, P1N, SP, V('is owed'), SP, BAL))],
    GR('What if you wait', ('Settle now', {'ahead': 0}), ('1 month', {'ahead': 1}), ('3 months', {'ahead': 3}), ('6 months', {'ahead': 6}), ('12 months', {'ahead': 12}))))
# 6 streak check -----------------------------------------------------------------------------------------------
LASTM = 'EDATE(%s,-1)' % MS
STK = 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (OV('streak'), LASTM, OV('month'))
OVTOT = 'SUMIFS(%s,%s,">"&EDATE(%s,-%s),%s,"<="&%s)' % (OV('over_by'), OV('month'), LASTM, STK, OV('month'), LASTM)
tools.append(TOOL('streak_check', 'Over-paid Streak Check', 'Is one partner always paying more than the share',
    'Months in a row partner 2 paid above the agreed share up to the last complete month, the money over in those months and when to settle.', [
    I('limit', 'Settle when the streak reaches this many months', 2, 'int')], [
    O('Months in a row over', 'int', STK), O('Months over in the last 12', 'int', 'COUNTIFS(%s,1,%s,">="&EDATE(%s,-12),%s,"<"&%s)' % (OV('over'), OV('month'), MS, OV('month'), MS)),
    O('Paid above the share in the streak', 'money', OVTOT), O('Average over a month in the streak', 'money', 'IF(%s>0,%s/%s,0)' % (STK, OVTOT, STK)),
    O('Partner 2 share paid last month', 'pct', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (OV('p2_paid_share'), LASTM, OV('month'))),
    O('Agreed share of partner 2', 'pct', '1-{set:agreed_p1_share}'),
    O('Verdict', 'text', 'IF(%s>={in:limit},%s%s%s%s%s%s%s,%s)' % (STK, P2N, SP, V('over for'), SP, STK, SP, V('months, settle up'), V('No streak to settle')))],
    GR('What if you settle at', ('1 month', {'limit': 1}), ('2 months', {'limit': 2}), ('3 months', {'limit': 3}), ('4 months', {'limit': 4}), ('6 months', {'limit': 6}))))
# 7 agreed share check ----------------------------------------------------------------------------------------------
W7 = '%s,">="&EDATE(%s,-{in:months}),%s,"<"&%s' % (SH('date'), MS, SH('date'), MS)
T7 = 'SUMIFS(%s,%s)' % (SH('amount'), W7)
PS7 = 'IFERROR(SUMIFS(%s,%s,%s,%s)/%s,0)' % (SH('amount'), W7, SH('paid_by'), P1, T7)
SG7 = 'ROUND(%s/0.05,0)*0.05' % PS7
tools.append(TOOL('agreed_check', 'Agreed Share Check', 'Does the agreed split still match what we pay',
    'The agreed split against what each partner actually paid over the months you choose; if they drift apart, the share to reset to.', [
    I('months', 'Complete months to check', 12, 'int'), I('tol', 'Within this share counts as holding', 0.05, 'pct')], [
    O('Shared costs', 'money', T7), O('Partner 1 paid share', 'pct', PS7), O('Agreed share of partner 1', 'pct', '{set:agreed_p1_share}'),
    O('Points apart', 'num', '(%s-{set:agreed_p1_share})*100' % PS7), O('Share to reset to, nearest 5%', 'pct', SG7),
    O('Partner 2 paid above the shares', 'money', 'SUMIFS(%s,%s,%s,%s)-(%s-SUMIFS(%s,%s))' % (SH('amount'), W7, SH('paid_by'), P2, T7, SH('p1_share'), W7)),
    O('Verdict', 'text', 'IF(ABS(%s-{set:agreed_p1_share})<={in:tol},%s,%s%sROUND(%s*100,0)&"%%")' % (PS7, V('Agreement holds'), V('Reset to'), SP, SG7))],
    GR('What if you check', ('3 months', {'months': 3}), ('6 months', {'months': 6}), ('9 months', {'months': 9}), ('12 months', {'months': 12}), ('24 months', {'months': 24}))))
# 8 shared cost categories ----------------------------------------------------------------------------------------
def CT(c): return 'SUMIFS(%s,%s,%s,%s)' % (SH('amount'), SH('category'), c, W7)
TOT8 = CT('{in:category}')
RANK8 = '1+' + '+'.join('IF(%s>%s,1,0)' % (CT(tok('sharedcat', c)), TOT8) for c in SHARED_CATS)
tools.append(TOOL('cost_categories', 'Shared Cost Categories', 'Where do the shared costs go',
    'Shared costs by category over the complete months you choose, the share of the one you pick, its rank and how much partner 2 paid.', [
    I('months', 'Complete months to look at', 12, 'int'), IL('category', 'Category', 'sharedcat', 'Household supplies')], [
    O(c, 'money', CT(tok('sharedcat', c))) for c in SHARED_CATS] + [
    O('Picked category total', 'money', TOT8), O('Share of all shared costs', 'pct', 'IFERROR(%s/%s,0)' % (TOT8, T7)), O('Rank among the categories', 'int', RANK8),
    O('Partner 2 paid in the category', 'money', 'SUMIFS(%s,%s,{in:category},%s,%s,%s)' % (SH('amount'), SH('category'), SH('paid_by'), P2, W7)),
    O('Average a month', 'money', '%s/{in:months}' % TOT8),
    O('Verdict', 'text', '{in:category}%s%s%sROUND(IFERROR(%s/%s,0)*100,0)&"%% "&%s' % (SP, V('is'), SP, TOT8, T7, V('of shared costs')))],
    GR('What if you look at', ('3 months', {'months': 3}), ('6 months', {'months': 6}), ('12 months', {'months': 12}), ('24 months', {'months': 24}))))
# 9 kids costs per child ---------------------------------------------------------------------------------------------
YW = '%s,">="&DATE({in:year},1,1),%s,"<="&DATE({in:year},12,31)' % (KC('date'), KC('date'))
def KK(kind): return 'SUMIFS(%s,%s,{in:child},%s,%s,%s)' % (KC('amount'), KC('child'), KC('kind'), tok('kidkind', kind), YW)
OWN = 'SUMIFS(%s,%s,{in:child},%s)' % (KC('amount'), KC('child'), YW)
HALF = 'IF({in:child}=%s,0,0.5*SUMIFS(%s,%s,%s,%s))' % (BOTH, KC('amount'), KC('child'), BOTH, YW)
ALLK = 'SUMIFS(%s,%s)' % (KC('amount'), YW)
MON9 = 'IF({in:year}=YEAR({today}),MONTH({today}),12)'
tools.append(TOOL('kids_per_child', 'Kids Costs per Child', 'What does each child cost a year',
    'Childcare, school, activities, clothing, allowance and other costs of one child in a year, plus half of the costs for both children.', [
    IL('child', 'Child', 'child', 'Noa'), I('year', 'Year', Y, 'int')], [
    O('Childcare', 'money', KK('Childcare')), O('School costs', 'money', KK('School costs')), O('Activities', 'money', KK('Activities')), O('Clothing', 'money', KK('Clothing')),
    O('Allowance', 'money', KK('Allowance')), O('Other', 'money', KK('Other')), O('Own costs', 'money', OWN), O('Half of the costs for both children', 'money', HALF),
    O('Total with half of both', 'money', '%s+%s' % (OWN, HALF)), O('Per month so far', 'money', '(%s+%s)/%s' % (OWN, HALF, MON9)), O('Share of all kids costs', 'pct', 'IFERROR(%s/%s,0)' % (OWN, ALLK)),
    O('Verdict', 'text', '{in:child}%s%s%sROUND(%s+%s,0)%s%s' % (SP, V('costs'), SP, OWN, HALF, SP, V('a year')))],
    GR('What if the year is', ('Two years ago', {'year': Y - 2}), ('Last year', {'year': Y - 1}), ('This year', {'year': Y}))))
# 10 allowance planner -------------------------------------------------------------------------------------------------
WD = '{in:day}'
WDN = 'IF(%s=%s,1,IF(%s=%s,2,IF(%s=%s,3,IF(%s=%s,4,IF(%s=%s,5,IF(%s=%s,6,7))))))' % tuple(x for i, d in enumerate(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']) for x in (WD, '{list:wday.%s}' % d))
DAYS10 = 'MOD(%s-WEEKDAY({today},2),7)' % WDN
AVG10 = 'SUMIFS(%s,%s,{in:child},%s,">="&({today}-365))/52' % (AL('amount'), AL('child'), AL('date'))
tools.append(TOOL('allowance_planner', 'Allowance Planner', 'What do we pay and when',
    'Weekly allowance, the day it is paid and how much is saved or spent; shows the amount a month and a year, the next pay date and your last 12 months average.', [
    IL('child', 'Child', 'kid', 'Noa'), I('amount', 'Weekly allowance', 10), I('saved', 'Share to save', 0.4, 'pct'), IL('day', 'Pay day', 'wday', 'Saturday')], [
    O('Saved each week', 'money', '{in:amount}*{in:saved}'), O('Spent each week', 'money', '{in:amount}*(1-{in:saved})'), O('Allowance a month', 'money', '{in:amount}*52/12'),
    O('Allowance a year', 'money', '{in:amount}*52'), O('Saved a year', 'money', '{in:amount}*{in:saved}*52'), O('Average paid a week, last 12 months', 'money', AVG10),
    O('Difference to your average a week', 'money', '{in:amount}-%s' % AVG10), O('Next pay date', 'date', '{today}+%s' % DAYS10), O('Days until the next pay day', 'int', DAYS10),
    O('Verdict', 'text', '%s%sROUND({in:amount},2)%s%s%s{in:day}' % (V('Pay'), SP, SP, V('on'), SP))],
    GR('What if the allowance is', ('5', {'amount': 5}), ('8', {'amount': 8}), ('10', {'amount': 10}), ('12', {'amount': 12}), ('15', {'amount': 15}))))
# 11 allowance saved check -----------------------------------------------------------------------------------------------
W11 = '%s,">="&EDATE(%s,-{in:months}),%s,"<"&%s,%s,{in:child}' % (AL('date'), MS, AL('date'), MS, AL('child'))
PD11 = 'SUMIFS(%s,%s)' % (AL('amount'), W11)
SV11 = 'SUMIFS(%s,%s)' % (AL('saved'), W11)
SS11 = 'IFERROR(%s/%s,0)' % (SV11, PD11)
tools.append(TOOL('allowance_saved', 'Allowance Saved Check', 'Is the child saving enough',
    'What a child saved against spent over the last complete months, compared with the share you want them to save.', [
    IL('child', 'Child', 'kid', 'Noa'), I('months', 'Complete months to check', 3, 'int'), I('target', 'Share you want saved', 0.3, 'pct')], [
    O('Allowance paid', 'money', PD11), O('Saved', 'money', SV11), O('Spent', 'money', '%s-%s' % (PD11, SV11)), O('Saved share', 'pct', SS11),
    O('Saved needed for the target', 'money', '{in:target}*%s' % PD11), O('Short of the target', 'money', 'MAX(0,{in:target}*%s-%s)' % (PD11, SV11)),
    O('Extra to save each week', 'money', 'MAX(0,{in:target}*%s-%s)/({in:months}*52/12)' % (PD11, SV11)),
    O('Verdict', 'text', 'IF(%s>={in:target},%s%sROUND(%s*100,0)&"%%",%s)' % (SS11, V('Saving'), SP, SS11, V('Ask to save more')))],
    GR('What if the target is', ('10%', {'target': 0.1}), ('20%', {'target': 0.2}), ('30%', {'target': 0.3}), ('40%', {'target': 0.4}), ('50%', {'target': 0.5}))))
# 12 cost per member --------------------------------------------------------------------------------------------------------
CM = lambda c: R('cost_member', c)
TOT12 = 'SUMIFS(%s,%s,{in:member},%s,{in:year})' % (CM('total'), CM('member'), CM('year'))
tools.append(TOOL('member_cost', 'Cost per Household Member', 'What does each member cost a year',
    'The yearly cost of one household member: own kids costs plus an even share of shared costs, against the whole household.', [
    IL('member', 'Household member', 'member', 'Partner 1'), I('year', 'Year', Y, 'int')], [
    O('Kids costs', 'money', 'SUMIFS(%s,%s,{in:member},%s,{in:year})' % (CM('kids_share'), CM('member'), CM('year'))),
    O('Share of shared costs', 'money', 'SUMIFS(%s,%s,{in:member},%s,{in:year})' % (CM('shared_share'), CM('member'), CM('year'))), O('Total for the year', 'money', TOT12),
    O('Per month with costs', 'money', 'SUMIFS(%s,%s,{in:member},%s,{in:year})' % (CM('per_month'), CM('member'), CM('year'))),
    O('All members, same year', 'money', 'SUMIFS(%s,%s,{in:year})' % (CM('total'), CM('year'))),
    O('Share of the household total', 'pct', 'IFERROR(%s/SUMIFS(%s,%s,{in:year}),0)' % (TOT12, CM('total'), CM('year'))),
    O('Verdict', 'text', '{in:member}%sROUND(%s,0)%s%s' % (SP, TOT12, SP, V('a year')))],
    GR('What if the year is', ('Two years ago', {'year': Y - 2}), ('Last year', {'year': Y - 1}), ('This year', {'year': Y}))))
# 13 lose one income -----------------------------------------------------------------------------------------------------------
WI = 'EDATE(%s,-%s)' % (MS, N)
OWN13 = '(%s/%s)' % (INC('{in:who}', WI, MS), N)
OTH13 = '(%s/%s-%s)' % (INCALL(WI, MS), N, OWN13)
PLAN13 = 'SUM(%s)' % LO('plan')
GAP13 = '(%s-(%s+%s*{in:kept}))' % (PLAN13, OTH13, OWN13)
CUT13 = 'SUM(%s)' % LO('cut_amount')
AFT13 = 'MAX(0,%s-%s)' % (GAP13, CUT13)
FUND13 = 'IF({in:fund}>0,{in:fund},{set:emergency_balance})'
tools.append(TOOL('lose_income', 'Lose One Income Test', 'What if one income stops or drops',
    'Set one partner\'s income to zero or a share: the new monthly gap, the cuts that close part of it and the months of emergency fund that cover the rest.', [
    IL('who', 'Whose income changes', 'payer', 'Partner 2'), I('kept', 'Share of that income kept', 0, 'pct'), I('fund', 'Emergency fund, 0 = from Settings', 0)], [
    O('Their take-home a month', 'money', OWN13), O('Income lost a month', 'money', '%s*(1-{in:kept})' % OWN13), O('Other income a month', 'money', OTH13), O('Plan a month', 'money', PLAN13),
    O('Gap a month before cuts', 'money', GAP13), O('Cuts available', 'money', CUT13), O('Gap a month after cuts', 'money', AFT13),
    O('Months of cover with the cuts', 'num', 'IF(%s>0,%s/%s,0)' % (AFT13, FUND13, AFT13)), O('Months of essential spending in the fund', 'num', '%s/%s' % (FUND13, NEED())),
    O('Verdict', 'text', 'IF(%s<=0,%s,%s%sROUND(%s,0)%s%s%sIF(%s<=0,%s,ROUND(%s/%s,1)%s%s))' % (GAP13, V('No gap, income covers the plan'), V('Gap'), SP, GAP13, SP, V('a month,'), SP, AFT13, V('Cuts close the gap'), FUND13, AFT13, SP, V('months of cover with the cuts')))],
    GR('What if the share kept is', ('None kept', {'kept': 0}), ('25% kept', {'kept': 0.25}), ('50% kept', {'kept': 0.5}), ('75% kept', {'kept': 0.75}), ('All kept', {'kept': 1}))))
# 14 cut list ----------------------------------------------------------------------------------------------------------------------
def RK(k, col, d): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),%s)' % (LO(col), k, LO('rank_cut'), d)
tools.append(TOOL('cut_list', 'Cut List to Close the Gap', 'Which categories do we cut first',
    'Categories ranked by the amount you could cut, how many it takes to close the gap you type and what is left if you cut them all.', [
    I('gap', 'Monthly gap to close', 2500)], sum(([O('Cut %d: category' % k, 'text', RK(k, 'category', '""')), O('Cut %d: amount' % k, 'money', RK(k, 'cut_amount', '0'))] for k in range(1, 6)), []) + [
    O('Top five cuts together', 'money', '+'.join(RK(k, 'cut_amount', '0') for k in range(1, 6))), O('All cuts available', 'money', CUT13),
    O('Categories needed to close the gap', 'int', 'COUNTIFS(%s,"<"&{in:gap},%s,">0")' % (LO('bigger_cuts'), LO('cut_amount'))), O('Gap left after all cuts', 'money', 'MAX(0,{in:gap}-%s)' % CUT13),
    O('Verdict', 'text', 'IF({in:gap}<=0,%s,IF(%s<{in:gap},%s,%s%sROUND(%s,0)%s%s%s%s))' % (V('No cut needed'), CUT13, V('Cuts do not close the gap'), V('Cut'), SP, RK(1, 'cut_amount', '0'), SP, V('from'), SP, RK(1, 'category', '""')))],
    GR('What if the gap is', ('500', {'gap': 500}), ('1000', {'gap': 1000}), ('2000', {'gap': 2000}), ('3000', {'gap': 3000}), ('4000', {'gap': 4000}))))
# 15 expense shock ------------------------------------------------------------------------------------------------------------------
USED15 = 'MAX(0,{in:cost}-{in:cash})/%s' % NEED()
NP = lambda pv: 'NPER({in:card_rate}/12,-{in:card_pay},%s)' % pv
DEL15 = 'IFERROR(%s-%s,0)' % (NP('{in:card_bal}+{in:cost}'), NP('{in:card_bal}'))
tools.append(TOOL('shock_test', 'Expense Shock Test', 'Can we absorb a one-off cost',
    'A one-off cost paid from cash above your floor first, then from the emergency fund: the low point, the months of essentials used and the delay if it went on a card.', [
    I('cost', 'One-off cost', 3500), I('cash', 'Cash you can use above your floor', 600), I('low', 'Lowest joint balance before payday', 1400), I('floor', 'Your cash floor', 500),
    I('card_bal', 'Card balance', 3300), I('card_rate', 'Card yearly rate', 0.1999, 'pct'), I('card_pay', 'Card payment a month', 245)], [
    O('Paid from cash', 'money', 'MIN({in:cost},{in:cash})'), O('Paid from the emergency fund', 'money', 'MAX(0,{in:cost}-{in:cash})'),
    O('Emergency fund after', 'money', '{set:emergency_balance}-MAX(0,{in:cost}-{in:cash})'), O('Months of essentials left', 'num', 'MAX(0,{set:emergency_balance}-MAX(0,{in:cost}-{in:cash}))/%s' % NEED()),
    O('Months of essentials used', 'num', USED15), O('Low point after the cash part', 'money', '{in:low}-MIN({in:cost},{in:cash})'),
    O('Low point against your floor', 'money', '{in:low}-MIN({in:cost},{in:cash})-{in:floor}'), O('Months added if all of it goes on the card', 'num', DEL15),
    O('Extra interest if all of it goes on the card', 'money', 'IF(%s>0,{in:card_pay}*%s-{in:cost},0)' % (DEL15, DEL15)),
    O('Verdict', 'text', 'IF({in:cost}<={in:cash},%s,%s%sROUND(%s,1)%s%s)' % (V('Covered'), V('Uses'), SP, USED15, SP, V('months of emergency fund')))],
    GR('What if the cost is', ('500', {'cost': 500}), ('1000', {'cost': 1000}), ('2000', {'cost': 2000}), ('3500', {'cost': 3500}), ('5000', {'cost': 5000}), ('8000', {'cost': 8000}))))
# 16 rate change -----------------------------------------------------------------------------------------------------------------------
PN16 = 'IF({in:term}>0,PMT({in:rate}/12,{in:term},-{in:balance}),{in:balance}*{in:rate}/12)'
PA16 = 'IF({in:term}>0,PMT(({in:rate}+{in:points})/12,{in:term},-{in:balance}),{in:balance}*({in:rate}+{in:points})/12)'
tools.append(TOOL('rate_test', 'Interest-rate Change Test', 'What does a rate rise do to the payment',
    'Points added to a variable loan or card: the new payment (interest only when the months left is 0), the rise a month and the extra cost over a year and the rest of the term.', [
    I('balance', 'Balance', 13600), I('rate', 'Yearly rate now', 0.0699, 'pct'), I('term', 'Months left, 0 on a card', 36, 'int'), I('points', 'Points added to the rate', 0.02, 'pct')], [
    O('Rate after', 'pct', '{in:rate}+{in:points}'), O('Payment now', 'money', PN16), O('Payment after', 'money', PA16), O('Rise a month', 'money', '%s-%s' % (PA16, PN16)),
    O('Rise in the payment', 'pct', 'IFERROR((%s-%s)/%s,0)' % (PA16, PN16, PN16)), O('Extra cost a year', 'money', '12*(%s-%s)' % (PA16, PN16)),
    O('Extra cost over the months left', 'money', 'IF({in:term}>0,{in:term},12)*(%s-%s)' % (PA16, PN16)),
    O('Verdict', 'text', 'IF({in:points}<=0,%s,%s%sROUND(%s-%s,0))' % (V('No change in the payment'), V('Payment rises by'), SP, PA16, PN16))],
    GR('What if the points are', ('0.5 point', {'points': 0.005}), ('1 point', {'points': 0.01}), ('2 points', {'points': 0.02}), ('3 points', {'points': 0.03}), ('4 points', {'points': 0.04}))))
# 17 new baby -----------------------------------------------------------------------------------------------------------------------------
G1 = '({in:monthly}+{in:loss}*{in:income}-{in:surplus})'
G2 = '({in:monthly}-{in:surplus})'
LEFT17 = '({in:savings}-{in:one_off})'
MON17 = 'IF(%s<=0,0,IF(%s<=0,999,IF(%s<={in:leave}*%s,%s/%s,{in:leave}+IF(%s>0,(%s-{in:leave}*%s)/%s,999))))' % (LEFT17, G1, LEFT17, G1, LEFT17, G1, G2, LEFT17, G1, G2)
tools.append(TOOL('baby_plan', 'New Baby Plan', 'Can we afford leave and the first year',
    'One-off and monthly baby costs, income lost on leave and your monthly surplus: the monthly gap, how long savings last and what to save before the birth.', [
    I('one_off', 'One-off costs', 2400), I('monthly', 'Monthly costs', 420), I('leave', 'Months of leave', 4, 'int'), I('loss', 'Share of income lost on leave', 0.4, 'pct'),
    I('income', 'Take-home of the partner on leave', 4680), I('surplus', 'Money left over each month now', 350), I('savings', 'Savings set aside', 8000), I('before', 'Months before the birth', 6, 'int')], [
    O('Gap a month during leave', 'money', G1), O('Gap a month after leave', 'money', G2), O('Income lost during leave', 'money', '{in:leave}*{in:loss}*{in:income}'),
    O('Total gap over the leave with one-off costs', 'money', '{in:one_off}+{in:leave}*%s' % G1), O('Months the savings last', 'num', 'MIN(99,%s)' % MON17),
    O('Save a month before the birth', 'money', 'MAX(0,({in:one_off}+{in:leave}*%s-{in:savings})/{in:before})' % G1),
    O('Verdict', 'text', 'IF(%s>=99,%s,%s%sROUND(%s,0)&", "&%s%sROUND(%s,1)%s%s)' % (MON17, V('Savings cover the plan'), V('Gap'), SP, G1, V('savings last'), SP, MON17, SP, V('months')))],
    GR('What if the leave is', ('2 months', {'leave': 2}), ('3 months', {'leave': 3}), ('4 months', {'leave': 4}), ('6 months', {'leave': 6}), ('12 months', {'leave': 12}))))
# 18 mortgage switch ----------------------------------------------------------------------------------------------------------------------
PAY18 = 'PMT({in:rate}/12,{in:years}*12,-({in:price}-{in:down}))'
TOT18 = '(%s+{in:upkeep}/12+{in:other})' % PAY18
DIF18 = '(%s-{in:rent})' % TOT18
tools.append(TOOL('mortgage_switch', 'Mortgage Switch Scenario', 'What changes if we move from rent to a mortgage',
    'Rent against a typed mortgage payment, yearly upkeep and local charges and other monthly changes; your numbers, not advice.', [
    I('price', 'Price', 310000), I('down', 'Down payment', 40000), I('rate', 'Yearly rate', 0.059, 'pct'), I('years', 'Term in years', 25, 'int'), I('upkeep', 'Upkeep and local charges a year', 3100),
    I('rent', 'Rent now, a month', 1650), I('other', 'Other monthly costs that change', 286)], [
    O('Loan', 'money', '{in:price}-{in:down}'), O('Mortgage payment a month', 'money', PAY18), O('Upkeep a month', 'money', '{in:upkeep}/12'), O('Total new cost a month', 'money', TOT18),
    O('Difference a month', 'money', DIF18), O('Difference a year', 'money', '12*%s' % DIF18), O('Interest in the first year, estimate', 'money', '({in:price}-{in:down})*{in:rate}'),
    O('New cost as a share of take-home', 'pct', 'IFERROR(%s/(%s/%s),0)' % (TOT18, INCALL(WI, MS), N)),
    O('Verdict', 'text', 'IF(ABS(%s)<1,%s,ROUND(ABS(%s),0)%sIF(%s>0,%s,%s))' % (DIF18, V('No difference'), DIF18, SP, DIF18, V('more a month, your numbers, not advice'), V('less a month, your numbers, not advice')))],
    GR('What if the rate is', ('4%', {'rate': 0.04}), ('5%', {'rate': 0.05}), ('5.9%', {'rate': 0.059}), ('7%', {'rate': 0.07}), ('8%', {'rate': 0.08}))))
assert len(tools) == 18
