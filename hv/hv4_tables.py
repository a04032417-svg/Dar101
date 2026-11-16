"""HVAC suite part 4: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv4_lists import *
import hv4_data as DD

YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def ph(v): return '"%s"' % v
def LKP(rng_, name_col, my, default='""'): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),%s)' % (rng_, my, name_col, default)
COMP, SCHED, PROG = tok('jobstatus', 'Completed'), tok('jobstatus', 'Scheduled'), tok('jobstatus', 'In progress')
WON, LOST, OPEN_ = tok('estoutcome', 'Won'), tok('estoutcome', 'Lost'), tok('estoutcome', 'Open')
OWNDRAW, SAL = tok('paypaid', 'Owner draw'), tok('paypaid', 'Salary')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
LW = '({today}-WEEKDAY({today},3)-7)'                         # Monday of the last full week
NW = '({today}-WEEKDAY({today},3)+7)'                         # Monday of next week
TS = lambda c_: '{range:timesheets.%s}' % c_
JB = lambda c_: '{range:jobs.%s}' % c_
def WK(n, t='timesheets'): return '{range:%s.week},">="&(%s-%d),{range:%s.week},"<="&%s' % (t, LW, 7 * (n - 1), t, LW)   # last n full weeks
W12M = '{range:timesheets.week},">="&({today}-365),{range:timesheets.week},"<="&{today}'
J13 = '{range:jobs.date},">="&(%s-84),{range:jobs.date},"<="&(%s+6)' % (LW, LW)                                  # jobs of the last 13 full weeks
def OPH(): return CA('owner_phone', 'Owner phone', 'text', ph(DD.OWNER_PH), 18)
def OFF(): return CA('office_phone', 'Office manager phone', 'text', ph(DD.OFFICE_PH), 18)
def COMPANY_COL(): return CA('company', 'Company', 'text', '{set:company}', 24)
def TECHPH(my='technician'): return CA('tech_phone', 'Technician phone', 'text', LKP('team.phone', 'team.name', my), 18)

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('util_target', 'Utilisation wanted (billed over clock hours), your own', 'pct', UTIL_TARGET),
    S('margin_target', 'Job margin wanted (a typical range, check your own numbers)', 'pct', 0.50), S('callback_target', 'Callback rate wanted, a typical range, check yours', 'pct', CALLBACK_TARGET),
    S('close_target', 'Close rate wanted: estimates won over estimates decided', 'pct', CLOSE_TARGET), S('ticket_target', 'Average ticket wanted: the amount billed on one job', 'money', 350),
    S('burden_pct', 'Employer extras on pay (confirm with your adviser)', 'pct', BURDEN_PCT), S('vehicle_hour', 'Vehicle cost per hour on the road', 'money', VEHICLE_HOUR),
    S('capacity_hours', 'Productive hours in a technician day, drive time included', 'num', 8.5), S('lead_techs', 'Technicians who run their own jobs', 'int', 6),
    S('overtime_after', 'Hours a week before overtime (confirm with your adviser)', 'int', 40), S('overtime_mult', 'Overtime pay multiplier (confirm with your adviser)', 'num', 1.5),
    S('overtime_limit', 'Overtime hours in 4 weeks that trigger a talk', 'int', 8), S('spiff_agreement', 'Spiff for each maintenance agreement sold', 'money', SPIFF_AGREEMENT),
    S('clawback_days', 'Days a callback or unpaid invoice takes commission back', 'int', 60), S('clawback_pct', 'Share of the commission taken back (your own rule)', 'pct', 0.50),
    S('commission_base', 'Commission is paid on', 'list', key('cbase', 'Sold'), list='cbase'), S('cash_floor', 'Lowest cash balance you want to keep', 'money', CASH_FLOOR),
    S('cash_now', 'Cash in the bank today', 'money', DD.ST['cash_now']), S('budget_tolerance', 'Share over planned monthly pay that counts as over', 'pct', 0.05),
]
assert len(settings) == 20
tables = []

# 1 timesheets
OTRATE = 'IFERROR(INDEX({range:team.hourly_rate},MATCH({col:technician},{range:team.name},0)),0)'
tables.append(T('timesheets', 'Timesheets', 'Weekly timesheets with billed, drive, shop and idle hours',
  'One row per person and week: hours on the clock split into billed, drive, shop and idle time, overtime, pay and loaded cost; utilisation, the cost of idle time, the unpaid-to-billed gap and the overtime cost fill in by themselves.', [
    C('ts_id', 'Timesheet', 'text', 10, required=True), C('week', 'Week (Monday)', 'date', 12), C('month', 'Month', 'date', 11), LST('technician', 'Technician', 'crew', 17), C('role', 'Role', 'text', 17),
    C('clock_hours', 'Clock hours', 'num', 9), C('billed_hours', 'Billed hours', 'num', 9), C('drive_hours', 'Drive hours', 'num', 9), C('shop_hours', 'Shop hours', 'num', 9), C('idle_hours', 'Idle hours', 'num', 9),
    C('overtime_hours', 'Overtime hours', 'num', 9), C('paid_hours', 'Paid hours', 'num', 9), C('gross_pay', 'Gross pay', 'money', 12), C('loaded_cost', 'Loaded cost', 'money', 12), C('on_time', 'Submitted on time', 'bool', 10),
    CA('utilisation', 'Utilisation', 'pct', 'IF({col:clock_hours}>0,{col:billed_hours}/{col:clock_hours},0)', 10),
    CA('cost_hour', 'Cost per paid hour', 'money', 'IF({col:paid_hours}>0,{col:loaded_cost}/{col:paid_hours},0)', 11),
    CA('idle_cost', 'Idle cost', 'money', '{col:idle_hours}*{col:cost_hour}', 11), CA('unbilled_hours', 'Paid minus billed hours', 'num', '{col:paid_hours}-{col:billed_hours}', 10),
    CA('unbilled_cost', 'Unbilled labour cost', 'money', '{col:unbilled_hours}*{col:cost_hour}', 12),
    CA('overtime_cost', 'Overtime cost', 'money', '{col:overtime_hours}*%s*{set:overtime_mult}*(1+{set:burden_pct})' % OTRATE, 11),
    CA('util_flag', 'Utilisation check', 'text', 'IF({col:utilisation}>={set:util_target},%s,%s)' % (ck('On target'), ck('Below target')), 14),
    CA('tm_unbilled', 'Unbilled cost of the month', 'money', 'SUMIFS({range:timesheets.unbilled_cost},{range:timesheets.technician},{col:technician},{range:timesheets.month},{col:month})', 12),
    CA('row_w', 'Share of the person-month', 'num', '1/COUNTIFS({range:timesheets.month},{col:month},{range:timesheets.technician},{col:technician})', 12),
    CA('tm_rank', 'Rank in the month', 'int', 'ROUND(SUMIFS({range:timesheets.row_w},{range:timesheets.month},{col:month},{range:timesheets.tm_unbilled},">"&{col:tm_unbilled}),0)+1', 10),
    CA('rank_key', 'Rank key for the lookup', 'num', '{col:month}*10+{col:tm_rank}', 14), CA('approve_by', 'Approve overtime before', 'date', '{col:week}+8', 11),
    TECHPH(), OPH(), OFF(), COMPANY_COL()],
  DD.timesheets_d(), 1500, [A('util_flag', '= ' + ck('Below target'), 'warn'), A('overtime_hours', '> 0', 'warn'), A('on_time', '= ' + NO, 'bad')]))

# 2 payroll
PLAN = 'IFERROR(IF({col:pay_type}=%s,{col:gross},IF({col:pay_type}=%s,INDEX({range:team.monthly_salary},MATCH({col:person},{range:team.name},0)),INDEX({range:team.hourly_rate},MATCH({col:person},{range:team.name},0))*INDEX({range:team.hours_week},MATCH({col:person},{range:team.name},0))*52/12)),0)' % (OWNDRAW, SAL)
tables.append(T('payroll', 'Payroll', 'Monthly payroll by person with commission and employer extras',
  'One row per person and month: hours, gross pay, commission and spiffs, employer extras and the total; the planned pay, the share over plan, the cost per hour and the month total fill in by themselves. Pay figures: confirm with your adviser.', [
    C('pay_id', 'Pay row', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('person', 'Person', 'payperson', 17), C('role', 'Role', 'text', 17), LST('pay_type', 'Pay type', 'paypaid', 11),
    C('hours', 'Hours', 'num', 9), C('gross', 'Gross pay', 'money', 12), C('commission', 'Commission and spiffs', 'num', 12), C('burden', 'Employer extras', 'money', 12), C('total', 'Total', 'money', 12),
    C('pay_date', 'Pay date', 'date', 11), LST('status', 'Status', 'paystatus', 10),
    CA('plan_gross', 'Planned gross pay', 'money', PLAN, 12), CA('over_plan', 'Over plan', 'pct', 'IF({col:plan_gross}>0,{col:gross}/{col:plan_gross}-1,0)', 9),
    CA('within_plan', 'Within plan (1 or 0)', 'int', 'IF({col:over_plan}<={set:budget_tolerance},1,0)', 9),
    CA('cost_hour', 'Cost per hour', 'money', 'IF({col:hours}>0,{col:total}/{col:hours},0)', 10),
    CA('month_total', 'Payroll of the month', 'money', 'SUMIFS({range:payroll.total},{range:payroll.month},{col:month},{range:payroll.pay_type},"<>"&%s)' % OWNDRAW, 13),
    CA('person_phone', 'Phone', 'text', LKP('team.phone', 'team.name', 'person'), 18), CA('acct_phone', 'Accountant phone', 'text', ph(DD.ACCT_PH), 18), OFF(), OPH(), COMPANY_COL()],
  DD.payroll_d(), 400, [A('over_plan', '> {set:budget_tolerance}', 'warn'), A('status', '= ' + tok('paystatus', 'Accruing'), 'warn')]))

# 3 team
tables.append(T('team', 'Team', 'Team and outside contacts with pay terms',
  'The owner, the office manager, the field crew and six outside contacts: role, pay type, rate, salary, hours a week and commission percent; the all-in cost per hour, years of service, the next review date and the van service date fill in by themselves.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 18), C('team', 'Team', 'text', 9), C('pay_type', 'Pay type', 'text', 11), C('phone', 'Phone', 'text', 18),
    C('hourly_rate', 'Hourly rate', 'money', 11), C('monthly_salary', 'Monthly salary', 'num', 12), C('hours_week', 'Hours a week', 'int', 9), C('commission_pct', 'Commission percent', 'pct', 10),
    C('assignment', 'Assignment', 'text', 26), C('trade', 'Trade', 'text', 10), C('start', 'Start', 'date', 11), C('van_service', 'Van service date', 'date', 11),
    CA('all_in_hour', 'All-in cost per hour', 'money', 'IF({col:monthly_salary}>0,{col:monthly_salary}/({col:hours_week}*52/12)*(1+{set:burden_pct}),{col:hourly_rate}*(1+{set:burden_pct}))', 11),
    CA('years', 'Years of service', 'num', '({today}-{col:start})/365', 9),
    CA('next_review', 'Next review', 'date', 'EDATE({col:start},3*(INT(((YEAR({today})-YEAR({col:start}))*12+MONTH({today})-MONTH({col:start}))/3)+1))', 11),
    CA('ride_with', 'Rides with', 'text', 'IF(LEN({col:assignment})>5,IFERROR(INDEX({range:vans.technician},MATCH(RIGHT({col:assignment},5),{range:vans.van},0)),""),"")', 17),
    CA('ride_date', 'Ride-along date', 'date', '{today}+7-WEEKDAY({today},3)', 11),
    CA('jobs_assisted', 'Jobs assisted, 13 weeks', 'int', 'COUNTIFS({range:jobs.assistant},{col:name},{range:jobs.status},%s,%s)' % (COMP, J13), 9),
    CA('billed_13w', 'Billed hours, 13 weeks', 'num', 'SUMIFS(%s,%s,{col:name},%s)' % (TS('billed_hours'), TS('technician'), WK(13)), 10),
    CA('clock_13w', 'Clock hours, 13 weeks', 'num', 'SUMIFS(%s,%s,{col:name},%s)' % (TS('clock_hours'), TS('technician'), WK(13)), 10),
    CA('field_count', 'Field crew', 'int', 'COUNTIFS({range:team.trade},"<>")', 8), CA('hours_year', 'Crew clock hours, 12 months', 'num', 'SUMIFS(%s,%s)' % (TS('clock_hours'), W12M), 12),
    CA('ins_phone', 'Insurance agent phone', 'text', ph(DD.INS_PH), 18), CA('counter_phone', 'Parts counter phone', 'text', ph(DD.COUNTER_PH), 18), OFF(), OPH(), COMPANY_COL()],
  DD.team_d(), 40, []))

# 4 pay models
tables.append(T('pay_models', 'Pay Models', 'The four pay models and how each is worked out',
  'The four ways a technician can be paid; the Pay Calculator and the Pay Model Comparison read this list. Pay rules differ by place: confirm with your adviser.', [
    C('model', 'Pay model', 'text', 22, required=True), C('how', 'How pay is worked out', 'text', 30), C('note', 'Owner note', 'text', 30)], DD.pay_models_d(), 10))
# 5 commission rules
tables.append(T('comm_rules', 'Commission Rules', 'Commission rules with base, percent and clawback window',
  'Your own rule for each kind of sale: paid on sold or on collected work, the percent, the days inside which a callback or an unpaid invoice takes it back, and the share taken back. Set your own, confirm with your adviser.', [
    C('rule', 'Rule', 'text', 22, required=True), LST('base', 'Paid on', 'cbase', 11), C('percent', 'Percent', 'pct', 9), C('clawback_days', 'Clawback days', 'int', 9), C('clawback_pct', 'Share taken back', 'pct', 10), C('note', 'Note', 'text', 30),
    CA('windows_end', 'Window of a job today ends', 'date', '{today}-{col:clawback_days}', 12)], DD.comm_rules_d(), 30))
# 6 commission statements
tables.append(T('comm_stmts', 'Commission Statements', 'Commission, spiffs and clawbacks per technician and month',
  'One row per technician and month: jobs, sold and collected work, agreements sold and the clawback bases; commission on your base, spiffs, clawback and the total to pay fill in by themselves. Confirm pay rules with your adviser.', [
    C('st_id', 'Statement', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('technician', 'Technician', 'tech', 17), C('jobs_done', 'Jobs done', 'int', 8), C('sold', 'Sold', 'money', 12),
    C('collected', 'Collected', 'money', 12), C('agreements', 'Agreements sold', 'int', 9), C('clawback_base', 'Clawback base, callbacks', 'num', 11), C('unpaid_base', 'Clawback base, unpaid', 'num', 11),
    CA('rate', 'Commission percent', 'pct', LKP('team.commission_pct', 'team.name', 'technician', '0'), 10),
    CA('base_used', 'Base used', 'money', 'IF({set:commission_base}=%s,{col:sold},{col:collected})' % tok('cbase', 'Sold'), 12),
    CA('commission', 'Commission', 'money', 'ROUND({col:base_used}*{col:rate},2)', 11),
    CA('spiffs', 'Spiffs', 'money', '{col:agreements}*SUMIFS({range:spiffs.amount},{range:spiffs.item},%s)' % tok('spiffitem', 'Maintenance agreement sold'), 10),
    CA('clawback', 'Clawback', 'money', 'ROUND(({col:clawback_base}+{col:unpaid_base})*{col:rate}*{set:clawback_pct},2)', 10), CA('total', 'Total to pay', 'money', '{col:commission}+{col:spiffs}-{col:clawback}', 11),
    CA('month_commission', 'Commission of the month, all', 'money', 'SUMIFS({range:comm_stmts.commission},{range:comm_stmts.month},{col:month})', 12),
    CA('month_clawback', 'Clawbacks of the month, all', 'money', 'SUMIFS({range:comm_stmts.clawback},{range:comm_stmts.month},{col:month})', 12),
    CA('month_spiffs', 'Spiffs of the month, all', 'money', 'SUMIFS({range:comm_stmts.spiffs},{range:comm_stmts.month},{col:month})', 12),
    TECHPH(), CA('acct_phone', 'Accountant phone', 'text', ph(DD.ACCT_PH), 18), OPH(), OFF(), COMPANY_COL()],
  DD.stmts_d(), 120, [A('clawback', '> 0', 'warn')]))
# 7 spiffs
tables.append(T('spiffs', 'Spiff List', 'Spiff amounts for each item sold',
  'A fixed bonus for each item sold: the amount and when it is paid. The statements and the Spiff Tracker read these amounts.', [
    LST('item', 'Item', 'spiffitem', 28, required=True), C('amount', 'Spiff amount', 'money', 12), C('note', 'Note', 'text', 30)], DD.spiffs_d(), 12))
# 8 jobs
tables.append(T('jobs', 'Jobs', 'Recent jobs with hours, price, margin and callback flag',
  'One row per job of the last 13 weeks and the next week: who did it, hours on site and driving, price, margin, callback and agreement sold; revenue and margin of finished jobs fill in by themselves.', [
    C('job_id', 'Job', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('week', 'Week (Monday)', 'date', 12), LST('technician', 'Technician', 'tech', 17), C('assistant', 'Assistant', 'text', 16),
    LST('job_type', 'Job type', 'jobtype', 26), LST('status', 'Status', 'jobstatus', 12), C('hours', 'Hours on site', 'num', 9), C('drive_hours', 'Drive hours', 'num', 9), C('price', 'Price', 'money', 11),
    C('margin', 'Margin', 'money', 11), C('callback', 'Callback', 'bool', 9), C('agreement_sold', 'Agreement sold', 'bool', 9),
    CA('revenue', 'Revenue', 'money', 'IF(AND({col:status}=%s,{col:callback}<>%s),{col:price},0)' % (COMP, YES), 11),
    CA('margin_done', 'Margin of finished jobs', 'money', 'IF({col:status}=%s,{col:margin},0)' % COMP, 12)],
  DD.jobs_d(), 1500, [A('callback', '= ' + YES, 'warn'), A('status', '= ' + tok('jobstatus', 'Cancelled'), 'warn')]))
# 9 callbacks
tables.append(T('callbacks', 'Callbacks', 'Callbacks, a return visit to fix the same job',
  'One row per callback: the technician of the original job, the reason, the cost and the days after the job; the commission clawback it triggers fills in by itself.', [
    C('callback_id', 'Callback', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('original_job', 'Original job', 'text', 11), LST('technician', 'Technician', 'tech', 17),
    LST('job_type', 'Job type', 'jobtype', 26), LST('reason', 'Reason', 'cbreason', 20), C('cost', 'Cost', 'money', 11), C('days_after', 'Days after the job', 'int', 9), C('job_price', 'Commissioned value of the job', 'num', 12),
    CA('rate', 'Commission percent', 'pct', LKP('team.commission_pct', 'team.name', 'technician', '0'), 10),
    CA('in_window', 'Inside the clawback window (1 or 0)', 'int', 'IF({col:days_after}<={set:clawback_days},1,0)', 10),
    CA('clawback', 'Clawback', 'money', 'ROUND(IF(AND({col:job_price}>0,{col:in_window}=1),{col:job_price}*{col:rate}*{set:clawback_pct},0),2)', 10),
    TECHPH(), OPH(), COMPANY_COL()], DD.callbacks_d(), 600, [A('clawback', '> 0', 'warn')]))
# 10 estimates
tables.append(T('estimates', 'Estimates', 'Recent estimates with outcome and price won',
  'One row per estimate: technician, job type, value, outcome and price won; the won flag fills in by itself and feeds the close rate on the scorecard.', [
    C('estimate_id', 'Estimate', 'text', 11, required=True), C('date', 'Date', 'date', 11), LST('technician', 'Technician', 'tech', 17), LST('job_type', 'Job type', 'jobtype', 26), LST('outcome', 'Outcome', 'estoutcome', 10),
    C('est_value', 'Estimate value', 'money', 12), C('price_won', 'Price won', 'num', 12),
    CA('won_flag', 'Won (1 or 0)', 'int', 'IF({col:outcome}=%s,1,IF({col:outcome}=%s,0,""))' % (WON, LOST), 8)], DD.estimates_d(), 800, [A('outcome', '= ' + WON, 'good'), A('outcome', '= ' + LOST, 'warn')]))
# 11 reviews
tables.append(T('reviews', 'Reviews and Referrals', 'Reviews and referrals per technician and month',
  'One row per technician and month: jobs, review requests sent, reviews received and referrals (counts only); the response rate fills in by itself.', [
    C('row_id', 'Row', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('technician', 'Technician', 'tech', 17), C('jobs', 'Jobs', 'int', 8), C('requests_sent', 'Requests sent', 'int', 9),
    C('reviews_received', 'Reviews received', 'int', 9), C('referrals', 'Referrals', 'int', 9),
    CA('response_rate', 'Response rate', 'pct', 'IF({col:requests_sent}>0,{col:reviews_received}/{col:requests_sent},0)', 9)], DD.reviews_d(), 300))
# 12 scorecard (each technician twice: the last 13 weeks and the last 4 weeks)
T_ = '{col:technician}'
P13, P4 = tok('period', 'Last 13 weeks'), tok('period', 'Last 4 weeks')
JW = '{range:jobs.date},">="&{col:from_w},{range:jobs.date},"<="&(%s+6)' % LW
TW_ = '{range:timesheets.week},">="&{col:from_w},{range:timesheets.week},"<="&%s' % LW
def ONLY13(c_): return 'IF({col:sel}=1,{col:%s},"")' % c_
scorecard_cols = [
    C('row_id', 'Row', 'text', 8, required=True), LST('technician', 'Technician', 'tech', 17), LST('period', 'Period', 'period', 14), C('jobs_12m', 'Jobs, 12 months', 'int', 9), C('revenue_12m', 'Revenue, 12 months', 'money', 13),
    CA('sel', 'Is the 13-week row (1 or 0)', 'int', 'IF({col:period}=%s,1,0)' % P13, 8),
    CA('from_w', 'From (Monday)', 'date', 'IF({col:period}=%s,%s-84,%s-21)' % (P13, LW, LW), 11), 
    CA('jobs_w', 'Jobs in the period', 'int', 'COUNTIFS(%s,%s,%s,%s,%s,%s,%s)' % (JB('technician'), T_, JB('status'), COMP, JB('callback'), NO, JW), 8),
    CA('revenue_w', 'Revenue in the period', 'money', 'SUMIFS(%s,%s,%s,%s)' % (JB('revenue'), JB('technician'), T_, JW), 12),
    CA('ticket', 'Average ticket', 'money', 'IFERROR({col:revenue_w}/{col:jobs_w},0)', 11), CA('ticket_12m', 'Average ticket, 12 months', 'money', 'IFERROR({col:revenue_12m}/{col:jobs_12m},0)', 11),
    CA('days_w', 'Days on the clock', 'num', 'SUMIFS(%s,%s,%s,%s)/8' % (TS('clock_hours'), TS('technician'), T_, TW_), 10),
    CA('rev_day', 'Revenue per day', 'money', 'IFERROR({col:revenue_w}/{col:days_w},0)', 11),
    CA('rev_day_12m', 'Revenue per day, 12 months', 'money', 'IFERROR({col:revenue_12m}/(SUMIFS(%s,%s,%s,%s)/8),0)' % (TS('clock_hours'), TS('technician'), T_, W12M), 11),
    CA('close_rate', 'Close rate', 'pct', 'IFERROR(COUNTIFS({range:estimates.technician},%s,{range:estimates.outcome},%s,{range:estimates.date},">="&({today}-365))/(COUNTIFS({range:estimates.technician},%s,{range:estimates.outcome},%s,{range:estimates.date},">="&({today}-365))+COUNTIFS({range:estimates.technician},%s,{range:estimates.outcome},%s,{range:estimates.date},">="&({today}-365))),0)' % (T_, WON, T_, WON, T_, LOST), 9),
    CA('cb_12m', 'Callbacks, 12 months', 'int', 'COUNTIFS({range:callbacks.technician},%s,{range:callbacks.date},">="&({today}-365),{range:callbacks.date},"<="&{today})' % T_, 9),
    CA('callback_rate', 'Callback rate', 'pct', 'IFERROR({col:cb_12m}/{col:jobs_12m},0)', 9),
    CA('util_w', 'Utilisation in the period', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,%s)/SUMIFS(%s,%s,%s,%s),0)' % (TS('billed_hours'), TS('technician'), T_, TW_, TS('clock_hours'), TS('technician'), T_, TW_), 9),
    CA('util_12m', 'Utilisation, 12 months', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,%s)/SUMIFS(%s,%s,%s,%s),0)' % (TS('billed_hours'), TS('technician'), T_, W12M, TS('clock_hours'), TS('technician'), T_, W12M), 9),
    CA('idle_4w', 'Idle hours, 4 weeks', 'num', 'SUMIFS(%s,%s,%s,%s)' % (TS('idle_hours'), TS('technician'), T_, WK(4)), 9),
    CA('overtime_4w', 'Overtime hours, 4 weeks', 'num', 'SUMIFS(%s,%s,%s,%s)' % (TS('overtime_hours'), TS('technician'), T_, WK(4)), 9),
    CA('reviews_90', 'Reviews, last 3 months', 'int', 'SUMIFS({range:reviews.reviews_received},{range:reviews.technician},%s,{range:reviews.month},">="&EDATE(%s,-3))' % (T_, MS), 9),
    CA('gp_w', 'Job margin in the period', 'money', 'SUMIFS(%s,%s,%s,%s)' % (JB('margin_done'), JB('technician'), T_, JW), 12),
    CA('unbilled_w', 'Unbilled labour cost in the period', 'money', 'SUMIFS(%s,%s,%s,%s)' % (TS('unbilled_cost'), TS('technician'), T_, TW_), 12),
    CA('net_margin', 'Margin after unbilled time', 'money', '{col:gp_w}-{col:unbilled_w}', 12),
    CA('points', 'Points of 6', 'int', 'IF({col:ticket}>={col:ticket_12m},1,0)+IF({col:close_rate}>={set:close_target},1,0)+IF({col:callback_rate}<={set:callback_target},1,0)+IF({col:util_w}>={set:util_target},1,0)+IF({col:rev_day}>={col:rev_day_12m},1,0)+IF({col:reviews_90}>=1,1,0)', 8),
    CA('verdict', 'Verdict', 'text', 'IF({col:points}>=5,%s,IF({col:points}>=3,%s,%s))' % (ck('Strong'), ck('Watch'), ck('Talk')), 9),
    CA('rev_13', 'Revenue, 13-week row', 'money', ONLY13('revenue_w'), 11), CA('days_13', 'Days, 13-week row', 'num', ONLY13('days_w'), 9), CA('net_13', 'Margin after unbilled time, 13-week row', 'money', ONLY13('net_margin'), 12),
    CA('idle_13', 'Idle hours, 13-week row', 'num', ONLY13('idle_4w'), 9), CA('ticket_13', 'Ticket, 13-week row', 'money', ONLY13('ticket'), 10), CA('close_13', 'Close rate, 13-week row', 'pct', ONLY13('close_rate'), 9),
    CA('score_key', 'Rank key for the lookup', 'num', 'IF({col:sel}=1,{col:points}+{col:net_margin}/10000000,"")', 10), CA('rank_pts', 'Rank', 'int', 'IF({col:sel}=1,COUNTIF({range:scorecard.score_key},">"&{col:score_key})+1,"")', 7),
    CA('overtime_limit', 'Overtime limit, 4 weeks', 'int', '{set:overtime_limit}', 9), TECHPH(), OPH(), COMPANY_COL()]
tables.append(T('scorecard', 'Scorecard by Technician', 'Technician scorecard against each own history',
  'Each lead technician twice, last 13 weeks and last 4 weeks: ticket, close rate, callback rate, utilisation, revenue per day and reviews against own history; points and verdict fill in. Type jobs and revenue of 12 months.', scorecard_cols, DD.scorecard_d(), 60,
  [A('verdict', '= ' + ck('Talk'), 'bad'), A('verdict', '= ' + ck('Watch'), 'warn'), A('verdict', '= ' + ck('Strong'), 'good')]))
# 13 hours by week
HW = lambda c_: 'SUMIFS(%s,%s,{col:week})' % (TS(c_), TS('week'))
tables.append(T('hours_week', 'Hours by Week', 'Hours by week against the utilisation target',
  'One row per week: clock, billed, drive, shop and idle hours of the whole crew; utilisation against the target and against the same week last year, the hours to fill and the cost of idle time fill in by themselves.', [
    C('week', 'Week (Monday)', 'date', 12, required=True), LST('wk', 'Week number', 'wk26', 10),
    CA('clock_hours', 'Clock hours', 'num', HW('clock_hours'), 9), CA('billed_hours', 'Billed hours', 'num', HW('billed_hours'), 9), CA('drive_hours', 'Drive hours', 'num', HW('drive_hours'), 9),
    CA('shop_hours', 'Shop hours', 'num', HW('shop_hours'), 9), CA('idle_hours', 'Idle hours', 'num', HW('idle_hours'), 9), CA('overtime_hours', 'Overtime hours', 'num', HW('overtime_hours'), 9),
    CA('utilisation', 'Utilisation', 'pct', 'IF({col:clock_hours}>0,{col:billed_hours}/{col:clock_hours},0)', 10), CA('gap_to_target', 'Gap to the target', 'pct', '{col:utilisation}-{set:util_target}', 9),
    CA('shortfall', 'Hours to fill to reach the target', 'num', 'MAX(0,{set:util_target}*{col:clock_hours}-{col:billed_hours})', 11),
    CA('idle_cost', 'Idle cost', 'money', HW('idle_cost'), 11),
    CA('util_ly', 'Utilisation, same week last year', 'pct', 'IFERROR(SUMIFS(%s,%s,{col:week}-364)/SUMIFS(%s,%s,{col:week}-364),0)' % (TS('billed_hours'), TS('week'), TS('clock_hours'), TS('week')), 11),
    CA('late_count', 'Timesheets not on time', 'int', 'COUNTIFS(%s,{col:week},%s,%s)' % (TS('week'), TS('on_time'), NO), 9), OPH(), OFF(), CA('acct_phone', 'Accountant phone', 'text', ph(DD.ACCT_PH), 18), COMPANY_COL()],
  DD.hours_week_d(), 60, [A('gap_to_target', '< 0', 'warn'), A('late_count', '> 0', 'warn')]))
# 14 capacity by week
CWK = lambda c_: '{range:capacity_week.%s}' % c_
BASEIDX = 'IFERROR(SUMIFS(%s,%s,">="&(%s-77),%s,"<="&%s)/SUMIFS(%s,%s,">="&(%s-77),%s,"<="&%s),0)' % (CWK('booked_actual'), CWK('week'), LW, CWK('week'), LW, CWK('idx'), CWK('week'), LW, CWK('week'), LW)
tables.append(T('capacity_week', 'Capacity by Week', 'Booked against available hours for 26 weeks back and 25 ahead',
  'One row per week: the hours booked from your jobs, the expected hours for weeks not yet booked (your last 12 weeks times the season), the hours your technicians can work after leave, the gap and the capacity check.', [
    C('week', 'Week (Monday)', 'date', 12, required=True), C('booked_actual', 'Booked hours so far', 'num', 11),
    CA('idx', 'Seasonal index', 'num', 'IFERROR(INDEX({range:season_hours.demand_index},MATCH(MONTH({col:week}),{range:season_hours.month_no},0)),1)', 9),
    CA('season', 'Season', 'text', 'IFERROR(INDEX({range:season_hours.season},MATCH(MONTH({col:week}),{range:season_hours.month_no},0))&"","")', 16),
    CA('forecast', 'Expected hours', 'num', 'ROUND(%s*{col:idx},1)' % BASEIDX, 10),
    CA('booked_hours', 'Booked and expected hours', 'num', 'IF({col:week}<=%s,{col:booked_actual},MAX({col:booked_actual},{col:forecast}))' % LW, 11),
    CA('leave_hours', 'Hours lost to leave', 'num', 'SUMIFS({range:leave.lead_hours},{range:leave.start},">="&{col:week},{range:leave.start},"<"&({col:week}+7))', 10),
    CA('available_hours', 'Available hours', 'num', '{set:lead_techs}*5*{set:capacity_hours}-{col:leave_hours}', 10), CA('gap', 'Gap', 'num', '{col:available_hours}-{col:booked_hours}', 9),
    CA('cap_flag', 'Capacity check', 'text', 'IF({col:gap}<0,%s,IF({col:gap}<0.1*{col:available_hours},%s,%s))' % (ck('Over capacity'), ck('Tight'), ck('Slack')), 13),
    CA('fgap', 'Gap of weeks from now on', 'num', 'IF({col:week}>=%s+7,{col:gap},"")' % LW, 10), OPH(), COMPANY_COL()], DD.capacity_d(), 80, [A('cap_flag', '= ' + ck('Over capacity'), 'bad'), A('cap_flag', '= ' + ck('Tight'), 'warn')]))
# 15 season hours
tables.append(T('season_hours', 'Season Hours', 'Seasonal index and hours needed by month',
  'One row per month for the next 12 months: the demand index of the month (1.00 is an average month; set your own) and the hours of work and technicians needed; the payroll of the last 3 months sits beside it.', [
    C('month', 'Month', 'date', 11, required=True), C('demand_index', 'Seasonal index', 'num', 9), LST('season', 'Season', 'season', 16),
    CA('month_no', 'Month number', 'int', 'MONTH({col:month})', 8),
    CA('hours_needed', 'Hours needed', 'num', 'ROUND(IFERROR(SUMIFS(%s,%s,">="&(%s-77),%s,"<="&%s)/SUMIFS(%s,%s,">="&(%s-77),%s,"<="&%s),0)*{col:demand_index}*52/12,0)' % (CWK('booked_actual'), CWK('week'), LW, CWK('week'), LW, CWK('idx'), CWK('week'), LW, CWK('week'), LW), 10),
    CA('techs_needed', 'Technicians needed', 'num', '{col:hours_needed}/({set:capacity_hours}*5*52/12)', 10),
    CA('crew_gap', 'Technicians short or spare', 'num', '{set:lead_techs}-{col:techs_needed}', 10),
    CA('payroll_13w', 'Payroll, last 3 months', 'money', 'SUMIFS({range:payroll.total},{range:payroll.month},">="&EDATE(%s,-3),{range:payroll.month},"<"&%s,{range:payroll.pay_type},"<>"&%s)' % (MS, MS, OWNDRAW), 12),
    OPH(), COMPANY_COL()], DD.season_hours_d(), 14))
# 16 hire scenarios
AVGM = 'IFERROR(AVERAGEIFS(%s,%s,%s,%s,%s),0)' % (JB('margin_done'), JB('status'), COMP, JB('callback'), NO)
AVGH = 'IFERROR(AVERAGEIFS(%s,%s,%s,%s,%s),0)' % (JB('hours'), JB('status'), COMP, JB('callback'), NO)
CH13 = 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (TS('loaded_cost'), WK(13), TS('paid_hours'), WK(13))
W4O = '%s,">"&%s,%s,"<="&(%s+28),%s,"<0"' % (CWK('week'), LW, CWK('week'), LW, CWK('gap'))
W13O = '%s,">"&%s,%s,"<="&(%s+91),%s,"<0"' % (CWK('week'), LW, CWK('week'), LW, CWK('gap'))
tables.append(T('hire_scenarios', 'Hire Scenarios', 'Hire options with monthly cost and jobs needed to break even',
  'One row per hire option and ramp-up length: the monthly all-in cost, the margin a job adds before the technician pay, the jobs a week needed to break even and the cost of the ramp-up; the verdict reads your capacity gap.', [
    C('hs_id', 'Scenario', 'text', 9, required=True), LST('option', 'Option', 'hireopt', 17), C('ramp_months', 'Ramp-up months', 'int', 9),
    CA('hourly', 'Hourly rate of the role', 'money', 'IFERROR(AVERAGEIFS({range:team.hourly_rate},{range:team.role},{col:option}),0)', 10),
    CA('monthly_cost', 'Monthly cost, all in', 'money', 'ROUND({col:hourly}*40*52/12*(1+{set:burden_pct})+IF({col:option}=%s,0,AVERAGE({range:vans.lease_monthly})),0)' % tok('hireopt', 'Apprentice'), 11),
    CA('contribution', 'Margin a job adds before technician pay', 'money', 'ROUND(%s+%s*%s,2)' % (AVGM, AVGH, CH13), 12),
    CA('jobs_month', 'Jobs a month to break even', 'num', 'IFERROR({col:monthly_cost}/{col:contribution},0)', 10), CA('jobs_week', 'Jobs a week to break even', 'num', 'ROUND({col:jobs_month}/(52/12),1)', 10),
    CA('ramp_cost', 'Cost of the ramp-up', 'money', 'ROUND({col:monthly_cost}*{col:ramp_months}*0.5,0)', 11),
    CA('weeks_over', 'Weeks over capacity, next 13', 'int', 'COUNTIFS(%s)' % W13O, 9),
    CA('verdict', 'Verdict', 'text', 'IF(COUNTIFS(%s)>=2,%s,IF({col:weeks_over}>=1,%s,%s))' % (W4O, ck('Hire now'), ck('Hire before the season'), ck('Wait')), 17), OPH(), COMPANY_COL()],
  DD.hire_d(), 24, [A('verdict', '= ' + ck('Hire now'), 'bad'), A('verdict', '= ' + ck('Hire before the season'), 'warn')]))
# 17 overtime by technician
tables.append(T('overtime_tech', 'Overtime by Technician', 'Overtime hours and cost of the last 4 weeks',
  'One row per lead technician: the overtime hours and the overtime cost of the last 4 weeks, read from the timesheets.', [
    LST('technician', 'Technician', 'tech', 17, required=True),
    CA('overtime_hours', 'Overtime hours, 4 weeks', 'num', 'SUMIFS(%s,%s,{col:technician},%s)' % (TS('overtime_hours'), TS('technician'), WK(4)), 11),
    CA('overtime_cost', 'Overtime cost, 4 weeks', 'money', 'SUMIFS(%s,%s,{col:technician},%s)' % (TS('overtime_cost'), TS('technician'), WK(4)), 12)], DD.overtime_d(), 12, [A('overtime_hours', '> {set:overtime_limit}', 'bad')]))
# 18 vans
tables.append(T('vans', 'Vans', 'Vans with driver and monthly lease', 'The six vans, who drives each and the lease cost a month.', [
    C('van', 'Van', 'text', 9, required=True), C('technician', 'Technician', 'text', 24), C('lease_monthly', 'Lease a month', 'money', 12)], DD.vans_d(), 12))
# 19 leave and training
tables.append(T('leave', 'Leave and Training', 'Leave, sick days and training days',
  'One row per leave or training period: who, what kind, first and last day; the working days, the hours lost, the status and the people away at the same time fill in by themselves.', [
    C('leave_id', 'Leave', 'text', 9, required=True), LST('person', 'Person', 'crew', 17), LST('type', 'Type', 'leavetype', 13), C('start', 'First day', 'date', 11), C('end', 'Last day', 'date', 11),
    CA('days', 'Working days', 'int', 'NETWORKDAYS({col:start},{col:end})', 8), CA('hours_lost', 'Hours lost', 'num', '{col:days}*{set:capacity_hours}', 9),
    CA('lead_hours', 'Hours lost, lead technicians', 'num', 'IF(ISNUMBER(MATCH({col:person},{range:vans.technician},0)),{col:hours_lost},0)', 10),
    CA('status', 'Status', 'text', 'IF({col:end}<{today},%s,IF({col:start}<={today},%s,%s))' % (ck('Past'), ck('Current'), ck('Upcoming')), 11),
    CA('overlap', 'Others away at the same time', 'int', 'COUNTIFS({range:leave.start},"<="&{col:end},{range:leave.end},">="&{col:start})-1', 9),
    CA('tech_phone', 'Phone', 'text', LKP('team.phone', 'team.name', 'person'), 18), OFF(), CA('equip_phone', 'Equipment supplier phone', 'text', ph(DD.EQUIP_PH), 18), COMPANY_COL()],
  DD.leave_d(), 80, [A('overlap', '> 0', 'warn')]))
# 20 settings echo
tables.append(T('settings_echo', 'Settings Echo', 'The pay and capacity limits in use', 'The eight limits the pay and capacity pages read; change them on the Start sheet, not here.', [
    C('setting', 'Setting', 'text', 30, required=True),
    CA('value', 'Value', 'num', 'IFERROR(CHOOSE(MATCH({col:setting},{range:settings_echo.setting},0),{set:util_target}*100,{set:margin_target}*100,{set:overtime_after},{set:overtime_mult},{set:overtime_limit},{set:clawback_days},{set:clawback_pct}*100,{set:burden_pct}*100),0)', 10),
    C('note', 'Note', 'text', 30)], DD.echo_d(), 12))
assert len(tables) == 20, len(tables)

_TH = {
 'timesheets': ('Weekly timesheets with billed, drive, shop and idle hours', 'One row per person and week: clock, billed, drive, shop and idle hours, overtime and pay; utilisation, idle cost, unbilled cost and overtime cost fill in.'),
 'payroll': ('Monthly payroll by person', 'One row per person and month: hours, gross pay, commission, employer extras and total; planned pay, share over plan and the month total fill in. Confirm pay figures with your adviser.'),
 'team': (None, 'The owner, office manager, field crew and six outside contacts with role, pay, hours and commission percent; all-in cost per hour, years of service and next review fill in.'),
 'comm_rules': (None, 'Your own rule for each kind of sale: paid on sold or collected work, the percent, the clawback days and the share taken back. Set your own, confirm with your adviser.'),
 'comm_stmts': (None, 'One row per technician and month: sold and collected work, agreements sold and clawback bases; commission, spiffs, clawback and the total fill in. Confirm pay rules with your adviser.'),
 'hours_week': (None, 'One row per week: clock, billed, drive, shop and idle hours of the crew; utilisation against the target and last year, hours to fill and idle cost fill in.'),
 'capacity_week': ('Booked against available hours by week', 'One row per week: booked and expected hours, hours your technicians can work after leave, the gap and the capacity check fill in.'),
 'season_hours': (None, 'One row per month for 12 months: your seasonal index (1.00 is an average month); hours and technicians needed and the payroll of the last 3 months fill in.'),
 'hire_scenarios': (None, 'One row per hire option and ramp-up: monthly all-in cost, margin a job adds, jobs a week to break even and ramp-up cost fill in; the verdict reads your capacity gap.'),
 'scorecard': (None, 'Each lead technician for the last 13 weeks and the last 4 weeks: ticket, close, callback, utilisation, revenue per day and reviews against own history; points and verdict fill in.')}
for _t in tables:
    if _t['key'] in _TH:
        if _TH[_t['key']][0]: _t['title'] = _TH[_t['key']][0]
        _t['hint'] = _TH[_t['key']][1]
    _t['rows'] = max(_t['rows'], 50)
    assert len(_t['hint']) <= 200 and len(_t['title']) <= 60, (_t['key'], len(_t['hint']), len(_t['title']))
