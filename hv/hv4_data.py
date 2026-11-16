"""HVAC and plumbing suite part 4: demo rows from hv_core (timesheets, payroll, commission, jobs, callbacks, capacity, leave)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv4_lists import *
import collections, hashlib, random

ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def h(s): return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)
PHONE = {t['name']: t['phone'] for t in team}
SID = {t['staff_id']: t for t in team}
OWNER_PH, OFFICE_PH, EQUIP_PH, COUNTER_PH, ACCT_PH, INS_PH = (SID[k]['phone'] for k in ('HV-01', 'HV-02', 'HV-11', 'HV-12', 'HV-15', 'HV-16'))
RATE = {t['name']: t['commission_pct'] for t in team}
TODAY_S = TODAY.isoformat()
LWK = week_start(TODAY) - day(7)          # Monday of the last full week
LWK_S = iso(LWK)

# ------------------------------------------------------------ timesheets (a few recent overtime weeks so the overtime pages have a story)
_TS = timesheet_rows(700)
def _bump(r, ot, extra_billed):
    rate = r['gross_pay'] / (r['paid_hours'] if r['overtime_hours'] == 0 and r['paid_hours'] <= 40 else 1.0) if False else None
    base = [t for t in team if t['name'] == r['technician']][0]['hourly_rate']
    r['clock_hours'] = round(40 + ot, 2); r['paid_hours'] = r['clock_hours']; r['overtime_hours'] = ot
    r['billed_hours'] = round(r['billed_hours'] + extra_billed, 2); r['drive_hours'] = round(r['drive_hours'] + ot * 0.2, 2); r['shop_hours'] = round(r['shop_hours'] + ot * 0.2, 2)
    r['gross_pay'] = round(base * (40 + 1.5 * ot), 2); r['loaded_cost'] = round(r['gross_pay'] * (1 + BURDEN_PCT), 2)
for r in _TS:
    if r['technician'] == 'Diego Morales' and r['week'] in (iso(LWK - day(14)), iso(LWK - day(7))): _bump(r, 5.5 if r['week'] == iso(LWK - day(7)) else 6.5, 3.4)
    if r['technician'] == 'Jamal Whitfield' and r['week'] == iso(LWK): _bump(r, 3.5, 2.1)
_LATE = {('Diego Morales', LWK_S), ('Amira Haddad', LWK_S), ("Liam O'Connell", iso(LWK - day(7)))}


def timesheets_d():
    out = []
    rows = sorted(_TS, key=lambda r: (r['week'] > LWK_S, not (r['technician'] == 'Diego Morales' and r['week'] == iso(LWK - day(7))), r['week'] if False else '', ))
    rows = [r for r in _TS if r['technician'] == 'Diego Morales' and r['week'] == iso(LWK - day(7))] + sorted([r for r in _TS if not (r['technician'] == 'Diego Morales' and r['week'] == iso(LWK - day(7))) and r['week'] <= LWK_S], key=lambda r: (r['week'], r['ts_id']), reverse=True) + [r for r in _TS if r['week'] > LWK_S]
    for r in rows:
        out.append(dict(ts_id=r['ts_id'], week=r['week'], month=r['month'], technician=key('crew', r['technician']), role=r['role'], clock_hours=r['clock_hours'], billed_hours=r['billed_hours'],
                        drive_hours=r['drive_hours'], shop_hours=r['shop_hours'], idle_hours=r['idle_hours'], overtime_hours=r['overtime_hours'], paid_hours=r['paid_hours'],
                        gross_pay=r['gross_pay'], loaded_cost=r['loaded_cost'], on_time=not ((r['technician'], r['week']) in _LATE or h(r['ts_id']) % 13 == 0)))
    return out


def payroll_d():
    return [dict(pay_id=p['pay_id'], month=p['month'], person=key('payperson', p['person']), role=p['role'], pay_type=key('paypaid', p['pay_type']), hours=p['hours'], gross=p['gross'],
                 commission=p['commission'], burden=p['burden'], total=p['total'], pay_date=p['pay_date'], status=key('paystatus', p['status'])) for p in
            sorted(pay_rows(), key=lambda p: (p['month'], p['person'] == 'Jamal Whitfield', p['pay_id']), reverse=True)]


_VANSRV = {}
for i, t in enumerate(team):
    if t['assignment'].startswith('Van') or t['assignment'].startswith('Rides'): _VANSRV[t['name']] = ahead(4 + 3 * i)
def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=t['role'], team=t['team'], pay_type=t['pay_type'], phone=t['phone'], hourly_rate=t['hourly_rate'], monthly_salary=t['monthly_salary'],
                    hours_week=t['hours_week'], commission_pct=t['commission_pct'], assignment=t['assignment'], trade=t['trade'], start=t['start'], van_service=_VANSRV.get(t['name'], ''))) for t in
            sorted(team, key=lambda t: (t['name'] != 'Amira Haddad', t['staff_id']))]


def pay_models_d():
    return [dict(model='Hourly', how='Clock hours times the hourly rate, overtime hours at the overtime multiplier', note='Simple to run, the shop carries idle time'),
            dict(model='Flat rate', how='Billed hours times a rate for each billed hour, whatever the clock says', note='Rewards speed, check callback and quality'),
            dict(model='Salary plus commission', how='A weekly salary plus a percent of sold or collected work', note='Steady income, commission rewards selling'),
            dict(model='Mixed', how='Part of the pay by clock hour and part by billed hour', note='A balance for a team of mixed jobs'),
            dict(model='Step rate', how='An hourly rate that steps up with months of experience', note='Used for apprentices, set the steps yourself')]


def comm_rules_d():
    rows = [('HVAC replacement', 'Sold', 0.020, 60, 0.50, 'Furnace, air conditioner and heat pump swaps'), ('Plumbing replacement', 'Sold', 0.020, 60, 0.50, 'Water heater and fixture swaps'),
            ('Install crew job', 'Sold', 0.025, 60, 0.50, 'Install crew lead on larger installs'), ('Heat pump install', 'Sold', 0.025, 60, 0.50, 'Two-system and heat pump installs'),
            ('Repipe', 'Collected', 0.015, 90, 0.50, 'Paid when the customer has paid'), ('Better option sold', 'Sold', 0.015, 60, 0.50, 'Middle option of a good-better-best estimate'),
            ('Best option sold', 'Sold', 0.020, 60, 0.50, 'Top option of a good-better-best estimate'), ('Service repair', 'Collected', 0.010, 30, 0.50, 'Repairs sold on a service call'),
            ('Landlord account job', 'Collected', 0.010, 90, 0.50, 'Paid when the account has paid'), ('Financed job', 'Collected', 0.015, 60, 0.50, 'Paid when the lender has paid'),
            ('Emergency call', 'Sold', 0.010, 30, 0.50, 'After-hours and emergency work'), ('Agreement sale', 'Sold', 0.000, 365, 1.00, 'Paid as a spiff, see the spiff list')]
    return [dict(rule=r, base=key('cbase', b), percent=p, clawback_days=d, clawback_pct=c_, note=n) for r, b, p, d, c_, n in rows]


# ------------------------------------------------------------ commission statements (aggregated from the full generators)
_EST = estimate_rows(); _JB = {j['job_id']: j for j in job_rows()}; _INV = {i['job_id']: i for i in invoice_rows()}; _CB = callback_rows(); _AG = agreement_rows()
_SOLD, _COLL, _JOBS, _AGR, _CLAW, _UNP = (collections.defaultdict(float) for _ in range(6))
for e in _EST:
    if e['outcome'] == 'Won' and e['technician'] in TECH6:
        k = (e['technician'], e['month']); _SOLD[k] += e['price_won']
        inv = _INV.get(e['job_id']); _COLL[k] += inv['paid_amount'] if inv else 0
        if inv and inv['balance'] > 0 and inv['date'] < ago(60): _UNP[(e['technician'], iso(month_start(0)))] += inv['balance']
for j in _JB.values():
    if j['status'] == 'Completed' and not j['is_callback'] and j['technician'] in TECH6: _JOBS[(j['technician'], j['month'])] += 1
for a in _AG:
    if a['sold_by'] in TECH6: _AGR[(a['sold_by'], a['start_date'][:8] + '01')] += 1
_EJ = {e['job_id']: e for e in _EST if e['job_id']}
for cb in _CB:
    o = _JB.get(cb['original_job'])
    if o and o['estimate_id'] in {e['estimate_id'] for e in _EST if e['outcome'] == 'Won'} and cb['days_after'] <= 60 and cb['technician'] in TECH6:
        e = _EJ.get(o['job_id'])
        if e: _CLAW[(cb['technician'], cb['month'])] += e['price_won']


def stmts_d():
    out, n = [], 0
    for mi in range(9, -1, -1):
        M = iso(month_start(mi))
        for t in TECH6:
            n += 1; k = (t, M)
            out.append(dict(st_id='ST-%03d' % n, month=M, technician=key('tech', t), jobs_done=int(_JOBS[k]), sold=round(_SOLD[k], 2), collected=round(_COLL[k], 2), agreements=int(_AGR[k]),
                            clawback_base=round(_CLAW[k], 2), unpaid_base=round(_UNP[k], 2)))
    order = {key('tech', n): i for i, n in enumerate(['Jamal Whitfield', 'Tomasz Nowak', 'Kofi Mensah', 'Elena Rossi', 'Sven Andersson', 'Diego Morales'])}
    out.sort(key=lambda r: (r['month'], -order[r['technician']]), reverse=True)
    return out


def spiffs_d():
    amt = [SPIFF_AGREEMENT, 15, 20, 20, 40, 10]
    note = ['Paid when the agreement is signed', 'Smart thermostat added to a job', 'Water filter added to a job', 'Customer chose the middle option', 'Customer chose the top option', 'A customer names the technician in a review']
    return [dict(item=key('spiffitem', i), amount=a, note=n) for i, a, n in zip(SPIFF_ITEMS, amt, note)]


# ------------------------------------------------------------ jobs, callbacks, estimates, reviews
_AGSITE = {(a['site_id'], a['start_date']): a for a in _AG}
def jobs_d():
    out = []
    for j in job_rows():
        if j['date'] < ago(92) or j['technician'] not in TECH6: continue
        sold = bool(_AGSITE.get((j['site_id'], j['date']))) or (j['status'] == 'Completed' and not j['is_callback'] and j['kind'] in ('Repair', 'Tune-up') and h(j['job_id']) % 31 == 0)
        out.append(nb(dict(job_id=j['job_id'], date=j['date'], week=j['week'], technician=key('tech', j['technician']), assistant=j['assistant'], job_type=key('jobtype', j['job_type']),
                           status=key('jobstatus', j['status']), hours=j['hours'], drive_hours=j['drive_hours'], price=j['price'], margin=round(j['margin'], 2), callback=j['is_callback'], agreement_sold=sold)))
    return out


def callbacks_d():
    out = []
    for cb in _CB:
        o = _JB.get(cb['original_job']); e = _EJ.get(cb['original_job'])
        out.append(dict(callback_id=cb['callback_id'], date=cb['date'], month=cb['month'], original_job=cb['original_job'], technician=key('tech', cb['technician']), job_type=key('jobtype', cb['job_type']),
                        reason=key('cbreason', cb['reason']), cost=cb['cost'], days_after=cb['days_after'], job_price=(e['price_won'] if e and e['outcome'] == 'Won' else 0)))
    out.sort(key=lambda r: (r['date'], r['job_price'] > 0, r['callback_id']), reverse=True)
    return out


def estimates_d():
    ests = sorted(_EST, key=lambda e: (e['date'], e['estimate_id']))[-400:]
    return [dict(estimate_id=e['estimate_id'], date=e['date'], technician=key('tech', e['technician']), job_type=key('jobtype', e['job_type']), outcome=key('estoutcome', e['outcome']),
                 est_value=e['better_price'] if e['better_price'] else e['good_price'], price_won=e['price_won']) for e in ests]


def reviews_d():
    return [dict(row_id=r['row_id'], month=r['month'], technician=key('tech', r['technician']), jobs=r['jobs'], requests_sent=r['requests_sent'], reviews_received=r['reviews_received'], referrals=r['referrals'])
            for r in review_rows()]


# ------------------------------------------------------------ scorecard, hours, capacity, seasons
_J12 = collections.defaultdict(lambda: [0, 0.0])
for j in _JB.values():
    if j['status'] == 'Completed' and not j['is_callback'] and ago(365) < j['date'] <= TODAY_S and j['technician'] in TECH6:
        _J12[j['technician']][0] += 1; _J12[j['technician']][1] += j['price']
def scorecard_d(): return [dict(row_id='SC-%02d' % (i + 1), technician=key('tech', t), period=key('period', p), jobs_12m=_J12[t][0], revenue_12m=round(_J12[t][1], 2)) for i, (p, t) in enumerate((p, t) for p in PERIODS for t in TECH6)]
def hours_week_d(): return [dict(week=iso(LWK - day(7 * (25 - i))), wk=key('wk26', 'Week %d' % (i + 1))) for i in range(25, -1, -1)]

_BOOK = collections.defaultdict(float)
for j in _JB.values():
    if j['status'] != 'Cancelled' and j['technician'] in TECH6: _BOOK[j['week']] += j['hours'] + j['drive_hours']
def capacity_d():
    out = []
    for i in range(-26, 26):
        w = iso(LWK + day(7 * (i + 1))); b = _BOOK.get(w, 0.0)
        out.append(nb(dict(week=w, booked_actual=round(b, 2) if b else '')))
    return out


def season_hours_d():
    out = []
    for i in range(12):
        M = month_start(-i); s = seasons[M.month - 1]
        out.append(dict(month=iso(M), demand_index=s['demand_index'], season=key('season', s['season'])))
    return out


def hire_d():
    out, n = [], 0
    for o in HIRE_OPTS:
        for r in (2, 4, 6): n += 1; out.append(dict(hs_id='HS-%02d' % n, option=key('hireopt', o), ramp_months=r))
    return out


def overtime_d(): return [dict(technician=key('tech', t)) for t in ['Diego Morales', 'Jamal Whitfield', 'Tomasz Nowak', 'Kofi Mensah', 'Elena Rossi', 'Sven Andersson']]
def vans_d(): return [dict(van=v['van'], technician=v['technician'], lease_monthly=v['lease_monthly']) for v in vans]
def echo_d():
    rows = [('Utilisation target', 'Percent, billed hours over clock hours'), ('Job margin target', 'Percent, set your own'), ('Overtime after, hours a week', 'Hours, confirm with your adviser'),
            ('Overtime multiplier', 'Times the hourly rate, confirm with your adviser'), ('Overtime limit, hours in 4 weeks', 'Hours that trigger a talk'), ('Clawback window, days', 'Days after the job'),
            ('Clawback share of commission', 'Percent taken back'), ('Employer extras on pay', 'Percent, confirm with your adviser')]
    return [dict(setting=a, note=b) for a, b in rows]


def leave_d():
    R = random.Random('hv4-leave'); out = []
    kinds = ['Annual leave'] * 14 + ['Sick leave'] * 7 + ['Training day'] * 6 + ['Unpaid leave'] * 3
    R.shuffle(kinds)
    for i, kd in enumerate(kinds, 1):
        p = R.choice(TECH_NAMES)
        off = R.randint(-330, -8) if i > 7 else R.randint(3, 60)
        d0 = TODAY + day(off)
        while d0.weekday() >= 5: d0 += day(1)
        ln = {'Annual leave': R.randint(3, 8), 'Sick leave': R.randint(1, 3), 'Training day': 1, 'Unpaid leave': R.randint(1, 4)}[kd]
        d1 = d0 + day(ln - 1 + (2 if ln > 5 else 0))
        while d1.weekday() >= 5: d1 += day(1)
        out.append(dict(leave_id='LV-%03d' % i, person=key('crew', p), type=key('leavetype', kd), start=iso(d0), end=iso(d1)))
    # two upcoming leaves that overlap, one upcoming training day
    out[0].update(person=key('crew', 'Kofi Mensah'), type=key('leavetype', 'Annual leave'), start=ahead(9), end=ahead(13))
    out[1].update(person=key('crew', 'Elena Rossi'), type=key('leavetype', 'Annual leave'), start=ahead(11), end=ahead(15))
    out[2].update(person=key('crew', 'Jamal Whitfield'), type=key('leavetype', 'Training day'), start=ahead(6), end=ahead(6))
    out[3].update(person=key('crew', 'Sven Andersson'), type=key('leavetype', 'Annual leave'), start=iso(week_start(TODAY + day(35))), end=iso(week_start(TODAY + day(35)) + day(8)))
    out[4].update(person=key('crew', 'Tomasz Nowak'), type=key('leavetype', 'Annual leave'), start=iso(week_start(TODAY + day(56))), end=iso(week_start(TODAY + day(56)) + day(4)))
    return sorted(out, key=lambda r: r['start'])


if __name__ == '__main__':
    for f in (timesheets_d, payroll_d, team_d, comm_rules_d, stmts_d, spiffs_d, jobs_d, callbacks_d, estimates_d, reviews_d, scorecard_d, hours_week_d, capacity_d, season_hours_d, hire_d, leave_d):
        print(f.__name__, len(f()))
    s = stmts_d()
    print([r for r in s if r['month'] == iso(month_start(0))])
    print(sum(1 for r in jobs_d() if r['agreement_sold']), len(jobs_d()), sum(1 for r in jobs_d() if r['callback']))
    cap = capacity_d(); print([(r['week'], r.get('booked_actual')) for r in cap][20:34])
