"""Car rental suite part 6: demo rows from cr_core (rows since 1 January where large, aggregated tables from the full generator output)."""
import sys, os, random; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr6_lists import *
import cr_core as cc
import datetime as _dt

dd = to_date
T0 = TODAY
Y0 = iso(D(T0.year, 1, 1))
TS = iso(T0)
mm = cc._mins
hm = cc._hm
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))
def rel(m): return iso(T0 + _dt.timedelta(days=m // 1440)), hm(m % 1440)
def absm(ds, t): return (dd(ds) - T0).days * 1440 + mm(t)

VCLS = {v['vehicle_id']: v['class'] for v in vehicle_rows()}
BKF = booking_rows(); BKD = {b['booking_id']: b for b in BKF}
RN = {r['renter_id']: r for r in renter_rows()}
TEAMD = {t['name']: t for t in team}
def phone_of(role): return [t for t in team if t['role'] == role][0]['phone']
OWNER_PHONE = TEAMD[OWNER]['phone']; MANAGER_PHONE = TEAMD[MANAGER]['phone']; ASSISTANT_PHONE = phone_of('Booking assistant')
BOOKKEEPER_PHONE = phone_of('Bookkeeper'); ACCOUNTANT_PHONE = phone_of('Accountant'); MECHANIC_PHONE = phone_of('Mechanic'); SUPPLIER_PHONE = phone_of('Car-wash supplier')
LIVE = ('Cancelled', 'No-show')

# ------------------------------------------------------------------ turnaround
TNF = turnaround_rows()
CLS_MEAN = {}
for cl in CLASSES:
    xs = [t['clean_minutes'] for t in TNF if VCLS[t['vehicle_id']] == cl]; CLS_MEAN[cl] = sum(xs) / len(xs)
BASE_CLEAN = {'Economy': 40, 'Compact': 45, 'Midsize SUV': 55, '7-seat Van': 70, 'Premium': 60, 'Electric': 45}


def _next_booking(b):
    c = [x for x in BKF if x['vehicle_id'] == b['vehicle_id'] and x['booking_id'] != b['booking_id'] and x['status'] not in LIVE and x['start_date'] >= b['end_date']]
    c.sort(key=lambda x: (x['start_date'], x['pickup_time']))
    return c[0] if c else None


def _tight(row, s):
    """set the next pickup so that slack = about s minutes after the cleaning ends (a pickup on a 15-minute step within opening hours)"""
    if not row.get('next_pickup'): return
    ce = absm(row['clean_date'], row['clean_end']); np_ = int(round((ce + s) / 15.0)) * 15
    if not 480 <= np_ % 1440 <= 1020 or np_ < ce - 30: return
    row['next_pickup'], row['next_pickup_time'] = rel(np_)


def turnaround_d():
    rows = []
    for t in TNF:
        if t['return_date'] < Y0: continue
        cl = VCLS[t['vehicle_id']]
        rows.append(dict(turn_id=t['turn_id'], booking_id=t['booking_id'], vehicle=t['vehicle'], cls=cl, return_date=t['return_date'], returned_time=t['returned_time'], clean_date=t['clean_date'],
                         clean_start=t['clean_start'], clean_end=t['clean_end'], cleaner=t['cleaner'], clean_minutes=t['clean_minutes'], clean_cost=t['clean_cost'], next_pickup=t['next_pickup'],
                         next_pickup_time=t['next_pickup_time']))
    PAT = [None, 30, None, -15, 45, None]
    i = 0
    for r in rows:
        if r['next_pickup'] and (dd(r['next_pickup']) - dd(r['return_date'])).days <= 2:
            s = PAT[i % len(PAT)]; i += 1
            if s is not None: _tight(r, s)
    # returns of today (cleaned or planned today)
    n = int(rows[-1]['turn_id'][3:]); k = 0
    for b in BKF:
        if b['end_date'] != TS or b['status'] not in ('Active', 'Completed'): continue
        k += 1; n += 1; cl = b['class']; ret = mm(b['return_time']); mins = int(BASE_CLEAN[cl] * (0.9 + 0.07 * k)); cs = ret + 12 + 6 * k
        nx = _next_booking(b)
        cleaner = 'Kofi Mensah'
        r = dict(turn_id='TN-%05d' % n, booking_id=b['booking_id'], vehicle=b['vehicle'], cls=cl, return_date=TS, returned_time=b['return_time'], clean_date=TS, clean_start=hm(cs), clean_end=hm(cs + mins),
                 cleaner=cleaner, clean_minutes=mins, clean_cost=round(mins / 60.0 * 16.5, 2), next_pickup=nx['start_date'] if nx else '', next_pickup_time=nx['pickup_time'] if nx else '')
        if k in (1, 3) and nx and (dd(nx['start_date']) - T0).days <= 2:
            _tight(r, {1: 30, 3: -15}[k])
        rows.append(r)
    for r in rows:
        r['dirty'] = r['clean_minutes'] >= 1.3 * CLS_MEAN[r['cls']]
    return rows


TNR = turnaround_d()
def _slack(r): return absm(r['next_pickup'], r['next_pickup_time']) - absm(r['clean_date'], r['clean_end']) if r['next_pickup'] else None
TIGHT_ID = [r['turn_id'] for r in TNR if r['return_date'] >= d_add(TS, -45) and _slack(r) is not None and 0 <= _slack(r) < 60][0]


def turnaround_rows_d():
    out = []
    for r in TNR:
        out.append(nb(dict(turn_id=r['turn_id'], booking_id=r['booking_id'], vehicle=r['vehicle'], cls=key('class', r['cls']), return_date=r['return_date'],
                           weekday=key('wday', WEEKDAYS[dd(r['return_date']).weekday()]), returned_time=r['returned_time'], clean_date=r['clean_date'], clean_start=r['clean_start'],
                           clean_end=r['clean_end'], cleaner=key('cleaner', r['cleaner']), clean_minutes=r['clean_minutes'], clean_cost=r['clean_cost'], dirty=r['dirty'],
                           next_pickup=r['next_pickup'], next_pickup_time=r['next_pickup_time'])))
    for o in out: o['class'] = o.pop('cls')
    return out


# ------------------------------------------------------------------ delivery runs
RUNF = delivery_rows()
GAP = 15
def _other(d): return 'Ravi Chandran' if d == 'Jun Park' else 'Jun Park'
def _r5(m): return int(-(-m // 5) * 5)


def runs_data():
    runs = [dict(x) for x in RUNF if x['date'] >= Y0]
    byd = {}
    for r in runs: byd.setdefault(r['date'], []).append(r)
    for d, lst in byd.items():
        if d >= TS: continue
        lst.sort(key=lambda r: (mm(r['start_time']), r['run_id']))
        last = {'Jun Park': -999, 'Ravi Chandran': -999}
        for r in lst:
            s = mm(r['start_time'])
            for drv in (r['driver'], _other(r['driver'])):
                if s >= last[drv] + GAP: r['driver'] = drv; break
            else:
                drv = min(last, key=lambda k: last[k]); s = _r5(last[drv] + GAP)
                if s + r['minutes'] < 1430: r['driver'] = drv; r['start_time'] = hm(s)
            last[r['driver']] = mm(r['start_time']) + r['minutes']
    out = []
    for r in runs:
        b = BKD[r['booking_id']]; rn = RN[b['renter_id']]; n = int(r['run_id'][3:])
        delay = [10, 15, 20, 25][n % 4] if n % 37 == 0 else 0
        out.append(dict(run_id=r['run_id'], date=r['date'], booking_id=r['booking_id'], vehicle=b['vehicle'], renter=rn['renter'], phone=rn['phone'], kind=key('runkind', r['kind']),
                        location=key('zone', r['location']), driver=key('driver', r['driver']), start_time=r['start_time'], minutes=r['minutes'], miles=r['miles'], fee_charged=r['fee_charged'],
                        driver_cost=r['driver_cost'], delay_min=delay, status=key('runstatus', r['status'])))
    return out


RUNS = runs_data()
N_TODAY_TOMORROW = len([r for r in RUNS if TS <= r['date'] <= d_add(TS, 1)])


# ------------------------------------------------------------------ shifts
SHF = shift_rows()
RATES = {'Lucia Fernandes': 17.5, 'Kofi Mensah': 16.5, 'Jun Park': 16.0, 'Ravi Chandran': 16.0, 'Sana Malik': 17.0, 'Elsa Nordin': 24.0}
ROLE_OF = {'Lucia Fernandes': 'Detailer', 'Kofi Mensah': 'Detailer', 'Jun Park': 'Delivery driver', 'Ravi Chandran': 'Delivery driver', 'Sana Malik': 'Booking assistant', 'Elsa Nordin': 'Bookkeeper'}
TASK_OF = {'Detailer': 'Cleaning and prep', 'Delivery driver': 'Delivery runs', 'Booking assistant': 'Counter and bookings', 'Bookkeeper': 'Bookkeeping'}


def planned_shifts():
    out = []
    def add(d, name, start, hours):
        h = max(0.5, round(hours * 4) / 4.0); s_ = cc._r15(start); e_ = s_ + int(h * 60) + (30 if h > 6 else 0)
        out.append(dict(date=iso(d), staff=name, start=hm(s_ % 1440), end=hm(e_ % 1440), hours=h, rate=RATES[name]))
    planned = {}
    for x in RUNF:
        if x['date'] > TS: planned.setdefault((x['date'], x['driver']), []).append(x)
    for k in range(1, 35):
        d = T0 + _dt.timedelta(days=k); ds = iso(d)
        rets = [b for b in BKF if b['end_date'] == ds and b['status'] not in LIVE]; pk = [b for b in BKF if b['start_date'] == ds and b['status'] not in LIVE]
        H = sum(BASE_CLEAN[b['class']] * 1.05 for b in rets) / 60.0 + 0.2 * len(pk) + (0.5 if rets else 0)
        if k == 10: H = 1.0
        if H > 0:
            if k != 10: H += 0.5
            if d.weekday() < 5:
                a = min(H, 8.0); add(d, 'Lucia Fernandes', 480, a)
                if H - a >= .5: add(d, 'Kofi Mensah', 600, H - a)
            else:
                a = min(H, 8.0); add(d, 'Kofi Mensah', 540, a)
                if H - a >= .5: add(d, 'Lucia Fernandes', 600, H - a)
        for nm in DRIVERS:
            rr = planned.get((ds, nm))
            if rr and k != 2: add(d, nm, min(mm(x['start_time']) for x in rr) - 15, max(2.0, sum(x['minutes'] + 5 for x in rr) / 60.0 + .5))
        if k != 6 and (d.weekday() >= 5 or (d.weekday() == 4 and d.month in (6, 7, 8, 12))): add(d, 'Sana Malik', 540, 4.0 if d.weekday() < 5 else 6.0)
        if d.weekday() in (2, 4): add(d, 'Elsa Nordin', 570, 4.0)
    return out


def shifts_d():
    rows = [dict(date=x['date'], staff=x['staff'], start=x['start'], end=x['end'], hours=x['hours'], rate=x['rate']) for x in SHF if x['date'] >= Y0]
    rows += planned_shifts()
    rows.sort(key=lambda r: (r['date'], r['staff']))
    out = []
    for i, r in enumerate(rows):
        d = dd(r['date']); role = ROLE_OF[r['staff']]
        out.append(dict(shift_id='SH-%05d' % (i + 1), date=r['date'], week=iso(cc.week_start(d)), month=iso(D(d.year, d.month, 1)), weekday=key('wday', WEEKDAYS[d.weekday()]),
                        staff=key('shiftstaff', r['staff']), role=key('payrole', role), task=key('task', TASK_OF[role]), start=r['start'], end=r['end'], hours=r['hours'], rate=r['rate']))
    return out


def pay_d():
    lo = iso(month_start(16)); out = []
    for p in pay_rows():
        if p['month'] < lo: continue
        out.append(dict(pay_id=p['pay_id'], month=p['month'], staff=key('staff', p['staff']), role=key('payrole', p['role']), pay_type=key('paytype', p['pay_type']), hours=p['hours'],
                        gross=p['gross'], employer_cost=p['employer_cost'], status=key('paystatus', p['status'])))
    return out


def team_d():
    return [dict(staff_id=t['staff_id'], name=t['name'], role=t['role'], team=t['team'], pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'],
                 monthly_salary=int(t['monthly_salary']), hourly_rate=t['hourly_rate'], area=t['area']) for t in team]


def bookings_d():
    lo = d_add(TS, -35); out = []
    for b in BKF:
        if b['end_date'] >= lo or b['start_date'] >= lo:
            out.append(dict(booking_id=b['booking_id'], start_date=b['start_date'], end_date=b['end_date'], vehicle=b['vehicle'], cls=key('class', b['class']), pickup_time=b['pickup_time'],
                            return_time=b['return_time'], pickup_location=key('location', b['pickup_location']), status=key('bstatus', b['status'])))
    for o in out: o['class'] = o.pop('cls')
    return out


def zones_d():
    return [dict(location=key('location', l['location']), fee_leg=l['fee_leg'], run_minutes=l['run_minutes']) for l in locations]


def dates_range(a, b): return [iso(T0 + _dt.timedelta(days=k)) for k in range(a, b + 1)]


def task_log_d():
    r = random.Random('p6-tasks'); out = []; n = 0
    who = {'Owner-operator': ['Nadia Haddad'], 'Manager': ['Tomas Kowalski'], 'Detailer': ['Lucia Fernandes', 'Kofi Mensah'], 'Delivery driver': ['Jun Park', 'Ravi Chandran'],
           'Booking assistant': ['Sana Malik'], 'Bookkeeper': ['Elsa Nordin']}
    for k in range(-24, 1):
        d = T0 + _dt.timedelta(days=k)
        for role in PAY_ROLES:
            task = TASKS[role][(k + PAY_ROLES.index(role)) % 3]
            p = {'Delivery driver': 0.78, 'Detailer': 0.9, 'Manager': 0.88}.get(role, 0.95)
            if task == 'Refuel or recharge before return': p = 0.6
            done = r.random() < p
            n += 1
            out.append(dict(log_id='TK-%04d' % n, date=iso(d), role=key('payrole', role), task=key('taskitem', task), staff=who[role][(k + n) % len(who[role])], done=done))
    # make sure the last 7 days show a few missed tasks for the review
    miss = {'Delivery driver': 2, 'Detailer': 1, 'Manager': 1}
    cnt = {}
    for o in out:
        if o['date'] >= d_add(TS, -6) and not o['done']: cnt[o['role']] = cnt.get(o['role'], 0) + 1
    for role, want in miss.items():
        have = cnt.get(key('payrole', role), 0)
        for o in reversed(out):
            if have >= want: break
            if o['role'] == key('payrole', role) and o['date'] >= d_add(TS, -6) and o['done']: o['done'] = False; have += 1
    for o in out:
        if o['date'] >= d_add(TS, -6) and o['role'] in (key('payrole', 'Owner-operator'), key('payrole', 'Bookkeeper')) and not o['done']: o['done'] = True
    return out


def hours_month_d():
    out = []
    for k in range(23, -1, -1):
        m = month_start(k); ms = iso(m)
        sh = [s for s in SHF if s['month'] == ms]
        rent = len([b for b in BKF if b['start_date'][:7] == ms[:7] and b['start_date'] <= TS and b['status'] not in LIVE])
        out.append(dict(month=ms, hours=round(sum(s['hours'] for s in sh), 2), pay=round(sum(s['cost'] for s in sh), 2), rentals=rent))
    return out


PRODUCTS = [('Interior cleaner', 6.4), ('Glass cleaner', 4.2), ('Microfibre cloths', 1.3), ('Vacuum bags', 2.9), ('Air freshener tags', 0.8), ('Tyre and trim shine', 7.6), ('Floor mat shampoo', 9.8),
            ('Disposable seat covers', 0.5)]


def supplies_d():
    ex = [e for e in expense_rows() if e['category'] == 'Cleaning supplies']
    r = random.Random('p6-supplies'); out = []; n = 0
    for i, e in enumerate(ex):
        parts = [(PRODUCTS[(i * 3) % 8], 1.0)] if i % 2 == 0 else [(PRODUCTS[(i * 3) % 8], 0.6), (PRODUCTS[(i * 3 + 1) % 8], 0.4)]
        for (name, base), share in parts:
            u = round(base * r.uniform(0.92, 1.12), 2); q = max(2, int(round(e['amount'] * share / u)))
            n += 1
            out.append(dict(order_id='SO-%03d' % n, date=e['date'], month=e['month'], product=name, quantity=q, unit_cost=u))
    return out


def clean_load_d():
    return [dict(date=d, cleaner=key('cleaner', c)) for d in dates_range(-29, 0) for c in CLEANERS]


def runs_week_d():
    w0 = cc.week_start(T0) - _dt.timedelta(days=7 * 51); agg = {}
    for x in RUNF:
        if x['date'] > TS or x['status'] != 'Done': continue
        w = iso(cc.week_start(dd(x['date'])))
        a = agg.setdefault(w, [0, 0, 0.0, 0.0]); a[0] += 1; a[1] += x['minutes']; a[2] += x['driver_cost']; a[3] += x['fee_charged']
    out = []
    for k in range(52):
        w = iso(w0 + _dt.timedelta(days=7 * k)); a = agg.get(w, [0, 0, 0.0, 0.0])
        out.append(dict(week=w, runs=a[0], minutes=a[1], driver_cost=round(a[2], 2), fees_charged=round(a[3], 2)))
    return out
