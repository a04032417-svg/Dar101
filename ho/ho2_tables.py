"""Home Management suite part 2: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho2_lists import *
import ho2_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def CL(k): return '{col:%s}' % k
def G(keycol, expr): return 'IF({col:%s}="","",%s)' % (keycol, expr)
def LKS(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),"")' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)


def STK(c): return R('stock', c)
def ING(c): return R('ingredients', c)
def MEAL(c): return R('meal_plan', c)
def LEF(c): return R('leftovers', c)
def REC(c): return R('recipes', c)
def ITM(c): return R('items', c)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
SHIFT = 'IF({set:week_start}=%s,6,IF({set:week_start}=%s,5,0))' % (tok('wday', 'Sunday'), tok('wday', 'Saturday'))
WK0 = '({today}-MOD(WEEKDAY({today},2)-1-%s,7))' % SHIFT          # first day of this week
D30 = '{today}-29'


def DT(d):
    """a day and month in words from a date expression (formulas never write a month name as text)"""
    ms = ','.join(MT(i) for i in range(12))
    return 'DAY(%s)&" "&CHOOSE(MONTH(%s),%s)&" "&YEAR(%s)' % (d, d, ms, d)


ROLE_OF = {'a1': ('Adult 1', 'Adult 1'), 'a2': ('Adult 2', 'Adult 2'), 'gp': ('Grandparent', 'Grandparent'), 'bs': ('Babysitter', 'Babysitter'), 'nb': ('Neighbour', 'Neighbour'),
           'sc': ('School office', 'School office'), 'cp': ('Carpool family', 'Carpool family')}


def TL(role, col): return 'IFERROR(INDEX({range:team.%s},MATCH({list:role.%s},{range:team.role},0))&"","")' % (col, key('role', role))


def CT(guard, *who):
    """calculated name and phone columns of household members and outside contacts, blank on rows without a key"""
    out = []
    for w in who:
        if w in ('c1', 'c2'):
            n = 'child%s' % w[1]
            out.append(CA(w + '_name', ('Child %s name' % w[1]), 'text', G(guard, '{set:%s}' % n), 22))
            out.append(CA(w + '_phone', ('Child %s phone' % w[1]), 'text', G(guard, 'IFERROR(INDEX({range:team.phone},MATCH({set:%s_id},{range:team.member_id},0))&"","")' % n), 18))
        else:
            role, label = ROLE_OF[w]
            out.append(CA(w + '_name', label + ' name', 'text', G(guard, TL(role, 'name')), 22))
            out.append(CA(w + '_phone', label + ' phone', 'text', G(guard, TL(role, 'phone')), 18))
    out.append(CA('household', 'Household', 'text', G(guard, '{set:household}'), 24))
    return out


def HOUSE(): return CA('household', 'Household', 'text', '{set:household}', 24)


settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('adult1', 'Adult 1 shown as', 'text', 'Adult 1'), S('adult2', 'Adult 2 shown as', 'text', 'Adult 2'),
    S('child1', 'Child 1 first name', 'text', first_name(team[2]['name'])), S('child2', 'Child 2 first name', 'text', first_name(team[3]['name'])),
    S('child1_id', 'Member ID of child 1 on Team', 'text', 'HO-03'), S('child2_id', 'Member ID of child 2 on Team', 'text', 'HO-04'),
    S('week_start', 'Week starts on', 'list', 'monday', list='wday'),
    S('use_soon_days', 'Use soon window in days, typical, check the label', 'int', USE_SOON_DAYS),
    S('leftover_days', 'Fridge days of cooked leftovers, typical 3 to 4, see label', 'int', FOOD_DAYS_TYPICAL),
    S('freezer_months', 'Freezer months of cooked dishes, typical 2 to 3, see label', 'int', 3),
    S('cooked_days', 'Cooked dishes rank this many days earlier in Use First', 'int', 3),
    S('freezer_capacity', 'Chest freezer space in units, a number you type', 'int', 60),
    S('shelf_tolerance', 'Shelf check: share either side that counts as typical', 'pct', 0.3),
    S('next_shop', 'Date of the next shop', 'date', ahead(3)), S('trip_start', 'Next trip away: leaving on', 'date', ahead(12)), S('trip_end', 'Next trip away: back on', 'date', ahead(19)),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 team ------------------------------------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact with phone and e-mail; the messages in this workbook use these phone numbers.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('group', 'Group', 'tgroup', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11), HOUSE()], D.team_d(), 50))
# 2 item catalog ----------------------------------------------------------------------------------------
tables.append(T('items', 'Item Catalog', 'Item catalog with pack sizes, minimum stock and shop',
    'One row per item you buy: section, unit, place, pack size, typical shelf days (typical, check the label), minimum stock and shop; stock now, packs to buy and last bought fill in.', [
    C('item_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 24), LST('section', 'Section', 'section', 16), LST('unit', 'Unit', 'unit', 8), LST('place', 'Place', 'place', 13),
    C('per_serving', 'Per serving', 'num', 10), C('pack_size', 'Pack size', 'num', 10), C('shelf_days', 'Typical shelf days', 'int', 10), C('min_stock', 'Minimum stock', 'num', 10),
    C('pack_price', 'Pack price', 'money', 11), LST('shop', 'Shop', 'shop', 13),
    CA('seq', 'Sequence', 'int', G('item_id', 'VALUE(RIGHT({col:item_id},3))'), 8),
    CA('stock_qty', 'Stock now', 'num', G('item_id', 'SUMIFS(%s,%s,{col:item})' % (STK('quantity'), STK('item'))), 10),
    CA('below', 'At or below minimum, 1 or 0', 'int', G('item_id', 'IF(AND({col:min_stock}>0,{col:stock_qty}<={col:min_stock}),1,0)'), 9),
    CA('gap', 'Short of the minimum', 'num', G('item_id', 'IF({col:below}=1,MAX(0,ROUND({col:min_stock}-{col:stock_qty},2)),0)'), 10),
    CA('packs', 'Packs to buy', 'int', G('item_id', 'IF({col:below}=1,IF({col:pack_size}>0,MAX(1,ROUNDUP(ROUND({col:gap}/{col:pack_size},6),0)),1),0)'), 8),
    CA('pack_cost', 'Cost line of the packs', 'money', G('item_id', 'ROUND({col:packs}*{col:pack_price},2)'), 11),
    CA('rank', 'Buy first, 1 is first', 'int', G('item_id', 'IF({col:packs}>0,COUNTIFS(%s,">"&{col:packs})+COUNTIFS(%s,{col:packs},%s,"<"&{col:seq})+1,"")' % (ITM('packs'), ITM('packs'), ITM('seq'))), 9),
    CA('last_bought', 'Last bought', 'date', G('item_id', 'IF(SUMPRODUCT(MAX((%s={col:item})*(%s=%s)*%s))=0,"",SUMPRODUCT(MAX((%s={col:item})*(%s=%s)*%s)))' % (R('bought', 'item'), R('bought', 'bought'), YES, R('bought', 'date'), R('bought', 'item'), R('bought', 'bought'), YES, R('bought', 'date'))), 11),
    CA('days_since', 'Days since bought', 'int', G('item_id', 'IF({col:last_bought}="","",{today}-{col:last_bought})'), 9),
    CA('servings', 'Servings in stock', 'num', G('item_id', 'IF({col:per_serving}>0,ROUND({col:stock_qty}/{col:per_serving},0),"")'), 9)],
    D.items_d(), 120, [A('below', '= 1', 'warn')]))
# 3 stock -----------------------------------------------------------------------------------------------
tables.append(T('stock', 'Stock', 'Pantry, fridge and chest freezer stock with use-by dates',
    'One row per item or cooked dish on a shelf: place, quantity, added and use-by date typed from the label; days left, status, minimum check, plan check and ranks fill in.', [
    C('stock_id', 'Stock ID', 'text', 9, required=True), C('item', 'Item', 'text', 24), LST('place', 'Place', 'place', 13), C('quantity', 'Quantity', 'num', 10), LST('unit', 'Unit', 'unit', 8),
    C('added', 'Added', 'date', 11), C('use_by', 'Use by', 'date', 11), C('min_qty', 'Minimum', 'num', 9), LST('section', 'Section', 'section', 16), C('recipe_id', 'Recipe ID', 'text', 9),
    LST('shop', 'Shop', 'shop', 13), C('counted', 'Counted', 'num', 9),
    CA('seq', 'Sequence', 'int', G('stock_id', 'VALUE(RIGHT({col:stock_id},3))'), 8),
    CA('days', 'Days to use-by', 'int', G('stock_id', 'IF({col:use_by}>0,{col:use_by}-{today},"")'), 9),
    CA('status', 'Status', 'text', G('stock_id', 'IF({col:use_by}>0,IF({col:use_by}<{today},%s,IF({col:use_by}-{today}<={set:use_soon_days},%s,%s)),%s)' % (PAST, SOON, OK, OK)), 10),
    CA('below', 'At or below minimum, 1 or 0', 'int', G('stock_id', 'IF(AND({col:min_qty}>0,{col:quantity}<={col:min_qty}),1,0)'), 9),
    CA('stored', 'Days from added to use-by', 'int', G('stock_id', 'IF(AND({col:added}>0,{col:use_by}>0),{col:use_by}-{col:added},"")'), 9),
    CA('in_plan', 'In the next 7 days plan, 1 or 0', 'int', G('stock_id', 'IF({col:recipe_id}<>"",IF(COUNTIFS(%s,{col:recipe_id},%s,1)>0,1,0),IF(COUNTIFS(%s,{col:item},%s,">0")>0,1,0))' % (MEAL('recipe_id'), MEAL('in_window'), ING('item'), ING('planned'))), 9),
    CA('frz_m', 'Months in the freezer', 'num', G('stock_id', 'IF(AND({col:place}=%s,{col:added}>0),ROUND(({today}-{col:added})/30.4,1),"")' % FREEZER), 9),
    CA('frz_ok', 'Within typed months, 1 or 0', 'int', G('stock_id', 'IF({col:frz_m}="","",IF({col:frz_m}<={set:freezer_months},1,0))'), 9),
    CA('frz_rank', 'Freezer rank, oldest first', 'int', G('stock_id', 'IF({col:frz_m}="","",COUNTIFS(%s,">"&{col:frz_m})+COUNTIFS(%s,{col:frz_m},%s,"<"&{col:seq})+1)' % (STK('frz_m'), STK('frz_m'), STK('seq'))), 9),
    CA('use_score', 'Use-first score', 'num', G('stock_id', 'IF(AND({col:use_by}>0,{col:use_by}>={today}),{col:days}-IF({col:recipe_id}<>"",{set:cooked_days},0),"")'), 9),
    CA('use_rank', 'Use first, 1 is first', 'int', G('stock_id', 'IF({col:use_score}="","",COUNTIFS(%s,"<"&{col:use_score})+COUNTIFS(%s,{col:use_score},%s,"<"&{col:seq})+1)' % (STK('use_score'), STK('use_score'), STK('seq'))), 9),
    CA('fr_score', 'Fridge order score', 'num', G('stock_id', 'IF({col:place}=%s,IF({col:use_by}>0,{col:days},9999),"")' % FRIDGE), 9),
    CA('fr_rank', 'Fridge order', 'int', G('stock_id', 'IF({col:fr_score}="","",COUNTIFS(%s,"<"&{col:fr_score})+COUNTIFS(%s,{col:fr_score},%s,"<"&{col:seq})+1)' % (STK('fr_score'), STK('fr_score'), STK('seq'))), 9),
    CA('diff', 'Counted less recorded', 'num', G('stock_id', 'IF({col:counted}="","",ROUND({col:counted}-{col:quantity},2))'), 10),
    CA('absdiff', 'Difference, any sign', 'num', G('stock_id', 'IF({col:diff}="","",ABS({col:diff}))'), 9),
    CA('adjust', 'To adjust, 1 or 0', 'int', G('stock_id', 'IF({col:diff}="","",IF({col:diff}<>0,1,0))'), 8),
    CA('adjust_n', 'Items to adjust', 'int', G('stock_id', 'COUNTIFS(%s,1)' % STK('adjust')), 8),
    CA('check_date', 'Check date', 'date', G('stock_id', '{today}'), 11)] + CT('stock_id', 'a1'),
    D.stock_d(), 150, [A('status', '= ' + PAST, 'bad'), A('status', '= ' + SOON, 'warn'), A('status', '= ' + OK, 'good'), A('below', '= 1', 'warn')]))
# 4 leftovers -------------------------------------------------------------------------------------------
tables.append(T('leftovers', 'Leftovers', 'Leftovers and batch-cooked dishes with portions and eat-by',
    'One row per cooked dish: date cooked, portions made and left, the date it went to the freezer and the eat-by date you type; days left, status and the board rank fill in.', [
    C('leftover_id', 'Leftover ID', 'text', 10, required=True), C('date', 'Cooked on', 'date', 11), C('dish', 'Dish', 'text', 24), C('recipe_id', 'Recipe ID', 'text', 9),
    C('portions_made', 'Portions made', 'int', 9), C('portions_left', 'Portions left', 'int', 9), C('to_freezer', 'To freezer on', 'date', 11), C('eat_by', 'Eat by', 'date', 11),
    LST('category', 'Dish kind', 'dkind', 18),
    CA('seq', 'Sequence', 'int', G('leftover_id', 'VALUE(RIGHT({col:leftover_id},3))'), 8),
    CA('days_left', 'Days to eat-by', 'int', G('leftover_id', 'IF({col:portions_left}>0,{col:eat_by}-{today},"")'), 9),
    CA('status', 'Status', 'text', G('leftover_id', 'IF({col:portions_left}=0,%s,IF({col:eat_by}<{today},%s,IF({col:eat_by}-{today}<={set:use_soon_days},%s,%s)))' % (FIN, PAST, SOON, OK)), 10),
    CA('frozen', 'Frozen, 1 or 0', 'int', G('leftover_id', 'IF({col:to_freezer}>0,1,0)'), 8),
    CA('in_plan', 'In the next 7 days plan, 1 or 0', 'int', G('leftover_id', 'IF({col:recipe_id}<>"",IF(COUNTIFS(%s,{col:recipe_id},%s,1)>0,1,0),0)' % (MEAL('recipe_id'), MEAL('in_window'))), 9),
    CA('closed', 'Eaten or within date, 1 or 0', 'int', G('leftover_id', 'IF(OR({col:portions_left}=0,{col:eat_by}>={today}),1,0)'), 9),
    CA('board_score', 'Board score', 'int', G('leftover_id', 'IF({col:portions_left}>0,{col:eat_by},90000+(50000-{col:date}))'), 9),
    CA('board_rank', 'Board rank', 'int', G('leftover_id', 'COUNTIFS(%s,"<"&{col:board_score})+COUNTIFS(%s,{col:board_score},%s,"<"&{col:seq})+1' % (LEF('board_score'), LEF('board_score'), LEF('seq'))), 8),
    CA('tomorrow', 'Tomorrow', 'date', G('leftover_id', '{today}+1'), 11),
    CA('friday', 'Next Friday', 'date', G('leftover_id', '{today}+MOD(5-WEEKDAY({today},2),7)'), 11)] + CT('leftover_id', 'a1', 'a2', 'gp', 'bs', 'cp', 'sc', 'c1'),
    D.leftovers_d(), 150, [A('status', '= ' + PAST, 'bad'), A('status', '= ' + SOON, 'warn'), A('status', '= ' + OK, 'good')]))
# 5 recipes ---------------------------------------------------------------------------------------------
tables.append(T('recipes', 'Recipes', 'Household recipes scored by what is in stock',
    'One row per recipe with prep minutes, servings and a preference label; ingredients on hand, share on hand, expiring items used, score and rank fill in from Stock.', [
    C('recipe_id', 'Recipe ID', 'text', 9, required=True), C('recipe', 'Recipe', 'text', 26), LST('category', 'Category', 'rcat', 16), C('prep_min', 'Prep minutes', 'int', 9), C('servings', 'Servings', 'int', 9),
    LST('pref_label', 'Preference label', 'pref', 16), C('ingredient_count', 'Ingredient count', 'int', 9),
    CA('seq', 'Sequence', 'int', G('recipe_id', 'VALUE(RIGHT({col:recipe_id},2))'), 8),
    CA('ing_n', 'Ingredients typed', 'int', G('recipe_id', 'COUNTIFS(%s,{col:recipe_id})' % ING('recipe_id')), 9),
    CA('on_n', 'Ingredients on hand', 'int', G('recipe_id', 'COUNTIFS(%s,{col:recipe_id},%s,1)' % (ING('recipe_id'), ING('on_hand'))), 9),
    CA('miss_n', 'Ingredients missing', 'int', G('recipe_id', '{col:ing_n}-{col:on_n}'), 9),
    CA('share', 'Share on hand', 'pct', G('recipe_id', 'IF({col:ing_n}>0,{col:on_n}/{col:ing_n},0)'), 9),
    CA('soon_n', 'Expiring items it uses', 'int', G('recipe_id', 'COUNTIFS(%s,{col:recipe_id},%s,1)' % (ING('recipe_id'), ING('soon'))), 9),
    CA('score', 'Cook-first score', 'num', G('recipe_id', 'ROUND({col:share}*100+15*{col:soon_n},1)'), 9),
    CA('rank', 'Cook first, 1 is first', 'int', G('recipe_id', 'COUNTIFS(%s,">"&{col:score})+COUNTIFS(%s,{col:score},%s,"<"&{col:seq})+1' % (REC('score'), REC('score'), REC('seq'))), 9),
    CA('ready', 'Ready, 1 or 0', 'int', G('recipe_id', 'IF(AND({col:ing_n}>0,{col:miss_n}=0),1,0)'), 8),
    CA('one_rank', 'One-missing rank', 'int', G('recipe_id', 'IF({col:miss_n}=1,COUNTIFS(%s,1,%s,">"&{col:score})+COUNTIFS(%s,1,%s,{col:score},%s,"<"&{col:seq})+1,"")' % (REC('miss_n'), REC('score'), REC('miss_n'), REC('score'), REC('seq'))), 9),
    CA('missing_first', 'First missing ingredient', 'text', G('recipe_id', 'IF({col:miss_n}>=1,IFERROR(INDEX(%s,MATCH({col:recipe_id}&"|1",%s,0)),""),"")' % (ING('item'), ING('mkey'))), 20),
    CA('planned', 'Planned in the next 7 days', 'int', G('recipe_id', 'COUNTIFS(%s,{col:recipe_id},%s,1)' % (MEAL('recipe_id'), MEAL('in_window'))), 9)],
    D.recipes_d(), 100, [A('ready', '= 1', 'good')]))
# 6 recipe ingredients ----------------------------------------------------------------------------------
tables.append(T('ingredients', 'Recipe ingredients', 'Ingredient lines of every recipe, checked against stock',
    'One row per ingredient of a recipe: quantity for the recipe servings; on hand (stock not past the date and at least the quantity), expiring and planned fill in from Stock and Meal Plan.', [
    C('ingredient_id', 'Ingredient ID', 'text', 10, required=True), C('recipe_id', 'Recipe ID', 'text', 9), C('recipe', 'Recipe', 'text', 26), C('item', 'Item', 'text', 22), C('qty', 'Quantity', 'num', 9),
    LST('unit', 'Unit', 'unit', 8), LST('section', 'Section', 'section', 16),
    CA('seq', 'Sequence', 'int', G('ingredient_id', 'VALUE(RIGHT({col:ingredient_id},4))'), 8),
    CA('on_hand', 'On hand, 1 or 0', 'int', G('ingredient_id', 'IF(SUMIFS(%s,%s,{col:item},%s,"<>"&%s)>={col:qty},1,0)' % (STK('quantity'), STK('item'), STK('status'), PAST)), 8),
    CA('soon', 'Expiring, 1 or 0', 'int', G('ingredient_id', 'IF({col:on_hand}=1,IF(SUMIFS(%s,%s,{col:item},%s,%s)>0,1,0),0)' % (STK('quantity'), STK('item'), STK('status'), SOON)), 8),
    CA('planned', 'Recipe planned in the next 7 days', 'int', G('ingredient_id', 'COUNTIFS(%s,{col:recipe_id},%s,1)' % (MEAL('recipe_id'), MEAL('in_window'))), 9),
    CA('share', 'Recipe share on hand', 'pct', G('ingredient_id', 'IFERROR(INDEX(%s,MATCH({col:recipe_id},%s,0)),0)' % (REC('share'), REC('recipe_id'))), 9),
    CA('mrank', 'Missing order in the recipe', 'int', G('ingredient_id', 'IF({col:on_hand}=0,COUNTIFS(%s,{col:recipe_id},%s,0,%s,"<"&{col:seq})+1,"")' % (ING('recipe_id'), ING('on_hand'), ING('seq'))), 9),
    CA('mkey', 'Missing key', 'text', G('ingredient_id', 'IF({col:mrank}="","",{col:recipe_id}&"|"&{col:mrank})'), 10),
    CA('frank', 'Best recipe for the item', 'int', G('ingredient_id', 'COUNTIFS(%s,{col:item},%s,">"&{col:share})+COUNTIFS(%s,{col:item},%s,{col:share},%s,"<"&{col:seq})+1' % (ING('item'), ING('share'), ING('item'), ING('share'), ING('seq'))), 9),
    CA('fkey', 'Item key', 'text', G('ingredient_id', '{col:item}&"|"&{col:frank}'), 10)],
    D.ingredients_d(), 400, [A('on_hand', '= 0', 'warn')]))
# 7 meal plan -------------------------------------------------------------------------------------------
tables.append(T('meal_plan', 'Meal plan', 'Meal plan for the last 30 days and the next 14',
    'One row per planned meal: date, slot, recipe, servings and cook; the next 7 days flag, the use-soon items in the recipe and the dinner date fill in.', [
    C('plan_id', 'Plan ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('slot', 'Slot', 'slot', 11), C('recipe_id', 'Recipe ID', 'text', 9), C('recipe', 'Recipe', 'text', 26),
    C('servings', 'Servings', 'int', 9), LST('cook', 'Cook', 'person', 11), C('prep_min', 'Prep minutes', 'int', 9), C('cooked', 'Cooked', 'bool', 9),
    CA('in_window', 'Next 7 days, 1 or 0', 'int', G('plan_id', 'IF(AND({col:date}>={today},{col:date}<={today}+6),1,0)'), 8),
    CA('soon_items', 'Use-soon items in the recipe', 'int', G('plan_id', 'COUNTIFS(%s,{col:recipe_id},%s,1)' % (ING('recipe_id'), ING('soon'))), 9),
    CA('dinner_date', 'Dinner date', 'date', G('plan_id', 'IF({col:slot}=%s,{col:date},"")' % DINNER), 11)],
    D.meal_plan_d(), 150, [A('in_window', '= 1', 'good')]))
# 8 bought lines ----------------------------------------------------------------------------------------
tables.append(T('bought', 'Bought Lines', 'Recent grocery lines bought, with their date and cost line',
    'One row per grocery line from your lists: date, item, quantity, bought or not and the cost line; days ago fills in and the Item Catalog shows the last bought date per item.', [
    C('grocery_item_id', 'Line ID', 'text', 10, required=True), C('list_id', 'List ID', 'text', 9), C('date', 'List date', 'date', 11), C('item', 'Item', 'text', 22), C('qty', 'Quantity', 'num', 9),
    LST('unit', 'Unit', 'unit', 8), C('bought', 'Bought', 'bool', 8), C('cost', 'Cost line', 'money', 11),
    CA('days_ago', 'Days ago', 'int', G('grocery_item_id', '{today}-{col:date}'), 8)],
    D.bought_d(), 500))
# 9 stock status board ----------------------------------------------------------------------------------
def SB(c): return LKS('stock.' + c, 'stock.stock_id', 'stock_id')
def SBN(c): return LKN('stock.' + c, 'stock.stock_id', 'stock_id')
tables.append(T('stock_board', 'Stock Status Board', 'Every stock row with its status, plan check and next action',
    'One row per stock row: days to use-by, ok, use soon or past date, the minimum check, whether the next 7 days plan uses it and the action; pick the stock IDs once.', [
    REF('stock_id', 'Stock ID', 'stock.stock_id', 9, required=True),
    CA('item', 'Item', 'text', G('stock_id', SB('item')), 24), CA('place', 'Place', 'text', G('stock_id', SB('place')), 13),
    CA('days', 'Days to use-by', 'int', G('stock_id', SBN('days')), 9), CA('status', 'Status', 'text', G('stock_id', SB('status')), 10),
    CA('below', 'At or below minimum', 'int', G('stock_id', SBN('below')), 9),
    CA('in_plan', 'Next 7 days plan', 'text', G('stock_id', 'IF(%s=1,%s,%s)' % (SBN('in_plan'), IN_PLAN, NOT_PLAN)), 14),
    CA('rank_use', 'Rank to use first', 'int', G('stock_id', SBN('use_rank')), 9),
    CA('action', 'Action', 'text', G('stock_id', 'IF({col:status}=%s,%s,IF({col:status}=%s,IF({col:in_plan}=%s,%s,%s),%s))' % (PAST, W('check_clear'), SOON, NOT_PLAN, W('plan_it'), W('use_today'), W('fine'))), 16),
    CA('past_total', 'Items past the date', 'int', G('stock_id', 'COUNTIFS(%s,%s)' % (STK('status'), PAST)), 9), CA('check_date', 'Check date', 'date', G('stock_id', '{today}'), 11)] + CT('stock_id', 'a1', 'a2'),
    D.board_d(), 150, [A('status', '= ' + PAST, 'bad'), A('status', '= ' + SOON, 'warn'), A('status', '= ' + OK, 'good')]))
# 10 use first ranking ----------------------------------------------------------------------------------
def UF(c): return LKS('stock.' + c, 'stock.stock_id', 'stock_id')
tables.append(T('use_first', 'Use First Ranking', 'The 20 items and dishes to use first, nearest date on top',
    'Ranks stock not past its date by days left, with cooked dishes a few days earlier (Settings); shows the plan check and a recipe that uses the item; type 1 to 20 once.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('stock_id', 'Stock ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:rank},%s,0)),"")' % (STK('stock_id'), STK('use_rank')), 9),
    CA('item', 'Item', 'text', G('stock_id', UF('item')), 24), CA('place', 'Place', 'text', G('stock_id', UF('place')), 13),
    CA('use_by', 'Use by', 'date', G('stock_id', LKD('stock.use_by', 'stock.stock_id', 'stock_id')), 11),
    CA('days_left', 'Days left', 'int', G('stock_id', LKN('stock.days', 'stock.stock_id', 'stock_id')), 8),
    CA('in_plan', 'Next 7 days plan', 'text', G('stock_id', 'IF(%s=1,%s,%s)' % (LKN('stock.in_plan', 'stock.stock_id', 'stock_id'), IN_PLAN, NOT_PLAN)), 14),
    CA('recipe', 'Suggested recipe', 'text', G('stock_id', 'IF(%s<>"",%s,IFERROR(INDEX(%s,MATCH({col:item}&"|1",%s,0)),%s))' % (UF('recipe_id'), W('as_it_is'), ING('recipe'), ING('fkey'), W('no_recipe'))), 24),
    CA('plan_for', 'Plan it for', 'date', G('stock_id', 'IF({col:use_by}="","",MAX({today},{col:use_by}-1))'), 11),
    CA('week_of', 'Week of', 'date', G('stock_id', '{today}-WEEKDAY({today},2)+1'), 11)] + CT('stock_id', 'a1', 'a2', 'c1', 'c2', 'bs', 'nb'),
    D.ranks_d(20), 50, [A('in_plan', '= ' + NOT_PLAN, 'warn')]))
# 11 recipe readiness -----------------------------------------------------------------------------------
def RL(c): return LKN('recipes.' + c, 'recipes.recipe_id', 'recipe_id')
tables.append(T('recipe_ready', 'Recipe Readiness', 'Every recipe scored by the share of its ingredients on hand',
    'One row per recipe: ingredients, how many are on hand, the share, how many expiring items it uses, the score and the rank; pick the recipe IDs once.', [
    REF('recipe_id', 'Recipe ID', 'recipes.recipe_id', 9, required=True),
    CA('recipe', 'Recipe', 'text', G('recipe_id', LKS('recipes.recipe', 'recipes.recipe_id', 'recipe_id')), 26), CA('ingredients', 'Ingredients', 'int', G('recipe_id', RL('ing_n')), 9),
    CA('on_hand', 'On hand', 'int', G('recipe_id', RL('on_n')), 8), CA('share', 'Share on hand', 'pct', G('recipe_id', RL('share')), 9), CA('expiring', 'Expiring items used', 'int', G('recipe_id', RL('soon_n')), 9),
    CA('score', 'Score', 'num', G('recipe_id', RL('score')), 8), CA('rank', 'Rank', 'int', G('recipe_id', RL('rank')), 7),
    CA('missing', 'Missing', 'int', G('recipe_id', RL('miss_n')), 8),
    CA('status', 'Status', 'text', G('recipe_id', 'IF({col:ingredients}=0,%s,IF({col:missing}=0,%s,IF({col:missing}=1,%s,%s)))' % (W('as_it_is'), W('ready'), W('one_missing'), W('shopping'))), 22)],
    D.ready_d(), 100, [A('missing', '= 0', 'good')]))
# 12 cook this first ------------------------------------------------------------------------------------
def CK(c): return LKS('recipes.' + c, 'recipes.recipe_id', 'recipe_id')
tables.append(T('cook_first', 'Cook This First Ranking', 'The 12 recipes to cook first',
    'Ranks every recipe by the share of its ingredients on hand and the expiring items it uses; type 1 to 12 once and the verdict fills in.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('recipe_id', 'Recipe ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:rank},%s,0)),"")' % (REC('recipe_id'), REC('rank')), 9),
    CA('recipe', 'Recipe', 'text', G('recipe_id', CK('recipe')), 26), CA('share', 'Share on hand', 'pct', G('recipe_id', RL('share')), 9),
    CA('share_whole', 'Share on hand, percent', 'int', G('recipe_id', 'ROUND({col:share}*100,0)'), 9),
    CA('on_hand', 'Ingredients on hand', 'int', G('recipe_id', RL('on_n')), 9), CA('ingredients', 'Ingredients', 'int', G('recipe_id', RL('ing_n')), 9),
    CA('expiring', 'Expiring items used', 'int', G('recipe_id', RL('soon_n')), 9), CA('prep_min', 'Prep minutes', 'int', G('recipe_id', LKN('recipes.prep_min', 'recipes.recipe_id', 'recipe_id')), 9),
    CA('missing', 'Missing', 'int', G('recipe_id', RL('miss_n')), 8),
    CA('verdict', 'Verdict', 'text', G('recipe_id', 'IF({col:rank}=1,%s,IF({col:missing}=0,%s,IF({col:missing}=1,%s,%s)))' % (W('cook_this'), W('ready'), W('one_missing'), W('shopping'))), 20)] + CT('recipe_id', 'a1'),
    D.ranks_d(12), 50, [A('verdict', '= ' + W('cook_this'), 'good')]))
# 13 freezer inventory ----------------------------------------------------------------------------------
def FZ(c): return LKS('stock.' + c, 'stock.stock_id', 'stock_id')
tables.append(T('freezer', 'Freezer Inventory', 'Chest freezer inventory, oldest first',
    'Lists the chest freezer stock oldest first with quantity, months in the freezer against the typed months and the use-by date; type 1 to 25 once.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('stock_id', 'Stock ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:rank},%s,0)),"")' % (STK('stock_id'), STK('frz_rank')), 9),
    CA('item', 'Item or dish', 'text', G('stock_id', FZ('item')), 24), CA('quantity', 'Quantity', 'num', G('stock_id', LKN('stock.quantity', 'stock.stock_id', 'stock_id')), 9),
    CA('unit', 'Unit', 'text', G('stock_id', FZ('unit')), 8), CA('months', 'Months in the freezer', 'num', G('stock_id', LKN('stock.frz_m', 'stock.stock_id', 'stock_id')), 9),
    CA('use_by', 'Use by', 'date', G('stock_id', LKD('stock.use_by', 'stock.stock_id', 'stock_id')), 11), CA('status', 'Status', 'text', G('stock_id', FZ('status')), 10),
    CA('typed_ok', 'Within typed months', 'text', G('stock_id', 'IF(%s=1,%s,%s)' % (LKN('stock.frz_ok', 'stock.stock_id', 'stock_id'), W('hold'), W('check_clear'))), 14),
    CA('portions_total', 'Units in the freezer', 'num', G('stock_id', 'SUMIFS(%s,%s,%s)' % (STK('quantity'), STK('place'), FREEZER)), 9),
    CA('full_pct', 'Freezer full, percent', 'int', G('stock_id', 'ROUND({col:portions_total}/{set:freezer_capacity}*100,0)'), 9),
    CA('check_date', 'Check date', 'date', G('stock_id', '{today}'), 11)] + CT('stock_id', 'a1', 'a2', 'bs'),
    D.ranks_d(D.N_FRZ), 50, [A('status', '= ' + PAST, 'bad'), A('status', '= ' + SOON, 'warn')]))
# 14 fridge and leftovers check -------------------------------------------------------------------------
tables.append(T('fridge', 'Fridge and Leftovers Check', 'Fridge items and cooked dishes, nearest date first',
    'Lists the fridge stock and cooked dishes by days to the use-by date typed from the label, past dates first; type 1 to 30 once.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('stock_id', 'Stock ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:rank},%s,0)),"")' % (STK('stock_id'), STK('fr_rank')), 9),
    CA('item', 'Item or dish', 'text', G('stock_id', FZ('item')), 24), CA('quantity', 'Quantity', 'num', G('stock_id', LKN('stock.quantity', 'stock.stock_id', 'stock_id')), 9),
    CA('unit', 'Unit', 'text', G('stock_id', FZ('unit')), 8), CA('days_left', 'Days left', 'int', G('stock_id', LKN('stock.days', 'stock.stock_id', 'stock_id')), 8),
    CA('status', 'Status', 'text', G('stock_id', FZ('status')), 10), CA('eat_by', 'Eat by', 'date', G('stock_id', LKD('stock.use_by', 'stock.stock_id', 'stock_id')), 11),
    CA('check_day', 'Check day', 'date', G('stock_id', '{today}+1'), 11), CA('leave_date', 'Leaving on', 'date', G('stock_id', '{set:trip_start}'), 11), CA('back_date', 'Back on', 'date', G('stock_id', '{set:trip_end}'), 11),
    CA('n_items', 'Fridge items', 'int', G('stock_id', 'COUNTIFS(%s,%s)' % (STK('place'), FRIDGE)), 8)] + CT('stock_id', 'c2', 'nb', 'a1'),
    D.ranks_d(D.N_FRIDGE), 50, [A('status', '= ' + PAST, 'bad'), A('status', '= ' + SOON, 'warn'), A('status', '= ' + OK, 'good')]))
# 15 below minimum --------------------------------------------------------------------------------------
def BM(c): return LKN('items.' + c, 'items.item_id', 'item_id')
tables.append(T('below_min', 'Below Minimum', 'Items at or below their minimum, packs to buy',
    'Lists the items at or below the minimum stock typed in the Item Catalog, with the gap, packs to buy rounded up, section and shop; type 1 to 30 once.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('item_id', 'Item ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:rank},%s,0)),"")' % (ITM('item_id'), ITM('rank')), 9),
    CA('item', 'Item', 'text', G('item_id', LKS('items.item', 'items.item_id', 'item_id')), 24), CA('quantity', 'In stock', 'num', G('item_id', BM('stock_qty')), 9),
    CA('minimum', 'Minimum', 'num', G('item_id', BM('min_stock')), 9), CA('gap', 'Gap', 'num', G('item_id', BM('gap')), 8), CA('packs', 'Packs to buy', 'int', G('item_id', BM('packs')), 8),
    CA('section', 'Section', 'text', G('item_id', LKS('items.section', 'items.item_id', 'item_id')), 16), CA('shop', 'Shop', 'text', G('item_id', LKS('items.shop', 'items.item_id', 'item_id')), 13),
    CA('shop_date', 'Next shop', 'date', G('item_id', '{set:next_shop}'), 11), CA('back_date', 'Back on', 'date', G('item_id', '{set:trip_end}'), 11),
    CA('n_below', 'Items at or below', 'int', G('item_id', 'COUNTIFS(%s,1)' % ITM('below')), 8)] + CT('item_id', 'a1', 'a2', 'gp'),
    D.ranks_d(D.N_BELOW), 50))
# 16 storage by section ---------------------------------------------------------------------------------
tables.append(T('storage', 'Storage by Section', 'Items by shop section and how many need attention',
    'One row per shop section: items in stock and how many are past the date or use soon.', [
    LST('section', 'Section', 'section', 18, required=True),
    CA('items', 'Items', 'int', G('section', 'COUNTIFS(%s,{col:section})' % STK('section')), 9),
    CA('flagged', 'Past date or use soon', 'int', G('section', 'COUNTIFS(%s,{col:section},%s,%s)+COUNTIFS(%s,{col:section},%s,%s)' % (STK('section'), STK('status'), PAST, STK('section'), STK('status'), SOON)), 12)],
    D.storage_d(), 50, [A('flagged', '> 0', 'warn')]))
# 17 leftover eat-by board -------------------------------------------------------------------------------
def LB(c): return LKS('leftovers.' + c, 'leftovers.leftover_id', 'leftover_id')
tables.append(T('leftover_board', 'Leftover Eat-By Board', 'Dishes with portions left first, then the latest finished',
    'Lists leftover dishes with portions left by eat-by date, then the latest dishes already finished; type 1 to 25 once.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('leftover_id', 'Leftover ID', 'text', 'IFERROR(INDEX(%s,MATCH({col:rank},%s,0)),"")' % (LEF('leftover_id'), LEF('board_rank')), 10),
    CA('dish', 'Dish', 'text', G('leftover_id', LB('dish')), 24), CA('portions_left', 'Portions left', 'int', G('leftover_id', LKN('leftovers.portions_left', 'leftovers.leftover_id', 'leftover_id')), 9),
    CA('eat_by', 'Eat by', 'date', G('leftover_id', LKD('leftovers.eat_by', 'leftovers.leftover_id', 'leftover_id')), 11),
    CA('days_left', 'Days left', 'int', G('leftover_id', LKN('leftovers.days_left', 'leftovers.leftover_id', 'leftover_id')), 8),
    CA('status', 'Status', 'text', G('leftover_id', LB('status')), 10),
    CA('in_plan', 'Next 7 days plan', 'text', G('leftover_id', 'IF(%s=1,%s,%s)' % (LKN('leftovers.in_plan', 'leftovers.leftover_id', 'leftover_id'), IN_PLAN, NOT_PLAN)), 14)],
    D.ranks_d(25), 50, [A('status', '= ' + PAST, 'bad'), A('status', '= ' + SOON, 'warn')]))
# 18 shelf life check -----------------------------------------------------------------------------------
def SH(c): return LKN('items.' + c, 'items.item_id', 'item_id')
tables.append(T('shelf_check', 'Shelf Life Check', 'Typed days from added to use-by against typical shelf days',
    'One row per catalog item: the typical shelf days you typed (typical, check the label), the average days between added and use-by in Stock and whether they are close.', [
    REF('item_id', 'Item ID', 'items.item_id', 9, required=True),
    CA('item', 'Item', 'text', G('item_id', LKS('items.item', 'items.item_id', 'item_id')), 24), CA('shelf_days', 'Typical shelf days', 'int', G('item_id', SH('shelf_days')), 9),
    CA('typed_days', 'Typed days in Stock', 'int', G('item_id', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,{col:item}),0),"")' % (STK('stored'), STK('item'))), 9),
    CA('difference', 'Typed less typical, days', 'int', G('item_id', 'IF(OR({col:typed_days}="",{col:shelf_days}=0),"",{col:typed_days}-{col:shelf_days})'), 10),
    CA('flag', 'Check', 'text', G('item_id', 'IF(OR({col:typed_days}="",{col:shelf_days}=0),%s,IF(ABS({col:typed_days}/{col:shelf_days}-1)<={set:shelf_tolerance},%s,IF({col:typed_days}<{col:shelf_days},%s,%s)))' % (tok('sflag', 'No date typed'), tok('sflag', 'Close to typical'), tok('sflag', 'Typed earlier than typical'), tok('sflag', 'Typed later than typical'))), 22)],
    D.shelf_d(), 120, [A('flag', '= ' + tok('sflag', 'Typed earlier than typical'), 'warn')]))
# 19 food flow by month ---------------------------------------------------------------------------------
def MW(col, rng): return '%s,">="&{col:month},%s,"<"&EDATE({col:month},1)' % (rng, rng)
tables.append(T('flow', 'Food Flow by Month', 'Grocery lines, leftover dishes and past-date items by month',
    'One row per month: type the grocery lines bought and the items past the typed date; leftover dishes, portions made and left and dishes frozen fill in from Leftovers.', [
    C('month', 'Month', 'date', 11, required=True), C('grocery_lines', 'Grocery lines bought', 'int', 10), C('past_date', 'Items past the typed date', 'int', 10),
    CA('offset', 'Offset', 'int', G('month', '(YEAR({col:month})-YEAR({today}))*12+MONTH({col:month})-MONTH({today})'), 7),
    CA('dishes', 'Leftover dishes cooked', 'int', G('month', 'COUNTIFS(%s)' % MW('month', LEF('date'))), 9),
    CA('portions_made', 'Portions made', 'int', G('month', 'SUMIFS(%s,%s)' % (LEF('portions_made'), MW('month', LEF('date')))), 9),
    CA('portions_left', 'Portions left', 'int', G('month', 'SUMIFS(%s,%s)' % (LEF('portions_left'), MW('month', LEF('date')))), 9),
    CA('frozen', 'Dishes frozen', 'int', G('month', 'COUNTIFS(%s,%s,">0")' % (MW('month', LEF('date')), LEF('to_freezer'))), 9),
    CA('not_frozen', 'Dishes not frozen', 'int', G('month', '{col:dishes}-{col:frozen}'), 9),
    CA('stock_added', 'Stock rows added', 'int', G('month', 'COUNTIFS(%s)' % MW('month', STK('added'))), 9),
    ] + CT('month', 'a2'),
    D.flow_d(), 50))
# 20 use-by calendar ------------------------------------------------------------------------------------
tables.append(T('calendar', 'Use-By Calendar', 'Items and leftover portions reaching their date, 8 weeks',
    'One row per day from today: items passing the use-by date, fridge items, leftover portions reaching eat-by, the planned dinner and a flag; type 0 to 55 once.', [
    C('day_no', 'Day number', 'int', 8, required=True), LST('week', 'Week', 'wk', 9),
    CA('date', 'Date', 'date', G('day_no', '{today}+{col:day_no}'), 11),
    CA('items_due', 'Items reaching the use-by date', 'int', G('day_no', 'COUNTIFS(%s,{col:date})' % STK('use_by')), 9),
    CA('fridge_due', 'Fridge items reaching it', 'int', G('day_no', 'COUNTIFS(%s,{col:date},%s,%s)' % (STK('use_by'), STK('place'), FRIDGE)), 9),
    CA('leftover_due', 'Leftover portions reaching eat-by', 'int', G('day_no', 'SUMIFS(%s,%s,{col:date})' % (LEF('portions_left'), LEF('eat_by'))), 9),
    CA('dinner', 'Planned dinner', 'text', G('day_no', 'IFERROR(INDEX(%s,MATCH({col:date},%s,0)),"")' % (MEAL('recipe'), MEAL('dinner_date'))), 26),
    CA('soon_in_plan', 'Use-soon items in that dinner', 'int', G('day_no', 'IFERROR(INDEX(%s,MATCH({col:date},%s,0)),0)' % (MEAL('soon_items'), MEAL('dinner_date'))), 9),
    CA('flag', 'Flag', 'text', G('day_no', 'IF({col:items_due}=0,%s,IF({col:soon_in_plan}>0,%s,%s))' % (W('nothing_due'), IN_PLAN, NOT_PLAN)), 14),
    CA('due14', 'Items in the next 14 days', 'int', G('day_no', 'IF({col:day_no}<14,{col:items_due},"")'), 9)],
    D.calendar_d(), 56, [A('items_due', '>= 3', 'warn')]))
assert len(tables) == 20, len(tables)
