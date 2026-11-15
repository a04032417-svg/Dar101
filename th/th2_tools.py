"""Therapy part 2: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th2_lists import *

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
WK0 = '({today}-WEEKDAY({today},2)+1)'
SC = 'CHOOSE({in:sc},1,1.15,0.85)'

# 1 capacity
EFF1 = 'ROUND({in:cap}*MAX(0,{in:workdays}-{in:away})/{in:workdays},0)'; TOP1 = 'MIN({set:band_high},%s)' % EFF1
# 2 caseload
LOAD2 = '({in:wk}+{in:fn}/2+{in:mo}/4)'; ROOM2 = 'MAX(0,{in:cap}*{set:target_utilisation}-%s)' % LOAD2
# 3 late fee
FEE3 = 'IF({in:hours}<{in:rule},{in:fee}*{in:share},0)'; CHG3 = 'IF({in:earlier}=0,0,%s)' % FEE3
# 4 no-show cost
N4 = '({in:ns}+{in:lc})'; REC4 = N4 + '*{in:fee}*{set:late_fee_pct}*(1-{in:waived})'
# 5 room use
SESS5 = 'ROUND({in:sessions}*%s,0)' % SC; USED5 = '(%s*({in:minutes}+{in:buffer})/60+{in:group}+{in:sublet})' % SESS5
# 6 room allocation
def NEED6(a): return '({in:%s}*({in:minutes}+{in:buffer})/60)' % a
def CAP6(r): return '({in:%s}*{in:hours}*{set:target_utilisation})' % r
# 7 online mix
ON7 = '({in:sessions}*{in:share})'; HRS7 = '({in:minutes}+{in:buffer})/60'
def RM7(x): return 'ROUNDUP(%s*%s/({in:hours}*{set:target_utilisation}),0)' % (x, HRS7)
# 8 absence
AFF8 = '({in:weeks}*{in:sess})'; MOV8 = 'MIN(ROUND(%s*{in:accept},0),{in:weeks}*{in:free})' % AFF8
# 9 rebook
IV9 = 'IF({in:freq}=%s,7,IF({in:freq}=%s,14,28))' % (tok('freq', 'Weekly'), tok('freq', 'Fortnightly'))
LATE9 = 'MAX(0,{today}-({in:last}+%s))' % IV9
# 10 reminder
DT10 = '({in:date}+{in:hour}/24)'
# 11 refill
ACC11 = 'ROUND({in:people}*{in:rate},0)'; REF11 = 'MIN({in:slots},%s)' % ACC11
# 12 double booking
DB = 'SUMPRODUCT(({range:diary.clinician}={in:clin})*({range:diary.date}={in:date})*(ROUND({range:diary.time}*24,0)={in:hour})*(({range:diary.status}=%s)+({range:diary.status}=%s)))' % (tok('slotst', 'Booked'), tok('slotst', 'Extra'))
RB = 'SUMPRODUCT(({range:room_bookings.room}={in:room})*({range:room_bookings.date}={in:date})*(ROUND({range:room_bookings.time}*24,0)={in:hour}))'
# 13 pairing
WA = '({in:da}-WEEKDAY({in:da},2)+1)'; WB = '({in:db}-WEEKDAY({in:db},2)+1)'
SHARE13 = 'AND(MOD(ABS(%s-%s)/7,2)=1,{in:wa}={in:wb},{in:ha}={in:hb})' % (WA, WB)
# 14 closure
AVG14 = 'SUMIFS({range:clin_weeks.booked},{range:clin_weeks.week},">="&(%s-56),{range:clin_weeks.week},"<"&%s)/8' % (WK0, WK0)
# 15 sublet rate
COST15 = '({in:room}+{in:clean})'; REQ15 = COST15 + '/(1-{in:margin})'
# 17 heavy day
# 18 sensitivity
def NET18(sh): return '{in:booked}*%s*{in:fee}*(1-{in:charge}*(1-{in:waived}))' % sh

tools = [
 TOOL('cap_check', 'Weekly Capacity Check', 'Can this clinician take more sessions next week?',
      'Type the session cap, sessions booked and days away; see free slots, sessions over the cap, the booked share of cap, the target load band and a verdict.', [
      I('cap', 'Session cap a week', 25), I('booked', 'Sessions booked', 31), I('away', 'Days away', 0), I('workdays', 'Days worked in a normal week', 5)], [
      O('Cap this week', 'int', EFF1), O('Free slots', 'int', 'MAX(0,%s-{in:booked})' % EFF1), O('Sessions over the cap', 'int', 'MAX(0,{in:booked}-%s)' % EFF1),
      O('Booked share of cap', 'pct', 'IF(%s>0,{in:booked}/%s,0)' % (EFF1, EFF1)), O('Top of the target load band', 'int', TOP1), O('Sessions to move to reach the band top', 'int', 'MAX(0,{in:booked}-%s)' % TOP1),
      O('Verdict', 'text', 'IF(%s=0,%s,IF({in:booked}>%s,%s,IF({in:booked}>=%s-1,%s,%s)))' % (EFF1, cb('Away: cover needed'), EFF1, cb('Over cap: move sessions'), TOP1, cc('Top of the band'), cb('Room to book')))],
      GR('What if', ('One day away', {'away': 1}), ('Two days away', {'away': 2}), ('At the cap, 25 booked', {'booked': 25}), ('Light week, 18 booked', {'booked': 18}), ('Part-time clinician, cap 14, 13 booked', {'cap': 14, 'booked': 13}))),
 TOOL('caseload_plan', 'Caseload Planner', 'How many new clients fit in this caseload?',
      'Type the weekly, fortnightly and monthly clients and the cap; see the weekly session load, the booked share of cap, the room left for new clients and the best rhythm to offer.', [
      I('wk', 'Weekly clients', 14), I('fn', 'Fortnightly clients', 10), I('mo', 'Monthly clients', 6), I('cap', 'Session cap a week', 25), I('attend', 'Attendance rate', 0.93, 'pct')], [
      O('Sessions a week from the caseload', 'num', LOAD2), O('Booked share of cap', 'pct', 'IF({in:cap}>0,%s/{in:cap},0)' % LOAD2), O('Sessions a week expected to be attended', 'num', LOAD2 + '*{in:attend}'),
      O('Sessions a week at the target share of cap', 'num', '{in:cap}*{set:target_utilisation}'), O('Room for new sessions a week', 'num', ROOM2), O('New weekly clients that fit', 'int', 'ROUNDDOWN(%s,0)' % ROOM2),
      O('New fortnightly clients that fit', 'int', 'ROUNDDOWN(%s/0.5,0)' % ROOM2), O('New monthly clients that fit', 'int', 'ROUNDDOWN(%s/0.25,0)' % ROOM2),
      O('Verdict', 'text', 'IF(%s>{in:cap},%s,IF(%s>=0.25,%s,%s))' % (LOAD2, cb('Over cap: move sessions'), ROOM2, cb('Room to book'), cc('Top of the band')))],
      GR('What if', ('Five more weekly clients', {'wk': 19}), ('Ten more monthly clients', {'mo': 16}), ('Cap 20, part-time', {'cap': 20, 'wk': 8, 'fn': 8, 'mo': 4}), ('Attendance 85 percent', {'attend': 0.85}), ('Lighter caseload', {'wk': 8, 'fn': 8, 'mo': 4}))),
 TOOL('late_fee_calc', 'Late-Cancel Fee Calculator', 'What fee does this late cancel or no-show carry?',
      'Type the session fee, the hours of notice, your rule and the fee share; see the fee to charge, the fee waived under the first-time rule and a verdict.', [
      I('fee', 'Session fee', 125, 'money'), I('hours', 'Hours of notice given', 6), I('rule', 'Hours of notice the rule asks for', 24), I('share', 'Share of the fee charged', 0.5, 'pct'), I('earlier', 'Late cancels by this client this year, before this one', 1)], [
      O('Late cancel under the rule (1 = yes)', 'int', 'IF({in:hours}<{in:rule},1,0)'), O('Fee before any waiver', 'money', FEE3), O('First-time waiver applies (1 = yes)', 'int', 'IF(AND({in:hours}<{in:rule},{in:earlier}=0),1,0)'),
      O('Fee to charge', 'money', CHG3), O('Fee waived', 'money', FEE3 + '-' + CHG3), O('Verdict', 'text', 'IF({in:hours}>={in:rule},%s,IF({in:earlier}=0,%s,%s))' % (cb('No fee: notice given'), cb('Waive the fee'), cb('Charge the fee')))],
      GR('What if', ('30 hours of notice', {'hours': 30}), ('First late cancel', {'earlier': 0}), ('No-show, 0 hours, third time', {'hours': 0, 'earlier': 2}), ('Full fee for a late cancel', {'share': 1.0}), ('Extended session, fee 180', {'fee': 180}))),
 TOOL('noshow_cost', 'Missed Session Cost', 'What do missed sessions cost the practice each month?',
      'Type the no-shows and late cancels a month, the average fee, the share of fees waived and the booked sessions; see the revenue lost, the room time wasted and whether the missed share is within target.', [
      I('ns', 'No-shows a month', 11), I('lc', 'Late cancels a month', 11), I('fee', 'Average session fee', 128, 'money'), I('pay', 'Clinician pay per session', 70, 'money'), I('waived', 'Share of late fees waived', 0.33, 'pct'),
      I('minutes', 'Session minutes', 50), I('booked', 'Booked sessions a month', 481), I('revenue', 'Revenue a month', 47000, 'money')], [
      O('Fees not earned', 'money', N4 + '*{in:fee}'), O('Late fees recovered', 'money', REC4), O('Net revenue lost a month', 'money', N4 + '*{in:fee}-' + REC4), O('Net revenue lost a year', 'money', '12*(' + N4 + '*{in:fee}-' + REC4 + ')'),
      O('Clinician pay still due on empty slots', 'money', N4 + '*{in:pay}'), O('Room time cost of empty slots', 'money', N4 + '*{in:minutes}/60*{set:room_cost_hour}'), O('Share of monthly revenue lost', 'pct', '(' + N4 + '*{in:fee}-' + REC4 + ')/{in:revenue}'),
      O('Missed and late-cancelled share of booked sessions', 'pct', N4 + '/{in:booked}'), O('Verdict', 'text', 'IF(%s/{in:booked}>{set:target_missed},%s,%s)' % (N4, cb('Above target'), cb('Within target')))],
      GR('What if', ('Double the no-shows', {'ns': 22}), ('No late fees waived', {'waived': 0.0}), ('Half the late cancels', {'lc': 5}), ('Busy month, 520 booked', {'booked': 520, 'ns': 18, 'lc': 17}), ('Fee 150', {'fee': 150}))),
 TOOL('room_use_calc', 'Room Utilization Calculator', 'How much of a room is used, and what is free?',
      'Type open hours, sessions, minutes, buffer, group and sublet hours and a scenario (1 base, 2 busier, 3 quieter); see room use against target, free hours and a verdict.', [
      I('open', 'Open hours in the month', 118, 'num'), I('sessions', 'Sessions in the room a month', 30), I('minutes', 'Session minutes', 50), I('buffer', 'Buffer minutes', 10), I('group', 'Group hours', 3, 'num'),
      I('sublet', 'Sublet hours', 8, 'num'), I('sc', 'Scenario: 1 base, 2 busier, 3 quieter', 1)], [
      O('Sessions in the scenario', 'int', SESS5), O('Used hours with buffers', 'num', USED5), O('Room use', 'pct', USED5 + '/{in:open}'), O('Free hours', 'num', 'MAX(0,{in:open}-%s)' % USED5),
      O('Hours at the target room use', 'num', '{in:open}*{set:target_room_use}'), O('Hours above (+) or below (-) the target', 'num', USED5 + '-{in:open}*{set:target_room_use}'),
      O('Extra sessions that still fit at 100 percent use', 'int', 'ROUNDDOWN(MAX(0,{in:open}-%s)*60/({in:minutes}+{in:buffer}),0)' % USED5),
      O('Verdict', 'text', 'IF(%s/{in:open}>={set:target_room_use},%s,IF(%s/{in:open}>=0.85*{set:target_room_use},%s,%s))' % (USED5, ca('Above room target'), USED5, ca('Near room target'), ca('Below room target')))],
      GR('What if', ('Busier scenario', {'sc': 2}), ('Quieter scenario', {'sc': 3}), ('No sublet', {'sublet': 0}), ('Longer buffers, 20 minutes', {'buffer': 20}), ('Fewer open hours, 90', {'open': 90}))),
 TOOL('room_alloc', 'Room Allocation Planner', 'Do we have enough rooms of each kind?',
      'Type the sessions a week for adult, family and child rooms and how many rooms of each kind you have; see the hours needed, the hours available at the target share of cap and any shortfall.', [
      I('adult', 'Sessions a week needing an adult room', 70), I('fam', 'Sessions a week needing a family room', 15), I('child', 'Sessions a week needing a child room', 25), I('ra', 'Adult rooms', 3), I('rf', 'Family rooms', 1),
      I('rc', 'Child rooms', 1), I('hours', 'Open hours a week in a room', 55), I('minutes', 'Session minutes', 50), I('buffer', 'Buffer minutes', 10)], [
      O('Adult room hours needed', 'num', NEED6('adult')), O('Family room hours needed', 'num', NEED6('fam')), O('Child room hours needed', 'num', NEED6('child')), O('Adult room shortfall, hours', 'num', 'MAX(0,%s-%s)' % (NEED6('adult'), CAP6('ra'))),
      O('Family room shortfall, hours', 'num', 'MAX(0,%s-%s)' % (NEED6('fam'), CAP6('rf'))), O('Child room shortfall, hours', 'num', 'MAX(0,%s-%s)' % (NEED6('child'), CAP6('rc'))),
      O('Total shortfall, hours', 'num', 'MAX(0,%s-%s)+MAX(0,%s-%s)+MAX(0,%s-%s)' % (NEED6('adult'), CAP6('ra'), NEED6('fam'), CAP6('rf'), NEED6('child'), CAP6('rc'))),
      O('Verdict', 'text', 'IF(MAX(0,%s-%s)+MAX(0,%s-%s)+MAX(0,%s-%s)>0,%s,%s)' % (NEED6('adult'), CAP6('ra'), NEED6('fam'), CAP6('rf'), NEED6('child'), CAP6('rc'), cc('Add room hours'), cc('Rooms are enough')))],
      GR('What if', ('Family sessions grow to 60', {'fam': 60}), ('Child sessions grow to 70', {'child': 70}), ('A second family room', {'fam': 60, 'rf': 2}), ('Longer buffers, 20 minutes', {'buffer': 20}), ('One adult room closed', {'ra': 1, 'adult': 70}))),
 TOOL('online_mix', 'Online and In-Person Mix', 'How many room hours does online work free?',
      'Type the sessions a week, the online share, minutes and buffers; see the room hours freed, the room time cost saved and how many rooms you need.', [
      I('sessions', 'Sessions a week', 110), I('share', 'Online or phone share', 0.30, 'pct'), I('minutes', 'Session minutes', 50), I('buffer', 'Buffer minutes', 10), I('hours', 'Open hours a week in a room', 55)], [
      O('Online sessions a week', 'num', ON7), O('In-person sessions a week', 'num', '{in:sessions}-' + ON7), O('Room hours needed a week', 'num', '({in:sessions}-%s)*%s' % (ON7, HRS7)), O('Room hours freed a week', 'num', ON7 + '*' + HRS7),
      O('Room time cost saved a month', 'money', ON7 + '*' + HRS7 + '*4.33*{set:room_cost_hour}'), O('Rooms needed if everything were in person', 'int', RM7('{in:sessions}')),
      O('Rooms needed with this mix', 'int', RM7('({in:sessions}-%s)' % ON7)), O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (RM7('{in:sessions}'), RM7('({in:sessions}-%s)' % ON7), cc('Rooms freed'), cc('No room saved')))],
      GR('What if', ('Online share 50 percent', {'share': 0.5}), ('Online share 10 percent', {'share': 0.1}), ('Busy week, 160 sessions', {'sessions': 160}), ('Longer buffers, 20 minutes', {'buffer': 20}), ('Rooms open 40 hours', {'hours': 40}))),
 TOOL('absence_cover', 'Absence Cover Planner', 'How many sessions can we move while a clinician is away?',
      'Type the weeks away, the clinician\'s sessions a week, the free slots of the others and how many clients accept cover; see the sessions to move, to rebook and the fees at risk.', [
      I('weeks', 'Weeks away', 2), I('sess', 'Sessions a week of the absent clinician', 22), I('free', 'Free slots a week of the other clinicians', 16), I('accept', 'Clients who accept a cover clinician', 0.70, 'pct'), I('fee', 'Average session fee', 125, 'money')], [
      O('Sessions affected', 'int', AFF8), O('Sessions that can move to a cover clinician', 'int', MOV8), O('Sessions to rebook or cancel', 'int', AFF8 + '-' + MOV8), O('Fees protected by cover', 'money', MOV8 + '*{in:fee}'),
      O('Fees at risk', 'money', '(%s-%s)*{in:fee}' % (AFF8, MOV8)), O('Share of sessions covered', 'pct', 'IF(%s>0,%s/%s,0)' % (AFF8, MOV8, AFF8)),
      O('Verdict', 'text', 'IF(%s>=0.8*%s,%s,%s)' % (MOV8, AFF8, cc('Cover most sessions'), cc('Rebook many clients')))],
      GR('What if', ('One week away', {'weeks': 1}), ('Four weeks away', {'weeks': 4}), ('More free slots, 30', {'free': 30}), ('Clients accept 90 percent', {'accept': 0.9}), ('Part-time clinician, 12 sessions', {'sess': 12}))),
 TOOL('rebook_gap', 'Rebooking Gap Finder', 'Which client do we call first about their next session?',
      'Type a client\'s last session and rhythm; see the expected next date, days late and a verdict, plus the most overdue client on the Rebooking Gaps sheet.', [
      I('last', 'Last session', 'today-23', 'date'), IN('freq', 'Frequency', 'list', key('freq', 'Fortnightly'), list='freq')], [
      O('Expected next session', 'date', '{in:last}+' + IV9), O('Days late', 'int', LATE9), O('Weeks since the last session', 'int', 'INT(({today}-{in:last})/7)'),
      O('Verdict', 'text', 'IF(%s>{set:gap_grace_days},%s,IF(%s>0,%s,%s))' % (LATE9, cb('Book now'), LATE9, cb('Due soon'), cb('On schedule'))),
      O('Call first: most overdue client on the list', 'text', 'IFERROR(INDEX({range:rebook.client},MATCH(1,{range:rebook.act_rank},0)),"")'), O('Days late of that client', 'int', 'MAX({range:rebook.days_late})'),
      O('Clients to call now', 'int', 'COUNTIFS({range:rebook.rebook_flag},%s)' % cb('Book now'))],
      GR('What if', ('Weekly client, last seen 12 days ago', {'last': '=({today}-12)', 'freq': '=' + tok('freq', 'Weekly')}), ('Monthly client, 40 days ago', {'last': '=({today}-40)', 'freq': '=' + tok('freq', 'Monthly')}), ('Fortnightly, 10 days ago', {'last': '=({today}-10)'}))),
 TOOL('reminder_timing', 'Reminder Timing', 'When do we send the reminder and the cancel deadline?',
      'Type the session date and hour and how many hours before to remind; see the send dates and hours, the cancel deadline and whether the reminder falls on a day you are closed.', [
      I('date', 'Session date', 'today+3', 'date'), I('hour', 'Session hour, 0 to 23', 10), I('lead', 'Hours before the session for the first reminder', 48), I('second', 'Hours before for a second reminder', 3)], [
      O('First reminder date', 'date', 'INT(%s-{in:lead}/24)' % DT10), O('First reminder hour', 'int', 'MOD({in:hour}-{in:lead},24)'), O('Second reminder date', 'date', 'INT(%s-{in:second}/24)' % DT10),
      O('Second reminder hour', 'int', 'MOD({in:hour}-{in:second},24)'), O('Cancel deadline date', 'date', 'INT(%s-{set:late_cancel_hours}/24)' % DT10), O('Cancel deadline hour', 'int', 'MOD({in:hour}-{set:late_cancel_hours},24)'),
      O('Hours the client has to cancel without a fee', 'int', '{in:lead}-{set:late_cancel_hours}'),
      O('Verdict', 'text', 'IF(WEEKDAY(INT(%s-{in:lead}/24),2)=7,%s,%s)' % (DT10, cc('Falls on a Sunday'), cc('Send on a working day')))],
      GR('What if', ('Reminder 24 hours before', {'lead': 24}), ('Reminder 72 hours before', {'lead': 72}), ('Late session, 18:00', {'hour': 18}), ('Session in a week', {'date': '=({today}+7)'}))),
 TOOL('refill_value', 'Cancellation Refill Value', 'What is the cancellation list worth, and is it long enough?',
      'Type cancelled slots a week, the people on the cancellation list, the share who accept an offer and the fee; see the slots refilled, revenue recovered and the people needed to fill every slot.', [
      I('slots', 'Cancelled slots a week', 12), I('people', 'People on the cancellation list', 9), I('rate', 'Share who accept an offered slot', 0.5, 'pct'), I('fee', 'Average session fee', 125, 'money')], [
      O('Offers accepted a week', 'int', ACC11), O('Slots refilled a week', 'int', REF11), O('Revenue recovered a week', 'money', REF11 + '*{in:fee}'), O('Revenue recovered a month', 'money', REF11 + '*{in:fee}*4.33'),
      O('Slots still empty a week', 'int', '{in:slots}-' + REF11), O('Revenue still lost a week', 'money', '({in:slots}-%s)*{in:fee}' % REF11), O('People needed to fill every slot', 'int', 'ROUNDUP({in:slots}/{in:rate},0)'),
      O('People to add to the list', 'int', 'MAX(0,ROUNDUP({in:slots}/{in:rate},0)-{in:people})'), O('Verdict', 'text', 'IF(%s>={in:slots},%s,%s)' % (REF11, cc('List is long enough'), cc('Add people to the list')))],
      GR('What if', ('Twice the people', {'people': 18}), ('Half the cancellations', {'slots': 6}), ('Acceptance 80 percent', {'rate': 0.8}), ('Fee 150', {'fee': 150}), ('Short list, 3 people', {'people': 3}))),
 TOOL('double_book', 'Double-Booking Check', 'Is this clinician and room free at that time?',
      'Type the clinician, room, date and hour; see the clinician\'s booked slots and the room bookings at that time, the clinician\'s free slots that day and a verdict.', [
      IN('clin', 'Clinician', 'list', key('clin', 'Daniel Okoye'), list='clin'), IN('room', 'Room', 'list', key('room5', 'Willow Room'), list='room5'), I('date', 'Date', 'today+1', 'date'), I('hour', 'Hour, 0 to 23', 14)], [
      O('Clinician bookings at that time', 'int', DB), O('Room bookings at that time', 'int', RB),
      O('Free slots of the clinician that day', 'int', 'COUNTIFS({range:diary.clinician},{in:clin},{range:diary.date},{in:date},{range:diary.status},%s)' % tok('slotst', 'Free')),
      O('Verdict', 'text', 'IF(AND(%s>0,%s>0),%s,IF(%s>0,%s,IF(%s>0,%s,%s)))' % (DB, RB, cc('Room and clinician clash'), DB, cc('Clinician clash'), RB, ca('Room clash'), cc('Clear to book')))],
      GR('What if', ('Same clinician at 9', {'hour': 9}), ('Same clinician at 16', {'hour': 16}), ('Quiet Room', {'room': '=' + tok('room5', 'Quiet Room')}), ('In a week', {'date': '=({today}+8)'}))),
 TOOL('slot_pair', 'Fortnightly Slot Pairing', 'Can two fortnightly clients share one slot?',
      'Type the start dates, weekdays and hours of two fortnightly clients; see whether they fall on opposite weeks and the same slot, and the slots you save.', [
      I('da', 'First client, a start date', 'today-6', 'date'), I('db', 'Second client, a start date', 'today+1', 'date'), IN('wa', 'First client weekday', 'list', key('wday', 'Tuesday'), list='wday'),
      IN('wb', 'Second client weekday', 'list', key('wday', 'Tuesday'), list='wday'), I('ha', 'First client hour', 15), I('hb', 'Second client hour', 15)], [
      O('Weeks between the two start weeks', 'int', 'ABS(%s-%s)/7' % (WA, WB)), O('On opposite weeks (1 = yes)', 'int', 'IF(MOD(ABS(%s-%s)/7,2)=1,1,0)' % (WA, WB)), O('Same weekday and hour (1 = yes)', 'int', 'IF(AND({in:wa}={in:wb},{in:ha}={in:hb}),1,0)'),
      O('Weekly slots saved by sharing', 'num', 'IF(%s,1,0)' % SHARE13), O('Verdict', 'text', 'IF(%s,%s,%s)' % (SHARE13, cc('Can share one slot'), cc('Cannot share the slot')))],
      GR('What if', ('Same week, same slot', {'db': '=({today}-6)'}), ('Different hour', {'hb': 16}), ('Different weekday', {'wb': '=' + tok('wday', 'Thursday')}))),
 TOOL('closure_week', 'Closure Week Impact', 'What does a closure week cost?',
      'Type the days closed, sessions a day, the average fee and the share of pay saved; see sessions and revenue lost, profit lost, and the same from your own last 8 weeks of bookings.', [
      I('days', 'Days closed', 5), I('perday', 'Sessions a day', 17), I('fee', 'Average session fee', 128, 'money'), I('paysaved', 'Share of the fee saved in pay', 0.30, 'pct'), I('revenue', 'Revenue in a normal month', 47000, 'money')], [
      O('Sessions lost', 'int', '{in:days}*{in:perday}'), O('Revenue lost', 'money', '{in:days}*{in:perday}*{in:fee}'), O('Pay saved on sessions not held', 'money', '{in:days}*{in:perday}*{in:fee}*{in:paysaved}'),
      O('Profit lost', 'money', '{in:days}*{in:perday}*{in:fee}*(1-{in:paysaved})'), O('Share of a normal month', 'pct', '{in:days}*{in:perday}*{in:fee}/{in:revenue}'),
      O('Sessions booked in a normal week, last 8 weeks', 'int', AVG14), O('Sessions lost at your own recent pace', 'int', '{in:days}/6*' + AVG14),
      O('Verdict', 'text', 'IF({in:days}*{in:perday}*{in:fee}/{in:revenue}>0.15,%s,%s)' % (cc('Large closure impact'), cc('Small closure impact')))],
      GR('What if', ('Two days closed', {'days': 2}), ('Ten days closed', {'days': 10}), ('Half the usual sessions', {'perday': 9}), ('More pay saved, 45 percent', {'paysaved': 0.45}), ('Quiet month revenue', {'revenue': 36000}))),
 TOOL('sublet_rate', 'Sublet Rate Setter', 'What hourly rate does a sublet need?',
      'Type the room cost and cleaning per hour, your wanted margin, the hours and the rate now; see the rate that meets the margin, the margin now and the monthly profit.', [
      I('room', 'Room cost per hour', 12, 'money'), I('clean', 'Cleaning and supplies per hour', 3, 'money'), I('margin', 'Wanted margin', 0.25, 'pct'), I('hours', 'Hours a month', 60, 'num'), I('rate', 'Rate per hour now', 22, 'money')], [
      O('Cost per hour', 'money', COST15), O('Rate that meets the margin', 'money', REQ15), O('Margin at the rate now', 'pct', '1-%s/{in:rate}' % COST15), O('Profit a month at the rate now', 'money', '({in:rate}-%s)*{in:hours}' % COST15),
      O('Profit a month at the wanted rate', 'money', '(%s-%s)*{in:hours}' % (REQ15, COST15)), O('Hours a month to cover a fixed cost of 300', 'int', 'ROUNDUP(300/MAX(0.01,{in:rate}-%s),0)' % COST15),
      O('Verdict', 'text', 'IF({in:rate}>=%s,%s,%s)' % (REQ15, cc('Rate meets margin'), cc('Rate below margin')))],
      GR('What if', ('Rate 18', {'rate': 18}), ('Margin 40 percent', {'margin': 0.4}), ('Costly room, 18 an hour', {'room': 18}), ('Twice the hours', {'hours': 120}), ('Rate 28', {'rate': 28}))),
 TOOL('sublet_income', 'Sublet Income Planner', 'What would free room hours earn?',
      'Type the free room hours a week, the rate and the share you expect to let; see the income a month and a year, the extra over your last three months of sublets and a verdict.', [
      I('free', 'Free room hours a week', 40, 'num'), I('rate', 'Rate per hour', 22, 'money'), I('take', 'Share of the free hours let', 0.5, 'pct')], [
      O('Hours let a month', 'num', '{in:free}*{in:take}*4.33'), O('Income a month', 'money', '{in:free}*{in:take}*4.33*{in:rate}'), O('Income a year', 'money', '12*{in:free}*{in:take}*4.33*{in:rate}'),
      O('Average sublet income, last 3 complete months', 'money', 'SUMIFS({range:sublets.amount},{range:sublets.month},">="&EDATE(DATE(YEAR({today}),MONTH({today}),1),-3),{range:sublets.month},"<"&DATE(YEAR({today}),MONTH({today}),1))/3'),
      O('Extra a month over the last 3 months', 'money', '{in:free}*{in:take}*4.33*{in:rate}-SUMIFS({range:sublets.amount},{range:sublets.month},">="&EDATE(DATE(YEAR({today}),MONTH({today}),1),-3),{range:sublets.month},"<"&DATE(YEAR({today}),MONTH({today}),1))/3'),
      O('Rate less room cost per hour', 'money', '{in:rate}-{set:room_cost_hour}'), O('Verdict', 'text', 'IF({in:rate}>{set:room_cost_hour},%s,%s)' % (cc('Worth listing the hours'), cc('Not worth listing')))],
      GR('What if', ('Half the take-up', {'take': 0.25}), ('Full take-up', {'take': 1.0}), ('Rate 26', {'rate': 26}), ('Rate 11', {'rate': 11}), ('Only 10 free hours', {'free': 10}))),
 TOOL('heavy_day', 'Heavy Day Check', 'Is this clinician\'s day too heavy?',
      'Type the clinician, sessions that day, the longest run without a break and the break minutes; see contact hours, the rest share and the clinician\'s back-to-back sessions next week.', [
      IN('clin', 'Clinician', 'list', key('clin', 'Sofia Marchetti'), list='clin'), I('sessions', 'Sessions that day', 7), I('inrow', 'Most sessions in a row', 4), I('minutes', 'Session minutes', 50), I('brk', 'Break minutes between sessions', 10)], [
      O('Contact hours that day', 'num', '{in:sessions}*{in:minutes}/60'), O('Hours in a row without a long break', 'num', '{in:inrow}*({in:minutes}+{in:brk})/60'), O('Share of the day on breaks between sessions', 'pct', '{in:brk}/({in:minutes}+{in:brk})'),
      O('Most sessions in a row allowed', 'int', '{set:max_in_row}'), O('Sessions to break up', 'int', 'MAX(0,{in:inrow}-{set:max_in_row})'),
      O('Weekly cap of the clinician', 'int', 'IFERROR(INDEX({range:team.session_cap},MATCH({in:clin},{range:team.name},0)),0)'),
      O('Back-to-back sessions booked next week', 'int', 'SUMIFS({range:clin_weeks.back_to_back},{range:clin_weeks.clinician},{in:clin},{range:clin_weeks.week},%s+7)' % WK0),
      O('Verdict', 'text', 'IF({in:inrow}>{set:max_in_row},%s,%s)' % (cc('Heavy day: add a break'), cc('Day is balanced')))],
      GR('What if', ('Three in a row', {'inrow': 3}), ('Longer breaks, 20 minutes', {'brk': 20}), ('Light day, 4 sessions', {'sessions': 4, 'inrow': 2}), ('Five in a row, no break', {'inrow': 5, 'brk': 0}))),
 TOOL('missed_sens', 'Missed Session Sensitivity', 'What does each point of missed sessions cost?',
      'Type booked sessions, the fee, the missed share, the share of the fee charged and the share waived; see the monthly loss, the policy value and the share that costs 2 percent of revenue.', [
      I('booked', 'Booked sessions a month', 481), I('fee', 'Average session fee', 128, 'money'), I('miss', 'Missed and late-cancelled share', 0.046, 'pct'), I('charge', 'Share of the fee charged', 0.5, 'pct'), I('waived', 'Share of late fees waived', 0.33, 'pct')], [
      O('Missed and late-cancelled sessions', 'num', '{in:booked}*{in:miss}'), O('Fees not earned', 'money', '{in:booked}*{in:miss}*{in:fee}'), O('Net revenue lost a month', 'money', NET18('{in:miss}')), O('Net revenue lost a year', 'money', '12*' + NET18('{in:miss}')),
      O('Late-fee policy value a year', 'money', '12*{in:booked}*{in:miss}*{in:fee}*{in:charge}*(1-{in:waived})'), O('Cost of one more point of missed share, a month', 'money', NET18('0.01')),
      O('Missed share that costs 2 percent of revenue', 'pct', '0.02/(1-{in:charge}*(1-{in:waived}))'), O('Verdict', 'text', 'IF({in:miss}>{set:target_missed},%s,%s)' % (cb('Above target'), cb('Within target')))],
      GR('Missed share against net revenue lost', ('Missed 2 percent', {'miss': 0.02}), ('Missed 4 percent', {'miss': 0.04}), ('Missed 6 percent', {'miss': 0.06}), ('Missed 8 percent', {'miss': 0.08}), ('Missed 12 percent', {'miss': 0.12}),
         ('No late fee charged', {'charge': 0.0}), ('Full fee charged', {'charge': 1.0}))),
]
assert len(tools) == 18, len(tools)
