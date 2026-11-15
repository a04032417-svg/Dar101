"""Travel agent suite part 1: the 14 calculators."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ta1_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
YES = tok('yn', 'Yes'); NO = key('yn', 'No'); YK = key('yn', 'Yes')

# 1 trip quote builder
NET1 = '({in:hotel}+{in:air}+{in:trans}+{in:tours}+{in:ins})'
GRS1 = '({in:hotel}/(1-{in:c1})+{in:air}+{in:trans}/(1-{in:c1})+{in:tours}/(1-{in:c1})+{in:ins}/(1-{in:c2}))'
MKU1 = 'IF({in:coll}=%s,%s*{set:markup_pct},0)' % (YES, NET1)
PRC1 = '(' + GRS1 + '+' + MKU1 + ')'
FEE1 = 'MAX({set:min_fee},IF({in:rep}=%s,0,{set:planning_fee})+{in:tickets}*{set:air_ticket_fee})' % YES
COM1 = '(' + GRS1 + '-' + NET1 + '+' + MKU1 + ')'
INC1 = '(' + COM1 + '+' + FEE1 + ')'
# 2 margin check
MG2 = '({in:comm}+{in:fee})'
# 3 service fee
def FV(n): return 'INDEX({range:fees.fee},%d)' % n
def FW(n): return 'INDEX({range:fees.waived_repeat},%d)' % n
def NEST(f): return 'IF({in:tt}=%s,%s,IF({in:tt}=%s,%s,IF({in:tt}=%s,%s,IF({in:tt}=%s,%s,%s))))' % (
    tok('ttype', 'Multi-destination'), f(6), tok('ttype', 'Honeymoon'), f(11), tok('ttype', 'Corporate travel'), f(10), tok('ttype', 'Group trip'), f(8) + '*{in:trav}', f(1))
PLAN3 = NEST(FV); WAI3 = NEST(FW).replace('*{in:trav}', '')
PL3 = 'IF(AND({in:rep}=%s,%s=%s),0,%s)' % (YES, WAI3, YES, PLAN3)
TOT3 = '(' + PL3 + '+{in:tickets}*' + FV(2) + '+{in:changes}*' + FV(3) + '+IF({in:rush}=%s,%s,0)+IF(AND({in:rep}=%s,%s=%s),0,{in:trav}*%s))' % (YES, FV(5), YES, FW(9), YES, FV(9))
# 4 budget check
G4 = lambda col: 'INDEX({range:price_guide.%s},{in:guide})' % col
ROOMS4 = 'ROUNDUP({in:trav}/2,0)'
HOT4 = ROOMS4 + '*{in:nights}*' + G4('hotel_night'); DAY4 = '{in:trav}*{in:nights}*' + G4('daily_budget'); AIR4 = '{in:trav}*' + G4('air_fare')
NEED4 = '(' + HOT4 + '+' + DAY4 + '+' + AIR4 + ')'
# 6 payment plan
HD6 = '({in:hotel}*{in:hdep})'; TD6 = '({in:tour}*{in:tdep})'
BOOK6 = '(' + HD6 + '+' + TD6 + '+{in:air}+{in:ins})'
FD6 = 'MIN({in:travel}-{in:hfin},{in:travel}-{in:tfin})'
# 7 win chance
BASE7 = 'IF({in:stage}=%s,1,IF({in:stage}=%s,0.2,IF({in:stage}=%s,0.4,0.02)))' % (tok('enqst', 'Won'), tok('enqst', 'New'), tok('enqst', 'Quoted'))
SRC7 = 'IF(OR({in:source}=%s,{in:source}=%s),1.4,IF(OR({in:source}=%s,{in:source}=%s,{in:source}=%s),1.2,IF(OR({in:source}=%s,{in:source}=%s,{in:source}=%s),0.8,1)))' % (
    tok('msrc', 'Referral from past client'), tok('msrc', 'Repeat client'), tok('msrc', 'Wedding planner referral'), tok('msrc', 'Partner referral'), tok('msrc', 'Corporate contact'),
    tok('msrc', 'Website and search'), tok('msrc', 'Directory listing'), tok('msrc', 'Newsletter'))
FIT7 = 'MIN(1.3,MAX(0.3,{in:fit}))'
TIME7 = 'IF({in:days}<=5,1.05,IF({in:days}<=14,0.95,IF({in:days}<=30,0.75,0.5)))'
P7 = 'IF({in:stage}=%s,1,MIN(0.95,%s*%s*%s*%s))' % (tok('enqst', 'Won'), BASE7, SRC7, FIT7, TIME7)
# 8 counter offer
GAP8 = '({in:price}-{in:budget})'
TIER8 = '({in:price}-{in:price}*{in:hshare}*{in:tier})'; DATE8 = '({in:price}*(1-{in:dsave}))'
# 9 compare
IA9 = '({in:aprice}-{in:anet}+{in:afee})'; IB9 = '({in:bprice}-{in:bnet}+{in:bfee})'
# 10 source cost
WON10 = '({in:bookings}*{in:value})'
# 11 capacity
WIN11 = '{range:capacity.week},">="&{in:start},{range:capacity.week},"<"&({in:start}+7*{in:weeks})'
FREE11 = 'SUMIFS({range:capacity.free_hours},' + WIN11 + ')'
# 12 add-on
NET12 = '({in:nights}*({in:rate}+{in:upg})+{in:trans})'
PRC12 = '({in:nights}*({in:rate}+{in:upg})/(1-{in:c1})+{in:trans}/(1-{in:c2}))'
# 14 what-if grid
GRS14 = '({in:net}/(1-{in:comm}))'; MKU14 = '({in:net}*{in:mk})'; INC14 = '(' + GRS14 + '-{in:net}+' + MKU14 + '+{in:fee})'

tools = [
    TOOL('quote_builder', 'Trip Quote Builder', 'Trip quote with mark-up, service fee and commission',
         'Type the net price of each component, the commission rates and the travellers; see the client price, fee, total quote, your commission and the host agency and advisor shares.', [
        I('hotel', 'Hotel net price', 5200), I('air', 'Flights net price', 2800), I('trans', 'Transfers net price', 260), I('tours', 'Tours and activities net price', 940), I('ins', 'Insurance net price', 210),
        I('c1', 'Commission rate of hotel, transfer and tour suppliers', 0.12, 'pct'), I('c2', 'Commission rate of the insurer', 0.20, 'pct'), I('trav', 'Travellers', 2, 'int'), I('nights', 'Nights', 8, 'int'), I('tickets', 'Air tickets to book', 2, 'int'),
        IN('coll', 'You collect the payment from the client', 'list', YK, list='yn'), IN('rep', 'Repeat client', 'list', NO, list='yn')], [
        O('Supplier net total', 'money', NET1), O('Client price before the fee', 'money', PRC1), O('Mark-up you add', 'money', MKU1), O('Service fee', 'money', FEE1), O('Total quote', 'money', PRC1 + '+' + FEE1),
        O('Expected commission', 'money', COM1), O('Agency income, commission and fee', 'money', INC1), O('Margin on the net price', 'pct', 'IFERROR(' + INC1 + '/' + NET1 + ',0)'),
        O('Price per person', 'money', 'IFERROR((' + PRC1 + '+' + FEE1 + ')/{in:trav},0)'), O('Price per person per night', 'money', 'IFERROR((' + PRC1 + '+' + FEE1 + ')/({in:trav}*{in:nights}),0)'),
        O('Host agency share of the commission', 'money', COM1 + '*{set:host_pct}'), O('Advisor payout from the commission', 'money', COM1 + '*(1-{set:host_pct})*{set:advisor_pct}'),
        O('Verdict', 'text', ('IF(IFERROR(' + INC1 + '/' + NET1 + ',0)>={set:target_margin},%s,%s)') % (ck2('Margin on target'), ck2('Margin under target')))],
         GR('What if', ('Repeat client, planning fee waived', {'rep': '={list:yn.yes}'}), ('You collect no payment', {'coll': '={list:yn.no}'}), ('Better hotel deal, 16 percent', {'c1': 0.16}), ('Larger trip, hotel 8800', {'hotel': 8800, 'trav': 4, 'air': 5600, 'tickets': 4}), ('Without insurance', {'ins': 0}))),
    TOOL('margin_check', 'Quote Margin Check', 'Margin check before a quote goes out',
         'Type the quote total, the supplier net price, the service fee and the expected commission; see the margin, whether it reaches your target and the lowest fee or price that does.', [
        I('total', 'Total quote', 14200), I('net', 'Supplier net price', 12700), I('fee', 'Service fee', 250), I('comm', 'Expected commission', 1480)], [
        O('Margin, commission and fee', 'money', MG2), O('Margin as a share of the price', 'pct', 'IFERROR(' + MG2 + '/{in:total},0)'), O('Margin on the net price', 'pct', 'IFERROR(' + MG2 + '/{in:net},0)'),
        O('Margin wanted on the net price', 'money', '{in:net}*{set:target_margin}'), O('Shortfall against the target', 'money', 'MAX(0,{in:net}*{set:target_margin}-' + MG2 + ')'),
        O('Lowest service fee that reaches the target', 'money', '{in:fee}+MAX(0,{in:net}*{set:target_margin}-' + MG2 + ')'), O('Lowest total quote if you add the shortfall as mark-up', 'money', '{in:total}+MAX(0,{in:net}*{set:target_margin}-' + MG2 + ')'),
        O('Commission as a share of the price', 'pct', 'IFERROR({in:comm}/{in:total},0)'), O('Commission wanted at your target rate', 'money', '{in:total}*{set:target_commission_pct}'),
        O('Host agency share of the commission', 'money', '{in:comm}*{set:host_pct}'),
        O('Verdict', 'text', ('IF(' + MG2 + '>={in:net}*{set:target_margin},%s,%s)') % (ck2('Quote can go out now'), ck2('Raise the fee first')))],
         GR('What if', ('Fee 400', {'fee': 400}), ('Commission 900', {'comm': 900}), ('Larger trip 32000', {'total': 32000, 'net': 28600, 'comm': 3100, 'fee': 450}), ('Airline-only trip', {'total': 3200, 'net': 3200, 'comm': 0, 'fee': 105}))),
    TOOL('fee_calc', 'Service Fee Calculator', 'Service fees for a trip from the fee schedule',
         'Pick the trip type, type the travellers, air tickets, changes and whether it is rush or a repeat client; the fees come from your Service Fee Schedule, with repeat-client waivers and the smallest fee.', [
        IN('tt', 'Trip type', 'list', key('ttype', 'Honeymoon'), list='ttype'), I('trav', 'Travellers', 2, 'int'), I('tickets', 'Air tickets to book', 2, 'int'), I('changes', 'Changes after booking', 0, 'int'),
        IN('rush', 'Rush booking, travel within 14 days', 'list', NO, list='yn'), IN('rep', 'Repeat client', 'list', NO, list='yn')], [
        O('Planning or design fee', 'money', PL3), O('Air ticket fees', 'money', '{in:tickets}*' + FV(2)), O('Change fees', 'money', '{in:changes}*' + FV(3)), O('Rush fee', 'money', 'IF({in:rush}=%s,%s,0)' % (YES, FV(5))),
        O('Document check fees', 'money', 'IF(AND({in:rep}=%s,%s=%s),0,{in:trav}*%s)' % (YES, FW(9), YES, FV(9))), O('Fees before the minimum', 'money', TOT3), O('Service fee to charge', 'money', 'MAX({set:min_fee},' + TOT3 + ')'),
        O('Fee per traveller', 'money', 'IFERROR(MAX({set:min_fee},' + TOT3 + ')/{in:trav},0)'), O('Waived because of a repeat client', 'money', 'IF({in:rep}=%s,%s-%s,0)' % (YES, PLAN3, PL3)),
        O('Fee as a share of the average trip price', 'pct', 'IFERROR(MAX({set:min_fee},' + TOT3 + ')/AVERAGEIFS({range:trips.total_price},{range:trips.is_sale},1),0)'),
        O('Verdict', 'text', ('IF(AND({in:rep}=%s,%s>0),%s,%s)') % (YES, PLAN3 + '-' + PL3, cb('Fee is waived'), cb('Fee applies')))],
         GR('What if', ('Repeat honeymoon client', {'rep': '={list:yn.yes}'}), ('Multi-destination trip', {'tt': '=' + tok('ttype', 'Multi-destination'), 'trav': 2}), ('Group of 12', {'tt': '=' + tok('ttype', 'Group trip'), 'trav': 12, 'tickets': 12}), ('Rush booking with two changes', {'rush': '={list:yn.yes}', 'changes': 2}), ('Cruise for four', {'tt': '=' + tok('ttype', 'Cruise'), 'trav': 4, 'tickets': 4}))),
    TOOL('budget_check', 'Budget Reality Check', 'Budget reality check by component for a destination',
         'Type the budget, travellers, nights and the Destination Price Guide row; see hotel, daily spend and flight costs, the gap and the hotel rate the budget can pay.', [
        I('budget', 'Budget', 9500), I('trav', 'Travellers', 2, 'int'), I('nights', 'Nights', 7, 'int'), I('guide', 'Row number in the Destination Price Guide, 1 to 24', 3, 'int')], [
        O('Destination', 'text', 'INDEX({range:price_guide.destination},{in:guide})'), O('Season', 'text', 'INDEX({range:price_guide.season},{in:guide})'), O('Budget per person', 'money', 'IFERROR({in:budget}/{in:trav},0)'),
        O('Budget per person per night', 'money', 'IFERROR({in:budget}/({in:trav}*{in:nights}),0)'), O('Hotel cost, rooms for the travellers', 'money', HOT4), O('Daily spend', 'money', DAY4), O('Flights', 'money', AIR4),
        O('What the trip needs', 'money', NEED4), O('Gap, budget less need', 'money', '{in:budget}-' + NEED4), O('Budget as a share of the need', 'pct', 'IFERROR({in:budget}/' + NEED4 + ',0)'),
        O('Hotel rate per night the budget can pay', 'money', 'IFERROR(({in:budget}-' + AIR4 + '-' + DAY4 + ')/(' + ROOMS4 + '*{in:nights}),0)'),
        O('Verdict', 'text', ('IF({in:budget}>=' + NEED4 + ',%s,IF({in:budget}>=' + NEED4 + '*0.85,%s,%s))') % (ck2('Budget is enough'), ck2('Budget is thin'), ck2('Budget is too low')))],
         GR('What if', ('Budget 14000', {'budget': 14000}), ('Budget 6000', {'budget': 6000}), ('Family of four', {'trav': 4, 'budget': 15000}), ('Ten nights', {'nights': 10}), ('Another destination, row 8', {'guide': 8}))),
    TOOL('per_person', 'Per-Person and Per-Night Price', 'Price per person and per night split by component',
         'Type the total price, travellers, nights and the main components; see the price per person, per night and per person per night, and the share and cost per person of each component.', [
        I('total', 'Total price', 14800), I('trav', 'Travellers', 4, 'int'), I('nights', 'Nights', 7, 'int'), I('hotel', 'Hotels', 7600), I('air', 'Flights', 4800), I('trans', 'Transfers', 600), I('tours', 'Tours and activities', 900)], [
        O('Price per person', 'money', 'IFERROR({in:total}/{in:trav},0)'), O('Price per night', 'money', 'IFERROR({in:total}/{in:nights},0)'), O('Price per person per night', 'money', 'IFERROR({in:total}/({in:trav}*{in:nights}),0)'),
        O('Hotels per person', 'money', 'IFERROR({in:hotel}/{in:trav},0)'), O('Flights per person', 'money', 'IFERROR({in:air}/{in:trav},0)'), O('Transfers and tours per person', 'money', 'IFERROR(({in:trans}+{in:tours})/{in:trav},0)'),
        O('Other costs and fees', 'money', '{in:total}-{in:hotel}-{in:air}-{in:trans}-{in:tours}'), O('Hotels share of the price', 'pct', 'IFERROR({in:hotel}/{in:total},0)'), O('Flights share of the price', 'pct', 'IFERROR({in:air}/{in:total},0)'),
        O('Hotel cost per night', 'money', 'IFERROR({in:hotel}/{in:nights},0)')],
         GR('What if', ('Two travellers', {'trav': 2, 'total': 8200, 'hotel': 3800, 'air': 2400}), ('Ten nights', {'nights': 10}), ('Six travellers, one more room', {'trav': 6, 'total': 21000, 'hotel': 10800, 'air': 7200}), ('No tours', {'tours': 0}))),
    TOOL('payment_plan', 'Deposit and Final Payment Plan', 'Deposit and final payment dates and amounts by component',
         'Type the booking and travel dates and each supplier price, deposit share and final payment days; see what is due at booking, each final payment date and amount and the first date you must chase.', [
        IN('booked', 'Booking date', 'date', 'today'), IN('travel', 'Travel date', 'date', 'today+150'), I('hotel', 'Hotel price', 5200), I('hdep', 'Hotel deposit share', 0.25, 'pct'), I('hfin', 'Hotel final payment, days before travel', 30, 'int'),
        I('tour', 'Tour or cruise price', 6400), I('tdep', 'Tour or cruise deposit share', 0.30, 'pct'), I('tfin', 'Tour or cruise final payment, days before travel', 75, 'int'), I('air', 'Flights, paid in full', 2800), I('ins', 'Insurance, paid in full', 240),
        I('grace', 'Days to pay the deposit', 5, 'int')], [
        O('Hotel deposit', 'money', HD6), O('Tour or cruise deposit', 'money', TD6), O('Due at booking, deposits plus flights and insurance', 'money', BOOK6), O('Deposit due on', 'date', '{in:booked}+{in:grace}'),
        O('Hotel final payment', 'money', '{in:hotel}-' + HD6), O('Hotel final payment due on', 'date', '{in:travel}-{in:hfin}'), O('Tour or cruise final payment', 'money', '{in:tour}-' + TD6), O('Tour or cruise final payment due on', 'date', '{in:travel}-{in:tfin}'),
        O('First final payment due on', 'date', FD6), O('Days from booking to the first final payment', 'int', FD6 + '-{in:booked}'), O('Total price', 'money', '{in:hotel}+{in:tour}+{in:air}+{in:ins}'),
        O('Share paid at booking', 'pct', 'IFERROR(' + BOOK6 + '/({in:hotel}+{in:tour}+{in:air}+{in:ins}),0)'),
        O('Verdict', 'text', ('IF(' + FD6 + '-{in:booked}<={set:warn_days},%s,%s)') % (ck2('Final payment is near'), ck2('Final payment is far')))],
         GR('What if', ('Travel in 60 days', {'travel': '={today}+60'}), ('Cruise only, 90 days final', {'hotel': 0, 'tfin': 90, 'tour': 9800}), ('Deposit 50 percent on the tour', {'tdep': 0.50}), ('Travel in 8 months', {'travel': '={today}+240'}))),
    TOOL('win_chance', 'Win Chance and Weighted Value', 'Win chance and weighted value of an enquiry or a quote',
         'Pick the stage and the source, type how well the budget fits the price, the days waiting, the quote value and your income on it; see the win chance and the weighted value for your pipeline.', [
        IN('stage', 'Stage', 'list', key('enqst', 'Quoted'), list='enqst'), IN('source', 'Source', 'list', key('msrc', 'Referral from past client'), list='msrc'), I('fit', 'Budget divided by your price (1 means equal)', 0.95, 'num'),
        I('days', 'Days waiting since the quote', 5, 'int'), I('value', 'Quote value', 14200), I('income', 'Your income on the trip, commission and fee', 1500)], [
        O('Chance from the stage', 'pct', BASE7), O('Source factor', 'num', SRC7), O('Budget fit factor', 'num', FIT7), O('Waiting factor', 'num', TIME7), O('Win chance', 'pct', P7),
        O('Weighted sales value', 'money', '{in:value}*' + P7), O('Weighted income', 'money', '{in:income}*' + P7), O('Income lost to the chance', 'money', '{in:income}-{in:income}*' + P7),
        O('Verdict', 'text', 'IF(%s>=0.5,%s,IF(%s>=0.3,%s,%s))' % (P7, ck2('Win chance is high'), P7, ck2('Win chance is moderate'), ck2('Win chance is low')))],
         GR('What if', ('Budget well below the price, 0.6', {'fit': 0.6}), ('Waiting 40 days', {'days': 40}), ('Found on a directory', {'source': '=' + tok('msrc', 'Directory listing')}), ('New enquiry, no quote yet', {'stage': '=' + tok('enqst', 'New')}), ('Large trip 41000', {'value': 41000, 'income': 4300}))),
    TOOL('counter_offer', 'Counter-Offer for a Low Budget', 'Counter-offer when the budget is below the quote',
         'Type the quote, the client budget, the nights, the hotel share and the savings of a lower hotel tier and of cheaper dates; see the gap, what is left after each option and which answer to offer first.', [
        I('price', 'Quote total', 14200), I('budget', 'Client budget', 11800), I('nights', 'Nights', 8, 'int'), I('trav', 'Travellers', 2, 'int'), I('hshare', 'Hotel share of the price', 0.55, 'pct'),
        I('tier', 'Saving from one hotel tier down', 0.22, 'pct'), I('dsave', 'Saving from cheaper dates', 0.15, 'pct')], [
        O('Gap', 'money', GAP8), O('Gap as a share of the quote', 'pct', 'IFERROR(' + GAP8 + '/{in:price},0)'), O('Price per night', 'money', 'IFERROR({in:price}/{in:nights},0)'),
        O('Nights that fit the budget now', 'int', 'MIN({in:nights},ROUNDDOWN(IFERROR({in:budget}/({in:price}/{in:nights}),0),0))'), O('Price with a hotel tier down', 'money', TIER8), O('Gap left after a tier down', 'money', 'MAX(0,' + TIER8 + '-{in:budget})'),
        O('Price on cheaper dates', 'money', DATE8), O('Gap left on cheaper dates', 'money', 'MAX(0,' + DATE8 + '-{in:budget})'), O('Price per person at the budget', 'money', 'IFERROR({in:budget}/{in:trav},0)'),
        O('Suggested answer', 'text', ('IF(' + GAP8 + '<=0,%s,IF(' + DATE8 + '<={in:budget},%s,IF(' + TIER8 + '<={in:budget},%s,%s)))') % (ck2('Keep the price'), ck2('Offer cheaper dates'), ck2('Offer a lower hotel tier'), ck2('Offer fewer nights')))],
         GR('What if', ('Budget 13500', {'budget': 13500}), ('Budget 9000', {'budget': 9000}), ('Cheaper dates save 25 percent', {'dsave': 0.25}), ('Small trip 4200 against 5000', {'price': 5000, 'budget': 4200, 'nights': 5}))),
    TOOL('compare', 'Price Comparison of Two Options', 'Two options side by side with price, income and margin',
         'Type the price, supplier net price and service fee of option A and option B; see the price difference, your income and margin on each and which option earns more and which costs the client less.', [
        I('aprice', 'Option A: price', 12400), I('anet', 'Option A: supplier net price', 11100), I('afee', 'Option A: service fee', 250), I('bprice', 'Option B: price', 11200), I('bnet', 'Option B: supplier net price', 10200),
        I('bfee', 'Option B: service fee', 250), I('trav', 'Travellers', 2, 'int'), I('nights', 'Nights', 7, 'int')], [
        O('Price difference, B less A', 'money', '{in:bprice}-{in:aprice}'), O('Price difference per person', 'money', 'IFERROR(({in:bprice}-{in:aprice})/{in:trav},0)'), O('Income on A, spread and fee', 'money', IA9), O('Income on B, spread and fee', 'money', IB9),
        O('Income difference, B less A', 'money', IB9 + '-' + IA9), O('Margin on net, A', 'pct', 'IFERROR(' + IA9 + '/{in:anet},0)'), O('Margin on net, B', 'pct', 'IFERROR(' + IB9 + '/{in:bnet},0)'),
        O('Price per night, A', 'money', 'IFERROR({in:aprice}/{in:nights},0)'), O('Price per night, B', 'money', 'IFERROR({in:bprice}/{in:nights},0)'),
        O('Verdict', 'text', ('IF(' + IA9 + '>' + IB9 + ',%s,IF(' + IB9 + '>' + IA9 + ',%s,%s))') % (ck2('Option A earns more'), ck2('Option B earns more'), ck2('Both earn the same')))],
         GR('What if', ('B with a fee of 450', {'bfee': 450}), ('A with a cheaper net price', {'anet': 10500}), ('Four travellers', {'trav': 4}), ('Ten nights', {'nights': 10}))),
    TOOL('source_cost', 'Cost per Enquiry by Source', 'Cost per enquiry and per booking for one source',
         'Type the spend, enquiries and bookings of one source, the average trip price and your income share; see the cost per enquiry and per booking, the conversion and whether the source pays back.', [
        I('spend', 'Spend on the source', 900), I('enq', 'Enquiries', 12, 'int'), I('bookings', 'Bookings', 3, 'int'), I('value', 'Average trip price', 15400), I('inc', 'Your income as a share of the price', 0.092, 'pct')], [
        O('Cost per enquiry', 'money', 'IFERROR({in:spend}/{in:enq},0)'), O('Cost per booking', 'money', 'IFERROR({in:spend}/{in:bookings},0)'), O('Enquiry-to-booking rate', 'pct', 'IFERROR({in:bookings}/{in:enq},0)'),
        O('Sales won', 'money', WON10), O('Sales per enquiry', 'money', 'IFERROR(' + WON10 + '/{in:enq},0)'), O('Sales per unit spent', 'num', 'IFERROR(' + WON10 + '/{in:spend},0)'),
        O('Income earned', 'money', WON10 + '*{in:inc}'), O('Income after the spend', 'money', WON10 + '*{in:inc}-{in:spend}'),
        O('Verdict', 'text', ('IF(' + WON10 + '*{in:inc}>{in:spend},%s,%s)') % (ck2('Source pays back'), ck2('Source does not pay back')))],
         GR('What if', ('Directory listing, no booking', {'spend': 600, 'enq': 6, 'bookings': 0}), ('Travel show', {'spend': 2400, 'enq': 18, 'bookings': 4}), ('Newsletter', {'spend': 150, 'enq': 9, 'bookings': 2}), ('Partner gift', {'spend': 200, 'enq': 4, 'bookings': 2, 'value': 22000}))),
    TOOL('capacity_check', 'Capacity Check for a New Trip', 'Capacity check for a new trip',
         'Type the planning start, the weeks and the hours needed; free hours come from Advisor Capacity Weeks; see if the team can take the trip and which weeks are tight.', [
        IN('start', 'Planning starts on', 'date', 'today'), I('weeks', 'Weeks of planning', 4, 'int'), I('hours', 'Hours the trip needs', 24, 'int')], [
        O('Free hours across the advisors in those weeks', 'int', FREE11), O('Hours needed per week', 'num', 'IFERROR({in:hours}/{in:weeks},0)'), O('Free hours per week, all advisors', 'num', 'IFERROR(' + FREE11 + '/{in:weeks},0)'),
        O('Share of the free hours the trip takes', 'pct', 'IFERROR({in:hours}/(' + FREE11 + '),0)'), O('Hours short', 'int', 'MAX(0,{in:hours}-(' + FREE11 + '))'),
        O('Advisor-weeks over capacity', 'int', 'COUNTIFS(' + WIN11 + ',{range:capacity.status},%s)' % cb('Over capacity')), O('Advisor-weeks that are tight', 'int', 'COUNTIFS(' + WIN11 + ',{range:capacity.status},%s)' % cb('Tight week')),
        O('Advisor-weeks with room for a new trip', 'int', 'COUNTIFS(' + WIN11 + ',{range:capacity.can_start},%s)' % cb('Fits this week')),
        O('Verdict', 'text', ('IF(' + FREE11 + '>={in:hours},%s,%s)') % (ck2('Capacity fits'), ck2('Capacity is short')))],
         GR('What if', ('Large group trip, 60 hours', {'hours': 60, 'weeks': 6}), ('Start in four weeks', {'start': '={today}+28'}), ('Quick weekend break, 6 hours', {'hours': 6, 'weeks': 1}), ('Start in six weeks', {'start': '={today}+42', 'hours': 40}))),
    TOOL('addon', 'Upgrade and Add-on Pricing', 'Extra nights, upgrade and transfers priced with commission',
         'Type the extra nights, the nightly net rate, the upgrade per night, the transfers and the commission rates; see the client price of the add-on, your extra commission and the change fee.', [
        I('nights', 'Extra nights', 2, 'int'), I('rate', 'Hotel net rate per night', 180), I('upg', 'Room upgrade net price per night', 40), I('trans', 'Extra transfers net price', 90), I('c1', 'Hotel commission rate', 0.12, 'pct'),
        I('c2', 'Transfer commission rate', 0.10, 'pct'), I('trav', 'Travellers', 2, 'int'), IN('chg', 'Change after booking, a change fee applies', 'list', YK, list='yn')], [
        O('Added supplier net price', 'money', NET12), O('Added client price', 'money', PRC12), O('Added commission', 'money', PRC12 + '-' + NET12), O('Change fee', 'money', 'IF({in:chg}=%s,%s,0)' % (YES, FV(3))),
        O('Total added for the client', 'money', PRC12 + '+IF({in:chg}=%s,%s,0)' % (YES, FV(3))), O('Added income, commission and fee', 'money', PRC12 + '-' + NET12 + '+IF({in:chg}=%s,%s,0)' % (YES, FV(3))),
        O('Commission as a share of the added price', 'pct', 'IFERROR((' + PRC12 + '-' + NET12 + ')/' + PRC12 + ',0)'), O('Added price per person', 'money', 'IFERROR(' + PRC12 + '/{in:trav},0)'),
        O('Verdict', 'text', ('IF(' + PRC12 + '>' + NET12 + ',%s,%s)') % (ck2('Add-on earns commission'), ck2('Add-on earns no commission')))],
         GR('What if', ('Four extra nights', {'nights': 4}), ('Suite upgrade 95 a night', {'upg': 95}), ('Supplier pays no commission', {'c1': 0, 'c2': 0}), ('No change fee', {'chg': '={list:yn.no}'}))),
    TOOL('expiry_planner', 'Quote Expiry Planner', 'Quote expiry and supplier price hold dates',
         'Type the send date, days valid, supplier price hold, travel date and final payment days; see the expiry, the last safe date, when to chase and the final payment date.', [
        IN('sent', 'Quote sent on', 'date', 'today'), I('valid', 'Days the quote stays valid', 14, 'int'), I('hold', 'Days the supplier holds the price', 10, 'int'), IN('travel', 'Travel date', 'date', 'today+160'), I('fdays', 'Final payment, days before travel', 75, 'int')], [
        O('Quote expires on', 'date', '{in:sent}+{in:valid}'), O('Supplier price hold ends on', 'date', '{in:sent}+{in:hold}'), O('Last safe date to book', 'date', 'MIN({in:sent}+{in:valid},{in:sent}+{in:hold})'),
        O('Chase the client on', 'date', 'MIN({in:sent}+{in:valid},{in:sent}+{in:hold})-{set:quote_chase_days}'), O('Days left to the last safe date', 'int', 'MIN({in:sent}+{in:valid},{in:sent}+{in:hold})-{today}'),
        O('Final payment due on', 'date', '{in:travel}-{in:fdays}'), O('Days from the last safe date to the final payment', 'int', '{in:travel}-{in:fdays}-MIN({in:sent}+{in:valid},{in:sent}+{in:hold})'), O('Days from today to travel', 'int', '{in:travel}-{today}'),
        O('Verdict', 'text', 'IF({in:hold}<{in:valid},%s,%s)' % (ck2('Price hold ends first'), ck2('Quote expiry ends first')))],
         GR('What if', ('Supplier holds 21 days', {'hold': 21}), ('Valid for 7 days', {'valid': 7}), ('Cruise, final 90 days', {'fdays': 90, 'travel': '={today}+300'}), ('Travel in 60 days', {'travel': '={today}+60', 'fdays': 30}))),
    TOOL('whatif', 'Mark-up and Fee What-if', 'Margin per trip for mark-up and service fee together',
         'Type a net price, commission rate, mark-up and service fee; see your income, margin on net and the mark-up that reaches the target. The grid tries mark-up and fee together.', [
        I('net', 'Supplier net price', 12000), I('comm', 'Commission rate on the client price', 0.10, 'pct'), I('mk', 'Mark-up on the net price', 0.06, 'pct'), I('fee', 'Service fee', 250), I('trav', 'Travellers', 2, 'int')], [
        O('Client price before the fee', 'money', GRS14 + '+' + MKU14), O('Total quote', 'money', GRS14 + '+' + MKU14 + '+{in:fee}'), O('Commission', 'money', GRS14 + '-{in:net}'), O('Mark-up', 'money', MKU14),
        O('Agency income', 'money', INC14), O('Margin on the net price', 'pct', 'IFERROR(' + INC14 + '/{in:net},0)'), O('Income per traveller', 'money', 'IFERROR(' + INC14 + '/{in:trav},0)'),
        O('Gap to the wanted margin', 'money', INC14 + '-{in:net}*{set:target_margin}'), O('Mark-up that reaches the target', 'pct', 'IFERROR(({in:net}*{set:target_margin}-(' + GRS14 + '-{in:net})-{in:fee})/{in:net},0)'),
        O('Verdict', 'text', ('IF(' + INC14 + '>={in:net}*{set:target_margin},%s,%s)') % (ck2('Margin on target'), ck2('Margin under target')))],
         GR('Mark-up and fee together', ('Mark-up 4, fee 150', {'mk': 0.04, 'fee': 150}), ('Mark-up 4, fee 350', {'mk': 0.04, 'fee': 350}), ('Mark-up 6, fee 150', {'mk': 0.06, 'fee': 150}), ('Mark-up 6, fee 350', {'mk': 0.06, 'fee': 350}),
            ('Mark-up 8, fee 150', {'mk': 0.08, 'fee': 150}), ('Mark-up 8, fee 350', {'mk': 0.08, 'fee': 350}), ('Net 30000, mark-up 6, fee 450', {'net': 30000, 'mk': 0.06, 'fee': 450}), ('Net 3000, mark-up 10, fee 90', {'net': 3000, 'mk': 0.10, 'fee': 90}))),
]
assert len(tools) == 14
