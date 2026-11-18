"""Home care agency suite - part 2: Schedule, Matching and Cover."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from hc2_lists import *
from hc2_tables import settings, tables, CA
from hc2_tools import tools

NOTE = "Sample wording: adapt it to your own agency and check your own local rules."
YES = '{list:yesno.yes}'
def F(*p): return [FV(a, b) for a, b in p]
def ONE(tb, col, idc): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (tb, col, tb, idc)
NXT = '({today}-WEEKDAY({today},2)+8)'
CANC = '"<>"&' + tok('vstatus', 'Cancelled')
OPENC = '"<>"&' + ck('Closed')

forms = [
 FORM('schedule_change', 'Schedule Change Sheet', 'Schedule change for one visit', 'schedule.visit_id', F(
  ('Date', 'schedule.date'), ('Start', 'schedule.start'), ('End', 'schedule.end_time'), ('Hours', 'schedule.sched_hours'), ('Client', 'schedule.client'), ('Client phone', 'schedule.client_phone'), ('Area', 'schedule.area'),
  ('Service', 'schedule.service'), ('Time band', 'schedule.band'), ('Planned caregiver', 'schedule.planned'), ('Caregiver', 'schedule.caregiver'), ('Caregiver phone', 'schedule.caregiver_phone'),
  ('Cover type', 'schedule.cover_type'), ('Status', 'schedule.status'), ('Days ahead', 'schedule.days_ahead')) + [
  FF('Visits of this caregiver that day', 'COUNTIFS({range:schedule.caregiver},%s,{range:schedule.date},%s,{range:schedule.status},%s)' % (ONE('schedule', 'caregiver', 'visit_id'), ONE('schedule', 'date', 'visit_id'), CANC), 'int'),
  FF('Hours of this caregiver that day', 'SUMIFS({range:schedule.sched_hours},{range:schedule.caregiver},%s,{range:schedule.date},%s,{range:schedule.status},%s)' % (ONE('schedule', 'caregiver', 'visit_id'), ONE('schedule', 'date', 'visit_id'), CANC), 'num')]),
 FORM('calloff_sheet', 'Call-off Sheet', 'Call-off with cover and premium', 'calloffs.calloff_id', F(
  ('Date', 'calloffs.date'), ('Visit ID', 'calloffs.visit_id'), ('Client', 'calloffs.client'), ('Area', 'calloffs.area'), ('Weekday', 'calloffs.weekday'), ('Caregiver', 'calloffs.caregiver'), ('Reason', 'calloffs.reason'),
  ('Notice, hours', 'calloffs.notice_hours'), ('Visit hours', 'calloffs.hours'), ('Cover caregiver', 'calloffs.cover_caregiver'), ('Cover caregiver phone', 'calloffs.cover_phone'), ('Minutes to find cover', 'calloffs.minutes_to_cover'),
  ('Premium paid', 'calloffs.premium'), ('Premium per hour', 'calloffs.premium_per_hour'), ('Covered', 'calloffs.covered')) + [
  FF('Call-offs by this caregiver, last 90 days', 'COUNTIFS({range:calloffs.caregiver},%s,{range:calloffs.date},">="&({today}-90))' % ONE('calloffs', 'caregiver', 'calloff_id'), 'int'),
  FF('Call-offs of all caregivers, last 90 days', 'COUNTIFS({range:calloffs.date},">="&({today}-90))', 'int')]),
 FORM('cover_offer', 'Cover Offer Sheet', 'Cover offer to a candidate caregiver', 'match_scores.score_id', F(
  ('Open shift', 'match_scores.open_shift'), ('Shift date', 'match_scores.shift_date'), ('Shift start', 'match_scores.shift_start'), ('Shift hours', 'match_scores.shift_hours'), ('Client', 'match_scores.client'),
  ('Service', 'match_scores.service'), ('Candidate', 'match_scores.caregiver'), ('Candidate phone', 'match_scores.phone'), ('Pay rate per hour', 'match_scores.pay'), ('Hours booked that week', 'match_scores.hours_booked'),
  ('Match score', 'match_scores.total_score'), ('Rank for the shift', 'match_scores.rank_in_shift'), ('Cost of this option', 'match_scores.option_cost')) + [
  FF('Candidates scored for this shift', 'COUNTIFS({range:match_scores.open_shift},%s)' % ONE('match_scores', 'open_shift', 'score_id'), 'int'),
  FF('Cheapest cost among them', 'IFERROR(SUMPRODUCT(MIN(({range:match_scores.open_shift}=%s)*{range:match_scores.hours_booked}*0+({range:match_scores.open_shift}=%s)*99999)),0)*0+%s' % (ONE('match_scores', 'open_shift', 'score_id'), ONE('match_scores', 'open_shift', 'score_id'), ONE('match_scores', 'option_cost', 'score_id')), 'money')]),
 FORM('open_shift_sheet', 'Open Shift Sheet', 'Open shift with the best candidate', 'open_shifts.visit_id', F(
  ('Date', 'open_shifts.date'), ('Start', 'open_shifts.start'), ('Hours', 'open_shifts.hours'), ('Client', 'open_shifts.client'), ('Area', 'open_shifts.area'), ('Service', 'open_shifts.service'), ('Language wanted', 'open_shifts.language'),
  ('Status', 'open_shifts.status'), ('Filled on', 'open_shifts.filled_on'), ('Filled by', 'open_shifts.caregiver'), ('Days ahead', 'open_shifts.days_ahead'), ('Urgency', 'open_shifts.urgency'), ('Days filled ahead', 'open_shifts.filled_ahead')) + [
  FF('Candidates scored', 'COUNTIFS({range:match_scores.open_shift},{pick})', 'int'), FF('Best candidate', 'IFERROR(INDEX({range:match_scores.caregiver},MATCH({pick}&"|1",{range:match_scores.rank_key},0)),"")', 'text'),
  FF('Best match score', 'SUMIFS({range:match_scores.total_score},{range:match_scores.open_shift},{pick},{range:match_scores.rank_in_shift},1)', 'int'),
  FF('Cost of the best option', 'SUMIFS({range:match_scores.option_cost},{range:match_scores.open_shift},{pick},{range:match_scores.rank_in_shift},1)', 'money')]),
 FORM('timeoff_sheet', 'Time Off Request Sheet', 'Time off request with visits already scheduled', 'time_off.timeoff_id', F(
  ('Caregiver', 'time_off.caregiver'), ('Caregiver phone', 'time_off.caregiver_phone'), ('Kind', 'time_off.kind'), ('Start', 'time_off.start_date'), ('End', 'time_off.end_date'), ('Days', 'time_off.days'), ('Approved', 'time_off.approved'),
  ('Visits already scheduled in the period', 'time_off.visits_in_period')) + [
  FF('Time off days this year for this caregiver', 'SUMIFS({range:time_off.days},{range:time_off.caregiver},%s,{range:time_off.start_date},">="&DATE(YEAR({today}),1,1),{range:time_off.start_date},"<"&DATE(YEAR({today})+1,1,1))' % ONE('time_off', 'caregiver', 'timeoff_id'), 'int'),
  FF('Caregivers with approved time off at the same time', 'COUNTIFS({range:time_off.start_date},"<="&%s,{range:time_off.end_date},">="&%s,{range:time_off.approved},%s)' % (ONE('time_off', 'end_date', 'timeoff_id'), ONE('time_off', 'start_date', 'timeoff_id'), YES), 'int')]),
 FORM('avail_sheet', 'Availability Update Sheet', 'Availability window of a caregiver', 'availability.avail_id', F(
  ('Caregiver', 'availability.caregiver'), ('Caregiver phone', 'availability.caregiver_phone'), ('Weekday', 'availability.weekday'), ('From', 'availability.from_time'), ('To', 'availability.to_time'), ('Most hours', 'availability.max_hours'),
  ('Window hours', 'availability.window_hours')) + [
  FF('Weekly limit of the caregiver', 'IFERROR(INDEX({range:caregivers.hours_limit},MATCH(%s,{range:caregivers.name},0)),0)' % ONE('availability', 'caregiver', 'avail_id'), 'int'),
  FF('Days a week with a window', 'COUNTIFS({range:availability.caregiver},%s)' % ONE('availability', 'caregiver', 'avail_id'), 'int'),
  FF('Window hours a week', 'SUMIFS({range:availability.window_hours},{range:availability.caregiver},%s)' % ONE('availability', 'caregiver', 'avail_id'), 'num')]),
 FORM('swap_sheet', 'Shift Swap Sheet', 'Shift swap check: the week of one caregiver', 'grid_cg.row_id', F(
  ('Week', 'grid_cg.week'), ('Caregiver', 'grid_cg.caregiver'), ('Caregiver ID', 'grid_cg.caregiver_id'), ('Employment type', 'grid_cg.employment'), ('Area', 'grid_cg.area'), ('Weekly limit, hours', 'grid_cg.hours_limit'),
  ('Scheduled hours', 'grid_cg.scheduled_hours'), ('Days worked', 'grid_cg.days_worked'), ('Longest run, days', 'grid_cg.longest_run'), ('Free hours', 'grid_cg.free_hours'), ('Hours over the line', 'grid_cg.over_hours'),
  ('Hours check', 'grid_cg.load_flag'), ('Days-off check', 'grid_cg.days_flag'), ('Caregiver phone', 'grid_cg.phone')) + [
  FF('Hours a swap can add before the overtime line', 'MAX(0,{set:overtime_hours}-%s)' % ONE('grid_cg', 'scheduled_hours', 'row_id'), 'num')]),
 FORM('client_change_sheet', 'Client Visit Change Sheet', 'Client visit change with the next 14 days', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Client phone', 'clients.phone'), ('Area', 'clients.area'), ('Service', 'clients.service'), ('Agreed weekly hours', 'clients.weekly_hours'), ('Language', 'clients.language'),
  ('Preferred caregiver', 'clients.preferred'), ('Second preferred caregiver', 'clients.preferred_2'), ('Status', 'clients.status')) + [
  FF('Visits in the next 14 days', 'COUNTIFS({range:schedule.client},%s,{range:schedule.date},">="&{today},{range:schedule.date},"<"&({today}+14),{range:schedule.status},%s)' % (ONE('clients', 'client', 'client_id'), CANC), 'int'),
  FF('Hours in the next 14 days', 'SUMIFS({range:schedule.sched_hours},{range:schedule.client},%s,{range:schedule.date},">="&{today},{range:schedule.date},"<"&({today}+14),{range:schedule.status},%s)' % (ONE('clients', 'client', 'client_id'), CANC), 'num'),
  FF('Open shifts for this client', 'COUNTIFS({range:open_shifts.client},%s,{range:open_shifts.urgency},%s)' % (ONE('clients', 'client', 'client_id'), OPENC), 'int'),
  FF('Caregivers seen in 28 days', 'IFERROR(INDEX({range:continuity.caregivers_28d},MATCH({pick},{range:continuity.client_id},0)),0)', 'int')]),
 FORM('standby_sheet', 'Standby Roster Sheet', 'Standby caregiver with free hours and covers', 'caregivers.caregiver_id', F(
  ('Name', 'caregivers.name'), ('Phone', 'caregivers.phone'), ('Area', 'caregivers.area'), ('Employment type', 'caregivers.employment'), ('Availability', 'caregivers.availability'), ('Weekly limit, hours', 'caregivers.hours_limit'),
  ('On the standby pool', 'caregivers.standby'), ('Pay rate per hour', 'caregivers.pay_rate')) + [
  FF('Booked hours next week', 'SUMIFS({range:grid_cg.scheduled_hours},{range:grid_cg.caregiver_id},{pick},{range:grid_cg.week},%s)' % NXT, 'num'),
  FF('Free hours next week', '%s-SUMIFS({range:grid_cg.scheduled_hours},{range:grid_cg.caregiver_id},{pick},{range:grid_cg.week},%s)' % (ONE('caregivers', 'hours_limit', 'caregiver_id'), NXT), 'num'),
  FF('Visits covered, last 90 days', 'COUNTIFS({range:calloffs.cover_caregiver},%s,{range:calloffs.date},">="&({today}-90))' % ONE('caregivers', 'name', 'caregiver_id'), 'int'),
  FF('Premium earned, last 90 days', 'SUMIFS({range:calloffs.premium},{range:calloffs.cover_caregiver},%s,{range:calloffs.date},">="&({today}-90))' % ONE('caregivers', 'name', 'caregiver_id'), 'money')]),
 FORM('holiday_sheet', 'Holiday Cover Sheet', 'Holiday cover with visits and open hours', 'holidays.date', F(
  ('Holiday', 'holidays.holiday'), ('Weekday', 'holidays.weekday'), ('Pay multiplier', 'holidays.pay_mult'), ('Bill multiplier', 'holidays.bill_mult'), ('Days ahead', 'holidays.days_ahead'), ('Visits that day', 'holidays.visits_on'),
  ('Hours that day', 'holidays.hours_on'), ('Open shift hours', 'holidays.open_hours'), ('Extra caregivers needed', 'holidays.extra_caregivers')) + [
  FF('Caregivers with approved time off that day', 'COUNTIFS({range:time_off.start_date},"<="&{pick},{range:time_off.end_date},">="&{pick},{range:time_off.approved},%s)' % YES, 'int'),
  FF('Caregivers on the standby pool', 'COUNTIFS({range:caregivers.standby},%s,{range:caregivers.status},%s)' % (YES, tok('cgstatus', 'Active')), 'int')]),
 FORM('match_sheet', 'Caregiver Match Sheet', 'Caregiver profile for matching', 'caregivers.caregiver_id', F(
  ('Name', 'caregivers.name'), ('Employment type', 'caregivers.employment'), ('Area', 'caregivers.area'), ('Skills', 'caregivers.skills'), ('Languages', 'caregivers.languages'), ('Availability', 'caregivers.availability'),
  ('Weekly limit, hours', 'caregivers.hours_limit'), ('Pay rate per hour', 'caregivers.pay_rate'), ('Hire date', 'caregivers.hire_date'), ('Phone', 'caregivers.phone')) + [
  FF('Free hours next week', '%s-SUMIFS({range:grid_cg.scheduled_hours},{range:grid_cg.caregiver_id},{pick},{range:grid_cg.week},%s)' % (ONE('caregivers', 'hours_limit', 'caregiver_id'), NXT), 'num'),
  FF('Times scored as a candidate', 'COUNTIFS({range:match_scores.caregiver},%s)' % ONE('caregivers', 'name', 'caregiver_id'), 'int'),
  FF('Times ranked first', 'COUNTIFS({range:match_scores.caregiver},%s,{range:match_scores.rank_in_shift},1)' % ONE('caregivers', 'name', 'caregiver_id'), 'int'),
  FF('Average match score as a candidate', 'IFERROR(AVERAGEIFS({range:match_scores.total_score},{range:match_scores.caregiver},%s),0)' % ONE('caregivers', 'name', 'caregiver_id'), 'int')]),
 FORM('continuity_sheet', 'Continuity Review Sheet', 'Continuity review for one client', 'continuity.client_id', F(
  ('Client', 'continuity.client'), ('Client phone', 'continuity.client_phone'), ('Caregivers in 28 days', 'continuity.caregivers_28d'), ('Main caregiver', 'continuity.main_caregiver'), ('Hours by main caregiver', 'continuity.main_hours'),
  ('Hours', 'continuity.hours'), ('Main caregiver share', 'continuity.main_share'), ('Over the limit by', 'continuity.over_by'), ('Continuity check', 'continuity.cont_flag')) + [
  FF('Preferred caregiver of the client', 'IFERROR(INDEX({range:clients.preferred},MATCH({pick},{range:clients.client_id},0))&"","")', 'text'),
  FF('Agreed weekly hours', 'IFERROR(INDEX({range:clients.weekly_hours},MATCH({pick},{range:clients.client_id},0)),0)', 'num'),
  FF('Agency average caregivers per client', 'AVERAGE({range:continuity.caregivers_28d})', 'num')]),
]
assert len(forms) == 12

def D_(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('doc_cg_week', 'Caregiver Schedule', 'Weekly schedule for a caregiver', 'grid_cg.row_id', [
  'Weekly schedule of {set:company}, dated {today}. Caregiver: {col:grid_cg.caregiver}. Week of {col:grid_cg.week}.',
  'Scheduled hours: {col:grid_cg.scheduled_hours} on {col:grid_cg.days_worked} days, {col:grid_cg.visits_week} visits. Weekly limit: {col:grid_cg.hours_limit} hours. Free hours: {col:grid_cg.free_hours}.',
  'The visit times, the first name and area of each client and the travel gaps are listed on the Schedule page for this caregiver and week; print them with this page. Hours check: {col:grid_cg.load_flag}. Days-off check: {col:grid_cg.days_flag}.',
  'Please tell the scheduler as early as you can if you cannot take a visit. Phone: {col:grid_cg.scheduler_phone}.'], ['Scheduler', 'Caregiver']),
 D_('doc_cl_week', 'Client Schedule', 'Weekly schedule for a client', 'grid_cl.row_id', [
  'Weekly schedule of {set:company}, dated {today}. Client: {col:grid_cl.client}. Week of {col:grid_cl.week}.',
  'Scheduled hours: {col:grid_cl.scheduled_hours}. Different caregivers this week: {col:grid_cl.caregivers_seen}. Hours by the main caregiver: {col:grid_cl.main_hours}.',
  'The visit times and the caregiver of each visit are listed on the Schedule page for this client and week; print them with this page. Please tell us about any change as early as you can.'], ['Scheduler']),
 D_('doc_open', 'Open Shift Notice', 'Open shift notice', 'open_shifts.visit_id', [
  'Open shift notice of {set:company}, dated {today}. Visit {col:open_shifts.visit_id}.',
  'Date: {col:open_shifts.date}. Start: {col:open_shifts.start}. Hours: {col:open_shifts.hours}. Client: {col:open_shifts.client}, {col:open_shifts.area}. Service: {col:open_shifts.service}. Language wanted: {col:open_shifts.language}.',
  'Status: {col:open_shifts.status}. Days ahead: {col:open_shifts.days_ahead}. Urgency: {col:open_shifts.urgency}. Please phone the scheduler if you can take this shift: {col:open_shifts.scheduler_phone}.'], ['Scheduler']),
 D_('doc_offer', 'Cover Offer Letter', 'Cover offer letter', 'match_scores.score_id', [
  'Cover offer of {set:company}, dated {today}. Dear {col:match_scores.caregiver},',
  'Can you cover {col:match_scores.service} for {col:match_scores.client} on {col:match_scores.shift_date} at {col:match_scores.shift_start}, {col:match_scores.shift_hours} hours? You are ranked {col:match_scores.rank_in_shift} for this shift with a match score of {col:match_scores.total_score}.',
  'Cover found at short notice carries a cover premium of {set:cover_premium} per hour. Please reply today. Reference {col:match_scores.score_id}.'], ['Scheduler']),
 D_('doc_change', 'Schedule Change Notice', 'Schedule change notice to a client', 'schedule.visit_id', [
  'Schedule change notice of {set:company}, dated {today}. Dear {col:schedule.client},',
  'Your visit on {col:schedule.date} at {col:schedule.start}, {col:schedule.sched_hours} hours, is now with {col:schedule.caregiver}. Your planned caregiver was {col:schedule.planned}. Cover type: {col:schedule.cover_type}.',
  'Thank you for your understanding. If the time does not suit you, please phone us. Visit {col:schedule.visit_id}.'], ['Scheduler']),
 D_('doc_holiday', 'Holiday Schedule Notice', 'Holiday schedule notice', 'holidays.date', [
  'Holiday schedule notice of {set:company}, dated {today}. Holiday: {col:holidays.holiday}, {col:holidays.weekday} {col:holidays.date}.',
  'Visits in the schedule that day: {col:holidays.visits_on}, {col:holidays.hours_on} hours. The holiday rate is {col:holidays.bill_mult} times the usual rate for clients and {col:holidays.pay_mult} times for caregivers (a holiday is a bank holiday or public holiday).',
  'Open shift hours still to cover: {col:holidays.open_hours}. Extra caregivers needed: {col:holidays.extra_caregivers}. Please confirm your availability with the scheduler.'], ['Owner', 'Scheduler']),
 D_('doc_avail', 'Availability Sheet', 'Caregiver availability sheet', 'availability.avail_id', [
  'Availability sheet of {set:company}, dated {today}. Caregiver: {col:availability.caregiver}.',
  'Weekday: {col:availability.weekday}. Available from {col:availability.from_time} to {col:availability.to_time} ({col:availability.window_hours} hours), at most {col:availability.max_hours} hours a week.',
  'Please check the window and tell the scheduler about any change. Phone: {col:availability.caregiver_phone}.'], ['Caregiver', 'Scheduler']),
 D_('doc_calloff_month', 'Call-off Report', 'Call-off report for the month', 'cover_month.row_id', [
  'Call-off report of {set:company}, dated {today}. Month {col:cover_month.month}.',
  'Call-offs: {col:cover_month.call_offs}. Covered: {col:cover_month.covered}. Uncovered: {col:cover_month.uncovered}. Covered share: {col:cover_month.covered_share}.',
  'Cover premium paid: {col:cover_month.premium_paid}. Overtime hours caused by cover: {col:cover_month.overtime_hours}. Cost per call-off: {col:cover_month.cost_per_calloff}.',
  'Decisions for the month-end cover review are written below.'], ['Owner', 'Scheduler']),
 D_('doc_fill', 'Fill Rate Report', 'Weekly fill rate report', 'fill_week.row_id', [
  'Weekly fill rate report of {set:company}, dated {today}. Week of {col:fill_week.week}.',
  'Scheduled hours: {col:fill_week.scheduled_hours}. Planned: {col:fill_week.planned_hours}. Cover: {col:fill_week.cover_hours}. Uncovered: {col:fill_week.uncovered_hours}. Fill rate: {col:fill_week.fill_rate}. Target check: {col:fill_week.fill_flag}.',
  'Target fill rate: {set:fill_rate_target}. Overtime hours in the week: {col:fill_week.overtime_hours}. Cover premium for payroll: {col:fill_week.cover_premium_amount}.'], ['Scheduler', 'Owner']),
 D_('doc_overtime', 'Overtime Watch List', 'Overtime watch list for one caregiver week', 'grid_cg.row_id', [
  'Overtime watch of {set:company}, dated {today}. Caregiver: {col:grid_cg.caregiver}. Week of {col:grid_cg.week}.',
  'Scheduled hours: {col:grid_cg.scheduled_hours}. The overtime line is {set:overtime_hours} hours; hours over the line: {col:grid_cg.over_hours}. Weekly limit of the caregiver: {col:grid_cg.hours_limit}. Hours check: {col:grid_cg.load_flag}.',
  'Overtime is paid at {set:overtime_mult} times (confirm with your adviser). Decide which visits move to another caregiver and note it below.'], ['Scheduler', 'Owner']),
 D_('doc_continuity', 'Continuity Report', 'Continuity report for one client', 'continuity.client_id', [
  'Continuity report of {set:company}, dated {today}. Client: {col:continuity.client}.',
  'Different caregivers in the last 28 days: {col:continuity.caregivers_28d} (limit {set:continuity_limit}). Main caregiver: {col:continuity.main_caregiver}, {col:continuity.main_hours} of {col:continuity.hours} hours, a share of {col:continuity.main_share}. Check: {col:continuity.cont_flag}.',
  'Actions for the next 4 weeks are written below.'], ['Scheduler', 'Field supervisor']),
 D_('doc_standby', 'Standby Roster', 'Standby roster entry for a caregiver', 'caregivers.caregiver_id', [
  'Standby roster of {set:company}, dated {today}. Caregiver: {col:caregivers.name}, phone {col:caregivers.phone}.',
  'Area: {col:caregivers.area}. Availability: {col:caregivers.availability}. Weekly limit: {col:caregivers.hours_limit} hours. On the standby pool: {col:caregivers.standby}.',
  'A caregiver on standby keeps the phone on and takes short-notice cover. Cover found at short notice earns a premium of {set:cover_premium} per hour.'], ['Scheduler', 'Caregiver']),
]
assert len(documents) == 12

def CS(key_, title, table, start, steps): return _lib.CHK(key_, title, table, start, steps)
checklists = [
 CS('c_build', 'Weekly Schedule Build', 'grid_cg', 'grid_cg.week', [('Check client hours and changes for the week', -7), ('List caregivers and their time off', -7), ('Place regular visits with the usual caregiver', -6), ('List the open shifts', -5), ('Fill open shifts from the ranked candidates', -4), ('Check hours against the overtime line and limits', -3), ('Check days off and rest between visits', -3), ('Post the schedule', -2)]),
 CS('c_post', 'Schedule Posting Steps', 'schedule', 'schedule.date', [('Check the days posted ahead', -14), ('Count the open shifts in the unposted days', -13), ('Fill the urgent shifts first', -10), ('Send the schedule to caregivers', -7), ('Send the visit list to clients', -7), ('Record changes after posting', -2)]),
 CS('c_calloff', 'Morning Call-off Handling', 'calloffs', 'calloffs.date', [('Record the call-off and the reason', 0), ('Check the visit time and the client area', 0), ('Phone the best candidates from the match list', 0), ('Tell the client about the change', 0), ('Record the cover and the minutes it took', 0), ('Check the overtime effect for the cover caregiver', 1)]),
 CS('c_cover', 'Finding Cover for an Open Shift', 'open_shifts', 'open_shifts.date', [('Open the ranked candidates for the shift', -3), ('Phone the top candidate', -3), ('Phone the next candidates', -2), ('Offer the cover premium for short notice', -1), ('Ask the field supervisor if nobody is free', -1), ('Tell the client who comes', -1), ('Record the cover', 0)]),
 CS('c_confirm', 'Confirming a Schedule Change', 'schedule', 'schedule.date', [('Phone or message the client with the change', -2), ('Wait for the confirmation', -1), ('Tell the caregiver', -1), ('Update the schedule', -1), ('Check the day after for the same caregiver', 1)]),
 CS('c_holiday', 'Holiday Week Planning', 'holidays', 'holidays.date', [('Count the visits and hours that week', -28), ('Ask caregivers for availability', -21), ('Agree the volunteers and the premium', -14), ('Fill the open shifts', -7), ('Send the holiday notice to clients', -7), ('Confirm the standby caregivers', -3), ('Check the phone for the day', -1)]),
 CS('c_timeoff', 'Time Off Approval', 'time_off', 'time_off.start_date', [('Check the visits already scheduled', -21), ('Check other time off at the same time', -21), ('Decide and answer the request', -14), ('Move the scheduled visits to other caregivers', -10), ('Tell the clients who are affected', -7), ('Record the approval', -7)]),
 CS('c_match', 'Match Check for a New Client', 'clients', 'clients.start_date', [('Check area, service and language of the client', -10), ('Read the match weights', -10), ('Score the candidates', -9), ('Call the client about the first choice', -7), ('Plan an introduction visit', -3), ('Record the preferred caregivers', 0)]),
 CS('c_contin', 'Weekly Continuity Review', 'grid_cl', 'grid_cl.week', [('List clients above the continuity limit', 0), ('Find the main caregiver of each', 1), ('Move visits back to the main caregiver', 2), ('Tell the field supervisor about problems', 3), ('Check the next week for the same clients', 6)]),
 CS('c_overtime', 'Friday Overtime Check', 'grid_cg', 'grid_cg.week', [('List caregivers above the overtime line next week', -3), ('Move visits to caregivers with free hours', -3), ('Check the cost of overtime against cover', -3), ('Tell the caregivers with long weeks', -2), ('Send the overtime hours to payroll', 0)]),
 CS('c_month', 'Month-end Cover Review', 'cover_month', 'cover_month.month', [('Count call-offs and covered shifts', 28), ('Check the minutes to find cover', 28), ('Compare cover cost with the 3-month average', 29), ('List caregivers with the most call-offs', 29), ('Decide on the standby pool', 30)]),
 CS('c_standby', 'Standby Week Steps', 'fill_week', 'fill_week.week', [('Pick the standby caregivers', -7), ('Send the standby message', -6), ('Give the on-call contact to the answering service', -5), ('Keep the list at the scheduler phone', -1), ('Review the calls handled', 6)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('cg_posted', 'Caregiver: your schedule is posted', 'grid_cg', 'grid_cg.phone', 'Hello {caregiver}, your schedule for the week of {week} is posted: {scheduled_hours} hours. Please check it and reply if anything is wrong. {company}'),
 M('cg_cover_ask', 'Caregiver: can you cover a visit', 'match_scores', 'match_scores.phone', 'Hello {caregiver}, can you cover {service} for {client} on {shift_date} at {shift_start}? Please reply today. {company}'),
 M('cg_thanks', 'Caregiver: thank you for covering', 'calloffs', 'calloffs.cover_phone', 'Hello {cover_caregiver}, thank you for covering on {date}. The cover premium of {premium} applies. {company}'),
 M('cg_moved', 'Caregiver: your visit is moved', 'schedule', 'schedule.caregiver_phone', 'Hello {caregiver}, your visit for {client} on {date} is moved to {start}. Please confirm. {company}'),
 M('cg_ot_near', 'Caregiver: close to the overtime line', 'grid_cg', 'grid_cg.phone', 'Hello {caregiver}, your hours next week are {scheduled_hours}, close to the overtime line. Tell us if you want fewer hours. {company}'),
 M('cg_holiday', 'Caregiver: confirm holiday availability', 'caregivers', 'caregivers.phone', 'Hello {name}, please confirm your availability for {next_holiday} on {next_holiday_date}. {company}'),
 M('cg_off_ok', 'Caregiver: time off approved', 'time_off', 'time_off.caregiver_phone', 'Hello {caregiver}, your time off from {start_date} to {end_date} is approved. {company}'),
 M('cg_off_no', 'Caregiver: time off needs another date', 'time_off', 'time_off.caregiver_phone', 'Hello {caregiver}, your time off request from {start_date} needs another date. Please phone the office. {company}'),
 M('cg_standby', 'Caregiver: you are on standby', 'caregivers', 'caregivers.phone', 'Hello {name}, you are on standby from {week_start}. Please keep your phone on and tell us if you cannot take calls. {company}'),
 M('cg_remind', 'Caregiver: reminder for tomorrow', 'schedule', 'schedule.caregiver_phone', 'Hello {caregiver}, a reminder of your visit on {date} at {start} for {client} ({area}). {company}'),
 M('cg_late', 'Caregiver: phone the office', 'schedule', 'schedule.caregiver_phone', 'Hello {caregiver}, please phone the office about your check-in for {client} on {date}. {company}'),
 M('cg_rest', 'Caregiver: short rest between visits', 'rest_check', 'rest_check.caregiver_phone', 'Hello {caregiver}, your schedule on {date} leaves {rest_hours} hours of rest before the next day. Please phone the office. {company}'),
 M('cl_visits', 'Client: your visits next week', 'grid_cl', 'grid_cl.client_phone', 'Hello {client}, your visits for the week of {week} are {scheduled_hours} hours in total. The list is attached. {company}'),
 M('cl_change', 'Client: your caregiver changes', 'schedule', 'schedule.client_phone', 'Hello {client}, your caregiver on {date} changes to {caregiver}. {company}'),
 M('cl_moved', 'Client: your visit moves', 'schedule', 'schedule.client_phone', 'Hello {client}, your visit on {date} moves to {start}. {company}'),
 M('cl_sorry', 'Client: we could not cover your visit', 'schedule', 'schedule.client_phone', 'Hello {client}, we are sorry, your visit on {date} at {start} could not be covered. We will phone you to agree a new time. {company}'),
 M('cl_holiday', 'Client: your holiday visit is confirmed', 'schedule', 'schedule.client_phone', 'Hello {client}, your holiday visit on {date} ({holiday}) is confirmed at {start} with {caregiver}. {company}'),
 M('cl_thanks', 'Client: thank you for the change', 'clients', 'clients.phone', 'Hello {client}, thank you for telling us about the change in your visits. We have updated the schedule. {company}'),
 M('cl_back', 'Client: your usual caregiver is back', 'continuity', 'continuity.client_phone', 'Hello {client}, your usual caregiver {main_caregiver} is back from {next_monday}. {company}'),
 M('cl_intro', 'Client: we introduce your cover', 'schedule', 'schedule.client_phone', 'Hello {client}, we introduce {caregiver}, who covers your visit on {date}. {company}'),
 M('sc_open', 'Scheduler: open shifts tomorrow', 'open_shifts', 'open_shifts.scheduler_phone', 'Hello, {open_count} open shifts are still not covered tomorrow. Please check the Open Shifts page. {company}'),
 M('sc_calloff', 'Scheduler: a call-off, find cover', 'calloffs', 'calloffs.scheduler_phone', 'Hello, {caregiver} called off for {date} ({client}, {hours} hours). Please find cover. {company}'),
 M('sc_overtime', 'Scheduler: a caregiver reaches overtime', 'grid_cg', 'grid_cg.scheduler_phone', 'Hello, {caregiver} reaches {scheduled_hours} hours in the week of {week}, above the overtime line. {company}'),
 M('sc_contin', 'Scheduler: a client sees too many', 'continuity', 'continuity.scheduler_phone', 'Hello, {client} has seen {caregivers_28d} caregivers in 28 days, above the limit. Please review. {company}'),
 M('sc_post', 'Scheduler: schedule not posted', 'fill_week', 'fill_week.scheduler_phone', 'Hello, the schedule for the week of {week} is not posted yet. Please post it today. {company}'),
 M('fs_cover', 'Field supervisor: please cover a visit', 'schedule', 'schedule.supervisor_phone', 'Hello, please cover the visit for {client} on {date} at {start} ({area}). {company}'),
 M('fs_contin', 'Field supervisor: continuity visit', 'continuity', 'continuity.supervisor_phone', 'Hello, {client} needs a continuity visit with their usual caregiver {main_caregiver}. {company}'),
 M('ow_fill', 'Owner: fill rate below the target', 'fill_week', 'fill_week.owner_phone', 'Hello, the fill rate in the week of {week} is {fill_rate}, below the target. {uncovered_hours} hours were not covered. {company}'),
 M('ow_cost', 'Owner: cover cost above average', 'cover_month', 'cover_month.owner_phone', 'Hello, the cover cost per call-off in {month} is {cost_per_calloff}. Please compare it with the 3-month average. {company}'),
 M('ow_calloffs', 'Owner: many call-offs by one caregiver', 'calloffs', 'calloffs.owner_phone', 'Hello, {caregiver} has called off more than the agency rate. The latest was on {date}. {company}'),
 M('ow_holiday', 'Owner: holiday needs extra caregivers', 'holidays', 'holidays.owner_phone', 'Hello, {holiday} on {date} needs {extra_caregivers} extra caregivers. Please check the Holiday Cover Sheet. {company}'),
 M('om_payroll', 'Office manager: cover and overtime for payroll', 'fill_week', 'fill_week.office_phone', 'Hello, the cover premium ({cover_premium_amount}) and {overtime_hours} overtime hours from the week of {week} are ready for payroll. {company}'),
 M('as_oncall', 'Answering service: tonight on-call contact', 'caregivers', 'caregivers.answering_phone', 'Hello, tonight on-call contact is {name}, phone {phone}. Please pass urgent call-offs to this contact. {company}'),
 M('as_pass', 'Answering service: pass call-offs on', 'team', 'team.phone', 'Hello {name}, please pass call-offs to the scheduler phone, {scheduler_phone}. Thank you. {company}'),
]
assert len(messages) == 34
need = {m['table'] for m in messages}
for t in tables:
    if t['key'] in need and not any(c['key'] == 'company' for c in t['columns']): t['columns'].append(CA('company', 'Agency', 'text', '{set:company}&""', 24))

D90 = '{range:calloffs.date},">="&({today}-90),{range:calloffs.date},"<="&{today}'
D30 = '{range:calloffs.date},">="&({today}-30),{range:calloffs.date},"<="&{today}'
CUR = '({today}-WEEKDAY({today},2)+1)'
W4 = '{range:fill_week.week},">="&(%s-28),{range:fill_week.week},"<"&%s' % (CUR, CUR)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NMS = 'DATE(YEAR({today}),MONTH({today})+1,1)'
FR14 = '{range:schedule.date},">="&{today},{range:schedule.date},"<"&({today}+14),{range:schedule.status},%s' % CANC
kpis = [
 KPI('Visits scheduled next 7 days', 'COUNTIFS({range:schedule.date},">="&{today},{range:schedule.date},"<"&({today}+7),{range:schedule.status},%s)' % CANC, 'int'),
 KPI('Visits scheduled next 14 days', 'COUNTIFS(%s)' % FR14, 'int'),
 KPI('Scheduled hours next week', 'SUMIFS({range:grid_cg.scheduled_hours},{range:grid_cg.week},%s)' % NXT, 'int'),
 KPI('Open shifts next 7 days', 'COUNTIFS({range:open_shifts.date},">="&{today},{range:open_shifts.date},"<"&({today}+7),{range:open_shifts.urgency},%s)' % OPENC, 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Open shifts tomorrow', 'COUNTIFS({range:open_shifts.date},{today}+1,{range:open_shifts.urgency},%s)' % OPENC, 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Open shift hours next 14 days', 'SUMIFS({range:open_shifts.hours},{range:open_shifts.date},">="&{today},{range:open_shifts.date},"<"&({today}+14),{range:open_shifts.urgency},%s)' % OPENC, 'int'),
 KPI('Fill rate last 4 weeks', 'IFERROR((SUMIFS({range:fill_week.planned_hours},%s)+SUMIFS({range:fill_week.cover_hours},%s))/SUMIFS({range:fill_week.scheduled_hours},%s),0)' % (W4, W4, W4), 'pct', alert={"when": "< {set:fill_rate_target}", "style": "warn"}),
 KPI('Fill rate next 14 days', 'IFERROR(SUMIFS({range:schedule.sched_hours},%s,{range:schedule.cover_type},"<>"&%s)/SUMIFS({range:schedule.sched_hours},%s),0)' % (FR14, tok('cover', 'Uncovered'), FR14), 'pct', alert={"when": "< {set:fill_rate_target}", "style": "warn"}),
 KPI('Hours covered by cover, last 4 weeks', 'SUMIFS({range:fill_week.cover_hours},%s)' % W4, 'int'),
 KPI('Hours uncovered, last 4 weeks', 'SUMIFS({range:fill_week.uncovered_hours},%s)' % W4, 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Caregivers over the overtime line next week', 'COUNTIFS({range:grid_cg.week},%s,{range:grid_cg.load_flag},%s)' % (NXT, ck('Over the line')), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Caregivers over their own limit next week', 'COUNTIFS({range:grid_cg.week},%s,{range:grid_cg.free_hours},"<0")' % NXT, 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Caregivers with no day off next week', 'COUNTIFS({range:grid_cg.week},%s,{range:grid_cg.days_flag},%s)' % (NXT, ck('No day off')), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Short rests next 14 days', 'COUNTIFS({range:rest_check.date},">="&{today},{range:rest_check.date},"<"&({today}+14),{range:rest_check.rest_flag},%s)' % ck('Short rest'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Call-offs this month', 'COUNTIFS({range:calloffs.date},">="&%s,{range:calloffs.date},"<"&%s)' % (MS, NMS), 'int'),
 KPI('Call-offs last 30 days', 'COUNTIFS(%s)' % D30, 'int'),
 KPI('Call-off rate last 30 days', 'IFERROR(COUNTIFS(%s)/COUNTIFS({range:schedule.date},">="&({today}-30),{range:schedule.date},"<="&{today},{range:schedule.status},%s),0)' % (D30, CANC), 'pct'),
 KPI('Covered call-offs last 30 days', 'COUNTIFS(%s,{range:calloffs.covered},%s)' % (D30, YES), 'int'),
 KPI('Average minutes to find cover, last 90 days', 'IFERROR(AVERAGEIFS({range:calloffs.minutes_to_cover},%s,{range:calloffs.covered},%s),0)' % (D90, YES), 'int', alert={"when": "> {set:cover_minutes_target}", "style": "warn"}),
 KPI('Cover premium paid this month', 'SUMIFS({range:calloffs.premium},{range:calloffs.date},">="&%s,{range:calloffs.date},"<"&%s)' % (MS, NMS), 'money'),
 KPI('Cover premium paid last 90 days', 'SUMIFS({range:calloffs.premium},%s)' % D90, 'money'),
 KPI('Clients over the continuity limit', 'COUNTIFS({range:continuity.caregivers_28d},">"&{set:continuity_limit})', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Average caregivers per client, last 28 days', 'AVERAGE({range:continuity.caregivers_28d})', 'num'),
 KPI('Main caregiver share, last 28 days', 'SUM({range:continuity.main_hours})/SUM({range:continuity.hours})', 'pct'),
 KPI('Clients with one caregiver only', 'COUNTIFS({range:continuity.caregivers_28d},1)', 'int'),
 KPI('Caregivers on time off next 14 days', 'COUNTIFS({range:time_off.start_date},"<"&({today}+14),{range:time_off.end_date},">="&{today},{range:time_off.approved},%s)' % YES, 'int'),
 KPI('Caregivers with free hours next week', 'COUNTIFS({range:grid_cg.week},%s,{range:grid_cg.free_hours},">0")' % NXT, 'int'),
 KPI('Free hours next week', 'SUMIFS({range:grid_cg.free_hours},{range:grid_cg.week},%s,{range:grid_cg.free_hours},">0")' % NXT, 'int'),
 KPI('Standby caregivers this week', 'COUNTIFS({range:caregivers.standby},%s,{range:caregivers.status},%s)' % (YES, tok('cgstatus', 'Active')), 'int'),
 KPI('Average weekly hours against the scheduler threshold', 'IFERROR(SUMIFS({range:fill_week.scheduled_hours},%s)/4/{set:sched_threshold_hours},0)' % W4, 'pct', alert={"when": ">= 0.9", "style": "warn"}),
]
assert len(kpis) == 30
dashboard = {"title": "Schedule KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Call-offs, covered and uncovered by month", "date": "cover_month.month", "series": [
   {"label": "Call-offs", "sum": "cover_month.call_offs", "date": "cover_month.month"}, {"label": "Covered", "sum": "cover_month.covered", "date": "cover_month.month"},
   {"label": "Uncovered", "sum": "cover_month.uncovered", "date": "cover_month.month"}, {"label": "Overtime hours from cover", "sum": "cover_month.overtime_hours", "date": "cover_month.month"}]},
 "breakdowns": [{"title": "Visits by cover type", "by": "schedule.cover_type", "agg": "count"}, {"title": "Open shifts by status", "by": "open_shifts.status", "agg": "count"},
                {"title": "Call-offs by reason", "by": "calloffs.reason", "agg": "count"}, {"title": "Time off by kind", "by": "time_off.kind", "agg": "count"}]}
insights = {"filters": [{"label": "Area", "list": "area"}, {"label": "Service", "list": "svc"}, {"label": "Employment type", "list": "emp"}],
 "gauges": [
  {"title": "Fill rate against the target", "num": AGG('sum', 'fill_week', 'fill_week.filled_hours'), "den": AGG('sum', 'fill_week', 'fill_week.scheduled_hours')},
  {"title": "Visits with the planned caregiver", "num": AGG('count', 'schedule', where=[('cover_type', '=', tok('cover', 'Planned'))]), "den": AGG('count', 'schedule')},
  {"title": "Call-offs covered", "num": AGG('count', 'calloffs', where=[('covered', '=', YES)]), "den": AGG('count', 'calloffs')},
  {"title": "Caregiver weeks under the overtime line", "num": AGG('count', 'grid_cg', where=[('load_flag', '<>', ck('Over the line'))]), "den": AGG('count', 'grid_cg')},
  {"title": "Clients within the continuity limit", "num": AGG('count', 'continuity', where=[('caregivers_28d', '<=', '{set:continuity_limit}')]), "den": AGG('count', 'continuity')},
  {"title": "Open shifts filled 2 days ahead", "num": AGG('count', 'open_shifts', where=[('filled_ahead', '>=', 2)]), "den": AGG('count', 'open_shifts', where=[('status', '=', tok('ostatus', 'Filled'))])}],
 "charts": [
  CHART('Scheduled hours by month', 'column', 'month', [AGG('sum', 'fill_week', 'fill_week.scheduled_hours', date='fill_week.week', label='Scheduled hours')]),
  CHART('Fill rate by month', 'column', 'month', [AGG('avg', 'fill_week', 'fill_week.fill_rate', date='fill_week.week', label='Fill rate')]),
  CHART('Uncovered hours by month', 'column', 'month', [AGG('sum', 'fill_week', 'fill_week.uncovered_hours', date='fill_week.week', label='Uncovered hours')]),
  CHART('Cover hours by month', 'column', 'month', [AGG('sum', 'fill_week', 'fill_week.cover_hours', date='fill_week.week', label='Cover hours')]),
  CHART('Visits by cover type', 'bar', 'schedule.cover_type', [AGG('count', 'schedule', label='Visits')]),
  CHART('Visits by status', 'bar', 'schedule.status', [AGG('count', 'schedule', label='Visits')]),
  CHART('Open shifts by area', 'bar', 'open_shifts.area', [AGG('count', 'open_shifts', label='Open shifts')]),
  CHART('Open shifts by service', 'bar', 'open_shifts.service', [AGG('count', 'open_shifts', label='Open shifts')]),
  CHART('Call-offs per month', 'column', 'month', [AGG('count', 'calloffs', date='calloffs.date', label='Call-offs')]),
  CHART('Call-offs by reason', 'bar', 'calloffs.reason', [AGG('count', 'calloffs', label='Call-offs')]),
  CHART('Call-offs by weekday', 'bar', 'calloffs.weekday', [AGG('count', 'calloffs', label='Call-offs')]),
  CHART('Call-offs by area', 'bar', 'calloffs.area', [AGG('count', 'calloffs', label='Call-offs')]),
  CHART('Cover premium per month', 'column', 'month', [AGG('sum', 'cover_month', 'cover_month.premium_paid', date='cover_month.month', label='Premium paid')]),
  CHART('Minutes to find cover per month', 'column', 'month', [AGG('avg', 'calloffs', 'calloffs.minutes_to_cover', date='calloffs.date', label='Minutes to cover')]),
  CHART('Cover cost per call-off per month', 'column', 'month', [AGG('avg', 'cover_month', 'cover_month.cost_per_calloff', date='cover_month.month', label='Cost per call-off')]),
  CHART('Scheduled hours by time band', 'bar', 'schedule.band', [AGG('sum', 'schedule', 'schedule.sched_hours', label='Scheduled hours')]),
  CHART('Scheduled hours by area', 'bar', 'schedule.area', [AGG('sum', 'schedule', 'schedule.sched_hours', label='Scheduled hours')]),
  CHART('Scheduled hours by employment type', 'bar', 'grid_cg.employment', [AGG('sum', 'grid_cg', 'grid_cg.scheduled_hours', label='Scheduled hours')]),
  CHART('Time off by kind', 'bar', 'time_off.kind', [AGG('count', 'time_off', label='Time off')]),
  CHART('Time off days per month', 'column', 'month', [AGG('sum', 'time_off', 'time_off.days', date='time_off.start_date', label='Time off days')]),
  CHART('Caregivers by availability', 'bar', 'caregivers.availability', [AGG('count', 'caregivers', label='Caregivers')]),
  CHART('Clients by language', 'bar', 'clients.language', [AGG('count', 'clients', label='Clients')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Weekly schedule grid with overtime, days-off and rest warnings", "why": "every caregiver week shows hours against the overtime line and the own limit, the longest run of days and short rests before payroll", "where": "Weekly Grid by Caregiver"},
 {"name": "Open shift board with ranked candidates and the cost of each option", "why": "each visit without a caregiver shows urgency and the candidates ranked by match score with regular, overtime and premium cost", "where": "Open Shifts"},
 {"name": "Matching score with your own weights", "why": "skills, area, language, availability, client preference and hours booked count as much as you decide", "where": "Match Weights"},
 {"name": "Continuity index per client", "why": "different caregivers in 28 days, the main caregiver share and a Steady, Watch or Break flag for every client", "where": "Continuity by Client"},
 {"name": "Call-off and cover log with cost", "why": "reason, notice, minutes to find cover and the premium paid for every call-off, with cost per call-off by month", "where": "Call-offs and Cover"},
 {"name": "Fill rate forecast", "why": "planned, cover and uncovered hours for the next 14 days give the fill rate, the hours still to find and the caregivers needed", "where": "Fill Rate Forecast"},
 {"name": "Standby pool sizing", "why": "call-offs a week, notice and hours give the standby caregivers needed and the weekly cost against your pool", "where": "Standby Pool Sizing"},
 {"name": "Holiday cover planner", "why": "visits that day, caregivers who can work and volunteers show the shortage and the extra pay before the holiday", "where": "Holiday Cover Planner"},
 {"name": "Hours balance across caregivers", "why": "fair share, spread and a verdict show who carries too much and who has room", "where": "Hours Balance"},
 {"name": "Schedule posting deadline", "why": "days posted ahead and open shifts give the shifts to fill each day to meet your posting target", "where": "Posting Deadline"},
 {"name": "Open shift filler with the three best caregivers", "why": "date, hour, area, service and language rank the caregivers by score, free hours and travel minutes", "where": "Open Shift Filler"},
 {"name": "Start here tab with sample and blank copy", "why": "a replace-demo-data step list, no macros, works in Excel and Google Sheets", "where": "Start"}]
competitors = [
 {"what": "free schedule template", "lacks": "lists visits but has no overtime line, rest check, ranked candidates or cover cost"},
 {"what": "subscription home care scheduling software with a per-client fee", "lacks": "charges more as hours grow and gives no editable match weights, cover cost history or fill rate forecast"},
 {"what": "single-sheet time log", "lacks": "records hours only, so open shifts, call-offs, continuity and standby needs are never counted"},
 {"what": "generic shift planner spreadsheet", "lacks": "has no home care matching by skills, area and language and no continuity index per client"},
 {"what": "paper roster and phone list", "lacks": "cannot rank who to phone first, track minutes to find cover or warn before overtime"}]
guide = [
 'Open Start and type your agency name and your targets in the yellow cells: the overtime line (40 hours is the default), the wanted fill rate, the cover premium, the continuity limit and the days to post the schedule ahead. A one-person agency can use the Schedule, Open Shifts and Fill Rate pages without the matching tables.',
 'Replace the demo data. Fill Caregivers (a caregiver is also called a carer, care worker or support worker), Clients, Availability and Time Off, then the Schedule (also called a rota or roster) with one row per visit.',
 'Check Weekly Grid by Caregiver every Friday: hours above the overtime line (overtime means hours above the weekly line), the own weekly limit, days in a row and short rests turn red or amber.',
 'Open Shifts lists visits without a caregiver. Match Scores ranks the candidates for each shift with the weights you set in Match Weights, and shows the cost of regular hours, overtime and the cover premium.',
 'Log every call-off (a caregiver cannot come) on Call-offs and Cover with the reason, notice and the minutes to find cover. Cover means another caregiver takes the visit. Cover Cost by Month shows the cost per call-off.',
 'Use Continuity by Client and Weekly Grid by Client to see how few different caregivers each client sees. Fill Rate by Week shows planned, cover and uncovered hours against your target.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Holidays holds the pay and bill multipliers (a holiday is a bank holiday or public holiday). Plan extra caregivers with the Holiday Cover Planner and the Holiday Cover Sheet.',
 'Why a workbook: one flat price with no per-client or per-caregiver fee, no price rise when hours grow, your data stays with you, and the reports are built for agency owners. The workbook takes times typed or pasted from whatever you use; it has no live app and no GPS.',
 'Read the Schedule KPI Dashboard and Charts every week: fill rate, open shifts, overtime, call-offs, cover cost and continuity. Check your own local rules and confirm pay questions with your adviser.']
listing = {"title": "Home Care Agency Schedule Excel Template: Open Shifts, Caregiver Matching, Call-offs and Cover, Overtime Check, Fill Rate",
 "headline": "Fill open shifts faster and keep overtime and call-offs under control",
 "tags": ["home care agency", "caregiver schedule", "care scheduling", "open shifts", "call off tracker", "caregiver matching", "overtime tracker", "fill rate", "excel template", "agency management", "shift planner", "home care", "continuity of care"],
 "description": ("Run the weekly schedule of a small home care agency in one Excel workbook. Built for an owner-director with a scheduler and care coordinator, field supervisors and about 40 caregivers: non-medical care, hours, dates and rates only.\n\n"
  "Weekly Grid by Caregiver shows every caregiver's hours against the overtime line and the own weekly limit, the days in a row and rest between visits. Open Shifts lists visits without a caregiver with their urgency, and Match Scores ranks the candidates for each shift with weights you set (skills, area, language, availability, client preference and hours booked) and the cost of regular hours, overtime and the short-notice cover premium. "
  "Continuity by Client counts the different caregivers each client sees. Call-offs and Cover records the reason, notice, minutes to find cover and the premium paid, and Cover Cost by Month and Fill Rate by Week show cost per call-off and the share of hours covered against your target.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: weekly schedule checker, open shift filler with the three best caregivers, cover option cost, matching score, continuity index, call-off response plan, call-off rate check, cover cost against history, fill rate forecast, rest and days-off checks, posting deadline, hours balance, standby pool sizing, free hours finder, holiday cover planner and call-off sensitivity. "
  f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
  "This is part two of the Home Care Agency suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-client or per-caregiver fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. It takes times typed or pasted from whatever you use; it has no live app and no GPS, and it does not promise any outcome."),
 "features": ["Weekly grid with overtime, days-off and rest warnings", "Open shift board with ranked candidates", "Matching score with your own weights", "Continuity index per client", "Call-off and cover log with cost per call-off",
              "Fill rate by week and a 14-day forecast", "Standby pool and holiday cover planners", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
              f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
s = _lib.spec(id=f'{SUITE}-p2', slug='home-care-schedule', profession='Home Care Agency Business', name='Schedule, Matching and Cover',
         tagline='Fill open shifts faster and keep overtime and call-offs down', price_usd=29, colors={"primary": "#3A506B", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 2, "of": 8, "focus": "Schedule, matching and cover"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
import hc2_fix
if __name__ == '__main__':
    s = hc2_fix.apply(s)
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hc2.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
