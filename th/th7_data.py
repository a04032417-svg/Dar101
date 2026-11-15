"""Therapy practice suite part 7: demo rows built from th_core (sampled rows for row-level tables, full data for monthly tables)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th7_lists import *
import collections

dd = to_date
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows
def eom(d): return add_months(d, 1) - day(1)
MONTHS = [month_start(k) for k in range(23, -1, -1)]

ENQ = enquiry_rows(); CLI = client_rows(); SES = session_rows(); GRP = group_rows(); GSU = group_signup_rows(); MK = marketing_rows()
for _i, _g in enumerate(GRP): _g['room'] = ROOM_NAMES[(_i * 3 + 1) % 5]
for _m in MK:
    if _m['kind'] == 'Online directory': _m['cost'] = _m['cost'] + rng('dlc' + _m['campaign_id']).randint(-11, 17)
CSRC = {c['client_id']: c['referral_source'] for c in CLI}
RKIND = {r['name']: r['kind'] for r in referrers}
PH = {s['name']: s['phone'] for s in team}
REFPH = {r['name']: r['phone'] for r in referrers}
TODAY_S = iso(T0)
ATT_N = collections.Counter(); ATT_R = collections.defaultdict(float); REV_SM = collections.defaultdict(float)
for s in SES:
    if s['status'] == 'Attended' and s['date'] <= TODAY_S:
        ATT_N[s['client_id']] += 1; ATT_R[s['client_id']] += s['charge']; REV_SM[(s['month'], CSRC.get(s['client_id'], ''))] += s['charge']

# ---------- enquiries by source (thinned sample)
ES = [e for i, e in enumerate(ENQ) if e['date'] >= ago(90) or i % 6 == 0]
def enquiries_d():
    rows = [nb(dict(enquiry_id=e['enquiry_id'], date=e['date'], source=key('src', e['source']), referrer=e['referrer'], service=key('svc', e['service']), client_type=key('ctype', e['client_type']),
                    status=key('enqst', e['status']), first_session=e['first_session'])) for e in ES]
    return front(rows, lambda r: r.get('first_session') and r.get('referrer') and r['status'] == key('enqst', 'Booked'))

# ---------- source performance by month (all enquiries)
def sourcemonths_d():
    out = []; i = 0
    cnt = collections.Counter((e['date'][:7], e['source']) for e in ENQ)
    bk = collections.Counter((e['date'][:7], e['source']) for e in ENQ if e['status'] == 'Booked')
    for m in MONTHS:
        ms = iso(m)
        for sname in REFERRAL_SOURCES:
            i += 1
            out.append(dict(row_id='SO-%03d' % i, month=ms, source=key('src', sname), enquiries=cnt[(ms[:7], sname)], booked=bk[(ms[:7], sname)], revenue=int(round(REV_SM[(ms, sname)]))))
    return out

# ---------- client value by source (every third client with attended sessions)
CV = [c for c in CLI if ATT_N[c['client_id']] > 0][::3]
def clientvalue_d():
    rows = [nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], source=key('src', c['referral_source']), referrer=c['referrer'], first_session=c['first_session'],
                    sessions_attended=ATT_N[c['client_id']], revenue=int(round(ATT_R[c['client_id']])))) for c in CV]
    return front(rows, lambda r: r.get('referrer') and r['sessions_attended'] >= 12)

# ---------- referrers, referral log, contacts
def referrers_d():
    return [dict(referrer_id=r['referrer_id'], name=r['name'], kind=key('rkind', r['kind']), phone=r['phone'], email=r['email']) for r in referrers]

RL = [e for e in ENQ if e['referrer']]
RL = [e for i, e in enumerate(RL) if e['date'] >= ago(365) or i % 3 == 0]
def referrallog_d():
    rows = [nb(dict(log_id='RL-%04d' % i, date=e['date'], referrer=e['referrer'], kind=key('rkind', RKIND[e['referrer']]), service=key('svc', e['service']), client_type=key('ctype', e['client_type']),
                    outcome=key('enqst', e['status']), first_session=e['first_session'])) for i, e in enumerate(RL, 1)]
    return front(rows, lambda r: r.get('first_session') and r['outcome'] == key('enqst', 'Booked'))

OVERDUE = {2, 9, 12, 15, 18, 20, 22}
def contacts_d():
    cnt = collections.Counter(e['referrer'] for e in ENQ if e['referrer'] and e['date'] >= ago(365))
    order = [n for n, _ in cnt.most_common()] + [r['name'] for r in referrers if r['name'] not in cnt]
    rows = []
    for idx, name in enumerate(order):
        r = rng('rc' + name)
        n = 4 if idx < 6 else 3 if idx < 14 else 2 if idx < 20 else 1
        last_gap = r.randint(95, 190) if idx in OVERDUE else r.randint(8, 80)
        ds = [last_gap]
        for k in range(1, n): ds.append(ds[-1] + r.randint(55, 110))
        for k, g in enumerate(ds):
            last = k == 0
            kind = r.choice(CKIND[:3]) if not last else r.choice(['Visit', 'Phone call', 'Thank-you note', 'Email'])
            if k == n - 1 and n > 1 and g > 300: kind = 'Information pack'
            nxt = iso(T0 - day(g) + day(90 + r.randint(-10, 15))) if last else ''
            rows.append(dict(date=iso(T0 - day(g)), referrer=name, contact_kind=key('ckind', kind), done_by=r.choice(['Amira Lindqvist', 'Amira Lindqvist', 'Grace Mensah', 'Daniel Okoye']), next_contact=nxt))
    rows.sort(key=lambda x: (x['date'], x['referrer']))
    for i, x in enumerate(rows, 1): x['contact_id'] = 'RC-%03d' % i
    rows = [nb(dict(contact_id=x['contact_id'], **{k: v for k, v in x.items() if k != 'contact_id'})) for x in rows]
    return front(rows, lambda r: r.get('next_contact') and r['next_contact'] > TODAY_S)

# ---------- campaigns, budget, directory, website
def campaigns_d():
    rows = [dict(campaign_id=m['campaign_id'], date=m['date'], kind=key('mkind', m['kind']), description=m['description'], cost=int(m['cost']), enquiries=m['enquiries'], clients_won=m['clients_won']) for m in MK]
    return front(rows, lambda r: r['cost'] > 0 and r['enquiries'] > 0 and r['clients_won'] > 0)

def budget_d():
    spent = collections.defaultdict(float)
    for m in MK: spent[m['date'][:7]] += m['cost']
    out = []
    for i, m in enumerate(MONTHS, 1):
        r = rng('bud' + iso(m)); s = spent[iso(m)[:7]]
        b = max(200, int(round(s * r.uniform(0.82, 1.55) / 25.0)) * 25)
        if m == MONTHS[-1]: b = max(b, int(s) + 75)
        out.append(dict(row_id='MB-%02d' % i, month=iso(m), budget=b))
    return out

def directory_d():
    rows = []
    for i, m in enumerate([x for x in MK if x['kind'] == 'Online directory'], 1):
        r = rng('dl' + m['campaign_id'])
        rows.append(dict(dl_id='DL-%02d' % i, month=iso(month_start_of(m['date'])), listing=key('listing', m['description']), cost=int(m['cost']),
                         profile_views=int(m['enquiries'] * r.randint(9, 19) + r.randint(20, 90)), enquiries=m['enquiries'], clients_won=m['clients_won']))
    rows.sort(key=lambda x: (x['month'], x['listing']))
    for i, x in enumerate(rows, 1): x['dl_id'] = 'DL-%02d' % i
    return front(rows, lambda r: r['clients_won'] >= 2)
def month_start_of(s):
    d = dd(s); return d.replace(day=1)

def website_d():
    cnt = collections.Counter((e['date'][:7]) for e in ENQ if e['source'] == 'Practice website')
    bk = collections.Counter((e['date'][:7]) for e in ENQ if e['source'] == 'Practice website' and e['status'] == 'Booked')
    out = []
    for i, m in enumerate(MONTHS, 1):
        r = rng('web' + iso(m)); ms = iso(m)[:7]; f = cnt[ms]
        share = 0.021 + 0.0006 * i + r.uniform(-0.003, 0.003)
        out.append(dict(row_id='WM-%02d' % i, month=iso(m), visits=int(round(f / share)), enquiry_forms=f, bookings=bk[ms]))
    return out

# ---------- workshops, newsletter
WK_AUD = {'Workshop': ['Employees of a local company', 'Members of the public', 'Parents and carers', 'Team leaders'], 'Community talk': ['Community centre members', 'Members of the public', 'Local volunteers'],
          'School talk': ['Parents at a local school', 'School staff', 'Parents and carers']}
WK_CONTACT = {'Workshop': 'Employer contact', 'Community talk': 'Community worker', 'School talk': 'School staff'}
def workshops_d():
    ws = [m for m in MK if m['kind'] in WK_AUD]
    ws.sort(key=lambda m: (m['date'], m['campaign_id'])); out = []
    for i, m in enumerate(ws, 1):
        r = rng('wk' + m['campaign_id']); k = m['kind']
        att = r.randint(12, 26) if k == 'Workshop' else r.randint(18, 38) if k == 'Community talk' else r.randint(22, 55)
        pool = [x['name'] for x in referrers if x['kind'] == WK_CONTACT[k]]
        out.append(dict(workshop_id='WK-%02d' % i, date=m['date'], kind=key('mkind', k), title=m['description'], audience=r.choice(WK_AUD[k]), attendees=att, cost=int(m['cost']), enquiries=m['enquiries'], contact=r.choice(pool)))
    return front(out, lambda r: r['enquiries'] > 0 and r['cost'] > 0)

TOPICS = ['New group programs this season', 'How to book and cancel a session', 'Meet the team', 'Opening hours over the holidays', 'A free talk for parents next month', 'Our fees and sliding scale',
          'How online sessions work', 'Our referrer information pack', 'Room and waiting area update', 'Group programs: places left', 'A thank-you to everyone who referred a friend']
def newsletter_d():
    nl = sorted([m for m in MK if m['kind'] == 'Newsletter'], key=lambda m: m['date']); out = []
    for i, m in enumerate(nl, 1):
        r = rng('nl' + m['campaign_id']); sent = 380 + int(i * 6.5) + r.randint(-8, 8)
        out.append(dict(issue_id='NL-%02d' % i, date=m['date'], topic=TOPICS[(i * 3) % len(TOPICS)], sent_to=sent, replies=int(round(sent * r.uniform(0.02, 0.07))), enquiries=m['enquiries']))
    return front(out, lambda r: r['enquiries'] > 0)

# ---------- feedback survey
TOPIC_MEAN = {'Booking': 8.7, 'Waiting time': 7.4, 'Clinician': 9.1, 'Room': 8.4, 'Fees': 8.0, 'Online session': 8.3}
def feedback_d():
    r = rng('fb'); out = []
    for i in range(150):
        off = int(420 * (r.betavariate(1, 1.45)))
        d = T0 - day(off)
        topic = r.choice(FBTOPIC); mean = TOPIC_MEAN[topic] + 0.45 * (1 - off / 420.0) - 0.25
        rating = int(max(3, min(10, round(r.gauss(mean, 1.25)))))
        rec = r.random() < min(0.98, max(0.05, (rating - 4) / 5.2))
        out.append(dict(date=iso(d), client_type=key('ctype', r.choice(['Adult'] * 5 + ['Couple', 'Family', 'Child', 'Child', 'Young person'])), service=key('svc', r.choice(
            ['Individual session'] * 5 + ['Extended individual', 'Couples session', 'Family session', 'Child session', 'Child session', 'Speech therapy', 'Behaviour therapy', 'Review session', 'Intake assessment'])),
            rating=rating, would_recommend=yn(rec), topic=key('fbtopic', topic)))
    out.sort(key=lambda x: x['date'])
    for i, x in enumerate(out, 1): x['survey_id'] = 'FB-%03d' % i
    rows = [nb(dict(survey_id=x['survey_id'], **{k: v for k, v in x.items() if k != 'survey_id'})) for x in out]
    return front(rows, lambda r: r['would_recommend'] == 'yes' and r['rating'] >= 9)

# ---------- groups, sign-ups, attendance, interest, ideas
GRD = {g['group_id']: g for g in GRP}
GSL = collections.defaultdict(list)
for s in GSU: GSL[s['group_id']].append(s)
def groups_d():
    rows = [nb(dict(group_id=g['group_id'], program=key('prog', g['program']), facilitator=key('clin', g['facilitator']), co_facilitator=key('clin', g['co_facilitator']) if g['co_facilitator'] else '',
                    room=key('room5', g['room']), start_date=g['start_date'], weekday=key('wday', g['weekday']), start_time=g['start_time'], weeks=g['weeks'], capacity=g['capacity'], fee=int(g['fee']),
                    signups=g['signups'], revenue=int(round(g['revenue'])), facilitator_pay=int(round(g['facilitator_pay'])), materials=int(g['materials']), marketing=int(g['marketing']),
                    room_cost=int(g['room_cost']), meetings_held=g['meetings_held'], status=key('grpst', g['status']))) for g in GRP]
    return rows

def signups_d():
    rows = [nb(dict(signup_id=s['signup_id'], group_id=s['group_id'], program=key('prog', s['program']), name=s['name'], phone=s['phone'], signed_on=s['signed_on'], paid_amount=int(round(s['paid_amount'])),
                    paid_on=s['paid_on'], sessions_attended=s['sessions_attended'], status=key('signst', s['status']))) for s in GSU]
    return front(rows, lambda r: r['status'] == key('signst', 'Completed') and r['sessions_attended'] >= 4 and r['group_id'] == 'GR-16')

def attendance_d():
    out = []; i = 0
    for g in GRP:
        if g['status'] not in ('Completed', 'Running'): continue
        people = [s for s in GSL[g['group_id']] if s['status'] != 'Refunded']
        for k in range(1, g['meetings_held'] + 1):
            i += 1
            out.append(dict(row_id='GA-%03d' % i, group_id=g['group_id'], meeting_no=k, date=iso(dd(g['start_date']) + day(7 * (k - 1))), attended=sum(1 for s in people if s['sessions_attended'] >= k)))
    return front(out, lambda r: r['group_id'] == 'GR-16' and r['meeting_no'] == 3)

IL_PROG = {'Parenting skills': 6, 'Stress skills': 4, 'Grief support': 3, 'Teen confidence': 3, 'Child social skills': 2}
def interest_d():
    r = rng('int'); rows = []
    signed = [s for s in GSU if s['signed_on'] >= ago(420) and s['status'] in ('Completed', 'Dropped out', 'Attending')]
    pick = [s for i, s in enumerate(signed) if i % 3 == 0][:22]
    for s in pick:
        add = dd(s['signed_on']) - day(r.randint(14, 70)); con = add + day(r.randint(1, 6))
        rows.append(dict(name=s['name'], phone=s['phone'], program=s['program'], added_on=iso(add), contacted_on=iso(con), signed_up='yes'))
    used = {s['name'] for s in GSU}
    pool = [c for c in CLI if c['name' if 'name' in c else 'client'] not in used and c['status'] in ('Active', 'Discharged') and c['client_type'] in ('Adult', 'Couple', 'Family', 'Young person', 'Child')]
    r2 = rng('intw'); r2.shuffle(pool); p = 0
    for prog, n in IL_PROG.items():
        for _ in range(n):
            c = pool[p]; p += 1
            ad = T0 - day(r2.randint(3, 130)); con = '' if (ad > T0 - day(14) and r2.random() < 0.8) or r2.random() < 0.12 else iso(ad + day(r2.randint(1, 5)))
            rows.append(dict(name=c['client'], phone=c['phone'], program=prog, added_on=iso(ad), contacted_on=con, signed_up='no'))
    rows.sort(key=lambda x: (x['added_on'], x['name']))
    for i, x in enumerate(rows, 1): x['interest_id'] = 'IL-%03d' % i
    out = [nb(dict(interest_id=x['interest_id'], **{k: v for k, v in x.items() if k != 'interest_id'})) for x in rows]
    for x in out:
        x['program'] = key('prog', x['program'])
    return front(out, lambda r: r['signed_up'] == 'no' and r['program'] == key('prog', 'Parenting skills') and r.get('contacted_on'))

IDEAS = [('Parenting skills for separated parents', 'Adult', 'Sofia Marchetti', 10, 240), ('Friendship skills for children', 'Child', 'Priya Raman', 8, 300), ('Study habits for teens', 'Young person', 'Lucas Moreau', 8, 220),
         ('Stress skills for team leaders', 'Adult', 'Daniel Okoye', 12, 260), ('Couples communication refresher', 'Couple', 'Amira Lindqvist', 6, 340), ('Returning to work after leave', 'Adult', 'Daniel Okoye', 10, 230),
         ('Settling in after a move', 'Family', 'Kenji Watanabe', 8, 200), ('Grief support evening, shorter course', 'Adult', 'Amira Lindqvist', 8, 170), ('Carers: looking after yourself', 'Adult', 'Sofia Marchetti', 10, 190),
         ('Teen confidence summer course', 'Young person', 'Lucas Moreau', 10, 250), ('Parent and toddler communication', 'Family', 'Priya Raman', 8, 210), ('Retirement and change', 'Adult', 'Amira Lindqvist', 10, 220)]
def ideas_d():
    out = []
    for i, (t, ct, f, cap, fee) in enumerate(IDEAS, 1):
        r = rng('idea' + t); ppl = r.randint(7, 24)
        out.append(dict(idea_id='ID-%02d' % i, idea=t, client_type=key('ctype', ct), people_interested=ppl, facilitator=key('clin', f), capacity=cap, expected_signups=max(3, min(cap, int(round(ppl * r.uniform(0.4, 0.7))))), fee=fee))
    return out

def programs_d(): return [dict(program=key('prog', p['program']), weeks=p['weeks'], fee=int(p['fee'])) for p in programs]
ROLE_NAME = {'Clinician': 'Employed clinician', 'Contract clinician': 'Contract clinician (self-employed)', 'Associate': 'Associate (works under supervision)'}
def team_d():
    return [nb(dict(staff_id=s['staff_id'], name=s['name'], role=ROLE_NAME.get(s['role'], s['role']), team=s['team'], pay_type=s['pay_type'], phone=s['phone'], email=s['email'], hours_week=s['hours_week'],
                    monthly_salary=s['monthly_salary'], split_pct=s['split_pct'], session_rate=s['session_rate'], hourly_rate=s['hourly_rate'], session_cap=s['session_cap'], session_target=s['session_target'],
                    speciality=s['speciality'], country=s['country'], start=s['start'])) for s in team]

if __name__ == '__main__':
    for f in (enquiries_d, sourcemonths_d, clientvalue_d, referrers_d, referrallog_d, contacts_d, campaigns_d, budget_d, directory_d, website_d, workshops_d, newsletter_d, feedback_d, groups_d, signups_d,
              attendance_d, interest_d, ideas_d, programs_d, team_d):
        print(f.__name__, len(f()))
