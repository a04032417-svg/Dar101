"""Wedding suite part 5: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp5_lists import *
import wp5_data as D
from wp5_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v_} for l, v_ in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def W(*parts): return '&" "&'.join(parts)
def IX(t, c_, n): return 'IFERROR(INDEX(%s,%s),"")' % (R(t, c_), n)
def IXN(t, c_, n): return 'IFERROR(INDEX(%s,%s),0)' % (R(t, c_), n)


tools = []
SZ = '{set:table_size}'
# 1 ---------------------------------------------------------------- table count solver
S1_ = '({in:headcount}+{in:couple}+{in:vendors}+{in:spare})'
T1_ = 'ROUNDUP(%s/{in:size},0)' % S1_
tools.append(TOOL('table_count', 'Table Count Solver', 'How many tables do we need',
    'Type the headcount, the table size and the seats for the couple, vendors and spare; the tool gives the seats and tables needed against the seated capacity and the tables the room holds.', [
    I('headcount', 'Headcount, guests who come', 118, 'int'), I('size', 'Seats at one table', 10, 'int'), I('couple', 'Seats for the couple', 2, 'int'), I('vendors', 'Seats for vendors who eat with you', 4, 'int'),
    I('spare', 'Spare seats for late changes', 4, 'int'), I('room', 'Tables the room holds', 13, 'int')], [
    O('Seats needed', 'int', S1_), O('Tables needed', 'int', T1_), O('Empty seats at those tables', 'int', '%s*{in:size}-%s' % (T1_, S1_)), O('Seated capacity of the venue', 'int', CAP),
    O('Seats over the seated capacity', 'int', 'MAX(0,%s-%s)' % (S1_, CAP)), O('Tables over what the room holds', 'int', 'MAX(0,%s-{in:room})' % T1_), O('Floor area per seat, square metres', 'num', 'IFERROR(%s/%s,0)' % (USABLE, S1_)),
    O('Dance floor area, square metres', 'num', SP('Dance floor')), O('Buffet area, square metres', 'num', SP('Buffet area')),
    O('Verdict', 'text', 'IF(AND(%s<=%s,%s<={in:room}),%s,%s&" "&MAX(%s-%s,(%s-{in:room})*{in:size})&" "&%s)' % (S1_, CAP, T1_, v('Fits'), v('Too tight by'), S1_, CAP, T1_, v('seats')))],
    GR('What if', ('As it is', {'headcount': 118}), ('Add 10 guests', {'headcount': 128}), ('Tables of 8', {'size': 8}), ('Cut 10 guests', {'headcount': 108}), ('No spare seats', {'spare': 0}))))

# 2 ---------------------------------------------------------------- table size comparison
def TS(s): return 'ROUNDUP({in:seats}/%d,0)' % s
def SCR(s): return 'IF(%s>{in:room},9999,%s*%d-{in:seats})' % (TS(s), TS(s), s)
MN = 'MIN(%s)' % ','.join(SCR(s) for s in (6, 8, 10, 12))
BEST = 'IF(%s=%s,12,IF(%s=%s,10,IF(%s=%s,8,IF(%s=%s,6,0))))' % (SCR(12), MN, SCR(10), MN, SCR(8), MN, SCR(6), MN)
outs = []
for s in (6, 8, 10, 12): outs += [O('Tables of %d' % s, 'int', TS(s)), O('Empty seats, tables of %d' % s, 'int', '%s*%d-{in:seats}' % (TS(s), s)), O('Floor area, tables of %d' % s, 'num', '%s*%d*{in:area}' % (TS(s), s))]
outs += [O('Fewest empty seats that fit the room', 'int', 'IF(%s=9999,0,%s)' % (MN, MN)), O('Best size', 'int', BEST), O('Verdict', 'text', 'IF(%s=9999,%s,%s&" "&%s)' % (MN, v('No size fits'), v('Best size'), BEST))]
tools.append(TOOL('table_size', 'Table Size Comparison', 'Which table size fits best',
    'Type the seats you need, the tables the room holds and the floor area for a seat; sizes 6, 8, 10 and 12 are compared and the size with the fewest empty seats that fits the room wins.', [
    I('seats', 'Seats needed', 123, 'int'), I('room', 'Tables the room holds', 13, 'int'), I('area', 'Floor area for one seat, square metres', 1.5, 'num')], outs,
    GR('What if', ('As it is', {'seats': 123}), ('A room for 16 tables', {'room': 16}), ('A room for 11 tables', {'room': 11}), ('Cut 20 seats', {'seats': 103}), ('Add 10 seats', {'seats': 133}))))

# 3 ---------------------------------------------------------------- everyone says yes
EV = '(%s+{in:plus}+%s)' % (GN, OTHERS)
EC = '(%s+{in:change})' % CAP
tools.append(TOOL('yes_scenario', 'Everyone Says Yes Scenario', 'What if everyone we invited says yes',
    'All invited guests plus the plus-ones you add and the couple and vendor seats against the seated capacity; shows how many must decline and how many pending guests can still say yes.', [
    I('plus', 'Plus-ones you add', 0, 'int'), I('change', 'Seats gained or lost', 0, 'int')], [
    O('Guests invited', 'int', GN), O('Seats needed if everyone says yes', 'int', EV), O('Seated capacity', 'int', EC), O('Seats over capacity', 'int', 'MAX(0,%s-%s)' % (EV, EC)),
    O('Guests who must decline to fit', 'int', 'MAX(0,%s-%s)' % (EV, EC)), O('Share of invited guests who must decline', 'pct', 'IFERROR(MAX(0,%s-%s)/%s,0)' % (EV, EC, GN)),
    O('Expected headcount seated', 'int', SEATS_EXP), O('Seats left at the expected headcount', 'int', '%s-%s' % (EC, SEATS_EXP)), O('Pending guests who can still say yes', 'int', 'MAX(0,%s-%s-%s)' % (EC, OTHERS, YESG)),
    O('Tables needed if everyone says yes', 'int', 'ROUNDUP(%s/%s,0)' % (EV, SZ)),
    O('Verdict', 'text', 'IF(%s>%s,%s&" "&(%s-%s)&" "&%s,%s&" "&(%s-%s)&" "&%s)' % (EV, EC, v('Over by'), EV, EC, v('seats'), v('Fits with'), EC, EV, v('spare')))],
    GR('What if', ('As it is', {'plus': 0, 'change': 0}), ('Add 6 plus-ones', {'plus': 6}), ('A room 10 seats bigger', {'change': 10}), ('A room 30 seats bigger', {'change': 30}), ('Cut 20 guests', {'plus': -20}))))

# 4 ---------------------------------------------------------------- capacity ladder
outs = []
for i in range(6):
    H = '({in:start}+%d*{in:step})' % i
    outs += [O('Headcount, step %d' % (i + 1), 'int', H), O('Tables, step %d' % (i + 1), 'int', 'ROUNDUP((%s+%s+{in:spare})/%s,0)' % (H, OTHERS, SZ)),
             O('Verdict, step %d' % (i + 1), 'text', VER_FIT('(%s+%s+{in:spare})' % (H, OTHERS), CAP))]
outs += [O('Last headcount that fits', 'int', '%s-%s-{in:spare}' % (CAP, OTHERS)), O('Verdict', 'text', '%s&" "&(%s-%s-{in:spare})' % (v('Last headcount that fits is'), CAP, OTHERS))]
tools.append(TOOL('capacity_ladder', 'Capacity Ladder', 'Up to which headcount do we fit',
    'Six headcounts from the one you type, with the couple and vendor seats and any spare seats: tables needed and fits, tight or over for each step, and the last headcount that fits.', [
    I('start', 'First headcount on the ladder', 100, 'int'), I('step', 'Guests between steps', 10, 'int'), I('spare', 'Spare seats you keep', 0, 'int')], outs,
    GR('What if', ('As it is', {'start': 100, 'step': 10}), ('Steps of 5', {'step': 5}), ('Start at 90', {'start': 90}), ('Keep 6 seats spare', {'spare': 6}), ('Start at 110', {'start': 110}))))

# 5 ---------------------------------------------------------------- floor space check
UF = '(%s-{in:extra})' % USABLE
tools.append(TOOL('floor_space', 'Floor Space Check', 'Is there enough floor space for the guests',
    'The floor area less the dance floor, buffet, stage, bar and walkways, shared among the guests you seat, against your least area per guest; the dance floor is checked too.', [
    I('guests', 'Guests you seat', 123, 'int'), I('extra', 'Extra area taken, square metres', 0, 'num'), I('per_dancer', 'Floor area for one dancer, square metres', 0.4, 'num')], [
    O('Venue floor area, square metres', 'num', SP('Venue floor area')), O('Dance floor, buffet, stage, bar and walkways', 'num', '%s-%s' % (SP('Venue floor area'), USABLE)), O('Area left for tables', 'num', UF),
    O('Area per guest', 'num', 'IFERROR(%s/{in:guests},0)' % UF), O('Your least area per guest', 'num', SP('Area per guest, minimum')), O('Guests that fit at your minimum', 'int', 'ROUNDDOWN(%s/%s,0)' % (UF, SP('Area per guest, minimum'))),
    O('Guests to spare or short', 'int', 'ROUNDDOWN(%s/%s,0)-{in:guests}' % (UF, SP('Area per guest, minimum'))), O('Guests on the floor at once', 'int', 'ROUND({in:guests}*%s,0)' % SP('Share of guests dancing')),
    O('Dance floor needed', 'num', 'ROUND({in:guests}*%s,0)*{in:per_dancer}' % SP('Share of guests dancing')), O('Dance floor you have', 'num', SP('Dance floor')),
    O('Verdict', 'text', 'IF(IFERROR(%s/{in:guests},0)>=%s,%s,%s&" "&{in:guests}&" "&%s)' % (UF, SP('Area per guest, minimum'), v('Enough space'), v('Tight at'), v('guests')))],
    GR('What if', ('As it is', {'guests': 123}), ('Add 20 guests', {'guests': 143}), ('Add 30 guests', {'guests': 153}), ('Take 20 square metres for a lounge', {'extra': 20}), ('Take 40 square metres', {'extra': 40}))))

# 6 ---------------------------------------------------------------- seat the table
def TI(c_, t='seating'): return IX(t, c_, '{in:table_no}')
tools.append(TOOL('seat_table', 'Seat the Table', 'Who sits at this table and is there room',
    'Type a table number from 1 to 13; the tool gives the seats, the guests seated, the free seats and the mix of sides and tiers.', [
    I('table_no', 'Table number, 1 to 13', 4, 'int')], [
    O('Table', 'text', TI('table_name')), O('Kind', 'text', TI('kind')), O('Seats', 'int', IXN('seating', 'capacity', '{in:table_no}')), O('Seats kept for the couple', 'int', IXN('seating', 'reserved', '{in:table_no}')),
    O('Guests seated', 'int', IXN('seating', 'seated', '{in:table_no}')), O('Free seats', 'int', IXN('seating', 'free', '{in:table_no}')), O('Partner 1 guests', 'int', IXN('fill', 'p1', '{in:table_no}')),
    O('Partner 2 guests', 'int', IXN('fill', 'p2', '{in:table_no}')), O('Shared friends', 'int', IXN('fill', 'shared', '{in:table_no}')), O('Family guests', 'int', IXN('balance', 'family', '{in:table_no}')),
    O('Fill share', 'pct', IXN('fill', 'fill_share', '{in:table_no}')),
    O('Verdict', 'text', 'IF(%s<=0,%s,%s&" "&%s)' % (IXN('seating', 'free', '{in:table_no}'), v('Table full'), v('Free seats'), IXN('seating', 'free', '{in:table_no}')))],
    GR('What if', ('Table 4', {'table_no': 4}), ('The head table', {'table_no': 1}), ('Table 6', {'table_no': 6}), ('Table 13', {'table_no': 13}), ('Table 9', {'table_no': 9}))))

# 7 ---------------------------------------------------------------- unseated finder
tools.append(TOOL('unseated_finder', 'Unseated Finder', 'Which guest do we seat next',
    'Pick a guest number from the Unseated Guests list; yes guests come first. The tool names the household table or the best table for the side and the free seats there.', [
    I('no', 'Guest number in the unseated list', 1, 'int')], [
    O('Yes guests without a seat', 'int', NEED), O('Pending guests', 'int', PENDG), O('Guest', 'text', IX('unseated', 'guest', '{in:no}')), O('Household', 'text', IX('unseated', 'household', '{in:no}')),
    O('Side', 'text', IX('unseated', 'side', '{in:no}')), O('Household table', 'text', IX('unseated', 'hh_table', '{in:no}')), O('Suggested table', 'text', IX('unseated', 'suggested', '{in:no}')),
    O('Free seats at the suggested table', 'int', IXN('unseated', 'suggested_free', '{in:no}')), O('Free seats in all', 'int', FREE_TOTAL), O('Seats to hold for pending guests', 'int', 'ROUND(%s*{set:expected_yes_rate},0)' % PENDG),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s&" "&%s)' % (NEED, v('Everyone is seated'), v('Seat'), IX('unseated', 'guest', '{in:no}'), v('at'), IX('unseated', 'suggested', '{in:no}')))],
    GR('What if', ('First guest', {'no': 1}), ('Second guest', {'no': 2}), ('Third guest', {'no': 3}), ('Fourth guest', {'no': 4}), ('A pending guest', {'no': 8}))))

# 8 ---------------------------------------------------------------- keep together and keep apart checker
CONF = 'SUM(%s)' % R('rules', 'conflict')
tools.append(TOOL('rule_checker', 'Keep Together Apart Checker', 'Do the seat rules hold',
    'Every rule is tested against the table assignments: kept, in conflict or a guest not yet seated. Pick a rule number to see its guests and tables.', [
    I('no', 'Rule number in fix order', 1, 'int')], [
    O('Rules in all', 'int', 'COUNTIFS(%s,"<>")' % R('rules', 'rule_id')), O('Keep-together rules kept', 'int', 'SUMIFS(%s,%s,%s)' % (R('rules', 'kept'), R('rules', 'kind'), TG)),
    O('Keep-together conflicts', 'int', 'SUMIFS(%s,%s,%s)' % (R('rules', 'conflict'), R('rules', 'kind'), TG)), O('Keep-apart rules kept', 'int', 'SUMIFS(%s,%s,%s)' % (R('rules', 'kept'), R('rules', 'kind'), tok('rkind', 'Keep apart'))),
    O('Keep-apart conflicts', 'int', 'SUMIFS(%s,%s,%s)' % (R('rules', 'conflict'), R('rules', 'kind'), tok('rkind', 'Keep apart'))), O('Rules with a guest not seated', 'int', 'COUNTIFS(%s,%s)' % (R('rules', 'status'), v('Not placed'))),
    O('Rule inspected', 'text', IX('conflicts', 'rule_id', '{in:no}')), O('Guest A', 'text', IX('conflicts', 'guest_a', '{in:no}')), O('Guest B', 'text', IX('conflicts', 'guest_b', '{in:no}')),
    O('Tables of the two guests', 'text', '%s&" / "&%s' % (IX('conflicts', 'table_a', '{in:no}'), IX('conflicts', 'table_b', '{in:no}'))), O('Status of the rule', 'text', IX('conflicts', 'flag', '{in:no}')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (CONF, v('No conflicts'), CONF, v('conflicts')))],
    GR('What if', ('First rule', {'no': 1}), ('Second rule', {'no': 2}), ('Third rule', {'no': 3}), ('Fourth rule', {'no': 4}), ('A rule that holds', {'no': 10}))))

# 9 ---------------------------------------------------------------- table balance
tools.append(TOOL('balance_tool', 'Table Balance Tool', 'Is any table all one side',
    'Type the share of one side that counts as all one side; family and head tables are left out. The tool names the most one-sided table and its side.', [
    I('thr', 'Share of one side that counts as all one side', 0.85, 'pct')], [
    O('Tables with guests', 'int', 'COUNTIFS(%s,">0")' % R('balance', 'seated')), O('Family and head tables, left out', 'int', 'SUM(%s)' % R('balance', 'exempt')),
    O('Mixed tables all one side', 'int', 'COUNTIFS(%s,">="&{in:thr},%s,0,%s,">0")' % (R('balance', 'top_share'), R('balance', 'exempt'), R('balance', 'seated'))),
    O('Most one-sided mixed table', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),"")' % (R('balance', 'table_name'), R('balance', 'mix_score'), R('balance', 'mix_score'))),
    O('Its largest side', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),"")' % (R('balance', 'top_side'), R('balance', 'mix_score'), R('balance', 'mix_score'))),
    O('Its largest side share', 'pct', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),0)' % (R('balance', 'top_share'), R('balance', 'mix_score'), R('balance', 'mix_score'))),
    O('Guests of partner 1 seated', 'int', 'SUM(%s)' % R('fill', 'p1')), O('Guests of partner 2 seated', 'int', 'SUM(%s)' % R('fill', 'p2')), O('Shared friends seated', 'int', 'SUM(%s)' % R('fill', 'shared')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">="&{in:thr},%s,0,%s,">0")=0,%s,IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),"")&" "&%s&" "&IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),""))' % (
        R('balance', 'top_share'), R('balance', 'exempt'), R('balance', 'seated'), v('Mixed well'), R('balance', 'table_name'), R('balance', 'mix_score'), R('balance', 'mix_score'), v('is all'),
        R('balance', 'top_side'), R('balance', 'mix_score'), R('balance', 'mix_score')))],
    GR('What if', ('As it is', {'thr': 0.85}), ('Stricter, 70%', {'thr': 0.7}), ('Looser, 100%', {'thr': 1}), ('Stricter, 60%', {'thr': 0.6}), ('Looser, 95%', {'thr': 0.95}))))

# 10 --------------------------------------------------------------- late reply seat finder
HID_ = '{in:hh}'
def HHI(c_): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (HR(c_), HID_, HR('household_id'))
SIDE10 = HHI('side'); N10 = '(IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)+{in:extra})' % (HR('size'), HID_, HR('household_id'))
BT10 = 'IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (SIDE10, S1, IDX('latefit', 'table', 'rank_p1', '1'), SIDE10, S2, IDX('latefit', 'table', 'rank_p2', '1'), IDX('latefit', 'table', 'rank_sh', '1'))
FR10 = 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (SR_('free'), BT10, SR_('table_id'))
tools.append(TOOL('late_reply', 'Late Reply Seat Tool', 'Where does a late yes sit',
    'Type a pending household ID and the plus-ones you allow; the tool finds the table with room that fits the side best and says if you need to open a table.', [
    I('hh', 'Household ID of the late reply', D.GI[D.ST['rsvp'][0]]['household_id'], 'text'), I('extra', 'Plus-ones you allow', 0, 'int')], [
    O('Household', 'text', HHI('household')), O('Side', 'text', SIDE10), O('Guests who need seats', 'int', N10), O('Best table', 'text', BT10), O('Free seats there', 'int', FR10),
    O('Free seats in all', 'int', FREE_TOTAL), O('Yes guests still without a seat', 'int', NEED), O('Seats left after them', 'int', '%s-%s' % (FREE_TOTAL, NEED)),
    O('Verdict', 'text', 'IF(%s>=%s,%s&" "&%s,%s)' % (FR10, N10, v('Seat at'), BT10, v('Open a table')))],
    GR('What if', ('As it is', {'extra': 0}), ('Allow 1 plus-one', {'extra': 1}), ('Allow 2 plus-ones', {'extra': 2}), ('Allow 4 plus-ones', {'extra': 4}), ('Allow 6 plus-ones', {'extra': 6}))))

# 11 --------------------------------------------------------------- B list seat impact
YA = 'COUNTIFS(%s,%s,%s,%s)' % (G('list_ab'), LA, G('rsvp'), RY); PA = 'COUNTIFS(%s,%s,%s,%s)' % (G('list_ab'), LA, G('rsvp'), RP)
YB = 'COUNTIFS(%s,%s,%s,%s)' % (G('list_ab'), LB, G('rsvp'), RY); PB = 'COUNTIFS(%s,%s,%s,%s)' % (G('list_ab'), LB, G('rsvp'), RP)
NB = '(%s+ROUND(%s*{in:b_rate},0)+{in:extra_b})' % (YB, PB); OB = 'MAX(0,%s-%s-%s-ROUND(%s*{set:expected_yes_rate},0))' % (CAP, OTHERS, YA, PA)
tools.append(TOOL('b_impact', 'B List Seat Impact', 'Do the B list guests fit',
    'A list guests at your expected yes rate fill the room first; the tool counts the seats the B list needs at the yes rate you type, plus any B guests you add, against the seats still open.', [
    I('b_rate', 'Yes rate of pending B list guests, your estimate', 0.85, 'pct'), I('extra_b', 'B list guests you add', 0, 'int')], [
    O('A list guests expected', 'int', '%s+ROUND(%s*{set:expected_yes_rate},0)' % (YA, PA)), O('Seats open for the B list', 'int', OB), O('B list guests yes', 'int', YB), O('B list guests pending', 'int', PB),
    O('B list seats needed', 'int', NB), O('Seats left after the B list', 'int', '%s-%s' % (OB, NB)), O('Seats short', 'int', 'MAX(0,%s-%s)' % (NB, OB)),
    O('Verdict', 'text', 'IF(%s>%s,%s&" "&(%s-%s)&" "&%s,%s)' % (NB, OB, v('Short by'), NB, OB, v('seats'), v('Fits')))],
    GR('What if', ('As it is', {'b_rate': 0.85, 'extra_b': 0}), ('Everyone pending says yes', {'b_rate': 1}), ('Add 10 B list guests', {'extra_b': 10}), ('Add 6 B list guests', {'extra_b': 6}), ('Half say yes', {'b_rate': 0.5}))))

# 12 --------------------------------------------------------------- head table plan
HG = 'COUNTIFS(%s,%s)' % (G('table'), HEADT)
HN = '({set:couple_seats}+%s+{in:parents}+{in:party})' % HG
tools.append(TOOL('head_tool', 'Head Table Tool', 'Does the head table fit everyone',
    'The couple, the guests already at the head table and the parents or wedding party you add against the head table seats; any extra people move to the table with the most free seats.', [
    I('parents', 'Parents you add to the head table', 2, 'int'), I('party', 'Wedding party members you add', 0, 'int')], [
    O('Seats at the head table', 'int', '{set:head_seats}'), O('Seats for the couple', 'int', '{set:couple_seats}'), O('Guests seated at the head table', 'int', HG), O('People you want at the head table', 'int', HN),
    O('People over the head table', 'int', 'MAX(0,%s-{set:head_seats})' % HN), O('Free seats at the head table', 'int', 'MAX(0,{set:head_seats}-%s)' % HN),
    O('Table with most free seats', 'text', IDX('latefit', 'table_name', 'rank', '1')), O('Free seats there', 'int', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),0)' % (R('latefit', 'free'), R('latefit', 'rank'))),
    O('Verdict', 'text', 'IF(%s<={set:head_seats},%s,%s&" "&(%s-{set:head_seats})&" "&%s&" "&%s)' % (HN, v('Fits'), v('Move'), HN, v('to'), IDX('latefit', 'table_name', 'rank', '1')))],
    GR('What if', ('As it is', {'parents': 2, 'party': 0}), ('No parents', {'parents': 0}), ('Four parents', {'parents': 4}), ('Parents and 2 more', {'parents': 2, 'party': 2}), ('One parent', {'parents': 1}))))

# 13 --------------------------------------------------------------- household split check
tools.append(TOOL('split_tool', 'Household Split Tool', 'Which households sit apart',
    'Type the smallest household to check; the tool counts yes households split across two tables, the children in them and names the first one to fix.', [
    I('min', 'Smallest household to check', 2, 'int')], [
    O('Households checked', 'int', 'COUNTIFS(%s,">="&{in:min})' % R('hhsplit', 'size')), O('Households split', 'int', 'COUNTIFS(%s,">="&{in:min},%s,%s)' % (R('hhsplit', 'size'), R('hhsplit', 'flag'), v('Split'))),
    O('Households not yet seated', 'int', 'COUNTIFS(%s,">="&{in:min},%s,%s)' % (R('hhsplit', 'size'), R('hhsplit', 'flag'), v('To be set'))),
    O('Children in split households', 'int', 'SUMIFS(%s,%s,%s,%s,">="&{in:min})' % (R('hhsplit', 'children'), R('hhsplit', 'flag'), v('Split'), R('hhsplit', 'size'))),
    O('First split household', 'text', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),"")' % (R('hhsplit', 'household'), R('hhsplit', 'split_rank'))),
    O('Its guests', 'int', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),0)' % (R('hhsplit', 'size'), R('hhsplit', 'split_rank'))), O('Its tables used', 'int', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),0)' % (R('hhsplit', 'tables_used'), R('hhsplit', 'split_rank'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">="&{in:min},%s,%s)=0,%s,%s&" "&IFERROR(INDEX(%s,MATCH(1,%s,0)),""))' % (R('hhsplit', 'size'), R('hhsplit', 'flag'), v('Split'), v('Keep together'), v('Split'), R('hhsplit', 'household'), R('hhsplit', 'split_rank')))],
    GR('What if', ('Households of 2 or more', {'min': 2}), ('Households of 3 or more', {'min': 3}), ('Households of 4 or more', {'min': 4}), ('Households of 5', {'min': 5}), ('All yes households', {'min': 1}))))

# 14 --------------------------------------------------------------- place card list builder
tools.append(TOOL('card_tool', 'Place Card List Builder', 'How many place cards do we print',
    'Guests with a table get a card; the tool adds spare cards, counts the guests with no table and the cards with no meal marker, and the table signs.', [
    I('spare', 'Spare cards for late replies', 6, 'int')], [
    O('Guests with a table', 'int', 'SUM(%s)' % G('seated')), O('Cards to print with spares', 'int', 'SUM(%s)+{in:spare}' % G('seated')), O('Yes guests missing a table', 'int', NEED), O('Pending guests', 'int', PENDG),
    O('Cards with no meal marker', 'int', 'COUNTIFS(%s,%s)' % (R('cards', 'marker'), v('No marker'))), O('Table signs to print', 'int', 'COUNTIFS(%s,">0")' % SR_('seated')), O('Days to the print date', 'int', '{set:wedding_day}-{set:print_days}-{today}'),
    O('Verdict', 'text', 'IF(%s=0,%s&" "&(SUM(%s)+{in:spare})&" "&%s,%s&" "&(SUM(%s)+{in:spare})&" "&%s&", "&%s&" "&%s)' % (NEED, v('Print'), G('seated'), v('cards'), v('Print'), G('seated'), v('cards'), NEED, v('guests missing a table')))],
    GR('What if', ('As it is', {'spare': 6}), ('No spare cards', {'spare': 0}), ('Ten spare cards', {'spare': 10}), ('Fifteen spare cards', {'spare': 15}), ('Three spare cards', {'spare': 3}))))

# 15 --------------------------------------------------------------- rental quantity calculator
SE15 = '({in:guests}+%s)' % OTHERS; TB15 = 'ROUNDUP(%s/%s,0)' % (SE15, SZ)
CH15 = 'ROUNDUP(%s*(1+{in:spare}),0)' % SE15
tools.append(TOOL('rental_tool', 'Rental Quantity Calculator', 'How many chairs, linens, plates and glasses do we order',
    'From the guests you seat and the final tables: chairs, tables, linens, plates and glasses with your spare share, what you have ordered and the chairs still to order.', [
    I('guests', 'Guests you seat', 117, 'int'), I('spare', 'Spare share of every item', 0.05, 'pct'), I('courses', 'Plates for each guest', 2, 'int'), I('glasses', 'Glasses for each guest', 3, 'int'),
    I('linens', 'Linens for each table', 1, 'int')], [
    O('Seats at the tables', 'int', SE15), O('Tables', 'int', TB15), O('Chairs to order', 'int', CH15), O('Linens to order', 'int', '%s*{in:linens}+2' % TB15),
    O('Plates to order', 'int', 'ROUNDUP(%s*{in:courses}*(1+{in:spare}),0)' % SE15), O('Glasses to order', 'int', 'ROUNDUP(%s*{in:glasses}*(1+{in:spare}),0)' % SE15),
    O('Chairs ordered so far', 'int', ORD('Chairs')), O('Chairs still to order', 'int', 'MAX(0,%s-%s)' % (CH15, ORD('Chairs'))), O('Cost of the chairs', 'money', 'ROUND(%s*SUMIFS(%s,%s,%s),0)' % (CH15, R('rentals', 'unit_cost'), R('rentals', 'item'), tok('ritem', 'Chairs'))),
    O('Cost of the whole rental list', 'money', 'SUM(%s)' % R('rentals', 'cost')),
    O('Verdict', 'text', 'IF(%s<=%s,%s,%s&" "&(%s-%s)&" "&%s)' % (CH15, ORD('Chairs'), v('Chairs covered'), v('Order'), CH15, ORD('Chairs'), v('chairs')))],
    GR('What if', ('As it is', {'guests': 117}), ('Add 10 guests', {'guests': 127}), ('No spare', {'spare': 0}), ('Spare 10%', {'spare': 0.1}), ('Cut 15 guests', {'guests': 102}))))

# 16 --------------------------------------------------------------- spare seat reserve
NH = 'COUNTIFS(%s,">="&{in:hold})' % R('fill', 'free')
HELD = '(%s*{in:hold}+SUMIFS(%s,%s,"<"&{in:hold},%s,">0"))' % (NH, R('fill', 'free'), R('fill', 'free'), R('fill', 'free'))
FULL = 'COUNTIFS(%s,0)' % R('fill', 'free')
tools.append(TOOL('spare_tool', 'Spare Seat Reserve Tool', 'How many seats do we hold for late replies',
    'Type the seats to hold at each table; the tool counts the seats held, the tables that stay full and the late replies you still expect.', [
    I('hold', 'Seats to hold at each table', 2, 'int')], [
    O('Free seats in all', 'int', FREE_TOTAL), O('Tables with a free seat', 'int', 'COUNTIFS(%s,">0")' % R('fill', 'free')), O('Seats held', 'int', HELD), O('Tables that stay full', 'int', FULL),
    O('Late seats you expect to need', 'int', LATE_NEED), O('Seats still to find', 'int', 'MAX(0,%s-%s)' % (LATE_NEED, HELD)), O('Free seats after the hold', 'int', '%s-%s' % (FREE_TOTAL, HELD)),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&", "&%s&" "&%s' % (v('Hold'), HELD, v('seats'), FULL, v('tables stay full')))],
    GR('What if', ('As it is', {'hold': 2}), ('Hold 1 a table', {'hold': 1}), ('Hold 3 a table', {'hold': 3}), ('Hold 4 a table', {'hold': 4}), ('Hold none', {'hold': 0}))))

# 17 --------------------------------------------------------------- seat swap suggester
def SX(c_): return IX('swaps', c_, '{in:no}')
tools.append(TOOL('swap_tool', 'Seat Swap Suggester', 'What is the smallest move that clears a conflict',
    'Pick a rule number in fix order; the tool names the guest to move, the table to move to, the seats free there and a guest to swap with when the table is full.', [
    I('no', 'Rule number in fix order', 1, 'int')], [
    O('Rule', 'text', SX('rule_id')), O('Rule status', 'text', SX('status')), O('Guest to move', 'text', SX('guest')), O('From table', 'text', SX('from_table')), O('To table', 'text', SX('to_table')),
    O('Free seats there', 'int', IXN('swaps', 'free_there', '{in:no}')), O('Guest to swap with', 'text', SX('partner')), O('Conflicts to clear in all', 'int', 'SUM(%s)' % R('swaps', 'fixed')),
    O('Verdict', 'text', 'IF(%s<>%s,%s,IF(%s>0,%s&" "&%s&" "&%s&" "&%s,%s&" "&%s&" "&%s&" "&%s))' % (SX('status'), v('Conflict'), v('No swap needed'), IXN('swaps', 'free_there', '{in:no}'), v('Move'), SX('guest'), v('to'), SX('to_table'),
                                                                                                          v('Swap'), SX('guest'), v('with'), SX('partner')))],
    GR('What if', ('First rule', {'no': 1}), ('Second rule', {'no': 2}), ('Third rule', {'no': 3}), ('Fourth rule', {'no': 4}))))

# 18 --------------------------------------------------------------- final sign-off
def SG(k): return IXN('signoff', 'count', str(k))
FIX = 'COUNTIFS(%s,">0")' % R('signoff', 'count')
tools.append(TOOL('signoff_tool', 'Final Seating Sign-off', 'Is the seating plan ready to print',
    'Eight checks from the other pages: seats, conflicts, tables over, split households, meals, rentals, head table and pending replies. It adds the print date and says what is left.', [
    I('days', 'Days before the wedding you print', 10, 'int')], [
    O('Yes guests without a seat', 'int', SG(1)), O('Seat rule conflicts', 'int', SG(2)), O('Tables over capacity', 'int', SG(3)), O('Households split', 'int', SG(4)), O('Yes guests at a table without a meal', 'int', SG(5)),
    O('Rental items still to order', 'int', SG(6)), O('People over the head table', 'int', SG(7)), O('Pending replies', 'int', SG(8)), O('Print date', 'date', '{set:wedding_day}-{in:days}'),
    O('Days to the print date', 'int', '{set:wedding_day}-{in:days}-{today}'), O('Checks still open', 'int', FIX),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (FIX, v('Ready to print'), FIX, v('to fix')))],
    GR('What if', ('Print 10 days before', {'days': 10}), ('Print 14 days before', {'days': 14}), ('Print 7 days before', {'days': 7}), ('Print 21 days before', {'days': 21}), ('Print 5 days before', {'days': 5}))))
assert len(tools) == 18, len(tools)
