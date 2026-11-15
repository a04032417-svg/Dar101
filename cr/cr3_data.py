"""Car rental suite part 3: demo rows from cr_core (recent rows where the table is a log, full history where a month table needs real totals)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datetime as _dt
from cr3_lists import *

ST = story()
dd = to_date
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))

TEAMD = {t['name']: t for t in team}
def tphone(name): return TEAMD[name]['phone']
OWNER_PHONE = tphone(OWNER); MANAGER_PHONE = tphone(MANAGER)
DETAILER_NAME = 'Lucia Fernandes'; DETAILER_PHONE = tphone(DETAILER_NAME)
BOOKKEEPER_NAME = 'Elsa Nordin'; BOOKKEEPER_PHONE = tphone(BOOKKEEPER_NAME)
def by_role(role): return [t for t in team if t['role'] == role][0]
ACCOUNTANT = by_role('Accountant'); BROKER = by_role('Insurance broker'); BODYSHOP = by_role('Body repair shop')
MARKET_PHONE = fake_phone(2101); HOTEL_PHONE = fake_phone(2102); CORP_PHONE = fake_phone(2103)

VEH = vehicle_rows(); VD = {v['vehicle_id']: v for v in VEH}
BKF = booking_rows(); BK = {b['booking_id']: b for b in BKF}
REN = renter_rows(); RD = {r['renter_id']: r for r in REN}
HOF = handover_rows(); FEF = fee_rows(); CLF = claim_rows(); DEPF = deposit_rows(); TOF = toll_rows(); ADF = addon_rows()
DEPB = {}
for x in DEPF: DEPB[x['booking_id']] = DEPB.get(x['booking_id'], 0.0) + x['amount']
COVER = {a['booking_id'] for a in ADF if a['addon'].startswith('Cover')}
CLEAN = {f['booking_id'] for f in FEF if f['kind'] == 'Cleaning'}
LO15 = iso(month_start(14))
HH = [h for h in HOF if h['out_date'] >= LO15]
OPEN_ST = ('Reported', 'Estimate', 'In repair')


def _t(s): return s if s else ''


def handover_d():
    out = []
    for h in HH:
        b = BK[h['booking_id']]; r = RD[h['renter_id']]
        out.append(nb(dict(handover_id=h['handover_id'], booking_id=h['booking_id'], vehicle=h['vehicle'], **{'class': key('class', b['class'])}, renter=r['renter'], out_date=h['out_date'],
                           out_time=h['out_time'], agreed_time=b['return_time'], out_odometer=h['out_odometer'], out_level=h['out_level'], photos_out=h['photos_out'], keys=h['keys'],
                           deposit_taken=h['deposit_taken'], handled_by=key('handler', h['handled_by']), in_date=h['in_date'], in_time=h['in_time'], in_odometer=h['in_odometer'],
                           in_level=h['in_level'], photos_in=h['photos_in'], damage_seen=h['damage_seen'], cleaning=h['booking_id'] in CLEAN and bool(h['in_date']),
                           miles_included=h['miles_included'], phone=r['phone'])))
    return out


def bookings_d():
    lo = ago(75); out = []
    for b in BKF:
        if b['start_date'] < lo: continue
        out.append(dict(booking_id=b['booking_id'], bk_no=int(b['booking_id'][3:]), start_date=b['start_date'], end_date=b['end_date'], vehicle=b['vehicle'], **{'class': key('class', b['class'])},
                        renter=b['renter'], channel=key('channel', b['channel']), return_time=b['return_time'], deposit=b['deposit'], status=key('bstatus', b['status'])))
    return out


def fees_d(): return [dict(fee=f['fee'], amount=f['amount'], basis=f['basis']) for f in fees]


def fee_log_d():
    out = []
    for f in FEF:
        b = BK[f['booking_id']]; r = RD[b['renter_id']]
        out.append(dict(fee_id=f['fee_id'], booking_id=f['booking_id'], vehicle_id=f['vehicle_id'], date=f['date'], month=f['month'], kind=key('feekind', f['kind']), amount_due=f['amount_due'],
                        billed=f['billed'], collected=f['collected'], status=key('feestatus', f['status']), renter=r['renter'], phone=r['phone']))
    return out


def fee_ageing_d(): return [dict(band=x) for x in ('0 to 14 days', '15 to 30 days', '31 to 90 days', '91 to 180 days', 'Over 180 days')]
def claim_ageing_d(): return [dict(band=x) for x in ('0 to 14 days', '15 to 30 days', '31 to 45 days', '46 to 90 days', 'Over 90 days')]
def money_left_d(): return [dict(month=iso(month_start(k))) for k in range(23, -1, -1)]
def fees_month_d(): return [dict(month=iso(month_start(k)), kind=key('feekind', f)) for k in range(23, -1, -1) for f in FEE_KINDS]


def claims_d():
    out = []; oi = 0
    for i, x in enumerate(CLF):
        b = BK[x['booking_id']]; r = RD[x['renter_id']]; op = x['status'] in OPEN_ST
        if op: slot = ahead(3 + 3 * oi); oi += 1
        else: slot = d_add(x['reported_on'], 5 + i % 7)
        out.append(nb(dict(claim_id=x['claim_id'], booking_id=x['booking_id'], vehicle=x['vehicle'], renter=r['renter'], **{'class': key('class', b['class'])}, channel=key('channel', b['channel']),
                           plan=key('plan', b['plan']), young=b['young_driver'], cover=x['booking_id'] in COVER, reported_on=x['reported_on'], month=x['month'], kind=key('claimkind', x['kind']),
                           status=key('claimstatus', x['status']), estimate=x['estimate'], repair_cost=x['repair_cost'], deposit=DEPB.get(x['booking_id'], 0.0), deposit_used=x['deposit_used'],
                           claim_paid=x['claim_paid'], written_off=x['written_off'], closed_on=x['closed_on'], slot_date=slot, phone=r['phone'])))
    return out


def _rentals_month(m):
    return sum(1 for b in BKF if b['status'] in ('Completed', 'Active') and b['start_date'][:7] == m[:7])
def claims_month_d():
    return [dict(month=iso(month_start(k)), rentals=_rentals_month(iso(month_start(k)))) for k in range(23, -1, -1)]


def segments_d():
    lo = ago(365); rent = [b for b in BKF if b['status'] in ('Completed', 'Active') and b['start_date'] >= lo]
    def n(f): return sum(1 for b in rent if f(b))
    out = []
    for c in CLASSES: out.append(dict(kind=key('segkind', 'Class'), segment=c, rentals=n(lambda b: b['class'] == c)))
    for c in CHANNELS: out.append(dict(kind=key('segkind', 'Channel'), segment=c, rentals=n(lambda b: b['channel'] == c)))
    for c in PLANS: out.append(dict(kind=key('segkind', 'Plan'), segment=c, rentals=n(lambda b: b['plan'] == c)))
    out.append(dict(kind=key('segkind', 'Young driver'), segment='Young driver: yes', flag=True, rentals=n(lambda b: b['young_driver'])))
    out.append(dict(kind=key('segkind', 'Young driver'), segment='Young driver: no', flag=False, rentals=n(lambda b: not b['young_driver'])))
    out.append(dict(kind=key('segkind', 'Cover option'), segment='Cover option: yes', flag=True, rentals=n(lambda b: b['booking_id'] in COVER)))
    out.append(dict(kind=key('segkind', 'Cover option'), segment='Cover option: no', flag=False, rentals=n(lambda b: b['booking_id'] not in COVER)))
    return out


def tolls_d():
    out = []
    for t in TOF:
        r = RD.get(t['renter_id']) if t['renter_id'] else None
        out.append(nb(dict(toll_id=t['toll_id'], date=t['date'], month=t['month'], vehicle=t['vehicle'], kind=key('tollkind', t['kind']), amount=t['amount'], booking_id=t['booking_id'],
                           renter=r['renter'] if r else '', status=key('tollstatus', t['status']), admin_fee=t['admin_fee'], recovered=t['recovered'], passed_on=t['passed_on'],
                           phone=r['phone'] if r else MARKET_PHONE)))
    return out


def toll_match_d(): return [dict(toll_id=t['toll_id']) for t in TOF[-60:]]


def renter_status_d():
    last = {}
    for b in BKF: last[b['renter_id']] = b['start_date'] if b['renter_id'] not in last or b['start_date'] > last[b['renter_id']] else last[b['renter_id']]
    flagged = [r for r in REN if r['status'] != 'Verified']
    fid = {r['renter_id'] for r in flagged}
    rest = sorted([r for r in REN if r['renter_id'] not in fid], key=lambda r: r['last_rental'])[-(150 - len(flagged)):]
    rows = sorted(flagged + rest, key=lambda r: last.get(r['renter_id'], r['last_rental']))
    return [nb(dict(renter_id=r['renter_id'], renter=r['renter'], age_band=key('ageband', r['age_band']), status=key('rstatus', r['status']), documents_checked=r['documents_checked'],
                    account=r['account'], rentals=r['rentals'], start_date=last.get(r['renter_id'], r['last_rental']), phone=r['phone'])) for r in rows]


def classes_d(): return [dict(**{'class': key('class', c['class'])}, deposit=c['deposit'], miles_day=c['included_miles_day']) for c in classes]


def _late(h):
    if not h['in_date']: return 0
    b = BK[h['booking_id']]
    return max(0, int(round((_mins(h['in_time']) - _mins(b['return_time'])))))
def _mins(t): return int(t[:2]) * 60 + int(t[3:5])


def late_returns_d():
    rows = [h for h in HH if h['in_date'] and _late(h) > 0][-160:]
    while rows and _late(rows[0]) <= LATE_GRACE_MIN: rows = rows[1:]
    return [dict(booking_id=h['booking_id'], vehicle=h['vehicle'], date=h['in_date'], agreed_time=BK[h['booking_id']]['return_time'], actual_time=h['in_time']) for h in rows]


def fuel_levels_d():
    rows = [h for h in HH if h['in_date'] and h['in_level'] != '' and h['out_level'] - h['in_level'] > 0][-160:]
    while rows and rows[0]['out_level'] - rows[0]['in_level'] < 10: rows = rows[1:]
    return [dict(booking_id=h['booking_id'], vehicle=h['vehicle'], date=h['in_date'], fuel=key('fuel', VD[h['vehicle_id']]['fuel']), out_level=h['out_level'], in_level=h['in_level']) for h in rows]


def extra_mileage_d():
    rows = [h for h in HH if h['in_date'] and h['extra_miles'] not in ('', 0)][-110:]
    return [dict(booking_id=h['booking_id'], date=h['in_date'], **{'class': key('class', BK[h['booking_id']]['class'])}, plan=key('plan', BK[h['booking_id']]['plan']),
                 miles_included=h['miles_included'], miles_driven=h['miles_driven']) for h in rows]


def _miss(h): return (0 if h['photos_out'] else 1) + (1 if h['keys'] < 2 else 0) + (0 if h['photos_in'] else 1)
def photos_keys_d():
    rows = [h for h in HH if h['in_date']][-110:]
    k = 0
    while k < len(rows) and _miss(rows[k]) == 0: k += 1
    rows = rows[k:]
    return [dict(booking_id=h['booking_id'], vehicle=h['vehicle'], handled_by=key('handler', h['handled_by']), date=h['in_date'], photos_out=h['photos_out'], photos_in=h['photos_in'], keys=h['keys'])
            for h in rows]


def vehicles_d():
    return [dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], plate=v['plate'], **{'class': key('class', v['class'])}, fuel=key('fuel', v['fuel']), status=key('vstatus', v['status']),
                 odometer=v['odometer']) for v in VEH]
