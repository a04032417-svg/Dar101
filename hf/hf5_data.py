"""Household Finance suite part 5: demo rows from hf_core (full output where small, aggregated by month where large)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf5_lists import *
from collections import defaultdict
import datetime as _dt

ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_(n): return iso(T0 + _dt.timedelta(days=n))
def first(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [r] + rows[:i] + rows[i + 1:]
    return rows

TEAM = {t['role']: t for t in team}
PH = {'p1': TEAM['Partner 1']['phone'], 'p2': TEAM['Partner 2']['phone'], 'gp': TEAM['Grandparent']['phone'], 'payroll': TEAM['Payroll office']['phone'], 'tax': TEAM['Tax preparer']['phone'],
      'ins': TEAM['Insurance agent']['phone'], 'child': TEAM['Childcare provider']['phone'], 'school': TEAM['School office']['phone'], 'mech': TEAM['Car mechanic']['phone'],
      'bank': TEAM['Bank branch']['phone']}
PH['member'] = PH['gp']

ACCS = account_rows()
ACC = {a['account_id']: a['account'] for a in ACCS}
EMERGENCY, INSURANCE = 'Emergency fund', 'Car insurance yearly premium'
GOALS = goal_rows()
GNAME = {g['goal_id']: g['goal'] for g in GOALS}
TDAY = {'SG-01': 5, 'SG-02': 5, 'SG-03': 12, 'SG-04': 12, 'SG-05': 15, 'SG-06': 20, 'SG-07': 3, 'SG-08': 15, 'SG-09': 17, 'SG-10': 15, 'SG-11': 12, 'SG-12': 3}


def _aug20():
    y = T0.year if _dt.date(T0.year, 8, 20) > T0 else T0.year + 1
    return iso(_dt.date(y, 8, 20))


EXTRA_GOALS = [
    dict(goal_id='SG-11', goal='Back-to-school costs', kind='Sinking fund', account_id='AC-05', target=600.0, target_date=_aug20(), monthly_amount=55.0, saved=330.0, priority='Medium',
         start_date=iso(month_start(6))),
    dict(goal_id='SG-12', goal='Phone replacement', kind='Savings goal', account_id='AC-05', target=700.0, target_date=d_(18), monthly_amount=60.0, saved=700.0, priority='Low',
         start_date=iso(month_start(13)))]
for g in EXTRA_GOALS: GNAME[g['goal_id']] = g['goal']
ALLGOALS = GOALS + EXTRA_GOALS


def goals_d():
    rows = [dict(goal_id=g['goal_id'], goal=g['goal'], kind=key('gkind', g['kind']), account=ACC[g['account_id']], target=g['target'], target_date=g['target_date'], monthly_amount=g['monthly_amount'],
                 saved=g['saved'], priority=key('priority', g['priority']), start_date=g['start_date'], transfer_day=TDAY[g['goal_id']]) for g in ALLGOALS]
    return first(rows, lambda r: r['goal'] == INSURANCE)


def contributions_d():
    rows = list(contribution_rows())
    n = len(rows)
    extra = []
    for i in range(6):
        extra.append(('SG-11', iso(month_start(6 - i))[:8] + '12', 55.0))
    amts = [60.0] * 10 + [50.0, 50.0]
    for i in range(12):
        extra.append(('SG-12', iso(month_start(13 - i))[:8] + '03', amts[i]))
    out = []
    for r in rows:
        out.append(dict(contribution_id=r['contribution_id'], date=r['date'], goal=r['goal'], kind=key('ctkind', r['kind']), amount=r['amount'], account=ACC[r['account_id']],
                        from_account=ACC[r['from_account']] if r['from_account'] else ''))
    for i, (gid, dt_, amt) in enumerate(sorted(extra, key=lambda e: e[1])):
        out.append(dict(contribution_id='CT-%04d' % (n + 1 + i), date=dt_, goal=GNAME[gid], kind=key('ctkind', 'Deposit'), amount=amt, account=ACC['AC-05'], from_account=ACC['AC-01']))
    out.sort(key=lambda r: (r['date'], r['contribution_id']))
    for i, r in enumerate(out): r['contribution_id'] = 'CT-%04d' % (i + 1)
    out = first(out[::-1], lambda r: r['kind'] == key('ctkind', 'Deposit') and r['goal'] != 'Phone replacement')
    return [nb(r) for r in out]


def accounts_d():
    return [dict(account_id=a['account_id'], account=a['account'], type=key('atype', a['type']), owner=key('person', a['owner']), opening_balance=a['opening_balance'], balance_now=a['balance_now'])
            for a in ACCS]


def income_d():
    rows, w = [], 0
    for r in income_rows():
        pers = r['person']
        if r['source'] == 'Windfall':
            w += 1
            if w % 3 == 0: pers = 'Joint'
        rows.append(dict(income_id=r['income_id'], date=r['date'], person=key('person', pers), source=key('isource', r['source']), net=r['net'], gross=r['gross']))
    return first(rows[::-1], lambda r: r['source'] == key('isource', 'Windfall'))


def bills_d():
    return [nb(dict(bill_id=b['bill_id'], bill=b['bill'], category=key('category', b['category']), amount=b['amount'], due_day=b['due_day'], cycle=key('cycle', b['cycle']), due_month=b['due_month']))
            for b in bill_rows()]


def tx_d():
    cut = iso(month_start(7))
    rows = [t for t in tx_rows() if t['date'] >= cut or t['from_goal']]
    return [nb(dict(tx_id=t['tx_id'], date=t['date'], payee=t['payee'], account_id=t['account_id'], category=key('category', t['category']), amount=t['amount'], from_goal=t['from_goal'])) for t in rows]


def retirement_d():
    rows = [dict(rt_id=r['rt_id'], date=r['date'], person=key('person', r['person']), source=key('rtsource', r['source']), account=ACC[r['account_id']], employee_amount=r['employee_amount'],
                 employer_amount=r['employer_amount']) for r in retirement_rows()]
    return first(rows[::-1], lambda r: r['source'] == key('rtsource', 'Payroll'))


def rank_d(n): return [dict(rank=i) for i in range(1, n + 1)]
def goal_names_d(): return first([dict(goal=g['goal']) for g in ALLGOALS], lambda r: r['goal'] == INSURANCE)
def months_d(n=25): return first([dict(month=iso(month_start(k))) for k in range(n - 1, -1, -1)], lambda r: r['month'] == iso(month_start(1)))
def months_ahead_d(): return first([dict(month=iso(month_start(-k))) for k in range(12)], lambda r: r['month'] == iso(month_start(-1)))


def essential_d():
    tx = tx_rows(); m = defaultdict(lambda: defaultdict(float))
    for t in tx: m[t['month']][t['group']] += t['amount']
    out = []
    for k in range(24, -1, -1):
        ms = iso(month_start(k)); g = m[ms]
        out.append(dict(month=ms, fixed=round(g['Fixed bills'], 2), variable=round(g['Variable needs'], 2), debt=round(g['Debt payments'], 2)))
    return out


def annual_d():
    rows = [('Car insurance yearly premium', 'Insurance', 1260.0, 1, 5, INSURANCE), ('Car registration', 'Car service', 185.0, 3, 12, ''), ('Annual car checks', 'Car service', 140.0, 9, 20, ''),
            ('Tax preparer fee', 'Work and tax costs', 240.0, 3, 20, ''), ('Antivirus yearly renewal', 'Subscriptions', 59.99, 12, 24, ''),
            ('Holidays and December costs', 'Holidays and trips', 1800.0, 12, 12, 'Holidays'), ('Gifts', 'Gifts', 700.0, 12, 8, 'Gifts'),
            ('Home repairs', 'Household supplies', 1200.0, 6, 20, 'Home repairs'), ("Kids' activities", 'Kids and family', 900.0, 9, 3, "Kids' activities"),
            ('Family trip', 'Holidays and trips', 2400.0, 8, 2, 'Family trip'), ('Tax set-aside, yearly bill', 'Tax set-aside', 4200.0, 1, 15, 'Tax set-aside'),
            ('Back-to-school costs', 'Childcare and school', 600.0, 8, 20, 'Back-to-school costs'), ('Birthday celebrations', 'Gifts', 360.0, 6, 15, ''),
            ('Yearly health checks', 'Health costs', 300.0, 5, 10, '')]
    return [nb(dict(item_id='AN-%02d' % (i + 1), item=it, category=key('acat', c), amount=a, due_month=m, due_day=d, goal=g)) for i, (it, c, a, m, d, g) in enumerate(rows)]


def plan_d(): return [dict(months=i) for i in range(1, 13)]


def summary_d():
    out, i = [], 0
    for w in RWIN:
        for acc in ('Retirement account partner 1', 'Retirement account partner 2', 'Brokerage account'):
            i += 1; out.append(dict(row_id='RS-%02d' % i, window=key('rwindow', w), account=acc))
    return out


def changes_d():
    rows = [(610, 'Emergency fund', 300, 350, 'Income changed'), (540, 'Car replacement', 150, 200, 'Income changed'), (480, 'Holidays', 100, 120, 'Price changed'),
            (430, 'Home repairs', 100, 80, 'Paused'), (390, 'Gifts', 50, 60, 'Price changed'), (340, 'Tax set-aside', 700, 900, 'Catch up'), (290, "Kids' activities", 60, 75, 'Date moved'),
            (250, 'Family trip', 120, 160, 'Extra paycheck'), (200, 'Emergency fund', 350, 400, 'Catch up'), (110, 'Car insurance yearly premium', 90, 105, 'Price changed'),
            (100, 'New laptop', 100, 150, 'Cost cut'), (60, 'Phone replacement', 50, 60, 'Catch up'), (30, 'Back-to-school costs', 40, 55, 'Catch up')]
    return [dict(change_id='GC-%02d' % (i + 1), date=iso(T0 - _dt.timedelta(days=a)), goal=g, old_monthly=o, new_monthly=n, reason=key('reason', r)) for i, (a, g, o, n, r) in enumerate(rows)]
