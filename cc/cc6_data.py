"""Childcare center suite part 6: demo rows from cc_core (full generator output for aggregated tables, thinned rows for the long ones)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc6_lists import *
import collections, datetime as dt

ST = story()
CH = child_rows(); CHD = {c['child_id']: c for c in CH}
TEAM = {t['staff_id']: t for t in team}
AT = attendance_rows(); ML = meal_rows(); HR = health_rows(); IN = incident_rows(); DR = drill_rows(); CK = check_rows()
OWNER_PHONE = TEAM['CC-01']['phone']; AD_PHONE = TEAM['CC-02']['phone']; COOK_PHONE = TEAM['CC-10']['phone']
SUPPLIER_PHONE = TEAM['CC-14']['phone']; CLEANER_PHONE = TEAM['CC-15']['phone']; MAINT_PHONE = TEAM['CC-16']['phone']
TEACHER_PHONE = {'Infants': TEAM['CC-03']['phone'], 'Toddlers': TEAM['CC-04']['phone'], 'Twos': TEAM['CC-05']['phone'], 'Preschool': TEAM['CC-06']['phone'], 'School-age': TEAM['CC-11']['phone']}
ASSIST_PHONE = TEAM['CC-07']['phone']
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def monday(d): x = dt.date.fromisoformat(d); return (x - dt.timedelta(days=x.weekday())).isoformat()
LAST_MEAL = max(m['date'] for m in ML)
LAST_WEEK = monday(LAST_MEAL)
def weeks_back(n): return [(dt.date.fromisoformat(LAST_WEEK) - dt.timedelta(days=7 * k)).isoformat() for k in range(n - 1, -1, -1)]


def children_d():
    return [nb(dict(child_id=c['child_id'], child=c['child'], family=c['family'], room=key('room', c['room']), status=key('cstatus', c['status']), start_date=c['start_date'],
                    schedule=key('schedule', c['schedule']), guardian=c['guardian'], phone=c['phone'])) for c in CH]
def rooms_d(): return [dict(room=r['room'], capacity=r['capacity'], ratio=r['ratio']) for r in rooms]


# ---------- meals: the last 45 days in full, every month of history as 1 or 2 sample days, plus the days that fail the check
def meals_sample():
    cut = ago(45); by_month = collections.defaultdict(list)
    for d in sorted({m['date'] for m in ML if m['date'] < cut}): by_month[d[:7]].append(d)
    keep = {m['date'] for m in ML if m['served'] > m['children_present']}
    for mo, ds in by_month.items():
        idx = [3, 13] if mo >= month_start(12).isoformat()[:7] else [8]
        for i in idx:
            if i < len(ds): keep.add(ds[i])
    return [m for m in ML if m['date'] >= cut or m['date'] in keep]
MLS = meals_sample()
def meals_d():
    return [dict(meal_id=m['meal_id'], date=m['date'], meal=key('meal', m['meal']), room=key('room', m['room']), children_present=m['children_present'], served=m['served'],
                 eligible=m['eligible'], unit_cost=m['unit_cost']) for m in MLS]


def menu_d():
    return [dict(menu_id=m['menu_id'], cycle_week=m['cycle_week'], weekday=key('wday', m['weekday']), meal=key('meal', m['meal']), dish=m['dish'], cost_child=m['cost_child'], portions_per_kg=m['portions_per_kg']) for m in menu_rows()]


# ---------- weekly food: 52 weeks of meals, child-days present and open days from the full data
def menu_week_d():
    cd = collections.defaultdict(int)
    for a in AT:
        if a['status'] == 'Present': cd[a['week']] += 1
    agg = collections.defaultdict(lambda: dict(b=0, l=0, s=0, cost=0.0, days=set()))
    for m in ML:
        x = agg[m['week']]; x[{'Breakfast': 'b', 'Lunch': 'l', 'Afternoon snack': 's'}[m['meal']]] += m['served']; x['cost'] += m['cost']; x['days'].add(m['date'])
    out = []
    for i, w in enumerate(weeks_back(52), 1):
        x = agg[w]
        out.append(dict(mw_id='MW-%03d' % i, week=w, open_days=len(x['days']), child_days=cd[w], served_b=x['b'], served_l=x['l'], served_s=x['s'], meals_cost=round(x['cost'], 2)))
    return out


# ---------- claim by month: 24 months x 3 meals from the full meal data
def claim_d():
    agg = collections.defaultdict(lambda: [0, 0, 0, set()])
    for m in ML:
        x = agg[(m['month'], m['meal'])]; x[0] += m['children_present']; x[1] += m['served']; x[2] += m['eligible']
    over = collections.defaultdict(set)
    for m in ML:
        if m['served'] > m['children_present']: over[(m['month'], m['meal'])].add(m['date'])
    months = sorted({k[0] for k in agg}); out = []; i = 0
    for mo in months[-24:]:
        for me in MEALS:
            i += 1; x = agg[(mo, me)]
            out.append(dict(claim_id='MC-%03d' % i, month=mo, meal=key('meal', me), children_present=x[0], served=x[1], eligible=x[2], days_failing=len(over[(mo, me)])))
    return out


def exceptions_d(): return [dict(ex_id='XC-%02d' % i, place=i) for i in range(1, 13)]


# ---------- health records, status board, cook's list, follow-up
def health_d():
    return [nb(dict(record_id=h['record_id'], child_id=h['child_id'], child=h['child'], room=key('room', h['room']), record=key('hrecord', h['record']), status=key('hstatus', h['status']),
                    due_date=h['due_date'], last_checked=h['last_checked'])) for h in HR]
def board_d():
    out = []; i = 0
    for r in ROOMS:
        for rec in HEALTH_RECORDS:
            i += 1; out.append(dict(board_id='SB-%02d' % i, room=key('room', r), record=key('hrecord', rec)))
    return out
def cook_d(): return [dict(child_id=c['child_id']) for c in CH if c['status'] == 'Enrolled']
def follow_n(): return sum(1 for h in HR if h['status'] != 'On file')
def follow_d(): return [dict(fu_id='FU-%02d' % i, place=i) for i in range(1, follow_n() + 1)]


# ---------- incidents, incidents by hour and by room and month
def incidents_d():
    return [dict(incident_id=i['incident_id'], date=i['date'], incident_time=i['time'], child_id=i['child_id'], child=i['child'], room=key('room', i['room']), type=key('itype', i['type']),
                 parent_informed=i['parent_informed'], staff=key('staff', i['staff']), follow_up_done=key('fup', 'Done' if i['follow_up_done'] else 'Open')) for i in IN]
def inc_hour_d(): return [dict(hour=key('hourl', h)) for h in HOURS_L]
def inc_month_d():
    cd = collections.defaultdict(int)
    for a in AT:
        if a['status'] == 'Present': cd[(a['room'], a['month'])] += 1
    months = [month_start(k).isoformat() for k in range(11, -1, -1)]; out = []; i = 0
    for r in ROOMS:
        for mo in months:
            i += 1; out.append(dict(im_id='IM-%02d' % i, room=key('room', r), month=mo, child_days=cd[(r, mo)]))
    return out


# ---------- drills, schedule by month, checks, completion by week, schedule
def drills_d():
    return [dict(drill_id=d['drill_id'], date=d['date'], kind=key('drill', d['kind']), minutes=d['minutes'], children_present=d['children_present'], staff=key('staff', d['staff']), status=key('dstatus', d['status'])) for d in DR]
def drill_plan_d():
    months = [add_months(month_start(0), k).isoformat() for k in range(-6, 6)]; out = []; i = 0
    for mo in months:
        for k in DRILL_KINDS:
            i += 1; out.append(dict(dp_id='DP-%02d' % i, month=mo, kind=key('drill', k)))
    return out
CKS = CK[-780:]
def checks_d():
    return [dict(check_id=c['check_id'], date=c['date'], room=key('room', c['room']), kind=key('ckind', c['kind']), status=key('checkstatus', c['status']), done_by=c['done_by'], minutes=c['minutes']) for c in CKS]
def check_week_d():
    out = []; i = 0
    for r in ROOMS:
        for w in weeks_back(13):
            i += 1; out.append(dict(cw_id='CW-%03d' % i, room=key('room', r), week=w))
    return out
def clean_sched_d():
    out = []; i = 0
    for r in ROOMS:
        for k in CHECK_KINDS:
            i += 1; out.append(dict(cs_id='CS-%02d' % i, room=key('room', r), kind=key('ckind', k)))
    return out


# ---------- food purchases: the weekly food orders of the last 52 weeks plus the week before
def food_d():
    rows = [e for e in expense_rows() if e['category'] == 'Food and groceries'][-53:]
    return [dict(exp_id=e['expense_id'], date=e['date'], category=e['category'], description=e['description'], amount=e['amount'], paid_to=e['paid_to']) for e in rows]

if __name__ == '__main__':
    for f in [children_d, rooms_d, meals_d, menu_d, menu_week_d, claim_d, exceptions_d, health_d, board_d, cook_d, follow_d, incidents_d, inc_hour_d, inc_month_d, drills_d, drill_plan_d, checks_d, check_week_d, clean_sched_d, food_d]:
        print(f.__name__, len(f()))
    print(LAST_MEAL, LAST_WEEK, menu_week_d()[-1], claim_d()[-1], food_d()[0]['date'], food_d()[-1]['date'])
