"""Car rental suite part 7: demo rows from cr_core (full generator output for the aggregated tables, thinned samples for row-level tables)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr7_lists import *
import datetime as _dt
import collections

dd = to_date
ST = story()
T0 = TODAY
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}

TEAM = {t['name']: t for t in team}
OWNER_PHONE = TEAM[OWNER]['phone']; MANAGER_PHONE = TEAM[MANAGER]['phone']
def _ph(role): return [t for t in team if t['role'] == role][0]['phone']
ACCOUNTANT_PHONE = _ph('Accountant'); BROKER_PHONE = _ph('Insurance broker'); MECHANIC_PHONE = _ph('Mechanic')
BOOKKEEPER_PHONE = _ph('Bookkeeper'); LENDER_PHONE = _ph('Lender')
HOTEL_PHONE = fake_phone(41); MARKET_PHONE = fake_phone(42)
CLS = {c['class']: c for c in classes}
VEH = vehicle_rows(); VEHD = {v['vehicle_id']: v for v in VEH}
VM = vehicle_month_rows()
BKF = booking_rows()
ACTIVE = [v for v in VEH if v['status'] != 'Sold']
OK_STATUS = ('Booked', 'Active', 'Completed')
MONTHS = sorted({r['month'] for r in VM})
SEASON_OF_MONTH = {1: 'Off-peak', 2: 'Off-peak', 3: 'Shoulder', 4: 'Shoulder', 5: 'Shoulder', 6: 'Peak', 7: 'Peak', 8: 'Peak', 9: 'Shoulder', 10: 'Shoulder', 11: 'Off-peak', 12: 'Holiday'}
def season_of(m): return key('season', SEASON_OF_MONTH[dd(m).month])
def mstart(d): return iso(_dt.date(dd(d).year, dd(d).month, 1))
def ms_of(k): return iso(month_start(k))


def vmonths_d():
    return [dict(row_id=r['row_id'], vehicle_id=r['vehicle_id'], vehicle=r['vehicle'], **{'class': key('class', r['class'])}, month=r['month'], available_days=r['available_days'],
                 rented_days=r['rented_days'], revenue=r['revenue'], channel_fees=r['channel_fees'], financing=r['financing'], insurance=r['insurance'], maintenance=r['maintenance'],
                 cleaning=r['cleaning'], fuel_charge=r['fuel_charge'], depreciation=r['depreciation']) for r in VM]


def vehicles_d():
    return [dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], **{'class': key('class', v['class'])}, status=key('vstatus', v['status']), purchase_date=v['purchase_date'],
                 purchase_price=v['purchase_price'], financed=v['financed'], monthly_payment=v['monthly_payment'], odometer=v['odometer']) for v in VEH]


def classes_d(): return [dict(**{'class': key('class', c['class'])}, daily_rate=c['daily_rate'], deposit=c['deposit']) for c in classes]


def vehicle_names(): return [v['vehicle'] for v in ACTIVE]


def _low_first(rows):
    return sorted(rows, key=lambda r: 0 if r['vehicle'] == ST['low_vehicle_name'] else 1)
def util_vehicle_d(): return _low_first([dict(vehicle=v['vehicle']) for v in ACTIVE])
def breakeven_d(): return util_vehicle_d()
def costday_d(): return _low_first([dict(vehicle=v['vehicle'], **{'class': key('class', v['class'])}) for v in ACTIVE])
def verdict_d(): return util_vehicle_d()
def vprofit_d(): return _low_first([dict(vehicle=v['vehicle'], status=key('vstatus', v['status'])) for v in VEH])


def util_class_d():
    seen = sorted({(r['class'], r['month']) for r in VM}, key=lambda x: (CLASSES.index(x[0]), x[1]))
    return [dict(row_id='UC-%03d' % (i + 1), **{'class': key('class', c)}, month=m, season=season_of(m)) for i, (c, m) in enumerate(seen)]


def rates_d():
    out = []; n = 0
    for c in classes:
        ly = c['last_year_daily'] / c['daily_rate']
        for plan, rate, days in (('Daily', c['daily_rate'], 1), ('Weekly', c['weekly_rate'], 7), ('Monthly', c['monthly_rate'], 30)):
            n += 1
            out.append(dict(rate_id='RT-%02d' % n, **{'class': key('class', c['class'])}, plan=key('plan', plan), rate=rate, last_year_rate=round(rate * ly), days=days, deposit=c['deposit']))
    return out


def _booking_list():
    return [b for b in BKF if b['status'] in OK_STATUS]


def adr_class_d():
    agg = collections.OrderedDict()
    for b in _booking_list():
        m = mstart(b['start_date']); k = (b['class'], m)
        a = agg.setdefault(k, [0, 0.0, 0.0])
        c = CLS[b['class']]; base = c['last_year_daily'] if dd(b['start_date']).year < T0.year else c['daily_rate']
        mult = [s['multiplier'] for s in seasons if s['season'] == b['season']][0]
        a[0] += b['days']; a[1] += b['rental_amount']; a[2] += b['days'] * base * mult
    out = []
    for (c, m), a in sorted(agg.items(), key=lambda x: (CLASSES.index(x[0][0]), x[0][1])):
        if m < MONTHS[0] or m > MONTHS[-1]: continue
        out.append(dict(**{'class': key('class', c)}, month=m, season=season_of(m), rented_days=a[0], rental_revenue=round(a[1], 2), list_revenue=round(a[2], 2)))
    return out


def adr_ly_d():
    out = []
    for k in range(11, -1, -1):
        for c in CLASSES: out.append(dict(row_id='AL-%03d' % (len(out) + 1), **{'class': key('class', c)}, month=ms_of(k)))
    return out


def _covered():
    cov = collections.defaultdict(set)
    for b in BKF:
        if b['status'] in ('Cancelled', 'No-show'): continue
        s = dd(b['start_date'])
        for i in range(b['days']): cov[b['vehicle_id']].add(s + _dt.timedelta(days=i))
    for m in maintenance_rows():
        s = dd(m['date'])
        for i in range(max(1, int(m['days_off_road'] or 0))): cov[m['vehicle_id']].add(s + _dt.timedelta(days=i))
    return cov


def idle_runs_d():
    cov = _covered(); lo = T0 - _dt.timedelta(days=365); hi = T0 + _dt.timedelta(days=21); runs = []
    for v in VEH:
        if v['status'] == 'In workshop': continue
        a = max(lo, dd(v['purchase_date'])); z = min(hi, dd(v['sold_date']) if v['sold_date'] else hi)
        d = a; start = None
        while d <= z + _dt.timedelta(days=1):
            free = d <= z and d not in cov[v['vehicle_id']]
            if free and start is None: start = d
            if not free and start is not None:
                if (d - start).days >= 3: runs.append((v, start, d - _dt.timedelta(days=1)))
                start = None
            d += _dt.timedelta(days=1)
    runs.sort(key=lambda r: r[1])
    recent = [r for r in runs if r[1] >= T0 - _dt.timedelta(days=20)]
    older = [r for r in runs if r[1] < T0 - _dt.timedelta(days=20)]
    step = max(1, len(older) // 60)
    pick = older[::step][:62] + recent
    pick.sort(key=lambda r: r[1])
    return [dict(run_id='IR-%03d' % (i + 1), vehicle=v['vehicle'], **{'class': key('class', v['class'])}, from_date=iso(s), to_date=iso(e)) for i, (v, s, e) in enumerate(pick)]


def bookings_d():
    ren = {r['renter_id']: r for r in renter_rows()}
    out = []
    for b in booking_rows(n=600):
        r = ren.get(b['renter_id'], {})
        out.append(dict(booking_id=b['booking_id'], vehicle_id=b['vehicle_id'], renter=b['renter'], phone=r.get('phone', fake_phone(int(b['renter_id'][3:]))), **{'class': key('class', b['class'])},
                        start_date=b['start_date'], end_date=b['end_date'], days=b['days'], start_day=key('wday', WEEKDAYS[dd(b['start_date']).weekday()]), channel=key('channel', b['channel']),
                        plan=key('plan', b['plan']), season=key('season', b['season']), day_rate=b['day_rate'], total=b['total'], delivery_fee=b['delivery_fee'], net_amount=b['net_amount'],
                        status=key('bstatus', b['status'])))
    return out


def _monday(d): return d - _dt.timedelta(days=d.weekday())


def _booked_days(cls, w0, w1, weekend=False, status=OK_STATUS):
    n = 0
    for b in BKF:
        if b['class'] != cls or b['status'] not in status: continue
        s = dd(b['start_date'])
        for i in range(b['days']):
            d = s + _dt.timedelta(days=i)
            if w0 <= d <= w1 and (not weekend or d.weekday() >= 5): n += 1
    return n


def trend_factor():
    a = b = 0
    w1 = _monday(T0) - _dt.timedelta(days=1); w0 = w1 - _dt.timedelta(days=55)
    for c in CLASSES:
        a += _booked_days(c, w0, w1, status=('Completed', 'Active')); b += _booked_days(c, w0 - _dt.timedelta(days=364), w1 - _dt.timedelta(days=364), status=('Completed', 'Active'))
    return round(a / b, 2)


def forecast_d():
    out = []; n_cls = {c: sum(1 for v in ACTIVE if v['class'] == c) for c in CLASSES}
    for k in range(12):
        w = _monday(T0) + _dt.timedelta(days=7 * k); e = w + _dt.timedelta(days=6); ly = (w - _dt.timedelta(days=364), e - _dt.timedelta(days=364))
        for c in CLASSES:
            out.append(dict(row_id='FW-%03d' % (len(out) + 1), week=iso(w), **{'class': key('class', c)}, booked_days=_booked_days(c, w, e), fleet_days=7 * n_cls[c], last_year_days=_booked_days(c, *ly, status=('Completed', 'Active')),
                            weekend_booked=_booked_days(c, w, e, weekend=True)))
    return out


def trend_d(): return [dict(month=m) for m in MONTHS]
def chprofit_d(): return [dict(channel=key('channel', c)) for c in CHANNELS]
def bands_d(): return [dict(**{'class': key('class', c)}, band=key('band', b)) for c in CLASSES for b in BANDS]
def seasons_d():
    mult = {s['season']: s['multiplier'] for s in seasons}
    import calendar as _c
    return [dict(months=_c.month_name[m], season=season_of('2026-%02d-01' % m), multiplier=mult[SEASON_OF_MONTH[m]]) for m in range(1, 13)]
def revpac_d(): return [dict(**{'class': key('class', c['class'])}, target=round(c['daily_rate'] * 0.62)) for c in classes]
