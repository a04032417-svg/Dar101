"""HVAC suite part 5: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv5_lists import *
import hv5_data as D
import datetime as _dt

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def SER(d): return (to_date(d) - _dt.date(1899, 12, 30)).days
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
BELOW = ck('Below minimum')
LAST3, LAST6, EARLY = tok('cperiod', 'Last 3 months'), tok('speriod', 'Last 6 counts'), tok('speriod', 'Earlier counts')
UNDER = ck('Under target'); ROSE = ck('Rose, still on target')
VAN = '{range:van_stock.van},{in:van}'
def PU30(extra=''): return '{range:parts_used.date},">="&({today}-30),{range:parts_used.date},"<="&{today}' + extra
tools = []
# 1 restock list
LN1 = 'COUNTIFS(%s,{range:van_stock.below_min},%s)' % (VAN, BELOW)
NONE = ck('None')
def TOP1(k, col, bl='""'): return 'IFERROR(INDEX({range:van_stock.%s},MATCH({in:van}&"|"&%d,{range:van_stock.van_rank_key},0)),%s)' % (col, k, bl)
O1 = [O('Parts below minimum on this van', 'int', LN1), O('Units to order to reach the maximum', 'int', 'SUMIFS({range:van_stock.restock_qty},%s)' % VAN), O('Restock cost for this van', 'money', 'SUMIFS({range:van_stock.restock_cost},%s)' % VAN),
      O('Next supplier run, all vans, parts counter', 'money', 'SUMIFS({range:van_stock.restock_cost},{range:van_stock.supplier},%s)' % tok('supplier', 'Your parts counter')),
      O('Parts below minimum, all vans', 'int', 'COUNTIFS({range:van_stock.below_min},%s)' % BELOW), O('Share of the run on this van', 'pct', 'IFERROR(SUMIFS({range:van_stock.restock_cost},%s)/SUM({range:van_stock.restock_cost}),0)' % VAN)]
for k in range(1, 5): O1 += [O('%d. Part to order' % k, 'text', TOP1(k, 'part', NONE)), O('%d. Quantity to order' % k, 'int', 'IFERROR(VALUE(%s),0)' % TOP1(k, 'restock_qty'))]
O1.append(O('Verdict', 'text', 'IF(%s>={set:order_lines},%s,IF(%s>0,%s,%s))' % (LN1, ck('Order today'), LN1, ck('Next run'), ck('Stocked'))))
tools.append(TOOL('restock_tool', 'Van Stock Restock List', 'Which parts to order for a van and what the run costs',
  'Pick a van: the parts below the minimum, the quantity to reach the maximum, the cost, the supplier run total and an order-today or next-run verdict. The what-if rows walk through every van.', [
    IN('van', 'Van', 'list', key('van', 'Van 4'), list='van')], O1, GR('Every van', *[(v, {'van': '=' + tok('van', v)}) for v in VAN_NAMES])))
# 2 stock count variance
CV = '{range:stock_counts.van},{in:van},{range:stock_counts.date},{in:cdate}'
def TOPC(k, col, bl='""'): return 'IFERROR(INDEX({range:stock_counts.%s},MATCH({in:van}&"|"&{in:cdate}&"|"&%d,{range:stock_counts.miss_rank_key},0)),%s)' % (col, k, bl)
OV = 'COUNTIFS(%s,{range:stock_counts.missing_value},">"&{in:tolerance})' % CV
O2 = [O('Lines counted', 'int', 'COUNTIFS(%s)' % CV), O('Lines short', 'int', 'COUNTIFS(%s,{range:stock_counts.variance},"<0")' % CV), O('Stock missing, value', 'money', 'SUMIFS({range:stock_counts.missing_value},%s)' % CV),
      O('Stock over expected, value', 'money', 'SUMIFS({range:stock_counts.variance_value},%s,{range:stock_counts.variance},">0")' % CV), O('Net variance, value', 'money', 'SUMIFS({range:stock_counts.variance_value},%s)' % CV),
      O('Lines missing more than the tolerance', 'int', OV)]
for k in range(1, 5): O2 += [O('%d. Part with the largest gap' % k, 'text', TOPC(k, 'part', NONE)), O('%d. Value missing' % k, 'money', 'IFERROR(VALUE(%s),0)' % TOPC(k, 'missing_value'))]
O2.append(O('Verdict', 'text', 'IF(%s>=3,%s,IF(%s>=1,%s,%s))' % (OV, ck('Investigate'), OV, ck('Recount'), ck('Fine'))))
tools.append(TOOL('count_variance', 'Stock Count Variance', 'Expected against counted: which gaps need a recount',
  'Pick a van, a count date and a tolerance: the gap in money, the four largest gaps and a recount, investigate or fine verdict. The what-if rows change the van, the date and the tolerance.', [
    IN('van', 'Van', 'list', key('van', 'Van 4'), list='van'), I('cdate', 'Count date', D.LATEST, 'date'), I('tolerance', 'Tolerance for one part line', 25)], O2,
  GR('What if', ('Van 1, same count', {'van': '=' + tok('van', 'Van 1')}), ('Van 5, same count', {'van': '=' + tok('van', 'Van 5')}), ('Van 4 earlier count', {'cdate': SER(D.COUNT_DATES[-2])}),
     ('Tolerance 100', {'tolerance': 100}), ('Tolerance 10', {'tolerance': 10}))))
# 3 shrink by van and technician
SM = '{range:shrink_van.van},{in:van},{range:shrink_van.period},%s'
def SH(col, per): return 'SUMIFS({range:shrink_van.%s},{range:shrink_van.van},{in:van},{range:shrink_van.period},%s)' % (col, per)
SHARE3 = 'IFERROR(%s/%s,0)' % (SH('missing', LAST6), SH('stock_value', LAST6))
SHOP3 = 'IFERROR(SUMIFS({range:shrink_van.missing},{range:shrink_van.period},%s)/SUMIFS({range:shrink_van.stock_value},{range:shrink_van.period},%s),0)' % (LAST6, LAST6)
tools.append(TOOL('shrink_tool', 'Shrink by Van and Tech', 'Stock missing between counts, ranked by van and technician',
  'Pick a van: stock missing over the last 6 counts (shrink), its share of the van stock value against the shop, the cost a month and a verdict against your shrink target.', [
    IN('van', 'Van', 'list', key('van', 'Van 4'), list='van')], [
    O('Technician who drives the van', 'text', 'IFERROR(INDEX({range:shrink_van.technician},MATCH({in:van},{range:shrink_van.van},0)),"")'), O('Stock missing, last 6 counts', 'money', SH('missing', LAST6)),
    O('Van stock value', 'money', SH('stock_value', LAST6)), O('Shrink share of stock value', 'pct', SHARE3), O('Shop average share', 'pct', SHOP3), O('Gap to the shop, points', 'pct', SHARE3 + '-' + SHOP3),
    O('Shrink target', 'pct', '{set:shrink_target}'), O('Cost a month', 'money', SH('per_month', LAST6)), O('Cost a year at this pace', 'money', SH('per_month', LAST6) + '*12'),
    O('Rank of the van, 1 is the most missing', 'int', 'COUNTIFS({range:shrink_van.period},%s,{range:shrink_van.missing},">"&%s)+1' % (LAST6, SH('missing', LAST6))),
    O('Van with the most missing', 'text', 'IFERROR(INDEX({range:shrink_van.van},MATCH(MAX({range:shrink_van.last_missing}),{range:shrink_van.last_missing},0)),"")'),
    O('Missing at the latest count', 'money', 'SUMIFS({range:stock_counts.missing_value},{range:stock_counts.van},{in:van},{range:stock_counts.date},MAX({range:stock_counts.date}))'),
    O('Missing in the counts before, a month', 'money', SH('per_month', EARLY)), O('Stock missing, all vans, last 6 counts', 'money', 'SUMIFS({range:shrink_van.missing},{range:shrink_van.period},%s)' % LAST6),
    O('Verdict', 'text', 'IF(%s>{set:shrink_target}*2,%s,IF(%s>{set:shrink_target},%s,%s))' % (SHARE3, ck('Investigate the van'), SHARE3, ck('Watch the next count'), ck('Within tolerance')))],
  GR('Every van', *[(v, {'van': '=' + tok('van', v)}) for v in VAN_NAMES])))
# 4 stock value and turnover
USE4 = 'SUMIFS({range:parts_used.cost},{range:parts_used.van},{in:van},{range:parts_used.from_van},%s,%s)' % (YES, '{range:parts_used.date},">="&({today}-30),{range:parts_used.date},"<="&{today}')
VAL4 = 'SUMIFS({range:van_stock.value},%s)' % VAN
MH4 = 'IFERROR(%s/%s,0)' % (VAL4, USE4)
ALLUSE = 'SUMIFS({range:parts_used.cost},{range:parts_used.from_van},%s,%s)' % (YES, '{range:parts_used.date},">="&({today}-30),{range:parts_used.date},"<="&{today}')
tools.append(TOOL('stock_turnover', 'Van Stock Turnover', 'Is the van carrying too much stock or too little?',
  'Pick a van: stock value, parts used from the van in 30 days, the months of stock held against your high and low limits, the stock to cut or add and a verdict.', [
    IN('van', 'Van', 'list', key('van', 'Van 6'), list='van')], [
    O('Stock value on the van', 'money', VAL4), O('Parts used from the van, last 30 days', 'money', USE4), O('Months of stock held', 'num', MH4),
    O('Months of stock held, all vans', 'num', 'IFERROR(SUM({range:van_stock.value})/%s,0)' % ALLUSE), O('Too much above', 'num', '{set:months_high}'), O('Too little below', 'num', '{set:months_low}'),
    O('Stock above the high limit, value', 'money', 'MAX(0,%s-%s*{set:months_high})' % (VAL4, USE4)), O('Stock to add to reach the low limit, value', 'money', 'MAX(0,%s*{set:months_low}-%s)' % (USE4, VAL4)),
    O('Parts lines on the van', 'int', 'COUNTIFS(%s)' % VAN), O('Lines below minimum', 'int', 'COUNTIFS(%s,{range:van_stock.below_min},%s)' % (VAN, BELOW)),
    O('Parts used a week', 'money', USE4 + '/30*7'),
    O('Verdict', 'text', 'IF(%s>{set:months_high},%s,IF(%s<{set:months_low},%s,%s))' % (MH4, ck('Too much stock'), MH4, ck('Too little stock'), ck('Right')))],
  GR('Every van', *[(v, {'van': '=' + tok('van', v)}) for v in VAN_NAMES])))
# 5 short-stock van finder
JN = 'SUMIFS({range:vehicle_van.jobs_next_week},{range:vehicle_van.van},{in:van},{range:vehicle_van.period},%s)' % LAST3
tools.append(TOOL('short_stock', 'Short-Stock Van Finder', 'Which vans are short, and which jobs next week are at risk',
  'Pick a van: its parts below minimum, the jobs booked in the next 7 days, the jobs at risk from short stock and the supplier run to fix it; the totals show every van at once.', [
    IN('van', 'Van', 'list', key('van', 'Van 4'), list='van')], [
    O('Parts below minimum on the van', 'int', LN1), O('Jobs booked in the next 7 days', 'int', JN), O('Jobs at risk from short stock', 'int', 'IF(%s>0,%s,0)' % (LN1, JN)),
    O('Supplier run to fix the van', 'money', 'SUMIFS({range:van_stock.restock_cost},%s)' % VAN), O('Vans with parts below minimum', 'int', 'COUNTIFS({range:shrink_van.period},%s,{range:shrink_van.below_lines},">0")' % LAST6),
    O('Jobs at risk, all vans', 'int', 'SUMIFS({range:vehicle_van.jobs_at_risk},{range:vehicle_van.period},%s)' % LAST3), O('Supplier run, all vans', 'money', 'SUM({range:van_stock.restock_cost})'),
    O('Van with the most lines below minimum', 'text', 'IFERROR(INDEX({range:shrink_van.van},MATCH(MAX({range:shrink_van.below_lines}),{range:shrink_van.below_lines},0)),"")'),
    O('Run the order by', 'date', 'WORKDAY({today},1)'),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>={set:order_lines},%s,%s))' % (LN1, ck('Clear to dispatch'), LN1, ck('Restock before dispatch'), ck('Check the parts first')))],
  GR('Every van', *[(v, {'van': '=' + tok('van', v)}) for v in VAN_NAMES])))
# 6 supplier price change log
KC = 'MATCH(LARGE({range:price_changes.order_key},{in:rank}),{range:price_changes.order_key},0)'
def PCI(col): return 'IFERROR(INDEX({range:price_changes.%s},%s),"")' % (col, KC)
P12 = '{range:price_changes.date},">="&({today}-365)'
tools.append(TOOL('price_log', 'Supplier Price Change Log', 'What each supplier price change cost and when it started',
  'Type a rank (1 is the newest change): the part, the old and new cost, the rise, the month it started, the jobs a year that use it and the extra cost a year; the totals cover the last 12 months.', [
    I('rank', 'Change, 1 is the newest', 1, 'int')], [
    O('Part', 'text', PCI('part')), O('Changed on', 'date', PCI('date')), O('Old cost', 'money', PCI('old_cost')), O('New cost', 'money', PCI('new_cost')), O('Rise', 'pct', PCI('rise')), O('Month it started', 'date', PCI('month')),
    O('Jobs a year that use the part', 'int', PCI('jobs_year')), O('Extra cost a year', 'money', PCI('extra_year')),
    O('Price changes, last 12 months', 'int', 'COUNTIFS(%s)' % P12), O('Average rise, last 12 months', 'pct', 'IFERROR(AVERAGEIFS({range:price_changes.rise},%s),0)' % P12),
    O('Extra cost a year, all changes', 'money', 'SUM({range:price_changes.extra_year})'), O('Largest rise', 'pct', 'MAX({range:price_changes.rise})'),
    O('Part with the largest rise', 'text', 'IFERROR(INDEX({range:price_changes.part},MATCH(MAX({range:price_changes.rise}),{range:price_changes.rise},0)),"")'),
    O('Verdict', 'text', 'IF(%s>=0.1,%s,IF(%s>={set:rise_alert},%s,%s))' % (PCI('rise'), ck('Update the price book now'), PCI('rise'), ck('Check the price book'), ck('Small change')))],
  GR('Which change', ('Newest', {'rank': 1}), ('Second newest', {'rank': 2}), ('Fifth', {'rank': 5}), ('Tenth', {'rank': 10}), ('Twentieth', {'rank': 20}))))
# 7 price book and estimate impact
def TOPL(k, col): return 'IFERROR(INDEX({range:price_book.%s},MATCH(LARGE({range:price_book.risk_key},%d),{range:price_book.risk_key},0)),"")' % (col, k)
def TOPE(k, col): return 'IFERROR(INDEX({range:estimates_open.%s},MATCH(LARGE({range:estimates_open.risk_key},%d),{range:estimates_open.risk_key},0)),"")' % (col, k)
O7 = [O('Price-book lines under the margin wanted', 'int', 'COUNTIFS({range:price_book.status},%s)' % UNDER), O('Lines that rose and still hold the margin', 'int', 'COUNTIFS({range:price_book.status},%s)' % ROSE),
      O('Money at risk a year on the price book', 'money', 'SUM({range:price_book.at_risk})'), O('Open estimates under the margin wanted', 'int', 'COUNTIFS({range:estimates_open.status},%s)' % UNDER),
      O('Money at risk on open estimates', 'money', 'SUM({range:estimates_open.at_risk})')]
for k in range(1, 4): O7 += [O('%d. Line to re-price' % k, 'text', TOPL(k, 'task')), O('%d. Flat price needed' % k, 'money', 'IFERROR(VALUE(%s),0)' % TOPL(k, 'price_needed'))]
O7 += [O('Flat price now, line 1', 'money', 'IFERROR(VALUE(%s),0)' % TOPL(1, 'flat_price')), O('Rise needed, line 1', 'pct', 'IFERROR(VALUE(%s)/VALUE(%s)-1,0)' % (TOPL(1, 'price_needed'), TOPL(1, 'flat_price'))),
       O('Flat price with your extra margin points, line 1', 'money', 'IFERROR(VALUE(%s)/(1-VALUE(%s)-{in:buffer}),0)' % (TOPL(1, 'cost'), TOPL(1, 'target_margin'))),
       O('Open estimate most at risk', 'text', TOPE(1, 'estimate_id')),
       O('Verdict', 'text', 'IF(COUNTIFS({range:price_book.status},%s)>0,%s,%s)' % (UNDER, ck('Raise price'), ck('Hold')))]
tools.append(TOOL('margin_impact', 'Price Change Margin Impact', 'Price-book lines under margin after a price rise',
  'Type extra margin points: the price-book lines and open estimates now under the margin wanted, ranked by money at risk, the flat price that restores it and a raise-price or hold verdict.', [
    I('buffer', 'Extra margin points on top', 0.02, 'pct')], O7, GR('What if', ('No extra points', {'buffer': 0}), ('Add 5 points', {'buffer': 0.05}), ('Add 8 points', {'buffer': 0.08}))))
# 8 parts cost trend
def RISE(cat): return 'IFERROR(SUMIFS({range:parts.year_spend},{range:parts.category},%s)/SUMIFS({range:parts.spend_old},{range:parts.category},%s)-1,0)' % (cat, cat)
CATS5 = [('Heating', tok('partcat', 'Heating')), ('Cooling', tok('partcat', 'Cooling')), ('Plumbing', tok('partcat', 'Plumbing')), ('Consumable', tok('partcat', 'Consumable')), ('Equipment', tok('partcat', 'Equipment'))]
MX8 = 'MAX(%s)' % ','.join(RISE(t) for _, t in CATS5)
NAME8 = ck(CATS5[4][0])
for i in range(3, -1, -1):
    n, t = CATS5[i]
    NAME8 = 'IF(%s>=MAX(%s),%s,%s)' % (RISE(t), ','.join(RISE(x) for _, x in CATS5[i + 1:]), ck(n), NAME8)
tools.append(TOOL('cost_trend', 'Parts Cost Trend', 'Which category of parts rose most in 12 months',
  'Pick a category: its cost rise over 12 months weighted by what you used, the extra cost a year and every category side by side; the verdict names the category to re-price first.', [
    IN('category', 'Part category', 'list', key('partcat', 'Plumbing'), list='partcat')], [
    O('Cost rise of the chosen category, 12 months', 'pct', RISE('{in:category}')), O('Spend, 12 months, at today cost', 'money', 'SUMIFS({range:parts.year_spend},{range:parts.category},{in:category})'),
    O('Extra cost a year from the rise', 'money', 'SUMIFS({range:parts.year_spend},{range:parts.category},{in:category})-SUMIFS({range:parts.spend_old},{range:parts.category},{in:category})')] +
    [O('Cost rise, %s' % n, 'pct', RISE(t)) for n, t in CATS5] +
    [O('Cost rise, all parts', 'pct', 'IFERROR(SUM({range:parts.year_spend})/SUM({range:parts.spend_old})-1,0)'), O('Parts with a rise above your alert', 'int', 'COUNTIFS({range:parts.rise_12m},">="&{set:rise_alert})'),
     O('Category to re-price first', 'text', NAME8),
     O('Verdict', 'text', 'IF(%s>={set:rise_alert},%s,%s)' % (MX8, ck('Re-price the highest category'), ck('Costs are steady')))],
  GR('Every category', *[(n, {'category': '=' + tok('partcat', n)}) for n, _ in CATS5])))
# 9 parts markup check
SALES9 = 'SUMPRODUCT(({range:parts.category}={in:category})*{range:parts.year_qty}*{range:parts.unit_cost}*(1+{range:parts.markup}))'
MK9 = 'IFERROR(%s/SUMIFS({range:parts.year_spend},{range:parts.category},{in:category})-1,0)' % SALES9
def TOPM(k, col, bl='""'): return 'IFERROR(INDEX({range:parts.%s},MATCH({in:category}&"|"&%d,{range:parts.cat_rank_key},0)),%s)' % (col, k, bl)
O9 = [O('Markup wanted', 'pct', '{set:markup_target}'), O('Markup earned in the category, weighted by use', 'pct', MK9), O('Gap to the target, points', 'pct', MK9 + '-{set:markup_target}'),
      O('Part lines in the category', 'int', 'COUNTIFS({range:parts.category},{in:category})'), O('Lines under the target', 'int', 'COUNTIFS({range:parts.category},{in:category},{range:parts.markup_gap},"<0")'),
      O('Gained a year at the target markup', 'money', 'SUMIFS({range:parts.price_gain},{range:parts.category},{in:category})')]
for k in range(1, 4): O9 += [O('%d. Line under target' % k, 'text', TOPM(k, 'part', NONE)), O('%d. Spend, 12 months' % k, 'money', 'IFERROR(VALUE(%s),0)' % TOPM(k, 'year_spend'))]
O9 += [O('Lines under the target, all categories', 'int', 'COUNTIFS({range:parts.markup_gap},"<0")'), O('Gained a year, all categories', 'money', 'SUM({range:parts.price_gain})'),
       O('Verdict', 'text', 'IF(%s<{set:markup_target},%s,%s)' % (MK9, ck('Raise the markup'), ck('Markup on target')))]
tools.append(TOOL('markup_check', 'Parts Markup Check', 'Parts markup under target, ranked by yearly spend',
  'Pick a category: the markup you earn on the parts you used, the lines under your markup target ranked by yearly spend, what the target would add a year and a verdict.', [
    IN('category', 'Part category', 'list', key('partcat', 'Equipment'), list='partcat')], O9, GR('Every category', *[(n, {'category': '=' + tok('partcat', n)}) for n, _ in CATS5])))
# 10 parts cost per job
JT = '{range:parts_used.job_type},{in:jtype}'
ACT10 = 'IFERROR(SUMIFS({range:parts_used.cost},%s)/SUMIFS({range:parts_used.job_weight},%s),0)' % (JT, JT)
ASM10 = 'IFERROR(SUMIFS({range:price_book.parts_jobs},{range:price_book.job_type},{in:jtype})/SUMIFS({range:price_book.jobs_year},{range:price_book.job_type},{in:jtype}),0)'
tools.append(TOOL('parts_per_job', 'Parts Cost per Job', 'Do your price-book parts costs match what jobs really use?',
  'Pick a job type: the parts cost per job from the parts logged in the last 45 days against the parts cost in your price book, the gap and a verdict of price book too low, right or too high.', [
    IN('jtype', 'Job type', 'list', key('jobtype', 'Heating repair'), list='jobtype')], [
    O('Jobs in the parts log', 'num', 'SUMIFS({range:parts_used.job_weight},%s)' % JT), O('Parts cost in the log', 'money', 'SUMIFS({range:parts_used.cost},%s)' % JT), O('Parts cost per job, from the log', 'money', ACT10),
    O('Parts cost per job in the price book', 'money', ASM10), O('Gap per job', 'money', ACT10 + '-' + ASM10), O('Gap, share of the price book figure', 'pct', 'IFERROR(%s/%s-1,0)' % (ACT10, ASM10)),
    O('Parts taken from the van, share of cost', 'pct', 'IFERROR(SUMIFS({range:parts_used.cost},%s,{range:parts_used.from_van},%s)/SUMIFS({range:parts_used.cost},%s),0)' % (JT, YES, JT)),
    O('Unbilled parts on this job type', 'money', 'SUMIFS({range:parts_used.cost},%s,{range:parts_used.from_van},%s,{range:parts_used.billed},%s)' % (JT, YES, NO)),
    O('Price-book lines for the job type', 'int', 'COUNTIFS({range:price_book.job_type},{in:jtype})'),
    O('Verdict', 'text', 'IF(%s>0.1,%s,IF(%s<-0.1,%s,%s))' % ('IFERROR(%s/%s-1,0)' % (ACT10, ASM10), ck('Price book too low'), 'IFERROR(%s/%s-1,0)' % (ACT10, ASM10), ck('Price book too high'), ck('Price book right')))],
  GR('Job types', *[(j, {'jtype': '=' + tok('jobtype', j)}) for j in ('Heating repair', 'Cooling repair', 'Water heater replacement', 'Leak repair', 'Drain clearing', 'Fixture install')])))
# 11 unbilled parts finder
UB = '{range:parts_used.from_van},%s,{range:parts_used.billed},%s,{range:parts_used.date},">="&({today}-{in:weeks}*7),{range:parts_used.date},"<="&{today}' % (YES, NO)
def UBT(t): return 'SUMIFS({range:parts_used.cost},{range:parts_used.technician},%s,%s)' % (tok('tech', t), UB)
O11 = [O('Unbilled parts lines in the window', 'int', 'COUNTIFS(%s)' % UB), O('Money leaked in the window', 'money', 'SUMIFS({range:parts_used.cost},%s)' % UB), O('Money leaked a week', 'money', 'SUMIFS({range:parts_used.cost},%s)/{in:weeks}' % UB)]
O11 += [O('Unbilled, %s' % t, 'money', UBT(t)) for t in TECH6]
O11 += [O('Technician of the largest unbilled line', 'text', 'IFERROR(INDEX({range:unbilled.technician},1),"")'), O('Highest technician, share of unbilled', 'pct', 'IFERROR(MAX(%s)/SUMIFS({range:parts_used.cost},%s),0)' % (','.join(UBT(x) for x in TECH6), UB)), O('Unbilled parts, last 12 months', 'money', 'SUMIFS({range:stock_month.unbilled_cost},{range:stock_month.month},">="&EDATE(%s,-12))' % MS),
        O('Largest unbilled line', 'text', 'IFERROR(INDEX({range:unbilled.job_id},1)&" "&INDEX({range:unbilled.part},1),"")'), O('Unbilled, share of parts taken from vans', 'pct', 'IFERROR(SUMIFS({range:parts_used.cost},%s)/SUMIFS({range:parts_used.cost},{range:parts_used.from_van},%s,{range:parts_used.date},">="&({today}-{in:weeks}*7)),0)' % (UB, YES)),
        O('Verdict', 'text', 'IF(SUMIFS({range:parts_used.cost},%s)/{in:weeks}>={set:unbilled_alert},%s,%s)' % (UB, ck('Bill these parts now'), ck('Under control')))]
tools.append(TOOL('unbilled_tool', 'Unbilled Parts Finder', 'Parts that left the van and never reached an invoice',
  'Type the weeks to look back: parts used and not billed, the money leaked a week, the technician with the most and a verdict against your weekly alert.', [
    I('weeks', 'Weeks to look back', 6, 'int')], O11, GR('What if', ('2 weeks', {'weeks': 2}), ('4 weeks', {'weeks': 4}), ('6 weeks', {'weeks': 6}))))
# 12 parts usage forecast
H12 = '{range:stock_month.month},">="&EDATE(%s,-12),{range:stock_month.month},"<"&%s' % (MS, MS)
BASE12 = 'SUMIFS({range:stock_month.parts_cost},%s)/12' % H12
IDX12 = 'IFERROR(AVERAGEIFS({range:stock_month.parts_cost},{range:stock_month.season},{in:season},%s)/(%s),1)' % (H12, BASE12)
CURS = 'INDEX({range:stock_month.season},MATCH(%s,{range:stock_month.month},0))' % MS
IDXN = 'IFERROR(AVERAGEIFS({range:stock_month.parts_cost},{range:stock_month.season},%s,%s)/(%s),1)' % (CURS, H12, BASE12)
USE12 = 'SUMIFS({range:parts_used.cost},{range:parts_used.van},{in:van},{range:parts_used.from_van},%s,%s)' % (YES, '{range:parts_used.date},">="&({today}-30),{range:parts_used.date},"<="&{today}')
FC12 = '(%s)*(%s)/(%s)*(1+{in:growth})' % (USE12, IDX12, IDXN)
HOLD12 = '(%s)*{in:cover}/4.33' % FC12
CUR12 = 'SUMIFS({range:van_stock.value},%s)' % VAN
O12 = [O('Average parts cost a month, last 12 months', 'money', BASE12), O('Seasonal index of the chosen season', 'num', IDX12), O('Seasonal index of this month', 'num', IDXN),
       O('Parts used from this van, last 30 days', 'money', USE12), O('Parts the van needs in a month of the season', 'money', FC12),
       O('Stock to hold on the van, Base', 'money', HOLD12), O('Stock to hold on the van, Best', 'money', HOLD12 + '*(1-{in:best})'), O('Stock to hold on the van, Worst', 'money', HOLD12 + '*(1+{in:worst})'),
       O('Stock on the van now', 'money', CUR12), O('Stock to add, Base', 'money', 'MAX(0,%s-%s)' % (HOLD12, CUR12)), O('Stock to add, Best', 'money', 'MAX(0,%s*(1-{in:best})-%s)' % (HOLD12, CUR12)),
       O('Stock to add, Worst', 'money', 'MAX(0,%s*(1+{in:worst})-%s)' % (HOLD12, CUR12)),
       O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (HOLD12, CUR12, ck('Stock up before the season'), ck('Enough stock')))]
tools.append(TOOL('parts_forecast', 'Parts Usage Forecast', 'How much stock each van should hold before the season',
  'Pick a season and a van: parts used from the van in 30 days scaled by your own seasonal index give the stock to hold, with Base, Best and Worst rows, the stock to add and a stock-up or enough verdict.', [
    IN('season', 'Season', 'list', key('season', 'Heating season'), list='season'), IN('van', 'Van', 'list', key('van', 'Van 4'), list='van'), I('cover', 'Weeks of parts to hold', 4, 'num'),
    I('growth', 'Growth in work on last year', 0.03, 'pct'), I('best', 'Best case, less demand', 0.15, 'pct'), I('worst', 'Worst case, more demand', 0.25, 'pct')], O12,
  GR('What if', ('Cooling season', {'season': '=' + tok('season', 'Cooling season')}), ('Van 1', {'van': '=' + tok('van', 'Van 1')}), ('Van 5', {'van': '=' + tok('van', 'Van 5')}),
     ('8 weeks of parts', {'cover': 8}), ('No growth', {'growth': 0}))))
# 13 vehicle cost per van
VW = '{range:vehicle_costs.van},{in:van},{range:vehicle_costs.month},">="&EDATE(%s,-3),{range:vehicle_costs.month},"<"&%s' % (MS, MS)
def VC(col): return 'SUMIFS({range:vehicle_costs.%s},%s)' % (col, VW)
VV = '{range:vehicle_van.van},{in:van},{range:vehicle_van.period},%s' % LAST3
PD13 = 'IFERROR(SUMIFS({range:vehicle_van.per_day},%s),0)' % VV
SH13 = 'SUMIFS({range:vehicle_van.shop_per_day},%s)' % VV
tools.append(TOOL('vehicle_tool', 'Vehicle Cost per Van', 'What each van costs per working day and per job',
  'Pick a van: its fuel, repairs, tyres, lease and insurance for the last 3 months, the cost per working day and per job against the shop average and your daily budget, and a verdict.', [
    IN('van', 'Van', 'list', key('van', 'Van 4'), list='van')], [
    O('Total cost, last 3 months', 'money', VC('total')), O('Fuel', 'money', VC('fuel')), O('Repairs', 'money', VC('repairs')), O('Tyres', 'money', VC('tyres')), O('Lease', 'money', VC('lease')), O('Insurance', 'money', VC('insurance')),
    O('Working days', 'int', VC('working_days')), O('Jobs', 'int', VC('jobs')), O('Cost per working day', 'money', PD13), O('Cost per job', 'money', 'IFERROR(%s/%s,0)' % (VC('total'), VC('jobs'))),
    O('Shop cost per working day', 'money', SH13), O('Gap to the shop', 'pct', 'IFERROR(%s/%s-1,0)' % (PD13, SH13)), O('Budget per working day', 'money', '{set:vehicle_budget_day}'),
    O('Rank, 1 is the most costly per day', 'int', 'COUNTIFS({range:vehicle_van.period},%s,{range:vehicle_van.per_day},">"&%s)+1' % (LAST3, PD13)),
    O('Van with the highest cost per day', 'text', 'IFERROR(INDEX({range:vehicle_van.van},MATCH(MAX({range:vehicle_van.per_day_last}),{range:vehicle_van.per_day_last},0)),"")'),
    O('Verdict', 'text', 'IF(%s>{set:vehicle_budget_day},%s,IF(IFERROR(%s/%s-1,0)>0.15,%s,%s))' % (PD13, ck('Over budget'), PD13, SH13, ck('Above shop average'), ck('In line with the shop')))],
  GR('Every van', *[(v, {'van': '=' + tok('van', v)}) for v in VAN_NAMES])))
# 14 keep replace or add a van
R12 = 'SUMIFS({range:vehicle_van.repairs_12m},%s)' % VV
C12 = 'SUMIFS({range:vehicle_van.cost_12m},%s)' % VV
LS12 = 'IFERROR(INDEX({range:vans.lease_monthly},MATCH({in:van},{range:vans.van},0)),0)*12'
KEEP = C12
DEP = '{in:price}*(1-{in:resale})/{in:years}+{in:price}*{in:finance}/2'
REPL = '(%s-%s-%s+{in:repairs_new}+%s)' % (C12, R12, LS12, DEP)
JD14 = 'IFERROR(SUMIFS({range:vehicle_van.jobs},%s)/SUMIFS({range:vehicle_van.working_days},%s),0)' % (VV, VV)
EXTRA = '(%s+(SUMIFS({range:vehicle_van.cost_12m},{range:vehicle_van.period},%s)/6-AVERAGE({range:vans.lease_monthly})*12)+{in:tech_year})' % (DEP, LAST3)
NEED14 = '%s/({in:days_year}*{in:contribution})' % EXTRA
SAV14 = 'IFERROR((%s-%s)/%s,0)' % (KEEP, REPL, KEEP)
tools.append(TOOL('van_decision', 'Keep Replace or Add a Van', 'Keep the van, replace it or add one: what each costs a year',
  'Pick a van and type a new van price, resale share, life and finance cost: the yearly cost of keeping against replacing, the jobs a day an added van needs and a keep, replace, add or wait verdict.', [
    IN('van', 'Van', 'list', key('van', 'Van 4'), list='van'), I('price', 'Price of a new van', 48000), I('resale', 'Share of the price kept at resale', 0.3, 'pct'), I('years', 'Years you would keep a new van', 6, 'num'),
    I('finance', 'Yearly finance cost, share of the price', 0.06, 'pct'), I('repairs_new', 'Repairs a year on a new van', 900), I('tech_year', 'Yearly cost of a technician for an added van', 64000),
    I('contribution', 'Margin per job before technician cost', 330), I('days_year', 'Working days a year', 230, 'int'), I('capacity', 'Jobs a working day one van can do', 3.2, 'num')], [
    O('Running cost of the van, last 12 months', 'money', C12), O('Repairs, last 12 months', 'money', R12), O('Lease, 12 months', 'money', LS12), O('Yearly cost of keeping the van', 'money', KEEP),
    O('Cost of owning a new van a year, depreciation and finance', 'money', DEP), O('Yearly cost with a new van', 'money', REPL), O('Saving a year from replacing', 'money', KEEP + '-' + REPL), O('Saving, share of the cost of keeping', 'pct', SAV14),
    O('Jobs a working day on this van now', 'num', JD14), O('Share of van capacity used', 'pct', '%s/{in:capacity}' % JD14), O('Yearly cost of an added van with its technician', 'money', EXTRA), O('Jobs a day an added van needs', 'num', NEED14),
    O('Verdict', 'text', 'IF(%s>=0.05,%s,IF(%s/{in:capacity}>=0.9,%s,IF(%s/{in:capacity}>=0.75,%s,%s)))' % (SAV14, ck('Replace'), JD14, ck('Add a van'), JD14, ck('Wait'), ck('Keep')))],
  GR('Every van', *[(v, {'van': '=' + tok('van', v)}) for v in VAN_NAMES])))
# 15 vehicle hour rate
VN = '{range:vehicle_costs.month},">="&EDATE(%s,-{in:months}),{range:vehicle_costs.month},"<"&%s' % (MS, MS)
TOT15 = 'SUMIFS({range:vehicle_costs.total},%s)' % VN
DAY15 = 'SUMIFS({range:vehicle_costs.working_days},%s)' % VN
RATE15 = 'IFERROR(%s/(%s*{in:road_hours}),0)' % (TOT15, DAY15)
tools.append(TOOL('vehicle_hour', 'Vehicle Hour Rate', 'The vehicle cost per hour on the road for job costing',
  'Type the months and the hours on the road for a working day: the total vehicle cost over those hours gives the cost per hour, compared with the figure in Settings, with an update-the-setting verdict.', [
    I('months', 'Months to include', 12, 'int'), I('road_hours', 'Hours on the road per van per working day', 8, 'num')], [
    O('Vehicle cost in the period', 'money', TOT15), O('Van working days in the period', 'int', DAY15), O('Hours on the road', 'num', '%s*{in:road_hours}' % DAY15), O('Vehicle cost per hour', 'money', RATE15), O('Figure in Settings', 'money', '{set:vehicle_hour}'),
    O('Gap to the setting', 'pct', 'IFERROR(%s/{set:vehicle_hour}-1,0)' % RATE15), O('Jobs in the period', 'int', 'SUMIFS({range:vehicle_costs.jobs},%s)' % VN), O('Vehicle cost per job', 'money', 'IFERROR(%s/SUMIFS({range:vehicle_costs.jobs},%s),0)' % (TOT15, VN)),
    O('Fuel share of the cost', 'pct', 'IFERROR(SUMIFS({range:vehicle_costs.fuel},%s)/%s,0)' % (VN, TOT15)), O('Lease and insurance share', 'pct', 'IFERROR((SUMIFS({range:vehicle_costs.lease},%s)+SUMIFS({range:vehicle_costs.insurance},%s))/%s,0)' % (VN, VN, TOT15)),
    O('Cost a year if the setting stays', 'money', '%s*{set:vehicle_hour}*12/{in:months}' % ('%s*{in:road_hours}' % DAY15)), O('Cost a year at the rate found', 'money', '%s*12/{in:months}' % TOT15),
    O('Verdict', 'text', 'IF(ABS(IFERROR(%s/{set:vehicle_hour}-1,0))>0.1,%s,%s)' % (RATE15, ck('Update the setting'), ck('The setting is right')))],
  GR('What if', ('6 months', {'months': 6}), ('3 months', {'months': 3}), ('6 road hours', {'road_hours': 6}), ('7 road hours', {'road_hours': 7}), ('9 road hours', {'road_hours': 9}))))
# 16 tool purchase log
def TTOP(k, col): return 'IFERROR(INDEX({range:tools.%s},MATCH(LARGE({range:tools.rank_key},%d),{range:tools.rank_key},0)),"")' % (col, k)
O16 = [O('Tools logged', 'int', 'COUNTA({range:tools.tool_id})'), O('Spend, last 12 months', 'money', 'SUMIFS({range:tools.cost},{range:tools.date},">="&({today}-365))'), O('Tools past their life', 'int', 'COUNTIFS({range:tools.over_life},">=0")'),
       O('Tools due within the look-ahead', 'int', 'COUNTIFS({range:tools.over_life},">="&-{in:ahead})'), O('Cost of those tools', 'money', 'SUMIFS({range:tools.cost},{range:tools.over_life},">="&-{in:ahead})')]
for k in range(1, 6): O16 += [O('%d. Tool to replace' % k, 'text', TTOP(k, 'item') + '&" - "&' + TTOP(k, 'technician')), O('%d. Years past life' % k, 'num', 'IFERROR(VALUE(%s),0)' % TTOP(k, 'over_life'))]
O16.append(O('Verdict', 'text', 'IF(COUNTIFS({range:tools.over_life},">="&-{in:ahead})>0,%s,%s)' % (ck('Buy this season'), ck('Nothing due'))))
tools.append(TOOL('tool_log', 'Tool Purchase Log', 'Which tools are past their life and what to buy this season',
  'Type how many years ahead to look: the tools bought, the spend, the tools past their life ranked by years over, the cost to replace the ones due and a buy-this-season or nothing-due verdict.', [
    I('ahead', 'Years ahead to look', 1, 'int')], O16, GR('What if', ('Now only', {'ahead': 0}), ('2 years', {'ahead': 2}), ('3 years', {'ahead': 3}))))
# 17 tool replacement budget
Y0 = 'YEAR({today})'
def TP(col, k): return 'SUMIFS({range:tool_plan.%s},{range:tool_plan.year},%s+%d)' % (col, Y0, k)
O17 = [O('Tools due this year or already past life', 'int', TP('items_due', 0))] + [O('Tools due in year %d' % k, 'int', TP('items_due', k)) for k in range(1, 5)] + \
      [O('Budget, this year and before', 'money', TP('budget', 0))] + [O('Budget, year %d' % k, 'money', TP('budget', k)) for k in range(1, 5)] + \
      [O('Budget over 5 years', 'money', '+'.join(TP('budget', k) for k in range(5))), O('Budget over 5 years with your price rise', 'money', '(%s)*(1+{in:rise})' % '+'.join(TP('budget', k) for k in range(5))),
       O('Set aside a month for next year', 'money', '%s*(1+{in:rise})/12' % TP('budget', 1)),
       O('Verdict', 'text', 'IF(%s>0,%s,IF(%s>0,%s,%s))' % (TP('budget', 0), ck('Buy now'), TP('budget', 1), ck('Start setting money aside'), ck('No tools due soon')))]
tools.append(TOOL('tool_budget', 'Tool Replacement Budget', 'The tool budget for five years, with a price rise test',
  'Type a price rise: the tools that reach the end of their life each year from the Tools and Equipment log, the budget each year and for 5 years with your rise, the monthly set-aside and a verdict.', [
    I('rise', 'Price rise to allow', 0.10, 'pct')], O17, GR('Price rise', ('No rise', {'rise': 0}), ('5 percent', {'rise': 0.05}), ('10 percent', {'rise': 0.10}), ('20 percent', {'rise': 0.20}))))
# 18 stock-up before the season
CAT18 = 'IF({in:season}=%s,%s,IF({in:season}=%s,%s,%s))' % (tok('season', 'Heating season'), tok('partcat', 'Heating'), tok('season', 'Cooling season'), tok('partcat', 'Cooling'), tok('partcat', 'Plumbing'))
VC18 = '{range:van_stock.van},{in:van},{range:van_stock.category},%s' % CAT18
NOW18 = 'SUMIFS({range:van_stock.value},%s)' % VC18
MAX18 = 'SUMPRODUCT(({range:van_stock.van}={in:van})*({range:van_stock.category}=%s)*{range:van_stock.van_max}*{range:van_stock.unit_cost})' % CAT18
IDX18 = 'IFERROR(AVERAGEIFS({range:stock_month.parts_cost},{range:stock_month.season},{in:season},%s)/(%s),1)' % (H12, BASE12)
HOLD18 = '%s*MAX(1,%s)' % (MAX18, IDX18)
RUN18 = 'WORKDAY({in:start},-{set:season_lead_days})'
tools.append(TOOL('stock_up', 'Stock-Up Before the Season', 'Parts to hold on a van before the heating or cooling season',
  'Pick a season, a van and the season start: the category to stock, what the van holds now and at its maximum, the stock to hold, the top-up cost and the supplier run date.', [
    IN('season', 'Season', 'list', key('season', 'Heating season'), list='season'), IN('van', 'Van', 'list', key('van', 'Van 1'), list='van'), I('start', 'Season start date', iso(_dt.date(D.TD.year + (1 if D.TD.month >= 12 else 0), 12, 1)), 'date')], [
    O('Seasonal index from your last 12 months', 'num', IDX18), O('Lines of the season category on the van', 'int', 'COUNTIFS(%s)' % VC18), O('Stock of that category on the van now', 'money', NOW18),
    O('Stock at the maximum', 'money', MAX18), O('Stock to hold for the season', 'money', HOLD18), O('Top-up to buy', 'money', 'MAX(0,%s-%s)' % (HOLD18, NOW18)),
    O('Lines below minimum in that category', 'int', 'COUNTIFS(%s,{range:van_stock.below_min},%s)' % (VC18, BELOW)), O('Supplier run date', 'date', RUN18), O('Days until the run date', 'int', RUN18 + '-{today}'),
    O('Stock on the van, all categories', 'money', 'SUMIFS({range:van_stock.value},%s)' % VAN),
    O('Verdict', 'text', 'IF(%s-{today}<=0,%s,IF(%s>%s,%s,%s))' % (RUN18, ck('Order now'), HOLD18, NOW18, ck('Order on the run date'), ck('Stocked for the season')))],
  GR('What if', ('Cooling season', {'season': '=' + tok('season', 'Cooling season')}), ('Van 4', {'van': '=' + tok('van', 'Van 4')}), ('Van 5', {'van': '=' + tok('van', 'Van 5')}))))
for t, hint in ((tools[0], None),): pass
assert len(tools) == 18, len(tools)
