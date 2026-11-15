"""Childcare center suite part 7: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc7_lists import *
import cc7_data as D


def DF(iso_s): return '=DATE(%d,%d,%d)' % tuple(int(x) for x in iso_s.split('-'))
def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, default_label): return IN(k, label, 'list', key(lst, default_label), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def RG(t, c): return '{range:%s.%s}' % (t, c)
def EQ(lst, label): return '=' + tok(lst, label)
ENR, LEFT = tok('cstatus', 'Enrolled'), tok('cstatus', 'Left')
REPL, AWAIT = tok('mstatus', 'Replied'), tok('mstatus', 'Awaiting reply')
HELD, BOOKED, NOSHOW = tok('confstatus', 'Held'), tok('confstatus', 'Booked'), tok('confstatus', 'No-show')
NEWS = tok('ekind', 'Newsletter')
BAS, SUMMER, HOLIDAY = tok('program', 'Before-after school'), tok('program', 'Summer camp'), tok('program', 'Holiday camp')
CV_RUN, CV_MIN, CV_CANCEL = tok('campverdict', 'Run'), tok('campverdict', 'Run with a minimum'), tok('campverdict', 'Cancel')
L30 = '">"&({today}-30),%s,"<="&{today}'
def D30(col): return '%s,">"&({today}-30),%s,"<="&{today}' % (col, col)

pw = lambda c: RG('program_weeks', c)
PWW = lambda col, w='{in:week}': 'SUMIFS(%s,%s,%s)' % (pw(col), pw('week'), w)
summer_weeks = [r for r in D.program_weeks_d() if r['program'] == key('program', 'Summer camp') and r['week'] >= ago(200)]
DEF_WEEK = next((r['week'] for r in summer_weeks if r['signups'] == 5), summer_weeks[-1]['week'])
DEF_WEEK6 = next((r['week'] for r in summer_weeks if r['signups'] == 6), summer_weeks[-1]['week'])
DEF_WEEK4 = next((r['week'] for r in summer_weeks if r['signups'] == 4), summer_weeks[-1]['week'])

tools = []

# 1 daily report and parent contact tracker
R1 = lambda col, extra='': 'COUNTIFS(%s,{in:room},%s%s)' % (RG('reports', 'room'), D30(RG('reports', 'date')), extra)
S1 = 'SUMIFS(%s,%s,{in:room},%s)' % (RG('reports', 'same_n'), RG('reports', 'room'), D30(RG('reports', 'date')))
ALL1 = 'IFERROR(SUMIFS(%s,%s)/COUNTIFS(%s),0)' % (RG('reports', 'same_n'), D30(RG('reports', 'date')), D30(RG('reports', 'date')))
SLOW1 = 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (RG('reports_room_month', 'room'), RG('reports_room_month', 'share30'), RG('reports_room_month', 'share30'))
UNH1 = 'COUNTIFS(%s,%s)' % (RG('comm_gaps', 'flag'), fl('Call this family'))
tools.append(TOOL('report_tracker', 'Report and Parent Contact', 'Daily report and parent contact tracker',
    'Pick a room: reports sent in the last 30 days and the share sent the same day, the slowest room, parent messages waiting and families with no contact. Status and counts only.', [
    IL('room', 'Room', 'room', 'Toddlers'), I('target', 'Share of reports sent the same day, your target', 0.90, 'pct')], [
    O('Reports sent, last 30 days', 'int', R1(0)), O('Sent the same day', 'int', S1), O('Share sent the same day', 'pct', 'IFERROR((%s)/%s,0)' % (S1, R1(0))), O('Sent next day', 'int', 'COUNTIFS(%s,{in:room},%s,%s,%s)' % (RG('reports', 'room'), D30(RG('reports', 'date')), RG('reports', 'sent_next_day'), YES)),
    O('All rooms, share sent the same day', 'pct', ALL1), O('Slowest room, last 30 days', 'text', SLOW1), O('Its share sent the same day', 'pct', 'MIN(%s)' % RG('reports_room_month', 'share30')),
    O('Parent messages waiting for a reply', 'int', 'COUNTIFS(%s,%s)' % (RG('parent_msgs', 'status'), AWAIT)), O('Oldest message waiting, hours', 'int', 'MAX(%s)' % RG('parent_msgs', 'wait_hours')),
    O('Families with no contact over the limit', 'int', UNH1),
    O('Verdict', 'text', 'IF(MIN(%s)<{in:target},%s&" "&%s,IF(%s>0,%s&" "&%s,%s))' % (RG('reports_room_month', 'share30'), SLOW1, vd('is behind'), UNH1, UNH1, vd('families unheard'), vd('on target')))],
    GR('What if', ('Infants', {'room': EQ('room', 'Infants')}), ('Twos', {'room': EQ('room', 'Twos')}), ('Preschool', {'room': EQ('room', 'Preschool')}), ('School-age', {'room': EQ('room', 'School-age')}), ('Target 99 percent', {'target': 0.99}))))

# 2 newsletter, event and conference planner
NE2 = 'SMALL(%s,COUNTIF(%s,"<="&{today})+1)' % (RG('events', 'fam_date'), RG('events', 'fam_date'))
DUE2 = 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+{in:days}))' % (RG('newsletter_plan', 'due_date'), RG('newsletter_plan', 'due_date'))
tools.append(TOOL('plan_tool', 'Newsletter and Event Planner', 'Newsletter, event and conference planner',
    'Type how many days ahead to look: the next newsletter and event, items you must start preparing, conference slots booked and free, families still without a slot and no-shows.', [
    I('days', 'Days ahead to look', 14)], [
    O('Next newsletter goes out', 'date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (RG('newsletter_plan', 'news_date'), RG('newsletter_plan', 'news_date'))),
    O('Next event date', 'date', 'IFERROR(%s,"")' % NE2), O('Next event kind', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (RG('events', 'kind'), NE2, RG('events', 'fam_date'))),
    O('Families invited to it', 'int', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (RG('events', 'invited'), NE2, RG('events', 'fam_date'))),
    O('Plan items to start preparing in the window', 'int', DUE2),
    O('Events planned, next 90 days, not newsletters', 'int', 'COUNTIFS(%s,">"&{today},%s,"<="&({today}+90))' % (RG('events', 'fam_date'), RG('events', 'fam_date'))),
    O('Conferences booked, next 30 days', 'int', 'COUNTIFS(%s,%s,%s,">"&{today},%s,"<="&({today}+30))' % (RG('conferences', 'status'), BOOKED, RG('conferences', 'date'), RG('conferences', 'date'))),
    O('Conference slots still free', 'int', 'COUNTIFS(%s,%s)' % (RG('conf_slots', 'status'), fl('Free slot'))),
    O('Families without a conference slot', 'int', 'COUNTIFS(%s,">0",%s,0)' % (RG('families', 'enrolled_kids'), RG('families', 'conf_booked'))),
    O('Conference no-shows, last 12 months', 'int', 'COUNTIFS(%s,%s,%s,">"&({today}-365))' % (RG('conferences', 'status'), NOSHOW, RG('conferences', 'date'))),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s,%s)' % (DUE2, DUE2, vd('items due this week'), vd('Plan is on schedule')))],
    GR('What if', ('Look 7 days ahead', {'days': 7}), ('Look 30 days ahead', {'days': 30}), ('Look 60 days ahead', {'days': 60}), ('Look 3 days ahead', {'days': 3}))))

# 3 observation and portfolio status by child
T3 = 'COUNTIFS(%s,{in:room},%s,0)' % (RG('obs_status', 'room'), RG('obs_status', 'entries_term'))
A3 = 'COUNTIFS(%s,0)' % RG('obs_status', 'entries_term')
tools.append(TOOL('obs_tool', 'Observation Status by Child', 'Observation and portfolio status by child',
    'Pick a room: children enrolled, entries this term, children with no entry and below your target, the last entry date and the teacher. Counts and dates only, never what was observed.', [
    IL('room', 'Room', 'room', 'Preschool')], [
    O('Children enrolled in the room', 'int', 'COUNTIFS(%s,{in:room})' % RG('obs_status', 'room')), O('Entries this term in the room', 'int', 'SUMIFS(%s,%s,{in:room})' % (RG('obs_status', 'entries_term'), RG('obs_status', 'room'))),
    O('Children with no entry this term', 'int', T3), O('Children below the entries target', 'int', 'COUNTIFS(%s,{in:room},%s,%s)' % (RG('obs_status', 'room'), RG('obs_status', 'flag'), fl('Below target'))),
    O('Share of children with an entry', 'pct', 'IFERROR(1-(%s)/COUNTIFS(%s,{in:room}),0)' % (T3, RG('obs_status', 'room'))),
    O('Last entry in the room', 'date', 'SUMPRODUCT(MAX((%s={in:room})*%s))' % (RG('observations', 'room'), RG('observations', 'date'))),
    O('Entries still to do in the room', 'int', 'SUMIFS(%s,%s,{in:room})' % (RG('obs_status', 'todo'), RG('obs_status', 'room'))),
    O('Teacher of the room', 'text', 'IFERROR(INDEX(%s,MATCH({in:room},%s,0))&"","")' % (RG('obs_status', 'teacher'), RG('obs_status', 'room'))),
    O('Children with no entry, all rooms', 'int', A3),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (A3, vd('All children have entries'), A3, vd('children need an entry')))],
    GR('What if', ('Infants', {'room': EQ('room', 'Infants')}), ('Toddlers', {'room': EQ('room', 'Toddlers')}), ('Twos', {'room': EQ('room', 'Twos')}), ('School-age', {'room': EQ('room', 'School-age')}))))

# 4 camp week fill and break-even
P4 = 'INDEX(%s,MATCH({in:week},%s,0))' % (pw('program'), pw('week'))
N4 = '(%s+{in:extra})' % PWW('signups')
PR4, DY4 = PWW('price_day'), PWW('days')
C1_4 = '{set:camp_hours_day}*%s*{set:camp_staff_rate}' % DY4
COST4 = 'IF(%s=%s,%s,MAX(1,ROUNDUP(%s/{set:ratio_schoolage},0))*(%s))' % (P4, BAS, PWW('staff_cost'), N4, C1_4)
BE4 = 'IF(%s*%s<=0,0,IF(%s=%s,ROUNDUP(%s/(%s*%s),0),IF(ROUNDUP((%s)/(%s*%s),0)<={set:ratio_schoolage},ROUNDUP((%s)/(%s*%s),0),ROUNDUP(2*(%s)/(%s*%s),0))))' % (
    PR4, DY4, P4, BAS, PWW('staff_cost'), PR4, DY4, C1_4, PR4, DY4, C1_4, PR4, DY4, C1_4, PR4, DY4)
tools.append(TOOL('camp_fill', 'Camp Week Fill and Break-even', 'Camp week fill and break-even',
    'Pick a program week and add what-if sign-ups: places, fill, revenue, staff cost, the break-even sign-ups and the decision run, run with a minimum or cancel for that week.', [
    I('week', 'Week (Monday)', DEF_WEEK, 'date'), I('extra', 'Extra sign-ups to test', 0)], [
    O('Program', 'text', 'IFERROR(%s&"","")' % P4), O('Places', 'int', PWW('places')), O('Sign-ups with the test', 'int', N4), O('Fill', 'pct', 'IFERROR(%s/%s,0)' % (N4, PWW('places'))),
    O('Price a day', 'money', PR4), O('Open days', 'int', DY4), O('Revenue', 'money', '%s*%s*%s' % (N4, PR4, DY4)), O('Staff cost', 'money', COST4), O('Break-even sign-ups', 'int', BE4),
    O('Sign-ups against break-even', 'int', '%s-(%s)' % (N4, BE4)), O('Profit', 'money', '%s*%s*%s-(%s)' % (N4, PR4, DY4, COST4)),
    O('Verdict', 'text', 'IF(%s<=0,"-",IF(%s>=(%s)+{set:run_margin},%s,IF(%s>=(%s),%s,%s)))' % (PWW('places'), N4, BE4, CV_RUN, N4, BE4, CV_MIN, CV_CANCEL))],
    GR('What if', ('A week with 6 sign-ups', {'week': DF(DEF_WEEK6)}), ('A week with 4 sign-ups', {'week': DF(DEF_WEEK4)}), ('Two more sign-ups', {'extra': 2}), ('Five more sign-ups', {'extra': 5}), ('Two fewer sign-ups', {'extra': -2}))))

# 5 camp minimum sign-ups finder
C5 = '({in:staff}*{set:camp_hours_day}*{in:days}*{set:camp_staff_rate})'
U5 = '({in:price}*{in:days})'
MIN5 = 'ROUNDUP(%s/%s,0)' % (C5, U5)
HIST5 = '%s,{in:program},%s,">"&({today}-365),%s,"<="&{today}' % (pw('program'), pw('week'), pw('week'))
tools.append(TOOL('camp_min', 'Camp Minimum Sign-ups Finder', 'Camp minimum sign-ups finder',
    'Type the price a day, days and staff for a camp week: staff cost over the income of one sign-up gives the minimum sign-ups, with price and staff changes and past weeks that reached it.', [
    IL('program', 'Program', 'program', 'Summer camp'), I('price', 'Price a day', 46, 'money'), I('days', 'Open days in the week', 5), I('staff', 'Staff members at camp', 1), I('step', 'Price step to test', 4, 'money')], [
    O('Staff cost for the week', 'money', C5), O('Income from one sign-up for the week', 'money', U5), O('Minimum sign-ups to break even', 'int', MIN5),
    O('Places in the program', 'int', 'SUMIFS(%s,%s,{in:program})' % (RG('programs', 'places'), RG('programs', 'program'))),
    O('Minimum as a share of places', 'pct', 'IFERROR(%s/SUMIFS(%s,%s,{in:program}),0)' % (MIN5, RG('programs', 'places'), RG('programs', 'program'))),
    O('Average sign-ups, last 12 months', 'num', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (pw('signups'), HIST5)),
    O('Weeks that reached the minimum, last 12 months', 'int', 'COUNTIFS(%s,%s,">="&%s)' % (HIST5, pw('signups'), MIN5)), O('Program weeks, last 12 months', 'int', 'COUNTIFS(%s)' % HIST5),
    O('Minimum if the price is lower by the step', 'int', 'ROUNDUP(%s/(({in:price}-{in:step})*{in:days}),0)' % C5), O('Minimum if the price is higher by the step', 'int', 'ROUNDUP(%s/(({in:price}+{in:step})*{in:days}),0)' % C5),
    O('Minimum with one more staff member', 'int', 'ROUNDUP(%s/%s,0)' % ('(({in:staff}+1)*{set:camp_hours_day}*{in:days}*{set:camp_staff_rate})', U5)),
    O('Verdict', 'text', '%s&" "&%s' % (vd('Set the minimum at'), MIN5))],
    GR('What if', ('Holiday camp, 42 a day', {'program': EQ('program', 'Holiday camp'), 'price': 42}), ('Two staff members', {'staff': 2}), ('Price 52 a day', {'price': 52}), ('Four open days', {'days': 4}), ('Price step 8', {'step': 8}))))

# 6 camp price tester
C6 = '({in:staff}*{set:camp_hours_day}*{in:days}*{set:camp_staff_rate})'
def PRF(p, n): return '((%s)*(%s)*{in:days}-%s)' % (p, n, C6)
tools.append(TOOL('camp_price', 'Camp Price Tester', 'Camp price tester',
    'Move the price a day up and down against the sign-ups you expect: revenue and profit for the week, the profit after a price rise that loses families, and the price that breaks even.', [
    I('price', 'Price a day', 46, 'money'), I('signups', 'Expected sign-ups', 6), I('days', 'Open days in the week', 5), I('staff', 'Staff members at camp', 1), I('step', 'Price step to test', 4, 'money'),
    I('lost', 'Families lost if the price rises', 1), I('won', 'Families won if the price falls', 0)], [
    O('Revenue for the week', 'money', '{in:price}*{in:signups}*{in:days}'), O('Staff cost for the week', 'money', C6), O('Profit for the week', 'money', PRF('{in:price}', '{in:signups}')),
    O('Profit if the price rises by the step and families leave', 'money', PRF('{in:price}+{in:step}', '{in:signups}-{in:lost}')), O('Profit if the price falls by the step and families join', 'money', PRF('{in:price}-{in:step}', '{in:signups}+{in:won}')),
    O('Profit if the price rises by the step, no one leaves', 'money', PRF('{in:price}+{in:step}', '{in:signups}')), O('Profit if the price falls by two steps', 'money', PRF('{in:price}-2*{in:step}', '{in:signups}')),
    O('Price a day that breaks even at these sign-ups', 'money', 'IFERROR(%s/({in:signups}*{in:days}),0)' % C6),
    O('Verdict', 'text', 'IF(AND(%s>%s,%s>=%s),%s,IF(%s>%s,%s,%s))' % (PRF('{in:price}+{in:step}', '{in:signups}-{in:lost}'), PRF('{in:price}', '{in:signups}'), PRF('{in:price}+{in:step}', '{in:signups}-{in:lost}'),
        PRF('{in:price}-{in:step}', '{in:signups}+{in:won}'), vd('Raise the price'), PRF('{in:price}-{in:step}', '{in:signups}+{in:won}'), PRF('{in:price}', '{in:signups}'), vd('Lower the price'), vd('Keep the price')))],
    GR('What if', ('Only 4 sign-ups', {'signups': 4}), ('Ten sign-ups', {'signups': 10}), ('Price 40 a day', {'price': 40}), ('Two families join on a fall', {'won': 2}), ('Two families leave on a rise', {'lost': 2}), ('Four open days', {'days': 4}))))

# 7 before-after school fill by weekday
WD7 = [('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'), ('thu', 'Thursday'), ('fri', 'Friday')]
PL7 = 'SUMIFS(%s,%s,%s)' % (RG('programs', 'places'), RG('programs', 'program'), BAS)
BUSY7 = 'MAX(%s)' % ','.join('{in:%s}' % k for k, _ in WD7)
def NAME7(): return 'IF({in:mon}=%s,%s,IF({in:tue}=%s,%s,IF({in:wed}=%s,%s,IF({in:thu}=%s,%s,%s))))' % (BUSY7, tok('wday', 'Monday'), BUSY7, tok('wday', 'Tuesday'), BUSY7, tok('wday', 'Wednesday'), BUSY7, tok('wday', 'Thursday'), tok('wday', 'Friday'))

tools.append(TOOL('bas_fill', 'Before-After School Fill', 'Before-after school fill by weekday',
    'Type the children booked on each weekday and the families asking for another day: places left each weekday, the busiest day, staff needed at the School-age ratio and whether to open more places.', [
    I('mon', 'Children booked on Monday', 5), I('tue', 'Children booked on Tuesday', 6), I('wed', 'Children booked on Wednesday', 6), I('thu', 'Children booked on Thursday', 7), I('fri', 'Children booked on Friday', 5),
    I('ask', 'Families asking for another day on the busiest day', 2)], [
    O('Before-after school places', 'int', PL7)] + [O('Free places on ' + w, 'int', '%s-{in:%s}' % (PL7, k)) for k, w in WD7] + [
    O('Busiest weekday, children booked', 'int', BUSY7), O('Share of places on the busiest weekday', 'pct', 'IFERROR((%s+{in:ask})/%s,0)' % (BUSY7, PL7)),
    O('Quietest weekday, children booked', 'int', 'MIN(%s)' % ','.join('{in:%s}' % k for k, _ in WD7)),
    O('Staff needed on the busiest day at the ratio', 'int', 'ROUNDUP((%s+{in:ask})/{set:ratio_schoolage},0)' % BUSY7),
    O('Busiest weekday', 'text', NAME7()),
    O('Verdict', 'text', 'IF(IFERROR((%s+{in:ask})/%s,0)>=0.8,%s&" "&%s,%s)' % (BUSY7, PL7, vd('Open more places on'), NAME7(), vd('Fine as it is')))],
    GR('What if', ('Thursday nearly full', {'thu': 12, 'ask': 2}), ('Thursday full with requests', {'thu': 13, 'ask': 3}), ('A quiet week', {'mon': 3, 'tue': 3, 'wed': 4, 'thu': 4, 'fri': 3}), ('Five families ask', {'ask': 5}))))

# 8 camp staff plan
N8 = '(%s+{in:extra})' % PWW('signups')
NEED8 = 'MAX(1,ROUNDUP(%s/{set:ratio_schoolage},0))' % N8
FLO8 = 'MAX(0,%s-{in:own})' % NEED8
tools.append(TOOL('camp_staff', 'Camp Staff Plan', 'Camp staff plan',
    'Pick a camp week and add what-if sign-ups: staff needed at the School-age ratio, how many floaters to book, the staff cost against revenue and the children per staff member. Check your local rules.', [
    I('week', 'Week (Monday)', DEF_WEEK6, 'date'), I('extra', 'Extra sign-ups to test', 0), I('own', 'Staff members from your own team at camp', 1), I('rate', 'Floater cost an hour', 17.0, 'money')], [
    O('Sign-ups with the test', 'int', N8), O('Open days', 'int', PWW('days')), O('Staff needed at the ratio', 'int', NEED8), O('Floaters to book', 'int', FLO8),
    O('Children per staff member', 'num', 'IFERROR(%s/%s,0)' % (N8, NEED8)),
    O('Floater cost for the week', 'money', '(%s)*{set:camp_hours_day}*%s*{in:rate}' % (FLO8, PWW('days'))),
    O('Own staff cost for the week', 'money', 'MIN({in:own},%s)*{set:camp_hours_day}*%s*{set:camp_staff_rate}' % (NEED8, PWW('days'))),
    O('Revenue for the week', 'money', '%s*%s*%s' % (N8, PWW('price_day'), PWW('days'))),
    O('Staff cost as a share of revenue', 'pct', 'IFERROR(((%s)*{set:camp_hours_day}*%s*{in:rate}+MIN({in:own},%s)*{set:camp_hours_day}*%s*{set:camp_staff_rate})/(%s*%s*%s),0)' % (FLO8, PWW('days'), NEED8, PWW('days'), N8, PWW('price_day'), PWW('days'))),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s&" "&%s,%s)' % (FLO8, vd('Book'), FLO8, v2('floater(s)'), v2('No floaters needed')))],
    GR('What if', ('A full camp of 18', {'extra': 12}), ('Two staff from your own team', {'own': 2, 'extra': 12}), ('No one from your own team', {'own': 0}), ('Floater cost 20 an hour', {'rate': 20}))))

# 9 camp profit by week ranked
tools.append(TOOL('camp_rank', 'Camp Profit by Week', 'Camp profit by week, ranked',
    'Type a rank: the camp week at that rank by profit, its program and sign-ups, the worst week, how many weeks made a profit and the total; the verdict names the program to promote and the one to drop.', [
    I('rank', 'Rank to show, 1 is the best week', 1)], [
    O('Week at this rank', 'date', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,{in:rank}),%s,0)),"")' % (RG('camp_cal', 'week'), RG('camp_cal', 'rank_score'), RG('camp_cal', 'rank_score'))),
    O('Its program', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,{in:rank}),%s,0))&"","")' % (RG('camp_cal', 'program'), RG('camp_cal', 'rank_score'), RG('camp_cal', 'rank_score'))),
    O('Sign-ups that week', 'int', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,{in:rank}),%s,0)),0)' % (RG('camp_cal', 'signups'), RG('camp_cal', 'rank_score'), RG('camp_cal', 'rank_score'))),
    O('Its profit', 'money', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,{in:rank}),%s,0)),0)' % (RG('camp_cal', 'profit'), RG('camp_cal', 'rank_score'), RG('camp_cal', 'rank_score'))),
    O('Worst week', 'date', 'IFERROR(INDEX(%s,MATCH(SMALL(%s,1),%s,0)),"")' % (RG('camp_cal', 'week'), RG('camp_cal', 'rank_score'), RG('camp_cal', 'rank_score'))),
    O('Worst week profit', 'money', 'IFERROR(INDEX(%s,MATCH(SMALL(%s,1),%s,0)),0)' % (RG('camp_cal', 'profit'), RG('camp_cal', 'rank_score'), RG('camp_cal', 'rank_score'))),
    O('Camp weeks in the calendar', 'int', 'COUNT(%s)' % RG('camp_cal', 'rank_score')), O('Camp weeks with a profit', 'int', 'COUNTIFS(%s,">0",%s,"<="&{today})' % (RG('camp_cal', 'profit'), RG('camp_cal', 'week'))),
    O('Profit of all camp weeks so far', 'money', 'SUMIFS(%s,%s,"<="&{today})' % (RG('camp_cal', 'profit'), RG('camp_cal', 'week'))), O('Average profit a week', 'money', 'IFERROR(AVERAGEIFS(%s,%s,"<="&{today}),0)' % (RG('camp_cal', 'profit'), RG('camp_cal', 'week'))),
    O('Verdict', 'text', 'IFERROR(%s&" "&INDEX(%s,MATCH(LARGE(%s,1),%s,0))&" / "&%s&" "&INDEX(%s,MATCH(SMALL(%s,1),%s,0)),%s)' % (
        v2('Promote'), RG('camp_cal', 'program'), RG('camp_cal', 'rank_score'), RG('camp_cal', 'rank_score'), vd('Drop'), RG('camp_cal', 'program'), RG('camp_cal', 'rank_score'), RG('camp_cal', 'rank_score'), v2('No camp weeks')))],
    GR('What if', ('Second best week', {'rank': 2}), ('Third best week', {'rank': 3}), ('Fifth best week', {'rank': 5}), ('Tenth best week', {'rank': 10}))))

# 10 communication gap finder
GS = RG('comm_gaps', 'gap_score')
def GAP10(col, d='""'): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,{in:rank}),%s,0)),%s)' % (RG('comm_gaps', col), GS, GS, d)
tools.append(TOOL('gap_finder', 'Communication Gap Finder', 'Communication gap finder',
    'Type a rank and your limit in days: the family at that rank by days since the last contact, the last contact date and messages waiting, and how many enrolled families are over your limit. Status only.', [
    I('rank', 'Rank to show, 1 is the longest gap', 1), I('limit', 'Days without contact that start a call', 180)], [
    O('Family at this rank', 'text', GAP10('family')), O('Days since contact', 'int', GAP10('days_since', '0')), O('Last contact', 'date', GAP10('last_contact')), O('Messages waiting', 'int', GAP10('waiting', '0')),
    O('Room of the family', 'text', GAP10('room')), O('Phone', 'text', GAP10('phone')),
    O('Enrolled families over the limit', 'int', 'COUNTIFS(%s,">"&{in:limit})' % RG('comm_gaps', 'days_since')), O('Enrolled families', 'int', 'COUNTIFS(%s,">0")' % RG('comm_gaps', 'enrolled')),
    O('Share of enrolled families over the limit', 'pct', 'IFERROR(COUNTIFS(%s,">"&{in:limit})/COUNTIFS(%s,">0"),0)' % (RG('comm_gaps', 'days_since'), RG('comm_gaps', 'enrolled'))),
    O('Verdict', 'text', 'IF(%s>{in:limit},%s&" "&%s,%s)' % (GAP10('days_since', '0'), vd('Call'), GAP10('family'), vd('Fine')))],
    GR('What if', ('Second longest gap', {'rank': 2}), ('Third longest gap', {'rank': 3}), ('Limit 60 days', {'limit': 60}), ('Limit 200 days', {'limit': 200}))))

# 11 message reply time check
W11 = '%s,{in:topic},%s,">"&({today}-{in:days})' % (RG('parent_msgs', 'topic'), RG('parent_msgs', 'date'))
SLOWT = 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (RG('reply_topic', 'topic'), RG('reply_topic', 'avg_hours'), RG('reply_topic', 'avg_hours'))
tools.append(TOOL('reply_check', 'Message Reply Time Check', 'Message reply time check',
    'Pick a topic, the target hours and a window in days: messages and average reply hours for the topic, the share answered within the target, the slowest topic and messages still waiting.', [
    IL('topic', 'Topic', 'topic', 'Billing'), I('target', 'Hours to reply, your target', 24), I('days', 'Days to look back', 90)], [
    O('Messages on the topic in the window', 'int', 'COUNTIFS(%s)' % W11), O('Average reply hours', 'num', 'IFERROR(AVERAGEIFS(%s,%s,%s,%s),0)' % (RG('parent_msgs', 'reply_hours'), W11, RG('parent_msgs', 'status'), REPL)),
    O('Share replied within the target', 'pct', 'IFERROR(COUNTIFS(%s,%s,%s,%s,"<="&{in:target})/COUNTIFS(%s,%s,%s),0)' % (W11, RG('parent_msgs', 'status'), REPL, RG('parent_msgs', 'reply_hours'), W11, RG('parent_msgs', 'status'), REPL)),
    O('Messages on the topic waiting now', 'int', 'COUNTIFS(%s,{in:topic},%s,%s)' % (RG('parent_msgs', 'topic'), RG('parent_msgs', 'status'), AWAIT)),
    O('All topics, average reply hours, last 30 days', 'num', 'IFERROR(AVERAGEIFS(%s,%s,%s,%s),0)' % (RG('parent_msgs', 'reply_hours'), D30(RG('parent_msgs', 'date')), RG('parent_msgs', 'status'), REPL)),
    O('Slowest topic', 'text', SLOWT), O('Its average reply hours', 'num', 'MAX(%s)' % RG('reply_topic', 'avg_hours')), O('Longest reply, hours', 'int', 'MAX(%s)' % RG('parent_msgs', 'reply_hours')),
    O('Verdict', 'text', 'IF(MAX(%s)>{in:target},%s&" "&%s,%s)' % (RG('reply_topic', 'avg_hours'), v2('Slow on'), SLOWT, v2('Reply time is on target')))],
    GR('What if', ('Pickup', {'topic': EQ('topic', 'Pickup')}), ('Schedule', {'topic': EQ('topic', 'Schedule')}), ('Target 6 hours', {'target': 6}), ('Target 12 hours', {'target': 12}), ('Look back 30 days', {'days': 30}))))

# 12 conference slot scheduler
ENRF12 = 'COUNTIFS(%s,">0")' % RG('families', 'enrolled_kids')
WITHOUT12 = 'COUNTIFS(%s,">0",%s,0)' % (RG('families', 'enrolled_kids'), RG('families', 'conf_booked'))
FREE12 = 'COUNTIFS(%s,%s)' % (RG('conf_slots', 'status'), fl('Free slot'))
NSR12 = 'IFERROR(COUNTIFS(%s,%s)/(COUNTIFS(%s,%s)+COUNTIFS(%s,%s)),0)' % (RG('conferences', 'status'), NOSHOW, RG('conferences', 'status'), HELD, RG('conferences', 'status'), NOSHOW)
NEED12 = '(%s)*{in:per}+ROUNDUP(COUNTIFS(%s,%s,%s,">"&{today})*%s,0)' % (WITHOUT12, RG('conferences', 'status'), BOOKED, RG('conferences', 'date'), NSR12)
tools.append(TOOL('slot_sched', 'Conference Slot Scheduler', 'Conference slot scheduler',
    'Type the slots a family needs: enrolled families, families without a slot, free slots, the no-show history and the slots you need, with the number of families still to book.', [
    I('per', 'Slots each family needs', 1)], [
    O('Enrolled families', 'int', ENRF12), O('Families with a slot booked', 'int', 'COUNTIFS(%s,">0",%s,">0")' % (RG('families', 'enrolled_kids'), RG('families', 'conf_booked'))), O('Families without a slot', 'int', WITHOUT12),
    O('Free slots', 'int', FREE12), O('Booked slots', 'int', 'COUNTIFS(%s,%s)' % (RG('conf_slots', 'status'), fl('Booked slot'))), O('No-show rate, all conference weeks', 'pct', NSR12),
    O('Families with a no-show on record', 'int', 'COUNTIFS(%s,">0")' % RG('families', 'conf_noshow')), O('Slots needed, with a spare for no-shows', 'int', NEED12), O('Free slots left after booking', 'int', '%s-(%s)' % (FREE12, NEED12)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>=(%s),%s&" "&%s&" "&%s,%s&" "&%s))' % (WITHOUT12, vd('Enough slots'), FREE12, NEED12, vd('Book'), WITHOUT12, vd('families'), v2('Add slots, families still to book'), WITHOUT12))],
    GR('What if', ('Two slots a family', {'per': 2}), ('Three slots a family', {'per': 3}))))

# 13 event attendance analysis
EV13 = '%s,{in:kind},%s,"<="&{today}' % (RG('events', 'kind'), RG('events', 'date'))
SH13 = 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (RG('events', 'attended'), EV13, RG('events', 'invited'), EV13)
LAST13 = 'SUMPRODUCT(MAX((%s={in:kind})*(%s<={today})*%s))' % (RG('events', 'kind'), RG('events', 'date'), RG('events', 'date'))
tools.append(TOOL('event_att', 'Event Attendance Analysis', 'Event attendance analysis',
    'Pick an event kind and the attendance you want: events held, families invited and attended, the share, the last event against the average and a verdict to repeat, change or drop the kind.', [
    IL('kind', 'Event kind', 'ekind', 'Open day'), I('target', 'Wanted attendance share', 0.60, 'pct')], [
    O('Events held', 'int', 'COUNTIFS(%s)' % EV13), O('Families invited in total', 'int', 'SUMIFS(%s,%s)' % (RG('events', 'invited'), EV13)), O('Families attended in total', 'int', 'SUMIFS(%s,%s)' % (RG('events', 'attended'), EV13)),
    O('Attendance share', 'pct', SH13), O('Average families attending', 'num', 'IFERROR(SUMIFS(%s,%s)/COUNTIFS(%s),0)' % (RG('events', 'attended'), EV13, EV13)), O('Date of the last one', 'date', LAST13),
    O('Share at the last one', 'pct', 'IFERROR(SUMIFS(%s,%s,{in:kind},%s,%s)/SUMIFS(%s,%s,{in:kind},%s,%s),0)' % (RG('events', 'attended'), RG('events', 'kind'), RG('events', 'date'), LAST13, RG('events', 'invited'), RG('events', 'kind'), RG('events', 'date'), LAST13)),
    O('All kinds except newsletters, attendance share', 'pct', 'IFERROR(SUMIFS(%s,%s,"<>"&%s,%s,"<="&{today})/SUMIFS(%s,%s,"<>"&%s,%s,"<="&{today}),0)' % (RG('events', 'attended'), RG('events', 'kind'), NEWS, RG('events', 'date'), RG('events', 'invited'), RG('events', 'kind'), NEWS, RG('events', 'date'))),
    O('Verdict', 'text', 'IF(%s>={in:target},%s,IF(%s>={in:target}*0.7,%s,%s))&" "&{in:kind}' % (SH13, vd('Repeat'), SH13, vd('Change'), vd('Drop')))],
    GR('What if', ('Newsletter', {'kind': EQ('ekind', 'Newsletter')}), ('Family event', {'kind': EQ('ekind', 'Family event')}), ('Family meeting week', {'kind': EQ('ekind', 'Family meeting week')}), ('Target 75 percent', {'target': 0.75}))))

# 14 leaver reason analyser
LV14 = '%s,%s,%s,">"&EDATE({today},-{in:months})' % (RG('children', 'status'), LEFT, RG('children', 'end_date'))
def LC14(label): return 'COUNTIFS(%s,%s,%s)' % (LV14, RG('children', 'leave_reason'), tok('leavereason', label))
c1, c2, c3 = LC14('Moved'), LC14('Other setting'), LC14('School')
TOPN14 = 'MAX(%s,%s,%s)' % (c1, c2, c3)
TOPL14 = 'IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (c1, TOPN14, tok('leavereason', 'Moved'), c2, TOPN14, tok('leavereason', 'Other setting'), tok('leavereason', 'School'))
tools.append(TOOL('leaver_tool', 'Leaver Reason Analyser', 'Leaver reason analyser',
    'Pick a reason and the months to look back: children who left, their months stayed, the weekly tuition and the tuition of a year that left with them, and the reason to act on first.', [
    IL('reason', 'Leaving reason', 'leavereason', 'Other setting'), I('months', 'Months to look back', 12)], [
    O('Children who left in the window', 'int', 'COUNTIFS(%s)' % LV14), O('Left for this reason', 'int', 'COUNTIFS(%s,%s,{in:reason})' % (LV14, RG('children', 'leave_reason'))),
    O('Share of leavers for this reason', 'pct', 'IFERROR(COUNTIFS(%s,%s,{in:reason})/COUNTIFS(%s),0)' % (LV14, RG('children', 'leave_reason'), LV14)),
    O('Average months stayed', 'num', 'IFERROR(AVERAGEIFS(%s,%s,%s,{in:reason}),0)' % (RG('children', 'months_stayed'), LV14, RG('children', 'leave_reason'))),
    O('Weekly tuition that left', 'money', 'SUMIFS(%s,%s,%s,{in:reason})' % (RG('children', 'weekly_fee'), LV14, RG('children', 'leave_reason'))),
    O('Tuition of a year that left', 'money', '52*SUMIFS(%s,%s,%s,{in:reason})' % (RG('children', 'weekly_fee'), LV14, RG('children', 'leave_reason'))),
    O('Reason to act on first', 'text', 'IF(COUNTIFS(%s)=0,"-",%s)' % (LV14, TOPL14)), O('Leavers for that reason', 'int', TOPN14),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,%s&" "&%s)' % (LV14, v2('No leavers'), v2('Act first on'), TOPL14))],
    GR('What if', ('Moved', {'reason': EQ('leavereason', 'Moved')}), ('School', {'reason': EQ('leavereason', 'School')}), ('Look back 6 months', {'months': 6}), ('Look back 24 months', {'months': 24}))))

# 15 family pulse score
now = '({in:s1}+{in:s2}+{in:s3}+{in:s4})/4'; prev = '({in:p1}+{in:p2}+{in:p3}+{in:p4})/4'
tools.append(TOOL('pulse_tool', 'Family Pulse Score', 'Family pulse score',
    'Type this pulse score out of 5 for four topics and the average of your last three pulses: the change, the topics that moved, the response rate and a verdict improving, steady or falling.', [
    I('s1', 'Communication, this pulse', 4.4, 'num'), I('s2', 'Daily reports, this pulse', 4.6, 'num'), I('s3', 'Pickup and drop-off, this pulse', 4.3, 'num'), I('s4', 'Value for the price, this pulse', 3.9, 'num'),
    I('p1', 'Communication, last 3 pulses', 4.1, 'num'), I('p2', 'Daily reports, last 3 pulses', 4.4, 'num'), I('p3', 'Pickup and drop-off, last 3 pulses', 4.3, 'num'), I('p4', 'Value for the price, last 3 pulses', 4.0, 'num'),
    I('asked', 'Families asked', 51), I('replies', 'Families who replied', 33)], [
    O('Average score now', 'num', 'ROUND(%s,2)' % now), O('Average of the last 3 pulses', 'num', 'ROUND(%s,2)' % prev), O('Change', 'num', 'ROUND(%s-%s,2)' % (now, prev)),
    O('Topics that improved', 'int', '({in:s1}>{in:p1})+({in:s2}>{in:p2})+({in:s3}>{in:p3})+({in:s4}>{in:p4})'), O('Topics that fell', 'int', '({in:s1}<{in:p1})+({in:s2}<{in:p2})+({in:s3}<{in:p3})+({in:s4}<{in:p4})'),
    O('Lowest score now', 'num', 'MIN({in:s1},{in:s2},{in:s3},{in:s4})'), O('Biggest fall on one topic', 'num', 'MIN({in:s1}-{in:p1},{in:s2}-{in:p2},{in:s3}-{in:p3},{in:s4}-{in:p4})'),
    O('Response rate', 'pct', 'IFERROR({in:replies}/{in:asked},0)'),
    O('Verdict', 'text', 'IF(%s-%s>={set:pulse_change},%s,IF(%s-%s<=-{set:pulse_change},%s,%s))' % (now, prev, vd('Improving'), now, prev, vd('Falling'), vd('Steady')))],
    GR('What if', ('Value for the price falls to 3.2', {'s4': 3.2}), ('Every score up by half a point', {'s1': 4.9, 's2': 5.0, 's3': 4.8, 's4': 4.4}), ('Every score down by half a point', {'s1': 3.6, 's2': 3.9, 's3': 3.8, 's4': 3.4}), ('Low response', {'replies': 12}))))

# 16 observation workload per staff
TD16 = 'SUMIFS(%s,%s,{in:staff})' % (RG('obs_status', 'todo'), RG('obs_status', 'teacher'))
def TDN(name): return 'SUMIFS(%s,%s,%s)' % (RG('obs_status', 'todo'), RG('obs_status', 'teacher'), tok('teacher', name))
MAX16 = 'MAX(%s)' % RG('obs_status', 'teacher_todo'); MIN16 = 'MIN(%s)' % RG('obs_status', 'teacher_todo')
NAME16 = 'INDEX(%s,MATCH(%s,%s,0))' % (RG('obs_status', 'teacher'), MAX16, RG('obs_status', 'teacher_todo'))
tools.append(TOOL('obs_load', 'Observation Workload', 'Observation workload per staff',
    'Pick a teacher and the weeks left in the term: children, entries done and entries still to do, the entries to write each week, and who has the most to do across the center.', [
    IL('staff', 'Teacher', 'teacher', 'Camille Fontaine'), I('weeks', 'Weeks left in the term', 5)], [
    O('Children in the teacher\'s room', 'int', 'COUNTIFS(%s,{in:staff})' % RG('obs_status', 'teacher')), O('Entries done this term', 'int', 'SUMIFS(%s,%s,{in:staff})' % (RG('obs_status', 'entries_term'), RG('obs_status', 'teacher'))),
    O('Entries still to do', 'int', TD16), O('Entries to write each week', 'num', 'IFERROR(ROUND((%s)/{in:weeks},1),0)' % TD16),
    O('Children with no entry', 'int', 'COUNTIFS(%s,{in:staff},%s,0)' % (RG('obs_status', 'teacher'), RG('obs_status', 'entries_term')))] + [
    O('Still to do, ' + t, 'int', TDN(t)) for t in TEACHERS] + [
    O('Most entries still to do', 'int', MAX16), O('Teacher with the most to do', 'text', NAME16),
    O('Verdict', 'text', 'IF(%s-%s<=2,%s,%s&" "&%s&" "&(%s-%s)&" "&%s)' % (MAX16, MIN16, vd('Even'), NAME16, v2('has'), MAX16, MIN16, v2('more to do')))],
    GR('What if', ('Aaliyah Rahman', {'staff': EQ('teacher', 'Aaliyah Rahman')}), ('Sofia Petrova', {'staff': EQ('teacher', 'Sofia Petrova')}), ('Ngozi Eze', {'staff': EQ('teacher', 'Ngozi Eze')}), ('Two weeks left', {'weeks': 2}))))

# 17 camp sibling and early-bird discount test
LOSS17 = '({in:base}*{in:qual}*{in:price}*{in:days}*{in:disc})'
NEED17 = 'ROUNDUP(%s/({in:price}*{in:days}*(1-{in:disc})),0)' % LOSS17
GAIN17 = '({in:extra}*{in:price}*{in:days}*(1-{in:disc}))'
tools.append(TOOL('disc_test', 'Camp Discount Test', 'Camp sibling and early-bird discount test',
    'Type the discount, the share of sign-ups who get it and the extra sign-ups you expect: the revenue given away, the extra sign-ups needed to pay for it and whether to offer it.', [
    I('disc', 'Discount', 0.10, 'pct'), I('qual', 'Share of sign-ups who get the discount', 0.5, 'pct'), I('price', 'Price a day', 46, 'money'), I('days', 'Open days in the week', 5), I('base', 'Sign-ups without the discount', 5),
    I('extra', 'Extra sign-ups the discount brings', 2), I('places', 'Camp places', 18)], [
    O('Revenue without the discount', 'money', '{in:base}*{in:price}*{in:days}'), O('Revenue given away', 'money', LOSS17), O('Income from one extra sign-up', 'money', '{in:price}*{in:days}*(1-{in:disc})'),
    O('Extra sign-ups needed to pay for it', 'int', NEED17), O('Free places left', 'int', '{in:places}-{in:base}'), O('Income from the extra sign-ups', 'money', GAIN17),
    O('Net effect on the week', 'money', '%s-%s' % (GAIN17, LOSS17)), O('Largest discount that still pays', 'pct', 'IFERROR(MAX(0,{in:extra}*{in:price}*{in:days}/({in:base}*{in:qual}*{in:price}*{in:days}+{in:extra}*{in:price}*{in:days})),0)'),
    O('Verdict', 'text', 'IF(AND(%s>=%s,%s<={in:places}-{in:base}),%s,%s)' % ('{in:extra}', NEED17, NEED17, vd('Offer the discount'), vd('Do not offer the discount')))],
    GR('What if', ('Only one extra sign-up', {'extra': 1}), ('Discount 20 percent', {'disc': 0.2}), ('Everyone gets it', {'qual': 1.0}), ('Three extra sign-ups', {'extra': 3}), ('Almost full camp', {'base': 17, 'extra': 2}))))

# 18 program mix test
def RPP(p): return 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (pw('revenue'), pw('program'), p, pw('places'), pw('program'), p)
def PPP(p): return 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (pw('profit'), pw('program'), p, pw('places'), pw('program'), p)
BEST18 = 'MAX(%s,%s,%s)' % (PPP(BAS), PPP(SUMMER), PPP(HOLIDAY))
BESTN18 = 'IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (PPP(BAS), BEST18, BAS, PPP(SUMMER), BEST18, SUMMER, HOLIDAY)
SEL18 = '(%s)'
rp = D.room_profit('School-age')
RPLACE = round(rp['profit'] / 52.0 / 16, 2)
PP_SEL = 'IF({in:program}=%s,%s,IF({in:program}=%s,%s,%s))' % (BAS, PPP(BAS), SUMMER, PPP(SUMMER), PPP(HOLIDAY))
tools.append(TOOL('mix_test', 'Program Mix Test', 'Program mix test',
    'Pick a program and type the profit the School-age room earns on one licensed place in a week after overhead: revenue and profit on a program place against it, and the program that earns most.', [
    IL('program', 'Program', 'program', 'Summer camp'), I('room_pp', 'School-age room profit on one place in a week', RPLACE, 'money')], [
    O('Places in the program', 'int', 'SUMIFS(%s,%s,{in:program})' % (RG('programs', 'places'), RG('programs', 'program'))),
    O('Program weeks recorded', 'int', 'COUNTIFS(%s,{in:program})' % pw('program')),
    O('Average sign-ups a week', 'num', 'IFERROR(AVERAGEIFS(%s,%s,{in:program}),0)' % (pw('signups'), pw('program'))),
    O('Revenue on one place in a week', 'money', 'IF({in:program}=%s,%s,IF({in:program}=%s,%s,%s))' % (BAS, RPP(BAS), SUMMER, RPP(SUMMER), RPP(HOLIDAY))),
    O('Profit on one place in a week', 'money', PP_SEL), O('Room profit on one place in a week', 'money', '{in:room_pp}'),
    O('Difference from the room', 'money', '%s-{in:room_pp}' % PP_SEL), O('Best program, profit on one place', 'money', BEST18), O('Best program', 'text', BESTN18),
    O('Verdict', 'text', 'IF(%s>{in:room_pp},%s&" "&{in:program},%s&" "&{in:program})' % (PP_SEL, v2('Grow'), v2('Hold')))],
    GR('What if', ('Before-after school', {'program': EQ('program', 'Before-after school')}), ('Holiday camp', {'program': EQ('program', 'Holiday camp')}), ('Room profit 5 a place', {'room_pp': 5}), ('Room profit 1 a place', {'room_pp': 1}))))
assert len(tools) == 18, len(tools)
