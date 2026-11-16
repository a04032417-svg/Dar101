"""Doula business suite part 8: demo rows from du_core (row-level tables thinned never; calculated tables get only their key columns)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du8_lists import *
import datetime as _dt

ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def I(x): return iso(x) if hasattr(x, 'isoformat') else x
def front(rows, pred):
    """move the first row that matches to the top (the sheets and printable pages open on it)"""
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows

_fr = front
TEAMD = {t['name']: t for t in team}
OWNER_PHONE = TEAMD[OWNER]['phone']; ADMIN_PHONE = TEAMD[ADMIN]['phone']
ACCOUNTANT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
INSURER_PHONE = [t for t in team if t['role'] == 'Insurer'][0]['phone']
MS0 = month_start(0)
LM0 = month_start(1)
PNL = pnl_rows(); CASH = cash_rows(); TAX = tax_rows(); EXF = expense_rows(); RNF = renewal_rows(); TRF = training_rows()
INF = plan_rows(); CTF = contract_rows(); CLF = client_rows(); PKF = pack_rows()
CLD = {c['client_id']: c for c in CLF}; PKD = {p['client_id']: p for p in PKF}


def pnl_d():
    return _fr([dict(pnl_id=p['pnl_id'], month=I(p['month']), birth_income=p['birth_income'], postpartum_income=p['postpartum_income'], addon_income=p['addon_income'], class_income=p['class_income'],
                 other_income=p['other_income'], doula_pay=p['doula_pay'], backup_pay=p['backup_pay'], mileage=p['mileage'], admin_pay=p['admin_pay'], other_costs=p['other_costs'], births=p['births'],
                 visit_hours=p['visit_hours']) for p in PNL], lambda r: r['pnl_id'] == 'PL-23')


def cash_d():
    return _fr([dict(cash_id=c['cash_id'], month=I(c['month']), opening=c['opening'], cash_in=c['cash_in'], pay_out=c['pay_out'], expenses_out=c['expenses_out'], refunds=c['refunds'], set_aside=c['set_aside'],
                 owner_draw=c['owner_draw'], closing=c['closing']) for c in CASH], lambda r: r['cash_id'] == 'CF-23')


def tax_d():
    return [nb(dict(tax_id=t['tax_id'], month=I(t['month']), set_aside_pct=t['set_aside_pct'], moved_on=I(t['moved_on']), status=key('taxstatus', t['status']))) for t in TAX]


def expenses_d():
    return [dict(expense_id=e['expense_id'], date=I(e['date']), category=key('expcat', e['category']), description=e['description'], amount=e['amount'], paid_to=key('payee', e['paid_to'])) for e in EXF]


def budget_d(): return front([dict(category=key('expcat', b['category']), monthly_budget=b['monthly_budget']) for b in budget], lambda r: r['category'] == key('expcat', 'Marketing'))
def items_d(): return [dict(item=key('renewal', r['item']), cycle_days=r['cycle_days'], cost=r['cost']) for r in renewal_items]


def renewals_d():
    out = [nb(dict(renewal_id=r['renewal_id'], holder=r['holder'], item=key('renewal', r['item']), due_date=I(r['due_date']), renewed_on=I(r['renewed_on']), cost=r['cost'])) for r in RNF]
    return front(out, lambda r: r['renewal_id'] == ST['renewal_id'])


def training_d():
    return [dict(training_id=t['training_id'], holder=t['holder'], kind=key('cpd', t['kind']), title=t['title'], date=I(t['date']), hours=t['hours'], cost=t['cost']) for t in TRF]


def instalments_d():
    out = [nb(dict(inst_id=p['inst_id'], client_id=p['client_id'], client=p['client'], due_date=I(p['due_date']), amount=p['amount'], paid_on=I(p['paid_on']), status=key('istatus', p['status']))) for p in INF]
    return front(out, lambda r: r['client_id'] == ST['plan_client_id'] and r.get('status') == key('istatus', 'Unpaid'))


def contracts_d():
    out = []
    for c in CTF:
        pk = PKD.get(c['client_id'])
        out.append(nb(dict(contract_id=c['contract_id'], client_id=c['client_id'], client=c['client'], package=c['package'], kind=key('ckind', c['kind']), price=c['price'], deposit=c['deposit'],
                           signed_on=I(c['signed_on']), deposit_paid_on=I(c['deposit_paid_on']), balance_due=I(c['balance_due']), balance_paid_on=I(c['balance_paid_on']), plan=key('plan', c['plan']),
                           status=key('ctstatus', c['status']), pack_hours=pk['hours_bought'] if pk else '', pack_used=pk['hours_used'] if pk else '')))
    return front(out, lambda r: r['client_id'] == ST['prepaid_client_id'])


def clients_d():
    return [dict(client_id=c['client_id'], client=c['client'], kind=key('ckind', c['kind']), package=c['package'], edd=I(c['edd']), status=key('cstatus', c['status'])) for c in CLF]


def team_d(): return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email']) for t in team]


# ------------------------------------------------------------------ calculated tables (key columns only)
def nxt(k): return I(add_months(MS0, k))
def forecast_d(): return [dict(month=nxt(k)) for k in range(1, 13)]
def ownerplan_d(): return [dict(month=nxt(k)) for k in range(1, 13)]
def expvar_d(): return [dict(category=key('expcat', c), month=I(month_start(k))) for k in range(11, -1, -1) for c in EXPENSE_CATEGORIES]
def cpd_d(): return [dict(holder=h) for h in DOULA_NAMES + BACKUP_NAMES]
def renewcal_d():
    op = sorted([r for r in RNF if r['renewed_on'] == ''], key=lambda r: r['due_date'])[:25]
    return [dict(renewal_id=r['renewal_id']) for r in op]

CMP = [('Revenue', 'revenue', 1), ('Birth income', 'birth_income', 1), ('Postpartum income', 'postpartum_income', 1), ('Add-on income', 'addon_income', 1), ('Class income', 'class_income', 1),
       ('Doula pay', 'doula_pay', -1), ('Backup pay', 'backup_pay', -1), ('Mileage cost', 'mileage', -1), ('Admin pay', 'admin_pay', -1), ('Other costs', 'other_costs', -1), ('Total costs', 'costs', -1),
       ('Profit', 'profit', 1), ('Profit margin', 'margin', 1), ('Births', 'births', 1), ('Visit hours', 'visit_hours', 1), ('Doula pay share of revenue', 'doula_share', -1),
       ('Cost per birth', 'cost_birth', -1), ('Profit per birth', 'profit_birth', 1), ('Cost share of revenue', 'cost_share', -1), ('Revenue per birth', 'revenue_birth', 1),
       ('Cash in', 'cash.cash_in', 1), ('Pay out', 'cash.pay_out', -1), ('Owner draw', 'cash.owner_draw', 0), ('Tax set-aside', 'tax.set_aside', 0)]
def compare_d(): return [dict(measure=m, no=i + 1, direction=d) for i, (m, c, d) in enumerate(CMP)]
YR = [('Revenue', 'pnl.revenue', 1), ('Birth income', 'pnl.birth_income', 1), ('Postpartum income', 'pnl.postpartum_income', 1), ('Add-on income', 'pnl.addon_income', 1), ('Class income', 'pnl.class_income', 1),
      ('Doula pay', 'pnl.doula_pay', -1), ('Backup pay', 'pnl.backup_pay', -1), ('Mileage cost', 'pnl.mileage', -1), ('Admin pay', 'pnl.admin_pay', -1), ('Other costs', 'pnl.other_costs', -1),
      ('Total costs', 'pnl.costs', -1), ('Profit', 'pnl.profit', 1), ('Profit margin', 'margin', 1), ('Births', 'pnl.births', 1), ('Visit hours', 'pnl.visit_hours', 1), ('Revenue per birth', 'rpb', 1),
      ('Profit per birth', 'ppb', 1), ('Owner draw', 'cash.owner_draw', 0), ('Tax set-aside', 'tax.set_aside', 0), ('Expenses', 'expenses.amount', -1)]
def yearrev_d(): return [dict(measure=m, no=i + 1, direction=d) for i, (m, c, d) in enumerate(YR)]
YP = [('Minus 5 births a month', -5), ('Minus 4 births a month', -4), ('Minus 3 births a month', -3), ('Minus 2 births a month', -2), ('Minus 1 birth a month', -1), ('Current births a month', 0),
      ('Plus 1 birth a month', 1), ('Plus 2 births a month', 2), ('Plus 3 births a month', 3), ('Plus 4 births a month', 4), ('Plus 5 births a month', 5), ('Plus 6 births a month', 6)]
def yearplan_d(): return [dict(scenario=s, delta=d) for s, d in YP]

# ------------------------------------------------------------------ defaults for the tools (from the demo story)
def _var():
    bud = {b['category']: b['monthly_budget'] for b in budget}; act = {}
    for e in EXF:
        if e['month'] == LM0: act[e['category']] = act.get(e['category'], 0) + e['amount']
    return {c: act.get(c, 0) - bud[c] for c in bud}
VAR = _var()
DEF_CAT = max(VAR, key=VAR.get)
DEF_RENEWAL = ST['renewal_item']
