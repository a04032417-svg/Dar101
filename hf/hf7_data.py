"""Household Finance suite part 7: demo rows from hf_core (full generator output; aggregated tables list only their keys, the formulas compute the rest)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf7_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
SHARED = shared_cost_rows()
KIDS_ROWS = kid_cost_rows()
ALLOW = allowance_rows()


def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def first(rows, pred):
    """move the first row that satisfies pred to the front (forms and documents show the first demo row)"""
    for i, r in enumerate(rows):
        if pred(r): return [r] + rows[:i] + rows[i + 1:]
    return rows


def month_order(n):
    """newest complete month first, then this month and the older months (forms and documents show the first row)"""
    return [month_start(k) for k in [1, 0] + list(range(2, n + 1))]


def team_d():
    return [dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=key('tgroup', t['group']), phone=t['phone'], email=t['email'], note=t['note'], start=t['start'])
            for t in team]


# shared costs: older rows vary the split rule so the three rules are all used (the story months, the last 6, stay as generated)
def shared_rows():
    cut = iso(month_start(6))
    out, i = [], 0
    for r in SHARED:
        r = dict(r)
        if r['date'] < cut:
            i += 1
            if i % 9 == 4: r['split_rule'], r['agreed_p1'] = 'Equal', 0.5
            elif i % 11 == 6: r['split_rule'], r['agreed_p1'] = 'Custom', 0.7
        out.append(r)
    return out


def shared_d():
    rows = [dict(shared_id=r['shared_id'], date=r['date'], description=r['description'], category=key('sharedcat', r['category']), amount=r['amount'], paid_by=key('payer', r['paid_by']),
                 agreed_p1=r['agreed_p1'], split_rule=key('split', r['split_rule'])) for r in shared_rows()]
    rows.sort(key=lambda r: (r['date'], r['shared_id']), reverse=True)
    return first(rows, lambda r: r['category'] == key('sharedcat', 'Household supplies') and r['paid_by'] == key('payer', 'Partner 2'))


def settle_d():
    rows = [nb(dict(settle_id=s['settle_id'], month=s['month'], settled_on=s['settled_on'])) for s in settle_rows()]
    rows.sort(key=lambda r: r['month'], reverse=True)
    return first(rows, lambda r: 'settled_on' not in r)


def income_d():
    rows = [dict(income_id=r['income_id'], date=r['date'], person=key('payer', r['person']), source=r['source'], net=r['net']) for r in income_rows()]
    rows.sort(key=lambda r: (r['date'], r['income_id']), reverse=True)
    return rows


def fair_split_d(): return [dict(month=iso(m)) for m in month_order(24)]


def split_cmp_d():
    out, i = [], 0
    for rule in ('Income share', 'Equal', 'Custom'):
        for m in (3, 1, 6, 12):
            i += 1; out.append(dict(sc_id='SC-%02d' % i, rule=key('split', rule), months=m))
    return out


def transfer_d():
    return [dict(partner=key('payer', p), basis=key('tbasis', b)) for p in PAYERS for b in TBASIS]


def overpaid_d(): return [dict(month=iso(m)) for m in month_order(24)]
def settle_plan_d(): return [dict(months_back=k) for k in [3, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12]]


def kids_costs_d():
    rows = [dict(kid_cost_id=r['kid_cost_id'], date=r['date'], child=key('child', r['child']), kind=key('kidkind', r['kind']), amount=r['amount'], tx_id=r['tx_id']) for r in KIDS_ROWS]
    rows.sort(key=lambda r: (r['date'], r['kid_cost_id']), reverse=True)
    return first(rows, lambda r: r['kind'] == key('kidkind', 'Childcare'))


def allowances_d():
    rows = [dict(allowance_id=r['allowance_id'], date=r['date'], child=key('kid', r['child']), amount=r['amount'], saved=r['saved'], paid_by=key('payer', r['paid_by'])) for r in ALLOW]
    rows.sort(key=lambda r: (r['date'], r['allowance_id']), reverse=True)
    return first(rows, lambda r: r['child'] == key('kid', 'Noa'))


def _kc_total(child, year):
    return sum(r['amount'] for r in KIDS_ROWS if r['child'] == child and r['date'].startswith(str(year)))


def kids_year_d():
    out = []
    for yr in (Y, Y - 1, Y - 2, Y + 1):
        for ch, tag in (('Noa', 'N'), ('Ike', 'I'), ('Both children', 'B')):
            if yr == Y + 1: plan = _kc_total(ch, Y - 1) * 1.04
            elif yr == Y: plan = _kc_total(ch, Y - 1) * 1.03 * (1.0)
            else: plan = _kc_total(ch, yr) * 1.08
            out.append(dict(ky_id='KY-%d-%s' % (yr, tag), year=yr, child=key('child', ch), plan=int(round(plan / 10.0)) * 10))
    return out


def cost_member_d():
    return [dict(cm_id='CM-%d-%d' % (yr, i + 1), member=key('member', m), year=yr) for yr in (Y, Y - 1, Y - 2) for i, m in enumerate(MEMBERS)]


def allowance_summary_d():
    out, i = [], 0
    for m in month_order(24):
        for k in KID:
            i += 1; out.append(dict(as_id='AS-%03d' % i, month=iso(m), child=key('kid', k)))
    return out


def scenarios_d():
    rows = []
    for i, r in enumerate(scenario_rows()):
        rows.append(dict(scenario_id=r['scenario_id'], scenario=key('scen', r['scenario']), item=key('sitem', r['item']), value=r['value'], unit=r['unit'], set_on=ago(9 + i * 21)))
    return rows


CUT = {'Rent or mortgage': 0, 'Utilities': 0.1, 'Phone and internet': 0.15, 'Insurance': 0, 'Childcare and school': 0.1, 'Groceries': 0.2, 'Fuel and transport': 0.25, 'Health costs': 0.1,
       'Household supplies': 0.3, 'Car service': 0.3, 'Kids and family': 0.3, 'Work and tax costs': 0.2, 'Other': 0.5, 'Eating out': 0.8, 'Subscriptions': 0.6, 'Shopping': 0.9,
       'Entertainment': 0.8, 'Personal care': 0.4, 'Holidays and trips': 0.9, 'Gifts': 0.7, 'Emergency fund': 0.5, 'Goal savings': 0.8, 'Retirement': 0.5, 'Tax set-aside': 0.7,
       'Card payments': 0, 'Car loan': 0, 'Student loan': 0, 'Extra debt payment': 1.0}
_PLAN_EXTRA = {'Holidays and trips': 150, 'Gifts': 90}
_BUD = {b['category']: b['planned'] for b in budget_rows() if b['month'] == iso(month_start(0))}
CATG = {c['category']: c['group'] for c in category_rows}


def lose_d():
    rows = [dict(category=c, group=key('group', CATG[c]), plan=_BUD.get(c, _PLAN_EXTRA.get(c, 100)), cut_share=CUT[c]) for c in CATEGORY_NAMES]
    return first(rows, lambda r: r['category'] == 'Eating out')


def expense_shock_d(): return [dict(month=iso(month_start(-k))) for k in range(0, 12)]


def rate_change_d():
    spec = {'Card A': (5600.0, 0.2499, 0), 'Card B': (3300.0, 0.1999, 0), 'Card C': (2100.0, 0.1599, 0), 'Car loan': (13600.0, 0.0699, 36), 'Student loan': (17400.0, 0.045, 72)}
    out, i = [], 0
    for pts in (0.02, 0.01, 0.03):
        for d in DEBTS:
            i += 1; b, r, t = spec[d]
            out.append(dict(rc_id='RC-%02d' % i, debt=key('debt', d), balance=b, rate=r, term_months=t, points=pts))
    return out


def new_baby_d(): return [dict(month=iso(month_start(-2 - k))) for k in range(12)]


def mortgage_pay(price=310000.0, down=40000.0, rate=0.059, years=25):
    n, r, loan = years * 12, rate / 12, price - down
    return loan * r / (1 - (1 + r) ** -n)


def mortgage_d():
    pay = round(mortgage_pay(), 0)
    items = [('Payment (rent now, mortgage after)', 1650, pay), ('Upkeep and local charges', 0, 258), ('Home insurance', 14, 55), ('Utilities', 160, 190), ('Internet and phone', 100, 100),
             ('Moving costs spread over 5 years', 0, 60), ('Furnishing spread over 5 years', 0, 50), ('Travel to work and school', 120, 90), ('Garden and seasonal', 0, 30),
             ('Repairs fund set aside', 0, 120), ('Loan fees spread over the term', 0, 25), ('Parking and storage', 45, 0)]
    return [dict(item=a, rent_now=b, mortgage_cost=c) for a, b, c in items]


if __name__ == '__main__':
    for f in (team_d, shared_d, settle_d, income_d, fair_split_d, split_cmp_d, transfer_d, overpaid_d, settle_plan_d, kids_costs_d, allowances_d, kids_year_d, cost_member_d,
              allowance_summary_d, scenarios_d, lose_d, expense_shock_d, rate_change_d, new_baby_d, mortgage_d):
        print(f.__name__, len(f()))
    print(sum(r['plan'] for r in lose_d()), mortgage_pay())
