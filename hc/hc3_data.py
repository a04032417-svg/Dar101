"""Home care suite part 3: demo rows built from hc_core (recent rows for the row-level tables, full history for the aggregated ones)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc3_lists import *
import collections

R = rng('hc3')
TS = iso(TODAY)
WK0 = iso(week_start(TODAY))
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def mins(s): h, m = s.split(':'); return int(h) * 60 + int(m)
def r2(x): return round(x + 1e-9, 2)
def front(rows, pred):
    for i_, r_ in enumerate(rows):
        if pred(r_): return [rows[i_]] + rows[:i_] + rows[i_ + 1:]
    return rows

V = visit_rows(); CGR = caregiver_rows(); CLR = client_rows()
CGEMP = {c['name']: c['employment'] for c in CGR}
CLMIN = {c['client']: c for c in CLR}
def cgname(v): return v['caregiver'] or v['planned']
RECENT = [v for v in V if ago(29) <= v['date'] <= TS]

# ---------- reference tables
def caregivers_d():
    late = collections.Counter(v['caregiver'] for v in V if v['status'] == 'Late' and ago(29) <= v['date'] <= TS)
    rows = [nb(dict(caregiver_id=c['caregiver_id'], name=c['name'], area=key('area', c['area']), employment=key('emp', c['employment']), pay_rate=c['pay_rate'], status=key('cgstatus', c['status']), hire_date=c['hire_date'], phone=c['phone'])) for c in CGR]
    top = max((c for c in CGR if c['status'] == 'Active'), key=lambda c: late[c['name']])['name']
    return front(rows, lambda r: r['name'] == top)
def clients_d():
    return [nb(dict(client_id=c['client_id'], client=c['client'], area=key('area', c['area']), service=key('svc', c['service']), min_visit_hours=c['min_visit_hours'], billing_cycle=key('cycle', c['billing_cycle']),
                    status=key('clstatus', c['status']), phone=c['phone'], bill_rate=c['bill_rate'])) for c in CLR]
def services_d(): return [dict(service=key('svc', s['service']), min_visit_hours=s['min_visit_hours'], bill_rate=s['bill_rate']) for s in services]
def areas_d(): return [dict(area=key('area', a['area']), zone=key('zone', a['zone']), avg_travel_min=a['avg_travel_min']) for a in areas]
def travel_d(): return [dict(from_area=key('area', a), to_area=key('area', b), minutes=m, km=travel_km(a, b)) for (a, b), m in TRAVEL.items()]
def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'],
                    monthly_salary=t['monthly_salary'], hourly_rate=t['hourly_rate'], speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]

# ---------- visit log (last 30 days)
def visits_d():
    out = []
    for v in RECENT:
        reason = v['reason'] if v['status'] in ('Late', 'Missed') else ''
        out.append(nb(dict(visit_id=v['visit_id'], date=v['date'], start=v['start'], sched_hours=v['sched_hours'], client=v['client'], area=key('area', v['area']), service=key('svc', v['service']), band=key('band', v['band']),
                           caregiver=cgname(v), cover=key('cover', v['cover_type']), status=key('vstatus', v['status']), check_in=v['check_in'], check_out=v['check_out'], reason=reason)))
    out = front(out, lambda r: r['status'] == key('vstatus', 'Late') and r.get('reason') and r.get('check_out') and r['date'] >= ago(10))
    for v in V:   # open visits (a visit without a caregiver) stay on the log
        if v['status'] == 'Open':
            out.append(nb(dict(visit_id=v['visit_id'], date=v['date'], start=v['start'], sched_hours=v['sched_hours'], client=v['client'], area=key('area', v['area']), service=key('svc', v['service']), band=key('band', v['band']),
                               cover=key('cover', v['cover_type']), status=key('vstatus', v['status']))))
    return out

# ---------- late and missed register (last 84 days)
LM = [v for v in V if v['status'] in ('Late', 'Missed', 'No check-in') and ago(83) <= v['date'] <= TS]
def register_d():
    out = []
    for v in LM:
        r = rng('reg' + v['visit_id']); late = v['status'] == 'Late'; nci = v['status'] == 'No check-in'; lm = v['late_minutes'] if late else 0
        phoned = v['date'] if (not late or lm >= 30 or r.random() < .25) else ''
        told = (r.random() < .95) if not late else (lm >= 30 and r.random() < .8) or r.random() < .2
        out.append(nb(dict(visit_id=v['visit_id'], date=v['date'], client=v['client'], caregiver=cgname(v), area=key('area', v['area']), status=key('vstatus', v['status']), minutes_late=lm,
                           delay_reason=key('delay', v['reason']) if late else '', miss_reason=key('miss', v['reason']) if not (late or nci) else '', weekday=key('wday', v['weekday']),
                           employment=key('emp', CGEMP.get(cgname(v), 'Hourly')), phoned_on=phoned, client_told=yn(told))))
    return front(out, lambda r: r['status'] == key('vstatus', 'Missed') and r.get('phoned_on') and r['client_told'] == 'yes' and r['date'] >= ago(30))

# ---------- today's check-ins (today plus the first visits of tomorrow)
def today_d():
    td = [v for v in V if v['date'] == TS]
    tm = sorted([v for v in V if v['date'] == ahead(1)], key=lambda v: (v['start'], v['visit_id']))[:25]
    out = []
    for v in sorted(td, key=lambda v: (v['start'], v['visit_id'])) + tm:
        out.append(nb(dict(visit_id=v['visit_id'], date=v['date'], start=v['start'], client=v['client'], area=key('area', v['area']), caregiver=cgname(v), status=key('vstatus', v['status']),
                           check_in=v['check_in'], sched_hours=v['sched_hours'], arrives_by={'VS-20954': '11:20', 'VS-20955': '11:40'}.get(v['visit_id'], ''))))
    return front(out, lambda r: r['visit_id'] == 'VS-20954') if any(r['visit_id'] == 'VS-20954' for r in out) else front(out, lambda r: r['status'] == key('vstatus', 'No check-in'))

# ---------- caregiver hours by week
def cgweeks_d():
    rows = [h for h in hours_rows() if h['week'] <= WK0 and h['week'] >= iso(week_start(TODAY) - day(7 * 15))]
    return [dict(row_id=h['row_id'], week=h['week'], caregiver=h['caregiver'], employment=key('emp', h['employment']), scheduled_hours=h['scheduled_hours'], worked_hours=h['worked_hours'], travel_hours=h['travel_hours'],
                 overtime_hours=h['overtime_hours'], visits=h['visits'], late_visits=h['late_visits']) for h in rows]

# ---------- agency hours by week (history up to the current week)
_wk = collections.defaultdict(lambda: dict(pay=0.0, hrs=0.0, late=[]))
for v in V:
    if v['status'] in ('Completed', 'Late'):
        _wk[v['week']]['pay'] += v['pay']; _wk[v['week']]['hrs'] += v['actual_hours']
    if v['status'] == 'Late': _wk[v['week']]['late'].append(v['late_minutes'])
def agencyweeks_d():
    out = []
    for w in week_rows():
        if w['week'] > WK0: continue
        a = _wk[w['week']]
        out.append(dict(row_id=w['row_id'], week=w['week'], month=w['month'], scheduled_hours=w['scheduled_hours'], delivered_hours=w['delivered_hours'], billed_hours=w['billed_hours'], paid_hours=w['paid_hours'],
                        visits=w['visits'], late_visits=w['late_visits'], missed_visits=w['missed_visits'], avg_pay_rate=r2(a['pay'] / a['hrs']) if a['hrs'] else 18.5,
                        avg_late_min=round(sum(a['late']) / len(a['late']), 1) if a['late'] else 0))
    return front(out, lambda r: r['week'] == iso(week_start(TODAY) - day(7)))

# ---------- client hours by month (last 8 months)
def climonths_d():
    m0 = iso(month_start(7))
    return [dict(row_id=r['row_id'], month=r['month'], client=r['client'], service=key('svc', r['service']), billed_hours=r['billed_hours'], delivered_hours=r['delivered_hours'], revenue=r['revenue'],
                 travel_cost=r['travel_cost'], late_visits=r['late_visits'], missed_visits=r['missed_visits']) for r in client_month_rows() if r['month'] >= m0]

# ---------- mileage
MG = mileage_rows()
def mileage_d():
    return [dict(mileage_id=m['mileage_id'], date=m['date'], caregiver=m['caregiver'], client=m['client'], from_area=key('area', m['from_area']), to_area=key('area', m['to_area']), distance_km=m['distance_km'],
                 travel_min=m['travel_min'], travel_pay=m['travel_pay'], mileage_pay=m['mileage_amount']) for m in MG[-500:]]

def pairs_d():
    g = collections.defaultdict(lambda: [0, 0, 0.0, 0.0])
    for m in MG:
        if m['date'] < ago(364) or m['from_area'] == m['to_area']: continue
        x = g[(m['from_area'], m['to_area'])]; x[0] += 1; x[1] += m['travel_min']; x[2] += m['distance_km']; x[3] += m['travel_pay'] + m['mileage_amount']
    out = []
    for i, (a, b) in enumerate(sorted(k for k in TRAVEL if k[0] != k[1]), 1):
        x = g.get((a, b), [0, 0, 0.0, 0.0])
        out.append(dict(pair_id='AP-%02d' % i, from_area=key('area', a), to_area=key('area', b), legs=x[0], minutes=x[1], km=round(x[2], 1), cost=round(x[3], 2)))
    return out

_mg = collections.defaultdict(lambda: [0.0, 0.0, 0.0]); _pay = collections.defaultdict(float)
for m in MG: x = _mg[(m['month'], m['from_area'])]; x[0] += m['distance_km']; x[1] += m['travel_pay']; x[2] += m['mileage_amount']
for v in V:
    if v['status'] in ('Completed', 'Late'): _pay[(v['month'], v['area'])] += v['pay']
def areamonths_d():
    rows = [dict(row_id=a['row_id'], month=a['month'], area=key('area', a['area']), visits=a['visits'], late_visits=a['late_visits'], missed_visits=a['missed_visits'], delivered_hours=a['delivered_hours'],
                 travel_min=a['travel_min'], distance_km=round(_mg[(a['month'], a['area'])][0], 1), travel_pay=round(_mg[(a['month'], a['area'])][1], 2), mileage_pay=round(_mg[(a['month'], a['area'])][2], 2),
                 pay_amount=round(_pay[(a['month'], a['area'])], 2)) for a in area_month_rows()]
    return front(rows, lambda r: r['month'] == iso(month_start(1)) and r['area'] == key('area', story()['problem_area']))

def delays_d():
    g = collections.Counter()
    for v in V:
        if v['status'] == 'Late' and v['date'] <= TS: g[(v['month'], v['reason'])] += 1
    out = []; i = 0
    for m in months14():
        for r_ in DELAY_REASONS:
            i += 1; out.append(dict(row_id='DR-%03d' % i, month=iso(m), reason=key('delay', r_), visits=g[(iso(m), r_)]))
    return out

# ---------- visit corrections (invented from real visits)
COR_REASON = ['Caregiver typed the check-in late', 'Caregiver forgot to check out', 'Wrong start time on the schedule', 'Cover caregiver was not recorded', 'Client confirmed the real time',
              'Time sheet and check-in differed', 'Phone battery was flat, time confirmed by call', 'Visit moved by the client and not updated']
def corrections_d():
    r = rng('cor'); pool = [v for v in V if v['status'] in ('Completed', 'Late') and ago(330) <= v['date'] <= ago(1)]
    recent = [v for v in pool if v['date'] >= ago(29)]; older = [v for v in pool if v['date'] < ago(29)]
    pick = r.sample(recent, 24) + r.sample(older, 56)
    others = [c['name'] for c in CGR]; staff = ['Tomasz Kowalski', 'Priyanka Nair', 'Joaquin Ramirez', 'Amara Diallo']
    out = []
    for v in pick:
        x = r.random()
        if x < .40: f, new, old = 'Check-in time', v['check_in'], '%02d:%02d' % divmod((mins(v['check_in']) + r.choice([-35, -22, -14, 12, 18, 27])) % 1440, 60)
        elif x < .65: f, new, old = 'Check-out time', v['check_out'], '%02d:%02d' % divmod((mins(v['check_out']) + r.choice([-40, -20, 15, 25, 45])) % 1440, 60)
        elif x < .75: f, new, old = 'Start time', v['start'], '%02d:%02d' % divmod((mins(v['start']) + r.choice([30, 60, -30])) % 1440, 60)
        elif x < .90: f, new, old = 'Caregiver', cgname(v), r.choice([n for n in others if n != cgname(v)])
        else: f, new, old = 'Visit status', 'Completed' if v['status'] == 'Completed' else 'Late', 'No check-in'
        d = min(day_add(v['date'], r.choice([0, 1, 1, 2, 3, 5, 8])), TS)
        out.append(dict(date=d, visit_id=v['visit_id'], visit_date=v['date'], client=v['client'], caregiver=cgname(v), field=key('cfield', f), old_value=old, new_value=new, reason=r.choice(COR_REASON),
                        corrected_by=r.choice(staff)))
    out.sort(key=lambda x: (x['date'], x['visit_id']))
    for i, o in enumerate(out, 1): o['correction_id'] = 'VC-%03d' % i
    return [{**{'correction_id': o['correction_id']}, **{k: v for k, v in o.items() if k != 'correction_id'}} for o in out]
def day_add(iso_s, n): return iso(to_date(iso_s) + day(n))

# ---------- client cancellations (the last 150)
CANC = [v for v in V if v['status'] == 'Cancelled' and v['date'] <= TS][-150:]
def cancels_d():
    out = []
    for i, v in enumerate(CANC, 1):
        r = rng('can' + v['visit_id']); x = r.random()
        h = r.randint(48, 120) if x < .36 else r.randint(24, 47) if x < .62 else r.randint(4, 23) if x < .88 else r.randint(0, 3)
        band = 'Two days or more' if h >= 48 else 'One to two days' if h >= 24 else 'Four to 23 hours' if h >= 4 else 'Under four hours'
        charged = h < 24 and r.random() < .8
        out.append(dict(cancel_id='CC-%03d' % i, date=v['date'], visit_id=v['visit_id'], client=v['client'], notice_hours=h, notice_band=key('notice', band), visit_value=r2(v['sched_hours'] * v['bill_rate']), charged=yn(charged)))
    return front(out, lambda r: r['charged'] == 'yes' and r['notice_hours'] < 24)

# ---------- overlong visits
OVER = [v for v in V if v['status'] in ('Completed', 'Late') and v['actual_hours'] - v['sched_hours'] >= 0.25 and v['date'] <= TS]
OVER = OVER[-62:]
OVR = ['Client asked for extra tasks', 'Household task took longer', 'Waiting for a family member to arrive', 'Handover to the next caregiver', 'Late start, finished late', 'Client wanted company a little longer',
       'Shopping trip ran over', 'Visit moved and not updated']
def overlong_d():
    out = []
    for v in OVER:
        r = rng('ovl' + v['visit_id']); agreed = r.random() < .35
        billed = v['billed_hours'] if agreed else v['sched_hours']
        out.append(dict(visit_id=v['visit_id'], date=v['date'], client=v['client'], caregiver=cgname(v), sched_hours=v['sched_hours'], actual_hours=v['actual_hours'], billed_hours=billed, reason=r.choice(OVR), client_agreed=yn(agreed)))
    return front(out, lambda r: r['client_agreed'] == 'no' and r['actual_hours'] - r['billed_hours'] > 0.2)

# ---------- time sheets (last 6 weeks all, earlier weeks sampled)
def timesheets_d():
    hr = [h for h in hours_rows() if h['worked_hours'] > 0 and h['week'] <= WK0]
    wks = sorted({h['week'] for h in hr})[-32:]
    cut = wks[-6]; out = []
    r = rng('ts')
    for w in wks:
        rows = [h for h in hr if h['week'] == w]
        if w < cut: rows = rng('tsw' + w).sample(rows, 3)
        for h in rows:
            rr = rng('tsr' + h['row_id']); x = rr.random(); wk = h['worked_hours']
            if x < .86: ent = wk + rr.choice([0, 0, 0.1, -0.1, 0.2, -0.2])
            elif x < .96: ent = wk + rr.choice([-1.5, -1.0, -0.5, 0.5, 1.0, 1.25, 1.5, 2.0])
            else: ent = wk + rr.choice([-3.0, -2.5, 2.5, 3.5, 4.0])
            ent = round(max(0.0, ent) * 4) / 4 if x >= .86 else round(max(0, ent), 2)
            conf = iso(min(to_date(w) + day(6 + rr.choice([0, 0, 1, 1, 2, 3])), TODAY))
            if w == WK0:
                if rr.random() < .22: ent, conf = '', ''
                else: conf = iso(to_date(w) + day(rr.choice([4, 5, 6])))
            out.append(nb(dict(week=w, caregiver=h['caregiver'], hours_entered=ent, hours_checkins=wk, confirmed_on=conf)))
    for i, o in enumerate(out, 1): o['sheet_id'] = 'TS-%04d' % i
    rows = [{**{'sheet_id': o['sheet_id']}, **{k: v for k, v in o.items() if k != 'sheet_id'}} for o in out]
    return front(rows, lambda r: 'hours_entered' in r and abs(r['hours_entered'] - r['hours_checkins']) > 1.2 and r['week'] == iso(week_start(TODAY) - day(7)))


# ---------- default inputs of the tools, taken from the same data
def _tool_defaults():
    am = area_month_rows(); st = story()
    def ms(k): m = iso(month_start(k)); return (sum(a['visits'] for a in am if a['month'] == m), sum(a['late_visits'] for a in am if a['month'] == m), sum(a['missed_visits'] for a in am if a['month'] == m))
    wk = [w for w in week_rows() if iso(week_start(TODAY) - day(28)) <= w['week'] < WK0]; n = len(wk)
    dh = sum(w['delivered_hours'] for w in wk) / n; bh = sum(w['billed_hours'] for w in wk) / n; ph = sum(w['paid_hours'] for w in wk) / n
    cm = [r for r in client_month_rows() if r['month'] == iso(month_start(1))]
    br = sum(r['revenue'] for r in cm) / sum(r['billed_hours'] for r in cm)
    pr = sum(_wk[w['week']]['pay'] for w in wk) / sum(_wk[w['week']]['hrs'] for w in wk)
    th = sum(sum(v['travel_min'] for v in V if v['week'] == w['week']) / 60 for w in wk) / n
    ov = overlong_d(); ow = max(1.0, (to_date(max(o['date'] for o in ov)) - to_date(min(o['date'] for o in ov))).days / 7)
    oh = sum(max(0, o['actual_hours'] - o['billed_hours']) for o in ov) / ow
    ex_min = sum((o['actual_hours'] - o['sched_hours']) * 60 for o in ov) / len(ov)
    n30 = len([o for o in ov if o['date'] >= ago(29)]); share = sum(1 for o in ov if o['billed_hours'] < o['actual_hours'] - 0.05) / len(ov)
    mis = [v for v in V if v['status'] == 'Missed' and v['reason'] in ('Schedule error', 'Client not home') and v['date'] >= ago(83)]
    mh = sum(v['sched_hours'] for v in mis) / 12
    r30 = [v for v in V if ago(29) <= v['date'] <= TS]
    should = sum(v['status'] in ('Completed', 'Late', 'No check-in') for v in r30)
    mg = [m for m in MG if ago(29) <= m['date'] <= TS]
    cur = ms(0); ly = iso(add_months(month_start(0), -12)); lyv = (sum(a['visits'] for a in am if a['month'] == ly), sum(a['late_visits'] for a in am if a['month'] == ly))
    m3 = [ms(1), ms(2), ms(3)]
    return dict(m3=ms(3), m2=ms(2), m1=ms(1), area=(st['problem_area_visits'], st['problem_area_late'], st['problem_area_missed']),
                agency=(sum(1 for v in V if ago(59) <= v['date'] <= TS), sum(1 for v in V if ago(59) <= v['date'] <= TS and v['status'] == 'Late'), sum(1 for v in V if ago(59) <= v['date'] <= TS and v['status'] == 'Missed')),
                wk=(round(dh, 1), round(bh, 1), round(ph, 1)), br=round(br, 2), pr=round(pr, 2), leak=(round(th, 1), round(oh, 1), round(bh - dh, 1), round(mh, 1)),
                over=(round(ex_min), n30, round(share, 2)), chk=(should, sum(bool(v['check_in']) for v in r30 if v['status'] in ('Completed', 'Late', 'No check-in')), sum(bool(v['check_out']) for v in r30 if v['status'] in ('Completed', 'Late', 'No check-in'))),
                mr=(round(sum(m['distance_km'] for m in mg), 1), len(r30), round(sum(m['travel_pay'] for m in mg), 2), round(sum(v['pay'] for v in r30), 2)),
                cmp=(cur[0], cur[1], sum(x[0] for x in m3), sum(x[1] for x in m3), lyv[0], lyv[1]), visits_month=ms(1)[0], charge_visit=round(sum(v['sched_hours'] * v['bill_rate'] for v in r30) / len(r30), 2),
                wi=(round(sum(v['travel_min'] for v in r30) / len(r30), 1), round(len(r30) / 30), round(sum(v['distance_km'] for v in r30) / len(r30), 1)))
TOOL_DEFAULTS = _tool_defaults()

if __name__ == '__main__':
    for n in ['caregivers_d', 'clients_d', 'visits_d', 'register_d', 'today_d', 'cgweeks_d', 'agencyweeks_d', 'climonths_d', 'mileage_d', 'pairs_d', 'areamonths_d', 'delays_d', 'corrections_d', 'cancels_d', 'overlong_d', 'timesheets_d']:
        d = globals()[n](); print(n, len(d), d[len(d) // 2])
