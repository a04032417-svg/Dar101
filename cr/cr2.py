"""Car Rental Business suite - part 2: Booking Calendar and Availability."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr2_lists import *
from cr2_tables import settings, tables, R, B, BL, VH, CVD, CCD, CAN, NOS, SOLD, CH, MS, HOLDC, HOLDA, PKT, RTT
from cr2_tools import tools
import cr2_data as D

NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES = '{list:yesno.yes}'
from cr_core import SUITE, OWNER, MANAGER, first_name
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def LB(c): return LK('bookings', 'booking_id', c)

# ------------------------------------------------------------------ forms (12)
def BOOK_FIELDS(): return F(('Renter', 'bookings.renter'), ('Renter phone', 'bookings.phone'), ('Vehicle', 'bookings.vehicle'), ('Class', 'bookings.class'), ('Channel', 'bookings.channel'), ('Plan', 'bookings.plan'),
                            ('Season', 'bookings.season'), ('Start date', 'bookings.start_date'), ('Pickup time', 'bookings.pickup_time'), ('End date', 'bookings.end_date'), ('Return time', 'bookings.return_time'),
                            ('Pickup location', 'bookings.pickup_location'), ('Days', 'bookings.days'), ('Total', 'bookings.total'), ('Status', 'bookings.status'))
forms = [
    FORM('booking_sheet', 'Booking Sheet', 'Booking with dates, car and amounts', 'bookings.booking_id', BOOK_FIELDS() + [
        FF('Included miles for the rental', '%s*{set:miles_day}' % LB('days'), 'int'), FF('Net amount after the channel fee', LB('net_amount'), 'money'), FF('Turnaround verdict', LB('turn'), 'text')]),
    FORM('change_sheet', 'Booking Change Sheet', 'Change of dates or car on a booking', 'bookings.booking_id', F(
        ('Renter', 'bookings.renter'), ('Vehicle', 'bookings.vehicle'), ('Class', 'bookings.class'), ('Start date now', 'bookings.start_date'), ('End date now', 'bookings.end_date'), ('Days now', 'bookings.days'), ('Total now', 'bookings.total'), ('Channel', 'bookings.channel')) + [
        FF('Day rate booked', 'ROUND(%s/%s,2)' % (LB('total'), LB('days')), 'money'), FF('Amount for one more day', 'ROUND(%s/%s,2)' % (LB('total'), LB('days')), 'money'),
        FF('Net rate per day', LB('net_per_day'), 'money'), FF('Turnaround buffer of the class, minutes', LB('buffer_min'), 'int'), FF('Turnaround verdict', LB('turn'), 'text')]),
    FORM('extension_sheet', 'Extension Request Sheet', 'Request to keep a car longer', 'extensions.ext_id', F(
        ('Booking', 'extensions.booking_id'), ('Renter', 'extensions.renter'), ('Vehicle', 'extensions.vehicle'), ('Class', 'extensions.class'), ('Requested on', 'extensions.requested_on'), ('Current end date', 'extensions.current_end'),
        ('Requested end date', 'extensions.requested_end'), ('Extra days', 'extensions.extra_days'), ('Day rate booked', 'extensions.day_rate'), ('Extra amount', 'extensions.extra_amount'), ('Free cars of the class', 'extensions.free_alt'),
        ('Verdict', 'extensions.verdict'), ('Decision', 'extensions.decision')) + [FF('Extra amount a week at this rate', 'ROUND(7*%s,2)' % LK('extensions', 'ext_id', 'day_rate'), 'money')]),
    FORM('swap_sheet', 'Vehicle Swap Sheet', 'Swap of the car during a rental', 'swaps.swap_id', F(
        ('Booking', 'swaps.booking_id'), ('Renter', 'swaps.renter'), ('From vehicle', 'swaps.from_vehicle'), ('To vehicle', 'swaps.to_vehicle'), ('From class', 'swaps.from_class'), ('To class', 'swaps.to_class'), ('Same class', 'swaps.same_class'),
        ('Swap date', 'swaps.swap_date'), ('Rental ends', 'swaps.end_date'), ('Days left', 'swaps.days_left'), ('Day rate booked', 'swaps.old_rate'), ('New day rate', 'swaps.new_rate'), ('Miles allowance from the swap', 'swaps.miles_allowance'),
        ('Change in the rental amount', 'swaps.rate_change'), ('Reason', 'swaps.reason')) + [FF('Amount still to run at new rate', 'ROUND(%s*%s,2)' % (LK('swaps', 'swap_id', 'new_rate'), LK('swaps', 'swap_id', 'days_left')), 'money')]),
    FORM('cancel_sheet', 'Cancellation Sheet', 'Cancellation with notice and fee', 'cancellations.booking_id', F(
        ('Renter', 'cancellations.renter'), ('Vehicle', 'cancellations.vehicle'), ('Class', 'cancellations.class'), ('Channel', 'cancellations.channel'), ('Start date', 'cancellations.start_date'), ('Cancelled on', 'cancellations.cancelled_on'),
        ('Notice days', 'cancellations.notice_days'), ('Notice check', 'cancellations.notice_check'), ('Booking total', 'cancellations.total'), ('Fee charged', 'cancellations.fee_charged'), ('Revenue lost', 'cancellations.revenue_lost')) + [
        FF('Days of notice for a free cancellation', '{set:free_cancel_days}', 'int'), FF('Late cancellation fee in your terms', '{set:cancel_fee}', 'money')]),
    FORM('noshow_sheet', 'No-show Sheet', 'Renter who did not collect the car', 'cancellations.booking_id', F(
        ('Renter', 'cancellations.renter'), ('Renter phone', 'cancellations.phone'), ('Vehicle', 'cancellations.vehicle'), ('Class', 'cancellations.class'), ('Start date', 'cancellations.start_date'), ('Kind', 'cancellations.kind'),
        ('Booking total', 'cancellations.total'), ('Fee charged', 'cancellations.fee_charged'), ('Revenue lost', 'cancellations.revenue_lost')) + [
        FF('Share of the booking lost', 'IFERROR(%s/%s,0)' % (LK('cancellations', 'booking_id', 'revenue_lost'), LK('cancellations', 'booking_id', 'total')), 'pct'), FF('Cancellations and no-shows you accept', '{set:cancel_limit}', 'pct')]),
    FORM('pickup_sheet', 'Pickup Schedule Sheet', 'Pickup with car, time and location', 'pickups_returns.slot_id', F(
        ('Date', 'pickups_returns.date'), ('Pickup or return', 'pickups_returns.kind'), ('Booking', 'pickups_returns.booking_id'), ('Vehicle', 'pickups_returns.vehicle'), ('Class', 'pickups_returns.class'), ('Renter', 'pickups_returns.renter'),
        ('Renter phone', 'pickups_returns.phone'), ('Location', 'pickups_returns.location'), ('Time', 'pickups_returns.time'), ('Car ready on time', 'pickups_returns.ready')) + [
        FF('Pickups and returns in the same hour', LK('pickups_returns', 'slot_id', 'hour_load'), 'int'), FF('Handled by one person in an hour', '{set:hour_capacity}', 'int')]),
    FORM('return_sheet', 'Return Schedule Sheet', 'Return with car, time and location', 'pickups_returns.slot_id', F(
        ('Date', 'pickups_returns.date'), ('Booking', 'pickups_returns.booking_id'), ('Vehicle', 'pickups_returns.vehicle'), ('Renter', 'pickups_returns.renter'), ('Renter phone', 'pickups_returns.phone'), ('Location', 'pickups_returns.location'),
        ('Time', 'pickups_returns.time'), ('Knock-on of a late return', 'pickups_returns.knock_on')) + [
        FF('Grace minutes before a late fee', '{set:late_grace_min}', 'int'), FF('Late fee for each started hour', '{set:late_fee_hour}', 'money'), FF('Hour of the return', LK('pickups_returns', 'slot_id', 'hour'), 'int')]),
    FORM('block_sheet', 'Service Block Sheet', 'Service or repair block on the calendar', 'service_blocks.block_id', F(
        ('Vehicle', 'service_blocks.vehicle'), ('Class', 'service_blocks.class'), ('Service kind', 'service_blocks.kind'), ('Start date', 'service_blocks.date'), ('Days off road', 'service_blocks.days_off_road'), ('End date', 'service_blocks.end_date')) + [
        FF('Cars of the class in the fleet', 'COUNTIFS({range:vehicles.class},%s,{range:vehicles.status},"<>"&%s)' % (LK('service_blocks', 'block_id', 'class'), SOLD), 'int'),
        FF('Bookings of the car in those days', 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s%s)' % (B('vehicle'), LK('service_blocks', 'block_id', 'vehicle'), B('start_date'), LK('service_blocks', 'block_id', 'end_date'), B('end_date'), LK('service_blocks', 'block_id', 'date'), HOLDC), 'int')]),
    FORM('mkt_block_sheet', 'Marketplace Block Dates Sheet', 'Dates to block on a marketplace listing', 'service_blocks.block_id', F(
        ('Vehicle', 'service_blocks.vehicle'), ('Class', 'service_blocks.class'), ('First date to block', 'service_blocks.date'), ('Last date to block', 'service_blocks.end_date'), ('Reason', 'service_blocks.kind')) + [
        FF('Days to block', LK('service_blocks', 'block_id', 'days_off_road'), 'int'), FF('Days until the block starts', '%s-{today}' % LK('service_blocks', 'block_id', 'date'), 'int'),
        FF('Marketplace fee share, A', 'INDEX({range:channels.fee_pct},MATCH(%s,{range:channels.channel},0))' % CH['Marketplace A'], 'pct'), FF('Marketplace fee share, B', 'INDEX({range:channels.fee_pct},MATCH(%s,{range:channels.channel},0))' % CH['Marketplace B'], 'pct')]),
    FORM('corporate_sheet', 'Corporate Booking Sheet', 'Booking for a corporate account', 'bookings.booking_id', F(
        ('Renter', 'bookings.renter'), ('Channel', 'bookings.channel'), ('Vehicle', 'bookings.vehicle'), ('Class', 'bookings.class'), ('Plan', 'bookings.plan'), ('Start date', 'bookings.start_date'), ('End date', 'bookings.end_date'),
        ('Days', 'bookings.days'), ('Total', 'bookings.total'), ('Status', 'bookings.status')) + [
        FF('Day rate invoiced', 'ROUND(%s/%s,2)' % (LB('total'), LB('days')), 'money'), FF('Included miles for the rental', '%s*{set:miles_day}' % LB('days'), 'int'), FF('Net rate per day', LB('net_per_day'), 'money')]),
    FORM('hotel_sheet', 'Hotel Partner Booking Sheet', 'Booking of a hotel guest through the partner', 'bookings.booking_id', F(
        ('Guest', 'bookings.renter'), ('Channel', 'bookings.channel'), ('Vehicle', 'bookings.vehicle'), ('Class', 'bookings.class'), ('Pickup location', 'bookings.pickup_location'), ('Start date', 'bookings.start_date'), ('Pickup time', 'bookings.pickup_time'),
        ('End date', 'bookings.end_date'), ('Days', 'bookings.days'), ('Total', 'bookings.total')) + [
        FF('Partner fee share in your terms', 'INDEX({range:channels.fee_pct},MATCH(%s,{range:channels.channel},0))' % CH['Hotel partner'], 'pct'),
        FF('Partner fee at that share', 'ROUND(%s*INDEX({range:channels.fee_pct},MATCH(%s,{range:channels.channel},0)),2)' % (LB('total'), CH['Hotel partner']), 'money'),
        FF('Net amount after the partner fee', 'ROUND(%s*(1-INDEX({range:channels.fee_pct},MATCH(%s,{range:channels.channel},0))),2)' % (LB('total'), CH['Hotel partner']), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
def BD(*c): return ' '.join('{col:bookings.%s}' % x for x in c)
documents = [
    DOC('confirm_doc', 'Booking Confirmation', 'Booking confirmation', 'bookings.booking_id', [
        'Booking confirmation of {set:company}, dated {today}. Booking {col:bookings.booking_id} for {col:bookings.renter}.',
        'Vehicle class: {col:bookings.class}. Plan: {col:bookings.plan}. Pickup on {col:bookings.start_date} at {col:bookings.pickup_time}, location {col:bookings.pickup_location}. Return on {col:bookings.end_date} at {col:bookings.return_time}.',
        'Rental days: {col:bookings.days}. Included miles a day: {set:miles_day} (miles are the demo unit). Total: {col:bookings.total}, before any sales tax.',
        'Please bring what your hire terms ask for. Check your local rules for what a renter must show at pickup.'], ['Manager', 'Renter'], NOTE),
    DOC('agreement_doc', 'Rental Agreement Summary', 'Rental agreement summary', 'bookings.booking_id', [
        'Rental summary of {set:company}, dated {today}. Booking {col:bookings.booking_id}, renter {col:bookings.renter}.',
        'Vehicle class: {col:bookings.class}. From {col:bookings.start_date} to {col:bookings.end_date}, {col:bookings.days} days. Price: {col:bookings.total}. Included miles a day: {set:miles_day}.',
        'Extra miles, late returns, cleaning and refuelling are charged as set in your hire terms. A late return is charged after {set:late_grace_min} minutes of grace at {set:late_fee_hour} for each started hour.',
        'This summary does not replace your hire terms. Check your local rules and your insurance terms.'], ['Manager', 'Renter'], NOTE),
    DOC('pickup_doc', 'Pickup Instructions', 'Pickup instructions', 'bookings.booking_id', [
        'Pickup instructions of {set:company}, dated {today}. Booking {col:bookings.booking_id} for {col:bookings.renter}.',
        'Pickup on {col:bookings.start_date} at {col:bookings.pickup_time}, location: {col:bookings.pickup_location}. Class: {col:bookings.class}.',
        'Please arrive on time and bring the documents your hire terms ask for. We check the car with you and note the odometer and the fuel or charge level.',
        'If you will be late, call us so that we can keep the car for you.'], ['Manager', 'Renter'], NOTE),
    DOC('return_doc', 'Return Instructions', 'Return instructions', 'bookings.booking_id', [
        'Return instructions of {set:company}, dated {today}. Booking {col:bookings.booking_id} for {col:bookings.renter}.',
        'Return on {col:bookings.end_date} at {col:bookings.return_time}. Vehicle: {col:bookings.vehicle}.',
        'Please bring the car back with the fuel or charge level agreed at pickup. After {set:late_grace_min} minutes a late return is charged at {set:late_fee_hour} for each started hour.',
        'The next renter may be waiting: please keep to the time. Call us if anything changes.'], ['Manager', 'Renter'], NOTE),
    DOC('extension_doc', 'Extension Confirmation', 'Extension confirmation', 'extensions.ext_id', [
        'Extension of {set:company}, dated {today}. Request {col:extensions.ext_id} for booking {col:extensions.booking_id}, renter {col:extensions.renter}.',
        'Vehicle: {col:extensions.vehicle}. The rental now ends on {col:extensions.requested_end} instead of {col:extensions.current_end}: {col:extensions.extra_days} extra days at {col:extensions.day_rate} a day, extra amount {col:extensions.extra_amount}.',
        'Decision: {col:extensions.decision}. Calendar check: {col:extensions.verdict}.',
        'The extension follows your hire terms. Please call us before the new end date if you need more time.'], ['Manager', 'Renter'], NOTE),
    DOC('swap_doc', 'Vehicle Swap Notice', 'Vehicle swap notice', 'swaps.swap_id', [
        'Swap notice of {set:company}, dated {today}. Booking {col:swaps.booking_id}, renter {col:swaps.renter}.',
        'On {col:swaps.swap_date} your car {col:swaps.from_vehicle} is replaced by {col:swaps.to_vehicle}. Reason: {col:swaps.reason}.',
        'Your day rate is {col:swaps.new_rate} for the {col:swaps.days_left} days left. Your included miles from the swap day: {col:swaps.miles_allowance} (miles are the demo unit).',
        'Please move your belongings and hand over the first car as we agreed. Check your insurance terms for the new car.'], ['Manager', 'Renter'], NOTE),
    DOC('cancel_doc', 'Cancellation Confirmation', 'Cancellation confirmation', 'cancellations.booking_id', [
        'Cancellation of {set:company}, dated {today}. Booking {col:cancellations.booking_id} for {col:cancellations.renter}.',
        'The booking for {col:cancellations.start_date} was cancelled on {col:cancellations.cancelled_on}, {col:cancellations.notice_days} days before the start. Notice check: {col:cancellations.notice_check}.',
        'Booking total: {col:cancellations.total}. Fee kept as set in your terms: {col:cancellations.fee_charged}. Free cancellation needs {set:free_cancel_days} days of notice.',
        'Check your local rules and your hire terms about cancellation fees and refunds.'], ['Manager', 'Renter'], NOTE),
    DOC('avail_doc', 'Weekly Availability by Class', 'Weekly availability sheet by class', 'next_free_class.class', [
        'Availability sheet of {set:company}, dated {today}. Class: {col:next_free_class.class}.',
        'First day in the next 14 days with a free car: {col:next_free_class.first_free}. Free cars that day: {col:next_free_class.free_cars}.',
        'Use the Calendar by Class and Day sheet for every day, and the Next Free Date and Class Finder for a request with dates.',
        'Keep {set:margin_cars} car back for late returns before you sell the last car of a class.'], ['Manager'], NOTE),
    DOC('tomorrow_doc', "Tomorrow's Pickups and Returns", "Tomorrow's pickups and returns sheet", 'daily_fleet.date', [
        'Daily sheet of {set:company} for {col:daily_fleet.date}.',
        'Pickups: {col:daily_fleet.pickups}. Returns: {col:daily_fleet.returns}. Cars in the fleet: {col:daily_fleet.fleet}. Cars rented: {col:daily_fleet.rented}. Cars in service: {col:daily_fleet.service}. Cars free: {col:daily_fleet.free}.',
        'Fleet utilisation of the day: {col:daily_fleet.utilisation} (rented days as a share of available days).',
        'One staff member handles about {set:hour_capacity} pickups and returns in an hour: plan the counter and the delivery runs from the Pickups and Returns sheet.'], ['Manager', 'Booking assistant'], NOTE),
    DOC('calendar_doc', 'Booking Calendar Print', 'Booking calendar print, next 14 days', 'cal_class.row_id', [
        'Booking calendar of {set:company}, dated {today}. Class: {col:cal_class.class}, day {col:cal_class.date}.',
        'Cars in the fleet: {col:cal_class.vehicles}. Booked: {col:cal_class.booked}. In service: {col:cal_class.service}. Free: {col:cal_class.free}. Free share: {col:cal_class.free_share}.',
        'Print the Calendar by Vehicle and Day sheet for the car by car view of the same 14 days.',
        'Rented and reserved days come from Bookings; service days come from Service Blocks.'], ['Manager'], NOTE),
    DOC('corp_doc', 'Corporate Monthly Booking List', 'Corporate monthly booking list', 'channel_month.row_id', [
        'Monthly booking list of {set:company}, dated {today}. Channel: {col:channel_month.channel}. Month: {col:channel_month.month}.',
        'Bookings started: {col:channel_month.bookings}. Rented days: {col:channel_month.rented_days}. Amount: {col:channel_month.revenue}, before any sales tax.',
        'Your own account terms apply to the invoice. Questions about a booking are welcome.',
        'Check your local rules and your hire terms for what an invoice must show.'], ['Manager', 'Account contact'], NOTE),
    DOC('hotel_doc', 'Hotel Partner Booking List', 'Hotel partner booking list', 'channel_month.row_id', [
        'Booking list of {set:company}, dated {today}. Channel: {col:channel_month.channel}. Month: {col:channel_month.month}.',
        'Bookings started: {col:channel_month.bookings}. Rented days: {col:channel_month.rented_days}. Revenue: {col:channel_month.revenue}. Partner fee: {col:channel_month.fee}. Net: {col:channel_month.net}.',
        'The partner fee is the share the partner keeps, as agreed in your partner terms.',
        'Please check the list and tell us of any difference.'], ['Manager', 'Partner contact'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_booking_chk', 'New Booking Entry', 'bookings', 'bookings.start_date', [('Check the class and dates in the Next Free Date and Class Finder', -7), ('Run the Double-Booking Guard', -7), ('Enter the booking with times and location', -7), ('Check the channel and the total', -7), ('Send the booking confirmation', -6), ('Block the dates on the marketplace listings', -6), ('Send the pickup reminder', -1), ('Check the car is ready', 0)]),
    CHK('daily_chk', 'Daily Pickups and Returns Check', 'pickups_returns', 'pickups_returns.date', [('Open Pickups and Returns for the day', -1), ('Check the cars are clean and ready', -1), ('Check late returns and the knock-on', 0), ('Plan the counter and the drivers', 0), ('Send the pickup and return reminders', 0), ('Note returns that ran late', 1)]),
    CHK('weekly_chk', 'Weekly Calendar Review', 'weekend', 'weekend.week', [('Open the Daily Fleet Status', 0), ('Check the idle gaps of the next 14 days', 0), ('Fill or price the gaps', 1), ('Check the service blocks', 1), ('Run the Weekend Shortage and Surplus tool', 2), ('Update the marketplace listings', 2)]),
    CHK('overlap_chk', 'Double-Booking Check', 'bookings', 'bookings.start_date', [('Open the Overlap Check sheet', -7), ('Check every verdict that is not clear', -7), ('Call the renter of the later booking', -6), ('Move or cancel the later booking', -5), ('Block the marketplace dates again', -5), ('Check the sheet is clear', -4)]),
    CHK('extension_chk', 'Extension Handling', 'extensions', 'extensions.requested_on', [('Write the request in Extension Requests', 0), ('Run the Extension Checker', 0), ('Offer the swap if the car is booked', 0), ('Confirm the new end date and amount', 1), ('Update the booking and the marketplace dates', 1), ('Tell the cleaner and the driver', 1)]),
    CHK('swap_chk', 'Mid-Rental Swap', 'swaps', 'swaps.swap_date', [('Run the Mid-Rental Swap Tool', -2), ('Agree the swap date with the renter', -2), ('Write the swap in Vehicle Swaps', -1), ('Send the swap notice', -1), ('Record the odometer and level of both cars', 0), ('Put the first car on the service list', 0)]),
    CHK('cancel_chk', 'Cancellation Handling', 'cancellations', 'cancellations.cancelled_on', [('Write the cancellation with the date', 0), ('Check the notice days and the fee', 0), ('Send the cancellation confirmation', 0), ('Open the dates on the calendar and on the listings', 0), ('Tell the marketplace if it came from one', 1), ('Offer the car to a waiting request', 1)]),
    CHK('noshow_chk', 'No-show Handling', 'cancellations', 'cancellations.cancelled_on', [('Wait for the time you set in your terms', 0), ('Call the renter', 0), ('Write the no-show in the sheet', 0), ('Charge the fee in your terms', 1), ('Release the car and the dates', 1), ('Tell the marketplace if it came from one', 1)]),
    CHK('mkt_cal_chk', 'Marketplace Calendar Update', 'service_blocks', 'service_blocks.date', [('Run the Marketplace Block List', -3), ('Block the service dates on each listing', -3), ('Block the direct booking dates', -3), ('Check the listing the day before', -1), ('Open the dates when the service ends', 0)]),
    CHK('weekend_chk', 'Weekend Preparation', 'weekend', 'weekend.week', [('Run the Weekend Shortage and Surplus tool', 0), ('Close or promote the listings', 1), ('Check the cars for Saturday pickups', 3), ('Check the counter staff for the weekend', 3), ('Print the pickups and returns of the weekend', 4)]),
    CHK('month_chk', 'Month-End Booking Check', 'channel_month', 'channel_month.month', [('Check every booking of the month has a status', 28), ('Check cancellations and no-shows', 28), ('Check the revenue by channel', 29), ('Send the monthly lists to corporate and hotel partners', 30), ('Send the totals to the bookkeeper', 31)]),
    CHK('one_car_chk', 'One-Car Host Calendar', 'bookings', 'bookings.start_date', [('Check the car is free for the dates', -5), ('Write the booking', -5), ('Block the dates on your listing', -5), ('Plan the cleaning between rentals', -1), ('Hand over the car', 0), ('Check the car on return and open the dates', 0)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
OWN = first_name(OWNER); MGR = first_name(MANAGER); DRV = 'Jun'; DET = 'Lucia'; MEC = 'Diego'; BKP = 'Elsa'
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('r_confirm', 'Renter: your booking is confirmed', 'bookings', 'bookings.phone', 'Hello {renter}, your booking {booking_id} is confirmed from {start_date} to {end_date}. Pickup at {pickup_time}. {center}'),
    M('r_pickup', 'Renter: pickup tomorrow', 'pickups_returns', 'pickups_returns.pickup_phone', 'Hello {renter}, your pickup is tomorrow at {time}, {location}. Booking {booking_id}. {center}'),
    M('r_return', 'Renter: please return the car', 'pickups_returns', 'pickups_returns.return_phone', 'Hello {renter}, please return the car by {time} on {date}. {center}'),
    M('r_ext_ok', 'Renter: your extension is confirmed', 'extensions', 'extensions.ok_phone', 'Hello {renter}, your extension to {requested_end} is confirmed, extra {extra_amount}. {center}'),
    M('r_ext_no', 'Renter: we cannot extend', 'extensions', 'extensions.no_phone', 'Hello {renter}, we cannot extend past {current_end}, the car is booked. {center}'),
    M('r_ext_alt', 'Renter: we offer another car to extend', 'extensions', 'extensions.alt_phone', 'Hello {renter}, we offer {vehicle_alt} to extend your rental to {requested_end}. {center}'),
    M('r_swap', 'Renter: we need to swap your car', 'swaps', 'swaps.swap_phone', 'Hello {renter}, we need to swap your car for {to_vehicle} on {swap_date}. Rate from then: {new_rate} a day. {center}'),
    M('r_cancel', 'Renter: your cancellation is confirmed', 'cancellations', 'cancellations.cancel_phone', 'Hello {renter}, your cancellation of {booking_id} is confirmed, fee {fee_charged}. {center}'),
    M('r_noshow', 'Renter: we missed you at pickup', 'cancellations', 'cancellations.noshow_phone', 'Hello {renter}, we missed you at pickup on {start_date}. Please call us. {center}'),
    M('r_late', 'Renter: late return knock-on', 'pickups_returns', 'pickups_returns.late_phone', 'Hello {renter}, a late return of {late_minutes} minutes affects the next renter of the car. Please bring it back as soon as you can. {center}'),
    M('r_moved', 'Renter: your pickup time moved', 'bookings', 'bookings.phone', 'Hello {renter}, your pickup for {booking_id} moved to {pickup_time} on {start_date}. {center}'),
    M('r_delivery', 'Renter: your delivery is booked', 'bookings', 'bookings.deliv_phone', 'Hello {renter}, your delivery to {pickup_location} is booked for {start_date} at {pickup_time}. {center}'),
    M('r_pay', 'Renter: booking waits for payment', 'bookings', 'bookings.pay_phone', 'Hello {renter}, booking {booking_id} for {start_date} is waiting for payment of {total}. {center}'),
    M('r_rebook', 'Renter: thank you, rebook and save', 'bookings', 'bookings.rebook_phone', 'Hello {renter}, thank you for renting with us. Book again and save {saving}. {center}'),
    M('c_list', 'Corporate account: your booking list', 'channel_month', 'channel_month.corp_phone', 'Hello, your booking list for {month}: {bookings} bookings, {rented_days} rented days, {revenue}. {center}'),
    M('c_ready', 'Corporate account: the car is ready', 'bookings', 'bookings.corp_phone', 'Hello, the car for {renter} is ready on {start_date} at {pickup_time}. Booking {booking_id}. {center}'),
    M('h_conf', 'Hotel partner: guest booking confirmed', 'bookings', 'bookings.hotel_phone', "Hello, your guest's booking {booking_id} for {renter} is confirmed from {start_date} to {end_date}. {center}"),
    M('h_list', 'Hotel partner: the monthly booking list', 'channel_month', 'channel_month.hotel_phone', 'Hello, the booking list for {month}: {bookings} bookings, revenue {revenue}, partner fee {fee}. {center}'),
    M('m_block', 'Marketplace support: block the car', 'service_blocks', 'service_blocks.mkt_phone', 'Hello, please block {vehicle} from {date} to {end_date}. {center}'),
    M('m_cancel', 'Marketplace support: the guest cancelled', 'cancellations', 'cancellations.mkt_phone', 'Hello, the guest on {booking_id} cancelled. Please release {vehicle} from {start_date}. {center}'),
    M('o_overlap', 'Owner: bookings overlap', 'overlap_check', 'overlap_check.owner_phone', 'Hello %s, %s' % (OWN, '{overlap_count} bookings overlap now: {booking_id} and {clash_with} on {vehicle} from {start_date}. {center}')),
    M('o_weekend', 'Owner: a class has no free car', 'cal_class', 'cal_class.owner_phone', 'Hello %s, %s' % (OWN, 'the class {class} has no free car on {date}. Check the listings. {center}')),
    M('o_free', 'Owner: cars free on a day', 'daily_fleet', 'daily_fleet.owner_phone', 'Hello %s, %s' % (OWN, '{free} cars are free on {date}, utilisation {utilisation}. {center}')),
    M('o_fee', 'Owner: what the marketplace fee costs', 'channel_month', 'channel_month.owner_phone', 'Hello %s, %s' % (OWN, '{channel} fees took {fee_per_day} a rented day in {month}. The net rate was {net_per_day} a day. {center}')),
    M('g_overlap', 'Manager: check the overlap', 'overlap_check', 'overlap_check.mgr_phone', 'Hello %s, %s' % (MGR, 'please check the overlap on {vehicle} for {start_date}. Booking {booking_id}. {center}')),
    M('g_tomorrow', 'Manager: tomorrow pickups and returns', 'daily_fleet', 'daily_fleet.mgr_phone', 'Hello %s, %s' % (MGR, 'tomorrow has {pickups} pickups and {returns} returns. {free} cars are free. {center}')),
    M('g_block', 'Manager: block a car for service', 'service_blocks', 'service_blocks.mgr_phone', 'Hello %s, %s' % (MGR, 'please block {vehicle} for service from {date}, {days_off_road} days off the road. {center}')),
    M('g_swap', 'Manager: confirm the swap', 'swaps', 'swaps.mgr_phone', 'Hello %s, %s' % (MGR, 'please confirm the swap on {booking_id} to {to_vehicle} on {swap_date}. {center}')),
    M('d_delivery', 'Driver: delivery', 'pickups_returns', 'pickups_returns.delivery_phone', 'Hello %s, %s' % (DRV, 'delivery to {location} at {time} for {booking_id}. {center}')),
    M('d_collect', 'Driver: collection', 'pickups_returns', 'pickups_returns.collect_phone', 'Hello %s, %s' % (DRV, 'collection from {location} at {time} for {booking_id}. {center}')),
    M('t_return', 'Detailer: a car returns', 'pickups_returns', 'pickups_returns.detailer_phone', 'Hello %s, %s' % (DET, '{vehicle} returns at {time}, next pickup {next_start}. {center}')),
    M('t_rush', 'Detailer: rush clean', 'pickups_returns', 'pickups_returns.rush_phone', 'Hello %s, %s' % (DET, 'the car {vehicle} for {date} needs a rush clean before {time}. {center}')),
    M('w_slot', 'Mechanic: next free slot', 'next_free_veh', 'next_free_veh.mech_phone', 'Hello %s, %s' % (MEC, 'the next free slot for {vehicle} is {first_free}. {center}')),
    M('b_month', 'Bookkeeper: bookings by channel', 'channel_month', 'channel_month.bookkeeper_phone', 'Hello %s, %s' % (BKP, '{channel} for {month}: {bookings} bookings, revenue {revenue}, fee {fee}, net {net}. {center}')),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
W90 = '%s,">="&({today}-90),%s,"<="&{today}' % (B('start_date'), B('start_date'))
W30 = '%s,">="&({today}-30),%s,"<="&{today}' % (B('start_date'), B('start_date'))
DF = lambda c: R('daily_fleet', c)
EXT = lambda c: R('extensions', c)
def CNT(w, extra=''): return 'COUNTIFS(%s%s%s)' % (w, HOLDC, extra)
kpis = [
    KPI('Bookings starting this month', 'COUNTIFS(%s,">="&%s,%s,"<"&EDATE(%s,1)%s)' % (B('start_date'), MS, B('start_date'), MS, HOLDC), 'int'),
    KPI('Bookings starting in the next 7 days', 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+6)%s)' % (B('start_date'), B('start_date'), HOLDC), 'int'),
    KPI('Pickups tomorrow', 'COUNTIFS(%s,{today}+1%s)' % (B('start_date'), HOLDC), 'int'),
    KPI('Returns tomorrow', 'COUNTIFS(%s,{today}+1%s)' % (B('end_date'), HOLDC), 'int'),
    KPI('Cars out today', 'SUMIFS(%s,%s,{today})' % (DF('rented'), DF('date')), 'int'),
    KPI('Cars free today', 'SUMIFS(%s,%s,{today})' % (DF('free'), DF('date')), 'int'),
    KPI('Cars free next Saturday', 'SUMIFS(%s,%s,{today}+MOD(6-WEEKDAY({today},2),7))' % (DF('free'), DF('date')), 'int'),
    KPI('Fleet utilisation today', 'SUMIFS(%s,%s,{today})' % (DF('utilisation'), DF('date')), 'pct'),
    KPI('Fleet utilisation, last 30 days', 'IFERROR(AVERAGEIFS(%s,%s,">="&({today}-30),%s,"<"&{today}),0)' % (DF('utilisation'), DF('date'), DF('date')), 'pct'),
    KPI('Fleet utilisation, next 14 days', 'IFERROR(AVERAGEIFS(%s,%s,">"&{today},%s,"<="&({today}+14)),0)' % (DF('utilisation'), DF('date'), DF('date')), 'pct'),
    KPI('Overlapping bookings now', 'COUNTIFS(%s,">0",%s,">="&{today})' % (B('overlap_n'), B('end_date')), 'int'),
    KPI('Tight or overlapping turns, next 14 days', '+'.join('COUNTIFS(%s,">="&{today},%s,"<="&({today}+14),%s,%s)' % (B('start_date'), B('start_date'), B('turn'), v(x)) for x in ('Tight turn', 'Inside turnaround time', 'Overlaps another booking')), 'int'),
    KPI('Vehicles in service now', 'COUNTIFS(%s,"<="&{today},%s,">="&{today})' % (BL('date'), BL('end_date')), 'int'),
    KPI('Service blocks, next 14 days', 'COUNTIFS(%s,">"&{today},%s,"<="&({today}+14))' % (BL('date'), BL('date')), 'int'),
    KPI('Extensions this month', 'COUNTIFS(%s,">="&%s,%s,"<"&EDATE(%s,1),%s,%s)' % (EXT('requested_on'), MS, EXT('requested_on'), MS, EXT('decision'), tok('extdec', 'Approved')), 'int'),
    KPI('Extension days this month', 'SUMIFS(%s,%s,">="&%s,%s,"<"&EDATE(%s,1),%s,%s)' % (EXT('extra_days'), EXT('requested_on'), MS, EXT('requested_on'), MS, EXT('decision'), tok('extdec', 'Approved')), 'int'),
    KPI('Vehicle swaps this month', 'COUNTIFS(%s,">="&%s,%s,"<"&EDATE(%s,1))' % (R('swaps', 'swap_date'), MS, R('swaps', 'swap_date'), MS), 'int'),
    KPI('Cancellation share, last 90 days', 'IFERROR(COUNTIFS(%s,%s,%s)/COUNTIFS(%s),0)' % (W90, B('status'), CAN, W90), 'pct'),
    KPI('No-shows, last 90 days', 'COUNTIFS(%s,%s,%s)' % (W90, B('status'), NOS), 'int'),
    KPI('Revenue lost to cancels, 90 days', 'SUMIFS(%s,%s,">="&({today}-90),%s,"<="&{today})' % (R('cancellations', 'revenue_lost'), R('cancellations', 'cancelled_on'), R('cancellations', 'cancelled_on')), 'money'),
    KPI('Average rental length, last 90 days', 'IFERROR(AVERAGEIFS(%s,%s%s),0)' % (B('days'), W90, HOLDC), 'num'),
    KPI('Average lead time, last 90 days', 'IFERROR(AVERAGEIFS(%s,%s,">="&({today}-90)%s),0)' % (B('lead_days'), B('created_on'), HOLDC), 'num'),
    KPI('Booked under 3 days ahead, 90 days', 'IFERROR(COUNTIFS(%s,"<3",%s,">="&({today}-90)%s)/COUNTIFS(%s,">="&({today}-90)%s),0)' % (B('lead_days'), B('created_on'), HOLDC, B('created_on'), HOLDC), 'pct'),
    KPI('Own channel share, last 90 days', 'IFERROR(COUNTIFS(%s,%s,0%s)/COUNTIFS(%s%s),0)' % (W90, B('fee_pct'), HOLDC, W90, HOLDC), 'pct'),
    KPI('Marketplace share, last 90 days', 'IFERROR((COUNTIFS(%s,%s%s)+COUNTIFS(%s,%s%s))/COUNTIFS(%s%s),0)' % (W90 + ',' + B('channel'), CH['Marketplace A'], HOLDC, W90 + ',' + B('channel'), CH['Marketplace B'], HOLDC, W90, HOLDC), 'pct'),
    KPI('Marketplace fees, last 30 days', 'SUMIFS(%s,%s,%s%s)+SUMIFS(%s,%s,%s%s)' % (B('channel_fee'), W30 + ',' + B('channel'), CH['Marketplace A'], HOLDC, B('channel_fee'), W30 + ',' + B('channel'), CH['Marketplace B'], HOLDC), 'money'),
    KPI('Net rate per day, own channels', 'IFERROR(SUMIFS(%s,%s,0%s)/SUMIFS(%s,%s,0%s),0)' % (B('net_amount'), W90 + ',' + B('fee_pct'), HOLDC, B('days'), W90 + ',' + B('fee_pct'), HOLDC), 'money'),
    KPI('Net rate per day, marketplaces', 'IFERROR((SUMIFS(%s,%s,%s%s)+SUMIFS(%s,%s,%s%s))/(SUMIFS(%s,%s,%s%s)+SUMIFS(%s,%s,%s%s)),0)' % (
        B('net_amount'), W90 + ',' + B('channel'), CH['Marketplace A'], HOLDC, B('net_amount'), W90 + ',' + B('channel'), CH['Marketplace B'], HOLDC, B('days'), W90 + ',' + B('channel'), CH['Marketplace A'], HOLDC, B('days'), W90 + ',' + B('channel'), CH['Marketplace B'], HOLDC), 'money'),
    KPI('Idle runs needing action, next 14 days', 'COUNTIFS(%s,">="&{set:idle_gap_days})' % R('idle_gaps', 'idle_days'), 'int'),
    KPI('First date a class has no free car', 'IFERROR(SMALL(%s,1),0)' % CCD('full_date'), 'date'),
]
assert len(kpis) == 30
dashboard = {"title": "Booking Dashboard", "kpis": kpis,
    "monthly": {"title": "Booking revenue, channel fees and net by month", "date": "bookings.start_date", "series": [
        {"label": "Revenue", "sum": "bookings.total", "date": "bookings.start_date"}, {"label": "Channel fees", "sum": "bookings.channel_fee", "date": "bookings.start_date"},
        {"label": "Net", "sum": "bookings.net_amount", "date": "bookings.start_date"}]},
    "breakdowns": [{"title": "Revenue by channel", "by": "bookings.channel", "value": "bookings.total", "agg": "sum"}, {"title": "Bookings by class", "by": "bookings.class", "value": "bookings.total", "agg": "count"},
                   {"title": "Bookings by status", "by": "bookings.status", "value": "bookings.total", "agg": "count"}, {"title": "Free car-days by class, next 14 days", "by": "cal_class.class", "value": "cal_class.free", "agg": "sum"}]}
PKR = PKT
insights = {"filters": [{"label": "Class", "list": "class"}, {"label": "Channel", "list": "channel"}, {"label": "Status", "list": "bstatus"}],
    "gauges": [
        {"title": "Class-months at the utilisation target", "num": AGG('count', 'class_month', where=[('utilisation', '>=', '{set:util_target}')]), "den": AGG('count', 'class_month')},
        {"title": "Bookings clear of overlaps", "num": AGG('count', 'bookings', where=[('overlap_n', '=', 0)]), "den": AGG('count', 'bookings')},
        {"title": "Pickups with a car ready", "num": AGG('count', 'pickups_returns', where=[('kind', '=', PKT), ('ready', '=', v('Car ready'))]), "den": AGG('count', 'pickups_returns', where=[('kind', '=', PKT)])},
        {"title": "Own channel share of bookings", "num": AGG('count', 'bookings', where=[('fee_pct', '=', 0)]), "den": AGG('count', 'bookings')},
        {"title": "Bookings kept after confirmation", "num": AGG('count', 'bookings', where=[('status', '<>', CAN), ('status', '<>', NOS)]), "den": AGG('count', 'bookings')},
        {"title": "Weekend car-days booked", "num": AGG('sum', 'weekend', 'weekend.booked_days'), "den": AGG('sum', 'weekend', 'weekend.fleet_days')}],
    "charts": [
        CHART('Booking revenue per month', 'column', 'month', [AGG('sum', 'bookings', 'bookings.total', date='bookings.start_date', label='Revenue')]),
        CHART('Bookings started per month', 'column', 'month', [AGG('count', 'bookings', date='bookings.start_date', label='Bookings')]),
        CHART('Channel fees per month', 'column', 'month', [AGG('sum', 'channel_month', 'channel_month.fee', date='channel_month.month', label='Channel fees')]),
        CHART('Net amount per month', 'line', 'month', [AGG('sum', 'channel_month', 'channel_month.net', date='channel_month.month', label='Net')]),
        CHART('Utilisation per month', 'line', 'month', [AGG('avg', 'class_month', 'class_month.utilisation', date='class_month.month', label='Utilisation')]),
        CHART('Rented days per month', 'column', 'month', [AGG('sum', 'class_month', 'class_month.rented_days', date='class_month.month', label='Rented days')]),
        CHART('Bookings by class', 'bar', 'bookings.class', [AGG('count', 'bookings', label='Bookings')]),
        CHART('Bookings by channel', 'bar', 'bookings.channel', [AGG('count', 'bookings', label='Bookings')]),
        CHART('Bookings by status', 'bar', 'bookings.status', [AGG('count', 'bookings', label='Bookings')]),
        CHART('Revenue by channel', 'bar', 'bookings.channel', [AGG('sum', 'bookings', 'bookings.total', label='Revenue')]),
        CHART('Bookings by pickup location', 'bar', 'bookings.pickup_location', [AGG('count', 'bookings', label='Bookings')]),
        CHART('Bookings by season', 'bar', 'bookings.season', [AGG('count', 'bookings', label='Bookings')]),
        CHART('Average utilisation by class', 'bar', 'class_month.class', [AGG('avg', 'class_month', 'class_month.utilisation', label='Utilisation')]),
        CHART('Bookings by start weekday', 'bar', 'bookings.start_day', [AGG('count', 'bookings', label='Bookings')]),
        CHART('Free car-days by class, next 14 days', 'bar', 'cal_class.class', [AGG('sum', 'cal_class', 'cal_class.free', label='Free car-days')]),
        CHART('Service blocks by kind', 'bar', 'service_blocks.kind', [AGG('count', 'service_blocks', label='Blocks')]),
        CHART('Pickups by weekday, next 45 days', 'bar', 'daily_fleet.weekday', [AGG('sum', 'daily_fleet', 'daily_fleet.pickups', label='Pickups')]),
        CHART('Cancellations and no-shows by kind', 'bar', 'cancellations.kind', [AGG('count', 'cancellations', label='Cancellations')]),
        CHART('Revenue lost by channel', 'bar', 'cancellations.channel', [AGG('sum', 'cancellations', 'cancellations.revenue_lost', label='Revenue lost')]),
        CHART('Extension requests by decision', 'bar', 'extensions.decision', [AGG('count', 'extensions', label='Requests')]),
        CHART('Vehicle swaps by reason', 'bar', 'swaps.reason', [AGG('count', 'swaps', label='Swaps')]),
        CHART('Idle days by class', 'bar', 'idle_gaps.class', [AGG('sum', 'idle_gaps', 'idle_gaps.idle_days', label='Idle days')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Next free date and class finder", "why": "a class, a start and a length give the car to offer, or the first free date, with the overlap and turnaround check", "where": "Next Free Date and Class Finder"},
    {"name": "Double-booking guard", "why": "every booking set against the others on the same car, with a verdict for a clash, a tight turn or a clear slot", "where": "Double-Booking Guard"},
    {"name": "Calendar by vehicle and day", "why": "the next 14 days car by car: rented, reserved, in service or free, from your own bookings and service blocks", "where": "Calendar by Vehicle and Day"},
    {"name": "Calendar by class and day", "why": "free cars of each class per day, with the first date a class has none", "where": "Calendar by Class and Day"},
    {"name": "Extension checker", "why": "a request to keep a car longer checked against the next booking and the service blocks, with an offer of another car", "where": "Extension Checker"},
    {"name": "Mid-rental swap tool", "why": "the best car to swap to, the change in the day rate and the miles allowance from the swap date", "where": "Mid-Rental Swap Tool"},
    {"name": "Marketplace fee share", "why": "fee per rented day against direct bookings, so a marketplace is compared like for like", "where": "Source Fee Share Report"},
    {"name": "Weekend shortage and surplus", "why": "weekend car-days booked against your target, with a list-more, list-fewer or hold verdict", "where": "Weekend Shortage and Surplus"},
    {"name": "Turnaround buffer tester", "why": "the minutes between a return and the next pickup of each class, and what a longer buffer would block", "where": "Turnaround Buffer Check"},
    {"name": "Marketplace block list", "why": "the dates to block on a listing today for every service block and booking, ready to send", "where": "Marketplace Block List"}]
competitors = [
    {"what": "generic booking calendar templates", "lacks": "show dates but cannot tell a clash, a tight turn or the first free car of a class"},
    {"what": "subscription rental-management software", "lacks": "charge each month or per vehicle and cannot test an extension, a swap or a buffer before you decide"},
    {"what": "shared online calendars", "lacks": "hold events but know nothing of fleet classes, service blocks, channel fees or utilisation"},
    {"what": "single-sheet fleet trackers", "lacks": "list cars and status but never show free cars by class and day or idle gaps to fill"},
    {"what": "marketplace host dashboards", "lacks": "see one channel only and give no view of the whole calendar, direct bookings and fees per rented day"}]
guide = [
    'Open Start and type your business name, your utilisation target, the turnaround hours that count as tight and the cancellation notice you ask for in the yellow cells.',
    'Check Vehicles, Vehicle Classes, Channels and Service Blocks: they hold the cars, the turnaround buffer of each class, the fee of each channel and the days a car is off the road.',
    'Enter every booking in Bookings with the car, the class, the channel, the dates, the times and the total. Days, fees, net amount and the turnaround verdict are worked out.',
    'Run the Overlap Check every day and fix every verdict that is not clear before the renter arrives.',
    'Read Calendar by Vehicle and Day and Calendar by Class and Day for the next 14 days, and Next Free Date to find the first free date of a car or a class.',
    'Use Pickups and Returns to plan the counter, the drivers and the cleaner, and to see the knock-on of a late return.',
    'Record each extension in Extension Requests, each swap in Vehicle Swaps and each cancellation or no-show in Cancellations.',
    'Fill gaps with Idle Gaps, and check weekends in Weekend Cars and the Weekend Tool.',
    'Update Channel by Month and Class by Month each month so utilisation and fee figures stay current.',
    f'Use the {len(tools)} calculators for calendar decisions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Read the Booking Dashboard and the Charts sheet every week: utilisation, free cars, clashes, cancellations and fees.',
    'A one-car host can use the same sheets with one vehicle and one channel and delete the rows that do not apply.']
listing = {"title": "Car Rental Booking Calendar Excel Template: Double-Booking Guard, Fleet Availability, Pickups and Returns, Extensions, Marketplace Fees",
    "headline": "See every car, every day, and never double-book a rental again",
    "tags": ["car rental", "booking calendar", "fleet availability", "excel template", "car hire", "double booking", "vehicle calendar", "rental business", "van rental", "pickup schedule", "marketplace fees", "car sharing host", "utilisation"],
    "description": ("Run the booking calendar of a small car or van rental in one Excel workbook. Built for an owner-operator and a manager who take bookings, plan pickups and returns and keep every car busy. "
        "Bookings holds every booking with the car, class, channel, dates, times and total, and works out the days, the channel fee, the net rate per day and a turnaround verdict. Overlap Check sets every booking against the others on the same car. "
        "Calendar by Vehicle and Day and Calendar by Class and Day show the next 14 days with rented, reserved, service and free cars. Next Free Date gives the first free date of each car and class.\n\n"
        "Pickups and Returns plans the counter and the knock-on of a late return. Extension Requests, Vehicle Swaps and Cancellations record the changes. Idle Gaps, Weekend Cars, Channel by Month, Class by Month and Daily Fleet Status show where cars sit idle and what each channel really pays.\n\n"
        f"{len(tools)} calculators answer weekly questions with a clear verdict: the class finder, the double-booking guard, the extension check, the mid-rental swap, the marketplace fee share, the weekend tool, the turnaround buffer, the late return, the cancellation fee, the pace, the marketplace block list and more. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to renters, corporate accounts, a hotel partner, marketplace support, the owner, the manager, drivers, the detailer, the mechanic and the bookkeeper.\n\n"
        "This is part two of the Car Rental Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Renters appear by first name and initial only. It helps you keep track of your calendar and does not promise results. Check your local rules and your insurance terms."),
    "features": ["Double-booking guard on every booking", "Next free date by car and by class", "Calendar by vehicle and by class for 14 days", "Pickups and returns with late-return knock-on", "Extension checker with another-car offer",
                 "Marketplace fee per rented day against direct", "Idle gaps and weekend shortage tool", f"{len(tools)} calculators for calendar decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Cancellation and no-show log with fees"]}
s = spec(id=f'{SUITE}-p2', slug='car-rental-bookings', profession='Car Rental Business', name='Booking Calendar and Availability',
         tagline='See every car, every day, and never double-book a rental again', price_usd=29,
         colors={"primary": "#1D3557", "accent": "#E63946"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 2, "of": 8, "focus": "Booking calendar and availability"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cr2.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
