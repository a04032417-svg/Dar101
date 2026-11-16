"""HVAC and plumbing contractor suite - part 5: Parts, Van Stock and Vehicles."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv5_lists import *
from hv5_tables import settings, tables
from hv5_tools import tools
import hv5_data as D

SUITE = 'fx-20261115-hvac-plumbing'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
BELOW = ck('Below minimum'); UNDER = ck('Under target'); ROSE = ck('Rose, still on target')
LAST3, LAST6 = tok('cperiod', 'Last 3 months'), tok('speriod', 'Last 6 counts')
def F(*pairs): return [FV(a, b) for a, b in pairs]
def PK(tbl, key, col, fmt):  # a calculated field read from the picked row
    return FF(col[1], 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (tbl, col[0], tbl, key), fmt)

forms = [
    FORM('van_count_sheet', 'Van Stock Count Sheet', 'Van stock count line', 'van_stock.stock_id', F(('Van', 'van_stock.van'), ('Part', 'van_stock.part_id'), ('Part name', 'van_stock.part'), ('Category', 'van_stock.category'), ('Minimum', 'van_stock.van_min'),
        ('Maximum', 'van_stock.van_max'), ('On hand', 'van_stock.on_hand'), ('Unit cost', 'van_stock.unit_cost'), ('Value', 'van_stock.value'), ('Last counted', 'van_stock.last_counted'), ('Stock check', 'van_stock.below_min'),
        ('Days since counted', 'van_stock.days_since_count'), ('Supplier', 'van_stock.supplier'))),
    FORM('restock_request', 'Van Restock Request Sheet', 'Restock request for one part', 'restock_list.rank', F(('Van', 'restock_list.van'), ('Part', 'restock_list.part'), ('Quantity to order', 'restock_list.qty'), ('Supplier', 'restock_list.supplier'),
        ('Cost', 'restock_list.cost'), ('On hand', 'restock_list.on_hand'), ('Minimum', 'restock_list.minimum'), ('Technician phone', 'restock_list.tech_phone'))),
    FORM('parts_used_sheet', 'Parts Used on Job Sheet', 'Parts used on a job', 'parts_used.use_id', F(('Date', 'parts_used.date'), ('Job', 'parts_used.job_id'), ('Job type', 'parts_used.job_type'), ('Van', 'parts_used.van'), ('Technician', 'parts_used.technician'),
        ('Part', 'parts_used.part'), ('Category', 'parts_used.category'), ('Quantity', 'parts_used.qty'), ('Unit cost', 'parts_used.unit_cost'), ('Cost', 'parts_used.cost'), ('From the van', 'parts_used.from_van'), ('Billed', 'parts_used.billed')) + [
        FF('Price to bill at your markup', 'IFERROR(INDEX({range:parts.price},MATCH(INDEX({range:parts_used.part_id},MATCH({pick},{range:parts_used.use_id},0)),{range:parts.part_id},0))*INDEX({range:parts_used.qty},MATCH({pick},{range:parts_used.use_id},0)),0)', 'money')]),
    FORM('parts_return_sheet', 'Parts Return Sheet', 'Parts return to the supplier', 'restocks.restock_id', F(('Date bought', 'restocks.date'), ('Van', 'restocks.van'), ('Part', 'restocks.part'), ('Quantity', 'restocks.qty'), ('Unit cost', 'restocks.unit_cost'),
        ('Cost', 'restocks.cost'), ('Supplier', 'restocks.supplier'), ('Technician', 'restocks.technician')) + [FF('Days since bought', '{today}-INDEX({range:restocks.date},MATCH({pick},{range:restocks.restock_id},0))', 'int')]),
    FORM('price_change_sheet', 'Supplier Price Change Sheet', 'Supplier price change record', 'price_changes.change_id', F(('Date', 'price_changes.date'), ('Part', 'price_changes.part'), ('Supplier', 'price_changes.supplier'), ('Category', 'price_changes.category'),
        ('Old cost', 'price_changes.old_cost'), ('New cost', 'price_changes.new_cost'), ('Rise', 'price_changes.rise'), ('Month', 'price_changes.month'), ('Jobs a year using the part', 'price_changes.jobs_year'), ('Extra cost a year', 'price_changes.extra_year'))),
    FORM('supplier_order_sheet', 'Supplier Order Sheet', 'Supplier order and its due date', 'purchases.po_id', F(('Date', 'purchases.date'), ('Payee', 'purchases.supplier'), ('Kind', 'purchases.kind'), ('Job', 'purchases.job_id'), ('Amount', 'purchases.amount'),
        ('Due date', 'purchases.due_date'), ('Paid on', 'purchases.paid_on'), ('Status', 'purchases.status'), ('Days to pay', 'purchases.days_to_pay'))),
    FORM('vehicle_cost_sheet', 'Vehicle Cost Sheet', 'Vehicle cost for one van and month', 'vehicle_costs.vc_id', F(('Month', 'vehicle_costs.month'), ('Van', 'vehicle_costs.van'), ('Fuel', 'vehicle_costs.fuel'), ('Repairs', 'vehicle_costs.repairs'), ('Tyres', 'vehicle_costs.tyres'),
        ('Lease', 'vehicle_costs.lease'), ('Insurance', 'vehicle_costs.insurance'), ('Total', 'vehicle_costs.total'), ('Working days', 'vehicle_costs.working_days'), ('Jobs', 'vehicle_costs.jobs'), ('Cost per working day', 'vehicle_costs.per_day'),
        ('Cost per job', 'vehicle_costs.per_job'), ('Budget check', 'vehicle_costs.budget_check'))),
    FORM('vehicle_service_sheet', 'Vehicle Service Sheet', 'Vehicle service booking', 'vehicle_van.row_id', F(('Van', 'vehicle_van.van'), ('Technician', 'vehicle_van.technician'), ('Service due', 'vehicle_van.service_due'), ('Days to service', 'vehicle_van.days_to_service'),
        ('Service check', 'vehicle_van.service_check'), ('Jobs booked next week', 'vehicle_van.jobs_next_week'), ('Jobs at risk from short stock', 'vehicle_van.jobs_at_risk'), ('Cost per working day', 'vehicle_van.per_day'), ('Technician phone', 'vehicle_van.tech_phone'))),
    FORM('vehicle_replace_sheet', 'Vehicle Replacement Sheet', 'Vehicle replacement review', 'vehicle_van.row_id', F(('Van', 'vehicle_van.van'), ('Technician', 'vehicle_van.technician'), ('Total cost, last 3 months', 'vehicle_van.total'), ('Repairs, last 12 months', 'vehicle_van.repairs_12m'),
        ('Total cost, last 12 months', 'vehicle_van.cost_12m'), ('Cost per working day', 'vehicle_van.per_day'), ('Gap to the shop', 'vehicle_van.gap'), ('Cost check', 'vehicle_van.status')) + [
        FF('Repairs, share of the 12-month cost', 'IFERROR(INDEX({range:vehicle_van.repairs_12m},MATCH({pick},{range:vehicle_van.row_id},0))/INDEX({range:vehicle_van.cost_12m},MATCH({pick},{range:vehicle_van.row_id},0)),0)', 'pct')]),
    FORM('tool_purchase_sheet', 'Tool Purchase Sheet', 'Tool or equipment purchase', 'tools.tool_id', F(('Date', 'tools.date'), ('Item', 'tools.item'), ('Description', 'tools.description'), ('Technician', 'tools.technician'), ('Cost', 'tools.cost'), ('Life, years', 'tools.life_years'),
        ('Replace in', 'tools.replace_year'), ('Age, years', 'tools.age_years'), ('Years past life', 'tools.over_life'), ('Tool check', 'tools.check'))),
    FORM('tool_assign_sheet', 'Tool Assignment Sheet', 'Tool assigned to a technician', 'tools.tool_id', F(('Item', 'tools.item'), ('Description', 'tools.description'), ('Technician', 'tools.technician'), ('Technician phone', 'tools.tech_phone'), ('Date bought', 'tools.date'), ('Tool check', 'tools.check')) + [
        FF('Van of the technician', 'IFERROR(INDEX({range:vans.van},MATCH(INDEX({range:tools.technician},MATCH({pick},{range:tools.tool_id},0)),{range:vans.technician},0)),"")', 'text')]),
    FORM('shrink_sheet', 'Shrink Investigation Sheet', 'Shrink investigation for one van', 'shrink_van.row_id', F(('Van', 'shrink_van.van'), ('Technician', 'shrink_van.technician'), ('Period', 'shrink_van.period'), ('From', 'shrink_van.from_date'), ('To', 'shrink_van.to_date'),
        ('Counts', 'shrink_van.counts'), ('Stock missing', 'shrink_van.missing'), ('Van stock value', 'shrink_van.stock_value'), ('Shrink share of stock', 'shrink_van.share'), ('Shrink a count month', 'shrink_van.per_month'), ('Shrink check', 'shrink_van.status'),
        ('Last count', 'shrink_van.last_count'), ('Count timing', 'shrink_van.on_time'), ('Parts below minimum', 'shrink_van.below_lines'))),
]
assert len(forms) == 12
SG = ['Technician', 'Office manager']
documents = [
    DOC('van_sheet_doc', 'Van Stock Sheet', 'Van stock sheet for one van', 'shrink_van.row_id', [
        'Van stock sheet of {set:company}, dated {today}. Van {col:shrink_van.van}, technician {col:shrink_van.technician}.', 'Van stock value: {col:shrink_van.stock_value}. Parts below minimum: {col:shrink_van.below_lines}. Restock cost to reach the maximum: {col:shrink_van.restock_cost}.',
        'Last count: {col:shrink_van.last_count}. Next count by: {col:shrink_van.next_count}. Count timing: {col:shrink_van.on_time}.', 'Each part line with its minimum, maximum and the quantity on hand is written below at the count.'], SG, NOTE),
    DOC('restock_order_doc', 'Restock Order', 'Restock order for the parts counter', 'supplier_runs.run_id', [
        'Restock order of {set:company}, dated {today}. Supplier: {col:supplier_runs.supplier}. Phone: {col:supplier_runs.parts_phone}.', 'Van {col:supplier_runs.van}: {col:supplier_runs.lines} lines, {col:supplier_runs.units} units, total {col:supplier_runs.total}, before sales tax.',
        'The part lines and quantities are written below. The parts counter confirms the price and the pick-up time.'], ['Office manager', 'Parts counter'], NOTE),
    DOC('price_notice_doc', 'Supplier Price Change Notice', 'Supplier price change notice', 'price_changes.change_id', [
        'Supplier price change notice of {set:company}, dated {today}. Change {col:price_changes.change_id} on {col:price_changes.date}.', 'Part: {col:price_changes.part}. Supplier: {col:price_changes.supplier}. Old cost {col:price_changes.old_cost}, new cost {col:price_changes.new_cost}, rise {col:price_changes.rise}.',
        'Jobs a year that use the part: {col:price_changes.jobs_year}. Extra cost a year: {col:price_changes.extra_year}.', 'The price-book lines and open estimates to update are written below.'], ['Office manager', 'Owner'], NOTE),
    DOC('parts_job_doc', 'Parts Used on a Job', 'Parts used on a job, for the invoice', 'parts_used.use_id', [
        'Parts used on a job, {set:company}, dated {today}. Use {col:parts_used.use_id} on {col:parts_used.date}, job {col:parts_used.job_id}, {col:parts_used.job_type}.', 'Technician: {col:parts_used.technician}, van {col:parts_used.van}. Part: {col:parts_used.part}, category {col:parts_used.category}, quantity {col:parts_used.qty}.',
        'Cost: {col:parts_used.cost}. Taken from the van: {col:parts_used.from_van}. Billed: {col:parts_used.billed}.', 'The invoice number the part is billed on is written below.'], SG, NOTE),
    DOC('unbilled_doc', 'Unbilled Parts Report', 'Unbilled parts report line', 'unbilled.rank', [
        'Unbilled parts report of {set:company}, dated {today}. Rank {col:unbilled.rank}.', 'Use {col:unbilled.use_id} on job {col:unbilled.job_id}, technician {col:unbilled.technician}, van {col:unbilled.van}. Part: {col:unbilled.part}. Cost: {col:unbilled.cost}. Week of {col:unbilled.week}.',
        'The invoice that now carries the part is written below.'], ['Office manager', 'Technician'], NOTE),
    DOC('count_report_doc', 'Stock Count Report', 'Stock count report with variances', 'stock_counts.count_id', [
        'Stock count report of {set:company}, dated {today}. Count {col:stock_counts.count_id} on {col:stock_counts.date}, van {col:stock_counts.van}, technician {col:stock_counts.technician}.', 'Part: {col:stock_counts.part}. Expected {col:stock_counts.expected}, counted {col:stock_counts.counted}, variance {col:stock_counts.variance}, variance value {col:stock_counts.variance_value}.',
        'Count check: {col:stock_counts.flag}. The recount and the reason are written below.'], SG, NOTE),
    DOC('vehicle_report_doc', 'Vehicle Cost Report', 'Vehicle cost report for one van', 'vehicle_van.row_id', [
        'Vehicle cost report of {set:company}, dated {today}. Van {col:vehicle_van.van}, technician {col:vehicle_van.technician}.', 'Total cost in the period: {col:vehicle_van.total}. Working days: {col:vehicle_van.working_days}. Jobs: {col:vehicle_van.jobs}. Cost per working day: {col:vehicle_van.per_day}. Cost per job: {col:vehicle_van.per_job}.',
        'Shop cost per working day: {col:vehicle_van.shop_per_day}. Cost check: {col:vehicle_van.status}.', 'Notes on fuel, repairs and tyres are written below.'], ['Owner', 'Accountant'], NOTE),
    DOC('van_summary_doc', 'Van Decision Summary', 'Keep, replace or add a van summary', 'vehicle_van.row_id', [
        'Van decision summary of {set:company}, dated {today}. Van {col:vehicle_van.van}, technician {col:vehicle_van.technician}.', 'Running cost, last 12 months: {col:vehicle_van.cost_12m}. Repairs, last 12 months: {col:vehicle_van.repairs_12m}. Cost per working day: {col:vehicle_van.per_day}, against {col:vehicle_van.shop_per_day} for the shop.',
        'Jobs booked next week: {col:vehicle_van.jobs_next_week}. Service due: {col:vehicle_van.service_due}. Use the Keep Replace or Add a Van tool for the verdict and write the decision below.'], ['Owner'], NOTE),
    DOC('tool_register_doc', 'Tool Register', 'Tool and equipment register entry', 'tools.tool_id', [
        'Tool and equipment register of {set:company}, dated {today}. Tool {col:tools.tool_id}.', 'Item: {col:tools.item}. Description: {col:tools.description}. Bought on {col:tools.date} for {col:tools.cost}. Assigned to {col:tools.technician}.',
        'Life: {col:tools.life_years} years. Replacement year: {col:tools.due_year}. Tool check: {col:tools.check}.', 'The serial number and where the tool is kept are written below.'], SG, NOTE),
    DOC('tool_budget_doc', 'Tool Replacement Budget Sheet', 'Tool replacement budget for one year', 'tool_plan.year', [
        'Tool replacement budget of {set:company}, dated {today}. Year {col:tool_plan.year}.', 'Tools due: {col:tool_plan.items_due}. Budget at today cost: {col:tool_plan.budget}. Budget with your price rise: {col:tool_plan.budget_rise}.',
        'The tools to buy and the month to set money aside are written below.'], ['Owner'], NOTE),
    DOC('van_checklist_doc', 'Van Checklist Print', 'Van checklist for stock, tools and paperwork', 'vans.van', [
        'Van checklist of {set:company}, dated {today}. Van {col:vans.van}, technician {col:vans.technician}.', 'Stock: parts at or above the minimum on the van sheet, restock list handed to the office. Tools: every tool on the register is on the van. Paperwork: van papers and work orders are in the van.',
        'Each tick and the date are written below.'], SG, NOTE),
    DOC('shrink_review_doc', 'Shrink Review', 'Shrink review for the owner meeting', 'shrink_van.row_id', [
        'Shrink review of {set:company}, dated {today}. Van {col:shrink_van.van}, technician {col:shrink_van.technician}, period {col:shrink_van.period}.', 'Stock missing: {col:shrink_van.missing}. Van stock value: {col:shrink_van.stock_value}. Shrink share: {col:shrink_van.share}. A count month: {col:shrink_van.per_month}. Shrink check: {col:shrink_van.status}.',
        'Parts below minimum: {col:shrink_van.below_lines}. Last count: {col:shrink_van.last_count}. The cause and the action agreed are written below.'], ['Owner', 'Technician'], NOTE),
]
assert len(documents) == 12
checklists = [
    CHK('van_count', 'Van Stock Count', 'stock_counts', 'stock_counts.date', [('Park the van and open the van stock sheet', 0), ('Count every tracked part line', 0), ('Write the counted quantity next to the expected one', 0), ('Mark lines missing more than your tolerance', 0), ('Hand the sheet to the office the same day', 0), ('Office enters the count and checks the variance', 1)]),
    CHK('restock_run', 'Restock Run', 'restocks', 'restocks.date', [('Print the restock list', 0), ('Order from your parts counter and your equipment supplier', 0), ('Pick up the order and check it against the list', 1), ('Load the van and tick each line', 1), ('Enter the restock on the Restocks sheet', 1), ('File the supplier invoice', 2)]),
    CHK('parts_on_job', 'Parts Entered on the Job', 'parts_used', 'parts_used.date', [('Write each part used on the work order', 0), ('Enter the parts on the Parts Used sheet', 1), ('Mark parts taken from the van', 1), ('Check that every part is billed', 2), ('Chase any unbilled part with the office', 3)]),
    CHK('parts_return', 'Parts Return', 'restocks', 'restocks.date', [('Check the part is unused and in its pack', 1), ('Write the return on the Parts Return Sheet', 1), ('Take the part back to your parts counter', 3), ('Ask for a credit note', 3), ('Match the credit to the supplier invoice', 14)]),
    CHK('price_change_in', 'Supplier Price Change Received', 'price_changes', 'price_changes.date', [('Write the change on the Supplier Price Changes sheet', 0), ('Check the Price Change Margin Impact tool', 1), ('Update the price-book lines that fell under target', 3), ('Check the open estimates', 3), ('Tell the technicians about the new prices', 5)]),
    CHK('weekly_order', 'Weekly Parts Counter Order', 'purchases', 'purchases.date', [('Open the restock list on Monday', 0), ('Add parts for the jobs booked this week', 0), ('Send the order to your parts counter', 0), ('Confirm the pick-up time', 1), ('Check the delivery against the order', 2), ('File the invoice and note the due date', 2)]),
    CHK('vehicle_week', 'Vehicle Weekly Check', 'vehicle_costs', 'vehicle_costs.month', [('Check fuel level and tyres on each van', 0), ('Check the van papers are inside', 0), ('Note any damage or noise', 0), ('Log the week on the Vehicle Costs sheet', 4)]),
    CHK('vehicle_service', 'Vehicle Service Due', 'vehicle_van', 'vehicle_van.service_due', [('Book the garage', -21), ('Plan which jobs move for the day', -14), ('Tell the technician the date', -7), ('Take the van in', 0), ('Enter the cost on the Vehicle Costs sheet', 1), ('Set the next service date', 1)]),
    CHK('vehicle_review', 'Monthly Vehicle Cost Review', 'vehicle_costs', 'vehicle_costs.month', [('Enter fuel, repairs and tyres for each van', 2), ('Check cost per working day against your budget', 3), ('Compare each van with the shop average', 3), ('Open the Keep Replace or Add a Van tool for the highest van', 4), ('Note the decision in the owner meeting', 7)]),
    CHK('tool_approval', 'Tool Purchase Approval', 'tools', 'tools.date', [('Write the request with the cost and the life in years', 0), ('Check the budget in the Tool Replacement Plan', 1), ('Owner approves or waits', 2), ('Buy the tool and keep the receipt', 3), ('Enter it on the Tools and Equipment sheet', 3), ('Assign it to a technician', 4)]),
    CHK('tool_review', 'Yearly Tool Review', 'tools', 'tools.date', [('Open the Tool Purchase Log tool', 0), ('Check which tools are past their life', 1), ('Set the budget for next year', 3), ('Plan the purchases before the season', 7), ('Retire the tools you replace', 14)]),
    CHK('shrink_check', 'Shrink Investigation', 'shrink_van', 'shrink_van.to_date', [('Open the Shrink by Van sheet', 1), ('Recount the parts with the largest gaps', 2), ('Check parts used and billed on the van', 3), ('Talk to the technician with the office manager', 5), ('Agree an action and a date', 7), ('Count the van again', 30)]),
]
assert len(checklists) == 12
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('t_count', 'Technician: please count your van', 'shrink_van', 'shrink_van.tech_phone', 'Hello {technician}, please count {van} by {next_count}. {company}'),
    M('t_below', 'Technician: parts below minimum', 'shrink_van', 'shrink_van.tech_phone', 'Hello {technician}, {van} is below minimum on {below_lines} parts. Please check the restock list. {company}'),
    M('t_ready', 'Technician: your restock is ready', 'shrink_van', 'shrink_van.tech_phone', 'Hello {technician}, the restock for {van} is ready at the yard: {below_lines} parts. {company}'),
    M('t_enter', 'Technician: please enter parts used', 'parts_used', 'parts_used.tech_phone', 'Hello {technician}, please confirm the parts used on {job_id}: {part}, quantity {qty}. {company}'),
    M('t_unbilled', 'Technician: parts were not billed', 'unbilled', 'unbilled.tech_phone', 'Hello {technician}, {part} on {job_id} was not billed, cost {cost}. Please tell the office. {company}'),
    M('t_service', 'Technician: your van service date', 'vehicle_van', 'vehicle_van.tech_phone', 'Hello {technician}, the service for {van} is on {service_due}. {company}'),
    M('t_paper', 'Technician: check the van paperwork', 'vehicle_van', 'vehicle_van.tech_phone', 'Hello {technician}, please check the paperwork in {van} this week. {company}'),
    M('t_tool', 'Technician: your new tool is assigned', 'tools', 'tools.tech_phone', 'Hello {technician}, {item} is now assigned to you. {company}'),
    M('t_shrink', 'Technician: shrink on your van', 'shrink_van', 'shrink_van.tech_phone', 'Hello {technician}, stock missing on {van} is {missing}. Please review it with the office. {company}'),
    M('t_recount', 'Technician: a variance needs a recount', 'stock_counts', 'stock_counts.tech_phone', 'Hello {technician}, the count of {part} on {van} on {date} shows variance {variance}. Please recount. {company}'),
    M('a_restock', 'Apprentice: please help restock a van', 'shrink_van', 'shrink_van.amira_phone', 'Hello, please help restock {van} today: {below_lines} parts are below minimum. {company}'),
    M('a_count', 'Apprentice: you count the stock', 'shrink_van', 'shrink_van.liam_phone', 'Hello, you count the stock on {van} by {next_count}. {company}'),
    M('om_run', 'Office manager: morning run restock', 'supplier_runs', 'supplier_runs.office_phone', 'Restock for the morning run: {lines} lines for {van} from {supplier}, total {total}. {company}'),
    M('om_total', 'Office manager: parts counter total', 'supplier_runs', 'supplier_runs.office_phone', 'The order for {supplier} on {van} is {total} for {units} units. {company}'),
    M('om_unbilled', 'Office manager: unbilled parts', 'unbilled', 'unbilled.office_phone', 'Unbilled parts on {job_id}: {part}, {cost}, week of {week}. Please add it to the invoice. {company}'),
    M('om_service', 'Office manager: vans due for service', 'vehicle_van', 'vehicle_van.office_phone', '{van} is due for service on {service_due}. Please book the day. {company}'),
    M('om_price', 'Office manager: update the price book', 'price_changes', 'price_changes.office_phone', 'Price change on {part} from {old_cost} to {new_cost}. Please update the price book. {company}'),
    M('ow_below', 'Owner: a van is below minimum', 'shrink_van', 'shrink_van.owner_phone', '{van} stock is below minimum on {below_lines} parts. Restock cost {restock_cost}. {company}'),
    M('ow_shrink', 'Owner: shrink on a van', 'shrink_van', 'shrink_van.owner_phone', 'Shrink on {van} is {missing}, {share} of its stock value. {company}'),
    M('ow_cost', 'Owner: the cost of running a van', 'vehicle_van', 'vehicle_van.owner_phone', 'The cost of running {van} is {per_day} per working day. {company}'),
    M('ow_keep', 'Owner: keep or replace a van', 'vehicle_van', 'vehicle_van.owner_phone', 'Keep or replace {van}: repairs {repairs_12m} in 12 months. See the Keep Replace or Add a Van tool. {company}'),
    M('ow_changes', 'Owner: supplier price changes', 'stock_month', 'stock_month.owner_phone', 'Supplier price changes in the month of {month}: {changes}. {company}'),
    M('ow_tools', 'Owner: tools due for replacement', 'tool_plan', 'tool_plan.owner_phone', 'Tools due for replacement in {year}: {items_due}, budget {budget}. {company}'),
    M('pc_confirm', 'Parts counter: please confirm the order', 'purchases', 'purchases.parts_phone', 'Hello, please confirm order {po_id}, amount {amount}, due {due_date}. {company}'),
    M('pc_prices', 'Parts counter: send the new price list', 'price_changes', 'price_changes.parts_phone', 'Hello, the cost of {part} changed on {date}. Please send your new price list. {company}'),
    M('pc_short', 'Parts counter: we are short, hold some', 'restock_list', 'restock_list.parts_phone', 'Hello, we are short on {part}, {qty} needed for {van}. Can you hold some for us? {company}'),
    M('pc_invoice', 'Parts counter: check the invoice total', 'purchases', 'purchases.parts_phone', 'Hello, please check invoice {po_id}: the total we hold is {amount}. {company}'),
    M('es_price', 'Equipment supplier: confirm the price', 'price_changes', 'price_changes.supplier_phone', 'Hello, please confirm the price for {part}: new cost {new_cost}. {company}'),
    M('el_materials', 'Electrical sub: send a materials list', 'purchases', 'purchases.elec_phone', 'Hello, please send the materials list for job {job_id}, order {po_id}. {company}'),
    M('sm_delivery', 'Sheet-metal sub: confirm delivery', 'purchases', 'purchases.sheet_phone', 'Hello, please confirm the delivery date for order {po_id}, due {due_date}. {company}'),
    M('ac_vehicle', 'Accountant: vehicle costs', 'vehicle_costs', 'vehicle_costs.acct_phone', 'Vehicle costs for {van} in the month of {month}: {total}. Please add them to the books. {company}'),
    M('ins_list', 'Insurance agent: vehicle list', 'vehicle_van', 'vehicle_van.ins_phone', 'Hello, for the vehicle list: {van}, driven by {technician}, running cost {cost_12m} in 12 months. {company}'),
    M('ow_unbilled', 'Owner: unbilled parts this month', 'stock_month', 'stock_month.owner_phone', 'Unbilled parts in the month of {month}: {unbilled_cost}. {company}'),
    M('pc_standing', 'Parts counter: standing season order', 'supplier_runs', 'supplier_runs.parts_phone', 'Hello, standing order for the season: {lines} lines for {van}, about {total}. {company}'),
]
assert len(messages) == 34, len(messages)

def PW(n=30): return '{range:parts_used.date},">="&({today}-%d),{range:parts_used.date},"<="&{today}' % n
M3 = '{range:stock_month.month},">="&EDATE(%s,-3),{range:stock_month.month},"<"&%s' % (MS, MS)
M12 = '{range:vehicle_costs.month},">="&EDATE(%s,-12),{range:vehicle_costs.month},"<"&%s' % (MS, MS)
kpis = [
    KPI('Stock value across all vans', 'SUM({range:van_stock.value})', 'money'),
    KPI('Stock value of the lowest van', 'MIN({range:shrink_van.stock_value})', 'money'),
    KPI('Parts below minimum today', 'COUNTIFS({range:van_stock.below_min},%s)' % BELOW, 'int'),
    KPI('Vans with parts below minimum', 'COUNTIFS({range:shrink_van.period},%s,{range:shrink_van.below_lines},">0")' % LAST6, 'int'),
    KPI('Restock cost for the next run', 'SUM({range:van_stock.restock_cost})', 'money'),
    KPI('Parts used, last 30 days', 'SUMIFS({range:parts_used.qty},%s)' % PW(), 'int'),
    KPI('Parts cost, last 30 days', 'SUMIFS({range:parts_used.cost},%s)' % PW(), 'money'),
    KPI('Parts cost share of revenue, 3 months', 'IFERROR(SUMIFS({range:stock_month.parts_cost},%s)/SUMIFS({range:stock_month.revenue},%s),0)' % (M3, M3), 'pct'),
    KPI('Unbilled parts, last 30 days', 'SUMIFS({range:parts_used.cost},{range:parts_used.from_van},%s,{range:parts_used.billed},%s,%s)' % (YES, NO, PW()), 'money'),
    KPI('Unbilled parts, last 12 months', 'SUMIFS({range:stock_month.unbilled_cost},{range:stock_month.month},">="&EDATE(%s,-12))' % MS, 'money'),
    KPI('Stock missing at the last count', 'SUMIFS({range:stock_counts.missing_value},{range:stock_counts.date},MAX({range:stock_counts.date}))', 'money'),
    KPI('Shrink, last 6 counts', 'SUMIFS({range:shrink_van.missing},{range:shrink_van.period},%s)' % LAST6, 'money'),
    KPI('Shrink share of van stock value', 'IFERROR(SUMIFS({range:shrink_van.missing},{range:shrink_van.period},%s)/SUM({range:van_stock.value}),0)' % LAST6, 'pct'),
    KPI('Van with the most shrink', 'IFERROR(INDEX({range:shrink_van.van},MATCH(MAX({range:shrink_van.last_missing}),{range:shrink_van.last_missing},0)),"")', 'text'),
    KPI('Part lines counted, last 90 days', 'COUNTIFS({range:stock_counts.date},">="&({today}-90),{range:stock_counts.date},"<="&{today})', 'int'),
    KPI('Vans not counted in time', 'COUNTIFS({range:shrink_van.period},%s,{range:shrink_van.on_time},%s)' % (LAST6, ck('Count overdue')), 'int'),
    KPI('Supplier price changes, last 12 months', 'COUNTIFS({range:price_changes.date},">="&({today}-365))', 'int'),
    KPI('Average parts cost rise, 12 months', 'IFERROR(SUM({range:parts.year_spend})/SUM({range:parts.spend_old})-1,0)', 'pct'),
    KPI('Price-book lines hit by price changes', 'COUNTIFS({range:price_book.status},%s)+COUNTIFS({range:price_book.status},%s)' % (UNDER, ROSE), 'int'),
    KPI('Money at risk a year from price changes', 'SUM({range:price_book.at_risk})', 'money'),
    KPI('Vehicle cost this month, month to date', 'SUMIFS({range:vehicle_costs.total},{range:vehicle_costs.month},%s)' % MS, 'money'),
    KPI('Vehicle cost per day, last 3 months', 'IFERROR(SUMIFS({range:vehicle_van.total},{range:vehicle_van.period},%s)/SUMIFS({range:vehicle_van.working_days},{range:vehicle_van.period},%s),0)' % (LAST3, LAST3), 'money'),
    KPI('Vehicle cost per job, last 3 months', 'IFERROR(SUMIFS({range:vehicle_van.total},{range:vehicle_van.period},%s)/SUMIFS({range:vehicle_van.jobs},{range:vehicle_van.period},%s),0)' % (LAST3, LAST3), 'money'),
    KPI('Vehicle cost per hour on the road', 'IFERROR(SUMIFS({range:vehicle_costs.total},%s)/(SUMIFS({range:vehicle_costs.working_days},%s)*{set:road_hours_day}),0)' % (M12, M12), 'money'),
    KPI('Highest cost van per working day', 'IFERROR(INDEX({range:vehicle_van.van},MATCH(MAX({range:vehicle_van.per_day_last}),{range:vehicle_van.per_day_last},0)),"")', 'text'),
    KPI('Vans due for service, next 30 days', 'COUNTIFS({range:vehicle_van.period},%s,{range:vehicle_van.service_due},">="&{today},{range:vehicle_van.service_due},"<="&({today}+30))' % LAST3, 'int'),
    KPI('Tools bought this year', 'COUNTIFS({range:tools.date},">="&DATE(YEAR({today}),1,1))', 'int'),
    KPI('Tool spend this year', 'SUMIFS({range:tools.cost},{range:tools.date},">="&DATE(YEAR({today}),1,1))', 'money'),
    KPI('Tools past replacement age', 'COUNTIFS({range:tools.over_life},">=0")', 'int'),
    KPI('Tool budget next year', 'SUMIFS({range:tool_plan.budget},{range:tool_plan.year},YEAR({today})+1)', 'money'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Parts and Van Dashboard", "kpis": kpis,
    "monthly": {"title": "Parts cost, restock cost and unbilled parts by month", "date": "stock_month.month", "series": [
        {"label": "Parts cost", "sum": "stock_month.parts_cost", "date": "stock_month.month"}, {"label": "Restock cost", "sum": "stock_month.restock_cost", "date": "stock_month.month"},
        {"label": "Unbilled parts", "sum": "stock_month.unbilled_cost", "date": "stock_month.month"}]},
    "breakdowns": [{"title": "Parts cost by category", "by": "parts_used.category", "value": "parts_used.cost", "agg": "sum"}, {"title": "Stock value by van", "by": "van_stock.van", "value": "van_stock.value", "agg": "sum"},
                   {"title": "Vehicle cost by van", "by": "vehicle_costs.van", "value": "vehicle_costs.total", "agg": "sum"}, {"title": "Purchases by supplier", "by": "purchases.supplier", "value": "purchases.amount", "agg": "sum"}]}
def CM(title, typ, tbl, col, date, label, agg='sum'): return CHART(title, typ, 'month', [AGG(agg, tbl, '%s.%s' % (tbl, col), date='%s.%s' % (tbl, date), label=label)])
def CB(title, tbl, by, col, label, agg='sum', where=None): return CHART(title, 'bar', '%s.%s' % (tbl, by), [AGG(agg, tbl, '%s.%s' % (tbl, col) if col else None, where=where, label=label)])
insights = {"filters": [{"label": "Technician", "list": "tech"}, {"label": "Van", "list": "van"}, {"label": "Part category", "list": "partcat"}],
    "gauges": [{"title": "Parts at or above minimum", "num": AGG('count', 'van_stock', where=[('below_min', '<>', BELOW)]), "den": AGG('count', 'van_stock')},
               {"title": "Vans counted on time", "num": AGG('count', 'shrink_van', where=[('period', '=', LAST6), ('on_time', '=', ck('Counted on time'))]), "den": AGG('count', 'shrink_van', where=[('period', '=', LAST6)])},
               {"title": "Parts billed to jobs", "num": AGG('count', 'parts_used', where=[('from_van', '=', YES), ('billed', '=', YES)]), "den": AGG('count', 'parts_used', where=[('from_van', '=', YES)])},
               {"title": "Count lines within tolerance", "num": AGG('count', 'stock_counts', where=[('missing_value', '<=', '{set:count_tolerance}')]), "den": AGG('count', 'stock_counts')},
               {"title": "Price-book lines on target", "num": AGG('count', 'price_book', where=[('status', '<>', UNDER)]), "den": AGG('count', 'price_book')},
               {"title": "Vehicle cost within budget", "num": AGG('count', 'vehicle_costs', where=[('per_day', '<=', '{set:vehicle_budget_day}')]), "den": AGG('count', 'vehicle_costs')}],
    "charts": [
        CM('Parts cost per month', 'column', 'stock_month', 'parts_cost', 'month', 'Parts cost'), CB('Parts used by category', 'parts_used', 'category', 'cost', 'Parts cost'), CB('Parts cost by van', 'parts_used', 'van', 'cost', 'Parts cost'),
        CB('Parts cost by technician', 'parts_used', 'technician', 'cost', 'Parts cost'), CB('Stock value by van', 'van_stock', 'van', 'value', 'Stock value'), CM('Stock value per month', 'line', 'stock_month', 'stock_value', 'month', 'Stock value'),
        CB('Parts below minimum by van', 'van_stock', 'van', None, 'Parts below minimum', 'count', [('below_min', '=', BELOW)]), CB('Shrink by van, last 6 counts', 'shrink_van', 'van', 'last_missing', 'Stock missing'),
        CM('Stock missing per count month', 'column', 'stock_counts', 'missing_value', 'date', 'Stock missing'), CM('Restock cost per month', 'column', 'stock_month', 'restock_cost', 'month', 'Restock cost'),
        CB('Purchases by supplier', 'purchases', 'supplier', 'amount', 'Purchases'), CM('Unbilled parts per month', 'column', 'stock_month', 'unbilled_cost', 'month', 'Unbilled parts'),
        CHART('Supplier price changes per month', 'column', 'month', [AGG('count', 'price_changes', date='price_changes.date', label='Price changes')]), CB('Average rise by category', 'price_changes', 'category', 'rise', 'Average rise', 'avg'),
        CM('Purchases per month', 'column', 'purchases', 'amount', 'date', 'Purchases'), CM('Vehicle cost per month', 'column', 'vehicle_costs', 'total', 'month', 'Vehicle cost'),
        CB('Vehicle cost by van', 'vehicle_costs', 'van', 'total', 'Vehicle cost'), CM('Fuel per month', 'line', 'vehicle_costs', 'fuel', 'month', 'Fuel'), CM('Repairs per month', 'column', 'vehicle_costs', 'repairs', 'month', 'Repairs'),
        CB('Cost per working day by van', 'vehicle_van', 'van', 'per_day_last', 'Cost per working day'), CM('Tool spend per month', 'column', 'tools', 'cost', 'date', 'Tool spend'), CB('Tools by replacement year', 'tools', 'replace_year', None, 'Tools', 'count')]}
assert len(insights['charts']) == 22
signature = [
    {"name": "Van Stock Restock List", "why": "the parts below minimum on every van with the quantity to reach the maximum, the supplier run total and an order-today or next-run verdict", "where": "Van Stock Restock List"},
    {"name": "Stock Count Variance", "why": "expected against counted by van and part, the four largest gaps in money and a recount, investigate or fine verdict against your tolerance", "where": "Stock Count Variance"},
    {"name": "Short-Stock Van Finder", "why": "the vans short of parts and the jobs booked next week that depend on them, with the supplier run to fix it", "where": "Short-Stock Van Finder"},
    {"name": "Price Change Margin Impact", "why": "price-book lines and open estimates that fell under your margin after a supplier price rise, ranked by money at risk with the flat price that restores it", "where": "Price Change Margin Impact"},
    {"name": "Unbilled Parts Finder", "why": "parts that left a van and never reached an invoice, by technician and week, with the money leaked a week and a bill-now verdict", "where": "Unbilled Parts Finder"},
    {"name": "Keep Replace or Add a Van", "why": "the yearly cost of keeping a van against replacing it and the jobs a day an added van needs to pay for itself, with a clear verdict", "where": "Keep Replace or Add a Van"},
    {"name": "Stock-Up Before the Season", "why": "the stock to hold on each van before the heating or cooling season from your own history, the top-up cost and the supplier run date", "where": "Stock-Up Before the Season"},
    {"name": "Shrink by Van and Tech", "why": "stock missing between counts ranked by van and driver against the shop average, with the cost a month and a watch or investigate verdict", "where": "Shrink by Van and Tech"},
    {"name": "Parts Usage Forecast", "why": "the parts to hold on a van next season from last 12 months and a seasonal index, with Base, Best and Worst rows", "where": "Parts Usage Forecast"},
    {"name": "Parts Markup Check", "why": "the markup you earn by category against your target, the lines under it ranked by yearly spend and what the target would add", "where": "Parts Markup Check"}]
competitors = [
    {"what": "field-service app with a per-technician fee", "lacks": "charges every month for each person, tracks stock only as a count and has no shrink by van, no unbilled parts finder and no price-book check"},
    {"what": "generic inventory template", "lacks": "lists items and quantities but has no van minimum and maximum, no supplier run total and no link from parts used to the jobs they were billed on"},
    {"what": "single-sheet quote calculator", "lacks": "prices one job but never learns that your parts cost rose, so margin quietly falls on lines you quoted last season"},
    {"what": "pen-and-paper van log", "lacks": "keeps no history, so missing stock, vehicle cost per working day and tools past their life never show up"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: days between counts, count tolerance, shrink target, markup wanted, vehicle budget a day and the price rise to test on tools.',
    'Check Technicians and Vans. They hold your people, vans and the lease cost a month that the other sheets look up.',
    'List the parts you carry on each van on Van Stock with a minimum, a maximum and the quantity on hand. The below-minimum check, the quantity to reach the maximum and the restock cost fill in by themselves.',
    'Count each van and write the expected and counted quantity on Stock Counts. The variance, the missing value and the recount flag calculate themselves; Shrink by Van adds up the stock missing between counts.',
    'Write each restock on Restocks and each part used on a job on Parts Used with whether it left the van and whether it was billed. Unbilled Parts ranks what is still to bill.',
    'Keep Parts, Supplier Price Changes and Price Book up to date. Price Change Margin Impact then shows the lines and open estimates that fell under your margin.',
    'Enter the vehicle costs of each van every month on Vehicle Costs. Vehicle Cost by Van shows the cost per working day and per job against the shop and the service dates.',
    'Log every tool and piece of equipment you buy on Tools and Equipment with its life in years. The Tool Replacement Plan shows the budget for each year.',
    f'Use the {len(tools)} tools: each answers one question with a verdict. Change the yellow inputs to try another van, category, season or price.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Parts and Van Dashboard and the Charts every week. A one-person owner-operator with one van uses the same sheets with one row in Vans; a shop with several vans uses every row.']
listing = {"title": "HVAC and Plumbing Contractor Excel Template: Van Stock, Parts Used, Unbilled Parts, Price Changes, Vehicle Cost, Tool Budget",
    "headline": "What is on every van, what it costs to run and which parts were never billed",
    "tags": ["hvac template", "plumbing template", "van stock", "inventory excel", "parts tracker", "vehicle cost", "contractor excel", "service business", "price book", "tool budget", "field service", "tradesman", "stock count"],
    "description": ("Run the parts and vehicles of an HVAC and plumbing contractor business in one Excel workbook. Built for an owner-run residential and light-commercial service shop with 1 to 15 technicians and a van for each lead technician. "
        "A one-person owner-operator with one van uses the same sheets with one row; a shop with several vans uses every row.\n\n"
        "Van Stock holds every part on every van with a minimum, a maximum and the quantity on hand, and works out the parts below minimum, the quantity to reach the maximum and the cost of the next supplier run. Stock Counts compares expected with counted, and Shrink by Van adds up the stock missing between counts for each van and driver. "
        "Parts Used links every part to a job and shows which parts left a van and were never billed. Supplier Price Changes and the Price Book show which flat-price lines and open estimates fell under your margin after a supplier raised a cost, ranked by money at risk.\n\n"
        f"Vehicle Costs tracks fuel, repairs, tyres, lease and insurance by van and month, with the cost per working day and per job against the shop average and the service dates. Tools and Equipment logs every purchase with its life and builds a replacement budget for each year. {len(tools)} tools answer weekly questions with a clear verdict: restock list, count variance, shrink, stock turnover, short-stock vans, price change impact, markup check, unbilled parts, usage forecast, vehicle cost, keep or replace a van and stock-up before the season. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to technicians, apprentices, the office, your parts counter, your equipment supplier, the accountant and the insurance agent.\n\n"
        "This is part five of the HVAC and Plumbing Contractor suite. A standard .xlsx workbook with no macros and no per-technician fee: you keep your data. A demo copy full of sample data and a blank copy are included. It helps you keep track of your business and does not promise results."),
    "features": ["Van stock with minimum, maximum and automatic restock list", "Stock count variance and shrink by van", "Unbilled parts finder by technician and week", "Supplier price change log with price-book impact",
                 "Markup check by part category", "Vehicle cost per working day and per job", "Keep, replace or add a van decision", "Tool purchase log with a five-year replacement budget",
                 "Stock-up planner before the heating and cooling season", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
for _l in ('Spare label',):
    if len(CKL) % 30 == 1: ck(_l)
s = spec(id=f'{SUITE}-p5', slug='hvac-plumbing-parts-vans', profession='HVAC and Plumbing Contractor', name='Parts, Van Stock and Vehicles',
         tagline='What is on every van, what it costs to run and which parts were never billed', price_usd=29,
         colors={"primary": "#1F4E5F", "accent": "#E07A3F"}, settings=settings, lists=base_lists + ck_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Parts, van stock and vehicles"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hv5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']))
