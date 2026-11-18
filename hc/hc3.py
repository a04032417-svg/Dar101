"""Home care agency suite - part 3: Visits, Hours and Travel."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from hc3_lists import *
from hc3_tables import settings, tables, CA
from hc3_tools import tools

SUITE = 'fx-20261115-home-care-agency'
NOTE = "Sample wording: adapt it to your own agency and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
def cnt(tb, col, pick): return 'COUNTIFS({range:%s.%s},INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0)))' % (tb, col, tb, col, tb, tb and pick_col[tb])
pick_col = {'visits': 'visit_id', 'register': 'visit_id', 'today': 'visit_id', 'caregivers': 'caregiver_id', 'areamonths': 'row_id'}
def LK(src, kc): return 'IFERROR(INDEX({range:%s},MATCH({pick},{range:%s},0)),"")' % (src, kc)
def LKT(src, kc): return 'IFERROR(INDEX({range:%s},MATCH({pick},{range:%s},0))&"","")' % (src, kc)

forms = [
 FORM('checkin_sheet', 'Check-in Entry Sheet', 'Check-in entry for one visit', 'visits.visit_id', F(
  ('Date', 'visits.date'), ('Scheduled start', 'visits.start'), ('Client', 'visits.client'), ('Client phone', 'visits.client_phone'), ('Area', 'visits.area'), ('Service', 'visits.service'), ('Caregiver', 'visits.caregiver'),
  ('Check-in', 'visits.check_in'), ('Check-out', 'visits.check_out'), ('Minutes late', 'visits.late_minutes'), ('Hours worked', 'visits.worked_hours'), ('Hours difference', 'visits.hours_diff'), ('Billable hours', 'visits.billable_hours'),
  ('Visit flag', 'visits.flag')) + [FF('Visits of this caregiver in the log', 'COUNTIFS({range:visits.caregiver},INDEX({range:visits.caregiver},MATCH({pick},{range:visits.visit_id},0)))', 'int')]),
 FORM('late_sheet', 'Late Visit Sheet', 'Late visit follow-up', 'visits.visit_id', F(
  ('Date', 'visits.date'), ('Client', 'visits.client'), ('Caregiver', 'visits.caregiver'), ('Caregiver phone', 'visits.caregiver_phone'), ('Area', 'visits.area'), ('Scheduled start', 'visits.start'), ('Check-in', 'visits.check_in'),
  ('Minutes late', 'visits.late_minutes'), ('Reason', 'visits.reason'), ('Visit flag', 'visits.flag')) + [
  FF('Late visits of this caregiver', 'COUNTIFS({range:register.caregiver},INDEX({range:visits.caregiver},MATCH({pick},{range:visits.visit_id},0)),{range:register.status},%s)' % tok('vstatus', 'Late'), 'int'),
  FF('Late limit in minutes', '{set:late_minutes}', 'int')]),
 FORM('missed_sheet', 'Missed Visit Sheet', 'Missed visit with phoning and cover', 'register.visit_id', F(
  ('Date', 'register.date'), ('Client', 'register.client'), ('Client phone', 'register.client_phone'), ('Caregiver', 'register.caregiver'), ('Caregiver phone', 'register.caregiver_phone'), ('Area', 'register.area'),
  ('Status', 'register.status'), ('Reason', 'register.reason'), ('Caregiver phoned on', 'register.phoned_on'), ('Client told', 'register.client_told'), ('Repeat check', 'register.repeat')) + [
  FF('Missed visits in this area', 'COUNTIFS({range:register.area},INDEX({range:register.area},MATCH({pick},{range:register.visit_id},0)),{range:register.status},%s)' % tok('vstatus', 'Missed'), 'int')]),
 FORM('correction_sheet', 'Visit Correction Sheet', 'Visit correction record', 'corrections.correction_id', F(
  ('Corrected on', 'corrections.date'), ('Visit ID', 'corrections.visit_id'), ('Visit date', 'corrections.visit_date'), ('Client', 'corrections.client'), ('Caregiver', 'corrections.caregiver'), ('Field corrected', 'corrections.field'),
  ('Old value', 'corrections.old_value'), ('New value', 'corrections.new_value'), ('Reason', 'corrections.reason'), ('Corrected by', 'corrections.corrected_by'), ('Days after the visit', 'corrections.days_after'), ('Timing check', 'corrections.timing'))),
 FORM('timesheet_sheet', 'Time Sheet Entry Sheet', 'Time sheet against check-ins', 'timesheets.sheet_id', F(
  ('Week (Monday)', 'timesheets.week'), ('Caregiver', 'timesheets.caregiver'), ('Caregiver phone', 'timesheets.caregiver_phone'), ('Hours entered', 'timesheets.hours_entered'), ('Hours from check-ins', 'timesheets.hours_checkins'),
  ('Confirmed on', 'timesheets.confirmed_on'), ('Difference (hours)', 'timesheets.difference'), ('Time sheet check', 'timesheets.flag')) + [
  FF('Mismatches for this caregiver', 'COUNTIFS({range:timesheets.caregiver},INDEX({range:timesheets.caregiver},MATCH({pick},{range:timesheets.sheet_id},0)),{range:timesheets.flag},%s)' % ck('Mismatch'), 'int')]),
 FORM('mileage_sheet', 'Mileage Entry Sheet', 'Mileage leg entry', 'mileage.mileage_id', F(
  ('Date', 'mileage.date'), ('Caregiver', 'mileage.caregiver'), ('Client', 'mileage.client'), ('From area', 'mileage.from_area'), ('To area', 'mileage.to_area'), ('Distance (km)', 'mileage.distance_km'), ('Travel minutes', 'mileage.travel_min'),
  ('Travel pay', 'mileage.travel_pay'), ('Mileage pay', 'mileage.mileage_pay'), ('Cost per leg', 'mileage.cost_leg')) + [
  FF('Expected distance between the areas (km)', 'SUMIFS({range:travel.km},{range:travel.from_area},INDEX({range:mileage.from_area},MATCH({pick},{range:mileage.mileage_id},0)),{range:travel.to_area},INDEX({range:mileage.to_area},MATCH({pick},{range:mileage.mileage_id},0)))', 'num')]),
 FORM('pair_sheet', 'Travel Pair Sheet', 'Travel between two areas', 'pairs.pair_id', F(
  ('From area', 'pairs.from_area'), ('To area', 'pairs.to_area'), ('Legs in 12 months', 'pairs.legs'), ('Paid minutes', 'pairs.minutes'), ('Kilometres', 'pairs.km'), ('Cost', 'pairs.cost'), ('Cost per leg', 'pairs.cost_per_leg'),
  ('Minutes per leg', 'pairs.min_per_leg'), ('Kilometres per leg', 'pairs.km_per_leg'))),
 FORM('cancel_sheet', 'Client Cancellation Sheet', 'Client cancellation with notice and charge', 'cancels.cancel_id', F(
  ('Visit date', 'cancels.date'), ('Visit ID', 'cancels.visit_id'), ('Client', 'cancels.client'), ('Client phone', 'cancels.client_phone'), ('Notice (hours)', 'cancels.notice_hours'), ('Notice band', 'cancels.notice_band'),
  ('Visit value', 'cancels.visit_value'), ('Charged', 'cancels.charged'), ('Notice check', 'cancels.short_notice'), ('Amount charged', 'cancels.charged_amount')) + [
  FF('Cancellations by this client', 'COUNTIFS({range:cancels.client},INDEX({range:cancels.client},MATCH({pick},{range:cancels.cancel_id},0)))', 'int')]),
 FORM('overlong_sheet', 'Overlong Visit Sheet', 'Overlong visit with unbilled money', 'overlong.visit_id', F(
  ('Date', 'overlong.date'), ('Client', 'overlong.client'), ('Client phone', 'overlong.client_phone'), ('Caregiver', 'overlong.caregiver'), ('Scheduled hours', 'overlong.sched_hours'), ('Actual hours', 'overlong.actual_hours'),
  ('Invoiced hours', 'overlong.billed_hours'), ('Reason', 'overlong.reason'), ('Client agreed', 'overlong.client_agreed'), ('Extra minutes', 'overlong.extra_minutes'), ('Unbilled hours', 'overlong.unbilled_hours'),
  ('Unbilled money', 'overlong.unbilled_money'), ('Billing check', 'overlong.billing_check'))),
 FORM('call_sheet', 'Client Call Log Sheet', 'Client call about a late or missing check-in', 'today.visit_id', F(
  ('Date', 'today.date'), ('Scheduled start', 'today.start'), ('Client', 'today.client'), ('Client phone', 'today.client_phone'), ('Caregiver', 'today.caregiver'), ('Caregiver phone', 'today.caregiver_phone'),
  ('Expected arrival', 'today.arrives_by'), ('Minutes overdue', 'today.minutes_overdue'), ('Call-first rank', 'today.call_rank'), ('Next step', 'today.next_step'), ('Scheduler phone', 'today.scheduler_phone'))),
 FORM('talk_sheet', 'Caregiver Lateness Talk Sheet', 'Caregiver lateness conversation', 'caregivers.caregiver_id', F(
  ('Caregiver', 'caregivers.name'), ('Phone', 'caregivers.phone'), ('Area', 'caregivers.area'), ('Employment type', 'caregivers.employment'), ('Hire date', 'caregivers.hire_date'), ('Visits, last 30 days', 'caregivers.visits_30d'),
  ('Late visits, last 30 days', 'caregivers.late_30d'), ('Missed visits, last 30 days', 'caregivers.missed_30d'), ('Lateness check', 'caregivers.late_flag'), ('Field supervisor phone', 'caregivers.supervisor_phone')) + [
  FF('Late limit in minutes', '{set:late_minutes}', 'int')]),
 FORM('area_sheet', 'Area Review Sheet', 'Area review with late and missed rates', 'areamonths.row_id', F(
  ('Month', 'areamonths.month'), ('Area', 'areamonths.area'), ('Visits', 'areamonths.visits'), ('Late visits', 'areamonths.late_visits'), ('Missed visits', 'areamonths.missed_visits'), ('Late rate', 'areamonths.late_rate'),
  ('Missed rate', 'areamonths.missed_rate'), ('Late rate of the area, last 2 months', 'areamonths.late_rate_2m'), ('Paid travel hours', 'areamonths.travel_hours'), ('Travel cost', 'areamonths.travel_cost'),
  ('Travel share of pay', 'areamonths.travel_share')) + [FF('Late target', '{set:late_visit_target}', 'pct')]),
]
assert len(forms) == 12

def D_(k, sheet, title, pick, paras, sign): return DOC(k, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('daily_doc', 'Daily Check-in Report', 'Daily check-in report with the visit that needs a call', 'today.visit_id', [
  'Daily check-in report of {set:company}, dated {today}. Visit {col:today.visit_id} on {col:today.date}.', 'Client: {col:today.client}, area {col:today.area}, scheduled start {col:today.start}, caregiver {col:today.caregiver}. Check-in: {col:today.check_in}.',
  'Minutes overdue: {col:today.minutes_overdue}. Next step: {col:today.next_step}. Visits overdue now: {col:today.overdue_count}.', 'The scheduler records the calls made and the expected arrival time below.'], ['Scheduler']),
 D_('weekly_doc', 'Weekly Visit Report', 'Weekly visit report', 'agencyweeks.row_id', [
  'Weekly visit report of {set:company}, dated {today}. Week of {col:agencyweeks.week}.', 'Visits: {col:agencyweeks.visits}. Late visits: {col:agencyweeks.late_visits} (late rate {col:agencyweeks.late_rate}). Missed visits: {col:agencyweeks.missed_visits} (missed rate {col:agencyweeks.missed_rate}).',
  'Targets: late {set:late_visit_target}, missed {set:missed_visit_target}. Average minutes late: {col:agencyweeks.avg_late_min}.', 'Scheduled hours {col:agencyweeks.scheduled_hours}, delivered hours {col:agencyweeks.delivered_hours}. Actions for the week are written below.'], ['Owner-director', 'Scheduler']),
 D_('register_doc', 'Register Entry Report', 'Late and missed register entry report', 'register.visit_id', [
  'Late and missed register entry of {set:company}, dated {today}. Visit {col:register.visit_id} on {col:register.date}, week of {col:register.week}.', 'Client {col:register.client}, caregiver {col:register.caregiver}, area {col:register.area}. Status: {col:register.status}. Minutes late: {col:register.minutes_late}.',
  'Reason: {col:register.reason}. Caregiver phoned on {col:register.phoned_on}. Client told: {col:register.client_told}. Repeat check: {col:register.repeat}.'], ['Scheduler', 'Field supervisor']),
 D_('timesheet_doc', 'Time Sheet Print', 'Time sheet for one caregiver and week', 'timesheets.sheet_id', [
  'Time sheet of {set:company}, dated {today}. Caregiver: {col:timesheets.caregiver}. Week of {col:timesheets.week}.', 'Hours entered by the caregiver: {col:timesheets.hours_entered}. Hours from the check-ins: {col:timesheets.hours_checkins}. Difference: {col:timesheets.difference} hours. Check: {col:timesheets.flag}.',
  'Confirmed on {col:timesheets.confirmed_on}. Differences above {set:ts_tolerance} hours are queried before payroll. Pay rules: check your own local rules and confirm with your adviser.'], ['Caregiver', 'Office manager']),
 D_('mileage_doc', 'Mileage Claim Form', 'Mileage claim form for one leg', 'mileage.mileage_id', [
  'Mileage claim of {set:company}, dated {today}. Leg {col:mileage.mileage_id} on {col:mileage.date}.', 'Caregiver: {col:mileage.caregiver}. Client: {col:mileage.client}. From {col:mileage.from_area} to {col:mileage.to_area}.',
  'Distance {col:mileage.distance_km} km, paid travel {col:mileage.travel_min} minutes. Travel pay {col:mileage.travel_pay}, mileage pay {col:mileage.mileage_pay}, cost of the leg {col:mileage.cost_leg}. Rate per km: {set:mileage_rate}.'], ['Caregiver', 'Office manager']),
 D_('correction_doc', 'Visit Correction Note', 'Visit correction note', 'corrections.correction_id', [
  'Visit correction note of {set:company}, dated {today}. Correction {col:corrections.correction_id}.', 'Visit {col:corrections.visit_id} of {col:corrections.visit_date} for {col:corrections.client}, caregiver {col:corrections.caregiver}.',
  'Field corrected: {col:corrections.field}. Old value: {col:corrections.old_value}. New value: {col:corrections.new_value}. Reason: {col:corrections.reason}.', 'Corrected by {col:corrections.corrected_by} on {col:corrections.date}, {col:corrections.days_after} days after the visit.'], ['Office', 'Caregiver']),
 D_('lateness_doc', 'Caregiver Lateness Letter', 'Caregiver lateness letter', 'caregivers.caregiver_id', [
  'Letter of {set:company}, dated {today}. Dear {col:caregivers.name},', 'In the last 30 days you had {col:caregivers.visits_30d} visits, {col:caregivers.late_30d} late check-ins and {col:caregivers.missed_30d} missed visits. A check-in more than {set:late_minutes} minutes after the start is late.',
  'Please call the office before a visit if you expect to be late. Your field supervisor will talk with you about how we can help. Lateness check: {col:caregivers.late_flag}.'], ['Field supervisor', 'Caregiver']),
 D_('apology_doc', 'Missed Visit Apology Letter', 'Client apology letter for a missed visit', 'register.visit_id', [
  'Letter of {set:company}, dated {today}. Dear {col:register.client},', 'We are sorry that your visit on {col:register.date} did not take place. The reason was: {col:register.reason}.',
  'We are arranging another visit and will phone you to agree the time. Thank you for your patience. Reference {col:register.visit_id}.'], ['Care coordinator']),
 D_('area_doc', 'Area Performance Report', 'Area performance report', 'areamonths.row_id', [
  'Area performance report of {set:company}, dated {today}. Area: {col:areamonths.area}. Month: {col:areamonths.month}.', 'Visits {col:areamonths.visits}, late {col:areamonths.late_visits} (rate {col:areamonths.late_rate}), missed {col:areamonths.missed_visits} (rate {col:areamonths.missed_rate}).',
  'Late rate of the area over the last 2 months: {col:areamonths.late_rate_2m}. Target: {set:late_visit_target}. Paid travel hours {col:areamonths.travel_hours}, travel cost {col:areamonths.travel_cost}, travel share of pay {col:areamonths.travel_share}.', 'Decisions for the area are written below.'], ['Owner-director', 'Field supervisor']),
 D_('leak_doc', 'Billed vs Paid Report', 'Billed against paid hours report: the leak', 'agencyweeks.row_id', [
  'Billed against paid hours report of {set:company}, dated {today}. Week of {col:agencyweeks.week}.', 'Delivered hours {col:agencyweeks.delivered_hours}, billed hours {col:agencyweeks.billed_hours}, paid hours {col:agencyweeks.paid_hours}. Billed minus paid hours: {col:agencyweeks.billed_minus_paid}.',
  'Hours paid above billed: {col:agencyweeks.paid_over_billed}. Average pay rate {col:agencyweeks.avg_pay_rate}. Leak amount at loaded pay: {col:agencyweeks.leak_amount}. Payroll burden: {set:payroll_burden} (confirm with your adviser).'], ['Office manager', 'Owner-director']),
 D_('pair_doc', 'Travel Pair Plan', 'Travel pair plan for two areas', 'pairs.pair_id', [
  'Travel pair plan of {set:company}, dated {today}. From {col:pairs.from_area} to {col:pairs.to_area}.', 'Over 12 months: {col:pairs.legs} legs, {col:pairs.minutes} paid minutes, {col:pairs.km} km, cost {col:pairs.cost}. Cost per leg {col:pairs.cost_per_leg}, {col:pairs.min_per_leg} minutes per leg.',
  'Plan: give both visits of the pair to one caregiver when the gap allows. Use the Visit Pair Sharing tool to check the saving.'], ['Scheduler']),
 D_('hours_doc', 'Caregiver Hours Statement', 'Monthly hours statement for a caregiver', 'caregivers.caregiver_id', [
  'Hours statement of {set:company}, dated {today}. Caregiver: {col:caregivers.name}, {col:caregivers.employment}.', 'Hours worked in the last 4 weeks: {col:caregivers.worked_4w}. Paid travel hours: {col:caregivers.travel_4w}. Visits in the last 30 days: {col:caregivers.visits_30d}.',
  'Pay rate per hour: {col:caregivers.pay_rate}. Pay, overtime and payroll taxes: check your own local rules and confirm with your adviser.'], ['Office manager']),
]
assert len(documents) == 12

def CS(k, title, table, start, steps): return _lib.CHK(k, title, table, start, steps)
checklists = [
 CS('c_morning', 'Morning Check-in Watch', 'today', 'today.date', [('Set the time now in the Start sheet', 0), ('Read the visits overdue and their call-first rank', 0), ('Phone the caregiver of the first overdue visit', 0), ('Phone the client if the visit is over the limit', 0), ('Write the expected arrival time', 0), ('Find cover if nobody can come', 0), ('Log the reason in the register', 1)]),
 CS('c_missed', 'Missed Visit Handling', 'register', 'register.date', [('Phone the caregiver', 0), ('Phone the client', 0), ('Find cover for the visit', 0), ('Log the reason', 0), ('Send the apology message', 1), ('Ask the field supervisor to follow up', 2)]),
 CS('c_late', 'Late Visit Follow-up', 'visits', 'visits.date', [('Check the check-in against the scheduled start', 0), ('Record the minutes late and the reason', 0), ('Tell the client if more than the limit', 0), ('Thank the caregiver who called ahead', 1), ('Count repeat cases for the month', 7)]),
 CS('c_sheets', 'Weekly Time Sheet Collection', 'timesheets', 'timesheets.week', [('Ask every caregiver for the time sheet', 7), ('Chase the missing time sheets', 8), ('Compare each with the check-ins', 8), ('Query differences above the tolerance', 9), ('Confirm the sheets', 9)]),
 CS('c_friday', 'Friday Hours Check', 'cgweeks', 'cgweeks.week', [('Compare scheduled and worked hours', 4), ('Check travel hours for the week', 4), ('Check hours near the overtime line', 4), ('Send corrected hours to the payroll service', 5)]),
 CS('c_mileage', 'Mileage Log Check', 'mileage', 'mileage.date', [('Compare the distance with Travel Times', 1), ('Query a claim above the tolerance', 2), ('Check the paid travel minutes', 2), ('Send the mileage list to payroll', 7)]),
 CS('c_correction', 'Visit Correction Steps', 'corrections', 'corrections.date', [('Write the old and new value', 0), ('Record the reason and who corrected it', 0), ('Tell the caregiver', 0), ('Tell the client if the billed time changes', 1), ('Check the next invoice', 7)]),
 CS('c_complaint', 'Schedule Complaint Follow-up', 'register', 'register.date', [('Call the client the same day', 0), ('Record what happened', 0), ('Agree a better time or caregiver', 1), ('Tell the scheduler', 1), ('Call again after a week', 7)]),
 CS('c_area', 'Area Review Steps', 'areamonths', 'areamonths.month', [('Read the late and missed rates of the area', 1), ('Check the delay reasons', 2), ('Check travel between visits', 3), ('Agree changes to the schedule', 7), ('Review again next month', 30)]),
 CS('c_month', 'Month-end Hours Reconciliation', 'agencyweeks', 'agencyweeks.month', [('Add delivered, billed and paid hours', 30), ('Explain the gap between billed and paid hours', 31), ('Check the leak amount', 31), ('Check overlong visits not billed', 32), ('Report to the owner-director', 33)]),
 CS('c_talk', 'Lateness Conversation Steps', 'register', 'register.date', [('Check the register for repeat cases', 0), ('Hold a private talk with the caregiver', 3), ('Agree what will change', 3), ('Write the agreement', 4), ('Check the check-ins after two weeks', 17)]),
 CS('c_new', 'New Caregiver Check-in Set-up', 'caregivers', 'caregivers.hire_date', [('Explain how to type or send check-in and check-out times', 0), ('Test one check-in with the scheduler', 1), ('Explain the late limit', 1), ('Explain time sheets and mileage', 2), ('Review the first week of check-ins', 7)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('cg_noin', 'Caregiver: check-in has not arrived', 'today', 'today.caregiver_phone', 'Hello {caregiver}, your check-in for {client} at {start} has not arrived. Please call the office. {company}'),
 M('cg_late', 'Caregiver: you checked in late', 'visits', 'visits.caregiver_phone', 'Hello {caregiver}, you checked in {late_minutes} minutes late for {client} on {date}. Please tell us the reason. {company}'),
 M('cg_sheet', 'Caregiver: send your time sheet', 'timesheets', 'timesheets.caregiver_phone', 'Hello {caregiver}, please send your time sheet for the week of {week}. {company}'),
 M('cg_diff', 'Caregiver: time sheet differs', 'timesheets', 'timesheets.caregiver_phone', 'Hello {caregiver}, your time sheet differs from your check-ins by {difference} hours for the week of {week}. Please check it. {company}'),
 M('cg_mile', 'Caregiver: mileage needs a correction', 'mileage', 'mileage.caregiver_phone', 'Hello {caregiver}, your mileage entry for {date} ({from_area} to {to_area}, {distance_km} km) needs a correction. {company}'),
 M('cg_out', 'Caregiver: please check out', 'visits', 'visits.caregiver_phone', 'Hello {caregiver}, please check out when you leave a visit. Your visit with {client} on {date} has no check-out. {company}'),
 M('cg_thanks', 'Caregiver: on time all month', 'caregivers', 'caregivers.phone', 'Hello {name}, thank you: all your check-ins were on time this month. {company}'),
 M('cg_over', 'Caregiver: visit ran over', 'overlong', 'overlong.caregiver_phone', 'Hello {caregiver}, your visit with {client} on {date} ran {extra_minutes} minutes over. Please tell us why. {company}'),
 M('cg_km', 'Caregiver: travel logged', 'mileage', 'mileage.caregiver_phone', 'Hello {caregiver}, your travel between {from_area} and {to_area} on {date} is logged as {distance_km} km. {company}'),
 M('cg_fix', 'Caregiver: confirm corrected time', 'corrections', 'corrections.caregiver_phone', 'Hello {caregiver}, please confirm the corrected time for {visit_date}: {new_value} ({field}). {company}'),
 M('cl_late', 'Client: caregiver running late', 'today', 'today.client_phone', 'Hello {client}, your caregiver {caregiver} is running late for your {start} visit and expects to arrive by {arrives_by}. We are sorry. {company}'),
 M('cl_missed', 'Client: visit was missed', 'register', 'register.client_phone', 'Hello {client}, we are sorry: your visit on {date} was missed. We are arranging another visit and will call you. {company}'),
 M('cl_thanks', 'Client: thank you for telling us', 'register', 'register.client_phone', 'Hello {client}, thank you for letting us know about the late arrival on {date}. We are sorry. {company}'),
 M('cl_time', 'Client: recorded visit time', 'visits', 'visits.client_phone', 'Hello {client}, your visit on {date} was recorded as {check_in} to {check_out}. Please tell us if this is not right. {company}'),
 M('cl_nochg', 'Client: cancellation, no charge', 'cancels', 'cancels.client_phone', 'Hello {client}, your cancellation of the visit on {date} is noted. No charge applies. {company}'),
 M('cl_chg', 'Client: short-notice charge', 'cancels', 'cancels.client_phone', 'Hello {client}, the visit on {date} was cancelled with {notice_hours} hours\' notice. A charge of {charged_amount} applies under your agreement. {company}'),
 M('cl_long', 'Client: caregiver stayed longer', 'overlong', 'overlong.client_phone', 'Hello {client}, your caregiver stayed {extra_minutes} minutes longer on {date}. Please confirm the billed time. {company}'),
 M('cl_fixed', 'Client: visit time corrected', 'corrections', 'corrections.client_phone', 'Hello {client}, we have corrected your visit time on {visit_date}: {new_value}. {company}'),
 M('sc_noin', 'Scheduler: no check-in', 'today', 'today.scheduler_phone', 'Hello, {client} has no check-in: the visit started at {start} with {caregiver}. {company}'),
 M('sc_count', 'Scheduler: visits overdue today', 'today', 'today.scheduler_phone', 'Hello, {overdue_count} visits have no check-in yet today. Please see Today Check-ins. {company}'),
 M('sc_area', 'Scheduler: late visits in an area', 'areamonths', 'areamonths.scheduler_phone', 'Hello, {area} had {late_visits} late visits in the month of {month}. {company}'),
 M('sc_cover', 'Scheduler: find cover', 'register', 'register.scheduler_phone', 'Hello, please find cover for the missed visit of {client} on {date} ({area}). {company}'),
 M('fs_talk', 'Field supervisor: repeated lateness', 'caregivers', 'caregivers.supervisor_phone', 'Hello, please speak with {name} about repeated late check-ins: {late_30d} late visits in 30 days. {company}'),
 M('fs_visit', 'Field supervisor: visit the client', 'register', 'register.supervisor_phone', 'Hello, please visit {client} after the missed visit on {date}. {company}'),
 M('om_sheets', 'Office manager: time sheets missing', 'timesheets', 'timesheets.office_phone', 'Hello, {sheets_missing} time sheets are still missing before payroll. {company}'),
 M('om_gap', 'Office manager: paid above billed', 'agencyweeks', 'agencyweeks.office_phone', 'Hello, in the week of {week} hours paid were {paid_over_billed} above hours billed. {company}'),
 M('om_mile', 'Office manager: mileage ready', 'mileage', 'mileage.office_phone', 'Hello, the mileage entries up to {date} are ready to check ({caregiver}, {distance_km} km). {company}'),
 M('ow_late', 'Owner: late rate above target', 'agencyweeks', 'agencyweeks.owner_phone', 'Hello, the late rate in the week of {week} was {late_rate}, above the target. {company}'),
 M('ow_leak', 'Owner: the leak', 'agencyweeks', 'agencyweeks.owner_phone', 'Hello, the leak between billed and paid hours in the week of {week} is {leak_amount}. {company}'),
 M('ow_area', 'Owner: area with the highest rate', 'areamonths', 'areamonths.owner_phone', 'Hello, {area} had a late rate of {late_rate} and a missed rate of {missed_rate} in {month}. {company}'),
 M('ow_report', 'Owner: weekly report ready', 'agencyweeks', 'agencyweeks.owner_phone', 'Hello, the visit report for the week of {week} is ready: {visits} visits, {late_visits} late, {missed_visits} missed. {company}'),
 M('pr_hours', 'Payroll service: corrected hours', 'timesheets', 'timesheets.payroll_phone', 'Hello, corrected hours for {caregiver} for the week of {week} follow ({hours_checkins} hours from the check-ins). {company}'),
 M('pr_mile', 'Payroll service: mileage list', 'mileage', 'mileage.payroll_phone', 'Hello, the mileage list for the period up to {date} is attached. {company}'),
 M('an_late', 'Answering service: report late arrivals', 'today', 'today.answering_phone', 'Hello, please report late arrivals from caregivers to the scheduler on {scheduler_phone}. {company}'),
]
assert len(messages) == 34
need = {m['table'] for m in messages}
for t in tables:
    if t['key'] in need and not any(c['key'] == 'company' for c in t['columns']): t['columns'].append(CA('company', 'Agency', 'text', '{set:company}&""', 24))

def L30(c): return '{range:%s},">="&({today}-29),{range:%s},"<="&{today}' % (c, c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
WKN = '({today}-WEEKDAY({today},2)+1)'
def VS(*labs): return ','.join('{range:visits.status},%s' % tok('vstatus', l) for l in labs)
DUE = '{range:visits.status},"<>"&%s,{range:visits.status},"<>"&%s,{range:visits.status},"<>"&%s' % (tok('vstatus', 'Scheduled'), tok('vstatus', 'Open'), tok('vstatus', 'Cancelled'))
HAPP = DUE + ',' + '{range:visits.date},">="&({today}-29),{range:visits.date},"<="&{today}'
LATE_AREA = 'INDEX({range:areamonths.area},MATCH(MAX({range:areamonths.late_rate_2m}),{range:areamonths.late_rate_2m},0))'
kpis = [
 KPI('Visits today', 'COUNTIFS({range:today.date},{today})', 'int'),
 KPI('Visits today without a check-in', 'COUNTIFS({range:today.minutes_overdue},">0")', 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Visits completed this month', 'COUNTIFS({range:visits.date},">="&%s,{range:visits.date},"<="&{today},{range:visits.status},%s)+COUNTIFS({range:visits.date},">="&%s,{range:visits.date},"<="&{today},{range:visits.status},%s)' % (MS, tok('vstatus', 'Completed'), MS, tok('vstatus', 'Late')), 'int'),
 KPI('Visits late this month', 'COUNTIFS({range:register.date},">="&%s,{range:register.date},"<="&{today},{range:register.status},%s)' % (MS, tok('vstatus', 'Late')), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Late rate last 30 days', 'IFERROR(COUNTIFS({range:visits.status},%s,%s)/COUNTIFS(%s),0)' % (tok('vstatus', 'Late'), L30('visits.date'), HAPP), 'pct', alert={"when": "> {set:late_visit_target}", "style": "bad"}),
 KPI('Missed visits this month', 'COUNTIFS({range:register.date},">="&%s,{range:register.date},"<="&{today},{range:register.status},%s)' % (MS, tok('vstatus', 'Missed')), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Missed rate last 30 days', 'IFERROR(COUNTIFS({range:visits.status},%s,%s)/COUNTIFS(%s),0)' % (tok('vstatus', 'Missed'), L30('visits.date'), HAPP), 'pct', alert={"when": "> {set:missed_visit_target}", "style": "bad"}),
 KPI('Client cancellations, last 30 days', 'COUNTIFS(%s)' % L30('cancels.date'), 'int'),
 KPI('Short-notice cancellations, last 30 days', 'COUNTIFS(%s,{range:cancels.short_notice},%s)' % (L30('cancels.date'), ck('Short notice')), 'int'),
 KPI('Average minutes late, last 30 days', 'IFERROR(AVERAGEIFS({range:visits.late_minutes},{range:visits.status},%s,%s),0)' % (tok('vstatus', 'Late'), L30('visits.date')), 'num'),
 KPI('Delivered hours this month', 'SUMIFS({range:agencyweeks.delivered_hours},{range:agencyweeks.month},%s)' % MS, 'num'),
 KPI('Billed hours this month', 'SUMIFS({range:agencyweeks.billed_hours},{range:agencyweeks.month},%s)' % MS, 'num'),
 KPI('Paid hours this month', 'SUMIFS({range:agencyweeks.paid_hours},{range:agencyweeks.month},%s)' % MS, 'num'),
 KPI('Billed minus paid hours, last 4 weeks', 'SUMIFS({range:agencyweeks.billed_minus_paid},{range:agencyweeks.week},">="&(%s-28),{range:agencyweeks.week},"<"&%s)' % (WKN, WKN), 'num'),
 KPI('Leak amount, last 4 weeks', 'SUMIFS({range:agencyweeks.leak_amount},{range:agencyweeks.week},">="&(%s-28),{range:agencyweeks.week},"<"&%s)' % (WKN, WKN), 'money', alert={"when": "> 0", "style": "warn"}),
 KPI('Leak amount this year', 'SUMIFS({range:agencyweeks.leak_amount},{range:agencyweeks.week},">="&DATE(YEAR({today}),1,1))', 'money'),
 KPI('Overlong visits, last 30 days', 'COUNTIFS(%s)' % L30('overlong.date'), 'int'),
 KPI('Unbilled overrun money, last 30 days', 'SUMIFS({range:overlong.unbilled_money},%s)' % L30('overlong.date'), 'money', alert={"when": "> 0", "style": "warn"}),
 KPI('Visits corrected, last 30 days', 'COUNTIFS(%s)' % L30('corrections.date'), 'int'),
 KPI('Time sheets missing this week', 'COUNTIFS({range:timesheets.flag},%s,{range:timesheets.week},%s)' % (ck('Not sent'), WKN), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Time sheet mismatches, last 4 weeks', 'COUNTIFS({range:timesheets.flag},%s,{range:timesheets.week},">="&(%s-28))' % (ck('Mismatch'), WKN), 'int'),
 KPI('Mileage legs, last 30 days', 'COUNTIFS(%s)' % L30('mileage.date'), 'int'),
 KPI('Kilometres, last 30 days', 'SUMIFS({range:mileage.distance_km},%s)' % L30('mileage.date'), 'num'),
 KPI('Mileage paid this month', 'SUMIFS({range:mileage.mileage_pay},{range:mileage.date},">="&%s,{range:mileage.date},"<="&{today})' % MS, 'money'),
 KPI('Paid travel hours this month', 'SUMIFS({range:areamonths.travel_hours},{range:areamonths.month},%s)' % MS, 'num'),
 KPI('Travel cost per visit, last 30 days', 'IFERROR(SUMIFS({range:mileage.cost_leg},%s)/COUNTIFS(%s),0)' % (L30('mileage.date'), HAPP), 'money'),
 KPI('Travel cost share of pay, last 30 days', 'IFERROR(SUMIFS({range:mileage.cost_leg},%s)/SUMIFS({range:visits.pay_estimate},%s),0)' % (L30('mileage.date'), L30('visits.date')), 'pct', alert={"when": "> {set:travel_share_target}", "style": "warn"}),
 KPI('Area with highest late rate, 2 months', LATE_AREA, 'text'),
 KPI('Late visits in that area, 2 months', 'SUMIFS({range:areamonths.late_visits},{range:areamonths.area},%s,{range:areamonths.month},">="&DATE(YEAR({today}),MONTH({today})-1,1))' % LATE_AREA, 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Caregivers with 3+ late visits, 30 days', 'COUNTIFS({range:caregivers.late_30d},">="&{set:repeat_late})', 'int', alert={"when": "> 0", "style": "warn"}),
]
assert len(kpis) == 30
dashboard = {"title": "Visits KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Visits, late visits and missed visits by month", "date": "areamonths.month", "series": [
   {"label": "Visits", "sum": "areamonths.visits", "date": "areamonths.month"}, {"label": "Late visits", "sum": "areamonths.late_visits", "date": "areamonths.month"},
   {"label": "Missed visits", "sum": "areamonths.missed_visits", "date": "areamonths.month"}]},
 "breakdowns": [{"title": "Visits by status", "by": "visits.status", "agg": "count"}, {"title": "Late and missed visits by area", "by": "register.area", "agg": "count"},
                {"title": "Cancellations by notice band", "by": "cancels.notice_band", "agg": "count"}, {"title": "Corrections by field", "by": "corrections.field", "agg": "count"}]}
LT = ('status', '=', tok('vstatus', 'Late')); MI = ('status', '=', tok('vstatus', 'Missed'))
insights = {"filters": [{"label": "Area", "list": "area"}, {"label": "Service", "list": "svc"}, {"label": "Employment type", "list": "emp"}],
 "gauges": [
  {"title": "Visits on time", "num": AGG('count', 'visits', where=[('late_minutes', '<=', '{set:late_minutes}')]), "den": AGG('count', 'visits', where=[('late_minutes', '>=', 0)])},
  {"title": "Check-ins recorded for every visit", "num": AGG('count', 'visits', where=[('check_in', '>', 0)]), "den": AGG('count', 'visits', where=[('status', '<>', tok('vstatus', 'Scheduled')), ('status', '<>', tok('vstatus', 'Cancelled')), ('status', '<>', tok('vstatus', 'Open')), ('status', '<>', tok('vstatus', 'Missed'))])},
  {"title": "Visits not missed", "num": AGG('count', 'visits', where=[('status', '<>', tok('vstatus', 'Scheduled')), ('status', '<>', tok('vstatus', 'Cancelled')), ('status', '<>', tok('vstatus', 'Open')), ('status', '<>', tok('vstatus', 'Missed'))]),
   "den": AGG('count', 'visits', where=[('status', '<>', tok('vstatus', 'Scheduled')), ('status', '<>', tok('vstatus', 'Cancelled')), ('status', '<>', tok('vstatus', 'Open'))])},
  {"title": "Hours billed against hours paid", "num": AGG('sum', 'agencyweeks', 'agencyweeks.billed_hours'), "den": AGG('sum', 'agencyweeks', 'agencyweeks.paid_hours')},
  {"title": "Time sheets matching check-ins", "num": AGG('count', 'timesheets', where=[('flag', '=', ck('Matches'))]), "den": AGG('count', 'timesheets', where=[('flag', '<>', ck('Not sent'))])},
  {"title": "Area months with travel within share", "num": AGG('count', 'areamonths', where=[('travel_share', '<=', '{set:travel_share_target}')]), "den": AGG('count', 'areamonths', where=[('travel_share', '>=', 0)])}],
 "charts": [
  CHART('Visits per month', 'column', 'month', [AGG('sum', 'agencyweeks', 'agencyweeks.visits', date='agencyweeks.week', label='Visits')]),
  CHART('Late rate per month', 'column', 'month', [AGG('avg', 'agencyweeks', 'agencyweeks.late_rate', date='agencyweeks.week', label='Late rate')]),
  CHART('Missed rate per month', 'column', 'month', [AGG('avg', 'agencyweeks', 'agencyweeks.missed_rate', date='agencyweeks.week', label='Missed rate')]),
  CHART('Late visits by area', 'bar', 'register.area', [AGG('count', 'register', where=[LT], label='Late visits')]),
  CHART('Missed visits by area', 'bar', 'register.area', [AGG('count', 'register', where=[MI], label='Missed visits')]),
  CHART('Late visits by reason', 'bar', 'register.delay_reason', [AGG('count', 'register', label='Late visits')]),
  CHART('Missed visits by reason', 'bar', 'register.miss_reason', [AGG('count', 'register', label='Missed visits')]),
  CHART('Late visits by weekday', 'bar', 'register.weekday', [AGG('count', 'register', where=[LT], label='Late visits')]),
  CHART('Late visits by employment type', 'bar', 'register.employment', [AGG('count', 'register', where=[LT], label='Late visits')]),
  CHART('Visits by status', 'bar', 'visits.status', [AGG('count', 'visits', label='Visits')]),
  CHART('Delivered, billed and paid hours per month', 'column', 'month', [AGG('sum', 'agencyweeks', 'agencyweeks.delivered_hours', date='agencyweeks.week', label='Delivered'),
        AGG('sum', 'agencyweeks', 'agencyweeks.billed_hours', date='agencyweeks.week', label='Billed'), AGG('sum', 'agencyweeks', 'agencyweeks.paid_hours', date='agencyweeks.week', label='Paid')]),
  CHART('Leak amount per month', 'column', 'month', [AGG('sum', 'agencyweeks', 'agencyweeks.leak_amount', date='agencyweeks.week', label='Leak amount')]),
  CHART('Billed minus paid hours per month', 'column', 'month', [AGG('sum', 'agencyweeks', 'agencyweeks.billed_minus_paid', date='agencyweeks.week', label='Billed minus paid')]),
  CHART('Paid travel hours per month', 'column', 'month', [AGG('sum', 'areamonths', 'areamonths.travel_hours', date='areamonths.month', label='Paid travel hours')]),
  CHART('Mileage amount per month', 'column', 'month', [AGG('sum', 'areamonths', 'areamonths.mileage_pay', date='areamonths.month', label='Mileage amount')]),
  CHART('Travel cost by area', 'bar', 'pairs.from_area', [AGG('sum', 'pairs', 'pairs.cost', label='Travel cost')]),
  CHART('Kilometres by area', 'bar', 'pairs.from_area', [AGG('sum', 'pairs', 'pairs.km', label='Kilometres')]),
  CHART('Cancellations per month', 'column', 'month', [AGG('count', 'cancels', date='cancels.date', label='Cancellations')]),
  CHART('Cancellations by notice band', 'bar', 'cancels.notice_band', [AGG('count', 'cancels', label='Cancellations')]),
  CHART('Corrections per month', 'column', 'month', [AGG('count', 'corrections', date='corrections.date', label='Corrections')]),
  CHART('Time sheet mismatches per month', 'column', 'month', [AGG('count', 'timesheets', date='timesheets.week', where=[('flag', '=', ck('Mismatch'))], label='Mismatches')]),
  CHART('Average minutes late per month', 'column', 'month', [AGG('avg', 'agencyweeks', 'agencyweeks.avg_late_min', date='agencyweeks.week', label='Minutes late')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Visit log against the schedule", "why": "check-in and check-out are compared with the schedule: minutes late, hours worked, billable hours and a Late, Short, Long or Missed flag", "where": "Visit Log"},
 {"name": "Who to call today list", "why": "visits without a check-in are ranked by minutes overdue with both phones and the verdict who to phone first", "where": "Who to Call Today"},
 {"name": "Late and missed register", "why": "every late or missed visit with reason, phoning, client told and a repeat-caregiver flag", "where": "Late and Missed Register"},
 {"name": "Area problem finder", "why": "an area's late and missed rate against the agency rate, with the gap in points and a verdict", "where": "Area Problem Finder"},
 {"name": "Billed against paid hours with the leak", "why": "delivered, billed and paid hours each week and the leak in money at loaded pay", "where": "Agency Hours by Week"},
 {"name": "Leak by cause", "why": "paid travel, overrun, minimum-visit rounding and missed visits with pay, each in money", "where": "Leak by Cause"},
 {"name": "Mileage and paid travel log", "why": "every travel leg with kilometres, minutes and cost, checked against the distance between areas", "where": "Mileage Log"},
 {"name": "Visit pair sharing", "why": "which two visits on one day should share a caregiver, and the travel saved a month", "where": "Visit Pair Sharing"},
 {"name": "Time sheet reconciliation", "why": "time sheet hours against check-in hours before payroll, with Pay as claimed, Query or Correct", "where": "Time Sheet Check"},
 {"name": "Rounding rule test", "why": "what a 5, 15 or 30 minute rounding step gains or loses a month", "where": "Rounding Rule Test"},
 {"name": "Missed visit cost", "why": "charge lost, cover and goodwill credits added up per month and per 100 visits", "where": "Missed Visit Cost"}]
competitors = [
 {"what": "free schedule template", "lacks": "lists visits but compares no check-in with the schedule and counts no late or missed visits"},
 {"what": "subscription home care software with a per-client fee", "lacks": "charges more as you grow and gives no editable leak, rounding or pair-sharing reports"},
 {"what": "single-sheet time log", "lacks": "records hours only, with no register, no area rates and no time sheet check before payroll"},
 {"what": "generic invoice spreadsheet", "lacks": "bills hours but never compares billed hours with paid hours or travel cost"},
 {"what": "paper mileage book", "lacks": "cannot check a claim against the distance between areas or find visit pairs to share"}]
guide = [
 'Open Start and type your agency name and your targets in the yellow cells: the late limit in minutes, the late and missed targets, the time now and the mileage rate.',
 'Check Caregivers, Clients, Services, Areas, Travel Times and Team. A caregiver is a carer, care worker or support worker. A one-person agency can keep only a few rows.',
 'Log each visit on Visit Log with the check-in and check-out times typed or pasted from whatever you use; there is no app and no GPS. Minutes late, hours worked, billable hours and the flag fill in.',
 'Each morning open Today Check-ins, type the time now in Start and read the call-first rank; Who to Call Today lists the five visits to phone about.',
 'Record every late or missed visit on Late and Missed Register with the reason, the phoning and whether the client was told; repeat caregivers are flagged.',
 'Keep Caregiver Hours by Week, Agency Hours by Week and Client Hours by Month up to date; the leak is the money paid for hours that were not billed.',
 'Log travel legs on Mileage Log. Travel by Area Pair and the Visit Pair Sharing and Area Clustering tools show where one caregiver can take two visits.',
 'Before each pay run use Time Sheet Check: a difference above the tolerance is queried. Pay, overtime and payroll taxes: check your own local rules and confirm with your adviser.',
 'Record corrections, client cancellations and overlong visits so the unbilled money and the notice rules are visible.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Why a workbook: one flat price, no per-client or per-caregiver fee, and your data stays with you. A one-person agency can start with Visit Log, Time Sheet Check and Mileage Log.',
 'Read the Visits KPI Dashboard and Charts every week: late rate, missed rate, hours delivered, billed and paid, the leak and travel.']
listing = {"title": "Home Care Agency Visit Tracker Excel Template: Late and Missed Visits, Billed vs Paid Hours, Mileage, Time Sheets, KPI Dashboard",
 "headline": "See late visits, hour leaks and travel cost in one Excel file",
 "tags": ["home care agency", "visit tracker", "time sheet check", "mileage log", "late visit log", "caregiver hours", "care agency excel", "check-in log", "billable hours", "agency management", "excel template", "missed visits", "travel cost"],
 "description": ("Compare what was scheduled with what happened, visit by visit, in one Excel workbook built for a small non-medical home care agency run by an owner-director, a scheduler, an office manager and field supervisors. A one-person start-up agency can use the Visit Log, Time Sheet Check and Mileage Log pages as its own time sheet.\n\n"
  "Visit Log takes check-in and check-out times typed or pasted from whatever you use (there is no app, no GPS and no automatic check-in) and works out minutes late, hours worked, billable hours and a Late, Short, Long or Missed flag. Today Check-ins ranks the visits without a check-in so you know who to phone first. "
  "Late and Missed Register records the reason, the phoning and whether the client was told, and flags repeat cases. Agency Hours by Week sets hours delivered against billed against paid and puts the leak in money. Area Performance by Month shows which area runs late.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: scheduled against actual, who to call today, late and missed rate, area problem finder, leak by cause, mileage claim check, visit pair sharing, area clustering saving, time sheet reconciliation, rounding rule test, missed visit cost and more. "
  f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
  "This is part three of the Home Care Agency Business suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-client or per-caregiver fee, your data stays with you, 15 languages in one purchase, and a demo copy full of sample data. The workbook holds dates, times, hours and amounts only, never care notes, and it does not promise results."),
 "features": ["Visit log with minutes late and billable hours", "Who to call today, ranked", "Late and missed register with repeat flags", "Billed against paid hours with the leak in money", "Mileage and paid travel log",
              "Time sheet check before payroll", "Area problem finder and pair sharing", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
              f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
def _trim(x, n=200):
    if len(x) <= n: return x
    parts = x.split('. ')
    while len('. '.join(parts)) > n - 1 and len(parts) > 1: parts.pop()
    r = '. '.join(parts)
    if len(r) > n - 1:
        r = r[:n - 2]
        for sep in ('; ', ', '):
            if sep in r: r = r[:r.rindex(sep)]; break
    return r if r.endswith('.') else r + '.'
for t_ in tables + tools: t_['hint'] = _trim(t_['hint'])
s = _lib.spec(id=f'{SUITE}-p3', slug='home-care-visits', profession='Home Care Agency Business', name='Visits, Hours and Travel',
         tagline='Late visits, billed against paid hours and travel in one file', price_usd=29, colors={"primary": "#3A506B", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Visits, hours and travel"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hc3.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
