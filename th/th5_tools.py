"""Therapy part 5: the 18 decision tools (each gives a verdict, the numbers behind it and a what-if table)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th5_lists import *
import th5_data as D
import th_core as C

def _fx(v): return {k: ('=' + x if isinstance(x, str) and not x.startswith('=') else x) for k, x in v.items()}
def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": _fx(v)} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def DIV(a, b): return 'IF((%s)>0,(%s)/(%s),0)' % (b, a, b)
SCF = 'IF({in:sc}=%s,1.15,IF({in:sc}=%s,0.85,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
EMP = '{set:employer_cost_pct}'
RA = '({in:minutes}/60*{set:room_cost_hour}+{set:admin_cost})'
LM0 = D.LM0
cmP = D.CM_BY[('Priya Raman', LM0)]; cmL = D.CM_BY[('Lucas Moreau', LM0)]
csP = [x for x in D.CFR if x['month'] == LM0 and x['contractor'] == 'Priya Raman'][0]
CARD_SH = round(C.card_share_month(LM0), 2)
SUPH = D.SUP_H[LM0]
INV_P = round(csP['amount_after_fees'] + 83.0, 2)
PAY_OCT = round(sum(x['amount'] + x['employer_cost'] for x in D.PAYR if x['month'] == LM0), 2)
REV_OCT = round(sum(x['revenue'] for x in D.CMR if x['month'] == LM0), 2)

# 1 utilization
CAP1 = '({in:cap}*{in:weeks})'; SH1 = DIV('{in:booked}', CAP1)
# 2 revenue per hour
RPH2 = DIV('{in:revenue}', '{in:hours}'); SPH2 = DIV('{in:sessions}', '{in:hours}'); NEED2 = DIV('{in:target}', SPH2)
# 3 all-in by pay type
AS3 = '({in:salary}*(1+%s)/{in:sessions}+%s)' % (EMP, RA); AP3 = '({in:fee}*{in:split}+%s)' % RA; AE3 = '({in:rate}+%s)' % RA; AH3 = '({in:hourly}*{in:hrs}*(1+%s)+%s)' % (EMP, RA)
def M3(a): return '({in:fee}-%s)' % a
CH3 = 'IF({in:type}=%s,%s,IF({in:type}=%s,%s,IF({in:type}=%s,%s,%s)))' % (tok('paykind', 'Salary'), AS3, tok('paykind', 'Percentage split'), AP3, tok('paykind', 'Per session'), AE3, AH3)
IDX3 = 'IF(%s>=MAX(%s,%s,%s),1,IF(%s>=MAX(%s,%s),2,IF(%s>=%s,3,4)))' % (M3(AS3), M3(AP3), M3(AE3), M3(AH3), M3(AP3), M3(AE3), M3(AH3), M3(AE3), M3(AH3))
# 4 contractor all-in
PAY4 = '({in:fees}*{in:split})'; CF4 = '({in:fees}*{in:card}*{set:card_fee_pct})'; AFT4 = '({in:split}*({in:fees}-%s))' % CF4; ALL4 = '(%s+{in:hours}*{set:room_cost_hour}+{in:booked}*{set:admin_cost})' % AFT4
EFF4 = DIV(AFT4, '{in:fees}')
# 5 split proposal
MG5 = lambda s: '({in:fee}*(1-%s)-%s)' % (s, RA); SESS5 = '({in:weekly}*{in:weeks})'
HI5 = '(1-%s/{in:fee}-{set:profit_target})' % RA
# 6 statement
DUE6 = '(ROUND({in:split}*({in:fees}-{in:card}),2)+{in:adj})'
# 7 associate
REV7 = '({in:sessions}*{in:charge})'; ROOM7 = '({in:sessions}*{in:minutes}/60*{set:room_cost_hour})'; ADM7 = '({in:sessions}*{set:admin_cost})'; SUP7 = '({in:sup_hours}*{in:sup_rate})'
NET7 = '(%s-{in:sessions}*{in:rate}-%s-%s-%s)' % (REV7, ROOM7, ADM7, SUP7)
# 8 salary or split
SES8 = '({in:load}*{in:weeks})'; SAL8 = '({in:salary}*(1+%s)+%s*%s)' % (EMP, SES8, RA); SPL8 = '(%s*({in:fee}*{in:split}+%s))' % (SES8, RA)
BE8 = DIV('{in:salary}*(1+%s)' % EMP, '{in:weeks}*{in:fee}*{in:split}')
# 10 break-even
CON10 = '({in:charge}-{in:var})'; BEM10 = DIV('{in:fixed}', CON10); BEW10 = DIV(BEM10, '{in:weeks}')
# 13 act-first
def NM13(k): return 'IFERROR(INDEX({range:team.name},MATCH(%d,{range:team.act_rank},0)),"")' % k
def SC13(k): return 'IFERROR(ROUNDDOWN(INDEX({range:team.act_score},MATCH(%d,{range:team.act_rank},0)),0),0)' % k
def VD13(k): return 'IF(%s>={in:review_at},%s,IF(%s>={in:watch_at},%s,%s))' % (SC13(k), V('Review now'), SC13(k), V('Watch'), V('Fine'))
# 14 target setter
BK14 = '({in:cap}*{in:weeks}*{in:share}*%s)'
# 15 leave
LEFT15 = '({in:allowed}-{in:taken})'; AFF15 = '({in:wanted}*{in:per_day})'; COV15 = 'MIN(ROUND(%s*{in:accept},0),{in:free})' % AFF15
# 16 admin
TOT16 = '({in:admin}+{in:clinical})'
# 17 pay rise
EXTRA17 = '(({in:new}-{in:old})*{in:units}*(1+{in:emp}))'
# 18 forecast
M1_18 = '({in:booked}*{in:att}*{in:charge}*%s)'

tools = [
 TOOL('util_check', 'Utilization Rate Check', 'Is this clinician idle, healthy or in strain?',
      'Type the weekly session cap, the weeks, the booked and attended sessions; see the Utilization Rate (booked sessions as a share of the session cap), the band and how many sessions to add or move.', [
      I('cap', 'Session cap a week', 25), I('weeks', 'Working weeks in the period', 4), I('booked', 'Booked sessions in the period', 71), I('attended', 'Attended sessions in the period', 68)], [
      O('Capacity in the period (sessions)', 'int', CAP1), O('Utilization Rate (booked share of cap)', 'pct', SH1), O('Attendance rate (attended of booked)', 'pct', DIV('{in:attended}', '{in:booked}')),
      O('Free slots', 'int', 'MAX(0,%s-{in:booked})' % CAP1), O('Booked sessions at the healthy floor', 'int', 'ROUND({set:util_healthy_from}*%s,0)' % CAP1),
      O('Booked sessions at the healthy top', 'int', 'ROUND({set:target_utilisation}*%s,0)' % CAP1), O('Sessions to add to reach the healthy floor', 'int', 'MAX(0,ROUND({set:util_healthy_from}*%s,0)-{in:booked})' % CAP1),
      O('Sessions above the strain line', 'int', 'MAX(0,{in:booked}-ROUNDDOWN({set:util_strain_above}*%s,0))' % CAP1), O('Verdict', 'text', BAND(SH1))],
      GR('What if', ('Idle: 55 booked', {'booked': 55, 'attended': 51}), ('Healthy: 80 booked', {'booked': 80, 'attended': 75}), ('Above healthy: 88 booked', {'booked': 88, 'attended': 83}),
         ('Strain: 96 booked', {'booked': 96, 'attended': 90}), ('Part-time, cap 14, 12 booked', {'cap': 14, 'booked': 12, 'attended': 11}))),
 TOOL('rev_hour', 'Revenue per Clinical Hour', 'Does this clinician earn the revenue per hour we need?',
      'Type the revenue, the clinical hours, the sessions and your target; see revenue per clinical hour, the gap and the charge per session needed to reach the target.', [
      I('revenue', 'Revenue in the period', cmP['revenue'], 'money'), I('hours', 'Clinical hours', cmP['clinical_hours'], 'num'), I('sessions', 'Attended sessions', cmP['attended']), I('target', 'Target revenue per clinical hour', 130, 'money')], [
      O('Revenue per clinical hour', 'money', RPH2), O('Gap to the target per hour', 'money', RPH2 + '-{in:target}'), O('Average charge per session', 'money', DIV('{in:revenue}', '{in:sessions}')),
      O('Sessions per clinical hour', 'num', SPH2), O('Charge per session needed for the target', 'money', NEED2), O('Rise in the average charge needed', 'pct', DIV(NEED2, DIV('{in:revenue}', '{in:sessions}')) + '-1'),
      O('Revenue at the target for the same hours', 'money', '{in:target}*{in:hours}'), O('Revenue short of the target', 'money', 'MAX(0,{in:target}*{in:hours}-{in:revenue})'),
      O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (RPH2, V('Above target'), V('Below target')))],
      GR('What if', ('Target 120', {'target': 120}), ('Revenue up 10 percent', {'revenue': '{in:revenue}*1.1'}), ('Revenue up 20 percent', {'revenue': '{in:revenue}*1.2'}), ('Fewer hours, 50', {'hours': 50}), ('Target 140', {'target': 140}))),
 TOOL('allin_pay', 'All-in Cost by Pay Type', 'Which pay type leaves the best margin on a session?',
      'Type the fee, the sessions a month and the pay terms; see the all-in cost (pay, employer cost, room time and admin) and margin per session of every pay type, ranked.', [
      I('fee', 'Average charge per session', 128, 'money'), I('sessions', 'Sessions a month', 90), I('minutes', 'Session minutes', 50), I('salary', 'Monthly salary', 4800, 'money'), I('split', 'Split of the fee', 0.60, 'pct'),
      I('rate', 'Rate per session (associate)', 45, 'money'), I('hourly', 'Hourly rate (hourly clinician)', 38, 'money'), I('hrs', 'Paid hours per session', 1.2, 'num'), IL('type', 'Pay type to check', 'paykind', 'Percentage split')], [
      O('All-in cost per session: salary', 'money', AS3), O('All-in cost per session: percentage split', 'money', AP3), O('All-in cost per session: per session', 'money', AE3), O('All-in cost per session: hourly', 'money', AH3),
      O('Margin per session: salary', 'money', M3(AS3)), O('Margin per session: percentage split', 'money', M3(AP3)), O('Margin per session: per session', 'money', M3(AE3)), O('Margin per session: hourly', 'money', M3(AH3)),
      O('Pay type with the best margin', 'text', 'CHOOSE(%s,%s,%s,%s,%s)' % (IDX3, tok('paykind', 'Salary'), tok('paykind', 'Percentage split'), tok('paykind', 'Per session'), tok('paykind', 'Hourly'))),
      O('All-in cost per session: pay type to check', 'money', CH3), O('Margin share: pay type to check', 'pct', DIV('{in:fee}-' + CH3, '{in:fee}')),
      O('Rank of the pay type to check by margin', 'int', '1+(%s>%s)+(%s>%s)+(%s>%s)+(%s>%s)' % (M3(AS3), M3(CH3), M3(AP3), M3(CH3), M3(AE3), M3(CH3), M3(AH3), M3(CH3))),
      O('Verdict', 'text', 'IF(%s>={set:profit_target},%s,%s)' % (DIV('{in:fee}-' + CH3, '{in:fee}'), V('Margin on target'), V('Below target')))],
      GR('What if', ('Fewer sessions, 60', {'sessions': 60}), ('More sessions, 120', {'sessions': 120}), ('Average charge 110', {'fee': 110}), ('Split 65 percent', {'split': 0.65}), ('Rate 50 per session', {'rate': 50}))),
 TOOL('contr_allin', 'Contractor All-in Cost', 'Is this contractor split affordable after card fees?',
      'Type the fees charged, the split, the card share of payments, room hours and booked sessions; see the effective split after card fees, the all-in cost and the highest split that holds the target.', [
      I('fees', 'Fees charged in the month', csP['fees_charged'], 'money'), I('split', 'Split of the fee', 0.65, 'pct'), I('card', 'Share of payments made by card', CARD_SH, 'pct'),
      I('hours', 'Room hours used', cmP['clinical_hours'], 'num'), I('booked', 'Booked sessions', cmP['booked'] - cmP['cancelled'])], [
      O('Contractor pay at the split', 'money', PAY4), O('Card fees', 'money', CF4), O('Pay after card fees', 'money', AFT4), O('Effective split after card fees', 'pct', EFF4),
      O('Room time cost', 'money', '{in:hours}*{set:room_cost_hour}'), O('Admin cost', 'money', '{in:booked}*{set:admin_cost}'), O('All-in cost to the practice', 'money', ALL4),
      O('All-in cost share of fees', 'pct', DIV(ALL4, '{in:fees}')), O('Practice margin', 'money', '{in:fees}-' + ALL4),
      O('Highest split that stays in the pay share band', 'pct', '({set:pay_share_target}+{set:target_tolerance})/(1-{in:card}*{set:card_fee_pct})'),
      O('Verdict', 'text', 'IF(%s<={set:pay_share_target}+{set:target_tolerance}+0.00001,%s,%s)' % (EFF4, V('Split affordable'), V('Above the pay share target')))],
      GR('What if', ('Split 60 percent', {'split': 0.60}), ('Split 62 percent', {'split': 0.62}), ('Card share 80 percent', {'card': 0.80}), ('Fees up 10 percent', {'fees': '{in:fees}*1.1'}), ('Split 68 percent', {'split': 0.68}))),
 TOOL('split_prop', 'Contractor Split Proposal', 'Accept this new split or make a counter-offer?',
      'Type the current and proposed split, the sessions a week, the fee and a scenario; see the practice margin per session and per year and the highest split that keeps your profit target.', [
      I('split_now', 'Current split of the fee', 0.65, 'pct'), I('split_new', 'Proposed split of the fee', 0.68, 'pct'), I('weekly', 'Sessions a week', 17), I('weeks', 'Working weeks a year', 46), I('fee', 'Average charge per session', 92, 'money'),
      I('minutes', 'Session minutes', 50), IL('sc', 'Scenario for the volume', 'scen', 'Base')], [
      O('Practice margin per session now', 'money', MG5('{in:split_now}')), O('Practice margin per session at the proposal', 'money', MG5('{in:split_new}')),
      O('Change per session', 'money', MG5('{in:split_new}') + '-' + MG5('{in:split_now}')), O('Sessions a year in the scenario', 'int', SESS5 + '*' + SCF),
      O('Effect on the margin per year, scenario chosen', 'money', '(%s-%s)*%s*%s' % (MG5('{in:split_new}'), MG5('{in:split_now}'), SESS5, SCF)),
      O('Effect per year: Base', 'money', '(%s-%s)*%s' % (MG5('{in:split_new}'), MG5('{in:split_now}'), SESS5)), O('Effect per year: Best', 'money', '(%s-%s)*%s*1.15' % (MG5('{in:split_new}'), MG5('{in:split_now}'), SESS5)),
      O('Effect per year: Worst', 'money', '(%s-%s)*%s*0.85' % (MG5('{in:split_new}'), MG5('{in:split_now}'), SESS5)), O('Margin share at the proposal', 'pct', DIV(MG5('{in:split_new}'), '{in:fee}')),
      O('Highest split that keeps the profit target', 'pct', HI5), O('Verdict', 'text', 'IF({in:split_new}<=%s+0.00001,%s,%s)' % (HI5, V('Accept'), V('Counter-offer')))],
      GR('What if', ('Offer 66 percent', {'split_new': 0.66}), ('Offer 67 percent', {'split_new': 0.67}), ('Offer 70 percent', {'split_new': 0.70}), ('Average charge 100', {'fee': 100}), ('Average charge 110', {'fee': 110}))),
 TOOL('stmt_check', 'Contractor Statement Check', 'Pay this contractor invoice or query it?',
      'Type the fees charged, the split, the card fees, any adjustment and the invoice amount; see the amount due and the difference with the invoice.', [
      I('fees', 'Fees charged in the month', csP['fees_charged'], 'money'), I('split', 'Split of the fee', 0.65, 'pct'), I('card', 'Card fees deducted', csP['card_fees'], 'money'),
      I('adj', 'Other adjustment (plus: owed to contractor)', 0, 'money'), I('invoice', 'Amount on the contractor invoice', INV_P, 'money'), I('tol', 'Difference accepted', 1, 'money')], [
      O('Pay at the split', 'money', 'ROUND({in:fees}*{in:split},2)'), O('Amount due after card fees and adjustment', 'money', DUE6), O('Amount on the invoice', 'money', '{in:invoice}'),
      O('Difference (invoice minus amount due)', 'money', '{in:invoice}-' + DUE6), O('Difference as a share of the amount due', 'pct', DIV('{in:invoice}-' + DUE6, DUE6)),
      O('Verdict', 'text', 'IF(ABS({in:invoice}-%s)<={in:tol},%s,%s)' % (DUE6, V('Pay'), V('Query the invoice')))],
      GR('What if', ('Invoice equals the amount due', {'invoice': DUE6}), ('Invoice 50 higher', {'invoice': DUE6 + '+50'}), ('Adjustment minus 40', {'adj': -40}), ('Split 60 percent', {'split': 0.60}), ('Fees 7,000', {'fees': 7000}))),
 TOOL('assoc_pay', 'Associate Pay Calculator', 'What does the associate cost after supervision?',
      'Type the attended sessions, the rate per session, the supervision hours and the average charge; see the pay, the supervision cost loaded onto the associate and the net margin per session.', [
      I('sessions', 'Attended sessions in the month', cmL['attended']), I('rate', 'Rate per session', 45, 'money'), I('sup_hours', 'Supervision hours in the month', SUPH, 'num'), I('sup_rate', 'Cost of one supervision hour', 60, 'money'),
      I('charge', 'Average charge per session', round(cmL['revenue'] / cmL['attended'], 2), 'money'), I('minutes', 'Session minutes', int(round(cmL['clinical_hours'] * 60 / cmL['attended']))), I('limit', 'Most supervision cost accepted, share of revenue', 0.08, 'pct')], [
      O('Associate pay', 'money', '{in:sessions}*{in:rate}'), O('Supervision cost loaded onto the associate', 'money', SUP7), O('Revenue from the associate sessions', 'money', REV7), O('Room time and admin cost', 'money', ROOM7 + '+' + ADM7),
      O('Net margin after pay, room, admin and supervision', 'money', NET7), O('Net margin per session', 'money', DIV(NET7, '{in:sessions}')), O('Net margin share of revenue', 'pct', DIV(NET7, REV7)),
      O('Supervision cost per session', 'money', DIV(SUP7, '{in:sessions}')), O('Supervision share of revenue', 'pct', DIV(SUP7, REV7)),
      O('Verdict', 'text', 'IF(AND(%s>={set:profit_target},%s<={in:limit}),%s,%s)' % (DIV(NET7, REV7), DIV(SUP7, REV7), V('Net margin on target'), V('Supervision erodes the margin')))],
      GR('What if', ('Supervision 10 hours', {'sup_hours': 10}), ('Supervision costs 90 an hour', {'sup_rate': 90}), ('Rate 48 per session', {'rate': 48}), ('Fewer sessions, 40', {'sessions': 40}), ('Average charge 100', {'charge': 100}))),
 TOOL('sal_split', 'Salary or Split Comparison', 'Is a salary or a split cheaper at this load?',
      'Type the charge, the salary, the split and the sessions a week; see the all-in cost of each pay type and the weekly load at which a salary becomes cheaper than a split.', [
      I('fee', 'Average charge per session', 128, 'money'), I('load', 'Sessions a week', 24), I('weeks', 'Weeks in a month', 4.33, 'num'), I('salary', 'Monthly salary', 4800, 'money'), I('split', 'Split of the fee', 0.60, 'pct'), I('minutes', 'Session minutes', 50)], [
      O('Sessions a month', 'num', SES8), O('All-in cost a month: salary with employer cost', 'money', SAL8), O('All-in cost a month: split', 'money', SPL8), O('Salary minus split (negative: salary is cheaper)', 'money', SAL8 + '-' + SPL8),
      O('All-in cost per session: salary', 'money', DIV(SAL8, SES8)), O('All-in cost per session: split', 'money', DIV(SPL8, SES8)), O('Break-even load, sessions a week', 'num', BE8),
      O('Verdict', 'text', 'IF({in:load}>%s,%s,%s)' % (BE8, V('Salary is cheaper'), V('Split is cheaper')))],
      GR('Five weekly loads', ('12 sessions a week', {'load': 12}), ('16 sessions a week', {'load': 16}), ('20 sessions a week', {'load': 20}), ('24 sessions a week', {'load': 24}), ('28 sessions a week', {'load': 28}))),
 TOOL('pay_share', 'Pay Share of Revenue', 'Is pay within the share of revenue we can afford?',
      'Type the pay with employer costs, the revenue and your target; see the pay share, the gap and the revenue needed at this pay.', [
      I('pay', 'Total pay with employer costs', PAY_OCT, 'money'), I('revenue', 'Revenue in the same month', REV_OCT, 'money'), I('target', 'Target pay share of revenue', 0.55, 'pct'), I('tol', 'Tolerance before the share is over', 0.05, 'pct')], [
      O('Pay share of revenue', 'pct', DIV('{in:pay}', '{in:revenue}')), O('Gap to the target (share points)', 'pct', DIV('{in:pay}', '{in:revenue}') + '-{in:target}'), O('Pay at the target share', 'money', '{in:revenue}*{in:target}'),
      O('Pay above (plus) or below (minus) the target', 'money', '{in:pay}-{in:revenue}*{in:target}'), O('Revenue needed at this pay to reach the target', 'money', DIV('{in:pay}', '{in:target}')),
      O('Verdict', 'text', 'IF(%s<={in:target},%s,IF(%s<={in:target}+{in:tol},%s,%s))' % (DIV('{in:pay}', '{in:revenue}'), V('Within the target'), DIV('{in:pay}', '{in:revenue}'), V('Watch'), V('Over')))],
      GR('What if', ('Revenue down 10 percent', {'revenue': '{in:revenue}*0.9'}), ('Revenue down 20 percent', {'revenue': '{in:revenue}*0.8'}), ('Pay up 5 percent', {'pay': '{in:pay}*1.05'}), ('Pay up 15 percent', {'pay': '{in:pay}*1.15'}), ('Target 50 percent', {'target': 0.50}))),
 TOOL('breakeven', 'Clinician Break-even Sessions', 'How many sessions a week cover this clinician cost?',
      'Type the fixed monthly cost, the cost that comes with each session and the average charge; see the sessions a week that cover the cost and how far the clinician is above it.', [
      I('fixed', 'Fixed cost a month (pay and employer cost)', 5376, 'money'), I('var', 'Room and admin cost per session', 16, 'money'), I('charge', 'Average charge per session', 127, 'money'), I('actual', 'Attended sessions a week now', 24), I('weeks', 'Weeks in a month', 4.33, 'num')], [
      O('Contribution per session', 'money', CON10), O('Break-even sessions a month', 'num', BEM10), O('Break-even sessions a week', 'num', BEW10), O('Attended sessions a month now', 'num', '{in:actual}*{in:weeks}'),
      O('Margin of safety above break-even', 'pct', DIV('{in:actual}-' + BEW10, '{in:actual}')), O('Margin a month at the current load', 'money', '{in:actual}*{in:weeks}*%s-{in:fixed}' % CON10),
      O('Verdict', 'text', 'IF({in:actual}>=%s,%s,%s)' % (BEW10, V('Above break-even'), V('Below break-even')))],
      GR('What if', ('Charge 100', {'charge': 100}), ('Charge 90', {'charge': 90}), ('Fixed cost up 10 percent', {'fixed': '{in:fixed}*1.1'}), ('12 sessions a week', {'actual': 12}), ('8 sessions a week', {'actual': 8}))),
 TOOL('retention_check', 'Retention Check', 'Are more clients staying to 6 sessions than before?',
      'Type the clients started, the clients still attending at 6 sessions and the rate of the last 12 months; see the retention rate, the change and how many more clients to keep to reach the target.', [
      I('started', 'Clients started', 54), I('kept', 'Clients still attending at 6 sessions', 38), I('history', 'Own retention rate, last 12 months', 0.74, 'pct'), I('target', 'Target retention to 6 sessions', 0.70, 'pct')], [
      O('Retention to 6 sessions', 'pct', DIV('{in:kept}', '{in:started}')), O('Change against the last 12 months (points)', 'pct', DIV('{in:kept}', '{in:started}') + '-{in:history}'),
      O('Gap to the target (points)', 'pct', DIV('{in:kept}', '{in:started}') + '-{in:target}'), O('Clients who stopped early', 'int', '{in:started}-{in:kept}'),
      O('Clients to keep to reach the target', 'int', 'MAX(0,ROUNDUP({in:target}*{in:started},0)-{in:kept})'), O('Verdict', 'text', 'IF(%s>={in:history},%s,%s)' % (DIV('{in:kept}', '{in:started}'), V('Improving'), V('Falling')))],
      GR('What if', ('Keep 4 more', {'kept': 42}), ('Keep 8 more', {'kept': 46}), ('Lose 4 more', {'kept': 34}), ('Start 70 clients, keep 50', {'started': 70, 'kept': 50}), ('History 60 percent', {'history': 0.60}))),
 TOOL('rebook_rate', 'Rebooking Rate', 'Are clients rebooking sooner than before?',
      'Type the sessions held, the next sessions booked within 14 days and your rate of the last 12 months; see the rebooking rate, the change and the clients to call.', [
      I('sessions', 'Sessions held', 73), I('rebooked', 'Next sessions booked within 14 days', 58), I('history', 'Own rebooking rate, last 12 months', 0.74, 'pct'), I('target', 'Target rebooked within 14 days', 0.75, 'pct')], [
      O('Rebooking rate', 'pct', DIV('{in:rebooked}', '{in:sessions}')), O('Change against the last 12 months (points)', 'pct', DIV('{in:rebooked}', '{in:sessions}') + '-{in:history}'),
      O('Gap to the target (points)', 'pct', DIV('{in:rebooked}', '{in:sessions}') + '-{in:target}'), O('Clients not yet rebooked', 'int', '{in:sessions}-{in:rebooked}'),
      O('Clients to call to reach the target', 'int', 'MAX(0,ROUNDUP({in:target}*{in:sessions},0)-{in:rebooked})'), O('Verdict', 'text', 'IF(%s>={in:history},%s,%s)' % (DIV('{in:rebooked}', '{in:sessions}'), V('Improving'), V('Falling')))],
      GR('What if', ('Book 5 more', {'rebooked': 63}), ('Book 10 more', {'rebooked': 68}), ('Book 5 fewer', {'rebooked': 53}), ('History 85 percent', {'history': 0.85}), ('Target 80 percent', {'target': 0.80}))),
 TOOL('act_first', 'Act-first Clinician List', 'Which clinician needs a review first?',
      'Reads last month from the Team sheet (utilization band, retention, late notes, pay share, margin) and ranks the six clinicians; type the scores at which a clinician needs a review or a watch.', [
      I('review_at', 'Score from which a clinician needs a review', 5), I('watch_at', 'Score from which a clinician is on watch', 3)], [
      O('First: clinician', 'text', NM13(1)), O('First: score', 'int', SC13(1)), O('First: verdict', 'text', VD13(1)), O('Second: clinician', 'text', NM13(2)), O('Second: score', 'int', SC13(2)), O('Second: verdict', 'text', VD13(2)),
      O('Third: clinician', 'text', NM13(3)), O('Third: score', 'int', SC13(3)), O('Third: verdict', 'text', VD13(3)), O('Fourth: clinician', 'text', NM13(4)), O('Fourth: score', 'int', SC13(4)), O('Fourth: verdict', 'text', VD13(4)),
      O('Fifth: clinician', 'text', NM13(5)), O('Fifth: score', 'int', SC13(5)), O('Fifth: verdict', 'text', VD13(5)), O('Sixth: clinician', 'text', NM13(6)), O('Sixth: score', 'int', SC13(6)), O('Sixth: verdict', 'text', VD13(6)),
      O('Clinicians who need a review now', 'int', 'COUNTIFS({range:team.act_score},">="&{in:review_at})'), O('Verdict for the first clinician', 'text', VD13(1))],
      GR('What if', ('Review from 4', {'review_at': 4}), ('Review from 3', {'review_at': 3}), ('Review from 6', {'review_at': 6}), ('Watch from 2', {'watch_at': 2}), ('Watch from 4', {'watch_at': 4}))),
 TOOL('target_setter', 'Monthly Target Setter', 'What session and revenue target is realistic?',
      'Type the weekly cap, the weeks, the share of the cap you want booked, the attendance rate, the charge and a scenario; see the session and revenue target and whether it fits the cap.', [
      I('cap', 'Session cap a week', 25), I('weeks', 'Working weeks in the month', 4), I('share', 'Share of the cap to book', 0.85, 'pct'), I('att', 'Attendance rate (attended of booked)', 0.93, 'pct'), I('charge', 'Average charge per session', 128, 'money'),
      IL('sc', 'Scenario', 'scen', 'Base')], [
      O('Capacity in the month (sessions)', 'int', '{in:cap}*{in:weeks}'), O('Booked sessions to aim for', 'int', 'ROUND(' + BK14 % SCF + ',0)'), O('Session target (attended)', 'int', 'ROUND(' + BK14 % SCF + '*{in:att},0)'),
      O('Revenue target', 'money', 'ROUND(' + BK14 % SCF + '*{in:att},0)*{in:charge}'), O('Session target a week', 'num', 'ROUND(' + BK14 % SCF + '*{in:att},0)/{in:weeks}'),
      O('Revenue target: Base', 'money', 'ROUND(' + BK14 % '1' + '*{in:att},0)*{in:charge}'), O('Revenue target: Best', 'money', 'ROUND(' + BK14 % '1.15' + '*{in:att},0)*{in:charge}'),
      O('Revenue target: Worst', 'money', 'ROUND(' + BK14 % '0.85' + '*{in:att},0)*{in:charge}'),
      O('Verdict', 'text', 'IF(ROUND(' + BK14 % SCF + ',0)>{in:cap}*{in:weeks},%s,%s)' % (V('Above the cap'), V('Realistic')))],
      GR('What if', ('Book 90 percent of the cap', {'share': 0.90}), ('Book 100 percent of the cap', {'share': 1.0}), ('Book 105 percent of the cap', {'share': 1.05}), ('Attendance 88 percent', {'att': 0.88}), ('Average charge 135', {'charge': 135}))),
 TOOL('leave_plan', 'Leave Planner', 'Does this leave fit, or must sessions move first?',
      'Type the leave days allowed and taken, the days wanted, the sessions a day and the free slots of colleagues; see the days left, the sessions to move and a verdict.', [
      I('allowed', 'Leave days allowed', 20), I('taken', 'Days taken so far', 15), I('wanted', 'Days wanted', 5), I('per_day', 'Sessions a day', 4), I('free', 'Free slots of colleagues in that week', 14), I('accept', 'Share of clients who accept a cover clinician', 0.75, 'pct')], [
      O('Days left now', 'int', LEFT15), O('Days left after this leave', 'int', LEFT15 + '-{in:wanted}'), O('Sessions affected', 'int', AFF15), O('Sessions colleagues can take', 'int', COV15),
      O('Sessions to move or rebook first', 'int', AFF15 + '-' + COV15), O('Verdict', 'text', 'IF(AND({in:wanted}<=%s,%s-%s<=0),%s,%s)' % (LEFT15, AFF15, COV15, V('Leave fits'), V('Move sessions first')))],
      GR('What if', ('Three days', {'wanted': 3}), ('Colleagues have 22 free slots', {'free': 22}), ('All clients accept cover', {'accept': 1.0}), ('Six days wanted', {'wanted': 6}), ('Three sessions a day', {'per_day': 3}))),
 TOOL('admin_share', 'Admin Time Share', 'Is admin taking too much of this clinician\'s time?',
      'Type the admin minutes and the clinical minutes of a month and the admin share you accept; see the share, the hours a week and the hours to cut.', [
      I('admin', 'Admin minutes in the month', 1500), I('clinical', 'Clinical minutes in the month', int(round(cmL['clinical_hours'] * 60))), I('weeks', 'Weeks in a month', 4.33, 'num'), I('accepted', 'Admin share accepted', 0.20, 'pct')], [
      O('Admin share of clinician time', 'pct', DIV('{in:admin}', TOT16)), O('Admin hours a week', 'num', '{in:admin}/60/{in:weeks}'), O('Clinical hours a week', 'num', '{in:clinical}/60/{in:weeks}'),
      O('Admin minutes at the accepted share', 'int', '{in:accepted}/(1-{in:accepted})*{in:clinical}'), O('Admin hours a week to cut', 'num', 'MAX(0,{in:admin}-{in:accepted}/(1-{in:accepted})*{in:clinical})/60/{in:weeks}'),
      O('Verdict', 'text', 'IF(%s>{in:accepted},%s,%s)' % (DIV('{in:admin}', TOT16), V('Admin heavy'), V('Balanced')))],
      GR('What if', ('Admin 900 minutes', {'admin': 900}), ('Admin 600 minutes', {'admin': 600}), ('Admin 2,000 minutes', {'admin': 2000}), ('Clinical time up 20 percent', {'clinical': '{in:clinical}*1.2'}), ('Accept 30 percent', {'accepted': 0.30}))),
 TOOL('pay_rise', 'Pay Rise Cost', 'Can we afford this pay rise?',
      'Type the old and new rate, the sessions or hours a year, the employer cost share, the yearly revenue and the yearly cost; see the yearly cost and the effect on the margin.', [
      I('old', 'Old rate per session or hour', 45, 'money'), I('new', 'New rate per session or hour', 48, 'money'), I('units', 'Sessions or hours a year', 720), I('emp', 'Employer cost share on top', 0.0, 'pct'),
      I('revenue', 'Revenue a year from this person', round(cmL['revenue'] * 12, 0), 'money'), I('cost', 'All-in cost a year now', round((2700 + D.ROOMC[('Lucas Moreau', LM0)] + 6 * (cmL['booked'] - cmL['cancelled']) + SUPH * 60) * 12, 0), 'money')], [
      O('Rise per session or hour', 'pct', DIV('{in:new}-{in:old}', '{in:old}')), O('Extra cost a year', 'money', EXTRA17), O('Margin share now', 'pct', DIV('{in:revenue}-{in:cost}', '{in:revenue}')),
      O('Margin share after the rise', 'pct', DIV('{in:revenue}-{in:cost}-' + EXTRA17, '{in:revenue}')), O('Margin lost (share points)', 'pct', DIV(EXTRA17, '{in:revenue}')),
      O('Extra charge per session or hour to keep the margin', 'money', DIV(EXTRA17, '{in:units}')),
      O('Verdict', 'text', 'IF(%s>={set:profit_target},%s,%s)' % (DIV('{in:revenue}-{in:cost}-' + EXTRA17, '{in:revenue}'), V('Affordable'), V('Pushes margin below target')))],
      GR('What if', ('Rise to 50', {'new': 50}), ('Rise to 55', {'new': 55}), ('Rise to 60', {'new': 60}), ('Rise to 48 with 12 percent employer cost', {'emp': 0.12}), ('Revenue down 10 percent', {'revenue': '{in:revenue}*0.9'}))),
 TOOL('rev_forecast', 'Clinician Revenue Forecast', 'What revenue does this clinician bring in the next 3 months?',
      'Type the sessions booked for the next 4 weeks, the clinician\'s own attendance rate, the average charge, a monthly trend and a scenario; see the revenue for 3 months against your monthly target.', [
      I('booked', 'Sessions booked, next 4 weeks', 107), I('att', 'Own attendance rate (attended of booked)', 0.925, 'pct'), I('charge', 'Average charge per attended session', 127.2, 'money'), I('trend', 'Monthly trend factor, 1 is flat', 1.01, 'num'),
      I('target', 'Monthly revenue target', 12300, 'money'), I('avg3', 'Average revenue of the last 3 months', 12115, 'money'), IL('sc', 'Scenario', 'scen', 'Base')], [
      O('Revenue expected, month 1', 'money', M1_18 % SCF), O('Revenue expected, month 2', 'money', M1_18 % SCF + '*{in:trend}'), O('Revenue expected, month 3', 'money', M1_18 % SCF + '*{in:trend}*{in:trend}'),
      O('Revenue expected, 3 months', 'money', M1_18 % SCF + '*(1+{in:trend}+{in:trend}*{in:trend})'), O('Month 1 against the monthly target', 'money', M1_18 % SCF + '-{in:target}'),
      O('Month 1 against the 3-month average', 'pct', DIV(M1_18 % SCF, '{in:avg3}') + '-1'), O('3-month revenue: Base', 'money', M1_18 % '1' + '*(1+{in:trend}+{in:trend}*{in:trend})'),
      O('3-month revenue: Best', 'money', M1_18 % '1.15' + '*(1+{in:trend}+{in:trend}*{in:trend})'), O('3-month revenue: Worst', 'money', M1_18 % '0.85' + '*(1+{in:trend}+{in:trend}*{in:trend})'),
      O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (M1_18 % SCF, V('On target'), V('Below target')))],
      GR('What if', ('Trend down 2 percent a month', {'trend': 0.98}), ('Trend up 3 percent a month', {'trend': 1.03}), ('Attendance 85 percent', {'att': 0.85}), ('Charge 135', {'charge': 135}), ('Booked 90 sessions', {'booked': 90}))),
]
assert len(tools) == 18, len(tools)
for t_ in tools:
    assert len(t_['sheet']) <= 31, t_['sheet']
