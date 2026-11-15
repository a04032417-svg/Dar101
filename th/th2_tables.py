"""Therapy part 2: settings and the 20 tables with calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th2_lists import *
import th2_data as D

YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
WK0 = '({today}-WEEKDAY({today},2)+1)'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
SS = lambda x: tok('sstatus', x)
LATE, NOSH, CANC = SS('Late cancel'), SS('No-show'), SS('Cancelled')
def ISMISS(c='status'): return 'OR({col:%s}=%s,{col:%s}=%s)' % (c, LATE, c, NOSH)

settings = [
    S('company', 'Your practice name', 'text', COMPANY), S('late_fee_pct', 'Share of the fee charged for a late cancel or no-show', 'pct', 0.5),
    S('late_cancel_hours', 'Hours of notice that avoid a late-cancel fee', 'int', 24), S('target_utilisation', 'Target booked share of the session cap', 'pct', 0.85),
    S('target_missed', 'Target missed and late-cancelled share of booked', 'pct', 0.10), S('band_low', 'Target load band, lowest sessions a week (full time)', 'int', 22),
    S('band_high', 'Target load band, highest sessions a week (full time)', 'int', 25), S('target_room_use', 'Target room use, share of open hours', 'pct', 0.30),
    S('room_cost_hour', 'Cost of one hour of room time', 'money', 12), S('admin_cost', 'Admin cost per booked session', 'money', 6),
    S('reminder_hours', 'Hours before a session to send the reminder', 'int', 48), S('waiver_limit', 'Late fees waived per client per year before a review', 'int', 2),
    S('gap_grace_days', 'Days a client may be late to rebook before a call', 'int', 7), S('wait_target_days', 'Target days from booking to first appointment', 'int', 14),
    S('buffer_minutes', 'Usual buffer between sessions, minutes', 'int', 10), S('sublet_margin', 'Wanted margin on room sublets', 'pct', 0.25),
    S('max_in_row', 'Most sessions in a row before a break of 15 minutes', 'int', 3)]
assert len(settings) <= 20

def T_(key, sheet, title, hint, cols, demo, rows, alerts=None):
    assert len(hint) <= 200, (key, len(hint))
    return T(key, sheet, title, hint, cols, demo, rows, alerts)

sess_cols = [C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('time', 'Time', 'time', 8), LST('weekday', 'Weekday', 'wday', 11), C('client_id', 'Client ID', 'text', 10),
    C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18), LST('client_type', 'Client type', 'ctype', 12), LST('service', 'Service', 'svc', 18), LST('clinician', 'Clinician', 'clin', 16),
    LST('format', 'Format', 'fmt', 10), LST('room', 'Room', 'room', 12), C('minutes', 'Minutes', 'int', 8), LST('status', 'Status', 'sstatus', 12), LST('cancel_reason', 'Cancel reason', 'creason', 20),
    C('fee_waived', 'Fee waived', 'bool', 9), C('fee', 'Fee', 'num', 9),
    CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12), CA('end_time', 'End time', 'time', '{col:time}+{col:minutes}/1440', 9),
    CA('late_fee', 'Late fee due', 'money', 'IF(%s,IF({col:fee_waived}=%s,0,{col:fee}*{set:late_fee_pct}),0)' % (ISMISS(), YES), 11),
    CA('fee_check', 'Fee check', 'text', 'IF(%s,IF({col:fee_waived}=%s,%s,%s),%s)' % (ISMISS(), YES, ca('Fee waived'), ca('Fee due'), ca('No fee')), 12),
    CA('back_to_back', 'Back-to-back', 'int', 'IF(AND({col:status}<>%s,SUMPRODUCT(({range:sessions.clinician}={col:clinician})*({range:sessions.date}={col:date})*(ROUND({range:sessions.time}*24,0)=ROUND({col:time}*24,0)-1)*({range:sessions.status}<>%s))>0),1,0)' % (CANC, CANC), 11)]

tables = [
 T_('sessions', 'Sessions', 'Session log with late-cancel fee and back-to-back flag',
    'One row per session from 30 days ago to 2 weeks ahead: who, when, room, format and status; the week, end time, late fee due, fee check and back-to-back flag fill in by themselves.', sess_cols, D.sessions_d(), 1000,
    [A('status', '= ' + LATE, 'warn'), A('status', '= ' + NOSH, 'bad'), A('fee_check', '= ' + ca('Fee due'), 'warn'), A('back_to_back', '= 1', 'warn')]),
 T_('diary', 'Weekly Diary', 'Weekly diary of every clinician slot for six weeks',
    'One row per usual slot of each clinician for this week and the next five: booked, free, away or extra; the days ahead and weeks ahead fill in by themselves.', [
    C('slot_id', 'Slot ID', 'text', 10, required=True), C('week', 'Week (Monday)', 'date', 12), C('date', 'Date', 'date', 11), LST('weekday', 'Weekday', 'wday', 11), C('time', 'Time', 'time', 8),
    LST('clinician', 'Clinician', 'clin', 16), LST('status', 'Slot status', 'slotst', 11), C('client', 'Client', 'text', 24), LST('service', 'Service', 'svc', 18), LST('room', 'Room', 'room', 12),
    CA('days_ahead', 'Days ahead', 'int', '{col:date}-{today}', 10), CA('weeks_ahead', 'Weeks ahead', 'int', 'INT(({col:week}-%s)/7)' % WK0, 10)], D.diary_d(), 900,
    [A('status', '= ' + tok('slotst', 'Free'), 'warn'), A('status', '= ' + tok('slotst', 'Away'), 'bad'), A('status', '= ' + tok('slotst', 'Extra'), 'good')]),
 T_('clin_weeks', 'Clinician Capacity', 'Sessions per clinician and week against cap and band',
    'One row per clinician and week: cap, booked, attended, missed and online sessions; booked share of the session cap (utilisation), free slots, target band check and missed share fill in by themselves.', [
    C('cw_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), LST('clinician', 'Clinician', 'clin', 16), C('cap', 'Session cap', 'int', 9), C('booked', 'Booked', 'int', 8),
    C('attended', 'Attended', 'int', 9), C('cancelled', 'Cancelled', 'int', 9), C('late_cancels', 'Late cancels', 'int', 9), C('no_shows', 'No-shows', 'int', 9), C('rescheduled', 'Rescheduled by client', 'int', 11),
    C('online', 'Online or phone', 'int', 9), C('back_to_back', 'Back-to-back', 'int', 9), C('days_away', 'Days away', 'int', 8), C('reminders_sent', 'Reminders sent', 'int', 9),
    C('reminders_confirmed', 'Reminders confirmed', 'int', 11), C('late_fees', 'Late fees charged', 'num', 10), C('fees_waived', 'Late fees waived', 'num', 10),
    CA('eff_cap', 'Cap this week', 'int', 'ROUND({col:cap}*MAX(0,5-{col:days_away})/5,0)', 9), CA('free_slots', 'Free slots', 'int', 'MAX(0,{col:eff_cap}-{col:booked})', 9),
    CA('share_of_cap', 'Booked share of cap', 'pct', 'IF({col:eff_cap}>0,{col:booked}/{col:eff_cap},0)', 10),
    CA('band_top', 'Band top', 'int', 'MIN({set:band_high},{col:eff_cap})', 8), CA('band_floor', 'Band floor', 'int', 'MIN({set:band_low},ROUND(0.85*{col:eff_cap},0))', 8),
    CA('cap_flag', 'Load check', 'text', 'IF({col:eff_cap}=0,%s,IF({col:booked}>{col:eff_cap},%s,IF({col:booked}>{col:band_top},%s,IF({col:booked}>={col:band_top}-1,%s,IF({col:booked}>={col:band_floor},%s,%s)))))' % (
        ca('Away this week'), ca('Over cap'), ca('Above target band'), ca('Top of target band'), ca('In target band'), ca('Below target band')), 16),
    CA('missed_share', 'Missed and late-cancelled share', 'pct', 'IF({col:booked}>0,({col:no_shows}+{col:late_cancels})/{col:booked},0)', 12),
    CA('held', 'Sessions held or missed', 'int', '{col:attended}+{col:late_cancels}+{col:no_shows}', 10), CA('in_person', 'In person', 'int', 'MAX(0,{col:booked}-{col:online})', 9)], sorted(D.clin_weeks_d(), key=lambda r: not (r['booked'] > r['cap'])), 800,
    [A('cap_flag', '= ' + ca('Over cap'), 'bad'), A('cap_flag', '= ' + ca('Above target band'), 'bad'), A('cap_flag', '= ' + ca('Top of target band'), 'warn'), A('cap_flag', '= ' + ca('In target band'), 'good')]),
 T_('caseload', 'Caseload', 'Caseload: the clients each clinician sees now',
    'One row per client a clinician sees now (caseload): usual weekday and time, frequency, first, last and next session; weeks since last session, days to first appointment and next session check fill in.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18), LST('clinician', 'Clinician', 'clin', 16), LST('service', 'Service', 'svc', 18),
    LST('frequency', 'Frequency', 'freq', 11), LST('format', 'Format', 'fmt', 10), LST('weekday', 'Usual weekday', 'wday', 11), C('time', 'Usual time', 'time', 8), C('booked_on', 'Booked on', 'date', 11),
    C('first_session', 'First session', 'date', 11), C('last_session', 'Last session', 'date', 11), C('next_session', 'Next session', 'date', 11), LST('client_status', 'Client status', 'cstatus', 11),
    CA('interval_days', 'Days between sessions', 'int', 'IF({col:frequency}=%s,7,IF({col:frequency}=%s,14,28))' % (tok('freq', 'Weekly'), tok('freq', 'Fortnightly')), 10),
    CA('weekly_load', 'Sessions per week', 'num', '7/IF({col:frequency}=%s,7,IF({col:frequency}=%s,14,28))' % (tok('freq', 'Weekly'), tok('freq', 'Fortnightly')), 9),
    CA('weeks_since_last', 'Weeks since last session', 'int', 'IF({col:last_session}=0,"",INT(({today}-{col:last_session})/7))', 10),
    CA('days_to_first', 'Days to first appointment', 'int', 'IF(OR({col:booked_on}=0,{col:first_session}=0),"",{col:first_session}-{col:booked_on})', 11),
    CA('next_flag', 'Next session check', 'text', 'IF({col:next_session}>={today},%s,%s)' % (ca('Next session booked'), ca('No next session')), 15)], sorted(D.caseload_d(), key=lambda r: not r.get('next_session')), 400,
    [A('next_flag', '= ' + ca('No next session'), 'bad'), A('days_to_first', '> {set:wait_target_days}', 'warn')]),
 T_('cancels', 'Cancellations and No-Shows', 'Cancellations and no-shows with fee and rebooking',
    'One row per session not held: reason, hours of notice, fee and rebooking; a late cancel is a cancellation with less than 24 hours\' notice. Fee charged, fee given up and rebooked flag fill in.', [
    C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18), LST('clinician', 'Clinician', 'clin', 16),
    LST('status', 'Status', 'sstatus', 12), LST('cancel_reason', 'Cancel reason', 'creason', 20), C('notice_hours', 'Hours of notice', 'int', 9), C('fee', 'Fee', 'num', 9), C('fee_waived', 'Fee waived', 'bool', 9),
    C('rebooked_on', 'Rebooked on', 'date', 11),
    CA('notice_flag', 'Notice check', 'text', 'IF({col:notice_hours}<{set:late_cancel_hours},%s,%s)' % (ca('Late notice'), ca('In time')), 12),
    CA('fee_charged', 'Fee charged', 'money', 'IF(AND(%s,{col:fee_waived}<>%s),{col:fee}*{set:late_fee_pct},0)' % (ISMISS(), YES), 10),
    CA('fee_given_up', 'Fee waived amount', 'money', 'IF(AND(%s,{col:fee_waived}=%s),{col:fee}*{set:late_fee_pct},0)' % (ISMISS(), YES), 11),
    CA('rebook_flag', 'Rebooked check', 'text', 'IF({col:rebooked_on}>0,%s,%s)' % (ca('Rebooked'), ca('Not rebooked')), 13),
    CA('days_to_rebook', 'Days to rebook', 'int', 'IF({col:rebooked_on}>0,{col:rebooked_on}-{col:date},"")', 10),
    CA('fee_due', 'Fee due', 'money', 'IF(%s,{col:fee}*{set:late_fee_pct},0)' % ISMISS(), 10)], D.cancels_d(), 500,
    [A('status', '= ' + NOSH, 'bad'), A('status', '= ' + LATE, 'warn'), A('rebook_flag', '= ' + ca('Not rebooked'), 'warn')]),
 T_('waivers', 'Fee Waivers', 'Fee waivers with who agreed and how often',
    'One row per late-cancel or no-show fee waived: client, fee, who agreed and why; the amount given up, waivers for the client this year and the limit check fill in by themselves.', [
    C('waiver_id', 'Waiver ID', 'text', 10, required=True), C('session_id', 'Session ID', 'text', 10), C('date', 'Date', 'date', 11), C('client', 'Client', 'text', 24), C('fee', 'Fee', 'num', 9),
    REF('waived_by', 'Waived by', 'team.name', 22), C('reason', 'Reason', 'text', 24),
    CA('fee_given_up', 'Amount given up', 'money', '{col:fee}*{set:late_fee_pct}', 11),
    CA('times_year', 'Waivers this year', 'int', 'COUNTIFS({range:waivers.client},{col:client},{range:waivers.date},">="&({today}-365),{range:waivers.date},"<="&{today})', 10),
    CA('limit_flag', 'Limit check', 'text', 'IF({col:times_year}>{set:waiver_limit},%s,%s)' % (ca('Over waiver limit'), ca('Within waiver limit')), 16)], D.waivers_d(), 300,
    [A('limit_flag', '= ' + ca('Over waiver limit'), 'warn')]),
 T_('cancel_list', 'Cancellation List', 'Cancellation list of clients who want an earlier slot',
    'One row per client waiting to be offered a cancelled slot: what they want, preferred days and when added; days on the list and the list status (waiting, offered, filled) fill in by themselves.', [
    C('list_id', 'List ID', 'text', 9, required=True), C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18), LST('clinician', 'Clinician', 'clin', 16), LST('service', 'Service', 'svc', 18),
    C('wants', 'Wants', 'text', 24), C('preferred_days', 'Preferred days', 'text', 22), C('added_on', 'Added on', 'date', 11), C('offered_on', 'Offered on', 'date', 11), C('filled', 'Filled', 'bool', 9),
    CA('list_status', 'List status', 'text', 'IF({col:filled}=%s,%s,IF({col:offered_on}>0,%s,%s))' % (YES, ca('Filled'), ca('Offered'), ca('Waiting')), 12),
    CA('days_on_list', 'Days on list', 'int', 'IF({col:offered_on}>0,{col:offered_on}-{col:added_on},{today}-{col:added_on})', 10)], sorted(D.cancel_list_d(), key=lambda r: not r.get('offered_on')), 100,
    [A('list_status', '= ' + ca('Waiting'), 'warn'), A('list_status', '= ' + ca('Filled'), 'good')]),
 T_('reminders', 'Reminders', 'Reminders with lead time and confirmation',
    'One row per reminder sent: session date and time, channel, when sent and whether the client confirmed; hours before the session and the cancel window check fill in by themselves.', [
    C('reminder_id', 'Reminder ID', 'text', 10, required=True), C('session_id', 'Session ID', 'text', 10), C('date', 'Session date', 'date', 11), C('time', 'Session time', 'time', 8), C('client', 'Client', 'text', 24),
    C('phone', 'Client phone', 'text', 18), LST('channel', 'Channel', 'chan', 13), C('sent_on', 'Sent on', 'date', 11), C('sent_time', 'Sent at', 'time', 8), C('confirmed', 'Confirmed', 'bool', 9),
    CA('hours_before', 'Hours before session', 'int', 'ROUND(({col:date}+{col:time}-{col:sent_on}-{col:sent_time})*24,0)', 11),
    CA('window_flag', 'Cancel window check', 'text', 'IF({col:hours_before}>={set:late_cancel_hours},%s,%s)' % (ca('Before cancel deadline'), ca('Inside cancel window')), 18)], D.reminders_d(), 600,
    [A('window_flag', '= ' + ca('Inside cancel window'), 'warn'), A('confirmed', '= ' + YES, 'good')]),
 T_('online', 'Online Sessions', 'Online session checks with connection problems',
    'One row per online or phone session: whether the details were sent, any connection problem and the minutes lost; the problem check and the share of the session lost fill in by themselves.', [
    C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18), LST('clinician', 'Clinician', 'clin', 16),
    LST('service', 'Service', 'svc', 18), C('minutes', 'Minutes', 'int', 8), C('details_sent', 'Details sent', 'bool', 9), C('connection_problem', 'Connection problem', 'bool', 11), C('minutes_lost', 'Minutes lost', 'int', 9),
    CA('problem_flag', 'Problem check', 'text', 'IF({col:connection_problem}=%s,%s,IF({col:details_sent}=%s,%s,%s))' % (YES, ca('Connection problem'), NO, ca('Details not sent'), ca('Smooth session')), 16),
    CA('lost_share', 'Share lost', 'pct', 'IF({col:minutes}>0,{col:minutes_lost}/{col:minutes},0)', 9)], sorted(D.online_d(), key=lambda r: not (int(r.get('minutes_lost') or 0) > 0)), 500,
    [A('problem_flag', '= ' + ca('Connection problem'), 'bad'), A('problem_flag', '= ' + ca('Details not sent'), 'warn')]),
 T_('room_bookings', 'Room Bookings', 'Room bookings for the next four weeks with clash check',
    'One row per room booking for client sessions, group programs and sublets in the next four weeks; the end time and a clash check for the same room at the same time fill in by themselves.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('time', 'Time', 'time', 8), LST('room', 'Room', 'room5', 13), LST('clinician', 'Clinician', 'clin', 16),
    LST('service', 'Service', 'svc', 18), C('use', 'Use', 'text', 14), C('minutes', 'Minutes', 'int', 8),
    CA('end_time', 'End time', 'time', '{col:time}+{col:minutes}/1440', 9),
    CA('clash', 'Clash check', 'text', 'IF(SUMPRODUCT(({range:room_bookings.room}={col:room})*({range:room_bookings.date}={col:date})*(ROUND({range:room_bookings.time}*24,0)=ROUND({col:time}*24,0)))>1,%s,%s)' % (ca('Room clash'), ca('Clear')), 11)],
    D.room_bookings_d(), 500, [A('clash', '= ' + ca('Room clash'), 'bad')]),
 T_('rooms', 'Rooms', 'Rooms with kind and open hours', 'The five therapy rooms with their kind and the hours a week they are open; room use and sublet sheets read these.', [
    LST('room', 'Room', 'room5', 14, required=True), C('kind', 'Room kind', 'text', 14), C('open_hours_week', 'Open hours a week', 'int', 12)], D.rooms_d(), 50),
 T_('room_rules', 'Room Rules', 'Room rules by service with buffer minutes', 'Which kind of room each service needs and the buffer minutes to reset it before the next session; the room allocation planner reads these.', [
    LST('service', 'Service', 'svc', 18, required=True), C('room_kind', 'Room kind', 'text', 14), C('buffer_minutes', 'Buffer minutes', 'int', 10)], D.room_rules_d(), 50),
 T_('room_months', 'Room Utilization', 'Room hours used by room and month',
    'One row per room and month: open hours and the hours used by sessions, groups and sublets; used hours, use share against your target, free hours and the use check fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('room', 'Room', 'room5', 13), C('open_hours', 'Open hours', 'num', 9), C('session_hours', 'Session hours', 'num', 10),
    C('group_hours', 'Group hours', 'num', 9), C('sublet_hours', 'Sublet hours', 'num', 9), C('sessions', 'Sessions', 'int', 9),
    CA('used_hours', 'Used hours', 'num', '{col:session_hours}+{col:group_hours}+{col:sublet_hours}', 9),
    CA('use_share', 'Room use', 'pct', 'IF({col:open_hours}>0,({col:session_hours}+{col:group_hours}+{col:sublet_hours})/{col:open_hours},0)', 9),
    CA('free_hours', 'Free hours', 'num', 'MAX(0,{col:open_hours}-{col:session_hours}-{col:group_hours}-{col:sublet_hours})', 9),
    CA('use_flag', 'Use check', 'text', 'IF({col:use_share}>={set:target_room_use},%s,IF({col:use_share}>=0.85*{set:target_room_use},%s,%s))' % (ca('Above room target'), ca('Near room target'), ca('Below room target')), 16)],
    D.room_months_d(), 200, [A('use_flag', '= ' + ca('Below room target'), 'warn'), A('use_flag', '= ' + ca('Above room target'), 'good')]),
 T_('busy', 'Busy Times', 'Busy times by weekday and hour',
    'One row per weekday and hour: sessions held in the last 12 weeks, no-shows and free diary slots in the next four weeks; the no-show share and the busy or quiet check fill in by themselves.', [
    C('bt_id', 'Row ID', 'text', 9, required=True), LST('weekday', 'Weekday', 'wday', 11), C('time', 'Hour', 'time', 8), C('sessions_12w', 'Sessions, 12 weeks', 'int', 10), C('no_shows', 'No-shows', 'int', 9),
    C('free_slots', 'Free slots, 4 weeks', 'int', 10),
    CA('no_show_share', 'No-show share', 'pct', 'IF({col:sessions_12w}>0,{col:no_shows}/{col:sessions_12w},0)', 9),
    CA('busy_flag', 'Busy check', 'text', 'IF({col:sessions_12w}>=1.4*AVERAGE({range:busy.sessions_12w}),%s,IF({col:sessions_12w}<=0.4*AVERAGE({range:busy.sessions_12w}),%s,%s))' % (cb('Busy hour'), cb('Quiet hour'), cb('Normal hour')), 12)],
    D.busy_d(), 100, [A('busy_flag', '= ' + cb('Busy hour'), 'good'), A('busy_flag', '= ' + cb('Quiet hour'), 'warn')]),
 T_('absences', 'Clinician Absences', 'Clinician absences with sessions moved and cover',
    'One row per clinician week away: kind, days, sessions moved and who covers; the absence status, the cover check and the clinician phone fill in by themselves.', [
    C('absence_id', 'Absence ID', 'text', 10, required=True), C('week', 'Week (Monday)', 'date', 12), LST('clinician', 'Clinician', 'clin', 16), LST('kind', 'Kind', 'absk', 14), C('days', 'Days', 'int', 7),
    C('sessions_moved', 'Sessions moved', 'int', 9), LST('cover_by', 'Cover by', 'clin', 16),
    CA('status', 'Absence status', 'text', 'IF({col:week}+6<{today},%s,IF({col:week}<={today},%s,%s))' % (cb('Past week'), cb('Away now'), cb('Planned')), 12),
    CA('cover_flag', 'Cover check', 'text', 'IF({col:sessions_moved}=0,%s,IF({col:cover_by}<>"",%s,%s))' % (cb('No cover needed'), cb('Cover set'), cb('Cover needed')), 14),
    CA('phone', 'Clinician phone', 'text', LKT('team.phone', 'team.name', 'clinician'), 18)], sorted(D.absences_d(), key=lambda r: not r.get('cover_by')), 100,
    [A('cover_flag', '= ' + cb('Cover needed'), 'warn'), A('status', '= ' + cb('Away now'), 'bad')]),
 T_('rebook', 'Rebooking Gaps', 'Rebooking gaps: clients to call about their next session',
    'One row per client with no next session or a booking later than their usual rhythm; the expected next date, days late, the rebooking check and the act-first rank (1 = call first) fill in.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('phone', 'Client phone', 'text', 18), LST('clinician', 'Clinician', 'clin', 16), LST('frequency', 'Frequency', 'freq', 11),
    C('last_session', 'Last session', 'date', 11), C('next_session', 'Next session', 'date', 11), C('called_on', 'Called on', 'date', 11), C('result', 'Call result', 'text', 16),
    CA('expected_next', 'Expected next session', 'date', '{col:last_session}+IF({col:frequency}=%s,7,IF({col:frequency}=%s,14,28))' % (tok('freq', 'Weekly'), tok('freq', 'Fortnightly')), 12),
    CA('days_late', 'Days late', 'int', 'IF({col:next_session}>0,MAX(0,{col:next_session}-{col:expected_next}),MAX(0,{today}-{col:expected_next}))', 9),
    CA('rebook_flag', 'Rebooking check', 'text', 'IF({col:days_late}>{set:gap_grace_days},%s,IF({col:days_late}>0,%s,%s))' % (cb('Book now'), cb('Due soon'), cb('On schedule')), 13),
    CA('act_rank', 'Act-first rank', 'int', 'IF({col:days_late}>0,1+COUNTIFS({range:rebook.days_late},">"&{col:days_late}),"")', 9)], D.rebook_d(), 100,
    [A('rebook_flag', '= ' + cb('Book now'), 'bad'), A('rebook_flag', '= ' + cb('Due soon'), 'warn')]),
 T_('tenants', 'Tenants', 'Tenants with room and hourly rate', 'The outside practitioners who sublet rooms with the agreed hourly rate for each room they may use; the sublet log reads these.', [
    C('name', 'Name', 'text', 24, required=True), LST('room', 'Room', 'room5', 13), C('rate', 'Rate per hour', 'money', 11)], D.tenants_d(), 50),
 T_('sublets', 'Sublet Log', 'Sublet log with invoices and days to pay',
    'One row per tenant and month: hours, rate, amount and the invoice and payment dates; the status, days to pay, the payment check and the tenant phone fill in by themselves.', [
    C('sublet_id', 'Sublet ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), REF('tenant', 'Tenant', 'tenants.name', 24), LST('room', 'Room', 'room5', 13), C('hours', 'Hours', 'num', 8), C('rate', 'Rate', 'money', 9),
    C('amount', 'Amount', 'money', 11), C('invoiced_on', 'Invoiced on', 'date', 11), C('paid_on', 'Paid on', 'date', 11),
    CA('status', 'Status', 'text', 'IF({col:paid_on}>0,%s,IF({col:invoiced_on}>0,%s,%s))' % (cb('Paid'), cb('Invoiced'), cb('Accruing')), 11),
    CA('days_to_pay', 'Days to pay', 'int', 'IF(AND({col:paid_on}>0,{col:invoiced_on}>0),{col:paid_on}-{col:invoiced_on},"")', 9),
    CA('pay_flag', 'Payment check', 'text', 'IF({col:paid_on}>0,IF({col:paid_on}-{col:invoiced_on}>14,%s,%s),IF({col:invoiced_on}>0,IF({today}-{col:invoiced_on}>14,%s,%s),%s))' % (cb('Paid late'), cb('Paid on time'), cb('Overdue'), cb('Not yet due'), cb('Accruing')), 13),
    CA('tenant_phone', 'Tenant phone', 'text', 'CHOOSE(MATCH({col:tenant},{range:tenants.name},0),"%s","%s","%s","%s","%s")' % tuple([t['phone'] for t in tenants] + ['+44 20 555 0142', '+44 20 555 0187']), 18)], D.sublets_d(), 100,
    [A('pay_flag', '= ' + cb('Overdue'), 'bad'), A('pay_flag', '= ' + cb('Paid late'), 'warn')]),
 T_('services', 'Services', 'Services with minutes and fee', 'The ten services with the session length and this year\'s list fee; session tools read these.', [
    C('service', 'Service', 'text', 24, required=True), C('minutes', 'Minutes', 'int', 9), C('fee', 'Fee', 'money', 10)], D.services_d(), 50),
 T_('team', 'Team', 'Team with weekly cap and sessions booked next week',
    'The owner clinician, employed clinicians, contract (self-employed) clinicians, the associate (works under supervision), the coordinator and five outside contacts; booked sessions next week fill in.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 28), C('team', 'Team', 'text', 12), C('pay_type', 'Pay type', 'text', 16),
    C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26), C('hours_week', 'Hours a week', 'int', 10), C('monthly_salary', 'Monthly salary', 'num', 11), C('split_pct', 'Share of the fee', 'pct', 10),
    C('session_rate', 'Rate per session', 'num', 10), C('hourly_rate', 'Hourly rate', 'num', 10), C('session_cap', 'Session cap a week', 'int', 10), C('session_target', 'Session target a week', 'int', 10),
    C('speciality', 'Speciality', 'text', 28), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
    CA('booked_next_week', 'Booked next week', 'int', 'SUMIFS({range:clin_weeks.booked},{range:clin_weeks.clinician},{col:name},{range:clin_weeks.week},%s+7)' % WK0, 11),
    CA('absence_weeks', 'Absence weeks', 'int', 'COUNTIFS({range:absences.clinician},{col:name})', 10)], D.team_d(), 50),
]
assert len(tables) == 20

def _role(role, col):
    return 'IFERROR(INDEX({range:team.%s},MATCH(%s,{range:team.role},0))&"","")' % (col, tok('role', role))
def _add(tk, *cols): next(t for t in tables if t['key'] == tk)['columns'].extend(cols)
def _clin_phone(): return CA('clinician_phone', 'Clinician phone', 'text', LKT('team.phone', 'team.name', 'clinician'), 18)
def _coord(): return [CA('coord', 'Coordinator', 'text', _role('Practice coordinator', 'name'), 20), CA('coord_phone', 'Coordinator phone', 'text', _role('Practice coordinator', 'phone'), 18)]
def _owner(): return [CA('owner', 'Owner', 'text', _role('Owner clinician', 'name'), 20), CA('owner_phone', 'Owner phone', 'text', _role('Owner clinician', 'phone'), 18)]
_add('sessions', _clin_phone(), *_coord())
_add('cancels', _clin_phone(), *_coord())
_add('clin_weeks', _clin_phone(), *_owner())
_add('room_bookings', _clin_phone(), *_coord(), CA('cleaner', 'Cleaner', 'text', _role('Cleaner', 'name'), 20), CA('cleaner_phone', 'Cleaner phone', 'text', _role('Cleaner', 'phone'), 18))
_add('online', *_coord())
_add('rebook', *_coord())
_add('room_months', *_owner())
assert len(tables) == 20
