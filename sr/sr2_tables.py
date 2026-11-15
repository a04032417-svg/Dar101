"""Short-term rental host suite part 2: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr2_lists import *
import sr2_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def HOST(): return CA('host_phone', 'Host phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def COH(): return CA('cohost_phone', 'Co-host phone', 'text', '"%s"' % D.COHOST_PHONE, 18)
def OWNP(my='unit'): return CA('owner_phone', 'Owner phone', 'text', LKT('units.owner_phone', 'units.name', my), 18)
BS = lambda s: tok('bstatus', s)
PS = lambda s: tok('payst', s)
YES = tok('yn', 'Yes'); DIRECT = tok('chan', 'Direct'); HOSTTAX = tok('taxby', 'Host')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('payout_grace_days', 'Days after the expected date before a payout is chased', 'int', 3), S('warn_days', 'Days ahead to warn of a check-in, a balance or a payout', 'int', 7),
    S('deposit_pct', 'Share of a direct booking paid as a deposit', 'pct', 0.30), S('balance_days', 'Days before check-in that a direct balance is due', 'int', 7),
    S('weekly_discount', 'Usual discount for a stay of 7 nights or more', 'pct', 0.08), S('monthly_discount', 'Usual discount for a stay of 28 nights or more', 'pct', 0.15),
    S('cleaning_cost', 'Usual cost of one turnover', 'money', 40), S('short_tolerance', 'Difference allowed before a payout counts as short', 'money', 1),
    S('target_direct_share', 'Wanted share of direct bookings', 'pct', 0.25), S('max_cancel_rate', 'Highest cancellation rate you accept', 'pct', 0.08),
]
assert 3 <= len(settings) <= 20

tables = [
    T('bookings', 'Bookings', 'Booking ledger with fees and net payout',
      'One row per booking: unit, channel, guest, dates, nightly rate, revenue, cleaning fee and local tax; the platform fee, the net payout and the value of a night after fees fill in by themselves.', [
        C('booking_id', 'Booking ID', 'text', 10, required=True), C('unit_id', 'Unit ID', 'text', 9), REF('unit', 'Unit', 'units.name', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), LST('channel', 'Channel', 'chan', 11),
        C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18), C('guest_country', 'Guest country', 'text', 16), C('guests', 'Guests', 'int', 8), C('check_in', 'Check-in', 'date', 11), C('check_out', 'Check-out', 'date', 11),
        C('booked_on', 'Booked on', 'date', 11), C('nights', 'Nights', 'int', 8), C('nightly_rate', 'Nightly rate', 'money', 11), C('room_revenue', 'Room revenue', 'money', 12), C('cleaning_fee', 'Cleaning fee', 'money', 11),
        C('gross', 'Gross', 'money', 11), C('earned', 'Earned amount', 'money', 12), C('tax_collected', 'Local tax collected', 'money', 12), LST('tax_by', 'Tax collected by', 'taxby', 11), LST('status', 'Status', 'bstatus', 11),
        CA('lead_days', 'Lead time, days', 'int', '{col:check_in}-{col:booked_on}', 10), CA('fee_pct', 'Channel fee', 'pct', LKN('channels.fee_pct', 'channels.channel', 'channel'), 9),
        CA('platform_fee', 'Platform fee', 'money', 'ROUND({col:earned}*{col:fee_pct},2)', 11), CA('host_tax', 'Tax the host remits', 'money', 'IF({col:tax_by}=%s,{col:tax_collected},0)' % HOSTTAX, 11),
        CA('net_payout', 'Net payout', 'money', '{col:earned}-{col:platform_fee}+{col:host_tax}', 11), CA('net_per_night', 'Net per night', 'money', 'IF({col:nights}>0,({col:net_payout}-{col:host_tax})/{col:nights},0)', 11),
        CA('payout_date', 'Payout date', 'date', '{col:check_in}+'+LKN('channels.payout_days', 'channels.channel', 'channel'), 11), CA('is_direct', 'Direct', 'int', 'IF({col:channel}=%s,1,0)' % DIRECT, 8), CA('route', 'Route', 'text', 'IF({col:channel}=%s,%s,%s)' % (DIRECT, cb('Direct booking'), cb('Platform booking')), 15),
        CA('weekly_rate', 'Weekly stay rate', 'money', 'ROUND({col:nightly_rate}*(1-{set:weekly_discount}),0)', 11), OWNP(), COH(), HOST()],
      D.bookings_d(), 700, [A('status', '= ' + BS('Cancelled'), 'bad'), A('fee_pct', '> 0.14', 'warn'), A('is_direct', '= 1', 'good')]),
    T('payouts', 'Payouts', 'Payouts with days late, short amount and chase flag',
      'One row per payout (the money a booking platform sends the host after a stay starts): expected and received amounts and dates; the days late, the short amount and the chase flag fill in by themselves.', [
        C('payout_id', 'Payout ID', 'text', 10, required=True), C('booking_id', 'Booking ID', 'text', 10), LST('channel', 'Channel', 'chan', 11), REF('unit', 'Unit', 'units.name', 26), C('expected_date', 'Expected date', 'date', 11), C('paid_on', 'Paid on', 'date', 11),
        C('expected_amount', 'Expected amount', 'money', 12), C('received_amount', 'Received amount', 'money', 12), LST('status', 'Status', 'payst', 11),
        CA('guest', 'Guest', 'text', LKT('bookings.guest', 'bookings.booking_id', 'booking_id'), 24),
        CA('days_late', 'Days late', 'int', 'IF({col:paid_on}=0,MAX(0,{today}-{col:expected_date}),MAX(0,{col:paid_on}-{col:expected_date}))', 9),
        CA('short_amount', 'Short amount', 'money', 'IF({col:status}=%s,0,MAX(0,{col:expected_amount}-{col:received_amount}))' % PS('Scheduled'), 11),
        CA('chase_flag', 'Payout check', 'text', 'IF({col:status}=%s,IF({col:days_late}<={set:payout_grace_days},%s,%s),IF({col:status}=%s,%s,IF({col:status}=%s,IF({col:days_late}>{set:payout_grace_days},%s,%s),IF({today}>{col:expected_date}+{set:payout_grace_days},%s,IF({col:expected_date}<={today}+{set:warn_days},%s,%s)))))'
           % (PS('Paid'), ca('Received on time'), ca('Received late'), PS('Short paid'), ca('Received short'), PS('Missing'), ca('Chase now'), ca('Due soon'), ca('Chase now'), ca('Due soon'), ca('Payout scheduled')), 16),
        OWNP(), HOST()],
      D.payouts_d(), 700, [A('chase_flag', '= ' + ca('Chase now'), 'bad'), A('chase_flag', '= ' + ca('Received short'), 'warn'), A('chase_flag', '= ' + ca('Received late'), 'warn'), A('chase_flag', '= ' + ca('Received on time'), 'good')]),
    T('cancellations', 'Cancellations', 'Cancellations with kept and refunded amounts',
      'One row per cancelled booking: when it was cancelled, why, the room revenue, the amount kept and the refund; the notice given, the kept share and the check fill in by themselves.', [
        C('cancel_id', 'Cancel ID', 'text', 9, required=True), C('booking_id', 'Booking ID', 'text', 10), C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18), REF('unit', 'Unit', 'units.name', 26), LST('channel', 'Channel', 'chan', 11),
        C('check_in', 'Check-in', 'date', 11), C('cancelled_on', 'Cancelled on', 'date', 12), C('room_revenue', 'Room revenue', 'money', 12), C('kept_amount', 'Kept amount', 'money', 11), C('refund_amount', 'Refund amount', 'money', 11),
        LST('reason', 'Reason', 'creason', 18), LST('notice', 'Notice given', 'band', 16),
        CA('days_before', 'Days before check-in', 'int', '{col:check_in}-{col:cancelled_on}', 10), CA('kept_share', 'Kept share', 'pct', 'IF({col:kept_amount}+{col:refund_amount}>0,{col:kept_amount}/({col:kept_amount}+{col:refund_amount}),0)', 9),
        CA('kept_flag', 'Kept check', 'text', 'IF({col:kept_share}>=0.5,%s,IF({col:kept_share}>0,%s,%s))' % (ca('Kept most of it'), ca('Kept part'), ca('Kept nothing')), 14), OWNP(), COH(), HOST()],
      D.cancellations_d(), 200, [A('kept_flag', '= ' + ca('Kept nothing'), 'warn'), A('kept_flag', '= ' + ca('Kept most of it'), 'good')]),
    T('channels', 'Channels', 'Channels with platform fee and payout days',
      'Booking platforms and direct routes with the fee and the days to the payout (negative means before check-in); the booking, fee and quote sheets read these.', [
        C('channel', 'Channel', 'text', 24, required=True), C('fee_pct', 'Platform fee', 'pct', 11), C('payout_days', 'Payout days after check-in', 'int', 13)],
      D.channels_d(), 50),
    T('channel_months', 'Channel Months', 'Bookings, fees and net payouts by month and channel',
      'One row per month and channel from every booking: bookings, nights, gross, platform fees, local tax and net payouts; the net after fees, the fee share and the average stay fill in by themselves.', [
        C('cm_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('channel', 'Channel', 'chan', 11), C('bookings', 'Bookings', 'int', 9), C('nights', 'Nights', 'int', 9), C('gross', 'Gross', 'money', 12),
        C('platform_fees', 'Platform fees', 'money', 12), C('tax_collected', 'Local tax collected', 'money', 12), C('net_payouts', 'Net payouts', 'money', 12), C('cancellations', 'Cancellations', 'int', 11),
        CA('net_after_fees', 'Net after fees', 'money', '{col:gross}-{col:platform_fees}', 12), CA('fee_share', 'Fee share of gross', 'pct', 'IF({col:gross}>0,{col:platform_fees}/{col:gross},0)', 10),
        CA('avg_stay', 'Average stay', 'num', 'IF({col:bookings}>0,{col:nights}/{col:bookings},0)', 9), CA('avg_gross', 'Gross per booking', 'money', 'IF({col:bookings}>0,{col:gross}/{col:bookings},0)', 11),
        CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCT_PHONE, 18)],
      D.channel_months_d(), 200, [A('fee_share', '> 0.14', 'warn')]),
    T('units', 'Units', 'Units with bookings and fees of the last 60 days',
      'One row per unit with type, city, owner, base rate and cleaning fee; bookings, nights, gross, platform fees and net payout of the last 60 days fill in by themselves.', [
        C('unit_id', 'Unit ID', 'text', 9, required=True), C('name', 'Name', 'text', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), C('bedrooms', 'Bedrooms', 'int', 9), C('owner', 'Owner', 'text', 22),
        C('owner_phone', 'Owner phone', 'text', 18), C('base_rate', 'Base rate', 'money', 11), C('cleaning_fee', 'Cleaning fee', 'money', 11),
        CA('bookings_60d', 'Bookings, 60 days', 'int', 'COUNTIFS({range:bookings.unit},{col:name},{range:bookings.check_in},">"&({today}-60),{range:bookings.check_in},"<="&{today},{range:bookings.status},"<>"&%s)' % BS('Cancelled'), 10),
        CA('nights_60d', 'Nights, 60 days', 'int', 'SUMIFS({range:bookings.nights},{range:bookings.unit},{col:name},{range:bookings.check_in},">"&({today}-60),{range:bookings.check_in},"<="&{today},{range:bookings.status},"<>"&%s)' % BS('Cancelled'), 10),
        CA('gross_60d', 'Gross, 60 days', 'money', 'SUMIFS({range:bookings.gross},{range:bookings.unit},{col:name},{range:bookings.check_in},">"&({today}-60),{range:bookings.check_in},"<="&{today},{range:bookings.status},"<>"&%s)' % BS('Cancelled'), 12),
        CA('fees_60d', 'Platform fees, 60 days', 'money', 'SUMIFS({range:bookings.platform_fee},{range:bookings.unit},{col:name},{range:bookings.check_in},">"&({today}-60),{range:bookings.check_in},"<="&{today},{range:bookings.status},"<>"&%s)' % BS('Cancelled'), 12),
        CA('net_60d', 'Net payout, 60 days', 'money', 'SUMIFS({range:bookings.net_payout},{range:bookings.unit},{col:name},{range:bookings.check_in},">"&({today}-60),{range:bookings.check_in},"<="&{today},{range:bookings.status},"<>"&%s)' % BS('Cancelled'), 12),
        CA('fee_share', 'Fee share of gross', 'pct', 'IF({col:gross_60d}>0,{col:fees_60d}/{col:gross_60d},0)', 10),
        CA('direct_60d', 'Direct bookings, 60 days', 'int', 'COUNTIFS({range:bookings.unit},{col:name},{range:bookings.check_in},">"&({today}-60),{range:bookings.check_in},"<="&{today},{range:bookings.channel},%s,{range:bookings.status},"<>"&%s)' % (DIRECT, BS('Cancelled')), 11),
        CA('next_30d', 'Check-ins, next 30 days', 'int', 'COUNTIFS({range:bookings.unit},{col:name},{range:bookings.check_in},">="&{today},{range:bookings.check_in},"<="&({today}+30),{range:bookings.status},"<>"&%s)' % BS('Cancelled'), 11), COH(), HOST()],
      D.units_d(), 50, [A('fee_share', '> 0.14', 'warn'), A('next_30d', '= 0', 'warn')]),
    T('cities', 'Cities', 'Local occupancy tax by city and who collects it',
      'One row per city and collector: the local occupancy tax (a tax on each night, collected from the guest) as a share of room revenue; check your own local rules for who must pay it over.', [
        LST('city', 'City', 'city', 10, required=True), LST('collected_by', 'Collected by', 'taxby', 12), C('tax_pct', 'Local tax share', 'pct', 11)],
      D.cities_d(), 50),
    T('guests', 'Guests', 'Guests with stays, spend and last stay',
      'One row per guest: country, usual channel, stays, nights, spend and dates; whether the guest is a repeat guest, the spend per stay and the days since the last stay fill in by themselves.', [
        C('guest_id', 'Guest ID', 'text', 9, required=True), C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18), C('guest_country', 'Country', 'text', 16), LST('channel', 'Usual channel', 'chan', 11),
        C('stays', 'Stays', 'int', 8), C('nights', 'Nights', 'int', 8), C('spend', 'Spend', 'money', 11), C('first_stay', 'First stay', 'date', 11), C('last_stay', 'Last stay', 'date', 11),
        CA('guest_flag', 'Guest type', 'text', 'IF({col:stays}>=2,%s,%s)' % (ca('Repeat guest'), ca('First stay')), 13), CA('spend_per_stay', 'Spend per stay', 'money', 'IF({col:stays}>0,{col:spend}/{col:stays},0)', 11),
        CA('days_since', 'Days since last stay', 'int', '{today}-{col:last_stay}', 10), CA('activity', 'Activity', 'text', 'IF({col:days_since}<=180,%s,%s)' % (ca('Recent guest'), ca('Lapsed guest')), 13), HOST()],
      D.guests_d(), 400, [A('guest_flag', '= ' + ca('Repeat guest'), 'good'), A('activity', '= ' + ca('Lapsed guest'), 'warn')]),
    T('calendar', 'Check-in Calendar', 'Check-in calendar with arrival check',
      'One row per upcoming or recent stay: unit, guest, guests, nights, arrival time and channel; the days to check-in and the arrival check (today, this week, under way, ended) fill in by themselves.', [
        C('checkin_id', 'Check-in ID', 'text', 10, required=True), C('booking_id', 'Booking ID', 'text', 10), C('check_in', 'Check-in', 'date', 11), C('check_out', 'Check-out', 'date', 11), REF('unit', 'Unit', 'units.name', 26),
        C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18), C('guests', 'Guests', 'int', 8), C('nights', 'Nights', 'int', 8), C('arrival_time', 'Arrival time', 'text', 9), LST('channel', 'Channel', 'chan', 11), LST('status', 'Status', 'bstatus', 11),
        CA('days_to', 'Days to check-in', 'int', '{col:check_in}-{today}', 10),
        CA('arrival', 'Arrival check', 'text', 'IF({col:check_out}<{today},%s,IF({col:check_in}<{today},%s,IF({col:check_in}={today},%s,IF({col:check_in}<={today}+{set:warn_days},%s,%s))))' % (ca('Stay ended'), ca('Stay under way'), ca('Arrives today'), ca('Arrives this week'), ca('Arrives later')), 14),
        COH(), HOST()],
      D.calendar_d(), 300, [A('arrival', '= ' + ca('Arrives today'), 'warn'), A('arrival', '= ' + ca('Arrives this week'), 'good')]),
    T('chase', 'Payout Chase Log', 'Payout chase log with days open',
      'One row per chase of a payout that was late, short or unclear: date, channel and the answer received; the amount, the days the chase has been open and the open or closed check fill in by themselves.', [
        C('chase_id', 'Chase ID', 'text', 9, required=True), C('payout_id', 'Payout ID', 'text', 10), C('booking_id', 'Booking ID', 'text', 10), LST('channel', 'Channel', 'chan', 11), C('chased_on', 'Chased on', 'date', 11),
        LST('answer', 'Answer', 'canswer', 22), C('resolved_on', 'Resolved on', 'date', 11),
        CA('expected_amount', 'Expected amount', 'money', LKN('payouts.expected_amount', 'payouts.payout_id', 'payout_id'), 12), CA('unit', 'Unit', 'text', LKT('payouts.unit', 'payouts.payout_id', 'payout_id'), 26),
        CA('days_open', 'Days open', 'int', 'IF({col:resolved_on}=0,{today}-{col:chased_on},{col:resolved_on}-{col:chased_on})', 9),
        CA('chase_state', 'Chase state', 'text', 'IF({col:resolved_on}=0,%s,%s)' % (cb('Chase is open'), cb('Chase is closed')), 13), HOST()],
      D.chase_d(), 200, [A('chase_state', '= ' + cb('Chase is open'), 'bad'), A('days_open', '> 10', 'warn')]),
    T('deposits', 'Direct Deposits', 'Direct deposits with balance and due date',
      'One row per direct booking: the deposit paid, the method and the date the balance is due; the balance, the days to the due date and the check (paid, due soon, overdue) fill in by themselves.', [
        C('deposit_id', 'Deposit ID', 'text', 10, required=True), C('booking_id', 'Booking ID', 'text', 10), C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18), REF('unit', 'Unit', 'units.name', 26), C('check_in', 'Check-in', 'date', 11),
        C('date', 'Deposit date', 'date', 11), C('total_amount', 'Total amount', 'money', 12), C('amount', 'Deposit', 'money', 11), C('method', 'Method', 'text', 14), C('due_date', 'Balance due date', 'date', 12), C('balance_paid_on', 'Balance paid on', 'date', 12),
        CA('balance', 'Balance', 'money', '{col:total_amount}-{col:amount}', 11), CA('days_to_due', 'Days to due date', 'int', '{col:due_date}-{today}', 10),
        CA('balance_flag', 'Balance check', 'text', 'IF({col:balance_paid_on}>0,%s,IF({col:due_date}<{today},%s,IF({col:due_date}<={today}+{set:warn_days},%s,%s)))' % (ca('Balance paid'), ca('Balance overdue'), ca('Balance due soon'), ca('Balance later')), 14),
        CA('deposit_share', 'Deposit share', 'pct', 'IF({col:total_amount}>0,{col:amount}/{col:total_amount},0)', 9), HOST()],
      D.deposits_d(), 200, [A('balance_flag', '= ' + ca('Balance overdue'), 'bad'), A('balance_flag', '= ' + ca('Balance due soon'), 'warn'), A('balance_flag', '= ' + ca('Balance paid'), 'good')]),
    T('sources', 'Booking Sources', 'Booking sources with lead time bucket',
      'One row per booking: where the guest came from, the first contact and the lead time; the lead time bucket, the days from first contact to booking and the gross fill in by themselves.', [
        C('source_id', 'Source ID', 'text', 9, required=True), C('booking_id', 'Booking ID', 'text', 10), LST('source', 'Source', 'bsrc', 18), LST('channel', 'Channel', 'chan', 11), C('lead_days', 'Lead time, days', 'int', 10), C('first_contact', 'First contact', 'date', 11),
        CA('lead_bucket', 'Lead time bucket', 'text', 'IF({col:lead_days}<=6,%s,IF({col:lead_days}<=14,%s,IF({col:lead_days}<=28,%s,IF({col:lead_days}<=90,%s,%s))))' % tuple(tok('band', b) for b in D.BAND), 18),
        CA('days_to_book', 'Days from first contact to booking', 'int', 'IFERROR(INDEX({range:bookings.booked_on},MATCH({col:booking_id},{range:bookings.booking_id},0))-{col:first_contact},0)', 12),
        CA('gross', 'Gross', 'money', LKN('bookings.gross', 'bookings.booking_id', 'booking_id'), 11), CA('guest', 'Guest', 'text', LKT('bookings.guest', 'bookings.booking_id', 'booking_id'), 24)],
      D.sources_d(), 200),
    T('fees', 'Fee Schedule', 'Fee schedule by channel',
      'One row per channel and kind of fee: the percent, what it applies to and the date it started; the cost if it applied to all gross of the last 12 months and the fee check fill in by themselves.', [
        C('fee_id', 'Fee ID', 'text', 8, required=True), LST('channel', 'Channel', 'chan', 11), C('fee_type', 'Fee type', 'text', 20), C('pct', 'Percent', 'pct', 9), C('applies_to', 'Applies to', 'text', 28), C('from_date', 'From date', 'date', 11),
        CA('gross_12m', 'Gross, 12 months', 'money', 'SUMIFS({range:channel_months.gross},{range:channel_months.channel},{col:channel},{range:channel_months.month},">="&%s,{range:channel_months.month},"<"&%s)' % (Y1, MS), 13),
        CA('cost_if_all', 'Cost if applied to all gross', 'money', '{col:gross_12m}*{col:pct}', 13), CA('fee_flag', 'Fee check', 'text', 'IF({col:pct}>0.10,%s,%s)' % (cb('Fee above 10 percent'), cb('Fee up to 10 percent')), 18)],
      D.fees_d(), 60, [A('fee_flag', '= ' + cb('Fee above 10 percent'), 'warn')]),
    T('tax_lines', 'Local Tax Lines', 'Local tax lines with check and amount to remit',
      'One row per booking with local occupancy tax (a tax on each night, collected from the guest): percent, amount and who collects; the expected tax, the check and the tax to remit fill in by themselves.', [
        C('tax_id', 'Tax ID', 'text', 9, required=True), C('booking_id', 'Booking ID', 'text', 10), LST('city', 'City', 'city', 10), LST('channel', 'Channel', 'chan', 11), C('check_in', 'Check-in', 'date', 11), C('room_revenue', 'Room revenue', 'money', 12),
        C('tax_pct', 'Tax percent', 'pct', 9), C('tax_collected', 'Tax collected', 'money', 11), LST('collected_by', 'Collected by', 'taxby', 11),
        CA('expected_tax', 'Expected tax', 'money', 'ROUND({col:room_revenue}*{col:tax_pct},2)', 11), CA('tax_check', 'Tax check', 'text', 'IF(ABS({col:tax_collected}-{col:expected_tax})<=0.05,%s,%s)' % (ca('Tax matches'), ca('Tax differs')), 13),
        CA('host_remit', 'Tax the host remits', 'money', 'IF({col:collected_by}=%s,{col:tax_collected},0)' % HOSTTAX, 11), CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCT_PHONE, 18), HOST()],
      D.tax_lines_d(), 400, [A('tax_check', '= ' + ca('Tax differs'), 'warn')]),
    T('changes', 'Booking Changes', 'Booking changes with the nights and amount difference',
      'One row per change of a booking: old and new dates, the kind of change and the amount difference; the old and new nights, the change in nights and the stay check fill in by themselves.', [
        C('change_id', 'Change ID', 'text', 9, required=True), C('booking_id', 'Booking ID', 'text', 10), C('guest', 'Guest', 'text', 24), C('date', 'Date', 'date', 11), LST('kind', 'Change', 'chkind', 18), C('old_check_in', 'Old check-in', 'date', 11),
        C('old_check_out', 'Old check-out', 'date', 11), C('new_check_in', 'New check-in', 'date', 11), C('new_check_out', 'New check-out', 'date', 11), C('amount_change', 'Amount change', 'money', 11),
        CA('old_nights', 'Old nights', 'int', '{col:old_check_out}-{col:old_check_in}', 9), CA('new_nights', 'New nights', 'int', '{col:new_check_out}-{col:new_check_in}', 9), CA('nights_change', 'Change in nights', 'int', '{col:new_nights}-{col:old_nights}', 10),
        CA('stay_flag', 'Stay check', 'text', 'IF({col:nights_change}>0,%s,IF({col:nights_change}<0,%s,%s))' % (cb('Stay longer'), cb('Stay shorter'), cb('Same length')), 12),
        CA('unit', 'Unit', 'text', LKT('bookings.unit', 'bookings.booking_id', 'booking_id'), 26), CA('guest_phone', 'Guest phone', 'text', LKT('bookings.guest_phone', 'bookings.booking_id', 'booking_id'), 18), COH()],
      D.changes_d(), 200, [A('amount_change', '< 0', 'warn'), A('amount_change', '> 100', 'good')]),
    T('sameday', 'Same-Day Turnovers', 'Same-day turnovers with hours between stays',
      'One row per day a unit has a check-out and a check-in (a turnover is the clean and reset between two stays): the times and hours between them; days to the date and the tight or roomy check fill in.', [
        C('sd_id', 'Row ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('out_booking', 'Check-out booking', 'text', 11), C('in_booking', 'Check-in booking', 'text', 11), C('in_guest', 'Arriving guest', 'text', 24),
        C('checkout_time', 'Check-out time', 'text', 9), C('checkin_time', 'Check-in time', 'text', 9), C('hours_between', 'Hours between', 'num', 9),
        CA('days_to', 'Days to the date', 'int', '{col:date}-{today}', 9), CA('turn_flag', 'Turnover check', 'text', 'IF({col:hours_between}<=3,%s,IF({col:hours_between}>=5,%s,%s))' % (ca('Tight turnover'), ca('Roomy turnover'), ca('Normal turnover')), 14), COH(), HOST()],
      D.sameday_d(), 200, [A('turn_flag', '= ' + ca('Tight turnover'), 'bad'), A('turn_flag', '= ' + ca('Roomy turnover'), 'good')]),
    T('longstays', 'Long Stays', 'Long stays with the discount given',
      'One row per stay of 7 nights or more: the list rate, the discount and the booked rate; the discount given in money, the saving per night and the discount check fill in by themselves.', [
        C('ls_id', 'Row ID', 'text', 8, required=True), C('booking_id', 'Booking ID', 'text', 10), C('guest', 'Guest', 'text', 24), REF('unit', 'Unit', 'units.name', 26), LST('channel', 'Channel', 'chan', 11), C('check_in', 'Check-in', 'date', 11),
        C('nights', 'Nights', 'int', 8), C('plan', 'Plan', 'text', 14), C('list_rate', 'List rate', 'money', 10), C('discount_pct', 'Discount', 'pct', 9), C('nightly_rate', 'Booked rate', 'money', 10), C('room_revenue', 'Room revenue', 'money', 12),
        CA('saving_night', 'Saving per night', 'money', '{col:list_rate}-{col:nightly_rate}', 10), CA('discount_given', 'Discount given', 'money', '({col:list_rate}-{col:nightly_rate})*{col:nights}', 11),
        CA('discount_flag', 'Discount check', 'text', 'IF({col:discount_pct}<{set:weekly_discount}-0.02,%s,IF({col:discount_pct}>{set:monthly_discount},%s,%s))' % (cb('Discount low'), cb('Discount high'), cb('Discount on target')), 14),
        CA('guest_phone', 'Guest phone', 'text', LKT('bookings.guest_phone', 'bookings.booking_id', 'booking_id'), 18)],
      D.longstays_d(), 100, [A('discount_flag', '= ' + cb('Discount high'), 'warn')]),
    T('notes', 'Booking Notes', 'Booking notes with kind and who handled them',
      'One row per note on a booking: the kind, the text, who handled it and whether it is done; the guest, the unit and the open or closed check fill in by themselves.', [
        C('note_id', 'Note ID', 'text', 8, required=True), C('booking_id', 'Booking ID', 'text', 10), C('date', 'Date', 'date', 11), LST('kind', 'Kind', 'nkind', 15), C('note', 'Note', 'text', 40), REF('handled_by', 'Handled by', 'team.name', 22), LST('done', 'Done', 'yn', 8),
        CA('guest', 'Guest', 'text', LKT('bookings.guest', 'bookings.booking_id', 'booking_id'), 24), CA('unit', 'Unit', 'text', LKT('bookings.unit', 'bookings.booking_id', 'booking_id'), 26),
        CA('note_flag', 'Note check', 'text', 'IF({col:done}=%s,%s,%s)' % (YES, cb('Note is closed'), cb('Note is open')), 12), CA('handler_phone', 'Handler phone', 'text', LKT('team.phone', 'team.name', 'handled_by'), 18), HOST()],
      D.notes_d(), 200, [A('note_flag', '= ' + cb('Note is open'), 'warn')]),
    T('seasons', 'Seasons', 'Seasons with the price factor and bookings of each month',
      'Twelve calendar months with the season and the price factor against the base rate; the check-ins of the month and their gross fill in by themselves.', [
        C('month', 'Month', 'date', 11, required=True), C('season', 'Season', 'text', 11), C('price_factor', 'Price factor', 'num', 10),
        CA('checkins', 'Check-ins in the month', 'int', 'COUNTIFS({range:bookings.check_in},">="&{col:month},{range:bookings.check_in},"<"&DATE(YEAR({col:month}),MONTH({col:month})+1,1),{range:bookings.status},"<>"&%s)' % BS('Cancelled'), 11),
        CA('gross', 'Gross of the month', 'money', 'SUMIFS({range:bookings.gross},{range:bookings.check_in},">="&{col:month},{range:bookings.check_in},"<"&DATE(YEAR({col:month}),MONTH({col:month})+1,1),{range:bookings.status},"<>"&%s)' % BS('Cancelled'), 12)],
      D.seasons_d(), 50),
    T('team', 'Team', 'Team with the notes each person handles',
      'The host, the co-host (a helper who handles guests for a fee), four cleaners, two handypeople and four outside contacts; the booking notes each person handles fill in by themselves.', [
        C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 14), LST('team', 'Team', 'team', 12), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
        C('hours_week', 'Hours a week', 'int', 10), C('hourly_rate', 'Hourly rate', 'money', 10), C('speciality', 'Speciality', 'text', 26), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
        CA('notes_handled', 'Booking notes handled', 'int', 'COUNTIFS({range:notes.handled_by},{col:name})', 11), CA('notes_open', 'Notes still open', 'int', 'COUNTIFS({range:notes.handled_by},{col:name},{range:notes.done},%s)' % tok('yn', 'No'), 11)],
      D.team_d(), 50),
]
assert len(tables) == 20, len(tables)


for _t in tables: assert len(_t['hint']) <= 200, (_t['key'], len(_t['hint']))
