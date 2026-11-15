"""Doula suite part 4: demo rows from du_core (full generator output for the window, client, rota, time-off and birth tables; the calculated tables only list their inputs)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du4_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def I(d): return iso(d) if hasattr(d, 'isoformat') else d

CL = client_rows(); CLD = {c['client_id']: c for c in CL}
OW = oncall_rows(); BI = birth_rows(); RT = rota_rows(); TO = timeoff_rows(); EN = enquiry_rows()
PKG = {p['package']: p for p in packages}
DOU = {d['doula']: d for d in doulas}
TEAM = {t['name']: t for t in team}
OWNER_PHONE = TEAM[OWNER]['phone']; ADMIN_PHONE = TEAM[ADMIN]['phone']
ACC_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
MS0 = month_start(0)


def mo(k): return I(add_months(MS0, k))


def clients_d():
    return [nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], area=key('area', c['area']), kind=key('ckind', c['kind']), package=key('package', c['package']), edd=I(c['edd']),
                    due_month=I(c['due_month']), doula=key('doula', c['doula']), backup=(key('backup', c['backup']) if c['backup'] else ''), source=key('source', c['source']),
                    status=key('cstatus', c['status']))) for c in CL]


def oncall_d():
    return [nb(dict(window_id=w['window_id'], client_id=w['client_id'], client=w['client'], doula=key('bdoula', w['doula']), backup=(key('backup', w['backup']) if w['backup'] else ''), edd=I(w['edd']),
                    oncall_start=I(w['oncall_start']), oncall_end=I(w['oncall_end']), area=key('area', w['area']), attended_on=I(w['attended_on']),
                    contact_hours=w['contact_hours'])) for w in OW]


def doulas_d(): return [dict(doula=key('doula', d['doula']), service=key('service', d['service']), cap_births=d['cap_births']) for d in doulas]


def rota_d(): return [dict(rota_id=r['rota_id'], week=I(r['week']), backup=key('backup', r['backup']), stipend=int(r['stipend'])) for r in RT]


def timeoff_d(): return [dict(timeoff_id=t['timeoff_id'], holder=key('holder', t['holder']), start=I(t['start']), end=I(t['end']), kind=key('toff', t['kind'])) for t in TO]


def births_d():
    out = []
    for b in BI:
        out.append(nb(dict(birth_id=b['birth_id'], date=I(b['date']), client_id=b['client_id'], client=b['client'], doula=key('holder', b['doula']), assigned=key('bdoula', b['assigned']),
                           backup=(key('backup', b['doula']) if b['backup_used'] else ''), backup_used=bool(b['backup_used']), hours=b['hours'])))
    return out


def team_d(): return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email']) for t in team]


def daily_d(): return [dict(day_no=k) for k in range(-10, 180)]
def weekly_d(): return [dict(week_no=k) for k in range(-4, 26)]
def capm_d(): return [dict(month=mo(k)) for k in range(12)]
def capd_d(): return [dict(row_id='CD-%03d' % (i * 12 + k + 1), doula=key('doula', d['doula']), month=mo(k)) for i, d in enumerate(doulas) for k in range(12)]
def busy_d(): return [dict(rank=k) for k in range(1, 13)]
def scn_d(): return [dict(month=mo(k)) for k in range(-5, 7)]
def named_d(): return [dict(month=mo(k)) for k in range(-5, 7)]


def cover_d():
    ws = sorted([w for w in OW if w['oncall_end'] >= T0], key=lambda w: (w['oncall_start'], w['window_id']))[:60]
    return [dict(window_id=w['window_id']) for w in ws]


def bload_d():
    out = []
    for k in range(13):
        for j, b in enumerate(BACKUP_NAMES): out.append(dict(row_id='BL-%02d' % (k * 2 + j + 1), backup=key('backup', b), week_no=k))
    return out


def requests_d():
    rows = EN[-16:]
    out = []
    for e in rows:
        out.append(nb(dict(enquiry_id=e['enquiry_id'], date=I(e['date']), name=e['name'], phone=e['phone'], service=key('service', e['service']), area=key('area', e['area']),
                           edd_wanted=I(e['edd_wanted']), source=key('source', e['source']), answered=(e['first_reply_hours'] != ''))))
    return out


def clash_d():
    rows = sorted(TO, key=lambda t: (t['start'], t['timeoff_id']))[-20:]
    return [dict(timeoff_id=t['timeoff_id']) for t in rows]


def rules_d():
    return [dict(rule='Weekly stipend', basis=key('rbasis', 'Per week on the rota'), amount=BACKUP_STIPEND_WEEK), dict(rule='Flat call-out', basis=key('rbasis', 'Per birth attended'), amount=BACKUP_FLAT_PAY),
            dict(rule='Share of the birth part', basis=key('rbasis', 'Share of the birth part'), amount=0.25), dict(rule='Hourly rate', basis=key('rbasis', 'Per hour attended'), amount=28),
            dict(rule='Missed call-out', basis=key('rbasis', 'Paid when the backup attends'), amount=0)]


def callouts_d():
    used = [b for b in BI if b['backup_used']]
    other = [b for b in BI if not b['backup_used']][-4:]
    out = []
    for b in used + other:
        c = CLD[b['client_id']]
        out.append(dict(birth_id=b['birth_id'], birth_value=PKG[c['package']]['birth_value'], agency_share=DOU[b['assigned']]['agency_share']))
    return out


# tool defaults taken from the story and the demo rows
OV_MONTH = ST['overlap_month']; OV_DOULA = ST['overlap_doula']
OV_EDD = I(dd(OV_MONTH) + _dt.timedelta(days=11))
NO_BACKUP = sorted([w for w in OW if not w['backup'] and w['oncall_end'] >= T0], key=lambda w: w['oncall_start'])
NB_START = I(NO_BACKUP[0]['oncall_start']) if NO_BACKUP else ahead(60)
_req_open = [e for e in EN[-16:] if e['first_reply_hours'] == '' and e['service'] != 'Postpartum']
_best = None
for e in _req_open:
    for w in OW:
        if w['oncall_start'] > T0 and w['doula']:
            gap = abs((w['edd'] - e['edd_wanted']).days)
            if _best is None or gap < _best[0]: _best = (gap, w['client'], e['name'])
FREED_CLIENT = _best[1]; FREED_GAP = _best[0]

TO_START = I(dd(OV_EDD) - _dt.timedelta(days=3))
# a doula with due dates close together in the next 12 months (gap 10 days)
def _b2b():
    best = None
    for dn in BDOULAS:
        e = sorted(w['edd'] for w in OW if w['doula'] == dn and T0 <= w['edd'] <= T0 + _dt.timedelta(days=365))
        n = sum(1 for i, x in enumerate(e) if any(abs((x - y).days) <= 10 for j, y in enumerate(e) if j != i))
        if best is None or n > best[0]: best = (n, dn)
    return best
B2B = _b2b(); B2B_DOULA = B2B[1]
