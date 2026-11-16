"""Doula business suite part 3: demo rows from du_core (full generator output, so the totals look real) with a few documented story touches."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du3_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def I(d): return iso(d) if hasattr(d, 'isoformat') else d
def d_add(d, n): return d + _dt.timedelta(days=n)

TEAM = {t['name']: t for t in team}
OWNER_PHONE = TEAM[OWNER]['phone']; ADMIN_PHONE = TEAM[ADMIN]['phone']
ACCOUNTANT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']

CLF = client_rows(); CLD = {c['client_id']: c for c in CLF}
CTF = [dict(c) for c in contract_rows()]; CTD = {c['client_id']: c for c in CTF}
INF = [dict(i) for i in plan_rows()]
PYF = [dict(p) for p in payment_rows()]
PKF = pack_rows(); CXF = cancel_rows(); PNF = pnl_rows()


def _drop_payment(client_id, kind, date=None, amount=None):
    for i, p in enumerate(PYF):
        if p['client_id'] == client_id and p['kind'] == kind and (date is None or p['date'] == date) and (amount is None or abs(p['amount'] - amount) < 0.01):
            del PYF[i]; return True
    return False


# ---- story touches (documented): two recent deposits are still unpaid (one just overdue), two old instalments were missed (66 and 81 days ago),
# and one plan now ends after the on-call window opens, so every ageing band, the deposit check and the plan check have a row.
_recent = [c for c in CTF if c['status'] == 'Signed' and c['kind'] != 'Postpartum' and c['deposit_paid_on'] != '' and c['signed_on'] >= T0 - _dt.timedelta(days=16)]
_new = max(_recent, key=lambda c: c['signed_on'])
_old = max([c for c in _recent if c['signed_on'] <= T0 - _dt.timedelta(days=8) and c['contract_id'] != _new['contract_id']], key=lambda c: c['signed_on'])
UNPAID_DEP = [_new['contract_id'], _old['contract_id']]
for c in (_new, _old):
    if _drop_payment(c['client_id'], 'Deposit'): c['deposit_paid_on'] = ''
MISSED = []
for iid in ('PI-0222', 'PI-0213'):
    i = next(x for x in INF if x['inst_id'] == iid)
    _drop_payment(i['client_id'], 'Instalment', i['paid_on'], i['amount'])
    i['paid_on'] = ''; i['status'] = 'Unpaid'; MISSED.append(iid)
_last = {}
for i in INF:
    if i['client_id'] not in _last or i['due_date'] > _last[i['client_id']]['due_date']: _last[i['client_id']] = i
_late = [i for cid, i in _last.items() if i['status'] == 'Unpaid' and i['due_date'] > T0 and CLD[cid]['oncall_start'] != '' and CLD[cid]['status'] in ('Booked', 'On call')]
_late.sort(key=lambda i: CLD[i['client_id']]['oncall_start'])
LATE_PLAN = _late[0]['client_id']
_late[0]['due_date'] = d_add(CLD[LATE_PLAN]['oncall_start'], 5)

# story touch: a few small payments came by gift voucher; a few finished contracts are marked renewed or on hold
for _p in [p for p in PYF if p['kind'] in ('Balance', 'Instalment')][5:11]: _p['method'] = 'Gift voucher'
_done = [c for c in CTF if c['status'] == 'Completed']
for _c, _st in zip(_done[:6], ['Renewed', 'Renewed', 'Renewed', 'On hold', 'On hold', 'On hold']): _c['status'] = _st
OPEN = ('Booked', 'On call', 'Postpartum care')
PAYSUM = {}
for p in PYF:
    if p['kind'] in ('Deposit', 'Balance', 'Instalment'): PAYSUM[p['client_id']] = PAYSUM.get(p['client_id'], 0) + p['amount']


def team_d(): return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email']) for t in team]


def packages_d():
    rows = [dict(package_id=p['package_id'], package=p['package'], kind=key('pkind', p['kind']), price=p['price'], birth_value=p['birth_value'], pp_value=p['pp_value'], deposit_pct=p['deposit_pct']) for p in packages]
    return sorted(rows, key=lambda r: r['kind'] == key('pkind', 'Add-on'))


def clients_d():
    return [nb(dict(client_id=c['client_id'], client=c['client'], kind=key('ckind', c['kind']), package=key('package', c['package']), edd=I(c['edd']), doula=key('doula', c['doula']), signed_on=I(c['signed_on']),
                    status=key('cstatus', c['status']), oncall_start=I(c['oncall_start']), oncall_end=I(c['oncall_end']), attended_on=I(c['attended_on']), phone=c['phone'])) for c in CLF]


def contracts_d():
    rows = [nb(dict(contract_id=c['contract_id'], client_id=c['client_id'], client=c['client'], package=key('package', c['package']), kind=key('ckind', c['kind']), list_price=c['list_price'], discount=key('discount', c['discount']),
                    price=c['price'], deposit=c['deposit'], signed_on=I(c['signed_on']), deposit_paid_on=I(c['deposit_paid_on']), balance_due=I(c['balance_due']), balance_paid_on=I(c['balance_paid_on']),
                    plan=key('plan', c['plan']), instalments=c['instalments'], status=key('ctstatus', c['status']))) for c in CTF]
    rows.sort(key=lambda r: r['client_id'] != ST['plan_client_id'])   # the first demo record: the client who paid two of four instalments
    return rows


def instalments_d():
    rows = [nb(dict(inst_id=i['inst_id'], client_id=i['client_id'], client=i['client'], no=i['no'], of=i['of'], due_date=I(i['due_date']), amount=i['amount'], paid_on=I(i['paid_on']), status=key('istatus', i['status']))) for i in INF]
    return rows


def payments_d():
    return [dict(payment_id=p['payment_id'], date=I(p['date']), month=I(p['month']), client_id=p['client_id'], client=p['client'], kind=key('paykind', p['kind']), amount=p['amount'], method=key('method', p['method'])) for p in PYF]


def packs_d():
    rows = [dict(pack_id=p['pack_id'], client_id=p['client_id'], client=p['client'], doula=key('doula', p['doula']), package=key('hpackage', p['package']), hours_bought=p['hours_bought'], price=p['price'],
                 bought_on=I(p['bought_on']), expires_on=I(p['expires_on']), hours_used=p['hours_used'], extra_hours=p['extra_hours']) for p in PKF]
    rows.sort(key=lambda r: r['client_id'] != ST['prepaid_client_id'])   # the first demo record: the 120-hour pack with most hours unused
    return rows


def cancels_d():
    rows = [dict(cancel_id=x['cancel_id'], date=I(x['date']), month=I(x['month']), client_id=x['client_id'], client=x['client'], kind=key('cxkind', x['kind']), reason=key('cxreason', x['reason']),
                 paid=x['paid'], kept=x['kept'], refunded=x['refunded']) for x in CXF]
    rows.sort(key=lambda r: r['kind'] != key('cxkind', 'Package changed'))
    return rows


def pnl_d():
    return [dict(month=I(r['month']), revenue=r['revenue'], birth_income=r['birth_income'], postpartum_income=r['postpartum_income'], addon_income=r['addon_income'], class_income=r['class_income'],
                 other_income=r['other_income'], costs=round(r['revenue'] - r['profit'], 2)) for r in PNF]


# ---- calculated tables: only the key column is a demo input
def deposits_d():
    ids = [c['contract_id'] for c in CTF if c['status'] != 'Cancelled'][-62:]
    return [dict(contract_id=i) for i in ids]


def _outstanding(c): return round(c['price'] - PAYSUM.get(c['client_id'], 0), 2) if c['status'] != 'Cancelled' else 0
def balances_d():
    open_ = [c for c in CTF if _outstanding(c) > 0.005]
    unpaid_inst = {}
    for i in INF:
        if i['status'] == 'Unpaid': unpaid_inst.setdefault(i['client_id'], []).append(i['due_date'])
    def nxt(c):
        if c['plan'] == 'Pay in full': return c['balance_due'] or T0 + _dt.timedelta(days=999)
        return min(unpaid_inst.get(c['client_id'], [T0 + _dt.timedelta(days=999)]))
    open_.sort(key=nxt)
    return [dict(contract_id=c['contract_id']) for c in open_]


def ageing_d(): return [dict(band=key('band', b)) for b in AGE]
def inst_window_d():
    ids = []
    for c in CTF:
        if c['plan'] == 'Instalments' and c['status'] != 'Cancelled' and CLD[c['client_id']]['oncall_start'] != '': ids.append(c['client_id'])
    ids = ids[-40:]
    ids.sort(key=lambda i: i != LATE_PLAN)   # first record: a plan that now ends after the window opens
    return [dict(client_id=i) for i in ids]


def unearned_client_d():
    ids = [c['client_id'] for c in CLF if c['status'] in OPEN]
    ids.sort(key=lambda i: i != ST['prepaid_client_id'])
    return [dict(client_id=i) for i in ids]


def months_d(): return [dict(month=iso(m)) for m in months24()]
def refund_reasons_d(): return [dict(reason=key('cxreason', r)) for r in CANCEL_REASONS]
def methods_d(): return [dict(method=key('method', m)) for m in PAYM]
def ct_status_d(): return [dict(status=key('ctstatus', s)) for s in CTS]


def late_payer():
    """the client with the most late instalments among those with 3 or more (default of the late-payer tool)"""
    import collections
    late = collections.defaultdict(list)
    for i in INF:
        if i['paid_on'] != '': late[i['client']].append((i['paid_on'] - i['due_date']).days)
    best = max(((sum(1 for d in v if d > 5), max(v), k) for k, v in late.items() if len(v) >= 3))
    return best[2]


if __name__ == '__main__':
    print('unpaid deposits', UNPAID_DEP, 'missed', MISSED, 'late plan', LATE_PLAN, late_payer())
    print({k: len(v()) for k, v in dict(clients=clients_d, contracts=contracts_d, instalments=instalments_d, payments=payments_d, packs=packs_d, cancels=cancels_d, pnl=pnl_d, deposits=deposits_d,
                                         balances=balances_d, inst_window=inst_window_d, unearned=unearned_client_d).items()})
