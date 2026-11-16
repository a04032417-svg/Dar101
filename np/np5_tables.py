"""Nonprofit suite part 5: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np5_lists import *
import np5_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def ORG(): return CA('org', 'Organization', 'text', '{set:org}', 22)
def CPH(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def R(t, c): return '{range:%s.%s}' % (t, c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YS = 'DATE(YEAR({today}),1,1)'
QSF = 'DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+1,1)'
PG = lambda p: tok('program', p)
ACTV, WAITG, COMP, LEFT = tok('pstat', 'Active'), tok('pstat', 'Waiting'), tok('pstat', 'Completed'), tok('pstat', 'Left')
FP, FS, FM_, FF_ = tok('function', 'Program'), tok('function', 'Shared'), tok('function', 'Management'), tok('function', 'Fundraising')
SHP = tok('sprogram', 'Shared')
UPTO = tok('cstat', 'Up to date')

settings = [
    S('org', 'Your organization name', 'text', COMPANY),
    S('not_seen_days', 'Days without a visit that put a person on the not-seen list', 'int', 14),
    S('close_after_days', 'Days without a visit after which you propose to close', 'int', 90),
    S('recent_days', 'Days that count as seen recently', 'int', 30),
    S('full_share', 'Share of capacity at which a program counts as full', 'pct', 0.95),
    S('quiet_share', 'Share of capacity below which a month is quiet', 'pct', 0.40),
    S('change_margin', 'Change against last year that still counts as the same', 'pct', 0.05),
    S('cost_rise_limit', 'Rise in cost per participant that makes you review a program', 'pct', 0.10),
    S('outcome_min', 'Share of the outcome targets a program should meet', 'pct', 0.90),
    S('waiting_target_weeks', 'Weeks a waiting list may take to clear before you add places', 'int', 4),
    S('volunteer_hour_value', 'Value of one volunteer hour, your setting', 'money', VOLUNTEER_HOUR_VALUE),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 participants -----------------------------------------------------------
tables.append(T('participants', 'Participants', 'Participants by name, program and last visit',
    'One row per participant: program, status, start, last attended and sessions; days since the last visit and the not-seen flag fill in. Names, contact status, counts and dates only.', [
    C('participant_id', 'Participant ID', 'text', 11, required=True), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18), LST('program', 'Program', 'program', 22), LST('status', 'Status', 'pstat', 11),
    C('start_date', 'Start date', 'date', 11), C('last_attended', 'Last attended', 'date', 11), C('sessions', 'Sessions', 'int', 9), LST('contact_status', 'Contact status', 'cstat', 13),
    C('notice_date', 'Date in a notice', 'date', 11), C('notice_time', 'Time in a notice', 'time', 10),
    CA('days_since', 'Days since last seen', 'int', 'IF({col:last_attended}>0,{today}-{col:last_attended},"")', 9),
    CA('seen_recent', 'Seen recently', 'int', 'IF(AND({col:status}=%s,ISNUMBER({col:days_since})),IF({col:days_since}<={set:recent_days},1,0),0)' % ACTV, 8),
    CA('not_seen', 'Not seen', 'int', 'IF(AND({col:status}=%s,ISNUMBER({col:days_since})),IF({col:days_since}>{set:not_seen_days},1,0),0)' % ACTV, 8),
    CA('contact_fix', 'Contact to fix', 'int', 'IF(AND({col:status}=%s,{col:contact_status}<>%s),1,0)' % (ACTV, UPTO), 8),
    CA('not_seen_score', 'Call score for the not-seen ranking', 'int', 'IF({col:not_seen}=1,{col:sessions}*10000000+{col:days_since}*10000+VALUE(RIGHT({col:participant_id},4)),0)', 12),
    CA('not_seen_n', 'Participants not seen', 'int', 'SUM({range:participants.not_seen})', 9), CA('not_seen_limit', 'Not-seen days', 'int', '{set:not_seen_days}', 8), CA('close_after', 'Close after days', 'int', '{set:close_after_days}', 8),
    CPH('pm_phone', 'Program manager phone', D.PM_PHONE), CPH('asst_phone', 'Program assistant phone', D.ASST_PHONE), ORG()],
    D.participants_d(), 3000, [A('contact_status', '= ' + tok('cstat', 'Lost touch'), 'bad'), A('contact_status', '= ' + tok('cstat', 'Check in'), 'warn'), A('status', '= ' + ACTV, 'good')]))
# 2 programs ---------------------------------------------------------------
tables.append(T('programs', 'Programs', 'Programs with their capacity and lead',
    'One row per program: the number of people it can hold at one time and the staff member who leads it. Shared stands for costs that belong to all programs.', [
    LST('program', 'Program', 'sprogram', 24, required=True), C('capacity', 'Capacity', 'int', 10), C('lead', 'Lead', 'text', 22)],
    [dict(program=key('sprogram', p['program']), capacity=p['capacity'], lead=p['lead']) for p in programs] + [dict(program=key('sprogram', 'Shared'), capacity=0, lead='Priya Nair')], 50))
# 3 program months ---------------------------------------------------------
tables.append(T('program_months', 'Program Months', 'People, visits and capacity of each program every month',
    'One row per program and month: people, visits, new people, sessions, capacity, waiting, volunteer hours and money coded to the program; the capacity used and a verdict (full, healthy, quiet) fill in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('program', 'Program', 'program', 22), C('participants', 'People', 'int', 9), C('visits', 'Visits', 'int', 9),
    C('new_participants', 'New people', 'int', 9), C('sessions', 'Sessions', 'int', 9), C('capacity', 'Capacity', 'int', 9), C('waiting', 'Waiting', 'int', 9), C('vol_hours', 'Volunteer hours', 'num', 11), C('funding', 'Money coded to program', 'money', 13),
    CA('share_used', 'Capacity used', 'pct', 'IF({col:capacity}>0,{col:participants}/{col:capacity},0)', 9),
    CA('visits_per_person', 'Visits per person', 'num', 'IF({col:participants}>0,ROUND({col:visits}/{col:participants},1),0)', 9),
    CA('verdict', 'Verdict', 'text', 'IF(AND({col:participants}=0,{col:sessions}=0),%s,IF({col:share_used}>={set:full_share},%s,IF({col:share_used}<{set:quiet_share},%s,%s)))' % (c1('Off season'), c1('Full'), c1('Quiet'), c1('Healthy')), 11),
    CA('is_now', 'This month', 'int', 'IF({col:month}=%s,1,0)' % MS, 7), CA('in_last12', 'Last 12 months', 'int', 'IF(AND({col:month}>=EDATE(%s,-11),{col:month}<=%s),1,0)' % (MS, MS), 7),
    CA('in_prev12', 'The 12 months before', 'int', 'IF(AND({col:month}>=EDATE(%s,-23),{col:month}<=EDATE(%s,-12)),1,0)' % (MS, MS), 7),
    CA('cap_in_season', 'Capacity in season', 'int', 'IF({col:participants}>0,{col:capacity},0)', 8), CA('free_places', 'Free places', 'int', 'IF({col:participants}>0,MAX(0,{col:capacity}-{col:participants}),{col:capacity})', 8),
    CA('fit', 'Waiting who fit', 'int', 'MIN({col:waiting},{col:free_places})', 8), CA('due_date', 'Numbers due by', 'date', 'EOMONTH({col:month},0)+5', 11),
    CPH('pm_phone', 'Program manager phone', D.PM_PHONE), CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('board_phone', 'Board member phone', D.TREAS_PHONE), CPH('partner_phone', 'Partner phone', D.PARTNER_PHONE), ORG()],
    D.program_months_d(), 300, [A('verdict', '= ' + c1('Full'), 'warn'), A('verdict', '= ' + c1('Quiet'), 'bad'), A('verdict', '= ' + c1('Healthy'), 'good')]))
# 4 sessions ---------------------------------------------------------------
tables.append(T('sessions', 'Sessions', 'Every session with its attendees and volunteers',
    'One row per session: date, program, the staff member, the people who came and the volunteers who helped; the staff phone fills in for the reminder messages.', [
    C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('program', 'Program', 'program', 22), LST('staff', 'Staff', 'staff', 18),
    C('attendees', 'Attendees', 'int', 9), C('volunteers', 'Volunteers', 'int', 9),
    CA('staff_phone', 'Staff phone', 'text', 'IF({col:staff}=%s,"%s",IF({col:staff}=%s,"%s","%s"))' % (tok('staff', 'Amira Haddad'), D.STAFF_PHONE['Amira Haddad'], tok('staff', 'Tomasz Wrona'), D.STAFF_PHONE['Tomasz Wrona'], D.STAFF_PHONE['Mei-Ling Tan']), 18),
    CPH('vol_phone', 'Volunteer phone', D.VOL_PHONE), ORG()], D.sessions_d(), 3000))
# 5 not seen list ------------------------------------------------------------
def NS(col): return 'IF({col:rank}>COUNTIF({range:participants.not_seen_score},">0"),"",IFERROR(INDEX({range:participants.%s},MATCH(LARGE({range:participants.not_seen_score},{col:rank}),{range:participants.not_seen_score},0)),""))' % col
tables.append(T('not_seen', 'Not Seen List', 'Active participants not seen, most sessions first',
    'Ranked by sessions before: the active participants not seen for more days than the setting, with the days since, contact status, phone and what to do (call this week or close the record).', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('participant_id', 'Participant ID', 'text', NS('participant_id'), 11), CA('name', 'Name', 'text', NS('name'), 24), CA('program', 'Program', 'text', NS('program'), 22), CA('last_attended', 'Last attended', 'date', NS('last_attended'), 11),
    CA('days_since', 'Days since', 'int', NS('days_since'), 8), CA('sessions', 'Sessions before', 'int', NS('sessions'), 9), CA('contact_status', 'Contact status', 'text', NS('contact_status'), 13), CA('phone', 'Phone', 'text', NS('phone'), 18),
    CA('action', 'Action', 'text', 'IF({col:days_since}="","",IF({col:days_since}>{set:close_after_days},%s,%s))' % (c1('Close the record'), c1('Call this week')), 16), ORG()],
    D.not_seen_d(), 120, [A('action', '= ' + c1('Close the record'), 'bad'), A('action', '= ' + c1('Call this week'), 'warn')]))
# 6 served by program and year ----------------------------------------------
def SYD(y): return 'COUNTIFS({range:participants.program},{col:program},{range:participants.start_date},"<="&DATE(%s,12,31),{range:participants.last_attended},">="&DATE(%s,1,1))' % (y, y)
def SYM(col, y): return 'SUMIFS({range:program_months.%s},{range:program_months.program},{col:program},{range:program_months.month},">="&DATE(%s,1,1),{range:program_months.month},"<="&DATE(%s,12,1))' % (col, y, y)
tables.append(T('served_year', 'Served by Program and Year', 'People, visits and sessions of each program by year',
    'One row per program and year: the people on your books in that year (started on or before its end, last seen on or after its start), visits, sessions and the change on the year before.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('program', 'Program', 'program', 22), LST('year', 'Year', 'syear', 8),
    CA('year_no', 'Year number', 'int', 'VALUE({col:year})', 8), CA('unique_people', 'Unique people', 'int', SYD('{col:year_no}'), 10), CA('visits', 'Visits', 'int', SYM('visits', '{col:year_no}'), 10),
    CA('sessions', 'Sessions', 'int', SYM('sessions', '{col:year_no}'), 10), CA('new_people', 'New people', 'int', SYM('new_participants', '{col:year_no}'), 10), CA('vol_hours', 'Volunteer hours', 'num', SYM('vol_hours', '{col:year_no}'), 10),
    CA('prev_people', 'People the year before', 'int', SYD('{col:year_no}-1'), 10), CA('change', 'Change on the year before', 'pct', 'IF({col:prev_people}>0,{col:unique_people}/{col:prev_people}-1,"")', 10),
    CA('visits_per_person', 'Visits per person', 'num', 'IF({col:unique_people}>0,ROUND({col:visits}/{col:unique_people},1),0)', 9), CPH('acc_phone', 'Accountant phone', D.ACC_PHONE), ORG()],
    D.served_year_d(), 50))
# 7 served this month ----------------------------------------------------------
tables.append(T('served_month', 'Served This Month', 'People and visits of each program this month',
    'One row per program: the people and visits of the current month, taken from Program Months; a program in its off season shows zero.', [
    LST('program', 'Program', 'sprogram', 24, required=True),
    CA('people', 'People', 'int', 'SUMIFS({range:program_months.participants},{range:program_months.program},{col:program},{range:program_months.month},%s)' % MS, 10),
    CA('visits', 'Visits', 'int', 'SUMIFS({range:program_months.visits},{range:program_months.program},{col:program},{range:program_months.month},%s)' % MS, 10)],
    [dict(program=key('sprogram', p)) for p in SPROGRAMS], 50))
# 8 expenses -------------------------------------------------------------------
def SHR(col): return 'IFERROR(INDEX({range:alloc.%s},MATCH({col:category},{range:alloc.category},0)),0)' % col
tables.append(T('expenses', 'Program Expenses', 'Every expense with its program, function and fund',
    'One row per expense: date, category, program, function, fund and amount; the part that belongs to programs, management and fundraising fills in from the Cost Allocation Rules.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('category', 'Category', 'category', 22), LST('program', 'Program', 'sprogram', 22),
    LST('function', 'Function', 'function', 12), LST('fund', 'Fund', 'fund', 22), C('amount', 'Amount', 'money', 12),
    CA('to_program', 'To programs', 'money', 'ROUND({col:amount}*IF({col:function}=%s,1,IF({col:function}=%s,%s,0)),2)' % (FP, FS, SHR('program_share')), 12),
    CA('to_management', 'To management', 'money', 'ROUND({col:amount}*IF({col:function}=%s,1,IF({col:function}=%s,%s,0)),2)' % (FM_, FS, SHR('management_share')), 12),
    CA('to_fundraising', 'To fundraising', 'money', 'ROUND({col:amount}*IF({col:function}=%s,1,IF({col:function}=%s,%s,0)),2)' % (FF_, FS, SHR('fundraising_share')), 12),
    CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), ORG()], D.expenses_d(), 3000))
# 9 cost allocation rules ------------------------------------------------------
tables.append(T('alloc', 'Cost Allocation Rules', 'How each shared cost is split three ways',
    'One row per expense category: the share to programs, management and fundraising and the rule that gives it; each row must total 100 percent. Costs coded Shared use these shares.', [
    LST('category', 'Category', 'category', 24, required=True), C('program_share', 'Program share', 'pct', 10), C('management_share', 'Management share', 'pct', 10), C('fundraising_share', 'Fundraising share', 'pct', 10), C('rule', 'Rule', 'text', 14),
    CA('total_share', 'Total', 'pct', '{col:program_share}+{col:management_share}+{col:fundraising_share}', 9),
    CA('check', 'Check', 'text', 'IF(ABS({col:total_share}-1)<0.0001,%s,%s)' % (c1('Rule is complete'), c1('Rule is off')), 14)], D.alloc_d(), 50, [A('check', '= ' + c1('Rule is off'), 'bad')]))
# 10 program cost ---------------------------------------------------------------
EXM = '{range:expenses.month},{col:month}'
tables.append(T('program_cost', 'Program Cost', 'Direct and shared cost of each program every month',
    'One row per program and month: direct cost coded to the program, its share of the shared cost, the total, the people and the cost per participant fill in from Program Expenses and Program Months.', [
    C('cost_id', 'Cost ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('program', 'Program', 'program', 22),
    CA('direct_cost', 'Direct cost', 'money', 'SUMIFS({range:expenses.amount},%s,{range:expenses.program},{col:program},{range:expenses.function},%s)' % (EXM, FP), 12),
    CA('pool', 'Shared cost to share out', 'money', 'SUMIFS({range:expenses.to_program},%s,{range:expenses.program},%s)' % (EXM, SHP), 12),
    CA('month_direct', 'Direct cost of all programs', 'money', 'SUMIFS({range:expenses.amount},%s,{range:expenses.function},%s,{range:expenses.program},"<>"&%s)' % (EXM, FP, SHP), 12),
    CA('shared_cost', 'Shared cost', 'money', 'IF({col:month_direct}>0,ROUND({col:pool}*{col:direct_cost}/{col:month_direct},2),0)', 12), CA('total', 'Total cost', 'money', '{col:direct_cost}+{col:shared_cost}', 12),
    CA('people', 'People', 'int', 'SUMIFS({range:program_months.participants},{range:program_months.program},{col:program},{range:program_months.month},{col:month})', 8),
    CA('cost_per_participant', 'Cost per participant', 'money', 'IF({col:people}>0,ROUND({col:total}/{col:people},2),"")', 12),
    CA('funding', 'Money coded to program', 'money', 'SUMIFS({range:program_months.funding},{range:program_months.program},{col:program},{range:program_months.month},{col:month})', 12),
    CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), CPH('treas_phone', 'Finance committee phone', D.TREAS_PHONE), ORG()], D.program_cost_d(), 200))
# 11 cost per participant by quarter --------------------------------------------
def CQ(col): return 'SUMIFS({range:program_cost.%s},{range:program_cost.program},{col:program},{range:program_cost.month},">="&{col:quarter_start},{range:program_cost.month},"<="&{col:quarter_end})' % col
tables.append(T('cpp_quarter', 'Cost per Participant by Quarter', 'Cost per participant of each program for each quarter',
    'One row per program and quarter: cost, unique people and cost per participant at a full quarter pace, with the same quarter last year and a verdict (rising, steady, falling).', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('quarter_start', 'Quarter starts', 'date', 12), LST('program', 'Program', 'program', 22),
    CA('quarter_end', 'Quarter ends', 'date', 'EDATE({col:quarter_start},3)-1', 11), CA('elapsed', 'Share of the quarter passed', 'pct', 'MIN(1,MAX(0,({today}-{col:quarter_start}+1)/({col:quarter_end}-{col:quarter_start}+1)))', 9),
    CA('direct_cost', 'Direct cost', 'money', CQ('direct_cost'), 12), CA('shared_cost', 'Shared cost', 'money', CQ('shared_cost'), 12), CA('cost', 'Cost to date', 'money', CQ('total'), 12),
    CA('people', 'Unique people', 'int', 'COUNTIFS({range:participants.program},{col:program},{range:participants.start_date},"<="&{col:quarter_end},{range:participants.last_attended},">="&{col:quarter_start})', 9),
    CA('cost_pace', 'Cost at a full quarter pace', 'money', 'IF({col:elapsed}>0,ROUND({col:cost}/{col:elapsed},0),0)', 12),
    CA('cost_per_participant', 'Cost per participant', 'money', 'IF(AND({col:people}>0,{col:cost}>0),ROUND({col:cost_pace}/{col:people},2),"")', 12),
    CA('is_now', 'This quarter', 'int', 'IF({col:quarter_start}=%s,1,0)' % QSF, 7), CA('is_year_ago', 'This quarter last year', 'int', 'IF({col:quarter_start}=EDATE(%s,-12),1,0)' % QSF, 7),
    CA('last_year', 'Same quarter last year', 'money', 'IF(SUMIFS({range:cpp_quarter.cost_per_participant},{range:cpp_quarter.program},{col:program},{range:cpp_quarter.quarter_start},EDATE({col:quarter_start},-12))=0,"",SUMIFS({range:cpp_quarter.cost_per_participant},{range:cpp_quarter.program},{col:program},{range:cpp_quarter.quarter_start},EDATE({col:quarter_start},-12)))', 12),
    CA('change', 'Change on last year', 'pct', 'IF(AND(ISNUMBER({col:cost_per_participant}),ISNUMBER({col:last_year})),{col:cost_per_participant}/{col:last_year}-1,"")', 9),
    CA('verdict', 'Verdict', 'text', 'IF(ISNUMBER({col:change}),IF({col:change}>{set:change_margin},%s,IF({col:change}<-{set:change_margin},%s,%s)),%s)' % (c1('Rising'), c1('Falling'), c1('Steady'), c1('Nothing to compare')), 14),
    CPH('pm_phone', 'Program manager phone', D.PM_PHONE), CPH('ed_phone', 'Executive director phone', D.ED_PHONE), ORG()],
    D.cpp_quarter_d(), 60, [A('verdict', '= ' + c1('Rising'), 'warn'), A('verdict', '= ' + c1('Falling'), 'good')]))
# 12 outcomes -----------------------------------------------------------------------
tables.append(T('outcomes', 'Outcomes', 'Outcome counts each quarter against the target',
    'One row per outcome and quarter: the target and the actual count of a result for participants; the share of the target, the gap and a status fill in by themselves.', [
    C('outcome_id', 'Outcome ID', 'text', 10, required=True), C('quarter', 'Quarter starts', 'date', 12), LST('program', 'Program', 'program', 22), LST('outcome', 'Outcome', 'outcome', 28), C('target', 'Target', 'num', 9), C('actual', 'Actual', 'num', 9),
    CA('share', 'Share of target', 'pct', 'IF({col:target}>0,{col:actual}/{col:target},0)', 9), CA('gap', 'Over or behind', 'num', '{col:actual}-{col:target}', 9), CA('met', 'Target met', 'int', 'IF({col:actual}>={col:target},1,0)', 7),
    CA('status', 'Status', 'text', 'IF({col:actual}>={col:target},%s,%s)' % (c1('On target'), c1('Behind target')), 14), CPH('pm_phone', 'Program manager phone', D.PM_PHONE), ORG()],
    D.outcomes_d(), 300, [A('status', '= ' + c1('Behind target'), 'warn'), A('status', '= ' + c1('On target'), 'good')]))
# 13 outcome definitions --------------------------------------------------------------
tables.append(T('outcome_defs', 'Outcome Definitions', 'Each outcome with its unit and its target for the year',
    'One row per outcome: the unit you count and the target for the year; the count so far this year, the share met and the number needed each month fill in from the Outcomes sheet.', [
    C('def_id', 'Definition ID', 'text', 10, required=True), LST('program', 'Program', 'program', 22), LST('outcome', 'Outcome', 'outcome', 28), C('unit', 'Unit', 'text', 12), C('target_year', 'Target for the year', 'num', 11),
    CA('ytd_actual', 'Counted this year', 'num', 'SUMIFS({range:outcomes.actual},{range:outcomes.program},{col:program},{range:outcomes.outcome},{col:outcome},{range:outcomes.quarter},">="&%s)' % YS, 10),
    CA('share_met', 'Share of the year target', 'pct', 'IF({col:target_year}>0,{col:ytd_actual}/{col:target_year},0)', 10), CA('gap', 'Still to count', 'num', 'MAX(0,{col:target_year}-{col:ytd_actual})', 10),
    CA('months_left', 'Months left this year', 'num', 'ROUND((DATE(YEAR({today}),12,31)-{today})/30.4375,1)', 9),
    CA('need_month', 'Needed each month', 'num', 'IF({col:months_left}>0,ROUNDUP({col:gap}/{col:months_left},0),{col:gap})', 9),
    CA('status', 'Status', 'text', 'IF({col:gap}=0,%s,%s)' % (c1('On target'), c1('Behind target')), 14), ORG()], D.outcome_defs_d(), 50, [A('status', '= ' + c1('Behind target'), 'warn')]))
# 14 report numbers -----------------------------------------------------------------------
TY, LYP, L12, TQ = tok('rperiod', 'This year'), tok('rperiod', 'Last year'), tok('rperiod', 'Last 12 months'), tok('rperiod', 'This quarter')
def RM(col): return 'SUMIFS({range:program_months.%s},{range:program_months.program},{col:program},{range:program_months.month},">="&{col:from_m},{range:program_months.month},"<="&{col:to_d})' % col
FQ = 'DATE(YEAR({col:from_m}),3*INT((MONTH({col:from_m})-1)/3)+1,1)'
OCR = '{range:outcomes.program},{col:program},{range:outcomes.quarter},">="&%s,{range:outcomes.quarter},"<="&{col:to_d}' % FQ
tables.append(T('report_numbers', 'Report Numbers', 'Numbers a funder report asks for, by program and period',
    'One row per program and period: people served, visits, outcomes, cost per participant, volunteer hours and their value, the funding gap and a ready sentence for a funder report.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('program', 'Program', 'program', 22), LST('period', 'Period', 'rperiod', 15),
    CA('from_m', 'First month', 'date', 'IF({col:period}=%s,%s,IF({col:period}=%s,DATE(YEAR({today})-1,1,1),IF({col:period}=%s,EDATE(%s,-11),IF({col:period}=%s,%s,EDATE(%s,-3)))))' % (TY, YS, LYP, L12, MS, TQ, QSF, QSF), 11),
    CA('from_d', 'From', 'date', 'IF({col:period}=%s,EDATE({today},-12)+1,{col:from_m})' % L12, 11),
    CA('to_d', 'To', 'date', 'IF({col:period}=%s,DATE(YEAR({today})-1,12,31),IF({col:period}=%s,%s-1,{today}))' % (LYP, tok('rperiod', 'Last quarter'), QSF), 11),
    CA('people', 'People served', 'int', 'COUNTIFS({range:participants.program},{col:program},{range:participants.start_date},"<="&{col:to_d},{range:participants.last_attended},">="&{col:from_d})', 9),
    CA('visits', 'Visits', 'int', RM('visits'), 9), CA('sessions', 'Sessions', 'int', RM('sessions'), 9),
    CA('outcomes_n', 'Outcomes counted', 'int', 'COUNTIFS(%s)' % OCR, 9), CA('outcomes_met', 'Outcomes met', 'int', 'COUNTIFS(%s,{range:outcomes.met},1)' % OCR, 9),
    CA('outcome_share', 'Share of outcome target', 'pct', 'IFERROR(SUMIFS({range:outcomes.actual},%s)/SUMIFS({range:outcomes.target},%s),0)' % (OCR, OCR), 9),
    CA('cost', 'Program cost', 'money', 'SUMIFS({range:program_cost.total},{range:program_cost.program},{col:program},{range:program_cost.month},">="&{col:from_m},{range:program_cost.month},"<="&{col:to_d})', 12),
    CA('cost_per_participant', 'Cost per participant', 'money', 'IF(AND({col:people}>0,{col:cost}>0),ROUND({col:cost}/{col:people},2),"")', 12),
    CA('vol_hours', 'Volunteer hours', 'num', RM('vol_hours'), 10), CA('hours_value', 'Value of volunteer hours', 'money', 'ROUND({col:vol_hours}*{set:volunteer_hour_value},0)', 12),
    CA('funding', 'Money coded to program', 'money', RM('funding'), 12), CA('gap', 'Funding gap', 'money', 'MAX(0,{col:cost}-{col:funding})', 12), CA('gap_flag', 'Has a gap', 'int', 'IF({col:gap}>0,1,0)', 7),
    CA('key', 'Key', 'text', '{col:program}&"|"&{col:period}', 22),
    CA('sentence', 'Sentence for a funder report', 'text', '{col:program}&" "&%s&" "&{col:people}&" "&%s&" "&{col:visits}&" "&%s&" "&{col:sessions}&" "&%s&" "&IF(ISNUMBER({col:cost_per_participant}),ROUND({col:cost_per_participant},0),0)&" "&%s&" "&ROUND({col:vol_hours},0)&" "&%s' % (sw('served'), sw('people with'), sw('visits in'), sw('sessions, at a cost of'), sw('per participant, with'), sw('volunteer hours')), 60),
    CA('missing_item', 'Missing item', 'text', 'IF({col:people}=0,%s,IF({col:visits}=0,%s,IF({col:sessions}=0,%s,IF({col:outcomes_n}=0,%s,IF({col:cost}=0,%s,IF({col:vol_hours}=0,%s,%s))))))' % (c3('people served'), c3('visits'), c3('sessions'), c3('outcomes'), c3('cost'), c3('volunteer hours'), c2('Nothing missing')), 16),
    CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('dm_phone', 'Development manager phone', D.DM_PHONE), CPH('po_phone', 'Funder phone', D.PO_PHONE), ORG()], D.report_numbers_d(), 60))
# 15 capacity --------------------------------------------------------------------------
tables.append(T('capacity', 'Capacity by Program', 'Enrolled and waiting people of each program',
    'One row per program: the active participants enrolled and the people waiting, counted from the Participants sheet; set against capacity on the Programs sheet.', [
    LST('program', 'Program', 'sprogram', 24, required=True),
    CA('enrolled', 'Enrolled', 'int', 'COUNTIFS({range:participants.program},{col:program},{range:participants.status},%s)' % ACTV, 10),
    CA('waiting', 'Waiting', 'int', 'COUNTIFS({range:participants.program},{col:program},{range:participants.status},%s)' % WAITG, 10)], [dict(program=key('sprogram', p)) for p in SPROGRAMS], 50))
# 16 waiting list -----------------------------------------------------------------------
tables.append(T('waiting', 'Waiting List', 'People waiting for a place, longest first',
    'One row per person waiting: since when, the date to reply by and the date a place is held; the name, phone, program, weeks waiting, place in the queue and whether to offer a place fill in.', [
    C('participant_id', 'Participant ID', 'text', 11, required=True), C('waiting_since', 'Waiting since', 'date', 11), C('reply_by', 'Reply by', 'date', 11), C('hold_until', 'Place held until', 'date', 11),
    CA('name', 'Name', 'text', LKT('participants.name', 'participants.participant_id', 'participant_id'), 22), CA('phone', 'Phone', 'text', LKT('participants.phone', 'participants.participant_id', 'participant_id'), 18),
    CA('program', 'Program', 'text', LKT('participants.program', 'participants.participant_id', 'participant_id'), 22), CA('weeks_waiting', 'Weeks waiting', 'int', 'INT(({today}-{col:waiting_since})/7)', 8),
    CA('position', 'Place in the queue', 'int', 'COUNTIFS({range:waiting.program},{col:program},{range:waiting.waiting_since},"<"&{col:waiting_since})+1', 8),
    CA('free_places', 'Free places', 'int', 'IFERROR(MAX(0,INDEX({range:programs.capacity},MATCH({col:program},{range:programs.program},0))-INDEX({range:capacity.enrolled},MATCH({col:program},{range:capacity.program},0))),0)', 8),
    CA('offer', 'Offer', 'text', 'IF({col:position}<={col:free_places},%s,%s)' % (c1('Offer a place'), c1('Keep waiting')), 14), CPH('asst_phone', 'Program assistant phone', D.ASST_PHONE), ORG()],
    D.waiting_d(), 100, [A('offer', '= ' + c1('Offer a place'), 'good')]))
# 17 clear time ----------------------------------------------------------------------------
PRG = lambda col, kc='programs.program': 'IFERROR(INDEX({range:%s},MATCH({col:program},{range:%s},0)),0)' % (col, kc)
tables.append(T('clear_time', 'Clear Time by Program', 'Weeks until each waiting list clears at three paces',
    'One row per program and pace: people waiting, free places, places freed a week (people who completed or left in 12 weeks) and weeks to clear, with a verdict.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('program', 'Program', 'program', 22), LST('pace', 'Pace', 'pace', 20),
    CA('capacity', 'Capacity', 'int', PRG('programs.capacity'), 9), CA('enrolled', 'Enrolled', 'int', PRG('capacity.enrolled', 'capacity.program'), 9), CA('waiting', 'Waiting', 'int', PRG('capacity.waiting', 'capacity.program'), 9),
    CA('free_places', 'Free places', 'int', 'MAX(0,{col:capacity}-{col:enrolled})', 9), CA('still', 'Waiting after free places', 'int', 'MAX(0,{col:waiting}-{col:free_places})', 9),
    CA('freed_week', 'Places freed a week, usual', 'num', 'ROUND((COUNTIFS({range:participants.program},{col:program},{range:participants.status},%s,{range:participants.last_attended},">="&({today}-84))+COUNTIFS({range:participants.program},{col:program},{range:participants.status},%s,{range:participants.last_attended},">="&({today}-84)))/12,2)' % (COMP, LEFT), 10),
    CA('places_week', 'Places freed a week at this pace', 'num', 'ROUND({col:freed_week}*IF({col:pace}=%s,0.5,IF({col:pace}=%s,1,1.5)),2)' % (tok('pace', 'Half your usual pace'), tok('pace', 'Your usual pace')), 10),
    CA('weeks_to_clear', 'Weeks to clear', 'int', 'IF({col:still}=0,0,IF({col:places_week}>0,ROUNDUP({col:still}/{col:places_week},0),""))', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:still}=0,%s,IF(AND(ISNUMBER({col:weeks_to_clear}),{col:weeks_to_clear}<={set:waiting_target_weeks}),%s,%s))' % (c1('Room free'), c1('Hold'), c1('Add a session')), 14),
    CA('weeks_usual', 'Weeks to clear at your usual pace', 'int', 'IF({col:pace}=%s,IF(ISNUMBER({col:weeks_to_clear}),{col:weeks_to_clear},0),0)' % tok('pace', 'Your usual pace'), 9),
    CA('to_offer', 'Places to offer now', 'int', 'MIN({col:waiting},{col:free_places})', 8), CPH('pm_phone', 'Program manager phone', D.PM_PHONE), CPH('asst_phone', 'Program assistant phone', D.ASST_PHONE), CPH('partner_phone', 'Partner phone', D.PARTNER_PHONE), ORG()],
    D.clear_time_d(), 50, [A('verdict', '= ' + c1('Add a session'), 'warn'), A('verdict', '= ' + c1('Room free'), 'good')]))
# 18 scenario cost per participant ---------------------------------------------------------
tables.append(T('scenario_cpp', 'Scenario Cost per Participant', 'What serving more with the same money does to the cost',
    'One row per program and step (10, 20 and 30 percent more people): cost and unique people of the last 12 months, and the cost per participant before and after, with the same money.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('program', 'Program', 'program', 22), C('serve_more', 'Serve more by', 'pct', 9),
    CA('cost12', 'Cost, last 12 months', 'money', 'SUMIFS({range:program_cost.total},{range:program_cost.program},{col:program},{range:program_cost.month},">="&EDATE(%s,-11))' % MS, 12),
    CA('people12', 'Unique people, last 12 months', 'int', 'COUNTIFS({range:participants.program},{col:program},{range:participants.start_date},"<="&{today},{range:participants.last_attended},">="&({today}-365))', 9),
    CA('cpp_now', 'Cost per participant now', 'money', 'IF({col:people12}>0,ROUND({col:cost12}/{col:people12},2),"")', 12),
    CA('people_after', 'People after', 'int', 'ROUND({col:people12}*(1+{col:serve_more}),0)', 9),
    CA('cpp_after', 'Cost per participant after', 'money', 'IF({col:people_after}>0,ROUND({col:cost12}/{col:people_after},2),"")', 12),
    CA('saving', 'Saving per participant', 'money', 'IF(ISNUMBER({col:cpp_now}),{col:cpp_now}-{col:cpp_after},"")', 11),
    CA('change', 'Change', 'pct', 'IF(ISNUMBER({col:cpp_now}),{col:cpp_after}/{col:cpp_now}-1,"")', 9), ORG()], D.scenario_d(), 50))
# 19 weekday attendance ------------------------------------------------------------------------
WDN = lambda: 'IF({col:weekday}=%s,1,IF({col:weekday}=%s,2,IF({col:weekday}=%s,3,IF({col:weekday}=%s,4,IF({col:weekday}=%s,5,IF({col:weekday}=%s,6,7))))))' % tuple(tok('wday', w) for w in WEEKDAYS[:6])
SW12 = '({range:sessions.program}={col:program})*(WEEKDAY({range:sessions.date},2)={col:wno})*({range:sessions.date}>={today}-365)'
tables.append(T('weekday_att', 'Attendance by Weekday', 'Sessions and attendees of each program by weekday',
    'One row per program and weekday: sessions in the last 12 months, average attendees and volunteers, the next date and the volunteers to ask for.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('program', 'Program', 'program', 22), LST('weekday', 'Weekday', 'wday', 12),
    CA('wno', 'Weekday number', 'int', WDN(), 8), CA('sessions', 'Sessions, last 12 months', 'int', 'SUMPRODUCT(%s)' % SW12, 9),
    CA('avg_att', 'Average attendees', 'num', 'IF({col:sessions}>0,ROUND(SUMPRODUCT(%s*{range:sessions.attendees})/{col:sessions},1),0)' % SW12, 9),
    CA('avg_vol', 'Average volunteers', 'num', 'IF({col:sessions}>0,ROUND(SUMPRODUCT(%s*{range:sessions.volunteers})/{col:sessions},1),0)' % SW12, 9),
    CA('pidx', 'Program number', 'int', 'IFERROR(MATCH({col:program},{range:programs.program},0),0)', 7), CA('plan_key', 'Plan key for the quietest weekday', 'int', 'IF({col:sessions}>=3,{col:pidx}*1000000+{col:sessions}*10+{col:wno},"")', 10),
    CA('next_date', 'Next date', 'date', '{today}+MOD({col:wno}-WEEKDAY({today},2),7)', 11), CA('vol_needed', 'Volunteers to ask for', 'int', 'ROUNDUP({col:avg_vol},0)', 8),
    CPH('vc_phone', 'Volunteer coordinator phone', D.VC_PHONE), ORG()], D.weekday_d(), 50))
# 20 staff hours ------------------------------------------------------------------------------------
tables.append(T('staff_hours', 'Program Staff Hours', 'Staff hours and cost on each program every month',
    'One row per month, staff member and program: the hours and cost of staff time on that program, summed from your staff time lines; the cost of one hour fills in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('staff', 'Staff member', 'staff', 18), LST('program', 'Program', 'program', 22), C('hours', 'Hours', 'num', 9), C('cost', 'Cost', 'money', 11),
    CA('rate', 'Cost of one hour', 'money', 'IF({col:hours}>0,ROUND({col:cost}/{col:hours},2),0)', 10), ORG()], D.staff_hours_d(), 700))
assert len(tables) == 20
