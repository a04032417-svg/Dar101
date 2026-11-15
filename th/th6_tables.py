"""Therapy practice suite part 6: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th6_lists import *
import th6_data as D

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF_PH(sid, k='phone', label='Phone to message'): return CA(k, label, 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % int(sid[-2:]), 18)
def CO(): return CA('company', 'Practice', 'text', '{set:company}&""', 24)
YES = '{list:yesno.yes}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'
JAN1 = 'DATE(YEAR({today}),1,1)'
def CPH(src_col='clinician', k='clinician_phone', label='Clinician phone'): return CA(k, label, 'text', LKT('team.phone', 'team.name', src_col), 18)
OV, DONEOK, DONELATE, SENT, NOTSENT = ck('Overdue'), ck('Done on time'), ck('Done late'), ck('Sent'), ck('Not sent')

settings = [
    S('company', 'Your practice name', 'text', COMPANY), S('note_due_days', 'Days within which a session note is done', 'int', NOTE_DUE_DAYS), S('note_target_rate', 'Wanted share of notes done within the rule', 'pct', 0.9),
    S('review_every_days', 'Days between treatment-plan reviews', 'int', REVIEW_EVERY_DAYS), S('supervision_ratio', 'Client sessions per supervision hour for the associate', 'int', SUPERVISION_RATIO),
    S('peer_hours_month', 'Supervision or peer hours a month for each other clinician', 'num', 2), S('ce_target_hours', 'CE (CPD) hours wanted a year (check your own rules)', 'int', CE_TARGET_HOURS),
    S('report_year', 'Year shown on the continuing education pages', 'int', TODAY.year), S('renewal_warn_days', 'Days before a renewal turns amber', 'int', 45), S('renewal_red_days', 'Days before a renewal turns red', 'int', 30),
    S('consent_review_months', 'Months between consent reviews (check your own local rules)', 'int', 12), S('request_days', 'Days to answer a record request (check local rules)', 'int', 30),
    S('archive_after_months', 'Months after discharge before a file is archived', 'int', 12), S('letter_days', 'Days after the last session to send the closing letter', 'int', 7),
    S('min_change_points', 'Points of change that count as a real change', 'int', 4), S('coverage_target', 'Wanted share of active clients with a current score', 'pct', 0.9)]
assert 3 <= len(settings) <= 20

tables = []
# 1
tables.append(T('notes', 'Note Status', 'Session note status: done on time, late or overdue',
    'One row per attended session: the date the note was done (never its content); days to note, the on-time flag and days overdue fill in by themselves.', [
    C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('client', 'Client', 'text', 24), LST('clinician', 'Clinician', 'clin', 16), LST('service', 'Service', 'svc', 18),
    C('note_done_on', 'Note done on', 'date', 12),
    CA('days_to_note', 'Days to note', 'int', 'IF({col:note_done_on}="","",{col:note_done_on}-{col:date})', 9),
    CA('note_check', 'On-time check', 'text', 'IF({col:note_done_on}<>"",IF({col:note_done_on}-{col:date}<={set:note_due_days},%s,%s),IF({today}-{col:date}>{set:note_due_days},%s,%s))' % (ck('On time'), ck('Late'), OV, ck('Due soon')), 12),
    CA('overdue_days', 'Days overdue', 'int', 'IF({col:note_done_on}="","",MAX(0,{today}-{col:date}-{set:note_due_days}))', 9), CPH(), CO()], D.notes_d(), 1000,
    [A('note_check', '= ' + OV, 'bad'), A('note_check', '= ' + ck('Late'), 'warn'), A('note_check', '= ' + ck('On time'), 'good')]))
# 2
tables.append(T('months', 'Admin by Clinician Month', 'Notes and plan reviews by clinician and month',
    'One row per clinician and month: notes done within the rule, done late or missing, and plan reviews due and done; attended sessions and the on-time share fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('clinician', 'Clinician', 'clin', 16), C('on_time', 'Notes within the rule', 'int', 10), C('late', 'Notes done late', 'int', 10),
    C('missing', 'Notes missing', 'int', 10), C('reviews_due', 'Plan reviews due', 'int', 10), C('reviews_done', 'Plan reviews done', 'int', 10),
    CA('attended', 'Attended sessions', 'int', '{col:on_time}+{col:late}+{col:missing}', 10),
    CA('on_time_share', 'On-time share, %', 'pct', 'IF({col:attended}>0,{col:on_time}/{col:attended},0)', 10),
    CA('rule_flag', 'Rule check', 'text', 'IF({col:on_time_share}>={set:note_target_rate},%s,%s)' % (ck('Within target'), ck('Below target')), 12), STAFF_PH('TH-01', 'owner_phone'), CO()], D.month_rows_d(), 200,
    [A('rule_flag', '= ' + ck('Below target'), 'warn'), A('missing', '> 0', 'bad')]))
# 3
tables.append(T('reviews', 'Plan Reviews', 'Treatment-plan reviews due and done',
    'One row per plan review: due date, the date it was done and the outcome score typed at the review; days overdue and the status fill in by themselves.', [
    C('review_id', 'Review ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), LST('clinician', 'Clinician', 'clin', 16), C('review_no', 'Review no', 'int', 9),
    C('due_date', 'Due date', 'date', 11), C('reviewed_on', 'Reviewed on', 'date', 11), C('score', 'Score at review', 'int', 9),
    CA('days_overdue', 'Days overdue', 'int', 'IF({col:reviewed_on}<>"",MAX(0,{col:reviewed_on}-{col:due_date}),MAX(0,{today}-{col:due_date}))', 9),
    CA('status', 'Review status', 'text', 'IF({col:reviewed_on}<>"",IF({col:reviewed_on}<={col:due_date},%s,%s),IF({col:due_date}<{today},%s,IF({col:due_date}<={today}+30,%s,%s)))' % (
        DONEOK, DONELATE, OV, ck('Due in 30 days'), ck('On schedule')), 14), CPH(), CO()], D.reviews_d(), 1000,
    [A('status', '= ' + OV, 'bad'), A('status', '= ' + DONELATE, 'warn'), A('status', '= ' + ck('Due in 30 days'), 'warn'), A('status', '= ' + DONEOK, 'good')]))
# 4
tables.append(T('scores', 'Outcome Scores', 'Outcome scores at intake, review and discharge',
    'One row per score: the plain number (0 to 40, lower is better) typed from the practice\'s own questionnaire; the change against the client\'s intake score fills in by itself.', [
    C('score_id', 'Score ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), LST('clinician', 'Clinician', 'clin', 16),
    LST('point', 'Point', 'opoint', 10), C('score', 'Score', 'int', 8),
    CA('vs_intake', 'Points against intake', 'int', 'IF({col:point}=%s,0,IFERROR(IF(INDEX({range:change.intake_score},MATCH({col:client_id},{range:change.client_id},0))="","",{col:score}-INDEX({range:change.intake_score},MATCH({col:client_id},{range:change.client_id},0))),""))' % tok('opoint', 'Intake'), 11)],
    D.scores_d(), 1000, [A('vs_intake', '<= -4', 'good'), A('vs_intake', '>= 4', 'warn')]))
# 5
tables.append(T('change', 'Score Change by Client', 'Score change from intake to the latest review, by client',
    'One row per client: the intake and latest score as plain numbers (lower is better); change, change share and the band fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), LST('clinician', 'Clinician', 'clin', 16), LST('service', 'Service', 'csvc', 18), LST('status', 'Status', 'cstatus', 12),
    C('phone', 'Phone', 'text', 18), C('intake_score', 'Intake score', 'int', 9), C('latest_score', 'Latest score', 'int', 9),
    CA('change', 'Change in points', 'int', 'IF(OR({col:intake_score}="",{col:latest_score}=""),"",{col:latest_score}-{col:intake_score})', 9),
    CA('change_share', 'Change share, %', 'pct', 'IF({col:change}="","",IF({col:intake_score}=0,0,{col:change}/{col:intake_score}))', 10),
    CA('band', 'Band', 'text', 'IF({col:intake_score}="",%s,IF({col:change}="",%s,IF({col:change}<=-{set:min_change_points},%s,IF({col:change}>={set:min_change_points},%s,%s))))' % (
        ck('Missing intake score'), ck('No score yet'), ck('Improved'), ck('Review the plan'), ck('No change')), 16), CPH(), CO()], D.change_d(), 800,
    [A('band', '= ' + ck('Missing intake score'), 'bad'), A('band', '= ' + ck('Review the plan'), 'warn'), A('band', '= ' + ck('Improved'), 'good')]))
# 6
tables.append(T('discharges', 'Discharges', 'Discharges and referrals out with closing letters',
    'One row per discharge: reason, sessions, where the client was referred and whether the closing letter and referral letter were sent; days since the last session fill in by themselves.', [
    C('discharge_id', 'Discharge ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), C('phone', 'Phone', 'text', 18),
    LST('clinician', 'Clinician', 'clin', 16), LST('service', 'Service', 'csvc', 18), LST('reason', 'Reason', 'dreason', 14), C('sessions', 'Sessions', 'int', 9), LST('referred_to', 'Referred to', 'refto', 18),
    C('last_session', 'Last session', 'date', 11), C('letter_sent', 'Closing letter sent', 'bool', 10), C('referral_sent', 'Referral letter sent', 'bool', 10), C('final_score', 'Final score', 'int', 9),
    CA('days_since_last', 'Days since last session', 'int', '{col:date}-{col:last_session}', 10),
    CA('letter_check', 'Closing letter check', 'text', 'IF({col:letter_sent}=%s,%s,%s)' % (YES, SENT, NOTSENT), 12),
    CA('referral_check', 'Referral letter check', 'text', 'IF({col:referred_to}="","",IF({col:referral_sent}=%s,%s,%s))' % (YES, SENT, NOTSENT), 12), CPH(), CO()], D.discharges_d(), 1000,
    [A('letter_check', '= ' + NOTSENT, 'warn'), A('referral_check', '= ' + NOTSENT, 'bad')]))
# 7
tables.append(T('weeks', 'Late Notes by Week', 'Late notes by clinician and week, last 13 weeks',
    'One row per clinician and week: notes due and notes late (done late or still missing); the on-time share and the rule check fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), LST('clinician', 'Clinician', 'clin', 16), LST('wk', 'Week no', 'wk', 10), C('notes_due', 'Notes due', 'int', 9),
    C('notes_late', 'Notes late', 'int', 9), CA('on_time_share', 'On-time share, %', 'pct', 'IF({col:notes_due}>0,({col:notes_due}-{col:notes_late})/{col:notes_due},0)', 10),
    CA('rule_flag', 'Rule check', 'text', 'IF({col:on_time_share}<{set:note_target_rate},%s,%s)' % (ck('Over the rule'), ck('Within the rule')), 13), STAFF_PH('TH-01', 'owner_phone'), CO()], D.weeks_d(), 300,
    [A('rule_flag', '= ' + ck('Over the rule'), 'warn'), A('notes_late', '>= 5', 'bad')]))
# 8
tables.append(T('suplog', 'Supervision Log', 'Supervision log: individual, group and peer hours with cost',
    'One row per supervision session: who was supervised, by whom, the hours and the cost the practice pays; the cost per hour and the phones fill in by themselves.', [
    C('supervision_id', 'Supervision ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), LST('supervisee', 'Supervisee', 'clin', 16), C('supervisor', 'Supervisor', 'text', 22), LST('kind', 'Kind', 'supk', 16),
    C('hours', 'Hours', 'num', 8), C('cost', 'Cost', 'int', 9), CA('cost_per_hour', 'Cost per hour', 'num', 'IF({col:hours}>0,{col:cost}/{col:hours},0)', 10),
    CPH('supervisee', 'supervisee_phone', 'Supervisee phone'), CPH('supervisor', 'supervisor_phone', 'Supervisor phone'), CO()], D.sup_log_d(), 500,
    [A('cost', '> 0', 'warn')]))
# 9
SUPD = 'IFERROR(INDEX({range:team.supervised},MATCH({col:clinician},{range:team.name},0))=%s,FALSE)' % YES
tables.append(T('supmonth', 'Supervision by Month', 'Supervision hours owed against logged, by month',
    'One row per clinician and month: client sessions seen; hours logged come from the Supervision Log and the hours owed to date from the ratio, so the debt and the up-to-date flag fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('clinician', 'Clinician', 'clin', 16), C('client_sessions', 'Client sessions', 'int', 10),
    CA('hours_logged', 'Hours logged', 'num', 'SUMIFS({range:suplog.hours},{range:suplog.supervisee},{col:clinician},{range:suplog.date},">="&{col:month},{range:suplog.date},"<"&EDATE({col:month},1))', 9),
    CA('required', 'Hours required', 'num', 'IF(%s,{col:client_sessions}/{set:supervision_ratio},{set:peer_hours_month})' % SUPD, 9),
    CA('owed_to_date', 'Hours owed to date', 'num', 'SUMIFS({range:supmonth.required},{range:supmonth.clinician},{col:clinician},{range:supmonth.month},"<="&{col:month})', 10),
    CA('logged_to_date', 'Hours logged to date', 'num', 'SUMIFS({range:supmonth.hours_logged},{range:supmonth.clinician},{col:clinician},{range:supmonth.month},"<="&{col:month})', 10),
    CA('hours_debt', 'Hours debt', 'num', 'MAX(0,{col:owed_to_date}-{col:logged_to_date})', 9),
    CA('sessions_per_hour', 'Sessions per supervision hour', 'num', 'IF({col:hours_logged}>0,{col:client_sessions}/{col:hours_logged},0)', 11),
    CA('up_flag', 'Supervision check', 'text', 'IF({col:hours_debt}<=0,%s,%s)' % (ck('Up to date'), ck('Behind')), 12), CPH(), CO()], D.sup_month_d(), 300,
    [A('up_flag', '= ' + ck('Behind'), 'warn'), A('up_flag', '= ' + ck('Up to date'), 'good')]))
# 10
tables.append(T('celog', 'Continuing Education Log', 'CE (CPD) log with hours, cost and certificates',
    'One row per course or training: hours, cost, who paid and whether a certificate is on file; only hours with a certificate count towards the yearly target.', [
    C('ce_id', 'CE ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('clinician', 'Clinician', 'clin', 16), LST('kind', 'Kind', 'cek', 14), C('title', 'Title', 'text', 28), C('hours', 'Hours', 'num', 8),
    C('cost', 'Cost', 'int', 9), LST('paid_by', 'Paid by', 'paidby', 11), C('certificate', 'Certificate', 'bool', 10),
    CA('counted_hours', 'Hours counted', 'num', 'IF({col:certificate}=%s,{col:hours},0)' % YES, 9), CA('cost_per_hour', 'Cost per hour', 'num', 'IF({col:hours}>0,{col:cost}/{col:hours},0)', 9), CPH(), CO()], D.ce_log_d(), 300,
    [A('certificate', '= {list:yesno.no}', 'bad')]))
# 11
CEY = '{range:celog.date},">="&DATE({col:year},1,1),{range:celog.date},"<="&DATE({col:year},12,31)'
tables.append(T('ceyear', 'CE by Year', 'CE (CPD) hours against the yearly target',
    'One row per clinician and year: the target hours; hours with a certificate, cost, hours still needed and the pace check fill in by themselves from the log.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('year', 'Year', 'int', 8), LST('clinician', 'Clinician', 'clin', 16), C('target', 'Target hours', 'int', 9),
    CA('hours', 'Hours counted', 'num', 'SUMIFS({range:celog.counted_hours},{range:celog.clinician},{col:clinician},%s)' % CEY, 9),
    CA('cost', 'Cost', 'int', 'SUMIFS({range:celog.cost},{range:celog.clinician},{col:clinician},%s)' % CEY, 9),
    CA('hours_needed', 'Hours still needed', 'num', 'IF({col:year}<YEAR({today}),0,MAX(0,{col:target}-{col:hours}))', 10),
    CA('cost_per_hour', 'Cost per hour', 'num', 'IF({col:hours}>0,{col:cost}/{col:hours},0)', 9),
    CA('pace_flag', 'Pace check', 'text', 'IF({col:year}<YEAR({today}),IF({col:hours}>={col:target},%s,%s),IF({col:hours}>={col:target}*MONTH({today})/12,%s,%s))' % (ck('On pace'), ck('Behind'), ck('On pace'), ck('Behind')), 10),
    CPH(), CO()], D.ce_year_d(), 100, [A('pace_flag', '= ' + ck('Behind'), 'warn'), A('hours_needed', '> 0', 'warn')]))
# 12
tables.append(T('renewals', 'Renewal Register', 'Renewals: licence, insurance and registration',
    'One row per renewal: holder, item, how often, due date and renewed date; days to due, the red or amber status and the act-first rank fill in by themselves.', [
    C('renewal_id', 'Renewal ID', 'text', 10, required=True), LST('holder', 'Holder', 'holder', 18), LST('item', 'Item', 'renk', 26), C('every_months', 'Every months', 'int', 9), C('due_date', 'Due date', 'date', 11),
    C('renewed_on', 'Renewed on', 'date', 11), C('cost', 'Cost', 'money', 10), LST('paid_by', 'Paid by', 'paidby', 11),
    CA('days_to_due', 'Days to due', 'int', 'IF({col:renewed_on}<>"","",{col:due_date}-{today})', 9),
    CA('status', 'Status', 'text', 'IF({col:renewed_on}<>"",%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<={set:renewal_red_days},%s,IF({col:due_date}-{today}<={set:renewal_warn_days},%s,%s))))' % (
        ck('Renewed'), OV, ck('Red'), ck('Amber'), ck('OK')), 10),
    CA('act_rank', 'Act-first rank', 'int', 'IF({col:renewed_on}<>"","",1+SUMPRODUCT(({range:renewals.status}<>'+ck('Renewed')+')*({range:renewals.renewal_id}<>"")*(({range:renewals.due_date}<{col:due_date})+({range:renewals.due_date}={col:due_date})*({range:renewals.renewal_id}<{col:renewal_id}))))', 9),
    CPH('holder', 'holder_phone', 'Holder phone'), STAFF_PH('TH-07', 'coordinator_phone'), STAFF_PH('TH-01', 'owner_phone'), CO()], D.renewals_d(), 300,
    [A('status', '= ' + ck('Red'), 'bad'), A('status', '= ' + OV, 'bad'), A('status', '= ' + ck('Amber'), 'warn'), A('status', '= ' + ck('Renewed'), 'good')]))
# 13
CSTAT = lambda n: tok('cstatus', n)
tables.append(T('consent', 'Consent Records', 'Consent records with the review date',
    'One row per client: when consent was signed and re-signed and whether contact and online sessions are agreed (never the content); the next review date and the review check fill in by themselves.', [
    C('consent_id', 'Consent ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), C('phone', 'Phone', 'text', 18), LST('clinician', 'Clinician', 'clin', 16),
    LST('status', 'Client status', 'cstatus', 12), C('signed_on', 'Consent signed on', 'date', 12), C('contact_ok', 'Contact agreed', 'bool', 9), C('online_ok', 'Online sessions agreed', 'bool', 10), C('reviewed_on', 'Re-signed on', 'date', 11),
    CA('next_review', 'Next review', 'date', 'EDATE(IF({col:reviewed_on}="",{col:signed_on},{col:reviewed_on}),{set:consent_review_months})', 11),
    CA('days_to_review', 'Days to review', 'int', '{col:next_review}-{today}', 9),
    CA('review_check', 'Review check', 'text', 'IF(OR({col:status}=%s,{col:status}=%s),%s,IF({col:next_review}<={today},%s,IF({col:next_review}<={today}+30,%s,%s)))' % (
        CSTAT('Discharged'), CSTAT('Referred out'), ck('Closed'), ck('Review due'), ck('Due in 30 days'), ck('Current')), 13), CPH(), CO()], D.consent_d(), 800,
    [A('review_check', '= ' + ck('Review due'), 'bad'), A('review_check', '= ' + ck('Due in 30 days'), 'warn')]))
# 14
tables.append(T('requests', 'Record Requests', 'Record requests with the deadline',
    'One row per request for a client\'s records: the kind and the date you answered; the deadline, days left and the status fill in by themselves.', [
    C('request_id', 'Request ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('client', 'Client', 'text', 24), C('phone', 'Phone', 'text', 18), LST('kind', 'Kind', 'reqkind', 20), C('sent_on', 'Sent on', 'date', 11),
    CA('due_date', 'Due date', 'date', '{col:date}+{set:request_days}', 11), CA('days_left', 'Days left', 'int', 'IF({col:sent_on}<>"","",{col:due_date}-{today})', 9),
    CA('status', 'Status', 'text', 'IF({col:sent_on}<>"",%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<=7,%s,%s)))' % (SENT, OV, ck('Due soon'), ck('On time')), 11),
    STAFF_PH('TH-07', 'coordinator_phone'), CO()], D.requests_d(), 200,
    [A('status', '= ' + OV, 'bad'), A('status', '= ' + ck('Due soon'), 'warn'), A('status', '= ' + SENT, 'good')]))
# 15
tables.append(T('keep', 'Records Keep-until', 'Records keep-until dates and files to archive',
    'One row per discharged client: years to keep from your own local rules and whether the file is archived; the archive date, keep-until date and the status fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('client_type', 'Client type', 'text', 12), C('discharge_date', 'Discharge date', 'date', 12),
    C('years_to_keep', 'Years to keep', 'int', 9), C('archived', 'Archived', 'bool', 9),
    CA('archive_on', 'Archive on', 'date', 'EDATE({col:discharge_date},{set:archive_after_months})', 11), CA('keep_until', 'Keep until', 'date', 'EDATE({col:discharge_date},12*{col:years_to_keep})', 11),
    CA('status', 'File status', 'text', 'IF({col:archived}=%s,IF({col:keep_until}<={today},%s,%s),IF({col:archive_on}<={today},%s,%s))' % (YES, ck('Past keep-until date'), ck('Archived'), ck('Archive now'), ck('Keep')), 16),
    STAFF_PH('TH-07', 'coordinator_phone'), CO()], D.keep_d(), 800, [A('status', '= ' + ck('Archive now'), 'warn'), A('status', '= ' + ck('Past keep-until date'), 'bad')]))
# 16
tables.append(T('privacy', 'Privacy Checks', 'Monthly privacy check: passwords, cabinets and devices',
    'One row per month: passwords changed, cabinets locked and devices checked, and who did it; the all-done flag fills in by itself (check your own local rules for what to check).', [
    C('check_id', 'Check ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('passwords_changed', 'Passwords changed', 'bool', 10), C('cabinets_locked', 'Cabinets locked', 'bool', 10),
    C('devices_checked', 'Devices checked', 'bool', 10), REF('done_by', 'Done by', 'team.name', 20),
    CA('all_done', 'All done', 'text', 'IF(AND({col:passwords_changed}=%s,{col:cabinets_locked}=%s,{col:devices_checked}=%s),%s,%s)' % (YES, YES, YES, ck('All done'), ck('Incomplete')), 11),
    STAFF_PH('TH-07', 'coordinator_phone'), STAFF_PH('TH-10', 'it_phone', 'IT support phone'), CO()], D.privacy_d(), 100,
    [A('all_done', '= ' + ck('Incomplete'), 'warn'), A('all_done', '= ' + ck('All done'), 'good')]))
# 17
tables.append(T('policies', 'Policy Reviews', 'Policy reviews and days to the next review',
    'One row per policy: when it was last reviewed, how often and by whom; the next review date, days to review and the review check fill in by themselves.', [
    C('policy_id', 'Policy ID', 'text', 9, required=True), C('policy', 'Policy', 'text', 30), C('last_reviewed', 'Last reviewed', 'date', 12), C('every_months', 'Review every months', 'int', 10),
    REF('reviewed_by', 'Reviewed by', 'team.name', 20), CA('next_review', 'Next review', 'date', 'EDATE({col:last_reviewed},{col:every_months})', 11), CA('days_to_review', 'Days to review', 'int', '{col:next_review}-{today}', 9),
    CA('review_check', 'Review check', 'text', 'IF({col:next_review}<={today},%s,IF({col:next_review}<={today}+{set:renewal_warn_days},%s,%s))' % (ck('Review due'), ck('Due soon'), ck('Current')), 12),
    STAFF_PH('TH-07', 'coordinator_phone'), CO()], D.policies_d(), 100, [A('review_check', '= ' + ck('Review due'), 'bad'), A('review_check', '= ' + ck('Due soon'), 'warn')]))
# 18
tables.append(T('incidents', 'Incident and Complaint Log', 'Incident and complaint log (admin facts only)',
    'One row per incident or complaint: the kind, area, action taken and the closing date, never any client detail; days open and the status fill in by themselves.', [
    C('incident_id', 'Incident ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('kind', 'Kind', 'inckind', 18), C('area', 'Area', 'text', 13), C('action_taken', 'Action taken', 'text', 30),
    REF('handled_by', 'Handled by', 'team.name', 20), C('closed_on', 'Closed on', 'date', 11),
    CA('days_open', 'Days open', 'int', 'IF({col:closed_on}="",{today}-{col:date},{col:closed_on}-{col:date})', 9),
    CA('status', 'Status', 'text', 'IF({col:closed_on}="",%s,%s)' % (ck('Open'), ck('Closed')), 10), STAFF_PH('TH-01', 'owner_phone'), CO()], D.incidents_d(), 200,
    [A('status', '= ' + ck('Open'), 'bad')]))
# 19
tables.append(T('clients', 'Clients', 'Clients with status, last session and score currency',
    'One row per client: status, first and last session and the date of the latest outcome score; days since the last session and the score check fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), LST('clinician', 'Clinician', 'clin', 16), LST('service', 'Service', 'csvc', 18), LST('status', 'Status', 'cstatus', 12),
    C('phone', 'Phone', 'text', 18), C('first_session', 'First session', 'date', 11), C('last_session', 'Last session', 'date', 11), C('next_session', 'Next session', 'date', 11), C('last_score_on', 'Latest score on', 'date', 11),
    CA('days_since_last', 'Days since last session', 'int', 'IF({col:last_session}="","",{today}-{col:last_session})', 10),
    CA('score_check', 'Score check', 'text', 'IF({col:status}<>%s,%s,IF({col:last_score_on}="",%s,IF({today}-{col:last_score_on}<={set:review_every_days},%s,%s)))' % (CSTAT('Active'), ck('Not active'), ck('Book review'), ck('Current'), ck('Book review')), 12),
    CPH(), CO()], D.clients_d(), 1000, [A('score_check', '= ' + ck('Book review'), 'warn')]))
# 20
tables.append(T('team', 'Team', 'Team with admin status',
    'One row per person: employed, contract (self-employed) and associate (works under supervision) clinicians, the coordinator and outside contacts; overdue notes, reviews, CE hours and renewals fill in.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 30), C('team', 'Team', 'text', 12), C('pay_type', 'Pay type', 'text', 16), C('phone', 'Phone', 'text', 18),
    C('email', 'Email', 'text', 26), C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'int', 11), C('split_pct', 'Split share', 'pct', 9), C('session_rate', 'Rate per session', 'int', 10),
    C('hourly_rate', 'Hourly rate', 'int', 9), C('session_cap', 'Session cap a week', 'int', 10), C('session_target', 'Session target a week', 'int', 10), C('speciality', 'Speciality', 'text', 30),
    C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11), C('supervised', 'Works under supervision', 'bool', 11),
    CA('notes_overdue', 'Notes overdue', 'int', 'IF({col:session_cap}>0,COUNTIFS({range:notes.clinician},{col:name},{range:notes.note_check},%s),"")' % OV, 9),
    CA('act_rank', 'Act-first rank', 'int', 'IF({col:session_cap}>0,1+COUNTIFS({range:team.notes_overdue},">"&{col:notes_overdue})+COUNTIFS({range:team.notes_overdue},{col:notes_overdue},{range:team.staff_id},"<"&{col:staff_id}),"")', 9),
    CA('reviews_overdue', 'Plan reviews overdue', 'int', 'IF({col:session_cap}>0,COUNTIFS({range:reviews.clinician},{col:name},{range:reviews.status},%s),"")' % OV, 10),
    CA('ce_hours', 'CE hours this year', 'num', 'IF({col:session_cap}>0,SUMIFS({range:celog.counted_hours},{range:celog.clinician},{col:name},{range:celog.date},">="&%s),"")' % JAN1, 10),
    CA('hours_needed', 'CE hours still needed', 'num', 'IF({col:session_cap}>0,MAX(0,{set:ce_target_hours}-{col:ce_hours}),"")', 10),
    CA('hours_owed', 'Supervision hours owed', 'num', 'IF({col:supervised}=%s,SUMIFS({range:supmonth.client_sessions},{range:supmonth.clinician},{col:name})/{set:supervision_ratio},"")' % YES, 10),
    CA('hours_logged', 'Supervision hours logged', 'num', 'IF({col:supervised}=%s,SUMIFS({range:suplog.hours},{range:suplog.supervisee},{col:name}),"")' % YES, 10),
    CA('renewals_open', 'Renewals not done', 'int', 'COUNTIFS({range:renewals.holder},{col:name},{range:renewals.status},"<>"&'+ck('Renewed')+')', 9),
    CA('next_renewal', 'Next renewal due', 'date', 'IF({col:renewals_open}=0,"",SUMPRODUCT(MIN(({range:renewals.holder}={col:name})*({range:renewals.status}<>'+ck('Renewed')+')*({range:renewals.due_date})+(1-({range:renewals.holder}={col:name})*({range:renewals.status}<>'+ck('Renewed')+'))*99999)))', 11),
    STAFF_PH('TH-07', 'coordinator_phone'), STAFF_PH('TH-01', 'owner_phone'), CO()], D.team_d(), 50))
assert len(tables) == 20
