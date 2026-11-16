"""HVAC suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv8_lists import *
import hv8_data as D

YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def EM(n): return 'EDATE(%s,%d)' % (MS, n)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def ph(v): return '"%s"' % v
def CONST(k, label, v): return CA(k, label, 'text', ph(v), 18)
def TECHPH(col='technician'): return CA('tech_phone', 'Technician phone', 'text', 'IFERROR(CHOOSE(MATCH({col:%s},{range:techs.technician},0),%s),"")' % (col, ','.join(ph(p) for p in D.TECH_PHONES[:6])), 18)
COMPLETED = tok('jobstatus', 'Completed')
OPEN, RENEWED = tok('rnstatus', 'Open'), tok('rnstatus', 'Renewed')
B_OVER, B_RED, B_AMB, B_GRN, B_DONE = [tok('band', b) for b in BANDS]
P3, P12, PP12 = tok('period', 'Last 3 months'), tok('period', 'Last 12 months'), tok('period', 'Previous 12 months')
G, AM, RD = ck('Green'), ck('Amber'), ck('Red')

settings = [
    S('company', 'Your company name', 'text', COMPANY),
    S('margin_target', 'Job margin wanted (a typical range, check your own numbers)', 'pct', 0.5),
    S('net_target', 'Net profit wanted before owner draw', 'pct', 0.12),
    S('util_target', 'Utilisation wanted, billed hours over clock hours', 'pct', UTIL_TARGET),
    S('callback_target', 'Callback rate wanted, return visits over repair jobs', 'pct', CALLBACK_TARGET),
    S('close_target', 'Close rate wanted, estimates won over estimates decided', 'pct', CLOSE_TARGET),
    S('lead_cost_target', 'Cost per booked job wanted', 'money', 150),
    S('renewal_target', 'Agreement renewals wanted, share renewed of those due', 'pct', 0.85),
    S('cash_floor', 'Lowest cash balance you want', 'money', CASH_FLOOR),
    S('cover_months', 'Cash cover wanted, months of fixed costs', 'int', 2),
    S('renewal_warn_days', 'Days before a renewal date that turn it red', 'int', RENEWAL_WARN_DAYS),
    S('renewal_amber_days', 'Days before a renewal date that turn it amber', 'int', 60),
    S('review_target', 'Reviews wanted, reviews over completed jobs', 'pct', 0.11),
    S('marketing_budget', 'Marketing budget wanted each month', 'money', 8000),
    S('rps_keep', 'Revenue per 1 spent at which a source is kept', 'num', 25),
    S('rps_drop', 'Revenue per 1 spent under which a source is dropped', 'num', 8),
    S('ageing_limit', 'Most you accept open for more than 60 days', 'money', 500),
    S('watch_job_type', 'Job type you watch (as written in your price book)', 'text', D.WATCH),
    S('watch_margin_target', 'Margin wanted on the watched job type', 'pct', D.WATCH_TARGET),
    S('tuneup_target', 'Planned tune-up visits done by their date, share wanted', 'pct', 0.90),
]

# ---------------- scorecard machinery: 12 measures, each read from the history table
HM = '{range:hist.month}'
CASHAFTER = '({range:hist.cash}-{range:hist.bill_7d})'
COVER = '({range:hist.cash}/({range:hist.fixed_cost}+({range:hist.fixed_cost}=0)))'
# key, history column, basis, scale, higher is better, setting, unit
MEAS = [('margin', 'flow', 100, 1, 'margin_target', 'points'), ('net_pct', 'flow', 100, 1, 'net_target', 'points'), ('utilisation', 'flow', 100, 1, 'util_target', 'points'),
        ('callbacks', 'flow', 100, 0, 'callback_target', 'points'), ('top_callback', 'point', 100, 0, 'callback_target', 'points'), ('close_rate', 'flow', 100, 1, 'close_target', 'points'),
        ('watch_margin', 'point', 100, 1, 'watch_margin_target', 'points'), ('ageing60', 'point', 1, 0, 'ageing_limit', 'amount'), ('renewals', 'point', 100, 1, 'renewal_target', 'points'),
        ('tuneups', 'point', 100, 1, 'tuneup_target', 'points'), ('cash_after', 'point', 1, 1, 'cash_floor', 'amount'), ('cash_cover', 'point', 1, 1, 'cover_months', 'months')]
def _col(c): return '{range:hist.%s}' % c
def _num(c): return CASHAFTER if c == 'cash_after' else COVER if c == 'cash_cover' else _col(c)
def _cur(c, b, s): return ('AVERAGEIFS(%s,%s,">="&%s,%s,"<"&%s)' % (_col(c), HM, EM(-3), HM, MS) if b == 'flow' else 'SUMIFS(%s,%s,%s)' % (_col(c), HM, MS)) + '*%d' % s
def _prev(c, b, s): return ('AVERAGEIFS(%s,%s,">="&%s,%s,"<"&%s)' % (_col(c), HM, EM(-6), HM, EM(-3)) if b == 'flow' else 'SUMIFS(%s,%s,%s)' % (_col(c), HM, EM(-1))) + '*%d' % s
def _ly(c, b, s): return ('AVERAGEIFS(%s,%s,">="&%s,%s,"<"&%s)' % (_col(c), HM, EM(-15), HM, EM(-12)) if b == 'flow' else 'SUMIFS(%s,%s,%s)' % (_col(c), HM, EM(-12))) + '*%d' % s
def _own(c, b, s): return 'AVERAGEIFS(%s,%s,">="&%s,%s,"<"&%s)*%d' % (_col(c), HM, EM(-12), HM, MS, s)
def _win(): return '(%s>=%s)*(%s<%s)' % (HM, EM(-12), HM, MS)
def _hi(c, b, s): return 'SUMPRODUCT(MAX(%s*%s))*%d' % (_win(), _num(c), s)
def _lo(c, b, s): return 'SUMPRODUCT(MIN(%s*%s+(1-%s)*1000000))*%d' % (_win(), _num(c), _win(), s)
def CH(fn, idx='{col:idx}'): return 'CHOOSE(%s,%s)' % (idx, ','.join('IFERROR(%s,0)' % fn(m[0], m[1], m[2]) for m in MEAS))
def TGT(): return 'CHOOSE({col:idx},%s)' % ','.join('{set:%s}*%d' % (m[4], m[2]) for m in MEAS)

LOWER = (4, 5, 8)   # measure numbers where lower is better

tables = []
# 1 lead sources
tables.append(T('sources', 'Lead Sources', 'Lead sources with monthly cost and kind', 'Where calls come from, what each source costs a month and whether it is paid, a reward or your own list. The marketing sheets read this list.',
  [LST('source', 'Source', 'source', 18, required=True), C('monthly_cost', 'Cost a month', 'money', 12), LST('kind', 'Kind', 'srckind', 10)], D.sources_d(), 12))
# 2 marketing spend
tables.append(T('marketing', 'Marketing Spend', 'Marketing spend, calls and jobs by source and month',
  'One row per source and month: spend, calls, booked and sold jobs and revenue from your own books; cost per lead, cost per booked job and revenue per spend fill in by themselves.', [
    C('row_id', 'Row', 'text', 9, required=True), C('month', 'Month', 'date', 10), LST('source', 'Source', 'source', 18), C('spend', 'Spend', 'money', 11), C('calls', 'Calls', 'int', 8), C('booked', 'Booked jobs', 'int', 9),
    C('sold', 'Sold jobs', 'int', 8), C('revenue', 'Revenue', 'money', 12),
    CA('cost_per_lead', 'Cost per lead', 'money', 'IFERROR({col:spend}/{col:calls},0)', 11), CA('cost_per_booked', 'Cost per booked job', 'money', 'IFERROR({col:spend}/{col:booked},0)', 12),
    CA('revenue_per_spend', 'Revenue per spend', 'num', 'IFERROR({col:revenue}/{col:spend},0)', 11), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.marketing_d(), 300, [A('cost_per_booked', '> {set:lead_cost_target}', 'warn')]))
# 3 source results
MKW = '{range:marketing.source},{col:source},{range:marketing.month},">="&{col:from_m},{range:marketing.month},"<="&{col:to_m}'
def MS_(c): return 'SUMIFS({range:marketing.%s},%s)' % (c, MKW)
JS = '{range:jobs.source},{col:source},{range:jobs.status},%s' % COMPLETED
tables.append(T('src_results', 'Source Results', 'Lead source results with a keep, renegotiate or drop verdict',
  'One row per source and period from Marketing Spend: spend, calls, jobs and revenue; cost per booked job, revenue per spend, the verdict and the job mix from Jobs fill in by themselves.', [
    C('row_id', 'Row', 'text', 8, required=True), LST('source', 'Source', 'source', 18), LST('period', 'Period', 'period', 18),
    CA('from_m', 'From month', 'date', 'IF({col:period}=%s,%s,IF({col:period}=%s,%s,%s))' % (P3, EM(-2), P12, EM(-11), EM(-23)), 11), CA('to_m', 'To month', 'date', 'IF({col:period}=%s,%s,%s)' % (PP12, EM(-12), MS), 11),
    CA('spend', 'Spend', 'money', MS_('spend'), 11), CA('calls', 'Calls', 'int', MS_('calls'), 8), CA('booked', 'Booked jobs', 'int', MS_('booked'), 9), CA('sold', 'Sold jobs', 'int', MS_('sold'), 8), CA('revenue', 'Revenue', 'money', MS_('revenue'), 12),
    CA('cost_per_lead', 'Cost per lead', 'money', 'IFERROR({col:spend}/{col:calls},0)', 11), CA('cost_per_booked', 'Cost per booked job', 'money', 'IFERROR({col:spend}/{col:booked},0)', 12),
    CA('revenue_per_spend', 'Revenue per spend', 'num', 'IFERROR({col:revenue}/{col:spend},0)', 11), CA('booking_rate', 'Booking rate', 'pct', 'IFERROR({col:booked}/{col:calls},0)', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:spend}<=0,%s,IF({col:revenue_per_spend}>={set:rps_keep},%s,IF({col:revenue_per_spend}>={set:rps_drop},%s,%s)))' % (ck('Free source'), ck('Keep'), ck('Renegotiate'), ck('Drop')), 13),
    CA('rank_key', 'Rank key, 12 months', 'num', 'IF(AND({col:period}=%s,{col:spend}>0),{col:revenue_per_spend}+VALUE(RIGHT({col:row_id},2))/1000000,"")' % P12, 11),
    CA('s_jobs', 'Completed jobs on the Jobs sheet', 'int', 'COUNTIFS(%s)' % JS, 11),
    CA('s_margin_job', 'Margin per job, Jobs sheet', 'money', 'IFERROR(SUMIFS({range:jobs.margin},%s)/COUNTIFS(%s),0)' % (JS, JS), 12),
    CA('s_repl_share', 'Share replacements and installs', 'pct', 'IFERROR((COUNTIFS(%s,{range:jobs.kind},%s)+COUNTIFS(%s,{range:jobs.kind},%s))/COUNTIFS(%s),0)' % (JS, tok('jobkind', 'Replacement'), JS, tok('jobkind', 'Install'), JS), 11),
    CA('mpj_key', 'Margin rank key', 'num', 'IF({col:period}=%s,{col:s_margin_job}+VALUE(RIGHT({col:row_id},2))/1000000,"")' % P12, 11),
    CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.src_results_d(), 40, [A('verdict', '= ' + ck('Drop'), 'bad'), A('verdict', '= ' + ck('Renegotiate'), 'warn'), A('verdict', '= ' + ck('Keep'), 'good')]))
# 4 calls
tables.append(T('calls', 'Calls', 'Recent calls with source, outcome and estimated value',
  'One row per incoming call of the last weeks: source, call type, outcome and the job value the call was worth; the booked flag fills in by itself.', [
    C('call_id', 'Call', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 10), LST('source', 'Source', 'source', 18), LST('call_type', 'Call type', 'calltype', 10), LST('outcome', 'Outcome', 'calloutcome', 15),
    C('est_value', 'Estimated value', 'money', 12), C('job_id', 'Job', 'text', 10),
    CA('booked', 'Booked (1 or 0)', 'int', 'IF(OR({col:outcome}=%s,{col:outcome}=%s),1,0)' % (tok('calloutcome', 'Booked'), tok('calloutcome', 'Estimate booked')), 9)],
  D.calls_d(), 700, [A('booked', '= 0', 'warn')]))
# 5 jobs
tables.append(T('jobs', 'Jobs', 'Recent jobs with source, price, margin and review request',
  'One row per job: source, job type, technician, price and margin, the customer site reference and phone, and whether a review was asked for and received; margin percent fills in by itself.', [
    C('job_id', 'Job', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('week', 'Week (Monday)', 'date', 12), C('month', 'Month', 'date', 10), LST('source', 'Source', 'source', 18), LST('job_type', 'Job type', 'jobtype', 26),
    LST('kind', 'Kind', 'jobkind', 12), LST('technician', 'Technician', 'tech', 16), LST('status', 'Status', 'jobstatus', 12), C('price', 'Price', 'money', 11), C('margin', 'Margin', 'money', 11),
    C('request_sent', 'Review asked', 'bool', 9), C('reviewed', 'Review received', 'bool', 9), C('site_ref', 'Site reference', 'text', 11), C('account', 'Account', 'text', 10), C('phone', 'Phone', 'text', 18), C('assistant', 'Assistant', 'text', 16),
    CA('margin_pct', 'Margin percent', 'pct', 'IFERROR({col:margin}/{col:price},0)', 9), TECHPH(),
    C('assistant_phone', 'Assistant phone', 'text', 18),
    CONST('parts_phone', 'Parts counter phone', D.PARTS_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.jobs_d(), 900, [A('request_sent', '= ' + NO, 'warn'), A('status', '= ' + tok('jobstatus', 'Cancelled'), 'bad')]))
# 6 source by month
SMW = '{range:marketing.source},{col:source},{range:marketing.month},{col:month}'
tables.append(T('src_month', 'Source by Month', 'Calls, booked jobs and revenue by source and month',
  'One row per source and month for 14 months, read from Marketing Spend: calls, booked jobs and revenue; booking rate and the share of the month calls fill in by themselves.', [
    C('row_id', 'Row', 'text', 8, required=True), C('month', 'Month', 'date', 10), LST('source', 'Source', 'source', 18),
    CA('calls', 'Calls', 'int', 'SUMIFS({range:marketing.calls},%s)' % SMW, 8), CA('booked', 'Booked jobs', 'int', 'SUMIFS({range:marketing.booked},%s)' % SMW, 9), CA('revenue', 'Revenue', 'money', 'SUMIFS({range:marketing.revenue},%s)' % SMW, 12),
    CA('booking_rate', 'Booking rate', 'pct', 'IFERROR({col:booked}/{col:calls},0)', 9), CA('call_share', 'Share of the month calls', 'pct', 'IFERROR({col:calls}/SUMIFS({range:marketing.calls},{range:marketing.month},{col:month}),0)', 10)],
  D.src_month_d(), 140))
# 7 reviews and referrals
tables.append(T('reviews', 'Reviews and Referrals', 'Review requests, reviews and referrals by technician',
  'One row per technician and month, counts only: jobs, requests sent, reviews received and referrals; request rate, conversion of jobs to reviews and the jobs with no request fill in by themselves.', [
    C('row_id', 'Row', 'text', 9, required=True), C('month', 'Month', 'date', 10), LST('technician', 'Technician', 'tech', 16), C('jobs', 'Jobs', 'int', 8), C('requests_sent', 'Requests sent', 'int', 9), C('reviews_received', 'Reviews received', 'int', 10),
    C('referrals', 'Referrals', 'int', 9), CA('request_rate', 'Request rate', 'pct', 'IFERROR({col:requests_sent}/{col:jobs},0)', 9), CA('conversion', 'Jobs to reviews', 'pct', 'IFERROR({col:reviews_received}/{col:jobs},0)', 9),
    CA('per_request', 'Reviews per request', 'pct', 'IFERROR({col:reviews_received}/{col:requests_sent},0)', 9), CA('not_requested', 'Jobs with no request', 'int', 'MAX(0,{col:jobs}-{col:requests_sent})', 10)],
  D.reviews_d(), 200, [A('conversion', '< {set:review_target}', 'warn'), A('conversion', '>= {set:review_target}', 'good')]))
# 8 review conversion by technician
RW = '{range:reviews.technician},{col:technician},{range:reviews.month},">="&{col:from_m},{range:reviews.month},"<="&{col:to_m}'
def RS(c): return 'SUMIFS({range:reviews.%s},%s)' % (c, RW)
tables.append(T('rev_tech', 'Review Conversion', 'Review conversion by technician and period',
  'One row per technician and period from Reviews and Referrals: jobs, requests, reviews, referrals, conversion of jobs to reviews and the gap to your review target fill in.', [
    C('row_id', 'Row', 'text', 8, required=True), LST('technician', 'Technician', 'tech', 16), LST('period', 'Period', 'period', 18),
    CA('from_m', 'From month', 'date', 'IF({col:period}=%s,%s,IF({col:period}=%s,%s,%s))' % (P3, EM(-2), P12, EM(-11), EM(-23)), 11), CA('to_m', 'To month', 'date', 'IF({col:period}=%s,%s,%s)' % (PP12, EM(-12), MS), 11),
    CA('jobs', 'Jobs', 'int', RS('jobs'), 8), CA('requests', 'Requests sent', 'int', RS('requests_sent'), 9), CA('reviews', 'Reviews received', 'int', RS('reviews_received'), 10), CA('referrals', 'Referrals', 'int', RS('referrals'), 9),
    CA('conversion', 'Jobs to reviews', 'pct', 'IFERROR({col:reviews}/{col:jobs},0)', 9), CA('request_rate', 'Request rate', 'pct', 'IFERROR({col:requests}/{col:jobs},0)', 9),
    CA('per_request', 'Reviews per request', 'pct', 'IFERROR({col:reviews}/{col:requests},0)', 9), CA('gap_to_target', 'Gap to the target', 'pct', '{col:conversion}-{set:review_target}', 9),
    CA('rank_key', 'Rank key, 12 months', 'num', 'IF({col:period}=%s,{col:conversion}+VALUE(RIGHT({col:row_id},2))/1000000,"")' % P12, 11), TECHPH(), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.rev_tech_d(), 30, [A('gap_to_target', '< 0', 'warn'), A('gap_to_target', '>= 0', 'good')]))
# 9 review requests by month
RMW = '{range:reviews.month},{col:month}'
def RM(c): return 'SUMIFS({range:reviews.%s},%s)' % (c, RMW)
tables.append(T('rev_month', 'Review Requests by Month', 'Jobs, review requests, reviews and referrals by month',
  'One row per month for 14 months from Reviews and Referrals: jobs, requests, reviews, referrals, conversion and jobs with no request fill in. The last month is month to date.', [
    C('month', 'Month', 'date', 10, required=True), CA('jobs', 'Jobs', 'int', RM('jobs'), 8), CA('requests', 'Requests sent', 'int', RM('requests_sent'), 9), CA('reviews', 'Reviews received', 'int', RM('reviews_received'), 10),
    CA('referrals', 'Referrals', 'int', RM('referrals'), 9), CA('conversion', 'Jobs to reviews', 'pct', 'IFERROR({col:reviews}/{col:jobs},0)', 9), CA('request_rate', 'Request rate', 'pct', 'IFERROR({col:requests}/{col:jobs},0)', 9),
    CA('not_sent', 'Jobs with no request', 'int', 'MAX(0,{col:jobs}-{col:requests})', 10), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.rev_month_d(), 20, [A('conversion', '< {set:review_target}', 'warn')]))
# 10 renewal dates
DAYS = 'IF({col:status}=%s,"",{col:due_date}-{today})' % RENEWED
tables.append(T('dates', 'Renewal Dates', 'Renewal dates: licence, insurance, registration, training',
  'One row per renewal: item, holder, due date, cost and status; days left, the band, who handles it and the next date fill in. Red and amber days are in Settings.', [
    C('licence_id', 'Renewal', 'text', 9, required=True), LST('item', 'Item', 'renewal', 20), C('holder', 'Holder', 'text', 18), C('due_date', 'Due date', 'date', 11), C('renewed_on', 'Renewed on', 'date', 11), C('cost', 'Cost', 'money', 11),
    LST('status', 'Status', 'rnstatus', 10),
    CA('days_left', 'Days left', 'int', DAYS, 8),
    CA('band', 'Band', 'text', 'IF({col:status}=%s,%s,IF({col:due_date}<{today},%s,IF({col:days_left}<={set:renewal_warn_days},%s,IF({col:days_left}<={set:renewal_amber_days},%s,%s))))' % (RENEWED, B_DONE, B_OVER, B_RED, B_AMB, B_GRN), 20),
    CA('on_time', 'Renewed on time (1 or 0)', 'int', 'IF({col:status}=%s,IF({col:renewed_on}<={col:due_date},1,0),"")' % RENEWED, 10),
    CA('handled_by', 'Handled by', 'text', 'IF(OR({col:item}=%s,{col:item}=%s),%s,IF(OR({col:item}=%s,{col:item}=%s),%s,%s))' % (tok('renewal', 'Business licence'), tok('renewal', 'Trade licence'), ck('Owner'),
        tok('renewal', 'Vehicle insurance'), tok('renewal', 'Liability insurance'), ck('Owner and insurance agent'), ck('Office manager')), 22),
    CA('act_key', 'Act-first key', 'num', 'IF({col:status}=%s,{col:days_left}+VALUE(RIGHT({col:licence_id},3))/10000,"")' % OPEN, 10),
    CA('next_due', 'Next due date after renewal', 'date', 'EDATE({col:due_date},12)', 12),
    CA('due_30', 'Open renewals due in 30 days', 'int', 'COUNTIFS({range:dates.status},%s,{range:dates.due_date},">="&{today},{range:dates.due_date},"<="&({today}+30))' % OPEN, 10),
    CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CONST('agent_phone', 'Insurance agent phone', D.AGENT_PHONE),
    CONST('elec_phone', 'Electrical sub phone', D.ELEC_PHONE), CONST('sheet_phone', 'Sheet-metal sub phone', D.SHEET_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.dates_d(), 100, [A('band', '= ' + B_OVER, 'bad'), A('band', '= ' + B_RED, 'bad'), A('band', '= ' + B_AMB, 'warn'), A('band', '= ' + B_DONE, 'good')]))
# 11 renewal budget
RBW = '{range:dates.due_date},">="&{col:month},{range:dates.due_date},"<"&EDATE({col:month},1)'
tables.append(T('ren_budget', 'Renewal Budget', 'Renewal cost by month for the next 12 months',
  'One row per coming month from Renewal Dates: renewals due and their cost; the running total, the year total and the share of the year fill in by themselves.', [
    C('month', 'Month', 'date', 10, required=True), CA('due', 'Renewals due', 'int', 'COUNTIFS(%s)' % RBW, 9), CA('cost', 'Cost', 'money', 'SUMIFS({range:dates.cost},%s)' % RBW, 11),
    CA('running', 'Running total', 'money', 'SUMIFS({range:ren_budget.cost},{range:ren_budget.month},"<="&{col:month})', 12), CA('year_cost', 'Cost of the 12 months', 'money', 'SUM({range:ren_budget.cost})', 12),
    CA('share', 'Share of the year', 'pct', 'IFERROR({col:cost}/{col:year_cost},0)', 9), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CONST('acct_phone', 'Accountant phone', D.ACCT_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.ren_budget_d(), 20, [A('share', '>= 0.15', 'warn')]))
# 12 renewal bands
tables.append(T('bands', 'Renewal Bands', 'Renewals by band: overdue, red, amber, green and renewed',
  'The five bands of the register with the number of renewals and their cost; the items and cost fill in by themselves from Renewal Dates.', [
    LST('band', 'Band', 'band', 22, required=True), CA('items', 'Items', 'int', 'COUNTIFS({range:dates.band},{col:band})', 8), CA('cost', 'Cost', 'money', 'SUMIFS({range:dates.cost},{range:dates.band},{col:band})', 12)],
  D.bands_d(), 10))
# 13 scorecard
IDX = 'MATCH({col:measure},{range:scorecard.measure},0)'
HB = '{col:higher_better}=%s' % YES
tables.append(T('scorecard', 'Scorecard', 'Owner scorecard: twelve measures against targets',
  'Twelve measures read from Scorecard History: value, target, your own 12 months, light, trend, gap, money behind it and a note. Targets come from Settings; do not reorder the rows.', [
    LST('measure', 'Measure', 'measure', 34, required=True), C('unit', 'Unit', 'text', 8), C('basis', 'Basis', 'text', 17), C('higher_better', 'Higher is better', 'bool', 9), C('money_per_point', 'Money a year per unit', 'money', 12),
    C('action', 'Action for the week', 'text', 44), LST('owner', 'Owner of the action', 'actowner', 16),
    CA('idx', 'Row number', 'int', IDX, 7),
    CA('value', 'Value', 'num', 'ROUND(%s,2)' % CH(_cur), 10), CA('target', 'Target', 'num', 'IFERROR(INDEX({range:targets.target},MATCH({col:measure},{range:targets.setting},0)),0)', 10),
    CA('own12', 'Own last 12 months', 'num', 'ROUND(%s,2)' % CH(_own), 10), CA('prev', 'Before this period', 'num', 'ROUND(%s,2)' % CH(_prev), 10), CA('ly', 'Same time last year', 'num', 'ROUND(%s,2)' % CH(_ly), 10),
    CA('gap_pct', 'Gap to target, % of target', 'num', 'IFERROR(ROUND(IF(%s,{col:target}-{col:value},{col:value}-{col:target})/{col:target}*100,1),0)' % HB, 11),
    CA('light', 'Light', 'text', 'IF({col:gap_pct}<=0,%s,IF({col:gap_pct}<=10,%s,%s))' % (G, AM, RD), 9),
    CA('trend', 'Against own 12 months', 'text', 'IF(ABS({col:value}-{col:own12})<=0.02*ABS({col:own12}),%s,IF(({col:value}>{col:own12})=(%s),%s,%s))' % (ck('Steady'), HB, ck('Improving'), ck('Slipping')), 11),
    CA('gap_units', 'Gap in units', 'num', 'MAX(0,IF(%s,{col:target}-{col:value},{col:value}-{col:target}))' % HB, 9),
    CA('money_at_stake', 'Money behind the gap', 'money', 'ROUND({col:gap_units}*{col:money_per_point},0)', 12),
    CA('note', 'Note', 'text', 'IF({col:gap_pct}<=0,%s,IF(%s,%s,%s)&" "&ROUND({col:gap_units},1)&" "&{col:unit}&", "&LOWER({col:trend}))' % (ck('On target or better'), HB, ck('Below the target by'), ck('Above the target by')), 40),
    CA('rank_key', 'Gap rank key', 'num', '{col:gap_pct}+{col:idx}/1000000', 10), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.scorecard_d(), 20, [A('light', '= ' + RD, 'bad'), A('light', '= ' + AM, 'warn'), A('light', '= ' + G, 'good')]))
# 14 scorecard history
tables.append(T('hist', 'Scorecard History', 'Scorecard history: 24 months of measures',
  'One row per month: the measures the scorecard reads. The current month is month to date or as of today; cash cover and measures at target fill in by themselves.', [
    C('month', 'Month', 'date', 10, required=True), C('margin', 'Job margin', 'pct', 9), C('net_pct', 'Net profit', 'pct', 9), C('utilisation', 'Utilisation', 'pct', 9), C('callbacks', 'Callback rate', 'pct', 9),
    C('top_callback', 'Highest technician callbacks', 'pct', 11), C('close_rate', 'Close rate', 'pct', 9), C('watch_margin', 'Watched job type margin', 'pct', 11), C('ageing60', 'Open over 60 days', 'money', 11),
    C('renewals', 'Renewals done', 'pct', 9), C('tuneups', 'Tune-ups done', 'pct', 9), C('cash', 'Cash at month end', 'money', 12), C('bill_7d', 'Largest bill due in 7 days', 'money', 12), C('fixed_cost', 'Fixed costs a month', 'money', 12),
    CA('cash_after', 'Cash after that bill', 'money', '{col:cash}-{col:bill_7d}', 12), CA('cash_cover', 'Cash cover, months', 'num', 'IFERROR({col:cash}/{col:fixed_cost},0)', 9),
    CA('greens', 'Measures at target', 'int', '({col:margin}>={set:margin_target})+({col:net_pct}>={set:net_target})+({col:utilisation}>={set:util_target})+({col:callbacks}<={set:callback_target})+({col:top_callback}<={set:callback_target})+({col:close_rate}>={set:close_target})+({col:watch_margin}>={set:watch_margin_target})+({col:ageing60}<={set:ageing_limit})+({col:renewals}>={set:renewal_target})+({col:tuneups}>={set:tuneup_target})+({col:cash_after}>={set:cash_floor})+({col:cash_cover}>={set:cover_months})', 9),
    CONST('acct_phone', 'Accountant phone', D.ACCT_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.sc_history_d(), 40, [A('greens', '<= 6', 'warn'), A('greens', '>= 9', 'good')]))
# 15 targets
TIDX = 'MATCH({col:setting},{range:targets.setting},0)'
LOWB = 'OR(%s)' % ','.join('{col:idx}=%d' % i for i in LOWER)
tables.append(T('targets', 'Targets', 'Targets with typical ranges and your own range',
  'The twelve scorecard targets with a typical range to check against your numbers; your own best and worst of 12 months fill in and a check flags a target outside them.', [
    LST('setting', 'Measure', 'measure', 34, required=True), C('typical_range', 'Typical range (check your own numbers)', 'text', 30),
    CA('idx', 'Row number', 'int', TIDX, 7), CA('target', 'Target', 'num', TGT(), 10),
    CA('own_high', 'Own highest, 12 months', 'num', 'ROUND(%s,2)' % CH(_hi), 11), CA('own_low', 'Own lowest, 12 months', 'num', 'ROUND(%s,2)' % CH(_lo), 11),
    CA('check', 'Target check', 'text', 'IF({col:target}>{col:own_high},IF(%s,%s,%s),IF({col:target}<{col:own_low},IF(%s,%s,%s),%s))' % (LOWB, ck('Easier than your best month'), ck('Harder than your best month'), LOWB, ck('Harder than your best month'), ck('Easier than your worst month'), ck('Inside your own range')), 26),
    CA('today_date', 'Today', 'date', '{today}', 11), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.targets_d(), 20, [A('check', '= ' + ck('Inside your own range'), 'good'), A('check', '= ' + ck('Harder than your best month'), 'warn')]))
# 16 technicians
tables.append(T('techs', 'Technicians', 'Technicians with trade and van', 'The six lead technicians, their trade and the van they drive; the review sheets read this list.',
  [C('technician', 'Technician', 'text', 24, required=True), C('trade', 'Trade', 'text', 11), C('van', 'Van', 'text', 9)], D.techs_d(), 12))
# 17 technician reviews by month
TMW = '{range:reviews.technician},{col:technician},{range:reviews.month},{col:month}'
def TMS(c): return 'SUMIFS({range:reviews.%s},%s)' % (c, TMW)
tables.append(T('tech_month', 'Technician Reviews by Month', 'Reviews and referrals by technician and month',
  'One row per technician and month for 12 months from Reviews and Referrals: jobs, requests, reviews, referrals and the difference from the own monthly average fill in.', [
    C('row_id', 'Row', 'text', 8, required=True), LST('technician', 'Technician', 'tech', 16), C('month', 'Month', 'date', 10),
    CA('jobs', 'Jobs', 'int', TMS('jobs'), 8), CA('requests', 'Requests sent', 'int', TMS('requests_sent'), 9), CA('reviews', 'Reviews received', 'int', TMS('reviews_received'), 10), CA('referrals', 'Referrals', 'int', TMS('referrals'), 9),
    CA('conversion', 'Jobs to reviews', 'pct', 'IFERROR({col:reviews}/{col:jobs},0)', 9),
    CA('vs_own', 'Reviews against own monthly average', 'num', 'ROUND({col:reviews}-IFERROR(SUMIFS({range:reviews.reviews_received},{range:reviews.technician},{col:technician},{range:reviews.month},">="&%s,{range:reviews.month},"<"&%s)/12,0),1)' % (EM(-12), MS), 12),
    TECHPH(), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.tech_month_d(), 90, [A('vs_own', '< 0', 'warn'), A('vs_own', '> 0', 'good')]))
# 18 monday actions
AIDX = 'MATCH(LARGE({range:scorecard.rank_key},{col:rank}),{range:scorecard.rank_key},0)'
def SCI(c): return 'INDEX({range:scorecard.%s},{col:pos})' % c
tables.append(T('actions', 'Monday Actions', 'Monday actions from the largest scorecard gaps',
  'One row per rank of the scorecard gap: the measure, its light, the action, who owns it, the due date and the money behind it fill in by themselves. Print the first five for the Monday meeting.', [
    C('rank', 'Rank', 'int', 6, required=True), CA('pos', 'Scorecard row', 'int', AIDX, 8), CA('measure', 'Measure', 'text', 'IFERROR(%s,"")' % SCI('measure'), 34), CA('gap_pct', 'Gap, % of target', 'num', 'IFERROR(%s,0)' % SCI('gap_pct'), 10),
    CA('light', 'Light', 'text', 'IFERROR(%s,"")' % SCI('light'), 9),
    CA('action', 'Action', 'text', 'IF({col:gap_pct}>0,IFERROR(%s,""),%s)' % (SCI('action'), ck('Hold: on target, no action this week')), 44), CA('owner', 'Owner', 'text', 'IF({col:gap_pct}>0,IFERROR(%s,""),"")' % SCI('owner'), 16),
    CA('due', 'Due', 'date', 'IF({col:gap_pct}>0,WORKDAY({today},CHOOSE(MIN({col:rank},5),1,2,3,4,5)),"")', 11),
    CA('money', 'Money at stake', 'money', 'IF({col:gap_pct}>0,IFERROR(%s,0),0)' % SCI('money_at_stake'), 12), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.actions_d(), 20, [A('light', '= ' + RD, 'bad'), A('light', '= ' + AM, 'warn'), A('light', '= ' + G, 'good')]))
# 19 cost per booked job by month
CMW = '{range:marketing.month},{col:month}'
def CM_(c): return 'SUMIFS({range:marketing.%s},%s)' % (c, CMW)
tables.append(T('cpb_month', 'Cost per Booked Job by Month', 'Marketing spend and cost per booked job by month',
  'One row per month for 14 months from Marketing Spend: spend, calls, booked jobs and revenue; cost per lead, cost per booked job, revenue per spend and the gap to your target fill in by themselves.', [
    C('month', 'Month', 'date', 10, required=True), CA('spend', 'Spend', 'money', CM_('spend'), 11), CA('calls', 'Calls', 'int', CM_('calls'), 8), CA('booked', 'Booked jobs', 'int', CM_('booked'), 9), CA('revenue', 'Revenue', 'money', CM_('revenue'), 12),
    CA('cost_per_lead', 'Cost per lead', 'money', 'IFERROR({col:spend}/{col:calls},0)', 11), CA('cost_per_booked', 'Cost per booked job', 'money', 'IFERROR({col:spend}/{col:booked},0)', 12),
    CA('revenue_per_spend', 'Revenue per spend', 'num', 'IFERROR({col:revenue}/{col:spend},0)', 11), CA('gap_to_target', 'Gap to the cost target', 'money', '{col:cost_per_booked}-{set:lead_cost_target}', 11),
    CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CONST('supplier_phone', 'Equipment supplier phone', D.SUP_PHONE), CA('company', 'Company', 'text', '{set:company}', 24)],
  D.cpb_month_d(), 20, [A('gap_to_target', '> 0', 'bad')]))
# 20 start here steps
tables.append(T('start_steps', 'Start Here Steps', 'The first-week steps with the tab each one uses', 'Ten steps for the first week: replace the demo data, set your targets, enter your spend and jobs and read the scorecard. The walk-through tool tracks which steps are done.',
  [C('step', 'Step', 'text', 34, required=True), C('what', 'What to do', 'text', 60), C('tab', 'Tab', 'text', 26)], D.start_steps_d(), 20))
