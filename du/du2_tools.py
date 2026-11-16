"""Doula Business suite part 2: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du2_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def PKG(p): return '=' + tok('cpackage', p)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
D365 = '">="&({today}-365)'; D90 = '">="&({today}-90)'
ADD, BIR, POS, COM = tok('pkind', 'Add-on'), tok('pkind', 'Birth'), tok('pkind', 'Postpartum'), tok('pkind', 'Combined')
TGT = '{set:target_income_hour}'


def AVG(c, P): return 'IFERROR(AVERAGEIFS({range:hours.%s},{range:hours.package},%s),0)' % (c, P)
def NH(P): return 'COUNTIFS({range:hours.package},%s)' % P
def PKP(c, P): return 'SUMIFS({range:packages.%s},{range:packages.package},%s)' % (c, P)
def PFN(c, P): return 'SUMIFS({range:pk_profit.%s},{range:pk_profit.package},%s)' % (c, P)
def PFT(c, P): return 'IFERROR(INDEX({range:pk_profit.%s},MATCH(%s,{range:pk_profit.package},0)),"")' % (c, P)
def SOLD12(P): return 'COUNTIFS({range:contracts.package},%s,{range:contracts.signed_on},%s)' % (P, D365)
def INC12(P): return 'SUMIFS({range:contracts.price},{range:contracts.package},%s,{range:contracts.signed_on},%s)' % (P, D365)
def LOWK(n, c): return 'IFERROR(INDEX({range:pk_profit.%s},MATCH(%d,{range:pk_profit.rank},0)),%s)' % (c, n, '""' if c == 'package' else '0')
def PPH(price, mil, hrs): return 'IF(%s>0,(%s-%s)/(%s),0)' % (hrs, price, mil, hrs)

tools = []
P1 = '{in:package}'
# 1 ------------------------------------------------------------ package profit per hour
AV1, MI1, HR1 = AVG('price', P1), AVG('mileage_cost', P1), AVG('total_hours', P1)
tools.append(TOOL('pph_tool', 'Package Profit per Hour', 'Which package earns the least for every hour you spend',
    'Pick a package and a price change: the hours really spent in each phase, the mileage and the income per hour, then the three lowest-earning packages and whether the lowest is below your target.', [
    IL('package', 'Package', 'cpackage', 'Complete Care Bundle'), I('target', 'Target income per hour', TARGET_INCOME_HOUR), I('chg', 'Price change to test', 0.0, 'pct')], [
    O('Average price paid, after discounts', 'money', AV1), O('Prenatal hours per client', 'num', AVG('prenatal_hours', P1)), O('On-call contact hours per client', 'num', AVG('oncall_hours', P1)),
    O('Birth hours per client', 'num', AVG('birth_hours', P1)), O('Postpartum hours per client', 'num', AVG('postpartum_hours', P1)), O('All hours per client', 'num', HR1),
    O('Mileage cost per client', 'money', MI1), O('Income per hour now', 'money', PFN('actual_pph', P1)), O('Income per hour after the price change', 'money', PPH('(%s)*(1+{in:chg})' % AV1, MI1, HR1)),
    O('Gap to your target after the change', 'money', '%s-{in:target}' % PPH('(%s)*(1+{in:chg})' % AV1, MI1, HR1)),
    O('Lowest-earning package', 'text', LOWK(1, 'package')), O('Its income per hour', 'money', LOWK(1, 'actual_pph')), O('Second lowest package', 'text', LOWK(2, 'package')), O('Its income per hour', 'money', LOWK(2, 'actual_pph')),
    O('Third lowest package', 'text', LOWK(3, 'package')), O('Its income per hour', 'money', LOWK(3, 'actual_pph')), O('Packages below your target', 'int', 'COUNTIFS({range:pk_profit.flag},%s)' % ck('Below the target')),
    O('Verdict', 'text', 'IF(%s<{in:target},%s,%s)' % (LOWK(1, 'actual_pph'), ck('Lowest package is below the target'), ck('Lowest package meets the target')))],
    GR('What if', ('Birth Plus', {'package': PKG('Birth Plus')}), ('Postpartum 80 Hours', {'package': PKG('Postpartum 80 Hours')}), ('Raise the price by 10 percent', {'chg': 0.10}), ('Target 35 an hour', {'target': 35}),
       ('Combined Plus', {'package': PKG('Combined Plus')}), ('Cut the price by 5 percent', {'chg': -0.05}))))

# 2 ------------------------------------------------------------ is my price right
AV2, MI2, HR2 = AVG('price', P1), AVG('mileage_cost', P1), AVG('total_hours', P1)
CH2 = '{in:owner_pay}+{in:costs}'
NEED2 = 'MAX(IFERROR((%s)/{in:billable},0),%s)' % (CH2, TGT)
tools.append(TOOL('price_right', 'Is my price right', 'Raise, hold or lower this package price',
    'Pick a package and type the owner pay you want, the monthly business costs and the hours you can bill in a month; see the income per hour you need, the price needed at plan hours and at actual hours, the local range and the verdict.', [
    IL('package', 'Package', 'cpackage', 'Complete Care Bundle'), I('owner_pay', 'Owner pay you want each month', OWNER_DRAW), I('costs', 'Business costs each month', 1660), I('billable', 'Hours you can bill in a month', 150, 'num')], [
    O('Cost per hour from owner pay and costs', 'money', 'IFERROR((%s)/{in:billable},0)' % CH2), O('Income per hour you need, the higher of that and your target', 'money', NEED2),
    O('List price now', 'money', PKP('price', P1)), O('Average price paid, after discounts', 'money', AV2), O('Plan hours', 'num', PKP('plan_hours', P1)), O('Actual hours per client', 'num', HR2),
    O('Mileage cost per client', 'money', MI2), O('Price needed at plan hours', 'money', '(%s)*%s+%s' % (NEED2, PKP('plan_hours', P1), MI2)), O('Price needed at actual hours', 'money', '(%s)*%s+%s' % (NEED2, HR2, MI2)),
    O('Change needed against the list price', 'money', '(%s)*%s+%s-%s' % (NEED2, HR2, MI2, PKP('price', P1))), O('Income per hour now', 'money', PFN('actual_pph', P1)),
    O('Local low', 'money', PFN('range_low', P1)), O('Local high', 'money', PFN('range_high', P1)), O('Price compared with the local range', 'money', PFN('range_value', P1)), O('Local range check', 'text', PFT('range_check', P1)),
    O('Verdict', 'text', 'IF(%s<%s,IF(%s=%s,%s,%s),IF(AND(%s>=1.5*(%s),%s=%s),%s,%s))' % (PFN('actual_pph', P1), NEED2, PFT('range_check', P1), ck('Above the range'), ck('Hold the price'), ck('Raise the price'),
        PFN('actual_pph', P1), NEED2, PFT('range_check', P1), ck('Above the range'), ck('Lower the price'), ck('Hold the price')))],
    GR('What if', ('Birth Plus', {'package': PKG('Birth Plus')}), ('Birth Premier', {'package': PKG('Birth Premier')}), ('Owner pay 4,500', {'owner_pay': 4500}), ('Costs 2,400', {'costs': 2400}),
       ('Only 110 billable hours', {'billable': 110}), ('Postpartum 40 Hours', {'package': PKG('Postpartum 40 Hours')}))))

# 3 ------------------------------------------------------------ combined-package test
BT = '{in:bundle}'
PB3 = 'IF({in:bundle}=%s,%s,IF({in:bundle}=%s,%s,%s))' % (tok('bundle', 'Combined Essential'), tok('package', 'Birth Essential'), tok('bundle', 'Combined Plus'), tok('package', 'Birth Plus'), tok('package', 'Birth Premier'))
PP3 = 'IF({in:bundle}=%s,%s,IF({in:bundle}=%s,%s,%s))' % (tok('bundle', 'Combined Essential'), tok('package', 'Postpartum 40 Hours'), tok('bundle', 'Combined Plus'), tok('package', 'Postpartum 80 Hours'), tok('package', 'Postpartum 120 Hours'))
SUM3 = '(%s+%s)' % (PKP('price', PB3), PKP('price', PP3))
AV3, MI3, HR3 = AVG('price', BT), AVG('mileage_cost', BT), AVG('total_hours', BT)
PARTS3 = 'IFERROR((%s*%s+%s*%s)/(%s+%s),0)' % (PFN('actual_pph', PB3), PKP('plan_hours', PB3), PFN('actual_pph', PP3), PKP('plan_hours', PP3), PKP('plan_hours', PB3), PKP('plan_hours', PP3))
tools.append(TOOL('bundle_tool', 'Combined-Package Test', 'Does the combined package pay against its parts',
    'Pick a combined package and an extra discount to test: its price against the list prices of the birth package and postpartum pack it is made of, the discount given, the hours and the income per hour, with a verdict against your target.', [
    IL('bundle', 'Combined package', 'bundle', 'Complete Care Bundle'), I('extra', 'Extra discount to test on the bundle price', 0.0, 'pct')], [
    O('Bundle list price', 'money', PKP('price', BT)), O('Sum of the parts at list price', 'money', SUM3), O('Discount given against the parts', 'money', '%s-%s' % (SUM3, PKP('price', BT))),
    O('Discount share of the parts', 'pct', 'IFERROR((%s-%s)/%s,0)' % (SUM3, PKP('price', BT), SUM3)), O('Plan hours of the bundle', 'num', PKP('plan_hours', BT)),
    O('Plan hours of the parts', 'num', '%s+%s' % (PKP('plan_hours', PB3), PKP('plan_hours', PP3))), O('Actual hours per client', 'num', HR3), O('Average price paid, after discounts', 'money', AV3),
    O('Mileage cost per client', 'money', MI3), O('Bundle income per hour now', 'money', PFN('actual_pph', BT)), O('Parts income per hour, plan hours weighted', 'money', PARTS3),
    O('Gap to your target per hour', 'money', '%s-%s' % (PFN('actual_pph', BT), TGT)), O('Income per hour with the extra discount', 'money', PPH('(%s)*(1-{in:extra})' % AV3, MI3, HR3)),
    O('Price needed for the target at actual hours', 'money', '%s*%s+%s' % (TGT, HR3, MI3)), O('Price short of the target, if any', 'money', 'MAX(0,%s*%s+%s-%s)' % (TGT, HR3, MI3, AV3)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (PFN('actual_pph', BT), TGT, ck('Bundle pays'), ck('Bundle loses')))],
    GR('What if', ('Combined Essential', {'bundle': '=' + tok('bundle', 'Combined Essential')}), ('Combined Plus', {'bundle': '=' + tok('bundle', 'Combined Plus')}), ('Extra discount 5 percent', {'extra': 0.05}),
       ('Extra discount 10 percent', {'extra': 0.10}), ('Raise the bundle price 5 percent', {'extra': -0.05}))))

# 4 ------------------------------------------------------------ add-on keep or drop
A4 = '{in:addon}'
SOLD4 = 'COUNTIFS({range:addons.addon},%s)' % A4; INC4 = 'SUMIFS({range:addons.price},{range:addons.addon},%s)' % A4; HRS4 = 'SUMIFS({range:addons.hours},{range:addons.addon},%s)' % A4
tools.append(TOOL('addon_keep', 'Add-on Keep or Drop', 'Keep, reprice or drop this add-on',
    'Pick an add-on: how often it sold, its income and hours, the income per hour against your target and its attach rate; the verdict keeps it, reprices it or drops it.', [
    IL('addon', 'Add-on', 'addon', 'Debrief visit'), I('target', 'Target income per hour', TARGET_INCOME_HOUR), I('min_sold', 'Fewest sales that justify keeping it', 8, 'int')], [
    O('Price', 'money', PKP('price', A4)), O('Sold, all history', 'int', SOLD4), O('Sold in the last 90 days', 'int', 'COUNTIFS({range:addons.addon},%s,{range:addons.date},%s)' % (A4, D90)), O('Income', 'money', INC4),
    O('Hours logged', 'num', HRS4), O('Hours per sale', 'num', 'IF(%s>0,%s/%s,0)' % (SOLD4, HRS4, SOLD4)), O('Income per hour', 'money', 'IF(%s>0,%s/%s,0)' % (HRS4, INC4, HRS4)),
    O('Gap to your target per hour', 'money', 'IF(%s>0,%s/%s-{in:target},0)' % (HRS4, INC4, HRS4)), O('Price needed for the target', 'money', '{in:target}*IF(%s>0,%s/%s,0)' % (SOLD4, HRS4, SOLD4)),
    O('Attach rate, per contract signed', 'pct', 'IFERROR(INDEX({range:addon_attach.attach_rate},MATCH(%s,{range:addon_attach.addon},0)),0)' % A4),
    O('Add-ons sold, all kinds', 'int', 'COUNTIFS({range:addons.addon},"<>")'), O('Verdict', 'text', 'IF(%s>0,IF(%s/%s>={in:target},%s,IF(%s>={in:min_sold},%s,%s)),IF(%s>={in:min_sold},%s,%s))' % (
        HRS4, INC4, HRS4, ck('Keep it'), SOLD4, ck('Reprice it'), ck('Drop it'), SOLD4, ck('Keep it'), ck('Drop it')))],
    GR('What if', ('Extra prenatal visit', {'addon': '=' + tok('addon', 'Extra prenatal visit')}), ('Class seat', {'addon': '=' + tok('addon', 'Class seat (series)')}), ('Photography referral', {'addon': '=' + tok('addon', 'Photography referral')}),
       ('Support referral note', {'addon': '=' + tok('addon', 'Support referral note')}), ('Target 50 an hour', {'target': 50}), ('Keep only if sold 15 times', {'min_sold': 15}))))

# 5 ------------------------------------------------------------ break-even price solver
AV5, MI5, HR5 = AVG('price', P1), AVG('mileage_cost', P1), AVG('total_hours', P1)
BE_P = '({in:target}*%s+%s)' % (PKP('plan_hours', P1), MI5); BE_A = '({in:target}*%s+%s)' % (HR5, MI5)
tools.append(TOOL('breakeven', 'Break-Even Price Solver', 'The price that earns exactly your target per hour',
    'Pick a package and your target income per hour: the price that gives exactly that target at plan hours and at the hours really spent, worked out in closed form, against the list price and the average price paid.', [
    IL('package', 'Package', 'cpackage', 'Complete Care Bundle'), I('target', 'Target income per hour', TARGET_INCOME_HOUR)], [
    O('List price', 'money', PKP('price', P1)), O('Average price paid, after discounts', 'money', AV5), O('Plan hours', 'num', PKP('plan_hours', P1)), O('Actual hours per client', 'num', HR5), O('Mileage cost per client', 'money', MI5),
    O('Break-even price at plan hours', 'money', BE_P), O('Break-even price at actual hours', 'money', BE_A), O('List price less the break-even at actual hours', 'money', '%s-%s' % (PKP('price', P1), BE_A)),
    O('Average price paid less the break-even', 'money', '%s-%s' % (AV5, BE_A)), O('Highest discount that holds the target', 'pct', 'IFERROR(MAX(0,1-%s/%s),0)' % (BE_A, PKP('price', P1))),
    O('Average discount given on this package', 'pct', 'IFERROR(1-%s/%s,0)' % (AV5, PKP('price', P1))), O('Income per hour now', 'money', PFN('actual_pph', P1)),
    O('Rise of the list price needed for the target', 'pct', 'IFERROR(MAX(0,%s/%s-1),0)' % (BE_A, PKP('price', P1))),
    O('Verdict', 'text', 'IF(%s<%s,%s,%s)' % (PKP('price', P1), BE_A, ck('Price is below the break-even'), ck('Price is above the break-even')))],
    GR('What if', ('Birth Essential', {'package': PKG('Birth Essential')}), ('Combined Plus', {'package': PKG('Combined Plus')}), ('Postpartum 120 Hours', {'package': PKG('Postpartum 120 Hours')}),
       ('Target 25 an hour', {'target': 25}), ('Target 40 an hour', {'target': 40}))))

# 6 ------------------------------------------------------------ price change scenario
E6 = 'IF({in:scn}=%s,0.2,IF({in:scn}=%s,1,0.5))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
AV6, MI6, HR6 = AVG('price', P1), AVG('mileage_cost', P1), AVG('total_hours', P1)
def INCCH(e): return '%s*((1+{in:chg})*(1-%s*{in:chg})-1)' % (INC12(P1), e)
PPH6 = PPH('(%s)*(1+{in:chg})' % AV6, MI6, HR6)
tools.append(TOOL('price_chg', 'Price Change Scenario', 'What a price rise or cut does to income and income per hour',
    'Pick a package, a price change and a Base, Best or Worst scenario (the share of sign-ups lost for each 1% rise): your own sign-ups of the last 12 months, the income and the income per hour after the change.', [
    IL('package', 'Package', 'cpackage', 'Birth Plus'), I('chg', 'Price change', 0.05, 'pct'), IL('scn', 'Scenario', 'scen', 'Base')], [
    O('Sign-ups in the last 12 months', 'int', SOLD12(P1)), O('List price now', 'money', PKP('price', P1)), O('List price after the change', 'money', 'ROUND(%s*(1+{in:chg}),0)' % PKP('price', P1)),
    O('Sign-ups lost per 1% rise, this scenario', 'num', E6), O('Expected sign-ups a year', 'num', '%s*(1-%s*{in:chg})' % (SOLD12(P1), E6)), O('Income, last 12 months', 'money', INC12(P1)),
    O('Expected income a year, this scenario', 'money', '%s*(1+{in:chg})*(1-%s*{in:chg})' % (INC12(P1), E6)), O('Income change, this scenario', 'money', INCCH(E6)),
    O('Income change, Best', 'money', INCCH('0.2')), O('Income change, Worst', 'money', INCCH('1')), O('Income per hour now', 'money', PFN('actual_pph', P1)), O('Income per hour after the change', 'money', PPH6),
    O('Gap to your target after the change', 'money', '%s-%s' % (PPH6, TGT)),
    O('Verdict', 'text', 'IF(AND(%s>0,%s>=%s),%s,%s)' % (INCCH(E6), PPH6, TGT, ck('Raise the price'), ck('Hold the price')))],
    GR('What if', ('Worst scenario', {'scn': '=' + tok('scen', 'Worst')}), ('Best scenario', {'scn': '=' + tok('scen', 'Best')}), ('Raise 10 percent', {'chg': 0.10}), ('Cut 5 percent', {'chg': -0.05}),
       ('Complete Care Bundle plus 8 percent', {'package': PKG('Complete Care Bundle'), 'chg': 0.08}), ('Birth Premier minus 5 percent', {'package': PKG('Birth Premier'), 'chg': -0.05}))))

# 7 ------------------------------------------------------------ postpartum rate check
PK7, SH7 = '{in:pack}', '{in:shift}'
RT7 = 'SUMIFS({range:pp_rates.rate_hour},{range:pp_rates.shift},%s)' % SH7
PH7 = 'IFERROR(%s/%s,0)' % (PKP('price', PK7), PKP('postpartum_hours', PK7))
tools.append(TOOL('pp_rate_check', 'Postpartum Rate Check', 'Is the pack cheaper than hourly booking',
    'Pick a postpartum pack and a shift: the pack price per hour against the hourly rate for that shift and the minimum booking, how much of the rate the pack gives away and a verdict against the most you accept.', [
    IL('pack', 'Postpartum pack', 'ppack', 'Night Support 60 Hours'), IL('shift', 'Shift', 'shift', 'Night shift'), I('max_saving', 'Most the pack may save against hourly', 0.10, 'pct')], [
    O('Pack price', 'money', PKP('price', PK7)), O('Pack hours', 'num', PKP('postpartum_hours', PK7)), O('Pack price per hour', 'money', PH7), O('Hourly rate for the shift', 'money', RT7),
    O('Minimum booking, hours', 'int', 'SUMIFS({range:pp_rates.min_hours},{range:pp_rates.shift},%s)' % SH7), O('Minimum booking charge', 'money', '%s*SUMIFS({range:pp_rates.min_hours},{range:pp_rates.shift},%s)' % (RT7, SH7)),
    O('Saving per hour against hourly', 'money', '%s-%s' % (RT7, PH7)), O('Share of the hourly rate saved', 'pct', 'IFERROR((%s-%s)/%s,0)' % (RT7, PH7, RT7)),
    O('Same hours at the hourly rate', 'money', '%s*%s' % (RT7, PKP('postpartum_hours', PK7))), O('Saving on the whole pack', 'money', '%s*%s-%s' % (RT7, PKP('postpartum_hours', PK7), PKP('price', PK7))),
    O('Pack price per hour that saves exactly your limit', 'money', '%s*(1-{in:max_saving})' % RT7), O('Contracts of this pack, last 12 months', 'int', SOLD12(PK7)),
    O('Verdict', 'text', 'IF(IFERROR((%s-%s)/%s,0)>{in:max_saving},%s,%s)' % (RT7, PH7, RT7, ck('Pack is cheaper than hourly'), ck('Pack price is fine')))],
    GR('What if', ('Postpartum 120 Hours, day shift', {'pack': '=' + tok('ppack', 'Postpartum 120 Hours'), 'shift': '=' + tok('shift', 'Day shift')}), ('Postpartum 80 Hours, evening', {'pack': '=' + tok('ppack', 'Postpartum 80 Hours'), 'shift': '=' + tok('shift', 'Evening shift')}),
       ('Postpartum 40 Hours, weekend', {'pack': '=' + tok('ppack', 'Postpartum 40 Hours'), 'shift': '=' + tok('shift', 'Weekend and holiday')}), ('Allow a 15 percent saving', {'max_saving': 0.15}), ('Allow a 5 percent saving', {'max_saving': 0.05}))))

# 8 ------------------------------------------------------------ hour-pack sizing
def PPH_OF(p): return 'IFERROR(%s/%s,0)' % (PKP('price', tok('package', p)), PKP('postpartum_hours', tok('package', p)))
RT8 = 'SUMIFS({range:pp_rates.rate_hour},{range:pp_rates.shift},{in:shift})'
def DISC8(p): return 'IFERROR(1-%s/%s,0)' % (PPH_OF(p), RT8)
def S12(p): return SOLD12(tok('package', p))
tools.append(TOOL('pack_ladder', 'Hour-Pack Sizing', 'Is the ladder of 40, 80 and 120 hour packs right',
    'Pick the shift to compare with: the price per hour of each pack, the discount each gives against that shift rate, the price of each extra step and your own sales of the last 12 months; the verdict keeps the ladder, reprices a pack or drops the 120.', [
    IL('shift', 'Shift to compare with', 'shift', 'Day shift'), I('max_disc', 'Largest discount a pack may give', 0.08, 'pct'), I('min_sales', 'Fewest sales a pack needs in a year', 4, 'int')], [
    O('Hourly rate for the shift', 'money', RT8), O('40 hours: price per hour', 'money', PPH_OF('Postpartum 40 Hours')), O('80 hours: price per hour', 'money', PPH_OF('Postpartum 80 Hours')),
    O('120 hours: price per hour', 'money', PPH_OF('Postpartum 120 Hours')), O('Night pack: price per hour', 'money', PPH_OF('Night Support 60 Hours')), O('40 hours: discount against hourly', 'pct', DISC8('Postpartum 40 Hours')),
    O('80 hours: discount against hourly', 'pct', DISC8('Postpartum 80 Hours')), O('120 hours: discount against hourly', 'pct', DISC8('Postpartum 120 Hours')),
    O('Price of each extra hour from 40 to 80', 'money', '(%s-%s)/40' % (PKP('price', tok('package', 'Postpartum 80 Hours')), PKP('price', tok('package', 'Postpartum 40 Hours')))),
    O('Price of each extra hour from 80 to 120', 'money', '(%s-%s)/40' % (PKP('price', tok('package', 'Postpartum 120 Hours')), PKP('price', tok('package', 'Postpartum 80 Hours')))),
    O('40 hours: sold in 12 months', 'int', S12('Postpartum 40 Hours')), O('80 hours: sold in 12 months', 'int', S12('Postpartum 80 Hours')), O('120 hours: sold in 12 months', 'int', S12('Postpartum 120 Hours')),
    O('Verdict', 'text', 'IF(OR(%s>{in:max_disc},%s>{in:max_disc},%s>{in:max_disc}),%s,IF(%s<{in:min_sales},%s,%s))' % (
        DISC8('Postpartum 40 Hours'), DISC8('Postpartum 80 Hours'), DISC8('Postpartum 120 Hours'), ck('Reprice a pack'), S12('Postpartum 120 Hours'), ck('Drop the 120 pack'), ck('Keep the ladder')))],
    GR('What if', ('Compare with the night shift', {'shift': '=' + tok('shift', 'Night shift')}), ('Compare with the evening shift', {'shift': '=' + tok('shift', 'Evening shift')}), ('Compare with weekends', {'shift': '=' + tok('shift', 'Weekend and holiday')}),
       ('Allow a 5 percent discount', {'max_disc': 0.05}), ('Every pack needs 10 sales', {'min_sales': 10}))))

# 9 ------------------------------------------------------------ discount ceiling
AV9, MI9, HR9 = AVG('price', P1), AVG('mileage_cost', P1), AVG('total_hours', P1)
NEED9 = '({in:target}*%s+%s)' % (HR9, MI9)
CEIL9 = 'IFERROR(MAX(0,1-%s/%s),0)' % (NEED9, PKP('price', P1))
tools.append(TOOL('disc_ceiling', 'Discount Ceiling', 'The biggest discount that still holds your target',
    'Pick a package and the discount you give (a community rate is a lower price for a client who cannot pay the full price): the highest discount that still holds your target income per hour, worked out in closed form, and the verdict.', [
    IL('package', 'Package', 'cpackage', 'Postpartum 120 Hours'), I('disc', 'Discount you give', DISCOUNT_PCT['Community rate'], 'pct'), I('target', 'Target income per hour', TARGET_INCOME_HOUR)], [
    O('List price', 'money', PKP('price', P1)), O('Actual hours per client', 'num', HR9), O('Mileage cost per client', 'money', MI9), O('Price needed for the target', 'money', NEED9), O('Highest discount that holds the target', 'pct', CEIL9),
    O('Room left under the ceiling', 'pct', '%s-{in:disc}' % CEIL9), O('Price after your discount', 'money', '%s*(1-{in:disc})' % PKP('price', P1)),
    O('Income per hour after your discount', 'money', PPH('%s*(1-{in:disc})' % PKP('price', P1), MI9, HR9)), O('Gap to the target per hour', 'money', '%s-{in:target}' % PPH('%s*(1-{in:disc})' % PKP('price', P1), MI9, HR9)),
    O('Community rate you set', 'pct', '{set:community_pct}'), O('Returning-client discount you set', 'pct', '{set:returning_pct}'),
    O('Contracts on a discount, last 12 months', 'int', 'COUNTIFS({range:contracts.package},%s,{range:contracts.discount_given},">0",{range:contracts.signed_on},%s)' % (P1, D365)),
    O('Price given up on this package, 12 months', 'money', 'SUMIFS({range:contracts.discount_given},{range:contracts.package},%s,{range:contracts.signed_on},%s)' % (P1, D365)),
    O('Verdict', 'text', 'IF({in:disc}>%s,%s,%s)' % (CEIL9, ck('Discount is above the ceiling'), ck('Discount is inside the ceiling')))],
    GR('What if', ('Returning client discount', {'disc': DISCOUNT_PCT['Returning client']}), ('Birth Plus, community rate', {'package': PKG('Birth Plus')}), ('Birth Essential, 30 percent', {'package': PKG('Birth Essential'), 'disc': 0.30}),
       ('Complete Care Bundle, 5 percent', {'package': PKG('Complete Care Bundle'), 'disc': 0.05}), ('Target 25 an hour', {'target': 25}))))

# 10 ----------------------------------------------------------- travel fee check
A10 = '{in:area}'
CL10 = 'COUNTIFS({range:hours.area},%s)' % A10
MIL10 = 'SUMIFS({range:hours.mileage_cost},{range:hours.area},%s)' % A10; PR10 = 'SUMIFS({range:hours.price},{range:hours.area},%s)' % A10
RATE10 = 'SUMIFS({range:areas.mileage_rate},{range:areas.area},%s)' % A10; MILES10 = 'SUMIFS({range:areas.miles_one_way},{range:areas.area},%s)' % A10
FEE10 = 'IF(%s>0,MAX(0,%s/%s-{in:limit}*%s/%s),0)' % (CL10, MIL10, CL10, PR10, CL10)
tools.append(TOOL('travel_fee', 'Travel Fee Check', 'Does this area need a travel fee',
    'Pick an area: the mileage rate and the miles one way, what mileage really cost on your finished clients in the area as a share of the price paid, the fee per client that brings it back to your limit and the verdict.', [
    IL('area', 'Service area', 'area', 'Southbank'), I('limit', 'Highest mileage cost as a share of the price', 0.07, 'pct')], [
    O('Mileage rate per mile', 'money', RATE10), O('Miles one way', 'int', MILES10), O('Mileage cost of one round trip', 'money', '%s*2*%s' % (RATE10, MILES10)), O('Finished clients in the area', 'int', CL10),
    O('Mileage cost, all of them', 'money', MIL10), O('Price paid, all of them', 'money', PR10), O('Mileage share of the price', 'pct', 'IFERROR(%s/%s,0)' % (MIL10, PR10)),
    O('Average mileage cost per client', 'money', 'IFERROR(%s/%s,0)' % (MIL10, CL10)), O('Average price paid per client', 'money', 'IFERROR(%s/%s,0)' % (PR10, CL10)),
    O('Highest mileage per client you accept', 'money', '{in:limit}*IFERROR(%s/%s,0)' % (PR10, CL10)), O('Travel fee needed per client', 'money', FEE10),
    O('Clients in the area, last 12 months', 'int', 'COUNTIFS({range:hours.area},%s,{range:hours.month},%s)' % (A10, D365)),
    O('Travel fee income a year at that volume', 'money', '%s*COUNTIFS({range:hours.area},%s,{range:hours.month},%s)' % (FEE10, A10, D365)),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>{in:limit},%s,%s)' % (MIL10, PR10, v2('Add a travel fee now'), v2('Hold the travel fee')))],
    GR('What if', ('Northgate', {'area': '=' + tok('area', 'Northgate')}), ('Accept 10 percent', {'limit': 0.10}), ('Accept 5 percent', {'limit': 0.05}), ('Northgate, accept 5 percent', {'area': '=' + tok('area', 'Northgate'), 'limit': 0.05}))))

# 11 ----------------------------------------------------------- plan hours vs actual
AV11, MI11, HR11 = AVG('price', P1), AVG('mileage_cost', P1), AVG('total_hours', P1)
GAP11 = 'IFERROR(%s/%s-1,0)' % (HR11, PKP('plan_hours', P1))
tools.append(TOOL('plan_actual', 'Plan Hours vs Actual', 'Is the plan hours figure of this package right',
    'Pick a package and the gap you accept: the plan hours against the hours your finished clients really took, the share of clients over plan, the income per hour at each and a verdict that points to the price or to the plan.', [
    IL('package', 'Package', 'cpackage', 'Complete Care Bundle'), I('tol', 'Gap to plan you accept', 0.10, 'pct')], [
    O('Plan hours', 'num', PKP('plan_hours', P1)), O('Actual hours per client', 'num', HR11), O('Gap in hours', 'num', '%s-%s' % (HR11, PKP('plan_hours', P1))), O('Gap to plan', 'pct', GAP11),
    O('Finished clients', 'int', NH(P1)), O('Clients over plan hours', 'int', 'COUNTIFS({range:hours.package},%s,{range:hours.over_plan},1)' % P1),
    O('Share of clients over plan hours', 'pct', 'IFERROR(COUNTIFS({range:hours.package},%s,{range:hours.over_plan},1)/%s,0)' % (P1, NH(P1))),
    O('Average price paid, after discounts', 'money', AV11), O('Income per hour at plan hours', 'money', PPH(AV11, MI11, PKP('plan_hours', P1))), O('Income per hour at actual hours', 'money', PPH(AV11, MI11, HR11)),
    O('Hours the package loses or gains against plan, yearly', 'num', '(%s-%s)*%s' % (HR11, PKP('plan_hours', P1), SOLD12(P1))),
    O('Verdict', 'text', 'IF(ABS(%s)<={in:tol},IF(%s<%s,%s,%s),IF(%s>{in:tol},IF(%s<%s,%s,%s),%s))' % (
        GAP11, PPH(AV11, MI11, HR11), TGT, ck('Raise the price'), ck('On plan'), GAP11, PPH(AV11, MI11, HR11), TGT, ck('Raise the price'), v2('Fix the plan hours'), v2('Fix the plan hours')))],
    GR('What if', ('Birth Premier', {'package': PKG('Birth Premier')}), ('Birth Plus', {'package': PKG('Birth Plus')}), ('Combined Plus', {'package': PKG('Combined Plus')}), ('Accept 3 percent', {'tol': 0.03}),
       ('Postpartum 40 Hours', {'package': PKG('Postpartum 40 Hours')}))))

# 12 ----------------------------------------------------------- volume and income grid
TOTAL12 = 'COUNTIFS({range:contracts.signed_on},%s)' % D365
AVGS12 = '(%s/COUNTIFS({range:packages.kind},"<>"&%s))' % (TOTAL12, ADD)
AVGS12 = '(%s/10)' % TOTAL12
tools.append(TOOL('volume_grid', 'Volume and Income Grid', 'Promote, reprice or retire this package',
    'Pick a package: how often it sold in the last 12 months against the average package and what it earns per hour against your target; the grid puts it in one of four boxes: promote, keep, reprice or retire.', [
    IL('package', 'Package', 'cpackage', 'Complete Care Bundle'), I('target', 'Target income per hour', TARGET_INCOME_HOUR), I('min_sold', 'Fewest sales that keep a package alive', 3, 'int')], [
    O('Sold in the last 12 months', 'int', SOLD12(P1)), O('Average sales per package', 'num', AVGS12), O('Share of all contracts', 'pct', 'IFERROR(%s/%s,0)' % (SOLD12(P1), TOTAL12)),
    O('Income booked in the last 12 months', 'money', INC12(P1)), O('Share of all income booked', 'pct', 'IFERROR(%s/SUMIFS({range:contracts.price},{range:contracts.signed_on},%s),0)' % (INC12(P1), D365)),
    O('Income per hour', 'money', PFN('actual_pph', P1)), O('Gap to your target per hour', 'money', '%s-{in:target}' % PFN('actual_pph', P1)), O('Sold less than average', 'int', 'IF(%s<%s,1,0)' % (SOLD12(P1), AVGS12)),
    O('Earns less than target', 'int', 'IF(%s<{in:target},1,0)' % PFN('actual_pph', P1)), O('Packages below your target', 'int', 'COUNTIFS({range:pk_profit.flag},%s)' % ck('Below the target')),
    O('Verdict', 'text', 'IF(%s>={in:target},IF(%s>=%s,%s,%s),IF(%s<{in:min_sold},%s,%s))' % (PFN('actual_pph', P1), SOLD12(P1), AVGS12, v2('Keep as it is'), v2('Promote it'), SOLD12(P1), v2('Retire it'), v2('Reprice it now')))],
    GR('What if', ('Birth Essential', {'package': PKG('Birth Essential')}), ('Birth Premier', {'package': PKG('Birth Premier')}), ('Night Support 60 Hours', {'package': PKG('Night Support 60 Hours')}),
       ('Combined Essential', {'package': PKG('Combined Essential')}), ('Target 40 an hour', {'target': 40}), ('Keep a package only with 8 sales', {'min_sold': 8}))))

# 13 ----------------------------------------------------------- new package designer
HRS13 = '({in:pv}*{set:prenatal_visit_hours}+{in:pov}*{set:pp_visit_hours}+{in:bh}+{in:oh}+{in:pph})'
PRICE13 = 'ROUNDUP(({in:target}*%s+{in:travel})/5,0)*5' % HRS13
LOW13 = 'SUMIFS({range:local_range.local_low},{range:local_range.label},IF({in:pph}>0,%s,%s))' % (tok('lrange', 'Combined package'), tok('lrange', 'Birth package'))
HIGH13 = 'SUMIFS({range:local_range.local_high},{range:local_range.label},IF({in:pph}>0,%s,%s))' % (tok('lrange', 'Combined package'), tok('lrange', 'Birth package'))
tools.append(TOOL('new_pkg', 'New Package Designer', 'Price a new package before you launch it',
    'Type the visits and hours of a new package, a travel allowance and your target income per hour: the price needed, the deposit and its place in your local range; the verdict launches it or sends you back to adjust it.', [
    I('pv', 'Prenatal visits', 3, 'int'), I('pov', 'Postpartum visits', 1, 'int'), I('bh', 'Birth hours planned', 20, 'num'), I('oh', 'On-call contact hours planned', 8, 'num'), I('pph', 'Postpartum hours in the pack', 0, 'num'),
    I('travel', 'Travel allowance', 45), I('target', 'Target income per hour', TARGET_INCOME_HOUR), I('dep', 'Deposit share', 0.30, 'pct')], [
    O('Plan hours, all phases', 'num', HRS13), O('Hours of prenatal visits', 'num', '{in:pv}*{set:prenatal_visit_hours}'), O('Hours of postpartum visits', 'num', '{in:pov}*{set:pp_visit_hours}'),
    O('Price needed, rounded up to 5', 'money', PRICE13), O('Deposit', 'money', 'ROUND((%s)*{in:dep},0)' % PRICE13), O('Balance after the deposit', 'money', '(%s)-ROUND((%s)*{in:dep},0)' % (PRICE13, PRICE13)),
    O('Price per plan hour', 'money', 'IFERROR((%s)/%s,0)' % (PRICE13, HRS13)), O('Local low for this kind', 'money', LOW13), O('Local high for this kind', 'money', HIGH13),
    O('Position in the local range', 'pct', 'IFERROR(((%s)-%s)/(%s-%s),0)' % (PRICE13, LOW13, HIGH13, LOW13)), O('Lowest price of your birth packages', 'money', 'SUMIFS({range:packages.price},{range:packages.package},%s)' % tok('package', 'Birth Essential')),
    O('Hours if you add 4 on-call hours', 'num', '%s+4' % HRS13), O('Price needed with 4 more on-call hours', 'money', 'ROUNDUP(({in:target}*(%s+4)+{in:travel})/5,0)*5' % HRS13),
    O('Verdict', 'text', 'IF(AND((%s)>=%s,(%s)<=%s),%s,%s)' % (PRICE13, LOW13, PRICE13, HIGH13, v2('Launch it'), v2('Adjust the package')))],
    GR('What if', ('Add a 20-hour postpartum block', {'pph': 20}), ('Bigger package, 5 prenatal visits', {'pv': 5, 'bh': 24, 'oh': 10}), ('Lean package, 1 prenatal visit', {'pv': 1, 'bh': 16, 'oh': 4, 'pov': 0}),
       ('Target 45 an hour', {'target': 45}), ('Longer travel, allowance 120', {'travel': 120}), ('Deposit 50 percent', {'dep': 0.5}))))

# 14 ----------------------------------------------------------- next-year price plan
AV14, MI14, HR14 = AVG('price', P1), AVG('mileage_cost', P1), AVG('total_hours', P1)
PPH14B = PPH('(%s)*(1+{in:rise})' % AV14, '(%s)*(1+{in:cost_rise})' % MI14, HR14)
tools.append(TOOL('next_year', 'Next-Year Price Plan', 'Does the planned rise keep up with your costs',
    'Pick a package, a planned price rise and how much your own costs and target rise: the income per hour after the rise against the raised target, the yearly income at your current volume and the rise you would need.', [
    IL('package', 'Package', 'cpackage', 'Complete Care Bundle'), I('rise', 'Planned rise of the price', 0.05, 'pct'), I('cost_rise', 'Rise of your costs and target', 0.04, 'pct')], [
    O('List price now', 'money', PKP('price', P1)), O('List price after the rise', 'money', 'ROUND(%s*(1+{in:rise}),0)' % PKP('price', P1)), O('Average price paid, after discounts', 'money', AV14),
    O('Actual hours per client', 'num', HR14), O('Sign-ups in the last 12 months', 'int', SOLD12(P1)), O('Income of the last 12 months', 'money', INC12(P1)),
    O('Yearly income after the rise, same volume', 'money', '%s*(1+{in:rise})' % INC12(P1)), O('Yearly income gained', 'money', '%s*{in:rise}' % INC12(P1)),
    O('Income per hour now', 'money', PPH(AV14, MI14, HR14)), O('Income per hour after the rise', 'money', PPH14B), O('Your target after the cost rise', 'money', '%s*(1+{in:cost_rise})' % TGT),
    O('Rise needed to meet the raised target', 'pct', 'IFERROR(MAX(0,(%s*(1+{in:cost_rise})*%s+(%s)*(1+{in:cost_rise}))/(%s)-1),0)' % (TGT, HR14, MI14, AV14)),
    O('Verdict', 'text', 'IF(%s>=%s*(1+{in:cost_rise}),%s,%s)' % (PPH14B, TGT, v2('Rise holds'), v2('Rise too small')))],
    GR('What if', ('Birth Essential, 5 percent', {'package': PKG('Birth Essential')}), ('Rise 10 percent', {'rise': 0.10}), ('Rise 2 percent', {'rise': 0.02}), ('Costs rise 8 percent', {'cost_rise': 0.08}),
       ('Birth Plus, 6 percent', {'package': PKG('Birth Plus'), 'rise': 0.06}))))

# 15 ----------------------------------------------------------- package sales forecast
def CK6(kind, a, b): return 'COUNTIFS({range:contracts.kind},%s,{range:contracts.signed_on},">="&EDATE(%s,%d),{range:contracts.signed_on},"<"&EDATE(%s,%d))' % (kind, MS, a, MS, b)
def CT(a, b): return 'COUNTIFS({range:contracts.signed_on},">="&EDATE(%s,%d),{range:contracts.signed_on},"<"&EDATE(%s,%d))' % (MS, a, MS, b)
TREND15 = 'MIN(1.3,MAX(0.7,IFERROR(%s/%s,1)))' % (CT(-6, 0), CT(-18, -12))
SCN15 = 'IF({in:scn}=%s,1.15,IF({in:scn}=%s,0.85,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
F15 = '%s*%s*(1+{in:adj})' % (TREND15, SCN15)
def EXP15(kind): return '%s*%s' % (CK6(kind, -11, -8), F15)
TOT15 = '(%s+%s+%s)' % (EXP15(BIR), EXP15(POS), EXP15(COM))
tools.append(TOOL('sales_fc', 'Package Sales Forecast', 'How many packages to expect in the next 3 months',
    'Pick a Base, Best or Worst scenario: the same 3 months a year ago by kind times your growth of the last 6 months against the 6 months a year earlier, set against your last 3 months.', [
    IL('scn', 'Scenario', 'scen', 'Base'), I('adj', 'Your own change on top of the trend', 0.0, 'pct')], [
    O('Birth contracts a month, last 6 months', 'num', '%s/6' % CK6(BIR, -6, 0)), O('Postpartum contracts a month, last 6 months', 'num', '%s/6' % CK6(POS, -6, 0)),
    O('Combined contracts a month, last 6 months', 'num', '%s/6' % CK6(COM, -6, 0)), O('Contracts, last 6 months', 'int', CT(-6, 0)), O('Contracts, the same 6 months a year earlier', 'int', CT(-18, -12)),
    O('Growth factor, capped 0.7 to 1.3', 'num', TREND15), O('Same 3 months a year ago, birth', 'int', CK6(BIR, -11, -8)), O('Same 3 months a year ago, postpartum', 'int', CK6(POS, -11, -8)),
    O('Same 3 months a year ago, combined', 'int', CK6(COM, -11, -8)), O('Expected birth packages, next 3 months', 'num', EXP15(BIR)), O('Expected postpartum packs, next 3 months', 'num', EXP15(POS)),
    O('Expected combined packages, next 3 months', 'num', EXP15(COM)), O('Expected contracts, next 3 months', 'num', TOT15), O('Contracts, last 3 months', 'int', CT(-3, 0)),
    O('Expected income, at the average price of 90 days', 'money', '%s*IFERROR(AVERAGEIFS({range:contracts.price},{range:contracts.signed_on},%s),0)' % (TOT15, D90)),
    O('Verdict', 'text', 'IF(%s>%s*1.05,%s,IF(%s<%s*0.95,%s,%s))' % (TOT15, CT(-3, 0), v2('Sales are rising'), TOT15, CT(-3, 0), v2('Sales are falling'), v2('Sales are flat')))],
    GR('What if', ('Best scenario', {'scn': '=' + tok('scen', 'Best')}), ('Worst scenario', {'scn': '=' + tok('scen', 'Worst')}), ('10 percent more on top', {'adj': 0.10}), ('15 percent less on top', {'adj': -0.15}),
       ('Best scenario and 10 percent more', {'scn': '=' + tok('scen', 'Best'), 'adj': 0.10}))))

# 16 ----------------------------------------------------------- on-call length effect
OCN = 'COUNTIFS({range:hours.oncall_hours},">0")'
OCH = 'SUMIFS({range:hours.oncall_hours},{range:hours.oncall_hours},">0")'
OCP = 'SUMIFS({range:hours.price},{range:hours.oncall_hours},">0")'; OCM = 'SUMIFS({range:hours.mileage_cost},{range:hours.oncall_hours},">0")'; OCT = 'SUMIFS({range:hours.total_hours},{range:hours.oncall_hours},">0")'
PD16 = 'IFERROR(%s/%s/{in:cur},0)' % (OCH, OCN)
SAV16 = '(%s*({in:cur}-{in:new}))' % PD16
CL16 = '(COUNTIFS({range:contracts.kind},%s,{range:contracts.signed_on},%s)+COUNTIFS({range:contracts.kind},%s,{range:contracts.signed_on},%s))' % (BIR, D365, COM, D365)
PPH16B = 'IFERROR((%s-%s)/(%s-%s*%s),0)' % (OCP, OCM, OCT, SAV16, OCN)
tools.append(TOOL('oncall_len', 'On-Call Length Effect', 'Would a shorter on-call window raise your income per hour',
    'Type the on-call window you use now (the days around the estimated due date when the doula keeps themselves free), a shorter window, and the share of your births you checked in your own birth log that fall inside it; see the contact hours saved and the income per hour.', [
    I('cur', 'On-call window now, days', 28, 'int'), I('new', 'Shorter on-call window, days', 21, 'int'), I('covered', 'Share of your births inside the shorter window', 0.93, 'pct'), I('min_cover', 'Least share you accept', 0.90, 'pct')], [
    O('Window on your Start sheet, days', 'int', '{set:oncall_before_days}+{set:oncall_after_days}'), O('Clients with on-call contact hours', 'int', OCN), O('Contact hours per window', 'num', 'IFERROR(%s/%s,0)' % (OCH, OCN)),
    O('Contact hours per window day', 'num', PD16), O('Contact hours saved per client', 'num', SAV16), O('Clients with a window, last 12 months', 'int', CL16), O('Contact hours saved a year', 'num', '%s*%s' % (SAV16, CL16)),
    O('Free days gained per client', 'int', '{in:cur}-{in:new}'), O('Free days gained a year', 'int', '({in:cur}-{in:new})*%s' % CL16),
    O('Income per hour now, clients with a window', 'money', 'IFERROR((%s-%s)/%s,0)' % (OCP, OCM, OCT)), O('Income per hour with the shorter window', 'money', PPH16B),
    O('Gain per hour', 'money', '%s-IFERROR((%s-%s)/%s,0)' % (PPH16B, OCP, OCM, OCT)),
    O('Verdict', 'text', 'IF(AND({in:covered}>={in:min_cover},{in:new}<{in:cur}),%s,%s)' % (v2('Shorten the window'), v2('Keep the window')))],
    GR('What if', ('Window of 14 days', {'new': 14}), ('Window of 24 days', {'new': 24}), ('Only 85 percent inside', {'covered': 0.85}), ('Accept 80 percent', {'covered': 0.85, 'min_cover': 0.80}),
       ('Longer window of 35 days', {'new': 35}))))

# 17 ----------------------------------------------------------- local range position
PK17 = '{in:package}'
VAL17 = 'IF(%s=%s,IF(IF({in:try}>0,{in:try},%s)>0,IF({in:try}>0,{in:try},%s)/%s,0),IF({in:try}>0,{in:try},%s))' % (PFT('kind', PK17), POS, PKP('price', PK17), PKP('price', PK17), PKP('plan_hours', PK17), PKP('price', PK17))
LO17, HI17 = PFN('range_low', PK17), PFN('range_high', PK17)
tools.append(TOOL('range_pos', 'Local Range Position', 'Is this price below, inside or above your local range',
    'Pick a package and type a price to test (0 keeps the list price): the price is compared with the low and high of your own local range for its kind, a price per hour for postpartum and night packs, with how many packages sit in each band.', [
    IL('package', 'Package or add-on', 'package', 'Birth Premier'), I('try', 'Price to test, 0 uses the list price', 0)], [
    O('Kind of range used', 'text', PFT('range_row', PK17)), O('List price', 'money', PKP('price', PK17)), O('Value compared, price or price per hour', 'money', VAL17), O('Local low', 'money', LO17), O('Local high', 'money', HI17),
    O('Position in the range, 0 low to 1 high', 'num', 'IFERROR((%s-%s)/(%s-%s),0)' % (VAL17, LO17, HI17, LO17)), O('Amount above the high', 'money', 'MAX(0,%s-%s)' % (VAL17, HI17)),
    O('Amount below the low', 'money', 'MAX(0,%s-%s)' % (LO17, VAL17)), O('Packages inside the range', 'int', 'COUNTIFS({range:pk_profit.range_check},%s)' % ck('Inside the range')),
    O('Packages above the range', 'int', 'COUNTIFS({range:pk_profit.range_check},%s)' % ck('Above the range')), O('Packages below the range', 'int', 'COUNTIFS({range:pk_profit.range_check},%s)' % ck('Below the range')),
    O('Income per hour of this package', 'money', PFN('actual_pph', PK17)),
    O('Verdict', 'text', 'IF(%s<%s,%s,IF(%s>%s,%s,%s))' % (VAL17, LO17, ck('Below the range'), VAL17, HI17, ck('Above the range'), ck('Inside the range')))],
    GR('What if', ('Complete Care Bundle', {'package': '=' + tok('package', 'Complete Care Bundle')}), ('Postpartum 120 Hours', {'package': '=' + tok('package', 'Postpartum 120 Hours')}),
       ('Night Support 60 Hours', {'package': '=' + tok('package', 'Night Support 60 Hours')}), ('Birth Premier at 2,100', {'try': 2100}), ('Birth Essential at 900', {'package': '=' + tok('package', 'Birth Essential'), 'try': 900}),
       ('Debrief visit', {'package': '=' + tok('package', 'Debrief visit')}))))

# 18 ----------------------------------------------------------- sensitivity row
AV18, MI18, HR18 = AVG('price', P1), AVG('mileage_cost', P1), AVG('total_hours', P1)
BASE18 = PPH(AV18, MI18, HR18)
PU = PPH('(%s)*(1+{in:ps})' % AV18, MI18, HR18); PD = PPH('(%s)*(1-{in:ps})' % AV18, MI18, HR18)
HU = PPH(AV18, MI18, '(%s)*(1+{in:hs})' % HR18); HD = PPH(AV18, MI18, '(%s)*(1-{in:hs})' % HR18)
tools.append(TOOL('sensitivity', 'Sensitivity Row', 'Which matters more: the price or the hours',
    'Pick a package and a price step and an hours step: the income per hour when the price moves up or down and when the hours move up or down; the verdict names the input that matters most for this package.', [
    IL('package', 'Package', 'cpackage', 'Complete Care Bundle'), I('ps', 'Price step', 0.05, 'pct'), I('hs', 'Hours step', 0.10, 'pct')], [
    O('Average price paid, after discounts', 'money', AV18), O('Actual hours per client', 'num', HR18), O('Mileage cost per client', 'money', MI18), O('Income per hour now', 'money', BASE18),
    O('Income per hour with the price up', 'money', PU), O('Income per hour with the price down', 'money', PD), O('Income per hour with the hours up', 'money', HU), O('Income per hour with the hours down', 'money', HD),
    O('Effect of the price step per hour', 'money', '(%s-%s)/2' % (PU, PD)), O('Effect of the hours step per hour', 'money', '(%s-%s)/2' % (HD, HU)),
    O('Hours step equal to the price step', 'pct', 'IFERROR(({in:ps}*%s/(%s-%s))/(1+{in:ps}*%s/(%s-%s)),0)' % (AV18, AV18, MI18, AV18, AV18, MI18)), O('Gap to your target now', 'money', '%s-%s' % (BASE18, TGT)),
    O('Verdict', 'text', 'IF((%s-%s)>=(%s-%s),%s,%s)' % (PU, PD, HD, HU, v2('Price matters most'), v2('Hours matter most')))],
    GR('What if', ('Price step 2 percent', {'ps': 0.02}), ('Price step 10 percent', {'ps': 0.10}), ('Hours step 20 percent', {'hs': 0.20}), ('Birth Plus', {'package': PKG('Birth Plus')}),
       ('Postpartum 80 Hours', {'package': PKG('Postpartum 80 Hours')}))))
assert len(tools) == 18, len(tools)
