"""Car rental suite part 7: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr7_lists import *
from cr7_tables import SV, VM, W3, W12, LY3, MS, OKS
import cr7_data as D

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dflt): return IN(k, label, 'list', key(lst, dflt), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def R(t, c): return '{range:%s.%s}' % (t, c)
def CLK(c): return '=' + tok('class', c)
PCT = lambda x: 'ROUND((%s)*100,0)&"%%"' % x
def U(*cond): return 'IFERROR(%s/%s,0)' % (SV('rented_days', *cond), SV('available_days', *cond))
def IDX(t, c, keycol, v): return 'INDEX(%s,MATCH(%s,%s,0))' % (R(t, c), v, R(t, keycol))
RED, AMB, GRN = tok('band', 'Red'), tok('band', 'Amber'), tok('band', 'Green')
LOWV = D.ST['low_vehicle_name']
tools = []
CLC = VM('class') + ',{in:class}'
VHC = VM('vehicle') + ',{in:vehicle}'

# 1 utilisation by vehicle and class
tools.append(TOOL('util_tool', 'Utilisation by Vehicle and Class', 'Which vehicles are red and is a class below its own usual',
    'Pick a class: its utilisation (rented days as a share of available days) for the last 3 months is set against its own last 12 months and the same months last year, with the red, amber and green vehicle counts from your settings.', [
    IL('class', 'Class', 'class', 'Premium')], [
    O('Fleet utilisation, last 3 months', 'pct', U(W3)), O('Fleet utilisation, same 3 months last year', 'pct', U(LY3)),
    O('Class utilisation, last 3 months', 'pct', U(CLC, W3)), O('Class utilisation, last 12 months', 'pct', U(CLC, W12)), O('Class utilisation, same 3 months last year', 'pct', U(CLC, LY3)),
    O('Class against its own usual, points', 'pct', U(CLC, W3) + '-' + U(CLC, W12)),
    O('Vehicles red', 'int', 'COUNTIFS(%s,%s)' % (R('util_vehicle', 'band'), RED)), O('Vehicles amber', 'int', 'COUNTIFS(%s,%s)' % (R('util_vehicle', 'band'), AMB)),
    O('Vehicles green', 'int', 'COUNTIFS(%s,%s)' % (R('util_vehicle', 'band'), GRN)), O('Vehicles red in this class', 'int', 'COUNTIFS(%s,{in:class},%s,%s)' % (R('util_vehicle', 'class'), R('util_vehicle', 'band'), RED)),
    O('Verdict', 'text', 'COUNTIFS(%s,%s)&" vehicles red, "&{in:class}&IF(%s<%s," is below its own usual"," is at or above its own usual")' % (R('util_vehicle', 'band'), RED, U(CLC, W3), U(CLC, W12)))],
    GR('What if', *[(c, {'class': CLK(c)}) for c in ('Economy', 'Compact', 'Midsize SUV', '7-seat Van', 'Electric')])))

# 2 profit per vehicle per day
PD = lambda col: 'IFERROR(%s/%s,0)' % (SV(col, VHC, W12), SV('available_days', VHC, W12))
RK = IDX('vprofit', 'rank', 'vehicle', '{in:vehicle}')
tools.append(TOOL('profit_day_tool', 'Profit per Vehicle per Day', 'Does this vehicle earn its place, per available day',
    'Type a vehicle: revenue per available day less financing, insurance, maintenance, cleaning, fuel or charge, depreciation and marketplace fees gives profit per day, ranked against the fleet, with a Keep, Reprice or Sell verdict. Profit is a contribution before office pay and overhead.', [
    I('vehicle', 'Vehicle', LOWV, 'text'), I('rise', 'Rate rise to test', 0.05, 'pct')], [
    O('Revenue per available day', 'money', PD('revenue')), O('Financing per day', 'money', PD('financing')), O('Insurance per day', 'money', PD('insurance')), O('Maintenance per day', 'money', PD('maintenance')),
    O('Cleaning per day', 'money', PD('cleaning')), O('Fuel or charge per day', 'money', PD('fuel_charge')), O('Depreciation per day', 'money', PD('depreciation')), O('Marketplace fees per day', 'money', PD('channel_fees')),
    O('Profit per available day', 'money', PD('profit')), O('Profit, last 12 months', 'money', SV('profit', VHC, W12)),
    O('Rank among vehicles (1 is best)', 'int', 'IFERROR(%s,0)' % RK), O('Vehicles ranked', 'int', 'COUNT(%s)' % R('vprofit', 'rank')),
    O('Best vehicle per day', 'text', 'INDEX(%s,MATCH(1,%s,0))' % (R('vprofit', 'vehicle'), R('vprofit', 'rank'))), O('Best profit per day', 'money', 'MAX(%s)' % R('vprofit', 'profit_per_day')),
    O('Profit per day with the rate rise', 'money', PD('profit') + '+{in:rise}*(%s-%s)' % (PD('revenue'), PD('channel_fees'))),
    O('Verdict', 'text', '{in:vehicle}&": "&IFERROR(%s,"no data")' % IDX('verdict', 'verdict', 'vehicle', '{in:vehicle}'))],
    GR('Rate rise', ('No rise', {'rise': 0}), ('Rise 10%', {'rise': 0.10}), ('Rise 15%', {'rise': 0.15}), ('Rise 20%', {'rise': 0.20}))))

# 3 break-even per vehicle
BE = lambda c: IDX('breakeven', c, 'vehicle', '{in:vehicle}')
BE_NEW = 'IF(%s*(1+{in:change})-%s>0,MIN(1,%s/(%s*(1+{in:change})-%s)),1)' % (BE('day_rate'), BE('var_per_day'), BE('fixed_per_day'), BE('day_rate'), BE('var_per_day'))
tools.append(TOOL('breakeven_tool', 'Break-even Utilisation per Vehicle', 'Is this vehicle above the utilisation at which it covers its cost',
    'Fixed cost per available day divided by the rate per rented day less the variable cost per rented day gives the break-even utilisation; test a rate change and see the extra rented days needed.', [
    I('vehicle', 'Vehicle', LOWV, 'text'), I('change', 'Rate change to test', 0.0, 'pct')], [
    O('Fixed cost per available day', 'money', BE('fixed_per_day')), O('Rate per rented day', 'money', BE('day_rate')), O('Variable cost per rented day', 'money', BE('var_per_day')),
    O('Actual utilisation, 12 months', 'pct', BE('actual_util')), O('Break-even utilisation at the tested rate', 'pct', BE_NEW),
    O('Gap to break-even, points', 'pct', BE('actual_util') + '-(' + BE_NEW + ')'), O('Loss months of the last 12', 'int', BE('months_below')),
    O('Rented days needed a year', 'int', 'ROUND(%s*(%s),0)' % (BE('avail_12m'), BE_NEW)), O('Rented days in the last 12 months', 'int', BE('rented_12m')),
    O('Extra rented days needed', 'int', 'MAX(0,ROUND(%s*(%s),0)-%s)' % (BE('avail_12m'), BE_NEW, BE('rented_12m'))),
    O('Rate needed at the actual utilisation', 'money', 'IF(%s>0,%s/%s+%s,0)' % (BE('actual_util'), BE('fixed_per_day'), BE('actual_util'), BE('var_per_day'))),
    O('Verdict', 'text', 'IF(%s>=%s,{in:vehicle}&" is above break-even","Below break-even for "&%s&" months, act")' % (BE('actual_util'), BE_NEW, BE('months_below')))],
    GR('Rate change', ('Rate +5%', {'change': 0.05}), ('Rate +10%', {'change': 0.10}), ('Rate +20%', {'change': 0.20}), ('Rate +30%', {'change': 0.30}))))

# 4 loss-making vehicle list
KTH = 'SMALL(%s,{in:rank})' % R('vprofit', 'profit_12m')
KV = 'INDEX(%s,MATCH(%s,%s,0))' % (R('vprofit', 'vehicle'), KTH, R('vprofit', 'profit_12m'))
KB = lambda c: 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('breakeven', c), KV, R('breakeven', 'vehicle'))
KMONTHS = 'COUNTIFS(%s,%s,%s)' % (VM('vehicle'), KV, W12)
tools.append(TOOL('loss_tool', 'Loss-making Vehicle List', 'Which vehicles lose money and how many rented days would recover it',
    'Pick a rank (1 is the biggest loss): the vehicle, its loss over 12 months and per month, and the extra rented days a month at its own margin that would recover the loss; the counts show how many vehicles lose in all of the last 3 or 12 months.', [
    I('rank', 'Rank of the loss (1 is the largest)', 1, 'int')], [
    O('Vehicle at this rank', 'text', 'IF(%s<0,%s,"No loss at this rank")' % (KTH, KV)), O('Profit, last 12 months', 'money', KTH), O('Months with data', 'int', KMONTHS),
    O('Loss a month', 'money', 'MAX(0,-%s/MAX(1,%s))' % (KTH, KMONTHS)), O('Margin per rented day', 'money', '%s-%s' % (KB('day_rate'), KB('var_per_day'))),
    O('Extra rented days a month to recover', 'num', 'IF(%s-%s>0,MAX(0,-%s/MAX(1,%s))/(%s-%s),0)' % (KB('day_rate'), KB('var_per_day'), KTH, KMONTHS, KB('day_rate'), KB('var_per_day'))),
    O('Vehicles with a loss in all of the last 3 months', 'int', 'COUNTIFS(%s,3)' % R('breakeven', 'loss_3m')), O('Vehicles with a loss in all of the last 12 months', 'int', 'COUNTIFS(%s,">=12")' % R('breakeven', 'months_below')),
    O('Vehicles with a loss over 12 months', 'int', 'COUNTIFS(%s,"<0")' % R('vprofit', 'profit_12m')), O('Total of those losses', 'money', '-SUMIFS(%s,%s,"<0")' % (R('vprofit', 'profit_12m'), R('vprofit', 'profit_12m'))),
    O('Verdict', 'text', 'IF(%s<0,%s&" loses "&ROUND(MAX(0,-%s/MAX(1,%s)),0)&" a month",%s&" is not losing money")' % (KTH, KV, KTH, KMONTHS, KV))],
    GR('Rank', ('Largest loss', {'rank': 1}), ('Second', {'rank': 2}), ('Third', {'rank': 3}), ('Fourth', {'rank': 4}), ('Fifth', {'rank': 5}))))

# 5 idle-day finder
AK = 'LARGE(%s,{in:rank})' % R('idle_runs', 'act_key')
AI = lambda c: 'INDEX(%s,MATCH(%s,%s,0))' % (R('idle_runs', c), AK, R('idle_runs', 'act_key'))
tools.append(TOOL('idle_tool', 'Idle-Day Finder', 'Which idle run do I fill first and at what price',
    'Idle days are days a vehicle is available but not rented. Runs of 3 or more idle days still open are ranked by lost revenue at the class rate; the offer price and the revenue gain if filled at that price are shown.', [
    I('rank', 'Rank of the idle run (1 is the largest)', 1, 'int'), I('discount', 'Discount to offer', 0.15, 'pct')], [
    O('Idle runs still open', 'int', 'COUNTIFS(%s,">0")' % R('idle_runs', 'open_days')), O('Vehicle at this rank', 'text', 'IFERROR(%s,"")' % AI('vehicle')), O('Class', 'text', 'IFERROR(%s,"")' % AI('class')),
    O('Offer from', 'date', 'IFERROR(%s,"")' % AI('date')), O('Run ends', 'date', 'IFERROR(%s,"")' % AI('to_date')), O('Idle days still open', 'int', 'IFERROR(%s,0)' % AI('open_days')),
    O('Class day rate', 'money', 'IFERROR(%s,0)' % AI('rate_card')), O('Offer price a day', 'money', 'IFERROR(ROUND(%s*(1-{in:discount}),0),0)' % AI('rate_card')),
    O('Revenue if filled at the offer', 'money', 'IFERROR(%s*ROUND(%s*(1-{in:discount}),0),0)' % (AI('open_days'), AI('rate_card'))), O('Revenue lost if it stays idle', 'money', 'IFERROR(%s,0)' % AI('open_lost')),
    O('Idle days in the next 14 days', 'int', 'SUM(%s)' % R('idle_runs', 'next14_days')), O('Revenue lost to idle runs, last 30 days', 'money', 'SUM(%s)' % R('idle_runs', 'last30_lost')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">0")=0,"No open idle run","Offer "&%s&" at "&ROUND(%s*(1-{in:discount}),0)&" a day from the date shown")' % (R('idle_runs', 'open_days'), AI('vehicle'), AI('rate_card')))],
    GR('Rank and discount', ('Largest run', {'rank': 1}), ('Second run', {'rank': 2}), ('Third run', {'rank': 3}), ('Discount 10%', {'discount': 0.10}), ('Discount 25%', {'discount': 0.25}))))

# 6 discount-to-fill floor
VAR6 = 'IFERROR((%s+%s+%s)/%s,0)' % (SV('maintenance', CLC, W12), SV('cleaning', CLC, W12), SV('fuel_charge', CLC, W12), SV('rented_days', CLC, W12))
CARD6 = 'SUMIFS(%s,%s,{in:class})' % (R('classes', 'daily_rate'), R('classes', 'class'))
FLOOR6 = '%s/(1-{in:fee_pct})' % VAR6
tools.append(TOOL('floor_tool', 'Discount-to-Fill Floor', 'How low can the price go for an idle gap and still cover the cost',
    'Closed form: the variable cost of a rented day (maintenance, cleaning, fuel or charge) divided by what you keep after the channel fee is the lowest price that does not lose money; test an offer price.', [
    IL('class', 'Class', 'class', 'Compact'), I('gap_days', 'Days in the gap', 4, 'int'), I('fee_pct', 'Channel fee share (0 for a direct booking)', 0.0, 'pct'), I('offer', 'Offer price a day', 42)], [
    O('Class day rate', 'money', CARD6), O('Variable cost per rented day', 'money', VAR6), O('Lowest safe price a day', 'money', FLOOR6),
    O('Room to discount from the card', 'pct', 'MAX(0,1-(%s)/%s)' % (FLOOR6, CARD6)), O('Offer discount from the card', 'pct', '1-{in:offer}/%s' % CARD6),
    O('Margin a day at the offer', 'money', '{in:offer}*(1-{in:fee_pct})-%s' % VAR6), O('Revenue from the gap at the offer', 'money', '{in:gap_days}*{in:offer}'),
    O('Contribution from the gap at the offer', 'money', '{in:gap_days}*({in:offer}*(1-{in:fee_pct})-%s)' % VAR6),
    O('Verdict', 'text', 'IF({in:offer}>=%s,"Discount down to "&ROUND(%s,0)&" is safe","Offer is below cost: the floor is "&ROUND(%s,0))' % (FLOOR6, FLOOR6, FLOOR6))],
    GR('Offer price', ('Offer 35', {'offer': 35}), ('Offer 30', {'offer': 30}), ('Offer 20', {'offer': 20}), ('Marketplace A fee', {'fee_pct': 0.20}), ('Longer gap, 7 days', {'gap_days': 7}))))

# 7 rate against history
def AD(col, *cond): return 'SUMIFS(%s,%s,{in:class},%s)' % (R('adr_class', col), R('adr_class', 'class'), ','.join(cond))
M3 = '%s,">="&EDATE(%s,-2)' % (R('adr_class', 'month'), MS)
MLY = '%s,">="&EDATE(%s,-14),%s,"<="&EDATE(%s,-12)' % (R('adr_class', 'month'), MS, R('adr_class', 'month'), MS)
A3 = 'IFERROR(%s/%s,0)' % (AD('rental_revenue', M3), AD('rented_days', M3)); ALY = 'IFERROR(%s/%s,0)' % (AD('rental_revenue', MLY), AD('rented_days', MLY))
tools.append(TOOL('rate_hist_tool', 'Rate Against History', 'Are discounts pulling the rate of a class under last year',
    'Pick a class: the average daily rate (ADR, revenue per rented day) of the last 3 months against the same months last year and against the rate card, with the discount share given.', [
    IL('class', 'Class', 'class', 'Compact')], [
    O('Achieved rate, last 3 months', 'money', A3), O('Achieved rate, same 3 months last year', 'money', ALY), O('Change against last year', 'money', A3 + '-' + ALY),
    O('Rate card day price', 'money', 'SUMIFS(%s,%s,{in:class})' % (R('classes', 'daily_rate'), R('classes', 'class'))), O('Card rate with the season, last 3 months', 'money', 'IFERROR(%s/%s,0)' % (AD('list_revenue', M3), AD('rented_days', M3))),
    O('Discount share, last 3 months', 'pct', 'IFERROR(MAX(0,1-%s/%s),0)' % (AD('rental_revenue', M3), AD('list_revenue', M3))), O('Discount share, same months last year', 'pct', 'IFERROR(MAX(0,1-%s/%s),0)' % (AD('rental_revenue', MLY), AD('list_revenue', MLY))),
    O('Months below last year, of 12', 'int', 'COUNTIFS(%s,{in:class},%s,%s)' % (R('adr_ly', 'class'), R('adr_ly', 'flag'), tok('flag', 'Below last year'))),
    O('All classes: achieved rate, last 3 months', 'money', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (R('adr_class', 'rental_revenue'), M3, R('adr_class', 'rented_days'), M3)),
    O('Verdict', 'text', 'IF(%s<0,{in:class}&" is "&ROUND(-(%s-%s),0)&" below last year, review the discounts",{in:class}&" is "&ROUND(%s-%s,0)&" above last year, hold the discounts")' % (A3 + '-' + ALY, A3, ALY, A3, ALY))],
    GR('What if', *[(c, {'class': CLK(c)}) for c in ('Economy', 'Midsize SUV', '7-seat Van', 'Premium', 'Electric')])))

# 8 demand forecast and weekend pressure
def SC(base, best, worst): return 'IF({in:scenario}=%s,SUM(%s),IF({in:scenario}=%s,SUM(%s),SUM(%s)))' % (tok('scenario', 'Best'), R('forecast', best), tok('scenario', 'Worst'), R('forecast', worst), R('forecast', base))
FC8 = SC('forecast_days', 'forecast_best', 'forecast_worst'); SH8 = SC('shortage_days', 'short_best', 'short_worst'); SU8 = SC('surplus_days', 'surplus_best', 'surplus_worst')
F_ = R('forecast', 'fleet_days')
WK0 = '({today}-WEEKDAY({today},2)+1)'
tools.append(TOOL('forecast_tool', 'Demand Forecast and Weekend Pressure', 'Where will the next 12 weeks be short of cars, and where is there room to promote',
    'Booked days, last year same weeks times your trend factor and the fleet days give a forecast for each week; pick Base, Best or Worst and see the shortage and surplus days and the weekend load.', [
    IL('scenario', 'Scenario', 'scenario', 'Base')], [
    O('Booked days, next 12 weeks', 'int', 'SUM(%s)' % R('forecast', 'booked_days')), O('Fleet days, next 12 weeks', 'int', 'SUM(%s)' % F_), O('Last year same weeks, days', 'int', 'SUM(%s)' % R('forecast', 'last_year_days')),
    O('Forecast days in this scenario', 'int', FC8), O('Shortage days in this scenario', 'int', SH8), O('Surplus days in this scenario', 'int', SU8), O('Fleet load in this scenario', 'pct', 'IFERROR((%s)/SUM(%s),0)' % (FC8, F_)),
    O('Weekend load, next 4 weeks', 'pct', 'IFERROR(SUMIFS(%s,%s,"<"&(%s+28))/SUMIFS(%s,%s,"<"&(%s+28)),0)' % (R('forecast', 'weekend_booked'), R('forecast', 'week'), WK0, R('forecast', 'weekend_fleet'), R('forecast', 'week'), WK0)),
    O('Week of the largest shortage (base)', 'date', 'IF(MAX(%s)>0,INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (R('forecast', 'shortage_days'), R('forecast', 'week'), R('forecast', 'shortage_days'), R('forecast', 'shortage_days'))),
    O('Largest shortage in one week and class (base)', 'int', 'MAX(%s)' % R('forecast', 'shortage_days')),
    O('Week from now with the most surplus (base)', 'int', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),0)' % (R('forecast', 'week_no'), R('forecast', 'surplus_days'), R('forecast', 'surplus_days'))),
    O('Verdict', 'text', 'IF((%s)>0,"Raise rates: "&(%s)&" days short",IF(IFERROR((%s)/SUM(%s),0)<{set:util_target}-0.15,"Promote in week "&IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),0),"Hold"))' % (SH8, SH8, FC8, F_, R('forecast', 'week_no'), R('forecast', 'surplus_days'), R('forecast', 'surplus_days')))],
    GR('Scenario', ('Base', {'scenario': '=' + tok('scenario', 'Base')}), ('Best', {'scenario': '=' + tok('scenario', 'Best')}), ('Worst', {'scenario': '=' + tok('scenario', 'Worst')}))))

# 9 revenue per available car-day
RP = 'IFERROR(%s/%s,0)' % (SV('revenue', CLC, W3), SV('available_days', CLC, W3))
TG9 = 'SUMIFS(%s,%s,{in:class})' % (R('revpac_class', 'target'), R('revpac_class', 'class'))
ADR9 = 'IFERROR(%s/%s,0)' % (SV('revenue', CLC, W3), SV('rented_days', CLC, W3))
tools.append(TOOL('revpac_tool', 'Revenue per Available Car-Day', 'Does a class earn its target for every day it is available',
    'Revenue per available car-day (RevPAC) is revenue divided by available days, the same as the average daily rate times utilisation; pick a class and compare it with your target.', [
    IL('class', 'Class', 'class', 'Premium')], [
    O('RevPAC of the class, last 3 months', 'money', RP), O('Your target', 'money', TG9), O('Gap to the target', 'money', RP + '-' + TG9),
    O('Average daily rate, revenue per rented day', 'money', ADR9), O('Utilisation, last 3 months', 'pct', U(CLC, W3)), O('Average daily rate times utilisation', 'money', ADR9 + '*' + U(CLC, W3)),
    O('Utilisation needed for the target at this rate', 'pct', 'IF(%s>0,MIN(1,%s/%s),0)' % (ADR9, TG9, ADR9)), O('RevPAC of the whole fleet', 'money', 'IFERROR(%s/%s,0)' % (SV('revenue', W3), SV('available_days', W3))),
    O('Verdict', 'text', '{in:class}&" earns "&ROUND(%s,1)&" against "&%s&IF(%s>=%s," (on target)"," (below target)")' % (RP, TG9, RP, TG9))],
    GR('What if', *[(c, {'class': CLK(c)}) for c in ('Economy', 'Compact', 'Midsize SUV', '7-seat Van', 'Electric')])))

# 10 class mix review
def PK(c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('vprofit', 'cpv'), c, R('vprofit', 'class'))
PSEL = PK('{in:class}')
SHARE10 = 'IFERROR(%s/%s,0)' % (SV('available_days', CLC, W12), SV('available_days', W12))
RANK10 = '1+' + '+'.join('(%s>%s)' % (PK(tok('class', c)), PSEL) for c in CLASSES)
tools.append(TOOL('mix_tool', 'Class Mix Review', 'Should I add a car to this class or trim it',
    'Pick a class: profit per vehicle over 12 months and its share of fleet days, ranked against the six classes; the best class with a small share is worth adding to, the lowest below your limit is worth trimming.', [
    IL('class', 'Class', 'class', 'Midsize SUV'), I('trim_below', 'Profit per vehicle below which you trim', 500), I('add_share', 'Fleet share below which you add to the best class', 0.20, 'pct')], [
    O('Vehicles in the class with data', 'int', 'COUNTIFS(%s,{in:class},%s,">0")' % (R('vprofit', 'class'), R('vprofit', 'avail_12m'))), O('Profit per vehicle, 12 months', 'money', PSEL),
    O('Share of fleet days', 'pct', SHARE10), O('Rank among the 6 classes (1 is best)', 'int', RANK10), O('Utilisation, 12 months', 'pct', U(CLC, W12)),
    O('Profit of the class, 12 months', 'money', SV('profit', CLC, W12)), O('Fleet profit per vehicle', 'money', 'IFERROR(SUMIFS(%s,%s,">0")/COUNTIFS(%s,">0"),0)' % (R('vprofit', 'profit_12m'), R('vprofit', 'avail_12m'), R('vprofit', 'avail_12m')) if False else 'IFERROR(SUM(%s)/COUNTIFS(%s,">0"),0)' % (R('vprofit', 'profit_12m'), R('vprofit', 'avail_12m'))),
    O('Verdict', 'text', 'IF(AND(%s=1,%s<{in:add_share}),"Add a "&{in:class},IF(OR(%s<{in:trim_below},%s=6),"Trim "&{in:class},"Balanced"))' % (RANK10, SHARE10, PSEL, RANK10))],
    GR('What if', *[(c, {'class': CLK(c)}) for c in ('Economy', 'Compact', '7-seat Van', 'Premium', 'Electric')])))

# 11 channel profit per day
NET11 = IDX('chprofit', 'net_per_day', 'channel', '{in:channel}')
AVG11 = 'IFERROR((SUMIFS(%s,%s)-SUMIFS(%s,%s))/SUM(%s),0)' % (R('bookings', 'net_amount'), OKS, R('bookings', 'delivery_fee'), OKS, R('bookings', 'rented_days'))
BEST11 = 'MAX(%s)' % R('chprofit', 'net_per_day')
tools.append(TOOL('channel_tool', 'Channel Profit per Day', 'Which booking channel should I feed and which should I cut',
    'The net rate per rented day after the channel fee (the share a car-sharing marketplace keeps) and without the delivery fee, by channel, set against your average; test moving days to the best channel.', [
    IL('channel', 'Channel', 'channel', 'Marketplace A'), I('shift_days', 'Rented days to move to the best channel', 20, 'int'), I('cut_below', 'Cut a channel below this share of the average', 0.90, 'pct')], [
    O('Net per rented day, this channel', 'money', NET11), O('Share of rented days', 'pct', IDX('chprofit', 'share_days', 'channel', '{in:channel}')), O('Average net per rented day', 'money', AVG11),
    O('Against the average', 'money', NET11 + '-' + AVG11), O('Best channel net per rented day', 'money', BEST11), O('Best channel', 'text', 'INDEX(%s,MATCH(%s,%s,0))' % (R('chprofit', 'channel'), BEST11, R('chprofit', 'net_per_day'))),
    O('Weakest channel net per rented day', 'money', 'MIN(%s)' % R('chprofit', 'net_per_day')), O('Revenue gained by moving the days', 'money', '{in:shift_days}*(%s-%s)' % (BEST11, NET11)),
    O('Verdict', 'text', 'IF(%s>=%s,"Feed "&{in:channel},IF(%s<{in:cut_below}*%s,"Cut "&{in:channel},"Hold "&{in:channel}))' % (NET11, AVG11, NET11, AVG11))],
    GR('Channel', *[(c, {'channel': '=' + tok('channel', c)}) for c in ('Website', 'Corporate account', 'Hotel partner', 'Marketplace B')])))

# 12 season rate effectiveness
SD = lambda col, s: 'SUMIFS(%s,%s,{in:class},%s,%s)' % (R('adr_class', col), R('adr_class', 'class'), R('adr_class', 'season'), tok('season', s))
SADR = lambda s: 'IFERROR(%s/%s,0)' % (SD('rental_revenue', s), SD('rented_days', s))
SU = lambda s: 'IFERROR(SUMIFS(%s,%s,{in:class},%s,%s)/SUMIFS(%s,%s,{in:class},%s,%s),0)' % (R('util_class', 'rented_days'), R('util_class', 'class'), R('util_class', 'season'), tok('season', s), R('util_class', 'available_days'), R('util_class', 'class'), R('util_class', 'season'), tok('season', s))
PEAKD = 'SUMIFS(%s,%s,{in:class},%s,%s,%s,">="&EDATE(%s,-11))' % (R('adr_class', 'rented_days'), R('adr_class', 'class'), R('adr_class', 'season'), tok('season', 'Peak'), R('adr_class', 'month'), MS)
MULT = lambda s: 'AVERAGEIFS(%s,%s,%s)' % (R('seasons', 'multiplier'), R('seasons', 'season'), tok('season', s))
tools.append(TOOL('season_tool', 'Season Rate Effectiveness', 'Is the peak multiplier too low for how full the cars are',
    'Achieved rate and utilisation by season for a class, against the season multipliers on your rate card; test a higher peak multiplier and see the extra revenue on last peak\'s rented days.', [
    IL('class', 'Class', 'class', 'Economy'), I('test_mult', 'Peak multiplier to test', 1.35, 'num')], [
    O('Achieved rate, Off-peak', 'money', SADR('Off-peak')), O('Achieved rate, Shoulder', 'money', SADR('Shoulder')), O('Achieved rate, Peak', 'money', SADR('Peak')), O('Achieved rate, Holiday', 'money', SADR('Holiday')),
    O('Achieved peak against shoulder', 'num', 'IF(%s>0,%s/%s,0)' % (SADR('Shoulder'), SADR('Peak'), SADR('Shoulder'))), O('Peak multiplier on the rate card', 'num', MULT('Peak')),
    O('Utilisation, Off-peak', 'pct', SU('Off-peak')), O('Utilisation, Peak', 'pct', SU('Peak')),
    O('Extra revenue with the tested multiplier, last peak', 'money', 'ROUND(%s*%s*({in:test_mult}/%s-1),0)' % (PEAKD, SADR('Peak'), MULT('Peak'))),
    O('Verdict', 'text', 'IF(%s>={set:util_green},"Peak multiplier is too low, fills at "&%s,"Peak multiplier is right, fills at "&%s)' % (SU('Peak'), PCT(SU('Peak')), PCT(SU('Peak'))))],
    GR('What if', *[(c, {'class': CLK(c)}) for c in ('Compact', 'Midsize SUV', '7-seat Van', 'Premium', 'Electric')])))

# 13 fleet size fit
N13 = 'COUNTIFS(%s,{in:class},%s,"<>"&%s)' % (R('vprofit', 'class'), R('vprofit', 'status'), tok('vstatus', 'Sold'))
AV13 = SV('available_days', CLC, W3); RN13 = SV('rented_days', CLC, W3)
NEED13 = 'IFERROR(ROUNDUP(%s/(%s/%s*{set:util_target}),0),0)' % (RN13, AV13, N13)
tools.append(TOOL('fleet_tool', 'Fleet Size Fit', 'Is the fleet of this class too big, the right size or too small',
    'From the rented days of the last 3 months: utilisation with one car more and one car fewer, and the cars the class needs to reach your utilisation target (closed form).', [
    IL('class', 'Class', 'class', 'Midsize SUV')], [
    O('Cars in the class now', 'int', N13), O('Available days, last 3 months', 'int', AV13), O('Rented days, last 3 months', 'int', RN13), O('Utilisation now', 'pct', U(CLC, W3)),
    O('Utilisation with one car more', 'pct', 'IFERROR(%s/(%s*(%s+1)/%s),0)' % (RN13, AV13, N13, N13)), O('Utilisation with one car fewer', 'pct', 'IF(%s>1,IFERROR(%s/(%s*(%s-1)/%s),0),0)' % (N13, RN13, AV13, N13, N13)),
    O('Cars needed for your utilisation target', 'int', NEED13),
    O('Verdict', 'text', 'IF(%s>%s,"Fleet too small: add "&(%s-%s),IF(%s<%s,"Fleet too big: trim "&(%s-%s),"Fleet right size"))' % (NEED13, N13, NEED13, N13, NEED13, N13, N13, NEED13))],
    GR('What if', *[(c, {'class': CLK(c)}) for c in ('Economy', 'Compact', '7-seat Van', 'Premium', 'Electric')])))

# 14 utilisation target solver
FIX14 = 'IFERROR((%s+%s+%s)/%s,0)' % (SV('financing', CLC, W12), SV('insurance', CLC, W12), SV('depreciation', CLC, W12), SV('available_days', CLC, W12))
RT14 = 'IFERROR(%s/%s,0)' % (SV('revenue', CLC, W12), SV('rented_days', CLC, W12))
VR14 = 'IFERROR((%s+%s+%s+%s)/%s,0)' % (SV('maintenance', CLC, W12), SV('cleaning', CLC, W12), SV('fuel_charge', CLC, W12), SV('channel_fees', CLC, W12), SV('rented_days', CLC, W12))
TPD = '({in:target}*12/365)'
NEED14 = 'IF(%s-%s>0,MIN(1,(%s+%s)/(%s-%s)),1)' % (RT14, VR14, FIX14, TPD, RT14, VR14)
ACT14 = U(CLC, W12)
tools.append(TOOL('target_tool', 'Utilisation Target Solver', 'What utilisation does a class need for the profit I want from each vehicle',
    'Closed form: (fixed cost per available day plus the profit you want per day) divided by the rate per rented day less the variable cost per rented day, against what the class reaches.', [
    IL('class', 'Class', 'class', 'Economy'), I('target', 'Profit wanted from one vehicle a month', 300)], [
    O('Fixed cost per available day', 'money', FIX14), O('Rate per rented day', 'money', RT14), O('Variable cost per rented day', 'money', VR14), O('Profit wanted per available day', 'money', TPD),
    O('Utilisation needed', 'pct', NEED14), O('Utilisation reached, 12 months', 'pct', ACT14), O('Gap, points', 'pct', ACT14 + '-' + NEED14),
    O('Rate needed at the utilisation reached', 'money', 'IF(%s>0,(%s+%s)/%s+%s,0)' % (ACT14, FIX14, TPD, ACT14, VR14)),
    O('Verdict', 'text', '{in:class}&" needs "&%s&" and reaches "&%s' % (PCT(NEED14), PCT(ACT14)))],
    GR('Profit wanted', ('Wanted 0', {'target': 0}), ('Wanted 600', {'target': 600}), ('Wanted 1000', {'target': 1000}), ('Premium wanted 300', {'class': CLK('Premium')}))))

# 15 weekday and weekend yield
BK = lambda c: R('bookings', c)
OKB = '(%s<>%s)*(%s<>%s)' % (BK('status'), tok('bstatus', 'Cancelled'), BK('status'), tok('bstatus', 'No-show'))
WD = lambda ds: '(' + '+'.join('(%s=%s)' % (BK('start_day'), tok('wday', d)) for d in ds) + ')'
def YLD(ds): return 'IFERROR(SUMPRODUCT(%s*%s*%s*%s)/SUMPRODUCT(%s*%s*%s),0)' % (WD(ds), OKB, BK('day_rate'), BK('days'), WD(ds), OKB, BK('days'))
FRI = YLD(['Friday']); MT = YLD(['Monday', 'Tuesday', 'Wednesday', 'Thursday']); SS = YLD(['Saturday', 'Sunday'])
PR15 = 'IFERROR(SUMIFS(%s,%s,">="&%s,%s,"<"&(%s+28))/SUMIFS(%s,%s,">="&%s,%s,"<"&(%s+28)),0)' % (R('forecast', 'weekend_booked'), R('forecast', 'week'), WK0, R('forecast', 'week'), WK0, R('forecast', 'weekend_fleet'), R('forecast', 'week'), WK0, R('forecast', 'week'), WK0)
tools.append(TOOL('weekday_tool', 'Weekday and Weekend Yield', 'Is the weekend uplift high enough for how full the weekends are',
    'Average daily rate by pickup weekday from the recent bookings against the weekend uplift setting, with the weekend load of the next 4 weeks; test a higher uplift.', [
    I('step', 'Uplift increase to test', 0.04, 'pct')], [
    O('Average daily rate, Monday to Thursday pickups', 'money', MT), O('Average daily rate, Friday pickups', 'money', FRI), O('Average daily rate, Saturday and Sunday pickups', 'money', SS),
    O('Friday against Monday to Thursday', 'pct', 'IF(%s>0,%s/%s-1,0)' % (MT, FRI, MT)), O('Weekend uplift setting', 'pct', '{set:weekend_uplift}'), O('Weekend load, next 4 weeks', 'pct', PR15),
    O('Extra revenue on Friday pickups with the increase', 'money', 'ROUND(SUMPRODUCT(%s*%s*%s*%s)*{in:step},0)' % (WD(['Friday']), OKB, BK('day_rate'), BK('days'))),
    O('Verdict', 'text', 'IF(%s>={set:weekend_pressure},"Raise the weekend uplift to "&%s,"Hold the weekend uplift at "&%s)' % (PR15, PCT('{set:weekend_uplift}+{in:step}'), PCT('{set:weekend_uplift}')))],
    GR('Increase', ('Plus 2 points', {'step': 0.02}), ('Plus 6 points', {'step': 0.06}), ('Plus 10 points', {'step': 0.10}))))

# 16 vehicle age and profit
def GRP(cond, col='profit_12m'): return 'SUMIFS(%s,%s)' % (R('vprofit', col), cond)
NEWC = '%s,"<="&{in:age_cut}' % R('vprofit', 'age_months'); OLDC = '%s,">"&{in:age_cut}' % R('vprofit', 'age_months')
NEWM = '%s,"<="&{in:miles_cut}' % R('vprofit', 'odometer'); OLDM = '%s,">"&{in:miles_cut}' % R('vprofit', 'odometer')
PPD = lambda c: 'IFERROR(%s/%s,0)' % (GRP(c), GRP(c, 'avail_12m'))
tools.append(TOOL('age_tool', 'Vehicle Age and Profit', 'Do older cars earn more or less than newer ones',
    'Profit per available day for vehicles up to and over an age you choose, and up to and over a mileage you choose, from the 12 month profit of every vehicle.', [
    I('age_cut', 'Age limit, months', 24, 'int'), I('miles_cut', 'Mileage limit, miles (the demo unit, set your own)', 60000, 'int')], [
    O('Vehicles up to the age limit', 'int', 'COUNTIFS(%s,%s,">0")' % (NEWC, R('vprofit', 'avail_12m'))), O('Vehicles over the age limit', 'int', 'COUNTIFS(%s,%s,">0")' % (OLDC, R('vprofit', 'avail_12m'))),
    O('Profit per day, up to the age limit', 'money', PPD(NEWC)), O('Profit per day, over the age limit', 'money', PPD(OLDC)),
    O('Profit per day, up to the mileage limit', 'money', PPD(NEWM)), O('Profit per day, over the mileage limit', 'money', PPD(OLDM)),
    O('Average age of the fleet, months', 'int', 'ROUND(AVERAGEIFS(%s,%s,">0"),0)' % (R('vprofit', 'age_months'), R('vprofit', 'avail_12m')), ),
    O('Verdict', 'text', 'IF(%s>%s,"Older cars earn more than newer ones: "&ROUND(%s-%s,2)&" more a day","Older cars earn less than newer ones: "&ROUND(%s-%s,2)&" less a day")' % (PPD(OLDC), PPD(NEWC), PPD(OLDC), PPD(NEWC), PPD(NEWC), PPD(OLDC)))],
    GR('What if', ('Age limit 12 months', {'age_cut': 12}), ('Age limit 36 months', {'age_cut': 36}), ('Mileage limit 40,000', {'miles_cut': 40000}), ('Mileage limit 90,000', {'miles_cut': 90000}))))

# 17 cost per day trend
M17 = 'EDATE(%s,-{in:month_back})' % MS
CM = lambda col: '%s,%s' % (VM('month'), M17)
def CD17(col): return 'IFERROR(%s/%s,0)' % (SV(col, VM('month') + ',' + M17), SV('available_days', VM('month') + ',' + M17))
def RS17(c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('trend', c), M17, R('trend', 'month'))
L17 = [('Financing', 'financing', 'fin_rise'), ('Insurance', 'insurance', 'ins_rise'), ('Maintenance', 'maintenance', 'maint_rise'), ('Cleaning', 'cleaning', 'clean_rise'),
       ('Fuel or charge', 'fuel_charge', 'fuel_rise'), ('Depreciation', 'depreciation', 'dep_rise'), ('Channel fees', 'channel_fees', 'fee_rise')]
TOT17 = 'IFERROR((%s-%s)/%s,0)' % (SV('revenue', VM('month') + ',' + M17), SV('profit', VM('month') + ',' + M17), SV('available_days', VM('month') + ',' + M17))
tools.append(TOOL('costtrend_tool', 'Cost per Day Trend', 'Which cost line per available day is rising fastest against a year ago',
    'Pick how many months back: each cost line per available day for that month and its rise against the same month a year earlier, with the fastest rising line named.', [
    I('month_back', 'Months back (1 is last month)', 1, 'int')], [
    O('Total cost per available day', 'money', TOT17)] + [O('%s per day' % n, 'money', CD17(c)) for n, c, _ in L17] + [O('%s, rise on a year ago' % n, 'pct', RS17(r)) for n, _, r in L17] + [
    O('Verdict', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&" is rising fastest","No year-ago month to compare")' % (R('trend', 'top_line'), M17, R('trend', 'month')))],
    GR('Month back', ('Two months back', {'month_back': 2}), ('Three months back', {'month_back': 3}), ('Six months back', {'month_back': 6}))))

# 18 monthly performance review
def TR(c, m): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('trend', c), m, R('trend', 'month'))
def AV3(c): return 'IFERROR(AVERAGEIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s),0)' % (R('trend', c), R('trend', 'month'), MS, R('trend', 'month'), MS)
def LGT(c): return 'IF(%s>=%s,%s,IF(%s>=%s*(1-{in:tol}),%s,%s))' % (TR(c, MS), AV3(c), GRN, TR(c, MS), AV3(c), AMB, RED)
MEAS = [('Utilisation', 'utilisation', 'pct'), ('Average daily rate', 'adr', 'money'), ('Revenue per available day', 'revpac', 'money'), ('Contribution per available day', 'profit_day', 'money')]
outs18 = []
for n, c, f in MEAS:
    outs18 += [O(n + ', this month', f, TR(c, MS)), O(n + ', last 3 months', f, AV3(c)), O(n + ', same month last year', f, TR(c, 'EDATE(%s,-12)' % MS)), O(n + ', light', 'text', LGT(c))]
REDS = '+'.join('(%s<%s*(1-{in:tol}))' % (TR(c, MS), AV3(c)) for _, c, _ in MEAS)
outs18.append(O('Verdict', 'text', 'IF((%s)=0,"All four measures on track",(%s)&" of 4 measures red")' % (REDS, REDS)))
tools.append(TOOL('review_tool', 'Monthly Performance Review', 'How is this month against my last 3 months and last year',
    'This month (so far) against the average of the last 3 full months and the same month last year for utilisation, average daily rate, revenue per available day and contribution per available day, with a green, amber or red light for each.', [
    I('tol', 'Amber when within this share below the 3-month average', 0.05, 'pct')], outs18,
    GR('Tolerance', ('Tolerance 0%', {'tol': 0.0}), ('Tolerance 10%', {'tol': 0.10}), ('Tolerance 20%', {'tol': 0.20}))))
assert len(tools) == 18, len(tools)
