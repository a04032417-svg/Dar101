"""Home care agency suite part 7: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc7_lists import *
import hc7_data as DT
import collections


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
O = OUT
YES = '{list:yesno.yes}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def M6(): return 'DATE(YEAR({today}),MONTH({today})-6,1)'

# ---- agency numbers for the default inputs
_tot = sum(m['hours'] for m in DT.MG.values())
AVG_RATE = round(sum(m['hours'] * m['rate'] for m in DT.MG.values()) / _tot, 2)
AVG_COST = round(sum(m['hours'] * m['cost_h'] for m in DT.MG.values()) / _tot, 2)
_sv = collections.defaultdict(lambda: [0.0, 0.0, 0.0]); _py = collections.defaultdict(lambda: [0.0, 0.0, 0.0])
for _c in DT.ACT:
    if _c['client_id'] not in DT.MG: continue
    _m = DT.MG[_c['client_id']]
    for _d, _k in ((_sv, _c['service']), (_py, _c['payer'])):
        _d[_k][0] += _m['hours']; _d[_k][1] += _m['hours'] * _m['rate']; _d[_k][2] += _m['hours'] * _m['cost_h']
SV_H = {k: round(v[0]) for k, v in _sv.items()}; SV_M = {k: round((v[1] - v[2]) / v[1], 3) for k, v in _sv.items()}
PY_H = {k: round(v[0]) for k, v in _py.items()}
_last6 = DT.GR[-7:-1]
NET6 = sum(r['hours_added'] - r['hours_lost'] for r in _last6); END6 = sum(r['clients_ended'] for r in _last6); LOST6 = sum(r['hours_lost'] for r in _last6)
ACT0 = DT.GR[-8]['active_clients']
_st = [r for r in DT.starts_d() if r.get('hours_90') not in (None, '')]
ST_H0 = round(sum(r['hours_start'] for r in _st) / len(_st), 1); ST_H90 = round(sum(r['hours_90'] for r in _st) / len(_st), 1)

# ---- 1 margin per client hour
PAYV = '({in:pay}*{in:hours})'; TRV = '({in:pay}*{in:travel}/60)'; OTV = '(({in:otm}-1)*{in:pay}*{in:hours}*{in:ot})'; CVV = '({set:cover_premium}*{in:hours}*{in:cover})'; MIV = '({in:km}*{set:mileage_rate})'
LOADV = '((%s+%s+%s+%s)*(1+{in:burden})+%s)' % (PAYV, TRV, OTV, CVV, MIV)
SH1 = '(({in:rate}-%s/{in:hours})/{in:rate})' % LOADV
V1 = 'IF(%s>={set:target_margin},%s,IF(%s>={set:red_margin},%s,IF(%s>=0,%s,%s)))' % (SH1, ck('On target'), SH1, ck('Below target'), SH1, ck('Below 30 percent'), ck('Negative margin'))
# ---- 3 keep this client
HPV = '({in:hours}/{in:visits})'
LD3 = '(({in:pay}+{in:pay}*{in:travel}/60/%s+{in:cover}/{in:hours})*(1+{set:payroll_burden})+{in:km}*{set:mileage_rate}/%s)' % (HPV, HPV)
SH3 = '(({in:rate}-%s)/{in:rate})' % LD3
NEED3 = '(%s/(1-{set:target_margin})/{in:rate}-1)' % LD3
# ---- 7 minimum visit loss
BIL7 = 'MAX({in:minv},{in:hrs})'; WRK7 = '({in:hrs}+{in:travel}/60)'
COST7 = '(%s*{in:pay}*(1+{in:burden})+{in:km}*{set:mileage_rate})' % WRK7; REV7 = '(%s*{in:rate})' % BIL7
TRC7 = '({in:travel}/60*{in:pay}*(1+{in:burden})+{in:km}*{set:mileage_rate})'
SHORT7 = '({set:target_margin}*%s-(%s-%s))' % (REV7, REV7, COST7)
# ---- 8 minimum change
GAIN8 = '({in:visits}*MAX(0,{in:newmin}-MAX({in:avg},{in:minnow})))'
# ---- 9 pay scenario
D9 = '({in:rise}*{in:covers}*(1+{set:payroll_burden}))'
# ---- 11 hours forecast
AVG11 = '({in:net6}/6*{in:trend})'
# ---- 12 churn
CH12 = '({in:ended}/{in:active}/{in:months})'
# ---- 15 service mix
SVS = ['Companion care', 'Personal care help', 'Homemaking', 'Respite care', 'Overnight care', 'Live-in day']
H15 = ['{in:h%d}' % i for i in range(1, 7)]; M15 = ['{in:m%d}' % i for i in range(1, 7)]
MAXM = 'MAX(%s)' % ','.join('IF(%s>0,%s,-9)' % (h, m) for h, m in zip(H15, M15))
MINM = 'MIN(%s)' % ','.join('IF(%s>0,%s,9)' % (h, m) for h, m in zip(H15, M15))
def PICK15(target):
    s = tok('svc', SVS[5])
    for i in range(4, -1, -1): s = 'IF(IF(%s>0,%s,%s)=%s,%s,%s)' % (H15[i], M15[i], '-9' if target == MAXM else '9', target, tok('svc', SVS[i]), s)
    return s
# ---- 16 payer mix
PN = ['Private pay', 'Care insurer', 'Third-party payer A', 'Third-party payer B']
HP = ['{in:p%d}' % i for i in range(1, 5)]; SP = ['{in:s%d}' % i for i in range(1, 5)]
REV16 = '(%s)' % '+'.join('%s*{in:rate}*%s' % (h, s) for h, s in zip(HP, SP))
CST16 = '({in:cost}*(%s))' % '+'.join(HP)

tools = [
 TOOL('margin_hour', 'Margin per Client Hour', 'Margin per client hour with the traffic light',
  'Type the rate, pay, burden, visit hours, travel, kilometres, overtime and cover share for one client; see loaded cost, margin per hour and per week, margin share and the traffic light.', [
  I('rate', 'Bill rate per hour', 36, 'money'), I('pay', 'Pay rate per hour', 17.5, 'money'), I('burden', 'Payroll burden on pay (confirm with your adviser)', 0.2, 'pct'), I('hours', 'Hours billed per visit', 3, 'num'),
  I('travel', 'Paid travel minutes per visit', 15), I('km', 'Kilometres per visit', 6, 'num'), I('ot', 'Share of hours paid as overtime', 0.02, 'pct'), I('otm', 'Overtime multiplier', 1.5, 'num'),
  I('cover', 'Share of hours covered at short notice', 0.1, 'pct'), I('weekly', 'Weekly hours for this client', 12, 'num')], [
  O('Pay cost per visit', 'money', PAYV), O('Paid travel per visit', 'money', TRV), O('Overtime cost per visit', 'money', OTV), O('Cover premium per visit', 'money', CVV),
  O('Payroll burden per visit', 'money', '((%s+%s+%s+%s)*{in:burden})' % (PAYV, TRV, OTV, CVV)), O('Mileage per visit', 'money', MIV), O('Loaded cost per visit', 'money', LOADV),
  O('Loaded cost per hour', 'money', LOADV + '/{in:hours}'), O('Margin per hour', 'money', '{in:rate}-%s/{in:hours}' % LOADV), O('Margin per visit', 'money', '{in:rate}*{in:hours}-%s' % LOADV),
  O('Margin per week', 'money', '({in:rate}-%s/{in:hours})*{in:weekly}' % LOADV), O('Margin share', 'pct', SH1), O('Wanted margin share', 'pct', '{set:target_margin}'),
  O('Rate needed for the target margin', 'money', '%s/{in:hours}/(1-{set:target_margin})' % LOADV), O('Traffic light', 'text', V1)],
  GR('What if', ('Rate 38 an hour', {'rate': 38}), ('Pay 18.5 an hour', {'pay': 18.5}), ('Travel 30 minutes', {'travel': 30}), ('Short visits: 2 hours', {'hours': 2}), ('Far client: 15 km', {'km': 15}))),
 TOOL('worst_rank', 'Worst-first Ranking', 'Worst-first client ranking against the target',
  'Pick how many of the weakest clients to count and the target; see the eight weakest clients with their margin shares, the money lost against the target a week and the verdict. Read from Client Margin.', [
  I('count', 'Weakest clients to count in the total (1 to 8)', 3), I('target', 'Target margin share', 0.35, 'pct')], [
  O('Weakest %d: client' % k if False else 'Weakest %d: %s' % (k, w), f, 'IFERROR(INDEX({range:margin.%s},MATCH(%d,{range:margin.rank},0)),"")' % (c, k)) for k in range(1, 9) for w, f, c in (('client', 'text', 'client'), ('margin share', 'pct', 'margin_pct'))][:16] + [
  O('Clients below the target margin', 'int', 'COUNTIFS({range:margin.margin_pct},"<"&{in:target})'),
  O('Money lost a week against the target, weakest counted', 'money', 'ROUND(MAX(0,{in:target}*SUMIFS({range:margin.revenue_week},{range:margin.rank},"<="&{in:count})-SUMIFS({range:margin.margin_week},{range:margin.rank},"<="&{in:count})),0)'),
  O('Money lost a week against the target, all below it', 'money', 'ROUND({in:target}*SUMIFS({range:margin.revenue_week},{range:margin.margin_pct},"<"&{in:target})-SUMIFS({range:margin.margin_week},{range:margin.margin_pct},"<"&{in:target}),0)'),
  O('Verdict', 'text', 'IF(SUMIFS({range:margin.gap_week},{range:margin.rank},"<="&{in:count})>0,%s,%s)' % (vd('Act first'), vd('All on target')))],
  GR('What if', ('Weakest 1 only', {'count': 1}), ('Weakest 5', {'count': 5}), ('All 8 shown', {'count': 8}), ('Floor of 30 percent', {'target': 0.30}), ('Target of 40 percent', {'target': 0.40}))),
 TOOL('keep_client', 'Keep This Client', 'Should I keep this client? Keep, raise the rate or release',
  'Type the client\'s hours, rate, pay, travel and late payments; see the margin share, the rate that reaches the target, the rise needed and the verdict Keep, Raise the rate or Release.', [
  I('hours', 'Weekly hours', 12, 'num'), I('visits', 'Visits a week', 4, 'num'), I('rate', 'Bill rate per hour', 30.6, 'money'), I('pay', 'Average pay per hour', 20.9, 'money'), I('travel', 'Paid travel minutes per visit', 30),
  I('km', 'Kilometres per visit', 16, 'num'), I('cover', 'Cover premium paid per week', 0, 'money'), I('late', 'Late payments in the last 90 days', 0)], [
  O('Loaded cost per hour', 'money', LD3), O('Margin per hour', 'money', '{in:rate}-%s' % LD3), O('Margin share', 'pct', SH3), O('Margin per week', 'money', '({in:rate}-%s)*{in:hours}' % LD3),
  O('Rate that reaches the target margin', 'money', '%s/(1-{set:target_margin})' % LD3), O('Rate rise needed, percent', 'pct', 'MAX(0,%s)' % NEED3), O('Largest rise you propose at once, percent', 'pct', '{set:max_rise_pct}'),
  O('Margin share after the largest rise', 'pct', '(({in:rate}*(1+{set:max_rise_pct})-%s)/({in:rate}*(1+{set:max_rise_pct})))' % LD3),
  O('Gap to the target a week', 'money', 'MAX(0,{set:target_margin}*{in:rate}*{in:hours}-({in:rate}-%s)*{in:hours})' % LD3),
  O('Verdict', 'text', 'IF(%s>={set:target_margin},%s,IF(AND(%s<={set:max_rise_pct},{in:late}<3),%s,%s))' % (SH3, vd('Keep'), NEED3, vd('Raise the rate'), vd('Release')))],
  GR('What if', ('Rate up 5 percent', {'rate': '={in:rate}*1.05'}), ('Rate up 10 percent', {'rate': '={in:rate}*1.1'}), ('Cluster the visits: 10 minutes', {'travel': 10}), ('Three visits a week', {'visits': 3}), ('Three late payments', {'late': 3}))),
 TOOL('rate_needed', 'Rate for Target', 'Rate needed for the target margin',
  'Type the loaded cost per hour, the rate now and the weekly hours; see the rate that reaches the target, the rise in money and percent, and the rise per week for the client.', [
  I('loaded', 'Loaded cost per hour', 23.5, 'money'), I('rate', 'Bill rate per hour now', 34, 'money'), I('hours', 'Weekly hours', 12, 'num'), I('target', 'Target margin share', 0.35, 'pct')], [
  O('Margin share now', 'pct', '({in:rate}-{in:loaded})/{in:rate}'), O('Rate needed for the target margin', 'money', '{in:loaded}/(1-{in:target})'), O('Rise in money per hour', 'money', 'MAX(0,{in:loaded}/(1-{in:target})-{in:rate})'),
  O('Rise, percent', 'pct', 'MAX(0,{in:loaded}/(1-{in:target})/{in:rate}-1)'), O('Rise per week for the client', 'money', 'MAX(0,{in:loaded}/(1-{in:target})-{in:rate})*{in:hours}'),
  O('Rate that reaches the red-line margin', 'money', '{in:loaded}/(1-{set:red_margin})'), O('Rise to reach the red line, percent', 'pct', 'MAX(0,{in:loaded}/(1-{set:red_margin})/{in:rate}-1)'),
  O('Verdict', 'text', 'IF({in:rate}>={in:loaded}/(1-{in:target}),%s,%s)' % (vd('Rate is enough'), vd('Raise the rate')))],
  GR('What if', ('Target 30 percent', {'target': 0.30}), ('Target 40 percent', {'target': 0.40}), ('Cost 26 an hour', {'loaded': 26}), ('Cost 21 an hour', {'loaded': 21}), ('Rate 36 an hour', {'rate': 36}))),
 TOOL('rise_effect', 'Rate Rise Effect', 'Rate rise effect with the chance the client leaves',
  'Type the rise, the chance the client leaves, weekly hours, rate and margin per hour; see the gain, the margin lost if they leave, the expected net effect and the verdict.', [
  I('rise', 'Rate rise, percent', 0.05, 'pct'), I('leave', 'Chance the client leaves (your guess)', 0.10, 'pct'), I('hours', 'Weekly hours', 12, 'num'), I('rate', 'Bill rate per hour now', 34, 'money'), I('mhour', 'Margin per hour now', 8, 'money')], [
  O('New rate per hour', 'money', '{in:rate}*(1+{in:rise})'), O('Income gain a year if they stay', 'money', '{in:hours}*52*{in:rate}*{in:rise}'), O('Margin lost a year if they leave', 'money', '{in:mhour}*{in:hours}*52'),
  O('Expected net effect a year', 'money', '(1-{in:leave})*{in:hours}*52*{in:rate}*{in:rise}-{in:leave}*{in:mhour}*{in:hours}*52'),
  O('Chance of leaving that cancels the gain', 'pct', '{in:hours}*52*{in:rate}*{in:rise}/({in:hours}*52*{in:rate}*{in:rise}+{in:mhour}*{in:hours}*52)'),
  O('Margin share after the rise', 'pct', '({in:mhour}+{in:rate}*{in:rise})/({in:rate}*(1+{in:rise}))'),
  O('Verdict', 'text', 'IF((1-{in:leave})*{in:rate}*{in:rise}-{in:leave}*{in:mhour}<=0,%s,IF((1-{in:leave})*{in:rate}*{in:rise}-{in:leave}*{in:mhour}<0.25*{in:rate}*{in:rise},%s,%s))' % (vd('Hold'), vd('Raise less'), vd('Raise')))],
  GR('What if', ('Rise 3 percent', {'rise': 0.03}), ('Rise 8 percent', {'rise': 0.08}), ('Medium risk: 15 percent leave', {'leave': 0.15}), ('High risk: 35 percent leave', {'leave': 0.35}), ('Strong client: margin 12', {'mhour': 12}))),
 TOOL('rise_planner', 'Rate Rise Planner', 'Rate-rise planner ranking by expected net effect',
  'Pick how many clients to count; the eight best rate rises by expected net effect a year are listed in the order to raise them, with the total gain. Read from Rate Rise Proposals.', [
  I('count', 'Clients to count in the total (1 to 8)', 8)], [
  O('Raise first %d: %s' % (k, w), f, 'IFERROR(INDEX({range:rises.%s},MATCH(%d,{range:rises.net_rank},0)),"")' % (c, k)) for k in range(1, 9) for w, f, c in (('client', 'text', 'client'), ('expected net a year', 'money', 'expected_net'))] + [
  O('Expected gain a year, clients counted', 'money', 'ROUND(SUMIFS({range:rises.expected_net},{range:rises.net_rank},"<="&{in:count},{range:rises.expected_net},">0"),0)'),
  O('Expected gain a year, all clients', 'money', 'ROUND(SUMIFS({range:rises.expected_net},{range:rises.expected_net},">0"),0)'),
  O('Clients with a positive expected net', 'int', 'COUNTIFS({range:rises.expected_net},">0")'),
  O('Verdict', 'text', 'IF(SUMIFS({range:rises.expected_net},{range:rises.expected_net},">0")>0,%s,%s)' % (vd('Raise now'), vd('Nothing to raise')))][:20],
  GR('What if', ('Only the first client', {'count': 1}), ('First three', {'count': 3}), ('First five', {'count': 5}), ('All eight', {'count': 8}))),
 TOOL('minvisit_loss', 'Minimum Visit Loss', 'Minimum-visit loss check for one client',
  'Type the hours worked, the minimum visit, travel, pay and rate; see the hours billed against the hours worked plus travel, the true margin per visit and the verdict.', [
  I('hrs', 'Hours worked per visit', 1.6, 'num'), I('minv', 'Minimum visit, hours', 2, 'num'), I('travel', 'Paid travel minutes per visit', 25), I('km', 'Kilometres per visit', 8, 'num'), I('pay', 'Pay rate per hour', 18.5, 'money'),
  I('burden', 'Payroll burden on pay (confirm with your adviser)', 0.2, 'pct'), I('rate', 'Bill rate per hour', 34, 'money')], [
  O('Hours billed', 'num', BIL7), O('Hours worked plus travel', 'num', WRK7), O('Billed minus worked plus travel, hours', 'num', '%s-%s' % (BIL7, WRK7)), O('Revenue per visit', 'money', REV7), O('Loaded cost per visit', 'money', COST7),
  O('True margin per visit', 'money', '%s-%s' % (REV7, COST7)), O('Margin share per visit', 'pct', '(%s-%s)/%s' % (REV7, COST7, REV7)), O('Travel charge per visit that closes the gap', 'money', 'MAX(0,MIN(%s,%s))' % (TRC7, SHORT7)),
  O('Minimum visit that reaches the target, hours', 'num', 'ROUNDUP(%s/({in:rate}*(1-{set:target_margin}))*4,0)/4' % COST7),
  O('Verdict', 'text', 'IF((%s-%s)/%s>={set:target_margin},%s,IF(%s>=%s,%s,%s))' % (REV7, COST7, REV7, vd('Fine'), TRC7, SHORT7, vd('Add a travel charge'), vd('Raise the minimum')))],
  GR('What if', ('Longer visit: 2.5 hours', {'hrs': 2.5}), ('Minimum 3 hours', {'minv': 3}), ('Far client: 50 minutes', {'travel': 50}), ('Close client: 8 minutes', {'travel': 8}), ('Rate 38 an hour', {'rate': 38}))),
 TOOL('minvisit_change', 'Minimum Visit Change', 'Minimum visit change test: hours gained against clients lost',
  'Type the minimum now and the new one, the visits it touches, the hours worked, the rate and the clients who might leave; see the billed hours and revenue gained and the net effect.', [
  I('minnow', 'Minimum visit now, hours', 2, 'num'), I('newmin', 'New minimum visit, hours', 3, 'num'), I('visits', 'Visits a month shorter than the new minimum', 28), I('avg', 'Average hours worked on those visits', 2.3, 'num'),
  I('rate', 'Bill rate per hour', 34, 'money'), I('clients', 'Clients affected', 6), I('leave', 'Chance each one leaves (your guess)', 0.15, 'pct'), I('wh', 'Weekly hours per affected client', 9, 'num'), I('mshare', 'Margin share of those clients', 0.3, 'pct')], [
  O('Billed hours gained a month', 'num', GAIN8), O('Revenue gained a month', 'money', GAIN8 + '*{in:rate}'), O('Revenue gained a year', 'money', GAIN8 + '*{in:rate}*12'),
  O('Clients who might leave (expected)', 'num', '{in:clients}*{in:leave}'), O('Margin lost a year if they leave', 'money', '{in:clients}*{in:leave}*{in:wh}*52*{in:rate}*{in:mshare}'),
  O('Net effect a year', 'money', GAIN8 + '*{in:rate}*12-{in:clients}*{in:leave}*{in:wh}*52*{in:rate}*{in:mshare}'),
  O('Verdict', 'text', 'IF(%s*{in:rate}*12-{in:clients}*{in:leave}*{in:wh}*52*{in:rate}*{in:mshare}>0,%s,%s)' % (GAIN8, vd('Change the minimum'), vd('Keep the minimum')))],
  GR('What if', ('Minimum 2.5 hours', {'newmin': 2.5}), ('Minimum 4 hours', {'newmin': 4}), ('More clients leave: 30 percent', {'leave': 0.3}), ('Fewer clients affected: 3', {'clients': 3}), ('Rate 36 an hour', {'rate': 36}))),
 TOOL('pay_scenario', 'Pay Rate Scenario', 'Pay-rate scenario test: margin, cost and the rate needed',
  'Type the pay rise, the share of hours covered, billed hours a month and your turnover guess; see margin after the rise, its cost, turnover cost saved and the bill rate rise needed.', [
  I('rise', 'Pay rise per hour', 0.75, 'money'), I('covers', 'Share of caregiver hours covered', 0.5, 'pct'), I('hours', 'Billed hours a month', 3900), I('turn', 'Change in yearly turnover (your guess)', -0.05, 'pct'),
  I('caregivers', 'Caregivers', 38), I('replace', 'Cost per replacement', 2400, 'money'), I('rate', 'Average bill rate per hour', AVG_RATE, 'money'), I('mnow', 'Average margin per hour now', round(AVG_RATE - AVG_COST, 2), 'money')], [
  O('Cost of the rise per client hour', 'money', D9), O('Margin per hour after the rise', 'money', '{in:mnow}-' + D9), O('Margin share now', 'pct', '{in:mnow}/{in:rate}'), O('Margin share after the rise', 'pct', '({in:mnow}-%s)/{in:rate}' % D9),
  O('Cost of the rise a month', 'money', D9 + '*{in:hours}'), O('Cost of the rise a year', 'money', D9 + '*{in:hours}*12'), O('Turnover cost saved a year', 'money', '-{in:turn}*{in:caregivers}*{in:replace}'),
  O('Net cost or saving a year', 'money', '-{in:turn}*{in:caregivers}*{in:replace}-%s*{in:hours}*12' % D9), O('Bill rate rise clients would need, percent', 'pct', D9 + '/({in:rate}-{in:mnow})'),
  O('Verdict', 'text', 'IF(({in:mnow}-%s)/{in:rate}>={set:target_margin},%s,%s)' % (D9, vd('On target'), vd('Below target')))],
  GR('What if', ('Rise 0.25 an hour', {'rise': 0.25}), ('Rise 1.50 an hour', {'rise': 1.5}), ('Everyone covered', {'covers': 1}), ('Turnover falls 10 points', {'turn': -0.10}), ('Replacement costs 1,200', {'replace': 1200}))),
 TOOL('pay_vs_turnover', 'Pay Rise vs Turnover', 'Pay rise against turnover: does it pay for itself',
  'Type the pay rise, caregivers, hours per caregiver, the leavers you expect to avoid and the cost per replacement; see the cost a year, the saving, the leavers needed to break even and the verdict.', [
  I('rise', 'Pay rise per hour', 0.5, 'money'), I('caregivers', 'Caregivers covered', 38), I('hpm', 'Hours per caregiver per month', 100), I('avoid', 'Leavers avoided a year (your guess)', 3), I('replace', 'Cost per replacement', 2400, 'money')], [
  O('Cost of the rise a year', 'money', '{in:rise}*{in:caregivers}*{in:hpm}*12*(1+{set:payroll_burden})'), O('Saving from leavers avoided a year', 'money', '{in:avoid}*{in:replace}'),
  O('Net cost or saving a year', 'money', '{in:avoid}*{in:replace}-{in:rise}*{in:caregivers}*{in:hpm}*12*(1+{set:payroll_burden})'),
  O('Leavers to avoid to break even', 'num', '{in:rise}*{in:caregivers}*{in:hpm}*12*(1+{set:payroll_burden})/{in:replace}'), O('Cost of the rise per caregiver a year', 'money', '{in:rise}*{in:hpm}*12*(1+{set:payroll_burden})'),
  O('Cost per replacement from your settings', 'money', '{set:hire_ad_cost}+{set:background_check_cost}+{set:onboard_hours}*AVERAGEIFS({range:paycg.pay_rate},{range:paycg.status},%s)*(1+{set:payroll_burden})+{set:replace_extra}' % tok('cgstatus', 'Active')),
  O('Verdict', 'text', 'IF({in:avoid}*{in:replace}>={in:rise}*{in:caregivers}*{in:hpm}*12*(1+{set:payroll_burden}),%s,%s)' % (vd('Worth it'), vd('Not yet')))],
  GR('What if', ('Rise 0.25 an hour', {'rise': 0.25}), ('Rise 1.00 an hour', {'rise': 1.0}), ('Six leavers avoided', {'avoid': 6}), ('Replacement costs 3,500', {'replace': 3500}), ('Only 12 caregivers covered', {'caregivers': 12}))),
 TOOL('hours_forecast', 'Hours Growth Forecast', 'Hours growth forecast to 12 months and the marker month',
  'Type the net hours of the last 6 months, a trend factor and the weekly hours now; see the weekly hours in 3, 6 and 12 months and the month the hours marker is reached. Your own history sits beside it.', [
  I('net6', 'Net weekly hours of the last 6 months', NET6, 'num'), I('trend', 'Trend factor (1 = same pace)', 1, 'num'), I('start', 'Weekly hours now', 909, 'num')], [
  O('Net weekly hours per month, forecast', 'num', AVG11), O('Weekly hours in 3 months', 'num', '{in:start}+3*' + AVG11), O('Weekly hours in 6 months', 'num', '{in:start}+6*' + AVG11), O('Weekly hours in 12 months', 'num', '{in:start}+12*' + AVG11),
  O('Months to the hours marker', 'int', 'IF(%s<=0,"",IF({in:start}>={set:scheduler_hours},0,ROUNDUP(({set:scheduler_hours}-{in:start})/%s,0)))' % (AVG11, AVG11)),
  O('Month the marker is reached', 'date', 'IF(%s<=0,"",EDATE(%s,IF({in:start}>={set:scheduler_hours},0,ROUNDUP(({set:scheduler_hours}-{in:start})/%s,0))))' % (AVG11, MS, AVG11)),
  O('Your net hours per month, last 3 months', 'num', 'IFERROR(AVERAGEIFS({range:growth.net_hours},{range:growth.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:growth.month},"<"&%s),0)' % MS),
  O('Your net hours, same month last year', 'num', 'IFERROR(SUMIFS({range:growth.net_hours},{range:growth.month},DATE(YEAR({today})-1,MONTH({today}),1)),0)'),
  O('Verdict', 'text', 'IF(%s>5,%s,IF(%s<-5,%s,%s))' % (AVG11, vd('Hours growing'), AVG11, vd('Hours shrinking'), vd('Hours flat')))],
  GR('What if', ('Faster: trend 1.5', {'trend': 1.5}), ('Slower: trend 0.5', {'trend': 0.5}), ('Best six months: 160 net hours', {'net6': 160}), ('Slow six months: 24 net hours', {'net6': 24}), ('Start at 950 hours', {'start': 950}))),
 TOOL('churn_hours', 'Churn and Hours Lost', 'Churn and hours lost: rate, revenue and biggest reason',
  'Type clients ended, weekly hours lost, active clients at the start and the months; see churn a month and a year, revenue lost a year and the biggest reason in your data.', [
  I('ended', 'Clients ended', END6), I('lost', 'Weekly hours lost', LOST6, 'num'), I('active', 'Active clients at the start', ACT0), I('months', 'Months in the period', 6), I('rate', 'Average bill rate per hour', AVG_RATE, 'money')], [
  O('Churn rate a month', 'pct', CH12), O('Churn rate a year, at this pace', 'pct', '1-POWER(1-%s,12)' % CH12), O('Churn you accept a month', 'pct', '{set:churn_limit}'), O('Hours lost per client', 'num', '{in:lost}/{in:ended}'),
  O('Revenue lost a year', 'money', '{in:lost}*52*{in:rate}'), O('Biggest reason in your data', 'text', 'IFERROR(INDEX({range:ends.reason},MATCH(MAX({range:ends.same_reason}),{range:ends.same_reason},0)),"")'),
  O('Clients ended for that reason', 'int', 'IFERROR(MAX({range:ends.same_reason}),0)'), O('Average tenure of ended clients, months', 'num', 'IFERROR(AVERAGE({range:ends.tenure_days})/30.4,0)'),
  O('Verdict', 'text', 'IF(%s<={set:churn_limit},%s,%s)' % (CH12, vd('Under the limit'), vd('Above the limit')))],
  GR('What if', ('Half the clients ended: 5', {'ended': 5}), ('A bad quarter: 14 ended', {'ended': 14}), ('Longer period: 12 months', {'months': 12}), ('More active clients: 60', {'active': 60}))),
 TOOL('start_hours', 'Start Hours Growth', 'Client hours at start and after 90 days',
  'Type the average weekly hours at the start, after 90 days and the number of new clients; see the growth share, the hours added and the verdict. Your own starts sit beside it.', [
  I('h0', 'Average weekly hours at start', ST_H0, 'num'), I('h90', 'Average weekly hours after 90 days', ST_H90 + 1.5, 'num'), I('clients', 'New clients', 6), I('rate', 'Average bill rate per hour', AVG_RATE, 'money')], [
  O('Growth share in 90 days', 'pct', '({in:h90}-{in:h0})/{in:h0}'), O('Weekly hours added in the first 90 days', 'num', '({in:h90}-{in:h0})*{in:clients}'), O('Revenue added a year', 'money', '({in:h90}-{in:h0})*{in:clients}*52*{in:rate}'),
  O('Your starts: average growth in hours', 'num', 'IFERROR(AVERAGE({range:starts.growth_hours}),0)'), O('Your starts: share that grew', 'pct', 'IFERROR(COUNTIFS({range:starts.growth_hours},">0")/COUNT({range:starts.growth_hours}),0)'),
  O('Your starts: share that shrank', 'pct', 'IFERROR(COUNTIFS({range:starts.growth_hours},"<0")/COUNT({range:starts.growth_hours}),0)'),
  O('Verdict', 'text', 'IF(({in:h90}-{in:h0})/{in:h0}>0.05,%s,IF(({in:h90}-{in:h0})/{in:h0}<-0.05,%s,%s))' % (vd('Hours grow'), vd('Hours shrink'), vd('Hours hold')))],
  GR('What if', ('Hours grow to 14', {'h90': 14}), ('Hours shrink to 9', {'h90': 9}), ('Twelve new clients', {'clients': 12}), ('Start at 8 hours', {'h0': 8}))),
 TOOL('client_ltv', 'Client Lifetime Value', 'Client lifetime value and payback on the cost to win',
  'Type the margin per week, the weeks you expect the client to stay and the cost to win them; see the value, the payback in weeks and the verdict. The tenure of your ended clients sits beside it.', [
  I('mweek', 'Margin per week', 95, 'money'), I('weeks', 'Weeks the client stays (your guess)', 70), I('cost', 'Cost to win the client', 380, 'money')], [
  O('Lifetime margin', 'money', '{in:mweek}*{in:weeks}'), O('Lifetime margin minus the cost to win', 'money', '{in:mweek}*{in:weeks}-{in:cost}'), O('Payback in weeks', 'num', '{in:cost}/{in:mweek}'),
  O('Margin for every unit spent winning', 'num', '{in:mweek}*{in:weeks}/{in:cost}'), O('Your ended clients: average tenure in weeks', 'num', 'IFERROR(AVERAGE({range:ends.tenure_days})/7,0)'),
  O('Weeks your guess is above or below your own tenure', 'num', '{in:weeks}-IFERROR(AVERAGE({range:ends.tenure_days})/7,0)'), O('Verdict', 'text', 'IF({in:mweek}*{in:weeks}/{in:cost}>=3,%s,%s)' % (vd('Worth winning'), vd('Too costly')))],
  GR('What if', ('Shorter stay: 30 weeks', {'weeks': 30}), ('Longer stay: 120 weeks', {'weeks': 120}), ('Dearer to win: 900', {'cost': 900}), ('Thin margin: 40 a week', {'mweek': 40}))),
 TOOL('service_mix', 'Service Mix Margin', 'Service mix margin: which service to grow and which to fix',
  'Type the weekly hours and the margin share of each service; see the blended margin, the service to grow, the service to fix and the hours in services below the target.', [
  IN('h%d' % (i + 1), '%s: weekly hours' % s, 'num', SV_H.get(s, 0)) for i, s in enumerate(SVS)] + [IN('m%d' % (i + 1), '%s: margin share' % s, 'pct', SV_M.get(s, 0)) for i, s in enumerate(SVS)], [
  O('Blended margin share, weighted by hours', 'pct', '(%s)/(%s)' % ('+'.join('%s*%s' % (h, m) for h, m in zip(H15, M15)), '+'.join(H15))), O('Weekly hours in total', 'num', '+'.join(H15)),
  O('Best margin share', 'pct', MAXM), O('Service to grow', 'text', PICK15(MAXM)), O('Lowest margin share', 'pct', MINM), O('Service to fix', 'text', PICK15(MINM)),
  O('Weekly hours in services below the target', 'num', '+'.join('IF(%s<{set:target_margin},%s,0)' % (m, h) for h, m in zip(H15, M15))),
  O('Points between the best and the lowest', 'num', '100*(%s-%s)' % (MAXM, MINM)),
  O('Verdict', 'text', 'IF((%s)/(%s)>={set:target_margin},%s,%s)' % ('+'.join('%s*%s' % (h, m) for h, m in zip(H15, M15)), '+'.join(H15), vd('On target'), vd('Below target')))],
  GR('What if', ('Homemaking up to 36 percent', {'m3': 0.36}), ('Companion care at 25 percent', {'m1': 0.25}), ('More overnight hours: 200', {'h5': 200}), ('Fewer live-in hours: 100', {'h6': 100}))),
 TOOL('payer_mix', 'Payer Mix Margin', 'Payer mix margin: what payers cost against private pay',
  'Type the hours and the share of the rate card each payer agrees, with the rate and the loaded cost per hour; see the blended margin and the margin given up to payers a year.', [
  IN('p%d' % (i + 1), '%s: weekly hours' % n, 'num', PY_H.get(n, 0)) for i, n in enumerate(PN)] + [IN('s%d' % (i + 1), '%s: share of the rate card' % n, 'pct', [1.0, 0.92, 0.90, 0.88][i]) for i, n in enumerate(PN)] + [
  I('rate', 'Rate card rate per hour', 35.8, 'money'), I('cost', 'Loaded cost per hour', 23.2, 'money')], [
  O('Margin per hour, private pay', 'money', '{in:rate}*{in:s1}-{in:cost}'), O('Margin per hour, care insurer', 'money', '{in:rate}*{in:s2}-{in:cost}'), O('Margin per hour, third-party payer A', 'money', '{in:rate}*{in:s3}-{in:cost}'),
  O('Margin per hour, third-party payer B', 'money', '{in:rate}*{in:s4}-{in:cost}'), O('Blended margin share', 'pct', '(%s-%s)/(%s)' % (REV16, CST16, REV16)),
  O('Margin share, private pay', 'pct', '({in:rate}*{in:s1}-{in:cost})/({in:rate}*{in:s1})'), O('Margin given up to payers a week', 'money', '{in:rate}*(%s)' % '+'.join('%s*(1-%s)' % (h, s) for h, s in zip(HP[1:], SP[1:]))),
  O('Margin given up to payers a year', 'money', '52*{in:rate}*(%s)' % '+'.join('%s*(1-%s)' % (h, s) for h, s in zip(HP[1:], SP[1:]))), O('Share of hours paid by payers', 'pct', '(%s)/(%s)' % ('+'.join(HP[1:]), '+'.join(HP))),
  O('Verdict', 'text', 'IF((%s-%s)/(%s)>={set:target_margin},%s,%s)' % (REV16, CST16, REV16, vd('On target'), vd('Below target')))],
  GR('What if', ('Payer A agrees 95 percent', {'s3': 0.95}), ('Payer B agrees 92 percent', {'s4': 0.92}), ('Care insurer at 88 percent', {'s2': 0.88}), ('Payers double their hours', {'p2': '={in:p2}*2', 'p3': '={in:p3}*2', 'p4': '={in:p4}*2'}), ('Cost 25 an hour', {'cost': 25}))),
 TOOL('sensitivity', 'Margin Sensitivity', 'Margin sensitivity: the same client base at five rate rises',
  'Type the rate, the loaded cost, the weekly hours and the share of hours you would lose; the what-if rows show 0, 3, 5, 8 and 10 percent rises, each with the margin share and the margin per week.', [
  I('rise', 'Rate rise, percent', 0, 'pct'), I('rate', 'Average bill rate per hour', AVG_RATE, 'money'), I('cost', 'Loaded cost per hour', AVG_COST, 'money'), I('hours', 'Weekly hours', 909, 'num'), I('lost', 'Share of hours lost after the rise', 0, 'pct')], [
  O('New rate per hour', 'money', '{in:rate}*(1+{in:rise})'), O('Margin per hour', 'money', '{in:rate}*(1+{in:rise})-{in:cost}'), O('Margin share', 'pct', '({in:rate}*(1+{in:rise})-{in:cost})/({in:rate}*(1+{in:rise}))'),
  O('Weekly hours kept', 'num', '{in:hours}*(1-{in:lost})'), O('Margin per week', 'money', '({in:rate}*(1+{in:rise})-{in:cost})*{in:hours}*(1-{in:lost})'),
  O('Margin per week gained against no rise', 'money', '({in:rate}*(1+{in:rise})-{in:cost})*{in:hours}*(1-{in:lost})-({in:rate}-{in:cost})*{in:hours}'),
  O('Hours you can lose before the gain is gone, share', 'pct', 'IF({in:rise}<=0,0,1-({in:rate}-{in:cost})/({in:rate}*(1+{in:rise})-{in:cost}))'),
  O('Verdict', 'text', 'IF(({in:rate}*(1+{in:rise})-{in:cost})/({in:rate}*(1+{in:rise}))>={set:target_margin},%s,%s)' % (vd('On target'), vd('Below target')))],
  GR('Rate rise', ('No rise', {'rise': 0}), ('Rise 3 percent', {'rise': 0.03}), ('Rise 5 percent', {'rise': 0.05}), ('Rise 8 percent', {'rise': 0.08}), ('Rise 10 percent', {'rise': 0.10}), ('Rise 5 percent, 3 percent of hours lost', {'rise': 0.05, 'lost': 0.03}))),
 TOOL('whatif_grid', 'Rate vs Pay Grid', 'What-if grid: bill rate rise against caregiver pay rise',
  'Type the rate, the pay cost per hour and the other extras, then a rate rise and a pay rise; the grid shows the margin per hour for twelve combinations of the two.', [
  I('rate', 'Bill rate per hour', AVG_RATE, 'money'), I('pay', 'Pay per hour', 17.4, 'money'), I('extras', 'Travel, overtime and mileage per hour', 2.4, 'money'), I('rrise', 'Bill rate rise, percent', 0, 'pct'), I('prise', 'Caregiver pay rise per hour', 0, 'money')], [
  O('New bill rate', 'money', '{in:rate}*(1+{in:rrise})'), O('Loaded cost per hour', 'money', '({in:pay}+{in:prise})*(1+{set:payroll_burden})+{in:extras}'),
  O('Margin per hour', 'money', '{in:rate}*(1+{in:rrise})-(({in:pay}+{in:prise})*(1+{set:payroll_burden})+{in:extras})'),
  O('Margin share', 'pct', '({in:rate}*(1+{in:rrise})-(({in:pay}+{in:prise})*(1+{set:payroll_burden})+{in:extras}))/({in:rate}*(1+{in:rrise}))'),
  O('Bill rate rise that keeps today\'s margin share', 'pct', 'IF({in:prise}<=0,0,{in:prise}*(1+{set:payroll_burden})/(({in:pay})*(1+{set:payroll_burden})+{in:extras}))'),
  O('Verdict', 'text', 'IF(({in:rate}*(1+{in:rrise})-(({in:pay}+{in:prise})*(1+{set:payroll_burden})+{in:extras}))/({in:rate}*(1+{in:rrise}))>={set:target_margin},%s,%s)' % (vd('On target'), vd('Below target')))],
  GR('Rate rise and pay rise', ('Rate 0, pay 0.50', {'rrise': 0, 'prise': 0.5}), ('Rate 0, pay 1.00', {'rrise': 0, 'prise': 1.0}), ('Rate 3%, pay 0.50', {'rrise': 0.03, 'prise': 0.5}), ('Rate 3%, pay 1.00', {'rrise': 0.03, 'prise': 1.0}),
     ('Rate 5%, pay 0.50', {'rrise': 0.05, 'prise': 0.5}), ('Rate 5%, pay 1.00', {'rrise': 0.05, 'prise': 1.0}), ('Rate 5%, pay 1.50', {'rrise': 0.05, 'prise': 1.5}), ('Rate 8%, pay 1.00', {'rrise': 0.08, 'prise': 1.0}),
     ('Rate 8%, pay 1.50', {'rrise': 0.08, 'prise': 1.5}), ('Rate 8%, pay 2.00', {'rrise': 0.08, 'prise': 2.0}), ('Rate 10%, pay 2.00', {'rrise': 0.10, 'prise': 2.0}), ('Rate 10%, pay 3.00', {'rrise': 0.10, 'prise': 3.0}))),
]
assert len(tools) == 18
