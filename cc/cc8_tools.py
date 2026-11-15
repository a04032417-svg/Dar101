"""Childcare center suite part 8: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc8_lists import *
from cc8_tables import MS, WN, SN, RT


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def AVG(t, c, n): return '((%s)/%d)' % (SN(t, c, n), n)
def RMS(col, room, n): return 'SUMIFS({range:room_months.%s},{range:room_months.room},%s,%s)' % (col, room, WN('room_months', n))
def TK(lst, label): return tok(lst, label)
def GL(lst, label): return '=' + tok(lst, label)

REV3 = AVG('pnl', 'revenue', 3); FOOD3 = AVG('pnl', 'food', 3); STAFF3 = AVG('pnl', 'staff_pay', 3); OWN3 = AVG('pnl', 'owner_pay', 3); RENT3 = AVG('pnl', 'rent', 3); OTH3 = AVG('pnl', 'other_costs', 3)
PROFIT3 = AVG('pnl', 'profit', 3); COST3 = AVG('pnl', 'costs', 3)
FIX3 = '(%s+%s+%s+%s)' % (STAFF3, OWN3, RENT3, OTH3)
CH3 = AVG('room_months', 'enrolled', 3)
PLACES = 'SUM({range:rooms.capacity})'
HOURLY = tok('paytype', 'Hourly')
STAFFH = 'IFERROR(SUMIFS({range:payroll.total},{range:payroll.pay_type},%s)/SUMIFS({range:payroll.hours},{range:payroll.pay_type},%s),0)' % (HOURLY, HOURLY)
FD = tok('schedule', '5 full days')
CASH_LAST = 'IFERROR(INDEX({range:cash.closing},MATCH(EDATE(%s,-1),{range:cash.month},0)),0)' % MS
MGN = '((%s-%s)/%s)' % (REV3, FOOD3, CH3)     # revenue less food for one child a month, center average
tools = []

# 1 ------------------------------------------------------------ break-even and occupancy scenario
RPC1 = 'IFERROR(%s/%s,0)' % (RMS('revenue', '{in:room}', 3), RMS('enrolled', '{in:room}', 3))
FPC1 = 'IFERROR(%s/%s,0)' % (RMS('food_cost', '{in:room}', 3), RMS('enrolled', '{in:room}', 3))
DP1 = '({in:change}*(%s*(1+{in:fee_change})-%s)+{in:fee_change}*%s-{in:staff_hours}*%s-{in:fixed_change})' % (RPC1, FPC1, REV3, STAFFH)
PA1 = '(%s+%s)' % (PROFIT3, DP1)
BEA1 = '(%s+{in:change}-%s/%s)' % (CH3, PA1, MGN)
tools.append(TOOL('break_even', 'Break-even Scenario', 'What happens to break-even when children come or go',
    'Pick a room and type the children added or lost, a fee change, staff hours and fixed costs: see the break-even children, the break-even occupancy and the first month above break-even, against your own last 3 months.', [
    IL('room', 'Room that changes', 'room', 'Infants'), I('change', 'Children added, or lost with a minus', 2, 'int'), I('fee_change', 'Fee change for all children', 0.0, 'pct'), I('staff_hours', 'Staff hours added a month', 0, 'num'),
    I('fixed_change', 'Fixed cost added a month', 0), I('start_in', 'Months until the change starts', 1, 'int')], [
    O('Children now, average of 3 months', 'num', CH3), O('Licensed places', 'int', PLACES), O('Occupancy now', 'pct', 'IFERROR(%s/%s,0)' % (CH3, PLACES)), O('Fixed costs a month: staff, owner, rent, other', 'money', FIX3),
    O('Revenue per child a month', 'money', 'IFERROR(%s/%s,0)' % (REV3, CH3)), O('Food cost per child a month', 'money', 'IFERROR(%s/%s,0)' % (FOOD3, CH3)),
    O('Break-even children now', 'num', 'IFERROR(%s-%s/%s,0)' % (CH3, PROFIT3, MGN)), O('Break-even occupancy now', 'pct', 'IFERROR((%s-%s/%s)/%s,0)' % (CH3, PROFIT3, MGN, PLACES)),
    O('Profit a month now', 'money', PROFIT3), O('Profit change a month from the change', 'money', DP1), O('Profit a month after the change', 'money', PA1),
    O('Children after the change', 'num', '%s+{in:change}' % CH3), O('Occupancy after the change', 'pct', 'IFERROR((%s+{in:change})/%s,0)' % (CH3, PLACES)),
    O('Break-even children after the change', 'num', 'IFERROR(%s,0)' % BEA1), O('Break-even occupancy after the change', 'pct', 'IFERROR(%s/%s,0)' % (BEA1, PLACES)),
    O('Children above break-even after the change', 'num', 'IFERROR(%s+{in:change}-%s,0)' % (CH3, BEA1)),
    O('First month above break-even', 'date', 'IF(%s>0,IF(%s>0,%s,EDATE(%s,{in:start_in})),"")' % (PA1, PROFIT3, MS, MS)),
    O('Verdict', 'text', 'IF(ABS(%s)<=0.01*%s,%s,IF(%s>0,%s,%s))' % (PA1, REV3, V('At break-even'), PA1, V('Above break-even'), V('Below break-even')))],
    GR('What if', ('Enrol two more infants', {'room': GL('room', 'Infants'), 'change': 2, 'staff_hours': 0}), ('Lose a family of two', {'room': GL('room', 'Toddlers'), 'change': -2, 'staff_hours': 0}),
       ('Open a part-time day', {'room': GL('room', 'School-age'), 'change': 4, 'staff_hours': 30}), ('Lose three Twos children', {'room': GL('room', 'Twos'), 'change': -3, 'staff_hours': 0}),
       ('Fee up 3 percent', {'change': 0, 'fee_change': 0.03, 'staff_hours': 0}), ('Rent up 300 a month', {'change': 0, 'fixed_change': 300, 'staff_hours': 0}), ('Enrol five Preschool children', {'room': GL('room', 'Preschool'), 'change': 5, 'staff_hours': 20}))))

# 2 ------------------------------------------------------------ cost per child-hour and fee check
CPH2 = 'IFERROR(INDEX({range:fee_check.cost_per_hour},MATCH({in:room},{range:fee_check.room},0)),0)'
FPH2 = 'IFERROR(INDEX({range:fee_check.fee_per_hour},MATCH({in:room},{range:fee_check.room},0)),0)'
WK2 = 'SUMIFS({range:rates.weekly_rate},{range:rates.room},{in:room},{range:rates.schedule},%s)' % FD
WH2 = 'SUMIFS({range:rates.days},{range:rates.room},{in:room},{range:rates.schedule},%s)*SUMIFS({range:rates.hours_day},{range:rates.room},{in:room},{range:rates.schedule},%s)' % (FD, FD)
NW2 = '(%s/(1-{in:margin})*%s)' % (CPH2, WH2)
DF2 = '(%s-%s)' % (NW2, WK2)
tools.append(TOOL('fee_check_tool', 'Fee Check', 'Is the fee of this room right for its cost per child-hour',
    'Pick a room and your wanted margin: the cost and the fee per child-hour over 12 months, the weekly rate that earns your margin, the staff pay share against your own limit and a verdict on the fee.', [
    IL('room', 'Room', 'room', 'Infants'), I('margin', 'Wanted margin', 0.12, 'pct')], [
    O('Cost per child-hour, 12 months', 'money', CPH2), O('Fee per child-hour, 12 months', 'money', FPH2), O('Margin per child-hour', 'money', '%s-%s' % (FPH2, CPH2)),
    O('Margin share of the fee', 'pct', 'IFERROR((%s-%s)/%s,0)' % (FPH2, CPH2, FPH2)), O('Fee per child-hour for your margin', 'money', 'IFERROR(%s/(1-{in:margin}),0)' % CPH2),
    O('Weekly rate now, 5 full days', 'money', WK2), O('Hours in a 5 full days week', 'num', WH2), O('Weekly rate for your margin', 'money', NW2), O('Weekly rate short, or above with a minus', 'money', DF2),
    O('Cost per child-hour, whole center', 'money', 'IFERROR(SUMIFS({range:cost_hour.total_cost},%s)/SUMIFS({range:cost_hour.child_hours},%s),0)' % (WN('cost_hour', 12), WN('cost_hour', 12))),
    O('Fee per child-hour, whole center', 'money', 'IFERROR(SUMIFS({range:cost_hour.revenue},%s)/SUMIFS({range:cost_hour.child_hours},%s),0)' % (WN('cost_hour', 12), WN('cost_hour', 12))),
    O('Staff pay share of revenue, 12 months', 'pct', 'IFERROR(%s/%s,0)' % (SN('pnl', 'staff_pay', 12), SN('pnl', 'revenue', 12))), O('Your highest accepted staff share', 'pct', '{set:staff_share_target}'),
    O('Verdict', 'text', 'IF(ABS(%s)<={set:steady_band}*%s,%s,IF(%s>0,%s&" "&ROUND(%s,2),%s&" "&ROUND(-%s,2)))' % (DF2, WK2, V('Your fee is right'), DF2, V('Your fee is low by'), DF2, V('Your fee is above your margin by'), DF2))],
    GR('What if', ('Toddlers room', {'room': GL('room', 'Toddlers')}), ('Twos room', {'room': GL('room', 'Twos')}), ('Preschool room', {'room': GL('room', 'Preschool')}), ('School-age group', {'room': GL('room', 'School-age')}),
       ('Margin of 5 percent', {'margin': 0.05}), ('Margin of 20 percent', {'margin': 0.20}))))

# 3 ------------------------------------------------------------ loss-making room finder
ASENT, CAPR, CHLD = tok('ovrule', 'As entered'), tok('ovrule', 'Capacity share'), tok('ovrule', 'Children share')
def P12(room): return ('IFERROR(IF({in:rule}=%s,INDEX({range:room_months.room_profit_12m},MATCH(%s,{range:room_months.room},0)),IF({in:rule}=%s,INDEX({range:room_months.p12_cap},MATCH(%s,{range:room_months.room},0)),'
                       'INDEX({range:room_months.p12_child},MATCH(%s,{range:room_months.room},0)))),0)' % (ASENT, room, CAPR, room, room))
MINP3 = 'IF({in:rule}=%s,MIN({range:room_months.room_profit_12m}),IF({in:rule}=%s,MIN({range:room_months.p12_cap}),MIN({range:room_months.p12_child})))' % (ASENT, CAPR)
def LOSER():
    def one(c): return 'INDEX({range:room_months.room},MATCH(MIN({range:room_months.%s}),{range:room_months.%s},0))' % (c, c)
    return 'IFERROR(IF({in:rule}=%s,%s,IF({in:rule}=%s,%s,%s)),"")' % (ASENT, one('room_profit_12m'), CAPR, one('p12_cap'), one('p12_child'))
L3 = LOSER()
MC3 = 'IFERROR((%s-%s)/%s,0)' % (RMS('revenue', L3, 12), RMS('food_cost', L3, 12), RMS('enrolled', L3, 12))
NEED3 = 'IF(%s>=0,0,IFERROR(ROUNDUP(-%s/12/%s,0),0))' % (MINP3, MINP3, MC3)
FREE3 = 'MAX(0,SUMIFS({range:rooms.capacity},{range:rooms.room},%s)-ROUND(%s/3,0))' % (L3, RMS('enrolled', L3, 3))
tools.append(TOOL('loss_room', 'Loss-Making Room Finder', 'Which room loses money and what turns it positive',
    'Pick the overhead rule: profit of each room over 12 months, the room that loses most, its occupancy and the children that would turn it positive, with the free places it has.', [
    IL('rule', 'Overhead rule', 'ovrule', 'As entered'), I('add_children', 'Children you could add to that room', 2, 'int')], [
    O('Infants profit, 12 months', 'money', P12(RT['Infants'])), O('Toddlers profit, 12 months', 'money', P12(RT['Toddlers'])), O('Twos profit, 12 months', 'money', P12(RT['Twos'])), O('Preschool profit, 12 months', 'money', P12(RT['Preschool'])),
    O('School-age profit, 12 months', 'money', P12(RT['School-age'])), O('Room that loses the most', 'text', 'IF(%s>=0,"",%s)' % (MINP3, L3)), O('Its profit, 12 months', 'money', MINP3),
    O('Its children now, average of 3 months', 'num', 'IF(%s>=0,0,%s/3)' % (MINP3, RMS('enrolled', L3, 3))), O('Its licensed places', 'int', 'IF(%s>=0,0,SUMIFS({range:rooms.capacity},{range:rooms.room},%s))' % (MINP3, L3)),
    O('Its revenue less food per child a month', 'money', 'IF(%s>=0,0,%s)' % (MINP3, MC3)), O('Children that turn it positive', 'int', NEED3), O('Free places it has', 'int', 'IF(%s>=0,0,%s)' % (MINP3, FREE3)),
    O('Its profit, 12 months, after adding your children', 'money', '%s+{in:add_children}*%s*12' % (MINP3, MC3)),
    O('Can its free places turn it positive', 'text', 'IF(%s>=0,"",IF(%s<=%s,%s,%s))' % (MINP3, NEED3, FREE3, V('Yes, fill the free places'), V('No, fix price and staffing'))),
    O('Verdict', 'text', 'IF(%s>=0,%s,%s&" "&%s)' % (MINP3, V('Every room earns'), V('Loses money:'), L3))],
    GR('What if', ('Capacity rule', {'rule': GL('ovrule', 'Capacity share')}), ('Children rule', {'rule': GL('ovrule', 'Children share')}), ('Add four children', {'add_children': 4}), ('Add no children', {'add_children': 0}))))

# 4 ------------------------------------------------------------ home-daycare mode and owner pay
SH4 = ('IF({in:rule}=%s,{in:rooms_used}/{in:rooms_total},IF({in:rule}=%s,{in:hours_used}/{in:hours_week},IF({in:rule}=%s,({in:rooms_used}/{in:rooms_total})*({in:hours_used}/{in:hours_week}),'
       'IF({in:rule}=%s,1,0))))' % (TK('homerule', 'Rooms share'), TK('homerule', 'Hours share'), TK('homerule', 'Rooms and hours'), TK('homerule', 'Whole amount')))
HC4 = '(SUM({range:home_lines.amount})*%s)' % SH4
REV4 = '({in:children_now}*{in:fee})'
CAP4 = 'MIN({in:places},{in:staff}*{in:ratio})'
CH4 = 'MIN({in:children_now},%s)' % CAP4
PRF4 = '(%s*{in:fee}-%s-{in:assistant}-%s*{in:direct_child})' % (CH4, HC4, CH4)
AFF4 = '(%s-{in:setaside}*MAX(0,%s))' % (PRF4, PRF4)
tools.append(TOOL('home_mode', 'Home-Daycare Mode', 'Is your draw affordable after the home share',
    'For a single home daycare provider: choose a rule (rooms, hours or both), type the rooms and hours used for the business, your fee, staff and draw: see the business share of the house costs, the one-room capacity (ratio: check your local rules) and whether the draw is affordable. Confirm with your adviser.', [
    IL('rule', 'Home-use rule', 'homerule', 'Rooms and hours'), I('rooms_total', 'Rooms in the home', 7, 'int'), I('rooms_used', 'Rooms used for the business', 2, 'int'), I('hours_used', 'Hours a week used for the business', 55, 'int'),
    I('hours_week', 'Hours in the week used for the share', 168, 'int'), I('places', 'Licensed places in the one room', 6, 'int'), I('staff', 'Staff in the room', 1, 'int'), I('ratio', 'Ratio, children per staff, check your local rules', 6, 'int'),
    I('children_now', 'Children you plan to enrol', 5, 'int'), I('fee', 'Fee per child a month', 1050), I('direct_child', 'Food and supplies per child a month', 70), I('assistant', 'Assistant pay a month', 0),
    I('draw', 'Draw you want a month', 2200), I('setaside', 'Set-aside share of profit, confirm with your adviser', 0.25, 'pct')], [
    O('Share by rooms', 'pct', 'IFERROR({in:rooms_used}/{in:rooms_total},0)'), O('Share by hours', 'pct', 'IFERROR({in:hours_used}/{in:hours_week},0)'), O('Business share under your rule', 'pct', 'IFERROR(%s,0)' % SH4),
    O('House costs a month in the cost lines', 'money', 'SUM({range:home_lines.amount})'), O('Business house cost a month, your rule on every line', 'money', 'IFERROR(%s,0)' % HC4),
    O('Business house cost a month, rule of each line', 'money', 'SUM({range:home_lines.business_amount})'), O('One-room capacity, places or staff times ratio', 'int', CAP4),
    O('Children counted', 'int', CH4), O('Revenue a month', 'money', '%s*{in:fee}' % CH4), O('Profit before the draw a month', 'money', 'IFERROR(%s,0)' % PRF4),
    O('Set-aside a month', 'money', '{in:setaside}*MAX(0,IFERROR(%s,0))' % PRF4), O('Draw you can afford a month', 'money', 'IFERROR(%s,0)' % AFF4),
    O('Reduce the draw by', 'money', 'MAX(0,{in:draw}-IFERROR(%s,0))' % AFF4), O('Children needed to cover the house share and assistant', 'int', 'IFERROR(ROUNDUP((%s+{in:assistant})/({in:fee}-{in:direct_child}),0),0)' % HC4),
    O('Verdict', 'text', 'IF({in:draw}<=IFERROR(%s,0),%s,%s&" "&ROUND({in:draw}-IFERROR(%s,0),0))' % (AFF4, V('Draw is affordable'), V('Reduce the draw by'), AFF4))],
    GR('What if', ('Rooms rule only', {'rule': GL('homerule', 'Rooms share')}), ('Hours rule only', {'rule': GL('homerule', 'Hours share')}), ('Draw of 3000', {'draw': 3000}), ('Four children', {'children_now': 4}),
       ('Two staff, ratio 6', {'staff': 2, 'places': 10, 'children_now': 9}), ('Fee of 1200', {'fee': 1200}))))

# 5 ------------------------------------------------------------ owner draw and tax set-aside planner
PF5 = '((%s+%s)/6*IF({in:scn}=%s,1.15,IF({in:scn}=%s,0.8,1)))' % (SN('pnl', 'profit', 6), SN('pnl', 'owner_pay', 6), TK('scen', 'Best'), TK('scen', 'Worst'))
AF5 = '(%s-{in:draw})' % PF5
SA5 = '({in:pct}*MAX(0,%s))' % AF5
NET5 = '(%s-%s)' % (AF5, SA5)
K1 = '(MOD({set:extra_draw_month}-MONTH(%s),3)+1)' % MS
NX = '(INT((12-%s)/3)+1)' % K1
FIRST5 = '(%s+%s*%s-{in:extra})' % (CASH_LAST, K1, NET5)
LAST5 = '(%s+(%s+3*(%s-1))*%s-%s*{in:extra})' % (CASH_LAST, K1, NX, NET5, NX)
END5 = '(%s+12*%s-%s*{in:extra})' % (CASH_LAST, NET5, NX)
LOW5 = 'MIN(%s,%s,%s,%s)' % (CASH_LAST, FIRST5, LAST5, END5)
tools.append(TOOL('draw_tool', 'Owner Draw Planner', 'Does cash stay above the floor with this draw and set-aside',
    'Pick a Base, Best or Worst case and type your draw, the quarterly extra draw and the set-aside share (confirm with your adviser): the profit forecast is your own last 6 months; see cash after the extra draws and the lowest cash in the next 12 months.', [
    IL('scn', 'Case', 'scen', 'Base'), I('draw', 'Owner draw a month', 5500), I('extra', 'Extra draw each quarter', 15000), I('pct', 'Set-aside share of profit', 0.25, 'pct')], [
    O('Profit before the draw a month, own last 6 months', 'money', PF5), O('Profit after the draw a month', 'money', AF5), O('Tax set-aside a month', 'money', SA5), O('Cash added a month after the set-aside', 'money', NET5),
    O('Cash at the end of last month', 'money', CASH_LAST), O('Months until the first extra draw, this month is 1', 'int', K1), O('Extra draws in the next 12 months', 'int', NX),
    O('Cash right after the first extra draw', 'money', FIRST5), O('Cash right after the last extra draw', 'money', LAST5), O('Cash in 12 months', 'money', END5), O('Lowest cash in the next 12 months', 'money', LOW5),
    O('Your cash floor', 'money', '{set:cash_floor}'), O('Lowest cash above the floor', 'money', '%s-{set:cash_floor}' % LOW5), O('Set-aside over 12 months', 'money', '12*%s' % SA5), O('Draws over 12 months, with the extra draws', 'money', '12*{in:draw}+%s*{in:extra}' % NX),
    O('Each extra draw to cut so the lowest cash reaches the floor', 'money', 'MAX(0,{set:cash_floor}-%s)' % LOW5),
    O('Verdict', 'text', 'IF(%s>={set:cash_floor},%s,%s)' % (LOW5, V('Cash stays above the floor'), V('Reduce the extra draw')))],
    GR('What if', ('Worst case', {'scn': GL('scen', 'Worst')}), ('Best case', {'scn': GL('scen', 'Best')}), ('Draw of 6500', {'draw': 6500}), ('Extra draw of 25000', {'extra': 25000}), ('Set-aside of 30 percent', {'pct': 0.30}), ('No extra draw', {'extra': 0}))))

# 6 ------------------------------------------------------------ year in review
RK6 = 'MATCH({in:measure}&"|"&{in:basis},{range:year_review.row_key},0)'
def YR(c): return 'IFERROR(INDEX({range:year_review.%s},%s),0)' % (c, RK6)
tools.append(TOOL('year_tool', 'Year in Review Tool', 'Is this measure stronger or weaker than the period before',
    'Pick a review period and a measure: this period against the period before, the change and the verdict, with how many of the 8 measures are stronger or weaker in that period.', [
    IL('basis', 'Review period', 'basis', BASIS[0]), IL('measure', 'Measure', 'ymeasure', 'Revenue')], [
    O('This period', 'num', YR('this_period')), O('Period before', 'num', YR('last_period')), O('Change', 'num', YR('change')), O('Change, share', 'pct', YR('change_pct')),
    O('Measures stronger in this review period', 'int', 'COUNTIFS({range:year_review.basis},{in:basis},{range:year_review.verdict},%s)' % V('Stronger')),
    O('Measures steady in this review period', 'int', 'COUNTIFS({range:year_review.basis},{in:basis},{range:year_review.verdict},%s)' % V('Steady')),
    O('Measures weaker in this review period', 'int', 'COUNTIFS({range:year_review.basis},{in:basis},{range:year_review.verdict},%s)' % V('Weaker')),
    O('Verdict on this measure', 'text', 'IFERROR(INDEX({range:year_review.verdict},%s),"")' % RK6),
    O('Overall verdict for the period', 'text', 'IF(COUNTIFS({range:year_review.basis},{in:basis},{range:year_review.verdict},%s)>COUNTIFS({range:year_review.basis},{in:basis},{range:year_review.verdict},%s),%s,IF(COUNTIFS({range:year_review.basis},{in:basis},{range:year_review.verdict},%s)>COUNTIFS({range:year_review.basis},{in:basis},{range:year_review.verdict},%s),%s,%s))' % (
        V('Stronger'), V('Weaker'), V('Stronger overall'), V('Weaker'), V('Stronger'), V('Weaker overall'), V('Steady overall')))],
    GR('What if', ('Profit, year to date', {'measure': GL('ymeasure', 'Profit')}), ('Occupancy, last 6 months', {'basis': GL('basis', BASIS[1]), 'measure': GL('ymeasure', 'Occupancy, percent')}),
       ('Staff pay share, last 3 months', {'basis': GL('basis', BASIS[2]), 'measure': GL('ymeasure', 'Staff cost share, percent')}), ('Costs, last 6 months', {'basis': GL('basis', BASIS[1]), 'measure': GL('ymeasure', 'Costs')}),
       ('Cash, last 3 months', {'basis': GL('basis', BASIS[2]), 'measure': GL('ymeasure', 'Cash at the end of the period')}))))

# 7 ------------------------------------------------------------ what-if enrolment
WR7 = 'SUMIFS({range:rates.weekly_rate},{range:rates.room},{in:room},{range:rates.schedule},{in:schedule})'
EN7 = 'ROUND(%s/3,0)' % RMS('enrolled', '{in:room}', 3)
RT7 = 'SUMIFS({range:rooms.ratio},{range:rooms.room},{in:room})'
def STF7(n): return 'MAX(IF({in:room}=%s,{in:min_staff},1),ROUNDUP((%s)/%s,0))' % (RT['Infants'], n, RT7)
EXH7 = '(%s-%s)*{in:hours_staff}+{in:extra_hours}' % (STF7('%s+{in:children}' % EN7), STF7(EN7))
REVC7 = '({in:children}*%s*52/12*(1-{in:discount}))' % WR7
FOOD7 = '({in:children}*IFERROR(%s/%s,0))' % (RMS('food_cost', '{in:room}', 3), RMS('enrolled', '{in:room}', 3))
PCH7 = '(%s-%s-(%s)*%s)' % (REVC7, FOOD7, EXH7, STAFFH)
tools.append(TOOL('whatif_enrol', 'What-If Enrolment', 'Is it worth enrolling or losing these children',
    'Pick a room and schedule and type the children added or lost: revenue from the rate card, food cost, the staff the ratio needs (check your local rules) and the profit change a month and a year.', [
    IL('room', 'Room', 'room', 'Infants'), IL('schedule', 'Schedule', 'schedule', '5 full days'), I('children', 'Children added, or lost with a minus', 2, 'int'), I('discount', 'Average discount on the new fees', 0.05, 'pct'),
    I('min_staff', 'Staff kept in the Infants room when children are in', 2, 'int'), I('hours_staff', 'Hours a month of one staff member', 140, 'int'), I('extra_hours', 'Extra staff hours a month', 0, 'num')], [
    O('Weekly rate of the schedule', 'money', WR7), O('Revenue per child a month', 'money', '%s*52/12*(1-{in:discount})' % WR7), O('Children in the room now, average of 3 months', 'int', EN7), O('Ratio, children per staff, check your local rules', 'int', RT7),
    O('Staff needed now', 'int', STF7(EN7)), O('Staff needed after the change', 'int', STF7('%s+{in:children}' % EN7)), O('Staff hours added a month', 'num', EXH7), O('Revenue change a month', 'money', REVC7),
    O('Food cost change a month', 'money', FOOD7), O('Staff cost change a month', 'money', '(%s)*%s' % (EXH7, STAFFH)), O('Profit change a month', 'money', PCH7), O('Profit change a year', 'money', '12*%s' % PCH7),
    O('Occupancy of the room after the change', 'pct', 'IFERROR((%s+{in:children})/SUMIFS({range:rooms.capacity},{range:rooms.room},{in:room}),0)' % EN7),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (PCH7, V('Worth it'), V('Not worth it')))],
    GR('What if', ('Lose two Toddlers', {'room': GL('room', 'Toddlers'), 'children': -2}), ('Add three to Preschool', {'room': GL('room', 'Preschool'), 'children': 3}), ('Add five school-age, 3 half days', {'room': GL('room', 'School-age'), 'schedule': GL('schedule', '3 half days'), 'children': 5}),
       ('Add three infants, 2 full days', {'schedule': GL('schedule', '2 full days'), 'children': 3}), ('Add two with 20 extra hours', {'extra_hours': 20}))))

# 8 ------------------------------------------------------------ staff cost share gap
def AVN(t, c): return '(SUMIFS({range:%s.%s},{range:%s.month},">="&EDATE(%s,-{in:months}),{range:%s.month},"<"&%s)/{in:months})' % (t, c, t, MS, t, MS)
SP8, RV8 = AVN('pnl', 'staff_pay'), AVN('pnl', 'revenue')
SV8 = 'MAX(0,%s-{in:target}*%s)' % (SP8, RV8)
tools.append(TOOL('staff_gap', 'Staff Cost Share Gap', 'What closes the gap between staff pay and your own limit',
    'Type the months to average and your highest accepted staff pay share of revenue: see the share, the gap, the saving or the extra revenue that closes it and the hours or children that means.', [
    I('months', 'Months to average', 3, 'int'), I('target', 'Highest staff pay share you accept', 0.70, 'pct')], [
    O('Staff pay a month', 'money', SP8), O('Revenue a month', 'money', RV8), O('Staff pay share of revenue', 'pct', 'IFERROR(%s/%s,0)' % (SP8, RV8)), O('Gap to your limit', 'pct', 'IFERROR(%s/%s,0)-{in:target}' % (SP8, RV8)),
    O('Staff pay at your limit', 'money', '{in:target}*%s' % RV8), O('Saving a month that closes the gap', 'money', SV8), O('Extra revenue a month that closes the gap', 'money', 'IF(%s>0,%s/{in:target}-%s,0)' % (SV8, SP8, RV8)),
    O('Staff hours to cut a month', 'num', 'IFERROR(%s/%s,0)' % (SV8, STAFFH)), O('Children to add to close it', 'num', 'IFERROR((%s/{in:target}-%s)/(%s/%s),0)*IF(%s>0,1,0)' % (SP8, RV8, REV3, CH3, SV8)),
    O('Staff pay share 3 months earlier', 'pct', 'IFERROR(SUMIFS({range:pnl.staff_pay},{range:pnl.month},">="&EDATE(%s,-6),{range:pnl.month},"<"&EDATE(%s,-3))/SUMIFS({range:pnl.revenue},{range:pnl.month},">="&EDATE(%s,-6),{range:pnl.month},"<"&EDATE(%s,-3)),0)' % (MS, MS, MS, MS)),
    O('Highest share in any month shown', 'pct', 'MAX({range:staff_share.share})'),
    O('Verdict', 'text', 'IF(%s<=0,%s,%s&" "&ROUND(%s,0))' % (SV8, V('On target'), V('Needs a staff saving of'), SV8))],
    GR('What if', ('Limit of 60 percent', {'target': 0.60}), ('Limit of 55 percent', {'target': 0.55}), ('Last 6 months', {'months': 6}), ('Last month only', {'months': 1}), ('Last 12 months, 58 percent', {'months': 12, 'target': 0.58}))))

# 9 ------------------------------------------------------------ budget variance ranker
def BRK(k, c): return 'IFERROR(INDEX({range:budget.%s},MATCH(%s,{range:budget.rank_over},0)),%s)' % (c, k, '""' if c == 'category' else '0')
LASTR = 'MAX({range:budget.rank_over})'
tools.append(TOOL('budget_rank', 'Budget Variance Ranker', 'Which category is furthest over budget',
    'Type the variance share that needs a look: expense categories ranked from the biggest overspend, the category furthest under budget and the total variance over 12 months.', [
    I('limit', 'Variance share of the budget that needs a look', 0.05, 'pct')], [
    O('Biggest overspend category', 'text', BRK(1, 'category')), O('Its variance, 12 months', 'money', BRK(1, 'cat_var')), O('Its budget, 12 months', 'money', BRK(1, 'cat_budget')),
    O('Its variance share of budget', 'pct', 'IFERROR(%s/%s,0)' % (BRK(1, 'cat_var'), BRK(1, 'cat_budget'))), O('Second overspend category', 'text', BRK(2, 'category')), O('Its variance, 12 months', 'money', BRK(2, 'cat_var')),
    O('Third overspend category', 'text', BRK(3, 'category')), O('Its variance, 12 months', 'money', BRK(3, 'cat_var')),
    O('Category furthest under budget', 'text', 'IFERROR(INDEX({range:budget.category},MATCH(%s,{range:budget.rank_over},0)),"")' % LASTR), O('Its variance, 12 months', 'money', 'IFERROR(INDEX({range:budget.cat_var},MATCH(%s,{range:budget.rank_over},0)),0)' % LASTR),
    O('Total budget, 12 months', 'money', 'SUM({range:budget.budget})'), O('Total actual, 12 months', 'money', 'SUM({range:budget.actual})'), O('Total variance share of budget', 'pct', 'IFERROR(SUM({range:budget.variance})/SUM({range:budget.budget}),0)'),
    O('Categories over your limit', 'int', 'ROUND(SUMIFS({range:budget.weight},{range:budget.cat_pct},">"&{in:limit}),0)'),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>{in:limit},%s&" "&%s,%s)' % (BRK(1, 'cat_var'), BRK(1, 'cat_budget'), V('Investigate'), BRK(1, 'category'), V('All within budget')))],
    GR('What if', ('Limit of 2 percent', {'limit': 0.02}), ('Limit of 10 percent', {'limit': 0.10}), ('Limit of 20 percent', {'limit': 0.20}))))

# 10 ----------------------------------------------------------- expense category ranking
def SRK(k, c): return 'IFERROR(INDEX({range:budget.%s},MATCH(%s,{range:budget.rank_spend},0)),%s)' % (c, k, '""' if c == 'category' else '0')
TOP3 = '(%s+%s+%s)' % (SRK(1, 'cat_actual_11'), SRK(2, 'cat_actual_11'), SRK(3, 'cat_actual_11'))
tools.append(TOOL('expense_rank', 'Expense Category Ranking', 'Which category to negotiate first',
    'Type the cut you want in your three biggest categories: the categories ranked by spend over the last 11 months, each against the same months last year, and the saving a cut would bring.', [
    I('cut', 'Cut in the top three categories', 0.05, 'pct')], [
    O('Largest spend category', 'text', SRK(1, 'category')), O('Its spend, last 11 months', 'money', SRK(1, 'cat_actual_11')), O('Its spend, same months last year', 'money', SRK(1, 'cat_last')),
    O('Its change against last year', 'pct', 'IFERROR(%s/%s-1,0)' % (SRK(1, 'cat_actual_11'), SRK(1, 'cat_last'))),
    O('Second category', 'text', SRK(2, 'category')), O('Its spend, last 11 months', 'money', SRK(2, 'cat_actual_11')), O('Its change against last year', 'pct', 'IFERROR(%s/%s-1,0)' % (SRK(2, 'cat_actual_11'), SRK(2, 'cat_last'))),
    O('Third category', 'text', SRK(3, 'category')), O('Its spend, last 11 months', 'money', SRK(3, 'cat_actual_11')), O('Its change against last year', 'pct', 'IFERROR(%s/%s-1,0)' % (SRK(3, 'cat_actual_11'), SRK(3, 'cat_last'))),
    O('Spend of the top three, last 11 months', 'money', TOP3), O('Share of all expenses', 'pct', 'IFERROR(%s/SUMIFS({range:budget.actual},{range:budget.month},">="&EDATE(%s,-11)),0)' % (TOP3, MS)),
    O('Saving over 11 months from your cut', 'money', '{in:cut}*%s' % TOP3), O('Saving over a year from your cut', 'money', '{in:cut}*%s*12/11' % TOP3),
    O('Total spend against last year, same months', 'pct', 'IFERROR(SUMIFS({range:budget.actual},{range:budget.month},">="&EDATE(%s,-11))/SUMIFS({range:budget.last_year},{range:budget.month},">="&EDATE(%s,-11))-1,0)' % (MS, MS)),
    O('Verdict', 'text', '%s&" "&%s' % (V('Negotiate'), SRK(1, 'category')))],
    GR('What if', ('Cut of 10 percent', {'cut': 0.10}), ('Cut of 3 percent', {'cut': 0.03}), ('Cut of 15 percent', {'cut': 0.15}))))

# 11 ----------------------------------------------------------- room profit ranker
def PPL(room): return 'IFERROR(INDEX({range:room_months.profit_place},MATCH(%s,{range:room_months.room},0)),0)' % room
def PHR(room): return 'IFERROR(INDEX({range:room_months.profit_hour},MATCH(%s,{range:room_months.room},0)),0)' % room
def NAMEOF(col, fn): return 'IFERROR(INDEX({range:room_months.room},MATCH(%s({range:room_months.%s}),{range:room_months.%s},0)),"")' % (fn, col, col)
tools.append(TOOL('room_rank', 'Room Profit Ranker', 'Which room to protect and which to fix',
    'No input needed: every room ranked by profit per place and per child-hour over the last 12 months, with the best and the worst room and a verdict.', [
    I('min_profit', 'Profit per place a year you want at least', 0, 'money')], [
    O('Infants profit per place', 'money', PPL(RT['Infants'])), O('Toddlers profit per place', 'money', PPL(RT['Toddlers'])), O('Twos profit per place', 'money', PPL(RT['Twos'])), O('Preschool profit per place', 'money', PPL(RT['Preschool'])),
    O('School-age profit per place', 'money', PPL(RT['School-age'])), O('Infants profit per child-hour', 'money', PHR(RT['Infants'])), O('Toddlers profit per child-hour', 'money', PHR(RT['Toddlers'])),
    O('Twos profit per child-hour', 'money', PHR(RT['Twos'])), O('Preschool profit per child-hour', 'money', PHR(RT['Preschool'])), O('School-age profit per child-hour', 'money', PHR(RT['School-age'])),
    O('Best room per place', 'text', NAMEOF('profit_place', 'MAX')), O('Worst room per place', 'text', NAMEOF('profit_place', 'MIN')), O('Best room per child-hour', 'text', NAMEOF('profit_hour', 'MAX')),
    O('Worst room per child-hour', 'text', NAMEOF('profit_hour', 'MIN')), O('Rooms above your minimum', 'int', '+'.join('IF(%s>={in:min_profit},1,0)' % PPL(RT[r]) for r in ROOMS)),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&%s' % (V('Protect'), NAMEOF('profit_place', 'MAX'), V('fix'), NAMEOF('profit_place', 'MIN')))],
    GR('What if', ('Minimum of 1000 a place', {'min_profit': 1000}), ('Minimum of 3000 a place', {'min_profit': 3000}), ('Minimum of 5000 a place', {'min_profit': 5000}))))

# 12 ----------------------------------------------------------- overhead allocation comparer
def PR(room, col): return 'IFERROR(INDEX({range:room_months.%s},MATCH(%s,{range:room_months.room},0)),0)' % (col, room)
def FLIP(room):
    a, b, c = PR(room, 'room_profit_12m'), PR(room, 'p12_cap'), PR(room, 'p12_child')
    return 'IF(OR(AND(%s>={in:loss_below},%s>={in:loss_below},%s>={in:loss_below}),AND(%s<{in:loss_below},%s<{in:loss_below},%s<{in:loss_below})),0,1)' % (a, b, c, a, b, c)
FL12 = '+'.join(FLIP(RT[r]) for r in ROOMS)
outs12 = []
for r in ROOMS:
    outs12 += [O('%s profit, rule as entered' % r, 'money', PR(RT[r], 'room_profit_12m')), O('%s profit, capacity rule' % r, 'money', PR(RT[r], 'p12_cap')), O('%s profit, children rule' % r, 'money', PR(RT[r], 'p12_child'))]
tools.append(TOOL('overhead_cmp', 'Overhead Rule Comparer', 'Does the room result depend on the overhead rule',
    'Each room over 12 months under the overhead rule as entered in Room Profit by Month, a capacity share and a children share: see which rooms change from profit to loss when the rule changes.', [
    I('loss_below', 'A room counts as losing when its profit is below', 0)], outs12[:15] + [
    O('Overhead shared by the rooms, 12 months', 'money', SN('room_months', 'overhead_share', 12)), O('Rooms whose result depends on the rule', 'int', FL12),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (FL12, V('The room result is stable'), V('The room result depends on the rule')))],
    GR('What if', ('Losing below 1000', {'loss_below': 1000}), ('Losing below minus 2000', {'loss_below': -2000}), ('Losing below 5000', {'loss_below': 5000}))))

# 13 ----------------------------------------------------------- fee needed to hold the margin
def NEED13(room): return 'IFERROR(INDEX({range:fee_check.cost_per_hour},MATCH(%s,{range:fee_check.room},0))*SUMIFS({range:rates.days},{range:rates.room},%s,{range:rates.schedule},%s)*SUMIFS({range:rates.hours_day},{range:rates.room},%s,{range:rates.schedule},%s)/(1-{in:margin}),0)' % (room, room, FD, room, FD)
def CUR13(room): return 'SUMIFS({range:rates.weekly_rate},{range:rates.room},%s,{range:rates.schedule},%s)' % (room, FD)
MAXK = 'MAX({range:rates.cost_to_rate})'
outs13 = []
for r in ROOMS:
    outs13 += [O('%s weekly rate for your margin' % r, 'money', NEED13(RT[r])), O('%s rise needed' % r, 'pct', 'IFERROR(MAX(0,%s/%s-1),0)' % (NEED13(RT[r]), CUR13(RT[r])))]
tools.append(TOOL('fee_needed', 'Fee Needed for the Margin', 'What weekly rate holds your margin in each room',
    'Type your wanted margin: for each room the weekly rate for 5 full days that earns it, worked out from the cost of a child-hour, and the rise it needs; the verdict names the room with the largest rise.', [
    I('margin', 'Wanted margin', 0.12, 'pct')], outs13 + [
    O('Room with the largest rise needed', 'text', 'IFERROR(INDEX({range:rates.room},MATCH(%s,{range:rates.cost_to_rate},0)),"")' % MAXK),
    O('Its rise needed', 'pct', 'IFERROR(MAX(0,%s/(1-{in:margin})-1),0)' % MAXK),
    O('Verdict', 'text', 'IF(IFERROR(%s/(1-{in:margin})-1,0)<=0,%s,%s&" "&IFERROR(INDEX({range:rates.room},MATCH(%s,{range:rates.cost_to_rate},0)),"")&" "&ROUND(100*(%s/(1-{in:margin})-1),1)&"%%")' % (MAXK, V('No rise needed'), V('Rise'), MAXK, MAXK))],
    GR('What if', ('Margin of 5 percent', {'margin': 0.05}), ('Margin of 8 percent', {'margin': 0.08}), ('Margin of 15 percent', {'margin': 0.15}), ('Margin of 20 percent', {'margin': 0.20}))))

# 14 ----------------------------------------------------------- sensitivity table
DO = '({in:step}*(%s-%s))' % (REV3, FOOD3)
DW = '({in:step}*%s)' % STAFF3
DF = '({in:step}*%s)' % REV3
tools.append(TOOL('sensitivity', 'Sensitivity Table', 'Which input moves profit most',
    'Type a step: occupancy, wages and fee are each moved up and down by that share of your own last 3 months, with the profit change of each move and the input that matters most.', [
    I('step', 'Step up and down', 0.05, 'pct')], [
    O('Profit a month now', 'money', PROFIT3), O('Occupancy up: profit change', 'money', DO), O('Occupancy down: profit change', 'money', '-%s' % DO), O('Wages up: profit change', 'money', '-%s' % DW), O('Wages down: profit change', 'money', DW),
    O('Fee up: profit change', 'money', DF), O('Fee down: profit change', 'money', '-%s' % DF), O('Profit after the worst move', 'money', '%s-MAX(%s,%s,%s)' % (PROFIT3, DO, DW, DF)),
    O('Profit after the best move', 'money', '%s+MAX(%s,%s,%s)' % (PROFIT3, DO, DW, DF)), O('Largest move as a share of profit', 'pct', 'IFERROR(MAX(%s,%s,%s)/%s,0)' % (DO, DW, DF, PROFIT3)),
    O('Input that matters most', 'text', 'IF(%s>=MAX(%s,%s),%s,IF(%s>=%s,%s,%s))' % (DF, DO, DW, V('Fee'), DO, DW, V('Occupancy'), V('Wages'))),
    O('Verdict', 'text', 'IF(%s>=MAX(%s,%s),%s,IF(%s>=%s,%s,%s))' % (DF, DO, DW, V('Watch your fee first'), DO, DW, V('Watch your occupancy first'), V('Watch your wages first')))],
    GR('What if', ('Step of 2 percent', {'step': 0.02}), ('Step of 3 percent', {'step': 0.03}), ('Step of 10 percent', {'step': 0.10}), ('Step of 15 percent', {'step': 0.15}))))

# 15 ----------------------------------------------------------- cash runway
NET15 = '(%s*(1-{in:drop})-%s*(1-{in:cut}))' % (REV3, COST3)
tools.append(TOOL('runway', 'Cash Runway', 'How long the cash lasts if revenue drops',
    'Type the revenue drop and any cost cut: see the monthly result, the months the cash lasts and the months until it reaches your floor; safe, watch or act now by the months you choose.', [
    I('drop', 'Drop in revenue', 0.20, 'pct'), I('cut', 'Cut in costs', 0.0, 'pct'), I('safe_months', 'Months of cash that count as safe', 12, 'int'), I('act_months', 'Months of cash below which you act', 6, 'int')], [
    O('Cash at the end of last month', 'money', CASH_LAST), O('Revenue a month, last 3 months', 'money', REV3), O('Costs a month, last 3 months', 'money', COST3), O('Revenue after the drop', 'money', '%s*(1-{in:drop})' % REV3),
    O('Costs after the cut', 'money', '%s*(1-{in:cut})' % COST3), O('Result a month after the drop', 'money', NET15), O('Months the cash lasts', 'num', 'IF(%s>=0,99,%s/-%s)' % (NET15, CASH_LAST, NET15)),
    O('Months until cash reaches your floor', 'num', 'IF(%s>=0,99,MAX(0,(%s-{set:cash_floor})/-%s))' % (NET15, CASH_LAST, NET15)), O('Cash floor', 'money', '{set:cash_floor}'),
    O('Months of cost the cash covers today', 'num', 'IFERROR(%s/%s,0)' % (CASH_LAST, COST3)), O('Revenue drop that uses no cash', 'pct', 'IFERROR(1-%s*(1-{in:cut})/%s,0)' % (COST3, REV3)),
    O('Verdict', 'text', 'IF(%s>=0,%s,IF((%s-{set:cash_floor})/-%s>={in:safe_months},%s,IF((%s-{set:cash_floor})/-%s>={in:act_months},%s,%s)))' % (NET15, V('Safe'), CASH_LAST, NET15, V('Safe'), CASH_LAST, NET15, V('Watch'), V('Act now')))],
    GR('What if', ('Drop of 10 percent', {'drop': 0.10}), ('Drop of 30 percent', {'drop': 0.30}), ('Drop of 40 percent', {'drop': 0.40}), ('Drop of 30 percent, costs cut 10 percent', {'drop': 0.30, 'cut': 0.10}), ('Drop of 25 percent', {'drop': 0.25}))))

# 16 ----------------------------------------------------------- schedule profitability
def SMG(s): return 'IFERROR(AVERAGEIFS({range:rates.margin_hour},{range:rates.schedule},%s),0)' % tok('schedule', s)
def SFE(s): return 'IFERROR(AVERAGEIFS({range:rates.collected_hour},{range:rates.schedule},%s),0)' % tok('schedule', s)
def PICK(fn, label_fmt):
    out = '""'
    for i, s in enumerate(SCHEDULES):
        others = ','.join(SMG(t) for t in SCHEDULES if t != s)
        out = 'IF(%s%s%s(%s),%s,%s)' % (SMG(s), '>=' if fn == 'MAX' else '<=', fn, others, tok('schedule', s), out)
    return out
BEST16, WORST16 = PICK('MAX', ''), PICK('MIN', '')
tools.append(TOOL('schedule_profit', 'Schedule Profitability', 'Which schedule earns most per child-hour',
    'No input needed: the rate and the margin per child-hour of each schedule, averaged over the rooms, with the schedule to promote and the one to reprice.', [
    I('min_margin', 'Margin per child-hour you want at least', 0.5, 'money')], [
    O('5 full days rate per child-hour', 'money', SFE('5 full days')), O('3 full days rate per child-hour', 'money', SFE('3 full days')), O('2 full days rate per child-hour', 'money', SFE('2 full days')),
    O('5 half days rate per child-hour', 'money', SFE('5 half days')), O('3 half days rate per child-hour', 'money', SFE('3 half days')), O('5 full days margin per child-hour', 'money', SMG('5 full days')),
    O('3 full days margin per child-hour', 'money', SMG('3 full days')), O('2 full days margin per child-hour', 'money', SMG('2 full days')), O('5 half days margin per child-hour', 'money', SMG('5 half days')),
    O('3 half days margin per child-hour', 'money', SMG('3 half days')), O('Schedule to promote', 'text', BEST16), O('Schedule to reprice', 'text', WORST16),
    O('Infants margin per child-hour, average of the schedules', 'money', 'IFERROR(AVERAGEIFS({range:rates.margin_hour},{range:rates.room},%s),0)' % RT['Infants']),
    O('Schedules under your minimum margin', 'int', '+'.join('IF(%s<{in:min_margin},1,0)' % SMG(s) for s in SCHEDULES)),
    O('Verdict', 'text', '%s&" "&%s' % (V('Promote'), BEST16))],
    GR('What if', ('Minimum margin of 0', {'min_margin': 0}), ('Minimum margin of 1', {'min_margin': 1}), ('Minimum margin of 2', {'min_margin': 2}))))

# 17 ----------------------------------------------------------- equipment purchase payback
GAIN17 = '({in:extra_children}*({in:fee}-%s/%s)+{in:saving})' % (FOOD3, CH3)
tools.append(TOOL('equipment', 'Equipment Payback', 'Should you buy this equipment now',
    'Type the cost, the extra children it makes room for and the saving a month: the gain a month, the months to pay back, the cash after the purchase against your floor and a buy or wait verdict.', [
    I('cost', 'Cost of the equipment', 2400), I('extra_children', 'Extra children it makes room for', 1, 'int'), I('fee', 'Fee per child a month', 1050), I('saving', 'Saving a month', 40), I('max_months', 'Longest payback you accept, months', 12, 'int')], [
    O('Food cost per child a month', 'money', 'IFERROR(%s/%s,0)' % (FOOD3, CH3)), O('Gain a month', 'money', GAIN17), O('Months to pay back', 'num', 'IF(%s>0,{in:cost}/%s,99)' % (GAIN17, GAIN17)),
    O('Month the purchase pays back', 'date', 'IF(%s>0,EDATE(%s,ROUNDUP({in:cost}/%s,0)),"")' % (GAIN17, MS, GAIN17)), O('Return in the first 12 months', 'money', '12*%s-{in:cost}' % GAIN17),
    O('Cash at the end of last month', 'money', CASH_LAST), O('Cash after the purchase', 'money', '%s-{in:cost}' % CASH_LAST), O('Cash after the purchase above your floor', 'money', '%s-{in:cost}-{set:cash_floor}' % CASH_LAST),
    O('Share of your cash used', 'pct', 'IFERROR({in:cost}/%s,0)' % CASH_LAST), O('Cost as months of profit', 'num', 'IFERROR({in:cost}/%s,0)' % PROFIT3),
    O('Verdict', 'text', 'IF(AND(%s>0,{in:cost}/%s<={in:max_months},%s-{in:cost}>={set:cash_floor}),%s,%s)' % (GAIN17, GAIN17, CASH_LAST, V('Buy'), V('Wait')))],
    GR('What if', ('No extra child', {'extra_children': 0}), ('Two extra children', {'extra_children': 2}), ('Cost of 12000', {'cost': 12000, 'extra_children': 2}), ('Cost of 40000', {'cost': 40000, 'extra_children': 3}), ('Payback of 24 months allowed', {'max_months': 24}))))

# 18 ----------------------------------------------------------- break-even for an extra room or day
CHF18 = '(({in:places}*{in:fill})'
STF18 = 'ROUNDUP(%s/{in:ratio},0)' % 'MAX(1,{in:places}*{in:fill})'
FIX18 = '({in:rent_extra}+{in:other_fixed}+%s*{in:hours_staff}*%s)' % (STF18, STAFFH)
tools.append(TOOL('new_group', 'New Room or Day', 'Is a new group of children worth opening',
    'Type the places of the new group, the fill you expect, the fee, the staff the ratio needs (check your local rules) and the extra fixed costs: the children needed to break even, the profit at your expected fill and the verdict.', [
    I('places', 'Places in the new group', 8, 'int'), I('fill', 'Fill you expect', 0.75, 'pct'), I('fee', 'Fee per child a month', 950), I('ratio', 'Ratio, children per staff, check your local rules', 6, 'int'),
    I('hours_staff', 'Hours a month of one staff member', 100, 'int'), I('rent_extra', 'Extra rent and utilities a month', 600), I('other_fixed', 'Other extra fixed costs a month', 150), I('min_profit', 'Profit a month you want at least', 300)], [
    O('Children expected', 'num', '{in:places}*{in:fill}'), O('Staff needed at the ratio', 'int', STF18), O('Staff cost a month', 'money', '%s*{in:hours_staff}*%s' % (STF18, STAFFH)), O('Fixed costs a month', 'money', FIX18),
    O('Food cost per child a month', 'money', 'IFERROR(%s/%s,0)' % (FOOD3, CH3)), O('Margin per child a month', 'money', '{in:fee}-IFERROR(%s/%s,0)' % (FOOD3, CH3)),
    O('Children to break even', 'num', 'IFERROR(%s/({in:fee}-%s/%s),0)' % (FIX18, FOOD3, CH3)), O('Break-even fill of the new group', 'pct', 'IFERROR(%s/({in:fee}-%s/%s)/{in:places},0)' % (FIX18, FOOD3, CH3)),
    O('Revenue a month at your fill', 'money', '{in:places}*{in:fill}*{in:fee}'), O('Profit a month at your fill', 'money', '{in:places}*{in:fill}*({in:fee}-%s/%s)-%s' % (FOOD3, CH3, FIX18)),
    O('Profit a month if the group is full', 'money', '{in:places}*({in:fee}-%s/%s)-%s' % (FOOD3, CH3, FIX18)), O('Profit a month today', 'money', PROFIT3),
    O('Fixed costs as a share of revenue at your fill', 'pct', 'IFERROR(%s/({in:places}*{in:fill}*{in:fee}),0)' % FIX18),
    O('Verdict', 'text', 'IF({in:places}*{in:fill}*({in:fee}-%s/%s)-%s>={in:min_profit},%s,%s)' % (FOOD3, CH3, FIX18, V('Open'), V('Not yet')))],
    GR('What if', ('Fill of 50 percent', {'fill': 0.50}), ('Fill of 90 percent', {'fill': 0.90}), ('Twelve places', {'places': 12, 'fill': 0.75}), ('Fee of 1100', {'fee': 1100}), ('One extra day, 4 places', {'places': 4, 'rent_extra': 100, 'other_fixed': 50, 'ratio': 6}))))
assert len(tools) == 18, len(tools)
