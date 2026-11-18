"""Home care agency suite - part 1: Enquiries, Quotes and Agreements."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from hc1_lists import *
from hc1_tables import settings, tables, CA, STAFF_PH, STAFF_NM, LKT, LKN
from hc1_tools import tools

SUITE = 'fx-20261115-home-care-agency'
NOTE = "Sample wording: adapt it to your own agency and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
TB = {t['key']: t for t in tables}

settings.append(S('rate_rise_pct', 'Planned rate rise at the next change (example)', 'pct', 0.04))
assert len(settings) <= 20

# ---------------- extra calculated columns that documents and messages read
def addcol(tk, col):
    if not any(c['key'] == col['key'] for c in TB[tk]['columns']): TB[tk]['columns'].append(col)
SVC_AG = LKT('clients.service', 'clients.client_id', 'client_id')
addcol('agreements', CA('ag_service', 'Service', 'text', SVC_AG, 18))
def AGR(b): return 'IFERROR({col:bill_rate}*SUMIFS({range:rate_card.bill_rate},{range:rate_card.service},{col:ag_service},{range:rate_card.band},%s)/SUMIFS({range:rate_card.bill_rate},{range:rate_card.service},{col:ag_service},{range:rate_card.band},%s),"")' % (tok('band', b), tok('band', 'Weekday'))
for b in ('Evening', 'Weekend', 'Night', 'Holiday'): addcol('agreements', CA('r_' + b.lower(), b + ' rate', 'money', AGR(b), 10))
addcol('agreements', CA('min_visit_charge', 'Charge for a minimum visit', 'money', '{col:min_visit_hours}*{col:bill_rate}', 11))
addcol('clients', CA('new_rate', 'Rate after the planned rise', 'money', 'ROUND({col:bill_rate}*(1+{set:rate_rise_pct}),2)', 10))
addcol('clients', CA('card_gap_week', 'Weekly change at the card rate', 'money', 'IF({col:card_rate}=0,"",ROUND(({col:card_rate}-{col:bill_rate})*{col:weekly_hours},0))', 12))
addcol('clients', CA('deposit_weeks', 'Deposit in weeks of hours', 'num', 'IF({col:weekly_value}=0,"",ROUND({col:deposit}/{col:weekly_value},1))', 10))
addcol('clients', CA('free_in_area', 'Caregivers with free hours in the area', 'int', 'COUNTIFS({range:capacity.area},{col:area},{range:capacity.cap_flag},%s)' % ck('Free hours'), 11))

COLS = {
 'company': lambda: CA('company', 'Agency', 'text', '{set:company}&""', 24),
 'reply_target': lambda: CA('reply_target', 'Reply target hours', 'int', '{set:reply_hours_target}', 9),
 'scheduler_name': lambda: STAFF_NM(2, 'scheduler_name', 'Scheduler'), 'scheduler_phone': lambda: STAFF_PH(2, 'scheduler_phone'),
 'owner_name': lambda: STAFF_NM(1, 'owner_name', 'Owner'), 'owner_phone': lambda: STAFF_PH(1, 'owner_phone'),
 'manager_name': lambda: STAFF_NM(3, 'manager_name', 'Office manager'), 'manager_phone': lambda: STAFF_PH(3, 'manager_phone'),
 'supervisor_name': lambda: STAFF_NM(5, 'supervisor_name', 'Field supervisor'), 'supervisor_phone': lambda: STAFF_PH(5, 'supervisor_phone'),
}

# ---------------- forms
def cnt(tb, col, pick): return 'COUNTIFS({range:%s.%s},INDEX({range:%s.%s},MATCH({pick},{range:%s},0)))' % (tb, col, tb, col, pick)
forms = [
 FORM('enquiry_sheet', 'Enquiry Sheet', 'Enquiry with reply speed and start of care', 'enquiries.enquiry_id', F(
  ('Received on', 'enquiries.received_on'), ('Name', 'enquiries.name'), ('Phone', 'enquiries.phone'), ('Source', 'enquiries.source'), ('Referral partner', 'enquiries.referrer'), ('Area', 'enquiries.area'), ('Service', 'enquiries.service'),
  ('Hours a week', 'enquiries.hours_week'), ('Handled by', 'enquiries.handled_by'), ('Hours to first reply', 'enquiries.first_reply_hours'), ('Reply speed check', 'enquiries.reply_flag'), ('Status', 'enquiries.status'),
  ('Assessor', 'enquiries.assessor'), ('Assessment on', 'enquiries.assessment_on'), ('Quote a week', 'enquiries.quote_weekly'), ('Quote valid until', 'enquiries.valid_until'), ('Agreement on', 'enquiries.agreement_on'),
  ('First visit on', 'enquiries.first_visit_on'), ('Client ID', 'enquiries.client_id'), ('Days to start of care', 'enquiries.days_to_start'))),
 FORM('reply_sheet', 'Reply Log Sheet', 'Reply log for one enquiry contact', 'calls.call_id', F(
  ('Date', 'calls.date'), ('Enquiry ID', 'calls.enquiry_id'), ('Name', 'calls.name'), ('Phone', 'calls.phone'), ('Kind', 'calls.kind'), ('Outcome', 'calls.outcome'), ('Minutes', 'calls.minutes'),
  ('Hours after the enquiry', 'calls.hours_after'), ('Days since the enquiry', 'calls.days_since')) + [
  FF('Contacts logged for this enquiry', cnt('calls', 'enquiry_id', 'calls.call_id'), 'int'),
  FF('Hours to the first reply on the enquiry', 'IFERROR(INDEX({range:enquiries.first_reply_hours},MATCH(INDEX({range:calls.enquiry_id},MATCH({pick},{range:calls.call_id},0)),{range:enquiries.enquiry_id},0)),0)', 'int'),
  FF('Reply target, hours', '{set:reply_hours_target}', 'int')]),
 FORM('assessment_sheet', 'Assessment Sheet', 'Assessment visit: service needs and hours only', 'assessments.assessment_id', F(
  ('Enquiry ID', 'assessments.enquiry_id'), ('Name', 'assessments.name'), ('Phone', 'assessments.phone'), ('Assessment on', 'assessments.assessment_on'), ('Assessor', 'assessments.assessor'), ('Service', 'assessments.service'),
  ('Hours a week', 'assessments.hours_week'), ('Days a week', 'assessments.days_week'), ('Average visit hours', 'assessments.visit_hours'), ('Preferred start time', 'assessments.start_time'),
  ('Language wanted', 'assessments.language'), ('Area', 'assessments.area'), ('Travel minutes from the office zone', 'assessments.travel_min'), ('Outcome', 'assessments.outcome')) + [
  FF('Assessor phone', 'IFERROR(INDEX({range:team.phone},MATCH(INDEX({range:assessments.assessor},MATCH({pick},{range:assessments.assessment_id},0)),{range:team.name},0))&"","")', 'text')]),
 FORM('quote_sheet', 'Quote Sheet', 'Quote with weekly cost and deposit', 'quotes.quote_id', F(
  ('Enquiry ID', 'quotes.enquiry_id'), ('Name', 'quotes.name'), ('Phone', 'quotes.phone'), ('Sent on', 'quotes.sent_on'), ('Service', 'quotes.service'), ('Hours a week', 'quotes.hours_week'), ('Bill rate per hour', 'quotes.bill_rate'),
  ('Weekly cost', 'quotes.weekly_cost'), ('Monthly estimate', 'quotes.monthly_estimate'), ('Deposit', 'quotes.deposit'), ('Valid until', 'quotes.valid_until'), ('Validity check', 'quotes.valid_flag'),
  ('Estimated margin', 'quotes.est_margin_pct'), ('Margin check', 'quotes.margin_flag'), ('Status', 'quotes.status'))),
 FORM('agreement_sheet', 'Service Agreement Sheet', 'Service agreement terms', 'agreements.agreement_id', F(
  ('Client', 'agreements.client'), ('Client ID', 'agreements.client_id'), ('Kind', 'agreements.kind'), ('Sent on', 'agreements.sent_on'), ('Weekly hours', 'agreements.weekly_hours'), ('Bill rate per hour', 'agreements.bill_rate'),
  ('Minimum visit hours', 'agreements.min_visit_hours'), ('Charge for a minimum visit', 'agreements.min_visit_charge'), ('Notice days', 'agreements.notice_days'), ('Deposit', 'agreements.deposit'), ('Weekly value', 'agreements.weekly_value')) + [
  FF('Monthly value (weekly x 52 / 12)', 'INDEX({range:agreements.weekly_value},MATCH({pick},{range:agreements.agreement_id},0))*52/12', 'money')]),
 FORM('signed_sheet', 'Agreement Signed Sheet', 'Agreement signed: timing and the next steps', 'agreements.agreement_id', F(
  ('Client', 'agreements.client'), ('Phone', 'agreements.phone'), ('Sent on', 'agreements.sent_on'), ('Signed on', 'agreements.signed_on'), ('Days to sign', 'agreements.days_to_sign'), ('Signature check', 'agreements.sign_flag'),
  ('Status', 'agreements.status'), ('Deposit to receive', 'agreements.deposit'), ('Scheduler phone', 'agreements.scheduler_phone'), ('Office manager phone', 'agreements.manager_phone')) + [
  FF('Days the target allows', '{set:sign_days_target}', 'int'), FF('Weekly hours to put on the schedule', 'INDEX({range:agreements.weekly_hours},MATCH({pick},{range:agreements.agreement_id},0))', 'num')]),
 FORM('rate_notice_sheet', 'Rate Notice Sheet', 'Rate notice for one client', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Phone', 'clients.phone'), ('Service', 'clients.service'), ('Payer', 'clients.payer'), ('Weekly hours', 'clients.weekly_hours'), ('Current bill rate per hour', 'clients.bill_rate'),
  ('Rate card rate for the payer', 'clients.card_rate'), ('Gap to the rate card', 'clients.rate_gap'), ('Rate check', 'clients.rate_flag'), ('Rate after the planned rise', 'clients.new_rate'), ('Next rate change', 'clients.rate_change_on'),
  ('Weekly change at the card rate', 'clients.card_gap_week')) + [FF('Last day to send the notice', '{set:rate_change_date}-{set:rate_notice_days}', 'date'),
  FF('Weekly value after the planned rise', 'INDEX({range:clients.weekly_hours},MATCH({pick},{range:clients.client_id},0))*INDEX({range:clients.new_rate},MATCH({pick},{range:clients.client_id},0))', 'money')]),
 FORM('deposit_sheet', 'Deposit Receipt Sheet', 'Deposit received from a client', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Phone', 'clients.phone'), ('Payer', 'clients.payer'), ('Start date', 'clients.start_date'), ('Deposit', 'clients.deposit'), ('Prepaid balance', 'clients.prepay'), ('Billing cycle', 'clients.billing_cycle'),
  ('Weekly value', 'clients.weekly_value'), ('Deposit in weeks of hours', 'clients.deposit_weeks'), ('Office manager phone', 'clients.manager_phone'))),
 FORM('start_sheet', 'Start of Care Sheet', 'Start of care: the first visit and billing set-up', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Phone', 'clients.phone'), ('Area', 'clients.area'), ('Service', 'clients.service'), ('Weekly hours', 'clients.weekly_hours'), ('Bill rate per hour', 'clients.bill_rate'), ('Minimum visit hours', 'clients.min_visit_hours'),
  ('Billing cycle', 'clients.billing_cycle'), ('Introduction visit', 'clients.intro_on'), ('First visit', 'clients.start_date'), ('Weekly value', 'clients.weekly_value'), ('Field supervisor', 'clients.supervisor_name'),
  ('Field supervisor phone', 'clients.supervisor_phone'), ('Office manager phone', 'clients.manager_phone'))),
 FORM('lost_sheet', 'Lost Enquiry Sheet', 'Lost enquiry with the reason and the quote', 'lost.enquiry_id', F(
  ('Lost on', 'lost.date'), ('Name', 'lost.name'), ('Phone', 'lost.phone'), ('Service', 'lost.service'), ('Area', 'lost.area'), ('Source', 'lost.source'), ('Reason', 'lost.reason'), ('Quoted weekly cost', 'lost.quote_weekly'),
  ('Last contact', 'lost.last_contact'), ('Days open', 'lost.days_open')) + [FF('Enquiries lost for the same reason', cnt('lost', 'reason', 'lost.enquiry_id'), 'int'), FF('Enquiries lost from the same source', cnt('lost', 'source', 'lost.enquiry_id'), 'int')]),
 FORM('partner_sheet', 'Referral Partner Sheet', 'Referral partner and the enquiries they sent', 'enquiries.enquiry_id', F(
  ('Referral partner', 'enquiries.referrer'), ('Partner phone', 'enquiries.referrer_phone'), ('Source', 'enquiries.source'), ('Person referred', 'enquiries.name'), ('Received on', 'enquiries.received_on'), ('Service', 'enquiries.service'),
  ('Hours a week', 'enquiries.hours_week'), ('Status', 'enquiries.status'), ('First visit on', 'enquiries.first_visit_on')) + [
  FF('Enquiries from this partner', cnt('enquiries', 'referrer', 'enquiries.enquiry_id'), 'int'),
  FF('Clients started from this partner', 'COUNTIFS({range:enquiries.referrer},INDEX({range:enquiries.referrer},MATCH({pick},{range:enquiries.enquiry_id},0)),{range:enquiries.status},%s)' % tok('enqst', 'Started'), 'int')]),
 FORM('intro_sheet', 'Client Introduction Sheet', 'Client introduction visit', 'clients.client_id', F(
  ('Client', 'clients.client'), ('Phone', 'clients.phone'), ('Area', 'clients.area'), ('Language', 'clients.language'), ('Introduction visit', 'clients.intro_on'), ('First visit', 'clients.start_date'),
  ('Preferred caregiver', 'clients.preferred'), ('Preferred caregiver phone', 'clients.preferred_phone'), ('Second caregiver', 'clients.preferred_2'), ('Weekly hours', 'clients.weekly_hours'), ('Service', 'clients.service'),
  ('Caregivers with free hours in the area', 'clients.free_in_area'), ('Field supervisor', 'clients.supervisor_name'))),
]
assert len(forms) == 12

# ---------------- documents
def D_(k, sheet, title, pick, paras, sign): return DOC(k, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('agreement_doc', 'Service Agreement', 'Service agreement', 'agreements.agreement_id', [
  'Service agreement of {set:company}, dated {today}. Agreement {col:agreements.agreement_id} ({col:agreements.kind}). Client: {col:agreements.client}.',
  'Service: {col:agreements.ag_service}. Agreed hours: {col:agreements.weekly_hours} a week. Minimum visit: {col:agreements.min_visit_hours} hours.',
  'Rates per hour, before any tax: weekday {col:agreements.bill_rate}, evening {col:agreements.r_evening}, weekend {col:agreements.r_weekend}, night {col:agreements.r_night}, holiday {col:agreements.r_holiday}.',
  'Invoices are payable within 14 days. A deposit of {col:agreements.deposit} is held until the agreement ends.',
  'To cancel a visit please give at least {col:agreements.notice_days} days of notice. A visit cancelled later may be charged up to the minimum visit of {col:agreements.min_visit_hours} hours, {col:agreements.min_visit_charge}.',
  'Rates may change after {set:rate_notice_days} days of written notice. Check your own local rules for any terms you must add.'], ['Client', 'Agency owner']),
 D_('quote_doc', 'Quote Letter', 'Quote letter', 'quotes.quote_id', [
  'Quote of {set:company}, dated {today}. Dear {col:quotes.name},', 'Thank you for speaking with us. For {col:quotes.service} for {col:quotes.hours_week} hours a week at {col:quotes.bill_rate} per hour (before any tax) the cost is {col:quotes.weekly_cost} a week, about {col:quotes.monthly_estimate} a month.',
  'A deposit of {col:quotes.deposit} is taken before the first visit for private pay clients (self-funded). This quote is valid until {col:quotes.valid_until}. Quote reference {col:quotes.quote_id}.'], ['Agency owner']),
 D_('pricelist_doc', 'Rate Card Price List', 'Rate card price list for one service', 'rate_card.rate_id', [
  'Price list of {set:company}, dated {today}. Service: {col:rate_card.service}.', 'Rates per hour, before any tax: weekday {col:rate_card.r_weekday}, evening {col:rate_card.r_evening}, weekend {col:rate_card.r_weekend}, night {col:rate_card.r_night}, holiday {col:rate_card.r_holiday}.',
  'The holiday rate applies on a holiday (a bank holiday or another public holiday). Visits have a minimum length; ask the scheduler for the minimum of each service. Rates may change after {set:rate_notice_days} days of notice.'], ['Agency owner']),
 D_('assessment_doc', 'Assessment Summary', 'Assessment summary: service needs and hours only', 'assessments.assessment_id', [
  'Assessment summary of {set:company}, dated {today}. Assessment {col:assessments.assessment_id} on {col:assessments.assessment_on} by {col:assessments.assessor}.', 'Person: {col:assessments.name}, phone {col:assessments.phone}. Area: {col:assessments.area}.',
  'Service wanted: {col:assessments.service}. Hours: {col:assessments.hours_week} a week over {col:assessments.days_week} days, about {col:assessments.visit_hours} hours a visit, from {col:assessments.start_time}. Language wanted: {col:assessments.language}.',
  'Outcome: {col:assessments.outcome}. This summary holds service needs and hours only.'], ['Assessor', 'Client']),
 D_('welcome_doc', 'Welcome Letter', 'Welcome letter for a new client', 'clients.client_id', [
  'Welcome letter of {set:company}, dated {today}. Dear {col:clients.client},', 'Thank you for choosing us. Your first visit is on {col:clients.start_date}, with {col:clients.preferred}; your second caregiver is {col:clients.preferred_2}. An introduction visit comes first on {col:clients.intro_on}.',
  'Our office is open during office hours. To change a visit, call {col:clients.scheduler_name} on {col:clients.scheduler_phone}. Your field supervisor is {col:clients.supervisor_name}.', 'Your agreement is for {col:clients.weekly_hours} hours a week of {col:clients.service}.'], ['Agency owner']),
 D_('deposit_doc', 'Deposit Receipt', 'Deposit receipt', 'clients.client_id', [
  'Deposit receipt of {set:company}, dated {today}. Client {col:clients.client_id}: {col:clients.client}.', 'We received a deposit of {col:clients.deposit}, about {col:clients.deposit_weeks} weeks of your hours, before your first visit on {col:clients.start_date}.',
  'The deposit is held until your agreement ends and is returned or applied to the last invoice. Agree the details with the office manager, {col:clients.manager_name}.'], ['Office manager']),
 D_('ratenotice_doc', 'Rate Change Notice', 'Rate change notice', 'clients.client_id', [
  'Rate change notice of {set:company}, dated {today}. Dear {col:clients.client},', 'Your rate for {col:clients.service} is now {col:clients.bill_rate} per hour. From {col:clients.rate_change_on} the rate will be {col:clients.new_rate} per hour, before any tax.',
  'We give {set:rate_notice_days} days of written notice. Your weekly hours stay at {col:clients.weekly_hours}. Please contact {col:clients.scheduler_name} with any question.'], ['Agency owner']),
 D_('terms_doc', 'Cancellation Terms Sheet', 'Cancellation terms for one agreement', 'agreements.agreement_id', [
  'Cancellation and notice terms of {set:company}, dated {today}. Client: {col:agreements.client}. Agreement {col:agreements.agreement_id}.',
  'Please give at least {col:agreements.notice_days} days of notice to cancel or move a visit. With less notice we may charge up to the minimum visit of {col:agreements.min_visit_hours} hours, {col:agreements.min_visit_charge}.',
  'A caregiver who cannot come will be replaced by another caregiver where we can; we will tell you as soon as we know. Check your own local rules for what you may charge.'], ['Client', 'Agency owner']),
 D_('startcare_doc', 'Start of Care Confirmation', 'Start of care confirmation', 'clients.client_id', [
  'Start of care confirmation of {set:company}, dated {today}. Dear {col:clients.client},', 'Your first visit is on {col:clients.start_date}. Your caregiver is {col:clients.preferred}. The visit is in the {col:clients.area} area for {col:clients.service}.',
  'Your introduction visit is on {col:clients.intro_on}. Your field supervisor is {col:clients.supervisor_name}, phone {col:clients.supervisor_phone}.'], ['Agency owner']),
 D_('reply_doc', 'Enquiry Reply Letter', 'Enquiry reply letter', 'enquiries.enquiry_id', [
  'Reply of {set:company}, dated {today}. Dear {col:enquiries.name},', 'Thank you for your enquiry of {col:enquiries.received_on} about {col:enquiries.service} for {col:enquiries.hours_week} hours a week in {col:enquiries.area}.',
  'We aim to reply within {set:reply_hours_target} hours. Your assessment visit is on {col:enquiries.assessment_on} with {col:enquiries.assessor}. If you have a question please call {col:enquiries.scheduler_name} on {col:enquiries.scheduler_phone}. Reference {col:enquiries.enquiry_id}.'], ['Scheduler']),
 D_('weekly_doc', 'Weekly Enquiry Report', 'Weekly enquiry report for one month', 'funnel.month', [
  'Weekly enquiry report of {set:company}, dated {today}. Month starting {col:funnel.month}.', 'Enquiries: {col:funnel.enquiries}, about {col:funnel.enq_per_week} a week. Assessments: {col:funnel.assessments}. Agreements: {col:funnel.agreements}. Started: {col:funnel.started}. Lost: {col:funnel.lost}.',
  'Enquiry-to-client conversion: {col:funnel.conversion}. Assessment rate: {col:funnel.assessment_rate}. Decide at the weekly meeting which open enquiries to chase first.'], ['Owner', 'Scheduler']),
 D_('funnel_doc', 'Funnel and Source Report', 'Funnel and source report for one source and month', 'sources.month', [
  'Source report of {set:company}, dated {today}. Month starting {col:sources.month}. Source: {col:sources.source}.', 'Enquiries: {col:sources.enquiries}. Clients started: {col:sources.started}. Weekly hours started: {col:sources.hours_started}. Cost: {col:sources.cost}.',
  'Cost per client started: {col:sources.cost_per_start}. Hours started per 100 of cost over 12 months: {col:sources.value_12m}. Grow the sources with the most hours per cost and fix or cut the rest.'], ['Owner']),
]
assert len(documents) == 12

# ---------------- checklists
def CS(k, title, table, start, steps): return _lib.CHK(k, title, table, start, steps)
checklists = [
 CS('c_enquiry', 'New Enquiry Steps', 'enquiries', 'enquiries.received_on', [('Reply to the enquiry within the reply target', 0), ('Log the source, area, service and hours wanted', 0), ('Send the thank-you message', 0), ('Book the assessment visit', 2), ('Tell the scheduler about the new enquiry', 0)]),
 CS('c_assess', 'Assessment Visit Steps', 'assessments', 'assessments.assessment_on', [('Confirm the date and time with the enquirer', -2), ('Prepare the rate card and the agreement', -1), ('Record services wanted and hours (service needs and hours only)', 0), ('Record access times, language and an emergency contact name; check your own local rules', 0), ('Explain rates, minimum visit and notice terms', 0), ('Send the quote within one day', 1)]),
 CS('c_quote', 'Quote and Agreement Steps', 'quotes', 'quotes.sent_on', [('Check the quote margin against the target', 0), ('Send the quote and the agreement', 0), ('Call to answer questions', 3), ('Remind about the valid-until date', 10), ('Close the quote as accepted, declined or expired', 15)]),
 CS('c_signed', 'Agreement Signed Steps', 'agreements', 'agreements.signed_on', [('File the signed copy', 0), ('Take the deposit', 0), ('Build the schedule with the scheduler', 1), ('Set up billing with the office manager', 1), ('Book the caregiver introduction', 2)]),
 CS('c_deposit', 'Taking a Deposit Steps', 'clients', 'clients.start_date', [('Explain the deposit and what it covers', -7), ('Take the payment', -5), ('Send the receipt', -5), ('Record the deposit with the client', -5), ('Check the balance on the first invoice', 14)]),
 CS('c_start', 'Start of Care Week Steps', 'clients', 'clients.start_date', [('Introduce the caregiver to the client', -2), ('Confirm the first visit', -1), ('Explain check-in and check-out times', 0), ('Call the client after the first visit', 1), ('Call the client after the first week', 7), ('Check the first invoice is right', 14)]),
 CS('c_ratecard', 'Yearly Rate Card Review Steps', 'rate_history', 'rate_history.effective_on', [('Review pay, payroll burden and travel costs', -90), ('Check the margin of every band', -75), ('Decide the new rates', -60), ('Send the rate notice to every client', -30), ('Update the website and listings', 0), ('Check the first invoices at the new rates', 14)]),
 CS('c_stale', 'Stale Enquiry Follow-up Steps', 'enquiries', 'enquiries.received_on', [('Call the enquirer again', 2), ('Send a text message', 3), ('Send an e-mail with the rates', 4), ('Make a last call', 7), ('Close the enquiry and record the reason', 10)]),
 CS('c_lostrev', 'Lost Enquiry Review Steps', 'lost', 'lost.date', [('Record the reason', 0), ('Compare the quote with the price asked', 1), ('Decide if a call back in two months is worth it', 7), ('Add to the monthly lost-enquiry review', 30)]),
 CS('c_ratenotice', 'Rate Notice to Clients Steps', 'rate_history', 'rate_history.effective_on', [('List the clients and their current rates', -45), ('Write the notice', -40), ('Send the notice', -30), ('Answer client questions', -20), ('Update the agreements', 0), ('Check the invoices show the new rates', 14)]),
 CS('c_funnelrev', 'Monthly Funnel Review Steps', 'funnel', 'funnel.month', [('Count enquiries, assessments, agreements and starts', 1), ('Find the weakest step', 2), ('Review the sources and their cost', 3), ('Review the lost enquiries', 4), ('Agree one change for next month', 5)]),
 CS('c_partner', 'Referral Partner Contact Steps', 'enquiries', 'enquiries.received_on', [('Thank the referral partner', 0), ('Tell the partner when care starts', 7), ('Send an update on how many people were helped', 30), ('Meet or call the partner', 90)]),
]
assert len(checklists) == 12

# ---------------- messages
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('e_thanks', 'Enquirer: thank you, we will call you', 'enquiries', 'enquiries.phone', 'Hello {name}, thank you for contacting {company} about {service}. We will call you within {reply_target} hours.'),
 M('e_tried', 'Enquirer: we tried to call you', 'enquiries', 'enquiries.phone', 'Hello {name}, we tried to call you today about your enquiry for {hours_week} hours a week. Please tell {company} a good time to call.'),
 M('e_assess', 'Enquirer: your assessment visit', 'enquiries', 'enquiries.phone', 'Hello {name}, your assessment visit with {assessor} is on {assessment_on}. Reply here if the date does not suit you. {company}'),
 M('e_quote', 'Enquirer: your quote is attached', 'enquiries', 'enquiries.phone', 'Hello {name}, your quote of {quote_weekly} a week is attached. Please ask us anything about it. {company}'),
 M('e_valid', 'Enquirer: the quote is valid until', 'enquiries', 'enquiries.phone', 'Hello {name}, a reminder that your quote is valid until {valid_until}. Tell us if you would like to go ahead. {company}'),
 M('e_notheard', 'Enquirer: are you still looking for care', 'enquiries', 'enquiries.phone', 'Hello {name}, we have not heard from you for {idle_days} days. Are you still looking for {service}? {company}'),
 M('e_nocover', 'Enquirer: we cannot cover your area', 'lost', 'lost.phone', 'Hello {name}, we are sorry: {company} cannot cover {service} in {area} at the hours you asked for right now. We will tell you if that changes.'),
 M('e_avail', 'Enquirer: a caregiver is available from', 'enquiries', 'enquiries.phone', 'Hello {name}, good news: we have a caregiver available from {first_visit_on}. Please call {company} to confirm.'),
 M('e_sign', 'Enquirer: agreement ready to sign', 'agreements', 'agreements.phone', 'Hello {client}, your service agreement for {weekly_hours} hours a week is ready to sign. {company}'),
 M('e_signremind', 'Enquirer: return the signed agreement', 'agreements', 'agreements.phone', 'Hello {client}, a reminder to return your signed agreement; it was sent {days_unsigned} days ago. {company}'),
 M('c_deposit', 'Client: your deposit is received', 'clients', 'clients.phone', 'Hello {client}, your deposit of {deposit} is received. Thank you. {company}'),
 M('c_welcome', 'Client: welcome, your first visit', 'clients', 'clients.phone', 'Hello {client}, welcome to {company}. Your first visit is on {start_date}.'),
 M('c_cg', 'Client: your first caregiver', 'clients', 'clients.phone', 'Hello {client}, your caregiver for the first visit is {preferred}. {company}'),
 M('c_week', 'Client: how did the first week go', 'clients', 'clients.phone', 'Hello {client}, how did your first week with {preferred} go? Tell {company} if anything should change.'),
 M('c_rate', 'Client: our rates change', 'clients', 'clients.phone', 'Hello {client}, our rates change from {rate_change_on}. Your new rate is {new_rate} per hour and the notice is attached. {company}'),
 M('c_renew', 'Client: your agreement renewal is due', 'clients', 'clients.phone', 'Hello {client}, your service agreement is due for renewal on {renewal_on}. Please call {company} to review it.'),
 M('c_holiday', 'Client: our holiday rates apply', 'clients', 'clients.phone', 'Hello {client}, our holiday rates apply on {next_holiday_on} ({next_holiday}). Tell {company} if you want to change that day.'),
 M('c_times', 'Client: your visit times from next week', 'clients', 'clients.phone', 'Hello {client}, your visit times from next week are on the schedule we are sending you: {weekly_hours} hours with {preferred}. {company}'),
 M('g_meet', 'Caregiver: please meet a new client', 'clients', 'clients.preferred_phone', 'Hello {preferred}, please meet our new client {client} in {area} on {start_date}. {company}'),
 M('g_take', 'Caregiver: can you take more hours', 'capacity', 'capacity.phone', 'Hello {caregiver}, can you take up to {free_hours} more hours a week in {area}? Please reply to {company}.'),
 M('g_intro', 'Caregiver: introduction visit booked', 'clients', 'clients.preferred_phone', 'Hello {preferred}, an introduction visit with {client} is booked for {intro_on}. {company}'),
 M('s_reply', 'Scheduler: new enquiry needs a reply', 'enquiries', 'enquiries.scheduler_phone', 'Hello {scheduler_name}, a new enquiry from {source} ({name}, {service}) needs a first reply within {reply_target} hours.'),
 M('s_assess', 'Scheduler: assessment booked', 'enquiries', 'enquiries.scheduler_phone', 'Hello {scheduler_name}, an assessment is booked for {name} on {assessment_on} with {assessor}.'),
 M('s_signed', 'Scheduler: agreement signed, schedule', 'agreements', 'agreements.scheduler_phone', 'Hello {scheduler_name}, {client} signed the agreement: please build the schedule for {weekly_hours} hours a week.'),
 M('s_stale', 'Scheduler: an enquiry is stale', 'enquiries', 'enquiries.scheduler_phone', 'Hello {scheduler_name}, the enquiry from {name} has had no contact for {idle_days} days. Please follow up today.'),
 M('f_assess', 'Field supervisor: do the assessment', 'enquiries', 'enquiries.assessor_phone', 'Hello {assessor}, please do the assessment for {name} on {assessment_on} in {area} ({service}, {hours_week} hours a week).'),
 M('f_start', 'Field supervisor: start-of-care visit', 'clients', 'clients.supervisor_phone', 'Hello {supervisor_name}, the start-of-care visit for {client} is on {start_date} in {area}.'),
 M('m_billing', 'Office manager: set up billing', 'clients', 'clients.manager_phone', 'Hello {manager_name}, please set up billing for {client}: {weekly_hours} hours a week at {bill_rate} per hour, billed {billing_cycle}.'),
 M('m_deposit', 'Office manager: deposit not received', 'agreements', 'agreements.manager_phone', 'Hello {manager_name}, the deposit of {deposit} for {client} is not received yet. Please check.'),
 M('o_quote', 'Owner: quote below target margin', 'quotes', 'quotes.owner_phone', 'Hello {owner_name}, the quote for {name} ({hours_week} hours at {bill_rate} per hour) is below the target margin. Please review it.'),
 M('o_report', 'Owner: the funnel report is ready', 'funnel', 'funnel.owner_phone', 'Hello {owner_name}, the enquiry funnel report for {month} is ready: {enquiries} enquiries, {started} started, {lost} lost.'),
 M('o_source', 'Owner: a source brought no paying hours', 'sources', 'sources.owner_phone', 'Hello {owner_name}, the source {source} brought {hours_started} paying hours in {month} for a cost of {cost}. Please review it.'),
 M('k_rates', 'Marketing helper: update the rates', 'rate_card', 'rate_card.marketing_phone', 'Hello {marketing_name}, please update the online directory listing and the website with the new {service} rates (weekday {r_weekday}, holiday {r_holiday}).'),
 M('p_thanks', 'Referral partner: thank you', 'enquiries', 'enquiries.referrer_phone', 'Hello {referrer}, thank you for sending {name} to {company}. We will keep you updated.'),
]
assert len(messages) == 34, len(messages)

# tables that send messages and forms need the shared columns
for m in messages:
    tk = m['table']
    for ph in {p.strip('{}') for p in __import__('re').findall(r'\{[a-z_0-9]+\}', m['text'])}:
        if ph in COLS: addcol(tk, COLS[ph]())
for t in ('clients', 'agreements', 'enquiries'):
    for k in ('scheduler_name', 'scheduler_phone', 'manager_name', 'manager_phone', 'supervisor_name'):
        if t == 'clients' or k.startswith('scheduler') and t in ('agreements', 'enquiries') or (t == 'agreements' and k == 'manager_phone'): addcol(t, COLS[k]())
addcol('lost', COLS['company']())

# the first demo row of a table is the record a form or document shows: move a complete row to the front
def front(tk, pred):
    rows = TB[tk]['demo']
    for i, r in enumerate(rows):
        if pred(r): rows.insert(0, rows.pop(i)); return
    raise SystemExit('no front row for ' + tk)
import hc1_data as _D
_QS = {e['enquiry_id'] for e in _D.QS}
front('enquiries', lambda r: r.get('status') == key('enqst', 'Started') and r.get('referrer') and r['enquiry_id'] in _QS and r.get('assessment_on') and r.get('agreement_on') and r.get('first_visit_on'))
front('sources', lambda r: r['started'] > 0 and r['enquiries'] > 0 and r['month'] >= iso(month_start(3)))
front('funnel', lambda r: r['month'] == iso(month_start(1)))
front('quotes', lambda r: r.get('status') == key('qst', 'Accepted'))
front('agreements', lambda r: r.get('client_id') and r.get('signed_on') and r.get('status') == key('agrst', 'Signed'))
_BASE = {key('svc', x['service']): x['bill_rate'] for x in _D.services}
front('calls', lambda r: r.get('enquiry_id') in _QS and r.get('hours_after', 0) >= 30)
front('clients', lambda r: abs(r.get('bill_rate', 0) - _BASE.get(r.get('service'), 0)) > 0.3 and r.get('status') == key('clstatus', 'Active') and r.get('preferred') and r.get('deposit', 0) > 0 and r.get('payer') == key('payer', 'Private pay') and r.get('preferred') in {c['name'] for c in _D.CGR if c['status'] != 'Left'})

# ---------------- dashboard
MSTART = 'DATE(YEAR({today}),MONTH({today}),1)'
def DW(c, n): return '{range:%s},">="&({today}-%d),{range:%s},"<="&{today}' % (c, n, c)
def THISM(c): return '{range:%s},">="&%s,{range:%s},"<="&{today}' % (c, MSTART, c)
ST_ = lambda k: tok('enqst', k)
kpis = [
 KPI('Enquiries this month', 'COUNTIFS(%s)' % THISM('enquiries.received_on'), 'int'),
 KPI('Enquiries last 30 days', 'COUNTIFS(%s)' % DW('enquiries.received_on', 29), 'int'),
 KPI('Open enquiries', 'COUNTIFS({range:enquiries.status},"<>"&%s,{range:enquiries.status},"<>"&%s,{range:enquiries.enquiry_id},"<>")' % (ST_('Started'), ST_('Lost')), 'int'),
 KPI('Stale open enquiries', 'COUNTIFS({range:enquiries.stale_flag},%s)' % ck('Stale'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Hours to first reply, 90 days', 'IFERROR(AVERAGEIFS({range:enquiries.first_reply_hours},%s),0)' % DW('enquiries.received_on', 90), 'num', alert={"when": "> {set:reply_hours_target}", "style": "warn"}),
 KPI('Replies within target, last 90 days', 'IFERROR(COUNTIFS({range:enquiries.reply_flag},%s,%s)/COUNTIFS(%s),0)' % (ck('Replied in time'), DW('enquiries.received_on', 90), DW('enquiries.received_on', 90)), 'pct', alert={"when": "< {set:reply_share_target}", "style": "warn"}),
 KPI('Assessments booked next 7 days', 'COUNTIFS({range:enquiries.assessment_on},">="&{today},{range:enquiries.assessment_on},"<="&({today}+7))', 'int'),
 KPI('Assessments done this month', 'COUNTIFS(%s)' % THISM('assessments.assessment_on'), 'int'),
 KPI('Quotes sent last 30 days', 'COUNTIFS(%s)' % DW('quotes.sent_on', 29), 'int'),
 KPI('Quote acceptance, last 90 days', 'IFERROR(COUNTIFS({range:quotes.status},%s,%s)/COUNTIFS({range:quotes.status},"<>"&%s,%s),0)' % (tok('qst', 'Accepted'), DW('quotes.sent_on', 90), tok('qst', 'Open'), DW('quotes.sent_on', 90)), 'pct'),
 KPI('Agreements out unsigned', 'COUNTIFS({range:agreements.status},%s)' % tok('agrst', 'Sent'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Oldest unsigned agreement, days', 'MAX({range:agreements.days_unsigned})', 'int', alert={"when": "> {set:sign_days_target}", "style": "bad"}),
 KPI('Agreements signed this month', 'COUNTIFS(%s)' % THISM('agreements.signed_on'), 'int'),
 KPI('First visits next 14 days', 'COUNTIFS({range:enquiries.first_visit_on},">="&{today},{range:enquiries.first_visit_on},"<="&({today}+14))', 'int'),
 KPI('New clients started this month', 'COUNTIFS(%s)' % THISM('clients.start_date'), 'int'),
 KPI('New weekly hours started this month', 'SUMIFS({range:clients.weekly_hours},%s)' % THISM('clients.start_date'), 'num'),
 KPI('Enquiry-to-client rate, 90 days', 'IFERROR(COUNTIFS({range:enquiries.status},%s,%s)/COUNTIFS(%s),0)' % (ST_('Started'), DW('enquiries.received_on', 90), DW('enquiries.received_on', 90)), 'pct'),
 KPI('Days first call to start, 90 days', 'IFERROR(AVERAGEIFS({range:enquiries.days_to_start},%s),0)' % DW('enquiries.first_visit_on', 90), 'num', alert={"when": "> {set:start_days_target}", "style": "warn"}),
 KPI('Enquiries lost last 30 days', 'COUNTIFS(%s)' % DW('lost.date', 29), 'int'),
 KPI('Lost to price, last 90 days', 'COUNTIFS({range:lost.reason},%s,%s)' % (tok('loss', 'Price'), DW('lost.date', 90)), 'int'),
 KPI('Lost for no cover, last 90 days', 'COUNTIFS({range:lost.reason},%s,%s)' % (tok('loss', 'No cover available'), DW('lost.date', 90)), 'int'),
 KPI('No-reply enquiries, last 30 days', 'COUNTIFS({range:lost.reason},%s,%s)' % (tok('loss', 'No reply'), DW('lost.date', 29)), 'int'),
 KPI('Deposits received this month', 'SUMIFS({range:clients.deposit},%s)' % THISM('clients.start_date'), 'money'),
 KPI('Rate card bands below target', 'COUNTIFS({range:rate_card.margin_flag},%s)' % ck('Below target'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Clients on a locked rate', 'COUNTIFS({range:clients.rate_flag},%s)' % ck('Locked rate'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Average bill rate across active clients', 'IFERROR(AVERAGEIFS({range:clients.bill_rate},{range:clients.status},%s),0)' % tok('clstatus', 'Active'), 'money'),
 KPI('Weekly hours under contract', 'SUMIFS({range:clients.weekly_hours},{range:clients.status},%s)' % tok('clstatus', 'Active'), 'num'),
 KPI('Active clients', 'COUNTIFS({range:clients.status},%s)' % tok('clstatus', 'Active'), 'int'),
 KPI('Caregivers with free hours next week', 'COUNTIFS({range:capacity.cap_flag},%s)' % ck('Free hours'), 'int'),
 KPI('Weekly hours waiting for a caregiver', 'SUMIFS({range:enquiries.hours_week},{range:enquiries.status},%s)' % ST_('Agreement sent'), 'num'),
]
assert len(kpis) == 30
dashboard = {"title": "Enquiries KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Enquiries, assessments, agreements and starts", "date": "funnel.month", "series": [
   {"label": "Enquiries", "sum": "funnel.enquiries", "date": "funnel.month"}, {"label": "Assessments", "sum": "funnel.assessments", "date": "funnel.month"},
   {"label": "Agreements", "sum": "funnel.agreements", "date": "funnel.month"}, {"label": "Started", "sum": "funnel.started", "date": "funnel.month"}]},
 "breakdowns": [{"title": "Enquiries by source", "by": "enquiries.source", "agg": "count"}, {"title": "Lost enquiries by reason", "by": "lost.reason", "agg": "count"},
                {"title": "Clients by payer", "by": "clients.payer", "agg": "count"}, {"title": "Quotes by status", "by": "quotes.status", "agg": "count"}]}
insights = {"filters": [{"label": "Service", "list": "svc"}, {"label": "Area", "list": "area"}, {"label": "Source", "list": "enqsrc"}],
 "gauges": [
  {"title": "Enquiries replied to within the target", "num": AGG('count', 'enquiries', where=[('reply_flag', '=', ck('Replied in time'))]), "den": AGG('count', 'enquiries')},
  {"title": "Enquiries that became clients", "num": AGG('count', 'enquiries', where=[('status', '=', ST_('Started'))]), "den": AGG('count', 'enquiries')},
  {"title": "Quotes accepted", "num": AGG('count', 'quotes', where=[('status', '=', tok('qst', 'Accepted'))]), "den": AGG('count', 'quotes', where=[('status', '<>', tok('qst', 'Open'))])},
  {"title": "Agreements signed within 7 days", "num": AGG('count', 'agreements', where=[('sign_flag', '=', ck('Signed within 7 days'))]), "den": AGG('count', 'agreements', where=[('days_to_sign', '>=', 0)])},
  {"title": "Rate card bands at target margin", "num": AGG('count', 'rate_card', where=[('margin_flag', '=', ck('Meets target'))]), "den": AGG('count', 'rate_card')},
  {"title": "Start of care within the target days", "num": AGG('count', 'enquiries', where=[('days_to_start', '<=', '{set:start_days_target}'), ('days_to_start', '>=', 0)]), "den": AGG('count', 'enquiries', where=[('days_to_start', '>=', 0)])}],
 "charts": [
  CHART('Enquiries per month', 'column', 'month', [AGG('count', 'enquiries', date='enquiries.received_on', label='Enquiries')]),
  CHART('Enquiries by source', 'bar', 'enquiries.source', [AGG('count', 'enquiries', label='Enquiries')]),
  CHART('Enquiries by service', 'bar', 'enquiries.service', [AGG('count', 'enquiries', label='Enquiries')]),
  CHART('Enquiries by area', 'bar', 'enquiries.area', [AGG('count', 'enquiries', label='Enquiries')]),
  CHART('Enquiries by status', 'bar', 'enquiries.status', [AGG('count', 'enquiries', label='Enquiries')]),
  CHART('Lost enquiries by reason', 'bar', 'lost.reason', [AGG('count', 'lost', label='Lost enquiries')]),
  CHART('Lost enquiries per month', 'column', 'month', [AGG('count', 'lost', date='lost.date', label='Lost enquiries')]),
  CHART('Assessments per month', 'column', 'month', [AGG('count', 'assessments', date='assessments.assessment_on', label='Assessments')]),
  CHART('Agreements signed per month', 'column', 'month', [AGG('count', 'agreements', date='agreements.signed_on', label='Agreements signed')]),
  CHART('Agreements by status', 'bar', 'agreements.status', [AGG('count', 'agreements', label='Agreements')]),
  CHART('Agreements by kind', 'bar', 'agreements.kind', [AGG('count', 'agreements', label='Agreements')]),
  CHART('New clients per month', 'column', 'month', [AGG('sum', 'starts', 'starts.clients_started', date='starts.month', label='Clients started')]),
  CHART('Weekly hours started and lost per month', 'column', 'month', [AGG('sum', 'starts', 'starts.hours_added', date='starts.month', label='Hours started'), AGG('sum', 'starts', 'starts.hours_lost', date='starts.month', label='Hours lost')]),
  CHART('Active clients per month', 'column', 'month', [AGG('sum', 'starts', 'starts.active_clients', date='starts.month', label='Active clients')]),
  CHART('Average hours to first reply per month', 'column', 'month', [AGG('avg', 'enquiries', 'enquiries.first_reply_hours', date='enquiries.received_on', label='Hours to first reply')]),
  CHART('Average days from first call to start per month', 'column', 'month', [AGG('avg', 'enquiries', 'enquiries.days_to_start', date='enquiries.first_visit_on', label='Days to start')]),
  CHART('Enquiry-to-client conversion per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.conversion', date='funnel.month', label='Conversion')]),
  CHART('Quotes by status', 'bar', 'quotes.status', [AGG('count', 'quotes', label='Quotes')]),
  CHART('Rate card margin by time band', 'bar', 'rate_card.band', [AGG('avg', 'rate_card', 'rate_card.margin_pct', label='Margin share')]),
  CHART('Rate card margin by service', 'bar', 'rate_card.service', [AGG('avg', 'rate_card', 'rate_card.margin_pct', label='Margin share')]),
  CHART('Clients by payer', 'bar', 'clients.payer', [AGG('count', 'clients', label='Clients')]),
  CHART('Clients by billing cycle', 'bar', 'clients.billing_cycle', [AGG('count', 'clients', label='Clients')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Enquiry log with reply speed and stale alert", "why": "every enquiry shows hours to first reply, days without contact and days to start against your targets, so none is forgotten", "where": "Enquiry Log"},
 {"name": "Can I take this client?", "why": "hours, area, language and quoted rate give the caregivers who could cover without overtime, the margin and a verdict of Accept, Quote higher or Decline", "where": "Can I Take This Client"},
 {"name": "Minimum rate for the target margin", "why": "pay, band mix, paid travel and mileage give the lowest bill rate that reaches your margin, never a guess", "where": "Minimum Rate for Target"},
 {"name": "Rate card with the margin check", "why": "30 rates show margin per hour and flag every band below your target", "where": "Rate Card"},
 {"name": "Quote and agreement that print", "why": "the quote and the service agreement fill from one record, with rates by band, minimum visit and notice terms", "where": "Quotes"},
 {"name": "Funnel with loss reasons", "why": "enquiry to assessment to agreement to first visit by month, with the reason every enquiry was lost", "where": "Monthly Funnel"},
 {"name": "Source value ranking", "why": "cost per client started and hours per 100 of cost show which source to grow", "where": "Source Value Ranking"},
 {"name": "Time from first call to start", "why": "the slowest step between the call and the first visit, against your target days", "where": "Time from First Call to Start"},
 {"name": "Price test for a lost enquiry", "why": "the margin you give up to match a competitor rate, with a hold or match verdict", "where": "Price Test for a Lost Enquiry"},
 {"name": "One-person capacity check", "why": "a start-up owner who works visits sees income and free hours before saying yes", "where": "One-Person Capacity Check"},
 {"name": "Caregiver capacity and availability", "why": "free hours next week, skills, languages and area for every working caregiver", "where": "Caregiver Capacity"}]
competitors = [
 {"what": "free schedule template", "lacks": "lists visits but has no enquiry log, quote, rate card margin or agreement"},
 {"what": "subscription home care software with a per-client fee", "lacks": "charges more as you grow, keeps your data in its system and has no editable margin checker or price test"},
 {"what": "single-sheet time log", "lacks": "records hours only, with no reply speed, funnel, loss reasons or source value"},
 {"what": "generic invoice spreadsheet", "lacks": "prints an invoice but cannot quote by time band, check the margin or track an unsigned agreement"},
 {"what": "generic customer contact list", "lacks": "holds names and phones but does not rank sources, show stale enquiries or match a client to free caregiver hours"}]
guide = [
 'Open Start here and type your agency name and targets in the yellow cells: reply hours, stale days, days to start, target margin and payroll burden (payroll taxes, workers\' insurance and benefits on top of pay; confirm with your adviser).',
 'Check Rate Card, Services, Areas and Payers. A caregiver is a carer, care worker or support worker. The holiday rate applies on a holiday (a bank holiday or another public holiday); private pay means self-funded.',
 'Log every enquiry on Enquiry Log with its source, hours and hours to first reply. The quote, days to start, reply check and stale flag fill in. An open enquiry is a stale enquiry when it has had no contact for more days than your limit.',
 'Record each call on Enquiry Calls, each assessment on Assessments (service needs and hours only, never care notes), each quote on Quotes and each agreement on Service Agreements.',
 'Use Can I Take This Client? before you say yes: it checks caregiver free hours without overtime (hours above the weekly line) and the margin at your quoted rate.',
 'Use Minimum Rate for Target, Rate Card Margin Checker and Rate Card Builder to set rates; Quote Builder and Quote Sensitivity to price one client; Deposit and Prepayment to size a deposit.',
 'Review Monthly Funnel, Lost Enquiries and Source by Month every month; Source Value Ranking shows the source to grow. A third-party payer is an insurer, a public body or an employer scheme in your area.',
 'A one-person start-up agency can use Enquiries, Quotes, Agreements and the One-Person Capacity Check from day one; it needs no caregiver list.',
 'Replace the demo data: clear the sample rows, keep the headers, type your own rows and your own targets. The workbook has no macros and works in Excel and Google Sheets.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Why a workbook: one flat price, no per-client or per-caregiver fee, no price rise when hours grow, and your data stays with you. It does not track visits live, use GPS or check in automatically; it works from the times you type or paste.']
listing = {"title": "Home Care Agency Excel Template: Enquiry Log, Quotes, Service Agreements, Rate Card Margin, Funnel and Can I Take This Client Tool",
 "headline": "Win more clients and price every quote above your margin, in one Excel file",
 "tags": ["home care agency", "home care template", "enquiry tracker", "rate card", "service agreement", "quote template", "caregiver matching", "client intake", "agency management", "excel template", "lead funnel", "pricing calculator", "non medical care"],
 "description": ("Run everything between the first call and the first visit of a non-medical home care agency in one Excel workbook. Built for an owner-director with a scheduler, an office manager and field supervisors, and simple enough for a one-person start-up agency.\n\n"
  "The Enquiry Log records every enquiry with its source, service, hours wanted, hours to first reply, assessment, agreement and first visit, then works out days to start and flags a stale enquiry against targets you set. "
  "Assessments, Quotes, Service Agreements, Enquiry Calls, Lost Enquiries (by reason), Source by Month and the Monthly Funnel follow every person to the first visit. The Rate Card holds 30 rates by service and time band with the margin per hour, the Rate History records every rise, and Caregiver Capacity and Availability show free hours next week.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: Can I take this client?, minimum rate for the target margin, rate card margin checker, quote builder, deposit sizing, short-visit surcharge, reply speed, funnel conversion, source value ranking, time to start, price test, hours to fill forecast and a one-person capacity check. "
  f"Print {len(forms)} sheets and {len(documents)} documents including the service agreement, quote letter and price list, follow {len(checklists)} checklists and send {len(messages)} ready messages.\n\n"
  "This is part one of the Home Care Agency Business suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-client fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. The workbook holds service types, hours, dates and amounts only; it is not a care plan, tracks nothing live and promises no results."),
 "features": ["Enquiry log with reply speed and stale alert", "Can I take this client? verdict from free caregiver hours", "Rate card with margin per hour by service and time band", "Quotes with weekly cost, monthly estimate and deposit",
              "Service agreements that print as a contract", "Funnel with loss reasons and source value ranking", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
              f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready messages", "One-person start-up capacity check", "One flat price, your data stays with you"]}
assert len(listing['description']) >= 900 and len(listing['title']) <= 140 and len(listing['headline']) <= 80 and all(len(t) <= 20 for t in listing['tags']) and len(listing['tags']) == 13

s = _lib.spec(id=f'{SUITE}-p1', slug='home-care-enquiries', profession='Home Care Agency Business', name='Enquiries, Quotes and Agreements',
         tagline='Win more clients and price every quote above your margin', price_usd=29, colors={"primary": "#3A506B", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Enquiries, quotes, rate card and agreements"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hc1.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
