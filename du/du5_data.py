"""Doula business suite part 5: demo rows from du_core (full generator output for the row-level tables, calculated tables get only their key columns)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du5_lists import *
import datetime as _dt

dd = to_date
R = rng('du5')
ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def I(x): return iso(x) if hasattr(x, 'isoformat') else x

TEAMD = {t['name']: t for t in team}
OWNER_PHONE = TEAMD[OWNER]['phone']; ADMIN_PHONE = TEAMD[ADMIN]['phone']
ACCOUNTANT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
AREAD = {a['area']: a for a in areas}
PKD = {p['package']: p for p in packages}
CLF = client_rows(); CLD = {c['client_id']: c for c in CLF}; CLN = {c['client']: c for c in CLF}
VSF = visit_rows(); BTF = birth_rows(); PKF = pack_rows(); ONF = oncall_rows()
T0 = TODAY
MS0 = month_start(0)

# ------------------------------------------------------------------ visits: start times (08:00 to 20:30), three recent visits with no miles written yet
def _vtime(v, i):
    r = rng('vt%d' % i)
    if v['kind'] == 'Night shift': m = 20 * 60 + 30 * r.randrange(0, 5)
    elif v['kind'] == 'Prenatal visit': m = 9 * 60 + 30 * r.randrange(0, 17)
    elif v['kind'] == 'Debrief visit': m = 10 * 60 + 30 * r.randrange(0, 11)
    else: m = (8 * 60 if v['hours'] >= 6 else 8 * 60 + 30 * r.randrange(0, 15)) + 30 * r.randrange(0, 2)
    m = min(m, 20 * 60 + 30)
    return '%02d:%02d' % (m // 60, m % 60)
_recent = [i for i, v in enumerate(VSF) if v['date'] >= MS0 and v['date'] < T0 - _dt.timedelta(days=2)]
NOMILES = set(_recent[::max(1, len(_recent) // 3)][:3])


def visits_d():
    out = []
    for i, v in enumerate(VSF):
        out.append(nb(dict(visit_id=v['visit_id'], date=I(v['date']), time=_vtime(v, i), client=v['client'], doula=key('doula', v['doula']), kind=key('vkind', v['kind']), hours=v['hours'],
                           miles=('' if i in NOMILES else v['miles']), area=key('area', v['area']))))
    return out


def births_d():
    out = []
    for b in BTF:
        out.append(dict(birth_id=b['birth_id'], date=I(b['date']), client=b['client'], doula=key('attender', b['doula']), assigned=key('doula', b['assigned']), backup_used=bool(b['backup_used']),
                        call_time=b['call_time'], arrive_time=b['arrive_time'], leave_time=b['leave_time'], hours=b['hours'], miles=b['miles'], area=key('area', b['area']), on_call_day=b['on_call_day']))
    return out


# ------------------------------------------------------------------ hour packs: the extra hours of two packs are not invoiced yet (one expired, one still running)
_EXTRA = [p for p in PKF if p['extra_hours'] > 0]
_OPEN = {p['pack_id'] for p in _EXTRA if p['expires_on'] >= T0 or p['pack_id'] == 'HP-0059'}
def front(rows, pred):
    """move the first row that matches to the top (the sheets and printable pages open on it)"""
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows


def packs_d():
    out = []
    for p in PKF:
        inv = ''
        if p['extra_hours'] > 0 and p['pack_id'] not in _OPEN: inv = I(p['expires_on'] + _dt.timedelta(days=5))
        out.append(nb(dict(pack_id=p['pack_id'], client=p['client'], doula=key('doula', p['doula']), package=key('hpack', p['package']), hours_bought=p['hours_bought'], price=p['price'],
                           bought_on=I(p['bought_on']), expires_on=I(p['expires_on']), hours_used=p['hours_used'], extra_hours=p['extra_hours'], invoiced_on=inv)))
    return front(out, lambda r: r['pack_id'] == 'HP-0101')


# ------------------------------------------------------------------ clients with the next visit (booked clients: a prenatal visit before the on-call start; clients in postpartum care: a shift)
def clients_d():
    out = []
    for c in CLF:
        nv, nk, nt = '', '', ''
        r = rng('nv' + c['client_id'])
        if c['status'] == 'Postpartum care':
            nv = I(T0 + _dt.timedelta(days=r.randrange(1, 10))); nk = r.choice(['Postpartum visit'] * 5 + ['Night shift', 'Debrief visit'])
            nt = '%02d:%02d' % (8 + r.randrange(0, 10), 30 * r.randrange(0, 2))
        elif c['status'] == 'Booked' and c['oncall_start']:
            room = (c['oncall_start'] - T0).days - 7
            if room >= 7:
                nv = I(T0 + _dt.timedelta(days=r.randrange(3, min(70, room) + 1))); nk = 'Prenatal visit'; nt = '%02d:%02d' % (9 + r.randrange(0, 9), 30 * r.randrange(0, 2))
        out.append(nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], area=key('area', c['area']), kind=key('ckind', c['kind']), package=c['package'], signed_on=I(c['signed_on']),
                           edd=I(c['edd']), oncall_start=I(c['oncall_start']) if c['oncall_start'] else '', doula=key('doula', c['doula']), status=key('cstatus', c['status']), next_visit=nv,
                           next_kind=key('vkind', nk) if nk else '', visit_time=nt)))
    return front(out, lambda r: r['client'] == RICH_CLIENT)


def packages_d():
    return [dict(package=p['package'], kind=key('pkind', p['kind']), price=p['price'], prenatal_visits=p['prenatal_visits'], postpartum_visits=p['postpartum_visits'], birth_hours=p['birth_hours'],
                 oncall_hours=p['oncall_hours'], postpartum_hours=p['postpartum_hours'], plan_hours=p['plan_hours']) for p in packages]


def areas_d():
    h = {'Northgate': [0.52, 0.55], 'Southbank': [0.56]}
    out = [dict(area=key('area', n), mileage_rate=r, in_use=0) for n, rs in h.items() for r in rs]
    out += [dict(area=key('area', a['area']), mileage_rate=a['mileage_rate'], in_use=1) for a in areas]
    return out
def doulas_d(): return [dict(doula=key('doula', d['doula']), service=key('service', d['service']), weekly_hours_cap=d['weekly_hours_cap']) for d in doulas]


def oncall_d():
    return [nb(dict(window_id=o['window_id'], client=o['client'], doula=key('doula', o['doula']), oncall_start=I(o['oncall_start']), oncall_end=I(o['oncall_end']), attended_on=I(o['attended_on']) if o['attended_on'] else '',
                    contact_hours=o['contact_hours'])) for o in ONF]


def phase_d(): return front([dict(client=c['client']) for c in CLF if c['status'] != 'Booked'], lambda r: r['client'] == DEF_OVER_CLIENT)
def ledger_d(): return front([dict(pack_id=p['pack_id']) for p in PKF], lambda r: r['pack_id'] == DEF_PACK)


def wk_doula_d():
    w0 = week_start(T0); out = []
    for k in range(17, -1, -1):
        for d in DOULA_NAMES: out.append(dict(doula=key('doula', d), week=I(w0 - _dt.timedelta(days=7 * k))))
    return out


def wk_all_d():
    w0 = week_start(T0)
    return [dict(week=I(w0 - _dt.timedelta(days=7 * k)), week_no=key('wkno', 'Week %d' % (26 - k))) for k in range(25, -1, -1)]


def months_d(): return [dict(month=I(m)) for m in months24()]


# ------------------------------------------------------------------ mileage by client: the 60 clients with the highest mileage cost (visits and births, round trips)
def _mil_costs():
    mc = {}
    for v in VSF: mc[v['client']] = mc.get(v['client'], 0) + (v['miles'] if v['miles'] != '' else 0) * AREAD[v['area']]['mileage_rate']
    for b in BTF: mc[b['client']] = mc.get(b['client'], 0) + b['miles'] * AREAD[b['area']]['mileage_rate']
    return mc
_MC = _mil_costs()
def mil_client_d():
    top = sorted([c for c in _MC if CLN[c]['package'] in PKD], key=lambda c: -_MC[c])[:60]
    return [dict(client=c) for c in top]


def mil_doula_d(): return [dict(doula=key('doula', d), area=key('area', a)) for d in DOULA_NAMES for a in AREAS]


def rest_d():
    last = {}; rows = []
    for b in BTF:
        if b['doula'] in last: rows.append(b['birth_id'])
        last[b['doula']] = b['date']
    return [dict(birth_id=i) for i in rows[-120:]]


def bands_d(): return [dict(band=key('hband', b)) for b in HBAND]
def calls_d(): return [dict(band=key('cband', b)) for b in CBAND]


def team_d():
    return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email']) for t in team]


# ------------------------------------------------------------------ defaults for the tools (taken from the demo story)
def _phase_over():
    H = {}
    for v in VSF: H[v['client']] = H.get(v['client'], 0) + v['hours']
    for b in BTF: H[b['client']] = H.get(b['client'], 0) + b['hours']
    for o in ONF:
        if o['contact_hours'] != '': H[o['client']] = H.get(o['client'], 0) + o['contact_hours']
    best = None
    for c in CLF:
        if c['status'] == 'Booked': continue
        plan = PKD[c['package']]['plan_hours']; tot = H.get(c['client'], 0)
        if plan and tot and (best is None or tot / plan > best[0]): best = (tot / plan, c['client'])
    return best[1]
DEF_OVER_CLIENT = _phase_over()
DEF_PACK = [p for p in PKF if p['client_id'] == ST['prepaid_client_id']][0]['pack_id']
_booked = [c for c in CLF if c['status'] == 'Booked' and c['oncall_start'] and (c['oncall_start'] - T0).days > 60]
DEF_BOOKED = _booked[0]['client']
def _night_doula():
    cnt = {}
    for v in VSF:
        if v['kind'] == 'Night shift' and v['date'] >= T0 - _dt.timedelta(days=90): cnt[v['doula']] = cnt.get(v['doula'], 0) + 1
    for b in BTF:
        h = int(b['call_time'][:2])
        if (h >= 22 or h < 6) and b['date'] >= T0 - _dt.timedelta(days=90): cnt[b['doula']] = cnt.get(b['doula'], 0) + 1
    return max(cnt, key=cnt.get)
DEF_NIGHT = _night_doula()

def _rich():
    n = {}
    for v in VSF: n[v['client']] = n.get(v['client'], 0) + 1
    ok = [c['client'] for c in CLF if c['status'] == 'Completed' and c['kind'] == 'Combined' and c['oncall_start']]
    return max(ok, key=lambda c: n.get(c, 0))
RICH_CLIENT = _rich()

def _timing():
    import collections
    n = collections.Counter(v['client'] for v in visits_d() if v['kind'] == 'prenatal_visit')
    pk = {p['package']: p for p in packages_d()}
    for x in clients_d():
        if x['status'] == 'booked' and x.get('next_visit') and pk[x['package']]['prenatal_visits'] > n[x['client']]: return x['client']
    return DEF_BOOKED
DEF_TIMING = _timing()
