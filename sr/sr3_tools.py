"""Short-term rental host suite part 3: the 14 calculators."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr3_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def MXN(names, f='MAX'): return f + '(' + ','.join('{in:%s}' % n for n in names) + ')'

# 1 occupancy, ADR, RevPAR
AV1 = '({in:nights}-{in:blocked})'; OCC1 = 'IFERROR({in:sold}/%s,0)' % AV1; ADR1 = 'IFERROR({in:rev}/{in:sold},0)'; RP1 = 'IFERROR({in:rev}/%s,0)' % AV1
TRP = '({set:target_occupancy}*{set:target_adr})'
# 2 unit health
S2A = '40*MIN(1,{in:occ}/{set:target_occupancy})'; S2B = '25*MIN(1,{in:adr}/{set:target_adr})'; S2C = '20*MAX(0,MIN(1,({in:rating}-3)/({set:min_rating}-3)))'; S2D = '15*MAX(0,MIN(1,{in:margin}/{set:target_margin}))'
TOT2 = '(%s+%s+%s+%s)' % (S2A, S2B, S2C, S2D)
# 3 pace
PK3 = '({in:now}-{in:ago})'; GP3 = 'IFERROR({in:now}/{in:target}-1,0)'
MOVE3 = 'IF(%s<-0.15,-0.1,IF(%s<-{set:pace_tolerance},-0.05,IF(%s>0.15,0.08,IF(%s>{set:pace_tolerance},0.04,0))))' % (GP3, GP3, GP3, GP3)
# 5 trade-off
NR5 = '({in:rate}*(1-{in:cut}))'; BE5 = 'IFERROR({in:occ}*({in:rate}-{in:var})/(%s-{in:var}),0)' % NR5
PD5 = '((%s-{in:var})*{in:exp_occ}-({in:rate}-{in:var})*{in:occ})*{in:avail}' % NR5
# 6 season planner
MONTHS = ['m%d' % i for i in range(1, 13)]
MXM = MXN(MONTHS); MNM = MXN(MONTHS, 'MIN')
def PICK(f, op):
    s = '0'
    for i in range(12, 0, -1): s = 'IF({in:m%d}=%s,%d,%s)' % (i, f, i, s)
    return s
# 7 blocked cost
LOST7 = '({in:nights}*{in:occ}*{in:adr})'
PR7 = '({in:nights}*{in:occ}*({in:adr}*(1-{in:fee})-{in:var}))'
# 8 market
OI8 = 'IFERROR({in:occ}/{in:mocc},0)'; AI8 = 'IFERROR({in:adr}/{in:madr},0)'
# 11 yoy
NP11 = '(({in:n1}-{in:n0})*IFERROR({in:r0}/{in:n0},0))'; RP11 = '(IFERROR({in:r1}/{in:n1},0)-IFERROR({in:r0}/{in:n0},0))*{in:n1}'
# 12 weekday gap
WD = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
WE12 = '(({in:fri}+{in:sat})/2)'; WK12 = '(({in:mon}+{in:tue}+{in:wed}+{in:thu}+{in:sun})/5)'
def WDPICK(f):
    s = tok('wday', 'Sunday')
    for i in range(5, -1, -1): s = 'IF({in:%s}=%s,%s,%s)' % (WD[i], f, tok('wday', WDAY[i]), s)
    return s
# 13 lead time
# 14 grid
RP14 = '({in:adr}*{in:occ})'

tools = [
    TOOL('occ_calc', 'Occupancy ADR RevPAR', 'Occupancy, ADR and RevPAR of a unit or a month',
         'Type the nights, blocked nights, nights sold and room revenue; see occupancy, ADR (the average price of a night sold), RevPAR (revenue per available night) and the gap to target.', [
        I('nights', 'Nights in the period', 30, 'int'), I('blocked', 'Nights blocked', 2, 'int'), I('sold', 'Nights sold', 19, 'int'), I('rev', 'Room revenue', 2850)], [
        O('Available nights', 'int', AV1), O('Occupancy', 'pct', OCC1), O('ADR, the average price of a night sold', 'money', ADR1), O('RevPAR, revenue per available night', 'money', RP1),
        O('RevPAR check, occupancy times ADR', 'money', OCC1 + '*' + ADR1), O('Free nights', 'int', AV1 + '-{in:sold}'), O('Occupancy against the wanted occupancy, points', 'pct', OCC1 + '-{set:target_occupancy}'),
        O('ADR against the wanted ADR', 'pct', 'IFERROR(%s/{set:target_adr}-1,0)' % ADR1), O('Revenue at the wanted occupancy and ADR', 'money', AV1 + '*' + TRP), O('Revenue gap to the wanted figures', 'money', '{in:rev}-' + AV1 + '*' + TRP),
        O('Verdict', 'text', 'IF(%s>=%s*1.02,%s,IF(%s>=%s*0.98,%s,%s))' % (RP1, TRP, ck2('Ahead of target'), RP1, TRP, ck2('On the target'), ck2('Behind target')))],
         GR('What if', ('A busy month', {'sold': 27, 'rev': 4100}), ('A quiet month', {'sold': 11, 'rev': 1450}), ('Two more blocked nights', {'blocked': 4}), ('Same nights at a higher rate', {'rev': 3300}), ('A full month, no blocks', {'blocked': 0, 'sold': 24, 'rev': 3500}))),
    TOOL('health', 'Unit Health Score', 'Unit health score from occupancy, ADR, rating and margin',
         'Type the occupancy, ADR, review rating and profit margin of a unit; each is scored against your targets and added to a score out of 100, with the weakest part named.', [
        I('occ', 'Occupancy', 0.58, 'pct'), I('adr', 'ADR', 128), I('rating', 'Average rating, 1 to 5', 4.5, 'num'), I('margin', 'Profit margin on revenue', 0.12, 'pct')], [
        O('Occupancy score, of 40', 'num', S2A), O('ADR score, of 25', 'num', S2B), O('Rating score, of 20', 'num', S2C), O('Margin score, of 15', 'num', S2D), O('Health score, of 100', 'int', 'ROUND(%s,0)' % TOT2),
        O('Weakest part', 'text', 'IF(AND(%s/40<=%s/25,%s/40<=%s/20,%s/40<=%s/15),%s,IF(AND(%s/25<=%s/20,%s/25<=%s/15),%s,IF(%s/20<=%s/15,%s,%s)))' % (
            S2A, S2B, S2A, S2C, S2A, S2D, ck3('Occupancy'), S2B, S2C, S2B, S2D, ck3('ADR'), S2C, S2D, ck3('Rating'), ck3('Margin'))),
        O('Occupancy points to the target', 'pct', '{in:occ}-{set:target_occupancy}'), O('ADR against the target', 'pct', 'IFERROR({in:adr}/{set:target_adr}-1,0)'),
        O('Verdict', 'text', 'IF(%s>=75,%s,IF(%s>=50,%s,%s))' % (TOT2, ck2('Healthy unit'), TOT2, ck2('Watch the unit'), ck2('Weak unit')))],
         GR('What if', ('Strong unit', {'occ': 0.78, 'adr': 150, 'rating': 4.8, 'margin': 0.26}), ('Weak reviews', {'rating': 3.9}), ('Low occupancy', {'occ': 0.38}), ('Thin margin', {'margin': 0.02}), ('Cheap rate', {'adr': 98}))),
    TOOL('pace_check', 'Pace Check', 'Pace of a coming month and the price move to make',
         'Type the nights booked now, a month ago and the nights wanted on the books by now and by the end of the month; see the pickup, the gap, the projected nights and the price move to make.', [
        I('now', 'Nights booked now', 14, 'int'), I('ago', 'Nights booked a month ago', 9, 'int'), I('target', 'Nights wanted on the books by now', 16, 'int'), I('final', 'Nights wanted by the end', 22, 'int'),
        I('days', 'Days left to keep selling', 20, 'int'), I('rate', 'Rate listed now', 130)], [
        O('Nights picked up in a month', 'int', PK3), O('Gap to the target now', 'int', '{in:now}-{in:target}'), O('Share of the target', 'pct', 'IFERROR({in:now}/{in:target},0)'), O('Pickup per day', 'num', 'IFERROR(%s/30,0)' % PK3),
        O('Projected nights at the end', 'int', 'ROUND({in:now}+IFERROR(%s/30,0)*{in:days},0)' % PK3), O('Projected nights against the final target', 'int', 'ROUND({in:now}+IFERROR(%s/30,0)*{in:days},0)-{in:final}' % PK3),
        O('Nights still to sell', 'int', 'MAX(0,{in:final}-{in:now})'), O('Pickup needed per day', 'num', 'IFERROR(MAX(0,{in:final}-{in:now})/{in:days},0)'), O('Price move to make', 'pct', MOVE3), O('Rate after the move', 'money', 'ROUND({in:rate}*(1+%s),0)' % MOVE3),
        O('Verdict', 'text', 'IF(%s>{set:pace_tolerance},%s,IF(%s<-{set:pace_tolerance},%s,%s))' % (GP3, ck2('Ahead of target'), GP3, ck2('Behind target'), ck2('On the target')))],
         GR('What if', ('Well ahead of pace', {'now': 20}), ('Far behind pace', {'now': 8, 'ago': 6}), ('Slow pickup', {'ago': 13}), ('Little time left', {'days': 7}), ('A higher target', {'target': 20, 'final': 26}))),
    TOOL('occ_needed', 'Occupancy Needed', 'Occupancy needed to reach a revenue goal',
         'Type the revenue goal, the ADR you can expect and the nights available; see the occupancy needed, the ADR needed at your wanted occupancy and whether the goal is realistic.', [
        I('goal', 'Room revenue goal for the year', 32000), I('adr', 'ADR you can expect', 140), I('avail', 'Nights available in the year', 350, 'int')], [
        O('Nights to sell', 'int', 'ROUNDUP(IFERROR({in:goal}/{in:adr},0),0)'), O('Occupancy needed', 'pct', 'IFERROR({in:goal}/({in:adr}*{in:avail}),0)'), O('Occupancy needed against the wanted occupancy', 'pct', 'IFERROR({in:goal}/({in:adr}*{in:avail}),0)-{set:target_occupancy}'),
        O('ADR needed at the wanted occupancy', 'money', 'IFERROR({in:goal}/({set:target_occupancy}*{in:avail}),0)'), O('Revenue at the wanted occupancy and this ADR', 'money', '{in:adr}*{in:avail}*{set:target_occupancy}'),
        O('Gap to the goal', 'money', '{in:goal}-{in:adr}*{in:avail}*{set:target_occupancy}'), O('Nights to sell each month', 'num', 'IFERROR({in:goal}/{in:adr}/12,0)'),
        O('Verdict', 'text', 'IF(IFERROR({in:goal}/({in:adr}*{in:avail}),0)<={set:target_occupancy},%s,IF(IFERROR({in:goal}/({in:adr}*{in:avail}),0)<={set:target_occupancy}+0.1,%s,%s))' % (ck2('Goal is realistic'), ck2('Goal is a stretch'), ck2('Goal is unrealistic')))],
         GR('What if', ('A higher goal', {'goal': 42000}), ('A higher ADR', {'adr': 170}), ('A lower ADR', {'adr': 115}), ('A small unit with few nights', {'avail': 300, 'goal': 22000}), ('A modest goal', {'goal': 24000}))),
    TOOL('trade_off', 'Rate or Occupancy Trade-off', 'Price cut against the extra occupancy it needs',
         'Type the rate, the occupancy, the price cut and the cost of each night sold; see the occupancy you need to earn the same profit, and whether the extra occupancy you expect pays for the cut.', [
        I('rate', 'Current rate', 140), I('occ', 'Current occupancy', 0.62, 'pct'), I('cut', 'Price cut', 0.08, 'pct'), I('var', 'Cost of each night sold, cleaning and supplies', 14), I('exp_occ', 'Occupancy you expect after the cut', 0.7, 'pct'),
        I('avail', 'Nights available in the month', 30, 'int')], [
        O('Rate after the cut', 'money', NR5), O('Revenue now', 'money', '{in:rate}*{in:occ}*{in:avail}'), O('Occupancy to keep the same revenue', 'pct', 'IFERROR({in:occ}/(1-{in:cut}),0)'),
        O('Occupancy to keep the same profit', 'pct', BE5), O('Extra occupancy needed, points', 'pct', BE5 + '-{in:occ}'), O('Extra nights needed in the month', 'num', '(%s-{in:occ})*{in:avail}' % BE5),
        O('Revenue after the cut at the expected occupancy', 'money', NR5 + '*{in:exp_occ}*{in:avail}'), O('Profit change in the month', 'money', PD5),
        O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (PD5, ck2('Cut is worth it'), ck2('Cut loses money')))],
         GR('What if', ('A deeper cut', {'cut': 0.15}), ('A small cut', {'cut': 0.04}), ('A weak response', {'exp_occ': 0.64}), ('A strong response', {'exp_occ': 0.82}), ('Costly cleaning', {'var': 30}))),
    TOOL('season_plan', 'Seasonality Planner', 'Best and worst months and an occupancy target for each month',
         'Type the occupancy of each month from last year; see the best and worst months, the spread, the months under your wanted occupancy and a target for the best and the worst month.', [
        I('m1', 'January occupancy', 0.42, 'pct'), I('m2', 'February occupancy', 0.46, 'pct'), I('m3', 'March occupancy', 0.55, 'pct'), I('m4', 'April occupancy', 0.62, 'pct'), I('m5', 'May occupancy', 0.68, 'pct'), I('m6', 'June occupancy', 0.75, 'pct'),
        I('m7', 'July occupancy', 0.86, 'pct'), I('m8', 'August occupancy', 0.9, 'pct'), I('m9', 'September occupancy', 0.72, 'pct'), I('m10', 'October occupancy', 0.6, 'pct'), I('m11', 'November occupancy', 0.5, 'pct'), I('m12', 'December occupancy', 0.52, 'pct'),
        I('uplift', 'Growth you want on last year', 0.05, 'pct'), I('cap', 'Highest occupancy to plan for', 0.92, 'pct')], [
        O('Average occupancy of the year', 'pct', 'AVERAGE(%s)' % ','.join('{in:%s}' % m for m in MONTHS)), O('Best month, number 1 to 12', 'int', PICK(MXM, 'max')), O('Best month occupancy', 'pct', MXM),
        O('Worst month, number 1 to 12', 'int', PICK(MNM, 'min')), O('Worst month occupancy', 'pct', MNM), O('Spread between best and worst, points', 'pct', MXM + '-' + MNM),
        O('Months under the wanted occupancy', 'int', '+'.join('({in:%s}<{set:target_occupancy})' % m for m in MONTHS)), O('Target for the best month', 'pct', 'MIN({in:cap},%s*(1+{in:uplift}))' % MXM),
        O('Target for the worst month', 'pct', 'MIN({in:cap},%s*(1+2*{in:uplift}))' % MNM), O('Target for the average month', 'pct', 'MIN({in:cap},AVERAGE(%s)*(1+{in:uplift}))' % ','.join('{in:%s}' % m for m in MONTHS))],
         GR('What if', ('Growth of 10 percent', {'uplift': 0.1}), ('A flat plan', {'uplift': 0}), ('A weak winter', {'m1': 0.3, 'm2': 0.32, 'm12': 0.4}), ('A stronger summer', {'m7': 0.95, 'm8': 0.96}), ('A lower cap', {'cap': 0.85}))),
    TOOL('blocked_cost', 'Blocked Night Cost', 'Revenue and profit lost by blocking nights',
         'Type the nights blocked, the ADR, the occupancy and the costs; see the nights you would probably have sold, the revenue and profit lost and whether the block is costly.', [
        I('nights', 'Nights blocked', 6, 'int'), I('adr', 'ADR of the unit', 135), I('occ', 'Occupancy of the unit', 0.68, 'pct'), I('fee', 'Platform fee', 0.13, 'pct'), I('var', 'Cost of each night sold, cleaning and supplies', 14)], [
        O('Nights you would probably have sold', 'num', '{in:nights}*{in:occ}'), O('Revenue lost', 'money', LOST7), O('Platform fee you do not pay', 'money', LOST7 + '*{in:fee}'), O('Cost you do not pay', 'money', '{in:nights}*{in:occ}*{in:var}'),
        O('Profit lost', 'money', PR7), O('Profit lost per blocked night', 'money', 'IFERROR(%s/{in:nights},0)' % PR7), O('Share of a normal month blocked', 'pct', '{in:nights}/30'),
        O('Profit of a normal month', 'money', '30*{in:occ}*({in:adr}*(1-{in:fee})-{in:var})'), O('Verdict', 'text', 'IF(%s>=0.15*30*{in:occ}*({in:adr}*(1-{in:fee})-{in:var}),%s,%s)' % (PR7, ck2('Block is costly'), ck3('Block is acceptable')))],
         GR('What if', ('A long renovation', {'nights': 14}), ('One night for an inspection', {'nights': 1}), ('A busy unit', {'occ': 0.85, 'adr': 160}), ('A quiet unit', {'occ': 0.4}), ('Direct bookings, low fee', {'fee': 0.03}))),
    TOOL('market_comp', 'Market Comparison', 'Our occupancy and ADR against the market',
         'Type your occupancy and ADR and those of comparable listings; see the occupancy, ADR and RevPAR indexes, where you win or lose and whether you hold a fair share of the market.', [
        I('occ', 'Our occupancy', 0.66, 'pct'), I('adr', 'Our ADR', 132), I('mocc', 'Market occupancy', 0.62, 'pct'), I('madr', 'Market ADR', 138)], [
        O('Occupancy index, 1 is the market', 'num', OI8), O('ADR index, 1 is the market', 'num', AI8), O('Our RevPAR', 'money', '{in:occ}*{in:adr}'), O('Market RevPAR', 'money', '{in:mocc}*{in:madr}'),
        O('RevPAR index, 1 is the market', 'num', 'IFERROR({in:occ}*{in:adr}/({in:mocc}*{in:madr}),0)'), O('RevPAR gap per available night', 'money', '{in:occ}*{in:adr}-{in:mocc}*{in:madr}'),
        O('Where we do better', 'text', 'IF(%s>=%s,%s,%s)' % (OI8, AI8, cb('Occupancy leads'), cb('Rate leads'))), O('Where we do worse', 'text', 'IF(%s<%s,%s,%s)' % (OI8, AI8, cb('Occupancy lags'), cb('Rate lags'))),
        O('Verdict', 'text', 'IF(IFERROR({in:occ}*{in:adr}/({in:mocc}*{in:madr}),0)>1+{set:market_tolerance},%s,IF(IFERROR({in:occ}*{in:adr}/({in:mocc}*{in:madr}),0)<1-{set:market_tolerance},%s,%s))' % (ck2('Ahead of the market'), ck2('Behind the market'), ck2('Fair share of the market')))],
         GR('What if', ('A stronger market', {'mocc': 0.75, 'madr': 150}), ('Our rate is higher', {'adr': 150}), ('Our occupancy is lower', {'occ': 0.5}), ('A cheap market', {'madr': 105}), ('Same as the market', {'occ': 0.62, 'adr': 138}))),
    TOOL('unit_compare', 'Unit Comparison', 'Two units side by side: occupancy, ADR, RevPAR and profit',
         'Type the available nights, nights sold, room revenue and costs of two units over the same period; see their occupancy, ADR, RevPAR and profit per night sold, and which unit is stronger.', [
        I('av_a', 'Unit A available nights', 360, 'int'), I('so_a', 'Unit A nights sold', 250, 'int'), I('rv_a', 'Unit A room revenue', 36500), I('co_a', 'Unit A costs', 24000),
        I('av_b', 'Unit B available nights', 360, 'int'), I('so_b', 'Unit B nights sold', 205, 'int'), I('rv_b', 'Unit B room revenue', 33800), I('co_b', 'Unit B costs', 26500)], [
        O('Unit A occupancy', 'pct', 'IFERROR({in:so_a}/{in:av_a},0)'), O('Unit B occupancy', 'pct', 'IFERROR({in:so_b}/{in:av_b},0)'), O('Unit A ADR', 'money', 'IFERROR({in:rv_a}/{in:so_a},0)'), O('Unit B ADR', 'money', 'IFERROR({in:rv_b}/{in:so_b},0)'),
        O('Unit A RevPAR', 'money', 'IFERROR({in:rv_a}/{in:av_a},0)'), O('Unit B RevPAR', 'money', 'IFERROR({in:rv_b}/{in:av_b},0)'), O('Unit A profit per night sold', 'money', 'IFERROR(({in:rv_a}-{in:co_a})/{in:so_a},0)'),
        O('Unit B profit per night sold', 'money', 'IFERROR(({in:rv_b}-{in:co_b})/{in:so_b},0)'), O('Profit difference, A less B', 'money', '({in:rv_a}-{in:co_a})-({in:rv_b}-{in:co_b})'),
        O('Verdict', 'text', 'IF(ABS(({in:rv_a}-{in:co_a})-({in:rv_b}-{in:co_b}))<0.02*MAX({in:rv_a},{in:rv_b}),%s,IF(({in:rv_a}-{in:co_a})>({in:rv_b}-{in:co_b}),%s,%s))' % (ck2('Units are level'), ck2('Unit A is stronger'), ck2('Unit B is stronger')))],
         GR('What if', ('B loses money', {'co_b': 36000}), ('B catches up', {'so_b': 250, 'rv_b': 37000}), ('A has higher costs', {'co_a': 34000}), ('Equal units', {'so_b': 250, 'rv_b': 36500, 'co_b': 24000}), ('B is a small unit', {'av_b': 300, 'so_b': 190, 'rv_b': 22000, 'co_b': 15000}))),
    TOOL('weak_diag', 'Weak Unit Diagnosis', 'Likely cause of a weak unit and the fix to try first',
         'Type occupancy, rate against the market, rating, lead time, open window and weekday and weekend occupancy; see the likely cause, the fix to try and the revenue at stake.', [
        I('occ', 'Occupancy', 0.48, 'pct'), I('vs_mkt', 'Our ADR against the market ADR', 0.02, 'pct'), I('rating', 'Average rating, 1 to 5', 4.5, 'num'), I('lead', 'Average lead time in days', 16, 'int'), I('window', 'Days ahead that dates are open', 120, 'int'),
        I('wk_occ', 'Weekday occupancy', 0.33, 'pct'), I('we_occ', 'Weekend occupancy', 0.78, 'pct'), I('avail', 'Nights available in the month', 30, 'int'), I('adr', 'ADR', 128)], [
        O('Occupancy points under the target', 'pct', '{set:target_occupancy}-{in:occ}'),
        O('Likely cause', 'text', 'IF({in:occ}>={set:target_occupancy},%s,IF({in:vs_mkt}>0.05,%s,IF({in:rating}<{set:min_rating},%s,IF({in:window}<3*{in:lead},%s,IF({in:we_occ}-{in:wk_occ}>0.2,%s,%s)))))' % (
            tok('cause', 'Unit is healthy'), tok('cause', 'Price too high'), tok('cause', 'Weak reviews'), tok('cause', 'Short booking window'), tok('cause', 'Too few weekday nights'), tok('cause', 'Late bookings'))),
        O('Fix to try first', 'text', 'IF({in:occ}>={set:target_occupancy},%s,IF({in:vs_mkt}>0.05,%s,IF({in:rating}<{set:min_rating},%s,IF({in:window}<3*{in:lead},%s,IF({in:we_occ}-{in:wk_occ}>0.2,%s,%s)))))' % (
            tok('fix', 'Keep the current plan'), tok('fix', 'Lower the rate on weekdays'), tok('fix', 'Fix the cleaning and the complaints'), tok('fix', 'Open dates further ahead'), tok('fix', 'Add midweek offers'), tok('fix', 'Cut the minimum stay'))),
        O('Nights to fill to reach the target', 'int', 'MAX(0,ROUND(({set:target_occupancy}-{in:occ})*{in:avail},0))'), O('Revenue at stake in the month', 'money', 'MAX(0,({set:target_occupancy}-{in:occ})*{in:avail}*{in:adr})'),
        O('Rating against the minimum', 'num', '{in:rating}-{set:min_rating}'), O('Weekend less weekday occupancy, points', 'pct', '{in:we_occ}-{in:wk_occ}'), O('Open window against three times the lead time, days', 'int', '{in:window}-3*{in:lead}')],
         GR('What if', ('Priced too high', {'vs_mkt': 0.12}), ('Weak reviews', {'rating': 3.9}), ('Short booking window', {'window': 40}), ('Healthy unit', {'occ': 0.72}), ('Weekday gap', {'we_occ': 0.9, 'wk_occ': 0.3}))),
    TOOL('yoy_change', 'Year-on-Year Change', 'Change in nights, ADR and revenue against last year',
         'Type the nights sold and the room revenue this year and a year earlier; see the change in nights, ADR and revenue, how much came from more nights and how much from the rate, and what drove the change.', [
        I('n1', 'Nights sold this year', 238, 'int'), I('n0', 'Nights sold last year', 221, 'int'), I('r1', 'Room revenue this year', 31600), I('r0', 'Room revenue last year', 29800)], [
        O('Change in nights', 'pct', 'IFERROR({in:n1}/{in:n0}-1,0)'), O('ADR this year', 'money', 'IFERROR({in:r1}/{in:n1},0)'), O('ADR last year', 'money', 'IFERROR({in:r0}/{in:n0},0)'), O('Change in ADR', 'pct', 'IFERROR(({in:r1}/{in:n1})/({in:r0}/{in:n0})-1,0)'),
        O('Change in revenue', 'pct', 'IFERROR({in:r1}/{in:r0}-1,0)'), O('Change in revenue, amount', 'money', '{in:r1}-{in:r0}'), O('Revenue from more or fewer nights', 'money', NP11), O('Revenue from the rate', 'money', RP11),
        O('Verdict', 'text', 'IF(AND({in:n1}<{in:n0},IFERROR({in:r1}/{in:n1},0)<IFERROR({in:r0}/{in:n0},0)),%s,IF(%s>%s,%s,%s))' % (ck2('Both fell'), RP11, NP11, ck2('Growth comes from rate'), ck2('Growth comes from nights')))],
         GR('What if', ('More nights, lower rate', {'n1': 262, 'r1': 29400}), ('Higher rate, fewer nights', {'n1': 205, 'r1': 32500}), ('Both fell', {'n1': 196, 'r1': 24500}), ('Strong growth', {'n1': 262, 'r1': 38500}), ('Flat year', {'n1': 221, 'r1': 29800}))),
    TOOL('weekday_gap', 'Weekday Gap Finder', 'The cheapest nights to fill and what they are worth',
         'Type the occupancy of each weekday and the rate for the weakest night; see the weekend and weekday averages, the weakest and strongest night, the nights a year to fill and the revenue they are worth.', [
        I('mon', 'Monday occupancy', 0.38, 'pct'), I('tue', 'Tuesday occupancy', 0.36, 'pct'), I('wed', 'Wednesday occupancy', 0.4, 'pct'), I('thu', 'Thursday occupancy', 0.5, 'pct'), I('fri', 'Friday occupancy', 0.82, 'pct'),
        I('sat', 'Saturday occupancy', 0.88, 'pct'), I('sun', 'Sunday occupancy', 0.55, 'pct'), I('rate', 'Rate for the weakest night', 110)], [
        O('Weekend occupancy, Friday and Saturday', 'pct', WE12), O('Weekday occupancy, other nights', 'pct', WK12), O('Gap between weekend and weekday, points', 'pct', WE12 + '-' + WK12), O('Weakest night', 'text', WDPICK(MXN(WD, 'MIN'))),
        O('Weakest night occupancy', 'pct', MXN(WD, 'MIN')), O('Strongest night', 'text', WDPICK(MXN(WD))), O('Strongest night occupancy', 'pct', MXN(WD)), O('Weakest nights to fill in a year at the wanted occupancy', 'int', 'MAX(0,ROUND(({set:target_occupancy}-%s)*52,0))' % MXN(WD, 'MIN')),
        O('Revenue those nights are worth', 'money', 'MAX(0,ROUND(({set:target_occupancy}-%s)*52,0))*{in:rate}' % MXN(WD, 'MIN')),
        O('Verdict', 'text', 'IF(%s-%s>0.25,%s,IF(%s-%s>0.05,%s,%s))' % (WE12, WK12, ck2('Fill the weekday nights'), WK12, WE12, ck2('Weekends are weak'), ck2('Evenly booked')))],
         GR('What if', ('Weekends weak', {'fri': 0.5, 'sat': 0.55}), ('Evenly booked', {'mon': 0.65, 'tue': 0.65, 'wed': 0.66, 'thu': 0.68, 'sun': 0.66, 'fri': 0.7, 'sat': 0.72}), ('Quiet Tuesdays', {'tue': 0.2}), ('A higher rate for the weakest night', {'rate': 140}), ('Strong Mondays', {'mon': 0.85}))),
    TOOL('lead_check', 'Lead Time Check', 'How far ahead to open dates for the lead time of your guests',
         'Type the average lead time, how far ahead dates are open, the minimum stay, the typical stay and the share of last-minute bookings; see the window to open and whether to open dates earlier.', [
        I('lead', 'Average lead time in days', 18, 'int'), I('window', 'Days ahead that dates are open now', 60, 'int'), I('minstay', 'Minimum stay in nights', 2, 'int'), I('stay', 'Typical stay in nights', 3.4, 'num'), I('late', 'Share of bookings made within a week', 0.22, 'pct')], [
        O('Window to keep open, days', 'int', 'ROUND(4*{in:lead},0)'), O('Open dates until', 'date', '{today}+ROUND(4*{in:lead},0)'), O('Window against the window now, days', 'int', 'ROUND(4*{in:lead},0)-{in:window}'),
        O('Minimum stay against the typical stay', 'pct', 'IFERROR({in:minstay}/{in:stay},0)'), O('Lead time as a share of the window now', 'pct', 'IFERROR({in:lead}/{in:window},0)'),
        O('Last-minute bookings, share', 'pct', '{in:late}'), O('Days of a free calendar to cover with offers', 'int', 'ROUND({in:lead}*{in:late},0)'),
        O('Verdict', 'text', 'IF({in:window}<3*{in:lead},%s,IF({in:window}>12*{in:lead},%s,%s))' % (ck2('Open dates earlier'), ck2('Shorten the window'), ck2('Keep the window')))],
         GR('What if', ('Short window', {'window': 30}), ('Long window', {'window': 330}), ('Guests book very early', {'lead': 60}), ('Guests book late', {'lead': 6, 'late': 0.5}), ('A longer minimum stay', {'minstay': 4}))),
    TOOL('rate_grid', 'Occupancy and ADR Grid', 'RevPAR for an occupancy and an ADR together',
         'Type an ADR, an occupancy, the nights available and the units; see RevPAR, room revenue of one unit and all units, and what one more point of occupancy or five more on ADR is worth.', [
        I('adr', 'ADR', 140), I('occ', 'Occupancy', 0.65, 'pct'), I('avail', 'Nights available in a month', 30, 'int'), I('units', 'Units', 12, 'int')], [
        O('RevPAR, revenue per available night', 'money', RP14), O('Room revenue of one unit in a month', 'money', RP14 + '*{in:avail}'), O('Room revenue of all units in a month', 'money', RP14 + '*{in:avail}*{in:units}'),
        O('Room revenue of all units in a year', 'money', RP14 + '*{in:avail}*{in:units}*12'), O('Target RevPAR', 'money', TRP), O('RevPAR against the target', 'money', RP14 + '-' + TRP),
        O('ADR needed at this occupancy for the target', 'money', 'IFERROR(%s/{in:occ},0)' % TRP), O('Occupancy needed at this ADR for the target', 'pct', 'IFERROR(%s/{in:adr},0)' % TRP),
        O('Revenue of one more point of occupancy, all units', 'money', '{in:adr}*{in:avail}*0.01*{in:units}'), O('Revenue of five more on the ADR, all units', 'money', '5*{in:avail}*{in:occ}*{in:units}')],
         GR('Occupancy and ADR together', ('ADR 120, occupancy 60', {'adr': 120, 'occ': 0.6}), ('ADR 120, occupancy 80', {'adr': 120, 'occ': 0.8}), ('ADR 140, occupancy 60', {'adr': 140, 'occ': 0.6}), ('ADR 140, occupancy 80', {'adr': 140, 'occ': 0.8}),
            ('ADR 160, occupancy 60', {'adr': 160, 'occ': 0.6}), ('ADR 160, occupancy 80', {'adr': 160, 'occ': 0.8}), ('ADR 180, occupancy 50', {'adr': 180, 'occ': 0.5}), ('ADR 100, occupancy 90', {'adr': 100, 'occ': 0.9}))),
]
assert len(tools) == 14, len(tools)
for _t in tools: assert len(_t['hint']) <= 200 and len(_t['title']) <= 60, (_t['key'], len(_t['hint']), len(_t['title']))
