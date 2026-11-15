"""Home care suite part 3: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc3_lists import *
import hc3_data as H

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
def i(k): return '{in:%s}' % k
def HM(k): return '(INT(%s/100)*60+MOD(%s,100))' % (i(k), i(k))
def TMIN(a, b): return 'SUMIFS({range:travel.minutes},{range:travel.from_area},%s,{range:travel.to_area},%s)' % (a, b)
def TKM(a, b): return 'SUMIFS({range:travel.km},{range:travel.from_area},%s,{range:travel.to_area},%s)' % (a, b)
def VERD3(x, a, b, lab=('On target', 'Watch', 'Act')):
    """x at or below a -> first label, at or below b -> second, else third"""
    return 'IF(%s<=%s,%s,IF(%s<=%s,%s,%s))' % (x, a, vd(lab[0]), x, b, vd(lab[1]), vd(lab[2]))
TD = H.TOOL_DEFAULTS
B = '(1+{set:payroll_burden})'

# 1 scheduled against actual
SCH = 'MOD(%s-%s,1440)/60' % (HM('s1'), HM('s0'))
WRK = 'ROUND(MOD(%s-%s,1440)/60,2)' % (HM('co'), HM('ci'))
LATE1 = 'MAX(0,%s-%s)' % (HM('ci'), HM('s0'))
DIFF1 = '(%s-%s)' % (WRK, SCH)
tools = [
 TOOL('sched_actual', 'Scheduled vs Actual', 'Scheduled against actual checker for one visit',
  'Type the scheduled start and end and the check-in and check-out as four digits (0900 is 09:00); see minutes late, hours worked, the billable hours and the flag Late, Short, Long or On time. Works for one visit of a one-person agency too.', [
  I('s0', 'Scheduled start (HHMM)', 900), I('s1', 'Scheduled end (HHMM)', 1200), I('ci', 'Check-in (HHMM)', 922), I('co', 'Check-out (HHMM)', 1141), I('mv', 'Minimum visit billed (hours)', 2)], [
  O('Scheduled hours', 'num', SCH), O('Minutes late', 'int', LATE1), O('Late check-in limit (minutes)', 'int', '{set:late_minutes}'), O('Hours worked', 'num', WRK), O('Hours difference against the schedule', 'num', DIFF1),
  O('Check-out against the scheduled end (minutes)', 'int', '%s-%s' % (HM('co'), HM('s1'))), O('Billable hours (quarter-hour steps, minimum visit)', 'num', 'MAX(%s,ROUND(%s*4,0)/4)' % (i('mv'), WRK)),
  O('Billable minus worked hours', 'num', 'MAX(%s,ROUND(%s*4,0)/4)-%s' % (i('mv'), WRK, WRK)),
  O('Visit flag', 'text', 'IF(%s>{set:late_minutes},%s,IF(%s<-0.25,%s,IF(%s>0.25,%s,%s)))' % (LATE1, ck('Late'), DIFF1, ck('Short'), DIFF1, ck('Long'), ck('On time')))],
  GR('What if', ('Arrives on time, full visit', {'ci': 900, 'co': 1200}), ('Stays 30 minutes longer', {'ci': 900, 'co': 1230}), ('Leaves 45 minutes early', {'ci': 900, 'co': 1115}), ('Arrives 40 minutes late', {'ci': 940, 'co': 1200}),
     ('90-minute stay on a 2-hour visit', {'s1': 1100, 'ci': 900, 'co': 1030}))),
 # 2 who to call
 TOOL('who_call', 'Who to Call Today', 'Who to call today: the visits without a check-in, ranked',
  'Reads Today Check-ins (type the time now in the Start sheet) and lists the five visits that are overdue the longest with the caregiver and client phones; the verdict says who to phone first. Works for a one-person agency as a daily to-do list.', [
  I('after', 'Minutes overdue after which the client is called first', 30)], [
  O('Visits overdue now', 'int', 'COUNTIFS({range:today.minutes_overdue},">0")'), O('Longest overdue (minutes)', 'int', 'MAX({range:today.minutes_overdue})'),
  O('Scheduled hours at risk', 'num', 'SUMIFS({range:today.sched_hours},{range:today.minutes_overdue},">0")'),
  O('Visits where the client is called first', 'int', 'COUNTIFS({range:today.minutes_overdue},">="&%s)' % i('after')),
  O('Verdict for the first call', 'text', 'IF(MAX({range:today.minutes_overdue})>=%s,%s,IF(MAX({range:today.minutes_overdue})>0,%s,%s))' % (i('after'), ck('Call client first'), ck('Call caregiver first'), ck('Checked in')))] + sum([[
  O('Call %d: caregiver and phone' % k, 'text', 'IFERROR(INDEX({range:today.caregiver},MATCH(%d,{range:today.call_rank},0))&" "&INDEX({range:today.caregiver_phone},MATCH(%d,{range:today.call_rank},0)),"-")' % (k, k)),
  O('Call %d: client and phone' % k, 'text', 'IFERROR(INDEX({range:today.client},MATCH(%d,{range:today.call_rank},0))&" "&INDEX({range:today.client_phone},MATCH(%d,{range:today.call_rank},0)),"-")' % (k, k)),
  O('Call %d: minutes overdue' % k, 'int', 'IFERROR(INDEX({range:today.minutes_overdue},MATCH(%d,{range:today.call_rank},0)),0)' % k)] for k in range(1, 6)], [])),
 # 3 late and missed rate
 TOOL('late_missed_rate', 'Late and Missed Rate', 'Late and missed rate per 100 visits, 3 months',
  'Type visits, late visits and missed visits for each of the last three full months; see the rates per 100 visits against your targets, the trend and a verdict On target, Watch or Act.', [
  I('v1', 'Visits, 3 months ago', TD['m3'][0]), I('l1', 'Late visits, 3 months ago', TD['m3'][1]), I('m1', 'Missed visits, 3 months ago', TD['m3'][2]),
  I('v2', 'Visits, 2 months ago', TD['m2'][0]), I('l2', 'Late visits, 2 months ago', TD['m2'][1]), I('m2', 'Missed visits, 2 months ago', TD['m2'][2]),
  I('v3', 'Visits, last month', TD['m1'][0]), I('l3', 'Late visits, last month', TD['m1'][1]), I('m3', 'Missed visits, last month', TD['m1'][2])], [
  O('Late per 100 visits, 3 months ago', 'num', '100*%s/%s' % (i('l1'), i('v1'))), O('Late per 100 visits, 2 months ago', 'num', '100*%s/%s' % (i('l2'), i('v2'))), O('Late per 100 visits, last month', 'num', '100*%s/%s' % (i('l3'), i('v3'))),
  O('Missed per 100 visits, 3 months ago', 'num', '100*%s/%s' % (i('m1'), i('v1'))), O('Missed per 100 visits, 2 months ago', 'num', '100*%s/%s' % (i('m2'), i('v2'))), O('Missed per 100 visits, last month', 'num', '100*%s/%s' % (i('m3'), i('v3'))),
  O('Late per 100 visits, 3 months together', 'num', '100*(%s+%s+%s)/(%s+%s+%s)' % (i('l1'), i('l2'), i('l3'), i('v1'), i('v2'), i('v3'))), O('Missed per 100 visits, 3 months together', 'num', '100*(%s+%s+%s)/(%s+%s+%s)' % (i('m1'), i('m2'), i('m3'), i('v1'), i('v2'), i('v3'))),
  O('Late target per 100 visits', 'num', '100*{set:late_visit_target}'), O('Missed target per 100 visits', 'num', '100*{set:missed_visit_target}'),
  O('Change in the late rate, first to last month (points)', 'num', '100*(%s/%s-%s/%s)' % (i('l3'), i('v3'), i('l1'), i('v1'))),
  O('Verdict, late rate (3 months)', 'text', VERD3('(%s+%s+%s)/(%s+%s+%s)' % (i('l1'), i('l2'), i('l3'), i('v1'), i('v2'), i('v3')), '{set:late_visit_target}', '1.5*{set:late_visit_target}')),
  O('Verdict, missed rate (3 months)', 'text', VERD3('(%s+%s+%s)/(%s+%s+%s)' % (i('m1'), i('m2'), i('m3'), i('v1'), i('v2'), i('v3')), '{set:missed_visit_target}', '1.5*{set:missed_visit_target}'))],
  GR('What if', ('Late visits 20% lower last month', {'l3': '=ROUND(%s*0.8,0)' % i('l3')}), ('Late visits at the target last month', {'l3': '=ROUND(%s*{set:late_visit_target},0)' % i('v3')}), ('Missed visits halved last month', {'m3': '=ROUND(%s*0.5,0)' % i('m3')}),
     ('Visits 10% higher, same late count', {'v3': '=ROUND(%s*1.1,0)' % i('v3')}))),
 # 4 area finder
 TOOL('area_finder', 'Area Problem Finder', 'Area problem finder: is one area worse than the agency?',
  'Type the visits, late and missed visits of one area and of the whole agency over the same period (60 days by default); see the gap in points and the verdict Investigate or Normal. The example is the area with repeated late and missed visits.', [
  I('av', 'Area visits', TD['area'][0]), I('al', 'Area late visits', TD['area'][1]), I('am', 'Area missed visits', TD['area'][2]), I('gv', 'Agency visits, same period', TD['agency'][0]), I('gl', 'Agency late visits', TD['agency'][1]),
  I('gm', 'Agency missed visits', TD['agency'][2]), I('gap', 'Gap in points that counts as a problem', 5)], [
  O('Area late per 100 visits', 'num', '100*%s/%s' % (i('al'), i('av'))), O('Agency late per 100 visits', 'num', '100*%s/%s' % (i('gl'), i('gv'))), O('Late gap (points)', 'num', '100*(%s/%s-%s/%s)' % (i('al'), i('av'), i('gl'), i('gv'))),
  O('Area missed per 100 visits', 'num', '100*%s/%s' % (i('am'), i('av'))), O('Agency missed per 100 visits', 'num', '100*%s/%s' % (i('gm'), i('gv'))), O('Missed gap (points)', 'num', '100*(%s/%s-%s/%s)' % (i('am'), i('av'), i('gm'), i('gv'))),
  O('Late visits above the agency rate', 'num', '%s-%s*%s/%s' % (i('al'), i('av'), i('gl'), i('gv'))), O('Missed visits above the agency rate', 'num', '%s-%s*%s/%s' % (i('am'), i('av'), i('gm'), i('gv'))),
  O('Area share of the agency\'s visits', 'pct', '%s/%s' % (i('av'), i('gv'))), O('Area share of the agency\'s late and missed visits', 'pct', '(%s+%s)/(%s+%s)' % (i('al'), i('am'), i('gl'), i('gm'))),
  O('Verdict', 'text', 'IF(OR(100*(%s/%s-%s/%s)>=%s,100*(%s/%s-%s/%s)>=%s/3),%s,%s)' % (i('al'), i('av'), i('gl'), i('gv'), i('gap'), i('am'), i('av'), i('gm'), i('gv'), i('gap'), vd('Investigate'), vd('Normal')))],
  GR('What if', ('Area late visits cut by a third', {'al': '=ROUND(%s*2/3,0)' % i('al')}), ('Area at the agency rate', {'al': '=ROUND(%s*%s/%s,0)' % (i('av'), i('gl'), i('gv')), 'am': '=ROUND(%s*%s/%s,0)' % (i('av'), i('gm'), i('gv'))}),
     ('Gap rule of 10 points', {'gap': 10}))),
 # 5 billable vs paid
 TOOL('billable_paid', 'Billable vs Paid Hours', 'Billable against paid hours and the weekly leak',
  'Type a typical week: hours delivered, billed and paid, the average bill rate and pay rate (example: the last four weeks); see the gap in hours and the leak in money per week and per year. A one-person agency can enter its own week.', [
  I('dh', 'Hours delivered in a week', TD['wk'][0], 'num'), I('bh', 'Hours billed in a week', TD['wk'][1], 'num'), I('ph', 'Hours paid in a week', TD['wk'][2], 'num'), I('br', 'Average bill rate per billed hour', TD['br'], 'money'), I('pr', 'Average pay rate per hour', TD['pr'], 'money')], [
  O('Paid minus billed hours a week', 'num', '%s-%s' % (i('ph'), i('bh'))), O('Paid minus delivered hours a week (paid travel)', 'num', '%s-%s' % (i('ph'), i('dh'))), O('Billed minus delivered hours a week (rounding)', 'num', '%s-%s' % (i('bh'), i('dh'))),
  O('Leak a week: hours paid above billed at loaded pay', 'money', 'MAX(0,%s-%s)*%s*%s' % (i('ph'), i('bh'), i('pr'), B)), O('Leak a year', 'money', '52*MAX(0,%s-%s)*%s*%s' % (i('ph'), i('bh'), i('pr'), B)),
  O('Value of hours billed above delivered, a week', 'money', '(%s-%s)*%s' % (i('bh'), i('dh'), i('br'))), O('Billed hours as a share of paid hours', 'pct', '%s/%s' % (i('bh'), i('ph'))),
  O('Hours of paid travel recovered by billing', 'pct', 'MIN(1,MAX(0,(%s-%s)/(%s-%s)))' % (i('bh'), i('dh'), i('ph'), i('dh'))),
  O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (i('ph'), i('bh'), vd('Leak found'), vd('No leak')))],
  GR('What if', ('Paid travel 20% higher', {'ph': '=%s+0.2*(%s-%s)' % (i('ph'), i('ph'), i('dh'))}), ('2 more hours billed a week', {'bh': '=%s+2' % i('bh')}), ('Pay rate +1', {'pr': '=%s+1' % i('pr')}), ('Billing back to paid hours', {'bh': '=%s' % i('ph')}))),
 # 6 leak by cause
 TOOL('leak_cause', 'Leak by Cause', 'Leak by cause: what pays hours that are never billed',
  'Type a typical week in hours: paid travel not billed, overrun not invoiced, hours billed above delivered (minimum visits) and hours paid on missed visits; see the leak per cause in money, the biggest cause and the net leak a year.', [
  I('th', 'Paid travel hours not billed, a week', TD['leak'][0], 'num'), I('oh', 'Overrun hours not invoiced, a week', TD['leak'][1], 'num'), I('rh', 'Hours billed above delivered (rounding), a week', TD['leak'][2], 'num'),
  I('mh', 'Hours paid on missed visits, a week', TD['leak'][3], 'num'), I('pr', 'Average pay rate per hour', TD['pr'], 'money')], [
  O('Travel paid, not billed: leak a week', 'money', '%s*%s*%s' % (i('th'), i('pr'), B)), O('Overrun not invoiced: leak a week', 'money', '%s*%s*%s' % (i('oh'), i('pr'), B)),
  O('Minimum-visit rounding: leak a week (negative is a gain)', 'money', '-%s*%s*%s' % (i('rh'), i('pr'), B)), O('Missed visit with pay: leak a week', 'money', '%s*%s*%s' % (i('mh'), i('pr'), B)),
  O('Net leak a week', 'money', '(%s+%s-%s+%s)*%s*%s' % (i('th'), i('oh'), i('rh'), i('mh'), i('pr'), B)), O('Net leak a year', 'money', '52*(%s+%s-%s+%s)*%s*%s' % (i('th'), i('oh'), i('rh'), i('mh'), i('pr'), B)),
  O('Net hours gap a week (paid minus billed)', 'num', '%s+%s-%s+%s' % (i('th'), i('oh'), i('rh'), i('mh'))),
  O('Biggest cause', 'text', 'IF(AND(%s>=%s,%s>=%s),%s,IF(%s>=%s,%s,%s))' % (i('th'), i('oh'), i('th'), i('mh'), vd('Travel paid, not billed'), i('oh'), i('mh'), vd('Overrun not billed'), vd('Missed visit with pay'))),
  O('Share of the leak that minimum visits recover', 'pct', 'MIN(1,%s/(%s+%s+%s))' % (i('rh'), i('th'), i('oh'), i('mh'))),
  O('Verdict', 'text', 'IF(%s+%s+%s>%s,%s,%s)' % (i('th'), i('oh'), i('mh'), i('rh'), vd('Leak found'), vd('No leak')))],
  GR('What if', ('Travel hours cut by a quarter', {'th': '=%s*0.75' % i('th')}), ('Overrun invoiced in full', {'oh': 0.01}), ('No missed visits paid', {'mh': 0.01}), ('Minimum visit rule dropped', {'rh': 0.01}))),
 # 7 mileage claim
 TOOL('mileage_claim', 'Mileage Claim Checker', 'Mileage claim checker against the distance between areas',
  'Choose the two areas of a leg and type the kilometres claimed; the expected distance and paid minutes come from Travel Times, the tolerance from the Start sheet; the verdict is Accept or Query.', [
  IL('fa', 'From area', 'area', 'Riverside'), IL('ta', 'To area', 'area', 'South Valley'), I('km', 'Distance claimed (km)', 26.5, 'num')], [
  O('Expected distance (km)', 'num', TKM(i('fa'), i('ta'))), O('Expected paid travel minutes', 'int', TMIN(i('fa'), i('ta'))), O('Difference claimed minus expected (km)', 'num', '%s-%s' % (i('km'), TKM(i('fa'), i('ta')))),
  O('Difference as a share of the expected distance', 'pct', '(%s-%s)/%s' % (i('km'), TKM(i('fa'), i('ta')), TKM(i('fa'), i('ta')))), O('Most that is accepted (km)', 'num', '%s*(1+{set:km_tolerance})' % TKM(i('fa'), i('ta'))),
  O('Amount claimed', 'money', '%s*{set:mileage_rate}' % i('km')), O('Amount at the expected distance', 'money', '%s*{set:mileage_rate}' % TKM(i('fa'), i('ta'))), O('Amount over the expected distance', 'money', 'MAX(0,%s-%s)*{set:mileage_rate}' % (i('km'), TKM(i('fa'), i('ta')))),
  O('Verdict', 'text', 'IF(%s<=%s*(1+{set:km_tolerance}),%s,%s)' % (i('km'), TKM(i('fa'), i('ta')), vd('Accept'), vd('Query')))],
  GR('What if', ('Claim at the expected distance', {'km': '=%s' % TKM(i('fa'), i('ta'))}), ('Claim 10% above', {'km': '=%s*1.1' % TKM(i('fa'), i('ta'))}), ('Claim 30% above', {'km': '=%s*1.3' % TKM(i('fa'), i('ta'))}))),
 # 8 travel cost per client
 TOOL('travel_client', 'Travel Cost per Client', 'Travel cost per client: absorb it or charge it',
  'Type a client\'s visits a month, the average paid travel minutes and kilometres per visit, the pay and bill rates and the hours per visit; see the travel cost per visit and per hour, its share of the bill and the verdict Absorb the travel or Charge travel.', [
  I('vis', 'Visits a month', 14), I('tm', 'Average paid travel minutes per visit', 32), I('km', 'Average kilometres per visit', 17.6, 'num'), I('pr', 'Pay rate per hour', TD['pr'], 'money'), I('hrs', 'Average hours per visit', 2.5, 'num'),
  I('br', 'Bill rate per hour', 34, 'money')], [
  O('Paid travel time per visit', 'money', '%s/60*%s' % (i('tm'), i('pr'))), O('Mileage per visit', 'money', '%s*{set:mileage_rate}' % i('km')), O('Payroll burden on the travel time', 'money', '%s/60*%s*{set:payroll_burden}' % (i('tm'), i('pr'))),
  O('Travel cost per visit', 'money', '%s/60*%s*%s+%s*{set:mileage_rate}' % (i('tm'), i('pr'), B, i('km'))), O('Travel cost per care hour', 'money', '(%s/60*%s*%s+%s*{set:mileage_rate})/%s' % (i('tm'), i('pr'), B, i('km'), i('hrs'))),
  O('Travel cost a month', 'money', '%s*(%s/60*%s*%s+%s*{set:mileage_rate})' % (i('vis'), i('tm'), i('pr'), B, i('km'))), O('Bill for one visit', 'money', '%s*%s' % (i('hrs'), i('br'))),
  O('Travel cost as a share of the bill', 'pct', '(%s/60*%s*%s+%s*{set:mileage_rate})/(%s*%s)' % (i('tm'), i('pr'), B, i('km'), i('hrs'), i('br'))),
  O('Travel charge per visit that covers the cost', 'money', '%s/60*%s*%s+%s*{set:mileage_rate}' % (i('tm'), i('pr'), B, i('km'))),
  O('Verdict', 'text', 'IF((%s/60*%s*%s+%s*{set:mileage_rate})/(%s*%s)<={set:travel_share_target},%s,%s)' % (i('tm'), i('pr'), B, i('km'), i('hrs'), i('br'), vd('Absorb the travel'), vd('Charge travel')))],
  GR('What if', ('Nearby client: 10 minutes, 5.5 km', {'tm': 10, 'km': 5.5}), ('Longer visits of 4 hours', {'hrs': 4}), ('Weekly visit instead of 3 a week', {'vis': 4}), ('Bill rate +10%', {'br': '=%s*1.1' % i('br')}))),
 # 9 pair sharing
 TOOL('pair_sharing', 'Visit Pair Sharing', 'Visit pair sharing: one caregiver for two visits',
  'Choose the areas of two visits and where each caregiver comes from, and type the minutes between the visits; see the travel minutes saved when one caregiver takes both, the saving a month and the verdict Share the pair or Keep apart.', [
  IL('va', 'Area of visit A', 'area', 'Riverside'), IL('vb', 'Area of visit B', 'area', 'Old Town'), IL('pa', 'Caregiver A comes from', 'area', 'North Hills'), IL('pb', 'Caregiver B comes from', 'area', 'South Valley'),
  I('gap', 'Minutes between the end of visit A and the start of visit B', 45), I('days', 'Days a month this pair repeats', 12), I('pr', 'Pay rate per hour', TD['pr'], 'money')], [
  O('Travel minutes now (two caregivers)', 'int', '%s+%s' % (TMIN(i('pa'), i('va')), TMIN(i('pb'), i('vb')))), O('Travel minutes if caregiver A takes both', 'int', '%s+%s' % (TMIN(i('pa'), i('va')), TMIN(i('va'), i('vb')))),
  O('Minutes saved each day', 'int', '%s-%s' % (TMIN(i('pb'), i('vb')), TMIN(i('va'), i('vb')))), O('Travel between the two visits (minutes)', 'int', TMIN(i('va'), i('vb'))), O('Spare minutes in the gap', 'int', '%s-%s' % (i('gap'), TMIN(i('va'), i('vb')))),
  O('Kilometres saved each day', 'num', '%s-%s' % (TKM(i('pb'), i('vb')), TKM(i('va'), i('vb')))), O('Saving a month: paid travel time', 'money', '(%s-%s)/60*%s*%s*%s' % (TMIN(i('pb'), i('vb')), TMIN(i('va'), i('vb')), i('pr'), B, i('days'))),
  O('Saving a month: mileage', 'money', '(%s-%s)*{set:mileage_rate}*%s' % (TKM(i('pb'), i('vb')), TKM(i('va'), i('vb')), i('days'))),
  O('Saving a month in total', 'money', '(%s-%s)/60*%s*%s*%s+(%s-%s)*{set:mileage_rate}*%s' % (TMIN(i('pb'), i('vb')), TMIN(i('va'), i('vb')), i('pr'), B, i('days'), TKM(i('pb'), i('vb')), TKM(i('va'), i('vb')), i('days'))),
  O('Verdict', 'text', 'IF(AND(%s>=%s,%s>%s),%s,%s)' % (i('gap'), TMIN(i('va'), i('vb')), TMIN(i('pb'), i('vb')), TMIN(i('va'), i('vb')), vd('Share the pair'), vd('Keep apart')))],
  GR('What if', ('Visits only 10 minutes apart', {'gap': 10}), ('Pair repeats 20 days a month', {'days': 20}), ('Caregiver B comes from Old Town', {'pb': '=' + tok('area', 'Old Town')}), ('Both visits in South Valley', {'va': '=' + tok('area', 'South Valley'), 'vb': '=' + tok('area', 'South Valley')}))),
 # 10 clustering
 TOOL('cluster_week', 'Area Clustering Saving', 'Area clustering saving for one caregiver\'s week',
  'Type one caregiver\'s visits by area for a week, the number of area changes in the schedule now and the minutes per change; see the travel minutes now, the minutes if the visits are clustered by day and the saving in money.', [
  I('v1', 'Visits in North Hills', 4), I('v2', 'Visits in Riverside', 3), I('v3', 'Visits in Old Town', 2), I('v4', 'Visits in East Park', 3), I('v5', 'Visits in Lakeside', 2), I('v6', 'Visits in South Valley', 1),
  I('chg', 'Area changes in the week as scheduled now', 11), I('mpc', 'Average paid minutes per area change', 28), I('pr', 'Pay rate per hour', TD['pr'], 'money')], [
  O('Visits in the week', 'int', '%s+%s+%s+%s+%s+%s' % tuple(i('v%d' % k) for k in range(1, 7))), O('Areas visited', 'int', '(%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)' % tuple(i('v%d' % k) for k in range(1, 7))),
  O('Area changes if clustered by day', 'int', '(%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)-1' % tuple(i('v%d' % k) for k in range(1, 7))), O('Travel minutes now', 'int', '%s*%s' % (i('chg'), i('mpc'))),
  O('Travel minutes if clustered', 'int', '((%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)-1)*%s' % (tuple(i('v%d' % k) for k in range(1, 7)) + (i('mpc'),))),
  O('Minutes saved a week', 'int', 'MAX(0,%s*%s-((%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)-1)*%s)' % ((i('chg'), i('mpc')) + tuple(i('v%d' % k) for k in range(1, 7)) + (i('mpc'),))),
  O('Saving a week in money', 'money', 'MAX(0,%s*%s-((%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)-1)*%s)/60*%s*%s' % ((i('chg'), i('mpc')) + tuple(i('v%d' % k) for k in range(1, 7)) + (i('mpc'), i('pr'), B))),
  O('Saving a year in money', 'money', '52*MAX(0,%s*%s-((%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)-1)*%s)/60*%s*%s' % ((i('chg'), i('mpc')) + tuple(i('v%d' % k) for k in range(1, 7)) + (i('mpc'), i('pr'), B))),
  O('Verdict', 'text', 'IF(%s*%s-((%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)+(%s>0)-1)*%s>=30,%s,%s)' % ((i('chg'), i('mpc')) + tuple(i('v%d' % k) for k in range(1, 7)) + (i('mpc'), vd('Cluster the week'), vd('Keep as is'))))],
  GR('What if', ('Only 7 area changes now', {'chg': 7}), ('Shorter hops of 18 minutes', {'mpc': 18}), ('Four areas only', {'v5': 0, 'v6': 0}), ('Pay rate +2', {'pr': '=%s+2' % i('pr')}))),
 # 11 time sheet reconciliation
 TOOL('timesheet_recon', 'Time Sheet Reconciliation', 'Time sheet reconciliation before payroll',
  'Type the hours claimed on a time sheet and the hours from the check-ins; see the difference, the money at stake and the verdict Pay as claimed, Query hours or Correct hours. A one-person agency can check its own time sheet.', [
  I('cl', 'Hours claimed on the time sheet', 38.5, 'num'), I('ck', 'Hours from the check-ins', 36.75, 'num'), I('tol', 'Tolerance (hours)', 0.25, 'num'), I('big', 'Difference at which hours are corrected, not queried (hours)', 1.0, 'num'), I('pr', 'Pay rate per hour', TD['pr'], 'money')], [
  O('Difference (claimed minus check-ins)', 'num', '%s-%s' % (i('cl'), i('ck'))), O('Difference as a share of the check-in hours', 'pct', '(%s-%s)/%s' % (i('cl'), i('ck'), i('ck'))),
  O('Money at stake at loaded pay', 'money', 'ABS(%s-%s)*%s*%s' % (i('cl'), i('ck'), i('pr'), B)),
  O('Hours to pay', 'num', 'IF(ABS(%s-%s)<=%s,%s,%s)' % (i('cl'), i('ck'), i('tol'), i('cl'), i('ck'))), O('Pay to release', 'money', 'IF(ABS(%s-%s)<=%s,%s,%s)*%s' % (i('cl'), i('ck'), i('tol'), i('cl'), i('ck'), i('pr'))),
  O('Hours still to prove if queried', 'num', 'MAX(0,%s-%s)' % (i('cl'), i('ck'))),
  O('Verdict', 'text', 'IF(ABS(%s-%s)<=%s,%s,IF(AND(%s>%s,%s-%s<=%s),%s,%s))' % (i('cl'), i('ck'), i('tol'), vd('Pay as claimed'), i('cl'), i('ck'), i('cl'), i('ck'), i('big'), vd('Query hours'), vd('Correct hours')))],
  GR('What if', ('Within tolerance', {'cl': '=%s+0.2' % i('ck')}), ('Half an hour over', {'cl': '=%s+0.5' % i('ck')}), ('Three hours over', {'cl': '=%s+3' % i('ck')}), ('Hours claimed below check-ins', {'cl': '=%s-1.5' % i('ck')}))),
 # 12 rounding rule
 TOOL('rounding_rule', 'Rounding Rule Test', 'Rounding rule test: 5, 15 or 30 minutes',
  'Type the average hours worked on a visit, the rounding step in minutes and the visits and rate; see billed against worked minutes and what the rule gains or loses a month, rounding to the nearest step or always up.', [
  I('wh', 'Hours worked on a typical visit', 2.33, 'num'), I('step', 'Rounding step (minutes: 5, 15 or 30)', 15), I('vis', 'Visits a month', TD['visits_month']), I('br', 'Average bill rate per hour', TD['br'], 'money')], [
  O('Minutes worked', 'num', '%s*60' % i('wh')), O('Minutes billed, rounded to the nearest step', 'int', 'ROUND(%s*60/%s,0)*%s' % (i('wh'), i('step'), i('step'))), O('Minutes billed, always rounded up', 'int', 'ROUNDUP(%s*60/%s,0)*%s' % (i('wh'), i('step'), i('step'))),
  O('Nearest step: minutes gained (+) or lost (-) a visit', 'num', 'ROUND(%s*60/%s,0)*%s-%s*60' % (i('wh'), i('step'), i('step'), i('wh'))), O('Round up: minutes gained a visit', 'num', 'ROUNDUP(%s*60/%s,0)*%s-%s*60' % (i('wh'), i('step'), i('step'), i('wh'))),
  O('Nearest step: money a month', 'money', '(ROUND(%s*60/%s,0)*%s-%s*60)/60*%s*%s' % (i('wh'), i('step'), i('step'), i('wh'), i('vis'), i('br'))),
  O('Round up: money a month', 'money', '(ROUNDUP(%s*60/%s,0)*%s-%s*60)/60*%s*%s' % (i('wh'), i('step'), i('step'), i('wh'), i('vis'), i('br'))),
  O('Round up: money a year', 'money', '12*(ROUNDUP(%s*60/%s,0)*%s-%s*60)/60*%s*%s' % (i('wh'), i('step'), i('step'), i('wh'), i('vis'), i('br'))),
  O('Verdict for the nearest-step rule', 'text', 'IF(ROUND(%s*60/%s,0)*%s>=%s*60,%s,%s)' % (i('wh'), i('step'), i('step'), i('wh'), vd('Rounds in your favour'), vd('Rounds against you')))],
  GR('Step sensitivity', ('Step 5 minutes', {'step': 5}), ('Step 10 minutes', {'step': 10}), ('Step 15 minutes', {'step': 15}), ('Step 30 minutes', {'step': 30}), ('Visit of 2.5 hours, step 15', {'wh': 2.5, 'step': 15}))),
 # 13 missed visit cost
 TOOL('missed_cost', 'Missed Visit Cost', 'Missed visit cost: what missed visits cost a month',
  'Type the missed visits in a month, the charge lost, the cover cost and the goodwill credit for each, and the visits; see the monthly cost, the cost per 100 visits, the saving at your target and a verdict On target, Watch or Act.', [
  I('mv', 'Missed visits a month', TD['m1'][2]), I('vis', 'Visits a month', TD['m1'][0]), I('lost', 'Charge lost per missed visit', TD['charge_visit'], 'money'), I('cover', 'Cover cost per missed visit', 24, 'money'), I('good', 'Goodwill credit per missed visit', 20, 'money')], [
  O('Missed visits per 100 visits', 'num', '100*%s/%s' % (i('mv'), i('vis'))), O('Charge lost a month', 'money', '%s*%s' % (i('mv'), i('lost'))), O('Cover cost a month', 'money', '%s*%s' % (i('mv'), i('cover'))),
  O('Goodwill credits a month', 'money', '%s*%s' % (i('mv'), i('good'))), O('Cost a month', 'money', '%s*(%s+%s+%s)' % (i('mv'), i('lost'), i('cover'), i('good'))), O('Cost per missed visit', 'money', '%s+%s+%s' % (i('lost'), i('cover'), i('good'))),
  O('Cost per 100 visits', 'money', '100*%s*(%s+%s+%s)/%s' % (i('mv'), i('lost'), i('cover'), i('good'), i('vis'))), O('Cost a year', 'money', '12*%s*(%s+%s+%s)' % (i('mv'), i('lost'), i('cover'), i('good'))),
  O('Cost a month at the missed-visit target', 'money', '%s*{set:missed_visit_target}*(%s+%s+%s)' % (i('vis'), i('lost'), i('cover'), i('good'))),
  O('Saving a month at the target', 'money', 'MAX(0,%s-%s*{set:missed_visit_target})*(%s+%s+%s)' % (i('mv'), i('vis'), i('lost'), i('cover'), i('good'))),
  O('Verdict', 'text', VERD3('%s/%s' % (i('mv'), i('vis')), '{set:missed_visit_target}', '1.5*{set:missed_visit_target}'))],
  GR('What if', ('Missed visits halved', {'mv': '=ROUND(%s/2,0)' % i('mv')}), ('At the target rate', {'mv': '=ROUND(%s*{set:missed_visit_target},0)' % i('vis')}), ('Cover found faster, cost 12', {'cover': 12}), ('No goodwill credit', {'good': 0}))),
 # 14 overlong
 TOOL('overlong_review', 'Overlong Visit Review', 'Overlong visit review: bill the extra or change the schedule',
  'Type the extra minutes of a typical overlong visit, how many a month, the share not billed and the bill rate; see the money lost a year and the verdict Bill the extra or Change the schedule.', [
  I('em', 'Extra minutes on a typical overlong visit', TD['over'][0]), I('cnt', 'Overlong visits a month', TD['over'][1]), I('share', 'Share of the extra time not billed', TD['over'][2], 'pct'), I('br', 'Bill rate per hour', TD['br'], 'money')], [
  O('Extra hours a month', 'num', '%s*%s/60' % (i('em'), i('cnt'))), O('Value of the extra hours a month', 'money', '%s*%s/60*%s' % (i('em'), i('cnt'), i('br'))), O('Money lost a month', 'money', '%s*%s/60*%s*%s' % (i('em'), i('cnt'), i('br'), i('share'))),
  O('Money lost a year', 'money', '12*%s*%s/60*%s*%s' % (i('em'), i('cnt'), i('br'), i('share'))), O('Overlong minutes limit', 'int', '{set:overlong_minutes}'), O('Care hours to add to the schedule a week', 'num', '%s*%s/60/4.33' % (i('em'), i('cnt'))),
  O('Verdict', 'text', 'IF(%s>={set:overlong_minutes},%s,%s)' % (i('em'), vd('Change the schedule'), vd('Bill the extra')))],
  GR('What if', ('Extra of 10 minutes', {'em': 10}), ('All extra time billed', {'share': 0}), ('Twice as many visits', {'cnt': '=%s*2' % i('cnt')}), ('Extra of 30 minutes', {'em': 30}))),
 # 15 check-in compliance
 TOOL('checkin_compliance', 'Check-in Compliance', 'Check-in compliance: check-ins and check-outs recorded',
  'Type the visits that should have a check-in and check-out, and how many have each; see the shares, the visits to correct and a verdict against your target. The check-ins are typed or pasted, there is no app or GPS.', [
  I('vis', 'Visits that should have check-in and check-out', TD['chk'][0]), I('cin', 'Visits with a check-in recorded', TD['chk'][1]), I('cout', 'Visits with a check-out recorded', TD['chk'][2])], [
  O('Check-in recorded', 'pct', '%s/%s' % (i('cin'), i('vis'))), O('Check-out recorded', 'pct', '%s/%s' % (i('cout'), i('vis'))), O('Both recorded (lowest of the two)', 'pct', 'MIN(%s,%s)/%s' % (i('cin'), i('cout'), i('vis'))),
  O('Target share', 'pct', '{set:checkin_target}'), O('Visits to correct', 'int', '%s-MIN(%s,%s)' % (i('vis'), i('cin'), i('cout'))), O('Visits that may be added before the share falls below target', 'int', 'MAX(0,ROUNDDOWN(MIN(%s,%s)/{set:checkin_target}-%s,0))' % (i('cin'), i('cout'), i('vis'))),
  O('Verdict', 'text', 'IF(MIN(%s,%s)/%s>={set:checkin_target},%s,IF(MIN(%s,%s)/%s>={set:checkin_target}-0.03,%s,%s))' % (i('cin'), i('cout'), i('vis'), vd('On target'), i('cin'), i('cout'), i('vis'), vd('Watch'), vd('Act')))],
  GR('What if', ('Ten check-outs missing', {'cout': '=%s-10' % i('vis')}), ('Twenty check-ins missing', {'cin': '=%s-20' % i('vis')}), ('All recorded', {'cin': '=%s' % i('vis'), 'cout': '=%s' % i('vis')}))),
 # 16 mileage rate test
 TOOL('mileage_rate', 'Mileage Rate Test', 'Mileage rate test: what a new rate per km costs',
  'Type the kilometres a month, the rate now and the new rate, the visits, and the paid travel and caregiver pay of a month; see the monthly cost, the change, the cost per visit and whether travel stays within its share of pay.', [
  I('km', 'Kilometres a month', TD['mr'][0], 'num'), I('now', 'Rate per km now', 0.40, 'money'), I('new', 'New rate per km', 0.45, 'money'), I('vis', 'Visits a month', TD['mr'][1]), I('tp', 'Paid travel time a month', TD['mr'][2], 'money'),
  I('pay', 'Caregiver pay a month', TD['mr'][3], 'money')], [
  O('Mileage cost a month now', 'money', '%s*%s' % (i('km'), i('now'))), O('Mileage cost a month at the new rate', 'money', '%s*%s' % (i('km'), i('new'))), O('Change a month', 'money', '%s*(%s-%s)' % (i('km'), i('new'), i('now'))),
  O('Change a year', 'money', '12*%s*(%s-%s)' % (i('km'), i('new'), i('now'))), O('Mileage cost per visit now', 'money', '%s*%s/%s' % (i('km'), i('now'), i('vis'))), O('Mileage cost per visit at the new rate', 'money', '%s*%s/%s' % (i('km'), i('new'), i('vis'))),
  O('Travel cost as a share of pay now', 'pct', '(%s+%s*%s)/%s' % (i('tp'), i('km'), i('now'), i('pay'))), O('Travel cost as a share of pay at the new rate', 'pct', '(%s+%s*%s)/%s' % (i('tp'), i('km'), i('new'), i('pay'))),
  O('Verdict', 'text', VERD3('(%s+%s*%s)/%s' % (i('tp'), i('km'), i('new'), i('pay')), '{set:travel_share_target}', '1.25*{set:travel_share_target}'))],
  GR('What if', ('Rate 0.50', {'new': 0.5}), ('Rate 0.60', {'new': 0.6}), ('Kilometres cut by 10% by clustering', {'km': '=%s*0.9' % i('km')}), ('Rate unchanged', {'new': '=%s' % i('now')}))),
 # 17 late rate comparison
 TOOL('late_comparison', 'Late Rate Comparison', 'Late rate comparison: now, 3 months, last year',
  'Type the visits and late visits of this month so far, of the last three full months together and of the same month last year; see the rates, the change in points and a verdict Better than last year, Watch or Worse than last year.', [
  I('v0', 'Visits this month so far', TD['cmp'][0]), I('l0', 'Late visits this month so far', TD['cmp'][1]), I('v3', 'Visits, last 3 full months', TD['cmp'][2]), I('l3', 'Late visits, last 3 full months', TD['cmp'][3]),
  I('vy', 'Visits, same month last year', TD['cmp'][4]), I('ly', 'Late visits, same month last year', TD['cmp'][5])], [
  O('Late rate this month', 'pct', '%s/%s' % (i('l0'), i('v0'))), O('Late rate, last 3 months', 'pct', '%s/%s' % (i('l3'), i('v3'))), O('Late rate, same month last year', 'pct', '%s/%s' % (i('ly'), i('vy'))), O('Target late rate', 'pct', '{set:late_visit_target}'),
  O('Change against the last 3 months (points)', 'num', '100*(%s/%s-%s/%s)' % (i('l0'), i('v0'), i('l3'), i('v3'))), O('Change against last year (points)', 'num', '100*(%s/%s-%s/%s)' % (i('l0'), i('v0'), i('ly'), i('vy'))),
  O('Late visits this month at last year\'s rate', 'num', '%s*%s/%s' % (i('v0'), i('ly'), i('vy'))), O('Late visits above the target so far', 'num', 'MAX(0,%s-%s*{set:late_visit_target})' % (i('l0'), i('v0'))),
  O('Verdict', 'text', 'IF(%s/%s<=%s/%s-0.005,%s,IF(%s/%s>=%s/%s+0.005,%s,%s))' % (i('l0'), i('v0'), i('ly'), i('vy'), vd('Better than last year'), i('l0'), i('v0'), i('ly'), i('vy'), vd('Worse than last year'), vd('Watch')))],
  GR('What if', ('Rest of the month with no late visits', {'l0': '=%s' % i('l0'), 'v0': '=%s*2' % i('v0')}), ('Late visits at the target', {'l0': '=ROUND(%s*{set:late_visit_target},0)' % i('v0')}), ('Late visits at last year\'s rate', {'l0': '=ROUND(%s*%s/%s,0)' % (i('v0'), i('ly'), i('vy'))}))),
 # 18 what-if grid
 TOOL('travel_grid', 'Travel What-if Grid', 'What-if grid: travel minutes against visits',
  'Type the paid travel minutes per visit, the visits per day and the days a month; see the monthly travel cost, and read the grid for other minutes and volumes. Each grid row is a scenario of minutes per visit and visits per day.', [
  I('tm', 'Paid travel minutes per visit', TD['wi'][0], 'num'), I('vpd', 'Visits per day', TD['wi'][1]), I('days', 'Days a month', 30), I('pr', 'Pay rate per hour', TD['pr'], 'money'), I('km', 'Kilometres per visit', TD['wi'][2], 'num')], [
  O('Paid travel hours a month', 'num', '%s*%s*%s/60' % (i('tm'), i('vpd'), i('days'))), O('Paid travel pay a month', 'money', '%s*%s*%s/60*%s' % (i('tm'), i('vpd'), i('days'), i('pr'))),
  O('Payroll burden on the travel pay', 'money', '%s*%s*%s/60*%s*{set:payroll_burden}' % (i('tm'), i('vpd'), i('days'), i('pr'))), O('Mileage a month', 'money', '%s*%s*%s*{set:mileage_rate}' % (i('km'), i('vpd'), i('days'))),
  O('Travel cost a month in total', 'money', '%s*%s*(%s/60*%s*%s+%s*{set:mileage_rate})' % (i('vpd'), i('days'), i('tm'), i('pr'), B, i('km'))), O('Travel cost per visit', 'money', '%s/60*%s*%s+%s*{set:mileage_rate}' % (i('tm'), i('pr'), B, i('km'))),
  O('Cost a month if each visit needs 2 minutes less', 'money', '%s*%s*((%s-2)/60*%s*%s+%s*{set:mileage_rate})' % (i('vpd'), i('days'), i('tm'), i('pr'), B, i('km'))),
  O('Cost a month if each visit needs 2 minutes more', 'money', '%s*%s*((%s+2)/60*%s*%s+%s*{set:mileage_rate})' % (i('vpd'), i('days'), i('tm'), i('pr'), B, i('km'))),
  O('Cost a year in total', 'money', '12*%s*%s*(%s/60*%s*%s+%s*{set:mileage_rate})' % (i('vpd'), i('days'), i('tm'), i('pr'), B, i('km')))],
  GR('Minutes per visit against visits per day', ('4 minutes, 30 visits', {'tm': 4, 'vpd': 30}), ('4 minutes, 36 visits', {'tm': 4, 'vpd': 36}), ('4 minutes, 42 visits', {'tm': 4, 'vpd': 42}), ('6.4 minutes, 30 visits', {'tm': 6.4, 'vpd': 30}),
     ('6.4 minutes, 36 visits', {'tm': 6.4, 'vpd': 36}), ('6.4 minutes, 42 visits', {'tm': 6.4, 'vpd': 42}), ('9 minutes, 30 visits', {'tm': 9, 'vpd': 30}), ('9 minutes, 36 visits', {'tm': 9, 'vpd': 36}), ('9 minutes, 42 visits', {'tm': 9, 'vpd': 42}),
     ('12 minutes, 36 visits', {'tm': 12, 'vpd': 36}))),
]
assert len(tools) == 18
