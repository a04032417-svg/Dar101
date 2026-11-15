"""Home Daycare and Childcare Center suite - part 1: Enquiries, Tours and Waitlist."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc1_lists import *
from cc1_tables import settings, tables
from cc1_tools import tools

SUITE = 'fx-20261115-childcare-center'
NOTE = "Sample wording: adapt it to your own center and check your local rules."
YES = '{list:yesno.yes}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def PK(t, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, t + '_id_placeholder')

# ------------------------------------------------------------------ forms (12)
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
WWt = tok('waitstatus', 'Waiting'); HELDt = tok('tourstatus', 'Held')
forms = [
    FORM('enquiry_sheet', 'Enquiry Sheet', 'Enquiry with reply time and weekly rate', 'enquiries.enquiry_id', F(
        ('Date', 'enquiries.date'), ('Name', 'enquiries.name'), ('Phone', 'enquiries.phone'), ('Child age in months', 'enquiries.child_age_months'), ('Room wanted', 'enquiries.want_room'), ('Schedule wanted', 'enquiries.want_schedule'),
        ('Wanted start', 'enquiries.want_start'), ('Source', 'enquiries.source'), ('Hours to a first reply', 'enquiries.first_reply_hours'), ('Reply check', 'enquiries.reply_flag'), ('Status', 'enquiries.status'),
        ('Weekly rate of the days wanted', 'enquiries.weekly_value'), ('Registration fee', 'enquiries.reg_fee')) + [
        FF('Enquiries from this source', 'COUNTIFS({range:enquiries.source},%s)' % LK('enquiries', 'enquiry_id', 'source'), 'int'),
        FF('Days since the enquiry', '{today}-%s' % LK('enquiries', 'enquiry_id', 'date'), 'int')]),
    FORM('tour_sheet', 'Tour Booking Sheet', 'Tour booking with the staff member and room', 'tours.tour_id', F(
        ('Tour date', 'tours.date'), ('Family', 'tours.name'), ('Phone', 'tours.phone'), ('Staff member', 'tours.staff'), ('Room shown', 'tours.room'), ('Source', 'tours.source'), ('Tour status', 'tours.status'),
        ('Assistant director phone', 'tours.director_phone')) + [
        FF('Tours booked on that day', 'COUNTIFS({range:tours.date},%s)' % LK('tours', 'tour_id', 'date'), 'int'),
        FF('Free tour slots left on that day', '{set:tour_slots_day}-COUNTIFS({range:tours.date},%s)' % LK('tours', 'tour_id', 'date'), 'int')]),
    FORM('followup_sheet', 'Tour Follow-up Sheet', 'Tour outcome and the next step', 'tours.tour_id', F(
        ('Family', 'tours.name'), ('Phone', 'tours.phone'), ('Tour date', 'tours.date'), ('Tour status', 'tours.status'), ('Outcome check', 'tours.outcome_flag'), ('Applied after the tour', 'tours.applied'), ('Owner phone', 'tours.owner_phone')) + [
        FF('Days since the tour', '{today}-%s' % LK('tours', 'tour_id', 'date'), 'int'),
        FF('Tours held from this source', 'COUNTIFS({range:tours.source},%s,{range:tours.status},%s)' % (LK('tours', 'tour_id', 'source'), HELDt), 'int'),
        FF('Share of those that applied', 'IFERROR(COUNTIFS({range:tours.source},%s,{range:tours.applied},%s)/COUNTIFS({range:tours.source},%s,{range:tours.status},%s),0)' % (LK('tours', 'tour_id', 'source'), YES, LK('tours', 'tour_id', 'source'), HELDt), 'pct')]),
    FORM('application_sheet', 'Application Sheet', 'Application with paperwork and deposit status', 'applications.enquiry_id', F(
        ('Family', 'applications.name'), ('Phone', 'applications.phone'), ('Applied on', 'applications.applied_on'), ('Room', 'applications.room'), ('Schedule', 'applications.schedule'), ('Wanted start', 'applications.want_start'),
        ('Forms back', 'applications.forms_back'), ('Deposit paid', 'applications.deposit_paid'), ('Status', 'applications.status'), ('Days since the application', 'applications.days_since'),
        ('Paperwork check', 'applications.paperwork_flag'), ('Weekly rate', 'applications.weekly_value')) + [
        FF('Applications in the same room', 'COUNTIFS({range:applications.room},%s)' % LK('applications', 'enquiry_id', 'room'), 'int')]),
    FORM('wl_entry_sheet', 'Waiting List Entry Sheet', 'Waiting list entry with priority and days waiting', 'waitlist.wait_id', F(
        ('Family', 'waitlist.name'), ('Phone', 'waitlist.phone'), ('Child age in months', 'waitlist.child_age_months'), ('Room', 'waitlist.room'), ('Schedule', 'waitlist.schedule'), ('Wanted start', 'waitlist.want_start'),
        ('Added on', 'waitlist.added_on'), ('Priority', 'waitlist.priority'), ('Status', 'waitlist.status'), ('Days waiting', 'waitlist.days_waiting'), ('Weekly rate', 'waitlist.weekly_value'), ('Check', 'waitlist.wait_flag')) + [
        FF('Families ahead in the same room', 'COUNTIFS({range:waitlist.room},%s,{range:waitlist.status},%s,{range:waitlist.added_on},"<"&%s)' % (LK('waitlist', 'wait_id', 'room'), WWt, LK('waitlist', 'wait_id', 'added_on')), 'int')]),
    FORM('wl_checkin_sheet', 'Waiting List Check-in Sheet', 'Waiting family against the free places today', 'fill.wait_id', F(
        ('Family', 'fill.name'), ('Room', 'fill.room'), ('Schedule', 'fill.schedule'), ('Status', 'fill.status'), ('Wanted start', 'fill.want_start'), ('Days to the wanted start', 'fill.days_to_start'),
        ('Free places in the room now', 'fill.free_now'), ('Room check', 'fill.room_fit'), ('Start check', 'fill.start_flag'), ('Weekly rate', 'fill.weekly_value'), ('Revenue over the weeks ahead', 'fill.horizon_value'), ('Rank in the room', 'fill.room_rank')) + [
        FF('Families waiting for this room', 'COUNTIFS({range:fill.room},%s)' % LK('fill', 'wait_id', 'room'), 'int')]),
    FORM('offer_sheet', 'Place Offer Sheet', 'Place offer with the answer due date', 'offers.offer_id', F(
        ('Family', 'offers.name'), ('Phone', 'offers.phone'), ('Room offered', 'offers.room'), ('Offered on', 'offers.offered_on'), ('Answer due', 'offers.offer_due'), ('Offer check', 'offers.offer_flag'), ('Owner phone', 'offers.owner_phone')) + [
        FF('Days left to answer', '%s-{today}' % LK('offers', 'offer_id', 'offer_due'), 'int'),
        FF('Offers answered by all families', 'COUNTIFS({range:offers.answered_on},">0")', 'int')]),
    FORM('accept_sheet', 'Place Acceptance Sheet', 'Offer answer and the start date', 'offers.offer_id', F(
        ('Family', 'offers.name'), ('Room', 'offers.room'), ('Offered on', 'offers.offered_on'), ('Answer', 'offers.answer'), ('Answered on', 'offers.answered_on'), ('Days to answer', 'offers.days_to_answer'), ('Started on', 'offers.started_on'),
        ('Check', 'offers.offer_flag')) + [
        FF('Offers accepted', 'COUNTIFS({range:offers.answer},%s)' % LK('offers', 'offer_id', 'answer'), 'int'),
        FF('Average days to answer, all offers', 'IFERROR(AVERAGEIFS({range:offers.days_to_answer},{range:offers.answered_on},">0"),0)', 'num')]),
    FORM('start_plan_sheet', 'Start Date Plan Sheet', 'Free places and starters for one room and month', 'places.place_id', F(
        ('Room', 'places.room'), ('Month', 'places.month'), ('Places', 'places.capacity'), ('Children booked', 'places.booked'), ('Leavers', 'places.leavers'), ('Starters', 'places.starters'), ('Free places', 'places.free_places'),
        ('Occupancy at month end', 'places.occupancy'), ('Weekly revenue left empty', 'places.weekly_left')) + [
        FF('Families waiting for this room', 'COUNTIFS({range:waitlist.room},%s,{range:waitlist.status},%s)' % (LK('places', 'place_id', 'room'), WWt), 'int'),
        FF('Wanted occupancy', '{set:occupancy_target}', 'pct')]),
    FORM('lost_sheet', 'Lost Enquiry Sheet', 'Reason for losing a family and what it costs', 'lost.reason', F(
        ('Reason', 'lost.reason'), ('Lost enquiries, 12 months', 'lost.lost_enquiries'), ('Weekly tuition lost', 'lost.weekly_lost')) + [
        FF('Share of all lost tuition', 'IFERROR(%s/SUM({range:lost.weekly_lost}),0)' % LK('lost', 'reason', 'weekly_lost'), 'pct'),
        FF('Yearly tuition lost', '%s*{set:weeks_open}' % LK('lost', 'reason', 'weekly_lost'), 'money'),
        FF('Lost in the last 90 days', 'COUNTIFS({range:enquiries.reason},{pick},{range:enquiries.date},">="&({today}-90))', 'int')]),
    FORM('marketing_sheet', 'Marketing Spend Sheet', 'Marketing spend with enquiries and enrolments', 'marketing.campaign_id', F(
        ('Month', 'marketing.month'), ('Kind of spend', 'marketing.kind'), ('Source', 'marketing.source'), ('Cost', 'marketing.cost'), ('Enquiries', 'marketing.enquiries'), ('Children enrolled', 'marketing.enrolled'),
        ('Cost per enquiry', 'marketing.cost_per_enquiry'), ('Owner phone', 'marketing.owner_phone')) + [
        FF('Spend of this kind, all months', 'SUMIFS({range:marketing.cost},{range:marketing.kind},%s)' % LK('marketing', 'campaign_id', 'kind'), 'money'),
        FF('Children enrolled from this kind', 'SUMIFS({range:marketing.enrolled},{range:marketing.kind},%s)' % LK('marketing', 'campaign_id', 'kind'), 'int')]),
    FORM('openday_sheet', 'Open Day Sign-up Sheet', 'Tour day with the families booked', 'tour_cal.date', F(
        ('Date', 'tour_cal.date'), ('Weekday', 'tour_cal.weekday'), ('Host', 'tour_cal.staff'), ('Tours booked', 'tour_cal.tours_booked'), ('Free slots', 'tour_cal.free_slots'), ('Slot check', 'tour_cal.slot_flag')) + [
        FF('Date of the next open day', '{set:open_day_date}', 'date')],
        {"from": "tours", "match": "tours.date", "columns": ["name", "phone", "room", "source", "status", "staff"], "max": 8}),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('welcome_doc', 'Welcome Letter', 'Welcome letter to a new enquiry', 'enquiries.enquiry_id', [
        'Welcome letter of {set:company}, dated {today}. Dear {col:enquiries.name}, thank you for your enquiry of {col:enquiries.date}.',
        'You asked about a place in {col:enquiries.want_room} on {col:enquiries.want_schedule} from {col:enquiries.want_start}. The weekly rate for those days is {col:enquiries.weekly_value}. The registration fee is {col:enquiries.reg_fee}. Fees are before any tax.',
        'The best next step is a tour. You see the rooms, meet the team and ask about days, hours and meals. A tour takes about {set:tour_minutes} minutes and your child is welcome to come.', 'Please call or write to book a time. We reply within {set:reply_hours_target} hours.'], ['Owner-director', 'Family'], NOTE),
    DOC('tour_confirm_doc', 'Tour Confirmation', 'Tour confirmation for a family', 'tours.tour_id', [
        'Tour confirmation of {set:company}, dated {today}. Family: {col:tours.name}, phone {col:tours.phone}.',
        'Your tour is booked for {col:tours.date} with {col:tours.staff}. You will see the {col:tours.room} room. Please come a few minutes early.', 'If you cannot come, tell us at least a day ahead so that we can offer the time to another family.',
        'After the tour we answer your questions about days, hours, fees and the start date.'], ['Staff member', 'Family'], NOTE),
    DOC('tour_followup_doc', 'Tour Follow-up Letter', 'Follow-up letter after a tour', 'tours.tour_id', [
        'Letter of {set:company}, dated {today}. Dear {col:tours.name}, thank you for visiting us on {col:tours.date}.',
        'We enjoyed meeting you. If the center suits your family, the next steps are the application form, the signed forms and the registration fee. We then hold a place in the {col:tours.room} room as soon as one is free.',
        'Questions about days, hours or the start date are welcome at any time. Please call {col:tours.owner_phone}.', 'We hope to welcome your family.'], ['Owner-director', 'Family'], NOTE),
    DOC('wl_letter_doc', 'Waiting List Letter', 'Waiting list confirmation letter', 'waitlist.wait_id', [
        'Waiting list letter of {set:company}, dated {today}. Dear {col:waitlist.name}, your family is on our waiting list.',
        'Entry {col:waitlist.wait_id}: room {col:waitlist.room}, schedule {col:waitlist.schedule}, wanted start {col:waitlist.want_start}. Added on {col:waitlist.added_on}. Priority: {col:waitlist.priority}.',
        'A place on the waiting list is not a promise of a place. When a place is free we offer it by phone and you have {set:offer_days} days to answer. We ask you to confirm every {set:recheck_days} days that you still need the place.',
        'Please tell us at once if your plans change.'], ['Owner-director', 'Family'], NOTE),
    DOC('offer_letter_doc', 'Place Offer Letter', 'Offer of a place', 'offers.offer_id', [
        'Place offer of {set:company}, dated {today}. Dear {col:offers.name}, we are glad to offer your child a place in {col:offers.room}.',
        'The offer was made on {col:offers.offered_on}. Please give your answer by {col:offers.offer_due}. After that date the place goes to the next family on the list.',
        'To accept, sign below and return the application forms, the deposit and the registration fee. A deposit is a payment held to keep a place, applied to the last invoice.', 'Please call {col:offers.phone} or the center to ask any question.'], ['Owner-director', 'Family'], NOTE),
    DOC('enrol_confirm_doc', 'Enrolment Confirmation', 'Enrolment confirmation for a child', 'children.child_id', [
        'Enrolment confirmation of {set:company}, dated {today}. Child: {col:children.child}, family {col:children.family}. Guardian: {col:children.guardian}.',
        'Room: {col:children.room}. Schedule: {col:children.schedule}, {col:children.days} days a week. Start date: {col:children.start_date}. Weekly tuition: {col:children.weekly_rate}.',
        'The place is held for the schedule above. A change of days needs notice in writing. Check the contract terms for notice, fees and late pickup.', 'We look forward to the first day.'], ['Owner-director', 'Guardian'], NOTE),
    DOC('rate_sheet_doc', 'Fee and Rate Sheet', 'Fee and rate sheet for a room and schedule', 'rates.rate_id', [
        'Fee and rate sheet of {set:company}, dated {today}. Room: {col:rates.room}. Schedule: {col:rates.schedule}, {col:rates.days} days a week, {col:rates.hours_day} hours a day.',
        'Weekly rate: {col:rates.weekly_rate}. Last year: {col:rates.last_year_rate}. Change: {col:rates.rise_pct}. Rate for one day: {col:rates.day_rate}. Monthly rate: {col:rates.monthly_rate}.',
        'A lower fee for a second child in the same family: {col:rates.sibling_rate} a week. Staff child rate: {col:rates.staff_rate} a week. Registration fee: {set:reg_fee}.', 'All fees are before any tax. Rates are reviewed once a year.'], ['Owner-director', 'Family'], NOTE),
    DOC('wl_checkin_doc', 'Waiting List Check-in Letter', 'Check-in letter to a waiting family', 'waitlist.wait_id', [
        'Check-in letter of {set:company}, dated {today}. Dear {col:waitlist.name}, you have been on our waiting list since {col:waitlist.added_on}, which is {col:waitlist.days_waiting} days.',
        'Please tell us if you still need a place in {col:waitlist.room} on {col:waitlist.schedule} and whether the wanted start of {col:waitlist.want_start} is still right. Check: {col:waitlist.wait_flag}.',
        'If we do not hear from you within {set:offer_days} days we will offer the place to the next family and take you off the list. You can join again at any time.', 'Please call us or write back.'], ['Owner-director', 'Family'], NOTE),
    DOC('no_place_doc', 'No Place Yet Letter', 'Letter when no place is free yet', 'enquiries.enquiry_id', [
        'Letter of {set:company}, dated {today}. Dear {col:enquiries.name}, thank you for your enquiry of {col:enquiries.date}.',
        'We have no free place in {col:enquiries.want_room} for {col:enquiries.want_schedule} from {col:enquiries.want_start}. We are sorry. We can add your family to the waiting list, and we offer places in the order of the list and the days wanted.',
        'You are welcome to visit while you wait. We tell families as soon as a place opens and you then have {set:offer_days} days to answer.', 'Please tell us if you would like to join the waiting list.'], ['Owner-director', 'Family'], NOTE),
    DOC('open_day_doc', 'Open Day Invitation', 'Open day invitation', 'enquiries.enquiry_id', [
        'Open day invitation of {set:company}, dated {today}. Dear {col:enquiries.name}, we invite you to our open day on {col:enquiries.open_day}.',
        'You see every room, meet the teachers and the owner-director and ask about days, hours, meals and fees. You enquired on {col:enquiries.date} about {col:enquiries.want_room}.',
        'Children are welcome. Please tell us how many will come so that we can plan the rooms and the tour slots.', 'Please call {col:enquiries.owner_phone} to reserve a time.'], ['Owner-director', 'Family'], NOTE),
    DOC('start_plan_doc', 'Start-Date Plan', 'Start-date plan for a room and month', 'places.place_id', [
        'Start-date plan of {set:company}, dated {today}. Room: {col:places.room}. Month: {col:places.month}.',
        'Places: {col:places.capacity}. Children booked at month end: {col:places.booked}. Leavers: {col:places.leavers}. Starters: {col:places.starters}. Free places: {col:places.free_places}. Free place check: {col:places.free_flag}.',
        'Occupancy at month end: {col:places.occupancy}, against a wanted {set:occupancy_target}. Weekly revenue left empty: {col:places.weekly_left}.', 'Offer the free places to the families on the waiting list in the order of the Fill Candidates sheet. Write the decision below.'], ['Owner-director', 'Assistant director'], NOTE),
    DOC('handbook_doc', 'Family Handbook Cover', 'Family handbook cover page', 'children.child_id', [
        'Family handbook of {set:company}, dated {today}. For the family of {col:children.family}. Child: {col:children.child}. Room: {col:children.room}. Start date: {col:children.start_date}.',
        'This handbook explains days and hours, fees, pickup, meals, sick days, closures and how we talk to families. Please read it before the first day and sign the page at the end.',
        'Your guardian contact on file: {col:children.guardian}, {col:children.phone}. Tell us at once if a phone number or a pickup person changes.', 'Check your local rules for any notice or consent a family must give.'], ['Owner-director', 'Guardian'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_enquiry', 'New Enquiry Steps', 'enquiries', 'enquiries.date', [('Write the enquiry in the Enquiries sheet', 0), ('Reply to the family within the target hours', 0), ('Offer two tour times', 1), ('Send the welcome letter and the rate sheet', 1), ('Call the family if there is no answer', 3), ('Note the source and the wanted start', 3), ('Close the enquiry if nothing comes back', 30)]),
    CHK('tour_day', 'Tour Day Steps', 'tours', 'tours.date', [('Confirm the tour with the family the day before', -1), ('Tidy the room that the family will see', 0), ('Have the rate sheet and the application form ready', 0), ('Welcome the family and show every room', 0), ('Answer questions about days, hours and meals', 0), ('Record whether the tour was held', 0), ('Rebook a missed tour', 1)]),
    CHK('after_tour', 'After the Tour Steps', 'tours', 'tours.date', [('Send the thank-you message the same day', 0), ('Send the application form and the next steps', 1), ('Write the outcome of the tour', 1), ('Call the family if no application arrives', 5), ('Offer a place on the waiting list if no place is free', 7), ('Close the enquiry if nothing comes back', 30)]),
    CHK('application_in', 'Application Received Steps', 'applications', 'applications.applied_on', [('Check that the form is complete', 0), ('Record the registration fee and the deposit', 0), ('Ask for missing forms', 2), ('Check the room and schedule against the free places', 3), ('Confirm the start date in writing', 5), ('Add the family to the waiting list if no place is free', 5), ('Chase forms and deposit that are still missing', 10)]),
    CHK('wl_add', 'Waiting List Entry Steps', 'waitlist', 'waitlist.added_on', [('Write the entry with room, schedule and wanted start', 0), ('Set the priority by your own rule', 0), ('Send the waiting list letter', 1), ('Tell the family how long families usually wait', 1), ('Re-confirm at the re-confirm limit', 90), ('Remove the family if no answer comes', 120)]),
    CHK('offer_run', 'Place Offer Steps', 'offers', 'offers.offered_on', [('Check the free place and the room', 0), ('Call the family and offer the place', 0), ('Send the offer letter with the answer date', 0), ('Chase on the day before the answer is due', 6), ('Release the place after the answer date', 8), ('Offer the place to the next family', 8), ('Record the answer in the Offer Log', 8)]),
    CHK('enrol_run', 'Enrolment Steps', 'children', 'children.start_date', [('Receive the signed forms', -28), ('Receive the deposit and the registration fee', -28), ('Add the child to the Children sheet and the room', -21), ('Send the enrolment confirmation', -21), ('Tell the assistant director for billing', -14), ('Share the family handbook', -14), ('Confirm the start date and pickup people', -3)]),
    CHK('first_week', 'First Week Preparation Steps', 'children', 'children.start_date', [('Tell the lead teacher and the cook', -7), ('Prepare the cubby and the name tag', -2), ('Call the family the day before the first day', -1), ('Welcome the family on the first day', 0), ('Send a short note on the first day', 0), ('Check in with the family after one week', 7), ('Review how the settling went', 14)]),
    CHK('wl_review', 'Waiting List Review Steps', 'funnel', 'funnel.month', [('List the families waiting in each room', 1), ('Re-confirm families past the re-confirm limit', 2), ('Remove families who do not answer', 7), ('Compare waiting families with the free places ahead', 8), ('Recruit more families for rooms with free places', 10), ('Write the decisions in the review notes', 12)]),
    CHK('mk_review', 'Marketing Review Steps', 'marketing', 'marketing.month', [('Add the spend of the month', 2), ('Count the enquiries and the children enrolled from each source', 3), ('Work out the cost per enrolled child', 4), ('Keep, change or drop each kind of spend', 5), ('Ask new families how they found you', 10), ('Plan next month spend', 14)]),
    CHK('open_day_run', 'Open Day Steps', 'tour_cal', 'tour_cal.date', [('Book the date and tell the team', -28), ('Invite families on the waiting list and recent enquiries', -21), ('Order the signs and the printed rate sheets', -14), ('Confirm the families who will come', -2), ('Prepare the rooms and the tour route', -1), ('Run the open day and record who came', 0), ('Send a thank-you message to every family', 1), ('Count the applications from the open day', 14)]),
    CHK('intake_meeting', 'Weekly Intake Meeting Steps', 'tour_cal', 'tour_cal.date', [('Count the enquiries still waiting for a first reply', 0), ('Check the tours booked for the week', 0), ('Check the free places by room', 0), ('Match the waiting families with the free places', 0), ('Assign the calls and the offers', 0), ('Write the actions in the notes', 0)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('e_first', 'Enquirer: first reply', 'enquiries', 'enquiries.phone', 'Hello {name}, thank you for contacting {center}. We may have a place for a child of {child_age_months} months in {want_room}. May we call you today to answer your questions and book a tour?'),
    M('e_tour_times', 'Enquirer: choose a tour time', 'enquiries', 'enquiries.phone', 'Hello {name}, we would be glad to show you {center}. A tour takes about 45 minutes. Reply with a day and time that suit you and we will confirm.'),
    M('e_slow', 'Enquirer: sorry for the slow reply', 'enquiries', 'enquiries.phone', 'Hello {name}, sorry for the wait. Your enquiry of {date} deserved a faster answer from {center}. May we call you today about {want_room}?'),
    M('e_rate', 'Enquirer: the weekly rate', 'enquiries', 'enquiries.phone', 'Hello {name}, at {center} the weekly rate for {want_room} on {want_schedule} is {weekly_value}. The registration fee is {reg_fee}. Shall we book a tour?'),
    M('e_open_day', 'Enquirer: open day invitation', 'enquiries', 'enquiries.phone', 'Hello {name}, {center} holds an open day on {open_day}. You can see the rooms and meet the team. Would you like us to keep a time for you?'),
    M('e_start', 'Enquirer: your wanted start date', 'enquiries', 'enquiries.phone', 'Hello {name}, you would like to start on {want_start}. We are checking the places in {want_room} and will come back to you this week. {center}'),
    M('e_no_place', 'Enquirer: no place yet, join the list', 'enquiries', 'enquiries.phone', 'Hello {name}, {want_room} is full for {want_schedule} right now. We can add your family to the waiting list at {center} from {want_start}. Shall we?'),
    M('e_close', 'Enquirer: still need a place?', 'enquiries', 'enquiries.phone', 'Hello {name}, we have not heard from you since {date}. Do you still need a place at {center}? Reply and we will help. If not, we will close your enquiry.'),
    M('e_bring', 'Enquirer: before your visit', 'enquiries', 'enquiries.phone', 'Hello {name}, before your visit to {center}, please think about the days, hours and meals you need. Your child is welcome to come along.'),
    M('e_age', 'Enquirer: the room for the age', 'enquiries', 'enquiries.phone', 'Hello {name}, a child of {child_age_months} months would join the {want_room} room at {center}. We can explain how the room works when we meet.'),
    M('e_source', 'Enquirer: thanks for finding us', 'enquiries', 'enquiries.phone', 'Hello {name}, thank you for finding {center} through {source}. We would like to meet you and your child. Which day is best for a tour?'),
    M('e_sched', 'Enquirer: confirm the days wanted', 'enquiries', 'enquiries.phone', 'Hello {name}, please confirm that you want {want_schedule} in {want_room} from {want_start}. We then check the free places for you. {center}'),
    M('t_confirm', 'Enquirer: tour confirmed', 'tours', 'tours.phone', 'Hello {name}, your tour at {center} is booked for {date} with {staff}. Reply if you need to change it.'),
    M('t_remind', 'Enquirer: tour reminder', 'tours', 'tours.phone', 'Hello {name}, a reminder of your tour at {center} on {date}. We will show you the {room} room. Please come a few minutes early.'),
    M('t_missed', 'Enquirer: we missed you at the tour', 'tours', 'tours.phone', 'Hello {name}, we missed you at your tour on {date}. Would you like to book another time at {center}? Reply with a day that suits you.'),
    M('t_thanks', 'Enquirer: thanks for visiting', 'tours', 'tours.phone', 'Hello {name}, thank you for visiting {center} on {date}. Would you like the application form? We can hold a place in {room} once forms and fee are in.'),
    M('t_apply', 'Enquirer: next steps after the tour', 'tours', 'tours.phone', 'Hello {name}, after your tour on {date} the next steps at {center} are the application, the signed forms and the registration fee. Shall we send the form?'),
    M('a_forms', 'Enquirer: forms still missing', 'applications', 'applications.phone', 'Hello {name}, we received your application on {applied_on}. We still need the signed forms for {room}. Please return them this week. {center}'),
    M('a_deposit', 'Enquirer: deposit is the last step', 'applications', 'applications.phone', 'Hello {name}, your forms are in. The deposit is the last step to hold your place in {room} on {schedule}. {center}'),
    M('a_ready', 'Enquirer: application complete', 'applications', 'applications.phone', 'Hello {name}, your application is complete. Your planned start is {want_start} in {room} on {schedule}. We will confirm in writing. {center}'),
    M('a_chase', 'Enquirer: days since you applied', 'applications', 'applications.phone', 'Hello {name}, it is {days_since} days since you applied to {center}. Please tell us if you still want the place in {room}.'),
    M('w_checkin', 'Waiting family: please re-confirm', 'waitlist', 'waitlist.phone', 'Hello {name}, you have been on the waiting list at {center} for {days_waiting} days. Do you still need a place in {room} on {schedule}? Please reply so that we keep your place on the list.'),
    M('w_offer', 'Waiting family: a place is free', 'offers', 'offers.phone', 'Hello {name}, good news from {center}: a place is free in {room}. Please tell us by {offer_due} whether you accept.'),
    M('f_welcome', 'Family: welcome to the center', 'children', 'children.phone', 'Hello {guardian}, we look forward to welcoming {child} to {center} on {start_date} in {room}. Please call us if you have any question.'),
    M('f_forms', 'Family: papers before day one', 'children', 'children.phone', 'Hello {guardian}, before {child} starts on {start_date}, please bring the signed forms and the pickup person details to {center}.'),
    M('f_week', 'Family: how was the first week', 'children', 'children.phone', 'Hello {guardian}, {child} has now spent a week in {room} at {center}. How did it go for your family? We are glad to talk.'),
    M('ow_new', 'Owner: enquiry has no reply', 'enquiries', 'enquiries.owner_phone', 'Hello, {name} asked about {want_room} on {date} and still has no reply. Please call {phone}. Reply check: {reply_flag}.'),
    M('ow_noshow', 'Owner: a family missed the tour', 'tours', 'tours.owner_phone', 'Hello, {name} did not come to the tour on {date}. Please call {phone} to rebook. Outcome: {outcome_flag}.'),
    M('ow_fill', 'Owner: place to fill today', 'fill', 'fill.owner_phone', 'Hello, a place is free in {room}. Best match on the list: {name} on {schedule}, worth {weekly_value} a week. Please make the offer.'),
    M('ow_offer', 'Owner: offer answer due', 'offers', 'offers.owner_phone', 'Hello, the offer to {name} for {room} is due on {offer_due}. Status: {offer_flag}. Please chase or release the place.'),
    M('ow_mk', 'Owner: marketing cost review', 'marketing', 'marketing.owner_phone', 'Hello, {kind} cost {cost} in {month} and brought {enrolled} children. Cost per enrolled child: {cost_per_enrolled}. Keep, change or drop?'),
    M('ad_tour', 'Assistant director: tour to host', 'tours', 'tours.director_phone', 'Hello, a tour with {name} is on {date} at {center}. Please meet the family at the door and show the {room} room. Family phone: {phone}.'),
    M('lt_start', 'Lead teacher: a child starts', 'children', 'children.teacher_phone', 'Hello, {child} starts on {start_date} in {room} on {schedule}. Guardian: {guardian}. Please prepare the cubby and the name tag. {center}'),
    M('ck_start', 'Cook: a child starts', 'children', 'children.cook_phone', 'Hello, {child} starts on {start_date}. Please check the meal plan with {guardian} before the first day. {center}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
D30 = '{range:enquiries.date},">="&({today}-30),{range:enquiries.date},"<="&{today}'
D90 = '{range:enquiries.date},">="&({today}-90),{range:enquiries.date},"<="&{today}'
T90 = '{range:tours.date},">="&({today}-90),{range:tours.date},"<="&{today}'
F6 = '{range:funnel.month},">="&EDATE(%s,-6),{range:funnel.month},"<"&%s' % (MS, MS)
HELD, NOSHOW, BOOKED = tok('tourstatus', 'Held'), tok('tourstatus', 'No-show'), tok('tourstatus', 'Booked')
WW, ENR, LOST = tok('waitstatus', 'Waiting'), tok('estatus', 'Enrolled'), tok('estatus', 'Lost')
kpis = [
    KPI('Enquiries, last 30 days', 'COUNTIFS(%s)' % D30, 'int'),
    KPI('Enquiries waiting for a first reply', 'COUNTIFS({range:enquiries.reply_flag},%s)' % ca('No reply yet'), 'int'),
    KPI('Average hours to a first reply, 90 days', 'IFERROR(AVERAGEIFS({range:enquiries.first_reply_hours},%s),0)' % D90, 'num'),
    KPI('Replies within the target, 90 days', 'IFERROR(COUNTIFS(%s,{range:enquiries.reply_flag},%s)/(COUNTIFS(%s,{range:enquiries.reply_flag},%s)+COUNTIFS(%s,{range:enquiries.reply_flag},%s)),0)' % (D90, ca('Reply in time'), D90, ca('Reply in time'), D90, ca('Slow reply')), 'pct'),
    KPI('Tours booked in the next 7 days', 'COUNTIFS({range:tours.date},">="&{today},{range:tours.date},"<="&({today}+6),{range:tours.status},%s)' % BOOKED, 'int'),
    KPI('Free tour slots in the next 7 days', 'SUMIFS({range:tour_cal.free_slots},{range:tour_cal.date},"<="&({today}+6))', 'int'),
    KPI('Tours held, last 30 days', 'COUNTIFS({range:tours.date},">="&({today}-30),{range:tours.date},"<="&{today},{range:tours.status},%s)' % HELD, 'int'),
    KPI('Tour no-show rate, 90 days', 'IFERROR(COUNTIFS(%s,{range:tours.status},%s)/(COUNTIFS(%s,{range:tours.status},%s)+COUNTIFS(%s,{range:tours.status},%s)),0)' % (T90, NOSHOW, T90, NOSHOW, T90, HELD), 'pct'),
    KPI('Applications, last 30 days', 'COUNTIFS({range:applications.applied_on},">="&({today}-30),{range:applications.applied_on},"<="&{today})', 'int'),
    KPI('Applications missing forms or deposit', 'COUNTIFS({range:applications.status},%s)+COUNTIFS({range:applications.status},%s)' % (tok('appstatus', 'Forms pending'), tok('appstatus', 'Deposit pending')), 'int'),
    KPI('Children starting this month', 'SUMIFS({range:funnel.enrolled},{range:funnel.month},%s)' % MS, 'int'),
    KPI('Starts per enquiry, last 6 months', 'IFERROR(SUMIFS({range:funnel.enrolled},%s)/SUMIFS({range:funnel.enquiries},%s),0)' % (F6, F6), 'pct'),
    KPI('Tours booked per enquiry, 6 months', 'IFERROR(SUMIFS({range:funnel.tours_booked},%s)/SUMIFS({range:funnel.enquiries},%s),0)' % (F6, F6), 'pct'),
    KPI('Applications per tour held, 6 months', 'IFERROR(SUMIFS({range:funnel.applications},%s)/SUMIFS({range:funnel.tours_held},%s),0)' % (F6, F6), 'pct'),
    KPI('Families on the waiting list', 'COUNTIFS({range:waitlist.status},%s)' % WW, 'int'),
    KPI('Weekly tuition waiting for a place', 'SUMIFS({range:waitlist.weekly_value},{range:waitlist.status},%s)' % WW, 'money'),
    KPI('Waiting families to re-confirm now', 'COUNTIFS({range:waitlist.wait_flag},%s)' % ca('Re-confirm now'), 'int'),
    KPI('Offers waiting for an answer', 'COUNTIFS({range:offers.offered_on},">0",{range:offers.answered_on},"")', 'int'),
    KPI('Offers accepted, share of answered', 'IFERROR(COUNTIFS({range:offers.answer},%s)/COUNTIFS({range:offers.answered_on},">0"),0)' % tok('offerans', 'Accepted'), 'pct'),
    KPI('Average days to answer an offer', 'IFERROR(AVERAGEIFS({range:offers.days_to_answer},{range:offers.answered_on},">0"),0)', 'num'),
    KPI('Free places now, all rooms', 'SUMIFS({range:places.free_places},{range:places.month},%s)' % MS, 'int'),
    KPI('Rooms with a free place', 'COUNTIFS({range:places.month},%s,{range:places.free_flag},1)' % MS, 'int'),
    KPI('Occupancy now, all rooms', 'IFERROR(1-SUMIFS({range:places.free_places},{range:places.month},%s)/SUM({range:rooms.capacity}),0)' % MS, 'pct'),
    KPI('Weekly tuition left empty', 'SUMIFS({range:places.weekly_left},{range:places.month},%s)' % MS, 'money'),
    KPI('Marketing spend, last 12 months', 'SUMIFS({range:marketing.cost},{range:marketing.month},">="&EDATE(%s,-12))' % MS, 'money'),
    KPI('Cost per enrolled child, 12 months', 'IFERROR(SUMIFS({range:marketing.cost},{range:marketing.month},">="&EDATE(%s,-12))/SUMIFS({range:marketing.enrolled},{range:marketing.month},">="&EDATE(%s,-12)),0)' % (MS, MS), 'money'),
    KPI('Enquiries lost, last 90 days', 'COUNTIFS(%s,{range:enquiries.status},%s)' % (D90, LOST), 'int'),
    KPI('Weekly tuition lost, 12 months', 'SUM({range:lost.weekly_lost})', 'money'),
    KPI('Best source by revenue per child', 'IFERROR(INDEX({range:sources.source},MATCH(MAX({range:sources.revenue_child}),{range:sources.revenue_child},0)),"")', 'text'),
    KPI('Stale enquiries to act on', 'COUNTIFS({range:stale.days_since},">="&{set:stale_days})', 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Intake Dashboard", "kpis": kpis,
    "monthly": {"title": "Enquiries, tours held, applications and children starting", "date": "funnel.month", "series": [
        {"label": "Enquiries", "sum": "funnel.enquiries", "date": "funnel.month"}, {"label": "Tours held", "sum": "funnel.tours_held", "date": "funnel.month"},
        {"label": "Applications", "sum": "funnel.applications", "date": "funnel.month"}, {"label": "Children starting", "sum": "funnel.enrolled", "date": "funnel.month"}]},
    "breakdowns": [{"title": "Enquiries by source", "by": "enquiries.source", "value": "enquiries.weekly_value", "agg": "count"}, {"title": "Marketing spend by kind", "by": "marketing.kind", "value": "marketing.cost", "agg": "sum"},
                   {"title": "Waiting list entries by room", "by": "waitlist.room", "value": "waitlist.weekly_value", "agg": "count"}, {"title": "Weekly tuition lost by reason", "by": "lost.reason", "value": "lost.weekly_lost", "agg": "sum"}]}
insights = {"filters": [{"label": "Room", "list": "room"}, {"label": "Enquiry source", "list": "source"}, {"label": "Enquiry status", "list": "estatus"}],
    "gauges": [
        {"title": "Replies within the target hours", "num": AGG('count', 'enquiries', where=[('reply_flag', '=', ca('Reply in time'))]), "den": AGG('count', 'enquiries', where=[('reply_flag', '<>', ca('No reply yet'))])},
        {"title": "Places booked, all months shown", "num": AGG('sum', 'places', 'places.booked'), "den": AGG('sum', 'places', 'places.capacity')},
        {"title": "Tours held, not missed", "num": AGG('count', 'tours', where=[('status', '=', HELD)]), "den": AGG('count', 'tours', where=[('status', '<>', BOOKED)])},
        {"title": "Tours that led to an application", "num": AGG('count', 'tours', where=[('applied', '=', YES)]), "den": AGG('count', 'tours', where=[('status', '=', HELD)])},
        {"title": "Enquiries that enrolled", "num": AGG('count', 'enquiries', where=[('status', '=', ENR)]), "den": AGG('count', 'enquiries')},
        {"title": "Offers answered in the days allowed", "num": AGG('count', 'offers', where=[('answered_on', '>', 0), ('days_to_answer', '<=', '{set:offer_days}')]), "den": AGG('count', 'offers', where=[('answered_on', '>', 0)])}],
    "charts": [
        CHART('Enquiries per month', 'column', 'month', [AGG('count', 'enquiries', date='enquiries.date', label='Enquiries')]),
        CHART('Enquiries by source', 'bar', 'enquiries.source', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Tours held and missed per month', 'column', 'month', [AGG('count', 'tours', date='tours.date', where=[('status', '=', HELD)], label='Held'), AGG('count', 'tours', date='tours.date', where=[('status', '=', NOSHOW)], label='No-show')]),
        CHART('Applications per month', 'column', 'month', [AGG('count', 'applications', date='applications.applied_on', label='Applications')]),
        CHART('Children starting per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.enrolled', date='funnel.month', label='Children starting')]),
        CHART('Starts per enquiry by month', 'line', 'month', [AGG('avg', 'funnel', 'funnel.conversion', date='funnel.month', label='Starts per enquiry')]),
        CHART('Tour show rate by month', 'line', 'month', [AGG('avg', 'funnel', 'funnel.show_rate', date='funnel.month', label='Show rate')]),
        CHART('Hours to a first reply by month', 'line', 'month', [AGG('avg', 'enquiries', 'enquiries.first_reply_hours', date='enquiries.date', label='Hours to a first reply')]),
        CHART('Enrolled share by reply time band', 'bar', 'reply_bands.band', [AGG('avg', 'reply_bands', 'reply_bands.enrolled_share', label='Enrolled share')]),
        CHART('Lost enquiries by reason', 'bar', 'lost.reason', [AGG('sum', 'lost', 'lost.lost_enquiries', label='Lost enquiries')]),
        CHART('Weekly tuition lost by reason', 'bar', 'lost.reason', [AGG('sum', 'lost', 'lost.weekly_lost', label='Weekly tuition lost')]),
        CHART('Average free places by room, months ahead', 'bar', 'places.room', [AGG('avg', 'places', 'places.free_places', where=[('month', '>=', '{today}')], label='Free places')]),
        CHART('Average occupancy by room, past months', 'bar', 'places.room', [AGG('avg', 'places', 'places.occupancy', where=[('month', '<=', '{today}')], label='Occupancy')]),
        CHART('Waiting families by room', 'bar', 'waitlist.room', [AGG('count', 'waitlist', where=[('status', '=', WW)], label='Waiting families')]),
        CHART('Waiting families by priority', 'bar', 'waitlist.priority', [AGG('count', 'waitlist', where=[('status', '=', WW)], label='Waiting families')]),
        CHART('Offers by answer', 'bar', 'offers.answer', [AGG('count', 'offers', label='Offers')]),
        CHART('Marketing spend per month', 'column', 'month', [AGG('sum', 'marketing', 'marketing.cost', date='marketing.month', label='Marketing spend')]),
        CHART('Marketing spend by kind', 'bar', 'marketing.kind', [AGG('sum', 'marketing', 'marketing.cost', label='Marketing spend')]),
        CHART('Cost per enrolled child by kind', 'bar', 'marketing.kind', [AGG('avg', 'marketing', 'marketing.cost_per_enrolled', label='Cost per enrolled child')]),
        CHART('Yearly revenue per child by source', 'bar', 'sources.source', [AGG('avg', 'sources', 'sources.revenue_child', label='Revenue per child')]),
        CHART('Tours by room shown', 'bar', 'tours.room', [AGG('count', 'tours', label='Tours')]),
        CHART('Enquiries by room wanted', 'bar', 'enquiries.want_room', [AGG('count', 'enquiries', label='Enquiries')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Place-filling decision by room", "why": "a free place is ranked against every waiting family by the tuition it brings over the weeks ahead, with the best match, the second choice and the verdict", "where": "Place-Filling Decision"},
    {"name": "Fill candidates with a rank per room", "why": "every waiting family scored by weekly tuition, wanted start and the free places in the room, so the next offer is never a guess", "where": "Fill Candidates"},
    {"name": "Waitlist start-date matcher", "why": "type the room, days and wanted start of a family and see if a place is free on that date, who is ahead and the first month with a place", "where": "Waitlist Start-Date Matcher"},
    {"name": "Tour funnel with your own history", "why": "enquiry, tour, application and start, each step set against your own last 6 months, with the leakiest step named", "where": "Tour Funnel Conversion"},
    {"name": "Reply-time impact on enrolments", "why": "enrolment share after a fast and a slow first reply, with the tuition a faster reply would add each year", "where": "Reply-Time Impact"},
    {"name": "Source value ranked by tuition", "why": "each enquiry source ranked by the yearly tuition of the children it enrolled, not by the number of enquiries", "where": "Referral Source Value Ranker"},
    {"name": "Marketing keep, change or drop", "why": "cost per enrolled child and months to pay back from the tuition you keep, for every kind of spend", "where": "Marketing Keep or Drop"},
    {"name": "Offer answer tracker", "why": "answer due date, days left, the day to chase and the day to release a place, with your own answer times from the Offer Log", "where": "Offer Answer Tracker"},
    {"name": "Starters and occupancy scenarios", "why": "Base, Best and Worst scenarios for starters and leavers in every room, with occupancy and the staff needed at the ratio", "where": "Starters Occupancy Scenario"},
    {"name": "Priority rule comparer", "why": "who wins the next place under date added, sibling first and staff child first, and which rule costs the longest waiter least", "where": "Priority Rule Comparer"},
    {"name": "Intake pipeline forecast", "why": "enquiries for the next 3 months from your own pattern and last year, turned into starts and set against the free places ahead", "where": "Intake Pipeline Forecast"}]
competitors = [
    {"what": "free enquiry log templates", "lacks": "list names and dates but never time the first reply, rank the waiting families or tell you which source brings paying children"},
    {"what": "subscription childcare-management software", "lacks": "charge every month for an intake module that hides how a place is chosen and cannot test your own priority rule"},
    {"what": "single-sheet waiting lists", "lacks": "sort by date added only, with no free places by room, no start-date match and no weekly tuition waiting for a place"},
    {"what": "generic sales pipeline spreadsheets", "lacks": "know leads and deals but not rooms, schedules, tour slots, offer answer dates or the lost reasons of a childcare center"},
    {"what": "paper tour and visit books", "lacks": "record who came but never count no-shows, applications after a tour or the cost of an open day"}]
guide = [
    'Open Start and type your center name and your own limits in the yellow cells: target hours to a first reply, wanted occupancy, days a family has to answer an offer and the days before a waiting family is re-confirmed.',
    'Check Rooms, Rates and Team. They hold the places and the weekly rate of each room and schedule that the other sheets look up.',
    'Write every enquiry in Enquiries: date, name, phone, room, days and wanted start, source and hours to a first reply. The reply check, the rate and the weekly value fill in by themselves.',
    'Book each tour in Tours and check the Tour Calendar for free slots. Record whether the tour was held or missed and whether the family applied.',
    'Log each application in Applications. The paperwork check tells you when forms or the deposit are still missing.',
    'Keep the Waiting List up to date. Waiting families to re-confirm and the weekly tuition waiting for a place show on the dashboard.',
    'Open Fill Candidates and Places by Room and Month when a place is free. They rank the waiting families by tuition and show the free places by room.',
    'Write each place offer in the Offer Log with the date and, when the family answers, the answer. The offer check shows open and overdue offers.',
    'Fill Marketing Spend and Marketing by Kind each month, and read Source Value and Lost Reasons to see which spend and which fixes pay back.',
    'Use Funnel by Month and Reply Time Bands to see where families drop out between the enquiry and the first day.',
    f'Use the {len(tools)} calculators to choose who gets a place, test a start date, find the leakiest funnel step, rank sources, test marketing, plan tour slots and forecast the next months.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Intake Dashboard and the charts every week: enquiries, tours, applications, starts, waiting families, free places and lost tuition.']
listing = {"title": "Childcare Center Enquiries, Tours and Waiting List Excel Template: Tour Funnel, Place Offers, Free Places, Marketing Return",
    "headline": "Fill every free place faster, from the first enquiry to the first day",
    "tags": ["childcare", "daycare", "waiting list", "enquiry tracker", "tour tracker", "childcare center", "excel template", "daycare enrolment", "place offers", "occupancy", "home daycare", "intake funnel", "preschool admin"],
    "description": ("Run the intake side of a home daycare or childcare center in one Excel workbook. Built for an owner-director and an assistant director who answer enquiries, give tours, keep a waiting list and fill free places by room. "
        "Enquiries records every family with the source, the wanted room and days, the hours to a first reply and the weekly rate of the days wanted. Tours and the Tour Calendar show booked, held and missed tours and the free slots. Applications show when forms or the deposit are still missing.\n\n"
        "The Waiting List holds each family with priority and days waiting. Fill Candidates ranks the waiting families for every free place by the tuition they bring over the weeks ahead, and Places by Room and Month shows the free places, the occupancy (children booked as a share of licensed places) and the weekly tuition left empty. "
        "The Offer Log tracks each place offer, the answer date and the answer. Funnel by Month, Reply Time Bands, Source Value, Lost Reasons and Marketing by Kind show where families drop out and which spend brings paying children.\n\n"
        f"{len(tools)} calculators cover the place-filling decision, the start-date match, the tour funnel, reply-time impact, source value, marketing keep or drop, lost-enquiry causes, unfilled tuition by room, tour slots, the waiting list clear-down, offer answers, starter scenarios, the waiting list value, open days, follow-up dates, priority rules, a price cut and a forecast of the next 3 months. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to enquirers, waiting families, families, the owner-director, the assistant director, a lead teacher and the cook.\n\n"
        "This is part one of the Home Daycare and Childcare Center suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Children appear by name, room and dates only, with no medical detail. It helps you keep track of your intake and does not promise results. Check your local rules for licensing, ratios and records."),
    "features": ["Place-filling decision ranked by tuition", "Waiting list with priority and days waiting", "Tour calendar with free slots", "Tour funnel against your own history", "Offer log with answer dates", "Free places and occupancy by room",
                 "Source value and marketing return", "Lost reasons and tuition lost", f"{len(tools)} calculators for intake decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
HINTS = {
 'enquiries': 'One row per enquiry: contact, wanted room and start, source, hours to the first reply, status and dates; the days to a tour, the reply check, the weekly value and message fields fill in.',
 'waitlist': 'One row per family waiting for a place: room, schedule, wanted start, priority and offer dates; the days waiting, the weekly value, the offer due date and the list check fill in by themselves.',
 'marketing': 'One row per month and spend item (directory, website, sign, flyers, open day, referral reward): cost, enquiries and children enrolled; the cost per enquiry and per enrolled child fill in.',
 'children': 'One row per child (first name and family name only): family, room, schedule, days a week, start and end date and status; the weekly rate, place-days and message fields fill in by themselves.',
 'places': 'One row per room and month: licensed places, children booked, leavers and starters; the free places at month end, the occupancy and the weekly revenue left empty fill in by themselves.',
 'funnel': 'One row per month: enquiries, tours booked, held and missed, applications and children starting, all counted from other sheets; the starts per enquiry and show rate fill in.',
 'applications': 'One row per application: room, schedule, wanted start, forms back, deposit paid (a payment held to keep a place) and status; the days since applying and the paperwork check fill in.',
 'fill': 'One row per family waiting or holding an offer: weekly value and wanted start from the Waiting List; the free places, revenue over the weeks ahead and the ranks fill in by themselves.',
 'place_fill': 'Pick a room with a free place: waiting families are ranked by the tuition they bring over the weeks ahead; see who to offer, the second choice and the verdict.',
 'funnel_tool': 'Type the last 3 months from Funnel by Month and your hours to a first reply; each step is set against your own previous 6 months and the weakest step is named.',
 'source_rank': 'Pick an enquiry source: the children it enrolled, yearly tuition per child and spend; it is ranked among all sources by tuition, with a feed, hold or cut verdict.',
 'mk_keep': 'Pick a kind of marketing spend: cost, children enrolled, cost per enrolled child and months to pay back from the tuition you keep, set against the payback you chose.',
 'reply_impact': 'Type your usual hours to a first reply, the enquiries a month and the weekly tuition of a child; see the share that enrol after a fast or slow reply and the tuition a faster reply adds.',
 'clear_down': 'Type the days waited, the days since you last spoke, the priority, the days to the wanted start and the free places; see whether to offer, re-confirm, keep waiting or remove.',
 'offer_tracker': 'Type the date you offered a place and the days to answer; see the due date, the days left and whether to wait, chase today or release the place, with your own answer times.',
 'starters_scn': 'Pick the start month and a Base, Best or Worst scenario and type starters and leavers by room; see children, occupancy and staff needed at the ratio (check your local rules).',
 'open_day': 'Type what the open day cost, the families who came, the applications and the children enrolled; see the cost of each step and the months to pay back against your own earlier open days.',
 'priority_rule': 'Type three waiting families, their days waited and whether each has a sibling or is a staff child; see who wins under each rule and which rule is fairest to the longest waiter.',
 'price_lost': 'Type the fee cut, the weekly tuition, the families who get the lower fee and the share of price-lost families you win back; see the break-even number of families.',
 'intake_forecast': 'Pick a Base, Best or Worst scenario: enquiries for 3 months follow your own pattern and last year, starts follow your own rate, set against the free places 3 months ahead.',
}
for _t in tables + tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
s = spec(id=f'{SUITE}-p1', slug='childcare-center-enquiries', profession='Home Daycare and Childcare Center', name='Enquiries, Tours and Waitlist',
         tagline='Fill every free place faster, from the first enquiry to the first day', price_usd=29,
         colors={"primary": "#33658A", "accent": "#F6AE2D"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Enquiries, tours and waiting list"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
