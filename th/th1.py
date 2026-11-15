"""Therapy private practice suite - part 1: Intake, Screening and Waitlist."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th1_lists import *
from th1_tables import settings, tables, CA
from th1_tools import tools

SUITE = 'fx-20261115-therapy-practice'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
def cnt(tb, col, pick): return 'COUNTIFS({range:%s.%s},INDEX({range:%s.%s},MATCH({pick},{range:%s},0)))' % (tb, col, tb, col, pick)

forms = [
 FORM('enquiry_sheet', 'Enquiry Sheet', 'Enquiry with reply speed and first appointment', 'enquiries.enquiry_id', F(
  ('Date', 'enquiries.date'), ('Name', 'enquiries.name'), ('Contact person', 'enquiries.contact'), ('Phone', 'enquiries.phone'), ('Client type', 'enquiries.client_type'), ('Service', 'enquiries.service'),
  ('Source', 'enquiries.source'), ('Referrer', 'enquiries.referrer'), ('Contact method', 'enquiries.contact_method'), ('Priority', 'enquiries.priority'), ('Hours to first reply', 'enquiries.reply_hours'),
  ('Reply speed check', 'enquiries.reply_flag'), ('Screening date', 'enquiries.screening_date'), ('Screened by', 'enquiries.screened_by'), ('Status', 'enquiries.status'), ('Clinician', 'enquiries.clinician'),
  ('First session', 'enquiries.first_session'), ('Days to screening', 'enquiries.days_to_screening'), ('Days to first appointment', 'enquiries.days_to_first'), ('Target check', 'enquiries.wait_check'))),
 FORM('screening_sheet', 'Screening Call Sheet', 'Screening call with next step', 'screening.call_id', F(
  ('Date', 'screening.date'), ('Enquiry ID', 'screening.enquiry_id'), ('Enquired on', 'screening.enquired_on'), ('Name', 'screening.name'), ('Phone', 'screening.phone'), ('Screened by', 'screening.screened_by'),
  ('Minutes', 'screening.minutes'), ('Suitable', 'screening.suitable'), ('Urgency', 'screening.urgency'), ('Next step', 'screening.next_step'), ('Days after the enquiry', 'screening.days_after')) + [
  FF('Calls by this person', cnt('screening', 'screened_by', 'screening.call_id'), 'int'), FF('Average minutes of all calls', 'AVERAGE({range:screening.minutes})', 'num')]),
 FORM('callback_sheet', 'Call-back Sheet', 'Call-back attempt', 'callbacks.callback_id', F(
  ('Date', 'callbacks.date'), ('Enquiry ID', 'callbacks.enquiry_id'), ('Name', 'callbacks.name'), ('Phone', 'callbacks.phone'), ('Attempt', 'callbacks.attempt'), ('Method', 'callbacks.method'), ('Reached', 'callbacks.reached'),
  ('Next try', 'callbacks.next_try'), ('Attempts left', 'callbacks.attempts_left'), ('Call-back check', 'callbacks.call_flag')) + [FF('Call-backs for this enquiry', cnt('callbacks', 'enquiry_id', 'callbacks.callback_id'), 'int')]),
 FORM('waitlist_sheet', 'Waitlist Entry Sheet', 'Waitlist entry with place and target', 'waiting.wait_id', F(
  ('Added on', 'waiting.added_on'), ('Enquiry ID', 'waiting.enquiry_id'), ('Name', 'waiting.name'), ('Phone', 'waiting.phone'), ('Client type', 'waiting.client_type'), ('Service', 'waiting.service'), ('Priority', 'waiting.priority'),
  ('Status', 'waiting.status'), ('Days waiting', 'waiting.days_waiting'), ('Target days to offer', 'waiting.target_days'), ('Target check', 'waiting.wait_check'), ('Days over target', 'waiting.days_over'),
  ('Act-first rank', 'waiting.act_rank'), ('Place on the list for the service', 'waiting.place'))),
 FORM('checkin_sheet', 'Waitlist Check-in Sheet', 'Waitlist check-in with answer', 'checkins.checkin_id', F(
  ('Date', 'checkins.date'), ('Wait ID', 'checkins.wait_id'), ('Name', 'checkins.name'), ('Phone', 'checkins.phone'), ('Contacted by', 'checkins.contacted_by'), ('Answer', 'checkins.answer'), ('Still waiting', 'checkins.still_waiting'),
  ('Added on', 'checkins.added_on'), ('Weeks on the list', 'checkins.weeks_on_list'), ('Next check-in', 'checkins.next_checkin'))),
 FORM('offer_sheet', 'Offer Sheet', 'Offer of a regular time', 'offers.offer_id', F(
  ('Offered on', 'offers.offered_on'), ('Wait ID', 'offers.wait_id'), ('Name', 'offers.name'), ('Phone', 'offers.phone'), ('Clinician', 'offers.clinician'), ('Weekday', 'offers.weekday'), ('Time', 'offers.time'), ('Reply by', 'offers.reply_by'),
  ('Answer', 'offers.answer'), ('Answered on', 'offers.answered_on'), ('Days to answer', 'offers.days_to_answer')) + [FF('Offers to this person', cnt('offers', 'wait_id', 'offers.offer_id'), 'int')]),
 FORM('booking_sheet', 'Intake Booking Sheet', 'First session booking', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Client type', 'clients.client_type'), ('Contact person', 'clients.contact'), ('Phone', 'clients.phone'), ('Service', 'clients.service'), ('Clinician', 'clients.clinician'), ('Booked on', 'clients.booked_on'),
  ('First session', 'clients.first_session'), ('First session time', 'clients.first_time'), ('Room', 'clients.room'), ('Format', 'clients.format'), ('Days booking to first session', 'clients.days_to_first'), ('Clinician phone', 'clients.clinician_phone'))),
 FORM('deposit_sheet', 'Deposit Receipt Sheet', 'Deposit received', 'deposits.deposit_id', F(
  ('Date', 'deposits.date'), ('Client ID', 'deposits.client_id'), ('Client', 'deposits.client'), ('Client phone', 'deposits.phone'), ('Amount', 'deposits.amount'), ('Status', 'deposits.status'), ('Applied on', 'deposits.applied_on'), ('Days held', 'deposits.days_held')) + [
  FF('Deposits held now, all clients', 'COUNTIFS({range:deposits.status},%s)' % tok('depst', 'Held'), 'int')]),
 FORM('paperwork_sheet', 'Intake Paperwork Sheet', 'Intake paperwork status', 'paperwork.client_id', F(
  ('Client', 'paperwork.client'), ('Client phone', 'paperwork.phone'), ('First session', 'paperwork.first_session'), ('Forms sent on', 'paperwork.forms_sent_on'), ('Forms back on', 'paperwork.forms_back_on'), ('Consent back', 'paperwork.consent_back'),
  ('Details checked', 'paperwork.details_checked'), ('Forms check', 'paperwork.form_flag')) + [FF('Forms still to come back', 'COUNTIFS({range:paperwork.form_flag},%s)+COUNTIFS({range:paperwork.form_flag},%s)' % (ck('Missing, session passed'), ck('Open, session ahead')), 'int')]),
 FORM('signpost_sheet', 'Signposting Sheet', 'Signposting record', 'signpost.signpost_id', F(
  ('Enquiry ID', 'signpost.enquiry_id'), ('Enquired on', 'signpost.enquired_on'), ('Signposted on', 'signpost.date'), ('Name', 'signpost.name'), ('Phone', 'signpost.phone'), ('Service needed', 'signpost.service'), ('Referred to', 'signpost.referred_to'),
  ('Reason', 'signpost.reason'), ('Information sent', 'signpost.info_sent'), ('Within 7 days check', 'signpost.same_week'))),
 FORM('lost_sheet', 'Lost Enquiry Sheet', 'Lost enquiry with cause and re-contact', 'lost.enquiry_id', F(
  ('Date', 'lost.date'), ('Name', 'lost.name'), ('Phone', 'lost.phone'), ('Service', 'lost.service'), ('Client type', 'lost.client_type'), ('Cause', 'lost.cause'), ('Last contact', 'lost.last_contact'), ('Re-contact date', 'lost.recontact_date'),
  ('Days open', 'lost.days_open'), ('Re-contact check', 'lost.recontact_flag')) + [FF('Enquiries lost to the same cause', cnt('lost', 'cause', 'lost.enquiry_id'), 'int')]),
 FORM('newclient_sheet', 'New Client Summary Sheet', 'New client summary with fee, forms and deposit', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Contact person', 'clients.contact'), ('Phone', 'clients.phone'), ('Service', 'clients.service'), ('Clinician', 'clients.clinician'), ('Fee type', 'clients.fee_type'), ('Sliding scale share', 'clients.sliding_pct'),
  ('List fee', 'clients.list_fee'), ('Fee per session', 'clients.fee_quote'), ('Frequency', 'clients.frequency'), ('Sessions attended', 'clients.sessions_attended')) + [
  FF('Forms check', 'IFERROR(INDEX({range:paperwork.form_flag},MATCH({pick},{range:paperwork.client_id},0)),"")', 'text'),
  FF('Deposit status', 'IFERROR(INDEX({range:deposits.status},MATCH({pick},{range:deposits.client_id},0)),"")', 'text')]),
]
assert len(forms) == 12

def D_(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('welcome_doc', 'Welcome Letter', 'Welcome letter for a new client', 'clients.client_id', [
  'Welcome letter of {set:company}, dated {today}. Dear {col:clients.client},', 'Thank you for choosing us. Your first session is on {col:clients.first_session} at {col:clients.first_time} with {col:clients.clinician}. Room or format: {col:clients.room} ({col:clients.format}).',
  'Your fee is {col:clients.fee_quote} per session. If you cannot come, please tell us at least {set:late_cancel_hours} hours before. A cancellation with less than {set:late_cancel_hours} hours\' notice (a late cancel) is charged {set:late_fee_pct} of the session fee, unless we agree otherwise.',
  'Please arrive 5 minutes early and bring your completed intake forms. Contact us if anything is unclear.'], ['Practice team']),
 D_('confirm_doc', 'First Session Confirmation', 'First session confirmation', 'clients.client_id', [
  'First session confirmation of {set:company}, dated {today}.', 'Client: {col:clients.client}. Service: {col:clients.service}. Clinician: {col:clients.clinician}.',
  'Date: {col:clients.first_session}. Time: {col:clients.first_time}. Place: {col:clients.room} ({col:clients.format}). Booked on {col:clients.booked_on}, {col:clients.days_to_first} days after booking.',
  'Please bring your completed intake forms. Please give {set:late_cancel_hours} hours\' notice if you need to change the time.'], ['Front desk']),
 D_('waitlist_doc', 'Waitlist Letter', 'Waitlist letter with place and expected wait', 'waiting.wait_id', [
  'Waitlist letter of {set:company}, dated {today}. Dear {col:waiting.name},', 'You joined our waitlist for {col:waiting.service} on {col:waiting.added_on}. Your place on the list for this service is {col:waiting.place}. Priority: {col:waiting.priority}.',
  'We aim to offer you a regular time within {col:waiting.target_days} days. You have waited {col:waiting.days_waiting} days so far.', 'To stay on the list, please answer our check-in message, which we send every {set:checkin_weeks} weeks. If your plans change, tell us and we will update the list.'], ['Front desk']),
 D_('offer_doc', 'Offer of a Regular Time', 'Offer of a regular time', 'offers.offer_id', [
  'Offer of a regular time from {set:company}, dated {today}. Dear {col:offers.name},', 'We can offer you a regular time with {col:offers.clinician} on {col:offers.weekday} at {col:offers.time}, starting from the date we agree together.',
  'Please reply by {col:offers.reply_by}. If we do not hear from you, we will offer the time to the next person and you keep your place on the waitlist.', 'Offer made on {col:offers.offered_on}. Reference {col:offers.offer_id}.'], ['Front desk']),
 D_('signpost_doc', 'Signposting Letter', 'Signposting letter', 'signpost.signpost_id', [
  'Signposting letter of {set:company}, dated {today}. Dear {col:signpost.name},', 'Thank you for contacting us on {col:signpost.enquired_on} about {col:signpost.service}. We cannot offer you a place soon enough, so we suggest you contact: {col:signpost.referred_to}.',
  'This may help you sooner. You are welcome to contact us again. In an emergency contact your local emergency number.', 'Reference {col:signpost.signpost_id}.'], ['Front desk']),
 D_('deposit_doc', 'Deposit Receipt', 'Deposit receipt', 'deposits.deposit_id', [
  'Deposit receipt of {set:company}, dated {today}. Receipt {col:deposits.deposit_id}.', 'Received on {col:deposits.date} from {col:deposits.client} (client {col:deposits.client_id}): a deposit of {col:deposits.amount}.',
  'Status: {col:deposits.status}. The deposit is taken off your first invoice once you attend. If you cancel with less than {set:late_cancel_hours} hours\' notice or miss the first session, we may keep the deposit; agree the details with us.'], ['Front desk']),
 D_('pack_doc', 'Intake Pack Cover Letter', 'Intake pack cover letter', 'paperwork.client_id', [
  'Intake pack of {set:company}, dated {today}. Dear {col:paperwork.client},', 'Your first session is on {col:paperwork.first_session}. Please complete the enclosed intake forms and return them by e-mail or in person at least {set:forms_days} days before.',
  'We sent the forms on {col:paperwork.forms_sent_on}. Forms check: {col:paperwork.form_flag}. The forms include consent and your contact details; check your own local rules on what you must complete.'], ['Front desk']),
 D_('info_doc', 'Practice Information Sheet', 'Practice information sheet for one service', 'services.service', [
  'Practice information of {set:company}, dated {today}.', 'Service: {col:services.service}. A session lasts {col:services.minutes} minutes. The list fee is {col:services.fee} per session, before any tax.',
  'We are open Monday to Saturday. Sessions are in person, by video or by phone. We start with a first assessment session (the intake). A lower fee agreed from your means (a sliding scale) may be available; ask the front desk.',
  'An organisation that pays part of your fee (a third-party payer) may be an insurer, an employer scheme or a public body in your area; ask us how it works.'], ['Practice team']),
 D_('referral_doc', 'Referral Acknowledgement', 'Referral received acknowledgement', 'enquiries.enquiry_id', [
  'Referral acknowledgement of {set:company}, dated {today}. Dear {col:enquiries.referrer},', 'Thank you. We received your referral on {col:enquiries.date}, reference {col:enquiries.enquiry_id}.',
  'We will contact the person you referred. For privacy we do not share any other details unless the person agrees; check your own local rules.'], ['Front desk']),
 D_('closed_doc', 'Enquiry Closed Letter', 'Enquiry closed letter', 'lost.enquiry_id', [
  'Enquiry closed letter of {set:company}, dated {today}. Dear {col:lost.name},', 'We tried to reach you about your enquiry of {col:lost.date} for {col:lost.service} and last contacted you on {col:lost.last_contact}, so we have closed it.',
  'You are welcome to contact us again at any time and we will open a new enquiry. Reference {col:lost.enquiry_id}.'], ['Front desk']),
 D_('intake_report_doc', 'Weekly Intake Report', 'Weekly intake report for one clinician and week', 'capacity.row_id', [
  'Weekly intake report of {set:company}, dated {today}. Week of {col:capacity.week}. Clinician: {col:capacity.clinician}.', 'Free slots: {col:capacity.free_slots}. Intakes booked: {col:capacity.intakes_booked}. Weekly intake limit: {set:intake_limit_week}.',
  'Intakes still possible: {col:capacity.intakes_possible}. Check: {col:capacity.cap_flag}.', 'Decisions for the weekly intake meeting are written below.'], ['Owner', 'Coordinator']),
 D_('waitlist_report_doc', 'Waitlist Report by Service', 'Waitlist report for one service and month', 'demand.row_id', [
  'Waitlist report of {set:company}, dated {today}. Month {col:demand.month}. Service: {col:demand.service}.', 'Enquiries: {col:demand.enquiries}. Booked: {col:demand.booked}. Still waiting: {col:demand.still_waiting}. Booked share of enquiries: {col:demand.booked_share}.',
  'Compare the booked share with the wanted conversion of {set:target_conv} and decide whether to open more intake slots for this service.'], ['Owner']),
]
assert len(documents) == 12

import lib as _lib
def CS(key_, title, table, start, steps): return _lib.CHK(key_, title, table, start, steps)
checklists = [
 CS('c_enquiry', 'New Enquiry Steps', 'enquiries', 'enquiries.date', [('Reply to the enquiry within one working day', 1), ('Record the source and the referrer', 0), ('Set the priority', 0), ('Book the screening call', 1), ('Send the thank-you message', 1), ('Check the match rules for a clinician', 2)]),
 CS('c_screen', 'Screening Call Steps', 'screening', 'screening.date', [('Check the enquiry and the priority before the call', 0), ('Ask about the service and the times that suit', 0), ('Record the minutes, suitability and urgency', 0), ('Choose the next step', 0), ('Send the follow-up message', 1), ('Update the enquiry log', 1)]),
 CS('c_callback', 'No-reply Call-back Steps', 'callbacks', 'callbacks.date', [('Call at a different time of day', 0), ('Send a text message if allowed', 1), ('Try again after the gap days', 3), ('Send the last message before closing', 6), ('Close the enquiry and record the cause', 8)]),
 CS('c_waitadd', 'Adding to the Waitlist Steps', 'waiting', 'waiting.added_on', [('Record service, client type and priority', 0), ('Tell the person their place and the target days', 0), ('Agree how to stay in touch', 1), ('Set the first check-in date', 1), ('Tell the clinician team about the new entry', 2)]),
 CS('c_offer', 'Making an Offer Steps', 'offers', 'offers.offered_on', [('Check the clinician has the slot', 0), ('Send the offer with the reply-by date', 0), ('Remind the person after one day', 1), ('Record the answer', 3), ('Offer the slot to the next person if declined', 3), ('Book the first session if accepted', 3)]),
 CS('c_first', 'Booking the First Session Steps', 'clients', 'clients.first_session', [('Send the intake forms', -10), ('Take the deposit', -7), ('Confirm date, time and room', -5), ('Check the forms are back', -2), ('Send a reminder', -1), ('Prepare the room or the video session', 0), ('Record the attendance', 1)]),
 CS('c_deposit', 'Taking a Deposit Steps', 'deposits', 'deposits.date', [('Explain the deposit and what it covers', 0), ('Take the payment', 0), ('Send the receipt', 0), ('Record the deposit as held', 0), ('Apply it to the first invoice after the session', 7)]),
 CS('c_paper', 'Paperwork and Consent Steps', 'paperwork', 'paperwork.forms_sent_on', [('Send the forms', 0), ('Remind if not back after 3 days', 3), ('Check consent is returned; check your own local rules', 5), ('Check contact details', 5), ('Record the forms as back', 6)]),
 CS('c_signpost', 'Signposting an Enquiry Steps', 'signpost', 'signpost.date', [('Decide where the person is best served', 0), ('Send the list of other services', 0), ('Record where and why', 0), ('Ask if they found a place', 14)]),
 CS('c_noshow', 'Intake No-show Follow-up Steps', 'intake', 'intake.date', [('Call the client the same day', 0), ('Send a message with a new time', 0), ('Decide whether to keep the deposit', 1), ('Offer the freed slot to the waitlist', 0), ('Close the enquiry if there is no answer', 7)]),
 CS('c_review', 'Monthly Waitlist Review Steps', 'funnel', 'funnel.month', [('Count people waiting by service', 1), ('Check who is over the target', 1), ('Contact the people waiting longest', 2), ('Compare offers with new joiners', 3), ('Decide on extra intake slots', 5)]),
 CS('c_meeting', 'Weekly Intake Meeting Steps', 'capacity', 'capacity.week', [('Review free slots and intakes possible', 0), ('Match waiting people to free slots', 0), ('Check the high priority list', 0), ('Agree the offers for the week', 1), ('Note actions for the coordinator', 1)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('e_thanks', 'Enquirer: screening call booked', 'enquiries', 'enquiries.phone', 'Hello {name}, thank you for contacting {company}. Your screening call is on {screening_date}. Reply here if the time does not suit you.'),
 M('e_tried', 'Enquirer: we tried to call you', 'callbacks', 'callbacks.phone', 'Hello {name}, we tried to call you today about your enquiry. Please message {company} when you can, or tell us a good time to call.'),
 M('e_choose', 'Enquirer: choose a time for the call', 'enquiries', 'enquiries.phone', 'Hello {name}, please tell us a time that suits you for a short screening call about {service}. {company}'),
 M('e_listed', 'Enquirer: you are on the waitlist', 'waiting', 'waiting.phone', 'Hello {name}, you are on the waitlist at {company} for {service}. We aim to offer you a place within {target_days} days.'),
 M('e_wait', 'Enquirer: your expected wait', 'waiting', 'waiting.phone', 'Hello {name}, your expected wait for {service} is about {target_days} days from {added_on}. We will contact you when a regular time is free. {company}'),
 M('e_checkin', 'Enquirer: stay on the list', 'checkins', 'checkins.phone', 'Hello {name}, you are on our waitlist (week {weeks_on_list}). Please reply to stay on the list. {company}'),
 M('e_free', 'Enquirer: a regular time is free', 'offers', 'offers.phone', 'Hello {name}, a regular time is free with {clinician} on {weekday} at {time}. Please reply by {reply_by} to take it. {company}'),
 M('e_confirm', 'Enquirer: confirm the offered time', 'offers', 'offers.phone', 'Hello {name}, please confirm the time offered with {clinician} ({weekday}, {time}) by {reply_by}, or we will offer it to the next person. {company}'),
 M('e_notaken', 'Enquirer: you keep your place', 'offers', 'offers.phone', 'Hello {name}, the time offered on {offered_on} was not taken. You keep your place on the waitlist and we will offer another time. {company}'),
 M('e_closed', 'Enquirer: enquiry closed', 'lost', 'lost.phone', 'Hello {name}, we could not reach you about your enquiry on {date}, so we have closed it. You are welcome to contact {company} again at any time.'),
 M('e_signpost', 'Enquirer: other services', 'signpost', 'signpost.phone', 'Hello {name}, thank you for contacting {company}. For {service} you may be seen sooner by: {referred_to}. We have sent you the details.'),
 M('e_cancel', 'Enquirer: a cancellation this week', 'waiting', 'waiting.phone', 'Hello {name}, we have a cancellation this week for a first session for {service}. Reply today if you would like it. {company}'),
 M('c_first', 'New client: your first session', 'clients', 'clients.phone', 'Hello {client}, your first session at {company} is on {first_session} at {first_time} with {clinician}.'),
 M('c_forms', 'New client: complete the intake forms', 'paperwork', 'paperwork.phone', 'Hello {client}, please complete the intake forms before your first session on {first_session}. {company}'),
 M('c_late', 'New client: forms have not reached us', 'paperwork', 'paperwork.phone', 'Hello {client}, your intake forms have not reached us yet. Please send them before your first session on {first_session}. {company}'),
 M('c_deposit', 'New client: deposit received', 'deposits', 'deposits.phone', 'Hello {client}, your deposit of {amount} is received. It will be taken off your first invoice. {company}'),
 M('c_expect', 'New client: what to expect', 'clients', 'clients.phone', 'Hello {client}, at your first session on {first_session} {clinician} will explain how we work together and answer your questions. Please arrive 5 minutes early. {company}'),
 M('c_fees', 'New client: fees and late-cancel rule', 'clients', 'clients.phone', 'Hello {client}, your fee is {fee_quote} per session. Please give at least 24 hours\' notice to cancel; later cancellations may be charged part of the fee. {company}'),
 M('c_find', 'New client: where to come', 'clients', 'clients.phone', 'Hello {client}, your first session on {first_session} is booked for {room}. Please arrive 5 minutes early and give your name at the front desk. {company}'),
 M('c_online', 'New client: video session link follows', 'clients', 'clients.phone', 'Hello {client}, if your first session on {first_session} is a video session, the link follows by e-mail before the session. {company}'),
 M('c_remind', 'New client: reminder for tomorrow', 'clients', 'clients.phone', 'Hello {client}, a reminder of your first session tomorrow, {first_session} at {first_time}, with {clinician}. {company}'),
 M('c_missed', 'New client: we missed you', 'intake', 'intake.client_phone', 'Hello {client}, we missed you at your first session on {date}. Please contact {company} to book another time.'),
 M('k_new', 'Clinician: a new client is booked', 'clients', 'clients.clinician_phone', 'Hello {clinician}, new client {client} is booked on {first_session} at {first_time} ({service}).'),
 M('k_take', 'Clinician: can you take a new client', 'match', 'match.clinician_phone', 'Hello {clinician}, can you take a {service} client ({client_type}) this month? You have {free_28d} free slots in the next 28 days.'),
 M('k_noshow', 'Clinician: an intake no-show', 'intake', 'intake.clinician_phone', 'Hello {clinician}, an intake no-show today: {client}, {date}. Please note it for the follow-up.'),
 M('k_high', 'Clinician: a high priority call back', 'screening', 'screening.screener_phone', 'Hello {screened_by}, the high priority enquiry from {name} (call {call_id}) needs a call back today.'),
 M('o_call', 'Coordinator: call back today', 'callbacks', 'callbacks.coordinator_phone', 'Hello, please call back {name} today: attempt {attempt}, enquiry {enquiry_id}.'),
 M('o_checkin', 'Coordinator: check-in is due', 'checkins', 'checkins.coordinator_phone', 'Hello, the waitlist check-in for {name} is due on {next_checkin}.'),
 M('o_forms', 'Coordinator: intake forms missing', 'paperwork', 'paperwork.coordinator_phone', 'Hello, intake forms are missing for {client}. The first session is on {first_session}.'),
 M('o_deposit', 'Coordinator: deposit not paid', 'deposits', 'deposits.coordinator_phone', 'Hello, the deposit {deposit_id} for {client} is not paid yet; it has been held {days_held} days.'),
 M('w_over', 'Owner: waitlist passed the target', 'waiting', 'waiting.owner_phone', 'Hello, the waitlist for {service} passed the target: {name} has waited {days_waiting} days against a target of {target_days}.'),
 M('w_report', 'Owner: weekly intake report ready', 'capacity', 'capacity.owner_phone', 'Hello, the weekly intake report is ready: week of {week}, {clinician} has {free_slots} free slots and {intakes_possible} intakes possible.'),
 M('w_long', 'Owner: an enquiry waited too long', 'enquiries', 'enquiries.owner_phone', 'Hello, the enquiry from {name} on {date} for {service} has waited longer than the target for a first appointment.'),
 M('r_thanks', 'Referrer: referral received', 'enquiries', 'enquiries.referrer_phone', 'Hello {referrer}, thank you. {company} received your referral on {date} and will contact the person you referred.'),
]
assert len(messages) == 34

# practice name column on every table that sends a message
need = {m['table'] for m in messages}
for t in tables:
    if t['key'] in need and not any(c['key'] == 'company' for c in t['columns']): t['columns'].append(CA('company', 'Practice', 'text', '{set:company}&""', 24))
for t in tables:
    if t['key'] == 'clients':
        for c in t['columns']:
            if c['key'] == 'company': c['formula'] = '{set:company}&""'
for t in tables:
    if t['key'] == 'capacity': t['columns'].append(CA('owner_phone', 'Phone to message', 'text', 'IFERROR(INDEX({range:team.phone},1)&"","")', 18))

MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'
def D90(c): return '{range:%s},">="&({today}-90),{range:%s},"<="&{today}' % (c, c)
WAIT = tok('waitst', 'Waiting')
kpis = [
 KPI('Enquiries, last 7 days', 'COUNTIFS({range:enquiries.date},">="&({today}-6),{range:enquiries.date},"<="&{today})', 'int'),
 KPI('Enquiries last 30 days', 'COUNTIFS({range:enquiries.date},">="&({today}-29),{range:enquiries.date},"<="&{today})', 'int'),
 KPI('Screening calls done, last 30 days', 'COUNTIFS({range:screening.date},">="&({today}-29),{range:screening.date},"<="&{today})', 'int'),
 KPI('Screening calls booked next 7 days', 'COUNTIFS({range:enquiries.screening_date},">="&{today},{range:enquiries.screening_date},"<="&({today}+7))', 'int'),
 KPI('New enquiries waiting for a first call', 'COUNTIFS({range:enquiries.status},%s)' % tok('enqst', 'New'), 'int', alert={"when": "> 5", "style": "warn"}),
 KPI('Days to screening, last 90 days', 'IFERROR(AVERAGEIFS({range:enquiries.days_to_screening},%s),0)' % D90('enquiries.date'), 'num', alert={"when": "> {set:screen_days}", "style": "warn"}),
 KPI('Replied in 1 working day, last 90 days', 'IFERROR(COUNTIFS({range:enquiries.reply_flag},%s,%s)/COUNTIFS(%s),0)' % (ck('Replied in time'), D90('enquiries.date'), D90('enquiries.date')), 'pct', alert={"when": "< {set:target_reply_rate}", "style": "bad"}),
 KPI('New clients booked, last 30 days', 'COUNTIFS({range:clients.booked_on},">="&({today}-29),{range:clients.booked_on},"<="&{today})', 'int'),
 KPI('Enquiry conversion, last 90 days', 'IFERROR(COUNTIFS({range:enquiries.status},%s,%s)/COUNTIFS(%s),0)' % (tok('enqst', 'Booked'), D90('enquiries.date'), D90('enquiries.date')), 'pct', alert={"when": "< {set:target_conv}", "style": "warn"}),
 KPI('Days to first appointment, last 90 days', 'IFERROR(AVERAGEIFS({range:enquiries.days_to_first},%s),0)' % D90('enquiries.date'), 'num', alert={"when": "> {set:target_wait_days}", "style": "bad"}),
 KPI('First sessions next 14 days', 'COUNTIFS({range:clients.first_session},">="&{today},{range:clients.first_session},"<="&({today}+14))', 'int'),
 KPI('People on the waitlist', 'COUNTIFS({range:waiting.status},%s)' % WAIT, 'int'),
 KPI('Waiting over their target days', 'COUNTIFS({range:waiting.status},%s,{range:waiting.wait_check},%s)' % (WAIT, ck('Over target')), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Longest wait, days', '{today}-SUMPRODUCT(MIN(({range:waiting.status}=%s)*{range:waiting.added_on}+({range:waiting.status}<>%s)*99999))' % (WAIT, WAIT), 'int'),
 KPI('High priority people waiting', 'COUNTIFS({range:waiting.status},%s,{range:waiting.priority},%s)' % (WAIT, tok('prio', 'High')), 'int'),
 KPI('Children waiting', 'COUNTIFS({range:waiting.status},%s,{range:waiting.client_type},%s)' % (WAIT, tok('ctype', 'Child')), 'int'),
 KPI('People who gave up waiting this year', 'COUNTIFS({range:waiting.status},%s,{range:waiting.withdrawn_on},">="&DATE(YEAR({today}),1,1))' % tok('waitst', 'Withdrawn'), 'int'),
 KPI('Offers made last 30 days', 'COUNTIFS({range:offers.offered_on},">="&({today}-30),{range:offers.offered_on},"<="&{today})', 'int'),
 KPI('Offer acceptance, last 90 days', 'IFERROR(COUNTIFS({range:offers.answer},%s,%s)/COUNTIFS({range:offers.answer},"<>"&%s,%s),0)' % (tok('answer', 'Accepted'), D90('offers.offered_on'), tok('answer', 'Waiting'), D90('offers.offered_on')), 'pct', alert={"when": "< {set:target_accept}", "style": "warn"}),
 KPI('Intake no-shows, last 90 days', 'COUNTIFS({range:intake.status},%s,%s)' % (tok('sstatus', 'No-show'), D90('intake.date')), 'int'),
 KPI('Intake show rate, last 90 days', 'IFERROR(COUNTIFS({range:intake.status},%s,%s)/(COUNTIFS({range:intake.status},%s,%s)+COUNTIFS({range:intake.status},%s,%s)+COUNTIFS({range:intake.status},%s,%s)),0)' % (
     tok('sstatus', 'Attended'), D90('intake.date'), tok('sstatus', 'Attended'), D90('intake.date'), tok('sstatus', 'No-show'), D90('intake.date'), tok('sstatus', 'Late cancel'), D90('intake.date')), 'pct', alert={"when": "< {set:target_show_rate}", "style": "warn"}),
 KPI('Lost enquiries last 30 days', 'COUNTIFS({range:lost.date},">="&({today}-29),{range:lost.date},"<="&{today})', 'int'),
 KPI('Lost to long waits, last 90 days', 'COUNTIFS({range:lost.cause},%s,%s)' % (tok('cause', 'Waited too long'), D90('lost.date')), 'int'),
 KPI('Signposted enquiries, last 30 days', 'COUNTIFS({range:signpost.date},">="&({today}-29),{range:signpost.date},"<="&{today})', 'int'),
 KPI('Deposits held now', 'COUNTIFS({range:deposits.status},%s)' % tok('depst', 'Held'), 'int'),
 KPI('Deposit value held', 'SUMIFS({range:deposits.amount},{range:deposits.status},%s)' % tok('depst', 'Held'), 'money'),
 KPI('Deposits kept after no-show, 12 months', 'COUNTIFS({range:deposits.status},%s,{range:deposits.date},">="&({today}-365))' % tok('depst', 'Kept'), 'int'),
 KPI('Intake forms not back', 'COUNTIFS({range:paperwork.form_flag},%s)+COUNTIFS({range:paperwork.form_flag},%s)' % (ck('Missing, session passed'), ck('Open, session ahead')), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Average days waited, people waiting now', 'IFERROR(AVERAGEIFS({range:waiting.days_waiting},{range:waiting.status},%s),0)' % WAIT, 'num'),
 KPI('Clinicians taking new clients', 'COUNTIFS({range:team.takes_flag},%s)' % ck('Takes new clients'), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Intake KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Enquiries, bookings, starts and people who gave up", "date": "funnel.month", "series": [
   {"label": "Enquiries", "sum": "funnel.enquiries", "date": "funnel.month"}, {"label": "Booked", "sum": "funnel.booked", "date": "funnel.month"},
   {"label": "Started", "sum": "funnel.started", "date": "funnel.month"}, {"label": "Gave up waiting", "sum": "funnel.withdrawn", "date": "funnel.month"}]},
 "breakdowns": [{"title": "Enquiries by status", "by": "enquiries.status", "agg": "count"}, {"title": "Waitlist by service", "by": "waiting.service", "agg": "count"},
                {"title": "Lost enquiries by cause", "by": "lost.cause", "agg": "count"}, {"title": "Intake sessions by clinician", "by": "intake.clinician", "agg": "count"}]}
W_ = lambda c, o, v: (c, o, v)
insights = {"filters": [{"label": "Clinician", "list": "clin"}, {"label": "Service", "list": "svc"}, {"label": "Client type", "list": "ctype"}],
 "gauges": [
  {"title": "Enquiries that became bookings", "num": AGG('count', 'enquiries', where=[('status', '=', tok('enqst', 'Booked'))]), "den": AGG('count', 'enquiries')},
  {"title": "Enquiries replied within 1 working day", "num": AGG('count', 'enquiries', where=[('reply_flag', '=', ck('Replied in time'))]), "den": AGG('count', 'enquiries', where=[('reply_hours', '>', 0)])},
  {"title": "First sessions within the target wait", "num": AGG('count', 'enquiries', where=[('days_to_first', '<=', '{set:target_wait_days}')]), "den": AGG('count', 'enquiries', where=[('days_to_first', '>=', 0)])},
  {"title": "Intake show rate", "num": AGG('count', 'intake', where=[('status', '=', tok('sstatus', 'Attended'))]), "den": AGG('count', 'intake', where=[('status', '<>', tok('sstatus', 'Scheduled')), ('status', '<>', tok('sstatus', 'Cancelled'))])},
  {"title": "Offers accepted", "num": AGG('count', 'offers', where=[('answer', '=', tok('answer', 'Accepted'))]), "den": AGG('count', 'offers', where=[('answer', '<>', tok('answer', 'Waiting'))])},
  {"title": "Intake forms back before first session", "num": AGG('count', 'paperwork', where=[('form_flag', '=', ck('Back on time'))]), "den": AGG('count', 'paperwork', where=[('form_flag', '<>', ck('Open, session ahead'))])}],
 "charts": [
  CHART('Enquiries per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.enquiries', date='funnel.month', label='Enquiries')]),
  CHART('Enquiries by service', 'bar', 'demand.service', [AGG('sum', 'demand', 'demand.enquiries', label='Enquiries')]),
  CHART('Enquiries by client type', 'bar', 'enquiries.client_type', [AGG('count', 'enquiries', label='Enquiries')]),
  CHART('Enquiries by contact method', 'bar', 'enquiries.contact_method', [AGG('count', 'enquiries', label='Enquiries')]),
  CHART('Enquiries by status', 'bar', 'enquiries.status', [AGG('count', 'enquiries', label='Enquiries')]),
  CHART('Enquiries by priority', 'bar', 'enquiries.priority', [AGG('count', 'enquiries', label='Enquiries')]),
  CHART('Lost enquiries by cause', 'bar', 'lost.cause', [AGG('count', 'lost', label='Lost enquiries')]),
  CHART('Bookings per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.booked', date='funnel.month', label='Booked')]),
  CHART('Days to first appointment per month', 'line', 'month', [AGG('avg', 'enquiries', 'enquiries.days_to_first', date='enquiries.date', label='Days to first appointment')]),
  CHART('Days to screening per month', 'line', 'month', [AGG('avg', 'enquiries', 'enquiries.days_to_screening', date='enquiries.date', label='Days to screening')]),
  CHART('Waitlist by service', 'bar', 'waiting.service', [AGG('count', 'waiting', label='People')]),
  CHART('Waitlist by priority', 'bar', 'waiting.priority', [AGG('count', 'waiting', label='People')]),
  CHART('Waitlist by status', 'bar', 'waiting.status', [AGG('count', 'waiting', label='People')]),
  CHART('Days waiting by service', 'bar', 'waiting.service', [AGG('avg', 'waiting', 'waiting.days_waiting', label='Days waiting')]),
  CHART('Offers per month', 'column', 'month', [AGG('count', 'offers', date='offers.offered_on', label='Offers')]),
  CHART('Intake sessions per month', 'column', 'month', [AGG('count', 'intake', date='intake.date', label='Intake sessions')]),
  CHART('Intake sessions by status', 'bar', 'intake.status', [AGG('count', 'intake', label='Intake sessions')]),
  CHART('Intake sessions by clinician', 'bar', 'intake.clinician', [AGG('count', 'intake', label='Intake sessions')]),
  CHART('First sessions by format', 'bar', 'clients.format', [AGG('count', 'clients', label='New clients')]),
  CHART('Deposits by status', 'bar', 'deposits.status', [AGG('count', 'deposits', label='Deposits')]),
  CHART('Deposits taken per month', 'column', 'month', [AGG('sum', 'deposits', 'deposits.amount', date='deposits.date', label='Deposit amount')]),
  CHART('Signposted enquiries per month', 'column', 'month', [AGG('count', 'signpost', date='signpost.date', label='Signposted')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Enquiry log with reply speed and first appointment", "why": "every enquiry shows hours to first reply, days to screening and days to the first session against your target", "where": "Enquiry Log"},
 {"name": "Waitlist with an act-first rank", "why": "priority, days waiting and the target for each person rank who to offer a place first", "where": "Waitlist"},
 {"name": "Clinician match finder with free slots", "why": "service, client type and weekday name the first-choice clinician, their free slots and the next free slot", "where": "Clinician Match Finder"},
 {"name": "Waitlist time estimate with scenarios", "why": "your place, clients finishing and new slots give the expected weeks to an offer in a base, best or worst case", "where": "Waitlist Time Estimate"},
 {"name": "Intake conversion funnel", "why": "enquiry to screened to offered to booked to started, with the weakest step named", "where": "Intake Conversion Funnel"},
 {"name": "Waitlist clear-down plan", "why": "weeks until the list is back to target and the extra intake slots needed to clear it in the weeks you choose", "where": "Waitlist Clear-down Plan"},
 {"name": "Call-back schedule", "why": "each call-back date and the close date from the working-day gap, with today's action", "where": "Call-back Schedule"},
 {"name": "Offer tracker", "why": "every offer of a regular time with the answer, days to answer and the reply-by date", "where": "Offers Made"},
 {"name": "Intake no-show cost and deposit solver", "why": "what no-shows cost a month and the deposit that covers the share you want", "where": "Intake No-show Cost"},
 {"name": "Lost enquiries by cause", "why": "no reply, fee too high, no suitable time or clinician and waited too long show marketing against capacity", "where": "Lost Enquiries"},
 {"name": "Signposting log", "why": "who was sent where, why, and whether it happened within 7 days", "where": "Signposting Log"},
 {"name": "Enquiry forecast from your own history", "why": "the last 3 months and their trend give the next 3 months, split by service", "where": "Enquiry Forecast"}]
competitors = [
 {"what": "free appointment templates", "lacks": "list bookings but have no enquiry log, reply speed, waitlist priority or time to first appointment"},
 {"what": "subscription practice-management software", "lacks": "charge per clinician and keep your data in their system, with no editable waitlist targets or clear-down planner"},
 {"what": "single-sheet session logs", "lacks": "record sessions only, so enquiries, screening calls, offers and lost enquiries are never counted"},
 {"what": "generic contact spreadsheets", "lacks": "hold names and phones but cannot rank the waitlist, match clients to clinicians or forecast enquiries"},
 {"what": "online directory enquiry inboxes", "lacks": "show leads but not how long each waited, why it was lost or what the deposit and no-show cost you"}]
guide = [
 'Open Start and type your practice name and your targets in the yellow cells: days to first appointment (14 is the default), hours for a first reply, call-back attempts, intake limit a week, deposit and wanted show rate.',
 'Check Team, Services, Clinician Match Rules and Priority Targets. An employed clinician is paid a salary, a contract (self-employed) clinician a share of each session, an associate (works under supervision) per session.',
 'Log every enquiry on Enquiry Log with its hours to first reply. Days to screening, days to first appointment and the target check fill in. The first assessment session is called the intake.',
 'Record screening calls, call-backs and each lost enquiry. Lost Enquiries shows the cause: no reply, fee too high, no suitable time, no suitable clinician or waited too long.',
 'Keep the Waitlist up to date. The act-first rank shows who to offer a place first; record offers on Offers Made and check-ins on Waitlist Check-ins.',
 'Use Free Slots Next 4 Weeks and Intake Capacity by Week to see where intakes still fit. Match the client with Clinician Match Finder.',
 'New Clients, Deposits and Intake Paperwork follow each person to the first session. A sliding scale is a lower fee agreed from the client\'s means. A late cancel is a cancellation with less than 24 hours\' notice.',
 'A third-party payer is an organisation that pays part of a client\'s fee; in your area it may be an insurer, an employer scheme or a public body. Check your own local rules.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Why a workbook: one flat price, no per-clinician fee, and your data stays with you in your own file. The workbook holds status only, never note content.',
 'Read the Intake KPI Dashboard and Charts every week: reply speed, days to first appointment, waitlist, offers, show rate and lost enquiries.']
listing = {"title": "Therapy Practice Intake Excel Template: Enquiry Log, Waitlist, Screening Calls, Clinician Match, Deposits, KPI Dashboard",
 "headline": "Win more enquiries and keep your waitlist short in one Excel file",
 "tags": ["therapy practice", "intake tracker", "waitlist template", "counselling practice", "practice management", "excel template", "client intake", "enquiry log", "private practice", "clinic scheduling", "no show tracker", "group practice", "screening calls"],
 "description": ("Run everything between the first call and the first session in one Excel workbook. Built for a small group practice of talking therapists and counsellors: an owner-clinician, employed clinicians, contract (self-employed) clinicians, an associate who works under supervision and a front-desk coordinator.\n\n"
  "The Enquiry Log records every enquiry with its source, priority, hours to first reply, screening call and first session, and works out days to screening and days to the first appointment against your editable target (14 days by default). "
  "The Waitlist gives each person a target by priority and client type, the days waiting, their place in line and an act-first rank, so you know who to offer a place first. Offers Made, Waitlist Check-ins, Call-back Log, Screening Calls, Lost Enquiries (by cause), Signposting Log, Intake Sessions, New Clients, Deposits and Intake Paperwork follow each person to the first session. "
  "Free slots, weekly intake capacity and clinician match rules show where a new client can be seen.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: time to first appointment, waitlist time estimate, clinician match finder, intake conversion funnel, urgent slot reserve, waitlist clear-down plan, deposit level solver, no-show cost, call-back schedule, enquiry forecast, fee quote and more. "
  f"Print {len(forms)} sheets and {len(documents)} letters and reports, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
  "This is part one of the Therapy Private Practice suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-clinician fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. The workbook holds status only, never session notes or diagnoses, and it does not promise results."),
 "features": ["Enquiry log with reply speed and days to first appointment", "Waitlist with priority targets and act-first rank", "Clinician match finder with free slots", "Lost enquiries by cause", "Offers, check-ins and call-back schedule",
              "Deposits, no-show cost and deposit solver", "Intake paperwork tracker", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
              f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
s = _lib.spec(id=f'{SUITE}-p1', slug='therapy-practice-intake', profession='Therapy Private Practice', name='Intake, Screening and Waitlist',
         tagline='Win more enquiries and keep your waitlist short', price_usd=29, colors={"primary": "#2F5D62", "accent": "#A7C4BC"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Intake, screening and waitlist"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'th1.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
