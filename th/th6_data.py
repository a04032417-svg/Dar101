"""Therapy practice suite part 6: demo rows built from th_core (row-level tables show a thinned sample, monthly and weekly tables use the full data)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th6_lists import *
import collections

R = rng('th6')
dd = to_date
T0 = TODAY
TISO = iso(T0)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows

SES = session_rows(); CLI = client_rows(); PLN = plan_review_rows(); OUT = outcome_rows(); DIS = discharge_rows(); SUP = supervision_rows(); CE = ce_rows()
RENS = renewal_rows() + extra_renewal_rows()
ATT = [s for s in SES if s['status'] == 'Attended']
CLD = {c['client_id']: c for c in CLI}
PH = {s['name']: s['phone'] for s in team}
ROLE2 = {'Owner clinician': 'Owner clinician', 'Clinician': 'Employed clinician', 'Contract clinician': 'Contract (self-employed) clinician', 'Associate': 'Associate (works under supervision)'}
MONTHS = [month_start(k) for k in range(23, -1, -1)]
def eom(d): return add_months(d, 1) - day(1)
MS_NOW = iso(month_start(0))

# ---------- note status: every attended session of the last 14 days, every missing note, and about 1 in 17 before that
def notes_d():
    rec = ago(14); out = []
    for i, s in enumerate(ATT):
        if s['date'] >= rec or s['note_done_on'] == '' or i % 17 == 0:
            out.append(nb(dict(session_id=s['session_id'], date=s['date'], client=s['client'], clinician=key('clin', s['clinician']), service=key('svc', s['service']), note_done_on=s['note_done_on'])))
    return front(out, lambda r: r.get('note_done_on') and r['date'] < ago(30))

# ---------- notes and plan reviews by clinician and month (full data)
def month_rows_d():
    rows = []; n = 0
    A = collections.defaultdict(lambda: [0, 0, 0, 0])
    for s in ATT:
        a = A[(s['clinician'], s['month'])]; a[0] += 1
        if s['note_done_on'] == '': a[3] += 1
        elif s['note_on_time'] == 'Yes': a[1] += 1
        else: a[2] += 1
    rd = collections.Counter((p['clinician'], p['due_date'][:7]) for p in PLN)
    rn = collections.Counter((p['clinician'], p['reviewed_on'][:7]) for p in PLN if p['reviewed_on'])
    for m in MONTHS:
        ms = iso(m)
        for cl in CLINICIANS:
            a = A.get((cl, ms))
            if not a: continue
            n += 1
            rows.append(dict(row_id='NM-%03d' % n, month=ms, clinician=key('clin', cl), on_time=a[1], late=a[2], missing=a[3], reviews_due=rd.get((cl, ms[:7]), 0), reviews_done=rn.get((cl, ms[:7]), 0)))
    return rows

# ---------- late notes by clinician and week, last 13 weeks (full data)
WEEK0 = week_start(T0)
def weeks_d():
    rows = []; n = 0
    for k in range(12, -1, -1):
        mon = WEEK0 - day(7 * k); ms = iso(mon); lab = 'Week %d' % (13 - k)
        for cl in CLINICIANS:
            ss = [s for s in ATT if s['clinician'] == cl and s['week'] == ms]
            if not ss: continue
            late = sum(1 for s in ss if (s['note_done_on'] and s['note_on_time'] == 'No') or (s['note_done_on'] == '' and dd(s['date']) < T0 - day(NOTE_DUE_DAYS)))
            n += 1
            rows.append(dict(row_id='LW-%03d' % n, week=ms, clinician=key('clin', cl), wk=key('wk', lab), notes_due=len(ss), notes_late=late))
    return rows

# ---------- plan reviews: every open review, every review of the last 120 days and about 1 in 6 before that
def reviews_d():
    cut = ago(120); out = []
    for i, p in enumerate(PLN):
        if p['reviewed_on'] == '' or p['reviewed_on'] >= cut or i % 6 == 0:
            c = CLD.get(p['client_id'])
            out.append(nb(dict(review_id=p['review_id'], client_id=p['client_id'], client=p['client'], clinician=key('clin', p['clinician']), review_no=p['review_no'], due_date=p['due_date'],
                               reviewed_on=p['reviewed_on'], score=p['score'])))
    out.sort(key=lambda r: (r['due_date'], r['review_id']))
    return front(out, lambda r: r.get('reviewed_on') and r['reviewed_on'] <= r['due_date'] and r['due_date'] > ago(100))

# ---------- outcome scores: 1 row in 4 across the whole history
def scores_d():
    out = [nb(dict(score_id=o['score_id'], date=o['date'], client_id=o['client_id'], client=o['client'], clinician=key('clin', o['clinician']), point=key('opoint', o['point']), score=o['score']))
           for i, o in enumerate(OUT) if i % 4 == 0 or o['date'] >= ago(10)]
    return front(out, lambda r: r['point'] == key('opoint', 'Review') and r['date'] < ago(60))

# ---------- score change by client (active, on hold and referred out; intake score read from the score log)
INTAKE = {}
for o in OUT:
    if o['point'] == 'Intake': INTAKE.setdefault(o['client_id'], o['score'])
LASTSC = {}
for o in sorted(OUT, key=lambda o: o['date']): LASTSC[o['client_id']] = o['date']
def change_d():
    out = []
    for c in CLI:
        if c['status'] in ('Active', 'On hold', 'Referred out'):
            has = c['client_id'] in INTAKE
            out.append(nb(dict(client_id=c['client_id'], client=c['client'], clinician=key('clin', c['clinician']), service=key('csvc', c['service']), status=key('cstatus', c['status']),
                               intake_score=INTAKE[c['client_id']] if has else '', latest_score=c['latest_score'] if has else '', phone=c['phone'])))
    return front(out, lambda r: r.get('intake_score') and r['latest_score'] < r['intake_score'] - 6 and r['status'] == key('cstatus', 'Active'))

# ---------- clients: everyone active, on hold or booked plus the 55 most recent discharges and referrals out
def _recent_discharged():
    dl = sorted([d for d in DIS], key=lambda d: (d['date'], d['discharge_id']))[-55:]
    return {d['client_id'] for d in dl}
RECENT = _recent_discharged()
CLSET = [c for c in CLI if c['status'] in ('Active', 'On hold', 'Booked') or c['client_id'] in RECENT]
def clients_d():
    out = [nb(dict(client_id=c['client_id'], client=c['client'], clinician=key('clin', c['clinician']), service=key('csvc', c['service']), status=key('cstatus', c['status']), phone=c['phone'],
                   first_session=c['first_session'], last_session=c['last_session'], next_session=c['next_session'], last_score_on=LASTSC.get(c['client_id'], ''))) for c in CLSET]
    return front(out, lambda r: r['status'] == key('cstatus', 'Active') and r.get('last_score_on') and r.get('next_session'))

# ---------- discharges: about 2 in 5 across the whole history, with the referral and letter status
DS = [d for i, d in enumerate(sorted(DIS, key=lambda d: (d['date'], d['discharge_id']))) if i % 5 in (0, 2) or (d['referred_to'] and i % 5 == 3)]
def discharges_d():
    out = []
    ref_rank = 0
    for d in DS:
        c = CLD[d['client_id']]
        sent = 'yes' if d['referred_to'] and dd(d['date']) < T0 - day(10) else ('no' if d['referred_to'] else '')
        out.append(nb(dict(discharge_id=d['discharge_id'], date=d['date'], client_id=d['client_id'], client=d['client'], phone=c['phone'], clinician=key('clin', d['clinician']), service=key('csvc', d['service']),
                           reason=key('dreason', d['reason']), sessions=d['sessions'], referred_to=key('refto', d['referred_to']) if d['referred_to'] else '', last_session=c['last_session'],
                           letter_sent=yn(d['letter_sent'] == 'Yes'), referral_sent=sent, final_score=d['final_score'])))
    return front(out, lambda r: r.get('referred_to') and r['referral_sent'] == 'yes' and r['letter_sent'] == 'yes' and r.get('final_score') not in ('', None) and r.get('last_session'))

# ---------- records keep-until list (the same discharged clients)
def keep_d():
    out = []; rr = rng('keep')
    for d in DS:
        c = CLD[d['client_id']]; dtd = dd(d['date'])
        yrs = 10 if c['client_type'] in ('Child', 'Young person') else 7
        old = dtd < add_months(T0, -13)
        arch = old and rr.random() < 0.88
        out.append(dict(client_id=d['client_id'], client=d['client'], client_type=c['client_type'], discharge_date=d['date'], years_to_keep=yrs, archived=yn(arch)))
    return front(out, lambda r: r['archived'] == 'yes')

# ---------- supervision
def sup_log_d():
    return [nb(dict(supervision_id=s['supervision_id'], date=s['date'], supervisee=key('clin', s['supervisee']), supervisor=s['supervisor'], kind=key('supk', s['kind']), hours=s['hours'], cost=int(s['cost']))) for s in SUP]

def sup_month_d():
    A = collections.Counter((s['clinician'], s['month']) for s in ATT)
    rows = []; n = 0
    for m in MONTHS:
        for cl in CLINICIANS:
            a = A.get((cl, iso(m)))
            if a:
                n += 1; rows.append(dict(row_id='SH-%03d' % n, month=iso(m), clinician=key('clin', cl), client_sessions=a))
    return rows

# ---------- continuing education
def ce_log_d():
    return [nb(dict(ce_id=x['ce_id'], date=x['date'], clinician=key('clin', x['clinician']), kind=key('cek', x['kind']), title=x['title'], hours=x['hours'], cost=int(x['cost']), paid_by=key('paidby', x['paid_by']),
                    certificate=yn(x['certificate'] == 'Yes'))) for x in CE]

def ce_year_d():
    out = []; n = 0
    for y in (T0.year - 1, T0.year):
        for cl in CLINICIANS:
            tg = 20
            if cl == 'Priya Raman' and y == T0.year - 1: tg = 10
            if cl == 'Lucas Moreau' and y == T0.year - 1: tg = 0
            n += 1; out.append(dict(row_id='CY-%02d' % n, year=y, clinician=key('clin', cl), target=tg))
    return out

# ---------- renewals (the register of th_core plus data protection registration and the associate's cover)
def renewals_d():
    rows = sorted(RENS, key=lambda r: (r['due_date'], r['renewal_id']))
    out = [nb(dict(renewal_id=r['renewal_id'], holder=key('holder', r['holder']), item=key('renk', r['item']), every_months=r['every_months'], due_date=r['due_date'], renewed_on=r['renewed_on'],
                   cost=int(r['cost']), paid_by=key('paidby', r['paid_by']))) for r in rows]
    s = story()
    return front(out, lambda r: r['renewal_id'] == s['renewal_due'])

# ---------- consent records: one per client of the clients table
def consent_d():
    out = []; rr = rng('consent'); n = 0
    for c in CLSET:
        n += 1
        signed = min(dd(c['first_session']), T0) - day(rr.randint(0, 4)) if c['status'] != 'Booked' else dd(c['booked_on']) + day(1)
        rev = ''
        if signed + day(365) < T0 - day(5) and rr.random() < 0.85:
            rev = min(T0 - day(1), signed + day(365 + rr.randint(-25, 30)))
        out.append(nb(dict(consent_id='CN-%04d' % n, client_id=c['client_id'], client=c['client'], phone=c['phone'], clinician=key('clin', c['clinician']), status=key('cstatus', c['status']), signed_on=iso(signed),
                           contact_ok=yn(rr.random() < .93), online_ok=yn(rr.random() < .72), reviewed_on=iso(rev) if rev else '')))
    return front(out, lambda r: r['status'] == key('cstatus', 'Active') and r.get('reviewed_on'))

# ---------- record requests
def requests_d():
    rr = rng('req'); act = [c for c in CLSET if c['status'] in ('Active', 'Discharged', 'Referred out')]
    days = [330, 305, 276, 251, 228, 205, 184, 160, 139, 118, 101, 86, 72, 60, 48, 38, 26, 12, 5, 3]
    kinds = ['Copy of records', 'Summary letter', 'Transfer of records', 'Copy of records', 'Correction request', 'Copy of records', 'Summary letter', 'Transfer of records']
    out = []
    for i, dy in enumerate(days, 1):
        c = act[(i * 37) % len(act)]; d0 = dd(ago(dy)); opn = dy in (38, 26, 12, 5, 3)
        sent = '' if opn else iso(d0 + day(rr.randint(3, 26)))
        out.append(nb(dict(request_id='RR-%03d' % i, date=iso(d0), client=c['client'], phone=c['phone'], kind=key('reqkind', kinds[i % len(kinds)]), sent_on=sent)))
    return front(out, lambda r: r.get('sent_on'))

# ---------- privacy checks, one a month
def privacy_d():
    out = []; rr = rng('priv')
    miss = {19: 'devices', 14: 'cabinets', 8: 'passwords', 0: 'devices'}
    for i, k in enumerate(range(23, -1, -1), 1):
        m = month_start(k); who = rr.choice(['Grace Mensah'] * 7 + [OWNER] * 2 + ['Samir Haddad'])
        out.append(dict(check_id='PV-%02d' % i, month=iso(m), passwords_changed=yn(miss.get(k) != 'passwords'), cabinets_locked=yn(miss.get(k) != 'cabinets'), devices_checked=yn(miss.get(k) != 'devices'), done_by=who))
    return front(out, lambda r: r['month'] < ago(100))

# ---------- policy reviews
def policies_d():
    P_ = [('Privacy policy', 290, 12, OWNER), ('Complaints policy', 150, 12, COORDINATOR), ('Cancellation and late fee policy', 60, 12, COORDINATOR), ('Fee and payment policy', 200, 12, OWNER),
          ('Records and retention policy', 410, 12, OWNER), ('Online session policy', 160, 6, 'Daniel Okoye'), ('Supervision policy', 330, 12, OWNER), ('Associate supervision agreement', 270, 12, OWNER),
          ('Contractor terms', 500, 24, OWNER), ('Group program rules', 100, 12, 'Sofia Marchetti'), ('Device and password policy', 240, 6, 'Samir Haddad'), ('Consent and information sheet', 190, 12, 'Daniel Okoye')]
    return [dict(policy_id='PO-%02d' % i, policy=p, last_reviewed=ago(d), every_months=m, reviewed_by=w) for i, (p, d, m, w) in enumerate(P_, 1)]

# ---------- incident and complaint log (admin facts only)
def incidents_d():
    X = [(318, 'Billing query', 'Billing', 'Invoice checked and corrected', 4, 'Grace Mensah'), (290, 'Room or equipment', 'Building', 'Repair booked with the landlord', 12, 'Grace Mensah'),
         (262, 'Complaint', 'Front desk', 'Called back and agreed the next step', 9, OWNER), (241, 'Near miss', 'Building', 'Door sign added', 2, 'Grace Mensah'),
         (214, 'Privacy incident', 'IT', 'Device checked and password changed', 3, 'Samir Haddad'), (196, 'Staff concern', 'Team', 'Talked with the owner and agreed a plan', 14, OWNER),
         (171, 'Billing query', 'Billing', 'Fee explained and invoice reissued', 6, 'Grace Mensah'), (149, 'Room or equipment', 'Building', 'Cleaner asked to check the heating', 5, 'Wanjiru Kamau'),
         (127, 'Complaint', 'Front desk', 'Reply sent and policy reviewed', 18, OWNER), (103, 'Near miss', 'Building', 'Waiting room layout changed', 1, 'Grace Mensah'),
         (84, 'Privacy incident', 'IT', 'Mis-sent e-mail recalled and logged', 2, OWNER), (61, 'Billing query', 'Billing', 'Payment matched and receipt sent', 7, 'Grace Mensah'),
         (33, 'Room or equipment', 'Building', 'Lock repair booked', None, 'Grace Mensah'), (19, 'Complaint', 'Front desk', 'Call-back planned with the owner', None, OWNER), (6, 'Staff concern', 'Team', 'Meeting booked with the owner', None, OWNER)]
    return [nb(dict(incident_id='IC-%03d' % i, date=ago(d), kind=key('inckind', k), area=a, action_taken=act, handled_by=w, closed_on=iso(dd(ago(d)) + day(n)) if n else '')) for i, (d, k, a, act, n, w) in enumerate(X, 1)]

def team_d():
    return [nb(dict(staff_id=s['staff_id'], name=s['name'], role=ROLE2.get(s['role'], s['role']), team=s['team'], pay_type=s['pay_type'], phone=s['phone'], email=s['email'], hours_week=s['hours_week'],
                    monthly_salary=s['monthly_salary'], split_pct=s['split_pct'], session_rate=s['session_rate'], hourly_rate=s['hourly_rate'], session_cap=s['session_cap'], session_target=s['session_target'],
                    speciality=s['speciality'], country=s['country'], start=s['start'], supervised=yn(s['role'] == 'Associate'))) for s in team]

if __name__ == '__main__':
    for f in (notes_d, month_rows_d, weeks_d, reviews_d, scores_d, change_d, clients_d, discharges_d, keep_d, sup_log_d, sup_month_d, ce_log_d, ce_year_d, renewals_d, consent_d, requests_d, privacy_d, policies_d, incidents_d, team_d):
        print(f.__name__, len(f()))
