"""HVAC suite part 1: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv1_lists import *
import hv1_data as D
import datetime as _dt

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def SER(d): return (to_date(d) - _dt.date(1899, 12, 30)).days
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
CANC, COMP, SCHED = tok('jobstatus', 'Cancelled'), tok('jobstatus', 'Completed'), tok('jobstatus', 'Scheduled')
LAST, PREV = tok('period', 'Last 90 days'), tok('period', 'Previous 90 days')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def CD(n): return '{range:calls.date},">="&({today}-%s)' % n
def JD(n): return '{range:jobs.date},">="&({today}-%s),{range:jobs.date},"<="&{today}' % n

tools = []
# 1 booking rate by source and who answered
def BSR(extra=''): return 'IFERROR(SUMIFS({range:book_source.booked},{range:book_source.period},%s%s)/SUMIFS({range:book_source.calls},{range:book_source.period},%s%s),0)' % (LAST, extra, LAST, extra)
def BAR(who): return 'IFERROR(SUMIFS({range:book_answered.booked},{range:book_answered.answered_by},%s,{range:book_answered.period},%s)/SUMIFS({range:book_answered.calls},{range:book_answered.answered_by},%s,{range:book_answered.period},%s),0)' % (who, LAST, who, LAST)
SRC = ',{range:book_source.source},{in:source}'
AH, OM, OW = tok('answeredby', 'After-hours line'), tok('answeredby', 'Office manager'), tok('answeredby', 'Owner')
tools.append(TOOL('booking_rate', 'Booking Rate Analyzer', 'Booking rate by source and by who answered',
  'Pick a lead source and an answering person: see the booking rate last 90 days against the 90 before, the lost value, the weakest source and a verdict against your booking target.', [
    IN('source', 'Lead source', 'list', key('source', 'Search ads'), list='source'), IN('who', 'Answered by', 'list', key('answeredby', 'After-hours line'), list='answeredby')], [
    O('Booking rate, all sources, last 90 days', 'pct', BSR()), O('Booking rate, all sources, previous 90 days', 'pct', 'IFERROR(SUMIFS({range:book_source.booked},{range:book_source.period},%s)/SUMIFS({range:book_source.calls},{range:book_source.period},%s),0)' % (PREV, PREV)),
    O('Booking rate target', 'pct', '{set:booking_target}'), O('Gap to the target, points', 'pct', BSR() + '-{set:booking_target}'),
    O('Booking rate of the chosen source, last 90 days', 'pct', BSR(SRC)), O('Lost value of the chosen source, last 90 days', 'money', 'SUMIFS({range:book_source.lost_value},{range:book_source.period},%s%s)' % (LAST, SRC)),
    O('Weakest source, last 90 days', 'text', 'IFERROR(INDEX({range:book_source.source},MATCH(SMALL({range:book_source.rate_last},1),{range:book_source.rate_last},0)),"")'),
    O('Booking rate of the weakest source', 'pct', 'IFERROR(SMALL({range:book_source.rate_last},1),0)'), O('Booking rate of the strongest source', 'pct', 'IFERROR(LARGE({range:book_source.rate_last},1),0)'),
    O('Booking rate of the chosen answerer, last 90 days', 'pct', BAR('{in:who}')), O('Booking rate when the office manager answers', 'pct', BAR(OM)), O('Booking rate when the owner answers', 'pct', BAR(OW)),
    O('Booking rate when the after-hours line answers', 'pct', BAR(AH)), O('Lost value, all sources, last 90 days', 'money', 'SUMIFS({range:book_source.lost_value},{range:book_source.period},%s)' % LAST),
    O('Verdict', 'text', 'IF(%s>={set:booking_target},%s,IF(%s<%s-0.05,%s,%s))' % (BSR(), ck('On target'), BAR(AH), BAR(OM), ck('Answer faster'), ck('Fix the weakest source')))],
  GR('What if', ('Referral', {'source': '=' + tok('source', 'Referral')}), ('Property manager', {'source': '=' + tok('source', 'Property manager')}), ('Local listing', {'source': '=' + tok('source', 'Local listing')}),
     ('Owner answering', {'who': '=' + OW}), ('Office manager answering', {'who': '=' + OM}))))
# 2 missed and unbooked call ranker
def M2(k): return 'MATCH(LARGE({range:calls.act_score},%d),{range:calls.act_score},0)' % k
OUT2 = []
for k in range(1, 6):
    OUT2 += [O('%d. Call to return' % k, 'text', 'IFERROR(INDEX({range:calls.call_id},%s)&" "&INDEX({range:calls.call_type},%s),"")' % (M2(k), M2(k))),
             O('%d. Estimated value' % k, 'money', 'IFERROR(INDEX({range:calls.lost_value},%s),0)' % M2(k)),
             O('%d. Age in days' % k, 'int', 'IFERROR({today}-INDEX({range:calls.date},%s),0)' % M2(k))]
tools.append(TOOL('call_ranker', 'Missed Call Ranker', 'Unbooked calls ranked by value, with the call-back date',
  'See the ten unbooked calls of the look-back window ranked by estimated job value, how old each one is and the money on the table; type the working days you allow for a call back and the share you expect to win back.', [
    I('callback_days', 'Working days allowed to call back', 1, 'int'), I('recovery', 'Share of the value you expect to win back', 0.3, 'pct')], [
    O('Unbooked calls in the window', 'int', 'COUNTIFS({range:calls.lost_value},">0",{range:calls.date},">="&({today}-{set:unbooked_days}))'),
    O('Money on the table, estimated value', 'money', 'SUMIFS({range:calls.lost_value},{range:calls.date},">="&({today}-{set:unbooked_days}))'),
    O('Expected win-back at your share', 'money', 'SUMIFS({range:calls.lost_value},{range:calls.date},">="&({today}-{set:unbooked_days}))*{in:recovery}'),
    O('Call back the first call by', 'date', 'IFERROR(WORKDAY(INDEX({range:calls.date},%s),{in:callback_days}),"")' % M2(1)),
    O('Verdict', 'text', 'IF(COUNTIFS({range:calls.lost_value},">0",{range:calls.date},">="&({today}-{set:unbooked_days}))=0,%s,IF(IFERROR({today}-INDEX({range:calls.date},%s),0)>={in:callback_days}+1,%s,%s))' % (ck('Nothing to recover'), M2(1), ck('Call back today'), ck('Call back this week')))] + OUT2,
  GR('What if', ('Allow 2 working days', {'callback_days': 2}), ('Win back 50 percent', {'recovery': 0.5}), ('Win back 15 percent', {'recovery': 0.15}), ('Same day call back', {'callback_days': 0}))))
# 3 after-hours and emergency call planner
def AHN(extra=''): return '(COUNTIFS({range:calls.hour},">="&{set:after_hour},%s%s)+COUNTIFS({range:calls.hour},"<7",%s%s))' % (CD(90), extra, CD(90), extra)
MISS = ',{range:calls.outcome},' + tok('calloutcome', 'Missed call')
def AHV(): return '(SUMIFS({range:calls.lost_value},{range:calls.hour},">="&{set:after_hour},%s%s)+SUMIFS({range:calls.lost_value},{range:calls.hour},"<7",%s%s))' % (CD(90), MISS, CD(90), MISS)
EMG = ',{range:calls.emergency},' + YES
NETG = '(%s/3*{in:win}*{set:margin_target}-{in:cost})' % AHV()
tools.append(TOOL('after_hours', 'After-Hours Call Planner', 'Emergency and after-hours calls: worth an answering service?',
  'From your own call log of the last 90 days: emergency calls by weekday, calls after hours, the calls nobody answered and the value they carried; type the monthly cost of an answering service and the share of those calls it would book.', [
    I('cost', 'Monthly cost of an answering service', 450), I('win', 'Share of missed after-hours calls it would book', 0.7, 'pct')], [
    O('Emergency calls, last 90 days', 'int', 'COUNTIFS(%s%s)' % (CD(90), EMG)), O('Calls after hours, last 90 days', 'int', AHN()), O('After-hours calls nobody answered', 'int', AHN(MISS)),
    O('Estimated value of those missed calls', 'money', AHV()), O('Missed after-hours calls a month', 'num', AHN(MISS) + '/3'), O('Value lost a month', 'money', AHV() + '/3'),
    O('Value you would win back a month', 'money', AHV() + '/3*{in:win}'), O('Margin on that value, at your margin target', 'money', AHV() + '/3*{in:win}*{set:margin_target}'),
    O('Net gain a month after the service cost', 'money', NETG)] +
    [O('Emergency calls on %s' % w, 'int', 'COUNTIFS(%s%s,{range:calls.weekday},%s)' % (CD(90), EMG, tok('wday7', w))) for w in WEEKDAYS7] +
    [O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (NETG, ck('Worth an answering service'), ck('Not yet')))],
  GR('What if', ('Service costs 900 a month', {'cost': 900}), ('Service books 50 percent', {'win': 0.5}), ('Service costs 250', {'cost': 250}), ('Service books 90 percent', {'win': 0.9}))))
# 4 call-to-job conversion by call type
TYP = ',{range:calls.call_type},{in:ctype}'
tools.append(TOOL('call_conversion', 'Call-to-Job Conversion', 'Conversion and lost value by call type',
  'Pick a call type and a number of days: calls, booked calls, jobs completed, the value booked and lost, and whether this type loses the most value of all types. The what-if rows walk through every call type.', [
    IN('ctype', 'Call type', 'list', key('calltype', 'Quote'), list='calltype'), I('days', 'Days back', 75, 'int')], [
    O('Calls of this type', 'int', 'COUNTIFS(%s%s)' % (CD('{in:days}'), TYP)), O('Booked calls', 'int', 'SUMIFS({range:calls.booked},%s%s)' % (CD('{in:days}'), TYP)),
    O('Booking rate', 'pct', 'IFERROR(SUMIFS({range:calls.booked},%s%s)/COUNTIFS(%s%s),0)' % (CD('{in:days}'), TYP, CD('{in:days}'), TYP)),
    O('Jobs completed from this reason', 'int', 'COUNTIFS({range:jobs.reason},{in:ctype},{range:jobs.status},%s,%s)' % (COMP, JD('{in:days}'))),
    O('Estimated value booked', 'money', 'SUMIFS({range:calls.est_value},{range:calls.booked},1,%s%s)' % (CD('{in:days}'), TYP)), O('Estimated value lost', 'money', 'SUMIFS({range:calls.lost_value},%s%s)' % (CD('{in:days}'), TYP)),
    O('Share of all lost value', 'pct', 'IFERROR(SUMIFS({range:calls.lost_value},%s%s)/SUMIFS({range:calls.lost_value},%s),0)' % (CD('{in:days}'), TYP, CD('{in:days}'))),
    O('Call type with the most lost value, 90 days', 'text', 'IFERROR(INDEX({range:calls.call_type},MATCH(MAX({range:calls.type_lost}),{range:calls.type_lost},0)),"")'),
    O('Verdict', 'text', 'IF({in:ctype}=IFERROR(INDEX({range:calls.call_type},MATCH(MAX({range:calls.type_lost}),{range:calls.type_lost},0)),""),%s,IF(IFERROR(SUMIFS({range:calls.lost_value},%s%s)/SUMIFS({range:calls.lost_value},%s),0)>=0.15,%s,%s))' % (ck('Most lost value: fix this type first'), CD('{in:days}'), TYP, CD('{in:days}'), ck('A large share of the loss'), ck('A smaller loss')))],
  GR('Every call type', *[(t, {'ctype': '=' + tok('calltype', t)}) for t in CALL_TYPES])))
# 5 weekly dispatch board
OUT5 = []
for k, w in enumerate(WEEKDAYS):
    d = '({in:week}+%d)' % k
    DS = lambda col: 'SUMIFS({range:dispatch.%s},{range:dispatch.date},%s)' % (col, d)
    OUT5 += [O('%s: jobs' % w, 'int', DS('jobs')), O('%s: free hours' % w, 'num', DS('free_hours')),
             O('%s: verdict' % w, 'text', 'IF(COUNTIFS({range:dispatch.date},%s,{range:dispatch.flag},%s)>0,%s,IF(OR(%s>0,%s<{set:capacity_hours}),%s,%s))' % (d, ck('Over capacity'), ck('Red: over capacity'), DS('no_parts'), DS('free_hours'), ck('Amber: parts or little room'), ck('Green: room and parts')))]
WK = '{range:dispatch.date},">="&{in:week},{range:dispatch.date},"<="&({in:week}+4)'
tools.append(TOOL('dispatch_week', 'Weekly Dispatch Board', 'Dispatch board for one week, day by day',
  'Type the Monday of the week: for each day the jobs, booked and drive hours, free hours, technicians over capacity and jobs with no parts confirmed, with a green, amber or red verdict from the Dispatch Board sheet.', [
    I('week', 'Monday of the week', iso(week_start(D.TD)), 'date')], [
    O('Jobs in the week', 'int', 'SUMIFS({range:dispatch.jobs},%s)' % WK), O('Booked and drive hours in the week', 'num', 'SUMIFS({range:dispatch.booked_hours},%s)+SUMIFS({range:dispatch.drive_hours},%s)' % (WK, WK)),
    O('Technician days over capacity', 'int', 'COUNTIFS(%s,{range:dispatch.flag},%s)' % (WK, ck('Over capacity'))),
    O('Jobs with no parts confirmed', 'int', 'SUMIFS({range:dispatch.no_parts},%s)' % WK),
    O('Week verdict', 'text', 'IF(COUNTIFS(%s,{range:dispatch.flag},%s)>0,%s,IF(SUMIFS({range:dispatch.no_parts},%s)>0,%s,%s))' % (WK, ck('Over capacity'), ck('Red: over capacity'), WK, ck('Amber: parts or little room'), ck('Green: room and parts')))] + OUT5,
  GR('Which week', ('This week', {'week': SER(week_start(D.TD))}), ('Next week', {'week': SER(week_start(D.TD)) + 7}))))
# 6 capacity check for a new job
def FD(k): return 'IFERROR(INDEX({range:capacity.free_hours},MATCH(WORKDAY({today},%d),{range:capacity.date},0)),0)' % k
NEED6 = '({in:hours}+IFERROR(AVERAGEIFS({range:jobs.drive_hours},{range:jobs.area},{in:area}),0.5))'
CH6 = 'IF(%s>=%s,WORKDAY({today},1)' % (FD(1), NEED6)
for k in range(2, 11): CH6 += ',IF(%s>=%s,WORKDAY({today},%d)' % (FD(k), NEED6, k)
CH6 += ',""' + ')' * 10
tools.append(TOOL('capacity_check', 'Capacity Check for a New Job', 'First day with room for a new job',
  'Type the job type, the hours on site and the area: see the hours the job needs with drive time and the first of the next 10 working days with enough free hours, or the day with the most room to offer.', [
    IN('jtype', 'Job type', 'list', key('jobtype', 'Furnace tune-up'), list='jobtype'), I('hours', 'Hours on site', 2.5, 'num'), IN('area', 'Area', 'list', key('area', 'Lakeside'), list='area')], [
    O('Average drive hours to the area', 'num', 'IFERROR(AVERAGEIFS({range:jobs.drive_hours},{range:jobs.area},{in:area}),0.5)'), O('Hours the job needs with drive time', 'num', NEED6),
    O('Usual hours for this job type', 'num', 'IFERROR(INDEX({range:job_types.avg_hours},MATCH({in:jtype},{range:job_types.job_type},0)),0)'),
    O('First day with room', 'date', CH6), O('Day with the most free hours', 'date', 'IFERROR(INDEX({range:capacity.date},MATCH(LARGE({range:capacity.room_score},1),{range:capacity.room_score},0)),"")'),
    O('Free hours on that day', 'num', 'IFERROR(INDEX({range:capacity.free_hours},MATCH(LARGE({range:capacity.room_score},1),{range:capacity.room_score},0)),0)'),
    O('Verdict', 'text', 'IF(%s="",%s,%s)' % (CH6, ck('No room: offer the day with most room'), ck('Book the first day with room')))] +
    [O('Free hours, working day %d' % k, 'num', FD(k)) for k in range(1, 11)],
  GR('What if', ('A long job, 6 hours', {'hours': 6}), ('A short job, 1 hour', {'hours': 1}), ('Westbrook', {'area': '=' + tok('area', 'Westbrook')}), ('Heavy day, 14 hours', {'hours': 14}))))
# 7 drive-time planner
tools.append(TOOL('drive_planner', 'Drive-Time Planner', 'Drive time and what regrouping jobs by area would save',
  'Type the days back and the share of drive time a regrouped week would save: see the drive hours, their share of the working time, the cost of that drive and the hours and cost saved.', [
    I('days', 'Days back', 30, 'int'), I('saving', 'Share of drive time a regrouped week would save', 0.25, 'pct'), I('ok', 'Drive share you accept', 0.15, 'pct')], [
    O('Jobs in the period', 'int', 'COUNTIFS(%s,{range:jobs.status},"<>"&%s)' % (JD('{in:days}'), CANC)), O('Hours on site', 'num', 'SUMIFS({range:jobs.hours},%s,{range:jobs.status},"<>"&%s)' % (JD('{in:days}'), CANC)),
    O('Drive hours', 'num', 'SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)' % (JD('{in:days}'), CANC)),
    O('Drive share of working time', 'pct', 'IFERROR(SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)/(SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)+SUMIFS({range:jobs.hours},%s,{range:jobs.status},"<>"&%s)),0)' % ((JD('{in:days}'), CANC) * 3)),
    O('Drive hours a job', 'num', 'IFERROR(SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)/COUNTIFS(%s,{range:jobs.status},"<>"&%s),0)' % ((JD('{in:days}'), CANC) * 2)),
    O('Cost of the drive, technician and vehicle', 'money', 'SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)*({set:tech_cost_hour}+{set:vehicle_hour})' % (JD('{in:days}'), CANC)),
    O('Hours a regrouped week would save', 'num', 'SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)*{in:saving}' % (JD('{in:days}'), CANC)),
    O('Cost saved in the period', 'money', 'SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)*{in:saving}*({set:tech_cost_hour}+{set:vehicle_hour})' % (JD('{in:days}'), CANC)),
    O('Cost saved over 12 months', 'money', 'SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)*{in:saving}*({set:tech_cost_hour}+{set:vehicle_hour})*365/{in:days}' % (JD('{in:days}'), CANC))] +
    [O('Average drive hours, %s' % a, 'num', 'IFERROR(AVERAGEIFS({range:jobs.drive_hours},{range:jobs.area},%s,%s,{range:jobs.status},"<>"&%s),0)' % (tok('area', a), JD('{in:days}'), CANC)) for a in AREAS] +
    [O('Verdict', 'text', 'IF(IFERROR(SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)/(SUMIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s)+SUMIFS({range:jobs.hours},%s,{range:jobs.status},"<>"&%s)),0)>{in:ok},%s,%s)' % ((JD('{in:days}'), CANC) * 3 + (ck('Regroup the week by area'), ck('Routes are tight'))))],
  GR('What if', ('Last 14 days', {'days': 14}), ('Last 60 days', {'days': 60}), ('Saving 40 percent', {'saving': 0.4}), ('Accept 10 percent drive', {'ok': 0.10}))))
# 8 emergency reserve
EM12 = '{range:calls_month.month},">="&EDATE(%s,-12),{range:calls_month.month},"<"&%s' % (MS, MS)
EPD = 'SUMIFS({range:calls_month.emergency_calls},%s)/365' % EM12
BR12 = 'IFERROR(SUMIFS({range:calls_month.booked},%s)/SUMIFS({range:calls_month.calls},%s),0)' % (EM12, EM12)
PEAK = 'SUMPRODUCT(MAX(({range:calls_month.month}>=EDATE(%s,-12))*({range:calls_month.month}<%s)*{range:calls_month.emergency_calls}))/30.4' % (MS, MS)
NEED8 = '(%s)*%s*{in:same}*{in:ehours}' % (EPD, BR12); PK8 = '(%s)*%s*{in:same}*{in:ehours}' % (PEAK, BR12)
tools.append(TOOL('emergency_reserve', 'Emergency Slot Reserve', 'Hours to hold back each day for emergency calls',
  'From the last 12 months of your call counts: emergency calls a day, in the busiest month, and the hours they need against the hours you hold back, with a hold-more, hold-less or right verdict.', [
    I('reserve', 'Hours held back each day', 2.5, 'num'), I('ehours', 'Hours of an emergency job, drive included', 2.2, 'num'), I('same', 'Share of emergencies you must serve the same day', 0.5, 'pct')], [
    O('Emergency calls, last 12 months', 'int', 'SUMIFS({range:calls_month.emergency_calls},%s)' % EM12), O('Emergency calls a day, 12-month average', 'num', EPD), O('Emergency calls a day, busiest month', 'num', PEAK),
    O('Booking rate, last 12 months', 'pct', BR12), O('Hours needed a day, average', 'num', NEED8), O('Hours needed a day, busiest month', 'num', PK8), O('Hours held back now', 'num', '{in:reserve}'),
    O('Gap to the average need, hours', 'num', '{in:reserve}-' + NEED8), O('Capacity share held back, one technician day', 'pct', '{in:reserve}/{set:capacity_hours}'),
    O('Verdict', 'text', 'IF({in:reserve}<%s,%s,IF({in:reserve}>%s,%s,%s))' % (NEED8, ck('Hold more'), PK8, ck('Hold less'), ck('Right')))],
  GR('What if', ('Hold 4 hours', {'reserve': 4}), ('Hold 6 hours', {'reserve': 6}), ('Serve 80 percent same day', {'same': 0.8}), ('Longer emergency jobs, 3 hours', {'ehours': 3}), ('Hold 1 hour', {'reserve': 1}))))
# 9 job record to work order
JD9 = next((j['job_id'] for j in D.JOBS if j['status'] == 'Scheduled' and j['date'] > D.iso(D.TD) and j['equipment_id'] and j['assistant'] and not j['parts_ready']), D.workorders_d()[0]['job_id'])
def J9(c, d='""'):
    f = 'IFERROR(INDEX({range:jobs.%s},MATCH({in:job},{range:jobs.job_id},0)),%s)' % (c, d)
    return f if d != '""' else '(' + f + '&"")'
PERM9 = 'IFERROR(INDEX({range:permits.status},MATCH({in:job},{range:permits.job_id},0)),%s)' % ck('No permit record')
MISS9 = ['%s=""' % J9('equipment_id'), '%s=%s' % (J9('parts_ready'), NO), 'AND(%s=%s,%s=%s)' % (J9('permit_needed'), YES, PERM9, tok('permitstatus', 'Applied')), 'IFERROR(INDEX({range:sites.phone},MATCH(%s,{range:sites.site_id},0)),"")=""' % J9('site_id')]
CNT9 = '(' + '+'.join('IF(%s,1,0)' % m for m in MISS9) + ')'
tools.append(TOOL('work_order_check', 'Work Order Builder', 'Job record to work order, with a completeness check',
  'Type a job number: the work order fields (date, site reference, area, job type, reason, technician, van, equipment, parts, permit) and a check that lists what is missing before you print the order with its customer-signature line.', [
    I('job', 'Job', JD9, 'text')], [
    O('Date', 'date', 'IFERROR(INDEX({range:jobs.date},MATCH({in:job},{range:jobs.job_id},0)),"")'), O('Start time', 'text', J9('start')), O('Site reference', 'text', J9('site_ref')), O('Area', 'text', J9('area')),
    O('Job type', 'text', J9('job_type')), O('Reason for the call', 'text', J9('reason')), O('Technician', 'text', J9('technician')), O('Assistant', 'text', J9('assistant')), O('Van', 'text', J9('van')),
    O('Hours on site', 'num', J9('hours', 0)), O('Equipment record', 'text', J9('equipment_id')), O('Parts confirmed', 'text', J9('parts_ready')), O('Permit needed', 'text', J9('permit_needed')),
    O('Permit status', 'text', PERM9), O('Customer phone', 'text', 'IFERROR(INDEX({range:sites.phone},MATCH(%s,{range:sites.site_id},0)),"")' % J9('site_id')), O('Items missing', 'int', CNT9),
    O('First item missing', 'text', 'IF(%s,%s,IF(%s,%s,IF(%s,%s,IF(%s,%s,%s))))' % (MISS9[0], ck('Equipment record missing'), MISS9[1], ck('Parts not confirmed'), MISS9[2], ck('Permit not approved'), MISS9[3], ck('Customer phone missing'), ck('Nothing missing'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (CNT9, ck('Ready to print'), ck('Fix before printing')))],
))
# 10 parts-ready checker
def M10(k): return 'MATCH(SMALL({range:jobs.parts_key},%d),{range:jobs.parts_key},0)' % k
EQ10 = ['Furnace replacement', 'Air conditioner replacement', 'Heat pump install', 'Water heater replacement']
def SUP(k): return 'IF(OR(%s),%s,%s)' % (','.join('INDEX({range:jobs.job_type},%s)=%s' % (M10(k), tok('jobtype', j)) for j in EQ10), ck('Your equipment supplier'), ck('Your parts counter'))
AT10 = '{range:jobs.parts_ready},%s,{range:jobs.status},%s,{range:jobs.date},">"&{today},{range:jobs.date},"<="&({today}+{in:days})' % (NO, SCHED)
OUT10 = []
for k in range(1, 5):
    OUT10 += [O('%d. Job and type' % k, 'text', 'IFERROR(INDEX({range:jobs.job_id},%s)&" "&INDEX({range:jobs.job_type},%s),"")' % (M10(k), M10(k))), O('%d. Date' % k, 'date', 'IFERROR(INDEX({range:jobs.date},%s),"")' % M10(k)),
              O('%d. Order from' % k, 'text', 'IFERROR(%s,"")' % SUP(k)), O('%d. Job price' % k, 'money', 'IFERROR(INDEX({range:jobs.price},%s),0)' % M10(k))]
tools.append(TOOL('parts_checker', 'Parts-Ready Checker', 'Jobs in the next days with parts not confirmed',
  'Type the days ahead: how many jobs have no parts confirmed, the money on those jobs and the five soonest, each with the date and who to order from, with an order-today verdict.', [
    I('days', 'Days ahead', 7, 'int')], [
    O('Jobs with no parts confirmed', 'int', 'COUNTIFS(%s)' % AT10), O('Job price at risk', 'money', 'SUMIFS({range:jobs.price},%s)' % AT10), O('Jobs due inside the order-ahead days', 'int', 'COUNTIFS({range:jobs.parts_ready},%s,{range:jobs.status},%s,{range:jobs.date},">"&{today},{range:jobs.date},"<="&({today}+{set:parts_alert_days}))' % (NO, SCHED)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,IF(COUNTIFS({range:jobs.parts_ready},%s,{range:jobs.status},%s,{range:jobs.date},">"&{today},{range:jobs.date},"<="&({today}+{set:parts_alert_days}))>0,%s,%s))' % (AT10, ck('All parts confirmed'), NO, SCHED, ck('Order today'), ck('Order this week')))] + OUT10,
  GR('What if', ('3 days ahead', {'days': 3}), ('14 days ahead', {'days': 14}), ('2 days ahead', {'days': 2}))))
# 11 same-day job slotter
BEST = lambda n: 'IF({in:trade}=%s,LARGE({range:dispatch.slot_hvac},%d),LARGE({range:dispatch.slot_plumbing},%d))' % (tok('trade', 'HVAC'), n, n)
def WHO(n): return 'IF({in:trade}=%s,INDEX({range:dispatch.technician},MATCH(LARGE({range:dispatch.slot_hvac},%d),{range:dispatch.slot_hvac},0)),INDEX({range:dispatch.technician},MATCH(LARGE({range:dispatch.slot_plumbing},%d),{range:dispatch.slot_plumbing},0)))' % (tok('trade', 'HVAC'), n, n)
NEED11 = '({in:hours}+IFERROR(AVERAGEIFS({range:jobs.drive_hours},{range:jobs.area},{in:area}),0.5))'
tools.append(TOOL('same_day_slotter', 'Same-Day Job Slotter', 'Which technician takes an urgent call today',
  'Type the trade, the hours on site and the area of an urgent call: the technicians of that trade ranked by free hours today from the Dispatch Board, the drive time to the area and a send-today or next-day verdict.', [
    IN('trade', 'Trade', 'list', key('trade', 'HVAC'), list='trade'), I('hours', 'Hours on site', 2, 'num'), IN('area', 'Area', 'list', key('area', 'Riverside'), list='area')], [
    O('Drive hours to the area', 'num', 'IFERROR(AVERAGEIFS({range:jobs.drive_hours},{range:jobs.area},{in:area}),0.5)'), O('Hours the call needs with drive time', 'num', NEED11),
    O('First choice', 'text', 'IFERROR(%s,"")' % WHO(1)), O('First choice, free hours today', 'num', 'IFERROR(%s,0)' % BEST(1)), O('Second choice', 'text', 'IFERROR(%s,"")' % WHO(2)), O('Second choice, free hours today', 'num', 'IFERROR(%s,0)' % BEST(2)),
    O('Free hours left after the call', 'num', 'IFERROR(%s-%s,0)' % (BEST(1), NEED11)), O('Verdict', 'text', 'IF(IFERROR(%s,0)>=%s,%s,%s)' % (BEST(1), NEED11, ck('Send the first choice today'), ck('Offer the next day')))],
  GR('What if', ('Plumbing call', {'trade': '=' + tok('trade', 'Plumbing')}), ('Long job, 5 hours', {'hours': 5}), ('Far area, Lakeside', {'area': '=' + tok('area', 'Lakeside')}), ('Short job, 1 hour', {'hours': 1}))))
# 12 permit and inspection tracker
OPEN12 = '{range:permits.status},"<>"&' + tok('permitstatus', 'Passed') + ',{range:permits.permit_id},"<>"'
AVG12 = 'IFERROR(AVERAGEIFS({range:permits.days_to_approve},{range:permits.applied_on},">="&({today}-365)),0)'
APP = tok('permitstatus', 'Applied')
def M12(k): return 'MATCH(LARGE({range:permits.chase_key},%d),{range:permits.chase_key},0)' % k
OUT12 = []
for k in range(1, 4):
    OUT12 += [O('%d. Permit and job type' % k, 'text', 'IFERROR(INDEX({range:permits.permit_id},%s)&" "&INDEX({range:permits.job_type},%s),"")' % (M12(k), M12(k))), O('%d. Status' % k, 'text', 'IFERROR(INDEX({range:permits.status},%s),"")' % M12(k)),
              O('%d. Days waiting' % k, 'int', 'IFERROR(INDEX({range:permits.days_waiting},%s),0)' % M12(k)), O('%d. Money held, job price' % k, 'money', 'IFERROR(INDEX({range:permits.job_price},%s),0)' % M12(k))]
tools.append(TOOL('permit_tracker', 'Permit and Inspection Tracker', 'Which permit to chase first',
  'Type the days over your shop average that you allow: open permits, those waiting for approval, your average wait from the Permit Log, the permits to chase today and the five open permits ranked by days waiting and money held.', [
    I('slack', 'Days over the shop average before you chase', 3, 'int')], [
    O('Open permits, not yet passed', 'int', 'COUNTIFS(%s)' % OPEN12), O('Waiting for approval', 'int', 'COUNTIFS({range:permits.status},%s)' % APP), O('Shop average days to approve, last 12 months', 'num', AVG12),
    O('Chase threshold, days', 'num', AVG12 + '+{in:slack}'), O('Permits to chase today', 'int', 'COUNTIFS({range:permits.status},%s,{range:permits.days_waiting},">"&(%s+{in:slack}))' % (APP, AVG12)),
    O('Money held on permits waiting for approval', 'money', 'SUMIFS({range:permits.job_price},{range:permits.status},%s)' % APP),
    O('Verdict', 'text', 'IF(COUNTIFS({range:permits.status},%s,{range:permits.days_waiting},">"&(%s+{in:slack}))>0,%s,IF(COUNTIFS(%s)>0,%s,%s))' % (APP, AVG12, ck('Chase today'), OPEN12, ck('Waiting normally'), ck('On track')))] + OUT12,
  GR('What if', ('Chase after 1 extra day', {'slack': 1}), ('Chase after 5 extra days', {'slack': 5}), ('Chase after 8 extra days', {'slack': 8}))))
# 13 van waiting cost
DAY13 = '({in:hours}*({in:tech}+{in:app}*{in:apprentice}+{in:vehicle}))'
tools.append(TOOL('van_waiting_cost', 'Van Waiting Cost', 'What a van and technician cost while they wait',
  'Type the days a van waits on a permit or parts and your hourly costs: the cost of one day and of the wait, what the permits held now already cost and which job to move first.', [
    I('days', 'Days the van waits', 3, 'int'), I('hours', 'Paid hours a day', 8.5, 'num'), I('tech', 'Technician cost per hour', 47), I('app', 'Apprentice on the van, 1 or 0', 1, 'int'), I('apprentice', 'Apprentice cost per hour', 27),
    I('vehicle', 'Vehicle cost per hour', 9.5), I('move', 'Move the van after this many days', 2, 'int')], [
    O('Cost of one day waiting', 'money', DAY13), O('Cost of the wait', 'money', DAY13 + '*{in:days}'), O('Jobs held by a permit now', 'int', 'COUNTIFS({range:permits.days_held},">0")'),
    O('Van cost already waiting on those permits', 'money', 'SUM({range:permits.van_cost_waiting})'), O('Job to move first', 'text', 'IF(MAX({range:permits.days_held})>0,INDEX({range:permits.job_id},MATCH(MAX({range:permits.days_held}),{range:permits.days_held},0)),"")'),
    O('Days that job is held', 'int', 'MAX({range:permits.days_held})'), O('Technician of that job', 'text', 'IF(MAX({range:permits.days_held})>0,INDEX({range:permits.technician},MATCH(MAX({range:permits.days_held}),{range:permits.days_held},0)),"")'),
    O('Verdict', 'text', 'IF({in:days}>={in:move},%s,%s)' % (ck('Move the van to other work'), ck('Hold one more day')))],
  GR('What if', ('One day waiting', {'days': 1}), ('Five days waiting', {'days': 5}), ('No apprentice', {'app': 0}), ('Costlier technician, 60 an hour', {'tech': 60}))))
# 14 permit lead-time forecast
AP14 = 'IFERROR(INDEX({range:permit_wait.avg_approve},MATCH({in:jtype},{range:permit_wait.job_type},0)),0)'
LEAD14 = 'ROUNDUP(%s+{in:buffer},0)' % AP14
CNT14 = 'IFERROR(INDEX({range:permit_wait.permits},MATCH({in:jtype},{range:permit_wait.job_type},0)),0)'
AB14 = 'WORKDAY({in:jobdate}-%s+1,-1)' % LEAD14
tools.append(TOOL('permit_lead_time', 'Permit Lead-Time Forecast', 'Latest safe date to apply for a permit',
  'Pick the job type and the job date: your own average days to approve and to inspect, the latest working day to apply with your buffer and a verdict. The history comes from the Permit Wait sheet.', [
    IN('jtype', 'Job type', 'list', key('jobtype', 'Water heater replacement'), list='jobtype'), I('jobdate', 'Job date', iso(D.TD + _dt.timedelta(days=11)), 'date'), I('buffer', 'Buffer days', 2, 'int')], [
    O('Permits in your history for this job type', 'int', CNT14), O('Average days to approve', 'num', AP14),
    O('Average days from approval to inspection', 'num', 'IFERROR(INDEX({range:permit_wait.avg_inspect},MATCH({in:jtype},{range:permit_wait.job_type},0)),0)'), O('Lead time with the buffer, days', 'int', LEAD14),
    O('Latest safe day to apply', 'date', AB14), O('Days from today to that day', 'int', AB14 + '-{today}'),
    O('Jobs of this type booked in the next 14 days', 'int', 'COUNTIFS({range:jobs.job_type},{in:jtype},{range:jobs.date},">"&{today},{range:jobs.date},"<="&({today}+14),{range:jobs.status},"<>"&%s)' % CANC),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<={today},%s,IF(%s-{today}<=2,%s,%s)))' % (CNT14, ck('No permit history: use your own estimate'), AB14, ck('Apply today'), AB14, ck('Apply within two days'), ck('Time is safe')))],
  GR('What if', ('Air conditioner replacement', {'jtype': '=' + tok('jobtype', 'Air conditioner replacement')}), ('Furnace replacement', {'jtype': '=' + tok('jobtype', 'Furnace replacement')}), ('Heat pump install', {'jtype': '=' + tok('jobtype', 'Heat pump install')}),
     ('Job in 3 days', {'jobdate': SER(D.TD) + 3}), ('Buffer 5 days', {'buffer': 5}))))
# 15 repeat-visit and callback flag
def R15(c, d='""'): return 'IFERROR(INDEX({range:repeats.%s},MATCH({in:job},{range:repeats.job_id},0)),%s)' % (c, d)
JD15 = D.repeats_d()[0]['job_id']
tools.append(TOOL('repeat_flag', 'Repeat-Visit Flag', 'Is this job a possible callback?',
  'Type a job number: the previous job at the same site, the days between, the technician of the earlier job and the cost of this visit shown against the earlier price, with a flag against your repeat window.', [
    I('job', 'Job', JD15, 'text')], [
    O('Site reference', 'text', R15('site_ref')), O('Job type', 'text', R15('job_type')), O('Technician', 'text', R15('technician')), O('Previous job at the site', 'text', R15('prev_job')),
    O('Technician of the earlier job', 'text', R15('prev_technician')), O('Days between the two jobs', 'int', R15('days_between', 0)), O('Repeat window, days', 'int', '{set:repeat_days}'),
    O('Cost of this visit', 'money', R15('cost', 0)), O('Price of the earlier job', 'money', R15('prev_price', 0)), O('Cost against the earlier price', 'pct', R15('cost_share', 0)),
    O('Possible callbacks of this technician, sample', 'int', 'COUNTIFS({range:jobs.technician},%s,{range:jobs.repeat},%s)' % (R15('technician'), ck('Possible callback'))),
    O('Verdict', 'text', 'IF(%s="",%s,%s)' % (R15('flag'), ck('Job not found'), R15('flag')))],
))
# 16 second-visit rate
def SV(extra): return 'IFERROR(COUNTIFS({range:jobs.repeat},%s,{range:jobs.date},"<="&{today}%s)/COUNTIFS({range:jobs.status},"<>"&%s,{range:jobs.date},"<="&{today}%s),0)' % (ck('Possible callback'), extra, CANC, extra)
STY = ',{range:jobs.site_type},{in:stype}'; JTY = ',{range:jobs.job_type},{in:jtype}'
LY12 = 'IFERROR(SUMIFS({range:calls_month.possible_callbacks},%s)/SUMIFS({range:calls_month.jobs},%s),0)' % (EM12, EM12)
RANK16 = '(1+' + '+'.join('IF(%s>%s,1,0)' % (SV(',{range:jobs.site_type},%s' % tok('sitetype', s)), SV(STY)) for s in SITE_TYPES) + ')'
tools.append(TOOL('second_visit_rate', 'Second-Visit Rate', 'Share of jobs followed by a second visit, by site type and job type',
  'Pick a site type and a job type: the share of jobs with another visit at the site inside your repeat window, the rate of every site type, the rank of your pick and a comparison with the last 12 months.', [
    IN('stype', 'Site type', 'list', key('sitetype', 'Rental'), list='sitetype'), IN('jtype', 'Job type', 'list', key('jobtype', 'Heating repair'), list='jobtype')], [
    O('Second-visit rate, all jobs in the sample', 'pct', SV('')), O('Second-visit rate of the chosen site type', 'pct', SV(STY)), O('Second-visit rate of the chosen job type', 'pct', SV(JTY)),
    O('Second-visit rate, last 12 months', 'pct', LY12)] + [O('Second-visit rate, %s sites' % s, 'pct', SV(',{range:jobs.site_type},%s' % tok('sitetype', s))) for s in SITE_TYPES] +
    [O('Rank of the chosen site type, 1 is highest', 'int', RANK16), O('Jobs of the chosen site type in the sample', 'int', 'COUNTIFS({range:jobs.site_type},{in:stype},{range:jobs.status},"<>"&%s)' % CANC),
     O('Verdict', 'text', 'IF(%s>%s*1.25,%s,IF(%s<%s*0.75,%s,%s))' % (SV(STY), LY12, ck('Above the last 12 months'), SV(STY), LY12, ck('Below the last 12 months'), ck('In line with the last 12 months')))],
  GR('What if', ('Home sites', {'stype': '=' + tok('sitetype', 'Home')}), ('Shop sites', {'stype': '=' + tok('sitetype', 'Shop')}), ('Office sites', {'stype': '=' + tok('sitetype', 'Office')}), ('Drain clearing', {'jtype': '=' + tok('jobtype', 'Drain clearing')}))))
# 17 call volume forecast
A3 = 'AVERAGEIFS({range:calls_month.calls},{range:calls_month.month},">="&EDATE(%s,-3),{range:calls_month.month},"<"&%s)' % (MS, MS)
def IDX(n): return 'IFERROR(SUMIFS({range:calls_month.calls},{range:calls_month.month},EDATE(%s,%d))/AVERAGEIFS({range:calls_month.calls},{range:calls_month.month},">="&EDATE(%s,%d),{range:calls_month.month},"<"&EDATE(%s,%d)),1)' % (MS, n - 12, MS, n - 15, MS, n - 12)
W1 = '(%s*%s*7/30.4)' % (A3, IDX(1)); W2 = '(%s*%s*7/30.4)' % (A3, IDX(2))
CALLS8 = '(4*%s+4*%s)' % (W1, W2)
BR17 = '{in:rate}'
tools.append(TOOL('call_forecast', 'Call Volume Forecast', 'Calls, jobs and hours for the next eight weeks',
  'From your last three full months and the same months last year: the seasonal index, expected calls, jobs and technician hours for the next 8 weeks with base, best and worst rows, and a capacity verdict.', [
    I('rate', 'Booking rate expected', 0.72, 'pct'), I('hours', 'Hours a job, drive included', 2.4, 'num'), I('spread', 'Best and worst case spread', 0.1, 'pct'), I('techs', 'Technicians on the road', 6, 'int')], [
    O('Average calls, last 3 full months', 'num', A3), O('Seasonal index, next month', 'num', IDX(1)), O('Seasonal index, month after', 'num', IDX(2)),
    O('Expected calls a week, next month', 'num', W1), O('Expected calls a week, month after', 'num', W2),
    O('Base: calls in 8 weeks', 'int', CALLS8), O('Base: jobs in 8 weeks', 'int', CALLS8 + '*{in:rate}'), O('Base: technician hours in 8 weeks', 'int', CALLS8 + '*{in:rate}*{in:hours}'),
    O('Best: calls in 8 weeks', 'int', CALLS8 + '*(1+{in:spread})'), O('Best: jobs in 8 weeks', 'int', CALLS8 + '*(1+{in:spread})*{in:rate}'), O('Best: technician hours in 8 weeks', 'int', CALLS8 + '*(1+{in:spread})*{in:rate}*{in:hours}'),
    O('Worst: calls in 8 weeks', 'int', CALLS8 + '*(1-{in:spread})'), O('Worst: jobs in 8 weeks', 'int', CALLS8 + '*(1-{in:spread})*{in:rate}'), O('Worst: technician hours in 8 weeks', 'int', CALLS8 + '*(1-{in:spread})*{in:rate}*{in:hours}'),
    O('Hours available a week', 'int', '{in:techs}*5*{set:capacity_hours}'), O('Base: hours needed a week', 'int', CALLS8 + '*{in:rate}*{in:hours}/8'),
    O('Best: share of capacity used', 'pct', 'IFERROR(%s*(1+{in:spread})*{in:rate}*{in:hours}/8/({in:techs}*5*{set:capacity_hours}),0)' % CALLS8),
    O('Verdict', 'text', 'IF(%s*(1+{in:spread})*{in:rate}*{in:hours}/8>{in:techs}*5*{set:capacity_hours}*0.85,%s,%s)' % (CALLS8, ck('Peak ahead: plan more capacity'), ck('Capacity is enough')))],
  GR('What if', ('Booking rate 80 percent', {'rate': 0.8}), ('Booking rate 65 percent', {'rate': 0.65}), ('Spread 20 percent', {'spread': 0.2}), ('Five technicians', {'techs': 5}), ('Longer jobs, 3 hours', {'hours': 3}))))
# 18 jobs-a-week break-even solver
NEED18 = '(({in:fixed}+{in:draw})/{in:margin})'
tools.append(TOOL('jobs_break_even', 'Jobs-a-Week Break-Even', 'Jobs a week to cover costs and the owner draw',
  'Type your fixed cost a month, the owner draw, the average margin per job and the jobs a week you do now: the jobs needed to cover both, the cushion and a verdict. The what-if rows move margin and cost by 10 percent.', [
    I('fixed', 'Fixed cost a month, overhead and vehicles', 38000), I('draw', 'Owner draw a month', 8500), I('margin', 'Average margin per job', 270), I('now', 'Jobs a week now', 75, 'int')], [
    O('Costs to cover a month, with the owner draw', 'money', '{in:fixed}+{in:draw}'), O('Jobs a month to break even', 'int', 'ROUNDUP(%s,0)' % NEED18), O('Jobs a week to break even', 'num', NEED18 + '/4.345'),
    O('Jobs a week now', 'int', '{in:now}'), O('Cushion over break-even, jobs a week', 'num', '{in:now}-%s/4.345' % NEED18), O('Cushion, share of jobs now', 'pct', 'IFERROR(({in:now}-%s/4.345)/{in:now},0)' % NEED18),
    O('Margin a month at the jobs now', 'money', '{in:now}*4.345*{in:margin}'), O('Left after fixed cost and draw', 'money', '{in:now}*4.345*{in:margin}-{in:fixed}-{in:draw}'),
    O('Break-even jobs a week, margin minus 10 percent', 'num', '({in:fixed}+{in:draw})/({in:margin}*0.9)/4.345'), O('Break-even jobs a week, margin plus 10 percent', 'num', '({in:fixed}+{in:draw})/({in:margin}*1.1)/4.345'),
    O('Break-even jobs a week, cost minus 10 percent', 'num', '({in:fixed}*0.9+{in:draw})/{in:margin}/4.345'), O('Break-even jobs a week, cost plus 10 percent', 'num', '({in:fixed}*1.1+{in:draw})/{in:margin}/4.345'),
    O('Verdict', 'text', 'IF({in:now}>=%s/4.345*1.2,%s,IF({in:now}>=%s/4.345,%s,%s))' % (NEED18, ck('Comfortably above break-even'), NEED18, ck('Just above break-even'), ck('Below break-even')))],
  GR('What if', ('Margin 10 percent lower', {'margin': 243}), ('Margin 10 percent higher', {'margin': 297}), ('Fixed cost 10 percent higher', {'fixed': 41800}), ('Slow season, 40 jobs a week', {'now': 40}), ('Owner draw 12000', {'draw': 12000}))))
assert len(tools) == 18, len(tools)
