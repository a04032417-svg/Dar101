"""Car rental suite part 5: demo rows from cr_core (full generator output where small, thinned where large, aggregated tables built from the full output)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr5_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))

TEAM = {t['role']: t for t in team}
PH = {r: t['phone'] for r, t in TEAM.items()}          # one phone per role (the contacts and the staff)
CLS = {c['class']: c for c in classes}
VEH = vehicle_rows(); VD = {v['vehicle_id']: v for v in VEH}; VN = {v['vehicle']: v for v in VEH}
NONSOLD = [v for v in VEH if v['status'] != 'Sold']

# miles driven and utilisation of the last 12 months, per vehicle (from the check-out rows and the vehicle months)
_HO = handover_rows()
MI12 = {}
for h in _HO:
    if h['out_date'] >= ago(365) and h['miles_driven'] != '': MI12[h['vehicle_id']] = MI12.get(h['vehicle_id'], 0) + h['miles_driven']
_vm = [x for x in vehicle_month_rows() if dd(x['month']) >= month_start(12) and dd(x['month']) < month_start(0)]
UT12 = {}
for x in _vm:
    a = UT12.setdefault(x['vehicle_id'], [0, 0]); a[0] += x['rented_days']; a[1] += x['available_days']
UT12 = {k: round(a[0] / a[1], 2) if a[1] else 0.6 for k, a in UT12.items()}

# ------------------------------------------------------------------ service log (all rows), one towing row moved so that one car has two breakdowns in 12 months
LOGF = maintenance_rows()
_tow = [m for m in LOGF if m['kind'] == 'Towing' and m['date'] >= ago(365)]
_mv = [m for m in _tow if m['vehicle_id'] == 'VH-021'][0]
_target = VD['VH-017']
_before = [m for m in LOGF if m['vehicle_id'] == 'VH-017' and m['date'] <= _mv['date']]
_od0 = (_before[-1]['odometer'] if _before else _target['odometer_at_purchase'])
_mv['vehicle_id'] = 'VH-017'; _mv['vehicle'] = _target['vehicle']
_mv['odometer'] = min(_target['odometer'], _od0 + 600)
# on time = a service done within 10% of the interval in miles since the previous service of that car
_ONT = {}
_last = {}
for m in LOGF:
    if m['kind'] in ('Minor service', 'Major service'):
        v = VD[m['vehicle_id']]; p = _last.get(m['vehicle_id'])
        _ONT[m['maint_id']] = True if p is None else (m['odometer'] - p) <= 1.10 * v['interval_miles']
        _last[m['vehicle_id']] = m['odometer']
LOG = LOGF
LOGD = {m['maint_id']: m for m in LOG}

# ------------------------------------------------------------------ renewals (a few past ones were paid a few days late)
RENF = [dict(r) for r in renewal_rows()]
_done = [r for r in RENF if r['status'] == 'Done']
for i, r in enumerate(_done):
    if i % 24 == 11: r['renewed_on'] = d_add(r['due_date'], 1 + (i % 5))
REN = RENF

# ------------------------------------------------------------------ bookings in the next 14 days
_RN = {r['renter_id']: r for r in renter_rows()}
BK = [b for b in booking_rows() if b['status'] in ('Booked', 'Active') and b['end_date'] >= ago(0) and b['start_date'] <= ahead(14)]
BK.sort(key=lambda b: (b['start_date'], b['booking_id']))


def vehicles_d():
    out = []
    for v in VEH:
        out.append(nb(dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], plate=v['plate'], class_=key('class', v['class']), fuel=key('fuel', v['fuel']), year=key('vyear', str(v['year'])),
                           purchase_date=v['purchase_date'], purchase_price=v['purchase_price'], financed=bool(v['financed']), monthly_payment=v['monthly_payment'], odometer=v['odometer'],
                           status=key('vstatus', v['status']), sold_date=v['sold_date'], interval_miles=v['interval_miles'], interval_months=v['interval_months'],
                           last_service_date=v['last_service_date'], last_service_odometer=v['last_service_odometer'], insurance_year=v['insurance_year'], resale_estimate=v['resale_estimate'],
                           miles_12m=int(MI12.get(v['vehicle_id'], 0)), util_12m=UT12.get(v['vehicle_id'], 0.0))))
        out[-1]['class'] = out[-1].pop('class_')
    return out


def service_log_d():
    return [nb(dict(maint_id=m['maint_id'], vehicle_id=m['vehicle_id'], vehicle=m['vehicle'], **{'class': key('class', VD[m['vehicle_id']]['class'])}, date=m['date'], month=m['month'],
                    kind=key('mkind', m['kind']), group=key('mgroup', GROUP_OF[m['kind']]), odometer=m['odometer'], cost=m['cost'], days_off_road=m['days_off_road'],
                    vendor=key('vendor', m['vendor']), on_time=_ONT.get(m['maint_id'], True))) for m in LOG]


def service_types_d():
    return [dict(service_type=key('mkind', s['service_type']), interval_miles=s['interval_miles'], interval_months=s['interval_months']) for s in service_types]


def service_due_d(): return [dict(vehicle=v['vehicle']) for v in NONSOLD]


def renewals_d():
    return [nb(dict(renewal_id=r['renewal_id'], vehicle=r['vehicle'], kind=key('renewal', r['kind']), due_date=r['due_date'], renewed_on=r['renewed_on'], cost=r['cost'],
                    status=key('rstatus2', r['status']))) for r in REN]


def renew_cost_ahead_d():
    return [dict(month=iso(add_months(month_start(0), i)), slot=key('mahead', 'Month %d' % (i + 1))) for i in range(12)]


_SLOT_VEH = [ST['service_vehicle'], 'VH-025', 'VH-004', 'VH-009', 'VH-023', 'VH-012', 'VH-019', 'VH-013']
_SLOT_OFF = [1, 3, 6, 9, 12]
_DROP = ['08:00', '08:30', '09:00', '09:30', '10:00', '08:15', '13:00', '13:30']


def slots_d():
    out, n = [], 0
    for i, vid in enumerate(_SLOT_VEH):
        v = VD[vid]
        kind = {'VH-025': 'Major service', 'VH-012': 'Major service', 'VH-004': 'Tyre set', 'VH-013': 'Tyre set', 'VH-023': 'Brake service'}.get(vid, 'Minor service')
        days = 2 if kind == 'Major service' else 1
        for j, off in enumerate(_SLOT_OFF):
            n += 1
            out.append(dict(slot_id='WS-%03d' % n, vehicle=v['vehicle'], date=ahead(off + (i % 2 if j else 0)), kind=key('mkind', kind), days=days, drop_time=_DROP[(i + j) % 8],
                            planned=(vid in ('VH-025', 'VH-013') and j == 2)))
    return out


_REPAIR_KINDS = ('Repair', 'Body repair', 'Towing', 'Brake service', 'Battery check')
_CLAIMS = claim_rows()
_RL = [m for m in LOG if m['kind'] in _REPAIR_KINDS][-120:]


def _claim_for(m):
    if m['kind'] != 'Body repair': return ''
    for c in _CLAIMS:
        if c['vehicle_id'] == m['vehicle_id'] and c['reported_on'] <= m['date'] <= d_add(c['reported_on'], 60): return c['claim_id']
    return ''


def repair_log_d():
    out = []
    for m in _RL:
        loc = LOCATIONS[(int(m['maint_id'][3:]) * 7) % 5] if m['kind'] == 'Towing' else 'Main lot'
        out.append(nb(dict(maint_id=m['maint_id'], vehicle=m['vehicle'], date=m['date'], kind=key('mkind', m['kind']), cost=m['cost'], days_off_road=m['days_off_road'],
                           claim_id=_claim_for(m), location=key('location', loc))))
    return out


def repair_month_d():
    seen = sorted({(m['month'], m['vehicle']) for m in LOG if m['month'] >= iso(month_start(12))})[-150:]
    return [dict(vehicle=v, month=mo) for mo, v in seen]


_TYR = {}
for m in LOG:
    if m['kind'] == 'Tyre set': _TYR[m['vehicle_id']] = m


def tyres_d():
    out = []
    for v in NONSOLD:
        m = _TYR.get(v['vehicle_id'])
        out.append(dict(vehicle=v['vehicle'], tyre_date=m['date'] if m else v['purchase_date'], odo_then=m['odometer'] if m else v['odometer_at_purchase']))
    return out


def days_lost_d(): return [dict(vehicle=v['vehicle']) for v in VEH]
def cost1000_d(): return [dict(vehicle=v['vehicle']) for v in VEH]
def class_mix_d(): return [dict(**{'class': key('class', c)}) for c in CLASSES]
def age_mix_d(): return [dict(band=key('fleetage', b)) for b in FLEET_AGE]
def inspections_d(): return [dict(maint_id=m['maint_id'], vehicle=m['vehicle'], date=m['date'], cost=m['cost'], days_off_road=m['days_off_road']) for m in LOG if m['kind'] == 'Inspection']


def bookings14_d():
    return [dict(booking_id=b['booking_id'], vehicle=b['vehicle'], **{'class': key('class', b['class'])}, start_date=b['start_date'], end_date=b['end_date'], status=key('bstat2', b['status']),
                 renter=b['renter'], phone=_RN[b['renter_id']]['phone']) for b in BK]


def wk_cal_d(): return [dict(date=ahead(i)) for i in range(30)]


_ROLE = {VENDOR['Mechanic']: 'Mechanic workshop: services and repairs', VENDOR['Tyre supplier']: 'Tyre supplier: tyre sets and fitting', VENDOR['Body repair shop']: 'Body repair shop: scratches, dents and glass',
         VENDOR['Towing service']: 'Towing service: breakdown recovery'}
def vendors_d(): return [dict(vendor=v, role=_ROLE[v]) for v in VENDORS] + [dict(vendor=TEAM['Car-wash supplier']['name'], role='Car-wash supplier: cleaning supplies')]


def renewals_by_veh_d(): return [dict(vehicle=v['vehicle']) for v in NONSOLD]


def fleet_changes_d():
    ev = []
    for v in VEH:
        if dd(v['purchase_date']) >= HISTORY_START: ev.append((v['purchase_date'], v['vehicle'], 'Bought', v['purchase_price']))
        if v['sold_date']: ev.append((v['sold_date'], v['vehicle'], 'Sold', v['sold_price']))
    ev.sort(key=lambda e: (e[2] != 'Sold', e[0]))
    return [dict(change_id='FC-%03d' % (i + 1), vehicle=n, event=key('fevent', e), date=d, amount=a) for i, (d, n, e, a) in enumerate(ev)]
