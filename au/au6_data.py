"""Author and self-publisher suite part 6: demo rows from au_core (inputs only; calculated columns are formulas)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au6_lists import *
import collections

dd = to_date
ST = story()
TITLES = title_rows(); TD = {t['title_id']: t for t in TITLES}; TBYNAME = {t['title']: t for t in TITLES}
SERIES_ROWS = series_rows()
EBOOK_PRICE = {e['title_id']: e['list_price'] for e in edition_rows() if e['format'] == 'Ebook'}
RELEASED = [t for t in TITLES if t['status'] == 'Released']
EXPECT = {s['series']: s['expected_readthrough'] for s in SERIES_ROWS}


def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}


def team_d():
    return [dict(person_id=t['person_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email']) for t in team]


def series_d():
    rows = [dict(series=key('series', s['series']), pen_name=s['pen_name'], books_planned=s['books_planned']) for s in SERIES_ROWS]
    return rows[3:4] + rows[:3] + rows[4:]      # the weak series first: it makes the best demo record


def titles_d():
    out = []
    for t in TITLES:
        tid = t['title_id']
        last_of_series = t['series'] in SERIES4 and t['series_order'] == max(x['series_order'] for x in TITLES if x['series'] == t['series'])
        exp = 0.0 if (t['series'] not in SERIES4 or last_of_series) else round(EXPECT[t['series']] + {1: 0.02, 2: 0.0, 3: -0.02, 4: 0.01, 5: 0.0}.get(t['series_order'], 0.0), 2)
        out.append(dict(title_id=tid, title=t['title'], pen_name=key('penname', t['pen_name']), series=key('series', t['series']), series_order=t['series_order'], genre=key('genre', t['genre']),
                        release_date=t['release_date'], status=key('tstatus', t['status']), words=t['words'], ebook_price=EBOOK_PRICE[tid], royalty_before=t['royalty_before'],
                        production_cost=title_cost(tid), expected_rt=exp))
    return out


# ---- ledger copies and royalties by title and month (home currency, page reads included) and costs by title and month
_AGG = collections.defaultdict(lambda: [0, 0.0])
for _x in sales_rows():
    _a = _AGG[(_x['title_id'], _x['month'])]; _a[0] += _x['units']; _a[1] += _x['royalty_home']
for _x in pageread_rows():
    _AGG[(_x['title_id'], _x['month'])][1] += _x['income']
SALES = sorted(((tid, m, v[0], round(v[1], 2)) for (tid, m), v in _AGG.items() if v[0] > 0), key=lambda r: (r[1], r[0]))


def tsales_d():
    return [dict(row_id='TS-%04d' % i, title=TD[tid]['title'], month=m, pen_name=key('penname', TD[tid]['pen_name']), series=key('series', TD[tid]['series']), units=u, royalties=r)
            for i, (tid, m, u, r) in enumerate(SALES, 1)]


_CST = collections.defaultdict(lambda: [0.0, 0.0])
for _x in ad_day_rows(): _CST[(_x['title_id'], _x['month'])][0] += _x['spend']
for _x in jobpay_rows():
    if _x['status'] == 'Paid': _CST[(_x['title_id'], _x['month'])][1] += _x['amount']


def tcosts_d():
    rows = sorted(((tid, m, round(a, 2), round(p, 2)) for (tid, m), (a, p) in _CST.items()), key=lambda r: (r[1], r[0]))
    return [dict(row_id='TC-%04d' % i, title=TD[tid]['title'], month=m, pen_name=key('penname', TD[tid]['pen_name']), ad_spend=a, production_paid=p) for i, (tid, m, a, p) in enumerate(rows, 1)]


def expenses_d():
    return [dict(expense_id=x['expense_id'], date=x['date'], month=x['month'], category=key('expcat', x['category']), vendor=x['vendor'], amount=x['amount'], pen_name=key('xpen', x['pen_name']))
            for x in expense_rows()]


# ---- series steps and chains (released titles only)
def _chain():
    out = []
    for s in SERIES4:
        ts = sorted([t for t in RELEASED if t['series'] == s], key=lambda t: t['series_order'])
        out.append((s, ts))
    return out


CHAIN = _chain()


def rtstep_d():
    out = []; k = 0
    for s, ts in CHAIN:
        for a, b in zip(ts, ts[1:]):
            k += 1
            out.append(dict(step_id='RT-%02d' % k, series=key('series4', s), stepno=key('bstep', 'Step %d' % a['series_order']), from_title=a['title'], to_title=b['title'], checked_on=ago(12 + (k * 23) % 250)))
    return out


def chain_d():
    out = []; k = 0
    for s, ts in CHAIN:
        for t in ts:
            k += 1; out.append(dict(row_id='CH-%02d' % k, series=key('series4', s), bookno=key('bookno', 'Book %d' % t['series_order']), title=t['title']))
    return out


def vreader_d():
    rows = [dict(row_id=c['row_id'].replace('CH', 'VR'), series=c['series'], bookno=c['bookno'], title=c['title']) for c in chain_d()]
    return rows[1:] + rows[:1]      # the first demo row is book 2 (a book 1 row has no read-through into it)


def drops_d(): return [dict(rank_no=i) for i in range(1, 13)]


def sincome_d():
    out = []; k = 0
    for s in SERIES:
        for j in range(15, -1, -1):
            k += 1; out.append(dict(row_id='SI-%03d' % k, series=key('series', s), month=iso(month_start(j))))
    return out


def pnl_d():
    out = []; k = 0
    ms = months24(); ms = ms[-2::-1] + ms[-1:]      # the last complete month first, then older months, the running month last
    for m in ms:
        for p in PEN_NAMES:
            k += 1; out.append(dict(row_id='PL-%02d' % k, pen_name=key('penname', p), month=iso(m)))
    return out


def sharesplit_d(): return [dict(row_id=r['row_id'].replace('PL', 'SP'), pen_name=r['pen_name'], month=r['month']) for r in pnl_d()]


def bundles_d():
    X = [  # case, bundle, series, books, singles total, bundle price, share, copies a month, singles copies lost a month, setup cost, decide by (days from today)
        ('BX-01', 'Lantern Bay Mysteries Books 1-3', 'Box set', 3, 14.97, 9.99, 0.70, 78, 18, 894.0, -300),
        ('BX-02', 'The Ember Crown Books 1-3', 'Box set', 3, 16.97, 10.99, 0.70, 91, 15, 866.0, -120),
        ('BX-03', 'Quiet Hollow Cases Books 1-3', 'Quiet Hollow Cases', 3, 14.97, 9.99, 0.70, 45, 20, 880.0, 21),
        ('BX-04', 'Lantern Bay Mysteries Books 4-6', 'Lantern Bay Mysteries', 3, 17.97, 10.99, 0.70, 30, 22, 840.0, 35),
        ('BX-05', 'The Ember Crown Books 4-5', 'The Ember Crown', 2, 13.98, 9.99, 0.70, 25, 20, 700.0, 60),
        ('BX-06', 'Tidebound Realms Books 1-3', 'Tidebound Realms', 3, 11.97, 8.99, 0.70, 40, 38, 850.0, 45),
        ('BX-07', 'Lantern Bay Mysteries Books 1-6 in print', 'Lantern Bay Mysteries', 6, 77.94, 39.99, 0.55, 14, 12, 950.0, 75),
        ('BX-08', 'Tamsin Hartwell mystery collection', 'Box set', 10, 59.90, 24.99, 0.70, 20, 30, 1300.0, 90),
        ('BX-09', 'Lantern Bay Mysteries Books 1-3 audiobook', 'Lantern Bay Mysteries', 3, 44.97, 34.99, 0.40, 15, 6, 600.0, 30),
        ('BX-10', 'Quiet Hollow Cases Books 1-4 in print', 'Quiet Hollow Cases', 4, 51.96, 29.99, 0.55, 12, 14, 900.0, 100),
        ('BX-11', 'Winter at Saltmere and Glassmaker duo', 'Standalone', 2, 12.98, 8.99, 0.70, 18, 14, 500.0, 50),
        ('BX-12', 'Tidebound Realms starter pair', 'Tidebound Realms', 2, 5.98, 4.99, 0.70, 35, 30, 420.0, 120)]
    return [dict(case_id=a, bundle=b, series=key('series', c), books=d, singles_total=e, bundle_price=f, share=g, copies_month=h, taken_month=i, setup_cost=j, decide_by=ahead(k)) for a, b, c, d, e, f, g, h, i, j, k in X]


_DEC = {'TL-009': 'Reprice', 'TL-014': 'Reprice', 'TL-020': 'Repackage', 'TL-019': 'Retire'}


def decisions_d():
    return [dict(title_id=t['title_id'], title=t['title'], decision=key('dverdict', _DEC.get(t['title_id'], 'Keep')), review_on=ahead(-40 + (i * 11) % 130)) for i, t in enumerate(TITLES)]


def ytest_d(): return [dict(title_id=t['title_id'], title=t['title'], series=key('series', t['series']), tested_on=ago(20 + (i * 17) % 330)) for i, t in enumerate(TITLES)]
def trend_d(): return [dict(title_id=t['title_id'], title=t['title']) for t in TITLES]
def ranking_d(): return [dict(rank_no=i) for i in range(1, 23)]
def backlist_d(): return [dict(month=iso(month_start(j))) for j in range(14, 0, -1)]


def target_d():
    T = [11000, 11500, 12000, 13000, 14000, 15000, 16000, 17500, 19000, 20500, 22000, 24000]
    A = [560, 555, 550, 545, 540, 535, 530, 520, 510, 500, 490, 480]
    return [dict(step_id='TI-%02d' % (i + 1), tstep=key('tstep', 'Step %d' % (i + 1)), target_income=T[i], avg_roy_book=A[i], books_on_sale=20 + (i // 4), review_on=ahead(i * 17 - 60)) for i in range(12)]
