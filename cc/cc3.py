"""Childcare center suite - part 3: Staff, Rota and Ratios."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc3_lists import *
from cc3_tables import settings, tables
from cc3_tools import tools

HINTS = {
 'ratio': 'One row per room and hour with children: type children counted and staff present; ratio, staff needed, the gap and the check fill in. Short means fewer staff than the ratio asks.',
 'weeks': 'One row per week: short room-hours, hours with no spare staff, covered share, children in short hours and relief and management cover hours, all calculated.',
 'staff_hour': 'One row per room and hour: average children and staff from the ratio sheet, staff needed, share of days short or tight, and the rank where one more floater hour helps most.',
 'cph': 'One row per room and month: type paid hours, wages with on-costs and child-hours attended; cost per child-hour, the center figure and the dearest-room rank are calculated.',
 'ratio_hour': 'Pick a room and an hour, type children counted, staff present and the ratio (check your local rules): see staff needed, the gap and how often the room was short in 30 days.',
 'break_tool': 'Pick a date and a room: see the breaks planned, clashes where fewer staff are left than the ratio needs, who clashes and a better time. Next week\'s clashes are shown too.',
 'cph_tool': 'Pick a room and a number of months: wages with on-costs over child-hours attended give the cost per child-hour, ranked against the center and the dearest room of this month.',
 'relief_test': 'Type the short hours a week, the relief wage and the tuition you would turn away: relief cost a month is set against the tuition at risk, with your own 13-week history beside it.',
 'turnover_tool': 'Type leavers in a year and the headcount: yearly turnover against your history, the cost of a replacement, and whether a raise for the people at risk pays back.',
 'register_tool': 'Pick a person: open renewals, next due date, training hours done and needed this year and cost. The center lines count renewals due in 30, 45 and 60 days. Dates only.',
 'rota_tool': 'Pick a date, room and hour of next week: staff needed come from your average children and the room ratio, compared with the staff-hours rostered; the verdict says how many shifts to add.',
 'cap_tool': 'Pick a person and a week and type your cap on weekly hours (check your local rules): hours rostered, hours over contract, their cost and weeks over the cap in 13 weeks.',
 'swap_tool': 'Type two shifts (room, start, end, break hour) and two hours to check: staff of shift A go to room B and B to room A; each room is compared with the staff your children need.',
 'mgmt_tool': 'Type the days to look back and the imputed rate: hours the assistant director and owner-director covered rooms are costed and compared with relief wages.',
 'hire_tool': 'Type the date notice was given and the days of notice: last day, days to hire, the vacancy and relief cost if you wait; the verdict says to advertise now or wait.',
 'payrun_tool': 'Pick a month: hourly pay in the payroll rows is compared with the wages and on-costs the shifts give, row by row; the verdict says whether the pay run matches.',
 'more_children': 'Pick a room and a scenario (Base adds the children set on the start sheet, Best a third fewer, Worst two thirds more): staff-hours and cost a month are recalculated.',
}
for t in tables + tools:
    if t['key'] in HINTS: t['hint'] = HINTS[t['key']]
for st in settings:
    st['label'] = {'infants_min_staff': 'Staff the Infants room keeps with 3+ children, check your local rules', 'hours_cap_week': 'Most paid hours in a week, check your local rules', 'mgmt_rate': 'Imputed hourly rate when management covers a room', 'pay_tolerance': 'Amount a pay row may differ from the shifts'}.get(st['key'], st['label'])
    if st['key'] == 'infants_min_staff': st['label'] = 'Infants staff with 3+ children, check your local rules'
for t in tools:
    for o in t['outputs']:
        if o['label'].startswith('Short hours a week at which relief'): o['label'] = 'Short hours a week where relief costs the tuition at risk'

SUITE = 'fx-20261115-childcare-center'
NOTE = "Sample wording: adapt it to your own center and check your own local rules."
SIGN = 'Willow Lane Early Learning'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LKI(t, col, pickcol): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, col, t, pickcol)
RELIEF = tok('shiftkind', 'Relief'); BCOVER = tok('shiftkind', 'Break cover'); ROLE_AD = tok('payrole', 'Assistant director'); ROLE_OWN = tok('payrole', 'Owner-director')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'

forms = [
    FORM('rota_sheet', 'Weekly Rota Sheet', 'Rota line for one planned shift', 'rota.rota_id', F(('Date', 'rota.date'), ('Staff member', 'rota.staff'), ('Room', 'rota.room'), ('Start', 'rota.start'), ('End', 'rota.end'), ('Break start', 'rota.break_start'), ('Paid hours', 'rota.hours'), ('Staff phone', 'rota.phone')) + [
        FF('Shifts in this room that day', 'COUNTIFS({range:rota.date},%s,{range:rota.room},%s)' % (LKI('rota', 'date', 'rota_id'), LKI('rota', 'room', 'rota_id')), 'int'),
        FF('Break check', LKI('break_plan', 'break_flag', 'rota_id') + '&""', 'text')]),
    FORM('swap_sheet', 'Shift Swap Sheet', 'Shift swap for one shift', 'shifts.shift_id', F(('Date', 'shifts.date'), ('Staff member', 'shifts.staff'), ('Role', 'shifts.role'), ('Room', 'shifts.room'), ('Start', 'shifts.start'), ('End', 'shifts.end'), ('Paid hours', 'shifts.hours'), ('Kind', 'shifts.kind'), ('Wages and on-costs', 'shifts.cost')) + [
        FF('Hours of this person that week', 'SUMIFS({range:shifts.hours},{range:shifts.staff},%s,{range:shifts.week},%s)' % (LKI('shifts', 'staff', 'shift_id'), LKI('shifts', 'week', 'shift_id')), 'num'),
        FF('Other shifts in this room that day', 'COUNTIFS({range:shifts.date},%s,{range:shifts.room},%s)-1' % (LKI('shifts', 'date', 'shift_id'), LKI('shifts', 'room', 'shift_id')), 'int')]),
    FORM('break_sheet', 'Break Schedule Sheet', 'Break schedule for one shift', 'break_plan.rota_id', F(('Date', 'break_plan.date'), ('Staff member', 'break_plan.staff'), ('Room', 'break_plan.room'), ('Break start', 'break_plan.break_time'), ('Paid hours', 'break_plan.shift_hours'),
        ('Staff needed in that hour', 'break_plan.needed'), ('Staff left without the break', 'break_plan.present_after'), ('Break check', 'break_plan.break_flag'), ('Suggested break time', 'break_plan.move_to'), ('Staff phone', 'break_plan.phone'))),
    FORM('cover_sheet', 'Cover Request Sheet', 'Cover request for one room and hour', 'cover_req.request_id', F(('Date', 'cover_req.date'), ('Room', 'cover_req.room'), ('Hour', 'cover_req.hour'), ('Short by', 'cover_req.short_by'), ('Status', 'cover_req.status'), ('Days to go', 'cover_req.days_to_go'), ('Phone to call', 'cover_req.phone'), ('Lead teacher phone', 'cover_req.teacher_phone'))),
    FORM('relief_sheet', 'Relief Booking Sheet', 'Relief booking for one shift', 'relief.cover_id', F(('Date', 'relief.date'), ('Staff member', 'relief.staff'), ('Room', 'relief.room'), ('Hour', 'relief.hour'), ('Kind', 'relief.kind'), ('Hours', 'relief.hours'), ('Cost', 'relief.cost'), ('Cost per hour', 'relief.cost_hour'), ('Staff phone', 'relief.phone'))),
    FORM('hours_sheet', 'Hours Worked Sheet', 'Hours worked by one person in one week', 'hours_week.hw_id', F(('Staff member', 'hours_week.staff'), ('Week (Monday)', 'hours_week.week'), ('Rostered hours', 'hours_week.rostered'), ('Contract hours', 'hours_week.contract'), ('Against contract', 'hours_week.diff'),
        ('Hours over contract', 'hours_week.over_hours'), ('Cap check', 'hours_week.cap_flag'), ('Contract check', 'hours_week.fit_flag'), ('Staff phone', 'hours_week.phone'))),
    FORM('renewal_sheet', 'Staff Renewal Sheet', 'Renewal status for one item', 'renewals.renewal_id', F(('Holder', 'renewals.holder'), ('Item', 'renewals.item'), ('Due date', 'renewals.due_date'), ('Cost', 'renewals.cost'), ('Days left', 'renewals.days_left'), ('Band', 'renewals.band'), ('Holder phone', 'renewals.phone'))),
    FORM('training_sheet', 'Training Record Sheet', 'Training record for one session', 'training.training_id', F(('Date', 'training.date'), ('Staff member', 'training.staff'), ('Kind', 'training.kind'), ('Title', 'training.title'), ('Hours', 'training.hours'), ('Cost', 'training.cost'), ('Staff phone', 'training.phone')) + [
        FF('Hours this person has done this year', 'SUMIFS({range:training.hours},{range:training.staff},%s,{range:training.year},YEAR({today}))' % LKI('training', 'staff', 'training_id'), 'num')]),
    FORM('start_sheet', 'New Staff Start Sheet', 'Start details for one staff member', 'team.staff_id', F(('Name', 'team.name'), ('Role', 'team.role'), ('Team', 'team.team'), ('Pay type', 'team.pay_type'), ('Start date', 'team.start'), ('Contract hours a week', 'team.hours_week'), ('Hourly rate', 'team.hourly_rate'), ('Room led', 'team.room'), ('Room next week', 'team.rota_room'),
        ('Hours next week', 'team.hours_next'), ('Open renewals', 'team.renewals_open'), ('Phone', 'team.phone'), ('E-mail', 'team.email'))),
    FORM('leaving_sheet', 'Leaving Staff Sheet', 'Leaving record for one staff member', 'leavers.name', F(('Name', 'leavers.name'), ('Left on', 'leavers.left_on'), ('Replacement cost', 'leavers.replacement_cost')) + [
        FF('Average replacement cost of all leavers', 'AVERAGE({range:leavers.replacement_cost})', 'money'), FF('Leavers in the last 12 months', 'COUNTIFS({range:leavers.left_on},">"&({today}-365))', 'int'),
        FF('Yearly turnover this month', 'SUMIFS({range:turnover.turnover_share},{range:turnover.month},%s)' % MS, 'pct')]),
    FORM('meeting_sheet', 'Staff Meeting Sheet', 'Staff meeting figures for one week', 'weeks.wk_id', F(('Week (Monday)', 'weeks.week'), ('Room-hours counted', 'weeks.room_hours'), ('Short room-hours', 'weeks.short_hours'), ('Hours with no spare staff', 'weeks.tight_hours'), ('Covered share', 'weeks.covered_share'),
        ('Children in short hours', 'weeks.children_short'), ('Relief hours', 'weeks.relief_hours'), ('Break cover hours', 'weeks.break_cover_hours'), ('Management cover hours', 'weeks.mgmt_hours'))),
    FORM('payrun_sheet', 'Pay Run Sheet', 'Pay run line for one person and month', 'payroll.pay_id', F(('Person', 'payroll.person'), ('Month', 'payroll.month'), ('Role', 'payroll.role'), ('Pay type', 'payroll.pay_type'), ('Hours', 'payroll.hours'), ('Gross pay', 'payroll.gross'), ('On-costs', 'payroll.on_costs'), ('Total cost', 'payroll.total'),
        ('Hours in the shifts', 'payroll.shift_hours'), ('Cost in the shifts', 'payroll.shift_cost'), ('Pay check', 'payroll.check_flag'), ('Pay date', 'payroll.pay_date'))),
]
assert len(forms) == 12

documents = [
    DOC('rota_doc', 'Weekly Rota for Staff Room', 'Weekly rota for one staff member', 'team.staff_id', [
        'Weekly rota of {set:company}, dated {today}. Staff member: {col:team.name}, role {col:team.role}. Room next week: {col:team.rota_room}.',
        'Hours next week: Monday {col:team.mon}, Tuesday {col:team.tue}, Wednesday {col:team.wed}, Thursday {col:team.thu}, Friday {col:team.fri}. Total {col:team.hours_next} hours in {col:team.shifts_next} shifts, against {col:team.hours_week} contract hours.',
        'Breaks planned: {col:team.breaks_next}. Break clashes found: {col:team.clashes_next}. Please tell the assistant director about a change before the day it affects.'], ['Assistant director', 'Staff member'], NOTE),
    DOC('cover_summary', 'Ratio and Cover Summary', 'Ratio and cover summary for a room and week', 'heat.hm_id', [
        'Ratio and cover summary of {set:company}, dated {today}. Room: {col:heat.room}, week of {col:heat.week}.',
        'Room-hours counted {col:heat.slots}. Short room-hours {col:heat.slots_short}. Hours with no spare staff {col:heat.slots_tight}. Covered share {col:heat.covered_share}. Ratio set for the room: {col:heat.ratio} children per staff member, check your local rules.',
        'The rank of this room-week among all room-weeks is {col:heat.rank}, where 1 needs relief first. This summary helps you keep track and is not a statement about any rule.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('break_doc', 'Break Plan Note', 'Break plan note for one shift', 'break_plan.rota_id', [
        'Break plan note of {set:company}, dated {today}. Staff member: {col:break_plan.staff}. Date: {col:break_plan.date}. Room: {col:break_plan.room}.',
        'Planned break at {col:break_plan.break_time}. Staff needed in that hour: {col:break_plan.needed}. Staff left without the break: {col:break_plan.present_after}. Check: {col:break_plan.break_flag}. Suggestion: {col:break_plan.move_to}.',
        'A break must not leave the room below the ratio for its hour. Please keep to the time or ask the lead teacher before you move it.'], ['Lead teacher', 'Staff member'], NOTE),
    DOC('offer_doc', 'Shift Offer Letter', 'Shift offer letter for relief or part-time hours', 'rota.rota_id', [
        'Shift offer of {set:company}, dated {today}. To: {col:rota.staff}.',
        'We offer you a shift on {col:rota.date} in the {col:rota.room} room, from {col:rota.start} to {col:rota.end}, {col:rota.hours} paid hours.',
        'Please reply to confirm. The shift is not confirmed until you answer and the assistant director has updated the rota.'], ['Assistant director', 'Staff member'], NOTE),
    DOC('cover_note', 'Cover Request Note', 'Cover request note for a room and hour', 'cover_req.request_id', [
        'Cover request of {set:company}, dated {today}. Room: {col:cover_req.room}. Date: {col:cover_req.date}, hour {col:cover_req.hour}.',
        'We are short by {col:cover_req.short_by} staff member(s) at that hour. Status: {col:cover_req.status}. Days to go: {col:cover_req.days_to_go}.',
        'Please call {col:cover_req.phone} if you can cover. Cover helps the room keep to its ratio, check your local rules.'], ['Assistant director', 'Floater'], NOTE),
    DOC('training_plan', 'Training Plan for the Year', 'Training plan for one person and year', 'train_year.ty_id', [
        'Training plan of {set:company}, dated {today}. Staff member: {col:train_year.staff}. Year: {col:train_year.year_label}.',
        'Hours done {col:train_year.done} of {col:train_year.target} planned. Hours still needed {col:train_year.needed}. Training cost so far {col:train_year.cost}. Target check: {col:train_year.status_flag}.',
        'Agree below the sessions you will book to close the gap, with the dates and who covers your room.'], ['Owner-director', 'Staff member'], NOTE),
    DOC('renewal_list', 'Renewal Reminder List', 'Renewal reminder for one item', 'renewals.renewal_id', [
        'Renewal reminder of {set:company}, dated {today}. Holder: {col:renewals.holder}. Item: {col:renewals.item}.',
        'Due date {col:renewals.due_date}. Days left {col:renewals.days_left}. Band: {col:renewals.band}. Cost of the renewal {col:renewals.cost}.',
        'Please send us the new date once it is done. This reminder lists status and dates only.'], ['Owner-director', 'Holder'], NOTE),
    DOC('welcome_staff', 'Welcome Letter for New Staff', 'Welcome letter for a new staff member', 'team.staff_id', [
        'Welcome to {set:company}, {col:team.name}. This letter is dated {today}.',
        'Your role is {col:team.role}. Your start date is {col:team.start}. Your contract is {col:team.hours_week} hours a week. Your first room is {col:team.rota_room}.',
        'On your first day please ask for the room plan, the break times and the sign-in routine. Your rota for next week shows {col:team.hours_next} hours.'], ['Owner-director', 'Staff member'], NOTE),
    DOC('handover_note', 'Staff Handover Note', 'Handover note when a staff member leaves', 'leavers.name', [
        'Handover note of {set:company}, dated {today}. Staff member: {col:leavers.name}. Last day: {col:leavers.left_on}.',
        'List below the room routines, the keys and passes to return and the families who need a call. Replacing a staff member cost about {col:leavers.replacement_cost} last time.',
        'Please agree the handover with the lead teacher before the last day.'], ['Owner-director', 'Lead teacher'], NOTE),
    DOC('payslip_doc', 'Pay Slip Summary', 'Pay slip summary for one person and month', 'payroll.pay_id', [
        'Pay summary of {set:company}, dated {today}. Person: {col:payroll.person}, role {col:payroll.role}. Month: {col:payroll.month}.',
        'Hours {col:payroll.hours}. Gross pay {col:payroll.gross}. On-costs {col:payroll.on_costs}. Total cost to the center {col:payroll.total}. Pay date {col:payroll.pay_date}. Pay check against the shifts: {col:payroll.check_flag}.',
        'This summary is not a legal payslip: ask your adviser what a payslip must show where you work.'], ['Assistant director', 'Staff member'], NOTE),
    DOC('hours_report', 'Staff Hours Accountant Report', 'Staff hours and cost report for the accountant', 'turnover.tm_id', [
        'Staff hours report of {set:company}, dated {today}. Month: {col:turnover.month}.',
        'Paid hours {col:turnover.hours}. Staff cost {col:turnover.staff_cost}. Revenue {col:turnover.revenue}. Staff cost share {col:turnover.cost_share}. Headcount {col:turnover.headcount}.',
        'Leavers in the month {col:turnover.leavers}, replacement cost {col:turnover.replacement_cost}. Please confirm with your adviser how these figures are reported.'], ['Assistant director', 'Accountant'], NOTE),
    DOC('review_sheet', 'Annual Staff Review Sheet', 'Annual review sheet for one staff member', 'team.staff_id', [
        'Annual review sheet of {set:company}, dated {today}. Staff member: {col:team.name}, role {col:team.role}. With us for {col:team.months_here} months.',
        'Contract hours {col:team.hours_week}. Hours next week {col:team.hours_next}. Training hours this year {col:team.train_hours}, still needed {col:team.train_gap}. Open renewals {col:team.renewals_open}, the next on {col:team.next_due}.',
        'Write below what went well, what you want to learn next year and the support you need.'], ['Owner-director', 'Staff member'], NOTE),
]
assert len(documents) == 12

checklists = [
    CHK('build_rota', 'Building Next Week\'s Rota Steps', 'weeks', 'weeks.week', [('Count the children booked for each room and hour', 0), ('Set staff needed at the ratio of each room', 0), ('Write the shifts on the rota sheet', 1), ('Plan every break so no room drops below ratio', 2), ('Check each person against their contract hours', 3), ('Publish the rota to staff', 4)]),
    CHK('daily_ratio', 'Daily Ratio Check Steps', 'ratio', 'ratio.date', [('Count the children in each room at the start of the day', 0), ('Count the staff present in each room', 0), ('Compare with the ratio of the room, check your local rules', 0), ('Call a floater for any room that is short', 0), ('Write the room-hours that were short', 1)]),
    CHK('break_cover', 'Break Cover Check Steps', 'rota', 'rota.date', [('List every break planned that day', -1), ('Check the room keeps its ratio during each break', -1), ('Move any break that causes a clash', -1), ('Tell the staff the break times', 0), ('Note any break that did not happen', 1)]),
    CHK('find_cover', 'Finding Cover Steps', 'cover_req', 'cover_req.date', [('Write the room, hour and how many staff are short', -2), ('Call a floater from the relief list', -2), ('Ask the assistant director to cover if no floater can', -1), ('Tell the lead teacher who is covering', -1), ('Record who filled the request', 0)]),
    CHK('book_relief', 'Booking Relief Steps', 'relief', 'relief.date', [('Agree the hours and the room with the relief staff member', -3), ('Send the shift offer', -3), ('Confirm the answer and add the shift to the rota', -2), ('Tell the lead teacher', -1), ('Check the hours worked and the cost afterwards', 1)]),
    CHK('new_staff', 'New Staff Member Start Steps', 'team', 'team.start', [('Send the welcome letter', -14), ('Check the background check and other renewals are on file', -7), ('Add the person to the team sheet and the rota', -3), ('Prepare the room and the key', -1), ('Welcome the person and walk through the routines', 0), ('Review the first week', 7)]),
    CHK('staff_leaving', 'Staff Leaving Steps', 'leavers', 'leavers.left_on', [('Confirm the last day in writing', -30), ('Plan the handover note', -14), ('Start the hiring plan', -14), ('Book relief for the gap', -7), ('Collect keys and passes', 0), ('Close the pay run and record the replacement cost', 7)]),
    CHK('renewal_review', 'Renewal and Training Steps', 'renewals', 'renewals.due_date', [('List renewals due in 30, 45 and 60 days', -60), ('Book the course or check', -45), ('Remind the person', -30), ('Check the date it was renewed', 0), ('Update the renewals sheet', 1)]),
    CHK('hours_pay', 'Monthly Hours and Pay Steps', 'payroll', 'payroll.pay_date', [('Total the hours by person from the shifts', -5), ('Compare with the payroll rows', -4), ('Look at hours over contract and over the cap', -3), ('Fix any row that differs', -2), ('Send the totals to the accountant', -1), ('Pay and file the pay run', 0)]),
    CHK('hire_replacement', 'Hiring a Replacement Steps', 'leavers', 'leavers.left_on', [('Write the role and the hours needed', -45), ('Place the advert', -40), ('Interview and offer', -30), ('Check references and background check, check your local rules', -20), ('Plan the first week and the relief gap', -5), ('Start the new staff member', 0)]),
    CHK('staff_meeting', 'Staff Meeting Preparation Steps', 'weeks', 'weeks.week', [('Print the week figures from the meeting sheet', 7), ('List short hours and the rooms involved', 7), ('Review renewals due and training hours', 8), ('Agree rota changes and break fixes', 9), ('Write the actions and who owns them', 10)]),
    CHK('year_training', 'Year-end Training Review Steps', 'training', 'training.date', [('List hours done by person against the target', 0), ('List who is below the target', 1), ('Plan sessions for next year', 5), ('Set the training budget', 7), ('Book the first sessions', 14)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text + ' ' + SIGN)
messages = [
    M('s_shifts', 'Staff: your shifts next week', 'team', 'team.phone', 'Hello {name}, you have {shifts_next} shifts next week, {hours_next} hours in total. Please check the rota.'),
    M('s_changed', 'Staff: your rota has changed', 'rota', 'rota.phone', 'Hello {staff}, your shift on {date} is now {start} to {end} in the {room} room. Please check the rota.'),
    M('s_cover', 'Staff: can you cover a room', 'cover_req', 'cover_req.phone', 'Hello, can you cover the {room} room on {date} at {hour}? We are short by {short_by}. Please reply yes or no.'),
    M('s_thanks', 'Staff: thank you for covering', 'relief', 'relief.phone', 'Hello {staff}, thank you for covering the {room} room on {date}, {hours} hours. It helped us keep the ratio.'),
    M('s_break', 'Staff: please confirm your break', 'break_plan', 'break_plan.phone', 'Hello {staff}, please confirm your break at {break_time} on {date} in the {room} room.'),
    M('s_move', 'Staff: your break time check', 'break_plan', 'break_plan.phone', 'Hello {staff}, about your break on {date} in the {room} room: planned for {break_time}, suggestion: {move_to}.'),
    M('s_over', 'Staff: hours above your contract', 'hours_week', 'hours_week.phone', 'Hello {staff}, your rostered hours for the week of {week} are {rostered}, above your contract hours of {contract}. Please talk to us if this is too many.'),
    M('s_under', 'Staff: hours below your contract', 'hours_week', 'hours_week.phone', 'Hello {staff}, your rostered hours for the week of {week} are {rostered}, below your contract hours of {contract}. We will try to offer more shifts.'),
    M('s_check', 'Staff: please send your new certificate', 'renewals', 'renewals.phone', 'Hello {holder}, your {item} was due on {due_date}. Please send us the new date once it is done.'),
    M('s_course', 'Staff: book your renewal course', 'renewals', 'renewals.phone', 'Hello {holder}, please book your renewal now: your {item} ends on {due_date}, status: {band}. Reply with the date you choose.'),
    M('s_hours', 'Staff: your training hours this year', 'train_year', 'train_year.phone', 'Hello {staff}, your training hours in {year_label} are {done} of {target}. {needed} hours are still needed.'),
    M('s_trainday', 'Staff: a training day is booked', 'training', 'training.phone', 'Hello {staff}, a training session is booked on {date}: {title}, {hours} hours. Please tell us if you cannot come.'),
    M('s_pay', 'Staff: your pay for the month', 'payroll', 'payroll.phone', 'Hello {person}, your pay for {month} is {total} including on-costs, paid on {pay_date}.'),
    M('s_payhours', 'Staff: please check your hours', 'payroll', 'payroll.phone', 'Hello {person}, please check your hours on the pay run for {month}: {hours} hours are recorded.'),
    M('s_welcome', 'Staff: welcome, you start on a date', 'team', 'team.phone', 'Hello {name}, welcome to the team. You start on {start} as {role}, {hours_week} hours a week.'),
    M('s_last', 'Staff: your handover before you leave', 'team', 'team.phone', 'Hello {name}, after {months_here} months with us please complete the handover note before your last day.'),
    M('f_relief', 'Floater: relief hours are available', 'relief', 'relief.phone', 'Hello {staff}, relief hours like {date} in the {room} room come up often. Please tell us the days you can work.'),
    M('f_confirm', 'Floater: please confirm you can work', 'rota', 'rota.phone', 'Hello {staff}, please confirm you can work on {date} from {start} to {end}.'),
    M('t_short', 'Lead teacher: your room is short', 'cover_req', 'cover_req.teacher_phone', 'Hello, your room, {room}, is short by {short_by} at {hour} on {date}. We are finding cover.'),
    M('t_over', 'Lead teacher: more staff than needed', 'staff_hour', 'staff_hour.teacher_phone', 'Hello, the {room} room has {avg_present} staff on average at {hour} against {needed_avg} needed. We may move a staff member to another room.'),
    M('t_leave', 'Lead teacher: cover is booked', 'cover_req', 'cover_req.teacher_phone', 'Hello, cover is booked for the {room} room on {date} at {hour}. Status: {status}.'),
    M('t_ratio', 'Lead teacher: the ratio for your room', 'heat', 'heat.teacher_phone', 'Hello, the ratio for the {room} room is {ratio} children per staff member, check your local rules. It was short {slots_short} room-hours in the week of {week}.'),
    M('a_moved', 'Assistant: you are moved to a room', 'rota', 'rota.phone', 'Hello {staff}, you are moved to the {room} room on {date}, {start} to {end}.'),
    M('o_short', 'Owner: a room is short', 'cover_req', 'cover_req.owner_phone', 'Hello, the {room} room is short by {short_by} at {hour} on {date}. Status: {status}.'),
    M('o_relief', 'Owner: relief and short hours this week', 'weeks', 'weeks.owner_phone', 'Hello, in the week of {week} we used {relief_hours} relief hours and {short_hours} room-hours were short.'),
    M('o_renew', 'Owner: renewals due soon', 'renewals', 'renewals.owner_phone', 'Hello, the {item} of {holder} is due on {due_date}, status: {band}.'),
    M('o_share', 'Owner: staff cost share this month', 'turnover', 'turnover.owner_phone', 'Hello, staff cost share for {month} is {cost_share}: staff cost {staff_cost} on revenue {revenue}.'),
    M('o_turnover', 'Owner: turnover this year', 'turnover', 'turnover.owner_phone', 'Hello, yearly turnover at {month} is {turnover_share} with {leavers_12m} leavers in 12 months.'),
    M('ad_mgmt', 'Assistant director: management cover', 'weeks', 'weeks.ad_phone', 'Hello, management cover in the week of {week} was {mgmt_hours} hours.'),
    M('ad_publish', 'Assistant director: shifts to publish', 'team', 'team.ad_phone', 'Hello, please publish next week\'s shifts: {name} has {shifts_next} shifts and {hours_next} hours.'),
    M('ac_payroll', 'Accountant: payroll totals for the month', 'turnover', 'turnover.accountant_phone', 'Hello, payroll totals for {month}: staff cost {staff_cost} on revenue {revenue}, {hours} paid hours.'),
    M('ac_hours', 'Accountant: staff hours and on-costs', 'payroll', 'payroll.accountant_phone', 'Hello, for {month}: {person}, {hours} hours, gross {gross}, on-costs {on_costs}.'),
    M('c_kitchen', 'Cook: children expected by hour', 'staff_hour', 'staff_hour.cook_phone', 'Hello, the {room} room averages {avg_children} children at {hour}. Please plan the kitchen for that hour.'),
    M('cl_site', 'Cleaner: staff on site', 'rota', 'rota.cleaner_phone', 'Hello, staff on site on {date}: {staff} in the {room} room until {end}.'),
]
assert len(messages) == 34, len(messages)

A30 = '{range:ratio.date},">"&({today}-30),{range:ratio.date},"<="&{today}'
A7 = '{range:ratio.date},">"&({today}-7),{range:ratio.date},"<="&{today}'
YR = 'YEAR({today})'
kpis = [
    KPI('Staff on the payroll', 'COUNTIFS({range:team.pay_type},%s)+COUNTIFS({range:team.pay_type},%s)+COUNTIFS({range:team.pay_type},%s)' % (tok('paytype', 'Hourly'), tok('paytype', 'Salary'), tok('paytype', 'Owner draw')), 'int'),
    KPI('Staff hours rostered this week', 'SUMIFS({range:shifts.hours},{range:shifts.week},{today}-WEEKDAY({today},2)+1)', 'hours'),
    KPI('Staff hours paid this month', 'SUMIFS({range:shifts.hours},{range:shifts.month},%s)' % MS, 'hours'),
    KPI('Short room-hours, last 7 days', 'SUMIFS({range:ratio.short_flag},%s)' % A7, 'int'),
    KPI('Short room-hours, last 30 days', 'SUMIFS({range:ratio.short_flag},%s)' % A30, 'int'),
    KPI('Room with most short hours, 13 weeks', 'IFERROR(INDEX({range:heat.room},MATCH(1,{range:heat.rank},0))&"","")', 'text'),
    KPI('No-spare-staff room-hours, last 30 days', 'SUMIFS({range:ratio.tight_flag},%s)' % A30, 'int'),
    KPI('Break clashes next week', 'SUM({range:break_plan.clash})', 'int'),
    KPI('Relief hours used this month', 'SUMIFS({range:shifts.hours},{range:shifts.kind},%s,{range:shifts.month},%s)' % (RELIEF, MS), 'hours'),
    KPI('Break cover hours this month', 'SUMIFS({range:shifts.hours},{range:shifts.kind},%s,{range:shifts.month},%s)' % (BCOVER, MS), 'hours'),
    KPI('Management cover hours this month', 'SUMIFS({range:shifts.hours},{range:shifts.role},%s,{range:shifts.month},%s)+SUMIFS({range:shifts.hours},{range:shifts.role},%s,{range:shifts.month},%s)' % (ROLE_AD, MS, ROLE_OWN, MS), 'hours'),
    KPI('Staff cost this month', 'SUMIFS({range:turnover.staff_cost},{range:turnover.month},%s)' % MS, 'money'),
    KPI('Staff cost share this month', 'SUMIFS({range:turnover.cost_share},{range:turnover.month},%s)' % MS, 'pct'),
    KPI('Staff cost share, last 12 months', 'IFERROR(SUMIFS({range:turnover.staff_cost},{range:turnover.month},">"&EDATE(%s,-12),{range:turnover.month},"<="&%s)/SUMIFS({range:turnover.revenue},{range:turnover.month},">"&EDATE(%s,-12),{range:turnover.month},"<="&%s),0)' % (MS, MS, MS, MS), 'pct'),
    KPI('Staff cost per child-hour this month', 'IFERROR(SUMIFS({range:cph.wages},{range:cph.month},%s)/SUMIFS({range:cph.child_hours},{range:cph.month},%s),0)' % (MS, MS), 'money'),
    KPI('Dearest room per child-hour', 'IFERROR(INDEX({range:cph.room},MATCH(%s&"|1",{range:cph.rank_key},0))&"","")' % MS, 'text'),
    KPI('Cheapest room per child-hour', 'IFERROR(INDEX({range:cph.room},MATCH(%s&"|5",{range:cph.rank_key},0))&"","")' % MS, 'text'),
    KPI('Hours over contract, last 4 weeks', 'SUMIFS({range:hours_week.over_hours},{range:hours_week.week},">="&({today}-28))', 'hours'),
    KPI('Average weekly hours, last 4 weeks', 'IFERROR(AVERAGEIFS({range:hours_week.rostered},{range:hours_week.week},">="&({today}-28)),0)', 'hours'),
    KPI('Renewals due in 30 days', 'COUNTIFS({range:renewals.band},%s)' % fl('Due in 30 days'), 'int'),
    KPI('Renewals due in 45 days', 'SUM({range:renewals.warn_flag})', 'int'),
    KPI('Renewals overdue', 'COUNTIFS({range:renewals.band},%s)' % fl('Overdue'), 'int'),
    KPI('Training hours done this year', 'SUMIFS({range:training.hours},{range:training.year},%s)' % YR, 'hours'),
    KPI('Training hours still needed', 'SUMIFS({range:train_year.needed},{range:train_year.this_year},1)', 'hours'),
    KPI('Staff below the yearly training target', 'COUNTIFS({range:train_year.this_year},1,{range:train_year.needed},">0")', 'int'),
    KPI('Training cost this year', 'SUMIFS({range:training.cost},{range:training.year},%s)' % YR, 'money'),
    KPI('Leavers, last 12 months', 'COUNTIFS({range:leavers.left_on},">"&({today}-365),{range:leavers.left_on},"<="&{today})', 'int'),
    KPI('Turnover, last 12 months', 'SUMIFS({range:turnover.turnover_share},{range:turnover.month},%s)' % MS, 'pct'),
    KPI('Average vacancy days a leaver', 'IFERROR(SUM({range:turnover.vacancy_days})/SUM({range:turnover.leavers}),0)', 'num'),
    KPI('Replacement cost, last 12 months', 'SUMIFS({range:leavers.replacement_cost},{range:leavers.left_on},">"&({today}-365),{range:leavers.left_on},"<="&{today})', 'money'),
]
assert len(kpis) == 30
dashboard = {"title": "Staff and Ratio Dashboard", "kpis": kpis,
    "monthly": {"title": "Staff cost and relief cost", "date": "turnover.month", "series": [{"label": "Staff cost", "sum": "turnover.staff_cost", "date": "turnover.month"}, {"label": "Relief and cover cost", "sum": "relief.cost", "date": "relief.date"}]},
    "breakdowns": [{"title": "Short room-hours by room", "by": "heat.room", "value": "heat.slots_short", "agg": "sum"}, {"title": "Paid hours by role", "by": "shifts.role", "value": "shifts.hours", "agg": "sum"},
                   {"title": "Paid hours by room", "by": "shifts.room", "value": "shifts.hours", "agg": "sum"}, {"title": "Training hours by staff member", "by": "train_year.staff", "value": "train_year.done", "agg": "sum"}]}
def G(t, **w): return AGG('count', t, where=[(k, '=', v) for k, v in w.items()])
insights = {"filters": [{"label": "Room", "list": "room"}, {"label": "Weekday", "list": "wday"}],
    "gauges": [{"title": "Room-hours covered at ratio", "num": AGG('count', 'ratio', where=[('short_flag', '=', 0)]), "den": AGG('count', 'ratio')},
               {"title": "Breaks without a clash", "num": AGG('count', 'break_plan', where=[('break_flag', '=', fl('No clash'))]), "den": AGG('count', 'break_plan', where=[('has_break', '=', 1)])},
               {"title": "Staff at the yearly training target", "num": AGG('count', 'train_year', where=[('this_year', '=', 1), ('status_flag', '=', fl('On track'))]), "den": AGG('count', 'train_year', where=[('this_year', '=', 1)])},
               {"title": "Renewals current", "num": AGG('count', 'renewals', where=[('open_flag', '=', 1), ('band', '<>', fl('Overdue'))]), "den": AGG('count', 'renewals', where=[('open_flag', '=', 1)])},
               {"title": "Months at or below the staff cost target", "num": AGG('count', 'turnover', where=[('share_ok', '=', 1)]), "den": AGG('count', 'turnover')},
               {"title": "Months at or below the turnover target", "num": AGG('count', 'turnover', where=[('turnover_ok', '=', 1)]), "den": AGG('count', 'turnover')}],
    "charts": [
        CHART('Short room-hours per week', 'bar', 'weeks.wk', [AGG('sum', 'weeks', 'weeks.short_hours', label='Short room-hours')]),
        CHART('Short hours by room', 'bar', 'heat.room', [AGG('sum', 'heat', 'heat.slots_short', label='Short room-hours')]),
        CHART('Short hours by weekday', 'bar', 'ratio.weekday', [AGG('sum', 'ratio', 'ratio.short_flag', label='Short room-hours')]),
        CHART('Short hours by hour of day', 'bar', 'ratio.hour', [AGG('sum', 'ratio', 'ratio.short_flag', label='Short room-hours')]),
        CHART('Staff present by hour', 'bar', 'staff_hour.hour', [AGG('avg', 'staff_hour', 'staff_hour.avg_present', label='Average staff present')]),
        CHART('Rostered hours per week', 'line', 'hours_week.wk', [AGG('sum', 'hours_week', 'hours_week.rostered', label='Rostered hours')]),
        CHART('Paid hours per month', 'column', 'month', [AGG('sum', 'shifts', 'shifts.hours', date='shifts.date', label='Paid hours')]),
        CHART('Staff cost per month', 'bar', 'month', [AGG('sum', 'turnover', 'turnover.staff_cost', date='turnover.month', label='Staff cost')]),
        CHART('Staff cost share per month', 'column', 'month', [AGG('avg', 'turnover', 'turnover.cost_share', date='turnover.month', label='Staff cost share')]),
        CHART('Staff cost by role', 'bar', 'payroll.role', [AGG('sum', 'payroll', 'payroll.total', label='Staff cost')]),
        CHART('Cost per child-hour by room', 'bar', 'cph.room', [AGG('avg', 'cph', 'cph.cost_ch', label='Cost per child-hour')]),
        CHART('Cost per child-hour per month', 'column', 'month', [AGG('avg', 'cph', 'cph.cost_ch', date='cph.month', label='Average of rooms')]),
        CHART('Relief and break cover hours per month', 'bar', 'month', [AGG('sum', 'shifts', 'shifts.hours', date='shifts.date', where=[('kind', '=', RELIEF)], label='Relief hours'), AGG('sum', 'shifts', 'shifts.hours', date='shifts.date', where=[('kind', '=', BCOVER)], label='Break cover hours')]),
        CHART('Management cover hours per month', 'bar', 'month', [AGG('sum', 'shifts', 'shifts.hours', date='shifts.date', where=[('role', '=', ROLE_AD)], label='Assistant director'), AGG('sum', 'shifts', 'shifts.hours', date='shifts.date', where=[('role', '=', ROLE_OWN)], label='Owner-director')]),
        CHART('Shifts by kind', 'bar', 'shifts.kind', [AGG('count', 'shifts', label='Shifts')]),
        CHART('Hours by staff member', 'bar', 'hours_week.staff', [AGG('sum', 'hours_week', 'hours_week.rostered', label='Rostered hours')]),
        CHART('Training hours by kind', 'bar', 'training.kind', [AGG('sum', 'training', 'training.hours', label='Training hours')]),
        CHART('Training hours per month', 'bar', 'month', [AGG('sum', 'training', 'training.hours', date='training.date', label='Training hours')]),
        CHART('Training cost by staff member', 'bar', 'train_year.staff', [AGG('sum', 'train_year', 'train_year.cost', label='Training cost')]),
        CHART('Renewals by item', 'bar', 'renewals.item', [AGG('count', 'renewals', label='Renewals')]),
        CHART('Renewals due by month', 'bar', 'month', [AGG('count', 'renewals', date='renewals.due_date', label='Renewals due')]),
        CHART('Leavers per month', 'bar', 'month', [AGG('count', 'leavers', date='leavers.left_on', label='Leavers')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6
signature = [
    {"name": "Ratio by hour", "why": "children counted every hour against the ratio of each room give staff needed, staff present and the gap, so a short hour never hides in a daily total", "where": "Ratio by Hour"},
    {"name": "Cover heat map", "why": "short room-hours by room and week are ranked so relief hours go where they are needed first", "where": "Cover Heat Map"},
    {"name": "Break planner", "why": "every break is checked against the staff the room needs in that hour, and a clash gets a better break time", "where": "Break Plan"},
    {"name": "Cost per child-hour", "why": "wages with on-costs over child-hours attended, by room and month, ranked from dearest to cheapest", "where": "Cost per Child-Hour"},
    {"name": "Relief hire test", "why": "short hours a week at the relief wage set against the tuition you would turn away, with a verdict to hire relief, use part-timers or hold", "where": "Relief Hire Test"},
    {"name": "Turnover and replacement cost", "why": "leavers over headcount against your own history, the real cost of a replacement and whether a raise pays back", "where": "Turnover and Replacement Cost"},
    {"name": "Renewals and training register", "why": "renewal dates in 30, 45 and 60 day bands and training hours against the yearly target, status and dates only", "where": "Renewals and Training Register"},
    {"name": "Shift swap checker", "why": "swap two shifts and see whether either room drops below the staff it needs in the hours you check", "where": "Shift Swap Checker"},
    {"name": "Floater placement ranker", "why": "every room-hour is ranked by days short and days with no spare staff so one more floater hour goes where it helps most", "where": "Floater Placement Ranker"}]
competitors = [
    {"what": "free sign-in sheet templates", "lacks": "record who was there but never compare children with staff each hour, so a short hour is invisible"},
    {"what": "single-sheet rota spreadsheets", "lacks": "list shifts but do not check breaks against the ratio, cost per child-hour or hours over contract"},
    {"what": "subscription childcare-management software", "lacks": "charge every month or per child and keep ratio and staff cost logic hidden, so you cannot see why a room is short"},
    {"what": "generic payroll spreadsheets", "lacks": "total pay but never tie it to the shifts, the rooms or the relief and cover cost"},
    {"what": "paper renewal diaries", "lacks": "hold dates but give no 30, 45 and 60 day bands, no training hours against a target and no cost per person"}]
guide = [
    'Open Start and type your center name and your own limits in the yellow cells: staff on the Infants room, break minutes, on-costs, staff cost target, training hours and the weekly hours cap.',
    'Check Rooms and Pay Rates. The ratio is the number of children each staff member may care for in a room: set it from your local rules, they are not a standard.',
    'Keep Team up to date: one row per staff member and outside contact with contract hours and the room each teacher leads.',
    'Enter shifts on Shifts: date, staff member, room, start, end, break and rate. Paid hours, wages and on-costs calculate by themselves.',
    'Type the children counted and the staff present each hour on Ratio by Hour. Staff needed, the gap and the short or covered check fill in; Short Hours by Week and Cover Heat Map follow.',
    'Plan next week on Rota Next Week, then read Break Plan: it shows every break that would leave a room below its ratio and a better time.',
    'Log cover requests on Cover Requests and every relief or break-cover shift on Relief and Cover Shifts.',
    'Enter payroll rows and check them against the shifts with the Pay-run Check; turnover and staff cost share by month sit on Turnover by Month.',
    'Keep Renewals and Training current: status and dates only. The register shows what is due in 30, 45 and 60 days.',
    f'Use the {len(tools)} calculators for ratio, cover, breaks, cost per child-hour, relief, turnover, renewals, rota, overtime, swaps, floaters, management cover, cost share, training, hiring, pay and contract hours.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Staff and Ratio Dashboard and Charts every week. A single home daycare provider can use the same sheets with one room and one helper.']
listing = {"title": "Childcare Center Staff, Rota and Ratio Excel Template: Ratio by Hour, Cover Heat Map, Break Planner, Cost per Child-Hour, Relief Test",
    "headline": "Know every hour your rooms are covered and what each staff hour costs",
    "tags": ["childcare center", "daycare template", "home daycare", "staff rota", "ratio tracker", "staff to child ratio", "break planner", "cost per child hour", "relief cover", "staff turnover", "training tracker", "childcare excel", "daycare owner"],
    "description": ("Run the people side of a home daycare or childcare center in one Excel workbook. Built for an owner-director with 1 to 5 rooms and up to a dozen staff. "
        "Ratio means the number of children each staff member may care for in a room: you set it per room from your local rules. Ratio by Hour turns the children counted each hour into staff needed, staff present and the gap, so you see the exact room-hours that were short.\n\n"
        "Short Hours by Week and a Cover Heat Map rank rooms and weeks for relief. Rota Next Week feeds a Break Plan that checks every break against the staff each room needs and suggests a better time. Cost per Child-Hour compares rooms month by month, Turnover by Month adds staff cost share against your own target, and Renewals and Training keep status and dates only, with 30, 45 and 60 day bands.\n\n"
        f"{len(tools)} calculators answer the weekly questions: is the room covered, where do relief hours go, do breaks clash, which room costs most, hire relief or hold, does a raise pay back, who is over the hours cap, is a swap safe and where does a floater help most. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to staff, floaters, teachers, the owner-director, the accountant, the cook and the cleaner. Children's data is counts and dates only.\n\n"
        "This is part three of the Home Daycare and Childcare Center suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. It helps you keep track of staffing and does not promise results."),
    "features": ["Ratio by hour and room with staff needed and the gap", "Cover heat map and short hours by week", "Break planner that finds clashes and suggests a time", "Cost per child-hour by room and month", "Relief hire test, turnover and replacement cost",
                 "Renewals and training register, status and dates only", "Rota, hours cap and contract fit checks", f"{len(tools)} calculators with a clear verdict", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p3', slug='childcare-center-staff', profession='Home Daycare and Childcare Center', name='Staff, Rota and Ratios',
         tagline='Know every hour your rooms are covered and what each staff hour costs', price_usd=29,
         colors={"primary": "#33658A", "accent": "#F6AE2D"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Staff, rota and ratios"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc3.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
