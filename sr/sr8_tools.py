"""Short-term rental host suite part 8: the 14 calculators."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr8_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def V(label, f): return O(label, 'text', f)

# 1 unit profit and loss
COST1 = '({in:fees}+{in:cleaning}+{in:supplies}+{in:maint}+{in:rent}+{in:util}+{in:other})'; PROF1 = '({in:rev}-%s)' % COST1
# 2 break-even occupancy
KEPT2 = '({in:rate}*(1-{in:fee})-{in:var})'; BEO2 = 'IF(%s>0,{in:fixed}/(%s*30.4),9.99)' % (KEPT2, KEPT2)
# 3 break-even rate
BER3 = '(({in:fixed}/({in:nights}*{in:occ})+{in:var})/(1-{in:fee}))'; TGR3 = '(({in:fixed}/({in:nights}*{in:occ})+{in:var})/(1-{in:fee}-{in:margin}))'
# 4 cash forecast
MON4 = '({in:lump}+{in:owners}+{in:draw}+{in:tax})'; NET4 = '(4.33*({in:pay}-{in:costs})-%s)' % MON4
B1 = '({in:open}+%s)' % NET4; B2 = '({in:open}+2*%s)' % NET4; B3 = '({in:open}+3*%s)' % NET4
LOW4 = 'MIN({in:open},%s,%s,%s)' % (B1, B2, B3)
# 5 floor warning
OUT5 = '({in:costs}/4.33)'
# 6 safe draw
A6 = '({in:profit}*(1-{in:taxpct}))'; B6 = '({in:cash}-{in:floor}-{in:next})'; SAFE6 = 'MAX(0,MIN(%s,%s))' % (A6, B6)
# 7 tax set-aside
HOLD7 = '({in:profit}*{in:pct})'; HELD7 = '({in:set}-{in:paid})'
# 8 payout gap
DAY8 = '({in:costs_month}/30)'; WIN8 = '(%s*{in:delay})' % DAY8; NEED8 = 'MAX(0,{in:due}+%s-{in:payouts}-{in:cash})' % WIN8
# 9 new unit
NIGHT9 = '(365*{in:occ})'; REV9 = '(%s*{in:rate})' % NIGHT9; PROF9 = '(%s*(1-{in:fee})-%s*{in:var}-12*({in:rent}+{in:bills}))' % (REV9, NIGHT9)
# 10 keep or drop
PAFT10 = '({in:profit}+{in:rev}*{in:rise}*(1-{in:fee}))'
# 11 rate rise
KEPT11C = '({in:cur}*(1-{in:fee})-{in:var})'; NEW11 = '({in:cur}*(1+{in:rise}))'; KEPT11N = '(%s*(1-{in:fee})-{in:var})' % NEW11
PB11 = '(%s*365*{in:occ}-{in:fixed}*12)' % KEPT11C; PA11 = '(%s*365*({in:occ}-{in:loss})-{in:fixed}*12)' % KEPT11N
# 12 direct saving
FNOW12 = '({in:gross}*((1-{in:share})*{in:pfee}+{in:share}*{in:dfee}))'; FTGT12 = '({in:gross}*((1-{in:target})*{in:pfee}+{in:target}*{in:dfee}))'
# 13 cost per night
CL13 = '({in:clean}/{in:stay})'; SU13 = '({in:supp}/{in:stay})'; UT13 = '({in:util}/{in:booked})'; MA13 = '({in:maint}/{in:booked})'; FE13 = '({in:rate}*{in:fee})'
TOT13 = '(%s+%s+%s+%s+%s)' % (CL13, SU13, UT13, MA13, FE13)
# 14 grid
REV14 = '({in:rate}*{in:nights}*{in:occ})'; PRO14 = '(%s*(1-{in:fee})-{in:nights}*{in:occ}*{in:var}-{in:fixed})' % REV14

tools = [
    TOOL('unit_pl', 'Unit Profit and Loss', 'Profit and margin of one unit for a month or a year',
         'Type the revenue and each cost of one unit and the nights; see the profit, the margin, the profit per night, the cost shares and whether the unit meets your wanted margin.', [
        I('rev', 'Revenue', 3200), I('fees', 'Platform fees', 440), I('cleaning', 'Cleaning', 330), I('supplies', 'Supplies', 70), I('maint', 'Maintenance', 120), I('rent', 'Rent or loan payment', 1150),
        I('util', 'Utilities and internet', 180), I('other', 'Other costs', 40), I('nights', 'Nights booked', 24, 'int'), I('avail', 'Nights available', 30, 'int')], [
        O('Total costs', 'money', COST1), O('Profit', 'money', PROF1), O('Margin', 'pct', 'IFERROR(%s/{in:rev},0)' % PROF1), O('Wanted margin', 'pct', '{set:target_margin}'),
        O('Profit per night booked', 'money', 'IFERROR(%s/{in:nights},0)' % PROF1), O('Cost per night booked', 'money', 'IFERROR(%s/{in:nights},0)' % COST1), O('Occupancy', 'pct', 'IFERROR({in:nights}/{in:avail},0)'),
        O('Platform fees share of revenue', 'pct', 'IFERROR({in:fees}/{in:rev},0)'), O('Rent share of revenue', 'pct', 'IFERROR({in:rent}/{in:rev},0)'), O('Revenue needed for the wanted margin', 'money', 'IFERROR(%s/(1-{set:target_margin}),0)' % COST1),
        V('Verdict', 'IF(%s<0,%s,IF(IFERROR(%s/{in:rev},0)<{set:target_margin},%s,%s))' % (PROF1, ck2('Loss'), PROF1, ck2('Review the unit'), ck2('Profit')))],
         GR('What if', ('Quiet month, revenue 1,900', {'rev': 1900, 'fees': 260, 'cleaning': 190, 'nights': 14}), ('Peak month, revenue 5,200', {'rev': 5200, 'fees': 720, 'cleaning': 450, 'nights': 28}),
            ('Studio that loses money', {'rev': 1100, 'fees': 150, 'cleaning': 140, 'rent': 1180, 'nights': 17}), ('Owned unit with no rent', {'rev': 4100, 'rent': 0, 'fees': 560, 'nights': 25}), ('Rent rises by 150', {'rent': 1300}))),
    TOOL('be_occ', 'Break-Even Occupancy', 'Occupancy at which a unit stops losing money',
         'Type the fixed cost of a month, what a night earns, the cost of a booked night and the platform fee share; see the break-even occupancy, the cushion over today and the profit at today\'s occupancy.', [
        I('fixed', 'Fixed cost per month', 1400), I('rate', 'Earned per night', 150), I('var', 'Cost per booked night', 28), I('fee', 'Platform fee share', 0.14, 'pct'), I('occ', 'Occupancy now', 0.6, 'pct')], [
        O('Kept per night after fee and cost', 'money', KEPT2), O('Break-even nights per month', 'num', 'IF(%s>0,{in:fixed}/%s,0)' % (KEPT2, KEPT2)), O('Break-even occupancy', 'pct', BEO2),
        O('Cushion over break-even', 'pct', '{in:occ}-' + BEO2), O('Nights booked now, a 30 day month', 'num', '30*{in:occ}'), O('Profit at the occupancy now', 'money', '30*{in:occ}*%s-{in:fixed}' % KEPT2),
        O('Profit at 10 points more occupancy', 'money', '30*({in:occ}+0.1)*%s-{in:fixed}' % KEPT2), O('Break-even occupancy with 10 percent higher rate', 'pct', 'IF({in:rate}*1.1*(1-{in:fee})-{in:var}>0,{in:fixed}/(({in:rate}*1.1*(1-{in:fee})-{in:var})*30.4),9.99)'),
        V('Verdict', 'IF(%s>1,%s,IF({in:occ}>=%s,%s,%s))' % (BEO2, cf('Cannot break even'), BEO2, cf('Above break-even'), cf('Below break-even')))],
         GR('What if', ('Studio at a low rate', {'fixed': 1355, 'rate': 80, 'var': 24, 'occ': 0.41}), ('Owned house', {'fixed': 2100, 'rate': 235, 'var': 38, 'occ': 0.62}), ('Managed unit, no rent', {'fixed': 280, 'rate': 190, 'var': 30, 'occ': 0.66}),
            ('Higher platform fees', {'fee': 0.2}), ('Busy unit at 80 percent', {'occ': 0.8}))),
    TOOL('be_rate', 'Break-Even Rate', 'Nightly rate at zero profit and at your wanted margin',
         'Type the fixed cost of a month, the expected occupancy, the nights, the cost of a booked night and the fee; see the earning per night for zero profit and for your wanted margin.', [
        I('fixed', 'Fixed cost per month', 1400), I('occ', 'Expected occupancy', 0.65, 'pct'), I('nights', 'Nights in the month', 30, 'int'), I('var', 'Cost per booked night', 28), I('fee', 'Platform fee share', 0.14, 'pct'),
        I('margin', 'Wanted margin', 0.2, 'pct'), I('now', 'Earning per night now', 140)], [
        O('Booked nights', 'num', '{in:nights}*{in:occ}'), O('Break-even rate, zero profit', 'money', BER3), O('Rate for the wanted margin', 'money', TGR3), O('Rate now against break-even', 'money', '{in:now}-' + BER3),
        O('Rate now against the margin rate', 'money', '{in:now}-' + TGR3), O('Profit a month at the rate now', 'money', '{in:nights}*{in:occ}*({in:now}*(1-{in:fee})-{in:var})-{in:fixed}'),
        O('Profit a month at the margin rate', 'money', '{in:nights}*{in:occ}*(%s*(1-{in:fee})-{in:var})-{in:fixed}' % TGR3), O('Rise needed from the rate now', 'pct', 'IFERROR(%s/{in:now}-1,0)' % TGR3),
        V('Verdict', 'IF({in:now}<%s,%s,IF({in:now}<%s,%s,%s))' % (BER3, ck2('Raise the rate'), TGR3, ck2('Fix the rate first'), ck2('Hold the rate')))],
         GR('What if', ('Occupancy 50 percent', {'occ': 0.5}), ('Occupancy 80 percent', {'occ': 0.8}), ('Studio, fixed cost 1,355', {'fixed': 1355, 'var': 24, 'now': 66}), ('Margin 30 percent', {'margin': 0.3}), ('Fee 20 percent', {'fee': 0.2}))),
    TOOL('cash13', '13-Week Cash Forecast', 'Cash in three months from today',
         'Type your cash now, the weekly payouts and costs and the monthly lump costs; see the balance after each month, the lowest balance, the weeks before you reach the floor and the gap to it.', [
        I('open', 'Cash now', 74000), I('pay', 'Payouts per week', 5400), I('costs', 'Running costs per week', 2100), I('lump', 'Rent and bills per month', 11200), I('owners', 'Owner payments per month', 9500),
        I('draw', 'Owner draw per month', 7000), I('tax', 'Local tax per month', 1000)], [
        O('Net per week before the monthly costs', 'money', '{in:pay}-{in:costs}'), O('Monthly costs paid out', 'money', MON4), O('Net per month', 'money', NET4), O('Balance after month 1', 'money', B1), O('Balance after month 2', 'money', B2),
        O('Balance after month 3, week 13', 'money', B3), O('Lowest balance', 'money', LOW4), O('Cash floor', 'money', '{set:cash_floor}'), O('Gap between the lowest balance and the floor', 'money', LOW4 + '-{set:cash_floor}'),
        O('Weeks until the floor is reached', 'num', 'IF(%s>=0,99,MAX(0,({in:open}-{set:cash_floor})/(-%s)*4.33))' % (NET4, NET4)),
        V('Verdict', 'IF(%s<{set:cash_floor},%s,IF(%s<2*{set:cash_floor},%s,%s))' % (LOW4, ck2('Cash is below the floor'), LOW4, ck2('Cash is tight'), ck2('Cash is safe')))],
         GR('What if', ('Slow winter, payouts 3,800', {'pay': 3800}), ('Draw cut to 4,000', {'draw': 4000}), ('Low cash start, 30,000', {'open': 30000}), ('Big repair month, costs 3,200 a week', {'costs': 3200}), ('Strong season, payouts 8,500', {'pay': 8500}))),
    TOOL('floor_warn', 'Cash Floor Warning', 'Weeks of cover and the gap to your cash floor',
         'Type the cash balance, the costs of the next 30 days and the money you expect in; see the weeks of cover, the balance in 30 days and the gap to your floor.', [
        I('balance', 'Cash balance now', 31000), I('costs', 'Costs in the next 30 days', 24000), I('inflow', 'Money expected in the next 30 days', 21000)], [
        O('Costs per week', 'money', OUT5), O('Weeks of cover', 'num', 'IFERROR({in:balance}/%s,0)' % OUT5), O('Balance in 30 days', 'money', '{in:balance}+{in:inflow}-{in:costs}'), O('Cash floor', 'money', '{set:cash_floor}'),
        O('Gap to the floor now', 'money', '{in:balance}-{set:cash_floor}'), O('Gap to the floor in 30 days', 'money', '{in:balance}+{in:inflow}-{in:costs}-{set:cash_floor}'),
        O('Extra money needed to stay above the floor', 'money', 'MAX(0,{set:cash_floor}-({in:balance}+{in:inflow}-{in:costs}))'),
        V('Verdict', 'IF({in:balance}+{in:inflow}-{in:costs}<{set:cash_floor},%s,IF({in:balance}+{in:inflow}-{in:costs}<2*{set:cash_floor},%s,%s))' % (ck2('Cash is below the floor'), ck2('Cash is tight'), ck2('Cash is safe')))],
         GR('What if', ('Comfortable cash', {'balance': 60000}), ('Heavy cost month', {'costs': 36000}), ('Late payouts', {'inflow': 9000}), ('Low cash', {'balance': 14000, 'inflow': 15000}), ('Good month', {'inflow': 34000}))),
    TOOL('safe_draw', 'Safe Owner Draw', 'How much the host can take out this month',
         'Type your cash, the monthly profit, the tax set-aside share, the cash floor and the cash needed next month; see the safe draw, the planned draw and what is left.', [
        I('cash', 'Cash now', 74000), I('profit', 'Profit of the month', 18000), I('taxpct', 'Tax set-aside share of profit', 0.15, 'pct'), I('floor', 'Cash floor', 12000), I('next', 'Net cash needed next month', 6000), I('plan', 'Planned draw', 7000)], [
        O('Profit after the tax set-aside', 'money', A6), O('Tax set-aside from the profit', 'money', '{in:profit}*{in:taxpct}'), O('Cash above the floor after next month', 'money', B6), O('Safe draw', 'money', SAFE6),
        O('Planned draw against safe draw', 'money', '{in:plan}-' + SAFE6), O('Cash left after the planned draw', 'money', '{in:cash}-{in:plan}'), O('Months of planned draws the cash above the floor covers', 'num', 'IFERROR(MAX(0,%s)/{in:plan},0)' % B6),
        V('Verdict', 'IF(%s<=0,%s,IF({in:plan}<=%s,%s,%s))' % (SAFE6, ck2('No draw this month'), SAFE6, ck2('Safe to draw'), ck2('Draw less')))],
         GR('What if', ('Winter month, profit 4,000, cash 20,000', {'cash': 20000, 'profit': 4000}), ('Peak month, profit 45,000', {'profit': 45000}), ('Cash near the floor', {'cash': 15000, 'next': 6000}), ('Bigger plan, 12,000', {'plan': 12000}), ('Tax share 25 percent', {'taxpct': 0.25}))),
    TOOL('tax_set', 'Tax Set-Aside Calculator', 'Amount to hold back for the business tax instalment',
         'Type the profit so far this year, your set-aside share, what you set aside and paid so far, and the profit expected next month; see what you should hold, the shortfall and the next set-aside.', [
        I('profit', 'Profit so far this year', 118000), I('pct', 'Set-aside share of profit', 0.15, 'pct'), I('set', 'Set aside so far', 15500), I('paid', 'Paid so far', 6000), I('next', 'Profit expected next month', 9000)], [
        O('Amount to hold for the year so far', 'money', HOLD7), O('Balance held now', 'money', HELD7), O('Shortfall against the amount to hold', 'money', HOLD7 + '-{in:set}'), O('Set-aside on next month profit', 'money', '{in:next}*{in:pct}'),
        O('Next month set-aside with the shortfall caught up', 'money', '{in:next}*{in:pct}+MAX(0,%s-{in:set})' % HOLD7), O('Tax still to pay at this share', 'money', HOLD7 + '-{in:paid}'), O('Share of profit already set aside', 'pct', 'IFERROR({in:set}/{in:profit},0)'),
        V('Verdict', 'IF({in:set}>=%s*0.99,%s,%s)' % (HOLD7, ck2('Tax is funded'), ck2('Set aside more')))],
         GR('What if', ('Weak winter, profit 40,000', {'profit': 40000, 'set': 6000, 'paid': 0}), ('Share 25 percent', {'pct': 0.25}), ('Fully funded', {'set': 17700}), ('Nothing set aside yet', {'set': 0, 'paid': 0}), ('Big peak month ahead', {'next': 30000}))),
    TOOL('payout_gap', 'Payout Timing Gap', 'Cash needed to bridge the wait for payouts',
         'Type the costs due before payouts arrive, the monthly costs, the days of delay, the payouts expected in that time and your cash; see the cash needed to bridge the gap.', [
        I('due', 'Costs due before the first payout', 11200), I('costs_month', 'Running costs per month', 9000), I('delay', 'Days between the costs and the payouts', 12, 'int'), I('payouts', 'Payouts arriving in that time', 9000), I('cash', 'Cash you can use', 6000)], [
        O('Running costs per day', 'money', DAY8), O('Running costs during the wait', 'money', WIN8), O('Total costs to cover', 'money', '{in:due}+' + WIN8), O('Cash needed to bridge the gap', 'money', NEED8),
        O('Days of delay your cash covers', 'num', 'IFERROR(MAX(0,{in:cash}+{in:payouts}-{in:due})/%s,0)' % DAY8), O('Gap after using your cash', 'money', '{in:due}+%s-{in:payouts}-{in:cash}' % WIN8),
        V('Verdict', 'IF({in:due}+%s-{in:payouts}<=0,%s,IF(%s=0,%s,%s))' % (WIN8, ck2('No gap'), NEED8, ck2('Cash covers the gap'), ck2('Gap needs cash')))],
         GR('What if', ('Late payout, 21 days', {'delay': 21}), ('Fast payouts, 3 days', {'delay': 3}), ('Heavy month, costs due 15,000', {'due': 15000}), ('No cash buffer', {'cash': 0}), ('Strong payouts, 20,000', {'payouts': 20000}))),
    TOOL('new_unit', 'New Unit Return', 'Yearly profit and payback of one more unit',
         'Type the set-up cost, rent, bills, what a night earns, the occupancy and the cost of a booked night; see the yearly profit, the margin, the payback in months and the first-year profit.', [
        I('setup', 'Set-up cost', 9000), I('rent', 'Rent per month', 1100), I('bills', 'Bills per month', 140), I('rate', 'Earning per night', 140), I('occ', 'Expected occupancy', 0.65, 'pct'), I('fee', 'Platform fee share', 0.13, 'pct'), I('var', 'Cost per booked night', 28)], [
        O('Nights booked per year', 'int', NIGHT9), O('Revenue per year', 'money', REV9), O('Profit per year', 'money', PROF9), O('Profit per month', 'money', PROF9 + '/12'), O('Margin', 'pct', 'IFERROR(%s/%s,0)' % (PROF9, REV9)),
        O('Payback in months', 'num', 'IF(%s>0,{in:setup}/%s*12,0)' % (PROF9, PROF9)), O('Break-even occupancy', 'pct', 'IF({in:rate}*(1-{in:fee})-{in:var}>0,12*({in:rent}+{in:bills})/(({in:rate}*(1-{in:fee})-{in:var})*365),9.99)'),
        O('First-year profit with the ramp-up share', 'money', PROF9 + '*{set:new_unit_share}'), O('Longest payback you accept, months', 'int', '{set:max_payback}'),
        V('Verdict', 'IF(%s<=0,%s,IF({in:setup}/%s*12<={set:max_payback},%s,%s))' % (PROF9, ck2('Do not add the unit'), PROF9, ck2('Pays back in time'), ck2('Pays back too slowly')))],
         GR('What if', ('Lower occupancy, 50 percent', {'occ': 0.5}), ('Higher rent, 1,500', {'rent': 1500}), ('Premium unit', {'rate': 230, 'occ': 0.58, 'rent': 1900, 'bills': 220, 'setup': 15000}), ('Cheaper set-up, 6,000', {'setup': 6000}), ('Weak beach studio', {'rate': 74, 'occ': 0.45, 'rent': 1100}))),
    TOOL('keep_drop', 'Keep or Drop a Unit', 'Decision on one unit and the reason',
         'Type the revenue, profit and margin of the last 12 months, the months left on the lease, the review rating and the rate rise you could make; see the loss until the lease ends and the decision.', [
        I('rev', 'Revenue, 12 months', 19000), I('profit', 'Profit, 12 months', -5600), I('months', 'Months left on the lease', 3, 'int'), I('rating', 'Review rating', 4.4, 'num'), I('rise', 'Rate rise you could make', 0.12, 'pct'), I('fee', 'Platform fee share', 0.14, 'pct')], [
        O('Margin', 'pct', 'IFERROR({in:profit}/{in:rev},0)'), O('Wanted margin', 'pct', '{set:target_margin}'), O('Profit after the rate rise', 'money', PAFT10), O('Margin after the rate rise', 'pct', 'IFERROR(%s/({in:rev}*(1+{in:rise})),0)' % PAFT10),
        O('Profit or loss until the lease ends', 'money', '{in:profit}/12*{in:months}'), O('Revenue needed for the wanted margin', 'money', 'IFERROR(({in:rev}-{in:profit})/(1-{set:target_margin}),0)'),
        V('Verdict', 'IF(AND({in:profit}>0,{in:profit}/{in:rev}>={set:target_margin}),%s,IF(%s>0,%s,IF({in:months}<=3,%s,%s)))' % (ck2('Keep the unit'), PAFT10, ck2('Fix the rate first'), ck2('Drop the unit'), ck2('Review the unit'))),
        O('Profit still needed for the wanted margin', 'money', 'MAX(0,{set:target_margin}*{in:rev}-{in:profit})')],
         GR('What if', ('Healthy unit', {'profit': 6500, 'rev': 26000}), ('Small loss, rate rise helps', {'profit': -800, 'rev': 21000}), ('Deep loss, lease ends in 12 months', {'profit': -9000, 'months': 12, 'rise': 0.05}), ('Thin margin', {'profit': 2400, 'rev': 24000}), ('Low rating', {'rating': 3.9}))),
    TOOL('rate_rise', 'Rate Rise Impact', 'Profit change from a rate rise',
         'Type the rate now, the rise, the occupancy now and the occupancy you expect to lose; see the profit before and after, and the largest occupancy loss the rise can take.', [
        I('cur', 'Earning per night now', 140), I('rise', 'Rate rise', 0.08, 'pct'), I('occ', 'Occupancy now', 0.65, 'pct'), I('loss', 'Occupancy you expect to lose, in points', 0.03, 'pct'), I('fixed', 'Fixed cost per month', 1400), I('var', 'Cost per booked night', 28), I('fee', 'Platform fee share', 0.14, 'pct')], [
        O('New rate', 'money', NEW11), O('Profit per year before', 'money', PB11), O('Profit per year after', 'money', PA11), O('Profit change per year', 'money', PA11 + '-' + PB11), O('Occupancy after the rise', 'pct', '{in:occ}-{in:loss}'),
        O('Largest occupancy loss that keeps the profit', 'pct', '{in:occ}-{in:occ}*%s/%s' % (KEPT11C, KEPT11N)), O('Profit change per night booked', 'money', KEPT11N + '-' + KEPT11C),
        V('Verdict', 'IF(%s>%s,%s,%s)' % (PA11, PB11, ck2('Rate rise adds profit'), ck2('Rate rise loses profit')))],
         GR('What if', ('Bigger rise, 15 percent', {'rise': 0.15, 'loss': 0.07}), ('Small rise, 3 percent', {'rise': 0.03, 'loss': 0.0}), ('Big loss of guests', {'loss': 0.12}), ('High-rate unit', {'cur': 230, 'fixed': 2100, 'var': 38}), ('Busy unit at 80 percent', {'occ': 0.8, 'loss': 0.02}))),
    TOOL('direct_save', 'Fee Saving by Direct Bookings', 'Yearly platform fee saved when more guests book direct',
         'Type the yearly revenue, the direct share now and the share you aim for, the platform fee and the card fee on direct bookings; see the fees now and then, and the yearly saving.', [
        I('gross', 'Revenue per year', 560000), I('share', 'Direct share now', 0.22, 'pct'), I('target', 'Direct share you aim for', 0.35, 'pct'), I('pfee', 'Platform fee share', 0.14, 'pct'), I('dfee', 'Card fee share on direct bookings', 0.03, 'pct')], [
        O('Fees now', 'money', FNOW12), O('Fees at the target share', 'money', FTGT12), O('Saving per year', 'money', FNOW12 + '-' + FTGT12), O('Saving for each extra point of direct share', 'money', '{in:gross}*0.01*({in:pfee}-{in:dfee})'),
        O('Direct revenue now', 'money', '{in:gross}*{in:share}'), O('Direct revenue at the target', 'money', '{in:gross}*{in:target}'), O('Fees as a share of revenue now', 'pct', 'IFERROR(%s/{in:gross},0)' % FNOW12),
        V('Verdict', 'IF(%s-%s>=5000,%s,%s)' % (FNOW12, FTGT12, ck2('Direct saves money'), ck2('Direct saves little')))],
         GR('What if', ('Direct share 50 percent', {'target': 0.5}), ('Small aim, 25 percent', {'target': 0.25}), ('Higher platform fees', {'pfee': 0.18}), ('Smaller business', {'gross': 250000}), ('Already high, 40 percent', {'share': 0.4, 'target': 0.45}))),
    TOOL('cost_night', 'Cost per Night by Type', 'Cost per night of each kind',
         'Type the cleaning and supplies for one turnover, the stay length, the monthly bills and repairs, the nights booked and the platform fee; see the cost per night of each kind and what a night keeps.', [
        I('clean', 'Cleaning cost per turnover', 68), I('supp', 'Supplies per turnover', 14), I('stay', 'Average stay in nights', 3.2, 'num'), I('util', 'Utilities and internet per month', 180), I('maint', 'Repairs per month', 60),
        I('booked', 'Nights booked per month', 19, 'int'), I('rate', 'Earning per night', 150), I('fee', 'Platform fee share', 0.14, 'pct')], [
        O('Cleaning per night', 'money', CL13), O('Supplies per night', 'money', SU13), O('Utilities per night', 'money', UT13), O('Repairs per night', 'money', MA13), O('Platform fee per night', 'money', FE13),
        O('Total cost per night', 'money', TOT13), O('Kept per night before rent', 'money', '{in:rate}-' + TOT13), O('Cleaning share of the cost', 'pct', 'IFERROR(%s/%s,0)' % (CL13, TOT13)),
        O('Cost per night as a share of what it earns', 'pct', 'IFERROR(%s/{in:rate},0)' % TOT13), O('Cost per night at 10 more nights booked', 'money', '(%s+%s+({in:util}+{in:maint})/({in:booked}+10)+%s)' % (CL13, SU13, FE13))],
         GR('What if', ('Short stays, 1.8 nights', {'stay': 1.8}), ('Long stays, 6 nights', {'stay': 6}), ('Quiet month, 9 nights booked', {'booked': 9}), ('Big house, cleaning 140', {'clean': 140, 'supp': 22, 'util': 260}), ('High platform fee', {'fee': 0.2}))),
    TOOL('rate_grid', 'Occupancy and Rate Grid', 'Monthly profit for an occupancy and a nightly rate',
         'Type a nightly rate, an occupancy, the nights, the fixed cost, the platform fee and the cost of a booked night; see the revenue and profit of one unit. The grid tries rate and occupancy together.', [
        I('rate', 'Earning per night', 150), I('occ', 'Occupancy', 0.65, 'pct'), I('nights', 'Nights in the month', 30, 'int'), I('fixed', 'Fixed cost per month', 1400), I('fee', 'Platform fee share', 0.14, 'pct'), I('var', 'Cost per booked night', 28)], [
        O('Booked nights', 'num', '{in:nights}*{in:occ}'), O('Revenue', 'money', REV14), O('Platform fees', 'money', REV14 + '*{in:fee}'), O('Cost of booked nights', 'money', '{in:nights}*{in:occ}*{in:var}'), O('Profit', 'money', PRO14),
        O('Margin', 'pct', 'IFERROR(%s/%s,0)' % (PRO14, REV14)), O('Profit per available night', 'money', PRO14 + '/{in:nights}'), O('Profit for one more point of occupancy', 'money', '{in:rate}*{in:nights}*0.01*(1-{in:fee})-{in:nights}*0.01*{in:var}'),
        O('Profit for 5 more on the rate', 'money', '5*{in:nights}*{in:occ}*(1-{in:fee})'), V('Verdict', 'IF(%s<0,%s,%s)' % (PRO14, ck2('Loss'), ck2('Profit')))],
         GR('Rate and occupancy together', ('Rate 110, occupancy 50', {'rate': 110, 'occ': 0.5}), ('Rate 110, occupancy 75', {'rate': 110, 'occ': 0.75}), ('Rate 150, occupancy 50', {'rate': 150, 'occ': 0.5}), ('Rate 150, occupancy 75', {'rate': 150, 'occ': 0.75}),
            ('Rate 190, occupancy 50', {'rate': 190, 'occ': 0.5}), ('Rate 190, occupancy 75', {'rate': 190, 'occ': 0.75}), ('Rate 230, occupancy 45', {'rate': 230, 'occ': 0.45}), ('Rate 90, occupancy 90', {'rate': 90, 'occ': 0.9}))),
]
assert len(tools) == 14, len(tools)
