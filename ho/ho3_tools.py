"""Home Management suite part 3: the 18 decision tools (a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho3_lists import *
from ho3_tables import R, A1, A2, C1, C2, YES, DAILY, OVD, MON, TUE, WED, THU, FRI, SAT, SUN, LATE, ROT, WS, W30, LOGW, NOTPAU, LASTFAIL
import ho3_data as DD


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dflt): return IN(k, label, 'list', key(lst, dflt), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def CAT(*xs): return '&'.join(xs)
def SP(*xs): return '&" "&'.join(xs)
CH = lambda c: R('chores', c)
MSD = 'DATE(YEAR({today}),MONTH({today}),1)'
PCT = lambda x: 'ROUND((%s)*100,0)&"%%"' % x
tools = []

# 1 cleaning plan this week
PL1 = lambda c: 'IFERROR(INDEX(%s,MATCH(1,%s,0)),"")' % (R('cleaning_plan', c), R('cleaning_plan', 'rank'))
OD1 = 'SUMIFS(%s,%s,1)' % (R('cleaning_plan', 'overdue_days'), R('cleaning_plan', 'rank'))
MIN1 = 'SUMIFS(%s,%s,1)' % (CH('minutes'), CH('due_week'))
tools.append(TOOL('plan_tool', 'Cleaning Plan This Week', 'What do we clean first this week',
    'Chores ranked by urgency with the minutes needed against the free minutes you type; the first chore and its suggested doer come from the work pattern.', [
    I('free', 'Free minutes a day for cleaning', 45), I('days', 'Days left to plan', 7)], [
    O('Most urgent chore', 'text', PL1('chore')), O('Room', 'text', PL1('room')), O('Days overdue', 'int', OD1), O('Suggested doer', 'text', PL1('suggested')),
    O('Chores overdue now', 'int', 'COUNTIFS(%s,%s)' % (CH('status'), OVD)), O('Overdue minutes', 'int', 'SUMIFS(%s,%s,%s)' % (CH('minutes'), CH('status'), OVD)),
    O('Chores due by the end of the week', 'int', 'COUNTIFS(%s,1)' % CH('due_week')), O('Minutes of those chores, each once', 'int', MIN1),
    O('Free minutes in the days', 'int', '{in:free}*{in:days}'), O('Share of the free minutes needed', 'pct', 'IFERROR((%s+SUMIFS(%s,%s,%s))/({in:free}*{in:days}),0)' % (MIN1, CH('minutes'), CH('status'), OVD)),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s&", "&%s&" "&%s,%s&" "&%s)' % (OD1, wa('Start with'), PL1('chore'), OD1, wa('days overdue'), wa('Nothing is overdue, next is'), PL1('chore')))],
    GR('What if', ('Free 20 minutes a day', {'free': 20}), ('Free 30 minutes a day', {'free': 30}), ('Free 60 minutes a day', {'free': 60}), ('Free 90 minutes a day', {'free': 90}), ('3 days left', {'days': 3}))))

# 2 rotation generator
def RM(g, s, col):
    return 'IF({in:method}=%s,SUMIFS(%s,%s,%d,%s,%s),SUMIFS(%s,%s,%d,%s,%s))' % (ROT, R('rotation', col), R('rotation', 'grp'), g, R('rotation', 'side_rot'), s, R('rotation', col), R('rotation', 'grp'), g, R('rotation', 'side_bal'), s)
PX, PY = 'MOD({in:week}-1,2)', '(1-MOD({in:week}-1,2))'
M2 = lambda g, s, c='min_week': 'ROUND(%s,0)' % RM(g, s, c)
GAP2 = 'ABS(%s-%s)' % (RM(1, PX, 'pts_week'), RM(1, PY, 'pts_week'))
tools.append(TOOL('rotation_tool', 'Chore Rotation Generator', 'Who takes which chores in a given week',
    'Chooses a method (rotation or balance by points) and a week 1 to 4; the minutes and points of each person come from the Chore rotation sheet, before any swap.', [
    IL('method', 'Method', 'meth', 'Rotation'), I('week', 'Week of the rotation, 1 to 4', 1), I('tol', 'Balanced when adults are within this many points', 10)], [
    O('Adult 1 minutes a week', 'int', M2(1, PX)), O('Adult 2 minutes a week', 'int', M2(1, PY)), O('Child 1 minutes a week', 'int', M2(2, PX)), O('Child 2 minutes a week', 'int', M2(2, PY)),
    O('Adult 1 points a week', 'num', 'ROUND(%s,1)' % RM(1, PX, 'pts_week')), O('Adult 2 points a week', 'num', 'ROUND(%s,1)' % RM(1, PY, 'pts_week')),
    O('Gap between adults, points', 'num', 'ROUND(%s,1)' % GAP2), O('Gap between adults, minutes', 'int', 'ROUND(ABS(%s-%s),0)' % (RM(1, PX, 'min_week'), RM(1, PY, 'min_week'))),
    O('Verdict', 'text', 'IF(%s<={in:tol},%s&" "&ROUND(%s,0)&" "&%s,IF(%s>%s,{set:adult1},{set:adult2})&" "&%s&" "&ROUND(%s,0)&" "&%s)' % (
        GAP2, wa('Balanced within'), GAP2, wa('points'), RM(1, PX, 'pts_week'), RM(1, PY, 'pts_week'), wa('carries'), GAP2, wa('more points')))],
    GR('What if', ('Balance, week 1', {'method': '=' + tok('meth', 'Balance by points'), 'week': 1}), ('Balance, week 2', {'method': '=' + tok('meth', 'Balance by points'), 'week': 2}),
       ('Rotation, week 2', {'method': '=' + ROT, 'week': 2}), ('Rotation, tolerance 20', {'tol': 20}), ('Balance, tolerance 20', {'method': '=' + tok('meth', 'Balance by points'), 'tol': 20}))))

# 3 fairness last 30 days
WIN = ('{today}-{in:days}+1', '{today}')
MA1 = LOGW('minutes', A1, *WIN); MA2 = LOGW('minutes', A2, *WIN)
AG = 'IF({in:agreed}>0,{in:agreed},{set:agreed_split_a2})'
SH2 = 'IFERROR(%s/(%s+%s),0)' % (MA2, MA1, MA2)
GAPF = '(%s-%s)' % (SH2, AG)
tools.append(TOOL('fairness_tool', 'Fairness Check, Last 30 Days', 'Do the adults carry the chores as agreed',
    'Minutes and points of each adult over the days you type, the share of adult minutes and the gap to the agreed share; a view calculated from your entries, never an alarm.', [
    I('days', 'Days to look back', 30), I('agreed', 'Adult 2 agreed share, 0 uses Settings', 0, 'pct')], [
    O('Adult 1 minutes', 'int', MA1), O('Adult 2 minutes', 'int', MA2), O('Adult minutes together', 'int', '%s+%s' % (MA1, MA2)), O('Adult 2 share of adult minutes', 'pct', SH2),
    O('Adult 1 share of adult minutes', 'pct', 'IFERROR(%s/(%s+%s),0)' % (MA1, MA1, MA2)), O('Agreed share of adult 2', 'pct', AG), O('Gap to the agreed share, points of share', 'pct', GAPF),
    O('Adult 1 points', 'int', LOGW('points', A1, *WIN)), O('Adult 2 points', 'int', LOGW('points', A2, *WIN)), O('Adult 2 minutes above the agreed share', 'int', '%s-%s*(%s+%s)' % (MA2, AG, MA1, MA2)),
    O('Verdict', 'text', 'IF(ABS(%s)<={set:fair_band},%s,IF(%s>0,{set:adult2}&" "&%s&" "&%s&"%% "&%s&" "&%s&"%%",{set:adult1}&" "&%s&" "&%s&"%% "&%s&" "&%s&"%%"))' % (
        GAPF, wa('In line with the agreed share'), GAPF, wa('carries'), 'ROUND(%s*100,0)' % SH2, wa('of adult minutes against an agreed'), 'ROUND(%s*100,0)' % AG,
        wa('carries'), 'ROUND((1-%s)*100,0)' % SH2, wa('of adult minutes against an agreed'), 'ROUND((1-%s)*100,0)' % AG))],
    GR('What if', ('Look back 14 days', {'days': 14}), ('Look back 60 days', {'days': 60}), ('Look back 90 days', {'days': 90}), ('Agreed 60%', {'agreed': 0.6}), ('Agreed 65%', {'agreed': 0.65}))))

# 4 fairness with hidden jobs
SH2H = 'IFERROR((%s+{in:hid2})/(%s+%s+{in:hid1}+{in:hid2}),0)' % (MA2, MA1, MA2)
SH1H = 'IFERROR((%s+{in:hid1})/(%s+%s+{in:hid1}+{in:hid2}),0)' % (MA1, MA1, MA2)
tools.append(TOOL('hidden_tool', 'Fairness With Hidden Jobs', 'Who carries the planning, booking and remembering too',
    'The same check after adding the hidden jobs (planning, booking, remembering) that are not on the chart, with the minutes you type for each adult.', [
    I('days', 'Days to look back', 30), I('hid1', 'Hidden minutes of adult 1 in those days', 180), I('hid2', 'Hidden minutes of adult 2 in those days', 30), I('agreed', 'Adult 2 agreed share, 0 uses Settings', 0, 'pct')], [
    O('Adult 1 visible minutes', 'int', MA1), O('Adult 2 visible minutes', 'int', MA2), O('Adult 1 minutes with hidden jobs', 'int', '%s+{in:hid1}' % MA1), O('Adult 2 minutes with hidden jobs', 'int', '%s+{in:hid2}' % MA2),
    O('Adult 2 share, visible only', 'pct', SH2), O('Adult 2 share with hidden jobs', 'pct', SH2H), O('Adult 1 share with hidden jobs', 'pct', SH1H),
    O('Shift in adult 2 share, points of share', 'pct', '%s-%s' % (SH2H, SH2)), O('Hidden minutes a month in the Hidden jobs sheet', 'int', 'SUM(%s)' % R('hidden', 'min_month')),
    O('Verdict', 'text', '%s&" "&{set:adult1}&" "&%s&" "&ROUND(%s*100,0)&"%% "&%s&" "&ROUND((1-%s)*100,0)&"%%"' % (wa('With hidden jobs'), wa('carries'), SH1H, wa('of adult minutes against an agreed'), AG))],
    GR('What if', ('No hidden minutes', {'hid1': 0, 'hid2': 0}), ('Adult 1 hidden 120', {'hid1': 120}), ('Adult 1 hidden 300', {'hid1': 300}), ('Shared, 100 each', {'hid1': 100, 'hid2': 100}), ('Look back 60 days', {'days': 60, 'hid1': 360, 'hid2': 60}))))

# 5 away week
DL5 = 'COUNTIFS(%s,{in:person},%s,%s,%s)' % (CH('owner'), CH('frequency'), DAILY, NOTPAU)
OT5 = 'COUNTIFS(%s,{in:person},%s,"<="&({today}+{in:days}-1),%s,"<>"&%s,%s)' % (CH('owner'), CH('next_due'), CH('frequency'), DAILY, NOTPAU)
EX5 = 'ROUND(SUMIFS(%s,%s,{in:person})*{in:days}/7,0)' % (CH('min_week'), CH('owner'))
US5 = 'ROUND(SUMIFS(%s,%s,{in:cover}),0)' % (CH('min_week'), CH('owner'))
tools.append(TOOL('away_tool', 'Chore Week One Person Away', 'Who takes the chores when someone is away',
    'Remove one person for the days you type: their daily and due chores become unowned and the person covering takes the minutes.', [
    IL('person', 'Person away', 'person', 'Adult 2'), I('days', 'Days away', 5), IL('cover', 'Covered by', 'person', 'Adult 1')], [
    O('Chores owned by the person', 'int', 'COUNTIFS(%s,{in:person},%s)' % (CH('owner'), NOTPAU)), O('Minutes a week owned', 'int', 'ROUND(SUMIFS(%s,%s,{in:person}),0)' % (CH('min_week'), CH('owner'))),
    O('Daily chores that need a doer', 'int', DL5), O('Other chores falling due in those days', 'int', OT5), O('Chores unowned in those days', 'int', '%s+%s' % (DL5, OT5)),
    O('Minutes to cover in those days', 'int', EX5), O('Usual minutes a week of who covers', 'int', US5), O('Week of who covers with the extra', 'int', '%s+%s' % (US5, EX5)),
    O('Extra as a share of their usual week', 'pct', 'IFERROR(%s/%s,0)' % (EX5, US5)),
    O('Verdict', 'text', 'IF({in:person}={in:cover},%s,(%s+%s)&" "&%s&" "&{in:cover}&" "&%s&" "&%s&" "&%s)' % (wa('Choose another person to cover'), DL5, OT5, wa('chores unowned,'), wa('takes'), EX5, wa('more minutes')))],
    GR('What if', ('2 days away', {'days': 2}), ('3 days away', {'days': 3}), ('A full week', {'days': 7}), ('Child 1 away', {'person': '=' + C1, 'days': 3}), ('Adult 1 away, adult 2 covers', {'person': '=' + A1, 'cover': '=' + A2}))))

# 6 children's points and reward
BAL6 = '(SUMIFS(%s,%s,{in:child},%s,13)+{in:extra})' % (R('child_points', 'balance'), R('child_points', 'child'), R('child_points', 'wkn'))
NX6 = 'SUMPRODUCT(MIN(%s+(%s<=%s)*1000000))' % (R('rewards', 'points'), R('rewards', 'points'), BAL6)
RN6 = 'IF(%s>=1000000,"",INDEX(%s,MATCH(%s,%s,0)))' % (NX6, R('rewards', 'reward'), NX6, R('rewards', 'points'))
PT6 = LOGW('points', '{in:child}', WS, '{today}') + '+{in:extra}'
tools.append(TOOL('child_points_tool', 'Children Points and Reward', 'How many points to the next reward this week',
    'Pick a child: points earned this week against the goal, the balance carried forward and the points to the next reward on the ladder. Points, never money.', [
    IL('child', 'Child', 'kid', 'Child 1'), I('extra', 'Extra points to test', 0)], [
    O('Points this week', 'int', '(%s)' % PT6), O('Weekly points goal', 'int', '{set:weekly_points_goal}'), O('Points to the goal', 'int', 'MAX(0,{set:weekly_points_goal}-(%s))' % PT6),
    O('Share of the goal', 'pct', 'IFERROR((%s)/{set:weekly_points_goal},0)' % PT6), O('Balance carried forward', 'int', BAL6), O('Next reward', 'text', RN6),
    O('Points needed for it', 'int', 'IF(%s>=1000000,"",%s)' % (NX6, NX6)), O('Points to the next reward', 'int', 'IF(%s>=1000000,0,%s-%s)' % (NX6, NX6, BAL6)),
    O('Rewards within reach now', 'int', 'COUNTIFS(%s,"<="&%s)' % (R('rewards', 'points'), BAL6)),
    O('Verdict', 'text', 'IF(%s>=1000000,%s,(%s-%s)&" "&%s&" "&%s)' % (NX6, wa('All rewards reached'), NX6, BAL6, wa('points to'), RN6))],
    GR('What if', ('Add 10 points', {'extra': 10}), ('Add 25 points', {'extra': 25}), ('Add 50 points', {'extra': 50}), ('Child 2', {'child': '=' + tok('kid', 'Child 2')}), ('Child 2, add 20', {'child': '=' + tok('kid', 'Child 2'), 'extra': 20}))))

# 7 reward ladder calculator
NX7 = 'SUMPRODUCT(MIN(%s+(%s<={in:balance})*1000000))' % (R('rewards', 'points'), R('rewards', 'points'))
NY7 = 'SUMPRODUCT(MIN(%s+(%s<=%s)*1000000))' % (R('rewards', 'points'), R('rewards', 'points'), NX7)
RN7 = 'IF(%s>=1000000,"",INDEX(%s,MATCH(%s,%s,0)))' % (NX7, R('rewards', 'reward'), NX7, R('rewards', 'points'))
tools.append(TOOL('ladder_tool', 'Reward Ladder Calculator', 'Where does a typed balance sit on the reward ladder',
    'Type a points balance and the points a week: the next two rewards, the points to go and the weeks to reach them at that pace.', [
    I('balance', 'Points balance', 91), I('weekly', 'Points a week at the usual pace', 25)], [
    O('Next reward', 'text', RN7), O('Points needed', 'int', 'IF(%s>=1000000,"",%s)' % (NX7, NX7)), O('Points to go', 'int', 'IF(%s>=1000000,0,%s-{in:balance})' % (NX7, NX7)),
    O('Weeks to the next reward', 'int', 'IF(%s>=1000000,0,IF({in:weekly}>0,ROUNDUP((%s-{in:balance})/{in:weekly},0),""))' % (NX7, NX7)),
    O('Reward after that', 'text', 'IF(%s>=1000000,"",INDEX(%s,MATCH(%s,%s,0)))' % (NY7, R('rewards', 'reward'), NY7, R('rewards', 'points'))),
    O('Points needed for it', 'int', 'IF(%s>=1000000,"",%s)' % (NY7, NY7)), O('Weeks to reach it', 'int', 'IF(%s>=1000000,"",IF({in:weekly}>0,ROUNDUP((%s-{in:balance})/{in:weekly},0),""))' % (NY7, NY7)),
    O('Rewards within reach now', 'int', 'COUNTIFS(%s,"<="&{in:balance})' % R('rewards', 'points')), O('Points of the top reward', 'int', 'MAX(%s)' % R('rewards', 'points')),
    O('Verdict', 'text', 'IF(%s>=1000000,%s,%s&" "&%s&" "&%s&" "&(%s-{in:balance})&" "&%s)' % (NX7, wa('All rewards reached'), wa('Next reward'), RN7, wa('in'), NX7, wa('points')))],
    GR('What if', ('Balance 0', {'balance': 0}), ('Balance 40', {'balance': 40}), ('Balance 100', {'balance': 100}), ('Balance 70', {'balance': 70}), ('25 points a week, balance 20', {'balance': 20, 'weekly': 15}))))

# 8 points balance carried forward
CPS = lambda col: 'SUMIFS(%s,%s,{in:child},%s,{in:week})' % (R('child_points', col), R('child_points', 'child'), R('child_points', 'wkn'))
tools.append(TOOL('balance_tool', 'Points Balance Carried', 'What balance does a child carry to next week',
    'Pick a child and a week 1 to 13: points earned, points spent, the balance at the end of the week and what carries forward after the points you plan to spend.', [
    IL('child', 'Child', 'kid', 'Child 1'), I('week', 'Week number, 1 to 13', 12), I('spend', 'Points to spend now', 10)], [
    O('Points earned in the week', 'int', CPS('points')), O('Points spent in the week', 'int', CPS('spent')), O('Balance at the end of the week', 'int', CPS('balance')),
    O('Balance carried in', 'int', '%s-%s+%s' % (CPS('balance'), CPS('points'), CPS('spent'))), O('Points to spend now', 'int', '{in:spend}'), O('Balance carried to next week', 'int', '%s-{in:spend}' % CPS('balance')),
    O('Weekly points goal', 'int', '{set:weekly_points_goal}'), O('Goal reached that week, 1 or 0', 'int', CPS('reached')),
    O('Verdict', 'text', 'IF(OR({in:week}<1,{in:week}>13),%s,%s&" "&(%s-{in:spend})&", "&%s)' % (wb('Pick a week from 1 to 13'), wa('Balance'), CPS('balance'), wa('carried to next week')))],
    GR('What if', ('Spend 30 points', {'spend': 30}), ('Spend 45 points', {'spend': 45}), ('Spend 60 points', {'spend': 60}), ('Week 8', {'week': 8}), ('Child 2, week 12', {'child': '=' + tok('kid', 'Child 2'), 'week': 12}))))

# 9 laundry planner
DAYS = [(MON, 'Monday'), (TUE, 'Tuesday'), (WED, 'Wednesday'), (THU, 'Thursday'), (FRI, 'Friday'), (SAT, 'Saturday'), (SUN, 'Sunday')]
def LD9(t): return '(SUMIFS(%s,%s,%s)+IF({in:add_day}=%s,{in:add_loads},0))' % (R('laundry', 'loads_wk'), R('laundry', 'usual_day'), t, t)
ADD9 = 'SUMIFS(%s,%s,{in:add_day})+{in:add_loads}' % (R('laundry', 'loads_wk'), R('laundry', 'usual_day'))
MX9 = 'MAX(MAX(%s),%s)' % (R('laundry', 'day_loads'), ADD9)
BD9 = 'IF(%s>MAX(%s),{in:add_day},IFERROR(INDEX(%s,1),""))' % (ADD9, R('laundry', 'day_loads'), R('laundry', 'busy_day'))
tools.append(TOOL('laundry_tool', 'Laundry Rota Planner', 'Which day is the busiest laundry day',
    'Loads a week for each day from the Laundry rota; add loads on a day to see whether the busiest day moves.', [
    IL('add_day', 'Add loads on', 'wday', 'Wednesday'), I('add_loads', 'Loads to add', 0, 'num')], [
    O('Loads on ' + n, 'num', LD9(t)) for t, n in DAYS] + [
    O('Loads a week, all days', 'num', 'SUM(%s)+{in:add_loads}' % R('laundry', 'loads_wk')), O('Minutes a week', 'int', 'ROUND(SUM(%s)+{in:add_loads}*IFERROR(SUM(%s)/SUM(%s),0),0)' % (R('laundry', 'min_week'), R('laundry', 'min_week'), R('laundry', 'loads_wk')), ),
    O('Busiest day', 'text', BD9), O('Loads on the busiest day', 'num', MX9),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&%s' % (wa('Busiest laundry day'), BD9, MX9, wa('loads')))],
    GR('What if', ('Add 2 loads on Monday', {'add_day': '=' + MON, 'add_loads': 2}), ('Add 1 load on Tuesday', {'add_day': '=' + TUE, 'add_loads': 1}), ('Add 2 loads on Thursday', {'add_day': '=' + THU, 'add_loads': 2}),
       ('Add 1 load on Saturday', {'add_day': '=' + SAT, 'add_loads': 1}), ('Add 3 loads on Sunday', {'add_day': '=' + SUN, 'add_loads': 3}))))

# 10 bedding and towel next change
NC10 = 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (R('laundry', 'next_change'), R('laundry', 'next_change'))
LK10 = lambda tk: 'IF(SUMIFS(%s,%s,%s)=0,"",SUMIFS(%s,%s,%s))' % (R('laundry', 'next_change'), R('laundry', 'load'), tk, R('laundry', 'next_change'), R('laundry', 'load'), tk)
tools.append(TOOL('bedding_tool', 'Bedding and Towel Next Change', 'When is the next bedding and towel change',
    'Type the last change and the interval (typical, your own habit): the next date, plus the nearest change in the Laundry rota.', [
    I('interval', 'Change every, days', 14), I('last', 'Last change on', 'today-9', 'date')], [
    O('Next change on', 'date', '{in:last}+{in:interval}'), O('Days to the change', 'int', '{in:last}+{in:interval}-{today}'), O('Changes a year at this interval', 'num', 'ROUND(365/{in:interval},1)'),
    O('Nearest change in the rota', 'date', NC10), O('Load type of that change', 'text', 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0)))' % (NC10, R('laundry', 'load'), NC10, R('laundry', 'next_change'))),
    O('Next change of towels', 'date', LK10(tok('ltype', 'Towels'))), O('Next change of main bedroom bed linen', 'date', LK10(tok('ltype', 'Bed linen, main bedroom'))),
    O('Changes overdue in the rota', 'int', 'COUNTIFS(%s,%s)' % (R('laundry', 'status'), OVD)),
    O('Verdict', 'text', 'IF({in:last}+{in:interval}<{today},%s,%s)' % (wb('Change the bedding now'), wa('Change the bedding on the date shown')))],
    GR('What if', ('Every 7 days', {'interval': 7}), ('Every 10 days', {'interval': 10}), ('Every 21 days', {'interval': 21}), ('Every 30 days', {'interval': 30}), ('Last change 20 days ago', {'last': '={today}-20'}))))

# 11 chore swap tester
def CX(c, n): return 'INDEX(%s,{in:%s})' % (CH(c), n)
def M30(n): return 'SUMIFS(%s,%s,%s,%s,">="&(%s),%s,"<="&{today})' % (R('chore_log', 'minutes'), R('chore_log', 'chore_id'), CX('chore_id', n), R('chore_log', 'done'), W30, R('chore_log', 'done'))
D2 = '((%s=%s)*(%s-%s)+(%s=%s)*(%s-%s))' % (CX('owner', 'cha'), A2, M30('chb'), M30('cha'), CX('owner', 'chb'), A2, M30('cha'), M30('chb'))
D1 = '((%s=%s)*(%s-%s)+(%s=%s)*(%s-%s))' % (CX('owner', 'cha'), A1, M30('chb'), M30('cha'), CX('owner', 'chb'), A1, M30('cha'), M30('chb'))
N1, N2 = LOGW('minutes', A1, W30, '{today}'), LOGW('minutes', A2, W30, '{today}')
S_NOW = 'IFERROR(%s/(%s+%s),0)' % (N2, N1, N2)
S_AFT = 'IFERROR((%s+%s)/(%s+%s+%s+%s),0)' % (N2, D2, N1, D1, N2, D2)
BAD = 'OR({in:cha}<1,{in:cha}>45,{in:chb}<1,{in:chb}>45)'
tools.append(TOOL('swap_tool', 'Chore Swap Tester', 'What happens to the shares if two chores swap owners',
    'Type two chore numbers (the number in the Chore ID): the owners swap them and the shares of adult minutes of the last 30 days are recalculated.', [
    I('cha', 'Chore A number, 1 to 45', 21), I('chb', 'Chore B number, 1 to 45', 5)], [
    O('Chore A', 'text', CX('chore', 'cha')), O('Owner of chore A', 'text', CX('owner', 'cha')), O('Minutes of chore A, last 30 days', 'int', M30('cha')),
    O('Chore B', 'text', CX('chore', 'chb')), O('Owner of chore B', 'text', CX('owner', 'chb')), O('Minutes of chore B, last 30 days', 'int', M30('chb')),
    O('Adult 2 share now', 'pct', S_NOW), O('Adult 2 share after the swap', 'pct', S_AFT), O('Adult 1 share after the swap', 'pct', '1-%s' % S_AFT), O('Adult 2 minutes after the swap', 'int', '%s+%s' % (N2, D2)),
    O('Verdict', 'text', 'IF(%s,%s,%s&" "&{set:adult2}&" "&%s&" "&ROUND(%s*100,0)&"%% "&%s&" "&ROUND(%s*100,0)&"%%")' % (BAD, wb('Pick a chore from 1 to 45'), wa('Swap moves'), wa('from'), S_NOW, wa('to'), S_AFT))],
    GR('What if', ('Shop and dust the surfaces', {'cha': 21, 'chb': 16}), ('Bathroom and vacuum', {'cha': 7, 'chb': 5}), ('Mop and vacuum', {'cha': 6, 'chb': 5}), ('Weekly shop and windows', {'cha': 21, 'chb': 35}), ('Oven and bathroom', {'cha': 26, 'chb': 7}))))

# 12 who does what on a late day
WP = lambda c: 'INDEX(%s,MATCH({in:date},%s,0))' % (R('work_pattern', c), R('work_pattern', 'date'))
IN12 = 'COUNTIFS(%s,{in:date})' % R('work_pattern', 'date')
DM12 = 'SUMIFS(%s,%s,%s,%s,1,%s)' % (CH('minutes'), CH('frequency'), DAILY, CH('grp'), NOTPAU)
DN12 = 'SUMIFS(%s,%s,{in:date},%s,1)' % (CH('minutes'), CH('next_due'), CH('grp'))
DC12 = 'COUNTIFS(%s,%s,%s,1,%s)+COUNTIFS(%s,{in:date},%s,1)' % (CH('frequency'), DAILY, CH('grp'), NOTPAU, CH('next_due'), CH('grp'))
TOT12 = 'MAX(0,%s+%s-{in:help})' % (DM12, DN12)
DOER = 'IF(IFERROR(%s,0)>IFERROR(%s,0),{set:adult2},{set:adult1})' % (WP('a2_free'), WP('a1_free'))
tools.append(TOOL('lateday_tool', 'Who Does What on a Late Day', 'Who does the evening chores on a late day',
    'Pick a date: adult 1 late day and adult 2 shift from the work pattern, the free minutes of each adult and the adult chores of that evening; type what a grandparent or sitter covers.', [
    I('date', 'Date', DD.iso(OVERLAP_DAY), 'date'), I('help', 'Minutes a grandparent or sitter covers', 0)], [
    O('Adult 1 late day, 1 or 0', 'int', 'COUNTIFS(%s,{in:date},%s,%s)' % (R('work_pattern', 'date'), R('work_pattern', 'adult1_late'), YES)), O('Adult 2 shift', 'text', 'IFERROR(%s&"","")' % WP('adult2_shift')),
    O('Adult 1 free minutes', 'int', 'IFERROR(%s,0)' % WP('a1_free')), O('Adult 2 free minutes', 'int', 'IFERROR(%s,0)' % WP('a2_free')), O('Daily adult chore minutes', 'int', DM12),
    O('Adult chore minutes due that date', 'int', DN12), O('Evening chore minutes after help', 'int', TOT12), O('Adult with more free minutes', 'text', DOER),
    O('Minutes that adult takes', 'int', 'MIN(%s,IF(%s={set:adult2},IFERROR(%s,0),IFERROR(%s,0)))' % (TOT12, DOER, WP('a2_free'), WP('a1_free'))), O('Chores that evening', 'int', DC12),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s=0,%s,%s&" "&%s&" "&(%s)&" "&%s&", "&%s&" "&%s))' % (IN12, wb('Date is outside the work pattern'), TOT12, wb('Nothing due that day'), DOER, wa('does'), DC12, wa('chores'), TOT12, wa('minutes')))],
    GR('What if', ('Tomorrow', {'date': '={today}+1'}), ('In 3 days', {'date': '={today}+3'}), ('In 5 days', {'date': '={today}+5'}), ('Grandparent helps 20', {'help': 20}), ('Sitter helps 30', {'help': 30}))))

# 13 free minutes by shift week
WK13 = '(%s+7*{in:weeks})' % WS
FM = lambda c: 'SUMIFS(%s,%s,%s)' % (R('work_pattern', c), R('work_pattern', 'week_start'), WK13)
LT13 = 'COUNTIFS(%s,%s,%s,%s)' % (R('work_pattern', 'week_start'), WK13, R('work_pattern', 'adult2_shift'), LATE)
AV13 = 'IFERROR(SUM(%s)/60/(COUNT(%s)/7),0)' % (R('work_pattern', 'a2_free'), R('work_pattern', 'date'))
tools.append(TOOL('free_tool', 'Free Minutes by Shift Week', 'How many free hours does each adult have in a shift week',
    'Pick a week (0 is this week, -8 to 8): free minutes of each adult from the work pattern and Settings, with adult 2 late shifts that week; typical values, your own.', [
    I('weeks', 'Weeks from this week', 3)], [
    O('Week starts', 'date', WK13), O('Adult 2 late shifts that week', 'int', LT13), O('Adult 1 late days that week', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (R('work_pattern', 'week_start'), WK13, R('work_pattern', 'adult1_late'), YES)),
    O('Adult 1 free minutes', 'int', FM('a1_free')), O('Adult 2 free minutes', 'int', FM('a2_free')), O('Adult 1 free hours', 'num', 'ROUND(%s/60,1)' % FM('a1_free')),
    O('Adult 2 free hours', 'num', 'ROUND(%s/60,1)' % FM('a2_free')), O('Adult 2 average free hours a week', 'num', 'ROUND(%s,1)' % AV13), O('Adult 2 hours against the average', 'num', 'ROUND(%s/60-%s,1)' % (FM('a2_free'), AV13)),
    O('Verdict', 'text', '{set:adult2}&" "&%s&" "&ROUND(%s/60,1)&" "&IF(%s>=3,%s,%s)' % (wa('has'), FM('a2_free'), LT13, wb('free hours on late weeks'), wb('free hours on a usual week')))],
    GR('What if', ('This week', {'weeks': 0}), ('Next week', {'weeks': 1}), ('In 2 weeks', {'weeks': 2}), ('In 4 weeks', {'weeks': 4}), ('2 weeks ago', {'weeks': -2}))))

# 14 compare with own history
HMS = lambda c, d: 'SUMIFS(%s,%s,%s)' % (R('history', c), R('history', 'month'), d)
AVG14 = 'IFERROR(AVERAGEIFS(%s,%s,">="&EDATE(%s,-{in:months}),%s,"<"&%s),0)' % (R('history', 'a2_share'), R('history', 'month'), MSD, R('history', 'month'), MSD)
THIS14 = HMS('a2_share', MSD)
tools.append(TOOL('compare_tool', 'Compare With Own History', 'Is adult 2 share this month above your own average',
    'This month so far against the complete months before it, from your own Chore log; the band is a gap of share, your own.', [
    I('band', 'In line when within this gap of share', 0.05, 'pct'), I('months', 'Complete months before this month, 1 to 6', 3)], [
    O('Adult 2 share this month so far', 'pct', THIS14), O('Average of the months before', 'pct', AVG14), O('Gap to your own average, points of share', 'pct', '%s-%s' % (THIS14, AVG14)),
    O('Adult 2 share, 1 month before', 'pct', HMS('a2_share', 'EDATE(%s,-1)' % MSD)), O('Adult 2 share, 2 months before', 'pct', HMS('a2_share', 'EDATE(%s,-2)' % MSD)), O('Adult 2 share, 3 months before', 'pct', HMS('a2_share', 'EDATE(%s,-3)' % MSD)),
    O('Adult minutes this month so far', 'int', '%s+%s' % (HMS('a1_min', MSD), HMS('a2_min', MSD))),
    O('Adult minutes a month, average before', 'int', 'IFERROR(ROUND((SUMIFS(%s,%s,">="&EDATE(%s,-{in:months}),%s,"<"&%s)+SUMIFS(%s,%s,">="&EDATE(%s,-{in:months}),%s,"<"&%s))/{in:months},0),0)' % (
        R('history', 'a1_min'), R('history', 'month'), MSD, R('history', 'month'), MSD, R('history', 'a2_min'), R('history', 'month'), MSD, R('history', 'month'), MSD)),
    O('Verdict', 'text', 'IF(%s-%s>{in:band},%s,IF(%s-%s<-{in:band},%s,%s))' % (THIS14, AVG14, wb('Above your own average'), THIS14, AVG14, wb('Below your own average'), wb('In line with your own average')))],
    GR('What if', ('Band 2 points', {'band': 0.02}), ('Band 10 points', {'band': 0.1}), ('2 months before', {'months': 2}), ('6 months before', {'months': 6}), ('Band 15 points', {'band': 0.15}))))

# 15 done and missed streak
DMR = lambda c: R('done_missed', c)
LF15 = 'MAX(' + ','.join('IF(COUNTIFS(%s,%d,%s,"<"&{in:goal})>0,%d,0)' % (DMR('wkn'), k, DMR('share_done'), k) for k in range(1, 13)) + ')'
ST4 = lambda c: 'SUMIFS(%s,%s,">=9",%s,"<=12")' % (DMR(c), DMR('wkn'), DMR('wkn'))
tools.append(TOOL('streak_tool', 'Done and Missed Streak', 'How many weeks in a row did we reach the completion goal',
    'Type a completion goal: the weeks in a row at goal ending last week, the weeks at goal of the last 12 and the share done in the last 4 complete weeks.', [
    I('goal', 'Weekly completion goal', 0.85, 'pct')], [
    O('Share done last week', 'pct', 'SUMIFS(%s,%s,12)' % (DMR('share_done'), DMR('wkn'))), O('Weeks in a row at goal', 'int', '12-%s' % LF15),
    O('Weeks at goal of the last 12', 'int', 'COUNTIFS(%s,">="&{in:goal},%s,"<=12")' % (DMR('share_done'), DMR('wkn'))), O('Weeks below goal of the last 12', 'int', 'COUNTIFS(%s,"<"&{in:goal},%s,"<=12")' % (DMR('share_done'), DMR('wkn'))),
    O('Share done, last 4 complete weeks', 'pct', 'IFERROR(%s/%s,0)' % (ST4('done'), ST4('due'))), O('Chores missed, last 4 complete weeks', 'int', ST4('missed')),
    O('Best week share of the 13', 'pct', 'MAX(%s)' % DMR('share_done')),
    O('Verdict', 'text', 'IF(12-%s>0,(12-%s)&" "&%s,%s)' % (LF15, LF15, wb('weeks in a row at goal'), wb('Below goal last week')))],
    GR('What if', ('Goal 70%', {'goal': 0.7}), ('Goal 80%', {'goal': 0.8}), ('Goal 90%', {'goal': 0.9}), ('Goal 95%', {'goal': 0.95}), ('Goal 100%', {'goal': 1}))))

# 16 time to clear the overdue list
OM16 = 'SUMIFS(%s,%s,%s)' % (CH('minutes'), CH('status'), OVD)
D7 = 'SUMIFS(%s,%s,">="&{today},%s,"<="&({today}+6),%s)' % (CH('minutes'), CH('next_due'), CH('next_due'), NOTPAU)
BK16 = '(%s+{in:next7}*%s)' % (OM16, D7)
OC16 = 'COUNTIFS(%s,%s)' % (CH('status'), OVD)
tools.append(TOOL('clear_tool', 'Time to Clear Overdue List', 'How many days to clear the overdue chores',
    'The minutes of the overdue chores (and, if you choose, those falling due in the next 7 days) against the minutes a day you can give.', [
    I('per_day', 'Minutes a day for catching up', 30), I('next7', 'Add chores due in the next 7 days, 1 yes 0 no', 0)], [
    O('Chores overdue', 'int', OC16), O('Overdue minutes', 'int', OM16), O('Minutes falling due in the next 7 days', 'int', D7), O('Backlog to clear, minutes', 'int', BK16),
    O('Days to clear', 'int', 'IFERROR(ROUNDUP(%s/{in:per_day},0),"")' % BK16), O('Cleared on', 'date', 'IF(%s=0,"",{today}+ROUNDUP(%s/{in:per_day},0))' % (BK16, BK16)),
    O('Minutes a day to clear in 7 days', 'int', 'ROUNDUP(%s/7,0)' % BK16), O('Longest overdue, days', 'int', 'MAX(%s)' % CH('overdue_days')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&ROUNDUP(%s/{in:per_day},0)&" "&%s&" "&{in:per_day}&" "&%s)' % (BK16, wb('Nothing is overdue'), wb('Clear in'), BK16, wb('days at'), wb('minutes a day')))],
    GR('What if', ('15 minutes a day', {'per_day': 15}), ('20 minutes a day', {'per_day': 20}), ('45 minutes a day', {'per_day': 45}), ('60 minutes a day', {'per_day': 60}), ('With the next 7 days', {'next7': 1, 'per_day': 45}))))

# 17 default frequency tuner
BAD17 = 'OR({in:nth}<1,{in:nth}>45)'
MN17 = lambda d: 'ROUND(%s*30/%s,0)' % (CX('minutes', 'nth'), d)
NOW17, AFT17 = MN17(CX('interval', 'nth')), MN17('{in:new_days}')
tools.append(TOOL('tuner_tool', 'Default Frequency Tuner', 'What changes if a chore repeats less or more often',
    'Pick a chore number and a new interval in days: the minutes a month before and after, calculated from your entries; no promise of saved time.', [
    I('nth', 'Chore number, 1 to 45', 7), I('new_days', 'New interval, days', 14)], [
    O('Chore', 'text', CX('chore', 'nth')), O('Frequency now', 'text', CX('frequency', 'nth')), O('Interval now, days', 'int', CX('interval', 'nth')), O('Minutes each time', 'int', CX('minutes', 'nth')),
    O('Minutes a month now', 'int', NOW17), O('Minutes a month after', 'int', AFT17), O('Change in minutes a month', 'int', '%s-%s' % (AFT17, NOW17)),
    O('Change in hours a year', 'num', 'ROUND((%s-%s)*12/60,1)' % (AFT17, NOW17)), O('Points a month after', 'num', 'ROUND(%s*30/{in:new_days},1)' % CX('points', 'nth')),
    O('Verdict', 'text', 'IF(%s,%s,%s&" "&(%s-%s)&" "&%s)' % (BAD17, wb('Pick a chore from 1 to 45'), wb('Moves'), AFT17, NOW17, wb('minutes a month')))],
    GR('What if', ('Every 7 days', {'new_days': 7}), ('Every 10 days', {'new_days': 10}), ('Every 30 days', {'new_days': 30}), ('Every 91 days', {'new_days': 91}), ('Oven, every 60 days', {'nth': 26, 'new_days': 60}))))

# 18 spring clean planner
RM18 = 'SUMIFS(%s,%s,{in:room},%s,"<>"&%s,%s,"<>"&%s,%s)' % (CH('minutes'), CH('room'), CH('hidden'), YES, CH('frequency'), DAILY, NOTPAU)
AL18 = 'SUMIFS(%s,%s,"<>"&%s,%s,"<>"&%s,%s)' % (CH('minutes'), CH('hidden'), YES, CH('frequency'), DAILY, NOTPAU)
DR18 = 'ROUND(%s*{in:factor},0)' % RM18
tools.append(TOOL('spring_tool', 'Spring Clean Planner', 'How many days does a deep clean of a room take',
    'Pick a room, a pace and how many times the usual minutes a deep clean takes: the minutes and days for the room and for the whole home.', [
    IL('room', 'Room', 'room', 'Kitchen'), I('pace', 'Minutes a day for the deep clean', 90), I('factor', 'Times the usual minutes', 1.5, 'num')], [
    O('Chores in the room, daily ones left out', 'int', 'COUNTIFS(%s,{in:room},%s,"<>"&%s,%s,"<>"&%s,%s)' % (CH('room'), CH('hidden'), YES, CH('frequency'), DAILY, NOTPAU)),
    O('Usual minutes of those chores', 'int', RM18), O('Deep clean minutes of the room', 'int', DR18), O('Days for the room', 'int', 'ROUNDUP(%s/{in:pace},0)' % DR18),
    O('Longest chore in the room', 'text', 'IFERROR(INDEX(%s,MATCH({in:room}&"-1",%s,0)),"")' % (CH('chore'), CH('rkey'))), O('Deep clean minutes, whole home', 'int', 'ROUND(%s*{in:factor},0)' % AL18),
    O('Days for the whole home', 'int', 'ROUNDUP(%s*{in:factor}/{in:pace},0)' % AL18), O('Weekends for the whole home, 2 days each', 'int', 'ROUNDUP(%s*{in:factor}/{in:pace}/2,0)' % AL18),
    O('Verdict', 'text', 'ROUNDUP(%s/{in:pace},0)&" "&%s&" "&{in:pace}&" "&%s' % (DR18, wb('days at'), wb('minutes a day')))],
    GR('What if', ('60 minutes a day', {'pace': 60}), ('120 minutes a day', {'pace': 120}), ('180 minutes a day', {'pace': 180}), ('Factor 1', {'factor': 1}), ('Factor 2', {'factor': 2}))))
assert len(tools) == 18, len(tools)
