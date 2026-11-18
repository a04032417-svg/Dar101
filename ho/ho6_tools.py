"""Home Management suite part 6: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho6_lists import *
import ho6_data as D
from ho6_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dflt): return IN(k, label, 'list', key(lst, dflt), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def V(*parts):
    out = []
    for p in parts:
        if isinstance(p, tuple): out.append('(' + p[1] + ')')
        else: out.append(lbl(p))
    return '&" "&'.join(out)
def F(x): return ('f', x)
def GZ(cnt, expr): return 'IF(%s=0,"",%s)' % (cnt, expr)
def PCT(x): return 'ROUND(%s*100,0)&"%%"' % x
def WD(col, a, b): return '%s,">="&%s,%s,"<="&%s' % (col, a, col, b)     # date column inside [a, b]
def INX(rng, row): return 'INDEX(%s,%s)' % (rng, row)

tools = []

# 1 -------------------------------------------------------------- conflict finder this week
N1 = 'COUNTIFS(%s,">=0",%s,"<"&{in:within})' % (CFR('days_to'), CFR('days_to'))
def C1(c): return 'IF(%s=0,"",INDEX(%s,1))' % (N1, CFR(c))
tools.append(TOOL('conflict_week', 'Conflict Finder Tool', 'Conflict finder: overlaps and double-booked drivers',
    'Type how many days ahead to look. Events that overlap for the same person or the same driver are counted, the first one is named with both events and the adults free from the work pattern.', [
    I('within', 'Look this many days ahead', 14)], [
    O('Conflicts in the window', 'int', N1),
    O('Of these, a driver double-booked', 'int', 'COUNTIFS(%s,%s,%s,">=0",%s,"<"&{in:within})' % (CFR('type'), lbl('Driver double-booked'), CFR('days_to'), CFR('days_to'))),
    O('Of these, a person double-booked', 'int', 'COUNTIFS(%s,%s,%s,">=0",%s,"<"&{in:within})' % (CFR('type'), lbl('Person double-booked'), CFR('days_to'), CFR('days_to'))),
    O('First conflict in, days', 'int', C1('days_to')), O('First event', 'text', C1('event_a') + '&""'), O('Starts', 'time', C1('a_start')), O('Second event', 'text', C1('event_b') + '&""'),
    O('Starts', 'time', C1('b_start')), O('Overlap, minutes', 'int', C1('overlap')), O('Adults free that evening', 'int', C1('free')), O('What to do', 'text', C1('advice') + '&""'),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (N1, lbl('Clear'), V('Conflict in', F(C1('days_to')), 'days:', F(C1('event_a')), 'and', F(C1('event_b')), 'with adults free', F(C1('free')))))],
    GR('What if you look further ahead', ('14 days', {'within': 14}), ('21 days', {'within': 21}), ('30 days', {'within': 30}), ('60 days', {'within': 60}), ('90 days', {'within': 90}))))

# 2 -------------------------------------------------------------- next week's driving
WIN2 = '%s' % (WD(ER('date'), '{in:start}', '({in:start}+{in:days}-1)'))
def DC2(d): return 'COUNTIFS(%s,%s,%s)' % (ER('driver'), d, WIN2)
TOT2 = '(' + '+'.join(DC2(d) for d in (D_A1, D_A2, D_GP, D_CP, D_WB)) + ')'
tools.append(TOOL('next_drive', 'Next Week Driving Tool', 'Who drives which activity in the next days',
    'Type the first day and how many days: trips by driver, the minutes adult 2 drives, the lifts that need a carpool family and the evenings with no free adult from the work pattern.', [
    I('start', 'First day', 'today', 'date'), I('days', 'Days to look at', 7)], [
    O('Trips with a driver', 'int', TOT2), O('Adult 1 drives', 'int', DC2(D_A1)), O('Adult 2 drives', 'int', DC2(D_A2)), O('Grandparent drives', 'int', DC2(D_GP)), O('Carpool family drives', 'int', DC2(D_CP)),
    O('Walk or bike', 'int', DC2(D_WB)), O('Event minutes driven by adult 2', 'int', 'SUMIFS(%s,%s,%s,%s)' % (ER('minutes'), ER('driver'), D_A2, WIN2)),
    O('Evenings with no adult free', 'int', 'COUNTIFS(%s,%s,0)' % (WD(SR('date'), '{in:start}', '({in:start}+{in:days}-1)'), SR('adults_free'))),
    O('Evenings with one adult free', 'int', 'COUNTIFS(%s,%s,1)' % (WD(SR('date'), '{in:start}', '({in:start}+{in:days}-1)'), SR('adults_free'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (TOT2, lbl('No trips in this window'), V('Adult 2 drives', F(DC2(D_A2)), 'of', F(TOT2), 'trips,', F(DC2(D_CP)), 'trips need a carpool')))],
    GR('What if you look at a longer span', ('3 days', {'days': 3}), ('7 days', {'days': 7}), ('14 days', {'days': 14}), ('21 days', {'days': 21}), ('30 days', {'days': 30}))))

# 3 -------------------------------------------------------------- double-booked driver finder
N3 = 'COUNTIFS(%s,{in:driver},%s,">0",%s,">="&{today},%s,"<="&({today}+{in:within}))' % (ER('driver'), ER('dclash'), ER('date'), ER('date'))
MK3 = 'MINIFS(%s,%s,{in:driver},%s,">0",%s,"<="&({today}+{in:within}))' % (ER('ckey'), ER('driver'), ER('dclash'), ER('date'))
IX3 = 'MOD(%s,2000)' % MK3
def E3(c): return 'IF(%s=0,"",INDEX(%s,%s))' % (N3, ER(c), IX3)
ALL3 = 'COUNTIFS(%s,{in:driver},%s,">="&{today},%s,"<="&({today}+{in:within}))' % (ER('driver'), ER('date'), ER('date'))
tools.append(TOOL('double_driver', 'Double Booked Driver Finder', 'Find a driver booked for two events at once',
    'Pick a driver and a window: the events where the same driver has two overlapping lifts, the first one named with its start, its place and how many adults are free that day.', [
    IL('driver', 'Driver', 'driver', 'Adult 2'), I('within', 'Look this many days ahead', 30)], [
    O('Events with a double-booked driver', 'int', N3), O('All events of this driver in the window', 'int', ALL3), O('Share of the driver events that clash', 'pct', 'IF(%s=0,0,ROUND(%s/%s,3))' % (ALL3, N3, ALL3)),
    O('First one in, days', 'int', 'IF(%s=0,"",INT(%s/10000000))' % (N3, MK3)), O('First event', 'text', E3('title') + '&""'), O('Starts', 'time', E3('start')), O('Place', 'text', E3('place') + '&""'), O('Adults free that day', 'int', E3('free')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (N3, lbl('No double-booked driver'), V('Find a second driver in', F('INT(%s/10000000)' % MK3), 'days for', F(E3('title')))))],
    GR('What if you look further ahead', ('14 days', {'within': 14}), ('21 days', {'within': 21}), ('30 days', {'within': 30}), ('60 days', {'within': 60}), ('90 days', {'within': 90}))))

# 4 -------------------------------------------------------------- busiest week ahead
BUSYROW = 'MATCH(1,%s,0)' % BR('rank')
QUIROW = 'MATCH(MIN(%s),%s,0)' % (BR('total'), BR('total'))
HAS4 = 'COUNT(%s)' % BR('total')
tools.append(TOOL('busiest_week', 'Busiest Week Tool', 'The busiest and the quietest week of the next 12',
    'Events and maintenance tasks per week for 12 weeks: type the number of items you call a heavy week and read the busiest week, the quietest week and how many weeks are heavy.', [
    I('heavy', 'A heavy week has this many items', 12)], [
    O('Weeks with this many items or more', 'int', 'COUNTIFS(%s,">="&{in:heavy})' % BR('total')), O('Busiest week, number', 'int', 'IFERROR(INDEX(%s,%s),"")' % (BR('no'), BUSYROW)),
    O('Items in the busiest week', 'int', 'IFERROR(INDEX(%s,%s),"")' % (BR('total'), BUSYROW)), O('Evening events there', 'int', 'IFERROR(INDEX(%s,%s),"")' % (BR('evenings'), BUSYROW)),
    O('Quietest week, number', 'int', 'IFERROR(INDEX(%s,%s),"")' % (BR('no'), QUIROW)), O('Items in the quietest week', 'int', 'IF(%s=0,"",MIN(%s))' % (HAS4, BR('total'))),
    O('Average items a week', 'num', 'IF(%s=0,"",ROUND(AVERAGE(%s),1))' % (HAS4, BR('total'))), O('Items in the next 12 weeks', 'int', 'SUM(%s)' % BR('total')),
    O('Verdict', 'text', 'IF(%s=0,"",%s)' % (HAS4, V('Week', F('INDEX(%s,%s)' % (BR('no'), BUSYROW)), 'has', F('INDEX(%s,%s)' % (BR('total'), BUSYROW)), 'items, the quietest is week', F('INDEX(%s,%s)' % (BR('no'), QUIROW)))))],
    GR('What if a heavy week is lower or higher', ('8 items', {'heavy': 8}), ('10 items', {'heavy': 10}), ('12 items', {'heavy': 12}), ('14 items', {'heavy': 14}), ('16 items', {'heavy': 16}))))

# 5 -------------------------------------------------------------- free evenings
WIN5 = WD(SR('date'), '{today}', '({today}+7*{in:weeks}-1)')
N5 = 'COUNTIFS(%s,%s,2)' % (WIN5, SR('adults_free'))
NXT5 = 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (SR('both_date'), SR('both_date'))
tools.append(TOOL('free_evenings', 'Free Evenings Tool', 'Evenings when both adults are free',
    'Type the weeks to look at: evenings with both adults free, with one adult and with none from the work pattern, and the evenings free of any event as well.', [
    I('weeks', 'Weeks to look at', 4)], [
    O('Evenings with both adults free', 'int', N5), O('Evenings with one adult free', 'int', 'COUNTIFS(%s,%s,1)' % (WIN5, SR('adults_free'))), O('Evenings with no adult free', 'int', 'COUNTIFS(%s,%s,0)' % (WIN5, SR('adults_free'))),
    O('Both free and no evening event', 'int', 'COUNTIFS(%s,%s,2,%s,0)' % (WIN5, SR('adults_free'), SR('evening_n'))), O('Next evening with both free, days', 'int', 'IF(%s="","",%s-{today})' % (NXT5, NXT5)),
    O('Share of evenings with both free', 'pct', 'IF({in:weeks}=0,0,ROUND(%s/(7*{in:weeks}),3))' % N5), O('Babysitter to ask', 'text', TLR('Babysitter', 'short')), O('Babysitter phone', 'text', TLR('Babysitter', 'phone')),
    O('Verdict', 'text', V(F(N5), 'evenings with both adults free'))],
    GR('What if you look further ahead', ('1 week', {'weeks': 1}), ('2 weeks', {'weeks': 2}), ('4 weeks', {'weeks': 4}), ('8 weeks', {'weeks': 8}), ('12 weeks', {'weeks': 12}))))

# 6 -------------------------------------------------------------- school days left
CURROW = 'MATCH(1,%s,0)' % TR('cur')
YEND = 'IFERROR(SMALL(%s,1),"")' % TR('sumend')
LEFT6 = 'SUMIFS(%s,%s,1)' % (TR('left_days'), TR('cur'))
tools.append(TOOL('school_left', 'School Days Left Tool', 'School days left this term and this school year',
    'Type the days you plan to be away in term time: the school days left in the term and in the school year (weekdays less the breaks), the end dates and the weeks of school left.', [
    I('days_off', 'Days off you plan in term time', 5)], [
    O('Current term', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (TR('term'), CURROW)), O('School days left this term', 'int', LEFT6), O('The term ends on', 'date', 'IFERROR(INDEX(%s,%s),"")' % (TR('end'), CURROW)),
    O('School year ends on', 'date', YEND), O('School days left this school year', 'int', 'IF(%s="",0,SUMIFS(%s,%s,"<="&%s))' % (YEND, TR('left_days'), TR('end'), YEND)),
    O('Left this term after your days off', 'int', 'MAX(0,%s-{in:days_off})' % LEFT6), O('Weeks of school left this term', 'num', 'ROUND(%s/5,1)' % LEFT6),
    O('Verdict', 'text', V(F('MAX(0,%s-{in:days_off})' % LEFT6), 'school days left this term'))],
    GR('What if you take more days off', ('0 days', {'days_off': 0}), ('2 days', {'days_off': 2}), ('5 days', {'days_off': 5}), ('8 days', {'days_off': 8}), ('10 days', {'days_off': 10}))))

# 7 -------------------------------------------------------------- days to the next break
BK7 = 'IFERROR(SMALL(%s,1),"")' % TR('bk')
BR7 = 'MATCH(%s,%s,0)' % (BK7, TR('bk'))
def B7(c): return 'IF(%s="","",INDEX(%s,%s))' % (BK7, TR(c), BR7)
tools.append(TOOL('next_break', 'Next Break Tool', 'Days to the next school break',
    'Type how many days before a break you want child care booked: the next break from the term table, its dates, the days to it and the child-care gap days it holds.', [
    I('lead', 'Book child care this many days before', 21)], [
    O('Next break', 'text', B7('term') + '&""'), O('Starts on', 'date', BK7), O('Ends on', 'date', B7('end')), O('Days to the break', 'int', 'IF(%s="","",%s-{today})' % (BK7, BK7)), O('Length, days', 'int', B7('days')),
    O('Child-care gap days', 'int', B7('gap_days')), O('Book care by', 'date', 'IF(%s="","",%s-{in:lead})' % (BK7, BK7)), O('Days to book care by, negative is past', 'int', 'IF(%s="","",%s-{in:lead}-{today})' % (BK7, BK7)),
    O('Verdict', 'text', 'IF(%s="",%s,%s)' % (BK7, lbl('No break ahead'), V(F(B7('term') + '&""'), 'starts in', F('%s-{today}' % BK7), 'days')))],
    GR('What if you book earlier or later', ('7 days', {'lead': 7}), ('14 days', {'lead': 14}), ('21 days', {'lead': 21}), ('28 days', {'lead': 28}), ('42 days', {'lead': 42}))))

# 8 -------------------------------------------------------------- child-care gap days
ST8 = 'MINIFS(%s,%s,{in:break_term},%s,%s)' % (TR('upc'), TR('term'), TR('kind'), T_BREAK)
HAS8 = 'COUNTIFS(%s,{in:break_term},%s,%s,%s,">0")' % (TR('term'), TR('kind'), T_BREAK, TR('upc'))
GAP8 = 'SUMIFS(%s,%s,{in:break_term},%s,%s)' % (TR('gap_days'), TR('term'), TR('upc'), ST8)
WDY8 = 'SUMIFS(%s,%s,{in:break_term},%s,%s)' % (TR('wdays'), TR('term'), TR('upc'), ST8)
tools.append(TOOL('gap_days', 'Child Care Gap Days Tool', 'Break days with no activity or visit typed',
    'Pick a break and the days relatives can cover: the weekdays of the break, the days with nothing on the calendar, the days left to cover and the share already covered.', [
    IL('break_term', 'School break', 'tname', 'Summer break'), I('help', 'Days a relative or friend can cover', 3)], [
    O('Break starts on', 'date', 'IF(%s=0,"",%s)' % (HAS8, ST8)), O('Days to the break', 'int', 'IF(%s=0,"",MAX(0,%s-{today}))' % (HAS8, ST8)), O('Weekdays in the break', 'int', 'IF(%s=0,"",%s)' % (HAS8, WDY8)),
    O('Gap days with nothing typed', 'int', 'IF(%s=0,"",%s)' % (HAS8, GAP8)), O('Gap days left after the help', 'int', 'IF(%s=0,"",MAX(0,%s-{in:help}))' % (HAS8, GAP8)),
    O('Share of the weekdays already covered', 'pct', 'IF(%s=0,0,IF(%s=0,0,ROUND(1-%s/%s,3)))' % (HAS8, WDY8, GAP8, WDY8)),
    O('Grandparent to ask', 'text', TLR('Grandparent', 'short')), O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (HAS8, lbl('No such break ahead'), V(F(GAP8), 'gap days in', F('{in:break_term}'))))],
    GR('What if more days are covered', ('No help', {'help': 0}), ('2 days', {'help': 2}), ('4 days', {'help': 4}), ('6 days', {'help': 6}), ('8 days', {'help': 8}))))

# 9 -------------------------------------------------------------- carpool rota planner
WS9 = 'MAX(0,INT(({today}-{in:start})/7))'
CUR9 = '(MOD(%s,{in:families})+1)' % WS9
WAIT9 = 'MOD({in:position}-%s,{in:families})' % CUR9
tools.append(TOOL('carpool_rota', 'Carpool Rota Planner', 'Your turn in the carpool rota',
    'Type the families in the rota, your place, the first week of the rota and the lifts a turn holds: whose turn it is, when yours comes and how many lifts you drive over the weeks.', [
    I('families', 'Families in the rota', 4), I('position', 'Your place in the rota', 2), I('start', 'First week of the rota starts on', 'today-14', 'date'), I('lifts', 'Lifts in one turn', 2), I('weeks', 'Weeks to plan', 12)], [
    O('Whose turn it is now', 'int', CUR9), O('Weeks until your turn, 0 is this week', 'int', WAIT9), O('Your next turn starts on', 'date', '{in:start}+7*(%s+%s)' % (WS9, WAIT9)),
    O('Your turns in the weeks planned', 'int', 'IF(%s>{in:weeks}-1,0,INT(({in:weeks}-1-%s)/{in:families})+1)' % (WAIT9, WAIT9)),
    O('Lifts you drive in the weeks planned', 'int', '{in:lifts}*IF(%s>{in:weeks}-1,0,INT(({in:weeks}-1-%s)/{in:families})+1)' % (WAIT9, WAIT9)),
    O('Carpool lifts typed in the next 4 weeks', 'int', 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<"&({today}+28))' % (ER('carpool'), YES, ER('date'), ER('date'))), O('Carpool family to message', 'text', TLR('Carpool family', 'short')),
    O('Verdict', 'text', V('Your turn', F('{in:position}'), 'of', F('{in:families}'), ', next in', F('MAX(0,{in:start}+7*(%s+%s)-{today})' % (WS9, WAIT9)), 'days'))],
    GR('What if the rota has more families', ('2 families', {'families': 2, 'position': 2}), ('3 families', {'families': 3}), ('4 families', {'families': 4}), ('5 families', {'families': 5}), ('6 families', {'families': 6}))))

# 10 ------------------------------------------------------------- driving fairness
A1T, A2T = tok('adult', 'Adult 1'), tok('adult', 'Adult 2')
def DS(c, a): return 'SUMIFS(%s,%s,%s,%s,"<="&{in:weeks})' % (DR(c), DR('adult'), a, DR('weeks_ago'))
SUM10 = '(%s+%s)' % (DS('trips', A1T), DS('trips', A2T))
SH10 = '(%s/%s)' % (DS('trips', A2T), SUM10)
tools.append(TOOL('fairness', 'Driving Fairness Tool', 'Trips and minutes driven by each adult against an even split',
    'Type the weeks to look at and the share you agreed: trips and event minutes for each adult, the share of adult 2 and how far it is from the agreed share; a view for a talk, not a score.', [
    I('weeks', 'Complete weeks to look back, 1 to 12', 4), I('agreed', 'Agreed share for adult 2', 0.5, 'pct')], [
    O('Trips adult 1', 'int', DS('trips', A1T)), O('Trips adult 2', 'int', DS('trips', A2T)), O('Event minutes adult 1', 'int', DS('minutes', A1T)), O('Event minutes adult 2', 'int', DS('minutes', A2T)),
    O('Share of the trips, adult 2', 'pct', 'IF(%s=0,"",ROUND(%s,3))' % (SUM10, SH10)), O('Agreed share', 'pct', '{in:agreed}'), O('Points from the agreed share', 'int', 'IF(%s=0,"",ROUND((%s-{in:agreed})*100,0))' % (SUM10, SH10)),
    O('Reading', 'text', 'IF(%s=0,"",IF(ABS(%s-{in:agreed})<={set:fair_margin},%s,IF(%s>{in:agreed},%s,%s)))' % (SUM10, SH10, lbl('Even within the margin'), SH10, lbl('Adult 2 drives more'), lbl('Adult 1 drives more'))),
    O('Verdict', 'text', 'IF(%s=0,"",%s)' % (SUM10, V('Adult 2 drives', F(PCT(SH10)), 'of trips')))],
    GR('What if you look back further', ('2 weeks', {'weeks': 2}), ('4 weeks', {'weeks': 4}), ('8 weeks', {'weeks': 8}), ('12 weeks', {'weeks': 12}), ('4 weeks, agreed 60%', {'weeks': 4, 'agreed': 0.6}))))

# 11 ------------------------------------------------------------- birthdays and gifts
W11 = WD(GR_('date'), '{today}', '({today}+{in:window})')
N11 = 'COUNTIFS(%s)' % W11
NXT11 = 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (GR_('date'), GR_('date'))
tools.append(TOOL('gifts60', 'Birthdays And Gifts Tool', 'Birthdays and gifts in the next days',
    'Type the window in days: the dates inside it, the gifts still an idea, bought, wrapped and given, the cost lines and the next name and date; names and dates only.', [
    I('window', 'Look this many days ahead', 60)], [
    O('Dates in the window', 'int', N11), O('Gifts still an idea', 'int', 'COUNTIFS(%s,%s,%s)' % (W11, GR_('status'), G_IDEA)), O('Gifts bought', 'int', 'COUNTIFS(%s,%s,%s)' % (W11, GR_('status'), G_BOUGHT)),
    O('Gifts wrapped', 'int', 'COUNTIFS(%s,%s,%s)' % (W11, GR_('status'), G_WRAP)), O('Gifts given', 'int', 'COUNTIFS(%s,%s,%s)' % (W11, GR_('status'), G_GIVEN)),
    O('Cost lines in the window', 'money', 'SUMIFS(%s,%s)' % (GR_('cost'), W11)), O('Next date, name', 'text', 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0))&"")' % (NXT11, GR_('name'), NXT11, GR_('date'))),
    O('Next date, days', 'int', 'IF(%s="","",%s-{today})' % (NXT11, NXT11)), O('Next date, status', 'text', 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0))&"")' % (NXT11, GR_('status'), NXT11, GR_('date'))),
    O('Verdict', 'text', V(F('COUNTIFS(%s,%s,%s)' % (W11, GR_('status'), G_IDEA)), 'gifts to buy in the next', F('{in:window}'), 'days'))],
    GR('What if you look further ahead', ('14 days', {'window': 14}), ('30 days', {'window': 30}), ('45 days', {'window': 45}), ('60 days', {'window': 60}), ('90 days', {'window': 90}))))

# 12 ------------------------------------------------------------- visitors clash and beds
LV12 = '({in:arrive}+{in:nights})'
OV12 = 'COUNTIFS(%s,"<"&%s,%s,">"&{in:arrive})' % (VSR('arrive'), LV12, VSR('leave'))
USED12 = 'SUMIFS(%s,%s,"<"&%s,%s,">"&{in:arrive})' % (VSR('beds'), VSR('arrive'), LV12, VSR('leave'))
OVER12 = 'MAX(0,%s+{in:guests}-{in:beds})' % USED12
tools.append(TOOL('visitors_beds', 'Visitors Clash And Beds Tool', 'Does a new stay fit the beds and the other stays',
    'Type the arrival, the nights, the guests and the beds you have: the stays that overlap, the beds they use, how many beds you are over and the dinners to add.', [
    I('arrive', 'Arrival date', 'today+30', 'date'), I('nights', 'Nights', 4), I('guests', 'Beds the new guests need', 2), I('beds', 'Beds you have for visitors', 4)], [
    O('Leaves on', 'date', LV12), O('Stays that overlap', 'int', OV12), O('Beds used by those stays', 'int', USED12), O('Beds free for the new stay', 'int', '{in:beds}-%s' % USED12), O('Over the beds by', 'int', OVER12),
    O('Dinners to add', 'int', '{in:guests}*{in:nights}'), O('Stays already over the beds typed', 'int', 'COUNTIFS(%s,">0")' % VSR('over_by')), O('Most beds in use on an arrival', 'int', 'MAX(%s)' % VSR('at_arr')),
    O('Verdict', 'text', 'IF(%s>0,%s,IF(%s>0,%s,%s))' % (OVER12, V('Over by', F(OVER12), 'beds'), OV12, V('Clash with', F(OV12), 'stays, beds fit'), lbl('Fits')))],
    GR('What if more guests come', ('1 bed', {'guests': 1}), ('2 beds', {'guests': 2}), ('3 beds', {'guests': 3}), ('4 beds', {'guests': 4}), ('6 beds', {'guests': 6}))))

# 13 ------------------------------------------------------------- pet care next due
NK13 = 'MINIFS(%s,%s,{in:task})' % (PSR('nk'), PSR('task'))
HAS13 = 'COUNTIFS(%s,{in:task},%s,">0")' % (PSR('task'), PSR('nk'))
D13 = 'INT(%s/100)' % NK13
PET13 = 'INDEX(%s,MATCH(%s,%s,0))' % (PSR('pet'), NK13, PSR('nk'))
tools.append(TOOL('pet_next', 'Pet Care Next Due Tool', 'The next care date of a task, dates only',
    'Pick a care task and a window: the pet and the date of the next one from the interval and the last date, the days left and the care dates and overdue dates of all pets; no treatments, dates only.', [
    IL('task', 'Care task', 'ptask', 'Grooming'), I('within', 'Count care dates in the next days', 30)], [
    O('Pet', 'text', 'IF(%s=0,"",%s&"")' % (HAS13, PET13)), O('Next due', 'date', 'IF(%s=0,"",%s)' % (HAS13, D13)), O('Days left, negative is overdue', 'int', 'IF(%s=0,"",%s-{today})' % (HAS13, D13)),
    O('Overdue for this task', 'int', 'COUNTIFS(%s,{in:task},%s,%s)' % (PSR('task'), PSR('status'), W_OVD)), O('Care dates of all pets in the window', 'int', 'COUNTIFS(%s,">=0",%s,"<="&{in:within})' % (PSR('days_left'), PSR('days_left'))),
    O('All overdue dates', 'int', 'COUNTIFS(%s,%s)' % (PSR('status'), W_OVD)), O('Vet clinic to ask', 'text', TLR('Vet clinic', 'short')),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<{today},%s,%s))' % (HAS13, lbl('No date typed for this task'), D13, V(F('{in:task}'), 'for', F(PET13), 'is overdue by', F('{today}-%s' % D13), 'days'), V(F('{in:task}'), 'for', F(PET13), 'in', F('%s-{today}' % D13), 'days')))],
    GR('What if you count a longer window', ('14 days', {'within': 14}), ('30 days', {'within': 30}), ('60 days', {'within': 60}), ('90 days', {'within': 90}), ('180 days', {'within': 180}))))

# 14 ------------------------------------------------------------- pet food days left
DAYS14 = 'IF({in:daily}=0,"",INT(MAX(0,{in:bag}*1000-{in:opened}*{in:daily})/{in:daily}))'
tools.append(TOOL('pet_food_tool', 'Pet Food Days Left Tool', 'Pet food stock in days and the reorder date',
    'Type the bag size, the daily amount, how many days ago the bag was opened and how early to reorder: the days of food left, the day it runs out and the day to reorder.', [
    I('bag', 'Bag size, kg', 12, 'num'), I('daily', 'Daily amount, grams', 320), I('opened', 'Bag opened this many days ago', 10), I('reorder', 'Reorder this many days before it runs out', 14)], [
    O('Food left, kg', 'num', 'MAX(0,ROUND({in:bag}-{in:opened}*{in:daily}/1000,1))'), O('Days of food left', 'int', DAYS14), O('Runs out on', 'date', 'IF(%s="","",{today}+%s)' % (DAYS14, DAYS14)),
    O('Reorder by', 'date', 'IF(%s="","",{today}+%s-{in:reorder})' % (DAYS14, DAYS14)), O('Days to reorder, negative is past', 'int', 'IF(%s="","",%s-{in:reorder})' % (DAYS14, DAYS14)),
    O('Lowest days left in the Pet food stock table', 'int', 'IF(COUNT(%s)=0,"",MIN(%s))' % (PFR('days_left'), PFR('days_left'))),
    O('Verdict', 'text', 'IF(%s="","",IF(%s<={in:reorder},%s,%s))' % (DAYS14, DAYS14, V('Reorder now,', F(DAYS14), 'days left'), V('Reorder in', F('%s-{in:reorder}' % DAYS14), 'days,', F(DAYS14), 'days left')))],
    GR('What if the daily amount changes', ('70 grams', {'daily': 70}), ('150 grams', {'daily': 150}), ('250 grams', {'daily': 250}), ('320 grams', {'daily': 320}), ('400 grams', {'daily': 400}))))

# 15 ------------------------------------------------------------- vehicle renewals next 90 days
def NXD(c): return 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),99999)' % (VDR(c), VDR(c))
A15, I15, R15 = NXD('adt'), NXD('ins'), NXD('reg')
M15 = 'MIN(%s,%s,%s)' % (A15, I15, R15)
KIND15 = 'IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (M15, A15, lbl('Annual test'), M15, I15, lbl('Insurance renewal'), lbl('Registration renewal'))
VEH15 = 'IF(%s=%s,INDEX(%s,MATCH(%s,%s,0)),IF(%s=%s,INDEX(%s,MATCH(%s,%s,0)),INDEX(%s,MATCH(%s,%s,0))))' % (M15, A15, VDR('vehicle'), A15, VDR('adt'), M15, I15, VDR('vehicle'), I15, VDR('ins'), VDR('vehicle'), R15, VDR('reg'))
def W15(c): return 'COUNTIFS(%s,">=0",%s,"<="&{in:within})' % (VDR(c), VDR(c))
tools.append(TOOL('vehicle_renew', 'Vehicle Renewals Tool', 'Annual test, insurance and registration dates ranked',
    'Type the window in days: the annual test, insurance and registration dates inside it, the next one of the three with its vehicle and the days left, and the dates already overdue.', [
    I('within', 'Look this many days ahead', 90)], [
    O('Renewal dates in the window', 'int', '%s+%s+%s' % (W15('adt'), W15('ins'), W15('reg'))), O('Annual tests', 'int', W15('adt')), O('Insurance renewals', 'int', W15('ins')), O('Registration renewals', 'int', W15('reg')),
    O('Overdue vehicle dates', 'int', 'COUNTIFS(%s,%s)' % (VDR('status'), W_OVD)), O('Next renewal', 'text', 'IF(%s=99999,"",%s)' % (M15, KIND15)), O('For vehicle', 'text', 'IF(%s=99999,"",%s&"")' % (M15, VEH15)),
    O('Days to it', 'int', 'IF(%s=99999,"",%s)' % (M15, M15)), O('Car mechanic', 'text', TLR('Car mechanic', 'short')),
    O('Verdict', 'text', 'IF(%s=99999,"",%s)' % (M15, V(F(KIND15), 'for', F(VEH15), 'in', F(M15), 'days')))],
    GR('What if you look further ahead', ('30 days', {'within': 30}), ('45 days', {'within': 45}), ('60 days', {'within': 60}), ('90 days', {'within': 90}), ('180 days', {'within': 180}))))

# 16 ------------------------------------------------------------- next vehicle service
KL16 = '({in:last_km}+{in:interval_km}-{in:km_now})'
DK16 = 'IF({in:rate}=0,"",ROUND(MAX(0,%s)/{in:rate},0))' % KL16
BYT16 = '({in:last_date}+{in:interval_days})'
DAYS16 = 'IF(%s="",%s-{today},MIN(%s,%s-{today}))' % (DK16, BYT16, DK16, BYT16)
tools.append(TOOL('next_service', 'Next Vehicle Service Tool', 'Next service by mileage or date, whichever is first',
    'Type the mileage now, the mileage and date of the last service, the km a day and the interval you use (typical, check the manual): the km left, the two dates and the one that comes first.', [
    I('km_now', 'Mileage now, km', 41800), I('last_km', 'Mileage at the last service, km', 36200), I('last_date', 'Date of the last service', 'today-150', 'date'), I('rate', 'Km driven a day', 35),
    I('interval_km', 'Service interval, km (typical)', 12000), I('interval_days', 'Service interval, days (typical)', 365)], [
    O('Km to the next service', 'int', KL16), O('Days by mileage', 'int', DK16), O('Date by mileage', 'date', 'IF(%s="","",{today}+%s)' % (DK16, DK16)), O('Date by the calendar', 'date', BYT16),
    O('Service by, days from now', 'int', DAYS16), O('Service by', 'date', '{today}+%s' % DAYS16), O('Mileage at that date', 'int', '{in:km_now}+{in:rate}*MAX(0,%s)' % DAYS16),
    O('Which comes first', 'text', 'IF(%s="",%s,IF(%s<=%s-{today},%s,%s))' % (DK16, lbl('The date comes first'), DK16, BYT16, lbl('Mileage comes first'), lbl('The date comes first'))),
    O('Verdict', 'text', V('Service in', F(DAYS16), 'days or at', F('{in:last_km}+{in:interval_km}'), 'km, whichever comes first'))],
    GR('What if you drive more or less', ('20 km a day', {'rate': 20}), ('35 km a day', {'rate': 35}), ('50 km a day', {'rate': 50}), ('80 km a day', {'rate': 80}), ('120 km a day', {'rate': 120}))))

# 17 ------------------------------------------------------------- trip moved by two weeks
NS17 = '({in:trip}+{in:shift})'
NE17 = '(%s+{in:days}-1)' % NS17
EV17 = 'COUNTIFS(%s,"<="&%s,%s,">="&%s,%s,"<>"&%s)' % (ER('date'), NE17, ER('end_date'), NS17, ER('kind'), K_TRIP)
DT17 = '(COUNTIFS(%s)+COUNTIFS(%s))' % (WD(VDR('date'), NS17, NE17), WD(PSR('next_due'), NS17, NE17))
tools.append(TOOL('trip_move', 'Trip Moved Tool', 'What clashes when the family trip moves by some days',
    'Type the trip and the days to move it: the new dates, the calendar events that now fall inside it, the birthdays and the vehicle and pet dates that land on the trip; dates only.', [
    I('trip', 'First day of the trip', 'today+70', 'date'), I('days', 'Days away', 8), I('shift', 'Move the trip by, days', 14)], [
    O('New first day', 'date', NS17), O('New last day', 'date', NE17), O('Calendar events that now clash', 'int', EV17), O('Birthdays and gift dates inside the new trip', 'int', 'COUNTIFS(%s)' % WD(GR_('date'), NS17, NE17)),
    O('Vehicle and pet dates inside the new trip', 'int', DT17), O('Weekdays away', 'int', 'NETWORKDAYS(%s,%s)' % (NS17, NE17)), O('Days to the new first day', 'int', '%s-{today}' % NS17),
    O('Visitors arriving during the new trip', 'int', 'COUNTIFS(%s,"<="&%s,%s,">="&%s)' % (VSR('arrive'), NE17, VSR('leave'), NS17)),
    O('Verdict', 'text', V(F(EV17), 'events clash,', F(DT17), 'dates to check'))],
    GR('What if the trip moves by other days', ('Not moved', {'shift': 0}), ('1 week', {'shift': 7}), ('2 weeks', {'shift': 14}), ('3 weeks', {'shift': 21}), ('6 weeks', {'shift': 42}))))

# 18 ------------------------------------------------------------- calendar against own history
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def MC(k): return 'COUNTIFS(%s,">="&EDATE(%s,%d),%s,"<"&EDATE(%s,%d))' % (ER('date'), MS, k, ER('date'), MS, k + 1)
AVG18 = '(%s+%s+%s)/3' % (MC(-1), MC(-2), MC(-3))
tools.append(TOOL('history', 'Calendar Against History Tool', 'Events this month against the 3 complete months before it',
    'Type how far from the usual counts as busier or quieter: the events of this month, each of the 3 complete months before it, the average and the ratio.', [
    I('margin', 'Busier or quieter beyond this margin', 0.2, 'pct')], [
    O('Events this month', 'int', MC(0)), O('Last month', 'int', MC(-1)), O('2 months ago', 'int', MC(-2)), O('3 months ago', 'int', MC(-3)), O('Average of the 3 months', 'num', 'ROUND(%s,1)' % AVG18),
    O('This month against the average', 'pct', 'IF(%s=0,0,ROUND(%s/(%s),3))' % (AVG18, MC(0), AVG18)), O('Evening events this month', 'int', 'COUNTIFS(%s,">="&%s,%s,"<"&EDATE(%s,1),%s,">="&{set:evening_hour}*60)' % (ER('date'), MS, ER('date'), MS, ER('sm'))),
    O('Verdict', 'text', 'IF(%s=0,"",IF(%s>=(%s)*(1+{in:margin}),%s,IF(%s<=(%s)*(1-{in:margin}),%s,%s)))' % (AVG18, MC(0), AVG18, lbl('Busier than usual'), MC(0), AVG18, lbl('Quieter than usual'), lbl('In line with usual')))],
    GR('What if the margin changes', ('10 points', {'margin': 0.1}), ('20 points', {'margin': 0.2}), ('30 points', {'margin': 0.3}), ('40 points', {'margin': 0.4}), ('50 points', {'margin': 0.5}))))

assert len(tools) == 18, len(tools)
