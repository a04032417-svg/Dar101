"""Part 3: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv3_lists import *
import hv3_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def PHONE(text): return CA('PH', 'Phone', 'text', '"%s"' % text, 18)
def ph(key_, label, text): return CA(key_, label, 'text', '"%s"' % text, 18)
def CO(): return CA('company', 'Company', 'text', '{set:company}', 24)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
Y12 = 'DATE(YEAR({today}),MONTH({today})-12,1)'
Y24 = 'DATE(YEAR({today}),MONTH({today})-24,1)'
WHT = tok('jobtype', WH) if False else None
WHT = LV('jobtype', key('jobtype', 'Water heater replacement'))
def TECHPH(my='technician'):
    return 'IFERROR(CHOOSE(MATCH({col:%s},{range:technicians.technician},0),%s),"")' % (my, ','.join('"%s"' % p for p in D.TECH_PHONES))
APPR = ['Amira Haddad', "Liam O'Connell"]
def ASSISTPH():
    f = '""'
    for n in reversed(APPR):
        f = 'IF({col:assistant}=%s,"%s",%s)' % (tok('assist', n), D.PH[n], f)
    return f

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('margin_target', 'Job margin target after all job costs, set your own', 'pct', 0.50),
    S('thin_margin', 'A job under this share of its price is flagged as thin', 'pct', 0.15), S('near_target', 'Points above target that still count as close', 'pct', 0.02),
    S('trend_pts', 'Change in margin points that counts as improving or slipping', 'pct', 0.01), S('callback_target', 'Callback rate target, set your own', 'pct', CALLBACK_TARGET),
    S('close_target', 'Close rate target, set your own', 'pct', CLOSE_TARGET), S('ticket_target', 'Average ticket target, the amount billed on one job', 'money', 350),
    S('warranty_reserve', 'Warranty reserve share of revenue, set your own', 'pct', 0.01), S('overhead_month', 'Overhead and unbilled technician time per month', 'money', D.OVERHEAD_MONTH),
    S('burden_pct', 'Employer extras on pay, confirm with your adviser', 'pct', BURDEN_PCT), S('vehicle_hour', 'Vehicle cost per hour on the road', 'money', VEHICLE_HOUR),
    S('replace_age', 'Equipment age that makes a replacement worth offering', 'int', 12),
]
assert 3 <= len(settings) <= 20

# ---- jobs
def LKJ(col, my='job_id', num=True):
    return 'IFERROR(INDEX({range:jobs.%s},MATCH({col:%s},{range:jobs.job_id},0)),%s)' % (col, my, '0' if num else '""')
PB = lambda col: 'IFERROR(INDEX({range:price_book.%s},MATCH({col:task_id},{range:price_book.pb_id},0)),0)' % col
CAUSE = ('IF({col:hours}=0,%s,IF({col:margin}>=0,IF(AND({col:price}>0,{col:margin_pct}<{set:thin_margin}),%s,%s),IF({col:is_callback}=%s,%s,'
         'IF(MAX({col:parts_over},0)>=MAX({col:hours_over}*IFERROR({col:labour_cost}/{col:hours},0),0),IF({col:parts_over}>0,%s,%s),IF({col:hours_over}>0,%s,%s)))))' %
         (c1('Costing incomplete'), c1('Thin margin'), c1('Won money'), YES, c1('Lost money: callback'), c1('Lost money: parts'), c1('Lost money: price'), c1('Lost money: hours'), c1('Lost money: price')))
ENTRY = ('IF({col:hours}=0,%s,IF(AND({col:parts_cost}=0,{col:is_callback}=%s,OR({col:kind}=%s,{col:kind}=%s,{col:kind}=%s)),%s,%s))' %
         (c4('Hours missing'), NO, tok('jobkind', 'Repair'), tok('jobkind', 'Replacement'), tok('jobkind', 'Install'), c4('Parts missing'), c4('Complete')))
W90 = '{col:date}>{today}-90'

JOB_COLS = [
    C('job_id', 'Job ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('site_ref', 'Site reference', 'text', 11), C('phone', 'Customer phone', 'text', 18),
    LST('site_type', 'Site type', 'sitetype', 10), LST('job_type', 'Job type', 'jobtype', 24), LST('technician', 'Technician', 'tech', 15), LST('assistant', 'Assistant', 'assist', 15), LST('van', 'Van', 'van', 8),
    C('hours', 'Hours on site', 'num', 8), C('assistant_hours', 'Assistant hours', 'num', 9), C('drive_hours', 'Drive hours', 'num', 9), C('price', 'Price', 'money', 11),
    C('parts_cost', 'Parts cost', 'money', 11), C('labour_cost', 'Labour cost', 'money', 11), C('permit_fee', 'Permit fee', 'num', 10), C('disposal', 'Disposal', 'num', 10), C('sub_cost', 'Subcontract cost', 'num', 12),
    C('vehicle_cost', 'Vehicle cost', 'money', 11), C('task_id', 'Task', 'text', 9), LST('tier', 'Option', 'tier', 9), C('is_callback', 'Callback', 'bool', 9), C('original_job', 'Original job', 'text', 11), C('warranty', 'Warranty', 'bool', 9),
    CA('total_cost', 'Total cost', 'money', '{col:parts_cost}+{col:labour_cost}+{col:permit_fee}+{col:disposal}+{col:sub_cost}+{col:vehicle_cost}', 12),
    CA('margin', 'Margin', 'money', '{col:price}-{col:total_cost}', 11), CA('margin_pct', 'Margin percent', 'pct', 'IF({col:price}>0,{col:margin}/{col:price},0)', 11),
    CA('kind', 'Job kind', 'text', LKT('job_types.kind', 'job_types.job_type', 'job_type'), 12),
    CA('book_hours', 'Price book hours', 'num', PB('labour_hours'), 11), CA('book_parts', 'Price book parts', 'money', PB('parts_cost'), 12),
    CA('hours_over', 'Hours over the book', 'num', 'IF({col:hours}>0,{col:hours}-{col:book_hours},0)', 11), CA('parts_over', 'Parts over the book', 'money', 'IF({col:hours}>0,{col:parts_cost}-{col:book_parts},0)', 12),
    CA('cause', 'Verdict', 'text', CAUSE, 22), CA('entry_flag', 'Entry check', 'text', ENTRY, 14),
    CA('lost', 'Money lost', 'money', 'IF(AND({col:hours}>0,{col:margin}<0),-{col:margin},0)', 11),
    CA('lostkey', 'Loss rank key', 'num', 'IF(AND({col:lost}>0,%s),{col:lost}+VALUE(RIGHT({col:job_id},5))/10000000,0)' % W90, 12),
    CA('overrun', 'Cost over the book', 'money', 'IF(AND({col:hours}>0,{col:is_callback}=%s,{col:task_id}<>"",%s),MAX(0,{col:total_cost}-%s),0)' % (NO, W90, PB('cost')), 12),
    CA('overkey', 'Overrun rank key', 'num', 'IF({col:overrun}>0,{col:overrun}+VALUE(RIGHT({col:job_id},5))/10000000,0)', 12),
    CA('tech_phone', 'Technician phone', 'text', TECHPH(), 18), CO(),
]
DP = lambda col: LKJ(col).replace('{col:job_id}', '{col:job_id}')
def LKC(col, num=True): return LKJ(col, num=num)

tables = [
    T('jobs', 'Jobs', 'Jobs with cost lines, margin and verdict',
      'One row per finished job: the price and every cost line (parts, labour, permit, disposal, subcontract, vehicle); total cost, margin, the price book gaps and a one-line verdict fill in by themselves.',
      JOB_COLS, D.jobs_d(), 1500, [A('margin', '< 0', 'bad'), A('cause', '= ' + c1('Thin margin'), 'warn'), A('cause', '= ' + c1('Won money'), 'good'), A('entry_flag', '= ' + c4('Hours missing'), 'bad'), A('entry_flag', '= ' + c4('Parts missing'), 'warn')]),
    T('costing', 'Job costing lines', 'Job costing lines with shares of the price',
      'Pick a job id on each row: price, every cost line, margin, the share of the price each big cost takes and the verdict fill in from the Jobs sheet.', [
        REF('job_id', 'Job ID', 'jobs.job_id', 10, required=True),
        CA('date', 'Date', 'date', LKJ('date'), 11), CA('job_type', 'Job type', 'text', LKJ('job_type', num=False), 24), CA('technician', 'Technician', 'text', LKJ('technician', num=False), 15),
        CA('price', 'Price', 'money', LKJ('price'), 11), CA('parts_cost', 'Parts cost', 'money', LKJ('parts_cost'), 11), CA('labour_cost', 'Labour cost', 'money', LKJ('labour_cost'), 11),
        CA('permit_fee', 'Permit and disposal', 'money', '%s+%s' % (LKJ('permit_fee'), LKJ('disposal')), 12), CA('sub_cost', 'Subcontract cost', 'money', LKJ('sub_cost'), 12),
        CA('vehicle_cost', 'Vehicle cost', 'money', LKJ('vehicle_cost'), 11), CA('total_cost', 'Total cost', 'money', LKJ('total_cost'), 12), CA('margin', 'Margin', 'money', LKJ('margin'), 11),
        CA('margin_pct', 'Margin percent', 'pct', 'IF({col:price}>0,{col:margin}/{col:price},0)', 11), CA('parts_share', 'Parts share of price', 'pct', 'IF({col:price}>0,{col:parts_cost}/{col:price},0)', 11),
        CA('labour_share', 'Labour share of price', 'pct', 'IF({col:price}>0,{col:labour_cost}/{col:price},0)', 11), CA('verdict', 'Verdict', 'text', LKJ('cause', num=False), 22),
        CA('site_ref', 'Site reference', 'text', LKJ('site_ref', num=False), 11), CA('assistant', 'Assistant', 'text', LKJ('assistant', num=False), 15), CA('assist_phone', 'Assistant phone', 'text', ASSISTPH(), 18),
        C('office_name', 'Office manager', 'text', 16), ph('office_phone', 'Office manager phone', D.OFFICE_PHONE), C('counter_name', 'Parts counter contact', 'text', 16), ph('counter_phone', 'Parts counter phone', D.COUNTER_PHONE),
        C('elec_name', 'Electrical subcontractor', 'text', 16), ph('elec_phone', 'Electrical subcontractor phone', D.ELEC_PHONE), C('sheet_name', 'Sheet-metal subcontractor', 'text', 16), ph('sheet_phone', 'Sheet-metal subcontractor phone', D.SHEET_PHONE), CO()],
      D.costing_d(), 400, [A('margin', '< 0', 'bad'), A('verdict', '= ' + c1('Won money'), 'good'), A('verdict', '= ' + c1('Thin margin'), 'warn')]),
    T('callbacks', 'Callbacks', 'Callbacks linked to the original job',
      'One row per return visit to fix the same job (a callback): hours, parts, travel and cost, linked to the original job; who paid and the share of the original price fill in.', [
        C('callback_id', 'Callback ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('original_job', 'Original job', 'text', 11), C('callback_job', 'Callback job', 'text', 11),
        LST('technician', 'Technician', 'tech', 15), LST('job_type', 'Job type', 'jobtype', 24), C('site_id', 'Site', 'text', 9), C('site_ref', 'Site reference', 'text', 11), C('phone', 'Customer phone', 'text', 18),
        LST('reason', 'Reason', 'cbreason', 20), C('hours', 'Hours', 'num', 8), C('drive_hours', 'Drive hours', 'num', 9), C('parts_cost', 'Parts cost', 'money', 11), C('cost', 'Cost', 'money', 11),
        C('warranty', 'Warranty', 'bool', 9), C('days_after', 'Days after', 'int', 9), LST('equip_type', 'Equipment type', 'eqtype', 18),
        CA('labour_travel', 'Labour and travel', 'money', '{col:cost}-{col:parts_cost}', 12),
        CA('paid_by', 'Who paid', 'text', 'IF({col:warranty}=%s,%s,%s)' % (YES, c5('Shop warranty'), c5('Shop goodwill')), 14),
        CA('orig_price', 'Original job price', 'money', 'IFERROR(INDEX({range:jobs.price},MATCH({col:original_job},{range:jobs.job_id},0)),0)', 12),
        CA('orig_tech', 'Original technician', 'text', 'IFERROR(INDEX({range:jobs.technician},MATCH({col:original_job},{range:jobs.job_id},0))&"","")', 15),
        CA('tech_phone', 'Technician phone', 'text', TECHPH(), 18), C('office_name', 'Office manager', 'text', 16), ph('office_phone', 'Office manager phone', D.OFFICE_PHONE), CO()],
      D.callbacks_d(), 700, [A('warranty', '= ' + YES, 'warn'), A('cost', '> 300', 'bad')]),
    T('margin_jt', 'Margin by job type', 'Margin by job type against its target',
      'Type totals of the last 120 days, the 12 months before and the same days last year per job type; margin, gap, trend, price rise needed and margin per hour fill in.', [
        LST('job_type', 'Job type', 'jobtype', 24, required=True), C('jobs_120', 'Jobs, last 120 days', 'int', 11), C('revenue_120', 'Revenue, last 120 days', 'money', 13), C('cost_120', 'Cost, last 120 days', 'money', 13),
        C('hours_120', 'Hours on site, last 120 days', 'num', 12), C('drive_120', 'Drive hours, last 120 days', 'num', 12), C('revenue_p12', 'Revenue, 12 months before', 'money', 13), C('cost_p12', 'Cost, 12 months before', 'money', 13),
        C('jobs_ly', 'Jobs, same days last year', 'int', 11), C('revenue_ly', 'Revenue, same days last year', 'money', 13), C('cost_ly', 'Cost, same days last year', 'money', 13),
        CA('kind', 'Job kind', 'text', LKT('job_types.kind', 'job_types.job_type', 'job_type'), 12), CA('target', 'Target margin', 'pct', LKN('job_types.target_margin', 'job_types.job_type', 'job_type'), 10),
        CA('margin_120', 'Margin, last 120 days', 'money', '{col:revenue_120}-{col:cost_120}', 13), CA('margin_pct_120', 'Margin percent, last 120 days', 'pct', 'IF({col:revenue_120}>0,{col:margin_120}/{col:revenue_120},0)', 12),
        CA('margin_pct_p12', 'Margin percent, 12 months before', 'pct', 'IF({col:revenue_p12}>0,({col:revenue_p12}-{col:cost_p12})/{col:revenue_p12},0)', 12),
        CA('change_pts', 'Change against the 12 months before', 'pct', '{col:margin_pct_120}-{col:margin_pct_p12}', 12), CA('gap', 'Gap to target', 'pct', '{col:margin_pct_120}-{col:target}', 10),
        CA('status', 'Target check', 'text', 'IF({col:gap}<0,%s,IF({col:gap}<{set:near_target},%s,%s))' % (c2('Under target'), c2('Close to target'), c2('On target')), 14),
        CA('margin_pct_ly', 'Margin percent, same days last year', 'pct', 'IF({col:revenue_ly}>0,({col:revenue_ly}-{col:cost_ly})/{col:revenue_ly},0)', 12),
        CA('trend', 'Trend against last year', 'text', 'IF({col:margin_pct_120}-{col:margin_pct_ly}>{set:trend_pts},%s,IF({col:margin_pct_120}-{col:margin_pct_ly}<-{set:trend_pts},%s,%s))' % (c3('Improving'), c3('Slipping'), c3('Steady')), 12),
        CA('price_job', 'Price per job, last 120 days', 'money', 'IF({col:jobs_120}>0,{col:revenue_120}/{col:jobs_120},0)', 12), CA('cost_job', 'Cost per job, last 120 days', 'money', 'IF({col:jobs_120}>0,{col:cost_120}/{col:jobs_120},0)', 12),
        CA('price_target', 'Price per job for the target', 'money', 'IF({col:target}<1,{col:cost_job}/(1-{col:target}),0)', 12),
        CA('rise_target', 'Price rise to reach the target', 'pct', 'IF(AND({col:revenue_120}>0,{col:margin_pct_120}<{col:target}),(1-{col:margin_pct_120})/(1-{col:target})-1,0)', 12),
        CA('rise_buffer', 'Price rise to reach target plus buffer', 'pct', 'IF({col:revenue_120}>0,MAX(0,(1-{col:margin_pct_120})/(1-{col:target}-{set:near_target})-1),0)', 12),
        CA('jobs_year', 'Jobs a year at this pace', 'int', '{col:jobs_120}*365/120', 10), CA('recover_year', 'Money recovered a year if re-priced', 'money', '{col:revenue_120}*{col:rise_buffer}*365/120', 13),
        CA('mph', 'Margin per hour on site and on the road', 'money', 'IF({col:hours_120}+{col:drive_120}>0,{col:margin_120}/({col:hours_120}+{col:drive_120}),0)', 12),
        CA('kind_mph', 'Margin per hour of the job kind', 'money', 'IFERROR(SUMIFS({range:margin_jt.margin_120},{range:margin_jt.kind},{col:kind})/(SUMIFS({range:margin_jt.hours_120},{range:margin_jt.kind},{col:kind})+SUMIFS({range:margin_jt.drive_120},{range:margin_jt.kind},{col:kind})),0)', 12),
        CA('kind_rev_share', 'Revenue share of the job kind', 'pct', 'IFERROR(SUMIFS({range:margin_jt.revenue_120},{range:margin_jt.kind},{col:kind})/SUM({range:margin_jt.revenue_120}),0)', 12),
        CA('kind_margin_share', 'Margin share of the job kind', 'pct', 'IFERROR(SUMIFS({range:margin_jt.margin_120},{range:margin_jt.kind},{col:kind})/SUM({range:margin_jt.margin_120}),0)', 12),
        CA('action', 'Hours decision', 'text', 'IF({col:mph}>=1.2*SUM({range:margin_jt.margin_120})/(SUM({range:margin_jt.hours_120})+SUM({range:margin_jt.drive_120})),%s,IF({col:mph}<0.8*SUM({range:margin_jt.margin_120})/(SUM({range:margin_jt.hours_120})+SUM({range:margin_jt.drive_120})),%s,%s))' % (c6('Book more'), c6('Re-price or book less'), c6('Margin looks fine')), 20),
        C('owner_name', 'Owner name', 'text', 16), ph('owner_phone', 'Owner phone', D.OWNER_PHONE), CO()],
      D.margin_jt_d(), 50, [A('status', '= ' + c2('Under target'), 'bad'), A('status', '= ' + c2('Close to target'), 'warn'), A('status', '= ' + c2('On target'), 'good'), A('trend', '= ' + c3('Slipping'), 'warn')]),
    T('margin_month', 'Margin by month and type', 'Margin by month for the six main job types',
      'Type each month for the six main job types: jobs, revenue and cost; margin and margin percent fill in by themselves, so a type that slips shows month by month.', [
        C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('job_type', 'Job type', 'jobtype', 24), C('jobs', 'Jobs', 'int', 8), C('revenue', 'Revenue', 'money', 12), C('cost', 'Cost', 'money', 12),
        CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 12), CA('margin_pct', 'Margin percent', 'pct', 'IF({col:revenue}>0,{col:margin}/{col:revenue},0)', 11),
        CA('ticket', 'Average ticket', 'money', 'IF({col:jobs}>0,{col:revenue}/{col:jobs},0)', 11)], D.margin_month_d(), 150, [A('margin_pct', '< 0.4', 'warn')]),
    T('tick_tech', 'Ticket by technician', 'Average ticket and margin by technician',
      'Type jobs, revenue and cost for each technician and period (last 90 days, last 12 months, the 12 months before); average ticket, margin percent and the gap to the shop average fill in by themselves.', [
        C('row_id', 'Row ID', 'text', 9, required=True), LST('technician', 'Technician', 'tech', 15), LST('period', 'Period', 'period', 18), C('jobs', 'Jobs', 'int', 8), C('revenue', 'Revenue', 'money', 12), C('cost', 'Cost', 'money', 12),
        CA('avg_ticket', 'Average ticket', 'money', 'IF({col:jobs}>0,{col:revenue}/{col:jobs},0)', 11), CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 12),
        CA('margin_pct', 'Margin percent', 'pct', 'IF({col:revenue}>0,{col:margin}/{col:revenue},0)', 11), CA('margin_job', 'Margin per job', 'money', 'IF({col:jobs}>0,{col:margin}/{col:jobs},0)', 11),
        CA('shop_ticket', 'Shop average ticket', 'money', 'IFERROR(SUMIFS({range:tick_tech.revenue},{range:tick_tech.period},{col:period})/SUMIFS({range:tick_tech.jobs},{range:tick_tech.period},{col:period}),0)', 12),
        CA('ticket_gap', 'Gap to shop average', 'money', '{col:avg_ticket}-{col:shop_ticket}', 11),
        CA('t12', 'Ticket, 12 months', 'money', 'IF({col:period}=%s,{col:avg_ticket},0)' % tok('period', 'Last 12 months'), 11), CA('t12lo', 'Ticket, 12 months for ranking', 'money', 'IF({col:period}=%s,{col:avg_ticket},999999)' % tok('period', 'Last 12 months'), 11),
        CA('cb_drop', 'Margin points lost to callbacks', 'pct', 'IF({col:revenue}>0,SUMIFS({range:cb_tech.cost},{range:cb_tech.technician},{col:technician},{range:cb_tech.period},{col:period})/{col:revenue},0)', 12),
        CA('after_pct', 'Margin percent after callbacks', 'pct', '{col:margin_pct}-{col:cb_drop}', 12), CA('drop12', 'Points lost, 12 months', 'pct', 'IF({col:period}=%s,{col:cb_drop},0)' % tok('period', 'Last 12 months'), 11),
        CA('tech_phone', 'Technician phone', 'text', TECHPH(), 18), CO()], D.tick_tech_d(), 60, [A('ticket_gap', '< -40', 'warn'), A('ticket_gap', '> 40', 'good')]),
    T('tick_van', 'Ticket by van', 'Average ticket and margin by van',
      'Type jobs, revenue and cost for each van and period; average ticket, margin percent and the gap to the shop average fill in by themselves.', [
        C('row_id', 'Row ID', 'text', 9, required=True), LST('van', 'Van', 'van', 8), LST('period', 'Period', 'period', 18), C('jobs', 'Jobs', 'int', 8), C('revenue', 'Revenue', 'money', 12), C('cost', 'Cost', 'money', 12),
        CA('avg_ticket', 'Average ticket', 'money', 'IF({col:jobs}>0,{col:revenue}/{col:jobs},0)', 11), CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 12),
        CA('margin_pct', 'Margin percent', 'pct', 'IF({col:revenue}>0,{col:margin}/{col:revenue},0)', 11),
        CA('shop_ticket', 'Shop average ticket', 'money', 'IFERROR(SUMIFS({range:tick_van.revenue},{range:tick_van.period},{col:period})/SUMIFS({range:tick_van.jobs},{range:tick_van.period},{col:period}),0)', 12),
        CA('ticket_gap', 'Gap to shop average', 'money', '{col:avg_ticket}-{col:shop_ticket}', 11),
        CA('t12', 'Ticket, 12 months', 'money', 'IF({col:period}=%s,{col:avg_ticket},0)' % tok('period', 'Last 12 months'), 11), CA('t12lo', 'Ticket, 12 months for ranking', 'money', 'IF({col:period}=%s,{col:avg_ticket},999999)' % tok('period', 'Last 12 months'), 11)],
      D.tick_van_d(), 60, [A('ticket_gap', '< -40', 'warn'), A('ticket_gap', '> 40', 'good')]),
    T('tick_site', 'Ticket by site type', 'Average ticket and margin by site type',
      'Type jobs, revenue and cost for homes, rentals, shops and offices by period; average ticket, margin percent and the gap to the shop average fill in by themselves.', [
        C('row_id', 'Row ID', 'text', 9, required=True), LST('site_type', 'Site type', 'sitetype', 10), LST('period', 'Period', 'period', 18), C('jobs', 'Jobs', 'int', 8), C('revenue', 'Revenue', 'money', 12), C('cost', 'Cost', 'money', 12),
        CA('avg_ticket', 'Average ticket', 'money', 'IF({col:jobs}>0,{col:revenue}/{col:jobs},0)', 11), CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 12),
        CA('margin_pct', 'Margin percent', 'pct', 'IF({col:revenue}>0,{col:margin}/{col:revenue},0)', 11),
        CA('shop_ticket', 'Shop average ticket', 'money', 'IFERROR(SUMIFS({range:tick_site.revenue},{range:tick_site.period},{col:period})/SUMIFS({range:tick_site.jobs},{range:tick_site.period},{col:period}),0)', 12),
        CA('ticket_gap', 'Gap to shop average', 'money', '{col:avg_ticket}-{col:shop_ticket}', 11),
        CA('t12', 'Ticket, 12 months', 'money', 'IF({col:period}=%s,{col:avg_ticket},0)' % tok('period', 'Last 12 months'), 11), CA('t12lo', 'Ticket, 12 months for ranking', 'money', 'IF({col:period}=%s,{col:avg_ticket},999999)' % tok('period', 'Last 12 months'), 11)],
      D.tick_site_d(), 60, [A('ticket_gap', '< -40', 'warn'), A('ticket_gap', '> 40', 'good')]),
    T('tick_month', 'Ticket by month', 'Revenue, cost, ticket and callbacks by month',
      'Type each month: jobs, revenue and four cost groups; margin, callback cost, gross profit, ticket, same month last year and the warranty reserve check fill in.', [
        C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('jobs', 'Jobs', 'int', 8), C('revenue', 'Revenue', 'money', 12), C('parts_cost', 'Parts cost', 'money', 12), C('labour_cost', 'Labour cost', 'money', 12),
        C('sub_cost', 'Subcontract cost', 'money', 12), C('other_cost', 'Permit, disposal and vehicle', 'money', 13), C('losing_jobs', 'Jobs that lost money', 'int', 10), C('base_jobs', 'Jobs that can have a callback', 'int', 11),
        CA('cost', 'Cost before callbacks', 'money', '{col:parts_cost}+{col:labour_cost}+{col:sub_cost}+{col:other_cost}', 12), CA('margin', 'Margin before callbacks', 'money', '{col:revenue}-{col:cost}', 12),
        CA('cb_count', 'Callbacks', 'int', 'COUNTIFS({range:callbacks.date},">="&{col:month},{range:callbacks.date},"<"&EDATE({col:month},1))', 9),
        CA('cb_cost', 'Callback cost', 'money', 'SUMIFS({range:callbacks.cost},{range:callbacks.date},">="&{col:month},{range:callbacks.date},"<"&EDATE({col:month},1))', 11),
        CA('gross_profit', 'Gross profit after callbacks', 'money', '{col:margin}-{col:cb_cost}', 13), CA('margin_pct', 'Margin percent after callbacks', 'pct', 'IF({col:revenue}>0,{col:gross_profit}/{col:revenue},0)', 12),
        CA('avg_ticket', 'Average ticket', 'money', 'IF({col:jobs}>0,{col:revenue}/{col:jobs},0)', 11),
        CA('ly_ticket', 'Same month last year', 'money', 'IFERROR(INDEX({range:tick_month.avg_ticket},MATCH(EDATE({col:month},-12),{range:tick_month.month},0)),"")', 12),
        CA('cb_rate', 'Callback rate', 'pct', 'IF({col:base_jobs}>0,{col:cb_count}/{col:base_jobs},0)', 10), CA('cb_share', 'Callback cost share of revenue', 'pct', 'IF({col:revenue}>0,{col:cb_cost}/{col:revenue},0)', 11),
        CA('warranty_cost', 'Warranty cost', 'money', 'SUMIFS({range:callbacks.cost},{range:callbacks.warranty},%s,{range:callbacks.date},">="&{col:month},{range:callbacks.date},"<"&EDATE({col:month},1))' % YES, 12),
        CA('reserve', 'Warranty reserve', 'money', '{col:revenue}*{set:warranty_reserve}', 12),
        CA('reserve_flag', 'Reserve check', 'text', 'IF({col:warranty_cost}<={col:reserve},%s,%s)' % (c5('Within reserve'), c5('Over reserve')), 13),
        CA('t12', 'Ticket, 12 months', 'money', 'IF(AND({col:month}>=%s,{col:month}<%s),{col:avg_ticket},0)' % (Y12, MS), 11),
        CA('t12lo', 'Ticket, 12 months for ranking', 'money', 'IF(AND({col:month}>=%s,{col:month}<%s),{col:avg_ticket},999999)' % (Y12, MS), 11),
        CA('profit_week', 'Gross profit per week', 'money', '{col:gross_profit}/(DAY(EOMONTH({col:month},0))/7)', 12),
        C('owner_name', 'Owner name', 'text', 16), ph('owner_phone', 'Owner phone', D.OWNER_PHONE), C('acct_name', 'Accountant', 'text', 16), ph('acct_phone', 'Accountant phone', D.ACCT_PHONE), C('ins_name', 'Insurance agent', 'text', 16), ph('ins_phone', 'Insurance agent phone', D.INS_PHONE), CO()],
      D.tick_month_d(), 60, [A('margin_pct', '< {set:margin_target}', 'warn'), A('reserve_flag', '= ' + c5('Over reserve'), 'bad')]),
    T('cb_tech', 'Callback rate by technician', 'Callback rate by technician and period',
      'Type the jobs that can have a callback per technician and period; callbacks and cost come from the Callbacks sheet, then rate, ratio and a verdict fill in.', [
        C('row_id', 'Row ID', 'text', 9, required=True), LST('technician', 'Technician', 'tech', 15), LST('period', 'Period', 'period', 18), C('jobs', 'Jobs that can have a callback', 'int', 12),
        CA('from_date', 'From', 'date', 'IF({col:period}=%s,{today}-89,IF({col:period}=%s,%s,%s))' % (tok('period', 'Last 90 days'), tok('period', 'Last 12 months'), Y12, Y24), 11),
        CA('to_date', 'To', 'date', 'IF({col:period}=%s,{today},IF({col:period}=%s,{today},%s-1))' % (tok('period', 'Last 90 days'), tok('period', 'Last 12 months'), Y12), 11),
        CA('callbacks', 'Callbacks', 'int', 'COUNTIFS({range:callbacks.technician},{col:technician},{range:callbacks.date},">="&{col:from_date},{range:callbacks.date},"<="&{col:to_date})', 10),
        CA('rate', 'Callback rate', 'pct', 'IF({col:jobs}>0,{col:callbacks}/{col:jobs},0)', 10),
        CA('cost', 'Callback cost', 'money', 'SUMIFS({range:callbacks.cost},{range:callbacks.technician},{col:technician},{range:callbacks.date},">="&{col:from_date},{range:callbacks.date},"<="&{col:to_date})', 12),
        CA('shop_rate', 'Shop callback rate', 'pct', 'IFERROR(SUMIFS({range:cb_tech.callbacks},{range:cb_tech.period},{col:period})/SUMIFS({range:cb_tech.jobs},{range:cb_tech.period},{col:period}),0)', 11),
        CA('ratio', 'Times the shop rate', 'num', 'IF({col:shop_rate}>0,{col:rate}/{col:shop_rate},0)', 10),
        CA('status', 'Verdict', 'text', 'IF(AND({col:rate}>{set:callback_target},{col:ratio}>=1.5),%s,IF({col:rate}>{set:callback_target},%s,%s))' % (c5('Talk this week'), c5('Watch'), c5('Fine')), 15),
        CA('rate12', 'Rate, 12 months', 'pct', 'IF({col:period}=%s,{col:rate},0)' % tok('period', 'Last 12 months'), 10),
        CA('tech_phone', 'Technician phone', 'text', TECHPH(), 18), C('owner_name', 'Owner name', 'text', 16), ph('owner_phone', 'Owner phone', D.OWNER_PHONE), CO()],
      D.cb_tech_d(), 60, [A('status', '= ' + c5('Talk this week'), 'bad'), A('status', '= ' + c5('Watch'), 'warn'), A('status', '= ' + c5('Fine'), 'good')]),
    T('cb_type', 'Callback rate by job type', 'Callback rate and margin after callbacks by job type',
      'Type 12 months of jobs, revenue and cost per job type; callbacks and cost come from the Callbacks sheet, then the rate and margin after callbacks fill in.', [
        LST('job_type', 'Job type', 'jobtype', 24, required=True), C('jobs', 'Jobs that can have a callback', 'int', 12), C('revenue', 'Revenue, 12 months', 'money', 13), C('cost', 'Cost before callbacks', 'money', 13),
        CA('callbacks', 'Callbacks', 'int', 'COUNTIFS({range:callbacks.job_type},{col:job_type},{range:callbacks.date},">="&%s,{range:callbacks.date},"<="&{today})' % Y12, 10),
        CA('rate', 'Callback rate', 'pct', 'IF({col:jobs}>0,{col:callbacks}/{col:jobs},0)', 10),
        CA('cb_cost', 'Callback cost', 'money', 'SUMIFS({range:callbacks.cost},{range:callbacks.job_type},{col:job_type},{range:callbacks.date},">="&%s,{range:callbacks.date},"<="&{today})' % Y12, 12),
        CA('shop_rate', 'Shop callback rate', 'pct', 'IFERROR(SUM({range:cb_type.callbacks})/SUM({range:cb_type.jobs}),0)', 11), CA('ratio', 'Times the shop rate', 'num', 'IF({col:shop_rate}>0,{col:rate}/{col:shop_rate},0)', 10),
        CA('margin_before', 'Margin percent before callbacks', 'pct', 'IF({col:revenue}>0,({col:revenue}-{col:cost})/{col:revenue},0)', 12),
        CA('margin_after', 'Margin percent after callbacks', 'pct', 'IF({col:revenue}>0,({col:revenue}-{col:cost}-{col:cb_cost})/{col:revenue},0)', 12),
        CA('drop', 'Points lost to callbacks', 'pct', '{col:margin_before}-{col:margin_after}', 11)],
      D.cb_type_d(), 50, [A('ratio', '>= 1.5', 'bad')]),
    T('cb_reason', 'Callback reasons', 'Callback reasons with count and cost',
      'One row per reason: callbacks and cost of the last 12 months come from the Callbacks sheet.', [
        LST('reason', 'Reason', 'cbreason', 24, required=True),
        CA('callbacks', 'Callbacks, 12 months', 'int', 'COUNTIFS({range:callbacks.reason},{col:reason},{range:callbacks.date},">="&%s,{range:callbacks.date},"<="&{today})' % Y12, 12),
        CA('cost', 'Cost, 12 months', 'money', 'SUMIFS({range:callbacks.cost},{range:callbacks.reason},{col:reason},{range:callbacks.date},">="&%s,{range:callbacks.date},"<="&{today})' % Y12, 13)],
      D.cb_reason_d(), 50),
    T('price_book', 'Price book', 'Flat-rate price book with margin against target',
      'The fixed price per task, built from cost: hours, parts, flat price and all-in cost; margin, gap to target and the price needed for the target fill in.', [
        C('pb_id', 'Task ID', 'text', 9, required=True), C('task', 'Task', 'text', 30), LST('job_type', 'Job type', 'jobtype', 24), LST('tier', 'Option', 'tier', 9), C('labour_hours', 'Labour hours', 'num', 9), C('parts_cost', 'Parts cost', 'money', 11),
        C('permit_fee', 'Permit fee', 'num', 10), C('disposal', 'Disposal', 'num', 10), C('sub_cost', 'Subcontract cost', 'num', 12), C('flat_price', 'Flat price', 'money', 11), C('previous_price', 'Price last year', 'money', 11), C('cost', 'All-in cost', 'money', 11),
        CA('target', 'Target margin', 'pct', LKN('job_types.target_margin', 'job_types.job_type', 'job_type'), 10), CA('margin_pct', 'Margin percent', 'pct', 'IF({col:flat_price}>0,({col:flat_price}-{col:cost})/{col:flat_price},0)', 10),
        CA('gap', 'Gap to target', 'pct', '{col:margin_pct}-{col:target}', 10), CA('status', 'Target check', 'text', 'IF({col:gap}<0,%s,IF({col:gap}<{set:near_target},%s,%s))' % (c2('Under target'), c2('Close to target'), c2('On target')), 14),
        CA('price_needed', 'Price for the target', 'money', 'IF({col:target}<1,{col:cost}/(1-{col:target}),0)', 11), CA('change_pct', 'Rise since last year', 'pct', 'IF({col:previous_price}>0,{col:flat_price}/{col:previous_price}-1,0)', 10)],
      D.price_book_d(), 100, [A('status', '= ' + c2('Under target'), 'bad'), A('status', '= ' + c2('Close to target'), 'warn')]),
    T('price_changes', 'Parts price changes', 'Supplier price changes of parts',
      'One row per supplier price change of a part: old and new cost; the rise and the supplier phone fill in by themselves.', [
        C('change_id', 'Change ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('part_id', 'Part', 'text', 9), C('part', 'Part name', 'text', 28), LST('supplier', 'Supplier', 'supplier', 22), C('old_cost', 'Old cost', 'money', 11), C('new_cost', 'New cost', 'money', 11),
        CA('rise', 'Rise', 'pct', 'IF({col:old_cost}>0,{col:new_cost}/{col:old_cost}-1,0)', 9),
        C('supplier_contact', 'Supplier contact', 'text', 16),
        CA('supplier_phone', 'Supplier phone', 'text', 'IF({col:supplier}=%s,"%s","%s")' % (tok('supplier', 'Your equipment supplier'), D.EQUIP_PHONE, D.COUNTER_PHONE), 18), CO()],
      D.price_changes_d(), 100, [A('rise', '>= 0.15', 'bad'), A('rise', '>= 0.08', 'warn')]),
    T('wh_month', 'Water heater margin', 'Water heater replacement margin by month against its target',
      'Type each month of water heater jobs: revenue, cost and unit cost; margin percent, gap to target, unit cost rise and the price needed fill in.', [
        C('month', 'Month', 'date', 11, required=True), C('jobs', 'Jobs', 'int', 8), C('revenue', 'Revenue', 'money', 12), C('cost', 'Cost', 'money', 12), C('unit_cost', 'Average unit cost', 'num', 12),
        CA('margin', 'Margin', 'money', '{col:revenue}-{col:cost}', 12), CA('margin_pct', 'Margin percent', 'pct', 'IF({col:revenue}>0,{col:margin}/{col:revenue},0)', 11),
        CA('target', 'Target margin', 'pct', 'IFERROR(INDEX({range:job_types.target_margin},MATCH(%s,{range:job_types.job_type},0)),0)' % WHT, 10), CA('gap', 'Gap to target', 'pct', '{col:margin_pct}-{col:target}', 10),
        CA('status', 'Target check', 'text', 'IF({col:gap}<0,%s,IF({col:gap}<{set:near_target},%s,%s))' % (c2('Under target'), c2('Close to target'), c2('On target')), 14),
        CA('unit_rise', 'Unit cost rise since the first month', 'pct', 'IF(INDEX({range:wh_month.unit_cost},1)>0,{col:unit_cost}/INDEX({range:wh_month.unit_cost},1)-1,0)', 12),
        CA('price_job', 'Price per job', 'money', 'IF({col:jobs}>0,{col:revenue}/{col:jobs},0)', 11), CA('cost_job', 'Cost per job', 'money', 'IF({col:jobs}>0,{col:cost}/{col:jobs},0)', 11),
        CA('price_needed', 'Price per job for the target', 'money', 'IF({col:target}<1,{col:cost_job}/(1-{col:target}),0)', 12), C('owner_name', 'Owner name', 'text', 16), ph('owner_phone', 'Owner phone', D.OWNER_PHONE), CO()],
      D.wh_month_d(), 50, [A('status', '= ' + c2('Under target'), 'bad'), A('status', '= ' + c2('Close to target'), 'warn')]),
    T('replace_inputs', 'Repair or replace', 'Repair or replace numbers entered by the owner',
      'One row per quote: age, repair quote, replacement price and expected life you enter; cost per year of each choice and a plain sentence fill in.', [
        C('site_ref', 'Site reference', 'text', 11, required=True), C('phone', 'Customer phone', 'text', 18), C('quote_date', 'Quote date', 'date', 11), LST('equip_type', 'Equipment type', 'eqtype', 18), C('age_years', 'Age in years', 'int', 9),
        C('repair_quote', 'Repair quote', 'money', 11), C('replace_price', 'Replacement price', 'money', 12), C('life_years', 'Expected life in years', 'int', 11),
        CA('remaining', 'Remaining years', 'int', 'MAX(0,{col:life_years}-{col:age_years})', 10), CA('repair_year', 'Repair cost per remaining year', 'money', 'IF({col:repair_quote}>0,{col:repair_quote}/MAX({col:remaining},1),0)', 12),
        CA('replace_year', 'Replacement cost per year', 'money', 'IF({col:life_years}>0,{col:replace_price}/{col:life_years},0)', 12), CA('ratio', 'Repair per year over replacement', 'num', 'IF({col:replace_year}>0,{col:repair_year}/{col:replace_year},0)', 12),
        CA('sentence', 'Sentence for the estimate', 'text', 'IF({col:ratio}<0.8,%s,IF({col:ratio}>1.2,%s,IF({col:age_years}>={set:replace_age},%s,%s)))' % (c5('Repair costs less per year'), c5('Replacement costs less per year'), c5('Replace lead: age is past your limit'), c5('Close call, ask the customer')), 30),
        CO()], D.replace_d(), 50),
    T('scenarios', 'Scenario table', 'Base, best and worst scenarios for monthly profit',
      'Type a labour change, a parts change and a close rate change for each scenario and a volume change; monthly profit and the break-even jobs a week fill in from your last 12 full months.', [
        C('row_id', 'Row ID', 'text', 9, required=True), LST('scenario', 'Scenario', 'scen', 10), C('volume_change', 'Jobs volume change', 'pct', 10), C('labour_change', 'Labour cost change', 'pct', 10), C('parts_change', 'Parts cost change', 'pct', 10),
        C('close_change', 'Close rate change in points', 'pct', 11),
        CA('contribution', 'Monthly contribution at today volume', 'money', 'SUMIFS({range:tick_month.revenue},{range:tick_month.month},">="&%s,{range:tick_month.month},"<"&%s)/12-SUMIFS({range:tick_month.labour_cost},{range:tick_month.month},">="&%s,{range:tick_month.month},"<"&%s)/12*(1+{col:labour_change})-SUMIFS({range:tick_month.parts_cost},{range:tick_month.month},">="&%s,{range:tick_month.month},"<"&%s)/12*(1+{col:parts_change})-(SUMIFS({range:tick_month.sub_cost},{range:tick_month.month},">="&%s,{range:tick_month.month},"<"&%s)+SUMIFS({range:tick_month.other_cost},{range:tick_month.month},">="&%s,{range:tick_month.month},"<"&%s)+SUMIFS({range:tick_month.cb_cost},{range:tick_month.month},">="&%s,{range:tick_month.month},"<"&%s))/12' % ((Y12, MS) * 6), 14),
        CA('volume_factor', 'Volume factor', 'num', '(1+{col:volume_change})*({set:close_target}+{col:close_change})/{set:close_target}', 10),
        CA('monthly_profit', 'Monthly profit', 'money', '{col:volume_factor}*{col:contribution}-{set:overhead_month}', 13),
        CA('profit_change', 'Against base at today volume', 'money', '{col:monthly_profit}-(SUMIFS({range:scenarios.monthly_profit},{range:scenarios.scenario},%s,{range:scenarios.volume_change},0))' % tok('scen', 'Base'), 13),
        CA('break_even_week', 'Break-even jobs a week', 'num', 'IFERROR({set:overhead_month}/({col:contribution}/(SUMIFS({range:tick_month.jobs},{range:tick_month.month},">="&%s,{range:tick_month.month},"<"&%s)/12))/4.345,0)' % (Y12, MS), 12)],
      D.scenarios_d(), 50, [A('monthly_profit', '< 0', 'bad')]),
    T('job_types', 'Job types', 'Job types with trade, kind and target margin',
      'The 15 job types with their trade, kind and target margin; set your own target for each (a typical range, check your own numbers).', [
        LST('job_type', 'Job type', 'jobtype', 24, required=True), LST('trade', 'Trade', 'trade', 10), LST('kind', 'Job kind', 'jobkind', 12), C('target_margin', 'Target margin', 'pct', 10)], D.job_types_d(), 50),
    T('technicians', 'Technicians', 'Technicians with pay rate and van',
      'The six lead technicians with their hourly rate and van; the job costing tool reads the rate.', [
        LST('technician', 'Technician', 'tech', 18, required=True), C('hourly_rate', 'Hourly rate', 'money', 11), LST('van', 'Van', 'van', 8)], D.technicians_d(), 50),
    T('settings_echo', 'Settings echo', 'Targets and rates used on these sheets',
      'The eight settings these sheets read, repeated here so the page you print shows the targets in force; change them on the Start sheet.', [
        C('setting', 'Setting', 'text', 34, required=True),
        CA('value', 'Value', 'num', 'CHOOSE(MATCH({col:setting},{range:settings_echo.setting},0),{set:margin_target},{set:thin_margin},{set:callback_target},{set:close_target},{set:warranty_reserve},{set:overhead_month},{set:burden_pct},{set:replace_age})', 12),
        C('note', 'Note', 'text', 50)], D.settings_echo_d(), 50),
]
assert len(tables) == 20, len(tables)
