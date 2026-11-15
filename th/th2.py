"""Therapy Private Practice suite - part 2: Scheduling, Caseload and Rooms."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th2_lists import *
from th2_tables import settings, tables
from th2_tools import tools

SUITE = 'fx-20261115-therapy-practice'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
YES = '{list:yesno.yes}'
SS = lambda x: tok('sstatus', x)
def F(*pairs): return [FV(a, b) for a, b in pairs]
def pk(tbl, idc, col): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (tbl, col, tbl, idc)

forms = [
    FORM('session_sheet', 'Session Booking Sheet', 'Session with room, fee and back-to-back flag', 'sessions.session_id', F(
        ('Date', 'sessions.date'), ('Time', 'sessions.time'), ('Weekday', 'sessions.weekday'), ('Client', 'sessions.client'), ('Client phone', 'sessions.phone'), ('Client type', 'sessions.client_type'), ('Service', 'sessions.service'),
        ('Clinician', 'sessions.clinician'), ('Format', 'sessions.format'), ('Room', 'sessions.room'), ('Minutes', 'sessions.minutes'), ('Status', 'sessions.status'), ('Fee', 'sessions.fee'), ('End time', 'sessions.end_time'),
        ('Back-to-back', 'sessions.back_to_back')) + [
        FF('Sessions of this clinician on the day', 'COUNTIFS({range:sessions.clinician},%s,{range:sessions.date},%s)' % (pk('sessions', 'session_id', 'clinician'), pk('sessions', 'session_id', 'date')), 'int')]),
    FORM('recurring_sheet', 'Recurring Booking Sheet', 'Recurring client with rhythm and next session', 'caseload.client_id', F(
        ('Client', 'caseload.client'), ('Client phone', 'caseload.phone'), ('Clinician', 'caseload.clinician'), ('Service', 'caseload.service'), ('Frequency', 'caseload.frequency'), ('Format', 'caseload.format'),
        ('Usual weekday', 'caseload.weekday'), ('Usual time', 'caseload.time'), ('First session', 'caseload.first_session'), ('Last session', 'caseload.last_session'), ('Next session', 'caseload.next_session'),
        ('Days between sessions', 'caseload.interval_days'), ('Sessions per week', 'caseload.weekly_load'), ('Next session check', 'caseload.next_flag')) + [
        FF('Clients of this clinician', 'COUNTIFS({range:caseload.clinician},%s)' % pk('caseload', 'client_id', 'clinician'), 'int')]),
    FORM('cancel_sheet', 'Cancellation Sheet', 'Cancellation or no-show with fee and rebooking', 'cancels.session_id', F(
        ('Date', 'cancels.date'), ('Client', 'cancels.client'), ('Clinician', 'cancels.clinician'), ('Status', 'cancels.status'), ('Cancel reason', 'cancels.cancel_reason'), ('Hours of notice', 'cancels.notice_hours'),
        ('Notice check', 'cancels.notice_flag'), ('Fee', 'cancels.fee'), ('Fee waived', 'cancels.fee_waived'), ('Fee charged', 'cancels.fee_charged'), ('Rebooked check', 'cancels.rebook_flag')) + [
        FF('Missed or cancelled, this client', 'COUNTIFS({range:cancels.client},%s)' % pk('cancels', 'session_id', 'client'), 'int')]),
    FORM('waiver_sheet', 'Fee Waiver Sheet', 'Waived late-cancel fee with limit check', 'waivers.waiver_id', F(
        ('Session', 'waivers.session_id'), ('Date', 'waivers.date'), ('Client', 'waivers.client'), ('Fee', 'waivers.fee'), ('Waived by', 'waivers.waived_by'), ('Reason', 'waivers.reason'),
        ('Amount given up', 'waivers.fee_given_up'), ('Waivers this year', 'waivers.times_year'), ('Limit check', 'waivers.limit_flag')) + [
        FF('All waivers, last 12 months', 'COUNTIFS({range:waivers.date},">="&({today}-365),{range:waivers.date},"<="&{today})', 'int')]),
    FORM('list_sheet', 'Cancellation List Sheet', 'Client waiting for an earlier slot', 'cancel_list.list_id', F(
        ('Client', 'cancel_list.client'), ('Client phone', 'cancel_list.phone'), ('Clinician', 'cancel_list.clinician'), ('Service', 'cancel_list.service'), ('Wants', 'cancel_list.wants'), ('Preferred days', 'cancel_list.preferred_days'),
        ('Added on', 'cancel_list.added_on'), ('Offered on', 'cancel_list.offered_on'), ('Filled', 'cancel_list.filled'), ('List status', 'cancel_list.list_status'), ('Days on list', 'cancel_list.days_on_list')) + [
        FF('People waiting on the list', 'COUNTIFS({range:cancel_list.list_status},%s)' % ca('Waiting'), 'int')]),
    FORM('room_sheet', 'Room Booking Sheet', 'Room booking with end time and clash check', 'room_bookings.booking_id', F(
        ('Date', 'room_bookings.date'), ('Time', 'room_bookings.time'), ('Room', 'room_bookings.room'), ('Clinician', 'room_bookings.clinician'), ('Service', 'room_bookings.service'), ('Use', 'room_bookings.use'),
        ('Minutes', 'room_bookings.minutes'), ('End time', 'room_bookings.end_time'), ('Clash check', 'room_bookings.clash')) + [
        FF('Bookings in this room on the day', 'COUNTIFS({range:room_bookings.room},%s,{range:room_bookings.date},%s)' % (pk('room_bookings', 'booking_id', 'room'), pk('room_bookings', 'booking_id', 'date')), 'int')]),
    FORM('online_sheet', 'Online Session Sheet', 'Online session with details sent and problems', 'online.session_id', F(
        ('Date', 'online.date'), ('Client', 'online.client'), ('Client phone', 'online.phone'), ('Clinician', 'online.clinician'), ('Service', 'online.service'), ('Minutes', 'online.minutes'),
        ('Details sent', 'online.details_sent'), ('Connection problem', 'online.connection_problem'), ('Minutes lost', 'online.minutes_lost'), ('Problem check', 'online.problem_flag'), ('Share lost', 'online.lost_share')) + [
        FF('Connection problems, last 30 days', 'COUNTIFS({range:online.connection_problem},%s,{range:online.date},">="&({today}-30))' % YES, 'int')]),
    FORM('absence_sheet', 'Absence Cover Sheet', 'Clinician absence with cover', 'absences.absence_id', F(
        ('Week', 'absences.week'), ('Clinician', 'absences.clinician'), ('Kind', 'absences.kind'), ('Days', 'absences.days'), ('Sessions moved', 'absences.sessions_moved'), ('Cover by', 'absences.cover_by'),
        ('Absence status', 'absences.status'), ('Cover check', 'absences.cover_flag'), ('Clinician phone', 'absences.phone')) + [
        FF('Absence weeks of this clinician', 'COUNTIFS({range:absences.clinician},%s)' % pk('absences', 'absence_id', 'clinician'), 'int')]),
    FORM('rebook_sheet', 'Rebooking Call Sheet', 'Client to call about the next session', 'rebook.client_id', F(
        ('Client', 'rebook.client'), ('Client phone', 'rebook.phone'), ('Clinician', 'rebook.clinician'), ('Frequency', 'rebook.frequency'), ('Last session', 'rebook.last_session'), ('Expected next session', 'rebook.expected_next'),
        ('Days late', 'rebook.days_late'), ('Rebooking check', 'rebook.rebook_flag'), ('Act-first rank', 'rebook.act_rank')) + [
        FF('Clients to call now', 'COUNTIFS({range:rebook.rebook_flag},%s)' % cb('Book now'), 'int')]),
    FORM('diary_sheet', 'Weekly Diary Sheet', 'Clinician week against cap and target band', 'clin_weeks.cw_id', F(
        ('Week', 'clin_weeks.week'), ('Clinician', 'clin_weeks.clinician'), ('Session cap', 'clin_weeks.cap'), ('Days away', 'clin_weeks.days_away'), ('Cap this week', 'clin_weeks.eff_cap'), ('Booked', 'clin_weeks.booked'),
        ('Free slots', 'clin_weeks.free_slots'), ('Booked share of cap', 'clin_weeks.share_of_cap'), ('Back-to-back', 'clin_weeks.back_to_back'), ('Online or phone', 'clin_weeks.online'), ('Load check', 'clin_weeks.cap_flag'),
        ('Missed and late-cancelled share', 'clin_weeks.missed_share')) + [
        FF('Clinicians above the cap that week', 'COUNTIFS({range:clin_weeks.week},%s,{range:clin_weeks.cap_flag},%s)' % (pk('clin_weeks', 'cw_id', 'week'), ca('Over cap')), 'int')]),
    FORM('sublet_sheet', 'Sublet Booking Sheet', 'Sublet hours and rate for a tenant', 'sublets.sublet_id', F(
        ('Month', 'sublets.month'), ('Tenant', 'sublets.tenant'), ('Room', 'sublets.room'), ('Hours', 'sublets.hours'), ('Rate', 'sublets.rate'), ('Amount', 'sublets.amount'), ('Tenant phone', 'sublets.tenant_phone')) + [
        FF('Hours of this tenant, all months', 'SUMIFS({range:sublets.hours},{range:sublets.tenant},%s)' % pk('sublets', 'sublet_id', 'tenant'), 'num'),
        FF('Margin on the rate over room cost', '%s/%s-1' % (pk('sublets', 'sublet_id', 'rate'), '({set:room_cost_hour}+3)'), 'pct')]),
    FORM('sublet_invoice_sheet', 'Sublet Invoice Sheet', 'Sublet invoice with payment status', 'sublets.sublet_id', F(
        ('Tenant', 'sublets.tenant'), ('Month', 'sublets.month'), ('Amount', 'sublets.amount'), ('Invoiced on', 'sublets.invoiced_on'), ('Paid on', 'sublets.paid_on'), ('Status', 'sublets.status'),
        ('Days to pay', 'sublets.days_to_pay'), ('Payment check', 'sublets.pay_flag')) + [
        FF('Unpaid invoices of this tenant', 'COUNTIFS({range:sublets.tenant},%s,{range:sublets.status},%s)' % (pk('sublets', 'sublet_id', 'tenant'), cb('Invoiced')), 'int')]),
]
assert len(forms) == 12
documents = [
    DOC('confirm_doc', 'Appointment Confirmation', 'Appointment confirmation for a client', 'sessions.session_id', [
        'Appointment confirmation of {set:company}, dated {today}. Client: {col:sessions.client}.',
        'Your session is on {col:sessions.date} ({col:sessions.weekday}) at {col:sessions.time}, {col:sessions.minutes} minutes, with {col:sessions.clinician}. Service: {col:sessions.service}. Format: {col:sessions.format}. Room: {col:sessions.room}. Session fee: {col:sessions.fee}.',
        'Please tell us at least {set:late_cancel_hours} hours before the session if you cannot come. A later change may carry a late-cancel fee of {set:late_fee_pct} of the session fee.', 'Reply to this confirmation if any detail is wrong.'], ['Practice', 'Client'], NOTE),
    DOC('policy_doc', 'Cancellation Policy', 'Cancellation and missed-session policy for a client', 'caseload.client_id', [
        'Cancellation and missed-session policy of {set:company}, dated {today}. Client: {col:caseload.client}, seen by {col:caseload.clinician}, {col:caseload.frequency}.',
        'A session cancelled with at least {set:late_cancel_hours} hours of notice carries no fee. A session cancelled with less notice (a late cancel), or missed without notice (a no-show), carries a fee of {set:late_fee_pct} of the session fee.',
        'The first late cancel in a year can be waived. After {set:waiver_limit} waived late fees in a year the practice reviews the waiver. A session you move yourself with enough notice is a reschedule and carries no fee.', 'Reminders are sent {set:reminder_hours} hours before each session.'], ['Practice', 'Client'], NOTE),
    DOC('fee_notice_doc', 'Late-Cancel Fee Notice', 'Late-cancel fee notice', 'cancels.session_id', [
        'Late-cancel fee notice of {set:company}, dated {today}. Client: {col:cancels.client}. Session {col:cancels.session_id} on {col:cancels.date} with {col:cancels.clinician}.',
        'Status: {col:cancels.status}. Hours of notice given: {col:cancels.notice_hours}. Notice check: {col:cancels.notice_flag}. Session fee: {col:cancels.fee}.',
        'Late-cancel fee charged: {col:cancels.fee_charged}, which is {set:late_fee_pct} of the session fee. Fee waived: {col:cancels.fee_given_up}.', 'The fee is added to your next invoice. Please speak to the practice if you would like it reviewed.'], ['Practice', 'Client'], NOTE),
    DOC('waiver_doc', 'Fee Waiver Note', 'Fee waiver note', 'waivers.waiver_id', [
        'Fee waiver note of {set:company}, dated {today}. Waiver {col:waivers.waiver_id} for session {col:waivers.session_id} on {col:waivers.date}. Client: {col:waivers.client}.',
        'Session fee: {col:waivers.fee}. Amount waived: {col:waivers.fee_given_up}. Waived by {col:waivers.waived_by}. Reason: {col:waivers.reason}.',
        'Waivers for this client in the last 12 months: {col:waivers.times_year}. Limit check: {col:waivers.limit_flag}. The practice limit is {set:waiver_limit} a year before a review.', 'The waiver is recorded and does not change the policy for later sessions.'], ['Practice', 'Approver'], NOTE),
    DOC('schedule_doc', 'Clinician Weekly Schedule', 'Weekly schedule for a clinician', 'clin_weeks.cw_id', [
        'Weekly schedule of {set:company}, dated {today}. Clinician: {col:clin_weeks.clinician}. Week of {col:clin_weeks.week}.',
        'Session cap {col:clin_weeks.cap}, days away {col:clin_weeks.days_away}, cap this week {col:clin_weeks.eff_cap}. Sessions booked: {col:clin_weeks.booked}. Free slots: {col:clin_weeks.free_slots}. Booked share of cap: {col:clin_weeks.share_of_cap}.',
        'Load check: {col:clin_weeks.cap_flag}. Target band: {set:band_low} to {set:band_high} sessions a week. Back-to-back sessions: {col:clin_weeks.back_to_back}. Online or phone sessions: {col:clin_weeks.online}.', 'Sessions above the cap are moved to the next free week or to another clinician.'], ['Coordinator', 'Clinician'], NOTE),
    DOC('room_day_doc', 'Daily Room Sheet', 'Daily room sheet for one booking', 'room_bookings.booking_id', [
        'Daily room sheet of {set:company}, dated {today}. Booking {col:room_bookings.booking_id}: {col:room_bookings.room} on {col:room_bookings.date}.',
        'From {col:room_bookings.time} to {col:room_bookings.end_time} ({col:room_bookings.minutes} minutes). Use: {col:room_bookings.use}. Clinician: {col:room_bookings.clinician}. Service: {col:room_bookings.service}. Clash check: {col:room_bookings.clash}.',
        'Reset the room before the next booking: {set:buffer_minutes} minutes for chairs, tissues, toys and a clean surface. Report a clash to the coordinator at once.'], ['Coordinator', 'Cleaner'], NOTE),
    DOC('online_doc', 'Online Session Guide', 'Online session guide for a client', 'online.session_id', [
        'Online session guide of {set:company}, dated {today}. Client: {col:online.client}. Session {col:online.session_id} on {col:online.date}, {col:online.minutes} minutes with {col:online.clinician}.',
        'Before the session: choose a quiet private place, check that your connection is stable, charge your device and use headphones if you can. The link and details are sent to you by e-mail.',
        'If the call drops: wait two minutes and reconnect with the same link. If you cannot, call the practice and your clinician will phone you. Minutes lost to a technical problem are not charged again.', 'Details sent: {col:online.details_sent}. Problem check: {col:online.problem_flag}.'], ['Practice', 'Client'], NOTE),
    DOC('absence_doc', 'Absence Notice', 'Clinician absence notice to clients', 'absences.absence_id', [
        'Absence notice of {set:company}, dated {today}. Your clinician, {col:absences.clinician}, is away in the week of {col:absences.week} ({col:absences.days} days, {col:absences.kind}).',
        '{col:absences.sessions_moved} sessions are affected. Cover check: {col:absences.cover_flag}. Cover clinician: {col:absences.cover_by}.',
        'We will call you to offer a session with the cover clinician or a new time. There is no late-cancel fee for a session moved because of an absence.', 'Thank you for your patience.'], ['Practice', 'Clinician'], NOTE),
    DOC('closure_doc', 'Practice Closure Notice', 'Practice closure notice for a week', 'clin_weeks.cw_id', [
        'Practice closure notice of {set:company}, dated {today}. Week of {col:clin_weeks.week}: {col:clin_weeks.days_away} days away for {col:clin_weeks.clinician}.',
        'Sessions booked that week: {col:clin_weeks.booked}. Cap that week: {col:clin_weeks.eff_cap}. Sessions affected are moved to the weeks before or after.',
        'Clients are told at least two weeks before the closure. In an urgent need, clients are given the contact details of an outside service.', 'The next regular session of every client is booked before the closure.'], ['Practice', 'Owner'], NOTE),
    DOC('sublet_terms_doc', 'Sublet Agreement Summary', 'Sublet agreement summary (adapt to your own terms)', 'sublets.sublet_id', [
        'Sublet agreement summary of {set:company}, dated {today}. Tenant: {col:sublets.tenant}. Room: {col:sublets.room}.',
        'Rate per hour: {col:sublets.rate}. Hours in {col:sublets.month}: {col:sublets.hours}. Amount for the month: {col:sublets.amount}. The tenant uses the room only for their own clients and leaves it reset.',
        'Invoices are sent after the month ends and are due within 14 days. The practice may change the rate with notice. This summary does not replace your written contract.', 'Check your own local rules and your contract terms.'], ['Practice', 'Tenant'], NOTE),
    DOC('sublet_invoice_doc', 'Sublet Invoice', 'Sublet invoice for a month', 'sublets.sublet_id', [
        'Sublet invoice of {set:company}, dated {today}. Tenant: {col:sublets.tenant}. Invoice for {col:sublets.month}, invoiced on {col:sublets.invoiced_on}.',
        'Room: {col:sublets.room}. Hours: {col:sublets.hours} at {col:sublets.rate} an hour. Amount due: {col:sublets.amount}. Status: {col:sublets.status}. Payment check: {col:sublets.pay_flag}.',
        'Please pay within 14 days of the invoice date. Paid on: {col:sublets.paid_on}.'], ['Practice', 'Tenant'], NOTE),
    DOC('room_report_doc', 'Room Use Report', 'Monthly room use report for one room', 'room_months.row_id', [
        'Monthly room use report of {set:company}, dated {today}. Room: {col:room_months.room}. Month: {col:room_months.month}.',
        'Open hours: {col:room_months.open_hours}. Session hours: {col:room_months.session_hours}. Group hours: {col:room_months.group_hours}. Sublet hours: {col:room_months.sublet_hours}. Used hours: {col:room_months.used_hours}. Free hours: {col:room_months.free_hours}.',
        'Room use: {col:room_months.use_share} against a target of {set:target_room_use}. Use check: {col:room_months.use_flag}. Sessions in the room: {col:room_months.sessions}.', 'Free hours are offered to a sublet tenant, to a group program or to online work.'], ['Coordinator', 'Owner'], NOTE),
]
assert len(documents) == 12
checklists = [
    CHK('recurring_run', 'Recurring Client Booking Steps', 'caseload', 'caseload.first_session', [('Agree the weekday, time and rhythm with the client', -7), ('Check the clinician has a free slot at that time', -7), ('Book the room for every session', -5), ('Book the first four sessions in the diary', -3), ('Send the appointment confirmation', -2), ('Send the cancellation policy', -2), ('Set the reminder for each session', -1), ('Check the caseload sheet shows the next session', 7)]),
    CHK('diary_run', 'Daily Diary Check Steps', 'diary', 'diary.date', [('Open the diary for the day', 0), ('Check that every session has a room', 0), ('Look for back-to-back sessions and add a break', 0), ('Confirm the sessions of the day with the clients', -1), ('Offer free slots to the cancellation list', 0), ('Mark sessions held, late cancelled or missed', 1)]),
    CHK('reset_run', 'Room Reset Steps', 'room_bookings', 'room_bookings.date', [('Check the next booking for the room', 0), ('Clear tissues, cups and notes', 0), ('Reset the chairs and the toys', 0), ('Air the room and check the light and heating', 0), ('Tell the clinician the room is ready', 0)]),
    CHK('online_run', 'Online Session Set-up Steps', 'online', 'online.date', [('Send the session link and details by e-mail', -2), ('Send the guide for online sessions', -2), ('Remind the client to find a quiet private place', -1), ('Test the clinician connection', 0), ('Record any connection problem and minutes lost', 1)]),
    CHK('late_cancel_run', 'Late Cancel or No-Show Steps', 'cancels', 'cancels.date', [('Mark the session late cancel or no-show', 0), ('Check the hours of notice against the rule', 0), ('Check the client history of late cancels', 0), ('Decide to charge or waive the fee', 1), ('Send the fee notice or the waiver text', 1), ('Offer the client a new time', 2), ('Offer the free slot to the cancellation list', 0)]),
    CHK('waiver_run', 'Fee Waiver Review Steps', 'waivers', 'waivers.date', [('Read the reason for each waiver', 0), ('Count waivers per client in the last 12 months', 0), ('Flag clients over the waiver limit', 1), ('Talk to the clinician about repeat waivers', 3), ('Record the decision on the fee waiver note', 5)]),
    CHK('cover_run', 'Clinician Absence Cover Steps', 'absences', 'absences.week', [('Count the sessions in the absence week', -28), ('Check the free slots of the other clinicians', -28), ('Tell clients about the absence', -21), ('Offer cover or a new time', -14), ('Book the cover sessions and rooms', -10), ('Send the handover to the cover clinician', -7), ('Check that every affected session is moved or cancelled', -3)]),
    CHK('closure_run', 'Practice Closure Weeks Steps', 'clin_weeks', 'clin_weeks.week', [('Set the closure dates', -42), ('Count the sessions that fall in the closure', -35), ('Tell clients the closure dates', -28), ('Move or cancel the affected sessions', -21), ('Update the diary and the rooms', -14), ('Send the closure notice', -14), ('Book the first sessions after the closure', -7)]),
    CHK('capacity_run', 'Weekly Capacity Review Steps', 'clin_weeks', 'clin_weeks.week', [('Open Clinician Capacity for the next two weeks', -7), ('List clinicians above the target band', -7), ('Move sessions above the cap', -6), ('Check clinicians below the band for new clients', -5), ('Check the free slots against the waitlist', -4), ('Send the weekly capacity report', -3)]),
    CHK('rebook_run', 'Rebooking Gap Review Steps', 'rebook', 'rebook.last_session', [('List clients with no next session', 7), ('Call the client with the most days late first', 9), ('Offer the usual weekday and time', 9), ('Record the call result', 10), ('Send a text if there is no answer', 12), ('Review clients not rebooked after two calls', 21)]),
    CHK('tenant_run', 'New Sublet Tenant Steps', 'sublets', 'sublets.month', [('Agree the room, the hours and the rate', -14), ('Send the sublet agreement summary', -12), ('Check the tenant liability insurance', -10), ('Give the tenant the room rules', -7), ('Add the tenant and the rate to the sheets', -7), ('Book the first room hours', -5), ('Check the first week with the tenant', 7)]),
    CHK('billing_run', 'Monthly Sublet Billing Steps', 'sublets', 'sublets.month', [('Total the hours of each tenant', 30), ('Check the hours against the room bookings', 30), ('Create the sublet invoices', 31), ('Send each invoice', 32), ('Record the payments', 45), ('Send a reminder for unpaid invoices', 46)]),
]
assert len(checklists) == 12
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('c_reminder', 'Client: a reminder of your session', 'sessions', 'sessions.phone', 'Hello {client}, a reminder of your session on {date} at {time} with {clinician}. Please tell us as early as you can if you need to change it. Reception team.'),
    M('c_confirm', 'Client: please confirm your session', 'sessions', 'sessions.phone', 'Hello {client}, please confirm your session on {date} at {time} with {clinician} by replying yes. Reception team.'),
    M('c_online', 'Client: your session is now online', 'sessions', 'sessions.phone', 'Hello {client}, your session on {date} at {time} with {clinician} is now online. The details come by e-mail. Please choose a quiet private place. Reception team.'),
    M('c_cancelled', 'Client: your session is cancelled', 'sessions', 'sessions.phone', 'Hello {client}, your session on {date} at {time} with {clinician} is cancelled as agreed. Tell us when you would like a new time. Reception team.'),
    M('c_missed', 'Client: we missed you, please rebook', 'cancels', 'cancels.phone', 'Hello {client}, we missed you at your session on {date} with {clinician}. Please call us to rebook. Reception team.'),
    M('c_latefee', 'Client: a late-cancel fee applies', 'cancels', 'cancels.phone', 'Hello {client}, a late-cancel fee of {fee_charged} applies to your session on {date}, cancelled with {notice_hours} hours of notice. Please speak to us if you would like to talk it through. Reception team.'),
    M('c_waived', 'Client: the late-cancel fee was waived', 'cancels', 'cancels.phone', 'Hello {client}, the late-cancel fee of {fee_given_up} for your session on {date} was waived this time. Reception team.'),
    M('c_earlier', 'Client: an earlier time is free', 'cancel_list', 'cancel_list.phone', 'Hello {client}, an earlier time with {clinician} is free on {offered_on}. Reply to take it, or we keep you on the list. Reception team.'),
    M('c_away', 'Client: your clinician is away', 'sessions', 'sessions.phone', 'Hello {client}, your clinician {clinician} is away, so your session is moved to {date} at {time}. Please reply to confirm. Reception team.'),
    M('c_closed', 'Client: the practice is closed', 'caseload', 'caseload.phone', 'Hello {client}, the practice is closed for the holidays. Your next session with {clinician} is on {next_session}. Reception team.'),
    M('c_regular', 'Client: your new regular time', 'caseload', 'caseload.phone', 'Hello {client}, your new regular time is {weekday} at {time}, {frequency}, with {clinician}. Your next session is on {next_session}. Reception team.'),
    M('c_room', 'Client: your session room changed', 'sessions', 'sessions.phone', 'Hello {client}, your session on {date} at {time} has moved to {room}. Reception team.'),
    M('c_book', 'Client: please book your next session', 'rebook', 'rebook.phone', 'Hello {client}, please book your next session with {clinician}. Your last session was on {last_session}. Reply with a day and time that suit you. Reception team.'),
    M('c_details', 'Client: online session details sent', 'online', 'online.phone', 'Hello {client}, the details of your online session on {date} with {clinician} are in your e-mail. If you cannot find them, tell us. Reception team.'),
    M('k_diary', 'Clinician: your diary for next week', 'clin_weeks', 'clin_weeks.clinician_phone', 'Hello {clinician}, your diary for the week of {week} is ready: {booked} sessions booked against a cap of {eff_cap}, with {free_slots} free slots. Reception team.'),
    M('k_overcap', 'Clinician: you are over your weekly cap', 'clin_weeks', 'clin_weeks.clinician_phone', 'Hello {clinician}, you are over your weekly cap in the week of {week}: {booked} sessions booked against a cap of {eff_cap}. Please tell us which sessions can move. Reception team.'),
    M('k_free', 'Clinician: a client cancelled, slot free', 'cancels', 'cancels.clinician_phone', 'Hello {clinician}, {client} cancelled the session on {date}. Your slot is free and we will offer it to the cancellation list. Reception team.'),
    M('k_noshow', 'Clinician: a no-show today', 'sessions', 'sessions.clinician_phone', 'Hello {clinician}, {client} did not attend the session on {date} at {time}. Please tell us how you would like us to follow up. Reception team.'),
    M('k_cover', 'Clinician: cover for your clients', 'absences', 'absences.phone', 'Hello {clinician}, we are arranging cover for your clients in the week of {week}, {sessions_moved} sessions to move. Please send your handover and confirm the cover clinician. Reception team.'),
    M('k_room', 'Clinician: a room change', 'room_bookings', 'room_bookings.clinician_phone', 'Hello {clinician}, your booking on {date} at {time} has moved to {room}. Reception team.'),
    M('o_fill', 'Coordinator: fill the cancelled slot', 'cancels', 'cancels.coord_phone', 'Hello {coord}, please fill the cancelled slot on {date} for {clinician} from the cancellation list. {client} cancelled with {notice_hours} hours of notice.'),
    M('o_confirm', 'Coordinator: confirm the sessions', 'sessions', 'sessions.coord_phone', 'Hello {coord}, please confirm the session of {client} on {date} at {time} with {clinician}.'),
    M('o_clash', 'Coordinator: a room clash', 'room_bookings', 'room_bookings.coord_phone', 'Hello {coord}, room clash in {room} on {date} at {time}. Booking {booking_id} needs another room or time.'),
    M('o_online', 'Coordinator: an online session problem', 'online', 'online.coord_phone', 'Hello {coord}, a problem was reported in the online session of {client} on {date} with {clinician}: {minutes_lost} minutes lost. Please call the client.'),
    M('o_nonext', 'Coordinator: client has no next session', 'rebook', 'rebook.coord_phone', 'Hello {coord}, {client} has no next session booked. The last session with {clinician} was on {last_session}, {days_late} days late. Please call to rebook.'),
    M('w_roomuse', 'Owner: room use for the month', 'room_months', 'room_months.owner_phone', 'Hello {owner}, room use in {room} for {month} is {use_share}, with {free_hours} free hours.'),
    M('w_noshows', 'Owner: no-shows rose', 'clin_weeks', 'clin_weeks.owner_phone', 'Hello {owner}, no-shows rose: {clinician} had {no_shows} no-shows and {late_cancels} late cancels in the week of {week}, a missed share of {missed_share}.'),
    M('w_capacity', 'Owner: weekly capacity report ready', 'clin_weeks', 'clin_weeks.owner_phone', 'Hello {owner}, the weekly capacity report is ready. Week of {week}: {clinician} has {booked} sessions against a cap of {eff_cap}, {share_of_cap} of the cap.'),
    M('w_overcap', 'Owner: a clinician is over cap', 'clin_weeks', 'clin_weeks.owner_phone', 'Hello {owner}, {clinician} is over cap in the week of {week}: {booked} sessions booked against a cap of {eff_cap}. Please agree which sessions move.'),
    M('t_invoice', 'Tenant: your sublet invoice', 'sublets', 'sublets.tenant_phone', 'Hello {tenant}, your sublet invoice for {month} is {amount}: {hours} hours in {room} at {rate} an hour. Reception team.'),
    M('t_booked', 'Tenant: your room booking is confirmed', 'sublets', 'sublets.tenant_phone', 'Hello {tenant}, your room booking is confirmed: {room} for {hours} hours in {month} at {rate} an hour. Reception team.'),
    M('t_remind', 'Tenant: a payment reminder', 'sublets', 'sublets.tenant_phone', 'Hello {tenant}, a payment reminder for {month}: {amount} was invoiced on {invoiced_on}. Please pay or tell us when you will. Reception team.'),
    M('t_notfree', 'Tenant: the room is not free', 'sublets', 'sublets.tenant_phone', 'Hello {tenant}, {room} is not free for the time you asked for in {month}. We can offer another room at {rate} an hour. Reception team.'),
    M('x_reset', 'Cleaner: an extra room reset is needed', 'room_bookings', 'room_bookings.cleaner_phone', 'Hello {cleaner}, an extra room reset is needed in {room} on {date} before {time}. Reception team.'),
]
assert len(messages) == 34, len(messages)

MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'
WK0 = '({today}-WEEKDAY({today},2)+1)'
def CW(col, a, b): return 'SUMIFS({range:clin_weeks.%s},{range:clin_weeks.week},">="&(%s+%d),{range:clin_weeks.week},"<"&(%s+%d))' % (col, WK0, a, WK0, b)
def D30(c): return '{range:%s},">="&({today}-30),{range:%s},"<="&{today}' % (c, c)
def PAST13(col): return 'SUMIFS({range:clin_weeks.%s},{range:clin_weeks.week},">="&(%s-91),{range:clin_weeks.week},"<"&%s)' % (col, WK0, WK0)
def RATE(num): return 'IFERROR((%s)/%s,0)' % (num, PAST13('booked'))
def RM(col, a, b): return 'SUMIFS({range:room_months.%s},{range:room_months.month},">="&%s,{range:room_months.month},"<"&%s)' % (col, a, b)
M3 = 'EDATE(%s,-3)' % MS
kpis = [
    KPI('Sessions this week', CW('booked', 0, 7), 'int'),
    KPI('Sessions booked next week', CW('booked', 7, 14), 'int'),
    KPI('Sessions booked next 4 weeks', CW('booked', 7, 35), 'int'),
    KPI('Sessions attended, last 30 days', 'COUNTIFS({range:sessions.status},%s,%s)' % (SS('Attended'), D30('sessions.date')), 'int'),
    KPI('Online share, last 30 days', 'IFERROR((COUNTIFS({range:sessions.status},%s,{range:sessions.format},%s,%s)+COUNTIFS({range:sessions.status},%s,{range:sessions.format},%s,%s))/COUNTIFS({range:sessions.status},%s,%s),0)' % (
        SS('Attended'), tok('fmt', 'Online'), D30('sessions.date'), SS('Attended'), tok('fmt', 'Phone'), D30('sessions.date'), SS('Attended'), D30('sessions.date')), 'pct'),
    KPI('No-Show Rate, last 90 days', RATE(PAST13('no_shows')), 'pct'),
    KPI('Late Cancellation Rate, last 90 days', RATE(PAST13('late_cancels')), 'pct'),
    KPI('Any Cancellation Rate, last 90 days', RATE(PAST13('cancelled') + '+' + PAST13('late_cancels')), 'pct'),
    KPI('Missed and late-cancelled, 30 days', 'IFERROR((COUNTIFS({range:sessions.status},%s,%s)+COUNTIFS({range:sessions.status},%s,%s))/COUNTIFS(%s),0)' % (SS('Late cancel'), D30('sessions.date'), SS('No-show'), D30('sessions.date'), D30('sessions.date')), 'pct', alert={"when": "> {set:target_missed}", "style": "bad"}),
    KPI('Reschedule share, last 90 days', RATE(PAST13('rescheduled')), 'pct'),
    KPI('Late-cancel fees charged, 30 days', 'SUMIFS({range:cancels.fee_charged},%s)' % D30('cancels.date'), 'money'),
    KPI('Late-cancel fees waived, 30 days', 'SUMIFS({range:cancels.fee_given_up},%s)' % D30('cancels.date'), 'money'),
    KPI('Clinicians over cap next week', 'COUNTIFS({range:clin_weeks.week},%s+7,{range:clin_weeks.cap_flag},%s)' % (WK0, ca('Over cap')), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Clinicians above target band next week', 'COUNTIFS({range:clin_weeks.week},%s+7,{range:clin_weeks.cap_flag},%s)+COUNTIFS({range:clin_weeks.week},%s+7,{range:clin_weeks.cap_flag},%s)' % (WK0, ca('Over cap'), WK0, ca('Above target band')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Free slots this week', CW('free_slots', 0, 7), 'int'),
    KPI('Free slots next 4 weeks', CW('free_slots', 7, 35), 'int'),
    KPI('Booked share of slots, next 4 weeks', 'IFERROR(%s/%s,0)' % (CW('booked', 7, 35), CW('eff_cap', 7, 35)), 'pct', alert={"when": "< {set:target_utilisation}", "style": "warn"}),
    KPI('Active clients', 'COUNTIFS({range:caseload.client_status},%s)' % tok('cstatus', 'Active'), 'int'),
    KPI('Clients without a next session', 'COUNTIFS({range:caseload.client_status},%s,{range:caseload.next_flag},%s)' % (tok('cstatus', 'Active'), ca('No next session')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Days to first appointment, 90 days', 'IFERROR(AVERAGEIFS({range:caseload.days_to_first},{range:caseload.booked_on},">="&({today}-90)),0)', 'num', alert={"when": "> {set:wait_target_days}", "style": "bad"}),
    KPI('Back-to-back sessions, last 30 days', 'SUMIFS({range:sessions.back_to_back},%s)' % D30('sessions.date'), 'int'),
    KPI('Room use this month', 'IFERROR(%s/%s,0)' % (RM('used_hours', MS, NXT), RM('open_hours', MS, NXT)), 'pct', alert={"when": "< {set:target_room_use}", "style": "warn"}),
    KPI('Room use vs last 3 months', 'IFERROR(%s/%s-%s/%s,0)' % (RM('used_hours', MS, NXT), RM('open_hours', MS, NXT), RM('used_hours', M3, MS), RM('open_hours', M3, MS)), 'pct'),
    KPI('Sublet hours this month', 'SUMIFS({range:sublets.hours},{range:sublets.month},">="&%s,{range:sublets.month},"<"&%s)' % (MS, NXT), 'num'),
    KPI('Sublet income this month', 'SUMIFS({range:sublets.amount},{range:sublets.month},">="&%s,{range:sublets.month},"<"&%s)' % (MS, NXT), 'money'),
    KPI('Sublet invoices unpaid', 'COUNTIFS({range:sublets.status},%s)' % cb('Invoiced'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Absence weeks next 8 weeks', 'COUNTIFS({range:absences.week},">="&%s,{range:absences.week},"<"&(%s+56))' % (WK0, WK0), 'int'),
    KPI('Reminders confirmed, last 30 days', 'IFERROR(COUNTIFS({range:reminders.confirmed},%s,%s)/COUNTIFS(%s),0)' % (YES, D30('reminders.date'), D30('reminders.date')), 'pct'),
    KPI('People on the cancellation list', 'COUNTIFS({range:cancel_list.list_status},%s)' % ca('Waiting'), 'int'),
    KPI('Online connection problems, 30 days', 'COUNTIFS({range:online.connection_problem},%s,%s)' % (YES, D30('online.date')), 'int', alert={"when": "> 0", "style": "warn"}),
]
assert len(kpis) == 30, len(kpis)
for k in kpis: assert len(k['label']) <= 40, k['label']
dashboard = {"title": "KPI Dashboard", "kpis": kpis,
    "monthly": {"title": "Sessions booked, attended, late cancelled and missed", "date": "clin_weeks.week", "series": [
        {"label": "Booked", "sum": "clin_weeks.booked", "date": "clin_weeks.week"}, {"label": "Attended", "sum": "clin_weeks.attended", "date": "clin_weeks.week"},
        {"label": "Late cancels", "sum": "clin_weeks.late_cancels", "date": "clin_weeks.week"}, {"label": "No-shows", "sum": "clin_weeks.no_shows", "date": "clin_weeks.week"}]},
    "breakdowns": [{"title": "Sessions by status", "by": "sessions.status", "agg": "count"}, {"title": "Sessions by format", "by": "sessions.format", "agg": "count"},
                   {"title": "Sessions by clinician", "by": "sessions.clinician", "agg": "count"}, {"title": "Diary slots by status", "by": "diary.status", "agg": "count"}]}
def SUMC(table, col, label, date=None, where=None): return AGG('sum', table, '%s.%s' % (table, col), date='%s.%s' % (table, date) if date else None, where=where, label=label)
insights = {"filters": [{"label": "Clinician", "list": "clin"}, {"label": "Service", "list": "svc"}, {"label": "Client type", "list": "ctype"}],
    "gauges": [
        {"title": "Booked share of the weeks ahead", "num": AGG('sum', 'clin_weeks', 'clin_weeks.booked', where=[('week', '>=', '{today}')]), "den": AGG('sum', 'clin_weeks', 'clin_weeks.eff_cap', where=[('week', '>=', '{today}')])},
        {"title": "Attendance rate", "num": AGG('sum', 'clin_weeks', 'clin_weeks.attended'), "den": AGG('sum', 'clin_weeks', 'clin_weeks.held')},
        {"title": "Late-cancel fees collected", "num": AGG('sum', 'cancels', 'cancels.fee_charged'), "den": AGG('sum', 'cancels', 'cancels.fee_due')},
        {"title": "Room use", "num": AGG('sum', 'room_months', 'room_months.used_hours'), "den": AGG('sum', 'room_months', 'room_months.open_hours')},
        {"title": "Reminders confirmed", "num": AGG('count', 'reminders', where=[('confirmed', '=', YES)]), "den": AGG('count', 'reminders')},
        {"title": "Active clients with a next session", "num": AGG('count', 'caseload', where=[('client_status', '=', tok('cstatus', 'Active')), ('next_flag', '=', ca('Next session booked'))]), "den": AGG('count', 'caseload', where=[('client_status', '=', tok('cstatus', 'Active'))])}],
    "charts": [
        CHART('Sessions attended per month', 'column', 'month', [SUMC('clin_weeks', 'attended', 'Attended', 'week')]),
        CHART('Sessions per month by format', 'stacked', 'month', [SUMC('clin_weeks', 'in_person', 'In person', 'week'), SUMC('clin_weeks', 'online', 'Online or phone', 'week')]),
        CHART('Sessions booked ahead by clinician', 'bar', 'clin_weeks.clinician', [AGG('sum', 'clin_weeks', 'clin_weeks.booked', where=[('week', '>=', '{today}')], label='Booked')]),
        CHART('Sessions by weekday', 'bar', 'sessions.weekday', [AGG('count', 'sessions', label='Sessions')]),
        CHART('Sessions by room', 'bar', 'sessions.room', [AGG('count', 'sessions', label='Sessions')]),
        CHART('Sessions by format', 'bar', 'sessions.format', [AGG('count', 'sessions', label='Sessions')]),
        CHART('Sessions by status', 'bar', 'sessions.status', [AGG('count', 'sessions', label='Sessions')]),
        CHART('Cancellations per month', 'column', 'month', [SUMC('clin_weeks', 'cancelled', 'Cancellations', 'week')]),
        CHART('No-shows per month', 'column', 'month', [SUMC('clin_weeks', 'no_shows', 'No-shows', 'week')]),
        CHART('Late cancels by reason', 'bar', 'cancels.cancel_reason', [AGG('count', 'cancels', where=[('status', '=', SS('Late cancel'))], label='Late cancels')]),
        CHART('Cancellations by reason', 'bar', 'cancels.cancel_reason', [AGG('count', 'cancels', where=[('status', '=', SS('Cancelled'))], label='Cancellations')]),
        CHART('No-shows by service', 'bar', 'sessions.service', [AGG('count', 'sessions', where=[('status', '=', SS('No-show'))], label='No-shows')]),
        CHART('Late-cancel fees per month', 'column', 'month', [SUMC('clin_weeks', 'late_fees', 'Fees charged', 'week')]),
        CHART('Fees waived per month', 'column', 'month', [SUMC('clin_weeks', 'fees_waived', 'Fees waived', 'week')]),
        CHART('Room session hours per month', 'column', 'month', [SUMC('room_months', 'session_hours', 'Session hours', 'month')]),
        CHART('Used hours by room', 'bar', 'room_months.room', [AGG('sum', 'room_months', 'room_months.used_hours', label='Used hours')]),
        CHART('Sublet hours per month', 'column', 'month', [SUMC('sublets', 'hours', 'Sublet hours', 'month')]),
        CHART('Sublet income by room', 'bar', 'sublets.room', [AGG('sum', 'sublets', 'sublets.amount', label='Income')]),
        CHART('Online sessions per month', 'line', 'month', [SUMC('clin_weeks', 'online', 'Online or phone', 'week')]),
        CHART('Absence weeks by clinician', 'bar', 'absences.clinician', [AGG('count', 'absences', label='Absence weeks')]),
        CHART('Reminders confirmed per month', 'line', 'month', [SUMC('clin_weeks', 'reminders_confirmed', 'Confirmed', 'week')]),
        CHART('Diary slots ahead by status', 'bar', 'diary.status', [AGG('count', 'diary', label='Slots')])]}
signature = [
    {"name": "Clinician capacity with a target load band", "why": "booked sessions against the weekly cap and a band such as 22 to 25 sessions, amber at the top and red above, so one clinician at 31 sessions stands out", "where": "Clinician Capacity"},
    {"name": "Three separate cancellation rates", "why": "No-Show Rate, Late Cancellation Rate and Any Cancellation Rate side by side, plus the missed and late-cancelled share against your own 10 percent target", "where": "KPI Dashboard"},
    {"name": "Late-cancel fee with a waiver limit", "why": "the notice hours, the fee charged or waived and the waivers per client in 12 months show when a waiver needs a review", "where": "Fee Waivers"},
    {"name": "Back-to-back flag and heavy day check", "why": "each session knows whether another follows it, and the check names a day with too many sessions in a row", "where": "Sessions"},
    {"name": "Rebooking gap list ranked act-first", "why": "clients with no next session or a late booking are ranked by days late, so you call the first one first", "where": "Rebooking Gaps"},
    {"name": "Cancellation list that refills slots", "why": "who waits, since when and who was offered a slot, with the value of refilling in the Cancellation Refill Value tool", "where": "Cancellation List"},
    {"name": "Room use against a target", "why": "open hours, sessions, groups and sublets give use share, free hours and a comparison with the last three months", "where": "Room Utilization"},
    {"name": "Absence cover planner", "why": "weeks away, sessions affected and the free slots of the others give sessions to move and sessions to rebook", "where": "Absence Cover Planner"},
    {"name": "Days to first appointment against a target", "why": "booking date to first session for every new client against an editable 14-day target", "where": "Caseload"},
    {"name": "Sublet rate and income tools", "why": "room cost, cleaning and your wanted margin give the hourly rate, and free hours give the income and the gain over your own last months", "where": "Sublet Rate Setter"}]
competitors = [
    {"what": "free appointment templates", "lacks": "list sessions but have no weekly cap, target load band, back-to-back flag or late-cancel fee rules"},
    {"what": "subscription practice-management software", "lacks": "charge per clinician and keep your data in their system, with no editable cancellation targets or room use tools"},
    {"what": "shared calendar apps", "lacks": "show bookings but never count free slots, cancellation rates, rooms used or sessions above a clinician cap"},
    {"what": "generic spreadsheet planners", "lacks": "hold dates and names but have no no-show cost, rebooking gap list, absence cover planner or sublet billing"},
    {"what": "paper appointment books", "lacks": "cannot total sessions a week, flag a clash between rooms or show the fees charged and waived"}]
guide = [
    'Open Start and type your practice name and your own limits in the yellow cells: the late-cancel hours and fee share, the target booked share of cap, the target load band, the missed-session target and the room use target.',
    'Check Team, Rooms, Services, Room Rules and Tenants. They hold your clinicians with their weekly session caps, your rooms with open hours, your services and the outside practitioners who sublet.',
    'Keep Sessions and Weekly Diary up to date each day. Late fee due, back-to-back flag, free slots and days ahead fill in by themselves.',
    'Read Clinician Capacity every week. Booked share of cap (utilisation, then booked share of cap) and the target load band show who has room and who is above the cap.',
    'List every client of a clinician on Caseload with the usual weekday, time and rhythm. Weeks since last session, days to first appointment and the next session check fill in.',
    'Record each cancellation, late cancel and no-show on Cancellations and No-Shows, each waived fee on Fee Waivers and each client waiting for an earlier slot on Cancellation List.',
    'Log Reminders and Online Sessions. Reminder lead time, the cancel window check and connection problems show what to fix.',
    'Book rooms on Room Bookings, read Room Utilization and Busy Times, and record sublets and their invoices on Sublet Log.',
    'Use Clinician Absences and Rebooking Gaps to arrange cover and to call clients with no next session, the most days late first.',
    f'Use the {len(tools)} decision tools for capacity, caseload, fees, room use, cover, reminders, sublets and heavy days. Each gives a verdict and a what-if table.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written.',
    'Read the KPI Dashboard and Charts every week: sessions, the three cancellation rates, fees charged and waived, free slots, room use and sublet income.']
listing = {"title": "Therapy Practice Scheduling Excel Template: Session Diary, Caseload, Clinician Cap, Late-Cancel Fees, Room Use, Sublets",
    "headline": "Fill every slot and keep every clinician at a healthy load",
    "tags": ["therapy practice", "scheduling template", "session diary", "counselling practice", "clinician caseload", "excel template", "no show tracker", "late cancel fee", "room booking", "private practice", "group practice", "sublet rooms", "practice management"],
    "description": ("Run the weekly diary of a group therapy practice in one Excel workbook. Built for an owner-clinician, employed clinicians, contract (self-employed) clinicians, an associate (works under supervision) and a front-desk coordinator who share rooms and sessions.\n\n"
        "Sessions and Weekly Diary show every slot with its clinician, room, format and status. Clinician Capacity compares sessions booked with the weekly cap and a target load band (22 to 25 sessions a week for full time by default), with the booked share of cap and the free slots for every clinician and week, so a clinician with 31 sessions against a cap of 25 is flagged red. "
        "Caseload follows every client with weekday, time, rhythm, next session and days to first appointment against your editable 14-day target. Rebooking Gaps ranks the clients to call first.\n\n"
        "Cancellations and No-Shows keep three separate rates, the No-Show Rate, the Late Cancellation Rate and the Any Cancellation Rate, with the late-cancel fee charged or waived and a waiver limit per client. Reminders, Online Sessions, Cancellation List, Room Bookings, Room Utilization, Busy Times, Clinician Absences, Sublet Log and Tenants complete the picture.\n\n"
        f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: capacity, caseload, late-cancel fee, missed session cost, room use, room allocation, online mix, absence cover, rebooking gaps, reminder timing, cancellation refill, double bookings, heavy days and sublet rates. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
        "This is part two of the Therapy Private Practice suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-clinician fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. The workbook holds status only, never session notes or diagnoses, and it does not promise results."),
    "features": ["Weekly cap and target load band per clinician", "Three separate cancellation rates", "Late-cancel fees charged and waived", "Back-to-back flag and heavy day check", "Rebooking gaps ranked act-first",
                 "Room use, bookings and sublet billing", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
import lib as _lib
s = _lib.spec(id=f'{SUITE}-p2', slug='therapy-practice-scheduling', profession='Therapy Private Practice', name='Scheduling, Caseload and Rooms',
         tagline='Fill every slot and keep every clinician at a healthy load', price_usd=29, colors={"primary": "#2F5D62", "accent": "#A7C4BC"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 2, "of": 8, "focus": "Scheduling, caseload and rooms"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'th2.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
