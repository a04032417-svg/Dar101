"""HVAC and plumbing contractor suite - part 4: Technicians: Hours, Pay and Capacity."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv4_lists import *
from hv4_tables import settings, tables, TS, JB, WK, LW, J13, W12M, MS, COMP, NO, YES, CWK, OWNDRAW, WON, LOST
from hv4_tools import tools

SUITE = 'fx-20261115-hvac-plumbing'
NOTE = "Sample wording: adapt it to your own business. Pay, overtime and tax rules differ by place: confirm with your adviser."
def fields(t, *pairs): return [FV(a, '%s.%s' % (t, b)) for a, b in pairs]
TS_ = lambda c_: '{range:timesheets.%s}' % c_
NW4 = '(%s+7)' % LW

forms = [
    FORM('weekly_timesheet', 'Weekly Timesheet', 'One weekly timesheet of one person', 'timesheets.ts_id', fields('timesheets', ('Week starting', 'week'), ('Person', 'technician'), ('Role', 'role'), ('Clock hours', 'clock_hours'),
        ('Billed hours', 'billed_hours'), ('Drive hours', 'drive_hours'), ('Shop hours', 'shop_hours'), ('Idle hours', 'idle_hours'), ('Overtime hours', 'overtime_hours'), ('Paid hours', 'paid_hours'), ('Gross pay', 'gross_pay'),
        ('Loaded cost', 'loaded_cost'), ('Utilisation', 'utilisation'), ('Idle cost', 'idle_cost'), ('Unbilled labour cost', 'unbilled_cost'), ('Submitted on time', 'on_time'))),
    FORM('hours_sheet', 'Technician Hours Sheet', 'Hours of one technician in a period', 'scorecard.technician', fields('scorecard', ('Utilisation in the period', 'util_w'), ('Utilisation, 12 months', 'util_12m'),
        ('Idle hours, 4 weeks', 'idle_4w'), ('Overtime hours, 4 weeks', 'overtime_4w'), ('Days on the clock in the period', 'days_w'), ('Revenue per day in the period', 'rev_day'), ('Revenue per day, 12 months', 'rev_day_12m'),
        ('Unbilled labour cost in the period', 'unbilled_w'), ('Margin after unbilled time', 'net_margin')) + [FF('Utilisation target', '{set:util_target}', 'pct')]),
    FORM('overtime_sheet', 'Overtime Approval Sheet', 'Overtime to approve with its cost', 'overtime_tech.technician', fields('overtime_tech', ('Overtime hours, last 4 weeks', 'overtime_hours'), ('Overtime cost, last 4 weeks', 'overtime_cost')) + [
        FF('Limit set on the Start sheet', '{set:overtime_limit}', 'int'), FF('Hours over the limit', 'MAX(0,INDEX({range:overtime_tech.overtime_hours},MATCH({pick},{range:overtime_tech.technician},0))-{set:overtime_limit})', 'num'),
        FF('Weeks over the threshold, 12 weeks', 'COUNTIFS(%s,{pick},%s,">"&{set:overtime_after},%s)' % (TS_('technician'), TS_('paid_hours'), WK(12)), 'int'), FF('Approve by', '{today}+2', 'date'), FF('Overtime multiplier', '{set:overtime_mult}', 'num')]),
    FORM('pay_sheet', 'Pay Calculation Sheet', 'One pay row with the plan and the cost per hour', 'payroll.pay_id', fields('payroll', ('Month', 'month'), ('Person', 'person'), ('Role', 'role'), ('Pay type', 'pay_type'), ('Hours', 'hours'),
        ('Gross pay', 'gross'), ('Commission and spiffs', 'commission'), ('Employer extras', 'burden'), ('Total', 'total'), ('Pay date', 'pay_date'), ('Status', 'status'), ('Planned gross pay', 'plan_gross'), ('Over plan', 'over_plan'),
        ('Cost per hour', 'cost_hour'), ('Payroll of the month', 'month_total'))),
    FORM('commission_sheet', 'Commission Statement Sheet', 'Commission statement of one technician and month', 'comm_stmts.st_id', fields('comm_stmts', ('Month', 'month'), ('Technician', 'technician'), ('Jobs done', 'jobs_done'), ('Sold', 'sold'),
        ('Collected', 'collected'), ('Commission percent', 'rate'), ('Base used', 'base_used'), ('Commission', 'commission'), ('Spiffs', 'spiffs'), ('Clawback', 'clawback'), ('Total to pay', 'total'))),
    FORM('spiff_sheet', 'Spiff Claim Sheet', 'Spiffs claimed by one technician in one month', 'comm_stmts.st_id', fields('comm_stmts', ('Month', 'month'), ('Technician', 'technician'), ('Agreements sold', 'agreements'), ('Spiffs', 'spiffs'),
        ('Spiffs of the month, all technicians', 'month_spiffs')) + [FF('Spiff for each agreement', '{set:spiff_agreement}', 'money'),
        FF('Spiffs the agreements should pay', 'INDEX({range:comm_stmts.agreements},MATCH({pick},{range:comm_stmts.st_id},0))*{set:spiff_agreement}', 'money')]),
    FORM('clawback_sheet', 'Clawback Notice Sheet', 'Clawback of one statement with the rule behind it', 'comm_stmts.st_id', fields('comm_stmts', ('Month', 'month'), ('Technician', 'technician'), ('Clawback base, callbacks', 'clawback_base'),
        ('Clawback base, unpaid invoices', 'unpaid_base'), ('Commission percent', 'rate'), ('Commission of the month', 'commission'), ('Clawback', 'clawback'), ('Total to pay', 'total')) + [
        FF('Clawback days', '{set:clawback_days}', 'int'), FF('Share of the commission taken back', '{set:clawback_pct}', 'pct'),
        FF('Share of the commission held back', 'IFERROR(INDEX({range:comm_stmts.clawback},MATCH({pick},{range:comm_stmts.st_id},0))/INDEX({range:comm_stmts.commission},MATCH({pick},{range:comm_stmts.st_id},0)),0)', 'pct')]),
    FORM('review_sheet', 'Technician Review Sheet', 'Review of one technician against own history', 'scorecard.technician', fields('scorecard', ('Period', 'period'), ('Average ticket in the period', 'ticket'), ('Average ticket, 12 months', 'ticket_12m'),
        ('Close rate', 'close_rate'), ('Callback rate', 'callback_rate'), ('Utilisation in the period', 'util_w'), ('Utilisation, 12 months', 'util_12m'), ('Revenue per day in the period', 'rev_day'), ('Revenue per day, 12 months', 'rev_day_12m'),
        ('Reviews, last 3 months', 'reviews_90'), ('Points of 6', 'points'), ('Verdict', 'verdict'), ('Rank', 'rank_pts'))),
    FORM('one_to_one', 'One-to-One Meeting Sheet', 'Facts for a one-to-one talk with one team member', 'team.staff_id', fields('team', ('Name', 'name'), ('Role', 'role'), ('Start date', 'start'), ('Years of service', 'years'), ('Hours a week', 'hours_week'),
        ('Assignment', 'assignment'), ('Clock hours, 13 weeks', 'clock_13w'), ('Billed hours, 13 weeks', 'billed_13w'), ('Jobs assisted, 13 weeks', 'jobs_assisted'), ('Next review', 'next_review')) + [
        FF('Billed share of clock hours', 'IFERROR(INDEX({range:team.billed_13w},MATCH({pick},{range:team.staff_id},0))/INDEX({range:team.clock_13w},MATCH({pick},{range:team.staff_id},0)),0)', 'pct')]),
    FORM('hiring_sheet', 'Hiring Decision Sheet', 'One hire option with cost, break-even and capacity', 'hire_scenarios.hs_id', fields('hire_scenarios', ('Option', 'option'), ('Ramp-up months', 'ramp_months'), ('Hourly rate of the role', 'hourly'),
        ('Monthly cost, all in', 'monthly_cost'), ('Margin a job adds before technician pay', 'contribution'), ('Jobs a month to break even', 'jobs_month'), ('Jobs a week to break even', 'jobs_week'), ('Cost of the ramp-up', 'ramp_cost'),
        ('Weeks over capacity, next 13', 'weeks_over'), ('Verdict', 'verdict'))),
    FORM('apprentice_sheet', 'Apprentice Progress Sheet', 'Progress of one apprentice or team member', 'team.staff_id', fields('team', ('Name', 'name'), ('Role', 'role'), ('Start date', 'start'), ('Assignment', 'assignment'),
        ('Hourly rate', 'hourly_rate'), ('Years of service', 'years'), ('Clock hours, 13 weeks', 'clock_13w'), ('Billed hours, 13 weeks', 'billed_13w'), ('Jobs assisted, 13 weeks', 'jobs_assisted'), ('Next review', 'next_review'),
        ('All-in cost per hour', 'all_in_hour'))),
    FORM('leave_sheet', 'Leave Request Sheet', 'Leave or training period and its effect', 'leave.leave_id', fields('leave', ('Person', 'person'), ('Type', 'type'), ('First day', 'start'), ('Last day', 'end'),
        ('Working days', 'days'), ('Hours lost', 'hours_lost'), ('Status', 'status'), ('Others away at the same time', 'overlap'))),
]
assert len(forms) == 12


def D_(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
    D_('pay_statement', 'Technician Pay Statement', 'Pay statement of one person and month', 'payroll.pay_id', [
        'Pay statement of {set:company}, dated {today}. Person: {col:payroll.person}, {col:payroll.role}. Month: {col:payroll.month}. Status: {col:payroll.status}.',
        'Hours: {col:payroll.hours}. Gross pay: {col:payroll.gross}. Commission and spiffs: {col:payroll.commission}. Employer extras: {col:payroll.burden}. Total cost of this row: {col:payroll.total}. Pay date: {col:payroll.pay_date}.',
        'Planned gross pay for the month was {col:payroll.plan_gross}. Amounts are before any deductions that apply in your place. Please confirm pay rules with your adviser.'], ['Owner', 'Team member']),
    D_('commission_plan', 'Commission Plan Summary', 'Commission plan of a technician', 'comm_stmts.st_id', [
        'Commission plan of {set:company}, dated {today}. Technician: {col:comm_stmts.technician}.',
        'Commission is paid on {set:commission_base} work at {col:comm_stmts.rate} of the base. A spiff of {set:spiff_agreement} is paid for each maintenance agreement sold (a yearly plan with two tune-ups).',
        'A callback or an unpaid invoice inside {set:clawback_days} days takes back {set:clawback_pct} of the commission on that job (a clawback). Your last statement shows commission {col:comm_stmts.commission}, spiffs {col:comm_stmts.spiffs} and clawback {col:comm_stmts.clawback}.',
        'The plan is reviewed each year. Please confirm pay rules with your adviser.'], ['Owner', 'Technician']),
    D_('spiff_notice', 'Spiff List Notice', 'Notice of the spiff for one item', 'spiffs.item', [
        'Notice of {set:company}, dated {today}. A spiff is a fixed bonus for each item sold.',
        'Item: {col:spiffs.item}. Spiff amount: {col:spiffs.amount}. {col:spiffs.note}.',
        'Claims are checked against the job record before they are paid with the monthly statement.'], ['Owner']),
    D_('clawback_notice', 'Clawback Notice', 'Notice of a commission clawback', 'comm_stmts.st_id', [
        'Notice of {set:company}, dated {today}. Technician: {col:comm_stmts.technician}. Statement month: {col:comm_stmts.month}.',
        'A callback or an unpaid invoice happened inside {set:clawback_days} days of the job. Commissioned value affected: {col:comm_stmts.clawback_base} for callbacks and {col:comm_stmts.unpaid_base} for unpaid invoices.',
        'Under the plan, {set:clawback_pct} of the commission on that value is taken back: {col:comm_stmts.clawback}. Commission of the month: {col:comm_stmts.commission}. Total to pay: {col:comm_stmts.total}.',
        'Please talk to the owner if you think the record is wrong. Confirm pay rules with your adviser.'], ['Owner', 'Technician']),
    D_('scorecard_print', 'Scorecard Print', 'Scorecard of one technician against own history', 'scorecard.technician', [
        'Scorecard of {set:company}, dated {today}. Technician: {col:scorecard.technician}, period: {col:scorecard.period}.',
        'Average ticket in the period: {col:scorecard.ticket}, against {col:scorecard.ticket_12m} over 12 months. Close rate: {col:scorecard.close_rate}. Callback rate: {col:scorecard.callback_rate}.',
        'Utilisation in the period: {col:scorecard.util_w}, against {col:scorecard.util_12m} over 12 months. Revenue per day in the period: {col:scorecard.rev_day}, against {col:scorecard.rev_day_12m}. Reviews in the last 3 months: {col:scorecard.reviews_90}.',
        'Points: {col:scorecard.points} of 6. Verdict: {col:scorecard.verdict}. Targets are your own, a typical range, check your own numbers.'], ['Owner', 'Technician']),
    D_('one_to_one_record', 'One-to-One Record', 'Record of a one-to-one meeting', 'team.staff_id', [
        'One-to-one meeting record of {set:company}, dated {today}. Team member: {col:team.name}, {col:team.role}.',
        'Years of service: {col:team.years}. Clock hours over 13 weeks: {col:team.clock_13w}. Billed hours: {col:team.billed_13w}. Jobs assisted: {col:team.jobs_assisted}. Next review: {col:team.next_review}.',
        'Topics discussed: ______________________________. One change agreed for the next month: ______________________________. Training wanted: ______________________________.'], ['Owner', 'Team member']),
    D_('weekly_report', 'Weekly Hours Report', 'Hours of the crew for one week', 'hours_week.week', [
        'Weekly hours report of {set:company}, dated {today}. Week starting {col:hours_week.week}.',
        'Clock hours: {col:hours_week.clock_hours}. Billed hours: {col:hours_week.billed_hours}. Drive hours: {col:hours_week.drive_hours}. Shop hours: {col:hours_week.shop_hours}. Idle hours: {col:hours_week.idle_hours}. Overtime hours: {col:hours_week.overtime_hours}.',
        'Utilisation: {col:hours_week.utilisation} against a target of {set:util_target}; the same week last year was {col:hours_week.util_ly}. Idle time cost {col:hours_week.idle_cost}. Hours to fill to reach the target: {col:hours_week.shortfall}. Timesheets not on time: {col:hours_week.late_count}.'], ['Office manager', 'Owner']),
    D_('capacity_summary', 'Capacity and Hire Summary', 'Capacity and hire summary for the owner', 'hire_scenarios.hs_id', [
        'Capacity and hire summary of {set:company}, dated {today}. Option: {col:hire_scenarios.option}, ramp-up {col:hire_scenarios.ramp_months} months.',
        'Monthly cost, all in: {col:hire_scenarios.monthly_cost}. A job adds {col:hire_scenarios.contribution} before technician pay, so the hire needs about {col:hire_scenarios.jobs_week} jobs a week to break even. The ramp-up costs about {col:hire_scenarios.ramp_cost}.',
        'Weeks over capacity in the next 13 weeks: {col:hire_scenarios.weeks_over}. Verdict: {col:hire_scenarios.verdict}. These are estimates from your own numbers.'], ['Owner']),
    D_('offer_letter', 'Offer Letter', 'Offer letter for a technician or apprentice', 'team.staff_id', [
        'Letter of {set:company}, dated {today}. Dear {col:team.name},',
        'We are pleased to offer you the role of {col:team.role}. Pay type: {col:team.pay_type}. Hourly rate: {col:team.hourly_rate}. Hours a week: {col:team.hours_week}. Commission: {col:team.commission_pct} of the base set in the commission plan. Assignment: {col:team.assignment}.',
        'Your first review is planned for {col:team.next_review}. Pay, overtime, leave and notice terms follow the written terms of your place: please confirm with your adviser before you sign.'], ['Owner', 'Candidate']),
    D_('apprentice_plan', 'Apprentice Plan', 'Plan for an apprentice with hours and reviews', 'team.staff_id', [
        'Apprentice plan of {set:company}, dated {today}. Apprentice: {col:team.name}. Start date: {col:team.start}. Assignment: {col:team.assignment}.',
        'Hours a week: {col:team.hours_week}. Over the last 13 weeks: {col:team.clock_13w} hours on the clock, {col:team.billed_13w} billed alongside a lead and {col:team.jobs_assisted} jobs assisted. The ramp-up is reviewed each quarter; next review {col:team.next_review}.',
        'Goals for the next quarter: ______________________________. Skills to practise with a lead: ______________________________.'], ['Owner', 'Apprentice']),
    D_('overtime_rules', 'Overtime Rules Notice', 'Overtime notice with the limits in use', 'overtime_tech.technician', [
        'Notice of {set:company}, dated {today}. Team member: {col:overtime_tech.technician}.',
        'Overtime starts after {set:overtime_after} paid hours in a week and is paid at {set:overtime_mult} times the hourly rate. Overtime must be approved by the owner or the office manager before the week ends. Over the last 4 weeks you worked {col:overtime_tech.overtime_hours} overtime hours.',
        'A talk is held when overtime passes {set:overtime_limit} hours in 4 weeks. Please confirm overtime rules with your adviser.'], ['Owner', 'Team member']),
    D_('leave_calendar', 'Leave and Training Calendar', 'Leave or training entry for the calendar', 'leave.leave_id', [
        'Calendar entry of {set:company}, dated {today}. Person: {col:leave.person}. Type: {col:leave.type}.',
        'From {col:leave.start} to {col:leave.end}: {col:leave.days} working days, {col:leave.hours_lost} hours not available for jobs. Status: {col:leave.status}. Others away at the same time: {col:leave.overlap}.',
        'The office manager moves booked jobs before the first day.'], ['Office manager', 'Team member']),
]
assert len(documents) == 12
checklists = [
    CHK('timesheet_week', 'Weekly Timesheet Closed', 'hours_week', 'hours_week.week', [('Collect every timesheet of the week', 7), ('Chase the missing timesheets', 8), ('Check billed hours against the job list', 8), ('Check overtime and ask for approval', 9), ('Close the week', 9)]),
    CHK('pay_run', 'Weekly Pay Run', 'hours_week', 'hours_week.week', [('Check paid hours against the timesheets', 7), ('Check commission and spiffs on the statement', 8), ('Check clawbacks', 8), ('Send the pay figures to the accountant', 9), ('Pay the team', 10)]),
    CHK('comm_month', 'Monthly Commission Statement', 'comm_stmts', 'comm_stmts.month', [('List sold and collected work of each technician', 30), ('Count agreements sold', 30), ('Check callbacks and unpaid invoices', 31), ('Send each statement for reading', 33), ('Pay with the monthly pay run', 37)]),
    CHK('spiff_check', 'Spiff Claims Checked', 'comm_stmts', 'comm_stmts.month', [('Collect the spiff claims', 30), ('Match each claim to a job record', 31), ('Reject a claim with no record', 32), ('Add the spiffs to the statement', 33)]),
    CHK('clawback_check', 'Clawback Check', 'comm_stmts', 'comm_stmts.month', [('List callbacks of the month', 30), ('Find the commissioned jobs among them', 30), ('List invoices unpaid over your clawback days', 31), ('Write the clawback on the statement', 32), ('Tell the technician why', 33)]),
    CHK('ot_approved', 'Overtime Approved', 'hours_week', 'hours_week.week', [('List the people over your weekly threshold', 7), ('Ask the owner to approve', 8), ('Record the approval on the timesheet', 8), ('Move jobs if the limit is near', 9)]),
    CHK('score_month', 'Technician Scorecard Month', 'comm_stmts', 'comm_stmts.month', [('Update jobs and revenue of the last 12 months', 30), ('Read the scorecard of each technician', 31), ('Mark who needs a talk', 31), ('Send the scorecards', 33)]),
    CHK('one_to_one_chk', 'One-to-One Meeting', 'team', 'team.start', [('Print the Technician Review Sheet', 0), ('Read the numbers with the technician', 1), ('Agree one change for the month', 1), ('Write the note and the next date', 2)]),
    CHK('hire_decision', 'Hiring Decision', 'season_hours', 'season_hours.month', [('Run the Capacity and Hire Tool', 0), ('Run the Hire Break-Even Solver', 1), ('Check the cash floor in the Payroll Cost Forecast', 2), ('Decide: hire now, hire before the season or wait', 7), ('Write the offer or the date to look again', 10)]),
    CHK('first_week', 'New Technician First Week', 'team', 'team.start', [('Agree pay model, rate and hours in writing', -3), ('Set up the van and the tools', -1), ('Ride with a lead on day one', 0), ('Give the van and parts account details', 1), ('Review the first timesheet', 7)]),
    CHK('apprentice_review', 'Apprentice Review', 'team', 'team.start', [('Read hours billed alongside a lead', 90), ('Check the ramp-up against the plan', 90), ('Talk about skills to practise', 91), ('Write the next goals', 92)]),
    CHK('leave_plan', 'Leave and Training Planning', 'leave', 'leave.start', [('Check who else is away at the same time', -14), ('Move the booked jobs', -7), ('Tell the customers who are moved', -5), ('Confirm cover for emergency calls', -2)]),
]
assert len(checklists) == 12


def M(k_, moment, table, phone, text): return MSG(k_, moment, table, phone, text)
messages = [
    M('t_due', 'Technician: your timesheet is due', 'timesheets', 'timesheets.tech_phone', 'Hello {technician}, please submit your timesheet for the week starting {week}. {company}'),
    M('t_fix', 'Technician: please correct your hours', 'timesheets', 'timesheets.tech_phone', 'Hello {technician}, please correct your hours for the week starting {week}: clock {clock_hours}, billed {billed_hours}. {company}'),
    M('t_pay', 'Technician: your pay statement is ready', 'payroll', 'payroll.person_phone', 'Hello {person}, your pay statement for {month} is ready: total {total}. {company}'),
    M('t_comm', 'Technician: your commission this month', 'comm_stmts', 'comm_stmts.tech_phone', 'Hello {technician}, your commission for {month} is {commission}. {company}'),
    M('t_claw', 'Technician: a clawback applies and why', 'callbacks', 'callbacks.tech_phone', 'Hello {technician}, a clawback of {clawback} applies to job {original_job}: a callback came {days_after} days after the job. {company}'),
    M('t_spiff', 'Technician: your spiffs this month', 'comm_stmts', 'comm_stmts.tech_phone', 'Hello {technician}, your spiffs for {month} are {spiffs}. {company}'),
    M('t_score', 'Technician: your scorecard is ready', 'scorecard', 'scorecard.tech_phone', 'Hello {technician}, your scorecard is ready. Let us book a time to talk. {company}'),
    M('t_great', 'Technician: great month, your ticket', 'scorecard', 'scorecard.tech_phone', 'Hello {technician}, great work: your average ticket for {period} is {ticket}. {company}'),
    M('t_ot', 'Technician: overtime needs approval', 'timesheets', 'timesheets.tech_phone', 'Hello {technician}, overtime of {overtime_hours} hours in the week of {week} needs approval before {approve_by}. {company}'),
    M('t_leave', 'Technician: your leave is approved', 'leave', 'leave.tech_phone', 'Hello {person}, your leave starting {start} is approved. {company}'),
    M('t_train', 'Technician: training day', 'leave', 'leave.tech_phone', 'Hello {person}, there is a training day on {start}. {company}'),
    M('a_hours', 'Apprentice: your hours this week', 'timesheets', 'timesheets.tech_phone', 'Hello {technician}, your hours for the week of {week}: {clock_hours} on the clock, {billed_hours} billed. {company}'),
    M('a_review', 'Apprentice: your review date', 'team', 'team.phone', 'Hello {name}, your review is on {next_review}. {company}'),
    M('a_ride', 'Apprentice: you ride with a lead', 'team', 'team.phone', 'Hello {name}, you ride with {ride_with} on {ride_date}. {company}'),
    M('a_well', 'Apprentice: well done on your jobs', 'team', 'team.phone', 'Hello {name}, well done: you finished {jobs_assisted} jobs with your lead in the last 13 weeks. {company}'),
    M('t_van', 'Technician: your van has a service', 'team', 'team.phone', 'Hello {name}, your van {assignment} has a service on {van_service}. {company}'),
    M('o_missing', 'Office manager: timesheets still missing', 'hours_week', 'hours_week.office_phone', 'Timesheets still missing for the week of {week}: {late_count}. Please chase them. {company}'),
    M('o_ot', 'Office manager: overtime this week', 'hours_week', 'hours_week.office_phone', 'Overtime in the week of {week} is {overtime_hours} hours. Please check the approvals. {company}'),
    M('o_payrun', 'Office manager: pay run date', 'payroll', 'payroll.office_phone', 'The pay run for {month} is on {pay_date}. Please check the statements. {company}'),
    M('o_overlap', 'Office manager: leave overlaps', 'leave', 'leave.office_phone', 'Leave from {start}: {person} and {overlap} others are away at the same time. Please check the dispatch board. {company}'),
    M('w_util', 'Owner: utilisation this week', 'hours_week', 'hours_week.owner_phone', 'Utilisation for the week of {week} is {utilisation}. {company}'),
    M('w_idle', 'Owner: idle hours cost', 'hours_week', 'hours_week.owner_phone', 'Idle hours cost {idle_cost} in the week of {week}. {company}'),
    M('w_over', 'Owner: a technician is over overtime', 'scorecard', 'scorecard.owner_phone', '{technician} has {overtime_4w} overtime hours in 4 weeks, the limit is {overtime_limit}. {company}'),
    M('w_score', 'Owner: the scorecard is ready', 'scorecard', 'scorecard.owner_phone', 'The scorecard for {technician} is ready: {verdict}. {company}'),
    M('w_hire', 'Owner: what the hire tool says', 'hire_scenarios', 'hire_scenarios.owner_phone', 'The hire tool for {option} says: {verdict}. {company}'),
    M('w_payroll', 'Owner: payroll of the last 13 weeks', 'season_hours', 'season_hours.owner_phone', 'Payroll of the last 3 months was {payroll_13w}. The month starting {month} needs about {hours_needed} hours of work. {company}'),
    M('w_comm', 'Owner: commission total of the month', 'comm_stmts', 'comm_stmts.owner_phone', 'Commission for the month starting {month} totals {month_commission}. {company}'),
    M('w_claw', 'Owner: clawbacks of the month', 'comm_stmts', 'comm_stmts.owner_phone', 'Clawbacks for the month starting {month} total {month_clawback}. {company}'),
    M('w_gap', 'Owner: the capacity gap of a week', 'capacity_week', 'capacity_week.owner_phone', 'Capacity for the week of {week}: gap {gap} hours, check {cap_flag}. {company}'),
    M('x_acct_pay', 'Accountant: payroll summary', 'payroll', 'payroll.acct_phone', 'Hello, the payroll summary for {month} is ready: total {month_total}. {company}'),
    M('x_acct_comm', 'Accountant: commission and spiff summary', 'comm_stmts', 'comm_stmts.acct_phone', 'Hello, the commission and spiff summary for {month}: commission {month_commission}, spiffs {month_spiffs}. {company}'),
    M('x_ins', 'Insurance agent: headcount and hours', 'team', 'team.ins_phone', 'Hello, headcount and hours for the year: {field_count} field people and {hours_year} hours on the clock. {company}'),
    M('x_equip', 'Equipment supplier: training dates', 'leave', 'leave.equip_phone', 'Please send the dates of your training for new models. {person} is free on {start}. {company}'),
    M('x_counter', 'Parts counter: add a technician', 'team', 'team.counter_phone', 'Please add {name} ({role}) to our account. {company}'),
]
assert len(messages) == 34, len(messages)

TSW = lambda c_, n: 'SUMIFS(%s,%s)' % (TS_(c_), WK(n))
def UTIL(n): return 'IFERROR(%s/%s,0)' % (TSW('billed_hours', n), TSW('clock_hours', n))
CWKP = lambda c_: '{range:capacity_week.%s}' % c_
N4 = '%s,">="&%s,%s,"<="&(%s+21)' % (CWKP('week'), NW4, CWKP('week'), NW4)
PX = '{range:payroll.pay_type},"<>"&%s' % OWNDRAW
MON = lambda c_: 'SUMIFS({range:payroll.%s},{range:payroll.month},%s,%s)' % (c_, MS, PX)
SCR = lambda c_: '{range:scorecard.%s}' % c_
kpis = [
    KPI('Clock hours last week', TSW('clock_hours', 1), 'num'), KPI('Billed hours last week', TSW('billed_hours', 1), 'num'),
    KPI('Utilisation last week', UTIL(1), 'pct', alert={"when": "< {set:util_target}", "style": "warn"}), KPI('Utilisation last 4 weeks', UTIL(4), 'pct', alert={"when": "< {set:util_target}", "style": "warn"}),
    KPI('Utilisation last 12 months', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (TS_('billed_hours'), W12M, TS_('clock_hours'), W12M), 'pct'),
    KPI('Utilisation against the target, points', UTIL(4) + '-{set:util_target}', 'pct', alert={"when": "< 0", "style": "warn"}),
    KPI('Idle hours last 4 weeks', TSW('idle_hours', 4), 'num'), KPI('Cost of idle hours last 4 weeks', TSW('idle_cost', 4), 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Drive hours last 4 weeks', TSW('drive_hours', 4), 'num'), KPI('Drive share of clock hours, last 4 weeks', 'IFERROR(%s/%s,0)' % (TSW('drive_hours', 4), TSW('clock_hours', 4)), 'pct'),
    KPI('Overtime hours last 4 weeks', TSW('overtime_hours', 4), 'num', alert={"when": "> 0", "style": "warn"}), KPI('Overtime cost last 4 weeks', TSW('overtime_cost', 4), 'money'),
    KPI('Paid minus billed hours, last 4 weeks', TSW('unbilled_hours', 4), 'num'),
    KPI('Gross pay this month so far', MON('gross'), 'money'), KPI('Employer extras this month so far', MON('burden'), 'money'), KPI('Payroll total this month so far', MON('total'), 'money'),
    KPI('Pay as a share of revenue, 13 weeks', 'IFERROR(%s/SUMIFS(%s,%s),0)' % (TSW('loaded_cost', 13), JB('revenue'), J13), 'pct'),
    KPI('Commission this month so far', 'SUMIFS({range:comm_stmts.commission},{range:comm_stmts.month},%s)' % MS, 'money'),
    KPI('Spiffs last 3 months', 'SUMIFS({range:comm_stmts.spiffs},{range:comm_stmts.month},">="&EDATE(%s,-2))' % MS, 'money'),
    KPI('Clawbacks this month so far', 'SUMIFS({range:comm_stmts.clawback},{range:comm_stmts.month},%s)' % MS, 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Revenue per technician day, 13 weeks', 'IFERROR(SUMIFS(%s,%s)/SUM(%s),0)' % (JB('revenue'), J13, SCR('days_13')), 'money'),
    KPI('Highest ticket by technician', 'MAX(%s)' % SCR('ticket_13'), 'money'), KPI('Highest close rate by technician', 'MAX(%s)' % SCR('close_13'), 'pct'),
    KPI('Reviews received, last 3 months', 'SUMIFS({range:reviews.reviews_received},{range:reviews.month},">="&EDATE(%s,-3))' % MS, 'int'),
    KPI('Technicians over the overtime limit', 'COUNTIFS({range:overtime_tech.overtime_hours},">"&{set:overtime_limit})', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Booked hours next 4 weeks', 'SUMIFS(%s,%s)' % (CWKP('booked_hours'), N4), 'num'), KPI('Available hours next 4 weeks', 'SUMIFS(%s,%s)' % (CWKP('available_hours'), N4), 'num'),
    KPI('Capacity gap next 4 weeks', 'SUMIFS(%s,%s)' % (CWKP('gap'), N4), 'num', alert={"when": "< 0", "style": "bad"}),
    KPI('Weeks over capacity next 13 weeks', 'COUNTIFS(%s,">="&%s,%s,"<="&(%s+84),%s,"<0")' % (CWKP('week'), NW4, CWKP('week'), NW4, CWKP('gap')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Break-even jobs a week for a new hire', 'IFERROR(AVERAGEIFS({range:hire_scenarios.jobs_week},{range:hire_scenarios.option},%s),0)' % tok('hireopt', 'HVAC technician'), 'num'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "KPI Dashboard", "kpis": kpis,
    "monthly": {"title": "Billed, idle, drive and overtime hours", "date": "timesheets.week", "series": [
        {"label": "Billed hours", "sum": "timesheets.billed_hours", "date": "timesheets.week"}, {"label": "Idle hours", "sum": "timesheets.idle_hours", "date": "timesheets.week"},
        {"label": "Drive hours", "sum": "timesheets.drive_hours", "date": "timesheets.week"}, {"label": "Overtime hours", "sum": "timesheets.overtime_hours", "date": "timesheets.week"}]},
    "breakdowns": [{"title": "Billed hours by person", "by": "timesheets.technician", "value": "timesheets.billed_hours", "agg": "sum"}, {"title": "Payroll by person", "by": "payroll.person", "value": "payroll.total", "agg": "sum"},
                   {"title": "Callbacks by technician", "by": "callbacks.technician", "agg": "count"}, {"title": "Idle cost by person", "by": "timesheets.technician", "value": "timesheets.idle_cost", "agg": "sum"}]}
P13W = [('period', '=', tok('period', 'Last 13 weeks'))]
def BY(title, typ, tbl, col, agg, val, label, where=None): return CHART(title, typ, '%s.%s' % (tbl, col), [AGG(agg, tbl, ('%s.%s' % (tbl, val)) if val else None, where=where, label=label)])
def MO(title, typ, tbl, dcol, val, label, agg='sum'): return CHART(title, typ, 'month', [AGG(agg, tbl, ('%s.%s' % (tbl, val)) if val else None, date='%s.%s' % (tbl, dcol), label=label)])
insights = {"filters": [{"label": "Technician", "list": "tech"}, {"label": "Job type", "list": "jobtype"}],
    "gauges": [
        {"title": "Weeks on the utilisation target", "num": AGG('count', 'timesheets', where=[('util_flag', '=', ck('On target'))]), "den": AGG('count', 'timesheets')},
        {"title": "Paid hours that were billed", "num": AGG('sum', 'timesheets', 'timesheets.billed_hours'), "den": AGG('sum', 'timesheets', 'timesheets.paid_hours')},
        {"title": "Timesheets submitted on time", "num": AGG('count', 'timesheets', where=[('on_time', '=', YES)]), "den": AGG('count', 'timesheets')},
        {"title": "Technicians within the overtime limit", "num": AGG('count', 'overtime_tech', where=[('overtime_hours', '<=', '{set:overtime_limit}')]), "den": AGG('count', 'overtime_tech')},
        {"title": "Booked hours against capacity", "num": AGG('sum', 'capacity_week', 'capacity_week.booked_hours', where=[('week', '>', '{today}')]), "den": AGG('sum', 'capacity_week', 'capacity_week.available_hours', where=[('week', '>', '{today}')])},
        {"title": "Payroll rows within plan", "num": AGG('count', 'payroll', where=[('within_plan', '=', 1)]), "den": AGG('count', 'payroll')}],
    "charts": [
        BY('Billed hours per week', 'line', 'hours_week', 'wk', 'sum', 'billed_hours', 'Billed hours'), BY('Utilisation per week', 'line', 'hours_week', 'wk', 'avg', 'utilisation', 'Utilisation'),
        BY('Clock hours by person', 'bar', 'timesheets', 'technician', 'sum', 'clock_hours', 'Clock hours'), BY('Billed hours by person', 'bar', 'timesheets', 'technician', 'sum', 'billed_hours', 'Billed hours'),
        BY('Idle hours by person', 'bar', 'timesheets', 'technician', 'sum', 'idle_hours', 'Idle hours'), BY('Drive hours by person', 'bar', 'timesheets', 'technician', 'sum', 'drive_hours', 'Drive hours'),
        MO('Overtime hours per month', 'column', 'timesheets', 'week', 'overtime_hours', 'Overtime hours'), MO('Payroll total per month', 'column', 'payroll', 'month', 'total', 'Payroll total'),
        BY('Gross pay by person', 'bar', 'payroll', 'person', 'sum', 'gross', 'Gross pay'), MO('Employer extras per month', 'column', 'payroll', 'month', 'burden', 'Employer extras'),
        MO('Commission per month', 'column', 'comm_stmts', 'month', 'commission', 'Commission'), MO('Spiffs per month', 'column', 'comm_stmts', 'month', 'spiffs', 'Spiffs'),
        MO('Clawbacks per month', 'column', 'comm_stmts', 'month', 'clawback', 'Clawbacks'), BY('Revenue per day by technician', 'bar', 'scorecard', 'technician', 'avg', 'rev_day', 'Revenue per day', P13W),
        BY('Ticket by technician', 'bar', 'scorecard', 'technician', 'avg', 'ticket', 'Average ticket', P13W), BY('Close rate by technician', 'bar', 'scorecard', 'technician', 'avg', 'close_rate', 'Close rate', P13W),
        BY('Callback rate by technician', 'bar', 'scorecard', 'technician', 'avg', 'callback_rate', 'Callback rate', P13W), MO('Reviews received per month', 'column', 'reviews', 'month', 'reviews_received', 'Reviews received'),
        CHART('Booked hours against available hours per month', 'column', 'month', [AGG('sum', 'capacity_week', 'capacity_week.booked_hours', date='capacity_week.week', label='Booked and expected hours'),
              AGG('sum', 'capacity_week', 'capacity_week.available_hours', date='capacity_week.week', label='Available hours')]),
        MO('Hours needed by month', 'column', 'season_hours', 'month', 'hours_needed', 'Hours needed'), MO('Idle cost per month', 'column', 'timesheets', 'week', 'idle_cost', 'Idle cost'),
        BY('Pay by pay type', 'bar', 'payroll', 'pay_type', 'sum', 'total', 'Payroll total')]}
assert len(insights['charts']) == 22

signature = [
    {"name": "Technician hours analyser", "why": "clock, billed, drive, shop and idle hours of each person, the utilisation gap, what idle time costs and who has room for the jobs", "where": "Technician Hours Analyser"},
    {"name": "Paid vs billed gap in money", "why": "the labour you paid for and did not bill, ranked by person and month with a traffic light", "where": "Paid vs Billed Gap"},
    {"name": "Pay calculator for every pay model", "why": "hourly, flat-rate, salary plus commission or mixed pay with overtime and employer extras, plus the cost per billed hour", "where": "Pay Calculator"},
    {"name": "Pay model comparison", "why": "the same week under each model: the cheapest for the shop and the best for the technician", "where": "Pay Model Comparison"},
    {"name": "Commission calculator with clawback", "why": "commission on sold or collected work with a tier, spiffs and a clawback for callbacks and unpaid invoices", "where": "Commission Calculator"},
    {"name": "Technician statement a person can read", "why": "hours, sales, commission, spiffs and clawbacks of one month on one page", "where": "Technician Statement"},
    {"name": "Technician scorecard against own history", "why": "six measures against your targets and each own 12 months, with points, rank and the first topic for a one-to-one talk", "where": "Technician Scorecard"},
    {"name": "Capacity and hire tool", "why": "booked against available hours for 26 weeks and a verdict: hire now, hire before the season or wait", "where": "Capacity and Hire Tool"},
    {"name": "Hire break-even solver", "why": "the extra jobs a week a new technician must bring, with the same at minus and plus 10 percent utilisation", "where": "Hire Break-Even Solver"},
    {"name": "Payroll cost forecast with scenarios", "why": "payroll for the next 13 weeks from your last 6 months and the season, with Base, Best and Worst rows and the effect on your cash floor", "where": "Payroll Cost Forecast"}]
competitors = [
    {"what": "field-service app with a per-technician fee", "lacks": "charges every month per person and keeps pay and commission rules hidden, so you cannot test a pay model or a clawback rule yourself"},
    {"what": "generic payroll template", "lacks": "adds up hours and pay but knows nothing about billed hours, drive time, idle cost or a commission with a clawback"},
    {"what": "single-sheet timesheet", "lacks": "collects hours only, with no utilisation against a target, no overtime warning and no link to jobs and revenue"},
    {"what": "pen-and-paper job book", "lacks": "keeps no history, so idle time, callbacks per technician and the cost of an unbilled hour are never counted"},
    {"what": "free hiring checklist", "lacks": "lists questions but never works out the jobs a week a new technician must bring to pay for the hire"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: utilisation target, overtime hours, clawback days and share, spiff, employer extras and cash floor. Pay figures: confirm with your adviser.',
    'Check Team: one row per person with role, pay type, hourly rate or salary, hours a week and commission percent. Everything else reads this sheet.',
    'Type each week of hours on Timesheets: clock, billed, drive, shop and idle hours, overtime and pay. Utilisation, idle cost and the unbilled labour cost fill in by themselves.',
    'Add every pay run to Payroll. Hours by Week and Capacity by Week add up the crew for you.',
    'Fill Commission Statements with the sold and collected work, the agreements sold and the clawback bases of each month. Commission, spiffs, clawback and the total fill in by themselves.',
    'Keep the Spiff List and the Commission Rules to your own numbers, and record every Callback so the clawback follows.',
    'Type the jobs and revenue of the last 12 months on Scorecard by Technician. Jobs, Estimates and Reviews and Referrals feed ticket, close rate, callback rate and reviews.',
    'Add leave and training days on Leave and Training; Capacity by Week takes them off the available hours.',
    f'Use the {len(tools)} tools: hours analysis, the paid versus billed gap, pay and commission calculators, clawback, statements, scorecards, overtime, capacity, hire break-even, apprentice ramp and the payroll forecast.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A shop with one technician and one apprentice uses the same sheets: type two people on Team and Timesheets.',
    'Read the KPI Dashboard and Charts every Monday: utilisation, idle cost, overtime, payroll, commission, capacity gap and weeks over capacity.']
listing = {"title": "HVAC and Plumbing Technician Hours, Pay, Commission and Capacity Excel Template: Utilisation, Spiffs, Clawbacks, Hire Break-Even",
    "headline": "Know what every technician hour costs and when to hire",
    "tags": ["hvac template", "plumbing template", "technician pay", "commission tracker", "tech utilisation", "payroll excel", "capacity planning", "hiring break even", "timesheet template", "contractor excel", "spiff tracker", "overtime tracker", "apprentice plan"],
    "description": ("Run the people side of an HVAC and plumbing business in one Excel workbook. Built for a small owner-run service shop with 1 to 15 technicians, or an owner-operator with one technician and one apprentice.\n\n"
        "Timesheets hold the hours of every person each week: clock, billed, drive, shop and idle hours, overtime, pay and loaded cost. Utilisation (billed hours over hours on the clock), the cost of idle time and the paid-but-unbilled gap in money fill in by themselves, with a weekly view against your own target and the same week last year.\n\n"
        "The Pay Calculator and the Pay Model Comparison work out hourly, flat-rate, salary plus commission and mixed pay, with overtime and employer extras from Settings, the all-in cost per clock hour and per billed hour, and the model that is cheapest for the shop. "
        "Commission Statements calculate commission on sold or collected work, spiffs (a fixed bonus for each item sold) and clawbacks (a commission amount taken back after a callback or an unpaid invoice), and the Technician Statement prints one month a person can read.\n\n"
        "The Technician Scorecard puts ticket, close rate, callback rate, utilisation, revenue per day and reviews against each technician's own history, with points, rank and a verdict for the one-to-one talk. "
        "Capacity by Week sets booked hours against the hours your people can work after leave, with the season in mind; the Capacity and Hire Tool, the Hire Break-Even Solver and the Apprentice Ramp tell you whether to hire a technician or an apprentice, now or before the season, and how many extra jobs a week it takes to pay for the hire. The Payroll Cost Forecast shows the next 13 weeks with Base, Best and Worst rows and the effect on your cash floor.\n\n"
        f"{len(tools)} tools, {len(forms)} printable sheets, {len(documents)} documents, {len(checklists)} checklists and {len(messages)} ready text messages to technicians, apprentices, the office manager, the owner, your accountant and your insurance agent are included.\n\n"
        "This is part four of the HVAC and Plumbing Contractor suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data. Pay, overtime and tax figures are examples: confirm them with your adviser. It helps you keep track of hours, pay and capacity and does not promise results."),
    "features": ["Weekly timesheets with utilisation and idle cost", "Paid versus billed gap in money by person", "Pay calculator for four pay models", "Commission with spiffs and clawbacks", "Technician statement a person can read",
                 "Scorecard against each own history", "Booked against available hours by week", "Hire break-even solver and apprentice ramp", "Payroll cost forecast with Base, Best and Worst", f"{len(tools)} decision tools",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p4', slug='hvac-plumbing-technicians', profession='HVAC and Plumbing Contractor', name='Technicians: Hours, Pay and Capacity',
         tagline='Know what every technician hour costs and when to hire', price_usd=29, colors={"primary": "#1F4E5F", "accent": "#E07A3F"},
         settings=settings, lists=base_lists + ck_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
         suite={"key": SUITE, "part": 4, "of": 8, "focus": "Technician hours, pay, commission and capacity"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hv4.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(s['lists']), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
