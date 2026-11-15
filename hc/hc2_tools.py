"""Home care suite part 2: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc2_lists import *

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
YES = '{list:yesno.yes}'
BURD = '(1+{set:payroll_burden})'
AVGPAY = 'AVERAGEIFS({range:caregivers.pay_rate},{range:caregivers.status},%s)' % tok('cgstatus', 'Active')
CURW = '({today}-WEEKDAY({today},2)+1)'
MSTART = 'DATE(YEAR({today}),MONTH({today}),1)'
def cgr(c): return '{range:caregivers.%s}' % c
def WT(i): return 'INDEX({range:match_weights.weight},%d)' % i

# ---- 1 weekly schedule checker
LIM1 = 'IFERROR(INDEX(%s,MATCH({in:cg},%s,0)),{set:overtime_hours})' % (cgr('hours_limit'), cgr('name'))
PAY1 = 'IFERROR(INDEX(%s,MATCH({in:cg},%s,0)),0)' % (cgr('pay_rate'), cgr('name'))
TOT1 = '({in:booked}+{in:add})'
OT1 = 'MAX(0,%s-{set:overtime_hours})' % TOT1
t1 = TOOL('sched_check', 'Weekly Schedule Checker', 'Can this caregiver take one more visit this week?',
  'Type the caregiver, the hours already booked, the visit hours to add and the days already worked; see the new total against the overtime line and the own limit, the days off left and a verdict.', [
  I('cg', 'Caregiver (name as in Caregivers)', 'Amara Okonkwo', 'text'), I('booked', 'Hours already booked that week', 36, 'num'), I('add', 'Visit hours to add', 6, 'num'), I('days', 'Days already worked that week', 4),
  I('same', 'The visit is on a day already worked (1 yes, 0 no)', 0)], [
  O('Weekly limit of this caregiver, hours', 'int', LIM1), O('Pay rate per hour', 'money', PAY1), O('New weekly total, hours', 'num', TOT1), O('Hours left to the overtime line (negative is over)', 'num', '{set:overtime_hours}-%s' % TOT1),
  O('Overtime hours', 'num', OT1), O('Overtime extra cost with payroll burden', 'money', 'ROUND(%s*%s*({set:overtime_mult}-1)*%s,2)' % (OT1, PAY1, BURD)),
  O('Free hours under the own limit (negative is over)', 'num', '%s-%s' % (LIM1, TOT1)), O('Days worked after this visit', 'int', '{in:days}+1-{in:same}'), O('Days off left in the week', 'int', '7-({in:days}+1-{in:same})'),
  O('Verdict', 'text', 'IF(%s>{set:overtime_hours},%s,IF(%s>%s,%s,%s))' % (TOT1, vd('Overtime'), TOT1, LIM1, vd('Over limit'), vd('Safe')))],
  GR('What if', ('Add 2 hours instead', {'add': 2}), ('Add 4 hours', {'add': 4}), ('Add 10 hours', {'add': 10}), ('Only 20 hours booked', {'booked': 20, 'add': 6}), ('Sixth day in a row', {'days': 5, 'same': 0}), ('Same day as another visit', {'same': 1})))

# ---- 2 open shift filler (ranked candidates)
SV_, AR_, LG_, D_, S_, H_ = '{in:sv}', '{in:ar}', '{in:lg}', '{in:sdate}', '{in:shour}', '{in:shrs}'
WK2 = '(%s-WEEKDAY(%s,2)+1)' % (D_, D_)
LIM = cgr('hours_limit')
BOOK2 = 'SUMIFS({range:grid_cg.scheduled_hours},{range:grid_cg.caregiver_id},%s,{range:grid_cg.week},%s)' % (cgr('caregiver_id'), WK2)
SK2 = '((%s)>0)' % '+'.join('(%s=%s)' % (cgr('skill_%d' % i), SV_) for i in range(1, 6))
LG2 = '(((%s=%s)+(%s=%s))>0)' % (cgr('language_1'), LG_, cgr('language_2'), LG_)
AREA2 = '((%s=%s)*100+(%s<>%s)*(100-2*SUMIFS({range:travel.minutes},{range:travel.from_area},%s,{range:travel.to_area},%s)))' % (cgr('area'), AR_, cgr('area'), AR_, cgr('area'), AR_)
WE2, NI2, EV2 = 'IF(WEEKDAY(%s,2)>=6,1,0)' % D_, 'IF(OR(%s>=21,%s<6),1,0)' % (S_, S_), 'IF(AND(%s>=17,%s<21),1,0)' % (S_, S_)
AV = cgr('availability')
AVF = '((%s=%s)+(%s=%s)*(1-%s)*(1-%s)*(1-%s)+(%s=%s)*(1-%s)*(1-%s)+(%s=%s)*(%s*(1-%s)+(1-%s)*%s)+(%s=%s)*MIN(1,%s+%s))' % (
    AV, tok('avail', 'Any time'), AV, tok('avail', 'Weekdays'), WE2, EV2, NI2, AV, tok('avail', 'Weekdays and evenings'), WE2, NI2, AV, tok('avail', 'Weekends and evenings'), WE2, NI2, WE2, EV2,
    AV, tok('avail', 'Nights and weekends'), NI2, WE2)
ELIG2 = '(%s=%s)*%s*(%s+%s<=%s)*(%s>0)' % (cgr('status'), tok('cgstatus', 'Active'), SK2, BOOK2, H_, LIM, AVF)
SCORE2 = '(%s*100+%s*%s+%s*(30+70*%s)+%s*100*%s+%s*100*(1-%s/(%s+(%s=0))))/(SUM({range:match_weights.weight})-%s)' % (WT(1), WT(2), AREA2, WT(3), LG2, WT(4), AVF, WT(6), BOOK2, LIM, LIM, WT(5))
KEYV = '%s*(ROUND(%s,0)*100000+ROUND(%s-%s,0)*1000+(999-%s))' % (ELIG2, SCORE2, LIM, BOOK2, cgr('seq'))
def KN(n): return 'SUMPRODUCT(LARGE(%s,%d))' % (KEYV, n)
def POS(n): return 'MATCH(999-MOD(%s,1000),%s,0)' % (KN(n), cgr('seq'))
def cand_outs(n):
    return [O('Candidate %d: name' % n, 'text', 'IFERROR(INDEX(%s,%s),"")' % (cgr('name'), POS(n))), O('Candidate %d: match score' % n, 'int', 'INT(%s/100000)' % KN(n)),
            O('Candidate %d: free hours that week' % n, 'int', 'MOD(INT(%s/1000),100)' % KN(n)),
            O('Candidate %d: travel minutes to the client area' % n, 'int', 'IFERROR(SUMIFS({range:travel.minutes},{range:travel.from_area},INDEX(%s,%s),{range:travel.to_area},%s),0)' % (cgr('area'), POS(n), AR_))]
t2 = TOOL('shift_filler', 'Open Shift Filler', 'Who should I phone first for this open shift?',
  'Type the day, start hour, hours, area, service and language; the caregivers table, their booked hours that week, the match weights and the travel times rank the three best caregivers and give a verdict.', [
  I('sdate', 'Shift date', 'today+1', 'date'), I('shour', 'Start hour, 24-hour clock (9.5 is 09:30)', 9, 'num'), I('shrs', 'Shift hours', 4, 'num'), IL('ar', 'Client area', 'area', 'East Park'), IL('sv', 'Service', 'svc', 'Companion care'),
  IL('lg', 'Language wanted', 'lang', 'English')], cand_outs(1) + cand_outs(2) + cand_outs(3) + [
  O('Candidate 1: phone', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (cgr('phone'), POS(1))),
  O('Verdict', 'text', 'IF(%s<=0,%s,%s)' % (KN(1), vd('No one is free'), vd('Phone first')))],
  GR('What if', ('Evening start at 18:00', {'shour': 18}), ('Night start at 21:00', {'shour': 21, 'shrs': 10}), ('Long shift of 8 hours', {'shrs': 8}), ('South Valley area', {'ar': '=' + tok('area', 'South Valley')}),
     ('Respite care, 3 hours', {'sv': '=' + tok('svc', 'Respite care'), 'shrs': 3}), ('Polish speaking client', {'lg': '=' + tok('lang', 'Polish')})))

# ---- 3 cover option cost
BASE3 = '({in:shift}+{in:trav}/60)*{in:pay}*%s' % BURD
OTH3 = 'MAX(0,MIN({in:shift},{in:booked}+{in:shift}-{set:overtime_hours}))'
OTX3 = '%s*{in:pay}*({set:overtime_mult}-1)*%s' % (OTH3, BURD)
PREM3 = 'IF({in:notice}<{set:short_notice_hours},{in:shift}*{in:prem},0)'
COST_OT3 = 'ROUND(%s+%s+%s,2)' % (BASE3, OTX3, PREM3); COST_PR3 = 'ROUND(%s+{in:shift}*{in:prem},2)' % BASE3
t3 = TOOL('cover_cost', 'Cover Option Cost', 'What does this cover cost: regular hours, overtime or the premium?',
  'Type the candidate pay rate, hours already booked, shift hours, travel minutes, notice hours and the cover premium; see the cost of each option and the cheapest one. Payroll burden is payroll taxes, workers\' insurance and benefits on top of pay (confirm with your adviser).', [
  I('pay', 'Candidate pay rate per hour', 19, 'num'), I('booked', 'Hours already booked that week', 38, 'num'), I('shift', 'Shift hours', 6, 'num'), I('trav', 'Paid travel minutes', 25), I('notice', 'Notice, hours before the visit', 8),
  I('prem', 'Cover premium per hour', 3, 'money')], [
  O('Cost as regular hours (pay, travel and burden)', 'money', 'ROUND(%s,2)' % BASE3), O('Overtime hours if this caregiver takes it', 'num', OTH3), O('Overtime extra cost', 'money', 'ROUND(%s,2)' % OTX3),
  O('Short-notice premium owed', 'money', 'ROUND(%s,2)' % PREM3), O('Cost with overtime and any premium', 'money', COST_OT3), O('Cost with another caregiver under the line and the premium', 'money', COST_PR3),
  O('Cheapest cost', 'money', 'IF(%s=0,ROUND(%s+%s,2),MIN(%s,%s))' % (OTH3, BASE3, PREM3, COST_OT3, COST_PR3)),
  O('Cheapest cost per visit hour', 'money', 'ROUND(IF(%s=0,%s+%s,MIN(%s,%s))/{in:shift},2)' % (OTH3, BASE3, PREM3, COST_OT3, COST_PR3)),
  O('Verdict', 'text', 'IF(%s=0,IF({in:notice}>={set:short_notice_hours},%s,%s),IF(%s<=%s,%s,%s))' % (OTH3, vd('Use regular hours'), vd('Pay the premium'), COST_OT3, COST_PR3, vd('Use overtime'), vd('Pay the premium')))],
  GR('What if', ('Only 20 hours booked, 48 hours notice', {'booked': 20, 'notice': 48}), ('Only 20 hours booked, 6 hours notice', {'booked': 20, 'notice': 6}), ('Premium of 5', {'prem': 5}), ('Higher pay rate 21', {'pay': 21}),
     ('Longer travel, 45 minutes', {'trav': 45}), ('Short shift of 3 hours', {'shift': 3})))

# ---- 4 matching score calculator
HP4 = 'MAX(0,ROUND(100*(1-{in:booked}/{in:limit}),0))'
PTS = ['{in:sk}', '{in:ar}', '{in:lg}', '{in:av}', '100*{in:pref}', HP4]
SCORE4 = 'ROUND((%s)/SUM({range:match_weights.weight}),0)' % '+'.join('%s*%s' % (WT(i + 1), PTS[i]) for i in range(6))
LOSS = ['%s*(100-%s)' % (WT(i + 1), PTS[i]) for i in range(6)]
MAXL = 'MAX(%s)' % ','.join(LOSS)
WEAK4 = 'IF(%s=%s,INDEX({range:match_weights.factor},1),IF(%s=%s,INDEX({range:match_weights.factor},2),IF(%s=%s,INDEX({range:match_weights.factor},3),IF(%s=%s,INDEX({range:match_weights.factor},4),IF(%s=%s,INDEX({range:match_weights.factor},5),INDEX({range:match_weights.factor},6))))))' % (
    LOSS[0], MAXL, LOSS[1], MAXL, LOSS[2], MAXL, LOSS[3], MAXL, LOSS[4], MAXL)
t4 = TOOL('match_calc', 'Matching Score', 'How well does this caregiver fit this client?',
  'Type the points (0 to 100) for skills, area, language and availability, whether the client prefers the caregiver, and the hours booked against the limit; your weights from Match Weights give the score, the weakest factor and a verdict. Use the grid to compare candidates A to E.', [
  I('sk', 'Skills points (0 to 100)', 100), I('ar', 'Area points (0 to 100)', 80), I('lg', 'Language points (0 to 100)', 100), I('av', 'Availability points (0 to 100)', 100), I('pref', 'Preferred by the client (1 yes, 0 no)', 0),
  I('booked', 'Hours booked that week', 30, 'num'), I('limit', 'Weekly limit, hours', 40, 'num'), I('strong', 'Strong match from this score', 75), I('poss', 'Possible match from this score', 55)], [
  O('Hours points (free hours share)', 'int', HP4), O('Match score out of 100', 'int', SCORE4), O('Weakest factor', 'text', WEAK4), O('Points lost to the weakest factor', 'num', 'ROUND(%s/SUM({range:match_weights.weight}),1)' % MAXL),
  O('Score if the weakest factor were perfect', 'int', 'MIN(100,%s+ROUND(%s/SUM({range:match_weights.weight}),0))' % (SCORE4, MAXL)),
  O('Verdict', 'text', 'IF(%s>={in:strong},%s,IF(%s>={in:poss},%s,%s))' % (SCORE4, vd('Strong match'), SCORE4, vd('Possible match'), vd('Weak match')))],
  GR('Five candidates', ('A: same area, English, free', {'sk': 100, 'ar': 100, 'lg': 100, 'av': 100, 'booked': 20}), ('B: nearby, wrong language', {'ar': 70, 'lg': 30, 'av': 100, 'booked': 28}), ('C: far away, preferred', {'ar': 40, 'pref': 1, 'booked': 36}),
     ('D: part of the window free', {'av': 50, 'ar': 90, 'booked': 18}), ('E: lacks the skill', {'sk': 0, 'ar': 100, 'booked': 10})))

# ---- 5 continuity index
SH5 = '({in:main}/{in:total})'
t5 = TOOL('cont_index', 'Continuity Index', 'Is this client seeing too many different caregivers?',
  'Type the different caregivers a client saw in 28 days, the hours by the main caregiver, all hours and the limit; see the main share, an index out of 100 and a verdict. Continuity means how few different caregivers a client sees.', [
  I('seen', 'Different caregivers in 28 days', 5), I('main', 'Hours by the main caregiver', 22, 'num'), I('total', 'All hours in 28 days', 40, 'num'), I('limit', 'Most caregivers allowed in 28 days', 3), I('want', 'Wanted main caregiver share', 0.7, 'pct')], [
  O('Main caregiver share', 'pct', SH5), O('Continuity index (0 to 100)', 'int', 'ROUND(100*%s*MIN(1,{in:limit}/{in:seen}),0)' % SH5), O('Caregivers over the limit', 'int', 'MAX(0,{in:seen}-{in:limit})'),
  O('Hours the main caregiver needs for the wanted share', 'num', 'ROUND({in:want}*{in:total},1)'), O('Extra hours to move to the main caregiver', 'num', 'MAX(0,ROUND({in:want}*{in:total}-{in:main},1))'),
  O('Agency average caregivers per client, last 28 days', 'num', 'ROUND(AVERAGE({range:continuity.caregivers_28d}),1)'),
  O('Agency main caregiver share, last 28 days', 'pct', 'SUM({range:continuity.main_hours})/SUM({range:continuity.hours})'),
  O('Verdict', 'text', 'IF({in:seen}<={in:limit},%s,IF({in:seen}<={in:limit}+2,%s,%s))' % (ck('Steady'), ck('Watch'), ck('Break')))],
  GR('What if', ('Two caregivers', {'seen': 2, 'main': 30}), ('Three caregivers', {'seen': 3, 'main': 28}), ('Four caregivers', {'seen': 4, 'main': 24}), ('Six caregivers', {'seen': 6, 'main': 12}), ('Ten caregivers', {'seen': 10, 'main': 8})))

# ---- 6 call-off response plan
ARM6 = 'IFERROR(AVERAGEIFS({range:calloffs.minutes_to_cover},{range:calloffs.area},{in:ar},{range:calloffs.covered},%s,{range:calloffs.date},">="&({today}-90)),0)' % YES
ALL6 = 'IFERROR(AVERAGEIFS({range:calloffs.minutes_to_cover},{range:calloffs.covered},%s,{range:calloffs.date},">="&({today}-90)),0)' % YES
HIST6 = 'IF(%s>0,%s,%s)' % (ARM6, ARM6, ALL6)
EXP6 = 'ROUND(%s*MIN(2,MAX(0.5,3/MAX(1,{in:cands}))),0)' % HIST6
BOOK6 = 'SUMIFS({range:grid_cg.scheduled_hours},{range:grid_cg.caregiver_id},%s,{range:grid_cg.week},{today}-WEEKDAY({today},2)+8)' % cgr('caregiver_id')
KEY6 = '(%s=%s)*(%s=%s)*(%s-%s>0)*(ROUND(%s-%s,0)*1000+(999-%s))' % (cgr('status'), tok('cgstatus', 'Active'), cgr('area'), AR_.replace('{in:ar}', '{in:ar}'), LIM, BOOK6, LIM, BOOK6, cgr('seq'))
K6 = 'SUMPRODUCT(LARGE(%s,1))' % KEY6
PREM6 = 'IF({in:left}<{set:short_notice_hours},{in:vh}*{set:cover_premium},0)'
TRV6 = 'IFERROR(INDEX({range:areas.avg_travel_min},MATCH({in:ar},{range:areas.area},0)),0)/60*%s*%s' % (AVGPAY, BURD)
t6 = TOOL('calloff_plan', 'Call-off Response Plan', 'A caregiver called off: how fast can I find cover, and what will it cost?',
  'Type the hours left to the visit, the caregivers free, the area and the visit hours; your own last 90 days give the expected minutes to find cover, the time left, the extra cost and who to phone first.', [
  I('left', 'Hours left until the visit', 5), I('cands', 'Caregivers free to ask', 3), IL('ar', 'Client area', 'area', 'South Valley'), I('vh', 'Visit hours', 4, 'num')], [
  O('Your average minutes to find cover in this area, last 90 days', 'int', 'ROUND(%s,0)' % HIST6), O('Expected minutes to find cover with these caregivers free', 'int', EXP6),
  O('Minutes left after finding cover', 'int', '{in:left}*60-%s' % EXP6), O('Short-notice premium', 'money', 'ROUND(%s,2)' % PREM6), O('Paid travel cost to the client area', 'money', 'ROUND(%s,2)' % TRV6),
  O('Extra cost of cover', 'money', 'ROUND(%s+%s,2)' % (PREM6, TRV6)),
  O('Phone first: caregiver with most free hours next week in the area', 'text', 'IFERROR(INDEX(%s,MATCH(999-MOD(%s,1000),%s,0)),"")' % (cgr('name'), K6, cgr('seq'))),
  O('Free hours next week of that caregiver', 'int', 'MOD(INT(%s/1000),1000)' % K6), O('Phone of that caregiver', 'text', 'IFERROR(INDEX(%s,MATCH(999-MOD(%s,1000),%s,0))&"","")' % (cgr('phone'), K6, cgr('seq'))),
  O('Verdict', 'text', 'IF(%s<=0,%s,IF({in:left}*60-%s<0,%s,%s))' % (K6, vd('No one is free'), EXP6, vd('Cover is tight'), vd('Phone now')))],
  GR('What if', ('Only 1 hour left', {'left': 1}), ('Ten hours left', {'left': 10}), ('One caregiver free', {'cands': 1}), ('Six caregivers free', {'cands': 6}), ('Overnight visit of 10 hours', {'vh': 10}), ('East Park area', {'ar': '=' + tok('area', 'East Park')})))

# ---- 7 call-off rate per caregiver
CO90 = 'COUNTIFS({range:calloffs.date},">="&(%s-91),{range:calloffs.date},"<"&%s)' % (CURW, CURW)
SH90 = 'SUMIFS({range:fill_week.visits},{range:fill_week.week},">="&(%s-91),{range:fill_week.week},"<"&%s)' % (CURW, CURW)
AG7 = '(100*%s/%s)' % (CO90, SH90)
t7 = TOOL('calloff_rate', 'Call-off Rate Check', 'Does this caregiver call off more than the agency?',
  'Type the call-offs and the scheduled shifts of one caregiver; see the rate per 100 shifts against the agency rate of the last 13 weeks and a verdict. A call-off means a caregiver cannot come.', [
  I('co', 'Call-offs of this caregiver', 4), I('sh', 'Scheduled shifts in the same period', 60)], [
  O('Rate per 100 shifts', 'num', 'ROUND(100*{in:co}/{in:sh},1)'), O('Agency rate per 100 shifts, last 13 weeks', 'num', 'ROUND(%s,1)' % AG7), O('Times the agency rate', 'num', 'ROUND((100*{in:co}/{in:sh})/%s,2)' % AG7),
  O('Rate that calls for a talk', 'num', 'ROUND(%s*{set:calloff_talk_factor},1)' % AG7), O('Call-offs above the agency rate', 'num', 'ROUND({in:co}-{in:sh}*%s/100,1)' % AG7),
  O('Call-offs in the agency, last 13 weeks', 'int', CO90), O('Verdict', 'text', 'IF(100*{in:co}/{in:sh}>%s*{set:calloff_talk_factor},%s,%s)' % (AG7, vd('Talk'), vd('Normal')))],
  GR('What if', ('1 call-off', {'co': 1}), ('2 call-offs', {'co': 2}), ('3 call-offs', {'co': 3}), ('6 call-offs', {'co': 6}), ('10 call-offs in 100 shifts', {'co': 10, 'sh': 100})))

# ---- 8 cover cost against history
def MCOST(off):
    m = 'DATE(YEAR({today}),MONTH({today})-%d,1)' % off
    return '(SUMIFS({range:cover_month.premium_paid},{range:cover_month.month},%s)+SUMIFS({range:cover_month.overtime_hours},{range:cover_month.month},%s)*%s*({set:overtime_mult}-1)*%s)' % (m, m, AVGPAY, BURD)
AVG3 = '((%s+%s+%s)/3)' % (MCOST(1), MCOST(2), MCOST(3))
t8 = TOOL('cover_history', 'Cover Cost vs History', 'Is cover costing more than usual?',
  'Type this month\'s cover cost (premium plus overtime extra), the 3-month average and the same month last year; see the change and a verdict. The lines below read the same figures from Cover Cost by Month.', [
  I('now', 'Cover cost this month', 470, 'money'), I('avg3', 'Average of the last 3 months', 391, 'money'), I('ly', 'Same month last year', 813, 'money'), I('band', 'Change that counts as up or down', 0.1, 'pct')], [
  O('Change against the 3-month average', 'money', '{in:now}-{in:avg3}'), O('Change against the 3-month average, %', 'pct', 'IF({in:avg3}>0,{in:now}/{in:avg3}-1,0)'), O('Change against last year, %', 'pct', 'IF({in:ly}>0,{in:now}/{in:ly}-1,0)'),
  O('Cover cost this month on your Cover Cost by Month page', 'money', 'ROUND(%s,0)' % MCOST(0)), O('3-month average on your Cover Cost by Month page', 'money', 'ROUND(%s,0)' % AVG3), O('Same month last year on your Cover Cost by Month page', 'money', 'ROUND(%s,0)' % MCOST(12)),
  O('Verdict', 'text', 'IF({in:now}>{in:avg3}*(1+{in:band}),%s,IF({in:now}<{in:avg3}*(1-{in:band}),%s,%s))' % (vd('Cost is up'), vd('Cost is down'), vd('Cost is steady')))],
  GR('What if', ('Cost 10 percent higher', {'now': '={in:now}*1.1'}), ('Cost 25 percent higher', {'now': '={in:now}*1.25'}), ('Cost 20 percent lower', {'now': '={in:now}*0.8'}), ('Wider band of 20 percent', {'band': 0.2})))

# ---- 9 fill rate forecast
TOT9 = '({in:planned}+{in:cover}+{in:unc})'
NEED9 = 'MAX(0,ROUNDUP({set:fill_rate_target}*%s-({in:planned}+{in:cover}),0))' % TOT9
t9 = TOOL('fill_forecast', 'Fill Rate Forecast', 'Will I meet the fill rate in the next 14 days?',
  'Type the planned, cover and uncovered hours for the next 14 days and the free hours one more caregiver can take; see the fill rate against your target, the hours still to find and the caregivers needed.', [
  I('planned', 'Planned hours, next 14 days', 1790, 'num'), I('cover', 'Cover hours, next 14 days', 70, 'num'), I('unc', 'Uncovered hours, next 14 days', 59, 'num'), I('free', 'Free hours one more caregiver can take in 14 days', 12, 'num')], [
  O('Scheduled hours, next 14 days', 'num', TOT9), O('Fill rate', 'pct', '({in:planned}+{in:cover})/%s' % TOT9), O('Wanted fill rate', 'pct', '{set:fill_rate_target}'), O('Hours still to find to reach the target', 'int', NEED9),
  O('Caregivers needed to take those hours', 'int', 'ROUNDUP(%s/{in:free},0)' % NEED9), O('Billing at risk from uncovered hours', 'money', 'ROUND({in:unc}*AVERAGE({range:services.bill_rate}),0)'),
  O('Uncovered hours in your Schedule, next 14 days', 'num', 'SUMIFS({range:schedule.sched_hours},{range:schedule.date},">="&{today},{range:schedule.date},"<"&({today}+14),{range:schedule.cover_type},%s,{range:schedule.status},"<>"&%s)' % (tok('cover', 'Uncovered'), tok('vstatus', 'Cancelled'))),
  O('Verdict', 'text', 'IF(({in:planned}+{in:cover})/%s>={set:fill_rate_target},%s,%s)' % (TOT9, ck('On target'), ck('Below target')))],
  GR('What if', ('Find 20 uncovered hours', {'unc': 39, 'cover': 90}), ('Find 50 uncovered hours', {'unc': 9, 'cover': 120}), ('Cover worsens by 30 hours', {'unc': 89}), ('Each caregiver takes 20 hours', {'free': 20})))

# ---- 10 rest between visits
REST10 = 'MOD({in:nxt}-{in:last},24)'
t10 = TOOL('rest_between', 'Rest Between Visits', 'Does this caregiver get enough rest before the next start?',
  'Type the hour the last visit ends, the hour the next visit starts and the least rest you allow; see the rest hours, the earliest start that keeps the rest and a verdict.', [
  I('last', 'Last visit ends at hour (21.5 is 21:30)', 21.5, 'num'), I('nxt', 'Next visit starts at hour (7 is 07:00)', 7, 'num'), I('minrest', 'Least rest allowed, hours', 10, 'num')], [
  O('Rest hours', 'num', REST10), O('Earliest start that keeps the rest', 'time', 'MOD({in:last}+{in:minrest},24)/24'), O('Hours short of the least rest', 'num', 'MAX(0,{in:minrest}-%s)' % REST10),
  O('Minutes to move the next start', 'int', 'ROUND(MAX(0,{in:minrest}-%s)*60,0)' % REST10), O('Short rests next 14 days in your Rest Check', 'int', 'COUNTIFS({range:rest_check.date},">="&{today},{range:rest_check.date},"<"&({today}+14),{range:rest_check.rest_flag},%s)' % ck('Short rest')),
  O('Verdict', 'text', 'IF(%s<{in:minrest},%s,%s)' % (REST10, ck('Short rest'), ck('Rest kept')))],
  GR('What if', ('Start at 08:00', {'nxt': 8}), ('Start at 09:00', {'nxt': 9}), ('Last visit ends at 19:00', {'last': 19}), ('Overnight ends 07:00, start 17:00', {'last': 7, 'nxt': 17}), ('Rest of 12 hours', {'minrest': 12})))

# ---- 11 days off check
t11 = TOOL('days_off', 'Days Off Check', 'When must this caregiver have a day off?',
  'Type the date the run of days started, the days worked in a row and the most days allowed; see the last day worked, the latest day for a day off and a verdict.', [
  I('start', 'Run of days started on', 'today-4', 'date'), I('days', 'Days worked in a row', 5), I('allowed', 'Most days in a row allowed', 6)], [
  O('Last day worked', 'date', '{in:start}+{in:days}-1'), O('Last day allowed in the run', 'date', '{in:start}+{in:allowed}-1'), O('Days left before the limit', 'int', '{in:allowed}-{in:days}'),
  O('Latest date for a day off', 'date', 'MAX({today},{in:start}+{in:allowed})'), O('Caregivers with no day off next week in your Weekly Grid', 'int', 'COUNTIFS({range:grid_cg.week},%s,{range:grid_cg.days_flag},%s)' % ('({today}-WEEKDAY({today},2)+8)', ck('No day off'))),
  O('Verdict', 'text', 'IF({in:days}>{in:allowed},%s,IF({in:days}={in:allowed},%s,%s))' % (ck('No day off'), ck('Long run'), ck('Day off kept')))],
  GR('What if', ('Four days so far', {'days': 4}), ('Six days so far', {'days': 6}), ('Seven days so far', {'days': 7}), ('Limit of 5 days', {'allowed': 5}), ('Limit of 7 days', {'allowed': 7})))

# ---- 12 schedule posting deadline
t12 = TOOL('post_deadline', 'Posting Deadline', 'Will the schedule be posted far enough ahead?',
  'Type the days posted ahead now, the open shifts left in the days not posted yet and the days to the deadline; see the days still to post and the shifts to fill each day to meet the target.', [
  I('posted', 'Days posted ahead now', 9), I('open', 'Open shifts in the days not posted yet', 14), I('left', 'Days to the posting deadline', 4), I('target', 'Posting target, days ahead', 14)], [
  O('Days still to post', 'int', 'MAX(0,{in:target}-{in:posted})'), O('Schedule posted until', 'date', '{today}+{in:posted}'), O('Target date for the posting', 'date', '{today}+{in:target}'), O('Posting deadline', 'date', '{today}+{in:left}'),
  O('Shifts to fill each day to meet the deadline', 'int', 'ROUNDUP({in:open}/MAX(1,{in:left}),0)'), O('Posted ahead in your Schedule now, days', 'int', 'MAX({range:schedule.date})-{today}'),
  O('Your posting setting, days ahead', 'int', '{set:post_schedule_days}'), O('Verdict', 'text', 'IF({in:posted}>={in:target},%s,%s)' % (vd('On track'), vd('Behind')))],
  GR('What if', ('Posted 14 days ahead', {'posted': 14}), ('Posted 12 days ahead', {'posted': 12}), ('Only 2 days to the deadline', {'left': 2}), ('30 open shifts', {'open': 30}), ('Target of 21 days', {'target': 21})))

# ---- 13 hours balance
FAIR13 = '({in:total}/{in:cgs})'
t13 = TOOL('hours_balance', 'Hours Balance', 'Are hours shared fairly across caregivers?',
  'Type the total hours, the caregivers available, the busiest and the lightest caregiver hours; see the fair share, the spread and a verdict. Evening out hours also lowers overtime.', [
  I('total', 'Total hours next week', 905, 'num'), I('cgs', 'Caregivers available', 36), I('top', 'Hours of the busiest caregiver', 47, 'num'), I('low', 'Hours of the lightest caregiver', 8, 'num'), I('tol', 'Spread allowed, share of the fair share', 0.8, 'pct')], [
  O('Fair share per caregiver, hours', 'num', 'ROUND(%s,1)' % FAIR13), O('Spread between busiest and lightest, hours', 'num', '{in:top}-{in:low}'), O('Busiest against the fair share', 'pct', '{in:top}/%s-1' % FAIR13),
  O('Lightest against the fair share', 'pct', '{in:low}/%s-1' % FAIR13), O('Hours to move from the busiest to the lightest to even out', 'num', 'ROUND(({in:top}-{in:low})/2,1)'),
  O('Caregivers over the overtime line next week in your Weekly Grid', 'int', 'COUNTIFS({range:grid_cg.week},{today}-WEEKDAY({today},2)+8,{range:grid_cg.load_flag},%s)' % ck('Over the line')),
  O('Verdict', 'text', 'IF({in:top}-{in:low}<={in:tol}*%s,%s,%s)' % (FAIR13, vd('Even'), vd('Uneven')))],
  GR('What if', ('Busiest 40, lightest 15', {'top': 40, 'low': 15}), ('Busiest 44, lightest 20', {'top': 44, 'low': 20}), ('Two more caregivers', {'cgs': 38}), ('Fewer caregivers, 30', {'cgs': 30}), ('Wider spread allowed', {'tol': 1.5})))

# ---- 14 standby pool sizing
SB = '({in:co}*{in:share})'
NEED14 = 'ROUNDUP(%s/{in:per},0)' % SB
t14 = TOOL('standby_pool', 'Standby Pool Sizing', 'How many caregivers should be on standby, and what does it cost?',
  'Type the call-offs a week, the hours of a call-off, the share found at short notice, the calls one standby can take a week, the standby fee and the cover premium; see the standby caregivers needed and the weekly cost.', [
  I('co', 'Call-offs a week', 10, 'num'), I('hrs', 'Hours of a call-off', 4, 'num'), I('share', 'Share found at short notice', 0.6, 'pct'), I('per', 'Calls one standby caregiver can take a week', 2), I('fee', 'Standby fee per caregiver per week', 45, 'money'),
  I('prem', 'Cover premium per hour', 3, 'money')], [
  O('Short-notice calls a week', 'num', SB), O('Standby caregivers needed', 'int', NEED14), O('Standby fees a week', 'money', '%s*{in:fee}' % NEED14),
  O('Cover premium a week', 'money', 'ROUND(%s*{in:hrs}*{in:prem},2)' % SB), O('Total weekly cost', 'money', 'ROUND(%s*{in:fee}+%s*{in:hrs}*{in:prem},2)' % (NEED14, SB)),
  O('Cost per call-off', 'money', 'ROUND((%s*{in:fee}+%s*{in:hrs}*{in:prem})/{in:co},2)' % (NEED14, SB)), O('Caregivers on your standby pool now', 'int', 'COUNTIFS({range:caregivers.standby},%s,{range:caregivers.status},%s)' % (YES, tok('cgstatus', 'Active'))),
  O('Verdict', 'text', 'IF(COUNTIFS({range:caregivers.standby},%s,{range:caregivers.status},%s)>=%s,%s,%s)' % (YES, tok('cgstatus', 'Active'), NEED14, vd('Pool is enough'), vd('Add standby')))],
  GR('What if', ('15 call-offs a week', {'co': 15}), ('20 call-offs a week', {'co': 20}), ('30 call-offs a week', {'co': 30}), ('Standbys take 3 calls each', {'per': 3, 'co': 20}), ('Fee of 60', {'fee': 60})))

# ---- 15 free hours finder
GW = '{range:grid_cg.week}'
FREEG = '(%s-%s)' % ('{range:grid_cg.hours_limit}', '{range:grid_cg.scheduled_hours}')
SEQG = 'SUMIFS(%s,%s,{range:grid_cg.caregiver_id})' % (cgr('seq'), cgr('caregiver_id'))
KEY15 = '(%s={in:wk})*({range:grid_cg.area}={in:ar})*(%s>0)*(ROUND(%s*10,0)*1000+(999-%s))' % (GW, FREEG, FREEG, SEQG)
def K15(n): return 'SUMPRODUCT(LARGE(%s,%d))' % (KEY15, n)
def f15(n): return [O('Free hours rank %d: caregiver' % n, 'text', 'IFERROR(INDEX(%s,MATCH(999-MOD(%s,1000),%s,0)),"")' % (cgr('name'), K15(n), cgr('seq'))), O('Free hours rank %d: hours' % n, 'num', 'INT(%s/1000)/10' % K15(n))]
t15 = TOOL('free_hours', 'Free Hours Finder', 'Who has free hours in this area, and is it enough for the waiting visits?',
  'Type the area, the Monday of the week and the hours waiting to be scheduled; Weekly Grid by Caregiver ranks the caregivers with free hours and compares the total with the waiting hours.', [
  IL('ar', 'Area', 'area', 'East Park'), I('wk', 'Monday of the week', 'today+1', 'date'), I('wait', 'Hours waiting to be scheduled', 24, 'num')], [
  O('Free hours in the area that week', 'num', 'SUMIFS({range:grid_cg.free_hours},{range:grid_cg.week},{in:wk},{range:grid_cg.area},{in:ar},{range:grid_cg.free_hours},">0")'),
  O('Caregivers with free hours', 'int', 'COUNTIFS({range:grid_cg.week},{in:wk},{range:grid_cg.area},{in:ar},{range:grid_cg.free_hours},">0")')] + f15(1) + f15(2) + f15(3) + [
  O('Hours short of the waiting hours', 'num', 'MAX(0,{in:wait}-SUMIFS({range:grid_cg.free_hours},{range:grid_cg.week},{in:wk},{range:grid_cg.area},{in:ar},{range:grid_cg.free_hours},">0"))'),
  O('Verdict', 'text', 'IF(SUMIFS({range:grid_cg.free_hours},{range:grid_cg.week},{in:wk},{range:grid_cg.area},{in:ar},{range:grid_cg.free_hours},">0")>={in:wait},%s,%s)' % (vd('Room to take it'), vd('Short of hours')))],
  GR('What if', ('Riverside', {'ar': '=' + tok('area', 'Riverside')}), ('Old Town', {'ar': '=' + tok('area', 'Old Town')}), ('Lakeside', {'ar': '=' + tok('area', 'Lakeside')}), ('60 hours waiting', {'wait': 60}), ('Week after next', {'wk': '={in:wk}+7'})))

# ---- 16 holiday cover planner
PM16 = 'IFERROR(INDEX({range:holidays.pay_mult},MATCH({in:hd},{range:holidays.date},0)),1.5)'
HRS16 = '({in:visits}*{in:vh})'
NEED16 = 'ROUNDUP(%s/{set:day_shift_hours},0)' % HRS16
AV16 = '({in:reg}+{in:vol})'
t16 = TOOL('holiday_planner', 'Holiday Cover Planner', 'Do I have enough caregivers for the holiday?',
  'Type the holiday date, the visits that day, the hours per visit, the caregivers who can work and the volunteers; see the caregivers needed, the shortage and the extra pay and premium. A holiday is a bank holiday or public holiday.', [
  I('hd', 'Holiday date', 'today+39', 'date'), I('visits', 'Visits that day', 38), I('vh', 'Average hours per visit', 3.4, 'num'), I('reg', 'Caregivers who can work that day', 12), I('vol', 'Caregivers volunteering', 3), I('prem', 'Volunteer premium per hour', 4, 'money')], [
  O('Holiday on your Holidays page', 'text', 'IFERROR(INDEX({range:holidays.holiday},MATCH({in:hd},{range:holidays.date},0))&"","")'), O('Pay multiplier for the day', 'num', PM16), O('Care hours to cover', 'num', 'ROUND(%s,1)' % HRS16),
  O('Caregivers needed', 'int', NEED16), O('Caregivers available', 'int', AV16), O('Shortage', 'int', 'MAX(0,%s-%s)' % (NEED16, AV16)),
  O('Extra holiday pay with burden', 'money', 'ROUND(%s*%s*(%s-1)*%s,2)' % (HRS16, AVGPAY, PM16, BURD)), O('Volunteer premium', 'money', 'ROUND({in:vol}*{set:day_shift_hours}*{in:prem},2)'),
  O('Visits already in your Schedule that day', 'int', 'COUNTIFS({range:schedule.date},{in:hd},{range:schedule.status},"<>"&%s)' % tok('vstatus', 'Cancelled')),
  O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (AV16, NEED16, vd('Enough volunteers'), vd('Short of volunteers')))],
  GR('What if', ('Six volunteers', {'vol': 6}), ('Only 1 volunteer', {'vol': 1}), ('50 visits that day', {'visits': 50}), ('Christmas-type day, 25 visits', {'visits': 25}), ('Premium of 6', {'prem': 6})))

# ---- 17 call-off sensitivity
def SENS(delta):
    r = '({in:rate}+%s)' % delta
    lost = '({in:visits}*%s*{in:chrs})' % r
    unc = '(%s*(1-{in:succ})+{in:other})' % lost
    cost = '(%s*{in:succ}*({set:cover_premium}+{in:otshare}*%s*({set:overtime_mult}-1)*%s))' % (lost, AVGPAY, BURD)
    fill = '(1-%s/({in:visits}*{in:vh}))' % unc
    return cost, fill
t17s = []
for lab, dl in (('minus 2 points', '-0.02'), ('minus 1 point', '-0.01'), ('the current rate', '0'), ('plus 1 point', '0.01'), ('plus 2 points', '0.02')):
    c_, f_ = SENS(dl); t17s.append((lab, c_, f_))
t17 = TOOL('calloff_sens', 'Call-off Sensitivity', 'How much do cost and fill rate move if call-offs rise or fall?',
  'Type the weekly visits, the call-off rate, the hours of a call-off, the share found cover, the other uncovered hours and the overtime share of cover; see the weekly cover cost and fill rate at minus 2 to plus 2 points of call-off rate.', [
  I('visits', 'Visits a week', 258), I('rate', 'Call-off rate per visit now', 0.04, 'pct'), I('chrs', 'Hours of a call-off', 4, 'num'), I('succ', 'Share of call-offs found cover', 0.7, 'pct'), I('other', 'Other uncovered hours a week', 14, 'num'),
  I('vh', 'Average hours per visit', 3.5, 'num'), I('otshare', 'Share of cover hours that run into overtime', 0.25, 'pct')], [
  O('Weekly cover cost at %s' % l, 'money', 'ROUND(%s,0)' % c) for l, c, f in t17s] + [O('Fill rate at %s' % l, 'pct', f) for l, c, f in t17s] + [
  O('Call-offs a week at the current rate', 'num', 'ROUND({in:visits}*{in:rate},1)'), O('Verdict at the current rate', 'text', 'IF(%s>={set:fill_rate_target},%s,%s)' % (t17s[2][2], ck('On target'), ck('Below target')))],
  GR('What if', ('Cover found more often, 85 percent', {'succ': 0.85}), ('Cover found less often, 55 percent', {'succ': 0.55}), ('Fewer other uncovered hours', {'other': 6}), ('Busier week, 300 visits', {'visits': 300}), ('Short call-offs of 2 hours', {'chrs': 2})))

# ---- 18 what-if: extra caregivers against call-off rate
LOST18 = '({in:visits}*{in:rate}*{in:chrs})'
CAP18 = '({in:base}+{in:extra}*{in:free})'
UNC18 = '(MAX(0,%s-%s)+{in:other})' % (LOST18, CAP18)
FILL18 = '(1-%s/({in:visits}*{in:vh}))' % UNC18
grid18 = [('0 extra, rate 2%%', {'extra': 0, 'rate': 0.02}), ('0 extra, rate 4%%', {'extra': 0, 'rate': 0.04}), ('0 extra, rate 6%%', {'extra': 0, 'rate': 0.06}), ('2 extra, rate 2%%', {'extra': 2, 'rate': 0.02}),
          ('2 extra, rate 4%%', {'extra': 2, 'rate': 0.04}), ('2 extra, rate 6%%', {'extra': 2, 'rate': 0.06}), ('4 extra, rate 2%%', {'extra': 4, 'rate': 0.02}), ('4 extra, rate 4%%', {'extra': 4, 'rate': 0.04}), ('4 extra, rate 6%%', {'extra': 4, 'rate': 0.06})]
t18 = TOOL('extra_whatif', 'Extra Caregivers What-if', 'How many extra caregivers lift the fill rate to the target?',
  'Type the extra caregivers, the call-off rate, the weekly visits and the free hours of each extra caregiver; see the fill rate, the hours still uncovered and the extra caregivers needed. The grid crosses extra caregivers with the call-off rate.', [
  I('extra', 'Extra caregivers', 0), I('rate', 'Call-off rate per visit', 0.04, 'pct'), I('visits', 'Visits a week', 258), I('chrs', 'Hours of a call-off', 4, 'num'), I('base', 'Free hours a week already available for cover', 24, 'num'),
  I('free', 'Free hours a week of each extra caregiver', 12, 'num'), I('other', 'Other uncovered hours a week', 12, 'num'), I('vh', 'Average hours per visit', 3.5, 'num')], [
  O('Hours lost to call-offs a week', 'num', 'ROUND(%s,1)' % LOST18), O('Cover capacity a week, hours', 'num', 'ROUND(%s,1)' % CAP18), O('Uncovered hours a week', 'num', 'ROUND(%s,1)' % UNC18), O('Fill rate', 'pct', FILL18),
  O('Wanted fill rate', 'pct', '{set:fill_rate_target}'),
  O('Extra caregivers needed to reach the target', 'int', 'MAX(0,ROUNDUP((%s-{in:base}+{in:other}-(1-{set:fill_rate_target})*{in:visits}*{in:vh})/{in:free},0))' % LOST18),
  O('Verdict', 'text', 'IF(%s>={set:fill_rate_target},%s,%s)' % (FILL18, ck('On target'), ck('Below target')))], GR('Extra caregivers against call-off rate', *grid18))

tools = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16, t17, t18]
assert len(tools) == 18
