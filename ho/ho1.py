"""Home Management suite - part 1: Meal Plan and Grocery List."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho1_lists import *
from ho1_tables import *
from ho1_tools import tools, V, F as FX, W7
import ho1_data as D

SUITE = 'fx-20261118-home-management'
NOTE = "Sample wording: adapt it to your own household, check the manufacturer's instructions and your local rules."
def FW(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
NO = '{list:yesno.no}'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('recipe_card', 'Recipe Card', 'One recipe with its ingredients', 'recipes.recipe_id', FW(
        ('Recipe', 'recipes.recipe'), ('Category', 'recipes.category'), ('Prep minutes', 'recipes.prep_min'), ('Servings', 'recipes.servings'), ('Preference label', 'recipes.pref_label'),
        ('Ingredient lines', 'recipes.ingredient_count'), ('Planned in the last 90 days', 'recipes.planned_90'), ('Days since last planned', 'recipes.days_since')) + [
        FF('Scale for the usual eaters', LK('recipes', 'recipe_id', 'scale_usual'), 'num'), FF('Prep minutes over the busy-day limit', 'MAX(0,%s-{set:busy_limit})' % LK('recipes', 'recipe_id', 'prep_min'), 'int')],
        {"from": "recipe_ingredients", "match": "recipe_ingredients.recipe_id", "columns": ["item", "qty", "unit", "section"], "max": 20}),
    FORM('meal_day_sheet', 'Meal Plan Day Sheet', 'One meal of the plan', 'meal_plan.plan_id', FW(
        ('Date', 'meal_plan.date'), ('Weekday', 'meal_plan.weekday'), ('Slot', 'meal_plan.slot'), ('Recipe', 'meal_plan.recipe'), ('Servings', 'meal_plan.servings'), ('Cook', 'meal_plan.cook'),
        ('Prep minutes', 'meal_plan.prep_min'), ('Preference label', 'meal_plan.pref_label'), ('Cooked', 'meal_plan.cooked')) + [
        FF('Days from today, negative is past', '-%s' % LK('meal_plan', 'plan_id', 'age'), 'int'), FF('Meals planned on this date', 'COUNTIFS({range:meal_plan.date},%s)' % LK('meal_plan', 'plan_id', 'date'), 'int'),
        FF('Prep minutes over the busy-day limit', 'MAX(0,SUMIFS({range:meal_plan.prep_min},{range:meal_plan.date},%s)-{set:busy_limit})' % LK('meal_plan', 'plan_id', 'date'), 'int')]),
    FORM('week_sheet', 'Weekly Meal Plan Sheet', 'One day of the 14-day plan with the cook', 'cook_load.day_no', FW(
        ('Date', 'cook_load.date'), ('Adult 2 shift', 'cook_load.a2_shift'), ('Adult 1 late day, 1 or 0', 'cook_load.late1'), ('Suggested cook', 'cook_load.suggested'), ('Planned cook', 'cook_load.planned_cook'),
        ('Dinner', 'cook_load.recipe'), ('Servings', 'cook_load.servings'), ('Dinner prep minutes', 'cook_load.dinner_prep'), ('Dinner time', 'cook_load.eat_at'), ('Start cooking by', 'cook_load.start_by'),
        ('Dinners planned, 7 days from this date', 'cook_load.dinners_week')) + [
        FF('Prep minutes of all meals that day', LK('cook_load', 'day_no', 'prep'), 'int'), FF('Minutes under the busy-day limit', '{set:busy_limit}-%s' % LK('cook_load', 'day_no', 'prep'), 'int')]),
    FORM('grocery_sheet', 'Grocery List Sheet', 'One grocery list with its items', 'grocery_lists.list_id', FW(
        ('Date', 'grocery_lists.date'), ('Shop', 'grocery_lists.shop'), ('Status', 'grocery_lists.status'), ('Items', 'grocery_lists.items'), ('Estimated cost', 'grocery_lists.est_cost'),
        ('Actual cost', 'grocery_lists.actual_cost'), ('Items the plan needs from this shop', 'grocery_lists.shop_plan_items')) + [
        FF('Items typed on the list', 'COUNTIFS({range:grocery_items.list_id},{pick})', 'int'), FF('Estimated cost per item', 'IFERROR(ROUND(%s/%s,2),0)' % (LK('grocery_lists', 'list_id', 'est_cost'), LK('grocery_lists', 'list_id', 'items')), 'money')],
        {"from": "grocery_items", "match": "grocery_items.list_id", "columns": ["item", "qty", "unit", "section", "bought"], "max": 40}),
    FORM('shop_trip_sheet', 'Shop Trip Sheet', 'One shop trip: bought, left and the cost line', 'grocery_lists.list_id', FW(
        ('Date', 'grocery_lists.date'), ('Shop', 'grocery_lists.shop'), ('Items', 'grocery_lists.items'), ('Estimated cost', 'grocery_lists.est_cost'), ('Actual cost', 'grocery_lists.actual_cost'),
        ('Actual less estimate', 'grocery_lists.diff'), ('Week starting', 'grocery_lists.week')) + [
        FF('Items bought', 'COUNTIFS({range:grocery_items.list_id},{pick},{range:grocery_items.bought},%s)' % YES, 'int'), FF('Items left for the next trip', 'COUNTIFS({range:grocery_items.list_id},{pick},{range:grocery_items.bought},%s)' % NO, 'int'),
        FF('Cost line of the bought items', 'SUMIFS({range:grocery_items.cost},{range:grocery_items.list_id},{pick})', 'money'),
        FF('Cost line per bought item', 'IFERROR(ROUND(SUMIFS({range:grocery_items.cost},{range:grocery_items.list_id},{pick})/COUNTIFS({range:grocery_items.list_id},{pick},{range:grocery_items.bought},%s),2),0)' % YES, 'money'),
        FF('Days since the last trip to this shop', '%s-SUMPRODUCT(MAX(({range:grocery_lists.shop}=%s)*({range:grocery_lists.date}<%s)*{range:grocery_lists.date}))' % (LK('grocery_lists', 'list_id', 'date'), LK('grocery_lists', 'list_id', 'shop'), LK('grocery_lists', 'list_id', 'date')), 'int')]),
    FORM('staples_card', 'Staples Card', 'One item and how often it runs out', 'staples.item', FW(
        ('Item', 'staples.item'), ('Section', 'staples.section'), ('Weeks on a list, last 26', 'staples.weeks'), ('Share of weeks', 'staples.share'), ('Last bought', 'staples.last_bought'),
        ('Days since last bought', 'staples.days_since'), ('Runs out most, 1 is most', 'staples.rank'), ('Standing item, 1 or 0', 'staples.standing')) + [
        FF('Pack size', 'INDEX({range:items.pack_size},MATCH({pick},{range:items.item},0))', 'num'), FF('Pack price, a cost line', 'INDEX({range:items.pack_price},MATCH({pick},{range:items.item},0))', 'money'),
        FF('Minimum stock', 'INDEX({range:items.min_stock},MATCH({pick},{range:items.item},0))', 'num'), FF('On hand', 'SUMIFS({range:stock.quantity},{range:stock.item},{pick})', 'num')]),
    FORM('people_home_sheet', 'People At Home Sheet', 'One scenario: who is at the table', 'scenarios.scenario', FW(
        ('Scenario', 'scenarios.scenario'), ('From', 'scenarios.date'), ('To', 'scenarios.end_date'), ('Days', 'scenarios.days'), ('Adults', 'scenarios.adults'), ('Children', 'scenarios.children'),
        ('Guests', 'scenarios.guests'), ('Servings per dinner', 'scenarios.servings'), ('Against the usual eaters', 'scenarios.change'), ('Dinner portions in the period', 'scenarios.portions'), ('Note', 'scenarios.note')) + [
        FF('Usual eaters from Settings', '{set:usual_eaters}', 'int'), FF('Dinner portions of a usual period', '{set:usual_eaters}*%s' % LK('scenarios', 'scenario', 'days'), 'int')]),
    FORM('guest_meals_sheet', 'Guest Meals Sheet', 'One day with guests at dinner', 'people_home.date', FW(
        ('Date', 'people_home.date'), ('Guests', 'people_home.guests'), ('Guest', 'people_home.guest_name'), ('Guest phone', 'people_home.guest_phone'), ('Dinner', 'people_home.recipe'),
        ('Servings planned', 'people_home.planned_servings'), ('Eaters', 'people_home.eaters'), ('Portions spare, negative is short', 'people_home.gap'), ('Preference label', 'people_home.pref_label'), ('Note', 'people_home.away_note')) + [
        FF('Portions to cook more', 'MAX(0,-%s)' % LK('people_home', 'date', 'gap'), 'int'), FF('Pick the dinner by', LK('people_home', 'date', 'pick_by'), 'date')]),
    FORM('item_sheet', 'Item Catalog Sheet', 'One catalog item with its pack and stock', 'items.item_id', FW(
        ('Item', 'items.item'), ('Section', 'items.section'), ('Unit', 'items.unit'), ('Place', 'items.place'), ('Per serving', 'items.per_serving'), ('Pack size', 'items.pack_size'),
        ('Shelf days, typical, check the label', 'items.shelf_days'), ('Minimum stock', 'items.min_stock'), ('Pack price', 'items.pack_price'), ('Shop', 'items.shop'), ('Recipes using it', 'items.used_in')) + [
        FF('On hand', 'SUMIFS({range:stock.quantity},{range:stock.item},%s)' % LK('items', 'item_id', 'item'), 'num'),
        FF('Packs to restock', 'IF(SUMIFS({range:stock.quantity},{range:stock.item},%s)<%s,ROUNDUP((%s-SUMIFS({range:stock.quantity},{range:stock.item},%s))/%s,0),0)' % (
            LK('items', 'item_id', 'item'), LK('items', 'item_id', 'min_stock'), LK('items', 'item_id', 'min_stock'), LK('items', 'item_id', 'item'), LK('items', 'item_id', 'pack_size')), 'int'),
        FF('Cost line of one pack at the pack size', LK('items', 'item_id', 'pack_price'), 'money')]),
    FORM('ingredient_sheet', 'Recipe Ingredient Sheet', 'One ingredient line and what the week plan needs', 'recipe_ingredients.ingredient_id', FW(
        ('Recipe ID', 'recipe_ingredients.recipe_id'), ('Recipe', 'recipe_ingredients.recipe'), ('Item', 'recipe_ingredients.item'), ('Quantity', 'recipe_ingredients.qty'), ('Unit', 'recipe_ingredients.unit'),
        ('Section', 'recipe_ingredients.section'), ('Recipe servings', 'recipe_ingredients.rec_servings'), ('Servings planned, next 7 days', 'recipe_ingredients.plan_servings'),
        ('Needed for the week plan', 'recipe_ingredients.need_week'), ('Pack size of the item', 'recipe_ingredients.pack_size')) + [
        FF('Share of a pack', LK('recipe_ingredients', 'ingredient_id', 'qty_packs'), 'num'), FF('On hand', 'SUMIFS({range:stock.quantity},{range:stock.item},%s)' % LK('recipe_ingredients', 'ingredient_id', 'item'), 'num')]),
    FORM('batch_sheet', 'Batch Cook Sheet', 'One recipe cooked as a batch', 'recipes.recipe_id', FW(
        ('Recipe', 'recipes.recipe'), ('Category', 'recipes.category'), ('Prep minutes', 'recipes.prep_min'), ('Servings', 'recipes.servings'), ('Ingredient lines', 'recipes.ingredient_count')) + [
        FF('Batches cooked at once', '{set:batch_factor}', 'int'), FF('Portions in the batch', LK('recipes', 'recipe_id', 'portions_batch'), 'int'),
        FF('Portions left after a usual dinner', '%s-{set:usual_eaters}' % LK('recipes', 'recipe_id', 'portions_batch'), 'int'), FF('Fridge days from Settings', '{set:leftover_days}', 'int')],
        {"from": "recipe_ingredients", "match": "recipe_ingredients.recipe_id", "columns": ["item", "qty", "unit"], "max": 20}),
    FORM('meal_review_sheet', 'Meal Review Sheet', 'One month of dinners and the grocery cost line', 'month_glance.month', FW(
        ('Month', 'month_glance.month'), ('Dinners planned', 'month_glance.dinners_planned'), ('Dinners planned up to today', 'month_glance.planned_to_date'), ('Dinners cooked', 'month_glance.dinners_cooked'),
        ('Share cooked', 'month_glance.share_cooked'), ('Lists bought', 'month_glance.lists'), ('Items bought', 'month_glance.items'), ('Grocery cost line', 'month_glance.grocery_cost'),
        ('Cost line per dinner cooked', 'month_glance.cost_per_dinner')) + [
        FF('Dinners not cooked', '%s-%s' % (LK('month_glance', 'month', 'planned_to_date'), LK('month_glance', 'month', 'dinners_cooked')), 'int'),
        FF('Average of the 3 months before', 'IFERROR(AVERAGEIFS({range:month_glance.grocery_cost},{range:month_glance.month},">="&EDATE({pick},-3),{range:month_glance.month},"<"&{pick}),0)', 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('day_page_doc', 'Meal Plan Day Page', 'Meal plan day page for the fridge', 'cook_load.day_no', [
        'Meal plan page of {set:household}, dated {today}. Day: {col:cook_load.date}. Adult 2 shift: {col:cook_load.a2_shift}. Dinner: {col:cook_load.recipe}, {col:cook_load.servings} servings, prep {col:cook_load.dinner_prep} minutes.',
        'Suggested cook from the work pattern: {col:cook_load.suggested}. Planned cook: {col:cook_load.planned_cook}. Start cooking by {col:cook_load.start_by} for dinner at {col:cook_load.eat_at}.',
        'Dinners planned in the 7 days from this date: {col:cook_load.dinners_week}. Prep minutes of all meals on the day: {col:cook_load.prep}.',
        'Put this page on the fridge. Dates and cooks are calculated from your entries.'], ['Cook', 'Household member'], NOTE),
    DOC('shop_page_doc', 'Grocery List Page', 'Grocery list by shop and section', 'grocery_lists.list_id', [
        'Grocery list page of {set:household}, dated {today}. List {col:grocery_lists.list_id} for the {col:grocery_lists.shop} on {col:grocery_lists.date}. Status: {col:grocery_lists.status}.',
        'Items typed: {col:grocery_lists.items}. Estimated cost line: {col:grocery_lists.est_cost}. Items the week plan needs from this shop: {col:grocery_lists.shop_plan_items}, cost line {col:grocery_lists.shop_plan_cost}.',
        'Take the list by section: fruit and veg, dairy and eggs, meat and fish, bakery, dry goods and tins, frozen, drinks, household and pet. The Plan needs vs stock sheet rounds every item up to the pack size.',
        'Quantities and cost lines are calculated from your entries.'], ['Shopper', 'Household member'], NOTE),
    DOC('recipe_card_doc', 'Recipe Card Page', 'Recipe card scaled to the usual eaters', 'recipes.recipe_id', [
        'Recipe card of {set:household}, dated {today}. Recipe: {col:recipes.recipe} ({col:recipes.category}). Preference label: {col:recipes.pref_label}.',
        'Prep minutes: {col:recipes.prep_min}. The recipe makes {col:recipes.servings} servings with {col:recipes.ingredient_count} ingredient lines. For {set:usual_eaters} eaters multiply the quantities by {col:recipes.scale_usual}.',
        'Planned {col:recipes.planned_90} times in the last 90 days. The ingredient lines are on the Recipe ingredients sheet or the Recipe Card form.',
        'Check the label and the manufacturer instructions for storage and cooking times.'], ['Cook', 'Household member'], NOTE),
    DOC('cook_rota_doc', 'Cook Rota Page', 'Cook rota for a day of the week', 'cook_load.day_no', [
        'Cook rota page of {set:household}, dated {today}. Day: {col:cook_load.date}. Adult 2 shift: {col:cook_load.a2_shift}. Adult 1 late day (1 yes, 0 no): {col:cook_load.late1}.',
        'Suggested cook: {col:cook_load.suggested}. Planned cook: {col:cook_load.planned_cook}. Check: {col:cook_load.check}.',
        'Dinner: {col:cook_load.recipe}, {col:cook_load.servings} servings, at {col:cook_load.eat_at}. The suggestion follows the work pattern and your plan decides.',
        'A rota is a repeating schedule of who does what. Agree changes together.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('prep_list_doc', 'Prep List Page', 'Prep list for a busy day', 'people_home.date', [
        'Prep list of {set:household} for {col:people_home.date}. Dinner: {col:people_home.recipe}, {col:people_home.planned_servings} servings for {col:people_home.eaters} eaters.',
        'Prep minutes: {col:people_home.prep_min}. Dinner at {col:people_home.eat_at}; set the table at {col:people_home.table_at}. Portions spare (negative is short): {col:people_home.gap}.',
        'Busy-day limit from Settings: {set:busy_limit} prep minutes. On a late day prepare the vegetables and sauce in the morning and keep a portion for the person who works late.',
        'Check the label and your local rules for how long cooked food keeps.'], ['Cook', 'Household member'], NOTE),
    DOC('staples_doc', 'Staples Checklist Page', 'Staples checklist for one item', 'staples.item', [
        'Staples page of {set:household}, dated {today}. Item: {col:staples.item} ({col:staples.section}).',
        'On a list in {col:staples.weeks} of the last 26 weeks, a share of {col:staples.share}. Last bought on {col:staples.last_bought}, {col:staples.days_since} days ago. Rank: {col:staples.rank} (1 runs out most).',
        'A staple is an item on the list almost every week. Keep a standing amount at home and check it every Sunday.',
        'Calculated from your own lists, not a promise of less waste.'], ['Shopper', 'Household member'], NOTE),
    DOC('away_plan_doc', 'One Adult Away Plan', 'Plan for a week with one adult away', 'scenarios.scenario', [
        'Plan of {set:household} for the scenario {col:scenarios.scenario}, dated {today}. From {col:scenarios.date} to {col:scenarios.end_date}, {col:scenarios.days} days.',
        'At the table: {col:scenarios.adults} adults, {col:scenarios.children} children and {col:scenarios.guests} guests, {col:scenarios.servings} servings per dinner, {col:scenarios.change} against the usual eaters.',
        'Dinner portions in the period: {col:scenarios.portions}. Choose quick recipes from the Busy-day meal picker and cut the list with the One adult away tool. Note: {col:scenarios.note}.',
        'Portions and items are calculated from your entries.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('guest_plan_doc', 'Guest Meal Plan', 'Guest meal plan for a day', 'people_home.date', [
        'Guest meal plan of {set:household} for {col:people_home.date}. Guests: {col:people_home.guests} ({col:people_home.guest_name}). Dinner: {col:people_home.recipe}.',
        'Eaters: {col:people_home.eaters}. Servings planned: {col:people_home.planned_servings}. Portions spare (negative is short): {col:people_home.gap}. Preference label of the dish: {col:people_home.pref_label}.',
        'Ask guests for a preference or avoid note by {col:people_home.pick_by}. Note: {col:people_home.away_note}.',
        'Use the Guests staying tool for the extra packs.'], ['Host', 'Guest'], NOTE),
    DOC('lunch_box_doc', 'School Lunch Box Plan', 'School lunch box plan for a day', 'people_home.date', [
        'Lunch box plan of {set:household} for {col:people_home.date}. Children at home: {col:people_home.children}. Dinner the evening before or after: {col:people_home.recipe}.',
        'Lunch boxes to pack: {col:people_home.children}. Portions spare from dinner (negative is short): {col:people_home.gap}. Spare portions can fill the next lunch boxes; check the label for how long they keep.',
        'Ask the children for a choice by {col:people_home.pick_by}. Note: {col:people_home.away_note}.',
        'Fridge days typed in Settings: {set:leftover_days}, typical, check the label.'], ['Adult', 'Child'], NOTE),
    DOC('month_doc', 'Monthly Meal Summary', 'Monthly meal summary', 'month_glance.month', [
        'Monthly meal summary of {set:household} for the month starting {col:month_glance.month}. Dinners planned: {col:month_glance.dinners_planned}, planned up to today {col:month_glance.planned_to_date}, cooked {col:month_glance.dinners_cooked}.',
        'Share cooked: {col:month_glance.share_cooked}. Lists bought: {col:month_glance.lists} with {col:month_glance.items} items. Grocery cost line: {col:month_glance.grocery_cost}, {col:month_glance.cost_per_dinner} per dinner cooked.',
        'Compare with your own earlier months. Write one change for next month.',
        'Calculated from your entries. A record, not advice.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('trip_record_doc', 'Shop Trip Record', 'Shop trip record', 'grocery_lists.list_id', [
        'Shop trip record of {set:household}. List {col:grocery_lists.list_id}, {col:grocery_lists.shop}, on {col:grocery_lists.date}, the week starting {col:grocery_lists.week}.',
        'Items: {col:grocery_lists.items}. Estimated cost line: {col:grocery_lists.est_cost}. Actual cost line: {col:grocery_lists.actual_cost}. Actual less estimate: {col:grocery_lists.diff}.',
        'On the usual shop day (1 yes, 0 no): {col:grocery_lists.on_shop_day}. Keep the receipt with this record if you want to check the cost line.',
        'A record of your own shopping, not advice.'], ['Shopper', 'Household member'], NOTE),
    DOC('contents_doc', 'Recipe Book Contents Page', 'Recipe book contents page', 'recipes.recipe_id', [
        'Recipe book page of {set:household}. {col:recipes.recipe_id}: {col:recipes.recipe}, category {col:recipes.category}, {col:recipes.prep_min} prep minutes, {col:recipes.servings} servings.',
        'The category holds {col:recipes.in_category} recipes with an average of {col:recipes.avg_prep_cat} prep minutes. Preference label: {col:recipes.pref_label}.',
        'Planned {col:recipes.planned_90} times in the last 90 days; {col:recipes.days_since} days since last planned. Quickest dinner rank: {col:recipes.quick_rank}.',
        'Print one page per category to keep a recipe book on the shelf.'], ['Cook', 'Household member'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('sunday_plan', 'Sunday Planning', 'people_home', 'people_home.date', [('Plan the dinners for the week', 0), ('Check the pantry, fridge and freezer', 0), ('Write or update the grocery list', 0), ('Glance at the family calendar', 0), ('Check the cook for every day', 1), ('Tell the household where the plan is', 1)]),
    CHK('weekly_shop', 'Weekly Shop', 'grocery_lists', 'grocery_lists.date', [('Check the list against stock', -1), ('Add what the household asked for', -1), ('Take bags and the list', 0), ('Buy the items by section', 0), ('Mark the items bought', 0), ('Type the actual cost line', 1)]),
    CHK('topup_shop', 'Top-up Shop', 'grocery_lists', 'grocery_lists.date', [('Check what runs out before the next weekly shop', -1), ('Write the short list', -1), ('Buy only the list', 0), ('Mark the items bought', 0), ('Type the actual cost line', 1)]),
    CHK('after_shop', 'After the Shop', 'grocery_lists', 'grocery_lists.date', [('Put cold items away first', 0), ('Move older items to the front', 0), ('Type new use-by dates from the labels', 0), ('Update the stock quantities', 1), ('Throw away the packaging', 1), ('Keep the receipt if you want to check it', 1)]),
    CHK('batch_cooking', 'Batch Cooking Day', 'meal_plan', 'meal_plan.date', [('Choose the recipe to batch', -2), ('Check the ingredients against stock', -2), ('Buy what is missing', -1), ('Cook the batch', 0), ('Cool and portion it', 0), ('Label the portions with the date', 0), ('Type the portions into Stock on hand', 1)]),
    CHK('shift_week', 'Meal Plan for a Shift Week', 'shifts', 'shifts.date', [('Read adult 2 shifts for the week', 0), ('Mark adult 1 late days', 0), ('Put quick dinners on the days both are busy', 0), ('Plan a dinner to prepare ahead', 1), ('Check the cook rota', 1), ('Send the plan to the household', 1)]),
    CHK('one_adult_away', 'Week with One Adult Away', 'people_home', 'people_home.date', [('Type the days away on People at home', -3), ('Use the One adult away tool', -3), ('Choose quick recipes', -2), ('Cut the grocery list', -1), ('Tell the grandparent or the sitter the plan', -1), ('Check the plan again on the first day', 0)]),
    CHK('hosting_meals', 'Hosting Weekend Meals', 'people_home', 'people_home.date', [('Count the guests on People at home', -7), ('Ask guests for a preference or avoid note', -6), ('Choose the menu', -5), ('Use the Guests staying tool', -4), ('Buy the extra packs', -2), ('Cook what can be made ahead', -1), ('Set the table', 0)]),
    CHK('back_to_school', 'Back-to-School Lunches', 'people_home', 'people_home.date', [('Count the lunch boxes needed', -7), ('Ask the children for choices', -6), ('Add lunch items to the list', -5), ('Buy the items', -2), ('Pack the first lunch boxes', 0), ('Review after the first week', 7)]),
    CHK('new_recipe', 'New Recipe Trial', 'meal_plan', 'meal_plan.date', [('Add the recipe to the Recipes sheet', -3), ('Type the ingredient lines', -3), ('Add it to the plan', -2), ('Buy the missing items', -1), ('Cook it', 0), ('Ask the household for a mark', 1), ('Keep or drop it', 2)]),
    CHK('month_review', 'Month Meal Review', 'month_glance', 'month_glance.month', [('Check dinners planned against cooked', 28), ('Read the grocery cost line of the month', 28), ('Look at the staples that ran out', 29), ('Pick recipes due a turn', 29), ('Write one change for next month', 30)]),
    CHK('single_adult', 'Single adult first week', 'people_home', 'people_home.date', [('Replace the demo data with your own', 0), ('Type 1 adult and no children on People at home', 0), ('Plan 3 dinners and one batch', 1), ('Use the Plan for one person tool', 1), ('Write the list and shop', 2), ('Check what was left over', 6)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('a2_start', 'Adult 2: start dinner by', 'cook_load', 'cook_load.a2_phone', 'Hi {a2_name}, dinner on {date} is {recipe}, prep {dinner_prep} minutes. Can you start it by {start_by}? {household}'),
    M('a2_late', 'Adult 2: your late shift, I cook', 'cook_load', 'cook_load.a2_phone', 'Hi {a2_name}, your shift on {date} is {a2_shift}. I will cook {recipe} and keep you a portion. {household}'),
    M('a1_late', 'Adult 1: late day, dinner time', 'cook_load', 'cook_load.a1_phone', 'Hi {a1_name}, dinner on {date} is {recipe}. You are on a late day, so we eat at {eat_at}. {household}'),
    M('a1_list', 'Adult 1: the list, anything to add', 'grocery_lists', 'grocery_lists.a1_phone', 'Hi {a1_name}, the list for {date} has {items} items for the {shop}. Anything to add? {household}'),
    M('a2_shop', 'Adult 2: can you take the weekly shop', 'grocery_lists', 'grocery_lists.a2_phone', 'Hi {a2_name}, the weekly shop is on {date}, the list has {items} items. Can you take it? {household}'),
    M('a1_topup', 'Adult 1: check the top-up list', 'grocery_lists', 'grocery_lists.a1_phone', 'Hi {a1_name}, please check the list for the top-up shop on {date}, {items} items so far. {household}'),
    M('shop_moves', 'Adult 2: the shop day moves', 'grocery_lists', 'grocery_lists.a2_phone', 'Hi {a2_name}, the shop day moves to {date}. The list has {items} items for the {shop}. {household}'),
    M('c1_table', 'Child 1: set the table', 'people_home', 'people_home.c1_phone', 'Hi {c1_name}, tonight is {recipe} on {date}. Can you set the table at {table_at}? {household}'),
    M('c1_pick', 'Child 1: you pick dinner', 'people_home', 'people_home.c1_phone', 'Hi {c1_name}, you pick dinner on {date}. Please choose from the recipe box by {pick_by}. {household}'),
    M('c2_help', 'Child 2: shall we help cook', 'people_home', 'people_home.c2_phone', 'Hi {c2_name}, dinner on {date} is {recipe}, it has the {pref_label} label. Shall we help cook? {household}'),
    M('c2_change', 'Child 2: tell me if you want a change', 'people_home', 'people_home.c2_phone', 'Hi {c2_name}, dinner on {date} is {recipe}. Please tell me by {pick_by} if you want a change. {household}'),
    M('gp_thanks', 'Grandparent: thank you for helping', 'people_home', 'people_home.gp_phone', 'Hello {gp_name}, thank you for helping on {date}. Dinner is {recipe}, it is in the fridge at {table_at}. {household}'),
    M('gp_join', 'Grandparent: would you like to join', 'people_home', 'people_home.gp_phone', 'Hello {gp_name}, we are {eaters} for dinner on {date}. Would you like to join us? {household}'),
    M('gp_bring', 'Grandparent: please bring an item', 'plan_needs', 'plan_needs.gp_phone', 'Hello {gp_name}, could you please bring {item} on {shop_date}? We are out. {household}'),
    M('bs_dinner', 'Babysitter: dinner for the children', 'people_home', 'people_home.bs_phone', 'Hello {bs_name}, dinner for the children on {date} is {recipe}. Prep notes are on the fridge. {household}'),
    M('bs_time', 'Babysitter: when the children eat', 'people_home', 'people_home.bs_phone', 'Hello {bs_name}, the children eat at {eat_at} on {date}. There is a portion of {recipe}. {household}'),
    M('cp_dish', 'Carpool family: bring a dish', 'people_home', 'people_home.cp_phone', 'Hello {cp_name}, we can bring a dish for the activity evening on {date}. {recipe} has {planned_servings} servings. {household}'),
    M('cp_eat', 'Carpool family: eat after the lift', 'people_home', 'people_home.cp_phone', 'Hello {cp_name}, the children eat after the lift on {date}. Dinner is {recipe}. {household}'),
    M('school_lunch', 'School office: lunch order change', 'people_home', 'people_home.so_phone', 'Hello {so_name}, the lunch order for {date} needs a change, one child is away. Thank you, {household}'),
    M('nb_portions', 'Neighbour: spare portions', 'people_home', 'people_home.nb_phone', 'Hello {nb_name}, we may have {gap} extra portions of {recipe} on {date}. Would you like one? {household}'),
    M('nb_borrow', 'Neighbour: borrow an item', 'plan_needs', 'plan_needs.nb_phone', 'Hello {nb_name}, can we borrow {item} on {shop_date} for a dinner? Thank you, {household}'),
    M('dw_late', 'Dog walker: dinner is late', 'cook_load', 'cook_load.dw_phone', 'Hello {dw_name}, dinner is late on {date}, please bring the dog back by {back_by}. Thank you, {household}'),
    M('guest_pref', 'Guest: preference or avoid note', 'people_home', 'people_home.guest_phone', 'Hello {guest_name}, dinner on {date} is {recipe}. Please tell us any preference or avoid note by {pick_by}. {household}'),
    M('guest_place', 'Guest: we have a place for you', 'people_home', 'people_home.guest_phone', 'Hello {guest_name}, we have a place for {guests} on {date}. The menu is {recipe}. {household}'),
    M('guest_thanks', 'Guest: thank you for coming', 'people_home', 'people_home.guest_phone', 'Hello {guest_name}, thank you for coming on {date}. We can send you the recipe of {recipe}. {household}'),
    M('plan_week', 'Adult 1: the plan is on the fridge', 'cook_load', 'cook_load.a1_phone', 'Hi {a1_name}, the plan for the week of {date} is on the fridge, {dinners_week} dinners planned. {household}'),
    M('away_cut', 'Adult 1: one adult away, portions cut', 'scenarios', 'scenarios.a1_phone', 'Hi {a1_name}, for {scenario} from {date} to {end_date}, dinners are cut to {servings} portions. {household}'),
    M('heavy_list', 'Adult 2: the list was heavier than usual', 'spend_hist', 'spend_hist.a2_phone', 'Hi {a2_name}, the list of the week starting {week_start} was heavier than usual by {heavier_by} items. {household}'),
    M('out_of', 'Adult 1: out of an item again', 'staples', 'staples.a1_phone', 'Hi {a1_name}, we are out of {item} again. It is on the list for {shop_date}. {household}'),
    M('leftovers', 'Adult 2: leftovers in the fridge', 'stock', 'stock.a2_phone', 'Hi {a2_name}, {item} is in the fridge, use by {use_by}. {household}'),
    M('batch_done', 'Adult 1: the batch is cooked', 'stock', 'stock.a1_phone', 'Hi {a1_name}, the batch of {item} is cooked, {quantity} portions are in stock. {household}'),
    M('ideas', 'Adult 2: add your recipe ideas', 'cook_load', 'cook_load.a2_phone', 'Hi {a2_name}, please add your recipe ideas for next week by {plan_by}. {household}'),
    M('month_review', 'Adult 2: month meal review', 'month_glance', 'month_glance.a2_phone', 'Hi {a2_name}, month meal review for {month}: {dinners_cooked} of {planned_to_date} dinners were cooked. {household}'),
    M('new_recipe', 'Adult 2: the new recipe', 'recipe_hist', 'recipe_hist.a2_phone', 'Hi {a2_name}, the recipe {recipe} is planned for {next_planned}. Please give it a mark after. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def C_(*a): return 'COUNTIFS(' + ','.join(a) + ')'
K = lambda label, f, fmt='int', **kw: KPI(label, f, fmt, **kw)
kpis = [
    K('Dinners planned next 7 days', C_(MP('slot'), DIN, N7)),
    K('Dinners planned next 14 days', C_(MP('slot'), DIN, N14)),
    K('Empty dinner slots next 7 days', C_(R('week_grid', 'flag'), V_MISS), alert={"when": "> 0", "style": "warn"}),
    K('Dinners cooked last 30 days', C_(MP('slot'), DIN, MP('cooked'), YES, L30)),
    K('Share of dinners cooked, last 30 days', 'IFERROR(%s/%s,0)' % (C_(MP('slot'), DIN, MP('cooked'), YES, L30), C_(MP('slot'), DIN, L30)), 'pct'),
    K('Recipes in the box', 'COUNTA(%s)' % R('recipes', 'recipe_id')),
    K('Recipes planned in the last 90 days', C_(R('recipes', 'planned_90'), '">0"')),
    K('Recipes not planned for 90 days or more', '%s+%s' % (C_(R('recipes', 'days_since'), '">="&{set:rare_days}'), C_(R('recipes', 'recipe_id'), '"<>"', R('recipes', 'days_since'), '""'))),
    K('Average dinner prep minutes next 14 days', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,%s,%s),0),0)' % (MP('prep_min'), MP('slot'), DIN, N14)),
    K('Quick dinners planned next 7 days', C_(MP('slot'), DIN, N7, MP('prep_min'), '"<="&{set:quick_min}')),
    K('Quick dinners on late days, next 14 days', C_(MP('slot'), DIN, N14, MP('late'), '1', MP('prep_min'), '"<="&{set:quick_min}')),
    K('Dinners cooked by adult 2 last 30 days', C_(MP('slot'), DIN, MP('cook'), A2, MP('cooked'), YES, L30)),
    K('Dinners cooked by adult 1 last 30 days', C_(MP('slot'), DIN, MP('cook'), A1, MP('cooked'), YES, L30)),
    K('Planned portions next 7 days', 'SUMIFS(%s,%s,%s,%s)' % (MP('servings'), MP('slot'), DIN, N7)),
    K('Eaters per dinner, average next 7 days', 'IFERROR(ROUND(AVERAGEIFS(%s,%s),1),0)' % (PH('eaters'), W7), 'num'),
    K('Grocery lists last 30 days', C_(GL('date'), '">="&({today}-29)', GL('date'), '"<="&{today}')),
    K('Grocery items bought last 30 days', C_(GIT('bought'), YES, GIT('date'), '">="&({today}-29)', GIT('date'), '"<="&{today}')),
    K('Grocery cost line last 30 days', 'SUMIFS(%s,%s)' % (GL('actual_cost'), G30), 'money'),
    K('Weekly shop average, 4 complete weeks', 'IFERROR(AVERAGEIFS(%s,%s,%s,%s,">="&(%s-28),%s,"<"&%s),0)' % (GL('actual_cost'), GL('shop'), SH_W, GL('date'), TW, GL('date'), TW), 'money'),
    K('Open grocery lists', C_(GL('status'), OPEN, GL('list_id'), '"<>"')),
    K('Items on the open lists', 'SUMIFS(%s,%s,%s)' % (GL('items'), GL('status'), OPEN)),
    K('Items to buy for the week plan', 'SUM(%s)' % PN('buy_flag')),
    K('Packs to buy for the week plan', 'SUM(%s)' % PN('total_packs')),
    K('Staples on a list every week, 26 weeks', C_(R('staples', 'weeks'), '">="&26')),
    K('Top-up shops last 30 days', C_(GL('shop'), SH_T, G30)),
    K('Market and online orders last 30 days', '%s+%s' % (C_(GL('shop'), SH_M, G30), C_(GL('shop'), tok('shop', 'Online order'), G30))),
    K('Avoid-label dinners, next 14 days', 'SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s)' % (R('pref_mix', 'dinners14'), R('pref_mix', 'label'), tok('pref', 'Child 2 avoids'), R('pref_mix', 'dinners14'), R('pref_mix', 'label'), tok('pref', 'Adult 2 avoids'))),
    K('Family favourites planned next 14 days', 'SUMIFS(%s,%s,%s)' % (R('pref_mix', 'dinners14'), R('pref_mix', 'label'), tok('pref', 'Family favourite'))),
    K('Leftover nights planned next 14 days', C_(MP('slot'), DIN, N14, MP('ings'), '0')),
    K('Stock items not in any planned dinner', C_(R('stock', 'in_plan'), '0')),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Meals Dashboard", "kpis": kpis,
    "monthly": {"title": "Grocery cost line: actual and estimated", "date": "grocery_lists.date", "series": [
        {"label": "Actual cost line", "sum": "grocery_lists.actual_cost", "date": "grocery_lists.date"}, {"label": "Estimated cost line", "sum": "grocery_lists.est_cost", "date": "grocery_lists.date"}]},
    "breakdowns": [{"title": "Items by section", "by": "grocery_items.section", "agg": "count"}, {"title": "Cost line by shop", "by": "grocery_lists.shop", "value": "grocery_lists.actual_cost", "agg": "sum"},
                   {"title": "Recipes by category", "by": "recipes.category", "agg": "count"}, {"title": "Dinners by weekday", "by": "meal_plan.weekday", "agg": "count"}]}
def W(c, op, v): return (c, op, v)
YESV = '{list:yesno.yes}'; DINV = tok('slot', 'Dinner')
insights = {"filters": [{"label": "Shop", "list": "shop"}, {"label": "Meal slot", "list": "slot"}],
    "gauges": [
        {"title": "Planned dinners cooked, last 30 days", "num": AGG('count', 'meal_plan', where=[W('slot', '=', DINV), W('cooked', '=', YESV), W('age', '>=', 0), W('age', '<=', 29)]),
         "den": AGG('count', 'meal_plan', where=[W('slot', '=', DINV), W('age', '>=', 0), W('age', '<=', 29)])},
        {"title": "Dinners planned next 7 days against 7", "num": AGG('count', 'week_grid', where=[W('slot', '=', DINV), W('planned', '=', 1)]), "den": AGG('count', 'week_grid', where=[W('slot', '=', DINV)])},
        {"title": "Quick dinners on late days, next 14 days", "num": AGG('count', 'meal_plan', where=[W('slot', '=', DINV), W('late', '=', 1), W('prep_min', '<=', '{set:quick_min}'), W('in14', '=', 1)]),
         "den": AGG('count', 'meal_plan', where=[W('slot', '=', DINV), W('late', '=', 1), W('in14', '=', 1)])},
        {"title": "Items in stock for the week plan", "num": AGG('sum', 'plan_needs', 'plan_needs.covered'), "den": AGG('sum', 'plan_needs', 'plan_needs.needs_flag')},
        {"title": "Weeks in the usual cost range, last 26", "num": AGG('count', 'spend_hist', where=[W('within_avg', '=', 1)]), "den": AGG('count', 'spend_hist')},
        {"title": "Weekly shops on the usual shop day", "num": AGG('count', 'grocery_lists', where=[W('shop', '=', SH_W), W('on_shop_day', '=', 1)]), "den": AGG('count', 'grocery_lists', where=[W('shop', '=', SH_W)])}],
    "charts": [
        CHART('Dinners planned per week, next 2 weeks', 'column', 'cook_load.week', [AGG('sum', 'cook_load', 'cook_load.dinners', label='Dinners planned')]),
        CHART('Dinners cooked per month', 'column', 'month', [AGG('count', 'meal_plan', date='meal_plan.date', where=[W('slot', '=', DINV), W('cooked', '=', YESV)], label='Dinners cooked')]),
        CHART('Planned against cooked per month', 'column', 'month', [AGG('count', 'meal_plan', date='meal_plan.date', where=[W('slot', '=', DINV)], label='Planned'),
                                                                    AGG('count', 'meal_plan', date='meal_plan.date', where=[W('slot', '=', DINV), W('cooked', '=', YESV)], label='Cooked')]),
        CHART('Dinners planned by recipe category, last 90 days', 'bar', 'recipes.category', [AGG('sum', 'recipes', 'recipes.planned_90', label='Planned in 90 days')]),
        CHART('Dinners by weekday', 'bar', 'meal_plan.weekday', [AGG('count', 'meal_plan', where=[W('slot', '=', DINV)], label='Dinners')]),
        CHART('Dinners by cook', 'bar', 'meal_plan.cook', [AGG('count', 'meal_plan', where=[W('slot', '=', DINV)], label='Dinners')]),
        CHART('Prep minutes per week, next 2 weeks', 'column', 'cook_load.week', [AGG('sum', 'cook_load', 'cook_load.prep', label='Prep minutes')]),
        CHART('Quick dinners per month', 'column', 'month', [AGG('count', 'meal_plan', date='meal_plan.date', where=[W('slot', '=', DINV), W('prep_min', '<=', '{set:quick_min}')], label='Quick dinners')]),
        CHART('Recipes by preference label', 'bar', 'recipes.pref_label', [AGG('count', 'recipes', label='Recipes')]),
        CHART('Recipes by category', 'bar', 'recipes.category', [AGG('count', 'recipes', label='Recipes')]),
        CHART('Servings per dinner by month', 'column', 'month', [AGG('avg', 'meal_plan', 'meal_plan.servings', date='meal_plan.date', where=[W('slot', '=', DINV)], label='Servings')]),
        CHART('Grocery lists per month', 'column', 'month', [AGG('count', 'grocery_lists', date='grocery_lists.date', label='Lists')]),
        CHART('Items bought per month', 'column', 'month', [AGG('sum', 'grocery_lists', 'grocery_lists.items', date='grocery_lists.date', where=[W('status', '=', tok('lstatus', 'Bought'))], label='Items')]),
        CHART('Grocery cost line per month', 'column', 'month', [AGG('sum', 'grocery_lists', 'grocery_lists.actual_cost', date='grocery_lists.date', label='Cost line')]),
        CHART('Cost line by shop', 'bar', 'grocery_lists.shop', [AGG('sum', 'grocery_lists', 'grocery_lists.actual_cost', label='Cost line')]),
        CHART('Items by section', 'bar', 'grocery_items.section', [AGG('count', 'grocery_items', label='Items')]),
        CHART('Items by shop', 'bar', 'grocery_items.shop', [AGG('count', 'grocery_items', label='Items')]),
        CHART('Weekly shop cost line per month', 'column', 'month', [AGG('sum', 'grocery_lists', 'grocery_lists.actual_cost', date='grocery_lists.date', where=[W('shop', '=', SH_W)], label='Weekly shop')]),
        CHART('Top-up shops per month', 'column', 'month', [AGG('count', 'grocery_lists', date='grocery_lists.date', where=[W('shop', '=', SH_T)], label='Top-up shops')]),
        CHART('Items on the list by section this week', 'bar', 'shop_split.section', [AGG('sum', 'shop_split', 'shop_split.items_to_buy', label='Items to buy')]),
        CHART('Weeks on a list by section, last 26 weeks', 'bar', 'staples.section', [AGG('sum', 'staples', 'staples.weeks', label='Weeks on a list')]),
        CHART('Meals by slot', 'bar', 'meal_plan.slot', [AGG('count', 'meal_plan', label='Meals')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Grocery list builder", "why": "the week plan needs minus stock on hand, rounded up to the pack sizes you typed, by section and shop", "where": "Grocery list builder"},
    {"name": "Plan needs against stock", "why": "every catalog item with what the next 7 days need, what is on hand, packs to buy and a restock under the minimum", "where": "Plan needs vs stock"},
    {"name": "Servings for the week", "why": "eaters at home each day against the servings of each dinner: cook more, right size or spare portions", "where": "Servings for the week"},
    {"name": "Week with one adult away", "why": "remove the portions for the days away and see how many fewer items the list needs", "where": "One adult away"},
    {"name": "Cook rota from the shift pattern", "why": "a suggested cook for every day from adult 2 shifts and adult 1 late days, with the days that need prep ahead", "where": "Cook rota"},
    {"name": "Shop split", "why": "one list divided across the weekly shop, top-up shop, market and online order with the trips needed", "where": "Shop split"},
    {"name": "Always runs out", "why": "items ranked by the weeks they were on a list in the last 26 complete weeks, so standing items are kept", "where": "Always runs out"},
    {"name": "This week's list against the last 4 weeks", "why": "the list and its cost line against your own last 4 complete weeks, lighter, typical or heavier", "where": "List vs last 4 weeks"},
    {"name": "Week plan check", "why": "missing dinners, the busiest prep day and stock to use soon that the plan does not use, flagged before the week starts", "where": "Week plan check"},
    {"name": "Leftover lunch planner", "why": "spare dinner portions and cooked dishes in the fridge counted as the lunches they cover", "where": "Leftover lunch planner"}]
competitors = [
    {"what": "meal-planner app with a paywall", "lacks": "charges every year, keeps your recipes in an account and has no fairness of who cooks, no pack rounding and no stock-aware list"},
    {"what": "single-sheet weekly meal plan template", "lacks": "a grid of recipe names with no servings for who is at home, no grocery list built from stock and no cook rota"},
    {"what": "grocery list app with sync and ads", "lacks": "lists what you type but cannot read your plan, round up to pack sizes or tell you what always runs out"},
    {"what": "recipe organiser with a subscription", "lacks": "stores recipes but has no shift-aware cook, no week with one adult away and no history of your own shopping weeks"}]
guide = [
    'Start here: this workbook plans the weekly meals of your home and builds the grocery list from the plan and what you already hold. Open Start and type the household name and the week start day in the yellow cells.',
    'Replace demo data: clear the yellow demo cells of Team, Recipes, Recipe ingredients, Item catalog and Stock on hand, then Meal plan, People at home, Work pattern, Grocery lists and Grocery items. Keep the lists and settings.',
    'Type your household and members first on Team. The shift pattern, late days and the people at home decide who cooks and how many portions each dinner needs.',
    'Calculated sheets (Week plan grid, Plan needs vs stock, Shopping list by shop, Staples, Weekly spend history, Recipe use history, Cook and prep load, Month at a glance): type the day numbers, item names or months once and the rest fills in.',
    'Weekly routine, every Sunday: plan the meals on Meal plan, check Stock on hand, read Plan needs vs stock for the list, check the cook on Cook and prep load and glance at the family calendar.',
    'Weekly shop routine: open the Grocery list builder, buy by section, tick the items bought on Grocery items and type the actual cost line on Grocery lists.',
    'Monthly routine: check the pantry, fridge and freezer dates in Stock on hand, read the staples that run out, pick recipes due a turn and write one change on Month at a glance.',
    'Pick the tool of the question you have: week plan check, servings, grocery list builder, shop split, one adult away, guests staying, cook rota, busy-day meal picker, prep budget, always runs out or moving the shop day.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Use-by dates and shelf days are typed from the label: typical, check the label. Intervals and fridge days are typical, check the manufacturer instructions and your local rules.',
    'Food-waste context, not a promise: studies find households waste a large share of the food they buy, and households using a shopping list waste less. Your own log shows your own figure.',
    'A single adult with no children or pets uses the same sheets: type 1 adult and no children on People at home, leave the children and carpool rows empty and use the Plan for one person tool.',
    'Renters change nothing here: where a help text says a trade, read it as a maintenance request to the landlord.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you, nothing to link, no ads and no upsell. It runs in Excel and Google Sheets with no macros, no add-ins and no accounts.',
    'What this is not: not a safety service, not a reminder app, not medical, nutrition, veterinary, legal or financial advice. Every date and total is calculated from your entries.',
]
listing = {"title": "Meal Plan and Grocery List Excel Template: Weekly Meal Planner, Pack-Rounded Shopping List, Cook Rota, Staples Tracker",
    "headline": "Plan the week of dinners and build the grocery list from what you already hold",
    "tags": ["meal plan template", "grocery list", "weekly meal planner", "family meal plan", "excel meal planner", "recipe box", "shopping list", "cook rota", "pantry stock", "household planner", "meal prep", "no subscription", "home management"],
    "description": ("Run the weekly dinners of your home in one Excel workbook. Built for a single adult, a couple or a family, owners or renters: one adult on shifts, one with late days, children, a grandparent who helps and guests who come on a Saturday. "
        "The recipe box holds your own recipes with prep minutes, servings and a plain preference label. The meal plan covers breakfast, lunch, dinner and snack for every day, People at home counts the eaters of each day and the Work pattern suggests who cooks from adult 2 shifts and adult 1 late days.\n\n"
        "The grocery list builder takes what the next 7 days need, subtracts what is in stock, rounds up to the pack sizes you typed and groups the result by section and by shop: weekly shop, top-up shop, market and online order. "
        "Staples that run out ranks the items on your lists week after week, Weekly spend history compares this week with your own last complete weeks and Recipe use history shows which recipe is due a turn.\n\n"
        f"{len(tools)} tools answer the questions of every week: is the plan complete, do the portions match who is at home, what changes when an adult is away, what do guests add, what is the quickest dinner for a late day and what runs short if the shop day moves. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the household, the grandparent, the sitter, the carpool family and guests.\n\n"
        "This is part one of the eight-part Home Management suite. A standard .xlsx workbook with no macros, no accounts and no yearly renewal, with a demo copy full of sample data and a blank copy. "
        "Dates, totals and ranks are calculated from your entries and are not advice; use-by dates and shelf days are typed from the label."),
    "features": ["Grocery list built from the plan minus stock, rounded to pack sizes", "Servings scaled to who is at home each day", "Cook rota from shifts and late days", "Several shops on one list with the trips needed",
                 "Staples that run out ranked over 26 weeks", "Week with one adult away and guests staying", f"{len(tools)} tools for the questions of every week", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "No macros, no accounts, no yearly renewal"]}
lists = lists_base + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p1', slug='home-management-meals', profession='Home Management', name='Meal Plan and Grocery List',
         tagline='Plan the week of dinners and build the grocery list from what you already hold', price_usd=29,
         colors={"primary": "#3E5C76", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Meal plan and grocery list"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ho1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']))
