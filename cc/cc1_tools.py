"""Childcare center suite part 1: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc1_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
RT = {r: tok('room', r) for r in ROOMS}
ENR = tok('estatus', 'Enrolled'); LOST = tok('estatus', 'Lost'); NEW = tok('estatus', 'New'); TB = tok('estatus', 'Tour booked'); TH = tok('estatus', 'Tour held'); APP = tok('estatus', 'Applied'); WLS = tok('estatus', 'Waitlist')
WW = tok('waitstatus', 'Waiting'); WO = tok('waitstatus', 'Offered'); WS = tok('waitstatus', 'Started')
def FREE(room): return 'SUMIFS({range:places.free_places},{range:places.room},%s,{range:places.month},%s)' % (room, MS)
def CAP(room): return 'SUMIFS({range:rooms.capacity},{range:rooms.room},%s)' % room
def RATE(room, sched): return 'SUMIFS({range:rates.weekly_rate},{range:rates.room},%s,{range:rates.schedule},%s)' % (room, sched)
def FUN6(col): return 'INDEX({range:funnel.%s},MATCH(%s,{range:funnel.month},0))' % (col, MS)
def GRD(**kw): return kw
tools = []

# 1 ------------------------------------------------------------ place-filling decision
M1 = 'MATCH({in:room}&"|1",{range:fill.room_key},0)'; M2 = 'MATCH({in:room}&"|2",{range:fill.room_key},0)'
NW1 = 'COUNTIFS({range:waitlist.room},{in:room},{range:waitlist.status},%s)' % WW
DAYS1 = 'IFERROR(INDEX({range:fill.days_to_start},%s),0)' % M1
tools.append(TOOL('place_fill', 'Place-Filling Decision', 'Which waiting family fills this free place best',
    'Pick the room with a free place: waiting families are ranked by the tuition they bring over the weeks ahead (weekly value of the days wanted and how soon they start); see who to offer, the second choice and the verdict.', [
    IL('room', 'Room with a free place', 'room', 'Infants'), I('window', 'Days ahead that count as starting now', 45, 'int')], [
    O('Free places in the room now', 'int', FREE('{in:room}')), O('Families waiting for this room', 'int', NW1),
    O('Best match', 'text', 'IF(%s=0,"",IFERROR(INDEX({range:fill.name},%s),""))' % (NW1, M1)), O('Schedule wanted', 'text', 'IF(%s=0,"",IFERROR(INDEX({range:fill.schedule},%s),""))' % (NW1, M1)),
    O('Weekly value of the best match', 'money', 'IF(%s=0,0,IFERROR(INDEX({range:fill.weekly_value},%s),0))' % (NW1, M1)),
    O('Wanted start of the best match', 'date', 'IF(%s=0,"",IFERROR(INDEX({range:fill.want_start},%s),""))' % (NW1, M1)), O('Days to the wanted start', 'int', 'IF(%s=0,0,%s)' % (NW1, DAYS1)),
    O('Revenue over the weeks ahead, best match', 'money', 'IF(%s=0,0,IFERROR(INDEX({range:fill.horizon_value},%s),0))' % (NW1, M1)),
    O('Second match', 'text', 'IF(%s<2,"",IFERROR(INDEX({range:fill.name},%s),""))' % (NW1, M2)),
    O('Revenue over the weeks ahead, second match', 'money', 'IF(%s<2,0,IFERROR(INDEX({range:fill.horizon_value},%s),0))' % (NW1, M2)),
    O('Weeks the place stays empty before the best start', 'num', 'IF(%s=0,0,MAX(0,%s)/7)' % (NW1, DAYS1)),
    O('Tuition lost while it waits', 'money', 'IF(%s=0,0,IFERROR(INDEX({range:fill.weekly_value},%s),0)*MAX(0,%s)/7)' % (NW1, M1, DAYS1)),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s=0,%s,IF(%s<={in:window},%s,IF(%s<=2*{in:window},%s,%s))))' % (FREE('{in:room}'), c2('No free place'), NW1, c2('No one waiting'), DAYS1, c2('Offer now'), DAYS1, c2('Offer soon'), c2('Hold the place')))],
    GR('What if', ('Toddlers room', {'room': '=' + RT['Toddlers']}), ('Twos room', {'room': '=' + RT['Twos']}), ('Preschool room', {'room': '=' + RT['Preschool']}), ('School-age group', {'room': '=' + RT['School-age']}),
       ('Starting now means 20 days', {'window': 20}), ('Starting now means 120 days', {'window': 120}))))

# 2 ------------------------------------------------------------ waitlist start-date matcher
SM = 'DATE(YEAR({in:start}),MONTH({in:start}),1)'
FAT = 'SUMIFS({range:places.free_places},{range:places.room},{in:room},{range:places.month},%s)' % SM
AHEAD2 = 'COUNTIFS({range:waitlist.room},{in:room},{range:waitlist.status},%s,{range:waitlist.want_start},"<"&{in:start})' % WW
CND2 = '({range:places.room}={in:room})*({range:places.month}>=%s)*({range:places.free_flag}=1)' % SM
FIRST2 = 'SUMPRODUCT(MIN(%s*{range:places.month}+(1-%s)*99999))' % (CND2, CND2)
tools.append(TOOL('start_match', 'Waitlist Start-Date Matcher', 'Can this family start on the date they want',
    'Type the room, schedule and wanted start of a waiting family; see the free places in that month, the families ahead of them and the first month with a free place, with the verdict.', [
    IL('room', 'Room wanted', 'room', 'Preschool'), IL('sched', 'Schedule wanted', 'schedule', '5 full days'), I('start', 'Wanted start date', ahead(40), 'date')], [
    O('Free places in the room now', 'int', FREE('{in:room}')), O('Days to the wanted start', 'int', '{in:start}-{today}'), O('Free places at the end of the start month', 'int', FAT),
    O('Waiting families ahead who want an earlier start', 'int', AHEAD2), O('Places left after the families ahead', 'int', '(%s)-(%s)' % (FAT, AHEAD2)),
    O('First month with a free place from then', 'date', 'IF(%s>=99999,"",%s)' % (FIRST2, FIRST2)), O('Weekly rate of the days wanted', 'money', RATE('{in:room}', '{in:sched}')),
    O('Weekly tuition waiting for a place', 'money', 'SUMIFS({range:waitlist.weekly_value},{range:waitlist.room},{in:room},{range:waitlist.status},%s)' % WW),
    O('Verdict', 'text', 'IF((%s)-(%s)>0,%s,IF(%s<99999,%s,%s))' % (FAT, AHEAD2, c2('Can start on the date'), FIRST2, c2('Start later'), c2('No place in 12 months')))],
    GR('What if', ('Infants, start in 20 days', {'room': '=' + RT['Infants'], 'start': '={today}+20'}), ('Toddlers, start in 40 days', {'room': '=' + RT['Toddlers'], 'start': '={today}+40'}),
       ('Twos, start in 90 days', {'room': '=' + RT['Twos'], 'start': '={today}+90'}), ('School-age, 3 half days', {'room': '=' + RT['School-age'], 'sched': '=' + tok('schedule', '3 half days'), 'start': '={today}+30'}),
       ('Preschool, start in 100 days', {'start': '={today}+100'}))))

# 3 ------------------------------------------------------------ tour funnel conversion
R1 = '(({in:tb}/{in:enq})/%s)' % FUN6('own_book'); R2 = '(({in:th}/{in:tb})/%s)' % FUN6('own_held')
R3 = '(({in:app}/{in:th})/%s)' % FUN6('own_app'); R4 = '(({in:enr}/{in:app})/%s)' % FUN6('own_enr')
RM = 'MIN(%s,%s,%s,%s)' % (R1, R2, R3, R4)
HRS6 = 'AVERAGEIFS({range:enquiries.first_reply_hours},{range:enquiries.date},">="&EDATE(%s,-6),{range:enquiries.date},"<"&%s)' % (MS, MS)
tools.append(TOOL('funnel_tool', 'Tour Funnel Conversion', 'Which step of the tour funnel leaks most',
    'Type the last 3 months from Funnel by Month (enquiries, tours booked, held, no-shows, applications, children starting) and your hours to a first reply; each step is set against your own previous 6 months and the weakest step is named.', [
    I('enq', 'Enquiries', 52, 'int'), I('tb', 'Tours booked', 41, 'int'), I('th', 'Tours held', 38, 'int'), I('ns', 'Tour no-shows', 3, 'int'), I('app', 'Applications', 15, 'int'), I('enr', 'Children starting', 6, 'int'),
    I('hours', 'Average hours to a first reply', 14, 'num')], [
    O('Tours booked per enquiry', 'pct', 'IFERROR({in:tb}/{in:enq},0)'), O('Own tours booked per enquiry, 6 months', 'pct', FUN6('own_book')),
    O('Tours held per tour booked', 'pct', 'IFERROR({in:th}/{in:tb},0)'), O('Own tours held per booked, 6 months', 'pct', FUN6('own_held')),
    O('Applications per tour held', 'pct', 'IFERROR({in:app}/{in:th},0)'), O('Own applications per tour held, 6 months', 'pct', FUN6('own_app')),
    O('Children starting per application', 'pct', 'IFERROR({in:enr}/{in:app},0)'), O('Own starts per application, 6 months', 'pct', FUN6('own_enr')),
    O('Starts per enquiry, all steps', 'pct', 'IFERROR({in:enr}/{in:enq},0)'), O('Wanted starts per enquiry', 'pct', '{set:target_conversion}'),
    O('Tour no-show rate', 'pct', 'IFERROR({in:ns}/({in:th}+{in:ns}),0)'), O('Own average hours to a first reply, previous 6 months', 'num', 'IFERROR(%s,0)' % HRS6),
    O('Weakest step against your own history', 'pct', 'IFERROR(%s,1)' % RM),
    O('Verdict', 'text', 'IFERROR(IF(%s>=0.9,IF({in:hours}>{set:reply_hours_target},%s,%s),IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s)))),%s)' % (
        RM, c2('Fix the first reply'), c2('Funnel on track'), R1, RM, c2('Fix tour booking'), R2, RM, c2('Fix tour attendance'), R3, RM, c2('Fix tour to application'), c2('Fix application to enrolment'), c2('Funnel on track')))],
    GR('What if', ('Few tours booked', {'tb': 24, 'th': 22}), ('Many no-shows', {'th': 30, 'ns': 11}), ('Few applications', {'app': 6}), ('Slow replies', {'hours': 40}), ('Strong quarter', {'enq': 60, 'tb': 52, 'th': 50, 'app': 24, 'enr': 14}))))

# 4 ------------------------------------------------------------ referral source value ranker
def REVSRC(s): return 'SUMIFS({range:enquiries.weekly_value},{range:enquiries.source},%s,{range:enquiries.status},%s)' % (s, ENR)
RANK4 = '1+' + '+'.join('(%s>%s)' % (REVSRC(tok('source', s)), REVSRC('{in:source}')) for s in SOURCES)
SPEND4 = 'SUMIFS({range:marketing.cost},{range:marketing.source},{in:source},{range:marketing.month},">="&EDATE(%s,-12))' % MS
ENRM4 = 'SUMIFS({range:marketing.enrolled},{range:marketing.source},{in:source},{range:marketing.month},">="&EDATE(%s,-12))' % MS
REVC4 = 'IFERROR(INDEX({range:sources.revenue_child},MATCH({in:source},{range:sources.source},0)),0)'
CPE4 = 'IF(%s>0,%s/%s,0)' % (ENRM4, SPEND4, ENRM4)
tools.append(TOOL('source_rank', 'Referral Source Value Ranker', 'Which enquiry source earns the most tuition',
    'Pick an enquiry source: enquiries, enrolled children, yearly tuition per child and spend; the source is ranked among all seven by the tuition of the children it enrolled, not by counts, with a feed, hold or cut verdict.', [
    IL('source', 'Enquiry source', 'source', 'Online directory'), I('planned', 'Spend planned for the next 12 months', 600)], [
    O('Enquiries, all history', 'int', 'COUNTIFS({range:enquiries.source},{in:source})'), O('Enrolled children, all history', 'int', 'COUNTIFS({range:enquiries.source},{in:source},{range:enquiries.status},%s)' % ENR),
    O('Enrolled per enquiry', 'pct', 'IFERROR(COUNTIFS({range:enquiries.source},{in:source},{range:enquiries.status},%s)/COUNTIFS({range:enquiries.source},{in:source}),0)' % ENR),
    O('Yearly revenue per enrolled child', 'money', REVC4), O('Yearly revenue per enquiry', 'money', 'IFERROR(%s*COUNTIFS({range:enquiries.source},{in:source},{range:enquiries.status},%s)/COUNTIFS({range:enquiries.source},{in:source}),0)' % (REVC4, ENR)),
    O('Tuition of the children enrolled, weekly', 'money', REVSRC('{in:source}')), O('Rank among the 7 sources by tuition', 'int', RANK4),
    O('Spend in the last 12 months', 'money', SPEND4), O('Children enrolled from that spend', 'int', ENRM4), O('Cost per enrolled child', 'money', CPE4),
    O('Yearly revenue for each unit of cost', 'num', 'IF(%s>0,%s/%s,0)' % (CPE4, REVC4, CPE4)), O('Children expected from the planned spend', 'num', 'IF(%s>0,{in:planned}/%s,0)' % (CPE4, CPE4)),
    O('Yearly revenue expected from the planned spend', 'money', 'IF(%s>0,{in:planned}/%s*%s,0)' % (CPE4, CPE4, REVC4)),
    O('Verdict', 'text', 'IF(%s<=2,%s,IF(AND(%s>=6,%s>0),%s,%s))' % (RANK4, c2('Feed this source'), RANK4, SPEND4, c2('Cut this source'), c2('Hold this source')))],
    GR('What if', ('Word of mouth', {'source': '=' + tok('source', 'Word of mouth')}), ('Website', {'source': '=' + tok('source', 'Website')}), ('Roadside sign', {'source': '=' + tok('source', 'Roadside sign')}),
       ('Current family referrals', {'source': '=' + tok('source', 'Current family')}), ('Other settings', {'source': '=' + tok('source', 'Other settings')}), ('Local event, spend 1,500', {'source': '=' + tok('source', 'Local event'), 'planned': 1500}))))

# 5 ------------------------------------------------------------ marketing keep-or-drop
KC = 'IFERROR(INDEX({range:kinds.cost},MATCH({in:kind},{range:kinds.kind},0)),0)'; KE = 'IFERROR(INDEX({range:kinds.enrolled},MATCH({in:kind},{range:kinds.kind},0)),0)'
KQ = 'SUMIFS({range:marketing.enquiries},{range:marketing.kind},{in:kind},{range:marketing.month},">="&EDATE(%s,-12))' % MS
CPE5 = 'IF(%s>0,%s/%s,0)' % (KE, KC, KE); MK5 = '({in:weekly}*52/12*{in:margin})'
PB5 = 'IF(%s>0,%s/%s,99)' % (KE, CPE5, MK5)
tools.append(TOOL('mk_keep', 'Marketing Keep or Drop', 'Keep, renegotiate or drop this listing, sign or ad',
    'Pick a kind of marketing spend: its cost and the children enrolled in 12 months, the cost per enrolled child and the months to pay back from the tuition you keep; the verdict compares it with the payback you set.', [
    IL('kind', 'Kind of spend', 'mkind', 'Roadside sign'), I('weekly', 'Average weekly tuition of a child', 243), I('margin', 'Share of tuition you keep after staff and running costs', 0.10, 'pct')], [
    O('Cost in the last 12 months', 'money', KC), O('Enquiries it brought', 'int', KQ), O('Children enrolled from it', 'int', KE), O('Cost per enquiry', 'money', 'IF(%s>0,%s/%s,0)' % (KQ, KC, KQ)),
    O('Cost per enrolled child', 'money', CPE5), O('Tuition kept from one child each month', 'money', MK5), O('Months to pay back', 'num', PB5), O('Payback you set, months', 'int', '{set:payback_months}'),
    O('Highest cost per enrolled child that pays back in time', 'money', MK5 + '*{set:payback_months}'), O('Saving needed to pay back in time', 'money', 'MAX(0,%s-%s*{set:payback_months})' % (CPE5, MK5)),
    O('Yearly cost if kept', 'money', KC), O('Verdict', 'text', 'IF(%s=0,IF(%s>0,%s,%s),IF(%s<={set:payback_months},%s,IF(%s<=2*{set:payback_months},%s,%s)))' % (KE, KC, c2('Drop it'), c2('Keep it'), PB5, c2('Keep it'), PB5, c2('Renegotiate it'), c2('Drop it')))],
    GR('What if', ('Website upkeep', {'kind': '=' + tok('mkind', 'Website upkeep')}), ('Online directory', {'kind': '=' + tok('mkind', 'Online directory')}), ('Local flyers', {'kind': '=' + tok('mkind', 'Local flyers')}),
       ('Open day', {'kind': '=' + tok('mkind', 'Open day')}), ('Referral reward', {'kind': '=' + tok('mkind', 'Referral reward')}), ('Keep 30 percent of tuition', {'margin': 0.30}))))

# 6 ------------------------------------------------------------ lost-enquiry cause analyser
def LV6(r, win): return 'IFERROR(INDEX({range:lost.weekly_lost},MATCH(%s,{range:lost.reason},0))*{in:%s},0)' % (tok('lostreason', r), win)
WINS = [('No place', 'w_place'), ('Price', 'w_price'), ('Hours', 'w_hours'), ('Distance', 'w_dist'), ('Slow reply', 'w_reply')]
VALS6 = [LV6(r, w) for r, w in WINS]; TOP6 = 'MAX(%s)' % ','.join(VALS6)
VERD6 = [c2('Fix places first'), c2('Fix price first'), c2('Fix hours first'), c2('Fix distance first'), c2('Fix reply time first')]
V6F = 'IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s))))' % (VALS6[0], TOP6, VERD6[0], VALS6[1], TOP6, VERD6[1], VALS6[2], TOP6, VERD6[2], VALS6[3], TOP6, VERD6[3], VERD6[4])
tools.append(TOOL('lost_cause', 'Lost-Enquiry Cause Analyser', 'Which reason for losing families is worth fixing first',
    'Type the share of lost families you could win back by fixing each cause; with the lost families and weekly tuition of the last 12 months, the cause that returns the most weekly tuition is named first.', [
    I('w_place', 'Winnable if you add places', 0.40, 'pct'), I('w_price', 'Winnable if you change price', 0.25, 'pct'), I('w_hours', 'Winnable if you change hours', 0.20, 'pct'),
    I('w_dist', 'Winnable if you fix distance', 0.05, 'pct'), I('w_reply', 'Winnable if you reply faster', 0.50, 'pct')], [
    O('Lost enquiries, 12 months', 'int', 'SUM({range:lost.lost_enquiries})'), O('Weekly tuition lost, 12 months', 'money', 'SUM({range:lost.weekly_lost})'),
    O('Weekly tuition winnable: no place', 'money', VALS6[0]), O('Weekly tuition winnable: price', 'money', VALS6[1]), O('Weekly tuition winnable: hours', 'money', VALS6[2]),
    O('Weekly tuition winnable: distance', 'money', VALS6[3]), O('Weekly tuition winnable: slow reply', 'money', VALS6[4]), O('Weekly tuition winnable, all causes', 'money', '+'.join(VALS6)),
    O('Yearly tuition winnable if places exist', 'money', '(%s)*{set:weeks_open}' % '+'.join(VALS6)), O('Largest cause by lost families', 'text', 'IFERROR(INDEX({range:lost.reason},MATCH(MAX({range:lost.lost_enquiries}),{range:lost.lost_enquiries},0)),"")'),
    O('Largest cause by weekly tuition lost', 'text', 'IFERROR(INDEX({range:lost.reason},MATCH(MAX({range:lost.weekly_lost}),{range:lost.weekly_lost},0)),"")'),
    O('Share of lost tuition in the largest cause', 'pct', 'IFERROR(MAX({range:lost.weekly_lost})/SUM({range:lost.weekly_lost}),0)'), O('Verdict', 'text', V6F)],
    GR('What if', ('Add places wins 60 percent', {'w_place': 0.60}), ('Price cut wins 50 percent', {'w_price': 0.50}), ('Faster reply wins 80 percent', {'w_reply': 0.80}), ('Nothing winnable by place', {'w_place': 0.0}),
       ('Longer hours win 70 percent', {'w_hours': 0.70}))))

# 7 ------------------------------------------------------------ reply-time impact
FAST = 'IFERROR(COUNTIFS({range:enquiries.first_reply_hours},"<="&{set:reply_hours_target},{range:enquiries.status},%s)/COUNTIFS({range:enquiries.first_reply_hours},"<="&{set:reply_hours_target}),0)' % ENR
SLOW = 'IFERROR(COUNTIFS({range:enquiries.first_reply_hours},">"&{set:reply_hours_target},{range:enquiries.status},%s)/COUNTIFS({range:enquiries.first_reply_hours},">"&{set:reply_hours_target}),0)' % ENR
LATE90 = 'IFERROR(COUNTIFS({range:enquiries.date},">="&({today}-90),{range:enquiries.first_reply_hours},">"&{set:reply_hours_target})/COUNTIFS({range:enquiries.date},">="&({today}-90),{range:enquiries.first_reply_hours},"<>"),0)'
BAND7 = 'IF({in:hours}<=4,%s,IF({in:hours}<=24,%s,IF({in:hours}<=48,%s,%s)))' % (tok('rband', 'Up to 4 hours'), tok('rband', '5 to 24 hours'), tok('rband', '25 to 48 hours'), tok('rband', 'Over 48 hours'))
tools.append(TOOL('reply_impact', 'Reply-Time Impact', 'What a slow first reply costs in enrolments',
    'Type your usual hours to a first reply, the enquiries a month and the weekly tuition of a child; see how often replies miss your target, the share of families that enrol after a fast or slow reply and the tuition a faster reply would add.', [
    I('hours', 'Usual hours to a first reply', 30, 'int'), I('enq_month', 'Enquiries a month', 22, 'int'), I('weekly', 'Weekly tuition of a child', 243)], [
    O('Target hours to a first reply', 'int', '{set:reply_hours_target}'), O('Share enrolled after a reply within the target', 'pct', FAST), O('Share enrolled after a slower reply', 'pct', SLOW),
    O('Share enrolled in your reply band', 'pct', 'IFERROR(INDEX({range:reply_bands.enrolled_share},MATCH(%s,{range:reply_bands.band},0)),0)' % BAND7),
    O('Replies later than the target, last 90 days', 'pct', LATE90), O('Enquiries a month answered late', 'num', '{in:enq_month}*%s' % LATE90),
    O('Extra children a month if every reply met the target', 'num', '{in:enq_month}*%s*MAX(0,(%s)-(%s))' % (LATE90, FAST, SLOW)),
    O('Weekly tuition added by each month of fast replies', 'money', '{in:enq_month}*%s*MAX(0,(%s)-(%s))*{in:weekly}' % (LATE90, FAST, SLOW)),
    O('Yearly tuition added', 'money', '{in:enq_month}*%s*MAX(0,(%s)-(%s))*{in:weekly}*12*{set:weeks_open}/12' % (LATE90, FAST, SLOW)),
    O('Own average hours to a first reply, last 90 days', 'num', 'IFERROR(AVERAGEIFS({range:enquiries.first_reply_hours},{range:enquiries.date},">="&({today}-90)),0)'),
    O('Verdict', 'text', 'IF({in:hours}<={set:reply_hours_target},%s,%s)' % (c2('Reply time on target'), c2('Reply faster')))],
    GR('What if', ('Reply the same day', {'hours': 6}), ('Reply in two days', {'hours': 48}), ('40 enquiries a month', {'enq_month': 40}), ('Half day tuition 170', {'weekly': 170}), ('Full week infant tuition 410', {'weekly': 410}))))

# 8 ------------------------------------------------------------ unfilled revenue by room
def FW(r): return '%s*%s*{in:factor}' % (FREE(RT[r]), RATE(RT[r], '{in:sched}'))
WV = [FW(r) for r in ROOMS]
def RK8(i): return '1+' + '+'.join('(%s>%s)' % (WV[j], WV[i]) for j in range(5) if j != i)
tools.append(TOOL('unfilled', 'Unfilled Revenue by Room', 'Tuition left empty by free places, room by room',
    'Pick the schedule most families book and a price level; see the free places in each room, the weekly tuition they leave empty, the rooms ranked and the occupancy against your target.', [
    IL('sched', 'Schedule most families book', 'schedule', '5 full days'), I('factor', 'Price level against the rate card, 1 is the rate card', 1.0, 'num')], [
    O('Infants: free places', 'int', FREE(RT['Infants'])), O('Toddlers: free places', 'int', FREE(RT['Toddlers'])), O('Twos: free places', 'int', FREE(RT['Twos'])),
    O('Preschool: free places', 'int', FREE(RT['Preschool'])), O('School-age: free places', 'int', FREE(RT['School-age'])),
    O('Infants: weekly tuition empty', 'money', WV[0]), O('Toddlers: weekly tuition empty', 'money', WV[1]), O('Twos: weekly tuition empty', 'money', WV[2]), O('Preschool: weekly tuition empty', 'money', WV[3]),
    O('School-age: weekly tuition empty', 'money', WV[4]),
    O('Infants: rank', 'int', RK8(0)), O('Toddlers: rank', 'int', RK8(1)), O('Twos: rank', 'int', RK8(2)), O('Preschool: rank', 'int', RK8(3)), O('School-age: rank', 'int', RK8(4)),
    O('Weekly tuition empty, all rooms', 'money', '+'.join(WV)), O('Yearly tuition empty, all rooms', 'money', '(%s)*{set:weeks_open}' % '+'.join(WV)),
    O('Occupancy, all rooms', 'pct', 'IFERROR(1-SUMIFS({range:places.free_places},{range:places.month},%s)/SUM({range:rooms.capacity}),0)' % MS),
    O('Verdict', 'text', 'IF(IFERROR(1-SUMIFS({range:places.free_places},{range:places.month},%s)/SUM({range:rooms.capacity}),0)<{set:occupancy_target},%s,%s)' % (MS, c2('Below occupancy target'), c2('At occupancy target')))],
    GR('What if', ('Half days, 5 a week', {'sched': '=' + tok('schedule', '5 half days')}), ('Three full days', {'sched': '=' + tok('schedule', '3 full days')}), ('Rates 5 percent higher', {'factor': 1.05}), ('Rates 5 percent lower', {'factor': 0.95}))))

# 9 ------------------------------------------------------------ tour slot planner
CAP9 = 'MIN({in:slots},ROUNDDOWN({in:hours}*60/{in:minutes},0))'
NEXT7 = 'COUNTIFS({range:tours.date},">="&{today},{range:tours.date},"<="&({today}+6),{range:tours.status},%s)' % tok('tourstatus', 'Booked')
tools.append(TOOL('tour_planner', 'Tour Slot Planner', 'Do you have enough tour slots for the queue',
    'Type the enquiries waiting for a tour, the slots a week, the staff hours you give to tours and your no-show rate; see the tours you can hold, the weeks to clear the queue and whether to add slots.', [
    I('waiting', 'Enquiries waiting for a tour', 9, 'int'), I('slots', 'Tour slots a week', 12, 'int'), I('hours', 'Staff hours a week for tours', 6, 'num'), I('minutes', 'Minutes one tour takes', 45, 'int'),
    I('noshow', 'Tour no-show rate', 0.08, 'pct'), I('target_days', 'Days you want to wait at most for a tour', 7, 'int')], [
    O('Tours the staff hours allow a week', 'int', 'ROUNDDOWN({in:hours}*60/{in:minutes},0)'), O('Tours you can give a week', 'int', CAP9),
    O('Tours expected to be held a week', 'num', '%s*(1-{in:noshow})' % CAP9), O('Weeks to clear the queue', 'num', 'IF(%s>0,{in:waiting}/%s,99)' % (CAP9, CAP9)),
    O('Days to clear the queue', 'int', 'IF(%s>0,ROUNDUP({in:waiting}/%s*7,0),999)' % (CAP9, CAP9)), O('Slots needed a week to clear it in time', 'int', 'ROUNDUP({in:waiting}/({in:target_days}/7),0)'),
    O('Extra slots needed a week', 'int', 'MAX(0,ROUNDUP({in:waiting}/({in:target_days}/7),0)-%s)' % CAP9), O('Extra staff hours needed a week', 'num', 'MAX(0,ROUNDUP({in:waiting}/({in:target_days}/7),0)-%s)*{in:minutes}/60' % CAP9),
    O('Tours booked in the next 7 days', 'int', NEXT7), O('Free slots in the next 7 days, tour calendar', 'int', 'SUMIFS({range:tour_cal.free_slots},{range:tour_cal.date},"<="&({today}+6))'),
    O('Own average days from enquiry to tour', 'num', 'IFERROR(AVERAGE({range:enquiries.days_to_tour}),0)'),
    O('Verdict', 'text', 'IF(%s<ROUNDUP({in:waiting}/({in:target_days}/7),0),%s,%s)' % (CAP9, c3('Add tour slots'), c3('Enough tour slots')))],
    GR('What if', ('Twenty enquiries waiting', {'waiting': 20}), ('Four slots a week', {'slots': 4}), ('Ten staff hours', {'hours': 10}), ('Half-hour tours', {'minutes': 30}), ('Wait at most 3 days', {'target_days': 3}))))

# 10 ----------------------------------------------------------- waitlist clear-down plan
RC10 = 'ROUND({set:recheck_days}*IF({in:priority}=%s,2/3,IF({in:priority}=%s,4/3,1)),0)' % (tok('priority', 'High'), tok('priority', 'Low'))
tools.append(TOOL('clear_down', 'Waitlist Clear-Down Plan', 'Re-confirm, offer or remove a waiting family',
    'Type how long a family has waited, the days since you last spoke, their priority, the days to their wanted start and the free places in their room; see the verdict, how many families are due a re-confirm and how long families usually wait.', [
    IN('priority', 'Priority', 'list', key('priority', 'Normal'), list='priority'), I('days_added', 'Days on the waiting list', 130, 'int'), I('days_contact', 'Days since you last spoke to them', 100, 'int'),
    I('days_start', 'Days to the wanted start, negative if it has passed', 40, 'int'), I('free', 'Free places in their room', 1, 'int')], [
    O('Re-confirm after this many days', 'int', RC10), O('Days past the re-confirm limit', 'int', 'MAX(0,{in:days_contact}-%s)' % RC10),
    O('Share of the list waiting longer than this family', 'pct', 'IFERROR(COUNTIFS({range:waitlist.status},%s,{range:waitlist.days_waiting},">"&{in:days_added})/COUNTIFS({range:waitlist.status},%s),0)' % (WW, WW)),
    O('Families waiting now', 'int', 'COUNTIFS({range:waitlist.status},%s)' % WW), O('Waiting families past the re-confirm limit', 'int', 'COUNTIFS({range:waitlist.status},%s,{range:waitlist.days_waiting},">"&{set:recheck_days})' % WW),
    O('Average days waited by families who started', 'num', 'IFERROR(AVERAGEIFS({range:waitlist.days_waiting},{range:waitlist.status},%s),0)' % WS),
    O('Days this family has waited against that average', 'int', '{in:days_added}-IFERROR(AVERAGEIFS({range:waitlist.days_waiting},{range:waitlist.status},%s),0)' % WS),
    O('Families who withdrew from the list', 'int', 'COUNTIFS({range:waitlist.status},%s)' % tok('waitstatus', 'Withdrawn')),
    O('Verdict', 'text', 'IF(AND({in:free}>0,{in:days_start}<={set:start_window_days},{in:days_start}>=0),%s,IF(OR({in:days_contact}>2*%s,{in:days_start}<-30),%s,IF({in:days_contact}>%s,%s,%s)))' % (
        c3('Offer a place'), RC10, c3('Remove from the list'), RC10, c3('Re-confirm'), c3('Keep waiting')))],
    GR('What if', ('Starts in 20 days, place free', {'days_start': 20, 'days_contact': 30}), ('Not spoken to for 200 days', {'days_contact': 200}), ('Wanted start passed 60 days ago', {'days_start': -60}), ('Recent contact', {'days_contact': 20}),
       ('High priority family', {'priority': '=' + tok('priority', 'High'), 'days_contact': 70}))))

# 11 ----------------------------------------------------------- offer answer tracker
DUE11 = '({in:offered}+{in:allowed})'
tools.append(TOOL('offer_tracker', 'Offer Answer Tracker', 'When to chase or release an offered place',
    'Type the date you offered a place and the days a family has to answer; see the answer due date, the days left and whether to wait, chase today or release the place, with your own answer times from the Offer Log.', [
    I('offered', 'Date the place was offered', ago(5), 'date'), I('allowed', 'Days allowed to answer', 7, 'int'), I('remind', 'Chase when this many days are left', 2, 'int')], [
    O('Answer due', 'date', DUE11), O('Days since the offer', 'int', '{today}-{in:offered}'), O('Days left to answer', 'int', '%s-{today}' % DUE11), O('Chase on', 'date', '%s-{in:remind}' % DUE11),
    O('Offers waiting for an answer', 'int', 'COUNTIFS({range:offers.offered_on},">0",{range:offers.answered_on},"")'),
    O('Average days to answer', 'num', 'IFERROR(AVERAGEIFS({range:offers.days_to_answer},{range:offers.answered_on},">0"),0)'),
    O('Longest answer, days', 'int', 'SUMPRODUCT(MAX(({range:offers.answered_on}>0)*({range:offers.answered_on}-{range:offers.offered_on})))'),
    O('Share answered within the days allowed', 'pct', 'IFERROR(COUNTIFS({range:offers.answered_on},">0",{range:offers.days_to_answer},"<="&{in:allowed})/COUNTIFS({range:offers.answered_on},">0"),0)'),
    O('Share of answered offers accepted', 'pct', 'IFERROR(COUNTIFS({range:offers.answer},%s)/COUNTIFS({range:offers.answered_on},">0"),0)' % tok('offerans', 'Accepted')),
    O('Verdict', 'text', 'IF(%s<{today},%s,IF(%s-{today}<={in:remind},%s,%s))' % (DUE11, ca('Release the place'), DUE11, ca('Chase today'), c3('Wait for the answer')))],
    GR('What if', ('Offered 10 days ago', {'offered': '={today}-10'}), ('Offered today', {'offered': '={today}'}), ('Offered 6 days ago', {'offered': '={today}-6'}), ('Allow 14 days', {'allowed': 14}), ('Allow 3 days', {'allowed': 3}))))

# 12 ----------------------------------------------------------- starters occupancy scenario
ROOMK = [(r, 'st_' + k, 'lv_' + k) for r, k in zip(ROOMS, ['inf', 'tod', 'two', 'pre', 'sch'])]
FS = 'IF({in:scn}=%s,0.5,1)' % tok('scen', 'Worst'); FL = 'IF({in:scn}=%s,0,IF({in:scn}=%s,1.5,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
MON = 'DATE(YEAR({in:month}),MONTH({in:month}),1)'
def AFT(r, st, lv): return 'MAX(0,ROUND(%s-SUMIFS({range:places.free_places},{range:places.room},%s,{range:places.month},%s)+{in:%s}*%s-{in:%s}*%s,0))' % (CAP(RT[r]), RT[r], MON, st, FS, lv, FL)
def RATIO(r): return 'SUMIFS({range:rooms.ratio},{range:rooms.room},%s)' % RT[r]
AF = {r: AFT(r, st, lv) for r, st, lv in ROOMK}
STAFF = {r: 'ROUNDUP((%s)/%s,0)' % (AF[r], RATIO(r)) for r in ROOMS}
STF = '+'.join(STAFF[r] for r in ROOMS)
ins12 = [I('month', 'Month the children start', iso(add_months(month_start(0), 1)), 'date'), IL('scn', 'Scenario', 'scen', 'Base')]
for r, st, lv in ROOMK: ins12 += [I(st, '%s starters' % r, {'Infants': 1, 'Toddlers': 1, 'Preschool': 1}.get(r, 0), 'int'), I(lv, '%s leavers' % r, {'Twos': 1}.get(r, 0), 'int')]
ins12.append(I('onhand', 'Staff on the floor at the busiest hour', 8, 'int'))
outs12 = [O('%s: children after the starters' % r, 'int', AF[r]) for r in ROOMS]
outs12 += [O('%s: occupancy' % r, 'pct', 'IFERROR((%s)/%s,0)' % (AF[r], CAP(RT[r]))) for r in ROOMS]
outs12 += [O('%s: staff needed at the ratio' % r, 'int', STAFF[r]) for r in ROOMS]
outs12 += [O('Staff needed, all rooms', 'int', STF), O('Staff needed less staff on the floor', 'int', '(%s)-{in:onhand}' % STF), O('Verdict', 'text', 'IF((%s)-{in:onhand}>0,%s,%s)' % (STF, c3('Hire relief'), c3('Hold staffing')))]
tools.append(TOOL('starters_scn', 'Starters Occupancy Scenario', 'Occupancy and staff needed when new children start',
    'Pick the start month and a Base, Best or Worst scenario and type the starters and leavers in each room (a ratio is the children each staff member may care for, check your local rules); see the children, occupancy and staff needed by room.',
    ins12, outs12, GR('What if', ('Best scenario', {'scn': '=' + tok('scen', 'Best')}), ('Worst scenario', {'scn': '=' + tok('scen', 'Worst')}), ('Three more Infants starters', {'st_inf': 3}), ('Two more Twos starters', {'st_two': 2}),
                      ('School-age fills up, 6 starters', {'st_sch': 6}), ('One more staff member', {'onhand': 9}))))

# 13 ----------------------------------------------------------- waiting list value by room
NW13 = 'COUNTIFS({range:waitlist.room},{in:room},{range:waitlist.status},%s)' % WW
FR13 = FREE('{in:room}')
TG13 = '(%s*{in:cover})' % FR13
tools.append(TOOL('wl_value', 'Waiting List Value by Room', 'Are enough families waiting for the places you have free',
    'Pick a room: the families waiting and the weekly tuition they bring against the free places and the tuition the empty places leave; the verdict says whether to recruit more or enough families wait.', [
    IL('room', 'Room', 'room', 'Infants'), I('cover', 'Families you want waiting for each free place', 1.5, 'num'), I('months', 'Months ahead to check free places', 3, 'int')], [
    O('Families waiting', 'int', NW13), O('Weekly tuition waiting', 'money', 'SUMIFS({range:waitlist.weekly_value},{range:waitlist.room},{in:room},{range:waitlist.status},%s)' % WW),
    O('Free places now', 'int', FR13), O('Free places at the end of the month ahead', 'int', 'SUMIFS({range:places.free_places},{range:places.room},{in:room},{range:places.month},EDATE(%s,{in:months}))' % MS),
    O('Weekly tuition the free places leave empty', 'money', 'MAX(0,%s)*%s' % (FR13, RATE('{in:room}', tok('schedule', '5 full days')))),
    O('Waiting tuition against empty tuition', 'num', 'IFERROR(SUMIFS({range:waitlist.weekly_value},{range:waitlist.room},{in:room},{range:waitlist.status},%s)/(MAX(0,%s)*%s),0)' % (WW, FR13, RATE('{in:room}', tok('schedule', '5 full days')))),
    O('Families waiting for each free place', 'num', 'IFERROR(%s/%s,0)' % (NW13, FR13)), O('Families you want waiting', 'num', TG13), O('Families still to recruit', 'int', 'MAX(0,ROUNDUP(%s-%s,0))' % (TG13, NW13)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (NW13, TG13, ca('Enough waiting'), ca('Recruit more')))],
    GR('What if', ('Twos', {'room': '=' + RT['Twos']}), ('Toddlers', {'room': '=' + RT['Toddlers']}), ('Preschool', {'room': '=' + RT['Preschool']}), ('School-age', {'room': '=' + RT['School-age']}), ('Want 3 waiting per place', {'cover': 3}), ('Look 6 months ahead', {'months': 6}))))

# 14 ----------------------------------------------------------- open day return test
OC = 'SUMIFS({range:marketing.cost},{range:marketing.kind},%s)' % tok('mkind', 'Open day'); OE = 'SUMIFS({range:marketing.enrolled},{range:marketing.kind},%s)' % tok('mkind', 'Open day')
PB14 = 'IF({in:enrolled}>0,{in:cost}/({in:enrolled}*{in:weekly}*52/12*{in:margin}),99)'
tools.append(TOOL('open_day', 'Open Day Return Test', 'Repeat, change or drop the open day',
    'Type what the open day cost, the families who came, the applications and the children enrolled from it; see the cost of each step, the months to pay back from the tuition you keep and a verdict set against your own earlier open days.', [
    I('cost', 'Cost of the open day', 250), I('attended', 'Families who came', 9, 'int'), I('applications', 'Applications from it', 3, 'int'), I('enrolled', 'Children enrolled from it', 2, 'int'),
    I('weekly', 'Weekly tuition of a child', 243), I('margin', 'Share of tuition you keep after costs', 0.10, 'pct')], [
    O('Cost per family who came', 'money', 'IFERROR({in:cost}/{in:attended},0)'), O('Cost per application', 'money', 'IFERROR({in:cost}/{in:applications},0)'), O('Cost per enrolled child', 'money', 'IFERROR({in:cost}/{in:enrolled},0)'),
    O('Applications per family who came', 'pct', 'IFERROR({in:applications}/{in:attended},0)'), O('Enrolled per application', 'pct', 'IFERROR({in:enrolled}/{in:applications},0)'),
    O('Yearly tuition from the children enrolled', 'money', '{in:enrolled}*{in:weekly}*{set:weeks_open}'), O('Tuition kept each month', 'money', '{in:enrolled}*{in:weekly}*52/12*{in:margin}'),
    O('Months to pay back', 'num', PB14), O('Payback you set, months', 'int', '{set:payback_months}'), O('Your open days so far', 'int', 'COUNTIFS({range:marketing.kind},%s)' % tok('mkind', 'Open day')),
    O('Children enrolled from them', 'int', OE), O('Cost per child enrolled, all your open days', 'money', 'IF(%s>0,%s/%s,0)' % (OE, OC, OE)),
    O('Verdict', 'text', 'IF({in:enrolled}=0,%s,IF(%s<={set:payback_months},%s,IF(%s<=2*{set:payback_months},%s,%s)))' % (c3('Drop the open day'), PB14, c3('Repeat the open day'), PB14, c3('Change the open day'), c3('Drop the open day')))],
    GR('What if', ('Nobody enrolls', {'enrolled': 0}), ('Three enroll', {'enrolled': 3, 'applications': 5}), ('Cheaper open day, cost 120', {'cost': 120}), ('Big turnout, 25 families', {'attended': 25, 'applications': 8, 'enrolled': 4}), ('Infant tuition 410', {'weekly': 410}))))

# 15 ----------------------------------------------------------- enquiry follow-up scheduler
INT15 = 'IF({in:status}=%s,1,IF({in:status}=%s,2,IF({in:status}=%s,3,IF({in:status}=%s,{set:recheck_days},0))))' % (NEW, TH, APP, WLS)
WAIT15 = 'IF({in:status}=%s,MAX(0,{in:tour_days}-2),MAX(0,%s-{in:days_since}))' % (TB, INT15)
tools.append(TOOL('follow_up', 'Enquiry Follow-Up Scheduler', 'Call, write or close this enquiry',
    'Pick the enquiry status, the days since the last step and, for a booked tour, the days to the tour; see when the next step is due, what it is and how many enquiries are stale right now.', [
    IL('status', 'Enquiry status', 'estatus', 'Tour held'), I('days_since', 'Days since the last step', 4, 'int'), I('tour_days', 'Days to the booked tour, if any', 3, 'int')], [
    O('Days until the next step, negative if late', 'int', 'IF({in:status}=%s,{in:tour_days}-2,%s-{in:days_since})' % (TB, INT15)), O('Next follow-up date', 'date', '{today}+%s' % WAIT15), O('Days overdue', 'int', 'IF({in:status}=%s,0,MAX(0,{in:days_since}-%s))' % (TB, INT15)),
    O('Stale enquiries now, open or waiting', 'int', 'COUNTIFS({range:stale.days_since},">="&{set:stale_days})'), O('Enquiries to close now', 'int', 'COUNTIFS({range:stale.next_step},%s)' % ns('Close the enquiry')),
    O('Calls due today', 'int', 'COUNTIFS({range:stale.next_step},%s)' % ns('Call today')), O('Forms to chase', 'int', 'COUNTIFS({range:stale.next_step},%s)' % ns('Chase the forms')),
    O('Verdict', 'text', 'IF({in:days_since}>={set:close_after_days},%s,IF(%s>0,%s,IF({in:status}=%s,IF({in:days_since}>=1,%s,%s),IF({in:status}=%s,%s,IF({in:status}=%s,%s,IF({in:status}=%s,%s,IF({in:status}=%s,%s,%s)))))))' % (
        ns('Close the enquiry'), WAIT15, ns('Not due yet'), NEW, ns('Call today'), ns('Write today'), TB, ns('Remind about the tour'), TH, ns('Send the next steps'), APP, ns('Chase the forms'), WLS, ns('Re-confirm the place'), ns('Not due yet')))],
    GR('What if', ('New enquiry, 3 days old', {'status': '=' + NEW, 'days_since': 3}), ('Tour tomorrow', {'status': '=' + TB, 'tour_days': 1}), ('Applied 5 days ago', {'status': '=' + APP, 'days_since': 5}), ('Waiting 100 days', {'status': '=' + WLS, 'days_since': 100}),
       ('No answer for 40 days', {'days_since': 40}))))

# 16 ----------------------------------------------------------- priority rule comparer
def SC(rule, n): return {'sib': '({in:s%d}*1000+{in:d%d})' % (n, n), 'staff': '({in:f%d}*1000+{in:s%d}*100+{in:d%d})' % (n, n, n), 'date': '{in:d%d}' % n}[rule]
def WIN(rule):
    a, b, c = SC(rule, 1), SC(rule, 2), SC(rule, 3)
    return 'IF(AND(%s>=%s,%s>=%s),{in:n1},IF(%s>=%s,{in:n2},{in:n3}))' % (a, b, a, c, b, c)
def WDAYS(rule):
    a, b, c = SC(rule, 1), SC(rule, 2), SC(rule, 3)
    return 'IF(AND(%s>=%s,%s>=%s),{in:d1},IF(%s>=%s,{in:d2},{in:d3}))' % (a, b, a, c, b, c)
LONGEST = 'MAX({in:d1},{in:d2},{in:d3})'
COST_S, COST_F, COST_D = ['(%s-%s)' % (LONGEST, WDAYS(r)) for r in ('sib', 'staff', 'date')]
tools.append(TOOL('priority_rule', 'Priority Rule Comparer', 'Which waiting-list rule is the fairest for the next place',
    'Type three waiting families, the days each has waited and whether they have a sibling at the center or are a staff child; see who wins under sibling first, staff child first and date added, and which rule makes the longest waiter wait least longer.', [
    I('n1', 'First family', 'Elena Fraser', 'text'), I('d1', 'First family: days waiting', 130, 'int'), I('s1', 'First family: sibling, 1 yes 0 no', 0, 'int'), I('f1', 'First family: staff child, 1 yes 0 no', 0, 'int'),
    I('n2', 'Second family', 'Nikolai Jung', 'text'), I('d2', 'Second family: days waiting', 48, 'int'), I('s2', 'Second family: sibling, 1 yes 0 no', 1, 'int'), I('f2', 'Second family: staff child, 1 yes 0 no', 0, 'int'),
    I('n3', 'Third family', 'Marcus Celik', 'text'), I('d3', 'Third family: days waiting', 28, 'int'), I('s3', 'Third family: sibling, 1 yes 0 no', 0, 'int'), I('f3', 'Third family: staff child, 1 yes 0 no', 1, 'int')], [
    O('Date added: the next place goes to', 'text', WIN('date')), O('Sibling first: the next place goes to', 'text', WIN('sib')), O('Staff child first: the next place goes to', 'text', WIN('staff')),
    O('Date added: days the winner has waited', 'int', WDAYS('date')), O('Sibling first: days the winner has waited', 'int', WDAYS('sib')), O('Staff child first: days the winner has waited', 'int', WDAYS('staff')),
    O('Longest wait among the three, days', 'int', LONGEST), O('Sibling first: days the longest waiter loses', 'int', COST_S), O('Staff child first: days the longest waiter loses', 'int', COST_F),
    O('Families who change place against date added', 'int', '(%s<>%s)+(%s<>%s)' % (WIN('sib'), WIN('date'), WIN('staff'), WIN('date'))),
    O('Verdict', 'text', 'IF(AND(%s=%s,%s=%s),%s,IF(AND(%s<=%s,%s<=%s),%s,IF(%s<=%s,%s,%s)))' % (WIN('sib'), WIN('date'), WIN('staff'), WIN('date'), c3('Same winner under every rule'),
        COST_D, COST_S, COST_D, COST_F, c3('Date added is fairest'), COST_S, COST_F, c3('Sibling first is fairest'), c3('Staff child first is fairest')))],
    GR('What if', ('Second family waited longer', {'d2': 150}), ('No sibling or staff child', {'s2': 0, 'f3': 0}), ('Third family has a sibling', {'s3': 1}), ('All waited the same', {'d1': 60, 'd2': 60, 'd3': 60}))))

# 17 ----------------------------------------------------------- price-lost break-even
LOSTP = 'COUNTIFS({range:enquiries.status},%s,{range:enquiries.reason},%s,{range:enquiries.date},">="&({today}-365))' % (LOST, tok('lostreason', 'Price'))
BE17 = 'ROUNDUP({in:disc}*{in:families}/(1-{in:disc}),0)'
tools.append(TOOL('price_lost', 'Price-Lost Break-Even', 'Does a fee cut win back enough price-lost families',
    'Type the fee cut, the weekly tuition of a child, the families who would get the lower fee and the share of price-lost families you expect to win back; the break-even number of families is worked out in closed form against the price-lost families of the last 12 months.', [
    I('disc', 'Fee cut', 0.05, 'pct'), I('weekly', 'Weekly tuition of a child', 243), I('families', 'Families who would pay the lower fee', 44, 'int'), I('winback', 'Share of price-lost families you expect to win back', 0.25, 'pct')], [
    O('Weekly tuition given up by the cut', 'money', '{in:disc}*{in:weekly}*{in:families}'), O('Weekly tuition of one family won back', 'money', '{in:weekly}*(1-{in:disc})'),
    O('Families to win back to break even', 'int', BE17), O('Price-lost enquiries, last 12 months', 'int', LOSTP), O('Families you expect to win back', 'num', '%s*{in:winback}' % LOSTP),
    O('Share of price-lost families needed to break even', 'pct', 'IFERROR(%s/%s,0)' % (BE17, LOSTP)), O('Weekly tuition gained less given up', 'money', '%s*{in:winback}*{in:weekly}*(1-{in:disc})-{in:disc}*{in:weekly}*{in:families}' % LOSTP),
    O('Yearly tuition gained less given up', 'money', '(%s*{in:winback}*{in:weekly}*(1-{in:disc})-{in:disc}*{in:weekly}*{in:families})*{set:weeks_open}' % LOSTP),
    O('Verdict', 'text', 'IF(%s*{in:winback}>=%s,%s,%s)' % (LOSTP, BE17, c3('Worth it'), c3('Not worth it')))],
    GR('What if', ('Cut 10 percent', {'disc': 0.10}), ('Cut 3 percent', {'disc': 0.03}), ('Win back half', {'winback': 0.50}), ('Only new families get the cut', {'families': 5}), ('Infant tuition 410', {'weekly': 410}))))

# 18 ----------------------------------------------------------- intake pipeline forecast
AVG12 = 'COUNTIFS({range:enquiries.month},">="&EDATE(%s,-12),{range:enquiries.month},"<"&%s)/12' % (MS, MS)
BASE3 = 'COUNTIFS({range:enquiries.month},">="&EDATE(%s,-3),{range:enquiries.month},"<"&%s)/3' % (MS, MS)
def SEAS(k): return 'IFERROR(COUNTIFS({range:enquiries.month},EDATE(%s,%d))/(%s),1)' % (MS, k - 12, AVG12)
CONV18 = 'IFERROR(SUMIFS({range:funnel.enrolled},{range:funnel.month},">="&EDATE(%s,-12),{range:funnel.month},"<"&%s)/SUMIFS({range:funnel.enquiries},{range:funnel.month},">="&EDATE(%s,-12),{range:funnel.month},"<"&%s),0)' % (MS, MS, MS, MS)
SF18 = 'IF({in:scn}=%s,1.2,IF({in:scn}=%s,0.75,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
def ENQ(k): return 'ROUND(%s*%s*(1+{in:enq_change}),0)' % (BASE3, SEAS(k))
def STR(k): return '%s*%s*%s' % (ENQ(k), CONV18, SF18)
TOT18 = '(%s+%s+%s)' % (STR(1), STR(2), STR(3)); FREE18 = 'SUMIFS({range:places.free_places},{range:places.month},EDATE(%s,3))' % MS
tools.append(TOOL('intake_forecast', 'Intake Pipeline Forecast', 'Will the free places fill in the next 3 months',
    'Pick a Base, Best or Worst scenario: enquiries for the next 3 months follow your own last 3 months and the same months last year, starts follow your own last 12 months of starts per enquiry, and the total is set against the free places 3 months ahead.', [
    IL('scn', 'Scenario', 'scen', 'Base'), I('enq_change', 'Change in enquiries against your own pattern', 0.0, 'pct'), I('waiting', 'Waiting families who will start in these months', 2, 'int')], [
    O('Average enquiries a month, last 3 months', 'num', BASE3), O('Own starts per enquiry, last 12 months', 'pct', CONV18),
    O('Seasonal factor, next month', 'num', SEAS(1)), O('Seasonal factor, month after', 'num', SEAS(2)), O('Seasonal factor, third month', 'num', SEAS(3)),
    O('Expected enquiries, next month', 'int', ENQ(1)), O('Expected enquiries, month after', 'int', ENQ(2)), O('Expected enquiries, third month', 'int', ENQ(3)),
    O('Expected starts from enquiries, next month', 'num', STR(1)), O('Expected starts from enquiries, month after', 'num', STR(2)), O('Expected starts from enquiries, third month', 'num', STR(3)),
    O('Expected starts in 3 months, with waiting families', 'num', '%s+{in:waiting}' % TOT18), O('Free places in 3 months', 'int', FREE18), O('Free places less expected starts', 'num', '%s-(%s+{in:waiting})' % (FREE18, TOT18)),
    O('Verdict', 'text', 'IF(%s+{in:waiting}>=%s,%s,%s)' % (TOT18, FREE18, c3('Places will fill'), c3('Places may stay empty')))],
    GR('What if', ('Best scenario', {'scn': '=' + tok('scen', 'Best')}), ('Worst scenario', {'scn': '=' + tok('scen', 'Worst')}), ('Enquiries 20 percent up', {'enq_change': 0.2}), ('Enquiries 30 percent down', {'enq_change': -0.3}), ('No waiting families start', {'waiting': 0}))))
assert len(tools) == 18, len(tools)
