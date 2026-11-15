"""Short-term rental host suite part 5: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr5_lists import *
import sr5_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def OWNP(my='unit'): return CA('owner_phone', 'Owner phone', 'text', LKT('units.owner_phone', 'units.name', my), 18)
def COH(): return CA('cohost_phone', 'Co-host phone', 'text', '"%s"' % D.COHOST_PHONE, 18)
def HOST(): return CA('host_phone', 'Host phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def ACC(): return CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCT_PHONE, 18)
TS = lambda s: tok('tkst', s)
YES = tok('yn', 'Yes'); NO = tok('yn', 'No')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'; YS = 'DATE(YEAR({today}),1,1)'

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('fix_days_high', 'Days to fix a high priority ticket', 'int', 2), S('fix_days_normal', 'Days to fix a normal priority ticket', 'int', 5),
    S('fix_days_low', 'Days to fix a low priority ticket', 'int', 30), S('due_soon_days', 'Days before the fix-by date to mark a ticket due soon', 'int', 2),
    S('warn_days', 'Days ahead to warn of a safety check or a deadline', 'int', 7), S('repair_limit', 'Repair cost above which the owner approves first', 'money', 300),
    S('cost_night_target', 'Wanted maintenance cost per booked night', 'money', 9.5), S('claim_wait_days', 'Days a damage claim may wait before you chase it', 'int', 14),
    S('deposit_days', 'Days after check-out to release a deposit', 'int', 7), S('service_warn_days', 'Days ahead to warn of a service', 'int', 30), S('warranty_warn_days', 'Days ahead to warn that a warranty ends', 'int', 60),
    S('repeat_min', 'Tickets of one kind in 12 months that make a repeat issue', 'int', 5), S('pass_score', 'Inspection score needed to pass', 'int', 75), S('appliance_age_limit', 'Appliance age in years to plan a replacement', 'int', 7),
    S('target_adr', 'Wanted average daily rate, the average price of a night sold', 'money', 140),
]
assert 3 <= len(settings) <= 20

TF = 'tickets'
CHK_T = ('IF({col:status}=%s,IF({col:done_on}=0,%s,IF({col:done_on}-{col:reported_on}<={col:limit_days},%s,%s)),IF({col:status}=%s,%s,IF({today}>{col:fix_by},%s,IF({col:fix_by}-{today}<={set:due_soon_days},%s,%s))))'
         % (TS('Done'), ca('Closed on time'), ca('Closed on time'), ca('Closed late'), TS('Waiting parts'), ca('Waiting for parts'), ca('Overdue'), ca('Due soon'), ca('On time')))
NXT_CI = 'SUMPRODUCT(MAX(({range:bookings.unit}={col:name})*({range:bookings.check_in}>{today})*({range:bookings.status}<>%s)*(100000-{range:bookings.check_in})))' % tok('bstatus', 'Cancelled')

tables = [
    T('tickets', 'Maintenance Tickets', 'Maintenance tickets from report to done',
      'One row per problem reported in a unit: kind, priority, handyperson, status and cost; the fix-by date, days open, on-time check, next check-in and phone numbers fill in by themselves.', [
        C('ticket_id', 'Ticket ID', 'text', 10, required=True), C('reported_on', 'Reported on', 'date', 11), REF('unit', 'Unit', 'units.name', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10),
        LST('kind', 'Kind', 'tkind', 18), LST('priority', 'Priority', 'prio', 9), LST('source', 'Source', 'tsrc', 14), REF('handyperson', 'Handyperson', 'team.name', 22), LST('status', 'Status', 'tkst', 13),
        C('done_on', 'Done on', 'date', 11), C('parts_cost', 'Parts cost', 'money', 11), C('labour_cost', 'Labour cost', 'money', 11), LST('guest_impact', 'Guest impact', 'yn', 9), C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18),
        CA('cost', 'Cost', 'money', '{col:parts_cost}+{col:labour_cost}', 11),
        CA('limit_days', 'Days allowed', 'int', 'IF({col:priority}=%s,{set:fix_days_high},IF({col:priority}=%s,{set:fix_days_normal},{set:fix_days_low}))' % (tok('prio', 'High'), tok('prio', 'Normal')), 9),
        CA('fix_by', 'Fix by', 'date', '{col:reported_on}+{col:limit_days}', 11),
        CA('days_open', 'Days open', 'int', 'IF({col:status}=%s,0,{today}-{col:reported_on})' % TS('Done'), 9),
        CA('days_to_fix', 'Days to fix', 'int', 'IF({col:status}=%s,IF({col:done_on}=0,0,MAX(0,{col:done_on}-{col:reported_on})),0)' % TS('Done'), 9),
        CA('chk', 'Ticket check', 'text', CHK_T, 17),
        CA('cost_flag', 'Repair limit check', 'text', 'IF({col:cost}>{set:repair_limit},%s,%s)' % (cb('Over the repair limit'), cb('Within the repair limit')), 18),
        CA('next_checkin', 'Next check-in at the unit', 'date', 'IF(INDEX({range:units.next_checkin},MATCH({col:unit},{range:units.name},0))=0,"",INDEX({range:units.next_checkin},MATCH({col:unit},{range:units.name},0)))', 12),
        CA('days_to_checkin', 'Days to next check-in', 'int', 'IFERROR(INDEX({range:units.days_to_checkin},MATCH({col:unit},{range:units.name},0)),999)', 10),
        CA('handyperson_phone', 'Handyperson phone', 'text', LKT('team.phone', 'team.name', 'handyperson'), 18), OWNP(), COH(), HOST()],
      D.tickets_d(), 700, [A('chk', '= ' + ca('Overdue'), 'bad'), A('chk', '= ' + ca('Closed late'), 'warn'), A('chk', '= ' + ca('Waiting for parts'), 'warn'), A('cost_flag', '= ' + cb('Over the repair limit'), 'warn'), A('guest_impact', '= ' + YES, 'warn')]),
    T('claims', 'Damage Claims', 'Damage claims against guests and platforms',
      'One row per damage found after a stay: booking, guest, channel, amount claimed, deposit held and repair cost; days pending, the amount not recovered and what to claim after the deposit fill in.', [
        C('claim_id', 'Claim ID', 'text', 10, required=True), C('reported_on', 'Reported on', 'date', 11), C('booking_id', 'Booking', 'text', 10), REF('unit', 'Unit', 'units.name', 26), C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18),
        LST('channel', 'Channel', 'chan', 11), C('damage', 'Damage', 'text', 30), C('claimed_amount', 'Claimed amount', 'money', 12), C('deposit_held', 'Deposit held', 'money', 11), C('repair_cost', 'Repair cost', 'money', 11),
        LST('status', 'Status', 'dmst', 13), C('paid_amount', 'Paid amount', 'money', 11), C('paid_on', 'Paid on', 'date', 11),
        CA('unrecovered', 'Unrecovered amount', 'money', 'MAX(0,{col:claimed_amount}-{col:paid_amount})', 12),
        CA('days_pending', 'Days pending', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),{today}-{col:reported_on},0)' % (tok('dmst', 'Pending'), tok('dmst', 'Approved')), 9),
        CA('to_claim', 'To claim after the deposit', 'money', 'MAX(0,{col:claimed_amount}-{col:deposit_held})', 12),
        CA('claim_flag', 'Claim check', 'text', 'IF(OR({col:status}=%s,{col:status}=%s),IF({col:days_pending}>{set:claim_wait_days},%s,%s),%s)' % (tok('dmst', 'Pending'), tok('dmst', 'Approved'), ca('Claim waiting too long'), ca('Claim waiting'), ca('Claim closed')), 20),
        OWNP(), HOST()],
      D.claims_d(), 150, [A('claim_flag', '= ' + ca('Claim waiting too long'), 'bad'), A('claim_flag', '= ' + ca('Claim waiting'), 'warn'), A('status', '= ' + tok('dmst', 'Rejected'), 'warn')]),
    T('units', 'Units', 'Units with maintenance cost and next check-in',
      'One row per unit: type, city, owner and listing date; tickets and cost of the last 12 months, cost per booked night, repeat issues, overdue safety checks and the next check-in fill in by themselves.', [
        C('unit_id', 'Unit ID', 'text', 9, required=True), C('name', 'Name', 'text', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), C('bedrooms', 'Bedrooms', 'int', 9), C('owner', 'Owner', 'text', 22),
        C('owner_phone', 'Owner phone', 'text', 18), C('since', 'Listed since', 'date', 11),
        CA('tickets_12m', 'Tickets, 12 months', 'int', 'COUNTIFS({range:tickets.unit},{col:name},{range:tickets.reported_on},">"&({today}-365))', 10),
        CA('tickets_open', 'Open tickets', 'int', 'COUNTIFS({range:tickets.unit},{col:name},{range:tickets.status},"<>"&%s)' % TS('Done'), 9),
        CA('cost_12m', 'Maintenance cost, 12 months', 'money', 'SUMIFS({range:cost_unit.cost},{range:cost_unit.unit},{col:name},{range:cost_unit.month},">="&%s,{range:cost_unit.month},"<"&%s)' % (Y1, MS), 13),
        CA('nights_12m', 'Booked nights, 12 months', 'int', 'SUMIFS({range:cost_unit.booked_nights},{range:cost_unit.unit},{col:name},{range:cost_unit.month},">="&%s,{range:cost_unit.month},"<"&%s)' % (Y1, MS), 11),
        CA('cost_per_night', 'Cost per booked night', 'money', 'IF({col:nights_12m}>0,{col:cost_12m}/{col:nights_12m},0)', 11),
        CA('cost_flag', 'Cost check', 'text', 'IF({col:cost_per_night}>{set:cost_night_target},%s,%s)' % (cb('Above cost target'), cb('Within cost target')), 16),
        CA('cost_year', 'Cost this year', 'money', 'SUMIFS({range:tickets.cost},{range:tickets.unit},{col:name},{range:tickets.reported_on},">="&%s)' % YS, 12),
        CA('repeat_n', 'Repeat issue kinds', 'int', 'COUNTIFS({range:recurring.unit},{col:name},{range:recurring.flag},%s)' % ca('Repeat issue'), 10),
        CA('repeat_flag', 'Repeat check', 'text', 'IF({col:repeat_n}>0,%s,%s)' % (cb('Repeat issues'), cb('No repeat issues')), 15),
        CA('safety_overdue', 'Safety checks overdue', 'int', 'COUNTIFS({range:safety.unit},{col:name},{range:safety.status},%s)' % ca('Overdue'), 11),
        CA('services_n', 'Services in the schedule', 'int', 'COUNTIFS({range:services.unit},{col:name})', 11),
        CA('services_due', 'Services overdue or due soon', 'int', 'COUNTIFS({range:services.unit},{col:name},{range:services.days_to_due},"<="&{set:service_warn_days})', 12),
        CA('service_cost_year', 'Service cost per year', 'money', 'SUMIFS({range:services.cost_year},{range:services.unit},{col:name})', 12),
        CA('next_checkin', 'Next check-in', 'date', 'IF(%s=0,"",100000-%s)' % (NXT_CI, NXT_CI), 11),
        CA('days_to_checkin', 'Days to next check-in', 'int', 'IF(ISNUMBER({col:next_checkin}),{col:next_checkin}-{today},999)', 10)],
      D.units_d(), 50, [A('cost_flag', '= ' + cb('Above cost target'), 'bad'), A('repeat_flag', '= ' + cb('Repeat issues'), 'warn'), A('safety_overdue', '> 0', 'bad')]),
    T('bookings', 'Bookings', 'Bookings with the issues reported during the stay',
      'One row per booking: unit, guest, channel, dates and status; the nights, the tickets reported during the stay and the damage claims on the booking fill in by themselves.', [
        C('booking_id', 'Booking ID', 'text', 10, required=True), REF('unit', 'Unit', 'units.name', 26), C('guest', 'Guest', 'text', 24), LST('channel', 'Channel', 'chan', 11), C('check_in', 'Check-in', 'date', 11), C('check_out', 'Check-out', 'date', 11),
        LST('status', 'Status', 'bstatus', 11),
        CA('nights', 'Nights', 'int', '{col:check_out}-{col:check_in}', 8),
        CA('issues_during', 'Tickets during the stay', 'int', 'COUNTIFS({range:tickets.unit},{col:unit},{range:tickets.reported_on},">="&{col:check_in},{range:tickets.reported_on},"<="&{col:check_out})', 11),
        CA('claims_n', 'Damage claims', 'int', 'COUNTIFS({range:claims.booking_id},{col:booking_id})', 9), CA('claimed', 'Amount claimed', 'money', 'SUMIFS({range:claims.claimed_amount},{range:claims.booking_id},{col:booking_id})', 11)],
      D.bookings_d(), 400, [A('claims_n', '> 0', 'bad'), A('issues_during', '> 0', 'warn'), A('status', '= ' + tok('bstatus', 'Cancelled'), 'warn')]),
    T('safety', 'Safety Checks', 'Safety checks with the next check date',
      'One row per safety check: unit, item, result, who did it and the next check date; whether the check is the latest, the days left and overdue or due soon fill in by themselves.', [
        C('safety_id', 'Check ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('item', 'Item', 'text', 28), LST('result', 'Result', 'sres', 16), C('next_check', 'Next check', 'date', 11),
        REF('done_by', 'Done by', 'team.name', 22),
        CA('latest', 'Latest check', 'int', 'IF({col:date}=SUMPRODUCT(MAX(({range:safety.unit}={col:unit})*({range:safety.item}={col:item})*{range:safety.date})),1,0)', 9),
        CA('days_left', 'Days to next check', 'int', '{col:next_check}-{today}', 10),
        CA('status', 'Check status', 'text', 'IF({col:latest}=0,%s,IF({col:days_left}<0,%s,IF({col:days_left}<={set:warn_days},%s,%s)))' % (ca('Superseded'), ca('Overdue'), ca('Due soon'), ca('Up to date')), 13),
        CA('doer_phone', 'Handyperson phone', 'text', LKT('team.phone', 'team.name', 'done_by'), 18), HOST()],
      D.safety_d(), 300, [A('status', '= ' + ca('Overdue'), 'bad'), A('status', '= ' + ca('Due soon'), 'warn'), A('result', '= ' + tok('sres', 'Needs repair'), 'warn')]),
    T('services', 'Service Schedule', 'Service schedule with the next due date',
      'One row per recurring service of a unit: how often, when it was last done and the cost; the next due date, the days to it and the cost per year fill in by themselves.', [
        C('service_id', 'Service ID', 'text', 10, required=True), REF('unit', 'Unit', 'units.name', 26), C('service', 'Service', 'text', 30), C('every_months', 'Every months', 'int', 9), C('last_done', 'Last done', 'date', 11), C('cost', 'Cost', 'money', 10),
        CA('next_due', 'Next due', 'date', 'EDATE({col:last_done},{col:every_months})', 11), CA('days_to_due', 'Days to due', 'int', '{col:next_due}-{today}', 9),
        CA('status', 'Service status', 'text', 'IF({col:days_to_due}<0,%s,IF({col:days_to_due}<={set:service_warn_days},%s,%s))' % (ca('Overdue'), ca('Due soon'), ca('On schedule')), 13),
        CA('cost_year', 'Cost per year', 'money', '{col:cost}*12/{col:every_months}', 11), OWNP(), HOST()],
      D.services_d(), 150, [A('status', '= ' + ca('Overdue'), 'bad'), A('status', '= ' + ca('Due soon'), 'warn')]),
    T('appliances', 'Appliance Register', 'Appliances with age and warranty left',
      'One row per appliance in a unit: purchase date, warranty end date and cost; the days of warranty left, the age and the warranty and replacement checks fill in by themselves.', [
        C('app_id', 'Appliance ID', 'text', 11, required=True), REF('unit', 'Unit', 'units.name', 26), C('appliance', 'Appliance', 'text', 20), C('bought_on', 'Bought on', 'date', 11), C('warranty_until', 'Warranty until', 'date', 11), C('cost', 'Cost', 'money', 10),
        CA('warranty_left', 'Warranty left, days', 'int', '{col:warranty_until}-{today}', 10), CA('age_years', 'Age in years', 'num', 'ROUND(({today}-{col:bought_on})/365,1)', 9),
        CA('status', 'Warranty check', 'text', 'IF({col:warranty_left}<0,%s,IF({col:warranty_left}<={set:warranty_warn_days},%s,%s))' % (ca('Warranty expired'), ca('Warranty ends soon'), ca('In warranty')), 17),
        CA('age_flag', 'Age check', 'text', 'IF({col:age_years}>={set:appliance_age_limit},%s,%s)' % (cb('Old, plan a replacement'), cb('Age is fine')), 18), HOST()],
      D.appliances_d(), 200, [A('status', '= ' + ca('Warranty ends soon'), 'warn'), A('age_flag', '= ' + cb('Old, plan a replacement'), 'bad'), A('status', '= ' + ca('In warranty'), 'good')]),
    T('quotes', 'Repair Quotes', 'Repair quotes with decision and days waiting',
      'One row per quote asked from a handyperson or supplier: work, amount and the decision; the days waiting, whether the owner must approve and the supplier and owner phones fill in by themselves.', [
        C('quote_id', 'Quote ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('work', 'Work', 'text', 30), REF('supplier', 'Supplier', 'team.name', 22), C('amount', 'Amount', 'money', 10),
        LST('decision', 'Decision', 'qdec', 11), C('decision_on', 'Decision on', 'date', 11),
        CA('days_waiting', 'Days to decide', 'int', 'IF({col:decision_on}=0,{today}-{col:date},{col:decision_on}-{col:date})', 10),
        CA('flag', 'Quote check', 'text', 'IF({col:decision}=%s,%s,%s)' % (tok('qdec', 'Waiting'), cb('Quote waiting'), cb('Quote decided')), 13),
        CA('limit_flag', 'Owner approval', 'text', 'IF({col:amount}>{set:repair_limit},%s,%s)' % (cb('Over the repair limit'), cb('Within the repair limit')), 18),
        CA('supplier_phone', 'Supplier phone', 'text', LKT('team.phone', 'team.name', 'supplier'), 18), OWNP(), HOST()],
      D.quotes_d(), 120, [A('flag', '= ' + cb('Quote waiting'), 'warn'), A('limit_flag', '= ' + cb('Over the repair limit'), 'warn')]),
    T('parts', 'Parts Orders', 'Parts orders with delivery check',
      'One row per parts order for a ticket: part, quantity, price, supplier and delivery date; the order value, the unit, the handyperson and whether the part is late fill in by themselves.', [
        C('part_id', 'Order ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('ticket_id', 'Ticket', 'tickets.ticket_id', 10), C('part', 'Part', 'text', 24), C('qty', 'Quantity', 'int', 9), C('unit_price', 'Price each', 'money', 10),
        C('supplier', 'Supplier', 'text', 22), C('delivery_date', 'Delivery date', 'date', 11), LST('status', 'Order status', 'pstat', 12),
        CA('amount', 'Order value', 'money', '{col:qty}*{col:unit_price}', 11), CA('unit', 'Unit', 'text', LKT('tickets.unit', 'tickets.ticket_id', 'ticket_id'), 26),
        CA('handyperson', 'Handyperson', 'text', LKT('tickets.handyperson', 'tickets.ticket_id', 'ticket_id'), 22),
        CA('days_to_delivery', 'Days to delivery', 'int', '{col:delivery_date}-{today}', 10),
        CA('flag', 'Delivery check', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:delivery_date}<{today},%s,%s)))' % (tok('pstat', 'Delivered'), ca('Part delivered'), tok('pstat', 'Cancelled'), cb('Order cancelled'), ca('Part late'), ca('Part on the way')), 15),
        CA('handyperson_phone', 'Handyperson phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:handyperson},{range:team.name},0))&"","")', 18)],
      D.parts_d(), 200, [A('flag', '= ' + ca('Part late'), 'bad'), A('flag', '= ' + ca('Part on the way'), 'warn')]),
    T('inspections', 'Inspections', 'Inspections with score and pass check',
      'One row per walk-through inspection of a unit: who inspected, the score and the number of issues found; whether the unit passed your score fills in by itself.', [
        C('insp_id', 'Inspection ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), REF('inspector', 'Inspector', 'team.name', 22), C('score', 'Score', 'int', 8), C('issues', 'Issues found', 'int', 9),
        CA('pass_flag', 'Pass check', 'text', 'IF({col:score}>={set:pass_score},%s,%s)' % (ca('Passed'), ca('Failed')), 10), CA('gap', 'Score against the pass mark', 'int', '{col:score}-{set:pass_score}', 12), HOST()],
      D.inspections_d(), 200, [A('pass_flag', '= ' + ca('Failed'), 'bad'), A('score', '>= 95', 'good')]),
    T('incidents', 'Incidents', 'Incidents during stays with action and close date',
      'One row per incident during a stay: unit, kind, guest and the action taken; the days open and whether it is closed fill in by themselves.', [
        C('inc_id', 'Incident ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('kind', 'Kind', 'text', 30), C('guest', 'Guest', 'text', 24), C('action', 'Action taken', 'text', 30), C('closed_on', 'Closed on', 'date', 11),
        CA('days_open', 'Days to close', 'int', 'IF({col:closed_on}=0,{today}-{col:date},{col:closed_on}-{col:date})', 10),
        CA('status', 'Incident status', 'text', 'IF({col:closed_on}=0,%s,%s)' % (ca('Incident open'), ca('Incident closed')), 14)],
      D.incidents_d(), 100, [A('status', '= ' + ca('Incident open'), 'warn')]),
    T('handy', 'Handyperson Weeks', 'Handyperson hours by week against capacity',
      'One row per handyperson and week: hours worked and jobs done; the weekly capacity from the Team sheet, the spare hours and whether the week was full fill in by themselves.', [
        C('hw_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), REF('handyperson', 'Handyperson', 'team.name', 22), C('hours', 'Hours worked', 'int', 10), C('jobs', 'Jobs done', 'int', 9),
        CA('capacity', 'Capacity, hours', 'int', LKN('team.hours_week', 'team.name', 'handyperson'), 10), CA('spare', 'Spare hours', 'int', '{col:capacity}-{col:hours}', 9),
        CA('load', 'Load check', 'text', 'IF({col:hours}>{col:capacity},%s,IF({col:hours}>={col:capacity}*0.85,%s,%s))' % (ca('Overloaded'), ca('Busy'), ca('Spare capacity')), 15),
        CA('open_tickets', 'Open tickets now', 'int', 'COUNTIFS({range:tickets.handyperson},{col:handyperson},{range:tickets.status},"<>"&%s)' % TS('Done'), 10)],
      D.handy_d(), 120, [A('load', '= ' + ca('Overloaded'), 'bad'), A('load', '= ' + ca('Busy'), 'warn')]),
    T('cost_unit', 'Cost by Unit', 'Maintenance cost by unit and month',
      'One row per unit and month: tickets, parts, labour and booked nights; the cost and the cost per booked night with a check against your target fill in by themselves.', [
        C('cu_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), REF('unit', 'Unit', 'units.name', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), C('tickets', 'Tickets', 'int', 8),
        C('parts_cost', 'Parts cost', 'money', 10), C('labour_cost', 'Labour cost', 'money', 10), C('booked_nights', 'Booked nights', 'int', 10),
        CA('cost', 'Cost', 'money', '{col:parts_cost}+{col:labour_cost}', 10), CA('cost_per_night', 'Cost per booked night', 'money', 'IF({col:booked_nights}>0,{col:cost}/{col:booked_nights},0)', 11),
        CA('flag', 'Cost check', 'text', 'IF({col:cost_per_night}>{set:cost_night_target},%s,%s)' % (cb('Above cost target'), cb('Within cost target')), 16), HOST(), ACC()],
      D.cost_unit_d(), 300, [A('flag', '= ' + cb('Above cost target'), 'warn')]),
    T('warranty', 'Warranty Claims', 'Warranty claims on appliances',
      'One row per warranty claim: the appliance, the date, the amount and the result; the unit, the appliance name and the days waiting fill in by themselves.', [
        C('wc_id', 'Claim ID', 'text', 9, required=True), REF('appliance', 'Appliance ID', 'appliances.app_id', 11), C('claimed_on', 'Claimed on', 'date', 11), C('amount', 'Amount', 'money', 10), LST('result', 'Result', 'wres', 11),
        CA('unit', 'Unit', 'text', LKT('appliances.unit', 'appliances.app_id', 'appliance'), 26), CA('name', 'Appliance', 'text', LKT('appliances.appliance', 'appliances.app_id', 'appliance'), 20),
        CA('days_waiting', 'Days waiting', 'int', 'IF({col:result}=%s,{today}-{col:claimed_on},0)' % tok('wres', 'Waiting'), 9), HOST()],
      D.warranty_d(), 60, [A('result', '= ' + tok('wres', 'Waiting'), 'warn'), A('result', '= ' + tok('wres', 'Rejected'), 'bad')]),
    T('deposits', 'Deposits Held', 'Damage deposits held and released',
      'One row per deposit taken on a direct booking: guest, check-out date, amount, release date and the part kept; the days since check-out and whether it is held, overdue or released fill in.', [
        C('dep_id', 'Deposit ID', 'text', 10, required=True), C('booking_id', 'Booking', 'text', 10), REF('unit', 'Unit', 'units.name', 26), C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18), C('check_out', 'Check-out', 'date', 11),
        C('amount', 'Deposit amount', 'money', 11), C('released_on', 'Released on', 'date', 11), C('kept_amount', 'Kept amount', 'money', 11), C('reason', 'Reason for keeping', 'text', 30),
        CA('days_since', 'Days since check-out', 'int', '{today}-{col:check_out}', 10), CA('held', 'Held now', 'money', 'IF({col:released_on}=0,{col:amount},0)', 10),
        CA('returned', 'Returned to the guest', 'money', 'IF({col:released_on}=0,0,{col:amount}-{col:kept_amount})', 11),
        CA('status', 'Deposit status', 'text', 'IF({col:released_on}=0,IF({col:days_since}>{set:deposit_days},%s,%s),IF({col:kept_amount}>0,%s,%s))' % (cb('Overdue to release'), cb('Deposit held'), cb('Released with deduction'), cb('Released in full')), 20), HOST()],
      D.deposits_d(), 150, [A('status', '= ' + cb('Overdue to release'), 'bad'), A('status', '= ' + cb('Deposit held'), 'warn'), A('status', '= ' + cb('Released with deduction'), 'warn')]),
    T('recurring', 'Recurring Issues', 'Recurring issues by unit and kind',
      'One row per unit and ticket kind that comes back: the root cause and the fix; the tickets in the last 12 months, the last date and whether it is a repeat issue fill in by themselves.', [
        C('rec_id', 'Row ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), LST('kind', 'Kind', 'tkind', 18), C('root_cause', 'Root cause', 'text', 30), C('fix', 'Fix', 'text', 30),
        CA('count_12m', 'Tickets, 12 months', 'int', 'COUNTIFS({range:tickets.unit},{col:unit},{range:tickets.kind},{col:kind},{range:tickets.reported_on},">"&({today}-365))', 10),
        CA('last_date', 'Last ticket', 'date', 'IF(SUMPRODUCT(MAX(({range:tickets.unit}={col:unit})*({range:tickets.kind}={col:kind})*{range:tickets.reported_on}))=0,"",SUMPRODUCT(MAX(({range:tickets.unit}={col:unit})*({range:tickets.kind}={col:kind})*{range:tickets.reported_on})))', 11),
        CA('flag', 'Repeat check', 'text', 'IF({col:count_12m}>={set:repeat_min},%s,IF({col:count_12m}={set:repeat_min}-1,%s,%s))' % (ca('Repeat issue'), ca('Watch'), ca('One-off')), 13)],
      D.recurring_d(), 80, [A('flag', '= ' + ca('Repeat issue'), 'bad'), A('flag', '= ' + ca('Watch'), 'warn')]),
    T('capex', 'Capex Plan', 'Capital spending plan by unit',
      'One row per planned purchase for a unit: item, planned month, cost, yearly saving and reason; the months to go, the payback time and a payback check fill in by themselves.', [
        C('cx_id', 'Plan ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), C('item', 'Item', 'text', 30), C('planned_month', 'Planned month', 'date', 11), C('cost', 'Cost', 'money', 10), C('saving_per_year', 'Saving per year', 'money', 11),
        C('reason', 'Reason', 'text', 30), LST('status', 'Status', 'cxst', 10),
        CA('months_to', 'Months to go', 'int', '(YEAR({col:planned_month})-YEAR({today}))*12+MONTH({col:planned_month})-MONTH({today})', 9),
        CA('payback_months', 'Payback, months', 'int', 'IF({col:saving_per_year}>0,ROUND({col:cost}/{col:saving_per_year}*12,0),0)', 10),
        CA('flag', 'Payback check', 'text', 'IF({col:saving_per_year}=0,%s,IF({col:payback_months}<=24,%s,%s))' % (cb('No saving counted'), cb('Payback under 24 months'), cb('Payback over 24 months')), 22), OWNP(), HOST()],
      D.capex_d(), 80, [A('flag', '= ' + cb('Payback over 24 months'), 'warn'), A('flag', '= ' + cb('Payback under 24 months'), 'good')]),
    T('locks', 'Key and Lock Log', 'Key and lock events with code changes',
      'One row per lock event: unit, what happened, whether the entry code changed and who did it; the days ago and a warning when a lost key has no new code fill in by themselves.', [
        C('lock_id', 'Event ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), LST('event', 'Event', 'levent', 26), LST('code_changed', 'Code changed', 'yn', 9), REF('who', 'Done by', 'team.name', 22),
        CA('days_ago', 'Days ago', 'int', '{today}-{col:date}', 8),
        CA('lock_flag', 'Code check', 'text', 'IF({col:code_changed}=%s,%s,IF({col:event}=%s,%s,%s))' % (YES, cb('Code safe'), tok('levent', 'Key lost'), cb('Change the code now'), cb('Code unchanged')), 20), COH()],
      D.locks_d(), 150, [A('lock_flag', '= ' + cb('Change the code now'), 'bad')]),
    T('pest', 'Pest and Exterior', 'Pest and exterior checks by unit',
      'One row per pest or exterior check: unit, area, finding and the action taken; the days ago and whether the area is clear or needs action fill in by themselves.', [
        C('pe_id', 'Check ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('area', 'Area', 'text', 20), LST('finding', 'Finding', 'pfind', 18), C('action', 'Action taken', 'text', 30),
        CA('days_ago', 'Days ago', 'int', '{today}-{col:date}', 8), CA('ok_flag', 'Area check', 'text', 'IF({col:finding}=%s,%s,%s)' % (tok('pfind', 'Nothing found'), ca('Clear'), ca('Needs action')), 12)],
      D.pest_d(), 120, [A('ok_flag', '= ' + ca('Needs action'), 'warn'), A('ok_flag', '= ' + ca('Clear'), 'good')]),
    T('team', 'Team', 'Team with tickets handled and hours',
      'The host, the co-host (a helper who handles guests for a fee), four cleaners, two handypeople and four outside contacts; tickets handled, cost and hours this month fill in by themselves.', [
        C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 16), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26), C('hours_week', 'Hours a week', 'int', 10),
        C('hourly_rate', 'Hourly rate', 'money', 10), C('speciality', 'Speciality', 'text', 26), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
        CA('tickets_open', 'Open tickets', 'int', 'COUNTIFS({range:tickets.handyperson},{col:name},{range:tickets.status},"<>"&%s)' % TS('Done'), 9),
        CA('tickets_12m', 'Tickets, 12 months', 'int', 'COUNTIFS({range:tickets.handyperson},{col:name},{range:tickets.reported_on},">"&({today}-365))', 10),
        CA('cost_12m', 'Ticket cost, 12 months', 'money', 'SUMIFS({range:tickets.cost},{range:tickets.handyperson},{col:name},{range:tickets.reported_on},">"&({today}-365))', 12),
        CA('hours_month', 'Hours this month', 'int', 'SUMIFS({range:handy.hours},{range:handy.handyperson},{col:name},{range:handy.week},">"&(%s-7),{range:handy.week},"<="&{today})' % MS, 10)],
      D.team_d(), 50),
]
assert len(tables) == 20, len(tables)
for _t in tables:
    assert len(_t['hint']) <= 200, (_t['key'], len(_t['hint'])); assert len(_t['title']) <= 60 and len(_t['sheet']) <= 31
