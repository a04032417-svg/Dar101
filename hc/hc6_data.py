"""Home care agency suite part 6: demo rows built from hc_core (row tables from the generators, monthly tables from the full data)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc6_lists import *
import collections, datetime as _dt

dd = to_date
TI = iso(TODAY)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def days(a, b): return (dd(a) - dd(b)).days

CG = caregiver_rows(); CGN = {g['name']: g for g in CG}; CGI = {g['caregiver_id']: g for g in CG}
APP = [dict(a) for a in applicant_rows()]
for a in APP:  # two open applicants have waited longer for a call (story: the call list is not empty)
    if a['applicant_id'] == 'AP-0240': a['applied_on'] = ago(5)
    if a['applicant_id'] == 'AP-0241': a['applied_on'] = ago(4)
APPN = {a['name']: a for a in APP}
PH = {s['staff_id']: s['phone'] for s in team}
NAMES = {s['staff_id']: s['name'] for s in team}
RECR, OWNER_N, SCHED_N = NAMES['HC-04'], NAMES['HC-01'], NAMES['HC-02']
MS = [month_start(k) for k in range(23, -1, -1)]  # 24 months, oldest first


# ---------- applicants
def applicants_d():
    return [nb(dict(applicant_id=a['applicant_id'], applied_on=a['applied_on'], name=a['name'], phone=a['phone'], source=key('recsrc', a['source']), phone_screen_on=a['phone_screen_on'],
                    interview_on=a['interview_on'], offer_on=a['offer_on'], start_on=a['start_on'], status=key('applst', a['status']),
                    reason=key('applrsn', a['reason']) if a['reason'] else '', caregiver_id=a['caregiver_id'])) for a in APP]


# ---------- funnel by month (cohort of the application month)
def funnel_d():
    out = []
    for i, m in enumerate(MS, 1):
        mi = iso(m); rows = [a for a in APP if a['applied_on'][:7] == mi[:7]]
        ok = lambda k: sum(1 for a in rows if a[k] and a[k] <= TI)
        out.append(dict(funnel_id='RF-%02d' % i, month=mi, applicants=len(rows), phone_screens=ok('phone_screen_on'), interviews=ok('interview_on'), offers=ok('offer_on'),
                        starts=sum(1 for a in rows if a['status'] == 'Started')))
    return out


# ---------- source by month
def active90(a):
    g = CGI.get(a['caregiver_id'])
    if not g: return False
    return g['left_date'] == '' or days(g['left_date'], a['start_on']) > 90


UNIT = {'Online job board': (95, 11), 'Agency website': (25, 3), 'Caregiver referral': (0, 0), 'Training school': (60, 14), 'Community notice': (20, 7), 'Walk-in': (0, 0), 'Social media post': (15, 5)}
def sources_d():
    out = []; n = 0
    for m in MS:
        mi = iso(m)
        for s in REC_SOURCES:
            rows = [a for a in APP if a['applied_on'][:7] == mi[:7] and a['source'] == s]
            if not rows and s not in ('Online job board', 'Agency website', 'Social media post', 'Community notice'): continue
            st = [a for a in rows if a['status'] == 'Started']; r = rng('hc6src' + mi + s)
            base, per = UNIT[s]
            cost = round(base * r.uniform(.85, 1.2) + per * len(rows) * r.uniform(.9, 1.15) + (230 * len(st) if s == 'Caregiver referral' else 0), 2)
            n += 1
            out.append(dict(source_id='SM-%03d' % n, month=mi, source=key('recsrc', s), applicants=len(rows), starts=len(st), active_90=sum(1 for a in st if active90(a)), cost=cost))
    return out


# ---------- screens and interviews (most recent 210)
def screens_d():
    rows = []
    for a in APP:
        r = rng('hc6sc' + a['applicant_id'])
        if a['phone_screen_on'] and a['phone_screen_on'] <= TI:
            res = 'Pass' if a['interview_on'] else ('Hold' if a['status'] in ('Applied', 'Phone screen') else 'Not selected')
            rows.append((a['phone_screen_on'], a['applicant_id'], 'Phone screen', RECR if r.random() < .85 else SCHED_N, res, r.randint(8, 24)))
        if a['interview_on'] and a['interview_on'] <= TI:
            res = 'Pass' if a['offer_on'] else ('Hold' if a['status'] == 'Interview' else 'Not selected')
            rows.append((a['interview_on'], a['applicant_id'], 'Interview', r.choice([RECR, RECR, OWNER_N, SCHED_N, NAMES['HC-05'], NAMES['HC-06']]), res, r.randint(25, 55)))
    rows.sort(key=lambda x: (x[0], x[1], x[2]))
    rows = rows[-210:]
    return [dict(screen_id='SC-%04d' % i, date=d, applicant_id=ap, kind=key('kind', k), done_by=by, result=key('outcome', res), minutes=mn) for i, (d, ap, k, by, res, mn) in enumerate(rows, 1)]


# ---------- offers
def offers_d():
    out = []; es = [a for a in APP if a['offer_on']]
    for i, a in enumerate(es, 1):
        r = rng('hc6of' + a['applicant_id'])
        if a['status'] in ('Started', 'Onboarding'): ans = 'Accepted'
        elif a['status'] == 'Offer': ans = 'Waiting'
        elif a['reason'] == 'No reply': ans = 'No reply'
        else: ans = 'Declined'
        answered = ''
        if ans in ('Accepted', 'Declined'): answered = iso(min(dd(a['offer_on']) + _dt.timedelta(days=r.randint(1, 4)), TODAY))
        if ans == 'No reply': answered = ''
        g = CGN.get(a['name'])
        pay = g['pay_rate'] if g else round(r.choice([17, 17.5, 18, 18.5, 19, 19.5, 20]), 2)
        out.append(nb(dict(offer_id='OF-%03d' % i, applicant_id=a['applicant_id'], offer_on=a['offer_on'], answer=key('outcome', ans), answered_on=answered, start_on=a['start_on'] if ans == 'Accepted' else '',
                           pay_rate=pay, hours_week=r.choice([16, 20, 24, 24, 30, 36, 40]))))
    return out


# ---------- onboarding
OB = [dict(o) for o in onboarding_rows()]
def _extra_ob():
    have = {o['person'] for o in OB}; st = [a for a in APP if a['status'] == 'Started' and a['name'] not in have]
    st.sort(key=lambda a: a['start_on'])
    out = []
    for k, a in enumerate(st[:2], len(OB) + 1):
        s = dd(a['start_on']); f = lambda n: iso(s + _dt.timedelta(days=n))
        out.append(dict(onboarding_id='OB-%03d' % k, person=a['name'], caregiver_id=a['caregiver_id'], start_date=a['start_on'], identity_check_on=f(-10), references_on=f(-5), background_check_on=f(-6),
                        training_on=f(2), agreement_signed_on=f(-2), first_shift_on=f(7), owner=RECR))
    return out
OB += _extra_ob()
assert len(OB) == 18


def onboarding_d():
    return [nb(dict(onboarding_id=o['onboarding_id'], person=o['person'], caregiver_id=o['caregiver_id'], start_date=o['start_date'], identity_check_on=o['identity_check_on'], references_on=o['references_on'],
                    background_check_on=o['background_check_on'], training_on=o['training_on'], agreement_signed_on=o['agreement_signed_on'], first_shift_on=o['first_shift_on'], owner=o['owner'])) for o in OB]


OFFS = {'identity_check_on': ('Identity check', -12), 'references_on': ('References', -8), 'background_check_on': ('Background check', -7), 'agreement_signed_on': ('Agreement signed', -3),
        'training_on': ('Training', -2), 'first_shift_on': ('First shift', 5)}
def steps_d():
    out = []; n = 0
    for o in OB:
        s = dd(o['start_date'])
        for col, (lab, off) in OFFS.items():
            n += 1
            out.append(nb(dict(step_id='ST-%03d' % n, person=o['person'], step=key('step', lab), due_date=iso(s + _dt.timedelta(days=off)), done_on=o[col])))
    return out


# ---------- credentials (the most urgent first, superseded records last)
CRED = sorted(credential_rows(), key=lambda r: (r['status'] != 'Valid', r['expires_on'], r['credential_id']))
def credentials_d():
    return [nb(dict(credential_id=r['credential_id'], caregiver=r['caregiver'], credential=key('cred', r['credential']), issued_on=r['issued_on'], expires_on=r['expires_on'], renewed_on=r['renewed_on'],
                    status=key('credst', r['status']), reminder_sent=yn(r['reminder_sent']))) for r in CRED]


def credtypes_d():
    return [dict(credential=key('cred', t['credential']), renew_months=t['renew_months'], required_for=t['required_for']) for t in credential_types]


# ---------- renewals due (valid credentials expiring first, 44 rows; at least one per type)
def _renew_rows():
    val = [r for r in CRED if r['status'] == 'Valid']
    pick = val[:44]
    for t in CRED_TYPES:
        if not any(r['credential'] == t for r in pick):
            pick.append(next(r for r in val if r['credential'] == t))
    return sorted(pick, key=lambda r: (r['expires_on'], r['credential_id']))
RENEW = _renew_rows()
def renewals_d():
    out = []
    for i, r in enumerate(RENEW, 1):
        rr = rng('hc6rn' + r['credential_id']); left = days(r['expires_on'], TI)
        booked = course = ''
        if r['credential_id'] != story()['credential_id'] and left <= 100 and rr.random() < .55:
            booked = ago(rr.randint(0, 12)); course = iso(max(TODAY + _dt.timedelta(days=rr.randint(4, 21)), TODAY)); course = min(course, iso(dd(r['expires_on']) - _dt.timedelta(days=3)))
        out.append(nb(dict(renewal_id='RN-%03d' % i, caregiver=r['caregiver'], credential=key('cred', r['credential']), expires_on=r['expires_on'], booked_on=booked, course_date=course)))
    return out


# ---------- scheduled visits after expiry
def visitsafter_d():
    out = []; V = visit_rows(); st = story(); n = 0
    # posted schedule of the story caregiver
    for v in V:
        if v['caregiver_id'] == st['credential_caregiver'] and v['date'] > st['credential_date'] and v['date'] > TI and len(out) < 6:
            n += 1; out.append(dict(item_id='VX-%03d' % n, credential=key('cred', st['credential_type']), caregiver=v['caregiver'], date=v['date'], client=v['client'], hours=v['sched_hours'], basis='Posted schedule'))
    # regular weekly visits of the other caregivers after their expiry
    recent = [v for v in V if TI >= v['date'] >= ago(14) and v['status'] != 'Cancelled' and v['status'] != 'Missed']
    bycg = collections.defaultdict(dict)
    for v in recent: bycg[v['caregiver_id']][dd(v['date']).weekday()] = v
    for r in RENEW:
        if r['caregiver_id'] == st['credential_caregiver'] or len(out) >= 40: continue
        exp = dd(r['expires_on'])
        if (exp - TODAY).days > 80: continue
        pat = bycg.get(r['caregiver_id'], {})
        for k in range(1, 8):
            d = exp + _dt.timedelta(days=k)
            if d.weekday() in pat and len(out) < 40:
                v = pat[d.weekday()]; n += 1
                out.append(dict(item_id='VX-%03d' % n, credential=key('cred', r['credential']), caregiver=r['caregiver'], date=iso(d), client=v['client'], hours=v['sched_hours'], basis='Regular weekly visit'))
    out.sort(key=lambda x: (x['date'], x['item_id']))
    for i, x in enumerate(out, 1): x['item_id'] = 'VX-%03d' % i
    return out


# ---------- caregivers, leavers
def caregivers_d():
    return [nb(dict(caregiver_id=g['caregiver_id'], name=g['name'], hire_date=g['hire_date'], employment=key('emp', g['employment']), area=key('area', g['area']), status=key('cgstatus', g['status']),
                    left_date=g['left_date'], leave_reason=key('leave', g['leave_reason']) if g['leave_reason'] else '', source=key('recsrc', g['source']) if g['source'] else '', pay_rate=g['pay_rate'], phone=g['phone'])) for g in CG]


LEAVERS = sorted([g for g in CG if g['left_date']], key=lambda g: g['left_date'])
def leavers_d():
    # most recent first would hide the oldest: keep the first row complete (reason and source known)
    rows = sorted(LEAVERS, key=lambda g: (g['source'] == '', g['left_date']))
    return [nb(dict(leaver_id='LV-%02d' % i, caregiver=g['name'], hire_date=g['hire_date'], left_date=g['left_date'], reason=key('leave', g['leave_reason']), source=key('recsrc', g['source']) if g['source'] else '')) for i, g in enumerate(rows, 1)]


# ---------- turnover by month
def turnover_d():
    out = []
    for i, m in enumerate(MS, 1):
        a = m; b = add_months(m, 1)
        start = sum(1 for g in CG if dd(g['hire_date']) < a and (g['left_date'] == '' or dd(g['left_date']) >= a))
        hires = sum(1 for g in CG if a <= dd(g['hire_date']) < b)
        lv = [g for g in CG if g['left_date'] and a <= dd(g['left_date']) < b]
        f90 = sum(1 for g in lv if days(g['left_date'], g['hire_date']) <= 90)
        out.append(dict(turn_id='TO-%02d' % i, month=iso(m), caregivers_start=start, hires=hires, leavers=len(lv), first90=f90))
    return out


# ---------- hiring cost log
def hirecost_d():
    rows = []
    for a in APP:
        r = rng('hc6hc' + a['applicant_id']); hired = a['status'] == 'Started'
        if not (hired or (a['status'] == 'Not selected' and a['reason'] == 'Check not passed')): continue
        free = a['source'] in ('Caregiver referral', 'Walk-in')
        ad = 0 if free and r.random() < .7 else round(r.uniform(90, 300), 2)
        chk = r.choice([45, 45, 38, 52, 60, 48, 41])
        m = (a['start_on'] if hired else (a['offer_on'] or a['interview_on'] or a['applied_on']))[:7] + '-01'
        rows.append(dict(month=m, person=a['name'], hired=yn(hired), advert_cost=ad, check_cost=chk, training_hours=r.randint(12, 22) if hired else 0,
                         other_cost=r.choice([0, 25, 30, 35, 40, 60, 45]) if hired else r.choice([6, 9, 12, 15, 18])))
    rows.sort(key=lambda x: (x['month'], x['hired'] != 'yes', x['person']))
    for i, x in enumerate(rows, 1): x['cost_id'] = 'HC-%03d' % i
    return [dict(cost_id=x['cost_id'], **{k: v for k, v in x.items() if k != 'cost_id'}) for x in rows]


# ---------- training sessions (most recent 100)
def training_d():
    rows = []
    for r in credential_rows():
        if r['renewed_on'] and r['credential'] in ('Core skills refresher', 'First aid course') and r['renewed_on'] <= TI:
            rows.append((r['renewed_on'], r['caregiver'], r['credential'], 7 if r['credential'] == 'First aid course' else 4))
    for o in OB:
        if o['training_on'] and o['training_on'] <= TI: rows.append((o['training_on'], o['person'], 'Onboarding training', 16))
    cg_active = [g['name'] for g in CG if g['status'] == 'Active']
    r = rng('hc6tr')
    for k in range(26):
        rows.append((ago(r.randint(5, 620)), r.choice(cg_active), r.choice(['Communication skills', 'Safe driving', 'Record keeping basics']), r.choice([2, 3, 3, 4])))
    rows = [x for x in rows if x[1] in CGN]
    rows.sort(key=lambda x: (x[0], x[1], x[2]))
    rows = rows[-100:]
    out = []
    for i, (d, nm, co_, h) in enumerate(rows, 1):
        rr = rng('hc6trf' + d + nm + co_); inh = co_ in ('Onboarding training', 'Communication skills', 'Record keeping basics')
        out.append(dict(training_id='TR-%03d' % i, date=d, caregiver=nm, course=key('course', co_), hours=h, provider='In-house' if inh else NAMES['HC-11'], paid=yn(rr.random() < .9 or co_ == 'Onboarding training'),
                        fee=0 if inh else rr.choice([45, 55, 65, 75, 85, 95, 110])))
    return out


# ---------- hire planning by week (26 weeks: 24 up to this week and 2 ahead)
def hireplan_d():
    W = {w['week']: w for w in week_rows()}; wk0 = week_start(TODAY) - _dt.timedelta(days=7 * 23)
    out = []
    for i in range(26):
        w = iso(wk0 + _dt.timedelta(days=7 * i)); row = W[w]; r = rng('hc6hp' + w)
        waiting = round(row['scheduled_hours'] - row['planned_hours'], 1)
        free = round(waiting * r.uniform(.2, .7) * 2) / 2
        out.append(dict(plan_id='HP-%02d' % (i + 1), week=w, hours_waiting=waiting, free_hours=free))
    return out


# ---------- recruiting campaigns
def campaigns_d():
    base = [m for m in marketing_rows() if m['target'] == 'Caregivers']; rows = []
    r = rng('hc6cp')
    for m in base:
        rows.append(dict(month=m['month'], kind=m['kind'], area=r.choice(AREAS), hours_week=r.choice([16, 20, 24, 30, 36]), cost=m['cost'], applicants=m['results'] + r.randint(2, 7), starts=m['started']))
    kinds = ['Online job ad', 'Community flyers', 'Directory listing', 'Website', 'Partner visit', 'Referral bonus', 'Local event']
    for k in range(36 - len(rows)):
        kd = r.choice(kinds); ap = r.randint(3, 20)
        rows.append(dict(month=iso(r.choice(MS)), kind=kd, area=r.choice(AREAS), hours_week=r.choice([16, 20, 24, 30, 36]), cost=round(r.uniform(90, 640), 2), applicants=ap, starts=min(ap // 6, r.choice([0, 1, 1, 2]))))
    rows.sort(key=lambda x: (x['month'], x['kind']))
    return [dict(campaign_id='RC-%03d' % i, month=x['month'], kind=key('mkind', x['kind']), area=key('area', x['area']), hours_week=x['hours_week'], cost=x['cost'], applicants=x['applicants'], starts=x['starts']) for i, x in enumerate(rows, 1)]


# ---------- referral bonuses
def referrals_d():
    rows = []; r = rng('hc6rf'); es = [a for a in APP if a['source'] == 'Caregiver referral' and a['interview_on']]
    due_set = False
    for a in es:
        pool = [g for g in CG if g['hire_date'] < a['applied_on'] and g['name'] != a['name'] and (g['left_date'] == '' or g['left_date'] > a['applied_on'])]
        ref = r.choice(pool)['name']; hired = a['status'] == 'Started'; hd = a['start_on'] if hired else ''
        amt = r.choice([150, 200, 250, 250, 300]); paid = ''
        if hired:
            n90 = dd(hd) + _dt.timedelta(days=90); g = CGN[a['name']]
            if n90 <= TODAY and g['left_date'] == '':
                if not due_set and n90 > TODAY - _dt.timedelta(days=60): due_set = True
                else: paid = iso(n90 + _dt.timedelta(days=r.randint(2, 8)))
        rows.append((a['applied_on'], dict(referring=ref, new_caregiver=a['name'], hire_date=hd, amount=amt, paid_on=paid)))
    rows.sort(key=lambda x: x[0])
    return [nb(dict(referral_id='RB-%02d' % i, **x[1])) for i, x in enumerate(rows, 1)]


# ---------- team
def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'],
                    monthly_salary=t['monthly_salary'], hourly_rate=t['hourly_rate'], speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]


if __name__ == '__main__':
    for f in (applicants_d, funnel_d, sources_d, screens_d, offers_d, onboarding_d, steps_d, credentials_d, credtypes_d, renewals_d, visitsafter_d, caregivers_d, leavers_d, turnover_d, hirecost_d, training_d, hireplan_d, campaigns_d, referrals_d, team_d):
        x = f(); print(f.__name__, len(x), x[0])
