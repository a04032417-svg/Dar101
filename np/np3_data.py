"""Nonprofit suite part 3: demo rows from np_core (full generator output where small, thinned where large)."""
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np3_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
TS = iso(T0)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))
TEAM = {t['name']: t for t in team}
TEAMID = {t['staff_id']: t for t in team}
DEV_PHONE = TEAM[DEV_MANAGER]['phone']; ED_PHONE = TEAM[OWNER]['phone']
PM_PHONE = TEAMID['NP-03']['phone']; BK_PHONE = TEAMID['NP-08']['phone']; ACC_PHONE = TEAMID['NP-09']['phone']; PO_PHONE = TEAMID['NP-15']['phone']
BOARD = board_rows()
TREAS = [b for b in BOARD if b['role'] == 'Treasurer'][0]; TREAS_PHONE = TREAS['phone']
VOLS = [v for v in volunteer_rows() if v['status'] == 'Active']
VOL = VOLS[3]; VOL_PHONE = VOL['phone']
OPEN = set(OPEN_STAGES)

# ---------------------------------------------------------------- grants
GRF = [dict(g) for g in grant_rows()]
def ftype_of(g):
    if g['funder_type'] == 'Private foundation' and 'Family' in g['funder']: return 'Family foundation'
    if g['funder_type'] == 'Government grant': return 'State government' if g['funder'].startswith('State') else 'Local government'
    return g['funder_type']
def stage_of(g): return 'Closed out' if g['awarded'] > 0 and g['end_on'] < TS else g['stage']
for g in GRF:
    g['funder_type'] = ftype_of(g); g['stage'] = stage_of(g)
GRD = {g['grant_id']: g for g in GRF}
FUNDERS = sorted({g['funder'] for g in GRF})
FPHONE = {f: fake_phone(i * 3 + 1) for i, f in enumerate(FUNDERS)}
_act = [g for g in GRF if g['stage'] == 'Awarded']
for i, g in enumerate(_act[:6]):
    g['visit_on'] = ahead(12 + 7 * i) if i % 2 == 0 else ago(4 + 5 * i)


def grants_d():
    out = []
    for g in GRF:
        out.append(nb(dict(grant_id=g['grant_id'], funder=g['funder'], funder_type=key('ftype', g['funder_type']), program=key('gprogram', g['program']), project=g['project'], fund=key('fund', g['fund']),
                           stage=key('gstage', g['stage']), asked=g['asked'], awarded=g['awarded'], probability=g['probability'], owner=key('staff', g['owner']), prospect_on=g['prospect_on'], loi_on=g['loi_on'],
                           applied_on=g['applied_on'], decision_on=g['decision_on'], expected_on=g['expected_on'], start_on=g['start_on'], end_on=g['end_on'], write_hours=g['write_hours'],
                           restricted=bool(g['restricted']), phone=FPHONE[g['funder']], visit_on=g.get('visit_on', ''))))
    return out


# ---------------------------------------------------------------- payments (two open instalments are late so the chaser has work)
PAYF = [dict(p) for p in grant_payment_rows()]
_PAYD = {p['pay_id']: p for p in PAYF}
LATE_PAY = [p['pay_id'] for p in PAYF if p['status'] == 'Received' and p['pay_id'] in ('GP-102', 'GP-104')]
for pid in LATE_PAY:
    _PAYD[pid]['status'] = 'Late'; _PAYD[pid]['received_on'] = ''
PAYD = _PAYD


def payments_d():
    return [nb(dict(pay_id=p['pay_id'], grant_id=p['grant_id'], funder=p['funder'], number=p['number'], due_date=p['due_date'], amount=p['amount'], received_on=p['received_on'], status=key('gpay', p['status']))) for p in PAYF]


REPF = grant_report_rows()
REPD = {r['report_id']: r for r in REPF}


def reports_d():
    rows = sorted(REPF, key=lambda r: r['report_id'] != ST['report'])
    return [nb(dict(report_id=r['report_id'], grant_id=r['grant_id'], funder=r['funder'], kind=key('rkind', r['kind']), due_date=r['due_date'], submitted_on=r['submitted_on'], status=key('rstatus', r['status']),
                    owner=key('staff', r['owner']))) for r in rows]


BLF = grant_budget_rows()
def budget_lines_d(): return [dict(line_id=b['line_id'], grant_id=b['grant_id'], line=key('gline', b['line']), budget=b['budget']) for b in BLF]


FT_NOTE = {'Private foundation': ('Ask early, answer in a letter of inquiry, report once or twice a year', 2), 'Family foundation': ('Few staff, a personal relationship matters, short reports', 1),
           'Community foundation': ('Local focus, clear forms, a final and an interim report', 3), 'Corporate giving': ('Often tied to a visit or a thank-you, light reports', 1),
           'Local government': ('Formal forms, strict budget lines, quarterly reports', 5), 'State government': ('Formal forms, long decisions, detailed spending reports', 5)}
def funder_types_d(): return [dict(funder_type=key('ftype', t), win_note=FT_NOTE[t][0], reporting_weight=FT_NOTE[t][1]) for t in FTYPES]


STAGE_ORDER = {s: i + 1 for i, s in enumerate(STAGES)}
def stages_d(): return [dict(stage=key('gstage', s), order=STAGE_ORDER[s]) for s in STAGES]
def pipeline_d(): return [dict(stage=key('gstage', s)) for s in STAGES]
def win_rate_d(): return [dict(funder_type=key('ftype', t), period=key('period', p)) for t in FTYPES for p in PERIODS]


def quarter_start(k):
    m0 = 3 * ((T0.month - 1) // 3) + 1 + 3 * k
    y = T0.year + (m0 - 1) // 12; m = (m0 - 1) % 12 + 1
    return _dt.date(y, m, 1)
def income_quarter_d(): return [dict(quarter_start=iso(quarter_start(k))) for k in range(-4, 8)]


# ---------------------------------------------------------------- spending of the grants that have a budget and started since the cut
CUT = '2024-07-01'
BUD = collections.defaultdict(float)
for b in BLF: BUD[b['grant_id']] += b['budget']
ACT_IDS = sorted([k for k in BUD if GRD[k]['awarded'] > 0 and GRD[k]['start_on'] >= CUT], key=lambda k: GRD[k]['end_on'], reverse=True)
LINE_OF = {'Staff pay': 'Staff', 'Food purchases': 'Direct costs', 'Meals contract': 'Direct costs', 'Camp costs': 'Direct costs', 'Program supplies': 'Other costs'}
EXF = [x for x in expense_rows() if x['grant_id'] in set(ACT_IDS)]
SPENT = collections.defaultdict(float)
for x in EXF: SPENT[x['grant_id']] += x['amount']


def spending_d():
    return [dict(expense_id=x['expense_id'], date=x['date'], month=x['month'], grant_id=x['grant_id'], category=key('gcat', x['category']), amount=x['amount'], program=key('gprogram', x['program']) if x['program'] in PROGRAMS else key('gprogram', GRD[x['grant_id']]['program']),
                 fund=key('fund', x['fund']), line=key('gline', LINE_OF[x['category']])) for x in EXF]


def actual_d(): return [dict(grant_id=k, funder_type=key('ftype', GRD[k]['funder_type'])) for k in ACT_IDS]
def lines_d(): return [dict(line_no='LN-%03d' % (i + 1), grant_id=b['grant_id'], line=key('gline', b['line'])) for i, b in enumerate([b for b in BLF if b['grant_id'] in set(ACT_IDS)])]


# ---------------------------------------------------------------- funds
def funds_d(): return [dict(fund=key('fund', f['fund']), restriction=key('fundkind', f['restriction']), opening_balance=f['opening_balance']) for f in funds]
FMF = fund_month_rows()
def fund_months_d(): return [dict(row_id=r['row_id'], month=r['month'], fund=key('fund', r['fund']), receipts=r['receipts'], released=r['released'], transfers=r['transfers'], balance=r['balance']) for r in FMF]
def fund_position_d_full(): return [dict(fund=key('fund', f['fund']), month=iso(month_start(k))) for k in (0, 1) for f in funds]
CUT_REL = iso(T0 - _dt.timedelta(days=8))
def release_d():
    rows = [r for r in release_rows() if r['date'] <= CUT_REL or r['fund'] != 'Food Pantry Fund']
    rows.sort(key=lambda r: not r['grant_id'])
    return [nb(dict(release_id=r['release_id'], date=r['date'], month=r['month'], fund=key('fund', r['fund']), amount=r['amount'], program=key('program', r['program']), grant_id=r['grant_id'])) for r in rows]
def free_money_d(): return [dict(month=r['month'], cash=r['closing'], avg_expense=r['avg_monthly_expense']) for r in cash_rows()]


# ---------------------------------------------------------------- staff time (two staff months of last month are off 100% so the check has work)
STF = [dict(r) for r in staff_time_rows()]
LASTM = iso(month_start(1))
_fix = [('Priya Nair', -0.06), ('Lars Henriksen', 0.04)]
for nm, dv in _fix:
    rows = [r for r in STF if r['staff'] == nm and r['month'] == LASTM and r['percent'] > 0.08]
    r = rows[0]; f = (r['percent'] + dv) / r['percent']
    r['percent'] = round(r['percent'] + dv, 3); r['hours'] = round(r['hours'] * f, 2); r['cost'] = round(r['cost'] * f, 2)
def staff_time_d():
    return [nb(dict(time_id=r['time_id'], month=r['month'], staff=key('staff', r['staff']), target_kind=key('tkind', r['target_kind']), grant_id=r['grant_id'], program=key('sprogram', r['program']),
                    function=r['function'], percent=r['percent'], hours=r['hours'], cost=r['cost'])) for r in STF]


def staff_check_d():
    out = []; n = 0
    for k in (2, 1, 0):
        for s in staff:
            n += 1
            out.append(dict(check_id='TC-%02d' % n, staff=key('staff', s['name']), month=iso(month_start(k)), phone=s['phone']))
    return out


# ---------------------------------------------------------------- calendar: open instalments and reports due in 90 days, plus items done in the last 30 days
def calendar_d():
    lo, hi = iso(T0 - _dt.timedelta(days=30)), iso(T0 + _dt.timedelta(days=90))
    rows = []
    for p in PAYF:
        if p['status'] != 'Received' and p['due_date'] <= hi: rows.append((p['due_date'], p['pay_id'], 'Instalment'))
        elif p['status'] == 'Received' and p['received_on'] >= lo: rows.append((p['received_on'], p['pay_id'], 'Instalment'))
    for r in REPF:
        if r['status'] != 'Submitted' and r['due_date'] <= hi: rows.append((r['due_date'], r['report_id'], 'Report'))
        elif r['status'] == 'Submitted' and r['submitted_on'] >= lo: rows.append((r['submitted_on'], r['report_id'], 'Report'))
    rows.sort()
    return [dict(item_id=i, kind=key('ckind', k)) for _, i, k in rows]


if __name__ == '__main__':
    print(len(GRF), len(PAYF), len(REPF), len(BLF), len(ACT_IDS), len(EXF), len(lines_d()), len(release_d()), len(STF), len(calendar_d()), LATE_PAY)
    print(collections.Counter(g['stage'] for g in GRF), collections.Counter(g['funder_type'] for g in GRF))
