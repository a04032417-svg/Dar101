"""Home care agency suite part 6: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc6_lists import *
import hc6_data as D

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
def IY(k, label, d='yes'): return IN(k, label, 'list', d, list='yesno')
O = OUT
YES = '{list:yesno.yes}'
def R(c): return '{range:%s}' % c
S_ = lambda c: 'SUM(%s)' % R(c)
def LAST12(tb): return '%s,">="&DATE(YEAR({today}),MONTH({today})-11,1),%s,"<="&{today}' % (R(tb + '.month'), R(tb + '.month'))

# own 12-month source totals for the ranking defaults
_rows = [r for r in D.sources_d() if r['month'] >= iso(month_start(11))]
def _tot(s):
    x = [r for r in _rows if r['source'] == key('recsrc', s)]
    return sum(r['applicants'] for r in x), sum(r['starts'] for r in x), sum(r['active_90'] for r in x), int(round(sum(r['cost'] for r in x)))
SRC4 = ['Online job board', 'Agency website', 'Caregiver referral', 'Training school']

# 1 funnel
RT = ['{in:sc}/{in:ap}', '{in:iv}/{in:sc}', '{in:of}/{in:iv}', '{in:st}/{in:of}']
OWN = ['%s/%s' % (S_('funnel.phone_screens'), S_('funnel.applicants')), '%s/%s' % (S_('funnel.interviews'), S_('funnel.phone_screens')), '%s/%s' % (S_('funnel.offers'), S_('funnel.interviews')), '%s/%s' % (S_('funnel.starts'), S_('funnel.offers'))]
Q = ['(%s)/(%s)' % (a, b) for a, b in zip(RT, OWN)]
MINQ = 'MIN(%s)' % ','.join(Q)
WEAK = 'IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s)))' % (Q[0], MINQ, vd('Weakest: phone screen'), Q[1], MINQ, vd('Weakest: interview'), Q[2], MINQ, vd('Weakest: offer'), vd('Weakest: start'))
# 3 sources
def CPA(i): return 'IF({in:ac%d}=0,99999,{in:co%d}/{in:ac%d})' % (i, i, i)
AVG3 = '(({in:co1}+{in:co2}+{in:co3}+{in:co4})/MAX(1,{in:ac1}+{in:ac2}+{in:ac3}+{in:ac4}))'
def RANK(i): return '1+' + '+'.join('(%s<%s)' % (CPA(j), CPA(i)) for j in range(1, 5) if j != i)
def VERD3(i): return 'IF(OR(%s>=1.25*%s,{in:ac%d}<0.5*{in:st%d}),%s,IF(%s<=0.75*%s,%s,%s))' % (CPA(i), AVG3, i, i, vd('Cut'), CPA(i), AVG3, vd('Grow'), vd('Keep'))
IN3 = []; OUT3 = []
for i, s in enumerate(SRC4, 1):
    a, st_, ac, co_ = _tot(s)
    IN3 += [IL('s%d' % i, 'Source %d' % i, 'recsrc', s), I('ap%d' % i, 'Applicants, source %d' % i, a), I('st%d' % i, 'Starts, source %d' % i, st_), I('ac%d' % i, 'Still active after 90 days, source %d' % i, ac), I('co%d' % i, 'Cost, source %d' % i, co_, 'money')]
    OUT3 += [O('Cost per active caregiver, source %d' % i, 'money', 'IF(%s=99999,0,%s)' % (CPA(i), CPA(i))), O('Rank, source %d (1 is best)' % i, 'int', RANK(i)), O('Verdict, source %d' % i, 'text', VERD3(i))]
OUT3.append(O('Best source by cost per active caregiver', 'text', 'IF(%s=1,{in:s1},IF(%s=1,{in:s2},IF(%s=1,{in:s3},{in:s4})))' % (RANK(1), RANK(2), RANK(3))))
# 4 days to start
SUMD = '({in:d1}+{in:d2}+{in:d3}+{in:d4}+{in:d5})'
MAXD = 'MAX({in:d1},{in:d2},{in:d3},{in:d4},{in:d5})'
SLOW = 'IF({in:d1}=%s,%s,IF({in:d2}=%s,%s,IF({in:d3}=%s,%s,IF({in:d4}=%s,%s,%s))))' % (MAXD, tok('kind', 'Phone screen'), MAXD, tok('kind', 'Interview'), MAXD, ck('Offered'), MAXD, tok('step', 'Background check'), tok('step', 'Training'))
# 5 ready
STEPSDONE = '(%s)' % '+'.join('IF({in:%s}=%s,1,0)' % (k, YES) for k in ('idc', 'ref', 'bgc', 'trn', 'agr'))
MISS = '&'.join('IF({in:%s}=%s,"",%s&" ")' % (k, YES, tok('step', n)) for k, n in (('idc', 'Identity check'), ('ref', 'References'), ('bgc', 'Background check'), ('trn', 'Training'), ('agr', 'Agreement signed')))
# 14 hire
PERS = 'COUNTIFS(%s,">="&({today}-56),%s,"<="&{today},%s,">=10")' % (R('hireplan.week'), R('hireplan.week'), R('hireplan.gap_hours'))
CAPH = 'MIN({in:wait},{in:cap})'
MM14 = '(%s*{in:mh}*52/12)' % CAPH
RAMP14 = '({in:wk}*%s*{in:mh}*{in:ramp})' % CAPH
PAY14 = '(({in:cost}+%s)/%s)' % (RAMP14, MM14)
# 17 payback
SC17 = 'IF({in:sc}=%s,1,IF({in:sc}=%s,1.1,0.85))' % (tok('scen', 'Base'), tok('scen', 'Best'))
def MG17(f): return '({in:hrs}*%s*{in:mh}*52/12*%s)' % (f, SC17)

tools = [
 TOOL('funnel_calc', 'Recruiting Funnel Calculator', 'Recruiting funnel and the weakest step',
  'Type the last months of applicants, phone screens, interviews, offers and starts; see the conversion at each step against your own history, the weakest step and the applicants you need.', [
  I('ap', 'Applicants', 62), I('sc', 'Phone screens', 44), I('iv', 'Interviews', 25), I('of', 'Offers', 9), I('st', 'Starts', 6), I('want', 'Starts wanted', 4)], [
  O('Applicants who got a phone screen', 'pct', RT[0]), O('Screens that became interviews', 'pct', RT[1]), O('Interviews that became offers', 'pct', RT[2]), O('Offers that became starts', 'pct', RT[3]),
  O('Applicants per start', 'num', '{in:ap}/{in:st}'), O('Your own applicants per start, all history', 'num', S_('funnel.applicants') + '/' + S_('funnel.starts')),
  O('Applicants needed for the starts wanted', 'int', 'ROUNDUP({in:want}*{in:ap}/{in:st},0)'), O('Weakest step against your own history', 'text', WEAK),
  O('Verdict', 'text', 'IF({in:ap}/{in:st}<=%s/%s,%s,%s)' % (S_('funnel.applicants'), S_('funnel.starts'), vd('Enough applicants'), vd('Need more applicants')))],
  GR('What if', ('More phone screens: 55', {'sc': 55}), ('More interviews: 32', {'iv': 32}), ('Fewer offers: 6', {'of': 6}), ('Wanted starts 8', {'want': 8}))),
 TOOL('cost_hire', 'Cost per Hire', 'Cost per hire with paid training',
  'Type the advert cost, hours of screening and interviewing, the background check and the paid training; see the cost per hire, the paid training share and how it compares with your last 12 months.', [
  I('ad', 'Advert cost', 180, 'money'), I('sh', 'Screening hours', 3, 'num'), I('ih', 'Interview hours', 2.5, 'num'), I('sr', 'Staff cost per hour', 22, 'money'), I('ck', 'Background check', 45, 'money'), I('th', 'Paid training hours', 16, 'num'), I('pr', 'Pay per training hour', 18.5, 'money')], [
  O('Staff time cost', 'money', '({in:sh}+{in:ih})*{in:sr}'), O('Paid training cost with payroll burden', 'money', '{in:th}*{in:pr}*(1+{set:payroll_burden})'),
  O('Cost per hire', 'money', '{in:ad}+{in:ck}+({in:sh}+{in:ih})*{in:sr}+{in:th}*{in:pr}*(1+{set:payroll_burden})'),
  O('Share that is paid training', 'pct', '{in:th}*{in:pr}*(1+{set:payroll_burden})/({in:ad}+{in:ck}+({in:sh}+{in:ih})*{in:sr}+{in:th}*{in:pr}*(1+{set:payroll_burden}))'),
  O('Your own cost per hire, last 12 months', 'money', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (R('hirecost.cost_per_hire'), LAST12('hirecost'))),
  O('Verdict', 'text', 'IF({in:ad}+{in:ck}+({in:sh}+{in:ih})*{in:sr}+{in:th}*{in:pr}*(1+{set:payroll_burden})<=IFERROR(AVERAGEIFS(%s,%s),0),%s,%s)' % (R('hirecost.cost_per_hire'), LAST12('hirecost'), vd('Below your average'), vd('Above your average')))],
  GR('What if', ('No advert (referral)', {'ad': 0}), ('Training 24 hours', {'th': 24}), ('Interviews take 4 hours', {'ih': 4}), ('Check costs 60', {'ck': 60}))),
 TOOL('source_rank', 'Source Ranking', 'Source ranking by caregivers still active after 90 days',
  'Type applicants, starts, caregivers still active after 90 days and the cost of up to four sources (your last 12 months are filled in); see cost per active caregiver, the rank and Grow, Keep or Cut.', IN3, OUT3,
  GR('What if', ('Source 1 cost 20% lower', {'co1': '=ROUND({in:co1}*0.8,0)'}), ('Source 2 gets 3 more active', {'ac2': '={in:ac2}+3'}), ('Source 3 loses 2 active', {'ac3': '=MAX(0,{in:ac3}-2)'}), ('Source 4 cost doubles', {'co4': '={in:co4}*2'}))),
 TOOL('days_start', 'Days to Start', 'Days from applying to the first day and the slowest step',
  'Type the day someone applied and the days each step takes; see the date of each step, the start date, the total days against your target and the slowest step.', [
  I('ad', 'Applied on', 'today-3', 'date'), I('d1', 'Days to the phone screen', 2), I('d2', 'Days from screen to interview', 6), I('d3', 'Days from interview to offer', 3), I('d4', 'Days for checks and references', 8), I('d5', 'Days for training and agreement', 5)], [
  O('Phone screen date', 'date', '{in:ad}+{in:d1}'), O('Interview date', 'date', '{in:ad}+{in:d1}+{in:d2}'), O('Offer date', 'date', '{in:ad}+{in:d1}+{in:d2}+{in:d3}'), O('Checks done date', 'date', '{in:ad}+{in:d1}+{in:d2}+{in:d3}+{in:d4}'),
  O('Start date', 'date', '{in:ad}+' + SUMD), O('Total days', 'int', SUMD), O('Target days', 'int', '{set:days_to_start_target}'), O('Days over (+) or under (-) the target', 'int', SUMD + '-{set:days_to_start_target}'),
  O('Slowest step', 'text', SLOW), O('Your own average days to start', 'num', 'IFERROR(AVERAGE(%s),0)' % R('applicants.days_to_start')),
  O('Verdict', 'text', 'IF(%s<={set:days_to_start_target},%s,%s)' % (SUMD, ck('Within target'), ck('Over target')))],
  GR('What if', ('Checks in 5 days', {'d4': 5}), ('Interview in 3 days', {'d2': 3}), ('Training in 2 days', {'d5': 2}), ('Slow: checks 14 days', {'d4': 14}))),
 TOOL('ready_first', 'Ready for First Shift', 'Ready for first shift: Ready or Blocked',
  'Answer yes or no for each of the five checks; see how many steps are done, what is missing and the verdict the schedule reads. A one-person agency can use it for its first hire.', [
  IY('idc', 'Identity check done'), IY('ref', 'References done'), IY('bgc', 'Background check done', 'no'), IY('trn', 'Training done'), IY('agr', 'Agreement signed')], [
  O('Steps done', 'int', STEPSDONE), O('Steps missing', 'int', '5-' + STEPSDONE), O('Missing steps', 'text', 'IF(%s=5,%s,%s)' % (STEPSDONE, ck('Ready'), MISS)),
  O('Verdict', 'text', 'IF(%s=5,%s,%s)' % (STEPSDONE, ck('Ready'), ck('Blocked'))), O('People blocked now in the Onboarding page', 'int', 'COUNTIFS(%s,%s)' % (R('onboarding.ready_check'), ck('Blocked')))]),
 TOOL('onboard_dates', 'Onboarding Due Dates', 'Onboarding due dates from the start date',
  'Type the start date and how many days before it each step is due; see the due date of every step and the first possible shift.', [
  I('sd', 'Start date', 'today+9', 'date'), I('l1', 'Identity check, days before start', 12), I('l2', 'References, days before start', 8), I('l3', 'Background check, days before start', 7), I('l4', 'Agreement, days before start', 3), I('l5', 'Training, days before start', 2), I('l6', 'First shift, days after start', 5)], [
  O('Identity check due', 'date', '{in:sd}-{in:l1}'), O('References due', 'date', '{in:sd}-{in:l2}'), O('Background check due', 'date', '{in:sd}-{in:l3}'), O('Agreement due', 'date', '{in:sd}-{in:l4}'), O('Training due', 'date', '{in:sd}-{in:l5}'),
  O('First shift due', 'date', '{in:sd}+{in:l6}'), O('First possible shift', 'date', 'MAX({in:sd},{in:sd}-MIN({in:l1},{in:l2},{in:l3},{in:l4},{in:l5})+1)'),
  O('Days from today to the first check due', 'int', '{in:sd}-MAX({in:l1},{in:l2},{in:l3})-{today}'),
  O('Verdict', 'text', 'IF({in:sd}-MAX({in:l1},{in:l2},{in:l3})>={today},%s,%s)' % (ck('Within target'), ck('Over target')))],
  GR('What if', ('Start in 5 days', {'sd': '={today}+5'}), ('Start in 20 days', {'sd': '={today}+20'}), ('Checks need 10 days', {'l3': 10}), ('References need 12 days', {'l2': 12}))),
 TOOL('renew_count', 'Renewal Countdown', 'Renewal countdown with red, amber and green',
  'Type an expiry date and your amber and red days; see the days left, the colour, the date to renew by and Renew now, Book soon or Valid.', [
  I('ex', 'Expiry date', 'today+26', 'date'), I('amb', 'Amber from (days left)', 60), I('red', 'Red from (days left)', 30)], [
  O('Days left', 'int', '{in:ex}-{today}'), O('Colour', 'text', 'IF({in:ex}<{today},%s,IF({in:ex}-{today}<={in:red},%s,IF({in:ex}-{today}<={in:amb},%s,%s)))' % (ck('Expired'), ck('Red zone'), ck('Amber zone'), ck('Green'))),
  O('Renew by', 'date', 'MIN({in:ex},MAX({today},{in:ex}-{in:red}))'), O('Cannot be scheduled from', 'date', '{in:ex}+1'),
  O('Verdict', 'text', 'IF({in:ex}-{today}<={in:red},%s,IF({in:ex}-{today}<={in:amb},%s,%s))' % (vd('Renew now'), vd('Book soon'), ck('Green')))],
  GR('What if', ('Expires in 10 days', {'ex': '={today}+10'}), ('Expires in 45 days', {'ex': '={today}+45'}), ('Expires in 90 days', {'ex': '={today}+90'}), ('Expired 3 days ago', {'ex': '={today}-3'}))),
 TOOL('cannot_sched', 'Cannot Be Scheduled After', 'Cannot be scheduled after the expiry date: visits to move',
  'Type the expiry date, the visits scheduled after it and the earliest course date; see the visits and hours to move, the cover cost and Move visits or Renew first.', [
  I('ex', 'Expiry date', 'today+10', 'date'), I('vn', 'Visits scheduled after expiry', 6), I('vh', 'Hours per visit', 3, 'num'), I('wh', 'Caregiver weekly hours', 24), I('cd', 'Earliest course in (days)', 14), I('cp', 'Cover premium per hour', 3, 'money')], [
  O('First date to move visits from', 'date', '{in:ex}+1'), O('Visits to move', 'int', '{in:vn}'), O('Hours to move', 'num', '{in:vn}*{in:vh}'), O('Share of the weekly hours', 'pct', '{in:vn}*{in:vh}/{in:wh}'),
  O('Cover premium if all are covered at short notice', 'money', '{in:vn}*{in:vh}*{in:cp}'), O('Days to expiry', 'int', '{in:ex}-{today}'),
  O('Verdict', 'text', 'IF({in:cd}<={in:ex}-{today},%s,%s)' % (vd('Renew first'), vd('Move visits')))],
  GR('What if', ('Course in 5 days', {'cd': 5}), ('12 visits', {'vn': 12}), ('Expires in 30 days', {'ex': '={today}+30'}), ('4-hour visits', {'vh': 4}))),
 TOOL('renew_cost', 'Renewal Cost and Booking', 'Renewal cost and the latest booking date',
  'Type how many caregivers are due, the course price, paid hours and the provider lead days; see the total cost, the latest date to book and the verdict.', [
  I('nc', 'Caregivers due', 5), I('pr', 'Course price each', 65, 'money'), I('ph', 'Paid hours each', 7, 'num'), I('pay', 'Pay per hour', 18.5, 'money'), I('lead', 'Provider lead time (days)', 21), I('ex', 'Earliest expiry date', 'today+26', 'date')], [
  O('Course fees', 'money', '{in:nc}*{in:pr}'), O('Paid hours with payroll burden', 'money', '{in:nc}*{in:ph}*{in:pay}*(1+{set:payroll_burden})'), O('Total cost', 'money', '{in:nc}*({in:pr}+{in:ph}*{in:pay}*(1+{set:payroll_burden}))'),
  O('Cost per caregiver', 'money', '{in:pr}+{in:ph}*{in:pay}*(1+{set:payroll_burden})'), O('Latest booking date', 'date', '{in:ex}-{in:lead}'), O('Days left to book', 'int', '{in:ex}-{in:lead}-{today}'),
  O('Verdict', 'text', 'IF({in:ex}-{in:lead}<={today},%s,%s)' % (vd('Book now'), vd('On time to book')))],
  GR('What if', ('8 caregivers due', {'nc': 8}), ('Lead time 35 days', {'lead': 35}), ('Course price 90', {'pr': 90}), ('Expiry in 60 days', {'ex': '={today}+60'}))),
 TOOL('turnover_rate', 'Turnover Rate', 'Turnover rate against your flag and your own history',
  'Type the leavers in 12 months and the average headcount; see the rate, the change from a year ago and Normal, Watch or High.', [
  I('lv', 'Leavers in 12 months', 7), I('hc', 'Average caregivers', 37), I('fl', 'Flag (share)', 0.30, 'pct')], [
  O('Annual turnover', 'pct', '{in:lv}/{in:hc}'), O('Turnover a year ago', 'pct', 'IFERROR(SUMIFS(%s,%s,DATE(YEAR({today})-1,MONTH({today}),1)),0)' % (R('turnover.trail12'), R('turnover.month'))),
  O('Change in points', 'num', '({in:lv}/{in:hc}-IFERROR(SUMIFS(%s,%s,DATE(YEAR({today})-1,MONTH({today}),1)),0))*100' % (R('turnover.trail12'), R('turnover.month'))),
  O('Leavers that reach the flag', 'num', '{in:fl}*{in:hc}'), O('Verdict', 'text', 'IF({in:lv}/{in:hc}>{in:fl},%s,IF({in:lv}/{in:hc}>0.8*{in:fl},%s,%s))' % (vd('High'), vd('Watch'), vd('Normal')))],
  GR('What if', ('10 leavers', {'lv': 10}), ('12 leavers', {'lv': 12}), ('4 leavers', {'lv': 4}), ('Headcount 30', {'hc': 30}))),
 TOOL('first90', 'First-90-Day Retention', 'First-90-day retention and hires needed to stay level',
  'Type new hires, those who left within 90 days and your target; see the share lost, the share kept and how many hires you need to keep the number you want.', [
  I('nh', 'New hires', 14), I('lo', 'Left within 90 days', 4), I('tg', 'Target share lost', 0.10, 'pct'), I('keep', 'Caregivers you want to keep', 10)], [
  O('Share lost in 90 days', 'pct', '{in:lo}/{in:nh}'), O('Share kept', 'pct', '1-{in:lo}/{in:nh}'), O('Hires needed to keep the number wanted', 'int', 'ROUNDUP({in:keep}/(1-{in:lo}/{in:nh}),0)'),
  O('Extra hires because of early leavers', 'int', 'ROUNDUP({in:keep}/(1-{in:lo}/{in:nh}),0)-{in:keep}'), O('Hires needed at your target', 'int', 'ROUNDUP({in:keep}/(1-{in:tg}),0)'),
  O('Verdict', 'text', 'IF({in:lo}/{in:nh}<={in:tg},%s,%s)' % (vd('On target'), vd('Below target')))],
  GR('What if', ('2 left early', {'lo': 2}), ('6 left early', {'lo': 6}), ('Keep 20', {'keep': 20}), ('20 hires, 4 left', {'nh': 20}))),
 TOOL('turn_cost', 'Cost of Turnover', 'Cost of turnover this year',
  'Type leavers, the recruiting cost per hire, onboarding hours and weeks to full hours; see the cost per leaver, the total and its share of a year of gross margin.', [
  I('lv', 'Leavers this year', 7), I('ch', 'Recruiting cost per hire', 1050, 'money'), I('oh', 'Onboarding hours', 16), I('pay', 'Pay per hour', 18.5, 'money'), I('wk', 'Weeks to full hours', 4), I('hpc', 'Weekly hours at full speed', 24),
  I('mh', 'Gross margin per hour', 12, 'money'), I('ramp', 'Share of margin lost while ramping', 0.5, 'pct'), I('wh', 'Agency care hours a week', 900)], [
  O('Onboarding pay with burden, per leaver', 'money', '{in:oh}*{in:pay}*(1+{set:payroll_burden})'), O('Lost margin while ramping, per leaver', 'money', '{in:wk}*{in:hpc}*{in:mh}*{in:ramp}'),
  O('Cost per leaver', 'money', '{in:ch}+{in:oh}*{in:pay}*(1+{set:payroll_burden})+{in:wk}*{in:hpc}*{in:mh}*{in:ramp}'),
  O('Cost of turnover this year', 'money', '{in:lv}*({in:ch}+{in:oh}*{in:pay}*(1+{set:payroll_burden})+{in:wk}*{in:hpc}*{in:mh}*{in:ramp})'),
  O('Share of a year of gross margin', 'pct', '{in:lv}*({in:ch}+{in:oh}*{in:pay}*(1+{set:payroll_burden})+{in:wk}*{in:hpc}*{in:mh}*{in:ramp})/({in:wh}*52*{in:mh})'),
  O('Verdict', 'text', 'IF({in:lv}*({in:ch}+{in:oh}*{in:pay}*(1+{set:payroll_burden})+{in:wk}*{in:hpc}*{in:mh}*{in:ramp})/({in:wh}*52*{in:mh})>0.03,%s,IF({in:lv}*({in:ch}+{in:oh}*{in:pay}*(1+{set:payroll_burden})+{in:wk}*{in:hpc}*{in:mh}*{in:ramp})/({in:wh}*52*{in:mh})>0.015,%s,%s))' % (vd('High'), vd('Watch'), vd('Normal')))],
  GR('What if', ('10 leavers', {'lv': 10}), ('3 leavers', {'lv': 3}), ('Ramp takes 6 weeks', {'wk': 6}), ('Recruiting cost 1500', {'ch': 1500}))),
 TOOL('replace_cost', 'Replacement Cost', 'Replacement cost and the saving if early leavers halve',
  'Type the advert, check, staff and onboarding hours and lost margin weeks; see the cost of one replacement and what you save if first-90-day leavers halve.', [
  I('ad', 'Advert cost', 180, 'money'), I('ck', 'Background check', 45, 'money'), I('sh', 'Screening and interview hours', 5.5, 'num'), I('sr', 'Staff cost per hour', 22, 'money'), I('oh', 'Onboarding hours', 16), I('pay', 'Pay per hour', 18.5, 'money'),
  I('wk', 'Lost margin weeks', 4), I('mh', 'Margin per hour', 12, 'money'), I('hpc', 'Weekly hours', 24), I('lv', 'Leavers a year', 7), I('f90', 'First-90-day leavers a year', 4)], [
  O('Cost per replacement', 'money', '{in:ad}+{in:ck}+{in:sh}*{in:sr}+{in:oh}*{in:pay}*(1+{set:payroll_burden})+{in:wk}*{in:hpc}*{in:mh}*{set:ramp_loss_share}'),
  O('Replacement cost a year', 'money', '{in:lv}*({in:ad}+{in:ck}+{in:sh}*{in:sr}+{in:oh}*{in:pay}*(1+{set:payroll_burden})+{in:wk}*{in:hpc}*{in:mh}*{set:ramp_loss_share})'),
  O('Cost of first-90-day leavers', 'money', '{in:f90}*({in:ad}+{in:ck}+{in:sh}*{in:sr}+{in:oh}*{in:pay}*(1+{set:payroll_burden})+{in:wk}*{in:hpc}*{in:mh}*{set:ramp_loss_share})'),
  O('Saving if first-90-day leavers halve', 'money', '{in:f90}/2*({in:ad}+{in:ck}+{in:sh}*{in:sr}+{in:oh}*{in:pay}*(1+{set:payroll_burden})+{in:wk}*{in:hpc}*{in:mh}*{set:ramp_loss_share})'),
  O('Verdict', 'text', 'IF({in:f90}/2>=1,%s,%s)' % (vd('Fix the first 90 days'), vd('Low priority')))],
  GR('What if', ('Lost margin weeks 6', {'wk': 6}), ('8 early leavers', {'f90': 8}), ('Onboarding 24 hours', {'oh': 24}), ('No advert', {'ad': 0}))),
 TOOL('hire_or_not', 'Hire-or-Not Decision', 'Hire-or-not decision from hours waiting for a caregiver',
  'Type the hours waiting for a caregiver, what one caregiver takes, your margin and the hiring cost; see margin gained, months to pay back, short weeks and the verdict.', [
  I('wait', 'Hours waiting for a caregiver a week', 30, 'num'), I('cap', 'Hours one caregiver can take', 24, 'num'), I('mh', 'Margin per hour', 12, 'money'), I('cost', 'Recruiting and onboarding cost', 1500, 'money'), I('wk', 'Weeks to full hours', 4), I('ramp', 'Share of margin lost while ramping', 0.5, 'pct')], [
  O('Caregivers to hire', 'int', 'ROUNDUP({in:wait}/{in:cap},0)'), O('Margin gained a month', 'money', MM14), O('Margin lost while ramping', 'money', RAMP14), O('Months to pay back', 'num', PAY14),
  O('Weeks of the last 8 with a gap of 10 hours or more', 'int', PERS),
  O('Verdict', 'text', 'IF(AND({in:wait}>=0.75*{in:cap},%s>=3,%s<=6),%s,IF({in:wait}>=0.4*{in:cap},%s,%s))' % (PERS, PAY14, vd('Hire now'), vd('Wait'), vd('Not yet')))],
  GR('What if', ('Hours waiting 15', {'wait': 15}), ('Hours waiting 45', {'wait': 45}), ('Margin per hour 9', {'mh': 9}), ('Cost 2500', {'cost': 2500}))),
 TOOL('cg_needed', 'Caregivers Needed', 'Caregivers needed for the weekly hours target',
  'Type the weekly hours target, the hours you have, the hours one caregiver takes and the leavers you expect; see how many to hire and the date to start recruiting.', [
  I('tg', 'Weekly hours target', 960), I('cur', 'Weekly hours now', 909), I('avg', 'Hours per caregiver', 24), I('lv', 'Expected leavers next 12 months', 7), I('by', 'Target date', 'today+120', 'date'), I('lead', 'Days from advert to first shift', 35)], [
  O('Hours to add', 'int', 'MAX(0,{in:tg}-{in:cur})'), O('Caregivers for the growth', 'int', 'ROUNDUP(MAX(0,{in:tg}-{in:cur})/{in:avg},0)'), O('Caregivers to replace leavers', 'int', '{in:lv}'),
  O('Caregivers to hire', 'int', 'ROUNDUP(MAX(0,{in:tg}-{in:cur})/{in:avg},0)+{in:lv}'), O('Start recruiting by', 'date', '{in:by}-{in:lead}'),
  O('Applicants needed at your own rate', 'int', 'ROUNDUP((ROUNDUP(MAX(0,{in:tg}-{in:cur})/{in:avg},0)+{in:lv})*%s/%s,0)' % (S_('funnel.applicants'), S_('funnel.starts'))),
  O('Verdict', 'text', 'IF({in:by}-{in:lead}<={today},%s,%s)' % (vd('Start recruiting now'), vd('Recruit later')))],
  GR('What if', ('Target 1,000 hours', {'tg': 1000}), ('Target 930 hours', {'tg': 930}), ('12 leavers', {'lv': 12}), ('Caregivers take 30 hours', {'avg': 30}))),
 TOOL('hire_timing', 'Hire Timing Planner', 'Hire timing planner: when to start recruiting',
  'Type the monthly growth in hours, the days from advert to first shift, expected leavers and the free hours you have; see the month to start recruiting and how many adverts to run.', [
  I('gr', 'Hours added a month', 35), I('lead', 'Days from advert to first shift', 35), I('lv', 'Expected leavers a year', 7), I('fr', 'Free caregiver hours now', 40), I('hpc', 'Hours per caregiver', 24), I('apa', 'Applicants per advert', 9)], [
  O('Hours lost a month to leavers', 'num', '{in:lv}/12*{in:hpc}'), O('Free hours used per month', 'num', '{in:gr}+{in:lv}/12*{in:hpc}'), O('Months until free hours run out', 'num', '{in:fr}/({in:gr}+{in:lv}/12*{in:hpc})'),
  O('Start recruiting on', 'date', '{today}+ROUND({in:fr}/({in:gr}+{in:lv}/12*{in:hpc})*30,0)-{in:lead}'), O('Caregivers to hire in 12 months', 'int', 'ROUNDUP(({in:gr}*12)/{in:hpc},0)+{in:lv}'),
  O('Adverts to run', 'int', 'ROUNDUP((ROUNDUP(({in:gr}*12)/{in:hpc},0)+{in:lv})*%s/%s/{in:apa},0)' % (S_('funnel.applicants'), S_('funnel.starts'))),
  O('Verdict', 'text', 'IF({today}+ROUND({in:fr}/({in:gr}+{in:lv}/12*{in:hpc})*30,0)-{in:lead}<={today},%s,%s)' % (vd('Start recruiting now'), vd('Recruit later')))],
  GR('What if', ('Growth 60 hours a month', {'gr': 60}), ('Growth 15 hours a month', {'gr': 15}), ('Lead time 50 days', {'lead': 50}), ('Free hours 80', {'fr': 80}))),
 TOOL('hire_payback', 'Hire Payback Sensitivity', 'Hire payback at 50 to 90 percent of full hours',
  'Type the hours one caregiver takes, the margin, the hiring cost and a scenario; see the margin a month and months to pay back at 50, 60, 70, 80 and 90 percent filled.', [
  I('hrs', 'Weekly hours of one caregiver', 24), I('mh', 'Margin per hour', 12, 'money'), I('cost', 'Recruiting and onboarding cost', 1500, 'money'), I('fill', 'Hours filled', 0.7, 'pct'), IL('sc', 'Scenario', 'scen', 'Base')], [
  O('Margin a month at your fill', 'money', MG17('{in:fill}')), O('Months to pay back at your fill', 'num', '{in:cost}/' + MG17('{in:fill}')),
  O('Margin a month at 50%', 'money', MG17('0.5')), O('Margin a month at 60%', 'money', MG17('0.6')), O('Margin a month at 70%', 'money', MG17('0.7')), O('Margin a month at 80%', 'money', MG17('0.8')), O('Margin a month at 90%', 'money', MG17('0.9')),
  O('Months to pay back at 50%', 'num', '{in:cost}/' + MG17('0.5')), O('Months to pay back at 70%', 'num', '{in:cost}/' + MG17('0.7')), O('Months to pay back at 90%', 'num', '{in:cost}/' + MG17('0.9')),
  O('Verdict', 'text', 'IF({in:cost}/%s<=6,%s,IF({in:cost}/%s<=12,%s,%s))' % (MG17('{in:fill}'), vd('Hire now'), MG17('{in:fill}'), vd('Wait'), vd('Not yet')))],
  GR('What if', ('Fill 50%', {'fill': 0.5}), ('Fill 90%', {'fill': 0.9}), ('Margin per hour 9', {'mh': 9}), ('Cost 2500', {'cost': 2500}))),
 TOOL('whatif_apps', 'Applicants Against Conversion', 'What-if grid: applicants a month against conversion to start',
  'Type applicants a month, the share that start, the share still active after 90 days and the starts you need; see starts a month and a year, the caregivers kept and the verdict.', [
  I('ap', 'Applicants a month', 20), I('cv', 'Share that start', 0.11, 'pct'), I('rt', 'Still active after 90 days', 0.85, 'pct'), I('need', 'Starts needed a month', 2, 'num')], [
  O('Starts a month', 'num', '{in:ap}*{in:cv}'), O('Starts a year', 'num', '{in:ap}*{in:cv}*12'), O('Caregivers kept after 90 days, a year', 'num', '{in:ap}*{in:cv}*12*{in:rt}'),
  O('Applicants a month needed', 'int', 'ROUNDUP({in:need}/{in:cv},0)'), O('Verdict', 'text', 'IF({in:ap}*{in:cv}>={in:need},%s,%s)' % (vd('Enough applicants'), vd('Need more applicants')))],
  GR('Applicants a month against conversion', ('10 applicants, 8%', {'ap': 10, 'cv': 0.08}), ('15 applicants, 10%', {'ap': 15, 'cv': 0.10}), ('20 applicants, 12%', {'ap': 20, 'cv': 0.12}), ('30 applicants, 12%', {'ap': 30, 'cv': 0.12}), ('40 applicants, 15%', {'ap': 40, 'cv': 0.15}))),
]
assert len(tools) == 18
