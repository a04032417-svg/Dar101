"""Home care suite part 3: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc3_lists import *
import hc3_data as D

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF_PH(n, k, label='Phone to message'): return CA(k, label, 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % n, 18)
YES = '{list:yesno.yes}'
NOW = '(VALUE(LEFT({set:now_time},LEN({set:now_time})-3))*60+VALUE(RIGHT({set:now_time},2)))'
MON = '({col:date}-WEEKDAY({col:date},2)+1)'
THISWEEK = '({today}-WEEKDAY({today},2)+1)'

settings = [
    S('company', 'Your agency name', 'text', COMPANY), S('late_minutes', 'Minutes after the start that count as a late check-in', 'int', LATE_MINUTES),
    S('late_visit_target', 'Late visits as a share of visits: target', 'pct', 0.05), S('missed_visit_target', 'Missed visits as a share of visits: target', 'pct', 0.01),
    S('checkin_target', 'Wanted share of visits with check-in and check-out', 'pct', 0.98), S('now_time', 'Time now, as HH:MM (type it when you open Today Check-ins)', 'text', '11:00'),
    S('call_client_after', 'Minutes overdue after which the client is called first', 'int', 30), S('repeat_late', 'Late or missed visits in 30 days for a repeat case', 'int', 3),
    S('min_visit_hours', 'Minimum visit billed, hours (example)', 'int', MIN_VISIT_HOURS), S('overlong_minutes', 'Minutes over the schedule that count as an overlong visit', 'int', 15),
    S('short_notice_hours', 'Notice hours below which a cancellation is short (example)', 'int', 24), S('cancel_charge_pct', 'Share of visit value charged for short notice (example)', 'pct', 0.5),
    S('ts_tolerance', 'Hours a time sheet may differ before it is queried', 'num', 0.25), S('km_tolerance', 'Share a claimed distance may exceed the expected one', 'pct', 0.15),
    S('mileage_rate', 'Mileage rate per km (or per mile, your own rate)', 'money', MILEAGE_RATE), S('payroll_burden', 'Payroll burden on pay (confirm with your adviser)', 'pct', PAYROLL_BURDEN),
    S('travel_share_target', 'Paid travel cost as a share of caregiver pay: target', 'pct', 0.06)]
assert 3 <= len(settings) <= 20

tables = []
# 1 visit log
tables.append(T('visits', 'Visit Log', 'Visit log: scheduled against actual check-in and check-out',
    'One row per visit of the last 30 days: type or paste the check-in and check-out times (no app, no GPS needed); minutes late, hours worked, billable hours and the Late, Short, Long or Missed flag fill in by themselves. A one-person agency can use this page as its own time log.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('start', 'Scheduled start', 'time', 10), C('sched_hours', 'Scheduled hours', 'num', 10), REF('client', 'Client', 'clients.client', 22),
    LST('area', 'Area', 'area', 13), LST('service', 'Service', 'svc', 18), LST('band', 'Time band', 'band', 10), REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('cover', 'Cover type', 'cover', 10),
    LST('status', 'Status', 'vstatus', 12), C('check_in', 'Check-in', 'time', 9), C('check_out', 'Check-out', 'time', 9), C('reason', 'Reason', 'text', 22),
    CA('client_id', 'Client ID', 'text', LKT('clients.client_id', 'clients.client', 'client'), 10),
    CA('late_minutes', 'Minutes late', 'int', 'IF({col:check_in}="","",MAX(0,ROUND(({col:check_in}-{col:start})*1440,0)))', 9),
    CA('worked_hours', 'Hours worked', 'num', 'IF(OR({col:check_in}="",{col:check_out}=""),"",ROUND(MOD({col:check_out}-{col:check_in},1)*24,2))', 9),
    CA('hours_diff', 'Hours difference', 'num', 'IF({col:worked_hours}="","",ROUND({col:worked_hours}-{col:sched_hours},2))', 10),
    CA('billable_hours', 'Billable hours', 'num', 'IF({col:worked_hours}="","",IF(OR({col:service}=%s,{col:service}=%s),{col:sched_hours},MAX(%s,ROUND({col:worked_hours}*4,0)/4)))' % (
        tok('svc', 'Overnight care'), tok('svc', 'Live-in day'), LKN('clients.min_visit_hours', 'clients.client', 'client')), 9),
    CA('pay_estimate', 'Pay estimate', 'money', 'IF({col:worked_hours}="","",ROUND({col:worked_hours}*%s,2))' % LKN('caregivers.pay_rate', 'caregivers.name', 'caregiver'), 10),
    CA('flag', 'Visit flag', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:check_in}="",%s,IF({col:late_minutes}>{set:late_minutes},%s,IF({col:hours_diff}="",%s,IF({col:hours_diff}<-0.25,%s,IF({col:hours_diff}>0.25,%s,%s))))))))' % (
        tok('vstatus', 'Missed'), ck('Missed'), tok('vstatus', 'Cancelled'), ck('Cancelled'), tok('vstatus', 'No check-in'), ck('No check-in'), ck('Not due yet'), ck('Late'), ck('Not due yet'), ck('Short'), ck('Long'), ck('On time')), 12),
    CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18), CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18)], D.visits_d(), 2500,
    [A('flag', '= ' + ck('Late'), 'warn'), A('flag', '= ' + ck('Missed'), 'bad'), A('flag', '= ' + ck('No check-in'), 'bad'), A('flag', '= ' + ck('On time'), 'good'), A('status', '= ' + tok('vstatus', 'Open'), 'warn')]))
# 2 register
tables.append(T('register', 'Late and Missed Register', 'Late and missed register with phoning and repeat cases',
    'One row per late or missed visit of the last 12 weeks: minutes late, reason, when the caregiver was phoned and whether the client was told; the week and the repeat-caregiver flag fill in by themselves.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('client', 'Client', 'clients.client', 22), REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('area', 'Area', 'area', 13),
    LST('status', 'Status', 'vstatus', 11), C('minutes_late', 'Minutes late', 'int', 9), LST('delay_reason', 'Delay reason', 'delay', 20), LST('miss_reason', 'Missed reason', 'miss', 18), LST('weekday', 'Weekday', 'wday', 11),
    LST('employment', 'Employment type', 'emp', 11), C('phoned_on', 'Caregiver phoned on', 'date', 12), C('client_told', 'Client told', 'bool', 9),
    CA('week', 'Week (Monday)', 'date', MON, 12),
    CA('reason', 'Reason', 'text', 'IF({col:status}=%s,{col:miss_reason}&"",{col:delay_reason}&"")' % tok('vstatus', 'Missed'), 20),
    CA('repeat', 'Repeat caregiver check', 'text', 'IF(COUNTIFS({range:register.caregiver},{col:caregiver},{range:register.date},">="&({col:date}-29),{range:register.date},"<="&{col:date})>={set:repeat_late},%s,%s)' % (ck('Repeat caregiver'), ck('Single event')), 14),
    CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18), CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18),
    STAFF_PH(2, 'scheduler_phone', 'Scheduler phone'), STAFF_PH(5, 'supervisor_phone', 'Field supervisor phone')], D.register_d(), 800,
    [A('repeat', '= ' + ck('Repeat caregiver'), 'bad'), A('status', '= ' + tok('vstatus', 'Missed'), 'bad'), A('status', '= ' + tok('vstatus', 'Late'), 'warn'), A('client_told', '= {list:yesno.no}', 'warn')]))
# 3 today
tables.append(T('today', 'Today Check-ins', 'Today\'s check-ins with minutes overdue and who to call first',
    'The scheduler\'s morning board: today\'s visits and the first visits of tomorrow; type the time now in the Start sheet and the check-in as it arrives; minutes overdue, the call-first rank and the next step fill in by themselves. A one-person agency can use it as a daily to-do list.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('start', 'Scheduled start', 'time', 10), REF('client', 'Client', 'clients.client', 22), LST('area', 'Area', 'area', 13),
    REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('status', 'Status', 'vstatus', 12), C('check_in', 'Check-in', 'time', 9), C('sched_hours', 'Scheduled hours', 'num', 10), C('arrives_by', 'Expected arrival', 'time', 10),
    CA('minutes_overdue', 'Minutes overdue', 'int', 'IF(AND({col:date}={today},{col:check_in}=""),MAX(0,%s-ROUND({col:start}*1440,0)),0)' % NOW, 9),
    CA('sort_key', 'Sort key', 'int', 'IF({col:minutes_overdue}>0,{col:minutes_overdue}*1000+VALUE(RIGHT({col:visit_id},3)),0)', 9),
    CA('call_rank', 'Call-first rank', 'int', 'IF({col:minutes_overdue}>0,1+COUNTIFS({range:today.sort_key},">"&{col:sort_key}),"")', 9),
    CA('next_step', 'Next step', 'text', 'IF({col:minutes_overdue}>0,IF({col:minutes_overdue}>={set:call_client_after},%s,%s),IF({col:check_in}<>"",%s,%s))' % (ck('Call client first'), ck('Call caregiver first'), ck('Checked in'), ck('Not due yet')), 18),
    CA('overdue_count', 'Visits overdue now', 'int', 'COUNTIFS({range:today.minutes_overdue},">0")', 9),
    CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18), CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18),
    STAFF_PH(2, 'scheduler_phone', 'Scheduler phone'), STAFF_PH(16, 'answering_phone', 'Answering service phone')], D.today_d(), 300,
    [A('next_step', '= ' + ck('Call client first'), 'bad'), A('next_step', '= ' + ck('Call caregiver first'), 'warn'), A('next_step', '= ' + ck('Checked in'), 'good'), A('call_rank', '<= 3', 'bad')]))
# 4 caregiver hours by week
tables.append(T('cgweeks', 'Caregiver Hours by Week', 'Caregiver hours by week: worked, travel, overtime',
    'One row per caregiver and week: scheduled, worked, travel and overtime hours with the visits and late visits; worked minus scheduled and the late rate fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 10, required=True), C('week', 'Week (Monday)', 'date', 12), REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('employment', 'Employment type', 'emp', 11), C('scheduled_hours', 'Scheduled hours', 'num', 10),
    C('worked_hours', 'Worked hours', 'num', 10), C('travel_hours', 'Travel hours', 'num', 9), C('overtime_hours', 'Overtime hours', 'num', 9), C('visits', 'Visits', 'int', 8), C('late_visits', 'Late visits', 'int', 8),
    CA('worked_minus_sched', 'Worked minus scheduled hours', 'num', 'ROUND({col:worked_hours}-{col:scheduled_hours},2)', 11),
    CA('late_rate', 'Late rate', 'pct', 'IF({col:visits}=0,0,{col:late_visits}/{col:visits})', 9)], D.cgweeks_d(), 1500,
    [A('late_rate', '> {set:late_visit_target}', 'warn'), A('overtime_hours', '> 0', 'warn'), A('worked_minus_sched', '< -2', 'bad')]))
# 5 agency hours by week
tables.append(T('agencyweeks', 'Agency Hours by Week', 'Agency hours by week: delivered, billed, paid, leak',
    'One row per week of the history: scheduled, delivered, billed and paid hours with the visit counts; billed minus paid hours, the leak amount and the late and missed rates fill in by themselves.', [
    C('row_id', 'Week ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), C('month', 'Month', 'date', 11), C('scheduled_hours', 'Scheduled hours', 'num', 10), C('delivered_hours', 'Delivered hours', 'num', 10),
    C('billed_hours', 'Billed hours', 'num', 10), C('paid_hours', 'Paid hours', 'num', 10), C('visits', 'Visits', 'int', 8), C('late_visits', 'Late visits', 'int', 8), C('missed_visits', 'Missed visits', 'int', 8),
    C('avg_pay_rate', 'Average pay rate per hour', 'money', 11), C('avg_late_min', 'Average minutes late', 'num', 10),
    CA('billed_minus_paid', 'Billed minus paid hours', 'num', 'ROUND({col:billed_hours}-{col:paid_hours},2)', 11),
    CA('paid_over_billed', 'Hours paid above billed', 'num', 'MAX(0,ROUND({col:paid_hours}-{col:billed_hours},2))', 10),
    CA('leak_amount', 'Leak amount', 'money', 'ROUND({col:paid_over_billed}*{col:avg_pay_rate}*(1+{set:payroll_burden}),2)', 11),
    CA('late_rate', 'Late rate', 'pct', 'IF({col:visits}=0,0,{col:late_visits}/{col:visits})', 9), CA('missed_rate', 'Missed rate', 'pct', 'IF({col:visits}=0,0,{col:missed_visits}/{col:visits})', 9),
    STAFF_PH(3, 'office_phone', 'Office manager phone'), STAFF_PH(1, 'owner_phone', 'Owner phone')], D.agencyweeks_d(), 400,
    [A('late_rate', '> {set:late_visit_target}', 'warn'), A('missed_rate', '> {set:missed_visit_target}', 'bad'), A('leak_amount', '> 0', 'warn')]))
# 6 client hours by month
tables.append(T('climonths', 'Client Hours by Month', 'Client hours by month: billed against delivered',
    'One row per client and month: billed and delivered hours, revenue, travel cost, late and missed visits; billed minus delivered hours and the travel share of revenue fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('client', 'Client', 'clients.client', 22), LST('service', 'Service', 'svc', 18), C('billed_hours', 'Billed hours', 'num', 10),
    C('delivered_hours', 'Delivered hours', 'num', 10), C('revenue', 'Revenue', 'money', 12), C('travel_cost', 'Travel cost', 'money', 11), C('late_visits', 'Late visits', 'int', 8), C('missed_visits', 'Missed visits', 'int', 8),
    CA('billed_less_delivered', 'Billed minus delivered hours', 'num', 'ROUND({col:billed_hours}-{col:delivered_hours},2)', 11),
    CA('travel_share', 'Travel share of revenue', 'pct', 'IF({col:revenue}=0,0,{col:travel_cost}/{col:revenue})', 10)], D.climonths_d(), 1200,
    [A('billed_less_delivered', '< 0', 'bad'), A('missed_visits', '> 0', 'warn'), A('travel_share', '> 0.1', 'warn')]))
# 7 mileage
tables.append(T('mileage', 'Mileage Log', 'Mileage and paid travel log, leg by leg',
    'One row per travel leg between two visits: areas, kilometres, paid travel minutes and the two amounts; cost per leg fills in by itself. A one-person agency can use it as its own mileage record (use miles and your own rate if you prefer).', [
    C('mileage_id', 'Leg ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('caregiver', 'Caregiver', 'caregivers.name', 22), REF('client', 'Client', 'clients.client', 22), LST('from_area', 'From area', 'area', 13),
    LST('to_area', 'To area', 'area', 13), C('distance_km', 'Distance (km)', 'num', 10), C('travel_min', 'Travel minutes', 'int', 9), C('travel_pay', 'Travel pay', 'money', 10), C('mileage_pay', 'Mileage pay', 'money', 10),
    CA('cost_leg', 'Cost per leg', 'money', 'ROUND({col:travel_pay}+{col:mileage_pay},2)', 10), CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18),
    STAFF_PH(3, 'office_phone', 'Office manager phone'), STAFF_PH(8, 'payroll_phone', 'Payroll service phone')], D.mileage_d(), 1500,
    [A('cost_leg', '> 12', 'warn'), A('travel_min', '>= 38', 'warn')]))
# 8 pairs
tables.append(T('pairs', 'Travel by Area Pair', 'Travel by area pair over 12 months',
    'One row per pair of areas (30 pairs): legs, paid minutes, kilometres and cost over the last 12 months; cost per leg, minutes per leg and kilometres per leg fill in by themselves. It shows which pairs of visits should share a caregiver.', [
    C('pair_id', 'Pair ID', 'text', 9, required=True), LST('from_area', 'From area', 'area', 13), LST('to_area', 'To area', 'area', 13), C('legs', 'Legs', 'int', 8), C('minutes', 'Paid minutes', 'int', 10), C('km', 'Kilometres', 'num', 10),
    C('cost', 'Cost', 'money', 12), CA('cost_per_leg', 'Cost per leg', 'money', 'IF({col:legs}=0,0,ROUND({col:cost}/{col:legs},2))', 10), CA('min_per_leg', 'Minutes per leg', 'num', 'IF({col:legs}=0,0,ROUND({col:minutes}/{col:legs},1))', 10),
    CA('km_per_leg', 'Kilometres per leg', 'num', 'IF({col:legs}=0,0,ROUND({col:km}/{col:legs},1))', 10)], D.pairs_d(), 60, [A('cost_per_leg', '> 8', 'warn')]))
# 9 area months
tables.append(T('areamonths', 'Area Performance by Month', 'Area performance by month: late and missed rates and travel',
    'One row per area and month: visits, late and missed visits, delivered hours, travel, kilometres and amounts; late rate, missed rate, the 2-month late rate of the area and the travel share fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('area', 'Area', 'area', 13), C('visits', 'Visits', 'int', 8), C('late_visits', 'Late visits', 'int', 8), C('missed_visits', 'Missed visits', 'int', 8),
    C('delivered_hours', 'Delivered hours', 'num', 10), C('travel_min', 'Travel minutes', 'int', 9), C('distance_km', 'Distance (km)', 'num', 10), C('travel_pay', 'Travel pay', 'money', 11), C('mileage_pay', 'Mileage pay', 'money', 11),
    C('pay_amount', 'Caregiver pay', 'money', 12),
    CA('late_rate', 'Late rate', 'pct', 'IF({col:visits}=0,0,{col:late_visits}/{col:visits})', 9), CA('missed_rate', 'Missed rate', 'pct', 'IF({col:visits}=0,0,{col:missed_visits}/{col:visits})', 9),
    CA('late_rate_2m', 'Late rate of the area, last 2 months', 'pct', 'IFERROR(SUMIFS({range:areamonths.late_visits},{range:areamonths.area},{col:area},{range:areamonths.month},">="&DATE(YEAR({today}),MONTH({today})-1,1))/SUMIFS({range:areamonths.visits},{range:areamonths.area},{col:area},{range:areamonths.month},">="&DATE(YEAR({today}),MONTH({today})-1,1)),0)', 11),
    CA('travel_hours', 'Paid travel hours', 'num', 'ROUND({col:travel_min}/60,1)', 9), CA('travel_cost', 'Travel cost', 'money', 'ROUND({col:travel_pay}+{col:mileage_pay},2)', 11),
    CA('travel_share', 'Travel share of pay', 'pct', 'IF({col:pay_amount}=0,0,{col:travel_cost}/{col:pay_amount})', 10), STAFF_PH(2, 'scheduler_phone', 'Scheduler phone'), STAFF_PH(1, 'owner_phone', 'Owner phone')], D.areamonths_d(), 400,
    [A('late_rate', '> {set:late_visit_target}', 'warn'), A('missed_rate', '> {set:missed_visit_target}', 'bad'), A('travel_share', '> {set:travel_share_target}', 'warn')]))
# 10 delay reasons
tables.append(T('delays', 'Delay Reasons by Month', 'Delay reasons by month: what made visits late',
    'One row per month and delay reason: the number of late visits; the share of the month fills in by itself. It shows whether lateness is traffic, an earlier visit overrunning or wrong times on the schedule.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('reason', 'Delay reason', 'delay', 20), C('visits', 'Late visits', 'int', 9),
    CA('share', 'Share of the month', 'pct', 'IF(SUMIFS({range:delays.visits},{range:delays.month},{col:month})=0,0,{col:visits}/SUMIFS({range:delays.visits},{range:delays.month},{col:month}))', 10)], D.delays_d(), 300,
    [A('share', '>= 0.3', 'warn')]))
# 11 corrections
tables.append(T('corrections', 'Visit Corrections', 'Visit corrections: what was changed, why and by whom',
    'One row per correction to a visit record: the field, the old and the new value, the reason and who corrected it; days after the visit and the timing check fill in by themselves.', [
    C('correction_id', 'Correction ID', 'text', 10, required=True), C('date', 'Corrected on', 'date', 11), C('visit_id', 'Visit ID', 'text', 10), C('visit_date', 'Visit date', 'date', 11), REF('client', 'Client', 'clients.client', 22),
    REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('field', 'Field corrected', 'cfield', 14), C('old_value', 'Old value', 'text', 20), C('new_value', 'New value', 'text', 20), C('reason', 'Reason', 'text', 28),
    REF('corrected_by', 'Corrected by', 'team.name', 20),
    CA('days_after', 'Days after the visit', 'int', '{col:date}-{col:visit_date}', 9),
    CA('timing', 'Timing check', 'text', 'IF({col:date}-WEEKDAY({col:date},2)={col:visit_date}-WEEKDAY({col:visit_date},2),%s,%s)' % (ck('Corrected same week'), ck('Corrected later')), 16),
    CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18), CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18)], D.corrections_d(), 400,
    [A('timing', '= ' + ck('Corrected later'), 'warn'), A('days_after', '> 7', 'warn')]))
# 12 cancellations
tables.append(T('cancels', 'Client Cancellations', 'Client cancellations with notice and the charge',
    'One row per visit the client cancelled: notice in hours, whether it was charged under the agreement and the visit value; the short-notice flag and the amount charged fill in by themselves.', [
    C('cancel_id', 'Cancel ID', 'text', 9, required=True), C('date', 'Visit date', 'date', 11), C('visit_id', 'Visit ID', 'text', 10), REF('client', 'Client', 'clients.client', 22), C('notice_hours', 'Notice (hours)', 'int', 9),
    LST('notice_band', 'Notice band', 'notice', 16), C('visit_value', 'Visit value', 'money', 11), C('charged', 'Charged', 'bool', 9),
    CA('short_notice', 'Notice check', 'text', 'IF({col:notice_hours}<{set:short_notice_hours},%s,%s)' % (ck('Short notice'), ck('Enough notice')), 13),
    CA('charged_amount', 'Amount charged', 'money', 'IF({col:charged}=%s,ROUND({col:visit_value}*{set:cancel_charge_pct},2),0)' % YES, 11),
    CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18)], D.cancels_d(), 500,
    [A('short_notice', '= ' + ck('Short notice'), 'warn'), A('charged', '= ' + YES, 'good')]))
# 13 overlong visits
tables.append(T('overlong', 'Overlong Visits', 'Overlong visits: extra minutes and the unbilled money',
    'One row per visit that ran over the schedule: scheduled, actual and invoiced hours, the reason and whether the client agreed; extra minutes, unbilled hours and unbilled money fill in by themselves.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('client', 'Client', 'clients.client', 22), REF('caregiver', 'Caregiver', 'caregivers.name', 22), C('sched_hours', 'Scheduled hours', 'num', 10),
    C('actual_hours', 'Actual hours', 'num', 9), C('billed_hours', 'Invoiced hours', 'num', 9), C('reason', 'Reason', 'text', 28), C('client_agreed', 'Client agreed', 'bool', 9),
    CA('extra_minutes', 'Extra minutes', 'int', 'ROUND(({col:actual_hours}-{col:sched_hours})*60,0)', 9),
    CA('unbilled_hours', 'Unbilled hours', 'num', 'MAX(0,ROUND({col:actual_hours}-{col:billed_hours},2))', 9),
    CA('unbilled_money', 'Unbilled money', 'money', 'ROUND({col:unbilled_hours}*%s,2)' % LKN('clients.bill_rate', 'clients.client', 'client'), 11),
    CA('billing_check', 'Billing check', 'text', 'IF({col:unbilled_hours}<0.05,%s,%s)' % (ck('Billed all'), ck('Part unbilled')), 13),
    CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18), CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18)], D.overlong_d(), 300,
    [A('billing_check', '= ' + ck('Part unbilled'), 'warn'), A('unbilled_money', '> 8', 'bad')]))
# 14 time sheets
tables.append(T('timesheets', 'Time Sheet Check', 'Time sheets checked against check-ins before payroll',
    'One row per caregiver and week: the hours on the time sheet against the hours from the check-ins; the difference and the Matches, Mismatch or Not sent flag fill in by themselves. A one-person agency can use it to check its own time sheet.', [
    C('sheet_id', 'Sheet ID', 'text', 10, required=True), C('week', 'Week (Monday)', 'date', 12), REF('caregiver', 'Caregiver', 'caregivers.name', 22), C('hours_entered', 'Hours entered', 'num', 10), C('hours_checkins', 'Hours from check-ins', 'num', 11),
    C('confirmed_on', 'Confirmed on', 'date', 11),
    CA('difference', 'Difference (hours)', 'num', 'IF({col:hours_entered}="","",ROUND({col:hours_entered}-{col:hours_checkins},2))', 10),
    CA('flag', 'Time sheet check', 'text', 'IF({col:hours_entered}="",%s,IF(ABS({col:hours_entered}-{col:hours_checkins})>{set:ts_tolerance},%s,%s))' % (ck('Not sent'), ck('Mismatch'), ck('Matches')), 13),
    CA('sheets_missing', 'Time sheets still missing', 'int', 'COUNTIFS({range:timesheets.flag},%s,{range:timesheets.week},%s)' % (ck('Not sent'), THISWEEK), 10),
    CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18), STAFF_PH(3, 'office_phone', 'Office manager phone'), STAFF_PH(8, 'payroll_phone', 'Payroll service phone')], D.timesheets_d(), 600,
    [A('flag', '= ' + ck('Mismatch'), 'bad'), A('flag', '= ' + ck('Not sent'), 'warn'), A('flag', '= ' + ck('Matches'), 'good')]))
# 15-20 reference tables
tables.append(T('caregivers', 'Caregivers', 'Caregivers with their late visits in the last 30 days',
    'Your caregivers (a carer, care worker or support worker): area, employment type, pay rate and status; visits and late or missed visits in the last 30 days fill in by themselves.', [
    C('caregiver_id', 'Caregiver ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('area', 'Area', 'area', 13), LST('employment', 'Employment type', 'emp', 11), C('pay_rate', 'Pay rate per hour', 'money', 11),
    LST('status', 'Status', 'cgstatus', 10), C('hire_date', 'Hire date', 'date', 11), C('phone', 'Phone', 'text', 18),
    CA('worked_4w', 'Worked hours, last 4 weeks', 'num', 'SUMIFS({range:cgweeks.worked_hours},{range:cgweeks.caregiver},{col:name},{range:cgweeks.week},">="&(%s-21))' % THISWEEK, 11),
    CA('travel_4w', 'Travel hours, last 4 weeks', 'num', 'SUMIFS({range:cgweeks.travel_hours},{range:cgweeks.caregiver},{col:name},{range:cgweeks.week},">="&(%s-21))' % THISWEEK, 10),
    CA('visits_30d', 'Visits, last 30 days', 'int', 'COUNTIFS({range:visits.caregiver},{col:name},{range:visits.date},">="&({today}-29),{range:visits.date},"<="&{today})', 10),
    CA('late_30d', 'Late visits, last 30 days', 'int', 'COUNTIFS({range:register.caregiver},{col:name},{range:register.status},%s,{range:register.date},">="&({today}-29),{range:register.date},"<="&{today})' % tok('vstatus', 'Late'), 10),
    CA('missed_30d', 'Missed visits, last 30 days', 'int', 'COUNTIFS({range:register.caregiver},{col:name},{range:register.status},%s,{range:register.date},">="&({today}-29),{range:register.date},"<="&{today})' % tok('vstatus', 'Missed'), 10),
    CA('late_flag', 'Lateness check', 'text', 'IF({col:late_30d}>={set:repeat_late},%s,%s)' % (ck('Repeat caregiver'), ck('Single event')), 14),
    STAFF_PH(5, 'supervisor_phone', 'Field supervisor phone')], D.caregivers_d(), 100,
    [A('late_flag', '= ' + ck('Repeat caregiver'), 'bad'), A('status', '= ' + tok('cgstatus', 'Left'), 'warn')]))
tables.append(T('clients', 'Clients', 'Clients with area, service, minimum visit and billing cycle',
    'Your clients: area, main service, minimum visit, billing cycle, status and bill rate; the other pages look up the phone and the rate here.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), LST('area', 'Area', 'area', 13), LST('service', 'Service', 'svc', 18), C('min_visit_hours', 'Minimum visit (hours)', 'int', 10),
    LST('billing_cycle', 'Billing cycle', 'cycle', 11), LST('status', 'Status', 'clstatus', 9), C('phone', 'Phone', 'text', 18), C('bill_rate', 'Bill rate per hour', 'money', 11)], D.clients_d(), 200,
    [A('status', '= ' + tok('clstatus', 'Ended'), 'warn')]))
tables.append(T('services', 'Services', 'Services with the minimum visit and base rate',
    'The six services, the minimum visit in hours and the weekday base rate per hour.', [LST('service', 'Service', 'svc', 18, required=True), C('min_visit_hours', 'Minimum visit (hours)', 'int', 10), C('bill_rate', 'Base rate per hour', 'money', 12)], D.services_d(), 50))
tables.append(T('areas', 'Areas', 'Areas with their zone and average travel time',
    'The six service areas, their zone and the average travel minutes to the other areas.', [LST('area', 'Area', 'area', 13, required=True), LST('zone', 'Zone', 'zone', 9), C('avg_travel_min', 'Average travel (minutes)', 'int', 11)], D.areas_d(), 50))
tables.append(T('travel', 'Travel Times', 'Travel minutes and kilometres between areas',
    'Travel minutes and kilometres for every pair of areas (the same area included): the base for paid travel and for the mileage checks.', [
    LST('from_area', 'From area', 'area', 13, required=True), LST('to_area', 'To area', 'area', 13), C('minutes', 'Minutes', 'int', 9), C('km', 'Distance (km)', 'num', 10)], D.travel_d(), 80))
tables.append(T('team', 'Team', 'Team and outside contacts',
    'The owner-director, the care coordinator (scheduler), the office manager, the recruiter, two field supervisors and ten outside contacts with their phones.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('team', 'Team', 'team', 10), LST('pay_type', 'Pay type', 'paytype', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'num', 12), C('hourly_rate', 'Hourly rate', 'num', 11), C('speciality', 'Speciality', 'text', 30),
    C('country', 'Country', 'text', 14), C('start', 'Start date', 'date', 11)], D.team_d(), 50))
