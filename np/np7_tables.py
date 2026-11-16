"""Nonprofit suite part 7: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np7_lists import *
import np7_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def ORG(): return CA('org', 'Organization', 'text', '{set:org}', 22)
def CPH(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def R(t, c): return '{range:%s.%s}' % (t, c)
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
YN = 'YEAR({today})'
THIS3 = tok('yr3', 'This year'); THIS2 = tok('yr2', 'This year'); THIS4 = tok('yr', 'This year')
HELD = tok('mstatus', 'Held'); PLANNED = tok('mstatus', 'Planned')
PRESENT = tok('attend', 'Present')
FILED = tok('dclstatus', 'Filed'); OBDONE = tok('obstatus', 'Done')
def YR3N(col): return 'IF(%s=%s,%s,IF(%s=%s,%s-1,%s-2))' % (col, THIS3, YN, col, tok('yr3', 'Last year'), YN, YN)
def YR2N(col): return 'IF(%s=%s,%s,%s-1)' % (col, THIS2, YN, YN)
def YR4N(col): return 'IF(%s=%s,%s,IF(%s=%s,%s-1,IF(%s=%s,%s-2,%s+1)))' % (col, THIS4, YN, col, tok('yr', 'Last year'), YN, col, tok('yr', 'Two years ago'), YN, YN)
JAN1 = 'DATE(YEAR({today}),1,1)'

settings = [
    S('org', 'Your organization name', 'text', COMPANY), S('board_seats', 'Board seats set by your own rules', 'int', BOARD_SEATS), S('quorum_number', 'Members needed for a quorum, your own rules', 'int', 6),
    S('attend_min', 'Attendance share you expect of each member', 'pct', ATTEND_MIN), S('give_or_get', 'Give or get a year for each member, your own policy', 'money', GIVE_OR_GET),
    S('min_committee', 'Fewest members you want on a committee', 'int', 4), S('term_window', 'Months ahead that count as terms ending soon', 'int', 6),
    S('minutes_days', 'Days after a meeting that the minutes should be final', 'int', 21), S('papers_days', 'Days before a meeting that papers go out', 'int', 7),
    S('ob_warn_days', 'Days ahead that an obligation is flagged', 'int', 30), S('reserve_months', 'Months of reserve, starting point, set your own', 'num', RESERVE_MONTHS),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 board ---------------------------------------------------------------------
BM = lambda col: 'IFERROR(INDEX({range:board.%s},MATCH({col:name},{range:board.name},0)),"")' % col
tables.append(T('board', 'Board Members', 'Board roster with roles, committees and terms',
    'One row per board member, serving or former: role, committee, term dates and two skills; months to term end, next meeting, attendance, giving and declaration date fill in.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'brole', 12), LST('committee', 'Committee', 'committee', 13), C('term_start', 'Term start', 'date', 11), C('term_end', 'Term end', 'date', 11),
    C('terms_served', 'Terms served', 'int', 8), LST('skill', 'Skill', 'skill', 15), LST('skill2', 'Second skill', 'skill', 15), C('donor_id', 'Donor ID', 'text', 9), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    CA('months_left', 'Months to term end', 'num', 'IF({col:term_end}>={today},ROUND(({col:term_end}-{today})/30.4375,1),0)', 9), CA('serving', 'Serving', 'int', 'IF({col:term_end}>={today},1,0)', 7),
    CA('ends_soon', 'Term ends soon', 'int', 'IF(AND({col:serving}=1,{col:term_end}<=EDATE({today},{set:term_window})),1,0)', 8),
    CA('next_date', 'Next board meeting', 'date', 'IFERROR(SMALL(%s,1),"")' % R('meetings', 'next_board'), 11),
    CA('next_time', 'Next meeting time', 'time', 'IFERROR(INDEX(%s,MATCH({col:next_date},%s,0)),"")' % (R('meetings', 'start_time'), R('meetings', 'next_board')), 9),
    CA('confirmed', 'Confirmed for the next meeting', 'int', 'IFERROR(INDEX(%s,MATCH({col:next_date},%s,0)),"")' % (R('meeting_plan', 'confirmed'), R('meeting_plan', 'date')), 9),
    CA('last_date', 'Last board meeting held', 'date', 'IFERROR(LARGE(%s,1),"")' % R('meetings', 'held_board'), 11),
    CA('decl_due', 'Declaration due', 'date', 'IFERROR(IF(SUMIFS(%s,%s,{col:member_id},%s,%s)=0,"",SUMIFS(%s,%s,{col:member_id},%s,%s)),"")' % (R('declarations', 'due_date'), R('declarations', 'member_id'), R('declarations', 'year'), THIS3,
                                                                                                                                                  R('declarations', 'due_date'), R('declarations', 'member_id'), R('declarations', 'year'), THIS3), 11),
    CA('committee_date', 'Next meeting of the committee', 'date', 'IFERROR(1/SUMPRODUCT(MAX((%s={col:committee})*(%s=%s)*(%s>0)/(%s+(%s=0)))),"")' % (R('meetings', 'kind'), R('meetings', 'status'), PLANNED, R('meetings', 'date'), R('meetings', 'date'), R('meetings', 'date')), 11),
    CA('att_share', 'Attendance this year', 'pct', 'IF(COUNTIFS(%s,{col:name},%s,%s)=0,"",SUMIFS(%s,%s,{col:name},%s,%s))' % (R('attendance_member', 'member'), R('attendance_member', 'period'), THIS3, R('attendance_member', 'share'), R('attendance_member', 'member'), R('attendance_member', 'period'), THIS3), 9),
    CA('gifts_total', 'Gifts this year', 'money', 'SUMIFS(%s,%s,{col:name},%s,%s)' % (R('board_giving', 'total'), R('board_giving', 'member'), R('board_giving', 'period'), THIS3), 11),
    CA('gg_total', 'Given and raised this year', 'money', 'SUMIFS(%s,%s,{col:name},%s,%s)' % (R('give_or_get', 'total'), R('give_or_get', 'member'), R('give_or_get', 'period'), THIS2), 11),
    CA('gg_target', 'Give or get target', 'money', '{set:give_or_get}', 11), CPH('chair_phone', 'Chair phone', D.CHAIR_PHONE), ORG()],
    D.board_d(), 40, [A('months_left', '<= {set:term_window}', 'warn')]))
# 2 board roles ---------------------------------------------------------------
tables.append(T('board_roles', 'Board Roles', 'Board roles with term length and term limit',
    'One row per role: the years of a term and the most terms one member may serve, your own rules; the roster uses them to show who can renew.', [
    LST('role', 'Role', 'brole', 16, required=True), C('term_years', 'Term years', 'int', 9), C('max_terms', 'Most terms', 'int', 9)], D.roles_d(), 30))
# 3 committees ----------------------------------------------------------------
tables.append(T('committees', 'Committees', 'Committees with their chair and meeting rhythm',
    'One row per committee: its chair and when it meets; the roster counts its members.', [
    C('committee', 'Committee', 'text', 16, required=True), LST('chair', 'Chair', 'bmember', 24), C('meets', 'Meets', 'text', 30)], D.committees_d(), 20))
# 4 skills --------------------------------------------------------------------
tables.append(T('skills', 'Skills', 'Skills the board needs',
    'One row per skill: how many members you want to hold it and what it is for, your own view.', [
    LST('skill', 'Skill', 'skill', 18, required=True), C('needed', 'Members needed', 'int', 9), C('note', 'What it is for', 'text', 30)], D.skills_d(), 20))
# 5 terms ending --------------------------------------------------------------
TE = lambda col: 'IFERROR(INDEX({range:board.%s},MATCH({col:member},{range:board.name},0)),"")' % col
tables.append(T('terms_ending', 'Terms Ending', 'Terms ranked by the date they end',
    'One row per member: pick the year the term ends; the term end, months left, terms served, the term limit, whether the member can renew and the rank fill in from the roster.', [
    REF('member', 'Member', 'board.name', 24, required=True), LST('ends_in', 'Term ends in', 'yend', 14),
    CA('member_id', 'Member ID', 'text', TE('member_id'), 9), CA('role', 'Role', 'text', TE('role') + '&""', 12), CA('term_end', 'Term end', 'date', LKD('board.term_end', 'board.name', 'member'), 11),
    CA('months_left', 'Months left', 'num', 'IFERROR(INDEX(%s,MATCH({col:member},%s,0)),0)' % (R('board', 'months_left'), R('board', 'name')), 8),
    CA('terms_served', 'Terms served', 'int', 'IFERROR(INDEX(%s,MATCH({col:member},%s,0)),0)' % (R('board', 'terms_served'), R('board', 'name')), 8),
    CA('max_terms', 'Most terms', 'int', 'IFERROR(INDEX(%s,MATCH({col:role},%s,0)),0)' % (R('board_roles', 'max_terms'), R('board_roles', 'role')), 8),
    CA('serving', 'Serving', 'int', 'IFERROR(INDEX(%s,MATCH({col:member},%s,0)),0)' % (R('board', 'serving'), R('board', 'name')), 7),
    CA('can_renew', 'Can renew', 'text', 'IF({col:serving}=0,"",IF({col:terms_served}<{col:max_terms},%s,%s))' % (c1('Can renew'), c1('Term limit reached')), 16),
    CA('ending_soon', 'Ends within the window', 'int', 'IF(AND({col:serving}=1,{col:months_left}<={set:term_window}),1,0)', 8),
    CA('skill', 'Skill', 'text', TE('skill') + '&""', 15), CA('sort_key', 'Sort key', 'num', 'IF({col:serving}=1,{col:term_end}+VALUE(RIGHT({col:member_id},2))/1000,"")', 11),
    CA('rank', 'Rank', 'int', 'IF(ISNUMBER({col:sort_key}),COUNTIF(%s,"<"&{col:sort_key})+1,"")' % R('terms_ending', 'sort_key'), 6),
    CA('check', 'Year check', 'text', 'IF(OR(AND(YEAR({col:term_end})<=%s,{col:ends_in}=%s),AND(YEAR({col:term_end})=%s+1,{col:ends_in}=%s),AND(YEAR({col:term_end})=%s+2,{col:ends_in}=%s),AND(YEAR({col:term_end})>=%s+3,{col:ends_in}=%s)),%s,%s)' % (
        YN, tok('yend', 'This year'), YN, tok('yend', 'Next year'), YN, tok('yend', 'In two years'), YN, tok('yend', 'In three years'), c2('OK'), c2('Watch')), 8),
    CA('phone', 'Phone', 'text', LKT('board.phone', 'board.name', 'member'), 18), CA('ending_n', 'Terms ending soon', 'int', 'SUM(%s)' % R('terms_ending', 'ending_soon'), 8), CPH('chair_phone', 'Chair phone', D.CHAIR_PHONE), ORG()],
    D.terms_ending_d(), 20, [A('can_renew', '= ' + c1('Term limit reached'), 'warn'), A('months_left', '<= {set:term_window}', 'warn')]))
# 6 seats ---------------------------------------------------------------------
SE = lambda col: 'IFERROR(INDEX({range:board.%s},MATCH({col:member},{range:board.name},0)),"")' % col
tables.append(T('seats', 'Seats', 'Board seats, filled and vacant',
    'One row per seat you set by your own rules: its role and who holds it (leave the member blank for an open seat); the committee, the term end, a note and the vacancy fill in by themselves.', [
    C('seat_id', 'Seat ID', 'text', 9, required=True), LST('seat', 'Seat', 'brole', 12), LST('member', 'Member', 'bmember', 24), C('call_on', 'Call with a candidate on', 'date', 11),
    CA('member_id', 'Member ID', 'text', SE('member_id') + '&""', 9), CA('committee', 'Committee', 'text', SE('committee') + '&""', 13), CA('term_end', 'Term end', 'date', LKD('board.term_end', 'board.name', 'member'), 11),
    CA('months_left', 'Months left', 'num', 'IF({col:member}="","",IFERROR(INDEX(%s,MATCH({col:member},%s,0)),""))' % (R('board', 'months_left'), R('board', 'name')), 8),
    CA('filled', 'Filled', 'int', 'IF({col:member}<>"",1,0)', 7), CA('vacant', 'Vacant', 'int', '1-{col:filled}', 7),
    CA('note', 'Note', 'text', 'IF({col:filled}=0,%s,IF(%s<>{col:seat},%s,IF({col:months_left}<={set:term_window},%s,%s)))' % (c1('Open now'), SE('role') + '&""', c1('Role differs'), c1('Term ends soon'), c1('Filled')), 14),
    CA('vacant_n', 'Seats vacant', 'int', 'SUM(%s)' % R('seats', 'vacant'), 7),
    CA('gap_skill', 'Skill to recruit for', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0))&"","")' % (R('skills_matrix', 'skill'), R('skills_matrix', 'gap_score'), R('skills_matrix', 'gap_score')), 16),
    CA('next_date', 'Next board meeting', 'date', 'IFERROR(SMALL(%s,1),"")' % R('meetings', 'next_board'), 11), CPH('chair_phone', 'Chair phone', D.CHAIR_PHONE), ORG()],
    D.seats_d(), 30, [A('note', '= ' + c1('Open now'), 'bad'), A('note', '= ' + c1('Term ends soon'), 'warn')]))
# 7 skills matrix -------------------------------------------------------------
MEM = ('COUNTIFS(%s,{col:skill},%s,">="&{col:date_at})+COUNTIFS(%s,{col:skill},%s,"<>"&{col:skill},%s,">="&{col:date_at},%s,"<>")' % (R('board', 'skill'), R('board', 'term_end'), R('board', 'skill2'), R('board', 'skill'), R('board', 'term_end'), R('board', 'member_id')))
tables.append(T('skills_matrix', 'Skills Matrix', 'Skills held now, in 6 months and in 12 months',
    'One row per skill and point in time: the members who hold the skill and are still serving at that date against the number you need; the gap and a flag fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('skill', 'Skill', 'skill', 18), LST('when', 'At', 'when', 13),
    CA('date_at', 'Date', 'date', 'IF({col:when}=%s,{today},IF({col:when}=%s,EDATE({today},6),EDATE({today},12)))' % (tok('when', 'Now'), tok('when', 'In 6 months')), 11),
    CA('members', 'Members with the skill', 'int', MEM, 9), CA('needed', 'Members needed', 'int', LKN('skills.needed', 'skills.skill', 'skill'), 9), CA('gap', 'Gap', 'int', 'MAX(0,{col:needed}-{col:members})', 6),
    CA('flag', 'Flag', 'text', 'IF({col:members}=0,%s,IF({col:gap}=0,%s,IF({col:gap}=1,%s,%s)))' % (c1('No member'), c1('Covered'), c1('One short'), c1('Short of two or more')), 18),
    CA('gap_score', 'Gap score in 6 months', 'int', 'IF(AND({col:when}=%s,{col:gap}>0),{col:gap}*100+10-IFERROR(MATCH({col:skill},%s,0),9),"")' % (tok('when', 'In 6 months'), R('skills', 'skill')), 9),
    CA('leaving', 'Leaving by then', 'int', '(COUNTIFS(%s,{col:skill},%s,">="&{today})+COUNTIFS(%s,{col:skill},%s,"<>"&{col:skill},%s,">="&{today},%s,"<>"))-{col:members}' % (R('board', 'skill'), R('board', 'term_end'), R('board', 'skill2'), R('board', 'skill'), R('board', 'term_end'), R('board', 'member_id')), 8)],
    D.skills_matrix_d(), 40, [A('flag', '= ' + c1('One short'), 'warn'), A('flag', '= ' + c1('Short of two or more'), 'bad'), A('flag', '= ' + c1('No member'), 'bad')]))
# 8 meetings ------------------------------------------------------------------
tables.append(T('meetings', 'Meetings', 'Board and committee meetings with quorum and minutes',
    'One row per meeting, held or planned: date, time, kind, members expected and present, quorum and minutes; the attendance share, days to go and the sort keys fill in by themselves.', [
    C('meeting_id', 'Meeting ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('start_time', 'Time', 'time', 8), LST('kind', 'Kind', 'mkind', 12), LST('period', 'Year', 'yr', 14), C('expected', 'Expected', 'int', 8), C('present', 'Present', 'int', 8),
    C('quorum_met', 'Quorum met', 'bool', 8), C('minutes_ready', 'Minutes final', 'bool', 8), LST('status', 'Status', 'mstatus', 10),
    CA('share', 'Attendance share', 'pct', 'IF(AND({col:status}=%s,{col:expected}>0),{col:present}/{col:expected},"")' % HELD, 9), CA('held', 'Held', 'int', 'IF({col:status}=%s,1,0)' % HELD, 6),
    CA('year', 'Year number', 'int', 'YEAR({col:date})', 7), CA('days_to', 'Days to go', 'int', 'IF({col:status}=%s,{col:date}-{today},"")' % PLANNED, 7),
    CA('minutes_age', 'Days since, minutes not final', 'int', 'IF(AND({col:status}=%s,{col:minutes_ready}=%s),{today}-{col:date},"")' % (HELD, NO), 9),
    CA('next_key', 'Next meeting key', 'num', 'IF(AND({col:status}=%s,{col:date}>={today}),{col:date}+VALUE(RIGHT({col:meeting_id},3))/1000,"")' % PLANNED, 11),
    CA('next_board', 'Next board meeting date', 'date', 'IF(AND({col:status}=%s,{col:date}>={today},{col:kind}=%s),{col:date},"")' % (PLANNED, tok('mkind', 'Board')), 11),
    CA('held_board', 'Held board meeting date', 'date', 'IF(AND({col:status}=%s,{col:kind}=%s),{col:date},"")' % (HELD, tok('mkind', 'Board')), 11),
    CA('minutes_key', 'Minutes key', 'num', 'IF(AND({col:status}=%s,{col:minutes_ready}=%s),{col:date}+VALUE(RIGHT({col:meeting_id},3))/1000,"")' % (HELD, NO), 11),
    CA('notfinal_n', 'Meetings with minutes not final', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (R('meetings', 'status'), HELD, R('meetings', 'minutes_ready'), NO), 8),
    CA('quorum_number', 'Quorum number', 'int', '{set:quorum_number}', 8), CPH('chair_phone', 'Chair phone', D.CHAIR_PHONE), CPH('acc_phone', 'Accountant phone', D.ACC_PHONE), ORG()],
    D.meetings_d(), 120, [A('quorum_met', '= ' + NO, 'bad'), A('minutes_age', '> {set:minutes_days}', 'warn')]))
# 9 attendance ----------------------------------------------------------------
tables.append(T('attendance', 'Attendance', 'Who was present, sent apologies or was absent',
    'One row per member and meeting: type the meeting ID, date, kind, member and status; the present flag and the year fill in by themselves.', [
    C('att_id', 'Attendance ID', 'text', 10, required=True), C('meeting_id', 'Meeting ID', 'text', 10), C('date', 'Date', 'date', 11), LST('kind', 'Kind', 'mkind', 12), C('member_id', 'Member ID', 'text', 9), LST('member', 'Member', 'bmember', 24), LST('status', 'Status', 'attend', 11),
    CA('present', 'Present', 'int', 'IF({col:status}=%s,1,0)' % PRESENT, 7), CA('year', 'Year number', 'int', 'YEAR({col:date})', 7)], D.attendance_d(), 700, [A('status', '= ' + tok('attend', 'Absent'), 'bad'), A('status', '= ' + tok('attend', 'Apologies'), 'warn')]))
# 10 attendance by member -----------------------------------------------------
AMD = lambda extra='': 'COUNTIFS(%s,{col:member},%s,">="&DATE({col:year},1,1),%s,"<="&DATE({col:year},12,31)%s)' % (R('attendance', 'member'), R('attendance', 'date'), R('attendance', 'date'), extra)
tables.append(T('attendance_member', 'Attendance by Member', 'Attendance share of each member and year',
    'One row per member and year: meetings expected, meetings attended and the share against the share you expect; the flag and the rank of the lowest shares fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('member', 'Member', 'bmember', 24), LST('period', 'Year', 'yr3', 14),
    CA('member_id', 'Member ID', 'text', LKT('board.member_id', 'board.name', 'member'), 9), CA('year', 'Year number', 'int', YR3N('{col:period}'), 7),
    CA('meetings', 'Meetings', 'int', AMD(), 8), CA('present', 'Present', 'int', AMD(',%s,%s' % (R('attendance', 'status'), PRESENT)), 8), CA('share', 'Attendance share', 'pct', 'IF({col:meetings}>0,{col:present}/{col:meetings},"")', 9),
    CA('flag', 'Flag', 'text', 'IF({col:meetings}=0,%s,IF({col:share}<{set:attend_min},%s,%s))' % (c1('No meetings'), c1('Under the setting'), c1('On track')), 16),
    CA('shortfall', 'Shortfall', 'pct', 'IF(AND(ISNUMBER({col:share}),{col:share}<{set:attend_min}),{set:attend_min}-{col:share},0)', 9),
    CA('rank_score', 'Lowest share score', 'int', 'IF(AND({col:period}=%s,ISNUMBER({col:share})),ROUND((1-{col:share})*10000,0)*100+VALUE(RIGHT({col:row_id},2)),"")' % THIS3, 10),
    CA('phone', 'Phone', 'text', LKT('board.phone', 'board.name', 'member'), 18), CA('under_n', 'Members under the setting', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (R('attendance_member', 'period'), THIS3, R('attendance_member', 'flag'), c1('Under the setting')), 8),
    CA('attend_min', 'Attendance setting', 'pct', '{set:attend_min}', 9), CPH('chair_phone', 'Chair phone', D.CHAIR_PHONE), ORG()],
    D.attendance_member_d(), 60, [A('flag', '= ' + c1('Under the setting'), 'bad'), A('flag', '= ' + c1('On track'), 'good')]))
# 11 board giving -------------------------------------------------------------
tables.append(T('board_giving', 'Board Giving', 'Personal giving of each member by year',
    'One row per member and year: the gifts and the total from your gift log; the donor ID, whether the member gave and the share of the give or get target fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('member', 'Member', 'bmember', 24), LST('period', 'Year', 'yr3', 14), C('gifts', 'Gifts', 'int', 7), C('total', 'Total given', 'money', 12),
    CA('donor_id', 'Donor ID', 'text', LKT('board.donor_id', 'board.name', 'member'), 9), CA('year', 'Year number', 'int', YR3N('{col:period}'), 7), CA('gave', 'Gave', 'int', 'IF({col:total}>0,1,0)', 6),
    CA('share', 'Share of the target', 'pct', 'IF({set:give_or_get}>0,{col:total}/{set:give_or_get},0)', 9), CA('state', 'State', 'text', 'IF({col:total}>0,%s,%s)' % (c1('Gave'), c1('Not yet')), 9),
    CA('committee', 'Committee', 'text', LKT('board.committee', 'board.name', 'member'), 13), CA('phone', 'Phone', 'text', LKT('board.phone', 'board.name', 'member'), 18), ORG()],
    D.board_giving_d(), 60, [A('state', '= ' + c1('Not yet'), 'warn'), A('state', '= ' + c1('Gave'), 'good')]))
# 12 give or get --------------------------------------------------------------
tables.append(T('give_or_get', 'Give or Get Progress', 'Each member against the give or get target',
    'One row per member and year: type the money raised through the member\'s own asks; the target, the money given (from Board Giving), the remaining amount and the status fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('member', 'Member', 'bmember', 24), LST('period', 'Year', 'yr2', 12), C('raised', 'Raised from their asks', 'money', 12),
    CA('target', 'Target', 'money', '{set:give_or_get}', 10), CA('given', 'Given', 'money', 'SUMIFS(%s,%s,{col:member},%s,{col:period})' % (R('board_giving', 'total'), R('board_giving', 'member'), R('board_giving', 'period')), 11),
    CA('total', 'Given and raised', 'money', '{col:given}+{col:raised}', 11), CA('remaining', 'Remaining', 'money', 'MAX(0,{col:target}-{col:total})', 10),
    CA('elapsed', 'Share of the year passed', 'pct', 'IF({col:period}=%s,MIN(1,({today}-%s)/365),1)' % (THIS2, JAN1), 9),
    CA('status', 'Status', 'text', 'IF({col:total}>={col:target},%s,IF({col:total}>={col:target}*{col:elapsed},%s,%s))' % (c1('Met'), c1('On target'), c1('Behind')), 10),
    CA('met', 'Target met', 'int', 'IF({col:total}>={col:target},1,0)', 6), CA('behind_by', 'Behind the year by', 'money', 'MAX(0,{col:target}*{col:elapsed}-{col:total})', 10),
    CA('rank_score', 'Remaining score', 'int', 'IF({col:period}=%s,ROUND({col:remaining},0)*100+VALUE(RIGHT({col:row_id},2)),"")' % THIS2, 10),
    CA('phone', 'Phone', 'text', LKT('board.phone', 'board.name', 'member'), 18), ORG()],
    D.give_or_get_d(), 60, [A('status', '= ' + c1('Behind'), 'warn'), A('status', '= ' + c1('Met'), 'good')]))
# 13 board giving share -------------------------------------------------------
BGV = lambda extra='': 'COUNTIFS(%s,{col:period},%s,1%s)' % (R('board_giving', 'period'), R('board_giving', 'gave'), extra)
tables.append(T('board_share', 'Board Giving Share', 'Share of members who gave, by year and group',
    'One row per year and group (the whole board or one committee): the members who gave, from Board Giving, against the members now; the share fills in by itself.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('period', 'Year', 'yr3', 14), LST('group', 'Group', 'bgroup', 13),
    CA('members', 'Members', 'int', 'IF({col:group}=%s,SUM(%s),COUNTIFS(%s,{col:group},%s,1))' % (tok('bgroup', 'Whole board'), R('board', 'serving'), R('board', 'committee'), R('board', 'serving')), 8),
    CA('gave', 'Members who gave', 'int', 'IF({col:group}=%s,%s,%s)' % (tok('bgroup', 'Whole board'), BGV(), BGV(',%s,{col:group}' % R('board_giving', 'committee'))), 9),
    CA('share', 'Share who gave', 'pct', 'IF({col:members}>0,{col:gave}/{col:members},0)', 9), CA('year', 'Year number', 'int', YR3N('{col:period}'), 7),
    CPH('fund_chair_phone', 'Fundraising chair phone', D.VICE_PHONE), ORG()], D.board_share_d(), 30))
# 14 declarations -------------------------------------------------------------
tables.append(T('declarations', 'Declarations', 'Yearly declarations of interest',
    'One row per member and year: the due date, the date filed and the items declared (a count, no detail here); the days late and the open flag fill in by themselves.', [
    C('decl_id', 'Declaration ID', 'text', 10, required=True), C('member_id', 'Member ID', 'text', 9), LST('member', 'Member', 'bmember', 24), LST('year', 'Year', 'yr3', 14), C('due_date', 'Due date', 'date', 11), C('filed_on', 'Filed on', 'date', 11),
    C('items_declared', 'Items declared', 'int', 8), LST('status', 'Status', 'dclstatus', 10),
    CA('days_late', 'Days late', 'int', 'IF({col:filed_on}>0,MAX(0,{col:filed_on}-{col:due_date}),MAX(0,{today}-{col:due_date}))', 8), CA('open_n', 'Open', 'int', 'IF({col:status}=%s,0,1)' % FILED, 6),
    CA('filed_n', 'Filed this year', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (R('declarations', 'year'), THIS3, R('declarations', 'status'), FILED), 8), CA('total_n', 'Declarations this year', 'int', 'COUNTIFS(%s,%s)' % (R('declarations', 'year'), THIS3), 8),
    CA('phone', 'Phone', 'text', LKT('board.phone', 'board.name', 'member'), 18), CPH('gov_phone', 'Governance chair phone', D.GOV_CHAIR_PHONE), ORG()],
    D.declarations_d(), 60, [A('status', '= ' + tok('dclstatus', 'Overdue'), 'bad'), A('status', '= ' + tok('dclstatus', 'Due'), 'warn'), A('status', '= ' + FILED, 'good')]))
# 15 declaration status -------------------------------------------------------
DSX = lambda col: 'SUMIFS(%s,%s,{col:member},%s,{col:year})' % (R('declarations', col), R('declarations', 'member'), R('declarations', 'year'))
tables.append(T('decl_status', 'Declaration Status', 'Who has filed, by member and year',
    'One row per member and year: the due date, the date filed, the items declared and the days late come from Declarations; a flag shows who to chase.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('member', 'Member', 'bmember', 24), LST('year', 'Year', 'yr3', 14),
    CA('due', 'Due date', 'date', 'IF(%s=0,"",%s)' % (DSX('due_date'), DSX('due_date')), 11), CA('filed', 'Filed on', 'date', 'IF(%s=0,"",%s)' % (DSX('filed_on'), DSX('filed_on')), 11),
    CA('items', 'Items declared', 'int', DSX('items_declared'), 8),
    CA('days_late', 'Days late', 'int', 'IF({col:due}="","",IF(ISNUMBER({col:filed}),MAX(0,{col:filed}-{col:due}),MAX(0,{today}-{col:due})))', 8),
    CA('flag', 'Flag', 'text', 'IF({col:due}="",%s,IF(ISNUMBER({col:filed}),IF({col:filed}<={col:due},%s,%s),IF({col:due}<{today},%s,%s)))' % (c1('Not recorded'), c1('Filed on time'), c1('Filed late'), c1('Overdue'), c1('Due soon')), 14),
    CA('rank_score', 'Overdue score', 'int', 'IF(AND({col:year}=%s,{col:flag}=%s),{col:days_late}*100+VALUE(RIGHT({col:row_id},2)),"")' % (THIS3, c1('Overdue')), 10),
    CA('phone', 'Phone', 'text', LKT('board.phone', 'board.name', 'member'), 18), ORG()], D.decl_status_d(), 60, [A('flag', '= ' + c1('Overdue'), 'bad'), A('flag', '= ' + c1('Due soon'), 'warn'), A('flag', '= ' + c1('Filed late'), 'warn')]))
# 16 obligations --------------------------------------------------------------
tables.append(T('obligations', 'Obligations', 'Policy reviews, renewals, returns and reports with due dates',
    'One row per obligation: item, kind, due date, owner (a committee), the date done and the status; the days away, the on-time flag and the late flag fill in by themselves.', [
    C('ob_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 36), LST('kind', 'Kind', 'obkind', 17), C('due_date', 'Due date', 'date', 11), LST('owner', 'Owner', 'committee', 13), C('done_on', 'Done on', 'date', 11), LST('status', 'Status', 'obstatus', 11),
    CA('days_away', 'Days away', 'int', 'IF({col:done_on}>0,"",{col:due_date}-{today})', 8), CA('on_time', 'Done on time', 'int', 'IF(AND({col:done_on}>0,{col:done_on}<={col:due_date}),1,0)', 7),
    CA('done_n', 'Done', 'int', 'IF({col:done_on}>0,1,0)', 6), CA('one', 'Count', 'int', '1', 6), CA('open_late', 'Open and late', 'int', 'IF(AND(NOT({col:done_on}>0),{col:due_date}<{today}),1,0)', 7),
    CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('broker_phone', 'Insurance broker phone', D.BROKER_PHONE), CPH('acc_phone', 'Accountant phone', D.ACC_PHONE), ORG()],
    D.obligations_d(), 80, [A('status', '= ' + tok('obstatus', 'Overdue'), 'bad'), A('days_away', '<= {set:ob_warn_days}', 'warn'), A('status', '= ' + OBDONE, 'good')]))
# 17 obligation calendar ------------------------------------------------------
OBL_ = lambda col: 'IFERROR(INDEX({range:obligations.%s},MATCH({col:ob_id},{range:obligations.ob_id},0)),"")' % col
tables.append(T('ob_calendar', 'Obligation Calendar', 'Obligations in date order with the late flag',
    'One row per obligation, from the last 200 days to the end of the year ahead: type the item ID; the date, owner, days away, flag and the order of the open items fill in by themselves.', [
    REF('ob_id', 'Item ID', 'obligations.ob_id', 10, required=True), CA('item', 'Item', 'text', OBL_('item') + '&""', 36), CA('kind', 'Kind', 'text', OBL_('kind') + '&""', 17), CA('owner', 'Owner', 'text', OBL_('owner') + '&""', 13),
    CA('due_date', 'Due date', 'date', LKD('obligations.due_date', 'obligations.ob_id', 'ob_id'), 11), CA('done_on', 'Done on', 'date', LKD('obligations.done_on', 'obligations.ob_id', 'ob_id'), 11),
    CA('days_away', 'Days away', 'int', 'IF(ISNUMBER({col:done_on}),"",{col:due_date}-{today})', 8),
    CA('flag', 'Flag', 'text', 'IF(ISNUMBER({col:done_on}),%s,IF({col:due_date}<{today},%s,IF({col:due_date}<={today}+7,%s,IF({col:due_date}<=EOMONTH({today},0),%s,%s))))' % (c1('Done'), c1('Overdue'), c1('Due this week'), c1('Due this month'), c1('Coming up')), 15),
    CA('sort_key', 'Sort key', 'num', 'IF(ISNUMBER({col:done_on}),"",{col:due_date}+VALUE(RIGHT({col:ob_id},3))/1000)', 11),
    CA('rank', 'Rank', 'int', 'IF(ISNUMBER({col:sort_key}),COUNTIF(%s,"<"&{col:sort_key})+1,"")' % R('ob_calendar', 'sort_key'), 6),
    CA('over_n', 'Obligations overdue', 'int', 'COUNTIFS(%s,%s)' % (R('ob_calendar', 'flag'), c1('Overdue')), 8),
    CA('month_n', 'Due this month', 'int', 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (R('ob_calendar', 'flag'), c1('Due this month'), R('ob_calendar', 'flag'), c1('Due this week')), 8),
    CA('due30_n', 'Due in the next 30 days', 'int', 'COUNTIFS(%s,">=0",%s,"<=30")' % (R('ob_calendar', 'days_away'), R('ob_calendar', 'days_away')), 8),
    CA('oldest_item', 'Oldest overdue item', 'text', 'IF(COUNTIFS(%s,%s)=0,"",INDEX(%s,MATCH(SMALL(%s,1),%s,0)))' % (R('ob_calendar', 'flag'), c1('Overdue'), R('ob_calendar', 'item'), R('ob_calendar', 'sort_key'), R('ob_calendar', 'sort_key')), 30),
    CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('chair_phone', 'Chair phone', D.CHAIR_PHONE), ORG()],
    D.ob_calendar_d(), 60, [A('flag', '= ' + c1('Overdue'), 'bad'), A('flag', '= ' + c1('Due this week'), 'warn'), A('flag', '= ' + c1('Done'), 'good')]))
# 18 obligation kinds ---------------------------------------------------------
tables.append(T('ob_kinds', 'Obligation Kinds', 'How often each kind of obligation comes round',
    'One row per kind: the months between two due dates and the committee that owns it; check your local rules for what each one needs.', [
    LST('kind', 'Kind', 'obkind', 18, required=True), C('repeats_months', 'Repeats every (months)', 'int', 10), LST('owner', 'Owner', 'committee', 13)], D.ob_kinds_d(), 20))
# 19 meeting plan -------------------------------------------------------------
MP = lambda col: 'IFERROR(INDEX({range:meetings.%s},MATCH({col:meeting_id},{range:meetings.meeting_id},0)),"")' % col
tables.append(T('meeting_plan', 'Meeting Plan', 'Board meetings: agenda, papers and quorum',
    'One row per board meeting: type the agenda items, whether the papers are ready and how many members confirmed; the date, time, papers due date and the quorum flag fill in by themselves.', [
    REF('meeting_id', 'Meeting ID', 'meetings.meeting_id', 10, required=True), C('agenda_items', 'Agenda items', 'int', 8), C('papers_ready', 'Papers ready', 'bool', 8), C('confirmed', 'Confirmed', 'int', 8),
    CA('date', 'Date', 'date', LKD('meetings.date', 'meetings.meeting_id', 'meeting_id'), 11), CA('time', 'Time', 'time', 'IFERROR(IF(INDEX(%s,MATCH({col:meeting_id},%s,0))=0,"",INDEX(%s,MATCH({col:meeting_id},%s,0))),"")' % (R('meetings', 'start_time'), R('meetings', 'meeting_id'), R('meetings', 'start_time'), R('meetings', 'meeting_id')), 8),
    CA('status', 'Status', 'text', MP('status') + '&""', 9), CA('expected', 'Expected', 'int', 'IFERROR(INDEX(%s,MATCH({col:meeting_id},%s,0)),0)' % (R('meetings', 'expected'), R('meetings', 'meeting_id')), 8),
    CA('days_to', 'Days to go', 'int', 'IF({col:date}>={today},{col:date}-{today},"")', 7),
    CA('papers_due', 'Papers due', 'date', '{col:date}-{set:papers_days}', 11),
    CA('papers', 'Papers', 'text', 'IF({col:papers_ready}=%s,%s,IF(AND(ISNUMBER({col:days_to}),{col:days_to}<={set:papers_days}),%s,%s))' % (YES, c2('Ready'), c2('Late'), c2('Not due yet')), 12),
    CA('quorum_flag', 'Quorum', 'text', 'IF(NOT(ISNUMBER({col:days_to})),%s,IF({col:confirmed}>={set:quorum_number},%s,IF({col:days_to}>21,%s,%s)))' % (c2('Held'), c2('Quorum expected'), c2('Not asked yet'), c2('Quorum at risk')), 16),
    CA('quorum_short', 'Confirmations short', 'int', 'IF(ISNUMBER({col:days_to}),MAX(0,{set:quorum_number}-{col:confirmed}),"")', 8),
    CA('next_key', 'Next key', 'num', 'IF(ISNUMBER({col:days_to}),{col:date},"")', 11), CA('quorum_number', 'Quorum number', 'int', '{set:quorum_number}', 8),
    CPH('treas_phone', 'Treasurer phone', D.TREAS_PHONE), CPH('secretary_phone', 'Secretary phone', D.SECR_PHONE), CPH('vol_phone', 'Volunteer phone', D.VOL_PHONE), ORG()],
    D.meeting_plan_d(), 30, [A('quorum_flag', '= ' + c2('Quorum at risk'), 'bad'), A('papers', '= ' + c2('Late'), 'warn')]))
# 20 board pack ---------------------------------------------------------------
def EX(i): return {
    5: 'SUM(%s)' % R('board', 'serving'), 6: 'MAX(0,{set:board_seats}-SUM(%s))' % R('board', 'serving'), 7: 'SUM(%s)' % R('board', 'ends_soon'),
    8: 'ROUND(100*IFERROR(SUMIFS(%s,%s,%s)/COUNTIFS(%s,%s),0),0)' % (R('attendance', 'present'), R('attendance', 'year'), YN, R('attendance', 'year'), YN),
    9: 'COUNTIFS(%s,%s,%s,%s)' % (R('attendance_member', 'period'), THIS3, R('attendance_member', 'flag'), c1('Under the setting')),
    10: 'COUNTIFS(%s,%s,%s,%s)' % (R('declarations', 'year'), THIS3, R('declarations', 'status'), FILED), 11: 'SUM(%s)' % R('obligations', 'open_late'),
    12: 'COUNTIFS(%s,">=0",%s,"<=30")' % (R('obligations', 'days_away'), R('obligations', 'days_away')),
    13: 'COUNTIFS(%s,%s,%s,%s)' % (R('meetings', 'status'), HELD, R('meetings', 'minutes_ready'), NO),
    14: 'COUNTIFS(%s,%s,%s,%s,%s,%s)' % (R('meetings', 'status'), HELD, R('meetings', 'quorum_met'), NO, R('meetings', 'year'), YN)}[i]
NUM = 'IF({col:no}<=4,IF({col:typed}="","",{col:typed}),CHOOSE({col:no}-4,%s))' % ','.join(EX(i) for i in range(5, 15))
OK_, WA_, AC_ = c2('OK'), c2('Watch'), c2('Act')
def GT0(w): return 'IF({col:number}>0,%s,%s)' % (w, OK_)
_FL = [OK_, 'IF({col:number}<{set:reserve_months},%s,%s)' % (AC_, OK_), OK_, GT0(AC_), OK_, GT0(WA_), GT0(WA_), 'IF({col:number}<100*{set:attend_min},%s,%s)' % (WA_, OK_), GT0(WA_),
       'IF({col:number}<SUM(%s),%s,%s)' % (R('board', 'serving'), WA_, OK_), GT0(AC_), GT0(WA_), GT0(WA_), GT0(WA_)]
FLAGF = 'IF({col:number}="",%s,CHOOSE({col:no},%s))' % (c2('Missing'), ','.join(_FL))
tables.append(T('board_pack', 'Board Pack', 'The numbers for the board pack on one page',
    'One row per pack item: type cash, months of reserve, grant pipeline and funds below zero, and last month\'s figure; the other items fill in with a trend and a flag.', [
    C('item', 'Item', 'text', 34, required=True), C('no', 'No', 'int', 5), C('unit', 'Unit', 'text', 8), C('typed', 'Typed number', 'num', 12), C('last', 'Last month', 'num', 12),
    CA('number', 'Number', 'num', NUM, 12), CA('trend', 'Trend', 'text', 'IF(OR({col:last}="",{col:number}=""),"",IF({col:number}>{col:last},%s,IF({col:number}<{col:last},%s,%s)))' % (c2('Up'), c2('Down'), c2('Same')), 8),
    CA('flag', 'Flag', 'text', FLAGF, 9), CA('missing_n', 'Items missing', 'int', 'COUNTIFS(%s,%s)' % (R('board_pack', 'flag'), c2('Missing')), 8),
    CA('first_missing', 'First missing item', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (R('board_pack', 'item'), c2('Missing'), R('board_pack', 'flag')), 30),
    CA('pack_date', 'Pack for the meeting on', 'date', 'IFERROR(SMALL(%s,1),"")' % R('meetings', 'next_board'), 11), CPH('chair_phone', 'Chair phone', D.CHAIR_PHONE), ORG()],
    D.board_pack_d(), 30, [A('flag', '= ' + c2('Missing'), 'bad'), A('flag', '= ' + c2('Act'), 'bad'), A('flag', '= ' + c2('Watch'), 'warn'), A('flag', '= ' + c2('OK'), 'good')]))
assert len(tables) == 20, len(tables)
