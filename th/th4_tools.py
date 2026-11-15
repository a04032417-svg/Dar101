"""Therapy practice suite part 4: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th4_lists import *

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PMS = 'DATE(YEAR({today}),MONTH({today})-1,1)'
JAN = 'DATE(YEAR({today}),1,1)'
SUBS, RESS, DENS, PAIDS, PARTS, WOS = (tok('clmst', x) for x in ('Submitted', 'Resubmitted', 'Denied', 'Paid', 'Partly paid', 'Written off'))
def SCN(x, a, b, c): return 'IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (x, tok('scen', 'Base'), a, x, tok('scen', 'Best'), b, c)
def OPENV(p): return '(SUMIFS({range:claims.amount},{range:claims.payer},%s,{range:claims.status},%s)+SUMIFS({range:claims.amount},{range:claims.payer},%s,{range:claims.status},%s)+SUMIFS({range:claims.amount},{range:claims.payer},%s,{range:claims.status},%s))' % (p, SUBS, p, RESS, p, DENS)
def OPENN(p): return '(COUNTIFS({range:claims.payer},%s,{range:claims.status},%s)+COUNTIFS({range:claims.payer},%s,{range:claims.status},%s)+COUNTIFS({range:claims.payer},%s,{range:claims.status},%s))' % (p, SUBS, p, RESS, p, DENS)
def FS(p): return 'SUMIFS({range:payers.fee_share},{range:payers.payer},%s)' % p
def CP(p): return 'SUMIFS({range:payers.copay},{range:payers.payer},%s)' % p
def DAYS(p, look): return 'IFERROR(AVERAGEIFS({range:claims.days_to_pay},{range:claims.payer},%s,{range:claims.paid_on},">="&({today}-%s)),30)' % (p, look)
def DENR(p, look): return 'IFERROR(COUNTIFS({range:claims.payer},%s,{range:claims.denied_on},">0",{range:claims.submitted_on},">="&({today}-%s))/COUNTIFS({range:claims.payer},%s,{range:claims.submitted_on},">="&({today}-%s)),0)' % (p, look, p, look)
PT = {x: tok('payer', 'Payer ' + x) for x in 'ABCD'}

# 13 payer mix
def NET13(p): return '({in:fee}*%s-{set:admin_cost}-{set:claim_admin}-({in:fee}*%s-%s)*%s/365*{set:cost_of_waiting}-%s*({in:fee}*%s-%s)*{in:unrec})' % (FS(p), FS(p), CP(p), DAYS(p, '{in:look}'), DENR(p, '{in:look}'), FS(p), CP(p))
def PD13(p): return '(%s/%s)' % (NET13(p), DAYS(p, '{in:look}'))
def SH13(p): return 'COUNTIFS({range:claims.payer},%s,{range:claims.submitted_on},">="&({today}-{in:look}))/COUNTIFS({range:claims.submitted_on},">="&({today}-{in:look}))' % p
# 14 self-pay or payer
PAYK = '({in:fee}*{in:share}-{in:ccost}-({in:fee}*{in:share}-{in:copay})*{in:days}/365*{set:cost_of_waiting}-{in:denial}*({in:fee}*{in:share}-{in:copay})*{in:unrec})'
SELFK = '({in:selffee}*(1-{set:card_fee_pct})-{set:admin_cost})'
# 10 write-off risk
USU10 = 'IFERROR(AVERAGEIFS({range:claims.days_to_pay},{range:claims.payer},{in:payer}),30)'
RISK10 = 'MIN(100,ROUND({in:age}/%s*35+IF({in:st}=%s,30,IF({in:st}=%s,15,0))+IF({in:age}>90,20,0),0))' % (USU10, DENS, RESS)
# 16 cash forecast
DAILY16 = 'SUMIFS({range:monthly.claimed},{range:monthly.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:monthly.month},"<"&%s)/(%s-DATE(YEAR({today}),MONTH({today})-3,1))' % (MS, MS)
AVGD16 = 'IFERROR(AVERAGEIFS({range:claims.days_to_pay},{range:claims.paid_on},">="&({today}-{in:look})),26)'
OPEN16 = lambda d: '(SUMIFS({range:claims.amount},{range:claims.expected_pay},">="&{today},{range:claims.expected_pay},"<="&({today}+%d))+{in:overdue}*SUMIFS({range:claims.amount},{range:claims.expected_pay},"<"&{today}))' % d
CASH16 = lambda d: '(%s)*(%s+%s*MAX(0,%d-%s))' % (SCN('{in:sc}', 1, 1.08, 0.85), OPEN16(d), DAILY16, d, AVGD16)
# 6 clean rate: denial reasons
def DR6(lab): return 'COUNTIFS({range:denials.reason},%s,{range:denials.denied_on},">="&({today}-90))' % tok('denial', lab)
CNT6 = 'COUNTIFS({range:denials.reason},{range:fixes.reason},{range:denials.denied_on},">="&({today}-90))'
TOP6 = 'INDEX({range:fixes.reason},SUMPRODUCT(MATCH(SUMPRODUCT(MAX(%s)),%s,0)))' % (CNT6, CNT6)
# 8 resubmission
SUC8 = 'MIN(1,{in:succ}*%s)' % SCN('{in:sc}', 1, 1.1, 0.75)
CST8 = '({in:mins}/60*{in:rate})'
# 12 approvals
LEFT12 = 'MAX(0,{in:appr}-{in:used})'
RUN12 = '({today}+ROUNDUP(7*%s/{in:perweek},0))' % LEFT12
END12 = 'MIN({in:until},%s)' % RUN12
# 18 write-off forecast
LOSS18 = lambda r: '({in:claims}*%s*{in:wo}*{in:avg})' % r

tools = [
 TOOL('benefits_cover', 'Benefits Coverage Check', 'Will this client\'s benefits cover it?',
  'Choose the payer and type the session limit, sessions used and pre-approval need; see what the client pays per session and whether to book, ask for a pre-approval or offer the self-pay fee.', [
  IL('payer', 'Payer', 'payer', 'Payer B'), I('fee', 'Session list fee', 125, 'money'), I('limit', 'Session limit from the benefits check', 20), I('used', 'Sessions already used', 14),
  I('pre', 'Pre-approval needed (1 yes, 0 no)', 0), I('onfile', 'Pre-approval on file (1 yes, 0 no)', 0), I('plan', 'Sessions you plan to book', 10)], [
  O('Share of the fee the payer allows', 'pct', FS('{in:payer}')), O('Allowed charge per session', 'money', '{in:fee}*' + FS('{in:payer}')), O('Payer pays per session', 'money', '{in:fee}*%s-%s' % (FS('{in:payer}'), CP('{in:payer}'))),
  O('Client co-pay per session', 'money', CP('{in:payer}')), O('Sessions left under the limit', 'int', 'MAX(0,{in:limit}-{in:used})'), O('Sessions of your plan that are covered', 'int', 'MIN({in:plan},MAX(0,{in:limit}-{in:used}))'),
  O('Client cost for the plan, self-pay fee after the limit', 'money', 'MIN({in:plan},MAX(0,{in:limit}-{in:used}))*%s+({in:plan}-MIN({in:plan},MAX(0,{in:limit}-{in:used})))*{in:fee}' % CP('{in:payer}')),
  O('Self-pay fallback fee per session', 'money', '{in:fee}'), O('Denial rate of this payer, last 90 days', 'pct', DENR('{in:payer}', 90)),
  O('Verdict', 'text', 'IF(AND({in:pre}=1,{in:onfile}=0),%s,IF(MAX(0,{in:limit}-{in:used})=0,%s,%s))' % (vd('Get pre-approval first'), vd('Offer the self-pay fee'), vd('Covered')))],
  GR('What if', ('Pre-approval needed, none on file', {'pre': 1}), ('No sessions left under the limit', {'used': 20}), ('Payer C, no co-pay', {'payer': '=' + PT['C']}), ('Payer D, 24 session limit', {'payer': '=' + PT['D'], 'limit': 24}), ('Long plan: 20 sessions', {'plan': 20}))),
 TOOL('selfpay_estimate', 'Self-pay Cost Estimate', 'Self-pay cost estimate with the package saving',
  'Type the list fee, the sliding scale share, expected sessions, the package option and the late-cancel rate; see the total cost to quote, the saving with a package and whether to offer one.', [
  I('fee', 'List fee per session', 125, 'money'), I('slide', 'Sliding scale share (1 is the full fee)', 0.8, 'pct'), I('num', 'Expected sessions', 12), IL('pkg', 'Package option', 'pkopt', '10 sessions'),
  I('late', 'Expected share of sessions ending as a late cancel', 0.08, 'pct'), I('dep', 'Deposit taken off the first invoice', 50, 'money')], [
  O('Fee per session after the sliding scale', 'money', '{in:fee}*{in:slide}'), O('Package discount applied', 'pct', 'IF(AND({in:pkg}=%s,{in:num}>=10),0.1,IF(AND({in:pkg}=%s,{in:num}>=6),0.05,0))' % (tok('pkopt', '10 sessions'), tok('pkopt', '6 sessions'))),
  O('Cost of the sessions', 'money', '{in:fee}*{in:slide}*{in:num}*(1-IF(AND({in:pkg}=%s,{in:num}>=10),0.1,IF(AND({in:pkg}=%s,{in:num}>=6),0.05,0)))' % (tok('pkopt', '10 sessions'), tok('pkopt', '6 sessions'))),
  O('Expected late-cancel fees', 'money', '{in:num}*{in:late}*{in:fee}*{in:slide}*{set:late_fee_pct}'),
  O('Expected total cost to quote', 'money', '{in:fee}*{in:slide}*{in:num}*(1-IF(AND({in:pkg}=%s,{in:num}>=10),0.1,IF(AND({in:pkg}=%s,{in:num}>=6),0.05,0)))+{in:num}*{in:late}*{in:fee}*{in:slide}*{set:late_fee_pct}' % (tok('pkopt', '10 sessions'), tok('pkopt', '6 sessions'))),
  O('Still to pay after the deposit', 'money', '{in:fee}*{in:slide}*{in:num}*(1-IF(AND({in:pkg}=%s,{in:num}>=10),0.1,IF(AND({in:pkg}=%s,{in:num}>=6),0.05,0)))+{in:num}*{in:late}*{in:fee}*{in:slide}*{set:late_fee_pct}-{in:dep}' % (tok('pkopt', '10 sessions'), tok('pkopt', '6 sessions'))),
  O('Saving with the best package against paying per session', 'money', '{in:fee}*{in:slide}*{in:num}*IF({in:num}>=10,0.1,IF({in:num}>=6,0.05,0))'),
  O('Average cost per session, all in', 'money', '({in:fee}*{in:slide}*{in:num}*(1-IF(AND({in:pkg}=%s,{in:num}>=10),0.1,IF(AND({in:pkg}=%s,{in:num}>=6),0.05,0)))+{in:num}*{in:late}*{in:fee}*{in:slide}*{set:late_fee_pct})/{in:num}' % (tok('pkopt', '10 sessions'), tok('pkopt', '6 sessions'))),
  O('Verdict', 'text', 'IF({in:num}>=6,%s,%s)' % (vd('Package saves money'), vd('Pay per session')))],
  GR('Sessions', ('6 sessions', {'num': 6}), ('8 sessions', {'num': 8}), ('10 sessions', {'num': 10}), ('12 sessions', {'num': 12}), ('20 sessions', {'num': 20}), ('Full fee, 12 sessions', {'slide': 1.0}), ('No package', {'pkg': '=' + tok('pkopt', 'No package')}))),
 TOOL('clean_check', 'Claim Clean-check', 'Claim clean-check before you submit',
  'Type the session date, whether client and session details are complete, whether the approval is valid and your rule days; see the submit-by date and whether to submit, fix first or submit now.', [
  I('sdate', 'Session date', 'today-3', 'date'), I('details', 'Client and session details complete (1 yes, 0 no)', 1), I('approval', 'Approval valid (1 yes, 0 no)', 1), I('rule', 'Rule: days after the session to submit', 5)], [
  O('Days since the session', 'int', '{today}-{in:sdate}'), O('Submit by', 'date', '{in:sdate}+{in:rule}'), O('Days left to submit', 'int', '{in:rule}-({today}-{in:sdate})'),
  O('Claims submitted within the rule, last 90 days (your claims)', 'pct', 'IFERROR(COUNTIFS({range:claims.days_to_submit},"<="&{in:rule},{range:claims.submitted_on},">="&({today}-90))/COUNTIFS({range:claims.submitted_on},">="&({today}-90)),0)'),
  O('Average days to submit, last 90 days (your claims)', 'num', 'IFERROR(AVERAGEIFS({range:claims.days_to_submit},{range:claims.submitted_on},">="&({today}-90)),0)'),
  O('Sessions not claimed yet (Unsubmitted Sessions)', 'int', 'COUNTA({range:unsub.session_id})'), O('Items complete, of 2', 'int', '{in:details}+{in:approval}'),
  O('Verdict', 'text', 'IF(OR({in:details}=0,{in:approval}=0),%s,IF({today}-{in:sdate}>{in:rule},%s,%s))' % (vd('Fix first'), vd('Submit now, it is late'), vd('Submit')))],
  GR('What if', ('Details missing', {'details': 0}), ('Approval expired', {'approval': 0}), ('Session 7 days ago', {'sdate': '={today}-7'}), ('Session 12 days ago, details missing', {'sdate': '={today}-12', 'details': 0}), ('Longer rule: 10 days', {'rule': 10, 'sdate': '={today}-7'}))),
 TOOL('chase_first', 'Chase-first Claims', 'Which open claims to chase first',
  'Open claims ranked by amount times days past the payer\'s usual payment time: type how many you can chase today and see the ten claims and their dates.', [
  I('num', 'Claims you can chase today', 5), I('mins', 'Minutes to chase one claim', 12), I('rate', 'Coordinator cost per hour', 24, 'money')], [
  *[O('Chase %d: claim, client, payer, amount, days open' % k, 'text', 'IFERROR(INDEX({range:claims.claim_id},MATCH(%d,{range:claims.chase_rank},0))&" | "&INDEX({range:claims.client},MATCH(%d,{range:claims.chase_rank},0))&" | "&INDEX({range:claims.payer},MATCH(%d,{range:claims.chase_rank},0))&" | "&INDEX({range:claims.amount},MATCH(%d,{range:claims.chase_rank},0))&" | "&INDEX({range:claims.days_open},MATCH(%d,{range:claims.chase_rank},0)),"")' % (k, k, k, k, k)) for k in range(1, 11)],
  O('Expected payment date of the first claim', 'date', 'IFERROR(INDEX({range:claims.expected_pay},MATCH(1,{range:claims.chase_rank},0)),"")'),
  O('Chase date of the first claim (submitted plus chase days)', 'date', 'IFERROR(INDEX({range:claims.submitted_on},MATCH(1,{range:claims.chase_rank},0))+{set:claim_chase_days},"")'),
  O('Claims past the usual payment time', 'int', 'COUNTIFS({range:claims.chase_rank},">=1")'), O('Value past the usual payment time', 'money', 'SUMIFS({range:claims.amount},{range:claims.chase_rank},">=1")'),
  O('Value of the claims you can chase today', 'money', 'SUMIFS({range:claims.amount},{range:claims.chase_rank},"<="&{in:num})'), O('Coordinator cost of chasing them', 'money', '{in:num}*{in:mins}/60*{in:rate}'),
  O('Verdict', 'text', 'IF(COUNTIFS({range:claims.chase_rank},">=1")>0,%s,%s)' % (vd('Chase first'), vd('Wait')))],
  GR('What if', ('Chase 3 claims', {'num': 3}), ('Chase 10 claims', {'num': 10}), ('Slow calls: 25 minutes', {'mins': 25}), ('Temp cover: 18 per hour', {'rate': 18}))),
 TOOL('days_ar', 'Days in AR by Payer', 'Days in A/R by payer and the 90+ tail',
  'Choose a payer; see its open claims, daily claim value and Days in A/R, the value over 90 days now against last month, and a verdict against your maximum days in A/R.', [
  IL('payer', 'Payer', 'payer', 'Payer D'), I('look', 'Look-back days for the daily claim value', 90), I('maxd', 'Most Days in A/R you accept', 40)], [
  O('Open claims, this payer', 'int', OPENN('{in:payer}')), O('Open value, this payer', 'money', OPENV('{in:payer}')),
  O('Daily claim value, this payer', 'money', 'SUMIFS({range:claims.amount},{range:claims.payer},{in:payer},{range:claims.submitted_on},">="&({today}-{in:look}))/{in:look}'),
  O('Days in A/R, this payer', 'num', OPENV('{in:payer}') + '/(SUMIFS({range:claims.amount},{range:claims.payer},{in:payer},{range:claims.submitted_on},">="&({today}-{in:look}))/{in:look})'),
  O('Days in A/R, all payers', 'num', '(%s+%s+%s)/(SUMIFS({range:claims.amount},{range:claims.submitted_on},">="&({today}-{in:look}))/{in:look})' % (
      'SUMIFS({range:claims.amount},{range:claims.status},%s)' % SUBS, 'SUMIFS({range:claims.amount},{range:claims.status},%s)' % RESS, 'SUMIFS({range:claims.amount},{range:claims.status},%s)' % DENS)),
  O('Open value at the last month end, this payer', 'money', 'SUMIFS({range:aging.amount},{range:aging.payer},{in:payer},{range:aging.month},%s)' % PMS),
  O('Value over 90 days now, this payer', 'money', 'SUMIFS({range:aging.amount},{range:aging.payer},{in:payer},{range:aging.month},%s,{range:aging.band},%s)' % (MS, tok('ageband', '90+'))),
  O('Value over 90 days a month ago, this payer', 'money', 'SUMIFS({range:aging.amount},{range:aging.payer},{in:payer},{range:aging.month},%s,{range:aging.band},%s)' % (PMS, tok('ageband', '90+'))),
  O('Days to payment, last 90 days (your claims)', 'num', 'IFERROR(AVERAGEIFS({range:claims.days_to_pay},{range:claims.payer},{in:payer},{range:claims.paid_on},">="&({today}-90)),0)'),
  O('Verdict', 'text', 'IF(AND(SUMIFS({range:aging.amount},{range:aging.payer},{in:payer},{range:aging.month},%s,{range:aging.band},%s)>SUMIFS({range:aging.amount},{range:aging.payer},{in:payer},{range:aging.month},%s,{range:aging.band},%s),SUMIFS({range:aging.amount},{range:aging.payer},{in:payer},{range:aging.month},%s,{range:aging.band},%s)>0),%s,IF(%s/(SUMIFS({range:claims.amount},{range:claims.payer},{in:payer},{range:claims.submitted_on},">="&({today}-{in:look}))/{in:look})>{in:maxd},%s,%s))' % (
      MS, tok('ageband', '90+'), PMS, tok('ageband', '90+'), MS, tok('ageband', '90+'), vd('Old tail growing'), OPENV('{in:payer}'), vd('Slow payer'), vd('Within the limit')))],
  GR('What if', ('Payer A', {'payer': '=' + PT['A']}), ('Payer B', {'payer': '=' + PT['B']}), ('Payer C', {'payer': '=' + PT['C']}), ('Longer look-back: 180 days', {'look': 180}), ('Stricter limit: 30 days', {'maxd': 30}))),
 TOOL('clean_rate', 'Clean Claim Rate Check', 'Clean Claim Rate against the target, with denial reasons',
  'Type the claims submitted and the claims accepted first time; see the Clean Claim Rate against your target, your last two quarters and the denial reasons of the last 90 days ranked.', [
  I('num', 'Claims submitted', 399), I('ok', 'Claims accepted first time', 382), I('target', 'Wanted Clean Claim Rate', 0.9, 'pct')], [
  O('Clean Claim Rate', 'pct', '{in:ok}/{in:num}'), O('Gap to the target, points', 'pct', '{in:ok}/{in:num}-{in:target}'), O('Claims not accepted first time', 'int', '{in:num}-{in:ok}'),
  O('Claims that must be clean to reach the target', 'int', 'ROUNDUP({in:target}*{in:num},0)'),
  O('Clean Claim Rate, last 3 full months', 'pct', 'IFERROR(SUMIFS({range:monthly.clean_claims},{range:monthly.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:monthly.month},"<"&%s)/SUMIFS({range:monthly.claims_submitted},{range:monthly.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:monthly.month},"<"&%s),0)' % (MS, MS)),
  O('Clean Claim Rate, the 3 months before', 'pct', 'IFERROR(SUMIFS({range:monthly.clean_claims},{range:monthly.month},">="&DATE(YEAR({today}),MONTH({today})-6,1),{range:monthly.month},"<"&DATE(YEAR({today}),MONTH({today})-3,1))/SUMIFS({range:monthly.claims_submitted},{range:monthly.month},">="&DATE(YEAR({today}),MONTH({today})-6,1),{range:monthly.month},"<"&DATE(YEAR({today}),MONTH({today})-3,1)),0)')]
  + [O('Denials last 90 days: ' + r, 'int', DR6(r)) for r in DENIAL_REASONS] + [
  O('Most common denial reason, last 90 days', 'text', TOP6), O('Verdict', 'text', 'IF({in:ok}/{in:num}>={in:target},%s,%s)' % (vd('On target'), vd('Below target')))],
  GR('What if', ('Worse quarter: 399 and 340', {'ok': 340}), ('Better quarter: 399 and 392', {'ok': 392}), ('Stricter target: 98%', {'target': 0.98}), ('Busy quarter: 500 and 470', {'num': 500, 'ok': 470}))),
 TOOL('denial_fix', 'Denial Fix Planner', 'Denial fix and resubmit-by date',
  'Choose the denial reason and type the date it was denied and the claim amount; see the usual fix, the resubmit-by date and whether there is still time to fix it.', [
  IL('reason', 'Denial reason', 'denial', 'Needs pre-approval'), I('denied', 'Denied on', 'today-46', 'date'), I('amt', 'Claim amount', 108, 'money')], [
  O('Usual fix', 'text', 'INDEX({range:fixes.usual_fix},MATCH({in:reason},{range:fixes.reason},0))'), O('Usual days to fix', 'int', 'INDEX({range:fixes.days_to_fix},MATCH({in:reason},{range:fixes.reason},0))'),
  O('Days since the denial', 'int', '{today}-{in:denied}'), O('Resubmit by', 'date', '{in:denied}+{set:resubmit_days}'), O('Days left to resubmit', 'int', '{in:denied}+{set:resubmit_days}-{today}'),
  O('Date the fix is done if you start today', 'date', '{today}+INDEX({range:fixes.days_to_fix},MATCH({in:reason},{range:fixes.reason},0))'),
  O('Latest day to start the fix', 'date', '{in:denied}+{set:resubmit_days}-INDEX({range:fixes.days_to_fix},MATCH({in:reason},{range:fixes.reason},0))'),
  O('Denials of this reason, last 12 months (your claims)', 'int', 'COUNTIFS({range:denials.reason},{in:reason},{range:denials.denied_on},">="&({today}-365))'),
  O('Share of them resubmitted', 'pct', 'IFERROR(COUNTIFS({range:denials.reason},{in:reason},{range:denials.denied_on},">="&({today}-365),{range:denials.resubmitted_on},">0")/COUNTIFS({range:denials.reason},{in:reason},{range:denials.denied_on},">="&({today}-365)),0)'),
  O('Amount at stake', 'money', '{in:amt}'),
  O('Verdict', 'text', 'IF({in:denied}+{set:resubmit_days}-{today}>=INDEX({range:fixes.days_to_fix},MATCH({in:reason},{range:fixes.reason},0)),%s,%s)' % (vd('Fix now'), vd('Too late, write off')))],
  GR('What if', ('Denied 80 days ago', {'denied': '={today}-80'}), ('Denied 10 days ago', {'denied': '={today}-10'}), ('Missing details', {'reason': '=' + tok('denial', 'Missing details')}), ('Limit reached, 70 days', {'reason': '=' + tok('denial', 'Limit reached'), 'denied': '={today}-70'}))),
 TOOL('resub_value', 'Resubmission Value', 'Money recovered by resubmitting denied claims',
  'Type the denied claims, their average amount, the fix success rate and a scenario; see the money recovered, the cost of fixing and the smallest claim worth resubmitting.', [
  I('num', 'Denied claims to resubmit', 12), I('amt', 'Average claim amount', 85, 'money'), I('succ', 'Fix success rate', 0.8, 'pct'), IL('sc', 'Scenario', 'scen', 'Base'), I('mins', 'Minutes to fix and resubmit one claim', 20), I('rate', 'Coordinator cost per hour', 24, 'money')], [
  O('Success rate used', 'pct', SUC8), O('Money recovered', 'money', '{in:num}*{in:amt}*' + SUC8), O('Money not recovered', 'money', '{in:num}*{in:amt}*(1-%s)' % SUC8), O('Cost of fixing and resubmitting', 'money', '{in:num}*' + CST8),
  O('Net gain', 'money', '{in:num}*{in:amt}*%s-{in:num}*%s' % (SUC8, CST8)), O('Net gain per claim', 'money', '{in:amt}*%s-%s' % (SUC8, CST8)), O('Smallest claim worth resubmitting', 'money', '%s/%s' % (CST8, SUC8)),
  O('Denied claims waiting now (your claims)', 'int', 'COUNTIFS({range:claims.status},%s)' % DENS), O('Value of denied claims waiting now', 'money', 'SUMIFS({range:claims.amount},{range:claims.status},%s)' % DENS),
  O('Verdict', 'text', 'IF({in:amt}>=%s/%s,%s,%s)' % (CST8, SUC8, vd('Resubmit all'), vd('Skip the small ones')))],
  GR('What if', ('Best case', {'sc': '=' + tok('scen', 'Best')}), ('Worst case', {'sc': '=' + tok('scen', 'Worst')}), ('Small claims: 8 each', {'amt': 8}), ('Slow fixing: 90 minutes', {'mins': 90, 'amt': 12}), ('Many denials: 30 claims', {'num': 30}))),
 TOOL('part_pay', 'Partial Payment Gap', 'Partial payment gap and what to ask the payer',
  'Choose the payer and type the amount claimed and the amount paid; see the short amount and share, how it compares with your own partly paid claims and whether to query the payer.', [
  IL('payer', 'Payer', 'payer', 'Payer B'), I('claimed', 'Amount claimed', 108, 'money'), I('paid', 'Amount paid', 81, 'money')], [
  O('Short amount', 'money', '{in:claimed}-{in:paid}'), O('Short share of the claim', 'pct', '({in:claimed}-{in:paid})/{in:claimed}'), O('Client co-pay this payer applies', 'money', CP('{in:payer}')),
  O('Query a short payment above', 'money', '{set:short_pay_query}'),
  O('Average short share of partly paid claims, last 12 months', 'pct', 'IFERROR(1-SUMIFS({range:claims.paid_amount},{range:claims.status},%s,{range:claims.paid_on},">="&({today}-365))/SUMIFS({range:claims.amount},{range:claims.status},%s,{range:claims.paid_on},">="&({today}-365)),0)' % (PARTS, PARTS)),
  O('Partly paid claims of this payer, last 12 months', 'int', 'COUNTIFS({range:claims.payer},{in:payer},{range:claims.status},%s,{range:claims.paid_on},">="&({today}-365))' % PARTS),
  O('Short-paid amount this year (Monthly Claims Summary)', 'money', 'SUMIFS({range:monthly.short_paid},{range:monthly.month},">="&%s)' % JAN),
  O('Verdict', 'text', 'IF({in:claimed}-{in:paid}>{set:short_pay_query},%s,%s)' % (vd('Query the payer'), vd('Accept')))],
  GR('What if', ('Tiny difference: 5 short', {'paid': 103}), ('Half paid', {'paid': 54}), ('Payer D', {'payer': '=' + PT['D']}), ('Larger claim: 180 claimed, 150 paid', {'claimed': 180, 'paid': 150}))),
 TOOL('wo_risk', 'Write-off Risk', 'Write-off risk of an open claim',
  'Type the claim age, status, payer and amount; a risk score against the payer\'s usual payment time gives the band and whether to chase, escalate or write off.', [
  I('age', 'Days since submission', 75), IL('st', 'Claim status', 'clmst', 'Submitted'), IL('payer', 'Payer', 'payer', 'Payer D'), I('amt', 'Claim amount', 85, 'money')], [
  O('Usual days to payment, this payer', 'int', 'ROUND(%s,0)' % USU10), O('Days past the usual time', 'int', 'MAX(0,{in:age}-ROUND(%s,0))' % USU10), O('Risk score, 0 to 100', 'int', RISK10),
  O('Expected recovery', 'money', '{in:amt}*(1-%s/100)' % RISK10), O('Value at risk', 'money', '{in:amt}*%s/100' % RISK10),
  O('Share of this payer\'s denials written off (your data)', 'pct', 'IFERROR(COUNTIFS({range:writeoffs.payer},{in:payer})/COUNTIFS({range:denials.payer},{in:payer}),0)'),
  O('Open claims of this payer over 90 days', 'int', 'COUNTIFS({range:claims.payer},{in:payer},{range:claims.days_open},">90")'),
  O('Verdict', 'text', 'IF(%s<50,%s,IF(%s<75,%s,%s))' % (RISK10, vd('Chase'), RISK10, vd('Escalate'), vd('Write off')))],
  GR('What if', ('Denied claim, 75 days', {'st': '=' + tok('clmst', 'Denied')}), ('Young claim: 20 days', {'age': 20}), ('Old claim: 120 days', {'age': 120}), ('Payer C, 40 days', {'payer': '=' + PT['C'], 'age': 40}), ('Resubmitted, 60 days', {'st': '=' + tok('clmst', 'Resubmitted'), 'age': 60}))),
 TOOL('remit_match', 'Remittance Match', 'Remittance match: matched, missing and extra',
  'Choose the payer and type the remittance amount, the claims it lists and the amount you matched in Claims Tracker; see the difference, the claims it equals and whether to investigate.', [
  IL('payer', 'Payer', 'payer', 'Payer C'), I('amount', 'Remittance amount', 1562, 'money'), I('num', 'Claims listed on the remittance', 14), I('matched', 'Amount you matched to claims', 1461, 'money')], [
  O('Difference', 'money', '{in:amount}-{in:matched}'), O('Average paid per claim on this remittance', 'money', '{in:amount}/{in:num}'),
  O('Your usual paid per claim, this payer, last 90 days', 'money', 'IFERROR(SUMIFS({range:claims.paid_amount},{range:claims.payer},{in:payer},{range:claims.paid_on},">="&({today}-90))/COUNTIFS({range:claims.payer},{in:payer},{range:claims.paid_on},">="&({today}-90)),0)'),
  O('Extra claims paid that are not matched', 'int', 'IF({in:amount}-{in:matched}>0.005,ROUND(({in:amount}-{in:matched})/IFERROR(SUMIFS({range:claims.paid_amount},{range:claims.payer},{in:payer},{range:claims.paid_on},">="&({today}-90))/COUNTIFS({range:claims.payer},{in:payer},{range:claims.paid_on},">="&({today}-90)),1),0),0)'),
  O('Matched claims missing from the payment', 'int', 'IF({in:matched}-{in:amount}>0.005,ROUND(({in:matched}-{in:amount})/IFERROR(SUMIFS({range:claims.paid_amount},{range:claims.payer},{in:payer},{range:claims.paid_on},">="&({today}-90))/COUNTIFS({range:claims.payer},{in:payer},{range:claims.paid_on},">="&({today}-90)),1),0),0)'),
  O('Remittances not matched in your data', 'int', 'COUNTIFS({range:remits.match_flag},%s)' % ck('Investigate')), O('Largest difference in your data', 'money', 'SUMPRODUCT(MAX(ABS({range:remits.amount}-{range:remits.matched_amount})))'),
  O('Verdict', 'text', 'IF(ABS({in:amount}-{in:matched})<0.005,%s,%s)' % (vd('Matched'), vd('Investigate')))],
  GR('What if', ('Exact match', {'matched': 1562}), ('Payment short by 120', {'matched': 1682}), ('Payer B, 9 claims', {'payer': '=' + PT['B'], 'num': 9, 'amount': 801, 'matched': 801}), ('Small gap: 0.50', {'matched': 1561.5}))),
 TOOL('approval_track', 'Approval Tracker', 'When an approval runs out and when to renew it',
  'Type the sessions approved and used, the valid-until date, sessions a week and the payer\'s days to process; see when sessions run out and the latest day to ask for a renewal.', [
  I('appr', 'Sessions approved', 24), I('used', 'Sessions used', 22), I('until', 'Approval valid until', 'today+60', 'date'), I('perweek', 'Sessions a week', 1, 'num'), I('lead', 'Days the payer needs to process a request', 14)], [
  O('Sessions left', 'int', LEFT12), O('Weeks of sessions left', 'num', LEFT12 + '/{in:perweek}'), O('Date the sessions run out', 'date', RUN12), O('Days until the valid-until date', 'int', '{in:until}-{today}'),
  O('The approval ends first on', 'date', END12), O('Latest day to ask for a new approval', 'date', END12 + '-{in:lead}'), O('Days left to ask', 'int', END12 + '-{in:lead}-{today}'),
  O('Approvals ending within the warning days (your data)', 'int', 'COUNTIFS({range:approvals.days_left},">=0",{range:approvals.days_left},"<="&{set:approval_warn_days})'), O('Clients with 2 sessions or fewer left', 'int', 'COUNTIFS({range:approvals.sessions_left},"<=2",{range:approvals.days_left},">=0")'),
  O('Verdict', 'text', 'IF(%s-{in:lead}-{today}<=7,%s,%s)' % (END12, v2('Renew now'), v2('Approval OK')))],
  GR('What if', ('Plenty left: 8 used', {'used': 8}), ('Two sessions a week', {'perweek': 2}), ('Approval ends in 10 days', {'until': '={today}+10', 'used': 12}), ('Slow payer: 30 days', {'lead': 30}))),
 TOOL('payer_mix', 'Payer Mix Value', 'Which payers to grow, hold or renegotiate',
  'Type the list fee and how long you look back; the net value per session and per day waited is shown for each payer, with a verdict for the payer you choose against your two targets.', [
  I('fee', 'Session list fee', 125, 'money'), I('look', 'Look-back days', 90), I('unrec', 'Share of denied claims never recovered', 0.3, 'pct'), IL('payer', 'Payer to judge', 'payer', 'Payer D'),
  I('hi', 'Net value per day waited to grow a payer', 4.0, 'money'), I('lo', 'Net value per day waited below which you renegotiate', 2.5, 'money')], [
  O('Net value per session, Payer A', 'money', NET13(PT['A'])), O('Net value per session, Payer B', 'money', NET13(PT['B'])), O('Net value per session, Payer C', 'money', NET13(PT['C'])), O('Net value per session, Payer D', 'money', NET13(PT['D'])),
  O('Net value per day waited, Payer A', 'num', PD13(PT['A'])), O('Net value per day waited, Payer B', 'num', PD13(PT['B'])), O('Net value per day waited, Payer C', 'num', PD13(PT['C'])), O('Net value per day waited, Payer D', 'num', PD13(PT['D'])),
  O('Share of claims, Payer A', 'pct', SH13(PT['A'])), O('Share of claims, Payer B', 'pct', SH13(PT['B'])), O('Share of claims, Payer C', 'pct', SH13(PT['C'])), O('Share of claims, Payer D', 'pct', SH13(PT['D'])),
  O('Net value per day waited, payer you judge', 'num', PD13('{in:payer}')), O('Verdict', 'text', 'IF(%s>={in:hi},%s,IF(%s<{in:lo},%s,%s))' % (PD13('{in:payer}'), v2('Grow'), PD13('{in:payer}'), v2('Renegotiate'), v2('Hold')))],
  GR('What if', ('Judge Payer A', {'payer': '=' + PT['A']}), ('Judge Payer B', {'payer': '=' + PT['B']}), ('Judge Payer C', {'payer': '=' + PT['C']}), ('Lower fee: 110', {'fee': 110}), ('Strict targets: 6 and 3', {'hi': 6, 'lo': 3}))),
 TOOL('selfpay_vs_payer', 'Self-pay or Payer', 'Self-pay or payer: what the practice keeps either way',
  'Type the fee, the payer share and co-pay, days to pay, claim cost, denial rate and the fee the client could pay self-pay; see what the practice keeps per session either way and which route to use.', [
  I('fee', 'Session list fee', 125, 'money'), I('share', 'Share of the fee the payer allows', 0.8, 'pct'), I('copay', 'Client co-pay', 15, 'money'), I('days', 'Days the payer takes to pay', 30), I('ccost', 'Admin cost per claim', 10, 'money'),
  I('denial', 'Denial rate of the payer', 0.08, 'pct'), I('unrec', 'Share of denied claims never recovered', 0.3, 'pct'), I('selffee', 'Fee the client can pay self-pay', 90, 'money')], [
  O('Practice keeps per session, bill the payer', 'money', PAYK), O('Practice keeps per session, self-pay', 'money', SELFK), O('Difference per session, payer route', 'money', PAYK + '-' + SELFK),
  O('Difference over 20 sessions', 'money', '20*(%s-%s)' % (PAYK, SELFK)), O('Self-pay fee that matches the payer route', 'money', '(%s+{set:admin_cost})/(1-{set:card_fee_pct})' % PAYK),
  O('Client pays per session, payer route', 'money', '{in:copay}'), O('Cost of waiting for the payer per session', 'money', '({in:fee}*{in:share}-{in:copay})*{in:days}/365*{set:cost_of_waiting}'),
  O('Expected denial loss per session', 'money', '{in:denial}*({in:fee}*{in:share}-{in:copay})*{in:unrec}'), O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (PAYK, SELFK, v2('Bill the payer'), v2('Self-pay')))],
  GR('Denial rate', ('Denial 4%', {'denial': 0.04}), ('Denial 8%', {'denial': 0.08}), ('Denial 12%', {'denial': 0.12}), ('Denial 16%', {'denial': 0.16}), ('Denial 20%', {'denial': 0.20}), ('Client can pay 110', {'selffee': 110}), ('Slow payer: 58 days', {'days': 58}))),
 TOOL('enrol_lead', 'Enrolment Lead Time', 'Payer enrolment lead time for a new clinician',
  'Choose the payer and type the clinician start date, the application date and the usual weeks; see the first billable date, the payer money that cannot be billed meanwhile and the latest day to apply.', [
  IL('payer', 'Payer', 'payer', 'Payer D'), I('start', 'Clinician start date', 'today+28', 'date'), I('sent', 'Application sent on', 'today-10', 'date'), I('usual', 'Usual weeks the payer takes to approve', 15),
  I('sess', 'Payer sessions a week the clinician will see', 6), I('fee', 'Session list fee', 125, 'money')], [
  O('First billable date', 'date', '{in:sent}+7*{in:usual}'), O('Days after the start before billing is possible', 'int', 'MAX(0,{in:sent}+7*{in:usual}-{in:start})'), O('Weeks that cannot be billed', 'num', 'MAX(0,{in:sent}+7*{in:usual}-{in:start})/7'),
  O('Payer sessions that cannot be billed meanwhile', 'int', '{in:sess}*MAX(0,{in:sent}+7*{in:usual}-{in:start})/7'), O('Payer money that cannot be billed meanwhile', 'money', '{in:sess}*MAX(0,{in:sent}+7*{in:usual}-{in:start})/7*({in:fee}*%s-%s)' % (FS('{in:payer}'), CP('{in:payer}'))),
  O('Months of delay', 'num', 'MAX(0,{in:sent}+7*{in:usual}-{in:start})/30.4'), O('Latest application date to bill from the start', 'date', '{in:start}-7*{in:usual}'), O('Days left to apply', 'int', '{in:start}-7*{in:usual}-{today}'),
  O('Your own usual weeks for this payer (Payer Enrolment)', 'num', 'IFERROR(AVERAGEIFS({range:enrol.weeks_wait},{range:enrol.payer},{in:payer},{range:enrol.effective_date},"<>"),0)'),
  O('Verdict', 'text', 'IF({in:sent}<={in:start}-7*{in:usual},%s,%s)' % (v2('On track'), v2('Apply now')))],
  GR('What if', ('Applied 18 weeks ago', {'sent': '={today}-126'}), ('Payer C, 7 weeks', {'payer': '=' + PT['C'], 'usual': 7}), ('Start in 90 days', {'start': '={today}+90'}), ('Part-time: 3 sessions a week', {'sess': 3}))),
 TOOL('claims_cash', 'Claims Cash Forecast', 'Payer money expected in 30 and 60 days against the pay run',
  'Choose a scenario and type the pay run; open claims by their expected payment date plus new claims from your last 3 months give the money expected in 30 and 60 days.', [
  IL('sc', 'Scenario', 'scen', 'Base'), I('look', 'Look-back days for the average days to pay', 90), I('payrun', 'Pay run to cover from payer money', 10416, 'money'), I('overdue', 'Share of overdue open claims that still pay', 0.5, 'pct')], [
  O('Open claims expected to pay within 30 days', 'money', OPEN16(30)), O('Open claims expected to pay within 60 days', 'money', OPEN16(60)), O('Daily claim value, last 3 full months', 'money', DAILY16),
  O('Average days to payment', 'num', AVGD16), O('Expected payer money in 30 days', 'money', CASH16(30)), O('Expected payer money in 60 days', 'money', CASH16(60)), O('Pay run to cover', 'money', '{in:payrun}'),
  O('Surplus (+) or short (-) in 30 days', 'money', CASH16(30) + '-{in:payrun}'), O('Overdue open claims, value', 'money', 'SUMIFS({range:claims.amount},{range:claims.expected_pay},"<"&{today})'), O('Open claims value, not denied', 'money', 'SUMIFS({range:claims.amount},{range:claims.expected_pay},">0")'),
  O('Verdict', 'text', 'IF(%s>={in:payrun},%s,%s)' % (CASH16(30), v2('Covers the pay run'), v2('Short of the pay run')))],
  GR('What if', ('Best case', {'sc': '=' + tok('scen', 'Best')}), ('Worst case', {'sc': '=' + tok('scen', 'Worst')}), ('Overdue claims never pay', {'overdue': 0}), ('Bigger pay run: 12,000', {'payrun': 12000}), ('Smaller pay run: 8,000', {'payrun': 8000}))),
 TOOL('receipt_build', 'Claim Back Receipt Builder', 'Receipt for claim back: total and completeness',
  'Type the sessions, the amount paid per session, the first and last dates and whether the practice and client details are complete; see the receipt total and whether it is ready to issue.', [
  I('num', 'Sessions on the receipt', 2), I('per', 'Amount paid per session', 120, 'money'), I('first', 'First session date', 'today-20', 'date'), I('last', 'Last session date', 'today-6', 'date'),
  I('prov', 'Practice details on the receipt (1 yes, 0 no)', 1), I('cid', 'Client details complete (1 yes, 0 no)', 1), I('paid', 'Paid in full (1 yes, 0 no)', 1)], [
  O('Receipt total', 'money', '{in:num}*{in:per}'), O('Days covered', 'int', '{in:last}-{in:first}+1'), O('Sessions a week on the receipt', 'num', '{in:num}/(({in:last}-{in:first}+1)/7)'),
  O('Typical receipt in your data, last 12 months', 'money', 'IFERROR(AVERAGEIFS({range:receipts.amount_paid},{range:receipts.issued_on},">="&({today}-365)),0)'),
  O('Typical sessions per receipt', 'num', 'IFERROR(AVERAGEIFS({range:receipts.sessions},{range:receipts.issued_on},">="&({today}-365)),0)'),
  O('This receipt against the typical one', 'pct', 'IFERROR({in:num}*{in:per}/AVERAGEIFS({range:receipts.amount_paid},{range:receipts.issued_on},">="&({today}-365))-1,0)'),
  O('Receipts issued, last 30 days', 'int', 'COUNTIFS({range:receipts.issued_on},">="&({today}-30))'), O('Value of receipts issued, last 30 days', 'money', 'SUMIFS({range:receipts.amount_paid},{range:receipts.issued_on},">="&({today}-30))'),
  O('Verdict', 'text', 'IF(AND({in:prov}=1,{in:cid}=1,{in:paid}=1,{in:num}>0,{in:last}>={in:first}),%s,%s)' % (v2('Ready to issue'), v2('Details missing')))],
  GR('What if', ('Client details missing', {'cid': 0}), ('Not paid in full', {'paid': 0}), ('Monthly receipt: 4 sessions', {'num': 4, 'first': '={today}-27'}), ('Dates the wrong way round', {'first': '={today}-3', 'last': '={today}-30'}))),
 TOOL('wo_forecast', 'Write-off Forecast', 'Yearly claim write-off forecast against the loss you accept',
  'Type claims a year, the average written-off claim, the denial rate and the share of denied claims written off; see the yearly loss, the denial rate you can afford and a verdict.', [
  I('claims', 'Claims a year', 1521), I('avg', 'Average amount of a written-off claim', 83, 'money'), I('denial', 'Denial rate', 0.069, 'pct'), I('wo', 'Share of denied claims written off', 0.40, 'pct')], [
  O('Denied claims a year', 'int', '{in:claims}*{in:denial}'), O('Claims written off a year', 'int', '{in:claims}*{in:denial}*{in:wo}'), O('Yearly loss from write-offs', 'money', LOSS18('{in:denial}')),
  O('Loss you accept', 'money', '{set:yearly_loss_accepted}'), O('Room under the loss you accept (+) or over it (-)', 'money', '{set:yearly_loss_accepted}-' + LOSS18('{in:denial}')),
  O('Highest denial rate you can afford', 'pct', '{set:yearly_loss_accepted}/({in:claims}*{in:wo}*{in:avg})'), O('Yearly loss if denials rise by 3 points', 'money', LOSS18('({in:denial}+0.03)')),
  O('Write-off loss, last 12 months (your data)', 'money', 'SUMIFS({range:writeoffs.amount},{range:writeoffs.date},">="&({today}-365))'),
  O('Claims submitted, last 12 months (Monthly Claims Summary)', 'int', 'SUMIFS({range:monthly.claims_submitted},{range:monthly.month},">="&DATE(YEAR({today}),MONTH({today})-11,1))'),
  O('Denial rate, last 12 months (your data)', 'pct', 'IFERROR(COUNTIFS({range:denials.denied_on},">="&({today}-365))/SUMIFS({range:monthly.claims_submitted},{range:monthly.month},">="&DATE(YEAR({today}),MONTH({today})-11,1)),0)'),
  O('Verdict', 'text', 'IF(%s<={set:yearly_loss_accepted},%s,%s)' % (LOSS18('{in:denial}'), v2('Acceptable'), v2('Act on denials')))],
  GR('Denial rate', ('Denial 3%', {'denial': 0.03}), ('Denial 6%', {'denial': 0.06}), ('Denial 9%', {'denial': 0.09}), ('Denial 12%', {'denial': 0.12}), ('Denial 15%', {'denial': 0.15}), ('Half of denied written off', {'wo': 0.5}))),
]
assert len(tools) == 18, len(tools)
