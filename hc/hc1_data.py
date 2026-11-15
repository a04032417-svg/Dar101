"""Home care agency suite part 1: demo rows built from hc_core (row-level tables from the generators, monthly tables from the full data)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc1_lists import *
import collections, datetime as _dt

dd = to_date
T0 = TODAY
TODAY_ISO = iso(TODAY)
ENQ = enquiry_rows(); CLI = client_rows(); AGR = agreement_rows(); GRO = growth_rows(); CGR = caregiver_rows(); AVL = availability_rows()
ST = story()
NEXT_WEEK = ST['overtime_week']
WEEKH = caregiver_week_hours(NEXT_WEEK)
PH = {s['name']: s['phone'] for s in team}
CLNAME = {c['client_id']: c for c in CLI}
ENQD = {e['enquiry_id']: e for e in ENQ}


def _plan():
    # planned first visits for the agreements still out, and a coming assessment (dates ahead are allowed for planned items)
    k = 0
    for e in ENQ:
        if e['status'] == 'Agreement sent':
            e['first_visit_on'] = ahead(4 + 5 * k); k += 1
            if k == 2: break
    ab = [e for e in ENQ if e['status'] == 'Assessment booked']
    if ab: ab[0]['assessment_on'] = ahead(2)
_plan()


def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def capd(s): return s if s <= TODAY_ISO else TODAY_ISO


# ---------- calls (made first: the enquiry log reads the last contact from them)
def calls_rows():
    out = []
    kinds_out = ['Outbound call', 'Outbound call', 'Text message', 'Email']
    for e in ENQ:
        r = rng('hc1call' + e['enquiry_id']); rec = dd(e['received_on']); st = e['status']
        if st == 'Lost' and e['loss_reason'] == 'No reply': extra = r.choice([2, 2, 3])
        elif st == 'Lost': extra = r.choice([0, 1, 1, 2])
        elif st == 'Started': extra = r.choice([1, 2, 2, 3])
        else: extra = r.choice([0, 1, 1])
        h = e['first_reply_hours']
        rows = []
        d0 = rec + _dt.timedelta(days=int(h) // 24)
        first_out = 'No answer' if (st == 'Lost' and e['loss_reason'] == 'No reply') else r.choice(['Reached', 'Reached', 'Reached', 'Left message'])
        rows.append(dict(date=iso(d0), kind='Inbound call' if r.random() < .3 and first_out == 'Reached' else 'Outbound call', outcome=first_out, minutes=r.randint(4, 22), hours_after=h))
        d = d0
        steps = ['Assessment booked', 'Quote discussed', 'Agreement chased', 'First visit confirmed', 'Reached']
        for k in range(extra):
            d = d + _dt.timedelta(days=r.randint(1, 3))
            if st == 'Lost' and e['loss_reason'] == 'No reply': kind, outc, mins = r.choice(['Outbound call', 'Text message', 'Email']), r.choice(['No answer', 'Left message', 'No answer']), r.randint(1, 4)
            else:
                kind = r.choice(kinds_out + ['Inbound call']); outc = steps[min(k, 3)] if r.random() < .8 else 'Reached'; mins = r.randint(1, 4) if kind in ('Text message', 'Email') else r.randint(4, 25)
            rows.append(dict(date=iso(d), kind=kind, outcome=outc, minutes=mins, hours_after=(d - rec).days * 24 + r.randint(0, 9)))
        for x in rows:
            if x['date'] > TODAY_ISO: continue
            out.append(dict(enquiry_id=e['enquiry_id'], **x))
    # open enquiries: keep the last contact varied (some stale, some not)
    out.sort(key=lambda x: (x['date'], x['enquiry_id'], x['hours_after']))
    for i, x in enumerate(out, 1): x['call_id'] = 'EC-%04d' % i
    return out


CALLS = calls_rows()


def calls_d():
    return [nb(dict(call_id=x['call_id'], enquiry_id=x['enquiry_id'], date=x['date'], kind=x['kind'], outcome=x['outcome'], minutes=x['minutes'], hours_after=x['hours_after'])) for x in CALLS]


# ---------- enquiries
def enquiries_d():
    rows = []
    for i, e in enumerate(ENQ):
        ref = ''; refp = ''
        if e['source'] in ('Discharge planner', 'Local clinic'):
            ref = '%s referral desk' % e['area']; refp = fake_phone(300 + (0 if e['area'] == AREAS[0] else AREAS.index(e['area'])) + (5 if e['source'] == 'Local clinic' else 0))
        rows.append(nb(dict(enquiry_id=e['enquiry_id'], received_on=e['received_on'], name=e['name'], phone=e['phone'], source=key('enqsrc', e['source']), area=key('area', e['area']), service=key('svc', e['service']),
                            hours_week=e['hours_week'], handled_by=e['handled_by'], first_reply_hours=e['first_reply_hours'], status=key('enqst', e['status']),
                            loss_reason=key('loss', e['loss_reason']) if e['loss_reason'] else '', assessor=e['assessor'], assessment_on=e['assessment_on'], agreement_on=e['agreement_on'],
                            first_visit_on=e['first_visit_on'], client_id=e['client_id'], referrer=ref, referrer_phone=refp)))
    # newest first would hide the story: keep oldest first but start with a complete row (started client, replied late, assessor set)
    return rows


# ---------- assessments
LANG_POOL = ['English'] * 6 + ['Spanish', 'Polish', 'Arabic', 'Hindi', 'Portuguese', 'Russian', 'Italian']
def assessments_d():
    rows = []; es = [e for e in ENQ if e['assessment_on']]; es.sort(key=lambda e: (e['assessment_on'], e['enquiry_id']))
    for i, e in enumerate(es, 1):
        r = rng('hc1as' + e['enquiry_id']); h = e['hours_week']
        days = max(1, min(7, int(round(h / r.uniform(3, 5.5)))))
        cl = CLNAME.get(e['client_id']); lang = cl['language'] if cl else r.choice(LANG_POOL)
        st = '21:00' if e['service'] == 'Overnight care' else r.choice(['08:00', '09:00', '09:30', '10:00', '13:00', '16:00', '17:00'])
        if e['assessment_on'] >= TODAY_ISO: outc = 'Visit planned'
        elif e['status'] == 'Lost' and e['loss_reason'] == 'No cover available': outc = 'No caregiver available'
        elif e['status'] == 'Lost' and e['loss_reason'] == 'Needs changed': outc = 'Needs changed'
        elif e['status'] == 'Started' and r.random() < .15: outc = 'Hours changed'
        else: outc = 'Quote sent'
        rows.append(nb(dict(assessment_id='AS-%03d' % i, enquiry_id=e['enquiry_id'], assessment_on=e['assessment_on'], assessor=e['assessor'], service=key('svc', e['service']), hours_week=h,
                            days_week=days, start_time=st, language=lang, area=key('area', e['area']), outcome=outc)))
    return rows


# ---------- quotes
def quote_set():
    es = [e for e in ENQ if e['assessment_on']]
    es += [e for e in ENQ if not e['assessment_on'] and e['status'] == 'Lost' and e['loss_reason'] in ('Price', 'Went elsewhere', 'Timing') and e['quote_weekly']]
    es.sort(key=lambda e: (e['received_on'], e['enquiry_id'])); return es
QS = quote_set()
def quote_status(e):
    if e['status'] == 'Started': return 'Accepted'
    if e['status'] in ('Agreement sent', 'Assessment booked'): return 'Open'
    if e['loss_reason'] in ('Price', 'Went elsewhere'): return 'Declined'
    return 'Expired'
def quote_sent(e):
    base = dd(e['assessment_on']) + _dt.timedelta(days=1) if e['assessment_on'] else dd(e['received_on']) + _dt.timedelta(days=1 + rng('hc1q' + e['enquiry_id']).randint(0, 2))
    return min(base, T0)
def quotes_d():
    rows = []
    for i, e in enumerate(QS, 1):
        rows.append(nb(dict(quote_id='QT-%04d' % i, enquiry_id=e['enquiry_id'], sent_on=iso(quote_sent(e)), service=key('svc', e['service']), hours_week=e['hours_week'],
                            bill_rate=round(e['quote_weekly'] / e['hours_week'], 2), status=key('qst', quote_status(e)))))
    return rows


# ---------- service agreements
def agreements_d():
    rows = []
    for a in AGR:
        rows.append(nb(dict(agreement_id=a['agreement_id'], client_id=a['client_id'], client=a['client'], kind=key('agrk', a['kind']), sent_on=a['sent_on'], signed_on=a['signed_on'], weekly_hours=a['weekly_hours'],
                            bill_rate=a['bill_rate'], min_visit_hours=a['min_visit_hours'], notice_days=a['notice_days'], deposit=a['deposit'], status=key('agrst', a['status']))))
    return rows


# ---------- rate card and rate history
def rate_card_d():
    return [dict(rate_id=r['rate_id'], service=key('svc', r['service']), band=key('band', r['band']), bill_rate=r['bill_rate'], pay_rate=r['pay_rate']) for r in rate_card]


def rate_history_d():
    rows = []; y = TODAY.year; n = 0
    for r in rate_card:
        new1 = r['bill_rate']; old1 = round(new1 / 1.04, 2); new0 = old1; old0 = round(new0 / 1.035, 2)
        rows.append((y - 1, r, old0, new0)); rows.append((y, r, old1, new1))
    rows.sort(key=lambda t: (t[0], t[1]['rate_id']))
    out = []
    for i, (yy, r, o, nw) in enumerate(rows, 1):
        out.append(dict(change_id='RH-%02d' % i, year=yy, effective_on='%d-01-01' % yy, service=key('svc', r['service']), band=key('band', r['band']), old_rate=o, new_rate=nw))
    return out


def holidays_d():
    return [dict(date=h['date'], holiday=h['holiday'], weekday=key('wday', h['weekday']), pay_mult=h['pay_mult'], bill_mult=h['bill_mult']) for h in holidays]


def services_d(): return [dict(service=key('svc', s['service']), min_visit_hours=s['min_visit_hours'], bill_rate=s['bill_rate']) for s in services]
def areas_d(): return [dict(area=key('area', a['area']), zone=key('zone', a['zone']), avg_travel_min=a['avg_travel_min']) for a in areas]
def travel_d(): return [dict(from_area=key('area', a), to_area=key('area', b), minutes=m, km=travel_km(a, b)) for (a, b), m in TRAVEL.items()]
def payers_d(): return [dict(payer=p['payer'], rate_share=p['rate_share'], pay_days=p['pay_days']) for p in payers] + [dict(payer='Private pay, prepaid balance', rate_share=1.0, pay_days=0)]


def clients_d():
    rows = []
    for c in CLI:
        rows.append(nb(dict(client_id=c['client_id'], client=c['client'], area=key('area', c['area']), phone=c['phone'], payer=key('payer', c['payer']),
                            service=key('svc', c['service']), weekly_hours=c['weekly_hours'], bill_rate=c['bill_rate'], min_visit_hours=c['min_visit_hours'], billing_cycle=key('cycle', c['billing_cycle']),
                            language=c['language'], preferred=c['preferred'], preferred_2=c['preferred_2'], source=key('enqsrc', c['source']), start_date=c['start_date'],
                            status=key('clstatus', c['status']), end_date=c['end_date'], deposit=c['deposit'], prepay=yn(c['prepay']))))
    return rows


def starts_d():
    return [dict(month=g['month'], clients_started=g['clients_started'], clients_ended=g['clients_ended'], hours_added=g['hours_added'], hours_lost=g['hours_lost'], active_clients=g['active_clients']) for g in GRO]


def funnel_d(): return [dict(month=iso(month_start(k))) for k in range(23, -1, -1)]


def lost_d():
    rows = []
    for e in ENQ:
        if e['status'] != 'Lost': continue
        r = rng('hc1lost' + e['enquiry_id']); rec = dd(e['received_on'])
        base = dd(e['assessment_on']) if e['assessment_on'] else rec
        lost_on = min(T0, base + _dt.timedelta(days=r.randint(2, 14)))
        last = max(rec, lost_on - _dt.timedelta(days=r.randint(0, 3)))
        rows.append(nb(dict(enquiry_id=e['enquiry_id'], date=iso(lost_on), service=key('svc', e['service']), area=key('area', e['area']), source=key('enqsrc', e['source']),
                            reason=key('loss', e['loss_reason']), quote_weekly=e['quote_weekly'], last_contact=iso(last))))
    rows.sort(key=lambda x: (x['date'], x['enquiry_id']))
    return rows


SRC_COST = {'Family or friend': 20, 'Discharge planner': 110, 'Online directory': 340, 'Agency website': 210, 'Community event': 130, 'Past client': 25, 'Local clinic': 90}


def sources_d():
    cnt = collections.defaultdict(lambda: [0, 0, 0.0])
    for e in ENQ:
        k = (e['received_on'][:7] + '-01', e['source']); cnt[k][0] += 1
        if e['status'] == 'Started': cnt[k][1] += 1; cnt[k][2] += e['hours_week']
    rows = []
    for k in range(23, -1, -1):
        m = iso(month_start(k))
        for s in ENQ_SOURCES:
            n, st, h = cnt.get((m, s), (0, 0, 0.0))
            r = rng('hc1cost%s%s' % (m, s))
            cost = round(SRC_COST[s] * r.uniform(0.7, 1.35) / 5) * 5 if (n or r.random() < .5) else round(SRC_COST[s] * 0.5 / 5) * 5
            rows.append(dict(month=m, source=key('enqsrc', s), enquiries=n, started=st, hours_started=h, cost=cost))
    return rows


def availability_d():
    return [dict(avail_id=a['avail_id'], caregiver_id=a['caregiver_id'], caregiver=a['caregiver'], weekday=key('wday', a['weekday']), from_time=a['from_time'], to_time=a['to_time'], max_hours=a['max_hours']) for a in AVL]


SKILL_COLS = ['sk_companion', 'sk_personal', 'sk_home', 'sk_respite', 'sk_overnight', 'sk_livein']
def capacity_d():
    rows = []; act = [g for g in CGR if g['status'] != 'Left']
    for i, g in enumerate(act, 1):
        sk = [s.strip() for s in g['skills'].split(';')]; lg = [s.strip() for s in g['languages'].split(';')]
        d = dict(no=i, caregiver_id=g['caregiver_id'], caregiver=g['name'], phone=g['phone'], area=key('area', g['area']), employment=key('emp', g['employment']), availability=key('avail', g['availability']),
                 language_1=lg[0], language_2=lg[1] if len(lg) > 1 else '', pay_rate=g['pay_rate'], hours_limit=g['hours_limit'], hours_next_week=WEEKH.get(g['name'], 0.0), working=yn(g['status'] == 'Active'))
        for col, svc in zip(SKILL_COLS, SERVICES): d[col] = yn(svc in sk)
        rows.append(nb(d))
    return rows


def team_d():
    return [dict(staff_id=t['staff_id'], name=t['name'], role=t['role'], team=t['team'], pay_type=t['pay_type'], phone=t['phone'], email=t['email'], hours_week=t['hours_week'], monthly_salary=int(t['monthly_salary']),
                 hourly_rate=int(t['hourly_rate']), speciality=t['speciality'], country=t['country'], start=t['start']) for t in team]
