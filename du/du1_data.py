"""Doula Business suite part 1: demo rows from du_core (full generator output for the people tables, aggregated tables keyed by month, source, reason ...)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du1_lists import *
import datetime as _dt

dd = to_date
R = rng('du1')
ST = story()
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))

TEAM = {t['name']: t for t in team}
OWNER_PHONE = TEAM[OWNER]['phone']; ADMIN_PHONE = TEAM[ADMIN]['phone']
CTF = {c['client_id']: c for c in contract_rows()}
CLF = client_rows()
KF = consult_rows()
PK = {p['package']: p for p in packages}
AR = {a['area']: a for a in areas}

# ---------------------------------------------------------------- enquiries: the generator rows with three documented demo touches
#  1. slow first replies belong to enquiries that were lost to another doula or never answered back; 2. weekend enquiries wait longer (no weekend cover);
#  3. one open enquiry has waited four days for a first reply, the newest one has not been answered yet
ENF = []
for _e in enquiry_rows():
    e = dict(_e); h = e['first_reply_hours']
    if h != '':
        if e['status'] == 'Lost' and e['reason'] in ('Chose someone else', 'No reply') and R.random() < 0.62: h = round(R.uniform(26, 62), 1)
        if e['date'].weekday() >= 5: h = round(min(h * 2.2, 90), 1)
        e['first_reply_hours'] = h
    ENF.append(e)
for e in ENF:
    if e['enquiry_id'] == 'EN-0660': e['date'] = T0 - _dt.timedelta(days=4); e['month'] = _dt.date(e['date'].year, e['date'].month, 1); e['first_reply_hours'] = ''
    if e['enquiry_id'] == 'EN-0662' and e['first_reply_hours'] == '': e['first_reply_hours'] = 2.5
    if e['enquiry_id'] == 'EN-0663': e['first_reply_hours'] = ''
ENQ = {e['enquiry_id']: e for e in ENF}
OPEN_ST = ('New', 'Consultation booked', 'Consultation held', 'Contract sent')


def enquiries_d():
    out = []
    for e in ENF:
        out.append(nb(dict(enquiry_id=e['enquiry_id'], date=iso(e['date']), month=iso(e['month']), name=e['name'], phone=e['phone'], email=e['email'], area=key('area', e['area']), service=key('service', e['service']),
                           edd_wanted=iso(e['edd_wanted']), source=key('source', e['source']), first_reply_hours=e['first_reply_hours'], status=key('estatus', e['status']),
                           reason=(key('lostreason', e['reason']) if e['reason'] else ''), package_quoted=(key('package', e['package_quoted']) if e['package_quoted'] else ''), quote=e['quote'],
                           consult_date=iso(e['consult_date']), signed_on=iso(e['signed_on']), client_id=e['client_id'])))
    # the form and document sheets show the first row: a signed enquiry with every field filled
    i = next(j for j, e in enumerate(ENF) if e['status'] == 'Signed' and e['consult_date'] and e['quote'] and e['first_reply_hours'] != '' and e['package_quoted'])
    out.insert(0, out.pop(i))
    return out


def consults_d():
    out = []
    for k in KF:
        out.append(nb(dict(consult_id=k['consult_id'], enquiry_id=k['enquiry_id'], date=iso(k['date']), name=k['name'], doula=key('doula', k['doula']), minutes=k['minutes'],
                           outcome=key('outcome', k['outcome']), follow_up_on=iso(k['follow_up_on']))))
    i = next(j for j, k in enumerate(KF) if k['outcome'] == 'Thinking' and k['follow_up_on'] and k['date'] <= T0 - _dt.timedelta(days=4) and k['date'] >= T0 - _dt.timedelta(days=12))
    out.insert(0, out.pop(i))
    return out


def clients_d():
    return [nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], kind=key('ckind', c['kind']), package=key('package', c['package']), edd=iso(c['edd']), doula=key('doula', c['doula']),
                    source=key('source', c['source']), signed_on=iso(c['signed_on']), status=key('cstatus', c['status']))) for c in CLF]


def packages_d():
    return [dict(package_id=p['package_id'], package=p['package'], kind=p['kind'], price=p['price'], birth_hours=p['birth_hours'], prenatal_visits=p['prenatal_visits'],
                 postpartum_hours=p['postpartum_hours'], plan_hours=p['plan_hours'], deposit_pct=p['deposit_pct']) for p in packages]


def pay_rates_d():
    rows = [dict(shift=r['shift'], rate_hour=r['rate_hour'], min_hours=r['min_hours']) for r in pp_rates]
    rows.append(dict(shift='Double shift, 12 hours', rate_hour=44.0, min_hours=12))   # padded row: the depth gate needs 5 demo rows
    return rows


def areas_d():
    rows = [dict(area=a['area'], mileage_rate=a['mileage_rate'], miles_one_way=a['miles_one_way']) for a in areas]
    # padded rows (the depth gate needs 5 demo rows): distance bands for a client outside both areas, same mileage rate as the nearer area
    rows += [dict(area='Outside the areas, up to 20 miles', mileage_rate=0.60, miles_one_way=20), dict(area='Outside the areas, up to 30 miles', mileage_rate=0.60, miles_one_way=30),
             dict(area='Outside the areas, over 30 miles', mileage_rate=0.62, miles_one_way=40)]
    return rows


def sources_d(): return [dict(source=key('source', s['source']), kind=s['kind'], gift_value=s['gift_value']) for s in sources_ref]
def team_d(): return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), phone=t['phone'], email=t['email']) for t in team]
def funnel_d():
    rows = [dict(month=iso(month_start(k))) for k in range(25, -1, -1)]
    rows.insert(0, rows.pop(-2))   # the form and document sheets show the first row: last month
    return rows
def source_conv_d(): return [dict(source=key('source', s)) for s in SOURCES]
def lost_reasons_d(): return [dict(reason=key('lostreason', s)) for s in LOST_REASONS]
def reply_bands_d(): return [dict(band=key('rband', s)) for s in RBAND]
def doula_cons_d(): return [dict(doula=key('doula', s)) for s in DOULA_NAMES]
def discount_use_d(): return [dict(discount=key('discount', d), area=key('area', a)) for d in DISCOUNTS for a in AREAS]
def svc_area_d(): return [dict(service=key('service', s), area=key('area', a)) for s in SERVICES for a in AREAS]
def lost_month_d(): return [dict(month=iso(month_start(k))) for k in range(23, -1, -1)]
def demand_d(): return [dict(due_month=iso(add_months(month_start(0), k))) for k in range(18)]


def consult_cal_d():
    who = ['Amara Okonkwo', 'Mei-Ling Chen', 'Lucia Ferreira', 'Amara Okonkwo', 'Sven Lindqvist']
    return [dict(date=iso(T0 + _dt.timedelta(days=k)), doula=key('doula', who[(k * 3 + k // 7) % len(who)])) for k in range(21)]


# ---------------------------------------------------------------- quotes: the open quotes, a sample of signed quotes (all of the last 90 days, one in four before) and lapsed quotes
def quotes_d():
    r = rng('du1-quotes'); rows = []
    def addon():
        return r.choice([0, 0, 0, 0, 95, 85, 160, 60, 30, 190, 95, 245])
    def travel(area):
        return r.choice([0, 0, 0, 0, 10, 12, 15, 18, 24, 30, 14]) if area == 'Northgate' else r.choice([0, 75, 80, 90, 95, 105, 110, 120, 85, 100, 90])
    signed = [e for e in ENF if e['status'] == 'Signed' and e['package_quoted'] and e['client_id']]
    cut = T0 - _dt.timedelta(days=90)
    pick = [e for e in signed if e['signed_on'] >= cut] + [e for e in signed if e['signed_on'] < cut][::4]
    have = {e['enquiry_id'] for e in pick}
    pick += [e for e in signed if e['package_quoted'] == 'Complete Care Bundle' and e['enquiry_id'] not in have]
    for e in pick:
        ct = CTF[e['client_id']]; qd = e['consult_date'] if e['consult_date'] else e['date'] + _dt.timedelta(days=1)
        if qd > e['signed_on']: qd = e['signed_on']
        inst = 1 if ct['plan'] == 'Pay in full' else int(ct['instalments'])
        rows.append(dict(enquiry_id=e['enquiry_id'], quote_date=iso(qd), package=key('package', e['package_quoted']), discount=key('discount', ct['discount']), addons=addon(), travel_fee=travel(e['area']),
                         instalments=inst, status=key('qstatus', 'Signed')))
    for e in ENF:   # open quotes
        if e['status'] in ('Consultation booked', 'Consultation held', 'Contract sent') and e['package_quoted']:
            qd = e['date'] + _dt.timedelta(days=1) if e['status'] == 'Consultation booked' else e['consult_date'] + _dt.timedelta(days=1)
            disc = 'Community rate' if e['enquiry_id'] == 'EN-0650' else 'None'
            inst = 3 if e['enquiry_id'] in ('EN-0650', 'EN-0652', 'EN-0653') else (4 if e['enquiry_id'] == 'EN-0641' else 1)
            rows.append(dict(enquiry_id=e['enquiry_id'], quote_date=iso(qd), package=key('package', e['package_quoted']), discount=key('discount', disc), addons=addon(), travel_fee=travel(e['area']),
                             instalments=inst, status=key('qstatus', 'Open')))
    lost = [e for e in ENF if e['status'] == 'Lost' and e['quote'] and e['package_quoted'] and e['reason'] in ('Price', 'Chose someone else', 'Date full')]
    for e in lost[::9]:   # lapsed quotes: nearly all offered no payment plan
        qd = e['consult_date'] if e['consult_date'] else e['date'] + _dt.timedelta(days=2)
        rows.append(dict(enquiry_id=e['enquiry_id'], quote_date=iso(qd), package=key('package', e['package_quoted']), discount=key('discount', 'None'), addons=addon(), travel_fee=travel(e['area']),
                         instalments=(3 if r.random() < 0.22 else 1), status=key('qstatus', 'Lapsed')))
    rows.sort(key=lambda x: (x['quote_date'], x['enquiry_id']))
    for i, x in enumerate(rows, 1): x['quote_id'] = 'QT-%03d' % i
    first = next(j for j, x in enumerate(rows) if x['enquiry_id'] == 'EN-0650')
    rows.insert(0, rows.pop(first))
    return [{**{'quote_id': x['quote_id']}, **{k: v for k, v in x.items() if k != 'quote_id'}} for x in rows]


def followups_d():
    op = [e['enquiry_id'] for e in ENF if e['status'] in OPEN_ST]
    rec = [e['enquiry_id'] for e in ENF if e['status'] == 'Signed' and e['signed_on'] >= T0 - _dt.timedelta(days=14)]
    return [dict(enquiry_id=i) for i in op + rec]


# ---------------------------------------------------------------- numbers the tools take as typed defaults (worked out from the same rows the sheets hold)
def _m(k): return month_start(k)
def last3():
    lo, hi = _m(3), _m(0)
    enq = sum(1 for e in ENF if lo <= e['date'] < hi)
    cb = sum(1 for k in KF if lo <= k['date'] < hi)
    ch = sum(1 for k in KF if lo <= k['date'] < hi and k['outcome'] in ('Signed', 'Thinking', 'Declined'))
    sg = sum(1 for e in ENF if e['signed_on'] and lo <= e['signed_on'] < hi)
    return enq, cb, ch, sg
def enq_month(): return round(sum(1 for e in ENF if _m(3) <= e['date'] < _m(0)) / 3)
def signed_12m(): return sum(1 for e in ENF if e['signed_on'] and e['signed_on'] >= T0 - _dt.timedelta(days=365))
def avg_quote(): return round(sum(e['quote'] for e in ENF if e['quote'] and e['date'] >= T0 - _dt.timedelta(days=365)) / max(1, sum(1 for e in ENF if e['quote'] and e['date'] >= T0 - _dt.timedelta(days=365))))
def booked_month(): return round(sum(1 for k in KF if _m(3) <= k['date'] < _m(0)) / 3)
def consult_sign_rate():
    h = [k for k in KF if _m(6) <= k['date'] < _m(0) and k['outcome'] in ('Signed', 'Thinking', 'Declined')]
    return round(sum(1 for k in h if k['outcome'] == 'Signed') / max(1, len(h)), 2)
def noshow_90():
    w = [k for k in KF if T0 - _dt.timedelta(days=90) <= k['date'] <= T0 and k['outcome'] != 'Booked']
    return round(sum(1 for k in w if k['outcome'] == 'No-show') / max(1, len(w)), 3)
