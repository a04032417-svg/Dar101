"""Home Management suite part 5: demo rows from ho_core (team, inventory, repairs) and the typed rows (replacement prices, rank and key rows of the calculated sheets)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho5_lists import *

ST = story()
INV = inventory_rows(); REP = repair_rows()


def team_d():
    return [dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=t['group'], phone=t['phone'], email=t['email'], note=t['note'], start=t['start'],
                 short=first_name(t['name'])) for t in team]


def inventory_d():
    out = []
    for r in INV:
        row = dict(item_id=r['item_id'], item=r['item'], room=key('room', r['room']), category=key('icat', r['category']), purchase_date=r['purchase_date'], price=r['price'],
                   manual_place=key('kept', r['manual_place']))
        if r['serial']: row['serial'] = r['serial']
        if r['warranty_end']: row['warranty_end'] = r['warranty_end']
        if r['receipt_date']: row['receipt_date'] = r['receipt_date']
        out.append(row)
    i = next(k for k, r in enumerate(out) if r['item_id'] == ST['washer'])
    out.insert(0, out.pop(i))                      # the story row first: the washing machine, warranty ending, fault waiting
    return out


def repairs_d():
    out = []
    for r in REP:
        row = dict(repair_id=r['repair_id'], date=r['date'], room=key('room', r['room']), issue=r['issue'], trade=key('trade', r['trade']), quote=r['quote'], cost=r['cost'],
                   status=key('rstatus', r['status']), warranty_used=bool(r['warranty_used']))
        if r['fixed_on']: row['fixed_on'] = r['fixed_on']
        if r['item_id']: row['item_id'] = r['item_id']
        out.append(row)
    return out


# replacement prices typed by the household: item, price, typical years of use (a household note, not a rule)
_RP = [('Washing machine', 540, 10), ('Tumble dryer', 500, 10), ('Dishwasher', 370, 10), ('Fridge freezer', 800, 12), ('Oven', 650, 12), ('Induction hob', 420, 12), ('Extractor hood', 240, 12),
       ('Boiler or furnace', 2000, 15), ('Chest freezer', 380, 15), ('Television', 650, 8), ('Sofa', 1200, 10), ('Mattress', 800, 8), ('Lawn mower', 400, 8), ('Laptop, Adult 1', 1100, 5),
       ('Child 1 laptop for school', 520, 4), ('Microwave', 120, 8), ('Vacuum cleaner', 270, 8), ('Robot vacuum', 300, 5), ('Stand mixer', 280, 10), ('Pressure washer', 200, 6)]


def replace_d(): return [dict(item=key('ritem', a), replacement_price=b, typical_years=c) for a, b, c in _RP]
def repair_view_d(): return [dict(item=key('ritem', a)) for a, b, c in sorted(_RP, key=lambda x: x[0] != 'Dishwasher')]
def nos(n): return [dict(no=i) for i in range(1, n + 1)]
def val_room_d(): return [dict(room=key('room', r)) for r in ROOMS]
def val_cat_d(): return [dict(category=key('icat', r)) for r in ITEM_CATS]
def by_year_d(): return [dict(yk=key('pyear', y)) for y in YEARS]
def age_band_d(): return [dict(band=key('aband', b)) for b in ABANDS]
def price_band_d(): return [dict(band=key('pband', b)) for b in PBANDS]
def manuals_d(): return [dict(place=key('kept', b)) for b in KEPT]
def warr_month_d(): return [dict(mk=i, ahead=key('ahead13', AHEAD13[i])) for i in range(13)]
