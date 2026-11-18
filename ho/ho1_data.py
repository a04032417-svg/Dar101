"""Home Management suite part 1: demo rows from ho_core (full output where small, thinned where large)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho1_lists import *
import datetime as _dt

ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def D_(s): return _dt.date.fromisoformat(s)

REC = recipe_rows(); RC = {r['recipe_id']: r for r in REC}
MP = meal_plan_rows(); SH = shift_rows(); SHD = {r['date']: r for r in SH}
GL = grocery_list_rows(); GI = grocery_item_rows(); CAT = item_rows()
TOP_UP = {'milk', 'bread', 'bananas', 'yoghurt', 'lettuce'}
ONLINE = {'dog food', 'cat food', 'laundry detergent', 'dish soap', 'toilet paper', 'bin bags', 'kitchen roll'}
TEAM = {t['role']: t for t in team}


def team_d():
    return [dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=key('tgroup', t['group']), phone=t['phone'], email=t['email'], note=t['note'], start=t['start'],
                 short=first_name(t['name'])) for t in team]


def recipes_d():
    return [dict(recipe_id=r['recipe_id'], recipe=r['recipe'], category=key('rcat', r['category']), prep_min=r['prep_min'], servings=r['servings'], pref_label=key('pref', r['pref_label'])) for r in REC]


def ri_d():
    first = _dinner(iso(T0))['recipe_id']
    rows = [dict(ingredient_id=r['ingredient_id'], recipe_id=r['recipe_id'], item=r['item'], qty=r['qty'], unit=key('unit', r['unit']), section=key('section', r['section'])) for r in recipe_ingredient_rows()]
    rows.sort(key=lambda r: (r['recipe_id'] != first,))
    return rows


def items_d():
    out = []
    for r in CAT:
        shop = 'Top-up shop' if r['item'] in TOP_UP else 'Online order' if r['item'] in ONLINE else r['shop']
        out.append(dict(item_id=r['item_id'], item=r['item'], section=key('section', r['section']), unit=key('unit', r['unit']), place=key('place', r['place']), per_serving=r['per_serving'],
                        pack_size=r['pack_size'], shelf_days=r['shelf_days'], min_stock=r['min_stock'], pack_price=r['pack_price'], shop=key('shop', shop)))
    return out


def stock_d():
    out = []
    for r in stock_rows():
        out.append(nb(dict(stock_id=r['stock_id'], item=r['item'], place=key('place', r['place']), quantity=r['quantity'], unit=key('unit', r['unit']), added=r['added'], use_by=r['use_by'],
                           min_qty=r['min_qty'], section=key('section', r['section']), recipe_id=r['recipe_id']))
                  | dict(min_qty=r['min_qty']))
    # the story row first: cooked soup portions in the fridge, use-by in about 2 days, not in this week's plan
    i = next(k for k, r in enumerate(out) if r['stock_id'] == ST['food'])
    out.insert(0, out.pop(i))
    return out


def meal_plan_d():
    out = []; n_b = 0
    for i, r in enumerate(MP):
        d = D_(r['date']); cook = key('cook', r['cook'])
        if r['slot'] == 'Breakfast':
            n_b += 1
            if n_b % 4 == 0: cook = key('cook', 'Child 1')
        if r['slot'] == 'Dinner' and d.weekday() == 6 and (d.toordinal() // 7) % 5 == 0: cook = key('cook', 'Child 1')
        row = dict(plan_id=r['plan_id'], date=r['date'], weekday=key('wday', WEEKDAYS[d.weekday()]), slot=key('slot', r['slot']), recipe_id=r['recipe_id'], servings=r['servings'], cook=cook)
        if d < T0: row['cooked'] = bool(r['cooked'])
        out.append(row)
    # this week first so the demo opens on the plan being used
    out.sort(key=lambda x: (x['date'] < iso(T0) and 1 or 0, x['date'], x['plan_id']))
    j = max((k for k, x in enumerate(out) if 'cooked' in x and x['cooked'] and x['slot'] == key('slot', 'Dinner')), key=lambda k: out[k]['date'])
    out.insert(0, out.pop(j))
    return out


def _dinner(date):
    for r in MP:
        if r['date'] == date and r['slot'] == 'Dinner': return r
    return None


def people_home_d():
    out = []
    guests = {3: ('Aunt Lena', 2), 12: ('Cousin Tobi', 1)}
    away = {-9: 'Adult 2 on a work trip', -8: 'Adult 2 on a work trip', -7: 'Adult 2 on a work trip', -5: 'Child 1 on a school trip', -4: 'Child 1 on a school trip'}
    for off in range(-14, 14):
        d = T0 + _dt.timedelta(days=off); sh = SHD[iso(d)]; din = _dinner(iso(d))
        adults = 2 - (1 if sh['adult2_shift'] == 'Late' and not sh['adult1_late'] else 0)
        children = 2; gp = bool(d.weekday() == 2 and (d.day - 1) // 7 in (1, 3)); g = 0; gname = ''; gph = ''
        if off in (-9, -8, -7): adults = 1
        if off in (-5, -4): children = 1
        if off in guests: gname, g = guests[off]; gph = fake_phone(40 + off)
        note = away.get(off, '')
        if gp and not note: note = 'Grandparent helps with school pick-up'
        if off == 3: note = 'Guests for Saturday dinner'
        if off == 12: note = 'A cousin stays over'
        out.append(nb(dict(date=iso(d), adults=adults, children=children, grandparent=gp, guests=g, guest_name=gname, guest_phone=gph, away_note=note)) | dict(guests=g, grandparent=gp))
    i = next(k for k, r in enumerate(out) if r['guests'] == 2)
    out.insert(0, out.pop(i))
    return out


def shifts_d():
    out = []
    for off in range(-30, 90):
        r = SHD[iso(T0 + _dt.timedelta(days=off))]
        out.append(dict(shift_id=r['shift_id'], date=r['date'], weekday=key('wday', r['weekday']), adult1_late=bool(r['adult1_late']), adult2_shift=key('shift', r['adult2_shift']), adults_free=r['adults_free']))
    return out


def week_grid_d(): return [dict(day_no=d, slot=key('slot', s)) for d in range(7) for s in MEAL_SLOTS]
def plan_needs_d(): return [dict(item=r['item']) for r in CAT]
def shop_split_d(): return [dict(shop=key('shop', sh), section=key('section', se)) for sh in SHOPS for se in SECTIONS]
def staples_d():
    rows = [dict(item=r['item'], section=key('section', r['section'])) for r in CAT]
    rows.sort(key=lambda r: (r['item'] != 'milk',))
    return rows
def spend_hist_d(): return [dict(week_no=i) for i in range(1, 27)]
def recipe_hist_d(): return [dict(recipe=r['recipe']) for r in REC]
def cook_load_d(): return [dict(day_no=i, week=key('wk', 'Week 1' if i < 7 else 'Week 2')) for i in range(14)]
def pref_mix_d(): return [dict(label=key('pref', p)) for p in PREF_LABELS]
def month_glance_d():
    rows = [dict(month=iso(month_start(k))) for k in range(24, -1, -1)]
    rows.sort(key=lambda r: (r['month'] != iso(month_start(1)),))
    return rows


def grocery_lists_d():
    rows = [dict(list_id=r['list_id'], date=r['date'], shop=key('shop', r['shop']), status=key('lstatus', r['status']), items=r['items'], est_cost=r['est_cost'], actual_cost=r['actual_cost']) for r in GL]
    rows.sort(key=lambda r: (r['list_id'] != 'GL-206',))
    return rows


GI_FROM = ago(210)
def grocery_items_d():
    ids = {r['list_id'] for r in GL if r['date'] >= GI_FROM}
    return [dict(grocery_item_id=r['grocery_item_id'], list_id=r['list_id'], item=r['item'], qty=r['qty'], unit=key('unit', r['unit']), section=key('section', r['section']), shop=key('shop', r['shop']),
                 bought=bool(r['bought']), cost=r['cost']) for r in GI if r['list_id'] in ids]


SCEN = [('Normal week', 0, 7, 2, 2, 0, 'The usual four at home'), ('Adult 2 away on a work trip', 7, 3, 1, 2, 0, 'Adult 1 cooks every dinner'), ('Adult 1 away for two nights', 4, 2, 1, 2, 0, 'Adult 2 cooks'),
        ('Grandparent stays for the weekend', 24, 2, 2, 2, 1, 'One more at the table'), ('Guests for Saturday dinner', 3, 1, 2, 2, 2, 'Two guests, plan a bigger dish'),
        ('Hosting a holiday dinner for 12', 37, 1, 2, 2, 8, 'See the hosting plan in part 8'), ('Children stay with the grandparent', 10, 2, 2, 0, 0, 'Adults only for two nights'),
        ('Half-term week at home', 40, 5, 2, 2, 0, 'Lunches at home every day'), ('Single adult household', 0, 7, 1, 0, 0, 'One portion, same sheets'),
        ('Both adults out, sitter at home', 21, 1, 0, 2, 1, 'The sitter eats with the children'), ('Adult 2 on late shifts all week', 14, 5, 1, 2, 0, 'Plan quick or prepared dinners'),
        ('Birthday party at home', 25, 1, 2, 2, 6, 'Finger food and a cake')]
def scenarios_d(): return [dict(scenario=n, day_offset=o, days=d, adults=a, children=c, guests=g, note=t) for n, o, d, a, c, g, t in SCEN]
