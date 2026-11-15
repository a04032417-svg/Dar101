"""Childcare center suite part 7: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc7_lists import *
import cc7_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def RG(t, c): return '{range:%s.%s}' % (t, c)
ENR, LEFT = tok('cstatus', 'Enrolled'), tok('cstatus', 'Left')
REPL, AWAIT = tok('mstatus', 'Replied'), tok('mstatus', 'Awaiting reply')
HELD, BOOKED, NOSHOW = tok('confstatus', 'Held'), tok('confstatus', 'Booked'), tok('confstatus', 'No-show')
NEWS, OPENDAY, FAMEV, MEETW = tok('ekind', 'Newsletter'), tok('ekind', 'Open day'), tok('ekind', 'Family event'), tok('ekind', 'Family meeting week')
PORT = tok('okind', 'Portfolio entry')
BAS, SUMMER, HOLIDAY = tok('program', 'Before-after school'), tok('program', 'Summer camp'), tok('program', 'Holiday camp')
CV_RUN, CV_MIN, CV_CANCEL = tok('campverdict', 'Run'), tok('campverdict', 'Run with a minimum'), tok('campverdict', 'Cancel')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
LAST30 = '">"&({today}-30)'


def PHONE_BY(col, lst, mp, default):
    """a constant phone number chosen by the list value in a column (digits and plus signs only)"""
    f = '"%s"' % default
    for name in reversed(list(mp)): f = 'IF({col:%s}=%s,"%s",%s)' % (col, tok(lst, name), mp[name], f)
    return f
def PHONE_BY_ROOM(col, mp, default): return PHONE_BY(col, 'room', mp, default)
def TEACHER_OF(col):
    f = '""'
    for r in reversed(ROOMS): f = 'IF({col:%s}=%s,%s,%s)' % (col, tok('room', r), tok('teacher', RM_LEAD[r]), f)
    return f

settings = [
    S('company', 'Your center name', 'text', COMPANY), S('reply_hours_target', 'Hours to reply to a parent message', 'int', 24),
    S('same_day_target', 'Share of daily reports sent the same day, your target', 'pct', 0.90), S('term_start', 'First day of the current term', 'date', iso(TERM_START) if not isinstance(TERM_START, str) else TERM_START),
    S('obs_per_term', 'Observation or portfolio entries each child needs in a term', 'int', 2), S('contact_days', 'Days without contact that start a call to a family', 'int', 180),
    S('ratio_schoolage', 'Camp children per staff member, check your local rules', 'int', 12), S('camp_hours_day', 'Camp staff hours a day', 'int', 8),
    S('camp_staff_rate', 'Camp staff cost an hour, with employer costs', 'money', 23.65), S('run_margin', 'Sign-ups above break-even to run without a minimum', 'int', 1),
    S('event_attend_target', 'Wanted attendance share at an event', 'pct', 0.60), S('prep_days', 'Days before a newsletter or event to start preparing', 'int', 14),
    S('leaver_months', 'Months of leavers the analysis looks at', 'int', 12), S('pulse_change', 'Change in the family pulse score that counts as a move', 'num', 0.15),
]
assert 3 <= len(settings) <= 20

tables = []

# 1 daily reports
tables.append(T('reports', 'Daily Reports', 'Daily reports sent by room and teacher',
    'One row per room and day: the teacher, the time the daily report was sent and whether it went the same day; the week, the month and the share sent the same day fill in for the charts.', [
    C('report_id', 'Report ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), LST('room', 'Room', 'room', 12), LST('staff', 'Teacher', 'teacher', 18), C('sent_time', 'Sent at', 'time', 9),
    C('same_day', 'Same day', 'bool', 9), C('sent_next_day', 'Sent next day', 'bool', 11),
    CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('same_n', 'Sent same day', 'int', 'IF({col:same_day}=%s,1,0)' % YES, 9), CA('next_n', 'Sent next day count', 'int', 'IF({col:sent_next_day}=%s,1,0)' % YES, 10),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18)],
    D.reports_d(), 3000, [A('sent_next_day', '= ' + YES, 'warn')]))

# 2 parent messages
tables.append(T('parent_msgs', 'Parent Messages', 'Parent messages with topic and reply time',
    'One row per family message: topic, status and reply hours; the family phone, hours waiting and reply-by date fill in. Status only, never the content.', [
    C('message_id', 'Message ID', 'text', 10, required=True), C('date', 'Date', 'date', 12), C('replied_on', 'Replied on', 'date', 12), REF('family', 'Family', 'families.family', 20), LST('topic', 'Topic', 'topic', 14),
    LST('status', 'Status', 'mstatus', 15), C('reply_hours', 'Reply hours', 'int', 9),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18),
    CA('room', 'Room', 'text', LKT('families.room', 'families.family', 'family'), 12),
    CA('wait_hours', 'Hours waiting', 'int', 'IF({col:status}=%s,({today}-{col:date})*24,"")' % AWAIT, 10),
    CA('within_n', 'Replied in time', 'int', 'IF(AND({col:status}=%s,{col:reply_hours}<={set:reply_hours_target}),1,0)' % REPL, 10),
    CA('reply_due', 'Reply by', 'date', '{col:date}+ROUNDUP({set:reply_hours_target}/24,0)', 12),
    CA('handled_by', 'Handled by', 'text', 'IF(OR({col:topic}=%s,{col:topic}=%s),%s,%s)' % (tok('topic', 'Billing'), tok('topic', 'Schedule'), tok('person', ASSISTANT_DIRECTOR), tok('person', OWNER)), 16),
    CA('topic_avg90', 'Topic average reply hours, 90 days', 'num', 'IFERROR(AVERAGEIFS(%s,%s,{col:topic},%s,%s,%s,">"&({today}-90)),0)' % (RG('parent_msgs', 'reply_hours'), RG('parent_msgs', 'topic'), RG('parent_msgs', 'status'), REPL, RG('parent_msgs', 'date')), 12),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('ad_phone', 'Assistant director phone', 'text', '"%s"' % D.AD_PHONE, 18),
    CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)],
    D.parent_msgs_d(), 600, [A('status', '= ' + AWAIT, 'warn'), A('reply_hours', '> {set:reply_hours_target}', 'bad')]))

# 3 families
FAMC = '{col:family}'
tables.append(T('families', 'Families', 'Families with contact and conference status',
    'One row per family: contact details and the room of an enrolled child; the last contact, the booked conference and the next event, newsletter and camp week fill in for the messages.', [
    C('family_id', 'Family ID', 'text', 10, required=True), C('family', 'Family', 'text', 22), C('guardian', 'Parent or guardian', 'text', 22), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    LST('cycle', 'Billing cycle', 'cycle', 11), LST('room', 'Room', 'room', 12), C('children', 'Children', 'int', 9), C('first_start', 'First start', 'date', 12),
    CA('enrolled_kids', 'Children enrolled now', 'int', 'COUNTIFS(%s,{col:family_id},%s,%s)' % (RG('children', 'family_id'), RG('children', 'status'), ENR), 10),
    CA('last_msg', 'Last message', 'date', 'SUMPRODUCT(MAX((%s=%s)*%s))' % (RG('parent_msgs', 'family'), FAMC, RG('parent_msgs', 'date')), 12),
    CA('last_conf', 'Last conference held', 'date', 'SUMPRODUCT(MAX((%s=%s)*(%s=%s)*%s))' % (RG('conferences', 'family'), FAMC, RG('conferences', 'status'), HELD, RG('conferences', 'date')), 12),
    CA('last_contact', 'Last contact', 'date', 'MAX({col:last_msg},{col:last_conf},{col:first_start})', 12),
    CA('conf_booked', 'Conferences booked', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (RG('conferences', 'family'), FAMC, RG('conferences', 'status'), BOOKED), 10),
    CA('conf_held', 'Conferences held', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (RG('conferences', 'family'), FAMC, RG('conferences', 'status'), HELD), 10),
    CA('conf_noshow', 'Conference no-shows', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (RG('conferences', 'family'), FAMC, RG('conferences', 'status'), NOSHOW), 10),
    CA('next_event_date', 'Next event', 'date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<="&{today})+1),"")' % (RG('events', 'fam_date'), RG('events', 'fam_date')), 12),
    CA('next_event', 'Next event kind', 'text', 'IF({col:next_event_date}="","",IFERROR(INDEX(%s,MATCH({col:next_event_date},%s,0))&"",""))' % (RG('events', 'kind'), RG('events', 'fam_date')), 18),
    CA('last_event_date', 'Last event', 'date', 'IFERROR(LARGE(%s,COUNTIF(%s,">"&{today})+1),"")' % (RG('events', 'fam_date'), RG('events', 'fam_date')), 12),
    CA('last_event', 'Last event kind', 'text', 'IF({col:last_event_date}="","",IFERROR(INDEX(%s,MATCH({col:last_event_date},%s,0))&"",""))' % (RG('events', 'kind'), RG('events', 'fam_date')), 18),
    CA('news_date', 'Next newsletter', 'date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (RG('newsletter_plan', 'news_date'), RG('newsletter_plan', 'news_date')), 12),
    CA('next_conf_week', 'Next conference week', 'date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<="&{today})+1)-WEEKDAY(SMALL(%s,COUNTIF(%s,"<="&{today})+1),2)+1,"")' % (
        RG('conferences', 'date'), RG('conferences', 'date'), RG('conferences', 'date'), RG('conferences', 'date')), 12),
    CA('next_camp_week', 'Next camp week', 'date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<="&{today})+1),"")' % (RG('camp_cal', 'week'), RG('camp_cal', 'week')), 12),
    CA('next_camp_program', 'Next camp program', 'text', 'IF({col:next_camp_week}="","",IFERROR(INDEX(%s,MATCH({col:next_camp_week},%s,0))&"",""))' % (RG('camp_cal', 'program'), RG('camp_cal', 'week')), 18)],
    D.families_d(), 150, [A('conf_noshow', '> 0', 'warn')]))

# 4 children
tables.append(T('children', 'Children', 'Children with room, status and dates',
    'One row per child, current and past: room, schedule, status and dates, the weekly tuition and the leaving reason when a child has left. Names, rooms and dates only, never health detail.', [
    C('child_id', 'Child ID', 'text', 9, required=True), C('child', 'Child', 'text', 24), C('family', 'Family', 'text', 20), C('family_id', 'Family ID', 'text', 10), LST('room', 'Room', 'room', 12),
    LST('schedule', 'Schedule', 'schedule', 13), LST('status', 'Status', 'cstatus', 13), C('start_date', 'Start date', 'date', 12), C('end_date', 'End date', 'date', 12),
    LST('leave_reason', 'Leaving reason', 'leavereason', 14), C('weekly_fee', 'Weekly tuition', 'money', 12), C('guardian', 'Parent or guardian', 'text', 22), C('phone', 'Phone', 'text', 18),
    CA('months_stayed', 'Months with us', 'int', 'IFERROR(DATEDIF({col:start_date},IF({col:end_date}="",{today},{col:end_date}),"M"),0)', 10)],
    D.children_d(), 150, [A('status', '= ' + LEFT, 'bad'), A('status', '= ' + ENR, 'good')]))

# 5 conferences
tables.append(T('conferences', 'Conferences', 'Conferences by family and slot',
    'One row per conference slot: family, child, teacher and time, with status held, booked or no-show; the family phone and days to go fill in. Status only.', [
    C('conference_id', 'Conference ID', 'text', 11, required=True), C('date', 'Date', 'date', 12), REF('family', 'Family', 'families.family', 20), REF('child', 'Child', 'children.child', 22),
    LST('staff', 'Teacher', 'teacher', 18), LST('status', 'Status', 'confstatus', 11), C('slot', 'Slot', 'time', 9),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18),
    CA('days_to', 'Days to go', 'int', 'IF({col:status}=%s,{col:date}-{today},"")' % BOOKED, 9), CA('noshow_n', 'No-show', 'int', 'IF({col:status}=%s,1,0)' % NOSHOW, 9),
    CA('slot_key', 'Slot key', 'text', '{col:staff}&"|"&{col:date}&"|"&ROUND({col:slot}*1440,0)', 16),
    CA('staff_phone', 'Teacher phone', 'text', PHONE_BY('staff', 'teacher', D.STAFF_PHONE, D.OWNER_PHONE), 18)],
    D.conferences_d(), 400, [A('status', '= ' + NOSHOW, 'bad'), A('status', '= ' + BOOKED, 'warn')]))

# 6 events
tables.append(T('events', 'Events', 'Events and newsletters with attendance',
    'One row per event or newsletter: the kind, the families invited and the families who came; the attendance share and whether it is held or planned fill in.', [
    C('event_id', 'Event ID', 'text', 9, required=True), C('date', 'Date', 'date', 12), LST('kind', 'Kind', 'ekind', 20), C('room', 'Room', 'text', 12), C('invited', 'Invited', 'int', 9), C('attended', 'Attended', 'int', 9),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('share', 'Attendance share', 'pct', 'IF(AND({col:date}<={today},{col:invited}>0),{col:attended}/{col:invited},"")', 11),
    CA('when', 'Held or planned', 'text', 'IF({col:date}<={today},%s,%s)' % (fl('Held'), fl('Planned')), 12),
    CA('fam_date', 'Event date, not newsletters', 'date', 'IF({col:kind}<>%s,{col:date},"")' % NEWS, 12), CA('ad_phone', 'Assistant director phone', 'text', '"%s"' % D.AD_PHONE, 18)],
    D.events_d(), 80, [A('when', '= ' + fl('Planned'), 'warn')]))

# 7 observations
tables.append(T('observations', 'Observations', 'Observation and portfolio entries by child',
    'One row per entry: the date, child, room, teacher and kind, observation or portfolio entry. Counts and dates only, never the content of an entry.', [
    C('obs_id', 'Entry ID', 'text', 9, required=True), C('date', 'Date', 'date', 12), REF('child', 'Child', 'children.child', 22), LST('room', 'Room', 'room', 12), LST('staff', 'Teacher', 'teacher', 18), LST('kind', 'Kind', 'okind', 14),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('in_term', 'In this term', 'int', 'IF(AND({col:date}>={set:term_start},{col:date}<={today}),1,0)', 9)],
    D.observations_d(), 1500, []))

# 8 observation status by child
tables.append(T('obs_status', 'Observation Status', 'Observation status by child this term',
    'One row per enrolled child: type the child ID; the entries this term, the last entry date, the entries still to do and the flag fill in from the Observations sheet. Counts and dates only.', [
    C('child_id', 'Child ID', 'text', 9, required=True),
    CA('child', 'Child', 'text', LKT('children.child', 'children.child_id', 'child_id'), 22), CA('room', 'Room', 'text', LKT('children.room', 'children.child_id', 'child_id'), 12),
    CA('teacher', 'Teacher', 'text', TEACHER_OF('room'), 18),
    CA('entries_term', 'Entries this term', 'int', 'COUNTIFS(%s,{col:child},%s,1)' % (RG('observations', 'child'), RG('observations', 'in_term')), 10),
    CA('portfolio_n', 'Portfolio entries this term', 'int', 'COUNTIFS(%s,{col:child},%s,1,%s,%s)' % (RG('observations', 'child'), RG('observations', 'in_term'), RG('observations', 'kind'), PORT), 11),
    CA('entries_all', 'Entries in total', 'int', 'COUNTIFS(%s,{col:child})' % RG('observations', 'child'), 9),
    CA('last_entry', 'Last entry', 'date', 'IF({col:entries_all}=0,"",SUMPRODUCT(MAX((%s={col:child})*%s)))' % (RG('observations', 'child'), RG('observations', 'date')), 12),
    CA('days_since', 'Days since the last entry', 'int', 'IF({col:last_entry}="","",{today}-{col:last_entry})', 10),
    CA('todo', 'Entries still to do', 'int', 'MAX(0,{set:obs_per_term}-{col:entries_term})', 9),
    CA('flag', 'Entry check', 'text', 'IF({col:entries_term}=0,%s,IF({col:entries_term}<{set:obs_per_term},%s,%s))' % (fl('No entry this term'), fl('Below target'), fl('Up to date')), 18),
    CA('teacher_todo', 'Entries to do by this teacher', 'int', 'SUMIFS(%s,%s,{col:teacher})' % (RG('obs_status', 'todo'), RG('obs_status', 'teacher')), 11),
    CA('teacher_phone', 'Teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18), CA('assistant_phone', 'Assistant phone', 'text', PHONE_BY_ROOM('room', D.ASSIST_PHONE, D.OWNER_PHONE), 18)],
    D.obs_status_d(), 100, [A('flag', '= ' + fl('No entry this term'), 'bad'), A('flag', '= ' + fl('Below target'), 'warn'), A('flag', '= ' + fl('Up to date'), 'good')]))

# 9 program weeks
tables.append(T('program_weeks', 'Program Weeks', 'Program weeks with places, sign-ups and staff cost',
    'One row per program and week: places, sign-ups, open days, price a day, revenue and staff cost; the fill, the profit, the break-even sign-ups and the run or cancel decision fill in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), C('month', 'Month', 'date', 11), LST('program', 'Program', 'program', 19), C('places', 'Places', 'int', 8), C('signups', 'Sign-ups', 'int', 9),
    C('days', 'Open days', 'int', 9), C('price_day', 'Price a day', 'money', 11), C('revenue', 'Revenue', 'money', 11), C('staff_cost', 'Staff cost', 'money', 11),
    CA('fill', 'Fill', 'pct', 'IF({col:places}>0,{col:signups}/{col:places},0)', 8), CA('profit', 'Profit', 'money', '{col:revenue}-{col:staff_cost}', 11),
    CA('break_even', 'Break-even sign-ups', 'int', 'IF({col:price_day}*{col:days}>0,ROUNDUP({col:staff_cost}/({col:price_day}*{col:days}),0),0)', 11),
    CA('gap', 'Sign-ups against break-even', 'int', '{col:signups}-{col:break_even}', 11),
    CA('verdict', 'Decision', 'text', 'IF({col:signups}>={col:break_even}+{set:run_margin},%s,IF({col:signups}>={col:break_even},%s,%s))' % (CV_RUN, CV_MIN, CV_CANCEL), 18),
    CA('wk_key', 'Week key', 'text', '{col:week}&"|"&{col:program}', 18), CA('floater_phone', 'Floater phone', 'text', '"%s"' % D.FLOAT_PHONE, 18)],
    D.program_weeks_d(), 250, [A('verdict', '= ' + CV_CANCEL, 'bad'), A('verdict', '= ' + CV_MIN, 'warn'), A('verdict', '= ' + CV_RUN, 'good')]))

# 10 program sign-ups
tables.append(T('program_signups', 'Program Sign-ups', 'Camp sign-ups by child and week',
    'One row per child and camp week: the days and the price a day; the family, the phone, the number of children that week and the decision for that week fill in.', [
    C('signup_id', 'Sign-up ID', 'text', 10, required=True), C('week', 'Week (Monday)', 'date', 12), LST('program', 'Program', 'campprog', 19), REF('child', 'Child', 'children.child', 22), C('days', 'Days', 'int', 7),
    C('price_day', 'Price a day', 'money', 11), C('fee', 'Fee', 'money', 10),
    CA('family', 'Family', 'text', LKT('children.family', 'children.child', 'child'), 20), CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child', 'child'), 18),
    CA('wk_key', 'Week key', 'text', '{col:week}&"|"&{col:program}', 18),
    CA('signups_n', 'Children that week', 'int', 'SUMIFS(%s,%s,{col:week},%s,{col:program})' % (RG('program_weeks', 'signups'), RG('program_weeks', 'week'), RG('program_weeks', 'program')), 10),
    CA('break_even', 'Break-even sign-ups', 'int', 'SUMIFS(%s,%s,{col:week},%s,{col:program})' % (RG('program_weeks', 'break_even'), RG('program_weeks', 'week'), RG('program_weeks', 'program')), 10),
    CA('verdict', 'Decision for the week', 'text', 'IFERROR(INDEX(%s,MATCH({col:wk_key},%s,0))&"","")' % (RG('program_weeks', 'verdict'), RG('program_weeks', 'wk_key')), 18)],
    D.program_signups_d(), 250, [A('verdict', '= ' + CV_CANCEL, 'bad'), A('verdict', '= ' + CV_MIN, 'warn')]))

# 11 programs
tables.append(T('programs', 'Programs', 'Programs with places and price a day',
    'The three programs: the places and the price a day. The camp weeks, the break-even and the tools read them.', [
    C('program', 'Program', 'text', 24, required=True), C('places', 'Places', 'int', 9), C('price_day', 'Price a day', 'money', 12)], D.programs_d(), 50))

# 12 camp calendar
CAL_UNIT = '{col:price_day}*{col:days}'
tables.append(T('camp_cal', 'Camp Calendar', 'Camp calendar with break-even and decision',
    'One row per camp week: type the week and program; places, sign-ups, staff cost, break-even sign-ups and the decision run, run with a minimum or cancel fill in.', [
    C('cal_id', 'Week ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), LST('program', 'Program', 'campprog', 19),
    CA('places', 'Places', 'int', 'SUMIFS(%s,%s,{col:program})' % (RG('programs', 'places'), RG('programs', 'program')), 8),
    CA('signups', 'Sign-ups', 'int', 'SUMIFS(%s,%s,{col:week},%s,{col:program})' % (RG('program_weeks', 'signups'), RG('program_weeks', 'week'), RG('program_weeks', 'program')), 9),
    CA('days', 'Open days', 'int', 'SUMIFS(%s,%s,{col:week},%s,{col:program})' % (RG('program_weeks', 'days'), RG('program_weeks', 'week'), RG('program_weeks', 'program')), 9),
    CA('price_day', 'Price a day', 'money', 'IF(SUMIFS(%s,%s,{col:week},%s,{col:program})>0,SUMIFS(%s,%s,{col:week},%s,{col:program}),SUMIFS(%s,%s,{col:program}))' % (
        RG('program_weeks', 'price_day'), RG('program_weeks', 'week'), RG('program_weeks', 'program'), RG('program_weeks', 'price_day'), RG('program_weeks', 'week'), RG('program_weeks', 'program'),
        RG('programs', 'price_day'), RG('programs', 'program')), 11),
    CA('revenue', 'Revenue', 'money', '{col:signups}*%s' % CAL_UNIT, 11),
    CA('staff_n', 'Staff needed', 'int', 'MAX(1,ROUNDUP({col:signups}/{set:ratio_schoolage},0))', 9),
    CA('one_staff', 'Cost of one staff member', 'money', '{set:camp_hours_day}*{col:days}*{set:camp_staff_rate}', 12),
    CA('staff_cost', 'Staff cost', 'money', '{col:staff_n}*{col:one_staff}', 11),
    CA('break_even', 'Break-even sign-ups', 'int', 'IF(%s<=0,0,IF(ROUNDUP({col:one_staff}/(%s),0)<={set:ratio_schoolage},ROUNDUP({col:one_staff}/(%s),0),IF(ROUNDUP(2*{col:one_staff}/(%s),0)<=2*{set:ratio_schoolage},ROUNDUP(2*{col:one_staff}/(%s),0),ROUNDUP(3*{col:one_staff}/(%s),0))))' % (
        CAL_UNIT, CAL_UNIT, CAL_UNIT, CAL_UNIT, CAL_UNIT, CAL_UNIT), 11),
    CA('gap', 'Sign-ups against break-even', 'int', '{col:signups}-{col:break_even}', 11), CA('profit', 'Profit', 'money', '{col:revenue}-{col:staff_cost}', 11),
    CA('fill', 'Fill', 'pct', 'IF({col:places}>0,{col:signups}/{col:places},0)', 8),
    CA('verdict', 'Decision', 'text', 'IF({col:signups}>={col:break_even}+{set:run_margin},%s,IF({col:signups}>={col:break_even},%s,%s))' % (CV_RUN, CV_MIN, CV_CANCEL), 18),
    CA('rank_score', 'Ranking score', 'num', 'IF({col:week}<={today},{col:profit}+{col:week}/10000000,"")', 11),
    CA('floater_phone', 'Floater phone', 'text', '"%s"' % D.FLOAT_PHONE, 18), CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)],
    D.camp_cal_d(), 60, [A('verdict', '= ' + CV_CANCEL, 'bad'), A('verdict', '= ' + CV_MIN, 'warn'), A('verdict', '= ' + CV_RUN, 'good')]))

# 13 communication gaps
tables.append(T('comm_gaps', 'Communication Gaps', 'Communication gaps by family',
    'One row per family: type the family ID; the last daily report of the room, the last reply, messages waiting and days since contact fill in, with a flag when a family needs a call. Status only.', [
    C('family_id', 'Family ID', 'text', 10, required=True),
    CA('family', 'Family', 'text', LKT('families.family', 'families.family_id', 'family_id'), 22), CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family_id', 'family_id'), 18),
    CA('room', 'Room', 'text', LKT('families.room', 'families.family_id', 'family_id'), 12), CA('enrolled', 'Children enrolled', 'int', LKN('families.enrolled_kids', 'families.family_id', 'family_id'), 10),
    CA('last_report', 'Last daily report', 'date', 'IF(OR({col:room}="",{col:enrolled}=0),"",SUMPRODUCT(MAX((%s={col:room})*%s)))' % (RG('reports', 'room'), RG('reports', 'date')), 12),
    CA('last_reply', 'Last reply', 'date', 'IF({col:enrolled}=0,"",IF(SUMPRODUCT(MAX((%s={col:family})*(%s=%s)*%s))=0,"",SUMPRODUCT(MAX((%s={col:family})*(%s=%s)*%s))))' % (
        RG('parent_msgs', 'family'), RG('parent_msgs', 'status'), REPL, RG('parent_msgs', 'replied_on'), RG('parent_msgs', 'family'), RG('parent_msgs', 'status'), REPL, RG('parent_msgs', 'replied_on')), 12),
    CA('waiting', 'Messages waiting', 'int', 'COUNTIFS(%s,{col:family},%s,%s)' % (RG('parent_msgs', 'family'), RG('parent_msgs', 'status'), AWAIT), 9),
    CA('last_contact', 'Last contact', 'date', LKN('families.last_contact', 'families.family_id', 'family_id'), 12),
    CA('days_since', 'Days since contact', 'int', 'IF({col:enrolled}=0,"",{today}-{col:last_contact})', 10),
    CA('flag', 'Contact check', 'text', 'IF({col:enrolled}=0,%s,IF({col:waiting}>0,%s,IF({col:days_since}>{set:contact_days},%s,%s)))' % (fl('Not enrolled'), fl('Reply waiting'), fl('Call this family'), fl('Recent contact')), 16),
    CA('gap_score', 'Ranking score', 'num', 'IF({col:enrolled}=0,"",{col:days_since}+(1000-MATCH({col:family_id},%s,0))/100000)' % RG('comm_gaps', 'family_id'), 10),
    CA('ad_phone', 'Assistant director phone', 'text', '"%s"' % D.AD_PHONE, 18)],
    D.comm_gaps_d(), 150, [A('flag', '= ' + fl('Call this family'), 'bad'), A('flag', '= ' + fl('Reply waiting'), 'warn'), A('flag', '= ' + fl('Recent contact'), 'good')]))

# 14 reply time by topic
tables.append(T('reply_topic', 'Reply Time by Topic', 'Reply time by topic',
    'One row per message topic: the number of messages and the average hours the reply took, calculated from the Parent Messages sheet.', [
    C('topic', 'Topic', 'text', 20, required=True),
    CA('messages', 'Messages', 'int', 'COUNTIFS(%s,{col:topic})' % RG('parent_msgs', 'topic'), 10),
    CA('avg_hours', 'Average reply hours', 'num', 'IFERROR(AVERAGEIFS(%s,%s,{col:topic},%s,%s),0)' % (RG('parent_msgs', 'reply_hours'), RG('parent_msgs', 'topic'), RG('parent_msgs', 'status'), REPL), 12)],
    D.reply_topic_d(), 50))

# 15 newsletter and event plan
M3 = '{col:month}+MOD(8-WEEKDAY({col:month},2),7)+14'
tables.append(T('newsletter_plan', 'Newsletter and Event Plan', 'Newsletter and event plan for the next 12 months',
    'One row per month: type the month and the owner; the newsletter date, the event, the conference week and the date to start preparing fill in from your calendar rules.', [
    C('plan_id', 'Plan ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('owner', 'Owner', 'role', 18),
    CA('news_date', 'Newsletter goes out', 'date', 'WORKDAY(DATE(YEAR({col:month}),MONTH({col:month}),25)-1,1)', 12),
    CA('event', 'Event this month', 'text', 'IF(OR(MONTH({col:month})=3,MONTH({col:month})=9),%s,IF(OR(MONTH({col:month})=6,MONTH({col:month})=12),%s,IF(OR(MONTH({col:month})=4,MONTH({col:month})=11),%s,"")))' % (OPENDAY, FAMEV, MEETW), 20),
    CA('conf_week', 'Conference week', 'date', 'IF(OR(MONTH({col:month})=4,MONTH({col:month})=11),%s,"")' % M3, 12),
    CA('event_date', 'Event date', 'date', 'IF({col:event}=%s,WORKDAY({col:month}+11,1),IF({col:event}=%s,WORKDAY({col:month}+7,1),IF({col:event}=%s,{col:conf_week},"")))' % (OPENDAY, FAMEV, MEETW), 12),
    CA('due_date', 'Start preparing by', 'date', 'MIN({col:news_date},IF({col:event_date}="",{col:news_date},{col:event_date}))-{set:prep_days}', 12),
    CA('days_to_due', 'Days to go', 'int', '{col:due_date}-{today}', 9),
    CA('flag', 'Plan check', 'text', 'IF({col:days_to_due}<0,%s,IF({col:days_to_due}<=7,%s,%s))' % (fl('Past'), fl('Due this week'), fl('Coming up')), 14),
    CA('ad_phone', 'Assistant director phone', 'text', '"%s"' % D.AD_PHONE, 18)],
    D.newsletter_plan_d(), 50, [A('flag', '= ' + fl('Due this week'), 'warn'), A('flag', '= ' + fl('Past'), 'good')]))

# 16 reports by staff and week
tables.append(T('reports_staff_week', 'Reports by Staff and Week', 'Daily reports by teacher and week',
    'One row per teacher and week: type the week and the teacher; the reports sent, the number sent the same day and the share against your target fill in from the Daily Reports sheet.', [
    C('sw_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), LST('staff', 'Teacher', 'teacher', 18),
    CA('reports', 'Reports sent', 'int', 'COUNTIFS(%s,{col:staff},%s,{col:week})' % (RG('reports', 'staff'), RG('reports', 'week')), 9),
    CA('same_day', 'Sent the same day', 'int', 'SUMIFS(%s,%s,{col:staff},%s,{col:week})' % (RG('reports', 'same_n'), RG('reports', 'staff'), RG('reports', 'week')), 10),
    CA('share', 'Same-day share', 'pct', 'IF({col:reports}>0,{col:same_day}/{col:reports},"")', 10),
    CA('flag', 'Target check', 'text', 'IF({col:share}="","",IF({col:share}>={set:same_day_target},%s,%s))' % (fl('On target'), fl('Behind target')), 14)],
    D.reports_staff_week_d(), 200, [A('flag', '= ' + fl('Behind target'), 'warn'), A('flag', '= ' + fl('On target'), 'good')]))

# 17 same-day share by room and month
tables.append(T('reports_room_month', 'Same-day Share by Room', 'Same-day report share by room and month',
    'One row per room and month: type the room and the month; the reports, the number sent the same day, the share, the last 30 days share and the teacher phone fill in.', [
    C('rm_id', 'Row ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), C('month', 'Month', 'date', 11),
    CA('reports', 'Reports sent', 'int', 'COUNTIFS(%s,{col:room},%s,{col:month})' % (RG('reports', 'room'), RG('reports', 'month')), 9),
    CA('same_day', 'Sent the same day', 'int', 'SUMIFS(%s,%s,{col:room},%s,{col:month})' % (RG('reports', 'same_n'), RG('reports', 'room'), RG('reports', 'month')), 10),
    CA('share', 'Same-day share', 'pct', 'IF({col:reports}>0,{col:same_day}/{col:reports},"")', 10),
    CA('flag', 'Target check', 'text', 'IF({col:share}="","",IF({col:share}>={set:same_day_target},%s,%s))' % (fl('On target'), fl('Behind target')), 14),
    CA('share30', 'Share, last 30 days', 'pct', 'IFERROR(SUMIFS(%s,%s,{col:room},%s,%s)/COUNTIFS(%s,{col:room},%s,%s),0)' % (RG('reports', 'same_n'), RG('reports', 'room'), RG('reports', 'date'), LAST30, RG('reports', 'room'), RG('reports', 'date'), LAST30), 11),
    CA('teacher_phone', 'Lead teacher phone', 'text', PHONE_BY_ROOM('room', D.TEACHER_PHONE, D.OWNER_PHONE), 18)],
    D.reports_room_month_d(), 100, [A('flag', '= ' + fl('Behind target'), 'warn'), A('flag', '= ' + fl('On target'), 'good')]))

# 18 conference slots
tables.append(T('conf_slots', 'Conference Slots', 'Conference slots for the next conference week',
    'One row per slot: type the date, time and teacher; the family and whether the slot is booked or free fill in from the Conferences sheet.', [
    C('slot_id', 'Slot ID', 'text', 9, required=True), C('date', 'Date', 'date', 12), C('slot', 'Slot', 'time', 9), LST('staff', 'Teacher', 'teacher', 18),
    CA('slot_key', 'Slot key', 'text', '{col:staff}&"|"&{col:date}&"|"&ROUND({col:slot}*1440,0)', 16),
    CA('family', 'Family', 'text', 'IFERROR(INDEX(%s,MATCH({col:slot_key},%s,0))&"","")' % (RG('conferences', 'family'), RG('conferences', 'slot_key')), 22),
    CA('status', 'Slot status', 'text', 'IF({col:family}="",%s,%s)' % (fl('Free slot'), fl('Booked slot')), 13),
    CA('staff_phone', 'Teacher phone', 'text', PHONE_BY('staff', 'teacher', D.STAFF_PHONE, D.OWNER_PHONE), 18)],
    D.conf_slots_d(), 100, [A('status', '= ' + fl('Free slot'), 'warn'), A('status', '= ' + fl('Booked slot'), 'good')]))

# 19 event attendance by kind and month
tables.append(T('att_month', 'Event Attendance by Kind', 'Event attendance by kind and month',
    'One row per month and event kind: type the month and the kind; the events held, the families invited and who came fill in from the Events sheet.', [
    C('am_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'ekind', 20),
    CA('events', 'Events held', 'int', 'COUNTIFS(%s,{col:kind},%s,{col:month},%s,"<="&{today})' % (RG('events', 'kind'), RG('events', 'month'), RG('events', 'date')), 9),
    CA('invited', 'Invited', 'int', 'SUMIFS(%s,%s,{col:kind},%s,{col:month},%s,"<="&{today})' % (RG('events', 'invited'), RG('events', 'kind'), RG('events', 'month'), RG('events', 'date')), 9),
    CA('attended', 'Attended', 'int', 'SUMIFS(%s,%s,{col:kind},%s,{col:month},%s,"<="&{today})' % (RG('events', 'attended'), RG('events', 'kind'), RG('events', 'month'), RG('events', 'date')), 9),
    CA('share', 'Attendance share', 'pct', 'IF({col:invited}>0,{col:attended}/{col:invited},0)', 11)],
    D.att_month_d(), 60, []))

# 20 children who left
tables.append(T('leavers_t', 'Children Who Left', 'Children who left, with months stayed and the reason',
    'One row per child who left: type the child ID; the family, room, dates, months stayed, reason and the yearly tuition of the place fill in from the Children sheet.', [
    C('child_id', 'Child ID', 'text', 9, required=True),
    CA('child', 'Child', 'text', LKT('children.child', 'children.child_id', 'child_id'), 22), CA('family', 'Family', 'text', LKT('children.family', 'children.child_id', 'child_id'), 20),
    CA('room', 'Room', 'text', LKT('children.room', 'children.child_id', 'child_id'), 12),
    CA('start_date', 'Start date', 'date', LKN('children.start_date', 'children.child_id', 'child_id'), 12), CA('end_date', 'End date', 'date', LKN('children.end_date', 'children.child_id', 'child_id'), 12),
    CA('months_stayed', 'Months stayed', 'int', LKN('children.months_stayed', 'children.child_id', 'child_id'), 9),
    CA('leave_reason', 'Leaving reason', 'text', LKT('children.leave_reason', 'children.child_id', 'child_id'), 14),
    CA('weekly_fee', 'Weekly tuition', 'money', LKN('children.weekly_fee', 'children.child_id', 'child_id'), 11), CA('lost_year', 'Tuition of a year', 'money', '{col:weekly_fee}*52', 12),
    CA('phone', 'Family phone', 'text', LKT('children.phone', 'children.child_id', 'child_id'), 18), CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)],
    D.leavers_d(), 80, []))
assert len(tables) == 20, len(tables)
