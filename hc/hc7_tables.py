"""Home care agency suite part 7: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc7_lists import *
import hc7_data as DT


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF(prefix, n, role):
    return [CA(prefix + '_name', role + ' name', 'text', 'IFERROR(INDEX({range:team.name},%d)&"","")' % n, 20), CA(prefix + '_phone', role + ' phone', 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % n, 18)]
YES = '{list:yesno.yes}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def PCT_TEXT(c): return 'ROUND({col:%s}*100,1)&" percent"' % c

settings = [
    S('company', 'Your agency name', 'text', COMPANY), S('target_margin', 'Wanted margin share per client hour (example: use your own)', 'pct', TARGET_MARGIN),
    S('red_margin', 'Margin share below which a client is red', 'pct', 0.30), S('payroll_burden', 'Payroll burden on pay (confirm with your adviser)', 'pct', PAYROLL_BURDEN),
    S('mileage_rate', 'Mileage rate per km (or per mile: your own rate)', 'money', MILEAGE_RATE), S('cover_premium', 'Cover premium per hour for short-notice cover', 'money', COVER_PREMIUM),
    S('min_visit_hours', 'Standard minimum visit, hours', 'int', MIN_VISIT_HOURS), S('scheduler_hours', 'Weekly hours marker for a dedicated scheduler', 'int', SCHEDULER_THRESHOLD_HOURS),
    S('churn_limit', 'Client churn you accept per month', 'pct', 0.03), S('max_rise_pct', 'Largest rate rise you propose at once', 'pct', 0.08),
    S('leave_low', 'Chance a Low risk client leaves after a rise (your guess)', 'pct', 0.05), S('leave_mid', 'Chance a Medium risk client leaves after a rise (your guess)', 'pct', 0.15),
    S('leave_high', 'Chance a High risk client leaves after a rise (your guess)', 'pct', 0.35), S('hire_ad_cost', 'Job advert cost per hire', 'money', HIRE_AD_COST),
    S('background_check_cost', 'Background check cost per hire', 'money', BACKGROUND_CHECK_COST), S('onboard_hours', 'Paid onboarding hours per new caregiver', 'int', ONBOARD_HOURS),
    S('replace_extra', 'Other cost to replace a caregiver (supervisor time, cover)', 'money', 2000), S('notice_days', 'Days of notice before a rate change', 'int', 30),
    S('holiday_name', 'Next holiday (bank holiday) name', 'text', DT.HOLIDAY['holiday']), S('holiday_on', 'Next holiday date', 'date', DT.HOLIDAY['date'])]
assert 3 <= len(settings) <= 20

tables = []
def add(*a, **k): tables.append(T(*a, **k))

# 1 Client margin now
add('margin', 'Client Margin', 'Client margin now: live margin per client hour, worst first',
    'One row per active client from the last 90 days of visits: type the rate, pay and extras per hour; loaded cost, margin per hour and per week, margin share, check and rank fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 24), LST('payer', 'Payer', 'payer', 18), LST('service', 'Service', 'svc', 18), LST('area', 'Area', 'area', 12),
    C('weekly_hours', 'Weekly hours', 'num', 9), C('bill_rate', 'Bill rate per hour', 'money', 11), C('pay_hour', 'Pay per hour', 'money', 11), C('travel_hour', 'Paid travel per hour', 'num', 11),
    C('mileage_hour', 'Mileage per hour', 'num', 11), C('ot_hour', 'Overtime per hour', 'num', 11), C('cover_hour', 'Cover premium per hour', 'num', 11), C('review_on', 'Review date', 'date', 11),
    CA('loaded_cost', 'Loaded cost per hour', 'money', '({col:pay_hour}+{col:travel_hour}+{col:ot_hour}+{col:cover_hour})*(1+{set:payroll_burden})+{col:mileage_hour}', 12),
    CA('margin_hour', 'Margin per hour', 'money', '{col:bill_rate}-{col:loaded_cost}', 12), CA('margin_week', 'Margin per week', 'money', '{col:margin_hour}*{col:weekly_hours}', 12),
    CA('revenue_week', 'Revenue per week', 'money', '{col:bill_rate}*{col:weekly_hours}', 12), CA('margin_pct', 'Margin share', 'pct', 'IF({col:bill_rate}>0,{col:margin_hour}/{col:bill_rate},0)', 10),
    CA('flag', 'Margin check', 'text', 'IF({col:margin_pct}>={set:target_margin},%s,IF({col:margin_pct}>={set:red_margin},%s,IF({col:margin_pct}>=0,%s,%s)))' % (
        ck('On target'), ck('Below target'), ck('Below 30 percent'), ck('Negative margin')), 16),
    CA('gap_week', 'Gap to the target per week', 'money', 'MAX(0,{set:target_margin}*{col:revenue_week}-{col:margin_week})', 12),
    CA('rate_needed', 'Rate for the target margin', 'money', '{col:loaded_cost}/(1-{set:target_margin})', 12),
    CA('order_key', 'Sort key for the rank', 'num', '{col:margin_pct}+VALUE(RIGHT({col:client_id},3))/1000000000', 9),
    CA('rank', 'Worst-first rank', 'int', '1+COUNTIFS({range:margin.order_key},"<"&{col:order_key})', 9),
    CA('share_pct', 'Margin share in percent', 'num', 'ROUND({col:margin_pct}*100,1)', 10),
    CA('below_count', 'Clients below the target', 'int', 'COUNTIFS({range:margin.margin_pct},"<"&{set:target_margin})', 10),
    CA('weak3_gap', 'Gap of the weakest three per week', 'money', 'ROUND(SUMIFS({range:margin.gap_week},{range:margin.rank},"<=3"),0)', 12),
    CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('sched', 2, 'Scheduler') + STAFF('office', 3, 'Office manager') + STAFF('owner', 1, 'Owner'),
    DT.margin_d(), 300, [A('flag', '= ' + ck('Negative margin'), 'bad'), A('flag', '= ' + ck('Below 30 percent'), 'bad'), A('flag', '= ' + ck('Below target'), 'warn'), A('flag', '= ' + ck('On target'), 'good')])

# 2 Client months
add('cmonths', 'Client Months', 'Client months: revenue, cost and margin per client per month',
    'One row per client per month: type billed hours, revenue, cost and the extras; margin and margin share fill in by themselves. A sample of the clients is shown.', [
    C('month_id', 'Row ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('client', 'Client', 'clients.client', 24), LST('service', 'Service', 'svc', 18), LST('payer', 'Payer', 'payer', 18),
    LST('area', 'Area', 'area', 12), C('billed_hours', 'Billed hours', 'num', 10), C('revenue', 'Revenue', 'money', 12), C('cost', 'Cost', 'money', 12), C('travel_cost', 'Travel and mileage cost', 'num', 12),
    C('overtime_cost', 'Overtime cost', 'num', 12), C('late_visits', 'Late visits', 'int', 9), C('missed_visits', 'Missed visits', 'int', 9), C('caregivers', 'Caregivers', 'int', 10),
    CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 12), CA('margin_pct', 'Margin share', 'pct', 'IF({col:revenue}>0,({col:revenue}-{col:cost})/{col:revenue},0)', 10),
    CA('margin_hour', 'Margin per hour', 'money', 'IF({col:billed_hours}>0,({col:revenue}-{col:cost})/{col:billed_hours},0)', 11), CA('share_pct', 'Margin share in percent', 'num', 'ROUND({col:margin_pct}*100,1)', 10),
    CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('mkt', 13, 'Marketing helper'), DT.cmonths_d(), 900,
    [A('margin_pct', '< {set:red_margin}', 'bad'), A('margin_pct', '>= {set:target_margin}', 'good'), A('caregivers', '> 5', 'warn')])

# 3 Visits with margin
add('visits', 'Visits with Margin', 'Visits with margin: charge against loaded pay cost',
    'The most recent completed visits: type the charge, pay, travel, mileage, overtime, cover premium and burden; cost, margin and margin per hour fill in by themselves.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('client', 'Client', 'clients.client', 24), LST('service', 'Service', 'svc', 18), LST('band', 'Time band', 'band', 10),
    C('caregiver', 'Caregiver', 'text', 22), C('billed_hours', 'Billed hours', 'num', 9), C('actual_hours', 'Hours worked', 'num', 9), C('charge', 'Charge', 'money', 11), C('pay', 'Pay', 'money', 11),
    C('travel_pay', 'Paid travel', 'num', 10), C('mileage_pay', 'Mileage', 'num', 10), C('overtime_pay', 'Overtime pay', 'num', 10), C('cover_premium', 'Cover premium', 'num', 10), C('burden', 'Payroll burden', 'money', 10),
    CA('cost', 'Loaded cost', 'money', '{col:pay}+{col:travel_pay}+{col:mileage_pay}+{col:overtime_pay}+{col:cover_premium}+{col:burden}', 11),
    CA('margin', 'Margin', 'money', '{col:charge}-({col:pay}+{col:travel_pay}+{col:mileage_pay}+{col:overtime_pay}+{col:cover_premium}+{col:burden})', 11),
    CA('margin_hour', 'Margin per billed hour', 'money', 'IF({col:billed_hours}>0,({col:charge}-({col:pay}+{col:travel_pay}+{col:mileage_pay}+{col:overtime_pay}+{col:cover_premium}+{col:burden}))/{col:billed_hours},0)', 11),
    CA('margin_pct', 'Margin share', 'pct', 'IF({col:charge}>0,({col:charge}-({col:pay}+{col:travel_pay}+{col:mileage_pay}+{col:overtime_pay}+{col:cover_premium}+{col:burden}))/{col:charge},0)', 10)],
    DT.visits_d(), 1500, [A('margin_pct', '< 0', 'bad'), A('margin_pct', '>= {set:target_margin}', 'good')])

# 4 Service margin by month
add('svcmonth', 'Service Margin', 'Service margin by month',
    'One row per service per month from the visits: revenue, cost, travel and overtime are typed; margin, margin share and margin per hour fill in by themselves.', [
    C('month_id', 'Row ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('service', 'Service', 'svc', 18), C('visits', 'Visits', 'int', 9), C('billed_hours', 'Billed hours', 'num', 10),
    C('revenue', 'Revenue', 'money', 12), C('cost', 'Cost', 'money', 12), C('travel_cost', 'Travel and mileage cost', 'num', 12), C('overtime_cost', 'Overtime cost', 'num', 12),
    CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 12), CA('margin_pct', 'Margin share', 'pct', 'IF({col:revenue}>0,({col:revenue}-{col:cost})/{col:revenue},0)', 10),
    CA('margin_hour', 'Margin per hour', 'money', 'IF({col:billed_hours}>0,({col:revenue}-{col:cost})/{col:billed_hours},0)', 11), CA('share_pct', 'Margin share in percent', 'num', 'ROUND({col:margin_pct}*100,1)', 10),
    CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('owner', 1, 'Owner') + STAFF('acct', 7, 'Accountant'), DT.svcmonth_d(), 400,
    [A('margin_pct', '< {set:red_margin}', 'bad'), A('margin_pct', '>= {set:target_margin}', 'good')])

# 5 Area margin by month
add('areamonth', 'Area Margin', 'Area margin by month',
    'One row per area per month: revenue, cost and paid travel minutes are typed; margin, margin share and travel minutes per visit fill in by themselves.', [
    C('month_id', 'Row ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('area', 'Area', 'area', 12), C('visits', 'Visits', 'int', 9), C('billed_hours', 'Billed hours', 'num', 10),
    C('revenue', 'Revenue', 'money', 12), C('cost', 'Cost', 'money', 12), C('travel_min', 'Travel minutes', 'int', 10),
    CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 12), CA('margin_pct', 'Margin share', 'pct', 'IF({col:revenue}>0,({col:revenue}-{col:cost})/{col:revenue},0)', 10),
    CA('travel_per_visit', 'Travel minutes per visit', 'num', 'IF({col:visits}>0,{col:travel_min}/{col:visits},0)', 11)], DT.areamonth_d(), 400,
    [A('margin_pct', '< {set:red_margin}', 'bad'), A('margin_pct', '>= {set:target_margin}', 'good')])

# 6 Payer margin by month
add('paymonth', 'Payer Margin', 'Payer margin by month',
    'One row per payer per month: billed hours, revenue and cost are typed; margin, margin share and the points behind private pay fill in by themselves.', [
    C('month_id', 'Row ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('payer', 'Payer', 'payer', 18), C('billed_hours', 'Billed hours', 'num', 10), C('revenue', 'Revenue', 'money', 12),
    C('cost', 'Cost', 'money', 12), CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 12), CA('margin_pct', 'Margin share', 'pct', 'IF({col:revenue}>0,({col:revenue}-{col:cost})/{col:revenue},0)', 10),
    CA('rate_hour', 'Revenue per billed hour', 'money', 'IF({col:billed_hours}>0,{col:revenue}/{col:billed_hours},0)', 11),
    CA('points_behind', 'Points behind private pay', 'num', 'ROUND(100*(IFERROR(SUMIFS({range:paymonth.margin},{range:paymonth.month},{col:month},{range:paymonth.payer},%s)/SUMIFS({range:paymonth.revenue},{range:paymonth.month},{col:month},{range:paymonth.payer},%s),0)-{col:margin_pct}),1)' % (tok('payer', 'Private pay'), tok('payer', 'Private pay')), 11),
    CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('owner', 1, 'Owner'), DT.paymonth_d(), 300,
    [A('margin_pct', '< {set:red_margin}', 'bad'), A('margin_pct', '>= {set:target_margin}', 'good')])

# 7 Rate card
add('ratecard', 'Rate Card', 'Rate card by service and time band',
    'The bill rate and the standard pay rate for each service and time band (weekday rates are before any payer share); loaded pay, margin per hour and margin share fill in by themselves.', [
    C('rate_id', 'Rate ID', 'text', 9, required=True), LST('service', 'Service', 'svc', 18), LST('band', 'Time band', 'band', 10), C('bill_rate', 'Bill rate per hour', 'money', 12), C('pay_rate', 'Pay rate per hour', 'money', 12),
    CA('loaded_pay', 'Loaded pay per hour', 'money', '{col:pay_rate}*(1+{set:payroll_burden})', 12), CA('margin_hour', 'Margin per hour', 'money', '{col:bill_rate}-{col:pay_rate}*(1+{set:payroll_burden})', 12),
    CA('margin_pct', 'Margin share', 'pct', 'IF({col:bill_rate}>0,({col:bill_rate}-{col:pay_rate}*(1+{set:payroll_burden}))/{col:bill_rate},0)', 10)], DT.ratecard_d(), 100,
    [A('margin_pct', '< {set:red_margin}', 'bad'), A('margin_pct', '>= {set:target_margin}', 'good')])

# 8 Rate rise proposals
add('rises', 'Rate Rise Proposals', 'Rate rise proposals with the chance the client leaves',
    'One row per client: type the proposed rise and your risk marker; new rate, income gain a year, expected net effect (gain if they stay, margin lost if they leave) and the verdict fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), REF('client', 'Client', 'margin.client', 24), C('rise_pct', 'Proposed rise', 'pct', 9), LST('risk', 'Risk of leaving', 'risk', 10),
    C('effective_on', 'New rate from', 'date', 12), C('notice_on', 'Notice sent on', 'date', 12), C('family_phone', 'Family contact phone', 'text', 18),
    CA('current_rate', 'Current rate per hour', 'money', LKN('margin.bill_rate', 'margin.client', 'client'), 11), CA('hours', 'Weekly hours', 'num', LKN('margin.weekly_hours', 'margin.client', 'client'), 9),
    CA('margin_pct', 'Margin share now', 'pct', LKN('margin.margin_pct', 'margin.client', 'client'), 10), CA('margin_week', 'Margin per week now', 'money', LKN('margin.margin_week', 'margin.client', 'client'), 11),
    CA('locked', 'Rate locked', 'text', LKT('clients.rate_locked', 'clients.client', 'client'), 9),
    CA('new_rate', 'New rate per hour', 'money', '{col:current_rate}*(1+{col:rise_pct})', 11), CA('gain_year', 'Income gain a year if they stay', 'money', '{col:hours}*52*{col:current_rate}*{col:rise_pct}', 13),
    CA('leave_chance', 'Chance they leave', 'pct', 'IF({col:risk}=%s,{set:leave_low},IF({col:risk}=%s,{set:leave_mid},{set:leave_high}))' % (tok('risk', 'Low'), tok('risk', 'Medium')), 10),
    CA('expected_net', 'Expected net effect a year', 'money', 'IF({col:locked}=%s,0,(1-{col:leave_chance})*{col:gain_year}-{col:leave_chance}*{col:margin_week}*52)' % YES, 13),
    CA('verdict', 'Verdict', 'text', 'IF({col:locked}=%s,%s,IF({col:rise_pct}<=0,%s,IF({col:expected_net}<=0,%s,IF({col:expected_net}<0.25*{col:gain_year},%s,%s))))' % (YES, ck('Rate locked'), ck('Hold'), ck('Hold'), ck('Raise less'), ck('Raise')), 13),
    CA('notice_check', 'Notice check', 'text', 'IF({col:notice_on}<>"",%s,IF({col:effective_on}-{today}<={set:notice_days}+14,%s,%s))' % (ck('Notice sent'), ck('Notice due'), ck('Not due yet')), 12),
    CA('order_key', 'Sort key for the raise order', 'num', '{col:expected_net}+VALUE(RIGHT({col:client_id},3))/1000000000', 16),
    CA('net_rank', 'Raise order', 'int', '1+COUNTIFS({range:rises.order_key},">"&{col:order_key})', 9),
    CA('gain_total', 'Expected gain, all clients', 'money', 'ROUND(SUMIFS({range:rises.expected_net},{range:rises.expected_net},">0"),0)', 12),
    CA('notice_count', 'Notices still to send', 'int', 'COUNTIFS({range:rises.notice_check},%s)' % ck('Notice due'), 9), CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18),
    CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('office', 3, 'Office manager') + STAFF('sup', 5, 'Field supervisor') + STAFF('owner', 1, 'Owner'),
    DT.rises_d(), 300, [A('verdict', '= ' + ck('Raise'), 'good'), A('verdict', '= ' + ck('Raise less'), 'warn'), A('verdict', '= ' + ck('Hold'), 'bad'), A('notice_check', '= ' + ck('Notice due'), 'warn')])
for _c in tables[-1]['columns']:
    if _c['key'] == 'sup_name': _c['formula'] = 'IFERROR(INDEX({range:team.name},5)&"","")'

# 9 Rate rise history
add('risehist', 'Rate Rise History', 'Rate rise history: what clients did after a rise',
    'One row per rate rise already made: the old and new rate and what the client did (accepted, talked it over, cut hours or left); the rise share and the hours kept after 3 months fill in by themselves.', [
    C('rise_id', 'Rise ID', 'text', 9, required=True), REF('client', 'Client', 'clients.client', 24), C('date', 'Rise date', 'date', 11), C('old_rate', 'Old rate per hour', 'money', 11), C('new_rate', 'New rate per hour', 'money', 11),
    LST('outcome', 'Outcome', 'outcome', 12), C('hours_before', 'Weekly hours before', 'num', 10), C('hours_after', 'Weekly hours after 3 months', 'num', 11),
    CA('rise_share', 'Rise share', 'pct', 'IF({col:old_rate}>0,{col:new_rate}/{col:old_rate}-1,0)', 9), CA('hours_kept', 'Hours kept', 'pct', 'IF({col:hours_before}>0,{col:hours_after}/{col:hours_before},0)', 9)],
    DT.risehist_d(), 150, [A('outcome', '= ' + tok('outcome', 'Left'), 'bad'), A('outcome', '= ' + tok('outcome', 'Hours cut'), 'warn'), A('outcome', '= ' + tok('outcome', 'Accepted'), 'good')])

# 10 Clients
add('clients', 'Clients', 'Clients: rate, minimum visit, start, end and reason',
    'One row per client, active and ended: payer, service, weekly hours, rate, minimum visit, start and end with the reason, and whether the rate is locked; months with the agency fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('phone', 'Phone', 'text', 18), LST('payer', 'Payer', 'payer', 18), LST('service', 'Service', 'svc', 18), LST('area', 'Area', 'area', 12),
    C('weekly_hours', 'Weekly hours', 'num', 9), C('bill_rate', 'Bill rate per hour', 'money', 11), C('min_visit_hours', 'Minimum visit, hours', 'int', 9), C('start_date', 'Start date', 'date', 11),
    LST('status', 'Status', 'clstatus', 9), C('end_date', 'End date', 'date', 11), LST('end_reason', 'End reason', 'endrsn', 16), C('rate_locked', 'Rate locked', 'bool', 8),
    CA('months_with_us', 'Months with the agency', 'num', 'ROUND((IF({col:end_date}="",{today},{col:end_date})-{col:start_date})/30.4,1)', 10),
    CA('holiday_name', 'Next holiday', 'text', '{set:holiday_name}&""', 18), CA('holiday_on', 'Next holiday date', 'date', '{set:holiday_on}', 11),
    CA('holiday_rate', 'Holiday rate per hour', 'money', 'IFERROR(ROUND({col:bill_rate}*SUMIFS({range:ratecard.bill_rate},{range:ratecard.service},{col:service},{range:ratecard.band},%s)/SUMIFS({range:ratecard.bill_rate},{range:ratecard.service},{col:service},{range:ratecard.band},%s),2),"")' % (tok('band', 'Holiday'), tok('band', 'Weekday')), 11),
    CA('company', 'Agency', 'text', '{set:company}&""', 22)], DT.clients_d(), 300, [A('status', '= ' + tok('clstatus', 'Ended'), 'warn'), A('rate_locked', '= ' + YES, 'warn')])

# 11 Client hours growth
add('growth', 'Client Hours Growth', 'Client hours growth and loss by month',
    'One row per month: clients started and ended, hours added and lost, weekly hours at month end and churn rate are typed; net hours, the forecast and the marker fill in by themselves.', [
    C('month_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('clients_started', 'Clients started', 'int', 9), C('clients_ended', 'Clients ended', 'int', 9), C('hours_added', 'Weekly hours added', 'num', 10),
    C('hours_lost', 'Weekly hours lost', 'num', 10), C('active_clients', 'Active clients', 'int', 9), C('weekly_hours_end', 'Weekly hours at month end', 'num', 11), C('churn_rate', 'Churn rate', 'pct', 9),
    CA('net_hours', 'Net hours', 'num', '{col:hours_added}-{col:hours_lost}', 9), CA('net_clients', 'Net clients', 'int', '{col:clients_started}-{col:clients_ended}', 9),
    CA('churn_pct', 'Churn in percent', 'num', 'ROUND({col:churn_rate}*100,1)', 10),
    CA('hours6', 'Forecast weekly hours in 6 months', 'num', 'ROUND(SUMIFS({range:forecast.weekly_end},{range:forecast.scenario},%s,{range:forecast.month},DATE(YEAR({today}),MONTH({today})+6,1)),0)' % tok('scen', 'Base'), 12),
    CA('months_marker', 'Months to the hours marker', 'int', 'IFERROR(IF(AVERAGEIFS({range:growth.net_hours},{range:growth.month},">="&DATE(YEAR({today}),MONTH({today})-6,1),{range:growth.month},"<"&%s)<=0,"",MAX(0,ROUNDUP(({set:scheduler_hours}-SUMIFS({range:clients.weekly_hours},{range:clients.status},%s))/AVERAGEIFS({range:growth.net_hours},{range:growth.month},">="&DATE(YEAR({today}),MONTH({today})-6,1),{range:growth.month},"<"&%s),0))),"")' % (MS, tok('clstatus', 'Active'), MS), 10),
    CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('owner', 1, 'Owner') + STAFF('broker', 9, 'Insurance broker'), DT.growth_d(), 120,
    [A('churn_rate', '> {set:churn_limit}', 'bad'), A('net_hours', '< 0', 'warn'), A('net_hours', '> 0', 'good')])

# 12 Client starts
add('starts', 'Client Starts', 'Client starts: hours at the start and after 90 days',
    'One row per new client: weekly hours at the start, hours after 90 days (blank while the client is newer) and the source; growth in hours fills in by itself.', [
    C('client_id', 'Client ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 24), C('start_date', 'Start date', 'date', 11), C('hours_start', 'Weekly hours at start', 'num', 10),
    C('hours_90', 'Weekly hours after 90 days', 'num', 11), LST('source', 'Source', 'enqsrc', 16),
    CA('growth_hours', 'Growth in hours', 'num', 'IF({col:hours_90}="","",{col:hours_90}-{col:hours_start})', 9), CA('growth_pct', 'Growth share', 'pct', 'IF({col:hours_90}="","",({col:hours_90}-{col:hours_start})/{col:hours_start})', 9),
    CA('days_since', 'Days since start', 'int', '{today}-{col:start_date}', 9), CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('sched', 2, 'Scheduler'), DT.starts_d(), 200,
    [A('growth_hours', '< 0', 'warn'), A('growth_hours', '> 0', 'good')])

# 13 Client ends
add('ends', 'Client Ends', 'Client ends: hours lost, reason and tenure',
    'One row per client who ended care: end date, weekly hours lost and the reason; tenure in days and revenue lost a year fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 24), C('end_date', 'End date', 'date', 11), C('hours_lost', 'Weekly hours lost', 'num', 10), LST('reason', 'Reason', 'endrsn', 16),
    CA('tenure_days', 'Tenure, days', 'int', 'IFERROR({col:end_date}-INDEX({range:clients.start_date},MATCH({col:client_id},{range:clients.client_id},0)),"")', 9),
    CA('same_reason', 'Clients with the same reason', 'int', 'COUNTIFS({range:ends.reason},{col:reason})', 10),
    CA('revenue_lost', 'Revenue lost a year', 'money', 'IFERROR(ROUND({col:hours_lost}*52*INDEX({range:clients.bill_rate},MATCH({col:client_id},{range:clients.client_id},0)),0),"")', 12),
    CA('phone', 'Client phone', 'text', 'IFERROR(INDEX({range:clients.phone},MATCH({col:client_id},{range:clients.client_id},0))&"","")', 18), CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('sup', 6, 'Field supervisor'),
    DT.ends_d(), 150, [A('reason', '= ' + tok('endrsn', 'Price'), 'warn'), A('reason', '= ' + tok('endrsn', 'Service issues'), 'bad')])

# 14 Churn reasons by month
add('reasons', 'Churn Reasons', 'Churn reasons by month',
    'One row per month and reason: clients ended and weekly hours lost; the share of that month and the hours per client fill in by themselves.', [
    C('reason_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('reason', 'Reason', 'endrsn', 16), C('clients', 'Clients ended', 'int', 9), C('hours_lost', 'Weekly hours lost', 'num', 10),
    CA('share', 'Share of the month', 'pct', 'IFERROR({col:clients}/SUMIFS({range:reasons.clients},{range:reasons.month},{col:month}),0)', 10), CA('hours_per_client', 'Hours per client', 'num', 'IF({col:clients}>0,{col:hours_lost}/{col:clients},0)', 10)],
    DT.reasons_d(), 150, [A('reason', '= ' + tok('endrsn', 'Price'), 'warn')])

# 15 Hours forecast
add('forecast', 'Hours Forecast', 'Hours forecast: weekly hours by scenario',
    'Type the new and lost weekly hours you expect each month for Base, Best and Worst; weekly hours at month end add up from today\'s weekly hours by themselves.', [
    C('fc_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('scenario', 'Scenario', 'scen', 10), C('new_hours', 'New weekly hours', 'num', 10), C('lost_hours', 'Lost weekly hours', 'num', 10),
    CA('net_month', 'Net hours in the month', 'num', '{col:new_hours}-{col:lost_hours}', 10),
    CA('weekly_end', 'Weekly hours at month end', 'num', 'SUMIFS({range:clients.weekly_hours},{range:clients.status},%s)+SUMIFS({range:forecast.new_hours},{range:forecast.scenario},{col:scenario},{range:forecast.month},"<="&{col:month})-SUMIFS({range:forecast.lost_hours},{range:forecast.scenario},{col:scenario},{range:forecast.month},"<="&{col:month})' % tok('clstatus', 'Active'), 11),
    CA('marker_gap', 'Hours to the marker', 'num', '{set:scheduler_hours}-SUMIFS({range:clients.weekly_hours},{range:clients.status},%s)-SUMIFS({range:forecast.new_hours},{range:forecast.scenario},{col:scenario},{range:forecast.month},"<="&{col:month})+SUMIFS({range:forecast.lost_hours},{range:forecast.scenario},{col:scenario},{range:forecast.month},"<="&{col:month})' % tok('clstatus', 'Active'), 11)],
    DT.forecast_d(), 100, [A('marker_gap', '<= 0', 'good')])

# 16 Pay rate scenarios
add('payscen', 'Pay Rate Scenarios', 'Pay rate scenarios: margin, cost and turnover saving',
    'One row per pay rise: the rise per hour, the share of hours it covers and your turnover guess; margin after the rise, cost, saving and the verdict fill in by themselves.', [
    C('scenario_id', 'Row ID', 'text', 9, required=True), LST('step', 'Pay step', 'step', 11), C('pay_rise', 'Pay rise per hour', 'money', 10), C('covers', 'Share of hours covered', 'pct', 10), C('turnover_change', 'Change in yearly turnover (your guess)', 'pct', 12),
    CA('delta_hour', 'Cost per client hour', 'money', '{col:pay_rise}*{col:covers}*(1+{set:payroll_burden})', 10),
    CA('new_margin_hour', 'Margin per hour after the rise', 'money', 'SUM({range:margin.margin_week})/SUM({range:margin.weekly_hours})-{col:delta_hour}', 11),
    CA('new_margin_pct', 'Margin share after the rise', 'pct', '(SUM({range:margin.margin_week})/SUM({range:margin.weekly_hours})-{col:delta_hour})/(SUM({range:margin.revenue_week})/SUM({range:margin.weekly_hours}))', 11),
    CA('rate_rise_needed', 'Bill rate rise clients would need', 'pct', '{col:delta_hour}/((SUM({range:margin.revenue_week})-SUM({range:margin.margin_week}))/SUM({range:margin.weekly_hours}))', 11),
    CA('cost_year', 'Cost of the rise a year', 'money', 'ROUND({col:delta_hour}*SUM({range:margin.weekly_hours})*52,0)', 12),
    CA('saving_year', 'Turnover saving a year', 'money', 'ROUND(-{col:turnover_change}*COUNTIFS({range:paycg.status},%s)*({set:hire_ad_cost}+{set:background_check_cost}+{set:onboard_hours}*AVERAGEIFS({range:paycg.pay_rate},{range:paycg.status},%s)*(1+{set:payroll_burden})+{set:replace_extra}),0)' % (tok('cgstatus', 'Active'), tok('cgstatus', 'Active')), 12),
    CA('net_year', 'Net cost or saving a year', 'money', '{col:saving_year}-{col:cost_year}', 12),
    CA('verdict', 'Verdict', 'text', 'IF({col:saving_year}-{col:cost_year}>=0,%s,%s)' % (ck('Worth it'), ck('Not yet')), 10),
    CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('owner', 1, 'Owner'), DT.payscen_d(), 60,
    [A('verdict', '= ' + ck('Worth it'), 'good'), A('verdict', '= ' + ck('Not yet'), 'warn')])

# 17 Caregiver pay rates
add('paycg', 'Caregiver Pay Rates', 'Caregiver pay rates and the planned pay change',
    'One row per caregiver: pay rate, hire date, status and any planned new pay rate with its start date; loaded pay and months with the agency fill in by themselves.', [
    C('caregiver_id', 'Caregiver ID', 'text', 11, required=True), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18), LST('employment', 'Employment', 'emp', 11), C('pay_rate', 'Pay rate per hour', 'money', 11),
    C('hire_date', 'Hire date', 'date', 11), LST('status', 'Status', 'cgstatus', 10), C('new_pay_rate', 'New pay rate per hour', 'money', 11), C('change_on', 'New rate from', 'date', 11),
    CA('loaded_pay', 'Loaded pay per hour', 'money', '{col:pay_rate}*(1+{set:payroll_burden})', 11), CA('months_with_us', 'Months with the agency', 'num', 'ROUND(({today}-{col:hire_date})/30.4,1)', 10),
    CA('step_change', 'Planned change per hour', 'money', 'IF({col:new_pay_rate}="","",{col:new_pay_rate}-{col:pay_rate})', 10), CA('mileage_rate', 'Mileage rate per km', 'money', '{set:mileage_rate}', 10),
    CA('company', 'Agency', 'text', '{set:company}&""', 22)], DT.paycg_d(), 200, [A('status', '= ' + tok('cgstatus', 'Left'), 'warn')])

# 18 Minimum visit check
add('minvisit', 'Minimum Visit Check', 'Minimum visit check: billed hours against worked hours',
    'One row per client from the last 90 days: type the visits, the visits at the minimum, hours, travel and kilometres; the true margin per visit, the gap in hours and the flag fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 24), C('min_visit_hours', 'Minimum visit, hours', 'int', 9), C('visits_90', 'Visits, last 90 days', 'int', 9),
    C('visits_min', 'Visits at the minimum', 'int', 9), C('avg_hours', 'Average hours worked', 'num', 9), C('avg_billed', 'Average hours billed', 'num', 9), C('avg_travel_min', 'Average travel minutes', 'num', 9),
    C('avg_km', 'Average km per visit', 'num', 9), C('pay_rate', 'Average pay rate per hour', 'money', 11), C('reviewed_on', 'Reviewed on', 'date', 11), C('new_min_visit', 'New minimum, hours', 'int', 9), C('change_on', 'Change from', 'date', 11),
    CA('bill_rate', 'Bill rate per hour', 'money', LKN('margin.bill_rate', 'margin.client', 'client'), 10), CA('hours_with_travel', 'Hours worked plus travel', 'num', '{col:avg_hours}+{col:avg_travel_min}/60', 10),
    CA('gap_hours', 'Billed minus worked plus travel', 'num', '{col:avg_billed}-({col:avg_hours}+{col:avg_travel_min}/60)', 10),
    CA('rev_visit', 'Revenue per visit', 'money', '{col:avg_billed}*{col:bill_rate}', 10),
    CA('cost_visit', 'Loaded cost per visit', 'money', '({col:avg_hours}+{col:avg_travel_min}/60)*{col:pay_rate}*(1+{set:payroll_burden})+{col:avg_km}*{set:mileage_rate}', 10),
    CA('margin_visit', 'True margin per visit', 'money', '{col:avg_billed}*{col:bill_rate}-(({col:avg_hours}+{col:avg_travel_min}/60)*{col:pay_rate}*(1+{set:payroll_burden})+{col:avg_km}*{set:mileage_rate})', 10),
    CA('margin_visit_pct', 'Margin share per visit', 'pct', 'IF({col:avg_billed}*{col:bill_rate}>0,({col:avg_billed}*{col:bill_rate}-(({col:avg_hours}+{col:avg_travel_min}/60)*{col:pay_rate}*(1+{set:payroll_burden})+{col:avg_km}*{set:mileage_rate}))/({col:avg_billed}*{col:bill_rate}),0)', 10),
    CA('short_share', 'Share of visits at the minimum', 'pct', 'IF({col:visits_90}>0,{col:visits_min}/{col:visits_90},0)', 10),
    CA('flag', 'Loss check', 'text', 'IF(AND({col:short_share}>=0.25,({col:avg_billed}*{col:bill_rate}-(({col:avg_hours}+{col:avg_travel_min}/60)*{col:pay_rate}*(1+{set:payroll_burden})+{col:avg_km}*{set:mileage_rate}))<{set:red_margin}*{col:avg_billed}*{col:bill_rate}),%s,%s)' % (ck('Loss on short visits'), ck('Fine')), 16),
    CA('travel_charge', 'Travel charge to cover a visit', 'money', 'ROUND(({col:avg_travel_min}/60*{col:pay_rate}*(1+{set:payroll_burden})+{col:avg_km}*{set:mileage_rate}),1)', 10),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18), CA('company', 'Agency', 'text', '{set:company}&""', 22)] + STAFF('sched', 2, 'Scheduler') + STAFF('office', 3, 'Office manager'),
    DT.minvisit_d(), 300, [A('flag', '= ' + ck('Loss on short visits'), 'bad'), A('flag', '= ' + ck('Fine'), 'good')])

# 19 Overtime, travel and cover by client
add('otravel', 'Overtime and Travel', 'Overtime, travel and cover by client',
    'One row per client from the last 90 days: type hours, revenue, overtime, paid travel, mileage and cover premium; cost per hour and the share of revenue fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 24), C('period_end', 'Period ends', 'date', 11), C('hours', 'Billed hours', 'num', 9), C('revenue', 'Revenue', 'money', 12),
    C('overtime_cost', 'Overtime cost', 'num', 10), C('travel_pay', 'Paid travel', 'num', 10), C('mileage_pay', 'Mileage', 'num', 10), C('cover_cost', 'Cover premium', 'num', 10),
    CA('extra_cost', 'Extras in total', 'money', '{col:overtime_cost}+{col:travel_pay}+{col:mileage_pay}+{col:cover_cost}', 10),
    CA('cost_hour', 'Extras per hour', 'money', 'IF({col:hours}>0,({col:overtime_cost}+{col:travel_pay}+{col:mileage_pay}+{col:cover_cost})/{col:hours},0)', 10),
    CA('share_revenue', 'Share of revenue', 'pct', 'IF({col:revenue}>0,({col:overtime_cost}+{col:travel_pay}+{col:mileage_pay}+{col:cover_cost})/{col:revenue},0)', 10),
    CA('margin_pct', 'Margin share', 'pct', LKN('margin.margin_pct', 'margin.client', 'client'), 10), CA('weekly_hours', 'Weekly hours', 'num', LKN('margin.weekly_hours', 'margin.client', 'client'), 9)],
    DT.otravel_d(), 300, [A('share_revenue', '> 0.08', 'bad'), A('share_revenue', '> 0.05', 'warn')])

# 20 Team
add('team', 'Team', 'Team and outside contacts',
    'The owner-director, scheduler and care coordinator, office manager, recruiter, two field supervisors and ten outside contacts; messages in this workbook look up their phones here.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('team', 'Team', 'team', 11), LST('pay_type', 'Pay type', 'paytype', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'Email', 'text', 26), C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'num', 11), C('hourly_rate', 'Hourly rate', 'num', 10), C('speciality', 'Speciality', 'text', 30),
    C('country', 'Country', 'text', 14), C('start', 'Start date', 'date', 11)], DT.team_d(), 60)
assert len(tables) == 20

# every table that sends a message needs the agency name
_need = {'margin', 'cmonths', 'svcmonth', 'paymonth', 'rises', 'clients', 'growth', 'starts', 'ends', 'payscen', 'paycg', 'minvisit'}
for t in tables:
    if t['key'] in _need and not any(c['key'] == 'company' for c in t['columns']): t['columns'].append(CA('company', 'Agency', 'text', '{set:company}&""', 22))
