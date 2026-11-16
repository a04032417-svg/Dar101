"""Household Finance suite part 2: demo rows from hf_core (full output where small, aggregated tables built from the full generator output)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf2_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def rk(n): return [dict(rank=i) for i in range(1, n + 1)]

TEAM = {t['member_id']: t for t in team}
ACC = account_rows(); ACCN = {a['account_id']: a['account'] for a in ACC}
BL = bill_rows(); BLD = {b['bill_id']: b for b in BL}
BI = bill_due_rows(); SB = subscription_rows(); CN = contract_rows()
SUBTX = [t for t in tx_rows() if t['category'] == 'Subscriptions']
PAYACCT = {'AC-01': 'Joint checking', 'AC-06': 'Car and home savings'}
CARDOF = {'AC-07': 'Card A', 'AC-08': 'Card B'}


def band(d):
    n = dd(d).day
    return DAYBANDS[0] if n <= 7 else DAYBANDS[1] if n <= 14 else DAYBANDS[2] if n <= 21 else DAYBANDS[3]


def first(rows, pred):
    """put the first row that satisfies pred at the front (the demo form and document show the first row)"""
    for i, r in enumerate(rows):
        if pred(r): return [r] + rows[:i] + rows[i + 1:]
    return rows


def team_d(): return [nb(dict(t, role=key('role', t['role']), group=key('tgroup', t['group']))) for t in team]


def accounts_d():
    return [dict(account_id=a['account_id'], account=a['account'], type=key('atype', a['type']), owner=key('person', a['owner']), opening_balance=a['opening_balance'], balance_now=a['balance_now']) for a in ACC]


def bills_d():
    out = []
    for i, b in enumerate(BL):
        rows = [r for r in BI if r['bill_id'] == b['bill_id']]
        past = [r for r in rows if r['due_date'] <= iso(T0)]
        latest = past[-1]; tgt = dd(latest['due_date']) - _dt.timedelta(days=365)
        ago_row = min(past, key=lambda r: abs((dd(r['due_date']) - tgt).days))
        ratio = ago_row['amount'] / latest['amount']
        since = dd(rows[0]['due_date']) - _dt.timedelta(days=120 + 83 * i)
        out.append(dict(bill_id=b['bill_id'], bill=b['bill'], category=key('bcat', b['category']), amount=b['amount'], due_day=b['due_day'], cycle=key('cycle', b['cycle']), autopay=b['autopay'],
                        account_id=b['account_id'], contact_id=b['contact_id'], payee=b['payee'], due_month=b['due_month'], last_amount=round(b['amount'] * ratio, 2), since=iso(since)))
    return first(out, lambda r: r['bill'] == 'Water and trash')


def bill_due_d():
    out = []
    for r in BI:
        b = BLD[r['bill_id']]
        out.append(nb(dict(due_id=r['due_id'], bill_id=r['bill_id'], bill=r['bill'], due_date=r['due_date'], month=r['month'], amount=r['amount'], status=key('bstatus', r['status']), paid_on=r['paid_on'],
                           account_id=r['account_id'], autopay=r['autopay'], category=key('bcat', b['category']), account=key('payacct', PAYACCT[r['account_id']]), cycle=key('cycle', b['cycle']),
                           dayband=key('dayband', band(r['due_date'])))))
    lo = iso(T0 - _dt.timedelta(days=330))
    def pick(x):
        return x.get('status') == key('bstatus', 'Paid') and not x['autopay'] and x['due_date'] >= lo and x.get('paid_on') and (dd(x['paid_on']) - dd(x['due_date'])).days >= 3
    cands = [x for x in out if pick(x)]
    if cands: out = [cands[-1]] + [x for x in out if x is not cands[-1]]
    return out


def bills_month_d(): return [dict(month=iso(m)) for m in months25()]


def bills_cat_d(): return [dict(category=key('bcat', c)) for c in BILL_CATS]


def autopay_d():
    names = [b['bill'] for b in BL]
    names = ['Water and trash'] + [n for n in names if n != 'Water and trash']
    return [dict(bill=n) for n in names]


def _use_band(days):
    return USE_BANDS[0] if days <= 7 else USE_BANDS[1] if days <= 29 else USE_BANDS[2] if days <= 59 else USE_BANDS[3]


def subs_d():
    out = []
    for i, s in enumerate(SB):
        days = (T0 - dd(s['last_used'])).days
        out.append(dict(sub_id=s['sub_id'], name=s['name'], price=s['price'], cycle=key('cycle', s['cycle']), monthly_cost=s['monthly_cost'], yearly_cost=s['yearly_cost'], card=key('card', CARDOF[s['account_id']]),
                        renewal_date=s['renewal_date'], last_used=s['last_used'], price_6m_ago=s['price_6m_ago'], decision=key('decision', 'Cancel' if s['sub_id'] == 'SB-07' else s['decision']), owner=key('person', s['owner']), start_date=s['start_date'],
                        use_band=key('useband', _use_band(days)), provider_phone=fake_phone(520 + i)))
    return first(out, lambda r: r['sub_id'] == 'SB-07')


def sub_charges_d():
    return [dict(tx_id=t['tx_id'], date=t['date'], payee=t['payee'], amount=t['amount'], account_id=t['account_id'], month=t['month']) for t in SUBTX]


def contracts_d():
    out = []
    for i, c in enumerate(CN):
        out.append(dict(contract_id=c['contract_id'], contract=c['contract'], kind=key('ckind', c['kind']), contact_id=c['contact_id'], amount=c['amount'], cycle=key('cycle', c['cycle']), yearly_cost=c['yearly_cost'],
                        renewal_date=c['renewal_date'], notice_days=c['notice_days'], review_on=c['review_on'], reviewed=c['contract'] in ('Electricity supply', 'Gas supply', 'Phone plan', 'Childcare agreement', 'Car loan agreement', 'Student loan agreement')))
    ren = iso(T0 + _dt.timedelta(days=190))
    out.append(dict(contract_id='CN-12', contract='Water and trash service', kind=key('ckind', 'Utility'), contact_id='HF-15', amount=58.0, cycle=key('cycle', 'Monthly'), yearly_cost=696.0, renewal_date=ren,
                    notice_days=30, review_on=iso(dd(ren) - _dt.timedelta(days=REVIEW_DAYS)), reviewed=False))
    return first(out, lambda r: r['contract'] == 'Car insurance')


def ins_cal_d(): return [dict(month=iso(month_start(-j))) for j in range(12)]
def sub_creep_d(): return [dict(month=iso(month_start(k))) for k in range(13, 0, -1)]


if __name__ == '__main__':
    for n in ('team_d', 'accounts_d', 'bills_d', 'bill_due_d', 'bills_month_d', 'bills_cat_d', 'autopay_d', 'subs_d', 'sub_charges_d', 'contracts_d', 'ins_cal_d', 'sub_creep_d'): print(n, len(globals()[n]()))
    print(bill_due_d()[0]); print(bills_d()[0]); print(subs_d()[0]); print(ST)
