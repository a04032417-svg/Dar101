"""Home care agency suite part 4: demo rows built from hc_core (row-level tables are thinned samples, monthly and period tables use the full generator output)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc4_lists import *
import collections, datetime as _dt

dd = to_date
T0 = TODAY
TODAY_S = iso(TODAY)
def day(n): return _dt.timedelta(days=n)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def z(x):
    return None if (x is None or x == '' or abs(x) < 1e-9) else x
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows

ST = story()
CG = caregiver_rows(); CGI = {r['caregiver_id']: r for r in CG}; CGN = {r['name']: r for r in CG}
PR = payroll_rows(); HW = hours_rows(); VS = visit_rows(); WK = {r['week']: r for r in week_rows()}
PERIODS = sorted({(r['period_start'], r['period_end'], r['pay_date']) for r in PR})
PER_ROWS = collections.defaultdict(list)
for _r in PR: PER_ROWS[_r['period_start']].append(_r)
MON = lambda d: iso(week_start(dd(d)))
def period_of(d):
    for p in PERIODS:
        if p[0] <= d <= p[1]: return p
    return None
TEAM_NAMES = {t['role']: t['name'] for t in team}

# ---------- caregivers (50)
def caregivers_d():
    rows = [nb(dict(caregiver_id=r['caregiver_id'], name=r['name'], employment=key('emp', r['employment']), pay_rate=r['pay_rate'], hire_date=r['hire_date'], hours_limit=r['hours_limit'],
                    status=key('cgstatus', r['status']), area=key('area', r['area']), left_date=r['left_date'], phone=r['phone'])) for r in CG]
    return rows

# ---------- pay run lines (the last 21 pay periods)
_SPARSE = ['overtime_hours', 'holiday_hours', 'travel_hours', 'distance_km', 'overtime_pay', 'holiday_premium', 'travel_pay', 'mileage_pay', 'cover_premium', 'bonus', 'deductions']
def payrun_d():
    sel = {p[0] for p in PERIODS[-21:]}
    rows = []
    for r in PR:
        if r['period_start'] not in sel: continue
        d = dict(pay_id=r['pay_id'], period_start=r['period_start'], period_end=r['period_end'], pay_date=r['pay_date'], caregiver=r['caregiver'], employment=key('emp', r['employment']),
                 regular_hours=r['regular_hours'], regular_pay=r['regular_pay'], status=key('paystat', r['status']))
        for k in _SPARSE: d[k] = z(r[k])
        rows.append(nb(d))
    score = lambda r: sum(1 for k in _SPARSE if k in r)
    best = max(range(len(rows)), key=lambda i: (score(rows[i]) - (1 if rows[i].get('status') != key('paystat', 'Paid') else 0), -i))
    return [rows[best]] + rows[:best] + rows[best + 1:]

# ---------- time sheets (about 300)
def timesheets_d():
    rows = []; ap = rng('hc4ts')
    sel = [p for p in PERIODS[-21:] if p[0] != '2026-11-09']
    for pi, p in enumerate(sel):
        for i, r in enumerate(PER_ROWS[p[0]]):
            due = p[0] == '2026-10-26'
            if not due and (i + pi) % 2: continue
            rr = rng('ts' + r['pay_id']); chk = round(r['regular_hours'] + r['overtime_hours'], 2); x = rr.random()
            ent = chk if x < .62 else round(chk + rr.choice([-0.5, -0.25, 0.25, 0.25, 0.5, 0.5]), 2) if x < .88 else round(chk + rr.choice([-3, -2, 1.5, 2, 2.5, 4]), 2)
            ent = max(ent, 0.5)
            by = rr.choices(['Priyanka Nair', 'Tomasz Kowalski', 'Joaquin Ramirez', 'Amara Diallo'], [60, 22, 10, 8])[0]
            ao = iso(dd(p[2]) - day(rr.randint(2, 4)))
            if due and (i % 6 == 4 or abs(ent - chk) > 1.2): ao = ''
            rows.append(nb(dict(caregiver=r['caregiver'], period_start=p[0], period_end=p[1], hours_entered=ent, hours_checkins=chk, approved_by='' if not ao else by, approved_on=ao)))
    if len(rows) > 330:
        keep = [r for r in rows if r['period_start'] == '2026-10-26']; other = [r for r in rows if r['period_start'] != '2026-10-26']
        stp = len(other) / float(300 - len(keep)); other = [other[int(i * stp)] for i in range(300 - len(keep))]
        rows = sorted(other + keep, key=lambda r: (r['period_start'], r['caregiver']))
    rows = [dict(sheet_id='TS-%04d' % (i + 1), **r) for i, r in enumerate(rows)]
    return front(rows, lambda r: r.get('approved_on') and r['hours_entered'] == r['hours_checkins'])

# ---------- pay periods (52)
def payperiods_d():
    rows = []
    for i, p in enumerate(PERIODS):
        rs = PER_ROWS[p[0]]
        billed = sum(WK[w]['billed_hours'] for w in (p[0], iso(dd(p[0]) + day(7))) if w in WK)
        rows.append(nb(dict(period_id='PP-%03d' % (i + 1), period_start=p[0], period_end=p[1], pay_date=p[2], status=key('paystat', rs[0]['status']),
                            hours=round(sum(r['regular_hours'] + r['overtime_hours'] for r in rs), 2), total_cost=round(sum(r['total_cost'] for r in rs), 2), caregivers_paid=len(rs),
                            travel_pay=round(sum(r['travel_pay'] for r in rs), 2), mileage_amount=round(sum(r['mileage_pay'] for r in rs), 2),
                            cover_premium=round(sum(r['cover_premium'] for r in rs), 2), billed_hours=round(billed, 2))))
    return front(rows, lambda r: r['period_start'] == '2026-10-26')

# ---------- overtime forecast (38 caregivers, the week of the story)
def otforecast_d():
    wk = ST['overtime_week']; sched = {r['caregiver_id']: r['scheduled_hours'] for r in HW if r['week'] == wk}
    rows = []
    for r in CG:
        if r['status'] == 'Left': continue
        h = sched.get(r['caregiver_id'], 0.0); so = round(h * 0.45 * 4) / 4 if h else 0.0
        rows.append(nb(dict(caregiver_id=r['caregiver_id'], caregiver=r['name'], week=wk, worked_so_far=z(so), still_scheduled=z(round(h - so, 2)), hours_limit=r['hours_limit'])))
    rows.sort(key=lambda x: -((x.get('worked_so_far') or 0) + (x.get('still_scheduled') or 0)))
    return rows

# ---------- overtime moves (about 40)
_ACTIVE_ON = lambda cg, wk: cg['hire_date'] <= wk and (not cg['left_date'] or cg['left_date'] > wk)
def otmoves_d():
    sched = collections.defaultdict(dict)
    for r in HW: sched[r['week']][r['caregiver_id']] = r['scheduled_hours']
    byvisit = collections.defaultdict(list)
    for v in VS:
        if v['planned_id'] and v['status'] not in ('Cancelled',) and 2 <= v['sched_hours'] <= 6: byvisit[(v['week'], v['planned_id'])].append(v)
    cands = sorted([(r['week'], r['caregiver_id'], r['scheduled_hours']) for r in HW if r['scheduled_hours'] >= 41 and r['week'] <= ST['overtime_week'] and r['week'] >= ago(420)])
    cur = [c for c in cands if c[0] == ST['overtime_week']]
    old = [c for c in cands if c[0] != ST['overtime_week']]
    step = max(1, len(old) // 38); pick = old[::step][:38] + cur
    rows = []
    for n, (wk, cid, fh) in enumerate(pick):
        vs = byvisit.get((wk, cid))
        if not vs: continue
        rr = rng('mv%s%s' % (wk, cid)); v = vs[rr.randrange(len(vs))]
        pool = [(sched[wk].get(c['caregiver_id'], 0.0), c) for c in CG if c['caregiver_id'] != cid and _ACTIVE_ON(c, wk) and c['status'] != 'On leave' and c['employment'] != 'Live-in']
        same = [x for x in pool if x[1]['area'] == v['area'] and 12 <= x[0] <= 33] or [x for x in pool if 12 <= x[0] <= 33] or [x for x in pool if x[0] <= 33]
        if n % 7 == 5: same = [x for x in pool if 37 <= x[0] <= 39.9] or same
        if not same: continue
        same.sort(key=lambda x: (abs(x[0] - 24) if n % 7 != 5 else -x[0], x[1]['caregiver_id'])); th, tc = same[0]
        rows.append(nb(dict(visit_id=v['visit_id'], visit_date=v['date'], from_caregiver=CGI[cid]['name'], to_caregiver=tc['name'], hours=v['sched_hours'], from_hours=fh, to_hours=th)))
    for i, r in enumerate(rows): r['move_id'] = 'MV-%03d' % (i + 1)
    rows = [{'move_id': r.pop('move_id'), **r} for r in rows]
    return rows

# ---------- caregiver hours by week (about 600)
def hoursweek_d():
    out = []
    for i, r in enumerate(HW):
        if r['week'] > TODAY_S: continue
        if i % 5 == 0 or (r['overtime_hours'] > 4 and r['week'] >= ago(150)):
            out.append(nb(dict(row_id=r['row_id'], caregiver=r['caregiver'], week=r['week'], scheduled_hours=r['scheduled_hours'], worked_hours=z(r['worked_hours']), travel_hours=z(r['travel_hours']),
                               overtime_hours=z(r['overtime_hours']), visits=r['visits'])))
    return out

# ---------- overtime by month (24)
def otmonth_d():
    g = collections.defaultdict(lambda: [0.0, 0.0, 0.0, set()])
    for r in PR:
        m = g[r['month']]; m[0] += r['regular_hours'] + r['overtime_hours']; m[1] += r['overtime_hours']; m[2] += r['overtime_pay']
        if r['overtime_hours'] > 0: m[3].add(r['caregiver_id'])
    return [nb(dict(row_id='OM-%02d' % (i + 1), month=k, hours=round(v[0], 1), overtime_hours=round(v[1], 1), overtime_pay=round(v[2], 2), caregivers_ot=len(v[3]))) for i, (k, v) in enumerate(sorted(g.items()))]

# ---------- holidays (26) and holiday pay history
_HV = collections.defaultdict(lambda: [0, 0.0, 0, 0.0, 0.0, 0.0])
_HD = {h['date'] for h in holidays}
for _v in VS:
    if _v['date'] in _HD:
        a = _HV[_v['date']]; a[0] += 1; a[1] += _v['sched_hours']
        if _v['actual_hours'] > 0: a[2] += 1; a[3] += _v['actual_hours']; a[4] += _v['holiday_premium']; a[5] += _v['charge']
def holidays_d():
    rows = []; names = [r['name'] for r in CG if r['status'] == 'Active']; prev = {}
    for i, h in enumerate(holidays):
        a = _HV.get(h['date'])
        if a and a[0]: cnt, hrs = a[0], a[1]
        else:
            p = prev.get(h['holiday']); cnt, hrs = (round(p[0] * 1.06), round(p[1] * 1.06)) if p else (30, 100)
        prev[h['holiday']] = (cnt, hrs)
        rows.append(dict(holiday_id=h['holiday_id'], date=h['date'], holiday=key('hol', h['holiday']), weekday=key('wday', h['weekday']), pay_mult=h['pay_mult'], bill_mult=h['bill_mult'],
                         visits_booked=cnt, hours_booked=hrs, notify=names[(i * 7 + 3) % len(names)]))
    return rows
def holpay_d():
    rows = []
    for h in holidays:
        if h['date'] >= TODAY_S: continue
        a = _HV[h['date']]
        rows.append(dict(holiday_id=h['holiday_id'], date=h['date'], holiday=key('hol', h['holiday']), visits=a[2], hours=round(a[3], 1), extra_pay=round(a[4], 2), extra_charge=round(a[5] * (h['bill_mult'] - 1) / h['bill_mult'], 2)))
    return rows

# ---------- payroll cost ratio and burden by month (24 each)
def payratio_d():
    return [dict(row_id='PC-%02d' % (i + 1), month=r['month'], revenue=r['revenue'], billed_hours=r['billed_hours'], caregiver_pay=r['caregiver_pay'], overtime_pay=r['overtime_pay'],
                 travel_mileage=round(r['travel_pay'] + r['mileage_pay'], 2), burden=r['payroll_burden']) for i, r in enumerate(pnl_rows())]
def burden_d():
    out = []
    for i, r in enumerate(pnl_rows()):
        rr = rng('bu%d' % i); tot = r['payroll_burden']; base = round(r['caregiver_pay'] + r['overtime_pay'] + r['travel_pay'], 2)
        tx = round(tot * (0.50 + rr.uniform(-0.02, 0.02)), 2); wi = round(tot * (0.28 + rr.uniform(-0.02, 0.02)), 2); bf = round(tot - tx - wi, 2)
        out.append(dict(row_id='BU-%02d' % (i + 1), month=r['month'], pay_base=base, payroll_taxes=tx, workers_insurance=wi, benefits=bf))
    return out

# ---------- pay rate card (30)
def paycard_d():
    return [dict(service=key('svc', r['service']), band=key('band', r['band']), bill_rate=r['bill_rate'], pay_rate=r['pay_rate']) for r in rate_card]

# ---------- travel and mileage pay (about 400)
def travelpay_d():
    sel = {p[0] for p in PERIODS[-16:]}
    rows = [r for r in PR if r['period_start'] in sel and r['travel_hours'] > 0 and r['distance_km'] > 0]
    out = [nb(dict(period_start=r['period_start'], period_end=r['period_end'], caregiver=r['caregiver'], travel_hours=r['travel_hours'], travel_pay=r['travel_pay'], distance_km=r['distance_km'],
                   mileage_amount=r['mileage_pay'])) for r in rows]
    if len(out) > 420: out = out[::max(1, round(len(out) / 400))]
    for i, r in enumerate(out): r['travel_id'] = 'TP-%03d' % (i + 1)
    return [{'travel_id': r.pop('travel_id'), **r} for r in out]

# ---------- bonuses and deductions
_BK = ['Retention bonus', 'Referral bonus', 'Holiday thank-you']; _DK = ['Advance repaid', 'Uniform and supplies', 'Overpayment recovered', 'Training fee repaid']
_BR = {'Retention bonus': 'Covered short-notice visits for three weeks', 'Referral bonus': 'New caregiver referred and still working after 90 days', 'Holiday thank-you': 'Worked the holiday visits'}
_DR = {'Advance repaid': 'Pay advance repaid in the agreed steps', 'Uniform and supplies': 'Replacement uniform and supplies kit', 'Overpayment recovered': 'Hours paid twice in a previous run, recovered', 'Training fee repaid': 'Course fee repaid after leaving early'}
def adjust_d():
    out = []; nbn = 0
    for r in PR:
        rr = rng('adj' + r['pay_id']); ap = rr.choices(['Priyanka Nair', 'Marguerite Adeyemi', 'Tomasz Kowalski'], [55, 30, 15])[0]
        if r['bonus'] > 0:
            k = _BK[nbn % 3]; nbn += 1; out.append(dict(period_start=r['period_start'], pay_date=r['pay_date'], caregiver=r['caregiver'], kind=key('adjk', k), amount=r['bonus'], reason=_BR[k], approved_by=ap))
        if r['deductions'] > 0:
            k = _DK[int(r['deductions'] * 7 + len(out)) % 4]; out.append(dict(period_start=r['period_start'], pay_date=r['pay_date'], caregiver=r['caregiver'], kind=key('adjk', k), amount=r['deductions'], reason=_DR[k], approved_by=ap))
    for i, r in enumerate(out): r['adjust_id'] = 'BD-%03d' % (i + 1)
    out = [{'adjust_id': r.pop('adjust_id'), **r} for r in out]
    return front(out, lambda r: r['kind'] in (key('adjk', 'Retention bonus'), key('adjk', 'Referral bonus'), key('adjk', 'Holiday thank-you')))

# ---------- pay rate changes (about 70)
def raises_d():
    ev = collections.defaultdict(list); rr = rng('raise')
    for c in CG:
        cid = c['caregiver_id']; h = c['hire_date']; lf = c['left_date'] or '9999'
        if h < '2025-10-01' and lf >= '2026-01-01': ev[cid].append(('2026-01-01', 'Live-in rate update' if c['employment'] == 'Live-in' else 'Yearly review'))
        if h < '2024-10-01' and lf >= '2025-01-01': ev[cid].append(('2025-01-01', 'Yearly review'))
        pd = iso(dd(h) + day(90))
        if h >= '2024-11-01' and pd <= min(lf, TODAY_S): ev[cid].append((pd, 'Probation passed'))
    ids = [c['caregiver_id'] for c in CG]
    for n, (k, lo, hi) in enumerate([('Extra skills', '2026-02-01', '2026-10-31')] * 7 + [('Market adjustment', '2025-06-01', '2026-09-30')] * 5 + [('Correction', '2026-03-01', '2026-10-31')] * 2):
        cid = ids[(n * 11 + 4) % len(ids)]; c = CGI[cid]
        d0 = iso(dd(lo) + day((n * 37) % 150))
        if d0 > max(c['hire_date'], '0') and d0 < (c['left_date'] or '9999') and d0 < TODAY_S and d0 > iso(dd(c['hire_date']) + day(100)): ev[cid].append((d0, k))
    out = []
    for cid, es in ev.items():
        new = CGI[cid]['pay_rate']
        for d0, why in sorted(es, reverse=True):
            step = 0.25 if why == 'Correction' else rng('st%s%s' % (cid, d0)).choice([0.5, 0.5, 0.75, 1.0])
            old = round(new - step, 2); out.append(dict(caregiver=CGI[cid]['name'], date=d0, old_rate=old, new_rate=new, reason=key('raisr', why))); new = old
    out.sort(key=lambda r: (r['date'], r['caregiver']))
    for i, r in enumerate(out): r['change_id'] = 'RC-%03d' % (i + 1)
    return [{'change_id': r.pop('change_id'), **r} for r in out]

# ---------- pay run by employment type
def byemp_d():
    out = []
    for p in PERIODS:
        for e in EMPLOYMENT:
            rs = [r for r in PER_ROWS[p[0]] if r['employment'] == e]
            if rs: out.append(nb(dict(period_start=p[0], period_end=p[1], employment=key('emp', e), caregivers=len(rs), hours=round(sum(r['regular_hours'] + r['overtime_hours'] for r in rs)),
                                      overtime_hours=z(round(sum(r['overtime_hours'] for r in rs), 2)), total_cost=round(sum(r['total_cost'] for r in rs), 2))))
    return out

# ---------- this week and next week visits
def weekvisits_d():
    lo, hi = iso(week_start(T0)), iso(week_start(T0) + day(13))
    return [nb(dict(visit_id=v['visit_id'], date=v['date'], start=v['start'], hours=v['sched_hours'], client=v['client'], band=key('band', v['band']), caregiver=v['caregiver'] if v['status'] != 'Open' else '',
                    status=key('vstatus', v['status']))) for v in VS if lo <= v['date'] <= hi]

# ---------- team (16)
def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'],
                    hours_week=t['hours_week'], monthly_salary=z(t['monthly_salary']), hourly_rate=z(t['hourly_rate']), speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]

# ---------- pre-payroll warnings (about 80)
def warnings_d():
    ev = []  # (found_on, kind, caregiver, period, detail, visit_date, open?)
    last26 = PERIODS[-26:]
    # 1 near the line: real caregiver weeks (schedule hours against the line)
    wk_rows = sorted([r for r in HW if r['scheduled_hours'] >= 39 and ago(360) <= r['week'] < iso(week_start(T0)) and r['caregiver_id'] in CGI], key=lambda r: (r['week'], r['caregiver_id']))
    for r in wk_rows[::max(1, len(wk_rows) // 22)][:22]:
        p = period_of(r['week']) or period_of(iso(dd(r['week']) + day(3)))
        if not p: continue
        ev.append((iso(dd(r['week']) - day(2)), 'Overtime near the line', r['caregiver'], p, '%g hours scheduled against the %d-hour line' % (r['scheduled_hours'], OVERTIME_HOURS), '', False))
    # story: the caregiver above the line next week (still open)
    ev.append((ago(1), 'Overtime near the line', ST['overtime_name'], period_of(ago(0)), '%g hours scheduled against the %d-hour line' % (ST['overtime_hours'], OVERTIME_HOURS), '', True))
    # 2 other kinds, spread over the last 26 pay periods
    for i, p in enumerate(last26):
        rows = PER_ROWS[p[0]]; rr = rng('wn%d' % i)
        for j in range(rr.choice([2, 3, 3, 4])):
            r = rows[rr.randrange(len(rows))]; kind = rr.choices(['Missing check-out', 'Hours mismatch', 'Missing time sheet', 'Negative net pay', 'Rate not set'], [34, 28, 24, 6, 8])[0]
            found = min(iso(dd(p[1]) + day(rr.randint(1, 3))), ago(1)); vd_ = ''
            if kind == 'Missing check-out':
                vd_ = iso(dd(p[0]) + day(rr.randint(0, 13))); det = 'Visit of %g hours has no check-out time' % rr.choice([2, 3, 3.5, 4, 5])
                vd_ = min(vd_, found)
            elif kind == 'Hours mismatch': det = 'Time sheet %.2f hours against %.2f hours from check-ins' % (r['regular_hours'] + rr.choice([1.5, 2, 2.5, 3]), r['regular_hours'])
            elif kind == 'Missing time sheet': det = 'Time sheet not received before the pay run cut-off'
            elif kind == 'Negative net pay': det = 'Deduction of %d is larger than gross pay of %.2f' % (round(r['gross_pay']) + rr.choice([20, 35, 60]), r['gross_pay'])
            else: det = 'Pay rate missing for a new caregiver in the first pay run'
            ev.append((found, kind, r['caregiver'], p, det, vd_, False))
    ev.sort(key=lambda e: e[0])
    # keep about 80, dropping some of the older ones evenly
    story_rows = [e for e in ev if e[6]]; rest = [e for e in ev if not e[6]]
    if len(rest) > 79:
        stp = len(rest) / 79.0; rest = [rest[int(i * stp)] for i in range(79)]
    ev = sorted(rest + story_rows, key=lambda e: e[0])
    # the open ones: the story, the newest periods
    open_idx = {i for i, e in enumerate(ev) if e[6]}
    recent = [i for i, e in enumerate(ev) if e[0] >= ago(8) and not e[6]]
    open_idx |= set(recent[:6])
    out = []
    for i, (found, kind, cg, p, det, vdt, _) in enumerate(ev):
        fx = '' if i in open_idx else min(iso(dd(found) + day(1 + (i * 5) % 4)), ago(0))
        if fx and fx < found: fx = found
        out.append(nb(dict(warning_id='WN-%03d' % (i + 1), period_start=p[0], period_end=p[1], caregiver=cg, kind=key('wkind', kind), detail=det, visit_date=vdt, found_on=found, fixed_on=fx)))
    return front(out, lambda r: r.get('fixed_on') and r.get('visit_date'))

if __name__ == '__main__':
    for f in [caregivers_d, payrun_d, timesheets_d, payperiods_d, otforecast_d, otmoves_d, hoursweek_d, otmonth_d, holidays_d, holpay_d, payratio_d, burden_d, paycard_d, travelpay_d, adjust_d, raises_d, byemp_d, weekvisits_d, team_d, warnings_d]:
        r = f(); print(f.__name__, len(r))
