"""Wedding Planning suite - part 7: Events, Travel and Honeymoon."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp7_lists import *
from wp7_tables import settings, tables, DONE, PLAN, OA, OB, RECV, PROM, NOTC, SAV, CHOSEN, OTHER_EV, RESERVE, MARRIAGE, YES, FUNDS, OPT, OPTK, TIN, MS
from wp7_tools import tools, TOTAL, OVER5, OPL, FIRST18, PTOT
import wp7_data as D

SUITE = 'fx-20261116-wedding'
NOTE = "Sample wording: adapt it to your own wedding."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c_): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c_, t, idc)
def R(t, c_): return '{range:%s.%s}' % (t, c_)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('event_sheet', 'Event Sheet', 'Event with its cost and guests', 'events.event', F(('Date', 'events.date'), ('Status', 'events.status')) + [
        FF('Start', LK('invitees', 'event', 'start'), 'text'), FF('Invitees', LK('invitees', 'event', 'invitees'), 'int'),
        FF('Event cost', 'SUMIFS(%s,%s,{pick})' % (R('lines', 'amount'), R('lines', 'event')), 'money'), FF('Event budget', 'SUMIFS(%s,%s,{pick})' % (R('lines', 'planned'), R('lines', 'event')), 'money'),
        FF('Paid so far', 'SUMIFS(%s,%s,{pick})' % (R('lines', 'paid'), R('lines', 'event')), 'money'), FF('Cost per invitee', LK('ecosts', 'event', 'per_guest'), 'money'),
        FF('Days to the event', LK('events', 'event', 'date') + '-{today}', 'int')],
        {"from": "lines", "match": "lines.event", "columns": ["item", "planned", "amount", "paid"], "max": 8}),
    FORM('event_line_sheet', 'Event Line Sheet', 'One cost line of an event', 'lines.line_id', F(('Event ID', 'lines.event_id'), ('Event', 'lines.event'), ('Item', 'lines.item'), ('Planned', 'lines.planned'), ('Amount', 'lines.amount'),
        ('Paid', 'lines.paid')) + [
        FF('Still to pay on this line', LK('lines', 'line_id', 'amount') + '-' + LK('lines', 'line_id', 'paid'), 'money'), FF('Over or under plan', LK('lines', 'line_id', 'amount') + '-' + LK('lines', 'line_id', 'planned'), 'money'),
        FF('Event date', LK('lines', 'line_id', 'date'), 'date'), FF('Event total', LK('lines', 'line_id', 'event_cost'), 'money')]),
    FORM('event_invitee_sheet', 'Event Invitee Sheet', 'Invitees of one event', 'invitees.event', F(('Start', 'invitees.start'), ('Invitees', 'invitees.invitees')) + [
        FF('Event date', LK('events', 'event', 'date'), 'date'), FF('Share of the guest list', 'IFERROR(%s/{set:guest_list},0)' % LK('invitees', 'event', 'invitees'), 'pct'),
        FF('Event cost', LK('ecosts', 'event', 'cost'), 'money'), FF('Cost per invitee', LK('ecosts', 'event', 'per_guest'), 'money'), FF('Guests on your list', '{set:guest_list}', 'int')]),
    FORM('optional_event_sheet', 'Optional Event Sheet', 'What an event takes from the Other events line', 'ecosts.event', F(('Cost', 'ecosts.cost'), ('Cost per invitee', 'ecosts.per_guest')) + [
        FF('Other events line, planned', OPL, 'money'), FF('Share of the line', 'IFERROR(%s/%s,0)' % (LK('ecosts', 'event', 'cost'), OPL), 'pct'), FF('Invitees', LK('invitees', 'event', 'invitees'), 'int'),
        FF('Event date', LK('events', 'event', 'date'), 'date'), FF('Days before the wedding', '{set:wedding_day}-' + LK('events', 'event', 'date'), 'int')]),
    FORM('night_sheet', 'Guest-night Sheet', 'One night of guests and rooms', 'nights.night', F(('Guests staying', 'nights.guests'), ('Rooms needed', 'nights.rooms')) + [
        FF('Share of all guest-nights', 'IFERROR(%s/SUM(%s),0)' % (LK('nights', 'night', 'guests'), R('nights', 'guests')), 'pct'), FF('Busiest night, rooms', 'MAX(%s)' % R('nights', 'rooms'), 'int'),
        FF('Cost of the rooms at your rate', LK('nights', 'night', 'rooms') + '*{set:room_rate}', 'money'), FF('Guests sharing a room', '{set:guests_per_room}', 'int')]),
    FORM('dest_quote_sheet', 'Destination Quote Sheet', 'One quote in local money', 'dest.dest_id', F(('Quote ID', 'dest.quote_id'), ('Category', 'dest.category'), ('Vendor', 'dest.vendor'), ('Base price', 'dest.base_price'),
        ('Local amount', 'dest.local_amount'), ('Difference', 'dest.difference'), ('Vendor phone', 'dest.phone')) + [
        FF('Exchange rate used', '{set:exchange_rate}', 'num'), FF('Share of all local quotes', 'IFERROR(%s/SUM(%s),0)' % (LK('dest', 'dest_id', 'local_amount'), R('dest', 'local_amount')), 'pct')]),
    FORM('party_travel_sheet', 'Party Travel Sheet', 'Travel and stay of one person', 'party.party_id', F(('Person', 'party.person'), ('Role', 'party.role'), ('Joins', 'party.event'), ('Flights', 'party.flights'), ('Nights', 'party.nights'),
        ('Helped by the couple', 'party.helped'), ('Stay', 'party.stay'), ('Total', 'party.total'), ('They cover', 'party.they_cover')) + [
        FF('Share the couple covers', 'IFERROR(%s/%s,0)' % (LK('party', 'party_id', 'helped'), LK('party', 'party_id', 'total')), 'pct'), FF('Send flight details by', LK('party', 'party_id', 'flight_by'), 'date')]),
    FORM('paper_lead_sheet', 'Paperwork Lead Sheet', 'One paperwork step and its start date', 'paper.item_id', F(('Step', 'paper.item'), ('Kind', 'paper.kind'), ('Due date', 'paper.due_date'), ('Status', 'paper.status'), ('Owner', 'paper.owner'),
        ('Lead time in days', 'paper.lead_days'), ('Start by', 'paper.start_by'), ('Days left to start', 'paper.days_left'), ('Flag', 'paper.flag')) + [
        FF('Days to the due date', LK('paper', 'item_id', 'due_date') + '-{today}', 'int')]),
    FORM('track_sheet', 'Track Comparison Sheet', 'One line of the two tracks', 'tracks.line', F(('Budget category', 'tracks.cat1'), ('Scales with guests', 'tracks.scales'), ('Share kept', 'tracks.share'), ('One big wedding', 'tracks.big'),
        ('Small ceremony plus a party', 'tracks.small'), ('Difference', 'tracks.difference')) + [
        FF('Share of the total difference', 'IFERROR(%s/SUM(%s),0)' % (LK('tracks', 'line', 'difference'), R('tracks', 'difference')), 'pct'), FF('Rank of the difference', LK('tracks', 'line', 'gap_rank'), 'int')]),
    FORM('hm_item_sheet', 'Honeymoon Item Sheet', 'One honeymoon cost', 'hm.hm_id', F(('Option', 'hm.option'), ('Kind', 'hm.kind'), ('Description', 'hm.description'), ('Amount', 'hm.amount'), ('Days', 'hm.days'), ('Due date', 'hm.due_date'),
        ('Status', 'hm.status')) + [
        FF('Share of the option', 'IFERROR(%s/%s,0)' % (LK('hm', 'hm_id', 'amount'), LK('hm', 'hm_id', 'option_total')), 'pct'), FF('Option total', LK('hm', 'hm_id', 'option_total'), 'money'),
        FF('Gap for this option', LK('hm', 'hm_id', 'gap'), 'money'), FF('Days to the due date', LK('hm', 'hm_id', 'due_date') + '-{today}', 'int')]),
    FORM('hf_sheet', 'Honeymoon Fund Sheet', 'One amount set aside', 'hf.hf_id', F(('Date', 'hf.date'), ('Month', 'hf.month'), ('Source', 'hf.source'), ('Amount', 'hf.amount'), ('Status', 'hf.status')) + [
        FF('Received and promised so far', 'SUMIFS(%s,%s,"<="&%s,%s,%s)+SUMIFS(%s,%s,"<="&%s,%s,%s)' % (R('hf', 'amount'), R('hf', 'date'), LK('hf', 'hf_id', 'date'), R('hf', 'status'), RECV,
                                                                                                    R('hf', 'amount'), R('hf', 'date'), LK('hf', 'hf_id', 'date'), R('hf', 'status'), PROM), 'money'),
        FF('Share of the money received and promised', 'IFERROR(%s/%s,0)' % (LK('hf', 'hf_id', 'amount'), FUNDS), 'pct'), FF('Your chosen option, total', OPT(CHOSEN), 'money')]),
    FORM('hscen_sheet', 'Honeymoon Option Sheet', 'One version of an honeymoon option', 'hscen.scenario', F(('Total', 'hscen.total'), ('Verdict', 'hscen.verdict')) + [
        FF('Funds, received and promised', FUNDS, 'money'), FF('Gap', 'MAX(0,%s-%s)' % (LK('hscen', 'scenario', 'total'), FUNDS), 'money'),
        FF('Share funded', 'IFERROR(MIN(1,%s/%s),0)' % (FUNDS, LK('hscen', 'scenario', 'total')), 'pct'), FF('Option A as planned, total', OPT(OA), 'money'), FF('Option B as planned, total', OPT(OB), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('calendar_page', 'Event Calendar Page', 'Event calendar of one month', 'ecal.month', [
        '{set:couple}, dated {today}. Events in the month starting {col:ecal.month}.',
        'Events: {col:ecal.events}. Cost of the events: {col:ecal.cost}. Invitee places across the events: {col:ecal.invitees}. This month is marked: {col:ecal.flag}.',
        'Use this page to tell your hosts and helpers what the month holds.'], ['The couple', 'Host'], NOTE),
    DOC('event_plan_page', 'One Event Plan', 'One event: date, invitees, lines and cost', 'lines.line_id', [
        '{set:couple}, dated {today}. Plan of the {col:lines.event}, on {col:lines.date}, start {col:lines.start}.',
        'Invitees: {col:lines.invitees}. Event budget: {col:lines.event_budget}. Event cost: {col:lines.event_cost}. Paid so far: {col:lines.event_paid}.',
        'This line: {col:lines.item}, planned {col:lines.planned}, amount {col:lines.amount}, paid {col:lines.paid}. The other lines of the event are on the Event Sheet.',
        'The couple covers {col:lines.couple_covers} of this event, your own rule. The host sends the guest list by {col:lines.list_by}.'], ['The couple', 'Host'], NOTE),
    DOC('combined_page', 'Combined Events Cost', 'Combined cost around the wedding day', 'comb.item', [
        '{set:couple}, dated {today}. Combined cost around the wedding day.',
        '{col:comb.item}: {col:comb.amount}, which is {col:comb.share} of the combined total of the six blocks.',
        'The blocks are the events done and planned, the party travel you cover, your own travel and the honeymoon of your chosen option.'], ['The couple'], NOTE),
    DOC('nights_page', 'Guest-nights Page', 'Guests and rooms for one night', 'nights.night', [
        '{set:couple}, dated {today}. Guests and rooms for: {col:nights.night}.',
        'Guests staying: {col:nights.guests}. Rooms needed at {set:guests_per_room} guests a room: {col:nights.rooms}.',
        'Share this page with the hotel contact. Check the cut-off date of your room block in your contract.'], ['The couple', 'Hotel contact'], NOTE),
    DOC('dest_page', 'Destination Cost Page', 'Destination quote in local money', 'dest.dest_id', [
        '{set:couple}, dated {today}. Destination quote {col:dest.dest_id}: {col:dest.vendor}, category {col:dest.category}.',
        'Base price {col:dest.base_price}. Local amount at the rate {set:exchange_rate}: {col:dest.local_amount}. Difference: {col:dest.difference}.',
        'A destination wedding adds {col:dest.dest_add} for your own travel and the party travel you cover. All local quotes together: {col:dest.local_total} in local money.'], ['The couple', 'Vendor'], NOTE),
    DOC('party_page', 'Party Travel Page', 'Travel and stay of one person', 'party.party_id', [
        '{set:couple}, dated {today}. Dear {col:party.person},',
        'Thank you for standing with us. For the {col:party.event} your flights are {col:party.flights} and your stay of {col:party.nights} nights is {col:party.stay}, a total of {col:party.total}.',
        'We cover {col:party.helped}. You cover {col:party.they_cover}. Please send your flight details by {col:party.flight_by}.'], ['The couple', 'Wedding party member'], NOTE),
    DOC('paper_page', 'Paperwork Lead Page', 'One paperwork step and when to start', 'paper.item_id', [
        '{set:couple}, dated {today}. Paperwork step {col:paper.item_id}: {col:paper.item}.',
        'Kind: {col:paper.kind}. Owner: {col:paper.owner}. Due date: {col:paper.due_date}. Status: {col:paper.status}. Your lead time for the marriage steps is {col:paper.lead_days} days, so start by {col:paper.start_by}.',
        'The lead time is your own number. Check it with your officiant or local office.'], ['The couple'], NOTE),
    DOC('track_page', 'Big vs Small Page', 'One line of the two tracks', 'tracks.line', [
        '{set:couple}, dated {today}. Line: {col:tracks.line}.',
        'One big wedding: {col:tracks.big}. Small ceremony plus a party: {col:tracks.small}. Difference: {col:tracks.difference}. Share kept in the small track: {col:tracks.share}.',
        'The small track uses your own estimates from Track Inputs. It is a way to compare, not a promise of a saving.'], ['The couple'], NOTE),
    DOC('honey_budget_page', 'Honeymoon Budget Page', 'Honeymoon budget of one item and its option', 'hm.hm_id', [
        '{set:couple}, dated {today}. Honeymoon item {col:hm.hm_id}: {col:hm.description}, {col:hm.option}.',
        'Amount {col:hm.amount} for {col:hm.days} days, due on {col:hm.due_date}. The option costs {col:hm.option_total} in all. Funds received and promised: {col:hm.funds}. Gap: {col:hm.gap}.',
        'To close the gap by the first booking date you would save {col:hm.monthly_need} a month on top of your plan.'], ['The couple'], NOTE),
    DOC('honey_options_page', 'Honeymoon Options Page', 'Honeymoon options side by side for one kind of cost', 'hcomp.kind', [
        '{set:couple}, dated {today}. Honeymoon cost kind: {col:hcomp.kind}.',
        'Option A: beach week: {col:hcomp.option_a}. Option B: city minimoon: {col:hcomp.option_b}.',
        'Use this page when you talk to a travel contact about one kind of cost.'], ['The couple'], NOTE),
    DOC('honey_dates_page', 'Honeymoon Booking Dates', 'Booking date of one honeymoon item', 'htime.hm_id', [
        '{set:couple}, dated {today}. Honeymoon booking date for {col:htime.item}.',
        'Due date: {col:htime.due_date}. Days left: {col:htime.days_left}. Flag: {col:htime.flag}.',
        'Check the cancellation terms of each booking in your contract.'], ['The couple', 'Travel contact'], NOTE),
    DOC('invitation_note', 'Event Invitation Note', 'Invitation note for one event', 'lines.line_id', [
        'Dear guest,',
        '{col:lines.couple} would love you to join the {col:lines.event} on {col:lines.date}, at {col:lines.start}. We will send the place and any details nearer the day.',
        'Please tell us by message or phone if you can come, and any short dietary note. We hope to see you there.'], ['The couple'], "Sample wording: adapt it to your own event and your own guests."),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('plan_event', 'Plan an event', 'events', 'events.date', [('Decide the guests and the host', -60), ('Set the budget and the lines', -50), ('Book the place or the host', -45), ('Send the invitations', -30), ('Collect the replies', -14),
                                                                     ('Confirm the numbers with the place', -7), ('Run the event', 0), ('Thank the host and the helpers', 3)]),
    CHK('hosts', 'Shower and weekend hosts', 'events', 'events.date', [('Agree who hosts and what you cover', -50), ('Ask the host for the guest list', -30), ('Check the cost against the line', -21), ('Confirm the date with the guests', -14), ('Thank the hosts', 3)]),
    CHK('rehearsal', 'Rehearsal dinner', 'events', 'events.date', [('Book the place and pay the deposit', -90), ('Make the guest list', -45), ('Ask for short dietary notes', -21), ('Confirm the numbers with the place', -7), ('Pay the balance', -1), ('Hand out thank-you gifts for helpers', 0)]),
    CHK('brunch', 'Farewell brunch', 'events', 'events.date', [('Choose the place and ask for a quote', -60), ('Invite the guests staying on', -30), ('Collect the replies', -14), ('Confirm the numbers', -5), ('Pay the balance', 0), ('Say goodbye to the guests', 0)]),
    CHK('cultural', 'Optional cultural events', 'events', 'events.date', [('Decide which events you want, if any', -120), ('Name each event and add it to Events', -100), ('Ask the family who will host', -80), ('Add the cost lines', -60), ('Send the invitations', -30), ('Hide or delete an event you drop', -20)]),
    CHK('destination', 'Destination wedding planning', 'events', 'events.date', [('Set the exchange rate in Settings', -300), ('Collect local quotes', -270), ('Check the lead time of your local marriage paperwork with your officiant or local office', -240), ('Send the save-the-dates early', -200),
                                                                              ('Book the room block', -180), ('Ask guests who travel to reply early', -90), ('Check the exchange rate again', -30)]),
    CHK('party_travel', 'Travel and stay for the party', 'events', 'events.date', [('Decide what you cover for each person', -150), ('Ask for flight details', -60), ('Book the rooms', -45), ('Send the travel page to each person', -30), ('Check the arrival times', -7)]),
    CHK('paper_lead', 'Local paperwork lead time', 'paper', 'paper.due_date', [('Ask your officiant or local office about the lead time', -120), ('Put the lead time into Settings', -110), ('Gather the documents', -60), ('Book the appointment', -45), ('Complete the steps', 0), ('Keep a copy of the record', 5)]),
    CHK('small_plus_party', 'Small ceremony plus a party', 'events', 'events.date', [('Fill in Track Inputs with your own numbers', -120), ('Compare the two tracks on the Big or Small Wedding tool', -110), ('Pick the track together', -100), ('Book the small place', -80), ('Invite the ceremony guests', -45), ('Plan the party for later', 30)]),
    CHK('honey_plan', 'Honeymoon planning', 'hm', 'hm.due_date', [('Pick the two options', -150), ('Fill in the cost lines', -140), ('Check the funds against each option', -120), ('Choose your option in Settings', -100), ('Plan the savings a month', -90)]),
    CHK('honey_book', 'Honeymoon booking', 'hm', 'hm.due_date', [('Ask for the quote', -45), ('Check the cancellation terms in the contract', -30), ('Book and mark the item Booked', -14), ('Pay on the due date', 0), ('Keep the booking dates together', 0)]),
    CHK('small_one_event', 'Small wedding one-event plan', 'events', 'events.date', [('Keep one row in Events', -90), ('Add the cost lines', -80), ('Set the invitees', -60), ('Book the place', -45), ('Confirm the numbers', -7), ('Enjoy the day', 0)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
M = MSG
messages = [
    M('m_host_date', 'Host: the date and the guests', 'lines', 'lines.host_phone', 'Hello, the {event} is on {date}. Here are the {invitees} guests we have invited. {couple}'),
    M('m_host_budget', 'Host: the budget and the plan', 'lines', 'lines.host_phone', 'Hello, the budget for the {event} is {event_budget}. What is the plan? {couple}'),
    M('m_host_list', 'Host: please send the guest list', 'lines', 'lines.host_phone', 'Hello, please send the guest list for the {event} by {list_by}. The date is {date}. {couple}'),
    M('m_host_cost', 'Host: the cost and what we cover', 'lines', 'lines.host_phone', 'Hello, the {event} costs {event_cost}. We cover {couple_covers}. {couple}'),
    M('m_par1_cost', 'Parent of partner 1: the cost, thank you', 'lines', 'lines.parent1_phone', 'Hello, the {event} cost {event_cost}. Thank you for your help. {couple}'),
    M('m_par2_plan', 'Parent of partner 2: confirm the plan', 'lines', 'lines.parent2_phone', 'Hello, the plan for the {event} is {event_budget}. Please confirm it works for you. {couple}'),
    M('m_par_deposit', 'Parent: the deposit was paid', 'lines', 'lines.parent1_phone', 'Hello, the deposit of {paid} for the {event} was paid. {couple}'),
    M('m_partner_cost', 'Partner: event cost against budget', 'lines', 'lines.partner_phone', 'Hello, the {event} costs {event_cost} against a budget of {event_budget}. {couple}'),
    M('m_partner_line', 'Partner: the events line against plan', 'lines', 'lines.partner_phone', 'Hello, all the events cost {events_line_var} against the Other events line of the budget. {couple}'),
    M('m_venue_confirm', 'Event venue: confirm the guests', 'lines', 'lines.venue_phone', 'Hello, please confirm the {event} for {invitees} guests on {date}. {couple}'),
    M('m_venue_deposit', 'Event venue: confirm the deposit', 'lines', 'lines.venue_phone', 'Hello, please confirm the amount of {amount} for the {event}. {couple}'),
    M('m_brunch_quote', 'Brunch venue: send a quote', 'lines', 'lines.venue_phone', 'Hello, please send a quote for {invitees} guests on {date} for the {event}. {couple}'),
    M('m_party_travel', 'Wedding party: your travel and stay', 'party', 'party.phone', 'Hello {person}, your travel and stay come to {total}. We cover {helped}. {couple}'),
    M('m_party_flights', 'Wedding party: send flight details', 'party', 'party.phone', 'Hello {person}, please send your flight details by {flight_by}. {couple}'),
    M('m_lead_join', 'Wedding party lead: who is joining', 'party', 'party.phone', 'Hello {person}, the {event} is on {event_date}. Who is joining? {couple}'),
    M('m_weekend_save', 'Weekend away guest: save the date', 'party', 'party.phone', 'Hello {person}, save the date for the {event}: {event_date}. Details to follow. {couple}'),
    M('m_weekend_confirm', 'Weekend away guest: please confirm', 'party', 'party.phone', 'Hello {person}, please confirm you can come to the {event} on {event_date}. {couple}'),
    M('m_weekend_share', 'Weekend away guest: your share', 'party', 'party.phone', 'Hello {person}, your share for the {event} is {event_share}. Please confirm. {couple}'),
    M('m_event_invite', 'Event guest: you are invited', 'party', 'party.phone', 'Hello {person}, you are invited to the rehearsal dinner on {rehearsal_date}. {couple}'),
    M('m_event_reply', 'Event guest: please reply', 'party', 'party.phone', 'Hello {person}, please reply by {reply_by} for the rehearsal dinner on {rehearsal_date}. {couple}'),
    M('m_event_arrive', 'Event guest: when to arrive', 'party', 'party.phone', 'Hello {person}, please arrive a little before {rehearsal_start} on {rehearsal_date}. {couple}'),
    M('m_rehearsal_time', 'Rehearsal dinner guest: the time', 'party', 'party.phone', 'Hello {person}, the rehearsal dinner is at {rehearsal_start} on {rehearsal_date}. {couple}'),
    M('m_rehearsal_diet', 'Rehearsal dinner guest: dietary note', 'party', 'party.phone', 'Hello {person}, please tell us about any short dietary note for the rehearsal dinner on {rehearsal_date}. {couple}'),
    M('m_brunch_time', 'Brunch guest: the time', 'party', 'party.phone', 'Hello {person}, the farewell brunch is at {brunch_start} on {brunch_date}. {couple}'),
    M('m_brunch_coming', 'Brunch guest: are you coming', 'party', 'party.phone', 'Hello {person}, please let us know if you are coming to the farewell brunch on {brunch_date}. {couple}'),
    M('m_hotel_rooms', 'Hotel contact: rooms for the party', 'party', 'party.hotel_phone', 'Hello, we need {party_rooms} rooms for up to {party_nights} nights for the wedding party. {couple}'),
    M('m_partner_dest', 'Partner: the destination adds', 'dest', 'dest.partner_phone', 'Hello, a destination wedding adds {dest_add}. Shall we compare it with a local wedding? {couple}'),
    M('m_partner_rate', 'Partner: the exchange rate moved', 'dest', 'dest.partner_phone', 'Hello, the exchange rate moved. The local quotes are now {local_total} in local money. {couple}'),
    M('m_partner_paper', 'Partner: the paperwork lead time', 'paper', 'paper.partner_phone', 'Hello, the lead time for our paperwork is {lead_days} days. Please start {item} by {start_by}. {couple}'),
    M('m_partner_tracks', 'Partner: big wedding or small plus party', 'tracks', 'tracks.partner_phone', 'Hello, for {line} one big wedding costs {big} and a small ceremony plus a party costs {small}. {couple}'),
    M('m_partner_honey', 'Partner: the honeymoon gap', 'hm', 'hm.partner_phone', 'Hello, {option} costs {option_total} and our honeymoon funds are {funds}, a gap of {gap}. {couple}'),
    M('m_partner_save', 'Partner: honeymoon savings', 'hm', 'hm.partner_phone', 'Hello, our honeymoon funds are {funds} and {option} needs {option_total}. We would need to save {monthly_need} more a month. {couple}'),
    M('m_travel_quote', 'Travel contact: send the honeymoon quote', 'hm', 'hm.phone', 'Hello, please send the honeymoon quote for {days} days: {description}. {couple}'),
]
messages.append(M('m_honey_dates', 'Honeymoon host: confirm the dates', 'hm', 'hm.phone', 'Hello, please confirm the booking dates for {description}. We plan to pay on {due_date}. {couple}'))
assert len(messages) == 34

# ------------------------------------------------------------------ dashboard
D_ = R('events', 'date')
CH_FIRST = '(100000-SUMPRODUCT(MAX((%s=%s)*(%s>0)*(100000-%s))))' % (R('hm', 'option'), CHOSEN, R('hm', 'due_date'), R('hm', 'due_date'))
CH_GAP = 'MAX(0,%s-%s)' % (OPT(CHOSEN), FUNDS)
kpis = [
    KPI('Events planned', 'COUNTIFS(%s,%s)' % (R('events', 'status'), PLAN), 'int'),
    KPI('Events done', 'COUNTIFS(%s,%s)' % (R('events', 'status'), DONE), 'int'),
    KPI('Next event in days', 'SMALL(%s,COUNTIFS(%s,"<"&{today})+1)-{today}' % (D_, D_), 'int'),
    KPI('Events cost total', TOTAL, 'money'),
    KPI('Events budget total', 'SUM(%s)' % R('lines', 'planned'), 'money'),
    KPI('Events over their budget', OVER5, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Event cost per guest on your list', 'IFERROR(ROUND(%s/{set:guest_list},2),0)' % TOTAL, 'num'),
    KPI('Largest event cost', 'MAX(%s)' % R('ecosts', 'cost'), 'money'),
    KPI('Invitees across events', 'SUM(%s)' % R('invitees', 'invitees'), 'int'),
    KPI('Guests invited to the rehearsal dinner', 'SUMIFS(%s,%s,%s)' % (R('invitees', 'invitees'), R('invitees', 'event'), tok('event', 'Rehearsal dinner')), 'int'),
    KPI('Guests invited to the brunch', 'SUMIFS(%s,%s,%s)' % (R('invitees', 'invitees'), R('invitees', 'event'), tok('event', 'Farewell brunch')), 'int'),
    KPI('Guest-nights', 'SUM(%s)' % R('nights', 'guests'), 'int'),
    KPI('Rooms needed at the busiest night', 'MAX(%s)' % R('nights', 'rooms'), 'int'),
    KPI('Destination add-on cost', '{set:couple_flights}+{set:couple_nights}*{set:room_rate}+SUM(%s)' % R('party', 'helped'), 'money'),
    KPI('Local quotes total at the rate', 'SUM(%s)' % R('dest', 'local_amount'), 'money'),
    KPI('Exchange rate used', '{set:exchange_rate}', 'num'),
    KPI('Expected declines from travel guests', 'ROUND({set:travel_guests}*{set:travel_decline_extra},0)', 'int'),
    KPI('Party travel cost', 'SUM(%s)' % R('party', 'total'), 'money'),
    KPI('Couple covers for party travel', 'SUM(%s)' % R('party', 'helped'), 'money'),
    KPI('Days to the paperwork start date', 'IFERROR(SMALL(%s,1)-{today},"")' % R('paper', 'start_by'), 'int', alert={"when": "< 30", "style": "warn"}),
    KPI('One big wedding total', 'SUM(%s)' % R('tracks', 'big'), 'money'),
    KPI('Small ceremony plus party total', 'SUM(%s)' % R('tracks', 'small'), 'money'),
    KPI('Difference between the tracks', 'SUM(%s)-SUM(%s)' % (R('tracks', 'small'), R('tracks', 'big')), 'money'),
    KPI('Honeymoon option A total', OPT(OA), 'money'),
    KPI('Honeymoon option B total', OPT(OB), 'money'),
    KPI('Honeymoon funds received', 'SUMIFS(%s,%s,%s)' % (R('hf', 'amount'), R('hf', 'status'), RECV), 'money'),
    KPI('Honeymoon funds promised', 'SUMIFS(%s,%s,%s)' % (R('hf', 'amount'), R('hf', 'status'), PROM), 'money'),
    KPI('Honeymoon gap for your chosen option', CH_GAP, 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Next honeymoon booking date in days', 'SMALL(%s,COUNTIFS(%s,"<"&{today})+1)-{today}' % (R('hm', 'due_date'), R('hm', 'due_date')), 'int'),
    KPI('Honeymoon extra saving a month needed', 'ROUND(%s/MAX(1,(%s-{today})/30.4),0)' % (CH_GAP, CH_FIRST), 'money'),
]
assert len(kpis) == 30
dashboard = {"title": "Events and Honeymoon Dashboard", "kpis": kpis,
    "monthly": {"title": "Event cost and honeymoon savings by month", "date": "ecal.month", "series": [
        {"label": "Event cost", "sum": "ecal.cost", "date": "ecal.month"}, {"label": "Honeymoon savings", "sum": "hfm.savings", "date": "hfm.month"}]},
    "breakdowns": [{"title": "Event cost by event", "by": "lines.event", "value": "lines.amount", "agg": "sum"}, {"title": "Honeymoon fund by source", "by": "hf.source", "value": "hf.amount", "agg": "sum"},
                   {"title": "Party travel by role", "by": "party.role", "value": "party.total", "agg": "sum"}, {"title": "Honeymoon fund by status", "by": "hf.status", "value": "hf.amount", "agg": "sum"}]}


def AG(kind, table, value=None, date=None, label=None, where=None): return AGG(kind, table, value, date, where, label)
insights = {"filters": [{"label": "Event", "list": "event"}, {"label": "Honeymoon option", "list": "hoption"}, {"label": "Budget category", "list": "category"}],
    "gauges": [
        {"title": "Event lines within their budget", "num": AG('count', 'lines', where=[('variance', '<=', 0)]), "den": AG('count', 'lines', where=[('amount', '>=', 0)])},
        {"title": "Honeymoon funded for the chosen option", "num": AG('sum', 'hf', 'hf.amount', where=[('status', '<>', NOTC)]), "den": AG('sum', 'hm', 'hm.amount', where=[('option', '=', '{set:honeymoon_option}')])},
        {"title": "Honeymoon fund received against promised", "num": AG('sum', 'hf', 'hf.amount', where=[('status', '=', RECV)]), "den": AG('sum', 'hf', 'hf.amount', where=[('status', '<>', NOTC)])},
        {"title": "Paperwork steps done", "num": AG('count', 'paper', where=[('status', '=', tok('tstatus', 'Done'))]), "den": AG('count', 'paper', where=[('due_date', '>', 0)])},
        {"title": "Party travel covered by the couple", "num": AG('sum', 'party', 'party.helped'), "den": AG('sum', 'party', 'party.total')},
        {"title": "Small plus party against the big wedding", "num": AG('sum', 'tracks', 'tracks.small'), "den": AG('sum', 'tracks', 'tracks.big')}],
    "charts": [
        CHART('Event cost by event', 'bar', 'ecosts.event', [AG('sum', 'ecosts', 'ecosts.cost', label='Cost')]),
        CHART('Event budget against cost', 'bar', 'lines.event', [AG('sum', 'lines', 'lines.planned', label='Budget'), AG('sum', 'lines', 'lines.amount', label='Cost')]),
        CHART('Event invitees by event', 'bar', 'invitees.event', [AG('sum', 'invitees', 'invitees.invitees', label='Invitees')]),
        CHART('Cost per guest by event', 'bar', 'ecosts.event', [AG('sum', 'ecosts', 'ecosts.per_guest', label='Cost per invitee')]),
        CHART('Event lines by item', 'bar', 'lines.item', [AG('sum', 'lines', 'lines.amount', label='Amount')]),
        CHART('Events by status', 'bar', 'events.status', [AG('count', 'events', label='Events')]),
        CHART('Event cost by month', 'column', 'month', [AG('sum', 'ecal', 'ecal.cost', date='ecal.month', label='Event cost')]),
        CHART('Event lines paid and unpaid', 'bar', 'lines.event', [AG('sum', 'lines', 'lines.paid', label='Paid'), AG('sum', 'lines', 'lines.balance', label='Still to pay')]),
        CHART('Guest-nights by night', 'bar', 'nights.night', [AG('sum', 'nights', 'nights.guests', label='Guests staying')]),
        CHART('Honeymoon amount by kind and option', 'bar', 'hcomp.kind', [AG('sum', 'hcomp', 'hcomp.option_a', label='Option A'), AG('sum', 'hcomp', 'hcomp.option_b', label='Option B')]),
        CHART('Honeymoon option A against B', 'bar', 'hm.option', [AG('sum', 'hm', 'hm.amount', label='Total')]),
        CHART('Honeymoon items by status', 'bar', 'hm.status', [AG('count', 'hm', label='Items')]),
        CHART('Honeymoon running total by month', 'column', 'month', [AG('sum', 'hfm', 'hfm.closing', date='hfm.month', label='Received and promised')]),
        CHART('Honeymoon fund by month', 'column', 'month', [AG('sum', 'hfm', 'hfm.savings', date='hfm.month', label='Savings'), AG('sum', 'hfm', 'hfm.cash_gifts', date='hfm.month', label='Cash gifts')]),
        CHART('Honeymoon fund by source', 'bar', 'hf.source', [AG('sum', 'hf', 'hf.amount', label='Amount')]),
        CHART('Honeymoon fund by status', 'bar', 'hf.status', [AG('sum', 'hf', 'hf.amount', label='Amount')]),
        CHART('Party travel by role', 'bar', 'party.role', [AG('sum', 'party', 'party.total', label='Travel and stay')]),
        CHART('Party travel by person', 'bar', 'party.person', [AG('sum', 'party', 'party.total', label='Travel and stay'), AG('sum', 'party', 'party.helped', label='Couple covers')]),
        CHART('Destination quotes by category', 'bar', 'dest.category', [AG('sum', 'dest', 'dest.difference', label='Difference')]),
        CHART('Local amount against base price by category', 'bar', 'dest.category', [AG('sum', 'dest', 'dest.base_price', label='Base price'), AG('sum', 'dest', 'dest.local_amount', label='Local amount')]),
        CHART('Two-track cost by line', 'bar', 'tracks.line', [AG('sum', 'tracks', 'tracks.big', label='One big wedding'), AG('sum', 'tracks', 'tracks.small', label='Small plus party')]),
        CHART('Honeymoon scenarios by total', 'bar', 'hscen.scenario', [AG('sum', 'hscen', 'hscen.total', label='Total')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Multi-event cost planner", "why": "every event with its cost, paid, still to pay and cost per invitee, so the shower, the weekends away and the dinners add up in one place", "where": "Event Cost Planner"},
    {"name": "Event invitee check", "why": "each event's invitees tested as a part of your guest list, with the overlap between two events", "where": "Event Invitee Check"},
    {"name": "Guest-nights counter", "why": "guests staying each night from their arrival days, with the rooms at the busiest night against the rooms you hold", "where": "Guest-nights Counter"},
    {"name": "Destination cost total", "why": "your own travel, the party travel you cover and the local quotes at your exchange rate in one verdict", "where": "Destination Cost Total"},
    {"name": "Exchange rate sensitivity", "why": "the local quotes priced back into your currency with the rate moved down and up, so you see the range", "where": "Exchange Rate Sensitivity"},
    {"name": "Travel decline uplift", "why": "extra declines for guests who travel, your expected headcount and the number to give the caterer, as your estimate", "where": "Travel Decline Uplift"},
    {"name": "Big wedding against small ceremony plus party", "why": "both tracks totalled line by line from your own budget, with cost per guest and a verdict on the difference", "where": "Big or Small Wedding"},
    {"name": "Honeymoon two options side by side", "why": "the beach week and the city minimoon with total, cost per day and the gap against the money received and promised", "where": "Honeymoon Two Options"},
    {"name": "Minimoon fallback", "why": "the days of the dear option your money can pay for once the fixed costs are kept", "where": "Minimoon Fallback"},
    {"name": "Honeymoon savings pace", "why": "the extra saving a month that closes the gap by the first booking date, solved from your own funds", "where": "Honeymoon Savings Pace"}]
competitors = [
    {"what": "a free planning app", "lacks": "has an event list but no cost per guest across events, no guest-nights, no destination exchange rate and no honeymoon funds against two options"},
    {"what": "a single budget spreadsheet", "lacks": "has one budget column but no events planner, no two-track comparison of a big wedding against a small ceremony plus a party, and no honeymoon verdict"},
    {"what": "a printable wedding binder", "lacks": "has blank pages for events and travel but does no sums, no clash check, no exchange rate sensitivity and no savings pace"},
    {"what": "a wedding website with a registry", "lacks": "shares your plans with a company and has no event costs, no paperwork lead-time check and no private honeymoon budget"}]
guide = [
    'Open Start here and type your names, the wedding day, the guests on your list and your room rate in the yellow cells. Replace demo data: clear the sample rows and type your own.',
    'Fill Events with each event and its date, then Event Invitees with the start time and how many guests are invited. Rename, add or delete rows: an optional event such as a welcome dinner or a tea ceremony is just a new row.',
    'Add the cost of each event in Event Lines (planned, amount, paid). Event Costs, the Event Calendar and the dashboard fill in by themselves.',
    'Use Guest-nights for the guests staying each night around the wedding; the rooms needed follow from the guests sharing a room.',
    'For a destination wedding set your exchange rate, then pick the quotes in Destination Quotes and the travel of each person in Party Travel. The local amount and the cost to the couple fill in.',
    'In Paperwork Rows type the lead time of your local marriage paperwork. Check it with your officiant or local office; the start-by date and the flag follow.',
    'Fill Track Inputs with your own numbers to compare one big wedding with a small ceremony plus a party. The lines come from your budget.',
    'Enter the honeymoon costs for two options in Honeymoon Items and the money you set aside in Honeymoon Fund. Only received and promised money counts, never a cash gift that is not confirmed. Pick your option in Settings.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A couple with a small wedding (30 guests, no wedding party) uses the same sheets with fewer rows: keep one event, leave Party Travel empty and skip the destination sheets.',
    'This workbook has no macros and works in Excel and Google Sheets. Print any page for a parent or a helper.',
    'Why a workbook: one flat price, no vendor ever sees your details, no fees on your gifts, your own numbers, and it works offline.',
    'What this is not: not a booking service, not a payment service, and not legal, tax or insurance advice. Every default is a typical starting value you can edit, never a promise.']
listing = {"title": "Wedding Events, Travel and Honeymoon Planner Excel Template: Shower, Rehearsal Dinner, Destination Wedding, Honeymoon Budget",
    "headline": "Plan every event, the travel and the honeymoon around your wedding",
    "tags": ["wedding planner", "honeymoon budget", "wedding events", "rehearsal dinner", "destination wedding", "shower planner", "wedding budget", "excel template", "wedding travel", "wedding checklist", "minimoon", "wedding party", "wedding spreadsheet"],
    "description": ("Plan the events around your wedding day in one Excel workbook. Built for an engaged couple planning their own wedding, with a parent, a host or a wedding party lead helping. "
        "Events holds the engagement party, the shower, the weekends away, the rehearsal dinner, the ceremony, the reception and the farewell brunch, with a date, a start time and the invitees as a part of your guest list. Event Lines adds the cost of each event against its budget, and Event Costs, the Event Calendar and a cost per invitee fill in by themselves.\n\n"
        "Guest-nights counts the guests staying each night and the rooms they need. The destination sheets hold your own travel, the travel and stay of each person in the wedding party, the quotes in local money at an exchange rate you edit, and the lead time of your local marriage paperwork. "
        "Two-track Comparison sets one big wedding against a small ceremony plus a later party, line by line, from your own budget.\n\n"
        "The honeymoon sheets hold two options side by side, the money you set aside month by month, a timeline of booking dates and six what-if scenarios with a verdict against the money received and promised.\n\n"
        f"{len(tools)} tools answer weekly questions: what the events cost, whether the invitees fit the list, whether two events clash, what a destination adds, what happens if the exchange rate moves, which honeymoon option you can afford and how much to save a month. Print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and send {len(messages)} ready text messages to hosts, parents, the wedding party and your vendors.\n\n"
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Guests appear as names only. Every default is a typical starting value you can edit, and forecasts are your own estimate. It is not a booking service, not a payment service and not legal, tax or insurance advice. This is part seven of the Wedding Planning suite."),
    "features": ["Eight events with cost, paid and cost per invitee", "Invitees checked against your guest list", "Guest-nights and rooms at the busiest night", "Destination quotes at an exchange rate you edit", "Exchange rate sensitivity",
                 "Paperwork lead-time check", "One big wedding against a small ceremony plus a party", "Two honeymoon options side by side", "Honeymoon savings pace", f"{len(tools)} decision tools",
                 f"{len(forms)} printable sheets and {len(documents)} pages", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}

lists = BASE_LISTS + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p7', slug='wedding-events', profession='Wedding Planning', name='Events, Travel and Honeymoon',
         tagline='Plan the events, travel and honeymoon around your wedding in one workbook', price_usd=29,
         colors={"primary": "#7A4B68", "accent": "#D9A86C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Events, travel and honeymoon"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wp7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']))
