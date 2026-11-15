"""Short-term rental host suite part 7: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr7_lists import *
import sr7_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def OWNP(my='owner'): return CA('owner_phone', 'Owner phone', 'text', LKT('units.owner_phone', 'units.owner', my), 18)
def ACC(): return CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCT_PHONE, 18)
def COH(): return CA('cohost_phone', 'Co-host phone', 'text', '"%s"' % D.COHOST_PHONE, 18)
def HOST(): return CA('host_phone', 'Host phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; Y1 = 'DATE(YEAR({today}),MONTH({today})-12,1)'
def W12(col): return '{range:%s},">="&%s,{range:%s},"<"&%s' % (col, Y1, col, MS)
STP, STS, STD = tok('stmst', 'Paid'), tok('stmst', 'Sent'), tok('stmst', 'Draft')
TXP = tok('taxst', 'Filed and paid')
YES = tok('yn', 'Yes')

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('warn_days', 'Days ahead to warn of a payment, a tax date or a contract', 'int', 7),
    S('statement_day', 'Day of the month the owner statements are sent', 'int', 5), S('pay_day', 'Day of the month owners are paid', 'int', 10),
    S('tax_due_day', 'Day of the month the local tax return is due', 'int', 20), S('cohost_fee_pct', 'Co-host fee on net revenue', 'pct', 0.10),
    S('min_mgmt_fee', 'Lowest management fee for one unit in one month', 'money', 90), S('margin_floor', 'Lowest comfortable net to owner as a share of revenue', 'pct', 0.40),
    S('reserve_min', 'Lowest comfortable repair reserve held for an owner', 'money', 600), S('reserve_months', 'Months of costs to hold as a safety reserve', 'num', 2),
    S('tax_tolerance', 'Local tax difference that is not worth chasing', 'money', 5), S('renewal_days', 'Days ahead to warn that an owner contract ends', 'int', 90),
    S('cleaner_rate', 'Cleaner pay per hour', 'money', 17),
]
assert 3 <= len(settings) <= 20

tables = [
    T('statements', 'Owner Statements', 'Monthly owner statements with fees, costs and net to owner',
      'One row per owner and month: revenue, fees, costs, management fee and net to owner; margin, sending and payment checks and 12-month totals fill in by themselves.', [
        C('statement_id', 'Statement ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('owner', 'Owner', 'owners.name', 22), C('units', 'Units', 'int', 7), C('nights', 'Nights', 'int', 8),
        C('revenue', 'Revenue', 'money', 12), C('platform_fees', 'Platform fees', 'money', 12), C('cleaning_costs', 'Cleaning costs', 'money', 12), C('supplies', 'Supplies', 'money', 11), C('maintenance', 'Maintenance', 'money', 12),
        C('utilities', 'Utilities', 'money', 11), C('mgmt_pct', 'Management percent', 'pct', 11), C('mgmt_fee', 'Management fee', 'money', 12), C('net_to_owner', 'Net to owner', 'money', 12),
        LST('status', 'Status', 'stmst', 9), C('sent_on', 'Sent on', 'date', 11), C('paid_on', 'Paid on', 'date', 11),
        CA('total_costs', 'Total costs and fee', 'money', '{col:platform_fees}+{col:cleaning_costs}+{col:supplies}+{col:maintenance}+{col:utilities}+{col:mgmt_fee}', 12),
        CA('costs_share', 'Costs share of revenue', 'pct', 'IF({col:revenue}>0,({col:total_costs}-{col:mgmt_fee})/{col:revenue},0)', 11),
        CA('fee_share', 'Fee share of revenue', 'pct', 'IF({col:revenue}>0,{col:mgmt_fee}/{col:revenue},0)', 11),
        CA('net_margin', 'Net to owner margin', 'pct', 'IF({col:revenue}>0,{col:net_to_owner}/{col:revenue},0)', 11),
        CA('net_calc', 'Net worked out', 'money', '{col:revenue}-{col:total_costs}', 12),
        CA('check_flag', 'Statement check', 'text', 'IF(ABS({col:net_calc}-{col:net_to_owner})+ABS({col:mgmt_pct}*({col:revenue}-{col:platform_fees})-{col:mgmt_fee})>0.05,%s,%s)' % (ca('Statement does not add up'), ca('Statement adds up')), 22),
        CA('sent_due', 'Send by', 'date', 'DATE(YEAR({col:month}),MONTH({col:month})+1,{set:statement_day})', 11),
        CA('pay_due', 'Pay by', 'date', 'DATE(YEAR({col:month}),MONTH({col:month})+1,{set:pay_day})', 11),
        CA('sent_flag', 'Sending check', 'text', 'IF({col:sent_on}=0,%s,IF({col:sent_on}<={col:sent_due},%s,%s))' % (ca('Not sent yet'), ca('Sent on time'), ca('Sent late')), 14),
        CA('pay_flag', 'Payment check', 'text', 'IF({col:status}=%s,IF({col:paid_on}<={col:pay_due},%s,%s),IF({col:status}=%s,IF({today}>{col:pay_due},%s,%s),%s))' % (STP, ca('Paid on time'), ca('Paid late'), STS, ca('Payment overdue'), ca('Payment due'), ca('Draft statement')), 16),
        CA('margin_flag', 'Margin check', 'text', 'IF({col:net_to_owner}<0,%s,IF({col:net_margin}<{set:margin_floor},%s,%s))' % (ca('Net is negative'), ca('Margin below the floor'), ca('Margin fine')), 22),
        CA('own_rev_12m', 'Owner revenue, 12 months', 'money', 'SUMIFS({range:statements.revenue},{range:statements.owner},{col:owner},%s)' % W12('statements.month'), 13),
        CA('own_net_12m', 'Owner net, 12 months', 'money', 'SUMIFS({range:statements.net_to_owner},{range:statements.owner},{col:owner},%s)' % W12('statements.month'), 13),
        CA('own_fee_12m', 'Management fees, 12 months', 'money', 'SUMIFS({range:statements.mgmt_fee},{range:statements.owner},{col:owner},%s)' % W12('statements.month'), 13),
        OWNP(), ACC(), HOST()],
      D.statements_d(), 120, [A('pay_flag', '= ' + ca('Payment overdue'), 'bad'), A('margin_flag', '= ' + ca('Margin below the floor'), 'warn'), A('margin_flag', '= ' + ca('Net is negative'), 'bad'),
                              A('check_flag', '= ' + ca('Statement does not add up'), 'bad'), A('sent_flag', '= ' + ca('Sent late'), 'warn'), A('pay_flag', '= ' + ca('Paid on time'), 'good')]),
    T('owners', 'Owners', 'Owners with the kind of service and the management percent',
      'The host\'s own portfolio and the three owners whose units are managed; the statements, units and contracts look these up.', [
        C('name', 'Name', 'text', 24, required=True), LST('kind', 'Kind', 'okind', 18), C('mgmt_pct', 'Management percent', 'pct', 12)], D.owners_d(), 50),
    T('units', 'Units', 'Units with owner, management percent and 12-month results',
      'One row per unit with its type, city, owner and management percent; the revenue, net to owner and management fee of the last 12 months and the margin fill in from the statement lines.', [
        C('unit_id', 'Unit ID', 'text', 9, required=True), C('name', 'Name', 'text', 26), C('unit_type', 'Unit type', 'text', 11), LST('city', 'City', 'city', 10), REF('owner', 'Owner', 'owners.name', 22),
        C('mgmt_pct', 'Management percent', 'pct', 11), C('since', 'Managed since', 'date', 11), C('owner_phone', 'Owner phone', 'text', 18),
        CA('unit_kind', 'Kind of unit', 'text', 'IF({col:mgmt_pct}>0,%s,%s)' % (cb('Managed unit'), cb('Own unit')), 14),
        CA('revenue_12m', 'Revenue, 12 months', 'money', 'SUMIFS({range:lines.amount},{range:lines.unit},{col:name},{range:lines.kind},%s,%s)' % (tok('lkind', 'Revenue'), W12('lines.month')), 13),
        CA('net_12m', 'Net to owner, 12 months', 'money', 'SUMIFS({range:lines.signed},{range:lines.unit},{col:name},%s)' % W12('lines.month'), 13),
        CA('fee_12m', 'Management fee, 12 months', 'money', 'SUMIFS({range:lines.amount},{range:lines.unit},{col:name},{range:lines.kind},%s,%s)' % (tok('lkind', 'Management fee'), W12('lines.month')), 13),
        CA('margin_12m', 'Net margin, 12 months', 'pct', 'IF({col:revenue_12m}>0,{col:net_12m}/{col:revenue_12m},0)', 11),
        CA('bookings_12m', 'Bookings, 12 months', 'int', 'COUNTIFS({range:bookings.unit},{col:name},%s,{range:bookings.status},"<>"&%s)' % (W12('bookings.check_out'), tok('bstatus', 'Cancelled')), 11)],
      D.units_d(), 50, [A('margin_12m', '< 0.4', 'warn'), A('margin_12m', '> 0.6', 'good')]),
    T('lines', 'Statement Lines', 'Statement lines by unit, month and kind',
      'One row per unit, month and kind of line (revenue, fees, costs) behind each statement, with the booking or repair it comes from; the signed amount and the owner fill in by themselves.', [
        C('line_id', 'Line ID', 'text', 9, required=True), REF('statement', 'Statement', 'statements.statement_id', 11), REF('unit', 'Unit', 'units.name', 26), C('month', 'Month', 'date', 11), LST('kind', 'Kind of line', 'lkind', 15),
        C('amount', 'Amount', 'money', 11), C('ref_id', 'Booking or repair ID', 'text', 12),
        CA('signed', 'Signed amount', 'money', 'IF({col:kind}=%s,{col:amount},-{col:amount})' % tok('lkind', 'Revenue'), 11), CA('owner', 'Owner', 'text', LKT('statements.owner', 'statements.statement_id', 'statement'), 22)],
      D.lines_d(), 600),
    T('payments', 'Owner Payments', 'Owner payments with date, method and payment check',
      'One row per payment made or planned to an owner, linked to its statement; the owner, the statement net, the day the payment was due and the on-time check fill in by themselves.', [
        C('pay_id', 'Payment ID', 'text', 10, required=True), REF('statement', 'Statement', 'statements.statement_id', 11), C('date', 'Date', 'date', 11), C('amount', 'Amount', 'money', 12), LST('method', 'Method', 'pmeth', 14), LST('status', 'Status', 'pstat', 10),
        CA('owner', 'Owner', 'text', LKT('statements.owner', 'statements.statement_id', 'statement'), 22), CA('stmt_month', 'Statement month', 'date', LKN('statements.month', 'statements.statement_id', 'statement'), 11),
        CA('stmt_net', 'Statement net', 'money', LKN('statements.net_to_owner', 'statements.statement_id', 'statement'), 12), CA('share', 'Share of the statement', 'pct', 'IF({col:stmt_net}>0,{col:amount}/{col:stmt_net},0)', 11),
        CA('pay_due', 'Pay by', 'date', LKN('statements.pay_due', 'statements.statement_id', 'statement'), 11),
        CA('pay_flag', 'Payment check', 'text', 'IF({col:status}=%s,IF({col:date}<={col:pay_due},%s,%s),IF({col:status}=%s,%s,%s))' % (tok('pstat', 'Paid'), ca('Paid on time'), ca('Paid late'), tok('pstat', 'Delayed'), ca('Delayed'), ca('Scheduled')), 14),
        OWNP(), HOST()],
      D.payments_d(), 150, [A('pay_flag', '= ' + ca('Delayed'), 'bad'), A('pay_flag', '= ' + ca('Paid late'), 'warn'), A('pay_flag', '= ' + ca('Paid on time'), 'good')]),
    T('cohost_fees', 'Co-host Fees', 'Co-host fees on net revenue with fee per message',
      'One row per month: revenue and platform fees of the units the co-host handles, the fee percent and the messages answered; the fee check, the fee per message and the fee share fill in by themselves.', [
        C('fee_id', 'Fee ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('units', 'Units', 'int', 7), C('revenue', 'Revenue', 'money', 12), C('platform_fees', 'Platform fees', 'money', 12),
        C('net_revenue', 'Net revenue', 'money', 12), C('fee_pct', 'Fee percent', 'pct', 10), C('fee_amount', 'Fee amount', 'money', 12), C('messages', 'Messages', 'int', 9), C('status', 'Status', 'text', 10), C('paid_on', 'Paid on', 'date', 11),
        CA('fee_per_message', 'Fee per message', 'money', 'IF({col:messages}>0,{col:fee_amount}/{col:messages},0)', 11), CA('fee_calc', 'Fee at the rate', 'money', 'ROUND({col:net_revenue}*{col:fee_pct},2)', 11),
        CA('fee_check', 'Fee check', 'text', 'IF(ABS({col:fee_calc}-{col:fee_amount})>0.05,%s,%s)' % (ca('Fee differs from the rate'), ca('Fee matches the rate')), 22),
        CA('msg_check', 'Message check', 'text', 'IF({col:fee_per_message}>1.3*AVERAGE({range:cohost_fees.fee_per_message}),%s,%s)' % (ca('Fee per message high'), ca('Fee per message normal')), 20),
        CA('fee_share', 'Fee share of revenue', 'pct', 'IF({col:revenue}>0,{col:fee_amount}/{col:revenue},0)', 11), COH(), HOST(), ACC()],
      D.cohost_fees_d(), 60, [A('msg_check', '= ' + ca('Fee per message high'), 'warn'), A('fee_check', '= ' + ca('Fee differs from the rate'), 'bad')]),
    T('duties', 'Co-host Duties', 'Co-host duties logged by unit with minutes',
      'One row per duty the co-host did or must do: task, unit and minutes; the hours and the duty check (done, planned or overdue) fill in by themselves.', [
        C('duty_id', 'Duty ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('task', 'Task', 'duty', 15), REF('unit', 'Unit', 'units.name', 26), C('minutes', 'Minutes', 'int', 9), LST('done', 'Done', 'yn', 8),
        CA('hours', 'Hours', 'num', '{col:minutes}/60', 8), CA('duty_flag', 'Duty check', 'text', 'IF({col:done}=%s,%s,IF({col:date}<{today},%s,%s))' % (YES, cb('Duty done'), cb('Duty overdue'), cb('Duty planned')), 13), COH(), HOST()],
      D.duties_d(), 200, [A('duty_flag', '= ' + cb('Duty overdue'), 'bad'), A('duty_flag', '= ' + cb('Duty planned'), 'warn')]),
    T('bookings', 'Bookings', 'Bookings on owner units with earned amount and platform fee',
      'One row per booking on a managed unit: guest, dates, earned amount and platform fee; the statement month, the net after the fee and the fee share fill in by themselves.', [
        C('booking_id', 'Booking ID', 'text', 10, required=True), REF('unit', 'Unit', 'units.name', 26), REF('owner', 'Owner', 'owners.name', 22), C('guest', 'Guest', 'text', 24), C('check_in', 'Check-in', 'date', 11),
        C('check_out', 'Check-out', 'date', 11), C('nights', 'Nights', 'int', 8), C('earned', 'Earned', 'money', 11), C('platform_fee', 'Platform fee', 'money', 11), LST('status', 'Status', 'bstatus', 11),
        CA('month', 'Statement month', 'date', 'DATE(YEAR({col:check_out}),MONTH({col:check_out}),1)', 11), CA('net_after_fee', 'Net after the fee', 'money', '{col:earned}-{col:platform_fee}', 11),
        CA('fee_share', 'Fee share', 'pct', 'IF({col:earned}>0,{col:platform_fee}/{col:earned},0)', 9), CA('per_night', 'Earned per night', 'money', 'IF({col:nights}>0,{col:earned}/{col:nights},0)', 11), OWNP()],
      D.bookings_d(), 700, [A('status', '= ' + tok('bstatus', 'Cancelled'), 'bad'), A('fee_share', '> 0.14', 'warn')]),
    T('local_tax', 'Local Tax', 'Local occupancy tax by city and month',
      'One row per city and month: the tax collected (a tax on each night, collected from the guest) by host and platform; the tax to remit, due date and checks fill in.', [
        C('tax_id', 'Tax ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('city', 'City', 'city', 10), C('tax_pct', 'Tax percent', 'pct', 9), C('nights', 'Nights', 'int', 8), C('room_revenue', 'Room revenue', 'money', 12),
        C('tax_collected', 'Tax collected', 'money', 11), C('collected_by_host', 'Collected by host', 'money', 11), C('platform_reported', 'Platform reported', 'money', 11), C('due_date', 'Due date', 'date', 11), C('remitted', 'Remitted', 'money', 11),
        C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'taxst', 12),
        CA('platform_part', 'Collected by platform', 'money', '{col:tax_collected}-{col:collected_by_host}', 12), CA('tax_diff', 'Platform report difference', 'money', '{col:platform_reported}-{col:platform_part}', 12),
        CA('tax_check', 'Tax check', 'text', 'IF(ABS({col:tax_diff})>{set:tax_tolerance},%s,%s)' % (ca('Difference to explain'), ca('Tax matches')), 20),
        CA('adj_sum', 'Adjustments', 'money', 'SUMIFS({range:adjustments.amount},{range:adjustments.month},{col:month},{range:adjustments.city},{col:city})', 11),
        CA('to_remit', 'Tax to remit', 'money', 'IF({col:status}=%s,{col:remitted},{col:collected_by_host}+{col:adj_sum})' % TXP, 11),
        CA('days_to_due', 'Days to the due date', 'int', 'IF({col:status}=%s,0,{col:due_date}-{today})' % TXP, 11),
        CA('file_flag', 'Filing check', 'text', 'IF({col:status}=%s,IF({col:paid_on}<={col:due_date},%s,%s),IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<={set:warn_days},%s,%s)))' % (TXP, ca('Filed on time'), ca('Filed late'), ca('Overdue'), ca('Due soon'), ca('Not yet due')), 13),
        CA('city_12m', 'City tax collected, 12 months', 'money', 'SUMIFS({range:local_tax.tax_collected},{range:local_tax.city},{col:city},%s)' % W12('local_tax.month'), 13),
        CA('city_host_12m', 'City tax collected by host, 12 months', 'money', 'SUMIFS({range:local_tax.collected_by_host},{range:local_tax.city},{col:city},%s)' % W12('local_tax.month'), 13),
        CA('city_paid_12m', 'City tax remitted, 12 months', 'money', 'SUMIFS({range:local_tax.remitted},{range:local_tax.city},{col:city},%s)' % W12('local_tax.month'), 13), ACC(), HOST()],
      D.local_tax_d(), 200, [A('file_flag', '= ' + ca('Overdue'), 'bad'), A('file_flag', '= ' + ca('Due soon'), 'warn'), A('tax_check', '= ' + ca('Difference to explain'), 'warn'), A('file_flag', '= ' + ca('Filed late'), 'warn')]),
    T('cities', 'Cities', 'Cities with the local tax percent and who collects it',
      'One row per city and collector (the host or the booking platform) with the local occupancy tax percent that the tools and the tax rows use.', [
        LST('city', 'City', 'city', 12, required=True), LST('collector', 'Tax collected by', 'coll', 14), C('tax_pct', 'Tax percent', 'pct', 11)], D.cities_d(), 50),
    T('adjustments', 'Tax Adjustments', 'Local tax adjustments with reason and filing date',
      'One row per correction to a local tax return: month, city, reason and the amount (positive adds tax, negative reduces it); the effect and the filing check fill in by themselves.', [
        C('adj_id', 'Adjustment ID', 'text', 11, required=True), C('month', 'Month', 'date', 11), LST('city', 'City', 'city', 10), LST('reason', 'Reason', 'adj', 22), C('amount', 'Amount', 'money', 11), C('filed_on', 'Filed on', 'date', 11),
        CA('effect', 'Effect', 'text', 'IF({col:amount}>=0,%s,%s)' % (cb('Adds to the return'), cb('Reduces the return')), 18), CA('filing_flag', 'Filing check', 'text', 'IF({col:filed_on}=0,%s,%s)' % (cb('Not yet filed'), cb('Filed')), 13),
        CA('days_to_file', 'Days from month start to filing', 'int', 'IF({col:filed_on}=0,{today}-{col:month},{col:filed_on}-{col:month})', 12), ACC(), HOST()],
      D.adjustments_d(), 80, [A('filing_flag', '= ' + cb('Not yet filed'), 'warn')]),
    T('tiers', 'Fee Tiers', 'Management fee tiers by package and units managed',
      'The fee percent for each service package and number of units an owner brings; the fee on the average monthly statement fills in by itself.', [
        C('tier', 'Tier', 'text', 24, required=True), LST('package', 'Package', 'pkg', 11), C('units_from', 'Units from', 'int', 9), C('units_to', 'Units to', 'int', 9), C('fee_pct', 'Fee percent', 'pct', 10),
        C('services', 'Services included', 'text', 30),
        CA('fee_on_avg', 'Fee on an average statement', 'money', 'ROUND({col:fee_pct}*(AVERAGE({range:statements.revenue})-AVERAGE({range:statements.platform_fees})),0)', 13)], D.tiers_d(), 50),
    T('requests', 'Owner Requests', 'Owner requests with cost and days open',
      'One row per request from an owner: the unit, what was asked, the cost and the day it was done; the status and the days open fill in by themselves.', [
        C('req_id', 'Request ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('owner', 'Owner', 'owners.name', 22), REF('unit', 'Unit', 'units.name', 26), LST('request', 'Request', 'req', 16), C('done_on', 'Done on', 'date', 11),
        C('cost', 'Cost', 'money', 11), CA('status', 'Status', 'text', 'IF({col:done_on}=0,%s,%s)' % (cb('Request open'), cb('Request done')), 13),
        CA('days_open', 'Days open', 'int', 'IF({col:done_on}=0,{today}-{col:date},{col:done_on}-{col:date})', 9), OWNP(), COH(), HOST()],
      D.requests_d(), 150, [A('status', '= ' + cb('Request open'), 'warn'), A('days_open', '> 10', 'bad')]),
    T('stays', 'Owner Stays', 'Owner stays with cleaning and linen charged',
      'One row per stay of an owner in their own unit: dates, the cleaning and linen charged; the nights, the total charge and whether the stay is upcoming fill in by themselves.', [
        C('stay_id', 'Stay ID', 'text', 9, required=True), REF('owner', 'Owner', 'owners.name', 22), REF('unit', 'Unit', 'units.name', 26), C('check_in', 'Check-in', 'date', 11), C('check_out', 'Check-out', 'date', 11),
        C('cleaning_charged', 'Cleaning charged', 'money', 11), C('linen_charged', 'Linen charged', 'money', 11), CA('nights', 'Nights', 'int', '{col:check_out}-{col:check_in}', 8),
        CA('stay_charge', 'Total charged', 'money', '{col:cleaning_charged}+{col:linen_charged}', 11), CA('stay_flag', 'Stay check', 'text', 'IF({col:check_in}>={today},%s,%s)' % (cb('Upcoming stay'), cb('Past stay')), 13), OWNP()],
      D.stays_d(), 80, [A('stay_flag', '= ' + cb('Upcoming stay'), 'good')]),
    T('reserves', 'Owner Reserves', 'Owner repair reserves held and spent by month',
      'One row per owner and month: money added to the repair reserve and money spent from it; the running balance and the low-reserve check fill in by themselves.', [
        C('reserve_id', 'Reserve ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('owner', 'Owner', 'owners.name', 22), C('reserve_held', 'Reserve held', 'money', 12), C('spent', 'Spent', 'money', 11),
        CA('balance', 'Balance', 'money', 'SUMIFS({range:reserves.reserve_held},{range:reserves.owner},{col:owner},{range:reserves.month},"<="&{col:month})-SUMIFS({range:reserves.spent},{range:reserves.owner},{col:owner},{range:reserves.month},"<="&{col:month})', 12),
        CA('low_flag', 'Reserve check', 'text', 'IF({col:balance}<{set:reserve_min},%s,%s)' % (ca('Reserve low'), ca('Reserve fine')), 13), OWNP()],
      D.reserves_d(), 120, [A('low_flag', '= ' + ca('Reserve low'), 'warn')]),
    T('expenses', 'Expenses', 'Expenses on owner units and on the portfolio',
      'One row per cost paid: date, unit, category, description, amount and who was paid; the month, the owner and who carries the cost fill in by themselves.', [
        C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('unit', 'Unit', 'text', 26), LST('category', 'Category', 'ecat', 20), C('description', 'Description', 'text', 28), C('amount', 'Amount', 'money', 11),
        C('paid_to', 'Paid to', 'text', 22),
        CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('owner', 'Owner', 'text', 'IFERROR(INDEX({range:units.owner},MATCH({col:unit},{range:units.name},0)),INDEX({range:owners.name},5))', 22),
        CA('carried_by', 'Carried by', 'text', 'IF(IFERROR(INDEX({range:units.mgmt_pct},MATCH({col:unit},{range:units.name},0)),0)>0,%s,%s)' % (cb('Charged to owner'), cb('Paid by the host')), 15)],
      D.expenses_d(), 700, [A('carried_by', '= ' + cb('Charged to owner'), 'good')]),
    T('cleaner_pay', 'Cleaner Pay', 'Cleaner pay by month with pay per turnover',
      'One row per cleaner and month: turnovers (the clean and reset between two stays), hours and the amount paid; the pay per turnover, the hourly rate and the rate check fill in by themselves.', [
        C('pay_id', 'Pay ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), REF('cleaner', 'Cleaner', 'team.name', 22), C('turnovers', 'Turnovers', 'int', 10), C('hours', 'Hours', 'num', 9), C('amount', 'Amount', 'money', 11),
        C('paid_on', 'Paid on', 'date', 11), CA('pay_per_turnover', 'Pay per turnover', 'money', 'IF({col:turnovers}>0,{col:amount}/{col:turnovers},0)', 11), CA('rate_per_hour', 'Rate per hour', 'money', 'IF({col:hours}>0,{col:amount}/{col:hours},0)', 10),
        CA('rate_flag', 'Rate check', 'text', 'IF(ABS({col:rate_per_hour}-{set:cleaner_rate})<=0.5,%s,%s)' % (ca('Pay rate on target'), ca('Pay rate off target')), 18), CA('cleaner_phone', 'Cleaner phone', 'text', LKT('team.phone', 'team.name', 'cleaner'), 18)],
      D.cleaner_pay_d(), 200, [A('rate_flag', '= ' + ca('Pay rate off target'), 'warn')]),
    T('maint', 'Maintenance Costs', 'Maintenance costs by repair and who pays',
      'One row per finished repair with a cost: unit, date, cost and whether it is charged to the owner; the owner, the month and the charge check fill in by themselves.', [
        C('ticket_id', 'Ticket ID', 'text', 10, required=True), REF('unit', 'Unit', 'units.name', 26), C('done_on', 'Done on', 'date', 11), C('cost', 'Cost', 'money', 11), LST('charged_to_owner', 'Charged to owner', 'yn', 11),
        CA('owner', 'Owner', 'text', LKT('units.owner', 'units.name', 'unit'), 22), CA('month', 'Month', 'date', 'DATE(YEAR({col:done_on}),MONTH({col:done_on}),1)', 11),
        CA('charge_flag', 'Charge check', 'text', 'IF({col:charged_to_owner}=%s,%s,%s)' % (YES, cb('Charged to owner'), cb('Paid by the host')), 15), OWNP('owner')],
      D.maint_d(), 300, [A('cost', '> 400', 'warn')]),
    T('contracts', 'Owner Contracts', 'Owner contracts with end dates and notice dates',
      'One row per contract term for a managed unit: start, end, management percent and notice days; the days to the end, the notice date and the renewal check fill in by themselves.', [
        C('contract_id', 'Contract ID', 'text', 10, required=True), REF('owner', 'Owner', 'owners.name', 22), REF('unit', 'Unit', 'units.name', 26), C('start_date', 'Start', 'date', 11), C('end_date', 'End', 'date', 11),
        C('mgmt_pct', 'Management percent', 'pct', 11), C('notice_days', 'Notice days', 'int', 9),
        CA('term_months', 'Term in months', 'int', 'ROUND(({col:end_date}-{col:start_date}+1)/30.4,0)', 9), CA('days_to_end', 'Days to the end', 'int', '{col:end_date}-{today}', 10),
        CA('end_flag', 'Renewal check', 'text', 'IF({col:end_date}<{today},%s,IF({col:end_date}-{today}<={set:renewal_days},%s,%s))' % (cb('Term ended'), cb('Ends within 90 days'), cb('Running')), 19),
        CA('notice_by', 'Notice by', 'date', '{col:end_date}-{col:notice_days}', 11), CA('notice_flag', 'Notice check', 'text', 'IF({col:notice_by}<{today},%s,%s)' % (cb('Notice date passed'), cb('Notice date ahead')), 18), OWNP(), HOST()],
      D.contracts_d(), 50, [A('end_flag', '= ' + cb('Ends within 90 days'), 'warn'), A('end_flag', '= ' + cb('Running'), 'good')]),
    T('team', 'Team', 'Team with cleaner pay of the last 12 months',
      'The host, the co-host (a helper who handles guests for a fee), four cleaners, two handypeople and four outside contacts; the pay and the turnovers of the last 12 months fill in for each cleaner.', [
        C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 14), LST('team', 'Team', 'team', 12), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
        C('hours_week', 'Hours a week', 'int', 10), C('hourly_rate', 'Hourly rate', 'money', 10), C('speciality', 'Speciality', 'text', 26), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
        CA('pay_12m', 'Cleaner pay, 12 months', 'money', 'SUMIFS({range:cleaner_pay.amount},{range:cleaner_pay.cleaner},{col:name},%s)' % W12('cleaner_pay.month'), 12),
        CA('turnovers_12m', 'Turnovers, 12 months', 'int', 'SUMIFS({range:cleaner_pay.turnovers},{range:cleaner_pay.cleaner},{col:name},%s)' % W12('cleaner_pay.month'), 11)], D.team_d(), 50),
]
assert len(tables) == 20, len(tables)
