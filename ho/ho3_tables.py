"""Home Management suite part 3: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho3_lists import *
import ho3_data as DD


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def HOUSE(): return CA('household', 'Household', 'text', '{set:household}', 24)


YES = '{list:yesno.yes}'
A1, A2, C1, C2 = (tok('person', p) for p in PERSONS)
EVERY = tok('pgrp', 'Everyone')
DAILY, WEEKLY, FORTN, MONTHLY, QUART, TWICE, YEARLY = (tok('freq', f) for f in FREQS)
OKS, DUES, OVD = (tok('cstat', s) for s in STATUS)
MON, TUE, WED, THU, FRI, SAT, SUN = (tok('wday', d) for d in WEEKDAYS)
EARLY, LATE, OFF = (tok('shift', s) for s in SHIFTS)
ROT, BAL = tok('meth', 'Rotation'), tok('meth', 'Balance by points')
# first day of the week from Settings: 0 = Monday ... 6 = Sunday
WKK = '(' + '+'.join('({set:week_start}=%s)*%d' % (tok('wday', d), i + 1) for i, d in enumerate(WEEKDAYS[1:])) + ')'
WS = '({today}-MOD(WEEKDAY({today},2)-1-%s,7))' % WKK
def WSD(x): return '(%s-MOD(WEEKDAY(%s,2)-1-%s,7))' % (x, x, WKK)
W30 = '{today}-29'
def LOGW(col, who, lo, hi): return 'SUMIFS(%s,%s,%s,%s,">="&(%s),%s,"<="&(%s))' % (R('chore_log', col), R('chore_log', 'who'), who, R('chore_log', 'done'), lo, R('chore_log', 'done'), hi)
def TL(col, who): return 'IFERROR(INDEX({range:team.%s},MATCH(%s,{range:team.person},0))&"","")' % (col, who)
def OCI(idx, k): return 'IFERROR(INDEX({range:chores.chore},MATCH((%s)*100+%d,{range:chores.okey},0)),"")' % (idx, k)
PAU = '({col:paused}=%s)' % YES
OP = TL('phone', '{col:owner}')
NOTPAU = '{range:chores.paused},"<>"&' + YES
def LASTFAIL(w, cnt):
    """largest week number k <= w (1..13) that has a failed week; cnt(k) is the COUNTIFS text for week k with a miss"""
    return 'MAX(' + ','.join('IF(AND(%s>0,%d<=%s),%d,0)' % (cnt(k), k, w, k) for k in range(1, 14)) + ')'


settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('adult1', 'Adult 1 shown as', 'text', 'Adult 1'), S('adult2', 'Adult 2 shown as', 'text', 'Adult 2'),
    S('child1', 'Child 1, first name only', 'text', 'Jo'), S('child2', 'Child 2, first name only', 'text', 'Kit'), S('week_start', 'Week starts on', 'list', key('wday', 'Monday'), list='wday'),
    S('soon_days', 'Due soon window, days (typical, your own)', 'int', SOON_DAYS), S('agreed_split_a2', 'Adult 2 agreed share of adult minutes, your own agreement', 'pct', AGREED_SPLIT_A2),
    S('weekly_points_goal', "Children's weekly points goal, your own", 'int', 24), S('adult_points_goal', 'Adult weekly points goal, your own', 'int', 30),
    S('rot_method', 'Rotation method', 'list', key('meth', 'Rotation'), list='meth'), S('done_goal', 'Weekly completion goal for streaks', 'pct', 0.85),
    S('fair_band', 'In line when within this gap of share', 'pct', 0.05), S('free_work', 'Free minutes on a working evening, typical', 'int', 40),
    S('free_late', 'Free minutes on a late day or late shift, typical', 'int', 15), S('free_off', 'Free minutes on a day off, typical', 'int', 90),
    S('meeting_time', 'Time of the monthly chore meeting', 'text', '19:30'), S('pace_min', 'Deep clean pace, minutes a day', 'int', 90),
    S('deep_factor', 'A deep clean takes this many times the usual minutes', 'num', 1.5),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 team ------------------------------------------------------------------------------------
def OWN(k): return 'IF({col:idx}="","",%s)' % OCI('{col:idx}', k)
OWN_LIST = 'IF({col:idx}="","",' + '&'.join([OCI('{col:idx}', 1)] + ['IF(%s="","",", "&%s)' % (OCI('{col:idx}', k), OCI('{col:idx}', k)) for k in range(2, 7)]) + ')'
def RTM(w): return 'IF({col:person}="","",ROUND(SUMIFS({range:rotation.min_week},{range:rotation.w%d},{col:person}),0))' % w
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact; the messages use these phones. Minutes, share, points and the chores of each person fill in from the Chore log.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 17), LST('group', 'Group', 'tgroup', 11), C('phone', 'Phone', 'text', 18),
    C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11), C('first_name', 'First name', 'text', 12), C('next_date', 'Next date', 'date', 11),
    C('end_date', 'Until', 'date', 11), C('at_time', 'Time', 'time', 8),
    CA('person', 'Person in the chore sheets', 'text', 'IF({col:role}=%s,%s,IF({col:role}=%s,%s,IF({col:role}=%s,IF(LEFT({col:note},LEN(%s))=%s,%s,%s),"")))' % (tok('role', 'Adult 1'), A1, tok('role', 'Adult 2'), A2, tok('role', 'Child'), C1, C1, C1, C2), 12),
    CA('idx', 'Person number', 'int', 'IF({col:person}=%s,1,IF({col:person}=%s,2,IF({col:person}=%s,3,IF({col:person}=%s,4,""))))' % (A1, A2, C1, C2), 8),
    CA('mins30', 'Minutes last 30 days', 'int', 'IF({col:person}="","",%s)' % LOGW('minutes', '{col:person}', W30, '{today}'), 10),
    CA('pts_wk', 'Points this week', 'int', 'IF({col:person}="","",%s)' % LOGW('points', '{col:person}', WS, '{today}'), 9),
    CA('share30', 'Share of adult minutes', 'pct', 'IF(OR({col:person}=%s,{col:person}=%s),IFERROR({col:mins30}/(SUMIFS({range:team.mins30},{range:team.person},%s)+SUMIFS({range:team.mins30},{range:team.person},%s)),0),"")' % (A1, A2, A1, A2), 10),
    CA('agreed', 'Agreed share', 'pct', 'IF({col:person}=%s,{set:agreed_split_a2},IF({col:person}=%s,1-{set:agreed_split_a2},""))' % (A2, A1), 9),
    CA('goal_pts', 'Weekly points goal', 'int', 'IF(OR({col:person}=%s,{col:person}=%s),{set:weekly_points_goal},IF(OR({col:person}=%s,{col:person}=%s),{set:adult_points_goal},""))' % (C1, C2, A1, A2), 9),
    CA('c1a', 'Child 1 chore a', 'text', OCI('3', 1), 24), CA('c2a', 'Child 2 chore a', 'text', OCI('4', 1), 24), CA('c2b', 'Child 2 chore b', 'text', OCI('4', 2), 24),
    CA('own_list', 'Own chores', 'text', OWN_LIST, 40),
    CA('hidden_n', 'Hidden jobs held', 'int', 'IF({col:person}="","",COUNTIFS({range:chores.owner},{col:person},{range:chores.hidden},%s,%s))' % (YES, NOTPAU), 9),
    CA('hidden_min', 'Hidden minutes a month', 'int', 'IF({col:person}="","",SUMIFS({range:hidden.min_month},{range:hidden.owner},{col:person}))', 10),
    CA('week_date', 'Week of', 'date', WS, 11), CA('due_n', 'Chores due this week', 'int', 'COUNTIFS({range:chores.due_week},1)', 9),
    CA('overdue_n', 'Chores overdue', 'int', 'COUNTIFS({range:chores.status},%s)' % OVD, 9), CA('meeting_date', 'Next monthly chore meeting', 'date', '{today}+MOD(7-WEEKDAY({today},2),7)', 11),
    CA('child1', 'Child 1 shown as', 'text', '{set:child1}', 11),
    CA('a2_phone', 'Phone of adult 2', 'text', 'IF({col:person}=%s,{col:phone},"")' % A2, 16),
    CA('c1_phone', 'Phone of child 1', 'text', 'IF({col:person}=%s,{col:phone},"")' % C1, 16), CA('c2_phone', 'Phone of child 2', 'text', 'IF({col:person}=%s,{col:phone},"")' % C2, 16),
    CA('gp_phone', 'Phone of the grandparent', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Grandparent'), 16), CA('bs_phone', 'Phone of the babysitter', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Babysitter'), 16),
    CA('cp_phone', 'Phone of the carpool family', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Carpool family'), 16), CA('nb_phone', 'Phone of the neighbour', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Neighbour'), 16),
    CA('dw_phone', 'Phone of the dog walker', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'Dog walker'), 16), CA('sc_phone', 'Phone of the school office', 'text', 'IF({col:role}=%s,{col:phone},"")' % tok('role', 'School office'), 16),
    CA('hm_phone', 'Phone of an adult', 'text', 'IF(OR({col:person}=%s,{col:person}=%s),{col:phone},"")' % (A1, A2), 16), HOUSE()], DD.team_d(), 50))

# 2 chores ----------------------------------------------------------------------------------
INT_F = 'IF({col:frequency}=%s,1,IF({col:frequency}=%s,7,IF({col:frequency}=%s,14,IF({col:frequency}=%s,30,IF({col:frequency}=%s,91,IF({col:frequency}=%s,182,IF({col:frequency}=%s,365,"")))))))' % (DAILY, WEEKLY, FORTN, MONTHLY, QUART, TWICE, YEARLY)
FIRSTD = 'SUMPRODUCT(MIN({range:chore_log.done}+({range:chore_log.chore_id}<>{col:chore_id})*1000000))'
SPRING = 'DATE(YEAR({today})+IF({today}>DATE(YEAR({today}),4,12),1,0),4,12)'
RANKF = ('IF(%s,"",COUNTIFS(%s,{range:chores.days_to_due},"<"&{col:days_to_due})+COUNTIFS(%s,{range:chores.days_to_due},{col:days_to_due},{range:chores.minutes},">"&{col:minutes})'
         '+COUNTIFS(%s,{range:chores.days_to_due},{col:days_to_due},{range:chores.minutes},{col:minutes},{range:chores.seq},"<"&{col:seq})+1)') % (PAU, NOTPAU, NOTPAU, NOTPAU)
tables.append(T('chores', 'Chores', 'Recurring chores by room and frequency',
    'One row per recurring chore: room, frequency, minutes, default owner, effort points and last done; next due, overdue days, status and rank fill in. Tick Paused for a chore out of season.', [
    C('chore_id', 'Chore ID', 'text', 9, required=True), C('chore', 'Chore', 'text', 30), LST('room', 'Room', 'room', 13), LST('frequency', 'Frequency', 'freq', 12), C('minutes', 'Minutes', 'int', 8),
    LST('owner', 'Default owner', 'person', 12), C('points', 'Points', 'int', 8), C('hidden', 'Hidden job', 'bool', 9), C('paused', 'Paused', 'bool', 8), C('last_done', 'Last done', 'date', 11),
    CA('interval', 'Interval, days', 'int', INT_F, 8),
    CA('next_due', 'Next due', 'date', 'IF(%s,"",IF({col:last_done}>0,{col:last_done}+{col:interval},{today}))' % PAU, 11),
    CA('days_to_due', 'Days to due', 'int', 'IF({col:next_due}="","",{col:next_due}-{today})', 8),
    CA('overdue_days', 'Overdue days', 'int', 'IF({col:next_due}="",0,MAX(0,{today}-{col:next_due}))', 8),
    CA('status', 'Status', 'text', 'IF(%s,%s,IF({col:next_due}<{today},%s,IF({col:next_due}-{today}<=MIN({set:soon_days},ROUNDDOWN({col:interval}/2,0)),%s,%s)))' % (PAU, OKS, OVD, DUES, OKS), 10),
    CA('min_week', 'Minutes a week', 'num', 'IF(%s,0,ROUND({col:minutes}*7/{col:interval},1))' % PAU, 9), CA('pts_week', 'Points a week', 'num', 'IF(%s,0,ROUND({col:points}*7/{col:interval},1))' % PAU, 9),
    CA('per_day', 'Times a day', 'num', 'IF(%s,0,1/{col:interval})' % PAU, 8),
    CA('grp', 'Group, 1 adult 2 child', 'int', 'IF(OR({col:owner}=%s,{col:owner}=%s),1,IF(OR({col:owner}=%s,{col:owner}=%s),2,0))' % (A1, A2, C1, C2), 8),
    CA('seq', 'Number', 'int', 'VALUE(RIGHT({col:chore_id},2))', 7),
    CA('mrank', 'Rank by minutes in group', 'int', 'IF({col:grp}=0,"",COUNTIFS({range:chores.grp},{col:grp},{range:chores.minutes},">"&{col:minutes})+COUNTIFS({range:chores.grp},{col:grp},{range:chores.minutes},{col:minutes},{range:chores.seq},"<"&{col:seq})+1)', 9),
    CA('rank', 'Do first, 1 is most urgent', 'int', RANKF, 9),
    CA('first_done', 'First logged', 'date', 'IFERROR(IF(%s>=1000000,"",%s),"")' % (FIRSTD, FIRSTD), 11),
    CA('due_week', 'Due this week, 1 or 0', 'int', 'IF(%s,0,IF({col:next_due}<=%s+6,1,0))' % (PAU, WS), 8),
    CA('idx', 'Owner number', 'int', 'IF({col:owner}=%s,1,IF({col:owner}=%s,2,IF({col:owner}=%s,3,IF({col:owner}=%s,4,0))))' % (A1, A2, C1, C2), 7),
    CA('orank', 'Number of the owner', 'int', 'COUNTIFS({range:chores.owner},{col:owner},{range:chores.seq},"<"&{col:seq})+1', 8), CA('okey', 'Owner key', 'int', '{col:idx}*100+{col:orank}', 8),
    CA('rrank', 'Rank by minutes in room', 'int', 'COUNTIFS({range:chores.room},{col:room},{range:chores.minutes},">"&{col:minutes})+COUNTIFS({range:chores.room},{col:room},{range:chores.minutes},{col:minutes},{range:chores.seq},"<"&{col:seq})+1', 9),
    CA('rkey', 'Room key', 'text', '{col:room}&"-"&{col:rrank}', 14),
    CA('owner_first', 'Owner first name', 'text', TL('first_name', '{col:owner}'), 12),
    CA('spring_date', 'Spring clean day', 'date', 'IF(%s>0,%s+MOD(6-WEEKDAY(%s,2),7),"")' % (SPRING, SPRING, SPRING), 11),
    CA('a2_shift_due', 'Adult 2 shift on the due date', 'text', 'IFERROR(INDEX({range:work_pattern.adult2_shift},MATCH({col:next_due},{range:work_pattern.date},0))&"","")', 12),
    CA('agree_by', 'Agree who by', 'date', '{today}+3', 11),
    CA('a2late_phone', 'Phone, adult 2 late shift', 'text', 'IF(AND({col:owner}=%s,{col:a2_shift_due}=%s),%s,"")' % (A2, LATE, OP), 16),
    CA('od_phone', 'Phone, adult overdue', 'text', 'IF(AND({col:status}=%s,{col:grp}=1),%s,"")' % (OVD, OP), 16),
    CA('c1_phone', 'Phone, child 1 chore', 'text', 'IF({col:owner}=%s,%s,"")' % (C1, OP), 16), CA('soon_phone', 'Phone, due soon adult chore', 'text', 'IF(AND({col:status}=%s,{col:grp}=1),%s,"")' % (DUES, OP), 16),
    CA('deep_phone', 'Phone, deep clean due', 'text', 'IF(AND({col:frequency}=%s,{col:next_due}>={today},{col:next_due}<={today}+30),%s,"")' % (QUART, OP), 16),
    CA('spring_phone', 'Phone, yearly chore', 'text', 'IF({col:frequency}=%s,%s,"")' % (YEARLY, OP), 16), HOUSE()],
    DD.chores_d(), 80, [A('status', '= ' + OVD, 'bad'), A('status', '= ' + DUES, 'warn'), A('status', '= ' + OKS, 'good')]))

# 3 chore log -------------------------------------------------------------------------------
tables.append(T('chore_log', 'Chore log', 'Every chore done, who did it and how long it took',
    'One row per chore done: date, chore, room, who, minutes and effort points; the week, late-day flag and the by-default-owner flag fill in. The last 30 days feed the fairness check.', [
    C('log_id', 'Log ID', 'text', 9, required=True), C('done', 'Done on', 'date', 11), REF('chore_id', 'Chore ID', 'chores.chore_id', 9), C('chore', 'Chore', 'text', 30), LST('room', 'Room', 'room', 13),
    LST('who', 'Who', 'person', 11), C('minutes', 'Minutes', 'int', 8), C('points', 'Points', 'int', 8), LST('weekday', 'Weekday', 'wday', 11),
    CA('week_start', 'Week of', 'date', WSD('{col:done}'), 11),
    CA('late_day', 'Adult 1 late day, 1 or 0', 'int', 'IF(COUNTIFS({range:work_pattern.date},{col:done},{range:work_pattern.adult1_late},%s)>0,1,0)' % YES, 8),
    CA('hid', 'Hidden job, 1 or 0', 'int', 'IF(IFERROR(INDEX({range:chores.hidden},MATCH({col:chore_id},{range:chores.chore_id},0)),"")=%s,1,0)' % YES, 8),
    CA('freq_d', 'Daily chore, 1 or 0', 'int', 'IF(IFERROR(INDEX({range:chores.frequency},MATCH({col:chore_id},{range:chores.chore_id},0)),"")=%s,1,0)' % DAILY, 8),
    CA('by_owner', 'By the default owner, 1 or 0', 'int', 'IF(IFERROR(INDEX({range:chores.owner},MATCH({col:chore_id},{range:chores.chore_id},0)),"")={col:who},1,0)', 8),
    CA('last30', 'Last 30 days, 1 or 0', 'int', 'IF(AND({col:done}>=%s,{col:done}<={today}),1,0)' % W30, 8),
    CA('adult', 'Adult, 1 or 0', 'int', 'IF(OR({col:who}=%s,{col:who}=%s),1,0)' % (A1, A2), 7),
    CA('who_first', 'First name', 'text', TL('first_name', '{col:who}'), 11), CA('a2_phone', 'Phone of adult 2, last 7 days', 'text', 'IF(AND({col:who}=%s,{col:done}>={today}-6,{col:done}<={today}),%s,"")' % (A2, TL('phone', A2)), 16)],
    DD.log_d(), 3000))

# 4 rewards ---------------------------------------------------------------------------------
tables.append(T('rewards', 'Rewards', 'Reward ladder for the children, points only',
    'One row per reward with the points it needs; children earn points, never money. Type your own rewards in order of points.', [
    C('reward_id', 'Reward ID', 'text', 9, required=True), C('reward', 'Reward', 'text', 38), C('points', 'Points needed', 'int', 12, visual='bar')], DD.rewards_d(), 50))

# 5 work pattern ----------------------------------------------------------------------------
tables.append(T('work_pattern', 'Work pattern', 'Adult 1 late days and adult 2 shifts, day by day',
    'One row per day: adult 1 late day, adult 2 shift (Early, Late or Off) and the adults free for the evening; free minutes for chores fill in from Settings.', [
    C('shift_id', 'Shift ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('weekday', 'Weekday', 'wday', 11), C('adult1_late', 'Adult 1 late', 'bool', 9), LST('adult2_shift', 'Adult 2 shift', 'shift', 11),
    C('adults_free', 'Adults free', 'int', 9),
    CA('week_start', 'Week of', 'date', WSD('{col:date}'), 11),
    CA('a1_free', 'Adult 1 free minutes', 'int', 'IF(OR({col:weekday}=%s,{col:weekday}=%s),{set:free_off},IF({col:adult1_late}=%s,{set:free_late},{set:free_work}))' % (SAT, SUN, YES), 10),
    CA('a2_free', 'Adult 2 free minutes', 'int', 'IF({col:adult2_shift}=%s,{set:free_off},IF({col:adult2_shift}=%s,{set:free_late},{set:free_work}))' % (OFF, LATE), 10),
    CA('free_both', 'Free minutes, both adults', 'int', '{col:a1_free}+{col:a2_free}', 10),
    CA('this_week', 'This week, 1 or 0', 'int', 'IF(AND({col:date}>=%s,{col:date}<=%s+6),1,0)' % (WS, WS), 8),
    CA('a1_first', 'Adult 1 first name', 'text', TL('first_name', A1), 12), CA('a2_first', 'Adult 2 first name', 'text', TL('first_name', A2), 12),
    CA('a1_phone_late', 'Adult 1 phone on late days', 'text', 'IF({col:adult1_late}=%s,%s,"")' % (YES, TL('phone', A1)), 18), HOUSE()],
    DD.wp_d(), 400, [A('adult2_shift', '= ' + LATE, 'warn')]))

# 6 cleaning schedule by room ---------------------------------------------------------------
def CI(col): return 'IFERROR(INDEX({range:chores.%s},{col:pos}),"")' % col
def CD(col): return 'IFERROR(IF(INDEX({range:chores.%s},{col:pos})=0,"",INDEX({range:chores.%s},{col:pos})),"")' % (col, col)
def CT(k): return 'IFERROR(INDEX({range:chores.chore},MATCH({col:room}&"-"&%d,{range:chores.rkey},0)),"")' % k
tables.append(T('cleaning', 'Cleaning schedule by room', 'Next due and overdue days of every chore, room by room',
    'One row per chore in room order: last done, next due, overdue days and status from the Chores sheet, with the minutes and the deep clean of its room.', [
    REF('chore_id', 'Chore ID', 'chores.chore_id', 9, required=True),
    CA('pos', 'Row in Chores', 'int', 'IFERROR(MATCH({col:chore_id},{range:chores.chore_id},0),"")', 8), CA('chore', 'Chore', 'text', CI('chore'), 30), CA('room', 'Room', 'text', CI('room'), 13),
    CA('frequency', 'Frequency', 'text', CI('frequency'), 12), CA('last_done', 'Last done', 'date', CD('last_done'), 11), CA('next_due', 'Next due', 'date', CD('next_due'), 11),
    CA('overdue_days', 'Overdue days', 'int', CI('overdue_days'), 8), CA('status', 'Status', 'text', CI('status'), 10), CA('minutes', 'Minutes', 'int', CI('minutes'), 8),
    CA('room_n', 'Chores in the room', 'int', 'COUNTIFS({range:chores.room},{col:room},%s)' % NOTPAU, 9),
    CA('room_wk', 'Room minutes a week', 'int', 'ROUND(SUMIFS({range:chores.min_week},{range:chores.room},{col:room}),0)', 9),
    CA('room_over', 'Overdue chores in the room', 'int', 'COUNTIFS({range:chores.room},{col:room},{range:chores.status},%s)' % OVD, 9),
    CA('deep_min', 'Deep clean minutes of the room', 'int', 'ROUND({set:deep_factor}*SUMIFS({range:chores.minutes},{range:chores.room},{col:room},{range:chores.hidden},"<>"&%s,{range:chores.frequency},"<>"&%s,%s),0)' % (YES, DAILY, NOTPAU), 10),
    CA('deep_days', 'Deep clean days at the pace', 'int', 'ROUNDUP({col:deep_min}/{set:pace_min},0)', 9),
    CA('t1', 'Longest chore in the room', 'text', CT(1), 28), CA('t2', 'Second longest', 'text', CT(2), 28), CA('t3', 'Third longest', 'text', CT(3), 28), HOUSE()],
    DD.cs_d(), 80, [A('status', '= ' + OVD, 'bad'), A('status', '= ' + DUES, 'warn'), A('status', '= ' + OKS, 'good')]))

# 7 this week's cleaning plan ---------------------------------------------------------------
def PI(col): return 'IF({col:pos}="","",INDEX({range:chores.%s},{col:pos}))' % col
def PLN(k): return 'IFERROR(INDEX({range:cleaning_plan.chore},MATCH(%d,{range:cleaning_plan.rank},0))&" | "&INDEX({range:cleaning_plan.minutes},MATCH(%d,{range:cleaning_plan.rank},0))&" | "&INDEX({range:cleaning_plan.suggested},MATCH(%d,{range:cleaning_plan.rank},0)),"")' % (k, k, k)
SUGG = ('IF({col:chore}="","",IF(OR({col:owner}=%s,{col:owner}=%s),{col:owner},IF(OR({col:free_a1}="",{col:free_a2}=""),{col:owner},'
        'IF(AND({col:owner}=%s,{col:free_a1}<={set:free_late},{col:free_a2}>{set:free_late}),%s,IF(AND({col:owner}=%s,{col:free_a2}<={set:free_late},{col:free_a1}>{set:free_late}),%s,{col:owner})))))') % (C1, C2, A1, A2, A2, A1)
tables.append(T('cleaning_plan', "This week's cleaning plan", 'Most urgent chores first, with minutes and doer',
    'Ranks 1 to 30 are typed once; the chores fill in most urgent first, with minutes, the default owner and a suggested doer from the work pattern.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('pos', 'Row in Chores', 'int', 'IFERROR(MATCH({col:rank},{range:chores.rank},0),"")', 8),
    CA('chore', 'Chore', 'text', 'IF({col:pos}="","",INDEX({range:chores.chore},{col:pos}))', 30), CA('room', 'Room', 'text', PI('room'), 13),
    CA('due_date', 'Do by', 'date', 'IF({col:pos}="","",MAX(INDEX({range:chores.next_due},{col:pos}),{today}))', 11), CA('overdue_days', 'Overdue days', 'int', PI('overdue_days'), 8),
    CA('minutes', 'Minutes', 'int', PI('minutes'), 8), CA('owner', 'Default owner', 'text', PI('owner'), 12),
    CA('free_a1', 'Adult 1 free minutes that day', 'int', 'IF({col:pos}="","",IFERROR(INDEX({range:work_pattern.a1_free},MATCH({col:due_date},{range:work_pattern.date},0)),""))', 10),
    CA('free_a2', 'Adult 2 free minutes that day', 'int', 'IF({col:pos}="","",IFERROR(INDEX({range:work_pattern.a2_free},MATCH({col:due_date},{range:work_pattern.date},0)),""))', 10),
    CA('suggested', 'Suggested doer', 'text', SUGG, 12),
    CA('cum_min', 'Minutes so far', 'int', 'IF({col:pos}="","",SUMIFS({range:cleaning_plan.minutes},{range:cleaning_plan.rank},"<="&{col:rank}))', 9),
    CA('this_week', 'Due this week, 1 or 0', 'int', 'IF({col:pos}="","",IF({col:due_date}<=%s+6,1,0))' % WS, 8)] +
    [CA('l%d' % k, 'Plan line %d' % k, 'text', PLN(k), 44) for k in range(1, 7)] + [CA('week_date', 'Week of', 'date', WS, 11), HOUSE()],
    DD.plan_d(), 60, [A('overdue_days', '> 0', 'warn')]))

# 8 chore rotation by week ------------------------------------------------------------------
def RI(col): return 'IFERROR(INDEX({range:chores.%s},MATCH({col:chore_id},{range:chores.chore_id},0)),"")' % col
def PW(w): return ('IF({col:grp}=0,"",IF({col:swap}<>"",{col:swap},IF(MOD({col:side}+%d,2)=0,IF({col:grp}=1,%s,%s),IF({col:grp}=1,%s,%s))))' % (w - 1, A1, C1, A2, C2))
tables.append(T('rotation', 'Chore rotation by week', 'Who does each chore in the next four weeks',
    'One row per chore: week 1 to week 4 assigned by the rotation method in Settings (rotation or balance by points); type a person in the Swap cell to fix a chore to them.', [
    REF('chore_id', 'Chore ID', 'chores.chore_id', 9, required=True), CA('chore', 'Chore', 'text', RI('chore'), 30), CA('owner', 'Default owner', 'text', RI('owner'), 12),
    CA('minutes', 'Minutes', 'int', RI('minutes'), 8), CA('min_week', 'Minutes a week', 'num', RI('min_week'), 9), CA('pts_week', 'Points a week', 'num', RI('pts_week'), 9),
    CA('grp', 'Group', 'int', RI('grp'), 7), CA('mrank', 'Rank by minutes', 'int', RI('mrank'), 8),
    CA('side_rot', 'Side, rotation', 'int', 'IF(OR({col:owner}=%s,{col:owner}=%s),0,1)' % (A1, C1), 8),
    CA('side_bal', 'Side, balance by points', 'int', 'IF({col:grp}=0,0,IF(OR(MOD({col:mrank}-1,4)=1,MOD({col:mrank}-1,4)=2),1,0))', 8),
    CA('side', 'Side, chosen method', 'int', 'IF({set:rot_method}=%s,{col:side_rot},{col:side_bal})' % ROT, 8), LST('swap', 'Swap to', 'person', 11),
    CA('w1', 'Week 1', 'text', PW(1), 11), CA('w2', 'Week 2', 'text', PW(2), 11), CA('w3', 'Week 3', 'text', PW(3), 11), CA('w4', 'Week 4', 'text', PW(4), 11),
    CA('week_date', 'Week 1 starts', 'date', WS, 11), CA('w1_first', 'Week 1 first name', 'text', TL('first_name', '{col:w1}'), 12), CA('w1_phone', 'Week 1 phone', 'text', TL('phone', '{col:w1}'), 18), CA('a1_phone', 'Phone, adult 1 in week 1', 'text', 'IF({col:w1}=%s,%s,"")' % (A1, TL('phone', A1)), 16), HOUSE()],
    DD.rot_d(), 80))

# 9 load by person and week -----------------------------------------------------------------
def LWC(k): return 'COUNTIFS({range:load_week.person},{col:person},{range:load_week.wkn},%d,{range:load_week.at_goal},0)' % k
tables.append(T('load_week', 'Load by person and week', 'Minutes and points of each person over the last 13 weeks',
    'One row per person and week (week 13 is this week): minutes, points, the share of the week, the weekly points goal and the weeks in a row at goal fill in from the Chore log.', [
    C('wkn', 'Week number', 'int', 8, required=True), LST('person', 'Person', 'person', 11),
    CA('week_start', 'Week of', 'date', '%s-7*(13-{col:wkn})' % WS, 11),
    CA('minutes', 'Minutes', 'int', LOGW('minutes', '{col:person}', '{col:week_start}', '{col:week_start}+6'), 9, visual='bar'),
    CA('points', 'Points', 'int', LOGW('points', '{col:person}', '{col:week_start}', '{col:week_start}+6'), 9),
    CA('share', 'Share of the week', 'pct', 'IFERROR({col:minutes}/SUMIFS({range:load_week.minutes},{range:load_week.wkn},{col:wkn}),0)', 10),
    CA('goal', 'Weekly points goal', 'int', 'IF(OR({col:person}=%s,{col:person}=%s),{set:weekly_points_goal},{set:adult_points_goal})' % (C1, C2), 9),
    CA('at_goal', 'At goal, 1 or 0', 'int', 'IF({col:points}>={col:goal},1,0)', 8),
    CA('run', 'Weeks in a row at goal', 'int', 'IF({col:at_goal}=1,{col:wkn}-%s,0)' % LASTFAIL('{col:wkn}', LWC), 9)],
    DD.lw_d(), 60))

# 10 fairness -------------------------------------------------------------------------------
tables.append(T('fairness', 'Fairness last 30 days', 'Chore minutes of each person in the last 30 days',
    'One row per person: minutes done in the last 30 days and the share inside the group (adults or children); a view, never an alarm.', [
    LST('person', 'Person', 'pgrp', 14, required=True), CA('minutes', 'Minutes, last 30 days', 'int', 'IF({col:person}=%s,SUMIFS({range:chore_log.minutes},{range:chore_log.last30},1),%s)' % (EVERY, LOGW('minutes', '{col:person}', W30, '{today}')), 14, visual='bar'),
    CA('share', 'Share of adults or children', 'pct', 'IF({col:person}=%s,1,IFERROR({col:minutes}/IF(OR({col:person}=%s,{col:person}=%s),SUMIFS({range:fairness.minutes},{range:fairness.person},%s)+SUMIFS({range:fairness.minutes},{range:fairness.person},%s),SUMIFS({range:fairness.minutes},{range:fairness.person},%s)+SUMIFS({range:fairness.minutes},{range:fairness.person},%s)),0))' % (EVERY, A1, A2, A1, A2, C1, C2), 14)],
    DD.fa_d(), 50))

# 11 hidden jobs ----------------------------------------------------------------------------
tables.append(T('hidden', 'Hidden jobs', 'Planning, booking and remembering, beside the visible chores',
    'One row per hidden job (planning, booking, remembering): its default owner and the minutes a month it takes, from the Chores sheet.', [
    REF('chore', 'Hidden job', 'chores.chore', 34, required=True), CA('owner', 'Default owner', 'text', LKT('chores.owner', 'chores.chore', 'chore'), 14),
    CA('min_month', 'Minutes a month', 'int', 'IFERROR(ROUND(INDEX({range:chores.minutes},MATCH({col:chore},{range:chores.chore},0))*30/INDEX({range:chores.interval},MATCH({col:chore},{range:chores.chore},0)),0),0)', 13, visual='bar')],
    DD.hj_d(), 50))

# 12 children's points by week --------------------------------------------------------------
def OWNK(k): return 'IFERROR(INDEX({range:chores.chore},MATCH(IF({col:child}=%s,3,4)*100+%d,{range:chores.okey},0)),"")' % (C1, k)
OWNK_LIST = '&'.join([OWNK(1)] + ['IF(%s="","",", "&%s)' % (OWNK(k), OWNK(k)) for k in range(2, 5)])
tables.append(T('child_points', "Children's points by week", 'Points per child and week, goal and balance',
    'One row per child and week (week 13 is this week): type the points spent on a reward; points earned, goal reached and the balance carried forward fill in. Points, never money.', [
    C('cp_id', 'Row ID', 'text', 9, required=True), LST('wk', 'Week', 'wk', 9), LST('child', 'Child', 'kid', 9), C('spent', 'Points spent', 'int', 9),
    CA('wkn', 'Week number', 'int', 'VALUE(TRIM(RIGHT({col:wk},2)))', 8), CA('week_start', 'Week of', 'date', '%s-7*(13-{col:wkn})' % WS, 11),
    CA('points', 'Points earned', 'int', LOGW('points', '{col:child}', '{col:week_start}', '{col:week_start}+6'), 9), CA('goal', 'Weekly points goal', 'int', '{set:weekly_points_goal}', 9),
    CA('reached', 'Goal reached, 1 or 0', 'int', 'IF({col:points}>={col:goal},1,0)', 8), CA('to_goal', 'Points to goal', 'int', 'MAX(0,{col:goal}-{col:points})', 8),
    CA('balance', 'Balance carried forward', 'int', 'SUMIFS({range:child_points.points},{range:child_points.child},{col:child},{range:child_points.wkn},"<="&{col:wkn})-SUMIFS({range:child_points.spent},{range:child_points.child},{col:child},{range:child_points.wkn},"<="&{col:wkn})', 10),
    CA('first_name', 'First name', 'text', TL('first_name', '{col:child}'), 11), CA('phone', 'Phone, this week', 'text', 'IF({col:wkn}=13,%s,"")' % TL('phone', '{col:child}'), 18),
    CA('own1', 'Chore 1', 'text', OWNK(1), 24), CA('own2', 'Chore 2', 'text', OWNK(2), 24), CA('own_list', 'Chores', 'text', OWNK_LIST, 40),
    CA('weekend', 'Saturday', 'date', '%s+5' % WS, 11),
    CA('c1_phone', 'Phone of child 1, this week', 'text', 'IF({col:child}=%s,{col:phone},"")' % C1, 16), CA('c2_phone', 'Phone of child 2, this week', 'text', 'IF({col:child}=%s,{col:phone},"")' % C2, 16), HOUSE()],
    DD.cp_d(), 60, [A('reached', '= 1', 'good')]))

# 13 reward ladder --------------------------------------------------------------------------
tables.append(T('ladder', 'Reward ladder', 'Each child on the reward ladder: balance and points to go',
    'One row per child and reward: points needed, the balance now, points to go, the next reward and the weeks to reach it at the last four weeks pace.', [
    C('rl_id', 'Row ID', 'text', 9, required=True), LST('child', 'Child', 'kid', 9), REF('reward', 'Reward', 'rewards.reward', 36),
    CA('points_needed', 'Points needed', 'int', LKN('rewards.points', 'rewards.reward', 'reward'), 9),
    CA('balance', 'Balance now', 'int', 'SUMIFS({range:child_points.balance},{range:child_points.child},{col:child},{range:child_points.wkn},13)', 9),
    CA('to_go', 'Points to go', 'int', 'MAX(0,{col:points_needed}-{col:balance})', 9),
    CA('is_next', 'Next reward, 1 or 0', 'int', 'IF(AND({col:to_go}>0,COUNTIFS({range:ladder.child},{col:child},{range:ladder.to_go},">0",{range:ladder.points_needed},"<"&{col:points_needed})=0),1,0)', 9),
    CA('status', 'Status', 'text', 'IF({col:to_go}=0,%s,IF({col:is_next}=1,%s,%s))' % (tok('rstat', 'Can claim now'), tok('rstat', 'Next reward'), tok('rstat', 'Points to go')), 14),
    CA('avg_week', 'Points a week, last 4 weeks', 'num', 'IFERROR(AVERAGEIFS({range:child_points.points},{range:child_points.child},{col:child},{range:child_points.wkn},">=9",{range:child_points.wkn},"<=12"),0)', 11),
    CA('weeks_to_go', 'Weeks to go', 'int', 'IF({col:to_go}=0,0,IF({col:avg_week}>0,ROUNDUP({col:to_go}/{col:avg_week},0),""))', 8),
    CA('pts_wk', 'Points this week', 'int', 'SUMIFS({range:child_points.points},{range:child_points.child},{col:child},{range:child_points.wkn},13)', 9),
    CA('first_name', 'First name', 'text', TL('first_name', '{col:child}'), 11), CA('phone_c1', 'Phone, next reward of Child 1', 'text', 'IF(AND({col:is_next}=1,{col:child}=%s),%s,"")' % (C1, TL('phone', '{col:child}')), 18),
    CA('phone_c2', 'Phone, next reward of Child 2', 'text', 'IF(AND({col:is_next}=1,{col:child}=%s),%s,"")' % (C2, TL('phone', '{col:child}')), 18), HOUSE()],
    DD.rl_d(), 50, [A('status', '= ' + tok('rstat', 'Can claim now'), 'good'), A('status', '= ' + tok('rstat', 'Next reward'), 'warn')]))

# 14 laundry rota ---------------------------------------------------------------------------
tables.append(T('laundry', 'Laundry rota', 'Laundry loads by type, usual day and next change date',
    'One row per load type: usual day, who, loads a week, minutes per load, the change interval (typical, your own) and the last change; next change, status and the busiest day fill in.', [
    LST('load', 'Load type', 'ltype', 24, required=True), LST('usual_day', 'Usual day', 'wday', 11), LST('who', 'Who', 'person', 10), C('loads_wk', 'Loads a week', 'num', 9),
    C('minutes', 'Minutes per load', 'int', 9), C('interval_days', 'Change every, days', 'int', 9), C('last_changed', 'Last changed', 'date', 11),
    CA('next_change', 'Next change', 'date', 'IF({col:last_changed}>0,{col:last_changed}+{col:interval_days},"")', 11), CA('days_to', 'Days to the change', 'int', 'IF({col:next_change}="","",{col:next_change}-{today})', 9),
    CA('status', 'Status', 'text', 'IF({col:next_change}="","",IF({col:next_change}<{today},%s,IF({col:next_change}-{today}<=MIN({set:soon_days},ROUNDDOWN({col:interval_days}/2,0)),%s,%s)))' % (OVD, DUES, OKS), 10),
    CA('min_week', 'Minutes a week', 'num', '{col:loads_wk}*{col:minutes}', 9),
    CA('day_loads', 'Loads on this day', 'num', 'SUMIFS({range:laundry.loads_wk},{range:laundry.usual_day},{col:usual_day})', 9),
    CA('busy_day', 'Busiest day', 'text', 'IFERROR(INDEX({range:laundry.usual_day},MATCH(MAX({range:laundry.day_loads}),{range:laundry.day_loads},0))&"","")', 11),
    CA('loads_total', 'Loads a week, all types', 'num', 'SUM({range:laundry.loads_wk})', 9), CA('week_date', 'Week of', 'date', WS, 11),
    CA('who_first', 'First name', 'text', TL('first_name', '{col:who}'), 11), CA('phone', 'Phone', 'text', TL('phone', '{col:who}'), 18), HOUSE()],
    DD.ld_d(), 50, [A('status', '= ' + OVD, 'bad'), A('status', '= ' + DUES, 'warn')]))

# 15 chore history by month -----------------------------------------------------------------
def HMS(who): return 'SUMIFS({range:chore_log.minutes},{range:chore_log.who},%s,{range:chore_log.done},">="&{col:month},{range:chore_log.done},"<"&EDATE({col:month},1))' % who
DUEM = ('ROUND(SUMPRODUCT(--({range:chores.first_done}<=EOMONTH({col:month},0)),--({range:chores.paused}<>%s),{range:chores.per_day})*MIN(DAY(EOMONTH({col:month},0)),{today}-{col:month}+1),0)' % YES)
tables.append(T('history', 'Chore history by month', 'Minutes, adult 2 share, done and missed by month',
    'One row per month (the 1st of the month): minutes of adult 1, adult 2 and the children, adult 2 share of adult minutes, chores done and missed; the current month counts days to date.', [
    C('month', 'Month', 'date', 11, required=True), CA('a1_min', 'Adult 1 minutes', 'int', HMS(A1), 10), CA('a2_min', 'Adult 2 minutes', 'int', HMS(A2), 10),
    CA('kids_min', 'Children minutes', 'int', '%s+%s' % (HMS(C1), HMS(C2)), 10), CA('a2_share', 'Adult 2 share of adult minutes', 'pct', 'IFERROR({col:a2_min}/({col:a1_min}+{col:a2_min}),0)', 11),
    CA('avg3', 'Adult 2 share, 3 months before', 'pct', 'IFERROR(AVERAGEIFS({range:history.a2_share},{range:history.month},">="&EDATE({col:month},-3),{range:history.month},"<"&{col:month}),0)', 11),
    CA('done', 'Chores done', 'int', 'COUNTIFS({range:chore_log.done},">="&{col:month},{range:chore_log.done},"<"&EDATE({col:month},1))', 9),
    CA('due', 'Chores due', 'int', DUEM, 9), CA('missed', 'Chores missed', 'int', 'MAX(0,{col:due}-{col:done})', 9),
    CA('first_name', 'Adult 1 first name', 'text', TL('first_name', A1), 12), CA('phone', 'Adult 1 phone', 'text', TL('phone', A1), 18), HOUSE()],
    DD.hm_d(), 60))

# 16 done and missed by week ----------------------------------------------------------------
def DMC(k): return 'COUNTIFS({range:done_missed.wkn},%d,{range:done_missed.at_goal},0)' % k
DUEW = 'ROUND(SUMPRODUCT(--({range:chores.first_done}<={col:week_start}+6),--({range:chores.paused}<>%s),{range:chores.per_day})*MIN(7,{today}-{col:week_start}+1),0)' % YES
tables.append(T('done_missed', 'Done and missed by week', 'Chores due, done and missed in the last 13 weeks',
    'One row per week (week 13 is this week, counted to today): chores due from the intervals, done from the Chore log, missed and the share done; weeks in a row at your completion goal.', [
    LST('wk', 'Week', 'wk', 9, required=True), CA('wkn', 'Week number', 'int', 'VALUE(TRIM(RIGHT({col:wk},2)))', 8), CA('week_start', 'Week of', 'date', '%s-7*(13-{col:wkn})' % WS, 11),
    CA('due', 'Chores due', 'int', DUEW, 9), CA('done', 'Chores done', 'int', 'COUNTIFS({range:chore_log.done},">="&{col:week_start},{range:chore_log.done},"<="&MIN({col:week_start}+6,{today}))', 9),
    CA('missed', 'Chores missed', 'int', 'MAX(0,{col:due}-{col:done})', 9), CA('share_done', 'Share done', 'pct', 'IF({col:due}>0,MIN(1,{col:done}/{col:due}),"")', 9),
    CA('at_goal', 'At goal, 1 or 0', 'int', 'IF({col:share_done}="","",IF({col:share_done}>={set:done_goal},1,0))', 8),
    CA('run', 'Weeks in a row at goal', 'int', 'IF({col:at_goal}=1,{col:wkn}-%s,0)' % LASTFAIL('{col:wkn}', DMC), 9),
    CA('meeting_date', 'Next monthly chore meeting', 'date', '{today}+MOD(7-WEEKDAY({today},2),7)', 11), CA('meeting_time', 'Meeting time', 'text', '{set:meeting_time}', 9),
    CA('due_n', 'Chores due this week', 'int', 'COUNTIFS({range:chores.due_week},1)', 9), CA('overdue_n', 'Chores overdue', 'int', 'COUNTIFS({range:chores.status},%s)' % OVD, 9),
    CA('first_name', 'Adult 2 first name', 'text', TL('first_name', A2), 12), CA('phone', 'Adult 2 phone, this week', 'text', 'IF({col:wkn}=13,%s,"")' % TL('phone', A2), 18), HOUSE()],
    DD.dm_d(), 50))

# 17 streaks by person ----------------------------------------------------------------------
tables.append(T('streaks', 'Streaks by person', 'Weeks in a row at the weekly points goal',
    'One row per person: the weeks in a row at the points goal ending last week, and the longest run of the 13 weeks.', [
    LST('person', 'Person', 'pgrp', 14, required=True), CA('streak', 'Weeks in a row at goal', 'int', 'IF({col:person}=%s,MIN(%s),SUMIFS({range:load_week.run},{range:load_week.person},{col:person},{range:load_week.wkn},12))' % (EVERY, ','.join('SUMIFS({range:load_week.run},{range:load_week.person},%s,{range:load_week.wkn},12)' % p for p in (A1, A2, C1, C2))), 14),
    CA('longest', 'Longest run', 'int', 'IF({col:person}=%s,"",MAX(' % EVERY + ','.join('IF(COUNTIFS({range:load_week.person},{col:person},{range:load_week.run},%d)>0,%d,0)' % (k, k) for k in range(1, 14)) + '))', 12)],
    DD.st_d(), 50))

# 18 away-week scenario ---------------------------------------------------------------------
tables.append(T('away', 'Away-week scenario', 'Who is away on which day and what moves',
    'One row per away day: the person, the hours away and a note; the chores and minutes of that person on the day, who covers and the unowned chores fill in.', [
    C('away_id', 'Away ID', 'text', 9, required=True), C('day', 'Day', 'date', 11), LST('person', 'Person away', 'person', 12), C('hours', 'Hours away', 'int', 9), C('note', 'Note', 'text', 30),
    CA('owned_n', 'Chores of the person that day', 'int', 'COUNTIFS({range:chores.owner},{col:person},{range:chores.frequency},%s,%s)+COUNTIFS({range:chores.owner},{col:person},{range:chores.next_due},{col:day},{range:chores.frequency},"<>"&%s)' % (DAILY, NOTPAU, DAILY), 10),
    CA('owned_min', 'Minutes of the person that day', 'int', 'SUMIFS({range:chores.minutes},{range:chores.owner},{col:person},{range:chores.frequency},%s,%s)+SUMIFS({range:chores.minutes},{range:chores.owner},{col:person},{range:chores.next_due},{col:day},{range:chores.frequency},"<>"&%s)' % (DAILY, NOTPAU, DAILY), 10),
    CA('cover', 'Covered by', 'text', 'IF({col:person}=%s,%s,IF({col:person}=%s,%s,IFERROR(IF(INDEX({range:work_pattern.a1_free},MATCH({col:day},{range:work_pattern.date},0))>=INDEX({range:work_pattern.a2_free},MATCH({col:day},{range:work_pattern.date},0)),%s,%s),%s)))' % (A1, A2, A2, A1, A1, A2, A1), 11),
    CA('cover_first', 'Cover first name', 'text', TL('first_name', '{col:cover}'), 12), CA('cover_phone', 'Cover phone', 'text', TL('phone', '{col:cover}'), 18),
    CA('away_from', 'Away from', 'date', 'IF(SUMPRODUCT(MIN({range:away.day}+({range:away.person}<>{col:person})*1000000))>=1000000,"",SUMPRODUCT(MIN({range:away.day}+({range:away.person}<>{col:person})*1000000)))', 11),
    CA('away_to', 'Away until', 'date', 'SUMPRODUCT(MAX({range:away.day}*({range:away.person}={col:person})))', 11),
    CA('unowned', 'Chores unowned until then', 'int', 'COUNTIFS({range:chores.owner},{col:person},{range:chores.next_due},"<="&{col:away_to},%s)' % NOTPAU, 10), HOUSE()],
    DD.aw_d(), 50))

# 19 room load ------------------------------------------------------------------------------
tables.append(T('room_load', 'Room load', 'Chore minutes a week and overdue chores of each room',
    'One row per room: the minutes a week of its chores and how many are overdue.', [
    LST('room', 'Room', 'room', 16, required=True), CA('min_week', 'Minutes a week', 'int', 'ROUND(SUMIFS({range:chores.min_week},{range:chores.room},{col:room}),0)', 13, visual='bar'),
    CA('overdue', 'Overdue chores', 'int', 'COUNTIFS({range:chores.room},{col:room},{range:chores.status},%s)' % OVD, 13)], DD.rm_d(), 50))

# 20 frequency summary ----------------------------------------------------------------------
tables.append(T('freq_sum', 'Frequency summary', 'Chores and minutes a week by frequency',
    'One row per frequency: how many chores repeat that often and the minutes a week they take.', [
    LST('frequency', 'Frequency', 'freq', 16, required=True), CA('chores', 'Chores', 'int', 'COUNTIFS({range:chores.frequency},{col:frequency},%s)' % NOTPAU, 11),
    CA('min_week', 'Minutes a week', 'int', 'ROUND(SUMIFS({range:chores.min_week},{range:chores.frequency},{col:frequency}),0)', 13, visual='bar')], DD.fq_d(), 50))
assert len(tables) == 20, len(tables)
