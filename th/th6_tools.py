"""Therapy practice suite part 6: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th6_lists import *

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
YES = '{list:yesno.yes}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
JAN1 = 'DATE(YEAR({today}),1,1)'
def W30(c): return '{range:%s},">="&({today}-29),{range:%s},"<="&{today}' % (c, c)
def W90(c): return '{range:%s},">="&({today}-89),{range:%s},"<="&{today}' % (c, c)
SC3 = 'IF({in:sc}=%s,1,IF({in:sc}=%s,0.75,1.4))' % (tok('scen', 'Base'), tok('scen', 'Best'))
def eq(v): return '=' + v

tools = []
# 1 note timeliness
tools.append(TOOL('note_timeliness', 'Note Timeliness Check', 'Was this session note done within the rule?',
  'Type the session date and the date the note was done; the rule in Settings (2 days, flagged at 48 hours) gives the days late, the deadline and a verdict, beside your own last 30 days.', [
  I('sd', 'Session date', 'today-4', 'date'), I('nd', 'Date the note was done', 'today-2', 'date')], [
  O('Days from session to note', 'int', '{in:nd}-{in:sd}'), O('Hours from session to note', 'hours', '({in:nd}-{in:sd})*24'), O('Rule in days (Settings)', 'int', '{set:note_due_days}'),
  O('Flag threshold in hours', 'hours', '{set:note_due_days}*24'), O('Note deadline', 'date', '{in:sd}+{set:note_due_days}'), O('Days late (+) or early (-)', 'int', '{in:nd}-{in:sd}-{set:note_due_days}'),
  O('Your notes done within the rule, last 30 days', 'pct', 'IFERROR(COUNTIFS({range:notes.note_check},%s,%s)/COUNTIFS(%s,{range:notes.note_check},"<>"&%s),0)' % (ck('On time'), W30('notes.date'), W30('notes.date'), ck('Due soon'))),
  O('Verdict', 'text', 'IF({in:nd}-{in:sd}<={set:note_due_days},%s,%s)' % (ck('On time'), ck('Late')))],
  GR('What if', ('Note on day 3', {'nd': eq('{in:sd}+3')}), ('Note on the same day', {'nd': eq('{in:sd}')}), ('Note after a week', {'nd': eq('{in:sd}+7')}), ('Session 10 days ago', {'sd': '={today}-10'}))))
# 2 late notes by clinician (ranked)
RK = lambda k, col: 'IFERROR(INDEX({range:team.%s},MATCH(%d,{range:team.act_rank},0)),"")' % (col, k)
tools.append(TOOL('late_notes', 'Late Notes by Clinician', 'Which clinician to call first about overdue notes',
  'Type the overdue notes you accept per clinician and the minutes a note takes; the ranked list names who to call first, how many notes they owe and the minutes to clear everything.', [
  I('limit', 'Overdue notes you accept per clinician', 1), I('mins', 'Minutes to finish one note', 10)], [
  O('Call first: clinician', 'text', RK(1, 'name')), O('Overdue notes, first', 'int', RK(1, 'notes_overdue')), O('Call second: clinician', 'text', RK(2, 'name')), O('Overdue notes, second', 'int', RK(2, 'notes_overdue')),
  O('Call third: clinician', 'text', RK(3, 'name')), O('Overdue notes, third', 'int', RK(3, 'notes_overdue')), O('Overdue notes, all clinicians', 'int', 'SUM({range:team.notes_overdue})'),
  O('Clinicians over your limit', 'int', 'COUNTIFS({range:team.notes_overdue},">"&{in:limit})'), O('Minutes to clear every overdue note', 'int', 'SUM({range:team.notes_overdue})*{in:mins}'),
  O('Overdue notes above the limit', 'int', 'SUMIFS({range:team.notes_overdue},{range:team.notes_overdue},">"&{in:limit})-{in:limit}*COUNTIFS({range:team.notes_overdue},">"&{in:limit})'),
  O('Verdict', 'text', 'IF(SUM({range:team.notes_overdue})=0,%s,%s)' % (ck('Clear today'), ck('Catch up this week')))],
  GR('What if', ('Accept 3 overdue notes', {'limit': 3}), ('Accept none', {'limit': 0}), ('15 minutes a note', {'mins': 15}), ('5 minutes a note', {'mins': 5}))))
# 3 catch-up
MIN3 = '({in:cnt}*{in:mins}*%s)' % SC3
tools.append(TOOL('catch_up', 'Overdue Notes Catch-up', 'How many days to clear the overdue notes',
  'Type the overdue notes, minutes a note, free admin minutes a day and a scenario; see the working days to clear, the date and the extra minutes a day needed to clear in 2 days.', [
  I('cnt', 'Overdue notes to clear', 9), I('mins', 'Minutes to finish one note', 10), I('admin', 'Free admin minutes a day', 30), IL('sc', 'Scenario', 'scen', 'Base')], [
  O('Minutes needed in this scenario', 'num', MIN3), O('Working days to clear', 'int', 'ROUNDUP(%s/{in:admin},0)' % MIN3), O('Cleared by', 'date', 'WORKDAY({today},ROUNDUP(%s/{in:admin},0))' % MIN3),
  O('Extra admin minutes a day to clear in 2 days', 'int', 'MAX(0,ROUNDUP(%s/2,0)-{in:admin})' % MIN3), O('Notes you can clear in one day', 'int', 'INT({in:admin}/({in:mins}*%s))' % SC3),
  O('Overdue notes in your data now', 'int', 'COUNTIFS({range:notes.note_check},%s)' % ck('Overdue')),
  O('Verdict', 'text', 'IF(ROUNDUP(%s/{in:admin},0)<=5,%s,%s)' % (MIN3, ck('Clear this week'), ck('Add admin time')))],
  GR('What if', ('Worst case', {'sc': eq(tok('scen', 'Worst'))}), ('Best case', {'sc': eq(tok('scen', 'Best'))}), ('15 admin minutes a day', {'admin': 15}), ('20 overdue notes', {'cnt': 20}), ('Only 5 minutes a note', {'mins': 5}))))
# 4 plan review due date
NX4 = '({in:first}+{in:every}*({in:done}+1))'
tools.append(TOOL('review_due', 'Plan Review Due Date', 'When is the next treatment-plan review due',
  'Type the first session date, the days between reviews and the reviews done; see the next due date, the reviews missed so far and a verdict.', [
  I('first', 'First session date', 'today-200', 'date'), I('every', 'Days between reviews', 90), I('done', 'Reviews done so far', 2)], [
  O('Next review due', 'date', NX4), O('Days to the next review', 'int', NX4 + '-{today}'), O('Reviews due by today', 'int', 'INT(({today}-{in:first})/{in:every})'),
  O('Reviews missed so far', 'int', 'MAX(0,INT(({today}-{in:first})/{in:every})-{in:done})'), O('Review window opens', 'date', NX4 + '-7'),
  O('Plan reviews overdue in your data', 'int', 'COUNTIFS({range:reviews.status},%s)' % ck('Overdue')),
  O('Verdict', 'text', 'IF(%s<{today},%s,IF(%s-{today}<=7,%s,%s))' % (NX4, ck('Overdue'), NX4, ck('Due this week'), ck('On schedule')))],
  GR('What if', ('One review missed', {'done': 1}), ('Every 60 days', {'every': 60}), ('Every 120 days', {'every': 120}), ('Started today', {'first': '={today}'}), ('Review due this week', {'first': '={today}-85', 'done': 0}))))
# 5 review backlog
tools.append(TOOL('review_backlog', 'Review Backlog Planner', 'Hours a week to clear overdue plan reviews',
  'Type the overdue reviews, minutes a review, admin hours a week and the weeks you want; closed-form maths gives the weeks to clear and the weekly hours needed.', [
  I('cnt', 'Plan reviews overdue', 11), I('mins', 'Minutes per review', 25), I('hrs', 'Admin hours a week for reviews', 3, 'num'), I('weeks', 'Weeks in which you want it cleared', 4)], [
  O('Total hours to clear', 'num', '{in:cnt}*{in:mins}/60'), O('Weeks to clear at your hours', 'num', '{in:cnt}*{in:mins}/60/{in:hrs}'), O('Hours a week needed to clear in the weeks wanted', 'num', '{in:cnt}*{in:mins}/60/{in:weeks}'),
  O('Extra hours a week needed', 'num', 'MAX(0,{in:cnt}*{in:mins}/60/{in:weeks}-{in:hrs})'), O('Cleared by', 'date', '{today}+7*ROUNDUP({in:cnt}*{in:mins}/60/{in:hrs},0)'),
  O('Plan reviews overdue in your data', 'int', 'COUNTIFS({range:reviews.status},%s)' % ck('Overdue')),
  O('Oldest overdue review, days', 'int', 'IFERROR({today}-SUMPRODUCT(MIN(({range:reviews.status}=%s)*({range:reviews.due_date})+({range:reviews.status}<>%s)*99999)),0)' % (ck('Overdue'), ck('Overdue'))),
  O('Verdict', 'text', 'IF({in:cnt}*{in:mins}/60/{in:hrs}<={in:weeks},%s,%s)' % (ck('Clear the backlog'), ck('Add admin time')))],
  GR('What if', ('One admin hour a week', {'hrs': 1}), ('Six admin hours a week', {'hrs': 6}), ('20 reviews overdue', {'cnt': 20}), ('Clear in 2 weeks', {'weeks': 2}), ('Short reviews: 15 minutes', {'mins': 15}))))
# 6 outcome score change
CH6 = '({in:latest}-{in:intake})'
tools.append(TOOL('score_change', 'Outcome Score Change', 'Did this client\'s outcome score change enough',
  'Type the intake and latest scores (plain numbers, 0 to 40, lower is better); see the change, the change share and the band, beside the average of all your clients.', [
  I('intake', 'Intake score (0 to 40)', 24), I('latest', 'Latest score (0 to 40)', 15)], [
  O('Change in points (negative is lower)', 'int', CH6), O('Points lower than intake', 'int', '{in:intake}-{in:latest}'), O('Change share of the intake score', 'pct', 'IF({in:intake}=0,0,%s/{in:intake})' % CH6),
  O('Points that count as a real change', 'int', '{set:min_change_points}'),
  O('Average change in your data', 'num', 'IFERROR(AVERAGE({range:change.change}),0)'),
  O('Share of your clients improved', 'pct', 'IFERROR(COUNTIFS({range:change.band},%s)/(COUNTIFS({range:change.band},%s)+COUNTIFS({range:change.band},%s)+COUNTIFS({range:change.band},%s)),0)' % (ck('Improved'), ck('Improved'), ck('No change'), ck('Review the plan'))),
  O('Verdict', 'text', 'IF(%s<=-{set:min_change_points},%s,IF(%s>={set:min_change_points},%s,%s))' % (CH6, ck('Improved'), CH6, ck('Review the plan'), ck('No change')))],
  GR('What if', ('No change: 24 to 24', {'latest': 24}), ('Higher score: 31', {'latest': 31}), ('Small drop: 21', {'latest': 21}), ('Low intake 12 to 6', {'intake': 12, 'latest': 6}))))
# 7 caseload score summary (10 clients)
PAIRS = [(28, 16), (24, 15), (31, 22), (19, 18), (26, 12), (22, 21), (33, 19), (17, 10), (29, 25), (21, 9)]
ins7 = []
for j, (a, b) in enumerate(PAIRS, 1): ins7 += [I('i%d' % j, 'Client %d intake score' % j, a), I('l%d' % j, 'Client %d latest score' % j, b)]
V7 = lambda j: '(({in:i%d}>0)*({in:l%d}>0))' % (j, j)
N7 = '(' + '+'.join(V7(j) for j in range(1, 11)) + ')'
SI7 = '(' + '+'.join('%s*{in:i%d}' % (V7(j), j) for j in range(1, 11)) + ')'
SL7 = '(' + '+'.join('%s*{in:l%d}' % (V7(j), j) for j in range(1, 11)) + ')'
IMP7 = '(' + '+'.join('%s*(({in:l%d}-{in:i%d})<=-{set:min_change_points})' % (V7(j), j, j) for j in range(1, 11)) + ')'
WOR7 = '(' + '+'.join('%s*(({in:l%d}-{in:i%d})>={set:min_change_points})' % (V7(j), j, j) for j in range(1, 11)) + ')'
MIN7 = 'MIN(' + ','.join('IF(%s=1,{in:l%d}-{in:i%d},99)' % (V7(j), j, j) for j in range(1, 11)) + ')'
tools.append(TOOL('caseload_scores', 'Caseload Score Summary', 'Is one clinician\'s caseload improving',
  'Type the intake and latest scores of up to 10 clients (a blank or 0 skips a pair); see the average change, the share improved and a verdict beside your own history.', ins7, [
  O('Clients counted', 'int', N7), O('Average intake score', 'num', 'IF(%s=0,0,%s/%s)' % (N7, SI7, N7)), O('Average latest score', 'num', 'IF(%s=0,0,%s/%s)' % (N7, SL7, N7)),
  O('Average change in points (negative is lower)', 'num', 'IF(%s=0,0,(%s-%s)/%s)' % (N7, SL7, SI7, N7)), O('Clients improved', 'int', IMP7), O('Clients to review the plan for', 'int', WOR7),
  O('Share improved', 'pct', 'IF(%s=0,0,%s/%s)' % (N7, IMP7, N7)), O('Largest drop in points', 'int', 'IF(%s=0,0,%s)' % (N7, MIN7)),
  O('Share improved in your whole data', 'pct', 'IFERROR(COUNTIFS({range:change.band},%s)/(COUNTIFS({range:change.band},%s)+COUNTIFS({range:change.band},%s)+COUNTIFS({range:change.band},%s)),0)' % (ck('Improved'), ck('Improved'), ck('No change'), ck('Review the plan'))),
  O('Verdict', 'text', 'IF(%s=0,%s,IF(%s/%s>=0.5,%s,%s))' % (N7, ck('Review the caseload'), IMP7, N7, ck('Most clients improved'), ck('Review the caseload')))],
  GR('What if', ('Client 1 no better: 28', {'l1': 28}), ('Clients 1 to 3 worse', {'l1': 30, 'l2': 26, 'l3': 33}), ('Two clients skipped', {'i9': 0, 'i10': 0}), ('Everyone 5 points lower', {'l1': 11, 'l2': 10, 'l3': 17, 'l5': 7, 'l7': 14}))))
# 8 supervision hours owed
tools.append(TOOL('sup_owed', 'Supervision Hours Owed', 'Is the associate\'s supervision up to date',
  'Type the client sessions seen to date, the sessions per supervision hour and the hours logged; see the hours owed, the debt, the hours to book and a verdict, beside your own log.', [
  I('sess', 'Client sessions seen to date (associate)', 528), I('ratio', 'Client sessions per supervision hour', 10), I('logged', 'Supervision hours logged', 53, 'num')], [
  O('Hours owed to date', 'num', '{in:sess}/{in:ratio}'), O('Hours logged', 'num', '{in:logged}'), O('Hours ahead (+) or behind (-)', 'num', '{in:logged}-{in:sess}/{in:ratio}'),
  O('Hours debt', 'num', 'MAX(0,{in:sess}/{in:ratio}-{in:logged})'), O('Hours to book (in half hours)', 'num', 'ROUNDUP(MAX(0,{in:sess}/{in:ratio}-{in:logged})*2,0)/2'),
  O('Sessions until the next hour is owed', 'int', 'INT({in:logged}*{in:ratio}-{in:sess})'),
  O('Associate in your data: hours owed', 'num', 'SUM({range:team.hours_owed})'), O('Associate in your data: hours logged', 'num', 'SUM({range:team.hours_logged})'),
  O('Verdict', 'text', 'IF({in:sess}/{in:ratio}<={in:logged},%s,%s)' % (ck('Supervision up to date'), ck('Book hours now')))],
  GR('What if', ('600 sessions seen', {'sess': 600}), ('One session per 8 hours', {'ratio': 8}), ('Only 40 hours logged', {'logged': 40}), ('Ratio of 12', {'ratio': 12}), ('One month busier: 590', {'sess': 590}))))
# 9 supervision cost
IND9 = '({in:hrs}*{in:rate})'; GRP9 = '({in:gn}*{in:gfee}*{in:att})'
tools.append(TOOL('sup_cost', 'Supervision Cost', 'What supervision costs each month and per associate session',
  'Type the external hours for the associate, the rate, the group fee, attendees, associate sessions and a monthly budget; see the monthly cost, the cost per session and a verdict.', [
  I('hrs', 'External supervision hours for the associate a month', 2, 'num'), I('rate', 'External supervisor rate per hour', 100, 'money'), I('gfee', 'Group supervision fee per attendee', 45, 'money'), I('gn', 'Group sessions a month', 1),
  I('att', 'Attendees in the group', 6), I('sess', 'Associate sessions a month', 55), I('bud', 'Monthly supervision budget', 600, 'money')], [
  O('Individual supervision cost a month', 'money', IND9), O('Group supervision cost a month', 'money', GRP9), O('Total supervision cost a month', 'money', IND9 + '+' + GRP9),
  O('Cost per group attendee a month', 'money', '{in:gn}*{in:gfee}'), O('Cost per associate session', 'money', '(%s+{in:gn}*{in:gfee})/{in:sess}' % IND9), O('Budget left a month', 'money', '{in:bud}-%s-%s' % (IND9, GRP9)),
  O('Your log: cost a month, last 12 months', 'money', 'SUMIFS({range:suplog.cost},{range:suplog.date},">="&({today}-365))/12'),
  O('Verdict', 'text', 'IF(%s+%s<={in:bud},%s,%s)' % (IND9, GRP9, ck('Within budget'), ck('Over budget')))],
  GR('What if', ('Four external hours', {'hrs': 4}), ('Group of 10', {'att': 10}), ('Higher rate: 130', {'rate': 130}), ('Two groups a month', {'gn': 2}), ('Tight budget: 400', {'bud': 400}))))
# 10 CE pace
EXP10 = '({in:target}*(12-{in:left})/12)'
tools.append(TOOL('ce_pace', 'Continuing Education (CPD) Pace', 'Is a clinician on pace for the yearly CE hours',
  'Type the target hours, the hours done (with a certificate) and the months left; see the hours still needed, the hours a month and a verdict against an even pace.', [
  I('target', 'Target hours for the year', 20), I('done', 'Hours done so far (with a certificate)', 16, 'num'), I('left', 'Months left in the year', 1.5, 'num')], [
  O('Hours still needed', 'num', 'MAX(0,{in:target}-{in:done})'), O('Hours a month needed', 'num', 'IF({in:left}>0,MAX(0,{in:target}-{in:done})/{in:left},MAX(0,{in:target}-{in:done}))'), O('Hours expected by now at an even pace', 'num', EXP10),
  O('Hours ahead (+) or behind (-) the pace', 'num', '{in:done}-' + EXP10), O('Share of the target done', 'pct', '{in:done}/{in:target}'),
  O('Clinicians still short of the target in your data', 'int', 'COUNTIFS({range:team.hours_needed},">0")'),
  O('Verdict', 'text', 'IF({in:done}>=%s,%s,%s)' % (EXP10, ck('On pace'), ck('Behind')))],
  GR('What if', ('Done 18 hours', {'done': 18}), ('Done 20 hours', {'done': 20}), ('Three months left', {'left': 3}), ('Target of 30', {'target': 30}), ('Done 10 hours', {'done': 10}))))
# 11 CE budget
CB11 = '({in:cnt}*{in:courses}*{in:avg})'
tools.append(TOOL('ce_budget', 'Continuing Education Budget', 'What continuing education costs the practice this year',
  'Type the clinicians, courses a year, average cost, hours per course, the share the practice pays and a budget; see the yearly cost, the cost per clinician and per hour, and a verdict.', [
  I('cnt', 'Clinicians', 6), I('courses', 'Courses per clinician a year', 6), I('avg', 'Average cost per course', 125, 'money'), I('hpc', 'Average hours per course', 3.5, 'num'), I('share', 'Share of the cost the practice pays', 0.8, 'pct'),
  I('bud', 'Yearly continuing education budget', 4500, 'money')], [
  O('Total cost a year', 'money', CB11), O('Cost per clinician', 'money', '{in:courses}*{in:avg}'), O('Practice cost a year', 'money', CB11 + '*{in:share}'), O('Hours per clinician a year', 'num', '{in:courses}*{in:hpc}'),
  O('Hours above (+) or below (-) the target', 'num', '{in:courses}*{in:hpc}-{set:ce_target_hours}'), O('Cost per hour', 'money', '{in:avg}/{in:hpc}'), O('Budget left a year', 'money', '{in:bud}-' + CB11 + '*{in:share}'),
  O('Your log: cost per clinician this year', 'money', 'SUMIFS({range:celog.cost},{range:celog.date},">="&%s)/MAX(1,COUNTIFS({range:team.session_cap},">0"))' % JAN1),
  O('Verdict', 'text', 'IF(%s*{in:share}<={in:bud},%s,%s)' % (CB11, ck('Within budget'), ck('Over budget')))],
  GR('What if', ('Eight courses each', {'courses': 8}), ('Practice pays everything', {'share': 1}), ('Costlier courses: 180', {'avg': 180}), ('Tight budget: 3000', {'bud': 3000}), ('Four courses each', {'courses': 4}))))
# 12 renewal register alert
DUE12 = 'EDATE({in:last},{in:every})'
def RR(k, col): return 'IFERROR(INDEX({range:renewals.%s},MATCH(%d,{range:renewals.act_rank},0)),"")' % (col, k)
def RRT(k): return 'IFERROR(INDEX({range:renewals.holder},MATCH(%d,{range:renewals.act_rank},0))&" - "&INDEX({range:renewals.item},MATCH(%d,{range:renewals.act_rank},0)),"")' % (k, k)
o12 = [O('Renewal due date', 'date', DUE12), O('Days to due', 'int', DUE12 + '-{today}'), O('Amber alert starts', 'date', DUE12 + '-{in:amber}'), O('Red alert starts', 'date', DUE12 + '-{in:red}')]
for k in range(1, 6): o12 += [O('Soonest renewal %d' % k, 'text', RRT(k)), O('Soonest renewal %d, due' % k, 'date', RR(k, 'due_date'))]
o12 += [O('Renewals not done in your register', 'int', 'COUNTIFS({range:renewals.status},"<>"&%s,{range:renewals.renewal_id},"<>")' % ck('Renewed')),
        O('Verdict', 'text', 'IF(%s<{today},%s,IF(%s-{today}<={in:red},%s,IF(%s-{today}<={in:amber},%s,%s)))' % (DUE12, ck('Overdue'), DUE12, ck('Red'), DUE12, ck('Amber'), ck('OK')))]
tools.append(TOOL('renewal_alert', 'Renewal Register Alert', 'Which renewal is about to be missed',
  'Type when an item was last renewed and how often; see its due date, the red and amber dates and a verdict, then the five soonest renewals of your register ranked.', [
  I('last', 'Last renewed on', 'today-350', 'date'), I('every', 'Renewed every (months)', 12), I('red', 'Red alert days before due', 30), I('amber', 'Amber alert days before due', 45)], o12,
  GR('What if', ('Renewed 6 months ago', {'last': '={today}-180'}), ('Renewed last month', {'last': '={today}-30'}), ('Every 24 months', {'every': 24, 'last': '={today}-700'}), ('Amber at 60 days', {'amber': 60}), ('Already overdue', {'last': '={today}-400'}))))
# 13 renewal cost planner
def MC(k): return 'SUMIFS({range:renewals.cost},{range:renewals.status},"<>"&{list:cka.renewed},{range:renewals.paid_by},%s,{range:renewals.due_date},">="&EDATE(%s,%d),{range:renewals.due_date},"<"&EDATE(%s,%d))*(1+{in:rise})' % (tok('paidby', 'Practice'), MS, k - 1, MS, k)
o13 = [O('Practice cost, month %d' % k, 'money', MC(k)) for k in range(1, 13)]
TOT13 = 'SUMIFS({range:renewals.cost},{range:renewals.status},"<>"&{list:cka.renewed},{range:renewals.paid_by},%s,{range:renewals.due_date},">="&%s,{range:renewals.due_date},"<"&EDATE(%s,12))*(1+{in:rise})' % (tok('paidby', 'Practice'), MS, MS)
o13 += [O('Practice renewal cost, next 12 months', 'money', TOT13),
        O('Heaviest month cost', 'money', 'MAX(' + ','.join(MC(k) for k in range(1, 13)) + ')'),
        O('Monthly amount to set aside', 'money', 'ROUNDUP(%s/12,0)' % TOT13),
        O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (TOT13, ck('Set money aside'), ck('Within budget')))]
tools.append(TOOL('renewal_cost', 'Renewal Cost Planner', 'What renewals cost the practice, month by month',
  'Type the cost rise at renewal; your open renewals paid by the practice are summed by month for 12 months, with the heaviest month, the monthly amount to set aside and a verdict.', [
  I('rise', 'Cost rise at renewal', 0.05, 'pct')], o13,
  GR('What if', ('No cost rise', {'rise': 0}), ('Ten percent rise', {'rise': 0.1}), ('Twenty percent rise', {'rise': 0.2}))))
# 14 records keep-until
tools.append(TOOL('keep_until', 'Records Keep-until Date', 'When to archive a file and how long to keep it',
  'Type the discharge date, the years to keep from your own local rules and the months before archiving; see the archive date, the keep-until date and a verdict.', [
  I('dd', 'Discharge date', 'today-400', 'date'), I('yrs', 'Years to keep (check your own local rules)', 7), I('arch', 'Months after discharge before archiving', 12)], [
  O('Archive on', 'date', 'EDATE({in:dd},{in:arch})'), O('Days to the archive date', 'int', 'EDATE({in:dd},{in:arch})-{today}'), O('Keep until', 'date', 'EDATE({in:dd},12*{in:yrs})'),
  O('Years left to keep', 'num', '(EDATE({in:dd},12*{in:yrs})-{today})/365.25'), O('Files to archive now in your data', 'int', 'COUNTIFS({range:keep.status},%s)' % ck('Archive now')),
  O('Verdict', 'text', 'IF(EDATE({in:dd},{in:arch})<={today},%s,%s)' % (ck('Archive now'), ck('Keep')))],
  GR('What if', ('Discharged last month', {'dd': '={today}-30'}), ('Keep 10 years', {'yrs': 10}), ('Archive after 6 months', {'arch': 6}), ('Discharged 3 years ago', {'dd': '={today}-1100'}))))
# 15 record request deadline
DL15 = '({in:rd}+{in:allowed})'
tools.append(TOOL('request_deadline', 'Record Request Deadline', 'When must a record request be answered',
  'Type the request date, the days your own local rules allow and a send-by buffer; see the deadline, the days left and a verdict, beside the open requests in your data.', [
  I('rd', 'Request received on', 'today-12', 'date'), I('allowed', 'Days allowed (check your own local rules)', 30), I('buf', 'Days before the deadline you want to send', 5)], [
  O('Deadline', 'date', DL15), O('Days left', 'int', DL15 + '-{today}'), O('Working days left', 'int', 'MAX(0,NETWORKDAYS({today},%s))' % DL15), O('Send by', 'date', DL15 + '-{in:buf}'),
  O('Open requests in your data', 'int', 'COUNTIFS({range:requests.status},%s)+COUNTIFS({range:requests.status},%s)+COUNTIFS({range:requests.status},%s)' % (ck('Overdue'), ck('Due soon'), ck('On time'))),
  O('Verdict', 'text', 'IF(%s<{today},%s,IF(%s-{today}<=7,%s,%s))' % (DL15, ck('Overdue'), DL15, ck('Due soon'), ck('On time')))],
  GR('What if', ('Received 25 days ago', {'rd': '={today}-25'}), ('Received today', {'rd': '={today}'}), ('Fourteen days allowed', {'allowed': 14}), ('Received 40 days ago', {'rd': '={today}-40'}))))
# 16 consent review date
NR16 = 'EDATE({in:signed},{in:months})'
tools.append(TOOL('consent_review', 'Consent Review Date', 'When is a client\'s consent review due',
  'Type when consent was signed, the months between reviews from your own local rules and a reminder lead time; see the next review date and a verdict, beside the reviews due in your data.', [
  I('signed', 'Consent signed (or re-signed) on', 'today-400', 'date'), I('months', 'Months between reviews (check your own local rules)', 12), I('warn', 'Reminder days before the review', 30)], [
  O('Next review date', 'date', NR16), O('Days to the review', 'int', NR16 + '-{today}'), O('Reminder date', 'date', NR16 + '-{in:warn}'),
  O('Consent reviews due in your data', 'int', 'COUNTIFS({range:consent.review_check},%s)' % ck('Review due')), O('Reviews due in the next 30 days', 'int', 'COUNTIFS({range:consent.review_check},%s)' % ck('Due in 30 days')),
  O('Verdict', 'text', 'IF(%s<={today},%s,%s)' % (NR16, ck('Review due'), ck('Current')))],
  GR('What if', ('Signed 6 months ago', {'signed': '={today}-180'}), ('Review every 6 months', {'months': 6, 'signed': '={today}-200'}), ('Signed last week', {'signed': '={today}-7'}), ('Review every 24 months', {'months': 24}))))
# 17 outcome review coverage
tools.append(TOOL('score_coverage', 'Outcome Review Coverage', 'How many active clients have a current outcome score',
  'Type the active clients, those with a score inside the review window, the minutes a review takes and a target share; see the coverage, the reviews to book and a verdict.', [
  I('active', 'Active clients', 224), I('scored', 'Clients with a score in the last 90 days', 209), I('mins', 'Minutes per review', 20), I('weeks', 'Weeks in which to book the reviews', 4), I('target', 'Wanted coverage', 0.9, 'pct')], [
  O('Coverage', 'pct', '{in:scored}/{in:active}'), O('Gap to the target (points of share)', 'pct', '{in:scored}/{in:active}-{in:target}'), O('Clients without a current score', 'int', '{in:active}-{in:scored}'),
  O('Reviews to book to reach the target', 'int', 'MAX(0,ROUNDUP({in:target}*{in:active}-{in:scored},0))'), O('Reviews a week to clear all in the weeks given', 'int', 'ROUNDUP(({in:active}-{in:scored})/{in:weeks},0)'),
  O('Clinician hours for all those reviews', 'num', '({in:active}-{in:scored})*{in:mins}/60'),
  O('Your clients: share with a current score', 'pct', 'IFERROR(COUNTIFS({range:clients.score_check},%s)/(COUNTIFS({range:clients.score_check},%s)+COUNTIFS({range:clients.score_check},%s)),0)' % (ck('Current'), ck('Current'), ck('Book review'))),
  O('Verdict', 'text', 'IF({in:scored}/{in:active}>={in:target},%s,%s)' % (ck('Covered'), ck('Book reviews')))],
  GR('What if', ('Only 180 scored', {'scored': 180}), ('Higher target: 95%', {'target': 0.95}), ('Eight weeks to book', {'weeks': 8}), ('Longer reviews: 30 minutes', {'mins': 30}), ('250 active clients', {'active': 250}))))
# 18 discharge letter timing
CL18 = '({in:last}+{in:wait})'
tools.append(TOOL('letter_timing', 'Discharge Letter Timing', 'When to send the closing letter after the last session',
  'Type the last session date, the days you wait for a client to rebook and the days allowed to send the letter; see the closing date, the letter-by date and a verdict.', [
  I('last', 'Last session date', 'today-10', 'date'), I('wait', 'Days to wait for a rebooking before closing', 7), I('allowed', 'Days allowed to send the letter after closing', 7)], [
  O('Closing date', 'date', CL18), O('Letter-by date', 'date', CL18 + '+{in:allowed}'), O('Days since the last session', 'int', '{today}-{in:last}'), O('Days left to send the letter', 'int', CL18 + '+{in:allowed}-{today}'),
  O('Closing letters not sent in your data, last 90 days', 'int', 'COUNTIFS({range:discharges.letter_check},%s,%s)' % (ck('Not sent'), W90('discharges.date'))),
  O('Verdict', 'text', 'IF({today}>=%s,%s,%s)' % (CL18, ck('Send now'), ck('Waiting')))],
  GR('What if', ('Last session 3 days ago', {'last': '={today}-3'}), ('Wait 14 days', {'wait': 14}), ('Last session 30 days ago', {'last': '={today}-30'}), ('Letter within 3 days', {'allowed': 3}))))
assert len(tools) == 18, len(tools)
