"""Car Rental Business suite - part 7: Utilisation, Profit and Pricing Review."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr7_lists import *
from cr7_tables import settings, tables, SV, VM, W3, W12, LY3, MS, OKS
from cr7_tools import tools, U, R, PR15, CLC
TOOL_FIX = {
'util_tool': ('Vehicle and Class Utilisation', 'Which vehicles are red and is a class below its usual', 'Pick a class: its utilisation over the last 3 months against its own 12 months and last year, with the red, amber and green vehicle counts from your settings.'),
'profit_day_tool': (None, None, 'Type a vehicle: revenue per available day less every cost line gives its profit per day, ranked, with a Keep, Reprice or Sell verdict. Profit is before office pay and overhead.'),
'breakeven_tool': ('Vehicle Break-even Tool', 'Is this vehicle above its break-even utilisation', None),
'loss_tool': (None, 'Which vehicles lose money and what would recover it', 'Pick a rank (1 is the biggest loss): the vehicle, its loss a month and the extra rented days a month that would recover it, with the counts of vehicles losing in 3 of 3 and 12 of 12 months.'),
'idle_tool': (None, None, 'Idle days are days a car is available but not rented. Open runs of 3 or more days are ranked by lost revenue, with the offer price and the revenue if filled.'),
'floor_tool': (None, 'How low can a price go for an idle gap', None),
'forecast_tool': ('Forecast and Weekend Pressure', 'Where are the next 12 weeks short of cars or free', None),
'mix_tool': (None, None, 'Pick a class: profit per vehicle over 12 months and its share of fleet days, ranked against the six classes, with an add or trim verdict from your limits.'),
'fleet_tool': (None, 'Is the fleet of this class the right size', None),
'target_tool': (None, 'What utilisation gives the profit I want per vehicle', None),
'weekday_tool': (None, 'Is the weekend uplift high enough', None),
'costtrend_tool': (None, 'Which cost line per day is rising fastest', None),
'review_tool': (None, None, 'This month so far against the average of the last 3 full months and the same month last year, with a green, amber or red light for utilisation, rate, revenue and contribution per available day.'),
}
for t_ in tools:
    sh, ti, hi = TOOL_FIX.get(t_['key'], (None, None, None))
    if sh: t_['sheet'] = sh
    if ti: t_['title'] = ti
    if hi: t_['hint'] = hi
    for o_ in t_['outputs']: o_['formula'] = fixlit(o_['formula'])
    for g_ in (t_.get('grid') or {}).get('rows', []):
        g_['values'] = {k: (fixlit(v) if isinstance(v, str) else v) for k, v in g_['values'].items()}
for tb_ in tables:
    for c_ in tb_['columns']:
        if c_.get('formula'): c_['formula'] = fixlit(c_['formula'])

import cr7_data as D

NOTE = "Sample wording: adapt it to your own business and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def FFL(label, t, idc, c, fmt): return FF(label, LK(t, idc, c), fmt)
RED, AMB, GRN = tok('band', 'Red'), tok('band', 'Amber'), tok('band', 'Green')

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('util_sheet', 'Utilisation Review Sheet', 'Utilisation review of one vehicle', 'util_vehicle.vehicle', F(
        ('Class', 'util_vehicle.class'), ('Utilisation, last 3 months', 'util_vehicle.util_3m'), ('Utilisation, last 12 months', 'util_vehicle.util_12m'), ('Same 3 months last year', 'util_vehicle.util_ly3m'),
        ('Against its own 12 months, points', 'util_vehicle.vs_usual'), ('Band', 'util_vehicle.band')) + [
        FF('Red below', '{set:util_red}', 'pct'), FF('Green from', '{set:util_green}', 'pct'), FF('Your utilisation target', '{set:util_target}', 'pct'),
        FF('Points to reach the target', 'MAX(0,{set:util_target}-%s)' % LK('util_vehicle', 'vehicle', 'util_3m'), 'pct'),
        FF('Extra rented days a month to reach it', 'ROUND(MAX(0,{set:util_target}-%s)*30,0)' % LK('util_vehicle', 'vehicle', 'util_3m'), 'int')]),
    FORM('profit_sheet', 'Vehicle Profit Sheet', 'Profit of one vehicle over 12 months', 'vprofit.vehicle', F(
        ('Class', 'vprofit.class'), ('Status', 'vprofit.status'), ('Revenue, 12 months', 'vprofit.revenue_12m'), ('Costs, 12 months', 'vprofit.cost_12m'), ('Profit, 12 months', 'vprofit.profit_12m'),
        ('Available days', 'vprofit.avail_12m'), ('Profit per available day', 'vprofit.profit_per_day'), ('Rank among vehicles', 'vprofit.rank')) + [
        FF('Profit a month', 'ROUND(%s/12,0)' % LK('vprofit', 'vehicle', 'profit_12m'), 'money'), FF('Costs as a share of revenue', 'IFERROR(%s/%s,0)' % (LK('vprofit', 'vehicle', 'cost_12m'), LK('vprofit', 'vehicle', 'revenue_12m')), 'pct'),
        FF('Profit you want a month', '{set:target_profit_month}', 'money'), FF('Gap to that profit a month', '%s/12-{set:target_profit_month}' % LK('vprofit', 'vehicle', 'profit_12m'), 'money')]),
    FORM('breakeven_sheet', 'Break-even Sheet', 'Break-even utilisation of one vehicle', 'breakeven.vehicle', F(
        ('Class', 'breakeven.class'), ('Fixed cost per available day', 'breakeven.fixed_per_day'), ('Rate per rented day', 'breakeven.day_rate'), ('Variable cost per rented day', 'breakeven.var_per_day'),
        ('Break-even utilisation', 'breakeven.breakeven_util'), ('Actual utilisation', 'breakeven.actual_util'), ('Loss months of 12', 'breakeven.months_below'), ('Status', 'breakeven.status')) + [
        FF('Rented days needed a year', 'ROUND(%s*%s,0)' % (LK('breakeven', 'vehicle', 'avail_12m'), LK('breakeven', 'vehicle', 'breakeven_util')), 'int'),
        FF('Rented days in the last 12 months', LK('breakeven', 'vehicle', 'rented_12m'), 'int'),
        FF('Rate that breaks even at the utilisation', 'IF(%s>0,%s/%s+%s,0)' % (LK('breakeven', 'vehicle', 'actual_util'), LK('breakeven', 'vehicle', 'fixed_per_day'), LK('breakeven', 'vehicle', 'actual_util'), LK('breakeven', 'vehicle', 'var_per_day')), 'money')]),
    FORM('idle_sheet', 'Idle Gap Offer Sheet', 'Offer for one idle run', 'idle_runs.run_id', F(
        ('Vehicle', 'idle_runs.vehicle'), ('Class', 'idle_runs.class'), ('From', 'idle_runs.from_date'), ('To', 'idle_runs.to_date'), ('Idle days', 'idle_runs.idle_days'), ('Class day rate', 'idle_runs.rate_card'),
        ('Lost revenue', 'idle_runs.lost_revenue'), ('Offer price a day', 'idle_runs.price'), ('Revenue if filled at the offer', 'idle_runs.offer_gain')) + [
        FF('Discount offered', '{set:offer_discount}', 'pct'), FF('Revenue given up by the discount', '%s-%s' % (LK('idle_runs', 'run_id', 'lost_revenue'), LK('idle_runs', 'run_id', 'offer_gain')), 'money'),
        FF('Share of the lost revenue recovered', 'IFERROR(%s/%s,0)' % (LK('idle_runs', 'run_id', 'offer_gain'), LK('idle_runs', 'run_id', 'lost_revenue')), 'pct')]),
    FORM('rate_sheet', 'Rate Review Sheet', 'Achieved rate of one class and month', 'adr_ly.row_id', F(
        ('Class', 'adr_ly.class'), ('Month', 'adr_ly.month'), ('Rate this year', 'adr_ly.rate_now'), ('Rate last year', 'adr_ly.rate_ly'), ('Change', 'adr_ly.change'), ('Change, %', 'adr_ly.change_pct'), ('Flag', 'adr_ly.flag'),
        ('Gap below last year', 'adr_ly.gap'), ('Profit per vehicle', 'adr_ly.profit_vehicle')) + [
        FF('Class day price on the rate card', 'SUMIFS({range:classes.daily_rate},{range:classes.class},%s)' % LK('adr_ly', 'row_id', 'class'), 'money'),
        FF('Achieved rate against the card price', 'IFERROR(%s/SUMIFS({range:classes.daily_rate},{range:classes.class},%s)-1,0)' % (LK('adr_ly', 'row_id', 'rate_now'), LK('adr_ly', 'row_id', 'class')), 'pct')]),
    FORM('discount_sheet', 'Discount Offer Sheet', 'Offer price for one booking', 'bookings.booking_id', F(
        ('Renter', 'bookings.renter'), ('Class', 'bookings.class'), ('Start date', 'bookings.start_date'), ('Days', 'bookings.days'), ('Channel', 'bookings.channel'), ('Plan', 'bookings.plan'),
        ('Day rate booked', 'bookings.day_rate'), ('Offer price a day', 'bookings.price'), ('Saving on a week', 'bookings.saving'), ('Long-hire price a day', 'bookings.long_price')) + [
        FF('Discount offered', '{set:offer_discount}', 'pct'), FF('Offer for these days', '%s*%s' % (LK('bookings', 'booking_id', 'price'), LK('bookings', 'booking_id', 'days')), 'money'),
        FF('Booked total', LK('bookings', 'booking_id', 'total'), 'money')]),
    FORM('class_sheet', 'Class Review Sheet', 'Review of one class', 'revpac_class.class', F(
        ('Revenue per available day', 'revpac_class.revpac'), ('Target', 'revpac_class.target')) + [
        FF('Gap to the target', '%s-%s' % (LK('revpac_class', 'class', 'revpac'), LK('revpac_class', 'class', 'target')), 'money'),
        FF('Utilisation, last 3 months', 'IFERROR(%s/%s,0)' % (SV('rented_days', VM('class') + ',{pick}', W3), SV('available_days', VM('class') + ',{pick}', W3)), 'pct'),
        FF('Utilisation, last 12 months', 'IFERROR(%s/%s,0)' % (SV('rented_days', VM('class') + ',{pick}', W12), SV('available_days', VM('class') + ',{pick}', W12)), 'pct'),
        FF('Profit, last 12 months', SV('profit', VM('class') + ',{pick}', W12), 'money'),
        FF('Class day price on the rate card', 'SUMIFS({range:classes.daily_rate},{range:classes.class},{pick})', 'money'),
        FF('Deposit', 'SUMIFS({range:classes.deposit},{range:classes.class},{pick})', 'money')]),
    FORM('forecast_sheet', 'Forecast Sheet', 'Forecast of one class and week', 'forecast.row_id', F(
        ('Week (Monday)', 'forecast.week'), ('Class', 'forecast.class'), ('Booked days', 'forecast.booked_days'), ('Fleet days', 'forecast.fleet_days'), ('Last year same week', 'forecast.last_year_days'),
        ('Forecast days', 'forecast.forecast_days'), ('Shortage days', 'forecast.shortage_days'), ('Surplus days', 'forecast.surplus_days'), ('Load', 'forecast.load'), ('Weekend load', 'forecast.weekend_load')) + [
        FF('Trend factor you use', '{set:trend_factor}', 'num'), FF('Forecast days, Best', LK('forecast', 'row_id', 'forecast_best'), 'int'), FF('Forecast days, Worst', LK('forecast', 'row_id', 'forecast_worst'), 'int'),
        FF('Free cars on the weekend', LK('forecast', 'row_id', 'free_cars'), 'int')]),
    FORM('month_sheet', 'Monthly Review Sheet', 'Review of one month', 'trend.month', F(
        ('Utilisation', 'trend.utilisation'), ('ADR, revenue per rented day', 'trend.adr'), ('Revenue per available day', 'trend.revpac'), ('Revenue', 'trend.revenue'), ('Contribution', 'trend.profit'),
        ('Contribution margin', 'trend.margin'), ('Vehicles red', 'trend.red_vehicles'), ('Profit per vehicle', 'trend.profit_vehicle')) + [
        FF('Utilisation target', '{set:util_target}', 'pct'), FF('Margin you want to hold', '{set:target_margin}', 'pct'),
        FF('Margin against the target, points', '%s-{set:target_margin}' % LK('trend', 'month', 'margin'), 'pct'), FF('Discount share', LK('trend', 'month', 'discount_share'), 'pct')]),
    FORM('verdict_sheet', 'Vehicle Keep or Sell Sheet', 'Keep, reprice or sell one vehicle', 'verdict.vehicle', F(
        ('Class', 'verdict.class'), ('Profit, 12 months', 'verdict.profit_12m'), ('Utilisation', 'verdict.utilisation'), ('Break-even utilisation', 'verdict.breakeven'), ('Loss months of 12', 'verdict.months'), ('Verdict', 'verdict.verdict')) + [
        FF('Sell below this share of break-even', '{set:sell_ratio}', 'pct'), FF('Utilisation as a share of break-even', 'IFERROR(%s/%s,0)' % (LK('verdict', 'vehicle', 'utilisation'), LK('verdict', 'vehicle', 'breakeven')), 'pct'),
        FF('Loss a month', 'ROUND(%s/12,0)' % LK('verdict', 'vehicle', 'loss'), 'money'),
        FF('Resale estimate', 'IFERROR(INDEX({range:vehicles.purchase_price},MATCH({pick},{range:vehicles.vehicle},0)),0)', 'money')]),
    FORM('price_sheet', 'Price Test Sheet', 'Price test for one rate', 'rates.rate_id', F(
        ('Class', 'rates.class'), ('Plan', 'rates.plan'), ('Rate', 'rates.rate'), ('Last year rate', 'rates.last_year_rate'), ('Days', 'rates.days'), ('Price of one day', 'rates.day_equivalent'), ('Rise this year', 'rates.rise_pct')) + [
        FF('Day price on a short Friday pickup', 'ROUND(%s*(1+{set:weekend_uplift}),2)' % LK('rates', 'rate_id', 'day_equivalent'), 'money'),
        FF('Day price in Peak', 'ROUND(%s*AVERAGEIFS({range:seasons.multiplier},{range:seasons.season},%s),2)' % (LK('rates', 'rate_id', 'day_equivalent'), tok('season', 'Peak')), 'money'),
        FF('Day price in Off-peak', 'ROUND(%s*AVERAGEIFS({range:seasons.multiplier},{range:seasons.season},%s),2)' % (LK('rates', 'rate_id', 'day_equivalent'), tok('season', 'Off-peak')), 'money'),
        FF('Day price with the idle gap discount', 'ROUND(%s*(1-{set:offer_discount}),2)' % LK('rates', 'rate_id', 'day_equivalent'), 'money')]),
    FORM('target_sheet', 'Target Setting Sheet', 'Targets for one class', 'classes.class', F(
        ('Day price on the rate card', 'classes.daily_rate'), ('Deposit', 'classes.deposit')) + [
        FF('Utilisation target', '{set:util_target}', 'pct'), FF('Revenue per available day at the target', 'ROUND(%s*{set:util_target},2)' % LK('classes', 'class', 'daily_rate'), 'money'),
        FF('Your revenue per available day target', 'SUMIFS({range:revpac_class.target},{range:revpac_class.class},{pick})', 'money'),
        FF('Revenue per available day now', 'SUMIFS({range:revpac_class.revpac},{range:revpac_class.class},{pick})', 'money'),
        FF('Profit you want from one vehicle a month', '{set:target_profit_month}', 'money'), FF('Contribution margin you want', '{set:target_margin}', 'pct'),
        FF('Utilisation red below', '{set:util_red}', 'pct'), FF('Utilisation green from', '{set:util_green}', 'pct')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('profit_doc', 'Vehicle Profit Report', 'Vehicle profit report, 12 months', 'vprofit.vehicle', [
        'Vehicle profit report of {set:company}, dated {today}. Vehicle: {col:vprofit.vehicle}. Class: {col:vprofit.class}. Status: {col:vprofit.status}.',
        'Revenue over 12 months: {col:vprofit.revenue_12m}. Costs over 12 months (financing, insurance, maintenance, cleaning, fuel or charge, depreciation and marketplace fees): {col:vprofit.cost_12m}. Profit: {col:vprofit.profit_12m}.',
        'Available days: {col:vprofit.avail_12m}. Profit per available day: {col:vprofit.profit_per_day}. Rank among your vehicles: {col:vprofit.rank}.',
        'Profit here is a contribution before office pay and overhead. Amounts are before any sales tax (confirm with your adviser).'], ['Owner', 'Manager'], NOTE),
    DOC('util_doc', 'Utilisation Report by Class', 'Utilisation report of a class and month', 'util_class.row_id', [
        'Utilisation report of {set:company}, dated {today}. Class: {col:util_class.class}. Month: {col:util_class.month}. Season: {col:util_class.season}.',
        'Available days: {col:util_class.available_days}. Rented days: {col:util_class.rented_days}. Utilisation (rented days as a share of available days): {col:util_class.utilisation}.',
        'Against the same month last year: {col:util_class.vs_last_year}. Red below {set:util_red}, green from {set:util_green}, target {set:util_target} (example values, set your own).',
        'Use this page in the monthly review to decide where to push the rate or the marketing.'], ['Manager', 'Owner'], NOTE),
    DOC('breakeven_doc', 'Break-even Note', 'Break-even note for a vehicle', 'breakeven.vehicle', [
        'Break-even note of {set:company}, dated {today}. Vehicle: {col:breakeven.vehicle}. Class: {col:breakeven.class}.',
        'Fixed cost per available day: {col:breakeven.fixed_per_day}. Rate per rented day: {col:breakeven.day_rate}. Variable cost per rented day: {col:breakeven.var_per_day}.',
        'Break-even utilisation (the utilisation at which a vehicle covers its cost): {col:breakeven.breakeven_util}. Actual utilisation over 12 months: {col:breakeven.actual_util}. Status: {col:breakeven.status}. Loss months of the last 12: {col:breakeven.months_below}.',
        'A vehicle that stays below break-even needs a higher rate, more rented days or a decision to sell.'], ['Owner', 'Manager'], NOTE),
    DOC('idle_doc', 'Idle Gap Offer Letter', 'Offer letter for an idle run', 'idle_runs.run_id', [
        'Offer of {set:company}, dated {today}. Dear renter, a {col:idle_runs.class} is free from {col:idle_runs.date} to {col:idle_runs.to_date}.',
        'The usual day price is {col:idle_runs.rate_card}. For this gap we offer {col:idle_runs.price} a day, a discount of {set:offer_discount}. A longer hire gives a lower price a day, please ask.',
        'The offer holds while the car is free and is before any sales tax. The deposit, fees and hire terms are the ones in your hire terms.',
        'Please reply to book. Thank you for choosing us.'], ['Manager', 'Renter'], NOTE),
    DOC('rate_doc', 'Rate Review Summary', 'Rate review of a class and month', 'adr_ly.row_id', [
        'Rate review of {set:company}, dated {today}. Class: {col:adr_ly.class}. Month: {col:adr_ly.month}.',
        'Average daily rate (revenue per rented day) this year: {col:adr_ly.rate_now}. Last year: {col:adr_ly.rate_ly}. Change: {col:adr_ly.change}. Flag: {col:adr_ly.flag}.',
        'Gap below last year: {col:adr_ly.gap}. Profit per vehicle of the class in the month: {col:adr_ly.profit_vehicle}.',
        'When the rate is below last year, review the discounts and the marketplace prices before the next month starts.'], ['Manager', 'Owner'], NOTE),
    DOC('month_doc', 'Monthly Performance Report', 'Monthly performance report', 'trend.month', [
        'Monthly performance report of {set:company}, dated {today}. Month: {col:trend.month}.',
        'Utilisation: {col:trend.utilisation}. Average daily rate: {col:trend.adr}. Revenue per available car-day: {col:trend.revpac}. Discount share: {col:trend.discount_share}.',
        'Revenue: {col:trend.revenue}. Contribution before office pay and overhead: {col:trend.profit}. Contribution margin: {col:trend.margin}. Vehicles red: {col:trend.red_vehicles} of {col:trend.vehicles}.',
        'Idle runs cost {col:trend.lost_revenue} in revenue this month. Amounts are before any sales tax (confirm with your adviser).'], ['Owner', 'Manager'], NOTE),
    DOC('outlook_doc', '12-Week Demand Outlook', 'Demand outlook for a class and week', 'forecast.row_id', [
        'Demand outlook of {set:company}, dated {today}. Class: {col:forecast.class}. Week starting {col:forecast.week}.',
        'Booked days: {col:forecast.booked_days}. Fleet days: {col:forecast.fleet_days}. Last year same week: {col:forecast.last_year_days}. Forecast days: {col:forecast.forecast_days} (last year times {set:trend_factor}).',
        'Shortage days: {col:forecast.shortage_days}. Surplus days: {col:forecast.surplus_days}. Weekend load: {col:forecast.weekend_load}. Free cars on the weekend: {col:forecast.free_cars}.',
        'A shortage calls for a higher rate or a closed marketplace listing; a surplus calls for an offer or a longer-hire price.'], ['Manager', 'Owner'], NOTE),
    DOC('mix_doc', 'Class Mix Report', 'Class mix report', 'revpac_class.class', [
        'Class mix report of {set:company}, dated {today}. Class: {col:revpac_class.class}.',
        'Revenue per available day over the last 3 months: {col:revpac_class.revpac}. Your target: {col:revpac_class.target}.',
        'Utilisation target: {set:util_target}. Profit wanted from one vehicle a month: {set:target_profit_month} (example values, set your own).',
        'Add to a class that earns well and fills often; trim a class that stays under its target.'], ['Owner', 'Manager'], NOTE),
    DOC('minutes_doc', 'Pricing Review Minutes', 'Minutes of a pricing review', 'trend.month', [
        'Pricing review of {set:company}, dated {today}. Month under review: {col:trend.month}. Present: owner, manager.',
        'Figures: utilisation {col:trend.utilisation}, average daily rate {col:trend.adr}, discount share {col:trend.discount_share}, revenue per available day {col:trend.revpac}, vehicles red {col:trend.red_vehicles}.',
        'Decisions: rates to change ______. Classes to promote ______. Vehicles to reprice or sell ______. Date of the next review ______.',
        'Weekend uplift now {set:weekend_uplift}; discount offered to fill an idle gap {set:offer_discount}.'], ['Owner', 'Manager'], NOTE),
    DOC('fleet_doc', 'Yearly Fleet Review', 'Yearly review of one vehicle', 'vehicles.vehicle_id', [
        'Yearly fleet review of {set:company}, dated {today}. Vehicle: {col:vehicles.vehicle}. Class: {col:vehicles.class}. Status: {col:vehicles.status}.',
        'Purchased on {col:vehicles.purchase_date} for {col:vehicles.purchase_price}. Age: {col:vehicles.age_months} months. Odometer: {col:vehicles.odometer} miles (the demo unit, set your own). Monthly payment: {col:vehicles.monthly_payment}.',
        'Depreciation setting: {set:dep_pct} of the purchase price a month (example, set your own).',
        'Decision for the coming year: keep, reprice or sell. Notes: ______.'], ['Owner', 'Manager'], NOTE),
    DOC('targets_doc', 'Targets Sheet', 'Utilisation, rate and profit targets of a class', 'classes.class', [
        'Targets of {set:company}, dated {today}. Class: {col:classes.class}. Day price on the rate card: {col:classes.daily_rate}. Deposit (an amount held on a card or kept until the car is back): {col:classes.deposit}.',
        'Utilisation: red below {set:util_red}, green from {set:util_green}, target {set:util_target}. Contribution margin to hold: {set:target_margin}.',
        'Profit wanted from one vehicle a month: {set:target_profit_month}. Weekend uplift: {set:weekend_uplift}. Offer to fill an idle gap: {set:offer_discount} off.',
        'These are example targets: set your own and review them every quarter.'], ['Owner', 'Manager'], NOTE),
    DOC('verdict_doc', 'Vehicle Verdict Note', 'Verdict of one vehicle', 'verdict.vehicle', [
        'Vehicle verdict of {set:company}, dated {today}. Vehicle: {col:verdict.vehicle}. Class: {col:verdict.class}.',
        'Profit over 12 months: {col:verdict.profit_12m}. Utilisation: {col:verdict.utilisation}. Break-even utilisation: {col:verdict.breakeven}. Loss months of 12: {col:verdict.months}.',
        'Verdict: {col:verdict.verdict}. A vehicle with a loss and a utilisation far below break-even is a sell; a smaller loss is a reprice.',
        'The verdict helps you keep track; the decision is yours.'], ['Owner', 'Manager'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('month_chk', 'Monthly Vehicle Review Steps', 'trend', 'trend.month', [('Check every vehicle in Vehicle months', 31), ('Open Utilisation by vehicle and note the red vehicles', 32), ('Open the Monthly Performance Review tool', 33), ('Write the three decisions of the month', 34), ('Send the owner message', 35)]),
    CHK('idle_chk', 'Weekly Idle-Day Check Steps', 'idle_runs', 'idle_runs.from_date', [('Open the Idle-Day Finder', 0), ('Check the largest open run', 0), ('Offer the car at the discount price', 1), ('Ask marketplace support to lower the price', 1), ('Note what filled', 7)]),
    CHK('rate_chk', 'Monthly Rate Review Steps', 'adr_ly', 'adr_ly.month', [('Open Rate Against History', 31), ('Check each class against last year', 32), ('Review the discounts on a class below last year', 33), ('Update the rate card', 35), ('Tell the manager and the marketplace support', 36)]),
    CHK('fleet_chk', 'Quarterly Fleet Review Steps', 'trend', 'trend.month', [('Open Vehicle verdict list', 31), ('List the Sell and Reprice vehicles', 32), ('Open Fleet Size Fit for each class', 33), ('Check the insurance broker and the lender figures', 40), ('Agree what to buy, keep or sell', 45)]),
    CHK('breakeven_chk', 'Break-even Check Steps', 'trend', 'trend.month', [('Open Break-even by vehicle', 31), ('Find vehicles below break-even', 31), ('Test a rate rise in the Break-even tool', 32), ('Decide to reprice or sell', 35)]),
    CHK('season_chk', 'Season Pricing Review Steps', 'forecast', 'forecast.week', [('Open Season Rate Effectiveness', -28), ('Compare peak and off-peak achieved rates', -27), ('Check the weekend uplift in Weekday and Weekend Yield', -21), ('Update the seasons table', -14), ('Update the marketplace prices', -7)]),
    CHK('outlook_chk', 'Demand Outlook Steps', 'forecast', 'forecast.week', [('Open the Demand Forecast', 0), ('Pick Base, Best and Worst', 0), ('Note weeks with a shortage', 1), ('Close a marketplace listing for a full week', 2), ('Plan an offer for a surplus week', 3)]),
    CHK('mix_chk', 'Class Mix Review Steps', 'util_class', 'util_class.month', [('Open Class Mix Review for each class', 31), ('Note profit per vehicle and share of days', 31), ('Open Fleet Size Fit', 32), ('Decide to add or trim a class', 35)]),
    CHK('loss_chk', 'Loss-making Vehicle Steps', 'trend', 'trend.month', [('Open the Loss-making Vehicle List', 31), ('Check each vehicle with a loss in 3 of 3 months', 31), ('Check the extra rented days needed', 32), ('Reprice, offer or sell', 35), ('Write the decision in the verdict list', 36)]),
    CHK('target_chk', 'Target Setting Steps', 'trend', 'trend.month', [('Review utilisation red and green levels', 31), ('Set the target profit for a vehicle a month', 31), ('Set the revenue per available day by class', 32), ('Share the targets with the manager', 33)]),
    CHK('year_chk', 'Year-End Review Steps', 'trend', 'trend.month', [('Open Profit per vehicle for 12 months', 31), ('Open the Yearly Fleet Review for each vehicle', 35), ('Send the profit per vehicle to the accountant', 38), ('Send the planned sales and fleet size to the insurance broker and the lender', 40)]),
    CHK('host_chk', 'One-Car Host Review Steps', 'bookings', 'bookings.start_date', [('Check how many days the car was rented this month', 30), ('Compare the rate with last year', 30), ('Check the break-even utilisation', 31), ('Offer an idle gap at a lower price', 32), ('Decide to keep, reprice or sell the car', 35)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
OWN = first_name(OWNER); MAN = first_name(MANAGER)
ACC = first_name([t for t in team if t['role'] == 'Accountant'][0]['name']); BRK = first_name([t for t in team if t['role'] == 'Insurance broker'][0]['name'])
MECH = first_name([t for t in team if t['role'] == 'Mechanic'][0]['name']); BKP = first_name([t for t in team if t['role'] == 'Bookkeeper'][0]['name'])
LND = first_name([t for t in team if t['role'] == 'Lender'][0]['name'])
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('o_red', 'Owner: vehicles below the red level', 'trend', 'trend.owner_phone', 'Hello %s, in {month} {red_vehicles} vehicles were below {util_red} utilisation. {business}' % OWN),
    M('o_loss', 'Owner: a vehicle lost money', 'verdict', 'verdict.owner_phone', 'Hello %s, {vehicle} lost {loss} over the last 12 months. Please review it. {business}' % OWN),
    M('o_breakeven', 'Owner: break-even against actual', 'verdict', 'verdict.owner_phone', 'Hello %s, {vehicle} needs {breakeven} utilisation and reaches {utilisation}. {business}' % OWN),
    M('o_idle', 'Owner: idle gaps cost revenue', 'trend', 'trend.owner_phone', 'Hello %s, idle gaps cost {lost_revenue} in {month}. {business}' % OWN),
    M('o_rate', 'Owner: rate below last year', 'adr_ly', 'adr_ly.owner_phone', 'Hello %s, the achieved rate for {class} is {gap} below last year in {month}. {business}' % OWN),
    M('o_short', 'Owner: forecast shortage', 'forecast', 'forecast.owner_phone', 'Hello %s, the forecast shows {shortage_days} days short for {class} in the week of {week}. {business}' % OWN),
    M('o_revpac', 'Owner: revenue per available day', 'trend', 'trend.owner_phone', 'Hello %s, revenue per available day was {revpac} in {month}. {business}' % OWN),
    M('o_profit', 'Owner: profit per vehicle', 'trend', 'trend.owner_phone', 'Hello %s, profit per vehicle was {profit_vehicle} in {month}. {business}' % OWN),
    M('o_class', 'Owner: a class and its profit', 'adr_ly', 'adr_ly.owner_phone', 'Hello %s, {class} earned {profit_vehicle} per vehicle in {month}. {business}' % OWN),
    M('o_month', 'Owner: monthly review is ready', 'trend', 'trend.owner_phone', 'Hello %s, your monthly review for {month} is ready: utilisation {utilisation}, contribution {profit}. {business}' % OWN),
    M('m_offer', 'Manager: offer an idle car', 'idle_runs', 'idle_runs.manager_phone', 'Hello %s, please offer {vehicle} at {price} from {date}, it is idle for {idle_days} days. {business}' % MAN),
    M('m_weekend', 'Manager: raise the weekend rate', 'forecast', 'forecast.manager_phone', 'Hello %s, please raise the weekend rate for {class} on {date}. {business}' % MAN),
    M('m_full', 'Manager: class is full', 'forecast', 'forecast.manager_phone', 'Hello %s, {class} is full on {date}, please close the marketplace listing. {business}' % MAN),
    M('m_promote', 'Manager: promote a class', 'forecast', 'forecast.manager_phone', 'Hello %s, please promote {class} for the week of {week}, {surplus_days} days are free. {business}' % MAN),
    M('m_discount', 'Manager: review the discounts', 'adr_ly', 'adr_ly.manager_phone', 'Hello %s, please review the discounts on {class}, the rate is {gap} below last year in {month}. {business}' % MAN),
    M('m_below', 'Manager: a vehicle is below break-even', 'verdict', 'verdict.manager_phone', 'Hello %s, {vehicle} is below break-even for {months} months. {business}' % MAN),
    M('m_targets', 'Manager: the utilisation targets', 'trend', 'trend.manager_phone', 'Hello %s, the utilisation targets for {month}: red below {util_red}, target {util_target}. {business}' % MAN),
    M('m_review', 'Manager: the rate card review', 'trend', 'trend.manager_phone', 'Hello %s, the rate card review is on {review_date}. Please bring the discount share ({discount_share}). {business}' % MAN),
    M('r_free', 'Renter: a class is free', 'bookings', 'bookings.phone', 'Hello {renter}, a {class} is free for {days} days from {start_date} at {price} a day. {business}'),
    M('r_week', 'Renter: rent for a week and save', 'bookings', 'bookings.phone', 'Hello {renter}, rent a {class} for a week and save {saving}. {business}'),
    M('r_weekend', 'Renter: a weekend deal', 'bookings', 'bookings.phone', 'Hello {renter}, a weekend deal for {class}, {price} a day. {business}'),
    M('r_long', 'Renter: a long-hire price', 'bookings', 'bookings.phone', 'Hello {renter}, thank you for renting. A long-hire price for {class} is {long_price} a day. {business}'),
    M('r_last', 'Renter: a last-minute car', 'bookings', 'bookings.phone', 'Hello {renter}, we have a last-minute {class} for {start_date}, at {price} a day. {business}'),
    M('c_month', 'Corporate account: monthly rate', 'bookings', 'bookings.phone', 'Hello {renter}, a monthly rate for {class} is {long_price} a day. {business}'),
    M('c_usage', 'Corporate account: usage', 'bookings', 'bookings.phone', 'Hello {renter}, your usage last quarter was {usage_days} rented days in the last 90 days. {business}'),
    M('h_weekend', 'Hotel partner: weekend availability', 'forecast', 'forecast.hotel_phone', 'Hello, weekend availability for {class} on {date} is {free_cars} cars. {business}'),
    M('k_lower', 'Marketplace support: lower a price', 'idle_runs', 'idle_runs.market_phone', 'Hello, please lower the price for {vehicle} to {price} a day on {date}. {business}'),
    M('k_raise', 'Marketplace support: raise a price', 'forecast', 'forecast.market_phone', 'Hello, please raise the price for {class} on {date}. {business}'),
    M('a_profit', 'Accountant: profit per vehicle', 'trend', 'trend.accountant_phone', 'Hello %s, profit per vehicle for {year} so far: {profit_vehicle} in {month}. {business}' % ACC),
    M('a_sell', 'Accountant: vehicles planned for sale', 'verdict', 'verdict.accountant_phone', 'Hello %s, we may sell {vehicle} ({class}) this year, profit over 12 months {profit_12m}. {business}' % ACC),
    M('l_summary', 'Lender: utilisation summary', 'trend', 'trend.lender_phone', 'Hello %s, the fleet utilisation summary for {quarter}: {utilisation} in {month}. {business}' % LND),
    M('b_dep', 'Bookkeeper: depreciation setting', 'trend', 'trend.bookkeeper_phone', 'Hello %s, please record the depreciation setting change to {dep_pct}. {business}' % BKP),
    M('i_fleet', 'Insurance broker: fleet size', 'verdict', 'verdict.broker_phone', 'Hello %s, the fleet size next season is {vehicles} vehicles. {business}' % BRK),
    M('x_idle', 'Mechanic: a car is idle', 'idle_runs', 'idle_runs.mechanic_phone', 'Hello %s, {vehicle} will be idle on {date}, a good day for service. {business}' % MECH),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def VMS(col, cond): return SV(col, '%s,%s' % (VM('month'), cond))
THIS = MS; LYM = 'EDATE(%s,-12)' % MS
def UTIL(cond): return 'IFERROR(%s/%s,0)' % (VMS('rented_days', cond), VMS('available_days', cond))
C3 = '">="&EDATE(%s,-2)' % MS
def ADRK(cond_m): return 'IFERROR(SUMIFS({range:adr_class.rental_revenue},%s)/SUMIFS({range:adr_class.rented_days},%s),0)' % (cond_m, cond_m)
AM = '{range:adr_class.month},'
def CU(c): return U(CLC.replace('{in:class}', tok('class', c)), W3)
kpis = [
    KPI('Fleet utilisation this month', UTIL(THIS), 'pct'),
    KPI('Fleet utilisation last 3 months', 'IFERROR(%s/%s,0)' % (SV('rented_days', W3), SV('available_days', W3)), 'pct'),
    KPI('Fleet utilisation same month last year', UTIL(LYM), 'pct'),
    KPI('Best class utilisation, last 3 months', 'MAX(%s)' % ','.join(CU(c) for c in CLASSES), 'pct'),
    KPI('Weakest class utilisation, last 3 months', 'MIN(%s)' % ','.join(CU(c) for c in CLASSES), 'pct'),
    KPI('Vehicles red last 3 months', 'COUNTIFS({range:util_vehicle.band},%s)' % RED, 'int'),
    KPI('Vehicles green last 3 months', 'COUNTIFS({range:util_vehicle.band},%s)' % GRN, 'int'),
    KPI('Vehicles below break-even', 'COUNTIFS({range:breakeven.status},%s)' % tok('be', 'Below break-even'), 'int'),
    KPI('Vehicles losing money last 12 months', 'COUNTIFS({range:vprofit.profit_12m},"<0")', 'int'),
    KPI('Loss of the worst vehicle last 12 months', 'MAX(0,-MIN({range:vprofit.profit_12m}))', 'money'),
    KPI('Profit per vehicle last 12 months', 'IFERROR(SUM({range:vprofit.profit_12m})/COUNTIFS({range:vprofit.avail_12m},">0"),0)', 'money'),
    KPI('Profit per available day last 12 months', 'IFERROR(SUM({range:vprofit.profit_12m})/SUM({range:vprofit.avail_12m}),0)', 'money'),
    KPI('Best vehicle profit last 12 months', 'MAX({range:vprofit.profit_12m})', 'money'),
    KPI('Revenue per available day this month', 'IFERROR(%s/%s,0)' % (VMS('revenue', THIS), VMS('available_days', THIS)), 'money'),
    KPI('Average daily rate this month', ADRK(AM + THIS), 'money'),
    KPI('Average daily rate last 3 months', ADRK(AM + C3), 'money'),
    KPI('Average daily rate same month last year', ADRK(AM + LYM), 'money'),
    KPI('Discount share this month', 'IFERROR(MAX(0,1-SUMIFS({range:adr_class.rental_revenue},%s%s)/SUMIFS({range:adr_class.list_revenue},%s%s)),0)' % (AM, THIS, AM, THIS), 'pct'),
    KPI('Revenue this month so far', VMS('revenue', THIS), 'money'),
    KPI('Contribution this month so far', VMS('profit', THIS), 'money'),
    KPI('Contribution margin last 3 months', 'IFERROR(%s/%s,0)' % (SV('profit', W3), SV('revenue', W3)), 'pct'),
    KPI('Idle days next 14 days', 'SUM({range:idle_runs.next14_days})', 'int'),
    KPI('Idle runs of 3 or more days next 14 days', 'COUNTIFS({range:idle_runs.next14_days},">0")', 'int'),
    KPI('Revenue lost to idle runs last 30 days', 'SUM({range:idle_runs.last30_lost})', 'money'),
    KPI('Weekend utilisation next 4 weeks', PR15, 'pct'),
    KPI('Forecast shortage days next 12 weeks', 'SUM({range:forecast.shortage_days})', 'int'),
    KPI('Forecast surplus days next 12 weeks', 'SUM({range:forecast.surplus_days})', 'int'),
    KPI('Marketplace share of days, last 90 days', 'IFERROR((SUMIFS({range:bookings.rented_days},{range:bookings.channel},%s,{range:bookings.start_date},">="&({today}-90),{range:bookings.start_date},"<="&{today})+SUMIFS({range:bookings.rented_days},{range:bookings.channel},%s,{range:bookings.start_date},">="&({today}-90),{range:bookings.start_date},"<="&{today}))/SUMIFS({range:bookings.rented_days},{range:bookings.start_date},">="&({today}-90),{range:bookings.start_date},"<="&{today}),0)' % (tok('channel', 'Marketplace A'), tok('channel', 'Marketplace B')), 'pct'),
    KPI('Cost per available day last 3 months', 'IFERROR((%s-%s)/%s,0)' % (SV('revenue', W3), SV('profit', W3), SV('available_days', W3)), 'money'),
    KPI('Depreciation per vehicle per month', 'IFERROR(%s/COUNTIFS(%s,">="&EDATE(%s,-2)),0)' % (SV('depreciation', W3), VM('month'), MS), 'money'),
]
assert len(kpis) == 30
dashboard = {"title": "Fleet Profit Dashboard", "kpis": kpis,
    "monthly": {"title": "Revenue, contribution and costs by month", "date": "vmonths.month", "series": [
        {"label": "Revenue", "sum": "vmonths.revenue", "date": "vmonths.month"}, {"label": "Contribution", "sum": "vmonths.profit", "date": "vmonths.month"},
        {"label": "Marketplace fees", "sum": "vmonths.channel_fees", "date": "vmonths.month"}, {"label": "Maintenance", "sum": "vmonths.maintenance", "date": "vmonths.month"}]},
    "breakdowns": [{"title": "Contribution by class", "by": "vmonths.class", "value": "vmonths.profit", "agg": "sum"}, {"title": "Booking value by channel", "by": "bookings.channel", "value": "bookings.total", "agg": "sum"},
                   {"title": "Idle run revenue lost by class", "by": "idle_runs.class", "value": "idle_runs.lost_revenue", "agg": "sum"}, {"title": "12 month profit by vehicle status", "by": "vprofit.status", "value": "vprofit.profit_12m", "agg": "sum"}]}
insights = {"filters": [{"label": "Class", "list": "class"}, {"label": "Channel", "list": "channel"}],
    "gauges": [
        {"title": "Utilisation against your target", "num": AGG('sum', 'vmonths', 'vmonths.rented_days'), "den": AGG('sum', 'vmonths', 'vmonths.available_days')},
        {"title": "Vehicles above break-even", "num": AGG('count', 'breakeven', where=[('status', '=', tok('be', 'Above break-even'))]), "den": AGG('count', 'breakeven')},
        {"title": "Achieved rate against the card", "num": AGG('sum', 'adr_class', 'adr_class.rental_revenue'), "den": AGG('sum', 'adr_class', 'adr_class.list_revenue')},
        {"title": "Revenue per day against your target", "num": AGG('sum', 'revpac_class', 'revpac_class.revpac'), "den": AGG('sum', 'revpac_class', 'revpac_class.target')},
        {"title": "Contribution margin against your target", "num": AGG('sum', 'vmonths', 'vmonths.profit'), "den": AGG('sum', 'vmonths', 'vmonths.revenue')},
        {"title": "Idle runs shorter than the limit", "num": AGG('count', 'idle_runs', where=[('idle_days', '<', 5)]), "den": AGG('count', 'idle_runs')}],
    "charts": [
        CHART('Utilisation per month', 'line', 'month', [AGG('sum', 'trend', 'trend.utilisation', date='trend.month', label='Utilisation')]),
        CHART('Utilisation by class', 'bar', 'util_class.class', [AGG('avg', 'util_class', 'util_class.utilisation', label='Utilisation')]),
        CHART('Utilisation by vehicle band', 'bar', 'bands.band', [AGG('sum', 'bands', 'bands.vehicles', label='Vehicles')]),
        CHART('Utilisation by season', 'bar', 'util_class.season', [AGG('avg', 'util_class', 'util_class.utilisation', label='Utilisation')]),
        CHART('Average daily rate per month', 'line', 'month', [AGG('sum', 'trend', 'trend.adr', date='trend.month', label='Average daily rate')]),
        CHART('Average daily rate by class', 'bar', 'adr_class.class', [AGG('avg', 'adr_class', 'adr_class.achieved_rate', label='Achieved rate'), AGG('avg', 'adr_class', 'adr_class.card_rate', label='Card rate')]),
        CHART('Discount share per month', 'line', 'month', [AGG('sum', 'trend', 'trend.discount_share', date='trend.month', label='Discount share')]),
        CHART('Revenue per available day per month', 'line', 'month', [AGG('sum', 'trend', 'trend.revpac', date='trend.month', label='Revenue per available day')]),
        CHART('Revenue per month', 'column', 'month', [AGG('sum', 'vmonths', 'vmonths.revenue', date='vmonths.month', label='Revenue')]),
        CHART('Contribution per month', 'column', 'month', [AGG('sum', 'vmonths', 'vmonths.profit', date='vmonths.month', label='Contribution')]),
        CHART('Profit by class', 'bar', 'vmonths.class', [AGG('sum', 'vmonths', 'vmonths.profit', label='Profit')]),
        CHART('Profit by vehicle status, 12 months', 'bar', 'vprofit.status', [AGG('sum', 'vprofit', 'vprofit.profit_12m', label='Profit')]),
        CHART('Booking value by channel', 'bar', 'bookings.channel', [AGG('sum', 'bookings', 'bookings.total', label='Booking value')]),
        CHART('Rented days by channel', 'bar', 'bookings.channel', [AGG('sum', 'bookings', 'bookings.rented_days', label='Rented days')]),
        CHART('Rented days by plan', 'bar', 'bookings.plan', [AGG('sum', 'bookings', 'bookings.rented_days', label='Rented days')]),
        CHART('Idle days by class', 'bar', 'idle_runs.class', [AGG('sum', 'idle_runs', 'idle_runs.idle_days', label='Idle days')]),
        CHART('Idle runs per month', 'column', 'month', [AGG('count', 'idle_runs', date='idle_runs.from_date', label='Idle runs')]),
        CHART('Cost per available day by class and line', 'bar', 'costday.class', [AGG('avg', 'costday', 'costday.financing_day', label='Financing'), AGG('avg', 'costday', 'costday.insurance_day', label='Insurance'),
                                                                                   AGG('avg', 'costday', 'costday.maintenance_day', label='Maintenance'), AGG('avg', 'costday', 'costday.depreciation_day', label='Depreciation')]),
        CHART('Maintenance per month', 'column', 'month', [AGG('sum', 'vmonths', 'vmonths.maintenance', date='vmonths.month', label='Maintenance')]),
        CHART('Depreciation per month', 'column', 'month', [AGG('sum', 'vmonths', 'vmonths.depreciation', date='vmonths.month', label='Depreciation')]),
        CHART('Bookings by start weekday', 'bar', 'bookings.start_day', [AGG('count', 'bookings', label='Bookings')]),
        CHART('Booked days by season', 'bar', 'bookings.season', [AGG('sum', 'bookings', 'bookings.rented_days', label='Rented days')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Profit per vehicle per day", "why": "revenue per available day less every cost line, including depreciation and marketplace fees, ranked best to worst for every vehicle", "where": "Profit per Vehicle per Day"},
    {"name": "Break-even utilisation per vehicle", "why": "the utilisation at which each vehicle covers its cost, with the months spent below it and the extra rented days needed", "where": "Vehicle Break-even Tool"},
    {"name": "Vehicle verdict list", "why": "Keep, Reprice or Sell for every vehicle from profit, utilisation and break-even, so the weak car is named", "where": "Vehicle verdict list"},
    {"name": "Idle-day finder", "why": "runs of idle days ranked by lost revenue with an offer price and the revenue if the run is filled", "where": "Idle-Day Finder"},
    {"name": "Discount-to-fill floor", "why": "the lowest price for an idle gap that still covers the variable cost, in closed form", "where": "Discount-to-Fill Floor"},
    {"name": "Rate against history", "why": "achieved average daily rate by class against the rate card and last year, with the discount share given", "where": "Rate Against History"},
    {"name": "Demand forecast and weekend pressure", "why": "12 weeks of booked days against fleet days with Base, Best and Worst scenarios and the weekend load", "where": "Forecast and Weekend Pressure"},
    {"name": "Fleet size fit", "why": "utilisation with one car more or one fewer and the cars a class needs for your target", "where": "Fleet Size Fit"},
    {"name": "Utilisation target solver", "why": "the utilisation a class needs for the profit you want from each vehicle, against what it reaches", "where": "Utilisation Target Solver"},
    {"name": "Monthly performance review", "why": "this month against your last 3 months and last year with a green, amber or red light for each measure", "where": "Monthly Performance Review"}]
competitors = [
    {"what": "subscription rental-management software", "lacks": "charges per vehicle or per user and shows bookings, but has no break-even utilisation per vehicle, no keep, reprice or sell verdict and no idle-day offer"},
    {"what": "generic booking calendar templates", "lacks": "show who has the car on which day but never utilisation by vehicle, profit per available day or the revenue lost to idle runs"},
    {"what": "single-sheet vehicle expense logs", "lacks": "add up costs but know nothing of revenue per available day, financing, depreciation or the utilisation each car must reach"},
    {"what": "budget-model templates", "lacks": "give one profit line for the whole fleet, so the car that loses money every month stays hidden inside a good total"},
    {"what": "pricing spreadsheets", "lacks": "list a rate card but cannot compare the achieved rate with last year, the discount share given or the weekend uplift against how full the weekends are"}]
guide = [
    'Open Start and type your business name, your utilisation levels, your depreciation setting, the discount for an idle gap and the profit you want from one vehicle a month.',
    'Check Vehicles, Vehicle classes, Rate card and Seasons: they hold the fleet, the day prices and the season multipliers every other sheet reads.',
    'Fill Vehicle months once a month: available and rented days, revenue and each cost line for every vehicle. Utilisation, idle days and profit fill in.',
    'Read Utilisation by vehicle and Utilisation by class and month to see the red, amber and green vehicles against your own last 3 months and last year.',
    'Open Profit per vehicle, Break-even by vehicle and Vehicle verdict list to see which cars earn their place and which are a reprice or a sell.',
    'Record idle runs of 3 or more days in Idle runs; the lost revenue, the offer price and the revenue if the run is filled fill in.',
    'Keep Bookings and ADR by class and month up to date to see the achieved rate, the discount share and the rate against last year.',
    'Type the week, fleet days and booked days in Demand forecast 12 weeks to see shortage and surplus days and the weekend load.',
    'Use the 18 tools for the weekly questions: which car to offer, how low a price can go, which vehicle to sell, whether the fleet fits.',
    'Read Month trend and the Monthly Performance Review for the month against your last 3 months and last year.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Profit and Utilisation Dashboard and the Charts every week.',
    'A one-car host can use the same sheets with one vehicle and one channel: the break-even and the verdict tell whether the car pays.']
listing = {"title": "Car Rental Utilisation, Profit and Pricing Review Excel Template: Profit per Vehicle, Break-even, Idle Days, ADR, Forecast",
    "headline": "See which cars earn their place, where the idle days are and what to charge",
    "tags": ["car rental", "fleet utilisation", "profit per vehicle", "break-even", "idle days", "rental pricing", "rental excel", "car sharing host", "revpac adr", "rate card review", "van rental", "fleet review", "excel template"],
    "description": ("Run the numbers side of a small car and van rental or a car-sharing host fleet in one Excel workbook. Built for an owner-operator and a manager who need to know whether each car earns its place: utilisation (rented days as a share of available days) by vehicle and class with red, amber and green bands from your own settings, profit per vehicle per available day, break-even utilisation per vehicle and a keep, reprice or sell verdict. "
        "Vehicle months holds revenue and every cost line (financing, insurance, maintenance, cleaning, fuel or charge, depreciation and marketplace fees) for each vehicle and month; Profit per vehicle, Break-even by vehicle and Cost per day by vehicle fill in by themselves. Profit here is a contribution before office pay and overhead.\n\n"
        "Idle runs lists runs of idle days with the revenue lost at the class rate, an offer price and the revenue if filled. ADR by class and month and ADR against last year show the achieved average daily rate (revenue per rented day) against the rate card, the discount share and the same month last year. Demand forecast 12 weeks sets booked days against fleet days with Base, Best and Worst scenarios and the weekend load. Month trend, Channel profit and RevPAC by class (revenue per available car-day) complete the picture.\n\n"
        f"{len(tools)} decision tools answer the weekly questions: which car to offer for an idle gap, how low a price can go, which vehicle loses money, whether the fleet is the right size, which class needs how much utilisation and how this month compares with your last 3 months. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the owner, the manager, renters, corporate accounts, a hotel partner, marketplace support, the accountant, the lender and the mechanic.\n\n"
        "This is part seven of the Car Rental Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Renters appear by first name and initial only. Miles are the demo unit, set your own; every target is an example, set your own. It helps you keep track of your numbers and does not promise results; confirm tax questions with your adviser."),
    "features": ["Utilisation by vehicle and class with bands", "Profit per vehicle per available day", "Break-even utilisation per vehicle", "Keep, reprice or sell verdict list", "Idle-day finder with offer price",
                 "Achieved rate against the rate card and last year", "12-week demand forecast, Base, Best and Worst", "Weekend pressure and uplift test", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
SUITE = 'fx-20261115-car-rental'
s = spec(id=f'{SUITE}-p7', slug='car-rental-profit', profession='Car Rental Business', name='Utilisation, Profit and Pricing',
         tagline='See which cars earn their place, where the idle days are and what to charge', price_usd=29,
         colors={"primary": "#1D3557", "accent": "#E63946"}, settings=settings, lists=lists + phrase_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Utilisation, profit and pricing review"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cr7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
