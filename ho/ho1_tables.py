"""Home Management suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho1_lists import *
import ho1_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)


YES = '{list:yesno.yes}'
DIN = tok('slot', 'Dinner'); LATE = tok('shift', 'Late')
OPEN = tok('lstatus', 'Open'); BOUGHT = tok('lstatus', 'Bought')
SH_W, SH_T, SH_M, SH_O = (tok('shop', s) for s in SHOPS)
A1, A2, C1 = (tok('cook', s) for s in ('Adult 1', 'Adult 2', 'Child 1'))
OK_, SOON_, PAST_ = lbl('ok'), lbl('use soon'), lbl('past date')
V_A1, V_A2, V_EITHER, V_PREP = lbl('Adult 1'), lbl('Adult 2'), lbl('Either adult'), lbl('Prep ahead')
V_PLANNED, V_MISS = lbl('Planned'), lbl('Dinner missing')
V_MATCH, V_CHECK, V_PREPNEED = lbl('Matches the pattern'), lbl('Check the cook'), lbl('Prep ahead needed')
V_HEAVY, V_LIGHT, V_TYP = lbl('Heavier'), lbl('Lighter'), lbl('Typical')


def IDX(setkey):
    """index 0..6 of a weekday setting (Monday = 0), built from list comparisons so no text is written"""
    return '(' + '+'.join('({set:%s}=%s)*%d' % (setkey, tok('wday', n), i) for i, n in enumerate(WEEKDAYS) if i) + ')'


WSI = IDX('week_start'); SDI = IDX('shop_day')
def WK(d): return '(%s-MOD(WEEKDAY(%s,2)-1-%s,7))' % (d, d, WSI)
TW = WK('{today}')                                   # first day of this week (Settings week start)
NEXT_SHOP = '({today}+MOD(%s-(WEEKDAY({today},2)-1),7))' % SDI
def MP(c): return R('meal_plan', c)
def GL(c): return R('grocery_lists', c)
def GIT(c): return R('grocery_items', c)
def PN(c): return R('plan_needs', c)
def PH(c): return R('people_home', c)
def CL_(c): return R('cook_load', c)
N7 = '%s,">="&{today},%s,"<="&({today}+6)' % (MP('date'), MP('date'))          # meal plan rows of the next 7 days
N14 = '%s,">="&{today},%s,"<="&({today}+13)' % (MP('date'), MP('date'))
L30 = '%s,">="&({today}-29),%s,"<="&{today}' % (MP('date'), MP('date'))
G30 = '%s,">="&({today}-29),%s,"<="&{today}' % (GL('date'), GL('date'))


def TLR(role, col): return 'IFERROR(INDEX({range:team.%s},MATCH({list:role.%s},{range:team.role},0))&"","")' % (col, key('role', role))
def TLC(n, col): return 'IFERROR(INDEX({range:team.%s},MATCH({set:child%d_id},{range:team.member_id},0))&"","")' % (col, n)
def NAME(role, k, label=None): return CA(k, label or (role + ' name'), 'text', TLR(role, 'short'), 14)
def PHONE(role, k, label=None): return CA(k, label or (role + ' phone'), 'text', TLR(role, 'phone'), 18)
def CNAME(n, k): return CA(k, 'Child %d name' % n, 'text', TLC(n, 'short'), 14)
def CPHONE(n, k): return CA(k, 'Child %d phone' % n, 'text', TLC(n, 'phone'), 18)
def HOUSE(): return CA('household', 'Household', 'text', '{set:household}', 24)
def A12(): return [NAME('Adult 1', 'a1_name'), PHONE('Adult 1', 'a1_phone'), NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone')]
def DLOOK(col, w=14):  # dinner of the row's date
    return 'IFERROR(INDEX(%s,MATCH({col:date}&"|"&%s,%s,0)),"")' % (MP(col), DIN, MP('slot_key'))


settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('adult1', 'Adult 1 shown as', 'text', 'Adult 1'), S('adult2', 'Adult 2 shown as', 'text', 'Adult 2'),
    S('child1_id', 'Team member ID of child 1', 'text', 'HO-03'), S('child2_id', 'Team member ID of child 2', 'text', 'HO-04'),
    S('week_start', 'Week starts on', 'list', key('wday', WEEK_START), list='wday'), S('units_system', 'Unit labels', 'list', key('usys', 'Metric'), list='usys'),
    S('shop_day', 'Usual weekly shop day', 'list', key('wday', 'Saturday'), list='wday'), S('use_soon_days', 'Use soon: days before the use-by date typed from the label', 'int', USE_SOON_DAYS),
    S('leftover_days', 'Cooked leftovers in the fridge, days (typical 3 to 4)', 'int', FOOD_DAYS_TYPICAL), S('busy_limit', 'Busy-day limit: prep minutes in one day', 'int', 75),
    S('quick_min', 'A quick dinner takes this many minutes or less', 'int', 40), S('rare_days', 'Rarely planned: days since a recipe was last planned', 'int', 90),
    S('heavy_margin', 'A list is heavier or lighter than usual beyond this margin', 'pct', 0.15), S('dinner_hour', 'Dinner is served at this hour, 24-hour clock', 'int', 18),
    S('late_dinner_hour', 'Dinner on adult 1 late days, hour of the 24-hour clock', 'int', 19), S('usual_eaters', 'Usual number of eaters at dinner', 'int', 4),
    S('batch_factor', 'Batches cooked at once on a batch cooking day', 'int', 3), S('staple_weeks', 'Standing item: weeks on a list out of the last 26', 'int', 20),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 team ----------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact: role, phone and e-mail; the texts in this workbook use these numbers. Renters read a trade as the landlord.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 16), LST('group', 'Group', 'tgroup', 10), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11), C('short', 'Short name', 'text', 12), HOUSE()], D.team_d(), 50))
# 2 recipes -------------------------------------------------------------------
LASTP = 'SUMPRODUCT(MAX((%s={col:recipe_id})*(%s<={today})*%s))' % (MP('recipe_id'), MP('date'), MP('date'))
tables.append(T('recipes', 'Recipes', 'Recipe box with how often each recipe is planned',
    'One row per household recipe: prep minutes, servings and a plain preference label (never health advice); the ingredient count, times planned in 90 days and days since fill in.', [
    C('recipe_id', 'Recipe ID', 'text', 9, required=True), C('recipe', 'Recipe', 'text', 28), LST('category', 'Category', 'rcat', 16), C('prep_min', 'Prep minutes', 'int', 9), C('servings', 'Servings', 'int', 9),
    LST('pref_label', 'Preference label', 'pref', 16),
    CA('ingredient_count', 'Ingredient lines', 'int', 'COUNTIFS(%s,{col:recipe_id})' % R('recipe_ingredients', 'recipe_id'), 9),
    CA('planned_90', 'Planned in the last 90 days', 'int', 'COUNTIFS(%s,{col:recipe_id},%s,">="&({today}-89),%s,"<="&{today})' % (MP('recipe_id'), MP('date'), MP('date')), 11),
    CA('days_since', 'Days since last planned', 'int', 'IF(%s=0,"",{today}-%s)' % (LASTP, LASTP), 10),
    CA('rno', 'Recipe number', 'int', 'VALUE(RIGHT({col:recipe_id},2))', 8),
    CA('dinner_prep', 'Dinner prep minutes', 'int', 'IF(OR({col:category}=%s,{col:category}=%s,{col:ingredient_count}=0),"",{col:prep_min})' % (tok('rcat', 'Breakfast dishes'), tok('rcat', 'Baking and sweets')), 10),
    CA('quick_rank', 'Quickest dinner, 1 is quickest', 'int', 'IF({col:dinner_prep}="","",COUNTIFS(%s,"<"&{col:dinner_prep})+COUNTIFS(%s,{col:dinner_prep},%s,"<"&{col:rno})+1)' % (R('recipes', 'dinner_prep'), R('recipes', 'dinner_prep'), R('recipes', 'rno')), 10),
    CA('in_category', 'Recipes in the category', 'int', 'COUNTIFS(%s,{col:category})' % R('recipes', 'category'), 9),
    CA('avg_prep_cat', 'Average prep minutes of the category', 'int', 'ROUND(AVERAGEIFS(%s,%s,{col:category}),0)' % (R('recipes', 'prep_min'), R('recipes', 'category')), 11),
    CA('scale_usual', 'Scale for the usual eaters', 'num', 'ROUND({set:usual_eaters}/{col:servings},2)', 10), CA('portions_batch', 'Portions in one batching day', 'int', '{col:servings}*{set:batch_factor}', 10)],
    D.recipes_d(), 80, [A('pref_label', '= ' + tok('pref', 'Family favourite'), 'good')]))
# 3 recipe ingredients --------------------------------------------------------
tables.append(T('recipe_ingredients', 'Recipe ingredients', 'Ingredient lines with what the week plan needs',
    'One row per ingredient of a recipe, quantity for the recipe servings; the quantity the next 7 days of the plan need, scaled to the servings planned, fills in.', [
    C('ingredient_id', 'Ingredient ID', 'text', 11, required=True), REF('recipe_id', 'Recipe ID', 'recipes.recipe_id', 9),
    CA('recipe', 'Recipe', 'text', LKT('recipes.recipe', 'recipes.recipe_id', 'recipe_id'), 26), REF('item', 'Item', 'items.item', 18), C('qty', 'Quantity', 'num', 9), LST('unit', 'Unit', 'unit', 8),
    LST('section', 'Section', 'section', 16),
    CA('rec_servings', 'Recipe servings', 'int', LKN('recipes.servings', 'recipes.recipe_id', 'recipe_id'), 9),
    CA('plan_servings', 'Servings planned, next 7 days', 'int', 'SUMIFS(%s,%s,{col:recipe_id},%s)' % (MP('servings'), MP('recipe_id'), N7), 11),
    CA('need_week', 'Needed for the week plan', 'num', 'IFERROR(ROUND({col:qty}*{col:plan_servings}/{col:rec_servings},3),0)', 11),
    CA('pack_size', 'Pack size of the item', 'num', LKN('items.pack_size', 'items.item', 'item'), 9),
    CA('qty_packs', 'Packs of the item in the recipe', 'num', 'IFERROR(ROUND({col:qty}/{col:pack_size},3),0)', 10)], D.ri_d(), 400))
# 4 item catalog --------------------------------------------------------------
tables.append(T('items', 'Item catalog', 'Item catalog with pack sizes, shelf days and shops',
    'One row per item you buy: section, unit, where it is kept, per-serving amount, pack size, shelf days and minimum stock (typical, check the label) and pack price (a cost line).', [
    C('item_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 22), LST('section', 'Section', 'section', 16), LST('unit', 'Unit', 'unit', 8), LST('place', 'Place', 'place', 13),
    C('per_serving', 'Per serving', 'num', 9), C('pack_size', 'Pack size', 'num', 9), C('shelf_days', 'Shelf days', 'int', 9), C('min_stock', 'Minimum stock', 'num', 9), C('pack_price', 'Pack price', 'money', 11),
    LST('shop', 'Shop', 'shop', 13),
    CA('used_in', 'Recipes using it', 'int', 'COUNTIFS(%s,{col:item})' % R('recipe_ingredients', 'item'), 9)], D.items_d(), 120))
# 5 stock on hand -------------------------------------------------------------
tables.append(T('stock', 'Stock on hand', 'Pantry, fridge and freezer stock with use-by dates',
    'One row per item held: quantity, unit, added and use-by date typed from the label; days left, a use-soon status and whether the next 7 days of the plan use it fill in.', [
    C('stock_id', 'Stock ID', 'text', 9, required=True), C('item', 'Item', 'text', 26), LST('place', 'Place', 'place', 13), C('quantity', 'Quantity', 'num', 9), LST('unit', 'Unit', 'unit', 8),
    C('added', 'Added', 'date', 11), C('use_by', 'Use by', 'date', 11), C('min_qty', 'Minimum quantity', 'num', 9), LST('section', 'Section', 'section', 16), C('recipe_id', 'Recipe ID', 'text', 9),
    CA('days_left', 'Days left', 'int', '{col:use_by}-{today}', 8),
    CA('status', 'Status', 'text', 'IF({col:use_by}="","",IF({col:days_left}<0,%s,IF({col:days_left}<={set:use_soon_days},%s,%s)))' % (PAST_, SOON_, OK_), 10),
    CA('in_plan', 'In the plan, 1 or 0', 'int', 'IF({col:recipe_id}<>"",IF(COUNTIFS(%s,{col:recipe_id},%s)>0,1,0),IF(SUMIFS(%s,%s,{col:item})>0,1,0))' % (MP('recipe_id'), N7, R('recipe_ingredients', 'need_week'), R('recipe_ingredients', 'item')), 9),
    CA('below_min', 'Below minimum, 1 or 0', 'int', 'IF(AND({col:min_qty}>0,{col:quantity}<{col:min_qty}),1,0)', 9)] + A12() + [HOUSE()],
    D.stock_d(), 120, [A('status', '= ' + SOON_, 'warn'), A('status', '= ' + PAST_, 'bad'), A('status', '= ' + OK_, 'good')]))
# 6 meal plan -----------------------------------------------------------------
tables.append(T('meal_plan', 'Meal plan', 'Meal plan: breakfast, lunch, dinner and snack for every day',
    'One row per meal planned: date, slot, recipe, eaters and cook; recipe name, prep minutes, label, adult 1 late day and age in days fill in. Tick cooked once it was made.', [
    C('plan_id', 'Plan ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('weekday', 'Weekday', 'wday', 10), LST('slot', 'Slot', 'slot', 10), REF('recipe_id', 'Recipe ID', 'recipes.recipe_id', 9),
    C('servings', 'Servings', 'int', 8), LST('cook', 'Cook', 'cook', 9), C('cooked', 'Cooked', 'bool', 8),
    CA('recipe', 'Recipe', 'text', LKT('recipes.recipe', 'recipes.recipe_id', 'recipe_id'), 26), CA('prep_min', 'Prep minutes', 'int', LKN('recipes.prep_min', 'recipes.recipe_id', 'recipe_id'), 9),
    CA('pref_label', 'Preference label', 'text', LKT('recipes.pref_label', 'recipes.recipe_id', 'recipe_id'), 16), CA('ings', 'Ingredient lines', 'int', LKN('recipes.ingredient_count', 'recipes.recipe_id', 'recipe_id'), 9),
    CA('age', 'Days ago, negative is ahead', 'int', '{today}-{col:date}', 9), CA('in14', 'In the next 14 days, 1 or 0', 'int', 'IF(AND({col:date}>={today},{col:date}<={today}+13),1,0)', 9), CA('week', 'Week starting', 'date', WK('{col:date}'), 11), CA('wk_ago', 'Complete weeks ago', 'int', 'IF({col:date}="","",ROUNDUP((%s-{col:date})/7,0))' % TW, 9), 
    CA('late', 'Adult 1 late day, 1 or 0', 'int', 'IF(COUNTIFS(%s,{col:date},%s,%s)>0,1,0)' % (R('shifts', 'date'), R('shifts', 'adult1_late'), YES), 9),
    CA('slot_key', 'Day and slot key', 'text', '{col:date}&"|"&{col:slot}', 14)],
    D.meal_plan_d(), 1500, [A('cooked', '= ' + YES, 'good')]))
# 7 people at home ------------------------------------------------------------
TIME_EAT = 'IF(COUNTIFS(%s,{col:date},%s,%s)>0,{set:late_dinner_hour},{set:dinner_hour})/24' % (R('shifts', 'date'), R('shifts', 'adult1_late'), YES)
tables.append(T('people_home', 'People at home', 'Who is at home for dinner each day',
    'One row per day: adults, children, the grandparent and guests at home and an away note; eaters, the dinner, portions planned and the gap fill in. Single adults type 1 adult and no children.', [
    C('date', 'Date', 'date', 11, required=True), C('adults', 'Adults at home', 'int', 9), C('children', 'Children at home', 'int', 9), C('grandparent', 'Grandparent at home', 'bool', 10),
    C('guests', 'Guests', 'int', 8), C('guest_name', 'Guest name', 'text', 14), C('guest_phone', 'Guest phone', 'text', 18), C('away_note', 'Away note', 'text', 28),
    CA('eaters', 'Eaters', 'int', '{col:adults}+{col:children}+IF({col:grandparent}=%s,1,0)+{col:guests}' % YES, 8),
    CA('recipe', 'Dinner', 'text', DLOOK('recipe'), 24), CA('planned_servings', 'Servings planned', 'int', DLOOK('servings'), 9),
    CA('gap', 'Portions spare, negative is short', 'int', 'IF({col:planned_servings}="","",{col:planned_servings}-{col:eaters})', 11),
    CA('gap7', 'Spare portions, next 7 days', 'int', 'IF(AND({col:date}>={today},{col:date}<={today}+6),{col:gap},"")', 11),
    CA('prep_min', 'Dinner prep minutes', 'int', DLOOK('prep_min'), 9), CA('pref_label', 'Preference label', 'text', DLOOK('pref_label'), 16),
    CA('eat_at', 'Dinner time', 'time', TIME_EAT, 9), CA('table_at', 'Set the table at', 'time', '%s-15/1440' % TIME_EAT, 9), CA('pick_by', 'Pick the dinner by', 'date', '{col:date}-3', 11),
    CNAME(1, 'c1_name'), CPHONE(1, 'c1_phone'), CNAME(2, 'c2_name'), CPHONE(2, 'c2_phone'), NAME('Grandparent', 'gp_name'), PHONE('Grandparent', 'gp_phone'),
    NAME('Babysitter', 'bs_name'), PHONE('Babysitter', 'bs_phone'), NAME('Carpool family', 'cp_name'), PHONE('Carpool family', 'cp_phone'), NAME('Neighbour', 'nb_name'), PHONE('Neighbour', 'nb_phone'),
    NAME('School office', 'so_name'), PHONE('School office', 'so_phone'), HOUSE()],
    D.people_home_d(), 60, [A('gap', '< 0', 'warn'), A('guests', '> 0', 'good')]))
# 8 work pattern --------------------------------------------------------------
tables.append(T('shifts', 'Work pattern', 'Adult 2 shift pattern and adult 1 late days',
    'One row per day: adult 2 works an Early, Late or Off shift and adult 1 has late days; adults free in the evening and a suggested cook fill the plan. Single adults mark every day Off.', [
    C('shift_id', 'Shift ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('weekday', 'Weekday', 'wday', 10), C('adult1_late', 'Adult 1 late day', 'bool', 9),
    LST('adult2_shift', 'Adult 2 shift', 'shift', 10), C('adults_free', 'Adults free in the evening', 'int', 10),
    CA('suggest', 'Suggested cook', 'text', 'IF({col:adult1_late}=%s,IF({col:adult2_shift}=%s,%s,%s),IF({col:adult2_shift}=%s,%s,%s))' % (YES, LATE, V_PREP, V_A2, LATE, V_A1, V_EITHER), 13)],
    D.shifts_d(), 200, [A('adult2_shift', '= ' + LATE, 'warn'), A('adult1_late', '= ' + YES, 'warn')]))
# 9 week plan grid ------------------------------------------------------------
tables.append(T('week_grid', 'Week plan grid', 'The next 7 days by meal slot',
    'Type the day numbers 0 to 6 once with each slot; the date, recipe, servings, prep minutes, cook and a flag for a dinner that is missing fill in from the meal plan.', [
    C('day_no', 'Day number', 'int', 8, required=True), LST('slot', 'Slot', 'slot', 10), CA('date', 'Date', 'date', '{today}+{col:day_no}', 11),
    CA('recipe', 'Recipe', 'text', 'IFERROR(INDEX(%s,MATCH({col:date}&"|"&{col:slot},%s,0))&"","")' % (MP('recipe'), MP('slot_key')), 26),
    CA('servings', 'Servings', 'int', 'IFERROR(INDEX(%s,MATCH({col:date}&"|"&{col:slot},%s,0)),"")' % (MP('servings'), MP('slot_key')), 9),
    CA('prep_min', 'Prep minutes', 'int', 'IFERROR(INDEX(%s,MATCH({col:date}&"|"&{col:slot},%s,0)),"")' % (MP('prep_min'), MP('slot_key')), 9),
    CA('cook', 'Cook', 'text', 'IFERROR(INDEX(%s,MATCH({col:date}&"|"&{col:slot},%s,0))&"","")' % (MP('cook'), MP('slot_key')), 9),
    CA('planned', 'Planned, 1 or 0', 'int', 'IF({col:recipe}="",0,1)', 9),
    CA('flag', 'Flag', 'text', 'IF({col:planned}=1,%s,IF({col:slot}=%s,%s,""))' % (V_PLANNED, DIN, V_MISS), 14)],
    D.week_grid_d(), 50, [A('flag', '= ' + V_MISS, 'bad'), A('flag', '= ' + V_PLANNED, 'good')]))
# 10 plan needs against stock -------------------------------------------------
tables.append(T('plan_needs', 'Plan needs vs stock', 'Shopping list: plan needs minus stock, by pack size',
    'One row per catalog item: what the next 7 days need, what is on hand, what to buy rounded up to pack sizes and a restock when stock is under the minimum; the cost line fills in.', [
    REF('item', 'Item', 'items.item', 22, required=True), CA('unit', 'Unit', 'text', LKT('items.unit', 'items.item', 'item'), 8), CA('section', 'Section', 'text', LKT('items.section', 'items.item', 'item'), 16),
    CA('shop', 'Shop', 'text', LKT('items.shop', 'items.item', 'item'), 13), CA('pack_size', 'Pack size', 'num', LKN('items.pack_size', 'items.item', 'item'), 9),
    CA('pack_price', 'Pack price', 'money', LKN('items.pack_price', 'items.item', 'item'), 10), CA('min_stock', 'Minimum stock', 'num', LKN('items.min_stock', 'items.item', 'item'), 9),
    CA('needed', 'Needed, next 7 days', 'num', 'ROUND(SUMIFS(%s,%s,{col:item}),2)' % (R('recipe_ingredients', 'need_week'), R('recipe_ingredients', 'item')), 10),
    CA('on_hand', 'On hand', 'num', 'ROUND(SUMIFS(%s,%s,{col:item}),2)' % (R('stock', 'quantity'), R('stock', 'item')), 9),
    CA('to_buy', 'To buy for the plan', 'num', 'MAX(0,ROUND({col:needed}-{col:on_hand},2))', 9),
    CA('packs', 'Packs for the plan', 'int', 'IF(AND({col:to_buy}>0,{col:pack_size}>0),ROUNDUP(ROUND({col:to_buy}/{col:pack_size},6),0),0)', 9),
    CA('restock', 'Packs to restock', 'int', 'IF(AND({col:packs}=0,{col:min_stock}>0,{col:pack_size}>0,{col:on_hand}<{col:min_stock}),ROUNDUP(ROUND(({col:min_stock}-{col:on_hand})/{col:pack_size},6),0),0)', 9),
    CA('total_packs', 'Packs to buy', 'int', '{col:packs}+{col:restock}', 9), CA('qty_bought', 'Quantity bought', 'num', 'ROUND({col:total_packs}*{col:pack_size},2)', 10),
    CA('plan_cost', 'Cost line of the plan', 'money', 'ROUND({col:packs}*{col:pack_price},2)', 11), CA('restock_cost', 'Cost line of the restock', 'money', 'ROUND({col:restock}*{col:pack_price},2)', 11),
    CA('cost', 'Cost line', 'money', '{col:plan_cost}+{col:restock_cost}', 11), CA('buy_flag', 'To buy, 1 or 0', 'int', 'IF({col:total_packs}>0,1,0)', 8),
    CA('needs_flag', 'Needed, 1 or 0', 'int', 'IF({col:needed}>0,1,0)', 8), CA('covered', 'Covered by stock, 1 or 0', 'int', 'IF(AND({col:needed}>0,{col:to_buy}=0),1,0)', 9),
    CA('ratio', 'Stock against need', 'num', 'IF({col:needed}>0,ROUND({col:on_hand}/{col:needed},4),"")', 9), CA('shop_date', 'Next shop day', 'date', NEXT_SHOP, 11),
    NAME('Grandparent', 'gp_name'), PHONE('Grandparent', 'gp_phone'), NAME('Neighbour', 'nb_name'), PHONE('Neighbour', 'nb_phone'), HOUSE()],
    D.plan_needs_d(), 120, [A('total_packs', '> 0', 'warn'), A('covered', '= 1', 'good')]))
# 11 grocery lists ------------------------------------------------------------
tables.append(T('grocery_lists', 'Grocery lists', 'Grocery lists, one per shop trip, with the cost line',
    'One row per shop trip: date, shop, status, items and the estimated and actual cost line; the week and whether it fell on the usual shop day fill in.', [
    C('list_id', 'List ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('shop', 'Shop', 'shop', 13), LST('status', 'Status', 'lstatus', 9), C('items', 'Items', 'int', 8),
    C('est_cost', 'Estimated cost', 'money', 11), C('actual_cost', 'Actual cost', 'money', 11),
    CA('week', 'Week starting', 'date', WK('{col:date}'), 11), CA('wk_ago', 'Complete weeks ago', 'int', 'IF({col:date}="","",ROUNDUP((%s-{col:date})/7,0))' % TW, 9),  CA('on_shop_day', 'On the shop day, 1 or 0', 'int', 'IF(WEEKDAY({col:date},2)-1=%s,1,0)' % SDI, 9),
    CA('diff', 'Actual less estimate', 'money', 'IF({col:status}=%s,ROUND({col:actual_cost}-{col:est_cost},2),"")' % BOUGHT, 11),
    CA('shop_plan_items', 'Items the plan needs from this shop', 'int', 'SUMIFS(%s,%s,{col:shop})' % (R('shop_split', 'items_to_buy'), R('shop_split', 'shop')), 11),
    CA('shop_plan_cost', 'Cost line of the plan at this shop', 'money', 'SUMIFS(%s,%s,{col:shop})' % (R('shop_split', 'cost'), R('shop_split', 'shop')), 12)] + A12() + [HOUSE()],
    D.grocery_lists_d(), 300, [A('status', '= ' + OPEN, 'warn'), A('status', '= ' + BOUGHT, 'good')]))
# 12 grocery items ------------------------------------------------------------
tables.append(T('grocery_items', 'Grocery items', 'Every item on every list, bought and cost line',
    'One row per item on a list: quantity, unit, section, shop, bought and cost line; the list date, week, and the first and last time the item was bought fill in.', [
    C('grocery_item_id', 'Grocery item ID', 'text', 11, required=True), REF('list_id', 'List ID', 'grocery_lists.list_id', 9), REF('item', 'Item', 'items.item', 20), C('qty', 'Quantity', 'num', 9),
    LST('unit', 'Unit', 'unit', 8), LST('section', 'Section', 'section', 16), LST('shop', 'Shop', 'shop', 13), C('bought', 'Bought', 'bool', 8), C('cost', 'Cost', 'money', 9),
    CA('date', 'List date', 'date', LKN('grocery_lists.date', 'grocery_lists.list_id', 'list_id'), 11), CA('week', 'Week starting', 'date', WK('{col:date}'), 11),
    CA('seq', 'Sequence', 'int', 'VALUE(RIGHT({col:grocery_item_id},4))', 8),
    CA('first_in_week', 'First of the week, 1 or 0', 'int', 'IF(COUNTIFS(%s,{col:item},%s,{col:week},%s,"<"&{col:seq})=0,1,0)' % (GIT('item'), GIT('week'), GIT('seq')), 9),
    CA('is_last', 'Last time bought, 1 or 0', 'int', 'IF({col:bought}=%s,IF(COUNTIFS(%s,{col:item},%s,%s,%s,">"&{col:date})+COUNTIFS(%s,{col:item},%s,%s,%s,{col:date},%s,">"&{col:seq})=0,1,0),0)'
       % (YES, GIT('item'), GIT('bought'), YES, GIT('date'), GIT('item'), GIT('bought'), YES, GIT('date'), GIT('seq')), 9)],
    D.grocery_items_d(), 1300, [A('bought', '= ' + YES, 'good')]))
# 13 shopping list by shop and section ---------------------------------------
tables.append(T('shop_split', 'Shopping list by shop', 'The list to buy by shop and section',
    'One row per shop and section: items to buy, packs and cost line from Plan needs vs stock; type the 36 combinations once and the rest fills in.', [
    LST('shop', 'Shop', 'shop', 13, required=True), LST('section', 'Section', 'section', 16),
    CA('items_to_buy', 'Items to buy', 'int', 'COUNTIFS(%s,{col:shop},%s,{col:section},%s,1)' % (PN('shop'), PN('section'), PN('buy_flag')), 9),
    CA('packs', 'Packs', 'int', 'SUMIFS(%s,%s,{col:shop},%s,{col:section})' % (PN('total_packs'), PN('shop'), PN('section')), 8),
    CA('cost', 'Cost line', 'money', 'SUMIFS(%s,%s,{col:shop},%s,{col:section})' % (PN('cost'), PN('shop'), PN('section')), 11),
    CA('shop_items', 'Items at this shop', 'int', 'SUMIFS(%s,%s,{col:shop})' % (R('shop_split', 'items_to_buy'), R('shop_split', 'shop')), 9),
    CA('shop_cost', 'Cost line at this shop', 'money', 'SUMIFS(%s,%s,{col:shop})' % (R('shop_split', 'cost'), R('shop_split', 'shop')), 11)],
    D.shop_split_d(), 50, [A('items_to_buy', '> 0', 'warn')]))
# 14 staples that run out -----------------------------------------------------
tables.append(T('staples', 'Staples that run out', 'How often each item is on a list, ranked',
    'One row per item: weeks on a list in the last 26 complete weeks, share of weeks, when it was last bought and a rank; the item and its section are typed once.', [
    REF('item', 'Item', 'items.item', 22, required=True), LST('section', 'Section', 'section', 16),
    CA('item_no', 'Item number', 'int', 'IFERROR(VALUE(RIGHT(INDEX(%s,MATCH({col:item},%s,0)),3)),0)' % (R('items', 'item_id'), R('items', 'item')), 8),
    CA('weeks', 'Weeks on a list, last 26', 'int', 'SUMIFS(%s,%s,{col:item},%s,">="&(%s-182),%s,"<"&%s)' % (GIT('first_in_week'), GIT('item'), GIT('week'), TW, GIT('week'), TW), 10),
    CA('share', 'Share of weeks', 'pct', 'ROUND({col:weeks}/26,3)', 9),
    CA('last_bought', 'Last bought', 'date', 'IF(SUMIFS(%s,%s,{col:item},%s,1)=0,"",SUMIFS(%s,%s,{col:item},%s,1))' % (GIT('date'), GIT('item'), GIT('is_last'), GIT('date'), GIT('item'), GIT('is_last')), 11),
    CA('days_since', 'Days since last bought', 'int', 'IF({col:last_bought}="","",{today}-{col:last_bought})', 9),
    CA('rank', 'Runs out most, 1 is most', 'int', 'COUNTIFS(%s,">"&{col:weeks})+COUNTIFS(%s,{col:weeks},%s,"<"&{col:item_no})+1' % (R('staples', 'weeks'), R('staples', 'weeks'), R('staples', 'item_no')), 9),
    CA('standing', 'Standing item, 1 or 0', 'int', 'IF({col:weeks}>={set:staple_weeks},1,0)', 8), CA('shop_date', 'Next shop day', 'date', NEXT_SHOP, 11)] + A12() + [HOUSE()],
    D.staples_d(), 120, [A('standing', '= 1', 'good')]))
# 15 weekly spend history -----------------------------------------------------
def GW(col, lo, hi): return 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (GL(col), GL('date'), lo, GL('date'), hi)
tables.append(T('spend_hist', 'Weekly spend history', 'The last 26 complete weeks of lists, items and cost line',
    'One row per complete week, 1 is the last one: lists, items, estimated and actual cost line, the 4-week average before it and whether the week was heavier; no price advice.', [
    C('week_no', 'Weeks ago', 'int', 8, required=True), CA('week_start', 'Week starting', 'date', '%s-7*{col:week_no}' % TW, 11),
    CA('lists', 'Lists', 'int', 'COUNTIFS(%s,">="&{col:week_start},%s,"<"&({col:week_start}+7))' % (GL('date'), GL('date')), 7),
    CA('items', 'Items', 'int', GW('items', '{col:week_start}', '({col:week_start}+7)'), 8), CA('est_cost', 'Estimated cost', 'money', GW('est_cost', '{col:week_start}', '({col:week_start}+7)'), 11),
    CA('actual_cost', 'Actual cost', 'money', GW('actual_cost', '{col:week_start}', '({col:week_start}+7)'), 11), CA('difference', 'Actual less estimate', 'money', 'ROUND({col:actual_cost}-{col:est_cost},2)', 11),
    CA('avg4_cost', 'Average cost of the 4 weeks before', 'money', 'ROUND(%s/4,2)' % GW('actual_cost', '({col:week_start}-28)', '{col:week_start}'), 12),
    CA('avg4_items', 'Average items of the 4 weeks before', 'num', 'ROUND(%s/4,1)' % GW('items', '({col:week_start}-28)', '{col:week_start}'), 12),
    CA('vs_avg', 'Cost against that average', 'pct', 'IFERROR(ROUND({col:actual_cost}/{col:avg4_cost}-1,3),0)', 10),
    CA('within_avg', 'Within the usual range, 1 or 0', 'int', 'IF({col:actual_cost}<={col:avg4_cost}*(1+{set:heavy_margin}),1,0)', 9),
    CA('heavier_by', 'Items more than usual', 'int', 'ROUND({col:items}-{col:avg4_items},0)', 9), NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone'), HOUSE()],
    D.spend_hist_d(), 50, [A('within_avg', '= 0', 'warn')]))
# 16 recipe use history -------------------------------------------------------
NXT = 'SUMPRODUCT(MIN(%s+((%s<>{col:rid})+(%s<{today})>0)*1000000000))' % (MP('date'), MP('recipe_id'), MP('date'))
tables.append(T('recipe_hist', 'Recipe use history', 'When each recipe was last planned and which is due a turn',
    'One row per recipe: times planned in 12 months, last planned, next planned, days since and a rank of the rarely planned; type the recipe name once.', [
    REF('recipe', 'Recipe', 'recipes.recipe', 28, required=True), CA('rid', 'Recipe ID', 'text', LKT('recipes.recipe_id', 'recipes.recipe', 'recipe'), 9),
    CA('category', 'Category', 'text', LKT('recipes.category', 'recipes.recipe', 'recipe'), 16), CA('prep_min', 'Prep minutes', 'int', LKN('recipes.prep_min', 'recipes.recipe', 'recipe'), 9),
    CA('planned_12m', 'Planned in 12 months', 'int', 'COUNTIFS(%s,{col:rid},%s,">="&({today}-364),%s,"<="&{today})' % (MP('recipe_id'), MP('date'), MP('date')), 10),
    CA('last_planned', 'Last planned', 'date', 'IF(SUMPRODUCT(MAX((%s={col:rid})*(%s<={today})*%s))=0,"",SUMPRODUCT(MAX((%s={col:rid})*(%s<={today})*%s)))' % ((MP('recipe_id'), MP('date'), MP('date')) * 2), 11),
    CA('next_planned', 'Next planned', 'date', 'IF(COUNTIFS(%s,{col:rid},%s,">="&{today})=0,"",%s)' % (MP('recipe_id'), MP('date'), NXT), 11),
    CA('days_since', 'Days since last planned', 'int', 'IF({col:last_planned}="","",{today}-{col:last_planned})', 9),
    CA('rare_score', 'Rarely planned score', 'int', 'IF({col:last_planned}="",100000,{col:days_since})', 9), CA('rno', 'Recipe number', 'int', 'VALUE(RIGHT({col:rid},2))', 8),
    CA('rare_rank', 'Due a turn, 1 is most', 'int', 'COUNTIFS(%s,">"&{col:rare_score})+COUNTIFS(%s,{col:rare_score},%s,"<"&{col:rno})+1' % (R('recipe_hist', 'rare_score'), R('recipe_hist', 'rare_score'), R('recipe_hist', 'rno')), 9),
    NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone'), HOUSE()], D.recipe_hist_d(), 80))
# 17 cook and prep load -------------------------------------------------------
def SHL(col): return 'IFERROR(INDEX(%s,MATCH({col:date},%s,0))&"","")' % (R('shifts', col), R('shifts', 'date'))
tables.append(T('cook_load', 'Cook and prep load', 'Who cooks and how many prep minutes each of the next 14 days',
    'Type the day numbers 0 to 13 once; adult 2 shift, adult 1 late day, the suggested cook, the planned cook, dinner, prep minutes and a mismatch flag fill in from the work pattern and meal plan.', [
    C('day_no', 'Day number', 'int', 8, required=True), LST('week', 'Plan week', 'wk', 9), CA('date', 'Date', 'date', '{today}+{col:day_no}', 11),
    CA('a2_shift', 'Adult 2 shift', 'text', SHL('adult2_shift'), 10), CA('late1', 'Adult 1 late day, 1 or 0', 'int', 'IF(COUNTIFS(%s,{col:date},%s,%s)>0,1,0)' % (R('shifts', 'date'), R('shifts', 'adult1_late'), YES), 9),
    CA('suggested', 'Suggested cook', 'text', SHL('suggest'), 13), CA('planned_cook', 'Planned cook', 'text', DLOOK('cook'), 10), CA('recipe', 'Dinner', 'text', DLOOK('recipe'), 24),
    CA('servings', 'Servings', 'int', DLOOK('servings'), 8), CA('dinner_prep', 'Dinner prep minutes', 'int', DLOOK('prep_min'), 9),
    CA('dinners', 'Dinners planned', 'int', 'COUNTIFS(%s,{col:date},%s,%s)' % (MP('date'), MP('slot'), DIN), 8),
    CA('prep', 'Prep minutes, all meals', 'int', 'SUMIFS(%s,%s,{col:date})' % (MP('prep_min'), MP('date')), 9),
    CA('prep_w1', 'Prep minutes, next 7 days', 'int', 'IF({col:day_no}<7,{col:prep},"")', 9),
    CA('over_limit', 'Over the busy-day limit, 1 or 0', 'int', 'IF({col:prep}>{set:busy_limit},1,0)', 9),
    CA('check', 'Check', 'text', 'IF({col:suggested}=%s,%s,IF(OR({col:suggested}=%s,{col:planned_cook}=""),"",IF({col:planned_cook}={col:suggested},%s,%s)))' % (V_PREP, V_PREPNEED, V_EITHER, V_MATCH, V_CHECK), 16),
    CA('eat_at', 'Dinner time', 'time', 'IF({col:late1}=1,{set:late_dinner_hour},{set:dinner_hour})/24', 9),
    CA('start_by', 'Start cooking by', 'time', 'IF({col:dinner_prep}="","",({col:eat_at}*1440-{col:dinner_prep})/1440)', 9), CA('back_by', 'Dog back by', 'time', '{col:eat_at}-1/24', 9),
    CA('plan_by', 'Recipe ideas by', 'date', '{col:date}-2', 11),
    CA('dinners_week', 'Dinners planned, 7 days from this date', 'int', 'COUNTIFS(%s,%s,%s,">="&{col:date},%s,"<="&({col:date}+6))' % (MP('slot'), DIN, MP('date'), MP('date')), 10)]
    + A12() + [NAME('Dog walker', 'dw_name'), PHONE('Dog walker', 'dw_phone'), HOUSE()],
    D.cook_load_d(), 50, [A('check', '= ' + V_CHECK, 'warn'), A('check', '= ' + V_PREPNEED, 'warn'), A('over_limit', '= 1', 'warn')]))
# 18 preference labels in the plan -------------------------------------------
tables.append(T('pref_mix', 'Preference labels', 'Preference labels of recipes and the next 14 dinners',
    'One row per plain preference label: recipes carrying it and dinners planned with it in the next 14 days.', [
    LST('label', 'Label', 'pref', 18, required=True),
    CA('recipes', 'Recipes', 'int', 'COUNTIFS(%s,{col:label})' % R('recipes', 'pref_label'), 9),
    CA('dinners14', 'Dinners planned, next 14 days', 'int', 'COUNTIFS(%s,{col:label},%s,%s,%s)' % (MP('pref_label'), MP('slot'), DIN, N14), 11)], D.pref_mix_d(), 50))
# 19 plan scenarios -----------------------------------------------------------
tables.append(T('scenarios', 'Plan scenarios', 'Ready scenarios: a week with one adult away, guests, a party',
    'One row per scenario you plan for: days from today, how long, adults, children and guests at the table; the dates and servings fill in. Use them with the One adult away and Guests staying tools.', [
    C('scenario', 'Scenario', 'text', 34, required=True), C('day_offset', 'Starts in days', 'int', 9), C('days', 'Days', 'int', 7), C('adults', 'Adults', 'int', 8), C('children', 'Children', 'int', 9),
    C('guests', 'Guests', 'int', 8), C('note', 'Note', 'text', 30),
    CA('date', 'From', 'date', '{today}+{col:day_offset}', 11), CA('end_date', 'To', 'date', '{col:date}+{col:days}-1', 11),
    CA('servings', 'Servings per dinner', 'int', '{col:adults}+{col:children}+{col:guests}', 9), CA('change', 'Against the usual eaters', 'int', '{col:servings}-{set:usual_eaters}', 10),
    CA('portions', 'Dinner portions in the period', 'int', '{col:servings}*{col:days}', 10)] + [NAME('Adult 1', 'a1_name'), PHONE('Adult 1', 'a1_phone'), HOUSE()],
    D.scenarios_d(), 50, [A('change', '< 0', 'warn'), A('change', '> 0', 'good')]))
# 20 month at a glance --------------------------------------------------------
def MG(extra): return 'COUNTIFS(%s,%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1)%s)' % (MP('slot'), DIN, MP('date'), MP('date'), extra)
tables.append(T('month_glance', 'Month at a glance', 'Dinners planned and cooked, grocery cost line by month',
    'One row per month: dinners planned and cooked, the share cooked, lists, items and the grocery cost line; type the month once. Complete months compare best.', [
    C('month', 'Month', 'date', 11, required=True), CA('dinners_planned', 'Dinners planned', 'int', MG(''), 9),
    CA('planned_to_date', 'Dinners planned up to today', 'int', 'COUNTIFS(%s,%s,%s,">="&{col:month},%s,"<"&MIN(EDATE({col:month},1),{today}+1))' % (MP('slot'), DIN, MP('date'), MP('date')), 10),
    CA('dinners_cooked', 'Dinners cooked', 'int', MG(',%s,%s' % (MP('cooked'), YES)), 9),
    CA('share_cooked', 'Share cooked', 'pct', 'IF({col:planned_to_date}=0,"",ROUND({col:dinners_cooked}/{col:planned_to_date},3))', 9),
    CA('lists', 'Lists', 'int', 'COUNTIFS(%s,">="&{col:month},%s,"<"&EDATE({col:month},1),%s,%s)' % (GL('date'), GL('date'), GL('status'), BOUGHT), 7),
    CA('items', 'Items', 'int', 'SUMIFS(%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1),%s,%s)' % (GL('items'), GL('date'), GL('date'), GL('status'), BOUGHT), 8),
    CA('grocery_cost', 'Grocery cost line', 'money', 'SUMIFS(%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1))' % (GL('actual_cost'), GL('date'), GL('date')), 12),
    CA('cost_per_dinner', 'Cost line per dinner cooked', 'money', 'IF({col:dinners_cooked}=0,"",ROUND({col:grocery_cost}/{col:dinners_cooked},2))', 11),
    NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone'), HOUSE()],
    D.month_glance_d(), 50))
assert len(tables) == 20, len(tables)
