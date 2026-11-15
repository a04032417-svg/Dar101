"""Home care agency suite part 4: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc4_lists import *
import hc4_data as D

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF(role, k, label):
    m = 'MATCH(%s,{range:team.role},0)' % tok('role', role)
    return [CA(k, label, 'text', 'IFERROR(INDEX({range:team.name},%s)&"","")' % m, 20), CA(k + '_phone', label + ' phone', 'text', 'IFERROR(INDEX({range:team.phone},%s)&"","")' % m, 18)]
def CGPH(): return CA('phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18)
def COMP(): return CA('company', 'Agency', 'text', '{set:company}&""', 22)
OT = '{set:overtime_hours}'; BUR = '(1+{set:payroll_burden})'
W = tok('band', 'Weekday')

settings = [
    S('company', 'Your agency name', 'text', COMPANY),
    S('overtime_hours', 'Overtime line: hours a week (hours above it are overtime)', 'int', OVERTIME_HOURS),
    S('overtime_mult', 'Overtime pay multiplier', 'num', OVERTIME_MULT),
    S('near_line_hours', 'Near the line from this many hours a week', 'int', 36),
    S('holiday_pay_mult', 'Holiday pay multiplier (bank holiday rate)', 'num', HOLIDAY_PAY_MULT),
    S('holiday_bill_mult', 'Holiday charge multiplier', 'num', HOLIDAY_BILL_MULT),
    S('holiday_shift_hours', 'Average hours one caregiver works on a holiday', 'num', 6),
    S('payroll_burden', 'Payroll burden on pay (example, confirm with your adviser)', 'pct', PAYROLL_BURDEN),
    S('payroll_taxes_pct', 'Burden part: payroll taxes (example, confirm)', 'pct', 0.10),
    S('workers_ins_pct', "Burden part: workers' insurance (example, confirm)", 'pct', 0.055),
    S('benefits_pct', 'Burden part: benefits (example, confirm)', 'pct', 0.045),
    S('payroll_ratio_ceiling', 'Payroll cost ceiling (share of revenue)', 'pct', PAYROLL_RATIO_CEILING),
    S('overtime_share_target', 'Overtime share target (share of paid hours)', 'pct', 0.03),
    S('target_margin', 'Target gross margin per client hour', 'pct', TARGET_MARGIN),
    S('mileage_rate', 'Mileage rate per km (or per mile, your own rate)', 'money', MILEAGE_RATE),
    S('cover_premium', 'Cover premium per hour (short-notice cover)', 'money', COVER_PREMIUM),
    S('timesheet_tolerance', 'Hours difference allowed on a time sheet', 'num', 0.5),
    S('cash_floor', 'Cash floor (cash kept after every pay run)', 'money', CASH_FLOOR)]
assert 3 <= len(settings) <= 20

tables = []
# 1 pay run lines
tables.append(T('payrun', 'Pay Run Lines', 'Pay run lines per caregiver and pay period',
    'One row per caregiver per bi-weekly pay run: hours, pay lines, bonus and deductions; gross pay, net pay, payroll burden, total cost and cost per hour fill in. Confirm every pay line with your adviser.', [
    C('pay_id', 'Pay line ID', 'text', 10, required=True), C('period_start', 'Period start', 'date', 11), C('period_end', 'Period end', 'date', 11), C('pay_date', 'Pay date', 'date', 11),
    REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('employment', 'Employment', 'emp', 11), C('regular_hours', 'Regular hours', 'num', 9), C('overtime_hours', 'Overtime hours', 'num', 9),
    C('holiday_hours', 'Holiday hours', 'num', 9), C('travel_hours', 'Travel hours', 'num', 9), C('distance_km', 'Kilometres', 'num', 9), C('regular_pay', 'Regular pay', 'money', 12),
    C('overtime_pay', 'Overtime pay', 'money', 11), C('holiday_premium', 'Holiday premium', 'money', 11), C('travel_pay', 'Travel pay', 'money', 11), C('mileage_pay', 'Mileage amount', 'money', 11),
    C('cover_premium', 'Cover premium', 'money', 11), C('bonus', 'Bonus', 'num', 9), C('deductions', 'Deductions', 'num', 10), LST('status', 'Pay status', 'paystat', 10),
    CA('gross_pay', 'Gross pay', 'money', 'ROUND({col:regular_pay}+{col:overtime_pay}+{col:holiday_premium}+{col:travel_pay}+{col:mileage_pay}+{col:cover_premium}+{col:bonus},2)', 12),
    CA('net_pay', 'Net pay', 'money', 'ROUND({col:gross_pay}-{col:deductions},2)', 12),
    CA('burden', 'Payroll burden', 'money', 'ROUND(({col:gross_pay}-{col:mileage_pay})*{set:payroll_burden},2)', 11),
    CA('total_cost', 'Total cost', 'money', 'ROUND({col:gross_pay}+{col:burden},2)', 12),
    CA('cost_per_hour', 'Cost per worked hour', 'money', 'IFERROR(ROUND({col:total_cost}/({col:regular_hours}+{col:overtime_hours}),2),0)', 11),
    CGPH(), COMP()], D.payrun_d(), 1500,
    [A('overtime_hours', '> 0', 'warn'), A('net_pay', '< 0', 'bad'), A('status', '= ' + tok('paystat', 'Due'), 'warn'), A('status', '= ' + tok('paystat', 'Paid'), 'good')]))
# 2 warnings
tables.append(T('warnings', 'Pre-payroll Warnings', 'Pre-payroll warnings found before pay day',
    'One row per problem found while preparing a pay run: overtime near the line, a missing check-out, a negative net pay, a time sheet mismatch; the open flag and days open fill in by themselves.', [
    C('warning_id', 'Warning ID', 'text', 10, required=True), C('period_start', 'Period start', 'date', 11), C('period_end', 'Period end', 'date', 11), REF('caregiver', 'Caregiver', 'caregivers.name', 22),
    LST('kind', 'Kind', 'wkind', 22), C('detail', 'Detail', 'text', 30), C('visit_date', 'Visit date', 'date', 11), C('found_on', 'Found on', 'date', 11), C('fixed_on', 'Fixed on', 'date', 11),
    CA('status', 'Open or fixed', 'text', 'IF({col:fixed_on}="",%s,%s)' % (ck('Open'), ck('Fixed')), 11),
    CA('days_open', 'Days open', 'int', 'IF({col:fixed_on}="",{today}-{col:found_on},{col:fixed_on}-{col:found_on})', 9),
    CGPH()] + STAFF('Care coordinator', 'scheduler', 'Scheduler') + STAFF('Office manager', 'office_manager', 'Office manager') + [COMP()], D.warnings_d(), 600,
    [A('status', '= ' + ck('Open'), 'bad'), A('days_open', '> 3', 'warn'), A('status', '= ' + ck('Fixed'), 'good')]))
# 3 overtime forecast
tables.append(T('otforecast', 'Overtime Forecast', 'Overtime forecast for the week, per caregiver',
    'One row per caregiver for the week: hours worked so far plus hours still scheduled give the forecast; hours over the line, the extra cost with burden and a Safe, Near or Over check fill in.', [
    C('caregiver_id', 'Caregiver ID', 'text', 10, required=True), REF('caregiver', 'Caregiver', 'caregivers.name', 22), C('week', 'Week starting', 'date', 11), C('worked_so_far', 'Hours worked so far', 'num', 10),
    C('still_scheduled', 'Hours still scheduled', 'num', 10), C('hours_limit', 'Own hours limit', 'int', 9),
    CA('forecast_hours', 'Forecast hours', 'num', 'ROUND({col:worked_so_far}+{col:still_scheduled},2)', 10),
    CA('hours_over', 'Hours over the line', 'num', 'MAX(0,{col:forecast_hours}-' + OT + ')', 10),
    CA('pay_rate', 'Pay rate', 'money', LKN('caregivers.pay_rate', 'caregivers.name', 'caregiver'), 9),
    CA('overtime_cost', 'Extra overtime cost', 'money', 'ROUND({col:hours_over}*{col:pay_rate}*({set:overtime_mult}-1)*' + BUR + ',2)', 11),
    CA('line_check', 'Line check', 'text', 'IF({col:forecast_hours}>' + OT + ',%s,IF({col:forecast_hours}>={set:near_line_hours},%s,%s))' % (ck('Over the line'), ck('Near the line'), ck('Safe')), 13),
    CA('over_limit', 'Hours over own limit', 'num', 'MAX(0,{col:forecast_hours}-{col:hours_limit})', 10),
    CGPH()] + STAFF('Care coordinator', 'scheduler', 'Scheduler') + [COMP()], D.otforecast_d(), 120,
    [A('line_check', '= ' + ck('Over the line'), 'bad'), A('line_check', '= ' + ck('Near the line'), 'warn'), A('line_check', '= ' + ck('Safe'), 'good')]))
# 4 overtime moves
MV_AV = ('(MAX(0,{col:from_hours}-%s)-MAX(0,{col:from_hours}-{col:hours}-%s))-(MAX(0,{col:to_hours}+{col:hours}-%s)-MAX(0,{col:to_hours}-%s))' % (OT, OT, OT, OT))
tables.append(T('otmoves', 'Overtime Moves', 'Overtime moves: visits to hand to another caregiver',
    'One row per suggested move of a visit from a caregiver near or over the line to another; the overtime hours avoided, the saving with burden and Move or Keep fill in by themselves.', [
    C('move_id', 'Move ID', 'text', 10, required=True), C('visit_id', 'Visit ID', 'text', 10), C('visit_date', 'Visit date', 'date', 11), REF('from_caregiver', 'From caregiver', 'caregivers.name', 22),
    REF('to_caregiver', 'To caregiver', 'caregivers.name', 22), C('hours', 'Visit hours', 'num', 9), C('from_hours', 'From hours that week', 'num', 11), C('to_hours', 'To hours that week', 'num', 11),
    CA('pay_rate', 'From pay rate', 'money', LKN('caregivers.pay_rate', 'caregivers.name', 'from_caregiver'), 9),
    CA('avoided', 'Overtime hours avoided', 'num', 'ROUND(' + MV_AV + ',2)', 11),
    CA('saving', 'Saving with burden', 'money', 'ROUND({col:avoided}*{col:pay_rate}*({set:overtime_mult}-1)*' + BUR + ',2)', 11),
    CA('verdict', 'Move or keep', 'text', 'IF({col:saving}>0,%s,%s)' % (ck('Move'), ck('Keep')), 11)], D.otmoves_d(), 200,
    [A('verdict', '= ' + ck('Move'), 'good'), A('verdict', '= ' + ck('Keep'), 'warn')]))
# 5 caregiver hours by week
tables.append(T('hoursweek', 'Caregiver Hours by Week', 'Caregiver hours by week with overtime',
    'One row per caregiver per week: scheduled hours, worked hours, travel hours, overtime hours and visits; total paid hours and the difference to the schedule fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 10, required=True), REF('caregiver', 'Caregiver', 'caregivers.name', 22), C('week', 'Week starting', 'date', 11), C('scheduled_hours', 'Scheduled hours', 'num', 10),
    C('worked_hours', 'Worked hours', 'num', 10), C('travel_hours', 'Travel hours', 'num', 10), C('overtime_hours', 'Overtime hours', 'num', 10), C('visits', 'Visits', 'int', 8),
    CA('total_paid', 'Total paid hours', 'num', 'ROUND({col:worked_hours}+{col:travel_hours},2)', 10),
    CA('vs_schedule', 'Paid minus scheduled', 'num', 'ROUND({col:total_paid}-{col:scheduled_hours},2)', 11)], D.hoursweek_d(), 1000,
    [A('overtime_hours', '> 0', 'warn'), A('vs_schedule', '> 3', 'warn')]))
# 6 overtime by month
tables.append(T('otmonth', 'Overtime by Month', 'Overtime by month with the share of paid hours',
    'One row per month: paid hours, overtime hours, overtime pay and caregivers with overtime; the overtime share and a check against your target fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('hours', 'Paid hours', 'num', 11), C('overtime_hours', 'Overtime hours', 'num', 11), C('overtime_pay', 'Overtime pay', 'money', 12),
    C('caregivers_ot', 'Caregivers with overtime', 'int', 11),
    CA('overtime_share', 'Overtime share', 'pct', 'IFERROR({col:overtime_hours}/{col:hours},0)', 10),
    CA('share_check', 'Target check', 'text', 'IF({col:overtime_share}<={set:overtime_share_target},%s,%s)' % (ck('Within target'), ck('Over target')), 13),
    CA('pay_per_hour', 'Overtime pay per hour', 'money', 'IFERROR(ROUND({col:overtime_pay}/{col:overtime_hours},2),0)', 11)] + STAFF('Care coordinator', 'scheduler', 'Scheduler') + STAFF('Owner-director', 'owner', 'Owner') + [COMP()],
    D.otmonth_d(), 60, [A('share_check', '= ' + ck('Over target'), 'bad')]))
# 7 holidays
AVP = 'IFERROR(AVERAGEIFS({range:paycard.pay_rate},{range:paycard.band},%s),0)' % W
AVB = 'IFERROR(AVERAGEIFS({range:paycard.bill_rate},{range:paycard.band},%s),0)' % W
tables.append(T('holidays', 'Holidays', 'Holiday calendar with extra pay, extra charge and margin',
    'One row per holiday (bank holiday): pay and charge multipliers, visits and hours booked; the extra pay, extra charge, margin on the day and a Worth it check fill in by themselves.', [
    C('holiday_id', 'Holiday ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('holiday', 'Holiday', 'hol', 20), LST('weekday', 'Weekday', 'wday', 11), C('pay_mult', 'Pay multiplier', 'num', 9),
    C('bill_mult', 'Bill multiplier', 'num', 9), C('visits_booked', 'Visits booked', 'int', 9), C('hours_booked', 'Hours booked', 'num', 9), REF('notify', 'Caregiver to tell first', 'caregivers.name', 22),
    CA('avg_pay', 'Average weekday pay rate', 'money', AVP, 10), CA('avg_bill', 'Average weekday bill rate', 'money', AVB, 10),
    CA('extra_pay', 'Extra pay with burden', 'money', 'ROUND({col:hours_booked}*{col:avg_pay}*({col:pay_mult}-1)*' + BUR + ',2)', 12),
    CA('extra_charge', 'Extra charge', 'money', 'ROUND({col:hours_booked}*{col:avg_bill}*({col:bill_mult}-1),2)', 12),
    CA('holiday_margin', 'Margin on the day', 'money', 'ROUND({col:hours_booked}*({col:avg_bill}*{col:bill_mult}-{col:avg_pay}*{col:pay_mult}*' + BUR + '),2)', 12),
    CA('margin_flag', 'Margin check', 'text', 'IF({col:holiday_margin}<0,%s,IF(IFERROR({col:holiday_margin}/({col:hours_booked}*{col:avg_bill}*{col:bill_mult}),0)<{set:target_margin}*0.75,%s,%s))' % (ck('Loses money'), ck('Thin margin'), ck('Worth it')), 12),
    CA('days_to', 'Days to the holiday', 'int', '{col:date}-{today}', 9),
    CA('caregivers_needed', 'Caregivers needed', 'int', 'ROUNDUP({col:hours_booked}/{set:holiday_shift_hours},0)', 10),
    CA('phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'notify'), 18)] + STAFF('Care coordinator', 'scheduler', 'Scheduler') + STAFF('Owner-director', 'owner', 'Owner') + [COMP()],
    D.holidays_d(), 80, [A('days_to', '<= 14', 'warn'), A('margin_flag', '= ' + ck('Loses money'), 'bad')]))
# 8 holiday pay history
tables.append(T('holpay', 'Holiday Pay History', 'Holiday pay history: extra pay paid and extra charge billed',
    'One row per past holiday: delivered visits and hours, the extra pay paid and the extra charge billed; the net holiday effect (extra charge minus extra pay with burden) fills in by itself.', [
    C('holiday_id', 'Holiday ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('holiday', 'Holiday', 'hol', 20), C('visits', 'Visits delivered', 'int', 10), C('hours', 'Hours delivered', 'num', 10),
    C('extra_pay', 'Extra pay paid', 'money', 12), C('extra_charge', 'Extra charge billed', 'money', 12),
    CA('net_effect', 'Net holiday effect', 'money', 'ROUND({col:extra_charge}-{col:extra_pay}*' + BUR + ',2)', 12),
    CA('pay_per_hour', 'Extra pay per hour', 'money', 'IFERROR(ROUND({col:extra_pay}/{col:hours},2),0)', 10)], D.holpay_d(), 60, [A('net_effect', '< 0', 'bad')]))
# 9 payroll cost ratio
tables.append(T('payratio', 'Payroll Cost Ratio', 'Payroll cost ratio by month against your ceiling',
    'One row per month: revenue, billed hours and pay lines (pay, overtime, travel and mileage, burden); total pay cost, ratio and a ceiling check (Within, Near up to 1 point over, Over) fill in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('revenue', 'Revenue', 'money', 13), C('billed_hours', 'Billed hours', 'num', 10), C('caregiver_pay', 'Caregiver pay', 'money', 13),
    C('overtime_pay', 'Overtime pay', 'money', 12), C('travel_mileage', 'Travel and mileage', 'money', 12), C('burden', 'Payroll burden', 'money', 12),
    CA('total_pay_cost', 'Total pay cost', 'money', '{col:caregiver_pay}+{col:overtime_pay}+{col:travel_mileage}+{col:burden}', 13),
    CA('ratio', 'Ratio to revenue', 'pct', 'IFERROR({col:total_pay_cost}/{col:revenue},0)', 10),
    CA('ceiling_check', 'Ceiling check', 'text', 'IF({col:ratio}>{set:payroll_ratio_ceiling}+0.01,%s,IF({col:ratio}>{set:payroll_ratio_ceiling},%s,%s))' % (ck('Over ceiling'), ck('Near ceiling'), ck('Within ceiling')), 13),
    CA('cost_per_hour', 'Pay cost per billed hour', 'money', 'IFERROR(ROUND({col:total_pay_cost}/{col:billed_hours},2),0)', 11),
    CA('room', 'Room under the ceiling', 'money', 'ROUND({set:payroll_ratio_ceiling}*{col:revenue}-{col:total_pay_cost},2)', 12)] + STAFF('Office manager', 'office_manager', 'Office manager') + STAFF('Accountant', 'accountant', 'Accountant') + [COMP()],
    D.payratio_d(), 60, [A('ceiling_check', '= ' + ck('Over ceiling'), 'bad'), A('ceiling_check', '= ' + ck('Near ceiling'), 'warn'), A('ceiling_check', '= ' + ck('Within ceiling'), 'good')]))
# 10 pay periods
tables.append(T('payperiods', 'Pay Periods', 'Pay periods with hours paid against hours billed',
    'One row per bi-weekly pay period: hours, total cost, caregivers paid, travel, mileage and cover amounts; days to pay date, hours gap and open warnings fill in. A one-person agency can use it.', [
    C('period_id', 'Period ID', 'text', 9, required=True), C('period_start', 'Period start', 'date', 11), C('period_end', 'Period end', 'date', 11), C('pay_date', 'Pay date', 'date', 11), LST('status', 'Status', 'paystat', 10),
    C('hours', 'Paid hours', 'num', 10), C('total_cost', 'Total cost', 'money', 13), C('caregivers_paid', 'Caregivers paid', 'int', 10), C('travel_pay', 'Travel pay', 'money', 11), C('mileage_amount', 'Mileage amount', 'money', 11),
    C('cover_premium', 'Cover premium', 'money', 11), C('billed_hours', 'Hours billed', 'num', 10),
    CA('days_to_pay', 'Days to pay date', 'int', '{col:pay_date}-{today}', 9),
    CA('hours_gap', 'Paid minus billed hours', 'num', 'ROUND({col:hours}-{col:billed_hours},2)', 11),
    CA('cost_per_hour', 'Cost per paid hour', 'money', 'IFERROR(ROUND({col:total_cost}/{col:hours},2),0)', 10),
    CA('open_warnings', 'Open warnings', 'int', 'COUNTIFS({range:warnings.period_end},{col:period_end},{range:warnings.status},%s)' % ck('Open'), 9),
    CA('approve_by', 'Approve by', 'date', '{col:pay_date}-2', 11)] + STAFF('Office manager', 'office_manager', 'Office manager') + STAFF('Owner-director', 'owner', 'Owner') + STAFF('Payroll service', 'payroll_service', 'Payroll service') + [COMP()],
    D.payperiods_d(), 120, [A('open_warnings', '> 0', 'warn'), A('status', '= ' + tok('paystat', 'Due'), 'warn')]))
# 11 caregivers
tables.append(T('caregivers', 'Caregivers', 'Caregivers with pay rate, hours limit and status',
    'One row per caregiver (a carer, care worker or support worker): employment type, pay rate, hire date, own hours limit, status and area; the pay lines and the forecast read the pay rate from here.', [
    C('caregiver_id', 'Caregiver ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('employment', 'Employment', 'emp', 11), C('pay_rate', 'Pay rate per hour', 'money', 11), C('hire_date', 'Hire date', 'date', 11),
    C('hours_limit', 'Hours limit a week', 'int', 10), LST('status', 'Status', 'cgstatus', 11), LST('area', 'Area', 'area', 13), C('left_date', 'Left on', 'date', 11), C('phone', 'Phone', 'text', 18)],
    D.caregivers_d(), 200, [A('status', '= ' + tok('cgstatus', 'Left'), 'warn')]))
# 12 pay rate card
tables.append(T('paycard', 'Pay Rate Card', 'Pay rate card by service and time band',
    'One row per service and time band: the bill rate per hour and the standard pay rate per hour; the pay multiplier against the weekday rate of the same service fills in by itself.', [
    LST('service', 'Service', 'svc', 18, required=True), LST('band', 'Time band', 'band', 11), C('bill_rate', 'Bill rate per hour', 'money', 11), C('pay_rate', 'Standard pay rate', 'money', 11),
    CA('pay_mult', 'Pay multiplier vs weekday', 'num', 'IFERROR(ROUND({col:pay_rate}/SUMIFS({range:paycard.pay_rate},{range:paycard.service},{col:service},{range:paycard.band},%s),2),0)' % W, 12),
    CA('margin_hour', 'Rate minus loaded pay', 'money', 'ROUND({col:bill_rate}-{col:pay_rate}*' + BUR + ',2)', 11)], D.paycard_d(), 60))
# 13 travel and mileage pay
tables.append(T('travelpay', 'Travel and Mileage Pay', 'Travel time pay and mileage per caregiver and period',
    'One row per caregiver per pay period with paid travel hours and kilometres; the all-in pay per kilometre fills in by itself. Use miles and your own rate if you prefer.', [
    C('travel_id', 'Travel line ID', 'text', 10, required=True), C('period_start', 'Period start', 'date', 11), C('period_end', 'Period end', 'date', 11), REF('caregiver', 'Caregiver', 'caregivers.name', 22),
    C('travel_hours', 'Travel hours', 'num', 9), C('travel_pay', 'Travel pay', 'money', 11), C('distance_km', 'Kilometres', 'num', 10), C('mileage_amount', 'Mileage amount', 'money', 11),
    CA('pay_per_km', 'Travel pay per km', 'money', 'IFERROR(ROUND(({col:travel_pay}+{col:mileage_amount})/{col:distance_km},2),0)', 10), CGPH()] + STAFF('Payroll service', 'payroll_service', 'Payroll service') + [COMP()],
    D.travelpay_d(), 600, [A('pay_per_km', '> 2', 'warn')]))
# 14 bonuses and deductions
BON = '%s,%s,%s' % (tok('adjk', 'Retention bonus'), tok('adjk', 'Referral bonus'), tok('adjk', 'Holiday thank-you'))
tables.append(T('adjust', 'Bonuses and Deductions', 'Bonuses and deductions per caregiver and pay run',
    'One row per bonus or deduction with the reason and who approved it; the type (Bonus or Deduction) fills in by itself. Deductions follow your own local rules: confirm with your adviser.', [
    C('adjust_id', 'Line ID', 'text', 9, required=True), C('period_start', 'Period start', 'date', 11), C('pay_date', 'Pay date', 'date', 11), REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('kind', 'Kind', 'adjk', 21),
    C('amount', 'Amount', 'money', 11), C('reason', 'Reason', 'text', 30), REF('approved_by', 'Approved by', 'team.name', 20),
    CA('type', 'Type', 'text', 'IF(OR({col:kind}=%s,{col:kind}=%s,{col:kind}=%s),%s,%s)' % (tok('adjk', 'Retention bonus'), tok('adjk', 'Referral bonus'), tok('adjk', 'Holiday thank-you'), ck('Bonus'), ck('Deduction')), 11),
    CGPH(), COMP()], D.adjust_d(), 400, [A('type', '= ' + ck('Deduction'), 'warn'), A('type', '= ' + ck('Bonus'), 'good')]))
# 15 pay rate changes
tables.append(T('raises', 'Pay Rate Changes', 'Pay rate changes per caregiver with the reason',
    'One row per change of a caregiver pay rate: the old rate, the new rate and the reason; the rise share and the rise per hour fill in by themselves.', [
    C('change_id', 'Change ID', 'text', 9, required=True), REF('caregiver', 'Caregiver', 'caregivers.name', 22), C('date', 'Effective date', 'date', 11), C('old_rate', 'Old rate', 'money', 10), C('new_rate', 'New rate', 'money', 10),
    LST('reason', 'Reason', 'raisr', 18), CA('rise_share', 'Rise share', 'pct', 'IFERROR(({col:new_rate}-{col:old_rate})/{col:old_rate},0)', 9),
    CA('rise_amount', 'Rise per hour', 'money', 'ROUND({col:new_rate}-{col:old_rate},2)', 9), CGPH()] + STAFF('Owner-director', 'owner', 'Owner') + [COMP()], D.raises_d(), 300,
    [A('rise_share', '> 0.06', 'warn')]))
# 16 payroll burden by month
tables.append(T('burden', 'Payroll Burden by Month', 'Payroll burden by month with the example split',
    "One row per month: the pay base and the example split of payroll taxes, workers' insurance and benefits; the total and the burden share of pay fill in. Example split, confirm with your adviser.", [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('pay_base', 'Pay base', 'money', 13), C('payroll_taxes', 'Payroll taxes', 'money', 12), C('workers_insurance', "Workers' insurance", 'money', 12),
    C('benefits', 'Benefits', 'money', 11), CA('total_burden', 'Total burden', 'money', '{col:payroll_taxes}+{col:workers_insurance}+{col:benefits}', 12),
    CA('burden_share', 'Burden share of pay', 'pct', 'IFERROR({col:total_burden}/{col:pay_base},0)', 11),
    CA('gap_points', 'Points vs the setting', 'num', 'ROUND(({col:burden_share}-{set:payroll_burden})*100,2)', 11)] + STAFF('Insurance broker', 'broker', 'Insurance broker') + [COMP()], D.burden_d(), 60,
    [A('gap_points', '> 1', 'warn')]))
# 17 time sheet approvals
tables.append(T('timesheets', 'Time Sheet Approvals', 'Time sheet approvals against check-in hours',
    'One row per caregiver time sheet: hours entered, hours from check-ins and who approved it; the difference, a Matches or Mismatch check and Approved or Awaiting approval fill in by themselves.', [
    C('sheet_id', 'Sheet ID', 'text', 9, required=True), REF('caregiver', 'Caregiver', 'caregivers.name', 22), C('period_start', 'Period start', 'date', 11), C('period_end', 'Period end', 'date', 11),
    C('hours_entered', 'Hours entered', 'num', 10), C('hours_checkins', 'Hours from check-ins', 'num', 11), REF('approved_by', 'Approved by', 'team.name', 20), C('approved_on', 'Approved on', 'date', 11),
    CA('difference', 'Difference', 'num', 'ROUND({col:hours_entered}-{col:hours_checkins},2)', 9),
    CA('mismatch', 'Hours check', 'text', 'IF(ABS({col:difference})>{set:timesheet_tolerance},%s,%s)' % (ck('Mismatch'), ck('Matches')), 11),
    CA('approval', 'Approval', 'text', 'IF({col:approved_on}="",%s,%s)' % (ck('Awaiting approval'), ck('Approved')), 15),
    CA('send_by', 'Send by', 'date', '{col:period_end}+3', 11), CGPH()] + STAFF('Payroll service', 'payroll_service', 'Payroll service') + [COMP()], D.timesheets_d(), 600,
    [A('mismatch', '= ' + ck('Mismatch'), 'bad'), A('approval', '= ' + ck('Awaiting approval'), 'warn')]))
# 18 pay run by employment type
tables.append(T('byemp', 'Pay Run by Employment', 'Pay run by employment type with cost per hour',
    'One row per pay period and employment type (hourly, part-time, live-in): caregivers, paid hours, overtime hours and total cost; cost per hour and overtime share fill in by themselves.', [
    C('period_start', 'Period start', 'date', 11, required=True), C('period_end', 'Period end', 'date', 11), LST('employment', 'Employment', 'emp', 12), C('caregivers', 'Caregivers', 'int', 11), C('hours', 'Paid hours', 'num', 13),
    C('overtime_hours', 'Overtime hours', 'num', 13), C('total_cost', 'Total cost', 'money', 14),
    CA('cost_per_hour', 'Cost per hour', 'money', 'IFERROR(ROUND({col:total_cost}/{col:hours},2),0)', 10),
    CA('overtime_share', 'Overtime share', 'pct', 'IFERROR({col:overtime_hours}/{col:hours},0)', 10)], D.byemp_d(), 300))
# 19 this week and next week visits
WKS = '({col:date}-WEEKDAY({col:date},2)+1)'
tables.append(T('weekvisits', 'This and Next Week Visits', 'This and next week visits with caregiver week hours',
    'One row per scheduled visit for this week and next week (paste from your scheduling software); the caregiver hours that week and the overtime line check fill in so you can move a visit before pay day.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('start', 'Start', 'time', 8), C('hours', 'Hours', 'num', 8), C('client', 'Client', 'text', 22), LST('band', 'Time band', 'band', 11),
    REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('status', 'Visit status', 'vstatus', 12),
    CA('week_hours', 'Caregiver hours that week', 'num', 'IF({col:caregiver}="",0,SUMIFS({range:weekvisits.hours},{range:weekvisits.caregiver},{col:caregiver},{range:weekvisits.date},">="&%s,{range:weekvisits.date},"<="&(%s+6),{range:weekvisits.status},"<>"&%s))' % (WKS, WKS, tok('vstatus', 'Cancelled')), 12),
    CA('week_check', 'Line check', 'text', 'IF({col:week_hours}>' + OT + ',%s,IF({col:week_hours}>={set:near_line_hours},%s,%s))' % (ck('Over the line'), ck('Near the line'), ck('Safe')), 13)], D.weekvisits_d(), 700,
    [A('week_check', '= ' + ck('Over the line'), 'bad'), A('week_check', '= ' + ck('Near the line'), 'warn'), A('status', '= ' + tok('vstatus', 'Open'), 'warn')]))
# 20 team
tables.append(T('team', 'Team', 'Team and outside contacts',
    'Your office team (owner-director, care coordinator, office manager, recruiter, two field supervisors) and ten outside contacts with phone and role; the messages read the phone numbers from here.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('team', 'Team', 'team', 11), LST('pay_type', 'Pay type', 'paytype', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('hours_week', 'Hours a week', 'int', 10), C('monthly_salary', 'Monthly salary', 'money', 12), C('hourly_rate', 'Hourly rate', 'num', 10), C('speciality', 'Speciality', 'text', 28),
    C('country', 'Country', 'text', 14), C('start', 'Start date', 'date', 11)], D.team_d(), 50))
assert len(tables) == 20
