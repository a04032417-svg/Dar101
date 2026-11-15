"""Car Rental Business suite - part 5: Fleet Register, Service and Renewals."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr5_lists import *
from cr5_tables import settings, tables
from cr5_tools import tools
import cr5_data as D

SUITE = 'fx-20261115-car-rental'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES = '{list:yesno.yes}'
SOLD = tok('vstatus', 'Sold'); ACT = tok('vstatus', 'Active'); WSH = tok('vstatus', 'In workshop'); UP = tok('rstatus2', 'Upcoming'); DONE = tok('rstatus2', 'Done')
def G(x): return tok('mgroup', x)
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def ADR(c):
    f = '0'
    for cl in reversed(CLASSES): f = 'IF(%s=%s,{set:adr_%s},%s)' % (c, tok('class', cl), key('class', cl), f)
    return f
def VLK(c, name): return 'IFERROR(INDEX({range:vehicles.%s},MATCH(%s,{range:vehicles.vehicle},0)),0)' % (c, name)

# ------------------------------------------------------------------ forms (12)
V1 = lambda c: LK('vehicles', 'vehicle_id', c)
S2 = lambda c: LK('slots', 'slot_id', c)
L3 = lambda c: LK('service_log', 'maint_id', c)
R4 = lambda c: LK('repair_log', 'maint_id', c)
T5 = lambda c: LK('tyres', 'vehicle', c)
RV = lambda c: LK('renewals_by_veh', 'vehicle', c)
FC = lambda c: LK('fleet_changes', 'change_id', c)
forms = [
    FORM('vehicle_sheet', 'Vehicle Register Sheet', 'Vehicle record with service due', 'vehicles.vehicle_id', F(
        ('Vehicle', 'vehicles.vehicle'), ('Plate', 'vehicles.plate'), ('Class', 'vehicles.class'), ('Model year', 'vehicles.year'), ('Purchase date', 'vehicles.purchase_date'), ('Purchase price', 'vehicles.purchase_price'),
        ('Financed', 'vehicles.financed'), ('Odometer, miles', 'vehicles.odometer'), ('Status', 'vehicles.status'), ('Service interval, miles', 'vehicles.interval_miles'), ('Service interval, months', 'vehicles.interval_months'),
        ('Last service date', 'vehicles.last_service_date'), ('Miles since service', 'vehicles.miles_since'), ('Miles to next service', 'vehicles.miles_to'), ('Next service date', 'vehicles.next_date'), ('Service check', 'vehicles.service_flag'),
        ('Register gaps', 'vehicles.gaps')) + [
        FF('Age in years', 'ROUND(%s/12,1)' % V1('age_months'), 'num'), FF('Insurance a month', 'ROUND(%s/12,2)' % V1('insurance_year'), 'money'), FF('Resale estimate as a share of the price', 'IFERROR(%s/%s,0)' % (V1('resale_estimate'), V1('purchase_price')), 'pct')]),
    FORM('service_booking_sheet', 'Service Booking Sheet', 'Workshop booking for one slot', 'slots.slot_id', F(
        ('Vehicle', 'slots.vehicle'), ('Class', 'slots.class'), ('Candidate date', 'slots.date'), ('Work', 'slots.kind'), ('Days needed', 'slots.days'), ('Drop-off time', 'slots.drop_time'), ('Back on', 'slots.return_date'),
        ('Booked days lost', 'slots.lost'), ('Free days after', 'slots.free_after'), ('Revenue lost', 'slots.revenue_lost'), ('Verdict', 'slots.verdict')) + [
        FF('Days from today', '%s-{today}' % S2('date'), 'int'), FF('Average daily rate of the class', 'IFERROR(%s,0)' % S2('adr'), 'money'), FF('Workshop slots you can use each week', '{set:slots_per_week}', 'int')]),
    FORM('service_done_sheet', 'Service Completed Sheet', 'Record of a completed workshop visit', 'service_log.maint_id', F(
        ('Vehicle', 'service_log.vehicle'), ('Class', 'service_log.class'), ('Date', 'service_log.date'), ('Kind', 'service_log.kind'), ('Odometer, miles', 'service_log.odometer'), ('Cost', 'service_log.cost'),
        ('Days off road', 'service_log.days_off_road'), ('Vendor', 'service_log.vendor'), ('Service on time', 'service_log.on_time')) + [
        FF('Next service date by months', 'EDATE(%s,%s)' % (L3('date'), VLK('interval_months', L3('vehicle'))), 'date'), FF('Next service at, miles', '%s+%s' % (L3('odometer'), VLK('interval_miles', L3('vehicle'))), 'int'),
        FF('Cost for each day off road', '%s/MAX(1,%s)' % (L3('cost'), L3('days_off_road')), 'money')]),
    FORM('repair_sheet', 'Repair Sheet', 'Repair job with cost and days off road', 'repair_log.maint_id', F(
        ('Vehicle', 'repair_log.vehicle'), ('Class', 'repair_log.class'), ('Date', 'repair_log.date'), ('Kind', 'repair_log.kind'), ('Cost', 'repair_log.cost'), ('Days off road', 'repair_log.days_off_road'),
        ('Location', 'repair_log.location'), ('Cost per 1,000 miles', 'repair_log.cost_1000')) + [
        FF('Booked days lost', 'ROUND(%s*%s,1)' % (R4('days_off_road'), VLK('util_12m', R4('vehicle'))), 'num'), FF('Cost for each day off road', '%s/MAX(1,%s)' % (R4('cost'), R4('days_off_road')), 'money'),
        FF('Days since the job', '{today}-%s' % R4('date'), 'int')]),
    FORM('tyre_sheet', 'Tyre Change Sheet', 'Tyre set and miles to the next one', 'tyres.vehicle', F(
        ('Class', 'tyres.class'), ('Last tyre set', 'tyres.tyre_date'), ('Odometer then, miles', 'tyres.odo_then'), ('Odometer now', 'tyres.odometer'), ('Miles since', 'tyres.miles_since'), ('Miles to next set', 'tyres.next_tyre_miles'),
        ('Tyres due on', 'tyres.due_on'), ('Tyre check', 'tyres.tyre_flag')) + [
        FF('Tyre life, miles', 'SUMIFS({range:service_types.interval_miles},{range:service_types.service_type},%s)' % tok('mkind', 'Tyre set'), 'int'),
        FF('Share of the tyre life used', 'IFERROR(%s/SUMIFS({range:service_types.interval_miles},{range:service_types.service_type},%s),0)' % (T5('miles_since'), tok('mkind', 'Tyre set')), 'pct'), FF('Next season change', '{set:season_change}', 'date')]),
    FORM('registration_sheet', 'Registration Renewal Sheet', 'Registration renewal of one vehicle', 'renewals_by_veh.vehicle', F(
        ('Class', 'renewals_by_veh.class'), ('Next registration', 'renewals_by_veh.next_reg'), ('Registration cost', 'renewals_by_veh.cost_reg'), ('Soonest renewal', 'renewals_by_veh.soonest'), ('Colour band', 'renewals_by_veh.band'),
        ('Renewals cost, next 12 months', 'renewals_by_veh.cost_12m')) + [
        FF('Days to the registration date', '%s-{today}' % RV('next_reg'), 'int'), FF('Set aside each month until due', 'ROUND(%s/MAX(1,ROUND((%s-{today})/30,0)),2)' % (RV('cost_reg'), RV('next_reg')), 'money')]),
    FORM('insurance_sheet', 'Insurance Renewal Sheet', 'Insurance renewal of one vehicle', 'renewals_by_veh.vehicle', F(
        ('Class', 'renewals_by_veh.class'), ('Next insurance', 'renewals_by_veh.next_ins'), ('Premium at the renewal', 'renewals_by_veh.cost_ins'), ('Insurance a year now', 'renewals_by_veh.insurance_year'), ('Colour band', 'renewals_by_veh.band')) + [
        FF('Days to the insurance date', '%s-{today}' % RV('next_ins'), 'int'), FF('Change against the premium now', '%s-%s' % (RV('cost_ins'), RV('insurance_year')), 'money'), FF('Premium a month', 'ROUND(%s/12,2)' % RV('cost_ins'), 'money')]),
    FORM('inspection_sheet', 'Inspection Sheet', 'Inspection due date and cost of one vehicle', 'renewals_by_veh.vehicle', F(
        ('Class', 'renewals_by_veh.class'), ('Next inspection', 'renewals_by_veh.next_insp'), ('Inspection cost', 'renewals_by_veh.cost_insp'), ('Last inspection', 'renewals_by_veh.last_insp'), ('Colour band', 'renewals_by_veh.band')) + [
        FF('Days to the inspection date', '%s-{today}' % RV('next_insp'), 'int'), FF('Days since the last inspection', '{today}-%s' % RV('last_insp'), 'int')]),
    FORM('towing_sheet', 'Towing Call Sheet', 'Breakdown or recovery job', 'repair_log.maint_id', F(
        ('Vehicle', 'repair_log.vehicle'), ('Class', 'repair_log.class'), ('Date', 'repair_log.date'), ('Kind', 'repair_log.kind'), ('Location', 'repair_log.location'), ('Cost', 'repair_log.cost'), ('Days off road', 'repair_log.days_off_road')) + [
        FF('Repair jobs of this vehicle, 12 months', 'COUNTIFS({range:service_log.vehicle},%s,{range:service_log.group},%s,{range:service_log.date},">="&({today}-365))+COUNTIFS({range:service_log.vehicle},%s,{range:service_log.group},%s,{range:service_log.date},">="&({today}-365))' % (R4('vehicle'), G('Repair'), R4('vehicle'), G('Towing')), 'int'),
        FF('Rental revenue lost to the days', 'ROUND(%s*%s*(%s),0)' % (R4('days_off_road'), VLK('util_12m', R4('vehicle')), ADR('%s' % VLK('class', R4('vehicle')).replace('IFERROR(', 'IFERROR(', 1).replace(',0)', ',"")', 1) if False else 'INDEX({range:repair_log.class},MATCH({pick},{range:repair_log.maint_id},0))')), 'money')]),
    FORM('out_of_service_sheet', 'Vehicle Out of Service Sheet', 'Vehicle taken off the road', 'vehicles.vehicle_id', F(
        ('Vehicle', 'vehicles.vehicle'), ('Plate', 'vehicles.plate'), ('Class', 'vehicles.class'), ('Status', 'vehicles.status'), ('Odometer, miles', 'vehicles.odometer'), ('Service check', 'vehicles.service_flag')) + [
        FF('Bookings in the next 14 days', 'COUNTIFS({range:bookings14.vehicle},%s)' % V1('vehicle'), 'int'), FF('Booked days in the next 14 days', 'SUMIFS({range:bookings14.days},{range:bookings14.vehicle},%s)' % V1('vehicle'), 'int'),
        FF('Average daily rate of the class', ADR(V1('class')), 'money'), FF('Revenue at risk, 14 days', 'SUMIFS({range:bookings14.days},{range:bookings14.vehicle},%s)*(%s)' % (V1('vehicle'), ADR(V1('class'))), 'money')]),
    FORM('vehicle_added_sheet', 'Vehicle Added Sheet', 'New vehicle for the register', 'vehicles.vehicle_id', F(
        ('Vehicle', 'vehicles.vehicle'), ('Plate', 'vehicles.plate'), ('Class', 'vehicles.class'), ('Model year', 'vehicles.year'), ('Purchase date', 'vehicles.purchase_date'), ('Purchase price', 'vehicles.purchase_price'),
        ('Financed', 'vehicles.financed'), ('Loan payment a month', 'vehicles.monthly_payment'), ('Insurance a year', 'vehicles.insurance_year'), ('Service interval, miles', 'vehicles.interval_miles')) + [
        FF('Monthly cost, payment and insurance', 'ROUND(%s+%s/12,2)' % (V1('monthly_payment'), V1('insurance_year')), 'money'), FF('First service at, miles', '%s+%s' % (V1('last_service_odometer'), V1('interval_miles')), 'int'),
        FF('Average daily rate of the class', ADR(V1('class')), 'money')]),
    FORM('vehicle_sold_sheet', 'Vehicle Sold Sheet', 'Sale or purchase of a vehicle', 'fleet_changes.change_id', F(
        ('Vehicle', 'fleet_changes.vehicle'), ('Event', 'fleet_changes.event'), ('Date', 'fleet_changes.date'), ('Amount', 'fleet_changes.amount'), ('Class', 'fleet_changes.class'), ('Purchase price', 'fleet_changes.purchase_price'),
        ('Amount against the purchase price', 'fleet_changes.vs_price'), ('Months held', 'fleet_changes.held_months')) + [
        FF('Amount as a share of the purchase price', 'IFERROR(%s/%s,0)' % (FC('amount'), FC('purchase_price')), 'pct'), FF('Days since the event', '{today}-%s' % FC('date'), 'int')]),
]
assert len(forms) == 12
# the towing form revenue field: simple and checked
forms[8]['fields'][-1] = FF('Rental revenue lost to the days', 'ROUND(%s*%s*(%s),0)' % (R4('days_off_road'), VLK('util_12m', R4('vehicle')), ADR('INDEX({range:repair_log.class},MATCH({pick},{range:repair_log.maint_id},0))')), 'money')

# ------------------------------------------------------------------ documents (12)
def DC(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
    DC('vehicle_card', 'Vehicle Record Card', 'Vehicle record card', 'vehicles.vehicle_id', [
        'Vehicle record card of {set:company}, dated {today}. Vehicle: {col:vehicles.vehicle}, plate {col:vehicles.plate}, class {col:vehicles.class}, fuel {col:vehicles.fuel}, model year {col:vehicles.year}.',
        'Purchased on {col:vehicles.purchase_date} for {col:vehicles.purchase_price}. Odometer: {col:vehicles.odometer} miles. Status: {col:vehicles.status}.',
        'Last service on {col:vehicles.last_service_date} at {col:vehicles.last_service_odometer} miles. Miles since service: {col:vehicles.miles_since}. Miles to the next service: {col:vehicles.miles_to}. Next service date: {col:vehicles.next_date}.',
        'Insurance a year: {col:vehicles.insurance_year}. Keep this card with the vehicle file. Miles are the unit used here, set your own.'], ['Manager', 'Owner']),
    DC('service_history', 'Service History', 'Workshop history of a vehicle, last 12 months', 'days_lost.vehicle', [
        'Service history of {set:company}, dated {today}. Vehicle: {col:days_lost.vehicle}, class {col:days_lost.class}.',
        'Service, inspection and tyre days in the last 12 months: {col:days_lost.service_days}. Repair and towing days: {col:days_lost.repair_days}. Workshop days in total: {col:days_lost.days}.',
        'Booked days lost at a utilisation of {col:days_lost.util} (rented days as a share of available days): {col:days_lost.booked_lost}. Revenue those days would have earned: {col:days_lost.lost_revenue}.',
        'Limit check: {col:days_lost.limit_check}. The limit is your own setting.'], ['Manager', 'Owner']),
    DC('service_due_note', 'Service Due Notice', 'Service due notice for the week', 'service_due.vehicle', [
        'Service due notice of {set:company}, dated {today}. Vehicle: {col:service_due.vehicle}, class {col:service_due.class}.',
        'Service check: {col:service_due.due_by}. Miles to the next service: {col:service_due.miles_to}. Days to the service date: {col:service_due.days_to}. Service due by: {col:service_due.due_date}.',
        'Next booking: {col:service_due.next_booking}, starting {col:service_due.next_start}. Flag: {col:service_due.flag}. Miles over the interval: {col:service_due.miles_over}.',
        'Please book a workshop slot or swap the vehicle before the next booking starts.'], ['Manager', 'Mechanic']),
    DC('job_request', 'Workshop Job Request', 'Workshop job request', 'slots.slot_id', [
        'Job request of {set:company}, dated {today}. Vehicle: {col:slots.vehicle}, class {col:slots.class}.',
        'Work: {col:slots.kind}. Drop-off on {col:slots.date} at {col:slots.drop_time}. Days needed: {col:slots.days}. The vehicle should be back on {col:slots.return_date}.',
        'Booked days this slot loses: {col:slots.lost}. Free days after the visit: {col:slots.free_after}. Slot verdict: {col:slots.verdict}.',
        'Please confirm the date and send an estimate before work starts.'], ['Manager', 'Workshop']),
    DC('estimate_request', 'Repair Estimate Request', 'Repair estimate request', 'repair_log.maint_id', [
        'Estimate request of {set:company}, dated {today}. Vehicle: {col:repair_log.vehicle}, class {col:repair_log.class}.',
        'Job: {col:repair_log.kind}, dated {col:repair_log.date}, location {col:repair_log.location}. Last cost: {col:repair_log.cost}. Days off road: {col:repair_log.days_off_road}.',
        'Please send an estimate with the parts, the labour and the days the vehicle will be off the road. Each day off the road costs us a booked day.',
        'We approve work in writing before it starts.'], ['Manager', 'Workshop']),
    DC('renewals_calendar', 'Renewals Calendar', 'Renewals calendar for one vehicle', 'renewals_by_veh.vehicle', [
        'Renewals calendar of {set:company}, dated {today}. Vehicle: {col:renewals_by_veh.vehicle}, class {col:renewals_by_veh.class}.',
        'Next registration: {col:renewals_by_veh.next_reg}, cost {col:renewals_by_veh.cost_reg}. Next insurance: {col:renewals_by_veh.next_ins}, cost {col:renewals_by_veh.cost_ins}. Next inspection: {col:renewals_by_veh.next_insp}, cost {col:renewals_by_veh.cost_insp}.',
        'Soonest renewal: {col:renewals_by_veh.soonest}, in {col:renewals_by_veh.days_soonest} days. Colour band: {col:renewals_by_veh.band}.',
        'Renewals cost for this vehicle in the next 12 months: {col:renewals_by_veh.cost_12m}.'], ['Manager', 'Owner']),
    DC('renewal_forecast', 'Renewal Cost Forecast', 'Renewal cost forecast for a month', 'renew_cost.month', [
        'Renewal cost forecast of {set:company}, dated {today}. Month: {col:renew_cost.month}.',
        'Renewals due: {col:renew_cost.due_n}. Registration: {col:renew_cost.registration}. Insurance: {col:renew_cost.insurance}. Inspection: {col:renew_cost.inspection}. Total for the month: {col:renew_cost.total}.',
        'Running total from now: {col:renew_cost.cumulative}. Set aside needed each month so cash never runs short: {col:renew_cost.avg_to_date}. Your monthly set-aside: {set:set_aside_month}.',
        'Confirm the set-aside with your adviser.'], ['Manager', 'Bookkeeper']),
    DC('broker_request', 'Insurance Renewal Request', 'Insurance renewal request for your broker', 'renewals_by_veh.vehicle', [
        'Renewal request of {set:company}, dated {today}. Vehicle: {col:renewals_by_veh.vehicle}, class {col:renewals_by_veh.class}.',
        'The insurance renewal is due on {col:renewals_by_veh.next_ins}. The premium we pay now is {col:renewals_by_veh.insurance_year} a year. The last renewal quote was {col:renewals_by_veh.cost_ins}.',
        'Please send a quote for the renewal with the cover options and the amount a renter pays in a claim. Check your insurance terms before you decide.',
        'We compare the quote with last year and with the other vehicles of the class.'], ['Manager', 'Insurance broker']),
    DC('out_of_service_notice', 'Out of Service Notice', 'Vehicle out of service notice', 'vehicles.vehicle_id', [
        'Out of service notice of {set:company}, dated {today}. Vehicle: {col:vehicles.vehicle}, plate {col:vehicles.plate}, class {col:vehicles.class}.',
        'The vehicle is taken off the road. Status: {col:vehicles.status}. Odometer: {col:vehicles.odometer} miles. Service check: {col:vehicles.service_flag}.',
        'Do not offer this vehicle for new bookings until it is back on the register as Active. Move any booking that starts before then.',
        'Record the date it returns in the Service Log.'], ['Manager', 'Staff member']),
    DC('tyre_schedule', 'Tyre Change Schedule', 'Tyre change schedule for a vehicle', 'tyres.vehicle', [
        'Tyre schedule of {set:company}, dated {today}. Vehicle: {col:tyres.vehicle}, class {col:tyres.class}.',
        'Last tyre set: {col:tyres.tyre_date} at {col:tyres.odo_then} miles. Odometer now: {col:tyres.odometer}. Miles since: {col:tyres.miles_since}. Miles to the next set: {col:tyres.next_tyre_miles}.',
        'Tyres due on about {col:tyres.due_on}. Tyre check: {col:tyres.tyre_flag}. Next season change: {col:tyres.season_date}.',
        'Sets due before the season change: {col:tyres.sets_due}. Order them early.'], ['Manager', 'Tyre supplier']),
    DC('fleet_list', 'Fleet List', 'Vehicle line for your lender or broker', 'vehicles.vehicle_id', [
        'Fleet list line of {set:company}, dated {today}. Vehicle: {col:vehicles.vehicle}, plate {col:vehicles.plate}, class {col:vehicles.class}, model year {col:vehicles.year}.',
        'Purchased on {col:vehicles.purchase_date} for {col:vehicles.purchase_price}. Resale estimate: {col:vehicles.resale_estimate}. Odometer: {col:vehicles.odometer} miles. Status: {col:vehicles.status}.',
        'Loan payment a month: {col:vehicles.monthly_payment}. Insurance a year: {col:vehicles.insurance_year}.',
        'Values are our own estimates and help you keep track.'], ['Owner', 'Lender']),
    DC('handover_to_buyer', 'Vehicle Handover to a Buyer', 'Vehicle handover to a buyer', 'vehicles.vehicle_id', [
        'Handover note of {set:company}, dated {today}. Vehicle: {col:vehicles.vehicle}, plate {col:vehicles.plate}, class {col:vehicles.class}, model year {col:vehicles.year}.',
        'Odometer at handover: {col:vehicles.odometer} miles. Last service on {col:vehicles.last_service_date} at {col:vehicles.last_service_odometer} miles. Purchased on {col:vehicles.purchase_date}.',
        'Status and dates only: this note records the vehicle and the dates. Check your local rules for registration transfer, records and any cover end date.',
        'Both parties sign to confirm the odometer and the date.'], ['Seller', 'Buyer']),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
def CK(k, title, table, start, steps): return CHK(k, title, table, start, steps)
checklists = [
    CK('add_vehicle_chk', 'Adding a Vehicle Steps', 'vehicles', 'vehicles.purchase_date', [('Add the vehicle to the Vehicle Register', 0), ('Fill plate, class, odometer and service interval', 0), ('Add registration, insurance and inspection dates', 0), ('Tell your insurance broker', 1), ('Add it to the rate card and the booking calendar', 2), ('Book the first service at the interval', 3), ('Check the register for gaps', 7)]),
    CK('weekly_service_chk', 'Weekly Service Due Check Steps', 'wk_cal', 'wk_cal.date', [('Open the Service Due List', 0), ('Pull overdue cars from bookings this week', 0), ('Book workshop slots in the Workshop Slots sheet', 0), ('Tell the mechanic and the driver', 1), ('Check the Workshop Calendar for busy days', 1), ('Update the register after each visit', 5)]),
    CK('book_slot_chk', 'Booking a Workshop Slot Steps', 'slots', 'slots.date', [('Add candidate dates for the vehicle', -7), ('Pick the slot that loses the fewest booked days', -5), ('Confirm the slot with the workshop', -4), ('Move or swap any booking in the way', -3), ('Plan the drop-off and the pick-up', -1), ('Drop the vehicle off', 0), ('Collect it and update the log', 1)]),
    CK('back_workshop_chk', 'Car Back from Workshop Steps', 'service_log', 'service_log.date', [('Check the invoice against the estimate', 0), ('Record the visit in the Service Log', 0), ('Update odometer and last service date', 0), ('Ask for a clean and a check by the detailer', 0), ('Put the vehicle back on the booking calendar', 1)]),
    CK('renewals_review_chk', 'Monthly Renewals Review Steps', 'renew_cost', 'renew_cost.month', [('Open the Renewals Dashboard', 0), ('Check overdue and due within 30 days', 0), ('Check the Renewal Cash Plan against your set-aside', 1), ('Ask the broker for quotes on insurance renewals', 2), ('Send the cost to the bookkeeper', 3)]),
    CK('registration_chk', 'Registration Renewal Steps', 'renewals', 'renewals.due_date', [('Check the renewal date and the cost', -30), ('Check your local rules for what you need', -28), ('Pay the renewal', -14), ('Record the date renewed on the Renewals sheet', -13), ('Keep the new registration with the vehicle file', -10)]),
    CK('insurance_chk', 'Insurance Renewal Steps', 'renewals', 'renewals.due_date', [('Ask the broker for a quote', -45), ('Compare with last year in Insurance Renewal Compare', -35), ('Check your insurance terms and cover options', -30), ('Choose and pay the renewal', -14), ('Record the date renewed and the cost', -13)]),
    CK('inspection_chk', 'Inspection Due Steps', 'renewals', 'renewals.due_date', [('Check the days the vehicle is free', -21), ('Book the inspection slot', -14), ('Move any booking in the way', -10), ('Take the vehicle to the inspection', -3), ('Record the result and the cost', 0)]),
    CK('tyre_season_chk', 'Tyre Season Change Steps', 'wk_cal', 'wk_cal.date', [('Run the Tyre Planner for sets due', -28), ('Order the sets', -21), ('Book the fitting days', -14), ('Plan the cars off the road, a few each day', -7), ('Fit the tyres', 0), ('Update the Tyre Dates sheet', 1)]),
    CK('breakdown_chk', 'Breakdown Response Steps', 'repair_log', 'repair_log.date', [('Make sure the renter is safe', 0), ('Call the towing service', 0), ('Send a replacement car if one is free', 0), ('Record the job in the Repair Log', 1), ('Check the cost with the Breakdown Cost Check', 7), ('Review repeat breakdowns of the vehicle', 30)]),
    CK('sell_vehicle_chk', 'Selling a Vehicle Steps', 'fleet_changes', 'fleet_changes.date', [('Check Replace or Sell figures in the finance part', -30), ('Ask your lender for a payoff figure', -21), ('Remove the vehicle from future bookings', -14), ('Hand over the vehicle with status and dates only', 0), ('Tell the broker to remove it', 1), ('Mark it Sold on the register', 1)]),
    CK('one_car_chk', 'One-Car Host Car Care Steps', 'vehicles', 'vehicles.purchase_date', [('Check tyres, lights and fluids each month', 30), ('Service at the interval in miles or months', 180), ('Renew registration and insurance on time', 335), ('Book the inspection when due', 350), ('Note every cost in the Service Log', 365)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def NM(role): return first_name(D.TEAM[role]['name'])
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
MECH, TYRE_, BODY, TOW, BRK, LEND, OWNR, MGRN, DRV, DET, BKP, ACC = (NM(r) for r in ('Mechanic', 'Tyre supplier', 'Body repair shop', 'Towing service', 'Insurance broker', 'Lender', 'Owner-operator', 'Manager', 'Delivery driver', 'Detailer', 'Bookkeeper', 'Accountant'))
messages = [
    M('mech_book', 'Mechanic: please book a service', 'slots', 'slots.mechanic_phone', 'Hello %s, please book {vehicle} for a {kind} on {date}. {business}' % MECH),
    M('mech_drop', 'Mechanic: ready to drop off', 'slots', 'slots.mechanic_phone', 'Hello %s, {vehicle} is ready to drop off at {drop_time}. {business}' % MECH),
    M('mech_estimate', 'Mechanic: please send the estimate', 'repair_log', 'repair_log.mechanic_phone', 'Hello %s, please send the estimate for {vehicle}. {business}' % MECH),
    M('mech_ready', 'Mechanic: is the vehicle ready', 'slots', 'slots.mechanic_phone', 'Hello %s, is {vehicle} ready for collection? {business}' % MECH),
    M('mech_invoice', 'Mechanic: please confirm the invoice', 'repair_log', 'repair_log.mechanic_phone', 'Hello %s, the invoice for {vehicle} is {cost}, please confirm. {business}' % MECH),
    M('mech_gap', 'Mechanic: we have a gap', 'slots', 'slots.mechanic_phone', 'Hello %s, we have a {days}-day gap on {date}, can you fit {vehicle}? {business}' % MECH),
    M('tyre_quote', 'Tyre supplier: please quote a set', 'tyres', 'tyres.tyre_phone', 'Hello %s, please quote a set for {vehicle}, {class}. {business}' % TYRE_),
    M('tyre_fit', 'Tyre supplier: please book the fitting', 'tyres', 'tyres.tyre_phone', 'Hello %s, please book the fitting for {vehicle} on {due_on}. {business}' % TYRE_),
    M('tyre_sets', 'Tyre supplier: sets before the change', 'tyres', 'tyres.tyre_phone', 'Hello %s, we need {sets_due} sets before the season change on {season_date}. {business}' % TYRE_),
    M('body_inspect', 'Body repair shop: please inspect', 'repair_log', 'repair_log.body_phone', 'Hello %s, please inspect {vehicle}, claim {claim_id}. {business}' % BODY),
    M('body_ready', 'Body repair shop: when is it ready', 'repair_log', 'repair_log.body_phone', 'Hello %s, when is {vehicle} ready? {business}' % BODY),
    M('tow_recover', 'Towing service: vehicle needs recovery', 'repair_log', 'repair_log.towing_phone', 'Hello %s, {vehicle} needs recovery from {location}. {business}' % TOW),
    M('tow_invoice', 'Towing service: please send the invoice', 'repair_log', 'repair_log.towing_phone', 'Hello %s, thank you, please send the invoice for {vehicle}. {business}' % TOW),
    M('brk_quote', 'Insurance broker: renewal quote', 'renewals', 'renewals.broker_phone', 'Hello %s, the renewal for {vehicle} is due on {due_date}, please send a quote. {business}' % BRK),
    M('brk_premium', 'Insurance broker: confirm the premium', 'renewals', 'renewals.broker_phone', 'Hello %s, please confirm the premium of {cost} for {vehicle}. {business}' % BRK),
    M('brk_added', 'Insurance broker: vehicle added', 'vehicles', 'vehicles.broker_phone', 'Hello %s, the fleet list changed, {vehicle} was added. {business}' % BRK),
    M('brk_sold', 'Insurance broker: vehicle sold', 'vehicles', 'vehicles.broker_phone', 'Hello %s, {vehicle} was sold on {sold_date}, please remove it. {business}' % BRK),
    M('lend_register', 'Lender: the register figures', 'vehicles', 'vehicles.lender_phone', 'Hello %s, the register shows {vehicle} with {odometer} miles. {business}' % LEND),
    M('lend_payoff', 'Lender: payoff figure', 'vehicles', 'vehicles.lender_phone', 'Hello %s, {vehicle} is sold, please send a payoff figure. {business}' % LEND),
    M('own_overdue', 'Owner: services overdue', 'service_due', 'service_due.owner_phone', 'Hello %s, {overdue_n} services are overdue, {booked_n} are booked this week. {business}' % OWNR),
    M('own_renewals', 'Owner: renewals due in 30 days', 'renew_cost', 'renew_cost.owner_phone', 'Hello %s, renewals due in 30 days cost {amount30}. {business}' % OWNR),
    M('own_cost1000', 'Owner: a vehicle costs too much', 'cost1000', 'cost1000.owner_phone', 'Hello %s, {vehicle} costs {cost_1000} per 1,000 miles, review it. {business}' % OWNR),
    M('own_days', 'Owner: workshop days of a vehicle', 'days_lost', 'days_lost.owner_phone', 'Hello %s, {vehicle} had {days} days in the workshop this year. {business}' % OWNR),
    M('mgr_move', 'Manager: please move a booking', 'bookings14', 'bookings14.manager_phone', 'Hello %s, please move booking {booking_id}, {vehicle} needs service. {business}' % MGRN),
    M('mgr_back', 'Manager: vehicle back from the workshop', 'service_due', 'service_due.manager_phone', 'Hello %s, {vehicle} is back from the workshop. {business}' % MGRN),
    M('mgr_block', 'Manager: block a vehicle', 'slots', 'slots.manager_phone', 'Hello %s, block {vehicle} for {days} days from {date}. {business}' % MGRN),
    M('mgr_reg', 'Manager: registration due', 'renewals', 'renewals.manager_phone', 'Hello %s, the renewal for {vehicle} is due on {due_date}. {business}' % MGRN),
    M('drv_take', 'Driver: take the vehicle to the workshop', 'slots', 'slots.driver_phone', 'Hello %s, take {vehicle} to the workshop at {drop_time}. {business}' % DRV),
    M('drv_collect', 'Driver: collect the vehicle', 'slots', 'slots.driver_phone', 'Hello %s, collect {vehicle} from the workshop. {business}' % DRV),
    M('det_prepare', 'Detailer: vehicle back from service', 'slots', 'slots.detailer_phone', 'Hello %s, {vehicle} is back from service, please prepare it. {business}' % DET),
    M('bkp_renewals', 'Bookkeeper: renewal costs of a month', 'renew_cost', 'renew_cost.bookkeeper_phone', 'Hello %s, renewal costs due in {month} are {total}. {business}' % BKP),
    M('acc_repairs', 'Accountant: repairs and tyres', 'cost1000', 'cost1000.accountant_phone', 'Hello %s, repairs and tyres for {vehicle} for {year} are {repairs_tyres}. {business}' % ACC),
    M('rent_swap', 'Renter: we need to swap your car', 'bookings14', 'bookings14.phone', 'Hello {renter}, we need to swap your car, {vehicle} needs a service. {business}'),
    M('rent_alt', 'Renter: your replacement car', 'bookings14', 'bookings14.phone', 'Hello {renter}, your replacement car is {vehicle_alt}. {business}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
SV = lambda col, extra='': 'SUMIFS({range:service_log.%s}%s)' % (col, extra)
def SLC(*conds): return ','.join('{range:service_log.%s},%s' % c for c in conds)
ACTN = '{range:vehicles.vehicle_id},"<>",{range:vehicles.status},"<>"&%s' % SOLD
LOG12 = '{range:service_log.date},">="&({today}-365)'
FLEET = 'COUNTIFS(%s)' % ACTN
kpis = [
    KPI('Vehicles in the fleet', FLEET, 'int'),
    KPI('Vehicles in service now', 'COUNTIFS({range:vehicles.status},%s)' % ACT, 'int'),
    KPI('Vehicles in the workshop now', 'COUNTIFS({range:vehicles.status},%s)' % WSH, 'int'),
    KPI('Vehicles sold last 12 months', 'COUNTIFS({range:vehicles.sold_date},">="&({today}-365))', 'int'),
    KPI('Vehicles bought last 12 months', 'COUNTIFS({range:vehicles.purchase_date},">="&({today}-365),{range:vehicles.vehicle_id},"<>")', 'int'),
    KPI('Average fleet age in months', 'IFERROR(AVERAGEIFS({range:vehicles.age_months},%s),0)' % ACTN, 'int'),
    KPI('Average odometer, miles', 'IFERROR(AVERAGEIFS({range:vehicles.odometer},%s),0)' % ACTN, 'int'),
    KPI('Services overdue now', 'COUNTIFS({range:service_due.due_by},%s)' % ca('Service now'), 'int'),
    KPI('Services due in the next 30 days', 'COUNTIFS({range:service_due.due_date},">="&{today},{range:service_due.due_date},"<="&({today}+30),{range:service_due.due_by},"<>"&%s)' % ca('Service now'), 'int'),
    KPI('Overdue cars booked this week', 'COUNTIFS({range:service_due.flag},%s)' % ca('Pull from booking'), 'int'),
    KPI('Largest miles over the interval', 'MAX({range:service_due.miles_over})', 'int'),
    KPI('Services done this month', 'COUNTIFS({range:service_log.month},DATE(YEAR({today}),MONTH({today}),1),{range:service_log.group},%s)' % G('Service'), 'int'),
    KPI('Service cost this month', 'SUMIFS({range:service_log.cost},{range:service_log.month},DATE(YEAR({today}),MONTH({today}),1),{range:service_log.group},%s)' % G('Service'), 'money'),
    KPI('Repair cost this month', 'SUMIFS({range:repair_log.cost},{range:repair_log.date},">="&DATE(YEAR({today}),MONTH({today}),1))', 'money'),
    KPI('Tyre cost last 12 months', 'SUMIFS({range:service_log.cost},%s,{range:service_log.group},%s)' % (LOG12, G('Tyres')), 'money'),
    KPI('Maintenance cost last 12 months', 'SUMIFS({range:service_log.cost},%s)' % LOG12, 'money'),
    KPI('Maintenance per vehicle, 12 months', 'IFERROR(SUMIFS({range:service_log.cost},%s)/%s,0)' % (LOG12, FLEET), 'money'),
    KPI('Cost per 1,000 miles, 12 months', 'IFERROR(SUM({range:cost1000.maint_cost})/SUM({range:cost1000.miles_12m})*1000,0)', 'money'),
    KPI('Workshop days last 90 days', 'SUMIFS({range:service_log.days_off_road},{range:service_log.date},">="&({today}-90))', 'int'),
    KPI('Booked days lost, last 90 days', 'SUMIFS({range:service_log.lost_days},{range:service_log.date},">="&({today}-90))', 'num'),
    KPI('Breakdowns last 12 months', 'COUNTIFS({range:service_log.kind},%s,%s)' % (tok('mkind', 'Towing'), LOG12), 'int'),
    KPI('Towing cost last 12 months', 'SUMIFS({range:service_log.cost},{range:service_log.kind},%s,%s)' % (tok('mkind', 'Towing'), LOG12), 'money'),
    KPI('Renewals overdue', 'COUNTIFS({range:renewals.status},%s,{range:renewals.due_date},"<"&{today})' % UP, 'int'),
    KPI('Renewals due in 30 days', 'COUNTIFS({range:renewals.status},%s,{range:renewals.due_date},">="&{today},{range:renewals.due_date},"<="&({today}+30))' % UP, 'int'),
    KPI('Renewals due in 60 days', 'COUNTIFS({range:renewals.status},%s,{range:renewals.due_date},">="&{today},{range:renewals.due_date},"<="&({today}+60))' % UP, 'int'),
    KPI('Cost of renewals next 12 months', 'SUMIFS({range:renewals.cost},{range:renewals.status},%s,{range:renewals.due_date},">="&{today},{range:renewals.due_date},"<="&({today}+365))' % UP, 'money'),
    KPI('Cost of renewals next 90 days', 'SUMIFS({range:renewals.cost},{range:renewals.status},%s,{range:renewals.due_date},">="&{today},{range:renewals.due_date},"<="&({today}+90))' % UP, 'money'),
    KPI('Insurance cost per vehicle, a year', 'IFERROR(AVERAGEIFS({range:vehicles.insurance_year},%s),0)' % ACTN, 'money'),
    KPI('Vehicles with a gap in the register', 'COUNTIFS({range:vehicles.gaps},">0")', 'int'),
    KPI('Next renewal days away', 'IFERROR(INT(SMALL({range:renewals.sort_key},1))-{today},0)', 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Fleet and Service Dashboard", "kpis": kpis,
    "monthly": {"title": "Maintenance, repair and inspection cost", "date": "service_log.month", "series": [
        {"label": "Maintenance cost", "sum": "service_log.cost", "date": "service_log.month"}, {"label": "Repair log cost", "sum": "repair_log.cost", "date": "repair_log.date"},
        {"label": "Inspection cost", "sum": "inspections.cost", "date": "inspections.date"}]},
    "breakdowns": [{"title": "Maintenance cost by kind", "by": "service_log.kind", "value": "service_log.cost", "agg": "sum"}, {"title": "Vehicles by class", "by": "vehicles.class", "value": "vehicles.odometer", "agg": "count"},
                   {"title": "Workshop days by vendor", "by": "service_log.vendor", "value": "service_log.days_off_road", "agg": "sum"}, {"title": "Renewals by kind", "by": "renewals.kind", "value": "renewals.cost", "agg": "count"}]}
SVC_G = [('group', '=', G('Service'))]
insights = {"filters": [{"label": "Vehicle class", "list": "class"}, {"label": "Service kind", "list": "mkind"}, {"label": "Workshop vendor", "list": "vendor"}],
    "gauges": [
        {"title": "Services done on time", "num": AGG('count', 'service_log', where=SVC_G + [('on_time', '=', YES)]), "den": AGG('count', 'service_log', where=SVC_G)},
        {"title": "Vehicles with no renewal overdue", "num": AGG('count', 'renewals_by_veh', where=[('overdue_n', '=', 0)]), "den": AGG('count', 'renewals_by_veh')},
        {"title": "Maintenance cost against your budget", "num": AGG('sum', 'cost1000', 'cost1000.maint_cost'), "den": AGG('sum', 'cost1000', 'cost1000.budget')},
        {"title": "Workshop days against your limit", "num": AGG('sum', 'days_lost', 'days_lost.days'), "den": AGG('sum', 'days_lost', 'days_lost.limit_days')},
        {"title": "Register completeness", "num": AGG('count', 'vehicles', where=[('gaps', '=', 0)]), "den": AGG('count', 'vehicles')},
        {"title": "Renewals paid before the due date", "num": AGG('count', 'renewals', where=[('paid_check', '=', ca('Paid on time'))]), "den": AGG('count', 'renewals', where=[('status', '=', DONE)])}],
    "charts": [
        CHART('Service cost per month', 'column', 'month', [AGG('sum', 'service_log', 'service_log.cost', date='service_log.date', where=SVC_G, label='Service cost')]),
        CHART('Maintenance cost per month', 'column', 'month', [AGG('sum', 'service_log', 'service_log.cost', date='service_log.date', label='Maintenance cost')]),
        CHART('Maintenance cost by kind', 'bar', 'service_log.kind', [AGG('sum', 'service_log', 'service_log.cost', label='Cost')]),
        CHART('Maintenance cost by class', 'bar', 'service_log.class', [AGG('sum', 'service_log', 'service_log.cost', label='Cost')]),
        CHART('Maintenance cost by vendor', 'bar', 'service_log.vendor', [AGG('sum', 'service_log', 'service_log.cost', label='Cost')]),
        CHART('Workshop days per month', 'column', 'month', [AGG('sum', 'service_log', 'service_log.days_off_road', date='service_log.date', label='Workshop days')]),
        CHART('Workshop days by kind', 'bar', 'service_log.kind', [AGG('sum', 'service_log', 'service_log.days_off_road', label='Workshop days')]),
        CHART('Services by kind', 'bar', 'service_log.kind', [AGG('count', 'service_log', where=SVC_G, label='Services')]),
        CHART('Repairs per month', 'column', 'month', [AGG('count', 'service_log', date='service_log.date', where=[('group', '=', G('Repair'))], label='Repairs')]),
        CHART('Repair cost by class', 'bar', 'service_log.class', [AGG('sum', 'service_log', 'service_log.cost', where=[('group', '=', G('Repair'))], label='Repair cost')]),
        CHART('Tyre sets per month', 'column', 'month', [AGG('count', 'service_log', date='service_log.date', where=[('kind', '=', tok('mkind', 'Tyre set'))], label='Tyre sets')]),
        CHART('Towing cost per month', 'column', 'month', [AGG('sum', 'service_log', 'service_log.cost', date='service_log.date', where=[('kind', '=', tok('mkind', 'Towing'))], label='Towing cost')]),
        CHART('Renewals by kind', 'bar', 'renewals.kind', [AGG('count', 'renewals', label='Renewals')]),
        CHART('Renewals by status', 'bar', 'renewals.status', [AGG('count', 'renewals', label='Renewals')]),
        CHART('Renewal cost by month ahead', 'column', 'renew_cost.slot', [AGG('sum', 'renew_cost', 'renew_cost.total', label='Renewal cost')]),
        CHART('Renewals due by month ahead', 'column', 'renew_cost.slot', [AGG('sum', 'renew_cost', 'renew_cost.due_n', label='Renewals due')]),
        CHART('Vehicles by class', 'bar', 'vehicles.class', [AGG('count', 'vehicles', where=[('status', '<>', SOLD)], label='Vehicles')]),
        CHART('Vehicles by status', 'bar', 'vehicles.status', [AGG('count', 'vehicles', label='Vehicles')]),
        CHART('Vehicles by fuel', 'bar', 'vehicles.fuel', [AGG('count', 'vehicles', label='Vehicles')]),
        CHART('Vehicles by model year', 'bar', 'vehicles.year', [AGG('count', 'vehicles', label='Vehicles')]),
        CHART('Purchases per month', 'column', 'month', [AGG('count', 'fleet_changes', date='fleet_changes.date', where=[('event', '=', tok('fevent', 'Bought'))], label='Vehicles bought')]),
        CHART('Sales per month', 'column', 'month', [AGG('count', 'fleet_changes', date='fleet_changes.date', where=[('event', '=', tok('fevent', 'Sold'))], label='Vehicles sold')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Service due planner", "why": "service falls due by miles or months, whichever comes first, with the date the miles run out at the car's own pace", "where": "Service Due Planner"},
    {"name": "Overdue cars booked this week", "why": "a car past its interval with a booking this week is named first, with the booking to move and a swap car of the same class", "where": "Overdue Cars Booked"},
    {"name": "Workshop slot planner", "why": "candidate dates are scored by the booked days each one loses, so the slot that costs the fewest rentals is marked", "where": "Workshop Slot Planner"},
    {"name": "Renewals dashboard", "why": "registration, insurance and inspection dates across the fleet in one sorted list with overdue, 30-day and 60-day colours", "where": "Renewals Dashboard"},
    {"name": "Renewal cash plan", "why": "the cost of renewals over the next 12 months turned into the amount to set aside each month, so a big month never surprises you", "where": "Renewal Cash Plan"},
    {"name": "Repair cost trend", "why": "repair and tyre cost per month and per 1,000 miles against the vehicle's own last 12 months, with a rising or steady flag", "where": "Repair Cost Trend"},
    {"name": "Cost per 1,000 miles ranking", "why": "vehicles ranked by maintenance cost per 1,000 miles against their class average so the money-eater is named", "where": "Cost per 1,000 Miles Ranking"},
    {"name": "Rental days lost to service", "why": "workshop days turned into booked days and revenue lost at the class average daily rate", "where": "Rental Days Lost"},
    {"name": "Downtime cost", "why": "workshop days times utilisation and daily rate compared with the repair bill itself", "where": "Downtime Cost"},
    {"name": "Next-service forecast", "why": "services due each week for 12 weeks in Base, Best and Worst cases, so you book the workshop ahead of the peak", "where": "Next-Service Forecast"}]
competitors = [
    {"what": "subscription rental-management software", "lacks": "charges per vehicle or per booking and keeps service and renewals in a module you cannot test, with no workshop slot that counts the booked days it loses"},
    {"what": "generic booking calendar template", "lacks": "shows the dates but knows nothing of service intervals in miles, overdue cars with a booking this week or renewal colours"},
    {"what": "single-sheet vehicle expense log", "lacks": "adds up costs but gives no cost per 1,000 miles, no class average and no rising-cost flag"},
    {"what": "budget-model template", "lacks": "plans yearly cash but has no renewal calendar by vehicle and no monthly set-aside for registration, insurance and inspection"},
    {"what": "paper service book", "lacks": "records visits but never warns that a booked car is past its interval or which workshop slot loses the fewest rentals"}]
guide = [
    'Open Start and type your business name, the service warning miles and days, your workshop days limit, the daily rate of each class and the date of the next tyre season change in the yellow cells.',
    'Fill the Vehicle Register with one row per vehicle: class, purchase, odometer, last service, service interval and insurance. Miles are the demo unit, set your own.',
    'Record every workshop visit in the Service Log and every repair in the Repair Log; the Service Due List shows miles and days to the next service by itself.',
    'Add rental bookings of the next 14 days to Bookings Next 14 Days so the list can flag an overdue car that is booked this week (utilisation means rented days as a share of available days).',
    'Add candidate dates in Workshop Slots; each one shows the booked days it loses and the best slot is marked.',
    'Keep Renewals up to date: registration, insurance and inspection, with due date, cost and the date renewed.',
    'Read Renewal Cost by Month for the next 12 months and set aside the amount the Renewal Cash Plan names.',
    'Check Cost per 1,000 Miles, Repair Cost by Vehicle and Rental Days Lost every month to find the vehicle that costs most.',
    'Record tyre sets in Tyre Dates and run the Tyre Planner before the season change.',
    'Log bought and sold vehicles in Fleet Changes and use the Vehicle Register Check to fill the gaps.',
    f'Use the {len(tools)} calculators, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Fleet and Service Dashboard and the Charts every week. A one-car host uses the same sheets with one vehicle as a car-care and renewals diary.',
    'To replace the demo data, clear the yellow cells of each sheet and type your own; no macros, works in Excel and Google Sheets, flat price with no per-vehicle fee, your data stays with you.']
listing = {"title": "Car Rental Fleet Register, Service and Renewals Excel Template: Service Due, Workshop Slots, Renewals Calendar, Cost per 1,000 Miles",
    "headline": "Know which car needs service, which renewal is due and what each vehicle costs",
    "tags": ["car rental", "fleet register", "vehicle service log", "service due", "renewals calendar", "excel template", "fleet maintenance", "workshop planner", "car hire", "vehicle tracker", "tyre planner", "car sharing host", "rental business"],
    "description": ("Keep the cars of a small car or van rental business on the road in one Excel workbook. Built for an owner-operator and a manager who need to know which vehicle is due for service, which registration, insurance or inspection falls due next, and what each vehicle costs to keep.\n\n"
        "The Vehicle Register holds one row per vehicle with class, purchase or financing, odometer, last service and insurance; miles since service, miles to the next service and the next service date fill in. The Service Due List flags every car by miles or months, whichever comes first, and marks a car that is past its interval and booked this week. "
        "Workshop Slots scores candidate dates by the booked days each one loses, so you book the slot that costs the fewest rentals. Renewals and Renewals by Vehicle show registration, insurance and inspection dates with overdue, 30-day and 60-day colours, and Renewal Cost by Month shows the next 12 months of cost for cash planning.\n\n"
        "Cost per 1,000 Miles ranks vehicles against their class average with a rising-cost flag; Rental Days Lost turns workshop days into booked days and revenue lost; Tyre Dates, Inspection Log, Repair Log, Fleet Changes and Workshop Vendors round out the sheets. "
        f"{len(tools)} calculators cover the service planner, the overdue-while-booked list, the slot planner, the renewals dashboard, the renewal cash plan, repair trend, tyre planner, cost ranking, register check, insurance compare, inspection planner, breakdown cost, interval check, vendor scorecard, backlog burn-down, 12-week forecast and downtime cost. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the mechanic, tyre supplier, body repair shop, towing service, broker, lender, owner, manager, driver, detailer, bookkeeper, accountant and renters.\n\n"
        "This is part five of the Car Rental Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Renters appear by first name only. Distances are in miles, the demo unit, set your own; amounts are plain numbers. It helps you keep track and does not promise results. Check your local rules for registration, inspection and insurance terms."),
    "features": ["Service due by miles or months, whichever first", "Overdue cars with a booking this week", "Workshop slot that loses the fewest booked days", "Renewals calendar with 30 and 60 day colours", "12-month renewal cost for cash planning",
                 "Cost per 1,000 miles against the class average", "Rental days lost to service and repair", f"{len(tools)} calculators for fleet decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p5', slug='car-rental-fleet', profession='Car Rental Business', name='Fleet Register, Service and Renewals',
         tagline='Know which car needs service, which renewal is due and what each vehicle costs', price_usd=29,
         colors={"primary": "#1D3557", "accent": "#E63946"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Fleet register, service and renewals"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cr5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
