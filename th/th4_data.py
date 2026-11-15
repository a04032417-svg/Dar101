"""Therapy practice suite part 4: demo rows built from th_core (sampled rows for row-level tables, full data for the monthly tables)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th4_lists import *
import collections

dd = to_date
T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows
def mon(s): return s[:7] + '-01'

ST = story()
SES = session_rows(); CLI = client_rows(); CLM = {c['client_id']: c for c in CLI}
PH = {s['name']: s['phone'] for s in team}
PAYCLI = {c['client_id']: c for c in CLI if c['fee_type'] == 'Third-party payer'}
CL = claim_rows()

# ---------- the practice's own gaps: four claims that were never answered, and sessions that were never claimed
_pool = lambda p: [c for c in CL if c['payer'] == p and c['status'] == 'Paid' and not c['denied_on'] and ago(125) <= c['submitted_on'] <= ago(96) and c['amount'] >= 60 and c['client_id'] != ST['denied_client_id']]
_lost = set()
_rl = rng('th4-lost')
for _p, _n in (('Payer D', 3), ('Payer B', 1)):
    for c in _rl.sample(_pool(_p), _n):
        c.update(status='Submitted', paid_on='', paid_amount=0.0, written_off=0.0); _lost.add(c['claim_id'])
_ru = rng('th4-unclaimed')
_upool = [c for c in CL if c['status'] == 'Paid' and not c['denied_on'] and ago(95) <= c['date'] <= ago(8) and c['client_id'] != ST['denied_client_id'] and c['claim_id'] not in _lost]
_drop = {c['claim_id'] for c in _ru.sample([c for c in _upool if c['clinician'] == ASSOCIATE], 18) + _ru.sample([c for c in _upool if c['clinician'] != ASSOCIATE], 30)}
CL = [c for c in CL if c['claim_id'] not in _drop]
CLAIMED = {c['session_id'] for c in CL}
PS_ALL = [s for s in SES if s['fee_type'] == 'Third-party payer']
UNC = [s for s in PS_ALL if s['status'] == 'Attended' and s['payer_amount'] > 0 and s['date'] <= iso(T0) and s['session_id'] not in CLAIMED]

# write-off dates: payers write off late, so some claims stay open in the older age bands first
def wo_date(c):
    r = rng('wo' + c['claim_id'])
    base = dd(c['resubmitted_on']) + day(25 + r.randint(0, 45)) if c['resubmitted_on'] else dd(c['denied_on']) + day(30 + r.randint(0, 75))
    return iso(min(base, T0 - day(1)))
WO = {c['claim_id']: wo_date(c) for c in CL if c['status'] == 'Written off'}
def closed_on(c):
    if c['paid_on']: return c['paid_on']
    return WO.get(c['claim_id'], '')
def pay_days(c): return (dd(c['paid_on']) - dd(c['submitted_on'])).days

# ---------- claims
CLAIM_KEEP = []
for i, c in enumerate(CL):
    if c['submitted_on'] >= ago(100) or c['denied_on'] or c['status'] in ('Submitted', 'Resubmitted', 'Written off', 'Denied') or i % 22 == 0: CLAIM_KEEP.append(c)
KEEP_IDS = {c['claim_id'] for c in CLAIM_KEEP}
CLD = {c['claim_id']: c for c in CLAIM_KEEP}
def claims_d():
    rows = []
    for c in CLAIM_KEEP:
        rows.append(nb(dict(claim_id=c['claim_id'], session_id=c['session_id'], date=c['date'], client_id=c['client_id'], client=c['client'], payer=key('payer', c['payer']), service=key('svc', c['service']),
                            clinician=key('clin', c['clinician']), amount=c['amount'], submitted_on=c['submitted_on'], status=key('clmst', c['status']),
                            denial_reason=key('denial', c['denial_reason']) if c['denial_reason'] else '', denied_on=c['denied_on'], resubmitted_on=c['resubmitted_on'], paid_on=c['paid_on'],
                            paid_amount=c['paid_amount'] or '', written_off=c['written_off'] or '')))
    return front(rows, lambda r: r['status'] == key('clmst', 'Paid') and r.get('denied_on') and r.get('resubmitted_on') and r.get('paid_on') and r['date'] >= ago(200))

# ---------- payer sessions (last 100 days) and sessions not yet claimed
def sessions_d():
    rows = [nb(dict(session_id=s['session_id'], date=s['date'], client_id=s['client_id'], client=s['client'], payer=key('payer', s['payer']), service=key('svc', s['service']), clinician=key('clin', s['clinician']),
                    status=key('sstatus', s['status']), fee=s['fee'], charge=s['charge'], payer_amount=s['payer_amount'], client_amount=s['client_amount']))
            for s in PS_ALL if ago(100) <= s['date'] <= iso(T0) and s['status'] != 'Scheduled']
    return front(rows, lambda r: r['status'] == key('sstatus', 'Attended') and r['client_amount'] > 0)

def unsub_d():
    rows = [nb(dict(session_id=s['session_id'], date=s['date'], client_id=s['client_id'], client=s['client'], payer=key('payer', s['payer']), clinician=key('clin', s['clinician']), payer_amount=s['payer_amount'])) for s in UNC]
    rows.sort(key=lambda r: r['date'])
    return front(rows, lambda r: r['date'] <= ago(20))

# ---------- pre-submission checks
def checks_d():
    rows = []; i = 0
    for c in CLAIM_KEEP:
        if c['submitted_on'] < ago(62): continue
        r = rng('ck' + c['claim_id']); i += 1
        det = not (c['denial_reason'] == 'Missing details' and r.random() > .15) and r.random() > .03
        app = not (c['denial_reason'] in ('Needs pre-approval', 'Limit reached') and r.random() > .1) and r.random() > .04
        ses = r.random() > .03
        by = COORDINATOR if r.random() < .88 else OWNER
        rows.append(dict(claim_id=c['claim_id'], checked_on=iso(max(dd(c['date']), dd(c['submitted_on']) - day(1 if r.random() < .3 else 0))), details_ok=yn(det), session_ok=yn(ses), approval_ok=yn(app), checked_by=by))
    rows.sort(key=lambda x: (x['checked_on'], x['claim_id']))
    for k, x in enumerate(rows, 1): x['check_id'] = 'PS-%04d' % k
    rows = [dict(check_id=x.pop('check_id'), **x) for x in rows]
    return front(rows, lambda r: r['details_ok'] == 'yes' and r['session_ok'] == 'yes' and r['approval_ok'] == 'yes')

# ---------- approvals (one row per payer client: the current or last approval period)
_ATT = collections.defaultdict(list)
for s in PS_ALL:
    if s['status'] == 'Attended': _ATT[s['client_id']].append(s['date'])
_PLEN = {'Payer A': 365, 'Payer B': 182, 'Payer C': 365, 'Payer D': 182}
def _approvals():
    out = []
    for cid, c in PAYCLI.items():
        if cid == ST['denied_client_id']: continue
        act = c['status'] in ('Active', 'Booked', 'On hold')
        if not act and not (c['last_session'] and c['last_session'] >= ago(300)): continue
        if not c['first_session']: continue
        r = rng('av' + cid); L = _PLEN[c['payer']]
        p0 = dd(c['first_session']) - day(3 + r.randint(0, 10))
        ref = T0 if act else dd(c['last_session'])
        k = max(0, (ref - p0).days // L); start = p0 + day(k * L)
        end = start + day(L - 1)
        if not act and c['discharge_date']: end = min(end, dd(c['discharge_date']))
        used = sum(1 for d in _ATT.get(cid, []) if iso(start) <= d <= iso(min(end, T0)))
        appr = max(12, int(((used + r.randint(3, 12)) + 3) // 4 * 4))
        out.append(dict(client_id=cid, client=c['client'], payer=c['payer'], clinician=c['clinician'], start=start, end=end, used=used, approved=appr, act=act, r=r))
    # engineered cases: approvals about to run out, and two active clients whose approval already ended
    act = sorted([o for o in out if o['act'] and o['used'] >= 8 and o['end'] > T0], key=lambda o: -o['used'])
    for o in act[:7]: o['approved'] = o['used'] + o['r'].choice([2, 3, 4])
    ended = [o for o in out if o['act'] and o['end'] > T0 and o['used'] >= 3][-60:]
    for o, back in zip(ended[5:7], (5, 12)):
        o['end'] = T0 - day(back); o['start'] = o['end'] - day(_PLEN[o['payer']] - 1)
        o['used'] = sum(1 for d in _ATT.get(o['client_id'], []) if iso(o['start']) <= d <= iso(o['end'])); o['approved'] = max(12, (o['used'] + 4) // 4 * 4)
    out.sort(key=lambda o: (o['start'], o['client_id']))
    for i, o in enumerate(out, 1): o['approval_id'] = 'AV-%04d' % i
    return out
APPR = _approvals()
AV_BY = {o['client_id']: o for o in APPR}
def approvals_d():
    rows = [nb(dict(approval_id=o['approval_id'], client_id=o['client_id'], client=o['client'], payer=key('payer', o['payer']), clinician=key('clin', o['clinician']), approved_on=iso(o['start']),
                    sessions_approved=o['approved'], valid_until=iso(o['end']), sessions_used=o['used'])) for o in APPR]
    return front(rows, lambda r: dd(r['valid_until']) > T0 + day(40) and 4 <= r['sessions_used'] < r['sessions_approved'] - 4)

# ---------- payer clients
def clients_d():
    rows = []
    for cid, c in sorted(PAYCLI.items()):
        rows.append(nb(dict(client_id=cid, client=c['client'], payer=key('payer', c['payer']), clinician=key('clin', c['clinician']), first_session=c['first_session'], status=key('cstatus', c['status']),
                            sessions_attended=c['sessions_attended'], approval_valid_until=iso(AV_BY[cid]['end']) if cid in AV_BY else '', phone=c['phone'])))
    return front(rows, lambda r: r['status'] == key('cstatus', 'Active') and r.get('approval_valid_until') and r['sessions_attended'] > 10)

# ---------- denials
def denials_d():
    rows = []
    for c in CLAIM_KEEP:
        if not c['denied_on']: continue
        r = rng('dn' + c['claim_id'])
        fx = ''
        if c['resubmitted_on']: fx = iso(max(dd(c['denied_on']) + day(1), dd(c['resubmitted_on']) - day(r.randint(0, 2))))
        rows.append(nb(dict(claim_id=c['claim_id'], denied_on=c['denied_on'], payer=key('payer', c['payer']), reason=key('denial', c['denial_reason']), fixed_on=fx, resubmitted_on=c['resubmitted_on'])))
    rows.sort(key=lambda x: (x['denied_on'], x['claim_id']))
    for k, x in enumerate(rows, 1): x['denial_id'] = 'DN-%04d' % k
    rows = [dict(denial_id=x.pop('denial_id'), **x) for x in rows]
    return front(rows, lambda r: r.get('resubmitted_on') and r.get('fixed_on') and CLD[r['claim_id']]['status'] == 'Paid' and r['denied_on'] >= ago(200))

# ---------- claim follow-ups
def followups_d():
    rows = []
    for c in CLAIM_KEEP:
        sub = dd(c['submitted_on']); r = rng('fu' + c['claim_id'])
        open_ = c['status'] in ('Submitted', 'Resubmitted')
        late = c['paid_on'] and pay_days(c) > 31 and c['submitted_on'] >= ago(280)
        if not (late or (open_ and (T0 - sub).days >= 26)): continue
        if late and r.random() > .78: continue
        first = sub + day(28 + r.randint(0, 6))
        stop = T0 - day(1) if open_ else dd(c['paid_on']) - day(1)
        d = first; n = 0
        while d <= stop and n < 3:
            ans = r.choice(['Being processed', 'Being processed', 'Paid soon', 'Needs more details', 'No answer'])
            rows.append(dict(claim_id=c['claim_id'], chased_on=iso(d), method=key('fmethod', r.choice(['Phone', 'Phone', 'Email', 'Online portal'])), answer=key('fanswer', ans), next_step_date=iso(d + day(r.choice([7, 10, 14])))))
            d = d + day(r.choice([9, 11, 14])); n += 1
    # a few open claims were chased this week
    opens = sorted({r['claim_id'] for r in rows if CLD[r['claim_id']]['status'] in ('Submitted', 'Resubmitted')})
    for j, cid in enumerate(opens):
        if j % 3 == 0:
            rows.append(dict(claim_id=cid, chased_on=ago(1 + j % 5), method=key('fmethod', 'Phone'), answer=key('fanswer', 'Being processed'), next_step_date=ahead(7)))
    rows.sort(key=lambda x: (x['chased_on'], x['claim_id']))
    seen = set(); out = []
    for x in rows:
        k = (x['claim_id'], x['chased_on'])
        if k in seen: continue
        seen.add(k); out.append(x)
    out = out[-190:] if len(out) > 190 else out
    for k, x in enumerate(out, 1): x['followup_id'] = 'FU-%04d' % k
    out = [dict(followup_id=x.pop('followup_id'), **x) for x in out]
    return front(out, lambda r: CLD[r['claim_id']]['status'] == 'Paid' and r['chased_on'] >= ago(200))

# ---------- benefits checks
def benefits_d():
    rows = []
    for b in benefit_check_rows():
        c = CLM[b['client_id']]; r = rng('bl' + b['check_id'])
        chk = dd(b['checked_on'])
        if b['payer'] and c['first_session'] and r.random() < .09 and dd(c['first_session']) + day(3) <= T0: chk = dd(c['first_session']) + day(r.randint(1, 5))
        rows.append(nb(dict(check_id=b['check_id'], client_id=b['client_id'], client=b['client'], phone=c['phone'], payer=key('payer', b['payer']) if b['payer'] else '', service=key('svc', b['service']),
                            first_session=c['first_session'], checked_on=iso(chk), checked_by=b['checked_by'], session_limit=b['session_limit'] or '', pre_approval_needed=yn(b['pre_approval_needed'] == 'Yes'),
                            client_share=b['client_share'], result=key('benres', b['result']), self_pay_fee=b['self_pay_fee'])))
    return front(rows, lambda r: r.get('payer') and r['result'] == key('benres', 'Needs pre-approval') and r['checked_on'] <= r['first_session'] and r['checked_on'] >= ago(300))

# ---------- write-offs
_WMAP = {'Duplicate claim': 'Duplicate claim', 'Not covered': 'Denied, not fixable', 'Limit reached': 'Denied, not fixable', 'Late submission': 'Not resubmitted in time',
         'Missing details': 'Payer would not pay', 'Needs pre-approval': 'Payer would not pay'}
def writeoffs_d():
    rows = []
    for c in CLAIM_KEEP:
        if c['status'] != 'Written off': continue
        r = rng('wr' + c['claim_id']); reason = _WMAP[c['denial_reason']]
        if c['amount'] <= 72 and r.random() < .35: reason = 'Small balance'
        rows.append(dict(claim_id=c['claim_id'], date=WO[c['claim_id']], payer=key('payer', c['payer']), amount=c['written_off'], reason=key('wreason', reason), approved_by=OWNER if c['amount'] >= 90 or r.random() < .3 else COORDINATOR))
    rows.sort(key=lambda x: (x['date'], x['claim_id']))
    for k, x in enumerate(rows, 1): x['writeoff_id'] = 'WO-%03d' % k
    return [dict(writeoff_id=x.pop('writeoff_id'), **x) for x in rows]

# ---------- remittances: one row per payer and week of payments
def remits_d():
    grp = collections.defaultdict(list)
    for c in CL:
        if c['paid_on'] and c['paid_on'] >= iso(month_start(13)): grp[(c['payer'], iso(week_start(dd(c['paid_on']))))].append(c)
    rows = []
    for (p, wk), cs in grp.items():
        d = min(T0, dd(wk) + day(4)); amt = round(sum(c['paid_amount'] for c in cs), 2)
        rows.append(dict(date=iso(d), payer=key('payer', p), claims_paid=len(cs), amount=amt, matched_amount=amt))
    rows.sort(key=lambda x: (x['date'], x['payer']))
    rr = rng('remit-gap')
    recent = [x for x in rows if x['date'] >= ago(60) and x['claims_paid'] >= 3]; older = [x for x in rows if ago(140) <= x['date'] < ago(60) and x['claims_paid'] >= 3]
    for x, delta in zip(rr.sample(recent, 3) + rr.sample(older, 3), (-96.0, 64.5, -108.0, 41.25, -85.0, 72.0)):
        x['matched_amount'] = round(x['amount'] + delta, 2)
    for k, x in enumerate(rows, 1): x['remit_id'] = 'RT-%04d' % k
    rows = [dict(remit_id=x.pop('remit_id'), **x) for x in rows]
    return front(rows, lambda r: r['claims_paid'] >= 5 and r['matched_amount'] != r['amount'] and r['date'] >= ago(200)) if False else front(rows, lambda r: r['claims_paid'] >= 6 and r['matched_amount'] == r['amount'] and r['date'] >= ago(200))

# ---------- payer enrolment
def enrol_d():
    rows = [nb(dict(enrolment_id=e['enrolment_id'], payer=key('payer', e['payer']), clinician=key('clin', e['clinician']), application_sent=e['application_sent'], effective_date=e['effective_date'],
                    renewal_due=e['renewal_due'], status=key('enrolst', e['status']))) for e in payer_enrolment_rows()]
    done = [r for r in rows if r['status'] == key('enrolst', 'Enrolled') and r.get('renewal_due')]
    for r in sorted(done, key=lambda r: r['renewal_due'])[:2]: r['status'] = key('enrolst', 'Renewal due')
    return rows

# ---------- receipts for claim back
def receipts_d():
    rows = [nb(dict(receipt_id=s['statement_id'], month=s['month'], client_id=s['client_id'], client=s['client'], phone=CLM[s['client_id']]['phone'], sessions=s['sessions'], amount_paid=s['amount_paid'], issued_on=s['issued_on']))
            for s in client_statement_rows() if s['issued_on'] <= iso(T0)]
    return front(rows, lambda r: r['sessions'] >= 3 and r['issued_on'] >= ago(200))

# ---------- self-pay cost estimates
def estimates_d():
    rr = rng('est'); SV_ = {s['service']: s for s in services}
    pool = [c for c in CLI if c['fee_type'] in ('Standard', 'Sliding scale') and c['booked_on'] >= ago(300) and c['booked_on'] <= iso(T0)]
    pick = sorted(rr.sample(pool, 30), key=lambda c: c['booked_on'])
    rows = []
    for i, c in enumerate(pick, 1):
        fee = round(SV_[c['service']]['fee'] * c['sliding_pct'])
        n = rr.choice([6, 8, 10, 12, 12, 16, 20, 24])
        rows.append(nb(dict(estimate_id='EC-%03d' % i, client_id=c['client_id'], client=c['client'], phone=c['phone'], service=key('svc', c['service']), fee=fee, expected_sessions=n,
                            late_rule=key('lcrule', rr.choice(LCRULE)), deposit=rr.choice([0, 25, 30, 40, 50, 50, 60, 75]), package=key('pkopt', 'No package' if n < 6 else rr.choice(['No package', '6 sessions', '10 sessions'] if n >= 10 else ['No package', '6 sessions'])),
                            sliding_pct=c['sliding_pct'], issued_on=iso(max(dd(c['booked_on']) - day(3), HISTORY_START)))))
    return front(rows, lambda r: r['expected_sessions'] >= 12 and r['package'] != key('pkopt', 'No package') and r['sliding_pct'] < 1)

# ---------- monthly claims summary and A/R aging (full data)
MONTHS = [month_start(k) for k in range(23, -1, -1)]
def monthly_d():
    att = collections.Counter(); cla = collections.Counter()
    for s in SES:
        if s['status'] == 'Attended' and s['date'] <= iso(T0):
            att[s['month']] += 1
            if s['fee_type'] == 'Third-party payer' and s['payer_amount'] > 0: cla[s['month']] += 1
    sub = collections.defaultdict(list); paid = collections.defaultdict(list); wo = collections.Counter(); sh = collections.Counter(); rec = collections.Counter()
    for c in CL:
        sub[mon(c['submitted_on'])].append(c)
        if c['paid_on']:
            paid[mon(c['paid_on'])].append(c)
            if c['status'] == 'Partly paid': sh[mon(c['paid_on'])] += c['amount'] - c['paid_amount']
        if c['status'] == 'Written off': wo[mon(WO[c['claim_id']])] += c['written_off']
    for s in client_statement_rows():
        if s['issued_on'] <= iso(T0): rec[mon(s['issued_on'])] += 1
    rows = []
    for m in MONTHS:
        k = iso(m); cs = sub[k]; ps = paid[k]
        rows.append(dict(month=k, attended_sessions=att[k], claimable_sessions=cla[k], claims_submitted=len(cs), clean_claims=sum(1 for c in cs if not c['denied_on']), claimed=round(sum(c['amount'] for c in cs), 2),
                         paid=round(sum(c['paid_amount'] for c in ps), 2), avg_days_to_pay=round(sum(pay_days(c) for c in ps) / len(ps), 1) if ps else 0, written_off=round(wo[k], 2),
                         short_paid=round(sh[k], 2), receipts=rec[k]))
    return rows

def aging_d():
    rows = []
    for m in months14():
        asof = T0 if m == dt.date(T0.year, T0.month, 1) else add_months(m, 1) - day(1)
        a = iso(asof); acc = {(p, b): [0, 0.0] for p in PAYERS for b in AGE_BANDS}
        for c in CL:
            if c['submitted_on'] > a: continue
            cl = closed_on(c)
            if cl and cl <= a: continue
            days = (asof - dd(c['submitted_on'])).days
            b = AGE_BANDS[0] if days <= 30 else AGE_BANDS[1] if days <= 60 else AGE_BANDS[2] if days <= 90 else AGE_BANDS[3]
            acc[(c['payer'], b)][0] += 1; acc[(c['payer'], b)][1] += c['amount']
        for p in PAYERS:
            for b in AGE_BANDS: rows.append(dict(month=iso(m), as_of=a, payer=key('payer', p), band=key('ageband', b), claims=acc[(p, b)][0], amount=round(acc[(p, b)][1], 2)))
    for i, x in enumerate(rows, 1): x['ageing_id'] = 'AP-%03d' % i
    return [dict(ageing_id=x.pop('ageing_id'), **x) for x in rows]

# ---------- reference tables
def payers_d(): return [dict(payer=p['payer'], fee_share=p['fee_share'], copay=p['copay']) for p in payers] + [dict(payer='Payer E', fee_share=0.75, copay=20)]
FIX = [('Missing details', 'Add missing details, send again', 3), ('Not covered', 'Check cover, else bill self-pay fee', 7), ('Limit reached', 'New approval or self-pay fee', 10),
       ('Late submission', 'Send proof of first submission', 5), ('Duplicate claim', 'Withdraw the duplicate claim', 2), ('Needs pre-approval', 'Get pre-approval, then resubmit', 14)]
def fixes_d(): return [dict(reason=key('denial', r), usual_fix=f, days_to_fix=d) for r, f, d in FIX]
def services_d(): return [dict(service=s['service'], minutes=s['minutes'], fee=s['fee']) for s in services]
def team_d():
    return [nb(dict(staff_id=s['staff_id'], name=s['name'], role=s['role'], team=s['team'], pay_type=s['pay_type'], phone=s['phone'], email=s['email'], hours_week=s['hours_week'],
                    monthly_salary=s['monthly_salary'], split_pct=s['split_pct'], session_rate=s['session_rate'], hourly_rate=s['hourly_rate'], session_cap=s['session_cap'], session_target=s['session_target'],
                    speciality=s['speciality'], country=s['country'], start=s['start'])) for s in team]

if __name__ == '__main__':
    for f in (claims_d, sessions_d, unsub_d, checks_d, approvals_d, denials_d, followups_d, benefits_d, writeoffs_d, remits_d, enrol_d, receipts_d, clients_d, estimates_d, monthly_d, aging_d, payers_d, fixes_d, services_d, team_d):
        print(f.__name__, len(f()))
