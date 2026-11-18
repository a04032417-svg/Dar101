"""Home care agency suite part 4: Caregiver Payroll and Overtime."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc4_lists import *
from hc4_tables import settings, tables, CA
from hc4_tools import tools
import lib as _lib

SUITE = 'fx-20261115-home-care-agency'
NOTE = "Sample wording: adapt it to your own agency and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
def V(tb, col, idc): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (tb, col, tb, idc)
OT = '{set:overtime_hours}'
THIS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXTM = 'DATE(YEAR({today}),MONTH({today})+1,1)'
def MS(k): return 'DATE(YEAR({today}),MONTH({today})-%d,1)' % k
YEAR0 = 'DATE(YEAR({today}),1,1)'
CUR = '{range:payperiods.period_start},"<="&{today},{range:payperiods.period_end},">="&{today}'
NEXTH = 'SUMPRODUCT(MIN(({range:holidays.date}>={today})*{range:holidays.date}+({range:holidays.date}<{today})*99999))'
def INMONTH(c): return '{range:%s},">="&%s,{range:%s},"<"&%s' % (c, THIS, c, NXTM)
BONUS, DEDUC, OPEN, OVER = ck('Bonus'), ck('Deduction'), ck('Open'), ck('Over the line')

forms = [
 FORM('payline_sheet', 'Pay Line Sheet', 'Pay line of one caregiver in one pay run', 'payrun.pay_id', F(
  ('Period start', 'payrun.period_start'), ('Period end', 'payrun.period_end'), ('Pay date', 'payrun.pay_date'), ('Caregiver', 'payrun.caregiver'), ('Employment', 'payrun.employment'),
  ('Regular hours', 'payrun.regular_hours'), ('Overtime hours', 'payrun.overtime_hours'), ('Holiday hours', 'payrun.holiday_hours'), ('Regular pay', 'payrun.regular_pay'), ('Overtime pay', 'payrun.overtime_pay'),
  ('Holiday premium', 'payrun.holiday_premium'), ('Travel pay', 'payrun.travel_pay'), ('Mileage amount', 'payrun.mileage_pay'), ('Cover premium', 'payrun.cover_premium'), ('Bonus', 'payrun.bonus'),
  ('Deductions', 'payrun.deductions'), ('Gross pay', 'payrun.gross_pay'), ('Net pay', 'payrun.net_pay'), ('Payroll burden', 'payrun.burden'), ('Total cost', 'payrun.total_cost'))),
 FORM('timesheet_sheet', 'Time Sheet Approval Sheet', 'Time sheet approval against check-ins', 'timesheets.sheet_id', F(
  ('Caregiver', 'timesheets.caregiver'), ('Period start', 'timesheets.period_start'), ('Period end', 'timesheets.period_end'), ('Hours entered', 'timesheets.hours_entered'), ('Hours from check-ins', 'timesheets.hours_checkins'),
  ('Difference', 'timesheets.difference'), ('Hours check', 'timesheets.mismatch'), ('Approved by', 'timesheets.approved_by'), ('Approved on', 'timesheets.approved_on'), ('Approval', 'timesheets.approval'),
  ('Send by', 'timesheets.send_by')) + [
  FF('Time sheets of this caregiver', 'COUNTIFS({range:timesheets.caregiver},%s)' % V('timesheets', 'caregiver', 'sheet_id'), 'int'),
  FF('Mismatches of this caregiver', 'COUNTIFS({range:timesheets.caregiver},%s,{range:timesheets.mismatch},%s)' % (V('timesheets', 'caregiver', 'sheet_id'), ck('Mismatch')), 'int')]),
 FORM('otapproval_sheet', 'Overtime Approval Sheet', 'Overtime approval for the week', 'otforecast.caregiver_id', F(
  ('Caregiver', 'otforecast.caregiver'), ('Week starting', 'otforecast.week'), ('Hours worked so far', 'otforecast.worked_so_far'), ('Hours still scheduled', 'otforecast.still_scheduled'), ('Forecast hours', 'otforecast.forecast_hours'),
  ('Hours over the line', 'otforecast.hours_over'), ('Pay rate', 'otforecast.pay_rate'), ('Extra overtime cost', 'otforecast.overtime_cost'), ('Line check', 'otforecast.line_check'), ('Own hours limit', 'otforecast.hours_limit'),
  ('Hours over own limit', 'otforecast.over_limit')) + [
  FF('Moves available for this caregiver', 'COUNTIFS({range:otmoves.from_caregiver},%s,{range:otmoves.verdict},%s,{range:otmoves.visit_date},">="&{today})' % (V('otforecast', 'caregiver', 'caregiver_id'), ck('Move')), 'int'),
  FF('Saving if every move is made', 'SUMIFS({range:otmoves.saving},{range:otmoves.from_caregiver},%s,{range:otmoves.verdict},%s,{range:otmoves.visit_date},">="&{today})' % (V('otforecast', 'caregiver', 'caregiver_id'), ck('Move')), 'money')]),
 FORM('holiday_sheet', 'Holiday Pay Sheet', 'Holiday pay and margin for one holiday', 'holidays.holiday_id', F(
  ('Date', 'holidays.date'), ('Holiday', 'holidays.holiday'), ('Weekday', 'holidays.weekday'), ('Pay multiplier', 'holidays.pay_mult'), ('Bill multiplier', 'holidays.bill_mult'), ('Visits booked', 'holidays.visits_booked'),
  ('Hours booked', 'holidays.hours_booked'), ('Caregivers needed', 'holidays.caregivers_needed'), ('Average weekday pay rate', 'holidays.avg_pay'), ('Average weekday bill rate', 'holidays.avg_bill'),
  ('Extra pay with burden', 'holidays.extra_pay'), ('Extra charge', 'holidays.extra_charge'), ('Margin on the day', 'holidays.holiday_margin'), ('Margin check', 'holidays.margin_flag'),
  ('Days to the holiday', 'holidays.days_to'), ('Caregiver to tell first', 'holidays.notify')) + [
  FF('Extra pay on this holiday, all years', 'SUMIFS({range:holpay.extra_pay},{range:holpay.holiday},%s)' % V('holidays', 'holiday', 'holiday_id'), 'money'),
  FF('Net holiday effect of past years', 'SUMIFS({range:holpay.net_effect},{range:holpay.holiday},%s)' % V('holidays', 'holiday', 'holiday_id'), 'money')]),
 FORM('bonus_sheet', 'Bonus Sheet', 'Bonus of one caregiver with the reason', 'adjust.adjust_id', F(
  ('Caregiver', 'adjust.caregiver'), ('Period start', 'adjust.period_start'), ('Pay date', 'adjust.pay_date'), ('Kind', 'adjust.kind'), ('Amount', 'adjust.amount'), ('Reason', 'adjust.reason'), ('Approved by', 'adjust.approved_by'),
  ('Type', 'adjust.type')) + [
  FF('Bonuses paid to this caregiver, all time', 'SUMIFS({range:adjust.amount},{range:adjust.caregiver},%s,{range:adjust.type},%s)' % (V('adjust', 'caregiver', 'adjust_id'), BONUS), 'money'),
  FF('Bonuses paid to this caregiver this year', 'SUMIFS({range:adjust.amount},{range:adjust.caregiver},%s,{range:adjust.type},%s,{range:adjust.pay_date},">="&%s)' % (V('adjust', 'caregiver', 'adjust_id'), BONUS, YEAR0), 'money'),
  FF('Bonuses paid to all caregivers this year', 'SUMIFS({range:adjust.amount},{range:adjust.type},%s,{range:adjust.pay_date},">="&%s)' % (BONUS, YEAR0), 'money')]),
 FORM('deduction_sheet', 'Deduction Sheet', 'Deductions on one pay line with the net pay', 'payrun.pay_id', F(
  ('Caregiver', 'payrun.caregiver'), ('Period end', 'payrun.period_end'), ('Pay date', 'payrun.pay_date'), ('Gross pay', 'payrun.gross_pay'), ('Deductions', 'payrun.deductions'), ('Net pay', 'payrun.net_pay')) + [
  FF('Deductions as a share of gross pay', 'IFERROR(%s/%s,0)' % (V('payrun', 'deductions', 'pay_id'), V('payrun', 'gross_pay', 'pay_id')), 'pct'),
  FF('Deductions of this caregiver on the page', 'SUMIFS({range:payrun.deductions},{range:payrun.caregiver},%s)' % V('payrun', 'caregiver', 'pay_id'), 'money'),
  FF('Deduction lines of this caregiver', 'COUNTIFS({range:payrun.caregiver},%s,{range:payrun.deductions},">0")' % V('payrun', 'caregiver', 'pay_id'), 'int'),
  FF('Net pay at a quarter-of-gross deduction', 'ROUND(%s-MIN(%s,%s*0.25),2)' % (V('payrun', 'gross_pay', 'pay_id'), V('payrun', 'deductions', 'pay_id'), V('payrun', 'gross_pay', 'pay_id')), 'money')]),
 FORM('mileage_sheet', 'Mileage Pay Sheet', 'Mileage and travel pay of one caregiver', 'travelpay.travel_id', F(
  ('Caregiver', 'travelpay.caregiver'), ('Period start', 'travelpay.period_start'), ('Period end', 'travelpay.period_end'), ('Travel hours', 'travelpay.travel_hours'), ('Travel pay', 'travelpay.travel_pay'),
  ('Kilometres', 'travelpay.distance_km'), ('Mileage amount', 'travelpay.mileage_amount'), ('Travel pay per km', 'travelpay.pay_per_km')) + [
  FF('Mileage at the rate in your settings', 'ROUND(%s*{set:mileage_rate},2)' % V('travelpay', 'distance_km', 'travel_id'), 'money'),
  FF('Difference to the amount paid', 'ROUND(%s-%s*{set:mileage_rate},2)' % (V('travelpay', 'mileage_amount', 'travel_id'), V('travelpay', 'distance_km', 'travel_id')), 'money'),
  FF('Kilometres of this caregiver on the page', 'SUMIFS({range:travelpay.distance_km},{range:travelpay.caregiver},%s)' % V('travelpay', 'caregiver', 'travel_id'), 'num')]),
 FORM('correction_sheet', 'Pay Correction Sheet', 'Pay correction after a warning', 'warnings.warning_id', F(
  ('Caregiver', 'warnings.caregiver'), ('Period start', 'warnings.period_start'), ('Period end', 'warnings.period_end'), ('Kind', 'warnings.kind'), ('Detail', 'warnings.detail'), ('Visit date', 'warnings.visit_date'),
  ('Found on', 'warnings.found_on'), ('Fixed on', 'warnings.fixed_on'), ('Open or fixed', 'warnings.status'), ('Days open', 'warnings.days_open'), ('Scheduler', 'warnings.scheduler'), ('Office manager', 'warnings.office_manager')) + [
  FF('Warnings of this caregiver, all pay runs', 'COUNTIFS({range:warnings.caregiver},%s)' % V('warnings', 'caregiver', 'warning_id'), 'int'),
  FF('Open warnings of this kind', 'COUNTIFS({range:warnings.kind},%s,{range:warnings.status},%s)' % (V('warnings', 'kind', 'warning_id'), OPEN), 'int')]),
 FORM('ratechange_sheet', 'Pay Rate Change Sheet', 'Pay rate change of one caregiver', 'raises.change_id', F(
  ('Caregiver', 'raises.caregiver'), ('Effective date', 'raises.date'), ('Old rate', 'raises.old_rate'), ('New rate', 'raises.new_rate'), ('Rise per hour', 'raises.rise_amount'), ('Rise share', 'raises.rise_share'), ('Reason', 'raises.reason')) + [
  FF('Pay rate changes of this caregiver', 'COUNTIFS({range:raises.caregiver},%s)' % V('raises', 'caregiver', 'change_id'), 'int'),
  FF('Average pay rate of active caregivers', 'IFERROR(AVERAGEIFS({range:caregivers.pay_rate},{range:caregivers.status},%s),0)' % tok('cgstatus', 'Active'), 'money'),
  FF('New rate against that average', 'ROUND(%s-IFERROR(AVERAGEIFS({range:caregivers.pay_rate},{range:caregivers.status},%s),0),2)' % (V('raises', 'new_rate', 'change_id'), tok('cgstatus', 'Active')), 'money'),
  FF('Rise over 1,000 hours, with burden', 'ROUND(%s*1000*(1+{set:payroll_burden}),2)' % V('raises', 'rise_amount', 'change_id'), 'money')]),
 FORM('precheck_sheet', 'Pre-Payroll Check Sheet', 'Pre-payroll check for one pay period', 'payperiods.period_id', F(
  ('Period start', 'payperiods.period_start'), ('Period end', 'payperiods.period_end'), ('Pay date', 'payperiods.pay_date'), ('Status', 'payperiods.status'), ('Paid hours', 'payperiods.hours'), ('Total cost', 'payperiods.total_cost'),
  ('Caregivers paid', 'payperiods.caregivers_paid'), ('Open warnings', 'payperiods.open_warnings'), ('Days to pay date', 'payperiods.days_to_pay'), ('Approve by', 'payperiods.approve_by')) + [
  FF('Time sheets awaiting approval', 'COUNTIFS({range:timesheets.period_end},%s,{range:timesheets.approval},%s)' % (V('payperiods', 'period_end', 'period_id'), ck('Awaiting approval')), 'int'),
  FF('Time sheets with a mismatch', 'COUNTIFS({range:timesheets.period_end},%s,{range:timesheets.mismatch},%s)' % (V('payperiods', 'period_end', 'period_id'), ck('Mismatch')), 'int'),
  FF('Missing check-outs still open', 'COUNTIFS({range:warnings.period_end},%s,{range:warnings.kind},%s,{range:warnings.status},%s)' % (V('payperiods', 'period_end', 'period_id'), tok('wkind', 'Missing check-out'), OPEN), 'int'),
  FF('Pay lines over the overtime line', 'COUNTIFS({range:payrun.period_end},%s,{range:payrun.overtime_hours},">0")' % V('payperiods', 'period_end', 'period_id'), 'int')]),
 FORM('signoff_sheet', 'Pay Run Sign-off Sheet', 'Pay run sign-off with totals and hours check', 'payperiods.period_id', F(
  ('Period start', 'payperiods.period_start'), ('Period end', 'payperiods.period_end'), ('Pay date', 'payperiods.pay_date'), ('Paid hours', 'payperiods.hours'), ('Hours billed', 'payperiods.billed_hours'),
  ('Paid minus billed hours', 'payperiods.hours_gap'), ('Total cost', 'payperiods.total_cost'), ('Cost per paid hour', 'payperiods.cost_per_hour'), ('Travel pay', 'payperiods.travel_pay'), ('Mileage amount', 'payperiods.mileage_amount'),
  ('Cover premium', 'payperiods.cover_premium'), ('Caregivers paid', 'payperiods.caregivers_paid')) + [
  FF('Net pay in this run', 'SUMIFS({range:payrun.net_pay},{range:payrun.period_end},%s)' % V('payperiods', 'period_end', 'period_id'), 'money'),
  FF('Payroll burden in this run', 'SUMIFS({range:payrun.burden},{range:payrun.period_end},%s)' % V('payperiods', 'period_end', 'period_id'), 'money'),
  FF('Overtime pay in this run', 'SUMIFS({range:payrun.overtime_pay},{range:payrun.period_end},%s)' % V('payperiods', 'period_end', 'period_id'), 'money'),
  FF('Cash floor in your settings', '{set:cash_floor}', 'money')]),
 FORM('query_sheet', 'Payroll Query Sheet', 'Payroll query: one caregiver week of hours', 'hoursweek.row_id', F(
  ('Caregiver', 'hoursweek.caregiver'), ('Week starting', 'hoursweek.week'), ('Scheduled hours', 'hoursweek.scheduled_hours'), ('Worked hours', 'hoursweek.worked_hours'), ('Travel hours', 'hoursweek.travel_hours'),
  ('Overtime hours', 'hoursweek.overtime_hours'), ('Visits', 'hoursweek.visits'), ('Total paid hours', 'hoursweek.total_paid'), ('Paid minus scheduled', 'hoursweek.vs_schedule')) + [
  FF('Pay rate of this caregiver', 'IFERROR(INDEX({range:caregivers.pay_rate},MATCH(%s,{range:caregivers.name},0)),0)' % V('hoursweek', 'caregiver', 'row_id'), 'money'),
  FF('Value of the paid hours at that rate', 'ROUND(%s*IFERROR(INDEX({range:caregivers.pay_rate},MATCH(%s,{range:caregivers.name},0)),0),2)' % (V('hoursweek', 'total_paid', 'row_id'), V('hoursweek', 'caregiver', 'row_id')), 'money'),
  FF('Overtime hours of this caregiver', 'SUMIFS({range:hoursweek.overtime_hours},{range:hoursweek.caregiver},%s)' % V('hoursweek', 'caregiver', 'row_id'), 'num'),
  FF('Weeks of this caregiver on the page', 'COUNTIFS({range:hoursweek.caregiver},%s)' % V('hoursweek', 'caregiver', 'row_id'), 'int')]),
]
def _fix(form, col, label, fmt):
    for i, f in enumerate(form['fields']):
        if f.get('value') == col:
            tb, c = col.split('.'); idc = {'payrun': 'pay_id', 'hoursweek': 'row_id'}[tb]
            form['fields'][i] = {'label': f['label'], 'formula': V(tb, c, idc) + '+0', 'format': fmt}
for _f in forms:
    if _f['key'] == 'payline_sheet': _fix(_f, 'payrun.bonus', 'Bonus', 'num')
    if _f['key'] == 'query_sheet': _fix(_f, 'hoursweek.travel_hours', 'Travel hours', 'num'); _fix(_f, 'hoursweek.overtime_hours', 'Overtime hours', 'num')
assert len(forms) == 12

def D_(k, sheet, title, pick, paras, sign): return DOC(k, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('pay_statement', 'Pay Statement', 'Pay statement for one caregiver and pay run', 'payrun.pay_id', [
  'Pay statement of {set:company}, dated {today}. Caregiver: {col:payrun.caregiver} ({col:payrun.employment}). Pay period {col:payrun.period_start} to {col:payrun.period_end}, paid on {col:payrun.pay_date}.',
  'Hours: regular {col:payrun.regular_hours}, overtime {col:payrun.overtime_hours} (hours above {set:overtime_hours} a week), holiday {col:payrun.holiday_hours}, paid travel {col:payrun.travel_hours}. Distance: {col:payrun.distance_km} km.',
  'Pay: regular pay {col:payrun.regular_pay}, overtime pay {col:payrun.overtime_pay}, holiday premium {col:payrun.holiday_premium}, travel pay {col:payrun.travel_pay}, mileage {col:payrun.mileage_pay}, cover premium {col:payrun.cover_premium}, bonus {col:payrun.bonus}.',
  'Gross pay {col:payrun.gross_pay}. Deductions {col:payrun.deductions}. Net pay {col:payrun.net_pay}.',
  'These figures are prepared for the payroll service. Taxes and other deductions that your local rules require are handled there: confirm with your adviser. If something looks wrong, tell the office within 7 days.'], ['Office manager', 'Caregiver']),
 D_('runsummary', 'Pay Run Summary', 'Pay run summary for the payroll service', 'payperiods.period_id', [
  'Pay run summary of {set:company}, dated {today}, for the payroll service. Pay period {col:payperiods.period_start} to {col:payperiods.period_end}, pay date {col:payperiods.pay_date}. Status: {col:payperiods.status}.',
  'Caregivers paid: {col:payperiods.caregivers_paid}. Paid hours: {col:payperiods.hours}. Hours billed to clients: {col:payperiods.billed_hours}. Paid minus billed hours: {col:payperiods.hours_gap}.',
  'Total cost with burden: {col:payperiods.total_cost}, or {col:payperiods.cost_per_hour} per paid hour. Travel pay {col:payperiods.travel_pay}, mileage {col:payperiods.mileage_amount}, cover premium {col:payperiods.cover_premium}.',
  'Open pre-payroll warnings: {col:payperiods.open_warnings}. Please approve by {col:payperiods.approve_by}. The pay lines are attached in the pay run file; confirm taxes and deductions with your adviser.'], ['Office manager', 'Owner']),
 D_('overtime_report', 'Overtime Report', 'Overtime report for one month', 'otmonth.row_id', [
  'Overtime report of {set:company}, dated {today}. Month: {col:otmonth.month}.',
  'Paid hours: {col:otmonth.hours}. Overtime hours: {col:otmonth.overtime_hours} by {col:otmonth.caregivers_ot} caregivers. Overtime pay: {col:otmonth.overtime_pay}, or {col:otmonth.pay_per_hour} per overtime hour.',
  'Overtime share of paid hours: {col:otmonth.overtime_share}. Target: {set:overtime_share_target}. Check: {col:otmonth.share_check}.',
  'Decisions for the scheduler: which visits to move, which caregivers to cover for, and whether the overtime line of {set:overtime_hours} hours still suits the agency.'], ['Scheduler', 'Owner']),
 D_('holiday_notice', 'Holiday Pay Notice', 'Holiday pay notice to caregivers', 'holidays.holiday_id', [
  'Holiday pay notice of {set:company}, dated {today}. Dear team,',
  'On {col:holidays.date} ({col:holidays.weekday}) it is {col:holidays.holiday}. Visits on that day are paid at {col:holidays.pay_mult} times your normal pay rate (the holiday rate, also called a bank holiday rate).',
  'We expect {col:holidays.visits_booked} visits and {col:holidays.hours_booked} hours, so we need about {col:holidays.caregivers_needed} caregivers. Please tell the scheduler if you can work.',
  'Your pay statement will show the holiday premium on its own line. If you have questions, call the office. Check your own local rules for anything not covered here.'], ['Care coordinator']),
 D_('ratechange_letter', 'Pay Rate Change Letter', 'Pay rate change letter', 'raises.change_id', [
  'Pay rate change letter of {set:company}, dated {today}. Dear {col:raises.caregiver},',
  'From {col:raises.date} your pay rate changes from {col:raises.old_rate} to {col:raises.new_rate} per hour, a rise of {col:raises.rise_amount} per hour ({col:raises.rise_share}). Reason: {col:raises.reason}.',
  'The new rate applies to hours worked from that date. Overtime and holiday pay use the new rate. This letter does not change any other term of your contract; confirm contract terms with your adviser.'], ['Owner', 'Caregiver']),
 D_('bonus_letter', 'Bonus Letter', 'Bonus letter', 'adjust.adjust_id', [
  'Bonus letter of {set:company}, dated {today}. Dear {col:adjust.caregiver},',
  'Thank you. We are pleased to pay you a bonus of {col:adjust.amount} ({col:adjust.kind}) with your pay on {col:adjust.pay_date}. Reason: {col:adjust.reason}.',
  'Approved by {col:adjust.approved_by}. Taxes on a bonus are handled by the payroll service; confirm with your adviser.'], ['Owner']),
 D_('mileage_statement', 'Mileage Statement', 'Mileage statement for one caregiver and period', 'travelpay.travel_id', [
  'Mileage statement of {set:company}, dated {today}. Caregiver: {col:travelpay.caregiver}. Period {col:travelpay.period_start} to {col:travelpay.period_end}.',
  'Paid travel time between visits: {col:travelpay.travel_hours} hours, paid {col:travelpay.travel_pay}. Distance driven: {col:travelpay.distance_km} km at {set:mileage_rate} per km, paid {col:travelpay.mileage_amount}.',
  'All-in travel pay per km: {col:travelpay.pay_per_km}. Please report any trip that is missing. If you prefer miles, use your own rate per mile.'], ['Office manager', 'Caregiver']),
 D_('cost_report', 'Payroll Cost Report', 'Payroll cost report for one month', 'payratio.row_id', [
  'Payroll cost report of {set:company}, dated {today}. Month: {col:payratio.month}.',
  'Revenue {col:payratio.revenue} from {col:payratio.billed_hours} billed hours. Caregiver pay {col:payratio.caregiver_pay}, overtime pay {col:payratio.overtime_pay}, travel and mileage {col:payratio.travel_mileage}, payroll burden {col:payratio.burden}.',
  'Total pay cost {col:payratio.total_pay_cost}, or {col:payratio.cost_per_hour} per billed hour. Ratio to revenue: {col:payratio.ratio}. Ceiling: {set:payroll_ratio_ceiling}. Check: {col:payratio.ceiling_check}. Room under the ceiling: {col:payratio.room}.',
  'Actions for the owner and the office manager are written below.'], ['Owner', 'Office manager']),
 D_('warning_list', 'Pre-payroll Warning List', 'Pre-payroll warning list for one pay period', 'payperiods.period_id', [
  'Pre-payroll warning list of {set:company}, dated {today}. Pay period {col:payperiods.period_start} to {col:payperiods.period_end}, pay date {col:payperiods.pay_date}.',
  'Open warnings: {col:payperiods.open_warnings}. Paid hours {col:payperiods.hours} against {col:payperiods.billed_hours} billed (difference {col:payperiods.hours_gap}).',
  'Write each open warning below with the caregiver, the kind (overtime near the line, missing check-out, negative net pay, hours mismatch, missing time sheet, rate not set) and who fixes it by {col:payperiods.approve_by}.',
  '1. ______________________   2. ______________________   3. ______________________   4. ______________________'], ['Office manager', 'Scheduler']),
 D_('holiday_rates', 'Holiday Rates Notice', 'Holiday rates notice to clients', 'holidays.holiday_id', [
  'Holiday rates notice of {set:company}, dated {today}. Dear client,',
  'Visits on {col:holidays.date} ({col:holidays.holiday}) are charged at {col:holidays.bill_mult} times the normal rate for the time band. This is the holiday rate and it is written in your service agreement.',
  'If you want to move a visit to another day, please tell us as early as you can. Rates are before any tax. We will confirm your visit times in advance.'], ['Care coordinator']),
 D_('correction_note', 'Payroll Correction Note', 'Payroll correction note for one time sheet', 'timesheets.sheet_id', [
  'Payroll correction note of {set:company}, dated {today}. Caregiver: {col:timesheets.caregiver}. Pay period {col:timesheets.period_start} to {col:timesheets.period_end}.',
  'Hours entered on the time sheet: {col:timesheets.hours_entered}. Hours from check-ins: {col:timesheets.hours_checkins}. Difference: {col:timesheets.difference} hours. Check: {col:timesheets.mismatch}.',
  'Corrected hours to pay: ____________. The correction is paid in the next pay run. Approved by {col:timesheets.approved_by} on {col:timesheets.approved_on}. Approval status: {col:timesheets.approval}.'], ['Office manager', 'Caregiver']),
 D_('yearend_summary', 'Year-end Pay Summary', 'Year-end pay summary line for the accountant', 'burden.row_id', [
  'Pay summary for the accountant from {set:company}, dated {today}. Month: {col:burden.month}. Use one copy per month and add the months up for the year.',
  'Pay base: {col:burden.pay_base}. Payroll taxes {col:burden.payroll_taxes}, workers insurance {col:burden.workers_insurance}, benefits {col:burden.benefits}. Total burden {col:burden.total_burden}, which is {col:burden.burden_share} of the pay base.',
  'This is an example split prepared from the pay runs. Confirm every figure and the rules for your own area with your adviser.'], ['Office manager', 'Accountant']),
]
assert len(documents) == 12

def CS(k, title, table, start, steps): return _lib.CHK(k, title, table, start, steps)
checklists = [
 CS('c_monday', 'Monday Pre-payroll Check', 'payperiods', 'payperiods.period_end', [('Export check-in times for the period', 1), ('Compare hours entered with hours from check-ins', 1), ('List visits with no check-out', 1), ('Fix or chase every open warning', 2), ('Look for negative net pay', 2), ('Mark the period ready or not ready', 3)]),
 CS('c_prep', 'Pay Run Preparation', 'payperiods', 'payperiods.period_end', [('Close the period and lock the hours', 1), ('Add bonuses and deductions with the reason', 2), ('Add travel time and mileage', 2), ('Check holiday and overtime lines', 3), ('Total the run and compare hours paid with hours billed', 3), ('Send the file to the payroll service', 4), ('Ask the owner to approve the total', 4)]),
 CS('c_timesheet', 'Time Sheet Approval', 'timesheets', 'timesheets.period_end', [('Collect every time sheet', 2), ('Compare each with the check-in hours', 3), ('Approve sheets within the allowed difference', 3), ('Ask for a correction on the others', 4), ('Record who approved and when', 4)]),
 CS('c_wednesday', 'Wednesday Overtime Review', 'otforecast', 'otforecast.week', [('Update hours worked so far', 2), ('Forecast the week for every caregiver', 2), ('List caregivers near or over the line', 2), ('Choose visits to move and to whom', 2), ('Call the caregivers about the changes', 3), ('Approve any overtime that stays', 3)]),
 CS('c_holiday', 'Holiday Pay Set-up', 'holidays', 'holidays.date', [('Set the pay and bill multipliers', -45), ('Count booked visits and hours', -30), ('Check the margin on the day', -30), ('Ask caregivers who can work', -21), ('Send the holiday pay notice', -21), ('Send the holiday rates notice to clients', -14), ('Confirm cover for open visits', -7)]),
 CS('c_mileage', 'Mileage and Travel Check', 'travelpay', 'travelpay.period_end', [('Collect kilometres for the period', 1), ('Check unusual trips', 2), ('Apply the rate per km', 2), ('Check paid travel time between visits', 3), ('Send the mileage list to the payroll service', 4)]),
 CS('c_adjust', 'Bonus and Deduction Check', 'adjust', 'adjust.pay_date', [('Check the reason for every bonus', -6), ('Check the reason and the note for every deduction', -6), ('Confirm the approver', -5), ('Check the limit on deductions; check your own local rules', -5), ('Tell each caregiver before pay day', -3)]),
 CS('c_correction', 'Pay Correction', 'warnings', 'warnings.found_on', [('Write down what is wrong', 0), ('Find the visit or time sheet', 1), ('Work out the difference', 1), ('Approve the correction', 2), ('Add it to the next pay run', 3), ('Tell the caregiver', 3), ('Mark the warning fixed', 4)]),
 CS('c_rates', 'Yearly Pay Rate Review', 'raises', 'raises.date', [('List current pay rates by caregiver', -30), ('Compare with the pay rate card and the market', -21), ('Check the cost of each rise with burden', -14), ('Decide the new rates', -7), ('Send the pay rate change letters', -3), ('Update the pay rate card', 0)]),
 CS('c_sent', 'Payroll Sent to Payroll Service', 'payperiods', 'payperiods.pay_date', [('Send the pay run file', -6), ('Confirm the file was received', -5), ('Check the funding of the pay run', -4), ('Approve the final totals', -3), ('Confirm the pay date with the payroll service', -2), ('Send pay statements to caregivers', 0)]),
 CS('c_monthend', 'Month-end Payroll Cost Check', 'payratio', 'payratio.month', [('Total the pay lines for the month', 32), ('Compare pay cost with revenue', 33), ('Check the ratio against the ceiling', 33), ('Look at overtime and cover premium', 34), ('Write actions for next month', 35)]),
 CS('c_yearend', 'Year-end Pay Pack Accountant', 'burden', 'burden.month', [('Collect the monthly pay summaries', 35), ('Check payroll taxes, workers insurance and benefits', 40), ('List bonuses and deductions of the year', 40), ('Add pay rate changes', 42), ('Send the pack and keep a copy', 45), ('Ask which figures need your adviser; check your own local rules', 45)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('c_pay', 'Caregiver: your pay is ready', 'payrun', 'payrun.phone', 'Hello {caregiver}, your pay for {period_start} to {period_end} is {net_pay} and is paid on {pay_date}. {company}'),
 M('c_sheet', 'Caregiver: time sheet is missing', 'timesheets', 'timesheets.phone', 'Hello {caregiver}, your time sheet for {period_start} to {period_end} is missing. Please send it by {send_by}. {company}'),
 M('c_near', 'Caregiver: near the overtime line', 'otforecast', 'otforecast.phone', 'Hello {caregiver}, you are forecast at {forecast_hours} hours in the week of {week}, near the overtime line. Please talk to the scheduler before you accept more visits. {company}'),
 M('c_otyes', 'Caregiver: overtime is approved', 'otforecast', 'otforecast.phone', 'Hello {caregiver}, overtime is approved for the week of {week} ({forecast_hours} hours). {company}'),
 M('c_otno', 'Caregiver: overtime is not approved', 'otforecast', 'otforecast.phone', 'Hello {caregiver}, extra hours above the line in the week of {week} are not approved. Please call {scheduler} before you accept more visits. {company}'),
 M('c_holiday', 'Caregiver: holiday pay applies', 'holidays', 'holidays.phone', 'Hello {notify}, holiday pay at {pay_mult} times applies on {holiday} ({date}). {company}'),
 M('c_mile', 'Caregiver: mileage added to pay', 'travelpay', 'travelpay.phone', 'Hello {caregiver}, your mileage of {distance_km} km ({mileage_amount}) for {period_start} to {period_end} is added to your pay. {company}'),
 M('c_bonus', 'Caregiver: a bonus in your pay', 'adjust', 'adjust.phone', 'Hello {caregiver}, your pay on {pay_date} includes a bonus of {amount}. Thank you. {company}'),
 M('c_deduct', 'Caregiver: a deduction is taken', 'adjust', 'adjust.phone', 'Hello {caregiver}, a deduction of {amount} ({kind}) is taken from your pay on {pay_date}. The note is attached. {company}'),
 M('c_fixed', 'Caregiver: your hours were corrected', 'warnings', 'warnings.phone', 'Hello {caregiver}, we corrected your hours for {period_start} to {period_end}. The difference is in the next pay run. {company}'),
 M('c_checkout', 'Caregiver: check-out is missing', 'warnings', 'warnings.phone', 'Hello {caregiver}, your check-out is missing for the visit on {visit_date}. Please send the time today. {company}'),
 M('c_rate', 'Caregiver: your pay rate changes', 'raises', 'raises.phone', 'Hello {caregiver}, your pay rate is {new_rate} per hour from {date}. {company}'),
 M('c_stmt', 'Caregiver: pay statement is ready', 'payrun', 'payrun.phone', 'Hello {caregiver}, your pay statement for the period ending {period_end} is ready. {company}'),
 M('c_bank', 'Caregiver: confirm your payment details', 'payrun', 'payrun.phone', 'Hello {caregiver}, please confirm your payment details with the office before the pay run on {pay_date}. Do not send them in a group chat. {company}'),
 M('c_hschedule', 'Caregiver: holiday schedule and pay', 'holidays', 'holidays.phone', 'Hello {notify}, the schedule for {holiday} on {date} is attached. Holiday pay is {pay_mult} times your pay rate. {company}'),
 M('s_ot', 'Scheduler: a caregiver reaches overtime', 'otforecast', 'otforecast.scheduler_phone', 'Hello {scheduler}, {caregiver} is forecast at {forecast_hours} hours in the week of {week}, {hours_over} over the line. Please move a visit. {company}'),
 M('s_month', 'Scheduler: overtime of the month', 'otmonth', 'otmonth.scheduler_phone', 'Hello {scheduler}, overtime in {month} was {overtime_hours} hours, {overtime_share} of paid hours. {company}'),
 M('s_checkout', 'Scheduler: fix missing check-outs', 'warnings', 'warnings.scheduler_phone', 'Hello {scheduler}, please fix the missing check-out of {caregiver} for {visit_date} before Monday. {company}'),
 M('s_holiday', 'Scheduler: holiday needs caregivers', 'holidays', 'holidays.scheduler_phone', 'Hello {scheduler}, {holiday} on {date} has {visits_booked} visits and needs about {caregivers_needed} caregivers. {company}'),
 M('o_open', 'Office manager: warnings still open', 'payperiods', 'payperiods.office_manager_phone', 'Hello {office_manager}, {open_warnings} pre-payroll warnings are still open for the period ending {period_end}. {company}'),
 M('o_total', 'Office manager: pay run total', 'payperiods', 'payperiods.office_manager_phone', 'Hello {office_manager}, the pay run total is {total_cost}. Please approve by {approve_by} (pay date {pay_date}). {company}'),
 M('o_gap', 'Office manager: paid above billed hours', 'payperiods', 'payperiods.office_manager_phone', 'Hello {office_manager}, hours paid are above hours billed by {hours_gap} in the period ending {period_end}. Please check. {company}'),
 M('o_ratio', 'Office manager: cost ratio above ceiling', 'payratio', 'payratio.office_manager_phone', 'Hello {office_manager}, the payroll cost ratio for {month} is {ratio}, above the ceiling. {company}'),
 M('o_neg', 'Office manager: negative net pay', 'warnings', 'warnings.office_manager_phone', 'Hello {office_manager}, a negative net pay needs fixing for {caregiver} (period ending {period_end}). {company}'),
 M('w_approve', 'Owner: please approve the pay run', 'payperiods', 'payperiods.owner_phone', 'Hello {owner}, please approve the pay run of {total_cost} for the period ending {period_end}. {company}'),
 M('w_ot', 'Owner: overtime cost of the month', 'otmonth', 'otmonth.owner_phone', 'Hello {owner}, overtime pay in {month} was {overtime_pay} for {overtime_hours} hours. {company}'),
 M('w_holiday', 'Owner: holiday margin check', 'holidays', 'holidays.owner_phone', 'Hello {owner}, {holiday} on {date}: forecast margin {holiday_margin} at {pay_mult} times pay and {bill_mult} times charge. {company}'),
 M('w_cph', 'Owner: payroll cost per hour', 'payperiods', 'payperiods.owner_phone', 'Hello {owner}, payroll cost per paid hour is {cost_per_hour} for the period ending {period_end}. {company}'),
 M('w_rates', 'Owner: pay rate change to review', 'raises', 'raises.owner_phone', 'Hello {owner}, the pay rate change for {caregiver} ({old_rate} to {new_rate}, from {date}) is ready to review. {company}'),
 M('p_file', 'Payroll service: pay run file', 'payperiods', 'payperiods.payroll_service_phone', 'Hello {payroll_service}, the pay run file for the period ending {period_end} is attached. Pay date {pay_date}. {company}'),
 M('p_hours', 'Payroll service: please correct hours', 'timesheets', 'timesheets.payroll_service_phone', 'Hello {payroll_service}, please correct the hours for {caregiver} ({period_start} to {period_end}): {hours_checkins} hours from check-ins. {company}'),
 M('p_mile', 'Payroll service: mileage list', 'travelpay', 'travelpay.payroll_service_phone', 'Hello {payroll_service}, the mileage list for {period_start} to {period_end} is attached ({distance_km} km for {caregiver}). {company}'),
 M('a_year', 'Accountant: pay summary is ready', 'payratio', 'payratio.accountant_phone', 'Hello {accountant}, the pay summary up to {month} is ready: total pay cost {total_pay_cost}. {company}'),
 M('b_total', 'Insurance broker: payroll total', 'burden', 'burden.broker_phone', 'Hello {broker}, the payroll total for the workers insurance estimate is {pay_base} for {month}. {company}'),
]
assert len(messages) == 34

def W_(c, o, v): return (c, o, v)
kpis = [
 KPI('Pay run total this period, so far', 'SUMIFS({range:payperiods.total_cost},%s)' % CUR, 'money'),
 KPI('Pay run due next', 'SUMIFS({range:payperiods.total_cost},{range:payperiods.status},%s)' % tok('paystat', 'Due'), 'money'),
 KPI('Days to the next pay date', 'SUMPRODUCT(MIN(({range:payperiods.pay_date}>={today})*{range:payperiods.pay_date}+({range:payperiods.pay_date}<{today})*99999))-{today}', 'int'),
 KPI('Paid hours this pay period, so far', 'SUMIFS({range:payperiods.hours},%s)' % CUR, 'num'),
 KPI('Overtime hours this period', 'SUMIFS({range:payrun.overtime_hours},{range:payrun.period_start},"<="&{today},{range:payrun.period_end},">="&{today})', 'num'),
 KPI('Overtime pay this period', 'SUMIFS({range:payrun.overtime_pay},{range:payrun.period_start},"<="&{today},{range:payrun.period_end},">="&{today})', 'money'),
 KPI('Overtime share, last 4 weeks', 'IFERROR(SUMIFS({range:payrun.overtime_hours},{range:payrun.period_end},">="&({today}-28),{range:payrun.period_end},"<="&{today})/(SUMIFS({range:payrun.overtime_hours},{range:payrun.period_end},">="&({today}-28),{range:payrun.period_end},"<="&{today})+SUMIFS({range:payrun.regular_hours},{range:payrun.period_end},">="&({today}-28),{range:payrun.period_end},"<="&{today})),0)', 'pct', alert={"when": "> {set:overtime_share_target}", "style": "warn"}),
 KPI('Caregivers forecast over the line', 'COUNTIFS({range:otforecast.line_check},%s)' % OVER, 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Forecast overtime cost this week', 'SUM({range:otforecast.overtime_cost})', 'money'),
 KPI('Overtime moves available this week', 'COUNTIFS({range:otmoves.verdict},%s,{range:otmoves.visit_date},">="&{today})' % ck('Move'), 'int'),
 KPI('Holiday premium paid this year', 'SUMIFS({range:holpay.extra_pay},{range:holpay.date},">="&%s)' % YEAR0, 'money'),
 KPI('Holiday premium paid last holiday', 'SUMIFS({range:holpay.extra_pay},{range:holpay.date},MAX({range:holpay.date}))', 'money'),
 KPI('Next holiday in days', NEXTH + '-{today}', 'int'),
 KPI('Visits booked on the next holiday', 'SUMIFS({range:holidays.visits_booked},{range:holidays.date},%s)' % NEXTH, 'int'),
 KPI('Forecast margin on the next holiday', 'SUMIFS({range:holidays.holiday_margin},{range:holidays.date},%s)' % NEXTH, 'money'),
 KPI('Travel pay this month', 'SUMIFS({range:payperiods.travel_pay},%s)' % INMONTH('payperiods.pay_date'), 'money'),
 KPI('Mileage paid this month', 'SUMIFS({range:payperiods.mileage_amount},%s)' % INMONTH('payperiods.pay_date'), 'money'),
 KPI('Cover premium paid this month', 'SUMIFS({range:payperiods.cover_premium},%s)' % INMONTH('payperiods.pay_date'), 'money'),
 KPI('Bonuses paid this year', 'SUMIFS({range:adjust.amount},{range:adjust.type},%s,{range:adjust.pay_date},">="&%s)' % (BONUS, YEAR0), 'money'),
 KPI('Deductions this month', 'SUMIFS({range:adjust.amount},{range:adjust.type},%s,%s)' % (DEDUC, INMONTH('adjust.pay_date')), 'money'),
 KPI('Payroll burden this month', 'SUMIFS({range:burden.total_burden},{range:burden.month},%s)' % THIS, 'money'),
 KPI('Payroll cost this month', 'SUMIFS({range:payratio.total_pay_cost},{range:payratio.month},%s)' % THIS, 'money'),
 KPI('Payroll cost ratio this month', 'SUMIFS({range:payratio.ratio},{range:payratio.month},%s)' % THIS, 'pct', alert={"when": "> {set:payroll_ratio_ceiling}", "style": "warn"}),
 KPI('Payroll cost ratio, last 3 months', 'IFERROR(SUMIFS({range:payratio.total_pay_cost},{range:payratio.month},">="&%s,{range:payratio.month},"<"&%s)/SUMIFS({range:payratio.revenue},{range:payratio.month},">="&%s,{range:payratio.month},"<"&%s),0)' % (MS(3), THIS, MS(3), THIS), 'pct', alert={"when": "> {set:payroll_ratio_ceiling}", "style": "warn"}),
 KPI('Months over the ceiling, last 12', 'COUNTIFS({range:payratio.ceiling_check},%s,{range:payratio.month},">="&%s,{range:payratio.month},"<"&%s)+COUNTIFS({range:payratio.ceiling_check},%s,{range:payratio.month},">="&%s,{range:payratio.month},"<"&%s)' % (ck('Over ceiling'), MS(12), THIS, ck('Near ceiling'), MS(12), THIS), 'int'),
 KPI('Payroll cost per paid hour this month', 'IFERROR(SUMIFS({range:payperiods.total_cost},%s)/SUMIFS({range:payperiods.hours},%s),0)' % (INMONTH('payperiods.pay_date'), INMONTH('payperiods.pay_date')), 'money'),
 KPI('Pre-payroll warnings open', 'COUNTIFS({range:warnings.status},%s)' % OPEN, 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Time sheets awaiting approval', 'COUNTIFS({range:timesheets.approval},%s)' % ck('Awaiting approval'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Time sheet mismatches, last 4 weeks', 'COUNTIFS({range:timesheets.mismatch},%s,{range:timesheets.period_end},">="&({today}-28))' % ck('Mismatch'), 'int'),
 KPI('Caregivers paid this period', 'SUMIFS({range:payperiods.caregivers_paid},%s)' % CUR, 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Payroll KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Pay cost, revenue, overtime pay and payroll burden", "date": "payratio.month", "series": [
   {"label": "Revenue", "sum": "payratio.revenue", "date": "payratio.month"}, {"label": "Total pay cost", "sum": "payratio.total_pay_cost", "date": "payratio.month"},
   {"label": "Payroll burden", "sum": "payratio.burden", "date": "payratio.month"}, {"label": "Overtime pay", "sum": "otmonth.overtime_pay", "date": "otmonth.month"}]},
 "breakdowns": [{"title": "Pay run cost by employment type", "by": "payrun.employment", "value": "payrun.total_cost", "agg": "sum"}, {"title": "Pre-payroll warnings by kind", "by": "warnings.kind", "agg": "count"},
                {"title": "Bonuses and deductions by kind", "by": "adjust.kind", "value": "adjust.amount", "agg": "sum"}, {"title": "Pay periods by status", "by": "payperiods.status", "agg": "count"}]}
insights = {"filters": [{"label": "Employment", "list": "emp"}, {"label": "Warning kind", "list": "wkind"}, {"label": "Holiday", "list": "hol"}],
 "gauges": [
  {"title": "Months within 1 point of the ceiling", "num": AGG('count', 'payratio', where=[('ceiling_check', '<>', ck('Over ceiling'))]), "den": AGG('count', 'payratio')},
  {"title": "Months with overtime under the target", "num": AGG('count', 'otmonth', where=[('share_check', '=', ck('Within target'))]), "den": AGG('count', 'otmonth')},
  {"title": "Time sheets approved", "num": AGG('count', 'timesheets', where=[('approval', '=', ck('Approved'))]), "den": AGG('count', 'timesheets')},
  {"title": "Pre-payroll warnings fixed", "num": AGG('count', 'warnings', where=[('status', '=', ck('Fixed'))]), "den": AGG('count', 'warnings')},
  {"title": "Caregivers under the overtime line", "num": AGG('count', 'otforecast', where=[('line_check', '<>', ck('Over the line'))]), "den": AGG('count', 'otforecast')},
  {"title": "Holidays with a positive margin", "num": AGG('count', 'holidays', where=[('holiday_margin', '>', 0)]), "den": AGG('count', 'holidays')}],
 "charts": [
  CHART('Payroll cost per month', 'column', 'month', [AGG('sum', 'payratio', 'payratio.total_pay_cost', date='payratio.month', label='Total pay cost')]),
  CHART('Payroll cost ratio per month', 'column', 'month', [AGG('avg', 'payratio', 'payratio.ratio', date='payratio.month', label='Ratio to revenue')]),
  CHART('Overtime hours per month', 'column', 'month', [AGG('sum', 'otmonth', 'otmonth.overtime_hours', date='otmonth.month', label='Overtime hours')]),
  CHART('Overtime pay per month', 'column', 'month', [AGG('sum', 'otmonth', 'otmonth.overtime_pay', date='otmonth.month', label='Overtime pay')]),
  CHART('Overtime share per month', 'column', 'month', [AGG('avg', 'otmonth', 'otmonth.overtime_share', date='otmonth.month', label='Overtime share')]),
  CHART('Pay by component per month', 'stacked', 'month', [AGG('sum', 'payratio', 'payratio.caregiver_pay', date='payratio.month', label='Caregiver pay'), AGG('sum', 'payratio', 'payratio.overtime_pay', date='payratio.month', label='Overtime pay'),
        AGG('sum', 'payratio', 'payratio.travel_mileage', date='payratio.month', label='Travel and mileage'), AGG('sum', 'payratio', 'payratio.burden', date='payratio.month', label='Payroll burden')]),
  CHART('Pay run total per month', 'column', 'month', [AGG('sum', 'payperiods', 'payperiods.total_cost', date='payperiods.pay_date', label='Pay run total')]),
  CHART('Paid hours per month', 'column', 'month', [AGG('sum', 'payperiods', 'payperiods.hours', date='payperiods.pay_date', label='Paid hours')]),
  CHART('Overtime hours by employment type', 'bar', 'payrun.employment', [AGG('sum', 'payrun', 'payrun.overtime_hours', label='Overtime hours')]),
  CHART('Cost per worked hour by employment type', 'bar', 'byemp.employment', [AGG('avg', 'byemp', 'byemp.cost_per_hour', label='Cost per hour')]),
  CHART('Holiday premium paid per holiday', 'bar', 'holpay.holiday', [AGG('sum', 'holpay', 'holpay.extra_pay', label='Extra pay paid')]),
  CHART('Holiday margin per holiday', 'bar', 'holidays.holiday', [AGG('sum', 'holidays', 'holidays.holiday_margin', label='Margin on the day')]),
  CHART('Holiday visits booked per holiday', 'bar', 'holidays.holiday', [AGG('sum', 'holidays', 'holidays.visits_booked', label='Visits booked')]),
  CHART('Travel pay per month', 'column', 'month', [AGG('sum', 'payperiods', 'payperiods.travel_pay', date='payperiods.pay_date', label='Travel pay')]),
  CHART('Mileage amount per month', 'column', 'month', [AGG('sum', 'payperiods', 'payperiods.mileage_amount', date='payperiods.pay_date', label='Mileage amount')]),
  CHART('Cover premium per month', 'column', 'month', [AGG('sum', 'payperiods', 'payperiods.cover_premium', date='payperiods.pay_date', label='Cover premium')]),
  CHART('Bonuses and deductions by kind', 'bar', 'adjust.kind', [AGG('sum', 'adjust', 'adjust.amount', label='Amount')]),
  CHART('Pay rate changes by reason', 'bar', 'raises.reason', [AGG('count', 'raises', label='Pay rate changes')]),
  CHART('Burden share per month', 'column', 'month', [AGG('avg', 'burden', 'burden.burden_share', date='burden.month', label='Burden share of pay')]),
  CHART('Warnings by kind', 'bar', 'warnings.kind', [AGG('count', 'warnings', label='Warnings')]),
  CHART('Warnings found per month', 'column', 'month', [AGG('count', 'warnings', date='warnings.found_on', label='Warnings found')]),
  CHART('Time sheet mismatches per month', 'column', 'month', [AGG('count', 'timesheets', date='timesheets.period_end', label='Mismatches', where=[('mismatch', '=', ck('Mismatch'))])])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Payroll line calculator with visible rules", "why": "regular, overtime, holiday, travel, mileage, bonus and deductions line by line, so a miscalculated time is found before pay day", "where": "Payroll Line Calculator"},
 {"name": "Pre-payroll check with a warnings log", "why": "overtime near the line, missing check-outs, negative net pay and time sheet mismatches are logged, ranked by days open and fixed before the pay run", "where": "Pre-payroll Check"},
 {"name": "Midweek overtime forecast", "why": "hours worked so far plus hours still scheduled show who crosses the line this week and what it costs with burden", "where": "Overtime Forecast"},
 {"name": "Move this visit to avoid overtime", "why": "three caregivers who could take a visit are compared on overtime created and travel, so you move the visit that saves the most", "where": "Move Visit to Avoid Overtime"},
 {"name": "Overtime rule test: weekly or daily line", "why": "the same week of hours priced under a weekly line and a daily line, so you see what each rule would cost you", "where": "Overtime Rule Test"},
 {"name": "Payroll cost per hour against the bill rate", "why": "cost per paid hour, share of the bill rate, margin per hour and the bill rate needed for your target margin", "where": "Payroll Cost per Hour"},
 {"name": "Payroll cost ceiling by month", "why": "24 months of pay cost against revenue, the room under your ceiling and the hours to cut or revenue to add", "where": "Payroll Cost Ratio"},
 {"name": "Holiday margin forecast and premium choice", "why": "pay at 1.25, 1.5 or 2 times with your guess of volunteers: the expected margin of each choice and the best premium", "where": "Holiday Premium Choice"},
 {"name": "Paid travel policy test", "why": "unpaid first minutes and a cap per leg priced for the whole team, with pay saved a year and the effect per caregiver", "where": "Paid Travel Policy Test"},
 {"name": "Pay run funding check", "why": "cash after the pay run, invoices expected before pay day and your cash floor give Fund now or Wait", "where": "Pay Run Funding Check"},
 {"name": "Burden check against your setting", "why": "payroll taxes, workers insurance and benefits as shares of pay against the burden you plan with", "where": "Burden Check"},
 {"name": "Time sheet approval against check-ins", "why": "hours entered against hours from check-ins with a mismatch flag and who approved and when", "where": "Time Sheet Approvals"}]
competitors = [
 {"what": "free payroll and time log templates", "lacks": "total hours but have no overtime forecast, no holiday margin, no travel and mileage lines and no warnings before pay day"},
 {"what": "subscription home care software with a per-user fee", "lacks": "charge per caregiver or per client, lock your data in and give no editable overtime rules, no cost ceiling and no premium choice"},
 {"what": "single-sheet overtime calculators", "lacks": "work out one week for one person, with no schedule view, no move suggestions and no history by month"},
 {"what": "generic payroll spreadsheets", "lacks": "are not built for visits, holiday bands, paid travel time or cover premium, so the agency rules are typed by hand each run"},
 {"what": "payroll service portals", "lacks": "pay the run but do not compare hours paid with hours billed, forecast overtime or show the payroll cost ratio against revenue"}]
guide = [
 'Open Start and type your agency name and your payroll settings in the yellow cells: the overtime line (40 hours a week), the overtime multiplier, the holiday multipliers, payroll burden, mileage rate and your cost ceiling.',
 'Check Caregivers, Pay Rate Card and Team. A caregiver is also called a carer, care worker or support worker. A one-person agency can use only Pay Run Lines, Pay Periods and Holidays.',
 'Each pay run, add one row per caregiver on Pay Run Lines. Gross pay, net pay, payroll burden (payroll taxes, workers insurance and benefits on top of pay) and cost per hour fill in by themselves. Confirm pay rules with your adviser.',
 'Enter time sheets on Time Sheet Approvals with the hours from check-ins typed or pasted from whatever you use. The workbook compares them; it has no app, no GPS and no automatic check-in.',
 'On Monday, use Pre-payroll Check and Pre-payroll Warnings: fix missing check-outs, negative net pay and mismatches before the pay run. Pay Periods shows hours paid against hours billed.',
 'On Wednesday, update Overtime Forecast and look at This and Next Week Visits. Overtime means hours above the weekly line. Midweek Overtime Forecast and Move Visit to Avoid Overtime say which visit to give to whom.',
 'Use Holidays, Holiday Margin Forecast and Holiday Premium Choice before every holiday. Holiday rate means the extra pay and charge on a bank holiday; Holiday Pay History shows what past holidays cost.',
 'Record Bonuses and Deductions, Pay Rate Changes, Travel and Mileage Pay and Payroll Burden by Month so every pay line has a reason you can show. Use miles and your own rate if you prefer.',
 'Read Payroll Cost Ratio and the Payroll KPI Dashboard every month: pay cost against revenue and your ceiling, overtime share, warnings and time sheets.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Why a workbook: one flat price, no per-caregiver or per-client fee, no price rise when hours grow, and your data stays in your own file. It prepares numbers for your payroll service or adviser and gives no legal or employment-status advice.']
listing = {"title": "Home Care Agency Payroll Excel Template: Overtime Forecast, Pay Run, Holiday Pay, Mileage, Cost Ceiling, KPI Dashboard",
 "headline": "Prepare the pay run, see overtime before it happens, in one Excel file",
 "tags": ["home care agency", "payroll template", "overtime forecast", "caregiver pay", "pay run", "holiday pay", "mileage pay", "payroll spreadsheet", "care agency", "excel template", "timesheet check", "payroll cost", "caregiver payroll"],
 "description": ("Prepare caregiver payroll in one Excel workbook, built for a small non-medical home care agency run by an owner-director with a scheduler, an office manager and about 40 caregivers. A one-person start-up agency can use Pay Run Lines, Pay Periods and Holidays on their own.\n\n"
  "Pay Run Lines show regular, overtime, holiday, paid travel, mileage, cover premium, bonus and deductions per caregiver and pay period, with gross pay, net pay, payroll burden, total cost and cost per worked hour calculated. "
  "Pre-payroll Warnings and Time Sheet Approvals compare hours entered with hours from check-ins and list overtime near the line, missing check-outs and negative net pay before pay day. "
  "Overtime Forecast and This and Next Week Visits show who crosses your overtime line this week, and Overtime Moves suggest which visit to give to whom. "
  "Holidays, Holiday Pay History, Pay Rate Card, Pay Rate Changes, Travel and Mileage Pay, Payroll Burden by Month, Overtime by Month and Payroll Cost Ratio keep every pay rule visible and checked against your own ceiling.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: payroll line calculator, pre-payroll check, midweek overtime forecast, move this visit, overtime rule test, payroll cost per hour, cost ceiling, burden check, holiday margin, premium choice, paid travel policy, pay run funding check and more. "
  f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.\n\n"
  "This is part four of the Home Care Agency Business suite. A standard .xlsx workbook with no macros, one flat price with no per-caregiver fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. "
  "It prepares numbers for a payroll service or an adviser and gives no legal, tax or employment advice: confirm every pay and tax cell with your adviser. It has no live app, no GPS and no automatic check-in."),
 "features": ["Pay run lines with gross, net, burden and cost per hour", "Pre-payroll warnings and time sheet check against check-ins", "Midweek overtime forecast with move suggestions", "Overtime rule test: weekly or daily line",
              "Holiday margin forecast and premium choice", "Paid travel and mileage policy test", "Pay run funding check against your cash floor", "Payroll cost ratio against your ceiling by month",
              f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
for t in tables:
    pass
s = _lib.spec(id=f'{SUITE}-p4', slug='home-care-payroll', profession='Home Care Agency Business', name='Caregiver Payroll and Overtime',
         tagline='Prepare the pay run and see overtime before it happens', price_usd=29, colors={"primary": "#3A506B", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 4, "of": 8, "focus": "Caregiver payroll and overtime"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hc4.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
