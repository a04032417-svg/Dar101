"""Childcare center suite part 2: demo rows from cc_core (full generator output for aggregated tables, thinned rows for the long ones)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc2_lists import *
import collections, datetime as dt

ST = story()
CH = child_rows(); CHD = {c['child_id']: c for c in CH}; CHN = {c['child']: c for c in CH}
AT = attendance_rows(); BK = booking_rows(); RATES = rates; TEAM = {t['staff_id']: t for t in team}
ENR = [c for c in CH if c['status'] == 'Enrolled']
RM = {r['room']: r for r in rooms}
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def months_between(d1, d2):
    a, b = dt.date.fromisoformat(d1), dt.date.fromisoformat(d2)
    m = (b.year - a.year) * 12 + b.month - a.month
    return m - (1 if b.day < a.day else 0)
def next_open(d):
    x = dt.date.fromisoformat(d)
    while x.weekday() > 4: x += dt.timedelta(days=1)
    return x.isoformat()
LAST_OPEN = max(a['date'] for a in AT)          # last day with sign-ins (a Friday when the build day is a Sunday)
SHEET_DATE = LAST_OPEN
OWNER_PHONE = TEAM['CC-01']['phone']; AD_PHONE = TEAM['CC-02']['phone']; COOK_PHONE = TEAM['CC-10']['phone']
FLOAT_PHONE = TEAM['CC-11']['phone']
TEACHER_PHONE = {'Infants': TEAM['CC-03']['phone'], 'Toddlers': TEAM['CC-04']['phone'], 'Twos': TEAM['CC-05']['phone'], 'Preschool': TEAM['CC-06']['phone'], 'School-age': TEAM['CC-11']['phone']}
ASSIST_PHONE = {'Infants': TEAM['CC-07']['phone'], 'Toddlers': TEAM['CC-08']['phone'], 'Twos': TEAM['CC-09']['phone'], 'Preschool': TEAM['CC-09']['phone'], 'School-age': TEAM['CC-12']['phone']}


def children_d():
    out = []
    for c in CH:
        out.append(nb(dict(child_id=c['child_id'], child=c['child'], family=c['family'], family_id=c['family_id'], dob=c['dob'], room=key('room', c['room']), schedule=key('schedule', c['schedule']),
                           days=int(c['schedule'][0]), start_date=c['start_date'], end_date=c['end_date'], status=key('cstatus', c['status']), discount=key('discount', c['discount']),
                           notice_on=c['notice_on'], guardian=c['guardian'], phone=c['phone'], email=c['email'])))
    return out


def bookings_d():
    return [dict(booking_id=b['booking_id'], child_id=b['child_id'], child=b['child'], room=key('room', b['room']), weekday=key('wday', b['weekday']), schedule=key('schedule', b['schedule']),
                 day_type=key('daytype', b['day_type']), hours=b['hours'], from_date=b['from_date']) for b in BK]


def attendance_sample():
    cut = ago(31); by_month = collections.defaultdict(list)
    for d in sorted({a['date'] for a in AT if a['date'] < cut}): by_month[d[:7]].append(d)
    keep = set()
    for m, ds in by_month.items():
        if m < '2025-01': continue
        idx = [3, 14] if m >= '2026-01' else [9]
        for i in idx:
            if i < len(ds): keep.add(ds[i])
    return [a for a in AT if a['date'] >= cut or a['date'] in keep]
ATS = attendance_sample()


def attendance_d():
    out = []
    for a in ATS:
        out.append(nb(dict(attendance_id=a['attendance_id'], date=a['date'], weekday=key('wday', a['weekday']), child_id=a['child_id'], child=a['child'], room=key('room', a['room']),
                           schedule=key('schedule', a['schedule']), booked=a['booked'], booked_hours=a['booked_hours'], status=key('attstatus', a['status']), sign_in=a['sign_in'], sign_out=a['sign_out'],
                           extra_day=a['extra_day'])))
    return out


def rooms_d(): return [dict(room=r['room'], capacity=r['capacity'], ratio=r['ratio']) for r in rooms]
def rates_d():
    return [dict(rate_id=r['rate_id'], room=key('room', r['room']), schedule=key('schedule', r['schedule']), weekly_rate=r['weekly_rate'], days=r['days'], hours_day=r['hours_day'],
                 day_rate=r['day_rate'], last_year_rate=r['last_year_rate']) for r in RATES]
def schedules_d():
    return [dict(schedule=r['schedule'], days=r['days'], hours_day=r['hours_day']) for r in RATES if r['room'] == 'Toddlers']
def room_day_d():
    out = []; i = 0
    for r in ROOMS:
        for n, w in enumerate(WEEKDAYS, 1):
            i += 1; out.append(dict(rd_id='RD-%02d' % i, room=key('room', r), weekday=key('wday', w), day_no=n))
    return out


# ---------- booked vs attended: the last 4 full weeks, 22 children with the largest drift
def week_list(n):
    w0 = dt.date.fromisoformat(week_start(TODAY)) if isinstance(week_start(TODAY), str) else week_start(TODAY)
    if (w0 + dt.timedelta(days=6)) > TODAY: w0 -= dt.timedelta(days=7)      # a week counts when it is over
    return [(w0 - dt.timedelta(days=7 * k)).isoformat() for k in range(n - 1, -1, -1)]
def bva_d():
    weeks = week_list(4); agg = collections.defaultdict(lambda: [0.0, 0.0])
    for a in AT:
        if a['week'] in weeks and a['booked']:
            agg[(a['child_id'], a['week'])][0] += a['booked_hours']; agg[(a['child_id'], a['week'])][1] += a['hours']
    tot = collections.defaultdict(float)
    for (cid, w), (b, h) in agg.items(): tot[cid] += abs(h - b)
    pick = [c for c, _ in sorted(tot.items(), key=lambda x: -x[1]) if CHD[c]['status'] == 'Enrolled'][:22]
    out = []
    for w in weeks:
        for cid in pick:
            if (cid, w) in agg:
                b, h = agg[(cid, w)]; out.append(dict(child=CHD[cid]['child'], week=w, booked_hours=round(b, 1), attended_hours=round(h, 1)))
    out.sort(key=lambda r: (r['week'], r['child']))
    for i, r in enumerate(out, 1): r['bva_id'] = 'BA-%03d' % i
    return [{**{'bva_id': r['bva_id']}, **{k: v for k, v in r.items() if k != 'bva_id'}} for r in out]


# ---------- weekly hours by room: 13 weeks, from the full attendance
def weekly_hours_d():
    weeks = week_list(13); agg = collections.defaultdict(lambda: [0.0, 0.0])
    for a in AT:
        if a['week'] in weeks and a['booked']:
            agg[(a['room'], a['week'])][0] += a['booked_hours']; agg[(a['room'], a['week'])][1] += a['hours']
    out = []; i = 0
    for w in weeks:
        for r in ROOMS:
            i += 1; b, h = agg.get((r, w), (0, 0)); out.append(dict(wh_id='WH-%03d' % i, room=key('room', r), week=w, booked_hours=round(b, 1), attended_hours=round(h, 1)))
    return out


# ---------- children by hour: average children present at half past, last 30 days
def by_hour_d():
    days = sorted({a['date'] for a in AT if a['date'] >= ago(30)}); n = len(days); cnt = collections.defaultdict(int)
    for a in AT:
        if a['date'] >= ago(30) and a['status'] == 'Present' and a['sign_in']:
            for h in range(7, 18):
                hh = '%02d:30' % h
                if a['sign_in'] <= hh < a['sign_out']: cnt[(a['room'], h)] += 1
    out = []; i = 0
    for r in ROOMS:
        for h, lab in zip(range(7, 18), HOURS_L):
            i += 1; out.append(dict(bh_id='BH-%02d' % i, room=key('room', r), hour=key('hour', lab), avg_children=round(cnt[(r, h)] / n, 1)))
    return out


# ---------- absences by child and month
def absences_d():
    months = [month_start(k).isoformat() for k in range(3, -1, -1)]; agg = collections.defaultdict(lambda: [0, 0, 0, ''])
    for a in AT:
        m = a['month']
        if m in months and a['booked']:
            x = agg[(a['child_id'], m)]; x[0] += 1; x[3] = a['room']
            if a['status'] != 'Present': x[1] += 1
            if a['status'] == 'Sick absence': x[2] += 1
    cand = sorted([(k, v) for k, v in agg.items() if v[1] >= 1], key=lambda kv: (-kv[1][1], kv[0][1], kv[0][0]))
    chosen = cand[:78]; have = {v[3] for _, v in chosen}
    for r in ROOMS:                                        # every room appears, so a chart by room has no empty bar
        if r not in have:
            extra = [kv for kv in cand if kv[1][3] == r][:2]; chosen += extra
    out = []
    for (cid, m), (booked, absent, sick, room) in sorted(chosen, key=lambda kv: (kv[0][1], kv[0][0])):
        out.append(dict(child=CHD[cid]['child'], month=m, room=key('room', room), days_absent=absent, booked_days=booked, sick_days=sick))
    for i, r in enumerate(out, 1): r['abs_id'] = 'AB-%03d' % i
    return [{**{'abs_id': r['abs_id']}, **{k: v for k, v in r.items() if k != 'abs_id'}} for r in out]


# ---------- late pickups (the 300 most recent), drop-in days, leavers, closures
def late_pickups_d():
    lf = late_fee_rows(); lf = lf[-300:]
    return [dict(fee_id=l['fee_id'], date=l['date'], child_id=l['child_id'], child=l['child'], room=key('room', CHD[l['child_id']]['room']), late_minutes=l['late_minutes'], fee=l['fee'],
                 waived=l['waived'], charged=l['charged']) for l in lf]
def dropins_d():
    rows = [a for a in AT if a['extra_day']]; out = []
    for i, a in enumerate(rows, 1):
        out.append(dict(dropin_id='DD-%02d' % i, date=a['date'], child=a['child'], family=CHD[a['child_id']]['family'], room=key('room', a['room']), hours=a['hours']))
    return out
def leavers_d():
    out = []
    for c in sorted([c for c in CH if c['status'] == 'Left'], key=lambda c: c['end_date']):
        out.append(dict(child_id=c['child_id'], child=c['child'], family=c['family'], room=key('room', c['room']), notice_on=c['notice_on'], end_date=c['end_date'], leave_reason=key('leavereason', c['leave_reason'])))
    return out
def closures_d():
    return [dict(closure_id=c['closure_id'], date=c['date'], weekday=key('wday', c['weekday']), reason=key('closereason', c['reason'])) for c in closure_rows()]


def signin_d(): return [dict(child_id=c['child_id']) for c in ENR]


# ---------- aging-up list (enrolled children), capacity next 6 months
def aging_up_d():
    out = []
    due = []
    ages = {c['child_id']: months_between(c['dob'], TODAY.isoformat()) for c in ENR}
    mv = {'Infants': 15, 'Toddlers': 27, 'Twos': 39, 'Preschool': 60}
    for c in ENR:
        if c['room'] in mv and ages[c['child_id']] - mv[c['room']] >= 0: due.append(c['child_id'])
    agreed = {cid: ahead(10 + 3 * i) for i, cid in enumerate(due[:4])}
    for c in sorted(ENR, key=lambda c: (c['child_id'] not in agreed, c['room'] == 'School-age')):
        out.append(nb(dict(child_id=c['child_id'], agreed_move=agreed.get(c['child_id'], ''))))
    return out
def capacity6_d():
    out = []; i = 0
    for r in ROOMS:
        for k in range(6):
            i += 1; out.append(dict(cap_id='RC-%02d' % i, room=key('room', r), month=add_months(month_start(0), k).isoformat() if hasattr(add_months(month_start(0), k), 'isoformat') else add_months(month_start(0), k)))
    return out


# ---------- place holds and part-time requests (families on the waiting list; names from cc_core)
WL = waitlist_rows()
DAYSETS = {5: [1, 1, 1, 1, 1], 3: [1, 0, 1, 0, 1], 2: [0, 1, 0, 1, 0]}
def dayflags(vec): return {d: bool(v) for d, v in zip(['mon', 'tue', 'wed', 'thu', 'fri'], vec)}
def holds_d():
    EN = {e['enquiry_id']: e for e in enquiry_rows()}
    act = [('EN-0316', [1, 1, 1, 1, 1], 4), ('EN-0319', [1, 1, 1, 1, 1], 9), ('EN-0320', [1, 0, 1, 0, 1], 2), ('EN-0317', [0, 1, 1, 1, 0], 6)]
    out = []
    for eid, vec, ago_d in act:
        e = EN[eid]
        out.append(dict(family=e['name'], phone=e['phone'], room=key('room', e['want_room']), **dayflags(vec), hold_from=ago(ago_d), hold_until=ahead(14 - ago_d), status=key('holdstatus', 'Active')))
    started = [w for w in WL if w['status'] == 'Started']
    pick = [w for w in started if w['room'] == 'Infants'] + [w for w in started if w['room'] == 'Toddlers'][:2] + [w for w in started if w['room'] == 'Twos'][:2] + [w for w in started if w['room'] == 'Preschool'][:1]
    wd = [w for w in WL if w['status'] == 'Withdrawn']
    other = [w for w in wd if w['room'] == 'School-age'][:2] + [w for w in wd if w['room'] == 'Preschool'][:1] + [w for w in wd if w['room'] == 'Toddlers'][:1]
    sts = ['Converted to start'] * len(pick) + ['Expired', 'Released', 'Expired', 'Released']
    for w, st in zip(pick[:6] + other, sts[:6] + sts[len(pick):]):
        n = int(w['schedule'][0]); hf = w['offered_on'] or w['added_on']
        out.append(dict(family=w['name'], phone=w['phone'], room=key('room', w['room']), **dayflags(DAYSETS[n]), hold_from=hf, hold_until=(dt.date.fromisoformat(hf) + dt.timedelta(days=14)).isoformat(), status=key('holdstatus', st)))
    out.sort(key=lambda r: (r['status'] != key('holdstatus', 'Active'), r['hold_from']))
    for i, r in enumerate(out, 1): r['hold_id'] = 'PH-%02d' % i
    return [{**{'hold_id': r['hold_id']}, **{k: v for k, v in r.items() if k != 'hold_id'}} for r in out]


def requests_d():
    wait = [w for w in WL if w['status'] == 'Waiting']; off = [w for w in WL if w['status'] == 'Offered']; acc = [w for w in WL if w['status'] == 'Started'][-1:]
    rows = []
    patterns3 = [[1, 0, 1, 0, 1], [1, 1, 1, 0, 0], [0, 1, 1, 1, 0], [1, 0, 1, 0, 1]]
    patterns2 = [[0, 1, 0, 1, 0], [1, 0, 1, 0, 0], [0, 0, 1, 0, 1], [1, 0, 0, 0, 1]]
    k3 = k2 = 0
    for i, w in enumerate(wait + off + acc):
        n = int(w['schedule'][0])
        if n == 5: vec = [1, 1, 1, 1, 1]
        elif n == 3: vec = patterns3[k3 % 4]; k3 += 1
        else: vec = patterns2[k2 % 4]; k2 += 1
        half = 'half' in w['schedule']
        st = 'Offered' if w['status'] == 'Offered' else 'Accepted' if w['status'] == 'Started' else ('Waiting for answer' if i < 7 else 'Declined' if i < 9 else 'Waiting for answer')
        rows.append(dict(request_id='PT-%02d' % (i + 1), family=w['name'], phone=w['phone'], room=key('room', w['room']), **dayflags(vec), day_type=key('daytype', 'Half day' if half else 'Full day'),
                         start_date=w['want_start'], status=key('reqstatus', st)))
    return rows[:14]

if __name__ == '__main__':
    for f in [children_d, bookings_d, attendance_d, rooms_d, rates_d, schedules_d, room_day_d, bva_d, weekly_hours_d, by_hour_d, absences_d, late_pickups_d, dropins_d, leavers_d, closures_d, signin_d, aging_up_d, capacity6_d, holds_d, requests_d]:
        r = f(); print(f.__name__, len(r)); 
    print(LAST_OPEN, len(ATS))
