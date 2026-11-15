"""Short-term rental host suite part 4: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr4_lists import *
import sr4_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def CPH(my='cleaner'): return CA('cleaner_phone', 'Cleaner phone', 'text', LKT('team.phone', 'team.name', my), 18)
def COH(): return CA('cohost_phone', 'Co-host phone', 'text', '"%s"' % D.COHOST_PHONE, 18)
def HOST(): return CA('host_phone', 'Host phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def ACC(): return CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCT_PHONE, 18)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'
WK0 = '({today}-WEEKDAY({today},2)+1)'
YES = tok('yn', 'Yes')

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('cleaner_rate', 'Cleaner pay per hour', 'money', 17), S('same_day_premium', 'Extra pay share for a same-day turn', 'pct', 0.15),
    S('reorder_cover_days', 'Days of stock to hold before reordering', 'int', 21), S('warn_days', 'Days ahead to warn of a turnover, a delivery or a follow-up', 'int', 7),
    S('min_inspection_score', 'Wanted inspection score, 1 to 5', 'num', 4.5), S('redo_target', 'Highest wanted share of turnovers that need a redo', 'pct', 0.05),
    S('fee_margin_target', 'Wanted margin of the cleaning fee over its cost', 'pct', 0.30), S('supplies_per_turnover', 'Consumable supplies used in one turnover', 'money', 8),
    S('linen_cost_per_set', 'Wash and wear cost of one linen set', 'money', 1), S('window_buffer_hours', 'Spare hours wanted between the end of a clean and check-in', 'num', 0.5),
    S('lost_item_days', 'Days before an unclaimed lost item needs a decision', 'int', 14),
]
assert 3 <= len(settings) <= 20

TK = tok('turnst', 'Redo needed')
tables = [
    T('turnovers', 'Turnovers', 'Turnovers by day with cleaner, hours and pay',
      'One row per turnover, the clean and reset between two stays: unit, cleaner, hours, pay, linen and score; hours to the next check-in, the tight-turn check and turnovers that day fill in by themselves.', [
        C('turnover_id', 'Turnover ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 24), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), LST('weekday', 'Weekday', 'wday', 11),
        C('booking_id', 'Booking', 'text', 10), C('next_check_in', 'Next check-in', 'date', 12), LST('same_day', 'Same-day turn', 'yn', 9), REF('cleaner', 'Cleaner', 'team.name', 24), C('hours', 'Hours', 'num', 8), C('pay', 'Pay', 'money', 9),
        C('linen_sets', 'Linen sets', 'int', 9), LST('status', 'Status', 'turnst', 13), C('score', 'Score', 'int', 8),
        CA('days_to_date', 'Days to date', 'int', '{col:date}-{today}', 10),
        CA('window_hours', 'Hours to next check-in', 'num', 'IF({col:next_check_in}>0,MIN(168,({col:next_check_in}-{col:date})*24+4),168)', 12),
        CA('tight_flag', 'Time check', 'text', 'IF({col:hours}+{set:window_buffer_hours}>{col:window_hours},%s,%s)' % (ca('Tight turn'), ca('Time to spare')), 14),
        CA('assign_flag', 'Cleaner check', 'text', 'IF({col:cleaner}="",%s,%s)' % (ca('No cleaner'), ca('Cleaner set')), 13),
        CA('day_turns', 'Turnovers that day', 'int', 'COUNTIFS({range:turnovers.date},{col:date})', 10),
        CA('busy_next', 'Busy day, next 14 days', 'int', 'IF(AND({col:date}>={today},{col:date}<{today}+14),{col:day_turns},0)', 12),
        CPH(), COH()],
      D.turnovers_d(), 600, [A('tight_flag', '= ' + ca('Tight turn'), 'bad'), A('assign_flag', '= ' + ca('No cleaner'), 'bad'), A('status', '= ' + TK, 'warn'), A('day_turns', '>= 4', 'warn')]),
    T('cleaner_pay', 'Cleaner Pay', 'Cleaner pay by month with pay per turnover and per hour',
      'One row per cleaner and month: turnovers, hours and the amount to pay; pay per turnover and per hour fill in by themselves, with the paid on date and the status.', [
        C('pay_id', 'Pay ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), REF('cleaner', 'Cleaner', 'team.name', 24), C('turnovers', 'Turnovers', 'int', 10), C('hours', 'Hours', 'num', 8), C('amount', 'Amount', 'money', 11),
        C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'paystat', 11),
        CA('pay_per_turnover', 'Pay per turnover', 'money', 'IF({col:turnovers}>0,{col:amount}/{col:turnovers},0)', 12), CA('pay_per_hour', 'Pay per hour', 'money', 'IF({col:hours}>0,{col:amount}/{col:hours},0)', 11),
        CPH(), ACC()],
      D.cleaner_pay_d(), 200, [A('status', '= ' + tok('paystat', 'Due'), 'bad'), A('status', '= ' + tok('paystat', 'Accruing'), 'warn')]),
    T('cleaners', 'Cleaners', 'Cleaners and backup helpers with weekly hours',
      'The four cleaners and the helpers who can cover a turnover, with the hours a week each can work and the hourly rate; the workload checks and the pay calculators read this sheet.', [
        C('name', 'Cleaner or helper', 'text', 24, required=True), C('hours_week', 'Hours a week', 'int', 12), C('hourly_rate', 'Hourly rate', 'money', 12)], D.cleaners_d(), 50),
    T('units', 'Units', 'Units with cleaning fee, cleaner cost and margin',
      'One row per unit: type, city, owner and cleaning fee; the average hours, cleaner cost, total cost of a turnover, the margin on the fee and the fee needed for your margin target fill in by themselves.', [
        C('unit_id', 'Unit ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), C('bedrooms', 'Bedrooms', 'int', 9), C('owner', 'Owner', 'text', 22),
        C('owner_phone', 'Owner phone', 'text', 18), C('cleaning_fee', 'Cleaning fee', 'money', 11),
        CA('avg_hours', 'Hours per turnover', 'num', 'IFERROR(AVERAGEIFS({range:turnovers.hours},{range:turnovers.unit},{col:name}),0)', 11),
        CA('cleaner_cost', 'Cleaner cost', 'money', 'IFERROR(AVERAGEIFS({range:turnovers.pay},{range:turnovers.unit},{col:name}),0)', 11),
        CA('cost_total', 'Total cost per turnover', 'money', '{col:cleaner_cost}+{set:supplies_per_turnover}+{set:linen_cost_per_set}*IFERROR(AVERAGEIFS({range:turnovers.linen_sets},{range:turnovers.unit},{col:name}),2)', 12),
        CA('fee_margin', 'Margin on the fee', 'money', '{col:cleaning_fee}-{col:cost_total}', 11), CA('margin_pct', 'Margin percent', 'pct', 'IF({col:cleaning_fee}>0,{col:fee_margin}/{col:cleaning_fee},0)', 11),
        CA('margin_flag', 'Fee check', 'text', 'IF({col:fee_margin}>=0,%s,%s)' % (ca('Fee covers cost'), ca('Fee too low')), 14),
        CA('fee_for_target', 'Fee for the margin target', 'money', 'ROUNDUP({col:cost_total}/(1-{set:fee_margin_target}),0)', 12),
        CA('cost_month', 'Cleaner cost this month', 'money', 'SUMIFS({range:turnovers.pay},{range:turnovers.unit},{col:name},{range:turnovers.date},">="&%s,{range:turnovers.date},"<"&%s)' % (MS, NXT), 12),
        CA('cost_per_night', 'Cost per night sold', 'money', 'IFERROR({col:cost_total}/AVERAGEIFS({range:bookings.nights},{range:bookings.unit},{col:name}),0)', 11),
        CA('redo_count', 'Redo jobs', 'int', 'COUNTIFS({range:redo.unit},{col:name})', 9), HOST()],
      D.units_d(), 50, [A('margin_flag', '= ' + ca('Fee too low'), 'bad'), A('margin_flag', '= ' + ca('Fee covers cost'), 'good')]),
    T('bookings', 'Bookings', 'Bookings with dates and the cleaner who turns the unit',
      'One row per upcoming or recent booking: unit, dates, guests, nights and status; the cleaner and the hours of the turnover that follows the stay fill in by themselves.', [
        C('booking_id', 'Booking', 'text', 10, required=True), C('guest', 'Guest', 'text', 24), REF('unit', 'Unit', 'units.name', 24), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), C('check_in', 'Check-in', 'date', 11),
        C('check_out', 'Check-out', 'date', 11), C('guests', 'Guests', 'int', 8), C('nights', 'Nights', 'int', 8), LST('status', 'Status', 'bstatus', 11),
        CA('cleaner', 'Cleaner', 'text', LKT('turnovers.cleaner', 'turnovers.booking_id', 'booking_id'), 24), CA('turn_hours', 'Turnover hours', 'num', LKN('turnovers.hours', 'turnovers.booking_id', 'booking_id'), 11)],
      D.bookings_d(), 400),
    T('supply_items', 'Supply Items', 'Supply items with pack, price, reorder point and supplier',
      'One row per item the units use: category, pack, unit cost, reorder point, par level (the stock to refill up to) and supplier; the stock on hand and the value of a full shelf fill in by themselves.', [
        C('item_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 24), LST('category', 'Category', 'scat', 16), C('pack', 'Pack', 'text', 12), C('unit_cost', 'Unit cost', 'money', 10), C('reorder_point', 'Reorder point', 'int', 10),
        C('par_level', 'Par level', 'int', 9), LST('supplier', 'Supplier', 'supplier', 17), C('supplier_phone', 'Supplier phone', 'text', 18),
        CA('on_hand', 'On hand', 'int', LKN('supply_stock.on_hand', 'supply_stock.item', 'item'), 9), CA('par_value', 'Value at par level', 'money', '{col:par_level}*{col:unit_cost}', 12)],
      D.supply_items_d(), 50),
    T('supply_stock', 'Supply Stock', 'Supply stock with days of cover and quantity to order',
      'One row per item: on hand, reorder point, par level, price, last bought and monthly use; the status, days of cover, quantity to order, its cost and the order by date fill in by themselves.', [
        REF('item', 'Item', 'supply_items.item', 24, required=True), LST('category', 'Category', 'scat', 16), C('on_hand', 'On hand', 'int', 9), C('reorder_point', 'Reorder point', 'int', 10), C('par_level', 'Par level', 'int', 9), C('unit_cost', 'Unit cost', 'money', 10),
        C('last_bought', 'Last bought', 'date', 11), C('lead_days', 'Lead days', 'int', 9), C('monthly_use', 'Used a month', 'int', 10),
        CA('status', 'Stock status', 'text', 'IF({col:on_hand}<={col:reorder_point},%s,IF({col:on_hand}<={col:reorder_point}*1.25,%s,%s))' % (ca('Below reorder point'), ca('Reorder soon'), ca('Stock is fine')), 17),
        CA('days_cover', 'Days of cover', 'int', 'MIN(365,IF({col:monthly_use}>0,ROUND({col:on_hand}/{col:monthly_use}*30,0),365))', 10),
        CA('qty_to_order', 'Quantity to order', 'int', 'IF(OR({col:on_hand}<={col:reorder_point}*1.25,{col:days_cover}<{set:reorder_cover_days}),MAX(0,{col:par_level}-{col:on_hand}),0)', 11),
        CA('order_value', 'Cost of the order', 'money', '{col:qty_to_order}*{col:unit_cost}', 11), CA('order_by', 'Order by', 'date', '{today}+MAX(0,{col:days_cover}-{col:lead_days})', 11), HOST()],
      D.supply_stock_d(), 50, [A('status', '= ' + ca('Below reorder point'), 'bad'), A('status', '= ' + ca('Reorder soon'), 'warn'), A('status', '= ' + ca('Stock is fine'), 'good')]),
    T('purchases', 'Supply Purchases', 'Supply purchases with amount, supplier and share of spend',
      'One row per purchase: date, item, quantity, unit cost, supplier and who paid; the amount check, the month and the share of all spend fill in by themselves.', [
        C('purchase_id', 'Purchase ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('item', 'Item', 'supply_items.item', 24), LST('category', 'Category', 'scat', 16), C('qty', 'Quantity', 'int', 9), C('unit_cost', 'Unit cost', 'money', 10),
        C('amount', 'Amount', 'money', 10), LST('supplier', 'Supplier', 'supplier', 17), LST('paid_by', 'Paid by', 'paidby', 13),
        CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('share_of_spend', 'Share of spend', 'pct', 'IFERROR({col:amount}/SUM({range:purchases.amount}),0)', 11)],
      D.purchases_d(), 500),
    T('inspections', 'Inspection Checks', 'Inspection checks with score, issues found and pass flag',
      'One row per inspection after a clean: date, unit, turnover, inspector, score from 1 to 5 and issues found; the cleaner and the pass check fill in by themselves.', [
        C('check_id', 'Check ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 24), C('turnover_id', 'Turnover', 'text', 10), REF('inspector', 'Inspector', 'team.name', 24), C('score', 'Score', 'int', 8),
        C('issues_found', 'Issues found', 'int', 9), CA('cleaner', 'Cleaner', 'text', LKT('turnovers.cleaner', 'turnovers.turnover_id', 'turnover_id'), 24),
        CA('pass_flag', 'Result', 'text', 'IF(AND({col:score}>=4,{col:issues_found}<=1),%s,%s)' % (ca('Pass'), ca('Fail')), 9), CPH(), COH()],
      D.inspections_d(), 300, [A('pass_flag', '= ' + ca('Fail'), 'bad'), A('pass_flag', '= ' + ca('Pass'), 'good')]),
    T('redo', 'Redo Jobs', 'Redo jobs with reason, hours lost and cost',
      'One row per clean that had to be done again: unit, cleaner, reason, hours lost and any refund or discount given; the cost of the redo fills in by itself.', [
        C('redo_id', 'Redo ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 24), REF('cleaner', 'Cleaner', 'team.name', 24), LST('reason', 'Reason', 'rreason', 22), C('hours_lost', 'Hours lost', 'num', 9),
        C('discount_given', 'Refund or discount', 'money', 11), CA('cost', 'Cost of the redo', 'money', '{col:hours_lost}*{set:cleaner_rate}+{col:discount_given}', 12), CPH(), HOST()],
      D.redo_d(), 150),
    T('linen', 'Linen Counts', 'Linen counts with sets in use, damaged and bought',
      'One row per unit and month from a linen count: sets in use, sets washed, damaged and bought; the loss share and the loss check fill in by themselves.', [
        C('linen_id', 'Count ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), REF('unit', 'Unit', 'units.name', 24), C('sets_in_use', 'Sets in use', 'int', 10), C('sets_washed', 'Sets washed', 'int', 10), C('sets_damaged', 'Sets damaged', 'int', 11),
        C('sets_bought', 'Sets bought', 'int', 10), REF('counted_by', 'Counted by', 'team.name', 24),
        CA('loss_pct', 'Loss share', 'pct', 'IF({col:sets_in_use}>0,{col:sets_damaged}/{col:sets_in_use},0)', 10), CA('loss_flag', 'Loss check', 'text', 'IF({col:loss_pct}>0.15,%s,%s)' % (cb('Loss is high'), cb('Loss is normal')), 13), CPH('counted_by'), HOST()],
      D.linen_d(), 200, [A('loss_flag', '= ' + cb('Loss is high'), 'bad')]),
    T('laundry', 'Laundry Runs', 'Laundry runs with loads, cost and route',
      'One row per laundry run: who ran it, the loads, the cost and the route (own machines, a laundry service or linen hire); the cost per load fills in by itself.', [
        C('run_id', 'Run ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('who', 'Who', 'team.name', 24), C('loads', 'Loads', 'int', 8), C('cost', 'Cost', 'money', 9), LST('location', 'Route', 'lloc', 16),
        CA('cost_per_load', 'Cost per load', 'money', 'IF({col:loads}>0,{col:cost}/{col:loads},0)', 11)],
      D.laundry_d(), 200),
    T('supplier_orders', 'Supplier Orders', 'Supplier orders with delivery date and status',
      'One row per order sent to a supplier: items, amount, delivery date and status; the days to delivery and the delivery check fill in by themselves.', [
        C('order_id', 'Order ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('supplier', 'Supplier', 'supplier', 17), C('items', 'Items', 'int', 8), C('amount', 'Amount', 'money', 10), C('delivery_date', 'Delivery date', 'date', 12),
        LST('status', 'Status', 'ordst', 14), C('supplier_phone', 'Supplier phone', 'text', 18), CA('lead_days', 'Days to delivery', 'int', '{col:delivery_date}-{col:date}', 11),
        CA('order_flag', 'Delivery check', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,IF({col:delivery_date}<{today},%s,%s),IF({col:status}=%s,%s,%s)))' % (
            tok('ordst', 'Delivered'), cb('Received'), tok('ordst', 'Ordered'), cb('Delivery overdue'), cb('On the way'), tok('ordst', 'Short delivery'), cb('Follow up needed'), cb('Delivery overdue')), 16), HOST()],
      D.supplier_orders_d(), 150, [A('order_flag', '= ' + cb('Delivery overdue'), 'bad'), A('order_flag', '= ' + cb('Follow up needed'), 'warn')]),
    T('availability', 'Cleaner Availability', 'Cleaner availability with booked and free hours',
      'One row per cleaner and day: hours available and hours booked from the turnovers; the free hours and the load check show who is overbooked.', [
        C('avail_id', 'Row ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('cleaner', 'Cleaner', 'team.name', 24), C('available_hours', 'Available hours', 'num', 11), C('booked_hours', 'Booked hours', 'num', 11),
        CA('free_hours', 'Free hours', 'num', '{col:available_hours}-{col:booked_hours}', 10),
        CA('load_flag', 'Load check', 'text', 'IF({col:free_hours}<0,%s,IF({col:free_hours}<1,%s,%s))' % (ca('Overbooked'), ca('Full day'), ca('Spare hours')), 12), CPH(), HOST()],
      D.availability_d(), 200, [A('load_flag', '= ' + ca('Overbooked'), 'bad'), A('load_flag', '= ' + ca('Full day'), 'warn')]),
    T('same_day', 'Same-Day Turns', 'Same-day turns with hours between stays and slack',
      'One row per turn where a guest leaves and another arrives the same day: the hours between the stays and the cleaner; the hours needed, the slack and the timing check fill in by themselves.', [
        C('sd_id', 'Turn ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 24), C('hours_between', 'Hours between stays', 'num', 11), REF('cleaner', 'Cleaner', 'team.name', 24), LST('status', 'Status', 'turnst', 13),
        CA('hours_needed', 'Hours needed', 'num', LKN('units.avg_hours', 'units.name', 'unit'), 10), CA('slack', 'Slack hours', 'num', '{col:hours_between}-{col:hours_needed}', 10),
        CA('slack_flag', 'Timing check', 'text', 'IF({col:slack}<{set:window_buffer_hours},%s,IF({col:slack}<1.5,%s,%s))' % (ca('Too tight'), ca('Tight but possible'), ca('Comfortable')), 17)],
      D.same_day_d(), 150, [A('slack_flag', '= ' + ca('Too tight'), 'bad'), A('slack_flag', '= ' + ca('Tight but possible'), 'warn')]),
    T('deep_cleans', 'Deep Cleans', 'Deep cleans with hours, cost and reason',
      'One row per deep clean, booked or done: unit, date, cleaner, hours, cost and reason; the cost per hour and the days to the date fill in by themselves.', [
        C('dc_id', 'Deep clean ID', 'text', 10, required=True), REF('unit', 'Unit', 'units.name', 24), C('date', 'Date', 'date', 11), REF('cleaner', 'Cleaner', 'team.name', 24), C('hours', 'Hours', 'num', 8), C('cost', 'Cost', 'money', 9),
        LST('reason', 'Reason', 'dreason', 17), CA('cost_per_hour', 'Cost per hour', 'money', 'IF({col:hours}>0,{col:cost}/{col:hours},0)', 11), CA('days_to', 'Days to date', 'int', '{col:date}-{today}', 10), CPH()],
      D.deep_cleans_d(), 100),
    T('unit_tasks', 'Unit Cleaning Tasks', 'Cleaning tasks by unit with minutes and frequency',
      'One row per cleaning task of a unit: the task, the minutes it takes and how often; the hours, the minutes of one turnover for the unit and the share of the task fill in by themselves.', [
        C('task_id', 'Task ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 24), C('task', 'Task', 'text', 30), C('minutes', 'Minutes', 'int', 9), LST('frequency', 'Frequency', 'freq', 15),
        CA('hours', 'Hours', 'num', '{col:minutes}/60', 8),
        CA('unit_minutes', 'Minutes per turnover, unit', 'int', 'SUMIFS({range:unit_tasks.minutes},{range:unit_tasks.unit},{col:unit},{range:unit_tasks.frequency},%s)' % tok('freq', 'Every turnover'), 13),
        CA('task_share', 'Share of the turnover', 'pct', 'IF(AND({col:frequency}=%s,{col:unit_minutes}>0),{col:minutes}/{col:unit_minutes},0)' % tok('freq', 'Every turnover'), 12)],
      D.unit_tasks_d(), 100),
    T('lost_found', 'Lost and Found', 'Lost and found items with status and days open',
      'One row per item a guest left behind: unit, item, guest and status; the days open and the follow-up check fill in by themselves.', [
        C('lf_id', 'Item ID', 'text', 9, required=True), C('date', 'Date found', 'date', 11), REF('unit', 'Unit', 'units.name', 24), C('item', 'Item', 'text', 22), C('guest', 'Guest', 'text', 24), LST('status', 'Status', 'lfst', 12), C('returned_on', 'Returned on', 'date', 12),
        CA('days_open', 'Days open', 'int', 'IF({col:returned_on}>0,{col:returned_on}-{col:date},{today}-{col:date})', 10),
        CA('open_flag', 'Follow-up check', 'text', 'IF(OR({col:status}=%s,{col:status}=%s),IF({col:days_open}>{set:lost_item_days},%s,%s),%s)' % (tok('lfst', 'Found'), tok('lfst', 'Contacted'), cb('Open for days'), cb('Open'), cb('Closed')), 14), COH()],
      D.lost_found_d(), 100, [A('open_flag', '= ' + cb('Open for days'), 'bad'), A('open_flag', '= ' + cb('Open'), 'warn')]),
    T('cleaner_notes', 'Cleaner Notes', 'Cleaner notes with unit, note and follow-up',
      'One row per note a cleaner leaves about a unit: date, cleaner, unit, the note and whether it needs a follow-up; the days since and the follow-up check fill in by themselves.', [
        C('note_id', 'Note ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('cleaner', 'Cleaner', 'team.name', 24), REF('unit', 'Unit', 'units.name', 24), C('note', 'Note', 'text', 30), LST('follow_up', 'Follow-up', 'yn', 9),
        CA('days_ago', 'Days since', 'int', '{today}-{col:date}', 10),
        CA('follow_flag', 'Follow-up check', 'text', 'IF(AND({col:follow_up}=%s,{col:days_ago}<={set:warn_days}*4),%s,%s)' % (YES, cb('Follow up needed'), cb('No follow-up')), 16), CPH()],
      D.cleaner_notes_d(), 120, [A('follow_flag', '= ' + cb('Follow up needed'), 'warn')]),
    T('team', 'Team', 'Team with hours this week, turnovers and pay',
      'The host, the co-host (a helper who handles guests for a fee), cleaners, handypeople and outside contacts; for cleaners the hours this week, turnovers and pay this month fill in.', [
        C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 14), LST('team', 'Team', 'team', 12), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26), C('hours_week', 'Hours a week', 'int', 10),
        C('hourly_rate', 'Hourly rate', 'money', 10), C('speciality', 'Speciality', 'text', 26), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
        CA('week_hours', 'Hours booked this week', 'num', 'SUMIFS({range:turnovers.hours},{range:turnovers.cleaner},{col:name},{range:turnovers.date},">="&%s,{range:turnovers.date},"<"&(%s+7))' % (WK0, WK0), 12),
        CA('week_flag', 'Weekly hours check', 'text', 'IF({col:role}=%s,IF({col:week_hours}>{col:hours_week},%s,%s),%s)' % (tok('role', 'Cleaner'), ca('Over weekly hours'), ca('Within weekly hours'), ca('Not a cleaner')), 18),
        CA('turnovers_month', 'Turnovers this month', 'int', 'COUNTIFS({range:turnovers.cleaner},{col:name},{range:turnovers.date},">="&%s,{range:turnovers.date},"<"&%s)' % (MS, NXT), 11),
        CA('pay_month', 'Pay this month', 'money', 'SUMIFS({range:cleaner_pay.amount},{range:cleaner_pay.cleaner},{col:name},{range:cleaner_pay.month},%s)' % MS, 11)],
      D.team_d(), 50, [A('week_flag', '= ' + ca('Over weekly hours'), 'bad')]),
]
assert len(tables) == 20, len(tables)
for _t in tables: assert len(_t['hint']) <= 200, (_t['key'], len(_t['hint']))
