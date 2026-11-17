"""Household Finance suite part 4: demo rows from hf_core (debts, payments, accounts, income, net worth) and the key rows of the calculated tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf4_lists import *
from collections import defaultdict
import datetime as _dt

ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_(n): return iso(T0 + _dt.timedelta(days=n))

TEAM = {t['role']: t for t in team}
PH = {'p1': TEAM['Partner 1']['phone'], 'p2': TEAM['Partner 2']['phone'], 'gp': TEAM['Grandparent']['phone'], 'payroll': TEAM['Payroll office']['phone'], 'tax': TEAM['Tax preparer']['phone'],
      'ins': TEAM['Insurance agent']['phone'], 'bank': TEAM['Bank branch']['phone']}
CONTACT = {'bank': first_name(TEAM['Bank branch']['name']), 'tax': first_name(TEAM['Tax preparer']['name']), 'ins': first_name(TEAM['Insurance agent']['name']), 'payroll': first_name(TEAM['Payroll office']['name']), 'gp': first_name(TEAM['Grandparent']['name'])}

DEBT_ROWS = debt_rows()
DNAME = {d['debt_id']: d['debt'] for d in DEBT_ROWS}
# five debts of the household plus seven that are already paid off (kept so a closed debt stays on record)
PAID_OFF = [('DB-06', 'Store card (paid off)', 'Credit card', 0.2299, 35.0, 5, 900, 0, 'Partner 2', '2022-03-10'),
            ('DB-07', 'Phone instalment (paid off)', 'Instalment loan', 0.0, 48.0, 12, 700, 12, 'Partner 1', '2024-02-12'),
            ('DB-08', 'Laptop instalment (paid off)', 'Instalment loan', 0.0, 62.0, 18, 1100, 24, 'Partner 2', '2023-06-18'),
            ('DB-09', 'Sofa instalment (paid off)', 'Instalment loan', 0.0899, 40.0, 3, 800, 12, 'Joint', '2023-09-03'),
            ('DB-10', 'Family loan (paid off)', 'Instalment loan', 0.0, 150.0, 25, 3000, 36, 'Joint', '2022-11-25'),
            ('DB-11', 'Overdraft (cleared)', 'Credit card', 0.1899, 25.0, 8, 500, 0, 'Partner 1', '2023-01-08'),
            ('DB-12', 'Holiday instalment (paid off)', 'Instalment loan', 0.0699, 70.0, 20, 2400, 24, 'Joint', '2024-04-20')]


def debts_d():
    rows = [dict(debt_id=d['debt_id'], debt=d['debt'], kind=key('dkind', d['kind']), account_id=d['account_id'], balance=d['balance'], rate=d['rate'], min_payment=d['min_payment'], due_day=d['due_day'],
                 extra_planned=int(d['extra_planned']), original_amount=int(d['original_amount']), term_months=d['term_months'], owner=key('person', d['owner']), opened=d['opened']) for d in DEBT_ROWS]
    for i, (did, nm, kd, rt, mn, dd, orig, tm, ow, op) in enumerate(PAID_OFF):
        rows.append(dict(debt_id=did, debt=nm, kind=key('dkind', kd), balance=0.0, rate=rt, min_payment=mn, due_day=dd, extra_planned=0, original_amount=orig, term_months=tm, owner=key('person', ow), opened=op))
    return rows


def payments_d():
    return [dict(payment_id=p['payment_id'], date=p['date'], debt_id=p['debt_id'], debt=p['debt'], minimum=p['minimum'], extra=int(p['extra'] or 0), amount=p['amount'], interest=p['interest'],
                 principal=p['principal'], balance_after=p['balance_after']) for p in debt_payment_rows()] + _paidoff_payments()


def _paidoff_payments():
    vals = [(60, 0, 4.1), (45, 15, 3.3), (120, 30, 6.8), (35, 0, 2.2), (80, 20, 5.4), (150, 0, 9.7), (55, 10, 3.9)]
    return [dict(payment_id='DP-%04d' % (123 + i), date='2026-%02d-%02d' % (1 + i % 4, 5 + i), debt_id='DB-%02d' % (6 + i), minimum=float(m), extra=e, amount=float(m + e), interest=it,
                 principal=round(m + e - it, 2), balance_after=0.0) for i, (m, e, it) in enumerate(vals)]


def accounts_d():
    return [dict(account_id=a['account_id'], account=a['account'], type=key('atype', a['type']), owner=key('person', a['owner']), opening_balance=a['opening_balance'], balance_now=a['balance_now'])
            for a in account_rows()]


def income_d():
    return [dict(income_id=r['income_id'], date=r['date'], person=key('payer', r['person']), source=key('isource', r['source']), gross=r['gross'], net=r['net']) for r in income_rows()]


def networth_d():
    return [dict(nw_id=r['nw_id'], month=r['month'], account_id=r['account_id'], type=key('atype', r['type']), side=key('side', r['side']), balance=r['balance']) for r in networth_rows()]


def sched_d(): return [dict(month_no=i, planyear=key('planyear', 'Year %d' % (1 + (i - 1) // 12))) for i in range(1, 61)]
def slots_d(): return [dict(slot=i) for i in range(1, 13)]
def plans_d(): return [dict(plan=key('plans', p)) for p in PLANS]
def debt_names_d(): return [dict(debt=d['debt']) for d in debts_d()]
def xsteps_d(): return [dict(step=key('xstep', s)) for s in XSTEPS]
def windfall_d(): return [dict(wfa=w) for w in WINDFALLS]
def months24_d(): return [dict(month=iso(month_start(k))) for k in range(24, 0, -1)]
def months25_d(): return [dict(month=iso(month_start(k))) for k in range(24, -1, -1)]
def ratios_d(): return [dict(ratio=key('ratio', r)) for r in RATIOS]

# essential spending a month (fixed bills and variable needs, last three complete months): the default of one tool
_tx = tx_rows(); _es = defaultdict(float)
for _t in _tx:
    if _t['group'] in ('Fixed bills', 'Variable needs') and not _t['from_goal']: _es[_t['month']] += _t['amount']
ESSENTIAL = round(sum(_es[iso(month_start(k))] for k in (1, 2, 3)) / 3 / 50) * 50.0
EMERGENCY = [a for a in account_rows() if a['account'] == 'Emergency savings'][0]['balance_now']
