"""Car Rental Business suite - part 6: Turnaround, Delivery Runs and Staff."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr6_lists import *
from cr6_tables import settings, tables
from cr6_tools import tools
import cr6_data as D

SUITE = 'fx-20261115-car-rental'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def R(t, c): return '{range:%s.%s}' % (t, c)

# first demo row of a table is the record a demo form or document shows: make it a complete one
def first(tkey, pred):
    for t in tables:
        if t['key'] == tkey:
            i = next(i for i, r in enumerate(t['demo']) if pred(r)); t['demo'].insert(0, t['demo'].pop(i))
first('turnaround', lambda r: r['turn_id'] == D.TIGHT_ID)
first('pay', lambda r: r.get('hours', 0) > 0)
first('tasks_role', lambda r: True)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('turnaround_sheet', 'Turnaround Sheet', 'Turnaround of one returned car', 'turnaround.turn_id', F(
        ('Booking', 'turnaround.booking_id'), ('Vehicle', 'turnaround.vehicle'), ('Class', 'turnaround.class'), ('Return date', 'turnaround.return_date'), ('Returned at', 'turnaround.returned_time'),
        ('Detailer', 'turnaround.cleaner'), ('Clean start', 'turnaround.clean_start'), ('Clean end', 'turnaround.clean_end'), ('Next pickup', 'turnaround.next_pickup'), ('Pickup time', 'turnaround.next_pickup_time'),
        ('Slack minutes', 'turnaround.slack_minutes'), ('Verdict', 'turnaround.verdict')) + [
        FF('Minutes from return to ready', LK('turnaround', 'turn_id', 'turn_minutes'), 'int'), FF('Buffer you set, minutes', '{set:buffer_min}', 'int'),
        FF('Minutes over the buffer', 'MAX(0,%s-{set:buffer_min})' % LK('turnaround', 'turn_id', 'turn_minutes'), 'int')]),
    FORM('cleaning_job_sheet', 'Cleaning Job Sheet', 'Cleaning job of one car', 'turnaround.turn_id', F(
        ('Vehicle', 'turnaround.vehicle'), ('Class', 'turnaround.class'), ('Detailer', 'turnaround.cleaner'), ('Clean date', 'turnaround.clean_date'), ('Clean minutes', 'turnaround.clean_minutes'),
        ('Clean cost', 'turnaround.clean_cost'), ('Very dirty', 'turnaround.dirty')) + [
        FF('Average minutes of the class', 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (R('turnaround', 'clean_minutes'), R('turnaround', 'class'), LK('turnaround', 'turn_id', 'class')), 'num'),
        FF('Minutes above the class average', '%s-IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (LK('turnaround', 'turn_id', 'clean_minutes'), R('turnaround', 'clean_minutes'), R('turnaround', 'class'), LK('turnaround', 'turn_id', 'class')), 'num'),
        FF('Cars cleaned by the detailer that day', LK('turnaround', 'turn_id', 'cars_today'), 'int'), FF('Cleaning fee for a very dirty car', '{set:cleaning_fee}', 'money')]),
    FORM('delivery_run_sheet', 'Delivery Run Sheet', 'Delivery run of one booking', 'delivery_runs.run_id', F(
        ('Date', 'delivery_runs.date'), ('Booking', 'delivery_runs.booking_id'), ('Vehicle', 'delivery_runs.vehicle'), ('Renter', 'delivery_runs.renter'), ('Zone', 'delivery_runs.location'),
        ('Driver', 'delivery_runs.driver'), ('Start', 'delivery_runs.start_time'), ('End', 'delivery_runs.end_time'), ('Minutes', 'delivery_runs.minutes'), ('Miles', 'delivery_runs.miles')) + [
        FF('Fee charged', LK('delivery_runs', 'run_id', 'fee_charged'), 'money'), FF('Driver cost', LK('delivery_runs', 'run_id', 'driver_cost'), 'money'), FF('Profit of the run', LK('delivery_runs', 'run_id', 'profit'), 'money'),
        FF('Zone profit per run, last days', LK('delivery_runs', 'run_id', 'zone_profit'), 'money')]),
    FORM('collection_run_sheet', 'Collection Run Sheet', 'Collection run of one booking', 'delivery_runs.run_id', F(
        ('Date', 'delivery_runs.date'), ('Booking', 'delivery_runs.booking_id'), ('Vehicle', 'delivery_runs.vehicle'), ('Zone', 'delivery_runs.location'), ('Driver', 'delivery_runs.driver'), ('Start', 'delivery_runs.start_time'),
        ('Status', 'delivery_runs.status')) + [
        FF('Runs of the driver that day', LK('delivery_runs', 'run_id', 'runs_day'), 'int'), FF('Runs that clash for the driver', 'MAX(0,%s)' % LK('delivery_runs', 'run_id', 'clash'), 'int'),
        FF('Minutes late, if any', LK('delivery_runs', 'run_id', 'delay_min'), 'int'), FF('Fees of this zone against cost', LK('delivery_runs', 'run_id', 'zone_cover'), 'pct')]),
    FORM('shift_sheet', 'Shift Sheet', 'One shift of a staff member', 'shifts.shift_id', F(
        ('Date', 'shifts.date'), ('Weekday', 'shifts.weekday'), ('Staff member', 'shifts.staff'), ('Role', 'shifts.role'), ('Task', 'shifts.task'), ('Start', 'shifts.start'), ('End', 'shifts.end'), ('Hours', 'shifts.hours'),
        ('Rate', 'shifts.rate'), ('Cost', 'shifts.cost')) + [
        FF('Overtime hours', LK('shifts', 'shift_id', 'overtime'), 'num'), FF('Hours of the week', LK('shifts', 'shift_id', 'week_hours'), 'num'), FF('Days worked that week', LK('shifts', 'shift_id', 'days_week'), 'int')]),
    FORM('time_sheet', 'Time Sheet', 'Hours of a staff member for a month', 'pay.pay_id', F(
        ('Staff member', 'pay.staff'), ('Role', 'pay.role'), ('Month', 'pay.month'), ('Hours', 'pay.hours')) + [
        FF('Shifts in the month', 'COUNTIFS(%s,%s,%s,%s)' % (R('shifts', 'staff'), LK('pay', 'pay_id', 'staff'), R('shifts', 'month'), LK('pay', 'pay_id', 'month')), 'int'),
        FF('Average shift in hours', 'IFERROR(%s/COUNTIFS(%s,%s,%s,%s),0)' % (LK('pay', 'pay_id', 'hours'), R('shifts', 'staff'), LK('pay', 'pay_id', 'staff'), R('shifts', 'month'), LK('pay', 'pay_id', 'month')), 'num'),
        FF('Overtime hours in the month', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('shifts', 'overtime'), R('shifts', 'staff'), LK('pay', 'pay_id', 'staff'), R('shifts', 'month'), LK('pay', 'pay_id', 'month')), 'num'),
        FF('All staff hours of the month', LK('pay', 'pay_id', 'month_hours'), 'num')]),
    FORM('pay_sheet', 'Pay Sheet', 'Pay of a staff member for a month', 'pay.pay_id', F(
        ('Staff member', 'pay.staff'), ('Role', 'pay.role'), ('Pay type', 'pay.pay_type'), ('Month', 'pay.month'), ('Hours', 'pay.hours'), ('Gross pay', 'pay.gross'), ('Employer cost', 'pay.employer_cost'),
        ('Total', 'pay.total'), ('Status', 'pay.status')) + [
        FF('Pay per hour', 'IFERROR(%s/%s,0)' % (LK('pay', 'pay_id', 'gross'), LK('pay', 'pay_id', 'hours')), 'money'), FF('Employer cost share', 'IFERROR(%s/%s,0)' % (LK('pay', 'pay_id', 'employer_cost'), LK('pay', 'pay_id', 'gross')), 'pct'),
        FF('Staff pay run of the month', LK('pay', 'pay_id', 'month_total'), 'money')]),
    FORM('task_checklist_sheet', 'Task Checklist Sheet', 'Task checklist of a role', 'tasks_role.role', F(
        ('Tasks done', 'tasks_role.tasks_done'), ('Tasks missed', 'tasks_role.tasks_missed')) + [
        FF('Days counted', '{set:task_days}', 'int'), FF('Done share', 'IFERROR(%s/(%s+%s),0)' % (LK('tasks_role', 'role', 'tasks_done'), LK('tasks_role', 'role', 'tasks_done'), LK('tasks_role', 'role', 'tasks_missed')), 'pct'),
        FF('Tasks of the role, last 30 days', 'COUNTIFS(%s,{pick},%s,">="&({today}-30))' % (R('task_log', 'role'), R('task_log', 'date')), 'int')],
        lines={"from": "task_log", "match": "task_log.role", "columns": ["date", "task", "staff", "done"], "max": 20}),
    FORM('roster_change_sheet', 'Roster Change Sheet', 'Roster change for one day', 'staff_need.date', F(
        ('Pickups', 'staff_need.pickups'), ('Returns', 'staff_need.returns'), ('Runs', 'staff_need.runs'), ('Cleaning hours needed', 'staff_need.clean_need'), ('Delivery hours needed', 'staff_need.delivery_need'),
        ('Counter hours needed', 'staff_need.counter_need'), ('Hours needed', 'staff_need.hours_needed'), ('Hours rostered', 'staff_need.hours_rostered'), ('Gap, hours', 'staff_need.gap'), ('Status', 'staff_need.status')) + [
        FF('Shifts rostered that day', 'COUNTIFS(%s,{pick})' % R('shifts', 'date'), 'int'), FF('Hours to add or move', 'MAX(0,%s)' % LK('staff_need', 'date', 'gap'), 'num'),
        FF('Cost of the added hours, detailer rate', 'MAX(0,%s)*{set:detailer_rate}*(1+{set:employer_cost_pct})' % LK('staff_need', 'date', 'gap'), 'money')]),
    FORM('run_handover_sheet', 'Run Handover Sheet', 'Run handed from one driver to the other', 'delivery_runs.run_id', F(
        ('Date', 'delivery_runs.date'), ('Start', 'delivery_runs.start_time'), ('End', 'delivery_runs.end_time'), ('Zone', 'delivery_runs.location'), ('Driver now', 'delivery_runs.driver'), ('Other driver', 'delivery_runs.other_driver')) + [
        FF('Other driver free, 1 for yes', LK('delivery_runs', 'run_id', 'other_free'), 'int'), FF('Runs that clash for the driver now', 'MAX(0,%s)' % LK('delivery_runs', 'run_id', 'clash'), 'int'),
        FF('Minutes you need between runs', '{set:clash_min}', 'int')]),
    FORM('late_ready_sheet', 'Late Ready Sheet', 'Car that may not be ready for its pickup', 'turnaround.turn_id', F(
        ('Vehicle', 'turnaround.vehicle'), ('Class', 'turnaround.class'), ('Clean end', 'turnaround.clean_end'), ('Next pickup', 'turnaround.next_pickup'), ('Pickup time', 'turnaround.next_pickup_time'),
        ('Slack minutes', 'turnaround.slack_minutes'), ('Clean by', 'turnaround.ready_by'), ('Verdict', 'turnaround.verdict')) + [
        FF('Minutes to find', 'MAX(0,{set:tight_min}-%s)' % LK('turnaround', 'turn_id', 'slack_minutes'), 'int'), FF('Cars at risk today and tomorrow', LK('turnaround', 'turn_id', 'risk_now'), 'int'),
        FF('Spare minutes you want', '{set:tight_min}', 'int')]),
    FORM('supplies_order_sheet', 'Supplies Order Sheet', 'Order of cleaning supplies', 'supplies.order_id', F(
        ('Date', 'supplies.date'), ('Product', 'supplies.product'), ('Quantity', 'supplies.quantity'), ('Unit cost', 'supplies.unit_cost'), ('Cost', 'supplies.cost'), ('Needed by', 'supplies.need_by')) + [
        FF('Supplies of the month', LK('supplies', 'order_id', 'month_cost'), 'money'), FF('Orders in the last 12 months', 'COUNTIFS(%s,">="&({today}-365))' % R('supplies', 'date'), 'int'),
        FF('Share of the month spent on this order', 'IFERROR(%s/%s,0)' % (LK('supplies', 'order_id', 'cost'), LK('supplies', 'order_id', 'month_cost')), 'pct')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('turnaround_board_doc', 'Daily Turnaround Board', 'Turnaround board line for a returned car', 'turnaround.turn_id', [
        'Turnaround board of {set:company}, dated {today}. Vehicle: {col:turnaround.vehicle}, class {col:turnaround.class}, booking {col:turnaround.booking_id}.',
        'Returned on {col:turnaround.return_date} at {col:turnaround.returned_time}. Cleaning by {col:turnaround.cleaner} from {col:turnaround.clean_start} to {col:turnaround.clean_end}, {col:turnaround.clean_minutes} minutes.',
        'Next pickup: {col:turnaround.next_pickup} at {col:turnaround.next_pickup_time}. Slack: {col:turnaround.slack_minutes} minutes. Verdict: {col:turnaround.verdict}. Clean by {col:turnaround.ready_by}.',
        'Turnaround is the time between a return and the next pickup. Slack is the time left after cleaning. The tight and buffer minutes are your own settings.'], ['Manager', 'Detailer'], NOTE),
    DOC('cleaning_card_doc', 'Cleaning Job Card', 'Cleaning job card for one car', 'turnaround.turn_id', [
        'Cleaning job card of {set:company}, dated {today}. Vehicle: {col:turnaround.vehicle}, class {col:turnaround.class}. Detailer: {col:turnaround.cleaner}.',
        'Cleaning date: {col:turnaround.clean_date}, from {col:turnaround.clean_start} to {col:turnaround.clean_end}. Minutes: {col:turnaround.clean_minutes}. Cleaning cost: {col:turnaround.clean_cost}. Very dirty: {col:turnaround.dirty}.',
        'Please clean the inside and outside, check the fuel or charge level, and tell the manager about anything that looks wrong. Photos taken: write yes or no on the booking.',
        'The next pickup is on {col:turnaround.next_pickup} at {col:turnaround.next_pickup_time}. Please finish by {col:turnaround.ready_by}.'], ['Detailer', 'Manager'], NOTE),
    DOC('run_sheet_doc', 'Delivery Collection Run Sheet', 'Delivery or collection run sheet', 'delivery_runs.run_id', [
        'Run sheet of {set:company}, dated {today}. Run {col:delivery_runs.run_id} on {col:delivery_runs.date}, {col:delivery_runs.kind}. Booking {col:delivery_runs.booking_id}, vehicle {col:delivery_runs.vehicle}.',
        'Zone: {col:delivery_runs.location}. Driver: {col:delivery_runs.driver}. Start: {col:delivery_runs.start_time}, end: {col:delivery_runs.end_time}. Minutes: {col:delivery_runs.minutes}. Miles: {col:delivery_runs.miles}.',
        'Fee charged: {col:delivery_runs.fee_charged}. Driver cost: {col:delivery_runs.driver_cost}. Profit of the run: {col:delivery_runs.profit}. Fees are before any sales tax.',
        'At the door, write the odometer and the fuel or charge level on the handover record and tell the renter the return time. Check your hire terms for the rest.'], ['Driver', 'Renter'], NOTE),
    DOC('weekly_roster_doc', 'Weekly Roster', 'Roster note for a staff member', 'shifts.shift_id', [
        'Roster of {set:company}, dated {today}. Staff member: {col:shifts.staff}, role {col:shifts.role}. Week of {col:shifts.week}.',
        'This shift: {col:shifts.weekday} {col:shifts.date}, {col:shifts.task}, from {col:shifts.start} to {col:shifts.end}, {col:shifts.hours} hours at a rate of {col:shifts.rate}.',
        'Hours of the week: {col:shifts.week_hours}. Days worked that week: {col:shifts.days_week}. All staff hours of the week: {col:shifts.week_total}.',
        'Please tell the manager as soon as you cannot work a shift so that the roster can change. Check your local rules for rest and notice.'], ['Manager', 'Staff member'], NOTE),
    DOC('pay_summary_doc', 'Pay Summary', 'Pay summary for a staff member', 'pay.pay_id', [
        'Pay summary of {set:company}, dated {today}. Staff member: {col:pay.staff}. Role: {col:pay.role}. Month: {col:pay.month}.',
        'Pay type: {col:pay.pay_type}. Hours: {col:pay.hours}. Gross pay: {col:pay.gross}. Employer cost: {col:pay.employer_cost}. Total cost: {col:pay.total}. Status: {col:pay.status}.',
        'This sheet only helps you keep track of hours and amounts. Tax and social contributions are worked out by your adviser; confirm with your adviser.',
        'Please tell the manager within a few days if the hours do not match your own record.'], ['Manager', 'Staff member'], NOTE),
    DOC('role_tasks_doc', 'Role Task Checklist', 'Task checklist of a role', 'tasks_role.role', [
        'Task checklist of {set:company}, dated {today}. Role: {col:tasks_role.role}.',
        'In the last {set:task_days} days: {col:tasks_role.tasks_done} tasks done and {col:tasks_role.tasks_missed} tasks missed.',
        'Each day, open the Task Log, tick the tasks of your role as you finish them and write a short note for any task you could not do.',
        'The manager reads the missed tasks every week and agrees the next step with you.'], ['Manager', 'Staff member'], NOTE),
    DOC('delivery_fee_doc', 'Delivery Fee Policy', 'Delivery fee policy for a location', 'zones.location', [
        'Delivery fee policy of {set:company}, dated {today}. Location: {col:zones.location}.',
        'Fee for one leg: {col:zones.fee_leg}. A delivery and a collection are two legs. Typical run: {col:zones.run_minutes} minutes. Fees are before any sales tax.',
        'The fee helps pay for driver time and fuel or charge. We review it when the cost of a run changes.',
        'The renter is told the delivery and collection times when booking. Check your hire terms for late or missed handovers.'], ['Owner', 'Renter'], NOTE),
    DOC('cleaning_standard_doc', 'Cleaning Standard Sheet', 'Cleaning standard for a vehicle class', 'clean_class.class', [
        'Cleaning standard of {set:company}, dated {today}. Vehicle class: {col:clean_class.class}.',
        'Average cleaning time: {col:clean_class.avg_minutes} minutes. Average cleaning cost: {col:clean_class.cost_rental}. A buffer of {set:buffer_min} minutes after a return is set aside.',
        'Standard: empty the car, vacuum the floor and seats, wipe the dashboard and doors, clean the windows, check the fuel or charge level and the odometer, and report anything unusual to the manager.',
        'A very dirty car may take a cleaning fee of {set:cleaning_fee}, as written in the hire terms.'], ['Manager', 'Detailer'], NOTE),
    DOC('handbook_cover_doc', 'Staff Handbook Cover', 'Staff handbook cover page', 'team.staff_id', [
        'Staff handbook of {set:company}, dated {today}. Staff member: {col:team.name}, {col:team.role}, staff ID {col:team.staff_id}.',
        'Hours a week: {col:team.hours_week}. Contact: {col:team.phone} and {col:team.email}. Area: {col:team.area}.',
        'This handbook explains shifts, the roster, pay days and daily tasks. Employment, leave, safety, privacy and record keeping rules differ by place: check your local rules.',
        'Please read it, ask the manager any question and sign below.'], ['Manager', 'Staff member'], NOTE),
    DOC('driver_note_doc', 'Driver Handover Note', 'Handover note for a run', 'delivery_runs.run_id', [
        'Driver handover note of {set:company}, dated {today}. Run {col:delivery_runs.run_id} on {col:delivery_runs.date} at {col:delivery_runs.start_time}.',
        'Zone: {col:delivery_runs.location}. Vehicle: {col:delivery_runs.vehicle}. Driver now: {col:delivery_runs.driver}. Other driver: {col:delivery_runs.other_driver}. The other driver is free for this run: {col:delivery_runs.other_free} (1 means yes).',
        'Please hand over the keys, the booking reference and the notes on the car. Check the odometer and the fuel or charge level together and write them down.',
        'Runs that clash for the driver now: {col:delivery_runs.clash}. Minutes late: {col:delivery_runs.delay_min}.'], ['Driver', 'Other driver'], NOTE),
    DOC('supplies_order_doc', 'Supplies Order', 'Order of cleaning supplies', 'supplies.order_id', [
        'Supplies order of {set:company}, dated {today}. Order {col:supplies.order_id}, placed on {col:supplies.date}.',
        'Product: {col:supplies.product}. Quantity: {col:supplies.quantity}. Unit cost: {col:supplies.unit_cost}. Cost: {col:supplies.cost}. Needed by {col:supplies.need_by}. Amounts are before any sales tax.',
        'Supplies of the month: {col:supplies.month_cost}. Please confirm the delivery date and any change of price.',
        'Please deliver to the main lot during opening hours.'], ['Manager', 'Supplier'], NOTE),
    DOC('monthly_ops_doc', 'Monthly Operations Report', 'Monthly operations report', 'hours_month.month', [
        'Monthly operations report of {set:company}, dated {today}. Month: {col:hours_month.month}.',
        'Shift hours: {col:hours_month.hours}. Shift pay: {col:hours_month.pay}. Rentals started: {col:hours_month.rentals}. Hours cost per rental: {col:hours_month.cost_rental}. Hours per rental: {col:hours_month.hours_rental}. Pay per hour: {col:hours_month.pay_hour}.',
        'Cleaning supplies: {col:hours_month.supplies}, that is {col:hours_month.supplies_rental} per rental. Your target for the hours cost per rental is {set:cost_target}.',
        'Check the Turnaround Board, the delivery profit by zone and the task log before you decide on hours or fees.'], ['Owner', 'Manager'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('opening_chk', 'Opening the Lot', 'staff_need', 'staff_need.date', [('Unlock the lot and check the gates and lights', 0), ('Open the Turnaround Board and read the returns of the day', 0), ('Check the cars booked for pickup and their cleaning status', 0), ('Check the runs of the day and the drivers', 0), ('Check who is on shift and the hours rostered', 0), ('Write any gap in the Roster Change Sheet', 0)]),
    CHK('morning_turn_chk', 'Morning Turnaround Check', 'turnaround', 'turnaround.return_date', [('List the cars returned overnight', 0), ('Run the Late-Ready Risk List', 0), ('Order the cleaning queue by next pickup', 0), ('Tell the detailers which car to clean first', 0), ('Check the fuel or charge level of each returned car', 0), ('Mark each car ready on the board', 1)]),
    CHK('run_start_chk', 'Delivery Run Start', 'delivery_runs', 'delivery_runs.date', [('Check the Runs Today and Tomorrow sheet', 0), ('Check the Run Clash Check for each driver', 0), ('Check the car is clean and has its fuel or charge level noted', 0), ('Take the keys and the booking reference', 0), ('Message the renter with the delivery time', 0)]),
    CHK('door_handover_chk', 'Delivery Handover at the Door', 'delivery_runs', 'delivery_runs.date', [('Greet the renter and check the booking reference', 0), ('Walk round the car and note any mark', 0), ('Write the odometer and the fuel or charge level', 0), ('Explain the return time and the late return rule', 0), ('Hand over the keys', 0), ('Close the run on the sheet', 0)]),
    CHK('collection_chk', 'Collection Run', 'delivery_runs', 'delivery_runs.date', [('Message the renter with the collection time', 0), ('Walk round the car and compare it with the handover notes', 0), ('Write the odometer and the fuel or charge level', 0), ('Take the keys and tell the manager about any mark', 0), ('Bring the car back to the lot', 0), ('Add the car to the Turnaround Board', 0)]),
    CHK('end_day_chk', 'End-of-Day Lot Check', 'roster_day', 'roster_day.date', [('Check every returned car is cleaned or queued', 0), ('Count the cars on the lot against the board', 0), ('Check the keys are in their place', 0), ('Close the Task Log for the day', 0), ('Read tomorrow pickups and runs', 0), ('Lock the lot and switch off the lights', 0)]),
    CHK('roster_chk', 'Weekly Roster Check', 'shifts', 'shifts.week', [('Open Staff Needed by Day for the next four weeks', -4), ('Run the Roster Check Against Bookings', -3), ('Run the Weekend Cover Planner', -3), ('Fill the gaps with shifts or part-time hours', -2), ('Run the Long-Day Check', -2), ('Send the shifts to each staff member', -1), ('Approve the roster', 0)]),
    CHK('pay_run_chk', 'Pay Run Steps', 'pay', 'pay.month', [('Check the shifts of the month in the Shifts sheet', 28), ('Check the hours in the Pay sheet', 29), ('Run the Pay Calculator for each person', 29), ('Check the hours cost per rental', 30), ('Send the hours and the pay run to the bookkeeper', 30), ('Send the pay summary to the accountant', 32), ('Mark each pay row as paid', 33)]),
    CHK('cleaning_std_chk', 'Cleaning Standard Steps', 'turnaround', 'turnaround.clean_date', [('Empty the car and remove any rubbish', 0), ('Vacuum the floor, seats and boot', 0), ('Wipe the dashboard, doors and handles', 0), ('Clean the windows and mirrors', 0), ('Check the fuel or charge level', 0), ('Mark very dirty cars on the board', 0)]),
    CHK('weekend_chk', 'Weekend Cover', 'roster_day', 'roster_day.date', [('Check the weekend pickups, returns and runs', -5), ('Check the assistant, driver and detailer hours', -4), ('Add a shift for any gap', -3), ('Message the assistant and the drivers', -2), ('Check the cleaning supplies for the weekend', -2), ('Leave a note for the manager on Monday', 2)]),
    CHK('supplies_chk', 'Supplies Check', 'supplies', 'supplies.date', [('Count the cleaning products on the shelf', -7), ('Compare the use with your usual in Cleaning Supplies Use', -6), ('Write the order in Supplies Orders', -5), ('Message the supplier', -5), ('Check the delivery against the order', 0), ('Put the order away and note any shortage', 1)]),
    CHK('one_car_chk', 'One-Car Host Day', 'bookings', 'bookings.start_date', [('Check the pickup time and the renter message', -1), ('Clean the car and check the fuel or charge level', -1), ('Write the odometer and level at handover', 0), ('Hand over the car and note the return time', 0), ('Write the odometer and level at return', 0), ('Clean and check the car for the next booking', 1)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def first_of(role): return first_name([t['name'] for t in team if t['role'] == role][0])
TOM = first_name(MANAGER); NAD = first_name(OWNER); SAN = first_of('Booking assistant'); ELS = first_of('Bookkeeper'); ING = first_of('Accountant'); DIE = first_of('Mechanic'); MEI = first_of('Car-wash supplier')
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('d_return', 'Detailer: a car returns soon', 'turnaround', 'turnaround.detailer_phone', 'Hello {cleaner}, {vehicle} returns at {returned_time}, next pickup {next_pickup_time}. {company}'),
    M('d_first', 'Detailer: clean this car first', 'turnaround', 'turnaround.detailer_phone', 'Hello {cleaner}, please clean {vehicle} first: {slack_minutes} minutes are left before its pickup. {company}'),
    M('d_finish', 'Detailer: finish by a time', 'turnaround', 'turnaround.detailer_phone', 'Hello {cleaner}, please finish {vehicle} by {ready_by}. The next pickup is at {next_pickup_time}. {company}'),
    M('d_week', 'Detailer: your shifts next week', 'shifts', 'shifts.staff_phone', 'Hello {staff}, your shifts for the week of {week} total {week_hours} hours. Please check them. {company}'),
    M('d_thanks', 'Detailer: thank you for the cars', 'clean_load', 'clean_load.cleaner_phone', 'Hello {cleaner}, thank you: {cars} cars were cleaned on {date}. {company}'),
    M('dr_delivery', 'Driver: delivery run', 'delivery_runs', 'delivery_runs.driver_phone', 'Hello {driver}, delivery to {location} at {start_time} for {booking_id}. {company}'),
    M('dr_collect', 'Driver: collection run', 'delivery_runs', 'delivery_runs.driver_phone', 'Hello {driver}, collection from {location} at {start_time} for {booking_id}. {company}'),
    M('dr_day', 'Driver: your runs of the day', 'delivery_runs', 'delivery_runs.driver_phone', 'Hello {driver}, you have {runs_day} runs on {date}. Please check the times. {company}'),
    M('dr_moved', 'Driver: a run moved', 'delivery_runs', 'delivery_runs.driver_phone', 'Hello {driver}, run {run_id} moved to {start_time}. {company}'),
    M('dr_confirm', 'Driver: confirm the delivery', 'delivery_runs', 'delivery_runs.driver_phone', 'Hello {driver}, please confirm you took {vehicle} to {location}. {company}'),
    M('dr_week', 'Driver: your shifts next week', 'shifts', 'shifts.staff_phone', 'Hello {staff}, your delivery shifts for the week of {week} total {week_hours} hours. {company}'),
    M('dr_thanks', 'Driver: thank you for the runs', 'delivery_runs', 'delivery_runs.driver_phone', 'Hello {driver}, thank you for the runs on {date}: {runs_day} done. {company}'),
    M('as_counter', 'Assistant: your counter day', 'roster_day', 'roster_day.assistant_phone', 'Hello %s, the counter on {date} has {pickups} pickups and {returns} returns, with {counter_hours} counter hours rostered. {company}' % SAN),
    M('as_pickups', 'Assistant: pickups booked', 'roster_day', 'roster_day.assistant_phone', 'Hello %s, {pickups} pickups are booked for {date}. Please be ready at the counter. {company}' % SAN),
    M('mg_risk', 'Manager: cars may not be ready', 'turnaround', 'turnaround.manager_phone', 'Hello %s, {risk_now} cars may not be ready on time today or tomorrow. Please check the turnaround board. {company}' % TOM),
    M('mg_ready', 'Manager: a car is ready', 'turnaround', 'turnaround.manager_phone', 'Hello %s, {vehicle} is ready for pickup at {next_pickup_time}. {company}' % TOM),
    M('mg_short', 'Manager: days short of staff', 'staff_need', 'staff_need.manager_phone', 'Hello %s, {short_days} days next week are short of staff. Please check the roster. {company}' % TOM),
    M('mg_payrun', 'Manager: the pay run', 'pay', 'pay.manager_phone', 'Hello %s, the pay run for {month} is {month_total}. {company}' % TOM),
    M('mg_missed', 'Manager: tasks missed by a role', 'task_log', 'task_log.manager_phone', 'Hello %s, the {role} role missed {role_missed} tasks this week. Please review them. {company}' % TOM),
    M('mg_fee', 'Manager: a delivery fee against cost', 'delivery_runs', 'delivery_runs.manager_phone', 'Hello %s, the delivery fee for {location} covers {zone_cover} of the cost of a run. {company}' % TOM),
    M('mg_roster', 'Manager: approve the roster', 'shifts', 'shifts.manager_phone', 'Hello %s, please approve the roster for the week of {week}: {week_total} hours in total. {company}' % TOM),
    M('ow_cost', 'Owner: hours cost per rental', 'hours_month', 'hours_month.owner_phone', 'Hello %s, hours cost per rental for {month} was {cost_rental}, with {hours_rental} hours per rental. {company}' % NAD),
    M('ow_zone', 'Owner: what a zone earns', 'delivery_runs', 'delivery_runs.owner_phone', 'Hello %s, the {location} zone earns {zone_profit} per run. {company}' % NAD),
    M('ow_tight', 'Owner: tight turnarounds', 'turnaround', 'turnaround.owner_phone', 'Hello %s, tight or late turnarounds were {tight_share_lm} of returns last month. {company}' % NAD),
    M('ow_pay', 'Owner: staff pay of the month', 'pay', 'pay.owner_phone', 'Hello %s, staff pay for {month} is {month_total}. {company}' % NAD),
    M('bk_hours', 'Bookkeeper: record the hours', 'pay', 'pay.bookkeeper_phone', 'Hello %s, please record the staff hours for {month}: {month_hours} hours in total. {company}' % ELS),
    M('bk_payrun', 'Bookkeeper: the pay run', 'pay', 'pay.bookkeeper_phone', 'Hello %s, the pay run is {month_total} for {month}. {company}' % ELS),
    M('acc_pay', 'Accountant: staff pay summary', 'pay', 'pay.accountant_phone', 'Hello %s, staff pay summary for {month}: gross {month_gross} and employer costs {month_employer}. {company}' % ING),
    M('cw_order', 'Supplier: please deliver supplies', 'supplies', 'supplies.vendor_phone', 'Hello %s, please deliver {quantity} units of {product} by {need_by}. {company}' % MEI),
    M('cw_use', 'Supplier: our monthly use', 'supplies', 'supplies.vendor_phone', 'Hello %s, our cleaning supplies use for {month} was {month_cost}. {company}' % MEI),
    M('me_wash', 'Mechanic: wash before the workshop', 'turnaround', 'turnaround.mechanic_phone', 'Hello %s, {vehicle} needs a wash before the workshop visit. {company}' % DIE),
    M('rn_deliver', 'Renter: your car will be delivered', 'delivery_runs', 'delivery_runs.phone', 'Hello {renter}, your car will be delivered to {location} at {start_time}. {company}'),
    M('rn_late', 'Renter: your driver is late', 'delivery_runs', 'delivery_runs.phone', 'Hello {renter}, your driver is running {delay_min} minutes late. Sorry for the wait. {company}'),
    M('rn_collect', 'Renter: we will collect the car', 'delivery_runs', 'delivery_runs.phone', 'Hello {renter}, we will collect the car from {location} at {start_time}. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
TNR_ = lambda c: R('turnaround', c); DRR = lambda c: R('delivery_runs', c); SHR = lambda c: R('shifts', c); PYR = lambda c: R('pay', c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def D30(t, c='date'): return '%s,">="&({today}-30),%s,"<="&{today}' % (R(t, c), R(t, c))
def DM(t, c='date'): return '%s,">="&%s,%s,"<="&{today}' % (R(t, c), MS, R(t, c))
BKLIVE = '%s,"<>"&%s,%s,"<>"&%s' % (R('bookings', 'status'), tok('bstatus', 'Cancelled'), R('bookings', 'status'), tok('bstatus', 'No-show'))
VR = lambda v: '%s,%s' % (TNR_('verdict'), va(v))
kpis = [
    KPI('Returns cleaned today', 'COUNTIFS(%s,{today})' % TNR_('clean_date'), 'int'),
    KPI('Cleaning minutes today', 'SUMIFS(%s,%s,{today})' % (TNR_('clean_minutes'), TNR_('clean_date')), 'int'),
    KPI('Turnarounds this month', 'COUNTIFS(%s,">="&%s)' % (TNR_('return_date'), MS), 'int'),
    KPI('Turnarounds ready on time, last 30 days', 'IFERROR(COUNTIFS(%s,%s)/COUNTIFS(%s,%s,"<>"&%s),0)' % (D30('turnaround', 'return_date'), VR('Ready on time'), D30('turnaround', 'return_date'), TNR_('verdict'), va('No pickup booked')), 'pct'),
    KPI('Tight turnarounds, last 30 days', 'COUNTIFS(%s,%s)' % (D30('turnaround', 'return_date'), VR('Tight, under the minimum')), 'int'),
    KPI('Late turnarounds, last 30 days', 'COUNTIFS(%s,%s)' % (D30('turnaround', 'return_date'), VR('Late, clean first')), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Average slack, pickup in a day, minutes', 'IFERROR(AVERAGEIFS(%s,%s,"<1440",%s,">="&({today}-60)),0)' % (TNR_('slack_minutes'), TNR_('slack_minutes'), TNR_('return_date')), 'int'),
    KPI('Clean minutes per car, last 30 days', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (TNR_('clean_minutes'), D30('turnaround', 'return_date')), 'num'),
    KPI('Cleaning cost per rental, last 30 days', 'IFERROR(SUMIFS(%s,%s)/COUNTIFS(%s),0)' % (TNR_('clean_cost'), D30('turnaround', 'return_date'), D30('turnaround', 'return_date')), 'money'),
    KPI('Cleaning hours this month', 'SUMIFS(%s,%s,">="&%s)/60' % (TNR_('clean_minutes'), TNR_('return_date'), MS), 'num'),
    KPI('Very dirty cars, last 90 days', 'IFERROR(COUNTIFS(%s,">="&({today}-90),%s,%s)/COUNTIFS(%s,">="&({today}-90)),0)' % (TNR_('return_date'), TNR_('dirty'), YES, TNR_('return_date')), 'pct'),
    KPI('Delivery and collection runs today', 'COUNTIFS(%s,{today})' % DRR('date'), 'int'),
    KPI('Runs this month', 'COUNTIFS(%s)' % DM('delivery_runs'), 'int'),
    KPI('Run minutes this month', 'SUMIFS(%s,%s)' % (DRR('minutes'), DM('delivery_runs')), 'int'),
    KPI('Driver cost this month', 'SUMIFS(%s,%s)' % (DRR('driver_cost'), DM('delivery_runs')), 'money'),
    KPI('Delivery fees charged this month', 'SUMIFS(%s,%s)' % (DRR('fee_charged'), DM('delivery_runs')), 'money'),
    KPI('Fees minus driver cost this month', 'SUMIFS(%s,%s)-SUMIFS(%s,%s)' % (DRR('fee_charged'), DM('delivery_runs'), DRR('driver_cost'), DM('delivery_runs')), 'money'),
    KPI('Delivery profit per run, last 90 days', 'IFERROR((SUMIFS(%s,%s,">="&({today}-90),%s,"<="&{today})-SUMIFS(%s,%s,">="&({today}-90),%s,"<="&{today}))/COUNTIFS(%s,">="&({today}-90),%s,"<="&{today}),0)'
        % (DRR('fee_charged'), DRR('date'), DRR('date'), DRR('driver_cost'), DRR('date'), DRR('date'), DRR('date'), DRR('date')), 'money'),
    KPI('Bookings with delivery, last 90 days', 'IFERROR(1-COUNTIFS(%s,">="&({today}-90),%s,"<="&{today},%s,%s,%s)/COUNTIFS(%s,">="&({today}-90),%s,"<="&{today},%s),0)'
        % (R('bookings', 'start_date'), R('bookings', 'start_date'), R('bookings', 'pickup_location'), tok('location', 'Main lot'), BKLIVE, R('bookings', 'start_date'), R('bookings', 'start_date'), BKLIVE), 'pct'),
    KPI('Least profitable zone', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (R('zone_profit', 'zone'), R('zone_profit', 'profit_run'), R('zone_profit', 'profit_run')), 'text'),
    KPI('Shift hours this month', 'SUMIFS(%s,%s)' % (SHR('hours'), DM('shifts')), 'num'),
    KPI('Staff pay this month', 'SUMIFS(%s,%s,%s,%s,"<>"&%s)' % (PYR('total'), PYR('month'), MS, PYR('pay_type'), tok('paytype', 'Owner draw')), 'money'),
    KPI('Staff pay last month', 'SUMIFS(%s,%s,EDATE(%s,-1),%s,"<>"&%s)' % (PYR('total'), PYR('month'), MS, PYR('pay_type'), tok('paytype', 'Owner draw')), 'money'),
    KPI('Hours cost per rental, last 30 days', 'IFERROR(SUMIFS(%s,%s)/COUNTIFS(%s,%s),0)' % (SHR('cost'), D30('shifts'), D30('bookings', 'start_date'), BKLIVE), 'money'),
    KPI('Pay per hour worked this month', 'IFERROR(SUMIFS(%s,%s,%s,%s,%s)/SUMIFS(%s,%s,%s,%s,%s),0)' % (PYR('total'), PYR('month'), MS, PYR('pay_type'), tok('paytype', 'Hourly'), PYR('hours'), PYR('month'), MS, PYR('pay_type'), tok('paytype', 'Hourly')), 'money'),
    KPI('Days short of staff, next 14 days', 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<"&({today}+14))' % (R('staff_need', 'status'), vb('Short'), R('staff_need', 'date'), R('staff_need', 'date')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Overtime hours this month', 'SUMIFS(%s,%s)' % (SHR('overtime'), DM('shifts')), 'num'),
    KPI('Tasks done, last 7 days', 'COUNTIFS(%s,">="&({today}-7),%s,%s)' % (R('task_log', 'date'), R('task_log', 'done'), YES), 'int'),
    KPI('Tasks missed, last 7 days', 'COUNTIFS(%s,">="&({today}-7),%s,%s)' % (R('task_log', 'date'), R('task_log', 'done'), NO), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Weekend hours this month', 'SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s)' % (SHR('hours'), DM('shifts'), '%s,%s' % (SHR('weekday'), tok('wday', 'Saturday')), SHR('hours'), DM('shifts'), '%s,%s' % (SHR('weekday'), tok('wday', 'Sunday'))), 'num'),
]
# the two SUMIFS above need the criteria pairs in a flat list: rebuild them explicitly
kpis[-1]['formula'] = 'SUMIFS(%s,%s,%s,%s)+SUMIFS(%s,%s,%s,%s)' % (SHR('hours'), DM('shifts'), SHR('weekday'), tok('wday', 'Saturday'), SHR('hours'), DM('shifts'), SHR('weekday'), tok('wday', 'Sunday'))
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Operations Dashboard", "kpis": kpis,
    "monthly": {"title": "Delivery fees, driver cost, cleaning cost and shift pay", "date": "delivery_runs.date", "series": [
        {"label": "Delivery fees", "sum": "delivery_runs.fee_charged", "date": "delivery_runs.date"}, {"label": "Driver cost", "sum": "delivery_runs.driver_cost", "date": "delivery_runs.date"},
        {"label": "Cleaning cost", "sum": "turnaround.clean_cost", "date": "turnaround.return_date"}, {"label": "Shift pay", "sum": "shifts.cost", "date": "shifts.date"}]},
    "breakdowns": [{"title": "Runs by zone", "by": "delivery_runs.location", "agg": "count"}, {"title": "Shift hours by task", "by": "shifts.task", "value": "shifts.hours", "agg": "sum"},
                   {"title": "Cleaning cost by class", "by": "turnaround.class", "value": "turnaround.clean_cost", "agg": "sum"}, {"title": "Staff pay by role", "by": "pay.role", "value": "pay.total", "agg": "sum"}]}
VERD = lambda v: ('verdict', '=', va(v))
insights = {"filters": [{"label": "Vehicle class", "list": "class"}, {"label": "Delivery zone", "list": "zone"}, {"label": "Detailer", "list": "cleaner"}],
    "gauges": [
        {"title": "Turnarounds ready on time", "num": AGG('count', 'turnaround', where=[VERD('Ready on time')]), "den": AGG('count', 'turnaround', where=[('verdict', '<>', va('No pickup booked'))])},
        {"title": "Driver cost against delivery fees", "num": AGG('sum', 'delivery_runs', 'delivery_runs.driver_cost'), "den": AGG('sum', 'delivery_runs', 'delivery_runs.fee_charged')},
        {"title": "Days covered by staff", "num": AGG('count', 'staff_need', where=[('status', '=', vb('Covered'))]), "den": AGG('count', 'staff_need')},
        {"title": "Tasks done against tasks planned", "num": AGG('count', 'task_log', where=[('done', '=', YES)]), "den": AGG('count', 'task_log')},
        {"title": "Months within the cost target", "num": AGG('count', 'hours_month', where=[('cost_rental', '<=', '{set:cost_target}')]), "den": AGG('count', 'hours_month')},
        {"title": "Cleaning done within the buffer", "num": AGG('count', 'turnaround', where=[('turn_minutes', '<=', '{set:buffer_min}')]), "den": AGG('count', 'turnaround')}],
    "charts": [
        CHART('Turnarounds per month', 'column', 'month', [AGG('count', 'turnaround', date='turnaround.return_date', label='Turnarounds')]),
        CHART('Turnaround slack by class, pickup within a day', 'bar', 'turnaround.class', [AGG('avg', 'turnaround', 'turnaround.slack_minutes', where=[('slack_minutes', '<', 1440)], label='Slack minutes')]),
        CHART('Tight and late turnarounds per month', 'column', 'month', [AGG('count', 'turnaround', date='turnaround.return_date', where=[VERD('Tight, under the minimum')], label='Tight'), AGG('count', 'turnaround', date='turnaround.return_date', where=[VERD('Late, clean first')], label='Late')]),
        CHART('Clean minutes by class', 'bar', 'turnaround.class', [AGG('avg', 'turnaround', 'turnaround.clean_minutes', label='Clean minutes')]),
        CHART('Cleaning cost per month', 'column', 'month', [AGG('sum', 'turnaround', 'turnaround.clean_cost', date='turnaround.return_date', label='Cleaning cost')]),
        CHART('Cleaning cost by detailer', 'bar', 'turnaround.cleaner', [AGG('sum', 'turnaround', 'turnaround.clean_cost', label='Cleaning cost')]),
        CHART('Cars cleaned by weekday', 'bar', 'turnaround.weekday', [AGG('count', 'turnaround', label='Cars cleaned')]),
        CHART('Runs per month', 'column', 'month', [AGG('count', 'delivery_runs', date='delivery_runs.date', label='Runs')]),
        CHART('Runs by zone', 'bar', 'delivery_runs.location', [AGG('count', 'delivery_runs', label='Runs')]),
        CHART('Runs by driver', 'bar', 'delivery_runs.driver', [AGG('count', 'delivery_runs', label='Runs')]),
        CHART('Runs by kind', 'bar', 'delivery_runs.kind', [AGG('count', 'delivery_runs', label='Runs')]),
        CHART('Run minutes per month', 'column', 'month', [AGG('sum', 'delivery_runs', 'delivery_runs.minutes', date='delivery_runs.date', label='Run minutes')]),
        CHART('Driver cost per month', 'column', 'month', [AGG('sum', 'delivery_runs', 'delivery_runs.driver_cost', date='delivery_runs.date', label='Driver cost')]),
        CHART('Delivery fees per month', 'column', 'month', [AGG('sum', 'delivery_runs', 'delivery_runs.fee_charged', date='delivery_runs.date', label='Delivery fees')]),
        CHART('Delivery profit by zone', 'bar', 'delivery_runs.location', [AGG('sum', 'delivery_runs', 'delivery_runs.profit', label='Profit')]),
        CHART('Shift hours per month', 'column', 'month', [AGG('sum', 'shifts', 'shifts.hours', date='shifts.date', label='Shift hours')]),
        CHART('Shift hours by staff member', 'bar', 'shifts.staff', [AGG('sum', 'shifts', 'shifts.hours', label='Shift hours')]),
        CHART('Shift hours by task', 'bar', 'shifts.task', [AGG('sum', 'shifts', 'shifts.hours', label='Shift hours')]),
        CHART('Staff pay per month', 'column', 'month', [AGG('sum', 'pay', 'pay.total', date='pay.month', where=[('pay_type', '<>', tok('paytype', 'Owner draw'))], label='Staff pay')]),
        CHART('Pay and owner draw by staff member', 'bar', 'pay.staff', [AGG('sum', 'pay', 'pay.total', label='Pay and draw')]),
        CHART('Hours cost per rental per month', 'column', 'month', [AGG('sum', 'hours_month', 'hours_month.cost_rental', date='hours_month.month', label='Hours cost per rental')]),
        CHART('Tasks missed by role', 'bar', 'tasks_role.role', [AGG('sum', 'tasks_role', 'tasks_role.tasks_missed', label='Tasks missed')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Turnaround board", "why": "every returned car with its cleaning times and the next pickup, so you see ready, tight or late before the renter arrives", "where": "Turnaround Board"},
    {"name": "Late-ready risk list", "why": "the cars with the least time left before a pickup, ranked, with the one to clean first", "where": "Late-Ready Risk List"},
    {"name": "Turnaround against the buffer", "why": "the share of cars ready within your buffer by class and the buffer each class really needs", "where": "Turnaround Against the Buffer"},
    {"name": "Delivery run planner", "why": "the deliveries and collections of a day with minutes, miles and driver cost against the fees collected", "where": "Delivery Run Planner"},
    {"name": "Delivery fee check by zone", "why": "the fee for one leg set against driver time and fuel, so the zone that loses money is repriced first", "where": "Delivery Fee Check by Zone"},
    {"name": "Driver assignment and clash check", "why": "runs that overlap for one driver, with the other driver named when they are free", "where": "Driver Assignment Planner"},
    {"name": "Roster check against bookings", "why": "pickups, returns and runs turned into hours needed per day, with the days short of staff named", "where": "Roster Check Against Bookings"},
    {"name": "Hours cost per rental", "why": "shift pay per rental against your last 3 months and the same month last year", "where": "Hours Cost per Rental"},
    {"name": "Peak-day staffing forecast", "why": "the next four weeks in Base, Best and Worst cases, with the week to hire part-time hours", "where": "Peak-Day Staffing Forecast"},
    {"name": "Task completion score", "why": "tasks done against missed by role, with the role to review", "where": "Task Completion Score"}]
competitors = [
    {"what": "subscription rental-management software", "lacks": "charges per vehicle or user and rarely shows cleaning slack, delivery profit by zone or hours cost per rental"},
    {"what": "generic booking calendar template", "lacks": "marks the dates of a rental but knows nothing of cleaning time, delivery runs or who is rostered"},
    {"what": "single-sheet vehicle expense log", "lacks": "adds up costs but never compares the fee of a delivery zone with driver time and fuel"},
    {"what": "budget-model template", "lacks": "gives one monthly staff cost line with no shifts, no overtime check and no pay per rental"},
    {"what": "paper cleaning and task sheets", "lacks": "record work done but never count missed tasks or warn when a car may not be ready"}]
guide = [
    'Open Start and type your business name, your buffer minutes, the spare minutes you want before a pickup, the pay of a detailer and a driver, and your hours cost target in the yellow cells.',
    'Keep Team up to date: every staff member and outside contact with role, pay type, phone, hours a week and rate.',
    'Add every return to the Turnaround Board with its cleaning times; slack, the verdict and the clean-by time fill in by themselves.',
    'Add every delivery and collection to Delivery Runs with driver, start time, minutes, miles, fee and driver cost; Zone Profit shows what each zone earns.',
    'Add each shift to Shifts and each month of pay to Pay; the roster and the staff needed by day read the shifts, the Bookings and the runs.',
    'Fill Bookings with the pickups and returns of the coming weeks so Staff Needed by Day can compare hours needed with hours rostered.',
    'Write the tasks of the day in the Task Log and tick them; Tasks by Role shows what each role missed.',
    'Record each order of cleaning supplies in Supplies Orders; Hours Cost by Month adds supplies per rental.',
    'Every morning run the Late-Ready Risk List and the Cleaning Queue Planner; every evening check the Delivery Run Planner for the next day.',
    'Every week run the Roster Check Against Bookings, the Weekend Cover Planner and the Long-Day Check before you approve the roster.',
    'Every month run the Pay Calculator, the Hours Cost per Rental and the Cleaning Supplies Use before the pay run.',
    f'Use the {len(tools)} calculators, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A one-car host can use the Turnaround Board, the task lists and the checklists with no staff: leave the Team, Shifts and Pay sheets empty.',
    'Read the Operations Dashboard and the charts every week. Miles are the demo unit, set your own.']
listing = {"title": "Car Rental Turnaround, Delivery Runs and Staff Roster Excel Template: Cleaning Board, Run Planner, Shifts, Pay",
    "headline": "Get every car ready on time and every run and shift paid for",
    "tags": ["car rental", "car hire", "fleet turnaround", "delivery runs", "staff roster", "excel template", "cleaning board", "shift planner", "pay calculator", "rental business", "van rental", "car sharing host", "ops tracker"],
    "description": ("Run the daily work of a small car or van rental in one Excel workbook. Built for an owner-operator, a manager, detailers, delivery drivers and a weekend assistant who must have every car clean and ready before the next pickup, deliver and collect cars at a fair fee and keep the roster and the pay under control. "
        "The Turnaround Board holds every return with cleaning start and end, detailer, minutes, cost and the next pickup, and works out the slack and a verdict: ready on time, tight or late. Delivery Runs holds every delivery and collection with driver, minutes, miles, fee and driver cost, and Zone Profit shows which zone earns least per run.\n\n"
        "Shifts, Pay, Team, Roster by Day and Staff Needed by Day turn your bookings, returns and runs into hours needed, set them against the hours rostered and name the days short of staff. The Task Log counts tasks done and missed by role, Hours Cost by Month shows shift pay per rental and Supplies Orders tracks cleaning supplies. "
        f"{len(tools)} calculators answer weekly questions: which car to clean first, whether the buffer is long enough, whether a delivery fee covers driver time and fuel, which driver takes a clashing run, which days are short of staff, what a weekend needs, and what the pay run costs. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to detailers, drivers, the assistant, the manager, the owner, the bookkeeper, the accountant, suppliers and renters.\n\n"
        "This is part six of the Car Rental Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data. A one-car host can use the turnaround board and task lists without staff. Renters appear as a first name and an initial, with dates only. It helps you keep track of your work and does not promise results. Check your local rules for employment, records and tax; confirm tax questions with your adviser."),
    "features": ["Turnaround board with ready, tight or late verdicts", "Late-ready risk list ranked by slack", "Delivery run planner with fees against cost", "Fee check and profit for every delivery zone", "Driver clash check and assignment",
                 "Roster check against bookings", "Hours cost per rental against your own history", "Pay calculator with employer costs", "Task completion score by role", f"{len(tools)} calculators for daily decisions",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p6', slug='car-rental-operations', profession='Car Rental Business', name='Turnaround, Runs and Staff',
         tagline='Cars ready on time, runs that pay and a roster that fits the bookings', price_usd=29,
         colors={"primary": "#1D3557", "accent": "#E63946"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Turnaround, delivery runs and staff"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cr6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
