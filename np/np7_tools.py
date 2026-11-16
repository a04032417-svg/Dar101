"""Nonprofit suite part 7: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np7_lists import *
import np7_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
YN = 'YEAR({today})'
THIS3 = tok('yr3', 'This year'); LAST3 = tok('yr3', 'Last year'); TWO3 = tok('yr3', 'Two years ago'); THIS2 = tok('yr2', 'This year')
HELD = tok('mstatus', 'Held'); FILED = tok('dclstatus', 'Filed'); OBDONE = tok('obstatus', 'Done')
NO = '{list:yesno.no}'; YES = '{list:yesno.yes}'
SERV = 'SUM(%s)' % R('board', 'serving')
ROLEN = lambda r: 'COUNTIFS(%s,%s,%s,1)' % (R('board', 'role'), tok('brole', r), R('board', 'serving'))
COMN = lambda c: 'COUNTIFS(%s,%s,%s,1)' % (R('board', 'committee'), tok('committee', c), R('board', 'serving'))
def SKN(s, date='{today}'):
    return '(COUNTIFS(%s,%s,%s,">="&%s)+COUNTIFS(%s,%s,%s,"<>"&%s,%s,">="&%s,%s,"<>"))' % (R('board', 'skill'), s, R('board', 'term_end'), date, R('board', 'skill2'), s, R('board', 'skill'), s, R('board', 'term_end'), date, R('board', 'member_id'))
def SK(table, col, key_, k, blank='"-"'): return 'IFERROR(INDEX(%s,MATCH(SMALL(%s,%d),%s,0)),%s)' % (R(table, col), R(table, key_), k, R(table, key_), blank)
def LG(table, col, key_, k): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"-")' % (R(table, col), R(table, key_), k, R(table, key_))
def MIND(kind_expr):  # next open due date of an obligation kind (input columns only)
    return 'IFERROR(1/SUMPRODUCT(MAX((%s=%s)*(%s<>%s)*(%s>0)/(%s+(%s=0)))),"")' % (R('obligations', 'kind'), kind_expr, R('obligations', 'status'), OBDONE, R('obligations', 'due_date'), R('obligations', 'due_date'), R('obligations', 'due_date'))
tools = []

# 1 ------------------------------------------------------------ board roster view
TE1 = lambda k, col: SK('terms_ending', col, 'sort_key', k)
OPEN1 = 'MAX(0,{in:seats}-%s)' % SERV
tools.append(TOOL('roster_view', 'Board Roster View', 'Is the roster complete, and who is on it',
    'Type the seats set by your own rules; members are counted by role and committee, the open seats are shown and the member whose term ends first is named.', [
    I('seats', 'Seats set by your own rules', BOARD_SEATS, 'int')], [
    O('Members serving now', 'int', SERV)] + [O('%s seats filled' % r, 'int', ROLEN(r)) for r in BOARD_ROLES] + [O('Members on the %s committee' % c, 'int', COMN(c)) for c in COMMITTEES] + [
    O('Seats set', 'int', '{in:seats}'), O('Seats open', 'int', OPEN1), O('Share of seats filled', 'pct', 'IFERROR(%s/{in:seats},0)' % SERV),
    O('Next term to end, member', 'text', TE1(1, 'member')), O('Next term to end, date', 'date', 'IFERROR(INT(SMALL(%s,1)),"-")' % R('terms_ending', 'sort_key')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (OPEN1, c3('Roster complete'), c3('Seats open'), OPEN1))],
    GR('What if', ('Ten seats', {'seats': 10}), ('Eleven seats', {'seats': 11}), ('Thirteen seats', {'seats': 13}), ('Fifteen seats', {'seats': 15}))))

# 2 ------------------------------------------------------------ terms ending ranker
def SKY(k): return 'IFERROR(SMALL(%s,%d),"")' % (R('terms_ending', 'sort_key'), k)
def INW(k): return 'IFERROR(INT(SMALL(%s,%d))<=EDATE({today},{in:months}),FALSE)' % (R('terms_ending', 'sort_key'), k)
def TW(k, col): return 'IF(%s,%s,"-")' % (INW(k), TE1(k, col))
VERD2 = 'IF(NOT(%s),%s,IF(%s<{in:limit},%s&" "&%s,%s&" "&%s))' % (INW(1), c3('Fine'), TE1(1, 'terms_served'), c3('Renew'), TE1(1, 'member'), c3('Recruit for'), TE1(1, 'skill'))
tools.append(TOOL('terms_ranker', 'Terms Ending Ranker', 'Whose term ends next, and do we renew or recruit',
    'Type the months ahead to look and the most terms you allow a member; the terms ending are ranked by date with terms served, and the first one gets a verdict to renew or recruit.', [
    I('months', 'Months ahead to look', 6, 'int'), I('limit', 'Most terms you allow a member', 2, 'int')], [
    O('Terms ending in the months ahead', 'int', 'COUNTIFS(%s,1,%s,"<="&EDATE({today},{in:months}))' % (R('board', 'serving'), R('board', 'term_end'))),
    O('Of those, members who may renew', 'int', 'COUNTIFS(%s,1,%s,"<="&EDATE({today},{in:months}),%s,"<"&{in:limit})' % (R('board', 'serving'), R('board', 'term_end'), R('board', 'terms_served'))),
    O('First term, member', 'text', TW(1, 'member')), O('First term, date', 'date', 'IF(%s,INT(%s),"-")' % (INW(1), SKY(1))), O('First term, months left', 'num', TW(1, 'months_left')), O('First term, terms served', 'int', TW(1, 'terms_served')), O('First term, skill', 'text', TW(1, 'skill')),
    O('Second term, member', 'text', TW(2, 'member')), O('Second term, date', 'date', 'IF(%s,INT(%s),"-")' % (INW(2), SKY(2))), O('Second term, months left', 'num', TW(2, 'months_left')), O('Second term, terms served', 'int', TW(2, 'terms_served')),
    O('Third term, member', 'text', TW(3, 'member')), O('Third term, date', 'date', 'IF(%s,INT(%s),"-")' % (INW(3), SKY(3))), O('Third term, months left', 'num', TW(3, 'months_left')),
    O('Verdict', 'text', VERD2)],
    GR('What if', ('Look 3 months ahead', {'months': 3}), ('Look 12 months ahead', {'months': 12}), ('Allow one term only', {'limit': 1}), ('Allow three terms', {'limit': 3}), ('24 months and three terms', {'months': 24, 'limit': 3}))))

# 3 ------------------------------------------------------------ vacancy check
END3 = 'COUNTIFS(%s,1,%s,"<="&EDATE({today},{in:months}))' % (R('board', 'serving'), R('board', 'term_end'))
tools.append(TOOL('vacancy_check', 'Vacancy Check', 'Are all seats filled, and how many will open',
    'Type the seats you set, the months to look ahead and the share of ending terms you expect to renew (your estimate); open seats now and the seats that may open are counted.', [
    I('seats', 'Seats set by your own rules', BOARD_SEATS, 'int'), I('months', 'Months ahead to look', 6, 'int'), I('renew', 'Share of ending terms that renew, your estimate', 0.5, 'pct')], [
    O('Seats set', 'int', '{in:seats}'), O('Seats filled', 'int', SERV), O('Seats open now', 'int', 'MAX(0,{in:seats}-%s)' % SERV), O('Seats open on the Seats sheet', 'int', 'SUM(%s)' % R('seats', 'vacant')),
    O('Terms ending in the months ahead', 'int', END3), O('Seats that may open, your estimate', 'int', 'ROUND(%s*(1-{in:renew}),0)' % END3), O('Seats open after those terms', 'int', 'MAX(0,{in:seats}-%s)+ROUND(%s*(1-{in:renew}),0)' % (SERV, END3)),
    O('Share of seats filled now', 'pct', 'IFERROR(%s/{in:seats},0)' % SERV), O('Members to recruit now', 'int', 'MAX(0,{in:seats}-%s)' % SERV), O('Members to recruit by then, your estimate', 'int', 'MAX(0,{in:seats}-%s)+ROUND(%s*(1-{in:renew}),0)' % (SERV, END3)),
    O('Verdict', 'text', 'IF({in:seats}-%s<=0,%s,%s&" "&({in:seats}-%s))' % (SERV, c3('Full'), c3('Recruit'), SERV))],
    GR('What if', ('Everyone renews', {'renew': 1.0}), ('One in four renews', {'renew': 0.25}), ('Eleven seats', {'seats': 11}), ('Look 12 months ahead', {'months': 12}), ('Fifteen seats', {'seats': 15}))))

# 4 ------------------------------------------------------------ skills gap finder
SEL = '{in:skill}'
NOW4 = SKN(SEL); LATER4 = SKN(SEL, 'EDATE({today},{in:months})')
NEED4 = 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('skills', 'needed'), SEL, R('skills', 'skill'))
LEAVE_DATE = 'IFERROR(1/SUMPRODUCT(MAX((((%s=%s)+(%s=%s))>0)*(%s>={today})*(%s<=EDATE({today},{in:months}))/(%s+(%s=0)))),"")' % (R('board', 'skill'), SEL, R('board', 'skill2'), SEL, R('board', 'term_end'), R('board', 'term_end'), R('board', 'term_end'), R('board', 'term_end'))
tools.append(TOOL('skills_gap', 'Skills Gap Finder', 'Which skill will the board lose, and who do we recruit for',
    'Pick a skill and the months to look ahead; members who hold it now and later are counted against the number you need, the first member to leave is named and the biggest gap in 6 months is shown.', [
    IL('skill', 'Skill', 'skill', 'Law and policy'), I('months', 'Months ahead to look', 6, 'int')], [
    O('Members needed', 'int', NEED4), O('Members with the skill now', 'int', NOW4), O('Members with the skill after the months', 'int', LATER4), O('Members leaving with the skill', 'int', '%s-%s' % (NOW4, LATER4)),
    O('Gap now', 'int', 'MAX(0,%s-%s)' % (NEED4, NOW4)), O('Gap after the months', 'int', 'MAX(0,%s-%s)' % (NEED4, LATER4)), O('First member leaving, term end', 'date', 'IF(%s="","-",%s)' % (LEAVE_DATE, LEAVE_DATE)),
    O('First member leaving, name', 'text', 'IF(%s="","-",IFERROR(INDEX(%s,MATCH(%s,%s,0)),"-"))' % (LEAVE_DATE, R('board', 'name'), LEAVE_DATE, R('board', 'term_end'))),
    O('Skills with no member now', 'int', 'COUNTIFS(%s,%s,%s,0)' % (R('skills_matrix', 'when'), tok('when', 'Now'), R('skills_matrix', 'members'))),
    O('Skills with a gap in 6 months', 'int', 'COUNTIFS(%s,%s,%s,">0")' % (R('skills_matrix', 'when'), tok('when', 'In 6 months'), R('skills_matrix', 'gap'))),
    O('Biggest gap in 6 months, skill', 'text', LG('skills_matrix', 'skill', 'gap_score', 1)),
    O('Verdict', 'text', 'IF(MAX(0,%s-%s)>0,%s&" "&%s,%s)' % (NEED4, LATER4, c3('Recruit for'), SEL, c3('Fine')))],
    GR('What if', ('Finance', {'skill': '=' + tok('skill', 'Finance')}), ('Fundraising', {'skill': '=' + tok('skill', 'Fundraising')}), ('Technology', {'skill': '=' + tok('skill', 'Technology')}),
       ('Education, 12 months', {'skill': '=' + tok('skill', 'Education'), 'months': 12}), ('Law and policy, 12 months', {'months': 12}))))

# 5 ------------------------------------------------------------ succession planner
def ENDY(k): return 'COUNTIFS(%s,1,%s,">="&DATE(YEAR({today})+%d,1,1),%s,"<="&DATE(YEAR({today})+%d,12,31))' % (R('board', 'serving'), R('board', 'term_end'), k, R('board', 'term_end'), k)
PEAK = 'MAX(%s)' % ','.join(ENDY(k) for k in range(4))
tools.append(TOOL('succession', 'Succession Planner', 'Do too many terms end in the same year',
    'Type the share of ending terms that renew (your estimate) and the most of the board you want to end in one year; terms ending each year are counted with the seats and skills at risk.', [
    I('renew', 'Share of ending terms that renew, your estimate', 0.5, 'pct'), I('peak', 'Most of the board that should end in one year', 0.4, 'pct')], [
    O('Members serving now', 'int', SERV), O('Terms ending this year', 'int', ENDY(0)), O('Terms ending next year', 'int', ENDY(1)), O('Terms ending in two years', 'int', ENDY(2)), O('Terms ending in three years', 'int', ENDY(3)),
    O('Seats that may open next year, your estimate', 'int', 'ROUND(%s*(1-{in:renew}),0)' % ENDY(1)), O('Seats that may open in two years, your estimate', 'int', 'ROUND(%s*(1-{in:renew}),0)' % ENDY(2)),
    O('Seats that may open in three years, your estimate', 'int', 'ROUND(%s*(1-{in:renew}),0)' % ENDY(3)), O('Largest number ending in one year', 'int', PEAK), O('Largest share of the board ending in one year', 'pct', 'IFERROR(%s/%s,0)' % (PEAK, SERV)),
    O('Skills short in 12 months', 'int', 'COUNTIFS(%s,%s,%s,">0")' % (R('skills_matrix', 'when'), tok('when', 'In 12 months'), R('skills_matrix', 'gap'))),
    O('Skills with no member in 12 months', 'int', 'COUNTIFS(%s,%s,%s,0)' % (R('skills_matrix', 'when'), tok('when', 'In 12 months'), R('skills_matrix', 'members'))),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>{in:peak},%s,%s)' % (PEAK, SERV, c3('Stagger terms'), c3('Fine')))],
    GR('What if', ('Everyone renews', {'renew': 1.0}), ('One in four renews', {'renew': 0.25}), ('Allow half the board in a year', {'peak': 0.5}), ('Allow a quarter in a year', {'peak': 0.25}))))

# 6 ------------------------------------------------------------ committee balance
CF, CR_, CG = COMN('Finance'), COMN('Fundraising'), COMN('Governance')
MN = 'MIN(%s,%s,%s)' % (CF, CR_, CG)
SMALLN = 'IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (CF, MN, tok('committee', 'Finance'), CR_, MN, tok('committee', 'Fundraising'), tok('committee', 'Governance'))
SELC = 'COUNTIFS(%s,{in:committee},%s,1)' % (R('board', 'committee'), R('board', 'serving'))
tools.append(TOOL('committee_balance', 'Committee Balance', 'Which committee has too few members',
    'Pick a committee and type the fewest members you want on each; the three committees are counted, the smallest is named and the verdict says how many to add.', [
    IL('committee', 'Committee', 'committee', 'Governance'), I('min', 'Fewest members on a committee', 4, 'int')], [
    O('Members on Finance', 'int', CF), O('Members on Fundraising', 'int', CR_), O('Members on Governance', 'int', CG), O('Members on the chosen committee', 'int', SELC),
    O('Short of the minimum, chosen committee', 'int', 'MAX(0,{in:min}-%s)' % SELC), O('Smallest committee', 'text', SMALLN), O('Members on the smallest committee', 'int', MN),
    O('Members on the largest committee', 'int', 'MAX(%s,%s,%s)' % (CF, CR_, CG)), O('Members you would need to add in all', 'int', 'MAX(0,{in:min}-%s)+MAX(0,{in:min}-%s)+MAX(0,{in:min}-%s)' % (CF, CR_, CG)),
    O('Chair of the chosen committee', 'text', 'IFERROR(INDEX(%s,MATCH({in:committee},%s,0))&"","")' % (R('committees', 'chair'), R('committees', 'committee'))),
    O('Verdict', 'text', 'IF(%s<{in:min},%s&" "&({in:min}-%s)&" "&%s&" "&%s,%s)' % (MN, c3('Add'), MN, c3('to'), SMALLN, c3('Fine')))],
    GR('What if', ('Minimum of 3', {'min': 3}), ('Minimum of 5', {'min': 5}), ('Finance', {'committee': '=' + tok('committee', 'Finance')}), ('Fundraising, minimum 5', {'committee': '=' + tok('committee', 'Fundraising'), 'min': 5}))))

# 7 ------------------------------------------------------------ meeting calendar
NB = 'IFERROR(SMALL(%s,1),"")' % R('meetings', 'next_board')
def MPN(col): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('meeting_plan', col), NB, R('meeting_plan', 'date'))
def NM(k, col): return 'IFERROR(INDEX(%s,MATCH(SMALL(%s,%d),%s,0)),"-")' % (R('meetings', col), R('meetings', 'next_key'), k, R('meetings', 'next_key'))
tools.append(TOOL('meeting_calendar', 'Meeting Calendar', 'Is the next board meeting ready',
    'Type how many days ahead you want to look; the next meetings are listed with date, time and kind, and the next board meeting is checked for papers and confirmations against the quorum.', [
    I('days', 'Days ahead to look', 60, 'int')], [
    O('Meetings in the days ahead', 'int', 'COUNTIFS(%s,">0",%s,"<"&({today}+{in:days}+1))' % (R('meetings', 'next_key'), R('meetings', 'next_key'))),
    O('Next meeting, date', 'date', 'IFERROR(INT(SMALL(%s,1)),"-")' % R('meetings', 'next_key')), O('Next meeting, kind', 'text', NM(1, 'kind')), O('Next meeting, time', 'time', NM(1, 'start_time')),
    O('Second meeting, date', 'date', 'IFERROR(INT(SMALL(%s,2)),"-")' % R('meetings', 'next_key')), O('Second meeting, kind', 'text', NM(2, 'kind')), O('Third meeting, date', 'date', 'IFERROR(INT(SMALL(%s,3)),"-")' % R('meetings', 'next_key')), O('Third meeting, kind', 'text', NM(3, 'kind')),
    O('Next board meeting, date', 'date', NB), O('Days to the next board meeting', 'int', 'IFERROR(%s-{today},"")' % NB), O('Papers due on', 'date', 'IFERROR(%s-{set:papers_days},"")' % NB), O('Agenda items so far', 'int', MPN('agenda_items')),
    O('Papers', 'text', MPN('papers')), O('Members confirmed', 'int', MPN('confirmed')), O('Quorum number', 'int', '{set:quorum_number}'), O('Confirmations still needed', 'int', 'IFERROR(MAX(0,{set:quorum_number}-%s),"")' % MPN('confirmed')),
    O('Verdict', 'text', 'IF(%s=%s,%s,%s)' % (MPN('quorum_flag'), c2('Quorum at risk'), c2('Quorum at risk'), c2('Ready')))],
    GR('What if', ('Two weeks ahead', {'days': 14}), ('30 days ahead', {'days': 30}), ('90 days ahead', {'days': 90}), ('Look one day ahead', {'days': 1}))))

# 8 ------------------------------------------------------------ quorum checker
UNAN = 'MAX(0,{in:expected}-{in:confirmed}-{in:declined})'
tools.append(TOOL('quorum_checker', 'Quorum Checker', 'Will we have a quorum for the meeting',
    'Type members expected, confirmed and unable to come, and the quorum your rules need; confirmations still needed and the best case are shown.', [
    I('expected', 'Members expected', 11, 'int'), I('confirmed', 'Members who confirmed', 5, 'int'), I('declined', 'Members who cannot come', 1, 'int'), I('quorum', 'Members needed for a quorum', 6, 'int'), I('reply', 'Share of those who have not replied that come, your estimate', 0.5, 'pct')], [
    O('Members needed for a quorum', 'int', '{in:quorum}'), O('Confirmed so far', 'int', '{in:confirmed}'), O('Confirmations still needed', 'int', 'MAX(0,{in:quorum}-{in:confirmed})'), O('Members who have not replied', 'int', UNAN),
    O('Best case, everyone who has not replied comes', 'int', '{in:expected}-{in:declined}'), O('Expected present, your estimate', 'int', '{in:confirmed}+ROUND(%s*{in:reply},0)' % UNAN),
    O('Spare members above the quorum, best case', 'int', '{in:expected}-{in:declined}-{in:quorum}'), O('Share of the board confirmed', 'pct', 'IFERROR({in:confirmed}/{in:expected},0)'),
    O('Members to call first', 'int', 'MIN(%s,MAX(0,{in:quorum}-{in:confirmed}))' % UNAN),
    O('Verdict', 'text', 'IF({in:confirmed}>={in:quorum},%s,%s&" "&({in:quorum}-{in:confirmed})&" "&%s)' % (c2('Quorum met'), c3('Need'), c3('more')))],
    GR('What if', ('Six confirmed', {'confirmed': 6}), ('Four confirmed, three cannot come', {'confirmed': 4, 'declined': 3}), ('Quorum of 5', {'quorum': 5}), ('Two confirmed', {'confirmed': 2}), ('Everyone replied yes', {'confirmed': 11, 'declined': 0}))))

# 9 ------------------------------------------------------------ minutes tracker
NF = 'COUNTIFS(%s,%s,%s,%s)' % (R('meetings', 'status'), HELD, R('meetings', 'minutes_ready'), NO)
MN_ = lambda k, col: SK('meetings', col, 'minutes_key', k)
tools.append(TOOL('minutes_tracker', 'Minutes Tracker', 'Which minutes are still not final',
    'Type the days after a meeting by which minutes should be final; held meetings without final minutes are counted and the oldest three are named with the days since.', [
    I('days', 'Days after a meeting that minutes should be final', 21, 'int')], [
    O('Meetings held', 'int', 'COUNTIFS(%s,%s)' % (R('meetings', 'status'), HELD)), O('Meetings held this year', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (R('meetings', 'status'), HELD, R('meetings', 'year'), YN)),
    O('Minutes not final', 'int', NF), O('Minutes not final past the days', 'int', 'COUNTIFS(%s,">"&{in:days})' % R('meetings', 'minutes_age')),
    O('Share of held meetings with final minutes', 'pct', 'IFERROR(1-%s/COUNTIFS(%s,%s),0)' % (NF, R('meetings', 'status'), HELD)),
    O('Oldest meeting, date', 'date', 'IFERROR(INT(SMALL(%s,1)),"-")' % R('meetings', 'minutes_key')), O('Oldest meeting, kind', 'text', MN_(1, 'kind')), O('Oldest meeting, days since', 'int', MN_(1, 'minutes_age')),
    O('Second meeting, date', 'date', 'IFERROR(INT(SMALL(%s,2)),"-")' % R('meetings', 'minutes_key')), O('Second meeting, kind', 'text', MN_(2, 'kind')), O('Third meeting, date', 'date', 'IFERROR(INT(SMALL(%s,3)),"-")' % R('meetings', 'minutes_key')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (NF, c3('Up to date'), c3('Finish minutes'), NF))],
    GR('What if', ('Final within 7 days', {'days': 7}), ('Final within 14 days', {'days': 14}), ('Final within 30 days', {'days': 30}), ('Final within 60 days', {'days': 60}))))

# 10 ----------------------------------------------------------- attendance by member
def AMV(col, per): return 'SUMIFS(%s,%s,{in:member},%s,%s)' % (R('attendance_member', col), R('attendance_member', 'member'), R('attendance_member', 'period'), per)
SH_T = 'IFERROR(%s/%s,0)' % (AMV('present', THIS3), AMV('meetings', THIS3))
SH_L = 'IFERROR(%s/%s,0)' % (AMV('present', LAST3), AMV('meetings', LAST3))
SH_2 = 'IFERROR(%s/%s,0)' % (AMV('present', TWO3), AMV('meetings', TWO3))
tools.append(TOOL('attendance_tool', 'Member Attendance Check', 'Is this member attending enough',
    'Pick a member and type the share you expect; the attendance of the last three years is set against it, with the extra meetings the member would need to attend to reach it.', [
    IL('member', 'Board member', 'bmember', 'Aisha Bello'), I('min', 'Attendance share you expect', ATTEND_MIN, 'pct')], [
    O('Meetings this year', 'int', AMV('meetings', THIS3)), O('Present this year', 'int', AMV('present', THIS3)), O('Attendance this year', 'pct', SH_T), O('Attendance last year', 'pct', SH_L), O('Attendance two years ago', 'pct', SH_2),
    O('Change from last year, points', 'pct', '%s-%s' % (SH_T, SH_L)), O('Share you expect', 'pct', '{in:min}'), O('Short of the share by', 'pct', 'MAX(0,{in:min}-%s)' % SH_T),
    O('Meetings in a row to attend to reach the share', 'int', 'IF(%s>={in:min},0,IFERROR(ROUNDUP(({in:min}*%s-%s)/(1-{in:min}),0),0))' % (SH_T, AMV('meetings', THIS3), AMV('present', THIS3))),
    O('Board meetings still planned', 'int', 'COUNT(%s)' % R('meetings', 'next_board')), O('Members under the share, all members', 'int', 'COUNTIFS(%s,%s,%s,"<"&{in:min})' % (R('attendance_member', 'period'), THIS3, R('attendance_member', 'share'))),
    O('Verdict', 'text', 'IF(%s>={in:min},%s,%s&" "&{in:member})' % (SH_T, c1('On track'), c3('Call')))],
    GR('What if', ('Thomas Whitmore', {'member': '=' + tok('bmember', 'Thomas Whitmore')}), ('Michael Brandt', {'member': '=' + tok('bmember', 'Michael Brandt')}), ('Jonas Eriksen', {'member': '=' + tok('bmember', 'Jonas Eriksen')}),
       ('Expect 90 percent', {'min': 0.9}), ('Expect 50 percent', {'min': 0.5}))))

# 11 ----------------------------------------------------------- low attendance ranker
def LA(k, col): return 'IF(%s<{in:min},%s,"-")' % (LG('attendance_member', 'share', 'rank_score', k), LG('attendance_member', col, 'rank_score', k))
tools.append(TOOL('low_attendance', 'Low Attendance Ranker', 'Who attends least, and who do we talk to first',
    'Type the share you expect; members under it this year are counted and the three furthest below are named with their share and the shortfall.', [
    I('min', 'Attendance share you expect', ATTEND_MIN, 'pct')], [
    O('Members under the share this year', 'int', 'COUNTIFS(%s,%s,%s,"<"&{in:min})' % (R('attendance_member', 'period'), THIS3, R('attendance_member', 'share'))),
    O('Average attendance of members this year', 'pct', 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (R('attendance_member', 'share'), R('attendance_member', 'period'), THIS3)),
    O('Lowest member', 'text', LA(1, 'member')), O('Lowest member, share', 'pct', LA(1, 'share')), O('Lowest member, short by', 'pct', 'IF(%s<{in:min},{in:min}-%s,"-")' % (LG('attendance_member', 'share', 'rank_score', 1), LG('attendance_member', 'share', 'rank_score', 1))),
    O('Second lowest member', 'text', LA(2, 'member')), O('Second lowest, share', 'pct', LA(2, 'share')), O('Third lowest member', 'text', LA(3, 'member')), O('Third lowest, share', 'pct', LA(3, 'share')),
    O('Members who attended all their meetings', 'int', 'COUNTIFS(%s,%s,%s,1)' % (R('attendance_member', 'period'), THIS3, R('attendance_member', 'share'))),
    O('Verdict', 'text', 'IF(%s<{in:min},%s&" "&%s,%s)' % (LG('attendance_member', 'share', 'rank_score', 1), c3('Talk to'), LG('attendance_member', 'member', 'rank_score', 1), c3('Fine')))],
    GR('What if', ('Expect 90 percent', {'min': 0.9}), ('Expect 65 percent', {'min': 0.65}), ('Expect 50 percent', {'min': 0.5}), ('Expect 40 percent', {'min': 0.4}))))

# 12 ----------------------------------------------------------- board giving view
def BGV_(col, per): return 'SUMIFS(%s,%s,{in:member},%s,%s)' % (R('board_giving', col), R('board_giving', 'member'), R('board_giving', 'period'), per)
tools.append(TOOL('board_giving_view', 'Board Giving View', 'Has this member given this year',
    'Pick a member; the gifts of the last three years from the gift log are shown with the board total and the members who have not given yet.', [
    IL('member', 'Board member', 'bmember', 'Aisha Bello')], [
    O('Gifts this year', 'int', BGV_('gifts', THIS3)), O('Total this year', 'money', BGV_('total', THIS3)), O('Total last year', 'money', BGV_('total', LAST3)), O('Total two years ago', 'money', BGV_('total', TWO3)),
    O('Change from last year', 'money', '%s-%s' % (BGV_('total', THIS3), BGV_('total', LAST3))), O('Share of the give or get target', 'pct', 'IFERROR(%s/{set:give_or_get},0)' % BGV_('total', THIS3)),
    O('Board giving this year', 'money', 'SUMIFS(%s,%s,%s)' % (R('board_giving', 'total'), R('board_giving', 'period'), THIS3)), O('Members who gave this year', 'int', 'SUMIFS(%s,%s,%s)' % (R('board_giving', 'gave'), R('board_giving', 'period'), THIS3)),
    O('Members who have not given yet', 'int', 'COUNTIFS(%s,%s,%s,0)' % (R('board_giving', 'period'), THIS3, R('board_giving', 'total'))),
    O('Average gift of the members who gave', 'money', 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s,%s,">0"),0)' % (R('board_giving', 'total'), R('board_giving', 'period'), THIS3, R('board_giving', 'gifts'), R('board_giving', 'period'), THIS3, R('board_giving', 'total'))),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (BGV_('total', THIS3), c1('Gave'), c1('Not yet')))],
    GR('What if', ('Dr. Ngozi Eze', {'member': '=' + tok('bmember', 'Dr. Ngozi Eze')}), ('Sunita Rao', {'member': '=' + tok('bmember', 'Sunita Rao')}), ('Peter Okonkwo', {'member': '=' + tok('bmember', 'Peter Okonkwo')}),
       ('Thomas Whitmore', {'member': '=' + tok('bmember', 'Thomas Whitmore')}), ('Lin Wei', {'member': '=' + tok('bmember', 'Lin Wei')}))))

# 13 ----------------------------------------------------------- board giving share
def GV(per): return 'SUMIFS(%s,%s,%s)' % (R('board_giving', 'gave'), R('board_giving', 'period'), per)
ST_ = 'IFERROR(%s/%s,0)' % (GV(THIS3), SERV); SL_ = 'IFERROR(%s/%s,0)' % (GV(LAST3), SERV); S2_ = 'IFERROR(%s/%s,0)' % (GV(TWO3), SERV)
tools.append(TOOL('giving_share', 'Board Giving Share Tool', 'Is the share of the board that gives better than last year',
    'Type the share of the board you want to give; members who gave this year, last year and two years ago are compared, with how many more need to give.', [
    I('target', 'Share of the board you want to give', 1.0, 'pct')], [
    O('Members serving now', 'int', SERV), O('Gave this year', 'int', GV(THIS3)), O('Share this year', 'pct', ST_), O('Gave last year', 'int', GV(LAST3)), O('Share last year', 'pct', SL_), O('Gave two years ago', 'int', GV(TWO3)), O('Share two years ago', 'pct', S2_),
    O('Change from last year, points', 'pct', '%s-%s' % (ST_, SL_)), O('Members who need to give to reach your target', 'int', 'MAX(0,ROUNDUP({in:target}*%s-%s,0))' % (SERV, GV(THIS3))),
    O('Board giving this year', 'money', 'SUMIFS(%s,%s,%s)' % (R('board_giving', 'total'), R('board_giving', 'period'), THIS3)), O('Board giving last year', 'money', 'SUMIFS(%s,%s,%s)' % (R('board_giving', 'total'), R('board_giving', 'period'), LAST3)),
    O('Verdict', 'text', 'IF(%s>%s,%s,IF(%s<%s,%s,%s))' % (ST_, SL_, c3('Better'), ST_, SL_, c3('Worse'), c3('Same')))],
    GR('What if', ('Target 90 percent', {'target': 0.9}), ('Target 75 percent', {'target': 0.75}), ('Target 50 percent', {'target': 0.5}), ('Target 100 percent', {'target': 1.0}))))

# 14 ----------------------------------------------------------- give or get tracker
GGV = lambda col: 'SUMIFS(%s,%s,%s)' % (R('give_or_get', col), R('give_or_get', 'period'), THIS2)
PACE = 'MIN(1,({today}-DATE(YEAR({today}),1,1))/365)'
TTOT = '({in:target}*%s)' % SERV
GGL = lambda k, col: LG('give_or_get', col, 'rank_score', k)
tools.append(TOOL('give_or_get_tracker', 'Give or Get Tracker', 'Is the board on target for give or get',
    'Type the give or get target for each member (your own policy); money given and raised is set against the target and the share of the year passed.', [
    I('target', 'Give or get target for each member', GIVE_OR_GET)], [
    O('Members serving now', 'int', SERV), O('Target for the whole board', 'money', TTOT), O('Given this year', 'money', GGV('given')), O('Raised through asks this year', 'money', GGV('raised')), O('Given and raised', 'money', GGV('total')),
    O('Remaining to the target', 'money', 'MAX(0,%s-%s)' % (TTOT, GGV('total'))), O('Share of the year that has passed', 'pct', PACE), O('Where you should be by now', 'money', 'ROUND(%s*%s,0)' % (TTOT, PACE)),
    O('Members who met the target', 'int', 'COUNTIFS(%s,%s,%s,">="&{in:target})' % (R('give_or_get', 'period'), THIS2, R('give_or_get', 'total'))), O('Members behind the year', 'int', 'COUNTIFS(%s,%s,%s,"<"&{in:target}*%s)' % (R('give_or_get', 'period'), THIS2, R('give_or_get', 'total'), PACE)),
    O('Most left to go, member', 'text', GGL(1, 'member')), O('Most left to go, remaining', 'money', GGL(1, 'remaining')), O('Second most left, member', 'text', GGL(2, 'member')), O('Second most left, remaining', 'money', GGL(2, 'remaining')),
    O('Verdict', 'text', 'IF(%s>=ROUND(%s*%s,0),%s,%s&" "&ROUND(ROUND(%s*%s,0)-%s,0))' % (GGV('total'), TTOT, PACE, c1('On target'), c3('Behind by'), TTOT, PACE, GGV('total')))],
    GR('What if', ('Target 500', {'target': 500}), ('Target 1,500', {'target': 1500}), ('Target 2,000', {'target': 2000}), ('Target 250', {'target': 250}))))

# 15 ----------------------------------------------------------- declaration tracker
DC = lambda extra='': 'COUNTIFS(%s,{in:year}%s)' % (R('declarations', 'year'), extra)
OPEN15 = DC(',%s,"<>"&%s,%s,"<>"' % (R('declarations', 'status'), FILED, R('declarations', 'decl_id')))
DL = lambda k, col: LG('decl_status', col, 'rank_score', k)
tools.append(TOOL('declaration_tool', 'Declaration Tracker', 'Who has filed their declaration of interests',
    'Pick a year; declarations filed, due and overdue are counted with the items declared, and the member with the most days overdue this year is named.', [
    IL('year', 'Year', 'yr3', 'This year')], [
    O('Declarations in the year', 'int', DC()), O('Filed', 'int', DC(',%s,%s' % (R('declarations', 'status'), FILED))), O('Due, not yet late', 'int', DC(',%s,%s' % (R('declarations', 'status'), tok('dclstatus', 'Due')))),
    O('Overdue', 'int', DC(',%s,%s' % (R('declarations', 'status'), tok('dclstatus', 'Overdue')))), O('Share filed', 'pct', 'IFERROR(%s/%s,0)' % (DC(',%s,%s' % (R('declarations', 'status'), FILED)), DC())),
    O('Items declared in the year', 'int', 'SUMIFS(%s,%s,{in:year})' % (R('declarations', 'items_declared'), R('declarations', 'year'))), O('Members who declared at least one item', 'int', DC(',%s,">0"' % R('declarations', 'items_declared'))),
    O('Filed late', 'int', 'COUNTIFS(%s,{in:year},%s,%s)' % (R('decl_status', 'year'), R('decl_status', 'flag'), c1('Filed late'))),
    O('Most overdue this year, member', 'text', DL(1, 'member')), O('Most overdue this year, days late', 'int', DL(1, 'days_late')), O('Second most overdue, member', 'text', DL(2, 'member')), O('Second most overdue, days late', 'int', DL(2, 'days_late')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (OPEN15, c3('All filed'), c3('Chase'), OPEN15))],
    GR('What if', ('Last year', {'year': '=' + tok('yr3', 'Last year')}), ('Two years ago', {'year': '=' + tok('yr3', 'Two years ago')}), ('This year', {'year': '=' + tok('yr3', 'This year')}))))

# 16 ----------------------------------------------------------- obligation calendar
OCK = lambda k, col: 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"-")' % (R('ob_calendar', col), k, R('ob_calendar', 'rank'))
OVN = 'COUNTIFS(%s,%s)' % (R('ob_calendar', 'flag'), c1('Overdue'))
MON = 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (R('ob_calendar', 'flag'), c1('Due this month'), R('ob_calendar', 'flag'), c1('Due this week'))
tools.append(TOOL('obligation_tool', 'Obligation Calendar Tool', 'What is overdue or due soon',
    'Type how many days ahead you want to look; obligations are counted as overdue, due this month and due in the days ahead, and the next three in date order are named.', [
    I('days', 'Days ahead to look', 30, 'int')], [
    O('Overdue now', 'int', OVN), O('Due this month, including this week', 'int', MON), O('Due in the days ahead', 'int', 'COUNTIFS(%s,">=0",%s,"<="&{in:days})' % (R('ob_calendar', 'days_away'), R('ob_calendar', 'days_away'))),
    O('Done in the last 30 days', 'int', 'COUNTIFS(%s,">="&({today}-30))' % R('ob_calendar', 'done_on')), O('Oldest overdue item', 'text', 'IFERROR(INDEX(%s,1),"")' % R('ob_calendar', 'oldest_item')),
    O('Next item, name', 'text', OCK(1, 'item')), O('Next item, date', 'date', OCK(1, 'due_date')), O('Next item, days away', 'int', OCK(1, 'days_away')),
    O('Second item, name', 'text', OCK(2, 'item')), O('Second item, date', 'date', OCK(2, 'due_date')), O('Third item, name', 'text', OCK(3, 'item')), O('Third item, date', 'date', OCK(3, 'due_date')),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s,IF(%s>0,%s&" "&(%s),%s))' % (OVN, c1('Overdue'), OVN, MON, c3('Due this month'), MON, c3('Clear')))],
    GR('What if', ('One week ahead', {'days': 7}), ('Two weeks ahead', {'days': 14}), ('60 days ahead', {'days': 60}), ('90 days ahead', {'days': 90}))))

# 17 ----------------------------------------------------------- policy and renewal review planner
DUE17 = MIND('{in:kind}')
def DASH(x): return 'IF(%s="","-",%s)' % (x, x)
LAST17 = 'SUMPRODUCT(MAX((%s={in:kind})*%s))' % (R('obligations', 'kind'), R('obligations', 'done_on'))
tools.append(TOOL('policy_planner', 'Policy and Renewal Planner', 'When must we start the next review or renewal',
    'Pick a kind of obligation and the days before the due date you start; the next due date, the start date and the dates of renewals and returns are shown.', [
    IL('kind', 'Kind of obligation', 'obkind', 'Insurance renewal'), I('lead', 'Days before the due date that you start', 45, 'int')], [
    O('Next open due date', 'date', DASH(DUE17)), O('Days to the due date', 'int', 'IF(%s="","-",%s-{today})' % (DUE17, DUE17)), O('Start on', 'date', 'IF(%s="","-",%s-{in:lead})' % (DUE17, DUE17)), O('Days to the start date', 'int', 'IF(%s="","-",%s-{in:lead}-{today})' % (DUE17, DUE17)),
    O('Last done on', 'date', 'IF(%s=0,"-",%s)' % (LAST17, LAST17)), O('Repeats every, months', 'int', 'IFERROR(INDEX(%s,MATCH({in:kind},%s,0)),"")' % (R('ob_kinds', 'repeats_months'), R('ob_kinds', 'kind'))),
    O('Owner', 'text', 'IFERROR(INDEX(%s,MATCH({in:kind},%s,0))&"","")' % (R('ob_kinds', 'owner'), R('ob_kinds', 'kind'))),
    O('Next insurance renewal', 'date', DASH(MIND(tok('obkind', 'Insurance renewal')))), O('Next policy review', 'date', DASH(MIND(tok('obkind', 'Policy review')))), O('Next yearly information return', 'date', DASH(MIND(tok('obkind', 'Yearly return')))),
    O('Open obligations of this kind', 'int', 'COUNTIFS(%s,{in:kind},%s,"<>"&%s,%s,"<>")' % (R('obligations', 'kind'), R('obligations', 'status'), OBDONE, R('obligations', 'ob_id'))),
    O('Verdict', 'text', 'IF(%s="",%s,IF({today}>=%s-{in:lead},%s,%s))' % (DUE17, c3('Clear'), DUE17, c3('Start now'), c3('On time')))],
    GR('What if', ('Policy review', {'kind': '=' + tok('obkind', 'Policy review')}), ('Yearly return, 90 days', {'kind': '=' + tok('obkind', 'Yearly return'), 'lead': 90}), ('Safety check', {'kind': '=' + tok('obkind', 'Safety check')}),
       ('Board training, 30 days', {'kind': '=' + tok('obkind', 'Board training'), 'lead': 30}), ('Annual report, 60 days', {'kind': '=' + tok('obkind', 'Annual report'), 'lead': 60}))))

# 18 ----------------------------------------------------------- board pack builder
PK = lambda n: 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"")' % (R('board_pack', 'number'), n, R('board_pack', 'no'))
tools.append(TOOL('pack_builder', 'Board Pack Builder', 'Is the board pack ready to send',
    'Type the days before the meeting that papers go out; the pack items are counted by flag, the first missing item is named and the main numbers are shown on one page.', [
    I('papers', 'Days before the meeting that papers go out', 7, 'int')], [
    O('Items in the pack', 'int', 'COUNTIFS(%s,">0")' % R('board_pack', 'no')), O('Items missing', 'int', 'COUNTIFS(%s,%s)' % (R('board_pack', 'flag'), c2('Missing'))), O('Items to act on', 'int', 'COUNTIFS(%s,%s)' % (R('board_pack', 'flag'), c2('Act'))),
    O('Items to watch', 'int', 'COUNTIFS(%s,%s)' % (R('board_pack', 'flag'), c2('Watch'))), O('Items fine', 'int', 'COUNTIFS(%s,%s)' % (R('board_pack', 'flag'), c2('OK'))), O('First missing item', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (R('board_pack', 'item'), c2('Missing'), R('board_pack', 'flag'))),
    O('Next board meeting', 'date', NB), O('Papers go out on', 'date', 'IFERROR(%s-{in:papers},"")' % NB), O('Days to send the papers', 'int', 'IFERROR(%s-{in:papers}-{today},"")' % NB),
    O('Cash at the bank', 'money', PK(1)), O('Months of reserve', 'num', PK(2)), O('Attendance this year, percent', 'int', PK(8)), O('Obligations overdue now', 'int', PK(11)), O('Members under the attendance setting', 'int', PK(9)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)=0,%s,%s&" "&IFERROR(INDEX(%s,MATCH(%s,%s,0)),""))' % (R('board_pack', 'flag'), c2('Missing'), c3('Pack ready'), c2('Missing'), R('board_pack', 'item'), c2('Missing'), R('board_pack', 'flag')))],
    GR('What if', ('Papers 3 days before', {'papers': 3}), ('Papers 10 days before', {'papers': 10}), ('Papers 14 days before', {'papers': 14}), ('Papers 1 day before', {'papers': 1}))))
assert len(tools) == 18, len(tools)
