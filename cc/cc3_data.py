"""Childcare center suite part 3: demo rows from cc_core."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc3_lists import *
import collections, datetime as dt

ST = story()
SH = shift_rows(); RH = ratio_hour_rows(); PAY = pay_rows(); REN = renewal_rows(); TRN = training_rows(); EXI = exit_rows(); PNL = pnl_rows()
TEAMD = {t['staff_id']: t for t in team}; TEAMN = {t['name']: t for t in team}
OWNER_PHONE = TEAMD['CC-01']['phone']; AD_PHONE = TEAMD['CC-02']['phone']; COOK_PHONE = TEAMD['CC-10']['phone']; FLOAT_PHONE = TEAMD['CC-11']['phone']
ACC_PHONE = TEAMD['CC-13']['phone']; CLEAN_PHONE = TEAMD['CC-15']['phone']
TEACHER_PHONE = {'Infants': TEAMD['CC-03']['phone'], 'Toddlers': TEAMD['CC-04']['phone'], 'Twos': TEAMD['CC-05']['phone'], 'Preschool': TEAMD['CC-06']['phone'], 'School-age': TEAMD['CC-11']['phone']}
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def iso_d(s): return dt.date.fromisoformat(s)
LAST_OPEN = max(x['date'] for x in SH)
def week_list(n):
    w0 = week_start(TODAY)
    if (w0 + dt.timedelta(days=6)) > TODAY: w0 -= dt.timedelta(days=7)
    return [(w0 - dt.timedelta(days=7 * k)).isoformat() for k in range(n - 1, -1, -1)]
WEEKS = week_list(13)
def mondays_from(n_rows):
    cut = None
    for k in range(60):
        w = (week_start(TODAY) - dt.timedelta(days=7 * k)).isoformat()
        if sum(1 for x in SH if x['date'] >= w) > n_rows: break
        cut = w
    return cut
SH_CUT = mondays_from(2990)


def team_d():
    rows = [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'],
                 hours_week=t['hours_week'], monthly_salary=t['monthly_salary'], hourly_rate=t['hourly_rate'], room=t['room'], start=t['start']) for t in team]
    rows.sort(key=lambda r: r['staff_id'] != 'CC-09')
    return rows


def shifts_d():
    out = []
    for x in SH:
        if x['date'] < SH_CUT: continue
        out.append(nb(dict(shift_id=x['shift_id'], date=x['date'], staff=key('shiftstaff', x['staff']), role=key('payrole', x['role']), room=key('shiftroom', x['room']), start=x['start'], end=x['end'],
                           break_start=x['break_start'], break_minutes=x['break_minutes'], kind=key('shiftkind', x['kind']), rate=x['rate'])))
    return out


def ratio_d():
    out = []; seen = set()
    for x in RH:
        if x['date'] >= WEEKS[0] or (x['gap'] > 0):
            out.append(dict(slot_id=x['slot_id'], date=x['date'], hour=key('hourl', x['hour']), room=key('room', x['room']), children=x['children'], present=x['present'], weekday=key('wday', x['weekday'])))
    return out


def payroll_d():
    out = []
    for x in PAY:
        if x['month'] < '2026-03-01': continue
        out.append(dict(pay_id=x['pay_id'], month=x['month'], person=key('shiftstaff', x['person']), role=key('payrole', x['role']), pay_type=key('paytype', x['pay_type']), hours=x['hours'],
                        gross=x['gross'], on_costs=x['on_costs'], pay_date=x['pay_date'], status=key('paystatus', x['status'] if x['status'] in PAY_STATUS else 'Paid')))
    out.sort(key=lambda r: (r['pay_type'] != key('paytype', 'Hourly'), r['month'] != '2026-10-01', r['role'] != key('payrole', 'Lead teacher')))
    return out


def renewals_d():
    rows = [dict(nb(dict(renewal_id=r['renewal_id'], holder='Center' if r['holder'] == 'Centre' else r['holder'], item=key('renewal', r['item']), due_date=r['due_date'], renewed_on=r['renewed_on'], cost=r['cost']))) for r in REN]
    rows.sort(key=lambda r: (r['renewal_id'] != ST['renewal_id'],))
    return rows


def training_d():
    return [dict(training_id=t['training_id'], date=t['date'], staff=key('staff', t['staff']), kind=key('cpd', t['kind']), title=t['title'], hours=t['hours'], cost=t['cost']) for t in TRN]


def leavers_d():
    return [dict(name=e['name'], left_on=e['left_on'], replacement_cost=e['replace_cost']) for e in sorted(EXI, key=lambda e: e['left_on'], reverse=True)]


def turnover_d():
    heads = collections.defaultdict(set)
    for p in PAY:
        if p['pay_type'] != 'Owner draw': heads[p['month']].add(p['person'])
    vac = collections.defaultdict(int)
    for e in EXI: vac[e['left_on'][:7] + '-01'] += e['vacancy_days']
    out = []
    for i, p in enumerate(PNL, 1):
        out.append(dict(tm_id='TM-%02d' % i, month=p['month'], headcount=len(heads[p['month']]), revenue=p['revenue'], staff_cost=p['staff_pay'], vacancy_days=vac.get(p['month'], 0)))
    out.sort(key=lambda r: r['month'] != month_start(1).isoformat())
    return out


def rota_d():
    wk = week_start(iso_d(LAST_OPEN)).isoformat(); rows = [x for x in SH if x['date'] >= wk]
    rows.sort(key=lambda x: (x['date'], x['room'], x['start'], x['staff']))
    out = []
    for i, x in enumerate(rows, 1):
        out.append(nb(dict(rota_id='RT-%03d' % i, date=(iso_d(x['date']) + dt.timedelta(days=7)).isoformat(), staff=key('shiftstaff', x['staff']), room=key('shiftroom', x['room']),
                           start=x['start'], end=x['end'], break_start=x['break_start'])))
    return out


def weeks_d(): return [dict(wk_id='WK-%02d' % i, week=w, wk=key('weekn', 'Week %d' % i)) for i, w in enumerate(WEEKS, 1)]
def heat_d():
    out = []; i = 0
    for r in ROOMS:
        for n, w in enumerate(WEEKS, 1):
            i += 1; out.append(dict(hm_id='HM-%02d' % i, room=key('room', r), week=w, wk=key('weekn', 'Week %d' % n)))
    out.sort(key=lambda x: (x['room'] != key('room', ST['ratio_room']), x['week'] != iso_d(ST['ratio_date']).isoformat() and x['week'] != (iso_d(ST['ratio_date']) - dt.timedelta(days=iso_d(ST['ratio_date']).weekday())).isoformat()))
    return out
def hours_week_d():
    out = []; i = 0
    for s in STAFF_NAMES:
        for n, w in enumerate(WEEKS, 1):
            i += 1; out.append(dict(hw_id='HW-%03d' % i, staff=key('staff', s), week=w, wk=key('weekn', 'Week %d' % n)))
    return out
def train_year_d():
    out = []; i = 0
    for s in STAFF_NAMES:
        for y in (TODAY.year - 1, TODAY.year):
            i += 1; out.append(dict(ty_id='TY-%02d' % i, staff=key('staff', s), year=y))
    out.sort(key=lambda r: (r['year'] != TODAY.year, r['staff'] != key('staff', 'Zainab Khalid')))
    return out
def staff_hour_d():
    out = []; i = 0
    for r in ROOMS:
        for h in HOUR_L:
            i += 1; out.append(dict(sd_id='SD-%02d' % i, room=key('room', r), hour=key('hourl', h)))
    return out
def break_plan_d():
    rows = rota_d(); first = [r for r in rows if r['date'] == (iso_d(ST['ratio_date']) + dt.timedelta(days=7)).isoformat() and r['room'] == 'toddlers' and r.get('break_start')]
    ids = [r['rota_id'] for r in first[:1]]
    return [dict(rota_id=i) for i in ids + [r['rota_id'] for r in rows if r['rota_id'] not in ids]]


def pay_rates_d():
    return [dict(role=key('payrole', 'Owner-director'), hourly_rate=18.5, on_cost_share=0.0), dict(role=key('payrole', 'Assistant director'), hourly_rate=20.8, on_cost_share=EMPLOYER_COST_PCT),
            dict(role=key('payrole', 'Lead teacher'), hourly_rate=20.5, on_cost_share=EMPLOYER_COST_PCT), dict(role=key('payrole', 'Assistant'), hourly_rate=16.0, on_cost_share=EMPLOYER_COST_PCT),
            dict(role=key('payrole', 'Cook'), hourly_rate=17.5, on_cost_share=EMPLOYER_COST_PCT), dict(role=key('payrole', 'Floater'), hourly_rate=15.5, on_cost_share=EMPLOYER_COST_PCT)]


def cph_d():
    months = [month_start(k).isoformat() for k in range(11, -1, -1)]
    hrs = collections.defaultdict(float); wag = collections.defaultdict(float); chh = collections.defaultdict(float)
    for x in SH:
        if x['room'] in ROOMS: hrs[(x['room'], x['month'])] += x['hours']; wag[(x['room'], x['month'])] += x['cost']
    for a in attendance_rows():
        if a['status'] == 'Present': chh[(a['room'], a['month'])] += a['hours']
    out = []; i = 0
    for m in months:
        for r in ROOMS:
            i += 1; out.append(dict(cp_id='CP-%03d' % i, room=key('room', r), month=m, paid_hours=round(hrs[(r, m)], 1), wages=round(wag[(r, m)], 2), child_hours=round(chh[(r, m)], 1)))
    return out


def relief_d():
    rows = [x for x in SH if x['kind'] != 'Regular'][-300:]
    return [dict(cover_id='CV-%03d' % i, date=x['date'], staff=key('shiftstaff', x['staff']), room=key('shiftroom', x['room']), hour=key('hourl', x['start']), kind=x['kind'],
                 hours=x['hours'], cost=x['cost']) for i, x in enumerate(rows, 1)]


def cover_req_d():
    rel = [x for x in SH if x['kind'] == 'Relief' and x['room'] in ROOMS and x['staff'] in STAFF_NAMES and ago(150) <= x['date'] < ST['ratio_date']]
    pick = rel[::max(1, len(rel) // 8)][-8:]
    rows = [(x['date'], x['room'], x['start'], 1, x['staff'], 'Filled') for x in pick]
    rows.append((ST['ratio_date'], ST['ratio_room'], ST['ratio_hour'], 1, '', 'Not filled'))
    nxt = (iso_d(ST['ratio_date']) + dt.timedelta(days=7)).isoformat()
    rows.append((nxt, ST['ratio_room'], '13:00', 1, '', 'Open'))
    for k, (r, h) in enumerate([('Twos', '12:00'), ('Infants', '08:00'), ('Preschool', '13:00'), ('Toddlers', '16:00')], 1):
        rows.append(((iso_d(nxt) + dt.timedelta(days=k % 3 + (k > 2))).isoformat(), r, h, 1 if k != 2 else 2, '', 'Open'))
    rows.sort()
    rows.sort(key=lambda r: r[5] != 'Open' or r[0] != nxt)
    return [nb(dict(request_id='CR-%02d' % i, date=d, room=key('room', r), hour=key('hourl', h), short_by=s, filled_by=key('shiftstaff', f) if f else '', status=key('reqstatus', st)))
            for i, (d, r, h, s, f, st) in enumerate(rows, 1)]


if __name__ == '__main__':
    for f in [team_d, shifts_d, ratio_d, payroll_d, renewals_d, training_d, leavers_d, turnover_d, rota_d, weeks_d, heat_d, hours_week_d, train_year_d, staff_hour_d, break_plan_d, pay_rates_d, cph_d, relief_d, cover_req_d]:
        r = f(); print(f.__name__, len(r))
    print(SH_CUT, WEEKS[0], collections.Counter(x['status'] for x in payroll_d()))
    print(cover_req_d())
