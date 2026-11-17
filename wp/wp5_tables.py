"""Wedding suite part 5: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp5_lists import *
import wp5_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def LIT(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
def CPL(): return CA('couple', 'Couple', 'text', '{set:couple}', 20)
def IDX(t, c_, kc, val): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R(t, c_), val, R(t, kc))


YES = '{list:yesno.yes}'
RY = tok('rsvp', 'Yes'); RN = tok('rsvp', 'No'); RP = tok('rsvp', 'Pending')
S1 = tok('side', 'Partner 1'); S2 = tok('side', 'Partner 2'); SS = tok('side', 'Shared')
FAM = tok('tier', 'Family'); CLO = tok('tier', 'Close friends'); FRI = tok('tier', 'Friends'); COL = tok('tier', 'Colleagues')
LA = tok('listab', 'A list'); LB = tok('listab', 'B list')
CHILD = tok('age', 'Child'); ADULT = tok('age', 'Adult')
G = lambda c_: R('guests', c_)
HR = lambda c_: R('households', c_)
SR_ = lambda c_: R('seating', c_)
GN = 'COUNTIFS(%s,"<>")' % G('guest_id')
YESG = 'COUNTIFS(%s,%s,%s,"<>")' % (G('rsvp'), RY, G('guest_id'))
NOG = 'COUNTIFS(%s,%s,%s,"<>")' % (G('rsvp'), RN, G('guest_id'))
PENDG = 'COUNTIFS(%s,%s,%s,"<>")' % (G('rsvp'), RP, G('guest_id'))
EXP = '(%s+%s*{set:expected_yes_rate})' % (YESG, PENDG)
OTHERS = '({set:couple_seats}+{set:vendor_seats})'
SEATS_EXP = '(ROUND(%s,0)+%s)' % (EXP, OTHERS)
SEATS_ALL = '(%s+%s)' % (GN, OTHERS)
CAP = '{set:venue_capacity}'
NEED = 'SUM(%s)' % G('need_seat')
TBL_N = 'ROUNDUP(%s/{set:table_size},0)' % SEATS_EXP
def SP(item): return 'SUMIFS(%s,%s,%s)' % (R('space', 'value'), R('space', 'item'), tok('sitem', item))
USABLE = '(%s-%s-%s-%s-%s-%s)' % (SP('Venue floor area'), SP('Dance floor'), SP('Buffet area'), SP('Stage and band'), SP('Bar and cake tables'), SP('Walkways and exits'))
HEADT = 'INDEX(%s,1)' % SR_('table_id')
FREE_TOTAL = 'SUM(%s)' % SR_('free')
LATE_NEED = '(%s+ROUND(%s*{set:expected_yes_rate},0))' % (NEED, PENDG)
def VER_FIT(h, cap): return 'IF(%s>%s,%s&" "&(%s-%s),IF(%s>=%s*{set:tight_pct},%s,%s))' % (h, cap, v('Over by'), h, cap, h, cap, v('Tight'), v('Fits'))
FIXN = 'COUNTIFS(%s,">0")' % R('signoff', 'count')
def QTY(item): return 'SUMIFS(%s,%s,%s)' % (R('rentals', 'quantity'), R('rentals', 'item'), tok('ritem', item))
def ORD(item): return 'SUMIFS(%s,%s,%s)' % (R('rentals', 'ordered'), R('rentals', 'item'), tok('ritem', item))

settings = [
    S('couple', 'Your names as the couple', 'text', COUPLE), S('partner1', 'Name of partner 1', 'text', PARTNER1), S('partner2', 'Name of partner 2', 'text', PARTNER2),
    S('wedding_day', 'Wedding day', 'date', iso(WEDDING_DAY)),
    S('venue_capacity', 'Seated capacity of the venue, from the venue contract', 'int', VENUE_CAPACITY), S('table_size', 'Seats at one table, your plan', 'int', TABLE_SIZE),
    S('couple_seats', 'Seats for the couple, your count', 'int', 2), S('vendor_seats', 'Seats for vendors who eat with you, your count', 'int', 4),
    S('expected_yes_rate', 'Expected yes rate of pending replies, typical, edit', 'pct', EXPECTED_YES_RATE), S('tight_pct', 'Share of the seats that counts as tight, your own rule', 'pct', 0.95),
    S('one_side_pct', 'Share of one side that counts as all one side, your own rule', 'pct', 0.85), S('head_seats', 'Seats at the head table, your plan', 'int', 10),
    S('front_row', 'Front row seats held for family, your count', 'int', 6), S('late_size', 'Seats a late reply needs, your estimate', 'int', 2), S('print_days', 'Days before the wedding to print place cards, your plan', 'int', 10),
    S('headcount_date', 'Date the final headcount is due, from the caterer contract', 'date', iso(HEADCOUNT_DATE)),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 guests ----------------------------------------------------------------------------------
tables.append(T('guests', 'Guests', 'Guests', 'One row per guest: household, side, tier, list, age group, RSVP, meal, a short dietary note and the table. Names only, no addresses and no health details; the seated flag and the seat finders fill in.', [
    C('guest_id', 'Guest ID', 'text', 9, required=True), C('guest', 'Guest', 'text', 22), REF('household_id', 'Household ID', 'households.household_id', 10), C('household', 'Household', 'text', 24),
    LST('side', 'Side', 'side', 12), LST('tier', 'Tier', 'tier', 14), LST('list_ab', 'List', 'listab', 9), LST('age_group', 'Age group', 'age', 9), LST('rsvp', 'RSVP', 'rsvp', 9),
    LST('meal', 'Meal', 'meal', 15), LST('dietary', 'Dietary note', 'dietary', 14), LST('table', 'Table', 'table', 9),
    CA('idnum', 'Order number', 'int', 'IFERROR(VALUE(MID({col:guest_id},4,6)),0)', 8),
    CA('seated', 'Seated', 'int', 'IF({col:table}<>"",1,0)', 8), CA('seated_yes', 'Yes guest seated', 'int', 'IF(AND({col:table}<>"",{col:rsvp}=%s),1,0)' % RY, 9),
    CA('need_seat', 'Yes guest without a seat', 'int', 'IF(AND({col:rsvp}=%s,{col:table}=""),1,0)' % RY, 9), CA('pend', 'Pending', 'int', 'IF({col:rsvp}=%s,1,0)' % RP, 8),
    CA('want_score', 'Seat finder score', 'num', 'IF({col:need_seat}+{col:pend}=0,0,IF({col:need_seat}=1,2000,1000)+(1000-{col:idnum})/1000)', 10),
    CA('want_rank', 'Seat finder rank', 'int', 'IF({col:want_score}>0,COUNTIFS({range:guests.want_score},">"&{col:want_score})+1,"")', 9),
    CA('first_at_table', 'First of household at table', 'int', 'IF({col:table}<>"",IF(COUNTIFS({range:guests.household_id},{col:household_id},{range:guests.table},{col:table},{range:guests.idnum},"<"&{col:idnum})=0,1,0),0)', 10),
    CA('hh_seat_rank', 'Household seat order', 'int', 'IF({col:seated}=1,COUNTIFS({range:guests.household_id},{col:household_id},{range:guests.seated},1,{range:guests.idnum},"<="&{col:idnum}),0)', 9),
    CA('hh_key', 'Household key', 'text', '{col:household_id}&"|"&{col:hh_seat_rank}', 10),
    CA('hh_table', 'Household table', 'text', 'IFERROR(INDEX({range:guests.table},MATCH({col:household_id}&"|1",{range:guests.hh_key},0))&"","")', 10),
    CA('tk_seq', 'Seat at table', 'int', 'IF({col:table}<>"",COUNTIFS({range:guests.table},{col:table},{range:guests.idnum},"<="&{col:idnum}),"")', 8),
    CA('tkey', 'Table key', 'text', 'IF({col:table}<>"",{col:table}&"|"&{col:tk_seq},"")', 10),
    CA('card_seq', 'Place card order', 'int', 'IF({col:seated}=1,COUNTIFS({range:guests.seated},1,{range:guests.idnum},"<="&{col:idnum}),"")', 9)],
    D.guests_d(), 400, [A('rsvp', '= ' + RP, 'warn'), A('rsvp', '= ' + RY, 'good')]))

# 2 households -------------------------------------------------------------------------------
tables.append(T('households', 'Households', 'Households', 'One row per household (one invitation, several people): contact, side, guests, RSVP and list; the seats used, the tables used and a split flag fill in from Guests.', [
    C('household_id', 'Household ID', 'text', 10, required=True), C('household', 'Household', 'text', 24), C('contact', 'Contact', 'text', 20), C('phone', 'Phone', 'text', 18),
    LST('side', 'Side', 'side', 12), C('size', 'Guests', 'int', 8), LST('rsvp', 'RSVP', 'rsvp', 9), LST('list_ab', 'List', 'listab', 9),
    CA('idnum', 'Order number', 'int', 'IFERROR(VALUE(MID({col:household_id},4,5)),0)', 8),
    CA('seated_guests', 'Guests seated', 'int', 'COUNTIFS({range:guests.household_id},{col:household_id},{range:guests.table},"<>")', 9),
    CA('tables_used', 'Tables used', 'int', 'SUMIFS({range:guests.first_at_table},{range:guests.household_id},{col:household_id})', 8),
    CA('children', 'Children', 'int', 'COUNTIFS({range:guests.household_id},{col:household_id},{range:guests.age_group},%s)' % CHILD, 8),
    CA('first_table', 'First table', 'text', 'IFERROR(INDEX({range:guests.table},MATCH({col:household_id}&"|1",{range:guests.hh_key},0))&"","")', 10),
    CA('table_name', 'Table name', 'text', 'IF({col:first_table}="",%s,IFERROR(INDEX(%s,MATCH({col:first_table},%s,0))&"",%s))' % (v('To be set'), SR_('table_name'), SR_('table_id'), v('To be set')), 16),
    CA('status', 'Seating status', 'text', 'IF({col:rsvp}=%s,%s,IF({col:seated_guests}=0,%s,IF({col:tables_used}>1,%s,%s)))' % (RN, v('Not coming'), v('To be set'), v('Split'), v('Together')), 12),
    CA('split_seq', 'Split check order', 'int', 'IF(AND({col:size}>=2,{col:rsvp}=%s),COUNTIFS({range:households.size},">=2",{range:households.rsvp},%s,{range:households.idnum},"<="&{col:idnum}),"")' % (RY, RY), 8),
    CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 12), CPL()],
    D.hh_d(), 300, [A('status', '= ' + v('Split'), 'warn'), A('status', '= ' + v('To be set'), 'bad'), A('status', '= ' + v('Together'), 'good')]))

# 3 seating tables (also the hub of the message figures) ----------------------------------------------
tables.append(T('seating', 'Seating Tables', 'Seating Tables', 'One row per table: capacity, kind and seats kept for the couple; seated guests, free seats and the side mix fill in. The plan totals and the phone numbers for the texts sit at the right.', [
    LST('table_id', 'Table', 'table', 9, required=True), C('table_name', 'Table name', 'text', 18), C('capacity', 'Seats', 'int', 8), LST('kind', 'Kind', 'tkind', 13), C('reserved', 'Seats for the couple', 'int', 10),
    CA('seated', 'Seated', 'int', 'COUNTIFS(%s,{col:table_id})' % G('table'), 8), CA('free', 'Free seats', 'int', '{col:capacity}-{col:reserved}-{col:seated}', 9),
    CA('side_mix', 'Side mix, P1 / P2 / shared', 'text', '%s&" / "&%s&" / "&%s' % (LKN('fill.p1', 'fill.table', 'table_id'), LKN('fill.p2', 'fill.table', 'table_id'), LKN('fill.shared', 'fill.table', 'table_id')), 14),
    CA('headcount', 'Expected headcount seated', 'int', SEATS_EXP, 10), CA('tables_total', 'Tables needed', 'int', TBL_N, 9), CA('spare', 'Seats spare at expected headcount', 'int', '%s-%s' % (CAP, SEATS_EXP), 11),
    CA('over', 'Seats over if everyone says yes', 'int', 'MAX(0,%s-%s)' % (SEATS_ALL, CAP), 11), CA('unseated', 'Yes guests without a seat', 'int', NEED, 10),
    CA('conflicts', 'Seat rule conflicts', 'int', 'SUM(%s)' % R('rules', 'conflict'), 9),
    CA('b_open', 'Open seats for the B list', 'int', 'MAX(0,%s-%s-COUNTIFS(%s,%s,%s,%s)-ROUND(COUNTIFS(%s,%s,%s,%s)*{set:expected_yes_rate},0))' % (
        CAP, OTHERS, G('list_ab'), LA, G('rsvp'), RY, G('list_ab'), LA, G('rsvp'), RP), 9),
    CA('b_need', 'B list seats needed', 'int', 'COUNTIFS(%s,%s,%s,%s)+ROUND(COUNTIFS(%s,%s,%s,%s)*{set:expected_yes_rate},0)' % (G('list_ab'), LB, G('rsvp'), RY, G('list_ab'), LB, G('rsvp'), RP), 9),
    CA('print_date', 'Print date for place cards', 'date', '{set:wedding_day}-{set:print_days}', 12), CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 12),
    CA('headcount_date', 'Headcount date', 'date', '{set:headcount_date}', 12),
    CA('venue_capacity', 'Seated capacity', 'int', CAP, 9), CA('table_size', 'Table size', 'int', '{set:table_size}', 8), CA('head_seats', 'Head table seats', 'int', '{set:head_seats}', 9),
    CA('front_row', 'Front row seats', 'int', '{set:front_row}', 8), CA('vendor_meals', 'Vendor meals', 'int', '{set:vendor_seats}', 8), CA('dance_area', 'Dance floor area', 'num', SP('Dance floor'), 9),
    CA('hold_n', 'Seats held for late replies', 'int', 'SUM(%s)' % R('spare', 'hold'), 9),
    CA('changes', 'Seating changes planned', 'int', 'COUNTIFS(%s,%s)' % (R('swaps', 'action'), v('Move')) + '+COUNTIFS(%s,%s)' % (R('swaps', 'action'), v('Swap')), 9),
    CA('sign_status', 'Sign-off status', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s)' % (FIXN, v('Ready'), v('Not ready,'), FIXN, v('to fix')), 16),
    LIT('partner_phone', 'Partner phone', D.P2_PHONE), LIT('venue_phone', 'Venue phone', D.VENUE_PHONE), LIT('caterer_phone', 'Caterer phone', D.CATERER_PHONE), LIT('rentals_phone', 'Rentals phone', D.RENTALS_PHONE),
    LIT('dayof_phone', 'Day-of coordinator phone', D.DAYOF_PHONE), LIT('lead_phone', 'Wedding party lead phone', D.LEAD1_PHONE), LIT('helper_phone', 'Helper phone', D.HELPER_PHONE),
    LIT('parent1_phone', 'Parent of partner 1 phone', D.PAR1_PHONE), LIT('parent2_phone', 'Parent of partner 2 phone', D.PAR2_PHONE), LIT('officiant_phone', 'Officiant phone', D.OFFICIANT_PHONE),
    LIT('hotel_phone', 'Hotel phone', D.HOTEL_PHONE), CPL()],
    D.seating_d(), 50, [A('free', '= 0', 'warn'), A('free', '< 0', 'bad')]))

# 4 seat rules -----------------------------------------------------------------------------------
TG = tok('rkind', 'Keep together')
RULE_CONF = 'IF({col:kind}=%s,IF(AND({col:table_a}<>"",{col:table_b}<>"",{col:table_a}<>{col:table_b}),1,0),IF(AND({col:table_a}<>"",{col:table_a}={col:table_b}),1,0))' % TG
RULE_KEPT = 'IF({col:kind}=%s,IF(AND({col:table_a}<>"",{col:table_a}={col:table_b}),1,0),IF(AND({col:table_a}<>"",{col:table_b}<>"",{col:table_a}<>{col:table_b}),1,0))' % TG
tables.append(T('rules', 'Seat Rules', 'Seat Rules', 'Keep-together and keep-apart rules between two guests with the reason Family, Friends, Work or Needs space; the tables, the status and the conflict flag fill in from the seating.', [
    C('rule_id', 'Rule ID', 'text', 9, required=True), LST('kind', 'Kind', 'rkind', 14), REF('guest_a', 'Guest A', 'guests.guest_id', 10), REF('guest_b', 'Guest B', 'guests.guest_id', 10),
    LST('reason', 'Reason', 'reason', 13), C('agreed_on', 'Agreed on', 'date', 12),
    CA('idnum', 'Order number', 'int', 'IFERROR(VALUE(MID({col:rule_id},4,3)),0)', 8), CA('name_a', 'Name A', 'text', LKT('guests.guest', 'guests.guest_id', 'guest_a').replace('{col:guest_a}', '{col:guest_a}'), 22),
    CA('name_b', 'Name B', 'text', LKT('guests.guest', 'guests.guest_id', 'guest_b'), 22), CA('table_a', 'Table A', 'text', LKT('guests.table', 'guests.guest_id', 'guest_a'), 9), CA('table_b', 'Table B', 'text', LKT('guests.table', 'guests.guest_id', 'guest_b'), 9),
    CA('conflict', 'Conflict', 'int', RULE_CONF, 8), CA('kept', 'Kept', 'int', RULE_KEPT, 8), CA('one', 'Rule', 'int', '1', 6),
    CA('status', 'Status', 'text', 'IF(OR({col:table_a}="",{col:table_b}=""),%s,IF({col:conflict}=1,%s,%s))' % (v('Not placed'), v('Conflict'), v('Kept')), 11),
    CA('rank_key', 'Fix order score', 'num', '{col:conflict}*1000+IF({col:status}=%s,500,0)+(1000-{col:idnum})/1000' % v('Not placed'), 10),
    CA('rank', 'Fix order', 'int', 'COUNTIFS({range:rules.rank_key},">"&{col:rank_key})+1', 8)],
    D.rules_d(), 60, [A('status', '= ' + v('Conflict'), 'bad'), A('status', '= ' + v('Not placed'), 'warn'), A('status', '= ' + v('Kept'), 'good')]))

# 5 space inputs ------------------------------------------------------------------------------------
tables.append(T('space', 'Space Inputs', 'Space Inputs', 'Eight numbers from your floor plan: floor area, dance floor, buffet, stage, bar, walkways, the least area per guest and the share who dance. Square metres; edit with your own measures.', [
    LST('item', 'Item', 'sitem', 26, required=True), C('value', 'Value', 'num', 10), C('note', 'Note', 'text', 44)], D.space_d(), 50))

# 6 table size options ---------------------------------------------------------------------------------
tables.append(T('tsizes', 'Table Size Options', 'Table Size Options', 'Five table sizes: the tables you need and the empty seats at the expected headcount with the couple and vendor seats.', [
    LST('size', 'Seats per table', 'tsize', 14, required=True), CA('tables', 'Tables needed', 'int', 'ROUNDUP(%s/VALUE({col:size}),0)' % SEATS_EXP, 12),
    CA('empty', 'Empty seats', 'int', '{col:tables}*VALUE({col:size})-%s' % SEATS_EXP, 12)], D.tsizes_d(), 50))

# 7 capacity scenarios -------------------------------------------------------------------------------------
tables.append(T('scenarios', 'Capacity Scenarios', 'Capacity Scenarios', 'Twelve headcounts against the seated capacity: the pending yes rate, declines that change their mind and guests added or cut. Seats, tables, floor area and a verdict fill in.', [
    LST('scenario', 'Scenario', 'scen', 28, required=True), C('yes_rate', 'Pending yes rate', 'pct', 10), C('include_no', 'Declines say yes', 'bool', 9), C('add_guests', 'Guests added or cut', 'int', 10),
    CA('headcount', 'Headcount', 'int', '%s+ROUND(%s*{col:yes_rate},0)+IF({col:include_no}=%s,%s,0)+{col:add_guests}' % (YESG, PENDG, YES, NOG), 10),
    CA('seats', 'Seats needed', 'int', '{col:headcount}+%s' % OTHERS, 9), CA('capacity', 'Seated capacity', 'int', CAP, 9), CA('tables', 'Tables needed', 'int', 'ROUNDUP({col:seats}/{set:table_size},0)', 9),
    CA('empty', 'Empty seats', 'int', '{col:tables}*{set:table_size}-{col:seats}', 9), CA('over', 'Seats over capacity', 'int', 'MAX(0,{col:seats}-{col:capacity})', 10),
    CA('floor_per_guest', 'Floor area per guest', 'num', 'IFERROR(%s/{col:seats},0)' % USABLE, 10), CA('floor_ok', 'Floor space enough', 'int', 'IF({col:floor_per_guest}>=%s,1,0)' % SP('Area per guest, minimum'), 9),
    CA('verdict', 'Verdict', 'text', VER_FIT('{col:seats}', '{col:capacity}'), 12)],
    D.scen_d(), 50, [A('verdict', '= ' + v('Fits'), 'good'), A('verdict', '= ' + v('Tight'), 'warn')]))

# 8 table fill ------------------------------------------------------------------------------------------------
def SIDEC(s): return 'COUNTIFS(%s,{col:table},%s,%s)' % (G('table'), G('side'), s)
tables.append(T('fill', 'Table Fill', 'Table Fill', 'One row per table: seated guests, free seats, the guests of partner 1, partner 2 and shared friends, and the fill share of the seats you can use.', [
    LST('table', 'Table', 'table', 9, required=True), CA('table_name', 'Table name', 'text', LKT('seating.table_name', 'seating.table_id', 'table'), 18),
    CA('seated', 'Seated', 'int', 'COUNTIFS(%s,{col:table})' % G('table'), 8), CA('free', 'Free seats', 'int', LKN('seating.free', 'seating.table_id', 'table'), 9),
    CA('p1', 'Partner 1', 'int', SIDEC(S1), 8), CA('p2', 'Partner 2', 'int', SIDEC(S2), 8), CA('shared', 'Shared', 'int', SIDEC(SS), 8),
    CA('fill_share', 'Fill share', 'pct', 'IFERROR(({col:seated}+%s)/%s,0)' % (LKN('seating.reserved', 'seating.table_id', 'table'), LKN('seating.capacity', 'seating.table_id', 'table')), 9),
    CA('kind', 'Kind', 'text', LKT('seating.kind', 'seating.table_id', 'table'), 13), CA('guests_text', 'Guests', 'text', '{col:seated}&"/"&%s' % LKN('seating.capacity', 'seating.table_id', 'table'), 10)],
    D.tid_d('table'), 50, [A('free', '= 0', 'warn'), A('fill_share', '>= 1', 'good')]))

# 9 unseated guests -----------------------------------------------------------------------------------------------
def UG(c_): return LKT('guests.%s' % c_, 'guests.guest_id', 'guest_id')
tables.append(T('unseated', 'Unseated Guests', 'Unseated Guests', 'Yes guests with no table first, then pending guests, with the household table and the suggested table. A yes guest sits with the household if a seat is free, else at the best table for the side.', [
    C('no', 'Number', 'int', 8, required=True), CA('guest_id', 'Guest ID', 'text', IDX('guests', 'guest_id', 'want_rank', '{col:no}'), 9), CA('guest', 'Guest', 'text', UG('guest'), 22),
    CA('rsvp', 'RSVP', 'text', UG('rsvp'), 9), CA('list_ab', 'List', 'text', UG('list_ab'), 9), CA('household', 'Household', 'text', UG('household'), 24), CA('side', 'Side', 'text', UG('side'), 12),
    CA('hh_table', 'Household table', 'text', 'IF(%s="",%s,%s)' % (UG('hh_table'), v('No table yet'), UG('hh_table')), 12),
    CA('hh_free', 'Free seats at the household table', 'int', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (SR_('free'), UG('hh_table'), SR_('table_id')), 11),
    CA('best_side', 'Best table for the side', 'text', 'IF({col:side}=%s,%s,IF({col:side}=%s,%s,%s))' % (
        S1, IDX('latefit', 'table', 'rank_p1', '1'), S2, IDX('latefit', 'table', 'rank_p2', '1'), IDX('latefit', 'table', 'rank_sh', '1')), 12),
    CA('suggested', 'Suggested table', 'text', 'IF({col:rsvp}<>%s,%s,IF({col:hh_free}>0,{col:hh_table},{col:best_side}))' % (RY, v('Wait for the reply')), 16),
    CA('suggested_free', 'Free seats there', 'int', 'IFERROR(INDEX(%s,MATCH({col:suggested},%s,0)),0)' % (SR_('free'), SR_('table_id')), 9),
    CA('status', 'Status', 'text', 'IF({col:rsvp}=%s,%s,%s)' % (RY, v('Needs a seat'), v('Waiting for a reply')), 14), CPL()],
    D.ranks(D.N_UNSEAT), 60, [A('status', '= ' + v('Needs a seat'), 'bad'), A('status', '= ' + v('Waiting for a reply'), 'warn')]))

# 10 rule conflicts -------------------------------------------------------------------------------------------------
def RC(c_): return IDX('rules', c_, 'rank', '{col:no}')
tables.append(T('conflicts', 'Rule Conflicts', 'Rule Conflicts', 'Every seat rule in fix order: conflicts first, then rules with a guest not yet seated, then rules that hold. Tables, status and the fix to try fill in.', [
    C('no', 'Number', 'int', 8, required=True), CA('rule_id', 'Rule ID', 'text', RC('rule_id'), 9), CA('kind', 'Kind', 'text', RC('kind'), 14), CA('guest_a', 'Guest A', 'text', RC('name_a'), 22), CA('guest_b', 'Guest B', 'text', RC('name_b'), 22),
    CA('table_a', 'Table A', 'text', RC('table_a'), 9), CA('table_b', 'Table B', 'text', RC('table_b'), 9), CA('flag', 'Conflict flag', 'text', RC('status'), 12),
    CA('reason', 'Reason', 'text', RC('reason'), 12), CA('fix', 'Fix to try', 'text', 'IF({col:flag}=%s,IF({col:kind}=%s,%s,%s),%s)' % (v('Conflict'), TG, v('Seat them together'), v('Seat them apart'), v('No fix needed')), 18), CPL()],
    D.ranks(14), 50, [A('flag', '= ' + v('Conflict'), 'bad'), A('flag', '= ' + v('Kept'), 'good')]))

# 11 household split check ------------------------------------------------------------------------------------------------
def HS(c_): return IDX('households', c_, 'split_seq', '{col:no}')
def HL(c_): return 'IFERROR(INDEX(%s,MATCH({col:household_id},%s,0)),0)' % (HR(c_), HR('household_id'))
tables.append(T('hhsplit', 'Household Split Check', 'Household Split Check', 'Yes households of two or more guests: guests, seats used, tables used and a flag. A household that sits at two tables is split; children sit with their household.', [
    C('no', 'Number', 'int', 8, required=True), CA('household_id', 'Household ID', 'text', HS('household_id'), 10), CA('household', 'Household', 'text', HS('household'), 24), CA('size', 'Guests', 'int', HL('size'), 8),
    CA('seated', 'Seated', 'int', HL('seated_guests'), 8), CA('tables_used', 'Tables used', 'int', HL('tables_used'), 9), CA('children', 'Children', 'int', HL('children'), 9),
    CA('flag', 'Split flag', 'text', 'IF({col:seated}=0,%s,IF({col:tables_used}>1,%s,%s))' % (v('To be set'), v('Split'), v('Together')), 12), CA('first_table', 'First table', 'text', IDX('households', 'table_name', 'household_id', '{col:household_id}'), 16),
    CA('split_rank', 'Split order', 'int', 'IF({col:flag}=%s,COUNTIFS({range:hhsplit.flag},%s,{range:hhsplit.no},"<="&{col:no}),"")' % (v('Split'), v('Split')), 8)],
    D.ranks(D.N_SPLIT), 60, [A('flag', '= ' + v('Split'), 'warn'), A('flag', '= ' + v('Together'), 'good'), A('flag', '= ' + v('To be set'), 'bad')]))

# 12 table balance --------------------------------------------------------------------------------------------------------------
def TIERC(t): return 'COUNTIFS(%s,{col:table},%s,%s)' % (G('table'), G('tier'), t)
def FL(c_): return LKN('fill.%s' % c_, 'fill.table', 'table')
tables.append(T('balance', 'Table Balance', 'Table Balance by Side and Tier', 'One row per table: guests by side and by tier, the largest side share and a flag. A table of one side is fine for family; a mixed table should not be all one side.', [
    LST('table', 'Table', 'table', 9, required=True), CA('p1', 'Partner 1', 'int', FL('p1'), 8), CA('p2', 'Partner 2', 'int', FL('p2'), 8), CA('shared', 'Shared', 'int', FL('shared'), 8),
    CA('family', 'Family', 'int', TIERC(FAM), 8), CA('close', 'Close friends', 'int', TIERC(CLO), 9), CA('friends', 'Friends', 'int', TIERC(FRI), 8), CA('colleagues', 'Colleagues', 'int', TIERC(COL), 9),
    CA('seated', 'Seated', 'int', '{col:p1}+{col:p2}+{col:shared}', 8), CA('top_share', 'Largest side share', 'pct', 'IFERROR(MAX({col:p1},{col:p2},{col:shared})/{col:seated},0)', 10),
    CA('kind', 'Kind', 'text', LKT('seating.kind', 'seating.table_id', 'table'), 13), CA('table_name', 'Table name', 'text', LKT('seating.table_name', 'seating.table_id', 'table'), 18),
    CA('top_side', 'Largest side', 'text', 'IF({col:seated}=0,%s,IF(AND({col:p1}>={col:p2},{col:p1}>={col:shared}),%s,IF({col:p2}>={col:shared},%s,%s)))' % (v('None'), S1, S2, SS), 12),
    CA('exempt', 'Family table', 'int', 'IF(OR({col:kind}=%s,{col:kind}=%s),1,0)' % (tok('tkind', 'Family'), tok('tkind', 'Head table')), 8),
    CA('one_side', 'All one side', 'int', 'IF(AND({col:seated}>0,{col:exempt}=0,{col:top_share}>={set:one_side_pct}),1,0)', 8),
    CA('flag', 'Flag', 'text', 'IF({col:seated}=0,%s,IF({col:one_side}=1,%s,%s))' % (v('Empty'), v('All one side'), v('Mixed well')), 12),
    CA('idn', 'Table number', 'int', 'IFERROR(VALUE(MID({col:table},4,2)),0)', 8),
    CA('mix_score', 'Largest side score', 'num', 'IF(AND({col:seated}>0,{col:exempt}=0),{col:top_share}*100+(20-{col:idn})/100,0)', 10)],
    D.tid_d('table'), 50, [A('flag', '= ' + v('All one side'), 'warn'), A('flag', '= ' + v('Mixed well'), 'good')]))

# 13 place cards ----------------------------------------------------------------------------------------------------------------------
def PC(c_): return IDX('guests', c_, 'card_seq', '{col:no}')
tables.append(T('cards', 'Place Cards', 'Place Cards', 'One row per seated guest in guest order: table, table name and a meal marker for the place card. Print the list and cut the cards, or send the list to the printer.', [
    C('no', 'Number', 'int', 8, required=True), CA('guest_id', 'Guest ID', 'text', PC('guest_id'), 9), CA('guest', 'Guest', 'text', LKT('guests.guest', 'guests.guest_id', 'guest_id'), 22),
    CA('table', 'Table', 'text', LKT('guests.table', 'guests.guest_id', 'guest_id'), 9), CA('table_name', 'Table name', 'text', IDX('seating', 'table_name', 'table_id', '{col:table}'), 18),
    CA('meal', 'Meal', 'text', LKT('guests.meal', 'guests.guest_id', 'guest_id'), 15), CA('marker', 'Meal marker', 'text', 'IF({col:meal}="",%s,LEFT({col:meal},1))' % v('No marker'), 9),
    CA('dietary', 'Dietary note', 'text', LKT('guests.dietary', 'guests.guest_id', 'guest_id'), 14), CA('household', 'Household', 'text', LKT('guests.household', 'guests.guest_id', 'guest_id'), 24),
    CA('card_text', 'Card text', 'text', '{col:guest}&", "&{col:table_name}', 28)],
    D.ranks(D.N_CARDS), 200))

# 14 late reply seat finder ---------------------------------------------------------------------------------------------------------------
def SC_(side_col): return 'IF({col:free}>={set:late_size},1000+{col:%s}*10+{col:free}+(20-{col:idn})/100,0)' % side_col
def RK(c_): return 'COUNTIFS({range:latefit.%s},">"&{col:%s})+1' % (c_, c_)
tables.append(T('latefit', 'Late Reply Seat Finder', 'Late Reply Seat Finder', 'One row per table: free seats, the side that fills it and the best table to give a late yes for guests of each side. The table with the most free seats and the best side fit ranks first.', [
    LST('table', 'Table', 'table', 9, required=True), CA('free', 'Free seats', 'int', LKN('seating.free', 'seating.table_id', 'table'), 9),
    CA('p1c', 'Partner 1', 'int', FL('p1'), 8), CA('p2c', 'Partner 2', 'int', FL('p2'), 8), CA('shc', 'Shared', 'int', FL('shared'), 8), CA('idn', 'Table number', 'int', 'IFERROR(VALUE(MID({col:table},4,2)),0)', 8),
    CA('fit_side', 'Best side fit', 'text', 'IF(AND({col:p1c}>={col:p2c},{col:p1c}>={col:shc}),%s,IF({col:p2c}>={col:shc},%s,%s))' % (S1, S2, SS), 12),
    CA('score_p1', 'Score partner 1', 'num', SC_('p1c'), 9), CA('score_p2', 'Score partner 2', 'num', SC_('p2c'), 9), CA('score_sh', 'Score shared', 'num', SC_('shc'), 9),
    CA('score_free', 'Score free seats', 'num', '{col:free}*100+(20-{col:idn})', 10),
    CA('rank_p1', 'Rank for partner 1 guests', 'int', RK('score_p1'), 9), CA('rank_p2', 'Rank for partner 2 guests', 'int', RK('score_p2'), 9), CA('rank_sh', 'Rank for shared guests', 'int', RK('score_sh'), 9),
    CA('rank', 'Rank by free seats', 'int', RK('score_free'), 9), CA('table_name', 'Table name', 'text', LKT('seating.table_name', 'seating.table_id', 'table'), 18)],
    D.tid_d('table'), 50, [A('rank', '= 1', 'good'), A('free', '= 0', 'warn')]))

# 15 rentals ---------------------------------------------------------------------------------------------------------------------------------------
BASE = 'IF({col:basis}=%s,%s,IF({col:basis}=%s,%s,IF({col:basis}=%s,%s,1)))' % (tok('rbasis', 'Per seat'), SEATS_EXP, tok('rbasis', 'Per table'), TBL_N, tok('rbasis', 'Per guest'), SEATS_EXP)
tables.append(T('rentals', 'Rental Quantities', 'Rental Quantities', 'One row per rental item: how it counts (per seat, table or guest), the spare share, the quantity to order from the final tables, what you have ordered, the gap and the cost.', [
    LST('item', 'Item', 'ritem', 20, required=True), LST('basis', 'Basis', 'rbasis', 11), C('per_unit', 'Pieces each', 'int', 9), C('spare_pct', 'Spare share', 'pct', 9), C('unit_cost', 'Unit cost', 'num', 10),
    C('ordered', 'Ordered', 'int', 9), C('order_by', 'Order by', 'date', 12),
    CA('base', 'Base count', 'int', BASE, 9), CA('quantity', 'Quantity to order', 'int', 'ROUNDUP({col:base}*{col:per_unit}*(1+{col:spare_pct}),0)', 10),
    CA('gap', 'Still to order', 'int', 'MAX(0,{col:quantity}-{col:ordered})', 9), CA('ordered_ok', 'Ordered, counted', 'int', 'MIN({col:ordered},{col:quantity})', 9),
    CA('cost', 'Cost', 'money', 'ROUND({col:quantity}*{col:unit_cost},0)', 11), CA('days_left', 'Days to order', 'int', 'IF({col:order_by}="","",{col:order_by}-{today})', 9),
    CA('status', 'Status', 'text', 'IF({col:gap}=0,%s,IF({col:ordered}=0,%s,%s))' % (v('Covered'), v('Not ordered'), v('Short')), 12), CA('one', 'Item', 'int', '1', 6),
    CA('chairs', 'Chairs to order', 'int', QTY('Chairs'), 9), CA('linens', 'Linens to order', 'int', QTY('Table linens'), 9), CA('plates', 'Plates to order', 'int', QTY('Dinner plates'), 9),
    CA('glasses', 'Glasses to order', 'int', QTY('Water glasses'), 9), CA('extra_chairs', 'Extra chairs for late replies', 'int', 'SUM(%s)' % R('spare', 'hold'), 9),
    CA('headcount_date', 'Headcount date', 'date', '{set:headcount_date}', 12), CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 12), LIT('rentals_phone', 'Rentals phone', D.RENTALS_PHONE), CPL()],
    D.rentals_d(), 50, [A('status', '= ' + v('Not ordered'), 'bad'), A('status', '= ' + v('Short'), 'warn'), A('status', '= ' + v('Covered'), 'good')]))

# 16 head table plan ------------------------------------------------------------------------------------------------------------------------------------
HK = '%s&"|"&({col:seat}-{set:couple_seats})' % HEADT
tables.append(T('headtable', 'Head Table Plan', 'Head Table Plan', 'Ten seats at the head table: the couple first, then the guests seated at the first table. Move people at Seating Tables if the head table is over.', [
    C('seat', 'Seat', 'int', 8, required=True),
    CA('person', 'Person', 'text', 'IF({col:seat}<={set:couple_seats},IF({col:seat}=1,{set:partner1},{set:partner2}),IFERROR(INDEX(%s,MATCH(%s,%s,0))&"",%s))' % (G('guest'), HK, G('tkey'), v('Free seat')), 24),
    CA('role', 'Role', 'text', 'IF({col:seat}<={set:couple_seats},%s,IFERROR(INDEX(%s,MATCH(%s,%s,0))&"",%s))' % (v('Couple'), G('tier'), HK, G('tkey'), v('Free seat')), 16)], D.headtable_d(), 50))

# 17 spare seat reserve -----------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('spare', 'Spare Seat Reserve', 'Spare Seat Reserve', 'One row per table: seated guests, spare seats and the seats to hold for late replies, shared out in proportion to the free seats. A table with nothing spare stays full.', [
    LST('table', 'Table', 'table', 9, required=True), CA('seated', 'Seated', 'int', LKN('seating.seated', 'seating.table_id', 'table'), 8), CA('spare', 'Spare seats', 'int', LKN('seating.free', 'seating.table_id', 'table'), 9),
    CA('hold', 'Seats to hold', 'int', 'IF({col:spare}<=0,0,MIN({col:spare},ROUND({col:spare}/MAX(1,%s)*%s,0)))' % (FREE_TOTAL, LATE_NEED), 9),
    CA('open', 'Open after the hold', 'int', '{col:spare}-{col:hold}', 9), CA('stays_full', 'Stays full', 'int', 'IF({col:spare}<=0,1,0)', 8), CA('table_name', 'Table name', 'text', LKT('seating.table_name', 'seating.table_id', 'table'), 18)],
    D.tid_d('table'), 50, [A('stays_full', '= 1', 'warn')]))

# 18 seat swaps --------------------------------------------------------------------------------------------------------------------------------------------------------
def SW(c_): return IDX('rules', c_, 'rank', '{col:no}')
TO = 'IF({col:status}<>%s,"",IF({col:kind}=%s,{col:table_a},%s))' % (v('Conflict'), TG, IDX('latefit', 'table', 'rank', '1'))
tables.append(T('swaps', 'Seat Swaps', 'Seat Swaps', 'For each rule in fix order: the guest to move, from which table to which table, the seat free there, a swap partner when the table is full and the action to take. Conflicts first.', [
    C('no', 'Number', 'int', 8, required=True), CA('rule_id', 'Rule ID', 'text', SW('rule_id'), 9), CA('kind', 'Kind', 'text', SW('kind'), 14), CA('status', 'Rule status', 'text', SW('status'), 12),
    CA('guest', 'Guest to move', 'text', SW('name_b'), 22), CA('from_table', 'From table', 'text', SW('table_b'), 9), CA('table_a', 'Table A', 'text', SW('table_a'), 9), CA('to_table', 'To table', 'text', TO, 9),
    CA('free_there', 'Free seats there', 'int', 'IF({col:to_table}="",0,IFERROR(INDEX(%s,MATCH({col:to_table},%s,0)),0))' % (SR_('free'), SR_('table_id')), 9),
    CA('partner', 'Swap partner', 'text', 'IF({col:to_table}="","",IFERROR(INDEX(%s,MATCH({col:to_table}&"|1",%s,0))&"",""))' % (G('guest'), G('tkey')), 22),
    CA('action', 'Action', 'text', 'IF({col:status}<>%s,%s,IF({col:free_there}>0,%s,%s))' % (v('Conflict'), v('No move needed'), v('Move'), v('Swap')), 14),
    CA('fixed', 'Conflicts fixed', 'int', 'IF({col:status}=%s,1,0)' % v('Conflict'), 9), CPL()],
    D.ranks(14), 50, [A('action', '= ' + v('Move'), 'warn'), A('action', '= ' + v('Swap'), 'bad')]))

# 19 table kinds -----------------------------------------------------------------------------------------------------------------------------------------------------------
tables.append(T('kinds', 'Table Kinds', 'Table Kinds Summary', 'One row per table kind: the tables of that kind and the guests seated at them.', [
    LST('kind', 'Kind', 'tkind', 16, required=True), CA('tables', 'Tables', 'int', 'COUNTIFS(%s,{col:kind},%s,"<>")' % (SR_('kind'), SR_('table_id')), 9), CA('seats', 'Guests seated', 'int', 'SUMIFS(%s,%s,{col:kind})' % (SR_('seated'), SR_('kind')), 11),
    ], [dict(kind=key('tkind', k)) for k in TABLE_KINDS], 50))

# 20 sign-off checks ---------------------------------------------------------------------------------------------------------------------------------------------------------
IDXS = 'MATCH({col:check},{range:signoff.check},0)'
tables.append(T('signoff', 'Seating Signoff Checks', 'Seating Sign-off Checks', 'Eight checks before you print the seating plan: each shows how many items need work. Zero on every line means ready to print.', [
    C('check', 'Check', 'text', 38, required=True),
    CA('count', 'Items to fix', 'int', 'CHOOSE(%s,%s,SUM(%s),COUNTIFS(%s,"<0"),COUNTIFS(%s,">1"),COUNTIFS(%s,%s,%s,"",%s,"<>"),COUNTIFS(%s,">0"),MAX(0,{set:couple_seats}+COUNTIFS(%s,%s)-{set:head_seats}),%s)' % (
        IDXS, NEED, R('rules', 'conflict'), SR_('free'), HR('tables_used'), G('rsvp'), RY, G('meal'), G('table'), R('rentals', 'gap'), G('table'), HEADT, PENDG), 10),
    CA('status', 'Status', 'text', 'IF({col:count}=0,%s,%s)' % (v('OK'), v('To fix')), 10)], D.signoff_d(), 50, [A('status', '= ' + v('To fix'), 'warn'), A('status', '= ' + v('OK'), 'good')]))
assert len(tables) == 20, len(tables)
