"""Childcare center suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc8_lists import *
import cc8_data as D


def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def CONST(key_, label, value, w=16): return CA(key_, label, 'text', '"%s"' % value, w)
def NAMEC(key_, label, who, w=14): return CA(key_, label, 'text', tok('person', who), w)
def CENTER(): return CA('center', 'Center', 'text', '{set:company}', 22)
def OWN(): return CA('owner', 'Owner-director', 'text', '{set:owner_name}', 14)
def OWNER_PH(): return CONST('owner_phone', 'Owner-director phone', D.OWNER_PHONE, 18)
def DIR(): return NAMEC('director', 'Assistant director', 'Tobias')
def DIR_PH(): return CONST('director_phone', 'Assistant director phone', D.DIRECTOR_PHONE, 18)
def ACC(): return NAMEC('accountant', 'Accountant', 'Eleni')
def ACC_PH(): return CONST('accountant_phone', 'Accountant phone', D.ACC_PHONE, 18)
def MNT(): return NAMEC('maintenance', 'Maintenance contact', 'Dae-ho')
def MNT_PH(): return CONST('maint_phone', 'Maintenance phone', D.MAINT_PHONE, 18)

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
RT = {r: tok('room', r) for r in ROOMS}
def WN(t, n, c='month'): return '{range:%s.%s},">="&EDATE(%s,-%d),{range:%s.%s},"<"&%s' % (t, c, MS, n, t, c, MS)
def SN(t, col, n): return 'SUMIFS({range:%s.%s},%s)' % (t, col, WN(t, n))
def BYM(t, col): return 'SUMIFS({range:%s.%s},{range:%s.month},{col:month})' % (t, col, t)
HOURLY = tok('paytype', 'Hourly')

settings = [
    S('company', 'Your center name', 'text', COMPANY), S('owner_name', 'Your first name for messages', 'text', D.FIRST(OWNER)),
    S('occupancy_target', 'Wanted occupancy, children booked of licensed places', 'pct', OCC_TARGET), S('staff_share_target', 'Highest staff pay share of revenue you accept, set your own', 'pct', STAFF_SHARE_TARGET),
    S('margin_target', 'Wanted profit margin, set your own', 'pct', 0.12), S('cash_floor', 'Lowest cash balance you want', 'money', CASH_FLOOR),
    S('tax_set_aside_pct', 'Income tax set-aside share, confirm with your adviser', 'pct', TAX_SET_ASIDE_PCT), S('owner_draw', 'Owner draw a month', 'money', OWNER_DRAW),
    S('owner_extra', 'Extra owner draw each quarter', 'money', OWNER_EXTRA), S('extra_draw_month', 'Month number of the first extra draw in a quarter, 1 to 3', 'int', 3),
    S('fee_review_date', 'Date of your yearly fee review', 'date', ahead(45)), S('steady_band', 'Change counted as steady, share', 'pct', 0.03),
    S('variance_pct', 'Budget variance that needs a look, share of the budget', 'pct', 0.05), S('home_rooms_total', 'Rooms in the home, for a home daycare', 'int', 7),
    S('home_rooms_used', 'Rooms used for the business', 'int', 2), S('home_hours_used', 'Hours a week those rooms are used for the business', 'int', 55),
    S('home_hours_week', 'Hours in the week used for the share', 'int', 168)
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 profit and loss
tables.append(T('pnl', 'Profit and Loss', 'Monthly profit and loss',
    'One row per month: tuition and fee revenue, staff pay, owner pay, food, rent and other costs, paid staff hours and child-days; revenue, costs, profit, margin and the shares fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), C('tuition_revenue', 'Tuition revenue', 'money', 13), C('fee_revenue', 'Fee revenue', 'money', 12), C('government_part', 'Government part of tuition', 'money', 13),
    C('staff_pay', 'Staff pay', 'money', 12), C('owner_pay', 'Owner pay', 'num', 11), C('food', 'Food', 'money', 11), C('rent', 'Rent', 'num', 11), C('other_costs', 'Other costs', 'money', 12),
    C('staff_hours', 'Paid staff hours', 'num', 11), C('child_days', 'Child-days attended', 'int', 11),
    CA('revenue', 'Revenue', 'money', '{col:tuition_revenue}+{col:fee_revenue}', 12), CA('costs', 'Costs', 'money', '{col:staff_pay}+{col:owner_pay}+{col:food}+{col:rent}+{col:other_costs}', 12),
    CA('profit', 'Profit', 'money', '{col:revenue}-{col:costs}', 12), CA('margin', 'Profit margin', 'pct', 'IF({col:revenue}>0,{col:profit}/{col:revenue},0)', 10),
    CA('staff_share', 'Staff pay share of revenue', 'pct', 'IF({col:revenue}>0,{col:staff_pay}/{col:revenue},0)', 11), CA('rent_share', 'Rent share of revenue', 'pct', 'IF({col:revenue}>0,{col:rent}/{col:revenue},0)', 10),
    CA('food_share', 'Food share of revenue', 'pct', 'IF({col:revenue}>0,{col:food}/{col:revenue},0)', 10), CA('food_per_day', 'Food cost per child-day', 'money', 'IF({col:child_days}>0,{col:food}/{col:child_days},0)', 11),
    CA('staff_hour', 'Staff pay per paid hour', 'money', 'IF({col:staff_hours}>0,{col:staff_pay}/{col:staff_hours},0)', 11),
    CA('result', 'Month result', 'text', 'IF({col:profit}<0,%s,IF({col:margin}<{set:margin_target},%s,%s))' % (V('Loss month'), V('Below margin target'), V('On margin target')), 18),
    CENTER(), OWN(), OWNER_PH(), DIR(), DIR_PH(), ACC(), ACC_PH()],
    D.pnl_d(), 60, [A('result', '= ' + V('Loss month'), 'bad'), A('result', '= ' + V('Below margin target'), 'warn'), A('staff_share', '> {set:staff_share_target}', 'warn')]))
# ---------------------------------------------------------------- 2 room profit by month
RMW = lambda n: WN('room_months', n)
tables.append(T('room_months', 'Room Profit by Month', 'Profit by room and month',
    'One row per room and month: children enrolled, revenue, staff cost, food cost and the room share of overhead; places, occupancy, cost, profit, the children still needed to break even and the profit under three overhead rules fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('room', 'Room', 'room', 12), C('enrolled', 'Children enrolled', 'int', 10), C('revenue', 'Revenue', 'money', 12), C('staff_cost', 'Staff cost', 'money', 12),
    C('food_cost', 'Food cost', 'money', 11), C('overhead_share', 'Overhead share', 'money', 12),
    CA('capacity', 'Licensed places', 'int', 'SUMIFS({range:rooms.capacity},{range:rooms.room},{col:room})', 9), CA('occupancy', 'Occupancy', 'pct', 'IF({col:capacity}>0,{col:enrolled}/{col:capacity},0)', 10),
    CA('cost', 'Cost', 'money', '{col:staff_cost}+{col:food_cost}+{col:overhead_share}', 12), CA('profit', 'Profit', 'money', '{col:revenue}-{col:cost}', 12),
    CA('margin', 'Margin', 'pct', 'IF({col:revenue}>0,{col:profit}/{col:revenue},0)', 9),
    CA('to_break_even', 'Children still needed to break even', 'int', 'IF(AND({col:profit}<0,{col:enrolled}>0),ROUNDUP(-{col:profit}/MAX(1,({col:revenue}-{col:food_cost})/{col:enrolled}),0),0)', 12),
    CA('profit_cap', 'Profit, capacity rule', 'money', '{col:revenue}-{col:staff_cost}-{col:food_cost}-IFERROR(%s*{col:capacity}/%s,0)' % (BYM('room_months', 'overhead_share'), BYM('room_months', 'capacity')), 12),
    CA('profit_child', 'Profit, children rule', 'money', '{col:revenue}-{col:staff_cost}-{col:food_cost}-IFERROR(%s*{col:enrolled}/%s,0)' % (BYM('room_months', 'overhead_share'), BYM('room_months', 'enrolled')), 12),
    CA('room_profit_12m', 'Room profit, 12 months', 'money', 'SUMIFS({range:room_months.profit},{range:room_months.room},{col:room},%s)' % RMW(12), 13),
    CA('p12_cap', 'Room profit, 12 months, capacity rule', 'money', 'SUMIFS({range:room_months.profit_cap},{range:room_months.room},{col:room},%s)' % RMW(12), 13),
    CA('p12_child', 'Room profit, 12 months, children rule', 'money', 'SUMIFS({range:room_months.profit_child},{range:room_months.room},{col:room},%s)' % RMW(12), 13),
    CA('room_margin_12m', 'Room margin, 12 months', 'pct', 'IFERROR({col:room_profit_12m}/SUMIFS({range:room_months.revenue},{range:room_months.room},{col:room},%s),0)' % RMW(12), 11),
    CA('profit_place', 'Profit per place, 12 months', 'money', 'IF({col:capacity}>0,{col:room_profit_12m}/{col:capacity},0)', 12),
    CA('profit_hour', 'Profit per child-hour, 12 months', 'money', 'IFERROR({col:room_profit_12m}/SUMIFS({range:cost_hour.child_hours},{range:cost_hour.room},{col:room},%s),0)' % WN('cost_hour', 12), 12),
    CA('supplies_budget', 'Supplies budget share', 'money', 'IFERROR(AVERAGEIFS({range:budget.budget},{range:budget.category},%s)*{col:enrolled}/SUMIFS({range:room_months.enrolled},{range:room_months.month},{col:month}),0)' % tok('expcat', 'Supplies and toys'), 11),
    CA('result', 'Room result', 'text', 'IF({col:profit}>=0,%s,%s)' % (V('Room earns'), V('Room loses money')), 16),
    CA('lead_teacher', 'Lead teacher', 'text', 'IF({col:room}=%s,%s,IF({col:room}=%s,%s,IF({col:room}=%s,%s,IF({col:room}=%s,%s,%s))))' % (
        RT['Infants'], tok('person', 'Aaliyah'), RT['Toddlers'], tok('person', 'Mateusz'), RT['Twos'], tok('person', 'Ngozi'), RT['Preschool'], tok('person', 'Camille'), tok('person', 'Sofia')), 14),
    CA('teacher_phone', 'Lead teacher phone', 'text', 'IF({col:room}=%s,"%s",IF({col:room}=%s,"%s",IF({col:room}=%s,"%s",IF({col:room}=%s,"%s","%s"))))' % (
        RT['Infants'], D.LEAD['Infants']['phone'], RT['Toddlers'], D.LEAD['Toddlers']['phone'], RT['Twos'], D.LEAD['Twos']['phone'], RT['Preschool'], D.LEAD['Preschool']['phone'], D.LEAD['School-age']['phone']), 18),
    CENTER(), OWN(), OWNER_PH()],
    D.room_months_d(), 200, [A('profit', '< 0', 'bad'), A('occupancy', '< {set:occupancy_target}', 'warn'), A('result', '= ' + V('Room loses money'), 'bad')]))
# ---------------------------------------------------------------- 3 cash by month
tables.append(T('cash', 'Cash by Month', 'Cash in, cash out and the closing balance',
    'One row per month: the opening balance, parent and government payments received, pay, expenses, income tax set-aside, deposit refunds and owner extra draws paid out; the closing balance and the margin over your cash floor fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), C('opening', 'Opening balance', 'money', 13), C('parent_payments', 'Parent payments', 'money', 13), C('government_payments', 'Government payments', 'money', 13),
    C('pay_out', 'Pay out', 'money', 12), C('expenses_out', 'Expenses out', 'money', 12), C('tax_set_aside', 'Tax set aside', 'num', 12), C('deposit_refunds', 'Deposit refunds', 'num', 11), C('owner_extra', 'Owner extra draw', 'num', 12),
    CA('closing', 'Closing balance', 'money', '{col:opening}+{col:parent_payments}+{col:government_payments}-{col:pay_out}-{col:expenses_out}-{col:tax_set_aside}-{col:deposit_refunds}-{col:owner_extra}', 13),
    CA('net_change', 'Change in the month', 'money', '{col:closing}-{col:opening}', 12), CA('above_floor', 'Closing less your cash floor', 'money', '{col:closing}-{set:cash_floor}', 13),
    CA('floor_flag', 'Cash check', 'text', 'IF({col:closing}>={set:cash_floor},%s,%s)' % (V('Above the floor'), V('Below the floor')), 14), CENTER(), OWN(), OWNER_PH(), ACC(), ACC_PH(), DIR(), DIR_PH()],
    D.cash_d(), 60, [A('floor_flag', '= ' + V('Below the floor'), 'bad'), A('owner_extra', '> 0', 'warn')]))
# ---------------------------------------------------------------- 4 tax set-aside
tables.append(T('tax', 'Tax Set-aside', 'Income tax set-aside by month',
    'One row per month: the due date and the date paid; revenue, costs and profit come from Profit and Loss, the set-aside is your share of profit (confirm with your adviser) and the status fills in by itself.', [
    C('month', 'Month', 'date', 11, required=True), C('due_date', 'Due date', 'date', 11), C('paid_on', 'Paid on', 'date', 11),
    CA('revenue', 'Revenue', 'money', BYM('pnl', 'revenue'), 12), CA('costs', 'Costs', 'money', BYM('pnl', 'costs'), 12), CA('profit', 'Profit', 'money', '{col:revenue}-{col:costs}', 12),
    CA('set_aside_pct', 'Set-aside share', 'pct', '{set:tax_set_aside_pct}', 9), CA('set_aside', 'Set aside', 'money', '{col:set_aside_pct}*MAX(0,{col:profit})', 11),
    CA('open_amount', 'Still to pay', 'money', 'IF({col:paid_on}>0,0,{col:set_aside})', 11), CA('days_to_due', 'Days to the due date', 'int', 'IF({col:paid_on}>0,"",{col:due_date}-{today})', 10),
    CA('status', 'Status', 'text', 'IF({col:paid_on}>0,%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<=30,%s,%s)))' % (V('Paid'), V('Overdue'), V('Due within 30 days'), V('Upcoming')), 16), CENTER(), OWN(), OWNER_PH(), ACC(), ACC_PH()],
    D.tax_d(), 60, [A('status', '= ' + V('Overdue'), 'bad'), A('status', '= ' + V('Due within 30 days'), 'warn'), A('status', '= ' + V('Paid'), 'good')]))
# ---------------------------------------------------------------- 5 expenses
tables.append(T('expenses', 'Expenses', 'Expenses with category and who was paid',
    'One row per expense of the last 12 months: date, category, description, amount and who was paid; the category check and the share of the category total fill in by themselves. Rows without a category show in the check.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('category', 'Category', 'expcat', 18), C('description', 'Description', 'text', 28),
    C('amount', 'Amount', 'money', 11), C('paid_to', 'Paid to', 'text', 24),
    CA('category_flag', 'Category check', 'text', 'IF({col:category}="",%s,%s)' % (V('No category'), V('Categorised')), 14),
    CA('share_of_category', 'Share of the category, 12 months', 'pct', 'IF({col:category}="",0,IFERROR({col:amount}/SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.month},">="&EDATE(%s,-12)),0))' % MS, 11),
    CENTER(), OWN(), OWNER_PH(), DIR(), DIR_PH(), ACC(), ACC_PH(), MNT(), MNT_PH()],
    D.expenses_d(), 400, [A('category_flag', '= ' + V('No category'), 'bad')]))
# ---------------------------------------------------------------- 6 bills
tables.append(T('bills', 'Bills', 'Bills coming due',
    'One row per bill: due date, category, who is paid, amount and whether it is paid; the status and the days to the due date fill in by themselves.', [
    C('bill_id', 'Bill ID', 'text', 9, required=True), C('due_date', 'Due date', 'date', 11), C('category', 'Category', 'text', 18), C('paid_to', 'Paid to', 'text', 24), C('amount', 'Amount', 'money', 12), C('paid', 'Paid', 'bool', 8),
    CA('days_to_due', 'Days to the due date', 'int', 'IF({col:paid}=%s,"",{col:due_date}-{today})' % YES, 10),
    CA('status', 'Status', 'text', 'IF({col:paid}=%s,%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<=7,%s,%s)))' % (YES, V('Paid'), V('Overdue'), V('Due this week'), V('Upcoming')), 14),
    CA('supplier_phone', 'Supplier phone', 'text', 'IF({col:paid_to}=%s,"%s",IF({col:paid_to}=%s,"%s",IF({col:paid_to}=%s,"%s",IF({col:paid_to}=%s,"%s",""))))' % (
        tok('person', 'Rajesh Menon'), D.FOOD_PHONE, tok('person', 'Thandiwe Nkosi'), D.CLEAN_PHONE, tok('person', 'Dae-ho Park'), D.MAINT_PHONE, tok('person', 'Eleni Papadakis'), D.ACC_PHONE), 18),
    CENTER(), OWN(), DIR(), DIR_PH()],
    D.bills_d(), 100, [A('status', '= ' + V('Overdue'), 'bad'), A('status', '= ' + V('Due this week'), 'warn'), A('status', '= ' + V('Paid'), 'good')]))
# ---------------------------------------------------------------- 7 rooms
tables.append(T('rooms', 'Rooms', 'Rooms with licensed places and ratio',
    'One row per room: licensed places and the ratio, the number of children each staff member may care for (check your local rules). A home daycare keeps one row.', [
    LST('room', 'Room', 'room', 12, required=True), C('capacity', 'Licensed places', 'int', 11), C('ratio', 'Ratio, children per staff', 'int', 11)], D.rooms_d(), 50))
# ---------------------------------------------------------------- 8 rates
CPH = 'INDEX({range:fee_check.cost_per_hour},MATCH({col:room},{range:fee_check.room},0))'
tables.append(T('rates', 'Rates', 'Weekly rates by room and schedule with the fee check',
    'One row per room and schedule: the weekly rate this year and last year, days and hours; the rate per child-hour, the cost per child-hour of the room, the weekly rate that earns your wanted margin and the rise needed fill in by themselves.', [
    C('rate_id', 'Rate ID', 'text', 9, required=True), LST('room', 'Room', 'room', 12), LST('schedule', 'Schedule', 'schedule', 13), C('weekly_rate', 'Weekly rate', 'money', 11), C('last_year_rate', 'Last year rate', 'money', 11),
    C('days', 'Days', 'int', 7), C('hours_day', 'Hours a day', 'num', 9), C('day_rate', 'Day rate', 'money', 10), C('reviewed_on', 'Rate card date', 'date', 11),
    CA('rise_pct', 'Rise this year', 'pct', 'IF({col:last_year_rate}>0,{col:weekly_rate}/{col:last_year_rate}-1,0)', 9),
    CA('child_hour_rate', 'Rate per child-hour', 'money', 'IF({col:days}*{col:hours_day}>0,{col:weekly_rate}/({col:days}*{col:hours_day}),0)', 11),
    CA('collected_hour', 'Collected per child-hour', 'money', 'IFERROR({col:child_hour_rate}*INDEX({range:fee_check.fee_per_hour},MATCH({col:room},{range:fee_check.room},0))/SUMIFS({range:rates.child_hour_rate},{range:rates.room},{col:room},{range:rates.schedule},%s),0)' % tok('schedule', '5 full days'), 11),
    CA('cost_per_hour', 'Cost per child-hour of the room', 'money', 'IFERROR(%s,0)' % CPH, 12),
    CA('margin_hour', 'Margin per child-hour', 'money', '{col:collected_hour}-{col:cost_per_hour}', 11),
    CA('cost_to_rate', 'Weekly cost against rate, 5 full days', 'num', 'IF(AND({col:weekly_rate}>0,{col:schedule}=%s),{col:cost_per_hour}*{col:days}*{col:hours_day}/{col:weekly_rate},0)' % tok('schedule', '5 full days'), 11),
    CA('needed_rate', 'Weekly rate for your wanted margin', 'money', '{col:cost_per_hour}*{col:days}*{col:hours_day}/(1-{set:margin_target})', 13),
    CA('rise_needed', 'Rise needed', 'pct', 'IF({col:weekly_rate}>0,MAX(0,{col:needed_rate}/{col:weekly_rate}-1),0)', 9),
    CA('fee_flag', 'Fee check', 'text', 'IF({col:needed_rate}<={col:weekly_rate},%s,%s)' % (V('Rate covers the target margin'), V('Rate below the target margin')), 22),
    CA('review_date', 'Fee review date', 'date', '{set:fee_review_date}', 11), CENTER(), OWN(), OWNER_PH()],
    D.rates_d(), 50, [A('fee_flag', '= ' + V('Rate below the target margin'), 'warn'), A('fee_flag', '= ' + V('Rate covers the target margin'), 'good')]))
# ---------------------------------------------------------------- 9 payroll
tables.append(T('payroll', 'Payroll', 'Payroll by person and month',
    'One row per person and month: role, pay type, hours, total pay with employer costs and the pay date; the status, the pay per hour and the share of the month pay fill in by themselves.', [
    C('pay_id', 'Pay ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('person', 'Person', 'text', 22), LST('role', 'Role', 'payrole', 18), LST('pay_type', 'Pay type', 'paytype', 12), C('hours', 'Hours', 'num', 8),
    C('total', 'Total pay', 'money', 11), C('pay_date', 'Pay date', 'date', 11),
    CA('status', 'Status', 'text', 'IF({col:pay_date}<={today},%s,%s)' % (V('Paid'), V('Accruing')), 10), CA('pay_hour', 'Pay per hour', 'money', 'IF({col:hours}>0,{col:total}/{col:hours},0)', 10),
    CA('share_of_month', 'Share of the month pay', 'pct', 'IFERROR({col:total}/(%s+%s),0)' % (BYM('pnl', 'staff_pay'), BYM('pnl', 'owner_pay')), 10)],
    D.payroll_d(), 200, [A('status', '= ' + V('Accruing'), 'warn')]))
# ---------------------------------------------------------------- 10 revenue by room
tables.append(T('rev_room', 'Revenue by Room', 'Revenue by room and month',
    'One row per room and month of the last 12 months: tuition, fees and revenue are worked out from Room Profit by Month and Profit and Loss, with the share of the center and the revenue per child.', [
    LST('room', 'Room', 'room', 12, required=True), C('month', 'Month', 'date', 11),
    CA('revenue', 'Revenue', 'money', 'SUMIFS({range:room_months.revenue},{range:room_months.room},{col:room},{range:room_months.month},{col:month})', 12),
    CA('fees', 'Fees', 'money', 'IFERROR({col:revenue}*%s/%s,0)' % (BYM('pnl', 'fee_revenue'), BYM('pnl', 'revenue')), 11), CA('tuition', 'Tuition', 'money', '{col:revenue}-{col:fees}', 12),
    CA('share', 'Share of the center', 'pct', 'IFERROR({col:revenue}/%s,0)' % BYM('pnl', 'revenue'), 10),
    CA('children', 'Children enrolled', 'int', 'SUMIFS({range:room_months.enrolled},{range:room_months.room},{col:room},{range:room_months.month},{col:month})', 10),
    CA('revenue_child', 'Revenue per child', 'money', 'IF({col:children}>0,{col:revenue}/{col:children},0)', 11)],
    D.rev_room_d(), 100))
# ---------------------------------------------------------------- 11 staff cost share
tables.append(T('staff_share', 'Staff Cost Share', 'Staff pay share of revenue by month',
    'One row per month: staff pay and revenue come from Profit and Loss; the share, your highest accepted share, the gap, the revenue or the saving that closes the gap fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), CA('staff_pay', 'Staff pay', 'money', BYM('pnl', 'staff_pay'), 12), CA('revenue', 'Revenue', 'money', BYM('pnl', 'revenue'), 12),
    CA('share', 'Staff pay share', 'pct', 'IF({col:revenue}>0,{col:staff_pay}/{col:revenue},0)', 10), CA('target', 'Highest share you accept', 'pct', '{set:staff_share_target}', 10),
    CA('gap', 'Gap to the target', 'pct', '{col:share}-{col:target}', 10), CA('revenue_needed', 'Extra revenue that closes the gap', 'money', 'IF({col:share}>{col:target},{col:staff_pay}/{col:target}-{col:revenue},0)', 12),
    CA('saving_needed', 'Staff saving that closes the gap', 'money', 'MAX(0,{col:staff_pay}-{col:target}*{col:revenue})', 12),
    CA('flag', 'Share check', 'text', 'IF({col:share}<={col:target},%s,%s)' % (V('Staff share on target'), V('Staff share above target')), 18), CENTER(), OWN(), OWNER_PH()],
    D.staff_share_d(), 60, [A('flag', '= ' + V('Staff share above target'), 'warn'), A('gap', '> 0', 'bad')]))
# ---------------------------------------------------------------- 12 cost per child-hour
tables.append(T('cost_hour', 'Cost per Child-Hour', 'Cost and fee per child-hour by room and month',
    'One row per room and month: the child-hours attended; the total cost and revenue come from Room Profit by Month, the cost per child-hour, the fee per child-hour and the gap fill in by themselves.', [
    LST('room', 'Room', 'room', 12, required=True), C('month', 'Month', 'date', 11), C('child_hours', 'Child-hours attended', 'num', 11),
    CA('total_cost', 'Total cost', 'money', 'SUMIFS({range:room_months.cost},{range:room_months.room},{col:room},{range:room_months.month},{col:month})', 12),
    CA('revenue', 'Revenue', 'money', 'SUMIFS({range:room_months.revenue},{range:room_months.room},{col:room},{range:room_months.month},{col:month})', 12),
    CA('cost_per_hour', 'Cost per child-hour', 'money', 'IF({col:child_hours}>0,{col:total_cost}/{col:child_hours},0)', 11), CA('fee_per_hour', 'Fee per child-hour', 'money', 'IF({col:child_hours}>0,{col:revenue}/{col:child_hours},0)', 11),
    CA('gap_hour', 'Fee less cost per child-hour', 'money', '{col:fee_per_hour}-{col:cost_per_hour}', 11), CA('low_by', 'Fee short of cost per child-hour', 'money', 'MAX(0,{col:cost_per_hour}-{col:fee_per_hour})', 11),
    CA('flag', 'Fee check', 'text', 'IF({col:child_hours}<=0,%s,IF({col:fee_per_hour}>={col:cost_per_hour},%s,%s))' % (V('No hours yet'), V('Fee covers cost'), V('Fee below cost')), 14), CENTER(), OWN(), OWNER_PH()],
    D.cost_hour_d(), 100, [A('flag', '= ' + V('Fee below cost'), 'bad'), A('flag', '= ' + V('Fee covers cost'), 'good')]))
# ---------------------------------------------------------------- 13 occupancy by month
tables.append(T('occupancy', 'Occupancy by Month', 'Occupancy by month against the target',
    'One row per month: places and children come from Room Profit by Month; the occupancy (children booked as a share of licensed places), the gap to your wanted occupancy and the children needed to reach it fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), CA('places', 'Licensed places', 'int', BYM('room_months', 'capacity'), 10), CA('children', 'Children enrolled', 'int', BYM('room_months', 'enrolled'), 10),
    CA('occupancy', 'Occupancy', 'pct', 'IF({col:places}>0,{col:children}/{col:places},0)', 10), CA('target', 'Wanted occupancy', 'pct', '{set:occupancy_target}', 10), CA('target_gap', 'Gap to the target', 'pct', '{col:occupancy}-{col:target}', 10),
    CA('free_places', 'Free places', 'int', '{col:places}-{col:children}', 9), CA('children_to_target', 'Children needed to reach the target', 'int', 'MAX(0,ROUNDUP({col:target}*{col:places},0)-{col:children})', 11),
    CA('flag', 'Occupancy check', 'text', 'IF({col:occupancy}>={col:target},%s,%s)' % (V('At occupancy target'), V('Below occupancy target')), 20), CENTER(), OWN(), OWNER_PH()],
    D.occupancy_d(), 60, [A('flag', '= ' + V('Below occupancy target'), 'warn'), A('flag', '= ' + V('At occupancy target'), 'good')]))
# ---------------------------------------------------------------- 14 scenarios
S3 = lambda t, c, room: 'SUMIFS({range:%s.%s},{range:%s.room},%s,%s)' % (t, c, t, room, WN(t, 3))
tables.append(T('scenarios', 'Scenarios', 'What-if scenarios for children and staff hours',
    'One row per scenario: the room, the children added or lost and the staff hours added or cut each month; the revenue, food and staff cost change and the profit change a month fill in from your own last 3 months.', [
    LST('scenario', 'Scenario', 'scnrow', 28, required=True), LST('room', 'Room', 'room', 12), C('children_change', 'Children change', 'int', 9), C('staff_hours_change', 'Staff hours change a month', 'num', 11),
    CA('revenue_child', 'Revenue per child a month', 'money', 'IFERROR(%s/%s,0)' % (S3('room_months', 'revenue', '{col:room}'), S3('room_months', 'enrolled', '{col:room}')), 11),
    CA('food_child', 'Food cost per child a month', 'money', 'IFERROR(%s/%s,0)' % (S3('room_months', 'food_cost', '{col:room}'), S3('room_months', 'enrolled', '{col:room}')), 11),
    CA('staff_hour', 'Staff cost per hour', 'money', 'IFERROR(SUMIFS({range:payroll.total},{range:payroll.pay_type},%s)/SUMIFS({range:payroll.hours},{range:payroll.pay_type},%s),0)' % (HOURLY, HOURLY), 10),
    CA('revenue_change', 'Revenue change', 'money', '{col:children_change}*{col:revenue_child}', 12), CA('staff_change', 'Staff cost change', 'money', '{col:staff_hours_change}*{col:staff_hour}', 12),
    CA('food_change', 'Food cost change', 'money', '{col:children_change}*{col:food_child}', 11), CA('cost_change', 'Cost change', 'money', '{col:staff_change}+{col:food_change}', 12),
    CA('profit_change', 'Profit change a month', 'money', '{col:revenue_change}-{col:cost_change}', 12),
    CA('profit_after', 'Profit a month after', 'money', '%s/3+{col:profit_change}' % SN('pnl', 'profit', 3), 12),
    CA('flag', 'Scenario check', 'text', 'IF({col:profit_change}>0,%s,%s)' % (V('Worth it'), V('Not worth it')), 12), CENTER(), OWN(), OWNER_PH()],
    D.scenarios_d(), 60, [A('profit_change', '< 0', 'bad'), A('profit_change', '> 0', 'good')]))
# ---------------------------------------------------------------- 15 fee check by room
tables.append(T('fee_check', 'Fee Check by Room', 'Fee and cost per child-hour by room',
    'One row per room: the fee and the cost per child-hour over the last 12 months, worked out from Cost per Child-Hour.', [
    LST('room', 'Room', 'room', 12, required=True),
    CA('fee_per_hour', 'Fee per child-hour', 'money', 'IFERROR(SUMIFS({range:cost_hour.revenue},{range:cost_hour.room},{col:room},%s)/SUMIFS({range:cost_hour.child_hours},{range:cost_hour.room},{col:room},%s),0)' % (WN('cost_hour', 12), WN('cost_hour', 12)), 12),
    CA('cost_per_hour', 'Cost per child-hour', 'money', 'IFERROR(SUMIFS({range:cost_hour.total_cost},{range:cost_hour.room},{col:room},%s)/SUMIFS({range:cost_hour.child_hours},{range:cost_hour.room},{col:room},%s),0)' % (WN('cost_hour', 12), WN('cost_hour', 12)), 12)],
    D.fee_check_d(), 50))
# ---------------------------------------------------------------- 16 break-even by month
tables.append(T('breakeven', 'Break-even by Month', 'Break-even children and occupancy by month',
    'One row per month: fixed costs (staff, owner, rent and other), food as the cost that grows with each child, revenue and children come from the other sheets; the break-even children, the break-even occupancy and the cushion fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('fixed_costs', 'Fixed costs', 'money', '%s+%s+%s+%s' % (BYM('pnl', 'staff_pay'), BYM('pnl', 'owner_pay'), BYM('pnl', 'rent'), BYM('pnl', 'other_costs')), 12), CA('variable_costs', 'Food cost', 'money', BYM('pnl', 'food'), 11),
    CA('revenue', 'Revenue', 'money', BYM('pnl', 'revenue'), 12), CA('children', 'Children enrolled', 'int', BYM('room_months', 'enrolled'), 10), CA('places', 'Licensed places', 'int', BYM('room_months', 'capacity'), 10),
    CA('revenue_child', 'Revenue per child', 'money', 'IF({col:children}>0,{col:revenue}/{col:children},0)', 11), CA('variable_child', 'Food cost per child', 'money', 'IF({col:children}>0,{col:variable_costs}/{col:children},0)', 11),
    CA('be_children', 'Break-even children', 'num', 'IF({col:revenue_child}>{col:variable_child},{col:fixed_costs}/({col:revenue_child}-{col:variable_child}),0)', 10),
    CA('be_occupancy', 'Break-even occupancy', 'pct', 'IF({col:places}>0,{col:be_children}/{col:places},0)', 10), CA('occupancy', 'Occupancy', 'pct', 'IF({col:places}>0,{col:children}/{col:places},0)', 10),
    CA('cushion', 'Cushion over break-even', 'pct', '{col:occupancy}-{col:be_occupancy}', 10), CA('above', 'Above break-even', 'int', 'IF({col:children}>={col:be_children},1,0)', 9),
    CA('position', 'Break-even check', 'text', 'IF({col:above}=1,%s,%s)' % (V('Above break-even'), V('Below break-even')), 16), CENTER(), OWN(), OWNER_PH()],
    D.breakeven_d(), 60, [A('position', '= ' + V('Below break-even'), 'bad'), A('cushion', '< 0.05', 'warn')]))
# ---------------------------------------------------------------- 17 budget against actual
BUDW = 'EDATE(%s,-12)' % MS
tables.append(T('budget', 'Budget against Actual', 'Budget against actual by category and month',
    'One row per category and month of the last 12 months: your budget and the same month last year; the actual comes from Expenses, the variance, the 12-month totals and the rank of each category fill in by themselves.', [
    C('budget_id', 'Budget ID', 'text', 9, required=True), LST('category', 'Category', 'expcat', 18), C('month', 'Month', 'date', 11), C('budget', 'Budget', 'money', 11), C('last_year', 'Same month last year', 'money', 11),
    CA('actual', 'Actual', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.month},{col:month})', 11), CA('variance', 'Variance, over is positive', 'money', '{col:actual}-{col:budget}', 12),
    CA('var_pct', 'Variance share of budget', 'pct', 'IF({col:budget}>0,{col:variance}/{col:budget},0)', 10),
    CA('cat_budget', 'Category budget, 12 months', 'money', 'SUMIFS({range:budget.budget},{range:budget.category},{col:category})', 12), CA('cat_actual', 'Category actual, 12 months', 'money', 'ROUND(SUMIFS({range:budget.actual},{range:budget.category},{col:category}),2)', 12),
    CA('cat_var', 'Category variance, 12 months', 'money', 'ROUND({col:cat_actual}-{col:cat_budget},2)', 12),
    CA('cat_last', 'Category last year, same months', 'money', 'SUMIFS({range:budget.last_year},{range:budget.category},{col:category},{range:budget.month},">="&EDATE(%s,-11))' % MS, 12),
    CA('cat_actual_11', 'Category actual, same months', 'money', 'SUMIFS({range:budget.actual},{range:budget.category},{col:category},{range:budget.month},">="&EDATE(%s,-11))' % MS, 12),
    CA('cat_pct', 'Category variance share of budget', 'pct', 'IF({col:cat_budget}>0,ROUND({col:cat_var}/{col:cat_budget},4),0)', 10),
    CA('weight', 'Row weight', 'num', '1/COUNTIFS({range:budget.category},{col:category})', 8),
    CA('rank_over', 'Rank by overspend, 1 is largest', 'int', '1+SUMIFS({range:budget.weight},{range:budget.cat_var},">"&{col:cat_var})', 9),
    CA('rank_spend', 'Rank by spend, 1 is largest', 'int', '1+SUMIFS({range:budget.weight},{range:budget.cat_actual},">"&{col:cat_actual})', 9),
    CA('flag', 'Budget check', 'text', 'IF({col:variance}>{col:budget}*{set:variance_pct},%s,IF({col:variance}<-{col:budget}*{set:variance_pct},%s,%s))' % (V('Over budget'), V('Under budget'), V('On budget')), 13), CENTER(), OWN(), OWNER_PH(), ACC(), ACC_PH()],
    D.budget_d(), 200, [A('flag', '= ' + V('Over budget'), 'bad'), A('flag', '= ' + V('On budget'), 'good')]))
# ---------------------------------------------------------------- 18 home-use share lines
HOMESH = ('IF({col:rule}=%s,{set:home_rooms_used}/{set:home_rooms_total},IF({col:rule}=%s,{set:home_hours_used}/{set:home_hours_week},IF({col:rule}=%s,({set:home_rooms_used}/{set:home_rooms_total})*({set:home_hours_used}/{set:home_hours_week}),'
          'IF({col:rule}=%s,1,0))))' % (tok('homerule', 'Rooms share'), tok('homerule', 'Hours share'), tok('homerule', 'Rooms and hours'), tok('homerule', 'Whole amount')))
tables.append(T('home_lines', 'Home-use Share Lines', 'Home-use cost lines for a home daycare',
    'One row per cost line of the home (for a home daycare provider): the whole-house amount a month, the rule (rooms, hours, both, whole amount or not shared) and whether your adviser confirmed it; the business share and amount fill in by themselves.', [
    C('line', 'Cost line', 'text', 26, required=True), C('amount', 'Whole-house amount a month', 'money', 13), LST('rule', 'Rule', 'homerule', 16), C('set_on', 'Set on', 'date', 11), C('confirmed', 'Adviser confirmed', 'bool', 9),
    CA('share', 'Business share', 'pct', HOMESH, 9), CA('business_amount', 'Business amount a month', 'money', '{col:amount}*{col:share}', 12), CA('yearly_amount', 'Business amount a year', 'money', '12*{col:business_amount}', 12),
    CA('status', 'To confirm with your adviser', 'text', 'IF({col:confirmed}=%s,%s,%s)' % (YES, V('Confirmed by your adviser'), V('To confirm with your adviser')), 24), CENTER(), OWN(), OWNER_PH(), ACC(), ACC_PH()],
    D.home_lines_d(), 60, [A('status', '= ' + V('To confirm with your adviser'), 'warn'), A('status', '= ' + V('Confirmed by your adviser'), 'good')]))
# ---------------------------------------------------------------- 19 owner draw plan
START_CASH = 'IFERROR(INDEX({range:cash.closing},MATCH(EDATE(%s,-1),{range:cash.month},0)),0)' % MS
tables.append(T('draw_plan', 'Owner Draw Plan', 'Owner draw and set-aside plan for the next 12 months',
    'One row per month ahead: the profit forecast is your own last 6 months before the owner draw; your draw, the income tax set-aside (confirm with your adviser), the quarterly extra draw and the cash left fill in by themselves.', [
    C('no', 'Month number', 'int', 9, required=True), CA('month', 'Month', 'date', 'EDATE(%s,{col:no}-1)' % MS, 11),
    CA('forecast', 'Profit before the draw', 'money', '(%s+%s)/6' % (SN('pnl', 'profit', 6), SN('pnl', 'owner_pay', 6)), 12), CA('draw', 'Owner draw', 'money', '{set:owner_draw}', 11),
    CA('profit_after', 'Profit after the draw', 'money', '{col:forecast}-{col:draw}', 12), CA('set_aside', 'Tax set-aside', 'money', '{set:tax_set_aside_pct}*MAX(0,{col:profit_after})', 11),
    CA('extra_draw', 'Extra draw', 'money', 'IF(MOD(MONTH({col:month})-{set:extra_draw_month},3)=0,{set:owner_extra},0)', 11), CA('net_cash', 'Cash change', 'money', '{col:profit_after}-{col:set_aside}-{col:extra_draw}', 12),
    CA('cash_left', 'Cash left', 'money', '%s+SUMIFS({range:draw_plan.net_cash},{range:draw_plan.no},"<="&{col:no})' % START_CASH, 12),
    CA('floor_flag', 'Cash check', 'text', 'IF({col:cash_left}>={set:cash_floor},%s,%s)' % (V('Above the floor'), V('Below the floor')), 14), CENTER(), OWN(), OWNER_PH(), ACC(), ACC_PH()],
    D.draw_plan_d(), 60, [A('floor_flag', '= ' + V('Below the floor'), 'bad'), A('extra_draw', '> 0', 'warn')]))
# ---------------------------------------------------------------- 20 year in review
YTD_Y = 'YEAR(EDATE(%s,-1))' % MS
F1 = 'IF({col:basis}=%s,DATE(%s,1,1),IF({col:basis}=%s,EDATE(%s,-6),EDATE(%s,-3)))' % (tok('basis', BASIS[0]), YTD_Y, tok('basis', BASIS[1]), MS, MS)
T1 = MS
F0 = 'IF({col:basis}=%s,EDATE({col:this_from},-12),IF({col:basis}=%s,EDATE(%s,-12),EDATE(%s,-6)))' % (tok('basis', BASIS[0]), tok('basis', BASIS[1]), MS, MS)
T0 = 'IF({col:basis}=%s,EDATE({col:this_to},-12),IF({col:basis}=%s,EDATE(%s,-6),EDATE(%s,-3)))' % (tok('basis', BASIS[0]), tok('basis', BASIS[1]), MS, MS)


def VAL(f, t):
    """the 8 measures over the months from f (included) to t (excluded); f and t are formula texts"""
    def pw(tb, c): return 'SUMIFS({range:%s.%s},{range:%s.month},">="&%s,{range:%s.month},"<"&%s)' % (tb, c, tb, f, tb, t)
    rev = pw('pnl', 'revenue')
    return ('CHOOSE({col:no},%s,%s,%s,IFERROR(100*%s/%s,0),IFERROR(100*%s/%s,0),IFERROR(100*%s/%s,0),IFERROR(%s/%s,0),IFERROR(INDEX({range:cash.closing},MATCH(EDATE(%s,-1),{range:cash.month},0)),0))' % (
        rev, pw('pnl', 'costs'), pw('pnl', 'profit'), pw('pnl', 'profit'), rev, pw('room_months', 'enrolled'), pw('room_months', 'capacity'), pw('pnl', 'staff_pay'), rev, rev, pw('room_months', 'enrolled'), t))


tables.append(T('year_review', 'Year in Review', 'This period against the same period before',
    'One row per measure and review period: revenue, costs, profit, margin, occupancy, staff pay share, revenue per child and cash, this period against the period before; the change and the verdict (stronger, steady or weaker) fill in from your own history.', [
    C('review_id', 'Review ID', 'text', 9, required=True), C('no', 'Measure number', 'int', 9), LST('basis', 'Review period', 'basis', 40),
    CA('measure', 'Measure', 'text', 'CHOOSE({col:no},%s)' % ','.join(tok('ymeasure', m) for m in YMEASURE), 26),
    CA('this_from', 'This period from', 'date', F1, 11), CA('this_to', 'This period ends before', 'date', T1, 11), CA('last_from', 'Period before from', 'date', F0, 11), CA('last_to', 'Period before ends before', 'date', T0, 11),
    CA('this_period', 'This period', 'num', VAL('{col:this_from}', '{col:this_to}'), 12), CA('last_period', 'Period before', 'num', VAL('{col:last_from}', '{col:last_to}'), 12),
    CA('change', 'Change', 'num', '{col:this_period}-{col:last_period}', 11), CA('change_pct', 'Change, share', 'pct', 'IF({col:last_period}<>0,{col:change}/ABS({col:last_period}),0)', 10),
    CA('lower_better', 'Lower is better', 'int', 'IF(OR({col:no}=2,{col:no}=6),1,0)', 8),
    CA('verdict', 'Verdict', 'text', 'IF(ABS({col:change_pct})<={set:steady_band},%s,IF(({col:change}>0)=({col:lower_better}=0),%s,%s))' % (V('Steady'), V('Stronger'), V('Weaker')), 12),
    CA('row_key', 'Row key', 'text', '{col:measure}&"|"&{col:basis}', 12), CENTER(), OWN(), OWNER_PH(), ACC(), ACC_PH()],
    D.year_review_d(), 60, [A('verdict', '= ' + V('Weaker'), 'bad'), A('verdict', '= ' + V('Stronger'), 'good')]))
assert len(tables) == 20, len(tables)
