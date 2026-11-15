"""Short-term rental host suite - part 4: Turnovers, Cleaners and Supplies."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr4_lists import *
from sr4_tables import settings, tables
from sr4_tools import tools

SUITE = 'fx-20261113-short-term-rental'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
forms = [
    FORM('turnover_sheet', 'Turnover Sheet', 'Turnover with cleaner, hours and time check', 'turnovers.turnover_id', F(
        ('Date', 'turnovers.date'), ('Unit', 'turnovers.unit'), ('Booking', 'turnovers.booking_id'), ('Next check-in', 'turnovers.next_check_in'), ('Same-day turn', 'turnovers.same_day'), ('Cleaner', 'turnovers.cleaner'), ('Hours', 'turnovers.hours'),
        ('Pay', 'turnovers.pay'), ('Linen sets', 'turnovers.linen_sets'), ('Hours to the next check-in', 'turnovers.window_hours'), ('Time check', 'turnovers.tight_flag'), ('Turnovers that day', 'turnovers.day_turns'), ('Cleaner phone', 'turnovers.cleaner_phone'))),
    FORM('inspection_sheet', 'Inspection Sheet', 'Inspection with score and issues found', 'inspections.check_id', F(
        ('Date', 'inspections.date'), ('Unit', 'inspections.unit'), ('Turnover', 'inspections.turnover_id'), ('Cleaner', 'inspections.cleaner'), ('Inspector', 'inspections.inspector'), ('Score', 'inspections.score'), ('Issues found', 'inspections.issues_found'),
        ('Result', 'inspections.pass_flag')) + [FF('Inspections of this unit', 'COUNTIFS({range:inspections.unit},INDEX({range:inspections.unit},MATCH({pick},{range:inspections.check_id},0)))', 'int'),
        FF('Average score of all inspections', 'AVERAGE({range:inspections.score})', 'num')]),
    FORM('redo_sheet', 'Redo Request Sheet', 'Redo request with reason, hours and cost', 'redo.redo_id', F(
        ('Date', 'redo.date'), ('Unit', 'redo.unit'), ('Cleaner', 'redo.cleaner'), ('Hours lost', 'redo.hours_lost'), ('Refund or discount', 'redo.discount_given'), ('Cost of the redo', 'redo.cost'), ('Cleaner phone', 'redo.cleaner_phone')) + [
        FF('Redo jobs on this unit', 'COUNTIFS({range:redo.unit},INDEX({range:redo.unit},MATCH({pick},{range:redo.redo_id},0)))', 'int'), FF('Cost of all redo jobs', 'SUM({range:redo.cost})', 'money')]),
    FORM('order_sheet', 'Supplies Order Sheet', 'Supplies order with amount and delivery date', 'supplier_orders.order_id', F(
        ('Date', 'supplier_orders.date'), ('Items', 'supplier_orders.items'), ('Amount', 'supplier_orders.amount'), ('Delivery date', 'supplier_orders.delivery_date'), ('Days to delivery', 'supplier_orders.lead_days'), ('Delivery check', 'supplier_orders.order_flag'),
        ('Supplier phone', 'supplier_orders.supplier_phone'))),
    FORM('stock_sheet', 'Stock Count Sheet', 'Stock count of one item with quantity to order', 'supply_stock.item', F(
        ('Category', 'supply_stock.category'), ('On hand', 'supply_stock.on_hand'), ('Reorder point', 'supply_stock.reorder_point'), ('Par level', 'supply_stock.par_level'), ('Unit cost', 'supply_stock.unit_cost'), ('Last bought', 'supply_stock.last_bought'),
        ('Used a month', 'supply_stock.monthly_use'), ('Stock status', 'supply_stock.status'), ('Days of cover', 'supply_stock.days_cover'), ('Quantity to order', 'supply_stock.qty_to_order'), ('Cost of the order', 'supply_stock.order_value'), ('Order by', 'supply_stock.order_by'))),
    FORM('pay_sheet', 'Cleaner Pay Sheet', 'Cleaner pay for a month', 'cleaner_pay.pay_id', F(
        ('Month', 'cleaner_pay.month'), ('Cleaner', 'cleaner_pay.cleaner'), ('Turnovers', 'cleaner_pay.turnovers'), ('Hours', 'cleaner_pay.hours'), ('Amount', 'cleaner_pay.amount'), ('Paid on', 'cleaner_pay.paid_on'), ('Pay per turnover', 'cleaner_pay.pay_per_turnover'),
        ('Pay per hour', 'cleaner_pay.pay_per_hour'), ('Cleaner phone', 'cleaner_pay.cleaner_phone'))),
    FORM('linen_sheet', 'Linen Count Sheet', 'Linen count of one unit for a month', 'linen.linen_id', F(
        ('Month', 'linen.month'), ('Unit', 'linen.unit'), ('Sets in use', 'linen.sets_in_use'), ('Sets washed', 'linen.sets_washed'), ('Sets damaged', 'linen.sets_damaged'), ('Sets bought', 'linen.sets_bought'), ('Counted by', 'linen.counted_by'),
        ('Loss share', 'linen.loss_pct'), ('Loss check', 'linen.loss_flag'))),
    FORM('laundry_sheet', 'Laundry Run Sheet', 'Laundry run with loads and cost per load', 'laundry.run_id', F(
        ('Date', 'laundry.date'), ('Who', 'laundry.who'), ('Loads', 'laundry.loads'), ('Cost', 'laundry.cost'), ('Cost per load', 'laundry.cost_per_load')) + [
        FF('Average cost per load, all runs', 'SUM({range:laundry.cost})/SUM({range:laundry.loads})', 'money'), FF('Runs logged', 'COUNTA({range:laundry.run_id})', 'int')]),
    FORM('deep_sheet', 'Deep Clean Sheet', 'Deep clean with hours, cost and reason', 'deep_cleans.dc_id', F(
        ('Unit', 'deep_cleans.unit'), ('Date', 'deep_cleans.date'), ('Cleaner', 'deep_cleans.cleaner'), ('Hours', 'deep_cleans.hours'), ('Cost', 'deep_cleans.cost'), ('Cost per hour', 'deep_cleans.cost_per_hour'), ('Days to the date', 'deep_cleans.days_to'))),
    FORM('lost_sheet', 'Lost and Found Sheet', 'Lost item with guest, status and days open', 'lost_found.lf_id', F(
        ('Date found', 'lost_found.date'), ('Unit', 'lost_found.unit'), ('Item', 'lost_found.item'), ('Guest', 'lost_found.guest'), ('Returned on', 'lost_found.returned_on'), ('Days open', 'lost_found.days_open'), ('Follow-up check', 'lost_found.open_flag'))),
]
assert len(forms) == 10
documents = [
    DOC('day_schedule', 'Daily Turnover Schedule', 'Daily turnover schedule for one turnover and its day', 'turnovers.turnover_id', [
        'Daily turnover schedule of {set:company}, dated {today}. Turnover {col:turnovers.turnover_id} on {col:turnovers.date} at {col:turnovers.unit} ({col:turnovers.city}).',
        'Cleaner: {col:turnovers.cleaner}. Expected time: {col:turnovers.hours} hours. Linen sets: {col:turnovers.linen_sets}. Booking {col:turnovers.booking_id}; next check-in {col:turnovers.next_check_in}.',
        'Hours to the next check-in: {col:turnovers.window_hours}. Time check: {col:turnovers.tight_flag}. Cleaner check: {col:turnovers.assign_flag}. Turnovers planned that day: {col:turnovers.day_turns}.',
        'A turnover is the clean and reset between two stays. Tell the host at once if a unit cannot be ready for check-in.'], ['Host', 'Cleaner'], NOTE),
    DOC('job_sheet', 'Cleaner Job Sheet', 'Cleaner job sheet for one day', 'availability.avail_id', [
        'Cleaner job sheet of {set:company}, dated {today}. Cleaner: {col:availability.cleaner}. Day: {col:availability.date}.', 'Hours available: {col:availability.available_hours}. Hours booked: {col:availability.booked_hours}. Free hours: {col:availability.free_hours}. Load check: {col:availability.load_flag}.',
        'Take the keys, the linen sets and the supplies listed in the turnover schedule. Photograph any damage before you clean and tell the co-host the same day.', 'Write the start and end time of each unit below and hand the sheet to the host.'], ['Cleaner', 'Host'], NOTE),
    DOC('pay_statement', 'Cleaner Pay Statement', 'Cleaner pay statement for one month', 'cleaner_pay.pay_id', [
        'Pay statement of {set:company}, dated {today}. Cleaner: {col:cleaner_pay.cleaner}. Month: {col:cleaner_pay.month}.', 'Turnovers: {col:cleaner_pay.turnovers}. Hours: {col:cleaner_pay.hours}. Amount: {col:cleaner_pay.amount}. Pay per turnover: {col:cleaner_pay.pay_per_turnover}. Pay per hour: {col:cleaner_pay.pay_per_hour}.',
        'Paid on: {col:cleaner_pay.paid_on}. Pay of a same-day turn includes the premium of {set:same_day_premium}.', 'Please check the figures and tell the host about any difference within {set:warn_days} days.'], ['Host', 'Cleaner'], NOTE),
    DOC('unit_checklist', 'Unit Cleaning Checklist', 'Cleaning task of one unit', 'unit_tasks.task_id', [
        'Unit cleaning checklist of {set:company}, dated {today}. Unit: {col:unit_tasks.unit}.', 'Task: {col:unit_tasks.task}. Time: {col:unit_tasks.minutes} minutes ({col:unit_tasks.hours} hours). Frequency: {col:unit_tasks.frequency}.',
        'Minutes of all tasks done at every turnover in this unit: {col:unit_tasks.unit_minutes}. This task is {col:unit_tasks.task_share} of the turnover.', 'Tick the task when it is done and note any problem for the co-host below.'], ['Cleaner', 'Host'], NOTE),
    DOC('order_doc', 'Supplies Order', 'Supplies order to a supplier', 'supplier_orders.order_id', [
        'Supplies order of {set:company}, dated {today}. Order {col:supplier_orders.order_id} placed on {col:supplier_orders.date}.', 'Items: {col:supplier_orders.items}. Amount: {col:supplier_orders.amount}. Delivery wanted by {col:supplier_orders.delivery_date} ({col:supplier_orders.lead_days} days).',
        'Delivery check: {col:supplier_orders.order_flag}. Please confirm the order and the delivery date in writing and note any item you cannot supply.', 'Prices are before any local tax. Check the delivery against this order and report a short delivery the same day.'], ['Host', 'Supplier'], NOTE),
    DOC('stock_doc', 'Stock Count Report', 'Stock count sheet for one item', 'supply_stock.item', [
        'Stock count sheet of {set:company}, dated {today}. Item: {col:supply_stock.item} ({col:supply_stock.category}).', 'On hand: {col:supply_stock.on_hand}. Reorder point: {col:supply_stock.reorder_point}. Par level: {col:supply_stock.par_level}. Used a month: {col:supply_stock.monthly_use}.',
        'Status: {col:supply_stock.status}. Days of cover: {col:supply_stock.days_cover}. Quantity to order: {col:supply_stock.qty_to_order}, cost {col:supply_stock.order_value}. Order by {col:supply_stock.order_by}.',
        'Write the counted quantity below and sign. A difference of more than a few percent is checked against the purchases.'], ['Host', 'Cleaner'], NOTE),
    DOC('cost_report', 'Monthly Cleaning Cost Report', 'Monthly cleaning cost report for one unit', 'units.unit_id', [
        'Monthly cleaning cost report of {set:company}, dated {today}. Unit: {col:units.name} ({col:units.city}), owner {col:units.owner}.', 'Cleaning fee charged: {col:units.cleaning_fee}. Hours per turnover: {col:units.avg_hours}. Cleaner cost per turnover: {col:units.cleaner_cost}. Total cost per turnover: {col:units.cost_total}.',
        'Margin on the fee: {col:units.fee_margin} ({col:units.margin_pct}). Fee check: {col:units.margin_flag}. Fee for the margin target: {col:units.fee_for_target}. Cleaner cost this month: {col:units.cost_month}.', 'Redo jobs on this unit: {col:units.redo_count}. Cost per night sold: {col:units.cost_per_night}.'], ['Host', 'Owner'], NOTE),
    DOC('inspection_doc', 'Inspection Report', 'Inspection report for one unit and turnover', 'inspections.check_id', [
        'Inspection report of {set:company}, dated {today}. Inspection {col:inspections.check_id} on {col:inspections.date} at {col:inspections.unit}.', 'Turnover {col:inspections.turnover_id} by {col:inspections.cleaner}. Inspector: {col:inspections.inspector}.',
        'Score: {col:inspections.score} out of 5. Issues found: {col:inspections.issues_found}. Result: {col:inspections.pass_flag}. Wanted score: {set:min_inspection_score}.', 'Issues and the action for each are written below with the date.'], ['Inspector', 'Cleaner'], NOTE),
    DOC('linen_doc', 'Linen Inventory', 'Linen inventory for one unit and month', 'linen.linen_id', [
        'Linen inventory of {set:company}, dated {today}. Unit: {col:linen.unit}. Month: {col:linen.month}. Counted by {col:linen.counted_by}.', 'Sets in use: {col:linen.sets_in_use}. Sets washed: {col:linen.sets_washed}. Sets damaged: {col:linen.sets_damaged}. Sets bought: {col:linen.sets_bought}.',
        'Loss share: {col:linen.loss_pct}. Loss check: {col:linen.loss_flag}.', 'Damaged sets are removed from use and written off. Order new sets when the loss check is high.'], ['Host', 'Cleaner'], NOTE),
    DOC('redo_doc', 'Redo and Quality Report', 'Redo and quality report for one redo job', 'redo.redo_id', [
        'Redo and quality report of {set:company}, dated {today}. Redo {col:redo.redo_id} on {col:redo.date} at {col:redo.unit}, cleaner {col:redo.cleaner}.', 'Reason: {col:redo.reason}. Hours lost: {col:redo.hours_lost}. Refund or discount given: {col:redo.discount_given}. Cost of the redo: {col:redo.cost}.',
        'Wanted share of turnovers that need a redo: {set:redo_target}. The cause and the step to prevent it are written below.', 'The cleaner is told the same day and the next turnover of this unit is inspected.'], ['Host', 'Cleaner'], NOTE),
]
assert len(documents) == 10
checklists = [
    CHK('std_turn', 'Standard Turnover Steps', 'turnovers', 'turnovers.date', [('Check the check-out time and the next check-in', -1), ('Collect keys, linen sets and supplies', 0), ('Strip the beds and start the laundry', 0), ('Clean the bathroom and the kitchen', 0),
        ('Make the beds and restock toiletries, coffee and tea', 0), ('Vacuum and mop all floors', 0), ('Walk through with the inspection list and take photos', 0), ('Lock up and tell the co-host the unit is ready', 0), ('Write any problem in the cleaner notes', 1)]),
    CHK('same_turn', 'Same-Day Turnover Steps', 'same_day', 'same_day.date', [('Check the hours between the stays and the hours needed', -2), ('Add a second cleaner if the slack is under the wanted spare hours', -2), ('Tell the co-host the exact check-out time', -1),
        ('Start the clean as soon as the guest leaves', 0), ('Do the beds and bathroom first', 0), ('Take a photo of the finished unit', 0), ('Tell the co-host the unit is ready', 0), ('Record the real hours and the slack', 1)]),
    CHK('deep_run', 'Deep Clean Steps', 'deep_cleans', 'deep_cleans.date', [('Choose a day with no check-in', -7), ('Tell the owner and the co-host', -7), ('Book the cleaner and extra hours', -5), ('Prepare supplies and equipment', -1),
        ('Clean oven, fridge, windows, curtains and under the beds', 0), ('Descale kettle, taps and shower head', 0), ('Take before and after photos', 0), ('Record hours and cost', 1)]),
    CHK('insp_run', 'Inspection After Cleaning Steps', 'inspections', 'inspections.date', [('Check the beds, towels and linen', 0), ('Check the bathroom and the kitchen', 0), ('Check floors, surfaces and smells', 0), ('Check lights, smoke alarm and lock', 0),
        ('Score the unit from 1 to 5 and write the issues found', 0), ('Send a redo request if the score is below 4', 0), ('Tell the cleaner the result', 1), ('Add the inspection to the monthly review', 7)]),
    CHK('stock_run', 'Weekly Stock Count Steps', 'supply_stock', 'supply_stock.last_bought', [('Count every item on the shelf', 0), ('Write the counts in the stock sheet', 0), ('Check the status and days of cover', 1), ('List the items below the reorder point', 1),
        ('Check that the price is still right', 2), ('Ask the cleaners about items running out', 2), ('Send the reorder list to the host', 3)]),
    CHK('reorder_run', 'Supplies Reorder Steps', 'supplier_orders', 'supplier_orders.date', [('Open the reorder list', 0), ('Check the quantity to order and the cost', 0), ('Compare supplier prices for big items', 0), ('Place the order with the supplier', 0),
        ('Write the order and the delivery date in the sheet', 0), ('Check the delivery against the order', 5), ('Report a short delivery the same day', 5), ('Update the stock sheet', 6)]),
    CHK('linen_day', 'Linen and Laundry Day Steps', 'laundry', 'laundry.date', [('Collect used sets from every unit', 0), ('Sort by colour and fabric', 0), ('Wash and dry the sets', 0), ('Fold the sets and count them', 1), ('Remove stained or worn sets', 1),
        ('Deliver the sets to the units', 1), ('Record the loads and the cost', 1), ('Order new sets if the loss is high', 3)]),
    CHK('pay_run', 'Monthly Cleaner Pay Steps', 'cleaner_pay', 'cleaner_pay.month', [('Close the month and list every turnover', 31), ('Add up hours and turnovers for each cleaner', 32), ('Add the same-day premium', 32), ('Send the pay statement to each cleaner', 33),
        ('Answer questions about the statement', 35), ('Pay the cleaners', 36), ('Send the pay summary to the accountant', 37), ('File the statements', 38)]),
    CHK('lost_run', 'Lost and Found Handling Steps', 'lost_found', 'lost_found.date', [('Photograph the item and note the unit', 0), ('Store it in a labelled bag', 0), ('Tell the co-host', 0), ('Write to the guest with the photo', 1), ('Agree how the item will be returned and who pays the post', 3),
        ('Return the item and record the date', 10), ('Decide about an unclaimed item after the wait in your settings', 30)]),
    CHK('onboard_run', 'New Cleaner Onboarding Steps', 'team', 'team.start', [('Agree hours, rate and payment day in writing', -3), ('Share the cleaning checklist of each unit', -2), ('Show the key and lock routines', 0), ('Walk through one unit together', 0),
        ('Do the first turnover with a trained cleaner', 1), ('Inspect the first three turnovers', 3), ('Give feedback and agree the weekly hours', 7), ('Review after 30 days', 30)]),
]
assert len(checklists) == 10
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('c_day', 'Cleaner: your turnovers for the day', 'turnovers', 'turnovers.cleaner_phone', 'Hello {cleaner}, your turnover on {date}: {unit}, about {hours} hours. {day_turns} turnovers are planned that day.'),
    M('c_same', 'Cleaner: same-day turn at a unit', 'turnovers', 'turnovers.cleaner_phone', 'Hello {cleaner}, {unit} is a same-day turn on {date}. The next guest arrives {next_check_in}. You have {window_hours} hours.'),
    M('c_redo', 'Cleaner: please redo a unit', 'redo', 'redo.cleaner_phone', 'Hello {cleaner}, please redo {unit}. The guest reported an issue: {reason}. It should take about {hours_lost} hours.'),
    M('c_over', 'Cleaner: too many turnovers on a day', 'availability', 'availability.cleaner_phone', 'Hello {cleaner}, you have {booked_hours} hours booked on {date} and {available_hours} available. I will move some turnovers.'),
    M('c_pay', 'Cleaner: your pay has been sent', 'cleaner_pay', 'cleaner_pay.cleaner_phone', 'Hello {cleaner}, your pay for {month} has been sent: {amount} for {turnovers} turnovers and {hours} hours. Thank you.'),
    M('c_deep', 'Cleaner: a deep clean is booked', 'deep_cleans', 'deep_cleans.cleaner_phone', 'Hello {cleaner}, a deep clean is booked at {unit} on {date}, about {hours} hours.'),
    M('c_early', 'Cleaner: the stay ended early', 'turnovers', 'turnovers.cleaner_phone', 'Hello {cleaner}, the guest at {unit} leaves early. Your turnover is now on {date}.'),
    M('c_arrive', 'Cleaner: guests arrive earlier', 'turnovers', 'turnovers.cleaner_phone', 'Hello {cleaner}, guests arrive earlier at {unit} on {next_check_in}. Please finish the turnover before they come.'),
    M('c_linen', 'Cleaner: please count the linen', 'linen', 'linen.cleaner_phone', 'Hello {counted_by}, please count the linen at {unit}. Last count: {sets_in_use} sets in use and {sets_damaged} damaged.'),
    M('c_new', 'Cleaner: a new turnover was added', 'turnovers', 'turnovers.cleaner_phone', 'Hello {cleaner}, a new turnover was added for {date}: {unit}, about {hours} hours.'),
    M('c_thanks', 'Cleaner: thank you, great inspection', 'inspections', 'inspections.cleaner_phone', 'Hello {cleaner}, thank you for the inspection at {unit} on {date}. The score was {score}. Great work.'),
    M('c_cover', 'Cleaner: can you cover a turnover', 'availability', 'availability.cleaner_phone', 'Hello {cleaner}, can you cover a turnover on {date}? You have {free_hours} free hours that day.'),
    M('h_late', 'Co-host: the cleaner is running late', 'turnovers', 'turnovers.cohost_phone', 'Hello, the cleaner {cleaner} is running late at {unit} on {date}. The next check-in is {next_check_in}.'),
    M('h_ready', 'Co-host: the unit is ready for check-in', 'turnovers', 'turnovers.cohost_phone', 'Hello, {unit} is ready for check-in after the turnover on {date} by {cleaner}.'),
    M('h_lost', 'Co-host: a guest left something behind', 'lost_found', 'lost_found.cohost_phone', 'Hello, a guest left {item} at {unit} on {date}. Please contact {guest}.'),
    M('h_issue', 'Co-host: the inspection found an issue', 'inspections', 'inspections.cohost_phone', 'Hello, the inspection at {unit} on {date} found {issues_found} issues. The score was {score}.'),
    M('o_reorder', 'Host: an item is below the reorder point', 'supply_stock', 'supply_stock.host_phone', 'Hello, {item} is below the reorder point: {on_hand} on hand, reorder point {reorder_point}. Quantity to order: {qty_to_order}.'),
    M('o_order', 'Host: the supplies order is ready', 'supplier_orders', 'supplier_orders.host_phone', 'Hello, the supplies order {order_id} is ready to send: {items} items, amount {amount}.'),
    M('o_hours', 'Host: cleaner hours are over the limit', 'availability', 'availability.host_phone', 'Hello, {cleaner} has {booked_hours} hours booked on {date} against {available_hours} available.'),
    M('o_fee', 'Host: the fee does not cover the cost', 'units', 'units.host_phone', 'Hello, the cleaning fee at {name} is {cleaning_fee} but a turnover costs {cost_total}. The fee for your margin target is {fee_for_target}.'),
    M('o_redo', 'Host: the redo rate is high', 'redo', 'redo.host_phone', 'Hello, the redo on {unit} by {cleaner} on {date} cost {cost}. The redo rate is high this month.'),
    M('o_report', 'Host: the cleaning cost report is ready', 'units', 'units.host_phone', 'Hello, the monthly cleaning cost report is ready. {name}: cleaner cost this month {cost_month}, margin on the fee {fee_margin}.'),
    M('o_linen', 'Host: linen sets are running low', 'linen', 'linen.host_phone', 'Hello, linen sets are running low at {unit}: {sets_in_use} in use and {sets_damaged} damaged.'),
    M('s_deliver', 'Supplier: please deliver the order', 'supplier_orders', 'supplier_orders.supplier_phone', 'Hello, please deliver order {order_id}: {items} items, amount {amount}, by {delivery_date}.'),
    M('s_short', 'Supplier: the delivery was short', 'supplier_orders', 'supplier_orders.supplier_phone', 'Hello, order {order_id} arrived short. Please send the rest of the {items} items as soon as you can.'),
    M('s_price', 'Supplier: a price update for an item', 'supply_items', 'supply_items.supplier_phone', 'Hello, please confirm the price of {item}. Our last price was {unit_cost} for {pack}.'),
    M('a_pay', 'Accountant: cleaner pay is attached', 'cleaner_pay', 'cleaner_pay.accountant_phone', 'Hello, cleaner pay for {month} is attached: {cleaner}, {amount} for {hours} hours.'),
    M('w_cost', 'Owner: cleaning cost of your unit', 'units', 'units.owner_phone', 'Hello {owner}, the cleaning cost for {name} this month is {cost_month}.'),
]
assert len(messages) == 28, len(messages)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'
M3 = 'DATE(YEAR({today}),MONTH({today})-3,1)'; JAN = 'DATE(YEAR({today}),1,1)'
QS = 'DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+1,1)'; QE = 'DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+4,1)'
YES = tok('yn', 'Yes')
def TD(a, b): return '{range:turnovers.date},">="&%s,{range:turnovers.date},"<"&%s' % (a, b)
kpis = [
    KPI('Turnovers this month', 'COUNTIFS(%s)' % TD(MS, NXT), 'int'),
    KPI('Turnovers next 7 days', 'COUNTIFS(%s)' % TD('{today}', '({today}+7)'), 'int'),
    KPI('Turnovers today', 'COUNTIFS({range:turnovers.date},{today})', 'int'),
    KPI('Same-day turns next 14 days', 'COUNTIFS(%s,{range:turnovers.same_day},%s)' % (TD('{today}', '({today}+14)'), YES), 'int'),
    KPI('Cleaner hours this month', 'SUMIFS({range:cleaner_pay.hours},{range:cleaner_pay.month},%s)' % MS, 'num'),
    KPI('Cleaner pay this month', 'SUMIFS({range:cleaner_pay.amount},{range:cleaner_pay.month},%s)' % MS, 'money'),
    KPI('Average hours per turnover', 'IFERROR(AVERAGE({range:turnovers.hours}),0)', 'num'),
    KPI('Average pay per turnover', 'IFERROR(AVERAGE({range:turnovers.pay}),0)', 'money'),
    KPI('Cleaning cost as share of cleaning fees', 'IFERROR((AVERAGE({range:turnovers.pay})+{set:supplies_per_turnover})/AVERAGE({range:units.cleaning_fee}),0)', 'pct'),
    KPI('Units where the fee is below the cost', 'COUNTIFS({range:units.margin_flag},%s)' % ca('Fee too low'), 'int'),
    KPI('Inspection score average', 'IFERROR(AVERAGE({range:inspections.score}),0)', 'num'),
    KPI('Redo jobs this month', 'COUNTIFS({range:redo.date},">="&%s,{range:redo.date},"<="&{today})' % MS, 'int'),
    KPI('Redo rate, last 3 months', 'IFERROR(COUNTIFS({range:redo.date},">="&%s,{range:redo.date},"<="&{today})/SUMIFS({range:cleaner_pay.turnovers},{range:cleaner_pay.month},">="&%s),0)' % (M3, M3), 'pct'),
    KPI('Top cleaner by turnovers this month', 'IFERROR(INDEX({range:team.name},MATCH(MAX({range:team.turnovers_month}),{range:team.turnovers_month},0)),"")', 'text'),
    KPI('Busiest day next 14 days, turnovers', 'MAX({range:turnovers.busy_next})', 'int'),
    KPI('Overbooked cleaner days ahead', 'COUNTIFS({range:availability.load_flag},%s,{range:availability.date},">="&{today})' % ca('Overbooked'), 'int'),
    KPI('Supplies spend this month', 'SUMIFS({range:purchases.amount},{range:purchases.date},">="&%s,{range:purchases.date},"<="&{today})' % MS, 'money'),
    KPI('Supplies spend per turnover, 12 months', 'IFERROR(SUMIFS({range:purchases.amount},{range:purchases.date},">="&%s,{range:purchases.date},"<"&%s)/SUMIFS({range:cleaner_pay.turnovers},{range:cleaner_pay.month},">="&%s,{range:cleaner_pay.month},"<"&%s),0)' % (Y1, MS, Y1, MS), 'money'),
    KPI('Items below reorder point', 'COUNTIFS({range:supply_stock.status},%s)' % ca('Below reorder point'), 'int'),
    KPI('Value to reorder', 'SUM({range:supply_stock.order_value})', 'money'),
    KPI('Days of cover for the lowest item', 'MIN({range:supply_stock.days_cover})', 'int'),
    KPI('Linen sets in use', 'SUMIFS({range:linen.sets_in_use},{range:linen.month},%s)' % MS, 'int'),
    KPI('Linen sets damaged this year', 'SUMIFS({range:linen.sets_damaged},{range:linen.month},">="&%s)' % JAN, 'int'),
    KPI('Laundry cost this month', 'SUMIFS({range:laundry.cost},{range:laundry.date},">="&%s,{range:laundry.date},"<="&{today})' % MS, 'money'),
    KPI('Deep cleans this quarter', 'COUNTIFS({range:deep_cleans.date},">="&%s,{range:deep_cleans.date},"<"&%s)' % (QS, QE), 'int'),
    KPI('Lost items open', 'COUNTIFS({range:lost_found.status},%s)+COUNTIFS({range:lost_found.status},%s)' % (tok('lfst', 'Found'), tok('lfst', 'Contacted')), 'int'),
    KPI('Open supplier orders', 'COUNTIFS({range:supplier_orders.status},%s)+COUNTIFS({range:supplier_orders.status},%s)+COUNTIFS({range:supplier_orders.status},%s)' % (tok('ordst', 'Ordered'), tok('ordst', 'Short delivery'), tok('ordst', 'Late')), 'int'),
    KPI('Turnovers without a cleaner', 'COUNTIFS({range:turnovers.assign_flag},%s)' % ca('No cleaner'), 'int'),
    KPI('Spend on supplies this year', 'SUMIFS({range:purchases.amount},{range:purchases.date},">="&%s,{range:purchases.date},"<="&{today})' % JAN, 'money'),
]
assert len(kpis) == 29, len(kpis)
dashboard = {"title": "Cleaning and Supplies Dashboard", "kpis": kpis,
    "monthly": {"title": "Cleaner pay, supplies, laundry and deep clean cost", "date": "cleaner_pay.month", "series": [
        {"label": "Cleaner pay", "sum": "cleaner_pay.amount", "date": "cleaner_pay.month"}, {"label": "Supplies purchases", "sum": "purchases.amount", "date": "purchases.date"},
        {"label": "Laundry cost", "sum": "laundry.cost", "date": "laundry.date"}, {"label": "Deep clean cost", "sum": "deep_cleans.cost", "date": "deep_cleans.date"}]},
    "breakdowns": [{"title": "Turnovers by city", "by": "turnovers.city", "value": "turnovers.pay", "agg": "count"}, {"title": "Supplies spend by category", "by": "purchases.category", "value": "purchases.amount", "agg": "sum"},
                   {"title": "Turnovers by cleaner", "by": "turnovers.cleaner", "value": "turnovers.pay", "agg": "count"}, {"title": "Cleaner pay by cleaner", "by": "cleaner_pay.cleaner", "value": "cleaner_pay.amount", "agg": "sum"}]}
insights = {"filters": [{"label": "Unit", "ref": "units.name"}, {"label": "City", "list": "city"}, {"label": "Cleaner", "ref": "team.name"}],
    "gauges": [{"title": "Inspections passed", "num": AGG('count', 'inspections', where=[('pass_flag', '=', ca('Pass'))]), "den": AGG('count', 'inspections')},
               {"title": "Redo jobs per turnover", "num": AGG('count', 'redo'), "den": AGG('count', 'turnovers')},
               {"title": "Items above the reorder point", "num": AGG('count', 'supply_stock', where=[('status', '<>', ca('Below reorder point'))]), "den": AGG('count', 'supply_stock')},
               {"title": "Units where the fee covers the cost", "num": AGG('count', 'units', where=[('margin_flag', '=', ca('Fee covers cost'))]), "den": AGG('count', 'units')},
               {"title": "Cleaners within weekly hours", "num": AGG('count', 'team', where=[('week_flag', '=', ca('Within weekly hours'))]), "den": AGG('count', 'team', where=[('week_flag', '<>', ca('Not a cleaner'))])},
               {"title": "Turnovers with a cleaner", "num": AGG('count', 'turnovers', where=[('assign_flag', '=', ca('Cleaner set'))]), "den": AGG('count', 'turnovers')}],
    "charts": [
        CHART('Turnovers per month', 'column', 'month', [AGG('count', 'turnovers', date='turnovers.date', label='Turnovers')]),
        CHART('Cleaner pay per month', 'column', 'month', [AGG('sum', 'cleaner_pay', 'cleaner_pay.amount', date='cleaner_pay.month', label='Cleaner pay')]),
        CHART('Cleaner hours per month', 'column', 'month', [AGG('sum', 'cleaner_pay', 'cleaner_pay.hours', date='cleaner_pay.month', label='Hours')]),
        CHART('Turnovers by cleaner', 'bar', 'turnovers.cleaner', [AGG('count', 'turnovers', label='Turnovers')]),
        CHART('Pay by cleaner', 'bar', 'cleaner_pay.cleaner', [AGG('sum', 'cleaner_pay', 'cleaner_pay.amount', label='Pay')]),
        CHART('Average hours per turnover by unit type', 'bar', 'turnovers.unit_type', [AGG('avg', 'turnovers', 'turnovers.hours', label='Hours per turnover')]),
        CHART('Turnovers by city', 'bar', 'turnovers.city', [AGG('count', 'turnovers', label='Turnovers')]),
        CHART('Redo jobs per month', 'column', 'month', [AGG('count', 'redo', date='redo.date', label='Redo jobs')]),
        CHART('Inspection score per month', 'line', 'month', [AGG('avg', 'inspections', 'inspections.score', date='inspections.date', label='Score')]),
        CHART('Same-day turns per month', 'column', 'month', [AGG('count', 'turnovers', date='turnovers.date', where=[('same_day', '=', YES)], label='Same-day turns')]),
        CHART('Supplies spend per month', 'column', 'month', [AGG('sum', 'purchases', 'purchases.amount', date='purchases.date', label='Supplies')]),
        CHART('Supplies spend by category', 'bar', 'purchases.category', [AGG('sum', 'purchases', 'purchases.amount', label='Spend')]),
        CHART('Purchases by supplier', 'bar', 'purchases.supplier', [AGG('sum', 'purchases', 'purchases.amount', label='Spend')]),
        CHART('Cleaner cost per turnover by month', 'line', 'month', [AGG('avg', 'turnovers', 'turnovers.pay', date='turnovers.date', label='Cleaner cost per turnover')]),
        CHART('Cleaning fee margin by unit type', 'bar', 'units.unit_type', [AGG('avg', 'units', 'units.margin_pct', label='Margin on the fee')]),
        CHART('Turnovers by weekday', 'bar', 'turnovers.weekday', [AGG('count', 'turnovers', label='Turnovers')]),
        CHART('Items below reorder point by category', 'bar', 'supply_stock.category', [AGG('count', 'supply_stock', where=[('status', '=', ca('Below reorder point'))], label='Items')]),
        CHART('Laundry cost per month', 'column', 'month', [AGG('sum', 'laundry', 'laundry.cost', date='laundry.date', label='Laundry cost')])]}
signature = [
    {"name": "Daily turnover schedule with cleaner workload", "why": "every turnover shows its cleaner, hours, time to the next check-in and how many turnovers fall on the same day", "where": "Turnovers"},
    {"name": "Overbooked cleaner alert", "why": "booked hours against available hours for each cleaner and day, with the days that cannot be covered", "where": "Cleaner Availability"},
    {"name": "Same-day turn timer", "why": "hours between check-out and check-in against the hours the unit needs, with the latest start and the slack", "where": "Same-Day Turn Timer"},
    {"name": "Cleaner pay statement", "why": "turnovers, hours, pay per turnover and per hour for each cleaner and month, ready to print", "where": "Cleaner Pay"},
    {"name": "Cleaning fee margin by unit", "why": "cleaner cost, supplies and linen against the cleaning fee of each unit, with the fee that reaches your margin target", "where": "Units"},
    {"name": "Supplies reorder list", "why": "stock against the reorder point and par level, with the quantity to order, its cost and the order by date", "where": "Supply Stock"},
    {"name": "Days of cover by item", "why": "stock on hand against monthly use and the supplier lead time, so nothing runs out before the delivery", "where": "Days of Cover"},
    {"name": "Linen sets needed", "why": "units, stays a week and laundry days give the sets on the beds, in the wash and spare, and the money tied up in linen", "where": "Linen Sets Needed"},
    {"name": "Inspection and redo tracker", "why": "every inspection with score and issues, every redo with its reason, hours lost and cost, by unit and cleaner", "where": "Inspection Checks"},
    {"name": "Monthly cleaning cost report", "why": "cleaner cost, supplies and margin on the fee for each unit and month, ready to send to the owner", "where": "Units"}]
competitors = [
    {"what": "free cleaning schedule templates", "lacks": "list the jobs of the day but never compare booked hours with the hours a cleaner has, so an overbooked cleaner goes unseen"},
    {"what": "subscription property-management software", "lacks": "charge every month for task lists and hide the cost of a turnover, so you cannot see which unit loses money on its cleaning fee"},
    {"what": "single-sheet supplies trackers", "lacks": "record purchases but have no reorder point, days of cover or quantity to order, so items run out before check-in"},
    {"what": "generic expense spreadsheets", "lacks": "add up cleaning and supplies costs but cannot give cost per turnover, cleaner pay per hour or the margin on the cleaning fee"},
    {"what": "paper cleaning checklists", "lacks": "cannot score inspections, count redo jobs and their cost or show which cleaner and which unit need attention"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: cleaner pay per hour, the extra pay for a same-day turn, the days of stock to hold, the wanted inspection score and the cleaning fee margin.',
    'Check Cleaners, Team and Units. They hold your cleaners with their weekly hours and rate, the people the other sheets look up and the cleaning fee of each unit.',
    'Log every clean on Turnovers: date, unit, cleaner, hours, pay and linen. A turnover is the clean and reset between two stays. The time to the next check-in and the tight-turn check fill in.',
    'Open Cleaner Availability to see the booked and free hours of each cleaner and day, and Same-Day Turns to see the slack when a guest leaves and another arrives the same day.',
    'Record each month of each cleaner on Cleaner Pay. Pay per turnover and per hour calculate themselves, and the pay statement prints from the row.',
    'Keep Supply Items and Supply Stock up to date. The status, days of cover and quantity to order fill in, and the order list shows what to buy before the next check-in.',
    'Log every purchase on Supply Purchases and every order on Supplier Orders. Share of spend, the days to delivery and the delivery check fill in by themselves.',
    'Score each clean on Inspection Checks and write each redo on Redo Jobs. The pass check and the cost of the redo calculate themselves.',
    'Count linen on Linen Counts, record each run on Laundry Runs and each deep clean on Deep Cleans. Unit Cleaning Tasks holds the minutes of every task of a unit.',
    'Write found items on Lost and Found and notes from your cleaners on Cleaner Notes. Follow-ups that wait are flagged.',
    f'Use the {len(tools)} calculators for the day plan, workload, same-day turns, cleaner pay, cleaning cost, fee margin, reorder, days of cover, linen sets, laundry, budget, redo cost and the weekly rota.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Cleaning and Supplies Dashboard and Charts every week: turnovers, pay, hours, inspections, redo jobs, stock and spend.']
listing = {"title": "Short-Term Rental Cleaning Excel Template: Turnover Schedule, Cleaner Pay, Supplies Stock, Inspections, Linen, Laundry",
    "headline": "Run every clean, every cleaner and every supply shelf from one workbook",
    "tags": ["short term rental", "vacation rental", "rental host", "turnover schedule", "cleaner pay", "excel template", "cleaning checklist", "supplies tracker", "linen inventory", "inspection log", "property host", "holiday let", "guest turnover"],
    "description": ("Run the cleaning side of a short-term or vacation rental business in one Excel workbook. Built for a host or co-host with 3 to 15 furnished units rented by the night, where every stay ends with a turnover, the clean and reset between two stays. "
        "The Turnovers sheet lists each clean with its unit, cleaner, hours, pay and linen sets, and works out the hours to the next check-in, a tight-turn check and the turnovers planned on the same day.\n\n"
        "Cleaner Availability compares the hours booked with the hours each cleaner has, so an overbooked cleaner shows before the day starts. Same-Day Turns shows the slack when a guest leaves and another arrives the same day. Cleaner Pay gives pay per turnover and per hour and prints a pay statement. "
        "Units compares the cleaning fee with the cleaner cost, supplies and linen of a turnover and shows the fee that reaches your margin target.\n\n"
        "Supply Items, Supply Stock, Supply Purchases and Supplier Orders keep the shelves full: status against the reorder point and par level, days of cover, the quantity to order and its cost, share of spend and the delivery check. "
        "Inspection Checks, Redo Jobs, Linen Counts, Laundry Runs, Deep Cleans, Unit Cleaning Tasks, Lost and Found and Cleaner Notes cover quality, linen and the small jobs that cost money.\n\n"
        f"{len(tools)} calculators cover the day plan, cleaner workload, same-day turns, pay, cost per night, fee margin, reorder, days of cover, linen sets, laundry routes, budget, redo cost and the weekly rota. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to cleaners, the co-host (a helper who handles guests for a fee), the host, suppliers, the accountant and owners.\n\n"
        "This is part four of the Short-Term Rental Host suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data to explore first. It helps you plan your cleaning and supplies and does not promise results."),
    "features": ["Turnover schedule with cleaner and time checks", "Overbooked cleaner alert by day", "Same-day turn slack and timer", "Cleaner pay statements", "Cleaning fee margin by unit",
                 "Supplies reorder list with days of cover", "Inspection and redo tracker", "Linen, laundry and deep clean logs", f"{len(tools)} calculators for cleaning and stock", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p4', slug='short-term-rental-turnovers', profession='Short-Term Rental Host', name='Turnovers, Cleaners and Supplies',
         tagline='Run every clean, every cleaner and every supply shelf from one workbook', price_usd=29,
         colors={"primary": "#264653", "accent": "#E9C46A"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 4, "of": 8, "focus": "Turnovers, cleaners and supplies"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sr4.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
