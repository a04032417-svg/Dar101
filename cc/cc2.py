"""Childcare center suite - part 2: Rooms, Places and Attendance."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc2_lists import *
from cc2_tables import settings, tables
from cc2_tools import tools

SUITE = 'fx-20261115-childcare-center'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def DAYF(t): return [(w[:3], '%s.%s' % (t, k)) for k, w in (('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'), ('thu', 'Thursday'), ('fri', 'Friday'))]
ENR = tok('cstatus', 'Enrolled'); SOON = tok('cstatus', 'Starting soon')
BY = 'IF(WEEKDAY({today},2)>5,1,WEEKDAY({today},2))'   # next open weekday number
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
SIGN = 'Willow Lane Early Learning'

forms = [
    FORM('signin_sheet', 'Daily Sign-in Sheet', 'Daily sign-in record for one child and day', 'attendance.attendance_id', F(
        ('Date', 'attendance.date'), ('Weekday', 'attendance.weekday'), ('Child', 'attendance.child'), ('Room', 'attendance.room'), ('Schedule', 'attendance.schedule'), ('Booked', 'attendance.booked'), ('Booked hours', 'attendance.booked_hours'),
        ('Status', 'attendance.status'), ('Sign in', 'attendance.sign_in'), ('Sign out', 'attendance.sign_out'), ('Hours attended', 'attendance.hours'), ('Minutes past closing', 'attendance.late_minutes'))),
    FORM('pickup_sheet', 'Sign-out and Late Pickup', 'Sign-out and late pickup record', 'late_pickups.fee_id', F(
        ('Date', 'late_pickups.date'), ('Child', 'late_pickups.child'), ('Room', 'late_pickups.room'), ('Minutes past closing', 'late_pickups.late_minutes'), ('Fee under your rule', 'late_pickups.expected_fee'), ('Fee entered', 'late_pickups.fee'),
        ('Waived', 'late_pickups.waived'), ('Charged', 'late_pickups.charged'), ('Fee check', 'late_pickups.fee_flag'), ('Family phone', 'late_pickups.phone')) + [
        FF('Late pickups of this child, all time', 'COUNTIFS({range:late_pickups.child},INDEX({range:late_pickups.child},MATCH({pick},{range:late_pickups.fee_id},0)))', 'int')]),
    FORM('booking_change', 'Booking Change Sheet', 'Booking change for one child and weekday', 'bookings.booking_id', F(
        ('Child', 'bookings.child'), ('Room', 'bookings.room'), ('Weekday', 'bookings.weekday'), ('Schedule', 'bookings.schedule'), ('Day type', 'bookings.day_type'), ('Hours', 'bookings.hours'), ('Change starts', 'bookings.from_date'),
        ('Day rate', 'bookings.day_rate'), ('Family phone', 'bookings.phone')) + [
        FF('Booked weekdays of this child', 'COUNTIFS({range:bookings.child},INDEX({range:bookings.child},MATCH({pick},{range:bookings.booking_id},0)))', 'int')]),
    FORM('request_sheet', 'Part-time Request Sheet', 'Part-time request with day-by-day fit', 'requests.request_id', F(
        ('Family', 'requests.family'), ('Room', 'requests.room')) + F(*DAYF('requests')) + F(
        ('Day type', 'requests.day_type'), ('Wanted start', 'requests.start_date'), ('Status', 'requests.status'), ('Days wanted', 'requests.days_wanted'), ('Days with no free place', 'requests.days_blocked'),
        ('Fit verdict', 'requests.fit'), ('Weekly price', 'requests.weekly_rate'), ('Family phone', 'requests.phone'))),
    FORM('move_sheet', 'Room Move Sheet', 'Room move for one child', 'aging_up.child_id', F(
        ('Child', 'aging_up.child'), ('Room now', 'aging_up.room'), ('Next room', 'aging_up.next_room'), ('Age in months', 'aging_up.age_months'), ('Moving age in months', 'aging_up.move_age'), ('Months to move', 'aging_up.months_to_move'),
        ('Move date', 'aging_up.move_date'), ('Free places in the next room', 'aging_up.next_free'), ('Move check', 'aging_up.move_flag'), ('Family phone', 'aging_up.phone'))),
    FORM('absence_sheet', 'Absence Notice Sheet', 'Absence notice for one child and month', 'absences.abs_id', F(
        ('Child', 'absences.child'), ('Month', 'absences.month'), ('Room', 'absences.room'), ('Days absent', 'absences.days_absent'), ('Booked days', 'absences.booked_days'), ('Sick absence days', 'absences.sick_days'),
        ('Share of booked days', 'absences.share'), ('Check-in flag', 'absences.abs_flag'), ('Family phone', 'absences.phone'))),
    FORM('dropin_sheet', 'Drop-in Day Request Sheet', 'Drop-in day request and charge', 'dropins.dropin_id', F(
        ('Date', 'dropins.date'), ('Child', 'dropins.child'), ('Family', 'dropins.family'), ('Room', 'dropins.room'), ('Hours', 'dropins.hours'), ('Booked schedule', 'dropins.schedule'), ('Day rate', 'dropins.day_rate'),
        ('Surcharge', 'dropins.surcharge'), ('Charge', 'dropins.charge'), ('Family phone', 'dropins.phone'))),
    FORM('schedule_notice', 'Schedule Change Notice Sheet', 'Schedule change notice for one child', 'children.child_id', F(
        ('Child', 'children.child'), ('Family', 'children.family'), ('Room', 'children.room'), ('Schedule', 'children.schedule'), ('Days a week', 'children.days'), ('Weekly rate', 'children.weekly_rate'),
        ('Start date', 'children.start_date'), ('Status', 'children.status'), ('Months enrolled', 'children.months_enrolled'), ('Family phone', 'children.phone')) + [
        FF('Booked weekdays on file', 'COUNTIFS({range:bookings.child_id},{pick})', 'int')]),
    FORM('afterschool_sheet', 'After-school Pickup Sheet', 'After-school pickup for one child today', 'signin.child_id', F(
        ('Child', 'signin.child'), ('Room', 'signin.room'), ('Booked hours', 'signin.booked_hours'), ('Sign in', 'signin.sign_in'), ('Sign out', 'signin.sign_out'), ('Hours attended', 'signin.hours'),
        ('Minutes past closing', 'signin.late_minutes'), ('Status', 'signin.status'), ('Family phone', 'signin.phone'))),
    FORM('pickup_list', 'Authorised Pickup List Sheet', 'Authorised pickup list for one child', 'children.child_id', F(
        ('Child', 'children.child'), ('Family', 'children.family'), ('Room', 'children.room'), ('Parent or guardian', 'children.guardian'), ('Phone', 'children.phone'), ('Email', 'children.email'), ('Schedule', 'children.schedule'), ('Status', 'children.status'))),
    FORM('closure_sheet', 'Closure Notice Sheet', 'Closure notice with tuition and credit', 'closures.closure_id', F(
        ('Date', 'closures.date'), ('Weekday', 'closures.weekday'), ('Reason', 'closures.reason'), ('Days to go', 'closures.days_to_go'), ('When', 'closures.when'), ('Children affected', 'closures.children_affected'),
        ('Day tuition at stake', 'closures.tuition_at_stake'), ('Credit under your rule', 'closures.credit_value'))),
    FORM('hold_sheet', 'Place Hold Sheet', 'Place hold for one family', 'holds.hold_id', F(
        ('Family', 'holds.family'), ('Room', 'holds.room')) + F(*DAYF('holds')) + F(
        ('Hold from', 'holds.hold_from'), ('Hold until', 'holds.hold_until'), ('Status', 'holds.status'), ('Days left', 'holds.days_left'), ('Hold check', 'holds.hold_flag'), ('Days held', 'holds.days_held'), ('Family phone', 'holds.phone'))),
]
assert len(forms) == 12

documents = [
    DOC('booking_confirm', 'Booking Confirmation', 'Booking confirmation for one booked day', 'bookings.booking_id', [
        'Booking confirmation of {set:company}, dated {today}. Child: {col:bookings.child}. Room: {col:bookings.room}.',
        'Booked day: {col:bookings.weekday}, {col:bookings.day_type}, {col:bookings.hours} hours, from {col:bookings.from_date}. Schedule: {col:bookings.schedule}. Day rate: {col:bookings.day_rate}.',
        'The booking stays the same each week until we agree a change in writing. Closing time is {set:closing_time}; a pickup more than {set:late_grace_min} minutes after it adds {set:late_fee_per_min} a minute.'], ['Owner-director', 'Parent or guardian'], NOTE),
    DOC('schedule_letter', 'Schedule Change Letter', 'Schedule change letter for a family', 'children.child_id', [
        'Schedule change letter of {set:company}, dated {today}. To the family of {col:children.child} ({col:children.family}).',
        'Your child is in the {col:children.room} room on the {col:children.schedule} schedule, {col:children.days} days a week at {col:children.weekly_rate} a week.',
        'A change to the days needs {set:notice_days} days of notice and a free place on each new day. We will confirm the new days and the new weekly rate in writing before the first changed day.'], ['Owner-director', 'Parent or guardian'], NOTE),
    DOC('moveup_letter', 'Moving Up Letter', 'Moving up to the next room letter', 'aging_up.child_id', [
        'Moving up letter of {set:company}, dated {today}. Child: {col:aging_up.child}, date of birth {col:aging_up.dob}.',
        '{col:aging_up.child} is {col:aging_up.age_months} months old in the {col:aging_up.room} room. The planned move to the {col:aging_up.next_room} room is on {col:aging_up.move_date}, at {col:aging_up.move_age} months.',
        'Places free in the {col:aging_up.next_room} room today: {col:aging_up.next_free}. If no place is free on the date, the move waits until one opens and we will tell you. Move check: {col:aging_up.move_flag}.'], ['Lead teacher', 'Parent or guardian'], NOTE),
    DOC('dropin_confirm', 'Drop-in Day Confirmation', 'Drop-in day confirmation', 'dropins.dropin_id', [
        'Drop-in day confirmation of {set:company}, dated {today}. Child: {col:dropins.child}, family {col:dropins.family}.',
        'Date: {col:dropins.date}. Room: {col:dropins.room}. Hours: {col:dropins.hours}. Day rate {col:dropins.day_rate}, surcharge {col:dropins.surcharge}, total charge {col:dropins.charge}.',
        'The charge is added to your next invoice. A drop-in day is an extra day booked at short notice and depends on a free place and the staff on that day.'], ['Assistant director', 'Parent or guardian'], NOTE),
    DOC('absence_record', 'Absence Record', 'Absence record for a family', 'absences.abs_id', [
        'Absence record of {set:company}, dated {today}. Child: {col:absences.child}, room {col:absences.room}, month of {col:absences.month}.',
        'Days absent: {col:absences.days_absent} of {col:absences.booked_days} booked days, of which sick absence {col:absences.sick_days}. Share of booked days: {col:absences.share}. Check: {col:absences.abs_flag}.',
        'This record lists counts only. Booked days stay billed under your agreement; ask us if you want to talk about the absence rule.'], ['Assistant director', 'Parent or guardian'], NOTE),
    DOC('attendance_summary', 'Attendance Summary', 'Attendance summary for a child and week', 'bva.bva_id', [
        'Attendance summary of {set:company}, dated {today}. Child: {col:bva.child}, room {col:bva.room}, week of {col:bva.week}.',
        'Booked hours: {col:bva.booked_hours}. Attended hours: {col:bva.attended_hours}. Difference: {col:bva.drift} hours, {col:bva.drift_pct} of the booked hours. Tolerance check: {col:bva.drift_flag}.',
        'Hours billed on booked hours against attended hours would differ by {col:bva.money_gap}. Tell us if the booked days no longer suit your family.'], ['Assistant director', 'Parent or guardian'], NOTE),
    DOC('pickup_doc', 'Authorised Pickup List', 'Authorised pickup list for a child', 'children.child_id', [
        'Authorised pickup list of {set:company}, dated {today}. Child: {col:children.child}, room {col:children.room}.',
        'Parent or guardian on file: {col:children.guardian}, phone {col:children.phone}, email {col:children.email}.',
        'Write below every other adult who may collect the child, with a phone number. Staff check the list at each pickup and ask for a name that is not on it before the child leaves.'], ['Parent or guardian', 'Staff member'], NOTE),
    DOC('afterschool_letter', 'After-school Arrangements', 'After-school arrangements letter for a request', 'requests.request_id', [
        'After-school arrangements letter of {set:company}, dated {today}. Family contact: {col:requests.family}. Room: {col:requests.room}.',
        'Days wanted: {col:requests.days_wanted}, day type {col:requests.day_type}, from {col:requests.start_date}. Fit check: {col:requests.fit}. Days with no free place: {col:requests.days_blocked}. Weekly price: {col:requests.weekly_rate}.',
        'Children arrive from school by the agreed route and are signed in on arrival. Collection is by an adult on the authorised pickup list before {set:closing_time}.'], ['Assistant director', 'Parent or guardian'], NOTE),
    DOC('closure_calendar', 'Closure Calendar', 'Closure notice for families', 'closures.closure_id', [
        'Closure notice of {set:company}, dated {today}. We are closed on {col:closures.date} ({col:closures.weekday}). Reason: {col:closures.reason}.',
        'Children affected: {col:closures.children_affected}. Day tuition on that day: {col:closures.tuition_at_stake}. Credit under our rule: {col:closures.credit_value}.',
        'Please plan other care for that day. The full list of closure days for the year is on our closure calendar.'], ['Owner-director', 'Parent or guardian'], NOTE),
    DOC('latepickup_notice', 'Late Pickup Notice', 'Late pickup notice for a family', 'late_pickups.fee_id', [
        'Late pickup notice of {set:company}, dated {today}. Child: {col:late_pickups.child}, room {col:late_pickups.room}.',
        'On {col:late_pickups.date} the child was collected {col:late_pickups.late_minutes} minutes after closing time. Fee under our rule: {col:late_pickups.expected_fee}. Fee charged: {col:late_pickups.charged}.',
        'We close at {set:closing_time} and allow {set:late_grace_min} minutes; after that the fee is {set:late_fee_per_min} a minute. Please tell us if you expect to be late.'], ['Assistant director', 'Parent or guardian'], NOTE),
    DOC('occupancy_report', 'Room Occupancy Report', 'Room occupancy report for the owner-director', 'capacity6.cap_id', [
        'Room occupancy report of {set:company}, dated {today}. Room: {col:capacity6.room}, month of {col:capacity6.month}.',
        'Licensed places {col:capacity6.capacity}. Children enrolled now {col:capacity6.enrolled_now}. Moving in {col:capacity6.moving_in}, moving out {col:capacity6.moving_out}, starters {col:capacity6.starters}, leaving on notice {col:capacity6.leaving}.',
        'Expected children {col:capacity6.expected}, free places {col:capacity6.free_places}, expected occupancy {col:capacity6.occupancy}. Capacity check: {col:capacity6.cap_flag}.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('room_plan', 'Weekly Room Plan', 'Weekly room plan for a room and weekday', 'room_day.rd_id', [
        'Weekly room plan of {set:company}, dated {today}. Room: {col:room_day.room}, weekday: {col:room_day.weekday}.',
        'Licensed places {col:room_day.capacity}, children booked {col:room_day.booked_places}, places held for families {col:room_day.held_places}, free places {col:room_day.free_places}. Occupancy {col:room_day.occupancy}.',
        'Paid but absent share on this day: {col:room_day.absent_share}. Weekly revenue left unfilled: {col:room_day.unfilled_revenue}. Day check: {col:room_day.day_flag}. Staff are planned for the booked children at the ratio of the room.'], ['Lead teacher', 'Assistant director'], NOTE),
]
assert len(documents) == 12

def S(*a): return CHK(*a)
checklists = [
    CHK('open_room', 'Opening the Room Steps', 'attendance', 'attendance.date', [('Unlock the room and check the space is safe', 0), ('Count the staff present against the ratio', 0), ('Open the sign-in sheet for the day', 0), ('Check the booked children and any drop-in days', 0), ('Set out the morning activities', 0), ('Check the allergy and pickup notes for the day', 0)]),
    CHK('morning_signin', 'Morning Sign-in Steps', 'attendance', 'attendance.date', [('Greet each child and parent or guardian', 0), ('Write the sign-in time for every child', 0), ('Mark children who are absent and note why', 0), ('Call the family when a booked child has not arrived by mid-morning', 0), ('Send the first headcount to the office', 0)]),
    CHK('afternoon_signout', 'Afternoon Sign-out Steps', 'attendance', 'attendance.date', [('Check the authorised pickup list for each collection', 0), ('Write the sign-out time for each child', 0), ('Note minutes past closing for late pickups', 0), ('Tell the family about the late fee under your rule', 0), ('Pass the sheet to the assistant director', 1)]),
    CHK('headcount_end', 'End-of-Day Headcount Steps', 'attendance', 'attendance.date', [('Count the children in each room', 0), ('Compare the count with the sign-in sheet', 0), ('Look for any child not signed out', 0), ('Record the busiest hour of the day', 0), ('File the day sheet', 1)]),
    CHK('close_room', 'Closing the Room Steps', 'closures', 'closures.date', [('Check every child has been collected and signed out', 0), ('Tidy toys, tables and cots', 0), ('Wash and put away the day\'s dishes', 0), ('Check doors, windows and the outdoor area', 0), ('Switch off lights and lock up', 0), ('Tell families about the closure day plan', -14)]),
    CHK('move_day', 'Room Move Day Steps', 'aging_up', 'aging_up.agreed_move', [('Check a place is free in the next room', -14), ('Tell the family the move date', -14), ('Plan two settling visits to the next room', -7), ('Share the child\'s routine with the new lead teacher', -3), ('Move belongings and update the room list', 0), ('Update the Children sheet and the sign-in sheet', 0), ('Check in with the family after the first week', 7)]),
    CHK('first_day', 'A Child\'s First Day Steps', 'children', 'children.start_date', [('Confirm the booking and the schedule with the family', -7), ('Check the authorised pickup list is complete', -3), ('Prepare the peg, bed and name label', -1), ('Welcome the child and sign in', 0), ('Agree the settling plan with the family', 0), ('Call the family at the end of the morning', 0), ('Review the first week', 7)]),
    CHK('request_review', 'Part-time Request Review Steps', 'requests', 'requests.start_date', [('Check each wanted day for a free place', -14), ('Check the ratio of the room on each day', -14), ('Offer a day swap when one day is full', -10), ('Tell the family the answer', -10), ('Put the family on the list when no place is free', -10), ('Add the booking to the Bookings sheet', -3)]),
    CHK('weekly_attendance', 'Weekly Attendance Check Steps', 'weekly_hours', 'weekly_hours.week', [('Total booked and attended hours for each room', 5), ('Compare attended hours with booked hours', 5), ('List children above your tolerance', 6), ('Check absence counts against your rule', 6), ('Call the families you want to check in with', 7)]),
    CHK('monthly_aging', 'Monthly Aging-Up Review Steps', 'capacity6', 'capacity6.month', [('List children reaching the moving age in six months', 0), ('Check the places free in each next room', 0), ('Find the month a room runs out', 1), ('Plan staff for the rooms that grow', 3), ('Tell the families about the planned moves', 5), ('Update the waiting list answers', 7)]),
    CHK('pickup_handover', 'Afternoon Pickup Handover Steps', 'late_pickups', 'late_pickups.date', [('Hand over the sign-out sheet to the closing staff member', 0), ('List the children still to be collected', 0), ('Call the family at closing time', 0), ('Write the late minutes', 0), ('Tell the assistant director about the late fee', 1)]),
    CHK('hold_review', 'Weekly Place-Hold Review Steps', 'holds', 'holds.hold_from', [('List the active holds and their end dates', 7), ('Call the families whose hold ends soon', 7), ('Confirm the start date for each hold that converts', 8), ('Release the places of holds that ended', 9), ('Update the free places for the waiting list', 10)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text + ' ' + SIGN)
messages = [
    M('f_late', 'Family: late pickup today', 'late_pickups', 'late_pickups.phone', 'Hello, {child} was collected {late_minutes} minutes past closing on {date}. Please tell us if you expect to be late again.'),
    M('f_latefee', 'Family: the late fee for the date', 'late_pickups', 'late_pickups.phone', 'Hello, the late pickup fee for {child} on {date} is {fee}.'),
    M('f_signout', 'Family: please confirm sign-out time', 'signin', 'signin.phone', 'Hello, we forgot to write the sign-out time for {child} today. Please confirm when you collected them.'),
    M('f_absent', 'Family: we have not heard from you', 'signin', 'signin.phone', 'Hello, we have not heard why {child} is absent today. Please tell us when you can.'),
    M('f_change', 'Family: your booking change starts', 'bookings', 'bookings.phone', 'Hello, the booking change for {child} on {weekday} starts on {from_date} in the {room} room.'),
    M('f_offer', 'Family: we can offer the days', 'requests', 'requests.phone', 'Hello, we can offer the days you asked for in the {room} room from {start_date}, at {weekly_rate} a week. Please reply to accept.'),
    M('f_swap', 'Family: one day swapped', 'requests', 'requests.phone', 'Hello, we can offer your days in the {room} room with one day swapped to {swap_day}, at {weekly_rate} a week. Would that suit you?'),
    M('f_decline', 'Family: we cannot offer those days yet', 'requests', 'requests.phone', 'Hello, we cannot offer those days in the {room} room yet. You stay on the list and we will call when a place opens.'),
    M('f_moves', 'Family: your child moves room', 'aging_up', 'aging_up.phone', 'Hello, {child} moves to the {next_room} room on {move_date}. Please ask us if you have questions.'),
    M('f_congrats', 'Family: congratulations on moving up', 'aging_up', 'aging_up.phone', 'Hello, congratulations, {child} is moving up to the {next_room} room soon. The teachers will plan settling visits.'),
    M('f_dropin', 'Family: a drop-in day is available', 'dropins', 'dropins.phone', 'Hello, a drop-in day is available on {date} in the {room} room for {child}. Please reply if you want it.'),
    M('f_dropin_ok', 'Family: your drop-in day is confirmed', 'dropins', 'dropins.phone', 'Hello, your drop-in day for {child} on {date} is confirmed at {charge}, added to your next invoice.'),
    M('f_pickup', 'Family: who collects your child today', 'signin', 'signin.phone', 'Hello, please confirm who collects {child} today. Staff will check the authorised pickup list.'),
    M('f_holdend', 'Family: your place hold ends', 'holds', 'holds.phone', 'Hello, your place hold in the {room} room ends on {hold_until}. Please tell us if you want to start.'),
    M('f_afterschool', 'Family: your after-school days start', 'bookings', 'bookings.phone', 'Hello, the after-school days for {child} start on {from_date}, with sign-in on arrival and collection before closing time.'),
    M('f_pickup_ok', 'Family: your pickup change is confirmed', 'children', 'children.phone', 'Hello, your pickup arrangement for {child} is confirmed. Please keep the authorised pickup list up to date.'),
    M('f_closed', 'Family: we are closed on a date', 'children', 'children.phone', 'Hello, we are closed on {next_closure} ({closure_reason}). Please plan other care for {child} that day.'),
    M('f_year', 'Family: holiday closure dates', 'children', 'children.phone', 'Hello, there are {closures_year} closure days this year. The full list is on the closure calendar we sent. Next is {next_closure}.'),
    M('f_hours', 'Family: attended hours were below booked', 'bva', 'bva.phone', 'Hello, in the week of {week} {child} attended {attended_hours} hours of {booked_hours} booked. Do the booked days still suit you?'),
    M('f_absent_days', 'Family: is everything fine', 'absences', 'absences.phone', 'Hello, {child} has been absent {days_absent} days in {month}. Is everything fine? Please call us.'),
    M('f_notice', 'Family: your notice period ends', 'children', 'children.phone', 'Hello, the notice period for {child} ends on {end_date}. We will confirm the last day and the final invoice.'),
    M('f_delay', 'Family: moving up is delayed', 'aging_up', 'aging_up.phone', 'Hello, the move for {child} to the {next_room} room is delayed until a place opens. We will call you as soon as one is free.'),
    M('f_latesum', 'Family: late pickups have added up', 'late_pickups', 'late_pickups.phone', 'Hello, late pickups of {child} have added up recently, the latest on {date}. Can we talk about a time that suits your family?'),
    M('o_lowday', 'Owner: low occupancy on a weekday', 'room_day', 'room_day.owner_phone', 'Hello, the {room} room is at {occupancy} occupancy on {weekday}, with {free_places} free places and {unfilled_revenue} a week unfilled.'),
    M('o_runout', 'Owner: a room runs out of places', 'capacity6', 'capacity6.owner_phone', 'Hello, the {room} room expects {expected} children in {month} against {capacity} places.'),
    M('o_notout', 'Owner: a child is not signed out', 'signin', 'signin.owner_phone', 'Hello, {child} in the {room} room has not been signed out yet. Status: {status}.'),
    M('o_over', 'Owner: a room is over its places', 'capacity6', 'capacity6.owner_phone', 'Hello, the {room} room is over its licensed places by {over_by} in {month}. Please check your local rules.'),
    M('t_moving', 'Teacher: children moving into your room', 'aging_up', 'aging_up.teacher_phone', 'Hello, {child} moves into the {next_room} room on {move_date}. Please plan a settling visit.'),
    M('t_list', 'Teacher: your room list for tomorrow', 'room_day', 'room_day.teacher_phone', 'Hello, the {room} room has {booked_places} children booked on {weekday}, {held_places} places held and {free_places} free.'),
    M('a_headcount', 'Assistant: headcount for a room and hour', 'by_hour', 'by_hour.assistant_phone', 'Hello, please count the {room} room at {hour}. We expect {avg_children} children and {staff_needed} staff members at the ratio.'),
    M('c_meals', 'Cook: meal counts for tomorrow', 'room_day', 'room_day.cook_phone', 'Hello, meal counts for the {room} room on {weekday}: {booked_places} children booked.'),
    M('fl_cover', 'Floater: after-school cover needed', 'dropins', 'dropins.floater_phone', 'Hello, we need cover in the {room} room on {date} for {hours} hours because of a drop-in day.'),
    M('ad_requests', 'Assistant director: requests waiting', 'requests', 'requests.ad_phone', 'Hello, the part-time request from {family} for the {room} room is waiting for an answer. Fit check: {fit}.'),
    M('ad_dropins', 'Assistant director: drop-in days to bill', 'dropins', 'dropins.ad_phone', 'Hello, the drop-in day of {child} on {date} is {charge} and goes on the next invoice.'),
]
assert len(messages) == 34, len(messages)

def CNT(c, *w): return 'COUNTIFS(%s)' % ','.join(w)
A30 = '{range:attendance.date},">"&({today}-30),{range:attendance.date},"<="&{today}'
A28 = '{range:attendance.date},">="&({today}-28),{range:attendance.date},"<="&{today}'
A7 = '{range:attendance.date},">"&({today}-7),{range:attendance.date},"<="&{today}'
BKD = '{range:attendance.booked},%s' % YES
L30 = '{range:late_pickups.date},">"&({today}-30),{range:late_pickups.date},"<="&{today}'
EMPT = 'MIN(%s)' % ','.join('IFERROR(SUMIFS({range:room_day.booked_places},{range:room_day.room},%s)/SUMIFS({range:room_day.capacity},{range:room_day.room},%s),1)' % (tok('room', r), tok('room', r)) for r in ('Infants', 'Toddlers', 'Twos', 'Preschool', 'School-age'))
kpis = [
    KPI('Children enrolled', 'COUNTIFS({range:children.status},%s)' % ENR, 'int'),
    KPI('Children starting soon', 'COUNTIFS({range:children.status},%s)' % SOON, 'int'),
    KPI('Occupancy on the next open day', 'IFERROR(SUMIFS({range:room_day.booked_places},{range:room_day.day_no},%s)/SUMIFS({range:room_day.capacity},{range:room_day.day_no},%s),0)' % (BY, BY), 'pct'),
    KPI('Booked share of room hours, last 4 weeks', 'IFERROR(AVERAGEIFS({range:weekly_hours.occupancy},{range:weekly_hours.week},">="&({today}-28)),0)', 'pct'),
    KPI('Occupancy of the emptiest room', EMPT, 'pct'),
    KPI('Free places on the next open day', 'SUMIFS({range:room_day.free_places},{range:room_day.day_no},%s)' % BY, 'int'),
    KPI('Free places next month', 'SUMIFS({range:capacity6.free_places},{range:capacity6.month},EDATE(%s,1))' % MS, 'int'),
    KPI('Booked days a week', 'COUNTIFS({range:bookings.child_status},%s)' % ENR, 'int'),
    KPI('Attended days, last 7 days', 'SUMIFS({range:attendance.present_flag},%s)' % A7, 'int'),
    KPI('Attendance rate, last 4 weeks', 'IFERROR(SUMIFS({range:attendance.present_flag},%s,%s)/COUNTIFS(%s,%s),0)' % (A28, BKD, A28, BKD), 'pct'),
    KPI('Paid but absent share, last 30 days', 'IFERROR(SUMIFS({range:attendance.absent_flag},%s)/COUNTIFS(%s,%s),0)' % (A30, A30, BKD), 'pct'),
    KPI('Sick absences, last 30 days', 'SUMIFS({range:attendance.sick_flag},%s)' % A30, 'int'),
    KPI('Family holiday days, last 30 days', 'SUMIFS({range:attendance.holiday_flag},%s)' % A30, 'int'),
    KPI('Booked hours, last 7 days', 'SUMIFS({range:attendance.booked_hours},%s,%s)' % (A7, BKD), 'hours'),
    KPI('Attended hours, last 7 days', 'SUMIFS({range:attendance.hours},%s)' % A7, 'hours'),
    KPI('Hours drift, last 4 weeks', 'IFERROR(SUMIFS({range:bva.attended_hours},{range:bva.week},">="&({today}-28))/SUMIFS({range:bva.booked_hours},{range:bva.week},">="&({today}-28))-1,0)', 'pct'),
    KPI('Late pickups, last 30 days', 'COUNTIFS(%s)' % L30, 'int'),
    KPI('Late minutes, last 30 days', 'SUMIFS({range:late_pickups.late_minutes},%s)' % L30, 'int'),
    KPI('Late fees charged, last 30 days', 'SUMIFS({range:late_pickups.charged},%s)' % L30, 'money'),
    KPI('Late fees waived, last 30 days', 'SUMIFS({range:late_pickups.fee},%s,{range:late_pickups.waived},%s)' % (L30, YES), 'money'),
    KPI('Drop-in days, last 90 days', 'COUNTIFS({range:dropins.date},">"&({today}-90),{range:dropins.date},"<="&{today})', 'int'),
    KPI('Part-time requests waiting', 'COUNTIFS({range:requests.status},%s)' % tok('reqstatus', 'Waiting for answer'), 'int'),
    KPI('Children moving up in 6 months', 'COUNTIFS({range:aging_up.move_flag},%s)+COUNTIFS({range:aging_up.move_flag},%s)' % (fl('Move now'), fl('Move within window')), 'int'),
    KPI('Rooms running out in 6 months', 'COUNTIFS({range:capacity6.full_rank},1)', 'int'),
    KPI('Weekly revenue left unfilled', 'SUM({range:room_day.unfilled_revenue})', 'money'),
    KPI('Place holds active', 'COUNTIFS({range:holds.status},%s)' % tok('holdstatus', 'Active'), 'int'),
    KPI('Leavers, last 90 days', 'COUNTIFS({range:leavers.end_date},">"&({today}-90),{range:leavers.end_date},"<="&{today})', 'int'),
    KPI('Closure days this year', 'COUNTIFS({range:closures.date},">="&DATE(YEAR({today}),1,1),{range:closures.date},"<="&DATE(YEAR({today}),12,31))', 'int'),
    KPI('Hours per child per day, last 30 days', 'IFERROR(AVERAGEIFS({range:attendance.hours},%s,{range:attendance.status},%s),0)' % (A30, tok('attstatus', 'Present')), 'hours'),
    KPI('Busiest hour of the day', 'INDEX({range:by_hour.hour},MATCH(MAX({range:by_hour.hour_total}),{range:by_hour.hour_total},0))', 'text'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Rooms and Attendance Dashboard", "kpis": kpis,
    "monthly": {"title": "Late fees and drop-in charges", "date": "late_pickups.date", "series": [
        {"label": "Late fees charged", "sum": "late_pickups.charged", "date": "late_pickups.date"}, {"label": "Drop-in charges", "sum": "dropins.charge", "date": "dropins.date"}]},
    "breakdowns": [{"title": "Weekly revenue unfilled by room", "by": "room_day.room", "value": "room_day.unfilled_revenue", "agg": "sum"}, {"title": "Children by room", "by": "children.room", "value": "children.days", "agg": "count"},
                   {"title": "Late minutes by room", "by": "late_pickups.room", "value": "late_pickups.late_minutes", "agg": "sum"}, {"title": "Children booked by weekday", "by": "room_day.weekday", "value": "room_day.booked_places", "agg": "sum"}]}
EN = ('status', '=', ENR)
BK = ('booked', '=', YES)
insights = {"filters": [{"label": "Room", "list": "room"}, {"label": "Weekday", "list": "wday"}],
    "gauges": [{"title": "Occupancy against the target", "num": AGG('sum', 'room_day', 'room_day.booked_places'), "den": AGG('sum', 'room_day', 'room_day.capacity')},
               {"title": "Attendance rate", "num": AGG('sum', 'attendance', 'attendance.present_flag', where=[BK]), "den": AGG('count', 'attendance', where=[BK])},
               {"title": "Booked hours attended", "num": AGG('sum', 'attendance', 'attendance.hours', where=[BK]), "den": AGG('sum', 'attendance', 'attendance.booked_hours', where=[BK])},
               {"title": "Late pickups avoided", "num": AGG('count', 'attendance', where=[('status', '=', tok('attstatus', 'Present')), ('late_minutes', '=', 0)]), "den": AGG('count', 'attendance', where=[('status', '=', tok('attstatus', 'Present'))])},
               {"title": "Place holds converted to starts", "num": AGG('count', 'holds', where=[('status', '=', tok('holdstatus', 'Converted to start'))]), "den": AGG('count', 'holds')},
               {"title": "Moving-up places ready", "num": AGG('count', 'aging_up', where=[('next_free', '>', 0), ('move_flag', '<>', fl('Move later'))]), "den": AGG('count', 'aging_up', where=[('move_flag', '<>', fl('Move later')), ('move_flag', '<>', fl('No next room'))])}],
    "charts": [
        CHART('Occupancy by room', 'bar', 'room_day.room', [AGG('avg', 'room_day', 'room_day.occupancy', label='Occupancy')]),
        CHART('Occupancy by weekday', 'bar', 'room_day.weekday', [AGG('avg', 'room_day', 'room_day.occupancy', label='Occupancy')]),
        CHART('Children by room', 'bar', 'children.room', [AGG('count', 'children', where=[EN], label='Children')]),
        CHART('Children by schedule', 'bar', 'children.schedule', [AGG('count', 'children', where=[EN], label='Children')]),
        CHART('Attendance rate per month', 'line', 'month', [AGG('avg', 'attendance', 'attendance.present_flag', date='attendance.date', where=[BK], label='Attendance rate')]),
        CHART('Attendance status by month', 'bar', 'month', [AGG('sum', 'attendance', 'attendance.present_flag', date='attendance.date', label='Present'), AGG('sum', 'attendance', 'attendance.sick_flag', date='attendance.date', label='Sick absence'),
                                                              AGG('sum', 'attendance', 'attendance.holiday_flag', date='attendance.date', label='Family holiday')]),
        CHART('Paid but absent days per month', 'bar', 'month', [AGG('sum', 'attendance', 'attendance.absent_flag', date='attendance.date', label='Absent booked days')]),
        CHART('Booked and attended hours per month', 'line', 'month', [AGG('avg', 'attendance', 'attendance.booked_hours', date='attendance.date', where=[BK], label='Booked hours'), AGG('avg', 'attendance', 'attendance.hours', date='attendance.date', where=[BK], label='Attended hours')]),
        CHART('Late pickups per month', 'bar', 'month', [AGG('count', 'late_pickups', date='late_pickups.date', label='Late pickups')]),
        CHART('Late fees per month', 'bar', 'month', [AGG('sum', 'late_pickups', 'late_pickups.charged', date='late_pickups.date', label='Late fees charged')]),
        CHART('Late minutes by room', 'bar', 'late_pickups.room', [AGG('sum', 'late_pickups', 'late_pickups.late_minutes', label='Late minutes')]),
        CHART('Drop-in days per month', 'bar', 'month', [AGG('count', 'dropins', date='dropins.date', label='Drop-in days')]),
        CHART('Average children by hour', 'bar', 'by_hour.hour', [AGG('avg', 'by_hour', 'by_hour.avg_children', label='Average children')]),
        CHART('Free places by room', 'bar', 'room_day.room', [AGG('avg', 'room_day', 'room_day.free_places', label='Free places')]),
        CHART('Moving up by room', 'bar', 'capacity6.room', [AGG('sum', 'capacity6', 'capacity6.moving_in', label='Children moving in')]),
        CHART('Leavers per month', 'bar', 'month', [AGG('count', 'leavers', date='leavers.end_date', label='Leavers')]),
        CHART('Children by status', 'bar', 'children.status', [AGG('count', 'children', label='Children')]),
        CHART('Notices by room', 'bar', 'leavers.room', [AGG('count', 'leavers', label='Notices')]),
        CHART('Place holds by room', 'bar', 'holds.room', [AGG('count', 'holds', label='Place holds')]),
        CHART('Absent days by room', 'bar', 'absences.room', [AGG('sum', 'absences', 'absences.days_absent', label='Absent days')]),
        CHART('Closure days per month', 'bar', 'month', [AGG('count', 'closures', date='closures.date', label='Closure days')]),
        CHART('New children enrolled per month', 'line', 'month', [AGG('count', 'children', date='children.start_date', label='Children starting')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6
signature = [
    {"name": "Occupancy by room and weekday", "why": "booked over licensed places for each room and day, the paid-but-absent share and revenue left unfilled, ranked so you market the emptiest day first", "where": "Occupancy by Room and Day"},
    {"name": "Part-time schedule puzzle", "why": "tick the days a family wants and each day is checked against free places and the ratio, with a day swap named when exactly one day is full", "where": "Part-Time Schedule Puzzle"},
    {"name": "Aging-up planner", "why": "children reaching the next room's age in the next six months, the places the next room gives up and the month a room runs out", "where": "Aging-Up Planner"},
    {"name": "Booked hours against attended hours", "why": "booked and attended hours by child and week with your tolerance and the money gap if billing used attended hours", "where": "Booked vs Attended Drift"},
    {"name": "Sign-in hours with late minutes", "why": "sign-in and sign-out times give hours attended, minutes past closing, the grace time and the late fee for the invoice", "where": "Sign-in and Sign-out Hours"},
    {"name": "Notice and leaving planner", "why": "notice date plus your notice days gives the last day, the date the place opens and when to start advertising it", "where": "Notice and Leaving Planner"},
    {"name": "Room capacity forecast", "why": "six months of expected children by room from moves, starters and notices, in Base, Best and Worst, with the month a room reaches your target", "where": "Room Capacity Forecast"}]
competitors = [
    {"what": "free attendance sheets", "lacks": "tick present or absent but never compare booked and attended hours, count minutes past closing or show which weekday is emptiest"},
    {"what": "paper sign-in books", "lacks": "hold the times but cannot total hours, add up late pickups or warn when a room is over its places"},
    {"what": "subscription childcare management software", "lacks": "charge every month or per child and hide the occupancy and aging-up logic, so you cannot see why a room runs out of places"},
    {"what": "generic booking calendars", "lacks": "list who comes on which day but have no ratio, no part-time day check and no paid-but-absent revenue"},
    {"what": "single-sheet waiting lists", "lacks": "record the family but never test the requested days against free places or the month the next room opens"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: closing time, grace minutes, late fee, drop-in surcharge, wanted occupancy and the age in months at which children move up.',
    'Check Rooms, Schedules and Rates. They hold your licensed places, the children per staff member (check your local rules) and the weekly and day prices the other sheets look up.',
    'Keep Children and Bookings up to date. Each booked weekday of an enrolled child is one row; the Room-Day Occupancy sheet counts them against the licensed places.',
    'Write the daily sign-in on Attendance Log: date, child, sign in and sign out. Hours attended, minutes past closing and absence flags calculate themselves.',
    'Enter booked and attended hours by child and week on Booked vs Attended, and read the drift against your tolerance and the money gap.',
    'Log late pickups on Late Pickups and drop-in days on Drop-in Days. Fees follow your late fee and surcharge settings.',
    'Add every part-time request on Part-Time Requests and every held place on Place Holds. The fit verdict and the free places update with your bookings.',
    'Read Aging-Up List and Capacity Next 6 Months each month to see who moves up and the month a room runs out. Leavers and Notices shows the places about to open.',
    'Use Absences by Child, Weekly Hours by Room and Children by Hour to see attendance patterns without writing any reasons.',
    f'Use the {len(tools)} calculators for occupancy, the part-time puzzle, moving up, drift, sign-in hours, drop-in days, closures, forecasts and notices.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Rooms and Attendance Dashboard and Charts every week: occupancy, attendance, late pickups, free places and children moving up.']
listing = {"title": "Childcare Center Rooms and Attendance Excel Template: Occupancy by Room, Part-Time Puzzle, Aging-Up Planner, Sign-in Hours, Late Pickups",
    "headline": "Fill every place and know who comes, when, and for how long",
    "tags": ["childcare center", "daycare template", "home daycare", "attendance tracker", "occupancy by room", "aging up planner", "sign in sheet", "late pickup fee", "part time schedule", "childcare excel", "nursery spreadsheet", "capacity forecast", "daycare owner"],
    "description": ("Run the places and the daily sign-in of a home daycare or childcare center in one Excel workbook. Built for an owner-director with 1 to 5 rooms. "
        "Occupancy means children booked as a share of licensed places, and ratio means children per staff member. Rooms, Children and Bookings feed a Room-Day Occupancy sheet that shows booked, held and free places for every room and weekday, the paid-but-absent share and the weekly revenue left unfilled.\n\n"
        "The Attendance Log gives hours attended, minutes past closing and absence flags; Booked vs Attended compares billed hours with hours children were there; Late Pickups and Drop-in Days carry your fees and surcharge. "
        "Part-Time Requests checks each wanted day against free places, Aging-Up List and Capacity Next 6 Months show who moves up and the month a room runs out, and Leavers and Notices, Place Holds and Closures show how places open and close.\n\n"
        f"{len(tools)} calculators cover occupancy by room and day, the part-time puzzle, aging-up, drift, sign-in hours, afternoon load, free places, move dates, absent revenue, peak hours, drop-in days, closures, forecasts, patterns, capacity, absences, trends and notices. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to families, the owner-director, teachers, the cook and floaters. Children's data is names, rooms, dates and status only.\n\n"
        "This is part two of the Home Daycare and Childcare Center suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data to explore first. It helps you keep track of places and attendance and does not promise results."),
    "features": ["Occupancy by room and weekday with revenue left unfilled", "Part-time schedule puzzle with day swaps", "Aging-up planner and six-month capacity forecast", "Booked hours against attended hours", "Sign-in hours, late minutes and late fees",
                 "Drop-in days, closures and place holds", "Absence flags with status only", f"{len(tools)} calculators for places and attendance", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p2', slug='childcare-center-rooms', profession='Home Daycare and Childcare Center', name='Rooms, Places and Attendance',
         tagline='Fill every place and know who comes, when, and for how long', price_usd=29,
         colors={"primary": "#33658A", "accent": "#F6AE2D"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 2, "of": 8, "focus": "Rooms, places and attendance"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc2.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
