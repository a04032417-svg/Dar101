"""Therapy practice suite part 4: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th4_lists import *
import th4_data as DT

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF_PH(sid, k='phone'): return CA(k, 'Phone to message', 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % int(sid[-2:]), 18)
YES = '{list:yesno.yes}'
def ST(lst, lab): return tok(lst, lab)
SUB, RES, DEN, PAID, PART, WOFF = (ST('clmst', x) for x in ('Submitted', 'Resubmitted', 'Denied', 'Paid', 'Partly paid', 'Written off'))
ATT = ST('sstatus', 'Attended')
def OPEN3(c='status'): return 'OR({col:%s}=%s,{col:%s}=%s,{col:%s}=%s)' % (c, SUB, c, RES, c, DEN)
def OPEN2(c='status'): return 'OR({col:%s}=%s,{col:%s}=%s)' % (c, SUB, c, RES)
USUAL = 'ROUND(IFERROR(AVERAGEIFS({range:claims.days_to_pay},{range:claims.payer},{col:payer}),30),0)'
CLINPH = lambda: CA('clinician_phone', 'Clinician phone', 'text', LKT('team.phone', 'team.name', 'clinician'), 18)
CLIPH = lambda: CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18)

settings = [
    S('company', 'Your practice name', 'text', COMPANY), S('claim_submit_days', 'Days after a session within which a claim is submitted', 'int', 5),
    S('claim_chase_days', 'Days after submission before a claim is chased', 'int', 30), S('resubmit_days', 'Days allowed to resubmit a denied claim', 'int', 90),
    S('clean_claim_target', 'Wanted Clean Claim Rate (accepted first time)', 'pct', 0.90), S('max_days_ar', 'Most Days in A/R (money owed) you accept', 'int', 40),
    S('denial_target', 'Denial rate you accept', 'pct', 0.08), S('submit_target', 'Wanted share of claims submitted within the rule days', 'pct', 0.90),
    S('approval_warn_days', 'Days before an approval ends that it is flagged', 'int', 30), S('late_fee_pct', 'Share of the fee charged for a late cancel or no-show', 'pct', 0.5),
    S('late_cancel_hours', 'Hours of notice for a cancellation (less is a late cancel)', 'int', 24), S('deposit', 'New self-pay client deposit', 'money', 50),
    S('admin_cost', 'Booking and billing cost per booked session', 'money', 6), S('claim_admin', 'Extra admin cost per payer claim', 'money', 4),
    S('cost_of_waiting', 'Yearly cost of waiting for money (share of the amount)', 'pct', 0.08), S('card_fee_pct', 'Card payment fee, share of the amount', 'pct', 0.025),
    S('pay_run', 'Pay run to cover from payer money (monthly)', 'money', 10416), S('yearly_loss_accepted', 'Yearly claim write-off loss you accept', 'money', 3000),
    S('short_pay_query', 'Query a short payment above this amount', 'money', 10)]
assert 3 <= len(settings) <= 20

tables = []
tables.append(T('claims', 'Claims Tracker', 'Claims Tracker: one claim per attended session',
    'One row per payer claim: status, denial, resubmission and payment dates; days open, A/R age band, Clean Claim flag, expected payment date and the chase-first rank fill in by themselves.', [
    C('claim_id', 'Claim ID', 'text', 10, required=True), C('session_id', 'Session ID', 'text', 10), C('date', 'Session date', 'date', 11), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24),
    LST('payer', 'Payer', 'payer', 9), LST('service', 'Service', 'svc', 18), LST('clinician', 'Clinician', 'clin', 16), C('amount', 'Claim amount', 'money', 11), C('submitted_on', 'Submitted on', 'date', 11),
    LST('status', 'Status', 'clmst', 12), LST('denial_reason', 'Denial reason', 'denial', 18), C('denied_on', 'Denied on', 'date', 11), C('resubmitted_on', 'Resubmitted on', 'date', 12),
    C('paid_on', 'Paid on', 'date', 11), C('paid_amount', 'Paid amount', 'money', 11), C('written_off', 'Written off', 'money', 11),
    CA('days_to_submit', 'Days to submit', 'int', '{col:submitted_on}-{col:date}', 9),
    CA('days_open', 'Days open', 'int', 'IF(%s,{today}-{col:submitted_on},"")' % OPEN3(), 9),
    CA('days_to_pay', 'Days to payment', 'int', 'IF({col:paid_on}="","",{col:paid_on}-{col:submitted_on})', 10),
    CA('age_band', 'A/R age band, days', 'text', 'IF({col:days_open}="","",IF({col:days_open}<=30,%s,IF({col:days_open}<=60,%s,IF({col:days_open}<=90,%s,%s))))' % tuple(ST('ageband', b) for b in AGE_BANDS), 12),
    CA('clean_flag', 'Clean claim check', 'text', 'IF({col:denied_on}="",%s,%s)' % (ck('Accepted first time'), ck('Not accepted first time')), 17),
    CA('expected_pay', 'Expected payment date', 'date', 'IF(%s,IF({col:resubmitted_on}="",{col:submitted_on},{col:resubmitted_on})+%s,"")' % (OPEN2(), USUAL), 12),
    CA('chase_flag', 'Chase check', 'text', 'IF(%s,IF({col:days_open}>{set:claim_chase_days},IF(COUNTIFS({range:followups.claim_id},{col:claim_id},{range:followups.chased_on},">="&({today}-7))>0,%s,%s),%s),IF({col:status}=%s,%s,%s))' % (
        OPEN2(), ck('Chased this week'), ck('Chase now'), ck('Within usual time'), DEN, ck('Fix and resubmit'), ck('Closed')), 16),
    CA('chase_score', 'Chase score', 'int', 'IF(%s,ROUND({col:amount}*MAX(0,{col:days_open}-%s),0),"")' % (OPEN2(), USUAL), 9),
    CA('chase_rank', 'Chase-first rank', 'int', 'IF({col:chase_score}="","",IF({col:chase_score}<=0,"",1+COUNTIFS({range:claims.chase_score},">"&{col:chase_score})+COUNTIFS({range:claims.chase_score},{col:chase_score},{range:claims.claim_id},"<"&{col:claim_id})))', 10),
    CLIPH(), STAFF_PH('TH-07', 'coordinator_phone'), CLINPH()], DT.claims_d(), 1500,
    [A('chase_flag', '= ' + ck('Chase now'), 'bad'), A('chase_flag', '= ' + ck('Fix and resubmit'), 'warn'), A('chase_rank', '<= 10', 'warn'), A('status', '= ' + PAID, 'good'), A('status', '= ' + WOFF, 'bad')]))
tables.append(T('sessions', 'Payer Sessions', 'Payer sessions with payer amount and client co-pay',
    'One row per session of a client whose fee is partly paid by a third-party payer (the last 100 days): fee, charge and the two parts; the claimed check fills in by itself.', [
    C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), LST('payer', 'Payer', 'payer', 9),
    LST('service', 'Service', 'svc', 18), LST('clinician', 'Clinician', 'clin', 16), LST('status', 'Status', 'sstatus', 12), C('fee', 'List fee', 'money', 11), C('charge', 'Charge', 'money', 11),
    C('payer_amount', 'Payer amount', 'money', 11), C('client_amount', 'Client co-pay', 'money', 11),
    CA('claimed', 'Claimed check', 'text', 'IF({col:status}<>%s,%s,IF(COUNTIFS({range:claims.session_id},{col:session_id})>0,%s,%s))' % (ATT, ck('Not claimable'), ck('Claimed'), ck('Not claimed yet')), 15),
    CLIPH(), STAFF_PH('TH-07', 'coordinator_phone')], DT.sessions_d(), 1200, [A('claimed', '= ' + ck('Not claimed yet'), 'bad'), A('status', '= ' + ST('sstatus', 'No-show'), 'warn')]))
tables.append(T('unsub', 'Unsubmitted Sessions', 'Unsubmitted sessions: attended, no claim yet',
    'One row per attended payer session that has no claim: payer amount at stake; days since the session and the late flag against your claim rule fill in by themselves.', [
    C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Session date', 'date', 11), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), LST('payer', 'Payer', 'payer', 9),
    LST('clinician', 'Clinician', 'clin', 16), C('payer_amount', 'Payer amount', 'money', 11), CA('days_since', 'Days since session', 'int', '{today}-{col:date}', 10),
    CA('late_flag', 'Rule check', 'text', 'IF({col:days_since}>{set:claim_submit_days},%s,%s)' % (ck('Late, over the rule'), ck('Within the rule')), 16), CLINPH(), STAFF_PH('TH-07', 'coordinator_phone')], DT.unsub_d(), 400,
    [A('late_flag', '= ' + ck('Late, over the rule'), 'bad'), A('days_since', '> 30', 'bad')]))
tables.append(T('checks', 'Pre-submission Checks', 'Pre-submission checks before a claim is sent',
    'One row per claim checked before submission: client details, session details and approval; the client, payer, days before submission and the ready flag fill in by themselves.', [
    C('check_id', 'Check ID', 'text', 10, required=True), C('claim_id', 'Claim ID', 'text', 10), C('checked_on', 'Checked on', 'date', 11), C('details_ok', 'Client details complete', 'bool', 11),
    C('session_ok', 'Session details complete', 'bool', 11), C('approval_ok', 'Approval valid', 'bool', 10), REF('checked_by', 'Checked by', 'team.name', 20),
    CA('client', 'Client', 'text', LKT('claims.client', 'claims.claim_id', 'claim_id'), 24), CA('payer', 'Payer', 'text', LKT('claims.payer', 'claims.claim_id', 'claim_id'), 9),
    CA('days_before', 'Days before submission', 'int', 'IFERROR(INDEX({range:claims.submitted_on},MATCH({col:claim_id},{range:claims.claim_id},0))-{col:checked_on},"")', 11),
    CA('ready_flag', 'Ready check', 'text', 'IF(AND({col:details_ok}=%s,{col:session_ok}=%s,{col:approval_ok}=%s),%s,%s)' % (YES, YES, YES, ck('Ready to submit'), ck('Fix first')), 15)], DT.checks_d(), 800,
    [A('ready_flag', '= ' + ck('Fix first'), 'bad'), A('ready_flag', '= ' + ck('Ready to submit'), 'good')]))
tables.append(T('approvals', 'Approvals', 'Approvals and session limits by payer client',
    'One row per approval period: sessions approved, sessions used and the valid-until date; sessions left, days left and the approval check fill in by themselves.', [
    C('approval_id', 'Approval ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), LST('payer', 'Payer', 'payer', 9), LST('clinician', 'Clinician', 'clin', 16),
    C('approved_on', 'Approved on', 'date', 11), C('sessions_approved', 'Sessions approved', 'int', 10), C('valid_until', 'Valid until', 'date', 11), C('sessions_used', 'Sessions used', 'int', 10),
    CA('sessions_left', 'Sessions left', 'int', 'MAX(0,{col:sessions_approved}-{col:sessions_used})', 9), CA('days_left', 'Days left', 'int', '{col:valid_until}-{today}', 9),
    CA('approval_check', 'Approval check', 'text', 'IF({col:days_left}<0,%s,IF(OR({col:days_left}<={set:approval_warn_days},{col:sessions_left}<=2),%s,%s))' % (ck('Ended'), ck('Ending soon'), ck('Valid')), 14),
    CLIPH(), CLINPH()], DT.approvals_d(), 600, [A('approval_check', '= ' + ck('Ending soon'), 'warn'), A('sessions_left', '<= 2', 'bad'), A('approval_check', '= ' + ck('Valid'), 'good')]))
tables.append(T('denials', 'Denials', 'Denials with the fix and the resubmit-by date',
    'One row per denied claim: reason, fix and resubmission dates; the client, amount, usual fix, days to fix, resubmit-by date and the fix check fill in by themselves.', [
    C('denial_id', 'Denial ID', 'text', 10, required=True), C('claim_id', 'Claim ID', 'text', 10), C('denied_on', 'Denied on', 'date', 11), LST('payer', 'Payer', 'payer', 9), LST('reason', 'Denial reason', 'denial', 18),
    C('fixed_on', 'Fixed on', 'date', 11), C('resubmitted_on', 'Resubmitted on', 'date', 12),
    CA('client', 'Client', 'text', LKT('claims.client', 'claims.claim_id', 'claim_id'), 24), CA('amount', 'Claim amount', 'money', LKN('claims.amount', 'claims.claim_id', 'claim_id'), 11),
    CA('fix_needed', 'Usual fix', 'text', 'IFERROR(INDEX({range:fixes.usual_fix},MATCH({col:reason},{range:fixes.reason},0))&"","")', 30),
    CA('days_to_fix', 'Days to fix', 'int', 'IF({col:fixed_on}="","",{col:fixed_on}-{col:denied_on})', 9), CA('resubmit_by', 'Resubmit by', 'date', '{col:denied_on}+{set:resubmit_days}', 11),
    CA('days_left', 'Days left to resubmit', 'int', '{col:resubmit_by}-{today}', 10),
    CA('fix_check', 'Fix check', 'text', 'IF({col:resubmitted_on}<>"",%s,IF(IFERROR(INDEX({range:claims.status},MATCH({col:claim_id},{range:claims.claim_id},0)),"")=%s,%s,IF({col:days_left}<0,%s,%s)))' % (
        ck('Fixed and resent'), WOFF, ck('Written off'), ck('Past resubmit window'), ck('Fix now')), 18),
    CA('client_phone', 'Client phone', 'text', LKT('claims.client_phone', 'claims.claim_id', 'claim_id'), 18), STAFF_PH('TH-07', 'coordinator_phone'), STAFF_PH('TH-01', 'owner_phone')], DT.denials_d(), 500,
    [A('fix_check', '= ' + ck('Fix now'), 'bad'), A('fix_check', '= ' + ck('Past resubmit window'), 'warn'), A('fix_check', '= ' + ck('Fixed and resent'), 'good')]))
tables.append(T('followups', 'Claim Follow-ups', 'Claim follow-ups with the payer answer',
    'One row per chase of an open claim: method, payer answer and next step date; the payer, client, days since submission and the next-chase check fill in by themselves.', [
    C('followup_id', 'Follow-up ID', 'text', 10, required=True), C('claim_id', 'Claim ID', 'text', 10), C('chased_on', 'Chased on', 'date', 11), LST('method', 'Method', 'fmethod', 13), LST('answer', 'Payer answer', 'fanswer', 17),
    C('next_step_date', 'Next step date', 'date', 11),
    CA('payer', 'Payer', 'text', LKT('claims.payer', 'claims.claim_id', 'claim_id'), 9), CA('client', 'Client', 'text', LKT('claims.client', 'claims.claim_id', 'claim_id'), 24),
    CA('days_since', 'Days since submission', 'int', 'IFERROR({col:chased_on}-INDEX({range:claims.submitted_on},MATCH({col:claim_id},{range:claims.claim_id},0)),"")', 11),
    CA('next_check', 'Next chase check', 'text', 'IF(OR(IFERROR(INDEX({range:claims.status},MATCH({col:claim_id},{range:claims.claim_id},0)),"")=%s,IFERROR(INDEX({range:claims.status},MATCH({col:claim_id},{range:claims.claim_id},0)),"")=%s),IF(COUNTIFS({range:followups.claim_id},{col:claim_id},{range:followups.chased_on},">"&{col:chased_on})>0,%s,IF({col:next_step_date}<={today},%s,%s)),%s)' % (SUB, RES, ck('Closed'), ck('Chase now'), ck('Within usual time'), ck('Closed')), 16),
    STAFF_PH('TH-07', 'coordinator_phone'), STAFF_PH('TH-01', 'owner_phone')], DT.followups_d(), 500, [A('next_check', '= ' + ck('Chase now'), 'bad'), A('answer', '= ' + ST('fanswer', 'No answer'), 'warn')]))
tables.append(T('benefits', 'Benefits Checks', 'Benefits checks with the self-pay fallback',
    'One row per benefits check: session limit, pre-approval, client share and result with the self-pay fee as the fallback; whether it was checked before the first session fills in by itself.', [
    C('check_id', 'Check ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18), LST('payer', 'Payer', 'payer', 9),
    LST('service', 'Service', 'svc', 18), C('first_session', 'First session', 'date', 11), C('checked_on', 'Checked on', 'date', 11), REF('checked_by', 'Checked by', 'team.name', 20), C('session_limit', 'Session limit', 'int', 9),
    C('pre_approval_needed', 'Pre-approval needed', 'bool', 10), C('client_share', 'Client share per session', 'money', 11), LST('result', 'Result', 'benres', 18), C('self_pay_fee', 'Self-pay fee', 'money', 11),
    CA('before_flag', 'Timing check', 'text', 'IF({col:checked_on}<={col:first_session},%s,%s)' % (ck('Checked before first session'), ck('Checked after first session')), 18), STAFF_PH('TH-07', 'coordinator_phone')], DT.benefits_d(), 800,
    [A('before_flag', '= ' + ck('Checked after first session'), 'warn'), A('result', '= ' + ST('benres', 'Needs pre-approval'), 'warn'), A('result', '= ' + ST('benres', 'Covered'), 'good')]))
tables.append(T('writeoffs', 'Claim Write-offs', 'Claim write-offs with the reason and who approved them',
    'One row per claim written off: date, amount, reason and approver; the client and the days the claim was open fill in by themselves.', [
    C('writeoff_id', 'Write-off ID', 'text', 10, required=True), C('claim_id', 'Claim ID', 'text', 10), C('date', 'Date', 'date', 11), LST('payer', 'Payer', 'payer', 9), C('amount', 'Amount', 'money', 11),
    LST('reason', 'Reason', 'wreason', 22), REF('approved_by', 'Approved by', 'team.name', 20), CA('client', 'Client', 'text', LKT('claims.client', 'claims.claim_id', 'claim_id'), 24),
    CA('days_open', 'Days open at write-off', 'int', 'IFERROR({col:date}-INDEX({range:claims.submitted_on},MATCH({col:claim_id},{range:claims.claim_id},0)),"")', 11), STAFF_PH('TH-01', 'owner_phone')], DT.writeoffs_d(), 300,
    [A('amount', '>= 100', 'warn')]))
tables.append(T('remits', 'Remittances', 'Remittances: payer payments matched to claims',
    'One row per payer payment that covers several claims: claims paid, amount received and amount matched to claims; the difference and the match check fill in by themselves.', [
    C('remit_id', 'Remittance ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('payer', 'Payer', 'payer', 9), C('claims_paid', 'Claims paid', 'int', 9), C('amount', 'Amount received', 'money', 12), C('matched_amount', 'Matched to claims', 'money', 12),
    CA('difference', 'Difference', 'money', '{col:amount}-{col:matched_amount}', 11), CA('avg_claim', 'Average per claim', 'money', 'IF({col:claims_paid}>0,ROUND({col:amount}/{col:claims_paid},2),0)', 11),
    CA('match_flag', 'Match check', 'text', 'IF(ABS({col:difference})<0.005,%s,%s)' % (ck('Matched'), ck('Investigate')), 12), STAFF_PH('TH-07', 'coordinator_phone')], DT.remits_d(), 600,
    [A('match_flag', '= ' + ck('Investigate'), 'bad'), A('match_flag', '= ' + ck('Matched'), 'good')]))
tables.append(T('enrol', 'Payer Enrolment', 'Payer enrolment of each clinician',
    'One row per payer and clinician: application sent, effective date and renewal; weeks waiting, the usual weeks for the payer, the expected effective date and the billing check fill in by themselves.', [
    C('enrolment_id', 'Enrolment ID', 'text', 10, required=True), LST('payer', 'Payer', 'payer', 9), LST('clinician', 'Clinician', 'clin', 16), C('application_sent', 'Application sent', 'date', 12),
    C('effective_date', 'Effective date', 'date', 11), C('renewal_due', 'Renewal due', 'date', 11), LST('status', 'Status', 'enrolst', 13),
    CA('weeks_wait', 'Weeks from application', 'int', 'ROUND((IF({col:effective_date}="",{today},{col:effective_date})-{col:application_sent})/7,0)', 11),
    CA('usual_weeks', 'Usual weeks for this payer', 'int', 'IFERROR(ROUND(AVERAGEIFS({range:enrol.weeks_wait},{range:enrol.payer},{col:payer},{range:enrol.effective_date},"<>"),0),0)', 11),
    CA('expected_effective', 'Expected effective date', 'date', 'IF({col:effective_date}<>"",{col:effective_date},{col:application_sent}+7*{col:usual_weeks})', 12),
    CA('bill_flag', 'Billing check', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,%s,%s))' % (ST('enrolst', 'Applied'), ck('Waiting for payer'), ST('enrolst', 'Renewal due'), ck('Renew soon'), ck('Can bill')), 16),
    STAFF_PH('TH-01', 'owner_phone')], DT.enrol_d(), 60, [A('bill_flag', '= ' + ck('Waiting for payer'), 'bad'), A('bill_flag', '= ' + ck('Renew soon'), 'warn'), A('bill_flag', '= ' + ck('Can bill'), 'good')]))
tables.append(T('receipts', 'Receipts for Claim Back', 'Receipts for claim back (superbill)',
    'One row per receipt (superbill): the month, sessions and the amount the client paid, which they send to their own payer; the average per session fills in by itself.', [
    C('receipt_id', 'Receipt ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18),
    C('sessions', 'Sessions', 'int', 9), C('amount_paid', 'Amount paid', 'money', 11), C('issued_on', 'Issued on', 'date', 11), CA('per_session', 'Average per session', 'money', 'IF({col:sessions}>0,ROUND({col:amount_paid}/{col:sessions},0),0)', 11)],
    DT.receipts_d(), 800))
tables.append(T('clients', 'Payer Clients', 'Payer clients with payer, status and approval date',
    'One row per client whose fee is partly paid by a third-party payer: payer, clinician, status and approval date; the active check and open claims fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), LST('payer', 'Payer', 'payer', 9), LST('clinician', 'Clinician', 'clin', 16), C('first_session', 'First session', 'date', 11),
    LST('status', 'Status', 'cstatus', 12), C('sessions_attended', 'Sessions attended', 'int', 10), C('approval_valid_until', 'Approval valid until', 'date', 12), C('phone', 'Phone', 'text', 18),
    CA('active_flag', 'Active check', 'text', 'IF(OR({col:status}=%s,{col:status}=%s,{col:status}=%s),%s,%s)' % (ST('cstatus', 'Active'), ST('cstatus', 'Booked'), ST('cstatus', 'On hold'), ck('Active payer client'), ck('Not active')), 17),
    CA('open_claims', 'Open claims', 'int', 'COUNTIFS({range:claims.client_id},{col:client_id},{range:claims.status},%s)+COUNTIFS({range:claims.client_id},{col:client_id},{range:claims.status},%s)+COUNTIFS({range:claims.client_id},{col:client_id},{range:claims.status},%s)' % (SUB, RES, DEN), 9)],
    DT.clients_d(), 800, [A('open_claims', '> 0', 'warn')]))
tables.append(T('estimates', 'Self-pay Estimates', 'Self-pay cost estimates given to clients before they start',
    'One row per written estimate: fee, expected sessions, late-cancel rule, deposit and package option; the discount, the expected total and the best option fill in by themselves.', [
    C('estimate_id', 'Estimate ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18), LST('service', 'Service', 'svc', 18),
    C('fee', 'Fee per session', 'money', 11), C('expected_sessions', 'Expected sessions', 'int', 10), LST('late_rule', 'Late-cancel rule', 'lcrule', 24), C('deposit', 'Deposit', 'money', 9), LST('package', 'Package option', 'pkopt', 13),
    C('sliding_pct', 'Sliding scale share', 'pct', 10), C('issued_on', 'Issued on', 'date', 11),
    CA('discount', 'Package discount', 'pct', 'IF(AND({col:package}=%s,{col:expected_sessions}>=10),0.1,IF(AND({col:package}=%s,{col:expected_sessions}>=6),0.05,0))' % (ST('pkopt', '10 sessions'), ST('pkopt', '6 sessions')), 10),
    CA('expected_total', 'Expected total cost', 'money', 'ROUND({col:fee}*{col:expected_sessions}*(1-{col:discount}),0)', 12),
    CA('best_option', 'Best option', 'text', 'IF({col:expected_sessions}>=6,%s,%s)' % (vd('Package saves money'), vd('Pay per session')), 19)], DT.estimates_d(), 200))
tables.append(T('monthly', 'Monthly Claims Summary', 'Monthly claims summary, 24 months',
    'One row per month: claimable sessions, claims submitted, clean claims, amounts claimed and paid, write-offs and receipts; open claims at month end and the Clean Claim Rate fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), C('attended_sessions', 'Attended sessions', 'int', 10), C('claimable_sessions', 'Claimable sessions', 'int', 10), C('claims_submitted', 'Claims submitted', 'int', 10),
    C('clean_claims', 'Clean claims', 'int', 9), C('claimed', 'Amount claimed', 'money', 12), C('paid', 'Payer money received', 'money', 12), C('avg_days_to_pay', 'Average days to pay', 'num', 10),
    C('written_off', 'Written off', 'money', 11), C('short_paid', 'Short-paid amount', 'money', 11), C('receipts', 'Receipts for claim back', 'int', 10),
    CA('open_at_end', 'Open claims at month end', 'int', 'IF(COUNTIFS({range:aging.month},{col:month})=0,"",SUMIFS({range:aging.claims},{range:aging.month},{col:month}))', 11),
    CA('clean_rate', 'Clean Claim Rate', 'pct', 'IF({col:claims_submitted}>0,{col:clean_claims}/{col:claims_submitted},0)', 10),
    CA('payer_share', 'Payer share of sessions', 'pct', 'IF({col:attended_sessions}>0,{col:claimable_sessions}/{col:attended_sessions},0)', 10),
    CA('rate_flag', 'Rate check', 'text', 'IF({col:clean_rate}>={set:clean_claim_target},%s,%s)' % (vd('On target'), vd('Below target')), 12),
    STAFF_PH('TH-01', 'owner_phone'), STAFF_PH('TH-08', 'accountant_phone')], DT.monthly_d(), 60, [A('clean_rate', '< {set:clean_claim_target}', 'warn')]))
tables.append(T('aging', 'AR Aging by Payer', 'A/R aging by payer and month, by age band',
    'One row per month, payer and age band (0-30, 31-60, 61-90, 90+ days since submission): open claims and their value at the month end; the average per claim fills in by itself.', [
    C('ageing_id', 'Aging ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), C('as_of', 'As of', 'date', 11), LST('payer', 'Payer', 'payer', 9), LST('band', 'Age band, days', 'ageband', 12),
    C('claims', 'Open claims', 'int', 9), C('amount', 'Open amount', 'money', 11), CA('avg_claim', 'Average per claim', 'money', 'IF({col:claims}>0,ROUND({col:amount}/{col:claims},0),0)', 11),
    STAFF_PH('TH-01', 'owner_phone')], DT.aging_d(), 400, [A('band', '= ' + ST('ageband', '90+'), 'warn')]))
tables.append(T('payers', 'Payers', 'Payers: the share of the fee allowed and the client co-pay',
    'One row per third-party payer (an organisation that pays part of a client\'s fee): the share of the fee it allows and the co-pay (the part of the fee the client still pays).', [
    C('payer', 'Payer', 'text', 12, required=True), C('fee_share', 'Fee share allowed', 'pct', 12), C('copay', 'Client co-pay', 'money', 11)], DT.payers_d(), 50))
tables.append(T('fixes', 'Denial Fixes', 'Denial reasons with the usual fix and the days it takes',
    'One row per denial reason: the usual fix and the days it takes to fix and resubmit; the Denials sheet reads them.', [
    LST('reason', 'Denial reason', 'denial', 18, required=True), C('usual_fix', 'Usual fix', 'text', 30), C('days_to_fix', 'Days to fix', 'int', 10)], DT.fixes_d(), 50))
tables.append(T('services', 'Services', 'Services with minutes and list fee', 'One row per service: minutes and this year\'s list fee before any tax.', [
    C('service', 'Service', 'text', 22, required=True), C('minutes', 'Minutes', 'int', 9), C('fee', 'Fee', 'money', 11)], DT.services_d(), 50))
tables.append(T('team', 'Team', 'Team: clinicians, coordinator and outside contacts',
    'One row per person: employed, contract (self-employed) and associate (works under supervision) clinicians, the coordinator and outside contacts; payer clients and enrolments fill in by themselves.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 24), C('team', 'Team', 'text', 12), C('pay_type', 'Pay type', 'text', 16), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26),
    C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'int', 11), C('split_pct', 'Split share', 'pct', 9), C('session_rate', 'Rate per session', 'int', 10), C('hourly_rate', 'Hourly rate', 'int', 9),
    C('session_cap', 'Session cap a week', 'int', 10), C('session_target', 'Session target a week', 'int', 10), C('speciality', 'Speciality', 'text', 30), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
    CA('payer_clients', 'Active payer clients', 'int', 'COUNTIFS({range:clients.clinician},{col:name},{range:clients.active_flag},%s)' % ck('Active payer client'), 10),
    CA('payers_enrolled', 'Payers enrolled', 'int', 'COUNTIFS({range:enrol.clinician},{col:name},{range:enrol.bill_flag},%s)+COUNTIFS({range:enrol.clinician},{col:name},{range:enrol.bill_flag},%s)' % (ck('Can bill'), ck('Renew soon')), 10)], DT.team_d(), 50))
assert len(tables) == 20
