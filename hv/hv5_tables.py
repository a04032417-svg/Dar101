"""HVAC suite part 5: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv5_lists import *
import hv5_data as D

YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def ph(v): return '"%s"' % v
def CONST(k, label, v): return CA(k, label, 'text', ph(v), 18)
def VANPH(col='van'): return CA('tech_phone', 'Technician phone', 'text', 'IFERROR(CHOOSE(MATCH({col:%s},{range:vans.van},0),%s),"")' % (col, ','.join(ph(p) for p in D.VAN_PHONES)), 18)
def NAMEPH(col='technician', n=6): return CA('tech_phone', 'Technician phone', 'text', 'IFERROR(CHOOSE(MATCH({col:%s},{range:techs.technician},0),%s),"")' % (col, ','.join(ph(p) for p in D.CREW_PHONES[:6])), 18)
def CREWPH(col='technician'):
    f = '""'
    for n, p in reversed(list(zip(TECH_NAMES, D.CREW_PHONES))): f = 'IF({col:%s}=%s,%s,%s)' % (col, tok('crew', n), ph(p), f)
    return CA('tech_phone', 'Technician phone', 'text', f, 18)
COMPANY_COL = lambda: CA('company', 'Company', 'text', '{set:company}', 24)
BELOW, ATMIN, STOCKED = ck('Below minimum'), ck('At minimum'), ck('Stocked')
LAST3, PREV3 = tok('cperiod', 'Last 3 months'), tok('cperiod', 'Previous 3 months')
LAST6 = tok('speriod', 'Last 6 counts')

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('vehicle_hour', 'Vehicle cost per hour on the road', 'money', VEHICLE_HOUR),
    S('count_days', 'Days allowed between van stock counts', 'int', 60), S('count_tolerance', 'Stock count tolerance for one part line (money)', 'money', 25),
    S('shrink_target', 'Shrink wanted at most, share of van stock (typical range)', 'pct', 0.03),
    S('markup_target', 'Markup wanted on parts (typical range, check yours)', 'pct', 0.6), S('order_lines', 'Parts below minimum on a van that mean order today', 'int', 3),
    S('unbilled_alert', 'Unbilled parts a week that you want to chase (money)', 'money', 100), S('months_high', 'Months of stock held that is too much', 'num', 2.5),
    S('months_low', 'Months of stock held that is too little', 'num', 1.1), S('road_hours_day', 'Hours on the road for a van on a working day', 'num', 8),
    S('vehicle_budget_day', 'Vehicle cost wanted per working day, per van (money)', 'money', 105), S('rise_alert', 'Supplier cost rise that flags a price-book line', 'pct', 0.03),
    S('tool_rise', 'Price rise to test on tool replacement', 'pct', 0.10), S('season_lead_days', 'Days before a season to run the supplier order', 'int', 7),
]
tables = []
# 1 van stock
tables.append(T('van_stock', 'Van Stock', 'Van stock with minimum, maximum and restock quantity',
  'One row per part carried on a van with a minimum and a maximum; value, the below-minimum check, the quantity to reach the maximum and the restock cost fill in by themselves.', [
    C('stock_id', 'Stock', 'text', 10, required=True), LST('van', 'Van', 'van', 8), C('part_id', 'Part', 'text', 10), C('part', 'Part name', 'text', 24), LST('category', 'Category', 'partcat', 12),
    C('van_min', 'Minimum', 'int', 9), C('van_max', 'Maximum', 'int', 9), C('on_hand', 'On hand', 'int', 9), C('unit_cost', 'Unit cost', 'money', 11), C('last_counted', 'Last counted', 'date', 12), LST('supplier', 'Supplier', 'supplier', 22),
    CA('value', 'Value', 'money', '{col:on_hand}*{col:unit_cost}', 11),
    CA('below_min', 'Stock check', 'text', 'IF({col:on_hand}<{col:van_min},%s,IF({col:on_hand}={col:van_min},%s,%s))' % (BELOW, ATMIN, STOCKED), 16),
    CA('restock_qty', 'Quantity to reach the maximum', 'int', 'IF({col:on_hand}<{col:van_min},{col:van_max}-{col:on_hand},0)', 11),
    CA('restock_cost', 'Restock cost', 'money', '{col:restock_qty}*{col:unit_cost}', 11),
    CA('restock_key', 'Restock order score', 'num', 'IF({col:restock_cost}>0,{col:restock_cost}+VALUE(RIGHT({col:stock_id},4))/100000,"")', 12),
    CA('van_rank', 'Rank on the van', 'int', 'IF(ISNUMBER({col:restock_key}),COUNTIFS({range:van_stock.van},{col:van},{range:van_stock.restock_key},">"&{col:restock_key})+1,"")', 9),
    CA('van_rank_key', 'Van and rank key', 'text', 'IF(ISNUMBER({col:van_rank}),{col:van}&"|"&{col:van_rank},"")', 12),
    CA('days_since_count', 'Days since counted', 'int', '{today}-{col:last_counted}', 9)],
  D.van_stock_d(), 300, [A('below_min', '= ' + BELOW, 'bad'), A('below_min', '= ' + ATMIN, 'warn')]))
# 2 stock counts
tables.append(T('stock_counts', 'Stock Counts', 'Stock counts: expected against counted',
  'One row per part counted on a van: expected and counted quantities; the variance, its value, the missing value and the recount flag fill in by themselves.', [
    C('count_id', 'Count', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('van', 'Van', 'van', 8), C('part_id', 'Part', 'text', 10), C('part', 'Part name', 'text', 24), C('expected', 'Expected', 'int', 9),
    C('counted', 'Counted', 'int', 9), C('unit_cost', 'Unit cost', 'money', 11),
    CA('variance', 'Variance', 'int', '{col:counted}-{col:expected}', 9), CA('variance_value', 'Variance value', 'money', '{col:variance}*{col:unit_cost}', 11),
    CA('missing_value', 'Missing value', 'money', 'IF({col:variance}<0,-{col:variance_value},0)', 11),
    CA('flag', 'Count check', 'text', 'IF({col:missing_value}>{set:count_tolerance},%s,IF({col:variance}<0,%s,IF({col:variance}>0,%s,%s)))' % (ck('Recount'), ck('Short, within tolerance'), ck('Over'), ck('Matches')), 18),
    CA('miss_key', 'Missing order score', 'num', 'IF({col:missing_value}>0,{col:missing_value}+VALUE(RIGHT({col:count_id},5))/10000000,"")', 12),
    CA('miss_rank', 'Rank in the count', 'int', 'IF(ISNUMBER({col:miss_key}),COUNTIFS({range:stock_counts.van},{col:van},{range:stock_counts.date},{col:date},{range:stock_counts.miss_key},">"&{col:miss_key})+1,"")', 9),
    CA('miss_rank_key', 'Van, date and rank key', 'text', 'IF(ISNUMBER({col:miss_rank}),{col:van}&"|"&{col:date}&"|"&{col:miss_rank},"")', 14),
    CA('technician', 'Technician', 'text', LKT('vans.technician', 'vans.van', 'van'), 16), VANPH(), COMPANY_COL()],
  D.stock_counts_d(), 700, [A('flag', '= ' + ck('Recount'), 'bad'), A('flag', '= ' + ck('Over'), 'warn')]))
# 3 restocks
tables.append(T('restocks', 'Restocks', 'Restocks: parts bought to fill the vans',
  'One row per part restocked on a van: date, week, quantity and cost from your parts counter or equipment supplier; the cost of each run adds up on the charts.', [
    C('restock_id', 'Restock', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('week', 'Week (Monday)', 'date', 12), LST('van', 'Van', 'van', 8), C('part_id', 'Part', 'text', 10), C('part', 'Part name', 'text', 24),
    C('qty', 'Quantity', 'int', 9), C('unit_cost', 'Unit cost', 'money', 11), C('cost', 'Cost', 'money', 11), LST('supplier', 'Supplier', 'supplier', 22),
    CA('technician', 'Technician', 'text', LKT('vans.technician', 'vans.van', 'van'), 16)],
  D.restocks_d(), 900))
# 4 parts used
tables.append(T('parts_used', 'Parts Used', 'Parts used on jobs, from the van or ordered in',
  'One row per part used on a job: van, technician, quantity and cost, whether it left the van and whether it was billed; the unbilled score, the week and the job weight fill in by themselves.', [
    C('use_id', 'Use', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 10), C('job_id', 'Job', 'text', 10), LST('job_type', 'Job type', 'jobtype', 26), LST('van', 'Van', 'van', 8),
    LST('technician', 'Technician', 'tech', 16), C('part_id', 'Part', 'text', 10), C('part', 'Part name', 'text', 24), LST('category', 'Category', 'partcat', 12), C('qty', 'Quantity', 'int', 9), C('unit_cost', 'Unit cost', 'money', 11),
    C('cost', 'Cost', 'money', 11), C('from_van', 'From the van', 'bool', 9), C('billed', 'Billed', 'bool', 9),
    CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12),
    CA('unbilled_key', 'Unbilled order score', 'num', 'IF(AND({col:from_van}=%s,{col:billed}=%s),{col:cost}+VALUE(RIGHT({col:use_id},6))/10000000,"")' % (YES, NO), 12),
    CA('job_weight', 'Job weight', 'num', '1/COUNTIFS({range:parts_used.job_id},{col:job_id})', 9), NAMEPH(), COMPANY_COL()],
  D.parts_used_d(), 1100, [A('billed', '= ' + NO, 'warn')]))
# 5 parts
tables.append(T('parts', 'Parts', 'Parts list with cost, markup and yearly use',
  'One row per part: cost now and a year ago, markup, van minimum and maximum, the yearly quantity and the jobs that used it; price, yearly spend, cost rise and markup gap fill in by themselves.', [
    C('part_id', 'Part', 'text', 10, required=True), C('part', 'Part name', 'text', 24), LST('category', 'Category', 'partcat', 12), C('unit_cost', 'Unit cost', 'money', 11), C('cost_year_ago', 'Cost a year ago', 'money', 12),
    C('markup', 'Markup', 'pct', 9), C('van_min', 'Van minimum', 'int', 9), C('van_max', 'Van maximum', 'int', 9), LST('supplier', 'Supplier', 'supplier', 22), C('year_qty', 'Quantity, 12 months', 'int', 10), C('year_jobs', 'Jobs, 12 months', 'int', 10),
    CA('price', 'Price at your markup', 'money', '{col:unit_cost}*(1+{col:markup})', 11), CA('rise_12m', 'Cost rise, 12 months', 'pct', 'IFERROR({col:unit_cost}/{col:cost_year_ago}-1,0)', 10),
    CA('year_spend', 'Spend, 12 months', 'money', '{col:year_qty}*{col:unit_cost}', 12), CA('spend_old', 'Spend at last year cost', 'money', '{col:year_qty}*{col:cost_year_ago}', 12),
    CA('markup_gap', 'Markup gap to the target', 'pct', '{col:markup}-{set:markup_target}', 10),
    CA('under_key', 'Under-target order score', 'num', 'IF(AND({col:markup}<{set:markup_target},{col:year_spend}>0),{col:year_spend}+VALUE(RIGHT({col:part_id},4))/100000,"")', 12),
    CA('cat_rank', 'Rank in the category', 'int', 'IF(ISNUMBER({col:under_key}),COUNTIFS({range:parts.category},{col:category},{range:parts.under_key},">"&{col:under_key})+1,"")', 9),
    CA('cat_rank_key', 'Category and rank key', 'text', 'IF(ISNUMBER({col:cat_rank}),{col:category}&"|"&{col:cat_rank},"")', 14),
    CA('price_gain', 'Gained a year at the target markup', 'money', 'IF(AND({col:markup}<{set:markup_target},{col:year_spend}>0),{col:year_spend}*({set:markup_target}-{col:markup}),0)', 12)],
  D.parts_d(), 100, [A('markup_gap', '< 0', 'warn'), A('rise_12m', '>= {set:rise_alert}', 'warn')]))
# 6 price changes
tables.append(T('price_changes', 'Supplier Price Changes', 'Supplier price changes with the cost impact',
  'One row per supplier cost change: old and new cost; the rise, the month, the jobs a year that use the part and the extra cost a year fill in by themselves.', [
    C('change_id', 'Change', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('part_id', 'Part', 'text', 10), C('part', 'Part name', 'text', 24), LST('supplier', 'Supplier', 'supplier', 22), LST('category', 'Category', 'pccat', 12),
    C('old_cost', 'Old cost', 'money', 11), C('new_cost', 'New cost', 'money', 11),
    CA('rise', 'Rise', 'pct', 'IFERROR({col:new_cost}/{col:old_cost}-1,0)', 9), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 10),
    CA('jobs_year', 'Jobs a year using the part', 'int', LKN('parts.year_jobs', 'parts.part_id', 'part_id'), 10),
    CA('extra_year', 'Extra cost a year', 'money', '({col:new_cost}-{col:old_cost})*IFERROR(INDEX({range:parts.year_qty},MATCH({col:part_id},{range:parts.part_id},0)),0)', 12),
    CA('order_key', 'Newest first score', 'num', '{col:date}+VALUE(RIGHT({col:change_id},3))/1000', 12),
    CONST('parts_phone', 'Parts counter phone', D.PARTS_PHONE), CONST('supplier_phone', 'Equipment supplier phone', D.SUP_PHONE), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), COMPANY_COL()],
  D.price_changes_d(), 80, [A('rise', '>= 0.1', 'bad'), A('rise', '>= 0.05', 'warn')]))
# 7 price book
UNDER, ROSE, ONT = ck('Under target'), ck('Rose, still on target'), ck('On target')
tables.append(T('price_book', 'Price Book', 'Flat-rate price book with margin after price changes',
  'Your flat-rate price book, a fixed price per task built from cost: parts cost now and a year ago, the flat price and the margin you want; margin, gap, price needed and money at risk fill in.', [
    C('pb_id', 'Task', 'text', 9, required=True), LST('job_type', 'Job type', 'jobtype', 26), C('task', 'Task name', 'text', 26), C('parts_cost', 'Parts cost now', 'money', 11), C('parts_before', 'Parts cost a year ago', 'money', 12),
    C('other_cost', 'Labour and other cost', 'money', 12), C('flat_price', 'Flat price', 'money', 11), C('target_margin', 'Margin wanted', 'pct', 9), C('jobs_year', 'Jobs, 12 months', 'int', 10),
    CA('cost', 'All-in cost', 'money', '{col:parts_cost}+{col:other_cost}', 11), CA('margin', 'Margin now', 'pct', 'IFERROR(1-{col:cost}/{col:flat_price},0)', 9),
    CA('margin_before', 'Margin at last year parts cost', 'pct', 'IFERROR(1-({col:parts_before}+{col:other_cost})/{col:flat_price},0)', 10), CA('gap', 'Gap to the margin wanted', 'pct', '{col:margin}-{col:target_margin}', 10),
    CA('parts_rise', 'Parts cost rise, 12 months', 'pct', 'IFERROR({col:parts_cost}/{col:parts_before}-1,0)', 10),
    CA('price_needed', 'Flat price to reach the margin', 'money', 'IFERROR({col:cost}/(1-{col:target_margin}),0)', 12),
    CA('status', 'Price check', 'text', 'IF({col:margin}<{col:target_margin},%s,IF({col:parts_rise}>={set:rise_alert},%s,%s))' % (UNDER, ROSE, ONT), 20),
    CA('at_risk', 'Money at risk a year', 'money', 'IF({col:margin}<{col:target_margin},{col:jobs_year}*({col:price_needed}-{col:flat_price}),0)', 12),
    CA('risk_key', 'Risk order score', 'num', 'IF({col:at_risk}>0,{col:at_risk}+VALUE(RIGHT({col:pb_id},3))/100000,"")', 12), CA('parts_jobs', 'Parts cost times jobs', 'money', '{col:parts_cost}*{col:jobs_year}', 12)],
  D.price_book_d(), 80, [A('status', '= ' + UNDER, 'bad'), A('status', '= ' + ROSE, 'warn')]))
# 8 open estimates
tables.append(T('estimates_open', 'Open Estimates', 'Open estimates checked against supplier price changes',
  'One row per open estimate: value, parts cost when priced and now, other cost; margin then and now, the gap to the margin wanted and the value needed fill in by themselves.', [
    C('estimate_id', 'Estimate', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('job_type', 'Job type', 'jobtype', 26), C('value', 'Value', 'money', 11), C('parts_priced', 'Parts cost when priced', 'money', 12),
    C('parts_now', 'Parts cost now', 'money', 11), C('other_cost', 'Labour and other cost', 'money', 12),
    CA('margin_priced', 'Margin when priced', 'pct', 'IFERROR(1-({col:parts_priced}+{col:other_cost})/{col:value},0)', 10), CA('margin_now', 'Margin now', 'pct', 'IFERROR(1-({col:parts_now}+{col:other_cost})/{col:value},0)', 9),
    CA('target', 'Margin wanted', 'pct', 'IFERROR(AVERAGEIFS({range:price_book.target_margin},{range:price_book.job_type},{col:job_type}),0)', 9), CA('gap', 'Gap to the margin wanted', 'pct', '{col:margin_now}-{col:target}', 10),
    CA('price_needed', 'Value to reach the margin', 'money', 'IFERROR(({col:parts_now}+{col:other_cost})/(1-{col:target}),0)', 12),
    CA('status', 'Estimate check', 'text', 'IF({col:margin_now}<{col:target},%s,%s)' % (UNDER, ONT), 16), CA('at_risk', 'Money at risk', 'money', 'IF({col:margin_now}<{col:target},{col:price_needed}-{col:value},0)', 11),
    CA('risk_key', 'Risk order score', 'num', 'IF({col:at_risk}>0,{col:at_risk}+VALUE(RIGHT({col:estimate_id},5))/1000000,"")', 12)],
  D.estimates_open_d(), 60, [A('status', '= ' + UNDER, 'bad')]))
# 9 purchases
tables.append(T('purchases', 'Purchases', 'Purchases from suppliers and subcontractors',
  'One row per supplier invoice: date, payee, kind, the job it belongs to, amount, due date and paid date; days to due and the phones for the messages fill in by themselves.', [
    C('po_id', 'Purchase', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('supplier', 'Payee', 'payee', 24), LST('kind', 'Kind', 'pokind', 12), C('job_id', 'Job', 'text', 10), C('amount', 'Amount', 'money', 12),
    C('due_date', 'Due date', 'date', 11), C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'postatus', 10),
    CA('days_to_due', 'Days to due', 'int', 'IF({col:status}=%s,{col:due_date}-{today},"")' % tok('postatus', 'Open'), 9), CA('days_to_pay', 'Days to pay', 'int', 'IF({col:paid_on}="","",{col:paid_on}-{col:date})', 9),
    CONST('parts_phone', 'Parts counter phone', D.PARTS_PHONE), CONST('elec_phone', 'Electrical subcontractor phone', D.ELEC_PHONE), CONST('sheet_phone', 'Sheet-metal subcontractor phone', D.SHEET_PHONE), COMPANY_COL()],
  D.purchases_d(), 400, [A('days_to_due', '<= 3', 'bad'), A('status', '= ' + tok('postatus', 'Open'), 'warn')]))
# 10 vehicle costs
OVER, WITHIN = ck('Over budget'), ck('Within budget')
tables.append(T('vehicle_costs', 'Vehicle Costs', 'Vehicle costs by van and month',
  'One row per van and month: fuel, repairs, tyres, lease and insurance with the working days and jobs; total, cost per working day, cost per job and the budget check fill in by themselves.', [
    C('vc_id', 'Vehicle cost', 'text', 10, required=True), C('month', 'Month', 'date', 10), LST('van', 'Van', 'van', 8), C('fuel', 'Fuel', 'money', 11), C('repairs', 'Repairs', 'money', 11), C('tyres', 'Tyres', 'num', 9),
    C('lease', 'Lease', 'money', 11), C('insurance', 'Insurance', 'num', 11), C('working_days', 'Working days', 'int', 9), C('jobs', 'Jobs', 'int', 7),
    CA('total', 'Total', 'money', '{col:fuel}+{col:repairs}+{col:tyres}+{col:lease}+{col:insurance}', 11), CA('per_day', 'Cost per working day', 'money', 'IFERROR({col:total}/{col:working_days},0)', 11),
    CA('per_job', 'Cost per job', 'money', 'IFERROR({col:total}/{col:jobs},0)', 10), CA('budget_check', 'Budget check', 'text', 'IF({col:per_day}>{set:vehicle_budget_day},%s,%s)' % (OVER, WITHIN), 14),
    CONST('acct_phone', 'Accountant phone', D.ACCT_PHONE), COMPANY_COL()],
  D.vehicle_costs_d(), 200, [A('budget_check', '= ' + OVER, 'warn')]))
# 11 vans, 20 technicians
tables.append(T('vans', 'Vans', 'Vans with driver and monthly lease', 'The six vans, who drives each and the lease cost a month; the van tables look up the driver and the phone here.',
  [C('van', 'Van', 'text', 9, required=True), C('technician', 'Technician', 'text', 24), C('lease_monthly', 'Lease a month', 'money', 12)], D.vans_d(), 12))
# 12 tools
PASTL, SOON, INL = ck('Past its life'), ck('Due within a year'), ck('In life')
tables.append(T('tools', 'Tools and Equipment', 'Tool and equipment purchase log with replacement year',
  'One row per tool or piece of equipment bought: date, cost, who uses it and its life in years; age, years past life, the replacement year and the check fill in by themselves.', [
    C('tool_id', 'Tool', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('item', 'Item', 'text', 18), C('description', 'Description', 'text', 28), LST('technician', 'Technician', 'crew', 16), C('cost', 'Cost', 'money', 11),
    C('life_years', 'Life, years', 'int', 8), LST('replace_year', 'Replace in', 'ryear', 9),
    CA('age_years', 'Age, years', 'num', '({today}-{col:date})/365.25', 9), CA('over_life', 'Years past life', 'num', '{col:age_years}-{col:life_years}', 9), CA('due_year', 'Replacement year', 'int', 'YEAR({col:date})+{col:life_years}', 10),
    CA('check', 'Tool check', 'text', 'IF({col:over_life}>=0,%s,IF({col:over_life}>=-1,%s,%s))' % (PASTL, SOON, INL), 16),
    CA('rank_key', 'Age order score', 'num', '{col:over_life}+VALUE(RIGHT({col:tool_id},4))/10000000', 12),
    CREWPH(), COMPANY_COL()],
  D.tools_d(), 80, [A('check', '= ' + PASTL, 'bad'), A('check', '= ' + SOON, 'warn')]))
# 13 restock list
def IXR(col): return 'IFERROR(INDEX({range:van_stock.%s},MATCH(LARGE({range:van_stock.restock_key},{col:rank}),{range:van_stock.restock_key},0)),"")' % col
tables.append(T('restock_list', 'Restock List', 'Restock list for the next supplier run, biggest cost first',
  'Parts below the minimum on any van ranked by restock cost: van, part, quantity to the maximum, supplier and cost; it fills in from the Van Stock sheet.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('van', 'Van', 'text', IXR('van'), 8), CA('part', 'Part', 'text', IXR('part'), 24), CA('qty', 'Quantity to order', 'int', IXR('restock_qty'), 10), CA('supplier', 'Supplier', 'text', IXR('supplier'), 22),
    CA('cost', 'Cost', 'money', IXR('restock_cost'), 11), CA('on_hand', 'On hand', 'int', IXR('on_hand'), 8), CA('minimum', 'Minimum', 'int', IXR('van_min'), 8), VANPH(), CONST('parts_phone', 'Parts counter phone', D.PARTS_PHONE), COMPANY_COL()],
  D.restock_list_d(), 60))
# 14 supplier runs
tables.append(T('supplier_runs', 'Supplier Runs', 'Supplier run totals by supplier and van',
  'One row per supplier and van: the lines below minimum, the units and the total for the next run; it fills in from the Van Stock sheet.', [
    C('run_id', 'Run', 'text', 8, required=True), LST('supplier', 'Supplier', 'supplier', 22), LST('van', 'Van', 'van', 8),
    CA('lines', 'Lines', 'int', 'COUNTIFS({range:van_stock.supplier},{col:supplier},{range:van_stock.van},{col:van},{range:van_stock.restock_cost},">0")', 8),
    CA('units', 'Units', 'int', 'SUMIFS({range:van_stock.restock_qty},{range:van_stock.supplier},{col:supplier},{range:van_stock.van},{col:van})', 8),
    CA('total', 'Total', 'money', 'SUMIFS({range:van_stock.restock_cost},{range:van_stock.supplier},{col:supplier},{range:van_stock.van},{col:van})', 11),
    CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CONST('parts_phone', 'Parts counter phone', D.PARTS_PHONE), COMPANY_COL()],
  D.supplier_runs_d(), 20, [A('total', '> 0', 'warn')]))
# 15 shrink by van
ABOVE, WITHINT = ck('Above tolerance'), ck('Within tolerance')
ONTIME, LATE = ck('Counted on time'), ck('Count overdue')
tables.append(T('shrink_van', 'Shrink by Van', 'Shrink by van over the last 6 counts and the counts before',
  'One row per van and count period: stock missing between counts (shrink), van stock value, share, lines below minimum and last count date; it fills in from Stock Counts.', [
    C('row_id', 'Row', 'text', 8, required=True), LST('van', 'Van', 'van', 8), LST('period', 'Period', 'speriod', 15), C('from_date', 'From', 'date', 11), C('to_date', 'To', 'date', 11), C('counts', 'Counts', 'int', 8),
    CA('technician', 'Technician', 'text', LKT('vans.technician', 'vans.van', 'van'), 16),
    CA('missing', 'Stock missing', 'money', 'SUMIFS({range:stock_counts.missing_value},{range:stock_counts.van},{col:van},{range:stock_counts.date},">="&{col:from_date},{range:stock_counts.date},"<="&{col:to_date})', 11),
    CA('net', 'Net variance value', 'money', 'SUMIFS({range:stock_counts.variance_value},{range:stock_counts.van},{col:van},{range:stock_counts.date},">="&{col:from_date},{range:stock_counts.date},"<="&{col:to_date})', 11),
    CA('stock_value', 'Van stock value', 'money', 'SUMIFS({range:van_stock.value},{range:van_stock.van},{col:van})', 11), CA('share', 'Shrink share of stock', 'pct', 'IFERROR({col:missing}/{col:stock_value},0)', 9),
    CA('per_month', 'Shrink a count month', 'money', 'IFERROR({col:missing}/{col:counts},0)', 10),
    CA('status', 'Shrink check', 'text', 'IF({col:share}>{set:shrink_target},%s,%s)' % (ABOVE, WITHINT), 16),
    CA('last_count', 'Last count', 'date', 'SUMPRODUCT(MAX(({range:stock_counts.van}={col:van})*{range:stock_counts.date}))', 11),
    CA('on_time', 'Count timing', 'text', 'IF({today}-{col:last_count}<={set:count_days},%s,%s)' % (ONTIME, LATE), 16), CA('next_count', 'Next count by', 'date', '{col:last_count}+{set:count_days}', 11),
    CA('below_lines', 'Parts below minimum', 'int', 'COUNTIFS({range:van_stock.van},{col:van},{range:van_stock.below_min},%s)' % BELOW, 9),
    CA('restock_cost', 'Restock cost', 'money', 'SUMIFS({range:van_stock.restock_cost},{range:van_stock.van},{col:van})', 11),
    CA('last_missing', 'Missing, last 6 counts', 'money', 'IF({col:period}=%s,{col:missing},"")' % LAST6, 11), VANPH(),
    CONST('amira_phone', 'Apprentice phone, restock', D.CREW_PHONES[6]), CONST('liam_phone', 'Apprentice phone, count', D.CREW_PHONES[7]), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), COMPANY_COL()],
  D.shrink_van_d(), 20, [A('status', '= ' + ABOVE, 'bad'), A('on_time', '= ' + LATE, 'warn')]))
# 16 unbilled parts
def IXU(col): return 'IFERROR(INDEX({range:parts_used.%s},MATCH(LARGE({range:parts_used.unbilled_key},{col:rank}),{range:parts_used.unbilled_key},0)),"")' % col
tables.append(T('unbilled', 'Unbilled Parts', 'Unbilled parts ranked by cost',
  'Parts that left a van and were not billed, biggest cost first: use, job, technician, part, cost and week; it fills in from the Parts Used sheet.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('use_id', 'Use', 'text', IXU('use_id'), 10), CA('job_id', 'Job', 'text', IXU('job_id'), 10), CA('technician', 'Technician', 'text', IXU('technician'), 16),
    CA('part', 'Part', 'text', IXU('part'), 24), CA('cost', 'Cost', 'money', IXU('cost'), 10), CA('week', 'Week (Monday)', 'date', IXU('week'), 12), CA('van', 'Van', 'text', IXU('van'), 8),
    CA('tech_phone', 'Technician phone', 'text', IXU('tech_phone'), 18), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), COMPANY_COL()],
  D.unbilled_d(), 50))
# 17 vehicle cost by van
SOONS, PLANNED = ck('Service due soon'), ck('Service planned')
ABV, BLW, INLN = ck('Above shop average'), ck('Below shop average'), ck('In line with the shop')
def WIN(): return 'IF({col:period}=%s,EDATE(%s,-3),EDATE(%s,-6))' % (LAST3, MS, MS)
def VSUM(col): return 'SUMIFS({range:vehicle_costs.%s},{range:vehicle_costs.van},{col:van},{range:vehicle_costs.month},">="&%s,{range:vehicle_costs.month},"<"&EDATE(%s,3))' % (col, WIN(), WIN())
tables.append(T('vehicle_van', 'Vehicle Cost by Van', 'Vehicle cost by van for the last 3 months and the 3 before',
  'One row per van and period: total cost, working days, jobs, cost per day and per job against the shop average, the service due date and next week jobs; it fills in from Vehicle Costs.', [
    C('row_id', 'Row', 'text', 8, required=True), LST('van', 'Van', 'van', 8), LST('period', 'Period', 'cperiod', 15), C('service_due', 'Service due', 'date', 11), C('jobs_next_week', 'Jobs booked next week', 'int', 10),
    CA('technician', 'Technician', 'text', LKT('vans.technician', 'vans.van', 'van'), 16),
    CA('total', 'Total cost', 'money', VSUM('total'), 11), CA('working_days', 'Working days', 'int', VSUM('working_days'), 9), CA('jobs', 'Jobs', 'int', VSUM('jobs'), 7),
    CA('per_day', 'Cost per working day', 'money', 'IFERROR({col:total}/{col:working_days},0)', 11), CA('per_job', 'Cost per job', 'money', 'IFERROR({col:total}/{col:jobs},0)', 10),
    CA('shop_per_day', 'Shop cost per working day', 'money', 'IFERROR(SUMIFS({range:vehicle_van.total},{range:vehicle_van.period},{col:period})/SUMIFS({range:vehicle_van.working_days},{range:vehicle_van.period},{col:period}),0)', 11),
    CA('gap', 'Gap to the shop', 'pct', 'IFERROR({col:per_day}/{col:shop_per_day}-1,0)', 9),
    CA('status', 'Cost check', 'text', 'IF({col:gap}>0.15,%s,IF({col:gap}<-0.15,%s,%s))' % (ABV, BLW, INLN), 18),
    CA('repairs_12m', 'Repairs, last 12 months', 'money', 'SUMIFS({range:vehicle_costs.repairs},{range:vehicle_costs.van},{col:van},{range:vehicle_costs.month},">="&EDATE(%s,-12),{range:vehicle_costs.month},"<"&%s)' % (MS, MS), 11),
    CA('cost_12m', 'Total cost, last 12 months', 'money', 'SUMIFS({range:vehicle_costs.total},{range:vehicle_costs.van},{col:van},{range:vehicle_costs.month},">="&EDATE(%s,-12),{range:vehicle_costs.month},"<"&%s)' % (MS, MS), 12),
    CA('days_to_service', 'Days to service', 'int', '{col:service_due}-{today}', 9), CA('service_check', 'Service check', 'text', 'IF({col:days_to_service}<=30,%s,%s)' % (SOONS, PLANNED), 16),
    CA('per_day_last', 'Cost per day, last 3 months', 'money', 'IF({col:period}=%s,{col:per_day},"")' % LAST3, 11),
    CA('jobs_at_risk', 'Jobs at risk from short stock', 'int', 'IF(COUNTIFS({range:van_stock.van},{col:van},{range:van_stock.below_min},%s)>0,{col:jobs_next_week},0)' % BELOW, 10),
    VANPH(), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CONST('ins_phone', 'Insurance agent phone', D.INS_PHONE), COMPANY_COL()],
  D.vehicle_van_d(), 20, [A('status', '= ' + ABV, 'warn'), A('service_check', '= ' + SOONS, 'warn')]))
# 18 stock value by month
tables.append(T('stock_month', 'Stock Value by Month', 'Van stock value, parts cost and restock cost by month',
  'One row per month: stock value, restock cost, parts cost, unbilled parts and job revenue; parts share, months of stock held and price changes fill in. The last month is month to date.', [
    C('month', 'Month', 'date', 10, required=True), LST('season', 'Season', 'season', 15), C('stock_value', 'Stock value', 'money', 12), C('restock_cost', 'Restock cost', 'money', 12), C('parts_cost', 'Parts cost', 'money', 12),
    C('unbilled_cost', 'Unbilled parts', 'money', 11), C('revenue', 'Job revenue', 'money', 12), C('jobs', 'Jobs', 'int', 7),
    CA('parts_share', 'Parts cost over revenue', 'pct', 'IFERROR({col:parts_cost}/{col:revenue},0)', 10), CA('months_held', 'Months of stock held', 'num', 'IFERROR({col:stock_value}/{col:parts_cost},0)', 10),
    CA('changes', 'Supplier price changes', 'int', 'COUNTIFS({range:price_changes.month},{col:month})', 9), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), COMPANY_COL()],
  D.stock_month_d(), 40))
# 19 tool plan
tables.append(T('tool_plan', 'Tool Replacement Plan', 'Tool replacement plan by year',
  'One row per year: tools reaching the end of their life, the budget at today cost and with your price rise; the first year includes tools already past life. It fills in from the tool log.', [
    C('year', 'Year', 'int', 8, required=True),
    CA('items_due', 'Tools due', 'int', 'IF({col:year}<=YEAR({today}),COUNTIFS({range:tools.due_year},"<="&{col:year}),COUNTIFS({range:tools.due_year},{col:year}))', 9),
    CA('budget', 'Budget', 'money', 'IF({col:year}<=YEAR({today}),SUMIFS({range:tools.cost},{range:tools.due_year},"<="&{col:year}),SUMIFS({range:tools.cost},{range:tools.due_year},{col:year}))', 12),
    CA('budget_rise', 'Budget with the price rise', 'money', '{col:budget}*(1+{set:tool_rise})', 12), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), COMPANY_COL()],
  D.tool_plan_d(), 20))
# 20 technicians
tables.append(T('techs', 'Technicians', 'Technicians with trade and van', 'The six lead technicians, their trade and the van they drive; the parts tables look up the phones here.',
  [C('technician', 'Technician', 'text', 24, required=True), C('trade', 'Trade', 'text', 11), C('van', 'Van', 'text', 9)], D.techs_d(), 12))
for _t in tables: _t['rows'] = max(50, _t['rows'])
assert len(tables) == 20, len(tables)
