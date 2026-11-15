"""Short-term rental host suite part 4: demo rows from sr_core (full generator output where totals matter, thinned rows elsewhere)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr4_lists import *
import collections

dd = to_date
R = rng('sr4')
ST = story()
UNI = {u['unit_id']: u for u in units}; UNN = {u['name']: u for u in units}
OWNP = {o['name']: o['phone'] for o in owners}
OWNER_PHONE = team[0]['phone']; COHOST_PHONE = team[1]['phone']
ACCT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
CLEANER_NAMES = [t['name'] for t in team if t['role'] == 'Cleaner']
HW = {t['name']: t['hours_week'] for t in team}
BKF = booking_rows(); BKD = {b['booking_id']: b for b in BKF}
TURN_ALL = turnover_rows()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def wd(s): return key('wday', WDAY[dd(s).weekday()])
SUP_PHONE = {s: fake_phone(40 + i) for i, s in enumerate(SUPPLIERS)}

# ---------- turnovers (about 560: every recent and upcoming turnover, older ones thinned, all redo jobs kept)
def _keep():
    out = []
    for i, t in enumerate(TURN_ALL):
        if t['status'] == 'Redo needed' or ago(21) <= t['date'] <= ahead(60) or t['date'] == ST['overbooked_date'] or i % 20 < 9: out.append(t)
    return out
TURN = _keep(); TURN_IDS = {t['turnover_id'] for t in TURN}
_nocl = [t['turnover_id'] for t in TURN if ahead(4) <= t['date'] <= ahead(25) and t['date'] != ST['overbooked_date'] and t['status'] == 'Scheduled'][:3]
def turnovers_d():
    out = []
    for t in TURN:
        u = UNI[t['unit_id']]
        out.append(nb(dict(turnover_id=t['turnover_id'], date=t['date'], unit=t['unit'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), weekday=wd(t['date']), booking_id=t['booking_id'],
                           next_check_in=t['next_check_in'], same_day=key('yn', t['same_day']), cleaner='' if t['turnover_id'] in _nocl else t['cleaner'], hours=t['hours'], pay=t['pay'], linen_sets=t['linen_sets'],
                           status=key('turnst', t['status']), score=t['score'] if t['status'] != 'Scheduled' else '')))
    return out

# ---------- bookings (about 300: bookings of recent turnovers and the next 45 days)
def bookings_d():
    ids = {t['booking_id'] for t in TURN if t['date'] >= ago(150)} | {b['booking_id'] for b in BKF if ahead(0) <= b['check_in'] <= ahead(45)}
    rows = sorted([b for b in BKF if b['booking_id'] in ids], key=lambda b: b['check_in'])
    return [nb(dict(booking_id=b['booking_id'], guest=b['guest'], unit=b['unit'], unit_type=key('utype', UNI[b['unit_id']]['unit_type']), city=key('city', b['city']), check_in=b['check_in'], check_out=b['check_out'],
                    guests=b['guests'], nights=b['nights'], status=key('bstatus', b['status']))) for b in rows]

# ---------- cleaner pay (90, full)
def cleaner_pay_d():
    out = []
    for p in cleaner_pay_rows():
        st, po = p['status'], p['paid_on']
        if p['month'] == month_start(1).isoformat() and p['cleaner'] == 'Dmitri Ivanov': st, po = 'Due', ''
        out.append(nb(dict(pay_id=p['pay_id'], month=p['month'], cleaner=p['cleaner'], turnovers=p['turnovers'], hours=p['hours'], amount=p['amount'], paid_on=po, status=key('paystat', st))))
    return out

def cleaners_d(): return [dict(name=t['name'], hours_week=t['hours_week'], hourly_rate=t['hourly_rate']) for t in team if t['role'] in ('Cleaner', 'Co-host', 'Handyperson')]

def units_d():
    return [dict(unit_id=u['unit_id'], name=u['name'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), bedrooms=u['bedrooms'], owner=u['owner'], owner_phone=OWNP[u['owner']], cleaning_fee=u['cleaning_fee']) for u in units]

# ---------- supplies
def supply_items_d():
    return [dict(item_id=s['item_id'], item=s['item'], category=key('scat', s['category']), pack=s['pack'], unit_cost=s['unit_cost'], reorder_point=s['reorder_point'], par_level=s['par_level'],
                 supplier=key('supplier', s['supplier']), supplier_phone=SUP_PHONE[s['supplier']]) for s in supply_items]
PURCH = supply_purchase_rows()
def supply_stock_d():
    use = collections.Counter()
    for p in PURCH:
        if p['date'] >= ago(180): use[p['item']] += p['qty']
    return [nb(dict(item=s['item'], category=key('scat', s['category']), on_hand=s['on_hand'], reorder_point=s['reorder_point'], par_level=s['par_level'], unit_cost=s['unit_cost'], last_bought=s['last_bought'],
                    lead_days=s['lead_days'], monthly_use=max(1, round(use[s['item']] / 6.0)))) for s in supply_stock_rows()]
def purchases_d():
    return [nb(dict(purchase_id=p['purchase_id'], date=p['date'], item=p['item'], category=key('scat', p['category']), qty=p['qty'], unit_cost=p['unit_cost'], amount=p['amount'], supplier=key('supplier', p['supplier']),
                    paid_by=key('paidby', p['paid_by']))) for p in PURCH]

# ---------- inspections (about 170)
def inspections_d():
    r = rng('sr4-insp'); out = []
    done = [t for t in TURN if t['status'] == 'Done' and t['score'] > 0 and t['date'] <= ago(0)]
    pick = [t for i, t in enumerate(done) if i % 3 == 0 or t['date'] >= ago(14)]
    pick = pick[-175:]
    for i, t in enumerate(pick):
        sc = t['score']; iss = {5: 0, 4: r.choice([0, 1]), 3: r.choice([1, 2, 3]), 2: r.choice([3, 4, 5])}[sc]
        out.append(dict(check_id='IC-%03d' % (i + 1), date=t['date'], unit=t['unit'], turnover_id=t['turnover_id'], inspector=r.choice([COHOST, COHOST, OWNER]), score=sc, issues_found=iss))
    return out

# ---------- redo jobs (about 40: every redo-needed turnover plus extra ones)
def redo_d():
    r = rng('sr4-redo'); rows = []
    for t in TURN_ALL:
        if t['status'] == 'Redo needed' and t['date'] <= ago(0): rows.append((t['date'], t['unit'], t['cleaner']))
    extra = [0, 5, 31, 58, 97, 150, 220, 305, 372, 430]
    for k in extra:
        t = [x for x in TURN_ALL if x['date'] <= ago(k) and x['status'] == 'Done'][-1]
        rows.append((ago(k), t['unit'], t['cleaner']))
    rows = sorted(set(rows))
    reasons = [key('rreason', x) for x in RREASON]
    return [dict(redo_id='RD-%02d' % (i + 1), date=d, unit=u, cleaner=c, reason=reasons[(i * 5 + int(r.random() * 3)) % len(reasons)], hours_lost=r.choice([1, 1.5, 2, 2.5, 3, 3.5]),
                 discount_given=r.choice([0, 0, 10, 15, 20, 25, 30, 40])) for i, (d, u, c) in enumerate(rows)]

# ---------- linen counts (96: 12 units x 8 months)
def linen_d():
    r = rng('sr4-linen'); out = []; n = 0
    for k in range(7, -1, -1):
        m = month_start(k).isoformat()
        for u in units:
            n += 1; base = u['bedrooms'] * 3 + 2
            damaged = r.choice([0, 0, 0, 1, 1, 2, 3]) if u['unit_id'] != ST['low_review_unit'] else r.choice([2, 3, 4])
            out.append(dict(linen_id='LC-%03d' % n, month=m, unit=u['name'], sets_in_use=base + r.randint(-1, 3), sets_washed=base * r.randint(3, 6) + r.randint(0, 6), sets_damaged=damaged,
                            sets_bought=damaged + r.choice([0, 0, 1, 2]), counted_by=CLEANER_NAMES[(n + k) % 3]))
    return out

# ---------- laundry runs (90)
def laundry_d():
    r = rng('sr4-laundry'); out = []
    per = {'Own machines': 2.4, 'Laundry service': 6.8, 'Linen hire': 4.9}
    for i in range(90):
        loc = r.choices(LLOC, [5, 3, 2])[0]; loads = r.randint(2, 7)
        out.append(dict(run_id='LR-%03d' % (i + 1), date=ago(1 + i * 4 + r.randint(0, 1)), who=CLEANER_NAMES[(i + r.randint(0, 1)) % 3], loads=loads, cost=round(loads * per[loc] * r.uniform(.9, 1.15), 2), location=key('lloc', loc)))
    return sorted(out, key=lambda x: x['date'])

# ---------- supplier orders (60)
def supplier_orders_d():
    r = rng('sr4-orders'); out = []
    for i in range(60):
        age = 6 + i * 6 + r.randint(0, 3); s = r.choices(SUPPLIERS, [4, 3, 2, 1, 1])[0]
        d = ago(age); lead = r.choice([2, 3, 4, 5, 7])
        out.append(dict(order_id='SO-%03d' % (i + 1), date=d, supplier=key('supplier', s), items=r.randint(1, 8), amount=round(r.uniform(40, 620), 2), delivery_date=(dd(d) + day(lead)).isoformat(),
                        status=key('ordst', 'Delivered'), supplier_phone=SUP_PHONE[s]))
    out.sort(key=lambda x: x['date'])
    for i, (age, lead, st) in enumerate([(1, 4, 'Ordered'), (3, 5, 'Ordered'), (5, 3, 'Ordered'), (9, 4, 'Short delivery'), (10, 3, 'Late'), (2, 2, 'Ordered')]):
        s = SUPPLIERS[(i * 2) % 5]
        out.append(dict(order_id='SO-%03d' % (61 + i), date=ago(age), supplier=key('supplier', s), items=r.randint(2, 7), amount=round(r.uniform(90, 480), 2), delivery_date=(dd(ago(age)) + day(lead)).isoformat(),
                        status=key('ordst', st), supplier_phone=SUP_PHONE[s]))
    return out

# ---------- cleaner availability (about 104, from the real turnover hours of each day)
def availability_d():
    out = []; n = 0
    offs = [-10, -7, -4] + list(range(0, 22)) + [(dd(ST['overbooked_date']) - TODAY).days]
    for o in offs:
        dte = ago(-o)
        for c in CLEANER_NAMES:
            n += 1; booked = round(sum(t['hours'] for t in TURN_ALL if t['date'] == dte and t['cleaner'] == c), 2)
            out.append(dict(avail_id='CA-%03d' % n, date=dte, cleaner=c, available_hours=max(4, round(HW[c] / 4)), booked_hours=booked))
    return out

# ---------- same-day turns (about 70)
def same_day_d():
    r = rng('sr4-sd'); sd = [t for t in TURN_ALL if t['same_day'] == 'Yes']
    pick = [t for i, t in enumerate(sd) if i % 4 == 0 or t['date'] >= ago(30)]
    pick = pick[-72:]
    return [nb(dict(sd_id='SD-%03d' % (i + 1), date=t['date'], unit=t['unit'], hours_between=r.choice([3, 3.5, 4, 4, 4.5, 4.5, 5, 5, 5.5, 6, 7]), cleaner=t['cleaner'], status=key('turnst', t['status']))) for i, t in enumerate(pick)]

# ---------- deep cleans (40)
def deep_cleans_d():
    r = rng('sr4-deep'); out = []
    ages = [380, 360, 340, 320, 300, 285, 270, 250, 230, 215, 200, 185, 170, 160, 150, 140, 130, 120, 112, 105, 98, 90, 84, 78, 70, 63, 57, 50, 44, 38, 33, 28, 22, 17, 12, 8, 4, 2, -6, -20]
    for i, a in enumerate(ages):
        u = units[(i * 5) % 12]; h = r.choice([4, 5, 5.5, 6, 7, 8, 9])
        out.append(dict(dc_id='DC-%02d' % (i + 1), unit=u['name'], date=ago(a), cleaner=CLEANER_NAMES[i % 3], hours=h, cost=round(h * 17 + r.uniform(8, 35), 2), reason=key('dreason', DREASON[(i * 3 + r.randint(0, 1)) % 5])))
    return out

# ---------- cleaning checklists by unit (48)
TASKS = [('Strip and make the beds', 'Every turnover', 9, 0), ('Clean the bathroom', 'Every turnover', 20, 4), ('Clean the kitchen and wipe appliances', 'Every turnover', 18, 3), ('Vacuum and mop all floors', 'Every turnover', 14, 4),
         ('Dust surfaces, mirrors and windows', 'Weekly', 20, 5), ('Clean the balcony or terrace', 'Weekly', 15, 0), ('Clean the oven and fridge inside', 'Monthly', 35, 0), ('Wash curtains and cushion covers', 'Quarterly', 45, 0),
         ('Test smoke alarms and replace batteries', 'Quarterly', 15, 0), ('Descale kettle, shower head and taps', 'Monthly', 25, 0), ('Restock toiletries, coffee and tea', 'Every turnover', 8, 0)]
def unit_tasks_d():
    out = []; n = 0
    for ui, u in enumerate(units):
        picks = [0, 1, 2, 3 if ui % 2 else 10]
        picks = [0, 1, 2, [3, 10, 4, 5, 6, 7, 8, 9][ui % 8]]
        for ti in picks:
            tk = TASKS[ti]; n += 1
            out.append(dict(task_id='CT-%02d' % n, unit=u['name'], task=tk[0], minutes=tk[2] + tk[3] * (u['bedrooms'] - 1) + (ui % 3) * 2 if tk[0] != 'Strip and make the beds' else 9 * u['bedrooms'] + 4, frequency=key('freq', tk[1])))
    return out

# ---------- lost and found (30)
ITEMS = ['Phone charger', 'Sunglasses', 'Scarf', 'Paperback book', 'Child\'s toy', 'Umbrella', 'Reading glasses', 'Hat', 'Headphones', 'Water bottle', 'Jacket', 'Laptop cable', 'Watch', 'Teddy bear', 'Sandals']
def lost_found_d():
    r = rng('sr4-lost'); out = []
    base = [t for t in TURN_ALL if t['date'] <= ago(0) and t['booking_id'] in BKD]
    ages = [3, 6, 11, 16, 24, 33, 41, 55, 64, 78, 92, 105, 119, 133, 150, 168, 184, 205, 222, 240, 265, 290, 310, 335, 350, 365, 388, 410, 430, 455]
    for i, a in enumerate(ages):
        d = ago(a); t = [x for x in base if x['date'] <= d][-1]; b = BKD[t['booking_id']]
        if a <= 8: st = 'Found'
        elif a <= 24 and i % 2 == 0: st = 'Contacted'
        else: st = 'Returned' if i % 5 else 'Disposed'
        ret = (dd(t['date']) + day(r.randint(3, 12))).isoformat() if st == 'Returned' else ''
        out.append(nb(dict(lf_id='LF-%02d' % (i + 1), date=t['date'], unit=t['unit'], item=ITEMS[(i * 7) % len(ITEMS)], guest=b['guest'], status=key('lfst', st), returned_on=ret)))
    return sorted(out, key=lambda x: x['date'])

# ---------- cleaner notes (50)
NOTES = ['Key box code did not work first time', 'Towels are thin and need replacing', 'Dishwasher leaks a little', 'Broken glass found under the sofa', 'Stain on the sofa cover, washed twice', 'Guest left late, turn started late',
         'Balcony door sticks', 'Smoke alarm beeps', 'Two sheet sets missing', 'Unit in great condition', 'Oven needs a deep clean', 'Light bulb out in the hall', 'Bin bags ran out', 'Coffee machine needs descaling', 'Wi-fi router unplugged']
def cleaner_notes_d():
    r = rng('sr4-notes'); out = []
    for i in range(50):
        a = 1 + i * 7 + r.randint(0, 3); u = units[(i * 7 + 3) % 12]
        out.append(dict(note_id='CN-%03d' % (i + 1), date=ago(a), cleaner=CLEANER_NAMES[(i + (i // 4)) % 3], unit=u['name'], note=NOTES[(i * 4 + r.randint(0, 2)) % len(NOTES)], follow_up=key('yn', 'Yes' if r.random() < .4 else 'No')))
    return sorted(out, key=lambda x: x['date'])

def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'], hourly_rate=t['hourly_rate'],
                    speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]

if __name__ == '__main__':
    for n in ['turnovers', 'bookings', 'cleaner_pay', 'cleaners', 'units', 'supply_items', 'supply_stock', 'purchases', 'inspections', 'redo', 'linen', 'laundry', 'supplier_orders', 'availability', 'same_day', 'deep_cleans', 'unit_tasks', 'lost_found', 'cleaner_notes', 'team']:
        print(n, len(globals()[n + '_d']()))
