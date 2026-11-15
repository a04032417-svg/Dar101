"""Car rental suite part 5: the 18 decision tools (each with a verdict, the numbers behind it and, where it helps, a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr5_lists import *
import cr5_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, default_label): return IN(k, label, 'list', key(lst, default_label), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def R(t, c): return '{range:%s.%s}' % (t, c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
SOLD = tok('vstatus', 'Sold')
UP = tok('rstatus2', 'Upcoming'); DONE = tok('rstatus2', 'Done')
def G(x): return tok('mgroup', x)
def KD(x): return tok('mkind', x)
def VL(c, v='{in:veh}'): return 'IFERROR(INDEX({range:vehicles.%s},MATCH(%s,{range:vehicles.vehicle},0)),0)' % (c, v)
def VLT(c, v='{in:veh}'): return 'IFERROR(INDEX({range:vehicles.%s},MATCH(%s,{range:vehicles.vehicle},0))&"","")' % (c, v)
def FOUND(f, v='{in:veh}'): return 'IF(ISNUMBER(MATCH(%s,{range:vehicles.vehicle},0)),%s,%s)' % (v, f, c2('Vehicle not found'))
def ADR(c):
    f = '0'
    for cl in reversed(CLASSES): f = 'IF(%s=%s,{set:adr_%s},%s)' % (c, tok('class', cl), key('class', cl), f)
    return f
def LOGSUM(col, extra='', lo=365, veh='{in:veh}'):
    return 'SUMIFS({range:service_log.%s},{range:service_log.vehicle},%s,{range:service_log.date},">="&({today}-%d)%s)' % (col, veh, lo, extra)
def LOGSUMG(col, groups, lo=365): return '(' + '+'.join(LOGSUM(col, ',{range:service_log.group},%s' % G(g), lo) for g in groups) + ')'
def RTW(lo, hi):   # repair, towing and tyre cost of the vehicle in full months (lo months back up to hi months back)
    return '(' + '+'.join('SUMIFS({range:service_log.cost},{range:service_log.vehicle},{in:veh},{range:service_log.group},%s,{range:service_log.date},">="&EDATE(%s,-%s),{range:service_log.date},"<"&EDATE(%s,-%s))' % (G(g), MS, lo, MS, hi) for g in ('Repair', 'Towing', 'Tyres')) + ')'
tools = []
VID = lambda i: D.VD[i]['vehicle']
SV = VID(D.ST['service_vehicle'])

# 1 ------------------------------------------------------------ service due planner
MT1 = '(%s-(%s+{in:odo_add}-%s))' % (VL('interval_miles'), VL('odometer'), VL('last_service_odometer'))
ND1 = 'EDATE(IF(%s>0,%s,%s),%s)' % (VL('last_service_date'), VL('last_service_date'), VL('purchase_date'), VL('interval_months'))
MPD1 = 'IF({in:mpd_in}>0,{in:mpd_in},MAX(20,ROUND(%s/365,0)))' % VL('miles_12m')
tools.append(TOOL('service_planner', 'Service Due Planner', 'Does this car need service now, soon or not yet',
    'Type a vehicle as written on the Vehicle Register; service falls due by miles or by months, whichever comes first; add miles to see when it turns due.', [
    I('veh', 'Vehicle', VID('VH-025'), 'text'), I('odo_add', 'Extra miles to add to the odometer', 0, 'int'), I('mpd_in', 'Miles a day, 0 uses the vehicle 12-month average', 0, 'int')], [
    O('Class', 'text', VLT('class')), O('Odometer used, miles', 'int', '%s+{in:odo_add}' % VL('odometer')), O('Miles since the last service', 'int', '%s+{in:odo_add}-%s' % (VL('odometer'), VL('last_service_odometer'))),
    O('Service interval, miles', 'int', VL('interval_miles')), O('Miles to the next service', 'int', MT1), O('Next service date, by months', 'date', ND1), O('Days to the service date', 'int', '%s-{today}' % ND1),
    O('Miles a day used', 'int', MPD1), O('Service due by, whichever comes first', 'date', 'MAX({today},INT(MIN(%s,{today}+MAX(0,%s)/(%s))))' % (ND1, MT1, MPD1)),
    O('Cars past their interval now', 'int', 'COUNTIFS(%s,%s)' % (R('service_due', 'due_by'), ca('Service now'))), O('Cars due soon', 'int', 'COUNTIFS(%s,%s)' % (R('service_due', 'due_by'), ca('Book soon'))),
    O('Verdict', 'text', FOUND('IF(OR(%s<=0,%s-{today}<=0),%s,IF(OR(%s<={set:service_warn_miles},%s-{today}<={set:service_warn_days}),%s,%s))' % (MT1, ND1, ca('Service now'), MT1, ND1, ca('Book soon'), ca('Current'))))],
    GR('What if', ('In two weeks, 900 more miles', {'odo_add': 900}), ('Next month, 1,800 more miles', {'odo_add': 1800}), ('Heavy use, 100 miles a day', {'mpd_in': 100}), ('Light use, 30 miles a day', {'mpd_in': 30}))))

# 2 ------------------------------------------------------------ service overdue while booked
SC = R('service_due', 'rank_score')
def LG(k): return 'LARGE(%s,%d)' % (SC, k)
def Q(k): return 'AND(%s>0,INT(%s)>={in:min_over})' % (LG(k), LG(k))
def NTH2(k, col): return 'IF(%s,IFERROR(INDEX(%s,MATCH(%s,%s,0)),"-"),"-")' % (Q(k), R('service_due', col), LG(k), SC)
def MO(k): return 'IF(%s,INT(%s),0)' % (Q(k), LG(k))
N2 = 'COUNTIFS(%s,%s)' % (R('service_due', 'flag'), ca('Pull from booking'))
tools.append(TOOL('overdue_booked', 'Overdue Cars Booked', 'Which overdue car must come off a booking this week',
    'Cars past their service interval that have a booking within 7 days, ranked by miles over the interval; the swap car is the first free car of the same class.', [
    I('min_over', 'Ignore cars with fewer miles over than', 0, 'int')], [
    O('Overdue cars with a booking this week', 'int', N2), O('Overdue cars with no booking this week', 'int', 'COUNTIFS(%s,%s)' % (R('service_due', 'flag'), ca('Book a slot'))),
    O('First car', 'text', NTH2(1, 'vehicle')), O('Miles over the interval', 'int', MO(1)), O('Its booking', 'text', NTH2(1, 'next_booking')),
    O('Booking starts', 'date', 'IF(%s,IFERROR(INDEX(%s,MATCH(%s,%s,0)),0),0)' % (Q(1), R('service_due', 'next_start'), LG(1), SC)), O('Its class', 'text', NTH2(1, 'class')),
    O('Swap to', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"-")' % (R('vehicles', 'vehicle'), NTH2(1, 'class'), R('vehicles', 'swap_class'))),
    O('Second car', 'text', NTH2(2, 'vehicle')), O('Second car, miles over', 'int', MO(2)), O('Second car booking', 'text', NTH2(2, 'next_booking')),
    O('Third car', 'text', NTH2(3, 'vehicle')),
    O('Verdict', 'text', 'IF(NOT(%s),%s,%s&" "&%s)' % (Q(1), c2('No overdue car is booked this week'), ca('Pull from booking'), NTH2(1, 'next_booking')))],
    GR('What if', ('Ignore under 1,000 miles over', {'min_over': 1000}), ('Ignore under 4,000 miles over', {'min_over': 4000}))))

# 3 ------------------------------------------------------------ workshop slot planner
SL = lambda col, v: 'SUMIFS(%s,%s,{in:veh},%s,%s)' % (R('slots', col), R('slots', 'vehicle'), R('slots', 'verdict'), v)
BEST = ca('Best slot'); CNT3 = 'COUNTIFS(%s,{in:veh})' % R('slots', 'vehicle')
LOST3 = SL('lost', BEST); AD3 = ADR(VLT('class'))
tools.append(TOOL('slot_planner', 'Workshop Slot Planner', 'Which workshop day loses the fewest booked days',
    'Add candidate dates for the vehicle on the Workshop Slots sheet; this planner picks the date that loses the fewest booked days and shows what the lost days cost.', [
    I('veh', 'Vehicle', SV, 'text'), IL('kind', 'Work to do', 'mkind', 'Minor service'), I('delay', 'Extra days off road if parts are late', 1, 'int')], [
    O('Class', 'text', VLT('class')), O('Candidate slots for this vehicle', 'int', CNT3), O('Slots that lose no booked day', 'int', 'COUNTIFS(%s,{in:veh},%s,0)' % (R('slots', 'vehicle'), R('slots', 'lost'))),
    O('Best date', 'date', 'IF(%s=0,"",%s)' % (CNT3, SL('date', BEST))), O('Days needed', 'int', 'IF(%s=0,"",%s)' % (CNT3, SL('days', BEST))),
    O('Booked days lost at the best date', 'int', 'IF(%s=0,"",%s)' % (CNT3, LOST3)), O('Free days after the visit', 'int', 'IF(%s=0,"",%s)' % (CNT3, SL('free_after', BEST))),
    O('Average daily rate of the class', 'money', AD3), O('Revenue lost at the best date', 'money', 'IF(%s=0,0,%s*(%s))' % (CNT3, LOST3, AD3)),
    O('Extra revenue lost if parts are late', 'money', '{in:delay}*%s*(%s)' % (VL('util_12m'), AD3)),
    O('Workshop', 'text', 'IF({in:kind}=%s,%s,IF({in:kind}=%s,%s,IF({in:kind}=%s,%s,%s)))' % (KD('Tyre set'), tok('vendor', VENDOR['Tyre supplier']), KD('Body repair'), tok('vendor', VENDOR['Body repair shop']),
                                                                                       KD('Towing'), tok('vendor', VENDOR['Towing service']), tok('vendor', VENDOR['Mechanic']))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s=0,%s,%s))' % (CNT3, c2('Add candidate dates'), LOST3, c2('Book the free slot'), c2('Book the best slot')))],
    GR('What if', ('Parts on time', {'delay': 0}), ('Parts arrive three days late', {'delay': 3}), ('A week in the workshop', {'delay': 7}))))

# 4 ------------------------------------------------------------ rental days lost to service
DAYS4 = LOGSUM('days_off_road')
PEAK4 = 'SUMPRODUCT((%s={in:veh})*(%s>={today}-365)*(((MONTH(%s)=6)+(MONTH(%s)=7)+(MONTH(%s)=8)+(MONTH(%s)=12))>0)*%s)' % (R('service_log', 'vehicle'), R('service_log', 'date'), R('service_log', 'date'),
                                                                                                                       R('service_log', 'date'), R('service_log', 'date'), R('service_log', 'date'), R('service_log', 'days_off_road'))
ADR4 = 'IF({in:adr_in}>0,{in:adr_in},%s)' % ADR(VLT('class'))
tools.append(TOOL('days_lost_tool', 'Rental Days Lost', 'How many rental days did service cost this vehicle',
    'Workshop days of the last 12 months for one vehicle, the booked days lost at its utilisation and the revenue those days would have earned; peak months are June to August and December.', [
    I('veh', 'Vehicle', 'Compact 06 Red', 'text'), I('peak_limit', 'Most workshop days you accept in peak months', 0.3, 'pct'), I('adr_in', 'Daily rate to use, 0 uses the class average daily rate', 0)], [
    O('Class', 'text', VLT('class')), O('Workshop days, 12 months', 'int', DAYS4), O('Service, inspection and tyre days', 'int', LOGSUMG('days_off_road', ['Service', 'Inspection', 'Tyres'])),
    O('Repair and towing days', 'int', LOGSUMG('days_off_road', ['Repair', 'Towing'])), O('Utilisation, 12 months', 'pct', VL('util_12m')), O('Booked days lost', 'num', 'ROUND(%s*%s,1)' % (DAYS4, VL('util_12m'))),
    O('Daily rate used', 'money', ADR4), O('Revenue lost', 'money', 'ROUND(%s*%s*(%s),0)' % (DAYS4, VL('util_12m'), ADR4)), O('Share of the year in the workshop', 'pct', '%s/365' % DAYS4),
    O('Average workshop days per vehicle, fleet', 'num', 'IFERROR(SUM(%s)/COUNTA(%s),0)' % (R('days_lost', 'days'), R('days_lost', 'vehicle'))),
    O('Share of days in peak months', 'pct', 'IFERROR(%s/%s,0)' % (PEAK4, DAYS4)),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>{in:peak_limit},%s,%s)' % (PEAK4, DAYS4, c2('Service in the low season'), ca('Acceptable')))],
    GR('What if', ('Accept only 15% in peak months', {'peak_limit': 0.15}), ('Accept 50% in peak months', {'peak_limit': 0.5}), ('Daily rate 150', {'adr_in': 150}))))

# 5 ------------------------------------------------------------ renewals dashboard
RW = lambda k, col: 'IFERROR(INDEX(%s,MATCH(SMALL(%s,%d),%s,0)),"")' % (R('renewals', col), R('renewals', 'sort_key'), k, R('renewals', 'sort_key'))
def RCNT(n): return 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<="&({today}+%s))' % (R('renewals', 'status'), UP, R('renewals', 'due_date'), R('renewals', 'due_date'), n)
OVD = 'COUNTIFS(%s,%s,%s,"<"&{today})' % (R('renewals', 'status'), UP, R('renewals', 'due_date'))
rows5 = []
for k in range(1, 6):
    rows5 += [O('Renewal %d' % k, 'text', 'IFERROR(INDEX(%s,MATCH(SMALL(%s,%d),%s,0))&" - "&INDEX(%s,MATCH(SMALL(%s,%d),%s,0)),"")' % (R('renewals', 'vehicle'), R('renewals', 'sort_key'), k, R('renewals', 'sort_key'),
                                                                                                                                    R('renewals', 'kind'), R('renewals', 'sort_key'), k, R('renewals', 'sort_key'))),
              O('Due on, renewal %d' % k, 'date', 'IFERROR(INT(SMALL(%s,%d)),"")' % (R('renewals', 'sort_key'), k))]
tools.append(TOOL('renewals_tool', 'Renewals Dashboard', 'What is overdue and what falls due next across the fleet',
    'Registration, insurance and inspection dates in one sorted list: overdue first, then due soon; choose how many days count as soon.', [
    I('d1', 'Days that count as due soon', 30, 'int'), I('d2', 'Days that count as due later', 60, 'int')], [
    O('Renewals overdue', 'int', OVD), O('Renewals due within the soon window', 'int', RCNT('{in:d1}')), O('Renewals due within the later window', 'int', RCNT('{in:d2}')),
    O('Cost due within the soon window', 'money', 'SUMIFS(%s,%s,%s,%s,">="&{today},%s,"<="&({today}+{in:d1}))' % (R('renewals', 'cost'), R('renewals', 'status'), UP, R('renewals', 'due_date'), R('renewals', 'due_date'))),
    O('Cost due within the later window', 'money', 'SUMIFS(%s,%s,%s,%s,">="&{today},%s,"<="&({today}+{in:d2}))' % (R('renewals', 'cost'), R('renewals', 'status'), UP, R('renewals', 'due_date'), R('renewals', 'due_date')))] + rows5 + [
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&%s' % (OVD, ca('Overdue'), RCNT('{in:d1}'), ca('Due in 30 days')))],
    GR('What if', ('Look 14 days ahead', {'d1': 14, 'd2': 45}), ('Look 90 days ahead', {'d1': 90, 'd2': 120}))))

# 6 ------------------------------------------------------------ renewal cash plan
TOT6 = 'SUM(%s)' % R('renew_cost', 'total'); NEED6 = 'MAX(%s)*(1+{in:buffer})' % R('renew_cost', 'avg_to_date')
tools.append(TOOL('cash_plan', 'Renewal Cash Plan', 'How much to set aside each month for renewals',
    'The cost of renewals due in the next 12 months against your monthly set-aside; the amount needed is the highest running average, so cash never runs short in any month.', [
    I('aside', 'Amount you set aside each month', 3500), I('buffer', 'Allowance for price rises', 0.05, 'pct'), I('start', 'Already set aside', 0)], [
    O('Renewals due, next 12 months', 'money', TOT6), O('With the price allowance', 'money', '%s*(1+{in:buffer})' % TOT6), O('Average a month', 'money', '%s*(1+{in:buffer})/12' % TOT6),
    O('Set aside needed each month', 'money', 'ROUNDUP(%s,0)' % NEED6), O('Month with the largest running need', 'date', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('renew_cost', 'month'), R('renew_cost', 'avg_to_date'), R('renew_cost', 'avg_to_date'))),
    O('Highest single month', 'money', 'MAX(%s)' % R('renew_cost', 'total')), O('You set aside in 12 months', 'money', '{in:start}+{in:aside}*12'),
    O('Cash left after 12 months', 'money', '{in:start}+{in:aside}*12-%s*(1+{in:buffer})' % TOT6), O('Gap each month, negative is spare', 'money', 'ROUNDUP(%s,0)-{in:aside}' % NEED6),
    O('Verdict', 'text', 'IF({in:aside}>=%s,%s,%s&" "&ROUNDUP(%s,0))' % (NEED6, cb('Enough set aside'), cb('Set aside more'), NEED6))],
    GR('What if', ('Set aside 2,500 a month', {'aside': 2500}), ('Set aside 4,500 a month', {'aside': 4500}), ('Prices rise 15%', {'buffer': 0.15}), ('Start with 2,000 set aside', {'start': 2000}))))

# 7 ------------------------------------------------------------ repair cost trend
TR_R = '%s' % RTW('{in:recent}', 0); TR_12 = RTW(12, 0)
tools.append(TOOL('repair_trend', 'Repair Cost Trend', 'Are repair and tyre costs rising for this vehicle',
    'Repair, towing and tyre cost of the last full months against the vehicle own 12-month average, per month and per 1,000 miles.', [
    I('veh', 'Vehicle', 'Economy 08 Orange', 'text'), I('recent', 'Recent months to compare', 3, 'int'), I('rise', 'Rise that counts as rising', 0.15, 'pct')], [
    O('Class', 'text', VLT('class')), O('Cost of the recent months', 'money', TR_R), O('Recent cost a month', 'money', '%s/{in:recent}' % TR_R), O('Cost of the last 12 months', 'money', TR_12),
    O('Own average a month, 12 months', 'money', '%s/12' % TR_12), O('Change against the own average', 'pct', 'IFERROR((%s/{in:recent})/(%s/12)-1,0)' % (TR_R, TR_12)), O('Miles, last 12 months', 'int', VL('miles_12m')),
    O('Cost per 1,000 miles, 12 months', 'money', 'IFERROR(%s/%s*1000,0)' % (TR_12, VL('miles_12m'))), O('Recent cost per 1,000 miles, yearly pace', 'money', 'IFERROR(%s/{in:recent}*12/%s*1000,0)' % (TR_R, VL('miles_12m'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF((%s/{in:recent})/(%s/12)-1>{in:rise},%s,IF((%s/{in:recent})/(%s/12)-1<-{in:rise},%s,%s)))' % (TR_12, c2('Trend needs more months'), TR_R, TR_12, ca('Rising'), TR_R, TR_12, ca('Falling'), ca('Steady')))],
    GR('What if', ('Compare the last month', {'recent': 1}), ('Compare the last 6 months', {'recent': 6}), ('Rise limit 40%', {'rise': 0.4}))))

# 8 ------------------------------------------------------------ tyre planner
SEA8 = '({set:season_change}+{in:extra})'; N8 = 'COUNTIFS(%s,"<="&%s)' % (R('tyres', 'due_on'), SEA8)
tools.append(TOOL('tyre_planner', 'Tyre Planner', 'How many tyre sets to order before the season change',
    'Miles to the next tyre set per vehicle from the Tyre Dates sheet; sets whose miles run out before the season change are counted and costed.', [
    I('price', 'Price of one set', 420), I('lead', 'Days the supplier needs to deliver', 14, 'int'), I('extra', 'Days to move the season change later', 0, 'int')], [
    O('Sets due before the season change', 'int', N8), O('Vehicles with tyres due now', 'int', 'COUNTIFS(%s,%s)' % (R('tyres', 'tyre_flag'), ca('Tyres due'))), O('Vehicles past the tyre life', 'int', 'COUNTIFS(%s,"<0")' % R('tyres', 'next_tyre_miles')),
    O('Order by', 'date', '%s-{in:lead}' % SEA8), O('Estimated spend', 'money', '%s*{in:price}' % N8), O('Vehicle with the fewest miles left', 'text', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (R('tyres', 'vehicle'), R('tyres', 'next_tyre_miles'), R('tyres', 'next_tyre_miles'))),
    O('Its miles left', 'int', 'MIN(%s)' % R('tyres', 'next_tyre_miles')), O('First tyres due on', 'date', 'MIN(%s)' % R('tyres', 'due_on')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (N8, cb('No tyre order needed'), cb('Order tyre sets now'), N8))],
    GR('What if', ('Season change two weeks later', {'extra': 14}), ('Season change a month later', {'extra': 30}), ('Sets cost 500', {'price': 500}))))

# 9 ------------------------------------------------------------ cost per 1,000 miles ranking
RK = lambda col: 'IFERROR(INDEX(%s,MATCH({in:rank},%s,0)),"")' % (R('cost1000', col), R('cost1000', 'rank'))
GAP9 = 'IFERROR(%s,0)' % RK('vs_class')
tools.append(TOOL('cost_ranking', 'Cost per 1,000 Miles Ranking', 'Which vehicle costs most to keep on the road per 1,000 miles',
    'Vehicles ranked by maintenance cost per 1,000 miles; pick a rank and see how far it sits above its class average.', [
    I('rank', 'Rank to show, 1 is the dearest', 1, 'int'), I('min_gap', 'Review when above the class by more than', 20)], [
    O('Vehicle', 'text', RK('vehicle')), O('Class', 'text', RK('class')), O('Cost per 1,000 miles', 'money', RK('cost_1000')), O('Class average per 1,000 miles', 'money', RK('class_avg')), O('Above the class', 'money', RK('vs_class')),
    O('Maintenance cost, 12 months', 'money', RK('maint_cost')), O('Miles, 12 months', 'int', RK('miles_12m')), O('Trend', 'text', RK('trend')),
    O('Fleet cost per 1,000 miles', 'money', 'IFERROR(SUM(%s)/SUM(%s)*1000,0)' % (R('cost1000', 'maint_cost'), R('cost1000', 'miles_12m'))), O('Vehicles above their class average', 'int', 'COUNTIFS(%s,%s)' % (R('cost1000', 'class_flag'), ca('Above class average'))),
    O('Summary', 'text', 'IF(%s>{in:min_gap},%s&" "&%s&" "&ROUND(%s,0),"")' % (GAP9, RK('vehicle'), c2('costs above its class by'), GAP9)),
    O('Verdict', 'text', 'IF(%s>{in:min_gap},%s,%s)' % (GAP9, cb('Review this vehicle'), cb('Within the class range')))],
    GR('What if', ('Second dearest', {'rank': 2}), ('Third dearest', {'rank': 3}), ('Review above 60', {'min_gap': 60}))))

# 10 ----------------------------------------------------------- vehicle register check
ACT10 = '%s,"<>",%s,"<>"&%s' % (R('vehicles', 'vehicle_id'), R('vehicles', 'status'), SOLD)
MISS = lambda col: 'COUNTIFS(%s,%s,"")' % (ACT10, R('vehicles', col))
GAPN = 'COUNTIFS(%s,">"&{in:allowed})' % R('vehicles', 'gaps')
tools.append(TOOL('register_check', 'Vehicle Register Check', 'Is every vehicle on the register complete',
    'Counts the missing plate, odometer, interval, service date, insurance and renewal dates for the vehicles in the fleet.', [
    I('allowed', 'Gaps you accept per vehicle', 0, 'int')], [
    O('Vehicles in the fleet', 'int', 'COUNTIFS(%s)' % ACT10), O('Vehicles with gaps', 'int', GAPN), O('Missing plate', 'int', MISS('plate')), O('Missing odometer', 'int', MISS('odometer')),
    O('Missing service interval, miles', 'int', MISS('interval_miles')), O('Missing service interval, months', 'int', MISS('interval_months')), O('Missing last service date', 'int', MISS('last_service_date')),
    O('Missing insurance amount', 'int', MISS('insurance_year')), O('Missing registration date', 'int', 'COUNTA(%s)-COUNT(%s)' % (R('renewals_by_veh', 'vehicle'), R('renewals_by_veh', 'next_reg'))),
    O('Missing insurance date', 'int', 'COUNTA(%s)-COUNT(%s)' % (R('renewals_by_veh', 'vehicle'), R('renewals_by_veh', 'next_ins'))), O('Missing inspection date', 'int', 'COUNTA(%s)-COUNT(%s)' % (R('renewals_by_veh', 'vehicle'), R('renewals_by_veh', 'next_insp'))),
    O('Vehicle with the most gaps', 'text', 'IF(MAX(%s)>0,INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (R('vehicles', 'gaps'), R('vehicles', 'vehicle'), R('vehicles', 'gaps'), R('vehicles', 'gaps'))),
    O('Register completeness', 'pct', 'IFERROR(1-%s/COUNTIFS(%s),0)' % (GAPN, ACT10)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (GAPN, cb('Register complete'), cb('Gaps to fill'), GAPN))],
    GR('What if', ('Accept one gap per vehicle', {'allowed': 1}), ('Accept two gaps per vehicle', {'allowed': 2}))))

# 11 ----------------------------------------------------------- insurance renewal compare
INS = lambda st, extra: 'AVERAGEIFS(%s,%s,%s,%s,%s,%s,{in:cls}%s)' % (R('renewals', 'cost'), R('renewals', 'kind'), tok('renewal', 'Insurance renewal'), R('renewals', 'status'), st, R('renewals', 'class'), extra)
UP11 = INS(UP, ',%s,"<="&({today}+365)' % R('renewals', 'due_date')); LY11 = INS(DONE, ',%s,">="&({today}-365)' % R('renewals', 'due_date'))
RS11 = 'IFERROR(%s/%s-1,0)' % (UP11, LY11)
tools.append(TOOL('insurance_compare', 'Insurance Renewal Compare', 'Which class needs a new insurance quote',
    'Yearly premium per class against last year and against the fleet average; a rise above your limit means ask your broker for a quote.', [
    IL('cls', 'Vehicle class', 'class', 'Premium'), I('limit', 'Re-quote when the premium rises more than', 0.08, 'pct')], [
    O('Vehicles in the class', 'int', 'COUNTIFS(%s,{in:cls},%s,"<>"&%s)' % (R('vehicles', 'class'), R('vehicles', 'status'), SOLD)),
    O('Average premium now, from the register', 'money', 'IFERROR(AVERAGEIFS(%s,%s,{in:cls},%s,"<>"&%s),0)' % (R('vehicles', 'insurance_year'), R('vehicles', 'class'), R('vehicles', 'status'), SOLD)),
    O('Fleet average premium', 'money', 'IFERROR(AVERAGEIFS(%s,%s,"<>"&%s,%s,"<>"),0)' % (R('vehicles', 'insurance_year'), R('vehicles', 'status'), SOLD, R('vehicles', 'vehicle_id'))),
    O('Next renewals, average premium', 'money', 'IFERROR(%s,0)' % UP11), O('Last year renewals, average premium', 'money', 'IFERROR(%s,0)' % LY11), O('Change against last year', 'pct', RS11),
    O('Total of the next renewals in the class', 'money', 'SUMIFS(%s,%s,%s,%s,%s,%s,{in:cls},%s,"<="&({today}+365))' % (R('renewals', 'cost'), R('renewals', 'kind'), tok('renewal', 'Insurance renewal'), R('renewals', 'status'), UP, R('renewals', 'class'), R('renewals', 'due_date'))),
    O('Class premium against the fleet average', 'pct', 'IFERROR(AVERAGEIFS(%s,%s,{in:cls},%s,"<>"&%s)/AVERAGEIFS(%s,%s,"<>"&%s,%s,"<>")-1,0)' % (R('vehicles', 'insurance_year'), R('vehicles', 'class'), R('vehicles', 'status'), SOLD, R('vehicles', 'insurance_year'), R('vehicles', 'status'), SOLD, R('vehicles', 'vehicle_id'))),
    O('Verdict', 'text', 'IF(%s>{in:limit},%s&" "&{in:cls},%s)' % (RS11, cb('Re-quote'), cb('Renew as is')))],
    GR('What if', ('Re-quote above 3%', {'limit': 0.03}), ('Re-quote above 15%', {'limit': 0.15}))))

# 12 ----------------------------------------------------------- inspection due planner
BV = lambda c: R('bookings14', c)
BUSY = 'COUNTIFS(%s,{in:veh},%s,"<="&{today},%s,">="&{today})' % (BV('vehicle'), BV('start_date'), BV('end_date'))
FREE = 'IF(%s>0,SUMPRODUCT(MAX((%s={in:veh})*(%s<={today})*(%s>={today})*%s))+1,{today})' % (BUSY, BV('vehicle'), BV('start_date'), BV('end_date'), BV('end_date'))
NXT12 = '(100000-SUMPRODUCT(MAX((%s={in:veh})*(%s>=%s)*(100000-%s))))' % (BV('vehicle'), BV('start_date'), FREE, BV('start_date'))
GAP12 = 'IF(%s>=100000,30,%s-%s)' % (NXT12, NXT12, FREE)
DUE12 = 'IFERROR(INDEX(%s,MATCH({in:veh},%s,0)),"")' % (R('renewals_by_veh', 'next_insp'), R('renewals_by_veh', 'vehicle'))
tools.append(TOOL('inspection_planner', 'Inspection Due Planner', 'When can this vehicle go for its inspection',
    'The inspection due date against the vehicle bookings: the first free day and the free days before the next booking tell you to book it in or move a booking.', [
    I('veh', 'Vehicle', 'Premium 02 Orange', 'text'), I('need', 'Days the inspection needs', 1, 'int')], [
    O('Inspection due on', 'date', DUE12), O('Days to the due date', 'int', 'IFERROR(%s-{today},"")' % DUE12), O('Rented out now', 'int', BUSY), O('First free day', 'date', FREE),
    O('Free days before the next booking', 'int', GAP12), O('Next booking', 'text', 'IFERROR(INDEX(%s,MATCH({in:veh}&"|"&%s,%s,0)),"")' % (BV('booking_id'), NXT12, BV('vkey'))),
    O('Days between the first free day and the due date', 'int', 'IFERROR(%s-%s,"")' % (DUE12, FREE)),
    O('Verdict', 'text', 'IF(%s>={in:need},%s,%s&" "&IFERROR(INDEX(%s,MATCH({in:veh}&"|"&%s,%s,0)),""))' % (GAP12, cb('Book the inspection'), cb('Move a booking'), BV('booking_id'), NXT12, BV('vkey')))],
    GR('What if', ('Two days needed', {'need': 2}), ('Five days needed', {'need': 5}), ('A week needed', {'need': 7}))))

# 13 ----------------------------------------------------------- breakdown cost check
BD = LOGSUM('cost', ',{range:service_log.kind},%s' % KD('Towing')); BN = 'COUNTIFS(%s,{in:veh},%s,%s,%s,">="&({today}-365))' % (R('service_log', 'vehicle'), R('service_log', 'kind'), KD('Towing'), R('service_log', 'date'))
RP = LOGSUM('cost', ',{range:service_log.kind},%s' % KD('Repair')); DYS = LOGSUMG('days_off_road', ['Repair', 'Towing'])
LOSS13 = '%s*%s*(%s)' % (DYS, VL('util_12m'), ADR(VLT('class')))
tools.append(TOOL('breakdown_check', 'Breakdown Cost Check', 'What do the breakdowns of this vehicle really cost',
    'Towing, repair and lost rental days of the last 12 months for one vehicle, with the cost per 1,000 miles; more than one breakdown means look closer.', [
    I('veh', 'Vehicle', VID('VH-017'), 'text'), I('repeat', 'Breakdowns that count as repeat', 2, 'int')], [
    O('Class', 'text', VLT('class')), O('Breakdowns, 12 months', 'int', BN), O('Towing cost', 'money', BD), O('Repair cost', 'money', RP), O('Workshop days for repairs and towing', 'int', DYS),
    O('Rental revenue lost to those days', 'money', 'ROUND(%s,0)' % LOSS13), O('Total breakdown cost', 'money', 'ROUND(%s+%s+%s,0)' % (BD, RP, LOSS13)), O('Miles, 12 months', 'int', VL('miles_12m')),
    O('Breakdown cost per 1,000 miles', 'money', 'IFERROR((%s+%s+%s)/%s*1000,0)' % (BD, RP, LOSS13, VL('miles_12m'))),
    O('Verdict', 'text', 'IF(%s>={in:repeat},%s,%s)' % (BN, cb('Repeat breakdowns, review'), cb('No repeat breakdowns')))],
    GR('What if', ('One breakdown is enough', {'repeat': 1}), ('Three breakdowns', {'repeat': 3}))))

# 14 ----------------------------------------------------------- service interval check
SVC = '((%s=%s)+(%s=%s))' % (R('service_log', 'kind'), KD('Minor service'), R('service_log', 'kind'), KD('Major service'))
SVV = '(%s={in:veh})*%s' % (R('service_log', 'vehicle'), SVC)
N14 = 'SUMPRODUCT(%s)' % SVV
MAXO = 'SUMPRODUCT(MAX(%s*%s))' % (SVV, R('service_log', 'odometer')); MINO = '(10000000-SUMPRODUCT(MAX(%s*(10000000-%s))))' % (SVV, R('service_log', 'odometer'))
MAXD = 'SUMPRODUCT(MAX(%s*%s))' % (SVV, R('service_log', 'date')); MIND = '(100000-SUMPRODUCT(MAX(%s*(100000-%s))))' % (SVV, R('service_log', 'date'))
AVGM = 'IF(%s>1,(%s-%s)/(%s-1),0)' % (N14, MAXO, MINO, N14)
RATIO14 = 'IFERROR(%s/%s,0)' % (AVGM, VL('interval_miles'))
tools.append(TOOL('interval_check', 'Service Interval Check', 'Is this vehicle serviced too early, on time or late',
    'Actual miles and months between services against the service interval, with the yearly cost of servicing earlier than needed.', [
    I('veh', 'Vehicle', VID('VH-026'), 'text'), I('early', 'Early when below this share of the interval', 0.85, 'pct'), I('late', 'Late when above this share of the interval', 1.05, 'pct'), I('svc', 'Cost of one service', 110)], [
    O('Services in the log', 'int', N14), O('Average miles between services', 'int', 'ROUND(%s,0)' % AVGM), O('Service interval, miles', 'int', VL('interval_miles')), O('Share of the interval used', 'pct', RATIO14),
    O('Average months between services', 'num', 'IF(%s>1,ROUND((%s-%s)/(%s-1)/30.4,1),0)' % (N14, MAXD, MIND, N14)), O('Service interval, months', 'int', VL('interval_months')),
    O('Services a year at the actual pace', 'num', 'IFERROR(ROUND(%s/%s,1),0)' % (VL('miles_12m'), AVGM)), O('Services a year at the interval', 'num', 'IFERROR(ROUND(%s/%s,1),0)' % (VL('miles_12m'), VL('interval_miles'))),
    O('Extra cost a year of servicing early', 'money', 'MAX(0,IFERROR(%s/%s-%s/%s,0))*{in:svc}' % (VL('miles_12m'), AVGM, VL('miles_12m'), VL('interval_miles'))),
    O('Verdict', 'text', 'IF(%s<2,%s,IF(%s<{in:early},%s,IF(%s>{in:late},%s,%s)))' % (N14, cb('Not enough services yet'), RATIO14, cb('Serving early, costs extra'), RATIO14, cb('Late'), cb('On time')))],
    GR('What if', ('Late only above 120%', {'late': 1.2}), ('Early below 95%', {'early': 0.95}), ('A service costs 180', {'svc': 180}))))

# 15 ----------------------------------------------------------- workshop vendor scorecard
VS = lambda col, lo, hi=None: 'SUMIFS(%s,%s,{in:vendor},%s,">="&({today}-%d)%s)' % (R('service_log', col), R('service_log', 'vendor'), R('service_log', 'date'), lo, (',%s,"<"&({today}-%d)' % (R('service_log', 'date'), hi)) if hi else '')
VC = lambda lo, hi=None: 'COUNTIFS(%s,{in:vendor},%s,">="&({today}-%d)%s)' % (R('service_log', 'vendor'), R('service_log', 'date'), lo, (',%s,"<"&({today}-%d)' % (R('service_log', 'date'), hi)) if hi else '')
CPV = 'IFERROR(%s/%s,0)' % (VS('cost', 365), VC(365)); CPV0 = 'IFERROR(%s/%s,0)' % (VS('cost', 730, 365), VC(730, 365)); DPV = 'IFERROR(%s/%s,0)' % (VS('days_off_road', 365), VC(365))
CH15 = 'IF(%s>0,%s/%s-1,0)' % (CPV0, CPV, CPV0)
tools.append(TOOL('vendor_scorecard', 'Workshop Vendor Scorecard', 'Which workshop to keep, push on price or replace',
    'Spend, visits, days off road and cost per visit of one vendor against the same vendor a year ago; high cost and slow turnaround together mean try another workshop.', [
    IL('vendor', 'Workshop vendor', 'vendor', VENDOR['Mechanic']), I('target', 'Days off road per visit you accept', 2.0, 'num'), I('tol', 'Cost per visit rise you accept', 0.15, 'pct')], [
    O('Spend, 12 months', 'money', VS('cost', 365)), O('Visits, 12 months', 'int', VC(365)), O('Average days off road per visit', 'num', DPV), O('Cost per visit', 'money', CPV),
    O('Cost per visit a year earlier', 'money', CPV0), O('Change in cost per visit', 'pct', CH15), O('Share of all workshop spend', 'pct', 'IFERROR(%s/SUMIFS(%s,%s,">="&({today}-365)),0)' % (VS('cost', 365), R('service_log', 'cost'), R('service_log', 'date'))),
    O('Cost per day off road', 'money', 'IFERROR(%s/%s,0)' % (VS('cost', 365), VS('days_off_road', 365))),
    O('Verdict', 'text', 'IF(AND(%s>{in:tol},%s>{in:target}),%s,IF(OR(%s>{in:tol},%s>{in:target}),%s,%s))' % (CH15, DPV, cb('Try another workshop'), CH15, DPV, cb('Renegotiate'), cb('Keep')))],
    GR('What if', ('Accept 1 day per visit', {'target': 1.0}), ('Accept 3 days per visit', {'target': 3.0}), ('Accept no rise', {'tol': 0.0}))))

# 16 ----------------------------------------------------------- service backlog burn-down
SD = lambda c: R('service_due', c)
OVR = 'COUNTIFS(%s,%s)' % (SD('due_by'), ca('Service now'))
NEXT28 = 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<="&({today}+28))' % (SD('due_by'), '"<>"&' + ca('Service now'), SD('due_date'), SD('due_date'))
TOT16 = '(%s+%s)' % (OVR, NEXT28)
tools.append(TOOL('backlog_burndown', 'Service Backlog Burn-Down', 'How fast can the workshop clear the services that are due',
    'Cars past their interval plus the cars falling due in the next 4 weeks, against the workshop slots you can use each week.', [
    I('slots', 'Workshop slots a week', 5, 'int'), I('weeks', 'Weeks you want the backlog cleared in', 4, 'int')], [
    O('Cars overdue now', 'int', OVR), O('Cars due in the next 28 days', 'int', NEXT28), O('Backlog', 'int', TOT16), O('Weeks to clear at your slots', 'int', 'IF({in:slots}>0,ROUNDUP(%s/{in:slots},0),0)' % TOT16),
    O('Slots a week needed to clear it in time', 'int', 'IF({in:weeks}>0,ROUNDUP(%s/{in:weeks},0),0)' % TOT16), O('Extra slots a week needed', 'int', 'MAX(0,IF({in:weeks}>0,ROUNDUP(%s/{in:weeks},0),0)-{in:slots})' % TOT16),
    O('Verdict', 'text', 'IF(IF({in:slots}>0,ROUNDUP(%s/{in:slots},0),99)<={in:weeks},%s&" "&IF({in:slots}>0,ROUNDUP(%s/{in:slots},0),0),%s)' % (TOT16, cb('Backlog clears in weeks'), TOT16, cb('Add a workshop slot')))],
    GR('What if', ('One slot a week', {'slots': 1}), ('Two slots a week', {'slots': 2}), ('Clear it in one week', {'weeks': 1}))))

# 17 ----------------------------------------------------------- next-service forecast
def WK(k): return 'IF({in:scen}=%s,COUNTIFS(%s,%d),IF({in:scen}=%s,COUNTIFS(%s,%d),COUNTIFS(%s,%d)))' % (tok('scen', 'Base'), SD('wk_base'), k, tok('scen', 'Best'), SD('wk_best'), k, SD('wk_worst'), k)
PK = 'IF({in:scen}=%s,MAX(%s),IF({in:scen}=%s,MAX(%s),MAX(%s)))' % (tok('scen', 'Base'), SD('peers_base'), tok('scen', 'Best'), SD('peers_best'), SD('peers_worst'))
PKW = 'IF({in:scen}=%s,INDEX(%s,MATCH(MAX(%s),%s,0)),IF({in:scen}=%s,INDEX(%s,MATCH(MAX(%s),%s,0)),INDEX(%s,MATCH(MAX(%s),%s,0))))' % (
    tok('scen', 'Base'), SD('wk_base'), SD('peers_base'), SD('peers_base'), tok('scen', 'Best'), SD('wk_best'), SD('peers_best'), SD('peers_best'), SD('wk_worst'), SD('peers_worst'), SD('peers_worst'))
tools.append(TOOL('service_forecast', 'Next-Service Forecast', 'In which week do most services fall due',
    'Services due each week for the next 12 weeks from the miles each vehicle drives a day; Best assumes 15% fewer miles and Worst 20% more.', [
    IL('scen', 'Scenario', 'scen', 'Base'), I('slots', 'Workshop slots a week', 5, 'int')], [
    O('Week %d' % 1, 'int', WK(1))] + [O('Week %d' % k, 'int', WK(k)) for k in range(2, 13)] + [
    O('Services due in 12 weeks, Base', 'int', 'COUNTIFS(%s,">0")' % SD('wk_base')), O('Services due in 12 weeks, Best', 'int', 'COUNTIFS(%s,">0")' % SD('wk_best')),
    O('Services due in 12 weeks, Worst', 'int', 'COUNTIFS(%s,">0")' % SD('wk_worst')), O('Busiest week', 'int', PKW), O('Services in the busiest week', 'int', PK),
    O('Verdict', 'text', 'IF(%s>{in:slots},%s,%s&" "&%s&": "&%s)' % (PK, cb('Add a workshop slot'), cb('Peak in week'), PKW, cb('Book ahead')))],
    GR('What if', ('Best case', {'scen': '=' + tok('scen', 'Best')}), ('Worst case', {'scen': '=' + tok('scen', 'Worst')}), ('Three slots a week', {'slots': 3}))))

# 18 ----------------------------------------------------------- downtime cost
UT18 = 'IF({in:util}>0,{in:util},%s)' % VL('util_12m'); AD18 = ADR(VLT('class'))
tools.append(TOOL('downtime_cost', 'Downtime Cost', 'Does the downtime cost more than the repair itself',
    'Workshop days times the utilisation and the class average daily rate give the rental revenue lost, compared with the repair or service cost.', [
    I('veh', 'Vehicle', 'Midsize SUV 04 Green', 'text'), I('wdays', 'Days in the workshop', 3, 'int'), I('repair', 'Repair or service cost', 280), I('util', 'Utilisation to use, 0 uses the vehicle 12-month figure', 0, 'pct')], [
    O('Class', 'text', VLT('class')), O('Average daily rate of the class', 'money', AD18), O('Utilisation used', 'pct', UT18), O('Rental days lost', 'num', 'ROUND({in:wdays}*%s,1)' % UT18),
    O('Rental revenue lost', 'money', 'ROUND({in:wdays}*%s*(%s),0)' % (UT18, AD18)), O('Repair or service cost', 'money', '{in:repair}'),
    O('Downtime cost less repair cost', 'money', 'ROUND({in:wdays}*%s*(%s)-{in:repair},0)' % (UT18, AD18)), O('Total cost of the visit', 'money', 'ROUND({in:wdays}*%s*(%s)+{in:repair},0)' % (UT18, AD18)),
    O('Revenue lost for each extra day', 'money', 'ROUND(%s*(%s),0)' % (UT18, AD18)),
    O('Verdict', 'text', 'IF({in:wdays}*%s*(%s)>{in:repair},%s,%s)' % (UT18, AD18, c2('Downtime costs more than the repair'), c2('Repair costs more than the downtime')))],
    GR('What if', ('One day in the workshop', {'wdays': 1}), ('Five days in the workshop', {'wdays': 5}), ('Ten days in the workshop', {'wdays': 10}), ('A 600 repair', {'repair': 600}))))
assert len(tools) == 18, len(tools)
