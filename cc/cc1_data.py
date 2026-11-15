"""Childcare center suite part 1: demo rows from cc_core (full generator output where the table is small, aggregated tables built from it)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc1_lists import *
import datetime as _dt

dd = to_date
R = rng('cc1')
ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))

TEAM = {t['name']: t for t in team}
OWNER_PHONE = TEAM[OWNER]['phone']; DIRECTOR_PHONE = TEAM[ASSISTANT_DIRECTOR]['phone']
COOK_PHONE = [t for t in team if t['role'] == 'Cook'][0]['phone']
CHF = child_rows(); CHD = {c['child_id']: c for c in CHF}
ENF = enquiry_rows(); ENQ = {e['enquiry_id']: e for e in ENF}
TRF = tour_rows(); WLF = waitlist_rows(); MKF = marketing_rows()

# demo story touches (documented): two newest "New" enquiries have no first reply yet, one recent tour was a no-show, three withdrawn families had declined an offer
NEW_IDS = [e['enquiry_id'] for e in ENF if e['status'] == 'New'][-2:]
_held = [t for t in TRF if t['status'] == 'Held' and not t['applied'] and ago(70) <= t['date'] <= ago(10)]
NOSHOW_ID = _held[-1]['tour_id'] if _held else None
_wd = [w for w in WLF if w['status'] == 'Withdrawn' and w['added_on'] <= ago(60)]
DECLINED = {w['wait_id']: d_add(w['added_on'], 21 + 3 * i) for i, w in enumerate(_wd[-3:])}
WL = []
for w in WLF:
    w = dict(w)
    if w['wait_id'] in DECLINED: w['offered_on'] = DECLINED[w['wait_id']]
    WL.append(w)
WLD = {w['wait_id']: w for w in WL}


def rooms_d(): return [dict(room=key('room', r['room']), capacity=r['capacity'], ratio=r['ratio']) for r in rooms]


def rates_d():
    return [dict(rate_id=r['rate_id'], room=key('room', r['room']), schedule=key('schedule', r['schedule']), weekly_rate=r['weekly_rate'], last_year_rate=r['last_year_rate'],
                 days=r['days'], hours_day=r['hours_day'], day_rate=r['day_rate']) for r in rates]


def team_d():
    return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email'], room=t['room']) for t in team]


def enquiries_d():
    out = []
    for e in ENF:
        out.append(nb(dict(enquiry_id=e['enquiry_id'], date=e['date'], month=e['month'], name=e['name'], phone=e['phone'], child_age_months=e['child_age_months'], want_room=key('room', e['want_room']),
                           want_schedule=key('schedule', e['want_schedule']), want_start=e['want_start'], source=key('source', e['source']),
                           first_reply_hours=('' if e['enquiry_id'] in NEW_IDS else e['first_reply_hours']), status=key('estatus', e['status']),
                           reason=(key('lostreason', e['reason']) if e['reason'] else ''), tour_date=e['tour_date'], applied_on=e['applied_on'], enrolled_on=e['enrolled_on'])))
    return out


def tours_d():
    out = []
    for t in TRF:
        st = 'No-show' if t['tour_id'] == NOSHOW_ID else t['status']
        out.append(dict(tour_id=t['tour_id'], date=t['date'], enquiry_id=t['enquiry_id'], name=t['name'], phone=t['phone'], staff=t['staff'], status=key('tourstatus', st), source=key('source', t['source']),
                        applied=bool(t['applied']) and st == 'Held', room=key('room', t['room'])))
    return out


def waitlist_d():
    return [nb(dict(wait_id=w['wait_id'], enquiry_id=w['enquiry_id'], name=w['name'], phone=w['phone'], child_age_months=w['child_age_months'], room=key('room', w['room']), schedule=key('schedule', w['schedule']),
                    want_start=w['want_start'], added_on=w['added_on'], offered_on=w['offered_on'], started_on=w['started_on'], priority=key('priority', w['priority']), status=key('waitstatus', w['status']))) for w in WL]


def marketing_d():
    out = []; od = 0
    for m in MKF:
        e = m['enrolled']
        if m['kind'] == 'Open day':   # story touch: every second open day brought a child
            od += 1; e = 1 if od % 2 == 0 else 0
        out.append(dict(campaign_id=m['campaign_id'], month=m['month'], kind=key('mkind', m['kind']), source=key('source', m['source']), cost=m['cost'], enquiries=m['enquiries'], enrolled=e))
    return out


def _days_int(c):
    return len(c['days'].split()) if c['days'] else 5


def children_d():
    return [nb(dict(child_id=c['child_id'], child=c['child'], family=c['family'], guardian=c['guardian'], phone=c['phone'], room=key('room', c['room']), schedule=key('schedule', c['schedule']),
                    days=_days_int(c), start_date=c['start_date'], end_date=c['end_date'], status=key('cstatus', c['status']))) for c in CHF]


def places_d():
    out = []; m0 = month_start(0); i = 0
    for r in ROOMS:
        for k in range(-5, 7):
            i += 1; out.append(dict(place_id='PL-%02d' % i, room=key('room', r), month=iso(add_months(m0, k))))
    return out


def funnel_d(): return [dict(month=iso(m)) for m in months14()]


def sources_d(): return [dict(source=key('source', s)) for s in SOURCES]
def lost_d(): return [dict(reason=key('lostreason', s)) for s in LOST_REASONS]
def bands_d(): return [dict(band=key('rband', s)) for s in RBAND]
def kinds_d(): return [dict(kind=key('mkind', s)) for s in MARKETING_KINDS]


def applications_d():
    out = []; r = rng('cc1-app'); openn = 0
    for e in ENF:
        if not e['applied_on']: continue
        st = e['status']
        if st == 'Enrolled': a, forms, dep = 'Enrolled', True, True
        elif st == 'Waitlist': a, forms, dep = 'On waiting list', True, True
        elif st == 'Applied':
            openn += 1
            a, forms, dep = ('Forms pending', False, False) if openn == 1 else ('Deposit pending', True, False)
        else: a, forms, dep = 'Withdrawn', True, r.random() < .3
        out.append(dict(enquiry_id=e['enquiry_id'], name=e['name'], applied_on=e['applied_on'], room=key('room', e['want_room']), schedule=key('schedule', e['want_schedule']), want_start=e['want_start'],
                        forms_back=forms, deposit_paid=dep, status=key('appstatus', a)))
    return out


def offers_d():
    rows = sorted([w for w in WL if w['offered_on']], key=lambda w: w['offered_on']); out = []; r = rng('cc1-offer')
    for i, w in enumerate(rows, 1):
        o = dict(offer_id='OF-%03d' % i, wait_id=w['wait_id'], offered_on=w['offered_on'])
        if w['status'] == 'Started': o['answer'] = key('offerans', 'Accepted'); o['answered_on'] = d_add(w['offered_on'], r.randint(1, 4))
        elif w['status'] == 'Withdrawn': o['answer'] = key('offerans', 'Declined'); o['answered_on'] = d_add(w['offered_on'], r.randint(3, 6))
        out.append(o)
    return out


def tour_cal_d():
    out = []; d = T0; i = 0
    while len(out) < 15:
        if d.weekday() != 6:
            out.append(dict(date=iso(d), staff=(OWNER if i % 2 == 0 else ASSISTANT_DIRECTOR))); i += 1
        d += _dt.timedelta(days=1)
    return out


def fill_d(): return [dict(wait_id=w['wait_id']) for w in WL if w['status'] in ('Waiting', 'Offered')]


def demand_d():
    out = []; m0 = month_start(0)
    for r in ROOMS:
        for k in range(6): out.append(dict(room=key('room', r), month=iso(add_months(m0, k))))
    return out


def stale_d():
    op = [e for e in ENF if e['status'] in ('New', 'Tour booked', 'Tour held', 'Applied')]
    wl = [e for e in ENF if e['status'] == 'Waitlist'][:10]
    return [dict(enquiry_id=e['enquiry_id']) for e in op + wl]
