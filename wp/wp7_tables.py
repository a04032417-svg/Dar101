"""Wedding suite part 7: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp7_lists import *
import wp7_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def LIT(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
def CPL(): return CA('couple', 'Couple', 'text', '{set:couple}', 20)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
DONE = tok('estatus', 'Done'); PLAN = tok('estatus', 'Planned')
OA = tok('hoption', 'Option A: beach week'); OB = tok('hoption', 'Option B: city minimoon')
RECV = tok('fstatus', 'Received'); PROM = tok('fstatus', 'Promised'); NOTC = tok('fstatus', 'Not confirmed')
SAV = tok('hsource', 'Savings'); CASH = tok('hsource', 'Cash gifts')
CHOSEN = '{set:honeymoon_option}'
OTHER_EV = tok('category', 'Other events')
RESERVE = tok('hkind', 'Reserve'); STAY = tok('hkind', 'Stay'); DAILY = tok('hkind', 'Daily spend'); ACTIV = tok('hkind', 'Activities')
MARRIAGE = tok('pkind', 'Marriage paperwork')
YES = '{list:yesno.yes}'
FUNDS = '(SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s))' % (R('hf', 'amount'), R('hf', 'status'), RECV, R('hf', 'amount'), R('hf', 'status'), PROM)
def OPT(o): return 'SUMIFS(%s,%s,%s)' % (R('hm', 'amount'), R('hm', 'option'), o)
def OPTK(o, k_): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('hm', 'amount'), R('hm', 'option'), o, R('hm', 'kind'), k_)
def TIN(label): return 'SUMIFS(%s,%s,%s)' % (R('tin', 'value'), R('tin', 'item'), tok('tinput', label))
def TD(t, label): return 'INDEX(%s,MATCH(%s,%s,0))' % (R(t, 'date'), tok('event', label), R(t, 'event'))

settings = [
    S('couple', 'Your names as the couple', 'text', COUPLE),
    S('wedding_day', 'Wedding day', 'date', iso(WEDDING_DAY)),
    S('headcount', 'Headcount for costing: your forecast from the guest list', 'int', 118),
    S('expected_yes_rate', 'Expected yes rate of pending replies, typical, edit', 'pct', EXPECTED_YES_RATE),
    S('travel_guests', 'Guests who travel to the wedding, your count', 'int', D.TRAVEL_GUESTS),
    S('travel_decline_extra', 'Extra decline rate for guests who travel, typical, edit', 'pct', TRAVEL_DECLINE_EXTRA),
    S('guest_list', 'Guests on your invitation list', 'int', GUESTS_INVITED),
    S('exchange_rate', 'Exchange rate: local amount per unit of your currency, edit', 'num', 1.18),
    S('room_rate', 'Room rate for one night, your own number', 'money', 139),
    S('guests_per_room', 'Guests sharing one room, typical, edit', 'int', 2),
    S('couple_flights', 'Your own travel for a destination wedding, flights for two', 'money', 920),
    S('couple_nights', 'Your own nights away for a destination wedding', 'int', 4),
    S('paperwork_lead_days', 'Lead time of your local marriage paperwork, days, your own', 'int', 45),
    S('clash_days', 'Days apart that count as a clash between two events', 'int', 6),
    S('couple_cover_pct', 'Share of a hosted event the couple covers, your own number', 'pct', 0.5),
    S('host_list_days', 'Days before an event a host sends the guest list', 'int', 30),
    S('reply_days', 'Days before an event guests reply by', 'int', 21),
    S('flight_days', 'Days before the wedding the party sends flight details', 'int', 60),
    S('honeymoon_option', 'Honeymoon option you plan, your choice', 'list', key('hoption', 'Option A: beach week'), list='hoption'),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 events ------------------------------------------------------------------
tables.append(T('events', 'Events', 'Events', 'One row per event of the wedding weekends and the parties around them: name, date and status. Rename, add or delete rows for your own events.', [
    LST('event', 'Event', 'event', 32, required=True), C('date', 'Date', 'date', 11), LST('status', 'Status', 'estatus', 10)],
    D.events_d(), 50, [A('status', '= ' + DONE, 'good')]))

# 2 event lines -------------------------------------------------------------
HOSTPH = '""'
for _e in reversed(EVENT_NAMES): HOSTPH = 'IF({col:event}=%s,"%s",%s)' % (tok('event', _e), D.HOST_PHONE[_e], HOSTPH)
tables.append(T('lines', 'Event Lines', 'Event Lines', 'One row per cost line of an event: planned, amount and paid; balance, variance, date, start and invitees, the event totals and the host phone fill in.', [
    C('line_id', 'Line ID', 'text', 9, required=True), C('event_id', 'Event ID', 'text', 9), LST('event', 'Event', 'event', 32), LST('item', 'Item', 'item', 30), C('planned', 'Planned', 'money', 11),
    C('amount', 'Amount', 'money', 11), C('paid', 'Paid', 'int', 9),
    CA('balance', 'Still to pay', 'money', '{col:amount}-{col:paid}', 11), CA('variance', 'Over or under plan', 'money', '{col:amount}-{col:planned}', 12),
    CA('date', 'Event date', 'date', LKD('events.date', 'events.event', 'event'), 11), CA('status', 'Event status', 'text', LKT('events.status', 'events.event', 'event'), 11),
    CA('start', 'Start', 'text', LKT('invitees.start', 'invitees.event', 'event'), 9), CA('invitees', 'Invitees', 'int', LKN('invitees.invitees', 'invitees.event', 'event'), 9),
    CA('event_cost', 'Event cost', 'money', 'SUMIFS({range:lines.amount},{range:lines.event},{col:event})', 11), CA('event_budget', 'Event budget', 'money', 'SUMIFS({range:lines.planned},{range:lines.event},{col:event})', 11),
    CA('event_paid', 'Event paid', 'money', 'SUMIFS({range:lines.paid},{range:lines.event},{col:event})', 11),
    CA('couple_covers', 'Couple covers', 'money', 'ROUND({col:event_cost}*{set:couple_cover_pct},0)', 11), CA('list_by', 'Host sends the list by', 'date', 'IF({col:date}="","",{col:date}-{set:host_list_days})', 12),
    CA('events_line_var', 'Events cost less the Other events line', 'money', 'SUM({range:lines.amount})-SUMIFS({range:budget.planned},{range:budget.category},%s)' % OTHER_EV, 12),
    CA('host_phone', 'Host phone', 'text', HOSTPH, 18), LIT('venue_phone', 'Venue phone', D.VENUE_PHONE), LIT('partner_phone', 'Partner phone', D.P2_PHONE),
    LIT('parent1_phone', 'Parent of partner 1 phone', D.PAR1_PHONE), LIT('parent2_phone', 'Parent of partner 2 phone', D.PAR2_PHONE), CPL()],
    D.lines_d(), 100, [A('variance', '> 0', 'warn'), A('balance', '> 0', 'warn')]))

# 3 event costs -------------------------------------------------------------
tables.append(T('ecosts', 'Event Costs', 'Event Costs', 'One row per event: its cost from the lines and the cost per invitee; both fill in by themselves.', [
    LST('event', 'Event', 'event', 32, required=True), CA('cost', 'Cost', 'money', 'SUMIFS({range:lines.amount},{range:lines.event},{col:event})', 12),
    CA('per_guest', 'Cost per invitee', 'money', 'IFERROR(ROUND({col:cost}/INDEX({range:invitees.invitees},MATCH({col:event},{range:invitees.event},0)),2),0)', 12)],
    D.ecosts_d(), 50))

# 4 invitees ----------------------------------------------------------------
tables.append(T('invitees', 'Event Invitees', 'Event Invitees', 'One row per event: its start time and how many guests are invited, as a part of your guest list.', [
    LST('event', 'Event', 'event', 32, required=True), C('start', 'Start', 'text', 9), C('invitees', 'Invitees', 'int', 10)], D.invitees_d(), 50))

# 5 event calendar ----------------------------------------------------------
tables.append(T('ecal', 'Event Calendar', 'Event Calendar', 'One row per month: how many events fall in it, what they cost and how many invitees they hold, from Events and Event Lines.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('events', 'Events', 'int', 'COUNTIFS({range:events.date},">="&{col:month},{range:events.date},"<"&EDATE({col:month},1))', 9),
    CA('cost', 'Cost', 'money', 'SUMIFS({range:lines.amount},{range:lines.date},">="&{col:month},{range:lines.date},"<"&EDATE({col:month},1))', 11),
    CA('invitees', 'Invitees', 'int', 'SUMPRODUCT(({range:events.date}>={col:month})*({range:events.date}<EDATE({col:month},1))*SUMIFS({range:invitees.invitees},{range:invitees.event},{range:events.event}))', 10),
    CA('flag', 'Busy month', 'text', 'IF({col:events}>=3,%s,IF({col:events}>0,%s,%s))' % (v('Busy'), v('Events'), v('Quiet')), 10)],
    D.calendar_d(), 50, [A('flag', '= ' + v('Busy'), 'warn')]))

# 6 guest-nights ------------------------------------------------------------
tables.append(T('nights', 'Guest-nights', 'Guest-nights', 'One row per night around the wedding: guests staying that night from your households and the rooms they need.', [
    LST('night', 'Night', 'night', 20, required=True), C('guests', 'Guests staying', 'int', 12), CA('rooms', 'Rooms needed', 'int', 'ROUNDUP({col:guests}/{set:guests_per_room},0)', 12)], D.nights_d(), 50))

# 7 combined cost -----------------------------------------------------------
CAMT = ('IF({col:item}=%s,SUMIFS({range:lines.amount},{range:lines.status},%s),IF({col:item}=%s,SUMIFS({range:lines.amount},{range:lines.status},%s),IF({col:item}=%s,SUM({range:party.helped}),'
        'IF({col:item}=%s,{set:couple_flights}+{set:couple_nights}*{set:room_rate},IF({col:item}=%s,%s-%s,IF({col:item}=%s,%s,0))))))') % (
    tok('citem', 'Events done'), DONE, tok('citem', 'Events planned'), PLAN, tok('citem', 'Party travel the couple covers'), tok('citem', 'Couple travel and stay'),
    tok('citem', 'Honeymoon trip, chosen option'), OPT(CHOSEN), OPTK(CHOSEN, RESERVE), tok('citem', 'Honeymoon reserve, chosen option'), OPTK(CHOSEN, RESERVE))
tables.append(T('comb', 'Combined Cost', 'Combined Cost', 'The six cost blocks around the wedding day added together: events, party travel, your own travel and the honeymoon, with each share of the total.', [
    LST('item', 'Item', 'citem', 34, required=True), CA('amount', 'Amount', 'money', CAMT, 12), CA('share', 'Share', 'pct', 'IF(SUM({range:comb.amount})>0,{col:amount}/SUM({range:comb.amount}),0)', 9)], D.combined_d(), 50))

# 8 honeymoon items ---------------------------------------------------------
tables.append(T('hm', 'Honeymoon Items', 'Honeymoon Items', 'One row per honeymoon cost for each of the two options: kind, amount, days, due date and status; the option total, funds, gap and the monthly saving fill in.', [
    C('hm_id', 'Item ID', 'text', 9, required=True), LST('option', 'Option', 'hoption', 24), LST('kind', 'Kind', 'hkind', 15), C('description', 'Description', 'text', 30), C('amount', 'Amount', 'money', 11),
    C('days', 'Days', 'int', 7), C('due_date', 'Due date', 'date', 11), C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'hmstatus', 15), C('phone', 'Contact phone', 'text', 18),
    CA('option_total', 'Option total', 'money', OPT('{col:option}'), 12), CA('funds', 'Funds received and promised', 'money', FUNDS, 12), CA('gap', 'Gap for this option', 'money', 'MAX(0,{col:option_total}-{col:funds})', 12),
    CA('first_due', 'First booking date of the option', 'date', '100000-SUMPRODUCT(MAX(({range:hm.option}={col:option})*({range:hm.due_date}>0)*(100000-{range:hm.due_date})))', 12),
    CA('monthly_need', 'Saving a month to close the gap', 'money', 'ROUND({col:gap}/MAX(1,({col:first_due}-{today})/30.4),0)', 12),
    LIT('partner_phone', 'Partner phone', D.P2_PHONE), CPL()],
    D.hm_d(), 60, [A('status', '= ' + tok('hmstatus', 'Booked'), 'good'), A('gap', '> 0', 'warn')]))

# 9 honeymoon fund ----------------------------------------------------------
tables.append(T('hf', 'Honeymoon Fund', 'Honeymoon Fund', 'One row per amount set aside for the honeymoon: date, month, source, amount and status. Only received and promised money counts; not confirmed cash gifts do not.', [
    C('hf_id', 'Fund ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('source', 'Source', 'hsource', 12), C('amount', 'Amount', 'int', 10),
    LST('status', 'Status', 'fstatus', 14)], D.hf_d(), 80, [A('status', '= ' + RECV, 'good'), A('status', '= ' + NOTC, 'warn')]))

# 10 honeymoon options compared ---------------------------------------------
tables.append(T('hcomp', 'Honeymoon Options', 'Honeymoon Options Compared', 'One row per kind of honeymoon cost: option A and option B side by side, from Honeymoon Items.', [
    LST('kind', 'Kind', 'hkind', 18, required=True), CA('option_a', 'Option A: beach week', 'money', OPTK(OA, '{col:kind}'), 14), CA('option_b', 'Option B: city minimoon', 'money', OPTK(OB, '{col:kind}'), 14)],
    D.hcomp_d(), 50))

# 11 honeymoon funds by month -----------------------------------------------
tables.append(T('hfm', 'Honeymoon by Month', 'Honeymoon Funds by Month', 'One row per month: savings, cash gifts, the running total of received and promised money and a flag against your chosen option.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('savings', 'Savings', 'money', 'SUMIFS({range:hf.amount},{range:hf.month},{col:month},{range:hf.source},%s,{range:hf.status},%s)+SUMIFS({range:hf.amount},{range:hf.month},{col:month},{range:hf.source},%s,{range:hf.status},%s)' % (SAV, RECV, SAV, PROM), 11),
    CA('cash_gifts', 'Cash gifts, any status', 'money', 'SUMIFS({range:hf.amount},{range:hf.month},{col:month},{range:hf.source},%s)' % CASH, 12),
    CA('closing', 'Running total, received and promised', 'money', 'SUMIFS({range:hf.amount},{range:hf.month},"<="&{col:month},{range:hf.status},%s)+SUMIFS({range:hf.amount},{range:hf.month},"<="&{col:month},{range:hf.status},%s)' % (RECV, PROM), 13),
    CA('flag', 'Against your option', 'text', 'IF({col:closing}>=%s,%s,IF({col:month}<=%s,%s,%s))' % (OPT(CHOSEN), v('Covered'), MS, v('Saved so far'), v('Planned')), 14)],
    D.hfm_d(), 50, [A('flag', '= ' + v('Covered'), 'good')]))

# 12 honeymoon timeline -----------------------------------------------------
tables.append(T('htime', 'Honeymoon Timeline', 'Honeymoon Timeline', 'One row per honeymoon item: its due date, the days left and a flag (paid, due soon, late or on time).', [
    REF('hm_id', 'Item ID', 'hm.hm_id', 9, required=True), CA('item', 'Item', 'text', LKT('hm.description', 'hm.hm_id', 'hm_id'), 30), CA('due_date', 'Due date', 'date', LKD('hm.due_date', 'hm.hm_id', 'hm_id'), 11),
    CA('days_left', 'Days left', 'int', 'IF({col:due_date}="","",{col:due_date}-{today})', 9),
    CA('flag', 'Flag', 'text', 'IF(IFERROR(INDEX({range:hm.paid_on},MATCH({col:hm_id},{range:hm.hm_id},0)),0)>0,%s,IF({col:due_date}="",%s,IF({col:days_left}<0,%s,IF({col:days_left}<=60,%s,%s))))' % (
        v('Paid'), v('No date'), v('Late'), v('Due soon'), v('On time')), 11)],
    D.htime_d(), 50, [A('flag', '= ' + v('Late'), 'bad'), A('flag', '= ' + v('Due soon'), 'warn'), A('flag', '= ' + v('Paid'), 'good')]))

# 13 quotes -----------------------------------------------------------------
tables.append(T('quotes', 'Quotes', 'Quotes', 'The vendor quotes you collected: vendor, category, option, base price and status. Destination Quotes picks from here.', [
    C('quote_id', 'Quote ID', 'text', 9, required=True), C('vendor_id', 'Vendor ID', 'text', 9), C('vendor', 'Vendor', 'text', 22), LST('category', 'Category', 'category', 24), C('option', 'Option', 'text', 10),
    C('base_price', 'Base price', 'money', 11), C('status', 'Status', 'text', 14), C('phone', 'Contact phone', 'text', 18)], D.quotes_d(), 120))

# 14 destination quotes -----------------------------------------------------
tables.append(T('dest', 'Destination Quotes', 'Destination Quotes', 'One row per vendor quote you may pay in local money: the base price, the local amount at your exchange rate and the difference.', [
    C('dest_id', 'Row ID', 'text', 9, required=True), REF('quote_id', 'Quote ID', 'quotes.quote_id', 9), REF('category', 'Category', 'budget.category', 24),
    CA('vendor', 'Vendor', 'text', LKT('quotes.vendor', 'quotes.quote_id', 'quote_id'), 20), CA('base_price', 'Base price', 'money', LKN('quotes.base_price', 'quotes.quote_id', 'quote_id'), 11),
    CA('local_amount', 'Local amount', 'money', 'ROUND({col:base_price}*{set:exchange_rate},0)', 12), CA('difference', 'Difference', 'money', '{col:local_amount}-{col:base_price}', 11),
    CA('phone', 'Vendor phone', 'text', LKT('quotes.phone', 'quotes.quote_id', 'quote_id'), 18),
    CA('dest_add', 'Destination adds', 'money', '{set:couple_flights}+{set:couple_nights}*{set:room_rate}+SUM({range:party.helped})', 12),
    CA('local_total', 'Local quotes total', 'money', 'SUM({range:dest.local_amount})', 12), LIT('partner_phone', 'Partner phone', D.P2_PHONE), CPL()],
    D.dest_d(), 50))

# 15 party travel -----------------------------------------------------------
REH = tok('event', 'Rehearsal dinner'); BRU = tok('event', 'Farewell brunch')
tables.append(T('party', 'Party Travel', 'Party Travel', 'One row per person in the wedding party and the family helpers: flights, nights and what the couple helps with; stay, total and what they cover fill in.', [
    C('party_id', 'Party ID', 'text', 9, required=True), LST('person', 'Person', 'person', 20), LST('role', 'Role', 'prole', 14), LST('event', 'Joins', 'event', 32), C('flights', 'Flights', 'money', 10),
    C('nights', 'Nights', 'int', 8), C('helped', 'Helped by the couple', 'money', 12), C('phone', 'Phone', 'text', 18),
    CA('stay', 'Stay', 'money', '{col:nights}*{set:room_rate}', 10), CA('total', 'Total', 'money', '{col:flights}+{col:stay}', 10), CA('they_cover', 'They cover', 'money', '{col:total}-{col:helped}', 11),
    CA('event_date', 'Event date', 'date', LKD('events.date', 'events.event', 'event'), 11),
    CA('event_share', 'Share per invitee', 'money', 'IFERROR(ROUND(INDEX({range:ecosts.per_guest},MATCH({col:event},{range:ecosts.event},0)),0),0)', 11),
    CA('rehearsal_date', 'Rehearsal dinner date', 'date', 'INDEX({range:events.date},MATCH(%s,{range:events.event},0))' % REH, 12),
    CA('rehearsal_start', 'Rehearsal dinner start', 'text', 'INDEX({range:invitees.start},MATCH(%s,{range:invitees.event},0))&""' % REH, 10),
    CA('brunch_date', 'Brunch date', 'date', 'INDEX({range:events.date},MATCH(%s,{range:events.event},0))' % BRU, 11),
    CA('brunch_start', 'Brunch start', 'text', 'INDEX({range:invitees.start},MATCH(%s,{range:invitees.event},0))&""' % BRU, 9),
    CA('flight_by', 'Send flight details by', 'date', '{set:wedding_day}-{set:flight_days}', 12), CA('reply_by', 'Reply by', 'date', '{col:rehearsal_date}-{set:reply_days}', 11),
    CA('party_rooms', 'Rooms for the party', 'int', 'COUNTIFS({range:party.nights},">0")', 9), CA('party_nights', 'Longest stay in nights', 'int', 'MAX({range:party.nights})', 9),
    LIT('hotel_phone', 'Hotel phone', D.HOTEL_PHONE), CPL()],
    D.party_d(), 50, [A('they_cover', '> 400', 'warn')]))

# 16 paperwork --------------------------------------------------------------
tables.append(T('paper', 'Paperwork', 'Paperwork Rows', 'One row per paperwork step: kind, due date, status and owner; start-by date, days left and a flag fill in. Check lead times with your officiant or local office.', [
    C('item_id', 'Step ID', 'text', 8, required=True), C('item', 'Step', 'text', 36), LST('kind', 'Kind', 'pkind', 18), C('due_date', 'Due date', 'date', 11), LST('status', 'Status', 'tstatus', 12), C('owner', 'Owner', 'text', 16),
    CA('lead_days', 'Lead time in days', 'int', '{set:paperwork_lead_days}', 10),
    CA('start_by', 'Start by', 'date', 'IF({col:status}=%s,"",IF({col:kind}=%s,{col:due_date}-{set:paperwork_lead_days},{col:due_date}))' % (tok('tstatus', 'Done'), MARRIAGE), 11),
    CA('days_left', 'Days left', 'int', 'IF({col:start_by}="","",{col:start_by}-{today})', 9),
    CA('flag', 'Flag', 'text', 'IF({col:status}=%s,%s,IF({col:days_left}<0,%s,IF({col:days_left}<=90,%s,%s)))' % (tok('tstatus', 'Done'), v('Done'), v('Late'), v('Start soon'), v('On time')), 11),
    LIT('partner_phone', 'Partner phone', D.P2_PHONE), CPL()],
    D.paper_d(), 50, [A('flag', '= ' + v('Late'), 'bad'), A('flag', '= ' + v('Start soon'), 'warn'), A('flag', '= ' + v('Done'), 'good')]))

# 17 two-track comparison ---------------------------------------------------
def MAXC(c_): return 'MAX(SUMIFS({range:budget.planned},{range:budget.category},{col:%s}),SUMIFS({range:budget.committed},{range:budget.category},{col:%s}))' % (c_, c_)
SMALL = ('ROUND(IF({col:line}=%s,%s+%s,IF({col:line}=%s,%s*%s+%s*%s,IF({col:scales}=%s,{col:big}*(%s+%s)/%s*{col:share},{col:big}*{col:share}))),0)') % (
    tok('tline', 'Venue'), TIN('Ceremony venue cost'), TIN('Party venue cost'), tok('tline', 'Food and drink'), TIN('Ceremony guests'), TIN('Ceremony food per guest'), TIN('Party guests'), TIN('Party food per guest'),
    YES, TIN('Ceremony guests'), TIN('Party guests'), TIN('Big wedding guests'))
tables.append(T('tracks', 'Two-track Compare', 'Two-track Comparison', 'One row per cost line: what the big wedding costs from your budget and what a small ceremony plus a later party would cost, with the difference; the track assumptions are in Track Inputs.', [
    LST('line', 'Line', 'tline', 24, required=True), LST('cat1', 'Budget category', 'category', 24), LST('cat2', 'Second category', 'category', 24), C('scales', 'Scales with guests', 'bool', 10), C('share', 'Share kept', 'pct', 9),
    CA('big', 'One big wedding', 'money', '%s+IF({col:cat2}="",0,%s)' % (MAXC('cat1'), MAXC('cat2')), 13), CA('small', 'Small ceremony plus a party', 'money', SMALL, 14),
    CA('difference', 'Difference', 'money', '{col:small}-{col:big}', 12), CA('gap_abs', 'Size of the difference', 'money', 'ABS({col:difference})', 12),
    CA('gap_rank', 'Rank of the difference', 'int', 'COUNTIFS({range:tracks.gap_abs},">"&{col:gap_abs})+1', 9), LIT('partner_phone', 'Partner phone', D.P2_PHONE), CPL()],
    D.tracks_d(), 50, [A('difference', '< 0', 'good')]))

# 18 track inputs -----------------------------------------------------------
tables.append(T('tin', 'Track Inputs', 'Track Inputs', 'The eight numbers behind the two-track comparison: guests, venue costs and food per guest. They are your own estimates; edit them.', [
    LST('item', 'Item', 'tinput', 30, required=True), C('value', 'Value', 'num', 10), C('note', 'Note', 'text', 34)], D.tin_d(), 50))

# 19 budget lines -----------------------------------------------------------
tables.append(T('budget', 'Budget Lines', 'Budget Lines', 'The budget lines of the whole wedding from the budget workbook: planned, committed and paid; the variance and what is still due fill in.', [
    C('line_id', 'Line ID', 'text', 9, required=True), LST('category', 'Category', 'category', 24), C('planned', 'Planned', 'money', 11), C('committed', 'Committed', 'money', 11), C('paid', 'Paid', 'money', 11),
    CA('variance', 'Committed less planned', 'money', '{col:committed}-{col:planned}', 12), CA('still_due', 'Still due', 'money', '{col:committed}-{col:paid}', 11)],
    D.budget_d(), 50, [A('variance', '> 0', 'warn')]))

# 20 honeymoon scenarios ----------------------------------------------------
def DB(o): return '(%s+%s)' % (OPTK(o, STAY), OPTK(o, DAILY))
def DAYS(o): return 'SUMPRODUCT(MAX((%s=%s)*%s))' % (R('hm', 'option'), o, R('hm', 'days'))
SCT = ('IF({col:scenario}=%s,%s,IF({col:scenario}=%s,%s-%s,IF({col:scenario}=%s,%s-3*%s/%s,IF({col:scenario}=%s,%s,IF({col:scenario}=%s,%s+2*%s/%s,%s+%s)))))') % (
    tok('hscen', 'Option A as planned'), OPT(OA), tok('hscen', 'Option A without activities'), OPT(OA), OPTK(OA, ACTIV), tok('hscen', 'Option A, three days shorter'), OPT(OA), DB(OA), DAYS(OA),
    tok('hscen', 'Option B as planned'), OPT(OB), tok('hscen', 'Option B, two days longer'), OPT(OB), DB(OB), DAYS(OB), OPT(OB), OPTK(OA, ACTIV))
tables.append(T('hscen', 'Honeymoon Scenarios', 'Honeymoon Scenarios', 'Six what-if versions of the two honeymoon options with their total and a verdict against the money received and promised.', [
    LST('scenario', 'Scenario', 'hscen', 34, required=True), CA('total', 'Total', 'money', 'ROUND(%s,0)' % SCT, 12),
    CA('verdict', 'Verdict', 'text', 'IF({col:total}<=%s,%s,%s&" "&ROUND({col:total}-%s,0))' % (FUNDS, v('Affordable'), v('Short by'), FUNDS), 20)],
    D.scen_d(), 50, [A('verdict', '= ' + v('Affordable'), 'good')]))
assert len(tables) == 20
