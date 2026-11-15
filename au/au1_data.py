"""Author and Self-Publisher suite part 1: demo rows from au_core (full generator output where a table is small, thinned or built where it is a register or a list)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au1_lists import *
import datetime as _dt, math, collections

dd = to_date
R = core.rng('au1')
ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))

TEAM = {t['name']: t for t in team}
def phone(name): return TEAM[name]['phone']
def role_phone(role): return [t for t in team if t['role'] == role][0]['phone']
PH = {'assistant': role_phone('Virtual assistant'), 'launch': role_phone('Launch coordinator'), 'ad': role_phone('Ad specialist'), 'web': role_phone('Web developer'),
      'rights': role_phone('Rights agent'), 'printer': role_phone('Printer'), 'organiser': role_phone('Event organiser'), 'author': role_phone('Author-publisher'),
      'accountant': role_phone('Accountant'), 'formatter': role_phone('Formatter'), 'designer': role_phone('Cover designer')}

TLF = core.title_rows(); TLD = {t['title_id']: t for t in TLF}
EDF = core.edition_rows()
JBF = core.job_rows()
PMF = core.promo_rows()

# ebook copies a month: the average of the last 3 full months of the ledger (typed in from the sales sheet)
_m0 = month_start(3); _m1 = month_start(0); _eb = collections.Counter()
for _x in core.sales_rows():
    if _x['format'] == 'Ebook' and _m0 <= dd(_x['month']) < _m1: _eb[_x['title_id']] += _x['units']
EBM = {k: int(round(v / 3.0)) for k, v in _eb.items()}

# demo touches (documented): four editions with a data problem for the checks: a blank identifier, a duplicate identifier, a missing page count, a missing release date
_live_pb = [e for e in EDF if e['format'] == 'Paperback' and e['status'] == 'Live']
TOUCH = {'blank_id': _live_pb[7]['edition_id'], 'dup_id': _live_pb[11]['edition_id'], 'no_pages': [e for e in EDF if e['format'] == 'Hardcover' and e['status'] == 'Live'][3]['edition_id'],
         'no_date': [e for e in EDF if e['title_id'] == 'TL-018' and e['format'] == 'Paperback'][0]['edition_id']}
_dup_src = _live_pb[10]['identifier']
ED = []
for e in EDF:
    e = dict(e)
    if e['edition_id'] == TOUCH['blank_id']: e['identifier'] = ''
    if e['edition_id'] == TOUCH['dup_id']: e['identifier'] = _dup_src
    if e['edition_id'] == TOUCH['no_pages']: e['pages'] = 0
    if e['edition_id'] == TOUCH['no_date']: e['release_date'] = ''
    ED.append(e)
EDD = {e['edition_id']: e for e in ED}


def titles_d():
    return [nb(dict(title_id=t['title_id'], title=t['title'], pen_name=key('penname', t['pen_name']), series=key('series', t['series']), series_order=t['series_order'], genre=key('genre', t['genre']),
                    words=t['words'], pages=t['pages'], release_date=t['release_date'], status=key('tstatus', t['status']), exclusive=bool(t['exclusive']), preorders=t['preorders'],
                    royalty_before=t['royalty_before'], ebook_copies_month=EBM.get(t['title_id'], 0))) for t in TLF]


def editions_d():
    return [nb(dict(edition_id=e['edition_id'], title_id=e['title_id'], title=e['title'], format=key('format', e['format']), list_price=e['list_price'], unit_cost=e['unit_cost'],
                    royalty_share=e['royalty_share'], identifier=e['identifier'], pages=e['pages'], hours=e['hours'], release_date=e['release_date'], status=key('estatus', e['status']))) for e in ED]


def series_d():
    return [dict(series=key('series', s['series']), pen_name=s['pen_name'], books_planned=s['books_planned']) for s in core.series_rows()]


def formats_d(): return [dict(format=key('format', f['format']), royalty_share=f['royalty_share'], base_cost=f['base_cost']) for f in core.formats]
def stores_d(): return [dict(store=key('store', s['store']), royalty_share=s['royalty_share'], delay_days=s['delay_days']) for s in core.stores]


def team_d(): return [dict(person_id=t['person_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email']) for t in team]


# ---------------------------------------------------------------- series plan steps (26)
def steps_d():
    out = []; n = 0
    SRW = {s['series']: s for s in core.series_rows()}
    for sname in SERIES:
        ts = sorted([t for t in TLF if t['series'] == sname], key=lambda t: (t['series_order'], t['release_date']))
        rt = SRW[sname]['expected_readthrough']; planned = SRW[sname]['books_planned']
        costs = [core.title_cost(t['title_id']) for t in ts if core.title_cost(t['title_id']) > 0]
        avg_cost = round(sum(costs) / max(1, len(costs)) * 1.05, -1) if costs else 0
        for i, t in enumerate(ts, 1):
            n += 1; last = (i == len(ts)) and planned == len(ts)
            exp = 0 if (sname in ('Standalone', 'Box set') or last) else round(max(0.2, rt + [0.04, -0.03, 0.02, -0.05, 0.03, 0.0][(i - 1) % 6]), 2)
            out.append(nb(dict(step_id='SP-%02d' % n, series=key('series', sname), book_number=i if t['series_order'] == 0 else t['series_order'], title=t['title'], planned_release=t['release_date'],
                               planned_cost=core.title_cost(t['title_id']) or round(avg_cost * 0.6, -1), expected_readthrough=exp, status=key('planstatus', {'Released': 'Released', 'Pre-order': 'Pre-order', 'In production': 'In production'}[t['status']]))))
        extra = planned - len(ts)
        for j in range(extra):
            n += 1; lastd = dd(ts[-1]['release_date']); gap = {'Lantern Bay Mysteries': 330, 'Quiet Hollow Cases': 420, 'The Ember Crown': 330}.get(sname)
            date = (lastd + _dt.timedelta(days=gap)).isoformat() if gap else ''
            out.append(nb(dict(step_id='SP-%02d' % n, series=key('series', sname), book_number=len(ts) + j + 1, title='Book %d (untitled)' % (len(ts) + j + 1), planned_release=date,
                               planned_cost=avg_cost, expected_readthrough=0, status=key('planstatus', 'Planned'))))
    return out


# ---------------------------------------------------------------- store price list (80)
_FXN = {c: core.fx_rate(c, month_start(0)) for c in CURRENCIES}
_STORE_OF = {'Ebook': ['Ebook store', 'Wide distribution', 'Direct store'], 'Paperback': ['Print-on-demand', 'Wide distribution', 'Direct store'], 'Hardcover': ['Print-on-demand', 'Direct store'],
             'Large print': ['Print-on-demand', 'Wide distribution'], 'Audiobook': ['Audiobook store', 'Library and lending', 'Direct store']}
_CUR_OF = {'Ebook store': ['Dollar', 'Pound', 'Euro', 'Australian dollar', 'Canadian dollar'], 'Print-on-demand': ['Dollar', 'Pound', 'Euro'], 'Audiobook store': ['Dollar', 'Pound', 'Euro'],
           'Library and lending': ['Dollar', 'Pound'], 'Wide distribution': ['Euro', 'Canadian dollar', 'Australian dollar', 'Dollar'], 'Direct store': ['Home currency']}


def _charm(x): return round(x, 2) if x < 1.5 else round(round(x * 2) / 2.0 - 0.01, 2)


_STALE_TITLES = {'TL-001', 'TL-002', 'TL-003', 'TL-007', 'TL-011', 'TL-012'}


def storeprices_d():
    live = [e for e in ED if e['status'] in ('Live', 'Pre-order')]
    rows = []
    for i, e in enumerate(live):
        ss = _STORE_OF[e['format']]; rows.append((e, ss[0]))
    extra = [e for e in live if e['format'] in ('Ebook', 'Paperback', 'Audiobook')][:40]
    for i, e in enumerate(extra):
        if len(rows) >= 80: break
        if i % 2 == 0: rows.append((e, _STORE_OF[e['format']][1]))
        elif len(rows) < 80 and e['format'] != 'Audiobook' and i % 4 == 1: rows.append((e, _STORE_OF[e['format']][2]))
    k = 0
    while len(rows) < 80:
        e = extra[k % len(extra)]; k += 1
        ss = _STORE_OF[e['format']]
        if (e, ss[-1]) not in rows: rows.append((e, ss[-1]))
        if k > 400: break
    rows = rows[:80]
    out = []; bad = {7, 19, 33, 46, 58, 71}
    for i, (e, st) in enumerate(rows):
        cur = _CUR_OF[st][(i // 2 + i) % len(_CUR_OF[st])]
        rate = _FXN[cur]; price = _charm(e['list_price'] / rate)
        if i in bad: price = _charm(price * (1.24 if i % 2 else 0.76))
        old = e['title_id'] in _STALE_TITLES
        days = [4, 21, 47, 66, 93, 118, 140, 162][i % 8] if not (old and i % 3 != 1) else [196, 238, 284, 330, 391][i % 5]
        out.append(dict(price_id='SP-%03d' % (i + 1), edition_id=e['edition_id'], store=key('store', st), currency=key('currency', cur), price=price, rate=rate, checked_on=ago(days)))
    return out


# ---------------------------------------------------------------- jobs and promotions
def _paid_recent(n):
    ps = [j for j in JBF if j['status'] == 'Paid']
    ps.sort(key=lambda j: j['due_date'])
    return ps[-n:]


def _deadline_jobs():
    openj = [j for j in JBF if j['status'] != 'Paid']
    must = list(openj)
    for who in ('Amara Oyelaran', 'Gideon Falk', 'Yuki Tanabe', 'Noor Castellan'):
        if not any(j['contractor'] == who for j in must):
            pj = [j for j in JBF if j['contractor'] == who and j['status'] == 'Paid']
            if pj: must.append(pj[-1])
    ids = {j['job_id'] for j in must}
    rest = [j for j in _paid_recent(60) if j['job_id'] not in ids][-(30 - len(must)):]
    return sorted(must + rest, key=lambda j: j['due_date'])


DJ = _deadline_jobs()


def deadlines_d():
    return [nb(dict(job_id=j['job_id'], title=j['title'], kind=key('jobkind', j['kind']), contractor=key('person', j['contractor']), start_date=j['start_date'], due_date=j['due_date'],
                    delivered_on=j['delivered_on'])) for j in DJ]


_extra_promo = dict(promo_id='PM-024', title_id='TL-011', title='Shard of the Ember Crown', kind='Holiday sale', start_date=ahead(72), end_date=ahead(77), days=6, normal_price=2.99, promo_price=0.99,
                    cost=60.0, units_before=0, units_during=0, units_after=0, pages_before=0, pages_during=0, status='Planned')
PMX = [dict(p) for p in PMF] + [_extra_promo]


def promos_d():
    return [dict(promo_id=p['promo_id'], title=p['title'], kind=key('pkind', p['kind']), start_date=p['start_date'], end_date=p['end_date'], normal_price=p['normal_price'], promo_price=p['promo_price'])
            for p in PMX]


# ---------------------------------------------------------------- release calendar (36)
def calendar_d():
    rows = []
    def add(d, kind, title, note): rows.append((d, kind, title, note))
    for tid in ('TL-006', 'TL-010', 'TL-015', 'TL-018'):
        t = TLD[tid]; add(t['release_date'], 'Release', t['title'], '%s, book %d' % (t['series'], t['series_order']))
    add(core.PRE_START.isoformat(), 'Pre-order opens', TLD['TL-015']['title'], 'Pre-order page live on the stores')
    add(d_add(TLD['TL-018']['release_date'], -60), 'Pre-order opens', TLD['TL-018']['title'], 'Pre-order opens 60 days before release')
    for eid, note in (('ED-0021', 'Large print edition planned'), ('ED-0050', 'Hardcover edition planned'), ('ED-0051', 'Audiobook in production, due to publish')):
        e = EDD[eid]; add(e['release_date'], 'Planned edition', e['title'], note)
    for p in [p for p in PMX if p['status'] == 'Done'][-7:] + [p for p in PMX if p['status'] == 'Planned']:
        add(p['start_date'], 'Promotion starts', p['title'], '%s, %.2f to %.2f' % (p['kind'], p['normal_price'], p['promo_price']))
    for j in sorted([j for j in JBF if j['status'] != 'Paid'], key=lambda j: j['due_date']) + _paid_recent(8):
        add(j['due_date'], 'Contractor deadline', j['title'], '%s, %s' % (j['kind'], j['contractor']))
    rows = rows[:36]
    rows.sort(key=lambda r: r[0])
    return [dict(entry_id='CL-%02d' % (i + 1), date=d, kind=key('ckind', k), title=t, note=n) for i, (d, k, t, n) in enumerate(rows)]


def gaps_d():
    return [dict(title=t['title']) for t in sorted(TLF, key=lambda t: t['release_date'])]


def completeness_d(): return [dict(edition_id=e['edition_id']) for e in ED]


def pipeline_d(): return [dict(status=key('estatus', s), format=key('format', f)) for s in EDITION_STATUS for f in FORMATS]


def pricepage_d(): return [dict(edition_id=e['edition_id']) for e in ED if e['format'] in ('Paperback', 'Hardcover', 'Large print')]


def calmonths_d(): return [dict(month=add_months(month_start(0), k).isoformat()) for k in range(-2, 12)]


def coverage_d(): return [dict(title=t['title']) for t in TLF]


def genre_d(): return [dict(genre=key('genre', g), status=key('tstatus', s)) for g in GENRES for s in TITLE_STATUS]


def reading_d():
    order = []
    for pen in PEN_NAMES:
        for s in SERIES:
            ts = sorted([t for t in TLF if t['pen_name'] == pen and t['series'] == s], key=lambda t: (t['series_order'], t['release_date']))
            order += ts
    return [dict(title=t['title']) for t in order]


_WISH = [('TL-005', 'Large print', 17.99, 75, 190, 'High', 'Booked', 'Large print file from the same interior'),
         ('TL-015', 'Hardcover', 27.99, 88, 320, 'High', 'Quoted', 'Hardcover for the launch window'),
         ('TL-004', 'Audiobook', 17.99, 150, 2650, 'Medium', 'Quoted', 'Narrator quote for about 9 finished hours'),
         ('TL-006', 'Audiobook', 17.99, 210, 3100, 'High', 'Idea', 'Newest book of the mystery series'),
         ('TL-013', 'Audiobook', 17.99, 240, 2900, 'Medium', 'Idea', 'Book 3 of the fantasy series'),
         ('TL-011', 'Large print', 17.99, 100, 190, 'Medium', 'Idea', 'Series starter, readers ask for larger type'),
         ('TL-012', 'Large print', 18.99, 130, 190, 'Low', 'Idea', 'After the first large print is live'),
         ('TL-004', 'Hardcover', 25.99, 95, 260, 'Low', 'On hold', 'Wait for the audiobook decision'),
         ('TL-007', 'Hardcover', 25.99, 160, 260, 'Low', 'Idea', 'Gift edition of book 1'),
         ('TL-020', 'Paperback', 14.99, 60, 640, 'Medium', 'Quoted', 'Second edition with a new cover'),
         ('TL-016', 'Paperback', 13.99, 45, 600, 'Medium', 'On hold', 'Second edition after the cover refresh'),
         ('TL-001', 'Ebook', 3.99, 30, 560, 'High', 'Booked', 'Relaunch with a new cover and a new price')]


def wishlist_d():
    return [dict(wish_id='WL-%02d' % (i + 1), title=TLD[t]['title'], format=key('format', f), planned_price=p, planned_release=ahead(d), planned_cost=c, priority=key('wprio', pr),
                 status=key('wstatus', st), note=n) for i, (t, f, p, d, c, pr, st, n) in enumerate(_WISH)]
