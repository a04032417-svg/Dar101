"""Nonprofit Organization suite - part 6: Volunteers and Members."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np6_lists import *
from np6_tables import settings, tables
from np6_tools import tools
import np6_data as D

SUITE = 'fx-20261115-nonprofit'
NOTE = "Sample wording: adapt it to your own organization and check your local rules."
YS = 'DATE(YEAR({today}),1,1)'
YSL = 'DATE(YEAR({today})-1,1,1)'
WORKED = tok('shstatus', 'Worked'); NOSHOW = tok('shstatus', 'No-show'); ACTIVE = tok('vstatus', 'Active'); LAPSED = tok('vstatus', 'Lapsed')
def R(t, c): return '{range:%s.%s}' % (t, c)
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def MSW(label): return 'INDEX({range:member_switch.setting},MATCH(%s,{range:member_switch.item},0))' % tok('mitem', label)
ON = MSW('Use membership pages')

# ------------------------------------------------------------------ forms (12)
V = lambda c: LK('volunteers', 'volunteer_id', c)
M = lambda c: LK('members', 'member_id', c)
forms = [
    FORM('signup_sheet', 'Volunteer Sign-up Sheet', 'New volunteer sign-up', 'volunteers.volunteer_id', F(
        ('Name', 'volunteers.name'), ('Phone', 'volunteers.phone'), ('Email', 'volunteers.email'), ('Role', 'volunteers.role'), ('Program or area', 'volunteers.program'), ('Joined', 'volunteers.joined'),
        ('Status', 'volunteers.status'), ('Availability', 'volunteers.availability'), ('Donor ID, if also a donor', 'volunteers.donor_id')) + [
        FF('Days since joining', '{today}-%s' % V('joined'), 'int'), FF('Shifts worked so far', V('shifts_n'), 'int'), FF('Hours worked so far', V('hours_worked'), 'hours')]),
    FORM('availability_sheet', 'Volunteer Availability Sheet', 'Availability of one volunteer', 'volunteers.volunteer_id', F(
        ('Name', 'volunteers.name'), ('Phone', 'volunteers.phone'), ('Role', 'volunteers.role'), ('Availability now', 'volunteers.availability'), ('Status', 'volunteers.status'), ('Last shift', 'volunteers.last_shift')) + [
        FF('Days since the last shift', V('days_since'), 'int'), FF('Hours this year', V('hours_year'), 'hours'),
        FF('Active with the same availability', 'COUNTIFS(%s,%s,%s,%s)' % (R('volunteers', 'availability'), V('availability'), R('volunteers', 'status'), ACTIVE), 'int')]),
    FORM('slot_sheet', 'Shift Slot Sheet', 'One planned shift slot', 'slots.slot_id', F(
        ('Date', 'slots.date'), ('Weekday', 'slots.weekday'), ('Program or area', 'slots.program'), ('Shift', 'slots.shift'), ('Role', 'slots.role'), ('People needed', 'slots.needed'), ('People signed up', 'slots.signed_up'), ('Hours', 'slots.hours')) + [
        FF('People short', LK('slots', 'slot_id', 'gap'), 'int'), FF('Share of the need filled', 'IFERROR(%s/%s,0)' % (LK('slots', 'slot_id', 'signed_up'), LK('slots', 'slot_id', 'needed')), 'pct'),
        FF('Volunteer hours the slot needs', '%s*%s' % (LK('slots', 'slot_id', 'needed'), LK('slots', 'slot_id', 'hours')), 'hours')]),
    FORM('shift_signup_sheet', 'Shift Sign-up Sheet', 'Sign a volunteer up to an open shift', 'gaps.slot_id', F(
        ('Date', 'gaps.date'), ('Weekday', 'gaps.weekday'), ('Program or area', 'gaps.program'), ('Shift', 'gaps.shift'), ('Role', 'gaps.role'), ('People needed', 'gaps.needed'), ('People signed up', 'gaps.signed_up'),
        ('People short', 'gaps.gap'), ('Ask first', 'gaps.ask_name'), ('Phone of the person to ask', 'gaps.ask_phone'), ('Action', 'gaps.state')) + [
        FF('Days away', LK('gaps', 'slot_id', 'days_away'), 'int'), FF('People short that week', LK('gaps', 'slot_id', 'week_gap'), 'int')]),
    FORM('shift_report_sheet', 'Shift Report Sheet', 'Report of one shift worked', 'shifts.shift_id', F(
        ('Date', 'shifts.date'), ('Weekday', 'shifts.weekday'), ('Volunteer', 'shifts.volunteer'), ('Role', 'shifts.role'), ('Program or area', 'shifts.program'), ('Shift', 'shifts.shift'), ('Hours', 'shifts.hours'), ('Status', 'shifts.status')) + [
        FF('Hours counted', LK('shifts', 'shift_id', 'worked_hours'), 'hours'),
        FF('Value of the hours, your setting', '%s*{set:volunteer_hour_value}' % LK('shifts', 'shift_id', 'worked_hours'), 'money'),
        FF('Shifts worked by this volunteer', 'COUNTIFS(%s,%s,%s,%s)' % (R('shifts', 'volunteer_id'), LK('shifts', 'shift_id', 'volunteer_id'), R('shifts', 'status'), WORKED), 'int')]),
    FORM('hours_log_sheet', 'Hours Log Sheet', 'Hours log of one volunteer', 'hours_by_volunteer.volunteer_id', F(
        ('Volunteer', 'hours_by_volunteer.volunteer'), ('Role', 'hours_by_volunteer.role'), ('Hours this year', 'hours_by_volunteer.hours_year'), ('Hours last year', 'hours_by_volunteer.hours_last'), ('Hours in all', 'hours_by_volunteer.hours_total'),
        ('Shifts worked', 'hours_by_volunteer.shifts_n'), ('Last shift', 'hours_by_volunteer.last_shift'), ('Rank this year', 'hours_by_volunteer.rank_year')) + [
        FF('Value this year, your setting', LK('hours_by_volunteer', 'volunteer_id', 'value_year'), 'money'), FF('Value in all, your setting', LK('hours_by_volunteer', 'volunteer_id', 'value_total'), 'money'),
        FF('Average hours a shift', 'IFERROR(%s/%s,0)' % (LK('hours_by_volunteer', 'volunteer_id', 'hours_total'), LK('hours_by_volunteer', 'volunteer_id', 'shifts_n')), 'hours')]),
    FORM('checkin_sheet', 'Volunteer Check-in Sheet', 'Check-in for one booked shift', 'tomorrow.shift_id', F(
        ('Date', 'tomorrow.date'), ('Starts at', 'tomorrow.starts'), ('Volunteer', 'tomorrow.volunteer'), ('Phone', 'tomorrow.phone'), ('Role', 'tomorrow.role'), ('Program or area', 'tomorrow.program'), ('Hours', 'tomorrow.hours'), ('Flag', 'tomorrow.flag')) + [
        FF('Days away', LK('tomorrow', 'shift_id', 'days_away'), 'int'), FF('Shifts worked before', LK('tomorrow', 'shift_id', 'before'), 'int'), FF('Volunteers booked the same day', 'COUNTIFS(%s,%s)' % (R('tomorrow', 'days_away'), LK('tomorrow', 'shift_id', 'days_away')), 'int')]),
    FORM('reachout_sheet', 'Reach-out Sheet', 'Reach-out to a lapsed volunteer', 'lapsed.volunteer_id', F(
        ('Volunteer', 'lapsed.volunteer'), ('Phone', 'lapsed.phone'), ('Role', 'lapsed.role'), ('Last shift', 'lapsed.last_shift'), ('Hours given', 'lapsed.hours_given'), ('Days since the last shift', 'lapsed.days_since'),
        ('Rank among lapsed volunteers', 'lapsed.rank'), ('Next step', 'lapsed.next_step')) + [
        FF('Value of the hours given, your setting', '%s*{set:volunteer_hour_value}' % LK('lapsed', 'volunteer_id', 'hours_given'), 'money'), FF('Lapsed volunteers in all', LK('lapsed', 'volunteer_id', 'lapsed_n'), 'int')]),
    FORM('welcome_sheet', 'New Volunteer Welcome Sheet', 'Welcome call for a new volunteer', 'volunteers.volunteer_id', F(
        ('Name', 'volunteers.name'), ('Phone', 'volunteers.phone'), ('Role', 'volunteers.role'), ('Program or area', 'volunteers.program'), ('Joined', 'volunteers.joined'), ('Availability', 'volunteers.availability'),
        ('Shifts worked', 'volunteers.shifts_n'), ('Next training', 'volunteers.training_on')) + [
        FF('Days since joining', '{today}-%s' % V('joined'), 'int'), FF('Shifts still to reach your setting', 'MAX(0,{set:new_min_shifts}-%s)' % V('shifts_n'), 'int'), FF('Coordinator phone', V('coord_phone'), 'text')]),
    FORM('member_sheet', 'Member Sheet', 'One member', 'members.member_id', F(
        ('Member', 'members.member'), ('Phone', 'members.phone'), ('Donor ID', 'members.donor_id'), ('Level', 'members.level'), ('Joined', 'members.joined'), ('Due date', 'members.due_date'), ('Last paid', 'members.last_paid'),
        ('Status', 'members.status'), ('Annual dues', 'members.annual_dues')) + [
        FF('Days to due', M('days_to_due'), 'int'), FF('Payments recorded', M('payments_n'), 'int'), FF('Members at this level', M('level_n'), 'int')]),
    FORM('dues_sheet', 'Dues Payment Sheet', 'One dues payment', 'dues_payments.dues_id', F(
        ('Member', 'dues_payments.member'), ('Member ID', 'dues_payments.member_id'), ('Date', 'dues_payments.date'), ('Amount', 'dues_payments.amount'), ('Year', 'dues_payments.year'), ('Method', 'dues_payments.method'), ('Level', 'dues_payments.level')) + [
        FF('Falls due again on', LK('dues_payments', 'dues_id', 'due_again'), 'date'), FF('Payments of this member', 'COUNTIFS(%s,%s)' % (R('dues_payments', 'member_id'), LK('dues_payments', 'dues_id', 'member_id')), 'int'),
        FF('Dues paid by this member in all', 'SUMIFS(%s,%s,%s)' % (R('dues_payments', 'amount'), R('dues_payments', 'member_id'), LK('dues_payments', 'dues_id', 'member_id')), 'money')]),
    FORM('renewal_sheet', 'Renewal Sheet', 'One renewal', 'renewals.member_id', F(
        ('Member', 'renewals.member'), ('Phone', 'renewals.phone'), ('Level', 'renewals.level'), ('Due date', 'renewals.due_date'), ('Days to due', 'renewals.days_to_due'), ('Status', 'renewals.status'),
        ('Annual dues', 'renewals.annual_dues'), ('Rank by dues', 'renewals.rank'), ('Action', 'renewals.action')) + [
        FF('Renewals due in 30 days', LK('renewals', 'member_id', 'due30_n'), 'int'), FF('Dues due in 30 days', LK('renewals', 'member_id', 'due30_money'), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('welcome_letter', 'Volunteer Welcome Letter', 'Welcome letter to a new volunteer', 'volunteers.volunteer_id', [
        'Letter of {set:org}, dated {today}. To: {col:volunteers.name}.',
        'Welcome, and thank you for joining us as {col:volunteers.role} in {col:volunteers.program}. You joined on {col:volunteers.joined} and you told us you are available: {col:volunteers.availability}.',
        'Your volunteer coordinator will call you before your first shift. A short training is on {col:volunteers.training_on}. Please tell us if you cannot come to a shift, as early as you can.',
        'We keep your name, phone and email only to plan shifts. Ask us at any time what we hold about you. Check your local rules for anything that applies to volunteers where you work.'], ['Volunteer coordinator', 'Volunteer'], NOTE),
    DOC('roster_doc', 'Shift Roster Page', 'Shift roster page for one slot', 'slots.slot_id', [
        'Shift roster of {set:org}, dated {today}. Slot {col:slots.slot_id}.',
        'Date: {col:slots.date} ({col:slots.weekday}), {col:slots.shift}. Program or area: {col:slots.program}. Role: {col:slots.role}. Hours of the shift: {col:slots.hours}.',
        'People needed: {col:slots.needed}. People signed up: {col:slots.signed_up}. People short: {col:slots.gap}. Week of {col:slots.week_start}.',
        'Write the names of the volunteers below and keep the page at the check-in table: ____________________  ____________________  ____________________  ____________________'], ['Volunteer coordinator', 'Program manager'], NOTE),
    DOC('tomorrow_doc', "Tomorrow's Shift Sheet", "Shift sheet for one booked shift", 'tomorrow.shift_id', [
        'Shift sheet of {set:org}, dated {today}. Shift {col:tomorrow.shift_id}.',
        'Volunteer: {col:tomorrow.volunteer}, phone {col:tomorrow.phone}. Role: {col:tomorrow.role}. Program or area: {col:tomorrow.program}.',
        'Date: {col:tomorrow.date}, starts at {col:tomorrow.starts}, {col:tomorrow.shift}, {col:tomorrow.hours} hours. Flag: {col:tomorrow.flag}.',
        'On the day: tick when the volunteer arrives and write the hours worked: ____________'], ['Volunteer coordinator', 'Volunteer'], NOTE),
    DOC('certificate_doc', 'Volunteer Hours Certificate', 'Record of the hours of one volunteer', 'hours_by_volunteer.volunteer_id', [
        'Record of volunteer hours, {set:org}, dated {today}.',
        'This page records that {col:hours_by_volunteer.volunteer} worked {col:hours_by_volunteer.hours_year} hours this year, {col:hours_by_volunteer.hours_last} hours last year and {col:hours_by_volunteer.hours_total} hours in all, over {col:hours_by_volunteer.shifts_n} shifts. Last shift: {col:hours_by_volunteer.last_shift}.',
        'It is a record of hours kept by {set:org} and nothing more. Check with the body that asks for it what it needs.',
        'Signed for {set:org}: ____________________'], ['Volunteer coordinator', 'Executive director'], NOTE),
    DOC('thanks_letter', 'Volunteer Thank-You Letter', 'Thank-you letter to a volunteer', 'hours_by_volunteer.volunteer_id', [
        'Letter of {set:org}, dated {today}. To: {col:hours_by_volunteer.volunteer}.',
        'Thank you. This year you have given {col:hours_by_volunteer.hours_year} hours as {col:hours_by_volunteer.role}, and {col:hours_by_volunteer.hours_total} hours in all. Our programs run because people like you come back.',
        'We would be glad to thank you in person at our next volunteer event on {set:thanks_on}.',
        'With thanks from all of us at {set:org}.'], ['Executive director', 'Volunteer coordinator'], NOTE),
    DOC('summary_doc', 'Volunteer Yearly Summary', 'Yearly summary of one volunteer', 'hours_by_volunteer.volunteer_id', [
        'Yearly summary of {set:org}, dated {today}. Volunteer: {col:hours_by_volunteer.volunteer}, role {col:hours_by_volunteer.role}.',
        'Hours this year: {col:hours_by_volunteer.hours_year}. Hours last year: {col:hours_by_volunteer.hours_last}. Shifts worked in all: {col:hours_by_volunteer.shifts_n}. Rank among volunteers this year: {col:hours_by_volunteer.rank_year}.',
        'Value of the hours this year at the value of one volunteer hour that {set:org} sets for itself: {col:hours_by_volunteer.value_year}. This is your own setting and not an outside figure.',
        'Thank you for a year of work.'], ['Volunteer coordinator', 'Executive director'], NOTE),
    DOC('gap_doc', 'Shift Gap Report', 'Shift gap report for one open slot', 'gaps.slot_id', [
        'Shift gap report of {set:org}, dated {today}. Slot {col:gaps.slot_id}.',
        'Date: {col:gaps.date} ({col:gaps.weekday}), {col:gaps.shift}. Program or area: {col:gaps.program}. Role: {col:gaps.role}. Days away: {col:gaps.days_away}.',
        'People needed: {col:gaps.needed}. People signed up: {col:gaps.signed_up}. People short: {col:gaps.gap}. People short in the same week: {col:gaps.week_gap}. Action: {col:gaps.state}.',
        'Ask first: {col:gaps.ask_name}, phone {col:gaps.ask_phone}.'], ['Volunteer coordinator', 'Program manager'], NOTE),
    DOC('lapsed_letter', 'Lapsed Volunteer Letter', 'Letter to a lapsed volunteer', 'lapsed.volunteer_id', [
        'Letter of {set:org}, dated {today}. To: {col:lapsed.volunteer}.',
        'We have not seen you since {col:lapsed.last_shift}. In all you gave {col:lapsed.hours_given} hours as {col:lapsed.role}, and we are grateful for every one of them.',
        'If you would like to come back, even for one shift a month, please tell us and we will find a time that suits you. If you would rather step away, thank you again and the door stays open.',
        'Please call or write to the volunteer coordinator.'], ['Volunteer coordinator', 'Executive director'], NOTE),
    DOC('member_welcome', 'Member Welcome Letter', 'Welcome letter to a member', 'members.member_id', [
        'Letter of {set:org}, dated {today}. To: {col:members.member}.',
        'Welcome to {set:org} as a member at the {col:members.level} level. Your yearly dues are {col:members.annual_dues}. You joined on {col:members.joined} and your dues are next due on {col:members.due_date}.',
        'Members are invited to our members event on {col:members.event_on}. Keep this letter as a record of your membership. Ask your accountant whether dues have any effect on your own taxes.',
        'We are glad to have you with us.'], ['Executive director', 'Development manager'], NOTE),
    DOC('renewal_notice', 'Membership Renewal Notice', 'Renewal notice to a member', 'renewals.member_id', [
        'Notice of {set:org}, dated {today}. To: {col:renewals.member}.',
        'Your membership at the {col:renewals.level} level is due for renewal on {col:renewals.due_date}. Yearly dues: {col:renewals.annual_dues}. Status: {col:renewals.status}.',
        'To renew, pay your dues to {set:org} by the due date, or call us and we will help. If you no longer wish to renew, please tell us.',
        'Thank you for your support.'], ['Development manager', 'Member'], NOTE),
    DOC('dues_statement', 'Dues Statement', 'Dues statement for one member', 'members.member_id', [
        'Dues statement of {set:org}, dated {today}. Member: {col:members.member}, level {col:members.level}.',
        'Dues paid this year: {col:members.dues_this}. Dues paid last year: {col:members.dues_last}. Dues paid the year before: {col:members.dues_prev}. Payments recorded: {col:members.payments_n}. Last paid: {col:members.last_paid}.',
        'Yearly dues: {col:members.annual_dues}. Next due: {col:members.due_date}. Status: {col:members.status}.',
        'This is a record of the dues you paid. Check with your accountant what your own rules need.'], ['Bookkeeper', 'Development manager'], NOTE),
    DOC('members_list_doc', 'Members List by Level', 'Level summary page for one member', 'members.member_id', [
        'Members list page of {set:org}, dated {today}. Level: {col:members.level}.',
        'Members at this level who have not lapsed: {col:members.level_n}. Yearly dues of those members: {col:members.level_dues}.',
        'Member on this page: {col:members.member}, ID {col:members.member_id}, status {col:members.status}, due {col:members.due_date}.',
        'Print one page for each level and attach the list of members at that level.'], ['Development manager', 'Executive director'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('onboarding_chk', 'New Volunteer Onboarding', 'volunteers', 'volunteers.joined', [('Call the volunteer to welcome them', 0), ('Send the welcome letter', 1), ('Agree role, program and availability', 3), ('Book the first shift', 5), ('Invite them to the next training', 7), ('Check in after the first shift', 14), ('Ask how it went', 30)]),
    CHK('roster_chk', 'Weekly Shift Roster', 'slots', 'slots.date', [('Check slots with a gap', -14), ('Ask volunteers for the open slots', -10), ('Send reminders for shifts still short', -7), ('Fix the roster', -3), ('Print the roster', -2), ('Send the roster to the program manager', -1)]),
    CHK('reminders_chk', "Tomorrow's Reminders", 'shifts', 'shifts.date', [('Open the reminder list', -1), ('Send every reminder', -1), ('Call volunteers on a first shift', -1), ('Find cover for anyone who cancels', 0), ('Record no-shows after the shift', 1)]),
    CHK('hours_chk', 'Monthly Hours Report', 'hours_program_month', 'hours_program_month.month', [('Enter every shift of the month', 28), ('Mark no-shows', 29), ('Check hours by program', 30), ('Compare with the same month last year', 31), ('Send the hours to the executive director', 33)]),
    CHK('thanks_round_chk', 'Volunteer Thank-You Round', 'hours_value', 'hours_value.month', [('List volunteers above 100 hours', 28), ('Write a thank-you letter to each', 30), ('Send the letters', 32), ('Invite them to the thank-you event', 35), ('Note who came', 45)]),
    CHK('outreach_chk', 'Lapsed Volunteer Outreach', 'new_by_month', 'new_by_month.month', [('Run the Lapsed Volunteer Ranker', 0), ('Call volunteers with 50 hours or more', 3), ('Write to volunteers with 10 hours or more', 7), ('Offer one easy shift', 10), ('Note replies', 21), ('Update the status of each', 28)]),
    CHK('recruit_chk', 'Recruitment Drive', 'slots', 'slots.date', [('Run Recruitment Need', -60), ('Write a short call for volunteers', -50), ('Ask current volunteers to bring one friend', -45), ('Post at community places', -40), ('Hold an open evening', -30), ('Call every new sign-up', -25), ('Book first shifts', -20)]),
    CHK('review_chk', 'Yearly Volunteer Review', 'hours_value', 'hours_value.month', [('Run Volunteer Retention Check', 0), ('Add up hours and value at your setting', 3), ('List volunteers who left and why', 7), ('Thank every volunteer', 14), ('Set the plan for next year', 30)]),
    CHK('member_onboarding_chk', 'Member Onboarding', 'members', 'members.joined', [('Record the member and the first payment', 0), ('Send the welcome letter', 1), ('Add them to the members list', 2), ('Invite them to the next members event', 14), ('Check the due date is right', 30)]),
    CHK('renewal_run_chk', 'Renewal Run', 'members', 'members.due_date', [('List members due in 30 days', -45), ('Send the renewal notice', -30), ('Send a reminder', -14), ('Call members who have not paid', -3), ('Mark paid members', 0), ('Phone the overdue', 7), ('Mark lapsed members', 60)]),
    CHK('dues_month_chk', 'Dues Month-End', 'dues_forecast', 'dues_forecast.month', [('Enter every dues payment of the month', 28), ('Match payments to the bank', 30), ('Update statuses', 31), ('Compare with the forecast', 32), ('Send the total to the bookkeeper', 33)]),
    CHK('founder_chk', 'Founder First Shifts', 'slots', 'slots.date', [('List the jobs that need helpers', -28), ('Write one slot for each job', -21), ('Ask five people to take a slot', -14), ('Send a reminder the day before', -1), ('Thank everyone after the shift', 1), ('Write the hours down', 1), ('Plan the next four weeks', 3)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
fn = first_name
CO, ED, PMN, DM, BK = fn(D.TEAMID['NP-04']['name']), fn(D.TEAMID['NP-01']['name']), fn(D.TEAMID['NP-03']['name']), fn(D.TEAMID['NP-02']['name']), fn(D.TEAMID['NP-08']['name'])
CH = D.CHAIR['name']
def Mg(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    Mg('v_welcome', 'Volunteer: welcome, your first shift', 'tomorrow', 'tomorrow.phone', 'Hello {volunteer}, welcome to {org}. Your first shift is on {date} at {starts}, {program}, as {role}. We look forward to meeting you.'),
    Mg('v_reminder', 'Volunteer: your shift is coming', 'tomorrow', 'tomorrow.phone', 'Hello {volunteer}, a reminder: your shift is on {date} at {starts} at {program}. Thank you. {org}'),
    Mg('v_confirm', 'Volunteer: please confirm', 'tomorrow', 'tomorrow.phone', 'Hello {volunteer}, please confirm that you can still help on {date} at {starts} ({program}). {org}'),
    Mg('v_cancel', 'Volunteer: your shift is cancelled', 'tomorrow', 'tomorrow.phone', 'Hello {volunteer}, your shift on {date} at {program} is cancelled. We will tell you about the next one. {org}'),
    Mg('v_need', 'Volunteer: we still need people', 'gaps', 'gaps.ask_phone', 'Hello {ask_name}, we still need {gap} people on {date} at {program}. Can you help? {org}'),
    Mg('v_open', 'Volunteer: a shift is open for a role', 'gaps', 'gaps.ask_phone', 'Hello {ask_name}, a {shift} shift on {date} is open for {role}. Would you like it? {org}'),
    Mg('v_thanks_hours', 'Volunteer: thank you for your hours', 'volunteers', 'volunteers.phone', 'Hello {name}, thank you for {hours_year} hours this year. {org}'),
    Mg('v_return', 'Volunteer: we have not seen you since', 'lapsed', 'lapsed.phone', 'Hello {volunteer}, we have not seen you since {last_shift}. Would you like to come back? {org}'),
    Mg('v_total', 'Volunteer: your hours this year', 'volunteers', 'volunteers.phone', 'Hello {name}, your hours this year total {hours_year}, and {hours_worked} in all. {org}'),
    Mg('v_availability', 'Volunteer: send your availability', 'volunteers', 'volunteers.phone', 'Hello {name}, please send us your availability for next month. We have you as {availability}. {org}'),
    Mg('v_joined', 'Volunteer: thank you for joining', 'volunteers', 'volunteers.phone', 'Hello {name}, thank you for joining {org} as {role}. Your coordinator will call you about your first shift.'),
    Mg('v_training', 'Volunteer: a short training', 'volunteers', 'volunteers.phone', 'Hello {name}, a short training is on {training_on}. Can you come? {org}'),
    Mg('v_event', 'Volunteer: join our thank-you event', 'volunteers', 'volunteers.phone', 'Hello {name}, we would like to thank you in person. Please join us on {thanks_on}. {org}'),
    Mg('v_give', 'Volunteer: would you like to give', 'volunteers', 'volunteers.phone', 'Hello {name}, if you ever wish to give to {program} as well as help, we would be glad. There is no need at all. {org}'),
    Mg('v_role', 'Volunteer: a role is open', 'volunteers', 'volunteers.phone', 'Hello {name}, a role helping with {program} is open. Are you interested? {org}'),
    Mg('v_first', 'New volunteer: how was your first shift', 'volunteers', 'volunteers.phone', 'Hello {name}, how was your first shift? Tell us what went well and what we can improve. {org}'),
    Mg('m_welcome', 'Member: welcome to your level', 'members', 'members.phone', 'Hello {member}, welcome to {org} at the {level} level. Dues of {annual_dues} are recorded.'),
    Mg('m_due', 'Member: your dues are due', 'members', 'members.phone', 'Hello {member}, your dues of {annual_dues} are due on {due_date}. {org}'),
    Mg('m_lapse', 'Member: your membership lapses', 'members', 'members.phone', 'Hello {member}, your membership lapses on {due_date}. Please renew to stay with us. {org}'),
    Mg('m_renewed', 'Member: your renewal is recorded', 'members', 'members.phone', 'Hello {member}, thank you, your renewal of {annual_dues} is recorded. {org}'),
    Mg('m_details', 'Member: please check your details', 'members', 'members.phone', 'Hello {member}, we have you at the {level} level, next due on {due_date}. Please tell us if anything is wrong. {org}'),
    Mg('m_event', 'Member: a members event', 'members', 'members.phone', 'Hello {member}, a members event is on {event_on}. We hope to see you. {org}'),
    Mg('m_missed', 'Member: we missed your renewal', 'members', 'members.phone', 'Hello {member}, we have missed your renewal of {annual_dues}, due on {due_date}. Can we help? {org}'),
    Mg('c_open', 'Volunteer coordinator: shifts are open', 'gaps', 'gaps.coord_phone', 'Hello %s, {n7} shifts are open in the next 7 days and {g7} people are short. {org}' % CO),
    Mg('c_tomorrow', "Volunteer coordinator: tomorrow's list", 'tomorrow', 'tomorrow.coord_phone', "Hello %s, {tomorrow_n} volunteers are on tomorrow's list. {org}" % CO),
    Mg('c_lapsed', 'Coordinator: volunteers have lapsed', 'lapsed', 'lapsed.coord_phone', 'Hello %s, {lapsed_n} volunteers have lapsed with {lapsed_hours} hours given. {org}' % CO),
    Mg('c_top', 'Volunteer coordinator: the top gap', 'gaps', 'gaps.coord_phone', 'Hello %s, the gap on {date} at {program} is {gap} people. {org}' % CO),
    Mg('ed_hours', 'Executive director: hours of the month', 'hours_value', 'hours_value.ed_phone', 'Hello %s, volunteer hours for the month starting {month} are {hours}, worth {value} at your setting. {org}' % ED),
    Mg('pm_gap', 'Program manager: unfilled shifts', 'gaps', 'gaps.pm_phone', 'Hello %s, {program} has {gap} unfilled places on {date}. {org}' % PMN),
    Mg('dm_give', 'Development manager: volunteers who give', 'givers', 'givers.dev_phone', 'Hello %s, {givers_n} volunteers also give, {givers_total} in all. {org}' % DM),
    Mg('b_numbers', 'Board member: volunteer numbers', 'hours_value', 'hours_value.chair_phone', 'Hello %s, the volunteer numbers are ready: {active_n} volunteers are active. {org}' % CH),
    Mg('bk_dues', 'Bookkeeper: dues of the month', 'dues_forecast', 'dues_forecast.bk_phone', 'Hello %s, dues received in the month starting {month} total {received}. {org}' % BK),
    Mg('bk_overdue', 'Bookkeeper: members are overdue', 'members', 'members.bk_phone', 'Hello %s, {overdue_n} members are overdue with their dues. {org}' % BK),
    Mg('ms_30', 'Member services: renewals in 30 days', 'renewals', 'renewals.dev_phone', 'Hello %s, {due30_n} renewals are due in 30 days, worth {due30_money}. {org}' % DM),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
H30 = 'SUMIFS(%s,%s,">="&({today}-30),%s,"<="&{today})' % (R('shifts', 'worked_hours'), R('shifts', 'date'), R('shifts', 'date'))
HY = 'SUMIFS(%s,%s,">="&%s)' % (R('hours_value', 'hours'), R('hours_value', 'month'), YS)
HL = 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (R('hours_value', 'hours'), R('hours_value', 'month'), YSL, R('hours_value', 'month'), YS)
def RET(col, yr): return 'SUMIFS(%s,%s,%s)' % (R('vol_retention', col), R('vol_retention', 'year'), yr)
def S30(st): return 'COUNTIFS(%s,%s,%s,">="&({today}-30),%s,"<="&{today})' % (R('shifts', 'status'), st, R('shifts', 'date'), R('shifts', 'date'))
def GAPW(d): return '%s,">"&{today},%s,"<="&({today}+%s)' % (R('slots', 'date'), R('slots', 'date'), d)
TOPP = 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (R('hours_program_month', 'program'), R('hours_program_month', 'year_hours'), R('hours_program_month', 'year_hours'))
kpis = [
    KPI('Active volunteers', 'COUNTIFS(%s,%s,%s,"<>")' % (R('volunteers', 'status'), ACTIVE, R('volunteers', 'volunteer_id')), 'int'),
    KPI('New volunteers, last 30 days', 'COUNTIFS(%s,">="&({today}-30),%s,"<="&{today})' % (R('volunteers', 'joined'), R('volunteers', 'joined')), 'int'),
    KPI('New volunteers this year', 'COUNTIFS(%s,">="&%s,%s,"<="&{today})' % (R('volunteers', 'joined'), YS, R('volunteers', 'joined')), 'int'),
    KPI('Volunteers on break', 'COUNTIFS(%s,%s,%s,"<>")' % (R('volunteers', 'status'), tok('vstatus', 'On break'), R('volunteers', 'volunteer_id')), 'int'),
    KPI('Volunteers lapsed this year', 'COUNTIFS(%s,%s,%s,">="&%s)' % (R('volunteers', 'status'), LAPSED, R('volunteers', 'last_shift'), YS), 'int'),
    KPI('Volunteers kept from last year', RET('kept', 'YEAR({today})'), 'int'),
    KPI('Volunteer retention', 'IFERROR(%s/%s,0)' % (RET('kept', 'YEAR({today})'), RET('active', 'YEAR({today})-1')), 'pct'),
    KPI('Hours, last 30 days', H30, 'hours'),
    KPI('Hours this year', HY, 'hours'),
    KPI('Hours last year', HL, 'hours'),
    KPI('Value of hours this year, your setting', '%s*{set:volunteer_hour_value}' % HY, 'money'),
    KPI('Value of hours, last 30 days', '%s*{set:volunteer_hour_value}' % H30, 'money'),
    KPI('Shifts worked, last 30 days', S30(WORKED), 'int'),
    KPI('Share of shifts worked, last 30 days', 'IFERROR(%s/(%s+%s),0)' % (S30(WORKED), S30(WORKED), S30(NOSHOW)), 'pct'),
    KPI('No-shows, last 30 days', S30(NOSHOW), 'int'),
    KPI('Open shifts, next 7 days', 'COUNTIFS(%s,%s,">0")' % (GAPW(7), R('slots', 'gap')), 'int'),
    KPI('Open shifts, next 30 days', 'COUNTIFS(%s,%s,">0")' % (GAPW(30), R('slots', 'gap')), 'int'),
    KPI('People short, next 7 days', 'SUMIFS(%s,%s)' % (R('slots', 'gap'), GAPW(7)), 'int'),
    KPI("Volunteers on tomorrow's list", 'COUNTIFS(%s,1)' % R('tomorrow', 'days_away'), 'int'),
    KPI('Average hours a volunteer this year', 'IFERROR(%s/COUNTIFS(%s,">0"),0)' % (HY, R('hours_by_volunteer', 'hours_year')), 'hours'),
    KPI('Top program by hours this year', TOPP, 'text'),
    KPI('Lapsed volunteers with 50 or more hours', 'COUNTIFS(%s,">="&{set:call_hours})' % R('lapsed', 'hours_given'), 'int'),
    KPI('Volunteers who also give', 'COUNTIFS(%s,"<>")' % R('givers', 'volunteer_id'), 'int'),
    KPI('Money given by volunteers', 'SUM(%s)' % R('givers', 'total_given'), 'money'),
    KPI('Members now', '%s*COUNTIFS(%s,"<>"&%s,%s,"<>")' % (ON, R('members', 'status'), tok('dues', 'Lapsed'), R('members', 'member_id')), 'int'),
    KPI('Members lapsing in 30 days', '%s*COUNTIFS(%s,">="&{today},%s,"<="&({today}+30),%s,%s)' % (ON, R('members', 'due_date'), R('members', 'due_date'), R('members', 'status'), tok('dues', 'Due soon')), 'int'),
    KPI('Dues received this year', '%s*SUMIFS(%s,%s,">="&%s)' % (ON, R('dues_payments', 'amount'), R('dues_payments', 'date'), YS), 'money'),
    KPI('Dues forecast, next 12 months', 'SUM(%s)' % R('dues_forecast', 'your_estimate'), 'money'),
    KPI('Renewal rate last year', '%s*IFERROR(SUMIFS(%s,%s,YEAR({today})-1)/SUMIFS(%s,%s,YEAR({today})-1),0)' % (ON, R('dues_payments', 'renewed'), R('dues_payments', 'due_year'), R('dues_payments', 'due_n'), R('dues_payments', 'due_year')), 'pct'),
    KPI('Members overdue', '%s*COUNTIFS(%s,%s,%s,"<>")' % (ON, R('members', 'status'), tok('dues', 'Overdue'), R('members', 'member_id')), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Volunteers Dashboard", "kpis": kpis,
    "monthly": {"title": "Volunteer hours, dues and people short", "date": "hours_value.month", "series": [
        {"label": "Volunteer hours", "sum": "hours_value.hours", "date": "hours_value.month"}, {"label": "Dues received", "sum": "dues_payments.amount", "date": "dues_payments.date"},
        {"label": "People short", "sum": "slots.gap", "date": "slots.date"}]},
    "breakdowns": [{"title": "Hours by program", "by": "hours_program_month.program", "value": "hours_program_month.hours", "agg": "sum"}, {"title": "Volunteers by status", "by": "volunteers.status", "value": "volunteers.hours_worked", "agg": "count"},
                   {"title": "Members by level", "by": "members.level", "value": "members.annual_dues", "agg": "count"}, {"title": "People short by program", "by": "slots.program", "value": "slots.gap", "agg": "sum"}]}


def W(c, o, v): return (c, o, v)
insights = {"filters": [{"label": "Program or area", "list": "sprog"}, {"label": "Volunteer role", "list": "vrole"}, {"label": "Member level", "list": "mlevel"}],
    "gauges": [
        {"title": "Shifts filled against needed", "num": AGG('sum', 'slots', 'slots.signed_up', where=[W('date', '<=', '{today}')]), "den": AGG('sum', 'slots', 'slots.needed', where=[W('date', '<=', '{today}')])},
        {"title": "Volunteers kept from last year", "num": AGG('count', 'hours_by_volunteer', where=[W('hours_year', '>', 0), W('hours_last', '>', 0)]), "den": AGG('count', 'hours_by_volunteer', where=[W('hours_last', '>', 0)])},
        {"title": "Shifts worked against booked", "num": AGG('count', 'shifts', where=[W('status', '=', WORKED)]), "den": AGG('count', 'shifts', where=[W('status', '<>', tok('shstatus', 'Booked'))])},
        {"title": "Hours this year against last year", "num": AGG('sum', 'hours_by_volunteer', 'hours_by_volunteer.hours_year'), "den": AGG('sum', 'hours_by_volunteer', 'hours_by_volunteer.hours_last')},
        {"title": "Members renewed on time", "num": AGG('sum', 'dues_payments', 'dues_payments.renewed'), "den": AGG('sum', 'dues_payments', 'dues_payments.due_n')},
        {"title": "Dues paid against dues not lapsed", "num": AGG('sum', 'members', 'members.annual_dues', where=[W('status', '=', tok('dues', 'Paid'))]), "den": AGG('sum', 'members', 'members.annual_dues', where=[W('status', '<>', tok('dues', 'Lapsed'))])}],
    "charts": [
        CHART('Volunteer hours per month', 'column', 'month', [AGG('sum', 'hours_value', 'hours_value.hours', date='hours_value.month', label='Hours')]),
        CHART('Volunteer value per month, your setting', 'column', 'month', [AGG('sum', 'hours_value', 'hours_value.value', date='hours_value.month', label='Value')]),
        CHART('Shifts worked per month', 'column', 'month', [AGG('sum', 'hours_value', 'hours_value.shifts_n', date='hours_value.month', label='Shifts worked')]),
        CHART('Hours by program', 'bar', 'hours_program_month.program', [AGG('sum', 'hours_program_month', 'hours_program_month.hours', label='Hours')]),
        CHART('Hours by role, recent shift log', 'bar', 'shifts.role', [AGG('sum', 'shifts', 'shifts.worked_hours', label='Hours')]),
        CHART('Shifts by status', 'bar', 'shifts.status', [AGG('count', 'shifts', label='Shifts')]),
        CHART('Shifts worked by weekday, recent log', 'bar', 'shifts.weekday', [AGG('count', 'shifts', where=[W('status', '=', WORKED)], label='Shifts worked')]),
        CHART('People short by program', 'bar', 'slots.program', [AGG('sum', 'slots', 'slots.gap', label='People short')]),
        CHART('Slots needed and filled per month', 'column', 'month', [AGG('sum', 'slots', 'slots.needed', date='slots.date', label='Needed'), AGG('sum', 'slots', 'slots.signed_up', date='slots.date', label='Signed up')]),
        CHART('New volunteers per month', 'column', 'month', [AGG('count', 'volunteers', date='volunteers.joined', label='New volunteers')]),
        CHART('Volunteers by status', 'bar', 'volunteers.status', [AGG('count', 'volunteers', label='Volunteers')]),
        CHART('Volunteers by role', 'bar', 'volunteers.role', [AGG('count', 'volunteers', label='Volunteers')]),
        CHART('Volunteers by availability', 'bar', 'volunteers.availability', [AGG('count', 'volunteers', label='Volunteers')]),
        CHART('Hours by shift time, recent log', 'bar', 'shifts.shift', [AGG('sum', 'shifts', 'shifts.worked_hours', label='Hours')]),
        CHART('No-shows per month', 'column', 'month', [AGG('count', 'shifts', date='shifts.date', where=[W('status', '=', NOSHOW)], label='No-shows')]),
        CHART('Members by level', 'bar', 'members.level', [AGG('count', 'members', label='Members')]),
        CHART('Members by status', 'bar', 'members.status', [AGG('count', 'members', label='Members')]),
        CHART('Dues per month', 'column', 'month', [AGG('sum', 'dues_payments', 'dues_payments.amount', date='dues_payments.date', label='Dues')]),
        CHART('Dues by level', 'bar', 'dues_payments.level', [AGG('sum', 'dues_payments', 'dues_payments.amount', label='Dues')]),
        CHART('Renewals due by month', 'column', 'month', [AGG('count', 'members', date='members.due_date', label='Renewals due')]),
        CHART('Dues by payment method', 'bar', 'dues_payments.method', [AGG('sum', 'dues_payments', 'dues_payments.amount', label='Dues')]),
        CHART('Members joined per month', 'column', 'month', [AGG('count', 'members', date='members.joined', label='Members joined')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Shift gap finder", "why": "open shifts ranked by date, the people short and the busiest week named so you fill the soonest gap first", "where": "Shift Gap Finder"},
    {"name": "Shift fill planner", "why": "how many people to ask so enough say yes and come, at your own reply rate and no-show rate", "where": "Shift Fill Planner"},
    {"name": "Next person to ask", "why": "each open slot names the most active available volunteer to ask first, with the phone", "where": "Gaps by Date"},
    {"name": "Availability matcher", "why": "a weekday and a shift set against the volunteers who can come and the gap ahead, with three names to ask", "where": "Availability Matcher"},
    {"name": "Tomorrow's reminder list", "why": "every booked shift of the next days with the phone and start time, and first-timers marked", "where": "Tomorrow's Reminder List"},
    {"name": "Volunteer value calculator", "why": "hours times your own value of one hour, by year and the last 30 days, with the full-time equivalent", "where": "Volunteer Value Calculator"},
    {"name": "Lapsed volunteer ranker", "why": "lapsed volunteers ranked by hours given with a step: call, write or let go", "where": "Lapsed Volunteer Ranker"},
    {"name": "Recruitment need", "why": "hours needed next quarter against hours worked and your own attrition, as a number of people to recruit", "where": "Recruitment Need"},
    {"name": "Renewal rate check", "why": "members who paid again on time, this year so far against last year, from every dues payment", "where": "Renewal Rate Check"},
    {"name": "Dues forecast", "why": "dues falling due over 12 months at your renewal rate, with a Base, Best and Worst row", "where": "Dues Forecast"}]
competitors = [
    {"what": "donor-management software", "lacks": "keeps people and gifts but has no shift gaps, no reminder list, no volunteer hours at your own value and no lapsed volunteer ranking"},
    {"what": "volunteer-scheduling templates", "lacks": "list shifts and names but never rank gaps by date, plan how many people to ask or connect volunteers who also give"},
    {"what": "generic membership spreadsheets", "lacks": "record dues but do not forecast renewals, test the renewal rate against last year or show lapsing members first"},
    {"what": "nonprofit accounting add-ons", "lacks": "hold the ledger but know nothing of shifts, volunteer retention or the value of the hours given"}]
guide = [
    'Open Start and type your organization name, the value of one volunteer hour (your own setting), the days a volunteer counts as new and the hours that decide a call or a letter.',
    'List every volunteer on Volunteers with a role, joined date, status and availability; hours worked, last shift and days since fill in from the shift log.',
    'Add the planned shifts of the coming weeks to Shift Slots with the people needed and signed up; the gap fills in.',
    'Record each shift in Shifts Worked as worked, no-show or booked; Hours by Volunteer, Hours by Program and Month and Hours Value fill in.',
    'Type the shift IDs of the next days into Tomorrow\'s Shifts and the IDs of open slots into Gaps by Date to get the reminders and the next person to ask.',
    'Type the IDs of lapsed volunteers into Lapsed Volunteers and of volunteers who also give into Volunteers Who Also Give.',
    'If you run memberships, list members on Members, record each payment on Dues Payments and type the IDs of members to renew into Renewals Due; switch the pages off on Membership Switch if you do not.',
    'Set the share of members who renew (your estimate) on Membership Switch and read Dues Forecast for the next 12 months.',
    f'Use the {len(tools)} tools for decisions: gaps, fill planning, reminders, matching, value, lapsed volunteers, recruitment, renewals and dues.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Read the Volunteers and Members Dashboard and the charts every week.',
    'A founder with volunteers and no staff can use the same sheets with one program and a short list of volunteers; start with Volunteers, Shift Slots and Shifts Worked.']
listing = {"title": "Nonprofit Volunteer and Membership Tracker Excel Template: Shifts, Hours, Lapsed Volunteers, Dues, Renewals",
    "headline": "Fill every shift, keep your volunteers and renew your members",
    "tags": ["volunteer tracker", "nonprofit", "volunteer hours", "shift schedule", "membership dues", "excel template", "volunteer management", "charity", "member renewals", "volunteer retention", "dues forecast", "shift roster", "lapsed volunteers"],
    "description": ("Run the people side of a small community nonprofit in one Excel workbook. Built for a volunteer coordinator, an executive director or a founder with volunteers and no staff who must fill shifts, remind volunteers, keep them coming back and renew members. "
        "Volunteers holds the roster with role, availability and status. Shift Slots shows the people needed against signed up, and Gaps by Date ranks the open shifts by date, names the busiest week and the volunteer to ask first. Shifts Worked records every shift, and Hours by Volunteer, Hours by Program and Month and Hours Value turn it into hours and into value at your own setting for one volunteer hour.\n\n"
        "Lapsed Volunteers ranks people who stopped coming by the hours they gave and sets a step: call, write or let go. Volunteers Who Also Give joins the roster to your donor book. The membership side holds Members, Dues Payments, Member Levels, Renewals Due and a 12-month Dues Forecast with your renewal rate, and it can be switched off. "
        f"{len(tools)} tools answer the weekly questions: the shift gap finder, the fill planner, the availability matcher, the reminder list, the value calculator, the lapsed ranker, recruitment need, the renewal rate check and the dues forecast with Base, Best and Worst. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to volunteers, members and staff.\n\n"
        "This is part six of the Nonprofit Organization suite. It works in Excel and Google Sheets, has no macros and no subscription, and comes with a demo copy full of sample data. Forecasts and verdicts are your own estimate, not a promise. It helps you keep records and is not accounting or legal advice; ask your accountant what your own rules need."),
    "features": ["Shift gaps ranked by date with the next person to ask", "Fill planner at your own reply rate", "Tomorrow's reminder list with phones", "Hours by volunteer, program and month", "Value of volunteer hours at your own setting",
                 "Lapsed volunteers ranked with a next step", "Volunteers who also give", "Membership dues, renewals and a 12-month forecast", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Works for a founder with volunteers and no staff"]}
lists_ = finish_lists()
s = spec(id=f'{SUITE}-p6', slug='nonprofit-volunteers', profession='Nonprofit Organization', name='Volunteers and Members',
         tagline='Fill every shift, keep your volunteers and renew your members', price_usd=29,
         colors={"primary": "#22577A", "accent": "#F2A541"}, settings=settings, lists=lists_, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Volunteers and members"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'np6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(lists_))
