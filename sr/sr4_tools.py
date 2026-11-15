"""Short-term rental host suite part 4: the 14 calculators."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr4_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
RATE = '{set:cleaner_rate}'

# 1 day planner
NEED1 = '({in:turns}*{in:hrs}+{in:same}*{in:extra})'; AV1 = '({in:cl}*{in:hpc})'
# 3 same-day timer
SLK3 = '({in:inn}-{in:out}-{in:need})'
# 7 reorder
COV7 = 'IF({in:use}>0,ROUND({in:on}/{in:use}*30,0),365)'
Q7 = 'IF(OR({in:on}<={in:point}*1.25,%s<{set:reorder_cover_days}),MAX(0,{in:par}-{in:on}),0)' % COV7
# 8 cover
DL8 = 'IF({in:use}>0,{in:on}/{in:use}*30,365)'
# 10 laundry compare
OWN10 = '(({in:load_cost}+{in:minutes}/60*' + RATE + ')/{in:per_load})'
# 14 grid
TOT14 = '({in:turns}*({in:hrs}*' + RATE + '+{in:supplies}+{in:linen}))'

tools = [
    TOOL('day_planner', 'Turnover Day Planner', 'Turnovers of a day against the cleaners and hours you have',
         'Type the turnovers of a day, the same-day turns, the hours each takes and the cleaners you have; see the hours needed, the spare hours, the cleaners needed and whether the day is overbooked.', [
        I('turns', 'Turnovers on the day', 5, 'int'), I('same', 'Same-day turns among them', 1, 'int'), I('hrs', 'Average hours per turnover', 3.3, 'num'), I('extra', 'Extra hours for a same-day turn', 0.5, 'num'),
        I('cl', 'Cleaners available', 1, 'int'), I('hpc', 'Hours one cleaner can work that day', 8, 'num')], [
        O('Hours needed', 'num', NEED1), O('Hours available', 'num', AV1), O('Spare hours', 'num', AV1 + '-' + NEED1), O('Hours for each cleaner', 'num', 'IFERROR(%s/{in:cl},0)' % NEED1),
        O('Load of the day', 'pct', 'IFERROR(%s/%s,0)' % (NEED1, AV1)), O('Cleaners needed', 'int', 'ROUNDUP(%s/{in:hpc},0)' % NEED1), O('Cleaners to add', 'int', 'MAX(0,ROUNDUP(%s/{in:hpc},0)-{in:cl})' % NEED1),
        O('Pay for the day', 'money', NEED1 + '*' + RATE + '+{in:same}*{in:hrs}*' + RATE + '*{set:same_day_premium}'),
        O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (NEED1, AV1, ck2('Overbooked'), ck2('Within the limit')))],
         GR('What if', ('Busy day, 5 turnovers and 1 cleaner', {'turns': 5, 'cl': 1}), ('Same day with 3 cleaners', {'turns': 5, 'cl': 3}), ('Festival day, 8 turnovers', {'turns': 8, 'same': 3, 'cl': 3}), ('Quiet day, 2 turnovers', {'turns': 2, 'same': 0, 'cl': 1}))),
    TOOL('workload', 'Cleaner Workload Check', 'Weekly load of one cleaner against the weekly limit',
         'Type the turnovers of one cleaner in a week, the hours each takes, laundry and errand hours and the weekly limit; see the load, the spare hours and how many more turnovers fit.', [
        I('turns', 'Turnovers this week', 14, 'int'), I('hrs', 'Average hours per turnover', 3.3, 'num'), I('other', 'Laundry and errand hours', 3, 'num'), I('limit', 'Weekly hour limit', 30, 'num')], [
        O('Turnover hours', 'num', '{in:turns}*{in:hrs}'), O('Total hours of the week', 'num', '{in:turns}*{in:hrs}+{in:other}'), O('Load against the limit', 'pct', 'IFERROR(({in:turns}*{in:hrs}+{in:other})/{in:limit},0)'),
        O('Spare hours', 'num', '{in:limit}-{in:turns}*{in:hrs}-{in:other}'), O('More turnovers that fit', 'int', 'ROUNDDOWN(MAX(0,{in:limit}-{in:turns}*{in:hrs}-{in:other})/{in:hrs},0)'),
        O('Hours over the limit', 'num', 'MAX(0,{in:turns}*{in:hrs}+{in:other}-{in:limit})'), O('Pay for the week', 'money', '({in:turns}*{in:hrs}+{in:other})*' + RATE),
        O('Verdict', 'text', 'IF({in:turns}*{in:hrs}+{in:other}>{in:limit},%s,%s)' % (ck2('Overbooked'), ck2('Within the limit')))],
         GR('What if', ('Light week, 8 turnovers', {'turns': 8}), ('Busy week, 18 turnovers', {'turns': 18}), ('Part-time limit of 20 hours', {'limit': 20}), ('Faster cleaner, 2.8 hours', {'hrs': 2.8}))),
    TOOL('same_day_timer', 'Same-Day Turn Timer', 'Slack or late start between check-out and check-in',
         'Type the check-out hour, the check-in hour and the hours the unit needs; see the time between the stays, the slack, the latest start and whether a second cleaner is needed.', [
        I('out', 'Check-out hour, 24-hour clock', 11, 'num'), I('inn', 'Check-in hour, 24-hour clock', 15, 'num'), I('need', 'Hours the unit needs', 3.5, 'num')], [
        O('Hours between the stays', 'num', '{in:inn}-{in:out}'), O('Slack after the clean', 'num', SLK3), O('Slack after the spare hours you want', 'num', SLK3 + '-{set:window_buffer_hours}'),
        O('Latest start hour', 'num', '{in:inn}-{in:need}-{set:window_buffer_hours}'), O('Cleaners needed to finish on time', 'int', 'IF(%s<{set:window_buffer_hours},ROUNDUP({in:need}/MAX(0.5,{in:inn}-{in:out}-{set:window_buffer_hours}),0),1)' % SLK3),
        O('Verdict', 'text', 'IF(%s<{set:window_buffer_hours},%s,%s)' % (SLK3, ck2('Late start'), ck2('Slack')))],
         GR('What if', ('Late check-out at 12', {'out': 12}), ('Early check-in at 14', {'inn': 14}), ('Large unit, 5 hours', {'need': 5}), ('Quick studio, 2 hours', {'need': 2}))),
    TOOL('pay_calc', 'Cleaner Pay Calculator', 'Pay for a period with the same-day premium',
         'Type the turnovers and hours of a period, the hourly rate and the hours worked on same-day turns; see the base pay, the premium, the total and the pay per turnover.', [
        I('turns', 'Turnovers in the period', 40, 'int'), I('hours', 'Hours worked', 132, 'num'), I('rate', 'Hourly rate', 17), I('sd_hours', 'Hours on same-day turns', 28, 'num')], [
        O('Base pay', 'money', '{in:hours}*{in:rate}'), O('Same-day premium', 'money', '{in:sd_hours}*{in:rate}*{set:same_day_premium}'), O('Total pay', 'money', '{in:hours}*{in:rate}+{in:sd_hours}*{in:rate}*{set:same_day_premium}'),
        O('Pay per turnover', 'money', 'IFERROR(({in:hours}*{in:rate}+{in:sd_hours}*{in:rate}*{set:same_day_premium})/{in:turns},0)'), O('Average pay per hour', 'money', 'IFERROR(({in:hours}*{in:rate}+{in:sd_hours}*{in:rate}*{set:same_day_premium})/{in:hours},0)'),
        O('Hours per turnover', 'num', 'IFERROR({in:hours}/{in:turns},0)'), O('Pay with the standard rate in your settings', 'money', '{in:hours}*' + RATE)],
         GR('What if', ('Busy month, 55 turnovers', {'turns': 55, 'hours': 180, 'sd_hours': 40}), ('Quiet month, 20 turnovers', {'turns': 20, 'hours': 66, 'sd_hours': 8}), ('Rate of 19 an hour', {'rate': 19}))),
    TOOL('cost_night', 'Cleaning Cost per Night', 'Cleaning cost of a stay spread over its nights',
         'Type the cleaner cost, supplies and linen of a turnover, the nights of a stay and the nightly rate; see the cost per night, its share of the rate and the nights that make a stay worth cleaning for.', [
        I('cleaner', 'Cleaner cost of the turnover', 56), I('supplies', 'Supplies', 14), I('linen', 'Linen wash and wear', 7), I('nights', 'Nights of the stay', 3, 'int'), I('rate', 'Nightly rate', 135)], [
        O('Cost of one turnover', 'money', '{in:cleaner}+{in:supplies}+{in:linen}'), O('Cost per night sold', 'money', 'IFERROR(({in:cleaner}+{in:supplies}+{in:linen})/{in:nights},0)'),
        O('Share of the nightly rate', 'pct', 'IFERROR(({in:cleaner}+{in:supplies}+{in:linen})/{in:nights}/{in:rate},0)'), O('Share of the room revenue of the stay', 'pct', 'IFERROR(({in:cleaner}+{in:supplies}+{in:linen})/({in:nights}*{in:rate}),0)'),
        O('Cost of a one-night stay, share of its rate', 'pct', 'IFERROR(({in:cleaner}+{in:supplies}+{in:linen})/{in:rate},0)'), O('Nights for the cost to be under 10 percent of revenue', 'int', 'IFERROR(ROUNDUP(({in:cleaner}+{in:supplies}+{in:linen})/(0.1*{in:rate}),0),0)')],
         GR('What if', ('One-night stay', {'nights': 1}), ('Week-long stay', {'nights': 7}), ('Large house, cleaner cost 95', {'cleaner': 95, 'rate': 220}), ('Studio, cleaner cost 34', {'cleaner': 34, 'rate': 85}))),
    TOOL('fee_margin', 'Cleaning Fee Margin', 'Margin of the cleaning fee over the cost of a turnover',
         'Type the fee you charge and the cleaner, supplies and linen cost of a turnover; see the margin on each turnover, the fee for your margin target and the margin over a year.', [
        I('fee', 'Cleaning fee charged', 60), I('cleaner', 'Cleaner cost', 56), I('supplies', 'Supplies', 14), I('linen', 'Linen wash and wear', 7), I('turns', 'Turnovers a year', 100, 'int')], [
        O('Total cost of the turnover', 'money', '{in:cleaner}+{in:supplies}+{in:linen}'), O('Margin on each turnover', 'money', '{in:fee}-{in:cleaner}-{in:supplies}-{in:linen}'),
        O('Margin percent', 'pct', 'IFERROR(({in:fee}-{in:cleaner}-{in:supplies}-{in:linen})/{in:fee},0)'), O('Fee for your margin target', 'money', 'ROUNDUP(({in:cleaner}+{in:supplies}+{in:linen})/(1-{set:fee_margin_target}),0)'),
        O('Change needed in the fee', 'money', 'ROUNDUP(({in:cleaner}+{in:supplies}+{in:linen})/(1-{set:fee_margin_target}),0)-{in:fee}'), O('Margin over a year', 'money', '({in:fee}-{in:cleaner}-{in:supplies}-{in:linen})*{in:turns}'),
        O('Verdict', 'text', 'IF({in:fee}<{in:cleaner}+{in:supplies}+{in:linen},%s,IF(({in:fee}-{in:cleaner}-{in:supplies}-{in:linen})/{in:fee}<{set:fee_margin_target},%s,%s))' % (ck2('Raise the fee'), ck2('Fee is fair'), ck2('Fee covers cost')))],
         GR('What if', ('Fee of 45', {'fee': 45}), ('Fee of 75', {'fee': 75}), ('Slow cleaner, cost 70', {'cleaner': 70}), ('Cost of supplies up to 22', {'supplies': 22}))),
    TOOL('reorder_item', 'Supplies Reorder List', 'What to order for an item and what it costs',
         'Type the stock on hand, the reorder point, the par level, the price and the monthly use of an item; see the quantity to order, the cost, the days of cover and the order date.', [
        I('on', 'On hand', 27, 'int'), I('point', 'Reorder point', 40, 'int'), I('par', 'Par level', 90, 'int'), I('price', 'Unit cost', 6.5), I('use', 'Used a month', 36, 'int'), I('lead', 'Lead days of the supplier', 5, 'int')], [
        O('Days of cover', 'int', COV7), O('Quantity to order', 'int', Q7), O('Cost of the order', 'money', '(' + Q7 + ')*{in:price}'), O('Value of the stock on hand', 'money', '{in:on}*{in:price}'),
        O('Order by', 'date', '{today}+MAX(0,%s-{in:lead})' % COV7), O('Stock after the delivery', 'int', '{in:on}+' + Q7),
        O('Verdict', 'text', 'IF(OR({in:on}<={in:point},%s<{in:lead}),%s,%s)' % (COV7, ck2('Order now'), ck2('Stock is fine')))],
         GR('What if', ('Bath towels, low stock', {'on': 27, 'point': 40, 'par': 90}), ('Toilet paper, plenty', {'on': 60, 'point': 24, 'par': 96, 'use': 30, 'price': 9}), ('Smoke alarm batteries', {'on': 3, 'point': 2, 'par': 8, 'use': 1, 'price': 12}), ('Slow supplier, 14 days', {'lead': 14}))),
    TOOL('days_cover', 'Days of Cover', 'Days of stock left and the date to order',
         'Type the stock on hand, the monthly use, the lead time of the supplier and a safety margin; see the days left, the date to order and the stock you need on the shelf at that date.', [
        I('on', 'On hand', 120, 'int'), I('use', 'Used a month', 90, 'int'), I('lead', 'Lead days of the supplier', 5, 'int'), I('safety', 'Safety days', 7, 'int')], [
        O('Used a day', 'num', '{in:use}/30'), O('Days left', 'int', 'ROUND(' + DL8 + ',0)'), O('Date the stock runs out', 'date', '{today}+ROUND(' + DL8 + ',0)'), O('Date to order', 'date', '{today}+MAX(0,ROUND(' + DL8 + ',0)-{in:lead}-{in:safety})'),
        O('Days until you must order', 'int', 'MAX(0,ROUND(' + DL8 + ',0)-{in:lead}-{in:safety})'), O('Stock to hold for the lead time and safety days', 'int', 'ROUNDUP({in:use}/30*({in:lead}+{in:safety}),0)'),
        O('Verdict', 'text', 'IF(' + DL8 + '<={in:lead}+{in:safety},%s,%s)' % (ck2('Order now'), ck2('Stock is fine')))],
         GR('What if', ('Low stock, 30 left', {'on': 30}), ('Heavy use, 150 a month', {'use': 150}), ('Slow supplier, 14 days', {'lead': 14}), ('Plenty of stock, 400', {'on': 400}))),
    TOOL('linen_sets', 'Linen Sets Needed', 'Sets of linen to own for your units and laundry days',
         'Type the units, the stays a week in each, the sets one stay uses and the laundry days a week; see the sets on the beds, in the wash and spare, the sets to own and the yearly replacement cost.', [
        I('units', 'Units', 12, 'int'), I('stays', 'Stays a week in each unit', 3, 'int'), I('per', 'Sets used in one stay', 2, 'int'), I('days', 'Laundry days a week', 2, 'int'), I('price', 'Price of one set', 28), I('wear', 'Sets worn out a year', 0.25, 'pct')], [
        O('Sets used in a week', 'int', '{in:units}*{in:stays}*{in:per}'), O('Sets in one laundry cycle', 'int', 'ROUNDUP({in:units}*{in:stays}*{in:per}/{in:days},0)'), O('Sets on the beds', 'int', '{in:units}*{in:per}'),
        O('Sets in the wash', 'int', 'ROUNDUP({in:units}*{in:stays}*{in:per}/{in:days},0)'), O('Spare sets on the shelf', 'int', 'ROUNDUP({in:units}*{in:stays}*{in:per}/{in:days},0)'),
        O('Sets to own', 'int', '{in:units}*{in:per}+2*ROUNDUP({in:units}*{in:stays}*{in:per}/{in:days},0)'), O('Money tied up in linen', 'money', '({in:units}*{in:per}+2*ROUNDUP({in:units}*{in:stays}*{in:per}/{in:days},0))*{in:price}'),
        O('Sets to replace in a year', 'int', 'ROUNDUP(({in:units}*{in:per}+2*ROUNDUP({in:units}*{in:stays}*{in:per}/{in:days},0))*{in:wear},0)'),
        O('Cost of replacing in a year', 'money', 'ROUNDUP(({in:units}*{in:per}+2*ROUNDUP({in:units}*{in:stays}*{in:per}/{in:days},0))*{in:wear},0)*{in:price}')],
         GR('What if', ('Laundry 3 days a week', {'days': 3}), ('Laundry once a week', {'days': 1}), ('15 units', {'units': 15}), ('Busy units, 5 stays a week', {'stays': 5}))),
    TOOL('laundry_compare', 'Laundry Cost Compare', 'Own machines, laundry service and linen hire per set',
         'Type the cost of a machine load, the minutes of work, the sets in a load and the prices of a laundry service and of linen hire; see the cost per set of each route and which is cheapest.', [
        I('sets', 'Sets a month', 160, 'int'), I('load_cost', 'Cost of one machine load', 2.4), I('minutes', 'Minutes of work per load', 45, 'int'), I('per_load', 'Sets in one load', 2, 'int'), I('service', 'Laundry service price per set', 4.2), I('hire', 'Linen hire price per set', 4.9)], [
        O('Own machines, cost per set', 'money', OWN10), O('Laundry service, cost per set', 'money', '{in:service}'), O('Linen hire, cost per set', 'money', '{in:hire}'),
        O('Own machines, cost a month', 'money', OWN10 + '*{in:sets}'), O('Laundry service, cost a month', 'money', '{in:service}*{in:sets}'), O('Linen hire, cost a month', 'money', '{in:hire}*{in:sets}'),
        O('Saved a month against the dearest route', 'money', '(MAX(%s,{in:service},{in:hire})-MIN(%s,{in:service},{in:hire}))*{in:sets}' % (OWN10, OWN10)),
        O('Verdict', 'text', 'IF(AND(%s<={in:service},%s<={in:hire}),%s,IF({in:service}<={in:hire},%s,%s))' % (OWN10, OWN10, ck2('Own machines are cheapest'), ck2('Laundry service is cheapest'), ck2('Linen hire is cheapest')))],
         GR('What if', ('Slow machines, 90 minutes', {'minutes': 90}), ('Large load, 4 sets', {'per_load': 4}), ('Cheaper service, 2.8', {'service': 2.8}), ('Busy month, 300 sets', {'sets': 300}))),
    TOOL('supplies_budget', 'Supplies Budget', 'Supplies budget for next month from the turnovers',
         'Type the turnovers expected next month, the supplies cost of one turnover, growth and a safety margin; see the budget, the cost per week and per unit and how it compares with last month.', [
        I('turns', 'Turnovers next month', 90, 'int'), I('cost', 'Supplies cost per turnover', 38), I('growth', 'Growth in turnovers', 0.05, 'pct'), I('buffer', 'Safety margin', 0.10, 'pct'), I('units', 'Units', 12, 'int'), I('last', 'Supplies spend last month', 3200)], [
        O('Budget before growth', 'money', '{in:turns}*{in:cost}'), O('Budget with growth', 'money', '{in:turns}*{in:cost}*(1+{in:growth})'), O('Budget with the safety margin', 'money', '{in:turns}*{in:cost}*(1+{in:growth})*(1+{in:buffer})'),
        O('Budget a week', 'money', '{in:turns}*{in:cost}*(1+{in:growth})*(1+{in:buffer})/4.3'), O('Budget a unit', 'money', 'IFERROR({in:turns}*{in:cost}*(1+{in:growth})*(1+{in:buffer})/{in:units},0)'),
        O('Change from last month', 'pct', 'IFERROR({in:turns}*{in:cost}*(1+{in:growth})*(1+{in:buffer})/{in:last}-1,0)'),
        O('Verdict', 'text', 'IF({in:turns}*{in:cost}*(1+{in:growth})*(1+{in:buffer})>{in:last}*1.1,%s,%s)' % (ck2('Over budget'), ck2('Within budget')))],
         GR('What if', ('Peak month, 140 turnovers', {'turns': 140}), ('Quiet month, 50 turnovers', {'turns': 50}), ('Prices up, 44 a turnover', {'cost': 44}), ('No safety margin', {'buffer': 0}))),
    TOOL('redo_cost', 'Redo Cost', 'What it costs when a clean has to be done again',
         'Type the hours lost, the cleaner rate, the refund or discount given, extra supplies and the cleaning fee; see the cost of one redo, its share of the fee and the cost of redos over a month and a year.', [
        I('hours', 'Hours lost', 2, 'num'), I('rate', 'Cleaner rate', 17), I('disc', 'Refund or discount given', 20), I('supplies', 'Extra supplies', 5), I('fee', 'Cleaning fee of the unit', 60), I('count', 'Redos a month', 4, 'int')], [
        O('Labour of the redo', 'money', '{in:hours}*{in:rate}'), O('Cost of one redo', 'money', '{in:hours}*{in:rate}+{in:disc}+{in:supplies}'), O('Share of the cleaning fee', 'pct', 'IFERROR(({in:hours}*{in:rate}+{in:disc}+{in:supplies})/{in:fee},0)'),
        O('Cost of redos in a month', 'money', '({in:hours}*{in:rate}+{in:disc}+{in:supplies})*{in:count}'), O('Cost of redos in a year', 'money', '({in:hours}*{in:rate}+{in:disc}+{in:supplies})*{in:count}*12'),
        O('Verdict', 'text', 'IF({in:hours}*{in:rate}+{in:disc}+{in:supplies}>{in:fee},%s,%s)' % (ck2('Redo costs more than the fee'), ck2('Redo is small')))],
         GR('What if', ('Small fix, 1 hour', {'hours': 1, 'disc': 0}), ('Bad clean, 4 hours and a refund', {'hours': 4, 'disc': 45}), ('Studio fee of 35', {'fee': 35}), ('Two redos a month', {'count': 2}))),
    TOOL('week_rota', 'Cleaner Rota for the Week', 'Cleaners needed on each day of the week',
         'Type the turnovers of each day, the hours each takes, the hours one cleaner works and the cleaners you have; see the cleaners needed each day and whether the week is covered.', [
        I('mon', 'Monday turnovers', 3, 'int'), I('tue', 'Tuesday turnovers', 2, 'int'), I('wed', 'Wednesday turnovers', 4, 'int'), I('thu', 'Thursday turnovers', 3, 'int'), I('fri', 'Friday turnovers', 6, 'int'), I('sat', 'Saturday turnovers', 7, 'int'),
        I('sun', 'Sunday turnovers', 2, 'int'), I('hrs', 'Average hours per turnover', 3.3, 'num'), I('hpc', 'Hours one cleaner works in a day', 8, 'num'), I('cl', 'Cleaners you have', 3, 'int')], [
        O('Cleaners needed on Monday', 'int', 'ROUNDUP({in:mon}*{in:hrs}/{in:hpc},0)'), O('Cleaners needed on Tuesday', 'int', 'ROUNDUP({in:tue}*{in:hrs}/{in:hpc},0)'), O('Cleaners needed on Wednesday', 'int', 'ROUNDUP({in:wed}*{in:hrs}/{in:hpc},0)'),
        O('Cleaners needed on Thursday', 'int', 'ROUNDUP({in:thu}*{in:hrs}/{in:hpc},0)'), O('Cleaners needed on Friday', 'int', 'ROUNDUP({in:fri}*{in:hrs}/{in:hpc},0)'), O('Cleaners needed on Saturday', 'int', 'ROUNDUP({in:sat}*{in:hrs}/{in:hpc},0)'),
        O('Cleaners needed on Sunday', 'int', 'ROUNDUP({in:sun}*{in:hrs}/{in:hpc},0)'), O('Hours of the week', 'num', '({in:mon}+{in:tue}+{in:wed}+{in:thu}+{in:fri}+{in:sat}+{in:sun})*{in:hrs}'),
        O('Hours for each cleaner in the week', 'num', 'IFERROR(({in:mon}+{in:tue}+{in:wed}+{in:thu}+{in:fri}+{in:sat}+{in:sun})*{in:hrs}/{in:cl},0)'),
        O('Verdict', 'text', 'IF(MAX(ROUNDUP({in:mon}*{in:hrs}/{in:hpc},0),ROUNDUP({in:tue}*{in:hrs}/{in:hpc},0),ROUNDUP({in:wed}*{in:hrs}/{in:hpc},0),ROUNDUP({in:thu}*{in:hrs}/{in:hpc},0),ROUNDUP({in:fri}*{in:hrs}/{in:hpc},0),ROUNDUP({in:sat}*{in:hrs}/{in:hpc},0),ROUNDUP({in:sun}*{in:hrs}/{in:hpc},0))>{in:cl},%s,%s)' % (ck2('Add a cleaner'), ck2('Cleaners cover it')))],
         GR('What if', ('Festival weekend', {'fri': 9, 'sat': 11}), ('Quiet week', {'mon': 1, 'tue': 1, 'wed': 2, 'thu': 1, 'fri': 3, 'sat': 3, 'sun': 1}), ('Four cleaners', {'cl': 4}), ('Fast cleaning, 2.6 hours', {'hrs': 2.6}))),
    TOOL('turn_grid', 'Turnovers Pay and Margin Grid', 'Monthly cleaner pay and fee margin for a number of turnovers',
         'Type the turnovers a month, the hours each takes, supplies, linen and the cleaning fee; see the cleaner pay, the cost, the margin and the break-even fee. The grid tries turnovers and fees together.', [
        I('turns', 'Turnovers a month', 90, 'int'), I('hrs', 'Average hours per turnover', 3.3, 'num'), I('supplies', 'Supplies per turnover', 14), I('linen', 'Linen per turnover', 7), I('fee', 'Cleaning fee charged', 60)], [
        O('Cleaner pay a month', 'money', '{in:turns}*{in:hrs}*' + RATE), O('Pay per turnover', 'money', '{in:hrs}*' + RATE), O('Total cleaning cost a month', 'money', TOT14), O('Cleaning fee income a month', 'money', '{in:turns}*{in:fee}'),
        O('Margin a month', 'money', '{in:turns}*{in:fee}-' + TOT14), O('Margin percent', 'pct', 'IFERROR(({in:turns}*{in:fee}-%s)/({in:turns}*{in:fee}),0)' % TOT14),
        O('Break-even fee', 'money', '{in:hrs}*' + RATE + '+{in:supplies}+{in:linen}'), O('Fee for your margin target', 'money', 'ROUNDUP(({in:hrs}*' + RATE + '+{in:supplies}+{in:linen})/(1-{set:fee_margin_target}),0)'),
        O('Margin over a year', 'money', '12*({in:turns}*{in:fee}-' + TOT14 + ')')],
         GR('Turnovers and fee together', ('60 turnovers, fee 50', {'turns': 60, 'fee': 50}), ('60 turnovers, fee 70', {'turns': 60, 'fee': 70}), ('90 turnovers, fee 50', {'turns': 90, 'fee': 50}), ('90 turnovers, fee 70', {'turns': 90, 'fee': 70}),
            ('120 turnovers, fee 50', {'turns': 120, 'fee': 50}), ('120 turnovers, fee 70', {'turns': 120, 'fee': 70}), ('150 turnovers, fee 60', {'turns': 150, 'fee': 60}), ('40 turnovers, fee 60', {'turns': 40, 'fee': 60}))),
]
assert len(tools) == 14, len(tools)
for _t in tools: assert len(_t['hint']) <= 200, (_t['key'], len(_t['hint'])); assert len(_t['title']) <= 60 and len(_t['sheet']) <= 31
