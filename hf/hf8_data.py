"""Household Finance suite part 8: demo rows from hf_core (full output where small, aggregated by month, category and tax year where large)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf8_lists import *
from collections import defaultdict
import datetime as _dt

ST = story()
T0 = TODAY
MS0 = month_start(0)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_(n): return iso(T0 + _dt.timedelta(days=n))
def first(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [r] + rows[:i] + rows[i + 1:]
    return rows

TEAM = {t['role']: t for t in team}
PH = {'p1': TEAM['Partner 1']['phone'], 'p2': TEAM['Partner 2']['phone'], 'gp': TEAM['Grandparent']['phone'], 'landlord': TEAM['Landlord']['phone'], 'payroll': TEAM['Payroll office']['phone'],
      'tax': TEAM['Tax preparer']['phone'], 'ins': TEAM['Insurance agent']['phone'], 'child': TEAM['Childcare provider']['phone'], 'school': TEAM['School office']['phone'],
      'mech': TEAM['Car mechanic']['phone'], 'util': TEAM['Utility company']['phone'], 'bank': TEAM['Bank branch']['phone']}
CLIENTS = [t for t in team if t['role'] == 'Freelance client']
PH['member'] = PH['gp']
PH['clienta'], PH['clientb'] = CLIENTS[0]['phone'], CLIENTS[1]['phone']

BIG_SAVING = 450.0
PAY_PER_YEAR = 26

# ------------------------------------------------------------------ big purchases and options
def big_purchases_d():
    rows = [dict(bp_id=b['bp_id'], item=b['item'], kind=key('bpkind', b['kind']), planned_date=b['planned_date'], target=b['target'], saved=b['saved'], goal_id=b['goal_id'],
                 priority=key('priority', b['priority']), status=key('bpstatus', b['status'])) for b in big_purchase_rows()]
    extra = [('Dishwasher', 'Equipment', -95, 640.0, 640.0, '', 'Medium', 'Bought'), ('Bicycles for the children', 'Equipment', 120, 560.0, 210.0, '', 'Low', 'Saving'),
             ('Garden fence repair', 'Home', -160, 1150.0, 1150.0, '', 'Medium', 'Bought'), ('Roof repair, first part', 'Home', 190, 2600.0, 1640.0, 'SG-06', 'High', 'Saving'),
             ('Sofa replacement', 'Home', -230, 880.0, 880.0, '', 'Low', 'Bought'), ('Winter break trip', 'Family trip', 34, 1100.0, 900.0, 'SG-03', 'Medium', 'Saving')]
    for i, (it, k, off, tg, sv, g, pr, stt) in enumerate(extra):
        rows.append(dict(bp_id='BP-%02d' % (7 + i), item=it, kind=key('bpkind', k), planned_date=d_(off), target=tg, saved=sv, goal_id=g, priority=key('priority', pr), status=key('bpstatus', stt)))
    return [nb(r) for r in rows]


def options_d():
    return [dict(option_id=o['option_id'], bp_id=o['bp_id'], option=o['option'], price=o['price'], down_payment=int(o['down_payment']), trade_in=int(o['trade_in']),
                 loan_months=o['loan_months'], rate=o['rate'], running_cost=o['running_cost']) for o in purchase_option_rows()]


def car_decision_d():
    out, i = [], 0
    for opt, terms in ((CAR_OPTS[0], (48, 24, 36, 60, 72, 84)), (CAR_OPTS[1], (36, 24, 48, 60, 72, 84)), (CAR_OPTS[2], (0,))):
        for t in terms:
            i += 1; out.append(dict(row_id='CD-%02d' % i, option=key('caropt', opt), loan_months=t))
    return out


# ------------------------------------------------------------------ move and event
_PAID = {'MV-02': 200.0, 'MV-03': 60.0, 'MV-08': 150.0, 'MV-09': 35.0, 'MV-10': 120.0, 'MV-11': 80.0}
def move_plan_d():
    return [dict(move_id=m['move_id'], item=m['item'], estimate=m['estimate'], paid=_PAID.get(m['move_id'], 0.0), due_date=m['due_date'], kind=key('mvkind', m['kind']), move_date=m['move_date'])
            for m in move_item_rows()]


def move_cash_d(): return [dict(month=iso(month_start(-k))) for k in range(13)]


_EPAID = {'EI-02': 0.0, 'EI-07': 100.0}
def event_budget_d():
    out = []
    for e in event_item_rows():
        out.append(dict(event_item_id=e['event_item_id'], event=e['event'], item=key('eitem', e['item']), estimate=e['estimate'], paid=_EPAID.get(e['event_item_id'], e['paid']), due_date=e['due_date'],
                        deposit=bool(e['deposit']), target_total=int(e['target_total'])))
    return out


def rb_inputs_d():
    rows = [('Home price', '', 310000, 'The price you would pay for the home'), ('Down payment', '', 40000, 'Cash you pay at purchase, taken from savings'),
            ('Mortgage rate, percent a year', '', 5.9, 'Ask your lender for a quote, this is a typed number'), ('Mortgage term, years', '', 25, 'Years to repay the loan'),
            ('Monthly rent', 1650, '', 'Your rent now or the rent of the home you would rent'), ('Rent growth, percent a year', 3, '', 'An example, check your own lease'),
            ('Home price growth, percent a year', '', 2, 'An example, not a forecast'), ('Upkeep and local charges a year', '', 4800, 'Repairs, local charges and similar'),
            ('Other running cost a month', 60, 140, 'Insurance and other fixed running costs'), ('Buying costs, percent of price', '', 3, 'Fees and charges at purchase'),
            ('Selling costs, percent of price', '', 5, 'Fees if you sell in the year tested'), ('Return on kept money, percent a year', 4, '', 'What the money you do not use as a down payment could earn')]
    return [nb(dict(item=key('rbitem', i), rent_option=r, buy_option=b, note=n)) for i, r, b, n in rows]


def rb_compare_d(): return [dict(year=y) for y in range(1, 16)]


# ------------------------------------------------------------------ tax papers
def tax_docs_d():
    contact = {'HF-07': 'Payroll office', 'HF-08': 'Freelance client', 'HF-09': 'Freelance client', 'HF-16': 'Bank branch', 'HF-12': 'Childcare provider'}
    rows = []
    for t in tax_doc_rows():
        r = dict(doc_id=t['doc_id'], tax_year=key('tyear', str(t['tax_year'])), doc_type=key('tdtype', t['doc_type']), description=t['description'], source_id=t['source_id'],
                 person=key('person', t['person']), expected_on=t['expected_on'], received_on=t['received_on'], filed=bool(t['filed']), due_date=t['due_date'])
        if t['source_id'] in contact: r['contact'] = key('contact', contact[t['source_id']])
        if t['doc_id'] == 'TD-28': r['expected_on'] = d_(-9); r['contact'] = key('contact', 'Tax preparer')
        if t['doc_id'] == 'TD-25': r['expected_on'] = d_(-12); r['received_on'] = ''
        rows.append(r)
    y = Y - 2
    extra = [('Income statement', 'Pay statement for the year, partner 1', 'HF-07', 'Partner 1', 9, 12), ('Income statement', 'Client A payments for the year', 'HF-08', 'Partner 2', 14, 18),
             ('Interest statement', 'Savings interest for the year', 'HF-16', 'Joint', 20, 23), ('Charity receipt', 'Charity gifts, receipts kept', '', 'Joint', -19, -15)]
    for i, (ty, desc, sid, pers, e, rc) in enumerate(extra):
        yy, mm = (y + 1, 1) if e > 0 else (y, 12)
        r = dict(doc_id='TD-%02d' % (29 + i), tax_year=key('tyear', str(Y - 2)), doc_type=key('tdtype', ty), description=desc, source_id=sid, person=key('person', pers),
                 expected_on='%d-%02d-%02d' % (yy, mm, abs(e)), received_on='%d-%02d-%02d' % (yy, mm, abs(rc)), filed=True, due_date='%d-04-15' % (Y - 1))
        if sid in contact: r['contact'] = key('contact', contact[sid])
        rows.append(r)
    return [nb(r) | dict(filed=r['filed']) for r in rows]


def missing_docs_d(): return [dict(rank=i) for i in range(1, 13)]
def missing_receipts_d(): return [dict(rank=i) for i in range(1, 21)]


DED = deduction_rows()
def deductions_d():
    return [dict(deduction_id=r['deduction_id'], date=r['date'], description=r['description'], category=key('dedcat', r['category']), amount=r['amount'], receipt=bool(r['receipt']),
                 tax_year=key('tyear', str(r['tax_year'])), person=key('person', r['person'])) for r in DED]


def ded_cat_d():
    out, i = [], 0
    for ty in TYEARS:
        for c in DEDUCTION_CATS:
            i += 1; out.append(dict(row_id='DC-%02d' % i, tax_year=key('tyear', ty), category=key('dedcat', c)))
    return out


# ------------------------------------------------------------------ set-aside and estimated payments
INC = income_rows()
FREEALL = sorted([r for r in INC if r['source'] != 'Paycheck' and r['source'] != 'Windfall'], key=lambda r: r['date'])
FREE = FREEALL[-75:]
def set_aside_d():
    return [dict(sa_id='SA-%03d' % (i + 1), date=r['date'], source=key('isource', r['source']), amount=r['net'], moved=r['set_aside']) for i, r in enumerate(FREE)]


def _moved_before(day):
    return sum(r['set_aside'] for r in FREE if r['date'] <= day)


def est_payments_d():
    out, paid_before = [], 0.0
    for k in range(12):
        off = 26 + 91 * (k - 7)
        day = d_(off)
        prev = d_(off - 91)
        quarter = sum(r['set_aside'] for r in FREE if prev < r['date'] <= day)
        if off <= 0:
            amt = round(quarter * 0.82 / 5) * 5.0
        else:
            amt = {26: 2300.0}.get(off, round((quarter or 3000.0) * 0.9 / 50) * 50.0)
        out.append(dict(pay_id='EP-%02d' % (k + 1), date=day, payment=amt or 1500.0, tax_year=key('pyear', str((T0 + _dt.timedelta(days=off)).year))))
    return out


# ------------------------------------------------------------------ monthly history and categories
TX = tx_rows(); CON = contribution_rows(); DPS = debt_payment_rows(); NW = networth_rows(); ACC = account_rows()
MONTHS25 = [month_start(k) for k in range(24, -1, -1)]


def year_months_d():
    inc = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for r in INC:
        inc[r['month']][0] += r['net']; inc[r['month']][3] += r['set_aside']
        if r['source'] == 'Paycheck': inc[r['month']][1] += r['net']
        inc[r['month']][2] += r['retirement']
    grp = defaultdict(float)
    for t in TX:
        if not t['from_goal'] and t['group'] in ('Fixed bills', 'Variable needs', 'Wants'): grp[(t['month'], t['group'])] += t['amount']
    sv = defaultdict(float)
    for c in CON:
        if c['kind'] == 'Deposit' and c['goal_id'] != 'SG-10': sv[c['month']] += c['amount']
    dp = defaultdict(lambda: [0.0, 0.0, 0.0])
    for p in DPS:
        dp[p['month']][0] += p['amount']; dp[p['month']][1] += p['extra'] or 0.0; dp[p['month']][2] += p['interest']
    nw = defaultdict(float)
    for n in NW: nw[n['month']] += n['balance'] if n['side'] == 'Asset' else -n['balance']
    out = []
    for m in MONTHS25:
        k = iso(m)
        out.append(dict(month=k, take_home=round(inc[k][0], 2), set_aside=round(inc[k][3], 2), paycheck=round(inc[k][1], 2), fixed=round(grp[(k, 'Fixed bills')], 2), variable=round(grp[(k, 'Variable needs')], 2),
                        wants=round(grp[(k, 'Wants')], 2), saved=round(sv[k], 2), retirement=round(inc[k][2], 2), debt_paid=round(dp[k][0], 2), debt_extra=round(dp[k][1], 2),
                        interest_paid=round(dp[k][2], 2), net_worth=round(nw[k], 2)))
    return out


GOALCAT = lambda g: 'Emergency fund' if g == 'SG-01' else ('Tax set-aside' if g == 'SG-10' else 'Goal savings')
CATG = {c['category']: c['group'] for c in category_rows}


def _cat_totals(m0, m1):
    """actual by category over the months m0 <= month < m1 (spending not from a goal + deposits into goals + retirement paid through payroll)"""
    a, b = iso(m0), iso(m1)
    tot = defaultdict(float)
    for t in TX:
        if a <= t['month'] < b and (not t['from_goal'] or t['category'] in ('Holidays and trips', 'Gifts')): tot[t['category']] += t['amount']
    for c in CON:
        if a <= c['month'] < b and c['kind'] == 'Deposit': tot[GOALCAT(c['goal_id'])] += c['amount']
    for r in INC:
        if a <= r['month'] < b: tot['Retirement'] += r['retirement']
    return tot


def category_changes_d():
    ty, ly = _cat_totals(month_start(12), month_start(0)), _cat_totals(month_start(24), month_start(12))
    return [dict(category=key('category', c['category']), group=key('group', c['group']), this_year=round(ty[c['category']], 2), last_year=round(ly[c['category']], 2)) for c in category_rows]


def goals_d():
    rows = [dict(item_id=g['goal_id'], item=g['goal'], kind=key('gdkind', g['kind']), target=g['target'], saved=g['saved']) for g in goal_rows()]
    for d in debt_rows():
        if d['original_amount']:
            rows.append(dict(item_id=d['debt_id'], item=d['debt'] + ' repaid', kind=key('gdkind', 'Instalment loan'), target=d['original_amount'], saved=round(d['original_amount'] - d['balance'], 2)))
    return rows


NEXT_CHANGE = {'Rent or mortgage': 0.0, 'Utilities': 0.04, 'Phone and internet': 0.0, 'Insurance': 0.05, 'Childcare and school': 0.03, 'Groceries': 0.03, 'Fuel and transport': 0.0, 'Health costs': 0.0,
               'Household supplies': 0.0, 'Car service': -0.1, 'Kids and family': 0.02, 'Work and tax costs': 0.0, 'Eating out': -0.15, 'Subscriptions': -0.35, 'Shopping': -0.1, 'Entertainment': 0.0,
               'Personal care': 0.0, 'Holidays and trips': 0.05, 'Gifts': 0.0, 'Emergency fund': 0.0, 'Goal savings': 0.05, 'Retirement': 0.0, 'Tax set-aside': 0.0, 'Card payments': -0.1,
               'Car loan': 0.0, 'Student loan': 0.0, 'Extra debt payment': 0.0, 'Other': -0.2}
def next_year_d(): return [dict(category=key('category', c['category']), change=NEXT_CHANGE.get(c['category'], 0.0)) for c in category_rows]


def year_review_d(): return [dict(item=key('yitem', i)) for i in YITEMS]
