"""HVAC suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv1_lists import *
import hv1_data as D

YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def ph(v): return '"%s"' % v
def CONST(k, label, v): return CA(k, label, 'text', ph(v), 18)
def TECHPH(col='technician'): return CA('tech_phone', 'Technician phone', 'text', 'IFERROR(CHOOSE(MATCH({col:%s},{range:techs.technician},0),%s),"")' % (col, ','.join(ph(p) for p in D.TECH_PHONES[:6])), 18)
CANC, COMP, SCHED, PROG = tok('jobstatus', 'Cancelled'), tok('jobstatus', 'Completed'), tok('jobstatus', 'Scheduled'), tok('jobstatus', 'In progress')
PASSED = tok('permitstatus', 'Passed')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('booking_target', 'Booking rate wanted (typical range, check yours)', 'pct', BOOKING_TARGET),
    S('repeat_days', 'Days for a repeat visit to count as a possible callback', 'int', REPEAT_DAYS), S('diag_fee', 'Diagnostic fee, credited if the customer goes ahead', 'money', DIAG_FEE),
    S('capacity_hours', 'Productive hours in a technician day, drive time included', 'num', 8.5), S('vehicle_hour', 'Vehicle cost per hour on the road', 'money', VEHICLE_HOUR),
    S('tech_cost_hour', 'Technician cost per hour (confirm with your adviser)', 'money', 47), S('owner_draw', 'Owner draw wanted each month', 'money', OWNER_DRAW),
    S('margin_target', 'Job margin wanted (a typical range, check your own numbers)', 'pct', 0.5),
    S('answering_cost', 'Monthly cost of an answering service', 'money', 450), S('reserve_hours', 'Hours held back each day for emergency calls', 'num', 2.5),
    S('parts_alert_days', 'Days ahead to order parts that are not confirmed', 'int', 3), S('chase_slack_days', 'Days over the shop average wait before a permit is chased', 'int', 3),
    S('unbooked_days', 'Days back to rank unbooked calls', 'int', 14), S('permit_ok_days', 'Days to approve a permit counted as on time', 'int', 10), S('after_hour', 'Hour of the day when after hours start (24-hour clock)', 'int', 18),
]

def PRICE(): return None
tables = []
# 1 calls
tables.append(T('calls', 'Calls', 'Call log with source, outcome and lost value',
  'One row per incoming call: source, call type, outcome, who answered and the estimated job value; booked flag, lost value, the act-first score and the call-back list fill in by themselves.', [
    C('call_id', 'Call', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 10), LST('weekday', 'Weekday', 'wday7', 11), C('time', 'Time', 'text', 8), LST('source', 'Source', 'source', 17),
    LST('call_type', 'Call type', 'calltype', 10), LST('outcome', 'Outcome', 'calloutcome', 15), LST('answered_by', 'Answered by', 'answeredby', 16), C('site_id', 'Site', 'text', 10), C('caller_phone', 'Caller phone', 'text', 18),
    C('est_value', 'Estimated value', 'money', 12), C('job_id', 'Job', 'text', 10), C('emergency', 'Emergency', 'bool', 9),
    CA('booked', 'Booked (1 or 0)', 'int', 'IF(IFERROR(INDEX({range:outcomes.booked},MATCH({col:outcome},{range:outcomes.outcome},0)),%s)=%s,1,0)' % (NO, YES), 9),
    CA('lost_value', 'Lost value', 'money', 'IF(OR({col:booked}=1,{col:outcome}=%s,{col:outcome}=%s),0,{col:est_value})' % (tok('calloutcome', 'Outside area'), tok('calloutcome', 'Existing job')), 12),
    CA('hour', 'Hour', 'int', 'VALUE(LEFT({col:time},2))', 7),
    CA('act_score', 'Act-first score', 'num', 'IF(AND({col:lost_value}>0,{col:date}>={today}-{set:unbooked_days}),{col:lost_value}+{col:date}/100000+{col:hour}/10000000+VALUE(RIGHT({col:time},2))/1000000000,"")', 12),
    CA('type_lost', 'Lost value of this call type, 90 days', 'money', 'SUMIFS({range:calls.lost_value},{range:calls.call_type},{col:call_type},{range:calls.date},">="&({today}-90))', 14),
    CA('site_ref', 'Site reference', 'text', LKT('sites.site_ref', 'sites.site_id', 'site_id'), 11),
    CA('company', 'Company', 'text', '{set:company}', 24), CA('office_phone', 'Office manager phone', 'text', ph(D.OFFICE_PHONE), 18)],
  D.calls_d(), 1500, [A('booked', '= 0', 'warn'), A('lost_value', '>= 1000', 'bad'), A('emergency', '= ' + YES, 'warn')]))
# 2 jobs
tables.append(T('jobs', 'Jobs', 'Jobs with parts, permit and repeat-visit flags',
  'One row per job: when, where, who, which van, hours, price and status; days since the last job at the site and the possible-callback flag fill in by themselves.', [
    C('job_id', 'Job', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('week', 'Week (Monday)', 'date', 12), LST('weekday', 'Weekday', 'wday7', 11), C('start', 'Start', 'text', 8), C('site_id', 'Site', 'text', 10),
    LST('area', 'Area', 'area', 11), LST('site_type', 'Site type', 'sitetype', 10), C('equipment_id', 'Equipment', 'text', 10), LST('job_type', 'Job type', 'jobtype', 26), LST('reason', 'Reason', 'calltype', 10),
    LST('technician', 'Technician', 'tech', 16), C('assistant', 'Assistant', 'text', 16), LST('van', 'Van', 'van', 8), C('hours', 'Hours on site', 'num', 8), C('drive_hours', 'Drive hours', 'num', 8),
    C('price', 'Price', 'money', 11), C('cost', 'Cost', 'money', 11), LST('status', 'Status', 'jobstatus', 12), C('parts_ready', 'Parts ready', 'bool', 9), C('permit_needed', 'Permit needed', 'bool', 9),
    C('emergency', 'Emergency', 'bool', 9), C('call_id', 'Call', 'text', 10),
    CA('site_ref', 'Site reference', 'text', LKT('sites.site_ref', 'sites.site_id', 'site_id'), 11),
    CA('site_date', 'Site and date key', 'text', 'IF({col:site_id}="","",{col:site_id}&"|"&{col:date})', 16),
    CA('prev_date', 'Previous job at the site', 'date', 'IF(SUMPRODUCT(MAX(({range:jobs.site_id}={col:site_id})*({range:jobs.date}<{col:date})*({range:jobs.status}<>%s)*{range:jobs.date}))=0,"",SUMPRODUCT(MAX(({range:jobs.site_id}={col:site_id})*({range:jobs.date}<{col:date})*({range:jobs.status}<>%s)*{range:jobs.date})))' % (CANC, CANC), 12),
    CA('days_since', 'Days since the last job at the site', 'int', 'IF(ISNUMBER({col:prev_date}),{col:date}-{col:prev_date},"")', 11),
    CA('repeat', 'Repeat check', 'text', 'IF({col:status}=%s,%s,IF(ISNUMBER({col:days_since}),IF({col:days_since}<={set:repeat_days},%s,%s),%s))' % (CANC, ck('No earlier visit'), ck('Possible callback'), ck('Later repeat'), ck('No earlier visit')), 16),
    CA('same_day', 'Same-day job (1 or 0)', 'int', 'IF(IFERROR(INDEX({range:calls.date},MATCH({col:call_id},{range:calls.call_id},0)),0)={col:date},1,0)', 9),
    CA('parts_key', 'Parts gap order', 'num', 'IF(AND({col:parts_ready}=%s,{col:status}=%s,{col:date}>{today}),{col:date}+VALUE(LEFT({col:start},2))/100+VALUE(RIGHT({col:start},2))/10000+VALUE(RIGHT({col:job_id},5))/1000000000,"")' % (NO, SCHED), 12),
    CA('owner_phone', 'Owner phone', 'text', ph(D.OWNER_PHONE), 18), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.jobs_d(), 1200, [A('repeat', '= ' + ck('Possible callback'), 'warn'), A('parts_ready', '= ' + NO, 'warn'), A('status', '= ' + CANC, 'bad')]))
# 3 dispatch board
tables.append(T('dispatch', 'Dispatch Board', 'Dispatch board by technician and day',
  'One row per technician and day: jobs, booked and drive hours, free hours and jobs with no parts come from the Jobs sheet; the flag shows full, short of parts or over capacity.', [
    C('row_id', 'Row', 'text', 9, required=True), LST('technician', 'Technician', 'tech', 16), C('date', 'Date', 'date', 11),
    CA('van', 'Van', 'text', LKT('techs.van', 'techs.technician', 'technician'), 8), CA('trade', 'Trade', 'text', LKT('techs.trade', 'techs.technician', 'technician'), 10),
    CA('jobs', 'Jobs', 'int', 'COUNTIFS({range:jobs.technician},{col:technician},{range:jobs.date},{col:date},{range:jobs.status},"<>"&%s)' % CANC, 7),
    CA('booked_hours', 'Booked hours', 'num', 'SUMIFS({range:jobs.hours},{range:jobs.technician},{col:technician},{range:jobs.date},{col:date},{range:jobs.status},"<>"&%s)' % CANC, 9),
    CA('drive_hours', 'Drive hours', 'num', 'SUMIFS({range:jobs.drive_hours},{range:jobs.technician},{col:technician},{range:jobs.date},{col:date},{range:jobs.status},"<>"&%s)' % CANC, 9),
    CA('free_hours', 'Free hours', 'num', '{set:capacity_hours}-{col:booked_hours}-{col:drive_hours}', 9),
    CA('no_parts', 'Jobs with no parts confirmed', 'int', 'COUNTIFS({range:jobs.technician},{col:technician},{range:jobs.date},{col:date},{range:jobs.status},"<>"&%s,{range:jobs.parts_ready},%s)' % (CANC, NO), 12),
    CA('flag', 'Day check', 'text', 'IF({col:free_hours}<0,%s,IF({col:no_parts}>0,%s,IF({col:jobs}=0,%s,IF({col:free_hours}<=1.5,%s,%s))))' % (ck('Over capacity'), ck('Parts not confirmed'), ck('Open day'), ck('Full day'), ck('Room left')), 18),
    CA('slot_hvac', 'Free today, HVAC', 'num', 'IF(AND({col:date}={today},{col:trade}=%s),{col:free_hours},"")' % tok('trade', 'HVAC'), 9),
    CA('slot_plumbing', 'Free today, plumbing', 'num', 'IF(AND({col:date}={today},{col:trade}=%s),{col:free_hours},"")' % tok('trade', 'Plumbing'), 9),
    TECHPH(), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.dispatch_d(), 80, [A('flag', '= ' + ck('Over capacity'), 'bad'), A('flag', '= ' + ck('Parts not confirmed'), 'warn'), A('flag', '= ' + ck('Room left'), 'good')]))
# 4 permits
tables.append(T('permits', 'Permit Log', 'Permit and inspection log with the cost of a van waiting',
  'One row per job that needs a permit: dates applied, approved, inspection booked and passed; days waiting, days held past the job date and the van cost waiting fill in by themselves.', [
    C('permit_id', 'Permit', 'text', 10, required=True), C('job_id', 'Job', 'text', 10), C('site_id', 'Site', 'text', 10), LST('job_type', 'Job type', 'jobtype', 26), LST('technician', 'Technician', 'tech', 16), C('job_date', 'Job date', 'date', 11),
    C('applied_on', 'Applied on', 'date', 11), C('fee', 'Fee', 'money', 10), C('approved_on', 'Approved on', 'date', 11), C('inspection_on', 'Inspection on', 'date', 11), C('passed_on', 'Passed on', 'date', 11), LST('status', 'Status', 'permitstatus', 16),
    CA('days_to_approve', 'Days to approve', 'int', 'IF({col:approved_on}="","",{col:approved_on}-{col:applied_on})', 9),
    CA('days_to_inspect', 'Days from approval to inspection', 'int', 'IF(OR({col:approved_on}="",{col:inspection_on}=""),"",{col:inspection_on}-{col:approved_on})', 11),
    CA('days_waiting', 'Days waiting', 'int', 'IF({col:approved_on}="",{today}-{col:applied_on},{col:approved_on}-{col:applied_on})', 9),
    CA('days_held', 'Days held past the job date', 'int', 'IF(AND({col:approved_on}="",{col:job_date}<{today}),{today}-{col:job_date},0)', 11),
    CA('van_cost_waiting', 'Van cost waiting', 'money', '{col:days_held}*{set:capacity_hours}*({set:tech_cost_hour}+{set:vehicle_hour})', 12),
    CA('job_price', 'Money held, job price', 'money', LKN('jobs.price', 'jobs.job_id', 'job_id'), 12),
    CA('chase_key', 'Chase order score', 'num', 'IF({col:status}<>%s,{col:days_waiting}+{col:job_price}/100000+VALUE(RIGHT({col:permit_id},4))/10000000000,"")' % PASSED, 12),
    CA('site_ref', 'Site reference', 'text', LKT('sites.site_ref', 'sites.site_id', 'site_id'), 11), CA('phone', 'Customer phone', 'text', LKT('sites.phone', 'sites.site_id', 'site_id'), 18),
    TECHPH(), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.permits_d(), 400, [A('days_held', '> 0', 'bad'), A('status', '= ' + tok('permitstatus', 'Applied'), 'warn'), A('status', '= ' + PASSED, 'good')]))
# 5 sites
tables.append(T('sites', 'Customer Sites', 'Customer sites by reference, area and phone',
  'One row per customer site: reference, area, site type, landlord or business account and phone; jobs and the last job date. Customers appear as a reference, never by name.', [
    C('site_id', 'Site', 'text', 10, required=True), C('site_ref', 'Site reference', 'text', 11), LST('area', 'Area', 'area', 11), LST('site_type', 'Site type', 'sitetype', 10), C('landlord', 'Landlord account', 'bool', 9),
    C('account', 'Account', 'text', 10), C('phone', 'Phone', 'text', 18), C('member', 'Member', 'bool', 9), C('jobs', 'Jobs', 'int', 7), C('last_job', 'Last job', 'date', 11)],
  D.sites_d(), 1600, [A('member', '= ' + YES, 'good')]))
# 6 technicians, 7 vans, 8 job types, 9 call types, 10 outcomes, 11 sources
tables.append(T('techs', 'Technicians', 'Technicians with trade and van', 'The six lead technicians, their trade and the van they drive; the dispatch board and the slotter read this sheet.',
  [C('technician', 'Technician', 'text', 24, required=True), C('trade', 'Trade', 'text', 11), C('van', 'Van', 'text', 9)], D.techs_d(), 12))
tables.append(T('vans', 'Vans', 'Vans with driver and monthly lease', 'The six vans, who drives each and the lease cost a month.',
  [C('van', 'Van', 'text', 9, required=True), C('technician', 'Technician', 'text', 24), C('lease_monthly', 'Lease a month', 'money', 12)], D.vans_d(), 12))
tables.append(T('job_types', 'Job Types', 'Job types with trade, kind, hours and target margin',
  'The job types you sell with the trade, the kind, the usual hours and the margin you want (set your own, a typical range, check your own numbers).',
  [C('job_type', 'Job type', 'text', 26, required=True), C('trade', 'Trade', 'text', 11), C('kind', 'Kind', 'text', 12), C('avg_hours', 'Average hours', 'num', 9), C('target_margin', 'Target margin', 'pct', 9)], D.job_types_d(), 30))
tables.append(T('call_types', 'Call Types', 'Call types with emergency flag and average value', 'Why people call, whether it counts as an emergency and the average value of a booked job.',
  [C('call_type', 'Call type', 'text', 14, required=True), C('emergency', 'Emergency', 'bool', 9), C('avg_value', 'Average value', 'money', 12)], D.call_types_d(), 20))
tables.append(T('outcomes', 'Call Outcomes', 'Call outcomes and which ones count as booked', 'What can happen to a call and whether it counts as booked; the booked flag of every call reads this sheet.',
  [C('outcome', 'Outcome', 'text', 16, required=True), C('booked', 'Counts as booked', 'bool', 10), C('note', 'Note', 'text', 28)], D.outcomes_d(), 20))
tables.append(T('sources', 'Lead Sources', 'Lead sources with monthly cost and kind', 'Where calls come from, what each source costs a month and whether it is paid or free.',
  [C('source', 'Source', 'text', 18, required=True), C('monthly_cost', 'Cost a month', 'money', 12), C('kind', 'Kind', 'text', 10)], D.sources_d(), 20))
# 12 booking by source
tables.append(T('book_source', 'Booking by Source', 'Booking rate by source, last 90 days and the 90 before',
  'One row per source and period: calls, booked calls and the estimated value of unbooked calls from your log; booking rate and the lost value per call fill in by themselves.', [
    C('row_id', 'Row', 'text', 8, required=True), LST('source', 'Source', 'source', 17), LST('period', 'Period', 'period', 16), C('calls', 'Calls', 'int', 8), C('booked', 'Booked', 'int', 8), C('lost_value', 'Lost value', 'money', 12),
    CA('booking_rate', 'Booking rate', 'pct', 'IFERROR({col:booked}/{col:calls},0)', 9), CA('lost_per_call', 'Lost value per call', 'money', 'IFERROR({col:lost_value}/{col:calls},0)', 11),
    CA('rate_last', 'Rate, last 90 days', 'pct', 'IF({col:period}=%s,{col:booking_rate},"")' % tok('period', 'Last 90 days'), 10),
    CA('gap_to_target', 'Gap to the target', 'pct', '{col:booking_rate}-{set:booking_target}', 9)],
  D.book_source_d(), 40, [A('gap_to_target', '< 0', 'warn'), A('gap_to_target', '>= 0', 'good')]))
# 13 booking by who answered
tables.append(T('book_answered', 'Booking by Answerer', 'Booking rate by who answered and the time of day',
  'One row per answering person, time of day and period: calls and booked calls; booking rate and the gap to the target fill in by themselves.', [
    C('row_id', 'Row', 'text', 8, required=True), LST('answered_by', 'Answered by', 'answeredby', 16), LST('daypart', 'Time of day', 'daypart', 15), LST('period', 'Period', 'period', 16), C('calls', 'Calls', 'int', 8), C('booked', 'Booked', 'int', 8),
    CA('booking_rate', 'Booking rate', 'pct', 'IFERROR({col:booked}/{col:calls},0)', 9), CA('gap_to_target', 'Gap to the target', 'pct', '{col:booking_rate}-{set:booking_target}', 9)],
  D.book_answered_d(), 30, [A('gap_to_target', '< 0', 'warn'), A('gap_to_target', '>= 0', 'good')]))
# 14 missed by weekday
tables.append(T('miss_weekday', 'Missed Calls by Weekday', 'Missed calls by weekday and time of day, last 12 months',
  'One row per weekday and time of day: calls, missed calls and the estimated value of the missed calls; the miss rate fills in by itself.', [
    C('row_id', 'Row', 'text', 8, required=True), LST('weekday', 'Weekday', 'wday7', 11), LST('daypart', 'Time of day', 'daypart', 15), C('calls', 'Calls', 'int', 8), C('missed', 'Missed calls', 'int', 8), C('lost_value', 'Lost value', 'money', 12),
    CA('miss_rate', 'Miss rate', 'pct', 'IFERROR({col:missed}/{col:calls},0)', 9)],
  D.miss_weekday_d(), 30, [A('miss_rate', '>= 0.1', 'bad'), A('miss_rate', '>= 0.05', 'warn')]))
# 15 calls by month
tables.append(T('calls_month', 'Calls by Month', 'Calls, jobs and possible callbacks by month',
  'One row per month from your call log and jobs: calls, booked, emergencies, jobs, drive hours, possible callbacks and unbooked value; booking rate fills in. Last month is month to date.', [
    C('month', 'Month', 'date', 10, required=True), C('calls', 'Calls', 'int', 8), C('booked', 'Booked', 'int', 8), C('emergency_calls', 'Emergency calls', 'int', 9), C('jobs', 'Jobs', 'int', 8), C('drive_hours', 'Drive hours', 'int', 9),
    C('possible_callbacks', 'Possible callbacks', 'int', 10), C('lost_value', 'Lost value', 'money', 12), CA('booking_rate', 'Booking rate', 'pct', 'IFERROR({col:booked}/{col:calls},0)', 9),
    CA('callback_share', 'Possible callbacks over jobs', 'pct', 'IFERROR({col:possible_callbacks}/{col:jobs},0)', 10),
    CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.calls_month_d(), 40, [A('booking_rate', '< {set:booking_target}', 'warn')]))
# 16 capacity by day
tables.append(T('capacity', 'Capacity by Day', 'Capacity by day for the next 30 days',
  'One row per day: technicians working; hours available, hours booked from the Jobs sheet, free hours and the load fill in by themselves.', [
    C('date', 'Date', 'date', 11, required=True), C('techs_working', 'Technicians working', 'int', 10),
    CA('hours_available', 'Hours available', 'num', '{col:techs_working}*{set:capacity_hours}', 10),
    CA('hours_booked', 'Hours booked', 'num', 'SUMIFS({range:jobs.hours},{range:jobs.date},{col:date},{range:jobs.status},"<>"&%s)+SUMIFS({range:jobs.drive_hours},{range:jobs.date},{col:date},{range:jobs.status},"<>"&%s)' % (CANC, CANC), 10),
    CA('free_hours', 'Free hours', 'num', '{col:hours_available}-{col:hours_booked}', 9), CA('load', 'Load', 'pct', 'IFERROR({col:hours_booked}/{col:hours_available},0)', 8),
    CA('flag', 'Capacity check', 'text', 'IF({col:load}>1,%s,IF({col:load}>=0.85,%s,%s))' % (ck('Over capacity'), ck('Nearly full'), ck('Room left')), 14),
    CA('room_score', 'Room score, next 10 working days', 'num', 'IF(AND({col:date}>{today},{col:date}<=WORKDAY({today},10),WEEKDAY({col:date},2)<6),{col:free_hours}+(100-({col:date}-{today}))/100000,"")', 12)],
  D.capacity_d(), 60, [A('flag', '= ' + ck('Over capacity'), 'bad'), A('flag', '= ' + ck('Nearly full'), 'warn')]))
# 17 jobs by status by week
tables.append(T('jobs_week', 'Jobs by Week', 'Jobs by status by week', 'One row per week (Monday): scheduled, in progress, completed and cancelled jobs and the jobs still waiting for parts, counted from the Jobs sheet.', [
    C('week', 'Week (Monday)', 'date', 12, required=True),
    CA('scheduled', 'Scheduled', 'int', 'COUNTIFS({range:jobs.week},{col:week},{range:jobs.status},%s)' % SCHED, 9), CA('in_progress', 'In progress', 'int', 'COUNTIFS({range:jobs.week},{col:week},{range:jobs.status},%s)' % PROG, 9),
    CA('completed', 'Completed', 'int', 'COUNTIFS({range:jobs.week},{col:week},{range:jobs.status},%s)' % COMP, 9), CA('cancelled', 'Cancelled', 'int', 'COUNTIFS({range:jobs.week},{col:week},{range:jobs.status},%s)' % CANC, 9),
    CA('waiting_parts', 'Waiting for parts', 'int', 'COUNTIFS({range:jobs.week},{col:week},{range:jobs.parts_ready},%s,{range:jobs.status},%s)+COUNTIFS({range:jobs.week},{col:week},{range:jobs.parts_ready},%s,{range:jobs.status},%s)' % (NO, SCHED, NO, PROG), 10),
    CONST('acct_phone', 'Accountant phone', D.ACCT_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.jobs_week_d(), 40))
# 18 permit wait by job type
tables.append(T('permit_wait', 'Permit Wait', 'Permit wait by job type from your own history',
  'One row per job type: permits, average days to approve, average days from approval to inspection and jobs held past their date, all counted from the Permit Log.', [
    LST('job_type', 'Job type', 'jobtype', 26, required=True),
    CA('permits', 'Permits', 'int', 'COUNTIFS({range:permits.job_type},{col:job_type})', 8), CA('avg_approve', 'Average days to approve', 'num', 'IFERROR(AVERAGEIFS({range:permits.days_to_approve},{range:permits.job_type},{col:job_type}),0)', 10),
    CA('avg_inspect', 'Average days to inspect', 'num', 'IFERROR(AVERAGEIFS({range:permits.days_to_inspect},{range:permits.job_type},{col:job_type}),0)', 10),
    CA('jobs_held', 'Jobs held', 'int', 'COUNTIFS({range:permits.job_type},{col:job_type},{range:permits.days_held},">0")', 8)],
  D.permit_wait_d(), 30))
# 19 repeat visits
tables.append(T('repeats', 'Repeat Visits', 'Repeat visits at the same site inside the repeat window',
  'Type a job: the site, the previous job at the site, the days between, the technician of the earlier job and the cost shown against the earlier price fill in by themselves.', [
    C('job_id', 'Job', 'text', 10, required=True),
    CA('date', 'Date', 'date', LKD('jobs.date', 'jobs.job_id', 'job_id'), 11), CA('site_id', 'Site', 'text', LKT('jobs.site_id', 'jobs.job_id', 'job_id'), 10), CA('site_ref', 'Site reference', 'text', LKT('jobs.site_ref', 'jobs.job_id', 'job_id'), 11),
    CA('job_type', 'Job type', 'text', LKT('jobs.job_type', 'jobs.job_id', 'job_id'), 26), CA('technician', 'Technician', 'text', LKT('jobs.technician', 'jobs.job_id', 'job_id'), 16),
    CA('prev_date', 'Previous job on', 'date', LKD('jobs.prev_date', 'jobs.job_id', 'job_id'), 11),
    CA('prev_job', 'Previous job', 'text', 'IFERROR(INDEX({range:jobs.job_id},MATCH({col:site_id}&"|"&{col:prev_date},{range:jobs.site_date},0)),"")', 10),
    CA('prev_technician', 'Technician of the earlier job', 'text', 'IFERROR(INDEX({range:jobs.technician},MATCH({col:site_id}&"|"&{col:prev_date},{range:jobs.site_date},0)),"")', 16),
    CA('prev_price', 'Earlier job price', 'money', 'IFERROR(INDEX({range:jobs.price},MATCH({col:site_id}&"|"&{col:prev_date},{range:jobs.site_date},0)),0)', 11),
    CA('days_between', 'Days between', 'int', 'IFERROR({col:date}-{col:prev_date},"")', 8), CA('cost', 'Cost of this visit', 'money', LKN('jobs.cost', 'jobs.job_id', 'job_id'), 11),
    CA('flag', 'Flag', 'text', 'IF(ISNUMBER({col:days_between}),IF({col:days_between}<={set:repeat_days},%s,%s),%s)' % (ck('Possible callback'), ck('Later repeat'), ck('No earlier visit')), 16),
    CA('cost_share', 'Cost against earlier price', 'pct', 'IFERROR({col:cost}/{col:prev_price},0)', 10), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.repeats_d(), 60, [A('flag', '= ' + ck('Possible callback'), 'warn')]))
# 20 work orders
JL = lambda c: LKT('jobs.' + c, 'jobs.job_id', 'job_id')
tables.append(T('workorders', 'Work Orders', 'Work order list for the coming days',
  'Type the job ids of the coming days: date, arrival window, site reference, area, job type, reason, parts and permit status, technician, van and the phones for the messages fill in by themselves.', [
    C('job_id', 'Job', 'text', 10, required=True),
    CA('date', 'Date', 'date', LKD('jobs.date', 'jobs.job_id', 'job_id'), 11),
    CA('window', 'Arrival window', 'text', 'IFERROR(INDEX({range:jobs.start},MATCH({col:job_id},{range:jobs.job_id},0))&" - "&(VALUE(LEFT(INDEX({range:jobs.start},MATCH({col:job_id},{range:jobs.job_id},0)),2))+2)&":"&RIGHT(INDEX({range:jobs.start},MATCH({col:job_id},{range:jobs.job_id},0)),2),"")', 14),
    CA('site_id', 'Site', 'text', JL('site_id'), 10), CA('site_ref', 'Site reference', 'text', JL('site_ref'), 11), CA('area', 'Area', 'text', JL('area'), 11), CA('job_type', 'Job type', 'text', JL('job_type'), 26),
    CA('reason', 'Reason', 'text', JL('reason'), 10), CA('technician', 'Technician', 'text', JL('technician'), 16), CA('assistant', 'Assistant', 'text', JL('assistant'), 16), CA('van', 'Van', 'text', JL('van'), 8),
    CA('hours', 'Hours on site', 'num', LKN('jobs.hours', 'jobs.job_id', 'job_id'), 8), CA('minutes', 'Drive minutes', 'int', 'ROUND(IFERROR(INDEX({range:jobs.drive_hours},MATCH({col:job_id},{range:jobs.job_id},0)),0)*60,0)', 8),
    CA('parts_ready', 'Parts ready', 'text', JL('parts_ready'), 9), CA('permit_needed', 'Permit needed', 'text', JL('permit_needed'), 9), CA('equipment', 'Equipment', 'text', JL('equipment_id'), 10),
    CA('account', 'Account', 'text', LKT('sites.account', 'sites.site_id', 'site_id'), 10), CA('phone', 'Customer phone', 'text', LKT('sites.phone', 'sites.site_id', 'site_id'), 18),
    CA('diag_fee', 'Diagnostic fee', 'money', '{set:diag_fee}', 10), CA('company', 'Company', 'text', '{set:company}', 24), TECHPH(),
    CA('assistant_phone', 'Assistant phone', 'text', 'IF({col:assistant}=%s,%s,IF({col:assistant}=%s,%s,""))' % (tok('crew', 'Amira Haddad'), ph(D.TECH_PHONES[6]), tok('crew', "Liam O'Connell"), ph(D.TECH_PHONES[7])), 18),
    CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CONST('supplier_phone', 'Equipment supplier phone', D.SUP_PHONE), CONST('parts_phone', 'Parts counter phone', D.PARTS_PHONE),
    CONST('elec_phone', 'Electrical subcontractor phone', D.ELEC_PHONE), CONST('sheet_phone', 'Sheet-metal subcontractor phone', D.SHEET_PHONE)],
  D.workorders_d(), 60, [A('parts_ready', '= ' + NO, 'warn'), A('permit_needed', '= ' + YES, 'warn')]))
for _t in tables: _t['rows'] = max(50, _t['rows'])
assert len(tables) == 20, len(tables)
