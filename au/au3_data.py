"""Part 3 demo rows: row-level tables show a thinned sample, aggregated tables are built from the full au_core output."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au3_lists import *
from collections import defaultdict

PERSON_PHONE = {t['name']: t['phone'] for t in team}
VA_PHONE = PERSON_PHONE[ASSISTANT]; ACCT_PHONE = PERSON_PHONE['Renata Bauer']; OWNER_PHONE = PERSON_PHONE[OWNER]
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}

CUR = month_start(0); CURI = iso(CUR)
FULL = sales_rows(); TIT = title_rows(); EDS = edition_rows(); STM = statement_rows(); PAY = payment_rows(); PRD = pageread_rows()
M12 = iso(month_start(12)); M24 = iso(month_start(24)); M3 = iso(month_start(2))
EDT = {e['edition_id']: e for e in EDS}


def sales_d(n=660):
    base = sales_rows(n); have = {r['sale_id'] for r in base}
    extra = [r for r in FULL if r['returns'] > 0 and r['sale_id'] not in have][::2]
    rows = sorted(base + extra, key=lambda r: r['sale_id'])
    return [nb(dict(sale_id=r['sale_id'], month=r['month'], edition_id=r['edition_id'], title_id=r['title_id'], title=r['title'], format=key('format', r['format']), store=key('store', r['store']),
                    country=key('country', r['country']), currency=key('currency', r['currency']), units=r['units'], returns=r['returns'], gross=r['gross'], royalty=r['royalty'], rate=round(r['rate'] * 100, 2)))
            for r in rows]


def pagereads_d(): return [dict(read_id=r['read_id'], month=r['month'], edition_id=r['edition_id'], title_id=r['title_id'], title=r['title'], pages_read=r['pages_read'], rate=round(r['rate'] * 1000, 2)) for r in PRD]
def statements_d(): return [nb(dict(statement_id=r['statement_id'], month=r['month'], store=key('store', r['store']), statement_amount=r['statement_amount'], paid_on=r['paid_on'], received=r['received'] if r['paid_on'] else '',
                                    status=key('ststatus', r['status']))) for r in STM]
def payments_d(): return [dict(payment_id=r['payment_id'], statement_id=r['statement_id'], store=key('store', r['store']), month=r['month'], received_on=r['received_on'], statement_amount=r['statement_amount'],
                               fee=r['fee'], fx_loss=r['fx_loss'], received=r['received']) for r in PAY]
def rates_d(): return [dict(currency=key('currency', c['currency']), rate=round(c['rate'] * 100, 2)) for c in currencies]
def stores_d(): return [dict(store=key('store', s['store']), royalty_share=s['royalty_share'], delay_days=s['delay_days']) for s in stores]
def countries_d(): return [dict(country=key('country', c['country']), currency=key('currency', c['currency']), sales_tax_pct=c['sales_tax_pct']) for c in countries]
def formats_d(): return [dict(format=key('format', f['format']), royalty_share=f['royalty_share'], base_cost=f['base_cost']) for f in formats]
def editions_d(): return [dict(edition_id=e['edition_id'], title_id=e['title_id'], title=e['title'], format=key('format', e['format']), list_price=e['list_price'], unit_cost=e['unit_cost'],
                               royalty_share=e['royalty_share'], status=key('estatus', e['status'])) for e in EDS]
def titles_d(): return [dict(title_id=t['title_id'], title=t['title'], pen_name=key('penname', t['pen_name']), series=key('series', t['series']), release_date=t['release_date'],
                             status=key('tstatus', t['status']), exclusive=bool(t['exclusive'])) for t in TIT]

_ms = defaultdict(lambda: [0, 0.0]); _mf = defaultdict(lambda: [0, 0.0]); _cm = defaultdict(float)
_ed = defaultdict(lambda: dict(u12=0, r12=0.0, u3=0, um=0, ms=set())); _cf = defaultdict(lambda: dict(u=0, r=0.0, p=0.0, um=0))
for r in FULL:
    a = _ms[(r['month'], r['store'])]; a[0] += r['units']; a[1] += r['royalty_home']
    b = _mf[(r['month'], r['format'])]; b[0] += r['units']; b[1] += r['royalty_home']
    _cm[(r['month'], r['currency'])] += r['royalty']
    e = _ed[r['edition_id']]
    if M12 <= r['month'] < CURI: e['u12'] += r['units']; e['r12'] += r['royalty_home']; e['ms'].add(r['month'])
    if r['month'] >= M3: e['u3'] += r['units']
    if r['month'] == CURI: e['um'] += r['units']
    c = _cf[(r['country'], r['format'])]
    if M12 <= r['month'] < CURI: c['u'] += r['units']; c['r'] += r['royalty_home']
    elif M24 <= r['month'] < M12: c['p'] += r['royalty_home']
    if r['month'] == CURI: c['um'] += r['units']
MONTHS = [iso(month_start(k)) for k in range(23, -1, -1)]


def mstore_d():
    out = []; i = 0
    for m in MONTHS:
        for s in STORES:
            if (m, s) in _ms:
                i += 1; u, v = _ms[(m, s)]; out.append(dict(row_id='MS-%03d' % i, month=m, store=key('store', s), units=u, royalty_home=R2(v)))
    return out


def mformat_d():
    out = []; i = 0
    for m in MONTHS:
        for f in FORMATS:
            if (m, f) in _mf:
                i += 1; u, v = _mf[(m, f)]; out.append(dict(row_id='MF-%03d' % i, month=m, format=key('format', f), units=u, royalty_home=R2(v)))
    return out


def edroy_d():
    out = []
    for e in EDS:
        d = _ed[e['edition_id']]
        out.append(dict(edition_id=e['edition_id'], units=d['u12'], royalty_home=R2(d['r12']), units_3m=d['u3'], units_month=d['um'], months_sold=len(d['ms'])))
    return out


def ctyfmt_d():
    out = []; i = 0
    for c in COUNTRIES:
        for f in FORMATS:
            i += 1; d = _cf[(c, f)]
            out.append(dict(row_id='CF-%02d' % i, country=key('country', c), format=key('format', f), units=d['u'], royalty_home=R2(d['r']), royalty_prev=R2(d['p']), units_month=d['um']))
    return out


def curmonth_d():
    out = []; i = 0
    for m in MONTHS[-17:]:
        mm = to_date(m)
        for c in CURRENCIES:
            i += 1; out.append(dict(row_id='CX-%03d' % i, month=m, currency=key('currency', c), amount_store=R2(_cm.get((m, c), 0.0)), rate_used=round(fx_rate(c, mm) * 100, 2)))
    return out


def earned_d():
    out = []
    for i, r in enumerate([x for x in STM if x['status'] in ('Paid', 'Short-paid')], 1): out.append(dict(row_id='EA-%03d' % i, month=r['month'], store=key('store', r['store'])))
    return out


def oldest_d(): return [dict(store=key('store', s)) for s in STORES]
def fees_d(): return [dict(payment_id=p['payment_id']) for p in PAY]
def prmonth_d(): return [dict(month=m) for m in MONTHS]
def depmonth_d(): return [dict(month=m) for m in MONTHS[-12:]]
