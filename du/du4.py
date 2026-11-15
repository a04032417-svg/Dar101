"""Doula Business suite - part 4: On-Call Capacity and Backup Cover."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du4_lists import *
from du4_tables import settings, tables
from du4_tools import tools

SUITE = 'fx-20261115-doula-business'
NOTE = "Sample wording: adapt it to your own business. Check your local rules for privacy, consent and records."
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def R(t, c): return '{range:%s.%s}' % (t, c)
OS, OE, OD, OB, OEDD = R('oncall', 'oncall_start'), R('oncall', 'oncall_end'), R('oncall', 'doula'), R('oncall', 'backup'), R('oncall', 'edd')
T0 = '{today}'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('due_request_sheet', 'Due Date Request Sheet', 'Due date request with the verdict', 'requests.enquiry_id', F(
        ('Received on', 'requests.date'), ('Name', 'requests.name'), ('Phone', 'requests.phone'), ('Service', 'requests.service'), ('Area', 'requests.area'), ('Estimated due date wanted', 'requests.edd_wanted'),
        ('Source', 'requests.source'), ('Window start', 'requests.window_start'), ('Window end', 'requests.window_end'), ('Clients overlapping', 'requests.overlapping'), ('Due dates that month', 'requests.month_count'),
        ('Doulas free', 'requests.free_doulas'), ('Doulas fully clear', 'requests.clear_doulas'), ('Verdict', 'requests.verdict')) + [
        FF('Agency cap for a month', '{set:agency_cap_month}', 'int'), FF('Days since the request', '%s-%s' % (T0, LK('requests', 'enquiry_id', 'date')), 'int')]),
    FORM('oncall_window_sheet', 'On-Call Window Sheet', 'On-call window of one client', 'oncall.window_id', F(
        ('Client', 'oncall.client'), ('Client phone', 'oncall.phone'), ('Doula', 'oncall.doula'), ('Doula phone', 'oncall.doula_phone'), ('Backup doula', 'oncall.backup'), ('Backup phone', 'oncall.backup_phone'),
        ('Estimated due date', 'oncall.edd'), ('On-call start', 'oncall.oncall_start'), ('On-call end', 'oncall.oncall_end'), ('Window days', 'oncall.window_days'), ('Area', 'oncall.area'),
        ('Window phase', 'oncall.phase'), ('Cover check', 'oncall.cover'), ('Overlap check', 'oncall.overlap_flag'), ('Contact hours', 'oncall.contact_hours'), ('Attended on', 'oncall.attended_on')) + [
        FF('Due dates of the doula that month', 'COUNTIFS(%s,%s,%s,">="&DATE(YEAR(%s),MONTH(%s),1),%s,"<="&EOMONTH(%s,0))' % (OD, LK('oncall', 'window_id', 'doula'), OEDD, LK('oncall', 'window_id', 'edd'), LK('oncall', 'window_id', 'edd'), OEDD, LK('oncall', 'window_id', 'edd')), 'int')]),
    FORM('backup_assign_sheet', 'Backup Assignment Sheet', 'Backup assignment for a window', 'cover.window_id', F(
        ('Client', 'cover.client'), ('Client phone', 'cover.client_phone'), ('Doula', 'cover.doula'), ('Doula phone', 'cover.doula_phone'), ('Backup doula', 'cover.backup'), ('Backup phone', 'cover.backup_phone'),
        ('On-call start', 'cover.oncall_start'), ('On-call end', 'cover.oncall_end'), ('Days to open', 'cover.days_to_open'), ('Backup load that week', 'cover.backup_load'), ('Cover check', 'cover.cover_flag')) + [
        FF('Windows this backup covers, all dates', 'COUNTIFS(%s,%s)' % (OB, LK('cover', 'window_id', 'backup')), 'int'),
        FF('Rota weeks of this backup, last 13 weeks', 'COUNTIFS(%s,%s,%s,">="&(%s-91))' % (R('rota', 'backup'), LK('cover', 'window_id', 'backup'), R('rota', 'week'), T0), 'int'),
        FF('Most windows a backup carries in a week', '{set:backup_load_max}', 'int')]),
    FORM('callout_sheet', 'Backup Call-Out Sheet', 'Backup call-out with the doula pay after the split', 'callouts.birth_id', F(
        ('Date', 'callouts.date'), ('Client', 'callouts.client'), ('Assigned doula', 'callouts.assigned'), ('Backup who attended', 'callouts.backup'), ('Backup phone', 'callouts.backup_phone'), ('Birth part of the package', 'callouts.birth_value'),
        ('Agency share', 'callouts.agency_share'), ('Outcome', 'callouts.outcome'), ('Call-out pay', 'callouts.backup_pay'), ('Agency cut', 'callouts.agency_cut'), ('Doula pay after the split', 'callouts.doula_pay')) + [
        FF('Agency net after overhead and call-out', '%s-{set:agency_cost_client}-%s' % (LK('callouts', 'birth_id', 'agency_cut'), LK('callouts', 'birth_id', 'backup_pay')), 'money'),
        FF('Births this backup attended, all dates', 'COUNTIFS(%s,%s)' % (R('births', 'backup'), LK('callouts', 'birth_id', 'backup')), 'int')]),
    FORM('timeoff_sheet', 'Time-Off Request Sheet', 'Time-off request with the clash check', 'timeoff.timeoff_id', F(
        ('Holder', 'timeoff.holder'), ('Holder phone', 'timeoff.holder_phone'), ('Start', 'timeoff.start'), ('End', 'timeoff.end'), ('Kind', 'timeoff.kind'), ('Days', 'timeoff.days'), ('Windows overlapped', 'timeoff.clashes'), ('Clash check', 'timeoff.status')) + [
        FF('Others away at the same time', 'COUNTIFS(%s,"<="&%s,%s,">="&%s)-1' % (R('timeoff', 'start'), LK('timeoff', 'timeoff_id', 'end'), R('timeoff', 'end'), LK('timeoff', 'timeoff_id', 'start')), 'int'),
        FF('Days away this year by this holder', 'SUMIFS(%s,%s,%s,%s,">="&DATE(YEAR(%s),1,1),%s,"<="&DATE(YEAR(%s),12,31))' % (R('timeoff', 'days'), R('timeoff', 'holder'), LK('timeoff', 'timeoff_id', 'holder'), R('timeoff', 'start'), T0, R('timeoff', 'start'), T0), 'int')]),
    FORM('capacity_sheet', 'Capacity Review Sheet', 'Capacity review of one month', 'capm.month', F(
        ('Months ahead', 'capm.m_ahead'), ('Due dates booked', 'capm.due_dates'), ('Agency cap', 'capm.cap'), ('Doula caps added', 'capm.doula_caps'), ('Free dates', 'capm.free_dates'), ('Cap used', 'capm.utilisation'),
        ('Cap check', 'capm.status'), ('Windows opening', 'capm.windows_opening'), ('Backup stipends', 'capm.stipend'), ('Planned stipends', 'capm.stipend_plan'), ('Call-out pay', 'capm.callout_pay')) + [
        FF('Backup pay in the month', '%s+%s' % (LK('capm', 'month', 'stipend'), LK('capm', 'month', 'callout_pay')), 'money'),
        FF('Due dates in the month a year earlier', 'COUNTIFS(%s,">="&EDATE({pick},-12),%s,"<="&EOMONTH(EDATE({pick},-12),0))' % (OEDD, OEDD), 'int')]),
    FORM('overlap_plan_sheet', 'Overlap Plan Sheet', 'Overlap plan for one month', 'overlap_scn.month', F(
        ('Due dates', 'overlap_scn.due_dates'), ('Doulas with a due date', 'overlap_scn.doulas_busy'), ('Births needing a backup', 'overlap_scn.extra'), ('Backups available', 'overlap_scn.backups'), ('Short by', 'overlap_scn.short_by'),
        ('Verdict', 'overlap_scn.verdict')) + [
        FF('Windows opening that month', 'COUNTIFS(%s,">="&{pick},%s,"<="&EOMONTH({pick},0))' % (OS, OS), 'int'),
        FF('Windows over the limit that month', 'COUNTIFS(%s,">="&{pick},%s,"<="&EOMONTH({pick},0),{range:oncall.overlap_flag},%s)' % (OS, OS, ck('Over the limit')), 'int'),
        FF('Most windows of one doula open at once', 'SUMPRODUCT(MAX((%s>={pick})*(%s<=EOMONTH({pick},0))*COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)))' % (OS, OS, OD, OD, OS, OS, OE, OS), 'int')]),
    FORM('doula_avail_sheet', 'Doula Availability Sheet', 'Availability of one doula in one month', 'capd.row_id', F(
        ('Doula', 'capd.doula'), ('Month', 'capd.month'), ('Due dates booked', 'capd.due_dates'), ('Doula cap', 'capd.cap'), ('Free dates', 'capd.free_dates'), ('Most windows open together', 'capd.peak_overlap'),
        ('Cap check', 'capd.status'), ('Limit check', 'capd.limit_flag'), ('Doula phone', 'capd.doula_phone')) + [
        FF('Time-off days of this doula in the month', 'SUMIFS(%s,%s,%s,%s,">="&%s,%s,"<="&EOMONTH(%s,0))' % (R('timeoff', 'days'), R('timeoff', 'holder'), LK('capd', 'row_id', 'doula'), R('timeoff', 'start'), LK('capd', 'row_id', 'month'), R('timeoff', 'start'), LK('capd', 'row_id', 'month')), 'int'),
        FF('Windows of this doula opening that month', 'COUNTIFS(%s,%s,%s,">="&%s,%s,"<="&EOMONTH(%s,0))' % (OD, LK('capd', 'row_id', 'doula'), OS, LK('capd', 'row_id', 'month'), OS, LK('capd', 'row_id', 'month')), 'int')]),
    FORM('waitlist_date_sheet', 'Waitlist Date Sheet', 'Waitlist entry for a date that is full', 'requests.enquiry_id', F(
        ('Name', 'requests.name'), ('Phone', 'requests.phone'), ('Service', 'requests.service'), ('Area', 'requests.area'), ('Estimated due date wanted', 'requests.edd_wanted'), ('Due dates that month', 'requests.month_count'),
        ('Doulas free', 'requests.free_doulas'), ('Verdict', 'requests.verdict')) + [
        FF('First month with a free date', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),{today})' % (R('capm', 'month'), ck('Open'), R('capm', 'status')), 'date'),
        FF('Other requests for the same month', 'COUNTIFS(%s,">="&DATE(YEAR(%s),MONTH(%s),1),%s,"<="&EOMONTH(%s,0))-1' % (R('requests', 'edd_wanted'), LK('requests', 'enquiry_id', 'edd_wanted'), LK('requests', 'enquiry_id', 'edd_wanted'), R('requests', 'edd_wanted'), LK('requests', 'enquiry_id', 'edd_wanted')), 'int'),
        FF('Free dates left in the month', 'MAX(0,{set:agency_cap_month}-%s)' % LK('requests', 'enquiry_id', 'month_count'), 'int')]),
    FORM('window_opens_sheet', 'Window Opens Sheet', 'Contact sheet for the day a window opens', 'cover.window_id', F(
        ('Client', 'cover.client'), ('Client phone', 'cover.client_phone'), ('Doula', 'cover.doula'), ('Doula phone', 'cover.doula_phone'), ('Backup doula', 'cover.backup'), ('Backup phone', 'cover.backup_phone'),
        ('On-call start', 'cover.oncall_start'), ('On-call end', 'cover.oncall_end'), ('Days to open', 'cover.days_to_open')) + [
        FF('Estimated due date', 'INDEX(%s,MATCH({pick},{range:oncall.window_id},0))' % OEDD, 'date'),
        FF('Other windows of the doula open that day', 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)-1' % (OD, LK('cover', 'window_id', 'doula'), OS, LK('cover', 'window_id', 'oncall_start'), OE, LK('cover', 'window_id', 'oncall_start')), 'int'),
        FF('Window length in days', '%s-%s+1' % (LK('cover', 'window_id', 'oncall_end'), LK('cover', 'window_id', 'oncall_start')), 'int')]),
    FORM('b2b_sheet', 'Back-to-Back Plan Sheet', 'Plan for due dates that sit close together', 'oncall.window_id', F(
        ('Client', 'oncall.client'), ('Doula', 'oncall.doula'), ('Estimated due date', 'oncall.edd'), ('Other due dates close by', 'oncall.b2b'), ('Doula next window opens', 'oncall.next_start'), ('Overlap check', 'oncall.overlap_flag'),
        ('Window days', 'oncall.window_days'), ('Backup doula', 'oncall.backup')) + [
        FF('Days from window end to next opening', '%s-%s' % (LK('oncall', 'window_id', 'next_start'), LK('oncall', 'window_id', 'oncall_end')), 'int'),
        FF('Closest gap you accept, in days', '{set:back_to_back_days}', 'int')]),
    FORM('rota_change_sheet', 'Rota Change Sheet', 'Rota change for one week', 'rota.rota_id', F(
        ('Week starting Monday', 'rota.week'), ('Backup doula', 'rota.backup'), ('Stipend', 'rota.stipend'), ('Windows covered', 'rota.windows'), ('Load check', 'rota.flag'), ('Backup phone', 'rota.backup_phone'), ('Admin phone', 'rota.admin_phone')) + [
        FF('Weeks this backup is on the rota, year', 'COUNTIFS(%s,%s,%s,">="&DATE(YEAR(%s),1,1),%s,"<="&DATE(YEAR(%s),12,31))' % (R('rota', 'backup'), LK('rota', 'rota_id', 'backup'), R('rota', 'week'), T0, R('rota', 'week'), T0), 'int'),
        FF('Stipend of that backup this year', 'SUMIFS(%s,%s,%s,%s,">="&DATE(YEAR(%s),1,1),%s,"<="&DATE(YEAR(%s),12,31))' % (R('rota', 'stipend'), R('rota', 'backup'), LK('rota', 'rota_id', 'backup'), R('rota', 'week'), T0, R('rota', 'week'), T0), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('window_letter', 'On-Call Window Letter', 'On-call window letter for a client', 'oncall.window_id', [
        'On-call window letter of {set:company}, dated {today}. Dear {col:oncall.client}, this letter sets out your on-call window and who to call.',
        'Your doula is {col:oncall.doula}, phone {col:oncall.doula_phone}. Your backup doula is {col:oncall.backup}, phone {col:oncall.backup_phone}. A backup doula is a second doula who attends if the assigned one cannot.',
        'The on-call window is the days around your estimated due date when the doula keeps themselves free. Your estimated due date is {col:oncall.edd}, a date you gave us and we use only to plan the window. Your window starts on {col:oncall.oncall_start} and ends on {col:oncall.oncall_end}, {col:oncall.window_days} days in all.',
        'Please call or write when you need your doula. For anything medical, ask your care provider. This letter sets out dates and contacts only.'], ['Owner-doula', 'Client'], NOTE),
    DOC('backup_intro', 'Backup Introduction Letter', 'Backup doula introduction letter', 'oncall.window_id', [
        'Letter of {set:company}, dated {today}. Dear {col:oncall.client}, we would like you to meet your backup doula, {col:oncall.backup}.',
        'Your doula for the window from {col:oncall.oncall_start} to {col:oncall.oncall_end} is {col:oncall.doula}. {col:oncall.backup} attends only if {col:oncall.doula} cannot, and the agency tells you at once if that happens.',
        'You can reach your backup doula on {col:oncall.backup_phone}. Your doula is on {col:oncall.doula_phone}. Please save both numbers before the window opens.', 'We are glad to look after you.'], ['Owner-doula', 'Client'], NOTE),
    DOC('doula_schedule', 'On-Call Schedule for a Doula', 'On-call schedule for a doula', 'oncall.window_id', [
        'On-call schedule of {set:company}, dated {today}. Doula: {col:oncall.doula}, phone {col:oncall.doula_phone}.',
        'Client: {col:oncall.client}, area {col:oncall.area}. Estimated due date {col:oncall.edd}. Window from {col:oncall.oncall_start} to {col:oncall.oncall_end}, {col:oncall.window_days} days. Backup doula: {col:oncall.backup}, phone {col:oncall.backup_phone}.',
        'Windows of your own that are open on the start day: {col:oncall.overlap}, against a limit of {set:max_oncall_overlap}. Overlap check: {col:oncall.overlap_flag}. Windows in your next 30 days: {col:oncall.load_30}. Your next window opens on {col:oncall.next_start}.',
        'Tell the owner-doula early if you need a backup or a day off. Keep yourself free for the whole window.'], ['Owner-doula', 'Doula'], NOTE),
    DOC('rota_month', 'Backup Rota for the Month', 'Backup rota notice for a week', 'rota.rota_id', [
        'Backup rota of {set:company}, dated {today}. Week starting {col:rota.week}.',
        'Backup doula on the rota: {col:rota.backup}, phone {col:rota.backup_phone}. Weekly stipend: {col:rota.stipend}. Windows the backup covers that week: {col:rota.windows}. Load check: {col:rota.flag}.',
        'The backup keeps themselves free to attend if an assigned doula cannot, and is paid a flat call-out amount when they attend, as set in the backup pay rules. Reply to the admin on {col:rota.admin_phone} if you cannot take the week.'], ['Owner-doula', 'Backup doula'], NOTE),
    DOC('capacity_report', 'Capacity Report', 'Capacity report for the owner-doula', 'capm.month', [
        'Capacity report of {set:company}, dated {today}. Month: {col:capm.month}, {col:capm.m_ahead} months ahead.',
        'Due dates booked: {col:capm.due_dates}. Agency cap: {col:capm.cap}. Free dates: {col:capm.free_dates}. Share of the cap used: {col:capm.utilisation}. Cap check: {col:capm.status}. Doula caps added together: {col:capm.doula_caps}.',
        'Windows opening: {col:capm.windows_opening}. Backup stipends: {col:capm.stipend}, planned {col:capm.stipend_plan}. Backup call-out pay: {col:capm.callout_pay}.',
        'Write the decision below: sell more of this month, waitlist new requests or ask for more backup cover.'], ['Owner-doula', 'Admin'], NOTE),
    DOC('overlap_note', 'Overlap Plan Note', 'Overlap plan note for a month', 'overlap_scn.month', [
        'Overlap plan of {set:company}, dated {today}. Month: {col:overlap_scn.month}.',
        'Due dates in the month: {col:overlap_scn.due_dates}. If all of them land in the same 7 days, each doula attends one, so {col:overlap_scn.extra} births need a backup. Backups available: {col:overlap_scn.backups}. Short by: {col:overlap_scn.short_by}. Verdict: {col:overlap_scn.verdict}.',
        'Decide below who calls the backups, whether to waitlist new requests for the month and which windows to move.'], ['Owner-doula', 'Admin'], NOTE),
    DOC('timeoff_notice', 'Time-Off Notice to Clients', 'Time-off notice to a client', 'clash.timeoff_id', [
        'Notice of {set:company}, dated {today}. Dear {col:clash.first_client}, a short notice about your on-call window.',
        '{col:clash.holder} is away from {col:clash.start} to {col:clash.end}. Your window opens on {col:clash.first_start}. Your doula is {col:clash.first_doula} and your backup doula is {col:clash.first_backup}.',
        'If the dates change we tell you at once. You can reach us on {col:clash.owner_phone}. For anything medical, ask your care provider.'], ['Owner-doula', 'Client'], NOTE),
    DOC('date_response', 'Date Request Response', 'Response to a due-date request', 'requests.enquiry_id', [
        'Letter of {set:company}, dated {today}. Dear {col:requests.name}, thank you for your request of {col:requests.date}.',
        'You asked about a due date around {col:requests.edd_wanted}. The on-call window would run from {col:requests.window_start} to {col:requests.window_end}. We have {col:requests.month_count} due dates booked that month and {col:requests.free_doulas} doulas free. Our answer: {col:requests.verdict}.',
        'If a date is not free we can add you to the waitlist and tell you at once when a place opens. Please call {col:requests.phone} or write back to confirm.'], ['Owner-doula', 'Client'], NOTE),
    DOC('waitlist_confirm', 'Waitlist Confirmation', 'Waitlist confirmation for a due date', 'requests.enquiry_id', [
        'Waitlist confirmation of {set:company}, dated {today}. Dear {col:requests.name}, your name is on our waitlist.',
        'Estimated due date: {col:requests.edd_wanted}, a date you gave us. Service: {col:requests.service}. Area: {col:requests.area}. Received on {col:requests.date}.',
        'A place on the waitlist is not a promise of a place. When a date opens we call you on {col:requests.phone} and you then have a few days to answer. Please tell us if your plans change.'], ['Owner-doula', 'Client'], NOTE),
    DOC('callout_statement', 'Backup Call-Out Statement', 'Backup call-out statement', 'callouts.birth_id', [
        'Backup call-out statement of {set:company}, dated {today}. Backup doula: {col:callouts.backup}. Date: {col:callouts.date}. Client: {col:callouts.client}.',
        'Assigned doula: {col:callouts.assigned}. Outcome: {col:callouts.outcome}. Birth part of the package: {col:callouts.birth_value}. Agency share: {col:callouts.agency_share}, which is {col:callouts.agency_cut}.',
        'Call-out pay for the backup: {col:callouts.backup_pay}. Doula pay after the split and the call-out: {col:callouts.doula_pay}. Amounts are before any tax. Check your contract terms.'], ['Owner-doula', 'Backup doula'], NOTE),
    DOC('window_reminder', 'On-Call Window Reminder', 'On-call window reminder', 'cover.window_id', [
        'Reminder of {set:company}, dated {today}. Dear {col:cover.client}, your on-call window opens in {col:cover.days_to_open} days.',
        'It runs from {col:cover.oncall_start} to {col:cover.oncall_end}. Your doula is {col:cover.doula}, phone {col:cover.doula_phone}. Your backup doula is {col:cover.backup}, phone {col:cover.backup_phone}.',
        'Please save both numbers and tell us if your estimated due date changes. For anything medical, ask your care provider.'], ['Owner-doula', 'Client'], NOTE),
    DOC('busy_summary', 'Busiest Weeks Summary', 'Busiest weeks summary', 'busy.rank', [
        'Busiest weeks summary of {set:company}, dated {today}. Rank {col:busy.rank}.',
        'Week starting {col:busy.week}: {col:busy.clients_on_call} clients on call, {col:busy.doulas_needed} doulas needed, and at most {col:busy.peak_overlap} windows of one doula. Limit check: {col:busy.flag}, against a limit of {set:max_oncall_overlap}.',
        'Use this page to plan backup cover, time off and new bookings for the week. Write the actions below.'], ['Owner-doula', 'Admin'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('window_opens', 'Window Opens Steps', 'oncall', 'oncall.oncall_start', [('Confirm the estimated due date with the client', -14), ('Send the on-call window letter', -7), ('Check the backup is named and has the dates', -7), ('Tell the client the window opens in 3 days', -3), ('Check the doula is free for the whole window', -1), ('Message the client the day the window opens', 0), ('Ask for a contact update after one week', 7)]),
    CHK('backup_named', 'Backup Named Steps', 'oncall', 'oncall.oncall_start', [('Check the backup load in the window weeks', -60), ('Ask the backup doula if they can take the window', -50), ('Write the backup name in On-Call Windows', -45), ('Send the backup introduction letter to the client', -30), ('Give the backup the client dates and phone', -21), ('Re-check the backup is free before the window opens', -7)]),
    CHK('weekly_check', 'Weekly On-Call Check Steps', 'rota', 'rota.week', [('Look at the clients on call this week', 0), ('Check the backup on the rota has no clash', 0), ('Check each doula is within the overlap limit', 0), ('Call the doulas with 2 or more windows', 1), ('Look at the windows opening in the next 14 days', 1), ('Write the actions in the weekly notes', 2)]),
    CHK('monthly_capacity', 'Monthly Capacity Review Steps', 'capm', 'capm.month', [('Count the due dates booked for the month', -28), ('Compare them with the agency cap', -28), ('Check each doula against their own cap', -21), ('Decide: sell more, waitlist or decline', -14), ('Check the backup rota for the month', -14), ('Update the date requests that wait', -7), ('Write the decisions in the review notes', 0)]),
    CHK('new_request', 'New Due Date Request Steps', 'requests', 'requests.date', [('Write the request in Date Requests', 0), ('Read the verdict and the doulas free', 0), ('Reply to the enquirer the same day', 0), ('Offer the waitlist if the date is full', 1), ('Book a consultation if a doula is free', 2), ('Hold the date for the client if they say yes', 3), ('Close the request if nothing comes back', 14)]),
    CHK('overlap_alert', 'Overlap Alert Steps', 'oncall', 'oncall.oncall_start', [('Find the doula with windows above the limit', -30), ('Ask a backup to cover one of the windows', -28), ('Name the backup on the window', -28), ('Tell the clients who their backup is', -21), ('Check the doula agrees to the plan', -14), ('Check the plan again before the window opens', -3)]),
    CHK('callout_run', 'Backup Call-Out Steps', 'births', 'births.date', [('Write the birth with the backup who attended', 0), ('Thank the backup doula and the assigned doula', 0), ('Work out the call-out pay and the doula share', 2), ('Add the call-out to the next pay run', 3), ('Tell the admin about the extra pay', 3), ('Check the backup rest days before the next call', 7)]),
    CHK('timeoff_run', 'Time-Off Request Steps', 'timeoff', 'timeoff.start', [('Write the request in Time Off', -60), ('Check the clash with on-call windows', -60), ('Name a swap for any window that clashes', -45), ('Tell the clients who are affected', -30), ('Approve the time off in writing', -28), ('Remind the swap doula a week before', -7)]),
    CHK('rota_change', 'Rota Change Steps', 'rota', 'rota.week', [('Write the change on the Backup Rota', -14), ('Ask the new backup if they can take the week', -14), ('Tell the backup who is stepping off', -10), ('Tell the clients with windows that week', -7), ('Update the admin and the owner-doula', -7), ('Check the rota again on Monday', 0)]),
    CHK('b2b_plan', 'Back-to-Back Plan Steps', 'oncall', 'oncall.edd', [('Find due dates of one doula that sit close together', -90), ('Decide who attends first if both call', -75), ('Name a backup for the second window', -60), ('Tell both clients the plan in plain words', -45), ('Check the rest days between the births', -30), ('Check the plan again at the window start', -14)]),
    CHK('peak_plan', 'Peak Season Plan Steps', 'capm', 'capm.month', [('Look at the same month last year', -120), ('Forecast the due dates with your own trend', -105), ('Count the backups you need', -90), ('Recruit or book extra backup cover', -75), ('Set the cap for the peak month', -60), ('Tell the team the peak dates', -45), ('Review the plan one month before', -30)]),
    CHK('window_closes', 'Window Closes Steps', 'oncall', 'oncall.oncall_end', [('Check the window dates with the doula', -3), ('Send a message that the window is closing', -1), ('Close the window and free the doula', 0), ('Write the contact hours in On-Call Windows', 1), ('Thank the backup doula', 2), ('Ask the client for a review after the postpartum visits', 14)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('c_window', 'Client: your on-call window', 'oncall', 'oncall.phone', 'Hello {client}, your on-call window starts on {oncall_start} and ends on {oncall_end}. Your doula is {doula}. {company}'),
    M('c_backup', 'Client: your backup doula', 'oncall', 'oncall.phone', 'Hello {client}, your backup doula is {backup}. You can reach them on {backup_phone}. Your doula is {doula}. {company}'),
    M('c_3days', 'Client: your window opens in 3 days', 'oncall', 'oncall.phone', 'Hello {client}, your on-call window opens on {oncall_start}, in {days_to_open} days. {doula} is keeping the dates free. {company}'),
    M('c_tomorrow', 'Client: your window opens tomorrow', 'oncall', 'oncall.phone', 'Hello {client}, your window opens tomorrow, {oncall_start}. Your doula is {doula}, phone {doula_phone}. {company}'),
    M('c_away', 'Client: your doula is away', 'clash', 'clash.client_phone', 'Hello {first_client}, {holder} is away from {start} to {end}. Your backup doula is {first_backup}. We tell you at once if anything changes. {company}'),
    M('c_new_backup', 'Client: we changed your backup', 'oncall', 'oncall.phone', 'Hello {client}, we have changed your backup doula. The new name is {backup}, phone {backup_phone}. Your doula stays {doula}. {company}'),
    M('c_confirm_edd', 'Client: confirm your estimated due date', 'clients', 'clients.phone', 'Hello {client}, please confirm your estimated due date of {edd}. We use it only to plan your on-call window. {company}'),
    M('c_moved', 'Client: your window moved', 'clients', 'clients.phone', 'Hello {client}, after the new due date of {edd} your on-call window is now {oncall_start} to {oncall_end}. {company}'),
    M('c_closed', 'Client: your window has closed', 'oncall', 'oncall.phone', 'Hello {client}, your on-call window closed on {oncall_end}. Thank you from {doula} and everyone at {company}.'),
    M('e_space', 'Enquirer: we have space', 'requests', 'requests.phone', 'Hello {name}, we have space around {edd_wanted}. May we call you to talk about your doula and your on-call window? {company}'),
    M('e_full', 'Enquirer: we are full, join the waitlist', 'requests', 'requests.phone', 'Hello {name}, we are full around {edd_wanted}. May we add you to the waitlist? We tell you as soon as a date opens. {company}'),
    M('e_opened', 'Enquirer: a date has opened up', 'requests', 'requests.phone', 'Hello {name}, a date has opened up around {edd_wanted}. Would you like us to hold it for you? Please reply today. {company}'),
    M('o_month', 'Owner: due dates this month', 'capm', 'capm.owner_phone', 'Hello, {month} has {due_dates} due dates against a cap of {cap}. Cap check: {status}. {company}'),
    M('o_overlap', 'Owner: a doula has overlapping windows', 'capd', 'capd.owner_phone', 'Hello, {doula} has {peak_overlap} windows open together in {month}. Limit check: {limit_flag}. Please name a backup. {company}'),
    M('o_nobackup', 'Owner: a client has no backup', 'cover', 'cover.owner_phone', 'Hello, {client} has no backup named and the window opens on {oncall_start}. Please name a backup today. {company}'),
    M('o_full', 'Owner: the cap is full', 'capm', 'capm.owner_phone', 'Hello, {month} has {due_dates} due dates and the cap is {cap}. Decline or waitlist new requests for that month. {company}'),
    M('o_room', 'Owner: room for more clients', 'capm', 'capm.owner_phone', 'Hello, {month} has room for {free_dates} more clients. Time to market that month. {company}'),
    M('o_scn', 'Owner: overlap scenario is short', 'overlap_scn', 'overlap_scn.owner_phone', 'Hello, the overlap scenario for {month} is short by {short_by}: {extra} births need a backup and {backups} backups are available. {company}'),
    M('o_timeoff', 'Owner: time off clashes', 'clash', 'clash.owner_phone', 'Hello, the time off of {holder} from {start} to {end} clashes with {first_client}. Please name a swap. {company}'),
    M('o_callout', 'Owner: a backup call-out cost', 'callouts', 'callouts.owner_phone', 'Hello, the call-out for {client} on {date} paid {backup} {backup_pay}. Doula pay after the split is {doula_pay}. {company}'),
    M('o_busy', 'Owner: the busiest week', 'busy', 'busy.owner_phone', 'Hello, rank {rank} week starts {week} with {clients_on_call} clients on call and {doulas_needed} doulas needed. {company}'),
    M('d_oncall', 'Doula: you are on call', 'oncall', 'oncall.doula_phone', 'Hello {doula}, you are on call for {client} from {oncall_start} to {oncall_end}. Backup doula: {backup}. {company}'),
    M('d_next', 'Doula: your next windows', 'oncall', 'oncall.doula_phone', 'Hello {doula}, your window for {client} opens on {oncall_start}. Your next window after it opens on {next_start}. {company}'),
    M('d_overlap', 'Doula: windows overlap', 'oncall', 'oncall.doula_phone', 'Hello {doula}, you have {overlap} windows open on {oncall_start}. Please tell us if you need a backup. {company}'),
    M('d_timeoff_ok', 'Doula: your time off is approved', 'timeoff', 'timeoff.holder_phone', 'Hello {holder}, your time off from {start} to {end} is approved. {company}'),
    M('d_avail', 'Doula: confirm your availability', 'capd', 'capd.doula_phone', 'Hello {doula}, please confirm your availability for {month}. You have {due_dates} due dates and a cap of {cap}. {company}'),
    M('b_rota', 'Backup doula: you are on the rota', 'rota', 'rota.backup_phone', 'Hello {backup}, you are on the rota for the week of {week}. The stipend is {stipend}. Please keep the week free. {company}'),
    M('b_named', 'Backup doula: you are named backup', 'oncall', 'oncall.backup_phone', 'Hello {backup}, {client} enters the on-call window on {oncall_start} and you are named backup. The window ends on {oncall_end}. {company}'),
    M('b_callout', 'Backup doula: your call-out pay', 'callouts', 'callouts.backup_phone', 'Hello {backup}, your call-out for {client} on {date} is {backup_pay}. It goes into the next pay run. {company}'),
    M('b_load', 'Backup doula: your rota weeks', 'bload', 'bload.backup_phone', 'Hello {backup}, in the week of {week} you cover {windows_covered} windows. Load check: {flag}. {company}'),
    M('a_week', 'Admin: windows open this week', 'weekly', 'weekly.admin_phone', 'Hello, in the week of {week} there are {windows_open} windows open and {due_dates} due dates. {company}'),
    M('a_nobackup', 'Admin: clients without a backup', 'cover', 'cover.admin_phone', 'Hello, {client} has no backup named and the window opens on {oncall_start}. Please call the owner-doula about it. {company}'),
    M('a_rota', 'Admin: the backup rota is ready', 'rota', 'rota.admin_phone', 'Hello, the rota for the week of {week} names {backup}. Please send the week notice and the stipend of {stipend}. {company}'),
    M('x_acc', 'Accountant: stipends and call-outs', 'capm', 'capm.accountant_phone', 'Hello, for {month} the backup stipends are {stipend} and the call-out pay is {callout_pay}. Amounts are before any tax. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def INMON(k): return '%s,">="&EDATE(%s,%d),%s,"<="&EOMONTH(EDATE(%s,%d),0)' % (OEDD, MS, k, OEDD, MS, k)
WIN = lambda c: R('oncall', c)
kpis = [
    KPI('Clients on call today', 'COUNTIFS(%s,"<="&%s,%s,">="&%s)' % (OS, T0, OE, T0), 'int'),
    KPI('Windows opening, next 14 days', 'COUNTIFS(%s,">="&%s,%s,"<="&(%s+14))' % (OS, T0, OS, T0), 'int'),
    KPI('Windows open, next 30 days', 'COUNTIFS(%s,"<="&(%s+30),%s,">="&%s)' % (OS, T0, OE, T0), 'int'),
    KPI('Busiest day, next 90 days', 'SUMPRODUCT(MAX(({range:daily.day_no}>=0)*({range:daily.day_no}<=90)*COUNTIFS(%s,"<="&({today}+{range:daily.day_no}),%s,">="&({today}+{range:daily.day_no}))))' % (OS, OE), 'int'),
    KPI('Days a doula has 2+ windows, 90d', 'COUNTIFS({range:daily.day_no},">=0",{range:daily.day_no},"<=90",{range:daily.two_plus},1)', 'int'),
    KPI('Days a doula has 3+ windows, 90d', 'COUNTIFS({range:daily.day_no},">=0",{range:daily.day_no},"<=90",{range:daily.three_plus},1)', 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Windows over the limit, 12 months', 'COUNTIFS({range:oncall.overlap_flag},%s,%s,">="&%s,%s,"<="&(%s+365))' % (ck('Over the limit'), OS, T0, OS, T0), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Due dates this month', 'COUNTIFS(%s)' % INMON(0), 'int'), KPI('Due dates next month', 'COUNTIFS(%s)' % INMON(1), 'int'),
    KPI('Due dates, next 3 months', 'COUNTIFS(%s,">="&%s,%s,"<="&EDATE(%s,3))' % (OEDD, T0, OEDD, T0), 'int'),
    KPI('Cap used this month', 'SUMIFS({range:capm.utilisation},{range:capm.m_ahead},0)', 'pct'), KPI('Cap used next month', 'SUMIFS({range:capm.utilisation},{range:capm.m_ahead},1)', 'pct'),
    KPI('Free due dates, next 3 months', 'SUMIFS({range:capm.free_dates},{range:capm.m_ahead},">=1",{range:capm.m_ahead},"<=3")', 'int'),
    KPI('Free due dates, next 12 months', 'SUM({range:capm.free_dates})', 'int'),
    KPI('Months left open, next 12', 'COUNTIFS({range:capm.status},%s)' % ck('Open'), 'int'), KPI('Months full, next 12', 'COUNTIFS({range:capm.status},%s)' % ck('Full'), 'int'),
    KPI('Windows without a named backup', 'COUNTIFS({range:oncall.no_backup},1,%s,">="&%s)' % (OE, T0), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Windows without a backup, soon', 'COUNTIFS(%s,"",%s,">="&%s,%s,"<="&(%s+{set:cover_alert_days}))' % (OB, OS, T0, OS, T0), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Backup named share, open windows', 'IFERROR(COUNTIFS({range:oncall.no_backup},0,%s,">="&%s)/COUNTIFS(%s,">="&%s),0)' % (OE, T0, OE, T0), 'pct'),
    KPI('Backups on call this week', 'COUNTIFS({range:rota.week},">="&(%s-6),{range:rota.week},"<="&%s)' % (T0, T0), 'int'),
    KPI('Backup load this week', 'SUMIFS({range:rota.windows},{range:rota.week},">="&(%s-6),{range:rota.week},"<="&%s)' % (T0, T0), 'int'),
    KPI('Backup call-outs, last 12 months', 'COUNTIFS({range:births.backup_used},%s,{range:births.date},">="&(%s-365),{range:births.date},"<="&%s)' % (YES, T0, T0), 'int'),
    KPI('Backup use rate, last 12 months', 'IFERROR(COUNTIFS({range:births.backup_used},%s,{range:births.date},">="&(%s-365),{range:births.date},"<="&%s)/COUNTIFS({range:births.date},">="&(%s-365),{range:births.date},"<="&%s),0)' % (YES, T0, T0, T0, T0), 'pct'),
    KPI('Backup pay, last 12 months', 'SUMIFS({range:rota.stipend},{range:rota.week},">="&(%s-365),{range:rota.week},"<="&%s)+SUMIFS({range:callouts.backup_pay},{range:callouts.date},">="&(%s-365),{range:callouts.date},"<="&%s)' % (T0, T0, T0, T0), 'money'),
    KPI('Time-off days, next 90 days', 'SUMIFS({range:timeoff.days},{range:timeoff.start},">="&%s,{range:timeoff.start},"<="&(%s+90))' % (T0, T0), 'int'),
    KPI('Time-off clashes', 'COUNTIFS({range:clash.flag},%s)' % ck('Clash'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Doula with the most windows, 30 days', 'IFERROR(INDEX(%s,MATCH(MAX({range:oncall.load_30}),{range:oncall.load_30},0)),"-")' % OD, 'text'),
    KPI('Back-to-back due dates, next 90 days', 'COUNTIFS({range:oncall.b2b},">0",%s,">="&%s,%s,"<="&(%s+90))' % (OEDD, T0, OEDD, T0), 'int'),
    KPI('Average on-call days per window', 'IFERROR(AVERAGE({range:oncall.window_days}),0)', 'num'),
    KPI('Date requests waiting', 'COUNTIFS({range:requests.answered},%s)' % NO, 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "On-Call Dashboard", "kpis": kpis,
    "monthly": {"title": "Contact hours, birth hours, days off and stipends", "date": "oncall.oncall_start", "series": [
        {"label": "Contact hours", "sum": "oncall.contact_hours", "date": "oncall.oncall_start"}, {"label": "Birth hours", "sum": "births.hours", "date": "births.date"},
        {"label": "Time-off days", "sum": "timeoff.days", "date": "timeoff.start"}, {"label": "Backup stipends", "sum": "rota.stipend", "date": "rota.week"}]},
    "breakdowns": [{"title": "Clients by status", "by": "clients.status", "agg": "count"}, {"title": "Windows by doula", "by": "oncall.doula", "agg": "count"},
                   {"title": "Windows by backup", "by": "oncall.backup", "agg": "count"}, {"title": "Time off by kind", "by": "timeoff.kind", "agg": "count"}]}
insights = {"filters": [{"label": "Doula", "list": "bdoula"}, {"label": "Backup doula", "list": "backup"}, {"label": "Area", "list": "area"}],
    "gauges": [
        {"title": "Open windows with a named backup", "num": AGG('count', 'oncall', where=[('oncall_end', '>=', '{today}'), ('no_backup', '=', 0)]), "den": AGG('count', 'oncall', where=[('oncall_end', '>=', '{today}')])},
        {"title": "Windows within the overlap limit", "num": AGG('count', 'oncall', where=[('overlap', '<=', '{set:max_oncall_overlap}')]), "den": AGG('count', 'oncall')},
        {"title": "Cap used next month", "num": AGG('sum', 'capm', 'capm.due_dates', where=[('m_ahead', '=', 1)]), "den": AGG('sum', 'capm', 'capm.cap', where=[('m_ahead', '=', 1)])},
        {"title": "Backup stipend against the plan", "num": AGG('sum', 'capm', 'capm.stipend', where=[('m_ahead', '=', 0)]), "den": AGG('sum', 'capm', 'capm.stipend_plan', where=[('m_ahead', '=', 0)])},
        {"title": "Time off without a clash", "num": AGG('count', 'clash', where=[('flag', '=', ck('Safe to book'))]), "den": AGG('count', 'clash', where=[('flag', '<>', ck('Past block'))])},
        {"title": "Closed windows with contact hours", "num": AGG('count', 'oncall', where=[('oncall_end', '<', '{today}'), ('contact_hours', '>', 0)]), "den": AGG('count', 'oncall', where=[('oncall_end', '<', '{today}')])}],
    "charts": [
        CHART('Windows opening per month', 'column', 'month', [AGG('count', 'oncall', date='oncall.oncall_start', label='Windows opening')]),
        CHART('Due dates per month', 'column', 'month', [AGG('count', 'oncall', date='oncall.edd', label='Due dates')]),
        CHART('Due dates by doula', 'bar', 'clients.doula', [AGG('count', 'clients', label='Due dates')]),
        CHART('Due dates by area', 'bar', 'oncall.area', [AGG('count', 'oncall', label='Due dates')]),
        CHART('Due dates by kind', 'bar', 'clients.kind', [AGG('count', 'clients', label='Clients')]),
        CHART('Due dates by status', 'bar', 'clients.status', [AGG('count', 'clients', label='Clients')]),
        CHART('On-call windows by doula', 'bar', 'oncall.doula', [AGG('count', 'oncall', label='Windows')]),
        CHART('On-call windows by backup', 'bar', 'oncall.backup', [AGG('count', 'oncall', label='Windows')]),
        CHART('Windows without a backup by doula', 'bar', 'oncall.doula', [AGG('count', 'oncall', where=[('no_backup', '=', 1)], label='Without a backup')]),
        CHART('Backup weeks per backup', 'bar', 'rota.backup', [AGG('count', 'rota', label='Rota weeks')]),
        CHART('Backup stipend per month', 'column', 'month', [AGG('sum', 'rota', 'rota.stipend', date='rota.week', label='Stipend')]),
        CHART('Births attended per month', 'column', 'month', [AGG('count', 'births', date='births.date', label='Births attended')]),
        CHART('Births by assigned doula', 'bar', 'births.assigned', [AGG('count', 'births', label='Births')]),
        CHART('Backup used by backup', 'bar', 'births.backup', [AGG('count', 'births', where=[('backup_used', '=', YES)], label='Births with a backup')]),
        CHART('Time off by kind', 'bar', 'timeoff.kind', [AGG('count', 'timeoff', label='Blocks')]),
        CHART('Time-off days per month', 'column', 'month', [AGG('sum', 'timeoff', 'timeoff.days', date='timeoff.start', label='Days off')]),
        CHART('Time off by holder', 'bar', 'timeoff.holder', [AGG('count', 'timeoff', label='Blocks')]),
        CHART('Contact hours per month', 'line', 'month', [AGG('sum', 'oncall', 'oncall.contact_hours', date='oncall.oncall_start', label='Contact hours')]),
        CHART('Contact hours by doula', 'bar', 'oncall.doula', [AGG('sum', 'oncall', 'oncall.contact_hours', label='Contact hours')]),
        CHART('Windows attended by doula', 'bar', 'oncall.doula', [AGG('count', 'oncall', where=[('attended_on', '>', 0)], label='Windows attended')]),
        CHART('Due dates by source', 'bar', 'clients.source', [AGG('count', 'clients', label='Clients')]),
        CHART('Date requests by service', 'bar', 'requests.service', [AGG('count', 'requests', label='Requests')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "On-call forecast", "why": "every client window laid over the next 6 months, day by day and week by week, with the busiest weeks ranked and the verdict", "where": "On-Call Forecast"},
    {"name": "Can I take this client?", "why": "type a due date and a doula and see the windows it overlaps, the monthly cap used and whether a backup is free: yes, yes with backup booked or decline", "where": "Can I Take This Client"},
    {"name": "Monthly cap and utilisation", "why": "due dates booked against your own cap for 12 months, the months left open and the free dates, with a what-if cap", "where": "Monthly Cap Utilisation"},
    {"name": "Overlap scenario test", "why": "all clients due in one month attended in the same 7 days: how many births need a backup and whether your backups are enough", "where": "Overlap Scenario Test"},
    {"name": "Backup cover check", "why": "every window with its backup, the backup load that week and the windows with no backup named, soonest first", "where": "Backup Cover Check"},
    {"name": "Backup pay and missed-birth tool", "why": "flat, share or hourly pay for a backup, what the doula and the agency keep, and the rule when the backup cannot attend", "where": "Backup Pay Calculator"},
    {"name": "Time-off planner", "why": "blackout dates tested against windows and due dates, with the first client affected and the earliest clash-free start", "where": "Time-Off Planner"},
    {"name": "Daily on-call load", "why": "clients on call, doulas on call and the busiest doula for every day, flagged at 2 and 3 windows", "where": "Daily On-Call Load"},
    {"name": "Busiest weeks ranked", "why": "the weeks ahead ranked by clients on call and the most windows of one doula, so backup cover goes where it counts", "where": "Busiest Weeks"},
    {"name": "Unnamed backup alerts", "why": "the soonest window without a backup, the client, the doula and the days left, so one call fixes it today", "where": "Unnamed Backup Alerts"},
    {"name": "Peak season planner", "why": "due dates by month this year and last year with your own trend, and the backups needed in the peak month", "where": "Peak Season Planner"}]
competitors = [
    {"what": "free client-tracker template", "lacks": "lists clients and due dates but never draws the on-call window, counts overlaps per doula or checks who is the backup"},
    {"what": "single-sheet on-call calendar", "lacks": "shows who is on call by hand with no monthly cap, no backup load and no answer to can I take this client"},
    {"what": "subscription practice-management software", "lacks": "charges every month for client records but has no overlap scenario, no backup pay split and no capacity forecast by doula"},
    {"what": "generic shift-rota spreadsheet", "lacks": "plans shifts of fixed hours, not 28-day windows around a due date that move with every client"},
    {"what": "paper diary and shared calendar", "lacks": "holds dates but cannot warn about three windows at once, a window without a backup or time off that clashes"}]
guide = [
    'Open Settings and type your agency name and your own limits in the yellow cells: days before and after the due date, the most windows of one doula at once, your monthly cap and the backup pay.',
    'Fill Team and Doulas first. A solo doula keeps one row in each and leaves the backup sheets empty: the same sheets still count windows, caps and time off.',
    'Write each client in Clients (name, area, due date, doula, backup) and each client window in On-Call Windows. The window days, the cover check and the overlap check fill in by themselves.',
    'Watch Daily On-Call Load, Weekly On-Call Load and Busiest Weeks. They count the windows for you and flag 2 or more windows of one doula and the limit you set.',
    'Use Capacity by Month and Capacity by Doula and Month before you say yes: they show the due dates booked against the cap for every month and every doula.',
    'Check Backup Cover Check and Backup Load by Week every Monday. They list windows with no backup named and backups carrying too many windows.',
    'Type each new request in Date Requests. The verdict says yes, yes with backup booked, or decline or waitlist, from the windows and caps already booked.',
    'Log time off in Time Off and look at Time-Off Clashes. Backup Rota and Backup Call-Outs hold the weekly stipend and the pay when a backup attends.',
    'Use Overlap Scenario and Backup Named Share to test a month when every birth lands in the same week and to see how many windows still need a backup.',
    f'Use the {len(tools)} calculators for decisions: take the client, cap the month, test the overlap, rank the backups, pay a backup, plan time off and forecast call-outs.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the dates already written in.',
    'Read the On-Call Dashboard and its charts every week. The sheet counts hours, dates, money and capacity only; it holds no medical detail and promises no outcome.']
listing = {"title": "Doula Business On-Call Schedule and Backup Cover Excel Template: Capacity Planner, Overlap Check, Backup Rota, Time Off",
    "headline": "See who is on call, when, and who covers, before you say yes",
    "tags": ["doula business", "doula template", "on call schedule", "backup doula", "doula capacity", "doula excel", "birth doula", "postpartum doula", "doula agency", "client tracker", "capacity planner", "rota planner", "doula planner"],
    "description": ("Run the on-call side of a doula business in one Excel workbook. Built for an owner-doula who also takes clients, an agency with contracted and backup doulas, or a solo doula who wants the same sheets with one doula and no backup rota. "
        "A doula is a non-medical support person who helps a client before, during or after a birth. The on-call window is the days around the estimated due date when the doula keeps themselves free, and a backup doula is a second doula who attends if the assigned one cannot.\n\n"
        "On-Call Windows holds the window of every client with the doula, the backup, the dates and the contact hours; the window days, the cover check and the overlap check fill in by themselves. Daily On-Call Load, Weekly On-Call Load and Busiest Weeks count the windows for you and flag two or more windows of one doula. "
        "Capacity by Month and Capacity by Doula and Month set due dates booked against your own caps. Backup Cover Check, Backup Load by Week and the Backup Rota show every window with its backup. Date Requests answers each new request: yes, yes with backup booked, or decline or waitlist.\n\n"
        f"{len(tools)} calculators cover the on-call forecast, can I take this client, the monthly cap, an overlap scenario, backup cover, backup pay when a backup attends, a time-off planner, backup ranking, window length, rota balance, back-to-back due dates, income left open, unnamed backup alerts, a swap finder, a call-out forecast, freed dates and the peak season. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to clients, enquirers, doulas, backup doulas, the admin and the accountant.\n\n"
        "This is part four of the Doula Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Clients appear by name, area and due date only, with no medical detail. It helps you keep track of dates, hours, money and capacity and does not promise results. Check your local rules for privacy, contracts and records."),
    "features": ["On-call forecast by day and week", "Can I take this client verdict", "Monthly cap and utilisation by doula", "Overlap scenario for a full month", "Backup cover check with load by week", "Backup pay and call-out statements",
                 "Time-off planner with clash check", f"{len(tools)} calculators for capacity decisions", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Works for a solo doula or an agency"]}
HINTS = {}
s = spec(id=f'{SUITE}-p4', slug='doula-business-oncall', profession='Doula Business', name='On-Call Capacity and Backup Cover',
         tagline='See who is on call, when, and who covers, before you say yes', price_usd=29,
         colors={"primary": "#4A3F6B", "accent": "#E8A87C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 4, "of": 8, "focus": "On-call capacity and backup cover"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'du4.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
