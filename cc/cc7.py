"""Childcare center suite - part 7: Families, Programs and Camps."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc7_lists import *
from cc7_tables import settings, tables
from cc7_tools import tools
import cc7_data as D

SUITE = 'fx-20261115-childcare-center'
NOTE = "Sample wording: adapt it to your own center and check your own local rules."
SIGN = 'Willow Lane Early Learning'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def RG(t, c): return '{range:%s.%s}' % (t, c)
REPL, AWAIT = tok('mstatus', 'Replied'), tok('mstatus', 'Awaiting reply')
HELD, BOOKED, NOSHOW = tok('confstatus', 'Held'), tok('confstatus', 'Booked'), tok('confstatus', 'No-show')
NEWS = tok('ekind', 'Newsletter'); PORT = tok('okind', 'Portfolio entry')
BAS, SUMMER = tok('program', 'Before-after school'), tok('program', 'Summer camp')
LEFT = tok('cstatus', 'Left')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def PK(t, col, idc): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, col, t, idc)

forms = [
    FORM('daily_sheet', 'Daily Report Sheet', 'Daily report record for one room and day', 'reports.report_id', F(
        ('Date', 'reports.date'), ('Room', 'reports.room'), ('Teacher', 'reports.staff'), ('Sent at', 'reports.sent_time'), ('Sent the same day', 'reports.same_day'), ('Sent the next day', 'reports.sent_next_day'),
        ('Week (Monday)', 'reports.week'), ('Lead teacher phone', 'reports.teacher_phone')) + [
        FF('Reports of this room that week', 'COUNTIFS({range:reports.room},%s,{range:reports.week},%s)' % (PK('reports', 'room', 'report_id'), PK('reports', 'week', 'report_id')), 'int'),
        FF('Of them sent the same day', 'SUMIFS({range:reports.same_n},{range:reports.room},%s,{range:reports.week},%s)' % (PK('reports', 'room', 'report_id'), PK('reports', 'week', 'report_id')), 'int')]),
    FORM('msg_sheet', 'Parent Message Log Sheet', 'Parent message log for one message', 'parent_msgs.message_id', F(
        ('Date', 'parent_msgs.date'), ('Family', 'parent_msgs.family'), ('Topic', 'parent_msgs.topic'), ('Status', 'parent_msgs.status'), ('Replied on', 'parent_msgs.replied_on'), ('Reply hours', 'parent_msgs.reply_hours'),
        ('Replied in time', 'parent_msgs.within_n'), ('Reply by', 'parent_msgs.reply_due'), ('Handled by', 'parent_msgs.handled_by'), ('Family phone', 'parent_msgs.phone')) + [
        FF('Messages from this family, all time', 'COUNTIFS({range:parent_msgs.family},%s)' % PK('parent_msgs', 'family', 'message_id'), 'int')]),
    FORM('conf_book', 'Conference Booking Sheet', 'Conference booking for one family and slot', 'conferences.conference_id', F(
        ('Date', 'conferences.date'), ('Slot', 'conferences.slot'), ('Family', 'conferences.family'), ('Child', 'conferences.child'), ('Teacher', 'conferences.staff'), ('Status', 'conferences.status'),
        ('Month', 'conferences.month'), ('Family phone', 'conferences.phone')) + [
        FF('Conferences held for this family', 'COUNTIFS({range:conferences.family},%s,{range:conferences.status},%s)' % (PK('conferences', 'family', 'conference_id'), HELD), 'int')]),
    FORM('conf_status', 'Conference Status Sheet', 'Conference status for one family, no notes', 'families.family_id', F(
        ('Family', 'families.family'), ('Parent or guardian', 'families.guardian'), ('Children enrolled now', 'families.enrolled_kids'), ('Conferences held', 'families.conf_held'), ('Conferences booked', 'families.conf_booked'),
        ('Conference no-shows', 'families.conf_noshow'), ('Last conference held', 'families.last_conf'), ('Next conference week', 'families.next_conf_week'), ('Phone', 'families.phone'))),
    FORM('event_plan', 'Event Plan Sheet', 'Event plan for one event', 'events.event_id', F(
        ('Date', 'events.date'), ('Kind', 'events.kind'), ('Room', 'events.room'), ('Families invited', 'events.invited'), ('Families attended', 'events.attended'), ('Attendance share', 'events.share'), ('Held or planned', 'events.when'))),
    FORM('event_att', 'Event Attendance Sheet', 'Event attendance for one kind and month', 'att_month.am_id', F(
        ('Month', 'att_month.month'), ('Kind', 'att_month.kind'), ('Events held', 'att_month.events'), ('Families invited', 'att_month.invited'), ('Families attended', 'att_month.attended'), ('Attendance share', 'att_month.share'))),
    FORM('news_plan', 'Newsletter Plan Sheet', 'Newsletter plan for one month', 'newsletter_plan.plan_id', F(
        ('Month', 'newsletter_plan.month'), ('Newsletter goes out', 'newsletter_plan.news_date'), ('Event this month', 'newsletter_plan.event'), ('Event date', 'newsletter_plan.event_date'), ('Conference week', 'newsletter_plan.conf_week'),
        ('Start preparing by', 'newsletter_plan.due_date'), ('Days to go', 'newsletter_plan.days_to_due'), ('Owner', 'newsletter_plan.owner'), ('Plan check', 'newsletter_plan.flag'))),
    FORM('obs_entry', 'Observation Entry Sheet', 'Observation entry record for one entry', 'observations.obs_id', F(
        ('Date', 'observations.date'), ('Child', 'observations.child'), ('Room', 'observations.room'), ('Teacher', 'observations.staff'), ('Kind', 'observations.kind'), ('In this term', 'observations.in_term')) + [
        FF('Entries of this child this term', 'COUNTIFS({range:observations.child},%s,{range:observations.in_term},1)' % PK('observations', 'child', 'obs_id'), 'int'),
        FF('Entries of this child in total', 'COUNTIFS({range:observations.child},%s)' % PK('observations', 'child', 'obs_id'), 'int')]),
    FORM('portfolio', 'Portfolio Update Sheet', 'Portfolio update status for one child', 'obs_status.child_id', F(
        ('Child', 'obs_status.child'), ('Room', 'obs_status.room'), ('Teacher', 'obs_status.teacher'), ('Entries this term', 'obs_status.entries_term'), ('Portfolio entries this term', 'obs_status.portfolio_n'), ('Last entry', 'obs_status.last_entry'),
        ('Days since the last entry', 'obs_status.days_since'), ('Entries still to do', 'obs_status.todo'), ('Entry check', 'obs_status.flag'))),
    FORM('survey_sheet', 'Leaving Family Survey Sheet', 'Leaving family survey record for one child', 'leavers_t.child_id', F(
        ('Child', 'leavers_t.child'), ('Family', 'leavers_t.family'), ('Room', 'leavers_t.room'), ('Start date', 'leavers_t.start_date'), ('Last day', 'leavers_t.end_date'), ('Months stayed', 'leavers_t.months_stayed'),
        ('Leaving reason', 'leavers_t.leave_reason'), ('Weekly tuition', 'leavers_t.weekly_fee'), ('Tuition of a year', 'leavers_t.lost_year'), ('Family phone', 'leavers_t.phone'))),
    FORM('camp_signup', 'Camp Sign-up Sheet', 'Camp sign-up for one child and week', 'program_signups.signup_id', F(
        ('Week (Monday)', 'program_signups.week'), ('Program', 'program_signups.program'), ('Child', 'program_signups.child'), ('Family', 'program_signups.family'), ('Days', 'program_signups.days'), ('Price a day', 'program_signups.price_day'),
        ('Fee', 'program_signups.fee'), ('Children signed up that week', 'program_signups.signups_n'), ('Break-even sign-ups', 'program_signups.break_even'), ('Decision for the week', 'program_signups.verdict'), ('Family phone', 'program_signups.phone'))),
    FORM('holiday_booking', 'Holiday Camp Booking Sheet', 'Camp week booking sheet for one week', 'camp_cal.cal_id', F(
        ('Week (Monday)', 'camp_cal.week'), ('Program', 'camp_cal.program'), ('Places', 'camp_cal.places'), ('Sign-ups', 'camp_cal.signups'), ('Open days', 'camp_cal.days'), ('Price a day', 'camp_cal.price_day'), ('Revenue', 'camp_cal.revenue'),
        ('Staff needed', 'camp_cal.staff_n'), ('Staff cost', 'camp_cal.staff_cost'), ('Break-even sign-ups', 'camp_cal.break_even'), ('Profit', 'camp_cal.profit'), ('Decision', 'camp_cal.verdict'))),
]
assert len(forms) == 12

documents = [
    DOC('newsletter_doc', 'Monthly Newsletter', 'Monthly newsletter for families', 'newsletter_plan.plan_id', [
        'Newsletter of {set:company} for the month of {col:newsletter_plan.month}, dated {today}. It goes out on {col:newsletter_plan.news_date}.',
        'This month: {col:newsletter_plan.event} on {col:newsletter_plan.event_date}. Conference week starts on {col:newsletter_plan.conf_week}. Please write these dates in your diary.',
        'Daily reports go home every day, and we try to send them the same day. Write to us if you want a message answered within {set:reply_hours_target} hours.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('event_invite', 'Event Invitation', 'Event invitation for families', 'events.event_id', [
        'Invitation of {set:company}, dated {today}. You are invited to our {col:events.kind} on {col:events.date}.',
        'We have invited {col:events.invited} families. Please tell us by message who will come so that we can plan the room and the refreshments.',
        'Children are welcome. If you cannot come, we will share what you missed in the next newsletter.'], ['Owner-director', 'Parent or guardian'], NOTE),
    DOC('conf_invite', 'Conference Invitation', 'Conference invitation and slot for a family', 'conferences.conference_id', [
        'Conference invitation of {set:company}, dated {today}. Family: {col:conferences.family}. Child: {col:conferences.child}.',
        'Your slot is {col:conferences.slot} on {col:conferences.date} with {col:conferences.staff}. Status: {col:conferences.status}.',
        'If the slot does not suit you, please message us as early as you can so that we can offer another one. Each conference is a short talk with the lead teacher.'], ['Lead teacher', 'Parent or guardian'], NOTE),
    DOC('conf_summary', 'Conference Summary Status', 'Conference summary status for a family, no content', 'families.family_id', [
        'Conference summary status of {set:company}, dated {today}. Family: {col:families.family}, parent or guardian {col:families.guardian}.',
        'Conferences held: {col:families.conf_held}. Conferences booked: {col:families.conf_booked}. No-shows: {col:families.conf_noshow}. Last conference held on {col:families.last_conf}. Next conference week: {col:families.next_conf_week}.',
        'This sheet records the status of each conference only. It holds no notes about the conversation.'], ['Lead teacher', 'Parent or guardian'], NOTE),
    DOC('report_template', 'Daily Report Template', 'Daily report cover for one room and day', 'reports.report_id', [
        'Daily report of {set:company}, room {col:reports.room}, date {col:reports.date}. Teacher: {col:reports.staff}.',
        'This report was sent at {col:reports.sent_time}. Sent the same day: {col:reports.same_day}.',
        'Write below the meals, the sleep times and the activities of the day in your own words. Tell us if you want to talk about anything.'], ['Lead teacher'], NOTE),
    DOC('weekly_update', 'Weekly Family Update', 'Weekly family update for a room', 'reports_room_month.rm_id', [
        'Weekly family update of {set:company}, room {col:reports_room_month.room}, month of {col:reports_room_month.month}.',
        'This month the room sent {col:reports_room_month.reports} daily reports, and {col:reports_room_month.same_day} of them went the same day. Target check: {col:reports_room_month.flag}.',
        'Write below the plans of the room for the coming week, the outings and any items families should bring.'], ['Lead teacher', 'Assistant director'], NOTE),
    DOC('camp_info', 'Camp Information Sheet', 'Camp information sheet for a week', 'camp_cal.cal_id', [
        'Camp information of {set:company}, dated {today}. Program: {col:camp_cal.program}, week of {col:camp_cal.week}.',
        'Open days: {col:camp_cal.days}. Hours each day: {set:camp_hours_day}. Price a day: {col:camp_cal.price_day}. Places: {col:camp_cal.places}. Children signed up so far: {col:camp_cal.signups}.',
        'Please bring a packed bag with spare clothes, a water bottle and a hat. We will tell you by message whether the week runs. A week runs when enough children sign up to cover its staff.'], ['Owner-director', 'Parent or guardian'], NOTE),
    DOC('camp_confirm', 'Camp Booking Confirmation', 'Camp booking confirmation for a child', 'program_signups.signup_id', [
        'Camp booking confirmation of {set:company}, dated {today}. Child: {col:program_signups.child}, family {col:program_signups.family}.',
        'Program: {col:program_signups.program}, week of {col:program_signups.week}, {col:program_signups.days} days at {col:program_signups.price_day} a day. Fee: {col:program_signups.fee}.',
        'Children signed up that week: {col:program_signups.signups_n}. The week needs {col:program_signups.break_even} to run. Decision so far: {col:program_signups.verdict}.'], ['Assistant director', 'Parent or guardian'], NOTE),
    DOC('camp_cancel', 'Camp Cancellation Notice', 'Camp cancellation notice for a week', 'camp_cal.cal_id', [
        'Camp cancellation notice of {set:company}, dated {today}. Program: {col:camp_cal.program}, week of {col:camp_cal.week}.',
        'We are sorry: {col:camp_cal.signups} children signed up and the week needed {col:camp_cal.break_even}. Decision: {col:camp_cal.verdict}.',
        'Any fee already paid for this week will be credited to your next invoice or returned on request. We will offer you another camp week.'], ['Owner-director', 'Parent or guardian'], NOTE),
    DOC('survey_letter', 'Family Survey Cover Letter', 'Family survey cover letter after leaving', 'leavers_t.child_id', [
        'Letter of {set:company}, dated {today}. To the family of {col:leavers_t.child} ({col:leavers_t.family}).',
        'Thank you for the {col:leavers_t.months_stayed} months with us in the {col:leavers_t.room} room, from {col:leavers_t.start_date} to {col:leavers_t.end_date}.',
        'We would like to ask you three short questions about your time with us: what worked, what we could change and whether you would recommend us. Your answers stay private.'], ['Owner-director', 'Parent or guardian'], NOTE),
    DOC('obs_report', 'Observation Status Report', 'Observation status report for a child, counts and dates only', 'obs_status.child_id', [
        'Observation status report of {set:company}, dated {today}. Child: {col:obs_status.child}, room {col:obs_status.room}, teacher {col:obs_status.teacher}.',
        'Entries this term: {col:obs_status.entries_term}, of which portfolio entries {col:obs_status.portfolio_n}. Last entry on {col:obs_status.last_entry}. Entries still to do: {col:obs_status.todo}. Check: {col:obs_status.flag}.',
        'This report lists counts and dates only. It holds no notes about what was observed.'], ['Lead teacher', 'Owner-director'], NOTE),
    DOC('year_end', 'Year-end Family Letter', 'Year-end letter for a family', 'families.family_id', [
        'Year-end letter of {set:company}, dated {today}. To {col:families.guardian} and the {col:families.family}.',
        'Thank you for the time you spend with us. Your family started with us on {col:families.first_start}; you have {col:families.enrolled_kids} children enrolled now and have joined {col:families.conf_held} conferences.',
        'Our next newsletter goes out on {col:families.news_date}. We wish you a calm and happy break and look forward to the new year together.'], ['Owner-director', 'Parent or guardian'], NOTE),
]
assert len(documents) == 12

checklists = [
    CHK('reports_sent', 'Daily Reports Sent Steps', 'reports', 'reports.date', [('Write the day\'s notes for each child', 0), ('Check every report in the room is written', 0), ('Send the reports before closing time', 0), ('Mark any report sent late', 0), ('Tell the assistant director about a late report', 1)]),
    CHK('reply_msgs', 'Replying to Messages Steps', 'parent_msgs', 'parent_msgs.date', [('Log the message with its topic', 0), ('Send a first answer within your target hours', 1), ('Hand billing and schedule questions to the assistant director', 1), ('Record the reply time', 1), ('Call the family if the message is still open', 3)]),
    CHK('newsletter', 'Newsletter Steps', 'newsletter_plan', 'newsletter_plan.month', [('Choose the dates and news for the month', 5), ('Ask each teacher for a short note', 8), ('Draft the newsletter', 14), ('Check dates and names', 20), ('Send the newsletter', 24), ('Note how many families opened it', 30)]),
    CHK('plan_event', 'Planning an Event Steps', 'events', 'events.date', [('Choose the date and the room', -42), ('Send the invitation', -28), ('Count the replies', -14), ('Order food and supplies', -7), ('Remind families', -1), ('Run the event and count who came', 0), ('Send thanks and record attendance', 2)]),
    CHK('conf_week', 'Conference Week Steps', 'conferences', 'conferences.date', [('Open the slots and send the invitation', -28), ('Book each family into a slot', -14), ('Remind families of their slot', -2), ('Prepare the room and the child folders', -1), ('Record held, booked or no-show', 0), ('Rebook the families who missed', 3)]),
    CHK('obs_update', 'Observation Update Steps', 'observations', 'observations.date', [('List the children with no entry this term', 0), ('Plan the entries for the week', 0), ('Write the entries and record the date', 3), ('Update the portfolio entries count', 5), ('Tell the owner-director about children still missing an entry', 7)]),
    CHK('term_portfolio', 'Term-end Portfolio Check Steps', 'observations', 'observations.date', [('Count the entries of each child this term', 0), ('Flag the children below your target', 1), ('Write the missing entries', 7), ('Check each portfolio is complete', 10), ('Share the status with the owner-director', 12)]),
    CHK('camp_setup', 'Camp Week Set-up Steps', 'camp_cal', 'camp_cal.week', [('Open sign-up for the week', -42), ('Send the camp information sheet', -35), ('Check sign-ups against break-even', -14), ('Decide: run, run with a minimum or cancel', -10), ('Book floaters for the days', -7), ('Order supplies and snacks', -5), ('Send the final confirmation', -3)]),
    CHK('camp_close', 'Camp Week Close Steps', 'camp_cal', 'camp_cal.week', [('Count the children who came each day', 4), ('Check staff hours against the plan', 5), ('Record revenue and staff cost', 6), ('Invoice the camp fees', 7), ('Note what to change for the next camp week', 8)]),
    CHK('holiday_plan', 'Holiday Camp Planning Steps', 'program_weeks', 'program_weeks.week', [('Choose the holiday weeks and the price a day', -60), ('Set the minimum sign-ups', -56), ('Tell families the dates', -49), ('Count sign-ups each week', -21), ('Confirm or cancel each week', -10), ('Book the staff and the floaters', -7)]),
    CHK('leaving_follow', 'Leaving Family Follow-up Steps', 'children', 'children.end_date', [('Confirm the last day and the final invoice', -14), ('Send the survey cover letter', -7), ('Thank the family on the last day', 0), ('Record the reason for leaving', 0), ('Offer the place to the waiting list', 1), ('Review the answers with the owner-director', 14)]),
    CHK('year_end_comm', 'Year-end Family Letter Steps', 'events', 'events.date', [('Choose the date of the year-end letter', -30), ('Write the letter and the closure dates', -21), ('Send the letter to every family', -14), ('Send a reminder of the closure days', -3), ('Send thanks and the first news of the new year', 7)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text + ' ' + SIGN)
messages = [
    M('f_report', 'Family: the daily report is ready', 'children', 'children.phone', 'Hello {guardian}, the daily report for {child} in the {room} room is ready. Please tell us if you have a question.'),
    M('f_report_late', 'Family: sorry, the report was late', 'children', 'children.phone', 'Hello {guardian}, we are sorry that the daily report for {child} was late today. We will send it before closing time.'),
    M('f_msg_ok', 'Family: we got your message', 'parent_msgs', 'parent_msgs.phone', 'Hello {family}, we received your message of {date} about {topic} and will reply by {reply_due}.'),
    M('f_reply_from', 'Family: your reply from a staff member', 'parent_msgs', 'parent_msgs.phone', 'Hello {family}, our reply to your message about {topic} comes from {handled_by}. Please call us if you want to talk.'),
    M('f_news', 'Family: our newsletter is coming', 'families', 'families.phone', 'Hello {guardian}, our newsletter goes out on {news_date}. Please tell us if you want it by email.'),
    M('f_invite', 'Family: you are invited to an event', 'families', 'families.phone', 'Hello {guardian}, you are invited to our {next_event} on {next_event_date}. Please reply to say who will come.'),
    M('f_remind', 'Family: reminder, the event is soon', 'families', 'families.phone', 'Hello {guardian}, a reminder: our {next_event} is on {next_event_date}. We look forward to seeing you.'),
    M('f_thanks', 'Family: thank you for coming', 'families', 'families.phone', 'Hello {guardian}, thank you for coming to our {last_event} on {last_event_date}.'),
    M('f_slot', 'Family: your conference slot', 'conferences', 'conferences.phone', 'Hello {family}, your conference for {child} is at {slot} on {date} with {staff}.'),
    M('f_choose', 'Family: please choose a conference slot', 'families', 'families.phone', 'Hello {guardian}, please choose a conference slot for the week of {next_conf_week}. Reply with a day and a time.'),
    M('f_conf_tomorrow', 'Family: conference reminder', 'conferences', 'conferences.phone', 'Hello {family}, a reminder: your conference with {staff} is on {date} at {slot}.'),
    M('f_conf_missed', 'Family: we missed you, may we rebook', 'conferences', 'conferences.phone', 'Hello {family}, we missed you at your conference on {date}. May we book a new time?'),
    M('f_camp_open', 'Family: camp sign-up is open', 'families', 'families.phone', 'Hello {guardian}, sign-up is open for {next_camp_program} in the week of {next_camp_week}. Reply to book a place.'),
    M('f_camp_remind', 'Family: camp reminder for the week', 'program_signups', 'program_signups.phone', 'Hello {family}, a reminder: {child} is booked for {program} in the week of {week}, {days} days at {price_day} a day.'),
    M('f_camp_ok', 'Family: camp is confirmed', 'program_signups', 'program_signups.phone', 'Hello {family}, {program} in the week of {week} is confirmed with {signups_n} children. The fee for {child} is {fee}.'),
    M('f_camp_cancel', 'Family: camp is cancelled', 'program_signups', 'program_signups.phone', 'Hello {family}, we are sorry: {program} in the week of {week} is cancelled because there are not enough sign-ups. We will offer another week.'),
    M('f_camp_free', 'Family: a place is free in camp', 'families', 'families.phone', 'Hello {guardian}, a place is free in {next_camp_program} in the week of {next_camp_week}. Reply if you want it.'),
    M('f_bas', 'Family: before-after school starts', 'children', 'children.phone', 'Hello {guardian}, the before-after school days for {child} start on {start_date}, with sign-in on arrival and collection before closing time.'),
    M('f_sorry', 'Family: sorry to see you go, why', 'children', 'children.phone', 'Hello {guardian}, we are sorry to see {child} go. May we ask in a short reply what made you decide?'),
    M('f_survey', 'Family: short survey after leaving', 'children', 'children.phone', 'Hello {guardian}, thank you for your time with us. Could you answer a short survey about {child} in the {room} room?'),
    M('f_pulse', 'Family: a 1 to 5 pulse', 'families', 'families.phone', 'Hello {guardian}, please share how we are doing: reply with one number from 1 to 5.'),
    M('t_reports', 'Lead teacher: reports to send today', 'reports_room_month', 'reports_room_month.teacher_phone', 'Hello, please send the daily report for the {room} room before closing. In {month} the room sent {same_day} of {reports} reports the same day.'),
    M('t_obs', 'Lead teacher: a child needs an entry', 'obs_status', 'obs_status.teacher_phone', 'Hello, {child} has {entries_term} entries this term. The last entry was on {last_entry}. Please add one this week.'),
    M('t_msgs', 'Lead teacher: messages waiting', 'parent_msgs', 'parent_msgs.teacher_phone', 'Hello, the message from {family} about {topic} on {date} is waiting for a reply. Please help us answer it today.'),
    M('t_slots', 'Lead teacher: your conference slots', 'conferences', 'conferences.staff_phone', 'Hello, you have a conference with {family} for {child} at {slot} on {date}.'),
    M('a_portfolio', 'Assistant: portfolio entry due', 'obs_status', 'obs_status.assistant_phone', 'Hello, a portfolio entry for {child} is due this week. The last entry was on {last_entry}.'),
    M('fl_camp', 'Floater: camp cover for a week', 'camp_cal', 'camp_cal.floater_phone', 'Hello, we need cover for {program} in the week of {week}: {signups} children are signed up. Can you work?'),
    M('fl_bas', 'Floater: before-after school cover', 'program_weeks', 'program_weeks.floater_phone', 'Hello, we need before-after school cover in the week of {week}: {signups} children are booked. Can you work?'),
    M('ad_waiting', 'Assistant director: message waiting', 'parent_msgs', 'parent_msgs.ad_phone', 'Hello, the message from {family} about {topic} has waited {wait_hours} hours for a reply.'),
    M('ad_contact', 'Assistant director: no contact', 'comm_gaps', 'comm_gaps.ad_phone', 'Hello, {family} has had no contact for {days_since} days. Please call them this week.'),
    M('ad_events', 'Assistant director: event reminders', 'events', 'events.ad_phone', 'Hello, please send the reminders for {kind} on {date}: {invited} families are invited.'),
    M('o_camp', 'Owner: camp weeks to run and to cancel', 'camp_cal', 'camp_cal.owner_phone', 'Hello, camp week {week} ({program}): {signups} sign-ups, {break_even} needed. Decision: {verdict}.'),
    M('o_reply', 'Owner: reply time by topic', 'parent_msgs', 'parent_msgs.owner_phone', 'Hello, replies on {topic} messages took {topic_avg90} hours on average in the last 90 days.'),
    M('o_leavers', 'Owner: leaver reasons', 'leavers_t', 'leavers_t.owner_phone', 'Hello, {child} left on {end_date} after {months_stayed} months. Reason: {leave_reason}. Weekly tuition: {weekly_fee}.'),
]
assert len(messages) == 34, len(messages)

R30 = '{range:reports.date},">"&({today}-30),{range:reports.date},"<="&{today}'
PM30 = '{range:parent_msgs.date},">"&({today}-30),{range:parent_msgs.date},"<="&{today}'
SUMR = '{range:program_weeks.week},">="&DATE(YEAR({today}),6,1),{range:program_weeks.week},"<="&DATE(YEAR({today}),9,15)'
NB = '{range:program_weeks.program},"<>"&%s' % BAS
EV90 = '{range:events.kind},"<>"&%s,{range:events.date},">"&({today}-90),{range:events.date},"<="&{today}' % NEWS
kpis = [
    KPI('Daily reports sent this month', 'COUNTIFS({range:reports.month},%s)' % MS, 'int'),
    KPI('Reports sent the same day, last 30 days', 'IFERROR(SUMIFS({range:reports.same_n},%s)/COUNTIFS(%s),0)' % (R30, R30), 'pct'),
    KPI('Reports sent next day, last 30 days', 'SUMIFS({range:reports.next_n},%s)' % R30, 'int'),
    KPI('Room with the slowest reports', 'INDEX({range:reports_room_month.room},MATCH(MIN({range:reports_room_month.share30}),{range:reports_room_month.share30},0))', 'text'),
    KPI('Parent messages this month', 'COUNTIFS({range:parent_msgs.month},%s)' % MS, 'int'),
    KPI('Messages awaiting a reply', 'COUNTIFS({range:parent_msgs.status},%s)' % AWAIT, 'int'),
    KPI('Oldest message waiting, hours', 'MAX({range:parent_msgs.wait_hours})', 'int'),
    KPI('Average reply hours, last 30 days', 'IFERROR(AVERAGEIFS({range:parent_msgs.reply_hours},%s,{range:parent_msgs.status},%s),0)' % (PM30, REPL), 'num'),
    KPI('Replies in the target hours, 90 days', 'IFERROR(SUMIFS({range:parent_msgs.within_n},{range:parent_msgs.date},">"&({today}-90))/COUNTIFS({range:parent_msgs.status},%s,{range:parent_msgs.date},">"&({today}-90)),0)' % REPL, 'pct'),
    KPI('Families with no contact over the limit', 'COUNTIFS({range:comm_gaps.days_since},">"&{set:contact_days})', 'int'),
    KPI('Billing messages, last 30 days', 'COUNTIFS(%s,{range:parent_msgs.topic},%s)' % (PM30, tok('topic', 'Billing')), 'int'),
    KPI('Pickup messages, last 30 days', 'COUNTIFS(%s,{range:parent_msgs.topic},%s)' % (PM30, tok('topic', 'Pickup')), 'int'),
    KPI('Events held this year, not newsletters', 'COUNTIFS({range:events.kind},"<>"&%s,{range:events.date},">="&DATE(YEAR({today}),1,1),{range:events.date},"<="&{today})' % NEWS, 'int'),
    KPI('Event attendance, last 90 days', 'IFERROR(SUMIFS({range:events.attended},%s)/SUMIFS({range:events.invited},%s),0)' % (EV90, EV90), 'pct'),
    KPI('Conferences held, last 12 months', 'COUNTIFS({range:conferences.status},%s,{range:conferences.date},">"&({today}-365),{range:conferences.date},"<="&{today})' % HELD, 'int'),
    KPI('Conferences booked, next 30 days', 'COUNTIFS({range:conferences.status},%s,{range:conferences.date},">"&{today},{range:conferences.date},"<="&({today}+30))' % BOOKED, 'int'),
    KPI('Conference no-show rate', 'IFERROR(COUNTIFS({range:conferences.status},%s)/(COUNTIFS({range:conferences.status},%s)+COUNTIFS({range:conferences.status},%s)),0)' % (NOSHOW, HELD, NOSHOW), 'pct'),
    KPI('Families without a conference slot', 'COUNTIFS({range:families.enrolled_kids},">0",{range:families.conf_booked},0)', 'int'),
    KPI('Observations this month', 'COUNTIFS({range:observations.month},%s)' % MS, 'int'),
    KPI('Observations this term', 'COUNTIFS({range:observations.in_term},1)', 'int'),
    KPI('Children with no entry this term', 'COUNTIFS({range:obs_status.entries_term},0)', 'int'),
    KPI('Portfolio entries this term', 'COUNTIFS({range:observations.in_term},1,{range:observations.kind},%s)' % PORT, 'int'),
    KPI('Teacher with the most entries to do', 'INDEX({range:obs_status.teacher},MATCH(MAX({range:obs_status.teacher_todo}),{range:obs_status.teacher_todo},0))', 'text'),
    KPI('Camp weeks this summer', 'COUNTIFS({range:program_weeks.program},%s,%s)' % (SUMMER, SUMR), 'int'),
    KPI('Camp sign-ups booked for coming weeks', 'SUMIFS({range:program_weeks.signups},{range:program_weeks.week},">"&{today},%s)' % NB, 'int'),
    KPI('Camp weeks below break-even, 12 months', 'COUNTIFS(%s,{range:program_weeks.gap},"<0",{range:program_weeks.week},">"&({today}-365),{range:program_weeks.week},"<="&{today})' % NB, 'int'),
    KPI('Camp revenue this summer', 'SUMIFS({range:program_weeks.revenue},{range:program_weeks.program},%s,%s)' % (SUMMER, SUMR), 'money'),
    KPI('Camp profit this summer', 'SUMIFS({range:program_weeks.profit},{range:program_weeks.program},%s,%s)' % (SUMMER, SUMR), 'money'),
    KPI('Before-after school children this month', 'ROUND(IFERROR(AVERAGEIFS({range:program_weeks.signups},{range:program_weeks.program},%s,{range:program_weeks.month},%s),0),0)' % (BAS, MS), 'int'),
    KPI('Children who left, last 12 months', 'COUNTIFS({range:children.status},%s,{range:children.end_date},">"&EDATE({today},-12))' % LEFT, 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Families and Camps Dashboard", "kpis": kpis,
    "monthly": {"title": "Daily reports sent the same day and next day", "date": "reports.date", "series": [
        {"label": "Sent the same day", "sum": "reports.same_n", "date": "reports.date"}, {"label": "Sent next day", "sum": "reports.next_n", "date": "reports.date"}]},
    "breakdowns": [{"title": "Parent messages by topic", "by": "parent_msgs.topic", "value": "parent_msgs.reply_hours", "agg": "count"}, {"title": "Camp revenue by program", "by": "program_weeks.program", "value": "program_weeks.revenue", "agg": "sum"},
                   {"title": "Conferences by status", "by": "conferences.status", "value": "conferences.noshow_n", "agg": "count"}, {"title": "Daily reports by room", "by": "reports.room", "value": "reports.same_n", "agg": "count"}]}
NBW = ('program', '<>', BAS)
insights = {"filters": [{"label": "Room", "list": "room"}, {"label": "Program", "list": "program"}],
    "gauges": [{"title": "Reports sent the same day", "num": AGG('sum', 'reports', 'reports.same_n'), "den": AGG('count', 'reports')},
               {"title": "Messages answered in the target hours", "num": AGG('sum', 'parent_msgs', 'parent_msgs.within_n'), "den": AGG('count', 'parent_msgs', where=[('status', '=', REPL)])},
               {"title": "Conference slots used", "num": AGG('count', 'conf_slots', where=[('status', '=', fl('Booked slot'))]), "den": AGG('count', 'conf_slots')},
               {"title": "Children with an observation this term", "num": AGG('count', 'obs_status', where=[('entries_term', '>', 0)]), "den": AGG('count', 'obs_status')},
               {"title": "Camp places filled", "num": AGG('sum', 'program_weeks', 'program_weeks.signups', where=[NBW]), "den": AGG('sum', 'program_weeks', 'program_weeks.places', where=[NBW])},
               {"title": "Camp weeks at or above break-even", "num": AGG('count', 'program_weeks', where=[NBW, ('gap', '>=', 0)]), "den": AGG('count', 'program_weeks', where=[NBW])}],
    "charts": [
        CHART('Daily reports per month', 'bar', 'month', [AGG('count', 'reports', date='reports.date', label='Reports')]),
        CHART('Same-day report share per month', 'column', 'month', [AGG('avg', 'reports', 'reports.same_n', date='reports.date', label='Share sent the same day')]),
        CHART('Daily reports by room', 'bar', 'reports.room', [AGG('count', 'reports', label='Reports')]),
        CHART('Daily reports by teacher', 'bar', 'reports.staff', [AGG('count', 'reports', label='Reports')]),
        CHART('Parent messages per month', 'bar', 'month', [AGG('count', 'parent_msgs', date='parent_msgs.date', label='Messages')]),
        CHART('Parent messages by topic', 'bar', 'parent_msgs.topic', [AGG('count', 'parent_msgs', label='Messages')]),
        CHART('Parent messages by status', 'bar', 'parent_msgs.status', [AGG('count', 'parent_msgs', label='Messages')]),
        CHART('Reply hours per month', 'column', 'month', [AGG('avg', 'parent_msgs', 'parent_msgs.reply_hours', date='parent_msgs.date', where=[('status', '=', REPL)], label='Average reply hours')]),
        CHART('Events by kind', 'bar', 'events.kind', [AGG('count', 'events', label='Events')]),
        CHART('Event attendance per month', 'bar', 'month', [AGG('sum', 'events', 'events.attended', date='events.date', label='Families attended')]),
        CHART('Conferences by status', 'bar', 'conferences.status', [AGG('count', 'conferences', label='Conferences')]),
        CHART('Conferences per month', 'bar', 'month', [AGG('count', 'conferences', date='conferences.date', label='Conferences')]),
        CHART('Observations per month', 'bar', 'month', [AGG('count', 'observations', date='observations.date', label='Entries')]),
        CHART('Observations by kind', 'bar', 'observations.kind', [AGG('count', 'observations', label='Entries')]),
        CHART('Observations by room', 'bar', 'observations.room', [AGG('count', 'observations', label='Entries')]),
        CHART('Observations by teacher', 'bar', 'observations.staff', [AGG('count', 'observations', label='Entries')]),
        CHART('Camp sign-ups per month', 'bar', 'month', [AGG('sum', 'program_weeks', 'program_weeks.signups', date='program_weeks.week', where=[NBW], label='Sign-ups')]),
        CHART('Camp revenue per month', 'bar', 'month', [AGG('sum', 'program_weeks', 'program_weeks.revenue', date='program_weeks.week', where=[NBW], label='Revenue')]),
        CHART('Sign-ups by program', 'bar', 'program_weeks.program', [AGG('sum', 'program_weeks', 'program_weeks.signups', label='Sign-ups')]),
        CHART('Places by program', 'bar', 'program_weeks.program', [AGG('avg', 'program_weeks', 'program_weeks.places', label='Places')]),
        CHART('Camp staff cost per month', 'bar', 'month', [AGG('sum', 'program_weeks', 'program_weeks.staff_cost', date='program_weeks.week', where=[NBW], label='Staff cost')]),
        CHART('Children leaving per month', 'bar', 'month', [AGG('count', 'children', date='children.end_date', where=[('status', '=', LEFT)], label='Children who left')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6
signature = [
    {"name": "Daily report and parent contact tracker", "why": "daily reports by room and teacher with the share sent the same day, parent messages waiting and families with no contact in one verdict", "where": "Report and Parent Contact"},
    {"name": "Newsletter, event and conference planner", "why": "a 12-month calendar of newsletters, events and conference weeks with the date to start preparing and the slots booked and free", "where": "Newsletter and Event Planner"},
    {"name": "Observation status by child", "why": "entries this term for every enrolled child with the children who have none flagged, counts and dates only", "where": "Observation Status by Child"},
    {"name": "Camp week fill and break-even", "why": "places, sign-ups and staff cost for each camp week give the break-even sign-ups and a decision to run, run with a minimum or cancel", "where": "Camp Week Fill and Break-even"},
    {"name": "Camp minimum sign-ups finder", "why": "staff cost over the income of one sign-up gives the minimum sign-ups, with price and staff changes and how many past weeks would have reached it", "where": "Camp Minimum Sign-ups Finder"},
    {"name": "Leaver reason analyser", "why": "months stayed, reason and the tuition that left with each child, and the reason to act on first", "where": "Leaver Reason Analyser"},
    {"name": "Communication gap finder", "why": "families ranked by days since the last contact, with messages waiting, so the assistant director calls the longest gap first", "where": "Communication Gap Finder"},
    {"name": "Conference slot scheduler", "why": "families without a slot, free slots and the no-show history show how many slots to add", "where": "Conference Slot Scheduler"},
    {"name": "Camp profit by week, ranked", "why": "every camp week ranked by revenue less staff cost, so you promote the best program and drop the weakest", "where": "Camp Profit by Week"},
    {"name": "Camp discount test", "why": "the extra sign-ups a sibling or early-bird discount must bring to pay for itself, with a verdict to offer it or not", "where": "Camp Discount Test"}]
competitors = [
    {"what": "free newsletter and event templates", "lacks": "give you a page to write on but no calendar of who is invited, no attendance share and no date to start preparing"},
    {"what": "subscription childcare-management software", "lacks": "charges every month or per child and hides how camp weeks are priced, so you cannot see why a week should run or be cancelled"},
    {"what": "generic parent-communication apps", "lacks": "send messages but never show the reply time by topic, the share of daily reports sent the same day or the families nobody has called"},
    {"what": "single-sheet camp sign-up lists", "lacks": "list the children but have no break-even sign-ups, no staff plan and no run or cancel decision for each week"}]
guide = [
    'Open Start and type your center name and your own limits in the yellow cells: reply hours, the same-day report target, the first day of the term and entries each child needs.',
    'Keep Children and Families up to date. Each family gets a room, and the Families sheet shows the last contact, the booked conference and the next event.',
    'Add each daily report on Daily Reports: the room, the teacher and the time it was sent. The same-day share and the room tables fill in by themselves.',
    'Log each parent message on Parent Messages with its topic and status only, never the content. Hours waiting and the reply-by date are calculated.',
    'Plan the year on Newsletter and Event Plan, add events on Events and conference slots on Conferences. Conference Slots shows which slots are booked and which are free.',
    'Add every observation or portfolio entry on Observations. Observation Status lists each enrolled child with the entries this term and a flag for children with none.',
    'Enter each program week on Program Weeks: places, sign-ups, price a day and staff cost. The Camp Calendar shows the break-even sign-ups and a decision for each camp week.',
    'Use Communication Gaps and the gap finder to call the families nobody has talked to for a long time.',
    'Add every child who leaves on Children with an end date and a reason; Children Who Left shows months stayed and the tuition of a year.',
    f'Use the {len(tools)} calculators for reports, planning, observations, camp fill, minimum sign-ups, price, staffing, discounts and leavers.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Families and Camps Dashboard and Charts every week: reports, messages, conferences, observations, camp fill and leavers.']
listing = {"title": "Childcare Center Families, Programs and Camps Excel Template: Daily Reports, Parent Messages, Conferences, Camp Break-even, Leavers",
    "headline": "Keep every family heard and know which camp weeks to run",
    "tags": ["childcare center", "daycare template", "home daycare", "parent communication", "daily report", "camp planner", "break even camp", "conference tracker", "newsletter planner", "childcare excel", "nursery spreadsheet", "family engagement", "daycare owner"],
    "description": ("Run the relationship with families and the camp programs of a home daycare or childcare center in one Excel workbook. Built for an owner-director with 1 to 5 rooms. "
        "Daily Reports show who sent each report and the share sent the same day by room and teacher; Parent Messages keeps the topic, the status and the hours a reply took, never the content. "
        "Families, Communication Gaps and a gap finder show who has not been called, and the conference sheets show held, booked and no-show status with free and booked slots.\n\n"
        "Observation Status lists every enrolled child with the entries this term and flags children with none, counts and dates only. "
        "Program Weeks and the Camp Calendar give places, sign-ups, price a day, staff cost and the break-even sign-ups for before-after school, summer camp and holiday camp weeks, with a decision to run, run with a minimum or cancel.\n\n"
        f"{len(tools)} calculators cover report tracking, the newsletter and event plan, observation status, camp fill, minimum sign-ups, price testing, staffing, discounts, reply time, conference slots, event attendance, leaver reasons and a family pulse score. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to families, teachers, floaters, the assistant director and the owner-director. Children's data is names, rooms, dates and status only.\n\n"
        "This is part seven of the Home Daycare and Childcare Center suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. It helps you keep track of families and camps and does not promise results."),
    "features": ["Daily report tracker with same-day share by room and teacher", "Parent messages by topic with reply time, status only", "Communication gap finder for families nobody has called",
                 "Conference slots booked and free with no-show history", "Observation status by child, counts and dates only", "Camp break-even and run or cancel decision for every week",
                 "Camp minimum sign-ups finder, price tester and discount test", "Leaver reasons with months stayed and tuition lost", f"{len(tools)} calculators for families and camps", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p7', slug='childcare-center-families', profession='Home Daycare and Childcare Center', name='Families, Programs and Camps',
         tagline='Keep every family heard and know which camp weeks to run', price_usd=29,
         colors={"primary": "#33658A", "accent": "#F6AE2D"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Families, programs and camps"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
