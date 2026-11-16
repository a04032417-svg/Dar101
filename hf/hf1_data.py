"""Household Finance suite part 1: demo rows from hf_core (full output where small, thinned or aggregated where large)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf1_lists import *
from collections import defaultdict

ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}

TEAM = {t['role']: t for t in team}
P1_PHONE = TEAM['Partner 1']['phone']; P2_PHONE = TEAM['Partner 2']['phone']
INC = income_rows(); INV = invoice_rows(); PAY = pay_schedule_rows(); BIL = bill_due_rows(); BL = {b['bill_id']: b for b in bill_rows()}
BUD = budget_rows(); ACC = account_rows()
PAYCHECK_NET = 2161.0
P2_BUDGET = 5200.0


def team_d():
    return [dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=key('tgroup', t['group']), phone=t['phone'], email=t['email'], note=t['note'], start=t['start']) for t in team]


def accounts_d():
    return [dict(account_id=a['account_id'], account=a['account'], type=key('atype', a['type']), owner=key('person', a['owner']), opening_balance=a['opening_balance'], balance_now=a['balance_now']) for a in ACC]


def categories_d(): return [dict(category=r['category'], group=key('group', r['group'])) for r in category_rows]


def income_d():
    rows = sorted(INC, key=lambda r: (r['date'], r['income_id']), reverse=True)
    i = next(k for k, r in enumerate(rows) if r['source'] == 'Paycheck')
    rows.insert(0, rows.pop(i))
    return [nb(dict(income_id=r['income_id'], date=r['date'], month=r['month'], person=key('person', 'Joint' if r['source'] == 'Windfall' and r['person'] == 'Partner 2' else r['person']), source=key('isource', r['source']), gross=r['gross'], tax=r['tax'], retirement=r['retirement'],
                    other_deductions=r['other_deductions'], deductions=r['deductions'], net=r['net'], set_aside=r['set_aside'], account_id=r['account_id'], invoice_id=r['invoice_id']))
            | dict(tax=r['tax'], retirement=r['retirement'], other_deductions=r['other_deductions'], set_aside=r['set_aside']) for r in rows]


def invoices_d():
    return [nb(dict(invoice_id=r['invoice_id'], client=key('isource', r['client']), issued=r['issued'], due_date=r['due_date'], amount=r['amount'], status=key('istatus', r['status']), paid_on=r['paid_on'],
                    contact_id=r['contact_id'])) for r in INV]


def pay_schedule_d():
    import datetime as _dt
    extra = []
    for i, off in enumerate((12, 27)):
        d = _dt.date.fromisoformat(T0) + _dt.timedelta(days=off) if isinstance(T0, str) else T0 + _dt.timedelta(days=off)
        extra.append(dict(pay_id='PD-%03d' % (len(PAY) + i + 1), date=d.isoformat(), month=d.replace(day=1).isoformat(), person=key('person', 'Joint'), source='Child benefit',
                          frequency=key('payfreq', 'Twice a month'), expected_net=120.0, pays_in_month=2, extra_pay_month=False, into_joint=False))
    return [dict(pay_id=r['pay_id'], date=r['date'], month=r['month'], person=key('person', r['person']), source=r['source'], frequency=key('payfreq', r['frequency']), expected_net=r['expected_net'],
                 pays_in_month=r['pays_in_month'], extra_pay_month=bool(r['extra_pay_month']), into_joint=(r['person'] == 'Partner 1')) for r in PAY] + extra


def _months13(): return [month_start(k) for k in range(0, -13, -1)]
def pay_rhythm_d(): return [dict(month=iso(m), ahead=key('ahead', AHEAD[i])) for i, m in enumerate(_months13())]
def extra_pay_d(): return [dict(month=iso(m)) for m in _months13()]
def baseline_d(): return [dict(month=iso(month_start(k))) for k in range(12, -1, -1)]


def bills_due_d():
    out = []
    for b in BIL:
        out.append(nb(dict(due_id=b['due_id'], bill_id=b['bill_id'], bill=b['bill'], due_date=b['due_date'], month=b['month'], amount=b['amount'], status=key('bstatus', b['status']), paid_on=b['paid_on'],
                           account_id=b['account_id'], autopay=bool(b['autopay']), category=key('bcat', BL[b['bill_id']]['category']))))
    return out


def budget_d():
    rows = [dict(plan_id=b['plan_id'], month=b['month'], category=key('category', b['category']), group=key('group', b['group']), planned=b['planned']) for b in BUD]
    i = next(k for k, r in enumerate(rows) if r['plan_id'] == ST['plan_line'])
    rows.insert(0, rows.pop(i))
    return rows


# ---- paycheck split lines: a paycheck of PAYCHECK_NET (partner 1's share of the joint bills plus saving, debt and spending money)
SPLIT = [
    ('Rent share', 'Bills', 'Fixed amount', None, 761), ('Utilities and phone', 'Bills', 'Fixed amount', None, 176), ('Insurance', 'Bills', 'Fixed amount', None, 32),
    ('School costs and activities club', 'Bills', 'Fixed amount', None, 83), ('Car loan payment', 'Debt', 'Fixed amount', None, 190), ('Student loan payment', 'Debt', 'Fixed amount', None, 131),
    ('Card minimums', 'Debt', 'Fixed amount', None, 132), ('Extra payment, highest-rate card', 'Debt', 'Fixed amount', None, 28), ('Extra payment, second card', 'Debt', 'Fixed amount', None, 74),
    ('Car insurance yearly premium fund', 'Sinking funds', 'Fixed amount', None, 49), ('Holidays and gifts fund', 'Sinking funds', 'Fixed amount', None, 40),
    ('Home repairs fund', 'Sinking funds', 'Fixed amount', None, 25), ('Car replacement fund', 'Sinking funds', 'Fixed amount', None, 45), ('Kids activities fund', 'Sinking funds', 'Fixed amount', None, 18),
    ('Health costs fund', 'Sinking funds', 'Fixed amount', None, 15), ('Family trip', 'Goals', 'Fixed amount', None, 30), ('New laptop', 'Goals', 'Fixed amount', None, 22),
    ('Emergency fund', 'Savings', 'Percent', 0.03, None), ('Retirement top-up', 'Savings', 'Percent', 0.02, None), ('Groceries top-up', 'Spending money', 'Fixed amount', None, 50),
    ('Fuel and transport', 'Spending money', 'Fixed amount', None, 50), ('Personal money, partner 1', 'Spending money', 'Percent', 0.02, None), ('Children pocket money', 'Spending money', 'Fixed amount', None, 30),
    ('Rest to spending money', 'Spending money', 'Rest', None, None)]
_assigned = sum((f or 0) + (p or 0) * PAYCHECK_NET for _, _, _, p, f in SPLIT)
assert PAYCHECK_NET - _assigned >= 20, PAYCHECK_NET - _assigned


def split_lines_d():
    rows = [nb(dict(line_id='SL-%02d' % (i + 1), line=n, kind=key('lkind', k), rule=key('lrule', r), percent=p, fixed_amount=f, priority=i + 1)) for i, (n, k, r, p, f) in enumerate(SPLIT)]
    rows.insert(0, rows.pop(17))
    return rows


def alloc_d(): return [dict(line_id='SL-%02d' % (i + 1)) for i in range(len(SPLIT))]
def forecast_d(): return [dict(day_no=d, week=key('week', 'Week %d' % (d // 7 + 1))) for d in range(90)]
def low_point_d(): return [dict(pn=i) for i in range(1, 13)]
def zero_month_d(): return [dict(category=n, order=i + 1) for i, n in enumerate(CATEGORY_NAMES)]
def need_want_d(): return [dict(group=key('group', g)) for g in GROUPS]


def windfalls_d():
    wf = []
    names = {700.0: 'Year-end bonus', 1150.0: 'Refund received', 200.0: 'Gift money'}
    uses = ['Emergency fund', 'Debt payoff', 'Spending', 'Goals', 'Emergency fund', 'Spending']
    for r, u in zip([r for r in sorted(INC, key=lambda r: r['date']) if r['source'] == 'Windfall'], uses):
        wf.append((r['date'], names[r['net']], r['net'], u))
    byp = defaultdict(list)
    for r in INC:
        if r['person'] == 'Partner 1' and r['source'] == 'Paycheck': byp[r['month']].append(r)
    for m, rs in sorted(byp.items()):
        if len(rs) >= 3:
            r = sorted(rs, key=lambda x: x['date'])[2]
            wf.append((r['date'], 'Extra pay month', r['net'], {'2025-04-01': 'Debt payoff', '2025-09-01': 'Goals', '2026-03-01': 'Emergency fund'}.get(m, 'Income buffer')))
    for r in PAY:
        if r['extra_pay_month']:
            nxt = [x for x in PAY if x['month'] == r['month'] and x['person'] == 'Partner 1']
            if r is sorted(nxt, key=lambda x: x['date'])[2]: wf.append((r['date'], 'Extra pay month, expected', r['expected_net'], 'Not assigned yet'))
    wf.sort()
    return [dict(wf_id='WF-%02d' % (i + 1), date=d, source=s, amount=a, assigned_to=key('wuse', u)) for i, (d, s, a, u) in enumerate(wf)]


def take_home_d():
    pcs = sorted([r for r in INC if r['source'] == 'Paycheck'], key=lambda r: r['date'])[-40:]
    diff = {len(pcs) - 3: -35.0, len(pcs) - 9: 40.0, len(pcs) - 15: -12.5}
    return [dict(income_id=r['income_id'], bank_deposit=round(r['net'] + diff.get(i, 0.0), 2)) for i, r in enumerate(pcs)]


def glance_d():
    tx = tx_rows(); sp = defaultdict(float)
    for t in tx:
        if t['group'] != 'Savings' and not t['from_goal']: sp[t['month']] += t['amount']
    sv = defaultdict(float)
    for x in contribution_rows():
        if x['kind'] == 'Deposit': sv[x['month']] += x['amount']
    nw = {n['month']: n['balance'] for n in networth_rows() if n['account_id'] == 'AC-01'}
    out = []
    for k in range(24, -1, -1):
        m = iso(month_start(k))
        out.append(dict(month=m, joint_close=nw[m], spending=round(sp[m], 2), saved=round(sv[m], 2)))
    return out
