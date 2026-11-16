"""Household Finance suite part 3: demo rows from hf_core (full generator output; aggregated tables list only their keys, the formulas compute the rest)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf3_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
DEBT_G, SAV_G = 'Debt payments', 'Savings'
CATG = {c['category']: c['group'] for c in category_rows}


def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def first(rows, pred):
    """move the first row that satisfies pred to the front (forms and documents show the first demo row)"""
    for i, r in enumerate(rows):
        if pred(r): return [r] + rows[:i] + rows[i + 1:]
    return rows


TXF = sorted(tx_rows(), key=lambda r: (r['date'], r['tx_id']), reverse=True)
TXD = {r['tx_id']: r for r in TXF}


def counted(r): return not r['from_goal'] and r['group'] not in (DEBT_G, SAV_G)


def tx_d():
    out = []
    for r in TXF:
        d = dict(tx_id=r['tx_id'], date=r['date'], account_id=r['account_id'], account=key('spendacct', r['account']), payee=r['payee'], category=key('category', r['category']),
                 amount=r['amount'], paid_by=key('payer', r['paid_by']))
        if r['from_goal']: d['from_goal'] = r['from_goal']
        out.append(d)
    return out


def categories_d():
    rows = [dict(category=key('category', c['category']), group=key('group', c['group'])) for c in category_rows]
    return first(rows, lambda r: r['category'] == key('category', 'Groceries'))


def accounts_d():
    return [dict(account_id=a['account_id'], account=a['account'], type=key('atype', a['type']), owner=key('person', a['owner']), opening_balance=a['opening_balance'], balance_now=a['balance_now'])
            for a in account_rows()]


BUDF = budget_rows()
def budget_d():
    rows = [dict(plan_id=b['plan_id'], month=b['month'], category=key('category', b['category']), planned=b['planned']) for b in BUDF]
    return first(rows, lambda r: r['plan_id'] == ST['plan_line'])


def income_d():
    out = []
    for r in income_rows():
        out.append(nb(dict(income_id=r['income_id'], date=r['date'], person=key('payer', r['person']), source=key('isource', r['source']), net=r['net'],
                           set_aside=r['set_aside'] or '', retirement=r['retirement'])))
    return out


def goal_cat(g): return 'Emergency fund' if g == 'SG-01' else ('Tax set-aside' if g == 'SG-10' else 'Goal savings')


def contributions_d():
    return [dict(contribution_id=c['contribution_id'], date=c['date'], goal_id=c['goal_id'], category=key('category', goal_cat(c['goal_id'])), kind=key('ctkind', c['kind']), amount=c['amount'])
            for c in contribution_rows()]


def debt_payments_d():
    return [nb(dict(payment_id=p['payment_id'], date=p['date'], debt_id=p['debt_id'], minimum=p['minimum'], extra=p['extra'] or '', amount=p['amount'])) for p in debt_payment_rows()]


def month_order(n):
    """newest complete month first, then this month and the older months (forms and documents show the first row)"""
    return [month_start(k) for k in [1, 0] + list(range(2, n + 1))]


def pva_d():
    out, i = [], 0
    for m in [month_start(k) for k in range(1, 13)]:
        for c in CATEGORY_NAMES:
            i += 1; out.append(dict(pa_id='PA-%03d' % i, month=iso(m), category=key('category', c)))
    return out


def this_month_d():
    cats = ['Groceries'] + [c for c in CATEGORY_NAMES if c != 'Groceries']
    return [dict(category=key('category', c)) for c in cats]


def compare_d():
    cats = ['Groceries', 'Eating out'] + [c for c in CATEGORY_NAMES if c not in ('Groceries', 'Eating out')]
    return [dict(category=key('category', c)) for c in cats]


def overbudget_d(n=12): return [dict(rank=i) for i in range(1, n + 1)]


_BUD_THIS = {b['category']: b['planned'] for b in BUDF if b['month'] == iso(month_start(0))}
ENVELOPES = [('Weekly groceries', 'Groceries', 'Monday'), ('Fuel and transport', 'Fuel and transport', 'Saturday'), ('Eating out', 'Eating out', 'Friday'), ('Kids and family', 'Kids and family', 'Monday'),
             ('Shopping', 'Shopping', 'Saturday'), ('Household supplies', 'Household supplies', 'Monday'), ('Entertainment', 'Entertainment', 'Friday'), ('Personal care', 'Personal care', 'Sunday'),
             ('Health costs', 'Health costs', 'Monday'), ('Work costs', 'Work and tax costs', 'Monday'), ('Car service', 'Car service', 'Saturday'), ('Small extras', 'Other', 'Sunday')]
def envelopes_d():
    return [dict(envelope=e, category=key('category', c), weekly=round(_BUD_THIS.get(c, 40) * 12 / 52), start_day=key('wday', w)) for e, c, w in ENVELOPES]
def env_status_d(): return [dict(envelope=e) for e, _, _ in ENVELOPES]


def grocery_week_d():
    cur = week_start(T0)
    weeks = [cur - _dt.timedelta(days=7 * k) for k in range(1, 52)]   # the last complete week first
    weeks = weeks + [cur]
    return [dict(week_start=iso(w), wom=key('wom', 'Week %d' % (((w.day - 1) // 7) + 1))) for w in weeks]


def monthgroup_d():
    out, i = [], 0
    for m in month_order(24):
        for g in GROUPS:
            i += 1; out.append(dict(mg_id='MG-%03d' % i, month=iso(m), group=key('group', g)))
    return out


def payees_d():
    w12 = [r for r in TXF if counted(r) and (T0 - dd(r['date'])).days <= 365]
    tot = {}
    for r in w12: tot[r['payee']] = tot.get(r['payee'], 0) + r['amount']
    planned = {'Allowance Noa', 'Allowance Ike', 'Landlord', 'Childcare provider', 'School office', 'Student loan', 'Car loan', 'Electricity supplier', 'Gas supplier', 'Water supplier',
               'Internet provider', 'Phone provider', 'Insurance agent', 'Transit pass'}
    rows = [dict(payee=p, planned=True) if p in planned else dict(payee=p) for p, _ in sorted(tot.items(), key=lambda kv: -kv[1])]
    return first(rows, lambda r: r['payee'] == 'Grocery store')


def by_person_d():
    out, i = [], 0
    for p in ('Last 12 months', 'This month', 'Last month', 'Last 3 months', 'This year', 'Last year'):
        for who in PAYERS:
            i += 1; out.append(dict(bp_id='BP-%02d' % i, paid_by=key('payer', who), period=key('period', p)))
    return out


def weekday_d():
    out, i = [], 0
    for p in ('Last 12 months', 'Last 3 months', 'Last month'):
        for w in WEEKDAYS:
            i += 1; out.append(dict(wd_id='WD-%02d' % i, weekday=key('wday', w), period=key('period', p)))
    return out


def savings_rate_d(): return [dict(month=iso(m)) for m in month_order(24)]


# duplicate rule as in the sheet: same payee and amount within dup_days days, amount at least dup_min
DUP_DAYS, DUP_MIN, LARGE = 2, 20, 400
def dup_ids():
    by = {}
    for r in TXF: by.setdefault((r['payee'], r['amount']), []).append(r)
    out = []
    for (p, a), rs in by.items():
        if a < DUP_MIN: continue
        for r in rs:
            if sum(1 for x in rs if abs((dd(x['date']) - dd(r['date'])).days) <= DUP_DAYS) > 1: out.append(r['tx_id'])
    return out


def checks_d():
    dups = sorted(dup_ids(), reverse=True)
    others = [r['tx_id'] for r in TXF if r['category'] == 'Other'][:6]
    big = [r['tx_id'] for r in TXF if r['amount'] >= LARGE and r['group'] not in ('Fixed bills', DEBT_G, SAV_G) and r['tx_id'] not in dups][:30 - len(dups) - len(others)]
    ids = dups + others + big
    ids = sorted(set(ids), key=lambda i: TXD[i]['date'], reverse=True)[:30]
    rows = [dict(tx_id=i) for i in ids]
    return first(rows, lambda r: r['tx_id'] in dups)


if __name__ == '__main__':
    for f in (tx_d, categories_d, accounts_d, budget_d, income_d, contributions_d, debt_payments_d, pva_d, this_month_d, compare_d, overbudget_d, envelopes_d, env_status_d, grocery_week_d,
              monthgroup_d, payees_d, by_person_d, weekday_d, savings_rate_d, checks_d):
        print(f.__name__, len(f()))
    print(checks_d()[:5], dup_ids())
