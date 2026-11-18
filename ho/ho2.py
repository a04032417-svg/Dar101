"""Home Management suite - part 2: Pantry, Freezer and Leftovers."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho2_lists import *
from ho2_tables import settings, tables, R, STK, ING, MEAL, LEF, REC, ITM, MS, DT, WK0
from ho2_tools import tools
import ho2_data as D

NOTE = "Sample wording: adapt it to your own household."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
FRZ_NOW = 'SUMIFS(%s,%s,%s)' % (STK('quantity'), STK('place'), FREEZER)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('stock_sheet', 'Stock Item Sheet', 'One stock row with its dates and checks', 'stock.stock_id', F(
        ('Item', 'stock.item'), ('Place', 'stock.place'), ('Quantity', 'stock.quantity'), ('Unit', 'stock.unit'), ('Added', 'stock.added'), ('Use by', 'stock.use_by'), ('Minimum', 'stock.min_qty'),
        ('Section', 'stock.section'), ('Shop', 'stock.shop'), ('Days to use-by', 'stock.days'), ('Status', 'stock.status'), ('Days from added to use-by', 'stock.stored')) + [
        FF('Items in the same place', 'COUNTIFS(%s,%s)' % (STK('place'), LK('stock', 'stock_id', 'place')), 'int'),
        FF('Share of all stock in that place', 'IFERROR(COUNTIFS(%s,%s)/COUNTIFS(%s,"<>"),0)' % (STK('place'), LK('stock', 'stock_id', 'place'), STK('stock_id')), 'pct'),
        FF('Items in the same section', 'COUNTIFS(%s,%s)' % (STK('section'), LK('stock', 'stock_id', 'section')), 'int')]),
    FORM('stock_take_sheet', 'Stock Take Sheet', 'One item counted against the record', 'stock.stock_id', F(
        ('Item', 'stock.item'), ('Place', 'stock.place'), ('Recorded quantity', 'stock.quantity'), ('Unit', 'stock.unit'), ('Counted', 'stock.counted'), ('Counted less recorded', 'stock.diff'), ('To adjust, 1 or 0', 'stock.adjust')) + [
        FF('Quantity to write in Stock', 'IF(%s="",%s,%s)' % (LK('stock', 'stock_id', 'counted'), LK('stock', 'stock_id', 'quantity'), LK('stock', 'stock_id', 'counted')), 'num'),
        FF('Items counted in all', 'COUNT(%s)' % STK('counted'), 'int'), FF('Items to adjust in all', 'COUNTIFS(%s,1)' % STK('adjust'), 'int'),
        FF('Share of items counted', 'IFERROR(COUNT(%s)/COUNTIFS(%s,"<>"),0)' % (STK('counted'), STK('stock_id')), 'pct')]),
    FORM('use_by_sheet', 'Use-By Check Sheet', 'One stock row checked against its typed date', 'stock_board.stock_id', F(
        ('Item', 'stock_board.item'), ('Place', 'stock_board.place'), ('Days to use-by', 'stock_board.days'), ('Status', 'stock_board.status'), ('At or below minimum, 1 or 0', 'stock_board.below'),
        ('Next 7 days plan', 'stock_board.in_plan'), ('Rank to use first', 'stock_board.rank_use'), ('Action', 'stock_board.action')) + [
        FF('Items past the date in this place', 'COUNTIFS(%s,%s,%s,%s)' % (STK('place'), LK('stock_board', 'stock_id', 'place'), STK('status'), PAST), 'int'),
        FF('Items use soon in this place', 'COUNTIFS(%s,%s,%s,%s)' % (STK('place'), LK('stock_board', 'stock_id', 'place'), STK('status'), SOON), 'int'), FF('Checked on', '{today}', 'date')]),
    FORM('leftover_card_sheet', 'Leftover Card', 'One cooked dish with portions and eat-by date', 'leftovers.leftover_id', F(
        ('Dish', 'leftovers.dish'), ('Cooked on', 'leftovers.date'), ('Portions made', 'leftovers.portions_made'), ('Portions left', 'leftovers.portions_left'), ('To freezer on', 'leftovers.to_freezer'),
        ('Eat by', 'leftovers.eat_by'), ('Days to eat-by', 'leftovers.days_left'), ('Status', 'leftovers.status'), ('Category', 'leftovers.category')) + [
        FF('Portions eaten', '%s-%s' % (LK('leftovers', 'leftover_id', 'portions_made'), LK('leftovers', 'leftover_id', 'portions_left')), 'int'),
        FF('Share eaten', 'IFERROR((%s-%s)/%s,0)' % (LK('leftovers', 'leftover_id', 'portions_made'), LK('leftovers', 'leftover_id', 'portions_left'), LK('leftovers', 'leftover_id', 'portions_made')), 'pct'),
        FF('Typical fridge days, from Settings', '{set:leftover_days}', 'int'), FF('Eat-by if kept in the fridge', '%s+{set:leftover_days}' % LK('leftovers', 'leftover_id', 'date'), 'date'),
        FF('Times cooked for leftovers', 'COUNTIFS(%s,%s)' % (LEF('recipe_id'), LK('leftovers', 'leftover_id', 'recipe_id')), 'int')]),
    FORM('freezer_entry_sheet', 'Freezer Entry Sheet', 'One freezer row against the typed freezer months', 'stock.stock_id', F(
        ('Item', 'stock.item'), ('Quantity', 'stock.quantity'), ('Unit', 'stock.unit'), ('Added', 'stock.added'), ('Use by', 'stock.use_by'), ('Months in the freezer', 'stock.frz_m'),
        ('Within the typed months, 1 or 0', 'stock.frz_ok'), ('Freezer rank, oldest first', 'stock.frz_rank')) + [
        FF('Typed freezer months, from Settings', '{set:freezer_months}', 'int'), FF('Months left of the typed months', '{set:freezer_months}-%s' % LK('stock', 'stock_id', 'frz_m'), 'num'),
        FF('Units in the freezer', FRZ_NOW, 'num'), FF('Freezer full', 'IFERROR(%s/{set:freezer_capacity},0)' % FRZ_NOW, 'pct')]),
    FORM('batch_cook_sheet', 'Batch Cook Log Sheet', 'One recipe checked for a batch', 'recipes.recipe_id', F(
        ('Recipe', 'recipes.recipe'), ('Category', 'recipes.category'), ('Prep minutes', 'recipes.prep_min'), ('Servings', 'recipes.servings'), ('Ingredients typed', 'recipes.ing_n'),
        ('Ingredients on hand', 'recipes.on_n'), ('Ingredients missing', 'recipes.miss_n'), ('Share on hand', 'recipes.share'), ('First missing ingredient', 'recipes.missing_first')) + [
        FF('Portions of a double batch', '2*%s' % LK('recipes', 'recipe_id', 'servings'), 'int'), FF('Room left in the freezer', '{set:freezer_capacity}-%s' % FRZ_NOW, 'num'),
        FF('Room after freezing half a double batch', '{set:freezer_capacity}-%s-%s' % (FRZ_NOW, LK('recipes', 'recipe_id', 'servings')), 'num')]),
    FORM('catalog_sheet', 'Item Catalog Sheet', 'One catalog item with pack size and shop', 'items.item_id', F(
        ('Item', 'items.item'), ('Section', 'items.section'), ('Unit', 'items.unit'), ('Place', 'items.place'), ('Per serving', 'items.per_serving'), ('Pack size', 'items.pack_size'),
        ('Typical shelf days', 'items.shelf_days'), ('Minimum stock', 'items.min_stock'), ('Pack price', 'items.pack_price'), ('Shop', 'items.shop'), ('Stock now', 'items.stock_qty'),
        ('Last bought', 'items.last_bought'), ('Servings in stock', 'items.servings')) + [
        FF('Packs in stock', 'IFERROR(%s/%s,0)' % (LK('items', 'item_id', 'stock_qty'), LK('items', 'item_id', 'pack_size')), 'num')]),
    FORM('minimum_sheet', 'Minimum Stock Sheet', 'One item against its minimum', 'items.item_id', F(
        ('Item', 'items.item'), ('Minimum stock', 'items.min_stock'), ('Stock now', 'items.stock_qty'), ('At or below the minimum, 1 or 0', 'items.below'), ('Short of the minimum', 'items.gap'),
        ('Packs to buy', 'items.packs'), ('Cost line of the packs', 'items.pack_cost'), ('Shop', 'items.shop'), ('Days since bought', 'items.days_since')) + [
        FF('Packs for twice the minimum', 'IF(%s>0,MAX(1,ROUNDUP(ROUND((2*%s-%s)/%s,6),0)),0)' % (LK('items', 'item_id', 'min_stock'), LK('items', 'item_id', 'min_stock'), LK('items', 'item_id', 'stock_qty'), LK('items', 'item_id', 'pack_size')), 'int'),
        FF('Items at or below the minimum in all', 'COUNTIFS(%s,1)' % ITM('below'), 'int')]),
    FORM('pantry_week_sheet', 'Pantry Week Check Sheet', 'One day of the use-by calendar', 'calendar.day_no', F(
        ('Date', 'calendar.date'), ('Items reaching the use-by date', 'calendar.items_due'), ('Fridge items reaching it', 'calendar.fridge_due'), ('Leftover portions reaching eat-by', 'calendar.leftover_due'),
        ('Planned dinner', 'calendar.dinner'), ('Use-soon items in that dinner', 'calendar.soon_in_plan'), ('Flag', 'calendar.flag')) + [
        FF('Items reaching the date, 7 days on', 'SUMIFS(%s,%s,">="&{pick},%s,"<"&({pick}+7))' % (R('calendar', 'items_due'), R('calendar', 'day_no'), R('calendar', 'day_no')), 'int'),
        FF('Fridge items in those 7 days', 'SUMIFS(%s,%s,">="&{pick},%s,"<"&({pick}+7))' % (R('calendar', 'fridge_due'), R('calendar', 'day_no'), R('calendar', 'day_no')), 'int')]),
    FORM('recipe_match_sheet', 'Recipe Match Sheet', 'One recipe against what is in stock', 'recipe_ready.recipe_id', F(
        ('Recipe', 'recipe_ready.recipe'), ('Ingredients', 'recipe_ready.ingredients'), ('On hand', 'recipe_ready.on_hand'), ('Share on hand', 'recipe_ready.share'), ('Expiring items used', 'recipe_ready.expiring'),
        ('Score', 'recipe_ready.score'), ('Rank', 'recipe_ready.rank'), ('Missing', 'recipe_ready.missing'), ('Status', 'recipe_ready.status')) + [
        FF('Recipes with a higher score', '%s-1' % LK('recipe_ready', 'recipe_id', 'rank'), 'int'),
        FF('Prep minutes', 'INDEX(%s,MATCH({pick},%s,0))' % (REC('prep_min'), REC('recipe_id')), 'int'),
        FF('First missing ingredient', 'INDEX(%s,MATCH({pick},%s,0))' % (REC('missing_first'), REC('recipe_id')), 'text')]),
    FORM('moving_stock_sheet', 'Moving Stock Sheet', 'One item before a trip or a move', 'stock.stock_id', F(
        ('Item', 'stock.item'), ('Place', 'stock.place'), ('Quantity', 'stock.quantity'), ('Unit', 'stock.unit'), ('Section', 'stock.section'), ('Shop', 'stock.shop'), ('Use by', 'stock.use_by')) + [
        FF('Leaving on, from Settings', '{set:trip_start}', 'date'), FF('Back on, from Settings', '{set:trip_end}', 'date'),
        FF('Passes the date before you are back', 'IF(AND(%s>0,%s<={set:trip_end}),1,0)' % (LK('stock', 'stock_id', 'use_by'), LK('stock', 'stock_id', 'use_by')), 'int'),
        FF('Items in the same place', 'COUNTIFS(%s,%s)' % (STK('place'), LK('stock', 'stock_id', 'place')), 'int')]),
    FORM('fridge_clearout_sheet', 'Fridge Clear-Out Sheet', 'One fridge row in the clear-out order', 'fridge.stock_id', F(
        ('Item or dish', 'fridge.item'), ('Quantity', 'fridge.quantity'), ('Unit', 'fridge.unit'), ('Days left', 'fridge.days_left'), ('Status', 'fridge.status'), ('Eat by', 'fridge.eat_by'),
        ('Fridge items in all', 'fridge.n_items')) + [
        FF('Fridge items past the date', 'COUNTIFS(%s,%s,%s,%s)' % (STK('place'), FRIDGE, STK('status'), PAST), 'int'),
        FF('Fridge items use soon', 'COUNTIFS(%s,%s,%s,%s)' % (STK('place'), FRIDGE, STK('status'), SOON), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
SG = ['Adult 1', 'Adult 2']
documents = [
    DOC('use_first_doc', 'Use First Page', 'Use-first page for the fridge', 'use_first.rank', [
        'Use-first page of {set:household}, dated {today}. Rank {col:use_first.rank}: {col:use_first.item}, in the {col:use_first.place}.',
        'Use-by date typed from the label: {col:use_first.use_by}, {col:use_first.days_left} days left. Next 7 days plan: {col:use_first.in_plan}. Suggested recipe: {col:use_first.recipe}.',
        'Plan it for {col:use_first.plan_for}. The ranking comes from the dates you typed; check the label for every item and your local rules.',
        'Pin this page to the fridge for the week of {col:use_first.week_of}.'], SG, NOTE),
    DOC('freezer_doc', 'Freezer Inventory Page', 'Freezer inventory page by shelf or basket', 'freezer.rank', [
        'Freezer inventory page of {set:household}, dated {today}. Rank {col:freezer.rank}, oldest first: {col:freezer.item}.',
        'Quantity: {col:freezer.quantity} {col:freezer.unit}. Months in the freezer: {col:freezer.months}. Use-by date typed from the label: {col:freezer.use_by}. Status: {col:freezer.status}.',
        'Units in the freezer: {col:freezer.portions_total}, about {col:freezer.full_pct} percent of the space you typed. Write the shelf or basket here: ________.',
        'Typical freezer times are set in Settings, typical, check the label.'], SG, NOTE),
    DOC('shelf_list_doc', 'Pantry Shelf List', 'Pantry stock list by shelf and section', 'storage.section', [
        'Stock list of {set:household} for the section {col:storage.section}, dated {today}. Items in stock: {col:storage.items}. Past the date or use soon: {col:storage.flagged}.',
        'Write the items by shelf below, with the quantity and the use-by date typed from the label.',
        'Shelf 1: ______________________   Shelf 2: ______________________   Shelf 3: ______________________',
        'Shelf 4: ______________________   Basket or drawer: ______________________'], SG, NOTE),
    DOC('leftover_board_doc', 'Leftovers Board Page', 'Leftovers board: dish, portions, eat by', 'leftover_board.rank', [
        'Leftovers board of {set:household}, dated {today}. Place {col:leftover_board.rank}: {col:leftover_board.dish}.',
        'Portions left: {col:leftover_board.portions_left}. Eat by: {col:leftover_board.eat_by}, {col:leftover_board.days_left} days left. Status: {col:leftover_board.status}. Next 7 days plan: {col:leftover_board.in_plan}.',
        'The eat-by date is the date you typed from the label; check the label and your local rules.',
        'Cooked leftovers in the fridge: typical days are set in Settings.'], SG, NOTE),
    DOC('below_min_doc', 'Below Minimum Shopping Page', 'Below-minimum shopping page', 'below_min.rank', [
        'Shopping page of {set:household} for the shop on {col:below_min.shop_date}, dated {today}. Rank {col:below_min.rank}: {col:below_min.item}.',
        'In stock: {col:below_min.quantity}. Minimum: {col:below_min.minimum}. Short of the minimum: {col:below_min.gap}. Packs to buy: {col:below_min.packs}. Section: {col:below_min.section}. Shop: {col:below_min.shop}.',
        'Items at or below the minimum in all: {col:below_min.n_below}. Packs are rounded up to the pack size typed in the Item Catalog.',
        'Tick each item when it is in the bag: [ ]'], SG, NOTE),
    DOC('cook_first_doc', 'Cook This First Card', 'Cook-this-first card for the week', 'cook_first.rank', [
        'Cook-this-first card of {set:household}, dated {today}. Rank {col:cook_first.rank}: {col:cook_first.recipe}. Verdict: {col:cook_first.verdict}.',
        'Ingredients on hand: {col:cook_first.on_hand} of {col:cook_first.ingredients}, {col:cook_first.share_whole} percent. Missing: {col:cook_first.missing}. Expiring items it uses: {col:cook_first.expiring}. Prep minutes: {col:cook_first.prep_min}.',
        'The score is calculated from your stock entries: the share on hand plus 15 points for each expiring item the recipe uses.',
        'Dinner planned for: ________'], SG, NOTE),
    DOC('stock_take_doc', 'Stock Take Page', 'Stock take sheet for one item', 'stock.stock_id', [
        'Stock take page of {set:household}, dated {today}. Stock row {col:stock.stock_id}: {col:stock.item}, in the {col:stock.place}.',
        'Recorded quantity: {col:stock.quantity} {col:stock.unit}. Counted: {col:stock.counted}. Counted less recorded: {col:stock.diff}. Use by: {col:stock.use_by}.',
        'Type the counted quantity in the Counted column of Stock; the difference fills in. Items to adjust in all: {col:stock.adjust_n}.',
        'Counted by: ________   Checked by: ________'], SG, NOTE),
    DOC('trip_fridge_doc', 'Pre-Trip Fridge Plan', 'Pre-trip fridge plan', 'fridge.rank', [
        'Pre-trip fridge plan of {set:household}, dated {today}. We leave on {col:fridge.leave_date} and are back on {col:fridge.back_date}.',
        'Fridge order {col:fridge.rank}: {col:fridge.item}, {col:fridge.quantity} {col:fridge.unit}. Days left: {col:fridge.days_left}. Eat by: {col:fridge.eat_by}. Status: {col:fridge.status}.',
        'Fridge items in all: {col:fridge.n_items}. Use, give away or ask a neighbour before the date; check the label for every item.',
        'Neighbour or house-sitter told on: ________'], SG, NOTE),
    DOC('batch_plan_doc', 'Batch Cooking Plan', 'Batch cooking plan for one recipe', 'recipes.recipe_id', [
        'Batch cooking plan of {set:household}, dated {today}. Recipe {col:recipes.recipe_id}: {col:recipes.recipe}, category {col:recipes.category}.',
        'Servings: {col:recipes.servings}. Prep minutes: {col:recipes.prep_min}. Ingredients on hand: {col:recipes.on_n} of {col:recipes.ing_n}. First missing ingredient: {col:recipes.missing_first}.',
        'Portions to freeze: ________   Date to freeze: ________   Eat-by date typed from the label: ________',
        'Label each box with the dish and the date.'], SG, NOTE),
    DOC('sitter_list_doc', 'Sitter Use-By List', 'Use-by list for a sitter or house-sitter', 'use_first.rank', [
        'Use-by list of {set:household} for the sitter, dated {today}. Please eat or use first: {col:use_first.item}.',
        'Where it is: {col:use_first.place}. Use-by date typed from the label: {col:use_first.use_by}. Days left: {col:use_first.days_left}.',
        'Please check the label on everything before you use it, and ask us if you are unsure. Our numbers are on the emergency page of this household.',
        'Thank you, {set:household}.'], ['Household', 'Sitter'], NOTE),
    DOC('monthly_review_doc', 'Monthly Pantry Review', 'Monthly pantry review', 'flow.month', [
        'Monthly pantry review of {set:household} for the month starting {col:flow.month}.',
        'Grocery lines bought: {col:flow.grocery_lines}. Items past the typed date: {col:flow.past_date}. Leftover dishes cooked: {col:flow.dishes}, portions made {col:flow.portions_made}, portions left {col:flow.portions_left}.',
        'Dishes frozen: {col:flow.frozen}. Dishes not frozen: {col:flow.not_frozen}. Stock rows added: {col:flow.stock_added}.',
        'Compare with your own earlier months. One thing to change next month: ________'], SG, NOTE),
    DOC('catalog_page_doc', 'Item Catalog Page', 'Item catalog page with pack size and shop', 'items.item_id', [
        'Item page of {set:household}, dated {today}. Item {col:items.item_id}: {col:items.item}, section {col:items.section}, kept in the {col:items.place}.',
        'Pack size: {col:items.pack_size} {col:items.unit}. Pack price: {col:items.pack_price}. Shop: {col:items.shop}. Typical shelf days: {col:items.shelf_days}, typical, check the label.',
        'Minimum stock: {col:items.min_stock}. Stock now: {col:items.stock_qty}. Packs to buy: {col:items.packs}. Last bought: {col:items.last_bought}.',
        'Servings in stock: {col:items.servings}.'], SG, NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('weekly_glance', 'Weekly Pantry Glance Steps', 'meal_plan', 'meal_plan.date', [('Open the Use First Ranking', 0), ('Check the items that are past the date', 0), ('Plan a dinner for the first item', 1), ('Read Cook This First', 1), ('Add the Below Minimum items to the list', 2), ('Glance at the freezer inventory', 3)]),
    CHK('fridge_clearout', 'Fridge Clear-Out Steps', 'stock', 'stock.use_by', [('Take out everything past its date', -2), ('Check the label of each item', -2), ('Wipe the shelf', -1), ('Move the oldest items to the front', -1), ('Type what you threw away', 0), ('Write the shopping list', 0)]),
    CHK('freezer_check', 'Freezer Check Steps', 'flow', 'flow.month', [('List what is in the chest freezer', 0), ('Check the months against Settings', 0), ('Move the oldest portions to the top', 1), ('Plan a dinner from the oldest dish', 2), ('Type the clear-out on Stock', 3), ('Write the space left', 3)]),
    CHK('stock_take', 'Stock Take Steps', 'flow', 'flow.month', [('Print the Stock Take Page', 0), ('Count the pantry shelves', 1), ('Count the fridge', 1), ('Count the chest freezer', 2), ('Type the Counted column on Stock', 3), ('Adjust the quantities that differ', 4)]),
    CHK('after_shop', 'After a Big Shop Steps', 'bought', 'bought.date', [('Check the bags against the list', 0), ('Write the use-by date on new items', 0), ('Move older items to the front', 0), ('Put new items in Stock', 1), ('Tick the lines on Bought Lines', 1), ('Clear the list for the next shop', 2)]),
    CHK('batch_cooking', 'Batch Cooking Steps', 'leftovers', 'leftovers.date', [('Choose the recipe and check the stock', -1), ('Cook the batch', 0), ('Cool and box the portions', 0), ('Label with the dish and the date', 0), ('Move the freezer portions to the freezer', 1), ('Type the dish on Leftovers', 1)]),
    CHK('leftover_night', 'Leftover Night Steps', 'leftovers', 'leftovers.eat_by', [('Read the Leftover Eat-By Board', -4), ('Choose the dish with the nearest date', -3), ('Plan the leftover meal', -2), ('Check the label before you serve', -1), ('Update the portions left', 0)]),
    CHK('before_trip', 'Before a Trip Away Steps', 'meal_plan', 'meal_plan.date', [('Run Before a Trip Away', -7), ('Plan dinners that use the fridge items', -6), ('Tell the neighbour what to take', -3), ('Clear the fridge of items that pass the date', -1), ('Take out the rubbish', -1), ('Check the freezer door', 0)]),
    CHK('after_trip', 'Return From a Trip Steps', 'meal_plan', 'meal_plan.date', [('Check the fridge and the freezer', 0), ('Clear anything past its date', 0), ('Write the first shop list', 0), ('Buy fresh basics', 1), ('Type the stock on Stock', 2), ('Plan the first dinners', 2)]),
    CHK('past_date_clear', 'Past-Date Clear-Out Steps', 'stock', 'stock.use_by', [('Open Past-Date Review', 1), ('Check the label of each item', 1), ('Clear the items you decide to clear', 1), ('Type the clear-out on Stock', 2), ('Add the count on Food Flow by Month', 3)]),
    CHK('spring_reset', 'Spring Pantry Reset Steps', 'flow', 'flow.month', [('Take everything off the shelves', 0), ('Wipe the shelves', 0), ('Check every date', 1), ('Group by section', 1), ('Update the minimum stock', 2), ('Print the shelf lists', 3)]),
    CHK('single_start', 'Single Adult First Pantry Steps', 'team', 'team.start', [('Replace the demo stock with your own', 0), ('Leave the child and pet rows empty', 0), ('Type the use-by date of each item', 1), ('Set the minimum stock of what you use', 2), ('Type three recipes you cook', 3), ('Read Use First after one week', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('use_soon_a1', 'Adult 1: item is use soon', 'use_first', 'use_first.a1_phone', 'Hi {a1_name}, {item} in the {place} is use soon, use-by {use_by}. Shall we plan it for {plan_for}? {household}'),
    M('portions_a2', 'Adult 2: use the dish portions', 'leftovers', 'leftovers.a2_phone', 'Hi {a2_name}, please use the {dish} portions by {eat_by}, {portions_left} are left. {household}'),
    M('best_fit_a1', 'Adult 1: best fit from stock tonight', 'cook_first', 'cook_first.a1_phone', 'Hi {a1_name}, the best fit from stock tonight is {recipe}: {share_whole} percent of the ingredients are on hand. {household}'),
    M('past_a2', 'Adult 2: items past the typed date', 'stock_board', 'stock_board.a2_phone', 'Hi {a2_name}, {past_total} items are past the typed date. Please check them against the label before you cook. {household}'),
    M('freezer_a1', 'Adult 1: freezer dish for the late days', 'freezer', 'freezer.a1_phone', 'Hi {a1_name}, the freezer holds {quantity} {unit} of {item} for the late days. {household}'),
    M('below_a2', 'Adult 2: below the minimum', 'below_min', 'below_min.a2_phone', 'Hi {a2_name}, we are at or below the minimum for {item}, {quantity} left. It goes on the list for {shop_date}. {household}'),
    M('moved_a1', 'Adult 1: dish moved to the freezer', 'leftovers', 'leftovers.a1_phone', 'Hi {a1_name}, I moved {dish} to the freezer on {to_freezer}, eat by {eat_by}. {household}'),
    M('full_a2', 'Adult 2: freezer is filling up', 'freezer', 'freezer.a2_phone', 'Hi {a2_name}, the chest freezer is about {full_pct} percent full on {check_date}. Please use the oldest portions first. {household}'),
    M('school_c1', 'Child 1: take an item to school', 'use_first', 'use_first.c1_phone', 'Hi {c1_name}, please take {item} to school on {plan_for}, it needs using by {use_by}. {household}'),
    M('lunch_c1', 'Child 1: leftovers are your lunch', 'leftovers', 'leftovers.c1_phone', 'Hi {c1_name}, the leftovers of {dish} are your lunch on {tomorrow}. {household}'),
    M('check_c2', 'Child 2: help check the dates', 'fridge', 'fridge.c2_phone', 'Hi {c2_name}, please help check the dates on the fridge shelf on {check_day}. {household}'),
    M('eat_c2', 'Child 2: we eat it today', 'use_first', 'use_first.c2_phone', 'Hi {c2_name}, we eat the {item} today, it is use soon. {household}'),
    M('gp_dish', 'Grandparent: portions in the fridge', 'leftovers', 'leftovers.gp_phone', 'Hello {gp_name}, there are {portions_left} portions of {dish} in the fridge for you on {tomorrow}. {household}'),
    M('gp_bring', 'Grandparent: bring a pack', 'below_min', 'below_min.gp_phone', 'Hello {gp_name}, could you bring a pack of {item}? We are at or below the minimum. Thank you, {household}'),
    M('gp_take', 'Grandparent: take the extra dish home', 'leftovers', 'leftovers.gp_phone', 'Hello {gp_name}, please take the extra {dish} home, eat by {eat_by}. {household}'),
    M('bs_dish', 'Babysitter: dish in the fridge', 'leftovers', 'leftovers.bs_phone', 'Hi {bs_name}, {dish} is in the fridge for the children on {friday}, eat by {eat_by}. {household}'),
    M('bs_first', 'Babysitter: use this item first', 'use_first', 'use_first.bs_phone', 'Hi {bs_name}, please use {item} first, it is use soon. {household}'),
    M('bs_freezer', 'Babysitter: freezer drawer dish', 'freezer', 'freezer.bs_phone', 'Hi {bs_name}, the freezer has {item}. Heat it as the label says. {household}'),
    M('cp_share', 'Carpool family: portions to share', 'leftovers', 'leftovers.cp_phone', 'Hello {cp_name}, we have {portions_left} portions of {dish} to share after the lift on {tomorrow}. {household}'),
    M('nb_offer', 'Neighbour: would you like an item', 'use_first', 'use_first.nb_phone', 'Hello {nb_name}, would you like {item}? It is use soon and we cannot finish it. {household}'),
    M('nb_away', 'Neighbour: please take an item', 'fridge', 'fridge.nb_phone', 'Hello {nb_name}, we are away from {leave_date} to {back_date}. Please take the {item} from the fridge. {household}'),
    M('nb_key', 'Neighbour: fridge items while away', 'fridge', 'fridge.nb_phone', 'Hello {nb_name}, you hold our spare key: the fridge has {n_items} items to use while we are away from {leave_date}. {household}'),
    M('school_lunch', 'School office: lunch box change', 'leftovers', 'leftovers.sc_phone', 'Hello {sc_name}, the lunch box on {tomorrow} has {dish}. Please tell us if there is a change. {household}'),
    M('check_done', 'Household member: past-date check done', 'stock_board', 'stock_board.a1_phone', 'Hi {a1_name}, the past-date check on {check_date} found {past_total} items to clear. {household}'),
    M('shop_list', 'Household member: top-up shop list', 'below_min', 'below_min.a1_phone', 'Hi {a1_name}, the pantry list for the top-up shop on {shop_date} has {n_below} items. {household}'),
    M('take_done', 'Household member: stock take result', 'stock', 'stock.a1_phone', 'Hi {a1_name}, the stock take on {check_date} found {adjust_n} items to adjust. {household}'),
    M('write_date', 'Household member: write the use-by date', 'team', 'team.phone', 'Hi {name}, please write the use-by date on new items when you put them away. Thank you, {household}'),
    M('dish_dinner', 'Household member: dinner uses an item', 'use_first', 'use_first.a2_phone', 'Hi {a2_name}, {recipe} is the dinner on {plan_for} to use up {item}. {household}'),
    M('frz_cleared', 'Household member: freezer cleared', 'freezer', 'freezer.a2_phone', 'Hi {a2_name}, the freezer was cleared on {check_date}, {portions_total} units are left. {household}'),
    M('we_leave', 'Household member: we leave on', 'fridge', 'fridge.a1_phone', 'Hi {a1_name}, we leave on {leave_date}, please eat {item} before then. {household}'),
    M('back_home', 'Household member: back from the trip', 'below_min', 'below_min.a2_phone', 'Hi {a2_name}, we are back on {back_date}. The first shop list is ready with {n_below} items. {household}'),
    M('week_list', 'Household member: use-first list is up', 'use_first', 'use_first.a1_phone', 'Hi {a1_name}, the use-first list for the week of {week_of} is on the fridge, {item} comes first. {household}'),
    M('month_review', 'Household member: monthly pantry review', 'flow', 'flow.a2_phone', 'Hi {a2_name}, the pantry review for the month starting {month}: {past_date} items were past the typed date. {household}'),
    M('batch_frozen', 'Household member: batch frozen', 'leftovers', 'leftovers.a1_phone', 'Hi {a1_name}, the batch of {dish} is in the freezer, {portions_made} portions. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def W_(c, op, v): return (c, op, v)
def CNT(extra=''): return 'COUNTIFS(%s%s)' % (STK('stock_id') + ',"<>"', extra)
def N30(rng): return '%s,">="&({today}-29),%s,"<="&{today}' % (rng, rng)
LAST90 = '%s,">="&({today}-89),%s,"<="&{today}' % (LEF('date'), LEF('date'))
kpis = [
    KPI('Items in stock', CNT(), 'int'),
    KPI('Items in the pantry', 'COUNTIFS(%s,%s)' % (STK('place'), PANTRY), 'int'),
    KPI('Items in the fridge', 'COUNTIFS(%s,%s)' % (STK('place'), FRIDGE), 'int'),
    KPI('Items in the chest freezer', 'COUNTIFS(%s,%s)' % (STK('place'), FREEZER), 'int'),
    KPI('Items use soon, within the window', 'COUNTIFS(%s,%s)' % (STK('status'), SOON), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Items past the typed date', 'COUNTIFS(%s,%s)' % (STK('status'), PAST), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Share of items ok', 'IFERROR(COUNTIFS(%s,%s)/COUNTIFS(%s,"<>"),0)' % (STK('status'), OK, STK('stock_id')), 'pct'),
    KPI('Items at or below minimum stock', 'COUNTIFS(%s,1)' % ITM('below'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Packs to buy to reach the minimum', 'SUM(%s)' % ITM('packs'), 'int'),
    KPI('Nearest use-by date from today', 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (STK('use_by'), STK('use_by')), 'date'),
    KPI('Leftover dishes in the fridge', 'COUNTIFS(%s,">0",%s,0)' % (LEF('portions_left'), LEF('frozen')), 'int'),
    KPI('Leftover portions left', 'SUM(%s)' % LEF('portions_left'), 'int'),
    KPI('Leftover dishes past eat-by', 'COUNTIFS(%s,%s)' % (LEF('status'), PAST), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Portions in the chest freezer', 'SUMIFS(%s,%s,%s,%s,%s)' % (STK('quantity'), STK('place'), FREEZER, STK('unit'), PORTION), 'int'),
    KPI('Freezer items older than typed months', 'COUNTIFS(%s,0)' % STK('frz_ok'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Average months in the freezer', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,%s),1),0)' % (STK('frz_m'), STK('place'), FREEZER), 'num'),
    KPI('Leftover dishes cooked, last 30 days', 'COUNTIFS(%s)' % N30(LEF('date')), 'int'),
    KPI('Batch dishes frozen, last 30 days', 'COUNTIFS(%s)' % N30(LEF('to_freezer')), 'int'),
    KPI('Dishes frozen, share of last 90 days', 'IFERROR(COUNTIFS(%s,%s,">0")/COUNTIFS(%s),0)' % (LAST90, LEF('to_freezer'), LAST90), 'pct'),
    KPI('Recipes cookable from stock alone', 'COUNTIFS(%s,1)' % REC('ready'), 'int'),
    KPI('Best recipe share on hand', 'SUMIFS(%s,%s,1)' % (REC('share'), REC('rank')), 'pct'),
    KPI('Recipes missing one ingredient', 'COUNTIFS(%s,1)' % REC('miss_n'), 'int'),
    KPI('Items used in the next 7 days plan', 'COUNTIFS(%s,1)' % STK('in_plan'), 'int'),
    KPI('Use-soon items not in the 7 day plan', 'COUNTIFS(%s,%s,%s,0)' % (STK('status'), SOON, STK('in_plan')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Stock added, last 30 days', 'COUNTIFS(%s)' % N30(STK('added')), 'int'),
    KPI('Items past the date, last complete month', 'SUMIFS(%s,%s,EDATE(%s,-1))' % (R('flow', 'past_date'), R('flow', 'month'), MS), 'int'),
    KPI('Grocery lines bought, last 30 days', 'COUNTIFS(%s,%s,%s)' % (R('bought', 'bought'), YES, N30(R('bought', 'date'))), 'int'),
    KPI('Grocery lines a week, last 4 full weeks', 'COUNTIFS(%s,%s,%s,">="&(%s-28),%s,"<"&%s)/4' % (R('bought', 'bought'), YES, R('bought', 'date'), WK0, R('bought', 'date'), WK0), 'num'),
    KPI('Fridge days from added to use-by', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,%s),1),0)' % (STK('stored'), STK('place'), FRIDGE), 'num'),
    KPI('Stock rows without a use-by date', 'COUNTIFS(%s,"<>",%s,"")' % (STK('stock_id'), STK('use_by')), 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Pantry and Freezer Dashboard", "kpis": kpis,
    "monthly": {"title": "Leftover dishes, frozen dishes and items past the date", "date": "flow.month", "series": [
        {"label": "Leftover dishes cooked", "sum": "flow.dishes", "date": "flow.month"}, {"label": "Dishes frozen", "sum": "flow.frozen", "date": "flow.month"},
        {"label": "Items past the typed date", "sum": "flow.past_date", "date": "flow.month"}]},
    "breakdowns": [{"title": "Items by place", "by": "stock.place", "value": "stock.quantity", "agg": "count"}, {"title": "Items by section", "by": "stock.section", "value": "stock.quantity", "agg": "count"},
                   {"title": "Packs to buy by shop", "by": "items.shop", "value": "items.packs", "agg": "sum"}, {"title": "Leftover dishes by dish kind", "by": "leftovers.category", "value": "leftovers.portions_made", "agg": "count"}]}
insights = {"filters": [{"label": "Place", "list": "place"}, {"label": "Section", "list": "section"}, {"label": "Shop", "list": "shop"}],
    "gauges": [
        {"title": "Items ok against all items", "num": AGG('count', 'stock', where=[W_('status', '=', OK)]), "den": AGG('count', 'stock')},
        {"title": "Items above their minimum", "num": AGG('count', 'stock', where=[W_('below', '=', 0)]), "den": AGG('count', 'stock')},
        {"title": "Leftover dishes eaten or within date", "num": AGG('count', 'leftovers', where=[W_('closed', '=', 1)]), "den": AGG('count', 'leftovers')},
        {"title": "Freezer items within the typed months", "num": AGG('count', 'stock', where=[W_('frz_ok', '=', 1)]), "den": AGG('count', 'stock', where=[W_('place', '=', FREEZER)])},
        {"title": "Use-soon items in the next 7 days plan", "num": AGG('count', 'stock', where=[W_('status', '=', SOON), W_('in_plan', '=', 1)]), "den": AGG('count', 'stock', where=[W_('status', '=', SOON)])},
        {"title": "Fridge items not past the date", "num": AGG('count', 'stock', where=[W_('place', '=', FRIDGE), W_('status', '<>', PAST)]), "den": AGG('count', 'stock', where=[W_('place', '=', FRIDGE)])}],
    "charts": [
        CHART('Items by place', 'bar', 'stock.place', [AGG('count', 'stock', label='Items')]),
        CHART('Items by section', 'bar', 'stock.section', [AGG('count', 'stock', label='Items')]),
        CHART('Items by place and status', 'stacked', 'stock.place', [AGG('count', 'stock', where=[W_('status', '=', OK)], label='ok'), AGG('count', 'stock', where=[W_('status', '=', SOON)], label='use soon'),
                                                                      AGG('count', 'stock', where=[W_('status', '=', PAST)], label='past date')]),
        CHART('Use-by dates by week, next 8 weeks', 'column', 'calendar.week', [AGG('sum', 'calendar', 'calendar.items_due', label='Items reaching the date')]),
        CHART('Items past the date per month', 'column', 'month', [AGG('sum', 'flow', 'flow.past_date', date='flow.month', label='Items past the date')]),
        CHART('Fridge items by section', 'bar', 'stock.section', [AGG('count', 'stock', where=[W_('place', '=', FRIDGE)], label='Fridge items')]),
        CHART('Leftover dishes per month', 'column', 'month', [AGG('sum', 'flow', 'flow.dishes', date='flow.month', label='Dishes cooked')]),
        CHART('Portions made and left per month', 'column', 'month', [AGG('sum', 'flow', 'flow.portions_made', date='flow.month', label='Portions made'), AGG('sum', 'flow', 'flow.portions_left', date='flow.month', label='Portions left')]),
        CHART('Dishes frozen and not frozen per month', 'stacked', 'month', [AGG('sum', 'flow', 'flow.frozen', date='flow.month', label='Frozen'), AGG('sum', 'flow', 'flow.not_frozen', date='flow.month', label='Not frozen')]),
        CHART('Freezer items by month added', 'column', 'month', [AGG('count', 'stock', date='stock.added', where=[W_('place', '=', FREEZER)], label='Freezer items')]),
        CHART('Freezer units by section', 'bar', 'stock.section', [AGG('sum', 'stock', 'stock.quantity', where=[W_('place', '=', FREEZER)], label='Units')]),
        CHART('Items at or below minimum by section', 'bar', 'stock.section', [AGG('count', 'stock', where=[W_('below', '=', 1)], label='At or below minimum')]),
        CHART('Packs to buy by shop', 'bar', 'items.shop', [AGG('sum', 'items', 'items.packs', label='Packs to buy')]),
        CHART('Stock added per month', 'column', 'month', [AGG('count', 'stock', date='stock.added', label='Stock rows added')]),
        CHART('Grocery lines bought per month', 'column', 'month', [AGG('sum', 'flow', 'flow.grocery_lines', date='flow.month', label='Grocery lines')]),
        CHART('Average share on hand by category', 'bar', 'recipes.category', [AGG('avg', 'recipes', 'recipes.share', label='Share on hand')]),
        CHART('Recipes cookable from stock by preference', 'bar', 'recipes.pref_label', [AGG('sum', 'recipes', 'recipes.ready', label='Recipes ready')]),
        CHART('Items in the next 7 days plan by place', 'bar', 'stock.place', [AGG('count', 'stock', where=[W_('in_plan', '=', 1)], label='Items in the plan')]),
        CHART('Use-soon items by section', 'bar', 'stock.section', [AGG('count', 'stock', where=[W_('status', '=', SOON)], label='Use soon')]),
        CHART('Leftover dishes by dish kind', 'bar', 'leftovers.category', [AGG('count', 'leftovers', label='Dishes')]),
        CHART('Stock by shop', 'bar', 'stock.shop', [AGG('count', 'stock', label='Items')]),
        CHART('Leftover portions reaching eat-by by week', 'column', 'calendar.week', [AGG('sum', 'calendar', 'calendar.leftover_due', label='Portions')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Cook this first", "why": "every recipe is scored by the share of its ingredients on hand and the expiring items it uses, ending in one recipe to cook first", "where": "Cook This First"},
    {"name": "Use first list", "why": "the stock nearest its typed use-by date on top, cooked dishes a few days earlier, with a check against the next 7 days plan", "where": "Use First List"},
    {"name": "Freezer dinner finder", "why": "the oldest freezer dish with enough portions for tonight's eaters", "where": "Freezer Dinner Finder"},
    {"name": "One missing ingredient finder", "why": "the recipes that are only one ingredient short, so one small shop gives a dinner", "where": "One Missing Ingredient Finder"},
    {"name": "Meal from the items you have", "why": "type three items and see which recipes use most of them", "where": "Meal From the Items You Have"},
    {"name": "Before a trip away", "why": "the fridge and pantry items that pass their typed date while you are away, counted before you leave", "where": "Before a Trip Away"},
    {"name": "Leftover eat-by planner", "why": "the dish with the nearest eat-by date, the meals it covers and the dinners planned before that date", "where": "Leftover Eat-By Planner"},
    {"name": "Stock below minimum", "why": "items at or below their minimum with the packs to buy, rounded up to the pack size", "where": "Stock Below Minimum"},
    {"name": "Freezer rotation and space", "why": "the oldest freezer items against the typed months and the room left for the next batch", "where": "Freezer Rotation"},
    {"name": "Past-date review against your own history", "why": "items past the typed date by place, and last month against your own earlier months", "where": "Past-Date Items vs Own History"}]
competitors = [
    {"what": "pantry or inventory app with a yearly renewal", "lacks": "charges every year, keeps your list in an account and does not rank what to use first or score recipes from your stock"},
    {"what": "single-sheet pantry inventory template", "lacks": "lists items and quantities but has no use-by status, no freezer rotation, no leftovers log and no cook-this-first ranking"},
    {"what": "meal-planner app with a paywall", "lacks": "plans meals but does not know what is in the fridge, so nothing says which dinner uses the soup that expires on Friday"},
    {"what": "printable freezer inventory sheet", "lacks": "a blank page you fill by hand: no months in the freezer, no space left, no portions that fit tonight's eaters"},
    {"what": "grocery list app", "lacks": "builds a list but has no minimum stock, no packs to buy rounded to the pack size and no past-date review"}]
guide = [
    'Start here: this workbook shows what is in the house and what to use first. Open Settings on the Start sheet and type your household name, the use-soon window and your freezer space in the yellow cells.',
    'Replace the demo data: clear the sample rows of Stock, Leftovers, Item Catalog, Recipes, Recipe ingredients and Meal plan and type your own; keep the lists and settings. Grey cells calculate by themselves.',
    'Stock: type each item or cooked dish with its place, quantity, the date added and the use-by date typed from the label. The use-by date is always the date you type; check the label and your local rules.',
    'Ranked sheets (Use First Ranking, Cook This First Ranking, Freezer Inventory, Fridge and Leftovers Check, Below Minimum, Leftover Eat-By Board): type the rank numbers 1, 2, 3 once and the rest fills in.',
    'Weekly routine, Sunday: plan the meals, read Cook This First and Use First List, check the Below Minimum sheet for the list, rotate the chores and glance at the calendar.',
    'Monthly routine: pantry and freezer check, a stock take, the past-date review, renewals in the next 90 days and a look at the projects; type the month on Food Flow by Month.',
    'Use the 18 tools for the questions of the week: what do we cook first, what do we use first, which freezer dish fits tonight, which recipe is one item short, what passes its date while we are away.',
    'Print 12 sheets and 12 documents, follow 12 checklists and tap a message link to send a text with the details already written in; the tables with a phone column carry the links.',
    'A single adult with no children or pets can use most sheets: leave the child, pet and carpool rows empty and the ranked lists still work with fewer items.',
    'Renters: read "a trade" as "a maintenance request to the landlord"; nothing on the pantry sheets changes for a rented home.',
    'Context, not a promise: a study of about 4,000 US households found the average household wastes about a third of the food it acquires; your own log shows your own figure.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you, nothing to link or re-connect, no ads and no upsell. It works in Excel and Google Sheets with no macros, no add-ins and no accounts.',
    'What this is not: not a safety service, not a reminder app, not medical, veterinary, legal or financial advice. Every date and rank is calculated from your entries: typical, check the manufacturer\'s instructions and your local rules.']
assert 5 <= len(guide) <= 20
listing = {"title": "Pantry Inventory and Freezer Tracker Excel Template: Use-By Dates, Leftovers Log, What to Cook First, Below-Minimum List",
    "headline": "Know what is in the house, what to use first and what to cook tonight",
    "tags": ["pantry inventory", "freezer inventory", "use by tracker", "leftovers log", "fridge tracker", "meal planning", "food inventory", "kitchen organizer", "home management", "excel template", "stock take", "cook this first", "no subscription"],
    "description": ("Run the food in your home from one Excel workbook: the pantry, the fridge and the chest freezer with the use-by date you type from the label, a status of ok, use soon or past date, and a ranking of what to use first. "
        "Built for a single adult, a couple or a family, owners or renters, with a household of two adults, two children and a dog and cat as the sample.\n\n"
        "The Cook This First ranking scores every recipe by the share of its ingredients on hand and by the expiring items it uses, and ends in one verdict. Use First List puts the item or cooked dish nearest its date on top and checks it against the next 7 days of the meal plan. "
        "The Leftovers sheet logs each batch with portions made and left, the date it went to the freezer and the eat-by date, and the Freezer Inventory lists the chest freezer oldest first with the months against your own typed months.\n\n"
        "18 tools answer the questions of the week: which freezer dish fits tonight, which recipe is only one ingredient short, what can we cook with three items, how many packs to buy for the items at or below their minimum, which items pass their date while we are away, how much room is left in the freezer, "
        "and whether fewer items passed their date than your own average. Print 12 sheets and 12 documents, follow 12 checklists and send 34 ready text messages to the household, the grandparent, the babysitter, the neighbour and the school office.\n\n"
        "This is part two of the eight-part Home Management suite. A standard .xlsx workbook with no macros, no accounts and no yearly renewal, with a demo copy full of sample data to explore first. "
        "Every date, rank and share is calculated from your entries: typical, check the label and your local rules. It is a home kit, not a safety service, and gives no health, medical or legal advice."),
    "features": ["Pantry, fridge and chest freezer stock with use-by status", "Use-first ranking with a next 7 days plan check", "Cook this first: recipes scored from your stock", "Leftovers log and freezer inventory oldest first",
                 "Below-minimum list with packs to buy", "One missing ingredient and three-item meal finders", f"{len(tools)} tools for the questions of every week", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Single adults and renters can use it unchanged", "No macros, no accounts, no yearly renewal"]}
SUITE_ID = SUITE
s = spec(id=f'{SUITE_ID}-p2', slug='home-management-pantry', profession='Home Management', name='Pantry, Freezer and Leftovers',
         tagline='Know what is in the house, what to use first and what to cook tonight', price_usd=29,
         colors={"primary": "#3E5C76", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE_ID, "part": 2, "of": 8, "focus": "Pantry, freezer and leftovers: what is in the house and what to use first"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ho2.en.json'))
    names = [t['sheet'] for t in tables] + [t['sheet'] for t in tools] + [f['sheet'] for f in forms] + [d['sheet'] for d in documents]
    assert len(names) == len(set(names)), [n for n in names if names.count(n) > 1]
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
