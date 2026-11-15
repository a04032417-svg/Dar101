"""Home care agency suite - part 7: Client Margin and Hours Growth."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from hc7_lists import *
from hc7_tables import settings, tables
from hc7_tools import tools
from hc_core import SUITE

NOTE = "Sample wording: adapt it to your own agency and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
def RL(col, t='rises', k='client_id'): return 'IFERROR(INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0)),"")' % (t, col, t, k)
def ML(col): return RL(col, 'margin')
def CLK(col): return 'IFERROR(INDEX({range:clients.%s},MATCH({pick},{range:clients.client_id},0)),"")' % col

forms = [
 FORM('review_sheet', 'Margin Review Sheet', 'Client margin review with loaded cost', 'margin.client_id', F(
  ('Client', 'margin.client'), ('Payer', 'margin.payer'), ('Service', 'margin.service'), ('Area', 'margin.area'), ('Weekly hours', 'margin.weekly_hours'), ('Bill rate per hour', 'margin.bill_rate'), ('Pay per hour', 'margin.pay_hour'),
  ('Paid travel per hour', 'margin.travel_hour'), ('Mileage per hour', 'margin.mileage_hour'), ('Overtime per hour', 'margin.ot_hour'), ('Cover premium per hour', 'margin.cover_hour'), ('Loaded cost per hour', 'margin.loaded_cost'),
  ('Margin per hour', 'margin.margin_hour'), ('Margin per week', 'margin.margin_week'), ('Margin share', 'margin.margin_pct'), ('Margin check', 'margin.flag'), ('Gap to the target per week', 'margin.gap_week'),
  ('Rate for the target margin', 'margin.rate_needed'), ('Worst-first rank', 'margin.rank'), ('Review date', 'margin.review_on'))),
 FORM('keep_sheet', 'Keep or Raise Sheet', 'Keep, raise or release a client', 'rises.client_id', F(
  ('Client', 'rises.client'), ('Client phone', 'rises.phone'), ('Weekly hours', 'rises.hours'), ('Current rate per hour', 'rises.current_rate'), ('Margin share now', 'rises.margin_pct'), ('Margin per week now', 'rises.margin_week'),
  ('Risk of leaving', 'rises.risk'), ('Proposed rise', 'rises.rise_pct'), ('New rate per hour', 'rises.new_rate'), ('Chance they leave', 'rises.leave_chance'), ('Income gain a year if they stay', 'rises.gain_year'),
  ('Expected net effect a year', 'rises.expected_net'), ('Verdict', 'rises.verdict')) + [
  FF('Margin check', ML('flag'), 'text'), FF('Rate for the target margin', ML('rate_needed'), 'money'), FF('Rise needed for the target, percent', 'IFERROR(MAX(0,INDEX({range:margin.rate_needed},MATCH({pick},{range:margin.client_id},0))/INDEX({range:rises.current_rate},MATCH({pick},{range:rises.client_id},0))-1),"")', 'pct'),
  FF('Gap to the target per week', ML('gap_week'), 'money')]),
 FORM('rise_sheet', 'Rate Rise Sheet', 'Rate rise with history of earlier rises', 'rises.client_id', F(
  ('Client', 'rises.client'), ('Current rate per hour', 'rises.current_rate'), ('Proposed rise', 'rises.rise_pct'), ('New rate per hour', 'rises.new_rate'), ('New rate from', 'rises.effective_on'), ('Risk of leaving', 'rises.risk'),
  ('Chance they leave', 'rises.leave_chance'), ('Income gain a year if they stay', 'rises.gain_year'), ('Expected net effect a year', 'rises.expected_net'), ('Verdict', 'rises.verdict'), ('Raise order', 'rises.net_rank')) + [
  FF('Rises made before', 'COUNTIFS({range:risehist.client},INDEX({range:rises.client},MATCH({pick},{range:rises.client_id},0)))', 'int'),
  FF('Last rise date', 'IFERROR(SUMPRODUCT(MAX(({range:risehist.client}=INDEX({range:rises.client},MATCH({pick},{range:rises.client_id},0)))*({range:risehist.date}))),"")', 'date'),
  FF('Rise share of the last rise', 'IFERROR(INDEX({range:risehist.rise_share},MATCH(INDEX({range:rises.client},MATCH({pick},{range:rises.client_id},0)),{range:risehist.client},0)),"")', 'pct')]),
 FORM('notice_sheet', 'Rate Notice Log Sheet', 'Rate notice log with notice given', 'rises.client_id', F(
  ('Client', 'rises.client'), ('Client phone', 'rises.phone'), ('Family contact phone', 'rises.family_phone'), ('New rate per hour', 'rises.new_rate'), ('New rate from', 'rises.effective_on'), ('Notice sent on', 'rises.notice_on'),
  ('Notice check', 'rises.notice_check'), ('Notices still to send', 'rises.notice_count'), ('Verdict', 'rises.verdict')) + [
  FF('Days of notice given', 'IFERROR(INDEX({range:rises.effective_on},MATCH({pick},{range:rises.client_id},0))-INDEX({range:rises.notice_on},MATCH({pick},{range:rises.client_id},0)),"")', 'int'),
  FF('Days of notice you aim for', '{set:notice_days}', 'int')]),
 FORM('minvisit_sheet', 'Minimum Visit Sheet', 'Minimum visit check with true margin per visit', 'minvisit.client_id', F(
  ('Client', 'minvisit.client'), ('Client phone', 'minvisit.phone'), ('Minimum visit, hours', 'minvisit.min_visit_hours'), ('Visits, last 90 days', 'minvisit.visits_90'), ('Visits at the minimum', 'minvisit.visits_min'),
  ('Share of visits at the minimum', 'minvisit.short_share'), ('Average hours worked', 'minvisit.avg_hours'), ('Average hours billed', 'minvisit.avg_billed'), ('Average travel minutes', 'minvisit.avg_travel_min'),
  ('Billed minus worked plus travel', 'minvisit.gap_hours'), ('Revenue per visit', 'minvisit.rev_visit'), ('Loaded cost per visit', 'minvisit.cost_visit'), ('True margin per visit', 'minvisit.margin_visit'),
  ('Margin share per visit', 'minvisit.margin_visit_pct'), ('Loss check', 'minvisit.flag'), ('Travel charge to cover a visit', 'minvisit.travel_charge'), ('New minimum, hours', 'minvisit.new_min_visit'), ('Change from', 'minvisit.change_on'))),
 FORM('end_sheet', 'Client End Sheet', 'Client end with reason and revenue lost', 'ends.client_id', F(
  ('Client', 'ends.client'), ('Client phone', 'ends.phone'), ('End date', 'ends.end_date'), ('Weekly hours lost', 'ends.hours_lost'), ('Reason', 'ends.reason'), ('Tenure, days', 'ends.tenure_days'),
  ('Revenue lost a year', 'ends.revenue_lost'), ('Clients with the same reason', 'ends.same_reason'), ('Field supervisor', 'ends.sup_name')) + [
  FF('Payer', CLK('payer'), 'text'), FF('Service', CLK('service'), 'text'), FF('Area', CLK('area'), 'text'), FF('Start date', CLK('start_date'), 'date')]),
 FORM('start_sheet', 'Client Start Hours Sheet', 'Client start hours at start and 90 days', 'starts.client_id', F(
  ('Client', 'starts.client'), ('Start date', 'starts.start_date'), ('Weekly hours at start', 'starts.hours_start'), ('Weekly hours after 90 days', 'starts.hours_90'), ('Growth in hours', 'starts.growth_hours'),
  ('Growth share', 'starts.growth_pct'), ('Source', 'starts.source'), ('Days since start', 'starts.days_since'), ('Scheduler', 'starts.sched_name')) + [
  FF('Payer', CLK('payer'), 'text'), FF('Service', CLK('service'), 'text'), FF('Area', CLK('area'), 'text'), FF('Bill rate per hour', CLK('bill_rate'), 'money')]),
 FORM('payscen_sheet', 'Pay Scenario Sheet', 'Pay scenario with margin, cost and turnover saving', 'payscen.scenario_id', F(
  ('Pay step', 'payscen.step'), ('Pay rise per hour', 'payscen.pay_rise'), ('Share of hours covered', 'payscen.covers'), ('Change in yearly turnover (your guess)', 'payscen.turnover_change'), ('Cost per client hour', 'payscen.delta_hour'),
  ('Margin per hour after the rise', 'payscen.new_margin_hour'), ('Margin share after the rise', 'payscen.new_margin_pct'), ('Bill rate rise clients would need', 'payscen.rate_rise_needed'),
  ('Cost of the rise a year', 'payscen.cost_year'), ('Turnover saving a year', 'payscen.saving_year'), ('Net cost or saving a year', 'payscen.net_year'), ('Verdict', 'payscen.verdict'))),
 FORM('churn_sheet', 'Churn Reason Sheet', 'Churn reason for one month', 'reasons.reason_id', F(
  ('Month', 'reasons.month'), ('Reason', 'reasons.reason'), ('Clients ended', 'reasons.clients'), ('Weekly hours lost', 'reasons.hours_lost'), ('Share of the month', 'reasons.share'), ('Hours per client', 'reasons.hours_per_client')) + [
  FF('Clients ended in the month', 'IFERROR(SUMIFS({range:growth.clients_ended},{range:growth.month},INDEX({range:reasons.month},MATCH({pick},{range:reasons.reason_id},0))),"")', 'int'),
  FF('Churn rate of the month', 'IFERROR(SUMIFS({range:growth.churn_rate},{range:growth.month},INDEX({range:reasons.month},MATCH({pick},{range:reasons.reason_id},0))),"")', 'pct'),
  FF('Clients ended for this reason, all time', 'IFERROR(SUMIFS({range:reasons.clients},{range:reasons.reason},INDEX({range:reasons.reason},MATCH({pick},{range:reasons.reason_id},0))),"")', 'int')]),
 FORM('service_sheet', 'Service Review Sheet', 'Service review for one month', 'svcmonth.month_id', F(
  ('Month', 'svcmonth.month'), ('Service', 'svcmonth.service'), ('Visits', 'svcmonth.visits'), ('Billed hours', 'svcmonth.billed_hours'), ('Revenue', 'svcmonth.revenue'), ('Cost', 'svcmonth.cost'), ('Margin', 'svcmonth.margin'),
  ('Margin share', 'svcmonth.margin_pct'), ('Margin per hour', 'svcmonth.margin_hour'), ('Travel and mileage cost', 'svcmonth.travel_cost'), ('Overtime cost', 'svcmonth.overtime_cost')) + [
  FF('Margin share of all services that month', 'IFERROR(SUMIFS({range:svcmonth.margin},{range:svcmonth.month},INDEX({range:svcmonth.month},MATCH({pick},{range:svcmonth.month_id},0)))/SUMIFS({range:svcmonth.revenue},{range:svcmonth.month},INDEX({range:svcmonth.month},MATCH({pick},{range:svcmonth.month_id},0))),"")', 'pct'),
  FF('Share of the month\'s billed hours', 'IFERROR(INDEX({range:svcmonth.billed_hours},MATCH({pick},{range:svcmonth.month_id},0))/SUMIFS({range:svcmonth.billed_hours},{range:svcmonth.month},INDEX({range:svcmonth.month},MATCH({pick},{range:svcmonth.month_id},0))),"")', 'pct')]),
 FORM('payer_sheet', 'Payer Rate Review Sheet', 'Payer rate review for one month', 'paymonth.month_id', F(
  ('Month', 'paymonth.month'), ('Payer', 'paymonth.payer'), ('Billed hours', 'paymonth.billed_hours'), ('Revenue', 'paymonth.revenue'), ('Cost', 'paymonth.cost'), ('Margin', 'paymonth.margin'), ('Margin share', 'paymonth.margin_pct'),
  ('Revenue per billed hour', 'paymonth.rate_hour'), ('Points behind private pay', 'paymonth.points_behind')) + [
  FF('Share of the month\'s billed hours', 'IFERROR(INDEX({range:paymonth.billed_hours},MATCH({pick},{range:paymonth.month_id},0))/SUMIFS({range:paymonth.billed_hours},{range:paymonth.month},INDEX({range:paymonth.month},MATCH({pick},{range:paymonth.month_id},0))),"")', 'pct'),
  FF('Revenue per billed hour, private pay', 'IFERROR(SUMIFS({range:paymonth.revenue},{range:paymonth.month},INDEX({range:paymonth.month},MATCH({pick},{range:paymonth.month_id},0)),{range:paymonth.payer},%s)/SUMIFS({range:paymonth.billed_hours},{range:paymonth.month},INDEX({range:paymonth.month},MATCH({pick},{range:paymonth.month_id},0)),{range:paymonth.payer},%s),"")' % (tok('payer', 'Private pay'), tok('payer', 'Private pay')), 'money')]),
 FORM('pattern_sheet', 'Visit Pattern Sheet', 'Client visit pattern: overtime, travel and cover', 'otravel.client_id', F(
  ('Client', 'otravel.client'), ('Period ends', 'otravel.period_end'), ('Billed hours', 'otravel.hours'), ('Revenue', 'otravel.revenue'), ('Overtime cost', 'otravel.overtime_cost'), ('Paid travel', 'otravel.travel_pay'),
  ('Mileage', 'otravel.mileage_pay'), ('Cover premium', 'otravel.cover_cost'), ('Extras in total', 'otravel.extra_cost'), ('Extras per hour', 'otravel.cost_hour'), ('Share of revenue', 'otravel.share_revenue'),
  ('Margin share', 'otravel.margin_pct'), ('Weekly hours', 'otravel.weekly_hours')) + [
  FF('Visits, last 90 days', 'IFERROR(INDEX({range:minvisit.visits_90},MATCH({pick},{range:minvisit.client_id},0)),"")', 'int'),
  FF('Average travel minutes per visit', 'IFERROR(INDEX({range:minvisit.avg_travel_min},MATCH({pick},{range:minvisit.client_id},0)),"")', 'num'), FF('Average km per visit', 'IFERROR(INDEX({range:minvisit.avg_km},MATCH({pick},{range:minvisit.client_id},0)),"")', 'num')]),
]
assert len(forms) == 12

def D_(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('margin_report', 'Client Margin Report', 'Client margin report, worst first', 'margin.client_id', [
  'Client margin report of {set:company}, dated {today}. Client: {col:margin.client} ({col:margin.service}, {col:margin.area}, payer: {col:margin.payer}). Report date: {today}.',
  'Weekly hours: {col:margin.weekly_hours}. Bill rate per hour: {col:margin.bill_rate}. Pay per hour: {col:margin.pay_hour}. Paid travel per hour: {col:margin.travel_hour}. Mileage per hour: {col:margin.mileage_hour}. Overtime per hour: {col:margin.ot_hour}. Cover premium per hour: {col:margin.cover_hour}.',
  'Loaded cost per hour: {col:margin.loaded_cost} (pay, travel, overtime and cover with the payroll burden on top; confirm the burden with your adviser). Margin per hour: {col:margin.margin_hour}. Margin per week: {col:margin.margin_week}.',
  'Margin share: {col:margin.margin_pct} against a wanted share of {set:target_margin}. Margin check: {col:margin.flag}. Worst-first rank: {col:margin.rank} (1 is the weakest client). Gap to the target per week: {col:margin.gap_week}.',
  'The rate that reaches the target margin is {col:margin.rate_needed} an hour. Review date: {col:margin.review_on}.'], ['Owner-director', 'Office manager']),
 D_('keep_doc', 'Keep or Raise Note', 'Keep-or-raise recommendation for one client', 'rises.client_id', [
  'Keep-or-raise recommendation of {set:company}, dated {today}. Client: {col:rises.client}.',
  'Current rate: {col:rises.current_rate} an hour for {col:rises.hours} hours a week. Margin share now: {col:rises.margin_pct}; margin per week: {col:rises.margin_week}. Wanted margin share: {set:target_margin}.',
  'Proposed rise: {col:rises.rise_pct}, giving a new rate of {col:rises.new_rate} an hour from {col:rises.effective_on}. Income gain a year if the client stays: {col:rises.gain_year}.',
  'Risk of leaving: {col:rises.risk} (chance {col:rises.leave_chance}, the owner\'s guess). Expected net effect a year: {col:rises.expected_net}. Verdict: {col:rises.verdict}.'], ['Owner-director']),
 D_('rise_letter', 'Rate Rise Letter', 'Rate rise letter to a client', 'rises.client_id', [
  'Letter of {set:company}, dated {today}. Dear {col:rises.client},',
  'Thank you for choosing us. We review our rates each year so that we can keep paying our caregivers fairly and keep your visits reliable. From {col:rises.effective_on} the rate for your visits changes from {col:rises.current_rate} to {col:rises.new_rate} an hour, before any tax.',
  'We give you at least {set:notice_days} days of notice. If you would like to talk about the change, or about your visit times, please contact us and we will find a time to speak.',
  'We value looking after you and hope to continue. Reference: {col:rises.client_id}.'], ['Owner-director']),
 D_('ratecard_doc', 'Updated Rate Card', 'Updated rate card line', 'ratecard.rate_id', [
  'Rate card of {set:company}, dated {today}. Line {col:ratecard.rate_id}.',
  'Service: {col:ratecard.service}. Time band: {col:ratecard.band}. Bill rate: {col:ratecard.bill_rate} an hour before any tax. A payer may agree a share of this rate.',
  'Standard pay rate for this line: {col:ratecard.pay_rate} an hour; loaded pay with the payroll burden: {col:ratecard.loaded_pay} (confirm the burden with your adviser). Margin per hour: {col:ratecard.margin_hour}; margin share: {col:ratecard.margin_pct}.',
  'The holiday rate (a bank holiday in your area) is a multiple of the weekday rate. Check your own local rules and your contract terms before you publish a rate card.'], ['Owner-director']),
 D_('minvisit_notice', 'Minimum Visit Notice', 'Minimum visit notice', 'minvisit.client_id', [
  'Notice of {set:company}, dated {today}. Dear {col:minvisit.client},',
  'Your minimum visit is now {col:minvisit.min_visit_hours} hours. From {col:minvisit.change_on} the minimum visit will be {col:minvisit.new_min_visit} hours. A visit shorter than the minimum is billed at the minimum, because our caregivers travel to you and plan their day around each visit.',
  'In the last 90 days we made {col:minvisit.visits_90} visits for you, and {col:minvisit.visits_min} were shorter than the minimum. Please contact us if you would like to talk about your visit times. We give {set:notice_days} days of notice.'], ['Office manager']),
 D_('end_letter', 'End of Service Letter', 'Polite end-of-service letter with notice period', 'ends.client_id', [
  'Letter of {set:company}, dated {today}. Dear {col:ends.client},',
  'Thank you for the time we looked after you. As we agreed, our visits end on {col:ends.end_date}. We aim to give at least {set:notice_days} days of notice, so that you have time to arrange what comes next.',
  'We will settle the last visits and any balance with you, and we are happy to share your visit dates and hours on request. Your feedback is welcome: it helps us improve.',
  'Reference {col:ends.client_id}. Check your own local rules on notice and records.'], ['Owner-director']),
 D_('growth_report', 'Hours Growth Report', 'Hours growth report for one month', 'growth.month_id', [
  'Hours growth report of {set:company}, dated {today}. Month: {col:growth.month}.',
  'Clients started: {col:growth.clients_started}. Clients ended: {col:growth.clients_ended}. Weekly hours added: {col:growth.hours_added}. Weekly hours lost: {col:growth.hours_lost}. Net hours: {col:growth.net_hours}.',
  'Active clients: {col:growth.active_clients}. Weekly hours at month end: {col:growth.weekly_hours_end}. Churn rate: {col:growth.churn_rate} against an accepted {set:churn_limit} a month.',
  'Forecast: {col:growth.hours6} weekly hours in 6 months. Months to the hours marker of {set:scheduler_hours}: {col:growth.months_marker}.'], ['Owner-director']),
 D_('churn_report', 'Churn Report', 'Churn report for one reason and month', 'reasons.reason_id', [
  'Churn report of {set:company}, dated {today}. Month: {col:reasons.month}.',
  'Reason: {col:reasons.reason}. Clients ended: {col:reasons.clients}. Weekly hours lost: {col:reasons.hours_lost}. Hours per client: {col:reasons.hours_per_client}. Share of the month\'s ended clients: {col:reasons.share}.',
  'Review each reason with the field supervisors and decide one change for the next month: price, service, funding or fit.'], ['Owner-director', 'Field supervisor']),
 D_('payscen_doc', 'Pay Scenario Summary', 'Pay scenario summary', 'payscen.scenario_id', [
  'Pay scenario summary of {set:company}, dated {today}. Scenario: {col:payscen.step}.',
  'Pay rise per hour: {col:payscen.pay_rise}, covering {col:payscen.covers} of caregiver hours. Cost per client hour with the payroll burden: {col:payscen.delta_hour} (confirm the burden with your adviser).',
  'Margin per hour after the rise: {col:payscen.new_margin_hour}; margin share after the rise: {col:payscen.new_margin_pct}. The bill rate rise clients would need to keep today\'s share: {col:payscen.rate_rise_needed}.',
  'Cost of the rise a year: {col:payscen.cost_year}. Turnover saving a year (guess of {col:payscen.turnover_change} change in turnover): {col:payscen.saving_year}. Net cost or saving a year: {col:payscen.net_year}. Verdict: {col:payscen.verdict}.'], ['Owner-director']),
 D_('service_doc', 'Service Margin Report', 'Service margin report for one month', 'svcmonth.month_id', [
  'Service margin report of {set:company}, dated {today}. Month: {col:svcmonth.month}. Service: {col:svcmonth.service}.',
  'Visits: {col:svcmonth.visits}. Billed hours: {col:svcmonth.billed_hours}. Revenue: {col:svcmonth.revenue}. Cost: {col:svcmonth.cost}. Margin: {col:svcmonth.margin}. Margin share: {col:svcmonth.margin_pct} against a wanted {set:target_margin}.',
  'Margin per billed hour: {col:svcmonth.margin_hour}. Paid travel and mileage: {col:svcmonth.travel_cost}. Overtime cost: {col:svcmonth.overtime_cost}.'], ['Owner-director']),
 D_('payer_doc', 'Payer Margin Report', 'Payer margin report for one month', 'paymonth.month_id', [
  'Payer margin report of {set:company}, dated {today}. Month: {col:paymonth.month}. Payer: {col:paymonth.payer}.',
  'Billed hours: {col:paymonth.billed_hours}. Revenue: {col:paymonth.revenue}. Cost: {col:paymonth.cost}. Margin: {col:paymonth.margin}. Margin share: {col:paymonth.margin_pct}. Revenue per billed hour: {col:paymonth.rate_hour}.',
  'Points behind private pay (self-funded clients): {col:paymonth.points_behind}. A third-party payer may be an insurer, a public body or an employer scheme in your area; check your contract terms before you ask for a new rate.'], ['Owner-director', 'Office manager']),
 D_('review_pack', 'Yearly Rate Review Pack', 'Yearly rate review pack: one earlier rise', 'risehist.rise_id', [
  'Yearly rate review pack of {set:company}, dated {today}. Rise {col:risehist.rise_id}.',
  'Client: {col:risehist.client}. Rise date: {col:risehist.date}. Old rate: {col:risehist.old_rate} an hour. New rate: {col:risehist.new_rate} an hour. Rise share: {col:risehist.rise_share}.',
  'Outcome: {col:risehist.outcome}. Weekly hours before the rise: {col:risehist.hours_before}. After 3 months: {col:risehist.hours_after}. Hours kept: {col:risehist.hours_kept}.',
  'Use the history of all rises to choose next year\'s rise and to set the risk marker for each client.'], ['Owner-director']),
]
assert len(documents) == 12

def CS(key_, title, table, start, steps): return _lib.CHK(key_, title, table, start, steps)
checklists = [
 CS('c_month', 'Monthly Margin Review', 'svcmonth', 'svcmonth.month', [('Compare margin share by service with the month before', 1), ('Check overtime and travel cost per service', 2), ('List clients below the target on Client Margin', 3), ('Update the rate rise proposals', 4), ('Send the scheduler the weak clients', 5), ('Record decisions and dates', 7)]),
 CS('c_below', 'Below-target Client Review', 'margin', 'margin.review_on', [('Open the client row on Client Margin', 0), ('Check pay, travel, overtime and cover per hour', 0), ('Look at short or far visits on Visits with Margin', 1), ('Decide: keep, raise the rate or release', 2), ('Tell the scheduler what to change', 3), ('Record the decision', 3)]),
 CS('c_rise', 'Rate Rise Decision', 'rises', 'rises.effective_on', [('Review the margin share and the risk marker', -60), ('Check the rate is not locked in the agreement', -55), ('Run the rate rise effect tool', -50), ('Prepare the rate rise letter', -40), ('Send the notice with the notice period', -35), ('Ask a field supervisor to talk to high risk clients', -30), ('Update the rate in billing on the new date', 0), ('Check hours three months later', 90)]),
 CS('c_notice', 'Rate Notice Sent', 'rises', 'rises.effective_on', [('Send the notice to the client', -35), ('Send a note to the family contact if one is listed', -33), ('Tell the field supervisor', -30), ('Tell the office manager the new rate', -14), ('Check the first invoice at the new rate', 14)]),
 CS('c_minvisit', 'Minimum Visit Review', 'minvisit', 'minvisit.reviewed_on', [('Check visits at the minimum and the share', 0), ('Check travel minutes and kilometres', 0), ('Run the minimum visit loss tool', 1), ('Choose: raise the minimum, add a travel charge or leave it', 2), ('Send the notice with the notice period', 3), ('Record the new minimum in the agreement', 5)]),
 CS('c_end', 'Ending Service for a Client', 'ends', 'ends.end_date', [('Confirm the end date and the notice period', -30), ('Tell the scheduler to release the visits', -14), ('Send the end-of-service letter', -14), ('Settle the last invoice and any balance', 3), ('Record the reason and the hours lost', 0), ('Thank the client and the family contact', 1)]),
 CS('c_exit', 'Client Exit Reason Capture', 'reasons', 'reasons.month', [('Ask each leaving client why, in their own words', 0), ('Record the reason from the list', 3), ('Group the month by reason', 30), ('Talk through price and service reasons with the team', 35), ('Choose one change for next month', 37)]),
 CS('c_paystep', 'Yearly Pay Scale Review', 'paycg', 'paycg.change_on', [('Compare pay rates with the Pay Rate Scenarios page', -60), ('Run the pay rise against turnover tool', -55), ('Decide the new pay rates', -45), ('Tell each caregiver before the change', -30), ('Send the new rates to the payroll service', -14), ('Check the margin after the first pay run', 21)]),
 CS('c_growth', 'Monthly Hours Growth Review', 'growth', 'growth.month', [('Count clients started and ended', 1), ('Check weekly hours at month end', 1), ('Compare churn with the limit', 2), ('Update the hours forecast', 3), ('Check the hours marker for a dedicated scheduler', 4)]),
 CS('c_mix', 'Service Mix Review', 'cmonths', 'cmonths.month', [('Compare margin share by service', 1), ('Name the service to grow and the service to fix', 2), ('Check the rate card for the weakest service', 3), ('Ask the marketing helper to focus on the strongest service', 5), ('Record the plan', 7)]),
 CS('c_payer', 'Payer Rate Review', 'paymonth', 'paymonth.month', [('Compare margin share by payer with private pay', 1), ('Check days to be paid with the office manager', 2), ('Check each payer contract terms for a rate review', 5), ('Decide which payer hours to grow or limit', 7)]),
 CS('c_year', 'Year-end Client Review', 'otravel', 'otravel.period_end', [('Review margin share for every client', 0), ('List clients below the target and the red line', 1), ('Review overtime, travel and cover per client', 3), ('Decide the rate rises for next year', 7), ('Set the risk marker for each client', 7), ('Plan the notices with the notice period', 10)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('r_change', 'Client: our rates change from a date', 'rises', 'rises.phone', 'Hello {client}, from {effective_on} our rate for your visits is {new_rate} an hour. The notice is attached. Please reply here with any question. {company}'),
 M('r_minvisit', 'Client: your minimum visit changes', 'minvisit', 'minvisit.phone', 'Hello {client}, from {change_on} the minimum visit is {new_min_visit} hours. The notice is attached. Please reply here if you would like to talk about it. {company}'),
 M('r_talk', 'Client: let us talk about your rate', 'rises', 'rises.phone', 'Hello {client}, we would like to talk about the rate for your visits. When is a good time for a short call this week? {company}'),
 M('r_same', 'Client: your rate stays the same', 'rises', 'rises.phone', 'Hello {client}, your rate stays at {current_rate} an hour this year. Thank you for staying with {company}.'),
 M('r_end', 'Client: we can no longer serve you', 'ends', 'ends.phone', 'Hello {client}, we are sorry that we can no longer serve you after {end_date}. The notice is attached. We will help to settle the last visits. {company}'),
 M('r_feedback', 'Client: thank you for your feedback', 'ends', 'ends.phone', 'Hello {client}, thank you for telling us why you ended care ({reason}). Your feedback helps us to improve. {company}'),
 M('r_times', 'Client: your agreed hours and rate', 'clients', 'clients.phone', 'Hello {client}, this confirms your agreed {weekly_hours} hours a week at {bill_rate} an hour from {start_date}. Reply here to change a visit time. {company}'),
 M('r_holiday', 'Client: the holiday rate applies', 'clients', 'clients.phone', 'Hello {client}, the holiday rate of {holiday_rate} an hour applies on {holiday_name} ({holiday_on}). Reply here if you would like to change your visits. {company}'),
 M('r_travel', 'Client: a travel charge for each visit', 'minvisit', 'minvisit.phone', 'Hello {client}, we would like to add a travel charge of {travel_charge} a visit to cover the travel to your home. Please reply here to talk it through. {company}'),
 M('r_family', 'Family contact: note on a rate change', 'rises', 'rises.family_phone', 'Hello, this is {company}. A note about {client}: from {effective_on} the rate for visits is {new_rate} an hour. We have sent the notice to {client}. Please reply with any question.'),
 M('s_below', 'Scheduler: a client is below the target', 'margin', 'margin.sched_phone', 'Hello {sched_name}, {client} is below the target margin ({share_pct} percent). Please review their visit times and caregiver. {company}'),
 M('s_cluster', 'Scheduler: cluster short far visits', 'minvisit', 'minvisit.sched_phone', 'Hello {sched_name}, {client} has short visits far from other visits ({avg_travel_min} travel minutes on average). Please cluster them. {company}'),
 M('s_lowerpay', 'Scheduler: move to a lower pay rate', 'margin', 'margin.sched_phone', 'Hello {sched_name}, please move {client} to a caregiver with a lower pay rate if you can: pay is {pay_hour} an hour against a bill rate of {bill_rate}. {company}'),
 M('s_newclient', 'Scheduler: new client, record the hours', 'starts', 'starts.sched_phone', 'Hello {sched_name}, {client} is a new client from {start_date}. Please record the weekly hours at the start ({hours_start}). {company}'),
 M('f_rise', 'Field supervisor: talk about the rate', 'rises', 'rises.sup_phone', 'Hello {sup_name}, please talk to {client} about the rate review before {effective_on}. The new rate would be {new_rate} an hour. {company}'),
 M('f_ended', 'Field supervisor: client ended', 'ends', 'ends.sup_phone', 'Hello {sup_name}, {client} ended care on {end_date}. Please record the reason ({reason}) with them. {company}'),
 M('c_pay', 'Caregiver: your pay rate changes', 'paycg', 'paycg.phone', 'Hello {name}, your pay rate changes to {new_pay_rate} an hour from {change_on}. Thank you for your work. {company}'),
 M('c_route', 'Caregiver: a longer route, mileage', 'paycg', 'paycg.phone', 'Hello {name}, from {change_on} you will cover a longer route. Mileage of {mileage_rate} a km is paid, and travel time is paid at your pay rate. {company}'),
 M('o_rate', 'Office manager: update the client rate', 'rises', 'rises.office_phone', 'Hello {office_name}, please update the rate for {client} to {new_rate} an hour from {effective_on}. {company}'),
 M('o_minvisit', 'Office manager: minimum visit changes', 'minvisit', 'minvisit.office_phone', 'Hello {office_name}, the minimum visit for {client} changes to {new_min_visit} hours from {change_on}. Please update the agreement. {company}'),
 M('o_below', 'Office manager: clients below the target', 'margin', 'margin.office_phone', 'Hello {office_name}, {below_count} clients are below the target margin. The list is on the Client Margin page. {company}'),
 M('o_notices', 'Office manager: rate notices are ready', 'rises', 'rises.office_phone', 'Hello {office_name}, the rate rise notices are ready to send. {notice_count} are still to send. {company}'),
 M('w_belowcost', 'Owner: a client is billed below cost', 'margin', 'margin.owner_phone', 'Hello {owner_name}, {client} has a margin share of {share_pct} percent. Please decide: keep, raise the rate or release. {company}'),
 M('w_weak3', 'Owner: the weakest three lose money', 'margin', 'margin.owner_phone', 'Hello {owner_name}, the weakest three clients lose {weak3_gap} a week against the target margin. {company}'),
 M('w_gain', 'Owner: the expected gain from rate rises', 'rises', 'rises.owner_phone', 'Hello {owner_name}, the expected gain from the rate rises is {gain_total} a year. {company}'),
 M('w_churn', 'Owner: churn in a month', 'growth', 'growth.owner_phone', 'Hello {owner_name}, client churn in {month} was {churn_pct} percent. {company}'),
 M('w_hours6', 'Owner: weekly hours in 6 months', 'growth', 'growth.owner_phone', 'Hello {owner_name}, weekly hours are forecast at {hours6} in 6 months. {company}'),
 M('w_marker', 'Owner: months to the hours marker', 'growth', 'growth.owner_phone', 'Hello {owner_name}, weekly hours reach the marker in {months_marker} months at the current pace. {company}'),
 M('w_pay', 'Owner: pay scenario cost and saving', 'payscen', 'payscen.owner_phone', 'Hello {owner_name}, the pay scenario {step} costs {cost_year} a year and saves {saving_year} in turnover. {company}'),
 M('w_service', 'Owner: the service margin of a month', 'svcmonth', 'svcmonth.owner_phone', 'Hello {owner_name}, {service} earned a margin share of {share_pct} percent in {month}. Please review its rate card. {company}'),
 M('w_payer', 'Owner: payer hours against private pay', 'paymonth', 'paymonth.owner_phone', 'Hello {owner_name}, {payer} hours earned {points_behind} points less than private pay in {month}. {company}'),
 M('a_summary', 'Accountant: the client margin summary', 'svcmonth', 'svcmonth.acct_phone', 'Hello {acct_name}, the client margin summary for the year is attached. {company}'),
 M('b_hours', 'Broker: hours forecast attached', 'growth', 'growth.broker_phone', 'Hello {broker_name}, the weekly hours forecast for the insurance estimate is attached: {hours6} hours in 6 months. {company}'),
 M('m_grow', 'Marketing helper: grow a service', 'cmonths', 'cmonths.mkt_phone', 'Hello {mkt_name}, please grow {service} in {area}: clients like this earn a margin share of {share_pct} percent. {company}'),
]
assert len(messages) == 34

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
ACTIVE = tok('clstatus', 'Active')
ACTH = 'SUMIFS({range:clients.weekly_hours},{range:clients.status},%s)' % ACTIVE
THIS_START = '{range:clients.start_date},">="&%s,{range:clients.start_date},"<="&{today}' % MS
THIS_END = '{range:clients.end_date},">="&%s,{range:clients.end_date},"<="&{today}' % MS
kpis = [
 KPI('Margin per client hour, last 90 days', 'IFERROR(SUM({range:margin.margin_week})/SUM({range:margin.weekly_hours}),0)', 'money'),
 KPI('Margin share, last 90 days', 'IFERROR(SUM({range:margin.margin_week})/SUM({range:margin.revenue_week}),0)', 'pct', alert={"when": "< {set:target_margin}", "style": "warn"}),
 KPI('Clients below the target margin', 'COUNTIFS({range:margin.margin_pct},"<"&{set:target_margin})', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Clients below the red margin line', 'COUNTIFS({range:margin.margin_pct},"<"&{set:red_margin})', 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Clients with a negative margin', 'COUNTIFS({range:margin.margin_pct},"<0")', 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Weekly margin lost against the target', 'ROUND(SUM({range:margin.gap_week}),0)', 'money', alert={"when": "> 0", "style": "warn"}),
 KPI('Margin this month', 'SUMIFS({range:svcmonth.margin},{range:svcmonth.month},%s)' % MS, 'money'),
 KPI('Margin share this month', 'IFERROR(SUMIFS({range:svcmonth.margin},{range:svcmonth.month},%s)/SUMIFS({range:svcmonth.revenue},{range:svcmonth.month},%s),0)' % (MS, MS), 'pct', alert={"when": "< {set:target_margin}", "style": "warn"}),
 KPI('Revenue per client hour, last 90 days', 'IFERROR(SUM({range:margin.revenue_week})/SUM({range:margin.weekly_hours}),0)', 'money'),
 KPI('Loaded cost per hour, last 90 days', 'IFERROR((SUM({range:margin.revenue_week})-SUM({range:margin.margin_week}))/SUM({range:margin.weekly_hours}),0)', 'money'),
 KPI('Travel and mileage per client hour', 'IFERROR((SUM({range:otravel.travel_pay})+SUM({range:otravel.mileage_pay}))/SUM({range:otravel.hours}),0)', 'money'),
 KPI('Overtime cost per client hour', 'IFERROR(SUM({range:otravel.overtime_cost})/SUM({range:otravel.hours}),0)', 'money'),
 KPI('Cover premium per client hour', 'IFERROR(SUM({range:otravel.cover_cost})/SUM({range:otravel.hours}),0)', 'money'),
 KPI('Visits at the minimum, last 90 days', 'SUM({range:minvisit.visits_min})', 'int'),
 KPI('Clients losing money on short visits', 'COUNTIFS({range:minvisit.flag},%s)' % ck('Loss on short visits'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Rate rises proposed', 'COUNTIFS({range:rises.rise_pct},">0")', 'int'),
 KPI('Expected gain from rate rises a year', 'ROUND(SUMIFS({range:rises.expected_net},{range:rises.expected_net},">0"),0)', 'money'),
 KPI('Clients on a locked rate', 'COUNTIFS({range:clients.rate_locked},%s,{range:clients.status},%s)' % ('{list:yesno.yes}', ACTIVE), 'int'),
 KPI('Weekly hours now', ACTH, 'num'),
 KPI('Weekly hours 90 days ago', 'SUMIFS({range:clients.weekly_hours},{range:clients.start_date},"<="&({today}-90),{range:clients.status},%s)+SUMIFS({range:clients.weekly_hours},{range:clients.start_date},"<="&({today}-90),{range:clients.end_date},">"&({today}-90))' % ACTIVE, 'num'),
 KPI('Clients started this month', 'COUNTIFS(%s)' % THIS_START, 'int'),
 KPI('Clients ended this month', 'COUNTIFS(%s)' % THIS_END, 'int'),
 KPI('Hours added this month', 'SUMIFS({range:clients.weekly_hours},%s)' % THIS_START, 'num'),
 KPI('Hours lost this month', 'SUMIFS({range:clients.weekly_hours},%s)' % THIS_END, 'num'),
 KPI('Net hours this month', 'SUMIFS({range:clients.weekly_hours},%s)-SUMIFS({range:clients.weekly_hours},%s)' % (THIS_START, THIS_END), 'num', alert={"when": "< 0", "style": "warn"}),
 KPI('Churn rate, last 3 months', 'IFERROR(AVERAGEIFS({range:growth.churn_rate},{range:growth.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:growth.month},"<"&%s),0)' % MS, 'pct', alert={"when": "> {set:churn_limit}", "style": "warn"}),
 KPI('Average tenure of ended clients, months', 'IFERROR(AVERAGE({range:ends.tenure_days})/30.4,0)', 'num'),
 KPI('Forecast weekly hours in 6 months', 'ROUND(SUMIFS({range:forecast.weekly_end},{range:forecast.scenario},%s,{range:forecast.month},DATE(YEAR({today}),MONTH({today})+6,1)),0)' % tok('scen', 'Base'), 'num'),
 KPI('Months to the 1,000-hour marker', 'IFERROR(IF(AVERAGEIFS({range:growth.net_hours},{range:growth.month},">="&DATE(YEAR({today}),MONTH({today})-6,1),{range:growth.month},"<"&%s)<=0,0,MAX(0,ROUNDUP(({set:scheduler_hours}-%s)/AVERAGEIFS({range:growth.net_hours},{range:growth.month},">="&DATE(YEAR({today}),MONTH({today})-6,1),{range:growth.month},"<"&%s),0))),0)' % (MS, ACTH, MS), 'int'),
 KPI('Private pay share of hours', 'IFERROR(SUMIFS({range:clients.weekly_hours},{range:clients.payer},%s,{range:clients.status},%s)/%s,0)' % (tok('payer', 'Private pay'), ACTIVE, ACTH), 'pct'),
]
assert len(kpis) == 30
dashboard = {"title": "Client Margin KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Revenue, cost and margin per month", "date": "svcmonth.month", "series": [
   {"label": "Revenue", "sum": "svcmonth.revenue", "date": "svcmonth.month"}, {"label": "Cost", "sum": "svcmonth.cost", "date": "svcmonth.month"}, {"label": "Margin", "sum": "svcmonth.margin", "date": "svcmonth.month"}]},
 "breakdowns": [{"title": "Clients by payer", "by": "margin.payer", "agg": "count"}, {"title": "Weekly hours by service", "by": "margin.service", "value": "margin.weekly_hours", "agg": "sum"},
                {"title": "Clients ended by reason", "by": "ends.reason", "agg": "count"}, {"title": "Rate rises by risk marker", "by": "rises.risk", "agg": "count"}]}

mw = lambda lo, hi: [('margin_pct', '>=', lo), ('margin_pct', '<', hi)]
insights = {"filters": [{"label": "Service", "list": "svc"}, {"label": "Payer", "list": "payer"}, {"label": "Area", "list": "area"}],
 "gauges": [
  {"title": "Clients at or above the target margin", "num": AGG('count', 'margin', where=[('margin_pct', '>=', '{set:target_margin}')]), "den": AGG('count', 'margin')},
  {"title": "Margin share of revenue (last 90 days)", "num": AGG('sum', 'margin', 'margin.margin_week'), "den": AGG('sum', 'margin', 'margin.revenue_week')},
  {"title": "Net hours growth against hours added", "num": AGG('sum', 'growth', 'growth.net_hours'), "den": AGG('sum', 'growth', 'growth.hours_added')},
  {"title": "Months with churn under the limit", "num": AGG('count', 'growth', where=[('churn_rate', '<=', '{set:churn_limit}')]), "den": AGG('count', 'growth')},
  {"title": "Clients whose short visits pay their way", "num": AGG('count', 'minvisit', where=[('flag', '=', ck('Fine'))]), "den": AGG('count', 'minvisit')},
  {"title": "Rate rises accepted", "num": AGG('count', 'risehist', where=[('outcome', '<>', tok('outcome', 'Left')), ('outcome', '<>', tok('outcome', 'Hours cut'))]), "den": AGG('count', 'risehist')}],
 "charts": [
  CHART('Margin share per month', 'line', 'month', [AGG('avg', 'svcmonth', 'svcmonth.margin_pct', date='svcmonth.month', label='Margin share')]),
  CHART('Margin per month', 'column', 'month', [AGG('sum', 'svcmonth', 'svcmonth.margin', date='svcmonth.month', label='Margin')]),
  CHART('Margin share by service', 'bar', 'svcmonth.service', [AGG('avg', 'svcmonth', 'svcmonth.margin_pct', label='Margin share')]),
  CHART('Margin share by area', 'bar', 'areamonth.area', [AGG('avg', 'areamonth', 'areamonth.margin_pct', label='Margin share')]),
  CHART('Margin share by payer', 'bar', 'paymonth.payer', [AGG('avg', 'paymonth', 'paymonth.margin_pct', label='Margin share')]),
  CHART('Revenue and cost per month', 'column', 'month', [AGG('sum', 'svcmonth', 'svcmonth.revenue', date='svcmonth.month', label='Revenue'), AGG('sum', 'svcmonth', 'svcmonth.cost', date='svcmonth.month', label='Cost')]),
  CHART('Margin per client hour per month', 'line', 'month', [AGG('avg', 'svcmonth', 'svcmonth.margin_hour', date='svcmonth.month', label='Margin per hour')]),
  CHART('Clients by margin band and service', 'stacked', 'margin.service', [AGG('count', 'margin', label='Below the red line', where=[('margin_pct', '<', '{set:red_margin}')]),
        AGG('count', 'margin', label='Between red line and target', where=mw('{set:red_margin}', '{set:target_margin}')), AGG('count', 'margin', label='At or above the target', where=[('margin_pct', '>=', '{set:target_margin}')])]),
  CHART('Overtime cost per month', 'column', 'month', [AGG('sum', 'svcmonth', 'svcmonth.overtime_cost', date='svcmonth.month', label='Overtime cost')]),
  CHART('Travel and mileage cost per month', 'column', 'month', [AGG('sum', 'svcmonth', 'svcmonth.travel_cost', date='svcmonth.month', label='Travel and mileage')]),
  CHART('Weekly hours at month end', 'line', 'month', [AGG('sum', 'growth', 'growth.weekly_hours_end', date='growth.month', label='Weekly hours')]),
  CHART('Hours added and lost per month', 'column', 'month', [AGG('sum', 'growth', 'growth.hours_added', date='growth.month', label='Hours added'), AGG('sum', 'growth', 'growth.hours_lost', date='growth.month', label='Hours lost')]),
  CHART('Net hours per month', 'column', 'month', [AGG('sum', 'growth', 'growth.net_hours', date='growth.month', label='Net hours')]),
  CHART('Clients started per month', 'column', 'month', [AGG('sum', 'growth', 'growth.clients_started', date='growth.month', label='Clients started')]),
  CHART('Clients ended per month', 'column', 'month', [AGG('sum', 'growth', 'growth.clients_ended', date='growth.month', label='Clients ended')]),
  CHART('Churn rate per month', 'line', 'month', [AGG('sum', 'growth', 'growth.churn_rate', date='growth.month', label='Churn rate')]),
  CHART('Clients ended by reason', 'bar', 'ends.reason', [AGG('count', 'ends', label='Clients ended')]),
  CHART('Hours lost by reason', 'bar', 'ends.reason', [AGG('sum', 'ends', 'ends.hours_lost', label='Weekly hours lost')]),
  CHART('Hours by service', 'bar', 'margin.service', [AGG('sum', 'margin', 'margin.weekly_hours', label='Weekly hours')]),
  CHART('Hours by payer', 'bar', 'margin.payer', [AGG('sum', 'margin', 'margin.weekly_hours', label='Weekly hours')]),
  CHART('Hours forecast by scenario', 'line', 'month', [AGG('sum', 'forecast', 'forecast.weekly_end', date='forecast.month', label='Base', where=[('scenario', '=', tok('scen', 'Base'))]),
        AGG('sum', 'forecast', 'forecast.weekly_end', date='forecast.month', label='Best', where=[('scenario', '=', tok('scen', 'Best'))]), AGG('sum', 'forecast', 'forecast.weekly_end', date='forecast.month', label='Worst', where=[('scenario', '=', tok('scen', 'Worst'))])]),
  CHART('Pay scenarios by margin per hour', 'bar', 'payscen.step', [AGG('avg', 'payscen', 'payscen.new_margin_hour', label='Margin per hour after the rise')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Live margin per hour, worst-first list", "why": "every client shows loaded cost (pay, travel, mileage, overtime, cover) against the bill rate, ranked from the weakest", "where": "Client Margin"},
 {"name": "Should I keep this client? verdict", "why": "keep, raise the rate or release, with the rate that reaches your target margin", "where": "Keep This Client"},
 {"name": "Rate needed for the target margin", "why": "a closed-form rate, the rise in money and percent and the rise per week for each client", "where": "Rate for Target"},
 {"name": "Minimum-visit loss check", "why": "hours billed against hours worked plus travel show where short visits lose money and what fixes them", "where": "Minimum Visit Loss"},
 {"name": "Rate-rise planner with the expected net effect", "why": "your risk marker for each client turns a rise into gain if they stay against margin lost if they leave", "where": "Rate Rise Proposals"},
 {"name": "Pay-rate scenario test", "why": "a caregiver pay rise against margin, turnover saved and the bill rate rise clients would need", "where": "Pay Rate Scenario"},
 {"name": "Pay rise against turnover", "why": "the leavers a pay rise must avoid to pay for itself, with the replacement cost from your settings", "where": "Pay Rise vs Turnover"},
 {"name": "Hours growth forecast to 12 months", "why": "your own last six months and a trend factor give weekly hours in 3, 6 and 12 months and the marker month", "where": "Hours Growth Forecast"},
 {"name": "Churn and hours lost by reason", "why": "churn per month against your limit, revenue lost a year and the biggest reason clients leave", "where": "Churn and Hours Lost"},
 {"name": "Service and payer mix margin", "why": "the service to grow, the service to fix and the margin given up to payers against private pay", "where": "Service Mix Margin"},
 {"name": "Rate rise history", "why": "what clients did after each rise (accepted, talked, cut hours or left) so the next rise uses facts", "where": "Rate Rise History"}]
competitors = [
 {"what": "free schedule templates", "lacks": "list visits but never turn them into margin per client hour, so a client billed below cost stays hidden"},
 {"what": "subscription home care software with a per-client fee", "lacks": "charges more as your hours grow and gives no rate-rise planner, minimum-visit loss check or pay-rate scenario test"},
 {"what": "single-sheet time logs", "lacks": "total hours and pay but never compare them with the bill rate, travel, overtime and cover premium of each client"},
 {"what": "generic invoice spreadsheets", "lacks": "show what was billed, not what each client cost, how many hours were won and lost or why clients left"}]
guide = [
 'Open Start here and type your agency name and targets in the yellow cells: margin share, red line, payroll burden (payroll taxes, workers\' insurance and benefits on top of pay; confirm with your adviser), mileage rate, churn limit.',
 'Replace the demo data: type your clients on Clients and Client Margin. Margin is gross margin per hour: the bill rate minus the loaded pay cost. A one-person start-up agency can use Client Margin and Hours Forecast first.',
 'Client Margin shows each client from the last 90 days: bill rate, pay, paid travel, mileage, overtime and cover (another caregiver takes the visit, paid a premium). Loaded cost, margin and a worst-first rank fill in by themselves.',
 'Words used here: a caregiver is a carer, care worker or support worker; the schedule is your rota or roster; a live-in day is a 12-hour day shift in the client\'s home; the holiday rate applies on a bank holiday in your area.',
 'Overtime means hours above the weekly line. Private pay means self-funded clients. A third-party payer is an insurer, a public body or an employer scheme in your area. Check your own contract terms before you change a payer rate.',
 'Use Rate Rise Proposals: type a rise and your risk marker (Low, Medium or High). The expected net effect weighs the gain if the client stays against the margin lost if they leave. Rate Rise History shows what clients did before.',
 'Minimum Visit Check and Overtime and Travel show where short visits, far visits, overtime and cover cost you margin. Use the Minimum Visit Loss tool before you add a travel charge or raise the minimum.',
 'Client Hours Growth, Client Starts, Client Ends and Churn Reasons track hours added and lost. Hours Forecast and the Hours Growth Forecast tool show weekly hours in 3, 6 and 12 months and when you reach the 1,000-hour marker.',
 'Pay Rate Scenarios and the pay tools compare a caregiver pay rise with margin, turnover saved and the bill rate rise clients would need. Caregiver Pay Rates holds the planned new rates.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Why a workbook: one flat price, no per-client or per-caregiver fee, no price rise as hours grow, your data stays with you. No macros, works in Excel and Google Sheets; typed or pasted figures, no live app, GPS or automatic check-in.',
 'Read the Client Margin KPI Dashboard and Charts every week: margin share, clients below the target, expected gain from rate rises, weekly hours, churn and the forecast.']
listing = {"title": "Home Care Agency Excel Template: Client Margin per Hour, Rate Rise Planner, Minimum Visit Check, Churn and Hours Forecast",
 "headline": "Know which clients make money and where your hours are going",
 "tags": ["home care agency", "client margin", "rate card", "excel template", "caregiver pay", "agency management", "rate rise planner", "client churn", "hours forecast", "margin per hour", "minimum visit", "overtime cost", "home care business"],
 "description": ("Find out which clients make money, in one Excel workbook built for a small non-medical home care agency run by an owner-director with a scheduler, an office manager and field supervisors.\n\n"
  "Client Margin shows every active client with the bill rate, caregiver pay, paid travel, mileage, overtime and cover premium of the last 90 days, works out the loaded cost per hour, the margin per hour and per week and the margin share against your target, and ranks the weakest clients first. "
  "Rate Rise Proposals weigh the income gain of a rise against your guess of the chance the client leaves, and Rate Rise History shows what clients did after earlier rises. Minimum Visit Check compares hours billed with hours worked plus travel. "
  "Client Hours Growth, Client Starts, Client Ends and Churn Reasons track hours added and lost, with a forecast of weekly hours in 3, 6 and 12 months and the month you reach the 1,000-hour marker.\n\n"
  f"{len(tools)} decision tools answer the weekly questions with a verdict and a what-if table: should I keep this client, the rate needed for the target margin, rate rise effect, minimum-visit loss, pay-rate scenario, pay rise against turnover, hours forecast, churn, client lifetime value, service and payer mix. "
  f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.\n\n"
  "This is part seven of the Home Care Agency Business suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-client or per-caregiver fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. "
  "It takes typed or pasted figures: there is no live app, no GPS and no automatic check-in, and it holds hours, rates and amounts only, never care notes or health details."),
 "features": ["Live margin per hour, worst-first list", "Keep, raise or release verdict for each client", "Rate rise planner with the expected net effect", "Minimum-visit loss check and travel charge", "Pay-rate scenario test and pay rise against turnover",
              "Hours growth forecast to 12 months", "Churn and hours lost by reason", "Service and payer mix margin", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
              f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
s = _lib.spec(id=f'{SUITE}-p7', slug='home-care-margin', profession='Home Care Agency Business', name='Client Margin and Hours Growth',
         tagline='Know which clients make money and how your hours will grow', price_usd=29, colors={"primary": "#3A506B", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Client margin and hours growth"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hc7.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis),
          'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
