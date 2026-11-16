"""Nonprofit suite part 1: demo rows from np_core (row tables thinned to this year, aggregated tables built from the full output)."""
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np1_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
Y0 = iso(D(T0.year, 1, 1))
BANK_TOL = 25.0
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
TEAM = {t['staff_id']: t for t in team}
DEV_PHONE = TEAM['NP-02']['phone']; BOOK_PHONE = TEAM['NP-08']['phone']; ACC_PHONE = TEAM['NP-09']['phone']
BOARD_PHONE = board_rows()[0]['phone']
VOL_PHONE = [v for v in volunteer_rows() if v['status'] == 'Active'][0]['phone']

DONF = donor_rows(); DON = {d['donor_id']: d for d in DONF}
GFF = [dict(g) for g in gift_rows()]
BTF = batch_rows(); BTD = {b['batch_id']: b for b in BTF}
GAP = {b['batch_id']: (round(b['banked_amount'] - b['logged_amount'], 2) if b['status'] == 'Banked' else None) for b in BTF}


# ---- gifts: this calendar year (the aggregated tables below carry the older history)
def _retag():
    pool = [g for g in GFF if g['date'] >= Y0 and g['gift_type'] == 'One-time' and g['amount'] >= 100 and g['fund'] == 'General Fund' and g['donor_id']]
    pool.sort(key=lambda g: g['date'])
    step = max(1, len(pool) // 12)
    for n, name in enumerate(['Facilities Reserve', 'Kitchen Equipment Fund', 'Learning Lab Grant Fund'] * 3):
        g = pool[(n + 1) * step - 1]
        g['fund'] = name; g['restricted'] = True
_retag()
GF = [g for g in GFF if g['date'] >= Y0]
WD = {i: WEEKDAYS[i] for i in range(7)}


def gifts_d():
    out = []
    for g in GF:
        out.append(nb(dict(gift_id=g['gift_id'], date=g['date'], donor_id=g['donor_id'], amount=g['amount'], fund=key('fund', g['fund']) if g['fund'] else '', campaign=key('campaign', g['campaign']),
                           appeal=key('appeal', g['appeal']) if g['appeal'] else '', channel=key('channel', g['channel']), method=key('method', g['method']), gift_type=key('gtype', g['gift_type']),
                           restricted=bool(g['restricted']), ack_sent=g['ack_sent'], batch_id=g['batch_id'], pledge_id=g['pledge_id'], recurring_id=g['recurring_id'], match_for=g['match_for'],
                           weekday=key('wday', WD[dd(g['date']).weekday()]))))
    return out


# expected gift flags (the same rules as the sheet formulas)
def _dup_ids():
    k = collections.defaultdict(list)
    for g in GF:
        if g['gift_type'] == 'One-time' and g['donor_id']: k[(g['donor_id'], g['amount'])].append(g)
    ids = set()
    for v in k.values():
        for a in v:
            for b in v:
                if a is not b and abs((dd(a['date']) - dd(b['date'])).days) <= 3: ids.add(a['gift_id'])
    return ids
DUP_GIFTS = _dup_ids()
def issue_of(g):
    if not g['donor_id']: return 1
    if not g['fund']: return 2
    if g['gift_id'] in DUP_GIFTS: return 3
    gp = GAP.get(g['batch_id'])
    if gp is not None and abs(gp) > BANK_TOL: return 4
    return 0
FLAGGED = [g for g in GF if issue_of(g)]
OPEN = [g for g in GF if not g['ack_sent']]


def batches_d():
    return [nb(dict(batch_id=b['batch_id'], week_start=b['week_start'], banked_on=b['banked_on'], logged_amount=b['logged_amount'], gift_count=b['gift_count'], banked_amount=b['banked_amount'] if b['status'] == 'Banked' else '',
                    status=key('batch', b['status']))) for b in BTF]


def donors_d():
    return [nb(dict(donor_id=d['donor_id'], donor=d['donor'], type=key('dtype', d['type']), contact=d['contact'], phone=d['phone'], email=d['email'], contact_pref=key('pref', d['contact_pref']),
                    status=key('dstatus', d['status']), first_gift=d['first_gift'], last_gift=d['last_gift'], gifts=d['gifts'], total_given=d['total_given'])) for d in DONF]


def contacts_d():
    return [dict(contact_id=x['contact_id'], donor_id=x['donor_id'], donor=x['donor'], contact=x['contact'], role=x['role'], phone=x['phone'], email=x['email']) for x in contact_rows()]


def funds_d(): return [dict(fund=key('fund', f['fund']), restriction=key('fundkind', f['restriction']), opening_balance=f['opening_balance']) for f in funds]


def campaigns_d():
    return [dict(campaign_id=x['campaign_id'], campaign=key('campaign', x['campaign']), year=x['year'], start_date=x['start_date'], end_date=x['end_date'], goal=x['goal']) for x in campaign_rows()]


def appeals_d():
    ch = collections.defaultdict(collections.Counter)
    for g in GFF:
        if g['appeal']: ch[g['appeal']][g['channel']] += 1
    return [dict(appeal=key('appeal', a['appeal']), campaign=key('campaign', a['campaign']), channel=key('channel', (ch[a['appeal']].most_common(1) or [(CHANNELS[0], 0)])[0][0])) for a in appeals]


# ---- giving by donor and year: the last two years come from the full log, this year is worked out by the sheet from Gifts
def giving_years_d(n=400):
    by = collections.defaultdict(lambda: collections.defaultdict(float))
    for g in GFF:
        if g['donor_id']: by[g['donor_id']][dd(g['date']).year] += g['amount']
    y = T0.year
    now = sorted([(d, v[y]) for d, v in by.items() if v[y] > 0], key=lambda t: -t[1])
    lapsing = sorted([(d, v[y - 1]) for d, v in by.items() if v[y] == 0 and v[y - 1] > 0], key=lambda t: -t[1])
    ids = [d for d, _ in now[:n - 60]] + [d for d, _ in lapsing[:60]]
    for d in [g['donor_id'] for g in GF if g['fund'] == '' and g['donor_id']] + [ST['donor']]:
        if d not in ids: ids.append(d)
    return [dict(donor_id=d, last_year=round(by[d][y - 1], 2), two_years_ago=round(by[d][y - 2], 2)) for d in ids]


def pledges_d():
    rows = _pledges_d()
    first = [r for r in rows if r['status'] == 'open' and r['pledge_id'] != ST['pledge']][0]
    rows.remove(first); rows.insert(0, first)
    return rows
def _pledges_d():
    return [dict(pledge_id=p['pledge_id'], donor_id=p['donor_id'], pledged_on=p['pledged_on'], total=p['total'], instalments=p['instalments'], every_months=p['every_months'],
                 fund=key('fund', p['fund']), status=key('plstatus', p['status'])) for p in pledge_rows()]


def instalments_d():
    return [nb(dict(pp_id=x['pp_id'], pledge_id=x['pledge_id'], due_date=x['due_date'], amount_due=float(x['amount_due']), paid_on=x['paid_on'], amount_paid=float(x['amount_paid']), status=key('instatus', x['status'])))
            for x in pledge_payment_rows()]


_RCH = ['Online form', 'Payroll giving', 'Mail']
def recurring_d():
    _rc = recurring_rows()
    for _i, _r in enumerate(_rc):
        if _i % 3 == 1: _r['channel'] = _RCH[(_i // 3) % 3]
    return [nb(dict(recurring_id=r['recurring_id'], donor_id=r['donor_id'], amount=r['amount'], start_date=r['start_date'], day=r['day'], channel=key('channel', r['channel']), fund=key('fund', r['fund']),
                    status=key('recstatus', r['status']), last_received=r['last_received'], missed=r['missed'])) for r in _rc]


def recurring_months_d():
    out = []
    for m in months14():
        mi = iso(m); rows = [g for g in GFF if g['month'] == mi]
        rec = [g for g in rows if g['gift_type'] == 'Recurring']
        out.append(dict(month=mi, recurring_gifts=len(rec), recurring_amount=round(sum(g['amount'] for g in rec), 2), all_amount=round(sum(g['amount'] for g in rows), 2)))
    return out


def gift_months_d():
    out = []; m = dd(GIFT_START)
    last = D(T0.year, T0.month, 1)
    by = collections.defaultdict(list)
    for g in GFF: by[g['month']].append(g)
    while m <= last:
        mi = iso(m); rows = by.get(mi, [])
        if rows:
            waits = [(dd(g['ack_sent']) - dd(g['date'])).days for g in rows if g['gift_type'] in ('One-time', 'Event gift') and g['ack_sent']]
            out.append(dict(month=mi, gifts=len(rows), amount=round(sum(g['amount'] for g in rows), 2), donors=len({g['donor_id'] for g in rows if g['donor_id']}),
                            recurring_amount=round(sum(g['amount'] for g in rows if g['gift_type'] == 'Recurring'), 2), restricted_amount=round(sum(g['amount'] for g in rows if g['restricted']), 2),
                            avg_wait=round(sum(waits) / len(waits), 1) if waits else 1.0))
        m = add_months(m, 1)
    return out


# ---- in-kind and matching
_IK = [dict(x) for x in inkind_rows()]
for _i in [x for x in _IK if x['date'] >= Y0][3::9][:6]: _i['value_basis'] = 'Not recorded'
def inkind_d():
    return [nb(dict(inkind_id=x['inkind_id'], date=x['date'], donor_id=x['donor_id'], kind=key('ikind', x['kind']), item=x['item'], qty=x['qty'], fair_value=x['fair_value'], value_basis=key('basis', x['value_basis']),
                    ack_sent=x['ack_sent'])) for x in _IK]


_MG = [dict(x) for x in matching_rows()]
# a few recent matches are still waiting on the employer (so the chase list has a real length)
_recv = [x for x in _MG if x['status'] == 'Received' and x['received_on'] and x['requested_on'] >= ago(200)]
for _m, _d in zip(_recv[-4:], (62, 78, 96, 120)):
    _m['status'] = 'Requested'; _m['received_on'] = ''; _m['received'] = 0.0; _m['requested_on'] = ago(_d)
for _m in _MG:
    if _m['requested_on'] and _m['requested_on'] > iso(T0): _m['requested_on'] = ago(1)
def matching_d():
    return [nb(dict(match_id=x['match_id'], gift_id=x['gift_id'], donor_id=x['donor_id'], employer=x['employer'], employer_donor_id=x['employer_donor_id'], ratio=x['ratio'], expected=x['expected'],
                    requested_on=x['requested_on'], received_on=x['received_on'], received=x['received'], status=key('mstatus', x['status']))) for x in _MG]
MATCH_OPEN = [x for x in _MG if x['status'] in ('Requested', 'Expected')]


# ---- ranked and picked lists
def thankyou_d(): return [dict(rank=i) for i in range(1, min(40, len(OPEN)) + 1)]
def gift_checks_d(): return [dict(rank=i) for i in range(1, min(60, len(FLAGGED)) + 1)]
def match_chase_d(): return [dict(rank=i) for i in range(1, min(30, len(MATCH_OPEN)) + 1)]


def _email_groups():
    g = collections.defaultdict(list)
    for d in DONF: g[(d['email'], d['type'])].append(d['donor_id'])
    return [v for v in g.values() if len(v) > 1]
EMAIL_DUPS = _email_groups()


def duplicates_d():
    ids = [i for grp in EMAIL_DUPS for i in grp]
    gdon = []
    for g in GF:
        if g['gift_id'] in DUP_GIFTS and g['donor_id'] not in gdon: gdon.append(g['donor_id'])
    ids += [i for i in gdon if i not in ids]
    names = collections.defaultdict(list)
    for d in DONF: names[d['donor']].append(d)
    same = [d['donor_id'] for v in names.values() if len(v) > 1 and len({x['email'] for x in v}) == len(v) for d in v]
    ids += [i for i in same[:10] if i not in ids]
    return [dict(donor_id=i, found_on=ago(4 + (n * 9) % 320)) for n, i in enumerate(ids)]


def households_d():
    gy = {r['donor_id'] for r in giving_years_d()}
    nc = collections.Counter(x['donor_id'] for x in contact_rows())
    hh = [d['donor_id'] for d in DONF if d['type'] == 'Household' and nc[d['donor_id']] >= 2 and d['donor_id'] in gy]
    rest = [d['donor_id'] for d in DONF if d['donor_id'] in gy and d['donor_id'] not in hh and nc[d['donor_id']] >= 2]
    return [dict(donor_id=i) for i in (hh + rest)[:60]]
