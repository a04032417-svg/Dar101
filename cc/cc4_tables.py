"""Childcare center suite part 4: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc4_lists import *
import cc4_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def CENTER(): return CA('center', 'Center', 'text', '{set:company}', 22)
def OWNER_PH(): return CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def DIR_PH(): return CA('director_phone', 'Assistant director phone', 'text', '"%s"' % D.DIRECTOR_PHONE, 18)
def ACC_PH(): return CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCOUNTANT_PHONE, 18)
def FAMPH(): return CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
ENR = tok('cstatus', 'Enrolled'); LEFT = tok('cstatus', 'Left'); WK = tok('cycle', 'Weekly'); MO = tok('cycle', 'Monthly'); HELD = tok('depstatus', 'Held')
def RATE_OF(room, sched): return 'SUMIFS({range:rates.weekly_rate},{range:rates.room},%s,{range:rates.schedule},%s)' % (room, sched)
def RATE_LY(room, sched): return 'SUMIFS({range:rates.last_year_rate},{range:rates.room},%s,{range:rates.schedule},%s)' % (room, sched)
BASE3 = '(SUMIFS({range:rev_room.revenue},{range:rev_room.month},">="&EDATE(%s,-3),{range:rev_room.month},"<"&%s)/3)' % (MS, MS)
NEXT_MON = '{today}+MOD(8-WEEKDAY({today},2),7)'
NEXT_1ST = 'IF(DAY({today})=1,{today},DATE(YEAR({today}),MONTH({today})+1,1))'

settings = [
    S('company', 'Your center name', 'text', COMPANY), S('reg_fee', 'Registration fee', 'money', REG_FEE), S('supply_fee', 'Supply fee each September', 'money', SUPPLY_FEE),
    S('sibling_pct', 'Sibling discount, lower fee for a second child', 'pct', SIBLING_PCT), S('staff_pct', 'Staff discount', 'pct', STAFF_PCT),
    S('drop_in_surcharge', 'Drop-in surcharge, added to the day rate', 'pct', DROP_IN_SURCHARGE), S('late_fee_per_min', 'Late pickup fee per minute', 'money', LATE_FEE_PER_MIN),
    S('late_grace_min', 'Grace minutes after closing time', 'int', LATE_GRACE_MIN), S('invoice_days', 'Days to pay a monthly invoice', 'int', INVOICE_DAYS),
    S('weekly_due_days', 'Days from Monday to the due date of a weekly invoice', 'int', WEEKLY_DUE_DAYS), S('notice_days', 'Notice days for a fee rise or leaving', 'int', NOTICE_DAYS),
    S('staff_share_target', 'Staff cost share of revenue you want to hold, set your own', 'pct', STAFF_SHARE_TARGET), S('discount_limit', 'Most discounts you give, share of tuition', 'pct', 0.04),
    S('tolerance', 'Rounding tolerance when checking an invoice', 'money', 1.0), S('overtime_cost_hour', 'Cost of one staff member for a late hour', 'money', 23.65),
    S('weeks_open', 'Weeks a year tuition is billed', 'int', 50), S('planned_rise', 'Planned fee rise', 'pct', 0.05), S('rise_start', 'Start date of the planned fee rise', 'date', ahead(75)),
    S('staff_pay_month', 'Planned monthly staff pay, next 12 months', 'money', 39000), S('repeat_events', 'Late pickups in 6 months that make a family repeat-late', 'int', 3),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 families ----------------------------------------------------------------
tables.append(T('families', 'Families', 'Families with billing cycle and government share',
    'One row per family: contact, billing cycle, payment method and government share; the children now, weekly tuition, next invoice date and planned rise fill in.', [
    C('family_id', 'Family ID', 'text', 9, required=True), C('family', 'Family', 'text', 22), C('guardian', 'Parent or guardian', 'text', 22), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    LST('cycle', 'Billing cycle', 'cycle', 10), LST('pay_method', 'Payment method', 'method', 14), C('autopay', 'Autopay', 'bool', 8), C('gov_share', 'Government share', 'pct', 10), C('late_prone', 'Late prone', 'bool', 8),
    C('staff_family', 'Staff family', 'bool', 8), C('children', 'Children', 'int', 8), C('first_start', 'First start', 'date', 11),
    CA('kids_now', 'Children enrolled now', 'int', 'COUNTIFS({range:children.family},{col:family},{range:children.status},%s)' % ENR, 10),
    CA('weekly_tuition', 'Weekly tuition after discounts', 'money', 'SUMIFS({range:children.net_weekly},{range:children.family},{col:family},{range:children.status},"<>"&%s)' % LEFT, 13),
    CA('next_invoice', 'Next invoice date', 'date', 'IF({col:cycle}=%s,%s,%s)' % (WK, NEXT_MON, NEXT_1ST), 11),
    CA('next_cycle', 'Other billing cycle', 'text', 'IF({col:cycle}=%s,%s,%s)' % (WK, MO, WK), 11),
    CA('rise_share', 'Planned rise', 'pct', '{set:planned_rise}', 9), CA('new_date', 'Rise starts on', 'date', '{set:rise_start}', 11), CA('notice_by', 'Send notice by', 'date', '{set:rise_start}-{set:notice_days}', 11),
    CA('new_weekly', 'New weekly tuition', 'money', 'ROUND({col:weekly_tuition}*(1+{set:planned_rise}),0)', 12),
    CA('next_closure', 'Next closure day', 'date', 'IFERROR(SMALL({range:closures.date},COUNTIFS({range:closures.date},"<"&{today})+1),"")', 11), CENTER()],
    D.families_d(), 150, [A('autopay', '= ' + YES, 'good'), A('late_prone', '= ' + YES, 'warn')]))
# 2 children ----------------------------------------------------------------
tables.append(T('children', 'Children', 'Children with room, schedule, days and discount',
    'One row per child (first name and family name only): room, schedule, days, dates, status and discount; the weekly rate, discount and net weekly tuition fill in.', [
    C('child_id', 'Child ID', 'text', 9, required=True), C('child', 'Child', 'text', 22), REF('family', 'Family', 'families.family', 22), C('family_id', 'Family ID', 'text', 9), LST('room', 'Room', 'room', 11),
    LST('schedule', 'Schedule', 'schedule', 13), C('days', 'Days a week', 'int', 8), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), LST('status', 'Status', 'cstatus', 12),
    LST('discount', 'Discount', 'discount', 10), C('discount_pct', 'Discount share', 'pct', 9), C('guardian', 'Parent or guardian', 'text', 22), C('phone', 'Phone', 'text', 18),
    CA('weekly_rate', 'Weekly rate', 'money', RATE_OF('{col:room}', '{col:schedule}'), 11), CA('last_year_rate', 'Last year weekly rate', 'money', RATE_LY('{col:room}', '{col:schedule}'), 11),
    CA('weekly_discount', 'Weekly discount', 'money', 'ROUND({col:weekly_rate}*{col:discount_pct},2)', 11), CA('net_weekly', 'Net weekly tuition', 'money', '{col:weekly_rate}-{col:weekly_discount}', 11),
    CA('supply_due', 'Supply fee', 'money', '{set:supply_fee}', 9), CENTER()],
    D.children_d(), 200, [A('status', '= ' + tok('cstatus', 'Starting soon'), 'good'), A('end_date', '> 0', 'warn')]))
# 3 rates -------------------------------------------------------------------
tables.append(T('rates', 'Rates', 'Rate card by room and schedule',
    'One row per room and schedule: weekly rate this year and last year, days and hours; the rise, monthly and hourly rate, sibling and staff rates fill in.', [
    C('rate_id', 'Rate ID', 'text', 9, required=True), LST('room', 'Room', 'room', 11), LST('schedule', 'Schedule', 'schedule', 13), C('weekly_rate', 'Weekly rate', 'money', 11), C('last_year_rate', 'Last year rate', 'money', 11),
    C('days', 'Days', 'int', 7), C('hours_day', 'Hours a day', 'num', 9), C('day_rate', 'Day rate', 'money', 10),
    CA('rise_pct', 'Rise this year', 'pct', 'IF({col:last_year_rate}>0,{col:weekly_rate}/{col:last_year_rate}-1,0)', 9),
    CA('monthly_rate', 'Monthly rate', 'money', 'ROUND({col:weekly_rate}*52/12,0)', 11), CA('hour_rate', 'Rate per hour', 'money', 'IF({col:days}*{col:hours_day}>0,ROUND({col:weekly_rate}/({col:days}*{col:hours_day}),2),0)', 10),
    CA('hour_rank', 'Hourly rank, 1 is lowest', 'int', 'COUNTIFS({range:rates.hour_rate},"<"&{col:hour_rate})+1', 10),
    CA('sibling_rate', 'Weekly rate, sibling discount', 'money', 'ROUND({col:weekly_rate}*(1-{set:sibling_pct}),0)', 13), CA('staff_rate', 'Weekly rate, staff discount', 'money', 'ROUND({col:weekly_rate}*(1-{set:staff_pct}),0)', 13)],
    D.rates_d(), 50))
# 4 fees --------------------------------------------------------------------
tables.append(T('fees', 'Fees', 'Fees and the rule behind each one',
    'One row per fee: registration, supply, late pickup, drop-in surcharge and deposit with the amount or share and the rule; the settings on the Start sheet drive the invoices.', [
    C('fee', 'Fee', 'text', 22, required=True), C('amount', 'Amount or share', 'num', 12), C('rule', 'Rule', 'text', 30)], D.fees_d(), 50))
# 5 invoices ----------------------------------------------------------------
tables.append(T('invoices', 'Invoices', 'Weekly and monthly invoices with discounts and extras',
    'One row per invoice: period, dates, tuition, discount, extras, government share and payment; the amount, parent due, days late and cash lag fill in.', [
    C('invoice_id', 'Invoice ID', 'text', 10, required=True), REF('family', 'Family', 'families.family', 22), LST('cycle', 'Cycle', 'cycle', 10), C('month', 'Month', 'date', 11), C('period_start', 'Period start', 'date', 11),
    C('period_end', 'Period end', 'date', 11), C('issued_on', 'Issued on', 'date', 11), C('due_date', 'Due date', 'date', 11), C('children', 'Children', 'int', 8), C('tuition', 'Tuition', 'money', 11),
    C('discount', 'Discount', 'num', 10), C('registration', 'Registration', 'num', 11), C('supply_fee', 'Supply fee', 'num', 10), C('camp_fee', 'Camp fee', 'num', 10), C('drop_in', 'Drop-in', 'num', 10),
    C('late_fees', 'Late fees', 'num', 10), C('gov_expected', 'Government expected', 'num', 12), C('paid_amount', 'Paid amount', 'money', 11), C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'istatus', 12),
    CA('extras', 'Extras', 'money', '{col:registration}+{col:supply_fee}+{col:camp_fee}+{col:drop_in}+{col:late_fees}', 10),
    CA('amount', 'Amount', 'money', '{col:tuition}-{col:discount}+{col:registration}+{col:supply_fee}+{col:camp_fee}+{col:drop_in}+{col:late_fees}', 11),
    CA('parent_due', 'Parent due', 'money', '{col:amount}-{col:gov_expected}', 11), CA('days_late', 'Days late', 'int', 'IF({col:paid_on}>0,{col:paid_on}-{col:due_date},"")', 8),
    CA('cash_lag', 'Days from mid-period to payment', 'int', 'IF({col:paid_on}>0,ROUND({col:paid_on}-({col:period_start}+({col:period_end}-{col:period_start})/2),0),"")', 11), FAMPH(), CENTER()],
    D.invoices_d(), 1500, [A('status', '= ' + tok('istatus', 'Unpaid'), 'warn'), A('status', '= ' + tok('istatus', 'Written off'), 'bad'), A('status', '= ' + tok('istatus', 'Paid'), 'good')]))
# 6 late fees ---------------------------------------------------------------
tables.append(T('late_fees', 'Late Fees', 'Late pickup fees with waivers and overtime cost',
    'One row per late pickup: date, child, room and minutes past closing time; the fee after the grace, the amount charged after a waiver and the staff overtime cost fill in by themselves.', [
    C('fee_id', 'Fee ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), REF('child', 'Child', 'children.child', 22), REF('family', 'Family', 'families.family', 22), LST('room', 'Room', 'room', 11),
    C('late_minutes', 'Late minutes', 'int', 9), C('waived', 'Waived', 'bool', 8), C('invoice_id', 'Invoice', 'text', 10),
    CA('fee', 'Fee', 'money', 'IF({col:late_minutes}>{set:late_grace_min},{col:late_minutes}*{set:late_fee_per_min},0)', 9), CA('charged', 'Charged', 'money', 'IF({col:waived}=%s,0,{col:fee})' % YES, 9),
    CA('overtime_cost', 'Overtime cost', 'money', 'ROUND({col:late_minutes}/60*{set:overtime_cost_hour},2)', 10), FAMPH(), CENTER()],
    D.late_fees_d(), 600, [A('waived', '= ' + YES, 'warn'), A('late_minutes', '> 20', 'bad')]))
# 7 deposits ----------------------------------------------------------------
tables.append(T('deposits', 'Deposits', 'Deposits held, applied, refunded or kept',
    'One row per deposit (a payment held to keep a place, applied to the last invoice): amount, dates, status and notice days; the notice check and refund date fill in.', [
    C('deposit_id', 'Deposit ID', 'text', 10, required=True), REF('child', 'Child', 'children.child', 22), C('amount', 'Amount', 'money', 11), C('received_on', 'Received on', 'date', 11), LST('status', 'Status', 'depstatus', 10),
    C('settled_on', 'Settled on', 'date', 11), C('notice_days', 'Notice days', 'int', 9),
    CA('family', 'Family', 'text', LKT('children.family', 'children.child', 'child'), 22), CA('end_date', 'End date', 'date', LKD('children.end_date', 'children.child', 'child'), 11),
    CA('notice_check', 'Notice check', 'text', 'IF({col:notice_days}>0,IF({col:notice_days}>={set:notice_days},%s,%s),%s)' % (ca('Notice kept'), ca('Notice short'), ca('No notice yet')), 12),
    CA('refund_date', 'Refund date', 'date', 'IF(AND({col:status}=%s,ISNUMBER({col:end_date})),{col:end_date}+5,"")' % HELD, 11), CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18), CENTER(), DIR_PH()],
    D.deposits_d(), 200, [A('status', '= ' + HELD, 'good'), A('notice_check', '= ' + ca('Notice short'), 'warn')]))
# 8 invoice check -----------------------------------------------------------
def INV(col): return LKN('invoices.' + col, 'invoices.invoice_id', 'invoice_id')
FAMX = '{range:children.family},{col:family}'
WS1 = 'SUMIFS({range:children.%s},%s,{range:children.start_date},"<="&{col:period_start})-SUMIFS({range:children.%s},%s,{range:children.start_date},"<="&{col:period_start},{range:children.end_date},"<"&{col:period_end})'
tables.append(T('inv_check', 'Invoice Check', 'Invoice against booked days times the rate',
    'One row per invoice to check: children booked, their weekly rates and weeks billed give the expected tuition; the difference and verdict flag invoices to look at.', [
    REF('invoice_id', 'Invoice', 'invoices.invoice_id', 10, required=True),
    CA('family', 'Family', 'text', LKT('invoices.family', 'invoices.invoice_id', 'invoice_id'), 22), CA('cycle', 'Cycle', 'text', LKT('invoices.cycle', 'invoices.invoice_id', 'invoice_id'), 10),
    CA('period_start', 'Period start', 'date', INV('period_start'), 11), CA('period_end', 'Period end', 'date', INV('period_end'), 11),
    CA('kids_booked', 'Children booked', 'int', 'COUNTIFS(%s,{range:children.start_date},"<="&{col:period_start})-COUNTIFS(%s,{range:children.start_date},"<="&{col:period_start},{range:children.end_date},"<"&{col:period_end})' % (FAMX, FAMX), 9),
    CA('booked_days', 'Booked days a week', 'int', WS1 % ('days', FAMX, 'days', FAMX), 9), CA('weekly_sum', 'Weekly rates of those children', 'money', WS1 % ('weekly_rate', FAMX, 'weekly_rate', FAMX), 12),
    CA('weeks', 'Weeks billed', 'num', 'IF({col:cycle}=%s,1,52/12)' % WK, 8), CA('expected', 'Expected tuition', 'money', 'ROUND({col:weekly_sum}*{col:weeks},2)', 11), CA('invoiced', 'Invoiced tuition', 'money', INV('tuition'), 11),
    CA('difference', 'Difference', 'money', 'ROUND({col:invoiced}-{col:expected},2)', 10), CA('abs_diff', 'Difference, no sign', 'money', 'ABS({col:difference})', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:abs_diff}<={set:tolerance},%s,%s)' % (ca('Matches'), ca('Differs')), 10), CENTER(), DIR_PH()],
    D.inv_check_d(), 100, [A('verdict', '= ' + ca('Differs'), 'bad'), A('verdict', '= ' + ca('Matches'), 'good')]))
# 9 statements --------------------------------------------------------------
tables.append(T('statements', 'Statements', 'Yearly payment statements for parents',
    'One row per family and year: parent and government payments, ledger total and date sent; the total, the difference to the ledger and the sent check fill in.', [
    C('statement_id', 'Statement ID', 'text', 11, required=True), REF('family', 'Family', 'families.family', 22), LST('year', 'Year', 'syear', 8), C('parent_paid', 'Parent paid', 'money', 11), C('government_paid', 'Government paid', 'num', 11),
    C('payments', 'Payments', 'int', 9), C('ledger_paid', 'Ledger parent paid', 'money', 12), C('sent_on', 'Sent on', 'date', 11),
    CA('total_paid', 'Total paid', 'money', '{col:parent_paid}+{col:government_paid}', 11), CA('difference', 'Difference to ledger', 'money', 'ROUND({col:parent_paid}-{col:ledger_paid},2)', 11),
    CA('check', 'Ledger check', 'text', 'IF(ABS({col:difference})<={set:tolerance},%s,%s)' % (ca('Statement matches'), ca('Statement differs')), 14),
    CA('sent_flag', 'Sent check', 'text', 'IF({col:sent_on}>0,%s,%s)' % (ca('Sent'), ca('Not sent yet')), 11), CA('key', 'Family and year', 'text', '{col:family}&"|"&{col:year}', 24),
    CA('differ_n', 'Statements that differ', 'int', 'COUNTIFS({range:statements.check},%s)' % ca('Statement differs'), 9), CA('unsent_n', 'Statements not sent', 'int', 'COUNTIFS({range:statements.sent_flag},%s)' % ca('Not sent yet'), 9),
    FAMPH(), DIR_PH(), ACC_PH(), CENTER()],
    D.statements_d(), 250, [A('check', '= ' + ca('Statement differs'), 'bad'), A('sent_flag', '= ' + ca('Not sent yet'), 'warn')]))
# 10 discounted children ----------------------------------------------------
def CH(col): return LKN('children.' + col, 'children.child', 'child')
tables.append(T('discounted', 'Discounted Children', 'Children with a sibling or staff discount and sibling pairs',
    'One row per child with a discount or a full-price sibling: the discount, its share, the weekly rate and the cost of the discount per week, month and year fill in from the Children sheet.', [
    REF('child', 'Child', 'children.child', 22, required=True), C('from_date', 'Discount from', 'date', 11),
    CA('family', 'Family', 'text', LKT('children.family', 'children.child', 'child'), 22), CA('room', 'Room', 'text', LKT('children.room', 'children.child', 'child'), 11),
    CA('schedule', 'Schedule', 'text', LKT('children.schedule', 'children.child', 'child'), 13), CA('status', 'Status', 'text', LKT('children.status', 'children.child', 'child'), 11),
    CA('discount', 'Discount', 'text', LKT('children.discount', 'children.child', 'child'), 10), CA('discount_pct', 'Discount share', 'pct', CH('discount_pct'), 9), CA('weekly_rate', 'Weekly rate', 'money', CH('weekly_rate'), 11),
    CA('weekly_cost', 'Cost per week', 'money', 'IF({col:status}=%s,0,ROUND({col:weekly_rate}*{col:discount_pct},2))' % LEFT, 10), CA('monthly_cost', 'Cost per month', 'money', 'ROUND({col:weekly_cost}*52/12,2)', 10),
    CA('yearly_cost', 'Cost per year', 'money', 'ROUND({col:weekly_cost}*{set:weeks_open},2)', 11), CA('phone', 'Phone', 'text', LKT('children.phone', 'children.child', 'child'), 18), CENTER()],
    D.discounted_d(), 60, [A('discount_pct', '> 0', 'good')]))
# 11 fee rise scenarios -----------------------------------------------------
tables.append(T('fee_rise', 'Fee Rise Scenarios', 'Fee rise scenarios with leavers and staff cost share',
    'One row per scenario: rise, expected leavers and announcement day; the new date, net monthly revenue and staff cost share after fill in from your last 3 months.', [
    C('announce_on', 'Announced on', 'date', 11, required=True), C('rise_pct', 'Rise share', 'pct', 9), C('leavers', 'Expected leavers', 'int', 9),
    CA('new_date', 'New date', 'date', '{col:announce_on}+{set:notice_days}', 11), CA('base_revenue', 'Monthly revenue now', 'money', BASE3, 12),
    CA('per_child', 'Revenue per child', 'money', 'IFERROR({col:base_revenue}/COUNTIFS({range:children.status},%s),0)' % ENR, 11),
    CA('net_revenue', 'Net monthly revenue', 'money', 'ROUND(({col:base_revenue}-{col:leavers}*{col:per_child})*(1+{col:rise_pct}),0)', 12), CA('gain', 'Gain per month', 'money', '{col:net_revenue}-{col:base_revenue}', 11),
    CA('share_now', 'Staff cost share now', 'pct', 'IFERROR({set:staff_pay_month}/{col:base_revenue},0)', 10), CA('share_after', 'Staff cost share after', 'pct', 'IFERROR({set:staff_pay_month}/{col:net_revenue},0)', 10),
    CA('holds', 'Target check', 'text', 'IF({col:share_after}<={set:staff_share_target},%s,%s)' % (ca('Holds target'), ca('Above target')), 12), CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18), CENTER()],
    D.fee_rise_d(), 50, [A('holds', '= ' + ca('Holds target'), 'good'), A('holds', '= ' + ca('Above target'), 'warn')]))
# 12 drop-in days -----------------------------------------------------------
tables.append(T('drop_in', 'Drop-in Days', 'Drop-in days with the day rate and surcharge',
    'One row per drop-in day (an extra day booked at short notice at a surcharge): date, child, room, hours and the day rate; the surcharge and the charge fill in by themselves.', [
    C('drop_id', 'Drop-in ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('child', 'Child', 'children.child', 22), REF('family', 'Family', 'families.family', 22), LST('room', 'Room', 'room', 11),
    C('hours', 'Hours', 'num', 8), C('day_rate', 'Day rate', 'money', 10), CA('surcharge', 'Surcharge', 'money', 'ROUND({col:day_rate}*{set:drop_in_surcharge},2)', 10), CA('charge', 'Charge', 'money', '{col:day_rate}+{col:surcharge}', 10),
    FAMPH(), CENTER()], D.drop_in_d(), 80))
# 13 discount rules ---------------------------------------------------------
tables.append(T('discount_rules', 'Discount Rules', 'Discount and waiver rules with their yearly cost',
    'One row per rule: the share you give; the yearly cost fills in from the children, late fees and starters.', [
    C('rule', 'Rule', 'text', 24, required=True), C('share', 'Share', 'pct', 10),
    CA('yearly_cost', 'Yearly cost', 'money', 'CHOOSE(MATCH({col:rule},{range:discount_rules.rule},0),SUMIFS({range:children.weekly_discount},{range:children.discount},%s,{range:children.status},%s)*{set:weeks_open},SUMIFS({range:children.weekly_discount},{range:children.discount},%s,{range:children.status},%s)*{set:weeks_open},SUMIFS({range:late_fees.fee},{range:late_fees.waived},%s,{range:late_fees.date},">="&({today}-365)),{col:share}*{set:reg_fee}*COUNTIFS({range:starters.start_date},">="&({today}-365)),{col:share}*SUMIFS({range:drop_in.surcharge},{range:drop_in.date},">="&({today}-365)))' % (
        tok('discount', 'Sibling'), ENR, tok('discount', 'Staff'), ENR, YES), 12)], D.discount_rules_d(), 50))
# 14 repeat late families ----------------------------------------------------
LF6 = '{range:late_fees.family},{col:family},{range:late_fees.date},">="&({today}-180)'
tables.append(T('repeat_late', 'Repeat-Late Families', 'Families with late pickups in the last 6 months',
    'One row per family that collects late: events, minutes, fees charged, waivers and overtime cost for the last 6 months fill in from the Late Fees sheet; a status flags the repeat-late families.', [
    REF('family', 'Family', 'families.family', 22, required=True),
    CA('events', 'Late pickups, 6 months', 'int', 'COUNTIFS(%s)' % LF6, 10), CA('minutes', 'Late minutes', 'int', 'SUMIFS({range:late_fees.late_minutes},%s)' % LF6, 9), CA('fees', 'Fees charged', 'money', 'SUMIFS({range:late_fees.charged},%s)' % LF6, 10),
    CA('waived_n', 'Waived', 'int', 'COUNTIFS(%s,{range:late_fees.waived},%s)' % (LF6, YES), 8), CA('share_waived', 'Share waived', 'pct', 'IF({col:events}>0,{col:waived_n}/{col:events},0)', 9),
    CA('overtime', 'Overtime cost', 'money', 'SUMIFS({range:late_fees.overtime_cost},%s)' % LF6, 10), CA('status', 'Status', 'text', 'IF({col:events}>={set:repeat_events},%s,%s)' % (ca('Repeat late'), ca('Occasional')), 11),
    CA('rank_score', 'Rank score', 'int', '{col:events}*1000+MIN(999,{col:minutes})', 9), FAMPH(), CENTER()], D.repeat_late_d(), 60, [A('status', '= ' + ca('Repeat late'), 'warn')]))
# 15 / 16 invoice runs ------------------------------------------------------
def run_cols(weekly):
    f = 1 if weekly else '52/12'
    win = '{col:run_date}-7,{range:%s.date},"<"&{col:run_date}' if weekly else 'EDATE({col:run_date},-1),{range:%s.date},"<"&{col:run_date}'
    ex = 'SUMIFS({range:late_fees.charged},{range:late_fees.family},{col:family},{range:late_fees.date},">="&%s)+SUMIFS({range:drop_in.charge},{range:drop_in.family},{col:family},{range:drop_in.date},">="&%s)' % (win % 'late_fees', win % 'drop_in')
    cols = [REF('family', 'Family', 'families.family', 22, required=True),
        CA('children', 'Children', 'int', 'COUNTIFS({range:children.family},{col:family},{range:children.status},"<>"&%s)' % LEFT, 8),
        CA('tuition', 'Tuition', 'money', 'ROUND(SUMIFS({range:children.weekly_rate},{range:children.family},{col:family},{range:children.status},"<>"&%s)*%s,2)' % (LEFT, f), 11),
        CA('discount', 'Discount', 'money', 'ROUND(SUMIFS({range:children.weekly_discount},{range:children.family},{col:family},{range:children.status},"<>"&%s)*%s,2)' % (LEFT, f), 10),
        CA('extras', 'Extras', 'money', 'ROUND(%s,2)' % ex, 9), CA('amount', 'Amount', 'money', '{col:tuition}-{col:discount}+{col:extras}', 10),
        CA('gov_expected', 'Government expected', 'money', 'ROUND(({col:tuition}-{col:discount})*%s,2)' % LKN('families.gov_share', 'families.family', 'family'), 12),
        CA('parent_due', 'Parent due', 'money', '{col:amount}-{col:gov_expected}', 10), CA('run_date', 'Run date', 'date', NEXT_MON if weekly else NEXT_1ST, 11),
        CA('due_date', 'Due date', 'date', '{col:run_date}+%s' % ('{set:weekly_due_days}' if weekly else '{set:invoice_days}'), 11),
        CA('run_check', 'Run check', 'text', 'IF({col:children}>0,%s,%s)' % (ca('On the run'), ca('No child enrolled')), 12), FAMPH(), DIR_PH(), CENTER()]
    return cols
tables.append(T('weekly_run', 'Weekly Invoice Run', 'Next weekly invoice run, family by family',
    'One row per family billed weekly: children, tuition, discount, extras from last week and the amount due on the Friday; run date, government share and parent due fill in by themselves.', run_cols(True), D.weekly_run_d(), 60))
tables.append(T('monthly_run', 'Monthly Invoice Run', 'Next monthly invoice run, family by family',
    'One row per family billed monthly: children, tuition at 52 weeks over 12, discount, extras from last month, amount, government expected and parent due fill in by themselves for the run on the 1st.', run_cols(False), D.monthly_run_d(), 80))
# 17 starters ---------------------------------------------------------------
tables.append(T('starters', 'New Starters Fees', 'Registration, supply fee and deposit of each new starter',
    'One row per child who started in the last 12 months: start date and the registration fee, supply fee and deposit charged; the expected fees, the fee check and the first invoice fill in by themselves.', [
    REF('child', 'Child', 'children.child', 22, required=True), C('start_date', 'Start date', 'date', 11), C('registration', 'Registration charged', 'num', 11), C('supply_fee', 'Supply fee charged', 'num', 11), C('deposit', 'Deposit paid', 'money', 11),
    CA('family', 'Family', 'text', LKT('children.family', 'children.child', 'child'), 22), CA('room', 'Room', 'text', LKT('children.room', 'children.child', 'child'), 11), CA('weekly_rate', 'Weekly rate', 'money', CH('weekly_rate'), 11),
    CA('cycle', 'Cycle', 'text', LKT('families.cycle', 'families.family', 'family'), 10),
    CA('period_start', 'First period starts', 'date', 'IF({col:cycle}=%s,DATE(YEAR({col:start_date}),MONTH({col:start_date}),1),{col:start_date}-WEEKDAY({col:start_date},2)+1)' % MO, 11),
    CA('period_end', 'First period ends', 'date', 'IF({col:cycle}=%s,EOMONTH({col:start_date},0),{col:period_start}+4)' % MO, 11),
    CA('days_share', 'Share of the period', 'pct', 'IFERROR(NETWORKDAYS(MAX({col:start_date},{col:period_start}),{col:period_end})/NETWORKDAYS({col:period_start},{col:period_end}),0)', 9),
    CA('first_tuition', 'First tuition', 'money', 'ROUND({col:weekly_rate}*IF({col:cycle}=%s,52/12,1)*{col:days_share}*(1-%s),2)' % (MO, CH('discount_pct')), 11),
    CA('first_invoice', 'First invoice', 'money', '{col:first_tuition}+{col:registration}+{col:supply_fee}', 11), CA('reg_due', 'Registration fee', 'money', '{set:reg_fee}', 10),
    CA('fee_flag', 'Fee check', 'text', 'IF({col:registration}>0,%s,%s)' % (ca('Fees charged'), ca('Registration missing')), 14), CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18), CENTER()],
    D.starters_d(), 80, [A('fee_flag', '= ' + ca('Registration missing'), 'bad')]))
# 18 revenue by room and month ---------------------------------------------
tables.append(T('rev_room', 'Revenue by Room', 'Tuition, discounts, extras and revenue by room and month',
    'One row per room and month: the tuition before discounts, the discounts and the extras taken from the invoices; the revenue fills in by itself.', [
    LST('room', 'Room', 'room', 11, required=True), C('month', 'Month', 'date', 11), C('tuition', 'Tuition', 'money', 11), C('discounts', 'Discounts', 'money', 11), C('extras', 'Extras', 'money', 11),
    CA('revenue', 'Revenue', 'money', '{col:tuition}-{col:discounts}+{col:extras}', 11)], D.rev_room_d(), 120))
# 19 invoice status by month -------------------------------------------------
tables.append(T('invoice_status', 'Invoice Status by Month', 'Invoices, billed, paid and unpaid by month',
    'One row per month: invoices issued, billed amount, discounts, government share and paid; the unpaid amount, the share unpaid, late fees against overtime and deposits held fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), C('invoices', 'Invoices', 'int', 9), C('billed', 'Billed', 'money', 12), C('discounts', 'Discounts', 'money', 11), C('government', 'Government share', 'money', 12), C('paid', 'Paid by parents', 'money', 12),
    CA('unpaid', 'Unpaid', 'money', 'ROUND({col:billed}-{col:government}-{col:paid},2)', 11), CA('share_unpaid', 'Share unpaid', 'pct', 'IF({col:billed}-{col:government}>0,{col:unpaid}/({col:billed}-{col:government}),0)', 9),
    CA('late_charged', 'Late fees charged', 'money', 'SUMIFS({range:late_fees.charged},{range:late_fees.month},{col:month})', 11), CA('overtime_cost', 'Overtime cost', 'money', 'SUMIFS({range:late_fees.overtime_cost},{range:late_fees.month},{col:month})', 11),
    CA('deposits_held', 'Deposits held now', 'money', 'SUMIFS({range:deposits.amount},{range:deposits.status},%s)' % HELD, 12), OWNER_PH(), ACC_PH(), CENTER()],
    D.invoice_status_d(), 60, [A('share_unpaid', '> 0.05', 'warn')]))
# 20 closures ----------------------------------------------------------------
tables.append(T('closures', 'Closures', 'Closure days and the tuition of a day',
    'One row per closure day: date, weekday and reason; the tuition of one day for all enrolled children fills in so you can see what a credit costs.', [
    C('closure_id', 'Closure ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('weekday', 'Weekday', 'wday', 11), LST('reason', 'Reason', 'creason', 17),
    CA('day_tuition', 'Tuition of one day', 'money', 'ROUND(SUMIFS({range:children.net_weekly},{range:children.status},%s)/5,2)' % ENR, 12)], D.closures_d(), 60))
assert len(tables) == 20
