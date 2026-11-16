"""Nonprofit suite part 5: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np5_lists import *
import np5_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YS = 'DATE(YEAR({today}),1,1)'
QSF = 'DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+1,1)'
ACTV, WAITG, COMP, LEFT = tok('pstat', 'Active'), tok('pstat', 'Waiting'), tok('pstat', 'Completed'), tok('pstat', 'Left')
FP, FS = tok('function', 'Program'), tok('function', 'Shared')
UPTO = tok('cstat', 'Up to date')
def DT(d): return '=DATE(%d,%d,%d)' % (d.year, d.month, d.day)
def PGt(p): return '=' + tok('program', p)
def MD(x): return 'DATE(YEAR(%s),MONTH(%s),1)' % (x, x)
def SUMPM(col, p='{in:program}', m=None, extra=''):
    return 'SUMIFS(%s,%s,%s,%s,%s%s)' % (R('program_months', col), R('program_months', 'program'), p, R('program_months', 'month'), m, extra)
def PEOPLE(p, frm, to): return 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)' % (R('participants', 'program'), p, R('participants', 'start_date'), to, R('participants', 'last_attended'), frm)
def PCOST(col, p, frm, to): return 'SUMIFS(%s,%s,%s,%s,">="&%s,%s,"<="&%s)' % (R('program_cost', col), R('program_cost', 'program'), p, R('program_cost', 'month'), frm, R('program_cost', 'month'), to)
def DIV(a, b, d=0): return 'IF(%s>0,%s/%s,%s)' % (b, a, b, d)
def ISF(p): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('programs', 'capacity'), p, R('programs', 'program'))
def ENR(p): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('capacity', 'enrolled'), p, R('capacity', 'program'))
def WAIT(p): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('capacity', 'waiting'), p, R('capacity', 'program'))
tools = []

# 1 ------------------------------------------------------------ not-seen finder
NSC = '%s,%s,%s,">"&{in:days}' % (R('participants', 'status'), ACTV, R('participants', 'days_since'))
def NSN(k, col): return 'IFERROR(INDEX(%s,%d),"")' % (R('not_seen', col), k)
tools.append(TOOL('not_seen_tool', 'Not-seen Finder', 'Who do we call this week because they stopped coming',
    'Type how many days count as not seen and when to close a record; active participants who stopped coming are counted and the three with the most sessions before are named from the Not Seen List.', [
    I('days', 'Days without a visit that count as not seen', 14, 'int'), I('close', 'Days without a visit after which to close the record', 90, 'int')], [
    O('Active participants', 'int', 'COUNTIFS(%s,%s)' % (R('participants', 'status'), ACTV)), O('Not seen for more than the days', 'int', 'COUNTIFS(%s)' % NSC),
    O('Share of active participants', 'pct', 'IFERROR(COUNTIFS(%s)/COUNTIFS(%s,%s),0)' % (NSC, R('participants', 'status'), ACTV)),
    O('Of those, with a contact status to fix', 'int', 'COUNTIFS(%s,%s,"<>"&%s)' % (NSC, R('participants', 'contact_status'), UPTO)),
    O('Of those, with 5 or more sessions before', 'int', 'COUNTIFS(%s,%s,">=5")' % (NSC, R('participants', 'sessions'))),
    O('Of those, beyond the close days', 'int', 'COUNTIFS(%s,%s,%s,">"&{in:close})' % (R('participants', 'status'), ACTV, R('participants', 'days_since'))),
    O('First to call', 'text', NSN(1, 'name')), O('First to call, program', 'text', NSN(1, 'program')), O('First to call, days since', 'int', NSN(1, 'days_since')), O('First to call, sessions before', 'int', NSN(1, 'sessions')),
    O('Second to call', 'text', NSN(2, 'name')), O('Second to call, days since', 'int', NSN(2, 'days_since')), O('Third to call', 'text', NSN(3, 'name')), O('Third to call, days since', 'int', NSN(3, 'days_since')),
    O('Days the Not Seen List uses', 'int', '{set:not_seen_days}'),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,IF(IFERROR(%s>{in:close},FALSE),%s,%s))' % (NSC, c2('Nobody is missing'), NSN(1, 'days_since'), c1('Close the record'), c1('Call this week')))],
    GR('What if', ('Seven days', {'days': 7}), ('30 days', {'days': 30}), ('45 days', {'days': 45}), ('60 days', {'days': 60}), ('90 days', {'days': 90}), ('Close after 60 days', {'close': 60}))))

# 2 ------------------------------------------------------------ people served counter
MD1 = MD('{in:month}')
YEND, YBEG = 'DATE({in:year},12,31)', 'DATE({in:year},1,1)'
UQ = PEOPLE('{in:program}', YBEG, YEND); UQP = PEOPLE('{in:program}', 'DATE({in:year}-1,1,1)', 'DATE({in:year}-1,12,31)')
def VYR(y): return 'SUMIFS(%s,%s,{in:program},%s,">="&DATE(%s,1,1),%s,"<="&DATE(%s,12,1))' % (R('program_months', 'visits'), R('program_months', 'program'), R('program_months', 'month'), y, R('program_months', 'month'), y)
tools.append(TOOL('people_served', 'People Served Counter', 'How many people did a program serve, up or down',
    'Pick a program, a month and a year; people and visits are counted for the month and for the year, with the year before, and the verdict says up, same or down.', [
    IL('program', 'Program', 'program', 'After-School Learning'), I('month', 'Month', iso(month_start(1)), 'date'), I('year', 'Year', Y, 'int')], [
    O('People in the month', 'int', SUMPM('participants', m=MD1)), O('Visits in the month', 'int', SUMPM('visits', m=MD1)), O('New people in the month', 'int', SUMPM('new_participants', m=MD1)), O('Sessions in the month', 'int', SUMPM('sessions', m=MD1)),
    O('People in the same month last year', 'int', SUMPM('participants', m='EDATE(%s,-12)' % MD1)), O('Unique people in the year', 'int', UQ), O('Unique people the year before', 'int', UQP),
    O('Change on the year before', 'pct', 'IF(%s>0,%s/%s-1,0)' % (UQP, UQ, UQP)), O('Visits in the year', 'int', VYR('{in:year}')), O('Visits the year before', 'int', VYR('{in:year}-1')),
    O('All programs, people in the month', 'int', 'SUMIFS(%s,%s,%s)' % (R('program_months', 'participants'), R('program_months', 'month'), MD1)),
    O('All programs, unique people in the year', 'int', 'COUNTIFS(%s,"<="&%s,%s,">="&%s)' % (R('participants', 'start_date'), YEND, R('participants', 'last_attended'), YBEG)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s/%s-1>{set:change_margin},%s,IF(%s/%s-1<-{set:change_margin},%s,%s)))' % (UQP, c1('Nothing to compare'), UQ, UQP, c1('Up'), UQ, UQP, c1('Down'), c1('Same')))],
    GR('What if', ('Family Food Pantry', {'program': PGt('Family Food Pantry')}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('Summer Youth Camp', {'program': PGt('Summer Youth Camp')}), ('Last year', {'year': Y - 1}), ('Two years ago', {'year': Y - 2}))))

# 3 ------------------------------------------------------------ program month report
PMX = SUMPM('participants', m=MD1)
tools.append(TOOL('month_report', 'Program Month Report', 'Is a program full, healthy or quiet this month',
    'Pick a program and a month; people, visits, sessions, capacity used, volunteer hours and the average attendees are shown with the change on the month before.', [
    IL('program', 'Program', 'program', 'After-School Learning'), I('month', 'Month', iso(month_start(0)), 'date')], [
    O('People', 'int', PMX), O('Visits', 'int', SUMPM('visits', m=MD1)), O('New people', 'int', SUMPM('new_participants', m=MD1)), O('Sessions', 'int', SUMPM('sessions', m=MD1)),
    O('Capacity', 'int', SUMPM('capacity', m=MD1)), O('Capacity used', 'pct', 'IFERROR(%s/%s,0)' % (PMX, SUMPM('capacity', m=MD1))), O('Free places', 'int', 'MAX(0,%s-%s)' % (SUMPM('capacity', m=MD1), PMX)), O('Waiting', 'int', SUMPM('waiting', m=MD1)),
    O('Volunteer hours', 'num', SUMPM('vol_hours', m=MD1)), O('Value of volunteer hours', 'money', 'ROUND(%s*{set:volunteer_hour_value},0)' % SUMPM('vol_hours', m=MD1)),
    O('Average attendees a session', 'num', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,{in:program},%s,%s),1),0)' % (R('sessions', 'attendees'), R('sessions', 'program'), R('sessions', 'month'), MD1)),
    O('Visits per person', 'num', 'IF(%s>0,ROUND(%s/%s,1),0)' % (PMX, SUMPM('visits', m=MD1), PMX)), O('People the month before', 'int', SUMPM('participants', m='EDATE(%s,-1)' % MD1)),
    O('Change on the month before', 'pct', 'IF(%s>0,%s/%s-1,0)' % (SUMPM('participants', m='EDATE(%s,-1)' % MD1), PMX, SUMPM('participants', m='EDATE(%s,-1)' % MD1))),
    O('Verdict', 'text', 'IF(AND(%s=0,%s=0),%s,IF(IFERROR(%s/%s,0)>={set:full_share},%s,IF(IFERROR(%s/%s,0)<{set:quiet_share},%s,%s)))' % (PMX, SUMPM('sessions', m=MD1), c1('Off season'), PMX, SUMPM('capacity', m=MD1), c1('Full'), PMX, SUMPM('capacity', m=MD1), c1('Quiet'), c1('Healthy')))],
    GR('What if', ('Last month', {'month': DT(month_start(1))}), ('Two months ago', {'month': DT(month_start(2))}), ('Family Food Pantry', {'program': PGt('Family Food Pantry')}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}),
       ('Summer Youth Camp', {'program': PGt('Summer Youth Camp')}))))

# 4 ------------------------------------------------------------ cost per participant
QEN = 'EDATE({in:quarter},3)-1'
def QEL(q): return 'MIN(1,MAX(0,({today}-%s+1)/(EDATE(%s,3)-%s)))' % (q, q, q)
def QC(col, q): return PCOST(col, '{in:program}', q, 'EDATE(%s,3)-1' % q)
def QP(q): return PEOPLE('{in:program}', q, 'EDATE(%s,3)-1' % q)
QLY = 'EDATE({in:quarter},-12)'
CPP1 = 'IF(AND(%s>0,%s>0),%s/%s/%s,0)' % (QP('{in:quarter}'), QEL('{in:quarter}'), QC('total', '{in:quarter}'), QEL('{in:quarter}'), QP('{in:quarter}'))
CPP0 = 'IF(%s>0,%s/%s,0)' % (QP(QLY), QC('total', QLY), QP(QLY))
tools.append(TOOL('cost_per_participant', 'Cost per Participant', 'Is the cost of serving one person rising or falling',
    'Pick a program and the first day of a quarter; direct plus shared cost is divided by the unique people, set against the same quarter last year, and the verdict says rising, steady or falling.', [
    IL('program', 'Program', 'program', 'After-School Learning'), I('quarter', 'Quarter starts', iso(add_months(D.QS0, -3)), 'date')], [
    O('Direct cost', 'money', QC('direct_cost', '{in:quarter}')), O('Shared cost', 'money', QC('shared_cost', '{in:quarter}')), O('Total cost to date', 'money', QC('total', '{in:quarter}')),
    O('Share of the quarter passed', 'pct', QEL('{in:quarter}')), O('Unique people', 'int', QP('{in:quarter}')), O('Cost per participant at a full quarter pace', 'money', 'ROUND(%s,2)' % CPP1),
    O('Same quarter last year, total cost', 'money', QC('total', QLY)), O('Same quarter last year, unique people', 'int', QP(QLY)), O('Same quarter last year, cost per participant', 'money', 'ROUND(%s,2)' % CPP0),
    O('Change on last year', 'pct', 'IF(%s>0,%s/%s-1,0)' % (CPP0, CPP1, CPP0)), O('Direct share of the cost', 'pct', 'IFERROR(%s/%s,0)' % (QC('direct_cost', '{in:quarter}'), QC('total', '{in:quarter}'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s/%s-1>{set:change_margin},%s,IF(%s/%s-1<-{set:change_margin},%s,%s)))' % (CPP0, c1('Nothing to compare'), CPP1, CPP0, c1('Rising'), CPP1, CPP0, c1('Falling'), c1('Steady')))],
    GR('What if', ('Family Food Pantry', {'program': PGt('Family Food Pantry')}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('A quarter earlier', {'quarter': DT(add_months(D.QS0, -6))}), ('This quarter so far', {'quarter': DT(D.QS0)}))))

# 5 ------------------------------------------------------------ cost allocation viewer
EXA = '%s,{in:category},%s,%s,%s,%s' % (R('expenses', 'category'), R('expenses', 'month'), MD('{in:month}'), R('expenses', 'function'), FS)
def EXS(col): return 'SUMIFS(%s,%s)' % (R('expenses', col), EXA)
def ALR(col): return 'IFERROR(INDEX(%s,MATCH({in:category},%s,0)),0)' % (R('alloc', col), R('alloc', 'category'))
def DSH(p): return 'IFERROR(SUMIFS(%s,%s,%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (R('program_cost', 'direct_cost'), R('program_cost', 'program'), tok('program', p), R('program_cost', 'month'), MD('{in:month}'), R('program_cost', 'direct_cost'), R('program_cost', 'month'), MD('{in:month}'))
tools.append(TOOL('alloc_viewer', 'Cost Allocation Viewer', 'How is a shared cost split between programs',
    'Pick an expense category and a month; the shared cost, its rule and the parts for programs, management and fundraising are shown, and each program\'s part.', [
    IL('category', 'Expense category', 'category', 'Rent and utilities'), I('month', 'Month', iso(month_start(1)), 'date')], [
    O('Shared cost in the month', 'money', EXS('amount')), O('Rule', 'text', 'IFERROR(INDEX(%s,MATCH({in:category},%s,0))&"","")' % (R('alloc', 'rule'), R('alloc', 'category'))),
    O('Program share', 'pct', ALR('program_share')), O('Management share', 'pct', ALR('management_share')), O('Fundraising share', 'pct', ALR('fundraising_share')),
    O('Part for programs', 'money', EXS('to_program')), O('Part for management', 'money', EXS('to_management')), O('Part for fundraising', 'money', EXS('to_fundraising')),
    O('After-School Learning carries', 'money', 'ROUND(%s*%s,2)' % (EXS('to_program'), DSH('After-School Learning'))), O('Family Food Pantry carries', 'money', 'ROUND(%s*%s,2)' % (EXS('to_program'), DSH('Family Food Pantry'))),
    O('Senior Meals and Visits carries', 'money', 'ROUND(%s*%s,2)' % (EXS('to_program'), DSH('Senior Meals and Visits'))), O('Summer Youth Camp carries', 'money', 'ROUND(%s*%s,2)' % (EXS('to_program'), DSH('Summer Youth Camp'))),
    O('Parts less the shared cost', 'money', 'ROUND(%s+%s+%s-%s,2)' % (EXS('to_program'), EXS('to_management'), EXS('to_fundraising'), EXS('amount'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&ROUND(%s,0))' % (EXS('amount'), c2('No shared cost that month'), c2('Rule applied to'), EXS('amount')))],
    GR('What if', ('Insurance', {'category': '=' + tok('category', 'Insurance')}), ('Marketing and comms', {'category': '=' + tok('category', 'Marketing and comms')}), ('Technology and phones', {'category': '=' + tok('category', 'Technology and phones')}),
       ('Training and volunteers', {'category': '=' + tok('category', 'Training and volunteers')}), ('Two months ago', {'month': DT(month_start(2))}))))

# 6 ------------------------------------------------------------ serve-more scenario
COST12 = 'SUMIFS(%s,%s,{in:program},%s,">="&EDATE(%s,-11))' % (R('program_cost', 'total'), R('program_cost', 'program'), R('program_cost', 'month'), MS)
PPL12 = PEOPLE('{in:program}', '{today}-365', '{today}')
CNOW = 'IF(%s>0,%s/%s,0)' % (PPL12, COST12, PPL12)
ADD = 'ROUND(%s*{in:more},0)' % PPL12
CAFT = 'IF(%s>0,(%s+%s*{in:extra})/(%s+%s),0)' % (PPL12, COST12, ADD, PPL12, ADD)
FREEP = 'MAX(0,%s-%s)' % (ISF('{in:program}'), ENR('{in:program}'))
tools.append(TOOL('serve_more', 'Serve-more Scenario', 'What happens to cost per participant if we serve more people',
    'Pick a program, how many more people you want to serve and any extra cost for each added person; with the same money, cost per participant falls, and the free places show whether they fit.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), I('more', 'Serve more by', 0.20, 'pct'), I('extra', 'Extra cost for each added person', 0, 'money')], [
    O('Cost, last 12 months', 'money', COST12), O('Unique people, last 12 months', 'int', PPL12), O('Cost per participant now', 'money', 'ROUND(%s,2)' % CNOW), O('People added', 'int', ADD), O('People after', 'int', '%s+%s' % (PPL12, ADD)),
    O('Cost after, with the extra cost', 'money', '%s+%s*{in:extra}' % (COST12, ADD)), O('Cost per participant after', 'money', 'ROUND(%s,2)' % CAFT), O('Saving per participant', 'money', 'ROUND(%s-%s,2)' % (CNOW, CAFT)),
    O('Change in cost per participant', 'pct', 'IF(%s>0,%s/%s-1,0)' % (CNOW, CAFT, CNOW)), O('Free places in the program now', 'int', FREEP), O('People added beyond the free places', 'int', 'MAX(0,%s-%s)' % (ADD, FREEP)),
    O('Verdict', 'text', 'IF(%s<%s,%s&" "&ROUND(%s,0),%s&" "&ROUND(%s,0))' % (CAFT, CNOW, c2('Cost per participant falls to'), CAFT, c2('Cost per participant is'), CAFT))],
    GR('What if', ('5 percent more', {'more': 0.05}), ('10 percent more', {'more': 0.10}), ('30 percent more', {'more': 0.30}), ('20 percent more, 40 extra each', {'more': 0.20, 'extra': 40}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('After-School Learning', {'program': PGt('After-School Learning')}))))

# 7 ------------------------------------------------------------ funder sentence writer
def RN(col): return 'IFERROR(INDEX(%s,MATCH({in:program}&"|"&{in:period},%s,0)),"")' % (R('report_numbers', col), R('report_numbers', 'key'))
tools.append(TOOL('sentence_writer', 'Funder Sentence Writer', 'What one plain sentence tells a funder what we did',
    'Pick a program and a period; people served, visits, sessions, cost per participant and volunteer hours are written into one sentence for a funder report, with a check for anything missing.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), IL('period', 'Period', 'rperiod', 'Last 12 months')], [
    O('Sentence', 'text', RN('sentence')), O('People served', 'int', RN('people')), O('Cost per participant', 'money', RN('cost_per_participant')), O('Volunteer hours', 'num', RN('vol_hours')), O('Value of volunteer hours, your setting', 'money', RN('hours_value')),
    O('Outcomes met', 'int', RN('outcomes_met')), O('First missing item', 'text', RN('missing_item')),
    O('Verdict', 'text', 'IF(%s=%s,%s,%s&" "&%s)' % (RN('missing_item'), c2('Nothing missing'), c2('Sentence ready, check the numbers'), c2('Missing'), RN('missing_item')))],
    GR('What if', ('After-School Learning', {'program': PGt('After-School Learning')}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('Summer Youth Camp', {'program': PGt('Summer Youth Camp')}), ('This year', {'period': '=' + tok('rperiod', 'This year')}), ('Last year', {'period': '=' + tok('rperiod', 'Last year')}))))

# 8 ------------------------------------------------------------ program funding gap
def FMON(col): return 'SUMIFS(%s,%s,{in:program},%s,">="&EDATE(%s,1-{in:months}))' % (R('program_cost', col), R('program_cost', 'program'), R('program_cost', 'month'), MS)
FUNDM = 'SUMIFS(%s,%s,{in:program},%s,">="&EDATE(%s,1-{in:months}))' % (R('program_months', 'funding'), R('program_months', 'program'), R('program_months', 'month'), MS)
GAP = '(%s-%s-{in:new_money})' % (FMON('total'), FUNDM)
tools.append(TOOL('funding_gap', 'Program Funding Gap', 'Is a program paid for by the money coded to it',
    'Pick a program and a number of months; the program cost is set against the money coded to its funds, and new money you expect is taken off the gap.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), I('months', 'Months to look at', 12, 'int'), I('new_money', 'New money you expect for the program', 0, 'money')], [
    O('Direct cost', 'money', FMON('direct_cost')), O('Shared cost', 'money', FMON('shared_cost')), O('Total program cost', 'money', FMON('total')), O('Money coded to the program', 'money', FUNDM),
    O('Share of the cost covered', 'pct', 'IFERROR(%s/%s,0)' % (FUNDM, FMON('total'))), O('Gap before new money', 'money', 'MAX(0,%s-%s)' % (FMON('total'), FUNDM)), O('Gap after new money', 'money', 'MAX(0,%s)' % GAP),
    O('Gap a month, to find from other money', 'money', 'ROUND(MAX(0,%s)/{in:months},0)' % GAP), O('Cost per month', 'money', 'ROUND(%s/{in:months},0)' % FMON('total')),
    O('Verdict', 'text', 'IF(%s<=0,%s,%s&" "&ROUND(%s,0))' % (GAP, c1('Funded'), c2('Short by'), GAP))],
    GR('What if', ('Six months', {'months': 6}), ('Three months', {'months': 3}), ('Two years', {'months': 24}), ('20,000 of new money', {'new_money': 20000}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('After-School Learning', {'program': PGt('After-School Learning')}))))

# 9 ------------------------------------------------------------ cost trend forecast
def CQV(k): return 'SUMIFS(%s,%s,{in:program},%s,EDATE(%s,%d))' % (R('cpp_quarter', 'cost_per_participant'), R('cpp_quarter', 'program'), R('cpp_quarter', 'quarter_start'), QSF, -3 * k)
TREND = '(%s-%s)/4' % (CQV(0), CQV(4))
FCST = '(%s+{in:weight}*%s)' % (CQV(0), TREND)
tools.append(TOOL('cost_trend', 'Cost Trend Forecast', 'What will one participant cost next quarter',
    'Pick a program and how much of the trend to follow; five quarters give an average change, a forecast for next quarter and a best and worst band, your estimate.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), I('weight', 'How much of the trend to follow, 1 is all', 1, 'num'), I('band', 'Band around the forecast', 0.10, 'pct')], [
    O('Cost per participant, a year ago', 'money', CQV(4)), O('Cost per participant, three quarters ago', 'money', CQV(3)), O('Cost per participant, two quarters ago', 'money', CQV(2)), O('Cost per participant, last quarter', 'money', CQV(1)),
    O('Cost per participant, this quarter at a full pace', 'money', CQV(0)), O('Average change a quarter', 'money', 'ROUND(%s,2)' % TREND), O('Forecast for next quarter', 'money', 'ROUND(%s,2)' % FCST),
    O('Best case', 'money', 'ROUND(%s*(1-{in:band}),2)' % FCST), O('Worst case', 'money', 'ROUND(%s*(1+{in:band}),2)' % FCST), O('Forecast against this quarter', 'pct', 'IF(%s>0,%s/%s-1,0)' % (CQV(0), FCST, CQV(0))),
    O('Verdict', 'text', 'IF(OR(%s=0,%s=0),%s,%s&" "&ROUND(%s,0))' % (CQV(0), CQV(4), c2('No forecast yet'), c2('Expect next quarter, your estimate'), FCST))],
    GR('What if', ('Half the trend', {'weight': 0.5}), ('No trend, flat', {'weight': 0}), ('Twice the trend', {'weight': 2}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('After-School Learning', {'program': PGt('After-School Learning')}), ('Band of 20 percent', {'band': 0.20}))))

# 10 ----------------------------------------------------------- outcome tracker
OCQ = '%s,{in:program},%s,{in:outcome},%s,{in:quarter}' % (R('outcomes', 'program'), R('outcomes', 'outcome'), R('outcomes', 'quarter'))
OCL = '%s,{in:program},%s,{in:outcome},%s,EDATE({in:quarter},-12)' % (R('outcomes', 'program'), R('outcomes', 'outcome'), R('outcomes', 'quarter'))
OCT = 'SUMIFS(%s,%s)' % (R('outcomes', 'target'), OCQ); OCA = 'SUMIFS(%s,%s)' % (R('outcomes', 'actual'), OCQ)
tools.append(TOOL('outcome_tracker', 'Outcome Tracker', 'Is an outcome on target this quarter',
    'Pick a program, an outcome of that program and a quarter start; the count of the result is set against the target, with the same quarter last year and the last four quarters.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), IL('outcome', 'Outcome', 'outcome', 'Households served'), I('quarter', 'Quarter starts', iso(D.QS0), 'date')], [
    O('Target', 'num', OCT), O('Actual', 'num', OCA), O('Share of the target', 'pct', 'IF(%s>0,%s/%s,0)' % (OCT, OCA, OCT)), O('Over or behind', 'num', '%s-%s' % (OCA, OCT)),
    O('Same quarter last year, actual', 'num', 'SUMIFS(%s,%s)' % (R('outcomes', 'actual'), OCL)), O('Change on last year', 'pct', 'IF(SUMIFS(%s,%s)>0,%s/SUMIFS(%s,%s)-1,0)' % (R('outcomes', 'actual'), OCL, OCA, R('outcomes', 'actual'), OCL)),
    O('Last four quarters behind target', 'int', 'COUNTIFS(%s,{in:program},%s,{in:outcome},%s,">="&EDATE({in:quarter},-9),%s,"<="&{in:quarter},%s,0)' % (R('outcomes', 'program'), R('outcomes', 'outcome'), R('outcomes', 'quarter'), R('outcomes', 'quarter'), R('outcomes', 'met'))),
    O('Target for the year', 'num', 'SUMIFS(%s,%s,{in:program},%s,{in:outcome})' % (R('outcome_defs', 'target_year'), R('outcome_defs', 'program'), R('outcome_defs', 'outcome'))),
    O('Counted this year', 'num', 'SUMIFS(%s,%s,{in:program},%s,{in:outcome})' % (R('outcome_defs', 'ytd_actual'), R('outcome_defs', 'program'), R('outcome_defs', 'outcome'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,IF(%s>=%s,%s,%s&" "&ROUND(%s-%s,0)))' % (OCQ, c2('Outcome not found'), OCA, OCT, c1('On target'), c2('Behind by'), OCT, OCA))],
    GR('What if', ('Last quarter', {'quarter': DT(add_months(D.QS0, -3))}), ('A year ago', {'quarter': DT(add_months(D.QS0, -12))}), ('Fresh produce boxes given', {'outcome': '=' + tok('outcome', 'Fresh produce boxes given')}),
       ('Returned within 60 days', {'outcome': '=' + tok('outcome', 'Returned within 60 days')}), ('Referred to another service', {'outcome': '=' + tok('outcome', 'Referred to another service')}))))

# 11 ----------------------------------------------------------- outcome gap solver
DEFA = lambda col: 'SUMIFS(%s,%s,{in:program},%s,{in:outcome})' % (R('outcome_defs', col), R('outcome_defs', 'program'), R('outcome_defs', 'outcome'))
MLEFT = 'ROUND((DATE(YEAR({today}),12,31)-{today})/30.4375,1)'
MPASS = 'MAX(1,(%s-%s)/30.4375)' % ('{today}', YS)
GAPN = 'MAX(0,%s-%s-{in:add_now})' % (DEFA('target_year'), DEFA('ytd_actual'))
NEEDM = 'IF(%s>0,ROUNDUP(%s/%s,0),%s)' % (MLEFT, GAPN, MLEFT, GAPN)
tools.append(TOOL('gap_solver', 'Outcome Gap Solver', 'How many a month to reach the yearly outcome target',
    'Pick a program and an outcome; the yearly target less what is counted so far, less any count you can add now, is divided by the months left, and the pace so far shows how hard that is.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), IL('outcome', 'Outcome', 'outcome', 'Households served'), I('add_now', 'Count you can add now', 0, 'num')], [
    O('Target for the year', 'num', DEFA('target_year')), O('Counted this year', 'num', DEFA('ytd_actual')), O('Share of the year target', 'pct', 'IF(%s>0,%s/%s,0)' % (DEFA('target_year'), DEFA('ytd_actual'), DEFA('target_year'))),
    O('Still to count', 'num', GAPN), O('Months left this year', 'num', MLEFT), O('Needed each month', 'num', NEEDM), O('Pace so far, a month', 'num', 'ROUND(%s/%s,1)' % (DEFA('ytd_actual'), MPASS)),
    O('Needed against the pace so far', 'pct', 'IFERROR(%s/(%s/%s),0)' % (NEEDM, DEFA('ytd_actual'), MPASS)), O('Share of the year passed', 'pct', 'MIN(1,%s/12)' % MPASS),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (GAPN, c2('Target reached'), c2('Needed each month'), NEEDM))],
    GR('What if', ('Add 5 now', {'add_now': 5}), ('Add 20 now', {'add_now': 20}), ('Returned within 60 days', {'outcome': '=' + tok('outcome', 'Returned within 60 days')}), ('Meals delivered', {'program': PGt('Senior Meals and Visits'), 'outcome': '=' + tok('outcome', 'Meals delivered')}),
       ('Finished the term', {'program': PGt('After-School Learning'), 'outcome': '=' + tok('outcome', 'Finished the term')}))))

# 12 ----------------------------------------------------------- outcome history comparison
def OCS(col, lo, hi): return 'SUMIFS(%s,%s,{in:program},%s,{in:outcome},%s,">="&%s,%s,"<="&%s)' % (R('outcomes', col), R('outcomes', 'program'), R('outcomes', 'outcome'), R('outcomes', 'quarter'), lo, R('outcomes', 'quarter'), hi)
TY_, LY_ = OCS('actual', YS, QSF), OCS('actual', 'EDATE(%s,-12)' % YS, 'EDATE(%s,-12)' % QSF)
TYT, LYT = OCS('target', YS, QSF), OCS('target', 'EDATE(%s,-12)' % YS, 'EDATE(%s,-12)' % QSF)
tools.append(TOOL('outcome_history', 'Outcome History Comparison', 'Is this year better than last year for an outcome',
    'Pick a program and an outcome; the count so far this year is set against the same quarters last year, with the share of the target for both, and the verdict says better, same or worse.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), IL('outcome', 'Outcome', 'outcome', 'Households served')], [
    O('Counted this year', 'num', TY_), O('Counted in the same quarters last year', 'num', LY_), O('Change', 'pct', 'IF(%s>0,%s/%s-1,0)' % (LY_, TY_, LY_)), O('Target this year so far', 'num', TYT), O('Target last year, same quarters', 'num', LYT),
    O('Share of target this year', 'pct', 'IF(%s>0,%s/%s,0)' % (TYT, TY_, TYT)), O('Share of target last year', 'pct', 'IF(%s>0,%s/%s,0)' % (LYT, LY_, LYT)),
    O('Quarters counted this year', 'int', 'COUNTIFS(%s,{in:program},%s,{in:outcome},%s,">="&%s)' % (R('outcomes', 'program'), R('outcomes', 'outcome'), R('outcomes', 'quarter'), YS)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s/%s-1>{set:change_margin},%s,IF(%s/%s-1<-{set:change_margin},%s,%s)))' % (LY_, c1('Nothing to compare'), TY_, LY_, c1('Better'), TY_, LY_, c1('Worse'), c1('Same')))],
    GR('What if', ('Fresh produce boxes given', {'outcome': '=' + tok('outcome', 'Fresh produce boxes given')}), ('Meals delivered', {'program': PGt('Senior Meals and Visits'), 'outcome': '=' + tok('outcome', 'Meals delivered')}),
       ('Finished the term', {'program': PGt('After-School Learning'), 'outcome': '=' + tok('outcome', 'Finished the term')}), ('Reading check passed', {'program': PGt('After-School Learning'), 'outcome': '=' + tok('outcome', 'Reading check passed')}))))

# 13 ----------------------------------------------------------- report numbers builder
MISS = RN('missing_item')
tools.append(TOOL('numbers_builder', 'Report Numbers Builder', 'Are all the numbers for a funder report in one place',
    'Pick a program and a period; people served, visits, outcomes, cost, volunteer hours and the funding gap come from the Report Numbers sheet, and the verdict says ready to paste or what is missing.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), IL('period', 'Period', 'rperiod', 'Last 12 months')], [
    O('From', 'date', RN('from_d')), O('To', 'date', RN('to_d')), O('People served', 'int', RN('people')), O('Visits', 'int', RN('visits')), O('Sessions', 'int', RN('sessions')), O('Outcomes counted', 'int', RN('outcomes_n')),
    O('Outcomes met', 'int', RN('outcomes_met')), O('Share of the outcome target', 'pct', RN('outcome_share')), O('Program cost', 'money', RN('cost')), O('Cost per participant', 'money', RN('cost_per_participant')),
    O('Volunteer hours', 'num', RN('vol_hours')), O('Value of volunteer hours, your setting', 'money', RN('hours_value')), O('Money coded to the program', 'money', RN('funding')), O('Funding gap', 'money', RN('gap')),
    O('Verdict', 'text', 'IF(%s=%s,%s,%s&" "&%s)' % (MISS, c2('Nothing missing'), c2('Ready to paste'), c2('Missing'), MISS))],
    GR('What if', ('After-School Learning', {'program': PGt('After-School Learning')}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('Summer Youth Camp', {'program': PGt('Summer Youth Camp')}), ('This quarter', {'period': '=' + tok('rperiod', 'This quarter')}), ('Last year', {'period': '=' + tok('rperiod', 'Last year')}))))

# 14 ----------------------------------------------------------- funder report checker
SESN = 'COUNTIFS(%s,{in:program},%s,">="&(%s))' % (R('sessions', 'program'), R('sessions', 'date'), RN('from_d'))
def MS_(need, val): return '{in:%s}*IF(%s>0,0,1)' % (need, val)
NEEDS = [('need_people', 'people served', RN('people')), ('need_visits', 'visits', RN('visits')), ('need_sessions', 'sessions', SESN), ('need_outcomes', 'outcomes', RN('outcomes_n')), ('need_cost', 'cost', RN('cost')), ('need_hours', 'volunteer hours', RN('vol_hours'))]
MISSN = '(' + '+'.join(MS_(n, v) for n, _, v in NEEDS) + ')'
FIRSTM = 'IF(%s,%s,IF(%s,%s,IF(%s,%s,IF(%s,%s,IF(%s,%s,%s)))))' % (tuple(x for (n, lab, v) in NEEDS[:5] for x in ('(' + MS_(n, v) + ')>0', c3(lab))) + (c3('volunteer hours'),))
tools.append(TOOL('funder_checker', 'Funder Report Checker', 'Does the workbook hold every number this funder asks for',
    'Pick a program and a period and type 1 for each number the funder asks for; each is checked against the numbers on file and the verdict says complete or what to add first.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), IL('period', 'Period', 'rperiod', 'This quarter'), I('need_people', 'Funder asks for people served, 1 or 0', 1, 'int'), I('need_visits', 'Funder asks for visits, 1 or 0', 1, 'int'),
    I('need_sessions', 'Funder asks for sessions, 1 or 0', 1, 'int'), I('need_outcomes', 'Funder asks for outcomes, 1 or 0', 1, 'int'), I('need_cost', 'Funder asks for cost, 1 or 0', 1, 'int'), I('need_hours', 'Funder asks for volunteer hours, 1 or 0', 1, 'int')], [
    O('People served on file', 'int', RN('people')), O('Visits on file', 'int', RN('visits')), O('Sessions with attendance on file', 'int', SESN), O('Outcomes counted on file', 'int', RN('outcomes_n')), O('Cost on file', 'money', RN('cost')),
    O('Volunteer hours on file', 'num', RN('vol_hours')), O('Numbers the funder asks for', 'int', '{in:need_people}+{in:need_visits}+{in:need_sessions}+{in:need_outcomes}+{in:need_cost}+{in:need_hours}'), O('Numbers missing', 'int', MISSN),
    O('First missing number', 'text', 'IF(%s=0,%s,%s)' % (MISSN, c2('Nothing missing'), FIRSTM)), O('Numbers on file', 'int', '{in:need_people}+{in:need_visits}+{in:need_sessions}+{in:need_outcomes}+{in:need_cost}+{in:need_hours}-%s' % MISSN),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (MISSN, c2('Complete'), c2('Add'), FIRSTM))],
    GR('What if', ('Summer Youth Camp this quarter', {'program': PGt('Summer Youth Camp')}), ('Camp, last 12 months', {'program': PGt('Summer Youth Camp'), 'period': '=' + tok('rperiod', 'Last 12 months')}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}),
       ('Only people and cost', {'need_visits': 0, 'need_sessions': 0, 'need_outcomes': 0, 'need_hours': 0}), ('Last year', {'period': '=' + tok('rperiod', 'Last year')}))))

# 15 ----------------------------------------------------------- capacity and waiting check
CAPP = ISF('{in:program}'); ENRP = ENR('{in:program}'); WAITP = WAIT('{in:program}')
tools.append(TOOL('capacity_check', 'Capacity and Waiting Check', 'Is a program full and do we add a session',
    'Pick a program; enrolled people are set against capacity and the waiting list, and the verdict says add a session, hold or room free.', [
    IL('program', 'Program', 'program', 'After-School Learning')], [
    O('Capacity', 'int', CAPP), O('Enrolled', 'int', ENRP), O('Free places', 'int', 'MAX(0,%s-%s)' % (CAPP, ENRP)), O('Capacity used', 'pct', 'IF(%s>0,%s/%s,0)' % (CAPP, ENRP, CAPP)), O('Waiting', 'int', WAITP),
    O('Waiting after the free places are filled', 'int', 'MAX(0,%s-MAX(0,%s-%s))' % (WAITP, CAPP, ENRP)), O('Sessions this month', 'int', 'SUMIFS(%s,%s,{in:program},%s,%s)' % (R('program_months', 'sessions'), R('program_months', 'program'), R('program_months', 'month'), MS)),
    O('Average attendees a session, last 12 months', 'num', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,{in:program},%s,">="&({today}-365)),1),0)' % (R('sessions', 'attendees'), R('sessions', 'program'), R('sessions', 'date'))),
    O('Full at this share of capacity', 'pct', '{set:full_share}'),
    O('Verdict', 'text', 'IF(%s>MAX(0,%s-%s),%s,IF(%s>0,%s,IF(IF(%s>0,%s/%s,0)>={set:full_share},%s,%s)))' % (WAITP, CAPP, ENRP, c1('Add a session'), WAITP, c1('Room free'), CAPP, ENRP, CAPP, c1('Hold'), c1('Room free')))],
    GR('What if', ('Family Food Pantry', {'program': PGt('Family Food Pantry')}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('Summer Youth Camp', {'program': PGt('Summer Youth Camp')}))))

# 16 ----------------------------------------------------------- waiting list clearer
FREEW = 'SUMIFS(%s,%s,{in:program},%s,%s)' % (R('clear_time', 'freed_week'), R('clear_time', 'program'), R('clear_time', 'pace'), tok('pace', 'Your usual pace'))
STILL = 'MAX(0,%s-MAX(0,%s-%s))' % (WAITP, CAPP, ENRP)
PW = '(%s+{in:extra_week})' % FREEW
WKS = 'IF(%s=0,0,IF(%s>0,ROUNDUP(%s/%s,0),9999))' % (STILL, PW, STILL, PW)
ADDP = 'MAX(0,ROUNDUP(%s-{in:target_weeks}*%s,0))' % (STILL, PW)
tools.append(TOOL('waiting_clearer', 'Waiting List Clearer', 'When does the waiting list clear, or what do we add',
    'Pick a program, extra places you can free a week and the weeks you accept; the list is divided by the places freed a week, and the verdict says when it clears or what to add.', [
    IL('program', 'Program', 'program', 'After-School Learning'), I('extra_week', 'Extra places you can free a week', 0, 'num'), I('target_weeks', 'Weeks you accept', 4, 'int')], [
    O('Waiting', 'int', WAITP), O('Free places now', 'int', 'MAX(0,%s-%s)' % (CAPP, ENRP)), O('Waiting after the free places', 'int', STILL), O('Places freed a week, your usual', 'num', 'ROUND(%s,2)' % FREEW), O('Places freed a week with the extra', 'num', 'ROUND(%s,2)' % PW),
    O('Weeks to clear', 'int', 'IF(%s=9999,0,%s)' % (WKS, WKS)), O('Clears around', 'date', 'IF(%s=9999,"",{today}+7*%s)' % (WKS, WKS)), O('Places to add to clear in the weeks you accept', 'int', ADDP),
    O('Waiting list share of capacity', 'pct', 'IF(%s>0,%s/%s,0)' % (CAPP, WAITP, CAPP)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<={in:target_weeks},%s&" "&%s&" "&%s,%s&" "&%s&" "&%s))' % (STILL, c2('List clears now'), WKS, c2('Clears in'), WKS, c2('weeks'), c2('Add'), ADDP, c2('places')))],
    GR('What if', ('Free 1 more a week', {'extra_week': 1}), ('Free 2 more a week', {'extra_week': 2}), ('Accept 8 weeks', {'target_weeks': 8}), ('Accept 12 weeks', {'target_weeks': 12}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('Summer Youth Camp', {'program': PGt('Summer Youth Camp')}))))

# 17 ----------------------------------------------------------- session planner
PIDX = 'IFERROR(MATCH({in:program},%s,0),0)' % R('programs', 'program')
PK = R('weekday_att', 'plan_key')
PKMIN = 'IFERROR(IF(SMALL(%s,COUNTIF(%s,"<"&%s*1000000)+1)<(%s+1)*1000000,SMALL(%s,COUNTIF(%s,"<"&%s*1000000)+1),""),"")' % (PK, PK, PIDX, PIDX, PK, PK, PIDX)
AVGA = 'IFERROR(AVERAGEIFS(%s,%s,{in:program},%s,">="&({today}-365)),0)' % (R('sessions', 'attendees'), R('sessions', 'program'), R('sessions', 'date'))
AVGV = 'IFERROR(AVERAGEIFS(%s,%s,{in:program},%s,">="&({today}-365)),0)' % (R('sessions', 'volunteers'), R('sessions', 'program'), R('sessions', 'date'))
NEEDP = 'MAX(0,%s-MAX(0,%s-%s))' % (WAITP, CAPP, ENRP)
SIZE = 'IF({in:group}>0,{in:group},%s)' % AVGA
NSES = 'IF(%s>0,ROUNDUP(%s/%s,0),0)' % (SIZE, NEEDP, SIZE)
SESN12 = 'COUNTIFS(%s,{in:program},%s,">="&({today}-365))' % (R('sessions', 'program'), R('sessions', 'date'))
WDL = 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (R('weekday_att', 'weekday'), PKMIN, PK)
tools.append(TOOL('session_planner', 'Session Planner', 'How many sessions do we add and on which weekday',
    'Pick a program and, if you know it, how many people one added session can take; the waiting list beyond the free places is divided by that size, and the quietest running weekday is named.', [
    IL('program', 'Program', 'program', 'After-School Learning'), I('group', 'People one added session can take, 0 uses your average', 0, 'int')], [
    O('Waiting', 'int', WAITP), O('People to place beyond the free places', 'int', NEEDP), O('Average attendees a session, last 12 months', 'num', 'ROUND(%s,1)' % AVGA), O('People one added session takes', 'num', 'ROUND(%s,1)' % SIZE),
    O('Sessions to add', 'int', NSES), O('Weekday to add them on', 'text', WDL), O('Next date of that weekday', 'date', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('weekday_att', 'next_date'), PKMIN, PK)),
    O('Sessions on that weekday, last 12 months', 'int', 'IFERROR(INT(MOD(%s,1000000)/10),0)' % PKMIN), O('Volunteers for each added session', 'int', 'ROUNDUP(%s,0)' % AVGV), O('Volunteers needed in all', 'int', '%s*ROUNDUP(%s,0)' % (NSES, AVGV)),
    O('Cost of one session, last 12 months', 'money', 'IF(%s>0,ROUND(SUMIFS(%s,%s,{in:program},%s,">="&EDATE(%s,-11))/%s,0),0)' % (SESN12, R('program_cost', 'total'), R('program_cost', 'program'), R('program_cost', 'month'), MS, SESN12)),
    O('Cost of the added sessions', 'money', 'IF(%s>0,ROUND(%s*SUMIFS(%s,%s,{in:program},%s,">="&EDATE(%s,-11))/%s,0),0)' % (SESN12, NSES, R('program_cost', 'total'), R('program_cost', 'program'), R('program_cost', 'month'), MS, SESN12)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s&" "&%s)' % (NSES, c2('Hold'), c2('Add'), NSES, c2('session(s) on'), WDL))],
    GR('What if', ('Each session takes 20', {'group': 20}), ('Each session takes 10', {'group': 10}), ('Each session takes 40', {'group': 40}), ('Senior Meals and Visits', {'program': PGt('Senior Meals and Visits')}), ('Family Food Pantry', {'program': PGt('Family Food Pantry')}))))

# 18 ----------------------------------------------------------- program priority view
def CQN(p, k): return 'SUMIFS(%s,%s,%s,%s,EDATE(%s,%d))' % (R('cpp_quarter', 'cost_per_participant'), R('cpp_quarter', 'program'), tok('program', p), R('cpp_quarter', 'quarter_start'), QSF, -3 * k)
def OSH(p): return 'IFERROR(SUMIFS(%s,%s,%s,%s,">="&%s)/SUMIFS(%s,%s,%s,%s,">="&%s),0)' % (R('outcomes', 'actual'), R('outcomes', 'program'), tok('program', p), R('outcomes', 'quarter'), YS, R('outcomes', 'target'), R('outcomes', 'program'), tok('program', p), R('outcomes', 'quarter'), YS)
def CHG(p): return 'IF(%s>0,%s/%s-1,0)' % (CQN(p, 4), CQN(p, 0), CQN(p, 4))
def WT(p): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('capacity', 'waiting'), tok('sprogram', p), R('capacity', 'program'))
def VERD(p): return 'IF(OR(%s<{in:minshare},%s>{in:rise}),%s,IF(%s>0,%s,%s))' % (OSH(p), CHG(p), c1('Review'), WT(p), c1('Grow'), c1('Hold'))
PO = []
for p in PROGRAMS:
    short = {'After-School Learning': 'After-School', 'Family Food Pantry': 'Pantry', 'Senior Meals and Visits': 'Senior Meals', 'Summer Youth Camp': 'Camp'}[p]
    PO += [O('%s, cost per participant' % short, 'money', CQN(p, 0)), O('%s, change on a year ago' % short, 'pct', CHG(p)), O('%s, share of outcome target' % short, 'pct', OSH(p)), O('%s, waiting' % short, 'int', WT(p)), O('%s, verdict' % short, 'text', VERD(p))]
tools.append(TOOL('priority_view', 'Program Priority View', 'Which program do we grow, hold or review',
    'Type the rise in cost you accept and the share of outcome targets a program should meet; cost, outcomes and waiting go side by side, and each program gets grow, hold or review.', [
    I('rise', 'Rise in cost per participant you accept', 0.10, 'pct'), I('minshare', 'Share of outcome targets a program should meet', 0.90, 'pct')], PO,
    GR('What if', ('Accept a 20 percent rise', {'rise': 0.20}), ('Accept no rise', {'rise': 0}), ('Outcomes at 80 percent', {'minshare': 0.80}), ('Outcomes at 95 percent', {'minshare': 0.95}))))
assert len(tools) == 18
