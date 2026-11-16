"""Wedding Planning suite - part 2: Guests, Invitations and RSVPs."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp2_lists import *
from wp2_tables import *
from wp2_tools import tools, HELD, PICK, OPENP, HID
import wp2_data as D

SUITE = 'fx-20261116-wedding'
NOTE = "Sample wording: adapt it to your own wedding."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c_): return 'INDEX(%s,MATCH({pick},%s,0))' % (R(t, c_), R(t, idc))
def LKH(c_): return 'INDEX(%s,MATCH(%s,%s,0))' % (HR(c_), LK('guests', 'guest_id', 'household_id'), HR('household_id'))

# ------------------------------------------------------------------ forms (12)
GL = {"from": "guests", "match": "guests.household_id", "columns": ["guest", "age_group", "rsvp", "meal", "dietary"], "max": 8}
forms = [
    FORM('household_sheet', 'Household Sheet', 'One household: who is invited and where it stands', 'households.household_id', F(
        ('Household', 'households.household'), ('Contact', 'households.contact'), ('Phone', 'households.phone'), ('Side', 'households.side'), ('Tier', 'households.tier'), ('List', 'households.list_ab'),
        ('Region', 'households.region'), ('Guests', 'households.size'), ('RSVP', 'households.rsvp'), ('Invite sent', 'households.invite_sent'), ('Contact status', 'households.contact_status'),
        ('Lodging', 'households.lodging'), ('Open plus-ones', 'households.open_plus_ones')) + [
        FF('Expected guests', LK('households', 'household_id', 'expected'), 'num'), FF('Days since the invitation', '{today}-' + LK('households', 'household_id', 'invite_sent'), 'int'),
        FF('Chase reason', LK('households', 'household_id', 'chase_reason'), 'text'), FF('Chase rank', LK('households', 'household_id', 'chase_rank'), 'int')], GL),
    FORM('guest_sheet', 'Guest Sheet', 'One guest: household, RSVP, meal and table', 'guests.guest_id', F(
        ('Guest', 'guests.guest'), ('Household', 'guests.household'), ('Side', 'guests.side'), ('Tier', 'guests.tier'), ('List', 'guests.list_ab'), ('Age group', 'guests.age_group'), ('Plus-one', 'guests.plus_one'),
        ('Invite sent', 'guests.invite_sent'), ('RSVP', 'guests.rsvp'), ('RSVP date', 'guests.rsvp_date'), ('Meal', 'guests.meal'), ('Dietary note', 'guests.dietary'), ('Table', 'guests.table')) + [
        FF('Household phone', LKH('phone'), 'text'), FF('Guests in the household', LKH('size'), 'int'), FF('Days since the invitation', '{today}-' + LK('guests', 'guest_id', 'invite_sent'), 'int'),
        FF('Days to the reply-by date', 'IF({set:rsvp_deadline}="","",{set:rsvp_deadline}-{today})', 'int')]),
    FORM('rsvp_sheet', 'RSVP Reply Sheet', 'One household reply, ready to write down', 'households.household_id', F(
        ('Household', 'households.household'), ('Contact', 'households.contact'), ('Phone', 'households.phone'), ('Guests', 'households.size'), ('RSVP', 'households.rsvp'), ('Invite sent', 'households.invite_sent')) + [
        FF('Days since the invitation', '{today}-' + LK('households', 'household_id', 'invite_sent'), 'int'), FF('Days to the reply-by date', 'IF({set:rsvp_deadline}="","",{set:rsvp_deadline}-{today})', 'int'),
        FF('Expected guests', LK('households', 'household_id', 'expected'), 'num'), FF('Meals chosen so far', 'COUNTIFS(%s,%s,%s,"<>")' % (GR_('household_id'), LK('households', 'household_id', 'household_id'), GR_('meal')), 'int')],
        {"from": "guests", "match": "guests.household_id", "columns": ["guest", "rsvp", "rsvp_date", "meal"], "max": 8}),
    FORM('b_list_sheet', 'B List Invitation Sheet', 'One B list household and the open seats', 'bqueue.rank', F(
        ('Household', 'bqueue.household'), ('Household ID', 'bqueue.household_id'), ('Tier', 'bqueue.tier'), ('Guests', 'bqueue.size'), ('Invite sent', 'bqueue.invite_date'), ('Status', 'bqueue.status'), ('Seats it would use', 'bqueue.seats')) + [
        FF('Open seats at the expected headcount', 'MAX(0,%s-ROUND(%s,0))' % (SEATED, LIKELY), 'int'), FF('B list guests waiting for a reply', 'SUMIFS(%s,%s,%s)' % (R('bqueue', 'size'), R('bqueue', 'status'), v('Waiting for a reply')), 'int'),
        FF('Days to the reply-by date', 'IF({set:rsvp_deadline}="","",{set:rsvp_deadline}-{today})', 'int')]),
    FORM('chase_sheet', 'Chase Log Sheet', 'One call to make and what to write down', 'chase.rank', F(
        ('Household', 'chase.household'), ('Contact', 'chase.contact'), ('Phone', 'chase.phone'), ('Chase reason', 'chase.reason'), ('Guests', 'chase.guests'), ('Guests at stake', 'chase.stake'),
        ('Silent days', 'chase.silent_days'), ('Contact status', 'chase.status'), ('Call order', 'chase.call_order')) + [
        FF('Days since the last chase', LK('chase', 'rank', 'since_chase'), 'int'), FF('Days to the reply-by date', 'IF({set:rsvp_deadline}="","",{set:rsvp_deadline}-{today})', 'int'), FF('Households silent in all', LK('chase', 'rank', 'pending_hh'), 'int')]),
    FORM('meal_sheet', 'Meal and Dietary Sheet', 'One table: meals and short notes', 'mtable.table', F(
        ('Guests', 'mtable.guests'), ('Meat', 'mtable.meat'), ('Fish', 'mtable.fish'), ('Vegetarian', 'mtable.vegetarian'), ('Vegan', 'mtable.vegan'), ('Children', 'mtable.children'), ('Dietary notes', 'mtable.notes'),
        ('Without a meal', 'mtable.no_meal')) + [FF('Share of all seated guests', 'IFERROR(%s/SUM(%s),0)' % (LK('mtable', 'table', 'guests'), R('mtable', 'guests')), 'pct'), FF('Headcount due', '{set:headcount_date}', 'date')],
        {"from": "guests", "match": "guests.table", "columns": ["guest", "meal", "dietary", "rsvp"], "max": 12}),
    FORM('plusone_sheet', 'Plus-one Sheet', 'One household and its plus-one slot', 'households.household_id', F(
        ('Household', 'households.household'), ('Contact', 'households.contact'), ('Phone', 'households.phone'), ('Guests', 'households.size'), ('Open plus-ones', 'households.open_plus_ones'), ('RSVP', 'households.rsvp')) + [
        FF('Seats if the slot is used', LK('households', 'household_id', 'size') + '+' + LK('households', 'household_id', 'open_plus_ones'), 'int'),
        FF('Food cost of the household with its slot', '(%s+%s)*{set:food_per_guest}' % (LK('households', 'household_id', 'size'), LK('households', 'household_id', 'open_plus_ones')), 'money'),
        FF('Ask for a name by', '{set:rsvp_deadline}-7', 'date')]),
    FORM('policy_sheet', 'Policy Test Sheet', 'One plus-one and children policy', 'polres.policy', F(('Headcount', 'polres.headcount'), ('Food cost at full price', 'polres.food_cost')) + [
        FF('Plus-ones counted', LK('pol', 'policy', 'plusones'), 'int'), FF('Children counted', LK('pol', 'policy', 'children'), 'int'), FF('Seated with the couple and helpers', LK('polres', 'policy', 'headcount') + '+{set:seats_others}', 'int'),
        FF('Seats left or over', '{set:venue_capacity}-%s-{set:seats_others}' % LK('polres', 'policy', 'headcount'), 'int'), FF('Cost per guest', '{set:food_per_guest}', 'money')]),
    FORM('timeline_sheet', 'Invitation Timeline Sheet', 'One invitation step and its date', 'itime.step', F(('Date', 'itime.date'), ('Done', 'itime.done'), ('Weeks before the wedding', 'itime.weeks_before'), ('Days left', 'itime.days_left'), ('Status', 'itime.status')) + [
        FF('Wedding day', '{set:wedding_day}', 'date'), FF('Days to the reply-by date from this step', '{set:rsvp_deadline}-' + LK('itime', 'step', 'date'), 'int')]),
    FORM('paper_sheet', 'Paper Order Sheet', 'One printed piece or postage line', 'paper.item', F(('Pieces each', 'paper.per_unit'), ('Per guest', 'paper.per_guest'), ('Unit cost', 'paper.unit_cost'), ('Quantity', 'paper.qty'), ('Spares', 'paper.spares'), ('Total', 'paper.total')) + [
        FF('Share of the paper and postage total', 'IFERROR(%s/SUM(%s),0)' % (LK('paper', 'item', 'total'), R('paper', 'total')), 'pct'), FF('Printer phone', LK('paper', 'item', 'printer_phone'), 'text'), FF('Paper and postage total', 'SUM(%s)' % R('paper', 'total'), 'money')]),
    FORM('roomblock_sheet', 'Room Block Sheet', 'One night of the room block', 'rooms.night', F(('Rooms held', 'rooms.rooms_held'), ('Picked up', 'rooms.picked_up')) + [
        FF('Rooms still to fill', LK('rooms', 'night', 'rooms_held') + '-' + LK('rooms', 'night', 'picked_up'), 'int'), FF('Share picked up', 'IFERROR(%s/%s,0)' % (LK('rooms', 'night', 'picked_up'), LK('rooms', 'night', 'rooms_held')), 'pct'),
        FF('Cut-off date', '{set:room_cutoff}', 'date'), FF('Days to the cut-off date', 'IF({set:room_cutoff}="","",{set:room_cutoff}-{today})', 'int'), FF('Cost of unfilled rooms at your rate', '(%s-%s)*{set:room_rate}' % (LK('rooms', 'night', 'rooms_held'), LK('rooms', 'night', 'picked_up')), 'money')]),
    FORM('arrival_sheet', 'Arrival Sheet', 'One arrival day: households and guests', 'arrivals.date', F(('Households', 'arrivals.households'), ('Guests', 'arrivals.guests')) + [
        FF('Rooms at two guests a room', 'ROUNDUP(%s/2,0)' % LK('arrivals', 'date', 'guests'), 'int'), FF('Days before the wedding', '{set:wedding_day}-{pick}', 'int'), FF('Share of all guests', 'IFERROR(%s/%s,0)' % (LK('arrivals', 'date', 'guests'), TOT), 'pct')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('guest_summary', 'Guest List Summary', 'Side and tier balance of the guest list', 'sidebal.row_id', [
        '{set:couple}, dated {today}. Guest list summary: {col:sidebal.hh_total} households and {col:sidebal.guests_total} guests.',
        'Row {col:sidebal.row_id}: {col:sidebal.side}, {col:sidebal.tier}: {col:sidebal.households} households and {col:sidebal.guests} guests, {col:sidebal.share} of the list.',
        'The whole {col:sidebal.side} side has {col:sidebal.side_guests} guests against {col:sidebal.agreed_guests} agreed ({col:sidebal.agreed_text}). Side check: {col:sidebal.flag}.'], ['The couple'], NOTE),
    DOC('headcount_page', 'Headcount Forecast Page', 'Low, expected and high headcount', 'forecast.row_id', [
        '{set:couple}, dated {today}. Headcount forecast for the final count due on {col:forecast.headcount_date}.',
        'Low {col:forecast.low_total}, expected {col:forecast.likely_total}, high {col:forecast.high_total}. Guests still pending: {col:forecast.pending_total}. The forecast is your own estimate, not a promise.',
        'This row, {col:forecast.tier} guests in the region {col:forecast.region}: {col:forecast.invited} invited, {col:forecast.yes} yes, {col:forecast.pending} pending, expected {col:forecast.expected}.',
        'If everyone says yes we are {col:forecast.over} seats over the seated capacity.'], ['The couple', 'Caterer'], NOTE),
    DOC('rsvp_page', 'RSVP Status Page', 'Yes, no and pending replies by list', 'rweek.week', [
        '{set:couple}, dated {today}. RSVP status page. The week starting {col:rweek.week_start} brought {col:rweek.replies} replies, {col:rweek.yes} yes and {col:rweek.no} no. Share of all guests replied by the end of the week: {col:rweek.cumulative}.',
        'A list: {col:rweek.yes_a} yes, {col:rweek.no_a} no, {col:rweek.pend_a} pending. B list: {col:rweek.yes_b} yes, {col:rweek.no_b} no, {col:rweek.pend_b} pending.',
        'Replies close on {set:rsvp_deadline}.'], ['The couple'], NOTE),
    DOC('chase_page', 'Chase List Page', 'One call to make', 'chase.rank', [
        '{set:couple}, dated {today}. Chase list, call {col:chase.rank}.',
        'Household: {col:chase.household}. Contact: {col:chase.contact}, {col:chase.phone}. Reason: {col:chase.reason}. Guests at stake: {col:chase.stake} of {col:chase.guests}. Silent days: {col:chase.silent_days}. Contact status: {col:chase.status}.',
        'Replies close on {col:chase.rsvp_deadline}. {col:chase.pending_hh} households and {col:chase.pending_guests} guests are silent in all. Write down what they say on the Chase Log Sheet.'], ['The couple', 'Helper'], NOTE),
    DOC('caterer_letter', 'Caterer Headcount Letter', 'Headcount and meal counts for the caterer', 'mtable.table', [
        'Dear caterer,',
        '{col:mtable.couple} send you our expected headcount of {col:mtable.likely}. The final headcount comes on {col:mtable.headcount_date}, as in your contract.',
        'Meal counts so far: meat {col:mtable.all_meat}, fish {col:mtable.all_fish}, vegetarian {col:mtable.all_veg}, vegan {col:mtable.all_vegan}. Table {col:mtable.table} has {col:mtable.guests} guests and {col:mtable.notes} short dietary notes.',
        'Please tell us the figure you need by the date in the contract.'], ['The couple', 'Caterer'], NOTE),
    DOC('meals_page', 'Meals by Table Page', 'Meals of one table', 'mtable.table', [
        '{set:couple}, dated {today}. Meals for table {col:mtable.table}: {col:mtable.guests} guests.',
        'Meat {col:mtable.meat}, fish {col:mtable.fish}, vegetarian {col:mtable.vegetarian}, vegan {col:mtable.vegan}, children {col:mtable.children}. Dietary notes: {col:mtable.notes}. Guests without a meal: {col:mtable.no_meal}.',
        'Give this page to the caterer with the place cards.'], ['The couple', 'Caterer'], NOTE),
    DOC('diet_page', 'Dietary Notes Page', 'One short dietary note', 'diet.rank', [
        '{set:couple}, dated {today}. Dietary note number {col:diet.rank}.',
        'Guest {col:diet.guest} of {col:diet.household}, table {col:diet.table}: {col:diet.note}. RSVP: {col:diet.rsvp}.',
        'A short note only. Pass it to the caterer with the table list.'], ['The couple', 'Caterer'], NOTE),
    DOC('timeline_page', 'Invitation Timeline Page', 'One invitation step', 'itime.step', [
        '{set:couple}, dated {today}. Invitation step: {col:itime.step}.',
        'Date: {col:itime.date}, {col:itime.weeks_before} weeks before the wedding. Days left: {col:itime.days_left}. Status: {col:itime.status}.',
        'Check the dates with your printer and your own plan.'], ['The couple'], NOTE),
    DOC('paper_page', 'Paper and Postage Order', 'One line of the paper order', 'paper.item', [
        '{col:paper.couple}, dated {today}. Order for the stationery printer: {col:paper.item}.',
        'Quantity {col:paper.qty} with {col:paper.spares} spares, unit cost {col:paper.unit_cost}, total {col:paper.total}.',
        'Please confirm the price and the date the order is ready.'], ['The couple', 'Printer'], NOTE),
    DOC('room_page', 'Room Block Pickup Page', 'Room block pickup for the hotel', 'roomhh.rank', [
        '{col:roomhh.couple}, dated {today}. Room block pickup: {col:roomhh.picked_up_total} of {col:roomhh.rooms_held_total} rooms picked up, {col:roomhh.to_fill} still to fill.',
        'Cut-off date: {col:roomhh.room_cutoff}. Household {col:roomhh.household}, {col:roomhh.lodging}: {col:roomhh.rooms_needed} rooms needed, status {col:roomhh.booked}.',
        'Please hold the block to the cut-off date in your contract.'], ['The couple', 'Hotel contact'], NOTE),
    DOC('arrivals_page', 'Arrivals by Day Page', 'Arrivals of one day', 'arrivals.date', [
        '{set:couple}, dated {today}. Arrivals on {col:arrivals.date}.',
        'Households: {col:arrivals.households}. Guests: {col:arrivals.guests}.',
        'Share this page with the hotel contact and the person who runs the transport.'], ['The couple', 'Hotel contact'], NOTE),
    DOC('guest_note', 'Guest Information Note', 'What a household needs to know', 'households.household_id', [
        'Dear {col:households.contact},',
        '{col:households.couple} are getting married on {col:households.wedding_day} and we would love to see {col:households.household} there.',
        'Please reply by {col:households.rsvp_deadline}. If you stay in the hotel block, please book by {col:households.room_cutoff}. Tell us a meal choice for each guest and any short dietary note.',
        'We will send the travel and hotel details with your invitation.'], ['The couple'], "Sample wording: adapt it to your own wedding and your own guests."),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('first_draft', 'Guest list first draft', 'itime', 'itime.date', [('Each partner writes a list of everyone they want', -330), ('Merge the two lists into households', -320), ('Mark the A list and the B list', -310), ('Check the total against the venue capacity', -300),
                                                                          ('Agree the side and tier balance', -290), ('Mark who travels and who needs a room', -280)]),
    CHK('balance_review', 'Side and tier balance review', 'itime', 'itime.date', [('Open the Side and Tier Balance table', 0), ('Compare each side with the agreed split', 1), ('Decide who moves to the B list', 3), ('Ask each parent for their final names', 7), ('Agree the final split', 10)]),
    CHK('std_send', 'Save-the-date send', 'itime', 'itime.date', [('Confirm every household contact', -14), ('Check the contact status of each household', -10), ('Write the short message', -7), ('Send to the A list', 0), ('Note the date in Households', 1), ('Follow up on the households with no answer', 14)]),
    CHK('invite_send', 'Invitation send', 'households', 'households.invite_sent', [('Proof the invitation and the reply card', -21), ('Order the printed suites with spares', -14), ('Check the postage for each region', -10), ('Address by household', -5), ('Post or send the invitations', 0), ('Note the sent date in Households', 1), ('Start the reply tracking', 7)]),
    CHK('b_wave', 'B list second wave', 'households', 'households.invite_sent', [('Count the seats opened by declines', -7), ('Pick the next B households by rank', -5), ('Check the last send date', -3), ('Send the invitations', 0), ('Note the sent date', 1), ('Chase the first replies', 10)]),
    CHK('weekly_chase', 'Weekly RSVP chase', 'itime', 'itime.date', [('Open the RSVP Chase List', 0), ('Call the first households in the call order', 0), ('Write down each answer in Households', 1), ('Message the households you could not reach', 2), ('Ask a family helper to chase the rest', 3), ('Check the reply pace', 4)]),
    CHK('reply_close', 'Reply-by day close', 'itime', 'itime.date', [('Message the last silent households', -3), ('Call anyone you could not reach', -1), ('Close the replies', 0), ('Mark the silent households as no', 1), ('Offer the open seats to the B list', 2), ('Send the final count to the caterer plan', 7)]),
    CHK('final_count', 'Final headcount to the caterer', 'itime', 'itime.date', [('Check the headcount forecast', -14), ('Check the minimum guarantee in your contract', -10), ('Reconcile the meals with the yes guests', -7), ('Send the final number', -1), ('Ask for written confirmation', 0), ('Note the cost at the final number', 1)]),
    CHK('meal_collect', 'Meal and dietary collection', 'itime', 'itime.date', [('Add the meal choices to the reply message', -14), ('Collect a meal for each guest', 0), ('Ask for short dietary notes only', 0), ('Chase the households with a meal missing', 7), ('Reconcile the meals with the headcount', 10), ('Send the table sheets to the caterer', 21)]),
    CHK('room_followup', 'Room block follow-up', 'rooms', 'rooms.night', [('Ask the hotel contact for the pickup count', -90), ('Message the households with a room not booked', -75), ('Check the pickup against the plan', -60), ('Ask the hotel to hold the block', -50), ('Check the cut-off date in your contract', -46), ('Release or extend the block', -44)]),
    CHK('guest_travel', 'Guest travel information', 'arrivals', 'arrivals.date', [('Send the arrival day to each household', -60), ('Confirm the arrival dates', -45), ('Share the shuttle plan', -21), ('Send the arrivals page to the hotel', -14), ('Confirm the room list', -7), ('Check the day-before plan', -1)]),
    CHK('small_wedding', 'Small wedding first guest list', 'itime', 'itime.date', [('Write every name you want at 30 guests', -120), ('Group them into households', -115), ('Skip the B list', -110), ('Send one round of invitations', -100), ('Chase by message', -80), ('Give the final number to the venue', -21)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
M = MSG
messages = [
    M('m_save', 'Household: save the date', 'households', 'households.phone', 'Hello {contact}, save the date: our wedding is on {wedding_day}. The invitation will follow. {couple}'),
    M('m_invite', 'Household: your invitation is on its way', 'households', 'households.phone', 'Hello {contact}, your invitation is on its way. Please reply by {rsvp_deadline}. {couple}'),
    M('m_reply', 'Household: please reply, plan seats', 'households', 'households.phone', 'Hello {contact}, please reply by {rsvp_deadline} so we can plan the seats. {couple}'),
    M('m_gentle', 'Household: a gentle reminder', 'households', 'households.phone', 'Hello {contact}, we have not yet heard from {household}. Could you reply by {rsvp_deadline}? {couple}'),
    M('m_last', 'Household: last reminder', 'households', 'households.phone', 'Hello {contact}, last reminder: replies close on {rsvp_deadline}. {couple}'),
    M('m_thanks', 'Household: thank you for your reply', 'households', 'households.phone', 'Hello {contact}, thank you for your reply. We have {household} down as {rsvp}. {couple}'),
    M('m_sorry', 'Household: we will miss you', 'households', 'households.phone', 'Hello {contact}, we are sorry you cannot come. We will miss you. {couple}'),
    M('m_meal', 'Household: please choose a meal', 'households', 'households.phone', 'Hello {contact}, please choose a meal for each guest of {household} by {rsvp_deadline}. {couple}'),
    M('m_diet', 'Household: a short dietary note', 'households', 'households.phone', 'Hello {contact}, please send any short dietary note for {household} by {rsvp_deadline}. {couple}'),
    M('m_plusone', 'Household: your plus-one slot', 'households', 'households.phone', 'Hello {contact}, you have a plus-one slot. Please send a name by {rsvp_deadline}. {couple}'),
    M('m_named', 'Household: named guests only', 'households', 'households.phone', 'Hello {contact}, the invitation is for the guests named on it. Thank you for understanding. {couple}'),
    M('m_children', 'Household: children are welcome', 'households', 'households.phone', 'Hello {contact}, children are welcome. Please confirm how many are coming from {household} by {rsvp_deadline}. {couple}'),
    M('m_room', 'Household: room block cut-off', 'households', 'households.phone', 'Hello {contact}, the hotel holds rooms for our guests until {room_cutoff}. Please book by then. {couple}'),
    M('m_arrival', 'Household: arrival day and shuttle', 'households', 'households.phone', 'Hello {contact}, please confirm your arrival on {arrival} so we can plan the shuttle. {couple}'),
    M('m_table', 'Household: your table', 'households', 'households.phone', 'Hello {contact}, we have {household} at {table} for the reception. {couple}'),
    M('m_travel', 'Household: travel and hotel details', 'households', 'households.phone', 'Hello {contact}, the travel and hotel details are in your invitation. The wedding is on {wedding_day}. {couple}'),
    M('m_b_love', 'B list household: we would love you', 'households', 'households.phone', 'Hello {contact}, we would love to have {household} at our wedding on {wedding_day}. Please reply by {rsvp_deadline}. {couple}'),
    M('m_b_invite', 'B list household: your invitation', 'households', 'households.phone', 'Hello {contact}, your invitation to our wedding on {wedding_day} is on its way. Please reply by {rsvp_deadline}. {couple}'),
    M('m_contact', 'Household: confirm your contact details', 'households', 'households.phone', 'Hello {contact}, please confirm that this is the best way to reach {household}. {couple}'),
    M('m_full', 'Household: the venue is full', 'households', 'households.phone', 'Hello {contact}, we are sorry, the venue is full and we cannot add more guests. Thank you for understanding. {couple}'),
    M('m_par_chase', 'Parent: help chase the replies', 'chase', 'chase.parent1_phone', 'Hello, {pending_hh} households have not replied yet. Can you help us chase before {rsvp_deadline}? {couple}'),
    M('m_par_share', 'Parent: your side and the agreed share', 'sidebal', 'sidebal.parent_phone', 'Hello, your side has {side_guests} guests. The agreed share is {agreed_text}. {couple}'),
    M('m_partner_fc', 'Partner: the headcount forecast', 'forecast', 'forecast.partner_phone', 'Hello, the headcount forecast is low {low_total}, likely {likely_total}, high {high_total}. {couple}'),
    M('m_partner_cater', 'Partner: the final count is due', 'forecast', 'forecast.partner_phone', 'Hello, the caterer needs the final count by {headcount_date}. The likely headcount is {likely_total}. {couple}'),
    M('m_partner_silent', 'Partner: guests are silent', 'chase', 'chase.partner_phone', 'Hello, {pending_guests} guests are silent. Here is the chase list. {couple}'),
    M('m_partner_over', 'Partner: over capacity if all say yes', 'forecast', 'forecast.partner_phone', 'Hello, if everyone says yes we are {over} seats over capacity. {couple}'),
    M('m_cater_fc', 'Caterer: the headcount forecast', 'forecast', 'forecast.caterer_phone', 'Hello, our headcount forecast is {likely_total}. The final figure comes on {headcount_date}. {couple}'),
    M('m_cater_meals', 'Caterer: meal counts', 'mtable', 'mtable.caterer_phone', 'Hello, the meal counts are meat {all_meat}, fish {all_fish}, vegetarian {all_veg}, vegan {all_vegan}. {couple}'),
    M('m_cater_diet', 'Caterer: dietary notes by table', 'mtable', 'mtable.caterer_phone', 'Hello, table {table} has {notes} short dietary notes. The notes by table are attached. {couple}'),
    M('m_venue_count', 'Venue: the expected guest count', 'forecast', 'forecast.venue_phone', 'Hello, the expected guest count is {likely_total}. We will confirm by {headcount_date}. {couple}'),
    M('m_hotel_pickup', 'Hotel contact: the pickup so far', 'roomhh', 'roomhh.hotel_phone', 'Hello, the pickup is {picked_up_total} of {rooms_held_total} rooms. Please hold the block until {room_cutoff}. {couple}'),
    M('m_hotel_extend', 'Hotel contact: extend the cut-off', 'roomhh', 'roomhh.hotel_phone', 'Hello, can we extend the cut-off to {extended_cutoff}? {couple}'),
    M('m_printer', 'Printer: quantity and spares', 'paper', 'paper.printer_phone', 'Hello, we need {qty} of {item} and {spares} spares. {couple}'),
    M('m_lead_chase', 'Wedding party lead: chase households', 'chase', 'chase.lead_phone', 'Hello, please chase the households on your list. {pending_hh} are still silent. {couple}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
HELDX = HELD; PICKX = PICK
kpis = [
    KPI('Households invited', HID, 'int'), KPI('Guests invited', TOT, 'int'),
    KPI('A list guests', 'SUMIFS(%s,%s,%s)' % (SZ, HR('list_ab'), LA), 'int'), KPI('B list guests', 'SUMIFS(%s,%s,%s)' % (SZ, HR('list_ab'), LB), 'int'),
    KPI('Yes replies, guests', YESG, 'int'), KPI('No replies, guests', NOG, 'int'), KPI('Pending replies, guests', PENDG, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Reply rate, households', 'IFERROR(1-COUNTIFS(%s,%s,%s,"<>")/%s,0)' % (HR('rsvp'), RP, HR('household_id'), HID), 'pct'),
    KPI('Households silent', 'COUNTIFS(%s,%s,%s,"<>")' % (HR('rsvp'), RP, HR('household_id')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Expected headcount, yes plus pending', 'ROUND(%s,0)' % LIKELY, 'int'), KPI('Low headcount', 'ROUND(%s,0)' % LOWT, 'int'), KPI('High headcount', 'ROUND(%s,0)' % HIGHT, 'int'),
    KPI('Everyone-says-yes headcount', TOT, 'int'), KPI('Seats over capacity if everyone says yes', 'MAX(0,%s+{set:seats_others}-{set:venue_capacity})' % TOT, 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Seats left at the expected headcount', '%s-ROUND(%s,0)' % (SEATED, LIKELY), 'int'),
    KPI('Partner 1 side share', 'IFERROR(SUMIFS(%s,%s,%s)/%s,0)' % (SZ, HR('side'), S1, TOT), 'pct'), KPI('Partner 2 side share', 'IFERROR(SUMIFS(%s,%s,%s)/%s,0)' % (SZ, HR('side'), S2, TOT), 'pct'),
    KPI('Shared friends share', 'IFERROR(SUMIFS(%s,%s,%s)/%s,0)' % (SZ, HR('side'), SS, TOT), 'pct'),
    KPI('Children invited', 'COUNTIFS(%s,%s,%s,"<>")' % (GR_('age_group'), CHILD, GR_('guest_id')), 'int'), KPI('Plus-ones named', 'COUNTIFS(%s,%s,%s,"<>")' % (GR_('plus_one'), YES, GR_('guest_id')), 'int'),
    KPI('Open plus-one slots', OPENP, 'int'), KPI('Meal choices still missing', 'COUNTIFS(%s,"<>",%s,%s,%s,"")' % (GR_('guest_id'), GR_('rsvp'), RY, GR_('meal')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Dietary notes recorded', 'COUNTIFS(%s,"<>",%s,"<>")' % (GR_('dietary'), GR_('guest_id')), 'int'), KPI('Meal choices recorded', 'SUM(%s)' % GR_('meal_done'), 'int'),
    KPI('Days to the reply-by date', 'IF({set:rsvp_deadline}="","",{set:rsvp_deadline}-{today})', 'int', alert={"when": "< 14", "style": "warn"}),
    KPI('Days to the headcount date', 'IF({set:headcount_date}="","",{set:headcount_date}-{today})', 'int'),
    KPI('Invitation paper cost', 'SUM(%s)' % R('paper', 'total'), 'money'), KPI('Rooms picked up', PICKX, 'int'), KPI('Rooms still to fill by the cut-off', '%s-%s' % (HELDX, PICKX), 'int'),
    KPI('Block exposure if no more rooms book', 'MAX(0,ROUNDUP(%s*{set:attrition_pct},0)-%s)*{set:room_rate}' % (HELDX, PICKX), 'money', alert={"when": "> 0", "style": "warn"}),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Guests and RSVP Dashboard", "kpis": kpis,
    "monthly": {"title": "Guests invited, told and replied by month", "date": "households.invite_sent", "series": [
        {"label": "Guests invited", "sum": "households.size", "date": "households.invite_sent"}, {"label": "Told by save the date", "sum": "households.size", "date": "households.save_the_date"},
        {"label": "Replies received", "sum": "guests.replied", "date": "guests.rsvp_date"}]},
    "breakdowns": [{"title": "Guests by side", "by": "households.side", "value": "households.size", "agg": "sum"}, {"title": "Guests by region", "by": "households.region", "value": "households.size", "agg": "sum"},
                   {"title": "Replies by status", "by": "guests.rsvp", "agg": "count"}, {"title": "Households by list", "by": "households.list_ab", "agg": "count"}]}


def AG(kind, table, value=None, date=None, label=None, where=None): return AGG(kind, table, value, date, where, label)
def RS(table, col, lst_by=None):
    return [AG('count', table, label='Yes', where=[(col, '=', RY)]), AG('count', table, label='No', where=[(col, '=', RN)]), AG('count', table, label='Pending', where=[(col, '=', RP)])]
def RSH(): return [AG('sum', 'households', 'households.size', label='Yes', where=[('rsvp', '=', RY)]), AG('sum', 'households', 'households.size', label='No', where=[('rsvp', '=', RN)]),
                   AG('sum', 'households', 'households.size', label='Pending', where=[('rsvp', '=', RP)])]
insights = {"filters": [{"label": "Side", "list": "side"}, {"label": "Tier", "list": "tier"}, {"label": "Region", "list": "region"}],
    "gauges": [
        {"title": "Reply rate of households", "num": AG('count', 'households', where=[('rsvp', '<>', RP)]), "den": AG('count', 'households', where=[('size', '>=', 0)])},
        {"title": "Expected headcount against capacity", "num": AG('sum', 'capacity', 'capacity.headcount', where=[('scenario', '=', tok('scen', 'Expected'))]), "den": AG('sum', 'capacity', 'capacity.headcount', where=[('scenario', '=', tok('scen', 'Seated capacity'))])},
        {"title": "Meals chosen against yes guests", "num": AG('sum', 'guests', 'guests.meal_done'), "den": AG('count', 'guests', where=[('rsvp', '=', RY)])},
        {"title": "Side balance against the agreed split", "num": AG('sum', 'sidebal', 'sidebal.within'), "den": AG('sum', 'sidebal', 'sidebal.guests')},
        {"title": "Rooms picked up against held", "num": AG('sum', 'rooms', 'rooms.picked_up'), "den": AG('sum', 'rooms', 'rooms.rooms_held')},
        {"title": "Households with contact up to date", "num": AG('count', 'households', where=[('contact_status', '=', UP)]), "den": AG('count', 'households', where=[('size', '>=', 0)])}],
    "charts": [
        CHART('Replies by status', 'bar', 'guests.rsvp', [AG('count', 'guests', label='Guests')]),
        CHART('Replies by list', 'bar', 'guests.list_ab', RS('guests', 'rsvp')),
        CHART('Replies by side', 'bar', 'guests.side', RS('guests', 'rsvp')),
        CHART('Replies by tier', 'bar', 'guests.tier', RS('guests', 'rsvp')),
        CHART('Replies by region', 'bar', 'households.region', RSH()),
        CHART('Replies per week', 'column', 'rweek.week', [AG('sum', 'rweek', 'rweek.yes', label='Yes'), AG('sum', 'rweek', 'rweek.no', label='No')]),
        CHART('Cumulative reply share by week', 'line', 'rweek.week', [AG('sum', 'rweek', 'rweek.cumulative', label='Share replied')]),
        CHART('Guests by side and tier', 'stacked', 'sidebal.tier', [AG('sum', 'sidebal', 'sidebal.guests', label='Partner 1', where=[('side', '=', S1)]), AG('sum', 'sidebal', 'sidebal.guests', label='Partner 2', where=[('side', '=', S2)]),
                                                                         AG('sum', 'sidebal', 'sidebal.guests', label='Shared', where=[('side', '=', SS)])]),
        CHART('Guests by age group', 'bar', 'guests.age_group', [AG('count', 'guests', label='Guests')]),
        CHART('Meals chosen', 'bar', 'meals.meal', [AG('sum', 'meals', 'meals.count', label='Guests')]),
        CHART('Dietary notes', 'bar', 'guests.dietary', [AG('count', 'guests', label='Guests')]),
        CHART('Meals by table', 'stacked', 'mtable.table', [AG('sum', 'mtable', 'mtable.meat', label='Meat'), AG('sum', 'mtable', 'mtable.fish', label='Fish'), AG('sum', 'mtable', 'mtable.vegetarian', label='Vegetarian'),
                                                           AG('sum', 'mtable', 'mtable.vegan', label='Vegan')]),
        CHART('Households by contact status', 'bar', 'households.contact_status', [AG('count', 'households', label='Households')]),
        CHART('Households by lodging', 'bar', 'households.lodging', [AG('count', 'households', label='Households')]),
        CHART('Households by region', 'bar', 'households.region', [AG('count', 'households', label='Households')]),
        CHART('Guests by region', 'bar', 'households.region', [AG('sum', 'households', 'households.size', label='Guests')]),
        CHART('Headcount low, likely and high', 'bar', 'forecast.region', [AG('sum', 'forecast', 'forecast.low', label='Low'), AG('sum', 'forecast', 'forecast.expected', label='Likely'), AG('sum', 'forecast', 'forecast.high', label='High')]),
        CHART('Headcount against capacity', 'bar', 'capacity.scenario', [AG('sum', 'capacity', 'capacity.headcount', label='Seated headcount')]),
        CHART('Cost by headcount', 'line', 'polres.policy', [AG('sum', 'polres', 'polres.food_cost', label='Food cost')]),
        CHART('Paper cost by item', 'bar', 'paper.item', [AG('sum', 'paper', 'paper.total', label='Total')]),
        CHART('Chase attempts by channel', 'bar', 'households.chase_channel', [AG('count', 'households', label='Households')]),
        CHART('Households by invitation wave', 'bar', 'households.list_ab', [AG('count', 'households', label='Households')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Final headcount forecast", "why": "confirmed yes plus pending households at your yes rate by region gives low, likely and high with the cost of each and the number for the caterer", "where": "Final Headcount Forecast"},
    {"name": "B list cascade", "why": "open seats at the expected headcount and the next B list household by rank, so declines never leave seats empty", "where": "B List Cascade"},
    {"name": "Last send date for the B list", "why": "counts back from your reply-by date to the latest day a second-wave invitation can still go out", "where": "Last Send Date B List"},
    {"name": "RSVP chase ranker", "why": "silent households ranked by guests at stake, days silent and contact status, skipping those you chased recently", "where": "RSVP Chase Ranker"},
    {"name": "Plus-one and children policy test", "why": "four policies side by side with headcount, food cost and venue fit, and the cheapest and the most inclusive named", "where": "Plus-one Children Policy"},
    {"name": "Guarantee exposure", "why": "what you pay for empty seats if fewer guests come than your minimum guarantee, on a ladder of five headcounts", "where": "Guarantee Exposure"},
    {"name": "Room block attrition exposure", "why": "the rooms you must fill against the rooms you expect, priced at your room rate, before the attrition date", "where": "Room Block Attrition"},
    {"name": "Side balance check", "why": "guests by side against the split you agreed with a verdict on which side is heavy and by how many", "where": "Side Balance Check"},
    {"name": "Capacity traffic light", "why": "confirmed, expected and everyone-says-yes headcounts against the seated capacity: fits, tight or over by a number of seats", "where": "Capacity Light"},
    {"name": "Reply pace forecast", "why": "replies per week so far, slowed as replies always slow, against the guests still silent before the reply-by date", "where": "Reply Pace Forecast"}]
competitors = [
    {"what": "a free planning app", "lacks": "keeps a guest list but has no headcount forecast by region, no B list cascade, no cost at each headcount and no ranked chase list"},
    {"what": "a single budget spreadsheet", "lacks": "has a guest count cell but no households, no RSVP tracker, no minimum guarantee exposure and no room block attrition check"},
    {"what": "a printable wedding binder", "lacks": "has blank guest pages but does no sums, no side balance, no capacity check and no meal order for the caterer"},
    {"what": "a wedding website with a registry", "lacks": "collects replies on a company's pages, has no private forecast, no policy test for plus-ones and children, and shares your guest data"}]
guide = [
    'Open Start here and type your names, the wedding day, the reply-by date, the seated capacity and the price per guest in the yellow cells. Replace demo data: clear the sample rows and type your own.',
    'Fill Households first: one row per invitation (one invitation, several people) with side, tier, list, region, number of guests and lodging. Then list each person in Guests with an age group, an RSVP, a meal and a short dietary note.',
    'Mark the A list (the first invitations) and the B list (the second wave when someone declines). The B List Queue ranks the B households and the B List Cascade names the next one to invite.',
    'Type the RSVP as replies arrive. The RSVP Chase List ranks the silent households and Replies by Week shows the pace; the Reply Pace Forecast says if you are on pace before the reply-by date.',
    'Edit the Expected Yes Rates by region (a typical starting value, not a fact about your area). The Forecast by Tier and the Final Headcount Forecast give low, likely and high and the number to give the caterer.',
    'Compare the headcount with the seated capacity in the Capacity Traffic Light and test your plus-one and children policy in Policy Options and Policy Results.',
    'Type each meal choice and a few words of dietary note only. Meal Counts, Meals by Table and the Caterer Meal Order follow from the replies.',
    'Use the Invitation Timeline and Paper and Postage for the dates and the cost of the paper; the total feeds the stationery line of your budget.',
    'Type the room block nights and the rooms picked up; Room Pickup lists the households that need a room and the Room Block tools show the rooms still to fill and the cost if the block is not filled.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A couple with a small wedding (30 guests, no B list) uses the same sheets with fewer rows: keep one tier, skip the B List Queue and leave the room block empty.',
    'This workbook has no macros and works in Excel and Google Sheets. Print any page for a parent or a helper.',
    'Why a workbook: one flat price, no vendor ever sees your details, no fees on your gifts, your own numbers, and it works offline.',
    'What this is not: not a booking service, not a payment service, and not legal, tax or insurance advice. Every default is a typical starting value you can edit, never a promise.']
listing = {"title": "Wedding Guest List and RSVP Tracker Excel Template: Headcount Forecast, A List and B List, Meals, Room Block, Seating Count",
    "headline": "Guest list, RSVPs, headcount and room block for your wedding",
    "tags": ["wedding guest list", "rsvp tracker", "wedding planner", "headcount forecast", "a list b list", "wedding spreadsheet", "excel template", "meal choices", "plus one policy", "room block", "wedding checklist", "invitation tracker", "wedding budget"],
    "description": ("Plan the guest side of your wedding in one Excel workbook. Built for an engaged couple planning their own wedding, with a parent or a wedding party lead helping to chase replies. "
        "Households holds one row per invitation (one invitation, several people) with side, tier, list, region and RSVP, and Guests holds each guest with an age group, a meal and a few words of dietary note. Names only: no addresses and no health details.\n\n"
        "The forecast does the thinking. Confirmed yes plus pending households at the yes rate you edit for each region gives a low, likely and high headcount, the cost at each figure and the number to give the caterer. The Capacity Traffic Light tests the headcount against the seated capacity, "
        "the B List Cascade names the next B list household when declines open seats, and the RSVP Chase List ranks the silent households by guests at stake, days silent and contact status.\n\n"
        "Meal Counts, Meals by Table and a Caterer Meal Order reconcile the meals with the headcount. The Plus-one and Children Policy test compares four policies by headcount and food cost. The Guarantee Exposure tool shows what you pay for empty seats, and the room block sheets show the rooms still to fill and the cost if the block is not filled. "
        "The Invitation Timeline and Paper and Postage price the paper.\n\n"
        f"{len(tools)} tools answer weekly questions. Print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and send {len(messages)} ready text messages to guests, parents, the caterer, the venue, the hotel contact and the printer. "
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Every default is a typical starting value you can edit and forecasts are your own estimate. It is not a booking service, not a payment service and not legal, tax or insurance advice. This is part two of the Wedding Planning suite."),
    "features": ["Households and guests with A list and B list", "Headcount forecast: low, likely and high", "B list cascade and last send date", "Ranked RSVP chase list", "Capacity traffic light against the venue seats",
                 "Plus-one and children policy test", "Meal counts, meals by table and caterer order", "Minimum guarantee exposure", "Room block pickup and attrition exposure", f"{len(tools)} decision tools",
                 f"{len(forms)} printable sheets and {len(documents)} pages", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}

lists = BASE_LISTS + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p2', slug='wedding-guests', profession='Wedding Planning', name='Guests, Invitations and RSVPs',
         tagline='Track every household, reply, meal and room, and know your headcount', price_usd=29,
         colors={"primary": "#7A4B68", "accent": "#D9A86C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 2, "of": 8, "focus": "Guests, invitations and RSVPs"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wp2.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']), 'va', len(lists[-2]['values']), 'vb', len(lists[-1]['values']))
