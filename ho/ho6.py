"""Home Management suite - part 6: Family Calendar, Pets and Vehicles."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho6_lists import *
from ho6_tables import *
from ho6_tools import tools, V, F as FX
import ho6_data as D

SUITE = 'fx-20261118-home-management'
NOTE = "Sample wording: adapt it to your own household and your local rules; check the school, the clinic and the garage for their own dates."
def FW(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def W(c, op, v): return (c, op, v)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('event_sheet', 'Event Sheet', 'One calendar event with its driver and clashes', 'events.event_id', FW(
        ('Date', 'events.date'), ('End date', 'events.end_date'), ('Person', 'events.person'), ('Kind', 'events.kind'), ('Title', 'events.title'), ('Starts', 'events.start'), ('Ends', 'events.end'),
        ('Place', 'events.place'), ('Driver', 'events.driver'), ('Carpool', 'events.carpool'), ('Minutes', 'events.minutes'), ('Adults free that evening', 'events.free'), ('Adult 2 shift', 'events.shift'),
        ('Later events, same driver, same time', 'events.dclash'), ('Later events, same person, same time', 'events.pclash')) + [
        FF('Days from today to the event', '%s-{today}' % LK('events', 'event_id', 'date'), 'int'), FF('Events on the same day', 'COUNTIFS({range:events.date},%s)' % LK('events', 'event_id', 'date'), 'int')]),
    FORM('activity_card', 'Activity Card', 'One weekly activity: times, driver, sessions', 'events.title', FW(
        ('Person', 'events.person'), ('Place', 'events.place'), ('Starts', 'events.start'), ('Ends', 'events.end'), ('Minutes', 'events.minutes'), ('Driver', 'events.driver'), ('Carpool', 'events.carpool'), ('Adult 2 name', 'events.a2_name'),
        ('Carpool family', 'events.cp_name')) + [
        FF('Sessions in the next 4 weeks', 'COUNTIFS({range:events.title},{pick},{range:events.date},">="&{today},{range:events.date},"<"&({today}+28))', 'int'),
        FF('Sessions in the last 4 weeks', 'COUNTIFS({range:events.title},{pick},{range:events.date},">="&({today}-28),{range:events.date},"<"&{today})', 'int'),
        FF('Minutes in the next 4 weeks', 'SUMIFS({range:events.minutes},{range:events.title},{pick},{range:events.date},">="&{today},{range:events.date},"<"&({today}+28))', 'int')]),
    FORM('carpool_day', 'Carpool Day Sheet', 'One week of driving for one adult', 'driving.no', FW(
        ('Weeks ago', 'driving.weeks_ago'), ('Adult', 'driving.adult'), ('Week starting', 'driving.week_start'), ('Trips driven', 'driving.trips'), ('Event minutes driven', 'driving.minutes'),
        ('Trips driven by both adults', 'driving.all'), ('Share of the week trips', 'driving.share'), ('Within the agreed margin, 1 or 0', 'driving.within'), ('Driver conflicts that week', 'driving.wk_conf'),
        ('Share of the 4 weeks to this one', 'driving.share4_txt')) + [
        FF('Carpool lifts that week', 'COUNTIFS({range:events.carpool},{list:yesno.yes},{range:events.date},">="&%s,{range:events.date},"<"&(%s+7))' % (LK('driving', 'no', 'week_start'), LK('driving', 'no', 'week_start')), 'int'),
        FF('Agreed share for adult 2', '{set:agreed_drive_share}', 'pct')]),
    FORM('conflict_sheet', 'Conflict Review Sheet', 'One clash: both events, the overlap and what to do', 'conflicts.no', FW(
        ('Date', 'conflicts.date'), ('Days to it', 'conflicts.days_to'), ('Weekday', 'conflicts.weekday'), ('Kind of conflict', 'conflicts.type'), ('Driver or person', 'conflicts.who'), ('First event', 'conflicts.event_a'),
        ('First starts', 'conflicts.a_start'), ('Second event', 'conflicts.event_b'), ('Second starts', 'conflicts.b_start'), ('Overlap, minutes', 'conflicts.overlap'), ('Adults free', 'conflicts.free'), ('What to do', 'conflicts.advice'),
        ('Adult 2', 'conflicts.a2_name'), ('Adult 2 phone', 'conflicts.a2_phone'), ('Carpool family', 'conflicts.cp_name'), ('Carpool family phone', 'conflicts.cp_phone')) + [
        FF('Minutes between the two starts', 'ROUND((%s-%s)*1440,0)' % (LK('conflicts', 'no', 'b_start'), LK('conflicts', 'no', 'a_start')), 'int')]),
    FORM('gift_sheet', 'Birthday And Gift Sheet', 'One birthday or gift date with the gift status', 'gifts.gift_id', FW(
        ('Name', 'gifts.name'), ('Relation', 'gifts.relation'), ('Date', 'gifts.date'), ('Age turning', 'gifts.age_turning'), ('Gift idea', 'gifts.gift_idea'), ('Status', 'gifts.status'), ('Cost line', 'gifts.cost'),
        ('Days left', 'gifts.days_left'), ('Buy by', 'gifts.buy_by')) + [
        FF('Days to the buy-by date', '%s-{today}' % LK('gifts', 'gift_id', 'buy_by'), 'int'), FF('Cost lines of all gifts', 'SUM({range:gifts.cost})', 'money')]),
    FORM('visitor_sheet', 'Visitor Stay Sheet', 'One stay: dates, beds, room and the clash check', 'visitors.visitor', FW(
        ('Arrive', 'visitors.arrive'), ('Leave', 'visitors.leave'), ('Beds needed', 'visitors.beds'), ('Room', 'visitors.room'), ('Phone', 'visitors.phone'), ('Nights', 'visitors.nights'), ('Dinners to add', 'visitors.dinners'),
        ('Beds in use on arrival', 'visitors.at_arr'), ('Over the beds typed by', 'visitors.over_by'), ('Other stays overlapping', 'visitors.clash_n'), ('Beds check', 'visitors.status'), ('Days to the arrival', 'visitors.to_arrive'),
        ('Grandparent', 'visitors.gp_name')) + [
        FF('Beds you have for visitors', '{set:beds_total}', 'int'), FF('Beds free on arrival', '{set:beds_total}-%s' % LK('visitors', 'visitor', 'at_arr'), 'int')]),
    FORM('holiday_sheet', 'Holiday Plan Sheet', 'The family trip: dates and who to tell', 'school_view.no', FW(
        ('Term or break', 'school_view.term'), ('Kind', 'school_view.kind'), ('Starts', 'school_view.start'), ('Ends', 'school_view.end'), ('Days to the start', 'school_view.to_start'), ('Family trip', 'school_view.trip_date'),
        ('Back from the trip', 'school_view.trip_end'), ('Check travel documents by', 'school_view.check_by'), ('School office', 'school_view.so_name'), ('School office phone', 'school_view.so_phone'), ('Neighbour', 'school_view.nb_name'),
        ('Neighbour phone', 'school_view.nb_phone'), ('Child 1', 'school_view.c1_name'), ('Child 2', 'school_view.c2_name')) + [
        FF('Days to the trip', '{set:trip_date}-{today}', 'int'), FF('Days away', '{set:trip_days}', 'int'), FF('Weeks to the trip', 'ROUND(({set:trip_date}-{today})/7,1)', 'num')]),
    FORM('pet_care_sheet', 'Pet Care Sheet', 'One pet care date: interval, last done, next due', 'pet_sched.ps_id', FW(
        ('Pet', 'pet_sched.pet'), ('Task', 'pet_sched.task'), ('Interval, days', 'pet_sched.interval_days'), ('Visit time', 'pet_sched.at'), ('Last done', 'pet_sched.last_done'), ('Next due', 'pet_sched.next_due'),
        ('Days left', 'pet_sched.days_left'), ('Status', 'pet_sched.status'), ('Vet clinic', 'pet_sched.vet_name'), ('Vet clinic phone', 'pet_sched.vet_phone')) + [
        FF('Care dates of this pet, next 90 days', 'COUNTIFS({range:pet_sched.pet},%s,{range:pet_sched.days_left},">=0",{range:pet_sched.days_left},"<=90")' % LK('pet_sched', 'ps_id', 'pet'), 'int')]),
    FORM('pet_food_sheet', 'Pet Food Stock Sheet', 'One pet: food left in days and the reorder date', 'pet_food.pet_id', FW(
        ('Days of food left', 'pet_food.days_left'), ('Reorder by', 'pet_food.reorder_date')) + [
        FF('Pet', 'INDEX({range:pets.pet},MATCH({pick},{range:pets.pet_id},0))', 'text'), FF('Species', 'INDEX({range:pets.species},MATCH({pick},{range:pets.pet_id},0))', 'text'),
        FF('Daily amount typed, grams', '{set:daily_g_1}', 'int'),
        FF('Latest food bag, kg', 'SUMIFS({range:pet_care.qty_kg},{range:pet_care.pet},INDEX({range:pets.pet},MATCH({pick},{range:pets.pet_id},0)),{range:pet_care.last_bag},1)', 'num'),
        FF('Days to the reorder date', '%s-{today}' % LK('pet_food', 'pet_id', 'reorder_date'), 'int'), FF('Reorder this many days before the end', '{set:reorder_days}', 'int')]),
    FORM('vehicle_service_sheet', 'Vehicle Service Sheet', 'One vehicle: mileage and the next service', 'vehicle_est.vehicle_id', FW(
        ('Km to the next service', 'vehicle_est.km_left'), ('Estimated service date', 'vehicle_est.est_date')) + [
        FF('Vehicle', 'INDEX({range:vehicles.vehicle},MATCH({pick},{range:vehicles.vehicle_id},0))', 'text'), FF('Year', 'INDEX({range:vehicles.year},MATCH({pick},{range:vehicles.vehicle_id},0))', 'int'),
        FF('Latest mileage reading, km', 'SUMIFS({range:vehicle_log.km},{range:vehicle_log.vehicle},INDEX({range:vehicles.vehicle},MATCH({pick},{range:vehicles.vehicle_id},0)),{range:vehicle_log.lm},1)', 'int'),
        FF('Mileage at the last service, km', 'SUMIFS({range:vehicle_log.km},{range:vehicle_log.vehicle},INDEX({range:vehicles.vehicle},MATCH({pick},{range:vehicles.vehicle_id},0)),{range:vehicle_log.ls},1)', 'int'),
        FF('Km a day, from two readings', 'SUMIFS({range:vehicle_log.rate},{range:vehicle_log.vehicle},INDEX({range:vehicles.vehicle},MATCH({pick},{range:vehicles.vehicle_id},0)),{range:vehicle_log.lm},1)', 'num'),
        FF('Days to the estimated date', '%s-{today}' % LK('vehicle_est', 'vehicle_id', 'est_date'), 'int'), FF('Service interval typed, km', '{set:service_km}', 'int')]),
    FORM('vehicle_renewal_sheet', 'Vehicle Renewal Sheet', 'One vehicle date: last done, next date, status', 'vehicle_dates.vd_id', FW(
        ('Vehicle', 'vehicle_dates.vehicle'), ('Kind', 'vehicle_dates.kind'), ('Interval, days', 'vehicle_dates.interval_days'), ('Last done', 'vehicle_dates.last_done'), ('Next date', 'vehicle_dates.date'), ('Days left', 'vehicle_dates.days_left'),
        ('Status', 'vehicle_dates.status'), ('Latest reading, km', 'vehicle_dates.km_now'), ('Car mechanic', 'vehicle_dates.cm_name'), ('Car mechanic phone', 'vehicle_dates.cm_phone')) + [
        FF('Start by, with the soon window', '%s-{set:soon_days}' % LK('vehicle_dates', 'vd_id', 'date'), 'date'), FF('Days to start', '%s-{set:soon_days}-0' % LK('vehicle_dates', 'vd_id', 'days_left'), 'int')]),
    FORM('term_sheet', 'School Term Sheet', 'One term or break: days, school days and days left', 'terms.term_id', FW(
        ('Term or break', 'terms.term'), ('Kind', 'terms.kind'), ('Starts', 'terms.start'), ('Ends', 'terms.end'), ('Days', 'terms.days'), ('Weekdays', 'terms.wdays'), ('School days', 'terms.school_days'),
        ('Current term, 1 or 0', 'terms.cur'), ('School days left', 'terms.left_days'), ('Days to the start', 'terms.to_start')) + [
        FF('School days as a share of the weekdays', 'IFERROR(%s/%s,0)' % (LK('terms', 'term_id', 'school_days'), LK('terms', 'term_id', 'wdays')), 'pct'),
        FF('Breaks in the list', 'COUNTIFS({range:terms.kind},%s)' % T_BREAK, 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('week_doc', 'Week At A Glance', 'Week at a glance, the fridge page, one day', 'shifts.shift_id', [
        'Week at a glance of {set:household}, dated {today}. Day: {col:shifts.date}, {col:shifts.weekday}. Week starting {col:shifts.wk}.',
        'Events starting that day: {col:shifts.events_n}, of which in the evening: {col:shifts.evening_n}. Adult 1 late day (1 yes, 0 no): {col:shifts.adult1_late}. Adult 2 shift: {col:shifts.adult2_shift}.',
        'Adults free for the evening: {col:shifts.adults_free} ({col:shifts.free_label}). Babysitter to call: {col:shifts.bs_name}, {col:shifts.bs_phone}.',
        'Print the seven days on one page, put it on the fridge and mark the lifts with the driver.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('month_doc', 'Month Calendar Page', 'Month calendar page: events in the month', 'shifts.shift_id', [
        'Month calendar of {set:household}, dated {today}. Day: {col:shifts.date} ({col:shifts.weekday}). Events in this month: {col:shifts.m_events}.',
        'Events covering this day: {col:shifts.busy_n}. In a school break (1 yes, 0 no): {col:shifts.in_break}. Child-care gap day (1 yes, 0 no): {col:shifts.gap}.',
        'Write each event under its day with the start time, the place and the driver. A day with a gap in a school break needs a plan for the children.',
        'Check the page against the family calendar every Sunday.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('rota_doc', 'Carpool And Activity Rota', 'Carpool and activity rota: one adult, one week', 'driving.no', [
        'Carpool and activity rota of {set:household}, dated {today}. Week starting {col:driving.week_start}, {col:driving.weeks_ago} weeks ago. Adult: {col:driving.adult}.',
        'Trips driven: {col:driving.trips} of {col:driving.all}. Event minutes driven: {col:driving.minutes}. Share of the week: {col:driving.share}. Share over four weeks: {col:driving.share4_txt}.',
        'Within the margin of the agreed share (1 yes, 0 no): {col:driving.within}. Driver conflicts that week: {col:driving.wk_conf}. Adult 1 phone: {col:driving.a1_phone}.',
        'A view for a talk about the rota, not a score. Agree the next weeks together.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('conflict_doc', 'Conflict Report', 'Conflict report for the week, one clash', 'conflicts.no', [
        'Conflict report of {set:household}, dated {today}. {col:conflicts.weekday} {col:conflicts.date}, in {col:conflicts.days_to} days. Kind: {col:conflicts.type}. Driver or person: {col:conflicts.who}.',
        'First event: {col:conflicts.event_a} at {col:conflicts.a_start}. Second event: {col:conflicts.event_b} at {col:conflicts.b_start}. Overlap: {col:conflicts.overlap} minutes.',
        'Adults free: {col:conflicts.free}. What to do: {col:conflicts.advice}. Carpool family: {col:conflicts.cp_name}, {col:conflicts.cp_phone}. Adult 2: {col:conflicts.a2_name}.',
        'Write the agreed driver for each event and the date it was settled.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('gift_doc', 'Birthdays And Gifts List', 'Birthdays and gifts list for the next 60 days', 'gift_plan.no', [
        'Birthdays and gifts of {set:household}, dated {today}. Date {col:gift_plan.no}: {col:gift_plan.name} on {col:gift_plan.date}, {col:gift_plan.days_left} days left.',
        'Gift idea: {col:gift_plan.gift_idea}. Status: {col:gift_plan.status}. Cost line: {col:gift_plan.cost}. Buy by: {col:gift_plan.buy_by}. Next step: {col:gift_plan.step}.',
        'Names and dates only. Child 1: {col:gift_plan.c1_name}, adult 1: {col:gift_plan.a1_name}.',
        'Tick the step when it is done and pass the list to the next person.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('stay_doc', 'Visitor Stay Sheet Page', 'Visitor and holiday stay sheet', 'visitors.visitor', [
        'Stay sheet of {set:household}, dated {today}. Visitor: {col:visitors.visitor}. Arrives {col:visitors.arrive}, leaves {col:visitors.leave}, {col:visitors.nights} nights.',
        'Beds needed: {col:visitors.beds}. Room: {col:visitors.room}. Dinners to add: {col:visitors.dinners}. Beds check: {col:visitors.status}. Phone: {col:visitors.phone}.',
        'Beds in use on arrival: {col:visitors.at_arr} of the {set:beds_total} typed. Grandparent to tell: {col:visitors.gp_name}, {col:visitors.gp_phone}.',
        'Give this page to the guest with the house routines.'], ['Adult 1', 'Guest'], NOTE),
    DOC('terms_doc', 'School Terms And Breaks Page', 'School terms and breaks page', 'school_view.no', [
        'School terms of {set:household}, dated {today}. {col:school_view.term} ({col:school_view.kind}): {col:school_view.start} to {col:school_view.end}, starting in {col:school_view.to_start} days.',
        'School days left: {col:school_view.left_days}. Child-care gap days in the break: {col:school_view.gap_days}. Family trip: {col:school_view.trip_date} to {col:school_view.trip_end}.',
        'Check travel documents by {col:school_view.check_by}. School office: {col:school_view.so_name}, {col:school_view.so_phone}. Neighbour: {col:school_view.nb_name}.',
        'Confirm the term dates with the school office each year.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('pet_doc', 'Pet Care Dates Page', 'Pet care dates page, dates only', 'pet_sched.ps_id', [
        'Pet care dates of {set:household}, dated {today}. Pet: {col:pet_sched.pet}. Task: {col:pet_sched.task}, every {col:pet_sched.interval_days} days (typed).',
        'Last done: {col:pet_sched.last_done}. Next due: {col:pet_sched.next_due}, {col:pet_sched.days_left} days left. Status: {col:pet_sched.status}. Visit time: {col:pet_sched.at}.',
        'Vet clinic: {col:pet_sched.vet_name}, {col:pet_sched.vet_phone}. Dates only: no treatments, no health details are written here.',
        'Ask the clinic for the interval that suits your pet.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('food_doc', 'Pet Food And Reorder Page', 'Pet food and reorder page', 'pet_food.pet_id', [
        'Pet food stock of {set:household}, dated {today}. Pet ID: {col:pet_food.pet_id}. Days of food left: {col:pet_food.days_left}.',
        'Reorder by: {col:pet_food.reorder_date}, {set:reorder_days} days before it runs out. The days come from the latest food bag in the Pet care log and the daily grams typed in Settings.',
        'Check the bag when you open it and type the new bag in the log.',
        'No feeding advice is written here, only the stock and the dates.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('service_doc', 'Vehicle Service Dates Page', 'Vehicle service estimate page', 'vehicle_est.vehicle_id', [
        'Vehicle service of {set:household}, dated {today}. Vehicle ID: {col:vehicle_est.vehicle_id}. Km to the next service: {col:vehicle_est.km_left}.',
        'Estimated service date: {col:vehicle_est.est_date}, by mileage or by the typed number of days, whichever comes first. The interval typed is {set:service_km} km or {set:service_days} days (typical, check the manual).',
        'Type the mileage at every fuel stop or service to keep the estimate close.',
        'Book the garage a few weeks before the date.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('renew_doc', 'Vehicle And Pet Renewals Page', 'Next 90 days renewals page for vehicles and pets', 'vehicle_dates.vd_id', [
        'Renewals of {set:household}, dated {today}. {col:vehicle_dates.vehicle}: {col:vehicle_dates.kind}, last done {col:vehicle_dates.last_done}, next {col:vehicle_dates.date}.',
        'Days left: {col:vehicle_dates.days_left}. Status: {col:vehicle_dates.status}. Latest reading: {col:vehicle_dates.km_now} km. Car mechanic: {col:vehicle_dates.cm_name}, {col:vehicle_dates.cm_phone}.',
        'Pet dates are on the Pet care schedule sheet; read both lists together for the next 90 days.',
        'Start each renewal in the soon window of {set:soon_days} days.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('sitter_cal_doc', 'Sitter Calendar', 'Sitter calendar: the children week, who drives, who to call', 'shifts.shift_id', [
        'Sitter calendar of {set:household}, for {col:shifts.date} ({col:shifts.weekday}). Welcome, {col:shifts.bs_name}.',
        'Events that day: {col:shifts.busy_n}, in the evening: {col:shifts.evening_n}. Adult 2 works the {col:shifts.adult2_shift} shift. Adults free for the evening: {col:shifts.adults_free}.',
        'The drivers and the places are on the family calendar sheet. First call: the adults, then the neighbour. Your number: {col:shifts.bs_phone}.',
        'No health details are written here; ask us before the evening.'], ['Adult 1', 'Babysitter'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('sunday_glance', 'Sunday Calendar Glance', 'shifts', 'shifts.date', [('Open the Busiest week ahead and read the total', 0), ('Read the Conflict finder for the week', 0), ('Settle each clash with a second driver', 1), ('Print the week at a glance', 1), ('Put it on the fridge', 1), ('Check the evenings with no adult free', 1)]),
    CHK('conflict_week', 'Week With A Conflict', 'events', 'events.date', [('Read the two events and the overlap', -7), ('Check the adults free that evening', -6), ('Ask the carpool family to take one lift', -5), ('Ask the grandparent if it still clashes', -4), ('Tell the children who drives', -2), ('Note the agreed driver on the event', -1)]),
    CHK('back_school', 'Back To School New Term', 'terms', 'terms.start', [('Check the term dates with the school office', -28), ('Book the activities for the new term', -21), ('Type the activities in the calendar', -14), ('Check the uniform and the bags', -7), ('Plan the first week of lifts', -3), ('Send the carpool family the new times', -2)]),
    CHK('break_week', 'School Break Week', 'terms', 'terms.start', [('Read the child-care gap days of the break', -28), ('Ask the grandparent and the carpool family for days', -21), ('Book a camp or a sitter for the gap days', -14), ('Type the plan for each weekday', -7), ('Check the visitors and the beds', -5), ('Tell the children the week', -1)]),
    CHK('birthday', 'Birthday Gift To Give', 'gifts', 'gifts.date', [('Choose the gift idea', -30), ('Buy the gift', -14), ('Wrap the gift', -3), ('Write the card', -2), ('Give the gift on the day', 0), ('Type the status as given', 1)]),
    CHK('visitors_arrive', 'Visitors Arriving', 'visitors', 'visitors.arrive', [('Check the beds against the other stays', -14), ('Make up the room', -2), ('Add the dinners to the meal plan', -3), ('Tell the school and the carpool family', -2), ('Leave a key and the routines page', -1), ('Type the leave date and the next visit', 0)]),
    CHK('holiday_trip', 'Holiday Trip Checklist', 'events', 'events.date', [('Check every travel document against the trip', -60), ('Tell the school office the dates', -28), ('Book the dog walker or the pet sitter', -21), ('Tell the neighbour and leave the spare key', -7), ('Cancel the activities and the lifts', -7), ('Check the pet food and the vehicle dates', -5), ('Print the sitter calendar', -2)]),
    CHK('pet_round', 'Pet Care Round Dates', 'pet_care', 'pet_care.date', [('Read the next due dates of every pet', -21), ('Ask the clinic or the groomer for a date', -14), ('Type the booked date', -10), ('Tell the dog walker', -2), ('Do the visit', 0), ('Type the new last-done date', 1)]),
    CHK('service_day', 'Vehicle Service Day', 'vehicle_log', 'vehicle_log.date', [('Read the km to the next service', -35), ('Ask the garage for a date', -28), ('Book the date and a lift home', -21), ('Type the mileage the day before', -1), ('Take the car in', 0), ('Type the service in the vehicle log', 0)]),
    CHK('renewals_vehicle', 'Vehicle Renewals Checklist', 'vehicle_log', 'vehicle_log.date', [('Read the vehicle dates of the next 90 days', -90), ('Ask for insurance offers', -45), ('Book the annual test', -30), ('Renew the registration', -14), ('Type the new dates in the vehicle log', 0), ('File the new papers', 3)]),
    CHK('year_setup', 'Year Calendar Set Up', 'team', 'team.start', [('Type the school terms and breaks', 0), ('Type the birthdays and the gift ideas', 1), ('Type the activities of each child', 2), ('Type the work pattern of both adults', 3), ('Type the vehicle and pet dates', 4), ('Read the busiest week ahead', 5)]),
    CHK('single_first', 'Single Adult First Calendar', 'team', 'team.start', [('Replace the demo data with your own', 0), ('Type your events and your work pattern', 1), ('Type the birthdays and the gift ideas', 2), ('Type the vehicle and renewal dates', 3), ('Leave the children, carpool and pet rows empty', 3), ('Read the busiest week ahead', 4)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('a2_dup', 'Adult 2: two events at the same time', 'conflicts', 'conflicts.a2_phone', 'Hi {a2_name}, {weekday} {date} has two events at the same time ({event_a} and {event_b}), you are down to drive both, can we find a second driver? {household}'),
    M('a1_late', 'Adult 1: a late day, take an event', 'events', 'events.a1_phone', 'Hi {a1_name}, I am on a late day on {date}, can you take {title} at {start}? {household}'),
    M('a1_share', 'Adult 1: your driving share', 'driving', 'driving.a1_phone', 'Hi {a1_name}, {adult} drives {share4_txt} of the trips over the last 4 weeks, shall we look at the rota? {household}'),
    M('a2_shift', 'Adult 2: your shift, I take the event', 'events', 'events.a2_phone', 'Hi {a2_name}, your shift on {date} is {shift}, I will take {title} at {start}. {household}'),
    M('a2_busy', 'Adult 2: a busy week ahead', 'busy', 'busy.a2_phone', 'Hi {a2_name}, the week of {week_start} has {total} items, rank {rank} of the next 12 weeks, 1 is the busiest. {household}'),
    M('a2_trip', 'Adult 2: the trip and your document', 'school_view', 'school_view.a2_phone', 'Hi {a2_name}, the family trip is on {trip_date}, please check your travel document before {check_by}. {household}'),
    M('c1_football', 'Child 1: practice and who takes you', 'events', 'events.c1_phone', 'Hi {c1_name}, {title} is on {date} at {start}, {driver} takes you. {household}'),
    M('c1_piano', 'Child 1: the lesson time and place', 'events', 'events.c1_phone', 'Hi {c1_name}, your {title} on {date} is at {start} at {place}. {household}'),
    M('c1_birthday', 'Child 1: a birthday for the gift list', 'gift_plan', 'gift_plan.c1_phone', 'Hi {c1_name}, the birthday of {name} is on {date}, the gift idea is {gift_idea}, shall we choose it together? {household}'),
    M('c2_swim', 'Child 2: pack your bag', 'events', 'events.c2_phone', 'Hi {c2_name}, {title} is on {date} at {start}, please pack your bag the evening before. {household}'),
    M('c2_party', 'Child 2: the party start and the lift', 'events', 'events.c2_phone', 'Hi {c2_name}, the event on {date} starts at {start} at {place}, {driver} takes you. {household}'),
    M('c2_art', 'Child 2: club time', 'events', 'events.c2_phone', 'Hi {c2_name}, {title} is on {date} at {start}. {household}'),
    M('gp_pickup', 'Grandparent: school pick-up', 'events', 'events.gp_phone', 'Hello {gp_name}, please do the school pick-up on {date} at {end}, the visit is on the calendar. {household}'),
    M('gp_holiday', 'Grandparent: we are on holiday', 'events', 'events.gp_phone', 'Hello {gp_name}, we are away from {date} to {end_date}, the dog goes to the walker. {household}'),
    M('gp_visit', 'Grandparent: your visit', 'visitors', 'visitors.gp_phone', 'Hello {gp_name}, {visitor} visits from {arrive} to {leave}, the room is {room}. {household}'),
    M('bs_out', 'Babysitter: we are out', 'events', 'events.bs_phone', 'Hello {bs_name}, we are out on {date} from {start} to {end}, the children week is attached. {household}'),
    M('bs_collect', 'Babysitter: who collects', 'events', 'events.bs_phone', 'Hello {bs_name}, the activity on {date} ends at {end}, {driver} collects. {household}'),
    M('cp_drive', 'Carpool family: can you drive', 'events', 'events.cp_phone', 'Hello {cp_name}, can you drive on {date} to {place} at {start}, we take the next week? {household}'),
    M('cp_thanks', 'Carpool family: thank you, our turn next', 'events', 'events.cp_phone', 'Hello {cp_name}, thank you for driving on {date}, it is our turn on {next_date}. {household}'),
    M('cp_moved', 'Carpool family: a time moved', 'events', 'events.cp_phone', 'Hello {cp_name}, the {title} on {date} moved to {start}. {household}'),
    M('cp_clash', 'Carpool family: a clash, take both', 'conflicts', 'conflicts.cp_phone', 'Hello {cp_name}, we have a clash on {date} ({event_a} and {event_b}), can you take both children? {household}'),
    M('so_away', 'School office: away for a family trip', 'school_view', 'school_view.so_phone', 'Hello {so_name}, {c1_name} and {c2_name} are away on {trip_date} for a family trip until {trip_end}. {household}'),
    M('so_terms', 'School office: confirm the term dates', 'school_view', 'school_view.so_phone', 'Hello {so_name}, please confirm the term dates for {term}, starting {start}. {household}'),
    M('nb_away', 'Neighbour: we are away', 'school_view', 'school_view.nb_phone', 'Hello {nb_name}, we are away from {trip_date} to {trip_end}, please keep the spare key. {household}'),
    M('vet_date', 'Vet clinic: ask for a date', 'pet_sched', 'pet_sched.vet_phone', 'Hello {vet_name}, we would like a date for {pet} around {next_due}, dates only. {household}'),
    M('vet_confirm', 'Vet clinic: confirm the visit', 'pet_sched', 'pet_sched.vet_phone', 'Hello {vet_name}, please confirm the visit of {pet} on {next_due} at {at}. {household}'),
    M('dw_cancel', 'Dog walker: cancel the walks', 'events', 'events.dw_phone', 'Hello {dw_name}, the walks on {date} are cancelled, we are at the {title}. {household}'),
    M('dw_confirm', 'Dog walker: confirm the walks', 'events', 'events.dw_phone', 'Hello {dw_name}, please confirm the walks from {date} to {end_date}. {household}'),
    M('cm_test', 'Car mechanic: book the test', 'vehicle_dates', 'vehicle_dates.cm_phone', 'Hello {cm_name}, please book the {kind} of the {vehicle} around {date}. {household}'),
    M('cm_service', 'Car mechanic: confirm the service', 'vehicle_dates', 'vehicle_dates.cm_phone', 'Hello {cm_name}, please confirm the {kind} of the {vehicle} on {date}, mileage {km_now}. {household}'),
    M('guest_stay', 'Guest: your stay', 'visitors', 'visitors.phone', 'Hello {visitor}, your stay is from {arrive} to {leave}, the room is {room}. {household}'),
    M('guest_thanks', 'Guest: thank you for the visit', 'visitors', 'visitors.phone', 'Hello {visitor}, thank you for the visit that ended on {leave}, you are welcome again. {household}'),
    M('hm_week', 'Household: the week is on the fridge', 'busy', 'busy.a1_phone', 'Hello {a1_name}, the calendar for the week of {week_start} is on the fridge, {total} items. {household}'),
    M('hm_birth', 'Household member: birthdays and gifts', 'gift_plan', 'gift_plan.a1_phone', 'Hello {a1_name}, birthdays in the next 60 days: {name} on {date}, gift status {status}. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def C_(*a): return 'COUNTIFS(' + ','.join(a) + ')'
K = lambda label, f, fmt='int', **kw: KPI(label, f, fmt, **kw)
def DW(col, a, b): return '%s,">="&%s,%s,"<="&%s' % (col, a, col, b)
TD = '{today}'
WEEK = DW(ER('date'), WS, '(%s+6)' % WS)
L4 = DW(ER('date'), '(%s-28)' % WS, '(%s-1)' % WS)
A1T, A2T = tok('adult', 'Adult 1'), tok('adult', 'Adult 2')
def NEXTD(c): return 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),"")' % (c, c)
BKS = 'IFERROR(SMALL(%s,1),"")' % TR('bk')
kpis = [
    K('Events this week', C_(WEEK)),
    K('Events next 7 days', C_(DW(ER('date'), TD, TD + '+6'))),
    K('Events next 30 days', C_(DW(ER('date'), TD, TD + '+29'))),
    K('Conflicts this week', C_(ER('conf'), '1', WEEK), alert={"when": "> 0", "style": "bad"}),
    K('Conflicts next 14 days', C_(ER('conf'), '1', DW(ER('date'), TD, TD + '+13')), alert={"when": "> 0", "style": "warn"}),
    K('Double-booked drivers next 14 days', C_(ER('dclash'), '">0"', DW(ER('date'), TD, TD + '+13')), alert={"when": "> 0", "style": "warn"}),
    K('Evenings, one adult free, next 14 days', C_(DW(SR('date'), TD, TD + '+13'), SR('adults_free'), '1')),
    K('Evenings, both adults free, next 14 days', C_(DW(SR('date'), TD, TD + '+13'), SR('adults_free'), '2')),
    K('Busiest week ahead, items', 'MAX(%s)' % BR('total')),
    K('Quietest week ahead, items', 'IF(COUNT(%s)=0,"",MIN(%s))' % (BR('total'), BR('total'))),
    K('Activities per week, last 4 weeks', 'ROUND(%s/4,1)' % C_(ER('kind'), K_ACT, L4), 'num'),
    K('Trips driven by adult 1, last 4 weeks', 'SUMIFS(%s,%s,%s,%s,"<=4")' % (DR('trips'), DR('adult'), A1T, DR('weeks_ago'))),
    K('Trips driven by adult 2, last 4 weeks', 'SUMIFS(%s,%s,%s,%s,"<=4")' % (DR('trips'), DR('adult'), A2T, DR('weeks_ago'))),
    K('Trips by carpool families, last 4 weeks', C_(ER('driver'), D_CP, L4)),
    K('School days left this term', 'SUMIFS(%s,%s,1)' % (TR('left_days'), TR('cur'))),
    K('Days to the next break', 'IF(%s="","",%s-{today})' % (BKS, BKS)),
    K('Child-care gap days in the next break', 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0)))' % (BKS, TR('gap_days'), BKS, TR('bk')), alert={"when": "> 0", "style": "warn"}),
    K('Birthdays in the next 60 days', 'SUM(%s)' % GR_('in_win')),
    K('Gifts still to buy', C_(GR_('in_win'), '1', GR_('status'), G_IDEA), alert={"when": "> 0", "style": "warn"}),
    K('Gifts wrapped or given', '%s+%s' % (C_(GR_('status'), G_WRAP), C_(GR_('status'), G_GIVEN))),
    K('Visitors in the next 30 days', C_(VSR('arrive'), '"<="&({today}+29)', VSR('leave'), '">="&{today}')),
    K('Visitor beds used, peak', 'MAX(%s)' % VSR('at_arr')),
    K('Pet care dates in the next 30 days', C_(PSR('days_left'), '">=0"', PSR('days_left'), '"<=30"')),
    K('Pet food days left, lowest', 'IF(COUNT(%s)=0,"",MIN(%s))' % (PFR('days_left'), PFR('days_left')), alert={"when": "<= {set:reorder_days}", "style": "warn"}),
    K('Next vet visit, days', NEXTD(PSR('vetd'))),
    K('Vehicle dates in the next 90 days', C_(VDR('days_left'), '">=0"', VDR('days_left'), '"<=90"')),
    K('Next annual test, days', NEXTD(VDR('adt'))),
    K('Next insurance renewal, days', NEXTD(VDR('ins'))),
    K('Estimated km to the next service, lowest', 'IF(COUNT(%s)=0,"",MIN(%s))' % (VER('km_left'), VER('km_left'))),
    K('Days to the family trip', 'IF({set:trip_date}="","",{set:trip_date}-{today})'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Family Calendar Dashboard", "kpis": kpis,
    "monthly": {"title": "Event minutes and cost lines by month", "date": "events.date", "series": [
        {"label": "Event minutes", "sum": "events.minutes", "date": "events.date"}, {"label": "Gift cost lines", "sum": "gifts.cost", "date": "gifts.date"},
        {"label": "Pet care cost lines", "sum": "pet_care.cost", "date": "pet_care.date"}, {"label": "Vehicle cost lines", "sum": "vehicle_log.cost", "date": "vehicle_log.date"}]},
    "breakdowns": [{"title": "Events by kind", "by": "events.kind", "agg": "count"}, {"title": "Events by person", "by": "events.person", "agg": "count"},
                   {"title": "Events by driver", "by": "events.driver", "agg": "count"}, {"title": "Pet care by task", "by": "pet_care.task", "agg": "count"}]}
YESV = '{list:yesno.yes}'
insights = {"filters": [{"label": "Person", "list": "epeople"}, {"label": "Driver", "list": "driver"}],
    "gauges": [
        {"title": "Weeks without a driver conflict, last 12", "num": AGG('count', 'driving', where=[W('wk_conf', '=', 0)]), "den": AGG('count', 'driving', where=[W('wk_conf', '>=', 0)])},
        {"title": "Trips with a driver, next 14 days", "num": AGG('count', 'events', where=[W('lift', '=', 1)]), "den": AGG('count', 'events', where=[W('lift', '>=', 0)])},
        {"title": "Gifts bought or wrapped before the date", "num": AGG('count', 'gifts', where=[W('in_win', '=', 1), W('bw', '=', 1)]), "den": AGG('count', 'gifts', where=[W('in_win', '=', 1)])},
        {"title": "Pet food above the reorder level", "num": AGG('count', 'pet_food', where=[W('days_left', '>', '{set:reorder_days}')]), "den": AGG('count', 'pet_food', where=[W('days_left', '>=', 0)])},
        {"title": "Vehicle dates not overdue", "num": AGG('count', 'vehicle_dates', where=[W('days_left', '>=', 0)]), "den": AGG('count', 'vehicle_dates', where=[W('days_left', '>=', -100000)])},
        {"title": "Driving shared within 10 points", "num": AGG('count', 'driving', where=[W('within', '=', 1)]), "den": AGG('count', 'driving', where=[W('within', '>=', 0)])}],
    "charts": [
        CHART('Events per month', 'column', 'month', [AGG('count', 'events', date='events.date', label='Events')]),
        CHART('Events by kind', 'bar', 'events.kind', [AGG('count', 'events', label='Events')]),
        CHART('Events by person', 'bar', 'events.person', [AGG('count', 'events', label='Events')]),
        CHART('Events by weekday', 'bar', 'shifts.weekday', [AGG('sum', 'shifts', 'shifts.events_n', label='Events')]),
        CHART('Activities by child', 'bar', 'events.person', [AGG('count', 'events', where=[W('kind', '=', K_ACT)], label='Activities')]),
        CHART('Drivers by trips', 'bar', 'events.driver', [AGG('count', 'events', label='Trips')]),
        CHART('Trips driven per month by adult', 'column', 'month', [AGG('count', 'events', date='events.date', where=[W('driver', '=', D_A1)], label='Adult 1'), AGG('count', 'events', date='events.date', where=[W('driver', '=', D_A2)], label='Adult 2'),
                                                                     AGG('count', 'events', date='events.date', where=[W('driver', '=', D_GP)], label='Grandparent'), AGG('count', 'events', date='events.date', where=[W('driver', '=', D_CP)], label='Carpool family')]),
        CHART('Carpool trips per month', 'column', 'month', [AGG('count', 'events', date='events.date', where=[W('carpool', '=', YESV)], label='Carpool trips')]),
        CHART('Conflicts per month', 'column', 'month', [AGG('count', 'events', date='events.date', where=[W('conf', '=', 1)], label='Conflicts')]),
        CHART('Events per week, next 12', 'column', 'busy.wk', [AGG('sum', 'busy', 'busy.events', label='Events')]),
        CHART('Evenings with one adult free per month', 'column', 'month', [AGG('count', 'shifts', date='shifts.date', where=[W('adults_free', '=', 1)], label='Evenings')]),
        CHART('School days per term', 'bar', 'terms.term', [AGG('sum', 'terms', 'terms.school_days', label='School days')]),
        CHART('Break days by month of the start', 'column', 'month', [AGG('sum', 'terms', 'terms.days', date='terms.start', where=[W('kind', '=', T_BREAK)], label='Break days')]),
        CHART('Birthdays by month', 'column', 'month', [AGG('count', 'gifts', date='gifts.date', label='Birthdays')]),
        CHART('Gift status', 'bar', 'gifts.status', [AGG('count', 'gifts', label='Gifts')]),
        CHART('Gift cost lines by month', 'column', 'month', [AGG('sum', 'gifts', 'gifts.cost', date='gifts.date', label='Cost lines')]),
        CHART('Visitor nights per month', 'column', 'month', [AGG('sum', 'visitors', 'visitors.nights', date='visitors.arrive', label='Nights')]),
        CHART('Pet care by task', 'bar', 'pet_care.task', [AGG('count', 'pet_care', label='Care dates')]),
        CHART('Pet care per month', 'column', 'month', [AGG('count', 'pet_care', date='pet_care.date', label='Care dates')]),
        CHART('Pet care cost lines by month', 'column', 'month', [AGG('sum', 'pet_care', 'pet_care.cost', date='pet_care.date', label='Cost lines')]),
        CHART('Vehicle log by kind', 'bar', 'vehicle_log.kind', [AGG('count', 'vehicle_log', label='Entries')]),
        CHART('Vehicle cost lines by month', 'column', 'month', [AGG('sum', 'vehicle_log', 'vehicle_log.cost', date='vehicle_log.date', label='Cost lines')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Conflict finder", "why": "overlapping events for the same person or the same driver, the first one named with both events and the adults free from the work pattern", "where": "Conflict Finder Tool"},
    {"name": "Double-booked driver finder", "why": "the same driver on two overlapping lifts, with the start, the place and the days to it", "where": "Double Booked Driver Finder"},
    {"name": "Busiest week ahead", "why": "events and maintenance tasks per week for 12 weeks, the busiest and the quietest week", "where": "Busiest Week Tool"},
    {"name": "Driving fairness", "why": "trips and minutes driven by each adult against the share you agreed, a view for a talk and not a score", "where": "Driving Fairness Tool"},
    {"name": "Carpool rota planner", "why": "your turn in the rota, the weeks until it and the lifts you drive over the weeks planned", "where": "Carpool Rota Planner"},
    {"name": "Trip date moved", "why": "the trip moved by typed days: the events and the vehicle and pet dates that now fall inside it", "where": "Trip Moved Tool"},
    {"name": "Next vehicle service", "why": "the service by mileage or by date, whichever comes first, from the readings and the interval you type", "where": "Next Vehicle Service Tool"},
    {"name": "Free evenings", "why": "evenings with both adults free in the next weeks, from the work pattern and the calendar", "where": "Free Evenings Tool"},
    {"name": "Pet food days left", "why": "the days of food left from the bag and the daily amount, with the reorder date", "where": "Pet Food Days Left Tool"},
    {"name": "Child-care gap days", "why": "the weekdays of a break with nothing typed, and how many a relative can cover", "where": "Child Care Gap Days Tool"}]
competitors = [
    {"what": "shared family calendar app with a yearly fee", "lacks": "shows events but does not count double-booked drivers, free adults from a work pattern, a driving share per adult or the days of food left for a pet"},
    {"what": "paper wall planner", "lacks": "cannot warn about two events at the same time, add up the week, rank the busiest week of the next twelve or count the gap days of a school break"},
    {"what": "single-sheet family schedule template", "lacks": "one list of events with no conflict check, no carpool rota, no work pattern and no pet or vehicle dates"},
    {"what": "phone reminders for the car and the pet", "lacks": "ring on one date and cannot rank the vehicle dates, estimate the next service from the mileage or show the pet food left"}]
guide = [
    'Start here: this workbook holds the family calendar, carpool rota, school terms, birthdays, visitors, pets and vehicles. Open Start and type the household name, the trip date and the week start in the yellow cells.',
    'Replace demo data: clear the yellow demo cells of Team, Family calendar, Work pattern, School terms, Birthdays and gifts, Pets, Pet care log, Vehicles, Vehicle log, Maintenance due dates and Visitors. Keep the lists and settings.',
    'Type the household on Team first: phones and first names are used by every text and by the sitter calendar. Children are listed by first name only.',
    'Calculated sheets (Conflict finder, Busiest week ahead, Driving load, School days and breaks, Gift planner, Pet schedule, Pet food, Vehicle dates, Service estimate): type the numbers or the IDs once and the rest fills in.',
    'Work pattern: adult 1 late days and the Early, Late or Off shifts of adult 2 decide how many adults are free in the evening. The conflict finder uses it to say whether to share the lifts or find a second driver.',
    'The conflict finder lists the next events that overlap for the same person or the same driver, in date order, with both events, the overlap in minutes and what to do.',
    'Driving load: type the weeks ago and the adult once; trips and minutes driven fill in with the share of the week. It is a view for a talk, not a score.',
    'School terms and breaks: type the terms and the breaks; school days left, the days to the next break and the child-care gap days (break weekdays with nothing on the calendar) follow.',
    'Pets and vehicles keep dates only: no treatments and no health details. Type the interval you use (typical, check the clinic and the manual) and the last date; the next date and the days left follow.',
    'Pet food: type the bag in the Pet care log and the daily grams in Settings; the days of food left and the reorder date follow. Vehicle service: type mileage readings in the Vehicle log; the km to the next service follow.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'A single adult keeps the calendar, birthdays, vehicles and renewals and leaves the children, carpool and pet rows empty.',
    'Renters change nothing: read a trade as a request to the landlord.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you, nothing to link, no ads and no upsell. It runs in Excel and Google Sheets with no macros, no add-ins and no accounts.',
    'What this is not: not a reminder app, not a safety service, not legal, medical, veterinary or financial advice. Every date and total is calculated from your entries; intervals are typical, so check with the clinic, garage and school.',
]
listing = {"title": "Family Calendar, Pets and Vehicles Excel Template: Family Planner, Carpool Rota, Conflict Finder, School Terms, Pet Care, Car Service Dates",
    "headline": "See who is where, who drives and what comes due in one family workbook",
    "tags": ["family calendar", "family planner", "carpool rota", "school term planner", "birthday gift list", "pet care tracker", "pet food reorder", "vehicle service log", "car renewal tracker", "household planner", "visitor stays", "no subscription", "home management"],
    "description": ("Know who is where and who drives. Built for a single adult, a couple or a family, owners or renters: a family calendar with events per person, the times, the place and the driver, and a work pattern that says how many adults are free in the evening.\n\n"
        "The conflict finder lists the events that overlap for the same person or the same driver, in date order, with both events, the overlap in minutes and what to do. The busiest week ahead counts events and maintenance tasks for 12 weeks, and the driving load shows the trips and the minutes of each adult against the share you agreed, as a view for a talk and not a score.\n\n"
        "School terms and breaks give the school days left, the days to the next break and the child-care gap days. Birthdays and gifts for the next 60 days keep names, dates, gift status and cost lines. Visitors and stays check the beds and the clashes. "
        "Pets keep care dates only, with the days of food left and a reorder date; vehicles keep service, tyres, annual test, insurance and registration dates, with a ranked list for the next 90 days and a service estimate from the mileage you type. No health details, ever.\n\n"
        f"{len(tools)} tools answer the questions of every week. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the household, the sitter, the carpool family, the school, the clinic and the garage.\n\n"
        "This is part six of the eight-part Home Management suite. A standard .xlsx workbook with no macros, no accounts and no yearly renewal, with a demo copy full of sample data and a blank copy. Dates and totals are calculated from your entries and are not advice."),
    "features": ["Family calendar with a driver for every event", "Conflict finder for overlapping events and double-booked drivers", "Work pattern: how many adults are free each evening", "Busiest week ahead for the next 12 weeks",
                 "Driving load by adult with a fairness line", "School terms, breaks and child-care gap days", "Birthdays and gifts for the next 60 days", "Pet care dates, food days left and reorder date", "Vehicle dates ranked for the next 90 days and a service estimate",
                 f"{len(tools)} tools for the questions of every week", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", "No macros, no accounts, no yearly renewal"]}
lists = lists_base + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p6', slug='home-management-calendar', profession='Home Management', name='Family Calendar, Pets and Vehicles',
         tagline='See who is where, who drives and what comes due, all in one family workbook', price_usd=29,
         colors={"primary": "#2F5D62", "accent": "#E0A030"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Family calendar, pets and vehicles"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ho6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']), 'tag', len(s['tagline']), 'name', len(s['name']))
