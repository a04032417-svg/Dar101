"""Nonprofit suite part 4 (Events and Campaigns): settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np4_lists import *
import np4_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKX(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),"")' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def ORG(): return CA('org', 'Organization', 'text', '{set:org}', 22)
def PH(k, label, phone): return CA(k, label, 'text', '"%s"' % phone, 17)
def R(t, c): return '{range:%s.%s}' % (t, c)
YES = '{list:yesno.yes}'
DONE = tok('estatus', 'Done'); PLANNED = tok('estatus', 'Planned'); GALA = tok('ekind', 'Gala')
DECL = tok('sstatus', 'Declined'); PROM = tok('sstatus', 'Promised'); SOLD = tok('auction', 'Sold')

settings = [
    S('org', 'Your organization name', 'text', COMPANY),
    S('cost_per_dollar', 'Cost to raise one dollar, starting point, set your own', 'num', COST_PER_DOLLAR),
    S('volunteer_hour_value', 'Value of one volunteer hour, your setting', 'money', VOLUNTEER_HOUR_VALUE),
    S('staff_hour_cost', 'Cost of one staff hour at an event, your own figure', 'money', 32),
    S('over_budget_pct', 'Cost above budget that counts as over, share of budget', 'pct', 0.05),
    S('tolerance', 'Change in net per guest that counts as the same', 'pct', 0.05),
    S('benefit_cost', 'Average cost of delivering one sponsor benefit', 'money', 350),
    S('benefit_days', 'Days after the event to deliver sponsor benefits', 'int', 30),
    S('pay_days_before', 'Sponsor payment due, days before the event', 'int', 14),
    S('call_days', 'Follow-up within this many days means call this week', 'int', 7),
    S('stale_days', 'Days after a follow-up date when a small sponsor is let go', 'int', 120),
    S('renew_min', 'Smallest sponsor amount worth a renewal call', 'money', 1000),
    S('names_days', 'Table names needed, days before the event', 'int', 14),
    S('send_days', 'Auction items and programs needed, days before the event', 'int', 10),
    S('pay_days_after', 'Auction buyer pays within, days after the event', 'int', 14),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 events ------------------------------------------------------------------
tables.append(T('events', 'Events', 'Events with budget, goal and result',
    'One row per event: plan, venue, budget and goal; seats sold, money raised, actual cost, net, cost per dollar, go or no-go and break-even tickets fill in by themselves.', [
    C('event_id', 'Event ID', 'text', 9, required=True), C('event', 'Event', 'text', 24), LST('kind', 'Kind', 'ekind', 10), C('date', 'Date', 'date', 11), C('year', 'Year', 'int', 7), C('venue', 'Venue', 'text', 24),
    C('doors', 'Doors open', 'time', 9), C('budget_cost', 'Budget cost', 'money', 12), C('goal', 'Goal', 'money', 12), C('expected', 'Expected guests', 'int', 9), LST('status', 'Status', 'estatus', 10),
    LST('campaign', 'Campaign', 'campaign', 16), C('campaign_id', 'Campaign ID', 'text', 10),
    CA('seats_sold', 'Seats sold', 'int', 'SUMIFS(%s,%s,{col:event})' % (R('event_tickets', 'seats'), R('event_tickets', 'event')), 9),
    CA('seats_left', 'Seats left', 'int', 'IF({col:expected}>0,MAX(0,{col:expected}-{col:seats_sold}),"")', 9),
    CA('ticket_money', 'Ticket money', 'money', 'SUMIFS(%s,%s,{col:event})' % (R('event_tickets', 'amount'), R('event_tickets', 'event')), 12),
    CA('sponsor_promised', 'Sponsor money promised', 'money', 'SUMIFS(%s,%s,{col:event},%s,"<>"&%s)' % (R('sponsors', 'promised'), R('sponsors', 'event'), R('sponsors', 'status'), DECL), 13),
    CA('sponsor_received', 'Sponsor money received', 'money', 'SUMIFS(%s,%s,{col:event})' % (R('sponsors', 'received'), R('sponsors', 'event')), 13),
    CA('auction_income', 'Auction income', 'money', 'SUMIFS(%s,%s,{col:event})' % (R('auction_items', 'sold_price'), R('auction_items', 'event')), 12),
    CA('gifts_total', 'Gifts at the event', 'money', 'SUMIFS(%s,%s,{col:event})' % (R('event_gifts', 'amount'), R('event_gifts', 'event')), 12),
    CA('raised', 'Raised', 'money', '{col:ticket_money}+{col:sponsor_received}+{col:auction_income}+{col:gifts_total}', 12),
    CA('actual_cost', 'Actual cost', 'money', 'SUMIFS(%s,%s,{col:event})' % (R('event_costs', 'amount'), R('event_costs', 'event')), 12),
    CA('net_raised', 'Net raised', 'money', '{col:raised}-{col:actual_cost}', 12),
    CA('cost_per_dollar', 'Cost per dollar', 'num', 'IF(AND({col:raised}>0,{col:status}=%s),{col:actual_cost}/{col:raised},"")' % DONE, 10),
    CA('cost_over', 'Cost over budget', 'money', 'MAX(0,{col:actual_cost}-{col:budget_cost})', 12),
    CA('days_to', 'Days to the event', 'int', '{col:date}-{today}', 9),
    CA('upcoming', 'Next ticketed date', 'date', 'IF(AND({col:date}>={today},{col:expected}>0),{col:date},"")', 11),
    CA('kind_year', 'Kind and year', 'text', '{col:kind}&"|"&{col:year}', 12),
    CA('price_seat', 'Last year ticket money per seat', 'money', 'IFERROR(SUMIFS(%s,%s,{col:kind},%s,{col:year}-1)/SUMIFS(%s,%s,{col:kind},%s,{col:year}-1),0)' % (
        R('events', 'ticket_money'), R('events', 'kind'), R('events', 'year'), R('events', 'seats_sold'), R('events', 'kind'), R('events', 'year')), 12),
    CA('break_even_tickets', 'Break-even seats', 'int', 'IF(AND({col:expected}>0,{col:price_seat}>0),ROUNDUP(MAX(0,{col:budget_cost}-{col:sponsor_promised})/{col:price_seat},0),"")', 10),
    CA('go_verdict', 'Go or no-go from the plan', 'text', 'IF({col:goal}=0,"",IF({col:budget_cost}/{col:goal}<={set:cost_per_dollar},%s,IF({col:goal}>{col:budget_cost},%s,%s)))' % (ca('Run'), ca('Run smaller'), ca('Do not run')), 16),
    CA('program_by', 'Programs needed by', 'date', '{col:date}-{set:send_days}', 11), ORG(),
    PH('director_phone', 'Development manager phone', D.DEV_PHONE), PH('exec_phone', 'Executive director phone', D.EXEC_PHONE), PH('chair_phone', 'Fundraising chair phone', D.CHAIR_PHONE),
    PH('venue_phone', 'Venue contact phone', D.VENUE_PHONE), PH('caterer_phone', 'Caterer phone', D.CATERER_PHONE), PH('printer_phone', 'Printer phone', D.PRINTER_PHONE)],
    D.events_d(), 40, [A('cost_over', '> 0', 'bad'), A('status', '= ' + tok('estatus', 'Planned'), 'good')]))
# 2 event tickets -----------------------------------------------------------
tables.append(T('event_tickets', 'Event Tickets', 'Ticket and registration sales',
    'One row per sale: buyer, ticket type, quantity, price and seats; the amount, the gift part of the price, the event date, the doors time and the seats left fill in.', [
    C('ticket_id', 'Ticket ID', 'text', 10, required=True), REF('event', 'Event', 'events.event', 24), C('sold_on', 'Sold on', 'date', 11), C('month', 'Month', 'date', 11), C('buyer', 'Buyer', 'text', 24),
    C('phone', 'Phone', 'text', 18), LST('ticket_type', 'Ticket type', 'ticket', 13), C('quantity', 'Quantity', 'int', 9), C('price_each', 'Price each', 'money', 11), C('seats', 'Seats', 'int', 8),
    CA('benefit_each', 'Benefit value each', 'money', 'IFERROR(INDEX(%s,MATCH({col:ticket_type},%s,0)),0)' % (R('ticket_types', 'benefit_value'), R('ticket_types', 'ticket')), 11), CA('amount', 'Amount', 'money', '{col:quantity}*{col:price_each}', 11), CA('gift_part', 'Gift part of the price', 'money', 'MAX(0,{col:quantity}*({col:price_each}-{col:benefit_each}))', 12),
    CA('event_date', 'Event date', 'date', LKD('events.date', 'events.event', 'event'), 11), CA('venue', 'Venue', 'text', LKT('events.venue', 'events.event', 'event'), 22),
    CA('doors', 'Doors open', 'time', LKX('events.doors', 'events.event', 'event'), 9), CA('seats_left', 'Seats left at the event', 'int', LKX('events.seats_left', 'events.event', 'event'), 10),
    CA('names_by', 'Names needed by', 'date', 'IF({col:event_date}="","",{col:event_date}-{set:names_days})', 11), ORG()],
    [{k: v for k, v in r.items() if k != 'benefit_each'} for r in D.tickets_d()], 1200, [A('seats', '>= 10', 'good')]))
# 3 ticket types ------------------------------------------------------------
tables.append(T('ticket_types', 'Ticket Types', 'Ticket types with price and benefit value',
    'One row per ticket type: the price and the value of what the guest gets back (dinner, shirt); the rest of the price is a gift.', [
    LST('ticket', 'Ticket type', 'ticket', 18, required=True), C('price', 'Price', 'money', 11), C('benefit_value', 'Benefit value', 'money', 11)], D.ticket_types_d(), 50))
# 4 sponsors ----------------------------------------------------------------
tables.append(T('sponsors', 'Sponsors', 'Sponsor log with benefits owed and delivered',
    'One row per sponsor and event: level, promised and received money, benefits owed and delivered and the next step; unpaid money, the payment due date and benefits left fill in.', [
    C('sponsor_id', 'Sponsor ID', 'text', 10, required=True), REF('event', 'Event', 'events.event', 24), C('sponsor', 'Sponsor', 'text', 26), C('contact', 'Contact', 'text', 20), C('phone', 'Phone', 'text', 18),
    LST('level', 'Level', 'level', 12), C('promised', 'Promised', 'money', 11), C('received', 'Received', 'money', 11), C('promised_on', 'Promised on', 'date', 11), C('received_on', 'Received on', 'date', 11),
    LST('status', 'Status', 'sstatus', 10), C('benefits_owed', 'Benefits owed', 'int', 9), C('benefits_delivered', 'Benefits delivered', 'int', 10), LST('next_step', 'Next step', 'snext', 22), C('next_step_date', 'Next step date', 'date', 11),
    CA('event_date', 'Event date', 'date', LKD('events.date', 'events.event', 'event'), 11), CA('kind', 'Event kind', 'text', LKT('events.kind', 'events.event', 'event'), 11),
    CA('unpaid', 'Promised, not paid', 'money', 'IF({col:status}=%s,MAX(0,{col:promised}-{col:received}),0)' % PROM, 12),
    CA('due_date', 'Payment due', 'date', 'IF({col:event_date}="","",{col:event_date}-{set:pay_days_before})', 11), CA('benefits_left', 'Benefits left', 'int', 'MAX(0,{col:benefits_owed}-{col:benefits_delivered})', 9),
    CA('event_raised', 'Event raised', 'money', LKN('events.raised', 'events.event', 'event'), 12), ORG()],
    D.sponsors_d(), 200, [A('unpaid', '> 0', 'warn'), A('benefits_left', '> 0', 'warn'), A('status', '= ' + DECL, 'bad')]))
# 5 sponsor levels ----------------------------------------------------------
tables.append(T('sponsor_levels', 'Sponsor Levels', 'Sponsor package price list',
    'One row per package level and event kind: your price and the number of benefits; sponsors sold, cost of benefits and margin fill in.', [
    LST('level', 'Level', 'level', 13, required=True), LST('kind', 'Event kind', 'ekind', 12), C('price', 'Price', 'money', 12), C('benefits_count', 'Benefits', 'int', 9),
    CA('sold', 'Sponsors sold', 'int', 'COUNTIFS(%s,{col:level},%s,{col:kind},%s,"<>"&%s)' % (R('sponsors', 'level'), R('sponsors', 'kind'), R('sponsors', 'status'), DECL), 9),
    CA('benefit_total', 'Cost of benefits', 'money', '{col:benefits_count}*{set:benefit_cost}', 12), CA('margin', 'Margin', 'money', '{col:price}-{col:benefit_total}', 12),
    CA('margin_share', 'Margin share of price', 'pct', 'IF({col:price}>0,{col:margin}/{col:price},"")', 11)], D.sponsor_levels_d(), 50))
# 6 auction items -----------------------------------------------------------
tables.append(T('auction_items', 'Auction Items', 'Auction and raffle items with value and sale price',
    'One row per donated item: fair value, starting bid, sold price and buyer; the value check, the date to send the item and the date to pay fill in.', [
    C('item_id', 'Item ID', 'text', 9, required=True), REF('event', 'Event', 'events.event', 24), C('item', 'Item', 'text', 26), C('donated_by', 'Donated by', 'text', 26), C('donor_phone', 'Donor phone', 'text', 18),
    C('fair_value', 'Fair value', 'money', 11), C('starting_bid', 'Starting bid', 'money', 11), C('sold_price', 'Sold price', 'money', 11), C('buyer', 'Buyer', 'text', 24), C('buyer_phone', 'Buyer phone', 'text', 18),
    LST('status', 'Status', 'auction', 10), C('received_on', 'Received on', 'date', 11),
    CA('vs_fair', 'Sold against fair value', 'money', 'IF(AND({col:status}=%s,{col:fair_value}>0),{col:sold_price}-{col:fair_value},"")' % SOLD, 12),
    CA('start_share', 'Start share of value', 'pct', 'IF({col:fair_value}>0,{col:starting_bid}/{col:fair_value},"")', 10),
    CA('event_date', 'Event date', 'date', LKD('events.date', 'events.event', 'event'), 11), CA('send_by', 'Send item by', 'date', 'IF({col:event_date}="","",{col:event_date}-{set:send_days})', 11),
    CA('pay_by', 'Buyer pays by', 'date', 'IF({col:event_date}="","",{col:event_date}+{set:pay_days_after})', 11),
    CA('check', 'Value check', 'text', 'IF({col:fair_value}=0,%s,IF({col:status}=%s,%s,IF({col:fair_value}>=500,%s,%s)))' % (ca('Add a fair value'), SOLD, ca('Keep item'), ca('Lower start'), ca('Drop item')), 15), ORG()],
    D.auction_d(), 200, [A('status', '= ' + tok('auction', 'Unsold'), 'warn')]))
# 7 event gifts -------------------------------------------------------------
tables.append(T('event_gifts', 'Event Gifts', 'Gifts to events and campaigns',
    'One row per gift to an event or a campaign (paste them from your gift log); first gift of the donor in the campaign, campaign totals and days left fill in.', [
    C('gift_id', 'Gift ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('donor_id', 'Donor ID', 'text', 9), C('donor', 'Donor', 'text', 24), C('phone', 'Phone', 'text', 18),
    C('amount', 'Amount', 'money', 11), REF('event', 'Event', 'events.event', 24), REF('campaign_id', 'Campaign ID', 'campaigns.campaign_id', 11), LST('campaign', 'Campaign', 'campaign', 18), LST('appeal', 'Appeal', 'appeal', 20),
    LST('gift_type', 'Gift type', 'gtype', 14), C('new_donor', 'New donor', 'bool', 8),
    CA('first_here', 'First gift in campaign', 'int', 'IF(COUNTIFS(%s,{col:donor_id},%s,{col:campaign_id},%s,"<"&{col:gift_id})=0,1,0)' % (R('event_gifts', 'donor_id'), R('event_gifts', 'campaign_id'), R('event_gifts', 'gift_id')), 10),
    CA('at_event', 'At an event', 'int', 'IF({col:event}="",0,1)', 8),
    CA('camp_raised', 'Campaign raised', 'money', LKN('campaign_compare.raised', 'campaign_compare.campaign_id', 'campaign_id'), 12), CA('camp_goal', 'Campaign goal', 'money', LKN('campaigns.goal', 'campaigns.campaign_id', 'campaign_id'), 12),
    CA('end_date', 'Campaign ends', 'date', LKD('campaigns.end_date', 'campaigns.campaign_id', 'campaign_id'), 11), CA('days_left', 'Days left', 'int', 'IF({col:end_date}="","",MAX(0,{col:end_date}-{today}))', 8), ORG()],
    D.event_gifts_d(), 2000))
# 8 event costs -------------------------------------------------------------
tables.append(T('event_costs', 'Event Costs', 'Event and campaign costs by category',
    'One row per cost line of an event or a campaign: category, vendor and amount; the budget of the event and the share of it fill in.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('event', 'Event', 'events.event', 24), REF('campaign_id', 'Campaign ID', 'campaigns.campaign_id', 11),
    LST('category', 'Category', 'ecat', 24), C('vendor', 'Vendor', 'text', 22), C('amount', 'Amount', 'money', 12),
    CA('budget', 'Event budget', 'money', LKN('events.budget_cost', 'events.event', 'event'), 12), CA('share_of_budget', 'Share of event budget', 'pct', 'IF({col:budget}>0,{col:amount}/{col:budget},"")', 10),
    PH('bookkeeper_phone', 'Bookkeeper phone', D.BOOK_PHONE), ORG()], D.event_costs_d(), 300))
# 9 event result ------------------------------------------------------------
tables.append(T('event_result', 'Event Result', 'Result of every event',
    'One row per event: tickets, sponsors, auction, gifts, costs, net, cost per dollar and net per guest against your own last year; the verdict fills in.', [
    REF('event', 'Event', 'events.event', 24, required=True),
    CA('event_id', 'Event ID', 'text', LKT('events.event_id', 'events.event', 'event'), 9), CA('kind', 'Kind', 'text', LKT('events.kind', 'events.event', 'event'), 10), CA('year', 'Year', 'int', LKN('events.year', 'events.event', 'event'), 7),
    CA('date', 'Date', 'date', LKD('events.date', 'events.event', 'event'), 11), CA('status', 'Status', 'text', LKT('events.status', 'events.event', 'event'), 9), CA('campaign_id', 'Campaign ID', 'text', LKT('events.campaign_id', 'events.event', 'event'), 10),
    CA('tickets', 'Ticket money', 'money', LKN('events.ticket_money', 'events.event', 'event'), 12), CA('sponsors', 'Sponsor money', 'money', LKN('events.sponsor_received', 'events.event', 'event'), 12),
    CA('auction', 'Auction income', 'money', LKN('events.auction_income', 'events.event', 'event'), 12), CA('gifts', 'Gifts', 'money', LKN('events.gifts_total', 'events.event', 'event'), 12),
    CA('raised', 'Raised', 'money', '{col:tickets}+{col:sponsors}+{col:auction}+{col:gifts}', 12), CA('costs', 'Costs', 'money', LKN('events.actual_cost', 'events.event', 'event'), 12),
    CA('net', 'Net raised', 'money', '{col:raised}-{col:costs}', 12), CA('budget_cost', 'Budget cost', 'money', LKN('events.budget_cost', 'events.event', 'event'), 12),
    CA('non_gift', 'Tickets, sponsors and auction', 'money', '{col:tickets}+{col:sponsors}+{col:auction}', 13),
    CA('ticket_gift_part', 'Gift part of ticket money', 'money', 'SUMIFS(%s,%s,{col:event})' % (R('event_tickets', 'gift_part'), R('event_tickets', 'event')), 12),
    CA('benefit_value', 'Benefit part of ticket money', 'money', '{col:tickets}-{col:ticket_gift_part}', 12),
    CA('cost_per_dollar', 'Cost per dollar', 'num', LKX('events.cost_per_dollar', 'events.event', 'event'), 10),
    CA('guests', 'Guests or donors', 'int', 'IF(%s>0,%s,COUNTIFS(%s,{col:event}))' % (LKN('events.seats_sold', 'events.event', 'event'), LKN('events.seats_sold', 'events.event', 'event'), R('event_gifts', 'event')), 9),
    CA('net_per_guest', 'Net per guest', 'money', 'IF(AND({col:status}=%s,{col:guests}>0),{col:net}/{col:guests},"")' % DONE, 11),
    CA('last_cpd', 'Last year cost per dollar', 'num', 'IFERROR(SUMIFS(%s,%s,{col:kind},%s,{col:year}-1)/SUMIFS(%s,%s,{col:kind},%s,{col:year}-1),"")' % (
        R('event_result', 'costs'), R('event_result', 'kind'), R('event_result', 'year'), R('event_result', 'raised'), R('event_result', 'kind'), R('event_result', 'year')), 10),
    CA('last_net', 'Last year net', 'money', 'SUMIFS(%s,%s,{col:kind},%s,{col:year}-1)' % (R('event_result', 'net'), R('event_result', 'kind'), R('event_result', 'year')), 12),
    CA('last_npg', 'Last year net per guest', 'money', 'IFERROR(SUMIFS(%s,%s,{col:kind},%s,{col:year}-1)/SUMIFS(%s,%s,{col:kind},%s,{col:year}-1),"")' % (
        R('event_result', 'net'), R('event_result', 'kind'), R('event_result', 'year'), R('event_result', 'guests'), R('event_result', 'kind'), R('event_result', 'year')), 11),
    CA('net_vs_last', 'Net against last year', 'pct', 'IF(AND({col:status}=%s,{col:last_net}>0),{col:net}/{col:last_net}-1,"")' % DONE, 10),
    CA('staff_hours', 'Staff hours', 'hours', 'SUMIFS(%s,%s,{col:event})' % (R('event_hours', 'staff_hours'), R('event_hours', 'event')), 9),
    CA('volunteer_hours', 'Volunteer hours', 'hours', 'SUMIFS(%s,%s,{col:event})' % (R('event_hours', 'volunteer_hours'), R('event_hours', 'event')), 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:status}<>%s,%s,IF({col:costs}>{col:budget_cost}*(1+{set:over_budget_pct}),%s&" "&ROUND({col:costs}-{col:budget_cost},0),IF(ISNUMBER({col:last_npg}),IF({col:net_per_guest}<{col:last_npg}*(1-{set:tolerance}),%s,%s),%s)))' % (
        DONE, ca('Not held yet'), ca('Over cost by'), ca('Below last year'), ca('Good result'), ca('Good result')), 20), ORG(), PH('chair_phone', 'Fundraising chair phone', D.CHAIR_PHONE)],
    [dict(event=r['event']) for r in sorted(D.events_d(), key=lambda r: (r['event_id'] != D.ST['event'], r['date'] < D.TS, r['date']))], 50, [A('cost_per_dollar', '> {set:cost_per_dollar}', 'bad')]))
# 10 event hours ------------------------------------------------------------
tables.append(T('event_hours', 'Event Hours', 'Staff and volunteer hours by work area',
    'One row per event and work area: the lead, staff hours, volunteer hours, volunteers needed and signed up; staff cost, volunteer value and volunteers still needed fill in.', [
    C('hours_id', 'Hours ID', 'text', 9, required=True), REF('event', 'Event', 'events.event', 24), LST('area', 'Work area', 'ework', 24), C('lead', 'Lead', 'text', 22), C('lead_phone', 'Lead phone', 'text', 18),
    C('work_date', 'Work date', 'date', 11), C('staff_hours', 'Staff hours', 'num', 9), C('volunteer_hours', 'Volunteer hours', 'num', 10), C('volunteers_needed', 'Volunteers needed', 'int', 10), C('volunteers_signed', 'Volunteers signed up', 'int', 10),
    CA('staff_cost', 'Staff cost', 'money', '{col:staff_hours}*{set:staff_hour_cost}', 11), CA('volunteer_value', 'Volunteer value', 'money', '{col:volunteer_hours}*{set:volunteer_hour_value}', 11),
    CA('still_needed', 'Still needed', 'int', 'MAX(0,{col:volunteers_needed}-{col:volunteers_signed})', 9),
    CA('event_still', 'Still needed for the event', 'int', 'SUMIFS(%s,%s,{col:event})' % (R('event_hours', 'still_needed'), R('event_hours', 'event')), 10),
    CA('event_date', 'Event date', 'date', LKD('events.date', 'events.event', 'event'), 11), PH('coordinator_phone', 'Volunteer coordinator phone', D.COORD_PHONE), ORG()], D.hours_d(), 200, [A('still_needed', '> 0', 'warn')]))
# 11 campaigns --------------------------------------------------------------
tables.append(T('campaigns', 'Campaigns', 'Campaigns by year with goal and dates',
    'One row per campaign and year: dates and goal, the pledges promised but not paid and, for ongoing giving, the totals you type from your gift log; the main campaign is the one you track.', [
    C('campaign_id', 'Campaign ID', 'text', 11, required=True), LST('campaign', 'Campaign', 'campaign', 20), C('year', 'Year', 'int', 7), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), C('goal', 'Goal', 'money', 12),
    C('pledged_open', 'Pledged, not yet paid', 'money', 12), C('other_raised', 'Raised outside the gift rows', 'money', 13), C('other_cost', 'Cost outside the cost rows', 'money', 12), C('other_donors', 'Donors outside the gift rows', 'int', 11),
    C('other_new', 'New donors outside the gift rows', 'int', 11), C('main', 'Main campaign', 'bool', 9),
    CA('label', 'Campaign and year', 'text', '{col:campaign}&" "&{col:year}', 24), CA('weeks', 'Weeks', 'int', 'ROUNDUP(({col:end_date}-{col:start_date}+1)/7,0)', 7),
    CA('state', 'State', 'text', 'IF({col:end_date}<{today},%s,IF({col:start_date}>{today},%s,%s))' % (ca('Closed'), ca('Coming'), ca('Running')), 10)], D.campaigns_d(), 60, [A('main', '= ' + YES, 'good')]))
# 12 campaign progress ------------------------------------------------------
tables.append(T('campaign_progress', 'Campaign Progress', 'Campaign thermometer',
    'One row per campaign: goal, raised, pledged not paid, share of goal, days left, the pace needed a week and a forecast to finish; the status fills in.', [
    REF('campaign_id', 'Campaign ID', 'campaigns.campaign_id', 11, required=True),
    CA('campaign', 'Campaign', 'text', LKT('campaigns.campaign', 'campaigns.campaign_id', 'campaign_id'), 20), CA('year', 'Year', 'int', LKN('campaigns.year', 'campaigns.campaign_id', 'campaign_id'), 7),
    CA('main', 'Main', 'text', LKT('campaigns.main', 'campaigns.campaign_id', 'campaign_id'), 7), CA('goal', 'Goal', 'money', LKN('campaigns.goal', 'campaigns.campaign_id', 'campaign_id'), 12),
    CA('start_date', 'Start date', 'date', LKD('campaigns.start_date', 'campaigns.campaign_id', 'campaign_id'), 11), CA('end_date', 'End date', 'date', LKD('campaigns.end_date', 'campaigns.campaign_id', 'campaign_id'), 11),
    CA('raised', 'Raised', 'money', LKN('campaign_compare.raised', 'campaign_compare.campaign_id', 'campaign_id'), 12), CA('pledged', 'Pledged, not yet paid', 'money', LKN('campaigns.pledged_open', 'campaigns.campaign_id', 'campaign_id'), 12),
    CA('share', 'Share of goal', 'pct', 'IF({col:goal}>0,{col:raised}/{col:goal},"")', 9), CA('days_left', 'Days left', 'int', 'IF({col:end_date}="","",MAX(0,{col:end_date}-{today}))', 8),
    CA('elapsed', 'Share of time gone', 'pct', 'IF({col:end_date}="","",MIN(1,MAX(0,({today}-{col:start_date}+1)/({col:end_date}-{col:start_date}+1))))', 9),
    CA('pace_needed', 'Pace needed a week', 'money', 'IF(N({col:days_left})>0,MAX(0,{col:goal}-{col:raised})/({col:days_left}/7),"")', 12),
    CA('recent_pace', 'Pace now a week', 'money', 'IF(N({col:days_left})>0,SUMIFS(%s,%s,{col:campaign_id},%s,">="&({today}-28),%s,"<="&{today})/(MAX(1,MIN(28,{today}-{col:start_date}+1))/7),"")' % (
        R('event_gifts', 'amount'), R('event_gifts', 'campaign_id'), R('event_gifts', 'date'), R('event_gifts', 'date')), 12),
    CA('forecast', 'Forecast to finish', 'money', 'IF(N({col:days_left})>0,{col:raised}+{col:recent_pace}*{col:days_left}/7,{col:raised})', 12),
    CA('status', 'Status', 'text', 'IF(N({col:days_left})=0,%s,IF({col:share}>={col:elapsed}*1.05,%s,IF({col:share}>={col:elapsed}*0.95,%s,%s&" "&ROUND({col:elapsed}*{col:goal}-{col:raised},0))))' % (
        ca('Closed'), ca('Ahead'), ca('On pace'), ca('Behind by')), 18), ORG(), PH('exec_phone', 'Executive director phone', D.EXEC_PHONE)], D.campaign_progress_d(), 50, [A('share', '< 0.5', 'warn')]))
# 13 campaign by week -------------------------------------------------------
WKN = '+'.join('({col:week}=%s)*%d' % (tok('wk', 'Week %d' % i), i) for i in range(1, 10))
tables.append(T('campaign_weeks', 'Campaign by Week', 'Campaign giving week by week',
    'One row per campaign and week: gifts raised in the week, the running total and the goal line; weeks after today show the running total so far.', [
    REF('campaign_id', 'Campaign ID', 'campaigns.campaign_id', 11, required=True), LST('week', 'Week', 'wk', 9),
    CA('campaign', 'Campaign', 'text', LKT('campaigns.campaign', 'campaigns.campaign_id', 'campaign_id'), 20), CA('year', 'Year', 'int', LKN('campaigns.year', 'campaigns.campaign_id', 'campaign_id'), 7),
    CA('camp_start', 'Campaign start', 'date', LKD('campaigns.start_date', 'campaigns.campaign_id', 'campaign_id'), 11), CA('camp_end', 'Campaign end', 'date', LKD('campaigns.end_date', 'campaigns.campaign_id', 'campaign_id'), 11),
    CA('camp_goal', 'Campaign goal', 'money', LKN('campaigns.goal', 'campaigns.campaign_id', 'campaign_id'), 12), CA('week_no', 'Week number', 'int', WKN, 8),
    CA('week_start', 'Week starts', 'date', '{col:camp_start}+({col:week_no}-1)*7', 11), CA('week_end', 'Week ends', 'date', 'MIN({col:camp_end},{col:week_start}+6)', 11),
    CA('raised', 'Raised in the week', 'money', 'SUMIFS(%s,%s,{col:campaign_id},%s,">="&{col:week_start},%s,"<="&{col:week_end})' % (R('event_gifts', 'amount'), R('event_gifts', 'campaign_id'), R('event_gifts', 'date'), R('event_gifts', 'date')), 12),
    CA('cumulative', 'Running total', 'money', 'SUMIFS(%s,%s,{col:campaign_id},%s,"<="&{col:week_end})' % (R('event_gifts', 'amount'), R('event_gifts', 'campaign_id'), R('event_gifts', 'date')), 12),
    CA('goal_line', 'Goal line', 'money', '{col:camp_goal}*MIN(1,({col:week_end}-{col:camp_start}+1)/({col:camp_end}-{col:camp_start}+1))', 12),
    CA('share_of_goal', 'Share of goal', 'pct', 'IF({col:camp_goal}>0,{col:cumulative}/{col:camp_goal},"")', 9)], D.campaign_weeks_d(), 150))
# 14 campaign comparison by year --------------------------------------------
COST_ID = 'SUMIFS(%s,%s,{col:campaign_id})+%s' % (R('event_costs', 'amount'), R('event_costs', 'campaign_id'), LKN('campaigns.other_cost', 'campaigns.campaign_id', 'campaign_id'))
tables.append(T('campaign_compare', 'Campaign Comparison', 'Campaign comparison by year',
    'One row per campaign and year: raised, cost, donors, new donors and cost per dollar, and the change on the year before; the verdict fills in.', [
    REF('campaign_id', 'Campaign ID', 'campaigns.campaign_id', 11, required=True), LST('campaign', 'Campaign', 'campaign', 20),
    CA('label', 'Campaign and year', 'text', '{col:campaign}&" "&{col:year}', 24), CA('year', 'Year', 'int', LKN('campaigns.year', 'campaigns.campaign_id', 'campaign_id'), 7),
    CA('goal', 'Goal', 'money', LKN('campaigns.goal', 'campaigns.campaign_id', 'campaign_id'), 12),
    CA('gifts_raised', 'Gifts raised', 'money', 'SUMIFS(%s,%s,{col:campaign_id})' % (R('event_gifts', 'amount'), R('event_gifts', 'campaign_id')), 12),
    CA('event_income', 'Tickets, sponsors and auction', 'money', 'SUMIFS(%s,%s,{col:campaign_id})' % (R('event_result', 'non_gift'), R('event_result', 'campaign_id')), 13),
    CA('other_raised', 'Raised outside the gift rows', 'money', LKN('campaigns.other_raised', 'campaigns.campaign_id', 'campaign_id'), 12), CA('raised', 'Raised', 'money', '{col:gifts_raised}+{col:event_income}+{col:other_raised}', 12),
    CA('cost', 'Cost', 'money', COST_ID, 12),
    CA('donors', 'Donors', 'int', 'COUNTIFS(%s,{col:campaign_id},%s,1)+%s' % (R('event_gifts', 'campaign_id'), R('event_gifts', 'first_here'), LKN('campaigns.other_donors', 'campaigns.campaign_id', 'campaign_id')), 9),
    CA('new_donors', 'New donors', 'int', 'COUNTIFS(%s,{col:campaign_id},%s,1,%s,%s)+%s' % (R('event_gifts', 'campaign_id'), R('event_gifts', 'first_here'), R('event_gifts', 'new_donor'), YES, LKN('campaigns.other_new', 'campaigns.campaign_id', 'campaign_id')), 9),
    CA('cost_per_dollar', 'Cost per dollar', 'num', 'IF({col:raised}>0,{col:cost}/{col:raised},"")', 10), CA('share_of_goal', 'Share of goal', 'pct', 'IF({col:goal}>0,{col:raised}/{col:goal},"")', 9),
    CA('prev_raised', 'Raised the year before', 'money', 'SUMIFS(%s,%s,{col:campaign},%s,{col:year}-1)' % (R('campaign_compare', 'raised'), R('campaign_compare', 'campaign'), R('campaign_compare', 'year')), 12),
    CA('change', 'Change on the year before', 'pct', 'IF({col:prev_raised}>0,{col:raised}/{col:prev_raised}-1,"")', 10),
    CA('verdict', 'Verdict', 'text', 'IF(N(%s)>{today},%s,IF({col:prev_raised}=0,%s,IF({col:raised}>={col:prev_raised},IF(N({col:cost_per_dollar})<={set:cost_per_dollar},%s,%s),IF(N({col:cost_per_dollar})>{set:cost_per_dollar},%s,%s))))' % (
        LKX('campaigns.end_date', 'campaigns.campaign_id', 'campaign_id'), ca('Running'), ca('Hold'), ca('Grow'), ca('Hold'), ca('Retire'), ca('Hold')), 9)], D.campaign_compare_d(), 60))
# 15 method ranking ---------------------------------------------------------
tables.append(T('method_rank', 'Method Ranking', 'Cheapest method ranking',
    'One row per campaign type: cost to raise one dollar over all the years in the comparison and its rank (1 is the cheapest).', [
    LST('campaign', 'Campaign', 'campaign', 22, required=True),
    CA('cost_per_dollar', 'Cost per dollar, all years', 'num', 'IFERROR(SUMIFS(%s,%s,{col:campaign})/SUMIFS(%s,%s,{col:campaign}),"")' % (R('campaign_compare', 'cost'), R('campaign_compare', 'campaign'), R('campaign_compare', 'raised'), R('campaign_compare', 'campaign')), 12),
    CA('rank', 'Rank, 1 is cheapest', 'int', 'IF({col:cost_per_dollar}="","",COUNTIFS(%s,"<"&{col:cost_per_dollar})+1)' % R('method_rank', 'cost_per_dollar'), 10)], D.method_rank_d(), 50))
# 16 sponsor renewal list ---------------------------------------------------
SPK = 'sponsors.sponsor_id'
def SL(c, kind='N'): return {'T': LKT, 'N': LKN, 'D': LKD, 'X': LKX}[kind]('sponsors.%s' % c, SPK, 'sponsor_id')
tables.append(T('sponsor_renewal', 'Sponsor Renewals', 'Sponsors to renew, ranked',
    'One row per sponsor of the last events: last amount, next step and the days to follow up; the verdict (call this week, renew, let go, renewed) and the rank fill in.', [
    REF('sponsor_id', 'Sponsor ID', 'sponsors.sponsor_id', 10, required=True),
    CA('sponsor', 'Sponsor', 'text', SL('sponsor', 'T'), 26), CA('event', 'Event', 'text', SL('event', 'T'), 22), CA('level', 'Level', 'text', SL('level', 'T'), 11), CA('last_amount', 'Last amount', 'money', SL('received'), 11),
    CA('status', 'Status', 'text', SL('status', 'T'), 9), CA('next_step', 'Next step', 'text', SL('next_step', 'T'), 22), CA('next_step_date', 'Next step date', 'date', SL('next_step_date', 'D'), 11),
    CA('days_to', 'Days to follow up', 'int', 'IF({col:next_step_date}="","",{col:next_step_date}-{today})', 9),
    CA('renewed', 'Sponsoring a coming event', 'int', 'COUNTIFS(%s,{col:sponsor},%s,">"&{today},%s,"<>"&%s)' % (R('sponsors', 'sponsor'), R('sponsors', 'event_date'), R('sponsors', 'status'), DECL), 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:renewed}>0,%s,IF({col:status}=%s,%s,IF(AND(N({col:days_to})<-{set:stale_days},{col:last_amount}<{set:renew_min}),%s,IF(N({col:days_to})<={set:call_days},%s,%s))))' % (
        ca('Renewed'), DECL, ca('Let go'), ca('Let go'), ca('Call this week'), ca('Renew')), 15),
    CA('score', 'Score', 'money', 'IF(OR({col:verdict}=%s,{col:verdict}=%s),{col:last_amount}+VALUE(RIGHT({col:sponsor_id},3))/1000,0)' % (ca('Call this week'), ca('Renew')), 10),
    CA('rank', 'Rank', 'int', 'IF({col:score}>0,COUNTIFS(%s,">"&{col:score})+1,"")' % R('sponsor_renewal', 'score'), 7),
    CA('call_n', 'Sponsors to call this week', 'int', 'COUNTIFS(%s,%s)' % (R('sponsor_renewal', 'verdict'), ca('Call this week')), 10), PH('director_phone', 'Development manager phone', D.DEV_PHONE), ORG()],
    D.sponsor_renewal_d(), 100, [A('days_to', '< 0', 'warn')]))
# 17 benefit tracker --------------------------------------------------------
tables.append(T('benefit_tracker', 'Benefit Tracker', 'Sponsor benefits owed and delivered',
    'One row per sponsor: benefits owed, delivered and left, the date they are due and a flag (delivered, overdue, due this month, later).', [
    REF('sponsor_id', 'Sponsor ID', 'sponsors.sponsor_id', 10, required=True),
    CA('sponsor', 'Sponsor', 'text', SL('sponsor', 'T'), 26), CA('event', 'Event', 'text', SL('event', 'T'), 22), CA('level', 'Level', 'text', SL('level', 'T'), 11), CA('event_date', 'Event date', 'date', SL('event_date', 'D'), 11),
    CA('owed', 'Benefits owed', 'int', SL('benefits_owed'), 9), CA('delivered', 'Delivered', 'int', SL('benefits_delivered'), 9), CA('left', 'Left to deliver', 'int', 'MAX(0,{col:owed}-{col:delivered})', 9),
    CA('due_date', 'Due date', 'date', 'IF({col:event_date}="","",{col:event_date}+{set:benefit_days})', 11), CA('days_to_due', 'Days to due date', 'int', 'IF({col:due_date}="","",{col:due_date}-{today})', 9),
    CA('flag', 'Flag', 'text', 'IF({col:left}=0,%s,IF({col:days_to_due}<0,%s,IF({col:days_to_due}<=30,%s,%s)))' % (ca('Delivered'), ca('Overdue'), ca('Due this month'), ca('Later')), 14),
    CA('due_n', 'Benefits due this month', 'int', 'SUMIFS(%s,%s,%s)' % (R('benefit_tracker', 'left'), R('benefit_tracker', 'flag'), ca('Due this month')), 10), PH('director_phone', 'Development manager phone', D.DEV_PHONE), ORG()],
    D.benefit_tracker_d(), 150, [A('left', '> 0', 'warn')]))
# 18 event scenarios --------------------------------------------------------
TK, SP, AU, GI = (tok('lines', x) for x in ('Ticket money', 'Sponsor money', 'Auction income', 'Gifts on the night and appeal'))
TOTR, TOTC, NET, CPD_ = (tok('lines', x) for x in ('Total raised', 'Total costs', 'Net raised', 'Cost per dollar'))
LASTEV = 'IFERROR(INDEX(%s,MATCH(INDEX(%s,MATCH({col:next_event},%s,0))&"|"&(INDEX(%s,MATCH({col:next_event},%s,0))-1),%s,0)),"")' % (
    R('events', 'event'), R('events', 'kind'), R('events', 'event'), R('events', 'year'), R('events', 'event'), R('events', 'kind_year'))
def SB(c): return 'SUMIFS(%s,%s,{col:last_event})' % (R('events', c), R('events', 'event'))
BASE = 'IF({col:line}=%s,%s,IF({col:line}=%s,%s,IF({col:line}=%s,%s,IF({col:line}=%s,%s,IF({col:side}=2,SUMIFS(%s,%s,{col:last_event},%s,{col:line}),0)))))' % (
    TK, SB('ticket_money'), SP, SB('sponsor_received'), AU, SB('auction_income'), GI, SB('gifts_total'), R('event_costs', 'amount'), R('event_costs', 'event'), R('event_costs', 'category'))
def SHOW(v):
    return ('IF({col:side}<>0,{col:%s},IF({col:line}=%s,SUMIFS(%s,%s,1),IF({col:line}=%s,SUMIFS(%s,%s,2),IF({col:line}=%s,SUMIFS(%s,%s,1)-SUMIFS(%s,%s,2),IFERROR(SUMIFS(%s,%s,2)/SUMIFS(%s,%s,1),0)))))' % (
        v, TOTR, R('event_scenarios', v), R('event_scenarios', 'side'), TOTC, R('event_scenarios', v), R('event_scenarios', 'side'), NET, R('event_scenarios', v), R('event_scenarios', 'side'), R('event_scenarios', v), R('event_scenarios', 'side'),
        R('event_scenarios', v), R('event_scenarios', 'side'), R('event_scenarios', v), R('event_scenarios', 'side')))
tables.append(T('event_scenarios', 'Event Scenarios', 'Low, expected and high result for the next ticketed event',
    'One row per result line: type the share of last year you expect for a low, expected and high case; the next event, last year base and each case with totals, net and cost per dollar fill in.', [
    LST('line', 'Result line', 'lines', 28, required=True), C('low_f', 'Low case share of last year', 'pct', 11), C('exp_f', 'Expected share of last year', 'pct', 11), C('high_f', 'High case share of last year', 'pct', 11),
    CA('next_event', 'Next ticketed event', 'text', 'IFERROR(INDEX(%s,MATCH(MIN(%s),%s,0)),"")' % (R('events', 'event'), R('events', 'upcoming'), R('events', 'upcoming')), 22), CA('last_event', 'Same kind last year', 'text', LASTEV, 22),
    CA('side', 'Side', 'int', 'IF(OR({col:line}=%s,{col:line}=%s,{col:line}=%s,{col:line}=%s),1,IF(OR({col:line}=%s,{col:line}=%s,{col:line}=%s,{col:line}=%s),0,2))' % (TK, SP, AU, GI, TOTR, TOTC, NET, CPD_), 6),
    CA('base', 'Last year actual', 'money', 'IF({col:side}=0,0,%s)' % BASE, 12),
    CA('v_low', 'Low line', 'money', 'IF({col:side}=0,0,{col:base}*{col:low_f})', 11), CA('v_exp', 'Expected line', 'money', 'IF({col:side}=0,0,{col:base}*{col:exp_f})', 11), CA('v_high', 'High line', 'money', 'IF({col:side}=0,0,{col:base}*{col:high_f})', 11),
    CA('low', 'Low case', 'money', SHOW('v_low'), 12), CA('expected', 'Expected case', 'money', SHOW('v_exp'), 12), CA('high', 'High case', 'money', SHOW('v_high'), 12)], D.scenarios_d(), 50))
# 19 appeals ----------------------------------------------------------------
tables.append(T('appeals', 'Appeals', 'Appeals by campaign and channel', 'One row per appeal: the campaign it belongs to and the channel it uses.', [
    LST('appeal', 'Appeal', 'appeal', 26, required=True), LST('campaign', 'Campaign', 'campaign', 20), LST('channel', 'Channel', 'channel', 14)], D.appeals_d(), 50))
# 20 gala by year -----------------------------------------------------------
def GX(c, yr): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('event_result', c), R('event_result', 'kind'), GALA, R('event_result', 'year'), yr)
def GMET(yr):
    X = lambda c: GX(c, yr)
    br = [('Ticket money', X('tickets')), ('Sponsor money', X('sponsors')), ('Auction income', X('auction')), ('Gifts on the night and appeal', X('gifts')), ('Total raised', X('raised')), ('Total costs', X('costs')),
          ('Net raised', X('net')), ('Cost per dollar', 'IFERROR(%s/%s,"")' % (X('costs'), X('raised'))), ('Guests', X('guests')), ('Net per guest', 'IFERROR(%s/%s,"")' % (X('net'), X('guests'))),
          ('Staff hours', X('staff_hours')), ('Volunteer hours', X('volunteer_hours'))]
    f = '""'
    for lab, e in reversed(br): f = 'IF({col:metric}=%s,%s,%s)' % (tok('lines', lab), e, f)
    return f
tables.append(T('gala_by_year', 'Gala by Year', 'The gala year by year',
    'One row per result line: your gala this year, last year and two years ago side by side, with the change on last year.', [
    LST('metric', 'Result line', 'lines', 28, required=True),
    CA('y0', 'Current year', 'num', GMET('YEAR({today})'), 16), CA('y1', 'Previous year', 'num', GMET('YEAR({today})-1'), 16), CA('y2', 'Two years earlier', 'num', GMET('YEAR({today})-2'), 16),
    CA('change', 'Change on last year', 'pct', 'IF(AND(ISNUMBER({col:y0}),ISNUMBER({col:y1})),IF({col:y1}<>0,{col:y0}/{col:y1}-1,""),"")', 11)], D.gala_d(), 50))
def _first(key, pred):
    for t_ in tables:
        if t_['key'] == key:
            d = t_['demo']; i = next(i for i, r in enumerate(d) if pred(r)); d.insert(0, d.pop(i))
def _set(key, idcol, idv, **kw):
    for t_ in tables:
        if t_['key'] == key:
            for r in t_['demo']:
                if r[idcol] == idv: r.update(kw)
_set('sponsors', 'sponsor_id', 'SP-081', event='Fun Run 2027')
_set('event_hours', 'hours_id', 'EH-012', event='Fun Run 2027')
_first('events', lambda r: r['event_id'] == 'EV-08')
_first('sponsors', lambda r: r['event'] == D.EVN['EV-08'] and r.get('received', 0) > 0 and r.get('received') == r.get('promised'))
_first('event_gifts', lambda r: r['campaign_id'] == 'CP-17' and r['amount'] >= 250)
assert len(tables) == 20
