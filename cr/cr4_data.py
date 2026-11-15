"""Car rental suite part 4: demo rows from cr_core (ledgers in full, patched for the story; aggregated tables are formulas)."""
import sys, os, random; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr4_lists import *
import datetime as _dt
from collections import defaultdict

dd = to_date
ST = story()
T0 = TODAY
TD = iso(T0)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))
RN = random.Random(4404)

TEAM = {t['name']: t for t in team}
def PH(name): return TEAM[name]['phone']
OWNER_PHONE = PH(OWNER); MANAGER_PHONE = PH(MANAGER)
BOOKKEEPER = [t for t in team if t['role'] == 'Bookkeeper'][0]; BOOKKEEPER_PHONE = BOOKKEEPER['phone']
ACCOUNTANT = [t for t in team if t['role'] == 'Accountant'][0]; ACCOUNTANT_PHONE = ACCOUNTANT['phone']
LENDER_PHONE = [t for t in team if t['role'] == 'Lender'][0]['phone']
SUPPORT_A = fake_phone(61); SUPPORT_B = fake_phone(62); HOTEL_PHONE = fake_phone(63)
ACC_PHONE = {a: fake_phone(70 + i) for i, a in enumerate(ACCOUNTS)}

RENT = {r['renter_id']: r for r in renter_rows()}
VCLS = {v['vehicle_id']: v['class'] for v in vehicle_rows()}
BKF = booking_rows(); BKD = {b['booking_id']: b for b in BKF}
CLB = {}
for c_ in claim_rows(): CLB[c_['booking_id']] = c_
FEEC = defaultdict(float)
for f_ in fee_rows(): FEEC[f_['booking_id']] += f_['collected']

DEP = [dict(x) for x in deposit_rows()]
PO = [dict(x) for x in payout_rows()]
IV = [dict(x) for x in invoice_rows()]
M12 = iso(month_start(11))
PAY = [dict(x) for x in payment_rows() if x['date'] >= M12]
PAYBY = {}
for p in PAY:
    if p['payout_id']: PAYBY[p['payout_id']] = p

# ---- payouts that arrived a few days after the promised date (the marketplaces pay later than they say)
_i = 0
for po in PO:
    if po['status'] != 'Paid' or po['paid_on'] < M12: continue
    _i += 1
    delay = 0
    if po['channel'] == 'Marketplace B' and _i % 3 == 0: delay = 1 + _i % 5
    elif po['channel'] == 'Marketplace A' and _i % 8 == 0: delay = 1 + _i % 2
    if delay and d_add(po['paid_on'], delay) <= TD:
        po['paid_on'] = d_add(po['paid_on'], delay)
        p = PAYBY.get(po['payout_id'])
        if p: p['date'] = po['paid_on']; p['month'] = po['paid_on'][:8] + '01'

# ---- a share of small walk-in payments are cash, so the till has something to count
_k = 0
for p in PAY:
    if p['date'] >= ago(75) and p['method'] == 'Card' and p['kind'] != 'Payout' and p['channel'] in ('Website', 'Phone') and p['amount'] <= 320:
        _k += 1
        if _k % 2 == 0: p['method'] = 'Cash'

_w = 0
for p in PAY:
    if p['method'] == 'Card' and p['kind'] != 'Payout' and p['channel'] in ('Website', 'Phone', 'Hotel partner'):
        _w += 1
        if _w % 9 == 0: p['method'] = 'Mobile wallet'

# ---- invoices: a few older open balances, a few credits (payments follow)
def _pay_inv(i): return next((p for p in PAY if p['booking_id'] == i['booking_id'] and p['kind'] == 'Invoice payment'), None)
def _pick(lo, hi, skip):
    for i in IV:
        if i['status'] == 'Paid' and i['invoice_id'] not in skip and ago(hi) <= i['due_date'] <= ago(lo) and _pay_inv(i): return i
PATCHED = set()
for lo, hi, mode in ((12, 26, 0.4), (68, 82, 0.0), (100, 125, 0.35)):
    i = _pick(lo, hi, PATCHED)
    if not i: continue
    PATCHED.add(i['invoice_id']); p = _pay_inv(i)
    if mode == 0.0:
        PAY.remove(p); i['paid_amount'] = 0.0; i['paid_on'] = ''; i['status'] = 'Unpaid'
    else:
        i['paid_amount'] = round(i['amount'] * mode, 2); i['paid_on'] = ''; i['status'] = 'Part paid'; p['amount'] = i['paid_amount']
CREDIT = {}
_c = 0
for i in IV:
    if i['status'] == 'Paid' and i['invoice_id'] not in PATCHED and i['amount'] >= 250 and i['paid_on'] and i['due_date'] >= ago(330):
        _c += 1
        if _c % 6 == 0 and len(CREDIT) < 8:
            cr_ = round(i['amount'] * (0.04 + 0.01 * (_c % 5)), 2); p = _pay_inv(i)
            if p: CREDIT[i['invoice_id']] = cr_; i['paid_amount'] = round(i['amount'] - cr_, 2); p['amount'] = i['paid_amount']
for i in IV:
    if i['paid_on'] and i['paid_on'] > TD: i['paid_on'] = TD
IVD = {i['invoice_id']: i for i in IV}
def inv_open(i): return i['status'] in ('Unpaid', 'Part paid')

# ---- tables -------------------------------------------------------------------------
def deposits_d():
    out = []
    for x in DEP:
        r = RENT[x['renter_id']]; cl = CLB.get(x['booking_id'])
        use = cl and (x['status'] == 'Held' or x['reason'] == 'Damage claim')
        out.append(nb(dict(deposit_id=x['deposit_id'], booking_id=x['booking_id'], vehicle_id=x['vehicle_id'], renter=r['renter'], phone=r['phone'], cls=key('class', VCLS[x['vehicle_id']]), amount=x['amount'],
                           held_on=x['held_on'], release_due=x['release_due'], released_on=x['released_on'], status=key('depstatus', x['status']), kept_amount=x['kept_amount'],
                           refunded_amount=x['refunded_amount'], reason=(key('depreason', x['reason']) if x['reason'] else ''), claim_id=(cl['claim_id'] if use else ''),
                           claim_amount=(cl['estimate'] if use else ''))))
    for r in out: r['class'] = r.pop('cls')
    return out


def payments_d():
    rows = [nb(dict(payment_id=p['payment_id'], date=p['date'], month=p['month'], booking_id=p['booking_id'], channel=key('channel', p['channel']), kind=key('paykind', p['kind']),
                    method=key('method', p['method']), amount=p['amount'], payout_id=p['payout_id'])) for p in PAY]
    bk = {b['booking_id'] for b in BKF[-420:]}
    first = next(i for i, r in enumerate(rows) if r['booking_id'] in bk and r['channel'] in ('website', 'phone') and r['date'] >= ago(40))
    rows.insert(0, rows.pop(first))
    return rows


def payouts_d():
    return [nb(dict(payout_id=p['payout_id'], booking_id=p['booking_id'], channel=key('market', p['channel']), returned_on=BKD[p['booking_id']]['end_date'], month=p['month'],
                    booking_value=p['booking_value'], fee=p['fee'], expected_payout=p['expected_payout'], expected_on=p['expected_on'], received=p['received'], paid_on=p['paid_on'],
                    status=key('payoutstatus', p['status']))) for p in PO]


def invoices_d():
    return [nb(dict(invoice_id=i['invoice_id'], booking_id=i['booking_id'], account=key('account', i['account']), phone=ACC_PHONE[i['account']], issued_on=i['issued_on'], due_date=i['due_date'],
                    amount=i['amount'], credit_amount=CREDIT.get(i['invoice_id'], 0.0), paid_amount=i['paid_amount'], paid_on=i['paid_on'], status=key('istatus', i['status']))) for i in IV]


def bookings_d():
    out = []
    for b in BKF[-420:]:
        r = RENT[b['renter_id']]
        out.append(nb(dict(booking_id=b['booking_id'], created_on=b['created_on'], start_date=b['start_date'], end_date=b['end_date'], vehicle=b['vehicle'], cls=key('class', b['class']), renter=b['renter'],
                           phone=r['phone'], channel=key('channel', b['channel']), total=b['total'], deposit=b['deposit'], status=key('bstatus', b['status']))))
    for r in out: r['class'] = r.pop('cls')
    return out


def channels_d(): return [dict(channel=key('channel', c['channel']), fee_pct=c['fee_pct'], payout_days=c['payout_days']) for c in channels]
def methods_d(): return [dict(method=key('method', m)) for m in METHODS]
def corporate_d(): return [dict(account=key('account', a)) for a in ACCOUNTS]
def ageing_d(): return [dict(bucket=key('bucket', b)) for b in BUCKETS]
def forecast_d(): return [dict(weekno=n) for n in (1, 2, 3, 4)]


NHELD = sum(1 for x in DEP if x['status'] == 'Held')
def hold_due_d(): return [dict(rank=n) for n in range(1, NHELD + 1)]


def inv_lines_d():
    ids = [i for i in IV if inv_open(i) or i['status'] == 'Written off']
    ids += [i for i in IV if i not in ids][-(150 - len(ids)):]
    out = []; k = 0
    for i in sorted(ids, key=lambda i: i['invoice_id']):
        k += 1
        dmg = round(i['amount'] * (0.1 + 0.02 * (k % 6)), 2) if (k % 5 == 0 or i['invoice_id'] in PATCHED) and i['amount'] >= 150 else 0.0
        fee = round(i['amount'] * (0.04 + 0.015 * (k % 7)), 2)
        out.append(dict(invoice_id=i['invoice_id'], rental=round(i['amount'] - dmg - fee, 2), addons_fees=fee, damage=dmg))
    return out


DEPR = {x['deposit_id']: x['reason'] for x in DEP}
DEPD_BK = {x['deposit_id']: x['booking_id'] for x in DEP}
KEPT_IDS = [x for x in DEP if x['status'] in ('Kept', 'Part kept')][-60:]
def kept_d():
    out = []
    for n, x in enumerate(KEPT_IDS):
        f = round(FEEC.get(x['booking_id'], 0.0), 2)
        if x['reason'] == 'Fees' and n in (11, 29, 47): f = round(max(0.0, f - 30.0), 2)
        out.append(dict(deposit_id=x['deposit_id'], fees_collected=f))
    out.sort(key=lambda r: 0 if CLB.get(DEPD_BK[r['deposit_id']]) and DEPR[r['deposit_id']] == 'Damage claim' else 1)
    return out


def promises_d():
    out = []; op = [i for i in IV if inv_open(i)]
    pend_days = [1, 3, 5, 6, 2, 4, 6, 1]
    for n, i in enumerate(op):
        if n < 6: out.append(dict(invoice_id=i['invoice_id'], promised_on=d_add(TD, pend_days[n]), amount=round((i['amount'] - i['paid_amount']) * (0.6 if n % 2 else 1.0), 2), outcome=key('outcome', 'Pending'), last_contact=d_add(TD, -(2 + n))))
        else: out.append(dict(invoice_id=i['invoice_id'], promised_on=d_add(TD, -(5 + n * 3)), amount=round(i['amount'] - i['paid_amount'], 2), outcome=key('outcome', 'Missed'), last_contact=d_add(TD, -(3 + n))))
    late = [i for i in IV if i['status'] == 'Paid' and i['paid_on'] and (dd(i['paid_on']) - dd(i['due_date'])).days >= 3 and i['paid_on'] >= ago(300)]
    for n, i in enumerate(late[-24:]):
        miss = n % 6 == 3
        prom = d_add(i['paid_on'], -4 if miss else 1 + n % 3)
        out.append(dict(invoice_id=i['invoice_id'], promised_on=prom, amount=i['amount'], outcome=key('outcome', 'Missed' if miss else 'Kept'), last_contact=d_add(prom, -3)))
    out.sort(key=lambda r: r['promised_on'])
    return out


def months24(): return [iso(add_months(month_start(0), -k)) for k in range(23, -1, -1)]
def liability_d(): return [dict(month=m) for m in months24()]
def recon_d(): return [dict(month=m, channel=key('market', ch)) for m in months24() for ch in MARKETS]
_PNL = {r['month']: r for r in pnl_rows()}
_HOT = defaultdict(float)
for b in BKF:
    if b['channel'] == 'Hotel partner' and b['status'] not in ('Cancelled', 'No-show'): _HOT[b['start_date'][:8] + '01'] += b['channel_fee']
def feeshare_d(): return [dict(month=m, revenue=round(_PNL[m]['revenue'], 2), hotel_commission=round(_HOT.get(m, 0.0), 2)) for m in months24() if m in _PNL]
def cash_day_d(): return [dict(date=ago(k)) for k in range(59, -1, -1)]
def card_cal_d(): return [dict(date=ago(k)) for k in range(29, -1, -1)]


def _cash_by_day():
    by = defaultdict(float)
    for p in PAY:
        if p['method'] == 'Cash': by[p['date']] += p['amount']
    return by
CASHDAY = _cash_by_day()
def till_d():
    days = [d for d in sorted(CASHDAY) if d >= ago(50) and d <= TD][-30:]
    dev = {3: -15.0, 8: 20.0, 13: -42.5, 19: -5.0, 24: 12.0, 27: -60.0}
    out = []
    for n, d in enumerate(days):
        out.append(dict(till_id='TC-%03d' % (n + 1), date=d, counted=round(CASHDAY[d] + dev.get(n, 0.0), 2)))
    return out
