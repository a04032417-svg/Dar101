"""Therapy practice suite part 1: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th1_lists import *

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
YES = '{list:yesno.yes}'
def WDN(x):
    return 'IF(%s=%s,1,IF(%s=%s,2,IF(%s=%s,3,IF(%s=%s,4,IF(%s=%s,5,6)))))' % (x, tok('wday', 'Monday'), x, tok('wday', 'Tuesday'), x, tok('wday', 'Wednesday'), x, tok('wday', 'Thursday'), x, tok('wday', 'Friday'))
def NEXTWD(base, wd): return '(%s+MOD(%s-WEEKDAY(%s,2),7))' % (base, WDN(wd), base)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def TV(a, b, cond): return 'IF(%s,%s,%s)' % (cond, a, b)
OVER, WITHIN = ck('Over target'), ck('Within target')

# 1 time to first session
B1 = '({in:enq}+{in:ds}+{in:wait})'; F1 = NEXTWD(B1, '{in:wd}')
B1b = '({in:enq}+{in:ds}+{in:wait}-3)'; F1b = NEXTWD(B1b, '{in:wd}')
# 3 match
M3 = '(({range:match.service}=%s)*({range:match.client_type}=%s)*({range:match.takes_new}=%s))' % ('{in:svc}', '{in:ct}', YES)
KEY3 = 'SUMPRODUCT(MIN(%s*({range:match.preference}*1000+{range:match.no})+(1-%s)*999999))' % (M3, M3)
MIN3 = 'INT(%s/1000)' % KEY3
POS3 = 'MOD(%s,1000)' % KEY3
CL3 = 'INDEX({range:match.clinician},%s)' % POS3
WK3 = '((({range:slots.weekday}={in:wd})+({in:fmt}<>%s))>0)' % tok('fmt', 'In person')
FREE3 = 'SUMPRODUCT(({range:slots.clinician}=%s)*({range:slots.status}<>%s)*%s)' % (CL3, tok('slothold', 'Urgent hold'), WK3)
NXT3 = 'SUMPRODUCT(MIN(({range:slots.clinician}=%s)*({range:slots.status}<>%s)*%s*({range:slots.date})+(1-({range:slots.clinician}=%s)*({range:slots.status}<>%s)*%s)*99999))' % (CL3, tok('slothold', 'Urgent hold'), WK3, CL3, tok('slothold', 'Urgent hold'), WK3)
# 4 funnel
STEPS4 = ['{in:scr}/{in:enq}', '{in:off}/{in:scr}', '{in:book}/{in:off}', '{in:start}/{in:book}']
MIN4 = 'MIN(%s)' % ','.join(STEPS4)
# 7 cleardown
NJ7 = '({in:new}*CHOOSE({in:sc},1,0.8,1.25))'; NET7 = '({in:off}+{in:extra}-%s)' % NJ7; TS7 = '(({in:off}+{in:extra})*{set:target_wait_days}/7)'
# 8 priority
PTS8_U = 'IF({in:urg}=%s,50,IF({in:urg}=%s,20,5))' % (tok('prio', 'High'), tok('prio', 'Normal'))
PTS8_D = 'MIN(30,{in:days}*1.5)'
PTS8_C = 'IF({in:ct}=%s,10,IF({in:ct}=%s,8,IF({in:ct}=%s,4,IF({in:ct}=%s,2,0))))' % (tok('ctype', 'Child'), tok('ctype', 'Young person'), tok('ctype', 'Family'), tok('ctype', 'Couple'))
PTS8_R = 'IF({in:ref}=%s,8,IF({in:ref}=%s,6,IF({in:ref}=%s,5,IF({in:ref}=%s,3,0))))' % (tok('src', 'Doctor referral'), tok('src', 'School referral'), tok('src', 'Other clinician'), tok('src', 'Employer program'))
SC8 = '(%s+%s+%s+%s)' % (PTS8_U, PTS8_D, PTS8_C, PTS8_R)
BAND8 = 'IF(%s>=70,%s,IF(%s>=35,%s,%s))' % (SC8, tok('prio', 'High'), SC8, tok('prio', 'Normal'), tok('prio', 'Low'))
TG8 = 'SUMIFS({range:targets.target_days},{range:targets.client_type},{in:ct},{range:targets.priority},%s)' % BAND8
# 9 deposit
NS9 = '({in:num}*{in:rate})'; KEPT9 = '(%s*{in:dep}*{in:keep})' % NS9
# 11
NS11 = '{in:num}'; REC11 = '({in:num}*{in:fee}*{set:late_fee_pct}*(1-{in:waived}))'
# 12
def CB(n): return 'WORKDAY({in:enq},1+{in:gap}*%d)' % (n - 1)
CLOSE12 = 'WORKDAY({in:enq},1+{in:gap}*{in:att})'
DUE12 = 'OR(%s)' % ','.join('AND({in:att}>=%d,WORKDAY({in:enq},1+{in:gap}*%d)={today})' % (n, n - 1) for n in range(1, 6))
AHEAD12 = '(%s)' % '+'.join('IF(AND({in:att}>=%d,WORKDAY({in:enq},1+{in:gap}*%d)>={today}),1,0)' % (n, n - 1) for n in range(1, 6))
# 15
Y = 'DATE(YEAR({today}),MONTH({today})-3,1)'
L3 = 'SUMIFS({range:funnel.enquiries},{range:funnel.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:funnel.month},"<"&%s)/3' % MS
P3 = 'SUMIFS({range:funnel.enquiries},{range:funnel.month},">="&DATE(YEAR({today}),MONTH({today})-6,1),{range:funnel.month},"<"&DATE(YEAR({today}),MONTH({today})-3,1))/3'
TR15 = 'MAX(0.85,MIN(1.15,(%s)/(%s)))' % (L3, P3)
def FC15(k, s): return 'ROUND((%s)*(1+(%s-1)*%d/3)*{in:%s}*CHOOSE({in:sc},1,1.15,0.85),0)' % (L3, TR15, k, s)
SHARE15 = lambda lab: 'SUMIFS({range:demand.enquiries},{range:demand.service},%s,{range:demand.month},">="&DATE(YEAR({today})-1,MONTH({today}),1))/SUMIFS({range:demand.enquiries},{range:demand.month},">="&DATE(YEAR({today})-1,MONTH({today}),1))' % tok('svc', lab)
# 16
FEE16 = 'SUMIFS({range:services.fee},{range:services.service},{in:svcname})'

tools = [
 TOOL('time_first', 'Time to First Appointment', 'Time to first appointment against the target',
  'Type the enquiry date, days to screening, days waiting after screening and the clinician\'s slot weekday; see the first appointment date, the days from enquiry and whether it is within the target.', [
  I('enq', 'Enquiry date', 'today-3', 'date'), I('ds', 'Days from enquiry to screening call', 2), I('wait', 'Days to wait after screening for a slot', 13), IL('wd', 'Clinician slot weekday', 'wday', 'Thursday')], [
  O('Screening call date', 'date', '{in:enq}+{in:ds}'), O('Earliest date after the wait', 'date', B1), O('First appointment date', 'date', F1), O('Days from enquiry to first appointment', 'int', F1 + '-{in:enq}'),
  O('Target days', 'int', '{set:target_wait_days}'), O('Days over (+) or under (-) the target', 'int', F1 + '-{in:enq}-{set:target_wait_days}'), O('Latest first appointment date that meets the target', 'date', '{in:enq}+{set:target_wait_days}'),
  O('Days to first appointment if the wait were 3 days shorter', 'int', F1b + '-{in:enq}'), O('Verdict', 'text', 'IF(%s-{in:enq}<={set:target_wait_days},%s,%s)' % (F1, WITHIN, OVER))],
  GR('What if', ('Wait 3 days longer', {'wait': 16}), ('Screening call after 5 days', {'ds': 5}), ('Saturday slot', {'wd': '=' + tok('wday', 'Saturday')}), ('Fast track: 1 day, wait 3', {'ds': 1, 'wait': 3}))),
 TOOL('wait_estimate', 'Waitlist Time Estimate', 'Expected weeks to an offer from your place on the waitlist',
  'Type your place on the list, clients finishing each week, clinicians offering the service and a scenario (1 Base, 2 Best, 3 Worst); see the weeks to an offer and the date.', [
  I('place', 'Place on the list for the service', 12), I('fin', 'Clients finishing each week for this service', 2.5, 'num'), I('clin', 'Clinicians offering the service', 3), I('gap', 'New regular slots per clinician per week', 0.4, 'num'),
  I('sc', 'Scenario: 1 Base, 2 Best, 3 Worst', 1)], [
  O('Openings per week', 'num', '({in:fin}+{in:clin}*{in:gap})*CHOOSE({in:sc},1,1.25,0.75)'), O('Expected weeks to an offer', 'num', '{in:place}/(({in:fin}+{in:clin}*{in:gap})*CHOOSE({in:sc},1,1.25,0.75))'),
  O('Expected days to an offer', 'int', 'ROUNDUP(7*{in:place}/(({in:fin}+{in:clin}*{in:gap})*CHOOSE({in:sc},1,1.25,0.75)),0)'), O('Expected offer date', 'date', '{today}+ROUNDUP(7*{in:place}/(({in:fin}+{in:clin}*{in:gap})*CHOOSE({in:sc},1,1.25,0.75)),0)'),
  O('Target days', 'int', '{set:target_wait_days}'), O('Last place that is reached within the target', 'int', 'INT(({in:fin}+{in:clin}*{in:gap})*CHOOSE({in:sc},1,1.25,0.75)*{set:target_wait_days}/7)'),
  O('Average days waited by people still waiting now', 'int', 'IFERROR(AVERAGEIFS({range:waiting.days_waiting},{range:waiting.status},%s),0)' % tok('waitst', 'Waiting'), ),
  O('Verdict', 'text', 'IF(7*{in:place}/(({in:fin}+{in:clin}*{in:gap})*CHOOSE({in:sc},1,1.25,0.75))<={set:target_wait_days},%s,%s)' % (WITHIN, OVER))],
  GR('Place on the list', ('Place 5', {'place': 5}), ('Place 10', {'place': 10}), ('Place 20', {'place': 20}), ('Place 30', {'place': 30}), ('Worst case, place 12', {'sc': 3}))),
 TOOL('match_finder', 'Clinician Match Finder', 'Who can take this new client this week',
  'Choose the service, client type, preferred weekday and format; the match rules and the free slots name the first-choice clinician, their free slots and the next free slot.', [
  IL('svc', 'Service', 'svc', 'Individual session'), IL('ct', 'Client type', 'ctype', 'Adult'), IL('wd', 'Preferred weekday', 'wday', 'Tuesday'), IL('fmt', 'Format', 'fmt', 'In person')], [
  O('First-choice clinician who takes new clients', 'text', 'IF(%s>=99,%s,%s)' % (MIN3, vd('No clinician free'), CL3)), O('Preference rank of that clinician', 'int', 'IF(%s>=99,0,%s)' % (MIN3, MIN3)),
  O('Clinicians who can take this client', 'int', 'SUMPRODUCT(%s)' % M3), O('Free slots in the next 28 days that fit', 'int', 'IF(%s>=99,0,%s)' % (MIN3, FREE3)),
  O('Next free slot that fits', 'date', 'IF(%s>=99,"",IF(%s>=99999,"",%s))' % (MIN3, NXT3, NXT3)),
  O('Verdict', 'text', 'IF(%s>=99,%s,IF(%s>0,%s,%s))' % (MIN3, vd('No clinician free'), FREE3, vd('Match found'), vd('No clinician free')))],
  GR('What if', ('Couples session, couple', {'svc': '=' + tok('svc', 'Couples session'), 'ct': '=' + tok('ctype', 'Couple')}), ('Child session, child', {'svc': '=' + tok('svc', 'Child session'), 'ct': '=' + tok('ctype', 'Child')}),
     ('Online, any weekday', {'fmt': '=' + tok('fmt', 'Online')}), ('Thursday, in person', {'wd': '=' + tok('wday', 'Thursday')}))),
 TOOL('conversion', 'Intake Conversion Funnel', 'Where enquiries are lost, call to first session',
  'Type the numbers at each step for a period; see the step-by-step conversion, the weakest step and how the period compares with your own last 3 months.', [
  I('enq', 'Enquiries', 90), I('scr', 'Screened', 74), I('off', 'Offered a time', 58), I('book', 'Booked', 42), I('start', 'Started', 38)], [
  O('Enquiry to screened, %', 'pct', '{in:scr}/{in:enq}'), O('Screened to offered, %', 'pct', '{in:off}/{in:scr}'), O('Offered to booked, %', 'pct', '{in:book}/{in:off}'), O('Booked to started, %', 'pct', '{in:start}/{in:book}'),
  O('Enquiry to started, %', 'pct', '{in:start}/{in:enq}'), O('Enquiries lost on the way', 'int', '{in:enq}-{in:start}'),
  O('Weakest step', 'text', 'IF(%s={in:scr}/{in:enq},%s,IF(%s={in:off}/{in:scr},%s,IF(%s={in:book}/{in:off},%s,%s)))' % (MIN4, vd('Weakest: screening'), MIN4, vd('Weakest: offering'), MIN4, vd('Weakest: booking'), vd('Weakest: starting'))),
  O('Booked share of enquiries, last 3 months of your funnel', 'pct', 'IFERROR(SUMIFS({range:funnel.booked},{range:funnel.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:funnel.month},"<"&%s)/SUMIFS({range:funnel.enquiries},{range:funnel.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:funnel.month},"<"&%s),0)' % (MS, MS)),
  O('Extra enquiries that would start at target conversion', 'int', 'MAX(0,ROUND({in:enq}*{set:target_conv}-{in:book},0))'),
  O('Verdict against the wanted conversion', 'text', 'IF({in:book}/{in:enq}>={set:target_conv},%s,%s)' % (WITHIN, OVER))],
  GR('What if', ('Screen more enquiries: 70 screened', {'scr': 70}), ('More offers: 60', {'off': 60}), ('Fewer starts: 38', {'start': 38}), ('Busy month: 100 enquiries', {'enq': 100}))),
 TOOL('urgent_reserve', 'Urgent Slot Reserve', 'Slots to hold back each week for urgent first sessions',
  'Type the high priority enquiries a month, the share needing an intake slot, the days to be seen within and a safety buffer; see the slots to hold each week against the diary.', [
  I('high', 'High priority enquiries a month', 14), I('share', 'Share that need an intake slot', 0.7, 'pct'), I('days', 'Days within which they should be seen', 7), I('buf', 'Safety buffer', 0.2, 'pct')], [
  O('High priority intake needs a week', 'num', '{in:high}/4.33*{in:share}'), O('Slots to hold each week', 'int', 'ROUNDUP({in:high}/4.33*{in:share}*MAX(1,{in:days}/7)*(1+{in:buf}),0)'),
  O('Urgent slots held in the diary now, per week', 'num', 'COUNTIFS({range:slots.status},%s)/4' % tok('slothold', 'Urgent hold')), O('Free slots a week in the next 4 weeks', 'num', 'COUNTA({range:slots.slot_id})/4'),
  O('Share of free slots to hold', 'pct', 'ROUNDUP({in:high}/4.33*{in:share}*MAX(1,{in:days}/7)*(1+{in:buf}),0)/(COUNTA({range:slots.slot_id})/4)'),
  O('Verdict', 'text', 'IF(COUNTIFS({range:slots.status},%s)/4>=ROUNDUP({in:high}/4.33*{in:share}*MAX(1,{in:days}/7)*(1+{in:buf}),0),%s,%s)' % (tok('slothold', 'Urgent hold'), vd('Reserve is enough'), vd('Hold more slots')))],
  GR('Days to be seen', ('Within 3 days', {'days': 3}), ('Within 5 days', {'days': 5}), ('Within 10 days', {'days': 10}), ('Within 14 days', {'days': 14}), ('Busy month: 24 enquiries', {'high': 24}))),
 TOOL('dropout_cost', 'Waitlist Drop-out Cost', 'What people who give up waiting cost the practice',
  'Type the people who gave up, the share who would have stayed, sessions per client and the average charge; see the revenue lost, the monthly cost and whether it is above what you accept.', [
  I('people', 'People who gave up waiting in a year', 40), I('stay', 'Share who would have become clients', 0.8, 'pct'), I('sess', 'Sessions per client', 14), I('charge', 'Average charge per session', 105, 'money'),
  I('accept', 'Revenue loss you accept per month', 2000, 'money'), I('cut', 'Drop-outs avoided with shorter waits', 0.25, 'pct')], [
  O('Clients lost', 'num', '{in:people}*{in:stay}'), O('Sessions lost', 'int', '{in:people}*{in:stay}*{in:sess}'), O('Revenue lost in the year', 'money', '{in:people}*{in:stay}*{in:sess}*{in:charge}'),
  O('Revenue lost per month', 'money', '{in:people}*{in:stay}*{in:sess}*{in:charge}/12'), O('Revenue kept if drop-outs fall', 'money', '{in:people}*{in:stay}*{in:sess}*{in:charge}*{in:cut}'),
  O('People who gave up in your waitlist data', 'int', 'COUNTIFS({range:waiting.status},%s)' % tok('waitst', 'Withdrawn')),
  O('Average days they waited before leaving', 'int', 'IFERROR(AVERAGEIFS({range:waiting.days_waiting},{range:waiting.status},%s),0)' % tok('waitst', 'Withdrawn')),
  O('Verdict', 'text', 'IF({in:people}*{in:stay}*{in:sess}*{in:charge}/12>{in:accept},%s,%s)' % (vd('Above what you accept'), vd('Within what you accept')))],
  GR('What if', ('Half the drop-outs: 20', {'people': 20}), ('Longer relationships: 20 sessions', {'sess': 20}), ('Higher charge: 125', {'charge': 125}), ('Bad year: 60 people', {'people': 60}))),
 TOOL('cleardown', 'Waitlist Clear-down Plan', 'Weeks until the waitlist is back to the target',
  'Type the people waiting, offers a week, extra intake slots, new joiners a week and a scenario (1 Base, 2 Best, 3 Worst); see the weeks to target and the extra slots needed to clear it.', [
  I('wait', 'People waiting', 49), I('off', 'Offers made each week now', 8), I('extra', 'Extra intake slots a week', 4), I('new', 'New people joining the list each week', 9), I('want', 'Weeks in which you want it cleared', 6), I('sc', 'Scenario: 1 Base, 2 Best, 3 Worst', 1)], [
  O('Net clearance per week', 'num', NET7), O('List length that is within the target', 'int', 'ROUND(%s,0)' % TS7), O('People above the target', 'int', 'MAX(0,{in:wait}-ROUND(%s,0))' % TS7),
  O('Weeks until back to the target', 'int', 'IF(%s>0,ROUNDUP(MAX(0,{in:wait}-%s)/%s,0),0)' % (NET7, TS7, NET7)), O('Date back to the target', 'date', 'IF(%s>0,{today}+7*ROUNDUP(MAX(0,{in:wait}-%s)/%s,0),"")' % (NET7, TS7, NET7)),
  O('Extra slots a week needed to clear in the weeks you want', 'int', 'MAX(0,ROUNDUP(({in:wait}+{in:want}*%s)/({in:want}+{set:target_wait_days}/7)-{in:off},0))' % NJ7),
  O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (NET7, vd('List is clearing'), vd('List is growing')))],
  GR('What if', ('Two extra slots', {'extra': 2}), ('8 extra slots', {'extra': 8}), ('Worst case joiners', {'sc': 3}), ('Best case joiners', {'sc': 2}), ('Bigger list: 70 waiting', {'wait': 70}))),
 TOOL('priority_scorer', 'Priority Scorer', 'Priority and target days to offer a place',
  'Choose the urgency, client type and referral source and type the days waiting; points give the priority band and the target days to offer, with a decision.', [
  IL('urg', 'Urgency from screening', 'prio', 'Normal'), IL('ct', 'Client type', 'ctype', 'Child'), IL('ref', 'Referral source', 'src', 'Doctor referral'), I('days', 'Days waiting', 12)], [
  O('Urgency points', 'int', PTS8_U), O('Waiting points, capped at 30', 'num', PTS8_D), O('Client type points', 'int', PTS8_C), O('Referral points', 'int', PTS8_R), O('Total score', 'num', SC8),
  O('Priority band', 'text', BAND8), O('Target days to offer', 'int', TG8), O('Days left to the target', 'int', TG8 + '-{in:days}'),
  O('Verdict', 'text', 'IF(%s-{in:days}<=0,%s,%s)' % (TG8, vd('Offer now'), WITHIN))],
  GR('What if', ('High urgency', {'urg': '=' + tok('prio', 'High')}), ('Low urgency, adult', {'urg': '=' + tok('prio', 'Low'), 'ct': '=' + tok('ctype', 'Adult')}), ('Waited 30 days', {'days': 30}), ('Waited 3 days', {'days': 3}))),
 TOOL('deposit_level', 'Deposit Level Solver', 'What deposit covers your intake no-show loss',
  'Type the intake fee, deposit, no-show rate, intakes a month, the share of deposits you keep after a no-show and the cover you want; see the cover now and the deposit needed.', [
  I('fee', 'Intake fee', 150, 'money'), I('dep', 'Deposit now', 50, 'money'), I('rate', 'Intake no-show rate', 0.08, 'pct'), I('num', 'Intakes a month', 60), I('keep', 'Share of deposits kept after a no-show', 0.9, 'pct'), I('goal', 'Cover wanted', 0.5, 'pct')], [
  O('No-shows a month', 'num', NS9), O('Revenue not earned a month', 'money', NS9 + '*{in:fee}'), O('Deposits kept a month', 'money', KEPT9), O('Cover of the loss now', 'pct', KEPT9 + '/(' + NS9 + '*{in:fee})'),
  O('Deposit needed for the cover you want', 'money', 'ROUND({in:goal}*{in:fee}/{in:keep}/5,0)*5'), O('Deposit as a share of the intake fee', 'pct', '{in:dep}/{in:fee}'),
  O('Cash held in deposits at any time', 'money', '{in:num}*{in:dep}*0.5'), O('Verdict', 'text', 'IF(%s/(%s*{in:fee})>={in:goal},%s,%s)' % (KEPT9, NS9, vd('Keep the deposit'), vd('Raise the deposit')))],
  GR('Deposit', ('Deposit 25', {'dep': 25}), ('Deposit 75', {'dep': 75}), ('Deposit 100', {'dep': 100}), ('Deposit 150', {'dep': 150}), ('No-show rate 12%', {'rate': 0.12}))),
 TOOL('workload', 'Screening Call Workload', 'Coordinator hours the screening calls and call-backs need',
  'Type the enquiries a week, minutes per screening call, call-backs per enquiry, minutes per call-back and the hours set aside; see the weekly hours, the cost and whether it fits.', [
  I('enq', 'Enquiries a week', 18), I('mins', 'Minutes per screening call', 20), I('cb', 'Call-backs per enquiry', 1.4, 'num'), I('cbm', 'Minutes per call-back', 6), I('hrs', 'Coordinator hours set aside a week', 8)], [
  O('Screening call hours a week', 'hours', '{in:enq}*{in:mins}/60'), O('Call-back hours a week', 'hours', '{in:enq}*{in:cb}*{in:cbm}/60'), O('Total hours a week', 'hours', '{in:enq}*({in:mins}+{in:cb}*{in:cbm})/60'),
  O('Share of the coordinator\'s weekly hours', 'pct', '{in:enq}*({in:mins}+{in:cb}*{in:cbm})/60/INDEX({range:team.hours_week},7)'),
  O('Cost a week at the coordinator\'s hourly rate', 'money', '{in:enq}*({in:mins}+{in:cb}*{in:cbm})/60*INDEX({range:team.hourly_rate},7)'),
  O('Cost per enquiry', 'money', '({in:mins}+{in:cb}*{in:cbm})/60*INDEX({range:team.hourly_rate},7)'),
  O('Most enquiries a week the hours cover', 'num', '{in:hrs}*60/({in:mins}+{in:cb}*{in:cbm})'), O('Verdict', 'text', 'IF({in:enq}*({in:mins}+{in:cb}*{in:cbm})/60<={in:hrs},%s,%s)' % (WITHIN, OVER))],
  GR('Enquiries a week', ('12 enquiries', {'enq': 12}), ('24 enquiries', {'enq': 24}), ('30 enquiries', {'enq': 30}), ('Shorter calls: 15 minutes', {'mins': 15}), ('More call-backs: 2.5 each', {'cb': 2.5}))),
 TOOL('noshow_cost', 'Intake No-show Cost', 'What intake no-shows cost each month',
  'Type the intake no-shows a month, intake fee, clinician pay, room hours and the share of late fees waived; see the revenue not earned, the costs still paid and the share the deposit covers.', [
  I('num', 'Intake no-shows a month', 5), I('fee', 'Intake fee', 150, 'money'), I('pay', 'Clinician pay per intake', 90, 'money'), I('hrs', 'Room hours per intake', 1.25, 'num'), I('waived', 'Share of late fees waived', 0.33, 'pct'), I('keep', 'Share of deposits kept', 0.9, 'pct')], [
  O('Revenue not earned', 'money', '{in:num}*{in:fee}'), O('Late fees recovered', 'money', REC11), O('Deposits kept', 'money', '{in:num}*{set:deposit}*{in:keep}'),
  O('Net money lost', 'money', '{in:num}*{in:fee}-%s-{in:num}*{set:deposit}*{in:keep}' % REC11), O('Pay, room time and admin still paid for the empty slots', 'money', '{in:num}*({in:pay}+{in:hrs}*{set:room_cost_hour}+{set:admin_cost})'),
  O('Share of the loss covered by deposits', 'pct', '{in:num}*{set:deposit}*{in:keep}/({in:num}*{in:fee}-%s)' % REC11), O('Net money lost in a year', 'money', '12*({in:num}*{in:fee}-%s-{in:num}*{set:deposit}*{in:keep})' % REC11),
  O('Verdict', 'text', 'IF({in:num}*{set:deposit}*{in:keep}>={in:num}*{in:fee}-%s,%s,%s)' % (REC11, vd('Deposit covers the loss'), vd('Deposit covers part')))],
  GR('What if', ('Fewer no-shows: 2', {'num': 2}), ('Waive nothing', {'waived': 0}), ('More no-shows: 9', {'num': 9}), ('Keep every deposit', {'keep': 1}))),
 TOOL('callback_plan', 'Call-back Schedule', 'Call-back dates and the date an enquiry closes',
  'Type the enquiry date, the attempts allowed (up to 5) and the working days between attempts; see each call-back date, the close date and what to do today.', [
  I('enq', 'Enquiry date', 'today-4', 'date'), I('att', 'Attempts allowed (1 to 5)', 3), I('gap', 'Working days between attempts', 2)], [
  O('Call-back 1', 'date', CB(1)), O('Call-back 2', 'date', CB(2)), O('Call-back 3', 'date', CB(3)), O('Call-back 4 if allowed', 'date', CB(4)), O('Call-back 5 if allowed', 'date', CB(5)), O('Close date', 'date', CLOSE12),
  O('Call-backs still ahead', 'int', AHEAD12), O('Days until the enquiry closes', 'int', CLOSE12 + '-{today}'),
  O('Verdict', 'text', 'IF({today}>%s,%s,IF(%s,%s,IF(%s>0,%s,%s)))' % (CLOSE12, ck('Closed'), DUE12, ck('Call today'), AHEAD12, ck('Not due yet'), ck('Call overdue')))],
  GR('What if', ('Enquiry today', {'enq': '={today}'}), ('5 attempts', {'att': 5}), ('Gap of 1 day', {'gap': 1}), ('Enquiry 10 days ago', {'enq': '={today}-10'}))),
 TOOL('booking_date', 'First Session Booking Date', 'First session date, forms deadline and reminder',
  'Type the screening date, the days since the enquiry at screening, the clinician\'s slot weekday and the notice days; see the first session date, the forms deadline and the reminder date.', [
  I('scr', 'Screening date', 'today-2', 'date'), I('since', 'Days from enquiry to screening', 2), IL('wd', 'Clinician slot weekday', 'wday', 'Wednesday'), I('notice', 'Notice days before the first session', 5)], [
  O('Earliest date with notice', 'date', '{in:scr}+{in:notice}'), O('First session date', 'date', NEXTWD('({in:scr}+{in:notice})', '{in:wd}')), O('Days from screening', 'int', NEXTWD('({in:scr}+{in:notice})', '{in:wd}') + '-{in:scr}'),
  O('Days from enquiry', 'int', NEXTWD('({in:scr}+{in:notice})', '{in:wd}') + '-{in:scr}+{in:since}'), O('Intake forms due back by', 'date', NEXTWD('({in:scr}+{in:notice})', '{in:wd}') + '-{set:forms_days}'),
  O('Reminder date (previous working day)', 'date', 'WORKDAY(' + NEXTWD('({in:scr}+{in:notice})', '{in:wd}') + ',-1)'), O('Latest first session date that meets the target', 'date', '{in:scr}-{in:since}+{set:target_wait_days}'),
  O('Verdict', 'text', 'IF(%s-{in:scr}+{in:since}<={set:target_wait_days},%s,%s)' % (NEXTWD('({in:scr}+{in:notice})', '{in:wd}'), WITHIN, OVER))],
  GR('What if', ('Friday slot', {'wd': '=' + tok('wday', 'Friday')}), ('Short notice: 2 days', {'notice': 2}), ('Long notice: 10 days', {'notice': 10}), ('Saturday slot', {'wd': '=' + tok('wday', 'Saturday')}))),
 TOOL('offer_check', 'Offer Acceptance Check', 'How many offers to send to fill the free slots',
  'Type the offers made and accepted, the offers still waiting for an answer and the slots to fill; see the acceptance rate, the offers needed and whether to send more.', [
  I('made', 'Offers answered so far', 40), I('acc', 'Offers accepted', 28), I('open', 'Offers waiting for an answer', 4), I('slots', 'Free slots to fill', 18)], [
  O('Acceptance rate', 'pct', '{in:acc}/{in:made}'), O('Gap to the wanted rate', 'pct', '{in:acc}/{in:made}-{set:target_accept}'), O('Slots the open offers should fill', 'num', '{in:open}*{in:acc}/{in:made}'),
  O('Slots still to fill after the open offers', 'num', 'MAX(0,{in:slots}-{in:open}*{in:acc}/{in:made})'), O('Offers needed from now', 'int', 'ROUNDUP(MAX(0,{in:slots}-{in:open}*{in:acc}/{in:made})/({in:acc}/{in:made}),0)'),
  O('Acceptance rate in your offers, last 90 days', 'pct', 'IFERROR(COUNTIFS({range:offers.answer},%s,{range:offers.offered_on},">="&({today}-90))/COUNTIFS({range:offers.answer},"<>"&%s,{range:offers.offered_on},">="&({today}-90)),0)' % (tok('answer', 'Accepted'), tok('answer', 'Waiting'))),
  O('Verdict', 'text', 'IF(ROUNDUP(MAX(0,{in:slots}-{in:open}*{in:acc}/{in:made})/({in:acc}/{in:made}),0)>0,%s,%s)' % (vd('Offer more'), vd('Enough offers')))],
  GR('What if', ('Lower acceptance: 20 of 40', {'acc': 20}), ('More slots: 30', {'slots': 30}), ('More open offers: 10', {'open': 10}), ('High acceptance: 36 of 40', {'acc': 36}))),
 TOOL('enquiry_forecast', 'Enquiry Forecast', 'Enquiries expected next 3 months, from your own history',
  'Type a seasonal factor for each of the next 3 months and a scenario (1 Base, 2 Best, 3 Worst); your last 3 months and their trend give the forecast, split by service.', [
  I('s1', 'Seasonal factor, next month', 0.85, 'num'), I('s2', 'Seasonal factor, month after', 1.2, 'num'), I('s3', 'Seasonal factor, third month', 1.25, 'num'), I('sc', 'Scenario: 1 Base, 2 Best, 3 Worst', 1)], [
  O('Average enquiries a month, last 3 months', 'int', 'ROUND(%s,0)' % L3), O('Average a month, the 3 months before', 'int', 'ROUND(%s,0)' % P3), O('Trend factor (limited to 0.85 to 1.15)', 'num', TR15),
  O('Enquiries expected next month', 'int', FC15(1, 's1')), O('Enquiries expected the month after', 'int', FC15(2, 's2')), O('Enquiries expected in the third month', 'int', FC15(3, 's3'))] + [
  O('Next month: ' + lab, 'int', 'ROUND((%s)*(%s),0)' % (FC15(1, 's1'), SHARE15(lab))) for lab in SESSION_SERVICES[1:7]] + [
  O('Verdict', 'text', 'IF(%s>1.1*(%s),%s,IF(%s<0.9*(%s),%s,%s))' % (FC15(1, 's1'), L3, vd('Busy month ahead'), FC15(1, 's1'), L3, vd('Quiet month ahead'), vd('Normal month ahead')))],
  GR('Scenario', ('Best case', {'sc': 2}), ('Worst case', {'sc': 3}), ('Quiet December: 0.7', {'s1': 0.7}), ('Strong January: 1.4', {'s2': 1.4}))),
 TOOL('fee_quote', 'New Client Fee Quote', 'Fee per session and first invoice for a new client',
  'Choose the service and fee type, type the sliding scale share, package discount, co-pay (the part the client still pays) and sessions a month; see the fee, deposit and first invoice.', [
  IL('svc', 'Service', 'svc', 'Individual session'), IL('ft', 'Fee type', 'feetype', 'Sliding scale'), I('share', 'Sliding scale share of the fee', 0.7, 'pct'), I('disc', 'Package discount', 0.05, 'pct'), I('copay', 'Co-pay per session', 20, 'money'), I('spm', 'Sessions a month', 4)], [
  O('List fee', 'money', 'SUMIFS({range:services.fee},{range:services.service},{in:svc})'),
  O('Client fee per session', 'money', 'IF({in:ft}=%s,SUMIFS({range:services.fee},{range:services.service},{in:svc}),IF({in:ft}=%s,ROUND(SUMIFS({range:services.fee},{range:services.service},{in:svc})*{in:share},0),IF({in:ft}=%s,ROUND(SUMIFS({range:services.fee},{range:services.service},{in:svc})*(1-{in:disc}),0),{in:copay})))' % (tok('feetype', 'Standard'), tok('feetype', 'Sliding scale'), tok('feetype', 'Package'))),
  O('Deposit to pay when booking', 'money', 'IF(OR({in:ft}=%s,{in:ft}=%s),{set:deposit},0)' % (tok('feetype', 'Standard'), tok('feetype', 'Sliding scale'))),
  O('Client cost in a month', 'money', '{in:spm}*IF({in:ft}=%s,SUMIFS({range:services.fee},{range:services.service},{in:svc}),IF({in:ft}=%s,ROUND(SUMIFS({range:services.fee},{range:services.service},{in:svc})*{in:share},0),IF({in:ft}=%s,ROUND(SUMIFS({range:services.fee},{range:services.service},{in:svc})*(1-{in:disc}),0),{in:copay})))' % (tok('feetype', 'Standard'), tok('feetype', 'Sliding scale'), tok('feetype', 'Package'))),
  O('Intake assessment fee at the same terms', 'money', 'IF({in:ft}=%s,SUMIFS({range:services.fee},{range:services.service},{list:svc.intake_assessment}),IF({in:ft}=%s,ROUND(SUMIFS({range:services.fee},{range:services.service},{list:svc.intake_assessment})*{in:share},0),IF({in:ft}=%s,ROUND(SUMIFS({range:services.fee},{range:services.service},{list:svc.intake_assessment})*(1-{in:disc}),0),{in:copay})))' % (tok('feetype', 'Standard'), tok('feetype', 'Sliding scale'), tok('feetype', 'Package'))),
  O('Verdict', 'text', 'IF(OR({in:ft}=%s,{in:ft}=%s),%s,%s)' % (tok('feetype', 'Standard'), tok('feetype', 'Sliding scale'), vd('Deposit is due'), vd('No deposit needed')))],
  GR('Sliding scale share', ('60% of the fee', {'share': 0.6}), ('80% of the fee', {'share': 0.8}), ('Package, 10% off', {'ft': '=' + tok('feetype', 'Package'), 'disc': 0.1}), ('Standard fee', {'ft': '=' + tok('feetype', 'Standard')}), ('Six sessions a month', {'spm': 6}))),
 TOOL('slot_release', 'Intake Slot Release', 'When to release a held intake slot for regular sessions',
  'Type the intake slots held a week, intakes ready to book, usual last-minute bookings, the days before the slot to release it and the next held slot date; see what to release and when.', [
  I('held', 'Intake slots held a week', 4), I('ready', 'Intakes ready to book now', 2), I('last', 'Usual last-minute intake bookings a week', 1), I('days', 'Days before the slot to release it', 3), I('slot', 'Next held slot date', 'today+6', 'date')], [
  O('Slots to release now', 'int', 'MAX(0,{in:held}-{in:ready}-{in:last})'), O('Slots kept for intakes', 'int', '{in:held}-MAX(0,{in:held}-{in:ready}-{in:last})'), O('Release date for the next held slot', 'date', 'WORKDAY({in:slot},-{in:days})'),
  O('Revenue if released slots are booked as individual sessions', 'money', 'MAX(0,{in:held}-{in:ready}-{in:last})*SUMIFS({range:services.fee},{range:services.service},{list:svc.individual_session})'),
  O('Intake-hold slots in the diary now, per week', 'num', 'COUNTIFS({range:slots.status},%s)/4' % tok('slothold', 'Intake hold')),
  O('Verdict', 'text', 'IF({in:held}-{in:ready}-{in:last}>0,%s,%s)' % (vd('Release slots now'), vd('Keep all held')))],
  GR('What if', ('Hold 6 slots', {'held': 6}), ('No intakes ready', {'ready': 0}), ('Release 5 days ahead', {'days': 5}), ('Busy intake week: 4 ready', {'ready': 4}))),
 TOOL('capacity_case', 'Intake Capacity Case', 'Is it worth opening more intake slots',
  'Type the people waiting, offers a week, new joiners, extra intake slots, intake fee and clinician pay per intake; see the weeks to clear the list, the weekly margin and whether it is worth it.', [
  I('wait', 'People waiting', 49), I('off', 'Offers made each week now', 8), I('new', 'New people joining each week', 9), I('extra', 'Extra intake slots a week', 4), I('fee', 'Intake fee', 150, 'money'), I('pay', 'Clinician pay per intake', 90, 'money')], [
  O('Net clearance a week', 'num', '{in:off}+{in:extra}-{in:new}'), O('Weeks to clear the whole list', 'int', 'IF({in:off}+{in:extra}-{in:new}>0,ROUNDUP({in:wait}/({in:off}+{in:extra}-{in:new}),0),0)'),
  O('Extra revenue a week at the target show rate', 'money', '{in:extra}*{set:target_show_rate}*{in:fee}'), O('Extra cost a week: pay, room time and admin', 'money', '{in:extra}*({in:pay}+1.25*{set:room_cost_hour}+{set:admin_cost})'),
  O('Extra margin a week', 'money', '{in:extra}*({set:target_show_rate}*{in:fee}-{in:pay}-1.25*{set:room_cost_hour}-{set:admin_cost})'),
  O('Extra margin until the list is clear', 'money', 'IF({in:off}+{in:extra}-{in:new}>0,ROUNDUP({in:wait}/({in:off}+{in:extra}-{in:new}),0),0)*{in:extra}*({set:target_show_rate}*{in:fee}-{in:pay}-1.25*{set:room_cost_hour}-{set:admin_cost})'),
  O('Verdict', 'text', 'IF(AND({in:off}+{in:extra}-{in:new}>0,{in:extra}*({set:target_show_rate}*{in:fee}-{in:pay}-1.25*{set:room_cost_hour}-{set:admin_cost})>0),%s,%s)' % (vd('Worth opening'), vd('Not worth opening')))],
  GR('Extra intake slots a week', ('0 extra slots', {'extra': 0}), ('2 extra slots', {'extra': 2}), ('4 extra slots', {'extra': 4}), ('6 extra slots', {'extra': 6}), ('8 extra slots', {'extra': 8}), ('12 extra slots', {'extra': 12}))),
]
assert len(tools) == 18
