"""Home Management suite part 2: the 18 decision tools (a verdict, the numbers behind it and a what-if grid each)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho2_lists import *
import ho2_data as D
from ho2_tables import R, STK, ING, MEAL, LEF, REC, ITM, MS, DT, WK0

CAL = lambda c: R('calendar', c)
FLW = lambda c: R('flow', c)


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def X(e, d='""'): return 'IFERROR(%s,%s)' % (e, d)
def TXT(e): return 'IFERROR(%s&"","")' % e
def NUM(e): return 'IFERROR(%s,0)' % e
def J(*parts): return '&" "&'.join(parts)
def ST_(c, rank_col, n): return 'INDEX(%s,MATCH(%s,%s,0))' % (STK(c), n, STK(rank_col))
def RC_(c, n, rank_col='rank'): return 'INDEX(%s,MATCH(%s,%s,0))' % (REC(c), n, REC(rank_col))


tools = []

# 1 ---------------------------------------------------------------- cook this first
B1 = lambda c: RC_(c, 1)
tools.append(TOOL('cook_tool', 'Cook This First', 'What do we cook first from what is in the house',
    'Each recipe is scored from stock: the share of ingredients on hand (not past the date, at least the recipe quantity) plus 15 points per expiring item it uses. Calculated from your entries.', [
    I('min_share', 'Smallest share on hand that counts', 0.6, 'pct')], [
    O('Best recipe', 'text', TXT(B1('recipe'))), O('Share of its ingredients on hand', 'pct', NUM(B1('share'))), O('Ingredients on hand', 'int', NUM(B1('on_n'))),
    O('Ingredients in the recipe', 'int', NUM(B1('ing_n'))), O('Expiring items it uses', 'int', NUM(B1('soon_n'))), O('Prep minutes', 'int', NUM(B1('prep_min'))),
    O('Second best', 'text', TXT(RC_('recipe', 2))), O('Third best', 'text', TXT(RC_('recipe', 3))),
    O('Recipes at or above the share', 'int', 'COUNTIFS(%s,">="&{in:min_share},%s,">0")' % (REC('share'), REC('ing_n'))), O('Recipes with every ingredient on hand', 'int', 'COUNTIFS(%s,1)' % REC('ready')),
    O('Verdict', 'text', X('IF(%s>={in:min_share},%s,%s)' % (B1('share'), J(W('cook'), B1('recipe'), W('first') + '&","', B1('on_n'), W('of'), B1('ing_n'), W('on_hand')), W('no_fit'))))],
    GR('What if', ('Share 40%', {'min_share': 0.4}), ('Share 60%', {'min_share': 0.6}), ('Share 80%', {'min_share': 0.8}), ('Share 90%', {'min_share': 0.9}), ('Every ingredient', {'min_share': 1}))))

# 2 ---------------------------------------------------------------- use first list
U = lambda c, n=1: ST_(c, 'use_rank', n)
tools.append(TOOL('use_first_tool', 'Use First List', 'Which item do we use first and is it in the plan',
    'Stock not past its date ranked by days to the use-by date typed from the label (cooked dishes a few days earlier, set in Settings), with the plan check for the next 7 days.', [
    I('window', 'Use-soon window in days', USE_SOON_DAYS)], [
    O('Use first', 'text', TXT(U('item'))), O('Where it is', 'text', TXT(U('place'))), O('Use-by date', 'date', X('IF(%s=0,"",%s)' % (U('use_by'), U('use_by')))), O('Days left', 'int', X(U('days'))),
    O('Next 7 days plan', 'text', X('IF(%s=1,%s,%s)' % (U('in_plan'), IN_PLAN, NOT_PLAN))), O('Next in line', 'text', TXT(U('item', 2))), O('Third in line', 'text', TXT(U('item', 3))),
    O('Items within the window', 'int', 'COUNTIFS(%s,">=0",%s,"<="&{in:window})' % (STK('days'), STK('days'))),
    O('Of those, not in the next 7 days plan', 'int', 'COUNTIFS(%s,">=0",%s,"<="&{in:window},%s,0)' % (STK('days'), STK('days'), STK('in_plan'))),
    O('Items past the typed date', 'int', 'COUNTIFS(%s,%s)' % (STK('status'), PAST)),
    O('Verdict', 'text', X(J(W('use'), U('item'), W('by'), DT(U('use_by'))), W('nothing_due')))],
    GR('What if', ('Window 1 day', {'window': 1}), ('Window 2 days', {'window': 2}), ('Window 5 days', {'window': 5}), ('Window 7 days', {'window': 7}), ('Window 14 days', {'window': 14}))))

# 3 ---------------------------------------------------------------- fridge check today
FR_P = 'COUNTIFS(%s,%s,%s,%s)' % (STK('place'), FRIDGE, STK('status'), PAST)
FR_W = 'COUNTIFS(%s,%s,%s,">=0",%s,"<="&{in:window})' % (STK('place'), FRIDGE, STK('days'), STK('days'))
tools.append(TOOL('fridge_tool', 'Fridge Check Today', 'How many fridge items need using or checking today',
    'Counts the fridge stock that is past the typed date or reaches it within the window; cooked dishes in the fridge are counted too. Check the label and your local rules for every item.', [
    I('window', 'Window in days', USE_SOON_DAYS)], [
    O('Items in the fridge', 'int', 'COUNTIFS(%s,%s)' % (STK('place'), FRIDGE)), O('Past the typed date', 'int', FR_P), O('Reaching the date within the window', 'int', FR_W),
    O('Cooked dishes in the fridge', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (STK('place'), FRIDGE, STK('recipe_id'))),
    O('First in the fridge order', 'text', TXT(ST_('item', 'fr_rank', 1))), O('Days left of the first', 'int', X(ST_('days', 'fr_rank', 1))),
    O('Leftover dishes in the log, not frozen', 'int', 'COUNTIFS(%s,">0",%s,0)' % (LEF('portions_left'), LEF('frozen'))),
    O('Items to use or check today', 'int', '%s+%s' % (FR_P, FR_W)),
    O('Verdict', 'text', J(W('use_check'), '(%s+%s)' % (FR_P, FR_W), W('items_today')))],
    GR('What if', ('Window 1 day', {'window': 1}), ('Window 2 days', {'window': 2}), ('Window 5 days', {'window': 5}), ('Window 7 days', {'window': 7}))))

# 4 ---------------------------------------------------------------- freezer dinner finder
COND4 = '(%s=%s)*(%s=%s)*(%s>={in:eaters})' % (STK('place'), FREEZER, STK('unit'), PORTION, STK('quantity'))
OLD4 = 'SUMPRODUCT(MIN(%s+(1-%s)*1000000))' % (STK('added'), COND4)
ROW4 = 'MATCH(1,INDEX(%s*(%s=%s),0),0)' % (COND4, STK('added'), OLD4)
tools.append(TOOL('freezer_dinner_tool', 'Freezer Dinner Finder', 'Which freezer dish fits tonight, oldest first',
    'Looks at the cooked-dish portions in the chest freezer and picks the oldest dish with at least as many portions as there are eaters; heat it as the label says.', [
    I('eaters', 'Eaters tonight', 4)], [
    O('Portions of cooked dishes in the freezer', 'int', 'SUMIFS(%s,%s,%s,%s,%s)' % (STK('quantity'), STK('place'), FREEZER, STK('unit'), PORTION)),
    O('Dishes with enough portions', 'int', 'SUMPRODUCT(%s)' % COND4), O('Oldest dish that fits', 'text', TXT('INDEX(%s,%s)' % (STK('item'), ROW4))),
    O('Portions in it', 'int', NUM('INDEX(%s,%s)' % (STK('quantity'), ROW4))), O('Added on', 'date', 'IF(%s>=1000000,"",%s)' % (OLD4, OLD4)),
    O('Months in the freezer', 'num', X('IF(%s>=1000000,"",ROUND(({today}-%s)/30.4,1))' % (OLD4, OLD4))), O('Portions left after tonight', 'int', NUM('INDEX(%s,%s)-{in:eaters}' % (STK('quantity'), ROW4))),
    O('Verdict', 'text', X('IF(SUMPRODUCT(%s)>0,%s,%s)' % (COND4, J(W('defrost'), TXT('INDEX(%s,%s)' % (STK('item'), ROW4)), 'INDEX(%s,%s)' % (STK('quantity'), ROW4), W('portions')), W('no_dish'))))],
    GR('What if', ('2 eaters', {'eaters': 2}), ('3 eaters', {'eaters': 3}), ('5 eaters', {'eaters': 5}), ('6 eaters', {'eaters': 6}), ('1 eater', {'eaters': 1}))))

# 5 ---------------------------------------------------------------- leftover eat-by planner
EB5 = 'SUMPRODUCT(MIN(%s+(1-(%s>0)*(%s>={today}))*1000000))' % (LEF('eat_by'), LEF('portions_left'), LEF('eat_by'))
RW5 = 'MATCH(1,INDEX((%s>0)*(%s=%s),0),0)' % (LEF('portions_left'), LEF('eat_by'), EB5)
tools.append(TOOL('leftover_tool', 'Leftover Eat-By Planner', 'Which leftover dish do we eat next',
    'Finds the dish with portions left and the nearest eat-by date typed from the label (dates before today are left for Past-Date Review) and counts the dinners planned before that date.', [
    I('ppm', 'Portions eaten per leftover meal', 2)], [
    O('Dishes with portions left', 'int', 'COUNTIFS(%s,">0")' % LEF('portions_left')), O('Portions left in all', 'int', 'SUM(%s)' % LEF('portions_left')),
    O('Next dish to eat', 'text', TXT('INDEX(%s,%s)' % (LEF('dish'), RW5))), O('Eat by', 'date', 'IF(%s>=1000000,"",%s)' % (EB5, EB5)), O('Days left', 'int', X('IF(%s>=1000000,"",%s-{today})' % (EB5, EB5))),
    O('Portions left of it', 'int', NUM('INDEX(%s,%s)' % (LEF('portions_left'), RW5))), O('Meals it covers', 'int', NUM('ROUNDUP(INDEX(%s,%s)/{in:ppm},0)' % (LEF('portions_left'), RW5))),
    O('Dinners planned before that date', 'int', X('COUNTIFS(%s,%s,%s,">="&{today},%s,"<="&%s)' % (MEAL('slot'), DINNER, MEAL('date'), MEAL('date'), EB5), '0')),
    O('Verdict', 'text', X('IF(%s>=1000000,%s,%s)' % (EB5, W('no_leftover'), J(W('eat'), TXT('INDEX(%s,%s)' % (LEF('dish'), RW5)), W('by'), DT(EB5)))))],
    GR('What if', ('1 portion a meal', {'ppm': 1}), ('2 portions a meal', {'ppm': 2}), ('3 portions a meal', {'ppm': 3}), ('4 portions a meal', {'ppm': 4}))))

# 6 ---------------------------------------------------------------- stock below minimum
MINS = ITM('min_stock'); PK6 = ITM('pack_size')
T6 = 'ROUND(%s*{in:cover}-SUMIFS(%s,%s,%s),2)' % (MINS, STK('quantity'), STK('item'), ITM('item'))
C6 = '(%s>0)*(%s>=0)' % (MINS, T6)
X6 = 'ROUNDUP(ROUND(%s/(%s+(%s=0)),6),0)' % (T6, PK6, PK6)
P6 = '(%s+(%s<1)*(1-%s))' % (X6, X6, X6)
N6 = 'SUMPRODUCT(%s)' % C6
tools.append(TOOL('below_min_tool', 'Stock Below Minimum', 'Which items are at or below minimum and what to buy',
    'Compares the stock of every catalog item with its minimum stock times the cover you type; packs to buy are rounded up to the pack size typed in the Item Catalog.', [
    I('cover', 'Cover: restock up to this many times the minimum', 1, 'num')], [
    O('Items at or below the level', 'int', N6), O('Packs to buy', 'int', 'SUMPRODUCT(%s*%s)' % (C6, P6)), O('Cost line of the packs', 'money', 'SUMPRODUCT(%s*%s*%s)' % (C6, P6, ITM('pack_price'))),
    O('Share of catalog items', 'pct', X('%s/COUNTIFS(%s,"<>")' % (N6, ITM('item_id')), '0')), O('Items with nothing in stock', 'int', 'SUMPRODUCT((%s>0)*(SUMIFS(%s,%s,%s)=0))' % (MINS, STK('quantity'), STK('item'), ITM('item'))),
    O('Items on the Below Minimum sheet', 'int', 'COUNTIFS(%s,1)' % ITM('below')), O('First item to buy', 'text', TXT('INDEX(%s,MATCH(1,%s,0))' % (ITM('item'), ITM('rank')))),
    O('Verdict', 'text', J(W('buy'), N6, W('items_list')))],
    GR('What if', ('Cover 1.25', {'cover': 1.25}), ('Cover 1.5', {'cover': 1.5}), ('Cover 2', {'cover': 2}), ('Cover 3', {'cover': 3}))))

# 7 ---------------------------------------------------------------- use-soon window what-if
def AT(n): return 'COUNTIFS(%s,">=0",%s,"<="&%s)' % (STK('days'), STK('days'), n)
tools.append(TOOL('window_tool', 'Use-Soon Window What-If', 'How many items turn use soon if the window changes',
    'Counts the stock reaching its typed use-by date within the window you type, next to the window in Settings, and shows the same count for five windows.', [
    I('window', 'Window in days to test', 5)], [
    O('Items use soon at this window', 'int', AT('{in:window}')), O('Items use soon at the Settings window', 'int', 'COUNTIFS(%s,%s)' % (STK('status'), SOON)),
    O('Items that flip to use soon', 'int', '%s-COUNTIFS(%s,%s)' % (AT('{in:window}'), STK('status'), SOON)), O('Items past the typed date', 'int', 'COUNTIFS(%s,%s)' % (STK('status'), PAST)),
    O('At 1 day', 'int', AT('1')), O('At 3 days', 'int', AT('3')), O('At 7 days', 'int', AT('7')), O('At 14 days', 'int', AT('14')), O('At 30 days', 'int', AT('30')),
    O('Verdict', 'text', J(AT('{in:window}'), W('use_soon_at'), '{in:window}', W('days')))],
    GR('What if', ('Window 1 day', {'window': 1}), ('Window 3 days', {'window': 3}), ('Window 7 days', {'window': 7}), ('Window 14 days', {'window': 14}), ('Window 30 days', {'window': 30}))))

# 8 ---------------------------------------------------------------- pantry coverage in dinners
CV8 = 'COUNTIFS(%s,">="&{in:min_share},%s,">0")' % (REC('share'), REC('ing_n'))
TT8 = 'COUNTIFS(%s,">0")' % REC('ing_n')
tools.append(TOOL('coverage_tool', 'Pantry Coverage in Dinners', 'How many recipes can we cook from stock alone',
    'Counts the recipes whose ingredients are on hand at the share you type; the pantry, fridge and freezer stock not past its typed date counts as on hand.', [
    I('min_share', 'Share of ingredients on hand to count', 1, 'pct')], [
    O('Recipes with ingredients typed', 'int', TT8), O('Dinners cookable at this share', 'int', CV8), O('Dinners that need a top-up', 'int', '%s-%s' % (TT8, CV8)),
    O('Recipes missing exactly one ingredient', 'int', 'COUNTIFS(%s,1)' % REC('miss_n')), O('Share of recipes cookable', 'pct', X('%s/%s' % (CV8, TT8), '0')),
    O('Average share on hand', 'pct', X('AVERAGEIFS(%s,%s,">0")' % (REC('share'), REC('ing_n')), '0')), O('Best recipe now', 'text', TXT(RC_('recipe', 1))),
    O('Verdict', 'text', J(W('covers'), CV8, W('dinners'), '(%s-%s)' % (TT8, CV8), W('topup')))],
    GR('What if', ('Share 100%', {'min_share': 1}), ('Share 80%', {'min_share': 0.8}), ('Share 60%', {'min_share': 0.6}), ('Share 40%', {'min_share': 0.4}), ('Share 20%', {'min_share': 0.2}))))

# 9 ---------------------------------------------------------------- batch cook size
COOK9 = 'ROUNDUP(ROUND({in:eaters}*({in:now}+{in:later})*(1+{in:spare}),6),0)'
FRZ_NOW = 'SUMIFS(%s,%s,%s)' % (STK('quantity'), STK('place'), FREEZER)
TYP9 = 'AVERAGEIFS(%s,%s,%s)' % (REC('servings'), REC('category'), tok('rcat', 'Batch and freezer'))
tools.append(TOOL('batch_tool', 'Batch Cook Size', 'How many portions do we cook and how many go in the freezer',
    'Type the eaters, the meals you eat from the batch this week and the meals you freeze, plus a spare share; the freezer space comes from Settings.', [
    I('eaters', 'Eaters per meal', 4), I('now', 'Meals eaten from the batch this week', 2), I('later', 'Meals to freeze for later', 2), I('spare', 'Spare share on top', 0.1, 'pct')], [
    O('Portions to cook', 'int', COOK9), O('Portions eaten this week', 'int', '{in:eaters}*{in:now}'), O('Portions to freeze', 'int', '%s-{in:eaters}*{in:now}' % COOK9),
    O('Units in the freezer now', 'num', FRZ_NOW), O('Room left in the freezer', 'num', '{set:freezer_capacity}-%s' % FRZ_NOW),
    O('Room after freezing', 'num', '{set:freezer_capacity}-%s-(%s-{in:eaters}*{in:now})' % (FRZ_NOW, COOK9)),
    O('Typical servings of a batch recipe', 'int', NUM('ROUND(%s,0)' % TYP9)), O('Batches of that size', 'int', NUM('ROUNDUP(%s/ROUND(%s,0),0)' % (COOK9, TYP9))),
    O('Verdict', 'text', J(W('cook'), COOK9, W('portions') + '&","', W('freeze'), '(%s-{in:eaters}*{in:now})' % COOK9))],
    GR('What if', ('2 eaters', {'eaters': 2}), ('3 eaters', {'eaters': 3}), ('5 eaters', {'eaters': 5}), ('6 eaters', {'eaters': 6}), ('Freeze 4 meals', {'later': 4}))))

# 10 --------------------------------------------------------------- freezer rotation
FZR = lambda c, n=1: ST_(c, 'frz_rank', n)
tools.append(TOOL('rotation_tool', 'Freezer Rotation', 'Which freezer item is the oldest',
    'Ranks the chest freezer stock by months since it was added; the months to test are typed here, the typical 2 to 3 months for cooked dishes is in Settings (typical, check the label).', [
    I('months', 'Months to test', 3, 'num')], [
    O('Oldest item', 'text', TXT(FZR('item'))), O('Its months in the freezer', 'num', X(FZR('frz_m'))), O('Second oldest', 'text', TXT(FZR('item', 2))), O('Its months', 'num', X(FZR('frz_m', 2))),
    O('Third oldest', 'text', TXT(FZR('item', 3))), O('Freezer items older than the months', 'int', 'COUNTIFS(%s,">"&{in:months})' % STK('frz_m')),
    O('Units older than the months', 'num', 'SUMIFS(%s,%s,">"&{in:months})' % (STK('quantity'), STK('frz_m'))),
    O('Average months in the freezer', 'num', X('ROUND(AVERAGEIFS(%s,%s,%s),1)' % (STK('frz_m'), STK('place'), FREEZER), '0')),
    O('Verdict', 'text', X(J(W('oldest'), TXT(FZR('item')) + '&","', 'ROUND(%s,1)' % FZR('frz_m'), W('months')), W('no_freezer')))],
    GR('What if', ('Months 1', {'months': 1}), ('Months 2', {'months': 2}), ('Months 4', {'months': 4}), ('Months 6', {'months': 6}), ('Months 9', {'months': 9}))))

# 11 --------------------------------------------------------------- past-date review
def PP(place): return 'COUNTIFS(%s,%s,%s,"<"&(0-{in:older}))' % (STK('place'), place, STK('days'))
TOT11 = 'COUNTIFS(%s,"<"&(0-{in:older}))' % STK('days')
tools.append(TOOL('pastdate_tool', 'Past-Date Review', 'How many items are past the date you typed, by place',
    'Counts the stock whose typed use-by date has passed by more than the days you type, split by pantry, fridge and chest freezer; check and clear them by the label.', [
    I('older', 'Past the date by more than, days', 0)], [
    O('Past the date in the pantry', 'int', PP(PANTRY)), O('Past the date in the fridge', 'int', PP(FRIDGE)), O('Past the date in the chest freezer', 'int', PP(FREEZER)),
    O('Past the date in all', 'int', TOT11), O('Share of all stock', 'pct', X('%s/COUNTIFS(%s,"<>")' % (TOT11, STK('stock_id')), '0')),
    O('Longest past the date', 'text', TXT('INDEX(%s,MATCH(SMALL(%s,1),%s,0))' % (STK('item'), STK('days'), STK('days')))), O('Days past the date', 'int', X('MAX(0,0-SMALL(%s,1))' % STK('days'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (TOT11, W('nothing_past'), J(W('check_clear'), TOT11, W('items'))))],
    GR('What if', ('More than 3 days', {'older': 3}), ('More than 7 days', {'older': 7}), ('More than 14 days', {'older': 14}), ('More than 30 days', {'older': 30}))))

# 12 --------------------------------------------------------------- one missing ingredient finder
OM = lambda c: RC_(c, '{in:show}', 'one_rank')
tools.append(TOOL('one_missing_tool', 'One Missing Ingredient Finder', 'Which recipe is only one ingredient short',
    'Lists the recipes with exactly one ingredient not on hand, best score first; type 1 for the best, 2 for the next and so on.', [
    I('show', 'Which one to show, 1 is the best', 1)], [
    O('Recipes missing exactly one ingredient', 'int', 'COUNTIFS(%s,1)' % REC('miss_n')), O('Recipe', 'text', TXT(OM('recipe'))), O('Missing ingredient', 'text', TXT(OM('missing_first'))),
    O('Share on hand', 'pct', NUM(OM('share'))), O('Prep minutes', 'int', NUM(OM('prep_min'))), O('Expiring items it uses', 'int', NUM(OM('soon_n'))),
    O('Next candidate', 'text', TXT(RC_('recipe', '({in:show}+1)', 'one_rank'))),
    O('Verdict', 'text', X(J(W('missing_only'), TXT(OM('missing_first')), W('for'), TXT(OM('recipe'))), W('no_missing')))],
    GR('What if', ('The 2nd best', {'show': 2}), ('The 3rd best', {'show': 3}), ('The 4th best', {'show': 4}), ('The 5th best', {'show': 5}))))

# 13 --------------------------------------------------------------- meal from the items you have
MCH = '(COUNTIFS(%s,%s,%s,{in:i1})+COUNTIFS(%s,%s,%s,{in:i2})+COUNTIFS(%s,%s,%s,{in:i3}))' % ((ING('recipe_id'), REC('recipe_id'), ING('item')) * 3)
SC13 = '(%s*1000-%s)' % (MCH, REC('prep_min'))
MX13 = 'SUMPRODUCT(MAX(%s))' % SC13
RW13 = 'MATCH(%s,INDEX(%s,0),0)' % (MX13, SC13)
HIT13 = 'SUMPRODUCT(MAX(%s))' % MCH
tools.append(TOOL('items_match_tool', 'Meal From the Items You Have', 'What can we cook with these three items',
    'Type three items (as written in the Item Catalog); the recipes that use most of them are ranked, shorter prep time first when tied.', [
    IN('i1', 'First item', 'text', 'rice'), IN('i2', 'Second item', 'text', 'chicken breast'), IN('i3', 'Third item', 'text', 'peppers')], [
    O('Best fit', 'text', TXT('INDEX(%s,%s)' % (REC('recipe'), RW13))), O('Typed items it uses', 'int', HIT13), O('Prep minutes', 'int', NUM('INDEX(%s,%s)' % (REC('prep_min'), RW13))),
    O('Share of its ingredients on hand', 'pct', NUM('INDEX(%s,%s)' % (REC('share'), RW13))), O('Recipes using all three', 'int', 'SUMPRODUCT(--(%s=3))' % MCH),
    O('Recipes using at least two', 'int', 'SUMPRODUCT(--(%s>=2))' % MCH), O('Recipes using at least one', 'int', 'SUMPRODUCT(--(%s>=1))' % MCH),
    O('Typed items found in stock', 'int', '(COUNTIFS(%s,{in:i1})>0)+(COUNTIFS(%s,{in:i2})>0)+(COUNTIFS(%s,{in:i3})>0)' % ((STK('item'),) * 3)),
    O('Verdict', 'text', X('IF(%s>0,%s,%s)' % (HIT13, J(W('best_fit'), TXT('INDEX(%s,%s)' % (REC('recipe'), RW13)) + '&","', HIT13, W('of3')), W('no_match')), W('no_match')))]))

# 14 --------------------------------------------------------------- stock take difference
tools.append(TOOL('stock_take_tool', 'Stock Take Difference', 'How many items differ between the shelf and the record',
    'Type what you counted in the Counted column of Stock; the difference to the recorded quantity is shown by item, and differences up to your tolerance are ignored.', [
    I('tol', 'Tolerance in units, ignored below this', 0, 'num')], [
    O('Items counted', 'int', 'COUNT(%s)' % STK('counted')), O('Items to adjust', 'int', 'COUNTIFS(%s,">"&{in:tol})' % STK('absdiff')),
    O('Units short, counted less than recorded', 'num', 'ROUND(0-SUMIFS(%s,%s,"<0",%s,">"&{in:tol}),2)' % (STK('diff'), STK('diff'), STK('absdiff'))),
    O('Units extra, counted more than recorded', 'num', 'ROUND(SUMIFS(%s,%s,">0",%s,">"&{in:tol}),2)' % (STK('diff'), STK('diff'), STK('absdiff'))),
    O('Units to adjust, any sign', 'num', 'ROUND(SUMIFS(%s,%s,">"&{in:tol}),2)' % (STK('absdiff'), STK('absdiff'))),
    O('Largest difference at', 'text', TXT('INDEX(%s,MATCH(LARGE(%s,1),%s,0))' % (STK('item'), STK('absdiff'), STK('absdiff')))), O('Largest difference', 'num', NUM('LARGE(%s,1)' % STK('absdiff'))),
    O('Verdict', 'text', J(W('adjust'), 'COUNTIFS(%s,">"&{in:tol})' % STK('absdiff'), W('items') + '&","', 'ROUND(SUMIFS(%s,%s,">"&{in:tol}),2)' % (STK('absdiff'), STK('absdiff')), W('units')))],
    GR('What if', ('Tolerance 0.5', {'tol': 0.5}), ('Tolerance 1', {'tol': 1}), ('Tolerance 2', {'tol': 2}), ('Tolerance 5', {'tol': 5}), ('Tolerance 50', {'tol': 50}))))

# 15 --------------------------------------------------------------- freezer space
ROOM15 = '({in:capacity}-%s)' % FRZ_NOW
tools.append(TOOL('space_tool', 'Freezer Space', 'How much room is left in the chest freezer',
    'Units are portions, packs or pieces as typed in Stock; the space is a number you type for your own freezer.', [
    I('capacity', 'Freezer space in units', 60), I('coming', 'Units about to go in', 8)], [
    O('Units in the freezer now', 'num', FRZ_NOW), O('Room now', 'num', ROOM15), O('Share full', 'pct', X('%s/{in:capacity}' % FRZ_NOW, '0')),
    O('Units about to go in', 'int', '{in:coming}'), O('Room after they go in', 'num', '%s-{in:coming}' % ROOM15), O('Rows in the freezer', 'int', 'COUNTIFS(%s,%s)' % (STK('place'), FREEZER)),
    O('Verdict', 'text', 'IF(%s>={in:coming},%s,%s)' % (ROOM15, J(W('room_for'), ROOM15, W('portions')), J(W('over_by'), '({in:coming}-%s)' % ROOM15, W('portions'))))],
    GR('What if', ('Nothing coming', {'coming': 0}), ('5 units coming', {'coming': 5}), ('15 units coming', {'coming': 15}), ('30 units coming', {'coming': 30}), ('Space 80', {'capacity': 80}))))

# 16 --------------------------------------------------------------- before a trip away
LV16 = '({today}+{in:leave_in})'; BK16 = '({today}+{in:leave_in}+{in:days_away})'
def TP(place_op, lo, hi): return 'COUNTIFS(%s,%s,%s,">="&%s,%s,"<="&%s)' % (STK('place'), place_op, STK('use_by'), lo, STK('use_by'), hi)
BEFORE = '(%s+%s)' % (TP('"<>"&' + FREEZER, '{today}', LV16 + '-1'), 0)
WHILE = TP('"<>"&' + FREEZER, LV16, BK16)
tools.append(TOOL('trip_tool', 'Before a Trip Away', 'Which items pass their date while we are away',
    'Type the days until you leave and the days away; fridge and pantry items whose typed use-by date falls before you are back are counted, freezer items stay.', [
    I('leave_in', 'Days until you leave', 12), I('days_away', 'Days away', 7)], [
    O('Leaving on', 'date', LV16), O('Back on', 'date', BK16), O('Fridge and pantry items to use before leaving', 'int', BEFORE),
    O('Fridge and pantry items that pass the date while away', 'int', WHILE), O('Of those, in the fridge', 'int', TP(FRIDGE, LV16, BK16)),
    O('Freezer items that pass the date while away', 'int', TP(FREEZER, LV16, BK16)), O('Dinners planned before you leave', 'int', 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<"&%s)' % (MEAL('slot'), DINNER, MEAL('date'), MEAL('date'), LV16)),
    O('Verdict', 'text', J(W('use_freeze'), '(%s+%s)' % (BEFORE, WHILE), W('items'), W('before_leaving')))],
    GR('What if', ('Leave in 5 days', {'leave_in': 5}), ('Leave in 20 days', {'leave_in': 20}), ('Away 14 days', {'days_away': 14}), ('Away 3 days', {'days_away': 3}), ('Away 28 days', {'days_away': 28}))))

# 17 --------------------------------------------------------------- expiry calendar next 14 days
BUSY = 'LARGE(%s,1)' % CAL('due14')
BDAY = 'INDEX(%s,MATCH(%s,%s,0))' % (CAL('date'), BUSY, CAL('due14'))
tools.append(TOOL('expiry_tool', 'Expiry Calendar Next 14 Days', 'Which day has the most items reaching their date',
    'Counts the stock whose typed use-by date falls on each of the next 14 days (from the Use-By Calendar sheet) and names the busiest day.', [
    I('busy', 'Items a day that count as a busy day', 2)], [
    O('Items reaching the date in the next 14 days', 'int', 'SUM(%s)' % CAL('due14')), O('In the next 7 days', 'int', 'SUMIFS(%s,%s,"<7")' % (CAL('items_due'), CAL('day_no'))),
    O('Busiest day', 'date', X(BDAY)), O('Items on the busiest day', 'int', NUM(BUSY)), O('Days with at least this many items', 'int', 'COUNTIFS(%s,">="&{in:busy})' % CAL('due14')),
    O('Fridge items in the next 14 days', 'int', 'SUMIFS(%s,%s,"<14")' % (CAL('fridge_due'), CAL('day_no'))), O('Leftover portions reaching eat-by in 14 days', 'int', 'SUMIFS(%s,%s,"<14")' % (CAL('leftover_due'), CAL('day_no'))),
    O('Verdict', 'text', X(J(W('busiest'), DT(BDAY) + '&","', BUSY, W('items')), W('nothing_due')))],
    GR('What if', ('Busy is 1 item', {'busy': 1}), ('Busy is 3 items', {'busy': 3}), ('Busy is 4 items', {'busy': 4}), ('Busy is 6 items', {'busy': 6}))))

# 18 --------------------------------------------------------------- past-date items against own history
def PM(k): return 'SUMIFS(%s,%s,EDATE(%s,-%d))' % (FLW('past_date'), FLW('month'), MS, k)
AVG18 = '((%s+%s+%s)/3)' % (PM(2), PM(3), PM(4))
tools.append(TOOL('history_tool', 'Past-Date Items vs Own History', 'Did fewer items pass their date than usual',
    'Last complete month against the average of the 3 complete months before it, from the counts typed on Food Flow by Month; a comparison with your own history, no promise.', [
    I('tol', 'Share either side that counts as typical', 0.2, 'pct')], [
    O('Last complete month', 'int', PM(1)), O('Average of the 3 months before it', 'num', 'ROUND(%s,1)' % AVG18), O('Difference', 'num', 'ROUND(%s-%s,1)' % (PM(1), AVG18)),
    O('Change against the average', 'pct', X('%s/%s-1' % (PM(1), AVG18), '0')), O('Items past the date now, month in progress', 'int', 'COUNTIFS(%s,%s)' % (STK('status'), PAST)),
    O('Highest of the last 12 complete months', 'int', 'SUMPRODUCT(MAX((%s>=EDATE(%s,-12))*(%s<%s)*%s))' % (FLW('month'), MS, FLW('month'), MS, FLW('past_date'))),
    O('Average of the last 12 complete months', 'num', 'ROUND(SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)/12,1)' % (FLW('past_date'), FLW('month'), MS, FLW('month'), MS)),
    O('Verdict', 'text', 'IF(%s<%s*(1-{in:tol}),%s,IF(%s>%s*(1+{in:tol}),%s,%s))' % (PM(1), AVG18, tok('cmp', 'Fewer than your own average'), PM(1), AVG18, tok('cmp', 'More than your own average'), tok('cmp', 'Typical for your own history')))],
    GR('What if', ('Typical within 5%', {'tol': 0.05}), ('Typical within 10%', {'tol': 0.1}), ('Typical within 30%', {'tol': 0.3}), ('Typical within 50%', {'tol': 0.5}))))
assert len(tools) == 18, len(tools)
