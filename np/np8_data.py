"""Nonprofit suite part 8: demo rows from np_core (budget, expenses, pay, cash, bank, forecast, scenarios, annual report)."""
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np8_lists import *

dd = to_date
T0 = TODAY
ST = story()
CUR = month_start(0)
TEAMID = {t['staff_id']: t for t in team}
ED_PHONE = TEAMID['NP-01']['phone']; DEV_PHONE = TEAMID['NP-02']['phone']; PM_PHONE = TEAMID['NP-03']['phone']; BK_PHONE = TEAMID['NP-08']['phone']
ACC_PHONE = TEAMID['NP-09']['phone']; BANK_PHONE = TEAMID['NP-10']['phone']; BROKER_PHONE = TEAMID['NP-11']['phone']; FUNDER_PHONE = TEAMID['NP-15']['phone']
STAFF_PHONE = TEAMID['NP-05']['phone']; STAFF_FIRST = first_name(TEAMID['NP-05']['name'])
_board = board_rows()
CHAIR, TREAS, VICE = _board[0], _board[1], _board[2]
FIN_PHONE = TREAS['phone']; BM_PHONE = VICE['phone']
_vol = [x for x in volunteer_rows() if x['status'] == 'Active'][3]
VOL_PHONE = _vol['phone']; VOL_FIRST = first_name(_vol['name'])
_don = [d for d in donor_rows() if d['type'] == 'Individual' and d['status'] == 'Active' and d['gifts'] >= 6][2]
DONOR_PHONE = _don['phone']; DONOR_FIRST = first_name(_don['donor'])
GRANT_ID = ST['grant']


def mkey(d): return d[:7] + '-01'
def yrk(d): return key('yr', {-2: 'Two years ago', -1: 'Last year', 0: 'This year'}[dd(d).year - T0.year])
def nz(x): return x if x else None


def clean(rows): return [{k: v_ for k, v_ in r.items() if v_ is not None and v_ != ''} for r in rows]


# ---------------------------------------------------------------- expenses: 3,000 rows (the earliest rows are merged by month, category, program, function and fund so the totals stay exact)
_EX = expense_rows()
def _merge(rows):
    g = collections.OrderedDict()
    for e in rows:
        k = (e['month'], e['category'], e['program'], e['function'], e['fund'], e['grant_id'], e['event_id'])
        if k in g: g[k] = dict(g[k], amount=round(g[k]['amount'] + e['amount'], 2))
        else: g[k] = dict(e)
    return list(g.values())
_cut = 0
while True:
    _cut += 25
    EXP = _merge(_EX[:_cut]) + _EX[_cut:]
    if len(EXP) <= 3000: break
for _e in EXP[:len(EXP) - (len(_EX) - _cut)]: _e['vendor'] = 'Various suppliers' if _e['vendor'] not in ('Payroll',) else 'Payroll'


def expenses_d():
    return clean([dict(expense_id=e['expense_id'], date=e['date'], month=e['month'], category=key('category', e['category']), vendor=e['vendor'], program=key('eprogram', e['program']),
                       function=key('function', e['function']), fund=key('fund', e['fund']), amount=e['amount'], grant_id=e['grant_id'], event_id=e['event_id']) for e in EXP])


def budget_d(): return [dict(budget_id=b['budget_id'], month=b['month'], area=key('area', b['area']), budget=b['budget']) for b in budget_rows()]
def ibudget_d(): return [dict(income_id=b['budget_id'], month=b['month'], line=key('iline', b['line']), budget=b['budget']) for b in income_budget_rows()]

CAT_SHARE_NOTE = {'staff time': 'Share of pay cost of each group', 'direct': 'Charged straight to one function', 'floor area': 'Floor area used by each group',
                  'headcount': 'Number of people in each group', 'use': 'Measured use by each function'}
def cats_d():
    return [dict(category=key('category', c['category']), program_share=c['program_share'], management_share=c['management_share'], fundraising_share=c['fundraising_share'],
                 rule=key('rule', c['rule'].capitalize()), basis=CAT_SHARE_NOTE[c['rule']]) for c in sorted(expense_categories, key=lambda c: c['category'] != 'Rent and utilities')]


def alloc_d(): return [dict(category=key('category', c)) for c in sorted(EXPENSE_CATEGORIES, key=lambda c: c != 'Rent and utilities')]


MONTHS = [m for m in (add_months(HISTORY_START, i) for i in range(0, 40)) if m <= CUR]
def functional_d(): return [dict(month=iso(m), period=yrk(iso(m))) for m in MONTHS]
def bact_d():
    rows = []; n = 0
    for m in MONTHS:
        if m.year == T0.year and m < CUR:
            for a in BUDGET_AREAS:
                n += 1; rows.append(dict(row_id='BA-%03d' % n, month=iso(m), area=key('area', a)))
    return rows


def pay_d():
    return [dict(pay_id=p['pay_id'], month=p['month'], staff=key('staff', p['staff']), role=key('payrole', p['role']), pay_type=p['pay_type'], hours=p['hours'], gross=p['gross'], employer_cost=p['employer_cost'],
                 paid=(p['status'] == 'Paid'), phone=next(s['phone'] for s in staff if s['name'] == p['staff'])) for p in pay_rows()]


# ---------------------------------------------------------------- income by source and month
GM = collections.Counter(); GR_ = collections.Counter(); EV = collections.Counter(); DU = collections.Counter(); IK = collections.Counter()
DON12 = collections.Counter()
for g in gift_rows():
    GM[g['month']] += g['amount']
    if (T0 - dd(g['date'])).days <= 365: DON12[g['donor_id']] += g['amount']
for g in grant_payment_rows():
    if g['received_on']: GR_[mkey(g['received_on'])] += g['amount']
for t in ticket_rows(): EV[mkey(t['sold_on'])] += t['qty'] * t['price_each']
for s in sponsor_rows():
    if s['received_on'] and dd(s['received_on']) <= T0: EV[mkey(s['received_on'])] += s['received']
_evd = {e['event_id']: e for e in event_rows()}
for a in auction_rows():
    if a['sold_price'] and a['sold_price'] != '' and a.get('received_on') and dd(a['received_on']) <= T0: EV[mkey(a['received_on'])] += a['sold_price']
for d in dues_rows(): DU[d['month']] += d['amount']
for i in inkind_rows(): IK[i['month']] += i['fair_value']
BIGDONOR = round(max(DON12.values()), 0)


def income_d():
    out = []
    for m in MONTHS:
        k = iso(m)
        out.append(dict(month=k, period=yrk(k), gifts=round(GM[k], 2), grants=nz(round(GR_[k], 2)), events=nz(round(EV[k], 2)), dues=round(DU[k], 2), inkind=round(IK[k], 2)))
    return clean(out)


def cash_d():
    return [dict(cash_id=c['cash_id'], month=c['month'], opening=c['opening'], receipts=c['receipts'], payments=c['payments'], restricted=c['restricted'], designated=c['designated']) for c in cash_rows()]


def bank_d():
    return clean([dict(bank_id=b['bank_id'], date=b['date'], month=b['month'], kind=key('bkind', b['kind']), description=b['description'], money_in=nz(b['money_in']), money_out=nz(b['money_out']),
                       balance=b['balance'], reconciled=bool(b['reconciled'])) for b in bank_rows()])


def forecast_d():
    return clean([dict(forecast_id=f['forecast_id'], month=f['month'], step=key('step', 'Month %d' % (i + 1)), gifts=f['gifts'], recurring=f['recurring'], pledges_due=f['pledges_due'], grants=f['grants'],
                       event_net=f['event_net'], dues=f['dues'], expenses=f['expenses'], one_off=f['one_off'], one_off_note=f['one_off_note'], event=f['event']) for i, f in enumerate(forecast_rows())])


FIN_VALUES = {'Gifts change': (0, 'Change on the plan for gifts, as a fraction, for example 0.05 is five percent more'), 'Recurring change': (0, 'Change on recurring gifts, as a fraction'),
              'Pledges collected share': (1, 'Share of the pledge instalments you expect to receive, 1 is all'), 'Grants received share': (1, 'Share of grant instalments you expect on time, 1 is all'),
              'Event net change': (0, 'Change on the planned event net, as a fraction'), 'Expenses change': (0, 'Change on planned expenses, as a fraction'),
              'Expense growth for reserve months': (0.04, 'Growth added to the last 12 months average expense; your estimate'),
              'Biggest donor giving a year': (BIGDONOR, 'Gifts of your largest donor in the last 12 months, from your gift log'), 'Dues change': (0, 'Change on membership dues, as a fraction'),
              'Opening cash change': (0, 'Add or take away cash at the start of the forecast, an amount')}
def finputs_d(): return [dict(item=key('finput', k), value=v_[0], note=v_[1]) for k, v_ in FIN_VALUES.items()]
def lowest_d(): return [dict(item=vkey(x)) for x in ('Lowest closing cash', 'Lowest free money', 'Lowest reserve months', 'Highest closing cash', 'Highest reserve months')]


SC = {'Base': {}, 'Lose the biggest donor': dict(lose_donor=True), 'Lose one grant': dict(lose_grant=True), 'Donors fall 5%': dict(gifts_pct=-0.05), 'Recurring grows 10%': dict(recurring_pct=0.10),
      'Costs up 8%': dict(cost_pct=0.08), 'Donors fall 10%': dict(gifts_pct=-0.10), 'Costs up 4%': dict(cost_pct=0.04), 'Costs up 12%': dict(cost_pct=0.12), 'Gifts up 5%': dict(gifts_pct=0.05),
      'Worst case together': dict(lose_donor=True, lose_grant=True, gifts_pct=-0.05, cost_pct=0.08), 'Best case together': dict(gifts_pct=0.05, recurring_pct=0.10, cost_pct=-0.02)}
def scen_d():
    return [dict(scenario=key('scen', k), gifts_pct=v_.get('gifts_pct', 0), recurring_pct=v_.get('recurring_pct', 0), cost_pct=v_.get('cost_pct', 0), lose_donor=v_.get('lose_donor', False),
                 lose_grant=v_.get('lose_grant', False)) for k, v_ in SC.items()]


AFFORD = [('Program assistant, part-time', 2400, 800, 1), ('Development officer, full-time', 4800, 2200, 1), ('Volunteer coordinator assistant', 1900, 600, 2), ('Grant writer, part-time', 2600, 900, 2),
          ('Bookkeeper hours added', 1200, 0, 1), ('Evening tutoring program', 3000, 1500, 3), ('Mobile pantry route', 3600, 4500, 4), ('Weekend meals for seniors', 2800, 1200, 2),
          ('Winter coats drive program', 1500, 900, 1), ('Camp bursary places', 2100, 0, 5), ('Data and donor software hours', 900, 600, 1), ('Facilities repairs plan', 3400, 6000, 6)]
def afford_d(): return [dict(item=a, monthly_cost=b, setup_cost=c_, start_no=d_, decide_on=ahead(5 + 4 * i)) for i, (a, b, c_, d_) in enumerate(AFFORD)]


# ---------------------------------------------------------------- annual report numbers (typed from other sheets of the suite)
def _yrset(rows, fld):
    out = collections.defaultdict(set)
    for r in rows: out[dd(r['date']).year].add(r[fld])
    return out
_gd = _yrset(gift_rows(), 'donor_id')
Y0 = T0.year
DON_THIS, DON_LAST = len(_gd[Y0]), len(_gd[Y0 - 1])
RET_LAST = len(_gd[Y0 - 1] & _gd[Y0 - 2]) / len(_gd[Y0 - 2]) if _gd[Y0 - 2] else 0.6
RET_THIS = len(_gd[Y0] & _gd[Y0 - 1]) / len(_gd[Y0 - 1]) if _gd[Y0 - 1] else 0.5
PEOPLE = collections.defaultdict(int)
for r in program_month_rows():
    if r['month'][5:7] == '12' or r['month'] == mkey(iso(T0)): PEOPLE[dd(r['month']).year] += r['participants']
_PSERV = collections.defaultdict(int)
for r in program_month_rows(): _PSERV[dd(r['month']).year] += r['new_participants']
HRS = collections.defaultdict(float)
for s in shift_rows():
    if s['status'] == 'Worked': HRS[dd(s['date']).year] += s['hours']
ITEMS = [(1, 'Money in'), (2, 'Gifts'), (3, 'Grants'), (4, 'Events'), (5, 'Membership dues'), (6, 'In-kind gifts, value'), (7, 'Money out'), (8, 'Program cost'), (9, 'Management cost'), (10, 'Fundraising cost'),
         (11, 'Net for the year'), (12, 'Program share of cost, percent'), (13, 'Cost to raise one dollar'), (14, 'Pay and staff cost'), (15, 'Months of reserve at the end'), (16, 'People served'),
         (17, 'Volunteer hours'), (18, 'Value of volunteer time'), (19, 'Donors who gave'), (20, 'Donor retention rate')]
def annual_d():
    typed = {16: (_PSERV[Y0], _PSERV[Y0 - 1]), 17: (None, round(HRS[Y0 - 1])), 19: (DON_THIS, DON_LAST), 20: (round(RET_THIS, 3), round(RET_LAST, 3))}
    out = []
    for n, item in ITEMS:
        r = dict(item=item, no=n, grant_id=GRANT_ID)
        if n in typed:
            a, b = typed[n]
            if a is not None: r['typed_this'] = a
            r['typed_last'] = b
        out.append(r)
    return out


def mbs_d(): return [dict(source=key('source', s), period=key('yr', p)) for p in ('This year', 'Last year', 'Two years ago') for s in SOURCES]
def mof_d(): return [dict(function=key('function', f), period=key('yr', p)) for p in ('This year', 'Last year', 'Two years ago') for f in FUNCTIONS]


def transfers_d():
    rows = [dict(transfer_id=t['transfer_id'], date=t['date'], from_fund=key('fund', t['from_fund']), to_fund=t['to_fund'], amount=t['amount'], note=t['note']) for t in transfer_rows()]
    rl = collections.defaultdict(float)
    for r in release_rows():
        if dd(r['month']) >= add_months(CUR, -2): rl[(r['month'], r['fund'])] += r['amount']
    n = 0
    for (m, f), a in sorted(rl.items()):
        n += 1
        rows.append(dict(transfer_id='RL-%s%02d' % (m[2:4], int(m[5:7])) + '-%d' % n, date=iso(min(add_months(dd(m), 1) - day(1), T0)), from_fund=key('fund', f), to_fund='General Fund', amount=round(a, 2),
                         note='Release from restriction for %s' % m[:7]))
    return rows


if __name__ == '__main__':
    print(len(EXP), len(expenses_d()), len(bank_d()), len(income_d()), len(transfers_d()), BIGDONOR, DON_THIS, DON_LAST, RET_THIS, RET_LAST, dict(_PSERV), dict(HRS))
