"""HVAC suite part 6: demo rows from hv_core (full generator output for aggregates, thinned samples for the long ranked lists)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv6_lists import *
import collections, datetime as _dt

TD = TODAY
SITES = site_rows(); SITE = {s['site_id']: s for s in SITES}
EQ = equipment_rows(); AG = agreement_rows(); RN = renewal_rows(); VS = visit_rows(); JOBS = job_rows()
ST = story()
AGB = {a['agreement_id']: a for a in AG}
PH = {t['name']: t['phone'] for t in team}
ROLEPH = {t['role']: t['phone'] for t in team}
OWNER_PHONE = PH[OWNER]; OFFICE_PHONE = PH[OFFICE_MANAGER]
SUP_PHONE = ROLEPH['Equipment supplier']; PARTS_PHONE = ROLEPH['Parts counter']; ACCT_PHONE = ROLEPH['Accountant']
TECH_PHONES = [PH[n] for n in TECH_NAMES]
APPRENTICE, APPRENTICE_PHONE = TECH_NAMES[6], PH[TECH_NAMES[6]]
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def D_(s): return to_date(s)
RUNNING = ('Active', 'Renewal due')
REPAIR_KINDS = ('Repair', 'Diagnostic', 'Drain', 'Repipe'); REPLACE_KINDS = ('Replacement', 'Install')

# ---------- lapse reasons (deterministic, weighted)
_r = rng('hv6-lapse')
def _reason(a):
    x = _r.random()
    for lim, lab in ((0.28, 'Price too high'), (0.46, 'Moved away'), (0.60, 'Service not as expected'), (0.78, 'Switched provider'), (0.90, 'Equipment replaced')):
        if x < lim: return lab
    return 'No reason given'
REASON = {a['agreement_id']: _reason(a) for a in AG if a['status'] in ('Lapsed', 'Cancelled')}

# ---------- sites, equipment
def sites_d():
    rows = [nb(dict(site_id=s['site_id'], site_ref=s['site_ref'], area=key('area', s['area']), site_type=key('sitetype', s['site_type']), landlord=s['landlord'], account=s['account'], phone=s['phone'],
                    member=s['member'], equipment=s['equipment'], jobs=s['jobs'], first_job=s['first_job'], last_job=s['last_job'], revenue=round(s['revenue']))) for s in SITES]
    k = next(i for i, r in enumerate(rows) if r['site_ref'] == DEF['site'])
    rows.insert(0, rows.pop(k))
    return rows

def _age(e): return (TD - D_(e['install_date'])).days / 365.25
SITE_EQ = collections.defaultdict(list)
for e in EQ: SITE_EQ[e['site_id']].append(e)

def equipment_d():
    out = []
    for i, e in enumerate(EQ):
        r = dict(equipment_id=e['equipment_id'], site_id=e['site_id'], type=key('equiptype', e['type']), fuel=key('fuel', e['fuel']), install_date=e['install_date'], warranty_end=e['warranty_end'], make=e['make'],
                 model=e['model'], serial=e['serial'], last_service=e['last_service'])
        if i % 13 == 5: r['serial'] = ''          # a few incomplete records, as in any real book
        if i % 29 == 7: r['model'] = ''
        out.append(nb(r))
    # first row: an aged unit with a last service (forms and documents open on it)
    k = next(i for i, e in enumerate(EQ) if _age(e) >= 13 and e['last_service'] and i % 13 != 5 and i % 29 != 7 and SITE[e['site_id']]['jobs'] >= 6 and SITE[e['site_id']]['member'])
    out.insert(0, out.pop(k))
    return out

# ---------- agreements, renewals, visits
def agreements_d():
    out = []
    for a in AG:
        r = dict(agreement_id=a['agreement_id'], site_id=a['site_id'], site_type=key('sitetype', a['site_type']), plan=key('plan', a['plan']), price=a['price'], visits_per_year=a['visits_per_year'], billing=a['billing'],
                 start_date=a['start_date'], end_date=a['end_date'], renewal_date=a['renewal_date'], last_renewed=a['last_renewed'], renewals=a['renewals'], status=key('agrstatus', a['status']),
                 sold_by=key('tech', a['sold_by']), visits_done=a['visits_done'])
        if a['agreement_id'] in REASON: r['lapse_reason'] = key('lapsereason', REASON[a['agreement_id']])
        out.append(nb(r))
    k = next(i for i, a in enumerate(AG) if a['status'] == 'Active' and a['last_renewed'] and a['renewals'] >= 2 and a['plan'] == 'Standard comfort')
    out.insert(0, out.pop(k))
    return out

def renewals_d():
    return [nb(dict(renewal_id=r['renewal_id'], agreement_id=r['agreement_id'], site_id=r['site_id'], plan=key('plan', r['plan']), due_date=r['due_date'], month=r['month'], renewed_on=r['renewed_on'],
                    outcome=key('renewout', r['outcome']), price=r['price'])) for r in RN]

def visits_d():
    out = []
    for v in VS:
        out.append(nb(dict(visit_id=v['visit_id'], agreement_id=v['agreement_id'], site_id=v['site_id'], plan=key('plan', v['plan']), season=key('visitseason', v['season']), window_start=v['window_start'],
                           window_end=v['window_end'], planned_date=v['planned_date'], done_on=v['done_on'], technician=key('tech', v['technician']) if v['technician'] else '', job_id=v['job_id'], status=key('visitstatus', v['status']))))
    k = next(i for i, v in enumerate(VS) if v['status'] == 'Done' and v['job_id'] and v['technician'] and v['window_start'] >= ago(200))
    out.insert(0, out.pop(k))
    return out

def plans_d(): return [dict(plan=p['plan'], price=p['price'], visits_per_year=p['visits_per_year']) for p in plans]
def techs_d(): return [dict(technician=t['name'], trade=t['trade'], van=t['van']) for t in techs[:6]]

# ---------- aggregates from the jobs
Y1, Y2 = ago(365), ago(730)
def _jobs(lo, hi=None):
    return [j for j in JOBS if j['date'] > lo and j['date'] <= (hi or iso(TD)) and j['status'] == 'Completed']
J12 = _jobs(Y1)
EQT = {e['equipment_id']: e['type'] for e in EQ}
def tickets():
    def avgp(jt, key_=None):
        v = [p['flat_price'] for p in price_book if p['job_type'] == jt and (key_ is None or key_ in p['task'])]
        return sum(v) / len(v)
    t = {'Furnace': avgp('Furnace replacement'), 'Air conditioner': avgp('Air conditioner replacement'), 'Heat pump': avgp('Heat pump install', 'Heat pump'),
         'Mini-split': avgp('Heat pump install', 'Mini-split'), 'Water heater': avgp('Water heater replacement')}
    t['Boiler'] = t['Furnace'] * 1.15
    return {k: round(v, -1) for k, v in t.items()}
TICKET = tickets()
def equip_types_d(): return [dict(type=t, replace_ticket=TICKET[t]) for t in EQUIP_TYPES]

SHARE = {'Up to 5 years': 0.01, 'From 6 to 10 years': 0.03, 'From 11 to 15 years': 0.08, 'Over 15 years': 0.20}
def age_bands_d(): return [dict(band=key('ageband', b), type=key('equiptype', t), replace_share=SHARE[b]) for b in AGE_BANDS for t in EQUIP_TYPES]

def member_rev_d():
    agg = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for j in J12:
        s = SITE[j['site_id']]; x = agg[(s['member'], s['area'])]
        if j['kind'] in REPAIR_KINDS: x[0] += j['price']
        elif j['kind'] in REPLACE_KINDS: x[1] += j['price']
        elif not j['agreement_id']: x[2] += j['price']          # tune-ups inside an agreement are paid by the plan fee
    for p in payment_rows():
        if p['kind'] == 'Agreement fee' and p['date'] > Y1 and p['site_id'] in SITE: agg[(SITE[p['site_id']]['member'], SITE[p['site_id']]['area'])][3] += p['amount']
    return [dict(member=m, area=key('area', a), repair_revenue=round(agg[(m, a)][0]), replacement_revenue=round(agg[(m, a)][1]), tune_up_revenue=round(agg[(m, a)][2]), agreement_fees=round(agg[(m, a)][3]))
            for m in (True, False) for a in AREAS]

def plan_profit_d():
    vc = collections.defaultdict(list); tv = collections.defaultdict(list)
    for j in JOBS:
        if j['agreement_id'] and j['kind'] == 'Tune-up' and j['status'] == 'Completed' and j['date'] > Y2:
            a = AGB.get(j['agreement_id'])
            if not a: continue
            vc[(a['plan'], a['site_type'])].append(j['labour_cost'] + j['parts_cost'] + j['permit_fee'] + j['disposal']); tv[(a['plan'], a['site_type'])].append(j['vehicle_cost'])
    fo = collections.defaultdict(float); dc = collections.defaultdict(float)
    for j in J12:
        a = AGB.get(j['agreement_id']) if j['agreement_id'] else None
        if not a: continue
        if j['kind'] != 'Tune-up': fo[(a['plan'], a['site_type'])] += j['price']
        dc[(a['plan'], a['site_type'])] += j['discount']
    cnt = collections.Counter((a['plan'], a['site_type']) for a in AG if a['status'] in RUNNING)
    cntp = collections.Counter(a['plan'] for a in AG if a['status'] in RUNNING)
    def avg(d, p, st):
        x = d.get((p, st)) or [v for (pp, _), l in d.items() if pp == p for v in l] or [v for l in d.values() for v in l]
        return sum(x) / len(x)
    out = []
    for p in PLAN_NAMES:
        fop = sum(v for (pp, _), v in fo.items() if pp == p) / max(1, cntp[p]); dcp = sum(v for (pp, _), v in dc.items() if pp == p) / max(1, cntp[p])
        for st in SITE_TYPES:
            n = cnt[(p, st)]
            out.append(dict(plan=key('plan', p), site_type=key('sitetype', st), visit_cost=round(avg(vc, p, st), 2), travel_cost=round(avg(tv, p, st), 2),
                            follow_on=round(fo[(p, st)] / n if n >= 3 else fop), discount_given=round(dc[(p, st)] / n if n >= 3 else dcp, 2)))
    return out

def attach_d():
    out = []
    for per, (lo, hi) in (('Last 12 months', (Y1, iso(TD))), ('Previous 12 months', (Y2, Y1))):
        c = collections.Counter(j['technician'] for j in _jobs(lo, hi) if j['kind'] in REPAIR_KINDS + REPLACE_KINDS and not j['agreement_id'])
        for t in TECH6: out.append(dict(technician=key('tech', t), period=key('period', per), eligible=c[t]))
    return out

# ---------- campaign list: sites with the oldest equipment and the longest gap since a service
def _site_stats(sid):
    eq = SITE_EQ.get(sid, [])
    if not eq: return None
    ls = max([e['last_service'] for e in eq if e['last_service']] or [''])
    return max(_age(e) for e in eq), ls
def campaign_d():
    rr = rng('hv6-campaign')
    cand = []
    for s in SITES:
        st = _site_stats(s['site_id'])
        if st and st[0] >= 6: cand.append((st[0] + (4 if not st[1] else (TD - D_(st[1])).days / 365.25 * 2), s['site_id']))
    cand.sort(reverse=True); pool = [x[1] for x in cand[:260]]; rr.shuffle(pool)
    plan = [5, 4, 3, 3, 4, 6, 8, 12, 16, 11, 5, 6]            # reminders per month, oldest first (month k=11..0): autumn and spring pushes
    out, n = [], 1; used = 0
    for i, cnt in enumerate(plan):
        k = 11 - i; m0 = month_start(k); last = (TD if k == 0 else add_months(m0, 1) - _dt.timedelta(days=1))
        span = (last - m0).days
        for _ in range(cnt):
            sid = pool[used]; used += 1
            d = m0 + _dt.timedelta(days=rr.randint(0, max(0, span)))
            if d > TD: d = TD - _dt.timedelta(days=rr.randint(0, 6))
            ch = rr.choices(CHANNELS, [35, 50, 15])[0]
            age = _site_stats(sid)[0]
            p = {'Text message': 0.30, 'Mailed letter': 0.20, 'Phone call': 0.42}[ch] * (1.25 if age >= 10 else 0.85)
            fresh = (TD - d).days
            booked = rr.random() < p * (min(1, fresh / 12) if fresh < 12 else 1)
            conv = booked and rr.random() < 0.32
            out.append(dict(campaign_id='CP-%03d' % n, site_id=sid, reminder_sent=iso(d), channel=key('channel', ch), booked=booked, converted=conv)); n += 1
    out.insert(0, out.pop(next(i for i, r in enumerate(out) if r['booked'] and r['converted'] and r['reminder_sent'] < ago(40) and _site_stats(r['site_id'])[1])))
    return out

# ---------- calculated tables: only the keys
def aged_d(): return [dict(rank_no=i) for i in range(1, 41)]
def renew_due_d(): return [dict(rank_no=i) for i in range(1, 31)]
def lapse_d(): return [dict(rank_no=i) for i in range(1, 31)]
def book_month_d(): return [dict(month=iso(m)) for m in months14()]
def plan_status_d(): return [dict(plan=key('plan', p), status=key('agrstatus', s)) for p in PLAN_NAMES for s in AGREEMENT_STATUS]
def visits_month_d():
    dem = {s['month_no']: s['demand_index'] for s in seasons}
    return [dict(month=iso(month_start(k)), demand_index=dem[month_start(k).month]) for k in range(8, -4, -1)]
def campaign_month_d(): return [dict(month=iso(month_start(k))) for k in range(11, -1, -1)]

if __name__ == '__main__':
    print('tickets', TICKET); print(plan_profit_d()[:6]); print(attach_d()); print(member_rev_d()[:3], member_rev_d()[8:11])
    c = campaign_d(); print(len(c), sum(r['booked'] for r in c), sum(r['converted'] for r in c), c[0])


# ---------- defaults for the tools (editable inputs, computed once from the same data)
def _defaults():
    dec = [r for r in RN if r['outcome'] != 'Open' and r['due_date'] >= ago(365) and r['due_date'] < iso(TD)]
    rate = sum(r['outcome'] == 'Renewed' for r in dec) / len(dec)
    ms0 = month_start(0); new6 = sum(1 for a in AG if iso(month_start(6)) <= a['start_date'] < iso(ms0)) / 6
    run = [a for a in AG if a['status'] in RUNNING]
    avgp = sum(a['price'] for a in run) / len(run); avgv = sum(a['price'] / a['visits_per_year'] for a in run) / len(run)
    pick = [s for s in SITES if s['member'] and s['equipment'] >= 2 and s['jobs'] >= 8 and any(_age(e) >= 12 and e['last_service'] for e in SITE_EQ[s['site_id']])]
    return dict(rate=round(rate, 2), signups=round(new6, 1), avg_price=round(avgp), avg_visit=round(avgv), site=(pick or SITES)[0]['site_ref'], running=len(run))
DEF = _defaults()
