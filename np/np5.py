"""Nonprofit Organization suite - part 5: Programs and People Served."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np5_lists import *
from np5_tables import settings, tables, MS, YS, QSF
from np5_tools import tools
import np5_data as D

SUITE = 'fx-20261115-nonprofit'
NOTE = "Sample wording: adapt it to your own organization and check your local rules."
def R(t, c): return '{range:%s.%s}' % (t, c)
def LK(t, idc, c_): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c_, t, idc)
def F(*pairs): return [FV(a, b) for a, b in pairs]
def C_(t, c): return '{col:%s.%s}' % (t, c)
ACTV = tok('pstat', 'Active')

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('participant_sheet', 'Participant Sheet', 'Participant record', 'participants.participant_id', F(
        ('Name', 'participants.name'), ('Phone', 'participants.phone'), ('Program', 'participants.program'), ('Status', 'participants.status'), ('Start date', 'participants.start_date'), ('Last attended', 'participants.last_attended'),
        ('Sessions', 'participants.sessions'), ('Contact status', 'participants.contact_status'), ('Days since last seen', 'participants.days_since')) + [
        FF('Months on the books', 'IFERROR(DATEDIF(%s,%s,"M"),0)' % (LK('participants', 'participant_id', 'start_date'), LK('participants', 'participant_id', 'last_attended')), 'int'),
        FF('Sessions a month on the books', 'IFERROR(ROUND(%s/MAX(1,DATEDIF(%s,%s,"M")),1),0)' % (LK('participants', 'participant_id', 'sessions'), LK('participants', 'participant_id', 'start_date'), LK('participants', 'participant_id', 'last_attended')), 'num')]),
    FORM('contact_sheet', 'Participant Contact Sheet', 'Contact check of a participant', 'participants.participant_id', F(
        ('Name', 'participants.name'), ('Phone', 'participants.phone'), ('Program', 'participants.program'), ('Contact status', 'participants.contact_status'), ('Last attended', 'participants.last_attended'), ('Days since last seen', 'participants.days_since')) + [
        FF('Days without a visit, not seen', '{set:not_seen_days}', 'int'), FF('Days after which you propose to close', '{set:close_after_days}', 'int'),
        FF('Next step', 'IF(%s>{set:close_after_days},%s,IF(%s>{set:not_seen_days},%s,%s))' % (LK('participants', 'participant_id', 'days_since'), c1('Close the record'), LK('participants', 'participant_id', 'days_since'), c1('Call this week'), c1('Healthy')), 'text')]),
    FORM('attendance_sheet', 'Session Attendance Sheet', 'Attendance of one session', 'sessions.session_id', F(
        ('Date', 'sessions.date'), ('Program', 'sessions.program'), ('Staff', 'sessions.staff'), ('Attendees', 'sessions.attendees'), ('Volunteers', 'sessions.volunteers')) + [
        FF('Sessions of this program that month', 'COUNTIFS(%s,%s,%s,%s)' % (R('sessions', 'program'), LK('sessions', 'session_id', 'program'), R('sessions', 'month'), LK('sessions', 'session_id', 'month')), 'int'),
        FF('Average attendees of this program', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,%s),1),0)' % (R('sessions', 'attendees'), R('sessions', 'program'), LK('sessions', 'session_id', 'program')), 'num'),
        FF('Attendees against that average', 'IFERROR(%s/AVERAGEIFS(%s,%s,%s)-1,0)' % (LK('sessions', 'session_id', 'attendees'), R('sessions', 'attendees'), R('sessions', 'program'), LK('sessions', 'session_id', 'program')), 'pct')]),
    FORM('month_sheet', 'Program Month Sheet', 'One program in one month', 'program_months.row_id', F(
        ('Month', 'program_months.month'), ('Program', 'program_months.program'), ('People', 'program_months.participants'), ('Visits', 'program_months.visits'), ('New people', 'program_months.new_participants'),
        ('Sessions', 'program_months.sessions'), ('Capacity', 'program_months.capacity'), ('Waiting', 'program_months.waiting'), ('Volunteer hours', 'program_months.vol_hours'), ('Capacity used', 'program_months.share_used'),
        ('Visits per person', 'program_months.visits_per_person'), ('Verdict', 'program_months.verdict')) + [
        FF('Value of volunteer hours, your setting', 'ROUND(%s*{set:volunteer_hour_value},0)' % LK('program_months', 'row_id', 'vol_hours'), 'money')]),
    FORM('outcome_sheet', 'Outcome Sheet', 'One outcome in one quarter', 'outcomes.outcome_id', F(
        ('Quarter starts', 'outcomes.quarter'), ('Program', 'outcomes.program'), ('Outcome', 'outcomes.outcome'), ('Target', 'outcomes.target'), ('Actual', 'outcomes.actual'), ('Share of target', 'outcomes.share'),
        ('Over or behind', 'outcomes.gap'), ('Status', 'outcomes.status')) + [
        FF('Counted in the last four quarters', 'SUMIFS(%s,%s,%s,%s,%s,%s,">="&EDATE(%s,-9),%s,"<="&%s)' % (R('outcomes', 'actual'), R('outcomes', 'program'), LK('outcomes', 'outcome_id', 'program'), R('outcomes', 'outcome'), LK('outcomes', 'outcome_id', 'outcome'), R('outcomes', 'quarter'), LK('outcomes', 'outcome_id', 'quarter'), R('outcomes', 'quarter'), LK('outcomes', 'outcome_id', 'quarter')), 'num')]),
    FORM('target_sheet', 'Outcome Target Sheet', 'Yearly target of one outcome', 'outcome_defs.def_id', F(
        ('Program', 'outcome_defs.program'), ('Outcome', 'outcome_defs.outcome'), ('Unit', 'outcome_defs.unit'), ('Target for the year', 'outcome_defs.target_year'), ('Counted this year', 'outcome_defs.ytd_actual'),
        ('Share of the year target', 'outcome_defs.share_met'), ('Still to count', 'outcome_defs.gap'), ('Months left this year', 'outcome_defs.months_left'), ('Needed each month', 'outcome_defs.need_month'), ('Status', 'outcome_defs.status')) + [
        FF('Target for one quarter', 'ROUND(%s/4,1)' % LK('outcome_defs', 'def_id', 'target_year'), 'num')]),
    FORM('waiting_sheet', 'Waiting List Sheet', 'One person on the waiting list', 'waiting.participant_id', F(
        ('Name', 'waiting.name'), ('Phone', 'waiting.phone'), ('Program', 'waiting.program'), ('Waiting since', 'waiting.waiting_since'), ('Weeks waiting', 'waiting.weeks_waiting'), ('Place in the queue', 'waiting.position'),
        ('Free places', 'waiting.free_places'), ('Offer', 'waiting.offer')) + [
        FF('People waiting for this program', 'COUNTIFS(%s,%s)' % (R('waiting', 'program'), LK('waiting', 'participant_id', 'program')), 'int')]),
    FORM('offer_sheet', 'Place Offer Sheet', 'Offer of a place', 'waiting.participant_id', F(
        ('Name', 'waiting.name'), ('Phone', 'waiting.phone'), ('Program', 'waiting.program'), ('Offer', 'waiting.offer'), ('Reply by', 'waiting.reply_by'), ('Place held until', 'waiting.hold_until')) + [
        FF('Days to reply', '%s-{today}' % LK('waiting', 'participant_id', 'reply_by'), 'int'), FF('Days the place is held', '%s-%s' % (LK('waiting', 'participant_id', 'hold_until'), LK('waiting', 'participant_id', 'reply_by')), 'int')]),
    FORM('cost_sheet', 'Program Cost Sheet', 'Cost of one program in one month', 'program_cost.cost_id', F(
        ('Month', 'program_cost.month'), ('Program', 'program_cost.program'), ('Direct cost', 'program_cost.direct_cost'), ('Shared cost', 'program_cost.shared_cost'), ('Total cost', 'program_cost.total'), ('People', 'program_cost.people'),
        ('Cost per participant', 'program_cost.cost_per_participant'), ('Money coded to the program', 'program_cost.funding')) + [
        FF('Shared share of the total', 'IFERROR(%s/%s,0)' % (LK('program_cost', 'cost_id', 'shared_cost'), LK('program_cost', 'cost_id', 'total')), 'pct'),
        FF('Gap between cost and money coded', 'MAX(0,%s-%s)' % (LK('program_cost', 'cost_id', 'total'), LK('program_cost', 'cost_id', 'funding')), 'money')]),
    FORM('numbers_sheet', 'Funder Numbers Sheet', 'Numbers for a funder report', 'report_numbers.row_id', F(
        ('Program', 'report_numbers.program'), ('Period', 'report_numbers.period'), ('From', 'report_numbers.from_d'), ('To', 'report_numbers.to_d'), ('People served', 'report_numbers.people'), ('Visits', 'report_numbers.visits'),
        ('Sessions', 'report_numbers.sessions'), ('Outcomes met', 'report_numbers.outcomes_met'), ('Share of outcome target', 'report_numbers.outcome_share'), ('Program cost', 'report_numbers.cost'),
        ('Cost per participant', 'report_numbers.cost_per_participant'), ('Volunteer hours', 'report_numbers.vol_hours'), ('Value of volunteer hours', 'report_numbers.hours_value'), ('Sentence', 'report_numbers.sentence'))),
    FORM('review_sheet', 'Program Review Sheet', 'Review of one program', 'capacity.program', F(('Enrolled', 'capacity.enrolled'), ('Waiting', 'capacity.waiting')) + [
        FF('Capacity', 'IFERROR(INDEX(%s,MATCH({pick},%s,0)),0)' % (R('programs', 'capacity'), R('programs', 'program')), 'int'),
        FF('Capacity used', 'IFERROR(%s/INDEX(%s,MATCH({pick},%s,0)),0)' % (LK('capacity', 'program', 'enrolled'), R('programs', 'capacity'), R('programs', 'program')), 'pct'),
        FF('Cost per participant this quarter', 'SUMIFS(%s,%s,{pick},%s,1)' % (R('cpp_quarter', 'cost_per_participant'), R('cpp_quarter', 'program'), R('cpp_quarter', 'is_now')), 'money'),
        FF('Cost per participant a year ago', 'SUMIFS(%s,%s,{pick},%s,1)' % (R('cpp_quarter', 'cost_per_participant'), R('cpp_quarter', 'program'), R('cpp_quarter', 'is_year_ago')), 'money'),
        FF('Share of outcome targets met this year', 'IFERROR(SUMIFS(%s,%s,{pick},%s,">="&%s)/SUMIFS(%s,%s,{pick},%s,">="&%s),0)' % (R('outcomes', 'actual'), R('outcomes', 'program'), R('outcomes', 'quarter'), YS, R('outcomes', 'target'), R('outcomes', 'program'), R('outcomes', 'quarter'), YS), 'pct'),
        FF('Sessions in the last 12 months', 'COUNTIFS(%s,{pick},%s,">="&({today}-365))' % (R('sessions', 'program'), R('sessions', 'date')), 'int')]),
    FORM('call_sheet', 'Not-seen Call Sheet', 'Call sheet for a participant not seen', 'not_seen.rank', F(
        ('Participant ID', 'not_seen.participant_id'), ('Name', 'not_seen.name'), ('Program', 'not_seen.program'), ('Last attended', 'not_seen.last_attended'), ('Days since last seen', 'not_seen.days_since'), ('Sessions before', 'not_seen.sessions'),
        ('Contact status', 'not_seen.contact_status'), ('Phone', 'not_seen.phone'), ('Action', 'not_seen.action')) + [FF('Days after which you propose to close', '{set:close_after_days}', 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
def DD(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
    DD('monthly_report', 'Program Monthly Report', 'Program monthly report', 'program_months.row_id', [
        '{set:org}, dated {today}. Program report for {col:program_months.program}, month starting {col:program_months.month}.',
        'People served: {col:program_months.participants}, of which {col:program_months.new_participants} are new. Visits: {col:program_months.visits}. Sessions: {col:program_months.sessions}. Visits per person: {col:program_months.visits_per_person}.',
        'Capacity: {col:program_months.capacity}, used {col:program_months.share_used}. Waiting: {col:program_months.waiting}. Verdict for the month: {col:program_months.verdict}.',
        'Volunteer hours: {col:program_months.vol_hours}. The numbers come from our own attendance records.'], ['Program manager', 'Executive director']),
    DD('yearly_summary', 'Program Yearly Summary', 'Program yearly summary', 'served_year.row_id', [
        '{set:org}, dated {today}. Yearly summary of {col:served_year.program} for {col:served_year.year}.',
        'Unique people on our books in the year: {col:served_year.unique_people}. The year before: {col:served_year.prev_people}. Change: {col:served_year.change}.',
        'Visits: {col:served_year.visits}. Sessions: {col:served_year.sessions}. New people: {col:served_year.new_people}. Visits per person: {col:served_year.visits_per_person}. Volunteer hours: {col:served_year.vol_hours}.'], ['Program manager', 'Executive director']),
    DD('cost_statement', 'Cost per Participant Statement', 'Cost per participant statement', 'cpp_quarter.row_id', [
        '{set:org}, dated {today}. Cost per participant of {col:cpp_quarter.program}, quarter starting {col:cpp_quarter.quarter_start}.',
        'Direct cost: {col:cpp_quarter.direct_cost}. Shared cost: {col:cpp_quarter.shared_cost}. Cost to date: {col:cpp_quarter.cost}. Unique people: {col:cpp_quarter.people}.',
        'Cost per participant at a full quarter pace: {col:cpp_quarter.cost_per_participant}. Same quarter last year: {col:cpp_quarter.last_year}. Change: {col:cpp_quarter.change}. Verdict: {col:cpp_quarter.verdict}.',
        'Shared cost is split by the rules on the Cost Allocation Rules sheet.'], ['Bookkeeper', 'Program manager']),
    DD('funder_page', 'Funder Report Numbers Page', 'Funder report numbers page', 'report_numbers.row_id', [
        '{set:org}, dated {today}. Numbers for a funder report: {col:report_numbers.program}, {col:report_numbers.period}, from {col:report_numbers.from_d} to {col:report_numbers.to_d}.',
        '{col:report_numbers.sentence}.',
        'People served: {col:report_numbers.people}. Visits: {col:report_numbers.visits}. Sessions: {col:report_numbers.sessions}. Outcomes met: {col:report_numbers.outcomes_met} of {col:report_numbers.outcomes_n}, {col:report_numbers.outcome_share} of the target.',
        'Program cost: {col:report_numbers.cost}. Cost per participant: {col:report_numbers.cost_per_participant}. Volunteer hours: {col:report_numbers.vol_hours}, valued at {col:report_numbers.hours_value} at your own setting.'], ['Development manager', 'Executive director']),
    DD('outcomes_report', 'Outcomes Report', 'Outcomes report, target against actual', 'outcome_defs.def_id', [
        '{set:org}, dated {today}. Outcome: {col:outcome_defs.outcome}, program {col:outcome_defs.program}.',
        'Target for the year: {col:outcome_defs.target_year} {col:outcome_defs.unit}. Counted this year: {col:outcome_defs.ytd_actual}. Share of the target: {col:outcome_defs.share_met}.',
        'Still to count: {col:outcome_defs.gap}. Months left this year: {col:outcome_defs.months_left}. Needed each month: {col:outcome_defs.need_month}. Status: {col:outcome_defs.status}.',
        'An outcome is a result for a participant that you count. These counts come from our own records.'], ['Program manager', 'Executive director']),
    DD('waiting_report', 'Waiting List Report', 'Waiting list report', 'capacity.program', [
        '{set:org}, dated {today}. Waiting list report for {col:capacity.program}.',
        'Enrolled: {col:capacity.enrolled}. Waiting: {col:capacity.waiting}.',
        'Compare these numbers with the capacity on the Programs sheet and with the weeks to clear on the Clear Time by Program sheet before you decide to add places or sessions.'], ['Program manager', 'Executive director']),
    DD('sessions_plan', 'Capacity and Sessions Plan', 'Capacity and sessions plan', 'clear_time.row_id', [
        '{set:org}, dated {today}. Capacity and sessions plan for {col:clear_time.program}, at the pace: {col:clear_time.pace}.',
        'Capacity: {col:clear_time.capacity}. Enrolled: {col:clear_time.enrolled}. Free places: {col:clear_time.free_places}. Waiting: {col:clear_time.waiting}. Waiting after the free places: {col:clear_time.still}.',
        'Places freed a week at this pace: {col:clear_time.places_week}. Weeks to clear: {col:clear_time.weeks_to_clear}. Verdict: {col:clear_time.verdict}. Places to offer now: {col:clear_time.to_offer}.'], ['Program manager', 'Executive director']),
    DD('fact_sheet', 'Program Fact Sheet', 'Program fact sheet: people, sessions, volunteers', 'weekday_att.row_id', [
        '{set:org}, dated {today}. Fact sheet of {col:weekday_att.program} on {col:weekday_att.weekday}.',
        'Sessions in the last 12 months: {col:weekday_att.sessions}. Average people at a session: {col:weekday_att.avg_att}. Average volunteers at a session: {col:weekday_att.avg_vol}.',
        'Next session on this weekday: {col:weekday_att.next_date}. Volunteers to ask for: {col:weekday_att.vol_needed}.'], ['Volunteer coordinator', 'Program manager']),
    DD('offer_letter', 'Place Offer Letter', 'Place offer letter', 'waiting.participant_id', [
        '{set:org}, dated {today}. Dear {col:waiting.name},',
        'A place is now free in {col:waiting.program}. You have been waiting since {col:waiting.waiting_since}. Please tell us by {col:waiting.reply_by} if you would like the place.',
        'We will hold the place until {col:waiting.hold_until}. If you no longer need it, please tell us so we can offer it to the next person.'], ['Program manager']),
    DD('welcome_note', 'Participant Welcome Note', 'Participant welcome note', 'participants.participant_id', [
        '{set:org}, dated {today}. Dear {col:participants.name},',
        'Welcome to {col:participants.program}. Your first session was on {col:participants.start_date}. We are glad you are here.',
        'If you cannot come, or if your phone number changes, please tell us. We will only keep your name, your program, your contact status and the dates you came.'], ['Program assistant', 'Program manager']),
    DD('board_review', 'Program Review for the Board', 'Program review for the board', 'scenario_cpp.row_id', [
        '{set:org}, dated {today}. Program review for the board: {col:scenario_cpp.program}.',
        'Cost in the last 12 months: {col:scenario_cpp.cost12}. Unique people: {col:scenario_cpp.people12}. Cost per participant now: {col:scenario_cpp.cpp_now}.',
        'If we served {col:scenario_cpp.serve_more} more people with the same money, there would be {col:scenario_cpp.people_after} people and a cost per participant of {col:scenario_cpp.cpp_after}, a saving of {col:scenario_cpp.saving} for each person. This is your own estimate, not a promise.'], ['Program manager', 'Board chair']),
    DD('annual_page', 'Annual Program Page', 'Annual program page for the annual report', 'report_numbers.row_id', [
        '{col:report_numbers.program}, {col:report_numbers.period}. {set:org}.',
        '{col:report_numbers.sentence}.',
        'Our volunteers gave {col:report_numbers.vol_hours} hours, a value of {col:report_numbers.hours_value} at the value we set for one volunteer hour.',
        'Numbers are from our own records and are checked before the report is printed.'], ['Executive director']),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('attendance_entry', 'Session Attendance Entry', 'sessions', 'sessions.date', [('Enter attendees and volunteers for the session', 0), ('Check the program and the staff member', 0), ('Mark any session that did not run', 1), ('Tell the program manager the week is complete', 7)]),
    CHK('weekly_check', 'Weekly Program Check', 'sessions', 'sessions.date', [('Open the Not Seen List', 0), ('Call the people at the top of the list', 2), ('Look at the waiting lists and free places', 3), ('Fix any contact status', 5)]),
    CHK('month_end', 'Month-end Program Numbers', 'program_months', 'program_months.month', [('Enter people, visits, new people and sessions for each program', 28), ('Enter the volunteer hours and the money coded to the program', 30), ('Check the Program Month Sheet', 32), ('Send the numbers to the executive director', 35)]),
    CHK('quarter_outcomes', 'Quarter-end Outcomes', 'outcomes', 'outcomes.quarter', [('Count each outcome for the quarter', 88), ('Enter target and actual on the Outcomes sheet', 90), ('Check the outcomes behind target', 93), ('Tell the program manager what is behind', 96)]),
    CHK('funder_numbers', 'Funder Report Numbers', 'cpp_quarter', 'cpp_quarter.quarter_start', [('Open the Report Numbers sheet for the period', 90), ('Check people, visits and outcomes with the Funder Report Checker', 92), ('Copy the sentence into the report', 94), ('Ask the development manager to review the numbers', 96)]),
    CHK('waiting_review', 'Waiting List Review', 'waiting', 'waiting.waiting_since', [('Check the waiting list against the free places', 0), ('Offer places to the people first in line', 1), ('Tell everyone else how long the wait may be', 3), ('Check the list again after the reply date', 10)]),
    CHK('notseen_followup', 'Not-seen Follow-up', 'participants', 'participants.last_attended', [('Call the participant', 14), ('Send a message if there is no answer', 17), ('Fix the contact status', 21), ('Propose to close the record after the set days', 90)]),
    CHK('cost_review', 'Cost per Participant Review', 'program_cost', 'program_cost.month', [('Check that every expense has a program and a function', 31), ('Check the Cost Allocation Rules', 33), ('Read the Cost per Participant tool for each program', 35), ('Send the shared cost split to the finance committee', 38)]),
    CHK('new_program', 'New Program Start', 'program_months', 'program_months.month', [('Add the program, its capacity and its lead', 0), ('Add the outcomes you will count and their yearly targets', 7), ('Code its expenses to the program', 14), ('Enter the first month of numbers', 31)]),
    CHK('program_close', 'Program Close-down', 'program_months', 'program_months.month', [('Tell the people on the program and the waiting list', 0), ('Count the final outcomes', 14), ('Finish the funder report numbers', 30), ('Move any left-over money as your rules allow', 45)]),
    CHK('yearly_review', 'Yearly Program Review', 'outcomes', 'outcomes.quarter', [('Read the Program Priority View', 270), ('Review cost per participant for each program', 275), ('Set the outcome targets for next year', 285), ('Take the review to the board', 300)]),
    CHK('founder_month', 'Founder First Program Month', 'participants', 'participants.start_date', [('Add the program and its capacity', 0), ('Enter each person who comes, with the date', 0), ('Enter the sessions and volunteers each week', 7), ('Read the month numbers and the not-seen list', 30)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
fn = first_name
PMN, EDN, DMN, VCN, ASN, BKN, ACN, PON = [fn(D.TEAMID[i]['name']) for i in ('NP-03', 'NP-01', 'NP-02', 'NP-04', 'NP-05', 'NP-08', 'NP-09', 'NP-15')]
TRN = fn(D.TREAS['name'])
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('p_welcome', 'Participant: welcome to the program', 'participants', 'participants.phone', 'Hello {name}, we are glad you joined {program}. Your first session is on {start_date}. {org}'),
    M('p_remind', 'Participant: session reminder', 'participants', 'participants.phone', 'Hello {name}, a reminder of {program} on {notice_date} at {notice_time}. {org}'),
    M('p_notseen', 'Participant: we have not seen you', 'participants', 'participants.phone', 'Hello {name}, we have not seen you at {program} since {last_attended}. Can we help? {org}'),
    M('p_place', 'Participant: a place is free', 'waiting', 'waiting.phone', 'Hello {name}, a place is now free in {program}. Please reply by {reply_by}. {org}'),
    M('p_onlist', 'Participant: you are on the waiting list', 'waiting', 'waiting.phone', 'Hello {name}, you are on the waiting list for {program}. We will tell you when a place opens. {org}'),
    M('p_moving', 'Participant: the program is moving', 'participants', 'participants.phone', 'Hello {name}, {program} is moving to {notice_time} on {notice_date}. {org}'),
    M('p_closed', 'Participant: the program is closed', 'participants', 'participants.phone', 'Hello {name}, {program} is closed on {notice_date}. {org}'),
    M('p_thanks', 'Participant: thank you for taking part', 'participants', 'participants.phone', 'Hello {name}, thank you for taking part in {program}. Please tell us how it went. {org}'),
    M('p_hold', 'Participant: we keep your place', 'waiting', 'waiting.phone', 'Hello {name}, we will keep your place in {program} until {hold_until}. {org}'),
    M('p_closing', 'Participant: we close your record', 'participants', 'participants.phone', 'Hello {name}, we are closing your record after {close_after} days without a visit. Tell us if you want to stay. {org}'),
    M('pm_notseen', 'Program manager: participants not seen', 'participants', 'participants.pm_phone', 'Hello %s, {not_seen_n} participants have not been seen for {not_seen_limit} days. {org}' % PMN),
    M('pm_waiting', 'Program manager: waiting and free places', 'clear_time', 'clear_time.pm_phone', 'Hello %s, {program} has {waiting} waiting and {free_places} free places. {org}' % PMN),
    M('pm_outcomes', 'Program manager: outcomes of the quarter', 'outcomes', 'outcomes.pm_phone', 'Hello %s, {outcome} in {program} for the quarter starting {quarter} is {actual} of {target}. {org}' % PMN),
    M('pm_cost', 'Program manager: cost per participant', 'cpp_quarter', 'cpp_quarter.pm_phone', 'Hello %s, cost per participant for {program} is {cost_per_participant}. {org}' % PMN),
    M('pm_numbers', 'Program manager: session numbers due', 'program_months', 'program_months.pm_phone', 'Hello %s, please send the session numbers for {month} by {due_date}. {org}' % PMN),
    M('pa_attend', 'Program assistant: enter attendance', 'sessions', 'sessions.staff_phone', 'Hello {staff}, please enter attendance for {date}. {org}'),
    M('pa_places', 'Program assistant: places to offer', 'clear_time', 'clear_time.asst_phone', 'Hello %s, {to_offer} places in {program} can be offered from the waiting list. {org}' % ASN),
    M('pa_call', 'Program assistant: please call people', 'participants', 'participants.asst_phone', 'Hello %s, please call {not_seen_n} people not seen for {not_seen_limit} days. {org}' % ASN),
    M('ed_served', 'Executive director: people served', 'program_months', 'program_months.ed_phone', 'Hello %s, {program} served {participants} people in the month starting {month}. {org}' % EDN),
    M('ed_cost', 'Executive director: cost per participant', 'cpp_quarter', 'cpp_quarter.ed_phone', 'Hello %s, cost per participant for {program} is {cost_per_participant} against {last_year} last year. {org}' % EDN),
    M('ed_gap', 'Executive director: funding gap', 'report_numbers', 'report_numbers.ed_phone', 'Hello %s, {program} is short of funding by {gap} for {period}. {org}' % EDN),
    M('dm_ready', 'Development manager: numbers ready', 'report_numbers', 'report_numbers.dm_phone', 'Hello %s, the numbers for the {program} report, {period}, are ready. {org}' % DMN),
    M('dm_served', 'Development manager: people and outcomes', 'report_numbers', 'report_numbers.dm_phone', 'Hello %s, {program} served {people} people with {outcomes_met} outcomes met, {period}. {org}' % DMN),
    M('dm_missing', 'Development manager: item missing', 'report_numbers', 'report_numbers.dm_phone', 'Hello %s, the {program} report, {period}, is missing: {missing_item}. {org}' % DMN),
    M('bd_numbers', 'Board member: program numbers', 'program_months', 'program_months.board_phone', 'Hello %s, the program numbers for the month starting {month} are ready. {org}' % TRN),
    M('fin_split', 'Finance committee: shared cost split', 'program_cost', 'program_cost.treas_phone', 'Hello finance committee, the shared cost split for the month starting {month} is attached: {shared_cost} to {program}. {org}'),
    M('fu_served', 'Funder: people served and cost', 'report_numbers', 'report_numbers.po_phone', 'Hello %s, people served in {period} were {people}, cost per participant {cost_per_participant}. {org}' % PON),
    M('vc_need', 'Volunteer coordinator: volunteers needed', 'weekday_att', 'weekday_att.vc_phone', 'Hello %s, {program} needs {vol_needed} volunteers on {next_date}. {org}' % VCN),
    M('vol_thanks', 'Volunteer: thank you for helping', 'sessions', 'sessions.vol_phone', 'Hello, thank you for helping at {program} on {date}. {org}'),
    M('bk_code', 'Bookkeeper: code an expense', 'expenses', 'expenses.bk_phone', 'Hello %s, please code {amount} of expense {expense_id} to {program}. {org}' % BKN),
    M('bk_split', 'Bookkeeper: check the shared cost split', 'program_cost', 'program_cost.bk_phone', 'Hello %s, the shared cost split for the month starting {month} needs your check: {shared_cost} to {program}. {org}' % BKN),
    M('acc_split', 'Accountant: program cost split', 'served_year', 'served_year.acc_phone', 'Hello %s, the program cost split for {year} is attached for {program}. {org}' % ACN),
    M('pt_places', 'Partner: places for referrals', 'clear_time', 'clear_time.partner_phone', 'Hello, we have {free_places} places in {program} for your referrals. {org}'),
    M('pt_thanks', 'Partner: thank you', 'program_months', 'program_months.partner_phone', 'Hello, thank you for working with us: {new_participants} people joined {program} in the month starting {month}. {org}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def RR(t, c): return '{range:%s.%s}' % (t, c)
SEC = lambda p: tok('sprogram', p)
kpis = [
    KPI('People served this month', 'SUMIFS(%s,%s,%s)' % (RR('program_months', 'participants'), RR('program_months', 'month'), MS), 'int'),
    KPI('People served this year', 'COUNTIFS(%s,"<="&{today},%s,">="&%s)' % (RR('participants', 'start_date'), RR('participants', 'last_attended'), YS), 'int'),
    KPI('Unique people, last 12 months', 'COUNTIFS(%s,"<="&{today},%s,">="&({today}-365))' % (RR('participants', 'start_date'), RR('participants', 'last_attended')), 'int'),
    KPI('Visits this month', 'SUMIFS(%s,%s,%s)' % (RR('program_months', 'visits'), RR('program_months', 'month'), MS), 'int'),
    KPI('Visits this year', 'SUMIFS(%s,%s,">="&%s)' % (RR('program_months', 'visits'), RR('program_months', 'month'), YS), 'int'),
    KPI('New participants this month', 'SUMIFS(%s,%s,%s)' % (RR('program_months', 'new_participants'), RR('program_months', 'month'), MS), 'int'),
    KPI('Sessions this month', 'COUNTIFS(%s,%s)' % (RR('sessions', 'month'), MS), 'int'),
    KPI('Average attendees a session this month', 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (RR('sessions', 'attendees'), RR('sessions', 'month'), MS), 'num'),
    KPI('After-School Learning served this month', 'SUMIFS(%s,%s,%s)' % (RR('served_month', 'people'), RR('served_month', 'program'), SEC('After-School Learning')), 'int'),
    KPI('Family Food Pantry served this month', 'SUMIFS(%s,%s,%s)' % (RR('served_month', 'people'), RR('served_month', 'program'), SEC('Family Food Pantry')), 'int'),
    KPI('Senior Meals served this month', 'SUMIFS(%s,%s,%s)' % (RR('served_month', 'people'), RR('served_month', 'program'), SEC('Senior Meals and Visits')), 'int'),
    KPI('Summer Youth Camp served this month', 'SUMIFS(%s,%s,%s)' % (RR('served_month', 'people'), RR('served_month', 'program'), SEC('Summer Youth Camp')), 'int'),
    KPI('Participants not seen for the set days', 'SUM(%s)' % RR('participants', 'not_seen'), 'int'),
    KPI('Contact status to fix', 'SUM(%s)' % RR('participants', 'contact_fix'), 'int'),
    KPI('Capacity used across programs in season', 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0)' % (RR('program_months', 'participants'), RR('program_months', 'is_now'), RR('program_months', 'cap_in_season'), RR('program_months', 'is_now')), 'pct'),
    KPI('Waiting list total', 'SUM(%s)' % RR('capacity', 'waiting'), 'int'),
    KPI('Weeks to clear the longest list', 'MAX(%s)' % RR('clear_time', 'weeks_usual'), 'int'),
    KPI('Cost per participant this quarter', 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0)' % (RR('cpp_quarter', 'cost_pace'), RR('cpp_quarter', 'is_now'), RR('cpp_quarter', 'people'), RR('cpp_quarter', 'is_now')), 'money'),
    KPI('Cost per participant last quarter', 'IFERROR(SUMIFS(%s,%s,EDATE(%s,-3))/SUMIFS(%s,%s,EDATE(%s,-3)),0)' % (RR('cpp_quarter', 'cost_pace'), RR('cpp_quarter', 'quarter_start'), QSF, RR('cpp_quarter', 'people'), RR('cpp_quarter', 'quarter_start'), QSF), 'money'),
    KPI('Cost per participant a year ago', 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0)' % (RR('cpp_quarter', 'cost_pace'), RR('cpp_quarter', 'is_year_ago'), RR('cpp_quarter', 'people'), RR('cpp_quarter', 'is_year_ago')), 'money'),
    KPI('Program cost this year', 'SUMIFS(%s,%s,">="&%s)' % (RR('program_cost', 'total'), RR('program_cost', 'month'), YS), 'money'),
    KPI('Program share of all cost this year', 'IFERROR(SUMIFS(%s,%s,">="&%s)/SUMIFS(%s,%s,">="&%s),0)' % (RR('expenses', 'to_program'), RR('expenses', 'month'), YS, RR('expenses', 'amount'), RR('expenses', 'month'), YS), 'pct'),
    KPI('Outcomes met this year', 'COUNTIFS(%s,1,%s,">="&%s)' % (RR('outcomes', 'met'), RR('outcomes', 'quarter'), YS), 'int'),
    KPI('Outcomes behind target this year', 'COUNTIFS(%s,0,%s,">="&%s)' % (RR('outcomes', 'met'), RR('outcomes', 'quarter'), YS), 'int'),
    KPI('Share of outcome target met this year', 'IFERROR(SUMIFS(%s,%s,">="&%s)/SUMIFS(%s,%s,">="&%s),0)' % (RR('outcomes', 'actual'), RR('outcomes', 'quarter'), YS, RR('outcomes', 'target'), RR('outcomes', 'quarter'), YS), 'pct'),
    KPI('People served against last year', 'IFERROR(COUNTIFS(%s,"<="&{today},%s,">="&({today}-365))/COUNTIFS(%s,"<="&({today}-365),%s,">="&({today}-730))-1,0)' % (RR('participants', 'start_date'), RR('participants', 'last_attended'), RR('participants', 'start_date'), RR('participants', 'last_attended')), 'pct'),
    KPI('Visits against last year', 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1)-1,0)' % (RR('program_months', 'visits'), RR('program_months', 'in_last12'), RR('program_months', 'visits'), RR('program_months', 'in_prev12')), 'pct'),
    KPI('Sessions with volunteers this month', 'COUNTIFS(%s,%s,%s,">0")' % (RR('sessions', 'month'), MS, RR('sessions', 'volunteers')), 'int'),
    KPI('Volunteer hours at programs this month', 'SUMIFS(%s,%s,%s)' % (RR('program_months', 'vol_hours'), RR('program_months', 'month'), MS), 'num'),
    KPI('Programs with a funding gap', 'COUNTIFS(%s,%s,%s,1)' % (RR('report_numbers', 'period'), tok('rperiod', 'Last 12 months'), RR('report_numbers', 'gap_flag')), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Programs Dashboard", "kpis": kpis,
    "monthly": {"title": "People, visits, new people and volunteer hours", "date": "program_months.month", "series": [
        {"label": "People served", "sum": "program_months.participants", "date": "program_months.month"}, {"label": "Visits", "sum": "program_months.visits", "date": "program_months.month"},
        {"label": "New people", "sum": "program_months.new_participants", "date": "program_months.month"}, {"label": "Volunteer hours", "sum": "program_months.vol_hours", "date": "program_months.month"}]},
    "breakdowns": [{"title": "People waiting by program, this month", "by": "program_months.program", "value": "program_months.waiting", "agg": "sum"}, {"title": "Participants by status", "by": "participants.status", "value": "participants.sessions", "agg": "count"},
                   {"title": "Outcomes counted by program", "by": "outcomes.program", "value": "outcomes.actual", "agg": "sum"}, {"title": "Program cost by program", "by": "program_cost.program", "value": "program_cost.total", "agg": "sum"}]}

def W(c, o, v): return (c, o, v)
NOW = [W('is_now', '=', 1)]
YR = lambda: tok('syear', str(Y))
insights = {"filters": [{"label": "Program", "list": "program"}, {"label": "Staff member", "list": "staff"}],
    "gauges": [
        {"title": "Capacity used, programs in season", "num": AGG('sum', 'program_months', 'program_months.participants', where=NOW), "den": AGG('sum', 'program_months', 'program_months.cap_in_season', where=NOW)},
        {"title": "Outcome target met", "num": AGG('sum', 'outcomes', 'outcomes.actual'), "den": AGG('sum', 'outcomes', 'outcomes.target')},
        {"title": "People served against last year", "num": AGG('sum', 'program_months', 'program_months.participants', where=[W('in_last12', '=', 1)]), "den": AGG('sum', 'program_months', 'program_months.participants', where=[W('in_prev12', '=', 1)])},
        {"title": "Cost per participant against a year ago", "num": AGG('avg', 'cpp_quarter', 'cpp_quarter.cost_per_participant', where=[W('is_now', '=', 1)]), "den": AGG('avg', 'cpp_quarter', 'cpp_quarter.cost_per_participant', where=[W('is_year_ago', '=', 1)])},
        {"title": "Participants seen in the last 30 days", "num": AGG('sum', 'participants', 'participants.seen_recent'), "den": AGG('count', 'participants', where=[W('status', '=', ACTV)])},
        {"title": "Waiting list against free places", "num": AGG('sum', 'program_months', 'program_months.fit', where=NOW), "den": AGG('sum', 'program_months', 'program_months.waiting', where=NOW)}],
    "charts": [
        CHART('People served per month', 'column', 'month', [AGG('sum', 'program_months', 'program_months.participants', date='program_months.month', label='People served')]),
        CHART('Visits per month', 'column', 'month', [AGG('sum', 'program_months', 'program_months.visits', date='program_months.month', label='Visits')]),
        CHART('New participants per month', 'column', 'month', [AGG('sum', 'program_months', 'program_months.new_participants', date='program_months.month', label='New people')]),
        CHART('Unique people by program, this year', 'bar', 'served_year.program', [AGG('sum', 'served_year', 'served_year.unique_people', where=[W('year', '=', YR())], label='Unique people')]),
        CHART('Visits by program, this year', 'bar', 'served_year.program', [AGG('sum', 'served_year', 'served_year.visits', where=[W('year', '=', YR())], label='Visits')]),
        CHART('Sessions per month', 'column', 'month', [AGG('count', 'sessions', date='sessions.date', label='Sessions')]),
        CHART('Average attendees per month', 'line', 'month', [AGG('avg', 'sessions', 'sessions.attendees', date='sessions.date', label='Average attendees')]),
        CHART('Capacity used by program, this month', 'bar', 'program_months.program', [AGG('avg', 'program_months', 'program_months.share_used', where=NOW, label='Capacity used')]),
        CHART('People waiting by program, this month', 'bar', 'program_months.program', [AGG('sum', 'program_months', 'program_months.waiting', where=NOW, label='Waiting')]),
        CHART('Cost per participant by program, this quarter', 'bar', 'cpp_quarter.program', [AGG('avg', 'cpp_quarter', 'cpp_quarter.cost_per_participant', where=NOW, label='Cost per participant')]),
        CHART('Cost per participant per month', 'line', 'month', [AGG('avg', 'program_cost', 'program_cost.cost_per_participant', date='program_cost.month', label='Cost per participant')]),
        CHART('Program cost by program', 'bar', 'program_cost.program', [AGG('sum', 'program_cost', 'program_cost.total', label='Program cost')]),
        CHART('Program cost per month', 'column', 'month', [AGG('sum', 'program_cost', 'program_cost.total', date='program_cost.month', label='Program cost')]),
        CHART('Participants by status', 'bar', 'participants.status', [AGG('count', 'participants', label='Participants')]),
        CHART('Participants by contact status', 'bar', 'participants.contact_status', [AGG('count', 'participants', label='Participants')]),
        CHART('Outcome actual and target by program', 'bar', 'outcomes.program', [AGG('sum', 'outcomes', 'outcomes.actual', label='Actual'), AGG('sum', 'outcomes', 'outcomes.target', label='Target')]),
        CHART('Share of outcome target met by program', 'bar', 'outcomes.program', [AGG('avg', 'outcomes', 'outcomes.share', label='Share of target')]),
        CHART('Outcomes counted per quarter', 'column', 'month', [AGG('sum', 'outcomes', 'outcomes.actual', date='outcomes.quarter', label='Outcomes counted')]),
        CHART('Sessions by weekday', 'bar', 'weekday_att.weekday', [AGG('sum', 'weekday_att', 'weekday_att.sessions', label='Sessions')]),
        CHART('Volunteers per session by program', 'bar', 'sessions.program', [AGG('avg', 'sessions', 'sessions.volunteers', label='Volunteers')]),
        CHART('Program staff hours by program', 'bar', 'staff_hours.program', [AGG('sum', 'staff_hours', 'staff_hours.hours', label='Staff hours')]),
        CHART('Unique people by year', 'bar', 'served_year.year', [AGG('sum', 'served_year', 'served_year.unique_people', label='Unique people')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Not-seen finder", "why": "active participants who stopped coming, ranked by sessions before, with the next step: call this week or close the record", "where": "Not-seen Finder"},
    {"name": "Cost per participant", "why": "direct plus shared cost divided by unique people, shown at a full-quarter pace and set against the same quarter last year", "where": "Cost per Participant"},
    {"name": "Cost allocation viewer", "why": "every shared cost with its visible rule and the part each program carries, so a funder can see how you split it", "where": "Cost Allocation Viewer"},
    {"name": "Serve-more scenario", "why": "what cost per participant becomes if you serve 5, 10, 20 or 30 percent more people with the same money", "where": "Serve-more Scenario"},
    {"name": "Funder sentence writer", "why": "people served, visits, cost per participant and volunteer hours written into one plain sentence for a funder report", "where": "Funder Sentence Writer"},
    {"name": "Outcome gap solver", "why": "the count needed each month to reach a yearly outcome target, set against your pace so far", "where": "Outcome Gap Solver"},
    {"name": "Report numbers builder", "why": "every number a funder report needs for any program and period, with a check for what is missing", "where": "Report Numbers Builder"},
    {"name": "Waiting list clearer", "why": "weeks until a waiting list clears at your own pace, and how many places to add if that is too long", "where": "Waiting List Clearer"},
    {"name": "Session planner", "why": "how many sessions cover the waiting list and which weekday is quietest, with the volunteers to ask for", "where": "Session Planner"},
    {"name": "Program priority view", "why": "cost per participant, outcomes met and waiting side by side, with grow, hold or review for each program", "where": "Program Priority View"}]
competitors = [
    {"what": "donor-management software", "lacks": "keeps gifts well but has no sessions, no not-seen list, no cost per participant and no waiting list against capacity"},
    {"what": "single-purpose attendance tracker templates", "lacks": "count visits but never split shared cost across programs, count outcomes against targets or write the funder sentence"},
    {"what": "generic client-list spreadsheets", "lacks": "hold names and dates with no capacity, no weeks to clear a waiting list and no month and year totals per program"},
    {"what": "nonprofit accounting add-ons", "lacks": "keep the ledger but give no unique people served, no cost allocation rules you can see and no outcome gap per month"}]
guide = [
    'Open the Start sheet and type your organization name, the days that count as not seen and the value you give one volunteer hour; every figure uses your own settings.',
    'To replace the demo data, clear the sample rows on each sheet and type your own; calculated columns fill in by themselves and nothing needs a macro.',
    'List your programs and their capacity on Programs; a founder with volunteers and no staff can keep one program and one fund and use the same sheets.',
    'Enter each person on Participants with program, status, start date, last attended and sessions; names, contact status, counts and dates only, nothing sensitive.',
    'Enter each session on Sessions and each month on Program Months (people, visits, new people, sessions, volunteer hours and money coded to the program).',
    'Open the Not Seen List every week and call the people at the top; the Not-seen Finder tool counts them and names the first three.',
    'Code every expense on Program Expenses to a program, a function and a fund; shared costs are split by the Cost Allocation Rules you can see and change.',
    'Read Program Cost and Cost per Participant by Quarter to see what one person costs; Serve-more Scenario shows what serving more would do.',
    'Count each outcome every quarter on Outcomes and set yearly targets on Outcome Definitions; the Outcome Gap Solver says how many a month you still need.',
    'Use Report Numbers and the Funder Sentence Writer when a funder report is due; the Funder Report Checker shows anything missing.',
    'Keep the Waiting List up to date; Capacity and Waiting Check, Waiting List Clearer and Session Planner say when to add a session.',
    f'Use the {len(tools)} tools for decisions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Why a workbook: one flat price, no fee for each contact, no paid add-ons for outcomes or volunteers, and your data stays with you. It works in Excel and Google Sheets.',
    'What this is not: not a mass-email tool, not a payment service, and not accounting or legal advice; check your local rules for records and privacy.']
listing = {"title": "Nonprofit Programs and People Served Excel Template: Participants, Cost per Participant, Outcomes, Waiting List",
    "headline": "Show what your programs deliver, who they serve and what each person costs",
    "tags": ["nonprofit", "program tracker", "outcomes tracking", "cost per participant", "waiting list", "excel template", "charity", "funder report", "people served", "attendance", "volunteer hours", "program evaluation", "nonprofit program"],
    "description": ("Run the program side of a small community nonprofit in one Excel workbook. Built for a program manager, an executive director and a development manager who must say how many people were served, what each person cost and what results were reached. "
        "Participants holds every person by name, program, status, start, last attended and sessions, and the Not Seen List ranks the active people who stopped coming so you know who to call this week. Program Months, Sessions and Served by Program and Year give people served, unique people and visits for every program, month and year.\n\n"
        "Program Expenses and the visible Cost Allocation Rules split shared cost across programs, management and fundraising, and Program Cost and Cost per Participant by Quarter show direct cost, shared cost and cost per participant against the same quarter last year. Outcomes and Outcome Definitions set each result against its yearly target. Report Numbers gathers people served, outcomes, cost per participant and volunteer hours for any funder report, with a ready sentence. Waiting List, Capacity and Clear Time show weeks until each list clears. "
        f"{len(tools)} tools answer the weekly questions: the not-seen finder, cost per participant, the cost allocation viewer, a serve-more scenario, the funder sentence writer, the outcome gap solver, the waiting list clearer, the session planner and a program priority view. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to participants, staff, the board and partners.\n\n"
        "This is part five of the Nonprofit Organization suite. It works in Excel and Google Sheets, has no macros and no subscription, and comes with a demo copy full of sample data. Forecasts and verdicts are your own estimate, not a promise. Participants are kept as names, contact status, counts and dates only. It helps you keep records and is not accounting or legal advice; ask your accountant what your own rules need."),
    "features": ["Participants with a ranked not-seen list", "People served per program, month and year", "Cost per participant with direct and shared cost", "Cost allocation rules you can see", "Outcomes against yearly targets", "Report numbers and a ready funder sentence",
                 "Waiting lists against capacity", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Works for a founder with one program"]}
s = spec(id=f'{SUITE}-p5', slug='nonprofit-programs', profession='Nonprofit Organization', name='Programs and People Served',
         tagline='Show who your programs serve, what each person costs and what results you reach', price_usd=29,
         colors={"primary": "#22577A", "accent": "#F2A541"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Programs and people served"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'np5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
