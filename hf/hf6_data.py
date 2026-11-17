"""Household Finance suite part 6: demo rows from hf_core (aggregated tables list only their keys, the formulas compute the rest)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf6_lists import *

ST = story()
ACC = account_rows()
NW = networth_rows()
dd = to_date
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
ANAME = {a['account_id']: a['account'] for a in ACC}
MONTHS = sorted({r['month'] for r in NW}, reverse=True)       # newest first


def team_d():
    return [dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=key('tgroup', t['group']), phone=t['phone'], email=t['email'], note=t['note'], start=t['start']) for t in team]


def accounts_d():
    rows = [dict(account_id=a['account_id'], account=a['account'], type=key('atype', a['type']), owner=key('person', a['owner']), opening_balance=a['opening_balance'],
                 balance_now=a['balance_now'], side=key('side', a['side']), opened=a['opened']) for a in ACC]
    # partner 1 checking first: it has bills, payments and transfers, so every form field has a value
    rows.sort(key=lambda r: r['account_id'] != 'AC-02')
    return rows


def networth_d():
    rows = [dict(nw_id=r['nw_id'], month=r['month'], as_of=r['as_of'], account_id=r['account_id'], account=r['account'], type=key('atype', r['type']), side=key('side', r['side']), balance=r['balance']) for r in NW]
    rows.sort(key=lambda r: (r['month'], r['nw_id']), reverse=True)
    return rows


def nwm_d(): return [dict(month=m) for m in MONTHS]
def nwg_d(): return [dict(month=m, group=key('atype', g)) for m in MONTHS for g in ACCOUNT_TYPES]
def bnow_d(): return [dict(account=a['account']) for a in sorted(ACC, key=lambda a: a['account_id'] != 'AC-12')]
def grp_d(): return [dict(grp_id='GR-%02d' % (i * 2 + j + 1), group=key('atype', g), months_back=mb) for i, g in enumerate(ACCOUNT_TYPES) for j, mb in enumerate((0, 12))]
def alm_d(): return [dict(month=m) for m in MONTHS]
def owners_d(): return [dict(own_id='OW-%02d' % (i * 4 + j + 1), owner=key('person', o), months_back=mb) for i, o in enumerate(PERSONS) for j, mb in enumerate((0, 3, 6, 12))]


def milestones_d():
    items = [('%s net worth' % format(v, ','), v) for v in (5000, 10000, 20000, 30000, 40000, 50000, 60000, 75000, 100000, 125000, 150000, 200000)]
    items.insert(0, items.pop(5))
    return [dict(milestone=a, amount=b) for a, b in items]


def proj_inputs_d():
    vals = [(0.02, 'A fraction: 0.02 = 2 points either side of the example growth rate'), (0, 'Type an amount to start from, or leave 0 to use your savings and retirement balances now'),
            (5, 'Years the projection page and dashboard figure look ahead'), (100000, 'The net worth you want to reach, used by the target tools'), (8, 'Years you give yourself to reach it')]
    return [dict(item=key('pitem', it), value=v, note=n) for it, (v, n) in zip(PITEMS, vals)]


def projection_d():
    return [dict(month=iso(month_start(-i)), year_no=key('pyear', PYEARS[(i - 1) // 12])) for i in range(1, 61)]


BILL_ACCT = {'BL-06': 'AC-02', 'BL-13': 'AC-02', 'BL-15': 'AC-02', 'BL-19': 'AC-02', 'BL-11': 'AC-03', 'BL-16': 'AC-03', 'BL-20': 'AC-03', 'BL-05': 'AC-03'}
def bills_d():
    return [dict(bill_id=b['bill_id'], bill=b['bill'], category=key('category', b['category']), amount=b['amount'], due_day=b['due_day'], cycle=key('cycle', b['cycle']), due_month=b['due_month'],
                 account_id=BILL_ACCT.get(b['bill_id'], b['account_id']), autopay=bool(b['autopay'])) for b in bill_rows()]


def map_d(): return [dict(bill=b['bill']) for b in sorted(bill_rows(), key=lambda b: b['bill_id'] != 'BL-09')]


def transfers_d():
    rows = [dict(transfer_id=t['transfer_id'], date=t['date'], from_account=t['from_account'], to_account=t['to_account'], amount=t['amount'], purpose=key('purpose', t['purpose'])) for t in transfer_rows()]
    rows.sort(key=lambda r: (r['date'], r['transfer_id']), reverse=True)
    return rows


def payplan_d():
    out, i = [], 0
    for p in ('Partner 2', 'Partner 1'):
        for b in BASES:
            for r in ('Every two weeks', 'Twice a month', 'Monthly'):
                i += 1; out.append(dict(plan_id='PP-%02d' % i, partner=key('payer', p), basis=key('basis', b), rhythm=key('payfreq', r)))
    return out


def pspend_d():
    oth = {}
    for r in income_rows():
        if r['account_id'] in ('AC-02', 'AC-03'): oth[(r['month'], r['account_id'])] = oth.get((r['month'], r['account_id']), 0) + r['net']
    out, i = [], 0
    for m in MONTHS:
        for p, a in (('Partner 2', 'AC-03'), ('Partner 1', 'AC-02')):
            i += 1; out.append(nb(dict(ps_id='PS-%03d' % i, month=m, partner=key('payer', p), account_id=a, other_in=oth.get((m, a), ''))))
    return out


def activity_d(): return [dict(account=a['account']) for a in ACC]


def bcheck_d():
    delta = {'AC-02': -12.4, 'AC-09': 25.0}
    out = []
    for a in ACC:
        r = dict(account_id=a['account_id'], statement_date=ago(2 + int(a['account_id'][-2:]) % 4))
        if a['account_id'] != 'AC-13': r['statement'] = round(a['balance_now'] + delta.get(a['account_id'], 0), 2)
        out.append(r)
    out.sort(key=lambda r: r['account_id'] != 'AC-02')
    return out


def tx_d():
    cut = ago(90)
    rows = [t for t in tx_rows() if t['account_id'] in ('AC-02', 'AC-03') or t['date'] >= cut]
    out = [dict(tx_id=t['tx_id'], date=t['date'], account_id=t['account_id'], payee=t['payee'], category=key('category', t['category']), amount=t['amount'], paid_by=key('payer', t['paid_by'])) for t in rows]
    out.sort(key=lambda r: (r['date'], r['tx_id']), reverse=True)
    return out


if __name__ == '__main__':
    for f in (team_d, accounts_d, networth_d, nwm_d, nwg_d, bnow_d, grp_d, alm_d, owners_d, milestones_d, proj_inputs_d, projection_d, bills_d, map_d, transfers_d, payplan_d, pspend_d, activity_d, bcheck_d, tx_d):
        print(f.__name__, len(f()))
