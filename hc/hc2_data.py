"""Home care suite part 2: demo rows built from hc_core (row-level tables are samples; monthly and weekly tables use the full history)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc2_lists import *
from hc2_lists import _M
import collections, datetime as _dt

R = rng('hc2')
dd = to_date
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def hm(s): h, m = s.split(':'); return int(h) * 60 + int(m)
def mon(d): return iso(week_start(dd(d)) if isinstance(d, str) else week_start(d))

CG = caregiver_rows(); CGN = {g['name']: g for g in CG}; CGI = {g['caregiver_id']: g for g in CG}
CL = client_rows(); CLN = {c['client']: c for c in CL}; CLI = {c['client_id']: c for c in CL}
VIS = visit_rows(); TODAY_S = iso(TODAY)
HR = hours_rows(); WK = week_rows(); AV = availability_rows(); TO = time_off_rows(); CO = calloff_rows(); HOL = holiday_rows()

# ---------- the schedule window: 30 days back to 14 days ahead; a few visits next week become open shifts (the planned caregiver cannot come)
WIN = [dict(v) for v in VIS if ago(30) <= v['date'] <= ahead(14)]
cand = [v for v in WIN if TODAY_S < v['date'] <= ahead(7) and v['status'] == 'Scheduled' and v['cover_type'] == 'Planned' and v['sched_hours'] >= 2]
picked, used_s = [], set()
for off in (1, 1, 2, 3, 3, 4, 5, 6, 7):
    pool = [v for v in cand if v['date'] == ahead(off) and v['visit_id'] not in {p['visit_id'] for p in picked}]
    pool.sort(key=lambda v: (v['service'] in used_s, R.random()))
    if pool: picked.append(pool[0]); used_s.add(pool[0]['service'])
PICK = {p['visit_id'] for p in picked}
for v in WIN:
    if v['visit_id'] in PICK: v.update(caregiver='', cover_type='Uncovered', status='Open')
OPEN_NOW = [v for v in WIN if v['status'] == 'Open']

def sch_row(v):
    return nb(dict(visit_id=v['visit_id'], date=v['date'], start=v['start'], sched_hours=v['sched_hours'], client=v['client'], area=key('area', v['area']), service=key('svc', v['service']),
                   band=key('band', v['band']), planned=v['planned'], caregiver=v['caregiver'], cover_type=key('cover', v['cover_type']), status=key('vstatus', v['status'])))
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows
def schedule_d():
    rows = [sch_row(v) for v in WIN]
    return front(rows, lambda r: r.get('caregiver') and r.get('planned') and r['status'] == key('vstatus', 'Scheduled') and r['date'] > TODAY_S)

# ---------- weekly grids
WEEKS = [iso(week_start(TODAY) + day(7 * k)) for k in range(-5, 3)]          # 5 weeks back .. 2 ahead (8 weeks)
dates_by = collections.defaultdict(set)
vis_by_cw = collections.defaultdict(list)
for v in VIS:
    if v['week'] in WEEKS and v['status'] != 'Cancelled':
        who = v['caregiver']
        if who: dates_by[(who, v['week'])].add(v['date']); vis_by_cw[(who, v['week'])].append(v)
def longest_run(ds):
    s = sorted(dd(x) for x in ds); best = run = 0; prev = None
    for d in s:
        run = run + 1 if prev is not None and (d - prev).days == 1 else 1; best = max(best, run); prev = d
    return best
def grid_cg_d():
    rows = []
    for h in HR:
        if h['week'] in WEEKS and h['scheduled_hours'] > 0:
            g = CGI[h['caregiver_id']]; ds = dates_by.get((h['caregiver'], h['week']), set())
            rows.append(dict(row_id=h['row_id'], week=h['week'], caregiver_id=h['caregiver_id'], caregiver=h['caregiver'], employment=key('emp', h['employment']), area=key('area', g['area']),
                             hours_limit=g['hours_limit'], scheduled_hours=h['scheduled_hours'], days_worked=max(1, len(ds)), longest_run=max(1, longest_run(ds))))
    rows.sort(key=lambda r: (r['week'], r['row_id']))
    return front(rows, lambda r: r['week'] == WEEKS[5] and r['scheduled_hours'] > 36 and r['days_worked'] < 7 and r['longest_run'] >= 3)

# continuity (last 28 days) and client weeks
def visits_of(client_id, lo, hi): return [v for v in VIS if v['client_id'] == client_id and lo <= v['date'] <= hi and v['status'] not in ('Cancelled', 'Open', 'Missed') and v['caregiver']]
def continuity_d():
    rows = []
    for c in CL:
        if c['status'] != 'Active': continue
        vs = visits_of(c['client_id'], ago(28), TODAY_S)
        if not vs: continue
        by = collections.defaultdict(float)
        for v in vs: by[v['caregiver']] += v['sched_hours']
        main = max(by, key=lambda k: (by[k], k))
        rows.append(dict(client_id=c['client_id'], client=c['client'], caregivers_28d=len(by), main_hours=round(by[main], 1), hours=round(sum(by.values()), 1), main_caregiver=main))
    rows.sort(key=lambda r: r['client_id'])
    return front(rows, lambda r: r['caregivers_28d'] == 4)
def grid_cl_d():
    rows, n = [], 0
    for c in CL:
        if c['status'] != 'Active': continue
        for w in WEEKS[2:]:
            vs = [v for v in VIS if v['client_id'] == c['client_id'] and v['week'] == w and v['status'] != 'Cancelled']
            if not vs: continue
            by = collections.defaultdict(float)
            for v in vs: by[v['caregiver'] or v['planned']] += v['sched_hours']
            rows.append(dict(week=w, client=c['client'], scheduled_hours=round(sum(by.values()), 1), caregivers_seen=len(by), main_hours=round(max(by.values()), 1)))
    rows.sort(key=lambda r: (r['week'], r['client']))
    for i, r in enumerate(rows, 1): r['row_id'] = 'CW-%05d' % i
    return front(rows, lambda r: r['week'] == WEEKS[5] and r['caregivers_seen'] >= 3)

# ---------- open shifts and match candidates
def open_row(v, status, filled_on='', filler=''):
    return nb(dict(visit_id=v['visit_id'], date=v['date'], start=v['start'], hours=v['sched_hours'], client=v['client'], area=key('area', v['area']), service=key('svc', v['service']),
                   language=key('lang', CLI[v['client_id']]['language']), status=key('ostatus', status), filled_on=filled_on, caregiver=filler))
def open_pack():
    rows, vmap = [], {}
    now = sorted(OPEN_NOW, key=lambda v: v['date'])
    for i, v in enumerate(now):
        rows.append(open_row(v, 'Offered' if i in (2, 5) else 'Open')); vmap[v['visit_id']] = v
    hist_f = [v for v in VIS if v['cover_type'] == 'Cover' and v['status'] in ('Completed', 'Late') and ago(60) <= v['date'] < TODAY_S]
    hist_n = [v for v in VIS if v['cover_type'] == 'Uncovered' and v['status'] == 'Missed' and ago(150) <= v['date'] < TODAY_S]
    hist_f.sort(key=lambda v: v['date'], reverse=True); hist_n.sort(key=lambda v: v['date'], reverse=True)
    chosen = []
    def cover_need():
        a = {r['area'] for r in rows}; s = {r['service'] for r in rows}
        return [x for x in _M['area'].values() if x not in a], [x for x in _M['svc'].values() if x not in s]
    for pool, status, n in ((hist_f, 'Filled', 18), (hist_n, 'Not filled', 14)):
        for v in pool[:n]:
            lead = R.choice([0, 1, 1, 2, 2, 3, 4, 5]) if status == 'Filled' else 0
            rows.append(open_row(v, status, iso(dd(v['date']) - day(lead)) if status == 'Filled' else '', v['caregiver'] if status == 'Filled' else '')); vmap[v['visit_id']] = v
    for _ in range(40):
        na, ns = cover_need()
        nl = len({r['language'] for r in rows}) < 4
        if not na and not ns and not nl: break
        if nl:
            pl = [v for v in hist_n + hist_f if v['visit_id'] not in vmap and CLI[v['client_id']]['language'] != 'English']
            if pl:
                v = pl[0]; st = 'Not filled' if v['cover_type'] == 'Uncovered' else 'Filled'
                rows.append(open_row(v, st, iso(dd(v['date']) - day(R.choice([1, 2, 3]))) if st == 'Filled' else '', v['caregiver'] if st == 'Filled' else '')); vmap[v['visit_id']] = v
                continue
        pool = [v for v in hist_n + hist_f if v['visit_id'] not in vmap and (key('area', v['area']) in na or key('svc', v['service']) in ns)]
        if not pool: break
        v = pool[0]; st = 'Not filled' if v['cover_type'] == 'Uncovered' else 'Filled'
        rows.append(open_row(v, st, iso(dd(v['date']) - day(R.choice([1, 2, 3]))) if st == 'Filled' else '', v['caregiver'] if st == 'Filled' else '')); vmap[v['visit_id']] = v
    rows.sort(key=lambda r: r['date'])
    return rows, vmap
OPEN_ROWS, OPEN_V = open_pack()
def open_d(): return front(OPEN_ROWS, lambda r: r['status'] == key('ostatus', 'Filled') and r.get('caregiver') and r.get('filled_on'))

def avail_fit(g, v):
    rows = [a for a in AV if a['caregiver_id'] == g['caregiver_id'] and a['weekday'] == v['weekday']]
    if not rows: return 0
    a = rows[0]; s = hm(v['start']); e = s + v['sched_hours'] * 60
    return 100 if hm(a['from_time']) <= s and hm(a['to_time']) >= min(e, 1439) else 50
def fits(g, v):
    c = CLI[v['client_id']]
    skills = 100 if v['service'] in g['skills'] else 0
    area = max(0, 100 - 2 * travel_minutes(g['area'], v['area'])) if g['area'] != v['area'] else 100
    lang = 100 if c['language'] in g['languages'] else 30
    pref = g['name'] in (c['preferred'], c['preferred_2'])
    wk = [h for h in HR if h['caregiver_id'] == g['caregiver_id'] and h['week'] == iso(week_start(dd(v['date'])))]
    booked = wk[0]['scheduled_hours'] if wk else 0.0
    return skills, area, lang, avail_fit(g, v), pref, booked
def scores_d():
    rows, n = [], 0
    act = [g for g in CG if g['status'] == 'Active']
    for vid in [r['visit_id'] for r in OPEN_ROWS]:
        v = OPEN_V[vid]; cs = []
        for g in act:
            if g['name'] == v['planned'] and v['status'] == 'Open': continue
            f = fits(g, v); tot = 25 * f[0] + 20 * f[1] + 15 * f[2] + 20 * f[3] + 10 * (100 if f[4] else 0) + 10 * max(0, 100 * (1 - f[5] / g['hours_limit']))
            cs.append((tot, g['name'], f))
        cs.sort(key=lambda x: (-x[0], x[1]))
        for tot, name, f in cs[:6 if v['status'] == 'Open' else 4]:
            n += 1
            rows.append(dict(score_id='MS-%03d' % n, open_shift=vid, caregiver=name, skills_fit=f[0], area_score=f[1], language_fit=f[2], availability_fit=f[3], preferred=yn(f[4]), hours_booked=f[5]))
    return rows

# ---------- people and reference tables
STANDBY = [g['caregiver_id'] for g in CG if g['status'] == 'Active' and g['availability'] in ('Any time', 'Weekdays and evenings') and g['employment'] != 'Live-in'][:5]
def caregivers_d():
    rows = []
    for g in CG:
        sk = [s.strip() for s in g['skills'].split(';')]; lg = [s.strip() for s in g['languages'].split(';')]
        i0 = int(g['caregiver_id'][3:]); sk = sk[i0 % len(sk):] + sk[:i0 % len(sk)]; lg = lg[i0 % len(lg):] + lg[:i0 % len(lg)]
        r = dict(caregiver_id=g['caregiver_id'], seq=int(g['caregiver_id'][3:]), name=g['name'], hire_date=g['hire_date'], employment=key('emp', g['employment']), pay_rate=g['pay_rate'], area=key('area', g['area']),
                 availability=key('avail', g['availability']), hours_limit=g['hours_limit'], status=key('cgstatus', g['status']), left_date=g['left_date'], leave_reason=key('leave', g['leave_reason']) if g['leave_reason'] else '',
                 source=key('recsrc', g['source']) if g['source'] else '', phone=g['phone'], email=g['email'], standby=yn(g['caregiver_id'] in STANDBY))
        for i in range(5): r['skill_%d' % (i + 1)] = key('svc', sk[i]) if i < len(sk) else ''
        for i in range(2): r['language_%d' % (i + 1)] = key('lang', lg[i]) if i < len(lg) else ''
        rows.append(nb(r))
    return front(rows, lambda r: r.get('standby') == 'yes' and r.get('skill_3') and r.get('language_2') and r.get('source') and not r.get('left_date'))
def clients_d():
    rows = [nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], area=key('area', c['area']), service=key('svc', c['service']), weekly_hours=c['weekly_hours'], language=key('clang', c['language']),
                    preferred=c['preferred'], preferred_2=c['preferred_2'], status=key('clstatus', c['status']), start_date=c['start_date'])) for c in CL]
    return front(rows, lambda r: r['status'] == key('clstatus', 'Active') and r.get('preferred_2'))
def availability_d():
    rows = [dict(avail_id=a['avail_id'], caregiver=a['caregiver'], weekday=key('wday', a['weekday']), from_time=a['from_time'], to_time=a['to_time'], max_hours=a['max_hours']) for a in AV]
    return rows
def time_off_d():
    rows = [dict(timeoff_id=t['timeoff_id'], caregiver=t['caregiver'], kind=key('timeoff', t['kind']), start_date=t['start_date'], end_date=t['end_date'], days=t['days'], approved=yn(t['approved'])) for t in TO]
    return front(rows, lambda r: r['approved'] == 'yes' and r['start_date'] >= TODAY_S)
def weights_d():
    return [dict(factor='Skills', weight=25, note='Points when the caregiver offers the service'), dict(factor='Area', weight=20, note='Same area scores full; travel minutes lower it'),
            dict(factor='Language', weight=15, note='Client language spoken by the caregiver'), dict(factor='Availability', weight=20, note='Free in the weekday and time window'),
            dict(factor='Client preference', weight=10, note='Named as a preferred caregiver by the client'), dict(factor='Hours already booked', weight=10, note='More free hours score higher')]

def calloffs_d():
    rows = []
    for r in CO[-500:]:
        rows.append(nb(dict(calloff_id=r['calloff_id'], date=r['date'], visit_id=r['visit_id'], client=r['client'], area=key('area', r['area']), weekday=key('wday', WEEKDAYS[dd(r['date']).weekday()]), caregiver=r['caregiver'],
                            reason=key('calloff', r['reason']), notice_hours=r['notice_hours'], hours=r['hours'], cover_caregiver=r['cover_caregiver'], minutes_to_cover=r['minutes_to_cover'], premium=r['premium'], covered=yn(r['covered']))))
    return front(rows, lambda r: r['covered'] == 'yes' and r.get('premium', 0) > 0 and r.get('cover_caregiver'))
OT_COVER = collections.defaultdict(float)
for v in VIS:
    if v['cover_type'] == 'Cover' and v['overtime_pay'] > 0: OT_COVER[v['month']] += v['actual_hours'] or v['sched_hours']
def cover_month_d():
    by = collections.defaultdict(lambda: [0, 0, 0.0])
    for r in CO:
        m = iso(dt.date(dd(r['date']).year, dd(r['date']).month, 1)); b = by[m]; b[0] += 1; b[1] += 1 if r['covered'] else 0; b[2] += r['premium']
    rows = []
    for i, m in enumerate([iso(month_start(k)) for k in range(23, -1, -1)], 1):
        b = by.get(m, [0, 0, 0.0])
        rows.append(dict(row_id='CV-%02d' % i, month=m, call_offs=b[0], covered=b[1], uncovered=b[0] - b[1], premium_paid=round(b[2], 2), overtime_hours=round(OT_COVER.get(m, 0.0), 1)))
    return rows
def fill_week_d():
    ot = collections.defaultdict(float)
    for h in HR: ot[h['week']] += h['overtime_hours']
    op = collections.defaultdict(float)
    for v in WIN:
        if v['status'] == 'Open': op[v['week']] += v['sched_hours']
    rows = []
    for w in WK:
        unc, cov, sch = w['uncovered_hours'], w['cover_hours'], w['scheduled_hours']
        if w['week'] > iso(week_start(TODAY)):
            unc = op[w['week']] if w['week'] in op else min(unc, 6.0)
        rows.append(dict(row_id=w['row_id'], week=w['week'], visits=w['visits'], scheduled_hours=sch, planned_hours=round(sch - cov - unc, 1), cover_hours=cov, uncovered_hours=round(unc, 1), overtime_hours=round(ot.get(w['week'], 0.0), 1)))
    return rows

def rest_d():
    byd = collections.defaultdict(list)
    for v in VIS:
        if ago(14) <= v['date'] <= ahead(14) and v['status'] not in ('Cancelled', 'Open') and v['caregiver']: byd[(v['caregiver'], v['date'])].append(v)
    out = []
    for (name, d), vs in byd.items():
        nxt = byd.get((name, iso(dd(d) + day(1))))
        if not nxt: continue
        vs.sort(key=lambda v: v['start']); s0 = hm(vs[0]['start']); ends = [hm(v['start']) + int(v['sched_hours'] * 60) for v in vs]; last = max(ends)
        gaps = [hm(vs[i + 1]['start']) - (hm(vs[i]['start']) + int(vs[i]['sched_hours'] * 60)) for i in range(len(vs) - 1)]
        ns = min(hm(v['start']) for v in nxt)
        out.append((d, name, s0, last, max(gaps) if gaps else 0, ns))
    short = [x for x in out if ((x[5] + 1440 - x[3]) % 1440) / 60 < 10]
    rest = [x for x in out if x not in short]; R.shuffle(rest)
    sel = sorted(short + rest[:max(0, 400 - len(short))])[:400]
    rows = []
    for i, (d, name, s0, last, gap, ns) in enumerate(sel, 1):
        rows.append(dict(row_id='RC-%03d' % i, caregiver=name, date=d, first_start='%02d:%02d' % (s0 // 60, s0 % 60), last_end='%02d:%02d' % ((last // 60) % 24, last % 60), longest_gap_min=max(0, gap), next_day_start='%02d:%02d' % (ns // 60, ns % 60)))
    return front(rows, lambda r: r['date'] >= TODAY_S)

def holidays_d(): return [dict(date=h['date'], holiday=h['holiday'], weekday=key('wday', h['weekday']), pay_mult=h['pay_mult'], bill_mult=h['bill_mult']) for h in HOL]
def areas_d(): return [dict(area=key('area', a['area']), zone=a['zone'], avg_travel_min=a['avg_travel_min']) for a in areas]
def travel_d():
    return [dict(from_area=key('area', a), to_area=key('area', b), minutes=TRAVEL[(a, b)], km=travel_km(a, b)) for a in AREAS for b in AREAS]
def services_d(): return [dict(service=key('svc', s['service']), min_visit_hours=s['min_visit_hours'], bill_rate=s['bill_rate']) for s in services]
def team_d(): return [dict(staff_id=t['staff_id'], name=t['name'], role=t['role'], team=t['team'], pay_type=t['pay_type'], phone=t['phone'], email=t['email'], hours_week=t['hours_week'],
                           monthly_salary=t['monthly_salary'], hourly_rate=t['hourly_rate'], speciality=t['speciality'], country=t['country'], start=t['start']) for t in team]
