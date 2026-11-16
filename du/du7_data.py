"""Doula business suite part 7: demo rows from du_core (full generator output for the row-level tables; calculated tables get only their key columns)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du7_lists import *
import datetime as _dt
import collections as _co

dd = to_date
ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def I(x): return iso(x) if hasattr(x, 'isoformat') else x
def front(rows, pred):
    """move the first row that matches to the top (the sheets and printable pages open on it)"""
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows


TEAMD = {t['name']: t for t in team}
OWNER_PHONE = TEAMD[OWNER]['phone']
VENUE_PHONE = [t for t in team if t['role'] == 'Class venue'][0]['phone']
CLF = client_rows(); CLN = {c['client']: c for c in CLF}; CLD = {c['client_id']: c for c in CLF}
CON = contract_rows(); RFF = referral_rows(); ENF = enquiry_rows(); MKF = marketing_rows(); CSF = class_session_rows(); CAF = class_attendee_rows(); RVF = review_rows()
CSD = {s['session_id']: s for s in CSF}
Y1 = T0 - _dt.timedelta(days=365); Y2 = T0 - _dt.timedelta(days=730)

# ------------------------------------------------------------------ referrers (every referrer in the referral rows, the busiest first)
_REFS = _co.defaultdict(list)
for r in RFF: _REFS[r['referrer']].append(r)
_SRC = {n: l[0]['source'] for n, l in _REFS.items()}
REF_ORDER = sorted(_REFS, key=lambda n: (-len(_REFS[n]), n))
def _ref_phone(name, i):
    if name in CLN: return CLN[name]['phone']
    if name in TEAMD: return TEAMD[name]['phone']
    if _SRC[name] == 'Class or workshop': return VENUE_PHONE
    return fake_phone(300 + i)
def referrers_d():
    return [dict(referrer=n, phone=_ref_phone(n, i), source=key('rsource', _SRC[n])) for i, n in enumerate(REF_ORDER)]
def _n12(n): return sum(1 for r in _REFS[n] if r['date'] > Y1)
def _p12(n): return sum(1 for r in _REFS[n] if Y2 < r['date'] <= Y1)
def _unthanked(n): return [r for r in _REFS[n] if r['client_id'] and r['thanked_on'] == '']


def referrals_d():
    out = []
    for r in RFF:
        out.append(nb(dict(referral_id=r['referral_id'], date=I(r['date']), source=key('rsource', r['source']), referrer=r['referrer'], enquiry_id=r['enquiry_id'], client_id=r['client_id'],
                           thanked_on=I(r['thanked_on']) if r['thanked_on'] else '', gift_cost=r['gift_cost'])))
    return front(out, lambda r: r['referrer'] == 'Birchwood Care Office' and r.get('client_id') and r.get('thanked_on') and r['date'] > ago(200))


def enquiries_d():
    return [nb(dict(enquiry_id=e['enquiry_id'], date=I(e['date']), name=e['name'], phone=e['phone'], source=key('source', e['source']), status=key('estatus', e['status']),
                    reason=key('lostreason', e['reason']) if e['reason'] else '', signed_on=I(e['signed_on']) if e['signed_on'] else '', client_id=e['client_id'])) for e in ENF]


def clients_d():
    out = [nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], kind=key('ckind', c['kind']), package=c['package'], doula=key('doula', c['doula']), source=key('source', c['source']),
                   signed_on=I(c['signed_on']), attended_on=I(c['attended_on']) if c['attended_on'] else '', status=key('cstatus', c['status']), edd=I(c['edd']))) for c in CLF]
    return front(out, lambda r: r.get('attended_on') and r['source'] == key('source', 'Care provider'))


def contracts_d():
    return [nb(dict(contract_id=c['contract_id'], client_id=c['client_id'], client=c['client'], package=c['package'], price=c['price'], signed_on=I(c['signed_on']), status=key('ctstatus', c['status']))) for c in CON]


def sources_d(): return [dict(source=key('source', s['source']), kind=s['kind'], gift_value=s['gift_value']) for s in sources_ref]
def _k(d): d['class'] = d.pop('klass'); return d
def class_types_d(): return [_k(dict(klass=key('ctype', t['class']), price=t['price'], seats=t['seats'])) for t in class_types]


def marketing_d():
    out = [dict(campaign_id=m['campaign_id'], month=I(m['month']), kind=key('mkind', m['kind']), source=key('source', m['source']), cost=m['cost'], enquiries=m['enquiries'], signed=m['signed']) for m in MKF]
    return front(out, lambda r: r['month'] == I(month_start(1)))


def class_sessions_d():
    out = [_k(dict(session_id=s['session_id'], date=I(s['date']), klass=key('ctype', s['class']), venue=s['venue'], instructor=key('doula', s['instructor']), seats=s['seats'], signed_up=s['signed_up'],
                attended=s['attended'], price=s['price'], hours=s['hours'], venue_cost=s['venue_cost'], income=s['income'], new_clients=s['new_clients'])) for s in CSF]
    return front(out, lambda r: r['session_id'] == DEF_SESSION)


_PH = {}
def class_attendees_d():
    out = []
    for i, a in enumerate(CAF):
        out.append(nb(dict(attendee_id=a['attendee_id'], session_id=a['session_id'], date=I(a['date']), attendee=a['attendee'], phone=fake_phone(500 + i), client_id=a['client_id'], paid=a['paid'], attended=bool(a['attended']))))
    return front(out, lambda r: r['session_id'] == DEF_SESSION and r['attended'])


def reviews_d():
    out = []
    for r in RVF:
        out.append(nb(dict(review_id=r['review_id'], client_id=r['client_id'], client=r['client'], doula=key('doula', r['doula']), asked_on=I(r['asked_on']),
                           received_on=I(r['received_on']) if r['received_on'] else '', stars=r['stars'], channel=key('channel', r['channel']) if r['channel'] else '')))
    return front(out, lambda r: r.get('received_on') and r.get('stars') == 5 and r['asked_on'] > ago(100))


def team_d():
    return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email']) for t in team]


# ------------------------------------------------------------------ calculated tables: key columns only
def src_d(): return [dict(source=key('source', s)) for s in SOURCES]


def thanks_d():
    rows = [(min(r['date'] for r in _unthanked(n)), n) for n in REF_ORDER if _unthanked(n)]
    rows.sort()
    names = [n for _, n in rows[:26]]
    due = [n for n in names if any(r for r in _unthanked(n) if (T0 - r['date']).days <= 90)]
    if due: names = [due[0]] + [n for n in names if n != due[0]]
    return [dict(referrer=n) for n in names]


def gaps_d():
    silent = [n for n in REF_ORDER if _p12(n) > 0 and _n12(n) == 0]
    down = [n for n in REF_ORDER if _p12(n) >= 4 and 0 < _n12(n) < _p12(n)]
    pick = down[:4] + sorted(silent, key=lambda n: (-_p12(n), n))[:11]
    out = []
    for i, n in enumerate(pick):
        out.append(nb(dict(referrer=n, visited_on=I(T0 - _dt.timedelta(days=20 + 17 * i)) if i % 3 != 2 else '')))
    return out


def class_econ_d(): return front([dict(session_id=s['session_id']) for s in CSF[::-1][:26]], lambda r: CSD[r['session_id']]['new_clients'] > 0 and CSD[r['session_id']]['attended'] > 0)
def ctype_stats_d(): return [_k(dict(klass=key('ctype', t['class']))) for t in class_types]


def _review_state():
    asked = {r['client']: r for r in RVF}
    return asked
def review_due_d():
    asked = _review_state(); rows = []
    for c in CLF:
        if c['attended_on'] == '' or c['status'] == 'Cancelled': continue
        age = (T0 - c['attended_on']).days
        if age > 125: continue
        r = asked.get(c['client'])
        # answered reviews of long-past births are not listed: the list shows what still needs an action
        if r and r['received_on'] != '' and age > 70: continue
        rows.append((c['attended_on'], c['client']))
    rows.sort(reverse=True)
    names = [n for _, n in rows[:34]]
    ask = [n for n in names if n not in asked and (T0 - CLN[n]['attended_on']).days >= 14]
    if ask: names = [ask[0]] + [n for n in names if n != ask[0]]
    return [dict(client=n) for n in names]


def review_month_d(): return [dict(month=I(m)) for m in months24()]


# ------------------------------------------------------------------ defaults for the tools and forms (taken from the demo story)
def _session():
    for s in reversed(CSF):
        if s['attended'] > 0 and s['new_clients'] == 0 and s['signed_up'] >= 8 and s['date'] < T0 - _dt.timedelta(days=3): return s['session_id']
    return CSF[-1]['session_id']
DEF_SESSION = _session()
DEF_REFERRER = 'Birchwood Care Office'
DEF_GAP = [n for n in REF_ORDER if _p12(n) > 0 and _n12(n) == 0][0]
DEF_DECLINE = 'Oakfield Care Office'
