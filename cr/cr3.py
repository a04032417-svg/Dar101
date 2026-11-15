"""Car Rental Business suite - part 3: Handover, Return, Fees and Damage."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr3_lists import *
from cr3_tables import settings, tables
from cr3_tools import tools
import cr3_data as D

SUITE = 'fx-20261115-car-rental'
NOTE = "Sample wording: adapt it to your own business and check your local rules and your insurance terms."
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
BILLED = tok('feestatus', 'Billed'); WOFF = tok('feestatus', 'Written off')
KE = tok('feekind', 'Extra mileage'); KL = tok('feekind', 'Late return'); KC = tok('feekind', 'Cleaning'); KR = tok('feekind', 'Fuel or charge refill')
OPENC = ca('Open claim'); T_OPEN = tok('tollstatus', 'Open'); T_PASSED = tok('tollstatus', 'Passed on')
D30 = '">="&({today}-30)'; D90 = '">="&({today}-90)'; D365 = '">="&({today}-365)'
def R(t, c): return '{range:%s.%s}' % (t, c)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('checkout_sheet', 'Check-out Sheet', 'Check-out record of one rental', 'checkout.handover_id', F(
        ('Booking', 'checkout.booking_id'), ('Vehicle', 'checkout.vehicle'), ('Class', 'checkout.class'), ('Renter', 'checkout.renter'), ('Out date', 'checkout.out_date'), ('Out time', 'checkout.out_time'),
        ('Return time agreed', 'checkout.agreed_time'), ('Out odometer, miles', 'checkout.out_odometer'), ('Out level, %', 'checkout.out_level'), ('Photos taken out', 'checkout.photos_out'), ('Keys', 'checkout.keys'),
        ('Deposit taken', 'checkout.deposit_taken'), ('Handled by', 'checkout.handled_by'), ('Miles included', 'checkout.miles_included')) + [
        FF('Level to bring back, %', LK('checkout', 'handover_id', 'out_level'), 'int'), FF('Grace minutes before a late fee', '{set:late_grace_min}', 'int'), FF('Late fee per started hour', '{set:late_fee_hour}', 'money'),
        FF('Fee per extra mile', '{set:extra_mile_fee}', 'money')]),
    FORM('checkin_sheet', 'Check-in Sheet', 'Check-in record of one rental', 'checkout.handover_id', F(
        ('Booking', 'checkout.booking_id'), ('Vehicle', 'checkout.vehicle'), ('Renter', 'checkout.renter'), ('In date', 'checkout.in_date'), ('In time', 'checkout.in_time'), ('Return time agreed', 'checkout.agreed_time'),
        ('In odometer, miles', 'checkout.in_odometer'), ('In level, %', 'checkout.in_level'), ('Photos taken in', 'checkout.photos_in'), ('Damage seen', 'checkout.damage_seen'), ('Miles driven', 'checkout.miles_driven'),
        ('Extra miles', 'checkout.extra_miles'), ('Late minutes', 'checkout.late_minutes'), ('Fee due', 'checkout.fee_due')) + [
        FF('Miles included in the rental', LK('checkout', 'handover_id', 'miles_included'), 'int'), FF('Miles driven, share of miles included', 'IFERROR(%s/%s,0)' % (LK('checkout', 'handover_id', 'miles_driven'), LK('checkout', 'handover_id', 'miles_included')), 'pct'),
        FF('Out level, %', LK('checkout', 'handover_id', 'out_level'), 'int')]),
    FORM('late_sheet', 'Late Return Sheet', 'Late return and its fee', 'late_returns.booking_id', F(
        ('Vehicle', 'late_returns.vehicle'), ('Return date', 'late_returns.date'), ('Agreed time', 'late_returns.agreed_time'), ('Actual time', 'late_returns.actual_time'), ('Late minutes', 'late_returns.late_minutes'),
        ('Started hours billed', 'late_returns.hours'), ('Fee due', 'late_returns.fee_due')) + [
        FF('Grace minutes', '{set:late_grace_min}', 'int'), FF('Minutes past the grace', 'MAX(0,%s-{set:late_grace_min})' % LK('late_returns', 'booking_id', 'late_minutes'), 'int'),
        FF('Fee per started hour', '{set:late_fee_hour}', 'money'), FF('Late returns of this vehicle in the log', 'COUNTIFS({range:late_returns.vehicle},%s)' % LK('late_returns', 'booking_id', 'vehicle'), 'int')]),
    FORM('mile_sheet', 'Extra Mileage Sheet', 'Extra mileage and its fee', 'extra_mileage.booking_id', F(
        ('Return date', 'extra_mileage.date'), ('Class', 'extra_mileage.class'), ('Plan', 'extra_mileage.plan'), ('Miles included', 'extra_mileage.miles_included'), ('Miles driven', 'extra_mileage.miles_driven'),
        ('Extra miles', 'extra_mileage.extra_miles'), ('Fee', 'extra_mileage.fee'), ('Overrun share', 'extra_mileage.over_share')) + [
        FF('Fee per extra mile', '{set:extra_mile_fee}', 'money'), FF('Extra-mileage rentals of this class', 'COUNTIFS({range:extra_mileage.class},%s)' % LK('extra_mileage', 'booking_id', 'class'), 'int'),
        FF('Average extra miles of this class', 'IFERROR(AVERAGEIFS({range:extra_mileage.extra_miles},{range:extra_mileage.class},%s),0)' % LK('extra_mileage', 'booking_id', 'class'), 'int')]),
    FORM('refill_sheet', 'Fuel or Charge Shortfall Sheet', 'Shortfall at check-in and the refill fee', 'fuel_levels.booking_id', F(
        ('Vehicle', 'fuel_levels.vehicle'), ('Return date', 'fuel_levels.date'), ('Fuel type', 'fuel_levels.fuel'), ('Out level, %', 'fuel_levels.out_level'), ('In level, %', 'fuel_levels.in_level'),
        ('Shortfall, points', 'fuel_levels.shortfall'), ('Refill steps of 10', 'fuel_levels.steps'), ('Refill fee', 'fuel_levels.refill_fee'), ('Real refill cost', 'fuel_levels.real_cost'), ('Margin', 'fuel_levels.margin')) + [
        FF('Fee per 10 points', '{set:refill_step_fee}', 'money'), FF('Service charge', '{set:refill_service_fee}', 'money'),
        FF('Margin as a share of the fee', 'IFERROR(%s/%s,0)' % (LK('fuel_levels', 'booking_id', 'margin'), LK('fuel_levels', 'booking_id', 'refill_fee')), 'pct')]),
    FORM('cleaning_sheet', 'Cleaning Fee Sheet', 'Cleaning fee of one rental', 'checkout.handover_id', F(
        ('Booking', 'checkout.booking_id'), ('Vehicle', 'checkout.vehicle'), ('Renter', 'checkout.renter'), ('In date', 'checkout.in_date'), ('Cleaning needed', 'checkout.cleaning'), ('Cleaning fee charged', 'checkout.clean_fee'),
        ('Total fee due on this rental', 'checkout.fee_due')) + [
        FF('Cleaning fee on your fee list', '{set:cleaning_fee}', 'money'), FF('Total fee due with cleaning added', '%s+IF(%s=%s,0,{set:cleaning_fee})' % (LK('checkout', 'handover_id', 'fee_due'), LK('checkout', 'handover_id', 'cleaning'), YES), 'money'),
        FF('Cleaning fees charged, last 90 days', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.kind},%s,{range:fee_log.date},%s)' % (KC, D90), 'money')]),
    FORM('damage_sheet', 'Damage Report Sheet', 'Damage reported on one rental', 'claims.claim_id', F(
        ('Booking', 'claims.booking_id'), ('Vehicle', 'claims.vehicle'), ('Renter', 'claims.renter'), ('Class', 'claims.class'), ('Channel', 'claims.channel'), ('Kind', 'claims.kind'), ('Status', 'claims.status'),
        ('Reported on', 'claims.reported_on'), ('Estimate', 'claims.estimate'), ('Deposit held on the booking', 'claims.deposit'), ('Days open', 'claims.days_open')) + [
        FF('Share of the estimate the deposit covers', 'IFERROR(MIN(1,%s/%s),0)' % (LK('claims', 'claim_id', 'deposit'), LK('claims', 'claim_id', 'estimate')), 'pct'),
        FF('Claims of this vehicle in the log', 'COUNTIFS({range:claims.vehicle},%s)' % LK('claims', 'claim_id', 'vehicle'), 'int'), FF('Days before you chase', '{set:claim_chase_days}', 'int')]),
    FORM('claim_update_sheet', 'Claim Update Sheet', 'Status update of one claim', 'claims.claim_id', F(
        ('Vehicle', 'claims.vehicle'), ('Kind', 'claims.kind'), ('Status', 'claims.status'), ('Open or closed', 'claims.open_flag'), ('Estimate', 'claims.estimate'), ('Repair cost', 'claims.repair_cost'),
        ('Deposit used', 'claims.deposit_used'), ('Claim paid', 'claims.claim_paid'), ('Written off', 'claims.written_off'), ('Closed on', 'claims.closed_on'), ('Net cost', 'claims.net_cost'), ('Action', 'claims.action')) + [
        FF('Recovered', LK('claims', 'claim_id', 'recovered'), 'money'), FF('Recovered as a share of the repair cost', 'IFERROR(%s/%s,0)' % (LK('claims', 'claim_id', 'recovered'), LK('claims', 'claim_id', 'repair_cost')), 'pct'),
        FF('Days open', LK('claims', 'claim_id', 'days_open'), 'int')]),
    FORM('toll_sheet', 'Toll and Ticket Sheet', 'Toll or ticket and what is passed on', 'tolls.toll_id', F(
        ('Date', 'tolls.date'), ('Vehicle', 'tolls.vehicle'), ('Kind', 'tolls.kind'), ('Amount', 'tolls.amount'), ('Booking', 'tolls.booking_id'), ('Renter', 'tolls.renter'), ('Status', 'tolls.status'),
        ('Admin fee charged', 'tolls.admin_fee'), ('Recovered', 'tolls.recovered')) + [
        FF('Admin fee on your list', '{set:toll_admin_fee}', 'money'), FF('Amount to pass on with the admin fee', '%s+{set:toll_admin_fee}' % LK('tolls', 'toll_id', 'amount'), 'money'),
        FF('Tolls and tickets of this vehicle', 'COUNTIFS({range:tolls.vehicle},%s)' % LK('tolls', 'toll_id', 'vehicle'), 'int')]),
    FORM('waiver_sheet', 'Fee Waiver Sheet', 'Waiver decision for one fee', 'fee_log.fee_id', F(
        ('Booking', 'fee_log.booking_id'), ('Vehicle ID', 'fee_log.vehicle_id'), ('Date', 'fee_log.date'), ('Kind', 'fee_log.kind'), ('Amount due', 'fee_log.amount_due'), ('Billed', 'fee_log.billed'),
        ('Collected', 'fee_log.collected'), ('Status', 'fee_log.status'), ('Renter', 'fee_log.renter'), ('Days since return', 'fee_log.days_since')) + [
        FF('Amount you give up if you waive it', '%s-%s' % (LK('fee_log', 'fee_id', 'amount_due'), LK('fee_log', 'fee_id', 'collected')), 'money'),
        FF('Share of the month fees due', 'IFERROR(%s/SUMIFS({range:fee_log.amount_due},{range:fee_log.month},%s),0)' % (LK('fee_log', 'fee_id', 'amount_due'), LK('fee_log', 'fee_id', 'month')), 'pct'),
        FF('Fees waived, written off in the log', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.status},%s)' % WOFF, 'money')]),
    FORM('renter_sheet', 'Renter Status Sheet', 'Status of one renter (status and dates only)', 'renter_status.renter_id', F(
        ('Renter', 'renter_status.renter'), ('Age band', 'renter_status.age_band'), ('Status', 'renter_status.status'), ('Documents checked', 'renter_status.documents_checked'),
        ('Rentals', 'renter_status.rentals'), ('Booking start', 'renter_status.start_date'), ('Go or no-go', 'renter_status.verdict')) + [
        FF('Renters with documents due in the list', 'COUNTIFS({range:renter_status.status},%s)' % tok('rstatus', 'Documents due'), 'int'),
        FF('Restricted renters in the list', 'COUNTIFS({range:renter_status.status},%s)' % tok('rstatus', 'Restricted'), 'int'), FF('Renters ready to go in the list', 'COUNTIFS({range:renter_status.verdict},%s)' % ca('Go'), 'int')]),
    FORM('keyphoto_sheet', 'Key and Photo Check Sheet', 'Keys and photo checks of one rental', 'photos_keys.booking_id', F(
        ('Vehicle', 'photos_keys.vehicle'), ('Handled by', 'photos_keys.handled_by'), ('Return date', 'photos_keys.date'), ('Photos taken out', 'photos_keys.photos_out'), ('Photos taken in', 'photos_keys.photos_in'),
        ('Keys', 'photos_keys.keys'), ('Checks missing', 'photos_keys.missing_checks'), ('Result', 'photos_keys.result')) + [
        FF('Your photo target', '{set:photo_target}', 'pct'), FF('Handovers by this staff member', 'COUNTIFS({range:photos_keys.handled_by},%s)' % LK('photos_keys', 'booking_id', 'handled_by'), 'int'),
        FF('Staff handovers with a check missing', 'COUNTIFS({range:photos_keys.handled_by},%s,{range:photos_keys.missing_checks},">0")' % LK('photos_keys', 'booking_id', 'handled_by'), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('checkout_doc', 'Check-out Report', 'Check-out condition report', 'checkout.handover_id', [
        'Check-out condition report of {set:company}, dated {today}. Handover {col:checkout.handover_id} for booking {col:checkout.booking_id}. Vehicle: {col:checkout.vehicle}, class {col:checkout.class}. Renter: {col:checkout.renter}.',
        'Out on {col:checkout.out_date} at {col:checkout.out_time}. Return agreed for {col:checkout.agreed_time}. Odometer out: {col:checkout.out_odometer} miles. Level out: {col:checkout.out_level} percent. Miles included: {col:checkout.miles_included}.',
        'Photos taken at check-out: {col:checkout.photos_out}. Keys handed over: {col:checkout.keys}. Deposit taken: {col:checkout.deposit_taken}. Handled by: {col:checkout.handled_by}.',
        'Please return the vehicle with the same level. A fee per extra mile of {set:extra_mile_fee} and a late fee of {set:late_fee_hour} per started hour after {set:late_grace_min} minutes apply as set in your hire terms.'], ['Staff member', 'Renter'], NOTE),
    DOC('checkin_doc', 'Check-in Report', 'Check-in condition report', 'checkout.handover_id', [
        'Check-in condition report of {set:company}, dated {today}. Handover {col:checkout.handover_id} for booking {col:checkout.booking_id}. Vehicle: {col:checkout.vehicle}. Renter: {col:checkout.renter}.',
        'Back on {col:checkout.in_date} at {col:checkout.in_time}. Odometer in: {col:checkout.in_odometer} miles. Level in: {col:checkout.in_level} percent. Miles driven: {col:checkout.miles_driven}. Photos taken at check-in: {col:checkout.photos_in}.',
        'Damage seen at return: {col:checkout.damage_seen}. Cleaning needed: {col:checkout.cleaning}. Checks missing on this handover: {col:checkout.missing}.',
        'Damage is recorded as a status and an amount only. Check your hire terms and your insurance terms for what happens next.'], ['Staff member', 'Renter'], NOTE),
    DOC('fee_statement_doc', 'Fee Statement', 'Fee statement for a rental', 'checkout.handover_id', [
        'Fee statement of {set:company}, dated {today}. Booking {col:checkout.booking_id}, vehicle {col:checkout.vehicle}, renter {col:checkout.renter}. Returned on {col:checkout.in_date}.',
        'Extra mileage: {col:checkout.extra_miles} extra miles, fee {col:checkout.mile_fee}. Late return: {col:checkout.late_minutes} minutes, fee {col:checkout.late_fee}. Refill: level short by {col:checkout.shortfall} points, fee {col:checkout.refill_fee}. Cleaning: {col:checkout.clean_fee}.',
        'Total fee due: {col:checkout.fee_due}. Fees are before any sales tax (confirm with your adviser).',
        'Please contact us within a few days if you think a line is wrong so that we can check it.'], ['Manager', 'Renter'], NOTE),
    DOC('late_notice_doc', 'Late Return Notice', 'Late return notice', 'late_returns.booking_id', [
        'Late return notice of {set:company}, dated {today}. Booking {col:late_returns.booking_id}, vehicle {col:late_returns.vehicle}. Return date {col:late_returns.date}.',
        'The return was agreed for {col:late_returns.agreed_time} and the vehicle came back at {col:late_returns.actual_time}, {col:late_returns.late_minutes} minutes later.',
        'After a grace of {set:late_grace_min} minutes we charge {set:late_fee_hour} for every started hour. Started hours billed: {col:late_returns.hours}. Fee due: {col:late_returns.fee_due}.',
        'Please call us as soon as you know you will be late the next time.'], ['Manager', 'Renter'], NOTE),
    DOC('mile_note_doc', 'Extra Mileage Note', 'Extra mileage charge note', 'extra_mileage.booking_id', [
        'Extra mileage note of {set:company}, dated {today}. Booking {col:extra_mileage.booking_id}, class {col:extra_mileage.class}, plan {col:extra_mileage.plan}. Return date {col:extra_mileage.date}.',
        'Miles included: {col:extra_mileage.miles_included}. Miles driven: {col:extra_mileage.miles_driven}. Extra miles: {col:extra_mileage.extra_miles}.',
        'The fee is {set:extra_mile_fee} for every mile over the allowance. Fee due: {col:extra_mileage.fee}. Miles are the unit of this sheet.',
        'The allowance of each plan is part of your hire terms.'], ['Manager', 'Renter'], NOTE),
    DOC('refill_note_doc', 'Refill Note', 'Fuel or charge refill note', 'fuel_levels.booking_id', [
        'Refill note of {set:company}, dated {today}. Booking {col:fuel_levels.booking_id}, vehicle {col:fuel_levels.vehicle}, fuel type {col:fuel_levels.fuel}. Return date {col:fuel_levels.date}.',
        'The level at check-out was {col:fuel_levels.out_level} percent and the level at check-in was {col:fuel_levels.in_level} percent, a shortfall of {col:fuel_levels.shortfall} points.',
        'We charge {set:refill_step_fee} for every 10 points plus a service charge of {set:refill_service_fee}. Refill steps: {col:fuel_levels.steps}. Refill fee: {col:fuel_levels.refill_fee}.',
        'Please return the vehicle at the same level to avoid this charge.'], ['Staff member', 'Renter'], NOTE),
    DOC('damage_doc', 'Damage Report Summary', 'Damage report summary (status and amounts only)', 'claims.claim_id', [
        'Damage report summary of {set:company}, dated {today}. Claim {col:claims.claim_id} for booking {col:claims.booking_id}, vehicle {col:claims.vehicle}. Renter: {col:claims.renter}.',
        'Kind: {col:claims.kind}. Reported on {col:claims.reported_on}. Status: {col:claims.status}. Estimate: {col:claims.estimate}. Deposit held on the booking: {col:claims.deposit}.',
        'This summary gives the status and the amounts only. It does not say who is at fault and it is not insurance or legal advice.',
        'Check your hire terms and your insurance terms for the next steps.'], ['Manager', 'Renter'], NOTE),
    DOC('claim_letter_doc', 'Claim Status Letter', 'Claim status letter', 'claims.claim_id', [
        'Claim status letter of {set:company}, dated {today}. Claim {col:claims.claim_id}, vehicle {col:claims.vehicle}. Dear {col:claims.renter},',
        'The status of the claim is {col:claims.status}. Estimate: {col:claims.estimate}. Repair cost: {col:claims.repair_cost}. Deposit used: {col:claims.deposit_used}. Claim paid: {col:claims.claim_paid}. Written off: {col:claims.written_off}.',
        'The claim has been open {col:claims.days_open} days. The deposit still held is {col:claims.deposit_held_now}.',
        'This letter gives the status and the amounts only and is not insurance or legal advice. Please check your hire terms and your insurance terms.'], ['Manager', 'Renter'], NOTE),
    DOC('toll_notice_doc', 'Toll Pass-On Notice', 'Toll and ticket pass-on notice', 'tolls.toll_id', [
        'Toll and ticket notice of {set:company}, dated {today}. Item {col:tolls.toll_id}, {col:tolls.kind}, dated {col:tolls.date}. Vehicle: {col:tolls.vehicle}. Booking: {col:tolls.booking_id}. Renter: {col:tolls.renter}.',
        'The item arrived while the vehicle was on your rental. Amount: {col:tolls.amount}. Admin fee: {set:toll_admin_fee}. Amount passed on: {col:tolls.to_pass}.',
        'Status of the item: {col:tolls.status}. Please pay within the time set in your hire terms.',
        'The admin fee covers the time to match and pass on the item.'], ['Manager', 'Renter'], NOTE),
    DOC('waiver_doc', 'Fee Waiver Note', 'Fee waiver note', 'fee_log.fee_id', [
        'Fee waiver note of {set:company}, dated {today}. Fee {col:fee_log.fee_id} on booking {col:fee_log.booking_id}, {col:fee_log.kind}, dated {col:fee_log.date}. Renter: {col:fee_log.renter}.',
        'Amount due: {col:fee_log.amount_due}. Collected so far: {col:fee_log.collected}. Status: {col:fee_log.status}.',
        'We waive this fee as a one-time courtesy. A waiver does not change your hire terms and the same fee can apply on a later rental.',
        'Please keep this note for your records.'], ['Manager', 'Renter'], NOTE),
    DOC('renter_doc', 'Renter Status Check', 'Renter status check sheet', 'renter_status.renter_id', [
        'Renter status check of {set:company}, dated {today}. Renter {col:renter_status.renter_id}: {col:renter_status.renter}. Age band: {col:renter_status.age_band}. Corporate account: {col:renter_status.account}.',
        'Status: {col:renter_status.status}. Documents checked: {col:renter_status.documents_checked}. Rentals so far: {col:renter_status.rentals}. Booking start: {col:renter_status.start_date}.',
        'Result of the check: {col:renter_status.verdict}.',
        'Only a status, dates and yes or no checks are kept. Check your local rules for what you may record about a renter.'], ['Manager', 'Renter'], NOTE),
    DOC('day_sheet_doc', 'Handover Day Sheet', 'Handover day sheet for one booking', 'bookings.booking_id', [
        'Handover day sheet of {set:company}, dated {today}. Booking {col:bookings.booking_id}: {col:bookings.vehicle}, class {col:bookings.class}. Renter: {col:bookings.renter}. Channel: {col:bookings.channel}.',
        'Pickup on {col:bookings.start_date}, return on {col:bookings.end_date} at {col:bookings.return_time}. Days: {col:bookings.days}. Deposit to hold: {col:bookings.deposit}. Status: {col:bookings.status}.',
        'Handover record: {col:bookings.handover_id}. Checks missing: {col:bookings.missing_checks}. Fee due so far: {col:bookings.fee_due}.',
        'Tick each check at the counter: photos, keys, level, odometer and deposit.'], ['Staff member', 'Manager'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('handover_chk', 'Car Handover Steps', 'checkout', 'checkout.out_date', [('Check the renter status and documents', -1), ('Clean the car and check the level', -1), ('Walk around the car and take photos', 0), ('Note the odometer and the level', 0),
        ('Hand over two keys', 0), ('Take the deposit or the card hold', 0), ('Explain the return time and the fees', 0), ('Save the check-out record', 0)]),
    CHK('return_chk', 'Car Return Steps', 'checkout', 'checkout.in_date', [('Note the return time', 0), ('Note the odometer and the level', 0), ('Walk around the car and take photos', 0), ('Count the keys', 0),
        ('Work out the fees due', 0), ('Tell the renter about any fee', 0), ('Send the car to cleaning', 0), ('Save the check-in record', 0), ('Release the deposit after the days you set', 5)]),
    CHK('photo_chk', 'Walk-Around Photo Steps', 'checkout', 'checkout.out_date', [('Photograph the front and the back', 0), ('Photograph both sides', 0), ('Photograph the wheels and the glass', 0), ('Photograph the inside and the dashboard', 0),
        ('Photograph the odometer and the level', 0), ('Note that photos were taken, yes or no', 0), ('Take the same photos at return', 3)]),
    CHK('level_chk', 'Fuel or Charge Level Steps', 'checkout', 'checkout.in_date', [('Read the level at check-in', 0), ('Compare it with the level at check-out', 0), ('Work out the shortfall in points', 0), ('Work out the refill steps and the fee', 0),
        ('Add the real refill cost to your records', 1), ('Tell the renter about the refill fee', 1)]),
    CHK('late_chk', 'Late Return Handling Steps', 'late_returns', 'late_returns.date', [('Note the agreed and the actual time', 0), ('Take off the grace minutes', 0), ('Work out the started hours', 0), ('Tell the renter about the fee', 0),
        ('Check the next pickup of the car', 0), ('Add the fee to the fee log', 1)]),
    CHK('billing_chk', 'Fee Billing at Return Steps', 'fee_log', 'fee_log.date', [('Work out every fee due on the return', 0), ('Enter the fees in the Fee Log', 0), ('Send the fee statement', 1), ('Bill the fees as one amount', 1), ('Record what was collected', 7),
        ('Chase fees that are still open', 14)]),
    CHK('damage_chk', 'Damage Found at Return Steps', 'claims', 'claims.reported_on', [('Photograph the damage', 0), ('Note the damage in the check-in record', 0), ('Tell the renter and note the date', 0), ('Ask for an estimate', 1), ('Record the claim status and the estimate', 1),
        ('Check the deposit held', 2), ('Check your insurance terms before you act', 2)]),
    CHK('claim_follow_chk', 'Claim Follow-Up Steps', 'claims', 'claims.reported_on', [('Record the estimate', 3), ('Book the repair slot', 7), ('Update the status each week', 14), ('Chase the claim after your chase day', 30),
        ('Use or release the deposit as the terms say', 35), ('Record the amounts paid and written off', 45), ('Close the claim', 50)]),
    CHK('toll_chk', 'Toll and Ticket Matching Steps', 'tolls', 'tolls.date', [('Enter the toll or ticket', 0), ('Find the rental that had the car on that date', 1), ('Add the admin fee', 1), ('Send the notice to the renter', 2), ('Record the amount passed on', 7),
        ('Mark items with no rental found', 14)]),
    CHK('fee_chase_chk', 'Weekly Fee Chase Steps', 'fee_log', 'fee_log.date', [('Open the Fee Ageing sheet', 7), ('List the fees older than your chase day', 7), ('Send a message to each renter', 8), ('Record any payment', 10), ('Review fees for write-off', 21),
        ('Check the money left on the table', 21)]),
    CHK('docs_chk', 'Renter Documents Check Steps', 'renter_status', 'renter_status.start_date', [('Ask for the documents before pickup', -3), ('Check them at the counter', 0), ('Note documents checked yes or no', 0), ('Check the age band', 0), ('Set the status', 0),
        ('Hold the car if documents are due', 0)]),
    CHK('one_car_chk', 'One-Car Host Handover Steps', 'bookings', 'bookings.start_date', [('Clean the car the day before', -1), ('Charge or fill the car', -1), ('Take photos of the car', 0), ('Note the odometer and the level', 0), ('Meet the renter or leave the keys', 0),
        ('Agree the return time', 0), ('Check the car and the level at return', 3), ('Bill any fee within a day', 4)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
OWN = first_name(OWNER); MGR = first_name(MANAGER); ACC = first_name(D.ACCOUNTANT['name']); DET = first_name(D.DETAILER_NAME); BKP = first_name(D.BOOKKEEPER_NAME)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('co_ready', 'Renter: your car is ready', 'checkout', 'checkout.phone', 'Hello {renter}, your car {vehicle} is ready, pickup at {out_time} on {out_date}. {center}'),
    M('co_level', 'Renter: return with the same level', 'checkout', 'checkout.phone', 'Hello {renter}, please return {vehicle} with the same fuel or charge level, {out_level} percent. {center}'),
    M('ci_thanks', 'Renter: thanks and fee statement', 'checkout', 'checkout.phone', 'Hello {renter}, thank you for returning {vehicle}. The fee statement for {booking_id} is {fee_due}. {center}'),
    M('late_fee', 'Renter: late return fee', 'checkout', 'checkout.phone', 'Hello {renter}, a late return fee of {late_fee} applies to {booking_id} for {late_minutes} minutes. {center}'),
    M('mile_fee', 'Renter: extra mileage charge', 'checkout', 'checkout.phone', 'Hello {renter}, an extra mileage charge of {mile_fee} applies to {booking_id} for {extra_miles} miles. {center}'),
    M('refill_fee', 'Renter: refill charge', 'checkout', 'checkout.phone', 'Hello {renter}, a refill charge of {refill_fee} applies to {booking_id}, the level at return was {in_level} percent. {center}'),
    M('clean_fee', 'Renter: cleaning fee', 'checkout', 'checkout.phone', 'Hello {renter}, a cleaning fee of {clean_fee} applies to {booking_id}. {center}'),
    M('fee_waived', 'Renter: fee waived', 'fee_log', 'fee_log.phone', 'Hello {renter}, we waived the fee of {amount_due} on {booking_id}. {center}'),
    M('pay_fees', 'Renter: please pay the fees', 'fee_log', 'fee_log.phone', 'Hello {renter}, please pay the fees of {open_amount} for {booking_id}. {center}'),
    M('toll_pass', 'Renter: toll passed on', 'tolls', 'tolls.phone', 'Hello {renter}, a toll on {date} of {amount} plus an admin fee of {admin_due} is passed on for {booking_id}. {center}'),
    M('ticket', 'Renter: a ticket was received', 'tolls', 'tolls.phone', 'Hello {renter}, a ticket dated {date} was received for {vehicle}, amount {amount}. {center}'),
    M('dmg_seen', 'Renter: damage noticed at return', 'claims', 'claims.phone', 'Hello {renter}, we noticed damage at the return of {vehicle}. The claim status is {status}. {center}'),
    M('dmg_estimate', 'Renter: repair estimate', 'claims', 'claims.phone', 'Hello {renter}, the repair estimate for claim {claim_id} is {estimate}. Your deposit of {deposit} is held. {center}'),
    M('claim_closed', 'Renter: claim closed', 'claims', 'claims.phone', 'Hello {renter}, claim {claim_id} is closed, the amount is {claim_paid}. {center}'),
    M('docs_ask', 'Renter: send your documents', 'renter_status', 'renter_status.phone', 'Hello {renter}, please send your documents before pickup on {start_date}. {center}'),
    M('docs_ok', 'Renter: documents checked', 'renter_status', 'renter_status.phone', 'Hello {renter}, your documents are checked, you are ready to go. {center}'),
    M('mp_dmg', 'Marketplace support: damage reported', 'claims', 'claims.market_phone', 'Hello, damage was reported on {booking_id}, the claim status is {status}. {center}'),
    M('mp_amount', 'Marketplace support: claim amount', 'claims', 'claims.market_phone', 'Hello, the claim amount for {booking_id} is {estimate}. {center}'),
    M('hotel_late', 'Hotel partner: late return fee', 'checkout', 'checkout.hotel_phone', 'Hello, the late return fee of your guest on {booking_id} is {late_fee} for {late_minutes} minutes. {center}'),
    M('corp_fees', 'Corporate account: fees on a booking', 'checkout', 'checkout.corp_phone', 'Hello, the fees on {booking_id} are {fee_due}. {center}'),
    M('ow_open', 'Owner: fees still open', 'fee_log', 'fee_log.owner_phone', 'Hello %s, {open_fees} fees worth {open_total} are still open. {center}' % OWN),
    M('ow_claim', 'Owner: a claim is open', 'claims', 'claims.owner_phone', 'Hello %s, claim {claim_id} has been open {days_open} days. {center}' % OWN),
    M('ow_left', 'Owner: money left on the table', 'money_left', 'money_left.owner_phone', 'Hello %s, the money left on the table for {month} is {not_billed}. {center}' % OWN),
    M('ow_damage', 'Owner: damage cost per 100 rentals', 'claims_month', 'claims_month.owner_phone', 'Hello %s, the damage cost per 100 rentals for {month} is {damage_rate}. {center}' % OWN),
    M('mg_bill', 'Manager: bill the fees today', 'fee_log', 'fee_log.manager_phone', 'Hello %s, please bill the fees for {booking_id} today, amount {amount_due}. {center}' % MGR),
    M('mg_missing', 'Manager: checks missing', 'checkout', 'checkout.manager_phone', 'Hello %s, {missing} checks are missing at check-out for {vehicle}. {center}' % MGR),
    M('mg_chase', 'Manager: chase a claim', 'claims', 'claims.manager_phone', 'Hello %s, please chase claim {claim_id} with the renter. {center}' % MGR),
    M('mg_tolls', 'Manager: tolls to pass on', 'tolls', 'tolls.manager_phone', 'Hello %s, the toll list has {open_tolls} items to pass on. {center}' % MGR),
    M('det_dirty', 'Detailer: car returned dirty', 'checkout', 'checkout.detailer_phone', 'Hello %s, {vehicle} returned dirty on {in_date}, the cleaning fee applies. {center}' % DET),
    M('body_est', 'Body repair shop: estimate request', 'claims', 'claims.body_phone', 'Hello, please give an estimate for {vehicle}, claim {claim_id}. {center}'),
    M('body_slot', 'Body repair shop: repair slot', 'claims', 'claims.body_phone', 'Hello, the repair slot for {vehicle} is {slot_date}. {center}'),
    M('broker', 'Insurance broker: claim status', 'claims', 'claims.broker_phone', 'Hello, claim {claim_id} has the status {status} and the estimate {estimate}. {center}'),
    M('acc_fees', 'Accountant: fees collected, written off', 'money_left', 'money_left.accountant_phone', 'Hello %s, the fees collected for {month} are {collected} and the fees written off are {written_off}. {center}' % ACC),
    M('bk_tolls', 'Bookkeeper: tolls and tickets passed on', 'tolls', 'tolls.bookkeeper_phone', 'Hello %s, the tolls and tickets passed on for {month} are {month_passed}. {center}' % BKP),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def FD(kind, d=''):
    return 'SUMIFS({range:fee_log.amount_due},{range:fee_log.kind},%s%s)' % (kind, d)
THIS = ',{range:fee_log.month},%s' % MS
kpis = [
    KPI('Check-outs this month', 'COUNTIFS({range:checkout.out_date},">="&%s)' % MS, 'int'),
    KPI('Check-ins this month', 'COUNTIFS({range:checkout.in_date},">="&%s)' % MS, 'int'),
    KPI('Photos both ways, last 30 days', 'COUNTIFS({range:checkout.out_date},%s,{range:checkout.photos_out},%s,{range:checkout.photos_in},%s)' % (D30, YES, YES), 'int'),
    KPI('Handovers missing a check, last 30 days', 'COUNTIFS({range:checkout.out_date},%s,{range:checkout.missing},">0")' % D30, 'int'),
    KPI('Average miles per rental, 90 days', 'IFERROR(AVERAGEIFS({range:checkout.miles_driven},{range:checkout.in_date},%s),0)' % D90, 'int'),
    KPI('Extra-mileage fees due this month', FD(KE, THIS), 'money'),
    KPI('Late returns this month', 'COUNTIFS({range:checkout.in_date},">="&%s,{range:checkout.late_minutes},">0")' % MS, 'int'),
    KPI('Late minutes this month', 'SUMIFS({range:checkout.late_minutes},{range:checkout.in_date},">="&%s)' % MS, 'int'),
    KPI('Late-return fees due this month', FD(KL, THIS), 'money'),
    KPI('Refill fees due, last 30 days', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.kind},%s,{range:fee_log.date},%s)' % (KR, D30), 'money'),
    KPI('Cleaning fees due, last 90 days', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.kind},%s,{range:fee_log.date},%s)' % (KC, D90), 'money'),
    KPI('Fees due this month', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.month},%s)' % MS, 'money'),
    KPI('Fees collected this month', 'SUMIFS({range:fee_log.collected},{range:fee_log.month},%s)' % MS, 'money'),
    KPI('Fees open now', 'SUM({range:fee_log.open_amount})', 'money'),
    KPI('Fees open over 14 days', 'SUMIFS({range:fee_log.open_amount},{range:fee_log.days_since},">"&{set:fee_collect_days})', 'money'),
    KPI('Fees written off, last 90 days', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.status},%s,{range:fee_log.date},%s)' % (WOFF, D90), 'money'),
    KPI('Money left on the table, last 90 days', 'SUMIFS({range:fee_log.not_billed_amt},{range:fee_log.date},%s)' % D90, 'money'),
    KPI('Collection rate, last 90 days', 'IFERROR(SUMIFS({range:fee_log.collected},{range:fee_log.date},%s)/SUMIFS({range:fee_log.amount_due},{range:fee_log.date},%s,{range:fee_log.billed},%s),0)' % (D90, D90, YES), 'pct'),
    KPI('Damage seen at return, last 90 days', 'COUNTIFS({range:checkout.damage_seen},%s,{range:checkout.in_date},%s)' % (YES, D90), 'int'),
    KPI('Claims open now', 'COUNTIFS({range:claims.open_flag},%s)' % OPENC, 'int'),
    KPI('Claims open over 30 days', 'COUNTIFS({range:claims.open_flag},%s,{range:claims.days_open},">"&{set:claim_chase_days})' % OPENC, 'int'),
    KPI('Oldest open claim, days', 'SUMPRODUCT(MAX((({range:claims.status}=%s)+({range:claims.status}=%s)+({range:claims.status}=%s))*({today}-{range:claims.reported_on})))' % (tok('claimstatus', 'Reported'), tok('claimstatus', 'Estimate'), tok('claimstatus', 'In repair')), 'int'),
    KPI('Estimate of open claims', 'SUMIFS({range:claims.estimate},{range:claims.open_flag},%s)' % OPENC, 'money'),
    KPI('Net damage cost, last 90 days', 'SUMIFS({range:claims.net_cost},{range:claims.reported_on},%s)' % D90, 'money'),
    KPI('Damage cost per 100 rentals, 12 months', 'IFERROR(SUMIFS({range:claims_month.net_cost},{range:claims_month.month},">="&EDATE(%s,-12),{range:claims_month.month},"<"&%s)/SUMIFS({range:claims_month.rentals},{range:claims_month.month},">="&EDATE(%s,-12),{range:claims_month.month},"<"&%s)*100,0)' % (MS, MS, MS, MS), 'money'),
    KPI('Damage written off, last 12 months', 'IFERROR(SUMIFS({range:claims.written_off},{range:claims.reported_on},%s)/SUMIFS({range:claims.repair_cost},{range:claims.reported_on},%s),0)' % (D365, D365), 'pct'),
    KPI('Tolls and tickets open now', 'COUNTIFS({range:tolls.status},%s)' % T_OPEN, 'int'),
    KPI('Tolls and tickets passed on, 90 days', 'COUNTIFS({range:tolls.status},%s,{range:tolls.passed_on},%s)' % (T_PASSED, D90), 'int'),
    KPI('Toll and ticket admin fees, last 30 days', 'SUMIFS({range:tolls.admin_fee},{range:tolls.passed_on},%s)' % D30, 'money'),
    KPI('Renters with documents due', 'COUNTIFS({range:renter_status.status},%s)' % tok('rstatus', 'Documents due'), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Handover and Fees Dashboard", "kpis": kpis,
    "monthly": {"title": "Fees due, fees collected and fees left unbilled", "date": "fee_log.date", "series": [
        {"label": "Fees due", "sum": "fee_log.amount_due", "date": "fee_log.date"}, {"label": "Fees collected", "sum": "fee_log.collected", "date": "fee_log.date"},
        {"label": "Not billed", "sum": "fee_log.not_billed_amt", "date": "fee_log.date"}]},
    "breakdowns": [{"title": "Fees due by kind", "by": "fee_log.kind", "value": "fee_log.amount_due", "agg": "sum"}, {"title": "Fees by status", "by": "fee_log.status", "value": "fee_log.amount_due", "agg": "sum"},
                   {"title": "Claims by status", "by": "claims.status", "value": "claims.estimate", "agg": "sum"}, {"title": "Tolls and tickets by status", "by": "tolls.status", "value": "tolls.amount", "agg": "count"}]}
insights = {"filters": [{"label": "Vehicle class", "list": "class"}, {"label": "Channel", "list": "channel"}, {"label": "Fee kind", "list": "feekind"}],
    "gauges": [
        {"title": "Handovers with photos both ways", "num": AGG('count', 'checkout', where=[('photos_out', '=', YES), ('photos_in', '=', YES)]), "den": AGG('count', 'checkout', where=[('in_odometer', '>', 0)])},
        {"title": "Fees collected against fees due", "num": AGG('sum', 'fee_log', 'fee_log.collected'), "den": AGG('sum', 'fee_log', 'fee_log.amount_due')},
        {"title": "Fees billed against fees due", "num": AGG('sum', 'fee_log', 'fee_log.amount_due', where=[('billed', '=', YES)]), "den": AGG('sum', 'fee_log', 'fee_log.amount_due')},
        {"title": "Claims closed within 30 days", "num": AGG('count', 'claims', where=[('closed_on', '>', 0), ('days_open', '<=', 30)]), "den": AGG('count', 'claims', where=[('closed_on', '>', 0)])},
        {"title": "Tolls and tickets passed on", "num": AGG('count', 'tolls', where=[('status', '=', T_PASSED)]), "den": AGG('count', 'tolls')},
        {"title": "Damage recovered against repair cost", "num": AGG('sum', 'claims', 'claims.recovered'), "den": AGG('sum', 'claims', 'claims.repair_cost')}],
    "charts": [
        CHART('Fees due per month', 'column', 'month', [AGG('sum', 'fee_log', 'fee_log.amount_due', date='fee_log.date', label='Fees due')]),
        CHART('Fees collected per month', 'column', 'month', [AGG('sum', 'fee_log', 'fee_log.collected', date='fee_log.date', label='Fees collected')]),
        CHART('Fees due by kind', 'bar', 'fee_log.kind', [AGG('sum', 'fee_log', 'fee_log.amount_due', label='Fees due')]),
        CHART('Fees by status', 'bar', 'fee_log.status', [AGG('sum', 'fee_log', 'fee_log.amount_due', label='Fees due')]),
        CHART('Money left on the table per month', 'column', 'month', [AGG('sum', 'fee_log', 'fee_log.not_billed_amt', date='fee_log.date', label='Not billed')]),
        CHART('Late returns per month', 'column', 'month', [AGG('count', 'checkout', date='checkout.in_date', where=[('late_minutes', '>', 0)], label='Late returns')]),
        CHART('Late minutes by class', 'bar', 'checkout.class', [AGG('sum', 'checkout', 'checkout.late_minutes', label='Late minutes')]),
        CHART('Extra miles per month', 'column', 'month', [AGG('sum', 'checkout', 'checkout.extra_miles', date='checkout.in_date', label='Extra miles')]),
        CHART('Refill fees per month', 'column', 'month', [AGG('sum', 'fee_log', 'fee_log.amount_due', date='fee_log.date', where=[('kind', '=', KR)], label='Refill fees')]),
        CHART('Cleaning fees per month', 'column', 'month', [AGG('sum', 'fee_log', 'fee_log.amount_due', date='fee_log.date', where=[('kind', '=', KC)], label='Cleaning fees')]),
        CHART('Damage claims per month', 'column', 'month', [AGG('count', 'claims', date='claims.reported_on', label='Claims')]),
        CHART('Claims by kind', 'bar', 'claims.kind', [AGG('count', 'claims', label='Claims')]),
        CHART('Claims by status', 'bar', 'claims.status', [AGG('count', 'claims', label='Claims')]),
        CHART('Net damage cost per month', 'column', 'month', [AGG('sum', 'claims', 'claims.net_cost', date='claims.reported_on', label='Net damage cost')]),
        CHART('Damage cost by class', 'bar', 'claims.class', [AGG('sum', 'claims', 'claims.repair_cost', label='Repair cost')]),
        CHART('Damage cost by channel', 'bar', 'claims.channel', [AGG('sum', 'claims', 'claims.repair_cost', label='Repair cost')]),
        CHART('Estimate by claim kind', 'bar', 'claims.kind', [AGG('sum', 'claims', 'claims.estimate', label='Estimate')]),
        CHART('Tolls and tickets per month', 'column', 'month', [AGG('count', 'tolls', date='tolls.date', label='Tolls and tickets')]),
        CHART('Tolls and tickets by kind', 'bar', 'tolls.kind', [AGG('sum', 'tolls', 'tolls.amount', label='Amount')]),
        CHART('Tolls and tickets by status', 'bar', 'tolls.status', [AGG('count', 'tolls', label='Items')]),
        CHART('Handovers per month', 'column', 'month', [AGG('count', 'checkout', date='checkout.out_date', label='Handovers')]),
        CHART('Handovers with photos both ways per month', 'line', 'month', [AGG('count', 'checkout', date='checkout.out_date', where=[('photos_out', '=', YES), ('photos_in', '=', YES)], label='With photos both ways')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Return fee calculator", "why": "agreed against actual time, miles, levels and cleaning give every fee due at the counter with a clear fee or no fee verdict", "where": "Return Fee Calculator"},
    {"name": "Money left on the table", "why": "fees that were due and never billed, by month and kind, with what you can still collect", "where": "Money Left Finder"},
    {"name": "Claim chase list", "why": "open claims ranked by days open times the estimate, so the oldest big claim is chased first", "where": "Claim Chase List"},
    {"name": "Repeat-damage finder", "why": "classes, channels, plans, young drivers and cover options ranked by damage cost per rental to show who needs a larger deposit", "where": "Repeat-Damage Finder"},
    {"name": "Deposit size test", "why": "repair costs of 12 months set against the deposit of each class, with the raise needed to cover most cases", "where": "Deposit Size Test"},
    {"name": "Toll and ticket pass-through", "why": "every toll and ticket matched to the rental that had the car on that date, with the admin fee added", "where": "Toll Match"},
    {"name": "Renter go or no-go screen", "why": "status, documents, age band and extra driver checked into a go, hold or no-go verdict before the keys change hands", "where": "Renter Go or No-Go Screen"},
    {"name": "Handover completeness check", "why": "photos, keys, level, odometer and deposit counted so a car never leaves with a check missing", "where": "Handover Completeness Check"},
    {"name": "Photo discipline score", "why": "the share of handovers with photos both ways and two keys by staff member against your target", "where": "Photo Discipline Score"},
    {"name": "Damage cost per 100 rentals", "why": "your net damage cost set against your own 3-month average, so a bad month is seen early", "where": "Damage Cost per 100 Rentals"}]
competitors = [
    {"what": "subscription rental-management software", "lacks": "charges per vehicle or per booking and hides fee leakage: no money-left-on-the-table view and no deposit size test you can change"},
    {"what": "generic booking calendar template", "lacks": "lists pickups and returns but has no odometer, level, photos or keys check and no fee calculation at return"},
    {"what": "single-sheet vehicle expense log", "lacks": "records costs only: no handover record, no claim status, no tolls matched to the renter that had the car"},
    {"what": "budget-model template", "lacks": "shows totals but never the damage cost per rental by class, channel or cover option"},
    {"what": "paper handover forms", "lacks": "keep a record per rental but never add up late minutes, extra miles, refills and fees due or chase what is open"}]
guide = [
    'Open Start and type your business name, your fees (extra mile, late return, cleaning, refill, toll admin) and your chase days in the yellow cells.',
    'Keep Vehicles and Vehicle Classes up to date: the class, fuel type, deposit and miles included each day (miles are the demo unit, set your own).',
    'At every pickup and return write one row in Check-out and Check-in: handing the car over and taking it back, with time, odometer, level, photos yes or no and keys.',
    'Read the fee columns of that row: extra miles, late minutes after the grace, refill steps and cleaning give the fee due.',
    'Copy each fee into Fee Log, mark it billed or not, and write what you collected; Fee Ageing and Money Left on the Table fill in by themselves.',
    'Use Return Fee Calculator at the counter and Handover Completeness Check before a car leaves.',
    'Record each damage in Damage Claims with its status and amounts only; Claim Chase List ranks the open claims and Claim Ageing shows how old they are.',
    'Run Repeat-Damage Finder and Deposit Size Test every quarter to see which segment needs a larger deposit.',
    'Enter every toll and ticket in Tolls and Tickets; Toll Match names the rental that had the car and the amount to pass on.',
    'Check Renter Status before a pickup: documents checked, age band and status give a go, hold or no-go.',
    'Use Photos and Keys and Photo Discipline Score to keep your handover habits steady.',
    'A one-car host uses the same sheets with one vehicle and one channel.',
    'Replace the demo rows with your own: delete the sample rows and keep the formulas, the sheets work with no macros in Excel and Google Sheets.',
    f'Use the {len(tools)} calculators, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Handover and Fees Dashboard and the Charts every week: fees due, collected and left unbilled, claims, tolls and photo checks.']
listing = {"title": "Car Rental Handover, Return, Fees and Damage Excel Template: Check-out and Check-in, Late Fees, Claims, Tolls and Deposits",
    "headline": "Every handover, return fee, damage claim and toll in one workbook",
    "tags": ["car rental", "rental car excel", "check-in check-out", "late return fee", "damage claim log", "car hire template", "vehicle handover", "rental fees", "toll tracker", "fleet management", "van rental", "car sharing host", "rental business"],
    "description": ("Run the moment a rental car changes hands, and the money that depends on it, in one Excel workbook. Built for the owner-operator of a small car or van rental or a car-sharing host and the manager, a detailer or a delivery driver who hands cars over and takes them back. "
        "Check-out and Check-in logs time, odometer, fuel or charge level, photos taken yes or no and keys; miles driven, late minutes after your grace, refill steps and the fee due fill in by themselves (miles are the demo unit, set your own). "
        "Fee Log shows each fee billed, collected, written off or never billed, Fee Ageing shows what is open, and Money Left on the Table shows the fees you were owed and forgot to bill, month by month.\n\n"
        "Damage Claims keeps each claim as a status and amounts only, with days open, net cost and a chase action; Claim Ageing and Claims by Month show how old the claims are, and Damage by Segment ranks classes, channels, plans, young drivers and cover options by damage cost per rental. "
        "Tolls and Tickets and Toll Match find the rental that had the car on the date and show the amount to pass on with your admin fee. Renter Status gives a go, hold or no-go verdict from status and documents checked. No addresses, licence or card numbers are kept.\n\n"
        f"{len(tools)} decision tools answer weekly questions: which fees are due on this return, how much money was left on the table, which claim to chase first, which segment needs a larger deposit, does the deposit of a class cover the damage, and whether to pass on a toll. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to renters, a hotel partner, marketplace support, your team and your advisers.\n\n"
        "This is part three of the Car Rental Business suite. A standard .xlsx workbook with no macros and no per-vehicle fee, with a demo copy full of sample data. It helps you keep track of your fees and claims and does not promise results. Check your local rules and your insurance terms."),
    "features": ["Check-out and check-in log with odometer and level", "Fee calculation at return", "Money left on the table, month by month", "Fee log with ageing and write-offs", "Damage claims as status and amounts",
                 "Claim chase list ranked by age and estimate", "Repeat-damage finder and deposit size test", "Tolls matched to the rental that had the car", "Renter go or no-go screen", f"{len(tools)} decision tools",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p3', slug='car-rental-handover', profession='Car Rental Business', name='Handover, Return, Fees and Damage',
         tagline='Every handover, return fee, damage claim and toll in one place', price_usd=29,
         colors={"primary": "#1D3557", "accent": "#E63946"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Handover, return, fees and damage"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cr3.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
