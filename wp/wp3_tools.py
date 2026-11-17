"""Wedding suite part 3: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp3_lists import *
import wp3_data as D
from wp3_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v_} for l, v_ in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def RND(x): return 'ROUND(%s,0)' % x
def T_(t, c_, rk, k, txt=False):
    return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))%s,%s)' % (R(t, c_), k, R(t, rk), '&""' if txt else '', '""' if txt else '0')
def HM(x): return 'INT(ROUND(%s*1440,0)/60)&":"&RIGHT("0"&MOD(ROUND(%s*1440,0),60),2)' % (x, x)
def OPT(o): return {'A': OPT_A, 'B': OPT_B, 'C': OPT_C}[o]
VE = '{in:vendor}'
def QS(col, o): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('quotes', col), R('quotes', 'vendor'), VE, R('quotes', 'option'), OPT(o))
def QC(o): return 'COUNTIFS(%s,%s,%s,%s)' % (R('quotes', 'vendor'), VE, R('quotes', 'option'), OPT(o))
def CMPS(col, key_): return 'SUMIFS(%s,%s,%s&"%s")' % (R('compare', col), R('compare', 'vkey'), VE, key_)
def CMPT(col, key_): return 'IFERROR(INDEX(%s,MATCH(%s&"%s",%s,0))&"","")' % (R('compare', col), VE, key_, R('compare', 'vkey'))
def VQ(col): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('vendors', col), VE, R('vendors', 'vendor'))
def VQT(col): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (R('vendors', col), VE, R('vendors', 'vendor'))
def VQD(col): return 'IFERROR(IF(INDEX(%s,MATCH(%s,%s,0))=0,"",INDEX(%s,MATCH(%s,%s,0))),"")' % (R('vendors', col), VE, R('vendors', 'vendor'), R('vendors', col), VE, R('vendors', 'vendor'))

tools = []
PL = lambda: None

# 1 ------------------------------------------------------------ vendor pipeline status
RK1 = lambda c_, k=1: T_('pipeline', c_, 'rank', str(k), c_ == 'category')
tools.append(TOOL('pipeline_status', 'Vendor Pipeline Status', 'Which categories still need a vendor and how long do we have',
    'Type how many days you want left before the latest booking date; every category is counted as booked, open, late or inside your buffer, and the verdict names the one to book first.', [
    I('buffer', 'Days you want left before the latest booking date', 120, 'int')], [
    O('Categories with a vendor listed', 'int', 'COUNTIFS(%s,">0")' % R('pipeline', 'vendors')), O('Vendor slots booked', 'int', 'COUNTIFS(%s,%s)' % (R('vendors', 'status'), BOOKED)),
    O('Categories still open', 'int', 'COUNTIFS(%s,">0")' % R('pipeline', 'open')), O('Open categories already past their latest booking date', 'int', 'COUNTIFS(%s,"<0")' % R('pipeline', 'days_left')),
    O('Open categories inside your buffer', 'int', 'COUNTIFS(%s,">=0",%s,"<="&{in:buffer})' % (R('pipeline', 'days_left'), R('pipeline', 'days_left'))),
    O('Category to book first', 'text', RK1('category')), O('Its latest booking date', 'date', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),"")' % (R('pipeline', 'deadline'), R('pipeline', 'rank'))),
    O('Days left for it', 'int', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),"")' % (R('pipeline', 'days_left'), R('pipeline', 'rank'))),
    O('Quotes in hand for the open categories', 'int', 'SUMIFS(%s,%s,">0")' % (R('pipeline', 'quotes_n'), R('pipeline', 'open'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">0")=0,%s,IF(%s<0,%s&" "&%s&" "&%s&", "&-%s&" "&%s,%s&" "&%s&" "&%s&" "&%s&" "&%s))' % (
        R('pipeline', 'open'), V('All categories booked'), 'INDEX(%s,MATCH(1,%s,0))' % (R('pipeline', 'days_left'), R('pipeline', 'rank')), V('Book'), RK1('category'), V('now'),
        'INDEX(%s,MATCH(1,%s,0))' % (R('pipeline', 'days_left'), R('pipeline', 'rank')), V('days late'), V('Book'), RK1('category'), V('within'),
        'INDEX(%s,MATCH(1,%s,0))' % (R('pipeline', 'days_left'), R('pipeline', 'rank')), V('days')))],
    GR('What if', ('Buffer 30 days', {'buffer': 30}), ('Buffer 60 days', {'buffer': 60}), ('Buffer 90 days', {'buffer': 90}), ('Buffer 120 days', {'buffer': 120}), ('Buffer 180 days', {'buffer': 180}))))

# 2 ------------------------------------------------------------ booking deadline ranker
def RKN(k): return T_('pipeline', 'category', 'rank', str(k), True)
def RKD(k): return T_('pipeline', 'days_left', 'rank', str(k))
tools.append(TOOL('deadline_ranker', 'Booking Deadline Ranker', 'Which open category do we decide first',
    'Type the days ahead you plan for; open categories are ranked by the days left to their latest booking date, the first three are listed and the verdict says which to decide first.', [
    I('horizon', 'Days ahead you plan for', 120, 'int')], [
    O('Decide first', 'text', RKN(1)), O('Days left, first', 'int', RKD(1)), O('Decide second', 'text', RKN(2)), O('Days left, second', 'int', RKD(2)), O('Decide third', 'text', RKN(3)), O('Days left, third', 'int', RKD(3)),
    O('Open categories whose date falls inside your plan', 'int', 'COUNTIFS(%s,"<="&{in:horizon},%s,"<>")' % (R('pipeline', 'days_left'), R('pipeline', 'category'))),
    O('Open categories whose date has passed', 'int', 'COUNTIFS(%s,"<0")' % R('pipeline', 'days_left')),
    O('Typical lead months of the first', 'int', T_('pipeline', 'lead_months', 'rank', '1')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">0")=0,%s,%s&" "&%s&" "&%s)' % (R('pipeline', 'open'), V('All categories booked'), V('Decide'), RKN(1), V('first')))],
    GR('What if', ('Plan 30 days', {'horizon': 30}), ('Plan 60 days', {'horizon': 60}), ('Plan 120 days', {'horizon': 120}), ('Plan 180 days', {'horizon': 180}), ('Plan 365 days', {'horizon': 365}))))

# 3 ------------------------------------------------------------ true-cost comparison
def TA(o): return 'IF(%s=0,0,%s+ROUND(%s*{in:extra_tip},0))' % (QC(o), QS('true_total', o), QS('base_price', o))
def BIG(o): return 'IF(%s=0,1000000000,%s+ROUND(%s*{in:extra_tip},0))' % (QC(o), QS('true_total', o), QS('base_price', o))
LOW3 = 'MIN(%s,%s,%s)' % (BIG('A'), BIG('B'), BIG('C'))
IDX3 = 'IF(%s=%s,1,IF(%s=%s,2,3))' % (BIG('A'), LOW3, BIG('B'), LOW3)
LOWOPT = 'CHOOSE(%s,%s,%s,%s)' % (IDX3, OPT_A, OPT_B, OPT_C)
tools.append(TOOL('true_cost', 'True-Cost Comparison', 'Which quote is really the cheapest and which is best value',
    'Pick a vendor and an extra tip share; each quote shows its service charge, taxes, delivery, overtime, travel and tip, and the verdict names the best value and the lowest price.', [
    IL('vendor', 'Vendor', 'vname', 'Photographer'), I('extra_tip', 'Extra tip share added to every option, optional', 0, 'pct')], [
    O('Option A true total', 'money', TA('A')), O('Option B true total', 'money', TA('B')), O('Option C true total', 'money', TA('C')),
    O('Lowest true total', 'money', LOW3), O('Lowest price option', 'text', LOWOPT), O('Best value option, on your weights', 'text', T_('winners', 'best_value', 'vendor', VE, True)),
    O('Best value true total', 'money', T_('winners', 'best_total', 'vendor', VE)), O('Best value above the lowest price', 'money', '%s-%s' % (T_('winners', 'best_total', 'vendor', VE), LOW3)),
    O('Extras over the base price in the best value quote', 'money', CMPS('lead_extras', '|1')),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&%s' % (V('Best value'), T_('winners', 'best_value', 'vendor', VE, True), V('lowest price'), LOWOPT))],
    GR('What if', ('No extra tip', {'extra_tip': 0}), ('Tip 5%', {'extra_tip': 0.05}), ('Tip 10%', {'extra_tip': 0.10}), ('Tip 15%', {'extra_tip': 0.15}), ('Tip 20%', {'extra_tip': 0.20}))))

# 4 ------------------------------------------------------------ weighted score ranker
def SC4(o): return 'ROUND(100*({in:price_weight}*SUMIFS(%s,%s,%s,%s,%s)+(1-{in:price_weight})*SUMIFS(%s,%s,%s,%s,%s)),1)' % (
    R('compare', 'p_raw'), R('compare', 'vendor'), VE, R('compare', 'option'), OPT(o), R('compare', 'r_raw'), R('compare', 'vendor'), VE, R('compare', 'option'), OPT(o))
BEST4 = 'IF(AND(%s>=%s,%s>=%s),%s,IF(%s>=%s,%s,%s))' % (SC4('A'), SC4('B'), SC4('A'), SC4('C'), OPT_A, SC4('B'), SC4('C'), OPT_B, OPT_C)
tools.append(TOOL('score_ranker', 'Weighted Score Ranker', 'Which quote fits us best',
    'Pick a vendor and the weight of price; the rest follows Scoring Weights. Each option scores out of 100 and the verdict names the best fit.', [
    IL('vendor', 'Vendor', 'vname', 'Photographer'), I('price_weight', 'Weight of price, your own number', 0.35, 'pct')], [
    O('Option A score', 'num', SC4('A')), O('Option B score', 'num', SC4('B')), O('Option C score', 'num', SC4('C')),
    O('Best fit, on your price weight', 'text', BEST4), O('Best score', 'num', 'MAX(%s,%s,%s)' % (SC4('A'), SC4('B'), SC4('C'))),
    O('Lead over the next option, points', 'num', 'ROUND(2*MAX(%s,%s,%s)+MIN(%s,%s,%s)-%s-%s-%s,1)' % (SC4('A'), SC4('B'), SC4('C'), SC4('A'), SC4('B'), SC4('C'), SC4('A'), SC4('B'), SC4('C'))),
    O('Winner on the Scoring Weights table', 'text', T_('winners', 'best_value', 'vendor', VE, True)),
    O('Quotes for this vendor', 'int', 'COUNTIFS(%s,%s)' % (R('quotes', 'vendor'), VE)),
    O('Verdict', 'text', '%s&" "&%s' % (V('Best fit'), BEST4))],
    GR('What if', ('Price counts 10%', {'price_weight': 0.1}), ('Price counts 35%', {'price_weight': 0.35}), ('Price counts 50%', {'price_weight': 0.5}), ('Price counts 70%', {'price_weight': 0.7}), ('Price counts 90%', {'price_weight': 0.9}))))

# 5 ------------------------------------------------------------ price against fit
TT1, TT2 = CMPS('true_total', '|1'), CMPS('true_total', '|2'); F1, F2 = CMPS('fit', '|1'), CMPS('fit', '|2')
CHEAP = 'MIN(%s,%s)' % (TT1, TT2); PRICY = 'MAX(%s,%s)' % (TT1, TT2)
FPR = 'IF(%s>=%s,%s,%s)' % (TT1, TT2, F1, F2); FCH = 'IF(%s>=%s,%s,%s)' % (TT1, TT2, F2, F1)
PTS = '(%s-%s)' % (FPR, FCH); EXTRA5 = '(%s-%s)' % (PRICY, CHEAP)
tools.append(TOOL('price_fit', 'Price against Fit', 'Is the better fit worth the extra cost',
    'Pick a vendor and the most you would pay for each extra point of fit; the top two quotes on your weights are compared on price and fit, and the verdict says Pay more or Take the cheaper.', [
    IL('vendor', 'Vendor', 'vname', 'Photographer'), I('max_per_point', 'Most you would pay for one extra fit point', 150)], [
    O('Leading quote, true total', 'money', TT1), O('Second quote, true total', 'money', TT2), O('Leading quote, fit rating', 'int', F1), O('Second quote, fit rating', 'int', F2),
    O('Cheaper of the two, true total', 'money', CHEAP), O('Extra cost of the dearer quote', 'money', EXTRA5), O('Fit points gained by paying more', 'int', PTS),
    O('Extra cost for each fit point', 'money', 'IF(%s>0,ROUND(%s/%s,0),0)' % (PTS, EXTRA5, PTS)), O('Your limit for each fit point', 'money', '{in:max_per_point}'),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<=0,%s,IF(%s/%s<={in:max_per_point},%s&" "&ROUND(%s,0)&" "&%s&" "&%s&" "&%s,%s)))' % (
        TT2, V('Only one quote'), PTS, V('Take the cheaper'), EXTRA5, PTS, V('Pay'), EXTRA5, V('more for'), PTS, V('points'), V('Take the cheaper')))],
    GR('What if', ('Limit 25 a point', {'max_per_point': 25}), ('Limit 50 a point', {'max_per_point': 50}), ('Limit 100 a point', {'max_per_point': 100}), ('Limit 150 a point', {'max_per_point': 150}), ('Limit 300 a point', {'max_per_point': 300}))))

# 6 ------------------------------------------------------------ quote negotiation lever
WN = lambda c_, txt=False: T_('winners', c_, 'vendor', VE, txt)
TT2_ = WN('second_total'); ASK = WN('drop_needed')
tools.append(TOOL('negotiation', 'Quote Negotiation Lever', 'How much must the second quote drop to win',
    'Pick a vendor and your biggest realistic discount; the closed form gives the drop that lets the second quote win on your weights, and the verdict says whom to ask.', [
    IL('vendor', 'Vendor', 'vname', 'Videographer'), I('max_discount', 'Biggest discount you would ask for', 0.10, 'pct')], [
    O('Leading quote', 'text', CMPT('label', '|1')), O('Second quote', 'text', CMPT('label', '|2')), O('Leading score', 'num', CMPS('score', '|1')), O('Second score', 'num', CMPS('score', '|2')),
    O('Second quote, true total', 'money', TT2_), O('Price score the second quote needs, 1 is the lowest price', 'num', 'IFERROR(ROUND(%s,2),0)' % WN('need_price')),
    O('Drop that makes it win', 'money', 'IFERROR(%s+0,0)' % ASK), O('That drop as a share of its total', 'pct', 'IF(ISNUMBER(%s),%s/%s,0)' % (ASK, ASK, TT2_)),
    O('Second quote after the drop', 'money', 'IF(ISNUMBER(%s),%s-%s,%s)' % (ASK, TT2_, ASK, TT2_)), O('Your biggest discount', 'pct', '{in:max_discount}'),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(NOT(ISNUMBER(%s)),%s,IF(%s/%s<={in:max_discount},%s&" "&%s&" "&%s&" "&%s,%s&" "&ROUND(100*%s/%s,0)&" "&%s)))' % (
        TT2_, V('Only one quote'), ASK, V('Cannot win on price alone'), ASK, TT2_, V('Ask'), CMPT('label', '|2'), V('to drop'), ASK, V('Needs a drop of'), ASK, TT2_, V('percent, ask for less')))],
    GR('What if', ('Ask for up to 2%', {'max_discount': 0.02}), ('Ask for up to 5%', {'max_discount': 0.05}), ('Ask for up to 10%', {'max_discount': 0.10}), ('Ask for up to 15%', {'max_discount': 0.15}), ('Ask for up to 25%', {'max_discount': 0.25}))))

# 7 ------------------------------------------------------------ overtime exposure
RATE = lambda name: 'SUMIFS(%s,%s,%s,%s,%s)' % (R('contracts', 'amount'), R('contracts', 'vendor'), VT(name), R('contracts', 'kind'), K_OT)
RUN_END = 'SUMPRODUCT(MAX((%s<>"")*(%s+%s/1440)))*24' % (R('run', 'step_id'), R('run', 'start'), R('run', 'minutes'))
OVER = 'MAX(0,%s-{set:venue_end_hour})' % RUN_END
ALLR = 'SUMIFS(%s,%s,%s)' % (R('contracts', 'amount'), R('contracts', 'kind'), K_OT)
TOT7 = '((%s+{in:extra_hours})*%s)' % (OVER, ALLR)
tools.append(TOOL('overtime', 'Overtime Exposure', 'What could overtime cost if the day runs long',
    'Type extra hours on top of what the run of show runs past the venue hours; every overtime rate in your contracts is added up and the verdict gives the most overtime could cost.', [
    I('extra_hours', 'Extra hours the day might run over, your estimate', 1, 'num')], [
    O('Venue hours end, 24-hour clock', 'num', '{set:venue_end_hour}'), O('Run of show ends, 24-hour clock, 24 is midnight', 'num', 'ROUND(%s,2)' % RUN_END), O('Hours the plan already runs over', 'num', 'ROUND(%s,2)' % OVER),
    O('Total hours of overtime to plan for', 'num', 'ROUND(%s+{in:extra_hours},2)' % OVER), O('Venue overtime rate per hour', 'money', RATE('Venue')), O('Band or DJ overtime rate per hour', 'money', RATE('Band or DJ')),
    O('Photographer overtime rate per hour', 'money', RATE('Photographer')), O('Day-of coordinator overtime rate per hour', 'money', RATE('Day-of coordinator')), O('All recorded overtime rates per hour', 'money', ALLR),
    O('Overtime estimates in the chosen quotes', 'money', 'SUMIFS(%s,%s,%s)' % (R('quotes', 'overtime'), R('quotes', 'chosen'), YES)),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)' % (V('Overtime up to'), TOT7))],
    GR('What if', ('No extra hour', {'extra_hours': 0}), ('Half an hour', {'extra_hours': 0.5}), ('One hour', {'extra_hours': 1}), ('Two hours', {'extra_hours': 2}), ('Three hours', {'extra_hours': 3}))))

# 8 ------------------------------------------------------------ hidden extras finder
def QX(col): return 'SUMIFS(%s,%s,%s,%s,{in:option})' % (R('quotes', col), R('quotes', 'vendor'), VE, R('quotes', 'option'))
EXT8 = '(%s+{in:add_extra})' % QX('extras')
tools.append(TOOL('hidden_extras', 'Hidden Extras Finder', 'What does this quote really add on top of the base price',
    'Pick a vendor and an option and type any extra cost you find; service charge, taxes, delivery, overtime, travel and tip are listed and the verdict says what the extras add.', [
    IL('vendor', 'Vendor', 'vname', 'Caterer'), IL('option', 'Option', 'option', 'Option A'), I('add_extra', 'An extra cost you find, your estimate', 0)], [
    O('Base price', 'money', QX('base_price')), O('Service charge', 'money', QX('service_amt')), O('Taxes', 'money', QX('tax_amt')), O('Delivery', 'money', QX('delivery')), O('Overtime estimate', 'money', QX('overtime')),
    O('Travel', 'money', QX('travel')), O('Expected tip', 'money', QX('tip_amt')), O('True total, with your extra cost', 'money', '%s+{in:add_extra}' % QX('true_total')), O('Extras over the base price', 'money', EXT8),
    O('Extras as a share of the base price', 'pct', 'IF(%s>0,%s/%s,0)' % (QX('base_price'), EXT8, QX('base_price'))),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&" "&%s&" "&{in:option}' % (V('Extras add'), EXT8, V('to')))],
    GR('What if', ('No extra cost', {'add_extra': 0}), ('Extra 100', {'add_extra': 100}), ('Extra 250', {'add_extra': 250}), ('Extra 500', {'add_extra': 500}), ('Extra 1000', {'add_extra': 1000}))))

# 9 ------------------------------------------------------------ plan fit check
CAT9 = 'INDEX(%s,MATCH(%s,%s,0))' % (R('vendors', 'category'), VE, R('vendors', 'vendor'))
PLN9 = 'SUMIFS(%s,%s,%s)' % (R('budget', 'planned'), R('budget', 'category'), CAT9)
COM9 = 'SUMIFS(%s,%s,%s)' % (R('budget', 'committed'), R('budget', 'category'), CAT9)
OWN9 = 'SUMIFS(%s,%s,%s)' % (R('vendors', 'contract_total'), R('vendors', 'vendor'), VE)
QT9 = 'SUMIFS(%s,%s,%s,%s,{in:option})' % (R('quotes', 'true_total'), R('quotes', 'vendor'), VE, R('quotes', 'option'))
ROOM9 = '(%s+{in:extra_budget}-(%s-%s)-%s)' % (PLN9, COM9, OWN9, QT9)
tools.append(TOOL('plan_fit', 'Plan Fit Check', 'Does this quote fit its budget line',
    'Pick a vendor and an option and type money you could move in; the true total is set against its budget line after other bookings: Fits the line or Over by.', [
    IL('vendor', 'Vendor', 'vname', 'Videographer'), IL('option', 'Option', 'option', 'Option A'), I('extra_budget', 'Money you could move into the line', 0)], [
    O('Budget category', 'text', 'IFERROR(%s&"","")' % CAT9), O('Planned in the line', 'money', PLN9), O('Committed in the line', 'money', COM9), O('Of which this vendor, if booked', 'money', OWN9),
    O('Room in the line before the quote, with your money', 'money', '%s+{in:extra_budget}-(%s-%s)' % (PLN9, COM9, OWN9)), O('True total of the quote', 'money', QT9), O('Room left after the quote', 'money', ROOM9),
    O('Budget not yet committed, all lines', 'money', 'SUM(%s)-SUM(%s)' % (R('budget', 'planned'), R('budget', 'committed'))),
    O('Budget not yet committed after the quote', 'money', 'SUM(%s)-SUM(%s)-%s+%s' % (R('budget', 'planned'), R('budget', 'committed'), QT9, OWN9)),
    O('Verdict', 'text', 'IF(%s>=0,%s,%s&" "&ROUND(-%s,0))' % (ROOM9, V('Fits the line'), V('Over by'), ROOM9))],
    GR('What if', ('No money moved', {'extra_budget': 0}), ('Move in 100', {'extra_budget': 100}), ('Move in 250', {'extra_budget': 250}), ('Move in 500', {'extra_budget': 500}), ('Move in 1000', {'extra_budget': 1000}))))

# 10 ----------------------------------------------------------- contract completeness
LEN10 = lambda c_: 'IF(LEN(%s)>0,%s,%s)' % (VQT(c_), YES, NO)
FD10 = 'IF(%s="",%s,%s)' % (VQD('final_pay_date'), NO, YES)
MISS10 = 'IF(LEN(%s)=0,%s,IF(LEN(%s)=0,%s,IF(%s="",%s,IF(AND({in:need_arrival}=1,LEN(%s)=0),%s,""))))' % (
    VQT('included'), V('what is included'), VQT('cancel_terms'), V('cancellation terms'), VQD('final_pay_date'), V('final payment date'), VQT('arrival_note'), V('arrival time'))
tools.append(TOOL('completeness', 'Contract Completeness Check', 'Has every booked vendor given us the terms we need',
    'Pick a vendor and say if the arrival time counts (1 or 0); included items, cancellation, final payment date and arrival are checked and the verdict names what is missing.', [
    IL('vendor', 'Vendor', 'vname', 'Cake baker'), I('need_arrival', 'Arrival time needed: 1 yes, 0 no', 1, 'int')], [
    O('What is included recorded', 'text', LEN10('included')), O('Cancellation terms recorded', 'text', LEN10('cancel_terms')), O('Final payment date recorded', 'text', FD10), O('Arrival and set-up recorded', 'text', LEN10('arrival_note')),
    O('Terms found for this vendor, of 4', 'int', VQ('terms_found')), O('Booked vendors', 'int', 'SUM(%s)' % R('vendors', 'booked')),
    O('Booked vendors with every term needed', 'int', 'IF({in:need_arrival}=1,COUNTIFS(%s,1,%s,4),COUNTIFS(%s,1,%s,3))' % (R('vendors', 'booked'), R('vendors', 'terms_found'), R('vendors', 'booked'), R('vendors', 'core_found'))),
    O('Terms still missing across all vendors', 'int', 'SUM(%s)-SUM(%s)' % (R('vendors', 'terms_needed'), R('vendors', 'terms_found'))),
    O('Vendors missing a cancellation term', 'int', 'SUM(%s)' % R('vendors', 'missing_cancel')),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s="",%s,%s&" "&%s&" "&%s&" "&{in:vendor}))' % (VQ('booked'), V('Not booked yet'), MISS10, V('Complete'), V('Missing'), MISS10, V('for')))],
    GR('What if', ('Arrival not needed', {'need_arrival': 0}), ('Arrival needed', {'need_arrival': 1}))))

# 11 ----------------------------------------------------------- contract deadline countdown
def DK(c_, k, txt=False): return T_('deadlines', c_, 'seq', str(k), txt)
def DL(k): return '%s&": "&%s&", "&%s&" "&%s' % (DK('vendor', k, True), DK('kind', k, True), DK('days_left', k), V('days'))
tools.append(TOOL('countdown', 'Contract Deadline Countdown', 'What is the next date we must act on',
    'Type your red and amber limits in days; the next dates across contracts, payments and quotes are listed with the days left, counted as red, amber or green, and the verdict says what to act on first.', [
    I('red', 'Days left for red', 14, 'int'), I('amber', 'Days left for amber', 30, 'int')], [
    O('Next date, first', 'date', DK('next_all', 1)), O('First, what and days left', 'text', DL(1)), O('Next date, second', 'date', DK('next_all', 2)), O('Second, what and days left', 'text', DL(2)),
    O('Next date, third', 'date', DK('next_all', 3)), O('Third, what and days left', 'text', DL(3)), O('Next date, fourth', 'date', DK('next_all', 4)), O('Fourth, what and days left', 'text', DL(4)),
    O('Next date, fifth', 'date', DK('next_all', 5)), O('Fifth, what and days left', 'text', DL(5)),
    O('Red among the next ten', 'int', 'COUNTIFS(%s,"<=10",%s,"<="&{in:red})' % (R('deadlines', 'seq'), R('deadlines', 'days_left'))),
    O('Amber among the next ten', 'int', 'COUNTIFS(%s,"<=10",%s,">"&{in:red},%s,"<="&{in:amber})' % (R('deadlines', 'seq'), R('deadlines', 'days_left'), R('deadlines', 'days_left'))),
    O('Green among the next ten', 'int', 'COUNTIFS(%s,"<=10",%s,">"&{in:amber})' % (R('deadlines', 'seq'), R('deadlines', 'days_left'))),
    O('Items overdue now', 'int', 'COUNTIFS(%s,%s)' % (R('deadlines', 'flag'), V('Overdue'))),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&" "&%s&" "&%s' % (V('Act on'), DK('vendor', 1, True), DK('kind', 1, True), V('in'), '%s&" "&%s' % (DK('days_left', 1), V('days'))))],
    GR('What if', ('Red 7, amber 14', {'red': 7, 'amber': 14}), ('Red 14, amber 30', {'red': 14, 'amber': 30}), ('Red 21, amber 45', {'red': 21, 'amber': 45}), ('Red 30, amber 60', {'red': 30, 'amber': 60}), ('Red 45, amber 90', {'red': 45, 'amber': 90}))))

# 12 ----------------------------------------------------------- final headcount alarm
FHC = lambda name: 'SUMIFS(%s,%s,%s,%s,%s)' % (R('contracts', 'item_date'), R('contracts', 'vendor'), VT(name), R('contracts', 'kind'), K_FHC)
HC_N = 'COUNTIFS(%s,%s,%s,">="&{today})' % (R('contracts', 'kind'), K_FHC, R('contracts', 'item_date'))
FBV = lambda name: 'SUMIFS(%s,%s,%s,%s,%s,%s,"<>"&%s)' % (R('schedule', 'amount_due'), R('schedule', 'vendor'), VT(name), R('schedule', 'kind'), FB, R('schedule', 'status'), PAID)
FIRSTHC = 'IFERROR(SMALL(%s,1),"")' % R('deadlines', 'hc_next')
tools.append(TOOL('headcount_alarm', 'Final Headcount Alarm', 'When must we give the final headcount and what number',
    'Type your headcount, the caterer price per guest and the alarm days; contract count dates are listed and the verdict says what to send and how long you have.', [
    I('headcount', 'Headcount forecast, your estimate', 118, 'int'), I('per_guest', 'Caterer price per guest, from your quote', 74), I('alarm_days', 'Days left that trigger the alarm', 21, 'int')], [
    O('Caterer needs the count by', 'date', 'IF(%s=0,"",%s)' % (FHC('Caterer'), FHC('Caterer'))), O('Venue needs the count by', 'date', 'IF(%s=0,"",%s)' % (FHC('Venue'), FHC('Venue'))),
    O('Rentals needs the count by', 'date', 'IF(%s=0,"",%s)' % (FHC('Rentals'), FHC('Rentals'))), O('Cake baker needs the count by', 'date', 'IF(%s=0,"",%s)' % (FHC('Cake baker'), FHC('Cake baker'))),
    O('First final headcount date', 'date', FIRSTHC), O('Days left to it', 'int', 'IFERROR(SMALL(%s,1)-{today},"")' % R('deadlines', 'hc_next')), O('Vendors who need the count', 'int', HC_N),
    O('Caterer bill at your headcount', 'money', '{in:headcount}*{in:per_guest}'), O('Caterer contract total', 'money', 'SUMIFS(%s,%s,%s)' % (R('vendors', 'contract_total'), R('vendors', 'vendor'), VT('Caterer'))),
    O('Bill less the contract total', 'money', '{in:headcount}*{in:per_guest}-SUMIFS(%s,%s,%s)' % (R('vendors', 'contract_total'), R('vendors', 'vendor'), VT('Caterer'))),
    O('Final balances still to pay to those vendors', 'money', '%s+%s+%s+%s' % (FBV('Caterer'), FBV('Venue'), FBV('Rentals'), FBV('Cake baker'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(SMALL(%s,1)-{today}<={in:alarm_days},%s&" "&{in:headcount}&" "&%s&" "&%s,%s&" "&{in:headcount}&" "&%s&" "&%s&" "&%s&" "&%s))' % (
        HC_N, V('No count date ahead'), R('deadlines', 'hc_next'), V('Send'), V('now to'), HC_N, V('Send'), V('to'), HC_N, V('vendors in'), 'SMALL(%s,1)-{today}&" "&%s' % (R('deadlines', 'hc_next'), V('days'))))],
    GR('What if', ('90 guests', {'headcount': 90}), ('105 guests', {'headcount': 105}), ('118 guests', {'headcount': 118}), ('130 guests', {'headcount': 130}), ('150 guests', {'headcount': 150}))))

# 13 ----------------------------------------------------------- cancellation exposure
DAYS13 = '({set:wedding_day}-{today}-{in:cancel_in})'
DEP_ALL = 'SUMIFS(%s,%s,%s)' % (R('schedule', 'amount_paid'), R('schedule', 'kind'), DEP); PAID_ALL = 'SUM(%s)' % R('schedule', 'amount_paid')
RISK13 = '(%s+IF(%s<{set:refund_days},%s-%s,0))' % (DEP_ALL, DAYS13, PAID_ALL, DEP_ALL)
VDEP = 'SUMIFS(%s,%s,%s,%s,%s)' % (R('schedule', 'amount_paid'), R('schedule', 'vendor'), VE, R('schedule', 'kind'), DEP); VPAID = 'SUMIFS(%s,%s,%s)' % (R('schedule', 'amount_paid'), R('schedule', 'vendor'), VE)
VRISK = '(%s+IF(%s<{set:refund_days},%s-%s,0))' % (VDEP, DAYS13, VPAID, VDEP)
tools.append(TOOL('cancel_exposure', 'Cancellation Exposure', 'How much could we lose if we cancelled',
    'Pick a vendor and the days from now you might cancel; deposits count as lost and later payments once inside your refund window. Check your contract for the real terms.', [
    IL('vendor', 'Vendor', 'vname', 'Venue'), I('cancel_in', 'Days from now you might cancel', 150, 'int')], [
    O('Days before the wedding at cancellation', 'int', DAYS13), O('Inside your refund window', 'text', 'IF(%s<{set:refund_days},%s,%s)' % (DAYS13, YES, NO)), O('Deposits paid, all vendors', 'money', DEP_ALL),
    O('Paid in total, all vendors', 'money', PAID_ALL), O('At risk, all vendors', 'money', RND(RISK13)), O('Deposit paid to this vendor', 'money', VDEP), O('Paid in total to this vendor', 'money', VPAID),
    O('At risk with this vendor', 'money', RND(VRISK)), O('Share of everything paid that is at risk', 'pct', 'IF(%s>0,%s/%s,0)' % (PAID_ALL, RISK13, PAID_ALL)),
    O('Largest exposure today, vendor', 'text', T_('cancel', 'vendor', 'at_risk', 'MAX(%s)' % R('cancel', 'at_risk'), True)), O('Its amount at risk', 'money', 'MAX(%s)' % R('cancel', 'at_risk')),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)' % (V('At risk'), RISK13))],
    GR('What if', ('Cancel today', {'cancel_in': 0}), ('In 90 days', {'cancel_in': 90}), ('In 140 days', {'cancel_in': 140}), ('In 160 days', {'cancel_in': 160}), ('In 190 days', {'cancel_in': 190}))))

# 14 ----------------------------------------------------------- arrival overlap finder
FIRSTC = 'IFERROR(SMALL(%s,1),"")' % R('arrivals', 'clash_at')
tools.append(TOOL('overlap_finder', 'Arrival Overlap Finder', 'Are two vendors set up in the same place at the same time',
    'Type the minutes you want between two vendors in one place; set-up and load-out steps are checked for overlaps and the verdict names the first clash time.', [
    I('buffer', 'Minutes you want between two vendors', 10, 'int')], [
    O('Set-up and load-out steps checked', 'int', 'COUNTIFS(%s,1)' % R('arrivals', 'setup')), O('Steps that overlap another vendor', 'int', 'COUNTIFS(%s,">0")' % R('arrivals', 'overlaps')),
    O('Steps with less than your buffer before the next vendor', 'int', 'COUNTIFS(%s,"<"&{in:buffer})' % R('arrivals', 'gap_next')),
    O('Steps with exactly enough room', 'int', 'COUNTIFS(%s,">="&{in:buffer})' % R('arrivals', 'gap_next')),
    O('First clash at', 'time', FIRSTC), O('Vendor in the first clash', 'text', T_('arrivals', 'vendor', 'clash_at', 'SMALL(%s,1)' % R('arrivals', 'clash_at'), True)),
    O('Longest set-up step, minutes', 'int', 'SUMPRODUCT(MAX((%s=%s)*(%s<>"")*%s))' % (R('run', 'block'), PREP, R('run', 'vendor_id'), R('run', 'minutes'))),
    O('Vendors in the run of show', 'int', 'COUNTIFS(%s,">0")' % R('contact', 'steps')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">0")=0,%s,%s&" "&%s)' % (R('arrivals', 'overlaps'), V('Clear'), V('Conflict at'), HM(FIRSTC)))],
    GR('What if', ('No buffer', {'buffer': 0}), ('5 minutes', {'buffer': 5}), ('10 minutes', {'buffer': 10}), ('15 minutes', {'buffer': 15}), ('30 minutes', {'buffer': 30}))))

# 15 ----------------------------------------------------------- vendor meals count
MH = R('meals', 'hours')
tools.append(TOOL('meals_count', 'Vendor Meals Count', 'How many vendor meals do we order',
    'Type the hours after which a vendor gets a meal and the meal price; vendors on site longer are counted with their crew and the verdict says how many to order.', [
    I('hours', 'Hours on site after which a vendor gets a meal', 5, 'int'), I('price', 'Price of one vendor meal, your own number', 18)], [
    O('Vendors on site on the day', 'int', 'COUNTIFS(%s,">0")' % MH), O('People on site in total', 'int', 'SUMIFS(%s,%s,">0")' % (R('meals', 'crew'), MH)),
    O('Vendors who get a meal', 'int', 'COUNTIFS(%s,">="&{in:hours})' % MH), O('Vendor meals to order', 'int', 'SUMIFS(%s,%s,">="&{in:hours})' % (R('meals', 'crew'), MH)),
    O('Cost of the vendor meals', 'money', '{in:price}*SUMIFS(%s,%s,">="&{in:hours})' % (R('meals', 'crew'), MH)), O('Longest day on site, hours', 'hours', 'MAX(%s)' % MH),
    O('Vendor with the longest day', 'text', T_('meals', 'vendor', 'hours', 'MAX(%s)' % MH, True)), O('Meals at the hours limit in Settings', 'int', 'SUM(%s)' % R('meals', 'count')),
    O('Verdict', 'text', '%s&" "&SUMIFS(%s,%s,">="&{in:hours})&" "&%s&", "&ROUND({in:price}*SUMIFS(%s,%s,">="&{in:hours}),0)' % (V('Order'), R('meals', 'crew'), MH, V('vendor meals'), R('meals', 'crew'), MH))],
    GR('What if', ('After 3 hours', {'hours': 3}), ('After 4 hours', {'hours': 4}), ('After 5 hours', {'hours': 5}), ('After 6 hours', {'hours': 6}), ('After 8 hours', {'hours': 8}))))

# 16 ----------------------------------------------------------- response time ranker
tools.append(TOOL('response_ranker', 'Response Time Ranker', 'Which vendor is slowest to answer',
    'Type the average days to reply that count as slow; vendors are ranked slowest first from their quotes, and the verdict names the open vendor to chase.', [
    I('slow', 'Average days to reply that count as slow', 6, 'int')], [
    O('Slowest vendor', 'text', T_('response', 'vendor', 'rank', '1', True)), O('Its average days to reply', 'num', T_('response', 'avg_days', 'rank', '1')), O('Second slowest vendor', 'text', T_('response', 'vendor', 'rank', '2', True)),
    O('Its average days to reply', 'num', T_('response', 'avg_days', 'rank', '2')), O('Slowest open vendor', 'text', T_('response', 'vendor', 'open_rank', '1', True)), O('Its average days to reply', 'num', T_('response', 'avg_days', 'open_rank', '1')),
    O('Vendors slower than your limit', 'int', 'COUNTIFS(%s,">"&{in:slow})' % R('response', 'avg_days')), O('Open vendors', 'int', 'SUM(%s)' % R('response', 'open')),
    O('Average days to reply, all vendors', 'num', 'ROUND(AVERAGE(%s),1)' % R('response', 'avg_days')),
    O('Verdict', 'text', '%s&" "&%s' % (V('Chase'), T_('response', 'vendor', 'open_rank', '1', True)))],
    GR('What if', ('Slow after 3 days', {'slow': 3}), ('Slow after 4 days', {'slow': 4}), ('Slow after 5 days', {'slow': 5}), ('Slow after 6 days', {'slow': 6}), ('Slow after 8 days', {'slow': 8}))))

# 17 ----------------------------------------------------------- follow-up ranker
FK = lambda c_, k, txt=False: T_('followups', c_, 'rank', str(k), txt)
tools.append(TOOL('followup_ranker', 'Follow-up Ranker', 'Who do we call today',
    'Type the days of silence that count as stale and the days before expiry that count as soon; vendors are ranked by urgency and the verdict names the first call.', [
    I('stale', 'Days of silence that count as stale', 30, 'int'), I('expiry', 'Days before a quote expires that count as soon', 14, 'int')], [
    O('First call', 'text', FK('vendor', 1, True)), O('Days since contact, first', 'int', FK('days_since', 1)), O('Second call', 'text', FK('vendor', 2, True)), O('Days since contact, second', 'int', FK('days_since', 2)),
    O('Third call', 'text', FK('vendor', 3, True)), O('Days since contact, third', 'int', FK('days_since', 3)),
    O('Vendors silent for longer than your limit', 'int', 'COUNTIFS(%s,">"&{in:stale})' % R('vendors', 'days_since')),
    O('Open quotes expiring soon', 'int', 'COUNTIFS(%s,">=0",%s,"<="&{in:expiry})' % (R('quotes', 'days_to_expiry'), R('quotes', 'days_to_expiry'))),
    O('Open quotes already expired', 'int', 'COUNTIFS(%s,"<0")' % R('quotes', 'days_to_expiry')),
    O('Follow-ups dated in the next 7 days', 'int', 'COUNTIFS(%s,">="&{today},%s,"<="&{today}+7)' % (R('vendors', 'follow_up'), R('vendors', 'follow_up'))),
    O('Verdict', 'text', '%s&" "&%s&" "&%s' % (V('Chase'), FK('vendor', 1, True), V('today')))],
    GR('What if', ('Stale after 14 days', {'stale': 14}), ('Stale after 30 days', {'stale': 30}), ('Stale after 45 days', {'stale': 45}), ('Quote soon in 7 days', {'expiry': 7}), ('Quote soon in 30 days', {'expiry': 30}))))

# 18 ----------------------------------------------------------- quote expiry watch
OD = R('quotes', 'open_days')
SOON = 'SMALL(%s,1)' % OD
tools.append(TOOL('expiry_watch', 'Quote Expiry Watch', 'Which quotes run out soon',
    'Type the window in days; open quotes that expire inside it are counted with their value, the soonest is named, and the verdict says which quote to decide on and in how many days.', [
    I('window', 'Window in days', 14, 'int')], [
    O('Open quotes', 'int', 'SUM(%s)' % R('quotes', 'open_flag')), O('Expiring inside your window', 'int', 'COUNTIFS(%s,">=0",%s,"<="&{in:window})' % (R('quotes', 'days_to_expiry'), R('quotes', 'days_to_expiry'))),
    O('Already expired', 'int', 'COUNTIFS(%s,"<0")' % R('quotes', 'days_to_expiry')),
    O('Value of the quotes expiring inside the window', 'money', 'SUMIFS(%s,%s,">=0",%s,"<="&{in:window})' % (R('quotes', 'true_total'), R('quotes', 'days_to_expiry'), R('quotes', 'days_to_expiry'))),
    O('Value of the expired quotes', 'money', 'SUMIFS(%s,%s,"<0")' % (R('quotes', 'true_total'), R('quotes', 'days_to_expiry'))),
    O('Soonest quote to expire, vendor', 'text', T_('quotes', 'vendor', 'open_days', SOON, True)), O('Its option', 'text', T_('quotes', 'option', 'open_days', SOON, True)),
    O('Its valid-until date', 'date', T_('quotes', 'valid_until', 'open_days', SOON)), O('Days left on it', 'int', 'IFERROR(%s,"")' % SOON),
    O('Verdict', 'text', 'IF(ISNUMBER(%s),%s&" "&%s&" "&%s&" "&%s&" "&%s&" "&%s,%s)' % (SOON, V('Decide'), T_('quotes', 'vendor', 'open_days', SOON, True), T_('quotes', 'option', 'open_days', SOON, True), V('within'), SOON, V('days'), V('No open quote left')))],
    GR('What if', ('Window 7 days', {'window': 7}), ('Window 14 days', {'window': 14}), ('Window 30 days', {'window': 30}), ('Window 45 days', {'window': 45}), ('Window 60 days', {'window': 60}))))
assert len(tools) == 18, len(tools)
