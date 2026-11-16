"""HVAC suite part 1: demo rows from hv_core (full generator output for the aggregated tables, recent rows elsewhere)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv1_lists import *
import collections, datetime as _dt

TD = TODAY
JS = iso(week_start(TD) - _dt.timedelta(days=77))        # first week of the jobs sample (13 weeks to next week)
SITES = {s['site_id']: s for s in site_rows()}
CALLS_ALL = call_rows(); JOBS_ALL = job_rows(); PERM_ALL = permit_rows(); CBS = callback_rows()
ST = story()
PH = {t['name']: t['phone'] for t in team}
ROLEPH = {t['role']: t['phone'] for t in team}
OWNER_PHONE = PH[OWNER]; OFFICE_PHONE = PH[OFFICE_MANAGER]
SUP_PHONE = ROLEPH['Equipment supplier']; PARTS_PHONE = ROLEPH['Parts counter']; ACCT_PHONE = ROLEPH['Accountant']
_sub = [t for t in team if t['role'] == 'Subcontractor']
ELEC_PHONE, SHEET_PHONE = _sub[0]['phone'], _sub[1]['phone']
TECH_PHONES = [PH[n] for n in TECH_NAMES]
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def wd(d): return WEEKDAYS7[to_date(d).weekday()]
def hhmm(t): return t
RECOV = ('Price shopper', 'No slot', 'Missed call')

# ---------- permits first (a story edit moves one job)
PERM = [dict(p) for p in PERM_ALL if p['applied_on'] >= ago(365)]
_open = [p for p in PERM if p['status'] == 'Applied']
_open.sort(key=lambda p: p['applied_on'])
HELD = _open[0]['permit_id'] if _open else None
HELD_JOB = _open[0]['job_id'] if _open else None
for p in PERM:
    if p['permit_id'] == HELD: p['job_date'] = ago(3)


def jobs_rows():
    out = []
    for j in JOBS_ALL:
        if j['date'] < JS: continue
        j = dict(j)
        if j['job_id'] == HELD_JOB:
            j['date'] = ago(3); j['week'] = iso(week_start(to_date(j['date']))); j['weekday'] = wd(j['date']); j['status'] = 'Scheduled'; j['parts_ready'] = True
        out.append(j)
    return out
JOBS = jobs_rows()
JOB_BY = {j['job_id']: j for j in JOBS}


def _prev(j, jobs=JOBS):
    best = None
    for k in jobs:
        if k['site_id'] == j['site_id'] and k['date'] < j['date'] and k['status'] != 'Cancelled' and (best is None or k['date'] > best['date']): best = k
    return best
_BYSITE = collections.defaultdict(list)
for _j in JOBS: _BYSITE[_j['site_id']].append(_j)
def prev_job(j):
    best = None
    for k in _BYSITE[j['site_id']]:
        if k['date'] < j['date'] and k['status'] != 'Cancelled' and (best is None or k['date'] > best['date']): best = k
    return best
REPEATS = []
for j in JOBS:
    if j['status'] == 'Cancelled' or j['date'] > iso(TD): continue
    p = prev_job(j)
    if p and (to_date(j['date']) - to_date(p['date'])).days <= REPEAT_DAYS: REPEATS.append(j)


def sites_d():
    return [nb(dict(site_id=s['site_id'], site_ref=s['site_ref'], area=key('area', s['area']), site_type=key('sitetype', s['site_type']), landlord=s['landlord'], account=s['account'], phone=s['phone'],
                    member=s['member'], jobs=s['jobs'], last_job=s['last_job'])) for s in SITES.values()]


def calls_d():
    rows = [c for c in CALLS_ALL if c['date'] >= ago(90)]
    out = []
    for i, c in enumerate(rows):
        s = SITES.get(c['site_id'])
        out.append(nb(dict(call_id=c['call_id'], date=c['date'], month=c['month'], weekday=key('wday7', c['weekday']), time=c['time'], source=key('source', c['source']), call_type=key('calltype', c['call_type']),
                           outcome=key('calloutcome', c['outcome']), answered_by=key('answeredby', c['answered_by']), site_id=c['site_id'], caller_phone=s['phone'] if s else fake_phone(i + 7), est_value=c['est_value'],
                           job_id=c['job_id'], emergency=c['emergency'])))
    first = next(i for i, r in enumerate(out) if r.get('site_id') and r.get('job_id') and r['outcome'] == key('calloutcome', 'Booked') and r['date'] < iso(TD))
    out.insert(0, out.pop(first))
    return out


def jobs_d():
    out = []
    for j in JOBS:
        out.append(nb(dict(job_id=j['job_id'], date=j['date'], week=j['week'], weekday=key('wday7', j['weekday']), start=j['start'], site_id=j['site_id'], area=key('area', j['area']), site_type=key('sitetype', j['site_type']),
                           equipment_id=j['equipment_id'], job_type=key('jobtype', j['job_type']), reason=key('calltype', j['reason']), technician=key('tech', j['technician']),
                           assistant=j['assistant'], van=key('van', j['van']), hours=j['hours'], drive_hours=j['drive_hours'], price=j['price'], cost=j['total_cost'],
                           status=key('jobstatus', j['status']), parts_ready=j['parts_ready'], permit_needed=j['permit_needed'], emergency=j['emergency'], call_id=j['call_id'])))
    # first row: a complete completed job with a previous visit (forms and documents open on it)
    rp = {r['job_id'] for r in REPEATS if r['equipment_id'] and r['assistant'] and r['status'] == 'Completed'}
    first = next((i for i, r in enumerate(out) if r['job_id'] in rp), 0)
    out.insert(0, out.pop(first))
    return out


def dispatch_d():
    days = [week_start(TD) + _dt.timedelta(days=k) for k in (0, 1, 2, 3, 4, 7, 8, 9, 10, 11)]
    out, n = [], 1
    for d in days:
        for t in TECH6:
            out.append(dict(row_id='DB-%03d' % n, technician=key('tech', t), date=iso(d))); n += 1
    return out


def capacity_d():
    out = []
    for k in range(30):
        d = TD + _dt.timedelta(days=k)
        out.append(dict(date=iso(d), techs_working=6 if d.weekday() < 5 else (2 if d.weekday() == 5 else 1)))
    return out


def permits_d():
    out = []
    for p in PERM:
        out.append(nb(dict(permit_id=p['permit_id'], job_id=p['job_id'], site_id=p['site_id'], job_type=key('jobtype', p['job_type']), technician=key('tech', p['technician']), job_date=p['job_date'],
                           applied_on=p['applied_on'], fee=p['fee'], approved_on=p['approved_on'], inspection_on=p['inspection_on'], passed_on=p['passed_on'], status=key('permitstatus', p['status']))))
    first = next(i for i, r in enumerate(out) if r.get('passed_on') and r.get('inspection_on'))
    out.insert(0, out.pop(first))
    return out


def techs_d(): return [dict(technician=t['name'], trade=t['trade'], van=t['van']) for t in techs[:6]]
def vans_d(): return [dict(van=v['van'], technician=v['technician'], lease_monthly=v['lease_monthly']) for v in vans]
def job_types_d(): return [dict(job_type=j['job_type'], trade=j['trade'], kind=j['kind'], avg_hours=j['avg_hours'], target_margin=j['target_margin']) for j in job_types]
EMERG_TYPES = ('No-heat', 'No-cool', 'Leak', 'Drain')
def call_types_d():
    out = []
    for ct in CALL_TYPES:
        v = [c['est_value'] for c in CALLS_ALL if c['call_type'] == ct and c['outcome'] in ('Booked', 'Estimate booked')]
        out.append(dict(call_type=ct, emergency=ct in EMERG_TYPES, avg_value=round(sum(v) / len(v)) if v else 0))
    return out
def outcomes_d():
    note = {'Booked': 'A job is booked', 'Estimate booked': 'An estimate visit is booked', 'Price shopper': 'Asked the price only', 'No slot': 'No time slot fitted', 'Outside area': 'Outside the service area',
            'Missed call': 'Nobody answered', 'Existing job': 'About a job already booked'}
    return [dict(outcome=o['outcome'], booked=o['booked'], note=note[o['outcome']]) for o in call_outcomes]
def sources_d(): return [dict(source=s['source'], monthly_cost=s['monthly_cost'], kind=s['kind']) for s in lead_sources]


def _period(d): return 'Last 90 days' if d >= ago(90) else ('Previous 90 days' if d >= ago(180) else None)
def _booked(c): return c['outcome'] in ('Booked', 'Estimate booked')
def _lost(c): return c['est_value'] if c['outcome'] in RECOV else 0
def book_source_d():
    agg = collections.defaultdict(lambda: [0, 0, 0.0])
    for c in CALLS_ALL:
        p = _period(c['date'])
        if not p: continue
        a = agg[(c['source'], p)]; a[0] += 1; a[1] += _booked(c); a[2] += _lost(c)
    out, n = [], 1
    for p in PERIOD:
        for s in SOURCES:
            a = agg[(s, p)]
            out.append(dict(row_id='BS-%02d' % n, source=key('source', s), period=key('period', p), calls=a[0], booked=a[1], lost_value=round(a[2]))); n += 1
    return out
def _daypart(c): return 'After hours' if c['time'] >= '18:00' else 'Business hours'
def book_answered_d():
    agg = collections.defaultdict(lambda: [0, 0])
    for c in CALLS_ALL:
        p = _period(c['date'])
        if not p: continue
        a = agg[(c['answered_by'], _daypart(c), p)]; a[0] += 1; a[1] += _booked(c)
    out, n = [], 1
    for p in PERIOD:
        for ab in ANSWERED_BY:
            for dp in DAYPART:
                a = agg[(ab, dp, p)]
                out.append(dict(row_id='BA-%02d' % n, answered_by=key('answeredby', ab), daypart=key('daypart', dp), period=key('period', p), calls=a[0], booked=a[1])); n += 1
    return out
def miss_weekday_d():
    agg = collections.defaultdict(lambda: [0, 0, 0.0])
    for c in CALLS_ALL:
        if c['date'] < ago(365): continue
        a = agg[(c['weekday'], _daypart(c))]; a[0] += 1
        if c['outcome'] == 'Missed call': a[1] += 1; a[2] += c['est_value']
    out, n = [], 1
    for w in WEEKDAYS7:
        for dp in DAYPART:
            a = agg[(w, dp)]
            out.append(dict(row_id='MW-%02d' % n, weekday=key('wday7', w), daypart=key('daypart', dp), calls=a[0], missed=a[1], lost_value=round(a[2]))); n += 1
    return out
def calls_month_d():
    months = sorted({c['month'] for c in CALLS_ALL})
    cm = collections.defaultdict(lambda: [0, 0, 0, 0.0]); jm = collections.defaultdict(lambda: [0, 0.0]); cb = collections.Counter()
    last = {}
    for j in JOBS_ALL:
        if j['status'] == 'Cancelled': continue
        p = last.get(j['site_id'])
        if p and j['date'] <= iso(TD) and 0 < (to_date(j['date']) - to_date(p)).days <= REPEAT_DAYS: cb[j['month']] += 1
        last[j['site_id']] = j['date']
    for c in CALLS_ALL:
        a = cm[c['month']]; a[0] += 1; a[1] += _booked(c); a[2] += c['emergency']; a[3] += _lost(c)
    for j in JOBS_ALL:
        if j['status'] == 'Cancelled' or j['date'] > iso(TD): continue
        a = jm[j['month']]; a[0] += 1; a[1] += j['drive_hours']
    return [dict(month=m, calls=cm[m][0], booked=cm[m][1], emergency_calls=cm[m][2], jobs=jm[m][0], drive_hours=round(jm[m][1]), possible_callbacks=cb[m], lost_value=round(cm[m][3])) for m in months]
def jobs_week_d(): return [dict(week=iso(to_date(JS) + _dt.timedelta(days=7 * k))) for k in range(13)]
def permit_wait_d(): return [dict(job_type=key('jobtype', j)) for j in JOB_TYPES]
def repeats_d():
    rows = sorted(REPEATS, key=lambda j: (j['date'], j['job_id']))[-30:]
    first = next((i for i, j in enumerate(rows) if j['equipment_id'] and (prev_job(j) or {}).get('price', 0) > 0), 0)
    return [dict(job_id=j['job_id']) for j in rows[first:first + 1] + rows[:first] + rows[first + 1:]]
def workorders_d():
    up = [j for j in JOBS if j['status'] == 'Scheduled' and j['date'] >= iso(TD)]
    up.sort(key=lambda j: (j['date'], j['start']))
    rows = up[:30]
    first = next((i for i, j in enumerate(rows) if j['assistant'] and j['equipment_id']), next((i for i, j in enumerate(rows) if j['equipment_id']), 0))
    rows.insert(0, rows.pop(first))
    return [dict(job_id=j['job_id']) for j in rows]


if __name__ == '__main__':
    print('held', HELD, HELD_JOB, 'jobs', len(JOBS), 'repeats', len(REPEATS), 'calls', len(calls_d()), 'permits', len(PERM), 'sites', len(SITES))
    print(calls_month_d()[-2:]); print(book_source_d()[:2]); print(workorders_d()[:3], repeats_d()[:2])
