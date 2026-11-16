"""Doula Business suite part 2: demo rows from du_core (full generator output where the table is small, aggregated tables built from it)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du2_lists import *

ST = story()
TEAMD = {t['name']: t for t in team}
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def I(x): return iso(x) if hasattr(x, 'isoformat') else x

CLF = client_rows(); CONF = contract_rows(); ADF = addon_rows()
CLD = {c['client_id']: c for c in CLF}
SUM = {c['client_id']: client_summary(c['client_id']) for c in CLF}


def packages_d():
    return [dict(package_id=p['package_id'], package=key('package', p['package']), kind=key('pkind', p['kind']), price=p['price'], birth_value=p['birth_value'], pp_value=p['pp_value'],
                 prenatal_visits=p['prenatal_visits'], postpartum_visits=p['postpartum_visits'], birth_hours=p['birth_hours'], oncall_hours=p['oncall_hours'],
                 postpartum_hours=p['postpartum_hours'], deposit_pct=p['deposit_pct']) for p in packages]


def contracts_d():
    rows = [nb(dict(contract_id=c['contract_id'], client_id=c['client_id'], client=c['client'], package=key('cpackage', c['package']), kind=key('ckind', c['kind']), list_price=c['list_price'],
                    discount=key('discount', c['discount']), price=c['price'], signed_on=I(c['signed_on']), status=key('ctstatus', c['status']))) for c in CONF]
    # demo touch: a completed community-rate contract comes first (the Community Rate Request Sheet and its message read the first row)
    i = next(j for j, c in enumerate(CONF) if c['discount'] == 'Community rate' and c['status'] == 'Completed' and c['price'] > 1000)
    return [rows[i]] + rows[:i] + rows[i + 1:]


def hours_d():
    rows = []
    for c in CLF:
        if c['status'] != 'Completed': continue
        s = SUM[c['client_id']]
        rows.append(nb(dict(client_id=c['client_id'], client=c['client'], package=key('cpackage', c['package']), doula=key('doula', c['doula']), area=key('area', c['area']), month=I(c['due_month']),
                            prenatal_hours=round(s['prenatal'], 2), oncall_hours=round(s['oncall'], 2), birth_hours=round(s['birth'], 2), postpartum_hours=round(s['postpartum'], 2),
                            mileage_cost=round(s['mileage'], 2))))
    i = next(j for j, r in enumerate(rows) if r['package'] == key('cpackage', 'Birth Plus') and r['prenatal_hours'] > 0 and r['oncall_hours'] > 0 and r['birth_hours'] > 0 and r['postpartum_hours'] > 0)
    return [rows[i]] + rows[:i] + rows[i + 1:]


def addons_d():
    rows = [dict(addon_id=a['addon_id'], date=I(a['date']), month=I(a['month']), client_id=a['client_id'], client=a['client'], addon=key('addon', a['addon']), price=a['price'], hours=a['hours'],
                 doula=key('doula', a['doula'])) for a in ADF]
    i = next(j for j, a in enumerate(ADF) if a['addon'] == 'Extra prenatal visit' and a['hours'] > 0)
    return [rows[i]] + rows[:i] + rows[i + 1:]


def rates_d():
    rows = [dict(shift=key('shift', r['shift']), rate_hour=r['rate_hour'], min_hours=r['min_hours']) for r in pp_rates]
    rows.append(dict(shift=key('shift', 'Short visit'), rate_hour=44.0, min_hours=2))
    return rows


def areas_d():
    return [dict(area='Northgate', mileage_rate=0.58, miles_one_way=12), dict(area='Southbank', mileage_rate=0.62, miles_one_way=16),
            dict(area='Northgate, far side', mileage_rate=0.58, miles_one_way=18), dict(area='Southbank, far side', mileage_rate=0.62, miles_one_way=22),
            dict(area='Class venue trip', mileage_rate=0.60, miles_one_way=14)]


def profit_d(): return [dict(package=key('package', p['package']), kind=key('pkind', p['kind'])) for p in packages]
def mix_d(): return [dict(month=iso(m), kind=key('pkind', k)) for m in months24() for k in PACKAGE_KINDS]


def _periods(): return [iso(month_start(k)) for k in (11, 8, 5, 2)]
def bundles_d():
    out = []; n = 0
    for b in BUNDLES:
        for p in _periods():
            n += 1; out.append(dict(bundle_id='BN-%02d' % n, bundle=key('bundle', b), from_month=p))
    # demo touch: the first row (read by the Bundle Proposal Sheet and the review note) is a bundle and period with sales
    def sold(r):
        b = BUNDLES[[key('bundle', x) for x in BUNDLES].index(r['bundle'])]; p0 = r['from_month']; p1 = iso(add_months(to_date(p0), 3))
        return sum(1 for c in CONF if c['package'] == b and p0 <= iso(c['signed_on']) < p1)
    i = max(range(len(out)), key=lambda j: (sold(out[j]), -j))
    return [out[i]] + out[:i] + out[i + 1:]
def discounts_d():
    out = []; n = 0
    for d in DISCOUNTS:
        for p in _periods():
            n += 1; out.append(dict(discount_id='DS-%02d' % n, discount=key('discount', d), from_month=p))
    i = next(j for j, r in enumerate(out) if r['discount'] == key('discount', 'Community rate') and r['from_month'] == _periods()[-1])
    return [out[i]] + out[:i] + out[i + 1:]
def attach_d(): return [dict(addon=key('addon', a)) for a in ADDONS]
def local_d():
    return [dict(label=key('lrange', 'Birth package'), local_low=1100.0, local_high=2200.0), dict(label=key('lrange', 'Postpartum hour'), local_low=30.0, local_high=50.0),
            dict(label=key('lrange', 'Night hour'), local_low=38.0, local_high=60.0), dict(label=key('lrange', 'Combined package'), local_low=2400.0, local_high=4800.0),
            dict(label=key('lrange', 'Add-on'), local_low=30.0, local_high=160.0)]
def scn_d():
    out = []; n = 0
    for s, e in (('Base', 0.5), ('Best', 0.2), ('Worst', 1.0)):
        for ch in (-0.10, -0.05, 0.05, 0.10):
            n += 1; out.append(dict(scn_id='SC-%02d' % n, scenario=key('scen', s), price_change=ch, volume_response=e))
    return out
def hplan_d(): return [dict(package=key('package', p['package'])) for p in packages]
def mileage_d(): return [dict(package=key('package', p['package'])) for p in packages]
def pp_d():
    out = []; n = 0
    for p in PPACKS:
        for s in ('Day shift', 'Evening shift', 'Night shift', 'Weekend and holiday'):
            n += 1; out.append(dict(pp_id='PP-%02d' % n, package=key('ppack', p), shift=key('shift', s)))
    return out
def sales_d(): return [dict(month=iso(m)) for m in months24()]
def plist_d(): return [dict(package=key('package', p['package'])) for p in packages]


def team_d():
    return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email']) for t in team]


def clients_d():
    rows = []
    for c in CLF:
        s = SUM[c['client_id']]
        rows.append(nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], area=key('area', c['area']), kind=key('ckind', c['kind']), package=key('cpackage', c['package']),
                            doula=key('doula', c['doula']), signed_on=I(c['signed_on']), status=key('cstatus', c['status']), pp_hours_used=round(s['postpartum'], 2))))
    i = next(j for j, c in enumerate(CLF) if c['client_id'] == ST['prepaid_client_id'])
    return [rows[i]] + rows[:i] + rows[i + 1:]
