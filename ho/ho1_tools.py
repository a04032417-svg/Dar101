"""Home Management suite part 1: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho1_lists import *
import ho1_data as D
from ho1_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def V(*parts):
    """a verdict: words (list labels) and numbers or names joined with spaces; a tuple ('f', formula) is a value"""
    out = []
    for p in parts:
        if isinstance(p, tuple): out.append('(' + p[1] + ')')
        elif p == ', ': out.append('", "')
        else: out.append(lbl(p))
    return '&" "&'.join(out)
def F(x): return ('f', x)


W7 = '%s,">="&{today},%s,"<="&({today}+6)' % (PH('date'), PH('date'))      # people at home rows of the next 7 days
SSR = lambda c: R('shop_split', c)
RH = lambda c: R('recipe_hist', c)
STP = lambda c: R('staples', c)
SKR = lambda c: R('stock', c)
tools = []

# 1 ---------------------------------------------------------------- week plan check
MISS = 'COUNTIFS(%s,%s)' % (R('week_grid', 'flag'), V_MISS)
MAXP = 'MAX(%s)' % CL_('prep_w1')
tools.append(TOOL('plan_check', 'Week plan check', 'Is the plan for the next 7 days complete',
    'Counts the dinners planned for the next 7 days, the days with no dinner, the busiest day of prep minutes against your limit and stock to use soon that the plan does not use.', [
    I('limit', 'Busy-day limit, prep minutes in one day', 75)], [
    O('Dinners planned, next 7 days', 'int', 'COUNTIFS(%s,%s,%s)' % (MP('slot'), DIN, N7)), O('Days with no dinner, next 7 days', 'int', MISS),
    O('Prep minutes on the busiest day', 'int', MAXP), O('Busiest day', 'date', 'INDEX(%s,MATCH(%s,%s,0))' % (CL_('date'), MAXP, CL_('prep_w1'))),
    O('Days over the limit', 'int', 'COUNTIFS(%s,">"&{in:limit})' % CL_('prep_w1')),
    O('Stock to use soon that the plan does not use', 'int', 'COUNTIFS(%s,%s,%s,0)' % (SKR('status'), SOON_, SKR('in_plan'))),
    O('Verdict', 'text', 'IF(%s>0,%s,IF(%s>{in:limit},%s,%s))' % (MISS, V('Dinners missing:', F(MISS)), MAXP, V('Busy day, minutes over the limit:', F('%s-{in:limit}' % MAXP)), lbl('Plan complete')))],
    GR('What if the limit changes', ('Limit 45', {'limit': 45}), ('Limit 60', {'limit': 60}), ('Limit 90', {'limit': 90}), ('Limit 120', {'limit': 120}), ('Limit 150', {'limit': 150}))))

# 2 ---------------------------------------------------------------- servings for the week
GAPN = 'COUNTIFS(%s,"<"&{in:extra})' % PH('gap7')
MORE = '({in:extra}*%s-SUMIFS(%s,%s,"<"&{in:extra}))' % (GAPN, PH('gap7'), PH('gap7'))
LEFT = '(SUMIFS(%s,%s,">"&{in:extra})-{in:extra}*COUNTIFS(%s,">"&{in:extra}))' % (PH('gap7'), PH('gap7'), PH('gap7'))
tools.append(TOOL('servings_week', 'Servings for the week', 'Do the dinner portions match who is at home',
    'Compares the eaters in People at home with the servings of each dinner for the next 7 days; type extra eaters at every dinner to test, and see how many portions to cook more or what is left over.', [
    I('extra', 'Extra eaters at every dinner', 0)], [
    O('Eaters at home, next 7 days, with the extra', 'int', 'SUMIFS(%s,%s)+{in:extra}*COUNTIFS(%s,%s,">0")' % (PH('eaters'), W7, W7, PH('planned_servings'))),
    O('Dinner portions planned, next 7 days', 'int', 'SUMIFS(%s,%s)' % (PH('planned_servings'), W7)), O('Days short of portions', 'int', GAPN), O('Portions to cook more', 'int', MORE),
    O('Portions left over', 'int', LEFT), O('Day with the fewest spare portions', 'date', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (PH('date'), PH('gap7'), PH('gap7'))),
    O('Verdict', 'text', 'IF(%s>0,%s,IF(%s>0,%s,%s))' % (MORE, V('Cook', F(MORE), 'portions more'), LEFT, V(F(LEFT), 'portions left over'), lbl('Right size')))],
    GR('What if extra eaters join', ('Extra 0', {'extra': 0}), ('Extra 1', {'extra': 1}), ('Extra 2', {'extra': 2}), ('Extra 3', {'extra': 3}), ('Extra 4', {'extra': 4}))))

# 3 ---------------------------------------------------------------- grocery list builder
ITEMS3 = '(COUNTIFS(%s,">0")+{in:restock}*COUNTIFS(%s,">0"))' % (PN('packs'), PN('restock'))
COST3 = '(SUM(%s)+{in:restock}*SUM(%s))' % (PN('plan_cost'), PN('restock_cost'))
tools.append(TOOL('list_builder', 'Grocery list builder', 'What do we need to buy for the week plan',
    'The next 7 days of the plan give what each item needs; stock is taken off and the rest is rounded up to catalog pack sizes. Type 1 to add a restock of items under their minimum.', [
    I('restock', 'Include a restock of items under the minimum, 1 yes or 0 no', 1)], [
    O('Items the week plan needs', 'int', 'COUNTIFS(%s,1)' % PN('needs_flag')), O('Of those, already in stock', 'int', 'SUM(%s)' % PN('covered')),
    O('Items to buy for the plan', 'int', 'COUNTIFS(%s,">0")' % PN('packs')), O('Items under their minimum stock', 'int', 'COUNTIFS(%s,">0")' % PN('restock')),
    O('Items on the list', 'int', ITEMS3), O('Packs on the list', 'int', 'SUM(%s)+{in:restock}*SUM(%s)' % (PN('packs'), PN('restock'))), O('Cost line of the list', 'money', COST3),
    O('Verdict', 'text', V('Buy', F(ITEMS3), 'items, about', F('ROUND(%s,2)' % COST3)))],
    GR('Plan only or with the restock', ('Plan only', {'restock': 0}), ('Plan and restock', {'restock': 1}))))

# 4 ---------------------------------------------------------------- shop split
def SI(sh): return 'SUMIFS(%s,%s,%s)' % (SSR('items_to_buy'), SSR('shop'), sh)
def SC(sh): return 'SUMIFS(%s,%s,%s)' % (SSR('cost'), SSR('shop'), sh)
TRIPS = '+'.join('IF(%s>0,ROUNDUP(%s/{in:max_items},0),0)' % (SI(s), SI(s)) for s in (SH_W, SH_T, SH_M, tok('shop', 'Online order')))
tools.append(TOOL('shop_split_tool', 'Shop split', 'Which shop gets which items',
    'The week list divided across the weekly shop, top-up shop, market and online order from the shop set in the item catalog; type the most items you carry on one trip to see the trips needed.', [
    I('max_items', 'Most items on one trip', 30)], [
    O('Weekly shop items', 'int', SI(SH_W)), O('Top-up shop items', 'int', SI(SH_T)), O('Market items', 'int', SI(SH_M)), O('Online order items', 'int', SI(tok('shop', 'Online order'))),
    O('Weekly shop cost line', 'money', SC(SH_W)), O('Top-up shop cost line', 'money', SC(SH_T)), O('Market cost line', 'money', SC(SH_M)), O('Online order cost line', 'money', SC(tok('shop', 'Online order'))),
    O('Trips needed at that limit', 'int', TRIPS), O('Verdict', 'text', V('Weekly shop', F(SI(SH_W)), 'items, top-up', F(SI(SH_T)), 'trips', F(TRIPS)))],
    GR('What if you carry more or fewer items', ('10 items a trip', {'max_items': 10}), ('20 items a trip', {'max_items': 20}), ('30 items a trip', {'max_items': 30}), ('40 items a trip', {'max_items': 40}), ('60 items a trip', {'max_items': 60}))))

# 5 ---------------------------------------------------------------- one adult away
S5 = '({today}+{in:from_day})'; E5 = 'MIN({today}+6,{today}+{in:from_day}+{in:away_days}-1)'
DW5 = 'COUNTIFS(%s,">="&%s,%s,"<="&%s,%s,">0")' % (PH('date'), S5, PH('date'), E5, PH('planned_servings'))
PL5 = 'SUMIFS(%s,%s)' % (PH('planned_servings'), W7)
RM5 = '({in:away_adults}*%s)' % DW5
F5 = '((%s-%s)/%s)' % (PL5, RM5, PL5)
IT_NOW = 'COUNTIFS(%s,"<1")' % PN('ratio'); IT_NEW = 'COUNTIFS(%s,"<"&%s)' % (PN('ratio'), F5)
tools.append(TOOL('one_adult_away', 'One adult away', 'What changes when an adult is away for some days',
    'Type how many adults are away, from which day and for how many days: portions for the days away are removed and the items to buy are recounted from the stock cover; an estimate from your entries.', [
    I('away_adults', 'Adults away', 1), I('from_day', 'First day away, days from today', 1), I('away_days', 'Days away', 3)], [
    O('Dinners in the days away', 'int', DW5), O('Dinner portions planned, next 7 days', 'int', PL5), O('Portions removed', 'int', RM5), O('Portions after the change', 'int', '%s-%s' % (PL5, RM5)),
    O('Items to buy now', 'int', IT_NOW), O('Items to buy with fewer portions', 'int', IT_NEW), O('Fewer items to buy', 'int', '%s-%s' % (IT_NOW, IT_NEW)),
    O('Verdict', 'text', V(F(RM5), 'fewer portions,', F('%s-%s' % (IT_NOW, IT_NEW)), 'fewer items'))],
    GR('What if the days away change', ('1 day away', {'away_days': 1}), ('2 days away', {'away_days': 2}), ('3 days away', {'away_days': 3}), ('5 days away', {'away_days': 5}), ('Both adults, 3 days', {'away_adults': 2, 'away_days': 3}))))

# 6 ---------------------------------------------------------------- guests staying
EX6 = '({in:guests}*{in:nights})'; PL6 = 'SUMIFS(%s,%s)' % (PH('planned_servings'), W7)
PK6 = 'ROUNDUP(SUM(%s)*%s/%s,0)' % (PN('packs'), EX6, PL6)
tools.append(TOOL('guests_staying', 'Guests staying', 'What guests add to the shop',
    'Type the guests and the nights they eat dinner with you: the extra portions, the items that become short and the extra packs, scaled from this week plan; an estimate from your entries.', [
    I('guests', 'Guests at dinner', 2), I('nights', 'Dinners with guests', 2)], [
    O('Extra dinner portions', 'int', EX6), O('Dinner portions planned now', 'int', PL6),
    O('Items that become short', 'int', 'COUNTIFS(%s,"<"&((%s+%s)/%s))-COUNTIFS(%s,"<1")' % (PN('ratio'), PL6, EX6, PL6, PN('ratio'))),
    O('Extra packs, scaled from the plan', 'int', PK6), O('Extra cost line, scaled from the plan', 'money', 'ROUND(SUM(%s)*%s/%s,2)' % (PN('plan_cost'), EX6, PL6)),
    O('Verdict', 'text', V('Add', F(PK6), 'packs for', F('{in:guests}'), 'guests'))],
    GR('What if more guests come', ('1 guest', {'guests': 1}), ('2 guests', {'guests': 2}), ('4 guests', {'guests': 4}), ('6 guests', {'guests': 6}), ('8 guests', {'guests': 8}))))

# 7 ---------------------------------------------------------------- cook rota
def CK(col, val, extra=''): return 'COUNTIFS(%s,%s,%s,"<"&{in:days}%s)' % (CL_(col), val, CL_('day_no'), extra)
LATE7 = 'COUNTIFS(%s,1,%s,"<"&{in:days})' % (CL_('late1'), CL_('day_no'))
tools.append(TOOL('cook_rota', 'Cook rota', 'Who cooks, from adult 2 shifts and adult 1 late days',
    'The work pattern gives a suggested cook: adult 2 cooks when adult 1 is late, adult 1 cooks when adult 2 is on a Late shift, and a day when both are busy needs prep ahead.', [
    I('days', 'Days ahead, 1 to 14', 7)], [
    O('Adult 2 is the suggested cook', 'int', CK('suggested', V_A2)), O('Adult 1 is the suggested cook', 'int', CK('suggested', V_A1)), O('Either adult can cook', 'int', CK('suggested', V_EITHER)),
    O('Days to prepare ahead, both busy', 'int', CK('suggested', V_PREP)), O('Adult 1 late days', 'int', LATE7), O('Planned dinners cooked by adult 2', 'int', CK('planned_cook', A2)),
    O('Planned dinners cooked by adult 1', 'int', CK('planned_cook', A1)), O('Planned cook differs from the pattern', 'int', CK('check', V_CHECK)),
    O('Verdict', 'text', V('Adult 2 cooks', F(CK('planned_cook', A2)), 'of', F('{in:days}'), 'days, late days that need prep ahead:', F(LATE7)))],
    GR('What if you look further ahead', ('3 days', {'days': 3}), ('5 days', {'days': 5}), ('7 days', {'days': 7}), ('10 days', {'days': 10}), ('14 days', {'days': 14}))))

# 8 ---------------------------------------------------------------- busy-day meal picker
def QP(k, col): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"")' % (R('recipes', col), k, R('recipes', 'quick_rank'))
Q1M = QP(1, 'prep_min')
tools.append(TOOL('busy_picker', 'Busy-day meal picker', 'What is the quickest dinner for a late day',
    'Dinner recipes ranked by prep minutes (breakfast dishes, baking and the leftovers night are left out) with the preference label; type your limit to see how many recipes fit.', [
    I('max_prep', 'Most prep minutes on a busy day', 30)], [
    O('Dinner recipes within the limit', 'int', 'COUNTIFS(%s,"<="&{in:max_prep})' % R('recipes', 'dinner_prep')), O('Quickest dinner', 'text', QP(1, 'recipe')), O('Its prep minutes', 'int', Q1M),
    O('Second quickest', 'text', QP(2, 'recipe')), O('Its prep minutes', 'int', QP(2, 'prep_min')), O('Third quickest', 'text', QP(3, 'recipe')), O('Its prep minutes', 'int', QP(3, 'prep_min')),
    O('Preference label of the quickest', 'text', QP(1, 'pref_label')), O('Times the quickest was planned in 90 days', 'int', QP(1, 'planned_90')),
    O('Verdict', 'text', 'IF(%s<={in:max_prep},%s&" "&%s&", "&%s&" "&%s,%s)' % (Q1M, lbl('Quick pick:'), QP(1, 'recipe'), Q1M, lbl('minutes'), lbl('No dinner this quick')))],
    GR('What if the limit changes', ('20 minutes', {'max_prep': 20}), ('30 minutes', {'max_prep': 30}), ('40 minutes', {'max_prep': 40}), ('50 minutes', {'max_prep': 50}), ('60 minutes', {'max_prep': 60}))))

# 9 ---------------------------------------------------------------- prep minutes budget
OVER9 = '(SUMIFS(%s,%s,">"&{in:limit})-{in:limit}*COUNTIFS(%s,">"&{in:limit}))' % (CL_('prep_w1'), CL_('prep_w1'), CL_('prep_w1'))
tools.append(TOOL('prep_budget', 'Prep minutes budget', 'Is any day of the week too heavy to cook',
    'Total prep minutes of all meals per day for the next 7 days against your limit, with the minutes over the limit across the week; the what-if rows step the limit.', [
    I('limit', 'Prep minutes you will spend in one day', 75)], [
    O('Prep minutes, next 7 days', 'int', 'SUM(%s)' % CL_('prep_w1')), O('Average prep minutes a day', 'int', 'ROUND(AVERAGE(%s),0)' % CL_('prep_w1')), O('Prep minutes on the busiest day', 'int', MAXP),
    O('Days over the limit', 'int', 'COUNTIFS(%s,">"&{in:limit})' % CL_('prep_w1')), O('Minutes over the limit across the week', 'int', OVER9),
    O('Minutes to cut on the busiest day', 'int', 'MAX(0,%s-{in:limit})' % MAXP),
    O('Verdict', 'text', 'IF(%s<={in:limit},%s,%s)' % (MAXP, lbl('Within limit'), V('Over the limit by', F(OVER9), 'minutes in the week')))],
    GR('What if your limit changes', ('Limit 45', {'limit': 45}), ('Limit 60', {'limit': 60}), ('Limit 90', {'limit': 90}), ('Limit 120', {'limit': 120}), ('Limit 150', {'limit': 150}))))

# 10 --------------------------------------------------------------- always runs out
def SP(k, col): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"")' % (STP(col), k, STP('rank'))
tools.append(TOOL('always_runs_out', 'Always runs out', 'Which items are on the list again and again',
    'Items ranked by the weeks they were on a list in the last 26 complete weeks; type how many weeks make a standing item.', [
    I('min_weeks', 'Weeks of 26 that make a standing item', 20)], [
    O('Standing items at that limit', 'int', 'COUNTIFS(%s,">="&{in:min_weeks})' % STP('weeks')), O('Runs out most', 'text', SP(1, 'item')), O('Weeks on a list', 'int', SP(1, 'weeks')),
    O('Days since it was last bought', 'int', SP(1, 'days_since')), O('Second', 'text', SP(2, 'item')), O('Weeks on a list', 'int', SP(2, 'weeks')), O('Third', 'text', SP(3, 'item')),
    O('Weeks on a list', 'int', SP(3, 'weeks')), O('Next shop day', 'date', NEXT_SHOP),
    O('Verdict', 'text', 'IF(%s>={in:min_weeks},%s&" "&%s&" "&%s,%s)' % (SP(1, 'weeks'), lbl('Keep'), SP(1, 'item'), lbl('as a standing item'), lbl('No standing item at this limit')))],
    GR('What if the limit changes', ('10 weeks', {'min_weeks': 10}), ('15 weeks', {'min_weeks': 15}), ('20 weeks', {'min_weeks': 20}), ('24 weeks', {'min_weeks': 24}), ('26 weeks', {'min_weeks': 26}))))

# 11 --------------------------------------------------------------- pack rounding
NET11 = 'MAX(0,{in:need}-{in:on_hand})'
PK11 = 'IF(%s>0,ROUNDUP(ROUND(%s/{in:pack},6),0),0)' % (NET11, NET11)
LF11 = 'ROUND(%s*{in:pack}+{in:on_hand}-{in:need},2)' % PK11
tools.append(TOOL('pack_rounding', 'Pack rounding', 'How many packs to buy for a quantity',
    'Type the quantity you need, what you have, the pack size and the pack price: packs are rounded up and the quantity left over is shown.', [
    I('need', 'Quantity needed', 1.3, 'num'), I('on_hand', 'Quantity on hand', 0.2, 'num'), I('pack', 'Pack size', 0.5, 'num'), I('price', 'Pack price, a cost line', 1.6, 'money')], [
    O('Still to buy', 'num', NET11), O('Packs to buy', 'int', PK11), O('Quantity bought', 'num', '%s*{in:pack}' % PK11), O('Quantity left over', 'num', LF11), O('Cost line', 'money', '%s*{in:price}' % PK11),
    O('Verdict', 'text', V('Buy', F(PK11), 'packs,', F(LF11), 'left over'))],
    GR('What if the need changes', ('Need 0.5', {'need': 0.5}), ('Need 1', {'need': 1}), ('Need 1.3', {'need': 1.3}), ('Need 2', {'need': 2}), ('Need 2.6', {'need': 2.6}))))

# 12 --------------------------------------------------------------- this week's list against the last 4 complete weeks
def GWK(col, lo, hi): return 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (GL(col), GL('date'), lo, GL('date'), hi)
EST_T = GWK('est_cost', TW, '(%s+7)' % TW); EST_A = '(%s/4)' % GWK('est_cost', '(%s-28)' % TW, TW)
ITM_T = GWK('items', TW, '(%s+7)' % TW); ITM_A = '(%s/4)' % GWK('items', '(%s-28)' % TW, TW)
tools.append(TOOL('list_vs_last4', 'List vs last 4 weeks', "Is this week's list lighter or heavier than usual",
    "This week's lists (estimated cost line and items) against the average of the last 4 complete weeks on the same estimate, with a margin you type; no price advice.", [
    I('margin', 'Margin for typical', 0.15, 'pct')], [
    O('Items on this week lists', 'int', ITM_T), O('Average items, last 4 complete weeks', 'num', 'ROUND(%s,1)' % ITM_A), O('Estimated cost line this week', 'money', EST_T),
    O('Average estimated cost line, last 4 complete weeks', 'money', 'ROUND(%s,2)' % EST_A), O('Difference', 'money', 'ROUND(%s-%s,2)' % (EST_T, EST_A)),
    O('Against the average', 'pct', 'IFERROR(ROUND(%s/%s-1,3),0)' % (EST_T, EST_A)),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:margin}),%s,IF(%s<%s*(1-{in:margin}),%s,%s))' % (EST_T, EST_A, V('Heavier by', F('ROUND(%s-%s,2)' % (EST_T, EST_A))), EST_T, EST_A,
                                                                                           V('Lighter by', F('ROUND(%s-%s,2)' % (EST_A, EST_T))), lbl('Typical')))],
    GR('What if the margin changes', ('Margin 5%', {'margin': 0.05}), ('Margin 10%', {'margin': 0.1}), ('Margin 15%', {'margin': 0.15}), ('Margin 25%', {'margin': 0.25}), ('Margin 40%', {'margin': 0.4}))))

# 13 --------------------------------------------------------------- recipe rotation
def RR(k, col): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"")' % (RH(col), k, RH('rare_rank'))
NR13 = 'COUNTIFS(%s,">="&{in:days})+COUNTIFS(%s,"<>",%s,"")' % (RH('days_since'), RH('recipe'), RH('days_since'))
tools.append(TOOL('recipe_rotation', 'Recipe rotation', 'Which recipe is due a turn',
    'Recipes not planned for the days you type, ranked from the longest ago; a recipe never planned comes first.', [
    I('days', 'Not planned for this many days', 90)], [
    O('Recipes not planned for that long', 'int', NR13), O('Due a turn', 'text', RR(1, 'recipe')), O('Days since it was planned', 'int', RR(1, 'days_since')), O('Its category', 'text', RR(1, 'category')),
    O('Its prep minutes', 'int', RR(1, 'prep_min')), O('Second', 'text', RR(2, 'recipe')), O('Days since', 'int', RR(2, 'days_since')), O('Third', 'text', RR(3, 'recipe')), O('Days since', 'int', RR(3, 'days_since')),
    O('Verdict', 'text', 'IF(%s="",%s&" "&%s&", "&%s,IF(%s>={in:days},%s&" "&%s&", "&%s&" "&%s&" "&%s,%s))' % (
        RR(1, 'days_since'), lbl('Try'), RR(1, 'recipe'), lbl('never planned'), RR(1, 'days_since'), lbl('Try'), RR(1, 'recipe'), lbl('last planned'), RR(1, 'days_since'), lbl('days ago'), lbl('Every recipe is in rotation')))],
    GR('What if the limit changes', ('30 days', {'days': 30}), ('60 days', {'days': 60}), ('90 days', {'days': 90}), ('120 days', {'days': 120}), ('180 days', {'days': 180}))))

# 14 --------------------------------------------------------------- preference balance
NOLAB = 'SUMIFS(%s,%s,%s)' % (R('pref_mix', 'dinners14'), R('pref_mix', 'label'), tok('pref', 'No label'))
TOT14 = 'SUM(%s)' % R('pref_mix', 'dinners14')
LAB14 = '(%s-%s)' % (TOT14, NOLAB)
MX14 = 'IF(%s=MAX(%s),LARGE(%s,2),MAX(%s))' % (NOLAB, R('pref_mix', 'dinners14'), R('pref_mix', 'dinners14'), R('pref_mix', 'dinners14'))
NM14 = 'INDEX(%s,MATCH(%s,%s,0))' % (R('pref_mix', 'label'), MX14, R('pref_mix', 'dinners14'))
SH14 = 'IFERROR(%s/%s,0)' % (MX14, LAB14)
tools.append(TOOL('pref_balance', 'Preference balance', 'Is one label taking over the dinners',
    'Share of the next 14 days of dinners by plain preference label, leaving out the dinners with no label; type the share above which one label dominates.', [
    I('limit', 'Share of labelled dinners that counts as dominating', 0.4, 'pct')], [
    O('Dinners planned, next 14 days', 'int', TOT14), O('Dinners with a label', 'int', LAB14), O('Most used label', 'text', NM14), O('Dinners with that label', 'int', MX14), O('Share of labelled dinners', 'pct', SH14),
    O('Family favourites planned', 'int', 'SUMIFS(%s,%s,%s)' % (R('pref_mix', 'dinners14'), R('pref_mix', 'label'), tok('pref', 'Family favourite'))),
    O('Dinners with an avoid label', 'int', 'SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s)' % (R('pref_mix', 'dinners14'), R('pref_mix', 'label'), tok('pref', 'Child 2 avoids'), R('pref_mix', 'dinners14'), R('pref_mix', 'label'), tok('pref', 'Adult 2 avoids'))),
    O('Verdict', 'text', 'IF(%s>{in:limit},%s&" "&%s,%s)' % (SH14, NM14, lbl('dominates'), lbl('Balanced')))],
    GR('What if the limit changes', ('Limit 25%', {'limit': 0.25}), ('Limit 35%', {'limit': 0.35}), ('Limit 40%', {'limit': 0.4}), ('Limit 50%', {'limit': 0.5}), ('Limit 60%', {'limit': 0.6}))))

# 15 --------------------------------------------------------------- leftover lunch planner
SPARE = 'SUMIFS(%s,%s,">0")' % (PH('gap7'), PH('gap7'))
FRIDGE = 'SUMIFS(%s,%s,%s,%s,"<>",%s,"<>"&%s)' % (SKR('quantity'), SKR('place'), tok('place', 'Fridge'), SKR('recipe_id'), SKR('status'), PAST_)
tools.append(TOOL('leftover_lunch', 'Leftover lunch planner', 'How many lunches do the leftovers cover',
    'Spare dinner portions of the next 7 days plus cooked dishes in the fridge feed the next day lunches; type how many eat lunch at home. Leftovers keep only a few days: typical, check the label.', [
    I('lunch_eaters', 'Eaters at lunch', 2)], [
    O('Spare dinner portions, next 7 days', 'int', SPARE), O('Nights with spare portions', 'int', 'COUNTIFS(%s,">0")' % PH('gap7')), O('Cooked dish portions in the fridge', 'int', FRIDGE),
    O('Portions that can feed lunches', 'int', '%s+%s' % (SPARE, FRIDGE)), O('Lunches covered', 'int', 'INT((%s+%s)/{in:lunch_eaters})' % (SPARE, FRIDGE)),
    O('Fridge days typed in Settings', 'int', '{set:leftover_days}'),
    O('Verdict', 'text', V(F('INT((%s+%s)/{in:lunch_eaters})' % (SPARE, FRIDGE)), 'lunches covered by leftovers'))],
    GR('What if more eat lunch', ('1 eater', {'lunch_eaters': 1}), ('2 eaters', {'lunch_eaters': 2}), ('3 eaters', {'lunch_eaters': 3}), ('4 eaters', {'lunch_eaters': 4}))))

# 16 --------------------------------------------------------------- moving the shop day
D0 = 'MOD(%s-(WEEKDAY({today},2)-1),7)' % SDI
OLD16 = 'COUNTIFS(%s,"<"&(%s/7))' % (PN('ratio'), D0); NEW16 = 'COUNTIFS(%s,"<"&((%s+{in:move})/7))' % (PN('ratio'), D0)
tools.append(TOOL('move_shop', 'Moving the shop day', 'What runs short if the shop day moves',
    'The usual shop day comes from Settings; type the days to move it. Items whose stock covers less than the days to the new shop day are counted from the stock cover; an estimate from your entries.', [
    I('move', 'Move the shop day by days, negative is earlier', 2)], [
    O('Usual shop day', 'date', NEXT_SHOP), O('New shop day', 'date', '%s+{in:move}' % NEXT_SHOP), O('Days until the new shop day', 'int', '%s+{in:move}' % D0),
    O('Items short before the usual day', 'int', OLD16), O('Items short before the new day', 'int', NEW16), O('Items short because of the move', 'int', '%s-%s' % (NEW16, OLD16)),
    O('Verdict', 'text', 'IF(%s-%s<=0,%s,%s)' % (NEW16, OLD16, lbl('Safe'), V('Items short because of the move:', F('%s-%s' % (NEW16, OLD16)))))],
    GR('What if the shop day moves', ('1 day earlier', {'move': -1}), ('Same day', {'move': 0}), ('1 day later', {'move': 1}), ('2 days later', {'move': 2}), ('3 days later', {'move': 3}))))

# 17 --------------------------------------------------------------- plan for one person
FAC = '({in:portions}/INDEX(%s,MATCH({in:recipe_id},%s,0)))' % (R('recipes', 'servings'), R('recipes', 'recipe_id'))
PK17 = '+'.join('COUNTIFS(%s,{in:recipe_id},%s,">"&(%d/%s))' % (R('recipe_ingredients', 'recipe_id'), R('recipe_ingredients', 'qty_packs'), k, FAC) for k in range(5))
tools.append(TOOL('plan_for_one', 'Plan for one person', 'How much to buy for a smaller or larger number of portions',
    'Type a recipe ID and the portions you cook: the recipe is scaled and the packs are counted with every ingredient rounded up to its pack size; a single adult uses the same sheet.', [
    I('recipe_id', 'Recipe ID', 'RC-01', 'text'), I('portions', 'Portions to cook', 1)], [
    O('Recipe', 'text', 'INDEX(%s,MATCH({in:recipe_id},%s,0))' % (R('recipes', 'recipe'), R('recipes', 'recipe_id'))), O('Servings in the recipe', 'int', 'INDEX(%s,MATCH({in:recipe_id},%s,0))' % (R('recipes', 'servings'), R('recipes', 'recipe_id'))),
    O('Scale factor', 'num', 'ROUND(%s,2)' % FAC), O('Ingredient lines', 'int', 'COUNTIFS(%s,{in:recipe_id})' % R('recipe_ingredients', 'recipe_id')),
    O('Packs to buy, each ingredient rounded up', 'int', PK17), O('Prep minutes', 'int', 'INDEX(%s,MATCH({in:recipe_id},%s,0))' % (R('recipes', 'prep_min'), R('recipes', 'recipe_id'))),
    O('Verdict', 'text', V('Scale to', F('{in:portions}'), 'portions,', F(PK17), 'packs'))],
    GR('What if the portions change', ('1 portion', {'portions': 1}), ('2 portions', {'portions': 2}), ('3 portions', {'portions': 3}), ('4 portions', {'portions': 4}), ('5 portions', {'portions': 5}))))

# 18 --------------------------------------------------------------- cost line per dinner
LW = '(%s-7)' % TW; AW = '(%s-7-7*{in:compare_weeks})' % TW
COST_L = 'SUMIFS(%s,%s,1)' % (GL('actual_cost'), GL('wk_ago')); DIN_L = 'COUNTIFS(%s,%s,%s,1)' % (MP('slot'), DIN, MP('wk_ago'))
COST_A = 'SUMIFS(%s,%s,">=2",%s,"<="&(1+{in:compare_weeks}))' % (GL('actual_cost'), GL('wk_ago'), GL('wk_ago')); DIN_A = 'COUNTIFS(%s,%s,%s,">=2",%s,"<="&(1+{in:compare_weeks}))' % (MP('slot'), DIN, MP('wk_ago'), MP('wk_ago'))
PL18 = 'ROUND(%s/%s,2)' % (COST_L, DIN_L); PA18 = 'ROUND(%s/%s,2)' % (COST_A, DIN_A)
tools.append(TOOL('cost_per_dinner', 'Cost line per dinner', 'Is a dinner costing more than your own usual',
    'List cost lines of the last complete week divided by its dinners against the weeks before it; type the weeks to compare and a margin. A comparison with your own history, not price advice.', [
    I('compare_weeks', 'Complete weeks before it to compare', 4), I('margin', 'Margin for typical', 0.1, 'pct')], [
    O('Cost line of the last complete week', 'money', COST_L), O('Dinners in that week', 'int', DIN_L), O('Cost line per dinner, last complete week', 'money', PL18),
    O('Average per dinner, the weeks before it', 'money', PA18), O('Difference', 'money', '%s-%s' % (PL18, PA18)),
    O('Open lists, estimated cost per planned dinner', 'money', 'ROUND(SUMIFS(%s,%s,%s,%s,">="&{today},%s,"<="&({today}+6))/MAX(1,COUNTIFS(%s,%s,%s)),2)' % (GL('est_cost'), GL('status'), OPEN, GL('date'), GL('date'), MP('slot'), DIN, N7)),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:margin}),%s,IF(%s<%s*(1-{in:margin}),%s,%s))' % (PL18, PA18, V('Above your own average by', F('ROUND(%s-%s,2)' % (PL18, PA18))), PL18, PA18, V('Below your own average by', F('ROUND(%s-%s,2)' % (PA18, PL18))), lbl('Typical')))],
    GR('What if the margin or the weeks change', ('Margin 5%', {'margin': 0.05}), ('Margin 10%', {'margin': 0.1}), ('Margin 20%', {'margin': 0.2}), ('Compare 2 weeks', {'compare_weeks': 2}), ('Compare 8 weeks', {'compare_weeks': 8}))))
assert len(tools) == 18, len(tools)
