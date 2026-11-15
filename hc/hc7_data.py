"""Home care agency suite part 7: demo rows built from hc_core (row-level tables are sampled, monthly tables use the full history)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc7_lists import *
import collections, datetime as _dt

R = rng('hc7')
dd = to_date
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def r2(x): return round(x + 1e-9, 2)
def r3(x): return round(x + 1e-9, 3)
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows

ST = story()
CL = client_rows(); CLD = {c['client_id']: c for c in CL}; CLN = {c['client']: c for c in CL}
ACT = [c for c in CL if c['status'] == 'Active']
CG = caregiver_rows()
V = [v for v in visit_rows() if v['status'] in ('Completed', 'Late') and v['date'] <= iso(TODAY)]
JAN1 = iso(_dt.date(TODAY.year, 1, 1)); NEXT_JAN1 = iso(_dt.date(TODAY.year + 1, 1, 1)); NEXT_FEB1 = iso(_dt.date(TODAY.year + 1, 2, 1)); DEC15 = iso(_dt.date(TODAY.year, 12, 15))
TARGET = TARGET_MARGIN

# ---------- locked rates: payer clients (the payer sets the rate) and two long private pay agreements
PRIV_OLD = sorted([c for c in CL if c['payer'] == 'Private pay' and c['status'] == 'Active' and c['client_id'] != ST['below_cost_client']], key=lambda c: c['start_date'])[:2]
LOCKED = {c['client_id'] for c in CL if c['payer'] != 'Private pay'} | {c['client_id'] for c in PRIV_OLD}

# ---------- 90-day sums per client
LO90 = ago(90)
A90 = collections.defaultdict(lambda: collections.defaultdict(float))
for v in V:
    if v['date'] >= LO90:
        a = A90[v['client_id']]
        for k in ('billed_hours', 'actual_hours', 'charge', 'pay', 'travel_pay', 'mileage_pay', 'overtime_pay', 'cover_premium', 'burden', 'cost', 'travel_min', 'distance_km'): a[k] += v[k]
        a['n'] += 1
        if v['actual_hours'] < CLD[v['client_id']]['min_visit_hours'] - 1e-9: a['short'] += 1

MG = {}
for c in ACT:
    a = A90[c['client_id']]; h = a['billed_hours']
    if h <= 0: continue
    loaded = (a['pay'] + a['travel_pay'] + a['overtime_pay'] + a['cover_premium']) * (1 + PAYROLL_BURDEN) + a['mileage_pay']
    MG[c['client_id']] = dict(rate=a['charge'] / h, cost_h=loaded / h, share=(a['charge'] - loaded) / a['charge'], hours=c['weekly_hours'])

# ---------- Client Margin
def margin_d():
    rows = []
    for i, c in enumerate(ACT):
        a = A90[c['client_id']]; h = a['billed_hours']
        if h <= 0: continue
        rows.append(nb(dict(client_id=c['client_id'], client=c['client'], payer=key('payer', c['payer']), service=key('svc', c['service']), area=key('area', c['area']), weekly_hours=c['weekly_hours'],
                            bill_rate=r2(a['charge'] / h), pay_hour=r2(a['pay'] / h), travel_hour=r3(a['travel_pay'] / h), mileage_hour=r3(a['mileage_pay'] / h), ot_hour=r3(a['overtime_pay'] / h),
                            cover_hour=r3(a['cover_premium'] / h), review_on=ago(R.randint(4, 75)) if i % 5 else ahead(R.randint(3, 25)))))
    rows.sort(key=lambda r: MG[r['client_id']]['share'])
    return front(rows, lambda r: r.get('ot_hour', 0) > 0 and r.get('cover_hour', 0) > 0)

# ---------- Client Months (two of every three client months of the last 14 months)
def cmonths_d():
    first = iso(month_start(13)); out = []
    for r in client_month_rows():
        if r['month'] < first: continue
        mi = (dd(r['month']).year * 12 + dd(r['month']).month); ci = int(r['client_id'][3:])
        if (mi + ci) % 3 == 0: continue
        out.append(nb(dict(month_id=r['row_id'], month=r['month'], client=r['client'], service=key('svc', r['service']), payer=key('payer', r['payer']), area=key('area', r['area']),
                           billed_hours=r['billed_hours'], revenue=r['revenue'], cost=r['cost'], travel_cost=r['travel_cost'], overtime_cost=r['overtime_cost'], late_visits=r['late_visits'],
                           missed_visits=r['missed_visits'], caregivers=r['caregivers'])))
    return front(out, lambda r: r['revenue'] > 0 and r.get('overtime_cost', 0) > 0 and r['month'] >= iso(month_start(2)))

# ---------- Visits with margin (the 800 most recent completed or late visits)
def visits_d():
    rows = []
    for v in V[-800:]:
        rows.append(nb(dict(visit_id=v['visit_id'], date=v['date'], client=v['client'], service=key('svc', v['service']), band=key('band', v['band']), caregiver=v['caregiver'],
                            billed_hours=v['billed_hours'], actual_hours=v['actual_hours'], charge=v['charge'], pay=v['pay'], travel_pay=v['travel_pay'], mileage_pay=v['mileage_pay'],
                            overtime_pay=v['overtime_pay'], cover_premium=v['cover_premium'], burden=v['burden'])))
    rows.reverse()
    return front(rows, lambda r: r.get('overtime_pay', 0) > 0 and r.get('cover_premium', 0) > 0) if any(r.get('overtime_pay', 0) > 0 and r.get('cover_premium', 0) > 0 for r in rows) else rows

# ---------- monthly aggregates from the full history
HS = HISTORY_START
def _agg(keyf):
    out = collections.defaultdict(lambda: collections.defaultdict(float))
    for v in V:
        if dd(v['date']) < HS: continue
        a = out[keyf(v)]; a['n'] += 1; a['bh'] += v['billed_hours']; a['rev'] += v['charge']; a['cost'] += v['cost']; a['tm'] += v['travel_min']
        a['tr'] += v['travel_pay'] + v['mileage_pay']; a['ot'] += v['overtime_pay']
    return out

def svcmonth_d():
    ex = {(r['month'], r['service']): r for r in service_month_rows()}
    agg = _agg(lambda v: (v['month'], v['service'])); rows = []
    for (m, s), r in sorted(ex.items()):
        a = agg[(m, s)]
        rows.append(dict(month_id=r['row_id'].replace('SM-', 'SM-'), month=m, service=key('svc', s), visits=r['visits'], billed_hours=r['billed_hours'], revenue=r['revenue'], cost=r['cost'],
                         travel_cost=r2(a['tr']), overtime_cost=r2(a['ot'])))
    return rows

def areamonth_d():
    agg = _agg(lambda v: (v['month'], v['area'])); rows = []
    for i, ((m, ar), a) in enumerate(sorted(agg.items(), key=lambda kv: (kv[0][0], AREAS.index(kv[0][1]))), 1):
        rows.append(dict(month_id='AM-%03d' % i, month=m, area=key('area', ar), visits=int(a['n']), billed_hours=r2(a['bh']), revenue=r2(a['rev']), cost=r2(a['cost']), travel_min=int(a['tm'])))
    return rows

def paymonth_d():
    agg = _agg(lambda v: (v['month'], CLD[v['client_id']]['payer'])); rows = []
    for i, ((m, p), a) in enumerate(sorted(agg.items(), key=lambda kv: (kv[0][0], PAYERS.index(kv[0][1]))), 1):
        rows.append(dict(month_id='YM-%03d' % i, month=m, payer=key('payer', p), billed_hours=r2(a['bh']), revenue=r2(a['rev']), cost=r2(a['cost'])))
    return front(rows, lambda r: r['month'] >= iso(month_start(3)) and r['payer'] == key('payer', 'Care insurer'))

def ratecard_d():
    return [dict(rate_id=r['rate_id'], service=key('svc', r['service']), band=key('band', r['band']), bill_rate=r['bill_rate'], pay_rate=r['pay_rate']) for r in rate_card]

# ---------- clients
def clients_d():
    rows = []
    for c in CL:
        rows.append(nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], payer=key('payer', c['payer']), service=key('svc', c['service']), area=key('area', c['area']),
                            weekly_hours=c['weekly_hours'], bill_rate=c['bill_rate'], min_visit_hours=c['min_visit_hours'], start_date=c['start_date'], status=key('clstatus', c['status']),
                            end_date=c['end_date'], end_reason=key('endrsn', c['end_reason']) if c['end_reason'] else '', rate_locked=yn(c['client_id'] in LOCKED))))
    return front(rows, lambda r: r['status'] == key('clstatus', 'Active') and r['payer'] == key('payer', 'Private pay'))

# ---------- rate rise proposals
def _risk(c, pct):
    r = rng('risk' + c['client_id']).random(); ten = (T0 - dd(c['start_date'])).days
    lvl = 0 if r < 0.50 else 1 if r < 0.83 else 2
    if ten > 540: lvl = max(0, lvl - 1)
    if pct >= 0.06: lvl = min(2, lvl + 1)
    return ['low', 'medium', 'high'][lvl]
def rise_pct(c):
    if c['client_id'] in LOCKED: return 0.0
    m = MG[c['client_id']]
    if m['share'] >= TARGET: return 0.03
    need = m['cost_h'] / ((1 - TARGET) * m['rate']) - 1
    return min(0.08, max(0.02, round(need * 200) / 200))
RISE_PCT = {c['client_id']: rise_pct(c) for c in ACT if c['client_id'] in MG}
def rises_d():
    rows = []
    for i, c in enumerate(ACT):
        if c['client_id'] not in MG: continue
        p = RISE_PCT[c['client_id']]; eff = [NEXT_JAN1, NEXT_JAN1, DEC15, NEXT_FEB1][i % 4]
        sent = eff == DEC15 or (i % 3 == 0 and p > 0)
        rows.append(nb(dict(client_id=c['client_id'], client=c['client'], rise_pct=p, risk=_risk(c, p), effective_on=eff, notice_on=ago(R.randint(2, 12)) if sent and p > 0 else '',
                            family_phone=fake_phone(300 + i) if i % 2 == 0 else '')))
    rows.sort(key=lambda r: MG[r['client_id']]['share'])
    return front(rows, lambda r: r['rise_pct'] > 0 and r.get('notice_on') and r.get('family_phone'))

# ---------- rate rise history (about 40 rows)
def risehist_d():
    rows = []; n = 0
    def add(c, date, new, old, hold=None):
        nonlocal n
        n += 1; rr = rng('rh' + c['client_id'] + date).random()
        left_after = c['status'] == 'Ended' and c['end_reason'] == 'Price' and c['end_date'] and 0 < (dd(c['end_date']) - dd(date)).days < 150
        out = 'left' if left_after else ('hours_cut' if rr > 0.90 else 'negotiated' if rr > 0.78 else 'accepted')
        hrs = c['weekly_hours']; after = 0.0 if out == 'left' else (float(round(hrs * 0.75)) if out == 'hours_cut' else hrs)
        rows.append(dict(rise_id='RH-%03d' % n, client=c['client'], date=date, old_rate=old, new_rate=new, outcome=out, hours_before=hrs, hours_after=after))
    ok = lambda c, d: c['client_id'] not in LOCKED and dd(c['start_date']) < dd(d) - _dt.timedelta(days=120) and (not c['end_date'] or dd(c['end_date']) > dd(d))
    pool = [c for c in CL if c['payer'] == 'Private pay' and c['client_id'] != ST['below_cost_client']]
    a_ = [c for c in pool if ok(c, JAN1)]
    for c in a_[:26]: add(c, JAN1, c['bill_rate'], r2(c['bill_rate'] / 1.04))
    d2 = iso(dd(JAN1) - _dt.timedelta(days=184))  # mid of last year
    for c in [x for x in pool if ok(x, d2)][:12]: add(c, d2, r2(c['bill_rate'] / 1.04), r2(c['bill_rate'] / 1.04 / 1.03))
    # price leavers get their own entry when they were not already included
    have = {r['client'] for r in rows}
    for c in CL:
        if c['status'] == 'Ended' and c['end_reason'] == 'Price' and c['client'] not in have and c['client_id'] not in LOCKED and c['end_date']:
            d = iso(max(HS, dd(c['end_date']) - _dt.timedelta(days=60)))
            if dd(c['start_date']) < dd(d): add(c, d, c['bill_rate'], r2(c['bill_rate'] / 1.04))
    rows.sort(key=lambda r: r['date'])
    out = []
    for i, r in enumerate(rows, 1):
        r['rise_id'] = 'RH-%03d' % i; r['outcome'] = key('outcome', {'accepted': 'Accepted', 'negotiated': 'Negotiated', 'hours_cut': 'Hours cut', 'left': 'Left'}[r['outcome']])
        out.append(r)
    return front(out, lambda r: r['outcome'] == key('outcome', 'Accepted'))

# ---------- growth, starts, ends, reasons, forecast
GR = growth_rows()
def growth_d():
    return [dict(month_id=r['row_id'], month=r['month'], clients_started=r['clients_started'], clients_ended=r['clients_ended'], hours_added=r['hours_added'], hours_lost=r['hours_lost'],
                 active_clients=r['active_clients'], weekly_hours_end=r['weekly_hours_end'], churn_rate=r['churn_rate']) for r in GR]

def starts_d():
    rows = []
    for c in CL:
        if dd(c['start_date']) < HS: continue
        r = rng('st' + c['client_id']).random(); h0 = c['weekly_hours']; h90 = ''
        full = (not c['end_date'] or (dd(c['end_date']) - dd(c['start_date'])).days >= 90) and (T0 - dd(c['start_date'])).days >= 90
        if full: h90 = h0 + (R.choice([2, 3]) if r < 0.22 else -R.choice([2, 3]) if r < 0.42 and h0 >= 8 else 0)
        rows.append(nb(dict(client_id=c['client_id'], client=c['client'], start_date=c['start_date'], hours_start=h0, hours_90=h90, source=key('enqsrc', c['source']))))
    rows.sort(key=lambda r: r['start_date'])
    return front(rows, lambda r: r.get('hours_90') not in (None, '') and r['hours_90'] != r['hours_start'])

def ends_d():
    rows = []
    for c in CL:
        if c['status'] != 'Ended': continue
        rows.append(dict(client_id=c['client_id'], client=c['client'], end_date=c['end_date'], hours_lost=c['weekly_hours'], reason=key('endrsn', c['end_reason'])))
    rows.sort(key=lambda r: r['end_date'])
    return front(rows, lambda r: r['reason'] == key('endrsn', 'Price'))

def reasons_d():
    agg = collections.defaultdict(lambda: [0, 0.0])
    for c in CL:
        if c['status'] != 'Ended': continue
        m = iso(dd(c['end_date']).replace(day=1)); a = agg[(m, c['end_reason'])]; a[0] += 1; a[1] += c['weekly_hours']
    return [dict(reason_id='CR-%03d' % i, month=m, reason=key('endrsn', rs), clients=a[0], hours_lost=a[1]) for i, ((m, rs), a) in enumerate(sorted(agg.items()), 1)]

L6 = GR[-7:-1]
BASE_NEW = round(sum(r['hours_added'] for r in L6) / 6, 1); BASE_LOST = round(sum(r['hours_lost'] for r in L6) / 6, 1)
def forecast_d():
    rows = []; n = 0
    for sc, fn, fl in (('Base', 1.0, 1.0), ('Best', 1.25, 0.8), ('Worst', 0.75, 1.25)):
        for k in range(1, 7):
            n += 1; m = iso(month_start(-k))
            rows.append(dict(fc_id='FC-%02d' % n, month=m, scenario=key('scen', sc), new_hours=round(BASE_NEW * fn, 1), lost_hours=round(BASE_LOST * fl, 1)))
    return rows

# ---------- pay scenarios
TURN = [-0.03, -0.04, -0.05, -0.05, -0.06, -0.065, -0.07, -0.08, -0.09, -0.095, -0.10, -0.105]
COVERS = [0.10, 0.10, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.80, 1.0]
def payscen_d():
    return [dict(scenario_id='PS-%02d' % (i + 1), step=key('step', STEPS[i]), pay_rise=STEP_VALUES[i], covers=COVERS[i], turnover_change=TURN[i]) for i in range(12)]

# ---------- caregiver pay rates and the team
def paycg_d():
    rows = []; n = 0
    act = [g for g in CG if g['status'] != 'Left']
    low = sorted([g for g in act if g['employment'] != 'Live-in' and (T0 - dd(g['hire_date'])).days > 200], key=lambda g: g['pay_rate'])[:15]
    pick = {g['caregiver_id'] for g in low}
    for g in CG:
        up = g['caregiver_id'] in pick
        rows.append(nb(dict(caregiver_id=g['caregiver_id'], name=g['name'], phone=g['phone'], employment=key('emp', g['employment']), pay_rate=g['pay_rate'], hire_date=g['hire_date'],
                            status=key('cgstatus', g['status']), new_pay_rate=r2(g['pay_rate'] + (0.5 if g['pay_rate'] < 18 else 0.75)) if up else '', change_on=NEXT_JAN1 if up else '')))
    return front(rows, lambda r: r.get('new_pay_rate') and r['status'] == key('cgstatus', 'Active'))

def team_d():
    return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'],
                 hours_week=t['hours_week'], monthly_salary=t['monthly_salary'], hourly_rate=t['hourly_rate'], speciality=t['speciality'], country=t['country'], start=t['start']) for t in team]

# ---------- minimum visit check and overtime, travel and cover by client
MV = {}
def minvisit_d():
    rows = []
    for i, c in enumerate(ACT):
        a = A90[c['client_id']]
        if a['n'] <= 0: continue
        n = a['n']
        pr = a['pay'] / a['actual_hours'] if a['actual_hours'] else 18.0
        row = dict(client_id=c['client_id'], client=c['client'], min_visit_hours=c['min_visit_hours'], visits_90=int(n), visits_min=int(a['short']), avg_hours=r2(a['actual_hours'] / n), avg_billed=r2(a['billed_hours'] / n),
                   avg_travel_min=round(a['travel_min'] / n, 1), avg_km=round(a['distance_km'] / n, 1), pay_rate=r2(pr), reviewed_on=ago(R.randint(8, 160)))
        rate = a['charge'] / a['billed_hours']
        cost_v = ((row['avg_hours'] + row['avg_travel_min'] / 60) * pr) * (1 + PAYROLL_BURDEN) + row['avg_km'] * MILEAGE_RATE
        rev_v = row['avg_billed'] * rate; row['_m'] = (rev_v - cost_v) / rev_v if rev_v else 0
        MV[c['client_id']] = row['_m']; rows.append(row)
    worst = sorted(rows, key=lambda r: r['_m'])[:12]
    for r in worst:
        if r['visits_min'] / r['visits_90'] >= 0.25: r['new_min_visit'] = r['min_visit_hours'] + 1; r['change_on'] = NEXT_JAN1
    for r in rows: del r['_m']
    rows.sort(key=lambda r: MV[r['client_id']])
    return front([nb(r) for r in rows], lambda r: r.get('new_min_visit') is not None)

def otravel_d():
    rows = []
    for c in ACT:
        a = A90[c['client_id']]
        if a['billed_hours'] <= 0: continue
        rows.append(dict(client_id=c['client_id'], client=c['client'], period_end=iso(T0), hours=r2(a['billed_hours']), revenue=r2(a['charge']), overtime_cost=r2(a['overtime_pay']),
                         travel_pay=r2(a['travel_pay']), mileage_pay=r2(a['mileage_pay']), cover_cost=r2(a['cover_premium'])))
    rows.sort(key=lambda r: -(r['overtime_cost'] + r['travel_pay'] + r['mileage_pay'] + r['cover_cost']) / r['revenue'])
    return front(rows, lambda r: r['overtime_cost'] > 0 and r['cover_cost'] > 0)

# ---------- numbers the tools and messages start from
HOLIDAY = next(h for h in holidays if h['date'] >= iso(TODAY))
WEAK = [r['client'] for r in margin_d()[:8]]
if __name__ == '__main__':
    for nm in ('margin', 'cmonths', 'visits', 'svcmonth', 'areamonth', 'paymonth', 'ratecard', 'clients', 'rises', 'risehist', 'growth', 'starts', 'ends', 'reasons', 'forecast', 'payscen', 'paycg', 'team', 'minvisit', 'otravel'):
        rows = globals()[nm + '_d'](); print(nm, len(rows), rows[0])
    print(BASE_NEW, BASE_LOST, HOLIDAY, WEAK)
