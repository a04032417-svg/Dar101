"""Short-term rental host suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr8_lists import *
import sr8_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def HOST(): return CA('host_phone', 'Host phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def COH(): return CA('cohost_phone', 'Co-host phone', 'text', '"%s"' % D.COHOST_PHONE, 18)
def ACC(): return CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCT_PHONE, 18)
YES = tok('yn', 'Yes')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'; Y2 = 'DATE(YEAR({today})-2,MONTH({today}),1)'
def W12(rng_): return '{range:pl.unit},{col:name},{range:pl.month},">="&%s,{range:pl.month},"<"&%s' % (Y1, MS)
def PLS(col): return 'SUMIFS({range:pl.%s},%s)' % (col, W12(col))

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('target_occupancy', 'Wanted occupancy', 'pct', 0.65), S('target_margin', 'Wanted profit share of revenue per unit', 'pct', 0.20),
    S('cash_floor', 'Lowest comfortable cash balance', 'money', 12000), S('owner_draw', 'Planned owner draw per month', 'money', 7000), S('tax_set_aside_pct', 'Share of profit set aside for income tax', 'pct', 0.15),
    S('cleaner_rate', 'Cleaner pay per hour', 'money', 17), S('payout_grace_days', 'Days after the expected date before a payout is chased', 'int', 3),
    S('warn_days', 'Days ahead to warn of a deadline', 'int', 7), S('lease_warn_days', 'Days ahead to warn that a lease or loan ends', 'int', 90),
    S('max_payback', 'Longest acceptable payback of a new unit, in months', 'int', 18), S('new_unit_share', 'Share of average unit profit a new unit earns in year one', 'pct', 0.7),
    S('budget_growth', 'Revenue growth planned for the yearly budget', 'pct', 0.05), S('cost_growth', 'Cost growth planned for the yearly budget', 'pct', 0.03),
]
assert 3 <= len(settings) <= 20

FEEP = '(SUM({range:units.fees_12m})/SUM({range:units.revenue_12m}))'
VARN = '(SUM({range:units.varcost_12m})/SUM({range:units.nights_12m}))'
VARSH = '(SUM({range:units.varcost_12m})/SUM({range:units.revenue_12m}))'
OCCN = '(SUM({range:units.nights_12m})/SUM({range:units.avail_12m}))'
CASHNOW = 'SUMIFS({range:cash.closing},{range:cash.month},%s)' % MS
TOT = '({col:revenue}-{col:total_costs})'

tables = [
    T('pl', 'Unit Profit by Month', 'Profit and loss of every unit for every month',
      'One row per unit and month: revenue and each cost; total costs, profit, margin, profit per night and occupancy fill in by themselves. The month in progress shows rent and bills so far.', [
        C('pl_id', 'Row ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('unit', 'Unit', 'units.name', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10),
        C('available_nights', 'Available nights', 'int', 10), C('nights', 'Nights booked', 'int', 10), C('revenue', 'Revenue', 'money', 12), C('platform_fees', 'Platform fees', 'money', 12), C('cleaning', 'Cleaning', 'money', 11),
        C('supplies', 'Supplies', 'money', 11), C('maintenance', 'Maintenance', 'money', 12), C('rent', 'Rent or loan', 'money', 11), C('utilities', 'Utilities', 'money', 11), C('other', 'Other costs', 'money', 11),
        CA('total_costs', 'Total costs', 'money', '{col:platform_fees}+{col:cleaning}+{col:supplies}+{col:maintenance}+{col:rent}+{col:utilities}+{col:other}', 12),
        CA('profit', 'Profit', 'money', '{col:revenue}-{col:total_costs}', 11), CA('margin', 'Margin', 'pct', 'IF({col:revenue}>0,{col:profit}/{col:revenue},0)', 9),
        CA('profit_per_night', 'Profit per night', 'money', 'IF({col:nights}>0,{col:profit}/{col:nights},0)', 11), CA('occupancy', 'Occupancy', 'pct', 'IF({col:available_nights}>0,{col:nights}/{col:available_nights},0)', 10),
        CA('cost_per_night', 'Cost per night', 'money', 'IF({col:nights}>0,{col:total_costs}/{col:nights},0)', 11), CA('be_occ', 'Break-even occupancy', 'pct', LKN('breakeven.be_occ', 'breakeven.unit', 'unit'), 11),
        CA('bills_other', 'Bills, supplies, repairs and other', 'money', '{col:utilities}+{col:supplies}+{col:maintenance}+{col:other}', 14),
        CA('pl_flag', 'Profit check', 'text', 'IF({col:profit}<0,%s,IF({col:margin}<{set:target_margin},%s,%s))' % (cf('Loss'), cf('Margin too thin'), cf('Profit on target')), 15)],
      D.pl_d(), 400, [A('pl_flag', '= ' + cf('Loss'), 'bad'), A('pl_flag', '= ' + cf('Margin too thin'), 'warn'), A('margin', '> 0.6', 'good')]),
    T('units', 'Units', 'Units with profit and margin of the last 12 months',
      'One row per unit with its fixed costs; revenue, costs, profit, margin, occupancy, break-even check, platform fees against last year and the yearly budget fill in by themselves.', [
        C('unit_id', 'Unit ID', 'text', 9, required=True), C('name', 'Name', 'text', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), C('bedrooms', 'Bedrooms', 'int', 9),
        C('owner', 'Owner', 'text', 22), C('owner_phone', 'Owner phone', 'text', 18), C('base_rate', 'Base rate', 'money', 11), C('rent', 'Rent per month', 'money', 11), C('utilities', 'Utilities per month', 'money', 11),
        C('internet', 'Internet per month', 'money', 11), C('mgmt_pct', 'Management fee', 'pct', 10), C('since', 'Listed since', 'date', 11), C('review_on', 'Next review', 'date', 11),
        CA('revenue_12m', 'Revenue, 12 months', 'money', PLS('revenue'), 13), CA('fees_12m', 'Platform fees, 12 months', 'money', PLS('platform_fees'), 13),
        CA('varcost_12m', 'Cleaning, supplies, repairs, 12 months', 'money', '%s+%s+%s' % (PLS('cleaning'), PLS('supplies'), PLS('maintenance')), 14), CA('costs_12m', 'Total costs, 12 months', 'money', PLS('total_costs'), 13),
        CA('profit_12m', 'Profit, 12 months', 'money', '{col:revenue_12m}-{col:costs_12m}', 12), CA('margin_12m', 'Margin, 12 months', 'pct', 'IF({col:revenue_12m}>0,{col:profit_12m}/{col:revenue_12m},0)', 10),
        CA('nights_12m', 'Nights, 12 months', 'int', PLS('nights'), 10), CA('avail_12m', 'Available nights, 12 months', 'int', PLS('available_nights'), 11),
        CA('occ_12m', 'Occupancy, 12 months', 'pct', 'IF({col:avail_12m}>0,{col:nights_12m}/{col:avail_12m},0)', 11), CA('profit_per_night', 'Profit per night', 'money', 'IF({col:nights_12m}>0,{col:profit_12m}/{col:nights_12m},0)', 11),
        CA('fees_prev12', 'Platform fees, year before', 'money', 'SUMIFS({range:pl.platform_fees},{range:pl.unit},{col:name},{range:pl.month},">="&%s,{range:pl.month},"<"&%s)' % (Y2, Y1), 13),
        CA('fees_change', 'Platform fees against year before', 'pct', 'IF({col:fees_prev12}>=0.5*{col:fees_12m},{col:fees_12m}/{col:fees_prev12}-1,0)', 12),
        CA('be_occ', 'Break-even occupancy', 'pct', LKN('breakeven.be_occ', 'breakeven.unit', 'name'), 11),
        CA('be_flag', 'Break-even check', 'text', LKT('breakeven.be_flag', 'breakeven.unit', 'name'), 17),
        CA('unit_flag', 'Profit check', 'text', 'IF({col:profit_12m}<0,%s,IF({col:margin_12m}<{set:target_margin},%s,%s))' % (cf('Loss'), cf('Margin too thin'), cf('Profit on target')), 15),
        CA('rev_budget', 'Revenue budget, next 12 months', 'money', 'ROUND({col:revenue_12m}*(1+{set:budget_growth}),0)', 14), CA('cost_budget', 'Cost budget, next 12 months', 'money', 'ROUND({col:costs_12m}*(1+{set:cost_growth}),0)', 14),
        CA('profit_budget', 'Profit budget, next 12 months', 'money', '{col:rev_budget}-{col:cost_budget}', 14), HOST(), COH(), ACC()],
      D.units_d(), 50, [A('unit_flag', '= ' + cf('Loss'), 'bad'), A('unit_flag', '= ' + cf('Margin too thin'), 'warn'), A('be_flag', '= ' + cf('Cannot break even'), 'bad'), A('fees_change', '> 0.1', 'warn')]),
    T('bookings', 'Bookings', 'Bookings with channel, earnings and platform fee',
      'A sample of bookings: unit, channel, dates, what the stay earned and the platform fee; the fee share, the amount kept and the earning per night fill in by themselves.', [
        C('booking_id', 'Booking ID', 'text', 10, required=True), REF('unit', 'Unit', 'units.name', 26), LST('city', 'City', 'city', 10), LST('channel', 'Channel', 'chan', 11), C('guest', 'Guest', 'text', 24),
        C('guest_country', 'Guest country', 'text', 16), C('check_in', 'Check-in', 'date', 11), C('check_out', 'Check-out', 'date', 11), C('nights', 'Nights', 'int', 8), C('room_revenue', 'Room revenue', 'money', 12),
        C('cleaning_fee', 'Cleaning fee', 'money', 11), C('earned', 'Earned', 'money', 11), C('platform_fee', 'Platform fee', 'money', 11), LST('status', 'Status', 'bstatus', 11),
        CA('fee_pct', 'Fee share', 'pct', 'IF({col:earned}>0,{col:platform_fee}/{col:earned},0)', 9), CA('kept', 'Kept after fee', 'money', '{col:earned}-{col:platform_fee}', 12),
        CA('earned_per_night', 'Earned per night', 'money', 'IF({col:nights}>0,{col:earned}/{col:nights},0)', 11)],
      D.bookings_d(), 700, [A('status', '= ' + tok('bstatus', 'Cancelled'), 'bad'), A('fee_pct', '> 0.14', 'warn'), A('fee_pct', '< 0.05', 'good')]),
    T('payouts', 'Payouts', 'Payouts with the days late and the amount missing',
      'One row per payout: the money a booking platform sends the host after a stay starts, with expected date and amount; days late, the amount still missing and the payout check fill in by themselves.', [
        C('payout_id', 'Payout ID', 'text', 10, required=True), C('booking_id', 'Booking ID', 'text', 10), LST('channel', 'Channel', 'chan', 11), REF('unit', 'Unit', 'units.name', 26), C('expected_date', 'Expected date', 'date', 11),
        C('paid_on', 'Paid on', 'date', 11), C('expected_amount', 'Expected amount', 'money', 12), C('received_amount', 'Received amount', 'money', 12), LST('status', 'Status', 'payst', 11),
        CA('days_late', 'Days late', 'int', 'IF({col:status}=%s,0,IF({col:paid_on}=0,MAX(0,{today}-{col:expected_date}),MAX(0,{col:paid_on}-{col:expected_date})))' % tok('payst', 'Scheduled'), 9),
        CA('gap', 'Amount missing', 'money', 'IF({col:status}=%s,0,{col:expected_amount}-{col:received_amount})' % tok('payst', 'Scheduled'), 12),
        CA('pay_flag', 'Payout check', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:status}=%s,IF({col:expected_date}<{today}-{set:payout_grace_days},%s,%s),IF({col:days_late}>{set:payout_grace_days},%s,%s))))' % (
            tok('payst', 'Missing'), cf('Payout missing'), tok('payst', 'Short paid'), cf('Payout short'), tok('payst', 'Scheduled'), cf('Payout late'), cf('Payout expected'), cf('Payout late'), cf('Payout on time')), 15), HOST()],
      D.payouts_d(), 600, [A('pay_flag', '= ' + cf('Payout missing'), 'bad'), A('pay_flag', '= ' + cf('Payout late'), 'bad'), A('pay_flag', '= ' + cf('Payout short'), 'warn'), A('pay_flag', '= ' + cf('Payout on time'), 'good')]),
    T('expenses', 'Expenses', 'Overheads and unit costs with the month calculated',
      'All business overheads and a sample of unit costs: date, unit, category, description, amount and who was paid; the month fills in by itself.', [
        C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('unit', 'Unit', 'text', 26), LST('category', 'Category', 'ecat', 20), C('description', 'Description', 'text', 28),
        C('amount', 'Amount', 'money', 11), C('paid_to', 'Paid to', 'text', 24), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), ACC()],
      D.expenses_d(), 700, [A('amount', '> 1000', 'warn')]),
    T('cash', 'Cash Months', 'Cash by month: money in, money out and the closing balance',
      'One row per month: opening cash, money in and each kind of money out; total out, closing cash, months of cover, the floor check, the month profit and the safe owner draw fill in by themselves.', [
        C('cash_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('opening', 'Opening cash', 'money', 12), C('cash_in', 'Cash in', 'money', 12), C('expenses', 'Expenses paid', 'money', 12),
        C('cleaners', 'Cleaners paid', 'money', 11), C('supplies', 'Supplies paid', 'money', 11), C('maintenance', 'Maintenance paid', 'money', 12), C('cohost_fees', 'Co-host fees paid', 'money', 12),
        C('owner_payouts', 'Owner payouts', 'money', 12), C('local_taxes', 'Local taxes paid', 'money', 12), C('owner_draw', 'Owner draw', 'money', 11),
        CA('total_out', 'Total cash out', 'money', '{col:expenses}+{col:cleaners}+{col:supplies}+{col:maintenance}+{col:cohost_fees}+{col:owner_payouts}+{col:local_taxes}+{col:owner_draw}', 12),
        CA('net_flow', 'Net cash flow', 'money', '{col:cash_in}-{col:total_out}', 12), CA('closing', 'Closing cash', 'money', '{col:opening}+{col:net_flow}', 12),
        CA('cover', 'Months of cover', 'num', 'IFERROR({col:closing}/AVERAGE({range:cash.total_out}),0)', 9),
        CA('cash_flag', 'Cash check', 'text', 'IF({col:closing}<{set:cash_floor},%s,IF({col:closing}<2*{set:cash_floor},%s,%s))' % (cf('Below the floor'), cf('Near the floor'), cf('Above the floor')), 15),
        CA('pl_revenue', 'Revenue of the month', 'money', 'SUMIFS({range:pl.revenue},{range:pl.month},{col:month})', 12), CA('pl_costs', 'Costs of the month', 'money', 'SUMIFS({range:pl.total_costs},{range:pl.month},{col:month})', 12),
        CA('pl_profit', 'Profit of the month', 'money', '{col:pl_revenue}-{col:pl_costs}', 12),
        CA('safe_draw', 'Safe owner draw', 'money', 'MAX(0,MIN({col:pl_profit}*(1-{set:tax_set_aside_pct}),{col:closing}-{set:cash_floor}))', 12), HOST(), ACC()],
      D.cash_d(), 50, [A('cash_flag', '= ' + cf('Below the floor'), 'bad'), A('cash_flag', '= ' + cf('Near the floor'), 'warn'), A('net_flow', '< 0', 'warn')]),
    T('forecast', 'Cash Forecast', 'Cash forecast for the next 13 weeks with the floor warning',
      'One row per week: expected payouts, costs, owner payments, local tax and owner draw; the opening and closing balance, the gap to your cash floor and the floor check fill in by themselves.', [
        C('fc_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), C('expected_payouts', 'Expected payouts', 'money', 13), C('expected_costs', 'Expected costs', 'money', 12),
        C('owner_payments', 'Owner payments', 'money', 12), C('local_tax', 'Local tax', 'money', 11), C('owner_draw', 'Owner draw', 'money', 11),
        CA('net', 'Net for the week', 'money', '{col:expected_payouts}-{col:expected_costs}-{col:owner_payments}-{col:local_tax}-{col:owner_draw}', 12),
        CA('opening', 'Opening balance', 'money', CASHNOW + '+SUMIFS({range:forecast.net},{range:forecast.week},"<"&{col:week})', 13), CA('closing', 'Closing balance', 'money', '{col:opening}+{col:net}', 13),
        CA('floor', 'Cash floor', 'money', '{set:cash_floor}', 11), CA('gap_to_floor', 'Gap to the floor', 'money', '{col:closing}-{col:floor}', 12),
        CA('floor_flag', 'Floor check', 'text', 'IF({col:closing}<{col:floor},%s,IF({col:closing}<2*{col:floor},%s,%s))' % (cf('Below the floor'), cf('Near the floor'), cf('Above the floor')), 15), HOST()],
      D.forecast_d(), 50, [A('floor_flag', '= ' + cf('Below the floor'), 'bad'), A('floor_flag', '= ' + cf('Near the floor'), 'warn'), A('net', '< -5000', 'warn')]),
    T('cleaner_pay', 'Cleaner Pay', 'Cleaner pay by month with cost per turnover',
      'One row per cleaner and month: turnovers (the clean and reset between two stays), hours and pay; the cost per turnover, the hourly pay and the pay check fill in by themselves.', [
        C('pay_id', 'Pay ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), REF('cleaner', 'Cleaner', 'team.name', 22), C('turnovers', 'Turnovers', 'int', 10), C('hours', 'Hours', 'num', 9), C('amount', 'Amount', 'money', 11),
        CA('per_turnover', 'Cost per turnover', 'money', 'IF({col:turnovers}>0,{col:amount}/{col:turnovers},0)', 11), CA('hourly', 'Hourly pay', 'money', 'IF({col:hours}>0,{col:amount}/{col:hours},0)', 10),
        CA('hours_per_turnover', 'Hours per turnover', 'num', 'IF({col:turnovers}>0,{col:hours}/{col:turnovers},0)', 10),
        CA('pay_flag', 'Pay check', 'text', 'IF({col:hourly}>{set:cleaner_rate}*1.05,%s,IF({col:hourly}<{set:cleaner_rate}*0.95,%s,%s))' % (cg('Pay above rate'), cg('Pay below rate'), cg('Pay in line with rate')), 18),
        CA('cleaner_phone', 'Cleaner phone', 'text', LKT('team.phone', 'team.name', 'cleaner'), 18)],
      D.cleaner_pay_d(), 150, [A('pay_flag', '= ' + cg('Pay above rate'), 'warn'), A('per_turnover', '> 90', 'warn')]),
    T('supplies', 'Supply Purchases', 'Supply purchases with the month calculated',
      'One row per purchase of linen, toiletries, kitchen items and cleaning products: date, item, quantity and amount; the month and the purchase size check fill in by themselves.', [
        C('purchase_id', 'Purchase ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('item', 'Item', 'text', 26), LST('category', 'Category', 'scat', 18), C('qty', 'Quantity', 'int', 9), C('unit_cost', 'Cost each', 'money', 10),
        C('amount', 'Amount', 'money', 11), C('supplier', 'Supplier', 'text', 22), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
        CA('size_flag', 'Size check', 'text', 'IF({col:amount}>=100,%s,%s)' % (cg('Big purchase'), cg('Normal purchase')), 15)],
      D.supplies_d(), 400, [A('size_flag', '= ' + cg('Big purchase'), 'warn')]),
    T('maint', 'Maintenance Costs', 'Maintenance costs by repair with parts and labour',
      'One row per finished repair: unit, kind, date, parts and labour; the total cost, the month, the labour share and the size check fill in by themselves.', [
        C('ticket_id', 'Ticket ID', 'text', 10, required=True), REF('unit', 'Unit', 'units.name', 26), C('kind', 'Kind', 'text', 16), C('done_on', 'Done on', 'date', 11), REF('handyperson', 'Handyperson', 'team.name', 22),
        C('parts_cost', 'Parts', 'money', 10), C('labour_cost', 'Labour', 'money', 10), C('cost', 'Cost', 'money', 10), CA('month', 'Month', 'date', 'DATE(YEAR({col:done_on}),MONTH({col:done_on}),1)', 11),
        CA('labour_share', 'Labour share', 'pct', 'IF({col:cost}>0,{col:labour_cost}/{col:cost},0)', 10), CA('size_flag', 'Size check', 'text', 'IF({col:cost}>300,%s,%s)' % (cg('Repair above 300'), cg('Repair under 300')), 15),
        CA('handyperson_phone', 'Handyperson phone', 'text', LKT('team.phone', 'team.name', 'handyperson'), 18)],
      D.maint_d(), 300, [A('size_flag', '= ' + cg('Repair above 300'), 'warn')]),
    T('statements', 'Owner Statements', 'Owner statements with the management fee',
      'One row per owner and month: revenue, platform fees, management fee and the net owed to the owner; the host share, the days to pay and the statement check fill in by themselves.', [
        C('statement_id', 'Statement ID', 'text', 11, required=True), C('month', 'Month', 'date', 11), C('owner', 'Owner', 'text', 22), C('owner_phone', 'Owner phone', 'text', 18), C('revenue', 'Revenue', 'money', 12),
        C('platform_fees', 'Platform fees', 'money', 12), C('mgmt_pct', 'Management fee share', 'pct', 11), C('mgmt_fee', 'Management fee', 'money', 12), C('net_to_owner', 'Net to owner', 'money', 12), LST('status', 'Status', 'stmst', 10),
        C('paid_on', 'Paid on', 'date', 11), CA('host_share', 'Host share of revenue', 'pct', 'IF({col:revenue}>0,{col:mgmt_fee}/{col:revenue},0)', 11),
        CA('days_to_pay', 'Days from month start to payment', 'int', 'IF({col:paid_on}=0,0,{col:paid_on}-{col:month})', 12),
        CA('stmt_flag', 'Statement check', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,IF({today}-{col:month}>45,%s,%s),%s))' % (tok('stmst', 'Paid'), cg('Statement paid'), tok('stmst', 'Sent'), cg('Statement overdue'), cg('Statement sent'), cg('Statement draft')), 17), ACC()],
      D.statements_d(), 80, [A('stmt_flag', '= ' + cg('Statement overdue'), 'bad'), A('stmt_flag', '= ' + cg('Statement draft'), 'warn')]),
    T('cohost', 'Co-host Fees', 'Co-host fees on the net revenue of their units',
      'One row per month: net revenue of the units the co-host handles, the fee share and the fee amount; the share check and the fee against the revenue fill in by themselves.', [
        C('fee_id', 'Fee ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('units', 'Units', 'int', 8), C('net_revenue', 'Net revenue', 'money', 12), C('fee_pct', 'Fee share', 'pct', 9), C('fee_amount', 'Fee amount', 'money', 12),
        LST('status', 'Status', 'stmst', 10), C('paid_on', 'Paid on', 'date', 11), CA('share', 'Fee against net revenue', 'pct', 'IF({col:net_revenue}>0,{col:fee_amount}/{col:net_revenue},0)', 11),
        CA('share_flag', 'Share check', 'text', 'IF(ABS({col:share}-{col:fee_pct})<0.002,%s,%s)' % (cg('Fee on agreed share'), cg('Fee differs from share')), 17), COH()],
      D.cohost_d(), 60, [A('share_flag', '= ' + cg('Fee differs from share'), 'warn')]),
    T('localtax', 'Local Tax', 'Local occupancy tax by month and city',
      'One row per city and month: the tax collected from guests (a tax on each night), the part the host must remit, what was remitted and the due date; the amount left and the check fill in by themselves.', [
        C('tax_id', 'Tax ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('city', 'City', 'city', 10), C('nights', 'Nights', 'int', 8), C('room_revenue', 'Room revenue', 'money', 12), C('tax_pct', 'Tax share', 'pct', 9),
        C('tax_collected', 'Tax collected', 'money', 12), C('collected_by_host', 'Collected by the host', 'money', 12), C('remitted', 'Remitted', 'money', 11), C('due_date', 'Due date', 'date', 11), LST('status', 'Status', 'taxst', 14), C('paid_on', 'Paid on', 'date', 11),
        CA('left_to_remit', 'Left to remit', 'money', '{col:collected_by_host}-{col:remitted}', 11),
        CA('tax_flag', 'Tax check', 'text', 'IF({col:left_to_remit}<=0.01,IF({col:collected_by_host}=0,%s,%s),IF({col:due_date}<{today},%s,IF({col:due_date}<={today}+{set:warn_days},%s,%s)))' % (
            cg('Nothing to remit'), cg('Filed and paid'), cg('Remit overdue'), cg('Remit soon'), cg('Collected, not yet remitted')), 24), ACC()],
      D.tax_d(), 150, [A('tax_flag', '= ' + cg('Remit overdue'), 'bad'), A('tax_flag', '= ' + cg('Remit soon'), 'warn')]),
    T('taxset', 'Income Tax Set-Aside', 'Income tax set-aside by month with the balance held',
      'One row per month: profit for tax, the amount you set aside and any payment made; the target, the shortfall, the balance held and the funding check fill in by themselves.', [
        C('ts_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('profit', 'Profit for tax', 'money', 12), C('set_aside', 'Set aside', 'money', 11), C('paid_amount', 'Paid', 'money', 11), C('paid_on', 'Paid on', 'date', 11),
        C('review_on', 'Review on', 'date', 11), CA('target', 'Target set-aside', 'money', 'MAX(0,{col:profit})*{set:tax_set_aside_pct}', 12), CA('shortfall', 'Shortfall', 'money', '{col:target}-{col:set_aside}', 11),
        CA('balance', 'Balance held', 'money', 'SUMIFS({range:taxset.set_aside},{range:taxset.month},"<="&{col:month})-SUMIFS({range:taxset.paid_amount},{range:taxset.month},"<="&{col:month})', 12),
        CA('fund_flag', 'Funding check', 'text', 'IF({col:set_aside}>={col:target}*0.99,%s,%s)' % (cf('Fully funded'), cf('Underfunded')), 14), ACC(), HOST()],
      D.taxset_d(), 50, [A('fund_flag', '= ' + cf('Underfunded'), 'warn'), A('fund_flag', '= ' + cf('Fully funded'), 'good')]),
    T('draws', 'Owner Draws', 'Owner draws by month with the safe limit',
      'One row per month: the amount the host took and why; the gap to the plan, the safe draw of that month and the draw check fill in by themselves.', [
        C('draw_id', 'Draw ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('amount', 'Amount', 'money', 11), LST('reason', 'Reason', 'dreason', 26),
        CA('vs_plan', 'Against plan', 'money', '{col:amount}-{set:owner_draw}', 11), CA('safe', 'Safe draw of the month', 'money', 'SUMIFS({range:cash.safe_draw},{range:cash.month},{col:month})', 12),
        CA('draw_flag', 'Draw check', 'text', 'IF({col:amount}<={col:safe},%s,%s)' % (cf('Draw within safe limit'), cf('Draw above safe limit')), 20), HOST()],
      D.draws_d(), 50, [A('draw_flag', '= ' + cf('Draw above safe limit'), 'warn')]),
    T('loans', 'Loans and Leases', 'Loans and leases with the months left',
      'One row per lease or loan: lender, monthly payment, balance and end date; months left, payments still to make and the end check fill in by themselves.', [
        C('loan_id', 'Loan ID', 'text', 9, required=True), C('item', 'Item', 'text', 34), LST('kind', 'Kind', 'lkind', 15), C('lender', 'Lender', 'text', 24), C('monthly_payment', 'Monthly payment', 'money', 12), C('balance', 'Balance', 'money', 11),
        C('end_date', 'End date', 'date', 11), C('review_on', 'Review on', 'date', 11), CA('days_left', 'Days left', 'int', '{col:end_date}-{today}', 9), CA('months_left', 'Months left', 'int', 'MAX(0,ROUND({col:days_left}/30.4,0))', 9),
        CA('payments_left', 'Payments still to make', 'money', '{col:monthly_payment}*{col:months_left}', 13),
        CA('end_flag', 'End check', 'text', 'IF({col:days_left}<0,%s,IF({col:days_left}<={set:lease_warn_days},%s,%s))' % (cf('Lease ended'), cf('Lease ends soon'), cf('Lease running')), 15), HOST()],
      D.loans_d(), 50, [A('end_flag', '= ' + cf('Lease ends soon'), 'warn'), A('end_flag', '= ' + cf('Lease ended'), 'bad')]),
    T('growth', 'Growth Scenarios', 'Growth scenarios with the extra yearly profit',
      'One row per scenario: units added, rate change, occupancy change and cost change; the gain from each, the extra yearly profit and the scenario check fill in by themselves from your last 12 months.', [
        C('scn_id', 'Scenario ID', 'text', 10, required=True), LST('scenario', 'Scenario', 'scn', 28), C('units_added', 'Units added', 'int', 9), C('rate_change', 'Rate change', 'pct', 9), C('occupancy_change', 'Occupancy change', 'pct', 11),
        C('cost_change', 'Cost change', 'pct', 9), C('review_on', 'Review on', 'date', 11),
        CA('rate_gain', 'Profit from rates', 'money', 'SUM({range:units.revenue_12m})*{col:rate_change}*(1-%s)' % FEEP, 12),
        CA('occ_gain', 'Profit from occupancy', 'money', 'SUM({range:units.revenue_12m})*({col:occupancy_change}/%s)*(1-%s-%s)' % (OCCN, FEEP, VARSH), 12),
        CA('unit_gain', 'Profit from units', 'money', 'IF({col:units_added}>=0,{col:units_added}*SUM({range:units.profit_12m})/COUNT({range:units.profit_12m})*{set:new_unit_share},-(SMALL({range:units.profit_12m},1)+IF({col:units_added}<=-2,SMALL({range:units.profit_12m},2),0)))', 12),
        CA('cost_effect', 'Profit from costs', 'money', '-{col:cost_change}*SUM({range:units.costs_12m})', 12), CA('extra_profit', 'Extra yearly profit', 'money', '{col:rate_gain}+{col:occ_gain}+{col:unit_gain}+{col:cost_effect}', 13),
        CA('scn_flag', 'Scenario check', 'text', 'IF({col:extra_profit}>=0.05*SUM({range:units.profit_12m}),%s,IF({col:extra_profit}>0,%s,%s))' % (cg('Scenario adds profit'), cg('Scenario small gain'), cg('Scenario loses profit')), 18), HOST()],
      D.growth_d(), 50, [A('scn_flag', '= ' + cg('Scenario adds profit'), 'good'), A('scn_flag', '= ' + cg('Scenario loses profit'), 'bad')]),
    T('pipeline', 'Unit Pipeline', 'Unit ideas with the yearly profit and the payback',
      'One row per unit idea: city, bedrooms, expected rate and occupancy, set-up cost and rent; the yearly profit, the margin, the payback in months and the check fill in by themselves.', [
        C('idea_id', 'Idea ID', 'text', 9, required=True), C('idea', 'Unit idea', 'text', 32), LST('city', 'City', 'city', 10), C('bedrooms', 'Bedrooms', 'int', 9), C('expected_rate', 'Expected earning per night', 'money', 12),
        C('expected_occ', 'Expected occupancy', 'pct', 10), C('setup_cost', 'Set-up cost', 'money', 11), C('rent', 'Rent per month', 'money', 11), C('running_cost', 'Bills per month', 'money', 11), C('decide_on', 'Decide by', 'date', 11),
        CA('revenue_year', 'Revenue per year', 'money', 'ROUND(365*{col:expected_occ},0)*{col:expected_rate}', 12),
        CA('yearly_profit', 'Profit per year', 'money', '{col:revenue_year}*(1-%s)-ROUND(365*{col:expected_occ},0)*%s-12*({col:rent}+{col:running_cost})' % (FEEP, VARN), 12),
        CA('margin', 'Margin', 'pct', 'IF({col:revenue_year}>0,{col:yearly_profit}/{col:revenue_year},0)', 9), CA('payback', 'Payback in months', 'num', 'IF({col:yearly_profit}>0,ROUND({col:setup_cost}/{col:yearly_profit}*12,1),0)', 10),
        CA('pipe_flag', 'Payback check', 'text', 'IF({col:yearly_profit}<=0,%s,IF({col:payback}<={set:max_payback},%s,%s))' % (cf('Does not pay back'), cf('Pays back fast'), cf('Pays back slowly')), 17), HOST()],
      D.pipeline_d(), 50, [A('pipe_flag', '= ' + cf('Pays back fast'), 'good'), A('pipe_flag', '= ' + cf('Does not pay back'), 'bad'), A('pipe_flag', '= ' + cf('Pays back slowly'), 'warn')]),
    T('breakeven', 'Break-Even Rows', 'Break-even occupancy and rate for every unit',
      'One row per unit: fixed cost a month, cost per booked night, earning per night and fee share; break-even occupancy and rate, the cushion over today and the check fill in by themselves.', [
        C('be_id', 'Row ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), C('fixed_cost', 'Fixed cost per month', 'money', 12), C('var_cost', 'Cost per booked night', 'money', 11), C('rate', 'Earned per night', 'money', 11),
        C('fee_pct', 'Platform fee share', 'pct', 10), C('review_on', 'Review on', 'date', 11),
        CA('margin_night', 'Kept per night after cost', 'money', '{col:rate}*(1-{col:fee_pct})-{col:var_cost}', 12),
        CA('be_occ', 'Break-even occupancy', 'pct', 'IF({col:margin_night}>0,{col:fixed_cost}/({col:margin_night}*30.4),9.99)', 11),
        CA('be_rate', 'Break-even rate at wanted occupancy', 'money', '({col:fixed_cost}/(30.4*{set:target_occupancy})+{col:var_cost})/(1-{col:fee_pct})', 13), CA('rate_gap', 'Earning against break-even rate', 'money', '{col:rate}-{col:be_rate}', 12),
        CA('occ_now', 'Occupancy, 12 months', 'pct', LKN('units.occ_12m', 'units.name', 'unit'), 11), CA('cushion', 'Cushion over break-even', 'pct', '{col:occ_now}-{col:be_occ}', 11),
        CA('be_flag', 'Break-even check', 'text', 'IF({col:be_occ}>1,%s,IF({col:occ_now}>={col:be_occ},%s,%s))' % (cf('Cannot break even'), cf('Above break-even'), cf('Below break-even')), 17), CA('owner_phone', 'Owner phone', 'text', LKT('units.owner_phone', 'units.name', 'unit'), 18)],
      D.breakeven_d(), 50, [A('be_flag', '= ' + cf('Cannot break even'), 'bad'), A('be_flag', '= ' + cf('Below break-even'), 'warn'), A('be_flag', '= ' + cf('Above break-even'), 'good')]),
    T('team', 'Team', 'Team with cleaner pay and repair costs',
      'The host, the co-host (a helper who handles guests for a fee), four cleaners, two handypeople and four outside contacts; cleaner pay and repair cost of the last 12 months fill in by themselves.', [
        C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 14), LST('team', 'Team', 'team', 12), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
        C('hours_week', 'Hours a week', 'int', 10), C('hourly_rate', 'Hourly rate', 'money', 10), C('speciality', 'Speciality', 'text', 26), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
        CA('pay_12m', 'Cleaner pay, 12 months', 'money', 'SUMIFS({range:cleaner_pay.amount},{range:cleaner_pay.cleaner},{col:name},{range:cleaner_pay.month},">="&%s,{range:cleaner_pay.month},"<"&%s)' % (Y1, MS), 12),
        CA('repairs_12m', 'Repair cost, 12 months', 'money', 'SUMIFS({range:maint.cost},{range:maint.handyperson},{col:name},{range:maint.done_on},">="&%s,{range:maint.done_on},"<"&%s)' % (Y1, MS), 12)],
      D.team_d(), 50),
]
assert len(tables) == 20, len(tables)
for _t in tables: assert len(_t['hint']) <= 200, (_t['key'], len(_t['hint']))
