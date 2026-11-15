"""Author and Self-Publisher suite part 4: demo rows from au_core (full generator output where the table is small; ad days thinned to the last 90 days plus one row per campaign and month before)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au4_lists import *
import datetime as _dt
from collections import defaultdict, OrderedDict

dd = to_date
R = rng('au4')
ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))

TEAM = {t['name']: t for t in team}
SPEC = TEAM['Lucia Ferreira']; VA = TEAM['Dario Lindqvist']; DEV = TEAM['Mikael Dahl']; ACC = TEAM['Renata Bauer']; OWN = TEAM[OWNER]
PARTNER = swap_rows()[1]            # a newsletter partner with a phone
TIT = title_rows(); TID = {t['title_id']: t for t in TIT}; TNAME = {t['title']: t for t in TIT}
EDS = edition_rows(); ED = {e['edition_id']: e for e in EDS}
CAMP = campaign_rows()
for _c in CAMP: _c['campaign'] = SHORT_NAMES.get(_c['campaign'], _c['campaign'])
CAMPD = {c['campaign_id']: c for c in CAMP}
ADF = ad_day_rows(); PRF = promo_rows(); SALES = sales_rows(); PRD = pageread_rows()

# demo story touch (documented): the pre-order ads of Crown of Last Embers reach many readers who do not buy yet: more clicks, the same sales and royalties
for r in ADF:
    if r['campaign_id'] == 'AC-030':
        r['clicks'] = int(round(r['clicks'] * 2.6)); r['impressions'] = int(round(r['impressions'] * 2.6))

CUT = iso(T0 - _dt.timedelta(days=95))


def titles_d():
    return [dict(title_id=t['title_id'], title=t['title'], pen_name=key('penname', t['pen_name']), series=key('series', t['series']), release_date=t['release_date'],
                 status=key('tstatus', t['status']), exclusive=bool(t['exclusive'])) for t in TIT]


def editions_d():
    return [dict(edition_id=e['edition_id'], title=e['title'], format=key('format', e['format']), list_price=e['list_price'], unit_cost=e['unit_cost'], royalty_share=e['royalty_share'],
                 status=key('estatus', e['status'])) for e in EDS]


def stores_d(): return [dict(store=key('store', s['store']), royalty_share=s['royalty_share'], delay_days=s['delay_days']) for s in stores]


EXTRA_PLAT = [('Newsletter feature', 0.0, 0.0), ('Reader group post', 0.0, 0.0)]
def platforms_d():
    return [dict(platform=p['platform'], typical_cpc=p['typical_cpc'], daily_min=p['daily_min']) for p in ad_platforms] + [dict(platform=n, typical_cpc=c, daily_min=m) for n, c, m in EXTRA_PLAT]


CAMP_ORD = sorted(CAMP, key=lambda c: (c['campaign_id'] != ST['ad_campaign']['campaign_id'], c['campaign_id']))


def campaigns_d():
    out = []
    for c in CAMP_ORD:
        if c['status'] == 'Running': rv = ago(2 + (int(c['campaign_id'][-2:]) * 3) % 9)
        else: rv = c['end_date']
        out.append(nb(dict(campaign_id=c['campaign_id'], campaign=c['campaign'], title=c['title'], platform=key('platform', c['platform']), start_date=c['start_date'], end_date=c['end_date'],
                           status=key('adstatus', c['status']), daily_budget=c['daily_budget'], bid=c['bid'], reviewed_on=rv)))
    return out


def adsdays_d():
    """daily rows for running and paused campaigns and for the last 95 days; ended campaigns before that are kept as one row per campaign and week-part of a month"""
    summ = OrderedDict(); daily = []
    for r in ADF:
        if r['date'] > CUT or CAMPD[r['campaign_id']]['status'] != 'Ended': daily.append(r); continue
        k = (r['campaign_id'], r['month'], (int(r['date'][8:10]) - 1) // 7)
        a = summ.setdefault(k, dict(date=r['date'], days=0, spend=0.0, impressions=0, clicks=0, sales=0, page_reads=0, royalties=0.0, campaign_id=r['campaign_id']))
        a['days'] += 1
        for f in ('spend', 'royalties'): a[f] += r[f]
        for f in ('impressions', 'clicks', 'sales', 'page_reads'): a[f] += r[f]
    out = []
    rows = [(a['date'], a['campaign_id'], 0, a) for a in summ.values()] + [(r['date'], r['campaign_id'], 1, r) for r in daily]
    rows.sort(key=lambda x: (x[0], x[1] == ST['ad_campaign']['campaign_id'], x[1], x[2]), reverse=True)
    n = 0
    for _, _, kind, a in rows:
        if kind == 0:
            n += 1
            out.append(dict(ad_id='AD-W%03d' % n, date=a['date'], campaign_id=a['campaign_id'], days=a['days'], spend=round(a['spend'], 2), impressions=a['impressions'], clicks=a['clicks'], sales=a['sales'],
                            page_reads=a['page_reads'], royalties=round(a['royalties'], 2)))
        else:
            out.append(dict(ad_id=a['ad_id'], date=a['date'], campaign_id=a['campaign_id'], days=1, spend=a['spend'], impressions=a['impressions'], clicks=a['clicks'], sales=a['sales'],
                            page_reads=a['page_reads'], royalties=a['royalties']))
    return out


PROMO_ORD = sorted(PRF, key=lambda p: (p['promo_id'] != 'PM-012', p['promo_id']))


def promos_d():
    return [dict(promo_id=p['promo_id'], title=p['title'], kind=key('pkind', p['kind']), start_date=p['start_date'], end_date=p['end_date'], days=p['days'], normal_price=p['normal_price'],
                 promo_price=p['promo_price'], cost=p['cost'], units_before=p['units_before'], units_during=p['units_during'], units_after=p['units_after'], pages_before=p['pages_before'],
                 pages_during=p['pages_during'], status=key('pstatus', p['status'])) for p in PROMO_ORD]


def _ebook(title):
    return next(e for e in EDS if e['title'] == title and e['format'] == 'Ebook')


def pricetests_d():
    """12 price tests of released ebooks: price A against price B over equal periods; units follow a believable price response with noise"""
    r = rng('au4-pt'); out = []
    cand = [t for t in TIT if t['status'] == 'Released' and t['title_id'] not in ('TL-018',)]
    picks = [cand[i] for i in (1, 2, 3, 5, 7, 8, 10, 11, 12, 13, 16, 17)]
    prices = [(4.99, 5.99), (5.99, 4.99), (5.99, 6.99), (3.99, 4.99), (4.99, 3.99), (6.99, 5.99), (5.99, 4.99), (6.99, 7.99), (4.99, 5.99), (5.99, 6.99), (3.99, 2.99), (4.99, 5.99)]
    resp = [0.93, 1.32, 0.80, 0.90, 1.12, 1.40, 1.30, 0.97, 0.86, 0.92, 1.06, 1.25]      # B units against A units
    for i, (t, (a, b), k) in enumerate(zip(picks, prices, resp)):
        start = T0 - _dt.timedelta(days=395 - i * 33)
        mon = [s for s in SALES if s['title_id'] == t['title_id'] and s['format'] == 'Ebook' and s['month'] == iso(_dt.date(start.year, start.month, 1))]
        base = max(1.0, sum(s['units'] for s in mon) / 30.0)
        days = 14 + 7 * (i % 3)
        ua = int(round(base * days * r.uniform(0.85, 1.1))); ub = int(round(ua * k * r.uniform(0.95, 1.05)))
        sh = lambda p: 0.70 if p >= 2.99 else 0.35
        out.append(dict(test_id='PT-%02d' % (i + 1), title=t['title'], start_date=iso(start), price_a=a, price_b=b, days_a=days, days_b=days, units_a=ua, units_b=ub,
                        royalty_a=round(a * sh(a) - 0.12, 2), royalty_b=round(b * sh(b) - 0.12, 2)))
    return out


# ------------------------------------------------------------------ aggregated tables (keys only: the workbook computes the rest)
def breakeven_d():
    out = []
    for e in sorted(EDS, key=lambda e: (e['edition_id'] != 'ED-0006', e['edition_id'])):
        t = TNAME[e['title']]
        st = {'Ebook': 'Ebook store' if t['exclusive'] else 'Wide distribution', 'Audiobook': 'Audiobook store'}.get(e['format'], 'Print-on-demand')
        out.append(dict(edition_id=e['edition_id'], store=key('store', st)))
    return out


def maxbid_d(): return [dict(campaign_id=c['campaign_id']) for c in CAMP_ORD]
def ledger_d(): return [dict(campaign_id=c['campaign_id']) for c in CAMP_ORD]
def rank_d(): return [dict(place=i) for i in range(1, len(CAMP) + 1)]


def _first_ad_month(): return dd(min(r['month'] for r in ADF))


def months_ad():
    m = _first_ad_month(); out = []
    while m <= month_start(0): out.append(m); m = add_months(m, 1)
    return out


def adsmonth_d(): return [dict(month=iso(m)) for m in reversed(months_ad())]


def adsplat_d():
    out = []; i = 0
    for m in reversed(months_ad()):
        for p in AD_PLATFORMS:
            i += 1; out.append(dict(line_id='AP-%03d' % i, platform=key('platform', p), month=iso(m)))
    return out


def adstitle_d():
    return [dict(title_id=t['title_id'], pen_name=key('penname', t['pen_name']), series=key('series', t['series'])) for t in TIT]


def adscompare_d(): return [dict(title_id=t['title_id']) for t in TIT]
def conv_d(): return [dict(title_id=t['title_id'], series=key('series', t['series'])) for t in TIT]
def promoresults_d(): return [dict(promo_id=p['promo_id'], kind=key('pkind', p['kind'])) for p in PROMO_ORD]
def pricecmp_d(): return [dict(test_id=p['test_id']) for p in pricetests_d()]


def salesmonth_d():
    out = []; i = 0
    ms = [month_start(k) for k in range(11, -1, -1)]
    agg = defaultdict(lambda: [0, 0.0]); pg = defaultdict(float)
    for s in SALES:
        agg[(s['title_id'], s['month'])][0] += s['units']; agg[(s['title_id'], s['month'])][1] += s['royalty_home']
    for p in PRD: pg[(p['title_id'], p['month'])] += p['pages_read'] * p['rate']
    for m in ms:
        for t in TIT:
            k = (t['title_id'], iso(m))
            if k in agg and agg[k][0] > 0:
                i += 1; out.append(dict(line_id='SM-%03d' % i, month=iso(m), title=t['title'], units=agg[k][0], royalties_home=round(agg[k][1], 2), page_income=round(pg.get(k, 0.0), 2)))
    return out
