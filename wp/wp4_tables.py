"""Wedding suite part 4: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp4_lists import *
import wp4_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IF({col:%s}="","",IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0))' % (my, src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
def CPL(): return CA('couple', 'Couple', 'text', '{set:couple}', 20)
def SC(key_, label, cond, phone): return CA(key_, label, 'text', 'IF(%s,%s,"")' % (cond, phone if phone.startswith('{') else '"%s"' % phone), 18)


DONE = tok('tstatus', 'Done'); NOTST = tok('tstatus', 'Not started')
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
OWN = {n: tok('owner', n) for n in OWNERS}
ROLE = lambda n: tok('role', n)
PAID = tok('paystatus', 'Paid'); FINALHC = tok('ckind', 'Final headcount date'); READY = tok('attire', 'Ready')
VN = lambda n: tok('vname', n)
V = lambda label: v(label)
TASK_PH = {t['team_id']: t['phone'] for t in team}
P1_PH, P2_PH, PAR1_PH, PAR2_PH = TASK_PH['WP-01'], TASK_PH['WP-02'], TASK_PH['WP-03'], TASK_PH['WP-04']
FRIEND_PH, COORD_PH = TASK_PH['WP-09'], TASK_PH['WP-10']

TODAYP7 = '{today}+7'
OPEN_N = 'COUNTIFS(%s,"<>"&%s,%s,"<>")' % (R('tasks', 'status'), DONE, R('tasks', 'task_id'))
ALL_N = 'COUNTIFS(%s,"<>")' % R('tasks', 'task_id')
DONE_N = 'COUNTIFS(%s,%s,%s,"<>")' % (R('tasks', 'status'), DONE, R('tasks', 'task_id'))
SENDBY = '({set:rsvp_deadline}-{set:reply_window}-{set:post_days}-{set:print_days})'

settings = [
    S('couple', 'Your names as the couple', 'text', COUPLE),
    S('wedding_day', 'Wedding day', 'date', iso(WEDDING_DAY)),
    S('wedding_type', 'Wedding type', 'list', key('wtype', 'Local wedding'), list='wtype'),
    S('plan_months', 'Months you have to plan, for the compressed plan', 'int', 6),
    S('rsvp_deadline', 'Reply-by date', 'date', iso(RSVP_DEADLINE)),
    S('headcount_date', 'Final headcount date, from your contract', 'date', iso(HEADCOUNT_DATE)),
    S('room_cutoff', 'Room block cut-off date', 'date', iso(ROOM_CUTOFF)),
    S('owner_share_max', 'Most open tasks one owner should hold, your own rule', 'pct', 0.40),
    S('red_days', 'Red when a date is this many days away or fewer', 'int', 7),
    S('amber_days', 'Amber when a date is this many days away or fewer', 'int', 21),
    S('week_hours', 'Hours a week you can give to the plan, your own number', 'int', 8),
    S('print_days', 'Days the printer needs, ask your printer', 'int', 8),
    S('post_days', 'Days to post and deliver the invitations, ask', 'int', 5),
    S('reply_window', 'Days to reply after the invitation arrives, typical, edit', 'int', 14),
    S('invite_lead_weeks', 'Weeks before the wedding invitations arrive, typical, edit', 'int', INVITE_LEAD_WEEKS),
    S('suites', 'Invitation suites you order, one per household', 'int', 82),
    S('move_days', 'Days earlier the date moves in the date change check', 'int', 30),
    S('thankyou_target_days', 'Days after the wedding for thank-you notes, your own target', 'int', THANKYOU_TARGET_DAYS),
    S('ontime_target', 'Share of tasks on time you aim for, your own number', 'pct', 0.85),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 team ---------------------------------------------------------------------
tables.append(T('team', 'Team', 'Team', 'The 16 people who own tasks or take your calls: partners, parents, siblings, wedding party leads, a close friend, the day-of coordinator, vendor contacts and the officiant. Their open tasks and next task fill in from the Tasks sheet.', [
    C('team_id', 'Team ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 22), LST('team', 'Team', 'team', 18), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    CA('count', 'Open tasks', 'int', 'COUNTIFS(%s,{col:team_id},%s,"<>"&%s,%s,"<>")' % (R('tasks', 'owner_id'), R('tasks', 'status'), DONE, R('tasks', 'task_id')), 9),
    CA('overdue', 'Overdue tasks', 'int', 'COUNTIFS(%s,{col:team_id},%s,">0")' % (R('tasks', 'owner_id'), R('tasks', 'days_overdue')), 9),
    CA('next_pos', 'Next task row', 'int', 'SUMPRODUCT(--(%s={col:team_id}),--(%s=1),%s)' % (R('tasks', 'owner_id'), R('tasks', 'owner_seq'), R('tasks', 'pos')), 9),
    CA('task', 'Next task', 'text', 'IF({col:next_pos}=0,"",INDEX(%s,{col:next_pos}))' % R('tasks', 'title'), 34),
    CA('due_date', 'Next task due', 'date', 'IF({col:next_pos}=0,"",INDEX(%s,{col:next_pos}))' % R('tasks', 'due_date'), 11),
    CA('share', 'Share of open tasks', 'pct', 'IFERROR({col:count}/%s,0)' % OPEN_N, 10),
    SC('ph_par1', 'Parent of partner 1 phone', '{col:role}=%s' % ROLE('Parent of partner 1'), '{col:phone}'), SC('ph_par2', 'Parent of partner 2 phone', '{col:role}=%s' % ROLE('Parent of partner 2'), '{col:phone}'),
    SC('ph_wpl', 'Wedding party lead phone', '{col:role}=%s' % ROLE('Wedding party lead 1'), '{col:phone}'), SC('ph_friend', 'Close friend helper phone', '{col:role}=%s' % ROLE('Close friend helper'), '{col:phone}'),
    SC('ph_coord', 'Day-of coordinator phone', '{col:role}=%s' % ROLE('Day-of coordinator'), '{col:phone}'), CPL()],
    D.team_d(), 50))

# 2 tasks --------------------------------------------------------------------
OPEN_ARR = '(%s<>%s)*(%s<>"")' % (R('tasks', 'status'), DONE, R('tasks', 'task_id'))
E0 = '((%s<{col:due_date})+(%s={col:due_date})*(%s<{col:task_id}))' % (R('tasks', 'due_date'), R('tasks', 'due_date'), R('tasks', 'task_id'))
HEAVY = 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('workload', 'owner'), R('workload', 'open'), R('workload', 'open'))
def VPH(name, label, vendor): return SC(name, label, 'AND({col:vendor}=%s,{col:vendor_seq}=1)' % VN(vendor), '{col:vphone}')
tables.append(T('tasks', 'Tasks', 'Tasks', 'The master checklist: one row per task with its month-out bucket, owner, status and critical flag. Days left, the flag, months before the wedding, overdue rank and the lists on the other sheets fill in by themselves.', [
    C('task_id', 'Task ID', 'text', 9, required=True), C('title', 'Task', 'text', 34), LST('area', 'Area', 'area', 16), LST('when', 'Month-out bucket', 'when', 11), C('due_date', 'Due date', 'date', 11),
    LST('owner', 'Owner', 'owner', 20), C('owner_id', 'Owner ID', 'text', 9), LST('vendor', 'Vendor', 'vname', 18), C('vphone', 'Vendor phone', 'text', 18), LST('status', 'Status', 'tstatus', 12),
    C('done_date', 'Done on', 'date', 11), C('critical', 'Critical', 'bool', 9),
    CA('days_left', 'Days left', 'int', 'IF({col:status}=%s,"",{col:due_date}-{today})' % DONE, 9),
    CA('flag', 'Flag', 'text', 'IF({col:status}=%s,%s,IF({col:days_left}<0,%s,IF({col:days_left}<=7,%s,IF({col:days_left}<=30,%s,%s))))' % (DONE, V('Done'), V('Overdue'), V('This week'), V('This month'), V('Later')), 11),
    CA('days_overdue', 'Days overdue', 'int', 'IF(AND({col:status}<>%s,{col:due_date}<{today}),{today}-{col:due_date},0)' % DONE, 9),
    CA('months_out', 'Months before the wedding', 'num', 'ROUND(({set:wedding_day}-{col:due_date})/30.4,1)', 10),
    CA('score', 'Overdue score', 'int', 'IF({col:days_overdue}>0,IF({col:critical}=%s,1000,0)+{col:days_overdue},"")' % YES, 9),
    CA('over_rank', 'Overdue rank', 'int', 'IF({col:score}="","",COUNTIFS(%s,">"&{col:score})+1+SUMPRODUCT((%s={col:score})*(%s<{col:task_id})))' % (R('tasks', 'score'), R('tasks', 'score'), R('tasks', 'task_id')), 9),
    CA('crit_seq', 'Critical order', 'int', 'IF(AND({col:critical}=%s,{col:status}<>%s),SUMPRODUCT(%s*(%s=%s)*(%s>0))+1,"")' % (YES, DONE, OPEN_ARR, R('tasks', 'critical'), YES, E0), 9),
    CA('week_seq', 'This week order', 'int', 'IF(AND({col:status}<>%s,{col:due_date}<=%s),SUMPRODUCT(%s*(%s<=%s)*(%s>0))+1,"")' % (DONE, TODAYP7, OPEN_ARR, R('tasks', 'due_date'), TODAYP7, E0), 9),
    CA('month_seq', 'This month order', 'int', 'IF(AND({col:status}<>%s,{col:due_date}<={today}+30),SUMPRODUCT(%s*(%s<={today}+30)*(%s>0))+1,"")' % (DONE, OPEN_ARR, R('tasks', 'due_date'), E0), 9),
    CA('owner_pos', 'Owner position', 'int', 'IFERROR(MATCH({col:owner},%s,0),"")' % R('workload', 'owner'), 9),
    CA('nudge_seq', 'Nudge order', 'int', 'IF({col:week_seq}="","",SUMPRODUCT(%s*(%s<=%s)*((%s<{col:owner_pos})+(%s={col:owner_pos})*%s>0))+1)' % (OPEN_ARR, R('tasks', 'due_date'), TODAYP7, R('tasks', 'owner_pos'), R('tasks', 'owner_pos'), E0), 9),
    CA('owner_seq', 'Order for the owner', 'int', 'IF({col:status}<>%s,SUMPRODUCT(%s*(%s={col:owner_id})*(%s>0))+1,"")' % (DONE, OPEN_ARR, R('tasks', 'owner_id'), E0), 9),
    CA('pos', 'Row number', 'int', 'IFERROR(MATCH({col:task_id},%s,0),0)' % R('tasks', 'task_id'), 8),
    CA('vendor_seq', 'Order for the vendor', 'int', 'IF(AND({col:status}<>%s,{col:vendor}<>""),SUMPRODUCT(%s*(%s={col:vendor})*(%s>0))+1,"")' % (DONE, OPEN_ARR, R('tasks', 'vendor'), E0), 9),
    CA('move_seq', 'Delegation order', 'int', 'IF(AND({col:owner}=%s,{col:status}=%s,{col:critical}=%s),SUMPRODUCT(%s*(%s=%s)*(%s=%s)*(%s=%s)*(%s>0))+1,"")' % (HEAVY, NOTST, NO, OPEN_ARR, R('tasks', 'owner'), HEAVY, R('tasks', 'status'), NOTST, R('tasks', 'critical'), NO, E0), 9),
    CA('lead_gap', 'Days short of the lead time', 'int', 'IF({col:status}<>%s,IFERROR(INDEX(%s,MATCH({col:area},%s,0)),0)-{col:days_left},"")' % (DONE, R('fit', 'lead_days'), R('fit', 'area')), 10),
    CA('lead_days', 'Lead days of the area', 'int', 'IFERROR(INDEX(%s,MATCH({col:area},%s,0)),0)' % (R('fit', 'lead_days'), R('fit', 'area')), 9),
    SC('ph_move', 'Parent 1 phone, task to take over', '{col:move_seq}=1', PAR1_PH),
    SC('ph_diy', 'Close friend phone, next DIY task', 'AND({col:area}=%s,{col:status}<>%s,COUNTIFS(%s,%s,%s,"<>"&%s,%s,"<"&{col:due_date})=0)' % (tok('area', 'Decor and DIY'), DONE, R('tasks', 'area'), tok('area', 'Decor and DIY'), R('tasks', 'status'), DONE, R('tasks', 'due_date')), FRIEND_PH),
    VPH('ph_officiant', 'Officiant phone', 'Officiant'), VPH('ph_venue', 'Venue phone', 'Venue'), VPH('ph_caterer', 'Caterer phone', 'Caterer'), VPH('ph_florist', 'Florist phone', 'Florist'),
    VPH('ph_attire', 'Attire shop phone', 'Attire shop'), VPH('ph_tailor', 'Tailor phone', 'Tailor'), CPL()],
    D.tasks_d(), 300, [A('flag', '= ' + V('Overdue'), 'bad'), A('flag', '= ' + V('This week'), 'warn'), A('flag', '= ' + V('Done'), 'good')]))

# 3 wedding types ------------------------------------------------------------
tables.append(T('wtypes', 'Wedding Types', 'Wedding Types', 'The wedding types you can plan for with the typical lead time in months (typical, edit) and what changes. Pick one in Settings; the Task Fit sheet says which task areas apply.', [
    LST('type', 'Wedding type', 'wtype', 26, required=True), C('lead_months', 'Lead months', 'int', 10), C('note', 'What changes', 'text', 46)], D.wtypes_d(), 20))

# 4 task fit by wedding type -------------------------------------------------
tables.append(T('fit', 'Task Fit', 'Task Fit by Wedding Type', 'One row per task area: yes or no for each wedding type (edit them), the typical days a task of this area must be started before its due date and the typical hours one task takes (typical, edit). A small wedding hides the areas marked no.', [
    LST('area', 'Area', 'area', 20, required=True), C('local', 'Local', 'bool', 8), C('destination', 'Destination', 'bool', 10), C('small', 'Small plus a party', 'bool', 10), C('multi', 'Multi-event', 'bool', 10),
    C('home', 'Home or garden', 'bool', 10), C('lead_days', 'Lead days', 'int', 9), C('hours', 'Hours per task', 'num', 9),
    CA('tasks_n', 'Tasks in the area', 'int', 'COUNTIFS(%s,{col:area},%s,"<>")' % (R('tasks', 'area'), R('tasks', 'task_id')), 9)], D.fit_d(), 40))

# 5 month-out progress -------------------------------------------------------
tables.append(T('mprog', 'Month-out Progress', 'Month-out Progress', 'One row per month-out bucket: how many tasks it holds and the share done.', [
    LST('when', 'Month-out bucket', 'when', 20, required=True),
    CA('tasks', 'Tasks', 'int', 'COUNTIFS(%s,{col:when},%s,"<>")' % (R('tasks', 'when'), R('tasks', 'task_id')), 9),
    CA('done_share', 'Done share', 'pct', 'IF({col:tasks}=0,0,COUNTIFS(%s,{col:when},%s,%s,%s,"<>")/{col:tasks})' % (R('tasks', 'when'), R('tasks', 'status'), DONE, R('tasks', 'task_id')), 10)], D.mprog_d(), 20))

# 6 overdue tasks ------------------------------------------------------------
tables.append(T('overdue', 'Overdue Tasks', 'Overdue Tasks', 'Open tasks past their due date, critical ones first and then the longest overdue. It fills in from the Tasks sheet.', [
    C('seqno', 'Rank', 'int', 7, required=True),
    CA('task_id', 'Task ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:seqno},%s,0))&"","")' % (R('tasks', 'task_id'), R('tasks', 'over_rank')), 9),
    CA('task', 'Task', 'text', LKT('tasks.title', 'tasks.task_id', 'task_id'), 34), CA('owner', 'Owner', 'text', LKT('tasks.owner', 'tasks.task_id', 'task_id'), 20),
    CA('due_date', 'Due date', 'date', LKD('tasks.due_date', 'tasks.task_id', 'task_id'), 11), CA('days_overdue', 'Days overdue', 'int', LKN('tasks.days_overdue', 'tasks.task_id', 'task_id'), 9),
    CA('critical', 'Critical', 'text', LKT('tasks.critical', 'tasks.task_id', 'task_id'), 9), CA('count', 'Tasks overdue', 'int', 'COUNTIFS(%s,">0")' % R('tasks', 'days_overdue'), 9),
    SC('ph_p2', 'Partner phone, first row', 'AND({col:seqno}=1,{col:task_id}<>"")', P2_PH), CPL()],
    D.slots(12), 50, [A('days_overdue', '> 0', 'bad')]))

# 7 critical path ------------------------------------------------------------
tables.append(T('critical', 'Critical Path', 'Critical Path', 'The open critical tasks in date order with the days between each one and the next (the slack). A task that is late or has no slack moves the wedding date.', [
    C('seqno', 'Order', 'int', 7, required=True),
    CA('task_id', 'Task ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:seqno},%s,0))&"","")' % (R('tasks', 'task_id'), R('tasks', 'crit_seq')), 9),
    CA('task', 'Task', 'text', LKT('tasks.title', 'tasks.task_id', 'task_id'), 34), CA('due_date', 'Due date', 'date', LKD('tasks.due_date', 'tasks.task_id', 'task_id'), 11),
    CA('status', 'Status', 'text', LKT('tasks.status', 'tasks.task_id', 'task_id'), 12), CA('days_left', 'Days left', 'int', LKN('tasks.days_left', 'tasks.task_id', 'task_id'), 9),
    CA('slack', 'Slack to the next critical task', 'int', 'IFERROR(IF(INDEX(%s,{col:seqno}+1)="","",INDEX(%s,{col:seqno}+1)-{col:due_date}),"")' % (R('critical', 'due_date'), R('critical', 'due_date')), 11),
    CA('count', 'Open critical tasks', 'int', 'COUNTIFS(%s,">0")' % R('tasks', 'crit_seq'), 9),
    SC('ph_p2', 'Partner phone, first row', 'AND({col:seqno}=1,{col:task_id}<>"")', P2_PH), CPL()],
    D.slots(20), 50, [A('days_left', '< 0', 'bad'), A('days_left', '<= 7', 'warn')]))

# 8 workload by owner --------------------------------------------------------
tables.append(T('workload', 'Workload by Owner', 'Workload by Owner', 'Open tasks for each owner and the share of all open tasks; the set maximum share is in Settings.', [
    LST('owner', 'Owner', 'owner', 24, required=True),
    CA('open', 'Open tasks', 'int', 'COUNTIFS(%s,{col:owner},%s,"<>"&%s,%s,"<>")' % (R('tasks', 'owner'), R('tasks', 'status'), DONE, R('tasks', 'task_id')), 10),
    CA('share', 'Share of open tasks', 'pct', 'IFERROR({col:open}/%s,0)' % OPEN_N, 10)], D.workload_d(), 20, [A('share', '> {set:owner_share_max}', 'bad')]))

# 9 owner overdue and next seven days ---------------------------------------
tables.append(T('nudge', 'Owner Nudge List', 'Owner Overdue and Next Seven Days', 'Open tasks that are overdue or due in the next seven days, grouped by owner with the owner\'s phone, so you know who to nudge.', [
    C('seqno', 'Order', 'int', 7, required=True),
    CA('task_id', 'Task ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:seqno},%s,0))&"","")' % (R('tasks', 'task_id'), R('tasks', 'nudge_seq')), 9),
    CA('owner', 'Owner', 'text', LKT('tasks.owner', 'tasks.task_id', 'task_id'), 20), CA('task', 'Task', 'text', LKT('tasks.title', 'tasks.task_id', 'task_id'), 34),
    CA('due_date', 'Due date', 'date', LKD('tasks.due_date', 'tasks.task_id', 'task_id'), 11),
    CA('phone', 'Owner phone', 'text', 'IF({col:task_id}="","",IFERROR(INDEX(%s,MATCH(INDEX(%s,MATCH({col:task_id},%s,0)),%s,0)),""))' % (R('team', 'phone'), R('tasks', 'owner_id'), R('tasks', 'task_id'), R('team', 'team_id')), 18),
    CA('flag', 'Flag', 'text', LKT('tasks.flag', 'tasks.task_id', 'task_id'), 11),
    CA('share', 'Owner share of open tasks', 'pct', 'IF({col:task_id}="","",IFERROR(INDEX(%s,MATCH({col:owner},%s,0)),0))' % (R('workload', 'share'), R('workload', 'owner')), 10),
    CA('n_owner', 'Tasks of the owner here', 'int', 'IF({col:task_id}="","",COUNTIFS(%s,{col:owner}))' % R('nudge', 'owner'), 9),
    SC('ph_share', 'Partner phone, owner over the share', 'AND({col:task_id}<>"",{col:share}>={set:owner_share_max},COUNTIFS(%s,{col:owner},%s,"<"&{col:seqno})=0)' % (R('nudge', 'owner'), R('nudge', 'seqno')), P2_PH), CPL()],
    D.slots(15), 50, [A('flag', '= ' + V('Overdue'), 'bad'), A('flag', '= ' + V('This week'), 'warn')]))

# 10 task area summary -------------------------------------------------------
tables.append(T('areasum', 'Task Area Summary', 'Task Area Summary', 'One row per task area: tasks, done, open, overdue and share of all tasks; the helper is who usually takes tasks of that area when one owner holds too many (your own choice).', [
    LST('area', 'Area', 'area', 20, required=True), LST('helper', 'Usual helper', 'owner', 20),
    CA('tasks', 'Tasks', 'int', 'COUNTIFS(%s,{col:area},%s,"<>")' % (R('tasks', 'area'), R('tasks', 'task_id')), 9),
    CA('done', 'Done', 'int', 'COUNTIFS(%s,{col:area},%s,%s,%s,"<>")' % (R('tasks', 'area'), R('tasks', 'status'), DONE, R('tasks', 'task_id')), 9), CA('open', 'Open', 'int', '{col:tasks}-{col:done}', 9),
    CA('overdue', 'Overdue', 'int', 'COUNTIFS(%s,{col:area},%s,">0")' % (R('tasks', 'area'), R('tasks', 'days_overdue')), 9),
    CA('share', 'Share of all tasks', 'pct', 'IFERROR({col:tasks}/%s,0)' % ALL_N, 10)], D.areasum_d(), 40, [A('overdue', '> 0', 'warn')]))

# 11 key dates ---------------------------------------------------------------
KD = ['Wedding day', 'Reply-by date', 'Final headcount date', 'Room cut-off date', 'Invitation files to the printer', 'Next fitting', 'Last fitting', 'Next payment due', 'Last scheduled payment',
      'Next critical task due', 'Next planning review', 'Thank-you notes target']
KS = ['Wedding', 'Guests', 'Vendors', 'Hotel', 'Paper', 'Attire', 'Attire', 'Payments', 'Payments', 'Tasks', 'Planning', 'After']
KDATE = ('CHOOSE({col:no},{set:wedding_day},{set:rsvp_deadline},{set:headcount_date},{set:room_cutoff},%s,IFERROR(SMALL(%s,1),""),IF(COUNT(%s)=0,"",MAX(%s)),IFERROR(SMALL(%s,1),""),IF(COUNT(%s)=0,"",MAX(%s)),'
         'IFERROR(INDEX(%s,MATCH(1,%s,0)),""),EOMONTH({today},0)+1,{set:wedding_day}+{set:thankyou_target_days})') % (
    SENDBY, R('party', 'dl_date'), R('party', 'fitting_date'), R('party', 'fitting_date'), R('schedule', 'dl_date'), R('schedule', 'due_date'), R('schedule', 'due_date'), R('tasks', 'due_date'), R('tasks', 'crit_seq'))
def RANK(me, d, first_ties, same_tie):
    """position of a deadline among the dates of the four sources (key dates, payments, vendor cut-offs, fittings); ties go to the earlier source"""
    cnt = '+'.join('COUNTIFS(%s,"<"&%s)' % (R(t_, 'dl_date'), d) for t_ in ('key', 'schedule', 'contracts', 'party'))
    return 'IF(%s="","",%s+1+%s%s)' % (d, cnt, same_tie, first_ties)
tables.append(T('key', 'Key Dates', 'Key Dates', 'Twelve dates the whole plan hangs on, each pulled from the settings or from another sheet, with the days left and a red, amber or green flag; change a date in Settings and it moves everywhere.', [
    C('no', 'No', 'int', 6, required=True),
    CA('item', 'Key date', 'text', 'CHOOSE({col:no},%s)' % ','.join(V(x) for x in KD), 30), CA('date', 'Date', 'date', KDATE, 11),
    CA('days_left', 'Days left', 'int', 'IF({col:date}="","",{col:date}-{today})', 9), CA('source', 'Source', 'text', 'CHOOSE({col:no},%s)' % ','.join(V(x) for x in KS), 12),
    CA('flag', 'Flag', 'text', 'IF({col:days_left}="","",IF({col:days_left}<={set:red_days},%s,IF({col:days_left}<={set:amber_days},%s,%s)))' % (V('Red'), V('Amber'), V('Green')), 9),
    CA('dl_date', 'Date for the countdown', 'date', 'IF(OR({col:date}="",AND({col:no}>5,{col:no}<11)),"",IF({col:date}>={today},{col:date},""))', 11),
    CA('dl_rank', 'Countdown order', 'int', RANK('key', '{col:dl_date}', '', 'SUMPRODUCT((%s={col:dl_date})*(%s<{col:no}))' % (R('key', 'dl_date'), R('key', 'no'))), 9),
    CA('move_days', 'Days the date moves', 'int', '{set:move_days}', 9),
    CA('count_moved', 'Tasks newly overdue after the move', 'int', 'COUNTIFS(%s,"<>"&%s,%s,"<>",%s,">="&{today},%s,"<"&{today}+{set:move_days})' % (R('tasks', 'status'), DONE, R('tasks', 'task_id'), R('tasks', 'due_date'), R('tasks', 'due_date')), 10),
    CA('open', 'Open tasks', 'int', OPEN_N, 9), CA('done_share', 'Tasks done', 'pct', 'IFERROR(%s/%s,0)' % (DONE_N, ALL_N), 9),
    SC('ph_print', 'Partner phone, printer date', '{col:no}=5', P2_PH), SC('ph_review', 'Partner phone, planning review', '{col:no}=11', P2_PH),
    SC('ph_next', 'Partner phone, next key date', 'AND({col:date}<>"",{col:date}>={today},COUNTIFS(%s,">="&{today},%s,"<"&{col:date})=0)' % (R('key', 'date'), R('key', 'date')), P2_PH),
    SC('ph_one', 'Partner phone, wedding day row', '{col:no}=1', P2_PH),
    CA('ph_hotel', 'Hotel phone, room cut-off row', 'text', 'IF({col:no}=4,IFERROR(INDEX(%s,MATCH(%s,%s,0)),""),"")' % (R('schedule', 'phone'), VN('Hotel room block'), R('schedule', 'vendor')), 18), CPL()],
    D.key_d(), 50, [A('flag', '= ' + V('Red'), 'bad'), A('flag', '= ' + V('Amber'), 'warn'), A('flag', '= ' + V('Green'), 'good')]))

# 12 deadlines across the wedding -------------------------------------------
def MT(t_, c_='dl_rank'): return 'ISNUMBER(MATCH({col:seqno},%s,0))' % R(t_, c_)
def MP(t_): return 'MATCH({col:seqno},%s,0)' % R(t_, 'dl_rank')
UPCOMING = 'AND({col:date}<>"",{col:days_left}>=0,COUNTIFS(%s,">=0",%s,"<"&{col:seqno})=0)' % (R('deadlines', 'days_left'), R('deadlines', 'seqno'))
tables.append(T('deadlines', 'Deadlines across Wedding', 'Deadlines across the Wedding', 'The next dates from every part in date order: payments still to pay, the reply-by date, the headcount date, the room cut-off, vendor cut-offs and fittings, each red, amber or green on the days you set. It fills in from the other sheets.', [
    C('seqno', 'Order', 'int', 7, required=True),
    CA('src', 'Source', 'int', 'IF(%s,1,IF(%s,2,IF(%s,3,IF(%s,4,0))))' % (MT('key'), MT('schedule'), MT('contracts'), MT('party')), 7),
    CA('pos', 'Row in the source', 'int', 'IF({col:src}=0,"",CHOOSE({col:src},%s,%s,%s,%s))' % (MP('key'), MP('schedule'), MP('contracts'), MP('party')), 7),
    CA('part', 'Part', 'text', 'IF({col:src}=0,"",CHOOSE({col:src},%s,%s,%s,%s))' % (V('Key date'), V('Payment'), V('Vendor cut-off'), V('Fitting')), 14),
    CA('item', 'Item', 'text', 'IF({col:src}=0,"",CHOOSE({col:src},INDEX(%s,{col:pos}),INDEX(%s,{col:pos}),INDEX(%s,{col:pos}),INDEX(%s,{col:pos})))' % (R('key', 'item'), R('schedule', 'dl_item'), R('contracts', 'dl_item'), R('party', 'dl_item')), 30),
    CA('date', 'Date', 'date', 'IF({col:src}=0,"",CHOOSE({col:src},INDEX(%s,{col:pos}),INDEX(%s,{col:pos}),INDEX(%s,{col:pos}),INDEX(%s,{col:pos})))' % (R('key', 'dl_date'), R('schedule', 'dl_date'), R('contracts', 'dl_date'), R('party', 'dl_date')), 11),
    CA('days_left', 'Days left', 'int', 'IF({col:date}="","",{col:date}-{today})', 9),
    CA('rag', 'Red, amber, green', 'text', 'IF({col:date}="","",IF({col:days_left}<={set:red_days},%s,IF({col:days_left}<={set:amber_days},%s,%s)))' % (V('Red'), V('Amber'), V('Green')), 10),
    SC('ph_p2', 'Partner phone, next deadline', UPCOMING, P2_PH), SC('ph_coord', 'Coordinator phone, next deadline', UPCOMING, COORD_PH), CPL()],
    D.slots(45), 80, [A('rag', '= ' + V('Red'), 'bad'), A('rag', '= ' + V('Amber'), 'warn'), A('rag', '= ' + V('Green'), 'good')]))

# 13 this week ---------------------------------------------------------------
def SLOT_COLS(tkey, seqcol):
    return [C('seqno', 'Order', 'int', 7, required=True),
            CA('task_id', 'Task ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:seqno},%s,0))&"","")' % (R('tasks', 'task_id'), R('tasks', seqcol)), 9),
            CA('task', 'Task', 'text', LKT('tasks.title', 'tasks.task_id', 'task_id'), 34), CA('owner', 'Owner', 'text', LKT('tasks.owner', 'tasks.task_id', 'task_id'), 20),
            CA('due_date', 'Due date', 'date', LKD('tasks.due_date', 'tasks.task_id', 'task_id'), 11), CA('status', 'Status', 'text', LKT('tasks.status', 'tasks.task_id', 'task_id'), 12),
            CA('days_left', 'Days left', 'int', LKN('tasks.days_left', 'tasks.task_id', 'task_id'), 9)]
tables.append(T('week', 'This Week', 'This Week', 'Everything open that is overdue or due in the next seven days, in date order. It fills in from the Tasks sheet.', SLOT_COLS('week', 'week_seq') + [
    CA('when', 'Month-out bucket', 'text', LKT('tasks.when', 'tasks.task_id', 'task_id'), 11), CA('count', 'Tasks this week', 'int', 'COUNTIFS(%s,">0")' % R('tasks', 'week_seq'), 9),
    CA('bucket_done', 'Done share of the bucket', 'pct', 'IF({col:when}="","",IFERROR(INDEX(%s,MATCH({col:when},%s,0)),0))' % (R('mprog', 'done_share'), R('mprog', 'when')), 10),
    CA('count_pay', 'Payments due this week', 'int', 'COUNTIFS(%s,"<>"&%s,%s,"<="&%s,%s,"<>")' % (R('schedule', 'status'), PAID, R('schedule', 'due_date'), TODAYP7, R('schedule', 'pay_id')), 9),
    SC('ph_p2', 'Partner phone, first row', 'AND({col:seqno}=1,{col:task_id}<>"")', P2_PH), CPL()], D.slots(12), 50, [A('days_left', '< 0', 'bad'), A('days_left', '<= 7', 'warn')]))

# 14 this month --------------------------------------------------------------
tables.append(T('month', 'This Month', 'This Month', 'Everything open that is overdue or due in the next 30 days, in date order. It fills in from the Tasks sheet.', SLOT_COLS('month', 'month_seq'), D.slots(30), 60,
                [A('days_left', '< 0', 'bad'), A('days_left', '<= 7', 'warn')]))

# 15 payment schedule (reference copy) --------------------------------------
def DLR(d, pre, same):
    return 'IF(%s="","",%s+1+%s+%s)' % (d, '+'.join('COUNTIFS(%s,"<"&%s)' % (R(t_, 'dl_date'), d) for t_ in ('key', 'schedule', 'contracts', 'party')), same, pre)
tables.append(T('schedule', 'Payment Schedule', 'Payment Schedule', 'A copy of the payment schedule from the budget workbook: the dates feed the Deadlines sheet. Paid rows drop out of the countdown.', [
    C('pay_id', 'Pay ID', 'text', 9, required=True), LST('vendor', 'Vendor', 'vname', 22), LST('kind', 'Kind', 'paykind', 12), C('due_date', 'Due date', 'date', 11), C('amount_due', 'Amount due', 'money', 11),
    LST('status', 'Status', 'paystatus', 11), C('phone', 'Vendor phone', 'text', 18),
    CA('dl_date', 'Date for the countdown', 'date', 'IF({col:status}<>%s,{col:due_date},"")' % PAID, 11), CA('dl_item', 'Countdown item', 'text', '{col:vendor}&" "&{col:kind}', 30),
    CA('dl_rank', 'Countdown order', 'int', DLR('{col:dl_date}', 'COUNTIFS(%s,{col:dl_date})' % R('key', 'dl_date'), 'SUMPRODUCT((%s={col:dl_date})*(%s<{col:pay_id}))' % (R('schedule', 'dl_date'), R('schedule', 'pay_id'))), 9),
    CA('days_left', 'Days left', 'int', 'IF({col:status}<>%s,{col:due_date}-{today},"")' % PAID, 9), CA('quantity', 'Invitation suites', 'int', '{set:suites}', 9),
    SC('ph_pay', 'Partner phone, payment due soon', 'AND({col:status}<>%s,{col:days_left}>=0,{col:days_left}<=14)' % PAID, P2_PH),
    SC('ph_printer', 'Printer phone, final balance', 'AND({col:vendor}=%s,{col:status}<>%s)' % (VN('Stationery printer'), PAID), '{col:phone}'), CPL()],
    D.schedule_d(), 100, [A('status', '= ' + PAID, 'good'), A('status', '= ' + tok('paystatus', 'Overdue'), 'bad')]))

# 16 contract items (reference copy) ----------------------------------------
tables.append(T('contracts', 'Contract Items', 'Contract Items', 'A copy of the contract items from the vendor workbook: final headcount dates are vendor cut-offs and feed the Deadlines sheet. Check your contract for every date.', [
    C('contract_id', 'Contract ID', 'text', 9, required=True), LST('vendor', 'Vendor', 'vname', 22), LST('kind', 'Kind', 'ckind', 20), C('detail', 'Detail', 'text', 36), C('item_date', 'Item date', 'date', 11),
    CA('dl_date', 'Date for the countdown', 'date', 'IF(AND({col:kind}=%s,{col:item_date}>={today}),{col:item_date},"")' % FINALHC, 11), CA('dl_item', 'Countdown item', 'text', '{col:vendor}&" "&{col:kind}', 30),
    CA('dl_rank', 'Countdown order', 'int', DLR('{col:dl_date}', 'COUNTIFS(%s,{col:dl_date})+COUNTIFS(%s,{col:dl_date})' % (R('key', 'dl_date'), R('schedule', 'dl_date')),
                                                'SUMPRODUCT((%s={col:dl_date})*(%s<{col:contract_id}))' % (R('contracts', 'dl_date'), R('contracts', 'contract_id'))), 9)],
    D.contracts_d(), 150))

# 17 wedding party (reference copy) -----------------------------------------
tables.append(T('party', 'Wedding Party', 'Wedding Party', 'A copy of the wedding party from the party workbook: fitting dates feed the Deadlines sheet until attire is Ready.', [
    C('party_id', 'Party ID', 'text', 9, required=True), C('person', 'Person', 'text', 24), LST('role', 'Role', 'prole', 16), C('fitting_date', 'Fitting date', 'date', 11), LST('attire_status', 'Attire status', 'attire', 13),
    CA('dl_date', 'Date for the countdown', 'date', 'IF(AND({col:fitting_date}>={today},{col:attire_status}<>%s),{col:fitting_date},"")' % READY, 11), CA('dl_item', 'Countdown item', 'text', '{col:person}&" "&%s' % V('Fitting'), 30),
    CA('dl_rank', 'Countdown order', 'int', DLR('{col:dl_date}', 'COUNTIFS(%s,{col:dl_date})+COUNTIFS(%s,{col:dl_date})+COUNTIFS(%s,{col:dl_date})' % (R('key', 'dl_date'), R('schedule', 'dl_date'), R('contracts', 'dl_date')),
                                                'SUMPRODUCT((%s={col:dl_date})*(%s<{col:party_id}))' % (R('party', 'dl_date'), R('party', 'party_id'))), 9)],
    D.party_d(), 50))

# 18 compressed plan ---------------------------------------------------------
WIN = 'ROUND({set:plan_months}*30.4,0)'
SPAN = '({set:wedding_day}-MIN(%s))' % R('tasks', 'due_date')
tables.append(T('compress', 'Compressed Plan', 'Compressed Plan', 'Every task re-dated in proportion as if you had only the months you set in Settings: the task fits when the new date leaves its lead time after the start; the others are Do now (critical) or Drop or merge.', [
    C('task_id', 'Task ID', 'text', 9, required=True), CA('title', 'Task', 'text', LKT('tasks.title', 'tasks.task_id', 'task_id'), 34), CA('area', 'Area', 'text', LKT('tasks.area', 'tasks.task_id', 'task_id'), 16),
    CA('critical', 'Critical', 'text', LKT('tasks.critical', 'tasks.task_id', 'task_id'), 9), CA('original_due', 'Original due', 'date', LKD('tasks.due_date', 'tasks.task_id', 'task_id'), 11),
    CA('compressed_due', 'Compressed due', 'date', 'IF({col:original_due}="","",{set:wedding_day}-ROUND(({set:wedding_day}-{col:original_due})*MIN(1,%s/%s),0))' % (WIN, SPAN), 11),
    CA('lead_days', 'Lead days', 'int', 'IF({col:area}="","",IFERROR(INDEX(%s,MATCH({col:area},%s,0)),0))' % (R('fit', 'lead_days'), R('fit', 'area')), 9),
    CA('fits', 'Fits', 'text', 'IF({col:original_due}="","",IF(%s>=%s,%s,IF({col:compressed_due}-({set:wedding_day}-%s)>={col:lead_days},%s,IF({col:critical}=%s,%s,%s))))' % (WIN, SPAN, V('Fits'), WIN, V('Fits'), YES, V('Do now'), V('Drop or merge')), 13),
    CA('count_drop', 'Tasks that no longer fit', 'int', 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (R('compress', 'fits'), V('Do now'), R('compress', 'fits'), V('Drop or merge')), 9),
    SC('ph_p2', 'Partner phone, first row', '{col:task_id}=INDEX(%s,1)' % R('compress', 'task_id'), P2_PH), CPL()],
    D.compress_d(), 300, [A('fits', '= ' + V('Do now'), 'bad'), A('fits', '= ' + V('Drop or merge'), 'warn')]))

# 19 next 12 weeks -----------------------------------------------------------
WS = '{col:week_start}'
WK = '%s,">="&%s,%s,"<"&%s+7' % (R('tasks', 'due_date'), WS, R('tasks', 'due_date'), WS)
tables.append(T('weeks', 'Next 12 Weeks', 'Next 12 Weeks', 'The next twelve weeks, Monday to Sunday: tasks due, done and still open, the hours the open ones need at the typical hours per task, the payments due and a Heavy or Doable flag against the hours you can give.', [
    C('seqno', 'Week', 'int', 7, required=True), CA('week_start', 'Week starts', 'date', '{today}-WEEKDAY({today},2)+1+7*({col:seqno}-1)', 11),
    CA('tasks_due', 'Tasks due', 'int', 'COUNTIFS(%s,%s,"<>")' % (WK, R('tasks', 'task_id')), 9),
    CA('done', 'Done', 'int', 'COUNTIFS(%s,%s,%s,%s,"<>")' % (WK, R('tasks', 'status'), DONE, R('tasks', 'task_id')), 9), CA('open', 'Open', 'int', '{col:tasks_due}-{col:done}', 9),
    CA('hours', 'Hours of open tasks', 'num', 'SUMPRODUCT(COUNTIFS(%s,%s,%s,"<>"&%s,%s,"<>",%s),%s)' % (R('tasks', 'area'), R('fit', 'area'), R('tasks', 'status'), DONE, R('tasks', 'task_id'), WK, R('fit', 'hours')), 10),
    CA('payments_due', 'Payments due', 'money', 'SUMIFS(%s,%s,"<>"&%s,%s,">="&%s,%s,"<"&%s+7)' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'), WS, R('schedule', 'due_date'), WS), 11),
    CA('flag', 'Flag', 'text', 'IF({col:hours}>{set:week_hours},%s,%s)' % (V('Heavy'), V('Doable')), 9)], D.slots(12), 50, [A('flag', '= ' + V('Heavy'), 'warn')]))

# 20 done by month -----------------------------------------------------------
tables.append(T('doneby', 'Done by Month', 'Done by Month', 'One row per month: tasks done in the month, tasks that were due and how many of those are still open. Add months as the plan runs on.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('done', 'Tasks done', 'int', 'COUNTIFS(%s,">="&{col:month},%s,"<"&EDATE({col:month},1),%s,"<>")' % (R('tasks', 'done_date'), R('tasks', 'done_date'), R('tasks', 'task_id')), 9),
    CA('due', 'Tasks due', 'int', 'COUNTIFS(%s,">="&{col:month},%s,"<"&EDATE({col:month},1),%s,"<>")' % (R('tasks', 'due_date'), R('tasks', 'due_date'), R('tasks', 'task_id')), 9),
    CA('open', 'Due and still open', 'int', 'COUNTIFS(%s,">="&{col:month},%s,"<"&EDATE({col:month},1),%s,"<>"&%s,%s,"<>")' % (R('tasks', 'due_date'), R('tasks', 'due_date'), R('tasks', 'status'), DONE, R('tasks', 'task_id')), 9)],
    D.doneby_d(), 50))

for _t in tables: _t['rows'] = max(50, _t['rows'])
assert len(tables) == 20, len(tables)
