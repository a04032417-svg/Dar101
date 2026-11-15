"""Short-term rental host suite - part 2: Bookings, Channels and Payouts."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr2_lists import *
from sr2_tables import settings, tables
from sr2_tools import tools

SUITE = 'fx-20261113-short-term-rental'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
BS = lambda s: tok('bstatus', s)
def F(*pairs): return [FV(a, b) for a, b in pairs]
forms = [
    FORM('booking_entry', 'Booking Entry Sheet', 'Booking with fees, tax and net payout', 'bookings.booking_id', F(
        ('Guest', 'bookings.guest'), ('Guest country', 'bookings.guest_country'), ('Unit', 'bookings.unit'), ('Channel', 'bookings.channel'), ('Check-in', 'bookings.check_in'), ('Check-out', 'bookings.check_out'), ('Nights', 'bookings.nights'),
        ('Guests', 'bookings.guests'), ('Nightly rate', 'bookings.nightly_rate'), ('Room revenue', 'bookings.room_revenue'), ('Cleaning fee', 'bookings.cleaning_fee'), ('Gross', 'bookings.gross'), ('Platform fee', 'bookings.platform_fee'),
        ('Local tax collected', 'bookings.tax_collected'), ('Net payout', 'bookings.net_payout'), ('Net per night', 'bookings.net_per_night'), ('Status', 'bookings.status')) + [
        FF('Bookings of this guest', 'COUNTIFS({range:bookings.guest},INDEX({range:bookings.guest},MATCH({pick},{range:bookings.booking_id},0)))', 'int')]),
    FORM('direct_booking', 'Direct Booking Sheet', 'Direct booking source and lead time', 'sources.source_id', F(
        ('Booking', 'sources.booking_id'), ('Guest', 'sources.guest'), ('Source', 'sources.source'), ('Channel', 'sources.channel'), ('First contact', 'sources.first_contact'), ('Lead time, days', 'sources.lead_days'), ('Lead time bucket', 'sources.lead_bucket'),
        ('Days from first contact to booking', 'sources.days_to_book'), ('Gross', 'sources.gross')) + [
        FF('Bookings from this source', 'COUNTIFS({range:sources.source},INDEX({range:sources.source},MATCH({pick},{range:sources.source_id},0)))', 'int'),
        FF('Average lead time of all sources', 'AVERAGE({range:sources.lead_days})', 'num')]),
    FORM('cancellation', 'Cancellation Sheet', 'Cancellation with kept amount and refund', 'cancellations.cancel_id', F(
        ('Booking', 'cancellations.booking_id'), ('Guest', 'cancellations.guest'), ('Unit', 'cancellations.unit'), ('Channel', 'cancellations.channel'), ('Check-in', 'cancellations.check_in'), ('Cancelled on', 'cancellations.cancelled_on'),
        ('Days before check-in', 'cancellations.days_before'), ('Reason', 'cancellations.reason'), ('Room revenue', 'cancellations.room_revenue'), ('Kept amount', 'cancellations.kept_amount'), ('Refund amount', 'cancellations.refund_amount'),
        ('Kept share', 'cancellations.kept_share'), ('Kept check', 'cancellations.kept_flag')) + [
        FF('Cancellations on this channel', 'COUNTIFS({range:cancellations.channel},INDEX({range:cancellations.channel},MATCH({pick},{range:cancellations.cancel_id},0)))', 'int')]),
    FORM('date_change', 'Date Change Sheet', 'Date change with nights and amount difference', 'changes.change_id', F(
        ('Booking', 'changes.booking_id'), ('Guest', 'changes.guest'), ('Unit', 'changes.unit'), ('Change made on', 'changes.date'), ('Kind of change', 'changes.kind'), ('Old check-in', 'changes.old_check_in'), ('Old check-out', 'changes.old_check_out'),
        ('New check-in', 'changes.new_check_in'), ('New check-out', 'changes.new_check_out'), ('Old nights', 'changes.old_nights'), ('New nights', 'changes.new_nights'), ('Amount change', 'changes.amount_change'), ('Stay check', 'changes.stay_flag')) + [
        FF('Changes on this booking', 'COUNTIFS({range:changes.booking_id},INDEX({range:changes.booking_id},MATCH({pick},{range:changes.change_id},0)))', 'int')]),
    FORM('payout_check', 'Payout Check Sheet', 'Payout with days late and short amount', 'payouts.payout_id', F(
        ('Booking', 'payouts.booking_id'), ('Guest', 'payouts.guest'), ('Unit', 'payouts.unit'), ('Channel', 'payouts.channel'), ('Expected date', 'payouts.expected_date'), ('Expected amount', 'payouts.expected_amount'),
        ('Received amount', 'payouts.received_amount'), ('Status', 'payouts.status'), ('Days late', 'payouts.days_late'), ('Short amount', 'payouts.short_amount'), ('Payout check', 'payouts.chase_flag')) + [
        FF('Payouts to chase now', 'COUNTIFS({range:payouts.chase_flag},%s)' % ca('Chase now'), 'int'), FF('Short amount, all payouts', 'SUM({range:payouts.short_amount})', 'money')]),
    FORM('claim_sheet', 'Missing Payout Claim Sheet', 'Chase of a payout with the answer received', 'chase.chase_id', F(
        ('Payout', 'chase.payout_id'), ('Booking', 'chase.booking_id'), ('Unit', 'chase.unit'), ('Channel', 'chase.channel'), ('Expected amount', 'chase.expected_amount'), ('Chased on', 'chase.chased_on'), ('Answer', 'chase.answer'),
        ('Days open', 'chase.days_open'), ('Chase state', 'chase.chase_state')) + [
        FF('Chases on this payout', 'COUNTIFS({range:chase.payout_id},INDEX({range:chase.payout_id},MATCH({pick},{range:chase.chase_id},0)))', 'int'), FF('Chases still open', 'COUNTIFS({range:chase.chase_state},%s)' % cb('Chase is open'), 'int')]),
    FORM('deposit_sheet', 'Direct Deposit Sheet', 'Deposit and balance of a direct booking', 'deposits.deposit_id', F(
        ('Booking', 'deposits.booking_id'), ('Guest', 'deposits.guest'), ('Unit', 'deposits.unit'), ('Check-in', 'deposits.check_in'), ('Deposit date', 'deposits.date'), ('Method', 'deposits.method'), ('Total amount', 'deposits.total_amount'),
        ('Deposit', 'deposits.amount'), ('Deposit share', 'deposits.deposit_share'), ('Balance', 'deposits.balance'), ('Balance due date', 'deposits.due_date'), ('Days to due date', 'deposits.days_to_due'), ('Balance check', 'deposits.balance_flag')) + [
        FF('Balances overdue', 'COUNTIFS({range:deposits.balance_flag},%s)' % ca('Balance overdue'), 'int')]),
    FORM('note_sheet', 'Booking Note Sheet', 'Note on a booking and who handled it', 'notes.note_id', F(
        ('Booking', 'notes.booking_id'), ('Guest', 'notes.guest'), ('Unit', 'notes.unit'), ('Date', 'notes.date'), ('Kind', 'notes.kind'), ('Note', 'notes.note'), ('Handled by', 'notes.handled_by'), ('Done', 'notes.done'), ('Note check', 'notes.note_flag')) + [
        FF('Notes still open', 'COUNTIFS({range:notes.note_flag},%s)' % cb('Note is open'), 'int')]),
    FORM('longstay_sheet', 'Long Stay Sheet', 'Long stay with the discount given', 'longstays.ls_id', F(
        ('Booking', 'longstays.booking_id'), ('Guest', 'longstays.guest'), ('Unit', 'longstays.unit'), ('Channel', 'longstays.channel'), ('Check-in', 'longstays.check_in'), ('Nights', 'longstays.nights'), ('Plan', 'longstays.plan'),
        ('List rate', 'longstays.list_rate'), ('Discount', 'longstays.discount_pct'), ('Booked rate', 'longstays.nightly_rate'), ('Saving per night', 'longstays.saving_night'), ('Room revenue', 'longstays.room_revenue'),
        ('Discount given', 'longstays.discount_given'), ('Discount check', 'longstays.discount_flag')) + [FF('Discount given on all long stays', 'SUM({range:longstays.discount_given})', 'money')]),
    FORM('checkin_plan', 'Check-in Plan Sheet', 'Check-in with arrival time and days to go', 'calendar.checkin_id', F(
        ('Booking', 'calendar.booking_id'), ('Guest', 'calendar.guest'), ('Unit', 'calendar.unit'), ('Check-in', 'calendar.check_in'), ('Check-out', 'calendar.check_out'), ('Nights', 'calendar.nights'), ('Guests', 'calendar.guests'),
        ('Arrival time', 'calendar.arrival_time'), ('Channel', 'calendar.channel'), ('Status', 'calendar.status'), ('Days to check-in', 'calendar.days_to'), ('Arrival check', 'calendar.arrival'), ('Co-host phone', 'calendar.cohost_phone')) + [
        FF('Check-ins in the next 7 days', 'COUNTIFS({range:calendar.arrival},%s)+COUNTIFS({range:calendar.arrival},%s)' % (ca('Arrives today'), ca('Arrives this week')), 'int')]),
]
documents = [
    DOC('confirmation', 'Booking Confirmation', 'Booking confirmation for a guest', 'bookings.booking_id', [
        'Booking confirmation of {set:company}, dated {today}. Booking {col:bookings.booking_id} for {col:bookings.guest}, {col:bookings.guest_country}.',
        'Unit: {col:bookings.unit}. Check-in {col:bookings.check_in}, check-out {col:bookings.check_out}, {col:bookings.nights} nights for {col:bookings.guests} guests.',
        'Nightly rate {col:bookings.nightly_rate}, room revenue {col:bookings.room_revenue}, cleaning fee {col:bookings.cleaning_fee}. Total {col:bookings.gross}, with local tax of {col:bookings.tax_collected} collected from the guest.',
        'Please tell us your arrival time. Cancellation terms follow the contract terms you were sent. Check your own local rules for registration of guests.'], ['Host', 'Guest'], NOTE),
    DOC('direct_agreement', 'Direct Booking Agreement', 'Direct booking agreement with deposit and balance', 'deposits.deposit_id', [
        'Direct booking agreement of {set:company}, dated {today}, for booking {col:deposits.booking_id}. Guest: {col:deposits.guest}. Unit: {col:deposits.unit}. Check-in: {col:deposits.check_in}.',
        'Total price {col:deposits.total_amount}. Deposit of {col:deposits.amount} paid on {col:deposits.date} by {col:deposits.method}. Balance of {col:deposits.balance} is due on {col:deposits.due_date}.',
        'The dates are held for the guest while the balance is paid on time. Cancellation and refund terms are the contract terms agreed in writing between host and guest.', 'Both sides keep a signed copy of this agreement.'], ['Host', 'Guest'], NOTE),
    DOC('invoice', 'Guest Invoice', 'Guest invoice with a local tax line', 'bookings.booking_id', [
        'Invoice of {set:company}, dated {today}, for booking {col:bookings.booking_id}. Guest: {col:bookings.guest}. Unit: {col:bookings.unit}, stay {col:bookings.check_in} to {col:bookings.check_out}.',
        'Room revenue, {col:bookings.nights} nights at {col:bookings.nightly_rate}: {col:bookings.room_revenue}. Cleaning fee: {col:bookings.cleaning_fee}. Subtotal: {col:bookings.gross}.',
        'Local occupancy tax collected from the guest: {col:bookings.tax_collected}. Collected by: {col:bookings.tax_by}. Check your own local rules on how the tax is shown and paid over.', 'Amounts are in one currency and rates are before tax unless a line says otherwise.'], ['Host'], NOTE),
    DOC('cancel_notice', 'Cancellation Notice', 'Cancellation notice and refund summary', 'cancellations.cancel_id', [
        'Cancellation notice of {set:company}, dated {today}. Booking {col:cancellations.booking_id} for {col:cancellations.guest} at {col:cancellations.unit}, check-in {col:cancellations.check_in}.',
        'The booking was cancelled on {col:cancellations.cancelled_on}, {col:cancellations.days_before} days before check-in. Reason given: {col:cancellations.reason}.',
        'Room revenue of the booking: {col:cancellations.room_revenue}. Amount kept: {col:cancellations.kept_amount}. Refund to the guest: {col:cancellations.refund_amount}.', 'The refund is sent by the route used to pay. Terms follow the cancellation policy in the contract terms.'], ['Host', 'Guest'], NOTE),
    DOC('payout_statement', 'Payout Statement', 'Payout statement for a month and channel', 'channel_months.cm_id', [
        'Payout statement of {set:company}, dated {today}. Month {col:channel_months.month}, channel {col:channel_months.channel}.',
        'Bookings with check-in in the month: {col:channel_months.bookings}, {col:channel_months.nights} nights. Gross: {col:channel_months.gross}. Platform fees: {col:channel_months.platform_fees} ({col:channel_months.fee_share} of gross).',
        'Net after fees: {col:channel_months.net_after_fees}. Local tax collected: {col:channel_months.tax_collected}. Net payouts due to the host: {col:channel_months.net_payouts}. Cancellations in the month: {col:channel_months.cancellations}.', 'Compare this statement with the money received on the Payouts sheet.'], ['Host', 'Accountant'], NOTE),
    DOC('claim_letter', 'Missing Payout Claim Letter', 'Missing payout claim letter to a booking platform', 'payouts.payout_id', [
        'Date: {today}. From {set:company} to the booking platform ({col:payouts.channel}). Subject: payout {col:payouts.payout_id} for booking {col:payouts.booking_id}.',
        'The stay of {col:payouts.guest} at {col:payouts.unit} was due to pay out on {col:payouts.expected_date}. The expected amount is {col:payouts.expected_amount} and the amount received is {col:payouts.received_amount}. The payout is {col:payouts.days_late} days late.',
        'We ask you to send the amount of {col:payouts.short_amount} or to explain the difference in writing. Please reply within the usual answer time of the platform.', 'We keep the booking confirmation and the check-in record as proof.'], ['Host'], NOTE),
    DOC('ledger', 'Monthly Booking Ledger', 'Monthly booking ledger', 'seasons.month', [
        'Monthly booking ledger of {set:company}, dated {today}, for the month starting {col:seasons.month}. Season: {col:seasons.season}, price factor {col:seasons.price_factor}.',
        'Check-ins in the month: {col:seasons.checkins}. Gross of the month: {col:seasons.gross}, rates before any local tax.',
        'Check every booking of the month against the Payouts sheet and the Local Tax Lines sheet before the books are closed.', 'The accountant receives this ledger with the payout statements of each channel.'], ['Host', 'Accountant'], NOTE),
    DOC('checkin_doc', 'Check-in Sheet', 'Check-in sheet for the co-host', 'calendar.checkin_id', [
        'Check-in sheet of {set:company}, dated {today}. Booking {col:calendar.booking_id}, unit {col:calendar.unit}, channel {col:calendar.channel}.',
        'Guest: {col:calendar.guest}, {col:calendar.guests} guests, {col:calendar.nights} nights. Check-in {col:calendar.check_in} around {col:calendar.arrival_time}. Check-out {col:calendar.check_out}.',
        'Arrival check: {col:calendar.arrival}, {col:calendar.days_to} days to check-in. Send the check-in instructions, confirm the arrival time and note any request on the Booking Notes sheet.', 'Co-host phone: {col:calendar.cohost_phone}.'], ['Co-host', 'Host'], NOTE),
    DOC('unit_report', 'Unit Booking Report', 'Booking report for one unit', 'units.unit_id', [
        'Booking report of {set:company}, dated {today}. Unit {col:units.unit_id}: {col:units.name} in {col:units.city}, a {col:units.unit_type} with {col:units.bedrooms} bedrooms. Owner: {col:units.owner}.',
        'Last 60 days: {col:units.bookings_60d} bookings, {col:units.nights_60d} nights, gross {col:units.gross_60d}. Platform fees {col:units.fees_60d} ({col:units.fee_share} of gross). Net payout {col:units.net_60d}.',
        'Direct bookings in the last 60 days: {col:units.direct_60d}. Check-ins in the next 30 days: {col:units.next_30d}. Base rate {col:units.base_rate}, cleaning fee {col:units.cleaning_fee}.', 'The report goes to the owner of the unit with the payout statements.'], ['Host', 'Owner'], NOTE),
    DOC('fee_report', 'Channel Fee Report', 'Channel fee report for one fee', 'fees.fee_id', [
        'Channel fee report of {set:company}, dated {today}. Channel {col:fees.channel}, fee type {col:fees.fee_type}, applies to: {col:fees.applies_to}.',
        'Percent: {col:fees.pct}, in force since {col:fees.from_date}. Gross of the last 12 months on this channel: {col:fees.gross_12m}.',
        'If the fee applied to all that gross it would cost {col:fees.cost_if_all}. Fee check: {col:fees.fee_flag}.', 'Review the fee schedule every quarter and compare it with the fees on the payout statements.'], ['Host'], NOTE),
]
def S(*st): return list(st)
checklists = [
    CHK('new_booking', 'New Booking Steps', 'bookings', 'bookings.booked_on', [('Check the unit is free for the dates', 0), ('Enter the booking with channel, rate and cleaning fee', 0), ('Send the booking confirmation to the guest', 0), ('Tell the co-host about the new booking', 0),
        ('Ask the guest for the arrival time', 2), ('Check the local tax line and who collects it', 2), ('Add a note for any special request', 3), ('Check the booking again 3 days before arrival', 14)]),
    CHK('direct_deposit', 'Direct Booking Deposit Steps', 'deposits', 'deposits.date', [('Agree the price and the dates in writing', 0), ('Send the direct booking agreement', 0), ('Collect the deposit', 1), ('Record the deposit on the Direct Deposits sheet', 1),
        ('Send the balance reminder', 14), ('Collect the balance', 21), ('Send the check-in instructions', 28)]),
    CHK('cancel_run', 'Cancellation Handling Steps', 'cancellations', 'cancellations.cancelled_on', [('Record the date and the reason', 0), ('Free the dates on every channel', 0), ('Work out the kept amount from the policy', 0), ('Send the cancellation notice to the guest', 1),
        ('Send the refund and write the date', 3), ('Tell the co-host and the owner', 1), ('Offer the dates to waiting guests', 2)]),
    CHK('change_run', 'Date Change Steps', 'changes', 'changes.date', [('Check the new dates are free', 0), ('Work out the price difference', 0), ('Confirm the new dates to the guest', 1), ('Update every channel calendar', 1), ('Collect or refund the difference', 3), ('Tell the co-host about the new dates', 1)]),
    CHK('payout_run', 'Payout Check Steps', 'payouts', 'payouts.expected_date', [('Open the platform payout list', 0), ('Match each payout with its booking', 0), ('Check the amount against the net payout', 1), ('Mark received payouts as paid', 1),
        ('Flag short payouts', 2), ('Start the chase of late payouts after the grace days', 4)]),
    CHK('chase_run', 'Late Payout Chase Steps', 'chase', 'chase.chased_on', [('Write the booking, the amount and the days late', 0), ('Send the message to the platform', 0), ('Write the date and the answer in the chase log', 1), ('Chase again after 7 days without an answer', 7),
        ('Send the claim letter with the booking proof', 10), ('Tell the owner if the unit is managed for an owner', 14), ('Close the chase when the money arrives', 21)]),
    CHK('weekly_run', 'Weekly Booking Review Steps', 'calendar', 'calendar.check_in', [('List the check-ins of the next 7 days', -7), ('Confirm arrival times with the guests', -6), ('Check same-day turnovers', -5), ('Check payouts expected this week', -4),
        ('Chase payouts that are late', -3), ('Check direct balances due', -3), ('Review new bookings and cancellations', -1), ('Send the weekly summary to the owners', 0)]),
    CHK('sameday_run', 'Same-Day Turnover Steps', 'sameday', 'sameday.date', [('Check the check-out time and the check-in time', -3), ('Tell the cleaner and the co-host', -3), ('Ask the arriving guest for the arrival time', -2), ('Offer a later check-in if the gap is tight', -2),
        ('Check linen and supplies for the unit', -1), ('Confirm the unit is ready', 0)]),
    CHK('month_close', 'Month-End Booking Close Steps', 'seasons', 'seasons.month', [('List every booking with check-out in the month', 30), ('Match every payout with its booking', 31), ('Chase missing and short payouts', 32), ('Check the local tax lines', 33),
        ('Work out platform fees by channel', 33), ('Send the ledger to the accountant', 34), ('Send statements to owners of managed units', 35)]),
    CHK('fee_run', 'Channel Fee Review Steps', 'fees', 'fees.from_date', [('Read the fee schedule of each channel', 0), ('Compare fees on the payout statements with the schedule', 3), ('Work out fees as a share of gross', 5), ('Compare the direct share with the wanted share', 7),
        ('Decide which bookings to move to direct', 10), ('Write the review date', 12)]),
]
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('g_confirm', 'Guest: your booking is confirmed', 'bookings', 'bookings.guest_phone', 'Hello {guest}, your booking at {unit} is confirmed from {check_in} to {check_out}, {nights} nights. Total {gross}. We look forward to hosting you.'),
    M('g_deposit', 'Guest: your deposit has arrived', 'deposits', 'deposits.guest_phone', 'Hello {guest}, your deposit of {amount} for {unit} has arrived. The balance of {balance} is due on {due_date}.'),
    M('g_balance', 'Guest: the balance is due', 'deposits', 'deposits.guest_phone', 'Hello {guest}, the balance of {balance} for {unit} is due on {due_date}. Please pay it on time to keep your dates.'),
    M('g_cancel', 'Guest: stay cancelled, refund sent', 'cancellations', 'cancellations.guest_phone', 'Hello {guest}, your stay at {unit} from {check_in} is cancelled. Your refund of {refund_amount} is on the way.'),
    M('g_newdates', 'Guest: your new dates are confirmed', 'changes', 'changes.guest_phone', 'Hello {guest}, your new dates at {unit} are confirmed: {new_check_in} to {new_check_out}. The change in price is {amount_change}.'),
    M('g_checkin', 'Guest: your check-in is coming up', 'calendar', 'calendar.guest_phone', 'Hello {guest}, your check-in at {unit} is on {check_in}. We expect you around {arrival_time}. Please reply if that changes.'),
    M('g_arrival', 'Guest: please confirm your arrival time', 'calendar', 'calendar.guest_phone', 'Hello {guest}, please tell us your arrival time for {check_in} at {unit}, {nights} nights for {guests} guests. We will send the check-in instructions.'),
    M('g_hold', 'Guest: we hold your dates', 'deposits', 'deposits.guest_phone', 'Hello {guest}, we hold {unit} for you from {check_in}. The balance of {balance} keeps your dates until {due_date}.'),
    M('g_longstay', 'Guest: a long stay offer for you', 'bookings', 'bookings.guest_phone', 'Hello {guest}, stay 7 nights or more in {unit} and pay {weekly_rate} a night instead of {nightly_rate}. Shall I check your dates?'),
    M('g_tax', 'Guest: local tax is in your invoice', 'bookings', 'bookings.guest_phone', 'Hello {guest}, your invoice for {unit} includes local tax of {tax_collected}. The total of your stay is {gross} before tax.'),
    M('g_invoice', 'Guest: your invoice is attached', 'bookings', 'bookings.guest_phone', 'Hello {guest}, your invoice for booking {booking_id} at {unit} is attached. Gross {gross}, nights {nights}. Thank you for staying with us.'),
    M('g_thanks', 'Guest: thanks, book direct next time', 'guests', 'guests.guest_phone', 'Hello {guest}, thank you for your {stays} stays with us. Book direct next time for a lower price and no platform fee.'),
    M('c_new', 'Co-host: new booking for the unit', 'bookings', 'bookings.cohost_phone', 'Hello, new booking {booking_id} for {unit}: {guest}, {guests} guests, check-in {check_in}, {nights} nights.'),
    M('c_cancel', 'Co-host: a booking was cancelled', 'cancellations', 'cancellations.cohost_phone', 'Hello, booking {booking_id} for {unit} from {check_in} was cancelled. The dates are free again. Please update the calendars.'),
    M('c_changed', 'Co-host: the dates changed', 'changes', 'changes.cohost_phone', 'Hello, the dates of booking {booking_id} at {unit} changed to {new_check_in} to {new_check_out}. Please update the calendar.'),
    M('c_sameday', 'Co-host: same-day turnover', 'sameday', 'sameday.cohost_phone', 'Hello, same-day turnover at {unit} on {date}: check-out {checkout_time}, check-in {checkin_time}, {hours_between} hours between. Arriving guest: {in_guest}.'),
    M('c_late', 'Co-host: a guest arrives late', 'calendar', 'calendar.cohost_phone', 'Hello, {guest} arrives late at {unit} on {check_in}, around {arrival_time}. Please be ready with the check-in instructions.'),
    M('h_missing', 'Host: the payout has not arrived', 'payouts', 'payouts.host_phone', 'Hello, payout {payout_id} for booking {booking_id} ({unit}) of {expected_amount} was due on {expected_date} and has not arrived. Days late: {days_late}.'),
    M('h_short', 'Host: the payout is short', 'payouts', 'payouts.host_phone', 'Hello, payout {payout_id} for booking {booking_id} is short by {short_amount}. Expected {expected_amount}, received {received_amount}.'),
    M('h_expected', 'Host: a payout is expected', 'payouts', 'payouts.host_phone', 'Hello, payout {payout_id} of {expected_amount} for {unit} is expected on {expected_date} from {channel}.'),
    M('h_balance', 'Host: a direct balance is overdue', 'deposits', 'deposits.host_phone', 'Hello, the balance of {balance} for booking {booking_id} ({guest}) was due on {due_date}. Please remind the guest.'),
    M('h_kept', 'Host: the cancellation kept an amount', 'cancellations', 'cancellations.host_phone', 'Hello, the cancellation of booking {booking_id} kept {kept_amount} and refunded {refund_amount}. Reason: {reason}.'),
    M('h_clash', 'Host: check a possible double booking', 'bookings', 'bookings.host_phone', 'Hello, please check {unit}: booking {booking_id} for {guest} starts on {check_in}. Make sure no other stay overlaps these dates.'),
    M('o_new', 'Owner: your unit has a new booking', 'bookings', 'bookings.owner_phone', 'Hello, {unit} has a new booking: {guest}, {check_in} to {check_out}, {nights} nights, gross {gross}.'),
    M('o_cancel', 'Owner: your unit has a cancellation', 'cancellations', 'cancellations.owner_phone', 'Hello, the booking of {guest} at {unit} from {check_in} was cancelled. Amount kept: {kept_amount}, refund: {refund_amount}.'),
    M('o_payout', 'Owner: a payout for your unit is due', 'payouts', 'payouts.owner_phone', 'Hello, a payout of {expected_amount} for {unit} (booking {booking_id}) is expected on {expected_date}. Status: {chase_flag}.'),
    M('a_ledger', 'Accountant: the booking ledger is ready', 'channel_months', 'channel_months.accountant_phone', 'Hello, the booking ledger for {month} on {channel} is ready: gross {gross}, platform fees {platform_fees}, net payouts {net_payouts}.'),
    M('a_tax', 'Accountant: local tax to remit', 'tax_lines', 'tax_lines.accountant_phone', 'Hello, local tax of {tax_collected} on booking {booking_id} (check-in {check_in}) is collected by the host. Amount to remit: {host_remit}.'),
]
assert len(messages) == 28, len(messages)

MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'; YS = 'DATE(YEAR({today}),1,1)'
NC = '{range:bookings.status},"<>"&' + BS('Cancelled')
def CI(a, b): return '{range:bookings.check_in},">="&%s,{range:bookings.check_in},"<"&%s' % (a, b)
CIM = CI(MS, NXT); CIN = '{range:bookings.check_in},">="&{today},{range:bookings.check_in},"<="&({today}+%d)'
CIL = '{range:bookings.check_in},">"&({today}-30),{range:bookings.check_in},"<="&{today}'
def CMW(col): return 'SUMIFS({range:channel_months.%s},{range:channel_months.month},">="&%s,{range:channel_months.month},"<"&%s)' % (col, Y1, MS)
kpis = [
    KPI('Bookings made this month', 'COUNTIFS({range:bookings.booked_on},">="&%s,{range:bookings.booked_on},"<"&%s)' % (MS, NXT), 'int'),
    KPI('Bookings made, last 30 days', 'COUNTIFS({range:bookings.booked_on},">"&({today}-30),{range:bookings.booked_on},"<="&{today})', 'int'),
    KPI('Check-ins this month', 'COUNTIFS(%s,%s)' % (CIM, NC), 'int'),
    KPI('Check-ins next 7 days', 'COUNTIFS(%s,%s)' % (CIN % 7, NC), 'int'),
    KPI('Nights sold this month', 'SUMIFS({range:bookings.nights},%s,%s)' % (CIM, NC), 'int'),
    KPI('Gross revenue this month', 'SUMIFS({range:bookings.gross},%s,%s)' % (CIM, NC), 'money'),
    KPI('Gross revenue, last 30 days', 'SUMIFS({range:bookings.gross},%s,%s)' % (CIL, NC), 'money'),
    KPI('Net payouts received this month', 'SUMIFS({range:payouts.received_amount},{range:payouts.paid_on},">="&%s,{range:payouts.paid_on},"<"&%s)' % (MS, NXT), 'money'),
    KPI('Net payouts received, last 30 days', 'SUMIFS({range:payouts.received_amount},{range:payouts.paid_on},">"&({today}-30),{range:payouts.paid_on},"<="&{today})', 'money'),
    KPI('Payouts expected next 14 days', 'SUMIFS({range:payouts.expected_amount},{range:payouts.expected_date},">="&{today},{range:payouts.expected_date},"<="&({today}+14),{range:payouts.status},%s)' % tok('payst', 'Scheduled'), 'money'),
    KPI('Payouts late over the grace days', 'COUNTIFS({range:payouts.chase_flag},%s)' % ca('Chase now'), 'int'),
    KPI('Value of missing payouts', 'SUMIFS({range:payouts.expected_amount},{range:payouts.status},%s)' % tok('payst', 'Missing'), 'money'),
    KPI('Short-paid payouts this year', 'COUNTIFS({range:payouts.status},%s,{range:payouts.expected_date},">="&%s)' % (tok('payst', 'Short paid'), YS), 'int'),
    KPI('Platform fees this month', 'SUMIFS({range:bookings.platform_fee},%s,%s)' % (CIM, NC), 'money'),
    KPI('Platform fees share of gross, 12 months', 'IFERROR(%s/%s,0)' % (CMW('platform_fees'), CMW('gross')), 'pct'),
    KPI('Direct bookings share this month', 'IFERROR(COUNTIFS(%s,%s,{range:bookings.is_direct},1)/COUNTIFS(%s,%s),0)' % (CIM, NC, CIM, NC), 'pct'),
    KPI('Cancellations this month', 'COUNTIFS({range:cancellations.cancelled_on},">="&%s,{range:cancellations.cancelled_on},"<"&%s)' % (MS, NXT), 'int'),
    KPI('Cancellation rate, last 12 months', 'IFERROR(%s/(%s+%s),0)' % (CMW('cancellations'), CMW('cancellations'), CMW('bookings')), 'pct'),
    KPI('Kept cancellation money this year', 'SUMIFS({range:cancellations.kept_amount},{range:cancellations.cancelled_on},">="&%s)' % YS, 'money'),
    KPI('Average lead time in days', 'IFERROR(AVERAGEIFS({range:bookings.lead_days},%s),0)' % NC, 'int'),
    KPI('Average stay in nights', 'IFERROR(AVERAGEIFS({range:bookings.nights},%s),0)' % NC, 'num'),
    KPI('Average guests per booking', 'IFERROR(AVERAGEIFS({range:bookings.guests},%s),0)' % NC, 'num'),
    KPI('Same-day turnovers next 14 days', 'COUNTIFS({range:sameday.date},">="&{today},{range:sameday.date},"<="&({today}+14))', 'int'),
    KPI('Local tax collected this month', 'SUMIFS({range:tax_lines.tax_collected},{range:tax_lines.check_in},">="&%s,{range:tax_lines.check_in},"<"&%s)' % (MS, NXT), 'money'),
    KPI('Local tax to remit, last 90 days', 'SUMIFS({range:tax_lines.host_remit},{range:tax_lines.check_in},">"&({today}-90),{range:tax_lines.check_in},"<="&{today})', 'money'),
    KPI('Direct balances overdue', 'COUNTIFS({range:deposits.balance_flag},%s)' % ca('Balance overdue'), 'int'),
    KPI('Repeat guests share', 'IFERROR(COUNTIFS({range:guests.guest_flag},%s)/COUNT({range:guests.stays}),0)' % ca('Repeat guest'), 'pct'),
    KPI('Average gross per booking', 'IFERROR(AVERAGEIFS({range:bookings.gross},%s),0)' % NC, 'money'),
    KPI('Bookings on the books, next 30 days', 'COUNTIFS(%s,%s)' % (CIN % 30, NC), 'int'),
]
assert len(kpis) == 29, len(kpis)
dashboard = {"title": "Bookings Dashboard", "kpis": kpis,
    "monthly": {"title": "Gross, platform fees, net payouts and local tax by month", "date": "channel_months.month", "series": [
        {"label": "Gross", "sum": "channel_months.gross", "date": "channel_months.month"}, {"label": "Platform fees", "sum": "channel_months.platform_fees", "date": "channel_months.month"},
        {"label": "Net payouts", "sum": "channel_months.net_payouts", "date": "channel_months.month"}, {"label": "Local tax collected", "sum": "channel_months.tax_collected", "date": "channel_months.month"}]},
    "breakdowns": [{"title": "Gross by channel", "by": "channel_months.channel", "value": "channel_months.gross", "agg": "sum"}, {"title": "Bookings by city", "by": "bookings.city", "value": "bookings.gross", "agg": "count"},
                   {"title": "Payouts by status", "by": "payouts.status", "value": "payouts.expected_amount", "agg": "sum"}, {"title": "Cancellations by reason", "by": "cancellations.reason", "value": "cancellations.kept_amount", "agg": "count"}]}
NCW = ('status', '<>', BS('Cancelled'))
insights = {"filters": [{"label": "Unit", "ref": "units.name"}, {"label": "City", "list": "city"}, {"label": "Channel", "list": "chan"}],
    "gauges": [{"title": "Payouts received on time", "num": AGG('count', 'payouts', where=[('chase_flag', '=', ca('Received on time'))]), "den": AGG('count', 'payouts', where=[('status', '<>', tok('payst', 'Scheduled'))])},
               {"title": "Direct bookings share", "num": AGG('sum', 'channel_months', 'channel_months.bookings', where=[('channel', '=', tok('chan', 'Direct'))]), "den": AGG('sum', 'channel_months', 'channel_months.bookings')},
               {"title": "Cancellations against bookings", "num": AGG('sum', 'channel_months', 'channel_months.cancellations'), "den": AGG('sum', 'channel_months', 'channel_months.bookings')},
               {"title": "Platform fees as share of gross", "num": AGG('sum', 'channel_months', 'channel_months.platform_fees'), "den": AGG('sum', 'channel_months', 'channel_months.gross')},
               {"title": "Repeat guests share", "num": AGG('count', 'guests', where=[('guest_flag', '=', ca('Repeat guest'))]), "den": AGG('count', 'guests')},
               {"title": "Net payouts against gross", "num": AGG('sum', 'channel_months', 'channel_months.net_payouts'), "den": AGG('sum', 'channel_months', 'channel_months.gross')}],
    "charts": [
        CHART('Bookings per month', 'column', 'month', [AGG('sum', 'channel_months', 'channel_months.bookings', date='channel_months.month', label='Bookings')]),
        CHART('Gross revenue per month', 'column', 'month', [AGG('sum', 'channel_months', 'channel_months.gross', date='channel_months.month', label='Gross')]),
        CHART('Net payouts per month', 'column', 'month', [AGG('sum', 'channel_months', 'channel_months.net_payouts', date='channel_months.month', label='Net payouts')]),
        CHART('Platform fees per month', 'column', 'month', [AGG('sum', 'channel_months', 'channel_months.platform_fees', date='channel_months.month', label='Platform fees')]),
        CHART('Bookings by channel', 'bar', 'channel_months.channel', [AGG('sum', 'channel_months', 'channel_months.bookings', label='Bookings')]),
        CHART('Gross by channel', 'bar', 'channel_months.channel', [AGG('sum', 'channel_months', 'channel_months.gross', label='Gross')]),
        CHART('Fee share by channel', 'bar', 'channel_months.channel', [AGG('avg', 'channel_months', 'channel_months.fee_share', label='Fee share of gross')]),
        CHART('Nights sold per month', 'column', 'month', [AGG('sum', 'channel_months', 'channel_months.nights', date='channel_months.month', label='Nights')]),
        CHART('Cancellations per month', 'column', 'month', [AGG('count', 'cancellations', date='cancellations.cancelled_on', label='Cancellations')]),
        CHART('Cancellations by notice given', 'bar', 'cancellations.notice', [AGG('count', 'cancellations', label='Cancellations')]),
        CHART('Payout status', 'bar', 'payouts.status', [AGG('count', 'payouts', label='Payouts')]),
        CHART('Payouts short or missing by channel', 'bar', 'payouts.channel', [AGG('count', 'payouts', where=[('status', '=', tok('payst', 'Short paid'))], label='Short paid'), AGG('count', 'payouts', where=[('status', '=', tok('payst', 'Missing'))], label='Missing')]),
        CHART('Bookings by unit type', 'bar', 'bookings.unit_type', [AGG('count', 'bookings', where=[NCW], label='Bookings')]),
        CHART('Bookings by city', 'bar', 'bookings.city', [AGG('count', 'bookings', where=[NCW], label='Bookings')]),
        CHART('Average stay by channel', 'bar', 'bookings.channel', [AGG('avg', 'bookings', 'bookings.nights', where=[NCW], label='Average nights')]),
        CHART('Average lead time per month', 'line', 'month', [AGG('avg', 'bookings', 'bookings.lead_days', date='bookings.check_in', where=[NCW], label='Average lead time')]),
        CHART('Direct bookings share per month', 'line', 'month', [AGG('avg', 'bookings', 'bookings.is_direct', date='bookings.check_in', where=[NCW], label='Direct share')]),
        CHART('Local tax collected per month', 'column', 'month', [AGG('sum', 'channel_months', 'channel_months.tax_collected', date='channel_months.month', label='Local tax')])]}
signature = [
    {"name": "Booking ledger with fees and payouts by channel", "why": "every stay shows the platform fee, the local tax and the net payout, and the monthly channel table shows what each channel really paid", "where": "Bookings"},
    {"name": "Payout reconciliation with late and short flags", "why": "each payout is checked against its booking: days late, short amount and a chase flag after your grace days", "where": "Payouts"},
    {"name": "Missing payout claim helper", "why": "the amount to claim, the days past the grace days and the value of all missing payouts, ready for the claim letter", "where": "Missing Payout Claim Helper"},
    {"name": "Channel fee comparison", "why": "what the host keeps on each platform and on a direct booking, and the yearly saving of moving bookings to direct", "where": "Channel Fee Comparison"},
    {"name": "Cancellation kept-amount calculator", "why": "days before check-in and the policy give the share refunded, the amount kept and what the host keeps after the fee", "where": "Cancellation Kept Amount"},
    {"name": "Double-booking check", "why": "new dates are searched against every booking of the unit, with the free nights before and after", "where": "Double-Booking Check"},
    {"name": "Payout forecast for 8 weeks", "why": "booked stays are placed in the week of their payout date, so you see the money coming in each week", "where": "Payout Forecast by Week"},
    {"name": "Direct deposit and balance planner", "why": "deposit, balance and the two dates for a direct booking, with the fees saved against a platform", "where": "Direct Deposit Planner"},
    {"name": "Local tax collected and to remit", "why": "tax per booking, who collects it, and the amount the host must pay over, checked against the city percent", "where": "Local Tax Lines"},
    {"name": "Check-in calendar and same-day turnovers", "why": "arrivals today and this week with arrival times, and the days a check-out and a check-in share one date", "where": "Check-in Calendar"}]
competitors = [
    {"what": "free occupancy templates", "lacks": "count nights and revenue but never work out platform fees, local tax or the net payout of a booking"},
    {"what": "subscription property-management software", "lacks": "charge every month and hide the fee rules, so you cannot check a payout line by line or see which payout never arrived"},
    {"what": "single-sheet booking trackers", "lacks": "list bookings and stop there: no payout check, no chase log, no cancellation kept amount and no direct deposit and balance"},
    {"what": "generic expense spreadsheets", "lacks": "record money in and out but cannot match a payout to its booking or tell short from late payouts"},
    {"what": "platform payout reports", "lacks": "show one platform at a time, so you cannot compare fees across channels or see the direct share and what it saves"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: the grace days before a payout is chased, the deposit share of a direct booking, the weekly and monthly discounts and the wanted direct share.',
    'Check Units, Channels, Cities and Team. They hold your units, the platform fees and payout days, the local tax percent of each city and the people the other sheets look up.',
    'Enter every stay on Bookings with its channel, dates, rate, cleaning fee, local tax and status. The platform fee, the net payout, the payout date and the net per night calculate themselves.',
    'Enter each payout on Payouts with the expected date and amount and what arrived. Days late, short amount and the chase flag show which payouts need a message today.',
    'Record each chase on Payout Chase Log with the answer received, and each cancellation on Cancellations with the amount kept and the refund.',
    'Keep Direct Deposits for direct bookings: the deposit, the balance and its due date, with overdue balances flagged red.',
    'Use Check-in Calendar for arrivals and Same-Day Turnovers for days with a check-out and a check-in in one unit. Booking Changes and Booking Notes keep the history of each stay.',
    'Read Channel Months and Fee Schedule to see what each channel costs, and Local Tax Lines for the tax collected and the tax the host must remit. Check your own local rules.',
    f'Use the {len(tools)} calculators for quotes, payout checks, fee comparison, cancellations, double bookings, forecasts, deposits, local tax, long stays and claims.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Bookings Dashboard and Charts every week: bookings, gross, fees, net payouts, cancellations, late payouts and the direct share.']
listing = {"title": "Short-Term Rental Bookings Excel Template: Booking Ledger, Platform Fees, Payout Check, Cancellations, Direct Deposits, Local Tax",
    "headline": "Know what every booking paid, what is late and what never arrived",
    "tags": ["short term rental", "vacation rental", "rental host", "booking tracker", "payout tracker", "excel template", "platform fees", "booking ledger", "cancellation tracker", "direct booking", "local tax tracker", "holiday let", "property host"],
    "description": ("Run the booking and payout side of a short-term or vacation rental business in one Excel workbook. Built for a host or co-host with 3 to 15 furnished units rented by the night through booking platforms and direct bookings. "
        "The Bookings sheet lists every stay with its channel, dates, nights, guests, nightly rate, room revenue, cleaning fee and local tax, and works out the platform fee, the net payout, the payout date and the net value of each night.\n\n"
        "Payouts compares each payout (the money a booking platform sends the host after a stay starts) with its booking and flags the ones that are late, short or missing; Payout Chase Log keeps every message and answer. "
        "Cancellations records the amount kept and the refund, Direct Deposits tracks deposits and balances, and Booking Changes and Booking Notes keep the history of each stay. Channel Months and Fee Schedule show what every channel really costs, and Local Tax Lines separates the tax each platform remits from the tax the host must pay over. "
        "Check-in Calendar and Same-Day Turnovers show arrivals and the days a check-out and a check-in share one date.\n\n"
        f"{len(tools)} calculators cover booking quotes, payout reconciliation, channel fees, cancellation kept amounts, double bookings, occupancy and revenue for a period, an 8-week payout forecast, deposits and balances, local tax, value per night, date changes, long stays, missing payout claims and a direct share grid. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to guests, the co-host (a helper who handles guests for a fee), the host, owners and the accountant.\n\n"
        "This is part two of the Short-Term Rental Host suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data for a small portfolio to explore first. It helps you keep track of bookings and payouts and does not give legal or tax advice."),
    "features": ["Booking ledger with fees, tax and net payout", "Payout check with late and short flags", "Payout chase log and claim letter", "Cancellations with kept amount and refund", "Direct deposits and balances",
                 "Channel fee comparison and fee schedule", "Local tax collected and to remit", "Check-in calendar and same-day turnovers", f"{len(tools)} calculators for quotes, payouts and fees", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p2', slug='short-term-rental-bookings', profession='Short-Term Rental Host', name='Bookings, Channels and Payouts',
         tagline='Know what every booking paid, what is late and what never arrived', price_usd=29,
         colors={"primary": "#264653", "accent": "#E9C46A"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 2, "of": 8, "focus": "Bookings, channels and payouts"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sr2.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
