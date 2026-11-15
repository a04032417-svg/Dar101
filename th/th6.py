"""Therapy private practice suite - part 6: Clinical Admin, Supervision and Renewals."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from th6_lists import *
from th6_tables import settings, tables
from th6_tools import tools

SUITE = 'fx-20261115-therapy-practice'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
YES = '{list:yesno.yes}'
JAN1 = 'DATE(YEAR({today}),1,1)'
def W(c, n): return '{range:%s},">="&({today}-%d),{range:%s},"<="&{today}' % (c, n - 1, c)

TB = {t['key']: t for t in tables}
def front(tk, pred):
    rows = TB[tk]['demo']
    for i, r in enumerate(rows):
        if pred(r):
            rows.insert(0, rows.pop(i)); return
    raise SystemExit('no front row for ' + tk)
_ch_int = {r['client_id'] for r in TB['change']['demo'] if r.get('intake_score')}
_k = 0
for r in TB['notes']['demo']:
    if r['date'] == ago(2) and r['clinician'] in ('priya_raman', 'sofia_marchetti') and r.get('note_done_on') and _k < 3:
        r['note_done_on'] = ''; _k += 1
assert _k == 3
front('notes', lambda r: r.get('note_done_on'))
front('reviews', lambda r: r.get('reviewed_on') and r.get('score'))
front('scores', lambda r: r.get('point') != key('opoint', 'Intake') and r.get('client_id') in _ch_int)
front('suplog', lambda r: (r.get('cost') or 0) > 0 and r.get('hours'))
front('celog', lambda r: (r.get('cost') or 0) > 0 and r.get('certificate') == 'yes' and r.get('hours'))
front('consent', lambda r: r.get('reviewed_on'))
front('requests', lambda r: not r.get('sent_on'))
front('incidents', lambda r: r.get('closed_on'))
front('discharges', lambda r: r.get('referred_to') and r.get('referral_sent') == 'yes' and r.get('letter_sent') == 'yes')

forms = [
 FORM('note_sheet', 'Session Note Sheet', 'Session note timing for one session', 'notes.session_id', F(
  ('Date', 'notes.date'), ('Client', 'notes.client'), ('Clinician', 'notes.clinician'), ('Service', 'notes.service'), ('Note done on', 'notes.note_done_on'), ('Days to note', 'notes.days_to_note'), ('On-time check', 'notes.note_check'))),
 FORM('review_sheet', 'Plan Review Sheet', 'Treatment-plan review with status', 'reviews.review_id', F(
  ('Client ID', 'reviews.client_id'), ('Client', 'reviews.client'), ('Clinician', 'reviews.clinician'), ('Review number', 'reviews.review_no'), ('Due date', 'reviews.due_date'), ('Reviewed on', 'reviews.reviewed_on'), ('Outcome score', 'reviews.score'), ('Review status', 'reviews.status'))),
 FORM('score_sheet', 'Outcome Score Sheet', 'Outcome score against the intake score', 'scores.score_id', F(
  ('Date', 'scores.date'), ('Client ID', 'scores.client_id'), ('Client', 'scores.client'), ('Clinician', 'scores.clinician'), ('Score point', 'scores.point'), ('Score', 'scores.score'), ('Points against intake', 'scores.vs_intake'))),
 FORM('closing_sheet', 'Closing Summary Sheet', 'Discharge with closing letter check', 'discharges.discharge_id', F(
  ('Date', 'discharges.date'), ('Client', 'discharges.client'), ('Phone', 'discharges.phone'), ('Clinician', 'discharges.clinician'), ('Service', 'discharges.service'), ('Reason', 'discharges.reason'), ('Sessions', 'discharges.sessions'),
  ('Last session', 'discharges.last_session'), ('Days since last session', 'discharges.days_since_last'), ('Closing letter sent', 'discharges.letter_sent'), ('Closing letter check', 'discharges.letter_check'))),
 FORM('referral_sheet', 'Referral Out Sheet', 'Referral out with letter check', 'discharges.discharge_id', F(
  ('Date', 'discharges.date'), ('Client', 'discharges.client'), ('Clinician', 'discharges.clinician'), ('Reason', 'discharges.reason'), ('Referred to', 'discharges.referred_to'), ('Referral letter sent', 'discharges.referral_sent'), ('Referral letter check', 'discharges.referral_check'))),
 FORM('supervision_sheet', 'Supervision Session Sheet', 'Supervision session with cost per hour', 'suplog.supervision_id', F(
  ('Date', 'suplog.date'), ('Supervisee', 'suplog.supervisee'), ('Supervisor', 'suplog.supervisor'), ('Kind', 'suplog.kind'), ('Hours', 'suplog.hours'), ('Cost', 'suplog.cost'), ('Cost per hour', 'suplog.cost_per_hour'))),
 FORM('ce_sheet', 'Continuing Education Sheet', 'Course with certificate and cost per hour', 'celog.ce_id', F(
  ('Date', 'celog.date'), ('Clinician', 'celog.clinician'), ('Kind', 'celog.kind'), ('Title', 'celog.title'), ('Hours', 'celog.hours'), ('Cost', 'celog.cost'), ('Paid by', 'celog.paid_by'), ('Certificate', 'celog.certificate'), ('Hours counted', 'celog.counted_hours'), ('Cost per hour', 'celog.cost_per_hour'))),
 FORM('renewal_sheet', 'Renewal Sheet', 'Renewal with status and act-first rank', 'renewals.renewal_id', F(
  ('Holder', 'renewals.holder'), ('Item', 'renewals.item'), ('Renewed every (months)', 'renewals.every_months'), ('Due date', 'renewals.due_date'), ('Cost', 'renewals.cost'), ('Paid by', 'renewals.paid_by'), ('Days to due', 'renewals.days_to_due'), ('Status', 'renewals.status'), ('Act-first rank', 'renewals.act_rank'))),
 FORM('consent_sheet', 'Consent Review Sheet', 'Client consent with next review', 'consent.consent_id', F(
  ('Client', 'consent.client'), ('Clinician', 'consent.clinician'), ('Client status', 'consent.status'), ('Signed on', 'consent.signed_on'), ('Reviewed on', 'consent.reviewed_on'), ('Next review', 'consent.next_review'), ('Days to review', 'consent.days_to_review'), ('Review check', 'consent.review_check'))),
 FORM('request_sheet', 'Record Request Sheet', 'Record request with deadline', 'requests.request_id', F(
  ('Date received', 'requests.date'), ('Client', 'requests.client'), ('Kind', 'requests.kind'), ('Due date', 'requests.due_date'), ('Days left', 'requests.days_left'), ('Status', 'requests.status'))),
 FORM('incident_sheet', 'Incident Sheet', 'Incident or complaint with days open', 'incidents.incident_id', F(
  ('Date', 'incidents.date'), ('Kind', 'incidents.kind'), ('Area', 'incidents.area'), ('Action taken', 'incidents.action_taken'), ('Handled by', 'incidents.handled_by'), ('Closed on', 'incidents.closed_on'), ('Days open', 'incidents.days_open'), ('Status', 'incidents.status'))),
 FORM('policy_sheet', 'Policy Review Sheet', 'Policy with next review date', 'policies.policy_id', F(
  ('Policy', 'policies.policy'), ('Last reviewed', 'policies.last_reviewed'), ('Reviewed every (months)', 'policies.every_months'), ('Reviewed by', 'policies.reviewed_by'), ('Next review', 'policies.next_review'), ('Days to review', 'policies.days_to_review'), ('Review check', 'policies.review_check'))),
]
assert len(forms) == 12

def D_(k, sheet, title, pick, paras, sign): return DOC(k, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('closing_doc', 'Closing Letter', 'Closing letter to a client', 'discharges.discharge_id', [
  'Closing letter of {set:company}, dated {today}. Dear {col:discharges.client},', 'Your last session was on {col:discharges.last_session} and your care with {col:discharges.clinician} closed on {col:discharges.date}. You had {col:discharges.sessions} sessions in all.',
  'You are welcome to contact us again at any time and we will open a new enquiry. Your records are kept securely; ask the front desk if you need a copy. Reference {col:discharges.discharge_id}.'], ['Clinician']),
 D_('referral_doc', 'Referral Letter', 'Referral letter to another service', 'discharges.discharge_id', [
  'Referral letter of {set:company}, dated {today}. Dear {col:discharges.client},', 'With your agreement we suggest you contact: {col:discharges.referred_to}. Your care with us closed on {col:discharges.date}; the reason recorded is {col:discharges.reason}.',
  'We only share details with the other service if you agree; check your own local rules. Reference {col:discharges.discharge_id}.'], ['Clinician']),
 D_('sup_record_doc', 'Supervision Record', 'Supervision record for one month', 'supmonth.row_id', [
  'Supervision record of {set:company}, dated {today}. Month {col:supmonth.month}. Clinician: {col:supmonth.clinician}.', 'Client sessions seen: {col:supmonth.client_sessions}. Supervision hours logged in the month: {col:supmonth.hours_logged}. Hours required at {set:supervision_ratio} client sessions per hour: {col:supmonth.required}.',
  'Hours owed to date: {col:supmonth.owed_to_date}. Hours logged to date: {col:supmonth.logged_to_date}. Hours behind: {col:supmonth.hours_debt}. Check: {col:supmonth.up_flag}.'], ['Clinician', 'Supervisor']),
 D_('sup_agreement_doc', 'Supervision Agreement', 'Supervision agreement for an associate', 'team.staff_id', [
  'Supervision agreement of {set:company}, dated {today}. Between {col:team.name} ({col:team.role}) and the supervising clinician.', 'We agree one hour of supervision for every {set:supervision_ratio} client sessions, plus {set:peer_hours_month} hours of peer supervision a month. Supervision hours owed to date: {col:team.hours_owed}. Logged: {col:team.hours_logged}.',
  'Supervision covers caseload, risk and practice questions. The workbook records hours and dates only, never case content.'], ['Associate', 'Supervisor']),
 D_('ce_record_doc', 'Continuing Education Record', 'Continuing education record for a year', 'ceyear.row_id', [
  'Continuing education record of {set:company}, dated {today}. Year {col:ceyear.year}. Clinician: {col:ceyear.clinician}.', 'Target hours: {col:ceyear.target}. Hours with a certificate: {col:ceyear.hours}. Hours still needed: {col:ceyear.hours_needed}. Cost: {col:ceyear.cost}. Cost per hour: {col:ceyear.cost_per_hour}.',
  'Pace check: {col:ceyear.pace_flag}. Check your own local rules on the hours and the proof you must keep.'], ['Clinician']),
 D_('renewal_doc', 'Renewal Reminder', 'Renewal reminder for one item', 'renewals.renewal_id', [
  'Renewal reminder of {set:company}, dated {today}. Dear {col:renewals.holder},', 'Your {col:renewals.item} is due for renewal on {col:renewals.due_date}. It is renewed every {col:renewals.every_months} months and costs {col:renewals.cost}, paid by {col:renewals.paid_by}.',
  'Status: {col:renewals.status}. Please send the new certificate to the front desk once renewed. Reference {col:renewals.renewal_id}.'], ['Practice coordinator']),
 D_('consent_doc', 'Consent Renewal Letter', 'Consent renewal letter to a client', 'consent.consent_id', [
  'Consent renewal letter of {set:company}, dated {today}. Dear {col:consent.client},', 'You signed your consent form on {col:consent.signed_on}. We review it every {set:consent_review_months} months; your next review is on {col:consent.next_review}.',
  'Please read the updated form with {col:consent.clinician} and sign it at your next session. Check your own local rules on consent. Reference {col:consent.consent_id}.'], ['Clinician']),
 D_('request_doc', 'Records Request Reply', 'Reply to a records request', 'requests.request_id', [
  'Reply to your request, from {set:company}, dated {today}. Dear {col:requests.client},', 'We received your request ({col:requests.kind}) on {col:requests.date}. We will answer by {col:requests.due_date}, within {set:request_days} days of the request. Check your own local rules on the time allowed.',
  'We may ask you to confirm who you are before we send anything. Reference {col:requests.request_id}.'], ['Practice coordinator']),
 D_('incident_doc', 'Incident Report', 'Incident or complaint report', 'incidents.incident_id', [
  'Incident report of {set:company}, dated {today}. Reference {col:incidents.incident_id}.', 'Date: {col:incidents.date}. Kind: {col:incidents.kind}. Area: {col:incidents.area}. Handled by: {col:incidents.handled_by}. Status: {col:incidents.status}. Days open: {col:incidents.days_open}.',
  'Action taken: {col:incidents.action_taken}. This report holds facts about the administration only and no client details or case content.'], ['Owner', 'Practice coordinator']),
 D_('notes_report_doc', 'Note Timeliness Report', 'Note timeliness report for one clinician and month', 'months.row_id', [
  'Note timeliness report of {set:company}, dated {today}. Month {col:months.month}. Clinician: {col:months.clinician}.', 'Sessions attended: {col:months.attended}. Notes on time: {col:months.on_time}. Late: {col:months.late}. Missing: {col:months.missing}. On-time share: {col:months.on_time_share}. Target: {set:note_target_rate}.',
  'Plan reviews due: {col:months.reviews_due}. Done: {col:months.reviews_done}. Rule check: {col:months.rule_flag}.'], ['Owner']),
 D_('privacy_doc', 'Privacy Check Record', 'Monthly privacy check record', 'privacy.check_id', [
  'Privacy check record of {set:company}, dated {today}. Month {col:privacy.month}. Done by {col:privacy.done_by}.', 'Passwords changed: {col:privacy.passwords_changed}. Cabinets locked: {col:privacy.cabinets_locked}. Devices checked: {col:privacy.devices_checked}. Result: {col:privacy.all_done}.',
  'Check your own local rules on privacy and keep this record with your policies.'], ['Practice coordinator']),
 D_('admin_register_doc', 'Clinician Admin Summary', 'Admin summary for one team member', 'team.staff_id', [
  'Admin summary of {set:company}, dated {today}. Team member: {col:team.name} ({col:team.role}).', 'Session notes overdue: {col:team.notes_overdue}. Plan reviews overdue: {col:team.reviews_overdue}. Continuing education hours this year: {col:team.ce_hours}. Hours still needed: {col:team.hours_needed}.',
  'Renewals open: {col:team.renewals_open}. Next renewal: {col:team.next_renewal}. Review these points together at the next one-to-one.'], ['Owner']),
]
assert len(documents) == 12

def CS(k, title, table, start, steps): return CHK(k, title, table, start, steps)
checklists = [
 CS('c_notes', 'Session Note Steps', 'notes', 'notes.date', [('Write the note the same day', 0), ('Record the note-done date', 1), ('Check the note is within the rule', 2), ('Escalate to the owner if still open', 3), ('Close the item', 4)]),
 CS('c_review', 'Plan Review Steps', 'reviews', 'reviews.due_date', [('Book the review session', -14), ('Collect the latest outcome score', -7), ('Hold the review', 0), ('Record the review date and score', 1), ('Set the next review date', 1)]),
 CS('c_score', 'Outcome Score Steps', 'scores', 'scores.date', [('Hand the client the form', 0), ('Record the score', 0), ('Compare with the intake score', 1), ('Note the change on the plan', 2), ('Book a review if the score did not improve', 7)]),
 CS('c_closing', 'Closing a Client Steps', 'discharges', 'discharges.date', [('Agree the closing with the client', -7), ('Record the final outcome score', 0), ('Send the closing letter', 7), ('Mark the file for archive', 14), ('Set the keep-until date', 14)]),
 CS('c_referral', 'Referral Out Steps', 'discharges', 'discharges.date', [('Choose the service with the client', -3), ('Get the client\'s agreement to share details', 0), ('Send the referral letter', 3), ('Record that it was sent', 3), ('Check the client reached the service', 21)]),
 CS('c_supweek', 'Weekly Supervision Steps', 'suplog', 'suplog.date', [('Prepare the cases to discuss', -2), ('Hold the supervision', 0), ('Log the date and hours', 0), ('Note the actions agreed', 1), ('Check hours against the ratio', 7)]),
 CS('c_supgroup', 'Monthly Group Supervision Steps', 'suplog', 'suplog.date', [('Send the invitation', -14), ('Confirm the attendees', -7), ('Pay the supervisor fee', 7), ('Log the hours for each attendee', 0), ('Book the next group', 1)]),
 CS('c_ceplan', 'Continuing Education Plan Steps', 'celog', 'celog.date', [('Choose the course', -30), ('Book and pay', -14), ('Attend and keep the certificate', 0), ('Record the hours and cost', 1), ('Check the yearly target', 7)]),
 CS('c_renewal', 'Renewal Steps', 'renewals', 'renewals.due_date', [('Check the renewal date', -60), ('Ask the holder for the new certificate', -45), ('Pay the renewal', -30), ('Record the renewed date', -7), ('Escalate to the owner if not done', -3)]),
 CS('c_consent', 'Consent Review Steps', 'consent', 'consent.signed_on', [('Send the updated form', 335), ('Review the form with the client', 350), ('Record the review date', 351), ('Set the next review date', 351), ('Store the signed form', 352)]),
 CS('c_request', 'Record Request Steps', 'requests', 'requests.date', [('Confirm who the client is', 0), ('Check what may be shared; check your own local rules', 2), ('Prepare the copy or letter', 10), ('Send it', 20), ('Record the sent date', 21)]),
 CS('c_privacy', 'Monthly Privacy Check Steps', 'privacy', 'privacy.month', [('Change shared passwords', 1), ('Lock the cabinets and check keys', 1), ('Check devices and backups', 2), ('Record the check', 3), ('Fix any gap found', 7)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('t_notes', 'Clinician: notes overdue', 'team', 'team.phone', 'Hello {name}, you have {notes_overdue} session notes still open past the deadline. Please finish them today. {company}'),
 M('t_ce', 'Clinician: hours still needed', 'team', 'team.phone', 'Hello {name}, you still need {hours_needed} continuing education hours with a certificate this year. Please book a course. {company}'),
 M('t_renew', 'Clinician: your next renewal', 'team', 'team.phone', 'Hello {name}, you have {renewals_open} open renewals and the next is on {next_renewal}. Please send the new certificate when done. {company}'),
 M('t_sup', 'Associate: supervision owed', 'team', 'team.phone', 'Hello {name}, supervision hours owed to date are {hours_owed} and logged are {hours_logged}. Please book the next supervision. {company}'),
 M('t_rev', 'Clinician: plan reviews overdue', 'team', 'team.phone', 'Hello {name}, {reviews_overdue} treatment-plan reviews in your caseload are overdue. Please book them this week. {company}'),
 M('n_due', 'Clinician: note due today', 'notes', 'notes.clinician_phone', 'Hello {clinician}, the note for {client} from the session on {date} is due now. Please finish it today. {company}'),
 M('n_over', 'Clinician: note overdue', 'notes', 'notes.clinician_phone', 'Hello {clinician}, the note for {client} (session {date}) is {overdue_days} days past the deadline. Please finish it today. {company}'),
 M('r_due', 'Clinician: plan review due', 'reviews', 'reviews.clinician_phone', 'Hello {clinician}, review {review_no} for {client} is due on {due_date}. Please book the review session. {company}'),
 M('r_over', 'Clinician: plan review overdue', 'reviews', 'reviews.clinician_phone', 'Hello {clinician}, the plan review for {client} was due on {due_date} and is {days_overdue} days overdue. Please do it this week. {company}'),
 M('ch_score', 'Clinician: intake score missing', 'change', 'change.clinician_phone', 'Hello {clinician}, {client} has no intake outcome score on record. Please add it so we can show the change. {company}'),
 M('d_letter', 'Client: closing letter', 'discharges', 'discharges.phone', 'Hello {client}, thank you for your time with us. Your closing letter after the last session on {last_session} is on its way. You are welcome to contact {company} again.'),
 M('d_refer', 'Client: referral letter', 'discharges', 'discharges.phone', 'Hello {client}, as agreed we have sent a letter suggesting {referred_to}. Please contact them when you are ready. {company}'),
 M('d_clin', 'Clinician: closing letter not sent', 'discharges', 'discharges.clinician_phone', 'Hello {clinician}, the closing letter for {client}, closed on {date}, is not sent yet. Please send it this week. {company}'),
 M('s_book', 'Supervisee: supervision booked', 'suplog', 'suplog.supervisee_phone', 'Hello {supervisee}, your supervision with {supervisor} is on {date} for {hours} hours. {company}'),
 M('s_sup', 'Supervisor: session to run', 'suplog', 'suplog.supervisor_phone', 'Hello {supervisor}, the {kind} session with {supervisee} is on {date}. Please log the hours afterwards. {company}'),
 M('s_fee', 'Supervisor: fee to pay', 'suplog', 'suplog.supervisor_phone', 'Hello {supervisor}, we will pay {cost} for the supervision on {date}. Please send your invoice to {company}.'),
 M('sm_behind', 'Clinician: supervision behind', 'supmonth', 'supmonth.clinician_phone', 'Hello {clinician}, after {client_sessions} sessions in the month you are {hours_debt} supervision hours behind. Please book more supervision. {company}'),
 M('cy_cost', 'Clinician: continuing education spend', 'ceyear', 'ceyear.clinician_phone', 'Hello {clinician}, your continuing education spend for {year} is {cost} for {hours} certified hours. {company}'),
 M('ce_cert', 'Clinician: send the certificate', 'celog', 'celog.clinician_phone', 'Hello {clinician}, please send the certificate for your course {title} on {date} so the hours count. {company}'),
 M('rn_on', 'Holder: your renewal date', 'renewals', 'renewals.holder_phone', 'Hello {holder}, your {item} renews on {due_date}. Please send the new certificate when you have it. {company}'),
 M('rn_over', 'Holder: renewal overdue', 'renewals', 'renewals.holder_phone', 'Hello {holder}, your {item} was due on {due_date} and is not renewed. Please renew it and send us the certificate today. {company}'),
 M('rn_coord', 'Coordinator: renewal inside 45 days', 'renewals', 'renewals.coordinator_phone', 'Hello, the {item} of {holder} is due on {due_date} and is not renewed. Please check it is in hand. {company}'),
 M('rn_own', 'Owner: renewal about to be missed', 'renewals', 'renewals.owner_phone', 'Hello, the {item} of {holder} is {days_to_due} days from its due date and not renewed. Please step in. {company}'),
 M('cn_clin', 'Clinician: consent review due', 'consent', 'consent.clinician_phone', 'Hello {clinician}, the consent of {client} is due for review on {next_review}. Please review it at the next session. {company}'),
 M('cn_client', 'Client: sign the updated consent', 'consent', 'consent.phone', 'Hello {client}, please read and sign your updated consent form with {clinician} at your next session. {company}'),
 M('rq_coord', 'Coordinator: record request deadline', 'requests', 'requests.coordinator_phone', 'Hello, the {kind} request from {client} is due on {due_date}. Please send it before then. {company}'),
 M('rq_client', 'Client: request received', 'requests', 'requests.phone', 'Hello {client}, we received your request on {date} and will reply by {due_date}. {company}'),
 M('kp_arch', 'Coordinator: file to archive', 'keep', 'keep.coordinator_phone', 'Hello, the file of {client} is due to be archived on {archive_on} and kept until {keep_until}. Please move it. {company}'),
 M('pv_coord', 'Coordinator: privacy check incomplete', 'privacy', 'privacy.coordinator_phone', 'Hello, the privacy check for {month} is not complete. Please finish the missing steps this week. {company}'),
 M('pv_it', 'IT contact: devices check', 'privacy', 'privacy.it_phone', 'Hello, please check the devices and backups for the {month} privacy check, done by {done_by}. {company}'),
 M('po_rev', 'Coordinator: policy review', 'policies', 'policies.coordinator_phone', 'Hello, the policy {policy} is due for review on {next_review}. Please book the review. {company}'),
 M('in_own', 'Owner: incident still open', 'incidents', 'incidents.owner_phone', 'Hello, incident {incident_id} ({kind}, opened {date}) has been open {days_open} days. Please decide the next step. {company}'),
 M('mo_own', 'Owner: notes report for a month', 'months', 'months.owner_phone', 'Hello, for {month} {clinician} had {late} late and {missing} missing notes. Please follow up. {company}'),
 M('wk_own', 'Owner: late notes in a week', 'weeks', 'weeks.owner_phone', 'Hello, {clinician} had {notes_late} late notes out of {notes_due} in the week of {week}. Please follow up. {company}'),
]
assert len(messages) == 34, len(messages)
_need = {}
for m in messages: _need.setdefault(m['table'], set())
for t in tables:
    if t['key'] in _need and not any(c['key'] == 'company' for c in t['columns']):
        t['columns'].append(CALC('company', 'Practice name', 'text', '{set:company}&""', 12))

TODAY_N = '{today}'
def NOTE_RATE(rng): return 'IFERROR(COUNTIFS({range:notes.note_check},%s,%s)/COUNTIFS(%s,{range:notes.note_check},"<>"&%s),0)' % (ck('On time'), W('notes.date', 30), W('notes.date', 30), ck('Due soon'))
CHSUM = '(COUNTIFS({range:change.band},%s)+COUNTIFS({range:change.band},%s)+COUNTIFS({range:change.band},%s))' % (ck('Improved'), ck('No change'), ck('Review the plan'))
kpis = [
 KPI('Overdue session notes', 'COUNTIFS({range:notes.note_check},%s)' % ck('Overdue'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Notes due soon, still inside the rule', 'COUNTIFS({range:notes.note_check},%s)' % ck('Due soon'), 'int'),
 KPI('Notes done within the rule, last 30 days', NOTE_RATE(1), 'pct', alert={"when": "< {set:note_target_rate}", "style": "warn"}),
 KPI('Notes done within 24 hours, last 30 days', 'IFERROR(COUNTIFS({range:notes.days_to_note},"<=1",%s)/COUNTIFS({range:notes.days_to_note},">=0",%s),0)' % (W('notes.date', 30), W('notes.date', 30)), 'pct'),
 KPI('Days to finish a note, last 30 days', 'IFERROR(AVERAGEIFS({range:notes.days_to_note},%s),0)' % W('notes.date', 30), 'num', alert={"when": "> {set:note_due_days}", "style": "warn"}),
 KPI('Late notes, last 30 days', 'COUNTIFS({range:notes.note_check},%s,%s)' % (ck('Late'), W('notes.date', 30)), 'int'),
 KPI('Plan reviews overdue', 'COUNTIFS({range:reviews.status},%s)' % ck('Overdue'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Plan reviews due in the next 14 days', 'COUNTIFS({range:reviews.status},"<>"&%s,{range:reviews.status},"<>"&%s,{range:reviews.due_date},">="&{today},{range:reviews.due_date},"<="&({today}+14))' % (ck('Done on time'), ck('Done late')), 'int'),
 KPI('Privacy checks complete, last 12 months', 'IFERROR(COUNTIFS({range:privacy.all_done},%s,{range:privacy.month},">"&EDATE({today},-12))/COUNTIFS({range:privacy.month},">"&EDATE({today},-12)),0)' % ck('All done'), 'pct', alert={"when": "< 1", "style": "warn"}),
 KPI('Reviews on time, last 12 months', 'IFERROR(COUNTIFS({range:reviews.status},%s,{range:reviews.due_date},">="&({today}-365))/(COUNTIFS({range:reviews.status},%s,{range:reviews.due_date},">="&({today}-365))+COUNTIFS({range:reviews.status},%s,{range:reviews.due_date},">="&({today}-365))),0)' % (ck('Done on time'), ck('Done on time'), ck('Done late')), 'pct'),
 KPI('Average outcome change, points', 'IFERROR(AVERAGE({range:change.change}),0)', 'num'),
 KPI('Clients improved by the minimum change', 'IFERROR(COUNTIFS({range:change.band},%s)/%s,0)' % (ck('Improved'), CHSUM), 'pct'),
 KPI('Clients with no intake score', 'COUNTIFS({range:change.band},%s)' % ck('Missing intake score'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Active clients to book a review', 'COUNTIFS({range:clients.score_check},%s)' % ck('Book review'), 'int'),
 KPI('Outcome scores recorded, last 30 days', 'COUNTIFS(%s)' % W('scores.date', 30), 'int'),
 KPI('Closing letters not sent, last 90 days', 'COUNTIFS({range:discharges.letter_check},%s,%s)' % (ck('Not sent'), W('discharges.date', 90)), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Discharges, last 90 days', 'COUNTIFS(%s)' % W('discharges.date', 90), 'int'),
 KPI('Supervision hours ahead or behind', 'SUM({range:team.hours_logged})-SUM({range:team.hours_owed})', 'num', alert={"when": "< 0", "style": "bad"}),
 KPI('Supervision hours logged, last 12 months', 'SUMIFS({range:suplog.hours},{range:suplog.date},">="&({today}-364))', 'num'),
 KPI('Supervision cost, last 12 months', 'SUMIFS({range:suplog.cost},{range:suplog.date},">="&({today}-364))', 'money'),
 KPI('Certified CE hours, this year', 'SUMIFS({range:celog.counted_hours},{range:celog.date},">="&%s)' % JAN1, 'num'),
 KPI('Clinicians short of the CE target', 'COUNTIFS({range:team.hours_needed},">0")', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Continuing education cost, this year', 'SUMIFS({range:celog.cost},{range:celog.date},">="&%s)' % JAN1, 'money'),
 KPI('Renewals due in 90 days, not done', 'COUNTIFS({range:renewals.status},"<>"&%s,{range:renewals.due_date},">="&{today},{range:renewals.due_date},"<="&({today}+90))' % ck('Renewed'), 'int'),
 KPI('Renewals red or overdue', 'COUNTIFS({range:renewals.status},%s)+COUNTIFS({range:renewals.status},%s)' % (ck('Red'), ck('Overdue')), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Renewal cost next 12 months, practice', 'SUMIFS({range:renewals.cost},{range:renewals.status},"<>"&{list:cka.renewed},{range:renewals.paid_by},%s,{range:renewals.due_date},">="&{today},{range:renewals.due_date},"<"&EDATE({today},12))' % tok('paidby', 'Practice'), 'money'),
 KPI('Consent reviews due now', 'COUNTIFS({range:consent.review_check},%s)' % ck('Review due'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Record requests open', 'COUNTIFS({range:requests.status},%s)+COUNTIFS({range:requests.status},%s)+COUNTIFS({range:requests.status},%s)' % (ck('Overdue'), ck('Due soon'), ck('On time')), 'int'),
 KPI('Files to archive now', 'COUNTIFS({range:keep.status},%s)' % ck('Archive now'), 'int'),
 KPI('Incidents and complaints open', 'COUNTIFS({range:incidents.status},%s)' % ck('Open'), 'int', alert={"when": "> 0", "style": "warn"}),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Clinical Admin KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Notes on time, late and missing per month", "date": "months.month", "series": [
   {"label": "On time", "sum": "months.on_time", "date": "months.month"}, {"label": "Late", "sum": "months.late", "date": "months.month"},
   {"label": "Missing", "sum": "months.missing", "date": "months.month"}, {"label": "Plan reviews done", "sum": "months.reviews_done", "date": "months.month"}]},
 "breakdowns": [{"title": "Session notes by clinician", "by": "notes.clinician", "agg": "count"}, {"title": "Discharges by reason", "by": "discharges.reason", "agg": "count"},
                {"title": "Renewals by item", "by": "renewals.item", "agg": "count"}, {"title": "Incidents by kind", "by": "incidents.kind", "agg": "count"}]}
insights = {"filters": [{"label": "Clinician", "list": "clin"}, {"label": "Service", "list": "svc"}, {"label": "Client status", "list": "cstatus"}],
 "gauges": [
  {"title": "Notes done within the rule", "num": AGG('count', 'notes', where=[('note_check', '=', ck('On time'))]), "den": AGG('count', 'notes', where=[('note_check', '<>', ck('Due soon')), ('date', '>', 0)])},
  {"title": "Plan reviews done on time", "num": AGG('count', 'reviews', where=[('status', '=', ck('Done on time'))]), "den": AGG('count', 'reviews', where=[('reviewed_on', '>', 0)])},
  {"title": "Clients with an intake score", "num": AGG('count', 'change', where=[('intake_score', '>', 0)]), "den": AGG('count', 'change')},
  {"title": "Privacy checks complete", "num": AGG('count', 'privacy', where=[('all_done', '=', ck('All done'))]), "den": AGG('count', 'privacy')},
  {"title": "Clinician years on CE pace", "num": AGG('count', 'ceyear', where=[('pace_flag', '=', ck('On pace'))]), "den": AGG('count', 'ceyear')},
  {"title": "Renewals done of those due or done", "num": AGG('count', 'renewals', where=[('status', '=', ck('Renewed'))]), "den": AGG('count', 'renewals', where=[('status', '<>', ck('OK'))])}],
 "charts": [
  CHART('Late notes per month', 'column', 'month', [AGG('sum', 'months', 'months.late', date='months.month', label='Late notes')]),
  CHART('Missing notes per month', 'column', 'month', [AGG('sum', 'months', 'months.missing', date='months.month', label='Missing notes')]),
  CHART('Session notes by clinician', 'bar', 'notes.clinician', [AGG('count', 'notes', label='Notes')]),
  CHART('Late notes by clinician', 'bar', 'months.clinician', [AGG('sum', 'months', 'months.late', label='Late notes')]),
  CHART('Late notes per week', 'column', 'weeks.wk', [AGG('sum', 'weeks', 'weeks.notes_late', label='Late notes')]),
  CHART('Plan reviews by clinician', 'bar', 'reviews.clinician', [AGG('count', 'reviews', label='Reviews')]),
  CHART('Plan reviews done per month', 'column', 'month', [AGG('count', 'reviews', date='reviews.reviewed_on', label='Reviews done')]),
  CHART('Outcome scores per month', 'column', 'month', [AGG('count', 'scores', date='scores.date', label='Scores')]),
  CHART('Outcome scores by point', 'bar', 'scores.point', [AGG('count', 'scores', label='Scores')]),
  CHART('Average score change by service', 'bar', 'change.service', [AGG('avg', 'change', 'change.change', label='Points')]),
  CHART('Clients by status', 'bar', 'clients.status', [AGG('count', 'clients', label='Clients')]),
  CHART('Discharges by reason', 'bar', 'discharges.reason', [AGG('count', 'discharges', label='Discharges')]),
  CHART('Supervision hours per month', 'column', 'month', [AGG('sum', 'suplog', 'suplog.hours', date='suplog.date', label='Hours')]),
  CHART('Supervision cost per month', 'column', 'month', [AGG('sum', 'suplog', 'suplog.cost', date='suplog.date', label='Cost')]),
  CHART('Supervision hours by kind', 'bar', 'suplog.kind', [AGG('sum', 'suplog', 'suplog.hours', label='Hours')]),
  CHART('Continuing education hours per month', 'column', 'month', [AGG('sum', 'celog', 'celog.counted_hours', date='celog.date', label='Hours')]),
  CHART('Continuing education cost by course kind', 'bar', 'celog.kind', [AGG('sum', 'celog', 'celog.cost', label='Cost')]),
  CHART('Continuing education hours still needed by clinician', 'bar', 'ceyear.clinician', [AGG('sum', 'ceyear', 'ceyear.hours_needed', label='Hours needed')]),
  CHART('Renewals by item', 'bar', 'renewals.item', [AGG('count', 'renewals', label='Renewals')]),
  CHART('Renewal cost by holder', 'bar', 'renewals.holder', [AGG('sum', 'renewals', 'renewals.cost', label='Cost')]),
  CHART('Record requests by kind', 'bar', 'requests.kind', [AGG('count', 'requests', label='Requests')]),
  CHART('Incidents and complaints by kind', 'bar', 'incidents.kind', [AGG('count', 'incidents', label='Incidents')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Session note timeliness by clinician", "why": "every session shows days to the note against the rule and the overdue notes are counted per clinician", "where": "Note Status"},
 {"name": "Late notes act-first list", "why": "the team table ranks who owes the most overdue notes so you know who to call first", "where": "Late Notes by Clinician"},
 {"name": "Overdue notes catch-up with scenarios", "why": "base, best and worst case give the working days and the extra admin minutes needed to clear the backlog", "where": "Overdue Notes Catch-up"},
 {"name": "Plan review tracker", "why": "each treatment-plan review shows days overdue and status, with a backlog planner for the weekly hours needed", "where": "Plan Reviews"},
 {"name": "Outcome change by client", "why": "intake against latest score, the change in points and a band that flags clients who did not improve", "where": "Score Change by Client"},
 {"name": "Supervision hours owed", "why": "client sessions divided by your ratio against hours logged gives the hours ahead or behind for the associate", "where": "Supervision by Month"},
 {"name": "Continuing education pace", "why": "hours with a certificate against the yearly target, the hours still needed and the cost per hour", "where": "CE by Year"},
 {"name": "Renewal register with act-first rank", "why": "liability insurance, licences and certificates ranked by due date with amber and red alerts", "where": "Renewal Register"},
 {"name": "Renewal cost planner", "why": "twelve monthly amounts the practice must pay and a monthly sum to set aside", "where": "Renewal Cost Planner"},
 {"name": "Records keep-until dates", "why": "archive date and keep-until date for every discharged client from your own retention years", "where": "Records Keep-until"},
 {"name": "Consent, requests and privacy checks", "why": "consent review dates, record request deadlines and monthly privacy checks in one place", "where": "Consent Records"}]
competitors = [
 {"what": "free compliance checklists", "lacks": "list what to do but never count overdue notes, supervision hours owed or renewals due"},
 {"what": "subscription practice-management software", "lacks": "charge per clinician and keep your data in their system, with no editable supervision ratio or renewal planner"},
 {"what": "single-sheet supervision logs", "lacks": "record hours only, so the hours owed, the cost and the continuing education pace are never worked out"},
 {"what": "calendar reminders and sticky notes", "lacks": "remind you of a date but show no rank of what to act on first, no cost and no history"}]
guide = [
 'Open Start and type your practice name and your rules in the yellow cells: days to finish a note (2 is the default), supervision ratio, continuing education hours a year, renewal alert days and months between consent reviews.',
 'Check Team first. The associate (works under supervision) is flagged there, and each member has a phone number for the ready messages.',
 'Log every session on Note Status and fill the note-done date when the note is finished. Overdue notes are counted by clinician and the team table ranks who to call first.',
 'Record treatment-plan reviews on Plan Reviews and outcome scores on Outcome Scores. Score Change by Client compares the intake score with the latest score.',
 'Record each discharge on Discharges with its closing letter and referral letter. Records Keep-until shows the archive date and the keep-until date from the years you enter.',
 'Log supervision on Supervision Log and the monthly sessions on Supervision by Month. The hours owed are client sessions divided by your ratio.',
 'Log courses on Continuing Education Log. Only hours with a certificate count towards the yearly target; check your own local rules.',
 'Keep the Renewal Register current: insurance, licences and certificates. Amber and red alerts and the act-first rank show what to renew first.',
 'Use Consent Records, Record Requests, Privacy Checks, Policy Reviews and the Incident and Complaint Log for the rest of your admin duties. The workbook holds dates and status only, never case content.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Read the Clinical Admin KPI Dashboard and Charts every week: notes on time, overdue reviews, supervision hours, continuing education and renewals.']
listing = {"title": "Therapy Practice Clinical Admin Excel Template: Session Notes, Supervision Hours, CE Tracker, Renewal Register, KPI Dashboard",
 "headline": "Keep notes, supervision, CE and renewals on track in one Excel file",
 "tags": ["therapy practice", "supervision log", "ce tracker", "renewal register", "session notes", "counselling practice", "practice management", "excel template", "private practice", "compliance tracker", "outcome tracking", "group practice", "records retention"],
 "description": ("Run the clinical admin of a small group practice in one Excel workbook. Built for talking therapists and counsellors: an owner-clinician, employed clinicians, contract (self-employed) clinicians, an associate who works under supervision and a practice coordinator.\n\n"
  "Note Status checks every session note against your rule (2 days by default) and ranks which clinician to call first about overdue notes. Plan Reviews tracks treatment-plan reviews with days overdue, and Score Change by Client compares each intake outcome score with the latest to show who improved. "
  "Discharges, Records Keep-until, Consent Records, Record Requests, Privacy Checks, Policy Reviews and the Incident and Complaint Log cover the rest of the duty of care in admin terms. "
  "Supervision Log and Supervision by Month work out the hours owed to an associate from your sessions-per-hour ratio, with cost. CE Log and CE by Year count only certified hours against your yearly target. The Renewal Register ranks insurance, licences and certificates with amber and red alerts and a twelve-month cost planner.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: overdue notes catch-up, review backlog planner, supervision hours owed, continuing education pace and budget, renewal alert and cost, records keep-until date and more. "
  f"Print {len(forms)} sheets and {len(documents)} letters and reports, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
  "This is part six of the Therapy Private Practice suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-clinician fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. The workbook holds dates and status only, never session notes or diagnoses, and it does not promise results."),
 "features": ["Session note timeliness with act-first clinician list", "Treatment-plan reviews with backlog planner", "Outcome score change by client", "Supervision hours owed to the associate", "Continuing education pace and budget",
              "Renewal register with amber and red alerts", "Records keep-until and consent review dates", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
              f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
s = _lib.spec(id=f'{SUITE}-p6', slug='therapy-practice-admin', profession='Therapy Private Practice', name='Clinical Admin and Renewals',
         tagline='Keep notes, supervision and renewals on track', price_usd=29, colors={"primary": "#2F5D62", "accent": "#A7C4BC"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Clinical admin, supervision and renewals"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'th6.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
