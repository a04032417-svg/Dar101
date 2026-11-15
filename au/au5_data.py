"""Author and self-publisher suite part 5: demo rows from au_core (full generator output where the table is small, aggregated tables built from it)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au5_lists import *
import collections

dd = to_date
ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}

TITLES = title_rows(); TD = {t['title_id']: t for t in TITLES}
TEAM = {t['name']: t for t in team}
def phone_of(role): return next(t['phone'] for t in team if t['role'] == role)

TASKS = launch_task_rows(); ARCS = arc_rows(); REVS = reviewer_rows(); SENDS = newsletter_rows(); SUBS = subscriber_rows(); SWAPS = swap_rows()
for _x in TASKS:
    if _x['task_id'] in ('LT-067', 'LT-068'): _x['status'] = 'Open'; _x['done_on'] = ''


def titles_d():
    return [dict(title_id=t['title_id'], title=t['title'], pen_name=key('penname', t['pen_name']), series=key('series', t['series']), release_date=t['release_date'], status=key('tstatus', t['status']),
                 preorders=t['preorders']) for t in sorted(TITLES, key=lambda t: t['release_date'], reverse=True)]


def team_d(): return [dict(person_id=t['person_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email']) for t in team]


def steps_d(): return [dict(step=key('step', s['step']), days_from_release=s['days_from_release'], owner_role=key('ownerrole', s['owner_role'])) for s in launch_steps]


def tasks_d():
    ordered = sorted(TASKS, key=lambda x: (x['status'] != 'Open', x['due_date'] if x['status'] == 'Open' else '', ''))
    ordered = sorted([x for x in TASKS if x['status'] != 'Open'], key=lambda x: x['done_on'], reverse=True) + [x for x in ordered if x['status'] == 'Open']
    return [nb(dict(task_id=x['task_id'], title_id=x['title_id'], title=x['title'], step=key('step', x['step']), owner=x['owner'], owner_role=key('ownerrole', PERSON[x['owner']]['role']), due_date=x['due_date'], done_on=x['done_on'],
                    status=key('taskstatus', x['status']))) for x in ordered]


def reviewers_d():
    return [dict(reviewer_id=r['reviewer_id'], name=r['name'], kind=key('rkind', r['kind']), email=r['email'], phone=r['phone'], joined_on=r['joined_on']) for r in REVS]


def arcs_d():
    return [nb(dict(arc_id=a['arc_id'], title_id=a['title_id'], title=a['title'], reviewer=a['reviewer'], sent_on=a['sent_on'], due_on=a['due_on'], posted_on=a['posted_on'],
                    status=key('arcstatus', a['status']))) for a in ARCS]


def sends_d():
    return [dict(send_id=s['send_id'], date=s['date'], month=s['month'], kind=key('skind', s['kind']), list_size=s['list_size'], sent=s['sent'], opens=s['opens'], clicks=s['clicks'],
                 unsubscribes=s['unsubscribes'], new_subscribers=s['new_subscribers'], sales_7d=s['sales_7d'], royalty_7d=s['royalty_7d']) for s in SENDS]


_SWC = [0, 0, 10, 0, 15, 5, 0, 12]
_SWFIX = {'SW-009': (62, 11), 'SW-011': (70, 9), 'SW-030': (80, 5)}      # three paid promotions that did not pay back their cost
SWAPS = [dict(s, cost=(_SWC[i % 8] if s['kind'] == 'Newsletter swap' else s['cost']), subscribers=_SWFIX.get(s['swap_id'], (s['subscribers'],))[0], sales_7d=_SWFIX.get(s['swap_id'], (0, s['sales_7d']))[1]) for i, s in enumerate(SWAPS)]
_SWM = collections.defaultdict(float)
for _s in SWAPS: _SWM[(_s['date'][:7] + '-01', _s['kind'])] += _s['cost']
_SRC_EXTRA = {'Event sign-up': [0, 6, 0, 9, 4, 0, 12, 0], 'Store page link': [5, 0, 7, 0, 0, 9, 3, 0]}


def subs_d():
    out = []
    for i, s in enumerate(SUBS):
        c = s['cost']
        if s['source'] in ('Newsletter swap', 'Paid promotion'): c = round(_SWM.get((s['month'], s['source']), 0.0), 2)
        elif s['source'] == 'Reader magnet': c = float(10 + (i * 7) % 7)
        elif s['source'] in _SRC_EXTRA: c = float(_SRC_EXTRA[s['source']][(i // 6) % 8])
        out.append(dict(row_id=s['row_id'], month=s['month'], source=key('subsource', s['source']), new_subscribers=s['new_subscribers'], lost=s['lost'], cost=c))
    return out


def swaps_d():
    return [dict(swap_id=s['swap_id'], date=s['date'], partner=s['partner'], phone=s['phone'], kind=key('swapkind', s['kind']), title=s['title'], cost=s['cost'], subscribers=s['subscribers'],
                 clicks=s['clicks'], sales_7d=s['sales_7d']) for s in SWAPS]


# ---- ledger copies and royalties by title and month (home currency), built from the full sales ledger
_AGG = collections.defaultdict(lambda: [0, 0.0])
for _x in sales_rows():
    _a = _AGG[(_x['title_id'], _x['month'])]; _a[0] += _x['units']; _a[1] += _x['royalty_home']
for _x in pageread_rows():
    _AGG[(_x['title_id'], _x['month'])][1] += _x['income']
SALES = sorted(((tid, m, v[0], round(v[1], 2)) for (tid, m), v in _AGG.items() if v[0] > 0), key=lambda r: (r[1], r[0]))


def titlesales_d():
    return [dict(title=TD[tid]['title'], month=m, units=u, royalties=r) for tid, m, u, r in SALES]


def _units(tid, m): return _AGG.get((tid, m), [0, 0.0])[0]
def _roy(tid, m): return _AGG.get((tid, m), [0, 0.0])[1]


# ---- launch results: typed launch numbers (from the store dashboards); the ledger titles are derived from the ledger, older launches are typed by the author
OLD = {'TL-008': (1180, 0.30, 0.56, 330, 0.53), 'TL-004': (1390, 0.27, 0.54, 360, 0.49), 'TL-013': (1260, 0.33, 0.57, 300, 0.55), 'TL-019': (1010, 0.29, 0.52, 270, 0.50),
       'TL-021': (1290, 0.31, 0.55, 290, 0.51)}      # copies in 12 months, 30-day share, 7-day share of the 30 days, pre-orders at release, pre-orders 30 days before as a share
PRE = {'TL-006': (400, 0.575), 'TL-010': (360, 0.545), 'TL-014': (310, 0.52), 'TL-017': (275, 0.50), 'TL-020': (240, 0.51), 'TL-022': (350, 0.56), 'TL-005': (290, 0.53), 'TL-009': (330, 0.55)}
LED = ['TL-006', 'TL-010', 'TL-022', 'TL-014', 'TL-020', 'TL-017', 'TL-005', 'TL-009']
AVG_ROY_COPY = 2.9


def launchres_d():
    out = []; r = rng('lr5')
    for tid in LED:
        t = TD[tid]; R = dd(t['release_date']); M0 = R.replace(day=1); m0 = iso(M0); m1 = iso(add_months(M0, 1))
        left = (add_months(M0, 1) - R).days
        c30 = int(round(_units(tid, m0) + _units(tid, m1) * max(0, 30 - left) / 30.0)); c7 = int(round(c30 * r.uniform(0.50, 0.58)))
        roy30 = round(_roy(tid, m0) + _roy(tid, m1) * max(0, 30 - left) / 30.0, 0)
        pt, ps = PRE[tid]
        out.append(dict(title=t['title'], copies_7d=c7, copies_30d=c30, royalties_30d=roy30, copies_12m_typed=0, pre_30=int(round(pt * ps)), pre_total=pt))
    for tid, (c12, s30, s7, pt, ps) in OLD.items():
        t = TD[tid]; c30 = int(round(c12 * s30)); out.append(dict(title=t['title'], copies_7d=int(round(c30 * s7)), copies_30d=c30, royalties_30d=round(c30 * AVG_ROY_COPY * (1.0 + 0.06 * (len(out) % 5 - 2)), 0),
                                                              copies_12m_typed=c12, pre_30=int(round(pt * ps)), pre_total=pt))
    for o in out:
        if not o['copies_12m_typed']: o.pop('copies_12m_typed')
    return out


def readiness_d(): return [dict(step=key('step', s['step'])) for s in launch_steps]
def ranking_d(): return [dict(reviewer_id=r['reviewer_id']) for r in REVS]
def responses_d(): return [dict(title=t['title']) for t in TITLES]
def sendres_d(): return [dict(send_id=s['send_id']) for s in SENDS]
def growth_d(): return [dict(month=iso(m)) for m in months24()]
def srccost_d(): return [dict(source=key('subsource', s)) for s in SUB_SOURCES]
def swapres_d(): return [dict(swap_id=s['swap_id']) for s in SWAPS]
def kindsales_d(): return [dict(kind=key('skind', s)) for s in SEND_KINDS]
def latesteps_d(): return [dict(rank_no=i) for i in range(1, 13)]

NEXT_TITLE = ST['launch']['title']
