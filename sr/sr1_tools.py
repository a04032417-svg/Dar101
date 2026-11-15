"""Short-term rental host suite part 1: the 14 calculators."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr1_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
FEE = 'AVERAGE({range:channels.fee_pct})'
FRI = tok('daytype', 'Friday or Saturday'); SUN = tok('daytype', 'Sunday to Thursday')

# 1 nightly rate suggester
SEAS1 = '({in:base}*{in:sf})'; WK1 = 'IF({in:wk}=%s,1+{set:weekend_lift},1)' % FRI
LM1 = 'IF(AND({in:days}<={set:lastmin_days},{in:occ}<{set:target_occupancy}),1-{set:lastmin_discount},1)'
RATE1 = 'ROUND(%s*%s*{in:dem}*(1+{in:ev})*%s,0)' % (SEAS1, WK1, LM1)
# 3 event week
SCAR3 = 'IF({in:left}<={in:total}*0.3,0.1,0)'; ASK3 = 'ROUND({in:cur}*(1+{in:lift}+%s),0)' % SCAR3
# 4 gap night
DISC4 = 'MIN(0.3,{set:gap_discount}*IF({in:days}<=3,2,IF({in:days}<=7,1.5,1)))'; OFF4 = 'ROUND({in:usual}*(1-%s),0)' % DISC4; LOW4 = '({in:var}/(1-' + FEE + '))'
# 5 last minute
DISC5 = 'IF(AND({in:days}<={set:lastmin_days},{in:occ}<{set:target_occupancy}),{set:lastmin_discount},IF(AND({in:days}<=2*{set:lastmin_days},{in:occ}<{set:target_occupancy}-0.1),{set:lastmin_discount}/2,0))'
OFF5 = '({in:usual}*(1-%s))' % DISC5
# 6 length of stay
DISC6 = 'IF({in:nights}>=28,{in:md},IF({in:nights}>=7,{in:wd},0))'
# 7 minimum stay
SMIN7 = 'IF({in:season}=%s,3,IF(OR({in:season}=%s,{in:season}=%s),2,1))' % (tok('season', 'Peak'), tok('season', 'High'), tok('season', 'Shoulder'))
NEED7 = 'MAX(1,ROUNDUP({in:turn}/({in:rate}*(1-' + FEE + ')),0))'; NORM7 = 'MAX(%s,%s)' % (SMIN7, NEED7)
SHORT7 = 'IF({in:lead}<={set:lastmin_days},MAX(1,%s-1),%s)' % (NORM7, NORM7)
NET7 = '({in:req}*{in:rate}*(1-' + FEE + ')-{in:turn})'
# 8 cleaning fee
COST8 = '({in:hours}*{set:cleaner_rate}+{in:supplies}+{in:linen})'; FEE8 = 'ROUND(%s/(1-{in:margin}),0)' % COST8
# 9 break-even
BER9 = '(({in:fixed}/(30.4*{in:occ})+{in:var})/(1-{in:fee}))'; UNIT9 = '({in:rate}*(1-{in:fee})-{in:var})'
# 10 comparables
AVG10 = '(({in:c1}+{in:c2}+{in:c3})/3)'; AVR10 = '(({in:s1}+{in:s2}+{in:s3})/3)'
# 11 direct
PN11 = '(({in:rate}*{in:nights}+{in:clean})*(1-{in:fee}))'; DN11 = '(({in:rate}*{in:nights}*(1-{in:disc})+{in:clean})*(1-{in:dfee}))'
# 12 rate impact
PR12 = '({in:cur}*(1-{in:fee})-{in:var})*{in:avail}*{in:occ}'; PN12 = '({in:new}*(1-{in:fee})-{in:var})*{in:avail}*{in:occ2}'
# 13 rate card
def SF13(s): return 'AVERAGEIF({range:seasons.season},%s,{range:seasons.price_factor})' % tok('season', s)
def RC13(s, wk): return 'ROUND({in:base}*%s%s/{in:step},0)*{in:step}' % (SF13(s), '*(1+{in:lift})' if wk else '')
# 14 grid
REV14 = '({in:rate}*{in:nights}*{in:occ})'

tools = [
    TOOL('rate_suggester', 'Nightly Rate Suggester', 'Nightly rate from season, demand and days left',
         'Type the base rate, season factor, night type, demand, event lift, days to check-in and occupancy; see the rate to list, how it compares with the base rate, the target ADR and the rate listed now.', [
        I('base', 'Base rate', 135), I('sf', 'Season factor of the month', 1.15, 'num'), IN('wk', 'Night type', 'list', key('daytype', 'Sunday to Thursday'), list='daytype'), I('dem', 'Demand index, 1 is a normal week', 1.0, 'num'),
        I('ev', 'Local event lift', 0.0, 'pct'), I('days', 'Days to check-in', 21, 'int'), I('occ', 'Occupancy of the next 30 days', 0.55, 'pct'), I('listed', 'Rate listed now', 150)], [
        O('Season rate, base rate times season factor', 'money', SEAS1), O('Night type factor', 'num', WK1), O('Demand and event factor', 'num', '{in:dem}*(1+{in:ev})'), O('Last-minute factor', 'num', LM1),
        O('Rate to list', 'money', RATE1), O('Against the base rate', 'pct', 'IFERROR(%s/{in:base}-1,0)' % RATE1), O('Against the wanted ADR', 'pct', 'IFERROR(%s/{set:target_adr}-1,0)' % RATE1),
        O('Change from the rate listed now', 'money', RATE1 + '-{in:listed}'), O('Change percent', 'pct', 'IFERROR(%s/{in:listed}-1,0)' % RATE1), O('Rate after the average platform fee', 'money', RATE1 + '*(1-' + FEE + ')'),
        O('Rate for a direct booking', 'money', 'ROUND(%s*(1-{set:direct_discount}),0)' % RATE1),
        O('Verdict', 'text', 'IF(%s>{in:listed}*(1+{set:rate_tolerance}),%s,IF(%s<{in:listed}*(1-{set:rate_tolerance}),%s,%s))' % (RATE1, ck2('Raise the rate'), RATE1, ck2('Lower the rate'), ck2('Hold the rate')))],
         GR('What if', ('Friday or Saturday night', {'wk': '=' + FRI}), ('Peak month, factor 1.42', {'sf': 1.42}), ('Festival week, lift 50 percent', {'ev': 0.5, 'dem': 1.0}), ('Check-in in 2 days, empty month', {'days': 2, 'occ': 0.35}),
            ('Quiet season, factor 0.79', {'sf': 0.79, 'dem': 0.9}))),
    TOOL('season_lift', 'Season and Weekend Lift', 'Rate card for a month and for the year',
         'Type the base rate, month, weekend lift and occupancy; the factor comes from your Seasons sheet; see the weekday and weekend rate, the lowest and peak rates and the revenue of the month and year.', [
        I('base', 'Base rate', 135), I('month', 'Month number, 1 to 12', 7, 'int'), I('lift', 'Friday and Saturday lift', 0.15, 'pct'), I('occ', 'Occupancy wanted', 0.65, 'pct')], [
        O('Season of the month', 'text', 'INDEX({range:seasons.season},{in:month})'), O('Price factor of the month', 'num', 'INDEX({range:seasons.price_factor},{in:month})'),
        O('Weekday rate', 'money', 'ROUND({in:base}*INDEX({range:seasons.price_factor},{in:month}),0)'), O('Weekend rate', 'money', 'ROUND({in:base}*INDEX({range:seasons.price_factor},{in:month})*(1+{in:lift}),0)'),
        O('Blended rate, five weekday and two weekend nights', 'money', 'ROUND({in:base}*INDEX({range:seasons.price_factor},{in:month})*(1+{in:lift}*2/7),0)'),
        O('Weekday rate in the lowest month', 'money', 'ROUND({in:base}*MIN({range:seasons.price_factor}),0)'), O('Weekday rate in the peak month', 'money', 'ROUND({in:base}*MAX({range:seasons.price_factor}),0)'),
        O('Peak month against lowest month', 'pct', 'IFERROR(MAX({range:seasons.price_factor})/MIN({range:seasons.price_factor})-1,0)'), O('Average weekday rate for the year', 'money', 'ROUND({in:base}*AVERAGE({range:seasons.price_factor}),0)'),
        O('Room revenue of the month at the wanted occupancy', 'money', '{in:base}*INDEX({range:seasons.price_factor},{in:month})*(1+{in:lift}*2/7)*30.4*{in:occ}'),
        O('Room revenue of the year at the wanted occupancy', 'money', '{in:base}*AVERAGE({range:seasons.price_factor})*(1+{in:lift}*2/7)*365*{in:occ}')],
         GR('What if', ('January', {'month': 1}), ('August', {'month': 8}), ('Weekend lift 25 percent', {'lift': 0.25}), ('Premium unit, base 280', {'base': 280}), ('Occupancy 80 percent', {'occ': 0.8}))),
    TOOL('event_pricing', 'Event Week Pricing', 'Rate to ask in a local event week',
         'Type the rate listed now, the event demand lift, the nights left and the nights in the event and the comparable rate; see the rate to ask, the extra revenue and the minimum stay to set.', [
        I('cur', 'Rate listed now', 135), I('lift', 'Event demand lift', 0.5, 'pct'), I('left', 'Nights still free in the event', 3, 'int'), I('total', 'Nights in the event', 7, 'int'), I('days', 'Days to the event', 24, 'int'),
        I('comp', 'Average comparable rate in the event', 205), I('booked', 'Nights already booked at the old rate', 4, 'int')], [
        O('Scarcity premium, when few nights are left', 'pct', SCAR3), O('Rate to ask', 'money', ASK3), O('Increase against the listed rate', 'money', ASK3 + '-{in:cur}'),
        O('Revenue from the free nights at the listed rate', 'money', '{in:left}*{in:cur}'), O('Revenue from the free nights at the asked rate', 'money', '{in:left}*' + ASK3),
        O('Extra revenue from the free nights', 'money', '{in:left}*(' + ASK3 + '-{in:cur})'), O('Revenue already booked at the old rate, left on the table', 'money', '{in:booked}*(' + ASK3 + '-{in:cur})'),
        O('Share of the event still free', 'pct', 'IFERROR({in:left}/{in:total},0)'), O('Asked rate against comparables', 'pct', 'IFERROR(%s/{in:comp}-1,0)' % ASK3),
        O('Minimum stay to set', 'int', 'IF({in:lift}>=0.4,3,IF({in:lift}>=0.25,2,1))'),
        O('Verdict', 'text', 'IF(%s>{in:comp}*1.15,%s,%s)' % (ASK3, ck2('Priced above comparables'), ck2('Event rate applies')))],
         GR('What if', ('Only one night left', {'left': 1}), ('Lift 30 percent', {'lift': 0.3}), ('Event in 5 days', {'days': 5, 'left': 5}), ('Comparable rate 170', {'comp': 170}), ('Weekend event, 3 nights', {'total': 3, 'left': 1, 'lift': 0.35}))),
    TOOL('gap_discount_tool', 'Gap-Night Discount', 'Discount for a free night between two bookings',
         'Type the free nights, the days to check-in, the usual rate and the extra cost of a night; see the discount to offer, the offer rate, the revenue and profit gained and the lowest rate that still pays.', [
        I('free', 'Free nights between the two bookings', 2, 'int'), I('days', 'Days until the first free night', 6, 'int'), I('usual', 'Usual rate for those nights', 118), I('var', 'Extra cost of one more night', 11)], [
        O('Discount to offer', 'pct', DISC4), O('Offer rate', 'money', OFF4), O('Revenue gained if filled', 'money', '{in:free}*' + OFF4), O('Extra cost of the nights', 'money', '{in:free}*{in:var}'),
        O('Profit gained after platform fee and cost', 'money', '{in:free}*(' + OFF4 + '*(1-' + FEE + ')-{in:var})'), O('Revenue lost to the discount if it would have filled anyway', 'money', '{in:free}*({in:usual}-' + OFF4 + ')'),
        O('Lowest rate that still covers cost', 'money', LOW4), O('Offer rate as a share of the usual rate', 'pct', 'IFERROR(%s/{in:usual},0)' % OFF4),
        O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (OFF4, LOW4, ck2('Offer the discount'), ck2('Hold the price')))],
         GR('What if', ('Check-in in 2 days', {'days': 2}), ('Three free nights', {'free': 3}), ('Check-in in 3 weeks', {'days': 21}), ('Studio at a low rate, 66', {'usual': 66, 'var': 9}), ('High cost night', {'var': 70}))),
    TOOL('lastmin_tool', 'Last-Minute Discount Decision', 'Last-minute discount or hold for the nights ahead',
         'Type the days to check-in, the free nights, the occupancy of the next 30 days, the usual rate and the cost of a stay; see whether to discount, the offer rate and the profit of one stay.', [
        I('days', 'Days to check-in', 2, 'int'), I('free', 'Free nights in the next 7 days', 3, 'int'), I('occ', 'Occupancy of the next 30 days', 0.52, 'pct'), I('usual', 'Usual rate', 140), I('var', 'Cost of one night', 12),
        I('nights', 'Length of the stay wanted', 2, 'int'), I('turn', 'Net cost of the turnover (clean and reset)', 28)], [
        O('Discount to offer', 'pct', DISC5), O('Offer rate', 'money', OFF5), O('Revenue of the stay', 'money', '{in:nights}*' + OFF5),
        O('Profit of the stay after platform fee, costs and turnover', 'money', '{in:nights}*(' + OFF5 + '*(1-' + FEE + ')-{in:var})-{in:turn}'),
        O('Occupancy against your target', 'pct', '{in:occ}-{set:target_occupancy}'), O('Revenue at risk if the nights stay empty', 'money', '{in:free}*{in:usual}'), O('Revenue lost to the discount per night', 'money', '{in:usual}-' + OFF5),
        O('Lowest rate that covers the cost of a night', 'money', '{in:var}/(1-' + FEE + ')'),
        O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (DISC5, ck2('Offer the discount'), ck2('Hold the price')))],
         GR('What if', ('Check-in tomorrow', {'days': 1}), ('Busy month, 80 percent', {'occ': 0.8}), ('Check-in in 12 days', {'days': 12, 'occ': 0.45}), ('Five free nights', {'free': 5}), ('Four-night stay', {'nights': 4}))),
    TOOL('stay_discount', 'Length-of-Stay Discount', 'Price per night and total for a long stay',
         'Type the nightly rate, the nights, the weekly and monthly discount and the cleaning fee; see the price per night, the total, the guest saving and what the host keeps.', [
        I('rate', 'Nightly rate', 140), I('nights', 'Nights', 9, 'int'), I('wd', 'Discount for 7 nights or more', 0.08, 'pct'), I('md', 'Discount for 28 nights or more', 0.20, 'pct'), I('clean', 'Cleaning fee', 60), I('turn', 'Cost of the turnover', 40)], [
        O('Discount applied', 'pct', DISC6), O('Price per night', 'money', '{in:rate}*(1-' + DISC6 + ')'), O('Room total', 'money', '{in:nights}*{in:rate}*(1-' + DISC6 + ')'), O('Total for the guest with the cleaning fee', 'money', '{in:nights}*{in:rate}*(1-' + DISC6 + ')+{in:clean}'),
        O('Total without the discount', 'money', '{in:nights}*{in:rate}+{in:clean}'), O('Guest saving', 'money', '{in:nights}*{in:rate}*' + DISC6), O('Price per night including the cleaning fee', 'money', 'IFERROR(({in:nights}*{in:rate}*(1-' + DISC6 + ')+{in:clean})/{in:nights},0)'),
        O('Host keeps after platform fee and turnover', 'money', '({in:nights}*{in:rate}*(1-' + DISC6 + ')+{in:clean})*(1-' + FEE + ')-{in:turn}'), O('Host keeps per night', 'money', 'IFERROR((({in:nights}*{in:rate}*(1-' + DISC6 + ')+{in:clean})*(1-' + FEE + ')-{in:turn})/{in:nights},0)'),
        O('Nights to the next discount level', 'int', 'IF({in:nights}>=28,0,IF({in:nights}>=7,28-{in:nights},7-{in:nights}))')],
         GR('What if', ('Six nights', {'nights': 6}), ('Seven nights', {'nights': 7}), ('A month, 30 nights', {'nights': 30}), ('Weekly discount 12 percent', {'wd': 0.12}), ('Premium unit, rate 280', {'rate': 280, 'clean': 95}))),
    TOOL('minstay_tool', 'Minimum-Stay Optimizer', 'Shortest stay worth accepting',
         'Type the days to check-in, the free gap, the season, the stay requested, the rate and the net cost of a turnover; see the seasonal minimum, the nights that pay for a turnover and whether to accept.', [
        I('lead', 'Days to check-in', 10, 'int'), I('gap', 'Free nights between the two bookings, 0 if none', 2, 'int'), IN('season', 'Season', 'list', key('season', 'Peak'), list='season'), I('req', 'Nights requested', 2, 'int'),
        I('rate', 'Nightly rate', 150), I('turn', 'Net cost of the turnover, cleaning less the fee paid', 35)], [
        O('Seasonal minimum stay', 'int', SMIN7), O('Nights needed to pay for one turnover', 'int', NEED7), O('Normal minimum stay', 'int', NORM7), O('Shortest stay worth accepting', 'int', SHORT7),
        O('Net income of the requested stay', 'money', NET7), O('Net income per night', 'money', 'IFERROR(%s/{in:req},0)' % NET7), O('Nights short of the shortest stay', 'int', 'MAX(0,%s-{in:req})' % SHORT7),
        O('Verdict', 'text', 'IF({in:req}>=%s,%s,IF(AND({in:gap}>0,{in:req}={in:gap},%s>0),%s,%s))' % (SHORT7, ck2('Accept the stay'), NET7, ck2('Shorten the minimum'), ck2('Keep the minimum')))],
         GR('What if', ('One night in peak season', {'req': 1, 'gap': 0}), ('Three nights', {'req': 3}), ('Low season, one night', {'season': '=' + tok('season', 'Low'), 'req': 1, 'gap': 0, 'rate': 95}), ('Check-in tomorrow', {'lead': 1, 'req': 2}), ('Costly turnover 70', {'turn': 70}))),
    TOOL('fee_pricer', 'Cleaning Fee Pricer', 'Cleaning fee that reaches your margin target',
         'Type the bedrooms, the cleaner hours, supplies, linen, your margin target and the fee you charge; see the cost of a turnover, the fee to charge, the margin now and the yearly shortfall.', [
        I('bed', 'Bedrooms', 2, 'int'), I('hours', 'Cleaner hours for one turnover', 1.8, 'num'), I('supplies', 'Supplies per turnover', 6), I('linen', 'Linen per turnover', 12), I('margin', 'Margin wanted on the fee', 0.30, 'pct'),
        I('cur', 'Fee charged now', 55), I('stays', 'Stays per year', 60, 'int'), I('avg', 'Average nights per stay', 3.2, 'num')], [
        O('Cleaner cost', 'money', '{in:hours}*{set:cleaner_rate}'), O('Total cost of a turnover', 'money', COST8), O('Fee for your margin target', 'money', FEE8), O('Margin at the fee charged now', 'money', '{in:cur}-' + COST8),
        O('Margin percent at the fee charged now', 'pct', 'IFERROR(({in:cur}-%s)/{in:cur},0)' % COST8), O('Shortfall per turnover', 'money', 'MAX(0,%s-{in:cur})' % FEE8), O('Shortfall per year', 'money', '{in:stays}*MAX(0,%s-{in:cur})' % FEE8),
        O('Fee per night of an average stay', 'money', 'IFERROR(%s/{in:avg},0)' % FEE8), O('Fee against the average of your units', 'pct', 'IFERROR(%s/AVERAGE({range:units.cleaning_fee})-1,0)' % FEE8), O('Cleaner hours per bedroom', 'num', 'IFERROR({in:hours}/{in:bed},0)'),
        O('Verdict', 'text', 'IF({in:cur}>=%s,%s,%s)' % (FEE8, ck2('Fee is fair'), ck2('Raise the fee')))],
         GR('What if', ('Studio, 1.5 hours, fee 25', {'bed': 1, 'hours': 1.5, 'cur': 25, 'linen': 8}), ('House, 3.7 hours, fee 85', {'bed': 3, 'hours': 3.7, 'cur': 85, 'linen': 22}), ('Margin target 40 percent', {'margin': 0.4}), ('Dearer linen 25', {'linen': 25}), ('Fee 75', {'cur': 75}))),
    TOOL('breakeven_tool', 'Break-Even Rate and Occupancy', 'Break-even rate and occupancy for one unit',
         'Type the fixed cost a month, cost per night, platform fee, target occupancy and your rate; see the break-even rate and occupancy, the profit a month and a year, and the lowest rate that pays.', [
        I('fixed', 'Fixed cost per month, rent, utilities, internet and other', 1620), I('var', 'Variable cost per night', 9), I('fee', 'Platform fee', 0.12, 'pct'), I('occ', 'Target occupancy', 0.62, 'pct'), I('rate', 'Rate you charge', 135)], [
        O('Break-even rate at the target occupancy', 'money', BER9), O('Break-even occupancy at your rate', 'pct', 'IF(%s>0,{in:fixed}/(%s*30.4),0)' % (UNIT9, UNIT9)), O('Margin per night at your rate', 'money', UNIT9),
        O('Booked nights a month at the target occupancy', 'num', '30.4*{in:occ}'), O('Profit per month at the target occupancy', 'money', UNIT9 + '*30.4*{in:occ}-{in:fixed}'),
        O('Profit per year at the target occupancy', 'money', '12*(' + UNIT9 + '*30.4*{in:occ}-{in:fixed})'), O('Rate against the break-even rate', 'pct', 'IFERROR({in:rate}/%s-1,0)' % BER9),
        O('Lowest rate that covers the cost of a night', 'money', '{in:var}/(1-{in:fee})'), O('Booked nights a month to break even', 'num', 'IF(%s>0,{in:fixed}/%s,0)' % (UNIT9, UNIT9)),
        O('Verdict', 'text', 'IF({in:rate}>=%s,%s,%s)' % (BER9, ck2('Above break-even'), ck2('Below break-even')))],
         GR('What if', ('Studio at a loss, rent 1180, rate 66', {'fixed': 1620, 'rate': 66, 'var': 9}), ('Managed unit, fixed cost 330', {'fixed': 330}), ('Occupancy 75 percent', {'occ': 0.75}), ('Direct bookings, fee 3 percent', {'fee': 0.03}), ('Rate 160', {'rate': 160}))),
    TOOL('comp_compare', 'Comparable Rate Position', 'Our rate against three comparable listings',
         'Type our rate and review score and the rates and review scores of three comparable listings; see the average, the gap, our rank by price and a review-adjusted rate.', [
        I('ours', 'Our rate', 150), I('r0', 'Our review score', 4.7, 'num'), I('c1', 'Comparable 1 rate', 165), I('s1', 'Comparable 1 review score', 4.8, 'num'), I('c2', 'Comparable 2 rate', 140), I('s2', 'Comparable 2 review score', 4.4, 'num'),
        I('c3', 'Comparable 3 rate', 175), I('s3', 'Comparable 3 review score', 4.9, 'num')], [
        O('Average comparable rate', 'money', AVG10), O('Highest comparable rate', 'money', 'MAX({in:c1},{in:c2},{in:c3})'), O('Lowest comparable rate', 'money', 'MIN({in:c1},{in:c2},{in:c3})'),
        O('Gap to the average', 'money', '{in:ours}-' + AVG10), O('Gap percent', 'pct', 'IFERROR({in:ours}/%s-1,0)' % AVG10), O('Our rank by price, 1 is the highest', 'int', '1+({in:c1}>{in:ours})+({in:c2}>{in:ours})+({in:c3}>{in:ours})'),
        O('Average comparable review score', 'num', AVR10), O('Our review score against the average', 'num', '{in:r0}-' + AVR10), O('Review-adjusted rate to match', 'money', 'ROUND(%s*(1+({in:r0}-%s)*0.2),0)' % (AVG10, AVR10)),
        O('Room to raise the rate', 'money', 'MAX(0,ROUND(%s*(1+({in:r0}-%s)*0.2),0)-{in:ours})' % (AVG10, AVR10)),
        O('Verdict', 'text', 'IF({in:ours}>%s*1.05,%s,IF({in:ours}<%s*0.95,%s,%s))' % (AVG10, ck2('Priced above comparables'), AVG10, ck2('Priced below comparables'), ck2('Priced in line')))],
         GR('What if', ('Our rate 130', {'ours': 130}), ('Our rate 190', {'ours': 190}), ('Our review score 4.3', {'r0': 4.3}), ('Comparable 3 drops to 150', {'c3': 150}), ('All comparables near 140', {'c1': 140, 'c2': 138, 'c3': 142}))),
    TOOL('direct_price', 'Direct Booking Price and Saving', 'Direct booking price, host income and guest saving',
         'Type the rate, nights, cleaning fee, platform fee, direct payment fee and the discount you give; see the guest price, what the host keeps on each route and the largest discount that still pays.', [
        I('rate', 'Nightly rate', 140), I('nights', 'Nights', 4, 'int'), I('clean', 'Cleaning fee', 60), I('fee', 'Platform fee', 0.15, 'pct'), I('dfee', 'Card payment fee on a direct booking', 0.03, 'pct'), I('disc', 'Discount you give a direct guest', 0.05, 'pct')], [
        O('Guest price on the platform', 'money', '{in:rate}*{in:nights}+{in:clean}'), O('Guest price booking direct', 'money', '{in:rate}*{in:nights}*(1-{in:disc})+{in:clean}'), O('Guest saving', 'money', '{in:rate}*{in:nights}*{in:disc}'),
        O('Host keeps on the platform', 'money', PN11), O('Host keeps booking direct', 'money', DN11), O('Host extra income from the direct booking', 'money', DN11 + '-' + PN11), O('Extra income per night', 'money', 'IFERROR((%s-%s)/{in:nights},0)' % (DN11, PN11)),
        O('Largest discount that earns the host the same', 'pct', 'IFERROR(1-((({in:rate}*{in:nights}+{in:clean})*(1-{in:fee}))/(1-{in:dfee})-{in:clean})/({in:rate}*{in:nights}),0)'),
        O('Platform fee saved', 'money', '({in:rate}*{in:nights}+{in:clean})*{in:fee}'), O('Share of the fee saving passed to the guest', 'pct', 'IFERROR({in:rate}*{in:nights}*{in:disc}/(({in:rate}*{in:nights}+{in:clean})*{in:fee}),0)'),
        O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (DN11, PN11, ck2('Direct earns the host more'), ck2('Direct is cheaper for the guest')))],
         GR('What if', ('Discount 10 percent', {'disc': 0.10}), ('Discount 15 percent', {'disc': 0.15}), ('Long stay, 10 nights', {'nights': 10}), ('Low platform fee 12 percent', {'fee': 0.12}), ('Premium unit, rate 280', {'rate': 280, 'clean': 95}))),
    TOOL('rate_impact', 'Revenue Impact of a Rate Change', 'Revenue and profit change when a rate changes',
         'Type the rate now and the new rate, the occupancy now and the occupancy you expect, the cost and the platform fee; see the revenue and profit change and the occupancy loss the new rate can bear.', [
        I('cur', 'Rate now', 140), I('new', 'New rate', 155), I('occ', 'Occupancy now', 0.62, 'pct'), I('occ2', 'Occupancy expected at the new rate', 0.58, 'pct'), I('var', 'Cost per booked night', 12), I('fee', 'Platform fee', 0.12, 'pct'),
        I('avail', 'Nights available in the month', 30, 'int')], [
        O('Booked nights now', 'num', '{in:avail}*{in:occ}'), O('Booked nights after the change', 'num', '{in:avail}*{in:occ2}'), O('Room revenue now', 'money', '{in:cur}*{in:avail}*{in:occ}'), O('Room revenue after the change', 'money', '{in:new}*{in:avail}*{in:occ2}'),
        O('Revenue change', 'money', '{in:new}*{in:avail}*{in:occ2}-{in:cur}*{in:avail}*{in:occ}'), O('Profit now', 'money', PR12), O('Profit after the change', 'money', PN12), O('Profit change', 'money', PN12 + '-' + PR12),
        O('Occupancy at which profit stays the same', 'pct', 'IFERROR((%s)/(({in:new}*(1-{in:fee})-{in:var})*{in:avail}),0)' % PR12), O('Occupancy loss the new rate can bear', 'pct', '{in:occ}-IFERROR((%s)/(({in:new}*(1-{in:fee})-{in:var})*{in:avail}),0)' % PR12),
        O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (PN12, PR12, ck2('Rate change adds profit'), ck2('Rate change loses profit')))],
         GR('What if', ('Occupancy falls to 50 percent', {'occ2': 0.50}), ('Occupancy holds at 62 percent', {'occ2': 0.62}), ('Small rise to 145', {'new': 145, 'occ2': 0.60}), ('Cut the rate to 125', {'new': 125, 'occ2': 0.72}), ('High-rate unit, 230 to 250', {'cur': 230, 'new': 250, 'occ2': 0.60, 'var': 15}))),
    TOOL('rate_card', 'Seasonal Rate Card Builder', 'Weekday and weekend rate for each season of a unit',
         'Type the row number of the unit in your Units sheet, the weekend lift and the rounding step; the rates come from the base rate and your Seasons sheet; see the card for each season.', [
        I('row', 'Row number in the Units sheet, 1 to 12', 1, 'int'), I('lift', 'Friday and Saturday lift', 0.15, 'pct'), I('step', 'Round rates to the nearest', 5, 'int')], [
        O('Unit', 'text', 'INDEX({range:units.name},{in:row})'), O('Base rate', 'money', 'INDEX({range:units.base_rate},{in:row})'),
        O('Low season weekday rate', 'money', RC13('Low', 0).replace('{in:base}', 'INDEX({range:units.base_rate},{in:row})')), O('Low season weekend rate', 'money', RC13('Low', 1).replace('{in:base}', 'INDEX({range:units.base_rate},{in:row})')),
        O('Shoulder season weekday rate', 'money', RC13('Shoulder', 0).replace('{in:base}', 'INDEX({range:units.base_rate},{in:row})')), O('Shoulder season weekend rate', 'money', RC13('Shoulder', 1).replace('{in:base}', 'INDEX({range:units.base_rate},{in:row})')),
        O('High season weekday rate', 'money', RC13('High', 0).replace('{in:base}', 'INDEX({range:units.base_rate},{in:row})')), O('High season weekend rate', 'money', RC13('High', 1).replace('{in:base}', 'INDEX({range:units.base_rate},{in:row})')),
        O('Peak season weekday rate', 'money', RC13('Peak', 0).replace('{in:base}', 'INDEX({range:units.base_rate},{in:row})')), O('Peak season weekend rate', 'money', RC13('Peak', 1).replace('{in:base}', 'INDEX({range:units.base_rate},{in:row})')),
        O('Break-even rate of the unit', 'money', 'INDEX({range:units.break_even},{in:row})'), O('Lowest season weekday rate against break-even', 'money', RC13('Low', 0).replace('{in:base}', 'INDEX({range:units.base_rate},{in:row})') + '-INDEX({range:units.break_even},{in:row})')],
         GR('What if', ('Studio, row 3', {'row': 3}), ('Cabin, row 8', {'row': 8}), ('Penthouse, row 11', {'row': 11}), ('Weekend lift 20 percent', {'lift': 0.2}), ('Round to 10', {'step': 10}))),
    TOOL('rate_grid', 'Rate and Occupancy Grid', 'Monthly revenue for a nightly rate and an occupancy',
         'Type a nightly rate, an occupancy, the nights in the month, the units and the costs; see the revenue and profit of one unit and of all units. The grid tries rate and occupancy together.', [
        I('rate', 'Nightly rate', 140), I('occ', 'Occupancy', 0.65, 'pct'), I('nights', 'Nights in the month', 30, 'int'), I('units', 'Units', 12, 'int'), I('fee', 'Platform fee', 0.12, 'pct'), I('var', 'Cost per booked night', 12)], [
        O('Booked nights of one unit', 'num', '{in:nights}*{in:occ}'), O('Room revenue of one unit', 'money', REV14), O('Room revenue of all units', 'money', REV14 + '*{in:units}'),
        O('Revenue per available night, RevPAR', 'money', '{in:rate}*{in:occ}'), O('Revenue after platform fee, one unit', 'money', REV14 + '*(1-{in:fee})'),
        O('Profit before fixed cost, one unit', 'money', REV14 + '*(1-{in:fee})-{in:nights}*{in:occ}*{in:var}'), O('Profit before fixed cost, all units', 'money', '{in:units}*(' + REV14 + '*(1-{in:fee})-{in:nights}*{in:occ}*{in:var})'),
        O('Revenue of all units over a year', 'money', REV14 + '*{in:units}*12'), O('Revenue for one more point of occupancy', 'money', '{in:rate}*{in:nights}*0.01*{in:units}'),
        O('Revenue for 5 more on the rate', 'money', '5*{in:nights}*{in:occ}*{in:units}')],
         GR('Rate and occupancy together', ('Rate 120, occupancy 60', {'rate': 120, 'occ': 0.6}), ('Rate 120, occupancy 80', {'rate': 120, 'occ': 0.8}), ('Rate 140, occupancy 60', {'rate': 140, 'occ': 0.6}), ('Rate 140, occupancy 80', {'rate': 140, 'occ': 0.8}),
            ('Rate 160, occupancy 60', {'rate': 160, 'occ': 0.6}), ('Rate 160, occupancy 80', {'rate': 160, 'occ': 0.8}), ('Rate 180, occupancy 50', {'rate': 180, 'occ': 0.5}), ('Rate 100, occupancy 90', {'rate': 100, 'occ': 0.9}))),
]
assert len(tools) == 14, len(tools)
