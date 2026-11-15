"""Therapy practice suite part 1: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th1_lists import *
import th1_data as D

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF_PH(sid, k='phone'): return CA(k, 'Phone to message', 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % int(sid[-2:]), 18)
YES = '{list:yesno.yes}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'
def ST(lst, lab): return tok(lst, lab)

settings = [
    S('company', 'Your practice name', 'text', COMPANY), S('target_wait_days', 'Target days from enquiry to first appointment', 'int', 14), S('screen_days', 'Days within which a screening call is wanted', 'int', 2),
    S('reply_hours', 'Hours that count as one working day for a first reply', 'int', 24), S('target_reply_rate', 'Wanted share of enquiries replied to in time', 'pct', 0.8),
    S('callback_attempts', 'Call-back attempts before an enquiry is closed', 'int', 3), S('callback_gap_days', 'Working days between call-back attempts', 'int', 2),
    S('offer_reply_days', 'Days a client has to answer an offer of a regular time', 'int', 3), S('checkin_weeks', 'Weeks between waitlist check-ins', 'int', 4),
    S('intake_limit_week', 'Most intake sessions one clinician takes in a week', 'int', 3), S('deposit', 'New self-pay client deposit', 'money', 50),
    S('late_fee_pct', 'Share of the fee charged for a late cancel or no-show', 'pct', 0.5), S('late_cancel_hours', 'Hours of notice for a cancellation (less is a late cancel)', 'int', 24),
    S('target_conv', 'Wanted share of enquiries that become bookings', 'pct', 0.5), S('target_show_rate', 'Wanted intake show rate', 'pct', 0.9),
    S('target_accept', 'Wanted share of offers accepted', 'pct', 0.8), S('forms_days', 'Days before the first session forms should be back', 'int', 2),
    S('room_cost_hour', 'Rent, cleaning and power per hour of room time', 'money', 12), S('admin_cost', 'Booking and billing cost per booked session', 'money', 6)]
assert 3 <= len(settings) <= 20

def T_(*a, **k): return T(*a, **k)
tables = []
tables.append(T('enquiries', 'Enquiry Log', 'Enquiry log with reply speed and first appointment',
    'One row per enquiry: contact details, source, priority, hours to first reply, screening and first session; days to screening, days to first appointment and the target check fill in by themselves.', [
    C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('name', 'Name', 'text', 24), C('contact', 'Contact person', 'text', 22), C('phone', 'Phone', 'text', 18),
    LST('client_type', 'Client type', 'ctype', 12), LST('service', 'Service', 'svc', 18), LST('source', 'Source', 'src', 16), C('referrer', 'Referrer', 'text', 22), C('referrer_phone', 'Referrer phone', 'text', 18),
    LST('contact_method', 'Contact method', 'cmethod', 13), LST('priority', 'Priority', 'prio', 9), C('reply_hours', 'Hours to first reply', 'num', 11), C('screening_date', 'Screening date', 'date', 12),
    REF('screened_by', 'Screened by', 'team.name', 20), LST('status', 'Status', 'enqst', 17), LST('reason', 'Reason', 'enqr', 18), LST('clinician', 'Clinician', 'clin', 16), C('first_session', 'First session', 'date', 12),
    CA('reply_flag', 'Reply speed check', 'text', 'IF({col:reply_hours}<={set:reply_hours},%s,%s)' % (ck('Replied in time'), ck('Replied late')), 15),
    CA('days_to_screening', 'Days to screening', 'int', 'IF({col:screening_date}="","",{col:screening_date}-{col:date})', 10),
    CA('days_to_first', 'Days to first appointment', 'int', 'IF({col:first_session}="","",{col:first_session}-{col:date})', 12),
    CA('wait_check', 'Target check', 'text', 'IF({col:first_session}<>"",IF({col:first_session}-{col:date}>{set:target_wait_days},%s,%s),IF(OR({col:status}=%s,{col:status}=%s,{col:status}=%s),IF({today}-{col:date}>{set:target_wait_days},%s,%s),%s))' % (
        ck('Over target'), ck('Within target'), ST('enqst', 'New'), ST('enqst', 'Screening booked'), ST('enqst', 'Waiting list'), ck('Over target'), ck('Within target'), ck('Closed')), 14),
    STAFF_PH('TH-01', 'owner_phone')], D.enquiries_d(), 1500,
    [A('wait_check', '= ' + ck('Over target'), 'bad'), A('reply_flag', '= ' + ck('Replied late'), 'warn'), A('status', '= ' + ST('enqst', 'New'), 'warn'), A('status', '= ' + ST('enqst', 'Booked'), 'good')]))
tables.append(T('waiting', 'Waitlist', 'Waitlist with priority, days waiting and an act-first rank',
    'One row per person on the waitlist: priority, offer and start dates; days waiting, the target, the place in line and the act-first rank fill in by themselves.', [
    C('wait_id', 'Wait ID', 'text', 9, required=True), C('added_on', 'Added on', 'date', 11), C('enquiry_id', 'Enquiry ID', 'text', 10), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18),
    LST('client_type', 'Client type', 'ctype', 12), LST('service', 'Service', 'svc', 18), LST('priority', 'Priority', 'prio', 9), C('offered_on', 'Offered on', 'date', 11), C('started_on', 'Started on', 'date', 11),
    C('withdrawn_on', 'Withdrawn on', 'date', 12), LST('clinician', 'Clinician', 'clin', 16), LST('status', 'Status', 'waitst', 11),
    CA('days_waiting', 'Days waiting', 'int', 'IF({col:status}=%s,{today}-{col:added_on},IF({col:status}=%s,IF({col:withdrawn_on}="",{today}-{col:added_on},{col:withdrawn_on}-{col:added_on}),IF({col:offered_on}="",{today}-{col:added_on},{col:offered_on}-{col:added_on})))' % (ST('waitst', 'Waiting'), ST('waitst', 'Withdrawn')), 9),
    CA('target_days', 'Target days to offer', 'int', 'SUMIFS({range:targets.target_days},{range:targets.client_type},{col:client_type},{range:targets.priority},{col:priority})', 10),
    CA('wait_check', 'Target check', 'text', 'IF({col:days_waiting}>{col:target_days},%s,%s)' % (ck('Over target'), ck('Within target')), 14),
    CA('days_over', 'Days over target', 'int', 'IF({col:status}=%s,{col:days_waiting}-{col:target_days},"")' % ST('waitst', 'Waiting'), 9),
    CA('act_rank', 'Act-first rank', 'int', 'IF({col:status}=%s,1+COUNTIFS({range:waiting.status},%s,{range:waiting.days_over},">"&{col:days_over}),"")' % (ST('waitst', 'Waiting'), ST('waitst', 'Waiting')), 9),
    CA('place', 'Place on the list for the service', 'int', 'IF({col:status}=%s,COUNTIFS({range:waiting.service},{col:service},{range:waiting.status},%s,{range:waiting.added_on},"<="&{col:added_on}),"")' % (ST('waitst', 'Waiting'), ST('waitst', 'Waiting')), 12),
    STAFF_PH('TH-01', 'owner_phone')], D.waiting_d(), 800,
    [A('wait_check', '= ' + ck('Over target'), 'bad'), A('act_rank', '<= 5', 'warn'), A('status', '= ' + ST('waitst', 'Started'), 'good')]))
tables.append(T('screening', 'Screening Calls', 'Screening calls with minutes, suitability and next step',
    'One row per screening call: who made it, minutes, whether the enquiry is suitable, the urgency and the next step; days after the enquiry fill in by themselves.', [
    C('call_id', 'Call ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('enquiry_id', 'Enquiry ID', 'text', 10), C('enquired_on', 'Enquired on', 'date', 11), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18),
    REF('screened_by', 'Screened by', 'team.name', 20), C('minutes', 'Minutes', 'int', 9), C('suitable', 'Suitable', 'bool', 9), LST('urgency', 'Urgency', 'prio', 9), LST('next_step', 'Next step', 'nextstep', 14),
    CA('days_after', 'Days after the enquiry', 'int', '{col:date}-{col:enquired_on}', 10), CA('screener_phone', 'Screener phone', 'text', LKT('team.phone', 'team.name', 'screened_by'), 18)], D.screening_d(), 800,
    [A('days_after', '> {set:screen_days}', 'warn'), A('urgency', '= ' + ST('prio', 'High'), 'bad')]))
tables.append(T('callbacks', 'Call-back Log', 'Call-back attempts for enquiries that did not answer',
    'One row per call-back attempt: method, whether the person was reached and the next try; attempts left and today\'s call-back check fill in by themselves.', [
    C('callback_id', 'Call-back ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('enquiry_id', 'Enquiry ID', 'text', 10), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18), C('attempt', 'Attempt', 'int', 9),
    C('method', 'Method', 'text', 14), C('reached', 'Reached', 'bool', 9), C('next_try', 'Next try', 'date', 11),
    CA('attempts_left', 'Attempts left', 'int', 'IF({col:reached}=%s,0,MAX(0,{set:callback_attempts}-{col:attempt}))' % YES, 9),
    CA('call_flag', 'Call-back check', 'text', 'IF({col:next_try}="",%s,IF({col:next_try}<{today},%s,IF({col:next_try}={today},%s,%s)))' % (ck('Closed'), ck('Closed'), ck('Call today'), ck('Not due yet')), 14),
    STAFF_PH('TH-07', 'coordinator_phone')], D.callbacks_d(), 800, [A('call_flag', '= ' + ck('Call today'), 'bad'), A('reached', '= ' + YES, 'good')]))
tables.append(T('offers', 'Offers Made', 'Offers of a regular time with the answer',
    'One row per offer of a regular time to someone on the waitlist: clinician, weekday, time and answer; the name, phone, days to answer and the reply-by date fill in by themselves.', [
    C('offer_id', 'Offer ID', 'text', 9, required=True), C('offered_on', 'Offered on', 'date', 11), C('wait_id', 'Wait ID', 'text', 9), LST('clinician', 'Clinician', 'clin', 16), LST('weekday', 'Weekday', 'wday', 11),
    C('time', 'Time', 'time', 8), LST('answer', 'Answer', 'answer', 10), C('answered_on', 'Answered on', 'date', 11),
    CA('name', 'Name', 'text', LKT('waiting.name', 'waiting.wait_id', 'wait_id'), 24), CA('phone', 'Phone', 'text', LKT('waiting.phone', 'waiting.wait_id', 'wait_id'), 18),
    CA('days_to_answer', 'Days to answer', 'int', 'IF({col:answered_on}="","",{col:answered_on}-{col:offered_on})', 10), CA('reply_by', 'Reply by', 'date', '{col:offered_on}+{set:offer_reply_days}', 11)], D.offers_d(), 800,
    [A('answer', '= ' + ST('answer', 'Declined'), 'warn'), A('answer', '= ' + ST('answer', 'Accepted'), 'good')]))
tables.append(T('checkins', 'Waitlist Check-ins', 'Waitlist check-ins and the answer',
    'One row per check-in call or message to someone waiting: who made it and the answer; weeks on the list and the date of the next check-in fill in by themselves.', [
    C('checkin_id', 'Check-in ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('wait_id', 'Wait ID', 'text', 9), REF('contacted_by', 'Contacted by', 'team.name', 20), LST('answer', 'Answer', 'answer', 10), C('still_waiting', 'Still waiting', 'bool', 9),
    CA('name', 'Name', 'text', LKT('waiting.name', 'waiting.wait_id', 'wait_id'), 24), CA('phone', 'Phone', 'text', LKT('waiting.phone', 'waiting.wait_id', 'wait_id'), 18),
    CA('added_on', 'Added on', 'date', LKD('waiting.added_on', 'waiting.wait_id', 'wait_id'), 11), CA('weeks_on_list', 'Weeks on the list', 'int', 'IF({col:added_on}="","",INT(({col:date}-{col:added_on})/7))', 10),
    CA('next_checkin', 'Next check-in', 'date', '{col:date}+7*{set:checkin_weeks}', 11), STAFF_PH('TH-07', 'coordinator_phone')], D.checkins_d(), 500,
    [A('answer', '= ' + ST('answer', 'Declined'), 'warn')]))
tables.append(T('lost', 'Lost Enquiries', 'Lost enquiries by cause with re-contact date',
    'One row per enquiry that did not become a client: the cause, the last contact and a re-contact date; days open and the re-contact check fill in by themselves.', [
    C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18), LST('service', 'Service', 'svc', 18), LST('client_type', 'Client type', 'ctype', 12),
    LST('cause', 'Cause', 'cause', 20), C('last_contact', 'Last contact', 'date', 11), C('recontact_date', 'Re-contact date', 'date', 12),
    CA('days_open', 'Days open', 'int', '{col:last_contact}-{col:date}', 9),
    CA('recontact_flag', 'Re-contact check', 'text', 'IF({col:recontact_date}="",%s,IF({col:recontact_date}<={today},%s,%s))' % (ck('No re-contact'), ck('Re-contact due'), ck('Re-contact planned')), 15)], D.lost_d(), 800,
    [A('recontact_flag', '= ' + ck('Re-contact due'), 'bad'), A('cause', '= ' + ST('cause', 'Waited too long'), 'warn')]))
tables.append(T('signpost', 'Signposting Log', 'Signposting log: enquiries sent to other services',
    'One row per enquiry the practice sent to another service: where, why and whether information was sent; the same-week check fills in by itself.', [
    C('signpost_id', 'Signpost ID', 'text', 10, required=True), C('enquiry_id', 'Enquiry ID', 'text', 10), C('enquired_on', 'Enquired on', 'date', 11), C('date', 'Signposted on', 'date', 11), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18),
    LST('service', 'Service needed', 'svc', 18), C('referred_to', 'Referred to', 'text', 20), C('reason', 'Reason', 'text', 20), C('info_sent', 'Information sent', 'bool', 10),
    CA('same_week', 'Within 7 days check', 'text', 'IF({col:date}-{col:enquired_on}<=6,%s,%s)' % (ck('Within 7 days'), ck('Later than 7 days')), 15)], D.signpost_d(), 500,
    [A('same_week', '= ' + ck('Later than 7 days'), 'warn')]))
tables.append(T('intake', 'Intake Sessions', 'Intake sessions with show rate and return flag',
    'One row per intake session (the first assessment session): clinician, format, room and status; the return check (did the client come back) and the clinician phone fill in by themselves.', [
    C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), LST('clinician', 'Clinician', 'clin', 16), LST('format', 'Format', 'fmt', 11),
    C('room', 'Room', 'text', 14), LST('status', 'Status', 'sstatus', 12), C('fee_waived', 'Fee waived', 'bool', 9),
    CA('came_back', 'Return check', 'text', 'IF({col:status}=%s,IF(%s>=2,%s,%s),%s)' % (ST('sstatus', 'Attended'), LKN('clients.sessions_attended', 'clients.client_id', 'client_id'), ck('Came back'), ck('Did not return'), ck('Not attended')), 14),
    CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), CA('clinician_phone', 'Clinician phone', 'text', LKT('team.phone', 'team.name', 'clinician'), 18)], D.intake_d(), 800,
    [A('status', '= ' + ST('sstatus', 'No-show'), 'bad'), A('status', '= ' + ST('sstatus', 'Late cancel'), 'warn'), A('came_back', '= ' + ck('Did not return'), 'warn')]))
tables.append(T('clients', 'New Clients', 'New clients with first session, fee and clinician',
    'One row per new client: service, clinician, booking and first session dates, format and fee type; days to first session and the fee per session fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), LST('client_type', 'Client type', 'ctype', 12), C('contact', 'Contact person', 'text', 22), C('phone', 'Phone', 'text', 18),
    LST('service', 'Service', 'svc', 18), LST('clinician', 'Clinician', 'clin', 16), C('booked_on', 'Booked on', 'date', 11), C('first_session', 'First session', 'date', 12), C('first_time', 'First session time', 'time', 9),
    C('room', 'Room', 'text', 14), LST('format', 'Format', 'fmt', 11), LST('fee_type', 'Fee type', 'feetype', 17), C('frequency', 'Frequency', 'text', 12), C('payer', 'Payer', 'text', 10),
    C('sliding_pct', 'Sliding scale share', 'pct', 10), C('sessions_attended', 'Sessions attended', 'int', 10),
    CA('days_to_first', 'Days booking to first session', 'int', '{col:first_session}-{col:booked_on}', 11),
    CA('list_fee', 'List fee', 'money', LKN('services.fee', 'services.service', 'service'), 10), CA('fee_quote', 'Fee per session', 'money', 'ROUND({col:list_fee}*{col:sliding_pct},0)', 11),
    CA('clinician_phone', 'Clinician phone', 'text', LKT('team.phone', 'team.name', 'clinician'), 18), CA('company', 'Practice', 'text', '"%s"' % COMPANY, 24)], D.clients_d(), 800,
    [A('days_to_first', '> {set:target_wait_days}', 'warn')]))
tables.append(T('deposits', 'Deposits', 'Deposits held, applied, kept or refunded',
    'One row per new-client deposit: the client, amount and status; days held and the client phone fill in by themselves.', [
    C('deposit_id', 'Deposit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), C('amount', 'Amount', 'int', 9),
    C('applied_on', 'Applied on', 'date', 11), LST('status', 'Status', 'depst', 10),
    CA('days_held', 'Days held', 'int', 'IF({col:status}=%s,{today}-{col:date},IF(AND({col:status}=%s,{col:applied_on}<>""),{col:applied_on}-{col:date},""))' % (ST('depst', 'Held'), ST('depst', 'Applied')), 9),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18), STAFF_PH('TH-07', 'coordinator_phone')], D.deposits_d(), 500,
    [A('status', '= ' + ST('depst', 'Held'), 'warn'), A('status', '= ' + ST('depst', 'Kept'), 'bad')]))
tables.append(T('paperwork', 'Intake Paperwork', 'Intake paperwork status before the first session',
    'One row per new client: forms sent and back, consent and contact details checked; the client, first session and the forms check fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('forms_sent_on', 'Forms sent on', 'date', 12), C('forms_back_on', 'Forms back on', 'date', 12), C('consent_back', 'Consent back', 'bool', 9), C('details_checked', 'Details checked', 'bool', 9),
    CA('client', 'Client', 'text', LKT('clients.client', 'clients.client_id', 'client_id'), 24), CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18),
    CA('first_session', 'First session', 'date', LKD('clients.first_session', 'clients.client_id', 'client_id'), 12),
    CA('form_flag', 'Forms check', 'text', 'IF({col:forms_back_on}<>"",IF({col:forms_back_on}<={col:first_session},%s,%s),IF({col:first_session}<={today},%s,%s))' % (ck('Back on time'), ck('Back late'), ck('Missing, session passed'), ck('Open, session ahead')), 18),
    STAFF_PH('TH-07', 'coordinator_phone')], D.paperwork_d(), 800, [A('form_flag', '= ' + ck('Missing, session passed'), 'bad'), A('form_flag', '= ' + ck('Back late'), 'warn'), A('form_flag', '= ' + ck('Back on time'), 'good')]))
tables.append(T('slots', 'Free Slots Next 4 Weeks', 'Free diary slots for the next four weeks',
    'One row per free diary slot: clinician, day, time and how the slot is used (open, held for intakes or held for urgent cases); days ahead fills in by itself.', [
    C('slot_id', 'Slot ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), C('date', 'Date', 'date', 11), LST('weekday', 'Weekday', 'wday', 11), C('time', 'Time', 'time', 8), LST('clinician', 'Clinician', 'clin', 16),
    LST('status', 'Slot use', 'slothold', 13), CA('days_ahead', 'Days ahead', 'int', '{col:date}-{today}', 9)], D.slots_d(), 400, [A('status', '= ' + ST('slothold', 'Urgent hold'), 'warn')]))
tables.append(T('capacity', 'Intake Capacity by Week', 'Intake capacity by clinician and week',
    'One row per clinician and week for six weeks: free slots and intakes booked; the intakes still possible under the weekly limit fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 8, required=True), C('week', 'Week (Monday)', 'date', 12), LST('clinician', 'Clinician', 'clin', 16), C('free_slots', 'Free slots', 'int', 9), C('intakes_booked', 'Intakes booked', 'int', 9),
    CA('intakes_possible', 'Intakes still possible', 'int', 'MAX(0,MIN({col:free_slots},{set:intake_limit_week}-{col:intakes_booked}))', 10),
    CA('cap_flag', 'Capacity check', 'text', 'IF({col:intakes_possible}>0,%s,%s)' % (ck('Intake possible'), ck('No intake possible')), 16)], D.capacity_d(), 100,
    [A('cap_flag', '= ' + ck('No intake possible'), 'warn'), A('cap_flag', '= ' + ck('Intake possible'), 'good')]))
FREEM = 'COUNTIFS({range:slots.clinician},{col:clinician},{range:slots.status},"<>"&%s)' % ST('slothold', 'Urgent hold')
tables.append(T('match', 'Clinician Match Rules', 'Clinician match rules by service and client type',
    'One row per rule: which clinician takes which service and client type (1 is first choice); free slots in 28 days, the next free date and the match check fill in by themselves.', [
    C('rule_id', 'Rule ID', 'text', 9, required=True), C('no', 'Rule no', 'int', 9), LST('service', 'Service', 'svc', 18), LST('client_type', 'Client type', 'ctype', 12), LST('clinician', 'Clinician', 'clin', 16), C('preference', 'Preference', 'int', 9), C('takes_new', 'Takes new clients', 'bool', 10),
    CA('free_28d', 'Free slots, 28 days', 'int', FREEM, 10),
    CA('next_free', 'Next free slot', 'date', 'IF(SUMPRODUCT(MIN(({range:slots.clinician}={col:clinician})*({range:slots.date})+({range:slots.clinician}<>{col:clinician})*99999))>=99999,"",SUMPRODUCT(MIN(({range:slots.clinician}={col:clinician})*({range:slots.date})+({range:slots.clinician}<>{col:clinician})*99999)))', 11),
    CA('match_flag', 'Match check', 'text', 'IF({col:takes_new}=%s,IF({col:free_28d}>0,%s,%s),%s)' % (YES, ck('Ready to take'), ck('No free slots'), ck('Full for now')), 14),
    CA('clinician_phone', 'Clinician phone', 'text', LKT('team.phone', 'team.name', 'clinician'), 18)], D.match_d(), 100, [A('match_flag', '= ' + ck('Ready to take'), 'good'), A('match_flag', '= ' + ck('Full for now'), 'warn')]))
tables.append(T('targets', 'Priority Targets', 'Target days to offer by client type and priority',
    'Fifteen targets: client type, priority and the days within which a place should be offered; the waitlist reads them.', [
    LST('client_type', 'Client type', 'ctype', 12, required=True), LST('priority', 'Priority', 'prio', 9), C('target_days', 'Target days to offer', 'int', 12)], D.targets_d(), 50))
tables.append(T('funnel', 'Intake Funnel by Month', 'Monthly intake funnel from enquiry to start',
    'One row per month: enquiries, screened, booked, started, people waiting at month end and people who gave up; the conversion and screening rates fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), C('enquiries', 'Enquiries', 'int', 10), C('screened', 'Screened', 'int', 10), C('booked', 'Booked', 'int', 10), C('started', 'Started', 'int', 10),
    C('waiting_end', 'Waiting at month end', 'int', 11), C('withdrawn', 'Withdrawn', 'int', 10),
    CA('conversion', 'Conversion, % booked', 'pct', 'IF({col:enquiries}>0,{col:booked}/{col:enquiries},0)', 11), CA('screening_rate', 'Screening rate, %', 'pct', 'IF({col:enquiries}>0,{col:screened}/{col:enquiries},0)', 11),
    CA('conv_flag', 'Conversion check', 'text', 'IF({col:conversion}>={set:target_conv},%s,%s)' % (ck('Within target'), ck('Over target')), 14)], D.funnel_d(), 60, [A('conversion', '< {set:target_conv}', 'warn')]))
tables.append(T('demand', 'Service Demand by Month', 'Service demand by month and service',
    'One row per month and service: enquiries, booked and still waiting; the booked share fills in by itself.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('service', 'Service', 'svc', 18), C('enquiries', 'Enquiries', 'int', 10), C('booked', 'Booked', 'int', 10), C('still_waiting', 'Still waiting', 'int', 10),
    CA('booked_share', 'Booked share', 'pct', 'IF({col:enquiries}>0,{col:booked}/{col:enquiries},0)', 10)], D.demand_d(), 300))
tables.append(T('services', 'Services', 'Services with minutes and list fee', 'One row per service: minutes and this year\'s list fee before any tax.', [
    C('service', 'Service', 'text', 22, required=True), C('minutes', 'Minutes', 'int', 9), C('fee', 'Fee', 'money', 11)], D.services_d(), 50))
tables.append(T('team', 'Team', 'Team: clinicians, coordinator and outside contacts',
    'One row per person: employed, contract (self-employed) and associate (works under supervision) clinicians, the coordinator and outside contacts; free slots fill in by themselves.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 24), C('team', 'Team', 'text', 12), C('pay_type', 'Pay type', 'text', 16), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26),
    C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'int', 11), C('split_pct', 'Split share', 'pct', 9), C('session_rate', 'Rate per session', 'int', 10), C('hourly_rate', 'Hourly rate', 'int', 9),
    C('session_cap', 'Session cap a week', 'int', 10), C('session_target', 'Session target a week', 'int', 10), C('speciality', 'Speciality', 'text', 30), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
    CA('free_28d', 'Free slots, 28 days', 'int', 'COUNTIFS({range:slots.clinician},{col:name},{range:slots.status},"<>"&%s)' % ST('slothold', 'Urgent hold'), 10),
    CA('takes_flag', 'New client check', 'text', 'IF({col:session_cap}=0,"",IF(COUNTIFS({range:match.clinician},{col:name},{range:match.takes_new},%s)>0,%s,%s))' % (YES, ck('Takes new clients'), ck('Full for now')), 16)], D.team_d(), 50))
assert len(tables) == 20
