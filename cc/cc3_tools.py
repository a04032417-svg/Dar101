"""Childcare center suite part 3: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc3_lists import *
import cc3_data as D


def DT(s): y, m, d = s.split('-'); return '=DATE(%d,%d,%d)' % (int(y), int(m), int(d))
def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, default_label): return IN(k, label, 'list', key(lst, default_label), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def RG(t, c): return '{range:%s.%s}' % (t, c)
def RT(x): return '=' + tok('room', x)
def RAT(room): return 'SUMIFS(%s,%s,%s)' % (RG('rooms', 'ratio'), RG('rooms', 'room'), room)
INF = tok('room', 'Infants'); MS = 'DATE(YEAR({today}),MONTH({today}),1)'; ONC = '(1+{set:employer_cost_pct})'
RELIEF = tok('shiftkind', 'Relief'); ROLE_AD = tok('payrole', 'Assistant director'); ROLE_OWN = tok('payrole', 'Owner-director')
def NEED(n, ratio, room): return 'IF(%s<=0,0,MAX(ROUNDUP(%s/%s,0),IF(AND(%s=%s,%s>=3),{set:infants_min_staff},1)))' % (n, n, ratio, room, INF, n)
NEXT_WED = (D.iso_d(ST := D.ST['ratio_date']) + D.dt.timedelta(days=7)).isoformat()
tools = []

# 1 ratio by hour
tools.append(TOOL('ratio_hour', 'Ratio by Hour per Room', 'Is the room covered at this hour, and is the ratio right',
    'Pick a room and an hour, type the children counted, the staff present and the ratio for the room (check your local rules): see the staff needed, the gap and how often this room was short in the last 30 days.', [
    IL('room', 'Room', 'room', 'Toddlers'), IL('hour', 'Hour', 'hourl', '13:00'), I('children', 'Children counted', 7), I('staff', 'Staff present', 1), I('ratio', 'Children per staff, check your local rules', 6)], [
    O('Staff needed', 'int', NEED('{in:children}', '{in:ratio}', '{in:room}')), O('Staff present', 'int', '{in:staff}'), O('Gap, above 0 is short', 'int', '%s-{in:staff}' % NEED('{in:children}', '{in:ratio}', '{in:room}')),
    O('Children the staff present may care for', 'int', '{in:staff}*{in:ratio}'), O('Children above that', 'int', 'MAX(0,{in:children}-{in:staff}*{in:ratio})'),
    O('Short room-hours of this room, last 30 days', 'int', 'SUMIFS(%s,%s,{in:room},%s,">"&({today}-30))' % (RG('ratio', 'short_flag'), RG('ratio', 'room'), RG('ratio', 'date'))),
    O('Share of this room\'s hours covered, last 30 days', 'pct', 'IFERROR(1-SUMIFS(%s,%s,{in:room},%s,">"&({today}-30))/COUNTIFS(%s,{in:room},%s,">"&({today}-30)),0)' % (RG('ratio', 'short_flag'), RG('ratio', 'room'), RG('ratio', 'date'), RG('ratio', 'room'), RG('ratio', 'date'))),
    O('Average staff present at this hour in your log', 'num', 'SUMIFS(%s,%s,{in:room},%s,{in:hour})' % (RG('staff_hour', 'avg_present'), RG('staff_hour', 'room'), RG('staff_hour', 'hour'))),
    O('Verdict', 'text', 'IF(%s-{in:staff}>0,%s&" "&(%s-{in:staff}),IF(%s-{in:staff}<0,%s&" "&({in:staff}-%s),%s))' % (
        NEED('{in:children}', '{in:ratio}', '{in:room}'), vd('Short by'), NEED('{in:children}', '{in:ratio}', '{in:room}'), NEED('{in:children}', '{in:ratio}', '{in:room}'), vd('Over-staffed by'), NEED('{in:children}', '{in:ratio}', '{in:room}'), vd('Covered')))],
    GR('What if', ('Two staff present', {'staff': 2}), ('Infants, 5 children, 2 staff', {'room': RT('Infants'), 'children': 5, 'staff': 2, 'ratio': 4}), ('Infants, 4 children, 1 staff', {'room': RT('Infants'), 'children': 4, 'staff': 1, 'ratio': 4}),
       ('Preschool, 21 children, 2 staff', {'room': RT('Preschool'), 'children': 21, 'staff': 2, 'ratio': 10}), ('Ratio of 5 for Toddlers', {'ratio': 5}))))

# 2 cover heat map ranker
HM = lambda extra='': 'SUMIFS(%s,%s,">="&({today}-7*{in:weeks})%s)' % (RG('heat', 'slots_short'), RG('heat', 'week'), extra)
RK = lambda n, c: 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"")' % (RG('heat', c), n, RG('heat', 'rank'))
tools.append(TOOL('cover_rank', 'Cover Heat Map Ranker', 'Where relief hours are needed first',
    'Pick a room and a window in weeks: see the short room-hours of the room and of the center, the three room-weeks that were shortest ranked, the weekly total and where relief hours belong.', [
    IL('room', 'Room', 'room', 'Toddlers'), I('weeks', 'Weeks to look back', 13)], [
    O('Short room-hours in the window, all rooms', 'int', HM()), O('Short room-hours of this room', 'int', HM(',%s,{in:room}' % RG('heat', 'room'))), O('Relief hours needed a week, all rooms', 'num', 'IFERROR(%s/{in:weeks},0)' % HM()),
    O('Weekly short room-hours, latest week', 'int', 'SUMIFS(%s,%s,MAX(%s))' % (RG('weeks', 'short_hours'), RG('weeks', 'week'), RG('weeks', 'week'))),
    O('Rank 1 room', 'text', RK(1, 'room')), O('Rank 1 week', 'date', RK(1, 'week')), O('Rank 1 slots short', 'int', RK(1, 'slots_short')),
    O('Rank 2 room', 'text', RK(2, 'room')), O('Rank 2 week', 'date', RK(2, 'week')), O('Rank 2 slots short', 'int', RK(2, 'slots_short')),
    O('Rank 3 room', 'text', RK(3, 'room')), O('Rank 3 slots short', 'int', RK(3, 'slots_short')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (HM(), vd('No relief needed'), vd('Hire relief hours for'), RK(1, 'room')))],
    GR('What if', ('Look back 4 weeks', {'weeks': 4}), ('Look back 8 weeks', {'weeks': 8}), ('Look back 2 weeks', {'weeks': 2}), ('Infants room', {'room': RT('Infants')}), ('Preschool room, 26 weeks', {'room': RT('Preschool'), 'weeks': 26}))))

# 3 break planner
BP = lambda c: RG('break_plan', c)
def BK(c, n): return 'IFERROR(INDEX(%s,MATCH(%s&%d,%s,0))&"","-")' % (BP(c), KEY1, n, BP('clash_key'))
KEY1 = '{in:date}&"|"&{in:room}&"|"'
tools.append(TOOL('break_tool', 'Break Planner', 'Do the planned breaks leave every room at ratio',
    'Pick a date and a room: see the breaks planned, the clashes where the staff left are fewer than the ratio needs, who clashes and a better break time. Clashes for the whole next week are shown at the end.', [
    I('date', 'Date', NEXT_WED, 'date'), IL('room', 'Room', 'room', 'Toddlers')], [
    O('Breaks planned in this room that day', 'int', 'COUNTIFS(%s,{in:date},%s,{in:room},%s,1)' % (BP('date'), BP('room'), BP('has_break'))),
    O('Clashes in this room that day', 'int', 'COUNTIFS(%s,{in:date},%s,{in:room},%s,1)' % (BP('date'), BP('room'), BP('clash'))),
    O('First clash, staff member', 'text', BK('staff', 1)), O('First clash, break start', 'time', 'IFERROR(INDEX(%s,MATCH(%s&1,%s,0)),"-")' % (BP('break_time'), KEY1, BP('clash_key'))),
    O('First clash, suggested time', 'text', BK('move_to', 1)), O('Second clash, staff member', 'text', BK('staff', 2)), O('Second clash, suggested time', 'text', BK('move_to', 2)),
    O('Long shifts with no break planned, next week', 'int', 'COUNTIFS(%s,%s)' % (BP('break_flag'), fl('Add a break'))), O('Clashes next week, all rooms', 'int', 'SUM(%s)' % BP('clash')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,{in:date},%s,{in:room},%s,1)=0,%s,COUNTIFS(%s,{in:date},%s,{in:room},%s,1)&" "&%s)' % (BP('date'), BP('room'), BP('clash'), vd('No clashes'), BP('date'), BP('room'), BP('clash'), vd('breaks to move')))],
    GR('What if', ('Twos that day', {'room': RT('Twos')}), ('Infants that day', {'room': RT('Infants')}), ('Preschool that day', {'room': RT('Preschool')}), ('The day before', {'date': DT((D.iso_d(NEXT_WED) - D.dt.timedelta(days=1)).isoformat())}), ('The day after', {'date': DT((D.iso_d(NEXT_WED) + D.dt.timedelta(days=1)).isoformat())}))))

# 4 cost per child-hour
WIN4 = '%s,">="&EDATE(%s,-({in:months}-1)),%s,"<="&%s' % (RG('cph', 'month'), MS, RG('cph', 'month'), MS)
def CR(r): return 'IFERROR(SUMIFS(%s,%s,%s,%s)/SUMIFS(%s,%s,%s,%s),0)' % (RG('cph', 'wages'), RG('cph', 'room'), r, WIN4, RG('cph', 'child_hours'), RG('cph', 'room'), r, WIN4)
C4 = CR('{in:room}')
CTR = 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (RG('cph', 'wages'), WIN4, RG('cph', 'child_hours'), WIN4)
RK4 = '1+' + '+'.join('(%s>%s)' % (CR(tok('room', r)), C4) for r in ROOMS)
tools.append(TOOL('cph_tool', 'Cost per Child-Hour by Room', 'Which room costs the most per child-hour',
    'Pick a room and a number of months: wages with on-costs over the child-hours attended give the cost per child-hour, ranked against the other rooms and the center. The dearest and cheapest room of this month come from your log.', [
    IL('room', 'Room', 'room', 'Infants'), I('months', 'Months to include', 3)], [
    O('Paid hours', 'num', 'SUMIFS(%s,%s,{in:room},%s)' % (RG('cph', 'paid_hours'), RG('cph', 'room'), WIN4)), O('Wages and on-costs', 'money', 'SUMIFS(%s,%s,{in:room},%s)' % (RG('cph', 'wages'), RG('cph', 'room'), WIN4)),
    O('Child-hours attended', 'num', 'SUMIFS(%s,%s,{in:room},%s)' % (RG('cph', 'child_hours'), RG('cph', 'room'), WIN4)), O('Cost per child-hour', 'money', 'ROUND(%s,2)' % C4), O('Center cost per child-hour', 'money', 'ROUND(%s,2)' % CTR),
    O('Against the center', 'money', 'ROUND(%s-%s,2)' % (C4, CTR)), O('Rank of this room this month, 1 is dearest', 'int', 'SUMIFS(%s,%s,{in:room},%s,%s)' % (RG('cph', 'rank_month'), RG('cph', 'room'), RG('cph', 'month'), MS)),
    O('Dearest room this month', 'text', 'IFERROR(INDEX(%s,MATCH(%s&"|1",%s,0)),"")' % (RG('cph', 'room'), MS, RG('cph', 'rank_key'))), O('Its cost per child-hour', 'money', 'SUMIFS(%s,%s,%s,%s,1)' % (RG('cph', 'cost_ch'), RG('cph', 'month'), MS, RG('cph', 'rank_month'))),
    O('Cheapest room this month', 'text', 'IFERROR(INDEX(%s,MATCH(%s&"|5",%s,0)),"")' % (RG('cph', 'room'), MS, RG('cph', 'rank_key'))),
    O('Verdict', 'text', 'IF({in:room}=IFERROR(INDEX(%s,MATCH(%s&"|1",%s,0)),""),%s,IF(%s>%s,%s,%s))' % (RG('cph', 'room'), MS, RG('cph', 'rank_key'), vd('Review the dearest room'), C4, CTR, v2('Above the center cost'), v2('At or below the center cost')))],
    GR('What if', ('Toddlers', {'room': RT('Toddlers')}), ('Twos', {'room': RT('Twos')}), ('Preschool', {'room': RT('Preschool')}), ('School-age', {'room': RT('School-age')}), ('Infants, 6 months', {'months': 6}))))

# 5 relief hire test
tools.append(TOOL('relief_test', 'Relief Hire Test', 'Hire relief, use part-timers or hold',
    'Type the short hours a week you must cover, the relief wage and the tuition you would turn away without cover: the relief cost a month is set against the tuition at risk, with your own 13-week history beside it.', [
    I('short', 'Short hours a week to cover', 12, 'num'), I('wage', 'Relief wage per hour', 15.5, 'money'), I('lost', 'Children you would turn away without cover', 2), I('rate', 'Weekly tuition per child', 340, 'money'), I('hire_from', 'Hours a week that justify a regular relief hire', 16, 'num')], [
    O('Relief cost a week', 'money', '{in:short}*{in:wage}*%s' % ONC), O('Relief cost a month', 'money', '{in:short}*{in:wage}*%s*52/12' % ONC), O('Tuition at risk a month', 'money', '{in:lost}*{in:rate}*52/12'),
    O('Tuition kept after relief cost, a month', 'money', '{in:lost}*{in:rate}*52/12-{in:short}*{in:wage}*%s*52/12' % ONC),
    O('Short hours a week at which relief costs as much as the tuition at risk', 'num', 'IFERROR({in:lost}*{in:rate}/({in:wage}*%s),0)' % ONC),
    O('Your own short room-hours a week, last 13 weeks', 'num', 'AVERAGE(%s)' % RG('weeks', 'short_hours')), O('Your own relief hours a week, last 13 weeks', 'num', 'SUM(%s)/COUNT(%s)' % (RG('weeks', 'relief_hours'), RG('weeks', 'relief_hours'))),
    O('Your own relief cost per hour', 'money', 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (RG('relief', 'cost'), RG('relief', 'kind'), RELIEF, RG('relief', 'hours'), RG('relief', 'kind'), RELIEF)),
    O('Verdict', 'text', 'IF({in:short}<=0,%s,IF({in:lost}*{in:rate}*52/12>{in:short}*{in:wage}*%s*52/12,IF({in:short}>={in:hire_from},%s,%s),%s))' % (vd('Hold'), ONC, vd('Hire relief'), vd('Use part-timers'), vd('Hold')))],
    GR('What if', ('Only 6 short hours', {'short': 6}), ('Short 20 hours', {'short': 20}), ('Relief wage 18', {'wage': 18}), ('No child turned away', {'lost': 0}), ('Four children turned away', {'lost': 4}))))

# 6 turnover and replacement cost
TUR_NOW = 'SUMIFS(%s,%s,%s)' % (RG('turnover', 'turnover_share'), RG('turnover', 'month'), MS)
REPL = '({in:advert}+{in:vac}/7*{in:relief_h}*{set:relief_wage}*%s+{in:train_h}*{set:relief_wage}*%s)' % (ONC, ONC)
YRC = 'SUMIFS(%s,%s,">"&EDATE(%s,-12))' % (RG('turnover', 'staff_cost'), RG('turnover', 'month'), MS)
tools.append(TOOL('turnover_tool', 'Turnover and Replacement Cost', 'What leavers cost and whether a raise pays back',
    'Type the leavers in a year and the headcount: the yearly turnover is set against your own history, a replacement is costed from advert, vacancy relief and training, and a raise for the people at risk is tested against it.', [
    I('leavers', 'Leavers in the last 12 months', 3), I('head', 'Average headcount', 11, 'num'), I('advert', 'Advert and interview cost for one hire', 120, 'money'), I('vac', 'Vacancy days until the hire starts', 26),
    I('relief_h', 'Relief hours a week while the post is empty', 20, 'num'), I('train_h', 'Training hours for the new person', 12, 'num'), I('group', 'People the raise would cover', 4), I('raise', 'Raise', 0.05, 'pct'), I('avoided', 'Leavers the raise would prevent a year', 2)], [
    O('Yearly turnover', 'pct', 'IFERROR({in:leavers}/{in:head},0)'), O('Your own yearly turnover now', 'pct', TUR_NOW), O('Your own yearly turnover a year ago', 'pct', 'SUMIFS(%s,%s,EDATE(%s,-12))' % (RG('turnover', 'turnover_share'), RG('turnover', 'month'), MS)),
    O('Cost of one replacement', 'money', REPL), O('Your own average replacement cost', 'money', 'AVERAGE(%s)' % RG('leavers', 'replacement_cost')), O('Replacement cost in a year', 'money', '{in:leavers}*%s' % REPL),
    O('Staff cost, last 12 months', 'money', YRC), O('Cost of the raise in a year', 'money', 'IFERROR({in:group}/{in:head}*%s*{in:raise},0)' % YRC), O('Replacement cost the raise would save', 'money', '{in:avoided}*%s' % REPL),
    O('Verdict', 'text', 'IF({in:avoided}*%s>IFERROR({in:group}/{in:head}*%s*{in:raise},0),%s,%s)' % (REPL, YRC, vd('Raise pays back'), vd('Raise does not pay back')))],
    GR('What if', ('Raise of 2 percent', {'raise': 0.02}), ('Raise of 2 percent, 1 person', {'raise': 0.02, 'group': 1, 'avoided': 1}), ('Two leavers', {'leavers': 2}), ('Long vacancy of 60 days', {'vac': 60}), ('No relief during the gap', {'relief_h': 0}))))

# 7 renewals and training register
tools.append(TOOL('register_tool', 'Renewals and Training Register', 'Who has a renewal or training gap',
    'Pick a person: see the open renewals, the next due date and days left, training hours done and still needed this year and the cost. The center line counts renewals due in 30, 45 and 60 days and any overdue; status and dates only.', [
    IL('person', 'Staff member', 'staff', 'Camille Fontaine')], [
    O('Open renewals of this person', 'int', 'COUNTIFS(%s,{in:person},%s,1)' % (RG('renewals', 'holder'), RG('renewals', 'open_flag'))),
    O('Next due date', 'date', 'IFERROR(SUMIFS(%s,%s,{in:person},%s,1),"")' % (RG('renewals', 'due_date'), RG('renewals', 'holder'), RG('renewals', 'person_rank'))), O('Days left', 'int', 'IFERROR(SUMIFS(%s,%s,{in:person},%s,1)-{today},"")' % (RG('renewals', 'due_date'), RG('renewals', 'holder'), RG('renewals', 'person_rank'))),
    O('Cost of the open renewals', 'money', 'SUMIFS(%s,%s,{in:person},%s,1)' % (RG('renewals', 'cost'), RG('renewals', 'holder'), RG('renewals', 'open_flag'))),
    O('Training hours done this year', 'num', 'SUMIFS(%s,%s,{in:person},%s,1)' % (RG('train_year', 'done'), RG('train_year', 'staff'), RG('train_year', 'this_year'))),
    O('Training hours still needed this year', 'num', 'SUMIFS(%s,%s,{in:person},%s,1)' % (RG('train_year', 'needed'), RG('train_year', 'staff'), RG('train_year', 'this_year'))),
    O('Training cost this year', 'money', 'SUMIFS(%s,%s,{in:person},%s,1)' % (RG('train_year', 'cost'), RG('train_year', 'staff'), RG('train_year', 'this_year'))),
    O('Center: due in 30 days', 'int', 'COUNTIFS(%s,%s)' % (RG('renewals', 'band'), fl('Due in 30 days'))), O('Center: due in 31 to 45 days', 'int', 'COUNTIFS(%s,%s)' % (RG('renewals', 'band'), fl('Due in 45 days'))),
    O('Center: due in 46 to 60 days', 'int', 'COUNTIFS(%s,%s)' % (RG('renewals', 'band'), fl('Due in 60 days'))), O('Center: overdue', 'int', 'COUNTIFS(%s,%s)' % (RG('renewals', 'band'), fl('Overdue'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)>0,COUNTIFS(%s,%s)&" "&%s,IF(SUM(%s)>0,SUM(%s)&" "&%s,%s))' % (RG('renewals', 'band'), fl('Overdue'), RG('renewals', 'band'), fl('Overdue'), vd('overdue'), RG('renewals', 'warn_flag'), RG('renewals', 'warn_flag'), vd('due soon'), vd('All current')))],
    GR('What if', ('Hana Sato', {'person': '=' + tok('staff', 'Hana Sato')}), ('Zainab Khalid', {'person': '=' + tok('staff', 'Zainab Khalid')}), ('Ibrahim Diallo', {'person': '=' + tok('staff', 'Ibrahim Diallo')}), ('Marisol Vega', {'person': '=' + tok('staff', 'Marisol Vega')}), ('Ngozi Eze', {'person': '=' + tok('staff', 'Ngozi Eze')}))))

# 8 rota builder
RD = lambda h: 'SUMPRODUCT((%s={in:room})*(%s={in:date})*(ROUND(%s*24,2)<=%s)*(ROUND(%s*24,2)>%s))-SUMPRODUCT((%s={in:room})*(%s={in:date})*(ROUND(%s*24,2)=%s))' % (
    RG('rota', 'room'), RG('rota', 'date'), RG('rota', 'start'), h, RG('rota', 'end'), h, RG('rota', 'room'), RG('rota', 'date'), RG('rota', 'break_start'), h)
H8 = 'VALUE(LEFT({in:hour},2))'
NEED8 = 'SUMIFS(%s,%s,{in:room})' % (RG('staff_hour', 'needed_avg'), RG('staff_hour', 'room')); ROS8 = 'SUMIFS(%s,%s,{in:date},%s,{in:room})' % (RG('rota', 'hours'), RG('rota', 'date'), RG('rota', 'room'))
tools.append(TOOL('rota_tool', 'Rota Builder', 'Does next week\'s rota cover the children expected',
    'Pick a date, room and hour of next week: the staff needed come from your average children by hour and the room ratio, and are compared with the staff-hours rostered; the verdict says how many shifts to add.', [
    I('date', 'Date', NEXT_WED, 'date'), IL('room', 'Room', 'room', 'Toddlers'), IL('hour', 'Hour', 'hourl', '13:00'), I('shift', 'Hours in a shift you would add', 8, 'num')], [
    O('Staff-hours needed that day', 'num', NEED8), O('Staff-hours rostered that day', 'num', ROS8), O('Rostered against needed', 'num', '%s-%s' % (ROS8, NEED8)), O('Shifts to add', 'int', 'MAX(IF(%s<SUMIFS(%s,%s,{in:room},%s,%s),1,0),ROUNDUP((%s-%s-1)/{in:shift},0))' % (RD(H8), RG('staff_hour', 'needed_avg'), RG('staff_hour', 'room'), RG('staff_hour', 'hour_no'), H8, NEED8, ROS8)),
    O('Children expected at that hour', 'num', 'SUMIFS(%s,%s,{in:room},%s,%s)' % (RG('staff_hour', 'avg_children'), RG('staff_hour', 'room'), RG('staff_hour', 'hour_no'), H8)),
    O('Staff needed at that hour', 'int', 'SUMIFS(%s,%s,{in:room},%s,%s)' % (RG('staff_hour', 'needed_avg'), RG('staff_hour', 'room'), RG('staff_hour', 'hour_no'), H8)),
    O('Staff rostered at that hour after breaks', 'int', RD(H8)),
    O('Verdict', 'text', 'IF(AND(%s-%s<=1,%s>=SUMIFS(%s,%s,{in:room},%s,%s)),%s,MAX(IF(%s<SUMIFS(%s,%s,{in:room},%s,%s),1,0),ROUNDUP((%s-%s-1)/{in:shift},0))&" "&%s)' % (
        NEED8, ROS8, RD(H8), RG('staff_hour', 'needed_avg'), RG('staff_hour', 'room'), RG('staff_hour', 'hour_no'), H8, vd('Rota covers'),
        RD(H8), RG('staff_hour', 'needed_avg'), RG('staff_hour', 'room'), RG('staff_hour', 'hour_no'), H8, NEED8, ROS8, vd('Add shifts')))],
    GR('What if', ('Infants that day', {'room': RT('Infants')}), ('Twos that day', {'room': RT('Twos')}), ('Preschool at 8 am', {'room': RT('Preschool'), 'hour': '=' + tok('hourl', '08:00')}), ('Toddlers at 3 pm', {'hour': '=' + tok('hourl', '15:00')}), ('Shifts of 6 hours', {'shift': 6}))))

# 9 overtime and hours cap
HWV = lambda c: 'SUMIFS(%s,%s,{in:person},%s,{in:week})' % (RG('hours_week', c), RG('hours_week', 'staff'), RG('hours_week', 'week'))
RATE9 = 'IF(SUMIFS(%s,%s,{in:person})=0,{set:mgmt_rate},SUMIFS(%s,%s,{in:person}))' % (RG('team', 'hourly_rate'), RG('team', 'name'), RG('team', 'hourly_rate'), RG('team', 'name'))
tools.append(TOOL('cap_tool', 'Overtime and Hours Cap Checker', 'Is anyone over the weekly hours cap',
    'Pick a person and a week and type your cap on weekly hours (check your local rules): see the hours rostered, the hours over contract, the cost of those hours and how often the person went over the cap in 13 weeks.', [
    IL('person', 'Staff member', 'staff', 'Tobias Lindgren'), I('week', 'Week (Monday)', D.WEEKS[2], 'date'), I('cap', 'Most hours in a week', 45, 'num')], [
    O('Hours rostered that week', 'num', HWV('rostered')), O('Contract hours', 'num', HWV('contract')), O('Hours over contract', 'num', HWV('over_hours')), O('Hours over the cap', 'num', 'MAX(0,%s-{in:cap})' % HWV('rostered')),
    O('Cost of the hours over contract', 'money', '%s*%s*%s' % (HWV('over_hours'), RATE9, ONC)), O('Weeks over the cap, last 13', 'int', 'COUNTIFS(%s,{in:person},%s,">"&{in:cap})' % (RG('hours_week', 'staff'), RG('hours_week', 'rostered'))),
    O('Average weekly hours, last 13 weeks', 'num', 'AVERAGEIFS(%s,%s,{in:person})' % (RG('hours_week', 'rostered'), RG('hours_week', 'staff'))), O('People over the cap that week', 'int', 'COUNTIFS(%s,{in:week},%s,">"&{in:cap})' % (RG('hours_week', 'week'), RG('hours_week', 'rostered'))),
    O('Verdict', 'text', 'IF(%s>{in:cap},%s&" "&ROUND(%s-{in:cap},1),%s)' % (HWV('rostered'), vd('Over the cap by'), HWV('rostered'), vd('Within the cap')))],
    GR('What if', ('Cap of 50 hours', {'cap': 50}), ('Cap of 40 hours', {'cap': 40}), ('Hana Sato, last week', {'person': '=' + tok('staff', 'Hana Sato'), 'week': DT(D.WEEKS[-1])}), ('Camille Fontaine', {'person': '=' + tok('staff', 'Camille Fontaine')}), ('Sofia Petrova, last week', {'person': '=' + tok('staff', 'Sofia Petrova'), 'week': DT(D.WEEKS[-1])}))))

# 10 shift swap checker
def PR(room, h): return 'SUMPRODUCT((%s=%s)*(%s={in:date})*((ROUND(%s*24,2)<=%s)*(ROUND(%s*24,2)>%s)-(ROUND(%s*24,2)=%s)))' % (
    RG('rota', 'room'), room, RG('rota', 'date'), RG('rota', 'start'), h, RG('rota', 'end'), h, RG('rota', 'break_start'), h)
def COV(s, e, b, h): return '(({in:%s}<=%s)*({in:%s}>%s)*({in:%s}<>%s))' % (s, h, e, h, b, h)
def NH(room, h): return 'SUMIFS(%s,%s,%s,%s,%s)' % (RG('staff_hour', 'needed_avg'), RG('staff_hour', 'room'), room, RG('staff_hour', 'hour_no'), h)
def MARGIN(side, h):
    me, other = ('a', 'b') if side == 'a' else ('b', 'a')
    room = '{in:room_%s}' % me
    return '(%s-%s+%s-%s)' % (PR(room, '{in:%s}' % h), COV('s' + me, 'e' + me, 'b' + me, '{in:%s}' % h), COV('s' + other, 'e' + other, 'b' + other, '{in:%s}' % h), NH(room, '{in:%s}' % h))
HRS = ['h1', 'h2']
BELOW = '+'.join('(%s<0)' % MARGIN(s, h) for s in ('a', 'b') for h in HRS)
tools.append(TOOL('swap_tool', 'Shift Swap Checker', 'Is a swap of two shifts safe for the ratio',
    'Type the two shifts (room, start, end and break hour) and two hours to check: the staff of shift A move to room B and the staff of shift B to room A; each room is compared with the staff your average children need.', [
    I('date', 'Date', NEXT_WED, 'date'), IL('room_a', 'Room of shift A', 'room', 'Toddlers'), I('sa', 'Shift A starts at hour', 8), I('ea', 'Shift A ends at hour', 17), I('ba', 'Shift A break hour', 13),
    IL('room_b', 'Room of shift B', 'room', 'Twos'), I('sb', 'Shift B starts at hour', 8), I('eb', 'Shift B ends at hour', 16), I('bb', 'Shift B break hour', 12), I('h1', 'Hour to check 1', 12), I('h2', 'Hour to check 2', 13)], [
    O('Room A, spare staff at hour 1 after the swap', 'int', MARGIN('a', 'h1')), O('Room A, spare staff at hour 2 after the swap', 'int', MARGIN('a', 'h2')),
    O('Room B, spare staff at hour 1 after the swap', 'int', MARGIN('b', 'h1')), O('Room B, spare staff at hour 2 after the swap', 'int', MARGIN('b', 'h2')),
    O('Room-hours below the ratio after the swap, of 4 checked', 'int', BELOW),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (BELOW, vd('Swap is safe'), vd('Swap breaks the ratio')))],
    GR('What if', ('Swap Twos with Preschool', {'room_b': RT('Preschool')}), ('Shift B ends at 12', {'eb': 12}), ('Shift A without a break', {'ba': 0}), ('Check 3 pm and 4 pm', {'h1': 15, 'h2': 16}), ('Infants with Toddlers', {'room_a': RT('Infants'), 'room_b': RT('Toddlers')}))))

# 11 floater placement ranker
PL = lambda n, c: 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"")' % (RG('staff_hour', c), n, RG('staff_hour', 'place_rank'))
tools.append(TOOL('floater_tool', 'Floater Placement Ranker', 'Where one more floater hour helps most',
    'Type the floater hours you have a week and their wage: every room-hour is ranked by the share of days it was short and then by days with no spare staff; the top slot is where the floater goes.', [
    I('hours', 'Floater hours available a week', 10, 'num'), I('wage', 'Floater wage per hour', 15.5, 'money')], [
    O('Rank 1 room', 'text', PL(1, 'room')), O('Rank 1 hour', 'text', PL(1, 'hour')), O('Rank 1, share of days short', 'pct', PL(1, 'short_share')), O('Rank 1, share of days with no spare staff', 'pct', PL(1, 'tight_share')),
    O('Rank 2 room', 'text', PL(2, 'room')), O('Rank 2 hour', 'text', PL(2, 'hour')), O('Rank 2, share of days with no spare staff', 'pct', PL(2, 'tight_share')),
    O('Rank 3 room', 'text', PL(3, 'room')), O('Rank 3 hour', 'text', PL(3, 'hour')), O('Floater cost a week', 'money', '{in:hours}*{in:wage}*%s' % ONC),
    O('Days a week the floater can fill the top slot', 'int', 'MIN(5,ROUNDDOWN({in:hours},0))'),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&" "&%s' % (vd('Place the floater in'), PL(1, 'room'), v2('at'), PL(1, 'hour')))],
    GR('What if', ('20 floater hours', {'hours': 20}), ('5 floater hours', {'hours': 5}), ('Wage of 18', {'wage': 18}), ('No hours', {'hours': 0}), ('Wage of 14', {'wage': 14}))))

# 12 management cover cost
MG = 'SUMIFS(%s,%s,%s,%s,">"&({today}-{in:days}))+SUMIFS(%s,%s,%s,%s,">"&({today}-{in:days}))' % (RG('shifts', 'hours'), RG('shifts', 'role'), ROLE_AD, RG('shifts', 'date'), RG('shifts', 'hours'), RG('shifts', 'role'), ROLE_OWN, RG('shifts', 'date'))
tools.append(TOOL('mgmt_tool', 'Management Cover Cost', 'What it costs when management covers a room',
    'Type the days to look back and the imputed rate for the assistant director and owner-director: the hours they covered rooms are costed, compared with relief wages, and the verdict says whether relief is cheaper.', [
    I('days', 'Days to look back', 30), I('rate', 'Imputed hourly rate', 20.8, 'money'), I('relief', 'Relief wage per hour', 15.5, 'money')], [
    O('Management hours in rooms', 'num', MG), O('Hours a week', 'num', 'IFERROR((%s)/{in:days}*7,0)' % MG), O('Imputed cost', 'money', '(%s)*{in:rate}*%s' % (MG, ONC)), O('Imputed cost a month', 'money', 'IFERROR((%s)*{in:rate}*%s/{in:days}*30,0)' % (MG, ONC)),
    O('Relief cost for the same hours', 'money', '(%s)*{in:relief}*%s' % (MG, ONC)), O('Saving a month with relief', 'money', 'IFERROR((%s)*({in:rate}-{in:relief})*%s/{in:days}*30,0)' % (MG, ONC)),
    O('Management hours, last 13 weeks', 'num', 'SUM(%s)' % RG('weeks', 'mgmt_hours')),
    O('Verdict', 'text', 'IF({in:rate}>{in:relief},%s,%s)' % (v2('Hire relief and stop cover'), v2('Cover is cheaper than relief')))],
    GR('What if', ('Look back 60 days', {'days': 60}), ('Look back 7 days', {'days': 7}), ('Relief wage 22', {'relief': 22}), ('Rate 16', {'rate': 16}), ('Look back 90 days', {'days': 90}))))

# 13 staff cost share
SC = lambda c, a, b: 'SUMIFS(%s,%s,">="&%s,%s,"<="&%s)' % (RG('turnover', c), RG('turnover', 'month'), a, RG('turnover', 'month'), b)
SH13 = 'IFERROR(SUMIFS(%s,%s,{in:month})/SUMIFS(%s,%s,{in:month}),0)' % (RG('turnover', 'staff_cost'), RG('turnover', 'month'), RG('turnover', 'revenue'), RG('turnover', 'month'))
tools.append(TOOL('share_tool', 'Staff Cost Share of Revenue', 'Is staff cost in line with revenue',
    'Pick a month and type your target share: staff cost over revenue is compared with your own last 12 months and the same month a year earlier, and the revenue needed to reach the target is shown.', [
    I('month', 'Month', D.month_start(1).isoformat(), 'date'), I('target', 'Target share, set your own', STAFF_SHARE_TARGET, 'pct')], [
    O('Staff cost', 'money', 'SUMIFS(%s,%s,{in:month})' % (RG('turnover', 'staff_cost'), RG('turnover', 'month'))), O('Revenue', 'money', 'SUMIFS(%s,%s,{in:month})' % (RG('turnover', 'revenue'), RG('turnover', 'month'))),
    O('Staff cost share', 'pct', SH13), O('Your own last 12 months', 'pct', 'IFERROR(%s/%s,0)' % (SC('staff_cost', 'EDATE({in:month},-11)', '{in:month}'), SC('revenue', 'EDATE({in:month},-11)', '{in:month}'))),
    O('Same month a year earlier', 'pct', 'IFERROR(SUMIFS(%s,%s,EDATE({in:month},-12))/SUMIFS(%s,%s,EDATE({in:month},-12)),0)' % (RG('turnover', 'staff_cost'), RG('turnover', 'month'), RG('turnover', 'revenue'), RG('turnover', 'month'))),
    O('Points above or below the target', 'pct', '%s-{in:target}' % SH13), O('Revenue needed to reach the target at this cost', 'money', 'IFERROR(SUMIFS(%s,%s,{in:month})/{in:target},0)' % (RG('turnover', 'staff_cost'), RG('turnover', 'month'))),
    O('Staff cost the target allows at this revenue', 'money', 'SUMIFS(%s,%s,{in:month})*{in:target}' % (RG('turnover', 'revenue'), RG('turnover', 'month'))),
    O('Verdict', 'text', 'IF(%s>{in:target}+0.02,%s,IF(%s<{in:target}-0.02,%s,%s))' % (SH13, vd('Above the target'), SH13, vd('Below the target'), vd('Near the target')))],
    GR('What if', ('Target 60 percent', {'target': 0.6}), ('Target 66 percent', {'target': 0.66}), ('Two months back', {'month': DT(D.month_start(2).isoformat())}), ('Six months back', {'month': DT(D.month_start(6).isoformat())}), ('A year back', {'month': DT(D.month_start(12).isoformat())}))))

# 14 training budget and hours gap
TY = lambda c, extra='': 'SUMIFS(%s,%s,1%s)' % (RG('train_year', c), RG('train_year', 'this_year'), extra)
BEL = 'COUNTIFS(%s,1,%s,"<"&{in:target})' % (RG('train_year', 'this_year'), RG('train_year', 'done'))
NEEDH = '(%s*{in:target}-%s)' % (BEL, TY('done', ',%s,"<"&{in:target}' % RG('train_year', 'done')))
tools.append(TOOL('train_tool', 'Training Budget and Hours Gap', 'Are staff on track for the yearly training hours',
    'Type your yearly target and the cost per training hour: the hours still needed by everyone below target, the budget, the pace needed for the months left and your own pace so far.', [
    I('target', 'Training hours a year per person', CPD_TARGET_HOURS), I('cost', 'Cost per training hour', 8, 'money')], [
    O('Staff below the target', 'int', BEL), O('Hours still needed', 'num', NEEDH), O('Budget for those hours', 'money', '%s*{in:cost}' % NEEDH), O('Training hours done this year', 'num', TY('done')),
    O('Training cost this year so far', 'money', TY('cost')), O('Months left this year', 'int', '12-MONTH({today})'), O('Hours a month needed to close the gap', 'num', 'IFERROR(%s/MAX(1,12-MONTH({today})),0)' % NEEDH),
    O('Your own pace, hours per person a year', 'num', 'IFERROR(%s/COUNTIFS(%s,1)/MONTH({today})*12,0)' % (TY('done'), RG('train_year', 'this_year')), ),
    O('Verdict', 'text', 'IF(IFERROR(%s/COUNTIFS(%s,1)/MONTH({today})*12,0)>={in:target},%s,%s)' % (TY('done'), RG('train_year', 'this_year'), vd('On track'), vd('Behind')))],
    GR('What if', ('Target 10 hours', {'target': 10}), ('Target 20 hours', {'target': 20}), ('Cost 12 an hour', {'cost': 12}), ('Target 8 hours', {'target': 8}), ('Cost 5 an hour', {'cost': 5}))))

# 15 hiring lead-time planner
LEAD = '({in:advert}+{in:interview}+{in:prep})'
tools.append(TOOL('hire_tool', 'Hiring Lead-time Planner', 'When to advertise so the room is never short',
    'Type the date notice was given and the notice days: the last day, the days an advert, interviews and preparation take, and the vacancy and relief cost if you wait; the verdict says to advertise now or wait.', [
    I('notice_on', 'Notice given on', D.ago(10), 'date'), I('notice', 'Days of notice', 30), I('advert', 'Days the advert runs', 14), I('interview', 'Days for interviews and offer', 10), I('prep', 'Days of checks before the first day', 7), I('relief_h', 'Relief hours a week while the post is empty', 20, 'num')], [
    O('Last day of the staff member', 'date', '{in:notice_on}+{in:notice}'), O('Days needed to hire', 'int', LEAD), O('Latest date to start advertising', 'date', '{in:notice_on}+{in:notice}-%s' % LEAD),
    O('Days from today until then', 'int', '{in:notice_on}+{in:notice}-%s-{today}' % LEAD), O('Vacancy days if you start today', 'int', 'MAX(0,{today}+%s-({in:notice_on}+{in:notice}))' % LEAD),
    O('Relief cost of that vacancy', 'money', 'MAX(0,{today}+%s-({in:notice_on}+{in:notice}))/7*{in:relief_h}*{set:relief_wage}*%s' % (LEAD, ONC)), O('Your own average vacancy days a leaver', 'num', 'IFERROR(SUM(%s)/SUM(%s),0)' % (RG('turnover', 'vacancy_days'), RG('turnover', 'leavers'))),
    O('Verdict', 'text', 'IF({in:notice_on}+{in:notice}-%s<={today},%s,%s)' % (LEAD, vd('Advertise now'), v2('Wait')))],
    GR('What if', ('Notice given today', {'notice_on': '={today}'}), ('Notice of 60 days', {'notice': 60}), ('Short advert of 7 days', {'advert': 7}), ('Long checks of 14 days', {'prep': 14}), ('Notice of 90 days', {'notice': 90}))))

# 16 pay-run check
PM = lambda c, extra='': 'SUMIFS(%s,%s,{in:month}%s)' % (RG('payroll', c), RG('payroll', 'month'), extra)
tools.append(TOOL('payrun_tool', 'Pay-run Check', 'Does the pay run match the shifts',
    'Pick a month: hourly pay in the payroll rows is compared with the wages and on-costs the shifts give, row by row with your tolerance from the start settings; the verdict says whether the pay run matches.', [
    I('month', 'Month', D.month_start(1).isoformat(), 'date')], [
    O('Payroll rows in the month', 'int', 'COUNTIFS(%s,{in:month})' % RG('payroll', 'month')), O('Hourly rows', 'int', 'COUNTIFS(%s,{in:month},%s,%s)' % (RG('payroll', 'month'), RG('payroll', 'pay_type'), tok('paytype', 'Hourly'))),
    O('Hourly pay in the payroll', 'money', PM('total', ',%s,%s' % (RG('payroll', 'pay_type'), tok('paytype', 'Hourly')))), O('Wages and on-costs in the shifts', 'money', 'SUMIFS(%s,%s,{in:month})' % (RG('shifts', 'cost'), RG('shifts', 'month'))),
    O('Difference', 'money', '%s-SUMIFS(%s,%s,{in:month})' % (PM('total', ',%s,%s' % (RG('payroll', 'pay_type'), tok('paytype', 'Hourly'))), RG('shifts', 'cost'), RG('shifts', 'month'))),
    O('Hours in the payroll, hourly rows', 'num', PM('hours', ',%s,%s' % (RG('payroll', 'pay_type'), tok('paytype', 'Hourly')))), O('Hours in the shifts, hourly staff', 'num', 'SUMIFS(%s,%s,{in:month},%s,">0")' % (RG('shifts', 'hours'), RG('shifts', 'month'), RG('shifts', 'rate'))),
    O('Rows that differ', 'int', 'COUNTIFS(%s,{in:month},%s,%s)' % (RG('payroll', 'month'), RG('payroll', 'check_flag'), fl('Differs'))), O('Total payroll cost including owner draw', 'money', PM('total')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,{in:month},%s,%s)=0,%s,COUNTIFS(%s,{in:month},%s,%s)&" "&%s)' % (RG('payroll', 'month'), RG('payroll', 'check_flag'), fl('Differs'), v2('Pay matches'), RG('payroll', 'month'), RG('payroll', 'check_flag'), fl('Differs'), v2('rows differ')))],
    GR('What if', ('Two months back', {'month': DT(D.month_start(2).isoformat())}), ('Three months back', {'month': DT(D.month_start(3).isoformat())}), ('Four months back', {'month': DT(D.month_start(4).isoformat())}), ('Five months back', {'month': DT(D.month_start(5).isoformat())}), ('Six months back', {'month': DT(D.month_start(6).isoformat())}))))

# 17 contract hours fit
HWA = lambda extra='': 'AVERAGEIFS(%s,%s,{in:person},%s,">="&({today}-7*{in:weeks})%s)' % (RG('hours_week', 'rostered'), RG('hours_week', 'staff'), RG('hours_week', 'week'), extra)
CON = 'SUMIFS(%s,%s,{in:person})' % (RG('team', 'hours_week'), RG('team', 'name'))
tools.append(TOOL('contract_tool', 'Contract Hours Fit', 'Do rostered hours fit the contract',
    'Pick a person and a window in weeks: the average rostered hours are set against the contract hours with your tolerance from the start settings, and the weeks over and under contract are counted.', [
    IL('person', 'Staff member', 'staff', 'Hana Sato'), I('weeks', 'Weeks to look back', 13)], [
    O('Contract hours a week', 'num', CON), O('Average rostered hours a week', 'num', 'IFERROR(%s,0)' % HWA()), O('Share of contract hours', 'pct', 'IFERROR(%s/%s,0)' % (HWA(), CON)), O('Hours a week above or below contract', 'num', 'IFERROR(%s-%s,0)' % (HWA(), CON)),
    O('Weeks over contract', 'int', 'COUNTIFS(%s,{in:person},%s,%s,%s,">="&({today}-7*{in:weeks}))' % (RG('hours_week', 'staff'), RG('hours_week', 'fit_flag'), fl('Over contract'), RG('hours_week', 'week'))),
    O('Weeks under contract', 'int', 'COUNTIFS(%s,{in:person},%s,%s,%s,">="&({today}-7*{in:weeks}))' % (RG('hours_week', 'staff'), RG('hours_week', 'fit_flag'), fl('Under contract'), RG('hours_week', 'week'))),
    O('Weeks counted', 'int', 'COUNTIFS(%s,{in:person},%s,">="&({today}-7*{in:weeks}))' % (RG('hours_week', 'staff'), RG('hours_week', 'week'))),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,1)>1+{set:contract_tolerance},%s,IF(IFERROR(%s/%s,1)<1-{set:contract_tolerance},%s,%s))' % (HWA(), CON, v2('Over-used'), HWA(), CON, v2('Under-used'), v2('Fits')))],
    GR('What if', ('Sofia Petrova', {'person': '=' + tok('staff', 'Sofia Petrova')}), ('Camille Fontaine', {'person': '=' + tok('staff', 'Camille Fontaine')}), ('Joao Barbosa', {'person': '=' + tok('staff', 'Joao Barbosa')}), ('Hana Sato, 4 weeks', {'weeks': 4}), ('Tobias Lindgren', {'person': '=' + tok('staff', 'Tobias Lindgren')}))))

# 18 rota with more children
SC18 = lambda c: 'SUMIFS(%s,%s,{in:room})' % (RG('staff_hour', c), RG('staff_hour', 'room'))
NEW18 = 'IF({in:scenario}=%s,%s,IF({in:scenario}=%s,%s,%s))' % (tok('scenario', 'Best'), SC18('need_best'), tok('scenario', 'Worst'), SC18('need_worst'), SC18('need_base'))
NOW18 = SC18('needed_avg')
tools.append(TOOL('more_children', 'Rota with More Children', 'What extra children do to the rota',
    'Pick a room and a scenario (Base adds the children set on the start sheet, Best about a third fewer, Worst two thirds more): the staff needed each hour is recalculated at the room ratio and the extra staff-hours and cost a month are shown.', [
    IL('room', 'Room', 'room', 'Toddlers'), IL('scenario', 'Scenario', 'scenario', 'Base'), I('wage', 'Staff wage per hour', 16, 'money')], [
    O('Extra children in this scenario', 'int', 'IF({in:scenario}=%s,ROUND({set:extra_children}*0.67,0),IF({in:scenario}=%s,ROUND({set:extra_children}*1.67,0),{set:extra_children}))' % (tok('scenario', 'Best'), tok('scenario', 'Worst'))),
    O('Staff-hours needed a day now', 'num', NOW18), O('Staff-hours needed a day with the extra children', 'num', NEW18),
    O('Extra staff-hours a day', 'num', '%s-%s' % (NEW18, NOW18)), O('Extra staff-hours a month', 'num', '(%s-%s)*21.7' % (NEW18, NOW18)), O('Extra staff cost a month', 'money', '(%s-%s)*21.7*{in:wage}*%s' % (NEW18, NOW18, ONC)),
    O('Children per staff in the room, check your local rules', 'int', RAT('{in:room}')),
    O('Verdict', 'text', 'IF(%s-%s<=0,%s,%s&" "&ROUND(%s-%s,1))' % (NEW18, NOW18, v2('Current rota holds'), v2('Add staff hours'), NEW18, NOW18))],
    GR('What if', ('Best case', {'scenario': '=' + tok('scenario', 'Best')}), ('Worst case', {'scenario': '=' + tok('scenario', 'Worst')}), ('Infants', {'room': RT('Infants')}), ('Preschool, worst case', {'room': RT('Preschool'), 'scenario': '=' + tok('scenario', 'Worst')}), ('Twos', {'room': RT('Twos')}))))
assert len(tools) == 18, len(tools)
