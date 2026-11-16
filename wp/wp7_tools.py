"""Wedding suite part 7: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp7_lists import *
import wp7_data as D
from wp7_tables import DONE, PLAN, OA, OB, RECV, PROM, SAV, CHOSEN, OTHER_EV, RESERVE, STAY, DAILY, ACTIV, MARRIAGE, YES, FUNDS, OPT, OPTK, TIN


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v_} for l, v_ in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
def LKUP(t, rc, kc, val): return 'INDEX(%s,MATCH(%s,%s,0))' % (R(t, rc), val, R(t, kc))


tools = []
TOTAL = 'SUM(%s)' % R('lines', 'amount')
EV = lambda label: tok('event', label)

# 1 ------------------------------------------------------------ multi-event cost planner
TOT1 = '(%s+{in:extra}-{in:cut_pct}*SUMIFS(%s,%s,%s))' % (TOTAL, R('lines', 'amount'), R('lines', 'status'), PLAN)
INV1 = 'SUMPRODUCT((SUMIFS(%s,%s,%s)>0)*%s)' % (R('lines', 'amount'), R('lines', 'event'), R('invitees', 'event'), R('invitees', 'invitees'))
tools.append(TOOL('event_planner', 'Event Cost Planner', 'What do all our events cost, and per guest',
    'Type an extra cost or a cut to the planned events; the events are added up with what is paid, what is still to pay and the cost per invitee, and the verdict gives the total.', [
    I('extra', 'Extra cost to test', 0), I('cut_pct', 'Cut to the planned events', 0, 'pct')], [
    O('Events with a cost', 'int', 'COUNTIFS(%s,">0")' % R('ecosts', 'cost')), O('Cost of the events done', 'money', 'SUMIFS(%s,%s,%s)' % (R('lines', 'amount'), R('lines', 'status'), DONE)),
    O('Cost of the events planned, after your what-if', 'money', 'SUMIFS(%s,%s,%s)*(1-{in:cut_pct})+{in:extra}' % (R('lines', 'amount'), R('lines', 'status'), PLAN)), O('Events cost total', 'money', TOT1),
    O('Invitees of the events with a cost', 'int', INV1), O('Cost per invitee', 'num', 'IFERROR(ROUND(%s/%s,2),0)' % (TOT1, INV1)),
    O('Paid so far', 'money', 'SUM(%s)' % R('lines', 'paid')), O('Still to pay', 'money', '%s-SUM(%s)' % (TOT1, R('lines', 'paid'))),
    O('Dearest event', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('ecosts', 'event'), R('ecosts', 'cost'), R('ecosts', 'cost'))),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&", "&ROUND(IFERROR(%s/%s,0),1)&" "&%s' % (v('Events cost'), TOT1, TOT1, INV1, v('per invitee')))],
    GR('What if', ('As it is', {'extra': 0, 'cut_pct': 0}), ('Add 100', {'extra': 100}), ('Add 300', {'extra': 300}), ('Cut the planned by 10%', {'cut_pct': 0.1}), ('Cut the planned by 25%', {'cut_pct': 0.25}))))

# 2 ------------------------------------------------------------ event invitee check
tools.append(TOOL('invitee_check', 'Event Invitee Check', 'Are the invitees a part of our guest list',
    'Pick an event and type how many you plan to invite, and the overlap with a second event; the tool checks the number against the guest list and counts the guests on either event.', [
    IL('event', 'Event', 'event', 'Rehearsal dinner'), I('planned', 'Invitees you plan', 30, 'int'), IL('other', 'Second event', 'event', 'Farewell brunch'), I('shared', 'Guests on both events', 25, 'int')], [
    O('Guests on your invitation list', 'int', '{set:guest_list}'), O('Invitees now entered for this event', 'int', 'IFERROR(%s,0)' % LKUP('invitees', 'invitees', 'event', '{in:event}')),
    O('Invitees you plan', 'int', '{in:planned}'), O('Share of the guest list', 'pct', 'IFERROR({in:planned}/{set:guest_list},0)'),
    O('Invitees of the second event', 'int', 'IFERROR(%s,0)' % LKUP('invitees', 'invitees', 'event', '{in:other}')), O('Guests on both events', 'int', '{in:shared}'),
    O('Guests on either event', 'int', '{in:planned}+IFERROR(%s,0)-{in:shared}' % LKUP('invitees', 'invitees', 'event', '{in:other}')),
    O('Second event guests not on this one', 'int', 'IFERROR(%s,0)-{in:shared}' % LKUP('invitees', 'invitees', 'event', '{in:other}')),
    O('Largest event as a share of the list', 'pct', 'IFERROR(MAX(%s)/{set:guest_list},0)' % R('invitees', 'invitees')),
    O('Verdict', 'text', 'IF({in:planned}>{set:guest_list},%s&" "&({in:planned}-{set:guest_list}),%s&" "&{in:planned})' % (v('Over the guest list by'), v('Invite')))],
    GR('What if', ('Thirty invited', {'planned': 30}), ('Forty-five invited', {'planned': 45}), ('The whole list', {'planned': 150}), ('Ten over the list', {'planned': 160}), ('Twenty invited', {'planned': 20}))))

# 3 ------------------------------------------------------------ guest-nights counter
N2 = '({in:before}*({in:stay}>=2)+{in:onday}*({in:stay}>=1))'
N3 = '({in:before}*({in:stay}>=3)+{in:onday}*({in:stay}>=2))'
GN = '(({in:before}+{in:onday})*{in:stay})'
RM = 'ROUNDUP(MAX({in:before},%s,%s)/{in:per_room},0)' % (N2, N3)
tools.append(TOOL('nights_counter', 'Guest-nights Counter', 'How many nights and rooms do our guests need',
    'Type the guests arriving the night before and on the day, the nights they stay and the rooms you hold; the tool counts the guests each night, the guest-nights and the rooms at the busiest night.', [
    I('before', 'Guests arriving the night before', D.STAY_BEFORE, 'int'), I('onday', 'Guests arriving on the wedding day', D.STAY_ONDAY, 'int'), I('stay', 'Nights each guest stays', 2, 'int'),
    I('per_room', 'Guests sharing one room', 2, 'int'), I('held', 'Rooms held in your block', D.ROOMS_HELD, 'int')], [
    O('Guests the night before', 'int', '{in:before}'), O('Guests on the wedding night', 'int', N2), O('Guests the night after', 'int', N3), O('Guest-nights', 'int', GN),
    O('Rooms at the busiest night', 'int', RM), O('Rooms held in your block', 'int', '{in:held}'), O('Rooms short at the busiest night', 'int', 'MAX(0,%s-{in:held})' % RM),
    O('Room-nights to fill', 'int', 'ROUNDUP(%s/{in:per_room},0)' % GN), O('Busiest night in the Guest-nights table, rooms', 'int', 'MAX(%s)' % R('nights', 'rooms')),
    O('Verdict', 'text', 'ROUND(%s,0)&" "&%s&", "&%s&" "&%s' % (GN, v('guest-nights'), RM, v('rooms')))],
    GR('What if', ('One night each', {'stay': 1}), ('Two nights each', {'stay': 2}), ('Three nights each', {'stay': 3}), ('Three guests a room', {'per_room': 3}), ('One guest a room', {'per_room': 1}))))

# 4 ------------------------------------------------------------ event calendar clash finder
D_ = R('events', 'date'); WDAY = '{set:wedding_day}'
ELIG = '(%s>0)*(ABS(%s-%s)>{in:skip})' % (D_, D_, WDAY)
NEIGH = ('(COUNTIFS(%s,">="&(%s-{in:window}),%s,"<="&(%s+{in:window}))-COUNTIFS(%s,">="&(%s-{in:window}),%s,"<="&(%s+{in:window}),%s,">="&(%s-{in:skip}),%s,"<="&(%s+{in:skip}))-1)') % (
    D_, D_, D_, D_, D_, D_, D_, D_, D_, WDAY, D_, WDAY)
FLAGN = '(%s>0)' % NEIGH
WK = '(%s-WEEKDAY(%s,2)+1)' % (D_, D_)
NEIGHW = ('(COUNTIFS(%s,">="&%s,%s,"<="&(%s+6))-COUNTIFS(%s,">="&%s,%s,"<="&(%s+6),%s,">="&(%s-{in:skip}),%s,"<="&(%s+{in:skip}))-1)') % (D_, WK, D_, WK, D_, WK, D_, WK, D_, WDAY, D_, WDAY)
NCL = 'SUMPRODUCT(%s*%s)' % (ELIG, FLAGN)
tools.append(TOOL('clash_finder', 'Event Clash Finder', 'Do two of our events clash',
    'Type how many days apart counts as a clash and how many days around the wedding day to ignore; the tool finds events inside that window or in the same week, and the verdict says Clear or Clash.', [
    I('window', 'Days apart that count as a clash', 6, 'int'), I('skip', 'Days around the wedding day to ignore', 2, 'int')], [
    O('Events checked', 'int', 'SUMPRODUCT(%s)' % ELIG), O('Events with a neighbour inside the window', 'int', NCL),
    O('Events in the same week as another', 'int', 'SUMPRODUCT(%s*((%s)>0))' % (ELIG, NEIGHW)),
    O('First clash date, or the wedding day when clear', 'date', 'IF(%s=0,{set:wedding_day},100000-SUMPRODUCT(MAX(%s*%s*(100000-%s))))' % (NCL, ELIG, FLAGN, D_)),
    O('Next event in days', 'int', 'SMALL(%s,COUNTIFS(%s,"<"&{today})+1)-{today}' % (D_, D_)), O('Events already done', 'int', 'COUNTIFS(%s,%s)' % (R('events', 'status'), DONE)),
    O('Events still to come', 'int', 'COUNTIFS(%s,%s)' % (R('events', 'status'), PLAN)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (NCL, v('Clear'), v('Clash on')))],
    GR('What if', ('Window of 3 days', {'window': 3}), ('Window of 7 days', {'window': 7}), ('Window of 14 days', {'window': 14}), ('Window of 30 days', {'window': 30}), ('Ignore only the day itself', {'window': 6, 'skip': 0}))))

# 5 ------------------------------------------------------------ event budget against the line
OPL = 'SUMIFS(%s,%s,%s)' % (R('budget', 'planned'), R('budget', 'category'), OTHER_EV)
CST5 = '(%s+{in:extra})' % TOTAL
OVER5 = 'SUMPRODUCT(--(SUMIFS(%s,%s,%s)>SUMIFS(%s,%s,%s)))' % (R('lines', 'amount'), R('lines', 'event'), R('events', 'event'), R('lines', 'planned'), R('lines', 'event'), R('events', 'event'))
tools.append(TOOL('event_line_check', 'Event Budget Check', 'Do the events fit the Other events line',
    'Type an extra event cost; the events are set against the Other events line of your budget, with what is paid, and the verdict says Within the line or Over by.', [
    I('extra', 'Extra event cost to test', 0)], [
    O('Other events line, planned', 'money', OPL), O('Other events line, committed', 'money', 'SUMIFS(%s,%s,%s)' % (R('budget', 'committed'), R('budget', 'category'), OTHER_EV)),
    O('Other events line, paid', 'money', 'SUMIFS(%s,%s,%s)' % (R('budget', 'paid'), R('budget', 'category'), OTHER_EV)), O('Events cost from the lines', 'money', CST5),
    O('Events paid', 'money', 'SUM(%s)' % R('lines', 'paid')), O('Room left in the line', 'money', '%s-%s' % (OPL, CST5)), O('Share of the line used', 'pct', 'IFERROR(%s/%s,0)' % (CST5, OPL)),
    O('Events over their own budget', 'int', OVER5), O('Planned total of the event budgets', 'money', 'SUM(%s)' % R('lines', 'planned')),
    O('Verdict', 'text', 'IF(%s<=%s,%s,%s&" "&ROUND(%s-%s,0))' % (CST5, OPL, v('Within the line'), v('Over by'), CST5, OPL))],
    GR('What if', ('As it is', {'extra': 0}), ('Add 50', {'extra': 50}), ('Add 150', {'extra': 150}), ('Add 400', {'extra': 400}), ('Take 100 out', {'extra': -100}))))

# 6 ------------------------------------------------------------ cost per guest ranker
PG = R('ecosts', 'per_guest')
def RK(k, fn='LARGE'): return 'IFERROR(INDEX(%s,MATCH(%s(%s,%d),%s,0))&" "&ROUND(%s(%s,%d),2),"")' % (R('ecosts', 'event'), fn, PG, k, PG, fn, PG, k)
CHEAP = 'SMALL(%s,COUNTIFS(%s,0)+1)' % (PG, PG)
tools.append(TOOL('cpg_ranker', 'Cost per Guest Ranker', 'Which event costs the most per guest',
    'Type the cost per invitee you accept; the events are ranked by cost per invitee, the dearest three and the cheapest are named, and the verdict names the cheapest and the dearest.', [
    I('target', 'Cost per invitee you accept, your own number', 12)], [
    O('Dearest event and cost per invitee', 'text', RK(1)), O('Second dearest', 'text', RK(2)), O('Third dearest', 'text', RK(3)),
    O('Cheapest event with a cost', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&" "&ROUND(%s,2),"")' % (R('ecosts', 'event'), CHEAP, PG, CHEAP)),
    O('Events above your number', 'int', 'COUNTIFS(%s,">"&{in:target})' % PG), O('Spread, dearest less cheapest', 'num', 'ROUND(MAX(%s)-%s,2)' % (PG, CHEAP)),
    O('Average cost per invitee, events with a cost', 'num', 'IFERROR(ROUND(%s/%s,2),0)' % (TOTAL, INV1)),
    O('Verdict', 'text', '%s&" "&INDEX(%s,MATCH(%s,%s,0))&", "&%s&" "&INDEX(%s,MATCH(MAX(%s),%s,0))' % (v('Cheapest'), R('ecosts', 'event'), CHEAP, PG, v('dearest'), R('ecosts', 'event'), PG, PG))],
    GR('What if', ('Accept 5', {'target': 5}), ('Accept 8', {'target': 8}), ('Accept 12', {'target': 12}), ('Accept 20', {'target': 20}), ('Accept 3', {'target': 3}))))

# 7 ------------------------------------------------------------ optional event adder
NEWTOT = '(%s+{in:cost})' % TOTAL
tools.append(TOOL('event_adder', 'Optional Event Adder', 'What does one more event add',
    'Type the date, the invitees and the cost of an optional event (a welcome dinner, a tea ceremony, a music night); the tool shows the effect on the Other events line and the total, and any clash.', [
    I('date', 'Date of the new event', 'today+120', 'date'), I('invitees', 'Invitees', 25, 'int'), I('cost', 'Cost', 300)], [
    O('Cost per invitee', 'num', 'IFERROR(ROUND({in:cost}/{in:invitees},2),0)'), O('Events cost with the new event', 'money', NEWTOT), O('Other events line, planned', 'money', OPL),
    O('Room left in the line after it', 'money', '%s-%s' % (OPL, NEWTOT)), O('Share of the line used after it', 'pct', 'IFERROR(%s/%s,0)' % (NEWTOT, OPL)),
    O('Invitee places across events with it', 'int', 'SUM(%s)+{in:invitees}' % R('invitees', 'invitees')), O('Invitees as a share of the guest list', 'pct', 'IFERROR({in:invitees}/{set:guest_list},0)'),
    O('Events inside the clash window of that date', 'int', 'COUNTIFS(%s,">="&({in:date}-{set:clash_days}),%s,"<="&({in:date}+{set:clash_days}))' % (R('events', 'date'), R('events', 'date'))),
    O('Days before the wedding', 'int', '{set:wedding_day}-{in:date}'),
    O('Verdict', 'text', '%s&" "&ROUND({in:cost},0)&", "&ROUND(IFERROR({in:cost}/{in:invitees},0),1)&" "&%s' % (v('Adds'), v('per invitee')))],
    GR('What if', ('A cost of 100', {'cost': 100}), ('A cost of 300', {'cost': 300}), ('A cost of 600', {'cost': 600}), ('A cost of 1000', {'cost': 1000}), ('Fifty invitees', {'invitees': 50}))))

# 8 ------------------------------------------------------------ destination cost total
PTOT = '(SUM(%s)+SUM(%s)*{set:room_rate})' % (R('party', 'flights'), R('party', 'nights'))
ADD8 = '({in:flights}+{in:nights}*{set:room_rate}+SUM(%s)+{in:extra})' % R('party', 'helped')
tools.append(TOOL('dest_total', 'Destination Cost Total', 'What does a destination wedding add',
    'Type your own flights and nights and any other cost; the tool adds the wedding party travel you cover and shows the local quotes at your exchange rate, and the verdict gives what the destination adds.', [
    I('flights', 'Your own flights for two', 920), I('nights', 'Your own nights away', 4, 'int'), I('extra', 'Other destination costs, your estimate', 0)], [
    O('Your flights', 'money', '{in:flights}'), O('Your stay', 'money', '{in:nights}*{set:room_rate}'), O('Wedding party flights and stay, all', 'money', PTOT),
    O('The couple covers for the party', 'money', 'SUM(%s)' % R('party', 'helped')), O('The party covers themselves', 'money', '%s-SUM(%s)' % (PTOT, R('party', 'helped'))),
    O('Local quotes at the base price', 'money', 'SUM(%s)' % R('dest', 'base_price')), O('Local quotes at your exchange rate', 'money', 'SUM(%s)' % R('dest', 'local_amount')),
    O('Exchange rate used', 'num', '{set:exchange_rate}'), O('Destination adds', 'money', ADD8), O('Verdict', 'text', '%s&" "&ROUND(%s,0)' % (v('Destination adds'), ADD8))],
    GR('What if', ('Two nights', {'nights': 2}), ('Four nights', {'nights': 4}), ('Seven nights', {'nights': 7}), ('Cheaper flights', {'flights': 600}), ('Dearer flights and 500 extra', {'flights': 1400, 'extra': 500}))))

# 9 ------------------------------------------------------------ exchange rate sensitivity
LOC = 'SUM(%s)' % R('dest', 'local_amount')
def AT(m): return 'IFERROR(%s/({set:exchange_rate}*(1+%s)),0)' % (LOC, m)
tools.append(TOOL('rate_sensitivity', 'Exchange Rate Sensitivity', 'What if the exchange rate moves',
    'Type the largest move you want to test; the local quotes are priced back into your currency at the rate moved down and up by that share and by half of it, and the verdict gives the range.', [
    I('move', 'Largest move of the rate to test', 0.1, 'pct')], [
    O('Exchange rate today', 'num', '{set:exchange_rate}'), O('Local quotes in local money', 'money', LOC), O('Cost at the rate moved down by the full move', 'money', AT('-{in:move}')),
    O('Cost at the rate moved down by half', 'money', AT('-{in:move}/2')), O('Cost at today\'s rate', 'money', AT('0')), O('Cost at the rate moved up by half', 'money', AT('{in:move}/2')),
    O('Cost at the rate moved up by the full move', 'money', AT('{in:move}')), O('Spread between the lowest and the highest', 'money', 'ROUND(%s-%s,0)' % (AT('-{in:move}'), AT('{in:move}'))),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&" "&%s&" "&ROUND(%s,0)' % (v('Local quotes cost'), AT('{in:move}'), v('to'), AT('-{in:move}')))],
    GR('What if', ('Move of 2%', {'move': 0.02}), ('Move of 5%', {'move': 0.05}), ('Move of 10%', {'move': 0.1}), ('Move of 15%', {'move': 0.15}), ('Move of 20%', {'move': 0.2}))))

# 10 ----------------------------------------------------------- travel guest decline uplift
FEW = 'ROUND({in:travel}*{in:extra},0)'
NEWH = '({set:headcount}-%s)' % FEW
tools.append(TOOL('decline_uplift', 'Travel Decline Uplift', 'How many fewer guests if travel is hard',
    'Type the guests who travel and the extra decline rate; the expected headcount is lowered and the number to give the caterer is shown. This is your estimate.', [
    I('travel', 'Guests who travel', D.TRAVEL_GUESTS, 'int'), I('extra', 'Extra decline rate for guests who travel, typical, edit', 0.1, 'pct'), I('seats', 'Couple and vendors who eat', 6, 'int')], [
    O('Headcount before the uplift', 'int', '{set:headcount}'), O('Expected fewer guests', 'int', FEW), O('New expected headcount', 'int', NEWH), O('Give the caterer', 'int', '%s+{in:seats}' % NEWH),
    O('Travel guests as a share of the list', 'pct', 'IFERROR({in:travel}/{set:guest_list},0)'), O('Expected headcount as a share of the list', 'pct', 'IFERROR(%s/{set:guest_list},0)' % NEWH),
    O('Yes rate of pending replies you use', 'pct', '{set:expected_yes_rate}'),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&", "&%s&" "&(%s+{in:seats})' % (v('Expect'), FEW, v('fewer guests'), v('give the caterer'), NEWH))],
    GR('What if', ('No extra declines', {'extra': 0}), ('Extra 5%', {'extra': 0.05}), ('Extra 10%', {'extra': 0.1}), ('Extra 15%', {'extra': 0.15}), ('Extra 20%', {'extra': 0.2}))))

# 11 ----------------------------------------------------------- paperwork lead-time check
OPENM = '(%s=%s)*(%s<>%s)*(%s>0)' % (R('paper', 'kind'), MARRIAGE, R('paper', 'status'), tok('tstatus', 'Done'), R('paper', 'due_date'))
FIRSTD = '(100000-SUMPRODUCT(MAX(%s*(100000-%s))))' % (OPENM, R('paper', 'due_date'))
tools.append(TOOL('paper_check', 'Paperwork Lead Check', 'When must we start our local marriage paperwork',
    'Type the lead time your local office needs, in days; the tool counts back from the first open step, and the verdict says when to start. Check it with your officiant or local office.', [
    I('lead', 'Lead time in days, your own number', 45, 'int')], [
    O('Wedding day', 'date', '{set:wedding_day}'), O('Latest start for a wedding-day deadline', 'date', '{set:wedding_day}-{in:lead}'), O('Days to that date', 'int', '{set:wedding_day}-{in:lead}-{today}'),
    O('Marriage steps still open', 'int', 'SUMPRODUCT(%s)' % OPENM), O('First open marriage step is due', 'date', FIRSTD), O('Start that step by', 'date', '%s-{in:lead}' % FIRSTD),
    O('Days to start it', 'int', '%s-{in:lead}-{today}' % FIRSTD), O('Marriage steps already late', 'int', 'SUMPRODUCT(%s*((%s-{in:lead})<{today}))' % (OPENM, R('paper', 'due_date'))),
    O('Steps done of all steps', 'pct', 'IFERROR(COUNTIFS(%s,%s)/COUNTIFS(%s,"<>"),0)' % (R('paper', 'status'), tok('tstatus', 'Done'), R('paper', 'item_id'))),
    O('Verdict', 'text', 'IF(%s-{in:lead}-{today}<0,%s&" "&-(%s-{in:lead}-{today})&" "&%s,%s&" "&(%s-{in:lead}-{today})&" "&%s)' % (FIRSTD, v('Late by'), FIRSTD, v('days'), v('Start in'), FIRSTD, v('days')))],
    GR('What if', ('Lead of 30 days', {'lead': 30}), ('Lead of 60 days', {'lead': 60}), ('Lead of 90 days', {'lead': 90}), ('Lead of 120 days', {'lead': 120}), ('Lead of 150 days', {'lead': 150}))))

# 12 ----------------------------------------------------------- party travel help
XP = '((%s+%s*{set:room_rate})*{in:help_pct})' % (R('party', 'flights'), R('party', 'nights'))
COV = 'ROUND(SUMPRODUCT(%s-(%s-{in:cap})*(%s>{in:cap})),0)' % (XP, XP, XP)
tools.append(TOOL('party_help', 'Party Travel Help', 'How much of the party travel do we cover',
    'Type the share of each trip you would cover and a cap per person; the tool compares that with what you cover now, and the verdict gives what you cover and what they cover.', [
    I('help_pct', 'Share of each trip you cover', 0.25, 'pct'), I('cap', 'Cap per person', 250)], [
    O('Party flights and stay, all', 'money', PTOT), O('You cover now', 'money', 'SUM(%s)' % R('party', 'helped')), O('Share covered now', 'pct', 'IFERROR(SUM(%s)/%s,0)' % (R('party', 'helped'), PTOT)),
    O('You would cover at your share and cap', 'money', COV), O('Change against now', 'money', '%s-SUM(%s)' % (COV, R('party', 'helped'))), O('They cover at your share and cap', 'money', '%s-%s' % (PTOT, COV)),
    O('Largest single trip', 'money', 'SUMPRODUCT(MAX(%s+%s*{set:room_rate}))' % (R('party', 'flights'), R('party', 'nights'))),
    O('People whose cover reaches the cap', 'int', 'SUMPRODUCT(--(%s>{in:cap}))' % XP),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&(%s-%s)' % (v('You cover'), COV, v('they cover'), PTOT, COV))],
    GR('What if', ('Cover 10%', {'help_pct': 0.1}), ('Cover 25%', {'help_pct': 0.25}), ('Cover 50%', {'help_pct': 0.5}), ('Cover 75%', {'help_pct': 0.75}), ('Cover all up to 600', {'help_pct': 1, 'cap': 600}))))

# 13 ----------------------------------------------------------- one big wedding against small ceremony plus a party
PGC = 'IFERROR(SUMIFS(%s,%s,%s)/%s,0)' % (R('tracks', 'big'), R('tracks', 'scales'), YES, TIN('Big wedding guests'))
BIG = '(SUM(%s)-{in:cut}*%s)' % (R('tracks', 'big'), PGC)
SML = '(SUM(%s)+{in:extra_party}*%s)' % (R('tracks', 'small'), TIN('Party food per guest'))
GBIG = '(%s-{in:cut})' % TIN('Big wedding guests')
GSML = '(%s+%s+{in:extra_party})' % (TIN('Ceremony guests'), TIN('Party guests'))
tools.append(TOOL('two_track', 'Big or Small Wedding', 'One big wedding or a small ceremony plus a party',
    'Type guests you could cut from the big wedding and guests to add to the party; both tracks are totalled from your budget and Track Inputs, and the verdict says saves or costs.', [
    I('cut', 'Guests cut from the big wedding', 0, 'int'), I('extra_party', 'Guests added to the party', 0, 'int')], [
    O('One big wedding, total', 'money', BIG), O('Small ceremony plus a party, total', 'money', SML), O('Difference, small less big', 'money', '%s-%s' % (SML, BIG)),
    O('Guests at the big wedding', 'int', GBIG), O('Guests across the ceremony and the party', 'int', GSML), O('Cost per guest, big wedding', 'money', 'IFERROR(ROUND(%s/%s,0),0)' % (BIG, GBIG)),
    O('Cost per guest, small plus party', 'money', 'IFERROR(ROUND(%s/%s,0),0)' % (SML, GSML)), O('Events, big wedding', 'int', 'COUNTIFS(%s,">0")' % R('events', 'date')),
    O('Events, small plus party', 'int', TIN('Events in the small track')), O('Small track as a share of the big', 'pct', 'IFERROR(%s/%s,0)' % (SML, BIG)),
    O('Verdict', 'text', 'IF(%s<%s,%s,%s)&" "&ROUND(ABS(%s-%s),0)' % (SML, BIG, v('Small plus party saves'), v('Small plus party costs'), SML, BIG))],
    GR('What if', ('As it is', {'cut': 0, 'extra_party': 0}), ('Cut 20 from the big', {'cut': 20}), ('Cut 40 from the big', {'cut': 40}), ('Add 30 to the party', {'extra_party': 30}), ('Add 100 to the party', {'extra_party': 100}))))

# 14 ----------------------------------------------------------- three biggest differences
def DIFF(k): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0))&": "&ROUND(INDEX(%s,MATCH(%d,%s,0)),0),"")' % (R('tracks', 'line'), k, R('tracks', 'gap_rank'), R('tracks', 'difference'), k, R('tracks', 'gap_rank'))
tools.append(TOOL('top_diffs', 'Three Biggest Differences', 'Where do the two tracks differ most',
    'Type the size of a difference you care about; the lines are ranked by how far the small ceremony plus a party differs from the big wedding, and the three largest are named.', [
    I('min_gap', 'Difference you care about', 500)], [
    O('Biggest difference', 'text', DIFF(1)), O('Second', 'text', DIFF(2)), O('Third', 'text', DIFF(3)),
    O('Lines that differ by more than your number', 'int', 'COUNTIFS(%s,">"&{in:min_gap})' % R('tracks', 'gap_abs')),
    O('Share of the total difference in the top three', 'pct', 'IFERROR((LARGE(%s,1)+LARGE(%s,2)+LARGE(%s,3))/SUM(%s),0)' % ((R('tracks', 'gap_abs'),) * 4)),
    O('Lines where the small track costs less', 'int', 'COUNTIFS(%s,"<0")' % R('tracks', 'difference')), O('Lines that stay the same', 'int', 'COUNTIFS(%s,0,%s,"<>")' % (R('tracks', 'difference'), R('tracks', 'line'))),
    O('Verdict', 'text', '%s&": "&INDEX(%s,MATCH(1,%s,0))&" "&ROUND(INDEX(%s,MATCH(1,%s,0)),0)' % (v('Biggest difference'), R('tracks', 'line'), R('tracks', 'gap_rank'), R('tracks', 'difference'), R('tracks', 'gap_rank')))],
    GR('What if', ('Care about 200', {'min_gap': 200}), ('Care about 500', {'min_gap': 500}), ('Care about 1000', {'min_gap': 1000}), ('Care about 2000', {'min_gap': 2000}), ('Care about 100', {'min_gap': 100}))))

# 15 ----------------------------------------------------------- honeymoon budget
HSUB = '({in:flights}+{in:days}*{in:stay_night}+{in:days}*{in:daily}+{in:extras})'
HTOT = '(%s+{in:reserve})' % HSUB
tools.append(TOOL('honey_budget', 'Honeymoon Budget', 'Can we afford this honeymoon',
    'Type the days, flights, stay, daily spend, other costs and a reserve; the trip is set against the honeymoon money received and promised, and the verdict says Affordable or Short by.', [
    I('days', 'Days', 10, 'int'), I('flights', 'Flights for two', 1240), I('stay_night', 'Stay per night', 150), I('daily', 'Daily spend', 90), I('extras', 'Activities, transport and insurance', 770), I('reserve', 'Reserve', 440)], [
    O('Stay', 'money', '{in:days}*{in:stay_night}'), O('Daily spend, all days', 'money', '{in:days}*{in:daily}'), O('Trip before the reserve', 'money', HSUB), O('Trip with the reserve', 'money', HTOT),
    O('Cost per day', 'money', 'IFERROR(ROUND(%s/{in:days},0),0)' % HTOT), O('Reserve as a share of the trip', 'pct', 'IFERROR({in:reserve}/%s,0)' % HSUB),
    O('Funds received', 'money', 'SUMIFS(%s,%s,%s)' % (R('hf', 'amount'), R('hf', 'status'), RECV)), O('Funds promised', 'money', 'SUMIFS(%s,%s,%s)' % (R('hf', 'amount'), R('hf', 'status'), PROM)),
    O('Gap to close', 'money', 'MAX(0,%s-%s)' % (HTOT, FUNDS)),
    O('Verdict', 'text', 'IF(%s<=%s,%s,%s&" "&ROUND(%s-%s,0))' % (HTOT, FUNDS, v('Affordable'), v('Short by'), HTOT, FUNDS))],
    GR('What if', ('Seven days', {'days': 7}), ('Ten days', {'days': 10}), ('Fourteen days', {'days': 14}), ('Five days, cheaper stay', {'days': 5, 'stay_night': 140, 'flights': 380}), ('Ten days, no activities', {'extras': 370}))))

# 16 ----------------------------------------------------------- honeymoon two options side by side
def DAYSO(o): return 'SUMPRODUCT(MAX((%s=%s)*%s))' % (R('hm', 'option'), o, R('hm', 'days'))
FA = '(%s+{in:extra_funds})' % FUNDS
tools.append(TOOL('honey_compare', 'Honeymoon Two Options', 'Which honeymoon option can we afford',
    'Type any extra money you could add; the beach week and the city minimoon are set side by side with total, cost per day and the gap against the funds received and promised.', [
    I('extra_funds', 'Extra money you could add', 0)], [
    O('Funds, received and promised, plus your extra', 'money', FA), O('Option A: beach week, total', 'money', OPT(OA)), O('Option A, days', 'int', DAYSO(OA)),
    O('Option A, cost per day', 'money', 'IFERROR(ROUND(%s/%s,0),0)' % (OPT(OA), DAYSO(OA))), O('Option A, gap', 'money', 'MAX(0,%s-%s)' % (OPT(OA), FA)),
    O('Option B: city minimoon, total', 'money', OPT(OB)), O('Option B, days', 'int', DAYSO(OB)), O('Option B, cost per day', 'money', 'IFERROR(ROUND(%s/%s,0),0)' % (OPT(OB), DAYSO(OB))),
    O('Option B, gap', 'money', 'MAX(0,%s-%s)' % (OPT(OB), FA)), O('Difference in total', 'money', '%s-%s' % (OPT(OA), OPT(OB))),
    O('Verdict', 'text', '%s&" "&IF(%s<=%s,%s,%s)&", "&%s&" "&IF(%s<=%s,%s,%s)' % (v('Option A'), OPT(OA), FA, v('affordable'), v('short'), v('Option B'), OPT(OB), FA, v('affordable'), v('short')))],
    GR('What if', ('No extra money', {'extra_funds': 0}), ('Add 500', {'extra_funds': 500}), ('Add 1000', {'extra_funds': 1000}), ('Add 1600', {'extra_funds': 1600}), ('Add 2000', {'extra_funds': 2000}))))

# 17 ----------------------------------------------------------- minimoon fallback
TOT17 = OPT('{in:option}'); FUN17 = '(%s+{in:extra_funds})' % FUNDS
PERDAY = 'IFERROR((%s+%s)/%s,0)' % (OPTK('{in:option}', STAY), OPTK('{in:option}', DAILY), DAYSO('{in:option}'))
FIXED = '(%s-%s-%s)' % (TOT17, OPTK('{in:option}', STAY), OPTK('{in:option}', DAILY))
FIT = 'MAX(0,MIN(%s,INT((%s-%s)/%s)))' % (DAYSO('{in:option}'), FUN17, FIXED, PERDAY)
tools.append(TOOL('minimoon', 'Minimoon Fallback', 'How long a trip fits the money we have',
    'Pick the option that is too dear and type any extra money; the tool keeps the fixed costs, counts the days of stay and daily spend your funds can pay for, and the verdict names the minimoon that fits.', [
    IL('option', 'Option', 'hoption', 'Option A: beach week'), I('extra_funds', 'Extra money you could add', 0)], [
    O('Funds, received and promised, plus your extra', 'money', FUN17), O('Option total', 'money', TOT17), O('Gap', 'money', 'MAX(0,%s-%s)' % (TOT17, FUN17)),
    O('Days planned', 'int', DAYSO('{in:option}')), O('Fixed costs: flights, activities, insurance, reserve', 'money', FIXED), O('Stay and daily spend for one day', 'money', 'ROUND(%s,0)' % PERDAY),
    O('Days that fit', 'int', FIT), O('Money left after those days', 'money', 'ROUND(%s-%s-%s*%s,0)' % (FUN17, FIXED, FIT, PERDAY)),
    O('Verdict', 'text', 'IF(%s<=%s,%s,%s&" "&%s&" "&%s)' % (TOT17, FUN17, v('Fits as planned'), v('Minimoon of'), FIT, v('days fits')))],
    GR('What if', ('No extra money', {'extra_funds': 0}), ('Add 300', {'extra_funds': 300}), ('Add 600', {'extra_funds': 600}), ('Add 1000', {'extra_funds': 1000}), ('Add 1600', {'extra_funds': 1600}))))

# 18 ----------------------------------------------------------- honeymoon savings pace
TOT18 = OPT('{in:option}')
FIRST18 = '(100000-SUMPRODUCT(MAX((%s={in:option})*(%s>0)*(100000-%s))))' % (R('hm', 'option'), R('hm', 'due_date'), R('hm', 'due_date'))
MON18 = 'MAX(1,(%s-{today})/30.4)' % FIRST18
GAP18 = 'MAX(0,%s-%s)' % (TOT18, FUNDS)
EXTRA18 = 'ROUND(%s*(1+{in:buffer})/%s,0)' % (GAP18, MON18)
RECVS = 'SUMIFS(%s,%s,%s)' % (R('hf', 'amount'), R('hf', 'status'), RECV)
tools.append(TOOL('savings_pace', 'Honeymoon Savings Pace', 'How much must we save a month for the honeymoon',
    'Pick the option and a margin; the tool counts the months to its first booking date and works out the extra saving a month that closes the gap after the money received and promised.', [
    IL('option', 'Option', 'hoption', 'Option A: beach week'), I('buffer', 'Margin on the gap, your own number', 0, 'pct')], [
    O('Option total', 'money', TOT18), O('Funds received', 'money', RECVS), O('Funds promised', 'money', 'SUMIFS(%s,%s,%s)' % (R('hf', 'amount'), R('hf', 'status'), PROM)),
    O('Gap after received and promised', 'money', GAP18), O('First booking date of the option', 'date', FIRST18), O('Months to that date', 'num', 'ROUND(%s,1)' % MON18),
    O('Saving a month to pay for all of it from money received', 'money', 'ROUND(MAX(0,%s-%s)/%s,0)' % (TOT18, RECVS, MON18)),
    O('Your promised savings a month, average', 'money', 'IFERROR(ROUND(SUMIFS(%s,%s,%s,%s,%s)/COUNTIFS(%s,%s,%s,%s),0),0)' % (R('hf', 'amount'), R('hf', 'status'), PROM, R('hf', 'source'), SAV, R('hf', 'status'), PROM, R('hf', 'source'), SAV)),
    O('Extra saving needed a month', 'money', EXTRA18), O('Verdict', 'text', '%s&" "&%s&" "&%s' % (v('Save'), EXTRA18, v('a month')))],
    GR('What if', ('No margin', {'buffer': 0}), ('Margin of 5%', {'buffer': 0.05}), ('Margin of 10%', {'buffer': 0.1}), ('Margin of 20%', {'buffer': 0.2}), ('Margin of 50%', {'buffer': 0.5}))))
assert len(tools) == 18
