"""HVAC and plumbing suite part 2: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv2_lists import *
import hv2_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def PH(k, label, phone): return CA(k, label, 'text', '"%s"' % phone, 18)
COMPANY_COL = lambda: CA('company', 'Company', 'text', '{set:company}', 26)
OWN = lambda: PH('owner_phone', 'Owner phone', D.OWNER_PH)
OFF = lambda: PH('office_phone', 'Office manager phone', D.OFFICE_PH)
TECHPH = lambda my='technician', rng_='technicians.technician': CA('tech_phone', 'Technician phone', 'text',
    'IFERROR(CHOOSE(MATCH({col:%s},{range:%s},0),%s),"")' % (my, rng_, ','.join('"%s"' % p for p in D.TECH_PH)), 18)
OPEN_, WON, LOST = tok('estoutcome', 'Open'), tok('estoutcome', 'Won'), tok('estoutcome', 'Lost')
GOOD, BETTER, BEST = tok('tier', 'Good'), tok('tier', 'Better'), tok('tier', 'Best')
P30, P90, P12, PPR = tok('period', 'Last 30 days'), tok('period', 'Last 90 days'), tok('period', 'Last 12 months'), tok('period', 'Year before')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
E = lambda c_: '{range:estimates.%s}' % c_

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('margin_target', 'Wanted job margin, a typical range, check your own numbers', 'pct', 0.50),
    S('close_target', 'Wanted close rate: estimates won over estimates decided', 'pct', 0.55), S('diag_fee', 'Diagnostic fee, credited if the customer goes ahead', 'money', DIAG_FEE),
    S('burden_pct', 'Employer extras on pay, confirm with your adviser', 'pct', BURDEN_PCT), S('vehicle_hour', 'Vehicle cost per hour on the road', 'money', VEHICLE_HOUR),
    S('deposit_pct', 'Deposit on installs and replacements', 'pct', DEPOSIT_PCT), S('member_discount', 'Member discount on repairs', 'pct', MEMBER_DISCOUNT),
    S('financing_factor', 'Monthly payment share of the amount financed, your own', 'pct', FINANCE_FACTOR), S('margin_floor', 'Lowest margin you accept on any job', 'pct', 0.30),
    S('margin_tolerance', 'Margin points below target that still count as a watch', 'pct', 0.01), S('rate_service', 'Loaded labour cost per hour, service work', 'money', 40),
    S('rate_install', 'Loaded labour cost per hour, installs and replacements', 'money', 66), S('drive_hours', 'Drive hours added to every price book task', 'num', 0.45),
    S('estimate_valid_days', 'Days an estimate stays valid', 'int', 30), S('stale_days', 'Days after which an open estimate is old', 'int', 14),
    S('followup_days', 'Days to send an estimate after the call', 'int', 3), S('price_change_date', 'Date of the next price change', 'date', 'today+45'),
    S('planned_rise', 'Price rise planned for the next change', 'pct', 0.04), S('finance_example', 'Example amount financed', 'money', 6000),
]
assert len(settings) == 20

# ---------------- price book
KIND = 'IFERROR(INDEX({range:job_types.kind},MATCH({col:job_type},{range:job_types.job_type},0))&"","")'
INST = 'OR({col:kind}=%s,{col:kind}=%s,{col:kind}=%s)' % (tok('jobkind', 'Replacement'), tok('jobkind', 'Install'), tok('jobkind', 'Repipe'))
COST = 'ROUND({col:labour_hours}*IF(%s,{set:rate_install},{set:rate_service})+{col:parts_cost}+{col:permit_fee}+{col:disposal}+{col:sub_cost}+({col:labour_hours}+{set:drive_hours})*{set:vehicle_hour},2)' % INST
NEEDED = 'IF({col:cost}/(1-{col:target_margin})<1000,ROUNDUP({col:cost}/(1-{col:target_margin})/5,0)*5,ROUNDUP({col:cost}/(1-{col:target_margin})/25,0)*25)'
price_book = T('price_book', 'Price Book', 'Flat-rate price book with margin per line',
    'One row per task: hours, parts, permit, disposal and subcontract cost against the flat price; cost, margin, the gap to the target, the price needed and the money lost a year fill in by themselves.', [
    C('pb_id', 'Task ID', 'text', 9, required=True), LST('job_type', 'Job type', 'jobtype', 24), C('task', 'Task', 'text', 30), LST('tier', 'Option', 'tier', 9),
    C('labour_hours', 'Labour hours', 'num', 9), C('parts_cost', 'Parts cost', 'money', 11), C('permit_fee', 'Permit fee', 'num', 10), C('disposal', 'Disposal', 'num', 10),
    C('sub_cost', 'Subcontract cost', 'num', 11), C('flat_price', 'Flat price', 'money', 11), C('previous_price', 'Previous price', 'money', 11),
    REF('main_part', 'Main part', 'parts.part_id', 10), C('main_qty', 'Main part qty', 'int', 9), C('jobs_12m', 'Jobs, 12 months', 'int', 9),
    CA('kind', 'Job kind', 'text', KIND, 12), CA('cost', 'Cost, all in', 'money', COST, 12),
    CA('margin', 'Margin', 'pct', 'IF({col:flat_price}>0,({col:flat_price}-{col:cost})/{col:flat_price},0)', 9),
    CA('target_margin', 'Target margin', 'pct', LKN('job_types.target_margin', 'job_types.job_type', 'job_type'), 9),
    CA('margin_gap', 'Margin gap', 'pct', '{col:margin}-{col:target_margin}', 9),
    CA('status', 'Margin check', 'text', 'IF({col:margin_gap}<-{set:margin_tolerance},%s,IF({col:margin_gap}<0,%s,%s))' % (ca('Under target'), ca('Watch'), ca('On target')), 13),
    CA('price_needed', 'Price at target', 'money', NEEDED, 11), CA('gap_money', 'Money lost per job', 'money', 'MAX(0,{col:price_needed}-{col:flat_price})', 11),
    CA('rise_needed', 'Rise needed', 'pct', 'IF({col:flat_price}>0,MAX(0,{col:price_needed}/{col:flat_price}-1),0)', 9),
    CA('revenue_year', 'Revenue, 12 months', 'money', '{col:jobs_12m}*{col:flat_price}', 13), CA('cost_year', 'Cost, 12 months', 'money', '{col:jobs_12m}*{col:cost}', 13),
    CA('lost_year', 'Margin lost a year', 'money', '{col:jobs_12m}*{col:gap_money}', 12),
    CA('member_price', 'Member price', 'money', 'IF({col:kind}=%s,ROUND({col:flat_price}*(1-{set:member_discount}),0),{col:flat_price})' % tok('jobkind', 'Repair'), 11),
    CA('member_margin', 'Member margin', 'pct', 'IF({col:member_price}>0,({col:member_price}-{col:cost})/{col:member_price},0)', 9),
    CA('member_flag', 'Member price check', 'text', 'IF({col:member_margin}<{set:margin_floor},%s,%s)' % (ca('Under floor'), ca('Above floor')), 13),
    CA('repair_margin', 'Repair margin', 'pct', 'IF({col:kind}=%s,{col:margin},"")' % tok('jobkind', 'Repair'), 9),
    CA('task_no', 'Task number', 'int', 'VALUE(RIGHT({col:pb_id},3))', 8),
    CA('gap_key', 'Gap key', 'num', '{col:margin_gap}+VALUE(RIGHT({col:pb_id},3))/1000000', 9),
    CA('rank_gap', 'Rank by gap', 'int', 'COUNTIF({range:price_book.gap_key},"<"&{col:gap_key})+1', 8),
    CA('year_key', 'Year key', 'num', '{col:lost_year}+(100-VALUE(RIGHT({col:pb_id},3)))/1000000', 9),
    CA('rank_year', 'Rank by money lost', 'int', 'COUNTIF({range:price_book.year_key},">"&{col:year_key})+1', 8),
    CA('lead_phone', 'Lead technician phone', 'text', 'IF(IFERROR(INDEX({range:job_types.trade},MATCH({col:job_type},{range:job_types.job_type},0)),"")=%s,"%s","%s")' % (tok('trade', 'Plumbing'), D.PLUMB_LEAD, D.HVAC_LEAD), 18),
    PH('elec_phone', 'Electrical subcontractor phone', D.ELEC_PH), PH('sheet_phone', 'Sheet-metal subcontractor phone', D.SHEET_PH), COMPANY_COL()],
    D.book_d(), 80, [A('status', '= ' + ca('Under target'), 'bad'), A('status', '= ' + ca('Watch'), 'warn'), A('member_flag', '= ' + ca('Under floor'), 'warn')])

parts = T('parts', 'Parts Cost List', 'Parts and equipment at today\'s supplier cost',
    'One row per part: supplier cost, the markup you add and the selling price; how many price book lines use it as their main part and how many cost rises are logged fill in by themselves.', [
    C('part_id', 'Part ID', 'text', 9, required=True), C('part', 'Part', 'text', 28), LST('category', 'Category', 'partcat', 12), C('unit_cost', 'Unit cost', 'money', 11), C('markup', 'Markup', 'pct', 9),
    LST('supplier', 'Supplier', 'supplier', 24),
    CA('part_no', 'Part number', 'int', 'VALUE(RIGHT({col:part_id},4))', 8),
    CA('sell_price', 'Selling price', 'money', '{col:unit_cost}*(1+{col:markup})', 11), CA('lines_main', 'Lines using it', 'int', 'COUNTIFS({range:price_book.main_part},{col:part_id})', 9),
    CA('rises_logged', 'Rises logged', 'int', 'COUNTIFS({range:price_changes.part_id},{col:part_id})', 9),
    PH('equip_phone', 'Equipment supplier phone', D.EQUIP_PH), PH('counter_phone', 'Parts counter phone', D.COUNTER_PH), COMPANY_COL()],
    D.parts_d(), 100, [A('rises_logged', '>= 2', 'warn')])

# ---------------- estimates
ESTC = [
    C('estimate_id', 'Estimate ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('site_id', 'Site', 'text', 9), C('site_ref', 'Site reference', 'text', 11),
    C('account', 'Account', 'text', 9), C('phone', 'Phone', 'text', 18), LST('job_type', 'Job type', 'estjt', 24), LST('technician', 'Technician', 'tech', 18), C('options_offered', 'Options offered', 'int', 9),
    C('good_price', 'Good price', 'money', 11), C('better_price', 'Better price', 'money', 11), C('best_price', 'Best price', 'money', 11), LST('option_chosen', 'Option chosen', 'optchosen', 11),
    LST('outcome', 'Outcome', 'estoutcome', 10), C('price_won', 'Price won', 'money', 11), LST('lost_reason', 'Lost reason', 'estlost', 17), C('followup_date', 'Follow-up date', 'date', 11),
    C('call_date', 'Call date', 'date', 11), C('job_date', 'Job date', 'date', 11),
    CA('est_value', 'Estimate value', 'money', 'IF({col:better_price}>0,{col:better_price},{col:good_price})', 12),
    CA('won_flag', 'Won', 'int', 'IF({col:outcome}=%s,1,IF({col:outcome}=%s,0,""))' % (WON, LOST), 7),
    CA('age_days', 'Age in days', 'int', 'IF({col:outcome}=%s,{today}-{col:date},"")' % OPEN_, 8),
    CA('value_open', 'Value open', 'money', 'IF({col:outcome}=%s,{col:est_value},0)' % OPEN_, 11), CA('lost_value', 'Lost value', 'money', 'IF({col:outcome}=%s,{col:est_value},0)' % LOST, 11),
    CA('followup_flag', 'Follow-up check', 'text', 'IF({col:outcome}<>%s,%s,IF({col:followup_date}=0,%s,IF({col:followup_date}<{today},%s,IF({col:followup_date}={today},%s,%s))))' % (OPEN_, ca('Decided'), ca('No follow-up date'), ca('Follow-up overdue'), ca('Due today'), ca('Follow-up set')), 16),
    CA('days_to_estimate', 'Days call to estimate', 'int', 'IF({col:call_date}=0,"",{col:date}-{col:call_date})', 9),
    CA('days_to_job', 'Days estimate to job', 'int', 'IF({col:job_date}=0,"",{col:job_date}-{col:date})', 9),
    CA('valid_until', 'Valid until', 'date', '{col:date}+{set:estimate_valid_days}', 11), CA('file_until', 'Kept on file until', 'date', '{col:date}+90', 11),
    CA('deposit', 'Deposit', 'money', 'ROUND({col:est_value}*{set:deposit_pct},0)', 10),
    CA('monthly_good', 'Monthly payment, good', 'money', 'ROUND({col:good_price}*{set:financing_factor},0)', 10), CA('monthly_better', 'Monthly payment, better', 'money', 'ROUND({col:better_price}*{set:financing_factor},0)', 10),
    CA('monthly_best', 'Monthly payment, best', 'money', 'ROUND({col:best_price}*{set:financing_factor},0)', 10),
    CA('score', 'Follow-up score', 'num', 'IF({col:outcome}=%s,{col:value_open}*({col:age_days}+1)+VALUE(RIGHT({col:estimate_id},5))/100000,"")' % OPEN_, 11),
    CA('open_rank', 'Follow-up rank', 'int', 'IF({col:outcome}=%s,COUNTIF({range:estimates.score},">"&{col:score})+1,"")' % OPEN_, 8),
    TECHPH(), PH('apprentice_phone', 'Apprentice phone', D.APPR_PH), COMPANY_COL()]
estimates = T('estimates', 'Estimates', 'Estimates with options, outcome and follow-up',
    'One row per estimate: site, job type, technician, three prices, option chosen, outcome and follow-up date; value, age, payments and the follow-up rank fill in by themselves.',
    ESTC, D.estimates_d(), 1500, [A('followup_flag', '= ' + ca('Follow-up overdue'), 'bad'), A('followup_flag', '= ' + ca('No follow-up date'), 'warn'), A('outcome', '= ' + WON, 'good'), A('outcome', '= ' + LOST, 'warn')])

option_lines = T('option_lines', 'Option Builder', 'Option lines with cost, margin and monthly payment',
    'One row per option of an estimate: pick the estimate and the option; the price, the cost from the price book, the margin against target, the deposit and the monthly payment fill in.', [
    C('line_id', 'Line ID', 'text', 9, required=True), REF('estimate_id', 'Estimate', 'estimates.estimate_id', 11), LST('option', 'Option', 'tier', 9),
    CA('pos', 'Row', 'int', 'IFERROR(MATCH({col:estimate_id},{range:estimates.estimate_id},0),"")', 6),
    CA('job_type', 'Job type', 'text', 'IF({col:pos}="","",INDEX({range:estimates.job_type},{col:pos}))', 24),
    CA('price', 'Price', 'money', 'IF({col:pos}="",0,IF({col:option}=%s,INDEX({range:estimates.good_price},{col:pos}),IF({col:option}=%s,INDEX({range:estimates.better_price},{col:pos}),INDEX({range:estimates.best_price},{col:pos}))))' % (GOOD, BETTER), 11),
    CA('cost', 'Cost', 'money', 'SUMIFS({range:price_book.cost},{range:price_book.job_type},{col:job_type},{range:price_book.tier},{col:option})', 11),
    CA('margin', 'Margin', 'pct', 'IF({col:price}>0,({col:price}-{col:cost})/{col:price},0)', 9),
    CA('target_margin', 'Target margin', 'pct', LKN('job_types.target_margin', 'job_types.job_type', 'job_type'), 9),
    CA('margin_flag', 'Margin check', 'text', 'IF({col:margin}>={col:target_margin},%s,%s)' % (ca('Meets target'), ca('Below target')), 13),
    CA('monthly_payment', 'Monthly payment', 'money', 'ROUND({col:price}*{set:financing_factor},0)', 11), CA('deposit', 'Deposit', 'money', 'ROUND({col:price}*{set:deposit_pct},0)', 10),
    CA('site_ref', 'Site reference', 'text', 'IF({col:pos}="","",INDEX({range:estimates.site_ref},{col:pos}))', 11), CA('technician', 'Technician', 'text', 'IF({col:pos}="","",INDEX({range:estimates.technician},{col:pos}))', 18)],
    D.option_lines_d(), 200, [A('margin_flag', '= ' + ca('Below target'), 'bad')])

IDX = lambda c_: 'IF({col:pos}="","",INDEX({range:estimates.%s},{col:pos}))' % c_
open_est = T('open_est', 'Open Estimates', 'Open estimates ranked by value times age',
    'Type the rank numbers 1, 2, 3 and so on: each row shows the open estimate with that rank, its value, age and follow-up check, and the date to call next.', [
    C('rank_no', 'Rank', 'int', 7, required=True), CA('pos', 'Row', 'int', 'IFERROR(MATCH({col:rank_no},{range:estimates.open_rank},0),"")', 6),
    CA('estimate_id', 'Estimate ID', 'text', IDX('estimate_id'), 11), CA('site_ref', 'Site reference', 'text', IDX('site_ref'), 11), CA('technician', 'Technician', 'text', IDX('technician'), 18),
    CA('job_type', 'Job type', 'text', IDX('job_type'), 24), CA('est_value', 'Value', 'money', IDX('est_value'), 11), CA('age_days', 'Age in days', 'int', IDX('age_days'), 8),
    CA('followup_date', 'Follow-up date', 'date', 'IF({col:pos}="","",IF(INDEX({range:estimates.followup_date},{col:pos})=0,"",INDEX({range:estimates.followup_date},{col:pos})))', 11),
    CA('followup_flag', 'Follow-up check', 'text', IDX('followup_flag'), 16),
    CA('next_call', 'Call next on', 'date', 'IF({col:pos}="","",IF({col:followup_date}="",{today},MAX({col:followup_date},{today})))', 11),
    CA('open_total', 'Money on the table', 'money', 'SUM({range:estimates.value_open})', 12), CA('open_count', 'Open estimates', 'int', 'COUNTIFS({range:estimates.outcome},%s)' % OPEN_, 9),
    CA('tech_phone', 'Technician phone', 'text', 'IF({col:pos}="","",IFERROR(CHOOSE(MATCH({col:technician},{range:technicians.technician},0),%s),""))' % ','.join('"%s"' % p for p in D.TECH_PH), 18),
    OFF(), OWN(), COMPANY_COL()], D.open_d(), 60, [A('followup_flag', '= ' + ca('Follow-up overdue'), 'bad'), A('followup_flag', '= ' + ca('No follow-up date'), 'warn')])

# ---------------- close rates
TOTAL12 = '{range:estimates.date},">="&({today}-365),{range:estimates.date},"<="&{today}'
FROM_D = 'IF({col:period}=%s,{today}-30,IF({col:period}=%s,{today}-90,IF({col:period}=%s,{today}-365,{today}-730)))' % (P30, P90, P12)
TO_D = 'IF({col:period}=%s,{today}-366,{today})' % PPR
OW_ = '{range:estimates.date},">="&{col:from_d},{range:estimates.date},"<="&{col:to_d}'
close_option = T('close_option', 'Close Rate by Option', 'Close rate by good, better and best',
    'One row per option and period: estimates won at that option and the close rate of the estimates that offered it.', [
    LST('option', 'Option', 'tier', 12, required=True), LST('period', 'Period', 'period', 15), CA('from_d', 'From', 'date', FROM_D, 11), CA('to_d', 'To', 'date', TO_D, 11),
    CA('won', 'Estimates won', 'int', 'COUNTIFS({range:estimates.option_chosen},{col:option},{range:estimates.outcome},%s,%s)' % (WON, OW_), 10),
    CA('close_rate', 'Close rate', 'pct', 'IFERROR({col:won}/IF({col:option}=%s,COUNTIFS({range:estimates.outcome},"<>"&%s,%s),IF({col:option}=%s,COUNTIFS({range:estimates.better_price},">0",{range:estimates.outcome},"<>"&%s,%s),COUNTIFS({range:estimates.best_price},">0",{range:estimates.outcome},"<>"&%s,%s))),0)' % (GOOD, OPEN_, OW_, BETTER, OPEN_, OW_, OPEN_, OW_), 10),
    CA('rate_12m', 'Rate, 12 months', 'pct', 'IF({col:period}=%s,{col:close_rate},"")' % P12, 9)],
    D.close_option_d(), 50)

def CLOSE_COLS(by, bykey):
    W = '{range:estimates.%s},{col:%s},{range:estimates.date},">="&{col:from_d},{range:estimates.date},"<="&{col:to_d}' % (bykey, by)
    return [CA('from_d', 'From', 'date', FROM_D, 11), CA('to_d', 'To', 'date', TO_D, 11),
        CA('estimates', 'Estimates decided', 'int', 'COUNTIFS(%s,{range:estimates.outcome},"<>"&%s)' % (W, OPEN_), 10),
        CA('won', 'Won', 'int', 'COUNTIFS(%s,{range:estimates.outcome},%s)' % (W, WON), 7),
        CA('close_rate', 'Close rate', 'pct', 'IF({col:estimates}>0,{col:won}/{col:estimates},0)', 9),
        CA('avg_ticket', 'Average ticket won', 'money', 'IFERROR(AVERAGEIFS({range:estimates.price_won},%s,{range:estimates.outcome},%s),0)' % (W, WON), 12),
        CA('lost_value', 'Lost value', 'money', 'SUMIFS({range:estimates.lost_value},%s)' % W, 11),
        CA('vs_target', 'Against target', 'text', 'IF({col:close_rate}>={set:close_target},%s,IF({col:close_rate}>={set:close_target}-0.05,%s,%s))' % (ca('On target'), ca('Watch'), ca('Under target')), 13),
        CA('rate_12m', 'Rate, 12 months', 'pct', 'IF({col:period}=%s,{col:close_rate},"")' % P12, 9)]
close_tech = T('close_tech', 'Close Rate by Technician', 'Close rate and average ticket by technician and period',
    'One row per technician and period: estimates decided, won, close rate, average ticket and lost value for the last 90 days, the last 12 months and the year before.', [
    LST('technician', 'Technician', 'tech', 18, required=True), LST('period', 'Period', 'period', 15)] + CLOSE_COLS('technician', 'technician') + [
    CA('won_recent', 'Won, last 90 days', 'int', 'IF({col:period}=%s,{col:won},0)' % P90, 9), TECHPH(), COMPANY_COL()], D.close_tech_d(), 50,
    [A('vs_target', '= ' + ca('Under target'), 'bad'), A('vs_target', '= ' + ca('On target'), 'good')])
close_jt = T('close_jt', 'Close Rate by Job Type', 'Close rate and ticket by job type and period',
    'One row per job type and period: estimates decided, won, close rate, average ticket and lost value for the last 90 days, the last 12 months and the year before.', [
    LST('job_type', 'Job type', 'estjt', 24, required=True), LST('period', 'Period', 'period', 15)] + CLOSE_COLS('job_type', 'job_type'), D.close_jt_d(), 50,
    [A('vs_target', '= ' + ca('Under target'), 'bad'), A('vs_target', '= ' + ca('On target'), 'good')])

lost_reasons = T('lost_reasons', 'Lost Reasons', 'Lost estimates and lost value by reason, last 12 months',
    'One row per reason: lost estimates and lost value in the last 12 months.', [
    LST('reason', 'Reason', 'estlost', 18, required=True),
    CA('estimates', 'Lost estimates', 'int', 'COUNTIFS({range:estimates.lost_reason},{col:reason},{range:estimates.outcome},%s,%s)' % (LOST, TOTAL12), 10),
    CA('lost_value', 'Lost value', 'money', 'SUMIFS({range:estimates.lost_value},{range:estimates.lost_reason},{col:reason},%s)' % TOTAL12, 12)], D.lost_d(), 50)

MR = '{range:estimates.date},">="&{col:month},{range:estimates.date},"<"&EDATE({col:month},1)'
est_months = T('est_months', 'Estimates by Month', 'Estimates, close rate and ticket by month',
    'One row per month: estimates sent, won and lost, value won, close rate and average ticket fill in; type the price book margin of that month.', [
    C('month', 'Month', 'date', 11, required=True), C('book_margin', 'Price book margin', 'pct', 10),
    CA('estimates', 'Estimates sent', 'int', 'COUNTIFS(%s)' % MR, 9), CA('won', 'Won', 'int', 'COUNTIFS(%s,{range:estimates.outcome},%s)' % (MR, WON), 7),
    CA('lost', 'Lost', 'int', 'COUNTIFS(%s,{range:estimates.outcome},%s)' % (MR, LOST), 7),
    CA('value_won', 'Value won', 'money', 'SUMIFS({range:estimates.price_won},%s)' % MR, 12), CA('lost_value', 'Lost value', 'money', 'SUMIFS({range:estimates.lost_value},%s)' % MR, 12),
    CA('close_rate', 'Close rate', 'pct', 'IF({col:won}+{col:lost}>0,{col:won}/({col:won}+{col:lost}),0)', 9),
    CA('avg_ticket', 'Average ticket won', 'money', 'IF({col:won}>0,{col:value_won}/{col:won},0)', 12), OWN(), COMPANY_COL()], D.est_months_d(), 60,
    [A('close_rate', '< {set:close_target}', 'warn')])
# est_months demo needs the month key
job_types = T('job_types', 'Job Types', 'Job types with target margin and price range',
    'One row per job type: trade, kind, average hours and your target margin; the number of price book lines and their lowest, highest and average price fill in by themselves.', [
    C('job_type', 'Job type', 'text', 26, required=True), LST('trade', 'Trade', 'trade', 10), LST('kind', 'Kind', 'jobkind', 12), C('avg_hours', 'Average hours', 'num', 9), C('target_margin', 'Target margin', 'pct', 9),
    CA('lines', 'Price book lines', 'int', 'COUNTIFS({range:price_book.job_type},{col:job_type})', 9),
    CA('min_price', 'Lowest price', 'money', 'SUMPRODUCT(MIN({range:price_book.flat_price}+({range:price_book.job_type}<>{col:job_type})*1000000))', 11),
    CA('max_price', 'Highest price', 'money', 'SUMPRODUCT(MAX({range:price_book.flat_price}*({range:price_book.job_type}={col:job_type})))', 11),
    CA('avg_price', 'Average price', 'money', 'IFERROR(AVERAGEIFS({range:price_book.flat_price},{range:price_book.job_type},{col:job_type}),0)', 11),
    CA('member_avg', 'Member price, average', 'money', 'IF({col:kind}=%s,ROUND({col:avg_price}*(1-{set:member_discount}),0),{col:avg_price})' % tok('jobkind', 'Repair'), 11), COMPANY_COL()], D.job_types_d(), 50)

labour_rates = T('labour_rates', 'Labour Rates', 'Hourly and loaded labour rate by technician',
    'One row per technician: hourly pay and the loaded rate with employer extras (confirm with your adviser).', [
    LST('technician', 'Technician', 'tech', 18, required=True), C('hourly_rate', 'Hourly rate', 'money', 11),
    CA('loaded_rate', 'Loaded rate', 'money', 'ROUND({col:hourly_rate}*(1+{set:burden_pct}),2)', 11)], D.labour_d(), 50)

price_changes = T('price_changes', 'Supplier Price Changes', 'Supplier cost changes by part',
    'One row per supplier price change: the part, old and new cost; the rise and the price book lines that use the part fill in by themselves.', [
    C('change_id', 'Change ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('part_id', 'Part ID', 'parts.part_id', 10), LST('supplier', 'Supplier', 'supplier', 24),
    C('old_cost', 'Old cost', 'money', 11), C('new_cost', 'New cost', 'money', 11),
    CA('part', 'Part', 'text', LKT('parts.part', 'parts.part_id', 'part_id'), 28), CA('rise', 'Rise', 'pct', 'IF({col:old_cost}>0,{col:new_cost}/{col:old_cost}-1,0)', 8),
    CA('lines_hit', 'Lines using it', 'int', 'COUNTIFS({range:price_book.main_part},{col:part_id})', 9), OWN(), OFF(), PH('acct_phone', 'Accountant phone', D.ACCT_PH), COMPANY_COL()],
    D.changes_d(), 80, [A('rise', '>= 0.1', 'bad')])

lines_under = T('lines_under', 'Lines Under Target', 'Price book lines ranked from the lowest margin gap',
    'Type the rank numbers 1, 2, 3 and so on: each row shows the price book line with that rank, its margin against the target and the price needed.', [
    C('rank_no', 'Rank', 'int', 7, required=True), CA('pos', 'Row', 'int', 'IFERROR(MATCH({col:rank_no},{range:price_book.rank_gap},0),"")', 6),
    CA('pb_id', 'Task ID', 'text', 'IF({col:pos}="","",INDEX({range:price_book.pb_id},{col:pos}))', 9), CA('task', 'Task', 'text', 'IF({col:pos}="","",INDEX({range:price_book.task},{col:pos}))', 30),
    CA('flat_price', 'Flat price', 'money', 'IF({col:pos}="","",INDEX({range:price_book.flat_price},{col:pos}))', 11), CA('cost', 'Cost', 'money', 'IF({col:pos}="","",INDEX({range:price_book.cost},{col:pos}))', 11),
    CA('margin', 'Margin', 'pct', 'IF({col:pos}="","",INDEX({range:price_book.margin},{col:pos}))', 9), CA('target_margin', 'Target', 'pct', 'IF({col:pos}="","",INDEX({range:price_book.target_margin},{col:pos}))', 9),
    CA('price_needed', 'Price needed', 'money', 'IF({col:pos}="","",INDEX({range:price_book.price_needed},{col:pos}))', 11),
    CA('rise_needed', 'Rise needed', 'pct', 'IF({col:pos}="","",INDEX({range:price_book.rise_needed},{col:pos}))', 9),
    CA('lost_year', 'Margin lost a year', 'money', 'IF({col:pos}="","",INDEX({range:price_book.lost_year},{col:pos}))', 12),
    CA('status', 'Margin check', 'text', 'IF({col:pos}="","",INDEX({range:price_book.status},{col:pos}))', 13),
    CA('under_count', 'Lines under target', 'int', 'COUNTIFS({range:price_book.status},%s)' % ca('Under target'), 9), OWN(), COMPANY_COL()],
    D.under_d(), 60, [A('status', '= ' + ca('Under target'), 'bad'), A('status', '= ' + ca('Watch'), 'warn')])

price_rise = T('price_rise', 'Price Rise Scenarios', 'What a price rise earns and how many jobs you can lose',
    'One row per price rise: price book lines brought back on target, the extra margin a year and the jobs you can lose before profit falls.', [
    C('rise_pct', 'Price rise', 'pct', 9, required=True),
    CA('lines_fixed', 'Lines back on target', 'int', 'COUNTIFS({range:price_book.rise_needed},">0",{range:price_book.rise_needed},"<="&{col:rise_pct})', 10),
    CA('extra_margin', 'Extra margin a year', 'money', 'SUM({range:price_book.revenue_year})*{col:rise_pct}', 13),
    CA('loss_share', 'Job loss allowed', 'pct', '{col:rise_pct}/((SUM({range:price_book.revenue_year})-SUM({range:price_book.cost_year}))/SUM({range:price_book.revenue_year})+{col:rise_pct})', 9),
    CA('jobs_lost', 'Jobs to lose to break even', 'int', 'ROUND({col:loss_share}*SUM({range:price_book.jobs_12m}),0)', 11)], D.rise_d(), 50)

fin_options = T('fin_options', 'Financing Options', 'Monthly payment factor by term',
    'One row per term in months: type the monthly factor of your financing offer; the payment on the example amount fills in.', [
    C('term_months', 'Term in months', 'int', 10, required=True), C('monthly_factor', 'Monthly factor', 'pct', 10),
    CA('example_payment', 'Example payment', 'money', 'ROUND({set:finance_example}*{col:monthly_factor},0)', 11)], D.fin_d(), 50)

diag_months = T('diag_months', 'Diagnostic Visits', 'Diagnostic visits, conversion and fee income by month',
    'One row per month: diagnostic visits, the visits that led to a repair or replacement estimate, fee income and visit cost; conversion and net cost per visit fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('visits', 'Diagnostic visits', 'int', 10), C('converted', 'Converted to repair', 'int', 10), C('fee_income', 'Fee income', 'money', 11), C('visit_cost', 'Visit cost', 'money', 11),
    CA('conversion', 'Conversion', 'pct', 'IF({col:visits}>0,{col:converted}/{col:visits},0)', 9), CA('cost_per_visit', 'Cost per visit', 'money', 'IF({col:visits}>0,{col:visit_cost}/{col:visits},0)', 11),
    CA('net_per_visit', 'Fee less cost per visit', 'money', 'IF({col:visits}>0,({col:fee_income}-{col:visit_cost})/{col:visits},0)', 11), OWN(), COMPANY_COL()], D.diag_d(), 50,
    [A('conversion', '< 0.55', 'warn')])

technicians = T('technicians', 'Technicians', 'Lead technicians with trade and van', 'One row per lead technician: trade and the van they drive.', [
    LST('technician', 'Technician', 'tech', 18, required=True), LST('trade', 'Trade', 'trade', 10), LST('van', 'Van', 'van', 10)], D.tech_d(), 50)

sites = T('sites', 'Customer Sites', 'Customer sites by reference, area and phone',
    'One row per site: reference, area, site type, account, phone and the date of the last job; a site is never named.', [
    C('site_id', 'Site', 'text', 9, required=True), C('site_ref', 'Site reference', 'text', 11), LST('area', 'Area', 'area', 12), LST('site_type', 'Site type', 'sitetype', 10), C('account', 'Account', 'text', 9),
    C('phone', 'Phone', 'text', 18), C('member', 'Member', 'bool', 8), C('last_job', 'Last job', 'date', 11),
    CA('price_date', 'Next price change', 'date', '{set:price_change_date}', 11), COMPANY_COL()], D.sites_d(), 300)

quote_log = T('quote_log', 'Quote Log', 'Quotes given by phone', 'One row per phone quote: site, job type, price quoted and outcome; the phone, the price book average, the member price and the deposit fill in.', [
    C('quote_id', 'Quote ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('site_ref', 'Site reference', 'sites.site_ref', 11), LST('job_type', 'Job type', 'jobtype', 24),
    C('price_quoted', 'Price quoted', 'money', 11), LST('outcome', 'Outcome', 'quoteout', 17),
    CA('phone', 'Phone', 'text', LKT('sites.phone', 'sites.site_ref', 'site_ref'), 18),
    CA('book_price', 'Price book average', 'money', 'IFERROR(AVERAGEIFS({range:price_book.flat_price},{range:price_book.job_type},{col:job_type}),0)', 11),
    CA('vs_book', 'Against the book', 'pct', 'IF({col:book_price}>0,{col:price_quoted}/{col:book_price}-1,0)', 9),
    CA('member_price', 'Member price', 'money', 'IF(IFERROR(INDEX({range:job_types.kind},MATCH({col:job_type},{range:job_types.job_type},0)),"")=%s,ROUND({col:price_quoted}*(1-{set:member_discount}),0),{col:price_quoted})' % tok('jobkind', 'Repair'), 11),
    CA('deposit', 'Deposit', 'money', 'ROUND({col:price_quoted}*{set:deposit_pct},0)', 10), COMPANY_COL()], D.quotes_d(), 100)

tables = [price_book, parts, estimates, option_lines, open_est, close_option, close_tech, close_jt, lost_reasons, est_months, job_types, labour_rates, price_changes, lines_under, price_rise, fin_options, diag_months, technicians, sites, quote_log]
assert len(tables) == 20
