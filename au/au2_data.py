"""Author and Self-Publisher suite, part 2: demo rows from au_core (full job and payment generators, aggregated tables built from the full ledger)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au2_lists import *
import datetime as _dt

dd = to_date
ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}

TEAM = {t['name']: t for t in team}
PHONE = {t['name']: t['phone'] for t in team}
TITLES = title_rows(); TT = {t['title_id']: t for t in TITLES}
EDS = edition_rows(); EE = {e['edition_id']: e for e in EDS}
JOBS = job_rows(); JB = {j['job_id']: j for j in JOBS}
PAYS = jobpay_rows()
WIN_MONTHS = [iso(month_start(k)) for k in range(11, -1, -1)]
CUR_M = iso(month_start(0))

# ---- ledger aggregates (home currency): title+month, edition lifetime, ebook copies a month
_SR = sales_rows(); _PR = pageread_rows()
TM = {}; ED_ROY = {}; ED_UNITS = {}; TL_ROY = {}; EB_6 = {}
for x in _SR:
    k = (x['title_id'], x['month']); TM[k] = TM.get(k, 0.0) + x['royalty_home']
    ED_ROY[x['edition_id']] = ED_ROY.get(x['edition_id'], 0.0) + x['royalty_home']
    ED_UNITS[x['edition_id']] = ED_UNITS.get(x['edition_id'], 0) + x['units']
    TL_ROY[x['title_id']] = TL_ROY.get(x['title_id'], 0.0) + x['royalty_home']
    if x['format'] == 'Ebook' and iso(month_start(6)) <= x['month'] < CUR_M: EB_6[x['title_id']] = EB_6.get(x['title_id'], 0) + x['units']
for x in _PR:
    k = (x['title_id'], x['month']); TM[k] = TM.get(k, 0.0) + x['income']
    ED_ROY[x['edition_id']] = ED_ROY.get(x['edition_id'], 0.0) + x['income']
    TL_ROY[x['title_id']] = TL_ROY.get(x['title_id'], 0.0) + x['income']
EB_MONTH = {t: v / 6.0 for t, v in EB_6.items()}
TITLE_FULL = {t['title_id']: title_royalty(t['title_id']) for t in TITLES}
WIN_SUM = {}
for (tid, m), v in TM.items():
    if m in WIN_MONTHS: WIN_SUM[tid] = WIN_SUM.get(tid, 0.0) + round(v)
ROYALTY_BEFORE = {t['title_id']: max(0.0, round(TITLE_FULL[t['title_id']] - WIN_SUM.get(t['title_id'], 0.0))) for t in TITLES}
SCALE = {t: (TITLE_FULL[t] / TL_ROY[t] if TL_ROY.get(t) else 1.0) for t in TT}


def team_d(): return [dict(person_id=t['person_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email'], rate=t['rate'], rate_unit=t['rate_unit']) for t in team]


def titles_d():
    return [dict(title_id=t['title_id'], title=t['title'], pen_name=key('penname', t['pen_name']), series=key('series', t['series']), release_date=t['release_date'],
                 status=key('tstatus', t['status']), words=t['words'], royalty_before=ROYALTY_BEFORE[t['title_id']]) for t in TITLES]


def editions_d():
    return [nb(dict(edition_id=e['edition_id'], title_id=e['title_id'], title=e['title'], format=key('format', e['format']), list_price=e['list_price'], unit_cost=e['unit_cost'],
                    royalty_share=e['royalty_share'], hours=e['hours'], release_date=e['release_date'], status=key('estatus', e['status']))) for e in EDS]


def jobs_d():
    first = [j for j in JOBS if j['job_id'] == ST['invoice']['job_id']]
    rest = sorted([j for j in JOBS if j['job_id'] != ST['invoice']['job_id']], key=lambda j: j['start_date'], reverse=True)
    return [nb(dict(job_id=j['job_id'], title_id=j['title_id'], title=j['title'], edition_id=j['edition_id'], kind=key('jobkind', j['kind']), contractor=j['contractor'], quote=j['quote'],
                    units=j['units'], unit_rate=j['unit_rate'], start_date=j['start_date'], due_date=j['due_date'], delivered_on=j['delivered_on'], paid=j['paid'], status=key('jstatus', j['status'])))
            for j in first + rest]


def jobpay_d():
    ordered = sorted([p for p in PAYS if p['status'] != 'Paid'], key=lambda p: p['date']) + sorted([p for p in PAYS if p['status'] == 'Paid'], key=lambda p: p['date'], reverse=True)
    return [dict(cpay_id=p['cpay_id'], job_id=p['job_id'], title_id=p['title_id'], contractor=p['contractor'], stage=key('stage', p['stage']), date=p['date'], amount=p['amount'],
                 status=key('cpaystatus', p['status'])) for p in ordered]


def cost_cat_d(): return [dict(kind=key('jobkind', c['kind']), unit=c['unit'], rate=c['rate']) for c in cost_categories]


def roy_month_d():
    out = []
    for t in TITLES:
        for m in WIN_MONTHS:
            v = TM.get((t['title_id'], m))
            if v and round(v) > 0:
                out.append(dict(roy_id='RM-%04d' % (len(out) + 1), title=t['title'], month=m, series=key('series', t['series']), royalties=round(v)))
    return out


def cash_d():
    rows = cash_rows()[-14:]
    return [dict(month=r['month'], closing=round(r['closing'])) for r in rows]


def cost_edition_d():
    out = []
    for e in EDS:
        f = SCALE[e['title_id']]
        out.append(dict(edition_id=e['edition_id'], copies_sold=int(round(ED_UNITS.get(e['edition_id'], 0) * f)), royalties_earned=round(ED_ROY.get(e['edition_id'], 0.0) * f)))
    return out


def budget_d(): return [dict(job_id=j['job_id']) for j in JOBS if j['kind'] != 'Setup and identifiers']
def unitcost_d(): return [dict(job_id=j['job_id']) for j in JOBS if j['units'] and j['units'] > 0]
def cost_title_d(): return [dict(title_id=t['title_id']) for t in TITLES]
def payback_d(): return [dict(title_id=t['title_id']) for t in TITLES]
def rank_d(n): return [dict(rank_no=i) for i in range(1, n + 1)]
def contractors_d(): return [dict(contractor=key('contractor', c)) for c in CONTRACTORS]
def be_series_d(): return [dict(series=key('series', s), format=key('format', f)) for s in SERIES for f in FORMATS]


def gonogo_d():
    """12 cases: new editions the author may produce; copies a month come from the title's own ebook sales times a ratio (your own number)"""
    spec = [('TL-004', 'Audiobook'), ('TL-008', 'Audiobook'), ('TL-013', 'Audiobook'), ('TL-017', 'Audiobook'), ('TL-009', 'Audiobook'),
            ('TL-005', 'Large print'), ('TL-008', 'Large print'), ('TL-013', 'Large print'), ('TL-009', 'Large print'),
            ('TL-015', 'Hardcover'), ('TL-004', 'Hardcover'), ('TL-014', 'Hardcover')]
    ratio = {'Audiobook': 0.09, 'Large print': 0.05, 'Hardcover': 0.035}
    rows = []
    for i, (tid, fm) in enumerate(spec, 1):
        t = TT[tid]; eb = EB_MONTH.get(tid, 60.0)
        if tid == 'TL-015': eb = 140.0
        ebk = [e for e in EDS if e['title_id'] == tid and e['format'] == 'Ebook'][0]
        pb = [e for e in EDS if e['title_id'] == tid and e['format'] == 'Paperback'][0]
        if fm == 'Audiobook':
            hrs = round(t['words'] / 9300.0, 1); cost = round(hrs * 285.0, -1); price = 14.99 if hrs <= 9 else 17.99 if hrs <= 11.5 else 22.99; rpc = round(price * 0.40, 2)
        elif fm == 'Large print':
            cost = 90.0 + 150.0 + 12.0 * i; price = 17.99 if t['pages'] < 380 else 19.99; rpc = round(price * 0.60 - (1.2 + 0.0118 * t['pages'] * 1.4), 2)
        else:
            cost = 110.0 + 150.0 + 18.0 * i; price = 24.99 if t['pages'] < 420 else 27.99; rpc = round(price * 0.60 - (6.5 + 0.0145 * t['pages']), 2)
        mid = max(1, int(round(eb * ratio[fm])))
        rows.append(dict(case_id='GN-%02d' % i, title=t['title'], format=key('gofmt', fm), opened_on=ago(5 + 9 * (12 - i)), one_off_cost=cost, list_price=price, royalty_per_copy=rpc,
                         copies_low=max(1, int(round(mid * 0.5))), copies_mid=mid, copies_high=int(round(mid * 1.6)) + 1, status=key('gostatus', 'Open' if i in (1, 6, 10, 11) else 'Decided')))
    return rows


def translation_d():
    spec = [('TL-001', 'Japanese', 55, 380, 260, 5.99, 40), ('TL-001', 'German', 58, 420, 260, 5.99, 55), ('TL-001', 'Spanish', 52, 380, 240, 4.99, 48), ('TL-007', 'German', 58, 420, 260, 5.99, 38),
            ('TL-011', 'German', 58, 520, 300, 6.99, 62), ('TL-011', 'French', 56, 480, 280, 6.99, 34), ('TL-016', 'Spanish', 52, 440, 280, 3.99, 58), ('TL-012', 'Portuguese', 50, 520, 280, 6.99, 30),
            ('TL-002', 'Italian', 54, 400, 260, 5.99, 22), ('TL-008', 'Polish', 48, 400, 240, 5.99, 14), ('TL-019', 'French', 56, 380, 260, 5.99, 20), ('TL-003', 'Japanese', 55, 400, 260, 5.99, 26)]
    rows = []
    for i, (tid, lg, rate, ed, cv, price, cm) in enumerate(spec, 1):
        t = TT[tid]
        rows.append(dict(case_id='TR-%02d' % i, title=t['title'], language=key('language', lg), translation_cost=round(t['words'] / 1000.0 * rate, -1), edit_cost=ed, cover_cost=cv,
                         price=price, royalty=round(price * 0.70 - 0.12, 2), copies_month=cm))
    return rows


def quotes_d():
    spec = [('Developmental edit', 'The Kelp Throne', 'Priya Nandakumar', 2450.0, 98.0, 30), ('Developmental edit', 'Crown of Last Embers', 'Leopold Brandt', 2380.0, 116.0, 35),
            ('Copy edit', 'The Kelp Throne', 'Leopold Brandt', 1830.0, 98.0, 28), ('Copy edit', 'Knots of Marrow Bay', 'Priya Nandakumar', 1990.0, 90.0, 25),
            ('Proofread', 'The Kelp Throne', 'Leopold Brandt', 690.0, 98.0, 14), ('Proofread', 'Knots of Marrow Bay', 'Priya Nandakumar', 740.0, 90.0, 12),
            ('Cover design', 'The Kelp Throne', 'Ines Carvalho', 560.0, 1.0, 40), ('Cover design', 'Crown of Last Embers', 'Ines Carvalho', 780.0, 1.0, 45),
            ('Formatting', 'The Kelp Throne', 'Tomasz Wrona', 170.0, 1.0, 10), ('Formatting', 'Knots of Marrow Bay', 'Tomasz Wrona', 95.0, 1.0, 8),
            ('Narration', 'Salt and Lantern Sky', 'Amara Oyelaran', 2850.0, 10.1, 60), ('Narration', 'The Kelp Throne', 'Gideon Falk', 4650.0, 10.5, 75),
            ('Translation', 'The Orchard Key', 'Yuki Tanabe', 4450.0, 81.0, 70), ('Translation', 'Oath of Brass Rivers', 'Yuki Tanabe', 5940.0, 108.0, 85),
            ('Setup and identifiers', 'The Kelp Throne', 'Noor Castellan', 56.0, 2.0, 5), ('Setup and identifiers', 'Crown of Last Embers', 'Tomasz Wrona', 84.0, 3.0, 6)]
    return [dict(quote_id='QT-%02d' % i, asked_on=ago(3 + 4 * (16 - i)), kind=key('jobkind', k), title=t, contractor=c, quote=q, units=u, days_to_deliver=d) for i, (k, t, c, q, u, d) in enumerate(spec, 1)]
