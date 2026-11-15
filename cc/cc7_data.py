"""Childcare center suite part 7: demo rows from cc_core (full generator output, so counts and shares look real)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc7_lists import *
import collections, datetime as dt, math

ST = story()
CH = child_rows(); CHD = {c['child_id']: c for c in CH}
FAM = family_rows(); FAMD = {f['family_id']: f for f in FAM}
TEAM = {t['staff_id']: t for t in team}
ENR = [c for c in CH if c['status'] == 'Enrolled']
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def D(s): return dt.date.fromisoformat(s)
def monday(s): d = D(s); return (d - dt.timedelta(days=d.weekday())).isoformat()
def month1(s): return s[:7] + '-01'

OWNER_PHONE = TEAM['CC-01']['phone']; AD_PHONE = TEAM['CC-02']['phone']
FLOAT_PHONE = TEAM['CC-11']['phone']
TEACHER_PHONE = {'Infants': TEAM['CC-03']['phone'], 'Toddlers': TEAM['CC-04']['phone'], 'Twos': TEAM['CC-05']['phone'], 'Preschool': TEAM['CC-06']['phone'], 'School-age': TEAM['CC-11']['phone']}
ASSIST_PHONE = {'Infants': TEAM['CC-07']['phone'], 'Toddlers': TEAM['CC-08']['phone'], 'Twos': TEAM['CC-09']['phone'], 'Preschool': TEAM['CC-09']['phone'], 'School-age': TEAM['CC-12']['phone']}
STAFF_PHONE = {RM_LEAD['Infants']: TEAM['CC-03']['phone'], RM_LEAD['Toddlers']: TEAM['CC-04']['phone'], RM_LEAD['Twos']: TEAM['CC-05']['phone'], RM_LEAD['Preschool']: TEAM['CC-06']['phone'], RM_LEAD['School-age']: TEAM['CC-11']['phone']}

# camp staffing model used by the camp weeks (the same numbers the settings give)
CAMP_HOURS = 8; CAMP_RATE = 23.65; RATIO_SA = 12; RUN_MARGIN = 1
def camp_cost(signups, days): return round(max(1, math.ceil(signups / RATIO_SA)) * CAMP_HOURS * days * CAMP_RATE, 2)

RATE = {(r['room'], r['schedule']): r['weekly_rate'] for r in rates}
def weekly_fee(c): return RATE.get((c['room'], c['schedule']), 0.0)


# ---------- families, children
def families_d():
    room = {}
    for c in sorted(CH, key=lambda c: c['child_id']):
        if c['status'] != 'Left' and c['family_id'] not in room: room[c['family_id']] = c['room']
    return [nb(dict(family_id=f['family_id'], family=f['family'], guardian=f['guardian'], phone=f['phone'], email=f['email'], cycle=key('cycle', f['cycle']),
                    room=key('room', room[f['family_id']]) if f['family_id'] in room else '', children=f['children'], first_start=f['first_start'])) for f in FAM]

def children_d():
    return [nb(dict(child_id=c['child_id'], child=c['child'], family=c['family'], family_id=c['family_id'], room=key('room', c['room']), schedule=key('schedule', c['schedule']),
                    status=key('cstatus', c['status']), start_date=c['start_date'], end_date=c['end_date'], leave_reason=key('leavereason', c['leave_reason']) if c['leave_reason'] else '',
                    weekly_fee=weekly_fee(c), guardian=c['guardian'], phone=c['phone'])) for c in CH]


# ---------- daily reports and parent messages
def reports_d():
    return [dict(report_id=r['report_id'], date=r['date'], room=key('room', r['room']), staff=key('teacher', r['staff']), sent_time=r['sent_time'], same_day=r['same_day'], sent_next_day=r['sent_next_day'])
            for r in report_rows()]

def parent_msgs_d():
    return [nb(dict(message_id=m['message_id'], date=m['date'], replied_on=m['replied_on'], family=m['family'], topic=key('topic', m['topic']), status=key('mstatus', m['status']),
                    reply_hours=m['reply_hours'])) for m in parent_message_rows()]


# ---------- conferences, events, observations
def conferences_d():
    return [dict(conference_id=c['conference_id'], date=c['date'], family=c['family'], child=c['child'], staff=key('teacher', c['staff']), status=key('confstatus', c['status']), slot=c['slot'])
            for c in conference_rows()]

def events_d():
    rows = event_rows(); out = [dict(event_id=e['event_id'], date=e['date'], kind=key('ekind', e['kind']), room=e['room'], invited=e['invited'], attended=e['attended']) for e in rows]
    n = len(out); more = [('Newsletter', 10 + 15, 52), ('Family event', 0, 50), ('Newsletter', 0, 52), ('Newsletter', 0, 52)]
    plan = [(iso(D(ago(-10))), 'Newsletter', 52), (iso(dt.date(TODAY.year, 12, 8)) if dt.date(TODAY.year, 12, 8) > TODAY else iso(dt.date(TODAY.year + 1, 12, 8)), 'Family event', 50),
            (iso(dt.date(TODAY.year, 12, 22)) if dt.date(TODAY.year, 12, 22) > TODAY else iso(dt.date(TODAY.year + 1, 12, 22)), 'Newsletter', 52), (iso(add_months(D(ago(-10)), 2)), 'Newsletter', 53)]
    for i, (d, k, inv) in enumerate(plan, 1):
        out.append(dict(event_id='EV-%02d' % (n + i), date=d, kind=key('ekind', k), room='All rooms', invited=inv, attended=0))
    return out

def observations_d():
    return [dict(obs_id=o['obs_id'], date=o['date'], child=o['child'], room=key('room', o['room']), staff=key('teacher', o['staff']), kind=key('okind', o['kind'])) for o in observation_rows()]

def obs_status_d(): return [dict(child_id=c['child_id']) for c in sorted(ENR, key=lambda c: c['child_id'])]


# ---------- programs: weeks, sign-ups, camp calendar
def _future_signups():
    kids = [c for c in sorted(ENR, key=lambda c: c['child_id']) if c['room'] == 'School-age']
    plan = [('2026-12-21', 5, 3), ('2027-02-15', 3, 5), ('2027-04-05', 1, 5)]
    plan = [(iso(D(a)) if D(a) > TODAY else iso(D(a) + dt.timedelta(days=364)), n, d) for a, n, d in plan]
    out = []; i = 94
    for wk, n, nd in plan:
        for c in kids[:n]:
            i += 1; out.append(dict(signup_id='PS-%03d' % i, week=wk, program='Holiday camp', child=c['child'], days=nd, price_day=PRG['Holiday camp']['price_day'], fee=round(nd * PRG['Holiday camp']['price_day'], 2)))
    return plan, out
FUT_PLAN, FUT_SIGN = _future_signups()

def program_signups_d():
    out = [dict(signup_id=s['signup_id'], week=s['week'], program=key('campprog', s['program']), child=s['child'], days=s['days'], price_day=s['price_day'], fee=s['fee']) for s in program_signup_rows()]
    out += [dict(x, program=key('campprog', x['program'])) for x in FUT_SIGN]
    return out

def program_weeks_d():
    out = []
    for r in program_week_rows():
        cost = r['staff_cost'] if r['program'] == 'Before-after school' else camp_cost(r['signups'], r['days'])
        out.append(dict(row_id=r['row_id'], week=r['week'], month=r['month'], program=key('program', r['program']), places=r['places'], signups=r['signups'], days=r['days'], price_day=r['price_day'],
                        revenue=r['revenue'], staff_cost=cost))
    n = len(out)
    for i, (wk, s, nd) in enumerate(FUT_PLAN, 1):
        out.append(dict(row_id='PW-%03d' % (n + i), week=wk, month=month1(wk), program=key('program', 'Holiday camp'), places=PRG['Holiday camp']['places'], signups=s, days=nd,
                        price_day=PRG['Holiday camp']['price_day'], revenue=round(s * nd * PRG['Holiday camp']['price_day'], 2), staff_cost=camp_cost(s, nd)))
    return out

def programs_d():
    out = [dict(program=p, places=PRG[p]['places'], price_day=PRG[p]['price_day']) for p in PROGRAMS]
    return out + [dict(program='Before school only', places=16, price_day=9.0), dict(program='After school only', places=16, price_day=15.0)]

def camp_cal_d():
    camp = [r for r in program_weeks_d() if r['program'] != key('program', 'Before-after school')]
    camp.sort(key=lambda r: r['week']); camp = camp[-22:]
    return [dict(cal_id='CW-%02d' % i, week=r['week'], program=key('campprog', 'Summer camp' if r['program'] == key('program', 'Summer camp') else 'Holiday camp')) for i, r in enumerate(camp, 1)]


# ---------- aggregated and planning tables
def comm_gaps_d(): return [dict(family_id=f['family_id']) for f in FAM]

def reply_topic_d(): return [dict(topic=t) for t in MSG_TOPICS]

def newsletter_plan_d():
    owners = ['assistant director', 'owner-director', 'lead teacher']; out = []
    for i in range(12):
        m = add_months(month_start(0), i); out.append(dict(plan_id='NP-%02d' % (i + 1), month=m.isoformat(), owner=key('role', ['Assistant director', 'Owner-director', 'Lead teacher'][i % 3])))
    return out

def reports_staff_week_d():
    w0 = week_start(TODAY); out = []; i = 0
    for k in range(29, -1, -1):
        w = (w0 - dt.timedelta(days=7 * k)).isoformat()
        for t in TEACHERS:
            i += 1; out.append(dict(sw_id='SW-%03d' % i, week=w, staff=key('teacher', t)))
    return out

def reports_room_month_d():
    out = []; i = 0
    for r in ROOMS:
        for k in range(11, -1, -1):
            i += 1; out.append(dict(rm_id='RM-%02d' % i, room=key('room', r), month=month_start(k).isoformat()))
    return out

def conf_slots_d():
    booked = [c for c in conference_rows() if c['status'] == 'Booked' and c['date'] > iso(TODAY)]
    seen = set(); out = []
    for c in sorted(booked, key=lambda c: (c['date'], c['slot'], c['staff'])):
        k = (c['staff'], c['date'], c['slot'])
        if k in seen: continue
        seen.add(k); out.append((c['date'], c['slot'], c['staff']))
    dates = sorted({d for d, _, _ in out})
    free = []
    times = ['08:00', '10:20', '13:40', '15:20', '16:20']
    for j, d in enumerate(dates):
        for t in TEACHERS[j % 5:j % 5 + 2]:
            for tm in times[j % 3:]:
                if (t, d, tm) not in seen and len([x for x in free if x[0] == d]) < 2: free.append((d, tm, t)); seen.add((t, d, tm))
    rows = sorted(out + free)
    return [dict(slot_id='SL-%03d' % i, date=d, slot=s, staff=key('teacher', t)) for i, (d, s, t) in enumerate(rows, 1)]

def att_month_d():
    seen = [];
    for e in event_rows():
        if e['date'] <= iso(TODAY):
            k = (month1(e['date']), e['kind'])
            if k not in seen: seen.append(k)
    return [dict(am_id='AM-%02d' % i, month=m, kind=key('ekind', k)) for i, (m, k) in enumerate(seen, 1)]

def leavers_d(): return [dict(child_id=c['child_id']) for c in sorted([c for c in CH if c['status'] == 'Left'], key=lambda c: c['end_date'])]
