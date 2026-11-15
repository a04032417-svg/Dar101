"""Short-term rental host suite part 5: demo rows (full generator output for aggregated tables, thinned rows elsewhere)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr5_lists import *
import collections

dd = to_date
BKF = booking_rows()
UNI = {u['unit_id']: u for u in units}; UNN = {u['name']: u for u in units}
OWNP = {o['name']: o['phone'] for o in owners}
TEAMN = {t['name']: t for t in team}
OWNER_PHONE = team[0]['phone']; COHOST_PHONE = team[1]['phone']
ACCT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
ST = story()
MT = maintenance_rows()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def ed(d, n): return add_months(d, n)
def d_iso(d): return d.isoformat()
def pick(r, seq): return seq[int(r.random() * len(seq)) % len(seq)]
BYU = collections.defaultdict(list)
for b in BKF:
    if b['status'] != 'Cancelled': BYU[b['unit_id']].append(b)

def guest_at(unit_id, date):
    """guest of the booking in the unit on that date, else the latest earlier guest"""
    best = None
    for b in BYU[unit_id]:
        if b['check_in'] <= date <= b['check_out']: return b
        if b['check_out'] < date and (best is None or b['check_out'] > best['check_out']): best = b
    return best or BYU[unit_id][0]


def units_d():
    return [nb(dict(unit_id=u['unit_id'], name=u['name'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), bedrooms=u['bedrooms'], owner=u['owner'], owner_phone=OWNP[u['owner']],
                    since=u['since'])) for u in units]


def tickets_d():
    out = []
    for m in MT:
        u = UNI[m['unit_id']]; g = guest_at(m['unit_id'], m['reported_on'])
        out.append(nb(dict(ticket_id=m['ticket_id'], reported_on=m['reported_on'], unit=m['unit'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), kind=key('tkind', m['kind']),
                           priority=key('prio', m['priority']), source=key('tsrc', m['source']), handyperson=m['handyperson'], status=key('tkst', m['status']), done_on=m['done_on'], parts_cost=m['parts_cost'],
                           labour_cost=m['labour_cost'], guest_impact=key('yn', m['guest_impact']), guest=g['guest'], guest_phone=fake_phone(int(g['booking_id'][3:])))))
    return out


def claims_d():
    out = []
    for c in damage_rows():
        out.append(nb(dict(claim_id=c['claim_id'], reported_on=c['reported_on'], booking_id=c['booking_id'], unit=c['unit'], guest=c['guest'], guest_phone=fake_phone(int(c['booking_id'][3:])),
                           channel=key('chan', c['channel']), damage=c['damage'], claimed_amount=c['claimed_amount'], deposit_held=c['deposit_held'], repair_cost=c['repair_cost'], status=key('dmst', c['status']),
                           paid_amount=c['paid_amount'], paid_on=c['paid_on'])))
    return out


def bookings_d():
    recent = [b for b in BKF if b['check_in'] >= ago(40)]
    old = [b for b in BKF if b['check_in'] < ago(40)]
    step = max(1, round(len(old) / 120.0)); keep = old[::step]
    rows = sorted(keep + recent, key=lambda b: b['check_in'])
    return [nb(dict(booking_id=b['booking_id'], unit=b['unit'], guest=b['guest'], channel=key('chan', b['channel']), check_in=b['check_in'], check_out=b['check_out'], status=key('bstatus', b['status'])))
            for b in rows]


SAFETY_ITEMS = [('Smoke alarm', 6), ('Carbon monoxide alarm', 6), ('Gas appliance check', 12), ('Fire extinguisher', 12), ('Door lock and entry code', 3), ('Electrical sockets and fuse box', 12)]
def safety_d():
    r = rng('sr5-safety'); rows = []
    who = ['Ravi Menon', 'Tariq Haddad', 'Kai Andersson', 'Ravi Menon', 'Tariq Haddad']
    pairs_ = [(u, it) for u in units for it in SAFETY_ITEMS]
    over = set(r.sample(range(len(pairs_)), 5)); soon = set(r.sample([i for i in range(len(pairs_)) if i not in over], 6))
    for i, (u, (item, mo)) in enumerate(pairs_):
        span = mo * 30
        if i in over: age = span + r.randint(5, 45)
        elif i in soon: age = span - r.randint(1, 6)
        else: age = r.randint(3, span - 10)
        last = dd(ago(age)); prev = ed(last, -mo) - day(r.randint(0, 12))
        for dte, final in ((prev, False), (last, True)):
            res = 'Pass' if r.random() < .84 else ('Fixed on the spot' if r.random() < .75 else 'Needs repair')
            if final and i in over: res = 'Pass'
            rows.append(dict(date=d_iso(dte), unit=u['name'], item=item, result=key('sres', res), next_check=d_iso(ed(dte, mo)), done_by=who[(i + int(final)) % len(who)]))
    rows.sort(key=lambda x: x['date'])
    return [dict(safety_id='SC-%03d' % i, **x) for i, x in enumerate(rows, 1)]


SERVICES = [('Boiler and water heater service', 12, 120), ('Air conditioning filter clean', 6, 85), ('Extractor fan and chimney clean', 12, 95), ('Mattress and sofa deep clean', 6, 110), ('Gutter and roof check', 12, 140)]
def services_d():
    r = rng('sr5-svc'); rows = []; k = 0
    over = set(r.sample(range(60), 4)); soon = set(r.sample([i for i in range(60) if i not in over], 6))
    for u in units:
        for s, mo, c in SERVICES:
            frac = r.uniform(1.04, 1.25) if k in over else (1 - r.randint(3, 27) / (mo * 30.4) if k in soon else r.uniform(.08, .8))
            last = dd(ago(int(frac * mo * 30.4)))
            cost = round(c * (0.85 + .12 * u['bedrooms']) * r.uniform(.92, 1.08))
            rows.append(dict(unit=u['name'], service=s, every_months=mo, last_done=d_iso(last), cost=cost)); k += 1
    rows.sort(key=lambda x: x['last_done'])
    return [dict(service_id='SV-%03d' % i, **x) for i, x in enumerate(rows, 1)]


APPL = [('Washing machine', 430, [24, 24, 36]), ('Dishwasher', 480, [24, 36]), ('Refrigerator', 540, [24, 36, 60]), ('Oven and hob', 390, [24, 24]), ('Water heater', 360, [24, 60]),
        ('Air conditioner', 780, [36, 60]), ('Television', 450, [24, 24]), ('Coffee machine', 95, [12, 24])]
def appliances_d():
    r = rng('sr5-app'); rows = []; soon = set(r.sample(range(96), 3))
    k = 0
    for u in units:
        for n, c, wm in APPL:
            mo = pick(r, wm)
            if k in soon: left = r.randint(15, 52); wu = dd(ahead(left)); bought = ed(wu, -mo)
            else:
                age = r.uniform(25, 365 * 7.2); bought = dd(ago(int(age)))
                wu = ed(bought, mo)
                if 0 <= (wu - TODAY).days <= 75: wu = wu + day(r.randint(90, 200)) if (wu - TODAY).days > 8 else wu - day(95)
            rows.append(dict(unit=u['name'], appliance=n, bought_on=d_iso(bought), warranty_until=d_iso(wu), cost=round(c * r.uniform(.85, 1.2))))
            k += 1
    r.shuffle(rows)
    return [dict(app_id='AP-%03d' % i, **x) for i, x in enumerate(rows, 1)]


WORKS = ['Replace the shower screen seal', 'Repair the balcony door lock', 'Fit a new water heater valve', 'Repaint the living room walls', 'Replace the bedroom blinds', 'Repair the kitchen tap and sink', 'Service the heat pump',
         'Replace two window handles', 'Fix the leaking roof edge', 'Rewire the hallway lights', 'Replace the dishwasher pump', 'Re-grout the bathroom floor', 'Repair the garden fence', 'Replace the sofa bed frame']
def quotes_d():
    r = rng('sr5-quotes'); rows = []
    for i in range(42):
        d = dd(ago(int(r.uniform(4, 420)))) if i >= 5 else dd(ago(r.randint(2, 16)))
        u = pick(r, units); sup = pick(r, ['Ravi Menon', 'Tariq Haddad', 'Ravi Menon', 'Tariq Haddad', 'Rafael Costa'])
        amt = round(r.choice([85, 140, 190, 260, 340, 480, 620, 780, 950, 1250, 1650]) * r.uniform(.9, 1.12))
        if i < 5: dec, don = 'Waiting', ''
        else:
            dec = 'Approved' if r.random() < .78 else 'Declined'; don = d_iso(d + day(r.randint(1, 6)))
        rows.append(dict(date=d_iso(d), unit=u['name'], work=pick(r, WORKS), supplier=sup, amount=amt, decision=key('qdec', dec), decision_on=don))
    rows.sort(key=lambda x: x['date'])
    return [nb(dict(quote_id='QT-%03d' % i, **x)) for i, x in enumerate(rows, 1)]


PARTS = {'Plumbing': ['Tap cartridge', 'Shower hose set', 'Toilet fill valve', 'Pipe seal kit'], 'Electrical': ['Light fitting', 'Socket and cover', 'Circuit breaker'], 'Appliance': ['Dishwasher pump', 'Washing machine belt', 'Oven heating element'],
         'Heating and cooling': ['Thermostat', 'Air filter set', 'Heat pump fan'], 'Furniture': ['Bed slats', 'Chair set', 'Curtain rail'], 'Locks and keys': ['Door lock body', 'Smart lock battery pack', 'Key blanks'],
         'Garden and exterior': ['Fence panels', 'Outdoor light', 'Gate hinge set'], 'Pest control': ['Door brush seal', 'Mesh screen'], 'Wi-Fi and TV': ['Router', 'TV remote and mount']}
SUPP = {'Plumbing': 'Plumbing supply shop', 'Electrical': 'Electrical supply shop', 'Appliance': 'Appliance parts shop', 'Heating and cooling': 'Heating supply shop', 'Furniture': 'Furniture warehouse',
        'Locks and keys': 'Lock supply shop', 'Garden and exterior': 'Garden centre', 'Pest control': 'Hardware wholesaler', 'Wi-Fi and TV': 'Electronics wholesaler'}
def parts_d():
    r = rng('sr5-parts'); wait = [m for m in MT if m['status'] == 'Waiting parts']
    cand = [m for m in MT if m['parts_cost'] > 0 and m['status'] == 'Done' and m['reported_on'] >= ago(400)]
    rec = [m for m in cand if m['reported_on'] >= ago(60)]; oth = [m for m in cand if m['reported_on'] < ago(60)]
    pickd = wait + rec[:12] + r.sample(oth, min(len(oth), 70 - len(wait) - min(12, len(rec)) - 3))
    rows = []
    for j, m in enumerate(pickd):
        qty = r.choice([1, 1, 1, 2, 2, 3]); price = round(m['parts_cost'] / qty, 2) if m['parts_cost'] > 0 else round(r.uniform(35, 210), 2)
        d = dd(m['reported_on']) + day(r.randint(0, 1))
        if m['status'] == 'Waiting parts':
            st = 'Ordered' if j % 2 else 'Shipped'; dl = d + day(r.randint(6, 12))
        else:
            st = 'Delivered'; dl = d + day(r.randint(1, 6))
            if r.random() < .05: st = 'Cancelled'
        rows.append(dict(date=d_iso(d), ticket_id=m['ticket_id'], part=pick(r, PARTS[m['kind']]), qty=qty, unit_price=price, supplier=SUPP[m['kind']], delivery_date=d_iso(dl), status=key('pstat', st)))
    for m in r.sample(oth, 3):   # three cancelled orders
        d = dd(m['reported_on'])
        rows.append(dict(date=d_iso(d), ticket_id=m['ticket_id'], part=pick(r, PARTS[m['kind']]), qty=1, unit_price=round(r.uniform(40, 160), 2), supplier=SUPP[m['kind']], delivery_date=d_iso(d + day(5)), status=key('pstat', 'Cancelled')))
    rows.sort(key=lambda x: x['date'])
    return [dict(part_id='PT-%03d' % i, **x) for i, x in enumerate(rows, 1)]


def inspections_d():
    r = rng('sr5-insp'); rows = []
    ins = ['Kai Andersson', 'Noor Castellanos', 'Lucia Fernandes', 'Amara Diallo', 'Yuki Sato', 'Dmitri Ivanov']
    for i in range(84):
        age = int(r.uniform(1, 430)) if i >= 6 else r.randint(1, 24)
        u = pick(r, units) if i >= 6 else units[8]
        base = 86 + r.gauss(0, 7)
        if u['unit_id'] == ST['low_review_unit'] and age < 120: base -= 14
        if u['unit_id'] == ST['unit_losing']: base -= 5
        sc = int(max(55, min(100, round(base)))); iss = max(0, int(round((100 - sc) / 5 + r.uniform(-1, 1))))
        rows.append(dict(date=ago(age), unit=u['name'], inspector=pick(r, ins), score=sc, issues=iss))
    rows.sort(key=lambda x: x['date'])
    return [dict(insp_id='IN-%03d' % i, **x) for i, x in enumerate(rows, 1)]


IKIND = [('Noise complaint from a neighbour', 'Spoke to the guest and agreed quiet hours'), ('Guest locked out', 'Sent the entry code again and checked the lock battery'), ('Water leak under the sink', 'Closed the valve and sent a handyperson'),
         ('Broken item reported at check-in', 'Replaced the item before the next stay'), ('Power cut in the building', 'Gave the guest a torch and checked the fuse box'), ('More guests than booked', 'Asked the guest to pay the extra guest fee'),
         ('Smoke alarm went off', 'Checked the kitchen and changed the battery'), ('Guest hurt on a loose step', 'Offered first aid and repaired the step the same day')]
def incidents_d():
    r = rng('sr5-inc'); rows = []
    for i in range(32):
        age = int(r.uniform(2, 420)) if i >= 4 else r.randint(1, 20)
        u = pick(r, units); g = guest_at(u['unit_id'], ago(age)); k, a = pick(r, IKIND)
        closed = '' if i < 3 else ago(max(0, age - r.randint(0, 3)))
        rows.append(nb(dict(date=ago(age), unit=u['name'], kind=k, guest=g['guest'], action=a, closed_on=closed)))
    rows.sort(key=lambda x: x['date'])
    return [dict(inc_id='IC-%02d' % i, **x) for i, x in enumerate(rows, 1)]


def handy_d():
    r = rng('sr5-handy'); wk0 = week_start(TODAY)
    weeks = [wk0 - day(7 * k) for k in range(0, 6)] + sorted(set(wk0 - day(7 * k) for k in r.sample(range(8, 54), 6)))
    out = []
    for w in sorted(weeks):
        for name, cap, mean in (('Ravi Menon', 24, 19), ('Tariq Haddad', 18, 13)):
            h = max(4, min(cap + 6, round(r.gauss(mean, 3.2))))
            out.append(dict(week=d_iso(w), handyperson=name, hours=h, jobs=max(1, round(h / 2.4 + r.uniform(-1, 1)))))
    return [dict(hw_id='HW-%03d' % i, **x) for i, x in enumerate(out, 1)]


def cost_unit_d():
    um = {(x['unit_id'], x['month']): x for x in unit_month_rows()}
    agg = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for m in MT:
        a = agg[(m['unit_id'], m['reported_on'][:7] + '-01')]; a[0] += 1; a[1] += m['parts_cost']; a[2] += m['labour_cost']
    out = []
    for ms in months14():
        for u in units:
            x = um.get((u['unit_id'], d_iso(ms)))
            if not x: continue
            a = agg.get((u['unit_id'], d_iso(ms)), [0, 0, 0])
            out.append(dict(month=d_iso(ms), unit=u['name'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), tickets=a[0], parts_cost=round(a[1], 2), labour_cost=round(a[2], 2), booked_nights=x['booked_nights']))
    return [dict(cu_id='CU-%04d' % i, **x) for i, x in enumerate(out, 1)]


def warranty_d():
    r = rng('sr5-wc'); ap = appliances_d(); rows = []
    act = [a for a in ap if dd(a['warranty_until']) > dd(a['bought_on']) + day(60) and dd(a['bought_on']) < TODAY - day(60)]
    inw = [a for a in act if dd(a['warranty_until']) > TODAY and dd(a['bought_on']) < TODAY - day(25)]
    old = [a for a in act if a not in inw]
    for a in r.sample(inw, 3):
        rows.append(dict(appliance=a['app_id'], claimed_on=ago(r.randint(3, 20)), amount=round(a['cost'] * r.uniform(.3, .7)), result=key('wres', 'Waiting')))
    for a in r.sample(old, 17):
        b = dd(a['bought_on']); e = min(TODAY - day(5), dd(a['warranty_until']))
        c = b + day(int(r.uniform(.15, .92) * max(1, (e - b).days)))
        rows.append(dict(appliance=a['app_id'], claimed_on=d_iso(c), amount=round(a['cost'] * r.uniform(.25, .8)), result=key('wres', 'Accepted' if r.random() < .72 else 'Rejected')))
    rows.sort(key=lambda x: x['claimed_on'])
    return [dict(wc_id='WC-%02d' % i, **x) for i, x in enumerate(rows, 1)]


DREAS = ['Heavy cleaning after a party', 'Broken glass and a stained rug', 'Missing towels and a remote', 'Smoke smell in the bedroom', 'Damaged chair']
def deposits_d():
    r = rng('sr5-dep'); dr = [b for b in BKF if b['channel'] == 'Direct' and b['status'] != 'Cancelled']
    past = [b for b in dr if b['check_out'] <= ago(8)]; rec = [b for b in dr if ago(8) < b['check_out'] <= ago(0)]; fut = [b for b in dr if b['check_out'] > ago(0)]
    over = [b for b in past if b['check_out'] >= ago(30)][:2]
    ch = sorted(r.sample([b for b in past if b not in over], 46) + over + rec[:6] + fut[:6], key=lambda b: b['check_out'])
    rows = []
    for b in ch:
        u = UNI[b['unit_id']]; amt = 100 + 50 * u['bedrooms']; co = dd(b['check_out'])
        kept = ""; reason = ''; rel = ''
        if b in over or b['check_out'] > ago(8): rel = ''
        else:
            rel = d_iso(co + day(r.randint(1, 5)))
            if r.random() < .3: kept = round(amt * r.uniform(.25, .8)); reason = pick(r, DREAS)
        rows.append(nb(dict(booking_id=b['booking_id'], unit=b['unit'], guest=b['guest'], guest_phone=fake_phone(int(b['booking_id'][3:])), check_out=b['check_out'], amount=amt, released_on=rel, kept_amount=kept, reason=reason)))
    rows[0]['kept_amount'] = 60; rows[0]['reason'] = DREAS[0]
    return [dict(dep_id='DP-%03d' % i, **x) for i, x in enumerate(rows, 1)]


RCAUSE = {'Plumbing': ('Old pipes and worn seals', 'Replace the worn seals and pipe sections'), 'Electrical': ('Overloaded circuit and old fittings', 'Add a new circuit and change the fittings'),
          'Appliance': ('Heavy use between short stays', 'Service each appliance twice a year'), 'Heating and cooling': ('Filters not cleaned', 'Clean the filters every quarter'),
          'Furniture': ('Wear from frequent check-ins', 'Replace with stronger furniture'), 'Locks and keys': ('Battery and keypad wear', 'Change batteries each quarter'),
          'Garden and exterior': ('Weather and no yearly check', 'Do a yearly exterior check'), 'Pest control': ('Gaps near doors and bins', 'Seal the gaps and add a pest contract'),
          'Wi-Fi and TV': ('Old router and weak signal', 'Replace the router and add a repeater')}
def recurring_d():
    cnt = collections.Counter((m['unit'], m['kind']) for m in MT if m['reported_on'] > ago(365))
    r = rng('sr5-rec'); items = sorted(cnt.items(), key=lambda x: (-x[1], r.random()))[:36]
    return [dict(rec_id='RI-%02d' % i, unit=u, kind=key('tkind', k), root_cause=RCAUSE[k][0], fix=RCAUSE[k][1]) for i, ((u, k), c) in enumerate(items, 1)]


CAPX = [('Replace the water heater', 'Fewer repairs and lower energy cost'), ('New mattresses for both bedrooms', 'Better review comfort score'), ('Repaint the living room and hall', 'Fresher look in photos'), ('Fit a smart lock', 'No key handover, fewer lockouts'),
        ('Replace the sofa', 'Worn after many stays'), ('Install a heat pump', 'Lower energy cost and comfort in summer'), ('Double glazing for the bedroom', 'Fewer noise complaints'), ('New balcony railing', 'Safety and fewer repairs'),
        ('New washing machine and dryer', 'Repeated appliance tickets'), ('LED lighting throughout', 'Lower electricity cost'), ('Kitchen refit', 'Higher nightly rate'), ('Outdoor furniture set', 'Higher rate in peak season'),
        ('New bathroom fittings', 'Repeated plumbing tickets'), ('Blackout curtains', 'Better sleep reviews'), ('Mesh Wi-Fi system', 'Fewer Wi-Fi complaints')]
def capex_d():
    r = rng('sr5-capex'); rows = []
    for i in range(24):
        pm = ed(month_start(0), r.randint(-8, 14)) if i >= 3 else ed(month_start(0), r.randint(0, 2))
        it, why = CAPX[i % len(CAPX)]; u = pick(r, units)
        cost = round(r.choice([260, 420, 650, 900, 1400, 2200, 3200, 4800, 6500]) * r.uniform(.9, 1.1))
        sav = round(cost * r.uniform(.12, .7)) if i % 6 else 0
        cur = month_start(0)
        st = 'Done' if pm < cur else ('Approved' if pm == cur else r.choice(['Planned', 'Planned', 'Idea']))
        rows.append(dict(unit=u['name'], item=it, planned_month=d_iso(pm), cost=cost, saving_per_year=sav, reason=why, status=key('cxst', st)))
    rows.sort(key=lambda x: x['planned_month'])
    return [dict(cx_id='CX-%02d' % i, **x) for i, x in enumerate(rows, 1)]


def locks_d():
    r = rng('sr5-lock'); rows = []
    ev = ['Code changed after check-out'] * 8 + ['Code changed on request'] * 3 + ['Battery changed'] * 4 + ['Key copied'] * 2 + ['Lock repaired'] * 2 + ['Lock replaced']
    who = ['Kai Andersson', 'Noor Castellanos', 'Rafael Costa', 'Ravi Menon', 'Lucia Fernandes']
    for i in range(62):
        age = int(r.uniform(1, 430)) if i >= 4 else r.randint(1, 14)
        e = pick(r, ev); cc = 'Yes' if e.startswith('Code') or r.random() < .5 else 'No'
        if e in ('Key copied', 'Battery changed') and r.random() < .6: cc = 'No'
        rows.append(dict(date=ago(age), unit=pick(r, units)['name'], event=key('levent', e), code_changed=key('yn', cc), who=pick(r, who)))
    for age, cc in ((6, 'Yes'), (95, 'Yes'), (210, 'Yes'), (3, 'No')):   # lost keys, one without a new code
        rows.append(dict(date=ago(age), unit=pick(r, units)['name'], event=key('levent', 'Key lost'), code_changed=key('yn', cc), who='Kai Andersson'))
    rows.sort(key=lambda x: x['date'])
    return [dict(lock_id='LK-%03d' % i, **x) for i, x in enumerate(rows, 1)]


AREAS = ['Kitchen', 'Bathroom', 'Balcony or garden', 'Roof or attic', 'Entrance', 'Bedrooms', 'Facade and gutters']
ACT = {'Nothing found': 'No action needed', 'Insects': 'Treated the area and set traps', 'Rodent signs': 'Sealed the gap and called the pest contractor', 'Damp or mould': 'Cleaned, dried and checked the source',
       'Crack or damage': 'Booked a repair and photographed the damage', 'Loose rail or tile': 'Fixed the same day', 'Blocked gutter': 'Cleared the gutter'}
def pest_d():
    r = rng('sr5-pest'); rows = []
    fl = ['Nothing found'] * 22 + ['Insects'] * 4 + ['Rodent signs'] * 2 + ['Damp or mould'] * 4 + ['Crack or damage'] * 3 + ['Loose rail or tile'] * 3 + ['Blocked gutter'] * 3
    for i in range(42):
        age = int(r.uniform(1, 420)) if i >= 3 else r.randint(1, 12)
        f = pick(r, fl) if i >= 3 else ['Insects', 'Damp or mould', 'Blocked gutter'][i]
        rows.append(dict(date=ago(age), unit=pick(r, units)['name'], area=pick(r, AREAS), finding=key('pfind', f), action=ACT[f]))
    rows.sort(key=lambda x: x['date'])
    return [dict(pe_id='PE-%02d' % i, **x) for i, x in enumerate(rows, 1)]


def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=t['role'], phone=t['phone'], email=t['email'], hours_week=t['hours_week'], hourly_rate=t['hourly_rate'], speciality=t['speciality'],
                    country=t['country'], start=t['start'])) for t in team]

if __name__ == '__main__':
    for n in ['units', 'tickets', 'claims', 'bookings', 'safety', 'services', 'appliances', 'quotes', 'parts', 'inspections', 'incidents', 'handy', 'cost_unit', 'warranty', 'deposits', 'recurring', 'capex', 'locks', 'pest', 'team']:
        print(n, len(globals()[n + '_d']()))
