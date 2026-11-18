"""Home Management suite part 2: demo rows from ho_core (thinned, adjusted where this part needs variety)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho2_lists import *
import random
from collections import defaultdict

ST = story()
T0 = TODAY
RG = random.Random(20261118)


def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def D_(s): return to_date(s)


RECIPES = recipe_rows(); ING = recipe_ingredient_rows(); ITEMS = item_rows(); STOCK = stock_rows(); LEFT = leftover_rows(); MP = meal_plan_rows()
GL = {g['list_id']: g for g in grocery_list_rows()}; GI = grocery_item_rows()
RCAT = {r['recipe_id']: r['category'] for r in RECIPES}

TOPUP = {'milk', 'bread', 'bread rolls', 'bananas', 'yoghurt', 'butter', 'cream', 'lettuce', 'cucumber', 'mushrooms', 'spinach'}
ONLINE = {'dog food', 'cat food', 'laundry detergent', 'kitchen roll', 'toilet paper', 'bin bags', 'dish soap', 'coffee', 'tea'}
SHOP_OF = {}
for _i in ITEMS:
    s = 'Top-up shop' if _i['item'] in TOPUP else 'Online order' if _i['item'] in ONLINE else _i['shop']
    SHOP_OF[_i['item']] = s


def team_d():
    return [dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=key('tgroup', t['group']), phone=t['phone'], email=t['email'], note=t['note'], start=t['start']) for t in team]


def items_d():
    out = [dict(item_id=r['item_id'], item=r['item'], section=key('section', r['section']), unit=key('unit', r['unit']), place=key('place', r['place']), per_serving=r['per_serving'],
                pack_size=r['pack_size'], shelf_days=r['shelf_days'], min_stock=r['min_stock'], pack_price=r['pack_price'], shop=key('shop', SHOP_OF[r['item']])) for r in ITEMS]
    qty = defaultdict(float)
    for r in STOCK: qty[r['item']] += r['quantity']
    seen = {b['item'] for b in bought_d() if b['bought']}
    i = next(k for k, r in enumerate(out) if r['min_stock'] > 0 and qty[r['item']] <= r['min_stock'] and r['per_serving'] > 0 and r['item'] in seen and r['item'] in SHELF_OK)
    out.insert(0, out.pop(i))
    return out


NO_DATE = {'bin bags', 'toilet paper', 'kitchen roll'}
SHELF_OK = {r['item'] for r in STOCK} - NO_DATE
COUNTED = {'ST-005': 3, 'ST-026': 10, 'ST-024': 250, 'ST-053': 14.5, 'ST-065': 1.0, 'ST-068': 2.5, 'ST-031': 3, 'ST-039': 7, 'ST-054': 1.5, 'ST-062': 3, 'ST-010': 1}


def stock_d():
    out = []
    for r in STOCK:
        added = r['added']; ub = r['use_by']
        days = (D_(ub) - T0).days
        if r['recipe_id'] == '' and r['place'] == 'Pantry' and days > 150: added = ago(RG.randint(20, 330))
        elif r['recipe_id'] == '' and r['place'] == 'Chest freezer' and days > 120: added = ago(RG.randint(35, 240))
        if r['item'] in NO_DATE: ub = ''
        shop = SHOP_OF.get(r['item'], 'Weekly shop')
        out.append(nb(dict(stock_id=r['stock_id'], item=r['item'], place=key('place', r['place']), quantity=r['quantity'], unit=key('unit', r['unit']), added=added, use_by=ub, min_qty=r['min_qty'],
                           section=key('section', r['section']), recipe_id=r['recipe_id'], shop=key('shop', shop), counted=COUNTED.get(r['stock_id'], ''))))
    i = next(k for k, r in enumerate(out) if r['stock_id'] == 'ST-005')
    out.insert(0, out.pop(i))
    return out


DISH_KIND = {'Soup': ('soup',), 'Stew or chilli': ('chilli', 'casserole'), 'Curry': ('curry',), 'Pasta dish or sauce': ('bolognese', 'Lasagne', 'sauce'), 'Burgers and balls': ('burgers', 'meatballs')}


def dish_kind(name):
    for k, ws in DISH_KIND.items():
        if any(w.lower() in name.lower() for w in ws): return k
    return 'Other'


def leftovers_d():
    rows = []
    for r in LEFT:
        e = r['eat_by']
        if r['leftover_id'] == 'LO-062': e = ago(2)
        rows.append(dict(r, eat_by=e))
    n = len(rows)
    soup = next(s for s in STOCK if s['stock_id'] == ST['food']); sauce = next(s for s in STOCK if s['stock_id'] == 'ST-015')
    rows.append(dict(leftover_id='LO-%03d' % (n + 1), date=soup['added'], dish='Chicken soup', recipe_id='RC-10', portions_made=6, portions_left=int(soup['quantity']), to_freezer='', eat_by=soup['use_by']))
    rows.append(dict(leftover_id='LO-%03d' % (n + 2), date=sauce['added'], dish='Pasta sauce jars', recipe_id='RC-59', portions_made=6, portions_left=int(sauce['quantity']), to_freezer='', eat_by=sauce['use_by']))
    rows.insert(0, rows.pop(next(k for k, r in enumerate(rows) if r['leftover_id'] == 'LO-069')))
    return [nb(dict(leftover_id=r['leftover_id'], date=r['date'], dish=r['dish'], recipe_id=r['recipe_id'], portions_made=r['portions_made'], portions_left=r['portions_left'], to_freezer=r['to_freezer'],
                    eat_by=r['eat_by'], category=key('dkind', dish_kind(r['dish'])))) | dict(portions_left=r['portions_left']) for r in rows]


def recipes_d():
    return [dict(recipe_id=r['recipe_id'], recipe=r['recipe'], category=key('rcat', r['category']), prep_min=r['prep_min'], servings=r['servings'], pref_label=key('pref', r['pref_label']),
                 ingredient_count=r['ingredient_count']) for r in RECIPES]


def ingredients_d():
    return [dict(ingredient_id=r['ingredient_id'], recipe_id=r['recipe_id'], recipe=r['recipe'], item=r['item'], qty=r['qty'], unit=key('unit', r['unit']), section=key('section', r['section'])) for r in ING]


def meal_plan_d():
    rows = [r for r in MP if -30 <= (D_(r['date']) - T0).days <= 14]
    return [nb(dict(plan_id=r['plan_id'], date=r['date'], slot=key('slot', r['slot']), recipe_id=r['recipe_id'], recipe=r['recipe'], servings=r['servings'], cook=key('person', 'Child 1' if (r['slot'] == 'Snack' or RCAT[r['recipe_id']] == 'Baking and sweets') else r['cook']), prep_min=r['prep_min'],
                    cooked=bool(r['cooked']) if r['cooked'] is not None and r['cooked'] != '' else None)) for r in rows]


def bought_d():
    rows = []
    for g in GI:
        l = GL[g['list_id']]
        rows.append(dict(grocery_item_id=g['grocery_item_id'], list_id=g['list_id'], date=l['date'], item=g['item'], qty=g['qty'], unit=key('unit', g['unit']), bought=bool(g['bought']), cost=g['cost']))
    recent = [r for r in rows if (D_(r['date']) - T0).days >= -45]
    older = [r for r in rows if (D_(r['date']) - T0).days < -45]
    step = max(1, len(older) // 70)
    sample = older[::step][-70:]
    out = sample + recent
    return out


def board_d(): return [dict(stock_id=r['stock_id']) for r in STOCK]
def ranks_d(n): return [dict(rank=i) for i in range(1, n + 1)]
def storage_d(): return [dict(section=key('section', p)) for p in SECTIONS]
def shelf_d(): return [dict(item_id=r['item_id']) for r in ITEMS]
def ready_d(): return [dict(recipe_id=r['recipe_id']) for r in RECIPES]
def calendar_d(): return [dict(day_no=i, week=key('wk', 'Week %d' % (i // 7 + 1))) for i in range(56)]


def flow_d():
    lines = defaultdict(int)
    for g in GI:
        if g['bought']: lines[D_(GL[g['list_id']]['date']).replace(day=1)] += 1
    past = [5, 4, 6, 3, 5, 7, 4, 3, 6, 5, 4, 6, 8, 5, 4, 6, 3, 5, 4, 6, 5, 7, 10]
    base = [5, 4, 6, 3, 5, 7, 4, 3, 6, 5, 4, 6, 8, 5, 4, 6, 3, 5, 4, 6, 4, 6, 5, 7, 10]
    out = []
    for i, k in enumerate(range(24, -1, -1)):
        m = month_start(k)
        out.append(dict(month=iso(m), grocery_lines=lines.get(m, 0), past_date=base[i]))
    return out


# counts the ranked tables need (computed from the same rows the sheets use)
def _counts():
    s = stock_d()
    qty = defaultdict(float)
    for r in STOCK: qty[r['item']] += r['quantity']
    below = sum(1 for i in ITEMS if i['min_stock'] > 0 and i['min_stock'] >= qty.get(i['item'], 0) - 1e-9)
    frz = sum(1 for r in STOCK if r['place'] == 'Chest freezer')
    fr = sum(1 for r in STOCK if r['place'] == 'Fridge')
    return below, frz, fr


N_BELOW, N_FRZ, N_FRIDGE = _counts()
