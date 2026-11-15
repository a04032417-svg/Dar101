"""Therapy private practice suite - part 4: Third-party Payer Billing and Claims."""
import sys, os, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from th4_lists import *
from th4_tables import settings, tables, CA, STAFF_PH
from th4_tools import tools

SUITE = 'fx-20261115-therapy-practice'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
TB = {t['key']: t for t in tables}
SKIP = {'client_phone', 'coordinator_phone', 'clinician_phone', 'owner_phone', 'accountant_phone', 'phone', 'company', 'chase_score', 'chase_rank'}
def FM(key_, sheet, title, tb, pick, cols=None, skip=()):
    t = TB[tb]
    ks = cols or [c['key'] for c in t['columns'] if c['key'] not in SKIP and c['key'] not in skip]
    ks = ks[:20]
    lab = {c['key']: c['label'] for c in t['columns']}
    return FORM(key_, sheet, title, '%s.%s' % (tb, pick), [FV(lab[k][:40], '%s.%s' % (tb, k)) for k in ks])

forms = [
 FM('claim_sheet', 'Claim Sheet', 'Claim with status, days to payment and age band', 'claims', 'claim_id',
    ['claim_id', 'session_id', 'date', 'client', 'payer', 'service', 'clinician', 'amount', 'submitted_on', 'status', 'denial_reason', 'denied_on', 'resubmitted_on', 'paid_on', 'paid_amount', 'days_to_submit', 'days_to_pay', 'clean_flag']),
 FM('check_sheet', 'Pre-submission Check Sheet', 'Pre-submission check with ready result', 'checks', 'check_id'),
 FM('approval_sheet', 'Approval Record Sheet', 'Approval record with sessions left', 'approvals', 'approval_id'),
 FM('denial_sheet', 'Denial Fix Sheet', 'Denial fix and resubmission', 'denials', 'denial_id'),
 FM('benefit_sheet', 'Benefits Check Sheet', 'Benefits check before the first session', 'benefits', 'check_id'),
 FM('followup_sheet', 'Claim Follow-up Sheet', 'Claim follow-up with the payer answer', 'followups', 'followup_id'),
 FM('enrol_sheet', 'Payer Enrolment Sheet', 'Payer enrolment of a clinician', 'enrol', 'enrolment_id'),
 FM('writeoff_sheet', 'Claim Write-off Sheet', 'Claim write-off with approval', 'writeoffs', 'writeoff_id'),
 FM('remit_sheet', 'Remittance Check Sheet', 'Remittance check against claims', 'remits', 'remit_id'),
 FM('estimate_sheet', 'Self-pay Estimate Sheet', 'Self-pay cost estimate', 'estimates', 'estimate_id'),
 FM('receipt_sheet', 'Claim Back Receipt Sheet', 'Receipt for claim back', 'receipts', 'receipt_id'),
 FM('payclient_sheet', 'Payer Client Sheet', 'Payer client record', 'clients', 'client_id'),
]
assert len(forms) == 12

def D_(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('claim_doc', 'Claim Summary', 'Claim summary for a session', 'claims.claim_id', [
  'Claim summary of {set:company}, dated {today}. Claim {col:claims.claim_id}.',
  'Client: {col:claims.client} (client {col:claims.client_id}). Payer: {col:claims.payer}. Service: {col:claims.service}. Clinician: {col:claims.clinician}.',
  'Session date: {col:claims.date}. Session ID: {col:claims.session_id}. Claim amount: {col:claims.amount}. Submitted on: {col:claims.submitted_on}, {col:claims.days_to_submit} days after the session.',
  'Status: {col:claims.status}. Age band: {col:claims.age_band} days. Paid amount: {col:claims.paid_amount}.',
  'Add any payer reference or identifier your payer asks for before you send this summary.'], ['Billing coordinator']),
 D_('superbill_doc', 'Receipt for Claim Back', 'Receipt for claim back (superbill)', 'receipts.receipt_id', [
  'Receipt for claim back from {set:company}, dated {today}. Receipt {col:receipts.receipt_id}.',
  'Client: {col:receipts.client} (client {col:receipts.client_id}). Period: {col:receipts.month}. Issued on {col:receipts.issued_on}.',
  'Sessions on this receipt: {col:receipts.sessions}. Total paid by the client: {col:receipts.amount_paid}. Average per session: {col:receipts.per_session}.',
  'This receipt confirms that the client paid the amount above in full. The client may send it to their own payer to claim back part of the cost.',
  'Add the clinician name, the registration details and the practice address that your payer asks for, and the date of each session, before you issue it.'], ['Billing coordinator']),
 D_('approval_doc', 'Approval Request Letter', 'Approval request letter to a payer', 'approvals.approval_id', [
  'Approval request from {set:company}, dated {today}. To {col:approvals.payer}.',
  'Client: {col:approvals.client} (client {col:approvals.client_id}). Clinician: {col:approvals.clinician}.',
  'Current approval {col:approvals.approval_id}: {col:approvals.sessions_approved} sessions approved on {col:approvals.approved_on}, valid until {col:approvals.valid_until}. Sessions used: {col:approvals.sessions_used}. Sessions left: {col:approvals.sessions_left}.',
  'We ask you to approve further sessions so that care can continue without a break. Please tell us what information you need and how long a decision takes.',
  'This is generic wording. Adapt it to the form and the steps your payer asks for.'], ['Billing coordinator']),
 D_('denial_doc', 'Denial Review Letter', 'Denial review letter to a payer', 'denials.denial_id', [
  'Denial review request from {set:company}, dated {today}. To {col:denials.payer}.',
  'Claim {col:denials.claim_id} for {col:denials.client}, amount {col:denials.amount}, was turned down on {col:denials.denied_on}. Reason given: {col:denials.reason}.',
  'We have checked the claim and ask you to review the decision. Usual fix for this reason: {col:denials.fix_needed}.',
  'Please reply within {set:claim_chase_days} days. Our resubmit-by date for this claim is {col:denials.resubmit_by}.',
  'This is generic wording. Adapt it to the review steps your payer uses.'], ['Billing coordinator']),
 D_('resub_doc', 'Resubmission Cover Note', 'Resubmission cover note', 'denials.denial_id', [
  'Resubmission cover note from {set:company}, dated {today}. To {col:denials.payer}.',
  'We send claim {col:denials.claim_id} again. It was turned down on {col:denials.denied_on} for the reason: {col:denials.reason}.',
  'What we changed: {col:denials.fix_needed}. The fix was finished on {col:denials.fixed_on} and the claim is sent again on {col:denials.resubmitted_on}.',
  'Client: {col:denials.client}. Amount: {col:denials.amount}. Please confirm that you have received it.'], ['Billing coordinator']),
 D_('followup_doc', 'Claim Follow-up Letter', 'Claim follow-up letter to a payer', 'followups.followup_id', [
  'Claim follow-up from {set:company}, dated {today}. To {col:followups.payer}.',
  'Claim {col:followups.claim_id} for {col:followups.client} was submitted {col:followups.days_since} days ago and is still open.',
  'We last contacted you on {col:followups.chased_on} by {col:followups.method}. Your answer was: {col:followups.answer}.',
  'Please tell us the status of this claim and when we can expect payment. We will contact you again on {col:followups.next_step_date}.'], ['Billing coordinator']),
 D_('partial_doc', 'Partial Payment Query', 'Partial payment query letter', 'claims.claim_id', [
  'Partial payment query from {set:company}, dated {today}. To {col:claims.payer}.',
  'Claim {col:claims.claim_id} for {col:claims.client}, session of {col:claims.date}, was claimed at {col:claims.amount} and paid at {col:claims.paid_amount} on {col:claims.paid_on}.',
  'We ask you to explain the difference and to tell us whether the balance is the client co-pay (the part of the fee the client still pays) or an amount you reduced.',
  'If the claim was reduced in error, please pay the balance. We will send further details on request.'], ['Billing coordinator']),
 D_('estimate_doc', 'Written Cost Estimate', 'Written cost estimate for a self-pay client', 'estimates.estimate_id', [
  'Written cost estimate from {set:company}, dated {today}. Estimate {col:estimates.estimate_id}, issued on {col:estimates.issued_on}.',
  'Client: {col:estimates.client} (client {col:estimates.client_id}). Service: {col:estimates.service}.',
  'Fee per session: {col:estimates.fee}. Sliding scale share (a lower fee agreed from the client\'s means): {col:estimates.sliding_pct}. Expected sessions: {col:estimates.expected_sessions}. Package option: {col:estimates.package}, discount {col:estimates.discount}.',
  'Deposit: {col:estimates.deposit}. Late-cancel rule: {col:estimates.late_rule}. Expected total cost: {col:estimates.expected_total}. The estimate is not a promise: the final cost depends on the sessions you attend.'], ['Practice team']),
 D_('howto_doc', 'How Payer Billing Works', 'How payer billing works at the practice', 'payers.payer', [
  'How payer billing works at {set:company}, dated {today}.',
  'A third-party payer is an organisation that pays part of a client\'s fee. This sheet is for clients whose sessions are billed to {col:payers.payer}.',
  'The payer allows {col:payers.fee_share} of our list fee. You pay the co-pay (the part of the fee you still pay): {col:payers.copay} per session.',
  'We submit a claim within {set:claim_submit_days} days of each session. If the payer turns down a claim, we fix it and send it again. If the payer will not pay, we tell you before any balance is due.',
  'Please give us your membership details and any approval from the payer before the first session. If the payer limit is reached, the self-pay fee applies.',
  'Late cancel: a cancellation with less than {set:late_cancel_hours} hours\' notice. The payer may not pay for it, so the late-cancel charge can fall to you.'], ['Practice team']),
 D_('monthly_doc', 'Monthly Claims Report', 'Monthly claims report with A/R aging', 'monthly.month', [
  'Monthly claims report of {set:company}, dated {today}. Month: {col:monthly.month}.',
  'Attended sessions: {col:monthly.attended_sessions}. Claimable sessions (payer sessions): {col:monthly.claimable_sessions}. Claims submitted: {col:monthly.claims_submitted}. Clean claims (accepted first time): {col:monthly.clean_claims}. Clean Claim Rate: {col:monthly.clean_rate}.',
  'Amount claimed: {col:monthly.claimed}. Payer money received: {col:monthly.paid}. Average days to payment: {col:monthly.avg_days_to_pay}. Short-paid amount: {col:monthly.short_paid}. Written off: {col:monthly.written_off}.',
  'Open claims at month end: {col:monthly.open_at_end}. Receipts for claim back issued: {col:monthly.receipts}. Payer share of sessions: {col:monthly.payer_share}.',
  'For A/R aging by payer and age band (0-30, 31-60, 61-90 and 90+ days), see the AR Aging by Payer sheet for the same month.'], ['Owner']),
 D_('writeoff_doc', 'Claim Write-off Report', 'Claim write-off report', 'writeoffs.writeoff_id', [
  'Claim write-off report of {set:company}, dated {today}. Write-off {col:writeoffs.writeoff_id}.',
  'Claim {col:writeoffs.claim_id} for {col:writeoffs.client}, payer {col:writeoffs.payer}. Written off on {col:writeoffs.date} after {col:writeoffs.days_open} days open.',
  'Amount written off: {col:writeoffs.amount}. Reason: {col:writeoffs.reason}. Approved by: {col:writeoffs.approved_by}.',
  'Check your own local rules on how long a claim must stay open and how to record a write-off.'], ['Owner']),
 D_('remit_doc', 'Remittance Report', 'Remittance reconciliation report', 'remits.remit_id', [
  'Remittance reconciliation report of {set:company}, dated {today}. Remittance {col:remits.remit_id}.',
  'Payer: {col:remits.payer}. Date: {col:remits.date}. Claims paid: {col:remits.claims_paid}. Average per claim: {col:remits.avg_claim}.',
  'Amount received: {col:remits.amount}. Matched to claims: {col:remits.matched_amount}. Difference: {col:remits.difference}. Check: {col:remits.match_flag}.',
  'If the difference is not zero, list the claims that are missing or extra and ask the payer to explain.'], ['Billing coordinator']),
]
assert len(documents) == 12

def CS(key_, title, table, start, steps): return _lib.CHK(key_, title, table, start, steps)
checklists = [
 CS('c_newclient', 'New Payer Client Set-up', 'clients', 'clients.first_session', [('Collect the payer membership details', -14), ('Run the benefits check', -10), ('Record the session limit and any pre-approval need', -10), ('Ask for a pre-approval if it is needed', -9), ('Tell the client the co-pay', -7), ('Add the approval to Approvals', -5), ('Agree the self-pay fee as a fallback', -3), ('Send the intake forms', -2), ('Record the client in Payer Clients', 0)]),
 CS('c_enrol', 'Payer Enrolment, New Clinician', 'enrol', 'enrol.application_sent', [('Collect the clinician registration details', 0), ('Complete the payer application', 0), ('Send the application and record the date', 0), ('Chase the payer after the usual weeks', 49), ('Confirm the effective date in writing', 77), ('Bill only from the effective date', 77), ('Set the renewal reminder', 80)]),
 CS('c_daily', 'Daily Claim Submission', 'sessions', 'sessions.date', [('List the attended payer sessions', 0), ('Run the pre-submission check', 1), ('Submit the claims', 2), ('Record the submission date', 2), ('Check Unsubmitted Sessions for older sessions', 5)]),
 CS('c_presub', 'Pre-submission Check', 'checks', 'checks.checked_on', [('Check the client details', 0), ('Check the session details', 0), ('Check the approval is valid', 0), ('Fix anything missing', 1), ('Record the check result', 1), ('Submit the claim', 2)]),
 CS('c_weekly', 'Weekly Claims Follow-up', 'followups', 'followups.chased_on', [('Open Chase-first Claims', 0), ('Contact the payer about the top claims', 0), ('Record the payer answer', 0), ('Set the next step date', 0), ('Tell the owner about claims over 60 days', 2), ('Repeat on the next step date', 7)]),
 CS('c_denial', 'Denial Handling', 'denials', 'denials.denied_on', [('Record the denial reason', 0), ('Find the usual fix', 1), ('Ask for the missing details', 2), ('Record the fix date', 5), ('Resubmit before the resubmit-by date', 7), ('Ask the owner to approve a write-off if it cannot be fixed', 90)]),
 CS('c_resub', 'Resubmission', 'denials', 'denials.resubmitted_on', [('Check the fix is complete', 0), ('Send the claim again with a cover note', 0), ('Record the resubmission date', 0), ('Chase the payer after the chase days', 30), ('Record the payment or the next denial', 35)]),
 CS('c_benefits', 'Benefits Check First Session', 'benefits', 'benefits.first_session', [('Ask the payer for the session limit', -7), ('Ask whether a pre-approval is needed', -7), ('Record the client share per session', -7), ('Tell the client the co-pay', -5), ('Offer the self-pay fee if the sessions are not covered', -5), ('Record the check before the first session', -1)]),
 CS('c_remit', 'Remittance Reconciliation', 'remits', 'remits.date', [('Record the remittance amount', 0), ('Match each paid claim', 1), ('Update the status and paid amount of each claim', 1), ('Check the difference', 2), ('Query a short payment', 3), ('Record the reason for any amount left unmatched', 5)]),
 CS('c_renew', 'Approval Renewal Before Expiry', 'approvals', 'approvals.valid_until', [('Check sessions left on Approvals', -45), ('Ask the clinician if the plan continues', -40), ('Send the renewal request', -35), ('Tell the client', -30), ('Chase the payer', -14), ('Record the new approval', -7), ('Switch to the self-pay fee if it is not renewed', 0)]),
 CS('c_month', 'Month-end Claims Close', 'monthly', 'monthly.month', [('Check Unsubmitted Sessions', 28), ('Match all remittances', 30), ('Update the Monthly Claims Summary', 31), ('Review A/R aging by payer', 31), ('Review write-offs with the owner', 33), ('Send the figures to the accountant', 34)]),
 CS('c_receipt', 'Receipt for Claim Back Issue', 'receipts', 'receipts.issued_on', [('Check the client paid in full', -1), ('Check the sessions and dates', -1), ('Check the practice and clinician details', 0), ('Issue the receipt', 0), ('Record it in Receipts for Claim Back', 0), ('Send it to the client', 1)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('c_details', 'Client: send your payer details', 'clients', 'clients.phone', 'Hello {client}, please send your payer membership details to {company} before your first session on {first_session}. We need them to submit your claims.'),
 M('c_runout', 'Client: your approval runs out soon', 'approvals', 'approvals.client_phone', 'Hello {client}, your approval from {payer} covers {sessions_left} more sessions and is valid until {valid_until}. We will ask for a renewal before it runs out. {company}'),
 M('c_preapp', 'Client: please ask for a pre-approval', 'benefits', 'benefits.phone', 'Hello {client}, {payer} needs a pre-approval before your sessions of {service}. Please ask {payer} to approve them and tell us the answer. {company}'),
 M('c_renewed', 'Client: your approval was renewed', 'approvals', 'approvals.client_phone', 'Hello {client}, your approval from {payer} was renewed on {approved_on}. It covers {sessions_approved} sessions and is valid until {valid_until}. {company}'),
 M('c_copay', 'Client: your co-pay per session', 'sessions', 'sessions.client_phone', 'Hello {client}, your co-pay (the part of the fee you still pay) for the session on {date} is {client_amount}. {company}'),
 M('c_benefits', 'Client: your benefits check result', 'benefits', 'benefits.phone', 'Hello {client}, your benefits check shows {session_limit} sessions with {payer} and a client share of {client_share} per session. If you prefer, the self-pay fee is {self_pay_fee} per session. {company}'),
 M('c_partpaid', 'Client: your payer paid part of a claim', 'claims', 'claims.client_phone', 'Hello {client}, {payer} paid {paid_amount} of the {amount} claimed for your session on {date}. We will tell you if any balance is due. {company}'),
 M('c_denied', 'Client: we need details for a claim', 'denials', 'denials.client_phone', 'Hello {client}, {payer} turned down a claim on {denied_on} (reason: {reason}). To fix it we need: {fix_needed}. Please reply with the details. {company}'),
 M('c_resent', 'Client: we sent your claim again', 'denials', 'denials.client_phone', 'Hello {client}, we are sending your claim to {payer} again, no later than {resubmit_by}. You do not need to do anything. {company}'),
 M('c_ends', 'Client: payer billing ends', 'clients', 'clients.phone', 'Hello {client}, payer billing for your sessions ends on {approval_valid_until}. After that date the self-pay fee applies. Please contact {company} if you want to talk about your options.'),
 M('c_receipt', 'Client: your receipt for claim back', 'receipts', 'receipts.phone', 'Hello {client}, your receipt for claim back for {sessions} sessions, total {amount_paid}, is ready. You can send it to your own payer. {company}'),
 M('c_estimate', 'Client: your self-pay cost estimate', 'estimates', 'estimates.phone', 'Hello {client}, your cost estimate for {expected_sessions} self-pay sessions of {service} is ready: expected total {expected_total}, with a deposit of {deposit}. {company}'),
 M('c_clear', 'Client: your payer account is clear', 'clients', 'clients.phone', 'Hello {client}, your payer account with {company} is clear: we have no open claims for your sessions. Thank you.'),
 M('k_approval', 'Clinician: an approval is ending', 'approvals', 'approvals.clinician_phone', 'Hello {clinician}, the approval for {client} ({payer}) ends on {valid_until} with {sessions_left} sessions left. Please tell the coordinator if the plan continues. {company}'),
 M('k_details', 'Clinician: session details needed', 'unsub', 'unsub.clinician_phone', 'Hello {clinician}, the session with {client} on {date} has not been claimed for {days_since} days. Please complete the session details today. {company}'),
 M('k_turned', 'Clinician: a claim was turned down', 'claims', 'claims.clinician_phone', 'Hello {clinician}, {payer} turned down the claim for your session with {client} on {date}. Reason: {denial_reason}. Please send any missing details. {company}'),
 M('o_ready', 'Coordinator: a claim is ready to submit', 'checks', 'checks.coordinator_phone', 'Hello {coordinator_name}, claim {claim_id} for {client} ({payer}) passed its check on {checked_on}. Please submit it today. {company}'),
 M('o_chase', 'Coordinator: claim past the chase date', 'claims', 'claims.coordinator_phone', 'Hello {coordinator_name}, claim {claim_id} for {client} ({payer}, {amount}) was submitted on {submitted_on} and is open for {days_open} days. Please contact {payer}. {company}'),
 M('o_denied', 'Coordinator: a claim was denied', 'denials', 'denials.coordinator_phone', 'Hello {coordinator_name}, claim {claim_id} was denied on {denied_on} for {reason}. The usual fix: {fix_needed}. Please start the fix today. {company}'),
 M('o_resend', 'Coordinator: send a claim again', 'denials', 'denials.coordinator_phone', 'Hello {coordinator_name}, please send claim {claim_id} ({client}, {amount}) to {payer} again by {resubmit_by}. {company}'),
 M('o_remit', 'Coordinator: a remittance does not match', 'remits', 'remits.coordinator_phone', 'Hello {coordinator_name}, the remittance from {payer} dated {date} does not match: received {amount}, matched {matched_amount}, difference {difference}. Please check it. {company}'),
 M('o_unclaimed', 'Coordinator: sessions not claimed yet', 'unsub', 'unsub.coordinator_phone', 'Hello {coordinator_name}, the session of {client} on {date} ({payer_amount} from {payer}) has not been claimed for {days_since} days. Please submit it. {company}'),
 M('o_needapp', 'Coordinator: approval request needed', 'approvals', 'approvals.coordinator_phone', 'Hello {coordinator_name}, an approval request is needed for {client} ({payer}): {sessions_left} sessions left, valid until {valid_until}. {company}'),
 M('o_part', 'Coordinator: a claim was partly paid', 'claims', 'claims.coordinator_phone', 'Hello {coordinator_name}, claim {claim_id} was partly paid: {paid_amount} of {amount}. Please ask {payer} about the balance. {company}'),
 M('w_unpaid', 'Owner: claims unpaid by band', 'aging', 'aging.owner_phone', 'Hello {owner_name}, {payer} has {claims} open claims worth {amount} in the {band} day band at {as_of}. Please review them. {company}'),
 M('w_denied', 'Owner: a denied claim waits for a fix', 'denials', 'denials.owner_phone', 'Hello {owner_name}, claim {claim_id} ({payer}, {amount}) was denied on {denied_on} and must be sent again by {resubmit_by}. {company}'),
 M('w_slow', 'Owner: a payer is paying slowly', 'followups', 'followups.owner_phone', 'Hello {owner_name}, {payer} has not paid claim {claim_id} for {client}. It is open for {days_since} days and the last answer was: {answer}. {company}'),
 M('w_writeoff', 'Owner: a claim was written off', 'writeoffs', 'writeoffs.owner_phone', 'Hello {owner_name}, claim {claim_id} ({payer}, {amount}) was written off on {date}. Reason: {reason}. Please review it. {company}'),
 M('w_report', 'Owner: the monthly claims report', 'monthly', 'monthly.owner_phone', 'Hello {owner_name}, the monthly claims report for {month} is ready: {claims_submitted} claims submitted, Clean Claim Rate {clean_rate}, {paid} paid. {company}'),
 M('w_enrol', 'Owner: a clinician cannot bill yet', 'enrol', 'enrol.owner_phone', 'Hello {owner_name}, {clinician} cannot bill {payer} until {expected_effective}. The application was sent on {application_sent}. {company}'),
 M('a_remits', 'Accountant: payer money for a month', 'monthly', 'monthly.accountant_phone', 'Hello {accountant_name}, payer money received for {month} is {paid}. The amount claimed was {claimed}. {company}'),
 M('a_writeoffs', 'Accountant: claim write-offs for a month', 'monthly', 'monthly.accountant_phone', 'Hello {accountant_name}, claim write-offs for {month} are {written_off} and short payments are {short_paid}. {company}'),
 M('a_open', 'Accountant: open claims at month end', 'monthly', 'monthly.accountant_phone', 'Hello {accountant_name}, open claims at the end of {month}: {open_at_end} claims. {company}'),
 M('a_receipts', 'Accountant: claim back receipts issued', 'monthly', 'monthly.accountant_phone', 'Hello {accountant_name}, {receipts} receipts for claim back were issued in {month}. {company}'),
]
assert len(messages) == 34

# practice name, staff phone and staff name columns on every table that sends a message
STAFF = {'coordinator': 'TH-07', 'owner': 'TH-01', 'accountant': 'TH-08'}
for m in messages:
    t = TB[m['table']]
    have = {c['key'] for c in t['columns']}
    if 'company' not in have: t['columns'].append(CA('company', 'Practice', 'text', '{set:company}&""', 24)); have.add('company')
    pk = m['phone'].split('.')[1]
    who = pk.replace('_phone', '')
    if pk not in have and who in STAFF: t['columns'].append(STAFF_PH(STAFF[who], pk)); have.add(pk)
    for who, sid in STAFF.items():
        if '{%s_name}' % who in m['text'] and who + '_name' not in have:
            t['columns'].append(CA(who + '_name', 'Name to greet', 'text', 'IFERROR(INDEX({range:team.name},%d)&"","")' % int(sid[-2:]), 24)); have.add(who + '_name')
for m in messages:
    cols = {c['key'] for c in TB[m['table']]['columns']}
    for p in re.findall(r'\{(\w+)\}', m['text']): assert p in cols, (m['key'], p)
    assert m['phone'].split('.')[1] in cols, m['key']

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PMS = 'DATE(YEAR({today}),MONTH({today})-1,1)'
JAN = 'DATE(YEAR({today}),1,1)'
def DN(c, n): return '{range:%s},">="&({today}-%d),{range:%s},"<="&{today}' % (c, n - 1, c)
def D90(c): return '{range:%s},">="&({today}-90)' % c
SUBS, RESS, DENS, PAIDS = (tok('clmst', x) for x in ('Submitted', 'Resubmitted', 'Denied', 'Paid'))
def OPV(): return '(SUMIFS({range:claims.amount},{range:claims.status},%s)+SUMIFS({range:claims.amount},{range:claims.status},%s)+SUMIFS({range:claims.amount},{range:claims.status},%s))' % (SUBS, RESS, DENS)
def OPN(): return '(COUNTIFS({range:claims.status},%s)+COUNTIFS({range:claims.status},%s)+COUNTIFS({range:claims.status},%s))' % (SUBS, RESS, DENS)
CLEAN = ck('Accepted first time')

kpis = [
 KPI('Claims submitted, last 30 days', 'COUNTIFS(%s)' % DN('claims.submitted_on', 30), 'int'),
 KPI('Clean Claim Rate, last 90 days', 'IFERROR(COUNTIFS({range:claims.clean_flag},%s,%s)/COUNTIFS(%s),0)' % (CLEAN, D90('claims.submitted_on'), D90('claims.submitted_on')), 'pct', alert={"when": "< {set:clean_claim_target}", "style": "warn"}),
 KPI('Amount claimed, last 30 days', 'SUMIFS({range:claims.amount},%s)' % DN('claims.submitted_on', 30), 'money'),
 KPI('Not accepted first time, 90 days', 'COUNTIFS({range:claims.clean_flag},%s,%s)' % (ck('Not accepted first time'), D90('claims.submitted_on')), 'int'),
 KPI('Payer money received, last 30 days', 'SUMIFS({range:claims.paid_amount},%s)' % DN('claims.paid_on', 30), 'money'),
 KPI('Self-pay fallback clients, 12 months', 'COUNTIFS({range:benefits.result},%s,{range:benefits.checked_on},">="&({today}-365))' % tok('benres', 'Self-pay fallback'), 'int'),
 KPI('Open claims', OPN(), 'int'),
 KPI('Open claims value', OPV(), 'money'),
 KPI('Claims unpaid over 30 days', 'COUNTIFS({range:claims.days_open},">30")', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Value unpaid over 30 days', 'SUMIFS({range:claims.amount},{range:claims.days_open},">30")', 'money'),
 KPI('Average days to payment, last 90 days', 'IFERROR(AVERAGEIFS({range:claims.days_to_pay},%s),0)' % D90('claims.paid_on'), 'num', alert={"when": "> {set:max_days_ar}", "style": "warn"}),
 KPI('Days in A/R now', 'IFERROR(%s/(SUMIFS({range:claims.amount},%s)/90),0)' % (OPV(), D90('claims.submitted_on')), 'num', alert={"when": "> {set:max_days_ar}", "style": "bad"}),
 KPI('Denied claims open', 'COUNTIFS({range:claims.status},%s)' % DENS, 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Value of denied claims open', 'SUMIFS({range:claims.amount},{range:claims.status},%s)' % DENS, 'money'),
 KPI('Denial rate, last 90 days', 'IFERROR(COUNTIFS({range:claims.denied_on},">0",%s)/COUNTIFS(%s),0)' % (D90('claims.submitted_on'), D90('claims.submitted_on')), 'pct', alert={"when": "> {set:denial_target}", "style": "warn"}),
 KPI('Denied claims fixed and paid, this year', 'COUNTIFS({range:claims.denied_on},">0",{range:claims.status},%s,{range:claims.paid_on},">="&%s)' % (PAIDS, JAN), 'int'),
 KPI('Resubmitted claims that were paid', 'IFERROR(COUNTIFS({range:claims.resubmitted_on},">0",{range:claims.status},%s)/COUNTIFS({range:claims.resubmitted_on},">0"),0)' % PAIDS, 'pct'),
 KPI('Benefits checked before first session', 'IFERROR(COUNTIFS({range:benefits.before_flag},%s,{range:benefits.first_session},">="&({today}-365))/COUNTIFS({range:benefits.first_session},">="&({today}-365)),0)' % ck('Checked before first session'), 'pct'),
 KPI('Short-paid amount, this year', 'SUMIFS({range:monthly.short_paid},{range:monthly.month},">="&%s)' % JAN, 'money'),
 KPI('Claims written off, this year', 'COUNTIFS({range:writeoffs.date},">="&%s)' % JAN, 'int'),
 KPI('Write-off share of amount claimed, 12m', 'IFERROR(SUMIFS({range:writeoffs.amount},{range:writeoffs.date},">="&({today}-365))/SUMIFS({range:claims.amount},{range:claims.submitted_on},">="&({today}-365)),0)', 'pct'),
 KPI('Sessions not yet claimed', 'COUNTA({range:unsub.session_id})', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Value not yet claimed', 'SUM({range:unsub.payer_amount})', 'money'),
 KPI('Submitted within the rule days, 90 days', 'IFERROR(COUNTIFS({range:claims.days_to_submit},"<="&{set:claim_submit_days},%s)/COUNTIFS(%s),0)' % (D90('claims.submitted_on'), D90('claims.submitted_on')), 'pct', alert={"when": "< {set:submit_target}", "style": "warn"}),
 KPI('Approvals ending in 30 days', 'COUNTIFS({range:approvals.days_left},">=0",{range:approvals.days_left},"<="&{set:approval_warn_days})', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Payer clients active', 'COUNTIFS({range:clients.active_flag},%s)' % ck('Active payer client'), 'int'),
 KPI('Payer share of sessions, last full month', 'SUMIFS({range:monthly.payer_share},{range:monthly.month},%s)' % PMS, 'pct'),
 KPI('Value over 90 days (A/R aging)', 'SUMIFS({range:aging.amount},{range:aging.month},%s,{range:aging.band},%s)' % (MS, tok('ageband', '90+')), 'money', alert={"when": "> 0", "style": "bad"}),
 KPI('Payer enrolments pending', 'COUNTIFS({range:enrol.status},%s)' % tok('enrolst', 'Applied'), 'int'),
 KPI('Remittances not matched', 'COUNTIFS({range:remits.match_flag},%s)' % ck('Investigate'), 'int', alert={"when": "> 0", "style": "warn"}),
]
assert len(kpis) == 30
dashboard = {"title": "Claims KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Claimed, paid, short-paid and written off", "date": "monthly.month", "series": [
   {"label": "Amount claimed", "sum": "monthly.claimed", "date": "monthly.month"}, {"label": "Payer money received", "sum": "monthly.paid", "date": "monthly.month"},
   {"label": "Short-paid amount", "sum": "monthly.short_paid", "date": "monthly.month"}, {"label": "Written off", "sum": "monthly.written_off", "date": "monthly.month"}]},
 "breakdowns": [{"title": "Claims by status", "by": "claims.status", "agg": "count"}, {"title": "Claims by payer", "by": "claims.payer", "agg": "count"},
                {"title": "Denials by reason", "by": "denials.reason", "agg": "count"}, {"title": "Write-offs by reason", "by": "writeoffs.reason", "agg": "count"}]}
def ARS(b, label): return AGG('sum', 'aging', 'aging.amount', date='aging.month', where=[('band', '=', tok('ageband', b))], label=label)
insights = {"filters": [{"label": "Clinician", "list": "clin"}, {"label": "Payer", "list": "payer"}, {"label": "Service", "list": "svc"}],
 "gauges": [
  {"title": "Claims accepted first time", "num": AGG('count', 'claims', where=[('clean_flag', '=', CLEAN)]), "den": AGG('count', 'claims')},
  {"title": "Claims submitted within the rule days", "num": AGG('count', 'claims', where=[('days_to_submit', '<=', '{set:claim_submit_days}')]), "den": AGG('count', 'claims')},
  {"title": "Claims paid in full", "num": AGG('count', 'claims', where=[('status', '=', PAIDS)]), "den": AGG('count', 'claims', where=[('status', '<>', SUBS)])},
  {"title": "Denials fixed and sent again", "num": AGG('count', 'denials', where=[('fix_check', '=', ck('Fixed and resent'))]), "den": AGG('count', 'denials')},
  {"title": "Benefits checked before first session", "num": AGG('count', 'benefits', where=[('before_flag', '=', ck('Checked before first session'))]), "den": AGG('count', 'benefits')},
  {"title": "Remittances matched to claims", "num": AGG('count', 'remits', where=[('match_flag', '=', ck('Matched'))]), "den": AGG('count', 'remits')}],
 "charts": [
  CHART('Amount claimed per month', 'column', 'month', [AGG('sum', 'monthly', 'monthly.claimed', date='monthly.month', label='Amount claimed')]),
  CHART('Payer money received per month', 'column', 'month', [AGG('sum', 'monthly', 'monthly.paid', date='monthly.month', label='Payer money received')]),
  CHART('Claims submitted per month', 'column', 'month', [AGG('sum', 'monthly', 'monthly.claims_submitted', date='monthly.month', label='Claims submitted')]),
  CHART('Clean claims and claims submitted per month', 'column', 'month', [AGG('sum', 'monthly', 'monthly.clean_claims', date='monthly.month', label='Accepted first time'), AGG('sum', 'monthly', 'monthly.claims_submitted', date='monthly.month', label='Submitted')]),
  CHART('Average days to payment per month', 'line', 'month', [AGG('avg', 'monthly', 'monthly.avg_days_to_pay', date='monthly.month', label='Days to payment')]),
  CHART('Written off per month', 'column', 'month', [AGG('sum', 'monthly', 'monthly.written_off', date='monthly.month', label='Written off')]),
  CHART('Short-paid amount per month', 'column', 'month', [AGG('sum', 'monthly', 'monthly.short_paid', date='monthly.month', label='Short-paid amount')]),
  CHART('Receipts for claim back per month', 'column', 'month', [AGG('sum', 'monthly', 'monthly.receipts', date='monthly.month', label='Receipts')]),
  CHART('Claims by status', 'bar', 'claims.status', [AGG('count', 'claims', label='Claims')]),
  CHART('Claims by payer', 'bar', 'claims.payer', [AGG('count', 'claims', label='Claims')]),
  CHART('Amount claimed by payer', 'bar', 'claims.payer', [AGG('sum', 'claims', 'claims.amount', label='Amount claimed')]),
  CHART('Denials by reason', 'bar', 'denials.reason', [AGG('count', 'denials', label='Denials')]),
  CHART('Denials by payer', 'bar', 'denials.payer', [AGG('count', 'denials', label='Denials')]),
  CHART('Write-offs by reason', 'bar', 'writeoffs.reason', [AGG('count', 'writeoffs', label='Write-offs')]),
  CHART('Write-off amount by payer', 'bar', 'writeoffs.payer', [AGG('sum', 'writeoffs', 'writeoffs.amount', label='Written off')]),
  CHART('A/R by age band per month', 'stacked', 'month', [ARS('0-30', '0-30 days'), ARS('31-60', '31-60 days'), ARS('61-90', '61-90 days'), ARS('90+', '90+ days')]),
  CHART('Claimable sessions per month', 'column', 'month', [AGG('sum', 'monthly', 'monthly.claimable_sessions', date='monthly.month', label='Claimable sessions')]),
  CHART('Remittances by payer', 'bar', 'remits.payer', [AGG('sum', 'remits', 'remits.amount', label='Amount received')]),
  CHART('Follow-ups by method', 'bar', 'followups.method', [AGG('count', 'followups', label='Follow-ups')]),
  CHART('Payer answers to follow-ups', 'bar', 'followups.answer', [AGG('count', 'followups', label='Follow-ups')]),
  CHART('Benefits check results', 'bar', 'benefits.result', [AGG('count', 'benefits', label='Checks')]),
  CHART('Payer enrolment by status', 'bar', 'enrol.status', [AGG('count', 'enrol', label='Enrolments')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
 {"name": "Claims tracker with a chase-first rank", "why": "one claim per session from submission to payment, with days open, age band and the ten claims to chase first", "where": "Claims Tracker"},
 {"name": "A/R aging by payer with Days in A/R", "why": "open claims in 0-30, 31-60, 61-90 and 90+ day bands, the Days in A/R and the old tail growing or shrinking", "where": "Days in AR by Payer"},
 {"name": "Clean Claim Rate with denial reasons", "why": "claims accepted first time against your target, the last two quarters and the denial reasons ranked", "where": "Clean Claim Rate Check"},
 {"name": "Benefits check with self-pay fallback", "why": "session limit, pre-approval and client share before the first session, and the self-pay fee if the payer will not cover it", "where": "Benefits Coverage Check"},
 {"name": "Approval tracker", "why": "sessions left, the date they run out and the latest day to ask for a renewal", "where": "Approval Tracker"},
 {"name": "Denial fix planner", "why": "the usual fix for each denial reason and the resubmit-by date, so a denied claim is not forgotten", "where": "Denial Fix Planner"},
 {"name": "Payer mix value", "why": "net value per session and per day waited for each payer, with grow, hold or renegotiate", "where": "Payer Mix Value"},
 {"name": "Claims cash forecast", "why": "open claims by expected payment date plus new claims give the payer money expected in 30 and 60 days in a base, best or worst case", "where": "Claims Cash Forecast"},
 {"name": "Payer enrolment lead time", "why": "the first billable date of a new clinician and the payer income that cannot be billed meanwhile", "where": "Enrolment Lead Time"},
 {"name": "Receipt for claim back (superbill)", "why": "a receipt a self-pay client sends to their own payer, with a completeness check before you issue it", "where": "Claim Back Receipt Builder"},
 {"name": "Remittance match", "why": "payer payments matched to claims, with the difference and the unmatched remittances", "where": "Remittance Match"},
 {"name": "Yearly write-off forecast", "why": "the yearly loss from denials at five denial rates against the loss you accept", "where": "Write-off Forecast"}]
competitors = [
 {"what": "free invoice templates", "lacks": "list one amount per session but have no payer, claim status, denial reason or time to payment"},
 {"what": "subscription practice-management software", "lacks": "charge per clinician and keep your claims in their system, with no editable targets for Days in A/R or Clean Claim Rate"},
 {"what": "single-sheet claim logs", "lacks": "record a claim and a paid date only, so A/R aging, denial fixes, approvals and write-offs are never worked out"},
 {"what": "generic accounting spreadsheets", "lacks": "show money in and out but cannot say which payer is slow, which claim to chase first or what a denial costs a year"},
 {"what": "outsourced billing services", "lacks": "take a share of every claim and give you a report, not a file you can check yourself"}]
guide = [
 'Open Start and type your practice name and targets in the yellow cells: days to submit a claim, days before a chase, your Clean Claim Rate, the most Days in A/R you accept and the pay run to cover.',
 'Check Payers (fee share and co-pay), Denial Fixes, Services and Team. A third-party payer is an organisation that pays part of a client\'s fee: an insurer, employer scheme or public body.',
 'Before the first session, record a benefits check: session limit, whether a pre-approval is needed and the client share. If the sessions are not covered, the self-pay fee is the fallback.',
 'Record each approval on Approvals. Sessions left and days left fill in, and the Approval Tracker shows the latest day to ask for a renewal.',
 'After every attended payer session, add a claim on Claims Tracker and submit it within your rule days. Sessions with no claim yet appear on Unsubmitted Sessions.',
 'Run a pre-submission check before sending. A claim accepted first time is a clean claim; the Clean Claim Rate is clean claims divided by claims submitted.',
 'Open Chase-first Claims every week. It ranks open claims by amount times days past the payer\'s usual payment time. Record each contact on Claim Follow-ups.',
 'When a payer turns down a claim, record it on Denials. The usual fix and the resubmit-by date fill in. Resubmit before that date or ask the owner to approve a write-off.',
 'Match every payer payment on Remittances. A difference that is not zero needs an explanation. A/R means money owed to the practice; Days in A/R is the open claim value divided by the claim value per day.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'For self-pay clients give a written estimate, then a receipt for claim back (superbill: the client sends it to their own payer). One flat price, your data stays in your file, billing status only.',
 'Read the Claims KPI Dashboard and Charts every week: Clean Claim Rate, Days in A/R, denials, the 90+ day tail and sessions not yet claimed.']
listing = {"title": "Therapy Practice Claims Excel Template: Claims Tracker, A/R Aging, Clean Claim Rate, Denials, Superbill, KPI Dashboard",
 "headline": "Get third-party payers to pay faster in one Excel file",
 "tags": ["claims tracker", "payer billing", "denial tracker", "ar aging report", "clean claim rate", "superbill template", "therapy practice", "counselling practice", "excel template", "private practice", "days in ar", "billing template", "third-party billing"],
 "description": ("Track every claim from the session to the payment in one Excel workbook. Built for a small group practice of talking therapists and counsellors with clients whose fee is partly paid by a third-party payer (an organisation that pays part of a client's fee: in your area an insurer, an employer scheme or a public body).\n\n"
  "Claims Tracker holds one claim per attended session with the date submitted, status (submitted, paid, partly paid, denied, resubmitted or written off), days to submit, days open, days to payment and the A/R age band (0-30, 31-60, 61-90 and 90+ days). A chase-first rank shows which open claims to call about first. Unsubmitted Sessions lists attended payer sessions with no claim yet and whether they are late against your own rule.\n\n"
  "Approvals, Pre-submission Checks, Benefits Checks, Denials with the usual fix and the resubmit-by date, Claim Follow-ups, Remittances matched to claims, Claim Write-offs, Payer Enrolment of each clinician, Receipts for Claim Back (superbill) and Self-pay Estimates cover the whole billing job. Monthly Claims Summary and A/R Aging by Payer give you 24 months of history to compare against.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: benefits coverage check, claim clean-check, chase-first claims, Days in A/R by payer, Clean Claim Rate check, denial fix planner, resubmission value, partial payment gap, write-off risk, remittance match, approval tracker, payer mix value, self-pay or payer, enrolment lead time, claims cash forecast and a yearly write-off forecast. "
  f"Print {len(forms)} sheets and {len(documents)} letters and reports, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
  "This is part four of the Therapy Private Practice suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-clinician fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. The workbook holds billing status only, never clinical notes, and it does not give legal, tax or billing-code advice: check your own local rules."),
 "features": ["Claims tracker with status, age band and chase-first rank", "A/R aging by payer and Days in A/R", "Clean Claim Rate with denial reasons ranked", "Benefits check with the self-pay fallback", "Approvals with sessions left and the renewal date",
              "Denials with the usual fix and resubmit-by date", "Remittances matched to claims", "Receipt for claim back (superbill) builder", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
              f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
assert len(listing['tags']) == 13 and all(len(x) <= 20 for x in listing['tags'])
s = _lib.spec(id=f'{SUITE}-p4', slug='therapy-practice-claims', profession='Therapy Private Practice', name='Third-party Payer Billing and Claims',
         tagline='Get third-party payers to pay faster', price_usd=29, colors={"primary": "#2F5D62", "accent": "#A7C4BC"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 4, "of": 8, "focus": "Third-party payer billing and claims"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'th4.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']))
