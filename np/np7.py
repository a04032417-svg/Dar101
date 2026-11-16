"""Nonprofit Organization suite - part 7: Board and Governance."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np7_lists import *
from np7_tables import settings, tables
from np7_tools import tools
import np7_data as D

SUITE = 'fx-20261115-nonprofit'
NOTE = "Sample wording: adapt it to your own organization and check your local rules."
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
YN = 'YEAR({today})'
JAN1 = 'DATE(YEAR({today}),1,1)'
THIS3 = tok('yr3', 'This year'); THIS2 = tok('yr2', 'This year')
HELD = tok('mstatus', 'Held'); FILED = tok('dclstatus', 'Filed'); OBDONE = tok('obstatus', 'Done'); PRESENT = tok('attend', 'Present')
def R(t, c): return '{range:%s.%s}' % (t, c)
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
fn = first_name
def FIRST(name): return name.replace('Dr. ', '').split()[0]

# ------------------------------------------------------------------ forms (12)
SEATS_OPEN = 'SUM(%s)' % R('seats', 'vacant')
forms = [
    FORM('member_sheet', 'Board Member Sheet', 'Board member record', 'board.member_id', F(
        ('Name', 'board.name'), ('Role', 'board.role'), ('Committee', 'board.committee'), ('Term start', 'board.term_start'), ('Term end', 'board.term_end'), ('Terms served', 'board.terms_served'), ('Skill', 'board.skill'), ('Second skill', 'board.skill2'),
        ('Donor ID', 'board.donor_id'), ('Months to term end', 'board.months_left'), ('Attendance this year', 'board.att_share'), ('Gifts this year', 'board.gifts_total'), ('Given and raised this year', 'board.gg_total')) + [
        FF('Terms left before your limit', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))-%s,"")' % (R('board_roles', 'max_terms'), LK('board', 'member_id', 'role'), R('board_roles', 'role'), LK('board', 'member_id', 'terms_served')), 'int'),
        FF('Declaration filed this year (1 or 0)', 'COUNTIFS(%s,{pick},%s,%s,%s,%s)' % (R('declarations', 'member_id'), R('declarations', 'year'), THIS3, R('declarations', 'status'), FILED), 'int')]),
    FORM('renewal_sheet', 'Term Renewal Sheet', 'Term renewal decision', 'terms_ending.member', F(
        ('Member', 'terms_ending.member'), ('Role', 'terms_ending.role'), ('Term end', 'terms_ending.term_end'), ('Months left', 'terms_ending.months_left'), ('Terms served', 'terms_ending.terms_served'), ('Most terms for the role', 'terms_ending.max_terms'),
        ('Can renew', 'terms_ending.can_renew'), ('Skill', 'terms_ending.skill'), ('Term ends in', 'terms_ending.ends_in'), ('Year check', 'terms_ending.check')) + [
        FF('Attendance this year', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('attendance_member', 'share'), R('attendance_member', 'member'), R('attendance_member', 'period'), THIS3), 'pct'),
        FF('Gifts this year', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('board_giving', 'total'), R('board_giving', 'member'), R('board_giving', 'period'), THIS3), 'money'),
        FF('Members with this skill in 6 months', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('skills_matrix', 'members'), R('skills_matrix', 'skill'), LK('terms_ending', 'member', 'skill'), R('skills_matrix', 'when'), tok('when', 'In 6 months')), 'int'),
        FF('Seats open now', SEATS_OPEN, 'int')]),
    FORM('recruit_sheet', 'Board Recruitment Sheet', 'Recruiting for a skill', 'skills.skill', F(('Skill', 'skills.skill'), ('Members needed', 'skills.needed'), ('What it is for', 'skills.note')) + [
        FF('Members with the skill now', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('skills_matrix', 'members'), R('skills_matrix', 'skill'), R('skills_matrix', 'when'), tok('when', 'Now')), 'int'),
        FF('Members with the skill in 6 months', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('skills_matrix', 'members'), R('skills_matrix', 'skill'), R('skills_matrix', 'when'), tok('when', 'In 6 months')), 'int'),
        FF('Members with the skill in 12 months', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('skills_matrix', 'members'), R('skills_matrix', 'skill'), R('skills_matrix', 'when'), tok('when', 'In 12 months')), 'int'),
        FF('Gap in 6 months', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('skills_matrix', 'gap'), R('skills_matrix', 'skill'), R('skills_matrix', 'when'), tok('when', 'In 6 months')), 'int'),
        FF('Gap in 12 months', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('skills_matrix', 'gap'), R('skills_matrix', 'skill'), R('skills_matrix', 'when'), tok('when', 'In 12 months')), 'int'),
        FF('Seats open now', SEATS_OPEN, 'int')]),
    FORM('committee_sheet', 'Committee Sheet', 'Committee record', 'committees.committee', F(('Committee', 'committees.committee'), ('Chair', 'committees.chair'), ('Meets', 'committees.meets')) + [
        FF('Next meeting of the committee', 'IFERROR(1/SUMPRODUCT(MAX((%s={pick})*(%s=%s)*(%s>0)/(%s+(%s=0)))),"")' % (R('meetings', 'kind'), R('meetings', 'status'), tok('mstatus', 'Planned'), R('meetings', 'date'), R('meetings', 'date'), R('meetings', 'date')), 'date'),
        FF('Chair phone', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('board', 'phone'), LK('committees', 'committee', 'chair'), R('board', 'name')), 'text'),
        FF('Members on the committee', 'COUNTIFS(%s,{pick},%s,1)' % (R('board', 'committee'), R('board', 'serving')), 'int'), FF('Fewest members you want', '{set:min_committee}', 'int'),
        FF('Members to add', 'MAX(0,{set:min_committee}-COUNTIFS(%s,{pick},%s,1))' % (R('board', 'committee'), R('board', 'serving')), 'int'),
        FF('Meetings held this year', 'COUNTIFS(%s,{pick},%s,%s,%s,%s)' % (R('meetings', 'kind'), R('meetings', 'status'), HELD, R('meetings', 'year'), YN), 'int'),
        FF('Share of expected members who came', 'IFERROR(SUMIFS(%s,%s,{pick},%s,%s,%s,%s)/SUMIFS(%s,%s,{pick},%s,%s,%s,%s),0)' % (R('meetings', 'present'), R('meetings', 'kind'), R('meetings', 'status'), HELD, R('meetings', 'year'), YN,
                                                                                                                                           R('meetings', 'expected'), R('meetings', 'kind'), R('meetings', 'status'), HELD, R('meetings', 'year'), YN), 'pct')]),
    FORM('meeting_sheet', 'Meeting Sheet', 'Meeting record', 'meetings.meeting_id', F(('Date', 'meetings.date'), ('Time', 'meetings.start_time'), ('Kind', 'meetings.kind'), ('Status', 'meetings.status'), ('Members expected', 'meetings.expected'), ('Members present', 'meetings.present'),
                                                                                       ('Quorum met', 'meetings.quorum_met'), ('Minutes final', 'meetings.minutes_ready'), ('Attendance share', 'meetings.share')) + [
        FF('Quorum number you set', '{set:quorum_number}', 'int'), FF('Members over or under the quorum', '%s-{set:quorum_number}' % LK('meetings', 'meeting_id', 'present'), 'int'),
        FF('Meetings of this kind that year', 'COUNTIFS(%s,%s,%s,%s)' % (R('meetings', 'kind'), LK('meetings', 'meeting_id', 'kind'), R('meetings', 'year'), LK('meetings', 'meeting_id', 'year')), 'int')]),
    FORM('attendance_sheet', 'Attendance Sheet', 'Attendance of a member at a meeting', 'attendance.att_id', F(('Meeting ID', 'attendance.meeting_id'), ('Date', 'attendance.date'), ('Kind', 'attendance.kind'), ('Member ID', 'attendance.member_id'), ('Member', 'attendance.member'),
                                                                                                           ('Status', 'attendance.status')) + [
        FF('Meetings of this member this year', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('attendance_member', 'meetings'), R('attendance_member', 'member'), LK('attendance', 'att_id', 'member'), R('attendance_member', 'period'), THIS3), 'int'),
        FF('Present this year', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('attendance_member', 'present'), R('attendance_member', 'member'), LK('attendance', 'att_id', 'member'), R('attendance_member', 'period'), THIS3), 'int'),
        FF('Attendance share this year', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('attendance_member', 'share'), R('attendance_member', 'member'), LK('attendance', 'att_id', 'member'), R('attendance_member', 'period'), THIS3), 'pct'),
        FF('Share you expect', '{set:attend_min}', 'pct')]),
    FORM('minutes_sheet', 'Minutes Sheet', 'Minutes of a meeting', 'meetings.meeting_id', F(('Date', 'meetings.date'), ('Time', 'meetings.start_time'), ('Kind', 'meetings.kind'), ('Members expected', 'meetings.expected'), ('Minutes final', 'meetings.minutes_ready')) + [
        FF('Members present on the attendance list', 'COUNTIFS(%s,{pick},%s,%s)' % (R('attendance', 'meeting_id'), R('attendance', 'status'), PRESENT), 'int'),
        FF('Members who sent apologies', 'COUNTIFS(%s,{pick},%s,%s)' % (R('attendance', 'meeting_id'), R('attendance', 'status'), tok('attend', 'Apologies')), 'int'),
        FF('Members absent', 'COUNTIFS(%s,{pick},%s,%s)' % (R('attendance', 'meeting_id'), R('attendance', 'status'), tok('attend', 'Absent')), 'int'),
        FF('Days since the meeting', '{today}-%s' % LK('meetings', 'meeting_id', 'date'), 'int'), FF('Days the minutes may take', '{set:minutes_days}', 'int')]),
    FORM('declaration_sheet', 'Declaration of Interests Sheet', 'Declaration of interests', 'declarations.decl_id', F(('Member ID', 'declarations.member_id'), ('Member', 'declarations.member'), ('Year', 'declarations.year'), ('Due date', 'declarations.due_date'),
                                                                                                                    ('Filed on', 'declarations.filed_on'), ('Items declared', 'declarations.items_declared'), ('Status', 'declarations.status'), ('Days late', 'declarations.days_late')) + [
        FF('Role of the member', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('board', 'role'), LK('declarations', 'decl_id', 'member_id'), R('board', 'member_id')), 'text'),
        FF('Declarations filed this year, all', 'COUNTIFS(%s,%s,%s,%s)' % (R('declarations', 'year'), THIS3, R('declarations', 'status'), FILED), 'int'),
        FF('Declarations still open this year', 'COUNTIFS(%s,%s,%s,"<>"&%s,%s,"<>")' % (R('declarations', 'year'), THIS3, R('declarations', 'status'), FILED, R('declarations', 'decl_id')), 'int')]),
    FORM('gog_sheet', 'Give or Get Sheet', 'Give or get record of a member', 'give_or_get.row_id', F(('Member', 'give_or_get.member'), ('Year', 'give_or_get.period'), ('Target', 'give_or_get.target'), ('Given', 'give_or_get.given'), ('Raised from their asks', 'give_or_get.raised'),
                                                                                                    ('Given and raised', 'give_or_get.total'), ('Remaining', 'give_or_get.remaining'), ('Share of the year passed', 'give_or_get.elapsed'), ('Status', 'give_or_get.status')) + [
        FF('Share of the target', 'IFERROR(%s/%s,0)' % (LK('give_or_get', 'row_id', 'total'), LK('give_or_get', 'row_id', 'target')), 'pct'), FF('Behind the year by', LK('give_or_get', 'row_id', 'behind_by'), 'money'),
        FF('Members who met the target this year', 'SUMIFS(%s,%s,%s)' % (R('give_or_get', 'met'), R('give_or_get', 'period'), THIS2), 'int')]),
    FORM('obligation_sheet', 'Obligation Sheet', 'Obligation record', 'obligations.ob_id', F(('Item', 'obligations.item'), ('Kind', 'obligations.kind'), ('Due date', 'obligations.due_date'), ('Owner', 'obligations.owner'), ('Done on', 'obligations.done_on'), ('Status', 'obligations.status'),
                                                                                           ('Done on time (1 yes, 0 no)', 'obligations.on_time')) + [
        FF('Days from the due date to done', '%s-%s' % (LK('obligations', 'ob_id', 'done_on'), LK('obligations', 'ob_id', 'due_date')), 'int'),
        FF('Repeats every, months', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('ob_kinds', 'repeats_months'), LK('obligations', 'ob_id', 'kind'), R('ob_kinds', 'kind')), 'int'),
        FF('Obligations of this kind', 'COUNTIFS(%s,%s)' % (R('obligations', 'kind'), LK('obligations', 'ob_id', 'kind')), 'int')]),
    FORM('policy_sheet', 'Policy Review Sheet', 'Review of a kind of obligation', 'ob_kinds.kind', F(('Kind', 'ob_kinds.kind'), ('Repeats every, months', 'ob_kinds.repeats_months'), ('Owner', 'ob_kinds.owner')) + [
        FF('Items done', 'COUNTIFS(%s,{pick},%s,%s)' % (R('obligations', 'kind'), R('obligations', 'status'), OBDONE), 'int'), FF('Items still open', 'COUNTIFS(%s,{pick},%s,"<>"&%s,%s,"<>")' % (R('obligations', 'kind'), R('obligations', 'status'), OBDONE, R('obligations', 'ob_id')), 'int'),
        FF('Items done on time', 'SUMIFS(%s,%s,{pick})' % (R('obligations', 'on_time'), R('obligations', 'kind')), 'int'),
        FF('Last done on', 'SUMPRODUCT(MAX((%s={pick})*%s))' % (R('obligations', 'kind'), R('obligations', 'done_on')), 'date'),
        FF('Next open due date', 'IFERROR(1/SUMPRODUCT(MAX((%s={pick})*(%s<>%s)*(%s>0)/(%s+(%s=0)))),"")' % (R('obligations', 'kind'), R('obligations', 'status'), OBDONE, R('obligations', 'due_date'), R('obligations', 'due_date'), R('obligations', 'due_date')), 'date')]),
    FORM('pack_sheet', 'Board Pack Sheet', 'Board pack item', 'board_pack.item', F(('Item', 'board_pack.item'), ('Unit', 'board_pack.unit'), ('Typed number', 'board_pack.typed'), ('Last month', 'board_pack.last'), ('Number', 'board_pack.number'), ('Trend', 'board_pack.trend'), ('Flag', 'board_pack.flag')) + [
        FF('Items missing from the pack', 'COUNTIFS(%s,%s)' % (R('board_pack', 'flag'), c2('Missing')), 'int'), FF('Items to act on', 'COUNTIFS(%s,%s)' % (R('board_pack', 'flag'), c2('Act')), 'int'),
        FF('Items to watch', 'COUNTIFS(%s,%s)' % (R('board_pack', 'flag'), c2('Watch')), 'int'), FF('Change from last month', '%s-%s' % (LK('board_pack', 'item', 'number'), LK('board_pack', 'item', 'last')), 'num')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('roster_doc', 'Board Roster Page', 'Board roster entry with terms', 'board.member_id', [
        'Board roster of {set:org}, dated {today}. Member: {col:board.name} ({col:board.member_id}). Role: {col:board.role}. Committee: {col:board.committee}.',
        'Term: {col:board.term_start} to {col:board.term_end}. Terms served: {col:board.terms_served}. Months to the end of the term: {col:board.months_left}.',
        'Skills: {col:board.skill} and {col:board.skill2}. Contact: {col:board.phone}, {col:board.email}.',
        'Attendance this year: {col:board.att_share}. Gifts this year: {col:board.gifts_total}. Given and raised against the give or get target: {col:board.gg_total} of {col:board.gg_target}.'], ['Board secretary', 'Chair'], NOTE),
    DOC('notice_doc', 'Terms Ending Notice', 'Notice that a term is ending', 'terms_ending.member', [
        'Notice of {set:org}, dated {today}. To: {col:terms_ending.member}, {col:terms_ending.role}.',
        'Your term ends on {col:terms_ending.term_end}, in {col:terms_ending.months_left} months. You have served {col:terms_ending.terms_served} terms and the most for your role is {col:terms_ending.max_terms}. {col:terms_ending.can_renew}.',
        'Please tell the chair before the next board meeting whether you wish to renew, if your rules allow it. We will list the skills the board needs ({col:terms_ending.skill} among them) and plan the handover.',
        'Thank you for your time and care for the work of the board.'], ['Chair', 'Member'], NOTE),
    DOC('brief_doc', 'Board Recruitment Brief', 'Brief for recruiting a board member with one skill', 'skills.skill', [
        'Board recruitment brief of {set:org}, dated {today}. Skill needed: {col:skills.skill}.',
        'We want {col:skills.needed} members who hold this skill. What it is for: {col:skills.note}.',
        'Time: a board meeting about every month, one committee and a short yearly declaration of interests. Giving: each member gives or raises a set amount a year, your own policy.',
        'To find out more, ask the chair for a call and a visit to a program. Everyone is asked to read the policies first.'], ['Chair', 'Nominating committee'], NOTE),
    DOC('matrix_doc', 'Skills Matrix Page', 'Skills matrix page for one skill and date', 'skills_matrix.row_id', [
        'Skills matrix of {set:org}, dated {today}. Skill: {col:skills_matrix.skill}. Point in time: {col:skills_matrix.when} ({col:skills_matrix.date_at}).',
        'Members who hold the skill and are still serving: {col:skills_matrix.members}. Members you need: {col:skills_matrix.needed}. Gap: {col:skills_matrix.gap}. Flag: {col:skills_matrix.flag}.',
        'Members who leave with this skill between now and then: {col:skills_matrix.leaving}.',
        'Use one page for each skill that has a gap, and bring it to the nominating committee.'], ['Chair', 'Governance committee chair'], NOTE),
    DOC('agenda_doc', 'Meeting Agenda', 'Agenda for a board meeting', 'meeting_plan.meeting_id', [
        'Agenda of the board of {set:org}. Meeting {col:meeting_plan.meeting_id} on {col:meeting_plan.date} at {col:meeting_plan.time}. Papers go out by {col:meeting_plan.papers_due}.',
        '1. Welcome, apologies and the quorum ({col:meeting_plan.quorum_number} members needed, {col:meeting_plan.confirmed} confirmed). 2. Declarations of interest. 3. Minutes of the last meeting and actions.',
        '4. Finance report and the cash forecast. 5. Fundraising and grants. 6. Programs and volunteers. 7. Governance: obligations and policy reviews. 8. Other business ({col:meeting_plan.agenda_items} items in all). 9. Date of the next meeting.',
        'Papers: {col:meeting_plan.papers}. Please read them before the meeting and send questions to the chair.'], ['Chair', 'Secretary'], NOTE),
    DOC('attendance_doc', 'Meeting Attendance Record', 'Attendance record for one meeting', 'meetings.meeting_id', [
        'Attendance record of {set:org}, dated {today}. Meeting {col:meetings.meeting_id}, {col:meetings.kind}, on {col:meetings.date} at {col:meetings.start_time}.',
        'Members expected: {col:meetings.expected}. Members present: {col:meetings.present}. Attendance share: {col:meetings.share}. Quorum number: {col:meetings.quorum_number}. Quorum met: {col:meetings.quorum_met}.',
        'List each member below with present, apologies or absent: ____________________________________________.',
        'The secretary confirms that this record is correct.'], ['Secretary', 'Chair'], NOTE),
    DOC('minutes_doc', 'Minutes Record', 'Minutes record for one meeting', 'meetings.meeting_id', [
        'Minutes of the {col:meetings.kind} meeting of {set:org}, meeting {col:meetings.meeting_id}, held on {col:meetings.date} at {col:meetings.start_time}. Present: {col:meetings.present} of {col:meetings.expected}. Quorum met: {col:meetings.quorum_met}.',
        'Declarations of interest made at the start: ____________________________________________.',
        'Decisions: ____________________________________________. Actions, who and by when: ____________________________________________.',
        'Minutes final: {col:meetings.minutes_ready}. The chair and the secretary sign when the board has agreed the minutes.'], ['Chair', 'Secretary'], NOTE),
    DOC('decl_doc', 'Declaration of Interests Form', 'Yearly declaration of interests', 'declarations.decl_id', [
        'Declaration of interests, {col:declarations.year}, {set:org}. Member: {col:declarations.member} ({col:declarations.member_id}). Due date: {col:declarations.due_date}.',
        'I confirm that I have read the conflict of interest policy. I declare the following interests that could be seen to affect my work as a board member: ____________________________________________. If I have none, I write none.',
        'I will tell the chair as soon as a new interest arises, and I will leave the room when the board decides on a matter where I have an interest. Items declared this year: {col:declarations.items_declared}.',
        'Check your local rules for how long to keep this form and who may see it.'], ['Member', 'Chair'], NOTE),
    DOC('decl_summary_doc', 'Declarations Summary', 'Declarations summary for one member and year', 'decl_status.row_id', [
        'Declarations summary of {set:org}, dated {today}. Member: {col:decl_status.member}. Year: {col:decl_status.year}.',
        'Due date: {col:decl_status.due}. Filed on: {col:decl_status.filed}. Items declared: {col:decl_status.items}. Days late: {col:decl_status.days_late}. Flag: {col:decl_status.flag}.',
        'Bring the open declarations to the governance committee and ask the chair to follow up with each member.',
        'This page is a record for the board and is not legal advice.'], ['Governance committee chair', 'Chair'], NOTE),
    DOC('gog_letter_doc', 'Give or Get Letter', 'Give or get letter to a member', 'give_or_get.row_id', [
        'Letter of {set:org}, dated {today}. To: {col:give_or_get.member}.',
        'Thank you for what you give and raise for our work. Under the board policy each member gives or raises {col:give_or_get.target} a year. This year so far you have given {col:give_or_get.given} and raised {col:give_or_get.raised}, together {col:give_or_get.total}. Remaining: {col:give_or_get.remaining}.',
        'Your status is {col:give_or_get.status}. If you would like a list of people to ask, or help with an ask, the development manager will meet you.',
        'The board agrees the policy each year, and we are grateful for your support. Please keep this letter as a record.'], ['Chair', 'Fundraising committee chair'], NOTE),
    DOC('ob_year_doc', 'Obligation Calendar Page', 'Obligation calendar entry', 'ob_calendar.ob_id', [
        'Obligation calendar of {set:org}, dated {today}. Item {col:ob_calendar.ob_id}: {col:ob_calendar.item}. Kind: {col:ob_calendar.kind}. Owner: {col:ob_calendar.owner}.',
        'Due date: {col:ob_calendar.due_date}. Done on: {col:ob_calendar.done_on}. Days away: {col:ob_calendar.days_away}. Flag: {col:ob_calendar.flag}.',
        'Obligations overdue now: {col:ob_calendar.over_n}. Due this month: {col:ob_calendar.month_n}. Due in the next 30 days: {col:ob_calendar.due30_n}.',
        'Check your local rules for the exact dates and what each item needs; ask your accountant about returns.'], ['Chair', 'Executive director'], NOTE),
    DOC('pack_doc', 'Board Pack Page', 'Board pack item', 'board_pack.item', [
        'Board pack of {set:org} for the meeting on {col:board_pack.pack_date}. Item: {col:board_pack.item}.',
        'Number: {col:board_pack.number} ({col:board_pack.unit}). Last month: {col:board_pack.last}. Trend: {col:board_pack.trend}. Flag: {col:board_pack.flag}.',
        'Items missing from the pack: {col:board_pack.missing_n}. First missing item: {col:board_pack.first_missing}.',
        'Add a short note for each item that is flagged Act or Watch: what changed and what the board is asked to do.'], ['Executive director', 'Chair'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('prep_chk', 'Board Meeting Preparation', 'meetings', 'meetings.date', [('Set the agenda with the chair', -21), ('Ask members to confirm they can come', -14), ('Collect the reports and the finance numbers', -10), ('Build the board pack', -8), ('Send the papers', -7),
                                                                                 ('Check the quorum count', -3), ('Book the room', -3), ('Remind members the day before', -1)]),
    CHK('day_chk', 'Board Meeting Day', 'meetings', 'meetings.date', [('Open the room and test the equipment', 0), ('Take attendance and check the quorum', 0), ('Ask for declarations of interest', 0), ('Record decisions and who does what', 0), ('Note the time the meeting closes', 0), ('Confirm the next meeting date', 0)]),
    CHK('after_chk', 'After the Meeting', 'meetings', 'meetings.date', [('Enter attendance', 0), ('Write the draft minutes', 3), ('Send the draft to the chair', 5), ('Record the actions with an owner and a date', 7), ('Send the minutes to members', 10), ('Make the minutes final at the next meeting', 30), ('File the final minutes', 31)]),
    CHK('decl_chk', 'Yearly Declarations', 'declarations', 'declarations.due_date', [('Send the form to every member', -30), ('Remind members who have not filed', -14), ('Collect the forms', 0), ('Record the date filed and the items declared', 1), ('Chase members who are overdue', 7),
                                                                                    ('Report the result to the governance committee', 14), ('Keep the forms where your local rules say', 21)]),
    CHK('terms_chk', 'Terms and Recruitment', 'board', 'board.term_end', [('Check the term limit with the member', -180), ('Ask the member if they will renew', -150), ('List the skills you will lose', -120), ('Ask the nominating committee to find candidates', -100), ('Hold a call with each candidate', -60),
                                                                          ('Invite the candidate to a meeting as a guest', -45), ('Vote at the board meeting', -21), ('Thank the member who leaves', 0)]),
    CHK('onboard_chk', 'New Board Member Onboarding', 'board', 'board.term_start', [('Send a welcome note', 0), ('Share the roster and the calendar', 1), ('Share the policies to read', 3), ('Ask for the declaration of interests', 7), ('Explain the give or get policy', 14), ('Assign a committee', 14),
                                                                                    ('Pair the member with a buddy', 14), ('Ask how the first meeting went', 45)]),
    CHK('committee_chk', 'Committee Meeting', 'meetings', 'meetings.date', [('Set the agenda with the committee chair', -14), ('Send the papers', -7), ('Confirm the quorum', -2), ('Hold the meeting and take notes', 0), ('Send the notes and the actions', 3), ('Report to the next board meeting', 14)]),
    CHK('gog_chk', 'Give or Get Round', 'meetings', 'meetings.date', [('Set the target for each member', 0), ('Share last year\'s numbers', 3), ('Ask each member for a plan', 10), ('Record money given and money raised', 30), ('Send a thank-you note', 31), ('Check progress at a board meeting', 60), ('Report the result to the board', 90)]),
    CHK('oblig_chk', 'Obligation Calendar Review', 'obligations', 'obligations.due_date', [('Check the date and the owner', -60), ('Start the work', -45), ('Check what the owner needs', -30), ('Remind the owner', -14), ('Mark it done on the day it is done', 0), ('Set the next date', 3)]),
    CHK('policy_chk', 'Policy Review', 'obligations', 'obligations.due_date', [('Read the current policy', -45), ('List what changed in practice', -35), ('Check your local rules', -30), ('Draft the changes', -21), ('Send to the committee', -14), ('Ask the board to approve', 0), ('Share with staff and volunteers', 7), ('Set the next review date', 7)]),
    CHK('self_chk', 'Yearly Board Self-Review', 'meetings', 'meetings.date', [('Send a short questionnaire', -30), ('Collect the answers', -14), ('Summarise the answers', -7), ('Discuss at the board meeting', 0), ('Agree three changes', 0), ('Review progress six months later', 180)]),
    CHK('founder_chk', 'Founder First Board', 'board', 'board.term_start', [('Write down what the board is for', 0), ('Ask two people you trust to join', 7), ('Agree the roles: chair, treasurer and secretary', 14), ('Hold a first meeting and set a quorum', 28), ('Write down who may sign and who may spend', 30),
                                                                           ('Ask each member for a declaration of interests', 35), ('Set a meeting calendar for the year', 42), ('Ask your accountant what your local rules need', 45)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
CH, TR, VP, SE, EDN = FIRST(D.CHAIR['name']), FIRST(D.TREAS['name']), FIRST(D.VICE['name']), FIRST(D.SECR['name']), fn(OWNER)
ACCN, BRK, VN = fn(D.TEAMID['NP-09']['name']), fn(D.TEAMID['NP-11']['name']), fn(D.VOL['name'])
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('bm_next', 'Board member: the next meeting', 'board', 'board.phone', 'Hello {name}, the next board meeting is on {next_date} at {next_time}. {org}'),
    M('bm_papers', 'Board member: papers are ready', 'board', 'board.phone', 'Hello {name}, the papers for {next_date} are ready. Please read them before the meeting. {org}'),
    M('bm_confirm', 'Board member: please confirm', 'board', 'board.phone', 'Hello {name}, please confirm that you can attend on {next_date}. A short yes or no is enough. {org}'),
    M('bm_quorum', 'Board member: we need a quorum', 'board', 'board.phone', 'Hello {name}, we need a quorum on {next_date} and {confirmed} members have confirmed so far. Can you come? {org}'),
    M('bm_minutes', 'Board member: minutes are ready', 'board', 'board.phone', 'Hello {name}, the minutes of {last_date} are ready for your review. {org}'),
    M('bm_renew', 'Board member: your term is ending', 'board', 'board.phone', 'Hello {name}, your term ends on {term_end}. Would you like to renew? {org}'),
    M('bm_thanks', 'Board member: thank you for your service', 'board', 'board.phone', 'Hello {name}, thank you for your service on the board. Your term ended on {term_end}. {org}'),
    M('bm_welcome', 'Board member: welcome to the board', 'board', 'board.phone', 'Hello {name}, welcome to the board. Your first meeting is on {next_date} at {next_time}. {org}'),
    M('bm_decl', 'Board member: file your declaration', 'board', 'board.phone', 'Hello {name}, please file your declaration of interests by {decl_due}. {org}'),
    M('bm_decl_ok', 'Board member: declaration recorded', 'board', 'board.phone', 'Hello {name}, your declaration is recorded. Thank you. {org}'),
    M('bm_attend', 'Board member: your attendance this year', 'board', 'board.phone', 'Hello {name}, you have attended {att_share} of meetings this year. Can we help in any way? {org}'),
    M('bm_gifts', 'Board member: your gifts this year', 'board', 'board.phone', 'Hello {name}, your gifts this year total {gifts_total}. Thank you. {org}'),
    M('bm_gog', 'Board member: give or get progress', 'board', 'board.phone', 'Hello {name}, your give or get progress is {gg_total} of {gg_target}. {org}'),
    M('bm_committee', 'Board member: please join a committee', 'board', 'board.phone', 'Hello {name}, please join the {committee} committee. It meets next on {committee_date}. {org}'),
    M('ch_attend', 'Chair: members under attendance', 'attendance_member', 'attendance_member.chair_phone', 'Hello %s, {under_n} members are under the attendance share of {attend_min} this year. {org}' % CH),
    M('ch_seats', 'Chair: seats are open', 'seats', 'seats.chair_phone', 'Hello %s, {vacant_n} seats are open. The skill to recruit for is {gap_skill}. {org}' % CH),
    M('ch_terms', 'Chair: terms are ending', 'terms_ending', 'terms_ending.chair_phone', 'Hello %s, {ending_n} terms end soon. Please look at the Terms Ending Ranker. {org}' % CH),
    M('ch_pack', 'Chair: the board pack is ready', 'board_pack', 'board_pack.chair_phone', 'Hello %s, the board pack for {pack_date} is ready. {org}' % CH),
    M('ch_ob_month', 'Chair: obligations due this month', 'ob_calendar', 'ob_calendar.chair_phone', 'Hello %s, {month_n} obligations are due this month. {org}' % CH),
    M('ch_ob_over', 'Chair: obligations are overdue', 'ob_calendar', 'ob_calendar.chair_phone', 'Hello %s, {over_n} obligations are overdue. The oldest is {oldest_item}. {org}' % CH),
    M('ch_minutes', 'Chair: minutes are not final', 'meetings', 'meetings.chair_phone', 'Hello %s, the minutes of {notfinal_n} meetings are not final. {org}' % CH),
    M('fin_budget', 'Finance chair: budget against actual', 'meeting_plan', 'meeting_plan.treas_phone', 'Hello %s, the budget against actual for the meeting on {date} is attached. {org}' % TR),
    M('gov_decl', 'Governance chair: declarations', 'declarations', 'declarations.gov_phone', 'Hello %s, declarations filed are {filed_n} of {total_n}. {org}' % CH),
    M('fund_share', 'Fundraising chair: board giving', 'board_share', 'board_share.fund_chair_phone', 'Hello %s, board giving is {share} of members: {gave} of {members}. {org}' % VP),
    M('ed_policy', 'Executive director: a policy is due', 'obligations', 'obligations.ed_phone', 'Hello %s, {item} is due for review on {due_date}. {org}' % EDN),
    M('ed_ob30', 'Executive director: due in 30 days', 'ob_calendar', 'ob_calendar.ed_phone', 'Hello %s, {due30_n} obligations are due in the next 30 days. {org}' % EDN),
    M('ed_insurance', 'Executive director: insurance renewal', 'obligations', 'obligations.ed_phone', 'Hello %s, the insurance renewal ({item}) is due on {due_date}. {org}' % EDN),
    M('broker', 'Insurance broker: our renewal is due', 'obligations', 'obligations.broker_phone', 'Hello %s, our renewal ({item}) is due on {due_date}. Please send terms. {org}' % BRK),
    M('acc_return', 'Accountant: our yearly return', 'obligations', 'obligations.acc_phone', 'Hello %s, the date for our yearly information return is {due_date}. What do you need from us? {org}' % ACCN),
    M('acc_budget', 'Accountant: budget approved', 'meetings', 'meetings.acc_phone', 'Hello %s, the board approved the budget on {date}. {org}' % ACCN),
    M('sec_agenda', 'Board secretary: send the agenda', 'meeting_plan', 'meeting_plan.secretary_phone', 'Hello %s, please send the agenda for {date}. {org}' % SE),
    M('cand_call', 'Candidate: a call is set', 'seats', 'seats.chair_phone', 'Hello, thank you for your interest in the board. A call is set for {call_on}. {org}'),
    M('cand_guest', 'Candidate: invitation as a guest', 'seats', 'seats.chair_phone', 'Hello, we would like to invite you to a board meeting on {next_date} as a guest. {org}'),
    M('vol_room', 'Volunteer: help set up the room', 'meeting_plan', 'meeting_plan.vol_phone', 'Hello %s, could you help set up the room on {date}? {org}' % VN),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
CF, CR_, CG = [ 'COUNTIFS(%s,%s,%s,1)' % (R('board', 'committee'), tok('committee', c), R('board', 'serving')) for c in COMMITTEES]
SERV = 'SUM(%s)' % R('board', 'serving')
def ATT(yr): return 'IFERROR(SUMIFS(%s,%s,%s)/COUNTIFS(%s,%s),0)' % (R('attendance', 'present'), R('attendance', 'year'), yr, R('attendance', 'year'), yr)
def MWHEN(w, extra): return 'COUNTIFS(%s,%s,%s%s)' % (R('skills_matrix', 'when'), tok('when', w), R('skills_matrix', 'members'), extra)
kpis = [
    KPI('Board members now', SERV, 'int'), KPI('Seats set by your rules', '{set:board_seats}', 'int'), KPI('Seats vacant', 'MAX(0,{set:board_seats}-%s)' % SERV, 'int'), KPI('Terms ending soon', 'SUM(%s)' % R('board', 'ends_soon'), 'int'),
    KPI('Members on a second term or more', 'COUNTIFS(%s,1,%s,">=2")' % (R('board', 'serving'), R('board', 'terms_served')), 'int'), KPI('Average terms served', 'IFERROR(AVERAGEIFS(%s,%s,1),0)' % (R('board', 'terms_served'), R('board', 'serving')), 'num'),
    KPI('Members on the smallest committee', 'MIN(%s,%s,%s)' % (CF, CR_, CG), 'int'), KPI('Skills with no member in 12 months', MWHEN('In 12 months', ',0'), 'int'), KPI('Skills with one member in 12 months', MWHEN('In 12 months', ',1'), 'int'),
    KPI('Meetings this year', 'COUNTIFS(%s,%s)' % (R('meetings', 'year'), YN), 'int'), KPI('Next meeting date', 'IFERROR(INT(SMALL(%s,1)),"")' % R('meetings', 'next_key'), 'date'),
    KPI('Days to the next meeting', 'IFERROR(INT(SMALL(%s,1))-{today},0)' % R('meetings', 'next_key'), 'int'),
    KPI('Meetings held with quorum this year', 'COUNTIFS(%s,%s,%s,%s,%s,%s)' % (R('meetings', 'status'), HELD, R('meetings', 'quorum_met'), YES, R('meetings', 'year'), YN), 'int'),
    KPI('Meetings without quorum this year', 'COUNTIFS(%s,%s,%s,%s,%s,%s)' % (R('meetings', 'status'), HELD, R('meetings', 'quorum_met'), NO, R('meetings', 'year'), YN), 'int'),
    KPI('Minutes not final', 'COUNTIFS(%s,%s,%s,%s)' % (R('meetings', 'status'), HELD, R('meetings', 'minutes_ready'), NO), 'int'),
    KPI('Attendance this year', ATT(YN), 'pct'), KPI('Attendance last year', ATT(YN + '-1'), 'pct'),
    KPI('Members under the attendance setting', 'COUNTIFS(%s,%s,%s,%s)' % (R('attendance_member', 'period'), THIS3, R('attendance_member', 'flag'), c1('Under the setting')), 'int'),
    KPI('Members who gave this year', 'SUMIFS(%s,%s,%s)' % (R('board_giving', 'gave'), R('board_giving', 'period'), THIS3), 'int'),
    KPI('Share of the board that gives', 'IFERROR(SUMIFS(%s,%s,%s)/%s,0)' % (R('board_giving', 'gave'), R('board_giving', 'period'), THIS3, SERV), 'pct'),
    KPI('Board giving this year', 'SUMIFS(%s,%s,%s)' % (R('board_giving', 'total'), R('board_giving', 'period'), THIS3), 'money'),
    KPI('Give or get target met, members', 'SUMIFS(%s,%s,%s)' % (R('give_or_get', 'met'), R('give_or_get', 'period'), THIS2), 'int'),
    KPI('Give or get remaining', 'SUMIFS(%s,%s,%s)' % (R('give_or_get', 'remaining'), R('give_or_get', 'period'), THIS2), 'money'),
    KPI('Declarations filed this year', 'COUNTIFS(%s,%s,%s,%s)' % (R('declarations', 'year'), THIS3, R('declarations', 'status'), FILED), 'int'),
    KPI('Declarations overdue', 'COUNTIFS(%s,%s,%s,%s)' % (R('declarations', 'year'), THIS3, R('declarations', 'status'), tok('dclstatus', 'Overdue')), 'int'),
    KPI('Obligations due next 30 days', 'COUNTIFS(%s,">=0",%s,"<=30")' % (R('obligations', 'days_away'), R('obligations', 'days_away')), 'int'),
    KPI('Obligations overdue now', 'SUM(%s)' % R('obligations', 'open_late'), 'int'),
    KPI('Obligations done on time this year', 'COUNTIFS(%s,1,%s,">="&%s)' % (R('obligations', 'on_time'), R('obligations', 'done_on'), JAN1), 'int'),
    KPI('Days to the next obligation', 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),0)' % (R('obligations', 'days_away'), R('obligations', 'days_away')), 'int'),
    KPI('Items missing from the board pack', 'COUNTIFS(%s,%s)' % (R('board_pack', 'flag'), c2('Missing')), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Board Dashboard", "kpis": kpis,
    "monthly": {"title": "Members present, meetings held and obligations", "date": "attendance.date", "series": [
        {"label": "Members present", "sum": "attendance.present", "date": "attendance.date"}, {"label": "Meetings held", "sum": "meetings.held", "date": "meetings.date"},
        {"label": "Obligations due", "sum": "obligations.one", "date": "obligations.due_date"}, {"label": "Obligations done", "sum": "obligations.done_n", "date": "obligations.done_on"}]},
    "breakdowns": [{"title": "Attendance by status", "by": "attendance.status", "value": "attendance.present", "agg": "count"}, {"title": "Meetings by kind", "by": "meetings.kind", "value": "meetings.present", "agg": "count"},
                   {"title": "Declarations by status", "by": "declarations.status", "value": "declarations.items_declared", "agg": "count"}, {"title": "Obligations by status", "by": "obligations.status", "value": "obligations.one", "agg": "count"}]}

def W(c, o, v): return (c, o, v)
insights = {"filters": [{"label": "Committee", "list": "committee"}, {"label": "Board role", "list": "brole"}, {"label": "Meeting kind", "list": "mkind"}],
    "gauges": [
        {"title": "Seats filled against the seat count", "num": AGG('sum', 'seats', 'seats.filled'), "den": AGG('count', 'seats')},
        {"title": "Attendance, share of meetings", "num": AGG('sum', 'attendance_member', 'attendance_member.present', where=[W('period', '=', THIS3)]), "den": AGG('sum', 'attendance_member', 'attendance_member.meetings', where=[W('period', '=', THIS3)])},
        {"title": "Declarations filed this year", "num": AGG('count', 'declarations', where=[W('year', '=', THIS3), W('status', '=', FILED)]), "den": AGG('count', 'declarations', where=[W('year', '=', THIS3)])},
        {"title": "Board members who give", "num": AGG('sum', 'board_giving', 'board_giving.gave', where=[W('period', '=', THIS3)]), "den": AGG('count', 'board_giving', where=[W('period', '=', THIS3)])},
        {"title": "Obligations done on time", "num": AGG('sum', 'obligations', 'obligations.on_time'), "den": AGG('sum', 'obligations', 'obligations.done_n')},
        {"title": "Give or get target met", "num": AGG('sum', 'give_or_get', 'give_or_get.met', where=[W('period', '=', THIS2)]), "den": AGG('count', 'give_or_get', where=[W('period', '=', THIS2)])}],
    "charts": [
        CHART('Board members by role', 'bar', 'board.role', [AGG('sum', 'board', 'board.serving', label='Members')]),
        CHART('Board members by committee', 'bar', 'board.committee', [AGG('sum', 'board', 'board.serving', label='Members')]),
        CHART('Terms ending by year', 'column', 'terms_ending.ends_in', [AGG('count', 'terms_ending', label='Terms ending')]),
        CHART('Terms served by member', 'bar', 'terms_ending.member', [AGG('sum', 'terms_ending', 'terms_ending.terms_served', label='Terms served')]),
        CHART('Skills held by skill', 'bar', 'skills_matrix.skill', [AGG('sum', 'skills_matrix', 'skills_matrix.members', where=[W('when', '=', tok('when', 'Now'))], label='Members with the skill')]),
        CHART('Skills needed by skill', 'bar', 'skills.skill', [AGG('sum', 'skills', 'skills.needed', label='Members needed')]),
        CHART('Meetings per year', 'column', 'meetings.period', [AGG('count', 'meetings', label='Meetings')]),
        CHART('Meetings by kind', 'bar', 'meetings.kind', [AGG('count', 'meetings', label='Meetings')]),
        CHART('Members present per month', 'column', 'month', [AGG('sum', 'meetings', 'meetings.present', date='meetings.date', label='Members present')]),
        CHART('Attendance share by member, this year', 'bar', 'attendance_member.member', [AGG('avg', 'attendance_member', 'attendance_member.share', where=[W('period', '=', THIS3)], label='Attendance share')]),
        CHART('Attendance share per year', 'line', 'attendance_member.period', [AGG('avg', 'attendance_member', 'attendance_member.share', label='Attendance share')]),
        CHART('Quorum met by year', 'column', 'meetings.period', [AGG('count', 'meetings', where=[W('quorum_met', '=', YES)], label='Meetings with quorum')]),
        CHART('Present by meeting kind', 'bar', 'meetings.kind', [AGG('sum', 'meetings', 'meetings.present', label='Members present')]),
        CHART('Board giving by member, this year', 'bar', 'board_giving.member', [AGG('sum', 'board_giving', 'board_giving.total', where=[W('period', '=', THIS3)], label='Given')]),
        CHART('Board giving per year', 'column', 'board_giving.period', [AGG('sum', 'board_giving', 'board_giving.total', label='Given')]),
        CHART('Members who gave per year', 'column', 'board_giving.period', [AGG('sum', 'board_giving', 'board_giving.gave', label='Members who gave')]),
        CHART('Declarations by status', 'bar', 'declarations.status', [AGG('count', 'declarations', label='Declarations')]),
        CHART('Declarations by year', 'column', 'declarations.year', [AGG('count', 'declarations', label='Declarations')]),
        CHART('Obligations by kind', 'bar', 'obligations.kind', [AGG('count', 'obligations', label='Obligations')]),
        CHART('Obligations by status', 'bar', 'obligations.status', [AGG('count', 'obligations', label='Obligations')]),
        CHART('Obligations due per month', 'column', 'month', [AGG('count', 'obligations', date='obligations.due_date', label='Obligations due')]),
        CHART('Obligations done per month', 'column', 'month', [AGG('count', 'obligations', date='obligations.done_on', label='Obligations done')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Terms ending ranker", "why": "the terms that end soon in date order, with terms served against your own limit and a verdict to renew or recruit", "where": "Terms Ending Ranker"},
    {"name": "Skills gap finder", "why": "skills held now and after terms end set against the number you need, with the first member to leave named", "where": "Skills Gap Finder"},
    {"name": "Quorum checker", "why": "members confirmed against the quorum your rules need, with the confirmations still needed and a best case", "where": "Quorum Checker"},
    {"name": "Low attendance ranker", "why": "members under the share you expect, ranked by how far they are below it, so the chair knows who to talk to first", "where": "Low Attendance Ranker"},
    {"name": "Give or get tracker", "why": "money given and raised through asks against the target and the share of the year that has passed, with the members who have most left", "where": "Give or Get Tracker"},
    {"name": "Obligation calendar", "why": "policy reviews, insurance renewals, your yearly information return and reports in date order, overdue first", "where": "Obligation Calendar Tool"},
    {"name": "Board pack builder", "why": "cash, months of reserve, pipeline, attendance and obligations on one page, with the first missing item named", "where": "Board Pack Builder"},
    {"name": "Succession planner", "why": "terms ending each year for three years, with the seats and skills at risk and a warning when too many end together", "where": "Succession Planner"},
    {"name": "Declaration tracker", "why": "who has filed this year, who is overdue and how many items were declared, with the most overdue member named", "where": "Declaration Tracker"},
    {"name": "Policy and renewal planner", "why": "the next due date of each kind of obligation with the date to start, so a renewal never arrives as a surprise", "where": "Policy and Renewal Planner"}]
competitors = [
    {"what": "donor-management software", "lacks": "tracks gifts well but has no board roster, no term dates, no quorum or attendance and no declarations of interest"},
    {"what": "generic meeting minutes templates", "lacks": "give a page to write on but never count who attended, flag a missing quorum or track minutes that are not final"},
    {"what": "single-purpose obligation calendar templates", "lacks": "list dates but do not rank them, show who owns them or join them to the board pack"},
    {"what": "nonprofit governance add-ons", "lacks": "cost a fee for each member and give no skills matrix, no succession view and no give or get progress from your own gift log"}]
guide = [
    'Open Start and type your organization name, the seats you set by your own rules, the quorum number, the attendance share you expect and the give or get amount.',
    'List every board member on Board Members with role, committee, term dates, terms served and two skills; one former member row shows how a past member is kept.',
    'Set the roles and term limits on Board Roles, the committees on Committees and the skills you need on Skills; the roster and the matrix fill in.',
    'Record each meeting on Meetings with date, time, kind, members expected and present, quorum and minutes; enter who came on Attendance.',
    'Add one row for each member and year on Attendance by Member, Board Giving and Give or Get Progress; shares, flags and ranks fill in.',
    'Type each member\'s gifts and total from your gift log on Board Giving, and the money raised through their asks on Give or Get Progress.',
    'Record each yearly declaration of interests on Declarations (due date, date filed, items declared) and read the flags on Declaration Status.',
    'List every policy review, insurance renewal, yearly information return and report on Obligations; Obligation Calendar puts them in date order.',
    'Plan each board meeting on Meeting Plan with the agenda items, whether papers are ready and how many members confirmed.',
    'Type the finance numbers on Board Pack; the other items fill in and the pack builder names what is missing.',
    f'Use the {len(tools)} tools for decisions: terms ending, skills gaps, quorum, attendance, give or get, declarations, obligations and the pack.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in. A founder with volunteers can use a three-person board in the same sheets.']
listing = {"title": "Nonprofit Board and Governance Excel Template: Board Roster, Terms, Quorum, Attendance, Give or Get, Obligations",
    "headline": "Run your board well: terms, quorum, attendance, giving and every due date",
    "tags": ["board governance", "nonprofit board", "board roster", "term limits", "quorum tracker", "board attendance", "give or get", "board pack", "skills matrix", "obligation calendar", "declarations", "nonprofit excel", "charity board"],
    "description": ("Run the board of a small community nonprofit in one Excel workbook. Built for an executive director, a board chair and a secretary who must know who sits on the board, whose term ends, whether the next meeting will have a quorum and which obligations are due. "
        "Board Members holds the roster with role, committee, term dates, terms served and two skills, and the months to each term end. Seats shows filled and vacant seats against the seat count you set, and Terms Ending ranks the terms by date with the term limit of each role. Skills Matrix sets the skills members hold now, in 6 months and in 12 months against the number you need.\n\n"
        "Meetings, Attendance and Meeting Plan track quorum, minutes that are not final, papers and confirmations. Attendance by Member flags members under the share you expect. Board Giving and Give or Get Progress read personal giving from your gift log against a give or get target. Declarations and Declaration Status show who has filed. Obligations and Obligation Calendar list policy reviews, insurance renewals and your yearly information return, overdue first. "
        f"{len(tools)} tools answer the weekly questions, such as the terms ending ranker, the skills gap finder, the quorum checker, the low attendance ranker, the give or get tracker, the obligation calendar and the board pack builder. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to members, the chair, the accountant and candidates.\n\n"
        "This is part seven of the Nonprofit Organization suite. It works in Excel and Google Sheets, has no macros and no subscription, and comes with a demo copy full of sample data. A founder with volunteers can use it with a three-person board. Probabilities and verdicts are your own estimate. It helps you keep records and is not accounting or legal advice; check your local rules and ask your accountant what you need."),
    "features": ["Board roster with terms and term limits", "Seats filled and vacant", "Skills matrix now, in 6 and 12 months", "Quorum, minutes and papers for each meeting", "Attendance by member against your share", "Give or get progress from your gift log",
                 "Declarations of interest by member and year", "Obligation calendar with overdue first", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Works for a founder with a three-person board"]}
for _t in tables: _t['rows'] = max(50, _t['rows'])
s = spec(id=f'{SUITE}-p7', slug='nonprofit-board', profession='Nonprofit Organization', name='Board and Governance',
         tagline='Run your board well: terms, quorum, attendance, giving and every due date', price_usd=29,
         colors={"primary": "#22577A", "accent": "#F2A541"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Board and governance"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'np7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
