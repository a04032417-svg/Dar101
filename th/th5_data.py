"""Therapy part 5: demo rows from th_core (full generator output for aggregated tables, windows of recent rows for row-level logs)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th5_lists import *
import th_core as C
import collections, datetime as _d

dd = to_date
ST = story()
MS0 = month_start(0).isoformat(); LM0 = month_start(1).isoformat()
SUP_RATE = 60.0
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def front(rows, pred):
    """move the first row that satisfies pred to the front (a form or document demo shows the first row)"""
    for i, r in enumerate(rows):
        if pred(r): return [r] + rows[:i] + rows[i + 1:]
    return rows
def newest(rows, col='month'): return sorted(rows, key=lambda r: r[col], reverse=True)
PH = {t['name']: t['phone'] for t in team}
CMR = C.clinician_month_rows(); PAYR = C.clinician_pay_rows(); CFR = C.contractor_fee_rows(); SES = C.session_rows(); CLI = C.client_rows(); DIS = C.discharge_rows()
PAY_BY = {(x['person'], x['month']): x for x in PAYR}
CM_BY = {(x['clinician'], x['month']): x for x in CMR}
SES_ATT = [s for s in SES if s['status'] == 'Attended' and s['date'] <= ago(0)]


# ---------------- clinician months: booked = sessions kept in the diary (booked minus cancelled), as in Part 2
def clin_months_d():
    out = [nb(dict(row_id=r['row_id'], month=r['month'], clinician=key('clin', r['clinician']), working_weeks=r['working_weeks'], capacity=r['capacity'], booked=r['booked'] - r['cancelled'],
                   attended=r['attended'], cancelled=r['cancelled'], late_cancels=r['late_cancels'], no_shows=r['no_shows'], clinical_hours=r['clinical_hours'], revenue=r['revenue'],
                   new_clients=r['new_clients'], discharges=r['discharges'], late_notes=r['late_notes'])) for r in CMR]
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0 and r['clinician'] == key('clin', 'Priya Raman'))


def sessions_d():
    rows = [s for s in SES if s['date'] <= ago(0)][-600:]
    out = [nb(dict(session_id=s['session_id'], date=s['date'], client=s['client'], service=key('svc', s['service']), clinician=key('clin', s['clinician']), status=key('sstatus', s['status']),
                   minutes=s['minutes'], charge=s['charge'], clinician_pay=s['clinician_pay'])) for s in rows]
    out.reverse()
    return front(out, lambda r: r['status'] == key('sstatus', 'Attended') and r['clinician'] == key('clin', 'Priya Raman'))


# ---------------- monthly targets (last 12 months)
AVG_CH = {}
for _n in CLINICIANS:
    _a = sum(x['attended'] for x in CMR if x['clinician'] == _n); _r = sum(x['revenue'] for x in CMR if x['clinician'] == _n); AVG_CH[_n] = _r / max(1, _a)
SESS_T = {t['name']: t['session_target'] for t in team}
def targets_d():
    out = []; n = 1
    for k in range(11, -1, -1):
        m = month_start(k).isoformat()
        for nm in CLINICIANS:
            r = CM_BY.get((nm, m))
            if not r: continue
            ts = SESS_T[nm] * r['working_weeks']
            out.append(dict(target_id='TG-%03d' % n, month=m, clinician=key('clin', nm), target_sessions=ts, target_revenue=round(ts * AVG_CH[nm] / 50.0) * 50.0)); n += 1
    out.reverse()
    return front(out, lambda r: r['month'] == LM0 and r['clinician'] == key('clin', 'Priya Raman'))


# ---------------- utilisation by weekday (slots a week from the diary, sessions of the last 12 weeks)
def weekday_d():
    slots = collections.Counter((s['clinician'], s['weekday']) for s in C.slot_rows() if s['status'] != 'Extra')
    sess = collections.Counter((s['clinician'], s['weekday']) for s in SES if s['status'] != 'Cancelled' and ago(84) <= s['date'] <= ago(1))
    out = []; n = 1
    for nm in CLINICIANS:
        for wd in WORKDAYS:
            out.append(dict(wu_id='WU-%02d' % n, clinician=key('clin', nm), weekday=key('wday', wd), slots_week=int(round(slots[(nm, wd)] / 6.0)), sessions_12w=sess[(nm, wd)])); n += 1
    return out


def mix_d():
    agg = collections.defaultdict(lambda: [0, 0.0])
    for s in SES_ATT:
        if s['date'] >= ago(365): a = agg[(s['clinician'], s['service'])]; a[0] += 1; a[1] += s['charge']
    out = []; n = 1
    for (nm, sv), (c, rev) in sorted(agg.items(), key=lambda x: (CLINICIANS.index(x[0][0]), SESSION_SERVICES.index(x[0][1]))):
        if c < 3: continue
        out.append(dict(mx_id='MX-%02d' % n, clinician=key('clin', nm), service=key('svc', sv), sessions=c, revenue=round(rev, 2))); n += 1
    return out


# ---------------- admin time log (blocks of work that take the clinician away from client sessions)
TASK_MIN = {'Session notes': (60, 180), 'Client e-mails and calls': (45, 120), 'Plan reviews': (60, 150), 'Referral letters': (45, 90), 'Team meeting': (60, 120),
            'Scheduling and billing queries': (45, 90), 'Supervision preparation': (60, 120), 'Reading and training': (90, 180)}
TASK_W = [28, 18, 14, 8, 8, 8, 8, 8]
def admin_d():
    r = rng('p5admin'); out = []; n = 1
    names = list(CLINICIANS); w = [t['hours_week'] for t in team[:6]]
    for k in range(11, -1, -1):
        m = month_start(k); days = []
        d0 = m
        while d0.month == m.month and d0 <= TODAY:
            if d0.weekday() < 5: days.append(d0)
            d0 += _d.timedelta(days=1)
        cnt = 27 if k > 0 else max(10, int(27 * len(days) / 21.0))
        picks = sorted(r.choices(days, k=cnt))
        for dt_ in picks:
            nm = r.choices(names, weights=w)[0]; tk = r.choices(ATASKS, weights=TASK_W)[0]; lo, hi = TASK_MIN[tk]
            out.append(dict(admin_id='AT-%04d' % n, date=dt_.isoformat(), clinician=key('clin', nm), task=key('atask', tk), minutes=int(round(r.randint(lo, hi) / 15.0) * 15))); n += 1
    out.reverse()
    return out


# ---------------- client retention and drop-outs
def retention_d():
    el = [x for x in CLI if (x['status'] in ('Discharged', 'Referred out') or (x['status'] == 'Active' and x['sessions_attended'] >= 6)) and x['first_session'] and x['first_session'] <= ago(0)]
    el.sort(key=lambda x: x['first_session']); el = el[-300:]
    out = [nb(dict(client_id=x['client_id'], client=x['client'], clinician=key('clin', x['clinician']), service=key('svc', x['service']), first_session=x['first_session'], sessions_attended=x['sessions_attended'],
                   last_session=x['last_session'], status=key('cstatus', x['status']))) for x in el]
    out.reverse()
    return front(out, lambda r: r['clinician'] == key('clin', 'Priya Raman') and r['status'] == key('cstatus', 'Discharged') and r['sessions_attended'] >= 6)


DROP_REASONS = ('Client ended', 'No contact', 'Fees')
def dropouts_d():
    rows = [x for x in DIS if x['reason'] in DROP_REASONS]
    step = len(rows) / 150.0; pick = [rows[int(i * step)] for i in range(150)]
    out = [dict(discharge_id=x['discharge_id'], date=x['date'], client=x['client'], clinician=key('clin', x['clinician']), service=key('svc', x['service']), sessions=x['sessions'], reason=key('dreason', x['reason'])) for x in pick]
    out.reverse()
    return front(out, lambda r: r['clinician'] == key('clin', 'Lucas Moreau') and r['sessions'] <= 1)


# ---------------- rebooking log
def rebook_d():
    byc = collections.defaultdict(list)
    for s in SES:
        if s['status'] in ('Attended', 'Scheduled', 'Late cancel', 'No-show'): byc[s['client_id']].append(s['date'])
    for v in byc.values(): v.sort()
    pool = [s for s in SES_ATT if s['date'] >= ago(400)]
    step = len(pool) / 400.0; pick = [pool[int(i * step)] for i in range(400)]
    r = rng('p5rebook'); out = []
    for s in pick:
        nxt = [d for d in byc[s['client_id']] if d > s['date']]
        booked = ''
        if nxt:
            p0 = 0.50 if s['clinician'] == 'Lucas Moreau' else (0.56 if s['clinician'] == 'Priya Raman' else 0.66)
            x = r.random()
            lag = 0 if x < p0 else (r.randint(1, 14) if x < p0 + 0.20 else (r.randint(15, 30) if x < p0 + 0.26 else None))
            if lag is not None:
                b = dd(s['date']) + _d.timedelta(days=lag)
                if b <= TODAY and b.isoformat() <= nxt[0]: booked = b.isoformat()
        out.append(nb(dict(session_id=s['session_id'], date=s['date'], client=s['client'], clinician=key('clin', s['clinician']), next_booked_on=booked)))
    out.reverse()
    return front(out, lambda r: r.get('next_booked_on') and r['clinician'] == key('clin', 'Priya Raman') and r['date'] < ago(30))


# ---------------- productivity reviews: two reviews a month for the two clinicians who most need one
def reviews_d():
    rows = []; n = 1
    for k in range(12, 0, -1):
        m = month_start(k).isoformat(); sc = []
        for nm in CLINICIANS:
            x = CM_BY.get((nm, m))
            if not x: continue
            share = (x['booked'] - x['cancelled']) / x['capacity']; rph = x['revenue'] / max(1, x['clinical_hours']); mis = (x['late_cancels'] + x['no_shows']) / max(1, x['booked'])
            if share > 0.90: f, p = 'Booked share of cap in strain', 3 + share
            elif share < 0.70: f, p = 'Booked share of cap idle', 3 + (0.7 - share)
            elif x['late_notes'] >= 5: f, p = 'Notes overdue', 2.5 + x['late_notes'] / 20.0
            elif mis > 0.07: f, p = 'Late cancels above target', 2 + mis
            elif rph < 118: f, p = 'Revenue per hour below target', 2 + (118 - rph) / 100.0
            else: f, p = 'On track', 0.1 + share / 10.0
            sc.append((p, nm, f))
        sc.sort(reverse=True)
        for p, nm, f in sc[:2]:
            rows.append((m, nm, f))
    ACT = {'Booked share of cap in strain': 'Move sessions to a colleague and pause new bookings', 'Booked share of cap idle': 'Offer the free slots to the waiting list first',
           'Late cancels above target': 'Send reminders two days ahead and review the late-cancel rule', 'Retention below target': 'Review the clients who stopped early',
           'Admin time heavy': 'Block two admin hours a week and drop one task', 'Rebooking below target': 'Book the next session at the end of each session',
           'Revenue per hour below target': 'Review the service mix and the fee for this clinician', 'Notes overdue': 'Block an hour a day to finish notes', 'On track': 'No action, review again next month'}
    out = []
    for m, nm, f in rows:
        dt_ = add_months(dd(m), 1) + _d.timedelta(days=4); due = dt_ + _d.timedelta(days=14)
        row = dict(review_id='PR-%03d' % n, date=dt_.isoformat(), clinician=key('clin', nm), finding=key('pfind', f), action=ACT[f], due_date=due.isoformat()); n += 1
        if due <= TODAY - _d.timedelta(days=3): row['done_on'] = (due - _d.timedelta(days=(n * 3) % 9)).isoformat()
        out.append(row)
    for r_ in out:
        if r_['clinician'] == key('clin', 'Lucas Moreau') and r_['date'] >= ago(60) and 'done_on' in r_: del r_['done_on']; break
    out.reverse()
    return front(out, lambda r: 'done_on' in r and r['finding'] != key('pfind', 'On track'))


# ---------------- pay, payroll, all-in cost
def pay_d():
    out = [nb(dict(pay_id=x['pay_id'], month=x['month'], person=key('staff', x['person']), pay_type=key('paykind', x['pay_type']), sessions=x['sessions'], hours=x['hours'], fees_charged=x['fees_charged'],
                   split_pct=x['split_pct'], amount=x['amount'], employer_cost=x['employer_cost'], paid_on=x['paid_on'], status=key('payst', x['status']))) for x in PAYR]
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0 and r['person'] == key('staff', 'Kenji Watanabe'))


def payroll_d():
    agg = collections.defaultdict(lambda: collections.Counter())
    for x in PAYR:
        a = agg[x['month']]
        a[{'Salary': 'salaries', 'Hourly': 'hourly_pay', 'Percentage split': 'contractor_pay', 'Per session': 'associate_pay'}[x['pay_type']]] += x['amount']; a['employer_costs'] += x['employer_cost']
    out = []; n = 1
    for m in sorted(agg):
        a = agg[m]
        out.append(nb(dict(payroll_id='PM-%03d' % n, month=m, salaries=round(a['salaries'], 2), hourly_pay=round(a['hourly_pay'], 2), contractor_pay=round(a['contractor_pay'], 2),
                           associate_pay=round(a['associate_pay'], 2) or '', employer_costs=round(a['employer_costs'], 2)))); n += 1
    out.reverse()
    return front(out, lambda r: r['month'] == LM0)


SUP_H = collections.defaultdict(float)
for _x in C.supervision_rows():
    if _x['supervisee'] == 'Lucas Moreau': SUP_H[_x['date'][:7] + '-01'] += _x['hours']
CPAY_OF = {'Amira Lindqvist': 'Owner draw', 'Daniel Okoye': 'Salary', 'Sofia Marchetti': 'Salary', 'Kenji Watanabe': 'Percentage split', 'Priya Raman': 'Percentage split', 'Lucas Moreau': 'Per session'}
ROOMC = collections.defaultdict(float)
for _s in SES: ROOMC[(_s['clinician'], _s['month'])] += _s['room_cost']
def allin_d():
    out = []
    for r in CMR:
        nm, m = r['clinician'], r['month']; p = PAY_BY.get((nm, m))
        out.append(nb(dict(allin_id='AC-%04d' % int(r['row_id'][3:]), month=m, clinician=key('clin', nm), pay_type=key('cpay', CPAY_OF[nm]), sessions=r['attended'], revenue=r['revenue'],
                           clinician_pay=p['amount'] if p else '', employer_cost=p['employer_cost'] if p and p['employer_cost'] else '', room_cost=round(ROOMC[(nm, m)], 2),
                           admin_cost=round(C.ADMIN_COST * (r['booked'] - r['cancelled']), 2), supervision_cost=round(SUP_H[m] * SUP_RATE, 2) if nm == 'Lucas Moreau' and SUP_H[m] else '')))
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0 and r['clinician'] == key('clin', 'Lucas Moreau'))


def pay_changes_d():
    rows = [('2023-01-01', 'Daniel Okoye', 'Salary raised', 'Monthly salary', 4200, 4500, 'Yearly review'), ('2024-07-01', 'Daniel Okoye', 'Salary raised', 'Monthly salary', 4500, 4800, 'Larger caseload'),
            ('2023-01-01', 'Sofia Marchetti', 'Salary raised', 'Monthly salary', 4000, 4200, 'Yearly review'), ('2024-07-01', 'Sofia Marchetti', 'Salary raised', 'Monthly salary', 4200, 4500, 'Cost of living'),
            ('2024-03-01', 'Kenji Watanabe', 'Split raised', 'Share of the fee, %', 58, 60, 'Larger caseload'), ('2024-09-01', 'Grace Mensah', 'Hourly rate raised', 'Hourly rate', 22, 24, 'Cost of living'),
            ('2025-07-15', 'Priya Raman', 'Split agreed', 'Share of the fee, %', 62, 65, 'New contract terms'), ('2025-12-15', 'Lucas Moreau', 'Rate agreed', 'Rate per session', 40, 45, 'New contract terms'),
            (ahead(47), 'Daniel Okoye', 'Salary raise planned', 'Monthly salary', 4800, 5000, 'Yearly review'), (ahead(47), 'Sofia Marchetti', 'Salary raise planned', 'Monthly salary', 4500, 4700, 'Yearly review'),
            (ahead(47), 'Lucas Moreau', 'Rate raise planned', 'Rate per session', 45, 48, 'Associate review'), (ahead(47), 'Grace Mensah', 'Hourly rate raise planned', 'Hourly rate', 24, 25, 'Cost of living')]
    out = [dict(change_id='PCH-%02d' % (i + 1), date=d, person=key('staff', p), change=ch, unit=u, old_rate=o, new_rate=nw, reason=key('pchg', rs)) for i, (d, p, ch, u, o, nw, rs) in enumerate(rows)]
    out.sort(key=lambda r: r['date'], reverse=True)
    return front(out, lambda r: r['date'] < ago(0) and r['person'] == key('staff', 'Lucas Moreau'))


# ---------------- contractor statements and invoices
def stmt_d():
    out = []
    for x in CFR:
        if x['month'] >= MS0: continue
        a = CM_BY[(x['contractor'], x['month'])]['attended']
        out.append(dict(pay_id=x['pay_id'], month=x['month'], contractor=x['contractor'], sessions=a, fees_charged=x['fees_charged'], split_pct=x['split_pct'], amount=x['amount'], card_fees=x['card_fees']))
    out = newest(out)
    return front(out, lambda r: r['month'] == LM0 and r['contractor'] == 'Kenji Watanabe')


def inv_d():
    r = rng('p5inv'); out = []; n = 1; rows = sorted([x for x in CFR if x['month'] < MS0], key=lambda x: (x['month'], x['contractor']))
    bad = set(r.sample(range(len(rows) - 2), 4))
    for i, x in enumerate(rows):
        pay = PAY_BY[(x['contractor'], x['month'])]; nxt = add_months(dd(x['month']), 1)
        recv = nxt + _d.timedelta(days=r.randint(2, 7)); amt = x['amount_after_fees']; paid = pay['paid_on']
        if i in bad:
            amt = round(amt * r.choice([1.02, 1.035, 0.985]), 2); paid = (dd(pay['paid_on']) + _d.timedelta(days=r.randint(4, 9))).isoformat() if pay['paid_on'] else ''
        if x['month'] == LM0 and x['contractor'] == 'Priya Raman':
            amt = round(x['amount_after_fees'] + 83.0, 2); recv = TODAY - _d.timedelta(days=3); paid = ''
        elif x['month'] == LM0: recv = nxt + _d.timedelta(days=r.randint(2, 4))
        out.append(nb(dict(invoice_id='CI-%03d' % n, month=x['month'], contractor=x['contractor'], received_on=recv.isoformat(), amount=amt, paid_on=paid))); n += 1
    out.reverse()
    out = front(out, lambda r: r['month'] == LM0 and r.get('paid_on') and r['contractor'] != 'Priya Raman')
    return [out[0]] + sorted(out[1:], key=lambda r: (r['month'], r['received_on']), reverse=True)


# ---------------- coordinator timesheet (weeks; hours reconcile with the pay rows of the coordinator)
def timesheet_d():
    r = rng('p5ts'); weeks = []; d0 = week_start(dd('2024-12-02'))
    while d0 <= week_start(TODAY) and d0 + _d.timedelta(days=4) <= TODAY: weeks.append(d0); d0 += _d.timedelta(days=7)
    bym = collections.defaultdict(list)
    for w in weeks: bym[w.replace(day=1).isoformat()].append(w)
    tasks = ['Front desk, reminders and diary', 'Invoices, claims and payments', 'Waiting list and new enquiries', 'Room set-up, supplies and rebooking', 'Reminders, payments and end-of-month billing']
    out = []; n = 1
    for m in sorted(bym):
        ws = bym[m]; tot = PAY_BY[('Grace Mensah', m)]['hours'] if ('Grace Mensah', m) in PAY_BY else 32.0 * len(ws)
        if m == MS0: tot = round(32.0 * len(ws) * r.uniform(0.97, 1.04), 2)
        raw = [r.uniform(0.88, 1.12) for _ in ws]; s_ = sum(raw); hrs = [round(tot * x / s_ * 4) / 4.0 for x in raw]; hrs[-1] = round(hrs[-1] + (tot - sum(hrs)), 2)
        for w, h in zip(ws, hrs):
            out.append(dict(ts_id='TS-%03d' % n, week=w.isoformat(), hours=h, overtime_hours=round(max(0.0, h - 32.0), 2), tasks=tasks[(n + r.randint(0, 1)) % len(tasks)])); n += 1
    out.reverse()
    return front(out, lambda r: r['overtime_hours'] > 0 and r['week'] < ago(20))


# ---------------- leave balances (taken days from the absence weeks of Part 2)
def leave_d():
    allowed = {'Amira Lindqvist': 25, 'Daniel Okoye': 25, 'Sofia Marchetti': 25, 'Kenji Watanabe': 20, 'Priya Raman': 20, 'Lucas Moreau': 20, 'Grace Mensah': 24}
    taken = collections.Counter(); plan = {}
    for a in C.absence_rows():
        if a['kind'] == 'Training': continue
        y = int(a['week'][:4])
        if a['week'] <= ago(0): taken[(a['clinician'], y)] += a['days']
        elif a['clinician'] not in plan: plan[a['clinician']] = (a['week'], a['days'])
    rows = [(2024, 'Daniel Okoye', 25, 22), (2025, 'Amira Lindqvist'), (2025, 'Daniel Okoye'), (2025, 'Sofia Marchetti'), (2025, 'Kenji Watanabe'), (2025, 'Priya Raman'), (2025, 'Grace Mensah')] + [(2026, n) for n in allowed]
    out = []
    for i, x in enumerate(rows):
        y, nm = x[0], x[1]; al = x[2] if len(x) > 2 else allowed[nm]
        tk = x[3] if len(x) > 3 else (taken[(nm, y)] if nm != 'Grace Mensah' else (21 if y == 2025 else 14))
        row = dict(leave_id='LV-%02d' % (i + 1), year=y, person=nm, leave_days_allowed=al, days_taken=tk)
        if y == 2026 and nm in plan: row['leave_from'] = plan[nm][0]; row['leave_days_next'] = plan[nm][1]
        out.append(row)
    out.reverse()
    return front(out, lambda r: r['year'] == 2026 and r.get('leave_from'))


def services_d(): return [dict(service=s['service'], minutes=s['minutes'], fee=s['fee']) for s in services]
def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', ROLE2.get(t['role'], t['role'])), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'],
                    hours_week=t['hours_week'], monthly_salary=t['monthly_salary'], split_pct=t['split_pct'], session_rate=t['session_rate'], hourly_rate=t['hourly_rate'], session_cap=t['session_cap'],
                    session_target=t['session_target'], speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]
