"""Car rental suite part 2: demo rows from cr_core (the bookings of the last 13 months, the 33 vehicles, calendars for the next 14 days, logs of extensions, swaps and cancellations)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr2_lists import *
import datetime as _dt

dd = to_date
ST = story()
T = TODAY
def td(n): return T + _dt.timedelta(days=n)
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))
def nb(x): return {k: v for k, v in x.items() if v not in ('', None)}
def tm(s): return int(s[:2]) * 60 + int(s[3:5])
HOLD = ('Booked', 'Active', 'Completed')
WIN = month_start(12)                       # the first month of the monthly tables
TEAM = {t['name']: t for t in team}
PH = {t['role']: t['phone'] for t in team}
OWNER_PHONE = TEAM[OWNER]['phone']; MANAGER_PHONE = TEAM[MANAGER]['phone']
DRIVER_PHONE = TEAM['Jun Park']['phone']; DETAILER_PHONE = TEAM['Lucia Fernandes']['phone']
MECHANIC_PHONE = PH['Mechanic']; BOOKKEEPER_PHONE = TEAM['Elsa Nordin']['phone']
CORP_PHONE = fake_phone(901); HOTEL_PHONE = fake_phone(902); MKT_PHONE = fake_phone(903)

VEH = vehicle_rows(); VID = {x['vehicle_id']: x for x in VEH}; VNAME = {x['vehicle']: x for x in VEH}
ACTIVE = [x for x in VEH if x['status'] != 'Sold']
BKA = [b for b in booking_rows() if b['end_date'] >= iso(WIN)]
RPH = {r['renter_id']: r['phone'] for r in renter_rows()}
BKD = {b['booking_id']: b for b in BKA}
HB = [b for b in BKA if b['status'] in HOLD]
HV = {}
for b in HB: HV.setdefault(b['vehicle'], []).append(b)
for l in HV.values(): l.sort(key=lambda x: (x['start_date'], x['pickup_time']))
def covers(b, day): return b['start_date'] <= day <= b['end_date']


def bookings_d():
    out = []
    for b in BKA:
        out.append(dict(booking_id=b['booking_id'], created_on=b['created_on'], start_date=b['start_date'], end_date=b['end_date'], pickup_time=b['pickup_time'], return_time=b['return_time'],
                        vehicle_id=b['vehicle_id'], vehicle=b['vehicle'], class_=key('class', b['class']), renter=b['renter'], phone=RPH.get(b['renter_id'], ''), channel=key('channel', b['channel']),
                        plan=key('plan', b['plan']), season=key('season', b['season']), total=b['total'], pickup_location=key('location', b['pickup_location']),
                        start_day=key('wday', WEEKDAYS[dd(b['start_date']).weekday()]), end_day=key('wday', WEEKDAYS[dd(b['end_date']).weekday()]), status=key('bstatus', b['status'])))
    for o in out: o['class'] = o.pop('class_')
    return out


def vehicles_d():
    return [nb(dict(vehicle_id=x['vehicle_id'], fleet_no=int(x['vehicle_id'][3:]), vehicle=x['vehicle'], plate=x['plate'], **{'class': key('class', x['class'])}, status=key('vstatus', x['status']),
                    purchase_date=x['purchase_date'], sold_date=x['sold_date'], odometer=x['odometer'])) for x in VEH]


def classes_d(): return [dict(**{'class': key('class', x['class'])}, buffer_min=x['buffer_min'], seats=x['seats']) for x in classes]
def channels_d(): return [dict(channel=key('channel', x['channel']), fee_pct=x['fee_pct'], payout_days=x['payout_days']) for x in channels]


# ---------------------------------------------------------------- service blocks: the last 12 months from the service rows plus the planned ones
def _free_window(name, start_from, days, latest=40):
    for k in range(start_from, latest):
        s = td(k); e = td(k + days - 1)
        if all(not (b['start_date'] <= iso(e + _dt.timedelta(days=1)) and b['end_date'] >= iso(s - _dt.timedelta(days=1))) for b in HV.get(name, []) if b['end_date'] >= iso(T)): return s
    return None


def _blocks():
    rows = [dict(vehicle_id=m['vehicle_id'], vehicle=m['vehicle'], date=m['date'], kind=m['kind'], days_off_road=m['days_off_road']) for m in maintenance_rows()
            if m['date'] >= ago(365) and m['days_off_road'] > 0]
    DOWN = {k: SVT[k]['downtime_days'] for k in SVT}
    plan = [(ST['service_vehicle'], 'Major service', 2, 4), ('VH-001', 'Minor service', 1, 2), ('VH-009', 'Tyre set', 1, 3), ('VH-012', 'Brake service', 2, 5), ('VH-016', 'Inspection', 1, 6),
            ('VH-019', 'Minor service', 1, 8), ('VH-021', 'Battery check', 1, 9), ('VH-022', 'Major service', 2, 10), ('VH-025', 'Inspection', 1, 12), ('VH-027', 'Tyre set', 1, 14),
            ('VH-030', 'Minor service', 1, 17), ('VH-031', 'Brake service', 2, 21)]
    for vid, kind, days, start in plan:
        nm = VID[vid]['vehicle']; s = _free_window(nm, start, days)
        if s: rows.append(dict(vehicle_id=vid, vehicle=nm, date=iso(s), kind=kind, days_off_road=days))
    rows.sort(key=lambda r: (r['date'], r['vehicle_id']))
    for i, r in enumerate(rows, 1): r['block_id'] = 'SB-%03d' % i
    return rows
BLK = _blocks()
def blocks_d(): return [dict(block_id=r['block_id'], vehicle_id=r['vehicle_id'], vehicle=r['vehicle'], date=r['date'], kind=key('mkind', r['kind']), days_off_road=r['days_off_road']) for r in BLK]
def block_end(r): return d_add(r['date'], r['days_off_road'] - 1)
def in_service(name, day): return any(r['vehicle'] == name and r['date'] <= day <= block_end(r) for r in BLK)


def day_status(name, day):
    if in_service(name, day): return 'Service'
    for b in HV.get(name, []):
        if covers(b, day): return 'Rented' if b['status'] == 'Active' else 'Reserved'
    return 'Free'


def cal_vehicle_d():
    out = []; i = 0
    for x in ACTIVE:
        for k in range(14):
            i += 1; out.append(dict(row_id='CV-%04d' % i, vehicle=x['vehicle'], date=iso(td(k))))
    return out


def cal_class_d():
    out = []; i = 0
    for cl in CLASSES:
        for k in range(14):
            i += 1; out.append(dict(row_id='CC-%03d' % i, class_=key('class', cl), date=iso(td(k))))
    for o in out: o['class'] = o.pop('class_')
    return out


def next_free_veh_d(): return [dict(vehicle_id=x['vehicle_id']) for x in ACTIVE]
def next_free_class_d(): return [{'class': key('class', cl)} for cl in CLASSES]


def overlap_d():
    sel = [b for b in HB if b['end_date'] >= iso(T) and b['start_date'] <= ahead(14)]
    return [dict(booking_id=b['booking_id']) for b in sorted(sel, key=lambda x: (x['start_date'], x['booking_id']))]


# ---------------------------------------------------------------- pickups and returns (next 7 days) with a few late returns on the phone
def pr_d():
    out = []; i = 0
    for k in range(7):
        day = iso(td(k))
        for kind, col in (('Pickup', 'start_date'), ('Return', 'end_date')):
            for b in sorted([x for x in HB if x[col] == day], key=lambda x: x['pickup_time' if kind == 'Pickup' else 'return_time']):
                i += 1; out.append(dict(slot_id='PR-%03d' % i, date=day, kind=key('pkind', kind), booking_id=b['booking_id']))
    # late returns reported by the renter: returns whose car has another booking within 2 days
    lates = (45, 90, 150, 30, 240, 75)
    li = 0
    for o in out:
        if o['kind'] == key('pkind', 'Return') and li < len(lates):
            b = BKD[o['booking_id']]; nxt = [x for x in HV[b['vehicle']] if x['start_date'] > b['end_date']]
            if nxt and (dd(nxt[0]['start_date']) - dd(b['end_date'])).days <= 2: o['late_minutes'] = lates[li]; li += 1
    return out


# ---------------------------------------------------------------- extensions (16), swaps (12), cancellations
def ext_d():
    R = rng('cr2-ext'); out = []
    ext = [b for b in BKA if b['extended'] and b['status'] == 'Completed' and b['days'] >= 4]
    by_m = {}
    for b in ext: by_m.setdefault(b['start_date'][:7], []).append(b)
    rows = []
    for m in sorted(by_m)[-10:]:
        b = by_m[m][-1]; k = R.choice((1, 2, 3)); rows.append((b, k, 'Approved'))
    recent = [b for b in BKA if b['extended'] and b['status'] == 'Completed' and b['days'] >= 2 and b['start_date'] >= ago(21)]
    for b in recent[-2:]:
        if all(r[0] is not b for r in rows): rows.append((b, 1, 'Approved'))
    # declined: the request runs past the next booking of the car
    n = 0
    for b in reversed(HB):
        nxt = [x for x in HV[b['vehicle']] if x['start_date'] > b['end_date']]
        if b['status'] == 'Completed' and nxt and 2 <= (dd(nxt[0]['start_date']) - dd(b['end_date'])).days <= 4 and b['start_date'] < ago(30) and all(r[0] is not b for r in rows):
            rows.append((b, (dd(nxt[0]['start_date']) - dd(b['end_date'])).days + 1, 'Declined')); n += 1
            if n == 2: break
    # open requests on cars that are out now or booked
    opened = 0
    for b in HB:
        if b['status'] in ('Active', 'Booked') and b['end_date'] >= iso(T) and opened < 4:
            nxt = [x for x in HV[b['vehicle']] if x['start_date'] > b['end_date']]
            gap = (dd(nxt[0]['start_date']) - dd(b['end_date'])).days if nxt else 9
            if opened == 0 and gap >= 3: rows.append((b, 2, 'Open')); opened += 1
            elif opened == 1 and 1 <= gap <= 2: rows.append((b, gap + 1, 'Open')); opened += 1
            elif opened == 2 and gap >= 3: rows.append((b, 3, 'Open')); opened += 1
            elif opened == 3 and gap == 1: rows.append((b, 2, 'Open')); opened += 1
    for b, k, dec in rows:
        if dec in ('Approved', 'Declined'):
            new_end = b['end_date'] if dec == 'Approved' else d_add(b['end_date'], k); cur = d_add(new_end, -k) if dec == 'Approved' else b['end_date']
            req_on = min(d_add(cur, -1), iso(T)); req_on = max(req_on, b['start_date'])
        else:
            cur = b['end_date']; new_end = d_add(cur, k); req_on = max(b['start_date'], ago(1)) if b['start_date'] <= iso(T) else iso(T)
        out.append(dict(booking_id=b['booking_id'], requested_on=req_on, current_end=cur, requested_end=new_end, decision=key('extdec', dec)))
    out.sort(key=lambda x: x['requested_on'])
    for i, o in enumerate(out, 1): o['ext_id'] = 'EX-%03d' % i
    return out


def swaps_d():
    R = rng('cr2-swap'); out = []
    pool = [b for b in HB if b['status'] in ('Completed', 'Active') and b['days'] >= 3]
    by_m = {}
    for b in pool: by_m.setdefault(b['start_date'][:7], []).append(b)
    picks = []
    for m in sorted(by_m)[-10:]: picks.append(by_m[m][len(by_m[m]) // 2])
    act = [b for b in pool if b['status'] == 'Active' and b['days'] >= 5][:2]
    for b in act:
        if b not in picks: picks.append(b)
    why = ['Service due', 'Damage', 'Breakdown', 'Renter request', 'Overlap fix']
    for i, b in enumerate(picks):
        same = [x for x in ACTIVE if x['class'] == b['class'] and x['vehicle'] != b['vehicle']]
        other = [x for x in ACTIVE if x['class'] != b['class'] and x['class'] in ('Compact', 'Midsize SUV', 'Premium', 'Economy')]
        to = (R.choice(other) if i in (3, 8) else R.choice(same)) if same or other else None
        sd = d_add(b['start_date'], max(1, min(b['days'] - 1, 1 + i % 3)))
        if b['status'] == 'Active': sd = max(b['start_date'], ago(1 + i % 2)) if i % 2 else iso(T)
        out.append(dict(booking_id=b['booking_id'], from_vehicle=b['vehicle'], to_vehicle=to['vehicle'], swap_date=sd, reason=key('swapwhy', why[i % 5])))
    out.sort(key=lambda x: x['swap_date'])
    for i, o in enumerate(out, 1): o['swap_id'] = 'SW-%03d' % i
    return out


def cancel_d():
    R = rng('cr2-cx'); out = []
    for b in BKA:
        if b['status'] not in ('Cancelled', 'No-show'): continue
        lead = max(0, (dd(b['start_date']) - dd(b['created_on'])).days)
        if b['status'] == 'No-show': on = b['start_date']; notice = 0
        else:
            notice = R.choice([0, 1, 1, 2, 3, 4, 6, 9, 14, 21, 30]); notice = min(notice, lead)
            on = d_add(b['start_date'], -notice)
            if on > iso(T): on = iso(T)
        fee = 0 if (b['status'] == 'Cancelled' and notice >= 2) else {'Economy': 20, 'Compact': 25, 'Midsize SUV': 30, '7-seat Van': 35, 'Premium': 45, 'Electric': 35}[b['class']]
        if b['channel'] in ('Marketplace A', 'Marketplace B') and b['status'] == 'Cancelled': fee = 0 if notice >= 1 else 15
        out.append(dict(booking_id=b['booking_id'], cancelled_on=on, channel=key('channel', b['channel']), kind=key('cxkind', b['status']), fee_charged=fee))
    return out


# ---------------------------------------------------------------- the monthly tables
MONTHS = [month_start(k) for k in range(12, -1, -1)]
def channel_month_d():
    out = []; i = 0
    for m in MONTHS:
        for ch in CHANNELS:
            i += 1; out.append(dict(row_id='CM-%03d' % i, month=iso(m), channel=key('channel', ch)))
    return out


def class_month_d():
    out = []; i = 0
    for m in MONTHS:
        for cl in CLASSES:
            i += 1; out.append({'row_id': 'KM-%03d' % i, 'month': iso(m), 'class': key('class', cl)})
    return out


def weekend_d():
    w0 = week_start(T); return [dict(week=iso(w0 + _dt.timedelta(days=7 * k))) for k in range(-5, 7)]


def daily_d():
    out = []
    for k in range(-30, 15):
        day = td(k); out.append(dict(date=iso(day), weekday=key('wday', WEEKDAYS[day.weekday()])))
    return out


def idle_d():
    out = []; i = 0
    for x in ACTIVE:
        st = [day_status(x['vehicle'], iso(td(k))) for k in range(14)]
        k = 0
        while k < 14:
            if st[k] == 'Free':
                j = k
                while j + 1 < 14 and st[j + 1] == 'Free': j += 1
                i += 1; out.append(dict(gap_id='IG-%03d' % i, vehicle=x['vehicle'], gap_from=iso(td(k)), class_=key('class', x['class'])))
                k = j + 1
            else: k += 1
    for o in out: o['class'] = o.pop('class_')
    return out


def bands_d(): return [dict(band=key('band', b)) for b in BANDS]
