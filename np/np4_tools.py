"""Nonprofit suite part 4: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np4_lists import *
import np4_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
YES = '{list:yesno.yes}'
DONE = tok('estatus', 'Done'); DECL = tok('sstatus', 'Declined'); SOLD = tok('auction', 'Sold'); UNSOLD = tok('auction', 'Unsold'); GALA = tok('ekind', 'Gala')
STORY = D.EVN[D.ST['event']]            # the over-budget gala
NEXT_GALA = D.EVN['EV-11']
tools = []

# ---- lookups by the picked event name
def ER(c, ev='{in:ev}'): return 'INDEX(%s,MATCH(%s,%s,0))' % (R('event_result', c), ev, R('event_result', 'event'))
def EV(c, ev='{in:ev}'): return 'INDEX(%s,MATCH(%s,%s,0))' % (R('events', c), ev, R('events', 'event'))
def ERN(c): return 'IFERROR(%s,0)' % ER(c)
KY = '(%s&"|"&(%s-1))' % (EV('kind'), EV('year'))               # kind and year of last year's event of the same kind
def LYN(col): return 'SUMIFS(%s,%s,%s)' % (R('events', col), R('events', 'kind_year'), KY)

# ---- lookups by the picked campaign and year
M = 'MATCH({in:camp},%s,0)' % R('campaign_compare', 'label')
CID = 'INDEX(%s,%s)' % (R('campaign_compare', 'campaign_id'), M)
def CPN(c): return 'IFERROR(INDEX(%s,%s),0)' % (R('campaign_compare', c), M)
def CMP(c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('campaigns', c), CID, R('campaigns', 'campaign_id'))
LYLABEL = '(INDEX(%s,%s)&" "&(INDEX(%s,%s)-1))' % (R('campaign_compare', 'campaign'), M, R('campaign_compare', 'year'), M)
LYID = 'INDEX(%s,MATCH(%s,%s,0))' % (R('campaign_compare', 'campaign_id'), LYLABEL, R('campaign_compare', 'label'))
def GIFT(cid, extra=''): return 'SUMIFS(%s,%s,%s%s)' % (R('event_gifts', 'amount'), R('event_gifts', 'campaign_id'), cid, extra)

TOT8 = D.TOT[D.ST['event']]; TOT5 = D.TOT['EV-05']

# 1 ------------------------------------------------------------ event result card
RAISED1 = ERN('raised'); COST1 = ERN('costs')
tools.append(TOOL('event_result_card', 'Event Result Card', 'How did this event do',
    'Pick an event: tickets, sponsors, auction, gifts, costs, net, cost per dollar and net per guest against your own last year, with a verdict and a what-if on costs and money raised.', [
    IL('ev', 'Event', 'evpick', STORY), I('cost_cut', 'What if costs were cut by', 0, 'pct'), I('raise_up', 'What if money raised were higher by', 0, 'pct')], [
    O('Ticket money', 'money', ERN('tickets')), O('Sponsor money received', 'money', ERN('sponsors')), O('Auction income', 'money', ERN('auction')), O('Gifts', 'money', ERN('gifts')), O('Total raised', 'money', RAISED1),
    O('Costs', 'money', COST1), O('Budget cost', 'money', ERN('budget_cost')), O('Net raised', 'money', ERN('net')), O('Cost per dollar', 'num', 'IFERROR(%s/%s,0)' % (COST1, RAISED1)),
    O('Cost per dollar, your setting', 'num', '{set:cost_per_dollar}'), O('Net per guest', 'money', 'IFERROR(%s,"")' % ER('net_per_guest')), O('Last year net per guest, same kind', 'money', 'IFERROR(%s,"")' % ER('last_npg')),
    O('Net after the what-if change', 'money', '%s*(1+{in:raise_up})-%s*(1-{in:cost_cut})' % (RAISED1, COST1)), O('Cost per dollar after the change', 'num', 'IFERROR(%s*(1-{in:cost_cut})/(%s*(1+{in:raise_up})),0)' % (COST1, RAISED1)),
    O('Verdict', 'text', 'IFERROR(%s,"")' % ER('verdict'))],
    GR('What if', ('Costs 10 percent lower', {'cost_cut': 0.10}), ('Costs 20 percent lower', {'cost_cut': 0.20}), ('Money raised 10 percent higher', {'raise_up': 0.10}),
       ('Costs down 15, raised up 5 percent', {'cost_cut': 0.15, 'raise_up': 0.05}), ('Costs back to budget', {'cost_cut': round(1 - 48000 / TOT8['cost'], 4)}))))

# 2 ------------------------------------------------------------ ticket and benefit split
PR2 = 'IF({in:price_over}>0,{in:price_over},SUMIFS(%s,%s,{in:tt}))' % (R('ticket_types', 'price'), R('ticket_types', 'ticket'))
BE2 = 'IF({in:benefit_over}>0,{in:benefit_over},SUMIFS(%s,%s,{in:tt}))' % (R('ticket_types', 'benefit_value'), R('ticket_types', 'ticket'))
GP2 = 'MAX(0,%s-%s)' % (PR2, BE2)
tools.append(TOOL('ticket_split', 'Ticket and Benefit Split', 'How much of a ticket is a gift',
    'Pick a ticket type and quantity: the price less the value the guest gets back is the gift part, with the event total beside it. Ask your adviser what your rules need.', [
    IL('tt', 'Ticket type', 'ticket', 'Supporter'), I('qty', 'Tickets bought', 2, 'int'), I('price_over', 'Your own price each, 0 uses the price list', 0), I('benefit_over', 'Your own benefit value each, 0 uses the price list', 0), IL('ev', 'Event for the event totals', 'evpick', STORY)], [
    O('Price each', 'money', PR2), O('Benefit value each', 'money', BE2), O('Gift part each', 'money', GP2), O('Gift share of the price', 'pct', 'IFERROR(%s/%s,0)' % (GP2, PR2)), O('Total paid', 'money', '{in:qty}*%s' % PR2),
    O('Benefit value of the order', 'money', '{in:qty}*%s' % BE2), O('Gift part of the order', 'money', '{in:qty}*%s' % GP2), O('Ticket money of the event', 'money', ERN('tickets')),
    O('Gift part of the event ticket money', 'money', ERN('ticket_gift_part')), O('Benefit part of the event ticket money', 'money', ERN('benefit_value')), O('Gift share of the event ticket money', 'pct', 'IFERROR(%s/%s,0)' % (ER('ticket_gift_part'), ER('tickets'))),
    O('Verdict', 'text', '%s&" "&ROUND({in:qty}*%s,0)&" / "&ROUND({in:qty}*%s,0)' % (cb('Gift part'), GP2, PR2))],
    GR('What if', ('Table of ten', {'tt': '=' + tok('ticket', 'Table of ten'), 'qty': 1}), ('Four standard tickets', {'tt': '=' + tok('ticket', 'Standard'), 'qty': 4}), ('Community ticket', {'tt': '=' + tok('ticket', 'Community'), 'qty': 2}),
       ('Supporter at 300', {'price_over': 300}), ('Supporter with a smaller benefit', {'benefit_over': 60}))))

# 3 ------------------------------------------------------------ event cost line watcher
SH5 = {c: sum(r['amount'] for r in D.COSTL if r['event'] == D.EVN['EV-05'] and r['category'] == c) / TOT5['cost'] for c in ECAT}
BUD3 = [round(48000 * SH5[c] / 100.0) * 100 for c in ECAT]
def ACT3(i): return 'SUMIFS(%s,%s,{in:ev},%s,%s)' % (R('event_costs', 'amount'), R('event_costs', 'event'), R('event_costs', 'category'), tok('ecat', ECAT[i]))
KEYS3 = ','.join('ROUND(MAX(0,%s-{in:b%d}),0)*10+%d' % (ACT3(i), i + 1, i + 1) for i in range(9))
MAXK = 'MAX(%s)' % KEYS3
CAT3 = 'CHOOSE(MOD(%s,10),%s)' % (MAXK, ','.join(tok('ecat', c) for c in ECAT))
SUMB = '(%s)' % '+'.join('{in:b%d}' % (i + 1) for i in range(9))
SUMA = 'SUMIFS(%s,%s,{in:ev})' % (R('event_costs', 'amount'), R('event_costs', 'event'))
tools.append(TOOL('cost_line_watcher', 'Event Cost Line Watcher', 'Which cost line ran over its budget',
    'Pick an event and type its budget line for each category: the actual cost of each line is read from Event Costs, the biggest overrun is named and the verdict says which line to cut next year.', [
    IL('ev', 'Event', 'evpick', STORY)] + [I('b%d' % (i + 1), 'Budget line, ' + ECAT[i], BUD3[i]) for i in range(9)], [
    O('Over or under, %s' % ECAT[i], 'money', '%s-{in:b%d}' % (ACT3(i), i + 1)) for i in range(9)] + [
    O('Total of the budget lines', 'money', SUMB), O('Total actual cost', 'money', SUMA), O('Total over or under', 'money', '%s-%s' % (SUMA, SUMB)),
    O('Largest overrun', 'money', 'INT(%s/10)' % MAXK), O('Category of the largest overrun', 'text', 'IF(INT(%s/10)>0,%s,"")' % (MAXK, CAT3)),
    O('Verdict', 'text', 'IF(INT(%s/10)<=0,%s,%s&" "&%s&" "&%s)' % (MAXK, cb('On budget'), cb('Cut'), CAT3, cb('next year')))],
    GR('What if', ('Venue and hall budget 15000', {'b1': 15000}), ('Catering budget 22000', {'b2': 22000}), ('Catering budget 30000', {'b2': 30000}), ('Stage budget 6000', {'b3': 6000}))))

# 4 ------------------------------------------------------------ event cost per dollar
FULL4 = '(%s+{in:staff}*SUMIFS(%s,%s,{in:ev})+{in:vol}*SUMIFS(%s,%s,{in:ev}))' % (COST1, R('event_hours', 'staff_cost'), R('event_hours', 'event'), R('event_hours', 'volunteer_value'), R('event_hours', 'event'))
CPD4 = 'IFERROR(%s/%s,0)' % (FULL4, RAISED1)
tools.append(TOOL('cost_per_dollar_tool', 'Event Cost per Dollar', 'Is this event within the cost setting',
    'Fundraising cost divided by money raised for one event, with staff time and the value of volunteer hours added when you choose; it shows the cost to cut or the money to raise to reach your setting.', [
    IL('ev', 'Event', 'evpick', STORY), I('staff', 'Add the cost of staff hours, 1 for yes', 0, 'int'), I('vol', 'Add the value of volunteer hours, 1 for yes', 0, 'int')], [
    O('Money raised', 'money', RAISED1), O('Direct costs', 'money', COST1), O('Staff hours cost', 'money', 'SUMIFS(%s,%s,{in:ev})' % (R('event_hours', 'staff_cost'), R('event_hours', 'event'))),
    O('Volunteer hours value, your setting', 'money', 'SUMIFS(%s,%s,{in:ev})' % (R('event_hours', 'volunteer_value'), R('event_hours', 'event'))), O('Cost counted', 'money', FULL4), O('Cost per dollar', 'num', CPD4),
    O('Cost per dollar, your setting', 'num', '{set:cost_per_dollar}'), O('Last year cost per dollar, same kind', 'num', 'IFERROR(%s,0)' % ER('last_cpd')), O('Gap to the setting', 'num', '%s-{set:cost_per_dollar}' % CPD4),
    O('Cost allowed at the setting', 'money', '%s*{set:cost_per_dollar}' % RAISED1), O('Cost to cut to reach the setting', 'money', 'MAX(0,%s-%s*{set:cost_per_dollar})' % (FULL4, RAISED1)),
    O('Money to raise at this cost to reach the setting', 'money', 'IF({set:cost_per_dollar}>0,%s/{set:cost_per_dollar},0)' % FULL4),
    O('Verdict', 'text', 'IF(%s<={set:cost_per_dollar},%s,%s&" "&ROUND(%s-{set:cost_per_dollar},2))' % (CPD4, cb('Within the setting'), cb('Above the setting by'), CPD4))],
    GR('What if', ('Add staff hours', {'staff': 1}), ('Add staff hours and volunteers', {'staff': 1, 'vol': 1}), ('Direct costs only', {'staff': 0, 'vol': 0}))))

# 5 ------------------------------------------------------------ event net per attendee
NET5 = ERN('net'); GU5 = 'IF({in:guests}>0,{in:guests},%s)' % ERN('guests'); NPG5 = 'IFERROR(%s/%s,0)' % (NET5, GU5)
LAST5 = 'IFERROR(%s,0)' % ER('last_npg')
tools.append(TOOL('net_per_guest_tool', 'Event Net per Attendee', 'Did each guest raise more than last year',
    'Net raised divided by guests (or donors for an online day) against your own last year for the same kind of event; type the guests to test a different count.', [
    IL('ev', 'Event', 'evpick', STORY), I('guests', 'Guests, 0 uses the count from Event Result', 0, 'int'), I('tol', 'Change that counts as the same', 0.05, 'pct')], [
    O('Net raised', 'money', NET5), O('Guests or donors', 'int', GU5), O('Net per guest', 'money', NPG5), O('Last year net per guest, same kind', 'money', LAST5),
    O('Change on last year', 'pct', 'IF(%s>0,%s/%s-1,0)' % (LAST5, NPG5, LAST5)), O('Ticket money per guest', 'money', 'IFERROR(%s/%s,0)' % (ERN('tickets'), GU5)),
    O('Cost per guest', 'money', 'IFERROR(%s/%s,0)' % (ERN('costs'), GU5)), O('Gift part of tickets per guest', 'money', 'IFERROR(%s/%s,0)' % (ERN('ticket_gift_part'), GU5)),
    O('Net needed to match last year at these guests', 'money', 'MAX(0,%s*%s-%s)' % (LAST5, GU5, NET5)),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s>%s*(1+{in:tol}),%s,IF(%s<%s*(1-{in:tol}),%s,%s)))' % (LAST5, cb('Same'), NPG5, LAST5, cb('Better'), NPG5, LAST5, cb('Worse'), cb('Same')))],
    GR('What if', ('Ten more guests', {'guests': round(TOT8['seats'] + 10)}), ('Twenty more guests', {'guests': round(TOT8['seats'] + 20)}), ('Tolerance 10 percent', {'tol': 0.10}), ('Tolerance 2 percent', {'tol': 0.02}))))

# 6 ------------------------------------------------------------ event go or no-go
S1 = round(TOT8['seats'] * 1.1); PRICE6 = round(TOT8['tickets'] / TOT8['seats'], 0); SPN6 = round(TOT8['sponsors'] * 0.95, -2); AUC6 = round(TOT8['auction'] * 0.9, -2); GIF6 = round(TOT8['gifts'] * 0.95, -2)
def RAI6(seats, f): return '(%s*{in:price}+%s*({in:spons}+{in:auct}+{in:gifts}))' % (seats, f)
def CST6(seats): return '({in:fixed}+{in:var}*%s)' % seats
SEATS = {'low': '{in:s_low}', 'exp': '{in:s_exp}', 'high': '{in:s_high}'}; FAC = {'low': '{in:f_low}', 'exp': '1', 'high': '{in:f_high}'}
NETX = {k: '(%s-%s)' % (RAI6(SEATS[k], FAC[k]), CST6(SEATS[k])) for k in SEATS}
CPDX = {k: 'IFERROR(%s/%s,0)' % (CST6(SEATS[k]), RAI6(SEATS[k], FAC[k])) for k in SEATS}
tools.append(TOOL('go_no_go', 'Event Go or No-go', 'Should we book this event',
    'Type low, expected and high guests, sponsor, auction and gift money and your costs: net and cost per dollar for each case, break-even seats and a verdict.', [
    IL('ev', 'Event', 'evpick', NEXT_GALA), I('s_low', 'Guests, low case', 150, 'int'), I('s_exp', 'Guests, expected case', 185, 'int'), I('s_high', 'Guests, high case', 205, 'int'), I('price', 'Ticket money per guest', PRICE6),
    I('spons', 'Sponsor money, expected case', SPN6), I('auct', 'Auction income, expected case', AUC6), I('gifts', 'Gifts on the night and appeal, expected case', GIF6), I('fixed', 'Fixed costs (venue, stage, printing)', 40000),
    I('var', 'Cost for each guest (food, drinks, seat)', 65), I('f_low', 'Low case: sponsors, auction, gifts, share of expected', 0.85, 'pct'), I('f_high', 'High case: sponsors, auction, gifts, share of expected', 1.10, 'pct')], [
    O('Raised, low case', 'money', RAI6(SEATS['low'], FAC['low'])), O('Raised, expected case', 'money', RAI6(SEATS['exp'], FAC['exp'])), O('Raised, high case', 'money', RAI6(SEATS['high'], FAC['high'])),
    O('Costs, expected case', 'money', CST6(SEATS['exp'])), O('Net, low case', 'money', NETX['low']), O('Net, expected case', 'money', NETX['exp']), O('Net, high case', 'money', NETX['high']),
    O('Cost per dollar, low case', 'num', CPDX['low']), O('Cost per dollar, expected case', 'num', CPDX['exp']), O('Cost per dollar, high case', 'num', CPDX['high']), O('Cost per dollar, your setting', 'num', '{set:cost_per_dollar}'),
    O('Seats to break even on ticket money alone', 'int', 'IF({in:price}>{in:var},ROUNDUP({in:fixed}/({in:price}-{in:var}),0),0)'),
    O('Net per guest, expected case', 'money', 'IFERROR((%s)/{in:s_exp},0)' % NETX['exp']),
    O('Cost line to cut to reach the setting', 'money', 'MAX(0,%s-{set:cost_per_dollar}*%s)' % (CST6(SEATS['exp']), RAI6(SEATS['exp'], FAC['exp']))),
    O('Budget cost of the event', 'money', 'IFERROR(%s,0)' % EV('budget_cost')), O('Last year cost, same kind', 'money', LYN('actual_cost')),
    O('Verdict, your estimate', 'text', 'IF(%s<0,%s,IF(OR(%s<0,%s>{set:cost_per_dollar}),%s,%s))' % (NETX['exp'], ca('Do not run'), NETX['low'], CPDX['exp'], ca('Run smaller'), ca('Run')))],
    GR('What if', ('Fewer guests: 120 expected', {'s_exp': 120, 's_low': 100, 's_high': 140}), ('Fixed costs 30000', {'fixed': 30000}), ('Fixed costs 55000', {'fixed': 55000}), ('Ticket money 180', {'price': 180}), ('No sponsors', {'spons': 0}))))

# 7 ------------------------------------------------------------ break-even solver
CON7 = '({in:price}-{in:var})'
GAP7 = 'MAX(0,{in:fixed}+{in:var}*{in:guests}+{in:wanted}-({in:price}*{in:guests}+{in:spons}+{in:other}))'
XT7 = 'IF(%s>0,ROUNDUP(%s/%s,0),0)' % (CON7, GAP7, CON7); XS7 = 'IF({in:sp_avg}>0,ROUNDUP(%s/{in:sp_avg},0),0)' % GAP7
tools.append(TOOL('break_even_solver', 'Break-even Solver', 'How many tickets or sponsors close the gap',
    'Type the costs, the ticket money, the sponsor money and the net you want: the break-even guests, the guests for the net you want and the tickets or sponsors that close the gap are solved for you.', [
    I('fixed', 'Fixed costs', 40000), I('var', 'Cost for each guest', 65), I('price', 'Ticket money per guest', 150), I('spons', 'Sponsor money', 20000), I('other', 'Auction and gifts money', 10000), I('guests', 'Guests booked or expected', 185, 'int'),
    I('wanted', 'Net you want from the event', 30000), I('sp_avg', 'Average sponsor package you can sell', 4150)], [
    O('Money from each guest after the guest cost', 'money', CON7), O('Guests to break even', 'int', 'IF(%s>0,ROUNDUP(MAX(0,{in:fixed}-{in:spons}-{in:other})/%s,0),0)' % (CON7, CON7)),
    O('Guests for the net you want', 'int', 'IF(%s>0,ROUNDUP(MAX(0,{in:fixed}+{in:wanted}-{in:spons}-{in:other})/%s,0),0)' % (CON7, CON7)), O('Net at the guests you expect', 'money', '{in:guests}*%s+{in:spons}+{in:other}-{in:fixed}' % CON7),
    O('Gap to the net you want', 'money', GAP7), O('More tickets that close the gap', 'int', XT7), O('Or more sponsors that close the gap', 'int', XS7),
    O('Ticket money needed per guest at these guests', 'money', 'IF({in:guests}>0,({in:fixed}+{in:wanted}-{in:spons}-{in:other})/{in:guests}+{in:var},0)'),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s&" "&%s&" "&%s)' % (GAP7, cc('Covered'), cb('Sell'), XT7, cb('more tickets or add'), XS7, cb('sponsors')))],
    GR('What if', ('Ticket money 120', {'price': 120}), ('Ticket money 180', {'price': 180}), ('150 guests', {'guests': 150}), ('220 guests', {'guests': 220}), ('Net wanted 80000', {'wanted': 80000}), ('Fixed costs 30000', {'fixed': 30000}))))

# 8 ------------------------------------------------------------ comparison with last year
def CH8(a, b): return 'IFERROR(%s/%s-1,0)' % (a, b)
TK_C, TK_L = ERN('tickets'), 'SUMIFS(%s,%s,%s)' % (R('event_result', 'tickets'), R('event_result', 'event'), 'INDEX(%s,MATCH(%s,%s,0))' % (R('events', 'event'), KY, R('events', 'kind_year')))
SEAT_C, SEAT_L = EV('seats_sold'), LYN('seats_sold'); SP_C, SP_L = EV('sponsor_received'), LYN('sponsor_received'); CO_C, CO_L = EV('actual_cost'), LYN('actual_cost')
RA_C, RA_L = EV('raised'), LYN('raised')
WORST8 = 'MIN(%s,%s,-%s)' % (CH8(SEAT_C, SEAT_L), CH8(SP_C, SP_L), CH8(CO_C, CO_L))
tools.append(TOOL('last_year_compare', 'Event Comparison with Last Year', 'Repeat the event or change something',
    'Pick an event: seats, ticket money, sponsors, costs and net side by side with the same kind of event a year earlier, and the line to change if one is clearly worse.', [
    IL('ev', 'Event', 'evpick', STORY), I('tol', 'Change that counts as the same', 0.05, 'pct')], [
    O('Seats sold', 'int', SEAT_C), O('Seats sold last year', 'int', SEAT_L), O('Ticket money per seat', 'money', 'IFERROR(%s/%s,0)' % (EV('ticket_money'), SEAT_C)), O('Ticket money per seat last year', 'money', 'IFERROR(%s/%s,0)' % (LYN('ticket_money'), SEAT_L)),
    O('Sponsor money', 'money', SP_C), O('Sponsor money last year', 'money', SP_L), O('Costs', 'money', CO_C), O('Costs last year', 'money', CO_L), O('Raised', 'money', RA_C), O('Raised last year', 'money', RA_L),
    O('Net raised', 'money', '%s-%s' % (RA_C, CO_C)), O('Net raised last year', 'money', '%s-%s' % (RA_L, CO_L)), O('Change in seats', 'pct', CH8(SEAT_C, SEAT_L)), O('Change in sponsor money', 'pct', CH8(SP_C, SP_L)),
    O('Change in costs', 'pct', CH8(CO_C, CO_L)),
    O('Verdict', 'text', 'IF(%s>=-{in:tol},%s,IF(-%s=%s,%s,IF(%s=%s,%s,%s)))' % (WORST8, cb('Repeat'), CH8(CO_C, CO_L), WORST8, cb('Change the cost line'), CH8(SEAT_C, SEAT_L), WORST8, cb('Change ticket sales'), cb('Change the sponsor ask')))],
    GR('What if', ('Spring Gala 2025', {'ev': '=' + tok('evpick', 'Spring Gala 2025')}), ('Fun Run 2026', {'ev': '=' + tok('evpick', 'Fun Run 2026')}), ('Giving Day 2026', {'ev': '=' + tok('evpick', 'Giving Day 2026')}), ('Tolerance 15 percent', {'tol': 0.15}))))

# 9 ------------------------------------------------------------ auction item value check
SOLDFAIR = 'SUMIFS(%s,%s,{in:ev},%s,%s)' % (R('auction_items', 'fair_value'), R('auction_items', 'event'), R('auction_items', 'status'), SOLD)
SOLDSUM = 'SUMIFS(%s,%s,{in:ev},%s,%s)' % (R('auction_items', 'sold_price'), R('auction_items', 'event'), R('auction_items', 'status'), SOLD)
NITEM = 'COUNTIFS(%s,{in:ev})' % R('auction_items', 'event'); NSOLD = 'COUNTIFS(%s,{in:ev},%s,%s)' % (R('auction_items', 'event'), R('auction_items', 'status'), SOLD)
tools.append(TOOL('auction_check', 'Auction Item Value Check', 'Keep the item, lower the start or drop it',
    'Type an item fair value, starting bid and sold price (0 when unsold): the start as a share of value, the sold price against value and how the event sold overall give a verdict.', [
    IL('ev', 'Event for the totals', 'evpick', STORY), I('fair', 'Fair value of the item', 800), I('start', 'Starting bid', 400), I('sold', 'Sold price, 0 when unsold', 725)], [
    O('Starting bid as a share of value', 'pct', 'IF({in:fair}>0,{in:start}/{in:fair},0)'), O('Sold price as a share of value', 'pct', 'IF({in:fair}>0,{in:sold}/{in:fair},0)'),
    O('Items at the event', 'int', NITEM), O('Items sold', 'int', NSOLD), O('Share of items sold', 'pct', 'IFERROR(%s/%s,0)' % (NSOLD, NITEM)),
    O('Sold price as a share of value, whole event', 'pct', 'IFERROR(%s/%s,0)' % (SOLDSUM, SOLDFAIR)), O('Items unsold', 'int', 'COUNTIFS(%s,{in:ev},%s,%s)' % (R('auction_items', 'event'), R('auction_items', 'status'), UNSOLD)),
    O('Items missing a fair value', 'int', 'SUMPRODUCT((%s={in:ev})*(%s<>"")*(%s=0))' % (R('auction_items', 'event'), R('auction_items', 'item'), R('auction_items', 'fair_value'))),
    O('Suggested starting bid', 'money', 'ROUND({in:fair}*IF(IFERROR(%s/%s,0)<0.75,0.4,0.5),0)' % (NSOLD, NITEM)), O('Money missed against value', 'money', 'MAX(0,{in:fair}-{in:sold})*({in:sold}>0)'),
    O('Verdict', 'text', 'IF({in:fair}<=0,%s,IF({in:sold}>0,IF({in:sold}>=0.8*{in:fair},%s,%s),IF({in:start}>0.5*{in:fair},%s,%s)))' % (ca('Add a fair value'), ca('Keep item'), ca('Lower start'), ca('Lower start'), ca('Drop item')))],
    GR('What if', ('Sold at 40 percent of value', {'sold': 320}), ('Unsold, high start', {'sold': 0, 'start': 600}), ('Unsold, start at half', {'sold': 0, 'start': 400}), ('Sold above value', {'sold': 1015}), ('No value typed', {'fair': 0}))))

# 10 ----------------------------------------------------------- sponsor benefit tracker
BT_EV = 'COUNTIFS(%s,{in:ev},%s,">0")' % (R('benefit_tracker', 'event'), R('benefit_tracker', 'left'))
LEFTSUM = 'SUMIFS(%s,%s,{in:ev})' % (R('benefit_tracker', 'left'), R('benefit_tracker', 'event'))
DUEWIN = 'SUMIFS(%s,%s,"<="&({today}+{in:window}),%s,">="&{today})' % (R('benefit_tracker', 'left'), R('benefit_tracker', 'due_date'), R('benefit_tracker', 'due_date'))
tools.append(TOOL('benefit_tool', 'Sponsor Benefit Tracker', 'Which sponsor benefits are due',
    'Pick an event and the number of days to look ahead: sponsors with benefits left, the benefits due in that window across all events, the overdue ones and the share delivered.', [
    IL('ev', 'Event', 'evpick', 'Fun Run 2026'), I('window', 'Days to look ahead', 30, 'int')], [
    O('Sponsors with benefits left, this event', 'int', BT_EV), O('Benefits left, this event', 'int', LEFTSUM), O('Benefits owed, this event', 'int', 'SUMIFS(%s,%s,{in:ev})' % (R('benefit_tracker', 'owed'), R('benefit_tracker', 'event'))),
    O('Share delivered, this event', 'pct', 'IFERROR(1-%s/SUMIFS(%s,%s,{in:ev}),0)' % (LEFTSUM, R('benefit_tracker', 'owed'), R('benefit_tracker', 'event'))), O('Benefits due in the window, all events', 'int', DUEWIN),
    O('Benefits overdue, all events', 'int', 'SUMIFS(%s,%s,%s)' % (R('benefit_tracker', 'left'), R('benefit_tracker', 'flag'), ca('Overdue'))),
    O('Sponsors with benefits overdue', 'int', 'COUNTIFS(%s,%s)' % (R('benefit_tracker', 'flag'), ca('Overdue'))),
    O('Benefits left, all events', 'int', 'SUM(%s)' % R('benefit_tracker', 'left')),
    O('Cost of the benefits still owed, your setting', 'money', 'SUM(%s)*{set:benefit_cost}' % R('benefit_tracker', 'left')),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s&" "&%s,%s)' % (DUEWIN, cb('Deliver'), DUEWIN, cb('benefits this month'), cb('Up to date')))],
    GR('What if', ('Look ahead 60 days', {'window': 60}), ('Look ahead 90 days', {'window': 90}), ('Spring Gala 2026', {'ev': '=' + tok('evpick', 'Spring Gala 2026')}), ('Spring Gala 2027', {'ev': '=' + tok('evpick', 'Spring Gala 2027')}))))

# 11 ----------------------------------------------------------- sponsor renewal ranker
def RK(k, col): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"")' % (R('sponsor_renewal', col), k, R('sponsor_renewal', 'rank'))
ro = []
for k in range(1, 6):
    ro += [O('Rank %d sponsor' % k, 'text', RK(k, 'sponsor')), O('Rank %d last amount' % k, 'money', 'N(%s)' % RK(k, 'last_amount')), O('Rank %d verdict' % k, 'text', RK(k, 'verdict'))]
tools.append(TOOL('renewal_ranker', 'Sponsor Renewal Ranker', 'Which sponsor do I call first',
    'The five open sponsors with the most money to renew, ranked by last amount; the verdict says call this week, renew or let go; the count of calls to make within your window is shown.', [
    I('days', 'Count follow-ups due within this many days', 14, 'int')], ro + [
    O('Sponsors to call within the window', 'int', 'COUNTIFS(%s,"<="&{in:days},%s,">0")' % (R('sponsor_renewal', 'days_to'), R('sponsor_renewal', 'score'))),
    O('Renewal money at stake', 'money', 'SUMIFS(%s,%s,">0")' % (R('sponsor_renewal', 'last_amount'), R('sponsor_renewal', 'score'))),
    O('Verdict for the first sponsor', 'text', RK(1, 'verdict'))],
    GR('What if', ('Window 7 days', {'days': 7}), ('Window 30 days', {'days': 30}), ('Window 60 days', {'days': 60}), ('Window 120 days', {'days': 120}))))

# 12 ----------------------------------------------------------- sponsor package pricer
PRICE12 = 'SUMIFS(%s,%s,{in:lv},%s,{in:kd})' % (R('sponsor_levels', 'price'), R('sponsor_levels', 'level'), R('sponsor_levels', 'kind'))
BEN12 = 'SUMIFS(%s,%s,{in:lv},%s,{in:kd})' % (R('sponsor_levels', 'benefits_count'), R('sponsor_levels', 'level'), R('sponsor_levels', 'kind'))
NEED12 = 'IF({in:target}<1,%s*{in:ben_cost}/(1-{in:target}),0)' % BEN12
tools.append(TOOL('package_pricer', 'Sponsor Package Pricer', 'Is the package priced high enough',
    'Pick a level and an event kind: the price, the cost of delivering the benefits, the margin and what price keeps the margin you want.', [
    IL('lv', 'Sponsor level', 'level', 'Gold'), IL('kd', 'Event kind', 'ekind', 'Gala'), I('ben_cost', 'Cost of one benefit', 350), I('target', 'Margin you want, share of the price', 0.80, 'pct')], [
    O('Price now', 'money', PRICE12), O('Benefits in the package', 'int', BEN12), O('Cost of the benefits', 'money', '%s*{in:ben_cost}' % BEN12), O('Margin', 'money', '%s-%s*{in:ben_cost}' % (PRICE12, BEN12)),
    O('Margin share of the price', 'pct', 'IF(%s>0,1-%s*{in:ben_cost}/%s,0)' % (PRICE12, BEN12, PRICE12)),
    O('Sponsors sold at this level', 'int', 'COUNTIFS(%s,{in:lv},%s,{in:kd},%s,"<>"&%s)' % (R('sponsors', 'level'), R('sponsors', 'kind'), R('sponsors', 'status'), DECL)),
    O('Money received at this level', 'money', 'SUMIFS(%s,%s,{in:lv},%s,{in:kd})' % (R('sponsors', 'received'), R('sponsors', 'level'), R('sponsors', 'kind'))), O('Price that keeps the margin you want', 'money', 'ROUND(%s,0)' % NEED12),
    O('Rise needed', 'money', 'MAX(0,ROUND(%s,0)-%s)' % (NEED12, PRICE12)),
    O('Verdict', 'text', 'IF(ROUND(%s,0)>%s,%s&" "&ROUND(%s,0),%s)' % (NEED12, PRICE12, cb('Raise the level price to'), NEED12, cb('Fine')))],
    GR('What if', ('Presenting at the gala', {'lv': '=' + tok('level', 'Presenting')}), ('Silver at the gala', {'lv': '=' + tok('level', 'Silver')}), ('Community at the gala', {'lv': '=' + tok('level', 'Community')}),
       ('Gold at the fun run', {'kd': '=' + tok('ekind', 'Fun run')}), ('Benefit cost 500', {'ben_cost': 500}))))

# 13 ----------------------------------------------------------- campaign thermometer
GOAL13, RAI13 = CPN('goal'), CPN('raised')
DL13 = 'MAX(0,%s-{today})' % CMP('end_date'); EL13 = 'MIN(1,MAX(0,({today}-%s+1)/(%s-%s+1)))' % (CMP('start_date'), CMP('end_date'), CMP('start_date'))
PACE13 = 'IFERROR(%s/(MAX(1,MIN(28,{today}-%s+1))/7),0)' % (GIFT(CID, ',%s,">="&({today}-28),%s,"<="&{today}' % (R('event_gifts', 'date'), R('event_gifts', 'date'))), CMP('start_date'))
SHARE13 = 'IFERROR((%s+{in:pledges}*%s)/%s,0)' % (RAI13, CMP('pledged_open'), GOAL13)
ST13 = 'IF(%s=0,%s,IF(%s>=%s*1.05,%s,IF(%s>=%s*0.95,%s,%s&" "&ROUND(%s*%s-%s-{in:pledges}*%s,0))))' % (DL13, ca('Closed'), SHARE13, EL13, ca('Ahead'), SHARE13, EL13, ca('On pace'), ca('Behind by'), EL13, GOAL13, RAI13, CMP('pledged_open'))
tools.append(TOOL('thermometer', 'Campaign Thermometer', 'Are we on pace for the goal',
    'Pick a campaign and year: goal, raised, share, days left and the pace needed a week against the pace now; count pledges as raised with one input.', [
    IL('camp', 'Campaign and year', 'cpick', 'Year-End Appeal %d' % D.T0.year), I('pledges', 'Count pledges not yet paid as raised, 1 for yes', 0, 'int')], [
    O('Goal', 'money', GOAL13), O('Raised', 'money', RAI13), O('Pledged, not yet paid', 'money', CMP('pledged_open')), O('Share of the goal', 'pct', 'IFERROR(%s/%s,0)' % (RAI13, GOAL13)), O('Share with pledges counted', 'pct', SHARE13),
    O('Days left', 'int', DL13), O('Share of time gone', 'pct', EL13), O('Still to raise', 'money', 'MAX(0,%s-%s-{in:pledges}*%s)' % (GOAL13, RAI13, CMP('pledged_open'))),
    O('Pace needed a week', 'money', 'IF(%s>0,MAX(0,%s-%s-{in:pledges}*%s)/(%s/7),0)' % (DL13, GOAL13, RAI13, CMP('pledged_open'), DL13)), O('Pace now a week, gifts of the last 28 days', 'money', PACE13), O('Verdict', 'text', ST13)],
    GR('What if', ('Count the pledges', {'pledges': 1}), ('Spring Gala this year', {'camp': '=' + tok('cpick', 'Spring Gala %d' % D.T0.year)}), ('Fun Run this year', {'camp': '=' + tok('cpick', 'Fun Run %d' % D.T0.year)}),
       ('Year-End Appeal last year', {'camp': '=' + tok('cpick', 'Year-End Appeal %d' % (D.T0.year - 1))}))))

# 14 ----------------------------------------------------------- campaign finish forecast
DAYS14 = 'MAX(1,MIN(28,{today}-%s+1))' % CMP('start_date')
PACEW = 'IFERROR(%s/(%s/7),0)' % (GIFT(CID, ',%s,">="&({today}-28),%s,"<="&{today}' % (R('event_gifts', 'date'), R('event_gifts', 'date'))), DAYS14)
WL14 = '(MAX(0,%s-{today})/7)' % CMP('end_date')
LYSTART = 'INDEX(%s,MATCH(%s,%s,0))' % (R('campaigns', 'start_date'), LYID, R('campaigns', 'campaign_id'))
LYBY = GIFT(LYID, ',%s,"<="&(%s+{today}-%s)' % (R('event_gifts', 'date'), LYSTART, CMP('start_date')))
LYTOT = 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('campaign_compare', 'gifts_raised'), LYLABEL, R('campaign_compare', 'label'))
BASE14 = '(%s+%s*%s*{in:trend})' % (CPN('gifts_raised'), PACEW, WL14)
tools.append(TOOL('finish_forecast', 'Campaign Finish Forecast', 'Where will the campaign finish',
    'Today\'s pace and last year\'s own curve give a base, best and worst forecast for the campaign; a verdict names the likely finish (your estimate, not a promise).', [
    IL('camp', 'Campaign and year', 'cpick', 'Year-End Appeal %d' % D.T0.year), I('trend', 'Base trend on the pace now', 1.0, 'num'), I('best', 'Best case trend', 1.2, 'num'), I('worst', 'Worst case trend', 0.8, 'num')], [
    O('Gifts raised so far', 'money', CPN('gifts_raised')), O('Goal', 'money', CPN('goal')), O('Weeks left', 'num', WL14), O('Pace now a week, gifts of the last 28 days', 'money', PACEW),
    O('Forecast, base', 'money', BASE14), O('Forecast, best', 'money', '(%s+%s*%s*{in:best})' % (CPN('gifts_raised'), PACEW, WL14)), O('Forecast, worst', 'money', '(%s+%s*%s*{in:worst})' % (CPN('gifts_raised'), PACEW, WL14)),
    O('Last year gifts at this point', 'money', 'IFERROR(%s,0)' % LYBY), O('Last year gifts in all', 'money', LYTOT), O('Share of last year reached at this point', 'pct', 'IFERROR(%s/%s,0)' % (LYBY, LYTOT)),
    O('Forecast from last year curve', 'money', 'IF(%s>0,%s/(%s/%s),%s)' % (LYBY, CPN('gifts_raised'), LYBY, LYTOT, CPN('gifts_raised'))), O('Base forecast as a share of the goal', 'pct', 'IFERROR(%s/%s,0)' % (BASE14, CPN('goal'))),
    O('Verdict, your estimate', 'text', '%s&" "&ROUND(%s,0)&" "&%s' % (cb('Likely to finish at'), BASE14, cb('(your estimate)')))],
    GR('What if', ('Pace holds', {'trend': 1.0}), ('Pace falls 30 percent', {'trend': 0.7}), ('Pace rises 50 percent', {'trend': 1.5}), ('Spring Gala this year', {'camp': '=' + tok('cpick', 'Spring Gala %d' % D.T0.year)}))))

# 15 ----------------------------------------------------------- pledges against cash
PL15 = CMP('pledged_open')
tools.append(TOOL('pledge_cash', 'Pledges against Cash', 'How much of the campaign is still a promise',
    'Pick a campaign: cash received against pledges promised and not yet paid, and what the goal looks like if you collect the share of pledges you expect (your estimate).', [
    IL('camp', 'Campaign and year', 'cpick', 'Year-End Appeal %d' % D.T0.year), I('rate', 'Share of pledges you expect to collect, your estimate', 0.85, 'pct')], [
    O('Cash raised', 'money', CPN('raised')), O('Pledged, not yet paid', 'money', PL15), O('Cash and pledges together', 'money', '%s+%s' % (CPN('raised'), PL15)), O('Cash share of all promised money', 'pct', 'IFERROR(%s/(%s+%s),0)' % (CPN('raised'), CPN('raised'), PL15)),
    O('Pledges you expect to collect', 'money', '%s*{in:rate}' % PL15), O('Cash plus expected pledges', 'money', '%s+%s*{in:rate}' % (CPN('raised'), PL15)), O('Goal', 'money', CPN('goal')),
    O('Gap to the goal after collecting', 'money', 'MAX(0,%s-%s-%s*{in:rate})' % (CPN('goal'), CPN('raised'), PL15)), O('Pledges at risk', 'money', '%s*(1-{in:rate})' % PL15),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&ROUND(%s,0)&" "&%s,%s)' % (PL15, cb('Collect'), PL15, cb('pledged'), cb('Nothing pledged')))],
    GR('What if', ('Collect 100 percent', {'rate': 1.0}), ('Collect 70 percent', {'rate': 0.7}), ('Spring Gala this year', {'camp': '=' + tok('cpick', 'Spring Gala %d' % D.T0.year)}), ('Fun Run this year', {'camp': '=' + tok('cpick', 'Fun Run %d' % D.T0.year)}))))

# 16 ----------------------------------------------------------- gifts needed to hit the goal
GN = GIFT(CID); GC = 'COUNTIFS(%s,%s)' % (R('event_gifts', 'campaign_id'), CID)
AVG16 = 'IF({in:avg}>0,{in:avg},IFERROR(%s/%s,0))' % (GN, GC)
GAP16 = 'MAX(0,%s-%s)' % (CPN('goal'), CPN('raised')); NEED16 = 'IF(%s>0,ROUNDUP(%s/%s,0),0)' % (AVG16, GAP16, AVG16)
tools.append(TOOL('gifts_needed', 'Gift Needed to Hit the Goal', 'How many more gifts do we need',
    'Pick a campaign: the gap to the goal divided by the average gift gives the gifts needed, and the days left give the gifts needed a week; type your own average gift to test it.', [
    IL('camp', 'Campaign and year', 'cpick', 'Year-End Appeal %d' % D.T0.year), I('avg', 'Average gift you expect, 0 uses the campaign average', 0)], [
    O('Goal', 'money', CPN('goal')), O('Raised', 'money', CPN('raised')), O('Gap to the goal', 'money', GAP16), O('Average gift so far', 'money', 'IFERROR(%s/%s,0)' % (GN, GC)), O('Gifts needed at the average', 'int', NEED16),
    O('Days left', 'int', 'MAX(0,%s-{today})' % CMP('end_date')), O('Gifts needed a week', 'int', 'IF(MAX(0,%s-{today})>0,ROUNDUP(%s/(MAX(0,%s-{today})/7),0),0)' % (CMP('end_date'), NEED16, CMP('end_date'))),
    O('Gifts so far', 'int', GC), O('Campaign ends', 'date', CMP('end_date')), O('Gap after pledges are collected', 'money', 'MAX(0,%s-%s-%s)' % (CPN('goal'), CPN('raised'), CMP('pledged_open'))),
    O('Verdict', 'text', 'IF(%s<=0,%s,%s&" "&%s&" "&%s)' % (GAP16, cb('Goal reached'), cb('Need'), NEED16, cb('gifts by the end date')))],
    GR('What if', ('Average gift 100', {'avg': 100}), ('Average gift 250', {'avg': 250}), ('Average gift 500', {'avg': 500}), ('Spring Gala this year', {'camp': '=' + tok('cpick', 'Spring Gala %d' % D.T0.year)}))))

# 17 ----------------------------------------------------------- campaign comparison over three years
def CY(col, k): return 'SUMIFS(%s,%s,{in:cm},%s,YEAR({today})-%d)' % (R('campaign_compare', col), R('campaign_compare', 'campaign'), R('campaign_compare', 'year'), k)
tools.append(TOOL('three_year', 'Three-year Campaign Comparison', 'Grow, hold or retire this campaign',
    'Pick a campaign type: raised, cost, donors and new donors for this year and the two before, with the change on last year and the verdict from your cost setting.', [
    IL('cm', 'Campaign', 'campaign', 'Spring Gala')], [
    O('Raised this year', 'money', CY('raised', 0)), O('Raised last year', 'money', CY('raised', 1)), O('Raised two years ago', 'money', CY('raised', 2)), O('Cost this year', 'money', CY('cost', 0)), O('Cost last year', 'money', CY('cost', 1)),
    O('Cost two years ago', 'money', CY('cost', 2)), O('Donors this year', 'int', CY('donors', 0)), O('Donors last year', 'int', CY('donors', 1)), O('New donors this year', 'int', CY('new_donors', 0)),
    O('Cost per dollar this year', 'num', 'IFERROR(%s/%s,0)' % (CY('cost', 0), CY('raised', 0))), O('Change on last year', 'pct', 'IFERROR(%s/%s-1,0)' % (CY('raised', 0), CY('raised', 1))),
    O('Verdict', 'text', 'IFERROR(INDEX(%s,MATCH({in:cm}&" "&YEAR({today}),%s,0)),%s)' % (R('campaign_compare', 'verdict'), R('campaign_compare', 'label'), ca('Hold')))],
    GR('What if', ('Giving Day', {'cm': '=' + tok('campaign', 'Giving Day')}), ('Year-End Appeal', {'cm': '=' + tok('campaign', 'Year-End Appeal')}), ('Fun Run', {'cm': '=' + tok('campaign', 'Fun Run')}), ('Summer Camp Appeal', {'cm': '=' + tok('campaign', 'Summer Camp Appeal')}),
       ('Monthly Giving', {'cm': '=' + tok('campaign', 'Monthly Giving')}))))

# 18 ----------------------------------------------------------- cheapest method ranker
def MR(k, col): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('method_rank', col), k, R('method_rank', 'rank'))
MAXR = 'MAX(%s)' % R('method_rank', 'rank')
tools.append(TOOL('cheapest_method', 'Cheapest Method Ranker', 'Which way of raising money costs least',
    'All campaign types ranked by cost to raise one dollar over the years in the comparison; the cheapest and the dearest are named and counted against the cost you want to stay under.', [
    I('target', 'Cost per dollar you want to stay under', 0.25, 'num')], [
    O('Cheapest method', 'text', MR(1, 'campaign')), O('Cost per dollar, cheapest', 'num', 'N(%s)' % MR(1, 'cost_per_dollar')), O('Second cheapest method', 'text', MR(2, 'campaign')), O('Cost per dollar, second', 'num', 'N(%s)' % MR(2, 'cost_per_dollar')),
    O('Third cheapest method', 'text', MR(3, 'campaign')), O('Cost per dollar, third', 'num', 'N(%s)' % MR(3, 'cost_per_dollar')), O('Dearest method', 'text', MR(MAXR, 'campaign')), O('Cost per dollar, dearest', 'num', 'N(%s)' % MR(MAXR, 'cost_per_dollar')),
    O('Methods at or under your target', 'int', 'COUNTIFS(%s,"<="&{in:target})' % R('method_rank', 'cost_per_dollar')), O('Methods over your target', 'int', 'COUNTIFS(%s,">"&{in:target})' % R('method_rank', 'cost_per_dollar')),
    O('Raised by the cheapest method, all years', 'money', 'SUMIFS(%s,%s,%s)' % (R('campaign_compare', 'raised'), R('campaign_compare', 'campaign'), MR(1, 'campaign'))),
    O('Verdict, do more', 'text', '%s&" "&%s' % (cb('Do more of'), MR(1, 'campaign'))), O('Verdict, do less', 'text', '%s&" "&%s' % (cc('Do less of'), MR(MAXR, 'campaign')))],
    GR('What if', ('Target 0.10', {'target': 0.10}), ('Target 0.20', {'target': 0.20}), ('Target 0.35', {'target': 0.35}), ('Target 0.50', {'target': 0.50}))))
assert len(tools) == 18, len(tools)
