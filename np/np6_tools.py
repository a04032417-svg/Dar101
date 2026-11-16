"""Nonprofit suite part 6: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np6_lists import *
import np6_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
YS = 'DATE(YEAR({today}),1,1)'
YSL = 'DATE(YEAR({today})-1,1,1)'
WORKED = tok('shstatus', 'Worked'); ACTIVE = tok('vstatus', 'Active'); LAPSED = tok('vstatus', 'Lapsed'); SAT = tok('wday', 'Saturday')
WH = R('shifts', 'worked_hours'); SD = R('shifts', 'date')
def HRS(extra=''): return 'SUMIFS(%s%s)' % (WH, extra)
def DT(a, b=None): return ',%s,">="&%s' % (SD, a) + ((',%s,"<"&%s' % (SD, b)) if b else '')
HV_ = lambda a, b=None: 'SUMIFS(%s,%s,">="&%s%s)' % (R('hours_value', 'hours'), R('hours_value', 'month'), a, (',%s,"<"&%s' % (R('hours_value', 'month'), b)) if b else '')
H_YEAR = HV_(YS); H_LAST = HV_(YSL, YS); H30 = HRS(',%s,">="&({today}-30),%s,"<="&{today}' % (SD, SD))
GAPW = lambda d: '%s,">"&{today},%s,"<="&({today}+%s)' % (R('slots', 'date'), R('slots', 'date'), d)
def RET(col, yr): return 'SUMIFS(%s,%s,%s)' % (R('vol_retention', col), R('vol_retention', 'year'), yr)
def MSW(label): return 'INDEX({range:member_switch.setting},MATCH(%s,{range:member_switch.item},0))' % tok('mitem', label)
tools = []

# 1 ------------------------------------------------------------ shift gap finder
N1 = 'COUNTIFS(%s,%s,">0")' % (GAPW('{in:days}'), R('slots', 'gap')); P1 = 'SUMIFS(%s,%s)' % (R('slots', 'gap'), GAPW('{in:days}'))
NEED1 = 'SUMIFS(%s,%s)' % (R('slots', 'needed'), GAPW('{in:days}')); SIGN1 = 'SUMIFS(%s,%s)' % (R('slots', 'signed_up'), GAPW('{in:days}'))
def GP(col, k): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"")' % (R('gaps', col), k, R('gaps', 'rank'))
tools.append(TOOL('gap_finder', 'Shift Gap Finder', 'Which shifts still need people, soonest first',
    'Type how many days ahead to look; the open shifts, the people short, the first three gaps by date and the busiest week are shown.', [
    I('days', 'Days ahead to look', 7, 'int')], [
    O('Shifts with a gap', 'int', N1), O('People short', 'int', P1), O('People needed in all', 'int', NEED1), O('People signed up', 'int', SIGN1),
    O('Share of the need filled', 'pct', 'IF(%s>0,%s/%s,1)' % (NEED1, SIGN1, NEED1)),
    O('First gap, date', 'date', GP('date', 1)), O('First gap, program', 'text', GP('program', 1)), O('First gap, people short', 'int', GP('gap', 1)),
    O('Second gap, date', 'date', GP('date', 2)), O('Second gap, program', 'text', GP('program', 2)), O('Second gap, people short', 'int', GP('gap', 2)),
    O('Third gap, date', 'date', GP('date', 3)), O('Third gap, program', 'text', GP('program', 3)), O('Third gap, people short', 'int', GP('gap', 3)),
    O('Busiest week starts', 'date', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (R('gaps', 'week_start'), R('gaps', 'week_gap'), R('gaps', 'week_gap'))), O('People short that week', 'int', 'MAX(%s)' % R('gaps', 'week_gap')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s&", "&%s&" "&%s)' % (N1, ck('Clear'), ck('Fill'), N1, ck('shifts'), P1, ck('people short')))],
    GR('What if', ('Three days ahead', {'days': 3}), ('Two weeks ahead', {'days': 14}), ('A month ahead', {'days': 30}), ('Two months ahead', {'days': 60}))))

# 2 ------------------------------------------------------------ shift fill planner
REAL2 = 'SUMIFS(%s,%s)' % (R('slots', 'gap'), GAPW(7)); USED2 = 'IF({in:gap}>0,{in:gap},%s)' % REAL2
NEED2 = 'ROUNDUP(%s/(1-{in:noshow}),0)' % USED2
ASK2 = 'ROUNDUP(%s/{in:reply},0)' % NEED2
POOL2 = 'COUNTIFS(%s,%s,%s,"<>")' % (R('volunteers', 'status'), ACTIVE, R('volunteers', 'volunteer_id'))
tools.append(TOOL('fill_planner', 'Shift Fill Planner', 'How many people must we ask to fill the gap',
    'Type your reply rate and no-show rate (0 in the gap box uses the real gap of the next 7 days); the number of people to ask is worked out and compared with your active volunteers.', [
    I('gap', 'People short (0 uses the next 7 days)', 0, 'int'), I('reply', 'Share of people you ask who say yes', 0.35, 'pct'), I('noshow', 'Share who say yes and do not come', 0.06, 'pct')], [
    O('Real gap, next 7 days', 'int', REAL2), O('People short used', 'int', USED2), O('Yes answers needed', 'int', NEED2), O('People to ask', 'int', ASK2), O('Active volunteers', 'int', POOL2),
    O('Share of active volunteers to ask', 'pct', 'IF(%s>0,%s/%s,0)' % (POOL2, ASK2, POOL2)),
    O('People to ask if 10 points fewer say yes', 'int', 'ROUNDUP(%s/MAX(0.01,{in:reply}-0.1),0)' % NEED2), O('People to ask if 10 points more say yes', 'int', 'ROUNDUP(%s/MIN(1,{in:reply}+0.1),0)' % NEED2),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>%s,%s,%s&" "&%s&" "&%s))' % (USED2, ck('Clear'), ASK2, POOL2, ck('Recruit more volunteers'), ck('Ask'), ASK2, ck('people')))],
    GR('What if', ('Twenty people short', {'gap': 20}), ('Half the usual replies', {'reply': 0.18}), ('Good replies', {'reply': 0.55}), ('More no-shows', {'noshow': 0.15}))))

# 3 ------------------------------------------------------------ tomorrow's reminder list
N3 = 'COUNTIFS(%s,{in:days})' % R('tomorrow', 'days_away')
def TL(k): return 'IFERROR(INDEX(%s,MATCH({in:days}*1000+%d,%s,0))&" "&INDEX(%s,MATCH({in:days}*1000+%d,%s,0))&" "&INDEX(%s,MATCH({in:days}*1000+%d,%s,0))&" "&INDEX(%s,MATCH({in:days}*1000+%d,%s,0)),"")' % (
    R('tomorrow', 'volunteer'), k, R('tomorrow', 'dkey'), R('tomorrow', 'phone'), k, R('tomorrow', 'dkey'), R('tomorrow', 'starts'), k, R('tomorrow', 'dkey'), R('tomorrow', 'program'), k, R('tomorrow', 'dkey'))
tools.append(TOOL('reminder_list', "Tomorrow's Reminder List", 'Who do we remind before the shift',
    "Type how many days ahead (1 is tomorrow); the shifts, the volunteers on a first shift, the hours and the first five reminders with phone and start time are shown.", [
    I('days', 'Days ahead (1 is tomorrow)', 1, 'int')], [
    O('Shifts booked that day', 'int', N3), O('Volunteers on a first shift', 'int', 'COUNTIFS(%s,{in:days},%s,%s)' % (R('tomorrow', 'days_away'), R('tomorrow', 'flag'), ck('First shift'))),
    O('Hours booked that day', 'hours', 'SUMIFS(%s,%s,{in:days})' % (R('tomorrow', 'hours'), R('tomorrow', 'days_away'))),
    O('Morning shifts', 'int', 'COUNTIFS(%s,{in:days},%s,%s)' % (R('tomorrow', 'days_away'), R('tomorrow', 'shift'), tok('shift', 'Morning'))), O('Afternoon shifts', 'int', 'COUNTIFS(%s,{in:days},%s,%s)' % (R('tomorrow', 'days_away'), R('tomorrow', 'shift'), tok('shift', 'Afternoon'))),
    O('Reminder 1', 'text', TL(1)), O('Reminder 2', 'text', TL(2)), O('Reminder 3', 'text', TL(3)), O('Reminder 4', 'text', TL(4)), O('Reminder 5', 'text', TL(5)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s)' % (N3, ck('Nothing booked'), ck('Send'), N3, ck('reminders')))],
    GR('What if', ('Two days ahead', {'days': 2}), ('Three days ahead', {'days': 3}))))

# 4 ------------------------------------------------------------ availability matcher
AV4 = 'SUMIFS(%s,%s,{in:weekday},%s,{in:shift})' % (R('availability_view', 'available'), R('availability_view', 'weekday'), R('availability_view', 'shift'))
GA4 = 'SUMIFS(%s,%s,{in:weekday},%s,{in:shift})' % (R('availability_view', 'gap_ahead'), R('availability_view', 'weekday'), R('availability_view', 'shift'))
def NM(k, col='volunteer'):
    def one(sc): return 'IF(LARGE(%s,%d)>0,IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),""),"")' % (R('hours_by_volunteer', sc), k, R('hours_by_volunteer', col), R('hours_by_volunteer', sc), k, R('hours_by_volunteer', sc))
    return 'IF({in:weekday}=%s,%s,%s)' % (SAT, one('ask_we'), one('ask_wd'))
tools.append(TOOL('avail_matcher', 'Availability Matcher', 'Who do we ask first for this weekday and shift',
    'Pick a weekday and a shift; the active volunteers who can come are set against the gap ahead and the three most active of them are named to ask first.', [
    IL('weekday', 'Weekday', 'wday', 'Tuesday'), IL('shift', 'Shift', 'shift', 'Morning')], [
    O('Volunteers available', 'int', AV4), O('People short ahead', 'int', GA4), O('Available for each person short', 'num', 'IF(%s>0,ROUND(%s/%s,1),0)' % (GA4, AV4, GA4)),
    O('Slots held in the last 90 days', 'int', 'SUMIFS(%s,%s,{in:weekday},%s,{in:shift})' % (R('availability_view', 'slots_held'), R('availability_view', 'weekday'), R('availability_view', 'shift'))),
    O('Average gap a slot, last 90 days', 'num', 'SUMIFS(%s,%s,{in:weekday},%s,{in:shift})' % (R('availability_view', 'avg_gap'), R('availability_view', 'weekday'), R('availability_view', 'shift'))),
    O('Ask first', 'text', NM(1)), O('Ask second', 'text', NM(2)), O('Ask third', 'text', NM(3)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>=%s*3,%s&" "&%s&", "&%s&", "&%s&" "&%s,%s&" "&{in:weekday}))' % (GA4, ck('Clear'), AV4, GA4, ck('Ask'), NM(1), NM(2), NM(3), ck('first'), ck('Recruit for')))],
    GR('What if', ('Saturday afternoon', {'weekday': '=' + tok('wday', 'Saturday'), 'shift': '=' + tok('shift', 'Afternoon')}), ('Monday morning', {'weekday': '=' + tok('wday', 'Monday'), 'shift': '=' + tok('shift', 'Morning')}),
       ('Thursday afternoon', {'weekday': '=' + tok('wday', 'Thursday'), 'shift': '=' + tok('shift', 'Afternoon')}), ('Friday morning', {'weekday': '=' + tok('wday', 'Friday'), 'shift': '=' + tok('shift', 'Morning')}))))

# 5 ------------------------------------------------------------ hours worked report
THIS5 = '{in:period}=%s' % tok('vperiod', 'This year')
HVM = lambda c: R('hours_value', c); HPM = lambda c: R('hours_program_month', c)
def PH(): return 'IF(%s,%s,%s)' % (THIS5, H_YEAR, H_LAST)
def PHP():
    f = lambda a, b=None: 'SUMIFS(%s,%s,{in:program},%s,">="&%s%s)' % (HPM('hours'), HPM('program'), HPM('month'), a, (',%s,"<"&%s' % (HPM('month'), b)) if b else '')
    return 'IF(%s,%s,%s)' % (THIS5, f(YS), f(YSL, YS))
TOPN = 'IF(%s,IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),""),IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),""))' % (THIS5, R('hours_by_volunteer', 'volunteer'), R('hours_by_volunteer', 'hours_year'), R('hours_by_volunteer', 'hours_year'),
                                                                                                      R('hours_by_volunteer', 'volunteer'), R('hours_by_volunteer', 'hours_last'), R('hours_by_volunteer', 'hours_last'))
YTD5 = HV_(YS, 'DATE(YEAR({today}),MONTH({today}),1)'); LYTD5 = HV_(YSL, 'EDATE(DATE(YEAR({today}),MONTH({today}),1),-12)')
tools.append(TOOL('hours_report', 'Hours Worked Report', 'Who gave the hours and are we on track',
    'Pick a period and a program; the hours, shifts, helpers and the top helper are shown, and this year to the last full month is set against the same months of last year.', [
    IL('period', 'Period', 'vperiod', 'This year'), IL('program', 'Program or area', 'sprog', 'Senior Meals and Visits')], [
    O('Hours worked, all programs', 'hours', PH()), O('Hours worked, this program', 'hours', PHP()), O('Share of the hours from this program', 'pct', 'IF(%s>0,%s/%s,0)' % (PH(), PHP(), PH())),
    O('Shifts worked, all programs', 'int', 'IF(%s,SUMIFS(%s,%s,">="&%s),SUMIFS(%s,%s,">="&%s,%s,"<"&%s))' % (THIS5, HVM('shifts_n'), HVM('month'), YS, HVM('shifts_n'), HVM('month'), YSL, HVM('month'), YS)),
    O('Volunteers who worked', 'int', 'IF(%s,COUNTIFS(%s,">0"),COUNTIFS(%s,">0"))' % (THIS5, R('hours_by_volunteer', 'hours_year'), R('hours_by_volunteer', 'hours_last'))),
    O('Volunteers with 100 hours or more', 'int', 'IF(%s,COUNTIFS(%s,">=100"),COUNTIFS(%s,">=100"))' % (THIS5, R('hours_by_volunteer', 'hours_year'), R('hours_by_volunteer', 'hours_last'))),
    O('Top helper', 'text', TOPN), O('Top helper, hours', 'hours', 'IF(%s,MAX(%s),MAX(%s))' % (THIS5, R('hours_by_volunteer', 'hours_year'), R('hours_by_volunteer', 'hours_last'))),
    O('Hours this year to the last full month', 'hours', YTD5), O('Hours last year to the same month', 'hours', LYTD5), O('Change on last year', 'pct', 'IF(%s>0,%s/%s-1,0)' % (LYTD5, YTD5, LYTD5)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)&", "&%s&" "&%s' % (YTD5, LYTD5, ck('On track'), ck('Behind last year'), ck('top helper'), TOPN))],
    GR('What if', ('Last year', {'period': '=' + tok('vperiod', 'Last year')}), ('Family Food Pantry', {'program': '=' + tok('sprog', 'Family Food Pantry')}), ('After-School Learning', {'program': '=' + tok('sprog', 'After-School Learning')}),
       ('Summer Youth Camp', {'program': '=' + tok('sprog', 'Summer Youth Camp')}))))

# 6 ------------------------------------------------------------ program volunteer cover
PD6 = '%s,{in:program},%s,">="&({today}-{in:days}),%s,"<="&{today}'
def S6(col): return 'SUMIFS(%s,%s,{in:program},%s,">="&({today}-{in:days}),%s,"<="&{today})' % (R('slots', col), R('slots', 'program'), R('slots', 'date'), R('slots', 'date'))
SLN6 = 'COUNTIFS(%s,{in:program},%s,">="&({today}-{in:days}),%s,"<="&{today})' % (R('slots', 'program'), R('slots', 'date'), R('slots', 'date'))
HW6 = 'SUMIFS(%s,%s,{in:program},%s,">="&({today}-{in:days}),%s,"<="&{today})' % (WH, R('shifts', 'program'), SD, SD)
NS6 = 'COUNTIFS(%s,{in:program},%s,%s,%s,">="&({today}-{in:days}),%s,"<="&{today})' % (R('shifts', 'program'), R('shifts', 'status'), tok('shstatus', 'No-show'), SD, SD)
WK6 = 'COUNTIFS(%s,{in:program},%s,%s,%s,">="&({today}-{in:days}),%s,"<="&{today})' % (R('shifts', 'program'), R('shifts', 'status'), WORKED, SD, SD)
FILL6 = 'IF(%s>0,%s/%s,1)' % (S6('needed'), S6('signed_up'), S6('needed'))
tools.append(TOOL('program_cover', 'Program Volunteer Cover', 'Does this program have enough volunteers',
    'Pick a program, the days to look back and the share of slots you want filled; the people needed, signed up, hours worked and no-shows decide whether the program is covered or thin.', [
    IL('program', 'Program', 'program', 'Family Food Pantry'), I('days', 'Days to look back', 90, 'int'), I('target', 'Share of slots you want filled', 0.9, 'pct')], [
    O('Slots held', 'int', SLN6), O('People needed', 'int', S6('needed')), O('People signed up', 'int', S6('signed_up')), O('Share of the need filled', 'pct', FILL6), O('Hours worked', 'hours', HW6),
    O('Hours worked for each slot', 'num', 'IF(%s>0,ROUND(%s/%s,1),0)' % (SLN6, HW6, SLN6)), O('Shifts worked', 'int', WK6), O('No-shows', 'int', NS6), O('Share of booked shifts that were no-shows', 'pct', 'IF(%s+%s>0,%s/(%s+%s),0)' % (WK6, NS6, NS6, WK6, NS6)),
    O('People short in the days ahead', 'int', 'SUMIFS(%s,%s,{in:program},%s,">"&{today})' % (R('slots', 'gap'), R('slots', 'program'), R('slots', 'date'))),
    O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (FILL6, ck('Covered'), ck('Thin')))],
    GR('What if', ('Senior Meals and Visits', {'program': '=' + tok('program', 'Senior Meals and Visits')}), ('After-School Learning', {'program': '=' + tok('program', 'After-School Learning')}), ('Summer Youth Camp', {'program': '=' + tok('program', 'Summer Youth Camp')}),
       ('Last 30 days', {'days': 30}), ('A stricter target', {'target': 0.95}))))

# 7 ------------------------------------------------------------ volunteer value calculator
VAL = lambda h: '%s*{in:rate}' % h
tools.append(TOOL('value_calc', 'Volunteer Value Calculator', 'What are the volunteer hours worth at our own hour value',
    'Type the value of one volunteer hour (your setting) and the hours of one full-time year; the value of this year, last year and the last 30 days is shown with the full-time equivalent.', [
    I('rate', 'Value of one volunteer hour, your setting', 30), I('fte', 'Hours in one full-time year, your setting', 1800, 'int')], [
    O('Hours this year', 'hours', H_YEAR), O('Value this year', 'money', VAL(H_YEAR)), O('Hours last year', 'hours', H_LAST), O('Value last year', 'money', VAL(H_LAST)), O('Hours, last 30 days', 'hours', H30), O('Value, last 30 days', 'money', VAL(H30)),
    O('Volunteers who worked this year', 'int', 'COUNTIFS(%s,">0")' % R('hours_by_volunteer', 'hours_year')), O('Value for each volunteer this year', 'money', 'IFERROR(%s/COUNTIFS(%s,">0"),0)' % (VAL(H_YEAR), R('hours_by_volunteer', 'hours_year')), ),
    O('Full-time staff equivalent this year', 'num', 'IF({in:fte}>0,ROUND(%s/{in:fte},1),0)' % H_YEAR), O('Change in value on last year', 'money', '%s-%s' % (VAL(H_YEAR), VAL(H_LAST))),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&" "&%s' % (ck('Worth'), VAL(H_YEAR), ck('this year, your setting')))],
    GR('What if', ('A lower hour value', {'rate': 22}), ('A higher hour value', {'rate': 38}), ('A shorter working year', {'fte': 1600}), ('A longer working year', {'fte': 2000}))))

# 8 ------------------------------------------------------------ value sensitivity
def VS(f): return 'ROUND(%s*%s,0)' % (H_YEAR, f)
tools.append(TOOL('value_sens', 'Value Sensitivity', 'How far does the value move if our hour value moves',
    'Type a low, a base and a high value for one volunteer hour; the value of this year at each and at five steps around the base shows how much of the figure rests on your own setting.', [
    I('low', 'Low value of one hour', 20), I('base', 'Base value of one hour', 30), I('high', 'High value of one hour', 42)], [
    O('Hours this year', 'hours', H_YEAR), O('Value at the low setting', 'money', VS('{in:low}')), O('Value at the base setting', 'money', VS('{in:base}')), O('Value at the high setting', 'money', VS('{in:high}')),
    O('Spread from low to high', 'money', '%s-%s' % (VS('{in:high}'), VS('{in:low}'))), O('Spread as a share of the base value', 'pct', 'IF({in:base}>0,({in:high}-{in:low})/{in:base},0)'),
    O('Base value less 20%', 'money', VS('{in:base}*0.8')), O('Base value less 10%', 'money', VS('{in:base}*0.9')), O('Base value plus 10%', 'money', VS('{in:base}*1.1')), O('Base value plus 20%', 'money', VS('{in:base}*1.2')),
    O('Value of last year at the base setting', 'money', 'ROUND(%s*{in:base},0)' % H_LAST),
    O('Verdict', 'text', '%s&" "&%s&" - "&%s' % (ck('Range'), VS('{in:low}'), VS('{in:high}')))],
    GR('What if', ('A narrow range', {'low': 26, 'high': 34}), ('A wide range', {'low': 15, 'high': 55}), ('A higher base', {'base': 36}), ('A lower base', {'base': 24}))))

# 9 ------------------------------------------------------------ volunteer retention check
A_LAST = RET('active', 'YEAR({today})-1'); K_THIS = RET('kept', 'YEAR({today})'); A_PREV = RET('active', 'YEAR({today})-2'); K_LAST = RET('kept', 'YEAR({today})-1')
RT_THIS = 'IF(%s>0,%s/%s,0)' % (A_LAST, K_THIS, A_LAST); RT_LAST = 'IF({set:retention_own}>0,{set:retention_own},IF(%s>0,%s/%s,0))' % (A_PREV, K_LAST, A_PREV)
tools.append(TOOL('retention_check', 'Volunteer Retention Check', 'Are we keeping volunteers as well as last year',
    "Type the points that count as the same; the share of last year's volunteers who worked again this year is set against your own figure of last year.", [
    I('band', 'Points that count as the same', 0.02, 'pct')], [
    O('Volunteers last year', 'int', A_LAST), O('Of them, working again this year', 'int', K_THIS), O('Retention this year', 'pct', RT_THIS), O('Volunteers the year before', 'int', A_PREV), O('Of them, working last year', 'int', K_LAST),
    O('Retention last year, your own figure (Start sheet)', 'pct', RT_LAST), O('Difference in points', 'pct', '%s-%s' % (RT_THIS, RT_LAST)), O('Volunteers who did not return', 'int', '%s-%s' % (A_LAST, K_THIS)),
    O('Volunteers active this year', 'int', RET('active', 'YEAR({today})')), O('New to the shift log this year', 'int', '%s-%s' % (RET('active', 'YEAR({today})'), K_THIS)),
    O('Verdict', 'text', 'IF(%s>%s+{in:band},%s,IF(%s<%s-{in:band},%s,%s))' % (RT_THIS, RT_LAST, ck('Better'), RT_THIS, RT_LAST, ck('Worse'), ck('Same')))],
    GR('What if', ('A wider band', {'band': 0.05}), ('No band', {'band': 0}))))

# 10 ----------------------------------------------------------- lapsed volunteer ranker
NL = 'COUNTIFS(%s,"<>")' % R('lapsed', 'volunteer_id')
NC = 'COUNTIFS(%s,">="&{in:call})' % R('lapsed', 'hours_given'); NWR = 'COUNTIFS(%s,">="&{in:write},%s,"<"&{in:call})' % (R('lapsed', 'hours_given'), R('lapsed', 'hours_given'))
def LP(col, k): return 'INDEX(%s,MATCH(%d,%s,0))' % (R('lapsed', col), k, R('lapsed', 'rank'))
def LLINE(k): return 'IFERROR(%s&" - "&%s&" "&%s&" - "&IF(%s>={in:call},%s,IF(%s>={in:write},%s,%s)),"")' % (LP('volunteer', k), LP('hours_given', k), ck('hours'), LP('hours_given', k), ck('Call'), LP('hours_given', k), ck('Write'), ck('Let go'))
tools.append(TOOL('lapsed_ranker', 'Lapsed Volunteer Ranker', 'Which lapsed volunteers do we call, write to or let go',
    'Type the hours at which a lapsed volunteer gets a call and a letter; lapsed volunteers are counted by step and the five with the most hours given are named first.', [
    I('call', 'Hours given for a call', 50, 'num'), I('write', 'Hours given for a letter', 10, 'num')], [
    O('Lapsed volunteers', 'int', NL), O('To call', 'int', NC), O('To write to', 'int', NWR), O('To let go', 'int', '%s-%s-%s' % (NL, NC, NWR)),
    O('Hours given by those to call', 'hours', 'SUMIFS(%s,%s,">="&{in:call})' % (R('lapsed', 'hours_given'), R('lapsed', 'hours_given'))), O('Hours given by all lapsed volunteers', 'hours', 'SUM(%s)' % R('lapsed', 'hours_given')),
    O('Value of the hours given by those to call', 'money', 'SUMIFS(%s,%s,">="&{in:call})*{set:volunteer_hour_value}' % (R('lapsed', 'hours_given'), R('lapsed', 'hours_given'))),
    O('First on the list', 'text', LLINE(1)), O('Second on the list', 'text', LLINE(2)), O('Third on the list', 'text', LLINE(3)), O('Fourth on the list', 'text', LLINE(4)), O('Fifth on the list', 'text', LLINE(5)),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&%s&", "&%s&" "&%s' % (ck('Call'), NC, ck('write'), NWR, ck('let go'), '(%s-%s-%s)' % (NL, NC, NWR)))],
    GR('What if', ('Call from 100 hours', {'call': 100}), ('Call from 25 hours', {'call': 25}), ('Write from 5 hours', {'write': 5}), ('Write from 20 hours', {'write': 20}))))

# 11 ----------------------------------------------------------- reach-out plan
RLINE = lambda k: 'IFERROR(%s&" - "&%s&" "&%s&" - "&IF(%s>={set:call_hours},%s,%s)&" - "&%s&" "&(INT((%d-1)/{in:per_week})+1),"")' % (LP('volunteer', k), LP('hours_given', k), ck('hours'), LP('hours_given', k), ck('Call'), ck('Write'), ck('Week'), k)
TOP10 = 'SUMIFS(%s,%s,"<=10")' % (R('lapsed', 'hours_given'), R('lapsed', 'rank'))
MONTHN = 'MIN(10,{in:per_week}*4,COUNTIFS(%s,">0"))' % R('lapsed', 'hours_given')
tools.append(TOOL('reach_out', 'Reach-out Plan', 'Who do we contact this month among the lapsed',
    'Type how many volunteers you can contact each week and the start date; the ten lapsed volunteers with the most hours are listed with the step and the week to reach out.', [
    I('per_week', 'People you can contact each week', 3, 'int'), I('start', 'Start date', 'today', 'date')], [
    O('Rank 1', 'text', RLINE(1)), O('Rank 2', 'text', RLINE(2)), O('Rank 3', 'text', RLINE(3)), O('Rank 4', 'text', RLINE(4)), O('Rank 5', 'text', RLINE(5)),
    O('Rank 6', 'text', RLINE(6)), O('Rank 7', 'text', RLINE(7)), O('Rank 8', 'text', RLINE(8)), O('Rank 9', 'text', RLINE(9)), O('Rank 10', 'text', RLINE(10)),
    O('Hours given by these ten', 'hours', TOP10), O('Value of those hours, your setting', 'money', '%s*{set:volunteer_hour_value}' % TOP10),
    O('Weeks to reach all ten', 'int', 'ROUNDUP(10/{in:per_week},0)'), O('Last contact date', 'date', '{in:start}+7*(ROUNDUP(10/{in:per_week},0)-1)'),
    O('Verdict', 'text', '%s&" "&%s&" "&%s' % (ck('Reach out to'), MONTHN, ck('this month')))],
    GR('What if', ('Two a week', {'per_week': 2}), ('Five a week', {'per_week': 5}), ('Start in a week', {'start': '=TODAY()+7'}))))

# 12 ----------------------------------------------------------- new volunteer follow-up
NEW12 = 'COUNTIFS(%s,">="&({today}-{in:days}),%s,"<="&{today})' % (R('volunteers', 'joined'), R('volunteers', 'joined'))
FEW12 = 'COUNTIFS(%s,">="&({today}-{in:days}),%s,"<="&{today},%s,"<"&{in:min})' % (R('volunteers', 'joined'), R('volunteers', 'joined'), R('volunteers', 'shifts_n'))
def FV_(k): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0))&" "&INDEX(%s,MATCH(%d,%s,0))&" - "&%s&" "&INDEX(%s,MATCH(%d,%s,0)),"")' % (
    R('volunteers', 'name'), k, R('volunteers', 'follow_rank'), R('volunteers', 'phone'), k, R('volunteers', 'follow_rank'), ck('shifts worked'), R('volunteers', 'shifts_n'), k, R('volunteers', 'follow_rank'))
tools.append(TOOL('new_followup', 'New Volunteer Follow-up', 'Which new volunteers need a welcome call',
    'Type how many days count as new and how many shifts a new volunteer should have worked; new volunteers with too few shifts are counted and the first three (by your settings) are named with a phone.', [
    I('days', 'Days a volunteer counts as new', 60, 'int'), I('min', 'Shifts a new volunteer should have worked', 2, 'int')], [
    O('New volunteers', 'int', NEW12), O('With too few shifts', 'int', FEW12), O('Settled', 'int', '%s-%s' % (NEW12, FEW12)), O('Share settled', 'pct', 'IF(%s>0,(%s-%s)/%s,0)' % (NEW12, NEW12, FEW12, NEW12)),
    O('Average shifts of the new volunteers', 'num', 'IFERROR(AVERAGEIFS(%s,%s,">="&({today}-{in:days}),%s,"<="&{today}),0)' % (R('volunteers', 'shifts_n'), R('volunteers', 'joined'), R('volunteers', 'joined'))),
    O('Call first', 'text', FV_(1)), O('Call second', 'text', FV_(2)), O('Call third', 'text', FV_(3)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (FEW12, ck('Settled'), ck('Welcome call'), FEW12))],
    GR('What if', ('Last 30 days', {'days': 30}), ('Last 90 days', {'days': 90}), ('At least 3 shifts', {'min': 3}), ('At least 1 shift', {'min': 1}))))

# 13 ----------------------------------------------------------- volunteers who also give
GIV = 'COUNTIFS(%s,"<>")' % R('givers', 'volunteer_id'); ACT13 = 'COUNTIFS(%s,%s,%s,"<>")' % (R('volunteers', 'status'), ACTIVE, R('volunteers', 'volunteer_id'))
INV13 = '(COUNTIFS(%s,%s,%s,">="&{in:min})-COUNTIFS(%s,%s,%s,">="&{in:min},%s,1))' % (R('volunteers', 'status'), ACTIVE, R('volunteers', 'hours_worked'), R('volunteers', 'status'), ACTIVE, R('volunteers', 'hours_worked'), R('volunteers', 'gives'))
THK13 = 'SUM(%s)' % R('givers', 'recent')
tools.append(TOOL('givers_tool', 'Volunteers Who Give', 'Whom do we thank for gifts and whom do we invite to give',
    'Type the hours that mark a committed volunteer; volunteers who also give are counted with the money given, and active volunteers above that mark who do not give are counted as people to invite.', [
    I('min', 'Hours worked that mark a committed volunteer', 100, 'num')], [
    O('Volunteers who also give', 'int', GIV), O('Money they gave', 'money', 'SUM(%s)' % R('givers', 'total_given')), O('Gifts they made', 'int', 'SUM(%s)' % R('givers', 'gifts')),
    O('Average given by one volunteer', 'money', 'IF(%s>0,SUM(%s)/%s,0)' % (GIV, R('givers', 'total_given'), GIV)), O('Share of active volunteers who also give', 'pct', 'IF(%s>0,COUNTIFS(%s,%s,%s,1)/%s,0)' % (ACT13, R('volunteers', 'status'), ACTIVE, R('volunteers', 'gives'), ACT13)),
    O('Gave in the last days set on Start', 'int', THK13), O('Committed volunteers who do not give', 'int', INV13),
    O('Hours worked by volunteers who give', 'hours', 'SUM(%s)' % R('givers', 'hours_given')),
    O('Largest total given by a volunteer', 'money', 'MAX(%s)' % R('givers', 'total_given')),
    O('Who gave most', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (R('givers', 'volunteer'), R('givers', 'total_given'), R('givers', 'total_given'))),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&%s&" "&%s' % (ck('Thank'), THK13, ck('invite'), INV13, ck('to give')))],
    GR('What if', ('From 50 hours', {'min': 50}), ('From 200 hours', {'min': 200}), ('From 25 hours', {'min': 25}))))

# 14 ----------------------------------------------------------- recruitment need
HQ = HRS(',%s,">="&({today}-90),%s,"<="&{today}' % (SD, SD)); VQ = 'COUNTIFS(%s,">="&({today}-90),%s,"<="&{today})' % (R('hours_by_volunteer', 'last_shift'), R('hours_by_volunteer', 'last_shift'))
ATTR = '(1-%s)' % RT_THIS
AVGQ = 'IF(%s>0,%s/%s,0)' % (VQ, HQ, VQ); NEEDH = '(%s*(1+{in:growth}))' % HQ
NEEDP = 'IF(%s>0,ROUNDUP(%s/%s,0),0)' % (AVGQ, NEEDH, AVGQ); KEEP = 'ROUND(%s*(1-%s/4),0)' % (VQ, ATTR)
REC14 = 'MAX(0,%s-%s)' % (NEEDP, KEEP)
tools.append(TOOL('recruit_need', 'Recruitment Need', 'How many volunteers must we recruit for next quarter',
    "Type the growth in hours you plan; the hours of the last 90 days, the volunteers who gave them, your own yearly attrition and the growth give the number of people to recruit.", [
    I('growth', 'Growth in hours you plan for next quarter', 0.10, 'pct')], [
    O('Hours worked in the last 90 days', 'hours', HQ), O('Volunteers who worked in the last 90 days', 'int', VQ), O('Hours for each volunteer in 90 days', 'num', 'ROUND(%s,1)' % AVGQ),
    O('Hours needed next quarter', 'hours', NEEDH), O('Volunteers needed for those hours', 'int', NEEDP), O('Your own yearly attrition', 'pct', ATTR), O('Volunteers you expect to keep, one quarter', 'int', KEEP),
    O('People to recruit', 'int', REC14), O('Hours a new volunteer adds in a quarter at your average', 'hours', 'ROUND(%s,1)' % AVGQ),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s)' % (REC14, ck('No recruiting needed'), ck('Recruit'), REC14, ck('people')))],
    GR('What if', ('No growth', {'growth': 0}), ('Growth of 25%', {'growth': 0.25}), ('Growth of 50%', {'growth': 0.5}), ('Cut hours by 10%', {'growth': -0.1}))))

# 15 ----------------------------------------------------------- membership renewal list
MD = R('members', 'due_date'); MST = R('members', 'status')
DUE15 = 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+{in:days}),%s,%s)' % (MD, MD, MST, tok('dues', 'Due soon'))
OVD15 = 'COUNTIFS(%s,%s,%s,"<>")' % (MST, tok('dues', 'Overdue'), R('members', 'member_id')); LAP15 = 'COUNTIFS(%s,%s,%s,"<>")' % (MST, tok('dues', 'Lapsed'), R('members', 'member_id'))
def RN(col, k): return 'INDEX(%s,MATCH(%d,%s,0))' % (R('renewals', col), k, R('renewals', 'rank'))
RLN = lambda k: 'IFERROR(%s&" - "&%s&" "&%s&" - "&%s,"")' % (RN('member', k), RN('annual_dues', k), ck('dues'), RN('action', k))
tools.append(TOOL('renewal_list', 'Membership Renewal List', 'Which members do we notify, call or try to win back',
    'Type the days ahead to look; members due soon, overdue and lapsed are counted with their dues, and the three with the highest dues are named with the action.', [
    I('days', 'Days ahead to look', 30, 'int')], [
    O('Members due in the days ahead', 'int', DUE15), O('Dues due in the days ahead', 'money', 'SUMIFS(%s,%s,">="&{today},%s,"<="&({today}+{in:days}),%s,%s)' % (R('members', 'annual_dues'), MD, MD, MST, tok('dues', 'Due soon'))),
    O('Members overdue', 'int', OVD15), O('Dues overdue', 'money', 'SUMIFS(%s,%s,%s)' % (R('members', 'annual_dues'), MST, tok('dues', 'Overdue'))), O('Members lapsed', 'int', LAP15),
    O('Dues lost to lapsed members', 'money', 'SUMIFS(%s,%s,%s)' % (R('members', 'annual_dues'), MST, tok('dues', 'Lapsed'))),
    O('Highest dues first', 'text', RLN(1)), O('Highest dues second', 'text', RLN(2)), O('Highest dues third', 'text', RLN(3)),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&%s&", "&%s&" "&%s' % (ck('Send notice'), DUE15, ck('call'), OVD15, ck('lapsing'), LAP15))],
    GR('What if', ('Next 14 days', {'days': 14}), ('Next 60 days', {'days': 60}), ('Next 90 days', {'days': 90}))))

# 16 ----------------------------------------------------------- renewal rate check
DP_ = lambda col, yr: 'SUMIFS(%s,%s,%s)' % (R('dues_payments', col), R('dues_payments', 'due_year'), yr)
DUE_L = DP_('due_n', 'YEAR({today})-1'); REN_L = DP_('renewed', 'YEAR({today})-1'); DUE_T = DP_('due_n', 'YEAR({today})'); REN_T = DP_('renewed', 'YEAR({today})')
RR_L = 'IF(%s>0,%s/%s,0)' % (DUE_L, REN_L, DUE_L); RR_T = 'IF(%s>0,%s/%s,0)' % (DUE_T, REN_T, DUE_T)
tools.append(TOOL('renewal_rate', 'Renewal Rate Check', 'Are members renewing as well as last year',
    'Type the points that count as the same; renewals that came due so far this year are set against last year, using every dues payment and whether the member paid again on time.', [
    I('band', 'Points that count as the same', 0.03, 'pct')], [
    O('Renewals due last year', 'int', DUE_L), O('Renewed on time last year', 'int', REN_L), O('Renewal rate last year', 'pct', RR_L), O('Renewals due so far this year', 'int', DUE_T), O('Renewed on time this year', 'int', REN_T),
    O('Renewal rate this year so far', 'pct', RR_T), O('Difference in points', 'pct', '%s-%s' % (RR_T, RR_L)), O('Members who did not renew this year', 'int', '%s-%s' % (DUE_T, REN_T)),
    O('Dues of those who did not renew this year', 'money', 'SUMIFS(%s,%s,YEAR({today}),%s,1,%s,0)' % (R('dues_payments', 'amount'), R('dues_payments', 'due_year'), R('dues_payments', 'due_n'), R('dues_payments', 'renewed'))),
    O('Verdict', 'text', 'IF(%s>%s+{in:band},%s,IF(%s<%s-{in:band},%s,%s))' % (RR_T, RR_L, ck('Better'), RR_T, RR_L, ck('Worse'), ck('Same')))],
    GR('What if', ('A wider band', {'band': 0.08}), ('No band', {'band': 0}))))

# 17 ----------------------------------------------------------- dues forecast
TOT17 = 'SUM(%s)' % R('dues_forecast', 'expected_dues')
FAC17 = 'IF({in:scn}=%s,{in:rate},IF({in:scn}=%s,MIN(1,{in:rate}+{in:up}),MAX(0,{in:rate}-{in:down})))' % (tok('scenario', 'Base'), tok('scenario', 'Best'))
EXP17 = 'ROUND(%s*%s,0)' % (TOT17, FAC17)
M3 = 'ROUND((%s)*%s,0)' % ('+'.join('INDEX(%s,%d)' % (R('dues_forecast', 'expected_dues'), i) for i in (1, 2, 3)), FAC17)
tools.append(TOOL('dues_forecast_tool', 'Dues Forecast', 'How much in dues do we expect over the next 12 months',
    'Pick Base, Best or Worst and type the share of due members who renew; the dues falling due in the next 12 months are turned into your estimate and compared with the dues of the year before.', [
    IL('scn', 'Scenario', 'scenario', 'Base'), I('rate', 'Share of due members who renew, your estimate', 0.8, 'pct'), I('up', 'Best case, points more renew', 0.1, 'pct'), I('down', 'Worst case, points fewer renew', 0.15, 'pct')], [
    O('Members falling due, 12 months', 'int', 'SUM(%s)' % R('dues_forecast', 'renewals_due')), O('Dues falling due, 12 months', 'money', TOT17), O('Share who renew in this scenario', 'pct', FAC17), O('Dues expected, this scenario', 'money', EXP17),
    O('Dues expected, Base', 'money', 'ROUND(%s*{in:rate},0)' % TOT17), O('Dues expected, Best', 'money', 'ROUND(%s*MIN(1,{in:rate}+{in:up}),0)' % TOT17), O('Dues expected, Worst', 'money', 'ROUND(%s*MAX(0,{in:rate}-{in:down}),0)' % TOT17),
    O('Dues expected in the next 3 months', 'money', M3), O('Dues received in the same 12 months a year ago', 'money', 'SUM(%s)' % R('dues_forecast', 'last_year')),
    O('Change on a year ago', 'pct', 'IF(SUM(%s)>0,%s/SUM(%s)-1,0)' % (R('dues_forecast', 'last_year'), EXP17, R('dues_forecast', 'last_year'))),
    O('Verdict', 'text', '%s&" "&%s&" "&%s' % (ck('Dues expected'), EXP17, ck('your estimate')))],
    GR('What if', ('Best case', {'scn': '=' + tok('scenario', 'Best')}), ('Worst case', {'scn': '=' + tok('scenario', 'Worst')}), ('Only 6 in 10 renew', {'rate': 0.6}), ('9 in 10 renew', {'rate': 0.9}))))

# 18 ----------------------------------------------------------- level mix view
def LV_(lvl, col=None):
    if col: return 'SUMIFS(%s,%s,%s,%s,"<>"&%s,%s,"<>")' % (R('members', col), R('members', 'level'), tok('mlevel', lvl), MST, tok('dues', 'Lapsed'), R('members', 'member_id'))
    return 'COUNTIFS(%s,%s,%s,"<>"&%s,%s,"<>")' % (R('members', 'level'), tok('mlevel', lvl), MST, tok('dues', 'Lapsed'), R('members', 'member_id'))
ALLM = '(%s+%s+%s)' % (LV_('Friend'), LV_('Supporter'), LV_('Patron')); ALLD = '(%s+%s+%s)' % (LV_('Friend', 'annual_dues'), LV_('Supporter', 'annual_dues'), LV_('Patron', 'annual_dues'))
tools.append(TOOL('level_mix', 'Level Mix View', 'Which membership level should we grow',
    'Type the share of members you want at the Patron and Supporter levels; members and dues by level are shown and the level furthest below its target is named.', [
    I('patron', 'Share of members you want at Patron', 0.12, 'pct'), I('supporter', 'Share of members you want at Supporter', 0.35, 'pct')], [
    O('Friend members', 'int', LV_('Friend')), O('Supporter members', 'int', LV_('Supporter')), O('Patron members', 'int', LV_('Patron')), O('Members in all (not lapsed)', 'int', ALLM),
    O('Dues of Friend members', 'money', LV_('Friend', 'annual_dues')), O('Dues of Supporter members', 'money', LV_('Supporter', 'annual_dues')), O('Dues of Patron members', 'money', LV_('Patron', 'annual_dues')), O('Dues in all', 'money', ALLD),
    O('Patron share of members', 'pct', 'IF(%s>0,%s/%s,0)' % (ALLM, LV_('Patron'), ALLM)), O('Supporter share of members', 'pct', 'IF(%s>0,%s/%s,0)' % (ALLM, LV_('Supporter'), ALLM)), O('Patron share of dues', 'pct', 'IF(%s>0,%s/%s,0)' % (ALLD, LV_('Patron', 'annual_dues'), ALLD)),
    O('Patrons needed for your target', 'int', 'MAX(0,ROUNDUP({in:patron}*%s,0)-%s)' % (ALLM, LV_('Patron'))),
    O('Verdict', 'text', 'IF(%s<{in:patron},%s&" "&%s,IF(%s<{in:supporter},%s&" "&%s,%s))' % ('IF(%s>0,%s/%s,0)' % (ALLM, LV_('Patron'), ALLM), ck('Grow'), tok('mlevel', 'Patron'), 'IF(%s>0,%s/%s,0)' % (ALLM, LV_('Supporter'), ALLM), ck('Grow'), tok('mlevel', 'Supporter'), ck('Fine')))],
    GR('What if', ('Fewer Patrons wanted', {'patron': 0.05}), ('More Supporters wanted', {'supporter': 0.5}), ('Both targets low', {'patron': 0.05, 'supporter': 0.2}))))
assert len(tools) == 18, len(tools)
