"""Therapy practice suite part 1: demo rows built from th_core (sampled rows for row-level tables, full data for monthly tables)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th1_lists import *
import collections

R = rng('th1')
dd = to_date
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def samp(rows, field, recent, step):
    cut = ago(recent)
    out = [r for i, r in enumerate(rows) if r[field] >= cut or i % step == 0]
    return out
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows

ENQ = enquiry_rows(); WL = waitlist_rows(); CLI = client_rows(); SES = session_rows(); DEP = deposit_rows(); SLOTS = slot_rows()
REFPH = {r['name']: r['phone'] for r in referrers}
PH = {s['name']: s['phone'] for s in team}
ROLE_NAME = {'Clinician': 'Employed clinician', 'Contract clinician': 'Contract clinician (self-employed)', 'Associate': 'Associate (works under supervision)'}
CAUSE_OF = {'No reply': 'No reply', 'Fees': 'Fee too high', 'Timing': 'No suitable time', 'Not a fit': 'No suitable clinician', 'Service not offered': 'No suitable clinician', 'Waited too long': 'Waited too long'}

# ---------- enquiries
def reply_hours(e):
    r = rng('rep' + e['enquiry_id']); x = r.random()
    h = r.uniform(0.3, 20) if x < .58 else r.uniform(21, 48) if x < .82 else r.uniform(49, 96) if x < .96 else r.uniform(97, 170)
    if e['contact_method'] == 'Walk-in': h = r.uniform(0.2, 2)
    if e['status'] == 'No reply': h *= 2.2
    if e['status'] == 'New': h = r.uniform(1, 6)
    return round(h, 1)
ES = samp(ENQ, 'date', 120, 7)
def enquiries_d():
    rows = [nb(dict(enquiry_id=e['enquiry_id'], date=e['date'], name=e['name'], contact=e['contact'], phone=e['phone'], client_type=key('ctype', e['client_type']), service=key('svc', e['service']),
                    source=key('src', e['source']), referrer=e['referrer'], referrer_phone=REFPH.get(e['referrer'], ''), contact_method=key('cmethod', e['contact_method']), priority=key('prio', e['priority']),
                    reply_hours=reply_hours(e), screening_date=e['screening_date'], screened_by=e['screened_by'], status=key('enqst', e['status']),
                    reason=key('enqr', e['reason']) if e['reason'] else '', clinician=key('clin', e['clinician']) if e['clinician'] else '', first_session=e['first_session'])) for e in ES]
    return front(rows, lambda r: r.get('first_session') and r.get('screening_date') and r.get('referrer') and r['status'] == key('enqst', 'Booked') and r.get('reason') is None)

# ---------- waiting list
def wd_out(w):
    return iso(min(T0 - day(1), dd(w['added_on']) + day(28 + rng('wo' + w['wait_id']).randint(0, 56)))) if w['status'] == 'Withdrawn' else ''
_st = [w for w in WL if w['status'] == 'Started']
WLS = [w for w in WL if w['status'] in ('Waiting', 'Offered', 'Withdrawn')] + [w for i, w in enumerate(_st) if i % 5 == 0 or w['added_on'] >= ago(120)]
WLS.sort(key=lambda w: w['wait_id'])
WLD = {w['wait_id']: w for w in WLS}
def waiting_d():
    rows = [nb(dict(wait_id=w['wait_id'], added_on=w['added_on'], enquiry_id=w['enquiry_id'], name=w['name'], phone=w['phone'], client_type=key('ctype', w['client_type']), service=key('svc', w['service']),
                    priority=key('prio', w['priority']), offered_on=w['offered_on'], started_on=w['started_on'], withdrawn_on=wd_out(w), clinician=key('clin', w['clinician']) if w['clinician'] else '',
                    status=key('waitst', w['status']))) for w in WLS]
    for i, r in enumerate(rows):
        if i % 11 == 3: r['service'] = key('svc', 'Intake assessment')
        elif i % 13 == 5: r['service'] = key('svc', 'Review session')
        if i % 9 == 4 and r['status'] == key('waitst', 'Waiting'): r['priority'] = key('prio', 'High')
    return front(rows, lambda r: r['status'] == key('waitst', 'Waiting') and r['priority'] == key('prio', 'Normal'))

# ---------- screening calls
def nstep(e): return {'Booked': 'Book intake', 'Waiting list': 'Waiting list', 'Referred elsewhere': 'Signpost'}.get(e['status'], 'Close enquiry')
def screening_d():
    es = [e for e in ENQ if e['screening_date'] and e['screening_date'] <= iso(T0) and e['status'] not in ('Screening booked', 'New')]
    es = samp(es, 'screening_date', 45, 5); es.sort(key=lambda e: (e['screening_date'], e['enquiry_id']))
    out = []
    for i, e in enumerate(es, 1):
        r = rng('sc' + e['enquiry_id']); ns = nstep(e)
        out.append(nb(dict(call_id='SC-%04d' % i, date=e['screening_date'], enquiry_id=e['enquiry_id'], enquired_on=e['date'], name=e['name'], phone=e['phone'], screened_by=e['screened_by'] or COORDINATOR,
                           minutes=r.randint(14, 38), suitable=yn(ns in ('Book intake', 'Waiting list')), urgency=key('prio', e['priority']), next_step=key('nextstep', ns))))
    return front(out, lambda r: True)

# ---------- call-backs
def callbacks_d():
    out = []
    noreply = samp([e for e in ENQ if e['status'] == 'No reply'], 'date', 20, 2)
    other = [e for i, e in enumerate(ENQ) if e['status'] in ('Booked', 'Waiting list', 'Declined') and i % 9 == 0 and e['date'] >= ago(200)]
    for e in noreply + other:
        r = rng('cb' + e['enquiry_id']); nr = e['status'] == 'No reply'; n = r.choice([2, 3, 3]) if nr else 2
        d0 = dd(e['date'])
        for k in range(1, n + 1):
            dt_ = d0 + day(1 + 2 * (k - 1)) if k > 1 else d0 + day(1)
            if dt_ > T0: break
            last = k == n; reached = (not nr) and last
            nxt = '' if (reached or (last and k >= 3)) else iso(dt_ + day(2))
            out.append(dict(date=iso(dt_), enquiry_id=e['enquiry_id'], name=e['name'], phone=e['phone'], attempt=k, method=r.choice(['Phone', 'Phone', 'Text message', 'Email']), reached=yn(reached), next_try=nxt))
    out.sort(key=lambda x: (x['date'], x['enquiry_id']))
    out = [x for i, x in enumerate(out) if x['date'] >= ago(20) or i % 2 == 0]
    for i, x in enumerate(out, 1): x['callback_id'] = 'CB-%04d' % i
    rows = [nb(dict(callback_id=x['callback_id'], **{k: v for k, v in x.items() if k != 'callback_id'})) for x in out]
    return front(rows, lambda r: r.get('next_try') and r['reached'] == 'no')

# ---------- offers
def offers_d():
    out = []
    for w in WLS:
        if not w['offered_on']: continue
        r = rng('of' + w['wait_id']); acc = w['status'] == 'Started'
        wd = dd(w['started_on']).weekday() if w['started_on'] else r.randint(0, 5)
        wd = wd if wd <= 5 else 5
        ans = 'Accepted' if acc else 'Waiting'; ansd = iso(min(T0, dd(w['offered_on']) + day(r.randint(0, 3)))) if acc else ''
        out.append(dict(offered_on=w['offered_on'], wait_id=w['wait_id'], clinician=w['clinician'], weekday=WORKDAYS[wd], time='%02d:00' % r.choice([9, 10, 11, 13, 14, 15, 16, 17, 18]), answer=ans, answered_on=ansd))
        if acc and r.random() < .26:
            od = iso(dd(w['offered_on']) - day(r.randint(6, 14))); a2 = r.choice(['Declined', 'Declined', 'No reply'])
            out.append(dict(offered_on=od, wait_id=w['wait_id'], clinician=w['clinician'], weekday=WORKDAYS[r.randint(0, 5)], time='%02d:00' % r.choice([9, 10, 13, 16, 17, 19]),
                            answer=a2, answered_on=iso(dd(od) + day(r.randint(1, 4))) if a2 == 'Declined' else ''))
    out.sort(key=lambda x: (x['offered_on'], x['wait_id']))
    for i, x in enumerate(out, 1): x['offer_id'] = 'OF-%03d' % i
    rows = [nb(dict(offer_id=x['offer_id'], offered_on=x['offered_on'], wait_id=x['wait_id'], clinician=key('clin', x['clinician']), weekday=key('wday', x['weekday']), time=x['time'],
                    answer=key('answer', x['answer']), answered_on=x['answered_on'])) for x in out]
    return front(rows, lambda r: r['answer'] == key('answer', 'Accepted') and r.get('answered_on') and r['answered_on'] > r['offered_on'])

# ---------- check-ins
def checkins_d():
    out = []
    for w in WLS:
        r = rng('ci' + w['wait_id'])
        if w['status'] == 'Waiting': ds = [dd(w['added_on']) + day(28 * k) for k in (1, 2, 3) if dd(w['added_on']) + day(28 * k) <= T0]; fin = 'Waiting'
        elif w['status'] == 'Withdrawn': ds = [dd(w['added_on']) + day(28 * k) for k in (1, 2) if dd(w['added_on']) + day(28 * k) <= dd(wd_out(w))] or [dd(wd_out(w)) - day(2)]; fin = r.choice(['Declined', 'Declined', 'No reply'])
        else: continue
        for j, d in enumerate(ds):
            a = fin if j == len(ds) - 1 else 'Waiting'
            out.append(dict(date=iso(d), wait_id=w['wait_id'], contacted_by=COORDINATOR if r.random() < .8 else OWNER, answer=a))
    out.sort(key=lambda x: (x['date'], x['wait_id']))
    for i, x in enumerate(out, 1): x['checkin_id'] = 'CI-%03d' % i
    rows = [dict(checkin_id=x['checkin_id'], date=x['date'], wait_id=x['wait_id'], contacted_by=x['contacted_by'], answer=key('answer', x['answer']), still_waiting=yn(x['answer'] == 'Waiting')) for x in out]
    return front(rows, lambda r: True)

# ---------- lost enquiries
def lost_d():
    es = [e for e in ENQ if e['status'] in ('Declined', 'No reply')]
    es = samp(es, 'date', 150, 3); out = []
    for e in es:
        r = rng('ls' + e['enquiry_id']); rs = e['reason']
        cause = CAUSE_OF.get(rs) or r.choice(['No suitable time', 'No suitable clinician'])
        lc = min(T0, dd(e['date']) + day(r.randint(0, 14)))
        rc = iso(lc + day(r.randint(55, 120))) if (cause in ('No suitable time', 'Waited too long') or (cause == 'Fee too high' and r.random() < .4)) else ''
        out.append(nb(dict(enquiry_id=e['enquiry_id'], date=e['date'], name=e['name'], phone=e['phone'], service=key('svc', e['service']), client_type=key('ctype', e['client_type']),
                           cause=key('cause', cause), last_contact=iso(lc), recontact_date=rc)))
    return front(out, lambda r: r.get('recontact_date'))

# ---------- signposting
SIGN_TO = {'Individual session': 'Another practice', 'Extended individual': 'Another practice', 'Couples session': 'Community service', 'Family session': 'Community service', 'Child session': 'Specialist service',
           'Speech therapy': 'Specialist service', 'Behaviour therapy': 'Specialist service', 'Review session': 'Family doctor', 'Intake assessment': 'Another practice'}
def signpost_d():
    es = samp([e for e in ENQ if e['status'] == 'Referred elsewhere'], 'date', 150, 2); out = []
    for i, e in enumerate(es, 1):
        r = rng('sg' + e['enquiry_id']); gap = r.choice([0, 1, 1, 2, 3, 5, 8, 11])
        to = SIGN_TO[e['service']] if r.random() < .7 else r.choice(REFERRED_TO)
        d = min(T0, dd(e['date']) + day(gap))
        out.append(dict(signpost_id='SP-%03d' % i, enquiry_id=e['enquiry_id'], enquired_on=e['date'], date=iso(d), name=e['name'], phone=e['phone'], service=key('svc', e['service']), referred_to=to,
                        reason=r.choice(['Not a fit', 'Service not offered', 'Service not offered', 'Timing', 'Fees', 'Not a fit']), info_sent=yn(r.random() < .9)))
    return front(out, lambda r: True)

# ---------- new clients, intake sessions, paperwork, deposits
CS = samp(CLI, 'booked_on', 150, 3); CSD = {c['client_id']: c for c in CS}; CSN = {c['client'] for c in CS}
_first = {}
for s in SES:
    if s['client_id'] in CSD and s['status'] != 'Cancelled':
        k = s['client_id']
        if k not in _first or s['date'] < _first[k]['date']: _first[k] = s
DEPC = {d['client_id'] for d in DEP}
def clients_d():
    rows = []
    for c in CS:
        f = _first.get(c['client_id'], {})
        rows.append(nb(dict(client_id=c['client_id'], client=c['client'], client_type=key('ctype', c['client_type']), contact=c['contact'], phone=c['phone'], service=key('svc', c['service']),
                            clinician=key('clin', c['clinician']), booked_on=c['booked_on'], first_session=c['first_session'], first_time=f.get('time', ''), room=f.get('room', ''), format=key('fmt', c['format']),
                            fee_type=key('feetype', c['fee_type']), frequency=c['frequency'], payer=c['payer'], sliding_pct=c['sliding_pct'], sessions_attended=c['sessions_attended'])))
    return front(rows, lambda r: r.get('first_time') and r.get('first_session') <= iso(T0) and r['fee_type'] == key('feetype', 'Sliding scale') and r['client_id'] in DEPC)

def intake_d():
    I = [s for s in SES if s['service'] == 'Intake assessment' and s['client_id'] in CSD]
    rows = [nb(dict(session_id=s['session_id'], date=s['date'], client_id=s['client_id'], client=s['client'], clinician=key('clin', s['clinician']), format=key('fmt', s['format']), room=s['room'],
                    status=key('sstatus', s['status']), fee_waived=yn(s['fee_waived'] in ('Yes', True)))) for s in I]
    return front(rows, lambda r: r['status'] == key('sstatus', 'Attended'))

def paperwork_d():
    out = []
    for c in CS:
        r = rng('pw' + c['client_id']); b = dd(c['booked_on']); fs = dd(c['first_session']); sent = min(T0, b + day(r.randint(0, 1)))
        x = r.random(); back = ''
        if fs <= T0:
            back = iso(max(sent, fs - day(r.randint(1, 6)))) if x < .88 else iso(min(T0, fs + day(r.randint(0, 3)))) if x < .95 else ''
        else:
            back = iso(min(T0, sent + day(r.randint(0, 5)))) if x < .55 else ''
        out.append(nb(dict(client_id=c['client_id'], forms_sent_on=iso(sent), forms_back_on=back, consent_back=yn(bool(back) and r.random() < .96), details_checked=yn(bool(back) and r.random() < .93))))
    return front(out, lambda r: r.get('forms_back_on'))

def deposits_d():
    rows = [nb(dict(deposit_id=d['deposit_id'], date=d['date'], client_id=d['client_id'], client=d['client'], amount=int(d['amount']), applied_on=d['applied_on'], status=key('depst', d['status'])))
            for d in DEP if d['client_id'] in CSD]
    return front(rows, lambda r: r['status'] == key('depst', 'Applied') and r.get('applied_on'))

# ---------- diary and capacity
def slots_d():
    lim = iso(T0 + day(28)); out = []
    for x in SLOTS:
        if x['status'] == 'Free' and iso(T0) < x['date'] <= lim:
            r = rng('sl' + x['slot_id']).random()
            out.append(dict(slot_id=x['slot_id'], week=x['week'], date=x['date'], weekday=key('wday', x['weekday']), time=x['time'], clinician=key('clin', x['clinician']),
                            status=key('slothold', 'Urgent hold' if r < .14 else 'Intake hold' if r < .40 else 'Open')))
    return out

def capacity_d():
    ws0 = week_start(T0); out = []; i = 0
    I = [s for s in SES if s['service'] == 'Intake assessment' and s['status'] in ('Scheduled', 'Attended')]
    for k in range(6):
        w = ws0 + day(7 * k)
        for nm in CLINICIANS:
            i += 1
            free = sum(1 for x in SLOTS if x['week'] == iso(w) and x['clinician'] == nm and x['status'] == 'Free')
            bk = sum(1 for s in I if s['week'] == iso(w) and s['clinician'] == nm)
            out.append(dict(row_id='IC-%02d' % i, week=iso(w), clinician=key('clin', nm), free_slots=free, intakes_booked=bk))
    return out

def match_d():
    return [dict(no=i + 1, rule_id=m['rule_id'], service=key('svc', m['service']), client_type=key('ctype', m['client_type']), clinician=key('clin', m['clinician']), preference=m['preference'], takes_new=yn(m['takes_new'] == 'Yes'))
            for i, m in enumerate(skill_rows())]

TARGET = {'High': {'Adult': 7, 'Couple': 10, 'Family': 10, 'Child': 5, 'Young person': 5}, 'Normal': {'Adult': 14, 'Couple': 14, 'Family': 14, 'Child': 10, 'Young person': 10},
          'Low': {'Adult': 28, 'Couple': 28, 'Family': 28, 'Child': 21, 'Young person': 21}}
def targets_d():
    return [dict(client_type=key('ctype', t), priority=key('prio', p), target_days=TARGET[p][t]) for p in PRIORITIES for t in CLIENT_TYPES]

# ---------- monthly tables
MONTHS = [month_start(k) for k in range(23, -1, -1)]
def eom(d): return add_months(d, 1) - day(1)
def funnel_d():
    out = []
    for m in MONTHS:
        e = eom(m); ms = iso(m); es = iso(e)
        inm = [x for x in ENQ if ms <= x['date'] <= es]
        wait_end = sum(1 for w in WL if w['added_on'] <= es and not (w['offered_on'] and w['offered_on'] <= es) and not (w['started_on'] and w['started_on'] <= es)
                       and not (w['status'] == 'Withdrawn' and wd_out(w) <= es))
        out.append(dict(month=ms, enquiries=len(inm), screened=sum(1 for x in inm if x['screening_date'] and x['screening_date'] <= iso(T0) and x['status'] != 'New'),
                        booked=sum(1 for x in inm if x['status'] == 'Booked'), started=sum(1 for x in inm if x['status'] == 'Booked' and x['first_session'] and x['first_session'] <= iso(T0)),
                        waiting_end=wait_end, withdrawn=sum(1 for w in WL if w['status'] == 'Withdrawn' and ms <= w['added_on'] <= es)))
    return out

def demand_d():
    out = []; i = 0
    for m in MONTHS:
        ms = iso(m); es = iso(eom(m))
        for sv in SESSION_SERVICES:
            i += 1
            inm = [x for x in ENQ if ms <= x['date'] <= es and x['service'] == sv]
            out.append(dict(row_id='SM-%03d' % i, month=ms, service=key('svc', sv), enquiries=len(inm), booked=sum(1 for x in inm if x['status'] == 'Booked'),
                            still_waiting=sum(1 for w in WL if ms <= w['added_on'] <= es and w['service'] == sv and w['status'] == 'Waiting')))
    return out

def services_d():
    return [dict(service=s['service'], minutes=s['minutes'], fee=s['fee']) for s in services]

def team_d():
    return [nb(dict(staff_id=s['staff_id'], name=s['name'], role=ROLE_NAME.get(s['role'], s['role']), team=s['team'], pay_type=s['pay_type'], phone=s['phone'], email=s['email'], hours_week=s['hours_week'],
                    monthly_salary=s['monthly_salary'], split_pct=s['split_pct'], session_rate=s['session_rate'], hourly_rate=s['hourly_rate'], session_cap=s['session_cap'], session_target=s['session_target'],
                    speciality=s['speciality'], country=s['country'], start=s['start'])) for s in team]
if __name__ == '__main__':
    for f in (enquiries_d, waiting_d, screening_d, callbacks_d, offers_d, checkins_d, lost_d, signpost_d, clients_d, intake_d, paperwork_d, deposits_d, slots_d, capacity_d, match_d, targets_d, funnel_d, demand_d):
        print(f.__name__, len(f()))
