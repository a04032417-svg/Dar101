"""Wedding Planning suite - part 5: Venue Capacity and Seating Plan."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp5_lists import *
from wp5_tables import *
from wp5_tools import tools
import wp5_data as D

SUITE = 'fx-20261116-wedding'
NOTE = "Sample wording: adapt it to your own wedding."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c_): return 'INDEX(%s,MATCH({pick},%s,0))' % (R(t, c_), R(t, idc))

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('table_sheet', 'Table Sheet', 'One table: seats, guests and free seats', 'seating.table_id', F(
        ('Table name', 'seating.table_name'), ('Kind', 'seating.kind'), ('Seats', 'seating.capacity'), ('Seats for the couple', 'seating.reserved'), ('Seated', 'seating.seated'), ('Free seats', 'seating.free'), ('Side mix, P1 / P2 / shared', 'seating.side_mix')) + [
        FF('Fill share', LK('fill', 'table', 'fill_share'), 'pct'), FF('Seat rule conflicts at this table', 'COUNTIFS(%s,{pick},%s,1)+COUNTIFS(%s,{pick},%s,1)' % (R('rules', 'table_a'), R('rules', 'conflict'), R('rules', 'table_b'), R('rules', 'conflict')), 'int'),
        FF('Seats to hold for late replies', LK('spare', 'table', 'hold'), 'int')],
        {"from": "guests", "match": "guests.table", "columns": ["guest", "age_group", "meal", "dietary"], "max": 10}),
    FORM('assign_sheet', 'Seat Assignment Sheet', 'One guest: RSVP, table and the seats free there', 'guests.guest_id', F(
        ('Guest', 'guests.guest'), ('Household', 'guests.household'), ('Side', 'guests.side'), ('Tier', 'guests.tier'), ('List', 'guests.list_ab'), ('Age group', 'guests.age_group'), ('RSVP', 'guests.rsvp'),
        ('Meal', 'guests.meal'), ('Dietary note', 'guests.dietary'), ('Table', 'guests.table')) + [
        FF('Table name', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (SR_('table_name'), LK('guests', 'guest_id', 'table'), SR_('table_id')), 'text'),
        FF('Free seats at that table', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (SR_('free'), LK('guests', 'guest_id', 'table'), SR_('table_id')), 'int'),
        FF('Table of the household', LK('guests', 'guest_id', 'hh_table'), 'text')]),
    FORM('rule_sheet', 'Seat Rule Sheet', 'One keep-together or keep-apart rule', 'rules.rule_id', F(
        ('Kind', 'rules.kind'), ('Guest A', 'rules.name_a'), ('Guest B', 'rules.name_b'), ('Table A', 'rules.table_a'), ('Table B', 'rules.table_b'), ('Reason', 'rules.reason'), ('Agreed on', 'rules.agreed_on'), ('Status', 'rules.status')) + [
        FF('Days since the rule was agreed', '{today}-' + LK('rules', 'rule_id', 'agreed_on'), 'int'), FF('Fix order', LK('rules', 'rule_id', 'rank'), 'int'), FF('Conflicts in all', 'SUM(%s)' % R('rules', 'conflict'), 'int')]),
    FORM('size_sheet', 'Table Size Sheet', 'One table size: tables and empty seats', 'tsizes.size', F(('Tables needed', 'tsizes.tables'), ('Empty seats', 'tsizes.empty')) + [
        FF('Seats at those tables', LK('tsizes', 'size', 'tables') + '*VALUE({pick})', 'int'), FF('Expected headcount seated', SEATS_EXP, 'int'), FF('Seated capacity of the venue', CAP, 'int'),
        FF('Share of the seated capacity used', 'IFERROR(%s/%s,0)' % (SEATS_EXP, CAP), 'pct')]),
    FORM('space_sheet', 'Space Sheet', 'One space number from your floor plan', 'space.item', F(('Value', 'space.value'), ('Note', 'space.note')) + [
        FF('Area left for tables', USABLE, 'num'), FF('Area per guest at the expected headcount', 'IFERROR(%s/%s,0)' % (USABLE, SEATS_EXP), 'num'), FF('Your least area per guest', SP('Area per guest, minimum'), 'num'),
        FF('Wedding day', '{set:wedding_day}', 'date')]),
    FORM('head_sheet', 'Head Table Sheet', 'One seat at the head table', 'headtable.seat', F(('Person', 'headtable.person'), ('Role', 'headtable.role')) + [
        FF('Seats at the head table', '{set:head_seats}', 'int'), FF('Guests seated at the head table', 'COUNTIFS(%s,%s)' % (G('table'), HEADT), 'int'),
        FF('Free seats at the head table', '{set:head_seats}-{set:couple_seats}-COUNTIFS(%s,%s)' % (G('table'), HEADT), 'int'), FF('Wedding day', '{set:wedding_day}', 'date')]),
    FORM('late_sheet', 'Late Reply Seat Sheet', 'One table as a home for a late yes', 'latefit.table', F(
        ('Free seats', 'latefit.free'), ('Partner 1 guests', 'latefit.p1c'), ('Partner 2 guests', 'latefit.p2c'), ('Shared friends', 'latefit.shc'), ('Best side fit', 'latefit.fit_side'), ('Rank by free seats', 'latefit.rank')) + [
        FF('Free seats in all', FREE_TOTAL, 'int'), FF('Yes guests without a seat', NEED, 'int'), FF('Pending guests', PENDG, 'int')]),
    FORM('swap_sheet', 'Seat Swap Sheet', 'One move that clears a conflict', 'swaps.no', F(
        ('Rule', 'swaps.rule_id'), ('Kind', 'swaps.kind'), ('Rule status', 'swaps.status'), ('Guest to move', 'swaps.guest'), ('From table', 'swaps.from_table'), ('To table', 'swaps.to_table'), ('Free seats there', 'swaps.free_there'),
        ('Swap partner', 'swaps.partner'), ('Action', 'swaps.action')) + [FF('Conflicts to clear in all', 'SUM(%s)' % R('swaps', 'fixed'), 'int'), FF('Wedding day', '{set:wedding_day}', 'date')]),
    FORM('rental_sheet', 'Rental Quantity Sheet', 'One rental item and its order', 'rentals.item', F(
        ('Basis', 'rentals.basis'), ('Pieces each', 'rentals.per_unit'), ('Spare share', 'rentals.spare_pct'), ('Unit cost', 'rentals.unit_cost'), ('Ordered', 'rentals.ordered'), ('Order by', 'rentals.order_by'),
        ('Base count', 'rentals.base'), ('Quantity to order', 'rentals.quantity'), ('Still to order', 'rentals.gap'), ('Cost', 'rentals.cost'), ('Status', 'rentals.status')) + [
        FF('Days to order', 'IF(%s="","",%s-{today})' % (LK('rentals', 'item', 'order_by'), LK('rentals', 'item', 'order_by')), 'int'), FF('Cost of the whole rental list', 'SUM(%s)' % R('rentals', 'cost'), 'money')]),
    FORM('card_sheet', 'Place Card Sheet', 'One place card', 'cards.no', F(('Guest', 'cards.guest'), ('Table', 'cards.table'), ('Table name', 'cards.table_name'), ('Meal', 'cards.meal'), ('Meal marker', 'cards.marker'), ('Household', 'cards.household')) + [
        FF('Card text', LK('cards', 'no', 'card_text'), 'text'), FF('Cards to print', 'SUM(%s)' % G('seated'), 'int'), FF('Print date', '{set:wedding_day}-{set:print_days}', 'date')]),
    FORM('spare_sheet', 'Spare Seat Sheet', 'One table and its held seats', 'spare.table', F(('Seated', 'spare.seated'), ('Spare seats', 'spare.spare'), ('Seats to hold', 'spare.hold'), ('Open after the hold', 'spare.open'), ('Stays full', 'spare.stays_full')) + [
        FF('Seats held in all', 'SUM(%s)' % R('spare', 'hold'), 'int'), FF('Late seats you expect to need', LATE_NEED, 'int'), FF('Table name', LK('spare', 'table', 'table_name'), 'text')]),
    FORM('signoff_sheet', 'Seating Sign-off Sheet', 'One check before you print', 'signoff.check', F(('Items to fix', 'signoff.count'), ('Status', 'signoff.status')) + [
        FF('Checks still open', 'COUNTIFS(%s,">0")' % R('signoff', 'count'), 'int'), FF('Print date', '{set:wedding_day}-{set:print_days}', 'date'), FF('Days to the print date', '{set:wedding_day}-{set:print_days}-{today}', 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('chart_page', 'Seating Chart Page', 'Seating chart for the plan', 'seating.table_id', [
        '{col:seating.couple}, dated {today}. Seating chart for {col:seating.wedding_day}: {col:seating.tables_total} tables of {col:seating.table_size} for an expected {col:seating.headcount} seats against a seated capacity of {col:seating.venue_capacity}.',
        '{col:seating.table_name}, {col:seating.kind}: {col:seating.seated} guests seated, {col:seating.free} seats free. Side mix, partner 1 / partner 2 / shared: {col:seating.side_mix}.',
        'Yes guests without a seat: {col:seating.unseated}. Seat rule conflicts: {col:seating.conflicts}. Sign-off: {col:seating.sign_status}.'], ['The couple', 'Venue contact'], NOTE),
    DOC('table_page', 'One Table Page', 'The guests at one table, for the venue', 'fill.table', [
        'Table {col:fill.table}, {col:fill.table_name}, {col:fill.kind}, dated {today}.',
        '{col:fill.guests_text} seats taken, {col:fill.free} free. Partner 1 guests {col:fill.p1}, partner 2 guests {col:fill.p2}, shared friends {col:fill.shared}. Fill share {col:fill.fill_share}.',
        'Give this page with the table sign and the place cards of this table.'], ['The couple', 'Venue contact'], NOTE),
    DOC('card_list', 'Place Card List Page', 'One place card line', 'cards.no', [
        '{set:couple}, dated {today}. Place card number {col:cards.no}.',
        'Guest {col:cards.guest}, {col:cards.table_name} ({col:cards.table}). Meal marker {col:cards.marker}. Dietary note: {col:cards.dietary}. Household: {col:cards.household}.',
        'Card text: {col:cards.card_text}. Print and cut, or send the list to the stationery printer.'], ['The couple', 'Helper'], NOTE),
    DOC('venue_list', 'Venue Table List', 'Table list for the venue and the caterer', 'seating.table_id', [
        'To the venue and the caterer. {col:seating.couple}, wedding day {col:seating.wedding_day}, dated {today}.',
        'We need {col:seating.tables_total} round tables of {col:seating.table_size} and a head table of {col:seating.head_seats}. {col:seating.table_name} has {col:seating.seated} guests and {col:seating.free} free seats.',
        'Vendor meals: {col:seating.vendor_meals}. The final headcount comes on {col:seating.headcount_date}, as in your contract. Please confirm the seated capacity of {col:seating.venue_capacity}.'], ['The couple', 'Venue contact', 'Caterer'], NOTE),
    DOC('head_page', 'Head Table Page', 'One seat at the head table', 'headtable.seat', [
        '{set:couple}, dated {today}. Head table of {set:head_seats} seats.',
        'Seat {col:headtable.seat}: {col:headtable.person}, {col:headtable.role}.',
        'Give this page to the day-of coordinator with the place cards.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('floor_page', 'Floor Space Page', 'Capacity and floor space for one headcount', 'scenarios.scenario', [
        '{set:couple}, dated {today}. Scenario {col:scenarios.scenario}.',
        'Headcount {col:scenarios.headcount}, seats needed {col:scenarios.seats} against a seated capacity of {col:scenarios.capacity}. Tables needed {col:scenarios.tables}, empty seats {col:scenarios.empty}. Verdict: {col:scenarios.verdict}.',
        'Floor area per guest {col:scenarios.floor_per_guest} square metres. Check the floor plan with the venue.'], ['The couple', 'Venue contact'], NOTE),
    DOC('yes_page', 'Yes Scenario Page', 'If everyone says yes', 'scenarios.scenario', [
        '{set:couple}, dated {today}. What if the replies change: {col:scenarios.scenario}.',
        'Seats needed {col:scenarios.seats}, seated capacity {col:scenarios.capacity}, seats over {col:scenarios.over}, tables {col:scenarios.tables}. Verdict: {col:scenarios.verdict}.',
        'A scenario is your own estimate, not a promise. Decide what to cut or how to enlarge the room before the reply-by date.'], ['The couple'], NOTE),
    DOC('rules_page', 'Seat Rules Page', 'One seat rule', 'rules.rule_id', [
        '{set:couple}, dated {today}. Seat rule {col:rules.rule_id}, agreed on {col:rules.agreed_on}.',
        '{col:rules.kind}: {col:rules.name_a} ({col:rules.table_a}) and {col:rules.name_b} ({col:rules.table_b}). Reason: {col:rules.reason}. Status: {col:rules.status}.',
        'Keep this page private: it is for the couple and the day-of coordinator only.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('unseated_page', 'Unseated Guests Page', 'One guest still to seat', 'unseated.no', [
        '{col:unseated.couple}, dated {today}. Guest number {col:unseated.no} on the seating to-do list.',
        '{col:unseated.guest}, {col:unseated.household}, {col:unseated.side}. RSVP {col:unseated.rsvp}. Household table: {col:unseated.hh_table}. Suggested table: {col:unseated.suggested}, {col:unseated.suggested_free} seats free there. Status: {col:unseated.status}.',
        'Seat yes guests first and hold seats for the pending replies.'], ['The couple'], NOTE),
    DOC('rental_page', 'Rental Order Page', 'Rental order for the rentals vendor', 'rentals.item', [
        'To the rentals vendor. {set:couple}, wedding day {set:wedding_day}, dated {today}.',
        'Item: {col:rentals.item}. Quantity {col:rentals.quantity} with a spare share of {col:rentals.spare_pct}. Already ordered {col:rentals.ordered}, still to order {col:rentals.gap}. Order by {col:rentals.order_by}.',
        'Please confirm the delivery window, the price and the final count date.'], ['The couple', 'Rentals vendor'], NOTE),
    DOC('change_log', 'Seating Change Log', 'One seating change', 'swaps.no', [
        '{col:swaps.couple}, dated {today}. Seating change {col:swaps.no}, rule {col:swaps.rule_id}.',
        'Guest to move: {col:swaps.guest}, from {col:swaps.from_table} to {col:swaps.to_table}. Free seats there: {col:swaps.free_there}. Swap partner: {col:swaps.partner}. Action: {col:swaps.action}.',
        'Write the date of the change here and update Guests.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('sign_page', 'Table Sign Page', 'The sign for one table', 'seating.table_id', [
        '{col:seating.table_name}',
        '{col:seating.kind}. {col:seating.seated} guests. Wedding of {col:seating.couple}, {col:seating.wedding_day}.',
        'Print one sign for each table and place it where guests can see it from the door.'], ['The couple'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
CK = CHK
checklists = [
    CK('capacity_check', 'Capacity check', 'rentals', 'rentals.order_by', [('Read the seated capacity in the venue contract', -190), ('Count the invited guests against it', -185), ('Run the everyone-says-yes scenario', -180), ('Decide what to cut if it is over', -170), ('Check the floor plan and the dance floor with the venue', -150), ('Write the agreed capacity in Space Inputs', -145)]),
    CK('table_size', 'Choose the table size', 'rentals', 'rentals.order_by', [('Compare tables of 6, 8, 10 and 12', -150), ('Ask the venue how many tables the room holds', -148), ('Check the floor area for each size', -145), ('Pick the size with the fewest empty seats that fits', -140), ('Tell the caterer and the rentals vendor', -135)]),
    CK('first_draft', 'First seating draft', 'rentals', 'rentals.order_by', [('Wait for most replies', -60), ('Seat the head table and the families', -55), ('Seat the wedding party and close friends', -52), ('Seat friends and colleagues', -49), ('Keep children with their household', -47), ('Check the side balance of each table', -45)]),
    CK('add_rules', 'Add seat rules', 'rules', 'rules.agreed_on', [('Ask each partner who must sit together', 0), ('Ask each partner who needs space, with the reason only', 1), ('Type each rule with a short reason', 3), ('Check the rules against the tables', 5), ('Fix every conflict', 10)]),
    CK('late_reply', 'Late reply seating', 'rentals', 'rentals.order_by', [('Open the Late Reply Seat Tool', -50), ('Find the table with room for the side', -50), ('Type the table in Guests', -49), ('Tell the household where they sit', -48), ('Update the place cards and the rentals count', -47)]),
    CK('weekly_review', 'Weekly seating review', 'rentals', 'rentals.order_by', [('Open the Seating Sign-off Checks', -120), ('Seat the yes guests who have no table', -119), ('Check the rule conflicts', -118), ('Check the split households', -117), ('Note the seats held for late replies', -116)]),
    CK('head_family', 'Head table and family', 'rentals', 'rentals.order_by', [('Ask each parent who sits at the head table', -90), ('Count the seats at the head table', -88), ('Move any extra people to the family table', -85), ('Fill in the Head Table Plan', -83), ('Tell the day-of coordinator', -80)]),
    CK('rental_order', 'Rentals order from tables', 'rentals', 'rentals.order_by', [('Check the tables and the seats in Rental Quantities', -14), ('Add your spare share', -12), ('Send the order page to the rentals vendor', -10), ('Ask for the delivery window', -7), ('Confirm the final count date', -3), ('Note what is ordered', 0)]),
    CK('place_cards', 'Place cards and table numbers', 'rentals', 'rentals.order_by', [('Check every yes guest has a table', 14), ('Check every guest has a meal marker', 16), ('Print the place cards', 21), ('Sort them by table', 22), ('Print the table numbers', 23), ('Give the box to the day-of coordinator', 28)]),
    CK('final_signoff', 'Seating sign-off steps', 'rentals', 'rentals.order_by', [('Open the Final Seating Sign-off tool', 14), ('Clear every check that is open', 17), ('Send the final chart to the venue and the caterer', 19), ('Print the table list and the place cards', 21), ('Keep one copy at home', 22)]),
    CK('dayof_setup', 'Day-of seating setup', 'rentals', 'rentals.order_by', [('Meet the venue contact at the room', 69), ('Check the tables and chairs against the order', 69), ('Place the table numbers', 70), ('Place the place cards by table', 70), ('Set the head table', 70), ('Walk the room with the day-of coordinator', 70)]),
    CK('small_wedding', 'Small wedding, one table plan', 'rentals', 'rentals.order_by', [('Count the guests and add the couple', -90), ('Choose one or two tables', -88), ('Skip the B list and the head table', -85), ('Seat by household', -80), ('Print one list for the venue', -20)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
M = MSG
messages = [
    M('m_p_fit', 'Partner: we fit the expected headcount', 'seating', 'seating.partner_phone', 'Hello, we fit {headcount} seats at {tables_total} tables, {spare} seats spare. {couple}'),
    M('m_p_over', 'Partner: everyone says yes, we are over', 'seating', 'seating.partner_phone', 'Hello, if everyone says yes we are {over} seats over capacity. {couple}'),
    M('m_p_unseated', 'Partner: yes guests have no seat yet', 'seating', 'seating.partner_phone', 'Hello, {unseated} yes guests have no seat yet. {couple}'),
    M('m_p_conf', 'Partner: seat rule conflicts to decide', 'seating', 'seating.partner_phone', 'Hello, {conflicts} seat rule conflicts need a decision. {couple}'),
    M('m_p_b', 'Partner: the B list and the open seats', 'seating', 'seating.partner_phone', 'Hello, the B list needs {b_need} seats and {b_open} are open. {couple}'),
    M('m_p_ready', 'Partner: seating ready to print', 'seating', 'seating.partner_phone', 'Hello, seating is ready to print on {print_date}. {couple}'),
    M('m_p_review', 'Partner: please review a table', 'seating', 'seating.partner_phone', 'Hello, please review {table_name} before we print, it has {free} free seats. {couple}'),
    M('m_h_seated', 'Household: you are seated at', 'households', 'households.phone', 'Hello {contact}, we have {household} at {table_name} for the reception. {couple}'),
    M('m_h_apart', 'Household: your table, sorry', 'households', 'households.phone', 'Hello {contact}, your table is {table_name}. We are sorry we could not seat you with every guest you asked for. {couple}'),
    M('m_h_kids', 'Household: who the children sit with', 'households', 'households.phone', 'Hello {contact}, please tell us who the children of {household} sit with. {couple}'),
    M('m_h_head', 'Household: you are at the head table', 'households', 'households.phone', 'Hello {contact}, we have you at {table_name}. Please come to the front of the room on {wedding_day}. {couple}'),
    M('m_h_thanks', 'Household: thank you for replying', 'households', 'households.phone', 'Hello {contact}, thank you for replying. We are finding the seats for {household}. {couple}'),
    M('m_v_tables', 'Venue: tables and head table', 'seating', 'seating.venue_phone', 'Hello, we need {tables_total} round tables of {table_size} and a head table. {couple}'),
    M('m_v_floor', 'Venue: confirm the floor plan', 'seating', 'seating.venue_phone', 'Hello, please confirm the floor plan with a dance floor of {dance_area} square metres. {couple}'),
    M('m_v_chart', 'Venue: the final seating chart', 'seating', 'seating.venue_phone', 'Hello, the final seating chart for {wedding_day} is attached. {couple}'),
    M('m_v_cap', 'Venue: confirm the seated capacity', 'seating', 'seating.venue_phone', 'Hello, please confirm the seated capacity of {venue_capacity}. {couple}'),
    M('m_c_count', 'Caterer: the table count', 'seating', 'seating.caterer_phone', 'Hello, the table count is {tables_total} with a head table of {head_seats}. {couple}'),
    M('m_c_meals', 'Caterer: table numbers and meals', 'seating', 'seating.caterer_phone', 'Hello, the table numbers and the meals by table are attached for {wedding_day}. {couple}'),
    M('m_c_vendor', 'Caterer: vendor meals', 'seating', 'seating.caterer_phone', 'Hello, vendor meals are {vendor_meals}. {couple}'),
    M('m_r_order', 'Rentals: the order', 'rentals', 'rentals.rentals_phone', 'Hello, we need {chairs} chairs, {linens} linens, {plates} plates and {glasses} glasses. {couple}'),
    M('m_r_window', 'Rentals: delivery window and final count', 'rentals', 'rentals.rentals_phone', 'Hello, please confirm the delivery window and the final count date of {headcount_date}. {couple}'),
    M('m_r_extra', 'Rentals: more chairs for late replies', 'rentals', 'rentals.rentals_phone', 'Hello, we need {extra_chairs} more chairs for late replies. {couple}'),
    M('m_d_ready', 'Day-of coordinator: chart and cards', 'seating', 'seating.dayof_phone', 'Hello, the seating chart and the place cards are ready. {couple}'),
    M('m_d_held', 'Day-of coordinator: seats held', 'seating', 'seating.dayof_phone', 'Hello, we hold {hold_n} seats for late replies across the tables. {couple}'),
    M('m_d_head', 'Day-of coordinator: set the head table', 'seating', 'seating.dayof_phone', 'Hello, please set the head table for {head_seats}. {couple}'),
    M('m_l_head', 'Wedding party lead: the head table', 'seating', 'seating.lead_phone', 'Hello, the wedding party sits at the head table of {head_seats} seats. {couple}'),
    M('m_f_cards', 'Helper: sort the place cards', 'seating', 'seating.helper_phone', 'Hello, can you print and sort the place cards by table? Print date {print_date}. {couple}'),
    M('m_pa1', 'Parent of partner 1: your guests sit', 'seating', 'seating.parent1_phone', 'Hello, your guests sit at {table_name} and the nearby tables. {couple}'),
    M('m_pa2', 'Parent of partner 2: your guests sit', 'seating', 'seating.parent2_phone', 'Hello, your guests sit at {table_name} and the nearby tables. {couple}'),
    M('m_o_front', 'Officiant: the front row', 'seating', 'seating.officiant_phone', 'Hello, we hold {front_row} front row seats for family on {wedding_day}. {couple}'),
    M('m_hotel', 'Hotel contact: the shuttle', 'seating', 'seating.hotel_phone', 'Hello, the shuttle runs for about {headcount} guests from the reception on {wedding_day}. {couple}'),
    M('m_p_changes', 'Partner: seating changes to make', 'seating', 'seating.partner_phone', 'Hello, after replies close the final seating changes are {changes}. {couple}'),
    M('m_v_walk', 'Venue: a seating walk-through', 'seating', 'seating.venue_phone', 'Hello, can we do a seating walk-through before {print_date}? {couple}'),
    M('m_p_sign', 'Partner: seating sign-off status', 'seating', 'seating.partner_phone', 'Hello, seating sign-off is: {sign_status}. {couple}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
kpis = [
    KPI('Seated capacity', CAP, 'int'), KPI('Guests invited', GN, 'int'), KPI('Expected headcount', 'ROUND(%s,0)' % EXP, 'int'), KPI('Everyone-says-yes headcount', GN, 'int'),
    KPI('Seats over capacity if everyone says yes', 'MAX(0,%s-%s)' % (SEATS_ALL, CAP), 'int', alert={"when": "> 0", "style": "bad"}), KPI('Seats left at the expected headcount', '%s-%s' % (CAP, SEATS_EXP), 'int'),
    KPI('Tables in use', 'COUNTIFS(%s,">0")' % SR_('seated'), 'int'), KPI('Tables with every seat taken', 'COUNTIFS(%s,0)' % SR_('free'), 'int'), KPI('Seats at one table', SZ if False else '{set:table_size}', 'int'),
    KPI('Seats at the tables in all', 'SUM(%s)' % SR_('capacity'), 'int'), KPI('Seats filled', 'SUM(%s)+SUM(%s)' % (SR_('seated'), SR_('reserved')), 'int'), KPI('Seats free', FREE_TOTAL, 'int'),
    KPI('Fill share', 'IFERROR((SUM(%s)+SUM(%s))/SUM(%s),0)' % (SR_('seated'), SR_('reserved'), SR_('capacity')), 'pct'), KPI('Yes guests seated', 'SUM(%s)' % G('seated_yes'), 'int'),
    KPI('Yes guests without a seat', NEED, 'int', alert={"when": "> 0", "style": "bad"}), KPI('Pending guests', PENDG, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Head table seats used', '{set:couple_seats}+COUNTIFS(%s,%s)' % (G('table'), HEADT), 'int'), KPI('Couple seats reserved', 'SUM(%s)' % SR_('reserved'), 'int'), KPI('Vendor seats', '{set:vendor_seats}', 'int'),
    KPI('Spare seats held for late replies', 'SUM(%s)' % R('spare', 'hold'), 'int'), KPI('Seat rule conflicts', 'SUM(%s)' % R('rules', 'conflict'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Keep-together rules kept', 'SUMIFS(%s,%s,%s)' % (R('rules', 'kept'), R('rules', 'kind'), TG), 'int'), KPI('Keep-apart rules kept', 'SUMIFS(%s,%s,%s)' % (R('rules', 'kept'), R('rules', 'kind'), tok('rkind', 'Keep apart')), 'int'),
    KPI('Households split across tables', 'COUNTIFS(%s,">1")' % HR('tables_used'), 'int', alert={"when": "> 0", "style": "warn"}), KPI('Mixed tables that are all one side', 'SUM(%s)' % R('balance', 'one_side'), 'int'),
    KPI('Largest side share at a mixed table', 'ROUND(LARGE(%s,1),0)/100' % R('balance', 'mix_score'), 'pct'), KPI('Chairs to order', QTY('Chairs'), 'int'), KPI('Place cards to print', 'SUM(%s)' % G('seated'), 'int'),
    KPI('Floor area per guest, square metres', 'IFERROR(%s/%s,0)' % (USABLE, SEATS_EXP), 'num'), KPI('Rental items not yet fully ordered', 'COUNTIFS(%s,">0")' % R('rentals', 'gap'), 'int', alert={"when": "> 0", "style": "warn"}),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Capacity and Seating Dashboard", "kpis": kpis,
    "monthly": {"title": "Seat rules agreed, in conflict and kept by month", "date": "rules.agreed_on", "series": [
        {"label": "Seat rules agreed", "sum": "rules.one", "date": "rules.agreed_on"}, {"label": "Rule conflicts", "sum": "rules.conflict", "date": "rules.agreed_on"},
        {"label": "Rules kept", "sum": "rules.kept", "date": "rules.agreed_on"}]},
    "breakdowns": [{"title": "Guests by RSVP", "by": "guests.rsvp", "agg": "count"}, {"title": "Guests seated by table kind", "by": "seating.kind", "value": "seating.seated", "agg": "sum"},
                   {"title": "Seat rules by kind", "by": "rules.kind", "agg": "count"}, {"title": "Rental cost by basis", "by": "rentals.basis", "value": "rentals.cost", "agg": "sum"}]}


def AG(kind, table, value=None, date=None, label=None, where=None): return AGG(kind, table, value, date, where, label)
def RSV(col='guests'): return [AG('count', 'guests', label='Yes', where=[('rsvp', '=', RY)]), AG('count', 'guests', label='No', where=[('rsvp', '=', RN)]), AG('count', 'guests', label='Pending', where=[('rsvp', '=', RP)])]
def MEALC(lbl): return AG('count', 'guests', label=lbl, where=[('meal', '=', tok('meal', lbl))])
SCX = tok('scen', 'Expected yes rate')
insights = {"filters": [{"label": "Side", "list": "side"}, {"label": "Tier", "list": "tier"}, {"label": "List", "list": "listab"}],
    "gauges": [
        {"title": "Expected headcount against capacity", "num": AG('sum', 'scenarios', 'scenarios.seats', where=[('scenario', '=', SCX)]), "den": AG('sum', 'scenarios', 'scenarios.capacity', where=[('scenario', '=', SCX)])},
        {"title": "Yes guests seated", "num": AG('sum', 'guests', 'guests.seated_yes'), "den": AG('count', 'guests', where=[('rsvp', '=', RY)])},
        {"title": "Seat rules kept", "num": AG('sum', 'rules', 'rules.kept'), "den": AG('sum', 'rules', 'rules.one')},
        {"title": "Seats filled against capacity", "num": AG('sum', 'seating', 'seating.seated'), "den": AG('sum', 'seating', 'seating.capacity')},
        {"title": "Rentals ordered against needed", "num": AG('sum', 'rentals', 'rentals.ordered_ok'), "den": AG('sum', 'rentals', 'rentals.quantity')},
        {"title": "Floor space against your minimum", "num": AG('sum', 'scenarios', 'scenarios.floor_ok'), "den": AG('count', 'scenarios', where=[('headcount', '>=', 0)])}],
    "charts": [
        CHART('Seated guests by table', 'bar', 'fill.table', [AG('sum', 'fill', 'fill.seated', label='Seated')]),
        CHART('Free seats by table', 'bar', 'fill.table', [AG('sum', 'fill', 'fill.free', label='Free seats')]),
        CHART('Guests by table and side', 'stacked', 'fill.table', [AG('sum', 'fill', 'fill.p1', label='Partner 1'), AG('sum', 'fill', 'fill.p2', label='Partner 2'), AG('sum', 'fill', 'fill.shared', label='Shared')]),
        CHART('Guests by table and tier', 'stacked', 'balance.table', [AG('sum', 'balance', 'balance.family', label='Family'), AG('sum', 'balance', 'balance.close', label='Close friends'), AG('sum', 'balance', 'balance.friends', label='Friends'),
                                                                     AG('sum', 'balance', 'balance.colleagues', label='Colleagues')]),
        CHART('Tables by kind', 'bar', 'kinds.kind', [AG('sum', 'kinds', 'kinds.tables', label='Tables')]),
        CHART('Guests by RSVP', 'bar', 'guests.rsvp', [AG('count', 'guests', label='Guests')]),
        CHART('Guests by list', 'stacked', 'guests.list_ab', RSV()), CHART('Guests by side', 'stacked', 'guests.side', RSV()),
        CHART('Guests by tier', 'bar', 'guests.tier', [AG('count', 'guests', label='Guests')]), CHART('Guests by age group', 'bar', 'guests.age_group', [AG('count', 'guests', label='Guests')]),
        CHART('Meals by table', 'stacked', 'guests.table', [MEALC('Meat'), MEALC('Fish'), MEALC('Vegetarian'), MEALC('Vegan')]),
        CHART('Seat rules by kind', 'bar', 'rules.kind', [AG('sum', 'rules', 'rules.kept', label='Kept'), AG('sum', 'rules', 'rules.conflict', label='Conflicts')]),
        CHART('Seat rules by reason', 'bar', 'rules.reason', [AG('sum', 'rules', 'rules.kept', label='Kept'), AG('sum', 'rules', 'rules.conflict', label='Conflicts')]),
        CHART('Capacity scenarios by headcount', 'bar', 'scenarios.scenario', [AG('sum', 'scenarios', 'scenarios.headcount', label='Headcount')]),
        CHART('Tables needed by table size', 'bar', 'tsizes.size', [AG('sum', 'tsizes', 'tsizes.tables', label='Tables')]),
        CHART('Empty seats by table size', 'bar', 'tsizes.size', [AG('sum', 'tsizes', 'tsizes.empty', label='Empty seats')]),
        CHART('Headcount ladder against capacity', 'line', 'scenarios.scenario', [AG('sum', 'scenarios', 'scenarios.seats', label='Seats needed'), AG('sum', 'scenarios', 'scenarios.capacity', label='Seated capacity')]),
        CHART('Rental quantities by item', 'bar', 'rentals.item', [AG('sum', 'rentals', 'rentals.quantity', label='To order'), AG('sum', 'rentals', 'rentals.ordered', label='Ordered')]),
        CHART('Free seats by table kind', 'bar', 'seating.kind', [AG('sum', 'seating', 'seating.free', label='Free seats')]),
        CHART('Households by list', 'bar', 'households.list_ab', [AG('count', 'households', label='Households')]),
        CHART('Seats held for late replies by table', 'bar', 'spare.table', [AG('sum', 'spare', 'spare.hold', label='Seats held')]),
        CHART('Guests by meal', 'bar', 'guests.meal', [AG('count', 'guests', label='Guests')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Table count solver", "why": "headcount plus couple, vendor and spare seats over the table size, against the seated capacity and the tables the room holds", "where": "Table Count Solver"},
    {"name": "Table size comparison", "why": "tables of 6, 8, 10 and 12 compared on tables, empty seats and floor area, with the best size for your room named", "where": "Table Size Comparison"},
    {"name": "Everyone-says-yes scenario", "why": "all invited guests against the seated capacity: how many seats over and how many guests must decline", "where": "Everyone Says Yes Scenario"},
    {"name": "Late reply seat finder", "why": "a pending household says yes and the tool finds the table with room that fits its side best, or says to open a table", "where": "Late Reply Seat Tool"},
    {"name": "Keep together and keep apart checker", "why": "every seat rule tested against the table assignments with the conflicts listed in fix order", "where": "Keep Together Apart Checker"},
    {"name": "Seat swap suggester", "why": "for each conflict the guest to move, the table to move to and a guest to swap with when that table is full", "where": "Seat Swap Suggester"},
    {"name": "Rental quantity calculator", "why": "chairs, linens, plates and glasses from the final tables with your spare share, and the chairs still to order", "where": "Rental Quantity Calculator"},
    {"name": "Spare seat reserve", "why": "the seats to hold at each table for late replies and the tables that stay full", "where": "Spare Seat Reserve Tool"},
    {"name": "Floor space check", "why": "the floor area less dance floor, buffet, stage and walkways shared among your guests against your own minimum", "where": "Floor Space Check"},
    {"name": "Final seating sign-off", "why": "eight checks on one page and a print date: ready to print or how many items are left to fix", "where": "Final Seating Sign-off"}]
competitors = [
    {"what": "a free planning app", "lacks": "has a drag-and-drop seating chart but no capacity check against the room, no everyone-says-yes scenario, no rental quantities and no sign-off"},
    {"what": "a single budget spreadsheet", "lacks": "has a guest count cell but no tables, no seat rules, no table balance and no place cards"},
    {"what": "a printable wedding binder", "lacks": "has blank seating pages but does no sums, finds no conflicts and cannot suggest a swap"},
    {"what": "a wedding website with a registry", "lacks": "keeps your guest list on a company's pages, has no private capacity scenarios and no rental order for the tables you chose"}]
guide = [
    'Open Start here and type your names, the wedding day, the seated capacity from the venue contract and the seats at one table in the yellow cells. Replace demo data: clear the sample rows and type your own.',
    'Fill Households and Guests first: one row per invitation and one per guest with side, tier, list, RSVP, meal and a short dietary note. Names only, no addresses and no health details.',
    'Type the seats of each table in Seating Tables. The seated guests, the free seats and the side mix fill in as you type a table for each guest in Guests.',
    'Check the room first: Capacity Scenarios, the Table Count Solver, the Table Size Comparison and the Floor Space Check say whether the guests fit before you seat anyone.',
    'Add Seat Rules (keep together or keep apart, with a short reason). Rule Conflicts and Seat Swaps list what to fix and the Keep Together Apart Checker counts it.',
    'Seat the yes guests with no table from Unseated Guests, then use the Late Reply Seat Tool for each late yes. Spare Seat Reserve shows the seats to hold for pending replies.',
    'Look at Table Fill and Table Balance by Side and Tier for tables that are full or all one side, and at the Household Split Check so children sit with their household.',
    'Type the rental items in Rental Quantities; the quantity comes from the final tables with your spare share. Send the Rental Order Page to the rentals vendor.',
    'Print the Place Cards, the Head Table Plan and the table signs, then run the Final Seating Sign-off. Ready to print means every check is clear.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A couple with a small wedding (30 guests, no wedding party) uses the same sheets with fewer rows: keep one or two tables, skip the head table or the whole seating plan.',
    'This workbook has no macros and works in Excel and Google Sheets. Print any page for a parent or the day-of coordinator.',
    'Why a workbook: one flat price, no vendor ever sees your details, no fees on your gifts, your own numbers, and it works offline.',
    'What this is not: not a booking service, not a payment service, and not legal, tax or insurance advice. Every default is a typical starting value you can edit, never a promise.']
listing = {"title": "Wedding Seating Chart and Venue Capacity Excel Template: Table Count, Seat Rules, Place Cards, Rentals, Head Table",
    "headline": "Seating chart, table count and venue capacity for your wedding",
    "tags": ["seating chart", "seating plan", "wedding planner", "table count", "place cards", "venue capacity", "excel template", "wedding spreadsheet", "head table", "rsvp seating", "wedding checklist", "rental quantities", "wedding budget"],
    "description": ("Plan where every guest sits in one Excel workbook. Built for an engaged couple planning their own wedding, with a parent, a wedding party lead or the day-of coordinator helping with the room. "
        "Guests and Households hold one row per guest and one per invitation (one invitation, several people) with side, tier, RSVP and meal. Names only: no addresses and no health details.\n\n"
        "Start with the room. The Table Count Solver turns the headcount plus the couple, vendor and spare seats into tables and tells you if you fit; the Table Size Comparison picks between tables of 6, 8, 10 and 12; the Everyone Says Yes Scenario shows how many seats over you are if every invited guest comes; "
        "the Floor Space Check shares the floor area among your guests after the dance floor, buffet and stage.\n\n"
        "Then seat. Seat Rules hold the keep-together and keep-apart pairs with a short reason; the Keep Together Apart Checker lists every conflict and the Seat Swap Suggester names the move or the swap. The Late Reply Seat Tool finds the table with room that fits the side of a late yes, "
        "Table Fill and Table Balance show full and one-sided tables, and the Household Split Check keeps children with their household.\n\n"
        "Finish with the paper. Rental Quantities gives chairs, linens, plates and glasses from the final tables with your spare share, Place Cards and the Head Table Plan print for the day, and the Final Seating Sign-off gives a print date and says what is left.\n\n"
        f"{len(tools)} tools answer weekly questions. Print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and send {len(messages)} ready text messages to guests, the venue, the caterer, the rentals vendor and your helpers. "
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Every default is a typical starting value you can edit and forecasts are your own estimate. It is not a booking service, not a payment service and not legal, tax or insurance advice. This is part five of the Wedding Planning suite."),
    "features": ["Table count solver with a fits or too tight verdict", "Table size comparison for 6, 8, 10 and 12", "Everyone-says-yes scenario against the seated capacity", "Keep together and keep apart checker",
                 "Seat swap suggester for every conflict", "Late reply seat finder by side", "Rental quantities from the final tables", "Place cards and head table plan",
                 f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} pages", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}

lists = BASE_LISTS + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p5', slug='wedding-seating', profession='Wedding Planning', name='Venue Capacity and Seating Plan',
         tagline='Know if your guests fit, seat every table and order the rentals', price_usd=29,
         colors={"primary": "#7A4B68", "accent": "#D9A86C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Venue capacity and seating plan"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wp5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']), [len(l['values']) for l in lists[16:]])
