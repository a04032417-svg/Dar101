"""Wedding Planning suite - part 4: Master Timeline, Checklist and Task Owners."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp4_lists import *
from wp4_tables import *
from wp4_lists import _VW
from wp4_tools import tools, OVN, HOLD, GR, CNT, TC, TID, OPENC
import wp4_data as D

SUITE = 'fx-20261116-wedding'
NOTE = "Sample wording: adapt it to your own wedding."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c_): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c_, t, idc)

# ------------------------------------------------------------------ forms (12)
IDXP = 'MATCH({pick},%s,0)' % R('wtypes', 'type')
FITP = 'CHOOSE(%s,%s,%s,%s,%s,%s)' % (IDXP, R('fit', 'local'), R('fit', 'destination'), R('fit', 'small'), R('fit', 'multi'), R('fit', 'home'))
APPLYP = 'SUMPRODUCT(COUNTIFS(%s,%s,%s),--(%s=%s))' % (R('tasks', 'area'), R('fit', 'area'), 'tasks_id_placeholder', FITP, YES)
APPLYP = APPLYP.replace('tasks_id_placeholder', '%s,"<>"' % R('tasks', 'task_id'))
forms = [
    FORM('task_sheet', 'Task Sheet', 'One task', 'tasks.task_id', F(('Task', 'tasks.title'), ('Area', 'tasks.area'), ('Month-out bucket', 'tasks.when'), ('Due date', 'tasks.due_date'), ('Owner', 'tasks.owner'), ('Status', 'tasks.status'),
        ('Done on', 'tasks.done_date'), ('Critical', 'tasks.critical'), ('Flag', 'tasks.flag'), ('Months before the wedding', 'tasks.months_out'), ('Days overdue', 'tasks.days_overdue'))),
    FORM('done_sheet', 'Task Done Sheet', 'One task done', 'tasks.task_id', F(('Task', 'tasks.title'), ('Owner', 'tasks.owner'), ('Due date', 'tasks.due_date'), ('Done on', 'tasks.done_date'), ('Status', 'tasks.status')) + [
        FF('Days early (minus) or late', 'IFERROR(%s-%s,"")' % (LK('tasks', 'task_id', 'done_date'), LK('tasks', 'task_id', 'due_date')), 'int'),
        FF('Done on time', 'IF(%s<=%s,{list:yesno.yes},{list:yesno.no})' % (LK('tasks', 'task_id', 'done_date'), LK('tasks', 'task_id', 'due_date')), 'text'), FF('Month-out bucket of the task', LK('tasks', 'task_id', 'when'), 'text')]),
    FORM('owner_sheet', 'Owner Change Sheet', 'One task and its owner', 'tasks.task_id', F(('Task', 'tasks.title'), ('Current owner', 'tasks.owner'), ('Owner ID', 'tasks.owner_id'), ('Area', 'tasks.area')) + [
        FF('Owner phone', 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.team_id},0)),"")' % LK('tasks', 'task_id', 'owner_id'), 'text'),
        FF('Usual helper for the area', 'IFERROR(INDEX({range:areasum.helper},MATCH(%s,{range:areasum.area},0)),"")' % LK('tasks', 'task_id', 'area'), 'text'),
        FF('Open tasks of the owner', 'IFERROR(INDEX({range:workload.open},MATCH(%s,{range:workload.owner},0)),0)' % LK('tasks', 'task_id', 'owner'), 'int'),
        FF('Share of the open tasks', 'IFERROR(INDEX({range:workload.share},MATCH(%s,{range:workload.owner},0)),0)' % LK('tasks', 'task_id', 'owner'), 'pct'), FF('Most one owner should hold', '{set:owner_share_max}', 'pct')]),
    FORM('date_sheet', 'Date Change Sheet', 'One key date if the wedding moves', 'key.no', F(('Key date', 'key.item'), ('Date', 'key.date'), ('Days left', 'key.days_left'), ('Days the wedding moves earlier', 'key.move_days'),
        ('Tasks newly overdue after the move', 'key.count_moved')) + [FF('Date if the wedding moves earlier', 'IFERROR(%s-{set:move_days},"")' % LK('key', 'no', 'date'), 'date'), FF('Wedding day', '{set:wedding_day}', 'date')]),
    FORM('wtype_sheet', 'Wedding Type Sheet', 'One wedding type', 'wtypes.type', F(('Typical lead time, months', 'wtypes.lead_months'), ('What changes', 'wtypes.note')) + [
        FF('Tasks that apply', APPLYP, 'int'), FF('Tasks hidden', '%s-%s' % (ALL_N, APPLYP), 'int'), FF('Tasks in the plan', ALL_N, 'int'), FF('Months you have to plan', '{set:plan_months}', 'int')]),
    FORM('critical_sheet', 'Critical Task Sheet', 'One critical task', 'critical.seqno', F(('Task', 'critical.task'), ('Due date', 'critical.due_date'), ('Status', 'critical.status'), ('Days left', 'critical.days_left'),
        ('Slack to the next critical task', 'critical.slack'), ('Open critical tasks', 'critical.count'))),
    FORM('weekly_sheet', 'Weekly Plan Sheet', 'One task of this week', 'week.seqno', F(('Task', 'week.task'), ('Owner', 'week.owner'), ('Due date', 'week.due_date'), ('Status', 'week.status'), ('Days left', 'week.days_left'),
        ('Month-out bucket', 'week.when'), ('Tasks this week', 'week.count'), ('Hours you can give a week', 'week.count')) [:7] + [FF('Hours you can give a week', '{set:week_hours}', 'int')]),
    FORM('deadline_sheet', 'Deadline Sheet', 'One deadline', 'deadlines.seqno', F(('Part', 'deadlines.part'), ('Item', 'deadlines.item'), ('Date', 'deadlines.date'), ('Days left', 'deadlines.days_left'), ('Red, amber, green', 'deadlines.rag')) + [
        FF('Red when days are at most', '{set:red_days}', 'int'), FF('Amber when days are at most', '{set:amber_days}', 'int')]),
    FORM('delegation_sheet', 'Delegation Sheet', 'One task area and its helper', 'areasum.area', F(('Usual helper', 'areasum.helper'), ('Tasks', 'areasum.tasks'), ('Done', 'areasum.done'), ('Open', 'areasum.open'), ('Overdue', 'areasum.overdue'),
        ('Share of all tasks', 'areasum.share')) + [FF('Heaviest owner now', HOLD, 'text'), FF('Most one owner should hold', '{set:owner_share_max}', 'pct')]),
    FORM('review_sheet', 'Month Review Sheet', 'One month of the plan', 'doneby.month', F(('Tasks done', 'doneby.done'), ('Tasks due', 'doneby.due'), ('Due and still open', 'doneby.open')) + [
        FF('Done less due', '%s-%s' % (LK('doneby', 'month', 'done'), LK('doneby', 'month', 'due')), 'int'), FF('Tasks overdue today', OVN, 'int'), FF('Share of the plan done', 'IFERROR(%s/%s,0)' % (DONE_N, ALL_N), 'pct')]),
    FORM('keydate_sheet', 'Key Date Sheet', 'One key date', 'key.no', F(('Key date', 'key.item'), ('Date', 'key.date'), ('Days left', 'key.days_left'), ('Source', 'key.source'), ('Red, amber, green', 'key.flag'), ('Open tasks', 'key.open'),
        ('Tasks done', 'key.done_share'))),
    FORM('small_sheet', 'Small Wedding Task Sheet', 'One task area for a small wedding', 'fit.area', F(('Applies to a local wedding', 'fit.local'), ('Applies to a destination wedding', 'fit.destination'), ('Applies to a small wedding plus a party', 'fit.small'),
        ('Applies to a multi-event wedding', 'fit.multi'), ('Applies to a home or garden wedding', 'fit.home'), ('Lead days', 'fit.lead_days'), ('Hours per task', 'fit.hours'), ('Tasks in the area', 'fit.tasks_n'))),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('master_page', 'Master Checklist Page', 'Master checklist by month-out', 'mprog.when', [
        '{set:couple}, dated {today}. Master checklist for the wedding on {set:wedding_day}, bucket {col:mprog.when}.',
        'Tasks in the bucket: {col:mprog.tasks}. Done share: {col:mprog.done_share}.', 'Open the Tasks sheet and look at the rows of this bucket for the full list with owners and due dates.'], ['The couple', 'Parent'], NOTE),
    DOC('week_page', 'This Week Page', 'This week', 'week.seqno', [
        '{set:couple}, dated {today}. This week: {col:week.count} tasks, overdue ones included, and {col:week.count_pay} payments.',
        'Task {col:week.seqno}: {col:week.task}. Owner: {col:week.owner}. Due: {col:week.due_date}. Days left: {col:week.days_left}. Status: {col:week.status}.'], ['The couple', 'Helper'], NOTE),
    DOC('month_page', 'This Month Page', 'This month', 'month.seqno', [
        '{set:couple}, dated {today}. The next 30 days, overdue tasks included.',
        'Task {col:month.seqno}: {col:month.task}. Owner: {col:month.owner}. Due: {col:month.due_date}. Days left: {col:month.days_left}. Status: {col:month.status}.'], ['The couple', 'Helper'], NOTE),
    DOC('overdue_page', 'Overdue Tasks Page', 'Overdue tasks', 'overdue.seqno', [
        '{set:couple}, dated {today}. Tasks overdue: {col:overdue.count}.',
        'Rank {col:overdue.seqno}: {col:overdue.task}. Owner: {col:overdue.owner}. Due: {col:overdue.due_date}, {col:overdue.days_overdue} days overdue. Critical: {col:overdue.critical}.'], ['The couple', 'Owner'], NOTE),
    DOC('critical_page', 'Critical Path Page', 'Critical path', 'critical.seqno', [
        '{set:couple}, dated {today}. Open critical tasks: {col:critical.count}.',
        'Task {col:critical.seqno}: {col:critical.task}. Due: {col:critical.due_date}. Days left: {col:critical.days_left}. Slack to the next critical task: {col:critical.slack} days.'], ['The couple', 'Parent'], NOTE),
    DOC('workload_page', 'Workload by Owner Page', 'Workload of one owner', 'workload.owner', [
        '{set:couple}, dated {today}. Owner: {col:workload.owner}.',
        'Open tasks: {col:workload.open}. Share of all open tasks: {col:workload.share}. The most one owner should hold, your own rule: {set:owner_share_max}.'], ['The couple', 'The owner'], NOTE),
    DOC('deadline_page', 'Deadline Countdown Page', 'Deadline countdown', 'deadlines.seqno', [
        '{set:couple}, dated {today}. Deadline {col:deadlines.seqno}, from the part {col:deadlines.part}.',
        '{col:deadlines.item} on {col:deadlines.date}, {col:deadlines.days_left} days left. Colour: {col:deadlines.rag}.', 'Check your contract for every vendor date.'], ['The couple', 'Parent'], NOTE),
    DOC('owner_page', 'Owner Task List', 'Task list for one person', 'team.team_id', [
        'Task list for {col:team.name}, {col:team.role}, dated {today}. Wedding of {set:couple} on {set:wedding_day}.',
        'Open tasks: {col:team.count}. Overdue: {col:team.overdue}. Share of all open tasks: {col:team.share}.', 'Next task: {col:team.task}, due {col:team.due_date}.'], ['The couple', 'The owner'], NOTE),
    DOC('compressed_page', 'Compressed Timeline Page', 'Compressed timeline', 'compress.task_id', [
        '{set:couple}, dated {today}. Compressed plan for {set:plan_months} months.',
        'Task {col:compress.task_id}: {col:compress.title}. Original due: {col:compress.original_due}. Compressed due: {col:compress.compressed_due}. Lead days: {col:compress.lead_days}. Result: {col:compress.fits}.',
        'Tasks that no longer fit: {col:compress.count_drop}.'], ['The couple', 'Parent'], NOTE),
    DOC('keydates_page', 'Key Dates Page', 'Key dates', 'key.no', [
        '{set:couple}, dated {today}. Key date {col:key.no}: {col:key.item}.',
        'Date: {col:key.date}. Days left: {col:key.days_left}. Source: {col:key.source}. Colour: {col:key.flag}.', 'Open tasks: {col:key.open}. Tasks done: {col:key.done_share}.'], ['The couple', 'Parent'], NOTE),
    DOC('review_page', 'Month Review Page', 'Month review', 'doneby.month', [
        '{set:couple}, dated {today}. Month review for the month starting {col:doneby.month}.',
        'Tasks done: {col:doneby.done}. Tasks due: {col:doneby.due}. Due and still open: {col:doneby.open}.', 'Talk about what slipped and who can help.'], ['The couple'], NOTE),
    DOC('family_page', 'Family Timeline Page', 'Wedding timeline for the family', 'key.no', [
        '{set:couple} are getting married on {set:wedding_day}, in {col:key.days_left} days.',
        'Replies are due by {set:rsvp_deadline}. The final headcount date is {set:headcount_date}. The room block cut-off is {set:room_cutoff}.',
        'So far {col:key.done_share} of the planning tasks are done and {col:key.open} are open. Thank you for your help.'], ['The couple', 'Family'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('set_type', 'Set the wedding date and type', 'tasks', 'tasks.due_date', [('Agree the date or season and pick the wedding type in Settings', -470), ('Check Wedding Types and Task Fit for your type', -465),
        ('Set the headcount date, the reply-by date and the room cut-off in Settings', -460), ('Run the Master Timeline Builder', -455), ('Ask each vendor for its lead time', -450), ('Share the plan with both families', -445)]),
    CHK('m12', '12+ months out', 'tasks', 'tasks.due_date', [('Agree the total budget and who pays what', -440), ('Choose the season, weekday and date range', -430), ('Book the venue and pay the deposit', -420), ('Hire a day-of coordinator or choose helpers', -400),
        ('Book the photographer and the caterer', -390), ('Send save-the-dates to the A list', -370)]),
    CHK('m9', '9 months out', 'tasks', 'tasks.due_date', [('Build the A list and the B list', -300), ('Plan the shower with the hosts', -290), ('Book the cake baker and hair and makeup', -280), ('Order the main outfits', -270), ('Book the florist', -260)]),
    CHK('m6', '6 months out', 'tasks', 'tasks.due_date', [('Send the invitation files to the printer', -190), ('Send the second wave to the B list', -180), ('Chase households that have not replied', -170), ('Book the honeymoon flights', -160), ('Close the reply-by date', -150)]),
    CHK('m3', '3 months out', 'tasks', 'tasks.due_date', [('Attend the menu tasting', -100), ('Draft the run of show with the coordinator', -90), ('Post the invitations that went to the printer', -80), ('Collect meal choices', -75), ('Confirm every vendor arrival time', -65)]),
    CHK('m1', '1 month out', 'tasks', 'tasks.due_date', [('Give the final headcount to the caterer and the venue', -33), ('Pay the final balances due this month', -30), ('Finalise the seating plan', -27), ('Share the run of show with every vendor', -24), ('Prepare labelled tip envelopes', -10)]),
    CHK('final_week', 'Final week', 'tasks', 'tasks.due_date', [('Hold the final wedding party briefing', -7), ('Complete your local marriage paperwork steps', -5), ('Walk through the venue one last time', -4), ('Rehearsal at the venue', -3), ('Rehearsal dinner', -1)]),
    CHK('day_morning', 'Wedding day morning', 'tasks', 'tasks.due_date', [('Check the run of show with the coordinator', -1), ('Hand the tip envelopes to the person who gives them out', 0), ('Confirm each vendor arrival', 0), ('Eat and drink something', 0), ('Collect cards and gifts in one place', 0)]),
    CHK('after', 'After the wedding', 'tasks', 'tasks.due_date', [('Farewell brunch', 1), ('Pay any remaining vendor balance', 2), ('Log every gift and card by household', 3), ('Return the rentals and attire', 5), ('Start the thank-you notes', 10), ('Compare the final budget against actual', 25)]),
    CHK('weekly', 'Weekly planning meeting', 'tasks', 'tasks.due_date', [('Open This Week and the Overdue Tasks sheet', 0), ('Nudge the owners on the Owner Nudge List', 0), ('Check the Next Payments and the Deadline Countdown', 1), ('Update the status of every task you touched', 1), ('Pick the three tasks that matter most this week', 2)]),
    CHK('monthly', 'Monthly review', 'doneby', 'doneby.month', [('Run the Month-out Progress Check', 1), ('Run the Owner Workload Balance and the Delegation Suggester', 2), ('Run the Done Pace Forecast', 3), ('Check the Critical Path Slack', 4), ('Talk about what slipped and who can help', 5)]),
    CHK('small', 'Small wedding short timeline', 'tasks', 'tasks.due_date', [('Pick Small plus a party in Settings', -190), ('Set the date, the budget and the guest list', -180), ('Book the venue and the officiant', -150), ('Book the photographer', -120), ('Check your local marriage paperwork steps', -60),
        ('Confirm everyone and the run of the day', -14), ('Send thank-you notes', 14)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
M = MSG
messages = [
    M('m_week', 'Partner: this week\'s tasks', 'week', 'week.ph_p2', 'Hi, this week we have {count} tasks, overdue ones included. The first is {task}. {couple}'),
    M('m_overdue', 'Partner: tasks are overdue', 'overdue', 'overdue.ph_p2', 'Hi, {count} tasks are overdue. The first is {task}, {days_overdue} days late. {couple}'),
    M('m_critical', 'Partner: the critical task', 'critical', 'critical.ph_p2', 'Hi, the critical task {task} is due on {due_date}. {count} critical tasks are open. {couple}'),
    M('m_share', 'Partner: you hold too many tasks', 'nudge', 'nudge.ph_share', 'Hi, {owner} holds {share} of the open tasks. Can we share some out? {couple}'),
    M('m_deadline', 'Partner: the next deadline', 'deadlines', 'deadlines.ph_p2', 'Hi, the next deadline is {item} in {days_left} days. {couple}'),
    M('m_print', 'Partner: the printer date', 'key', 'key.ph_print', 'Hi, the invitation files must reach the printer by {date}. {couple}'),
    M('m_bucket', 'Partner: done for the bucket', 'week', 'week.ph_p2', 'Hi, we are {bucket_done} done for the {when} bucket. {couple}'),
    M('m_review', 'Partner: review the timeline', 'key', 'key.ph_review', 'Hi, let us review the timeline on {date}. {open} tasks are open. {couple}'),
    M('m_keydate', 'Partner: the next key date', 'key', 'key.ph_next', 'Hi, the key date {item} is on {date}, in {days_left} days. {couple}'),
    M('m_move', 'Partner: moving the date', 'key', 'key.ph_one', 'Hi, moving the date by {move_days} days makes {count_moved} more tasks overdue. {couple}'),
    M('m_pay', 'Partner: a payment is due', 'schedule', 'schedule.ph_pay', 'Hi, the payment of {amount_due} to the {vendor} is due on {due_date}, {days_left} days left. {couple}'),
    M('m_heavy', 'Partner: a heavy week', 'week', 'week.ph_p2', 'Hi, this week is heavy: {count} tasks and {count_pay} payments. {couple}'),
    M('m_compress', 'Partner: the compressed plan', 'compress', 'compress.ph_p2', 'Hi, the compressed plan drops {count_drop} tasks. Shall we check them? {couple}'),
    M('m_days', 'Partner: days to the wedding', 'key', 'key.ph_one', 'Hi, the wedding is in {days_left} days and {open} tasks are open. {couple}'),
    M('m_par1', 'Parent of partner 1: your tasks', 'team', 'team.ph_par1', 'Hello {name}, you have {count} open tasks. The next is {task} by {due_date}. {couple}'),
    M('m_par2', 'Parent of partner 2: your tasks', 'team', 'team.ph_par2', 'Hello {name}, you have {count} open tasks. The next is {task} by {due_date}. {couple}'),
    M('m_takeover', 'Parent: can you take over a task', 'tasks', 'tasks.ph_move', 'Hello, can you take over {title} from {owner}? It is due on {due_date}. {couple}'),
    M('m_wpl', 'Wedding party lead: your tasks', 'team', 'team.ph_wpl', 'Hello {name}, you have {count} open tasks. The next is {task} by {due_date}. {couple}'),
    M('m_wpl_confirm', 'Wedding party lead: confirm a task', 'team', 'team.ph_wpl', 'Hello {name}, please confirm that you can do {task} by {due_date}. {couple}'),
    M('m_wpl_late', 'Wedding party lead: overdue tasks', 'team', 'team.ph_wpl', 'Hello {name}, {overdue} of your {count} open tasks are overdue. Do you need help? {couple}'),
    M('m_friend', 'Close friend helper: can you help', 'team', 'team.ph_friend', 'Hello {name}, can you help with {task} by {due_date}? {couple}'),
    M('m_friend_diy', 'Close friend helper: the DIY date', 'tasks', 'tasks.ph_diy', 'Hello, the next DIY item is {title}, due on {due_date}. Can you help? {couple}'),
    M('m_coord', 'Day-of coordinator: your next task', 'team', 'team.ph_coord', 'Hello {name}, your next task is {task}, due on {due_date}. {couple}'),
    M('m_coord_vendors', 'Day-of coordinator: the vendor list', 'team', 'team.ph_coord', 'Hello {name}, the vendor list for the day is ready. Please check the arrival times. {couple}'),
    M('m_coord_dead', 'Day-of coordinator: the next deadlines', 'deadlines', 'deadlines.ph_coord', 'Hello, the next deadline is {item} on {date}, in {days_left} days. The next ten are on the Deadline Countdown page. {couple}'),
    M('m_printer1', 'Printer: the files are on their way', 'schedule', 'schedule.ph_printer', 'Hello {vendor}, the invitation files are on their way. Please confirm the print date. {couple}'),
    M('m_printer2', 'Printer: posting dates', 'schedule', 'schedule.ph_printer', 'Hello {vendor}, please confirm the posting dates for {quantity} suites. {couple}'),
    M('m_officiant', 'Officiant: confirm the next date', 'tasks', 'tasks.ph_officiant', 'Hello {vendor}, please confirm the date for {title}. We plan it by {due_date}. {couple}'),
    M('m_venue', 'Venue: confirm the next date', 'tasks', 'tasks.ph_venue', 'Hello {vendor}, please confirm the date for {title}. We plan it by {due_date}. {couple}'),
    M('m_hotel', 'Hotel contact: the room cut-off', 'key', 'key.ph_hotel', 'Hello, please confirm the room block cut-off on {date}. {couple}'),
    M('m_caterer', 'Caterer: confirm the next date', 'tasks', 'tasks.ph_caterer', 'Hello {vendor}, please confirm the date for {title}. We plan it by {due_date}. {couple}'),
    M('m_florist', 'Florist: confirm the next date', 'tasks', 'tasks.ph_florist', 'Hello {vendor}, please confirm the date for {title}. We plan it by {due_date}. {couple}'),
    M('m_attire', 'Attire shop: confirm the next date', 'tasks', 'tasks.ph_attire', 'Hello {vendor}, please confirm the date for {title}. We plan it by {due_date}. {couple}'),
    M('m_tailor', 'Tailor: alteration dates', 'tasks', 'tasks.ph_tailor', 'Hello {vendor}, please confirm the alteration dates: {title}, planned by {due_date}. {couple}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def CR(c_): return CNT(TC('owner', OWN[c_]), OPENC)
CRIT_OPEN = CNT(TC('critical', YES), OPENC, TID)
kpis = [
    KPI('Tasks total', ALL_N, 'int'), KPI('Tasks done', DONE_N, 'int'), KPI('Tasks open', OPEN_N, 'int'), KPI('Done share', 'IFERROR(%s/%s,0)' % (DONE_N, ALL_N), 'pct'),
    KPI('Tasks overdue', OVN, 'int', alert={"when": "> 0", "style": "bad"}), KPI('Critical tasks open', CRIT_OPEN, 'int'),
    KPI('Critical tasks overdue', CNT(TC('critical', YES), TC('days_overdue', '">0"')), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Oldest overdue in days', 'MAX(%s)' % R('tasks', 'days_overdue'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Tasks due in the next 7 days', CNT(OPENC, TC('due_date', '">="&{today}'), TC('due_date', '"<="&{today}+7'), TID), 'int'),
    KPI('Tasks due in the rest of this month', CNT(OPENC, TC('due_date', '">="&{today}'), TC('due_date', '"<="&EOMONTH({today},0)'), TID), 'int'),
    KPI('Tasks due in the next 30 days', CNT(OPENC, TC('due_date', '">="&{today}'), TC('due_date', '"<="&{today}+30'), TID), 'int'),
    KPI('Days to the wedding', '{set:wedding_day}-{today}', 'int'), KPI('Weeks to the wedding', 'ROUND(({set:wedding_day}-{today})/7,1)', 'num'),
    KPI('Open tasks per week left', 'ROUND(%s/MAX(1,({set:wedding_day}-{today})/7),1)' % OPEN_N, 'num'),
    KPI('Tasks done in the last 30 days', CNT(TC('done_date', '">="&{today}-30'), TC('done_date', '"<="&{today}'), TID), 'int'),
    KPI('Tasks done so far this month', CNT(TC('done_date', '">="&DATE(YEAR({today}),MONTH({today}),1)'), TC('done_date', '"<="&{today}'), TID), 'int'),
    KPI('Partner 1 open tasks', CR('Partner 1'), 'int'), KPI('Partner 2 open tasks', CR('Partner 2'), 'int'), KPI('Both partners open tasks', CR('Both partners'), 'int'),
    KPI('Family and friends open tasks', '%s-%s-%s-%s' % (OPEN_N, CR('Partner 1'), CR('Partner 2'), CR('Both partners')), 'int'),
    KPI('Largest owner share', 'MAX(%s)' % R('workload', 'share'), 'pct'),
    KPI('Owners over the set share', 'COUNTIFS(%s,">"&{set:owner_share_max})' % R('workload', 'share'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Tasks without an owner', 'COUNTIFS(%s,"",%s)' % (R('tasks', 'owner'), TID), 'int'), KPI('Tasks without a due date', 'COUNTIFS(%s,"",%s)' % (R('tasks', 'due_date'), TID), 'int'),
    KPI('Next deadline in days', 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),"")' % (R('deadlines', 'days_left'), R('deadlines', 'days_left')), 'int'),
    KPI('Deadlines red now', 'COUNTIFS(%s,%s)' % (R('deadlines', 'rag'), V('Red')), 'int', alert={"when": "> 0", "style": "bad"}), KPI('Deadlines amber now', 'COUNTIFS(%s,%s)' % (R('deadlines', 'rag'), V('Amber')), 'int'),
    KPI('Payments due in 14 days, with overdue', 'SUMIFS(%s,%s,"<>"&%s,%s,"<="&{today}+14)' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date')), 'money'),
    KPI('Tasks that no longer fit when compressed', 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (R('compress', 'fits'), V('Do now'), R('compress', 'fits'), V('Drop or merge')), 'int'),
    KPI('Slack to the next critical task, days', 'IFERROR(INDEX(%s,1),"")' % R('critical', 'slack'), 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Wedding Timeline Dashboard", "kpis": kpis,
    "monthly": {"title": "Tasks due and tasks done by month", "date": "doneby.month", "series": [
        {"label": "Tasks due", "sum": "doneby.due", "date": "doneby.month"}, {"label": "Tasks done", "sum": "doneby.done", "date": "doneby.month"}, {"label": "Payments due", "sum": "schedule.amount_due", "date": "schedule.due_date"}]},
    "breakdowns": [{"title": "Open tasks by owner", "by": "workload.owner", "value": "workload.open", "agg": "sum"}, {"title": "Tasks by month-out bucket", "by": "mprog.when", "value": "mprog.tasks", "agg": "sum"},
                   {"title": "Open tasks by area", "by": "areasum.area", "value": "areasum.open", "agg": "sum"}, {"title": "Payments due by status", "by": "schedule.status", "value": "schedule.amount_due", "agg": "sum"}]}


def AG(kind, table, value=None, date=None, label=None, where=None): return AGG(kind, table, value, date, where, label)
OPENW = ('status', '<>', DONE)
insights = {"filters": [{"label": "Owner", "list": "owner"}, {"label": "Area", "list": "area"}, {"label": "Status", "list": "tstatus"}],
    "gauges": [
        {"title": "Tasks done", "num": AG('count', 'tasks', where=[('status', '=', DONE)]), "den": AG('count', 'tasks')},
        {"title": "Critical tasks on time", "num": AG('count', 'tasks', where=[('critical', '=', YES), ('days_overdue', '=', 0)]), "den": AG('count', 'tasks', where=[('critical', '=', YES)])},
        {"title": "Tasks due so far that are done", "num": AG('count', 'tasks', where=[('status', '=', DONE), ('due_date', '<=', '{today}')]), "den": AG('count', 'tasks', where=[('due_date', '<=', '{today}')])},
        {"title": "Owners within the set share", "num": AG('count', 'workload', where=[('share', '<=', '{set:owner_share_max}')]), "den": AG('count', 'workload', where=[('open', '>=', 0)])},
        {"title": "Tasks with an owner and a date", "num": AG('count', 'tasks', where=[('owner_pos', '>', 0), ('due_date', '>', 0)]), "den": AG('count', 'tasks')},
        {"title": "Deadlines not overdue", "num": AG('count', 'deadlines', where=[('days_left', '>=', 0)]), "den": AG('count', 'deadlines', where=[('days_left', '>', -100000)])}],
    "charts": [
        CHART('Tasks by month-out bucket', 'bar', 'tasks.when', [AG('count', 'tasks', label='Tasks')]),
        CHART('Done share by month-out bucket', 'bar', 'mprog.when', [AG('sum', 'mprog', 'mprog.done_share', label='Done share')]),
        CHART('Tasks by status', 'bar', 'tasks.status', [AG('count', 'tasks', label='Tasks')]),
        CHART('Tasks by area', 'bar', 'tasks.area', [AG('count', 'tasks', label='Tasks')]),
        CHART('Tasks by owner', 'bar', 'tasks.owner', [AG('count', 'tasks', label='Tasks')]),
        CHART('Open tasks by owner', 'bar', 'workload.owner', [AG('sum', 'workload', 'workload.open', label='Open tasks')]),
        CHART('Overdue tasks by owner', 'bar', 'tasks.owner', [AG('count', 'tasks', label='Overdue tasks', where=[('days_overdue', '>', 0)])]),
        CHART('Overdue tasks by area', 'bar', 'tasks.area', [AG('count', 'tasks', label='Overdue tasks', where=[('days_overdue', '>', 0)])]),
        CHART('Critical tasks by status', 'bar', 'tasks.status', [AG('count', 'tasks', label='Critical tasks', where=[('critical', '=', YES)])]),
        CHART('Tasks due by month', 'column', 'month', [AG('count', 'tasks', date='tasks.due_date', label='Tasks due')]),
        CHART('Tasks done by month', 'column', 'month', [AG('count', 'tasks', date='tasks.done_date', label='Tasks done')]),
        CHART('Done against due by month', 'column', 'month', [AG('sum', 'doneby', 'doneby.done', date='doneby.month', label='Done'), AG('sum', 'doneby', 'doneby.due', date='doneby.month', label='Due')]),
        CHART('Critical and other tasks by bucket', 'bar', 'tasks.when', [AG('count', 'tasks', label='Critical', where=[('critical', '=', YES)]), AG('count', 'tasks', label='Other', where=[('critical', '=', NO)])]),
        CHART('Done tasks by area', 'bar', 'tasks.area', [AG('count', 'tasks', label='Done tasks', where=[('status', '=', DONE)])]),
        CHART('Workload share by owner', 'bar', 'workload.owner', [AG('sum', 'workload', 'workload.share', label='Share of open tasks')]),
        CHART('Payments due by month', 'column', 'month', [AG('sum', 'schedule', 'schedule.amount_due', date='schedule.due_date', label='Payments due')]),
        CHART('Contract dates by month', 'column', 'month', [AG('count', 'contracts', date='contracts.item_date', label='Contract dates')]),
        CHART('Fittings by month', 'column', 'month', [AG('count', 'party', date='party.fitting_date', label='Fittings')]),
        CHART('Open critical tasks by owner', 'bar', 'tasks.owner', [AG('count', 'tasks', label='Open critical tasks', where=[('critical', '=', YES), ('status', '<>', DONE)])]),
        CHART('Payments by status', 'bar', 'schedule.status', [AG('sum', 'schedule', 'schedule.amount_due', label='Amount due')]),
        CHART('Contract items by kind', 'bar', 'contracts.kind', [AG('count', 'contracts', label='Items')]),
        CHART('Open tasks by month-out bucket', 'bar', 'tasks.when', [AG('count', 'tasks', label='Open tasks', where=[('status', '<>', DONE)])])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Master timeline builder", "why": "every task dated from the wedding day for your wedding type, with the tasks that do not apply counted as hidden", "where": "Master Timeline Builder"},
    {"name": "Compressed mode re-dater", "why": "less than 12 months: tasks re-dated in proportion and the ones that no longer leave their lead time named", "where": "Compressed Mode Re-dater"},
    {"name": "Invitation print slip", "why": "counts back from the reply-by date to the latest day the files can reach the printer", "where": "Invitation Print Slip"},
    {"name": "Critical path slack", "why": "the days between each critical task and the next, so you see which late task moves the wedding", "where": "Critical Path Slack"},
    {"name": "Owner workload balance", "why": "open tasks by owner against the most one person should hold, with a warning and the owner named", "where": "Owner Workload Balance"},
    {"name": "Delegation suggester", "why": "moves the first task that is not critical from the heaviest owner to the usual helper of its area", "where": "Delegation Suggester"},
    {"name": "Deadline countdown", "why": "the next dates from payments, replies, headcount, room cut-off, vendor cut-offs and fittings, red, amber or green", "where": "Deadline Countdown"},
    {"name": "Date change impact", "why": "move the wedding date and see which dates shift and which tasks become overdue", "where": "Date Change Impact"},
    {"name": "Lead-time check", "why": "each open task against the typical lead time of its area, naming the task that started too late", "where": "Lead-time Check"},
    {"name": "Done pace forecast", "why": "open tasks divided by your pace gives a finish date and how many days before the wedding it falls", "where": "Done Pace Forecast"}]
competitors = [
    {"what": "a free planning app", "lacks": "has a checklist but no critical path, no slack between tasks, no compressed plan and no check of who holds too many tasks"},
    {"what": "a single budget spreadsheet", "lacks": "tracks money only, with no task owners, no deadline countdown and no month-out progress"},
    {"what": "a printable wedding binder", "lacks": "has blank month-by-month pages but does no sums, no overdue ranking and no date change impact"},
    {"what": "a wedding website with a registry", "lacks": "shares your plans with a company and has no compressed mode, no workload balance and no private deadline list"}]
guide = [
    'Open Start here and type your names, the wedding day, the reply-by date, the headcount date and the room cut-off in the yellow cells. Replace demo data: clear the sample rows and type your own.',
    'Pick your wedding type in Settings. Wedding Types and Task Fit say which task areas apply; a small wedding hides the areas marked no.',
    'Enter every task in Tasks with its area, month-out bucket, due date, owner, status and a critical flag. Days left, the flag and the overdue rank fill in by themselves.',
    'Check Overdue Tasks, This Week and This Month every week, and use the Owner Nudge List to see who to call.',
    'Critical Path shows the open critical tasks in date order with the slack between them. Workload by Owner shows who holds how much; the Delegation Suggester names a task to hand over.',
    'Key Dates and Deadlines across Wedding pull the next dates from your payments, contract items and wedding party; paste your own copies into Payment Schedule, Contract Items and Wedding Party.',
    'Starting late? Set the months you have in Settings and read the Compressed Plan, then the Compressed Mode Re-dater tool.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A couple with a small wedding (30 guests, no wedding party) uses the same sheets with fewer rows: pick Small plus a party and hide the areas that do not apply.',
    'This workbook has no macros and works in Excel and Google Sheets. Print any page for a parent or a helper.',
    'Why a workbook: one flat price, no vendor ever sees your details, no fees, your own numbers, and it works offline.',
    'What this is not: not a booking service, not a payment service, and not legal, tax or insurance advice. Every default is a typical starting value you can edit, never a promise. Check your contract for every vendor date.']
listing = {"title": "Wedding Planning Checklist Excel Template: Timeline by Month, Task Owners, Critical Path, Deadline Countdown, Compressed Plan",
    "headline": "Every wedding task dated, owned and counted down to the day",
    "tags": ["wedding checklist", "wedding timeline", "wedding planner", "task owners", "critical path", "deadline countdown", "wedding spreadsheet", "excel template", "month by month", "small wedding", "day of timeline", "delegation", "wedding to do"],
    "description": ("Run the plan of your wedding in one Excel workbook. Built for an engaged couple planning their own wedding, with a partner, parents, a wedding party lead or a day-of coordinator who gets a printed page.\n\n"
        "Tasks holds the master checklist: every task with a month-out bucket, an owner, a status and a critical flag, with days left, an overdue rank and the months before the wedding filled in. Wedding Types and Task Fit date the plan for a local, destination, small plus a party, multi-event or home wedding, "
        "and a small wedding hides the areas that do not apply. Starting with less than twelve months? The Compressed Plan re-dates every task in proportion and names the ones that no longer fit.\n\n"
        "Overdue Tasks, This Week and This Month list what to do next, the Critical Path shows the slack between critical tasks, and Workload by Owner warns when one person holds too much. Key Dates and Deadlines across Wedding pull the next dates from your payments, contract items and wedding party, red, amber or green on the days you set.\n\n"
        f"{len(tools)} tools answer weekly questions: is the timeline right for our type, when must the invitation files reach the printer, which overdue task first, who do we nudge, who should take a task, can we do this week's tasks, what if the date moves and when will we finish. Print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and send {len(messages)} ready text messages to your partner, parents, helpers and vendors.\n\n"
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Every default is a typical starting value you can edit, and forecasts are your own estimate. It is not a booking service, not a payment service and not legal, tax or insurance advice. This is part four of the Wedding Planning suite."),
    "features": ["Master checklist by month-out with owners", "Timeline dated for five wedding types", "Compressed plan for couples with less than 12 months", "Critical path with slack between tasks", "Workload by owner with a warning",
                 "Delegation suggester", "Deadline countdown in red, amber and green", "Invitation print slip", "Date change impact", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} pages",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}

def _cut(h):
    if len(h) <= 200: return h
    h = h[:197]
    i = max(h.rfind(';'), h.rfind(','), h.rfind(' '))
    return h[:i].rstrip(' ,;') + '.'
for _x in tables + tools: _x['hint'] = _cut(_x['hint'])
lists = BASE_LISTS + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p4', slug='wedding-timeline', profession='Wedding Planning', name='Master Timeline and Task Owners',
         tagline='Wedding checklist by month, task owners, critical path and deadlines', price_usd=29,
         colors={"primary": "#7A4B68", "accent": "#D9A86C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 4, "of": 8, "focus": "Master timeline, checklist and task owners"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wp4.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']), 'tag', len(s['tagline']), 'words', [len(x) for x in (_VW['va'], _VW['vb'], _VW['vc'])])
