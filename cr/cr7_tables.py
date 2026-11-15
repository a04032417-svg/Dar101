"""Car rental suite part 7: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr7_lists import *
import cr7_data as D

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def PH(k, label, phone): return CA(k, label, 'text', '"%s"' % phone, 18)
def BUS(): return CA('business', 'Business', 'text', '{set:company}', 26)
MS = '(EOMONTH({today},-1)+1)'
def VM(c): return '{range:vmonths.%s}' % c
W3 = '%s,">="&EDATE(%s,-2)' % (VM('month'), MS)
W12 = '%s,">="&EDATE(%s,-11)' % (VM('month'), MS)
LY3 = '%s,">="&EDATE(%s,-14),%s,"<="&EDATE(%s,-12)' % (VM('month'), MS, VM('month'), MS)
def SV(col, *conds): return 'SUMIFS(%s,%s)' % (VM(col), ','.join(conds))
VEHC = '%s,{col:vehicle}' % VM('vehicle')
CLSC = '%s,{col:class}' % VM('class')
SOLD = tok('vstatus', 'Sold')
OKS = '{range:bookings.status},"<>"&%s,{range:bookings.status},"<>"&%s' % (tok('bstatus', 'Cancelled'), tok('bstatus', 'No-show'))

settings = [
    S('company', 'Your business name', 'text', COMPANY),
    S('util_red', 'Utilisation below this is red (example, set your own)', 'pct', UTIL_RED),
    S('util_green', 'Utilisation from this is green (example, set your own)', 'pct', UTIL_GREEN),
    S('util_target', 'Utilisation target (example, set your own)', 'pct', 0.75),
    S('dep_pct', 'Depreciation a month, share of price (example, set your own)', 'pct', DEP_PCT),
    S('weekend_uplift', 'Weekend uplift on short Friday pickups', 'pct', WEEKEND_UPLIFT),
    S('offer_discount', 'Discount offered to fill an idle gap', 'pct', 0.15),
    S('idle_min_days', 'Shortest idle run you count, in days', 'int', 3),
    S('long_idle_days', 'Idle run counted as long, in days', 'int', 5),
    S('target_margin', 'Contribution margin you want to hold', 'pct', 0.25),
    S('target_profit_month', 'Profit you want from one vehicle a month', 'money', 250),
    S('trend_factor', 'Demand against last year, from your own last 8 weeks', 'num', D.trend_factor()),
    S('scenario_swing', 'Best and Worst scenario swing on the forecast', 'pct', 0.10),
    S('scenario', 'Forecast scenario', 'list', key('scenario', 'Base'), list='scenario'),
    S('sell_ratio', 'Sell when utilisation is below this share of break-even', 'pct', 0.60),
    S('loss_months_warn', 'Months in a loss before you act', 'int', 3),
    S('weekend_pressure', 'Weekend load that calls for a higher weekend uplift', 'pct', 0.85),
]
assert 3 <= len(settings) <= 20
tables = []

# 1 vehicle months ------------------------------------------------------------
tables.append(T('vmonths', 'Vehicle months', 'Revenue and costs of every vehicle for every month',
    'One row per vehicle and month: available and rented days, revenue and each cost line; utilisation, idle days and the profit before office pay and overhead fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 10, required=True), C('vehicle_id', 'Vehicle ID', 'text', 10), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24), LST('class', 'Class', 'class', 12), C('month', 'Month', 'date', 11),
    C('available_days', 'Available days', 'int', 10), C('rented_days', 'Rented days', 'int', 10),
    CA('utilisation', 'Utilisation', 'pct', 'IF({col:available_days}>0,{col:rented_days}/{col:available_days},0)', 10),
    C('revenue', 'Revenue', 'money', 12), C('channel_fees', 'Channel fees', 'money', 12), C('financing', 'Financing', 'money', 12), C('insurance', 'Insurance', 'money', 12), C('maintenance', 'Maintenance', 'money', 12),
    C('cleaning', 'Cleaning', 'money', 12), C('fuel_charge', 'Fuel or charge', 'money', 12), C('depreciation', 'Depreciation', 'money', 12),
    CA('profit', 'Profit', 'money', 'ROUND({col:revenue}-{col:channel_fees}-{col:financing}-{col:insurance}-{col:maintenance}-{col:cleaning}-{col:fuel_charge}-{col:depreciation},2)', 12),
    CA('idle_days', 'Idle days', 'int', '{col:available_days}-{col:rented_days}', 9)], D.vmonths_d(), 800, [A('profit', '< 0', 'bad'), A('utilisation', '< {set:util_red}', 'warn')]))
# 2 vehicles -----------------------------------------------------------------
tables.append(T('vehicles', 'Vehicles', 'Every vehicle with class, status, price and loan payment',
    'One row per vehicle in the fleet or sold; the age in months fills in by itself from the purchase date.', [
    C('vehicle_id', 'Vehicle ID', 'text', 10, required=True), C('vehicle', 'Vehicle', 'text', 24), LST('class', 'Class', 'class', 12), LST('status', 'Status', 'vstatus', 12), C('purchase_date', 'Purchase date', 'date', 12),
    C('purchase_price', 'Purchase price', 'money', 13), C('financed', 'Financed', 'bool', 9), C('monthly_payment', 'Monthly payment', 'money', 13), C('odometer', 'Odometer, miles', 'int', 13),
    CA('age_months', 'Age, months', 'int', 'ROUND(({today}-{col:purchase_date})/30.4,0)', 10)], D.vehicles_d(), 60, [A('status', '= ' + SOLD, 'warn')]))
# 3 classes ------------------------------------------------------------------
tables.append(T('classes', 'Vehicle classes', 'Daily rate and deposit of each vehicle class',
    'Six classes with the rate card day price and the deposit, an amount held on a card or kept until the car is back; the other sheets read the day price from here.', [
    LST('class', 'Class', 'class', 14, required=True), C('daily_rate', 'Daily rate', 'money', 12), C('deposit', 'Deposit', 'money', 12)], D.classes_d(), 50))
# 4 utilisation by vehicle -----------------------------------------------------
UB = lambda col: 'IFERROR(%s/%s,0)' % (SV('rented_days', VEHC, col), SV('available_days', VEHC, col))
tables.append(T('util_vehicle', 'Utilisation by vehicle', 'Utilisation of each vehicle against its own year',
    'Utilisation is rented days as a share of available days; the last 3 months, the last 12 months and the same 3 months last year fill in, with a red, amber or green band from your settings.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), CA('class', 'Class', 'text', LKT('vehicles.class', 'vehicles.vehicle', 'vehicle'), 12),
    CA('util_3m', 'Last 3 months', 'pct', UB(W3), 10), CA('util_12m', 'Last 12 months', 'pct', UB(W12), 10),
    CA('util_ly3m', 'Same 3 months last year', 'pct', 'IFERROR(%s/%s,"")' % (SV('rented_days', VEHC, LY3), SV('available_days', VEHC, LY3)), 12),
    CA('vs_usual', 'Against own 12 months, points', 'pct', '{col:util_3m}-{col:util_12m}', 12),
    CA('band', 'Band', 'text', 'IF({col:util_3m}<{set:util_red},%s,IF({col:util_3m}>={set:util_green},%s,%s))' % (tok('band', 'Red'), tok('band', 'Green'), tok('band', 'Amber')), 9)],
    D.util_vehicle_d(), 60, [A('band', '= ' + tok('band', 'Red'), 'bad'), A('band', '= ' + tok('band', 'Green'), 'good')]))
# 5 utilisation by class and month ---------------------------------------------
tables.append(T('util_class', 'Utilisation by class and month', 'Utilisation of each class every month',
    'One row per class and month with its season; available days, rented days, utilisation and the change against the same month last year fill in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('class', 'Class', 'class', 12), C('month', 'Month', 'date', 11), LST('season', 'Season', 'season', 10),
    CA('available_days', 'Available days', 'int', SV('available_days', CLSC, '%s,{col:month}' % VM('month')), 10), CA('rented_days', 'Rented days', 'int', SV('rented_days', CLSC, '%s,{col:month}' % VM('month')), 10),
    CA('utilisation', 'Utilisation', 'pct', 'IF({col:available_days}>0,{col:rented_days}/{col:available_days},0)', 10),
    CA('vs_last_year', 'Against last year, points', 'pct', 'IFERROR({col:utilisation}-%s/%s,"")' % (SV('rented_days', CLSC, '%s,EDATE({col:month},-12)' % VM('month')), SV('available_days', CLSC, '%s,EDATE({col:month},-12)' % VM('month'))), 12)],
    D.util_class_d(), 200, [A('utilisation', '< {set:util_red}', 'warn'), A('utilisation', '>= {set:util_green}', 'good')]))
# 6 profit per vehicle ---------------------------------------------------------
tables.append(T('vprofit', 'Profit per vehicle', 'Revenue, costs and profit of each vehicle over 12 months',
    'One row per vehicle; revenue, costs, profit before office pay and overhead, profit per available day and the rank fill in by themselves from Vehicle months.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), LST('status', 'Status', 'vstatus', 12), CA('class', 'Class', 'text', LKT('vehicles.class', 'vehicles.vehicle', 'vehicle'), 12),
    CA('revenue_12m', 'Revenue, 12 months', 'money', SV('revenue', VEHC, W12), 13), CA('cost_12m', 'Costs, 12 months', 'money', 'ROUND({col:revenue_12m}-{col:profit_12m},2)', 13),
    CA('profit_12m', 'Profit, 12 months', 'money', SV('profit', VEHC, W12), 13), CA('avail_12m', 'Available days', 'int', SV('available_days', VEHC, W12), 10),
    CA('profit_per_day', 'Profit per available day', 'money', 'IF({col:avail_12m}>0,{col:profit_12m}/{col:avail_12m},0)', 12),
    CA('rank', 'Rank', 'int', 'COUNTIFS({range:vprofit.profit_per_day},">"&{col:profit_per_day})+1', 7),
    CA('cpv', 'Class profit per vehicle', 'money', 'IFERROR(SUMIFS({range:vprofit.profit_12m},{range:vprofit.class},{col:class})/COUNTIFS({range:vprofit.class},{col:class},{range:vprofit.avail_12m},">0"),0)', 12),
    CA('age_months', 'Age, months', 'int', LKN('vehicles.age_months', 'vehicles.vehicle', 'vehicle'), 9), CA('odometer', 'Odometer, miles', 'int', LKN('vehicles.odometer', 'vehicles.vehicle', 'vehicle'), 12)],
    D.vprofit_d(), 60, [A('profit_12m', '< 0', 'bad')]))
# 7 break-even by vehicle --------------------------------------------------------
tables.append(T('breakeven', 'Break-even by vehicle', 'The utilisation at which each vehicle covers its cost',
    'Break-even utilisation is the utilisation at which a vehicle covers its cost: fixed cost per available day divided by the rate per rented day less the variable cost per rented day.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), CA('class', 'Class', 'text', LKT('vehicles.class', 'vehicles.vehicle', 'vehicle'), 12),
    CA('avail_12m', 'Available days', 'int', SV('available_days', VEHC, W12), 10), CA('rented_12m', 'Rented days', 'int', SV('rented_days', VEHC, W12), 10),
    CA('fixed_per_day', 'Fixed cost per available day', 'money', 'IFERROR((%s+%s+%s)/{col:avail_12m},0)' % (SV('financing', VEHC, W12), SV('insurance', VEHC, W12), SV('depreciation', VEHC, W12)), 12),
    CA('day_rate', 'Rate per rented day', 'money', 'IFERROR(%s/{col:rented_12m},0)' % SV('revenue', VEHC, W12), 11),
    CA('var_per_day', 'Variable cost per rented day', 'money', 'IFERROR((%s+%s+%s+%s)/{col:rented_12m},0)' % (SV('maintenance', VEHC, W12), SV('cleaning', VEHC, W12), SV('fuel_charge', VEHC, W12), SV('channel_fees', VEHC, W12)), 12),
    CA('breakeven_util', 'Break-even utilisation', 'pct', 'IF({col:day_rate}-{col:var_per_day}>0,MIN(1,{col:fixed_per_day}/({col:day_rate}-{col:var_per_day})),1)', 11),
    CA('actual_util', 'Actual utilisation', 'pct', 'IF({col:avail_12m}>0,{col:rented_12m}/{col:avail_12m},0)', 10),
    CA('gap', 'Gap, points', 'pct', '{col:actual_util}-{col:breakeven_util}', 9),
    CA('months_below', 'Loss months of 12', 'int', 'COUNTIFS(%s,%s,{range:vmonths.profit},"<0")' % (VEHC, W12), 9),
    CA('loss_3m', 'Loss months of 3', 'int', 'COUNTIFS(%s,%s,{range:vmonths.profit},"<0")' % (VEHC, W3), 9),
    CA('status', 'Status', 'text', 'IF({col:actual_util}>={col:breakeven_util},%s,%s)' % (tok('be', 'Above break-even'), tok('be', 'Below break-even')), 16)],
    D.breakeven_d(), 60, [A('status', '= ' + tok('be', 'Below break-even'), 'bad'), A('status', '= ' + tok('be', 'Above break-even'), 'good')]))
# 8 idle runs ---------------------------------------------------------------------
tables.append(T('idle_runs', 'Idle runs', 'Runs of idle days with the lost revenue and a fill offer',
    'One row per run of 3 or more days a vehicle was available but not rented; idle days, the revenue lost at the class rate, the offer price and the revenue if filled at that price fill in.', [
    C('run_id', 'Run ID', 'text', 9, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24), LST('class', 'Class', 'class', 12), C('from_date', 'From', 'date', 11), C('to_date', 'To', 'date', 11),
    CA('idle_days', 'Idle days', 'int', '{col:to_date}-{col:from_date}+1', 9),
    CA('rate_card', 'Class day rate', 'money', LKN('classes.daily_rate', 'classes.class', 'class'), 11),
    CA('lost_revenue', 'Lost revenue', 'money', '{col:idle_days}*{col:rate_card}', 12),
    CA('price', 'Offer price a day', 'money', 'ROUND({col:rate_card}*(1-{set:offer_discount}),0)', 11),
    CA('offer_gain', 'Revenue if filled at the offer', 'money', '{col:idle_days}*{col:price}', 13),
    CA('open_days', 'Idle days still open', 'int', 'IF({col:to_date}>={today},{col:to_date}-MAX({col:from_date},{today})+1,0)', 10),
    CA('open_lost', 'Lost revenue still open', 'money', '{col:open_days}*{col:rate_card}', 12),
    CA('date', 'Offer from', 'date', 'IF({col:to_date}>={today},MAX({col:from_date},{today}),{col:from_date})', 11),
    CA('act_key', 'Act-first key', 'num', 'IF({col:open_days}>0,{col:open_lost}+(1000-VALUE(RIGHT({col:run_id},3)))/100000,0)', 11),
    CA('next14_days', 'Idle days, next 14 days', 'int', 'MAX(0,MIN({col:to_date},{today}+13)-MAX({col:from_date},{today})+1)', 10),
    CA('last30_days', 'Idle days, last 30 days', 'int', 'MAX(0,MIN({col:to_date},{today}-1)-MAX({col:from_date},{today}-30)+1)', 10),
    CA('last30_lost', 'Lost revenue, last 30 days', 'money', '{col:last30_days}*{col:rate_card}', 12),
    PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), PH('mechanic_phone', 'Mechanic phone', D.MECHANIC_PHONE), PH('market_phone', 'Marketplace support phone', D.MARKET_PHONE), BUS()],
    D.idle_runs_d(), 200, [A('idle_days', '>= {set:long_idle_days}', 'warn'), A('open_days', '> 0', 'good')]))
# 9 bookings ---------------------------------------------------------------------
tables.append(T('bookings', 'Bookings', 'Recent bookings with channel, plan, rate and total',
    'One row per booking: dates, channel, plan, rate and total as booked; rented days, the class offer price and the long-hire price fill in by themselves.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), C('vehicle_id', 'Vehicle ID', 'text', 10), C('renter', 'Renter', 'text', 22), C('phone', 'Phone', 'text', 18), LST('class', 'Class', 'class', 12),
    C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), C('days', 'Days', 'int', 7), LST('start_day', 'Start weekday', 'wday', 11), LST('channel', 'Channel', 'channel', 16),
    LST('plan', 'Plan', 'plan', 9), LST('season', 'Season', 'season', 10), C('day_rate', 'Day rate', 'money', 11), C('total', 'Total', 'money', 11), C('delivery_fee', 'Delivery fee', 'money', 11),
    C('net_amount', 'Net amount', 'money', 11), LST('status', 'Status', 'bstatus', 11),
    CA('rented_days', 'Rented days', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),0,{col:days})' % (tok('bstatus', 'Cancelled'), tok('bstatus', 'No-show')), 9),
    CA('price', 'Offer price a day', 'money', 'ROUND(SUMIFS({range:classes.daily_rate},{range:classes.class},{col:class})*(1-{set:offer_discount}),0)', 11),
    CA('saving', 'Saving on a week', 'money', 'ROUND(7*SUMIFS({range:classes.daily_rate},{range:classes.class},{col:class})-SUMIFS({range:rates.rate},{range:rates.class},{col:class},{range:rates.plan},%s),0)' % tok('plan', 'Weekly'), 11),
    CA('long_price', 'Long-hire price a day', 'money', 'ROUND(SUMIFS({range:rates.rate},{range:rates.class},{col:class},{range:rates.plan},%s)/30,0)' % tok('plan', 'Monthly'), 11),
    CA('usage_days', 'Rented days, last 90 days', 'int', 'SUMIFS({range:bookings.rented_days},{range:bookings.renter},{col:renter},{range:bookings.start_date},">="&({today}-90),{range:bookings.start_date},"<="&{today})', 11), BUS()],
    D.bookings_d(), 800, [A('status', '= ' + tok('bstatus', 'Cancelled'), 'warn')]))
# 10 rate card -------------------------------------------------------------------
tables.append(T('rates', 'Rate card', 'Price of a day, a week and a month for every class',
    'One row per class and plan: this year rate, last year rate and the days it covers; the price of one day and the rise this year fill in.', [
    C('rate_id', 'Rate ID', 'text', 9, required=True), LST('class', 'Class', 'class', 12), LST('plan', 'Plan', 'plan', 9), C('rate', 'Rate', 'money', 11), C('last_year_rate', 'Last year rate', 'money', 12),
    C('days', 'Days', 'int', 7), C('deposit', 'Deposit', 'money', 10), CA('day_equivalent', 'Price of one day', 'money', 'ROUND({col:rate}/{col:days},2)', 11),
    CA('rise_pct', 'Rise this year', 'pct', 'IF({col:last_year_rate}>0,{col:rate}/{col:last_year_rate}-1,0)', 9)], D.rates_d(), 50))
# 11 ADR by class and month --------------------------------------------------------
tables.append(T('adr_class', 'ADR by class and month', 'Average daily rate against the rate card',
    'One row per class and month: rented days, rental revenue and the revenue at the rate card and season; the achieved rate, the card rate and the discount share fill in.', [
    LST('class', 'Class', 'class', 12, required=True), C('month', 'Month', 'date', 11), LST('season', 'Season', 'season', 10), C('rented_days', 'Rented days', 'int', 10), C('rental_revenue', 'Rental revenue', 'money', 13),
    C('list_revenue', 'Revenue at card rate', 'money', 13), CA('achieved_rate', 'Achieved rate', 'money', 'IF({col:rented_days}>0,{col:rental_revenue}/{col:rented_days},0)', 11),
    CA('card_rate', 'Card rate', 'money', 'IF({col:rented_days}>0,{col:list_revenue}/{col:rented_days},0)', 11),
    CA('discount_share', 'Discount share', 'pct', 'IF({col:list_revenue}>0,MAX(0,1-{col:rental_revenue}/{col:list_revenue}),0)', 10)], D.adr_class_d(), 200, [A('discount_share', '> 0.1', 'warn')]))
# 12 ADR against last year -----------------------------------------------------------
RN = lambda m: 'IFERROR(SUMIFS({range:adr_class.rental_revenue},{range:adr_class.class},{col:class},{range:adr_class.month},%s)/SUMIFS({range:adr_class.rented_days},{range:adr_class.class},{col:class},{range:adr_class.month},%s),"")' % (m, m)
tables.append(T('adr_ly', 'ADR against last year', 'Achieved rate against the same month last year',
    'One row per class and month: this year and last year achieved rate, the change and a flag; the gap below last year and the manager and owner phones for messages fill in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('class', 'Class', 'class', 12), C('month', 'Month', 'date', 11), CA('rate_now', 'Rate this year', 'money', RN('{col:month}'), 11), CA('rate_ly', 'Rate last year', 'money', RN('EDATE({col:month},-12)'), 11),
    CA('change', 'Change', 'money', 'IF(AND(ISNUMBER({col:rate_now}),ISNUMBER({col:rate_ly})),{col:rate_now}-{col:rate_ly},0)', 10),
    CA('change_pct', 'Change, %', 'pct', 'IF(AND(ISNUMBER({col:rate_ly}),{col:change}<>0),{col:change}/{col:rate_ly},0)', 9),
    CA('flag', 'Flag', 'text', 'IF({col:change_pct}<-0.01,%s,IF({col:change_pct}>0.01,%s,%s))' % (tok('flag', 'Below last year'), tok('flag', 'Above last year'), tok('flag', 'In line')), 14),
    CA('gap', 'Gap below last year', 'money', 'MAX(0,-{col:change})', 11),
    CA('profit_vehicle', 'Profit per vehicle', 'money', 'IFERROR(SUMIFS({range:vmonths.profit},{range:vmonths.class},{col:class},{range:vmonths.month},{col:month})/COUNTIFS({range:vmonths.class},{col:class},{range:vmonths.month},{col:month}),0)', 12),
    PH('owner_phone', 'Owner phone', D.OWNER_PHONE), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), BUS()],
    D.adr_ly_d(), 100, [A('flag', '= ' + tok('flag', 'Below last year'), 'bad')]))
# 13 demand forecast -----------------------------------------------------------------
tables.append(T('forecast', 'Demand forecast 12 weeks', 'Booked days, fleet days and forecast for the next 12 weeks',
    'One row per week and class: booked days, fleet days, last year same week and weekend days; the forecast from last year times your trend factor, the shortage or surplus and the weekend load fill in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), LST('class', 'Class', 'class', 12), C('booked_days', 'Booked days', 'int', 10), C('fleet_days', 'Fleet days', 'int', 10), C('last_year_days', 'Last year same week', 'int', 11),
    C('weekend_booked', 'Weekend booked days', 'int', 11),
    CA('week_no', 'Week from now', 'int', 'ROUND(({col:week}-({today}-WEEKDAY({today},2)+1))/7,0)+1', 9),
    CA('forecast_days', 'Forecast days', 'int', 'ROUND(MAX({col:booked_days},{col:last_year_days}*{set:trend_factor}),0)', 10),
    CA('shortage_days', 'Shortage days', 'int', 'MAX(0,{col:forecast_days}-{col:fleet_days})', 10), CA('surplus_days', 'Surplus days', 'int', 'MAX(0,{col:fleet_days}-{col:forecast_days})', 10),
    CA('forecast_best', 'Forecast days, Best', 'int', 'ROUND(MAX({col:booked_days},{col:last_year_days}*{set:trend_factor}*(1+{set:scenario_swing})),0)', 10),
    CA('forecast_worst', 'Forecast days, Worst', 'int', 'ROUND(MAX({col:booked_days},{col:last_year_days}*{set:trend_factor}*(1-{set:scenario_swing})),0)', 10),
    CA('short_best', 'Shortage days, Best', 'int', 'MAX(0,{col:forecast_best}-{col:fleet_days})', 10), CA('short_worst', 'Shortage days, Worst', 'int', 'MAX(0,{col:forecast_worst}-{col:fleet_days})', 10),
    CA('surplus_best', 'Surplus days, Best', 'int', 'MAX(0,{col:fleet_days}-{col:forecast_best})', 10), CA('surplus_worst', 'Surplus days, Worst', 'int', 'MAX(0,{col:fleet_days}-{col:forecast_worst})', 10),
    CA('load', 'Load', 'pct', 'IF({col:fleet_days}>0,{col:forecast_days}/{col:fleet_days},0)', 8),
    CA('weekend_fleet', 'Weekend fleet days', 'int', 'ROUND({col:fleet_days}*2/7,0)', 10), CA('weekend_load', 'Weekend load', 'pct', 'IF({col:weekend_fleet}>0,{col:weekend_booked}/{col:weekend_fleet},0)', 9),
    CA('date', 'Saturday', 'date', '{col:week}+5', 11), CA('free_cars', 'Free cars on the weekend', 'int', 'MAX(0,ROUND({col:fleet_days}/7-{col:weekend_booked}/2,0))', 11),
    PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), PH('owner_phone', 'Owner phone', D.OWNER_PHONE), PH('hotel_phone', 'Hotel partner phone', D.HOTEL_PHONE), PH('market_phone', 'Marketplace support phone', D.MARKET_PHONE), BUS()],
    D.forecast_d(), 100, [A('shortage_days', '> 0', 'bad'), A('weekend_load', '>= {set:weekend_pressure}', 'warn')]))
# 14 cost per day -----------------------------------------------------------------------
CD = lambda col: 'IFERROR(%s/%s,0)' % (SV(col, VEHC, W12), SV('available_days', VEHC, W12))
tables.append(T('costday', 'Cost per day by vehicle', 'Cost of each vehicle for every available day, by cost line',
    'One row per vehicle: financing, insurance, maintenance, depreciation and other costs for each available day over 12 months; the total per day fills in.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), LST('class', 'Class', 'class', 12),
    CA('financing_day', 'Financing', 'money', CD('financing'), 10), CA('insurance_day', 'Insurance', 'money', CD('insurance'), 10), CA('maintenance_day', 'Maintenance', 'money', CD('maintenance'), 11),
    CA('depreciation_day', 'Depreciation', 'money', CD('depreciation'), 11),
    CA('other_day', 'Cleaning, fuel and fees', 'money', 'IFERROR((%s+%s+%s)/%s,0)' % (SV('cleaning', VEHC, W12), SV('fuel_charge', VEHC, W12), SV('channel_fees', VEHC, W12), SV('available_days', VEHC, W12)), 12),
    CA('total_day', 'Total per day', 'money', '{col:financing_day}+{col:insurance_day}+{col:maintenance_day}+{col:depreciation_day}+{col:other_day}', 11)], D.costday_d(), 60))
# 15 seasons -----------------------------------------------------------------------------
tables.append(T('seasons', 'Seasons', 'Season and multiplier of each calendar month',
    'One row per calendar month with its season and the multiplier applied to the class day rate; example values, set your own.', [
    C('months', 'Month', 'text', 14, required=True), LST('season', 'Season', 'season', 12), C('multiplier', 'Multiplier', 'num', 11)], D.seasons_d(), 50))
# 16 month trend ----------------------------------------------------------------------------
def VMM(col): return SV(col, '%s,{col:month}' % VM('month'))
def RISE(col): return 'IFERROR((%s/%s)/(%s/%s)-1,"")' % (VMM(col), VMM('available_days'), SV(col, '%s,EDATE({col:month},-12)' % VM('month')), SV('available_days', '%s,EDATE({col:month},-12)' % VM('month')))
LINES = [('fin_rise', 'Financing rise', 'financing', 'Financing'), ('ins_rise', 'Insurance rise', 'insurance', 'Insurance'), ('maint_rise', 'Maintenance rise', 'maintenance', 'Maintenance'),
         ('clean_rise', 'Cleaning rise', 'cleaning', 'Cleaning'), ('fuel_rise', 'Fuel or charge rise', 'fuel_charge', 'Fuel or charge'), ('dep_rise', 'Depreciation rise', 'depreciation', 'Depreciation'),
         ('fee_rise', 'Channel fees rise', 'channel_fees', 'Channel fees')]
TOP = 'IF(COUNT(%s)=0,"",%s"")' % (','.join('{col:%s}' % k for k, _, _, _ in LINES), ''.join('IF({col:%s}=MAX(%s),"%s",' % (k, ','.join('{col:%s}' % x for x, _, _, _ in LINES), nm) for k, _, _, nm in LINES) + '"")' * 0)
TOP = 'IF(COUNT(%s)=0,"",' % ','.join('{col:%s}' % k for k, _, _, _ in LINES) + ''.join('IF({col:%s}=MAX(%s),"%s",' % (k, ','.join('{col:%s}' % x for x, _, _, _ in LINES), nm) for k, _, _, nm in LINES) + '"")' + ')' * (len(LINES))
tables.append(T('trend', 'Month trend', 'Utilisation, ADR, revenue per day and profit by month',
    'One row per month: utilisation, ADR, revenue per available car-day (RevPAC), contribution and cost rises fill in from the other sheets, with the phones for the monthly messages.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('available_days', 'Available days', 'int', VMM('available_days'), 10), CA('rented_days', 'Rented days', 'int', VMM('rented_days'), 10),
    CA('utilisation', 'Utilisation', 'pct', 'IF({col:available_days}>0,{col:rented_days}/{col:available_days},0)', 10),
    CA('adr', 'ADR', 'money', 'IFERROR(SUMIFS({range:adr_class.rental_revenue},{range:adr_class.month},{col:month})/SUMIFS({range:adr_class.rented_days},{range:adr_class.month},{col:month}),0)', 9),
    CA('discount_share', 'Discount share', 'pct', 'IFERROR(MAX(0,1-SUMIFS({range:adr_class.rental_revenue},{range:adr_class.month},{col:month})/SUMIFS({range:adr_class.list_revenue},{range:adr_class.month},{col:month})),0)', 10),
    CA('revenue', 'Revenue', 'money', VMM('revenue'), 12), CA('revpac', 'Revenue per available day', 'money', 'IF({col:available_days}>0,{col:revenue}/{col:available_days},0)', 12),
    CA('profit', 'Contribution', 'money', VMM('profit'), 12), CA('profit_day', 'Contribution per available day', 'money', 'IF({col:available_days}>0,{col:profit}/{col:available_days},0)', 12),
    CA('margin', 'Contribution margin', 'pct', 'IF({col:revenue}>0,{col:profit}/{col:revenue},0)', 10),
    CA('vehicles', 'Vehicles', 'int', 'COUNTIFS({range:vmonths.month},{col:month})', 9),
    CA('red_vehicles', 'Vehicles red', 'int', 'COUNTIFS({range:vmonths.month},{col:month},{range:vmonths.utilisation},"<"&{set:util_red})', 9),
    CA('profit_vehicle', 'Profit per vehicle', 'money', 'IF({col:vehicles}>0,{col:profit}/{col:vehicles},0)', 11),
    CA('lost_revenue', 'Idle run revenue lost', 'money', 'SUMIFS({range:idle_runs.lost_revenue},{range:idle_runs.from_date},">="&{col:month},{range:idle_runs.from_date},"<"&EDATE({col:month},1))', 12),
    ] + [CA(k, lab, 'pct', RISE(col), 10) for k, lab, col, nm in LINES] + [
    CA('top_line', 'Fastest rising cost line', 'text', TOP, 16),
    CA('year', 'Year', 'int', 'YEAR({col:month})', 7), CA('quarter', 'Quarter', 'text', '"Q"&ROUNDUP(MONTH({col:month})/3,0)&" "&YEAR({col:month})', 9), CA('dep_pct', 'Depreciation setting', 'pct', '{set:dep_pct}', 10),
    CA('util_red', 'Red below', 'pct', '{set:util_red}', 9), CA('util_target', 'Utilisation target', 'pct', '{set:util_target}', 10), CA('review_date', 'Rate card review on', 'date', 'EOMONTH({col:month},0)+5', 11),
    PH('owner_phone', 'Owner phone', D.OWNER_PHONE), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), PH('accountant_phone', 'Accountant phone', D.ACCOUNTANT_PHONE), PH('broker_phone', 'Insurance broker phone', D.BROKER_PHONE),
    PH('bookkeeper_phone', 'Bookkeeper phone', D.BOOKKEEPER_PHONE), PH('lender_phone', 'Lender phone', D.LENDER_PHONE), BUS()], D.trend_d(), 50))
# 17 channel profit -------------------------------------------------------------------------
tables.append(T('chprofit', 'Channel profit', 'Net rate per rented day and share of days by channel',
    'Six channels with the net rate per rented day after the channel fee, without the delivery fee, and the share of rented days, from the recent bookings.', [
    LST('channel', 'Channel', 'channel', 18, required=True),
    CA('net_per_day', 'Net per rented day', 'money', 'IFERROR((SUMIFS({range:bookings.net_amount},{range:bookings.channel},{col:channel},%s)-SUMIFS({range:bookings.delivery_fee},{range:bookings.channel},{col:channel},%s))/SUMIFS({range:bookings.rented_days},{range:bookings.channel},{col:channel}),0)' % (OKS, OKS), 14),
    CA('share_days', 'Share of rented days', 'pct', 'IFERROR(SUMIFS({range:bookings.rented_days},{range:bookings.channel},{col:channel})/SUM({range:bookings.rented_days}),0)', 14)], D.chprofit_d(), 50))
# 18 utilisation bands ---------------------------------------------------------------------------
tables.append(T('bands', 'Utilisation bands', 'Vehicles of each class in each red, amber and green band',
    'One row per class and band from your utilisation settings; the number of vehicles and the share of the class fill in.', [
    LST('class', 'Class', 'class', 12, required=True), LST('band', 'Band', 'band', 10), CA('vehicles', 'Vehicles', 'int', 'COUNTIFS({range:util_vehicle.class},{col:class},{range:util_vehicle.band},{col:band})', 10),
    CA('share', 'Share of the class', 'pct', 'IFERROR({col:vehicles}/COUNTIFS({range:util_vehicle.class},{col:class}),0)', 12)], D.bands_d(), 50))
# 19 vehicle verdict list ---------------------------------------------------------------------------
LB = lambda c: LKN('breakeven.%s' % c, 'breakeven.vehicle', 'vehicle')
tables.append(T('verdict', 'Vehicle verdict list', 'Keep, reprice or sell for every vehicle',
    'One row per vehicle: 12 month profit, utilisation and break-even utilisation with a verdict; a loss with utilisation far under break-even is Sell, a smaller loss is Reprice.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), CA('class', 'Class', 'text', LKT('vehicles.class', 'vehicles.vehicle', 'vehicle'), 12),
    CA('profit_12m', 'Profit, 12 months', 'money', LKN('vprofit.profit_12m', 'vprofit.vehicle', 'vehicle'), 13), CA('utilisation', 'Utilisation', 'pct', LB('actual_util'), 10),
    CA('breakeven', 'Break-even utilisation', 'pct', LB('breakeven_util'), 11), CA('months', 'Loss months of 12', 'int', LB('months_below'), 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:profit_12m}>=0,%s,IF(AND({col:utilisation}<{set:sell_ratio}*{col:breakeven},{col:months}>={set:loss_months_warn}),%s,%s))' % (tok('verdict', 'Keep'), tok('verdict', 'Sell'), tok('verdict', 'Reprice')), 10),
    CA('loss', 'Loss, 12 months', 'money', 'MAX(0,-{col:profit_12m})', 12), CA('vehicles', 'Vehicles in the fleet', 'int', 'COUNTIFS({range:vehicles.status},%s)+COUNTIFS({range:vehicles.status},%s)' % (tok('vstatus', 'Active'), tok('vstatus', 'In workshop')), 9),
    PH('owner_phone', 'Owner phone', D.OWNER_PHONE), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), PH('accountant_phone', 'Accountant phone', D.ACCOUNTANT_PHONE), PH('broker_phone', 'Insurance broker phone', D.BROKER_PHONE), BUS()],
    D.verdict_d(), 60, [A('verdict', '= ' + tok('verdict', 'Sell'), 'bad'), A('verdict', '= ' + tok('verdict', 'Reprice'), 'warn'), A('verdict', '= ' + tok('verdict', 'Keep'), 'good')]))
# 20 revenue per available day by class ---------------------------------------------------------------
tables.append(T('revpac_class', 'RevPAC by class', 'Revenue per available car-day against your target',
    'Revenue per available car-day (RevPAC) is revenue divided by available days; the last 3 months by class fill in, your target is typed in.', [
    LST('class', 'Class', 'class', 14, required=True), CA('revpac', 'Revenue per available day', 'money', 'IFERROR(%s/%s,0)' % (SV('revenue', CLSC, W3), SV('available_days', CLSC, W3)), 13),
    C('target', 'Target', 'money', 11)], D.revpac_d(), 50))
assert len(tables) == 20, len(tables)
