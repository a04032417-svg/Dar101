"""Home care agency suite part 1: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc1_lists import *
import hc1_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF_PH(idx, k): return CA(k, 'Phone to message', 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % idx, 18)
def STAFF_NM(idx, k, label): return CA(k, label, 'text', 'IFERROR(INDEX({range:team.name},%d)&"","")' % idx, 20)
YES = '{list:yesno.yes}'
MON = 'DATE(YEAR({col:month}),MONTH({col:month})+1,1)'
OPEN_ST = 'AND({col:status}<>%s,{col:status}<>%s)' % (tok('enqst', 'Started'), tok('enqst', 'Lost'))
LAST_CALL = 'SUMPRODUCT(MAX(({range:calls.enquiry_id}={col:enquiry_id})*({range:calls.date})))'

settings = [
    S('company', 'Your agency name', 'text', COMPANY),
    S('target_margin', 'Wanted gross margin per client hour (example, use your own)', 'pct', TARGET_MARGIN),
    S('margin_red', 'Margin below this share is red (example)', 'pct', 0.30),
    S('payroll_burden', 'Payroll burden on pay (example, confirm with your adviser)', 'pct', PAYROLL_BURDEN),
    S('overtime_hours', 'Weekly hours above which overtime is paid (example)', 'int', OVERTIME_HOURS),
    S('holiday_pay_mult', 'Holiday pay multiplier', 'num', HOLIDAY_PAY_MULT), S('holiday_bill_mult', 'Holiday bill multiplier', 'num', HOLIDAY_BILL_MULT),
    S('mileage_rate', 'Mileage rate per km (or per mile, your own rate)', 'money', MILEAGE_RATE),
    S('deposit_weeks', 'Weeks of hours held as a deposit', 'int', DEPOSIT_WEEKS),
    S('reply_hours_target', 'Hours to the first reply to an enquiry (target)', 'int', 4), S('reply_share_target', 'Wanted share of enquiries replied to within the target', 'pct', 0.8),
    S('stale_enquiry_days', 'Days without contact after which an open enquiry is stale', 'int', 2), S('start_days_target', 'Days from the first call to the start of care (target)', 'int', 10),
    S('sign_days_target', 'Days within which a service agreement should be signed', 'int', 7), S('quote_valid_days', 'Days a quote stays valid', 'int', 14),
    S('notice_days', 'Days of notice to cancel a visit (agreement default)', 'int', 2), S('lock_gap', 'Gap below the rate card that marks a locked rate (example)', 'pct', 0.03),
    S('rate_change_date', 'Date of the next rate change', 'date', iso(dt.date(TODAY.year + 1, 1, 1))), S('rate_notice_days', 'Days of notice before a rate change (check local rules)', 'int', 30)]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 enquiries
tables.append(T('enquiries', 'Enquiry Log', 'Enquiry log with reply speed, assessment and start of care',
    'One row per enquiry: source, service, hours wanted, who replied and how fast, assessment, agreement and first visit dates; the quote, days to start, reply check and stale flag fill in by themselves.', [
    C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('received_on', 'Received on', 'date', 11), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18),
    LST('source', 'Source', 'enqsrc', 16), LST('area', 'Area', 'area', 13), LST('service', 'Service', 'svc', 18), C('hours_week', 'Hours a week', 'num', 9), REF('handled_by', 'Handled by', 'team.name', 20),
    C('first_reply_hours', 'Hours to first reply', 'num', 10), LST('status', 'Status', 'enqst', 17), LST('loss_reason', 'Loss reason', 'loss', 18), REF('assessor', 'Assessor', 'team.name', 20),
    C('assessment_on', 'Assessment on', 'date', 12), C('agreement_on', 'Agreement on', 'date', 12), C('first_visit_on', 'First visit on', 'date', 12), C('client_id', 'Client ID', 'text', 10),
    C('referrer', 'Referral partner', 'text', 24), C('referrer_phone', 'Referral partner phone', 'text', 18),
    CA('quote_weekly', 'Quote a week', 'money', 'IFERROR(INDEX({range:quotes.weekly_cost},MATCH({col:enquiry_id},{range:quotes.enquiry_id},0)),"")', 11),
    CA('valid_until', 'Quote valid until', 'date', 'IFERROR(INDEX({range:quotes.valid_until},MATCH({col:enquiry_id},{range:quotes.enquiry_id},0)),"")', 12),
    CA('days_to_assessment', 'Days to assessment', 'int', 'IF({col:assessment_on}="","",{col:assessment_on}-{col:received_on})', 10),
    CA('days_to_start', 'Days to start of care', 'int', 'IF({col:first_visit_on}="","",{col:first_visit_on}-{col:received_on})', 10),
    CA('reply_flag', 'Reply speed check', 'text', 'IF({col:first_reply_hours}<={set:reply_hours_target},%s,%s)' % (ck('Replied in time'), ck('Replied late')), 15),
    CA('idle_days', 'Days without contact', 'int', 'IF(%s,{today}-MAX({col:received_on},%s),"")' % (OPEN_ST, LAST_CALL), 10),
    CA('stale_flag', 'Stale check', 'text', 'IF(%s,IF({col:idle_days}>{set:stale_enquiry_days},%s,%s),%s)' % (OPEN_ST, ck('Stale'), ck('Open, in contact'), ck('Closed')), 15),
    STAFF_PH(2, 'scheduler_phone'), CA('assessor_phone', 'Assessor phone', 'text', LKT('team.phone', 'team.name', 'assessor'), 18)], D.enquiries_d(), 500,
    [A('stale_flag', '= ' + ck('Stale'), 'bad'), A('reply_flag', '= ' + ck('Replied late'), 'warn'), A('status', '= ' + tok('enqst', 'Started'), 'good'), A('status', '= ' + tok('enqst', 'Lost'), 'warn')]))
# ---------------------------------------------------------------- 2 assessments
tables.append(T('assessments', 'Assessments', 'Assessment visits: service needs and hours only',
    'One row per assessment visit: assessor, service, hours and days a week, start time, language and outcome (service needs and hours only); name, phone and travel minutes fill in.', [
    C('assessment_id', 'Assessment ID', 'text', 11, required=True), C('enquiry_id', 'Enquiry ID', 'text', 10), C('assessment_on', 'Assessment on', 'date', 12), REF('assessor', 'Assessor', 'team.name', 20),
    LST('service', 'Service', 'svc', 18), C('hours_week', 'Hours a week', 'num', 9), C('days_week', 'Days a week', 'int', 9), C('start_time', 'Preferred start time', 'time', 10), C('language', 'Language wanted', 'text', 12),
    LST('area', 'Area', 'area', 13), C('outcome', 'Outcome', 'text', 22),
    CA('name', 'Name', 'text', LKT('enquiries.name', 'enquiries.enquiry_id', 'enquiry_id'), 24), CA('phone', 'Phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18),
    CA('visit_hours', 'Average visit hours', 'num', 'IF({col:days_week}=0,"",ROUND({col:hours_week}/{col:days_week},1))', 10),
    CA('travel_min', 'Travel minutes from the office zone', 'int', LKN('areas.avg_travel_min', 'areas.area', 'area'), 12)], D.assessments_d(), 400,
    [A('assessment_on', '>= {today}', 'good')]))
# ---------------------------------------------------------------- 3 quotes
PAYW = 'SUMIFS({range:rate_card.pay_rate},{range:rate_card.service},{col:service},{range:rate_card.band},%s)' % tok('band', 'Weekday')
tables.append(T('quotes', 'Quotes', 'Quotes with weekly cost, monthly estimate and deposit',
    'One row per quote sent after an assessment: service, hours and rate; the weekly cost, monthly estimate, deposit, valid-until date and estimated margin fill in by themselves.', [
    C('quote_id', 'Quote ID', 'text', 10, required=True), C('enquiry_id', 'Enquiry ID', 'text', 10), C('sent_on', 'Sent on', 'date', 11), LST('service', 'Service', 'svc', 18), C('hours_week', 'Hours a week', 'num', 9),
    C('bill_rate', 'Bill rate per hour', 'money', 11), LST('status', 'Status', 'qst', 10),
    CA('name', 'Name', 'text', LKT('enquiries.name', 'enquiries.enquiry_id', 'enquiry_id'), 24), CA('phone', 'Phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18),
    CA('weekly_cost', 'Weekly cost', 'money', '{col:hours_week}*{col:bill_rate}', 11), CA('monthly_estimate', 'Monthly estimate', 'money', 'ROUND({col:weekly_cost}*52/12,0)', 12),
    CA('deposit', 'Deposit', 'money', '{col:weekly_cost}*{set:deposit_weeks}', 10), CA('valid_until', 'Valid until', 'date', '{col:sent_on}+{set:quote_valid_days}', 11),
    CA('valid_flag', 'Validity check', 'text', 'IF({col:status}=%s,IF({col:valid_until}>={today},%s,%s),%s)' % (tok('qst', 'Open'), ck('Valid'), ck('Expired'), ck('Closed')), 13),
    CA('est_margin_pct', 'Estimated margin', 'pct', 'IF({col:bill_rate}=0,"",1-%s*(1+{set:payroll_burden})/{col:bill_rate})' % PAYW, 10),
    CA('margin_flag', 'Margin check', 'text', 'IF({col:bill_rate}=0,"",IF(1-%s*(1+{set:payroll_burden})/{col:bill_rate}>={set:target_margin},%s,%s))' % (PAYW, ck('Quote on target'), ck('Quote below target')), 15),
    STAFF_PH(1, 'owner_phone')], D.quotes_d(), 400,
    [A('margin_flag', '= ' + ck('Quote below target'), 'bad'), A('valid_flag', '= ' + ck('Expired'), 'warn'), A('status', '= ' + tok('qst', 'Accepted'), 'good')]))
# ---------------------------------------------------------------- 4 agreements
tables.append(T('agreements', 'Service Agreements', 'Service agreements with signature timing and weekly value',
    'One row per service agreement (original, rate update or hours change): dates, hours, rate, minimum visit, notice and deposit; days to sign and the weekly value fill in.', [
    C('agreement_id', 'Agreement ID', 'text', 11, required=True), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), LST('kind', 'Kind', 'agrk', 14), C('sent_on', 'Sent on', 'date', 11),
    C('signed_on', 'Signed on', 'date', 11), C('weekly_hours', 'Weekly hours', 'num', 9), C('bill_rate', 'Bill rate per hour', 'money', 11), C('min_visit_hours', 'Minimum visit hours', 'int', 9),
    C('notice_days', 'Notice days', 'int', 8), C('deposit', 'Deposit', 'money', 10), LST('status', 'Status', 'agrst', 10),
    CA('days_to_sign', 'Days to sign', 'int', 'IF({col:signed_on}="","",{col:signed_on}-{col:sent_on})', 9),
    CA('days_unsigned', 'Days unsigned', 'int', 'IF(AND({col:signed_on}="",{col:status}=%s),{today}-{col:sent_on},"")' % tok('agrst', 'Sent'), 9),
    CA('weekly_value', 'Weekly value', 'money', '{col:weekly_hours}*{col:bill_rate}', 11),
    CA('sign_flag', 'Signature check', 'text', 'IF({col:signed_on}="",IF({col:status}=%s,IF({col:days_unsigned}>{set:sign_days_target},%s,%s),%s),IF({col:signed_on}-{col:sent_on}<={set:sign_days_target},%s,%s))' % (
        tok('agrst', 'Sent'), ck('Unsigned, chase'), ck('Unsigned, waiting'), ck('Closed'), ck('Signed within 7 days'), ck('Signed later')), 16),
    CA('phone', 'Phone', 'text', 'IFERROR(INDEX({range:clients.phone},MATCH({col:client},{range:clients.client},0))&"",IFERROR(INDEX({range:enquiries.phone},MATCH({col:client},{range:enquiries.name},0))&"",""))', 18),
    STAFF_PH(2, 'scheduler_phone'), STAFF_PH(3, 'manager_phone')], D.agreements_d(), 400,
    [A('sign_flag', '= ' + ck('Unsigned, chase'), 'bad'), A('sign_flag', '= ' + ck('Signed later'), 'warn'), A('sign_flag', '= ' + ck('Signed within 7 days'), 'good')]))
# ---------------------------------------------------------------- 5 rate card
def BANDRATE(b): return 'SUMIFS({range:rate_card.bill_rate},{range:rate_card.service},{col:service},{range:rate_card.band},%s)' % tok('band', b)
tables.append(T('rate_card', 'Rate Card', 'Rate card by service and time band with the margin check',
    'The price list: bill rate and standard pay rate for every service and time band; the loaded cost, margin per hour, margin share and below-target flag fill in by themselves.', [
    C('rate_id', 'Rate ID', 'text', 9, required=True), LST('service', 'Service', 'svc', 18), LST('band', 'Time band', 'band', 11), C('bill_rate', 'Bill rate per hour', 'money', 11), C('pay_rate', 'Pay rate per hour', 'money', 11),
    CA('loaded_cost', 'Loaded cost per hour', 'money', '{col:pay_rate}*(1+{set:payroll_burden})', 11), CA('margin_hour', 'Margin per hour', 'money', '{col:bill_rate}-{col:pay_rate}*(1+{set:payroll_burden})', 10),
    CA('margin_pct', 'Margin share', 'pct', 'IF({col:bill_rate}=0,"",1-{col:pay_rate}*(1+{set:payroll_burden})/{col:bill_rate})', 9),
    CA('margin_flag', 'Margin check', 'text', 'IF({col:bill_rate}=0,"",IF(1-{col:pay_rate}*(1+{set:payroll_burden})/{col:bill_rate}>={set:target_margin},%s,%s))' % (ck('Meets target'), ck('Below target')), 13),
    CA('r_weekday', 'Weekday rate', 'money', BANDRATE('Weekday'), 9), CA('r_evening', 'Evening rate', 'money', BANDRATE('Evening'), 9), CA('r_weekend', 'Weekend rate', 'money', BANDRATE('Weekend'), 9),
    CA('r_night', 'Night rate', 'money', BANDRATE('Night'), 9), CA('r_holiday', 'Holiday rate', 'money', BANDRATE('Holiday'), 9),
    STAFF_NM(13, 'marketing_name', 'Marketing helper'), STAFF_PH(13, 'marketing_phone')], D.rate_card_d(), 60,
    [A('margin_flag', '= ' + ck('Below target'), 'bad'), A('margin_flag', '= ' + ck('Meets target'), 'good')]))
# ---------------------------------------------------------------- 6 rate history
tables.append(T('rate_history', 'Rate History', 'Rate history: every rise by service and time band',
    'One row per rate change (old and new bill rate by service and band, one change a year); the rise share, the rise amount and the last day to give notice fill in by themselves.', [
    C('change_id', 'Change ID', 'text', 9, required=True), C('year', 'Year', 'int', 7), C('effective_on', 'Effective on', 'date', 12), LST('service', 'Service', 'svc', 18), LST('band', 'Time band', 'band', 11),
    C('old_rate', 'Old bill rate', 'money', 11), C('new_rate', 'New bill rate', 'money', 11),
    CA('rise_pct', 'Rise share', 'pct', 'IF({col:old_rate}=0,"",{col:new_rate}/{col:old_rate}-1)', 9), CA('rise_amount', 'Rise per hour', 'money', '{col:new_rate}-{col:old_rate}', 10),
    CA('notice_by', 'Notice sent by', 'date', '{col:effective_on}-{set:rate_notice_days}', 12)], D.rate_history_d(), 150))
# ---------------------------------------------------------------- 7 holidays
NEXT_H = 'SUMPRODUCT(MIN(({range:holidays.date}>={today})*({range:holidays.date})+({range:holidays.date}<{today})*99999))'
tables.append(T('holidays', 'Holidays', 'Holidays with pay and bill multipliers',
    'One row per holiday (a bank holiday or other day paid at the holiday rate): weekday and the pay and bill multipliers; days ahead and the next-holiday flag fill in by themselves.', [
    C('date', 'Date', 'date', 11, required=True), C('holiday', 'Holiday', 'text', 24), LST('weekday', 'Weekday', 'wday', 11), C('pay_mult', 'Pay multiplier', 'num', 9), C('bill_mult', 'Bill multiplier', 'num', 9),
    CA('days_ahead', 'Days ahead', 'int', '{col:date}-{today}', 9),
    CA('holiday_flag', 'Holiday check', 'text', 'IF({col:date}<{today},%s,IF({col:date}=%s,%s,%s))' % (ck('Past holiday'), NEXT_H, ck('Next holiday'), ck('Coming up')), 14)], D.holidays_d(), 60,
    [A('holiday_flag', '= ' + ck('Next holiday'), 'warn')]))
# ---------------------------------------------------------------- 8-11 references
tables.append(T('services', 'Services', 'Services with minimum visit and base rate',
    'The six services: minimum visit hours and the weekday base bill rate per hour.', [
    LST('service', 'Service', 'svc', 20, required=True), C('min_visit_hours', 'Minimum visit hours', 'int', 11), C('bill_rate', 'Weekday bill rate per hour', 'money', 12)], D.services_d(), 50))
tables.append(T('areas', 'Areas', 'Areas with zone and average travel minutes',
    'The six service areas: zone and the average travel minutes to the other areas.', [
    LST('area', 'Area', 'area', 16, required=True), LST('zone', 'Zone', 'zone', 10), C('avg_travel_min', 'Average travel minutes', 'int', 12)], D.areas_d(), 50))
tables.append(T('travel', 'Travel Times', 'Travel minutes and km between areas',
    'Minutes and km between every pair of areas (paid travel time and mileage are worked out from these).', [
    LST('from_area', 'From area', 'area', 16, required=True), LST('to_area', 'To area', 'area', 16), C('minutes', 'Minutes', 'int', 9), C('km', 'Km', 'num', 8)], D.travel_d(), 60))
tables.append(T('payers', 'Payers', 'Payers with rate share and days to pay',
    'Private pay and the payers: the share of the rate card each pays and the usual days to be paid. A third-party payer is an insurer, a public body or an employer scheme in your area.', [
    C('payer', 'Payer', 'text', 24, required=True), C('rate_share', 'Rate share', 'pct', 10), C('pay_days', 'Days to pay', 'int', 10)], D.payers_d(), 50))
# ---------------------------------------------------------------- 12 clients
CARD = 'SUMIFS({range:rate_card.bill_rate},{range:rate_card.service},{col:service},{range:rate_card.band},%s)*SUMIFS({range:payers.rate_share},{range:payers.payer},{col:payer})' % tok('band', 'Weekday')
tables.append(T('clients', 'Clients', 'Clients with rate, weekly hours and locked-rate check',
    'One row per client (private pay means self-funded): area, payer, service, weekly hours, rate and agreement terms; the weekly value, tenure, rate gap to the card and renewal date fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), LST('area', 'Area', 'area', 13), C('phone', 'Phone', 'text', 18), LST('payer', 'Payer', 'payer', 18), LST('service', 'Service', 'svc', 18), C('weekly_hours', 'Weekly hours', 'num', 9), C('bill_rate', 'Bill rate per hour', 'money', 11), C('min_visit_hours', 'Minimum visit hours', 'int', 9),
    LST('billing_cycle', 'Billing cycle', 'cycle', 11), C('language', 'Language', 'text', 12), C('preferred', 'Preferred caregiver', 'text', 20), C('preferred_2', 'Second caregiver', 'text', 20),
    LST('source', 'Source', 'enqsrc', 16), C('start_date', 'Start date', 'date', 11), LST('status', 'Status', 'clstatus', 10), C('end_date', 'End date', 'date', 11),
    C('deposit', 'Deposit', 'money', 10), C('prepay', 'Prepaid balance', 'bool', 9),
    CA('weekly_value', 'Weekly value', 'money', '{col:weekly_hours}*{col:bill_rate}', 11), 
    CA('card_rate', 'Rate card rate for the payer', 'money', CARD, 11), CA('rate_gap', 'Gap to the rate card', 'pct', 'IF(%s=0,"",{col:bill_rate}/(%s)-1)' % (CARD, CARD), 10),
    CA('rate_flag', 'Rate check', 'text', 'IF({col:status}<>%s,%s,IF(%s=0,%s,IF({col:bill_rate}/(%s)-1<-{set:lock_gap},%s,%s)))' % (tok('clstatus', 'Active'), ck('Closed'), CARD, ck('On the card'), CARD, ck('Locked rate'), ck('On the card')), 13),
    CA('renewal_on', 'Next agreement renewal', 'date', 'IF({col:status}<>%s,"",DATE(YEAR({today})+IF(DATE(YEAR({today}),MONTH({col:start_date}),DAY({col:start_date}))<{today},1,0),MONTH({col:start_date}),DAY({col:start_date})))' % tok('clstatus', 'Active'), 12),
    CA('intro_on', 'Introduction visit', 'date', '{col:start_date}-2', 11), CA('rate_change_on', 'Next rate change', 'date', '{set:rate_change_date}', 11),
    CA('next_holiday_on', 'Next holiday date', 'date', 'IF(%s>=99999,"",%s)' % (NEXT_H, NEXT_H), 11),
    CA('next_holiday', 'Next holiday', 'text', 'IFERROR(INDEX({range:holidays.holiday},MATCH(%s,{range:holidays.date},0))&"","")' % NEXT_H, 20),
    CA('preferred_phone', 'Preferred caregiver phone', 'text', LKT('capacity.phone', 'capacity.caregiver', 'preferred'), 18), STAFF_PH(5, 'supervisor_phone'), STAFF_PH(3, 'manager_phone')], D.clients_d(), 200,
    [A('rate_flag', '= ' + ck('Locked rate'), 'warn'), A('status', '= ' + tok('clstatus', 'Ended'), 'bad')]))
# ---------------------------------------------------------------- 13 starts
tables.append(T('starts', 'Client Starts and Ends', 'Clients and weekly hours started and lost each month',
    'One row per month: clients started and ended, weekly hours added and lost and active clients; net hours, net clients and the churn share fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), C('clients_started', 'Clients started', 'int', 9), C('clients_ended', 'Clients ended', 'int', 9), C('hours_added', 'Weekly hours added', 'num', 10),
    C('hours_lost', 'Weekly hours lost', 'num', 10), C('active_clients', 'Active clients', 'int', 9),
    CA('net_hours', 'Net weekly hours', 'num', '{col:hours_added}-{col:hours_lost}', 10), CA('net_clients', 'Net clients', 'int', '{col:clients_started}-{col:clients_ended}', 9),
    CA('churn_pct', 'Client churn', 'pct', 'IF({col:active_clients}=0,"",{col:clients_ended}/{col:active_clients})', 9)], D.starts_d(), 60,
    [A('churn_pct', '> 0.05', 'warn'), A('net_hours', '< 0', 'bad')]))
# ---------------------------------------------------------------- 14 funnel
def CNT(extra=''):
    return 'COUNTIFS({range:enquiries.received_on},">="&{col:month},{range:enquiries.received_on},"<"&%s%s)' % (MON, extra)
tables.append(T('funnel', 'Monthly Funnel', 'Monthly funnel from enquiry to start of care',
    'One row per month (type the 1st of the month): enquiries received that month and how many reached an assessment, an agreement, a first visit or were lost; conversion rates fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('enquiries', 'Enquiries', 'int', CNT(), 9), CA('assessments', 'Assessments', 'int', CNT(',{range:enquiries.assessment_on},">0"'), 11), CA('agreements', 'Agreements', 'int', CNT(',{range:enquiries.agreement_on},">0"'), 11),
    CA('started', 'Started', 'int', CNT(',{range:enquiries.first_visit_on},">0",{range:enquiries.status},%s' % tok('enqst', 'Started')), 9), CA('lost', 'Lost', 'int', CNT(',{range:enquiries.status},%s' % tok('enqst', 'Lost')), 9),
    CA('conversion', 'Enquiry-to-client conversion', 'pct', 'IF({col:enquiries}=0,"",{col:started}/{col:enquiries})', 11), CA('assessment_rate', 'Assessment rate', 'pct', 'IF({col:enquiries}=0,"",{col:assessments}/{col:enquiries})', 10),
    CA('enq_per_week', 'Enquiries a week', 'num', 'IF({col:enquiries}=0,"",ROUND({col:enquiries}*7/(DATE(YEAR({col:month}),MONTH({col:month})+1,1)-{col:month}),1))', 10),
    STAFF_PH(1, 'owner_phone')], D.funnel_d(), 60, [A('conversion', '< 0.2', 'warn')]))
# ---------------------------------------------------------------- 15 lost
tables.append(T('lost', 'Lost Enquiries', 'Lost enquiries by reason with the quote that was lost',
    'One row per enquiry that did not become a client: reason, quoted weekly cost and last contact; the name, phone and days open fill in by themselves.', [
    C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('date', 'Lost on', 'date', 11), LST('service', 'Service', 'svc', 18), LST('area', 'Area', 'area', 13), LST('source', 'Source', 'enqsrc', 16),
    LST('reason', 'Reason', 'loss', 18), C('quote_weekly', 'Quoted weekly cost', 'money', 11), C('last_contact', 'Last contact', 'date', 11),
    CA('name', 'Name', 'text', LKT('enquiries.name', 'enquiries.enquiry_id', 'enquiry_id'), 24), CA('phone', 'Phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18),
    CA('days_open', 'Days open', 'int', '{col:date}-%s' % LKN('enquiries.received_on', 'enquiries.enquiry_id', 'enquiry_id'), 9)], D.lost_d(), 400,
    [A('reason', '= ' + tok('loss', 'Price'), 'warn'), A('reason', '= ' + tok('loss', 'No cover available'), 'bad')]))
# ---------------------------------------------------------------- 16 sources
tables.append(T('sources', 'Source by Month', 'Enquiries, starts and hours by source and month',
    'One row per month and source: enquiries, clients started and weekly hours started; the start rate and hours per enquiry fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), LST('source', 'Source', 'enqsrc', 16), C('enquiries', 'Enquiries', 'int', 9), C('started', 'Started', 'int', 9), C('hours_started', 'Weekly hours started', 'num', 10),
    C('cost', 'Cost of the source', 'money', 11),
    CA('start_rate', 'Start rate', 'pct', 'IF({col:enquiries}=0,"",{col:started}/{col:enquiries})', 9), CA('hours_per_enquiry', 'Hours per enquiry', 'num', 'IF({col:enquiries}=0,"",ROUND({col:hours_started}/{col:enquiries},1))', 10),
    CA('rank_12m', 'Source rank, 12 months', 'int', '1+SUMPRODUCT(({range:sources.source}<>"")*({range:sources.value_12m}>{col:value_12m})/(COUNTIFS({range:sources.source},{range:sources.source})+({range:sources.source}="")))', 10),
    CA('cost_per_start', 'Cost per client started', 'money', 'IF({col:started}=0,"",ROUND({col:cost}/{col:started},0))', 11),
    CA('value_12m', 'Hours started per 100 of cost, 12 months', 'num', 'IFERROR(ROUND(100*SUMIFS({range:sources.hours_started},{range:sources.source},{col:source},{range:sources.month},">="&DATE(YEAR({today}),MONTH({today})-11,1))/SUMIFS({range:sources.cost},{range:sources.source},{col:source},{range:sources.month},">="&DATE(YEAR({today}),MONTH({today})-11,1)),1),0)', 12),
    STAFF_PH(1, 'owner_phone')], D.sources_d(), 400, [A('started', '> 0', 'good')]))
# ---------------------------------------------------------------- 17 availability
tables.append(T('availability', 'Caregiver Availability', 'Caregiver availability by weekday',
    'One row per caregiver and weekday: the hours the caregiver can work and the most hours that day (carer, care worker or support worker are other names for a caregiver).', [
    C('avail_id', 'Availability ID', 'text', 11, required=True), C('caregiver_id', 'Caregiver ID', 'text', 10), C('caregiver', 'Caregiver', 'text', 24), LST('weekday', 'Weekday', 'wday', 11),
    C('from_time', 'From', 'time', 8), C('to_time', 'To', 'time', 8), C('max_hours', 'Most hours', 'int', 9)], D.availability_d(), 400))
# ---------------------------------------------------------------- 18 capacity
SKILL_LABELS = ['Companion care', 'Personal care help', 'Homemaking', 'Respite care', 'Overnight care', 'Live-in day']
tables.append(T('capacity', 'Caregiver Capacity', 'Caregiver capacity and free hours next week',
    'One row per working caregiver: area, services they can do, languages, hours limit and hours booked next week; free hours, overtime line and the capacity flag fill in by themselves.', [
    C('caregiver_id', 'Caregiver ID', 'text', 10, required=True), C('no', 'Row no', 'int', 6), C('caregiver', 'Caregiver', 'text', 24), C('phone', 'Phone', 'text', 18), LST('area', 'Area', 'area', 13),
    LST('employment', 'Employment', 'emp', 10), LST('availability', 'Availability', 'avail', 20), C('language_1', 'Language 1', 'text', 11), C('language_2', 'Language 2', 'text', 11), C('pay_rate', 'Pay rate per hour', 'money', 10)] + [
    C(k, lab, 'bool', 9) for k, lab in zip(D.SKILL_COLS, SKILL_LABELS)] + [
    C('hours_limit', 'Hours limit', 'int', 8), C('hours_next_week', 'Hours booked next week', 'num', 10), C('working', 'Working next week', 'bool', 9),
    CA('free_hours', 'Free hours next week', 'num', 'IF({col:working}=%s,MAX(0,MIN({col:hours_limit},{set:overtime_hours})-{col:hours_next_week}),0)' % YES, 10),
    CA('clients_in_area', 'Active clients in the area', 'int', 'COUNTIFS({range:clients.area},{col:area},{range:clients.status},%s)' % tok('clstatus', 'Active'), 10),
    CA('cap_flag', 'Capacity check', 'text', 'IF({col:working}<>%s,%s,IF({col:hours_next_week}>{set:overtime_hours},%s,IF({col:free_hours}>0,%s,%s)))' % (YES, ck('Not working'), ck('Over the line'), ck('Free hours'), ck('Full')), 13)], D.capacity_d(), 100,
    [A('cap_flag', '= ' + ck('Over the line'), 'bad'), A('cap_flag', '= ' + ck('Free hours'), 'good')]))
# ---------------------------------------------------------------- 19 calls
tables.append(T('calls', 'Enquiry Calls', 'Enquiry calls and messages with hours since the enquiry',
    'One row per call, text message or email about an enquiry: kind, outcome and minutes; the name, phone and days since the enquiry fill in by themselves.', [
    C('call_id', 'Call ID', 'text', 9, required=True), C('enquiry_id', 'Enquiry ID', 'text', 10), C('date', 'Date', 'date', 11), C('kind', 'Kind', 'text', 14), C('outcome', 'Outcome', 'text', 20),
    C('minutes', 'Minutes', 'int', 8), C('hours_after', 'Hours after the enquiry', 'num', 10),
    CA('name', 'Name', 'text', LKT('enquiries.name', 'enquiries.enquiry_id', 'enquiry_id'), 24), CA('phone', 'Phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18),
    CA('days_since', 'Days since the enquiry', 'int', '{col:date}-%s' % LKN('enquiries.received_on', 'enquiries.enquiry_id', 'enquiry_id'), 10)], D.calls_d(), 900,
    [A('days_since', '> 7', 'warn')]))
# ---------------------------------------------------------------- 20 team
tables.append(T('team', 'Team', 'Team and outside contacts',
    'The owner-director, the scheduler, the office manager, the recruiter, two field supervisors and ten outside contacts with phone and e-mail (messages use these phones).', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 18), C('team', 'Team', 'text', 11), C('pay_type', 'Pay type', 'text', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'Email', 'text', 26), C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'int', 11), C('hourly_rate', 'Hourly rate', 'int', 9), C('speciality', 'Speciality', 'text', 30),
    C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11)], D.team_d(), 50))
assert len(tables) == 20
