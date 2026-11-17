"""Wedding suite part 4: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp4_lists import *
import wp4_data as D
from wp4_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v_} for l, v_ in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def DT(f): return 'IFERROR(IF(%s=0,"",%s),"")' % (f, f)
def TXT(t_, c_, kc, k): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (R(t_, c_), k, R(t_, kc))

W = '{set:wedding_day}'
MAXD = 'MAX(%s)' % R('tasks', 'due_date')
tools = []
CNT = lambda *cr: 'COUNTIFS(%s)' % ','.join(cr)
TID = '%s,"<>"' % R('tasks', 'task_id')
OPENC = '%s,"<>"&%s' % (R('tasks', 'status'), DONE)
def TC(col, crit): return '%s,%s' % (R('tasks', col), crit)

# 1 ------------------------------------------------------------ master timeline builder
IDX = 'MATCH({in:type},%s,0)' % R('wtypes', 'type')
FITCOL = 'CHOOSE(%s,%s,%s,%s,%s,%s)' % (IDX, R('fit', 'local'), R('fit', 'destination'), R('fit', 'small'), R('fit', 'multi'), R('fit', 'home'))
def APPLY(extra=''): return 'SUMPRODUCT(COUNTIFS(%s,%s,%s%s),--(%s=%s))' % (R('tasks', 'area'), R('fit', 'area'), TID, extra, FITCOL, YES)
START1 = '(%s-ROUND({in:months}*30.4,0))' % W
BEFORE1 = APPLY(',%s,"<"&%s' % (R('tasks', 'due_date'), START1))
LEAD1 = 'INDEX(%s,%s)' % (R('wtypes', 'lead_months'), IDX)
tools.append(TOOL('master_timeline', 'Master Timeline Builder', 'Is the timeline right for our wedding type',
    'Pick a wedding type and the months you have before the wedding; every task is dated from the wedding day, the tasks that do not apply to the type are counted as hidden, and the verdict says On time or how many tasks no longer fit.', [
    IL('type', 'Wedding type', 'wtype', 'Local wedding'), I('months', 'Months you have before the wedding', 6)], [
    O('Wedding day', 'date', W), O('Typical lead time of the type, months', 'int', LEAD1), O('Tasks in the plan', 'int', ALL_N), O('Tasks that apply to the type', 'int', APPLY()),
    O('Tasks hidden for the type', 'int', '%s-%s' % (ALL_N, APPLY())), O('Tasks that apply and are done', 'int', APPLY(',%s,%s' % (R('tasks', 'status'), DONE))),
    O('Tasks that apply and are open', 'int', APPLY(',%s' % OPENC)), O('First task date of the plan', 'date', DT('MIN(%s)' % R('tasks', 'due_date'))), O('Last task date of the plan', 'date', DT(MAXD)),
    O('Start of your planning window', 'date', START1), O('Applicable tasks dated before your start', 'int', BEFORE1),
    O('Verdict', 'text', 'IF({in:months}>=%s,%s,%s&" "&%s&" "&%s)' % (LEAD1, V('On time'), V('Compressed,'), BEFORE1, V('tasks no longer fit')))],
    GR('What if', ('14 months', {'months': 14}), ('12 months', {'months': 12}), ('9 months', {'months': 9}), ('6 months', {'months': 6}), ('3 months', {'months': 3}))))

# 2 ------------------------------------------------------------ compressed mode re-dater
WIN2 = 'ROUND({in:months}*30.4,0)'
SPAN2 = '(%s-MIN(%s))' % (W, R('tasks', 'due_date'))
def NOFIT(extra=''):
    return 'SUMPRODUCT(--(%s<>"")*(%s<%s),--(%s-ROUND((%s-%s)*MIN(1,%s/%s),0)<%s)%s)' % (
        R('tasks', 'task_id'), WIN2, SPAN2, WIN2, W, R('tasks', 'due_date'), WIN2, SPAN2, R('tasks', 'lead_days'), extra)
CRIT_X = ',--(%s=%s)' % (R('tasks', 'critical'), YES)
tools.append(TOOL('compress_redater', 'Compressed Mode Re-dater', 'We have less than 12 months: what still fits',
    'Type the months you really have; every task is re-dated in proportion, the ones that no longer leave their lead time are Do now (critical) or Drop or merge, and the verdict counts them.', [
    I('months', 'Months you have to plan', 6)], [
    O('Planning window, days', 'int', WIN2), O('Length of the standard plan, days', 'int', SPAN2), O('Compression of the dates', 'pct', 'MIN(1,%s/%s)' % (WIN2, SPAN2)), O('Window starts', 'date', '%s-%s' % (W, WIN2)),
    O('Tasks that fit', 'int', '%s-%s' % (ALL_N, NOFIT())), O('Tasks to do now, critical', 'int', NOFIT(CRIT_X)), O('Tasks to drop or merge', 'int', '%s-%s' % (NOFIT(), NOFIT(CRIT_X))),
    O('Tasks per week inside the window', 'num', 'ROUND(%s/MAX(1,%s/7),1)' % (ALL_N, WIN2)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s&" "&%s&" "&%s&" "&%s)' % (WIN2, SPAN2, V('On time'), V('Do'), NOFIT(CRIT_X), V('now, drop or merge'), '%s-%s' % (NOFIT(), NOFIT(CRIT_X))))],
    GR('What if', ('12 months', {'months': 12}), ('9 months', {'months': 9}), ('6 months', {'months': 6}), ('4 months', {'months': 4}), ('3 months', {'months': 3}))))

# 3 ------------------------------------------------------------ month-out progress check
DUE_SO_FAR = CNT(TC('due_date', '"<="&{today}'), TID)
DONE_SO_FAR = CNT(TC('due_date', '"<="&{today}'), TC('status', DONE), TID)
BEHIND3 = '(%s-%s)' % (DUE_SO_FAR, DONE_SO_FAR)
def BKT(w): return CNT(TC('when', tok('when', w)), TC('days_overdue', '">0"'))
tools.append(TOOL('monthout_check', 'Month-out Progress Check', 'Are we on track for each month-out bucket',
    'Type how many late tasks you accept; the tasks due so far are set against the tasks done, the late ones are counted by bucket, and the verdict says On track or Behind by.', [
    I('allow', 'Late tasks you accept', 0)], [
    O('Tasks due so far', 'int', DUE_SO_FAR), O('Of those, done', 'int', DONE_SO_FAR), O('Tasks behind, due and not done', 'int', BEHIND3), O('Done share of the tasks due so far', 'pct', 'IFERROR(%s/%s,0)' % (DONE_SO_FAR, DUE_SO_FAR)),
    O('Your target share on time', 'pct', '{set:ontime_target}'), O('Tasks done before they are due', 'int', 'SUMPRODUCT(--(%s=%s),--(%s<>""),--(%s<%s))' % (R('tasks', 'status'), DONE, R('tasks', 'done_date'), R('tasks', 'done_date'), R('tasks', 'due_date'))),
    O('Late in the 12+ months bucket', 'int', BKT('12+ months')), O('Late in the 9 months bucket', 'int', BKT('9 months')), O('Late in the 6 months bucket', 'int', BKT('6 months')),
    O('Done share of the whole plan', 'pct', 'IFERROR(%s/%s,0)' % (DONE_N, ALL_N)),
    O('Verdict', 'text', 'IF(%s<={in:allow},%s,%s&" "&(%s-{in:allow})&" "&%s)' % (BEHIND3, V('On track'), V('Behind by'), BEHIND3, V('tasks')))],
    GR('What if', ('Accept 0', {'allow': 0}), ('Accept 2', {'allow': 2}), ('Accept 5', {'allow': 5}), ('Accept 7', {'allow': 7}), ('Accept 10', {'allow': 10}))))

# 4 ------------------------------------------------------------ overdue task ranker
OVN = 'COUNTIFS(%s,">0")' % R('tasks', 'days_overdue')
def OVT(c_, k): return 'IFERROR(INDEX(%s,%d)&"","")' % (R('overdue', c_), k)
tools.append(TOOL('overdue_ranker', 'Overdue Task Ranker', 'Which overdue task do we do first',
    'Type the hours one overdue task takes; the overdue tasks are ranked with the critical ones first and then the longest overdue, the hours to clear them are set against the hours you can give, and the verdict names the first.', [
    I('hours_each', 'Hours one overdue task takes', 1.5, 'num')], [
    O('Tasks overdue', 'int', OVN), O('Critical tasks overdue', 'int', CNT(TC('days_overdue', '">0"'), TC('critical', YES))), O('Oldest overdue, days', 'int', 'MAX(%s)' % R('tasks', 'days_overdue')),
    O('Do first', 'text', OVT('task', 1)), O('Its owner', 'text', OVT('owner', 1)), O('Its days overdue', 'int', 'IFERROR(INDEX(%s,1),0)' % R('overdue', 'days_overdue')),
    O('Do second', 'text', OVT('task', 2)), O('Do third', 'text', OVT('task', 3)), O('Hours to clear all overdue tasks', 'num', '%s*{in:hours_each}' % OVN),
    O('Weeks of the time you can give', 'num', 'ROUND(%s*{in:hours_each}/MAX(1,{set:week_hours}),1)' % OVN),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (OVN, V('Nothing overdue'), V('Do first:'), OVT('task', 1)))],
    GR('What if', ('1 hour each', {'hours_each': 1}), ('1.5 hours each', {'hours_each': 1.5}), ('2 hours each', {'hours_each': 2}), ('3 hours each', {'hours_each': 3}), ('4 hours each', {'hours_each': 4}))))

# 5 ------------------------------------------------------------ critical path slack
SL = R('critical', 'slack')
MINSL = 'IF(COUNT(%s)=0,"",MIN(%s))' % (SL, SL)
def CRT(c_, k): return 'IFERROR(INDEX(%s,%d)&"","")' % (R('critical', c_), k)
tools.append(TOOL('critical_slack', 'Critical Path Slack', 'How much slack is left on the critical path',
    'Type the days of slack you want between critical tasks; the next critical tasks are listed with the days between each and the next, and the verdict says the slack or No slack.', [
    I('buffer', 'Days of slack you want', 7)], [
    O('Open critical tasks', 'int', 'COUNTIFS(%s,">0")' % R('tasks', 'crit_seq')), O('Next critical task', 'text', CRT('task', 1)), O('Its due date', 'date', 'IFERROR(IF(INDEX(%s,1)=0,"",INDEX(%s,1)),"")' % (R('critical', 'due_date'), R('critical', 'due_date'))),
    O('Its days left, minus when late', 'int', 'IFERROR(INDEX(%s,1),"")' % R('critical', 'days_left')), O('Slack after it, days', 'int', 'IFERROR(INDEX(%s,1),"")' % SL),
    O('Then', 'text', CRT('task', 2)), O('Slack after the second, days', 'int', 'IFERROR(INDEX(%s,2),"")' % SL), O('Smallest slack, days', 'int', MINSL),
    O('Critical tasks with less slack than you want', 'int', 'COUNTIFS(%s,"<"&{in:buffer})' % SL),
    O('Critical tasks overdue', 'int', CNT(TC('days_overdue', '">0"'), TC('critical', YES))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(OR(IFERROR(INDEX(%s,1),0)<0,%s<=0),%s,%s&" "&%s&" "&%s))' % ('COUNTIFS(%s,">0")' % R('tasks', 'crit_seq'), V('No open critical tasks'), R('critical', 'days_left'), MINSL, V('No slack'), V('Slack'), MINSL, V('days')))],
    GR('What if', ('Want 3 days', {'buffer': 3}), ('Want 7 days', {'buffer': 7}), ('Want 14 days', {'buffer': 14}), ('Want 21 days', {'buffer': 21}), ('Want 30 days', {'buffer': 30}))))

# 6 ------------------------------------------------------------ invitation print slip
ARRIVE = '({set:rsvp_deadline}-{in:window})'
POSTBY = '(%s-{in:post_days})' % ARRIVE
SEND = '(%s-{in:print_days})' % POSTBY
LEADARR = '(%s-7*{set:invite_lead_weeks})' % W
tools.append(TOOL('print_slip', 'Invitation Print Slip', 'When must the invitation files reach the printer',
    'Type the days the printer needs, the days to post and the days guests need to reply; counting back from the reply-by date gives the latest date the files can reach the printer, and the verdict says Send within or how many days late.', [
    I('print_days', 'Days the printer needs', 8), I('post_days', 'Days to post and deliver', 5), I('window', 'Days guests need to reply', 14)], [
    O('Reply-by date', 'date', '{set:rsvp_deadline}'), O('Invitations must arrive by', 'date', ARRIVE), O('Posting must start by', 'date', POSTBY), O('Send the files to the printer by', 'date', SEND),
    O('Days from today to that date, minus when late', 'int', '%s-{today}' % SEND), O('Wedding day less your invitation lead weeks', 'date', LEADARR), O('Send by under the lead weeks rule', 'date', '%s-{in:post_days}-{in:print_days}' % LEADARR),
    O('Days to the lead weeks date, minus when late', 'int', '%s-{in:post_days}-{in:print_days}-{today}' % LEADARR), O('Weeks from the reply-by date to the wedding', 'num', 'ROUND((%s-{set:rsvp_deadline})/7,1)' % W),
    O('Verdict', 'text', 'IF(%s-{today}>=0,%s&" "&(%s-{today})&" "&%s,({today}-%s)&" "&%s)' % (SEND, V('Send within'), SEND, V('days'), SEND, V('days late')))],
    GR('What if', ('Printer needs 5 days', {'print_days': 5}), ('Printer needs 8 days', {'print_days': 8}), ('Printer needs 10 days', {'print_days': 10}), ('Printer needs 14 days', {'print_days': 14}), ('Printer needs 21 days', {'print_days': 21}))))

# 7 ------------------------------------------------------------ owner workload balance
WS_ = R('workload', 'share'); WO = R('workload', 'owner'); WOP = R('workload', 'open')
HOLD = 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (WO, WS_, WS_)
tools.append(TOOL('owner_balance', 'Owner Workload Balance', 'Is the work shared fairly',
    'Type the most open tasks one owner should hold as a share; the open tasks of each owner are set against it, and the verdict names the owner who holds too much.', [
    I('max_pct', 'Most one owner should hold', 0.4, 'pct')], [
    O('Open tasks', 'int', OPEN_N), O('Heaviest owner', 'text', HOLD + '&""'), O('Its open tasks', 'int', 'MAX(%s)' % WOP), O('Its share of the open tasks', 'pct', 'MAX(%s)' % WS_),
    O('Lightest owner', 'text', 'INDEX(%s,MATCH(MIN(%s),%s,0))&""' % (WO, WS_, WS_)), O('Its share of the open tasks', 'pct', 'MIN(%s)' % WS_),
    O('Owners over your share', 'int', 'COUNTIFS(%s,">"&{in:max_pct})' % WS_), O('Tasks to hand over to reach your share', 'int', 'MAX(0,ROUNDUP(MAX(%s)-{in:max_pct}*%s,0))' % (WOP, OPEN_N)),
    O('Open tasks of the partners together', 'int', '%s+%s+%s' % tuple('COUNTIFS(%s,%s,%s)' % (R('tasks', 'owner'), OWN[o], OPENC) for o in ('Partner 1', 'Partner 2', 'Both partners'))),
    O('Verdict', 'text', 'IF(MAX(%s)>{in:max_pct},%s&" "&%s&" "&%s&" "&ROUND(MAX(%s)*100,0)&" "&%s,%s)' % (WS_, V('Share looks uneven:'), HOLD, V('holds'), WS_, V('percent'), V('Balanced')))],
    GR('What if', ('Limit 25%', {'max_pct': 0.25}), ('Limit 40%', {'max_pct': 0.4}), ('Limit 50%', {'max_pct': 0.5}), ('Limit 60%', {'max_pct': 0.6}), ('Limit 70%', {'max_pct': 0.7}))))

# 8 ------------------------------------------------------------ delegation suggester
MV = 'MATCH(1,%s,0)' % R('tasks', 'move_seq')
HOPEN = 'MAX(%s)' % WOP
MVAREA = 'IFERROR(INDEX(%s,%s)&"","")' % (R('tasks', 'area'), MV)
MVOWNER = 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (R('areasum', 'helper'), MVAREA, R('areasum', 'area'))
MVTASK = 'IFERROR(INDEX(%s,%s)&"","")' % (R('tasks', 'title'), MV)
tools.append(TOOL('delegation', 'Delegation Suggester', 'Which task should we hand over, and to whom',
    'Type how many tasks you will hand over; the owner with the most open tasks gives up the first task that is not started and not critical, to the usual helper of that area, and the verdict says Move task to owner.', [
    I('move', 'Tasks you will hand over', 5)], [
    O('Heaviest owner', 'text', HOLD + '&""'), O('Its open tasks', 'int', HOPEN), O('Tasks to hand over to reach your set share', 'int', 'MAX(0,ROUNDUP(%s-{set:owner_share_max}*%s,0))' % (HOPEN, OPEN_N)),
    O('Tasks it can hand over, not started and not critical', 'int', 'COUNTIFS(%s,">0")' % R('tasks', 'move_seq')), O('First task to move', 'text', MVTASK), O('Its area', 'text', MVAREA),
    O('Its due date', 'date', 'IFERROR(INDEX(%s,%s),"")' % (R('tasks', 'due_date'), MV)), O('Usual helper for the area', 'text', MVOWNER),
    O('Share of the heaviest owner after your move', 'pct', 'IFERROR((%s-{in:move})/%s,0)' % (HOPEN, OPEN_N)), O('Lightest owner', 'text', 'INDEX(%s,MATCH(MIN(%s),%s,0))&""' % (WO, WS_, WS_)),
    O('Verdict', 'text', 'IF(OR(MAX(%s)<={set:owner_share_max},%s=""),%s,%s&" "&%s&" "&%s&" "&%s)' % (WS_, MVTASK, V('Balanced'), V('Move'), MVTASK, V('to'), MVOWNER))],
    GR('What if', ('Hand over 0', {'move': 0}), ('Hand over 3', {'move': 3}), ('Hand over 5', {'move': 5}), ('Hand over 9', {'move': 9}), ('Hand over 12', {'move': 12}))))

# 9 ------------------------------------------------------------ owner nudge list
NO_ = R('nudge', 'n_owner')
NMAX = 'MATCH(MAX(%s),%s,0)' % (NO_, NO_)
NUDGEN = 'SUMPRODUCT(--(LEN(%s)>0))' % R('nudge', 'task_id')
tools.append(TOOL('nudge_list', 'Nudge Owners Today', 'Who do we nudge today',
    'Type how many days ahead to look; the overdue tasks and the tasks due soon are counted, the owner with the most is named with a phone number, and the verdict says Nudge owner about n tasks.', [
    I('days', 'Days ahead to look', 7)], [
    O('Tasks overdue', 'int', OVN), O('Tasks due within your days', 'int', CNT(OPENC, TC('due_date', '">="&{today}'), TC('due_date', '"<="&{today}+{in:days}'), TID)),
    O('Tasks on the nudge list, overdue and the next seven days', 'int', NUDGEN), O('Owners on the list', 'int', 'IFERROR(SUMPRODUCT(--(LEN(%s)>0),1/COUNTIFS(%s,%s&"")),0)' % (R('nudge', 'task_id'), R('nudge', 'owner'), R('nudge', 'owner'))),
    O('Owner with the most', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (R('nudge', 'owner'), NMAX)), O('Its tasks on the list', 'int', 'IF(%s=0,0,MAX(%s))' % (NUDGEN, NO_)), O('Its phone', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (R('nudge', 'phone'), NMAX)),
    O('Its first task', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (R('nudge', 'task'), NMAX)), O('Critical tasks on the list', 'int', CNT(TC('week_seq', '">0"'), TC('critical', YES))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&IFERROR(INDEX(%s,%s),"")&" "&%s&" "&MAX(%s)&" "&%s)' % (NUDGEN, V('Nobody to nudge'), V('Nudge'), R('nudge', 'owner'), NMAX, V('about'), NO_, V('tasks')))],
    GR('What if', ('Look 3 days ahead', {'days': 3}), ('7 days', {'days': 7}), ('14 days', {'days': 14}), ('21 days', {'days': 21}), ('30 days', {'days': 30}))))

# 10 ----------------------------------------------------------- weekly plan
def HOURS(extra, owners=None):
    base = lambda o: 'COUNTIFS(%s,%s,%s,%s,%s%s)' % (R('tasks', 'area'), R('fit', 'area'), OPENC, TID, TC('due_date', '"<="&{today}+7'), o)
    if owners is None: return 'SUMPRODUCT(%s,%s)' % (base(''), R('fit', 'hours'))
    return 'SUMPRODUCT(%s,%s)' % ('+'.join(base(',%s,%s' % (R('tasks', 'owner'), OWN[o])) for o in owners), R('fit', 'hours'))
CP = ('Partner 1', 'Partner 2', 'Both partners')
WEEKN = 'COUNTIFS(%s,">0")' % R('tasks', 'week_seq')
tools.append(TOOL('weekly_plan', 'Weekly Plan', 'Can we do this week\'s tasks',
    'Type the hours you can give this week; the overdue tasks and the tasks due in seven days are turned into hours at the typical hours per task, the share that falls on the couple is set against your hours, and the verdict says Doable or Over by.', [
    I('give', 'Hours the couple can give this week', 8)], [
    O('Tasks this week, with overdue', 'int', WEEKN), O('Of those, overdue', 'int', OVN), O('Hours of all of them', 'num', HOURS('')), O('Hours that fall on the couple', 'num', HOURS('', CP)),
    O('Hours that fall on others', 'num', '%s-%s' % (HOURS(''), HOURS('', CP))), O('Hours you can give', 'num', '{in:give}'), O('Hours over or under, couple', 'num', '%s-{in:give}' % HOURS('', CP)),
    O('Payments due this week, with overdue', 'int', 'COUNTIFS(%s,"<>"&%s,%s,"<="&{today}+7,%s,"<>")' % (R('schedule', 'status'), PAID, R('schedule', 'due_date'), R('schedule', 'pay_id'))),
    O('Next week the couple\'s hours', 'num', 'IFERROR(INDEX(%s,2),0)' % R('weeks', 'hours')),
    O('Verdict', 'text', 'IF(%s<={in:give},%s,%s&" "&ROUND(%s-{in:give},1)&" "&%s)' % (HOURS('', CP), V('Doable'), V('Over by'), HOURS('', CP), V('hours')))],
    GR('What if', ('4 hours', {'give': 4}), ('8 hours', {'give': 8}), ('12 hours', {'give': 12}), ('16 hours', {'give': 16}), ('24 hours', {'give': 24}))))

# 11 ----------------------------------------------------------- capacity check
def OPENH(owners):
    parts = '+'.join('COUNTIFS(%s,%s,%s,%s,%s,%s)' % (R('tasks', 'area'), R('fit', 'area'), OPENC, TID, R('tasks', 'owner'), OWN[o]) for o in owners)
    return 'SUMPRODUCT(%s,%s)' % (parts, R('fit', 'hours'))
WEEKSLEFT = 'MAX(1,(%s-{today})/7)' % W
NEED = '(%s/%s)' % (OPENH(CP), WEEKSLEFT)
tools.append(TOOL('capacity', 'Capacity Check', 'Do we have the hours to finish the plan',
    'Type the hours a week the couple can give; the open tasks the couple owns are turned into hours at the typical hours per task and spread over the weeks left, and the verdict says Doable or Short by hours a week.', [
    I('hours_week', 'Hours a week the couple can give', 8)], [
    O('Open tasks owned by the couple', 'int', '+'.join('COUNTIFS(%s,%s,%s)' % (R('tasks', 'owner'), OWN[o], OPENC) for o in CP)), O('Hours they need', 'num', OPENH(CP)), O('Weeks to the wedding', 'num', 'ROUND(%s,1)' % WEEKSLEFT),
    O('Hours needed a week', 'num', 'ROUND(%s,1)' % NEED), O('Hours a week you can give', 'num', '{in:hours_week}'), O('Hours of all open tasks, all owners', 'num', 'SUMPRODUCT(COUNTIFS(%s,%s,%s,%s),%s)' % (R('tasks', 'area'), R('fit', 'area'), OPENC, TID, R('fit', 'hours'))),
    O('Hours left to others', 'num', 'SUMPRODUCT(COUNTIFS(%s,%s,%s,%s),%s)-%s' % (R('tasks', 'area'), R('fit', 'area'), OPENC, TID, R('fit', 'hours'), OPENH(CP))),
    O('Weeks you need at your hours', 'num', 'ROUND(%s/MAX(1,{in:hours_week}),1)' % OPENH(CP)),
    O('Verdict', 'text', 'IF(%s<={in:hours_week},%s,%s&" "&ROUND(%s-{in:hours_week},1)&" "&%s&" "&%s)' % (NEED, V('Doable'), V('Short by'), NEED, V('hours'), V('a week')))],
    GR('What if', ('4 hours', {'hours_week': 4}), ('6 hours', {'hours_week': 6}), ('8 hours', {'hours_week': 8}), ('10 hours', {'hours_week': 10}), ('12 hours', {'hours_week': 12}))))

# 12 ----------------------------------------------------------- deadline countdown
K0 = '(COUNTIF(%s,"<0")+1)' % R('deadlines', 'days_left')
def DLI(c_, off=0): return 'IFERROR(INDEX(%s,%s+%d),"")' % (R('deadlines', c_), K0, off)
NXD = 'IFERROR(INDEX(%s,%s),"")' % (R('deadlines', 'days_left'), K0)
tools.append(TOOL('countdown', 'Deadline Countdown', 'What is the next date we cannot miss',
    'Type how many days count as red and amber; the next dates from payments, the reply-by date, the headcount date, the room cut-off, vendor cut-offs and fittings are shown, and the verdict says Next item in n days.', [
    I('red', 'Red when this many days away or fewer', 7), I('amber', 'Amber when this many days away or fewer', 21)], [
    O('Next deadline', 'text', DLI('item')), O('Its date', 'date', DLI('date')), O('Days to it', 'int', NXD),
    O('Its colour', 'text', 'IF(%s="","",IF(%s<={in:red},%s,IF(%s<={in:amber},%s,%s)))' % (NXD, NXD, V('Red'), NXD, V('Amber'), V('Green'))),
    O('Then', 'text', DLI('item', 1)), O('Then, third', 'text', DLI('item', 2)), O('Dates already overdue', 'int', 'COUNTIF(%s,"<0")' % R('deadlines', 'days_left')),
    O('Red in the next ten', 'int', 'COUNTIFS(%s,"<=10",%s,"<="&{in:red})' % (R('deadlines', 'seqno'), R('deadlines', 'days_left'))),
    O('Amber in the next ten', 'int', 'COUNTIFS(%s,"<=10",%s,">"&{in:red},%s,"<="&{in:amber})' % (R('deadlines', 'seqno'), R('deadlines', 'days_left'), R('deadlines', 'days_left'))),
    O('Green in the next ten', 'int', 'COUNTIFS(%s,"<=10",%s,">"&{in:amber})' % (R('deadlines', 'seqno'), R('deadlines', 'days_left'))),
    O('Verdict', 'text', 'IF(%s="","",%s&" "&%s&" "&%s&" "&%s&" "&%s)' % (DLI('item'), V('Next:'), DLI('item'), V('in'), NXD, V('days')))],
    GR('What if', ('Red 3, amber 14', {'red': 3, 'amber': 14}), ('Red 7, amber 21', {'red': 7, 'amber': 21}), ('Red 14, amber 30', {'red': 14, 'amber': 30}), ('Red 21, amber 45', {'red': 21, 'amber': 45}), ('Red 30, amber 60', {'red': 30, 'amber': 60}))))

# 13 ----------------------------------------------------------- cash deadline overlay
WP_ = R('weeks', 'payments_due')
HW = 'MATCH(MAX(%s),%s,0)' % (WP_, WP_)
PAYIN = 'SUMIFS(%s,%s,"<>"&%s,%s,"<="&{today}+{in:days})' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'))
tools.append(TOOL('cash_overlay', 'Cash Deadline Overlay', 'Which week has the most money and tasks due',
    'Type the days to look at and the payment total you call heavy; the payments due in those days sit beside the tasks due in the same days, the busiest payment week of the next twelve is named, and the verdict says Heavy week.', [
    I('days', 'Days to look at', 30), I('heavy', 'Payments in one week you call heavy', 1000, 'money')], [
    O('Payments due, with overdue', 'money', PAYIN), O('Payment rows due, with overdue', 'int', 'COUNTIFS(%s,"<>"&%s,%s,"<="&{today}+{in:days},%s,"<>")' % (R('schedule', 'status'), PAID, R('schedule', 'due_date'), R('schedule', 'pay_id'))),
    O('Of which overdue now', 'money', 'SUMIFS(%s,%s,"<>"&%s,%s,"<"&{today})' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'))),
    O('Open tasks due in the same days, with overdue', 'int', CNT(OPENC, TC('due_date', '"<="&{today}+{in:days}'), TID)),
    O('Busiest payment week starts', 'date', 'IF(MAX(%s)=0,"",IFERROR(INDEX(%s,%s),""))' % (WP_, R('weeks', 'week_start'), HW)), O('Payments due that week', 'money', 'MAX(%s)' % WP_),
    O('Tasks due that week', 'int', 'IF(MAX(%s)=0,0,IFERROR(INDEX(%s,%s),0))' % (WP_, R('weeks', 'tasks_due'), HW)), O('Hours of the open tasks that week', 'num', 'IF(MAX(%s)=0,0,IFERROR(INDEX(%s,%s),0))' % (WP_, R('weeks', 'hours'), HW)),
    O('Weeks of the next twelve that are heavy for payments', 'int', 'COUNTIFS(%s,">="&{in:heavy})' % WP_),
    O('Verdict', 'text', 'IF(MAX(%s)>={in:heavy},%s&" "&ROUND(MAX(%s),0),%s)' % (WP_, V('Heavy week'), WP_, V('Light weeks')))],
    GR('What if', ('Look 14 days', {'days': 14}), ('30 days', {'days': 30}), ('45 days', {'days': 45}), ('60 days', {'days': 60}), ('90 days', {'days': 90}))))

# 14 ----------------------------------------------------------- date change impact
AFTER14 = CNT(OPENC, TID, TC('due_date', '"<"&{today}+{in:days}'))
tools.append(TOOL('date_change', 'Date Change Impact', 'What happens if the wedding date moves',
    'Type how many days earlier the wedding would move (use a minus for later); the dates tied to the wedding day shift, the open tasks that fall before today are counted, and the verdict says how many tasks are overdue after the move.', [
    I('days', 'Days the wedding moves earlier, minus for later', 30)], [
    O('New wedding day', 'date', '%s-{in:days}' % W), O('New final headcount date', 'date', '{set:headcount_date}-{in:days}'), O('New reply-by date', 'date', '{set:rsvp_deadline}-{in:days}'), O('New room cut-off date', 'date', '{set:room_cutoff}-{in:days}'),
    O('Months to the new wedding day', 'num', 'ROUND((%s-{in:days}-{today})/30.4,1)' % W), O('Tasks overdue today', 'int', OVN), O('Tasks overdue after the move', 'int', AFTER14),
    O('Tasks that become overdue', 'int', '%s-%s' % (AFTER14, OVN)), O('Critical tasks that become overdue', 'int', CNT(OPENC, TC('critical', YES), TC('due_date', '">="&{today}'), TC('due_date', '"<"&{today}+{in:days}'))),
    O('Payments due after the new wedding day', 'money', 'SUMIFS(%s,%s,"<>"&%s,%s,">"&(%s-{in:days}))' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'), W)),
    O('Verdict', 'text', '%s&" "&%s' % (AFTER14, V('tasks overdue after the move')))],
    GR('What if', ('No move', {'days': 0}), ('14 days earlier', {'days': 14}), ('30 days earlier', {'days': 30}), ('60 days earlier', {'days': 60}), ('30 days later', {'days': -30}))))

# 15 ----------------------------------------------------------- lead-time check
LG = R('tasks', 'lead_gap')
LATE = 'COUNTIFS(%s,">"&(0-{in:extra}))' % LG
LGM = 'MATCH(MAX(%s),%s,0)' % (LG, LG)
tools.append(TOOL('lead_time', 'Lead-time Check', 'Which task did we start too late',
    'Type extra days of safety margin; each open task is checked against the typical lead time of its area (typical, edit on Task Fit), and the verdict names the task that is furthest behind.', [
    I('extra', 'Extra days of safety margin', 0)], [
    O('Open tasks checked', 'int', 'COUNTIFS(%s,">-100000")' % LG), O('Tasks that start late', 'int', LATE), O('Critical tasks that start late', 'int', 'COUNTIFS(%s,">"&(0-{in:extra}),%s,%s)' % (LG, R('tasks', 'critical'), YES)),
    O('Furthest behind', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (R('tasks', 'title'), LGM)), O('Its area', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (R('tasks', 'area'), LGM)),
    O('Its due date', 'date', 'IFERROR(INDEX(%s,%s),"")' % (R('tasks', 'due_date'), LGM)), O('Days short of its lead time', 'int', 'IF(COUNT(%s)=0,0,MAX(%s)+{in:extra})' % (LG, LG)),
    O('Its owner', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (R('tasks', 'owner'), LGM)), O('Share of open tasks that start late', 'pct', 'IFERROR(%s/COUNTIFS(%s,">-100000"),0)' % (LATE, LG)),
    O('Verdict', 'text', 'IF(OR(COUNT(%s)=0,MAX(%s)+{in:extra}<=0),%s,%s&" "&IFERROR(INDEX(%s,%s),""))' % (LG, LG, V('Nothing starts late'), V('Late start:'), R('tasks', 'title'), LGM))],
    GR('What if', ('No margin', {'extra': 0}), ('7 days margin', {'extra': 7}), ('14 days margin', {'extra': 14}), ('21 days margin', {'extra': 21}), ('Minus 14 days', {'extra': -14}))))

# 16 ----------------------------------------------------------- wedding type filter
KEEP = 'IF({in:include_done}=1,%s,%s)' % (APPLY(), APPLY(',%s' % OPENC))
TOTAL16 = 'IF({in:include_done}=1,%s,%s)' % (ALL_N, OPEN_N)
HRS16 = 'SUMPRODUCT(COUNTIFS(%s,%s,%s,%s),%s,--(%s=%s))' % (R('tasks', 'area'), R('fit', 'area'), OPENC, TID, R('fit', 'hours'), FITCOL, YES)
tools.append(TOOL('type_filter', 'Wedding Type Filter', 'Which tasks apply to a smaller or different wedding',
    'Pick a wedding type and say whether to count done tasks (1) or only open ones (0); the Task Fit sheet decides which areas apply, and the verdict says Keep n tasks, hide n.', [
    IL('type', 'Wedding type', 'wtype', 'Small plus a party'), I('include_done', 'Count done tasks too, 1 or 0', 1)], [
    O('Typical lead time of the type, months', 'int', LEAD1), O('Tasks that apply', 'int', KEEP), O('Tasks hidden', 'int', '%s-%s' % (TOTAL16, KEEP)), O('Task areas hidden', 'int', 'SUMPRODUCT(--(%s<>""),--(%s<>%s))' % (R('fit', 'area'), FITCOL, YES)),
    O('Hours of the open tasks that apply', 'num', HRS16), O('Hours of the open tasks hidden', 'num', 'SUMPRODUCT(COUNTIFS(%s,%s,%s,%s),%s)-%s' % (R('tasks', 'area'), R('fit', 'area'), OPENC, TID, R('fit', 'hours'), HRS16)),
    O('Open tasks that apply', 'int', APPLY(',%s' % OPENC)), O('Open tasks hidden', 'int', '%s-%s' % (OPEN_N, APPLY(',%s' % OPENC))),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&" "&(%s-%s)' % (V('Keep'), KEEP, V('tasks, hide'), TOTAL16, KEEP))],
    GR('What if', ('Count done tasks', {'include_done': 1}), ('Open tasks only', {'include_done': 0}))))

# 17 ----------------------------------------------------------- done pace forecast
FIN = '({today}+ROUND(%s/MAX(0.1,{in:pace})*7,0))' % OPEN_N
DONEBACK = CNT(TC('done_date', '">="&{today}-7*{in:weeks_back}'), TC('done_date', '"<="&{today}'), TID)
tools.append(TOOL('pace_forecast', 'Done Pace Forecast', 'When will we finish the checklist',
    'Type the tasks you will finish a week and the weeks to measure your recent pace over; the open tasks are divided by your pace to give a finish date, and the verdict says how many days before or after the wedding that is.', [
    I('pace', 'Tasks you will finish a week', 4, 'num'), I('weeks_back', 'Weeks to measure your recent pace', 8)], [
    O('Open tasks', 'int', OPEN_N), O('Tasks done in the weeks you measure', 'int', DONEBACK), O('Your recent pace, tasks a week', 'num', 'ROUND(%s/MAX(1,{in:weeks_back}),1)' % DONEBACK),
    O('Weeks to the wedding', 'num', 'ROUND(MAX(0,%s-{today})/7,1)' % W), O('Pace you need to finish a week before', 'num', 'ROUND(%s/MAX(1,(%s-{today}-7)/7),1)' % (OPEN_N, W)),
    O('Weeks to finish at your pace', 'num', 'ROUND(%s/MAX(0.1,{in:pace}),1)' % OPEN_N), O('Finish date at your pace', 'date', FIN), O('Days between the finish and the wedding', 'int', '%s-%s' % (W, FIN)),
    O('Tasks left on the wedding day at your pace', 'int', 'MAX(0,ROUND(%s-{in:pace}*MAX(0,%s-{today})/7,0))' % (OPEN_N, W)),
    O('Verdict', 'text', 'IF(%s<=%s,%s&" "&(%s-%s)&" "&%s,%s&" "&(%s-%s)&" "&%s)' % (FIN, W, V('Finish'), W, FIN, V('days before the wedding'), V('Behind pace:'), FIN, W, V('days after the wedding')))],
    GR('What if', ('2 a week', {'pace': 2}), ('3 a week', {'pace': 3}), ('4 a week', {'pace': 4}), ('5 a week', {'pace': 5}), ('6 a week', {'pace': 6}))))

# 18 ----------------------------------------------------------- task health score
COMPLETE = 'SUMPRODUCT((%s<>"")*(%s<>"")*(%s<>"")*(%s<>"")*(1-(%s=%s)*(%s="")))' % (R('tasks', 'task_id'), R('tasks', 'owner'), R('tasks', 'due_date'), R('tasks', 'status'), R('tasks', 'status'), DONE, R('tasks', 'done_date'))
tools.append(TOOL('task_health', 'Task Health Score', 'Is the task list complete enough to trust',
    'Type the share of complete rows you want; every task needs an owner, a due date and a status, and a done task needs a done date, and the verdict says Healthy or Fix n rows.', [
    I('target', 'Share of complete rows you want', 0.95, 'pct')], [
    O('Tasks in the list', 'int', ALL_N), O('Tasks with an owner, a due date and a status', 'int', COMPLETE), O('Rows to fix', 'int', '%s-%s' % (ALL_N, COMPLETE)),
    O('Tasks without an owner', 'int', 'COUNTIFS(%s,"",%s)' % (R('tasks', 'owner'), TID)), O('Tasks without a due date', 'int', 'COUNTIFS(%s,"",%s)' % (R('tasks', 'due_date'), TID)),
    O('Done tasks without a done date', 'int', 'COUNTIFS(%s,%s,%s,"",%s)' % (R('tasks', 'status'), DONE, R('tasks', 'done_date'), TID)), O('Tasks with no vendor named', 'int', 'COUNTIFS(%s,"",%s)' % (R('tasks', 'vendor'), TID)),
    O('Critical tasks in the list', 'int', CNT(TC('critical', YES), TID)), O('Complete share', 'pct', 'IFERROR(%s/%s,0)' % (COMPLETE, ALL_N)),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>={in:target},%s,%s&" "&(%s-%s)&" "&%s)' % (COMPLETE, ALL_N, V('Healthy'), V('Fix'), ALL_N, COMPLETE, V('rows')))],
    GR('What if', ('Want 50%', {'target': 0.5}), ('Want 80%', {'target': 0.8}), ('Want 90%', {'target': 0.9}), ('Want 95%', {'target': 0.95}), ('Want 100%', {'target': 1}))))
assert len(tools) == 18, len(tools)
