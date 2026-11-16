"""Nonprofit suite part 5: demo rows from np_core (full generator output where the table is the real record, aggregated where the table is a summary)."""
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np5_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
TS = iso(T0)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
TEAMID = {t['staff_id']: t for t in team}
ED_PHONE = TEAMID['NP-01']['phone']; DM_PHONE = TEAMID['NP-02']['phone']; PM_PHONE = TEAMID['NP-03']['phone']; VC_PHONE = TEAMID['NP-04']['phone']
ASST_PHONE = TEAMID['NP-05']['phone']; BK_PHONE = TEAMID['NP-08']['phone']; ACC_PHONE = TEAMID['NP-09']['phone']; PO_PHONE = TEAMID['NP-15']['phone']
STAFF_PHONE = {s['name']: s['phone'] for s in staff}
BOARD = board_rows()
TREAS = [b for b in BOARD if b['role'] == 'Treasurer'][0]; TREAS_PHONE = TREAS['phone']
VOL = [v for v in volunteer_rows() if v['status'] == 'Active'][3]; VOL_PHONE = VOL['phone']; VOL_NAME = VOL['name']
PARTNER_PHONE = fake_phone(777)
def first_of(d): return _dt.date(d.year, d.month, 1)
def qstart(d): return _dt.date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)
QS0 = qstart(T0)

# ------------------------------------------------------------ participants
PART = participant_rows()
NS_DAYS = 14
def next_dow(dow):
    d = T0 + _dt.timedelta(days=1)
    while d.weekday() != dow: d += _dt.timedelta(days=1)
    return iso(d)
SCHED = {'After-School Learning': (1, '15:30'), 'Family Food Pantry': (5, '09:30'), 'Senior Meals and Visits': (0, '11:30'), 'Summer Youth Camp': (0, '09:00')}


def participants_d():
    out = []
    for x in PART:
        r = dict(participant_id=x['participant_id'], name=x['name'], phone=x['phone'], program=key('program', x['program']), status=key('pstat', x['status']), start_date=x['start_date'],
                 last_attended=x['last_attended'], sessions=x['sessions'], contact_status=key('cstat', x['contact_status']))
        if x['status'] == 'Active' and x['program'] != 'Summer Youth Camp':
            dow, tm = SCHED[x['program']]; r['notice_date'] = next_dow(dow); r['notice_time'] = tm
        out.append(nb(r))
    return out


ACT = [x for x in PART if x['status'] == 'Active']
NS_N = sum(1 for x in ACT if (T0 - dd(x['last_attended'])).days > NS_DAYS)
def not_seen_d(): return [dict(rank=i + 1) for i in range(NS_N)]


# ------------------------------------------------------------ programs, months, sessions
def programs_d(): return [dict(program=key('program', p['program']), capacity=p['capacity'], lead=p['lead']) for p in programs]
PM = program_month_rows()
SH = shift_rows()
VH = collections.defaultdict(float)
for s in SH:
    if s['status'] == 'Worked' and s['program'] in PROGRAMS: VH[(s['month'], s['program'])] += s['hours']
FM = fund_month_rows()
FUNDING = collections.defaultdict(float)
for f in FM:
    for p in PROGRAMS:
        if f['fund'] == PROGRAM_FUND[p]: FUNDING[(f['month'], p)] += f['receipts']


def program_months_d():
    return sorted([dict(row_id=r['row_id'], month=r['month'], program=key('program', r['program']), participants=r['participants'], visits=r['visits'], new_participants=r['new_participants'],
                 sessions=r['sessions'], capacity=r['capacity'], waiting=r['waiting'], vol_hours=round(VH[(r['month'], r['program'])], 1), funding=round(FUNDING[(r['month'], r['program'])], 0)) for r in PM], key=lambda d: (d['month'], -PROGRAMS.index([p for p in PROGRAMS if key('program', p) == d['program']][0])), reverse=True)


SESS = session_rows()
def sessions_d():
    return sorted([dict(session_id=s['session_id'], date=s['date'], month=s['month'], program=key('program', s['program']), staff=key('staff', s['staff']), attendees=s['attendees'], volunteers=s['volunteers']) for s in SESS], key=lambda d: (d['date'], d['session_id']), reverse=True)


def weekday_d():
    return [dict(row_id='WA-%02d' % (i + 1), program=key('program', p), weekday=key('wday', w)) for i, (p, w) in enumerate((p, w) for p in PROGRAMS for w in WEEKDAYS)]


# ------------------------------------------------------------ summaries by program
def served_year_d(): return [dict(row_id='SY-%02d' % (i + 1), program=key('program', p), year=key('syear', y)) for i, (p, y) in enumerate((p, y) for y in reversed(YEARS) for p in PROGRAMS)]
def served_month_d(): return [dict(program=key('program', p)) for p in PROGRAMS]
def capacity_d(): return [dict(program=key('program', p)) for p in PROGRAMS]

# ------------------------------------------------------------ expenses and cost
EXP = expense_rows()[-2990:]
def expenses_d():
    return [dict(expense_id=x['expense_id'], date=x['date'], month=x['month'], category=key('category', x['category']), program=key('sprogram', x['program']), function=key('function', x['function']),
                 fund=key('fund', x['fund']), amount=x['amount']) for x in EXP]


def alloc_d():
    return [dict(category=key('category', c['category']), program_share=c['program_share'], management_share=c['management_share'], fundraising_share=c['fundraising_share'], rule=c['rule']) for c in expense_categories]


DIRECT = collections.defaultdict(float)
for x in EXP:
    if x['program'] in PROGRAMS: DIRECT[(x['month'], x['program'])] += x['amount']
PPL = {(r['month'], r['program']): r['participants'] for r in PM}
def program_cost_d():
    out = []; n = 0
    for k in range(29, -1, -1):
        m = iso(month_start(k))
        for p in PROGRAMS:
            if DIRECT[(m, p)] > 0 or PPL.get((m, p), 0) > 0:
                n += 1; out.append(dict(cost_id='PC-%03d' % n, month=m, program=key('program', p)))
    return out


def cpp_quarter_d():
    return [dict(row_id='CQ-%02d' % (i + 1), quarter_start=iso(add_months(QS0, -3 * k)), program=key('program', p)) for i, (k, p) in enumerate((k, p) for k in range(5) for p in PROGRAMS)]


# ------------------------------------------------------------ outcomes
OC = outcome_rows()
def outcomes_d(): return [dict(outcome_id=o['outcome_id'], quarter=o['quarter'], program=key('program', o['program']), outcome=key('outcome', o['outcome']), target=o['target'], actual=o['actual']) for o in OC]
UNITS = {'Finished the term': 'children', 'Homework done on time': 'children', 'Reading check passed': 'children', 'Attended 8 of 10 sessions': 'children', 'Households served': 'households',
         'Fresh produce boxes given': 'boxes', 'Referred to another service': 'people', 'Returned within 60 days': 'households', 'Meals delivered': 'meals', 'Wellbeing visits made': 'visits',
         'Joined a social event': 'people', 'Finished a full session': 'campers', 'Skill badge earned': 'badges', 'Bursary places filled': 'places', 'Parents joined an open day': 'parents'}
def outcome_defs_d():
    out = []; n = 0
    for p in PROGRAMS:
        for o in OUTCOMES[p]:
            n += 1
            tot = sum(r['target'] for r in OC if r['program'] == p and r['outcome'] == o and r['quarter'] >= '%d-01-01' % Y)
            out.append(dict(def_id='OD-%02d' % n, program=key('program', p), outcome=key('outcome', o), unit=UNITS.get(o, 'people'), target_year=tot))
    return out


def report_numbers_d():
    return [dict(row_id='RN-%02d' % (i + 1), program=key('program', p), period=key('rperiod', r)) for i, (p, r) in enumerate((p, r) for p in PROGRAMS for r in RPERIODS)]


# ------------------------------------------------------------ waiting list
WAIT = sorted([x for x in PART if x['status'] == 'Waiting'], key=lambda x: (PROGRAMS.index(x['program']), x['participant_id']))
def waiting_d():
    out = []; seen = collections.Counter()
    for x in WAIT:
        k = seen[x['program']]; seen[x['program']] += 1
        out.append(dict(participant_id=x['participant_id'], waiting_since=ago(78 - 7 * k - PROGRAMS.index(x['program']) * 3), reply_by=ahead(5 + (k % 4)), hold_until=ahead(14 + (k % 3) * 7)))
    return out


def clear_time_d(): return [dict(row_id='CT-%02d' % (i + 1), program=key('program', p), pace=key('pace', s)) for i, (p, s) in enumerate((p, s) for p in PROGRAMS for s in PACES)]
def scenario_d(): return [dict(row_id='SC-%02d' % (i + 1), program=key('program', p), serve_more=m) for i, (p, m) in enumerate((p, m) for p in PROGRAMS for m in (0.10, 0.20, 0.30))]


# ------------------------------------------------------------ staff hours on programs
def staff_hours_d():
    agg = collections.defaultdict(lambda: [0.0, 0.0])
    for r in staff_time_rows():
        if r['program'] in PROGRAMS:
            a = agg[(r['month'], r['staff'], r['program'])]; a[0] += r['hours']; a[1] += r['cost']
    rows = sorted(agg.items())
    return [dict(row_id='SH-%03d' % (i + 1), month=k[0], staff=key('staff', k[1]), program=key('program', k[2]), hours=round(v[0], 1), cost=round(v[1], 2)) for i, (k, v) in enumerate(rows)]
