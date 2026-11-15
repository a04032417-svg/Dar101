"""Therapy part 2: demo rows from th_core (full generator output for aggregated tables, windows of recent rows for row-level logs)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th2_lists import *
import th_core as C
import collections

dd = to_date
TS = iso(TODAY)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(v): return 'yes' if v in ('Yes', True, 'yes') else 'no'
def wk(d): return iso(week_start(dd(d)))
def hr(t): return int(t[:2])

S_ALL = session_rows()
CL = {c['client_id']: c for c in client_rows()}
PH = {c['client_id']: c['phone'] for c in CL.values()}
ST = story()


def reason(s):
    r = s['cancel_reason']
    if s['status'] == 'Cancelled' and r in ('Work clash', 'Travel', 'Childcare') and int(s['session_id'][3:]) % 5 < 2: return 'Rescheduled by client'
    return r


def late_fee(s): return s['fee'] * LATE_FEE_PCT if s['status'] in ('Late cancel', 'No-show') else 0.0


# ---------------- sessions (recent window)
def sessions_d():
    out = []
    for s in S_ALL:
        if not (ago(30) <= s['date'] <= ahead(14)): continue
        out.append(nb(dict(session_id=s['session_id'], date=s['date'], time=s['time'], weekday=key('wday', s['weekday']), client_id=s['client_id'], client=s['client'], phone=PH.get(s['client_id'], ''),
                           client_type=key('ctype', s['client_type']), service=key('svc', s['service']), clinician=key('clin', s['clinician']), format=key('fmt', s['format']), room=key('room', s['room']),
                           minutes=s['minutes'], status=key('sstatus', s['status']), cancel_reason=key('creason', reason(s)) if reason(s) else '', fee_waived=yn(s['fee_waived']), fee=s['fee'])))
    return out


def diary_d():
    return [nb(dict(slot_id=x['slot_id'], week=x['week'], date=x['date'], weekday=key('wday', x['weekday']), time=x['time'], clinician=key('clin', x['clinician']), status=key('slotst', x['status']),
                    client=x['client'], service=key('svc', x['service']) if x['service'] else '', room=key('room', x['room']) if x['room'] else '')) for x in slot_rows()]


# ---------------- clinician weeks (all history, aggregated from the full session list)
def _b2b():
    """sessions whose clinician has another non-cancelled session starting one hour earlier the same day"""
    have = set((s['clinician'], s['date'], hr(s['time'])) for s in S_ALL if s['status'] != 'Cancelled')
    return have


_HAVE = _b2b()
def is_b2b(s): return s['status'] != 'Cancelled' and (s['clinician'], s['date'], hr(s['time']) - 1) in _HAVE


def clin_weeks_d():
    agg = collections.defaultdict(lambda: collections.Counter())
    for s in S_ALL:
        a = agg[(s['clinician'], wk(s['date']))]; st = s['status']
        if st != 'Cancelled': a['booked'] += 1
        if st == 'Attended': a['attended'] += 1
        if st == 'Cancelled': a['cancelled'] += 1
        if st == 'Late cancel': a['late'] += 1
        if st == 'No-show': a['noshow'] += 1
        if st == 'Cancelled' and reason(s) == 'Rescheduled by client': a['resched'] += 1
        if st != 'Cancelled' and s['format'] != 'In person': a['online'] += 1
        if is_b2b(s): a['b2b'] += 1
        if s['date'] <= TS and st != 'Cancelled': a['sent'] += 1
        a['feec'] += late_fee(s) * (0 if s['fee_waived'] == 'Yes' else 1); a['feew'] += late_fee(s) * (1 if s['fee_waived'] == 'Yes' else 0)
    away = {(x['clinician'], x['week']): x['days'] for x in absence_rows()}
    r = rng('p2weeks'); out = []; n = 0
    w0 = week_start(HISTORY_START); wl = week_start(TODAY) + day(35)
    for nm in CLINICIANS:
        st = staff_by_name[nm]; w = max(w0, week_start(to_date(st['start'])))
        while w <= wl:
            wi = iso(w); a = agg.get((nm, wi), collections.Counter()); n += 1
            da = 5 if C._closed(w) else away.get((nm, wi), 0)
            conf = int(round(a['sent'] * r.uniform(0.72, 0.86)))
            out.append(dict(cw_id='CW-%04d' % n, week=wi, clinician=key('clin', nm), cap=st['session_cap'], booked=a['booked'], attended=a['attended'], cancelled=a['cancelled'], late_cancels=a['late'],
                            no_shows=a['noshow'], rescheduled=a['resched'], online=a['online'], back_to_back=a['b2b'], days_away=da, reminders_sent=a['sent'], reminders_confirmed=conf,
                            late_fees=round(a['feec'], 2), fees_waived=round(a['feew'], 2)))
            w += day(7)
    return out


# ---------------- caseload
def _usual(cid):
    ss = [s for s in S_ALL if s['client_id'] == cid]
    return ss
_BYCL = collections.defaultdict(list)
for _s in S_ALL: _BYCL[_s['client_id']].append(_s)


def caseload_d():
    out = []
    for c in client_rows():
        if c['status'] not in ('Booked', 'Active', 'On hold'): continue
        ss = sorted(_BYCL.get(c['client_id'], []), key=lambda s: s['date'])
        ref = ss[-1] if ss else None
        if ref: w, t = ref['weekday'], ref['time']
        else:
            w = WEEKDAYS[dd(c['first_session']).weekday()]; t = '10:00'
        if w == 'Sunday': w = 'Monday'
        out.append(nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], clinician=key('clin', c['clinician']), service=key('svc', c['service']), frequency=key('freq', c['frequency']),
                           format=key('fmt', c['format']), weekday=key('wday', w), time=t, booked_on=c['booked_on'], first_session=c['first_session'], last_session=c['last_session'],
                           next_session=c['next_session'], client_status=key('cstatus', c['status']))))
    return out


def cancels_d():
    r = rng('p2cancel'); out = []
    for s in S_ALL:
        if s['status'] not in ('Cancelled', 'Late cancel', 'No-show') or not (ago(150) <= s['date'] <= TS): continue
        st = s['status']; hrs = r.randint(25, 160) if st == 'Cancelled' else (r.randint(1, 23) if st == 'Late cancel' else 0)
        rb = ''
        p = {'Cancelled': .85 if reason(s) == 'Rescheduled by client' else .62, 'Late cancel': .5, 'No-show': .4}[st]
        if r.random() < p:
            d = dd(s['date']) + day(r.randint(1, 12 if reason(s) != 'Rescheduled by client' else 6))
            rb = iso(d) if d <= TODAY else ''
        out.append(nb(dict(session_id=s['session_id'], date=s['date'], client=s['client'], phone=PH.get(s['client_id'], ''), clinician=key('clin', s['clinician']), status=key('sstatus', st),
                           cancel_reason=key('creason', reason(s)) if reason(s) else '', notice_hours=hrs, fee=s['fee'], fee_waived=yn(s['fee_waived']), rebooked_on=rb)))
    return out


WREASON = ['First late cancel', 'Illness reported', 'Family emergency', 'Transport failed', 'Practice error', 'Long-standing client', 'Online link problem']
def waivers_d():
    r = rng('p2waive'); rows = [s for s in S_ALL if s['status'] in ('Late cancel', 'No-show') and s['fee_waived'] == 'Yes' and s['date'] <= TS][-100:]
    out = []
    for i, s in enumerate(rows, 1):
        by = r.choices(['Grace Mensah', 'Amira Lindqvist', s['clinician']], [5, 3, 2])[0]
        out.append(dict(waiver_id='WV-%03d' % i, session_id=s['session_id'], date=s['date'], client=s['client'], fee=s['fee'], waived_by=by, reason=r.choice(WREASON)))
    return out


WANTS = ['Earlier time', 'Extra session', 'Different day', 'Evening slot', 'Saturday slot', 'Same time, other clinician']
PDAYS = ['Weekday mornings', 'Tuesday or Thursday', 'After 17:00', 'Saturday morning', 'Any weekday', 'Monday to Wednesday']
def cancel_list_d():
    r = rng('p2clist'); act = [c for c in client_rows() if c['status'] == 'Active']; r.shuffle(act); out = []
    for i, c in enumerate(act[:42], 1):
        added = r.randint(1, 120); off = ''
        if r.random() < .55: off = iso(TODAY - day(max(0, added - r.randint(1, 14))))
        filled = 'yes' if off and r.random() < .6 else 'no'
        out.append(nb(dict(list_id='CN-%03d' % i, client=c['client'], phone=c['phone'], clinician=key('clin', c['clinician']), service=key('svc', c['service']), wants=r.choice(WANTS),
                           preferred_days=r.choice(PDAYS), added_on=ago(added), offered_on=off, filled=filled)))
    return out


def reminders_d():
    r = rng('p2remind'); out = []; n = 0
    for s in S_ALL:
        if s['status'] == 'Cancelled' or not (ago(21) <= s['date'] <= ahead(4)): continue
        lead = r.choice([1, 2, 2, 2, 3]); so = dd(s['date']) - day(lead)
        if so > TODAY: continue
        n += 1; sh = r.choice([8, 9, 10, 11, 14, 15, 16, 17])
        conf = r.random() < (0.82 if s['status'] == 'Attended' else 0.2 if s['status'] in ('No-show',) else 0.6)
        out.append(dict(reminder_id='RE-%04d' % n, session_id=s['session_id'], date=s['date'], time=s['time'], client=s['client'], phone=PH.get(s['client_id'], ''),
                        channel=key('chan', r.choice(['Text message', 'Text message', 'Text message', 'E-mail', 'Phone call'])), sent_on=iso(so), sent_time='%02d:00' % sh, confirmed='yes' if conf else 'no'))
    return out


def online_d():
    r = rng('p2online'); rows = [s for s in S_ALL if s['format'] != 'In person' and s['status'] != 'Cancelled' and s['date'] <= ahead(7)][-300:]; out = []
    for s in rows:
        fut = s['date'] > TS
        sent = 'yes' if (not fut and r.random() < .97) or (fut and (dd(s['date']) - TODAY).days <= 3 and r.random() < .9) else 'no'
        prob = (not fut) and r.random() < .06
        out.append(dict(session_id=s['session_id'], date=s['date'], client=s['client'], phone=PH.get(s['client_id'], ''), clinician=key('clin', s['clinician']), service=key('svc', s['service']),
                        minutes=s['minutes'], details_sent=sent, connection_problem='yes' if prob else 'no', minutes_lost=r.randint(5, 20) if prob else 0))
    return out


def room_bookings_d():
    rows = []
    for s in S_ALL:
        if s['room'] == 'Online' or s['status'] == 'Cancelled' or not (TS <= s['date'] <= ahead(27)): continue
        rows.append((s['date'], s['time'], s['room'], key('clin', s['clinician']), key('svc', s['service']), 'Client session', s['minutes']))
    taken = set((x[0], x[1], x[2]) for x in rows)
    for g in group_rows():
        if g['status'] not in ('Running', 'Open for sign-up', 'Planned'): continue
        st = dd(g['start_date'])
        for k in range(g['weeks']):
            d = st + day(7 * k)
            if TODAY <= d <= TODAY + day(27) and (iso(d), g['start_time'], g['room']) not in taken:
                rows.append((iso(d), g['start_time'], g['room'], key('clin', g['facilitator']), '', 'Group program', 90)); taken.add((iso(d), g['start_time'], g['room']))
    pat = {'TN-01': [(1, 18), (3, 18)], 'TN-02': [(2, 18)], 'TN-03': [(5, 9)]}
    for t in tenants:
        for wd, h in pat[t['tenant_id']]:
            for w in range(5):
                d = week_start(TODAY) + day(7 * w + wd)
                if TODAY <= d <= TODAY + day(27) and (iso(d), '%02d:00' % h, t['room']) not in taken:
                    rows.append((iso(d), '%02d:00' % h, t['room'], '', '', 'Sublet', 120 if t['hours_week'] > 3 else 180)); taken.add((iso(d), '%02d:00' % h, t['room']))
    rows.sort()
    return [nb(dict(booking_id='RB-%04d' % i, date=a, time=b, room=key('room5', c), clinician=cl, service=sv, use=u, minutes=m)) for i, (a, b, c, cl, sv, u, m) in enumerate(rows, 1)]


RKIND = {'Garden Room': 'Adult room'}
def rooms_d(): return [dict(room=key('room5', x['room']), kind=x['kind'], open_hours_week=x['open_hours_week']) for x in rooms]


def room_rules_d():
    cnt = collections.defaultdict(collections.Counter); kind = {x['room']: x['kind'] for x in rooms}
    for s in S_ALL:
        if s['room'] != 'Online': cnt[s['service']][kind[s['room']]] += 1
    buf = {'Child session': 15, 'Behaviour therapy': 15, 'Speech therapy': 15, 'Family session': 15, 'Couples session': 10}
    return [dict(service=key('svc', sv), room_kind=cnt[sv].most_common(1)[0][0] if cnt[sv] else 'Adult room', buffer_minutes=buf.get(sv, 10)) for sv in SESSION_SERVICES]


def room_months_d():
    return [dict(row_id=x['row_id'], month=x['month'], room=key('room5', x['room']), open_hours=x['open_hours'], session_hours=x['session_hours'], group_hours=x['group_hours'],
                 sublet_hours=x['sublet_hours'], sessions=x['sessions']) for x in room_month_rows()]


def busy_d():
    held = collections.Counter(); ns = collections.Counter(); free = collections.Counter()
    for s in S_ALL:
        if ago(84) <= s['date'] < TS and s['status'] in ('Attended', 'Late cancel', 'No-show') and s['weekday'] != 'Sunday':
            held[(s['weekday'], hr(s['time']))] += 1
            if s['status'] == 'No-show': ns[(s['weekday'], hr(s['time']))] += 1
    for x in slot_rows():
        if x['status'] == 'Free' and TS < x['date'] <= ahead(28) and x['weekday'] != 'Sunday': free[(x['weekday'], hr(x['time']))] += 1
    out = []; n = 0
    for w in WORKDAYS:
        for h in range(8, 21):
            n += 1; out.append(dict(bt_id='BT-%02d' % n, weekday=key('wday', w), time='%02d:00' % h, sessions_12w=held[(w, h)], no_shows=ns[(w, h)], free_slots=free[(w, h)]))
    return out


def absences_d():
    return [nb(dict(absence_id=x['absence_id'], week=x['week'], clinician=key('clin', x['clinician']), kind=key('absk', x['kind']), days=x['days'], sessions_moved=x['sessions_moved'],
                    cover_by=key('clin', x['cover_by']) if x['cover_by'] else '')) for x in absence_rows()]


def rebook_d():
    r = rng('p2rebook'); out = []; iv = {'Weekly': 7, 'Fortnightly': 14, 'Monthly': 28}
    for c in client_rows():
        if c['status'] not in ('Active', 'On hold') or not c['last_session']: continue
        gap = (dd(c['next_session']) - dd(c['last_session'])).days - iv[c['frequency']] if c['next_session'] else None
        if not (gap is None or gap > (2 if c['frequency'] == 'Weekly' else 7) or c['status'] == 'On hold'): continue
        called = ''; res = ''
        if gap is None and r.random() < .5: called = ago(r.randint(0, 6)); res = r.choice(['No answer', 'Left a message', 'Will call back'])
        out.append(nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], clinician=key('clin', c['clinician']), frequency=key('freq', c['frequency']), last_session=c['last_session'],
                           next_session=c['next_session'], called_on=called, result=res)))
    return out


def tenants_d():
    out = [dict(name=t['name'], room=key('room5', t['room']), rate=t['rate']) for t in tenants]
    out += [dict(name='Rosa Fernandez', room=key('room5', 'Willow Room'), rate=22.0), dict(name='Idris Okafor', room=key('room5', 'Quiet Room'), rate=21.0)]
    return out
def sublets_d():
    return [nb(dict(sublet_id=x['sublet_id'], month=x['month'], tenant=x['tenant'], room=key('room5', x['room']), hours=x['hours'], rate=x['rate'], amount=x['amount'], invoiced_on=x['invoiced_on'],
                    paid_on=x['paid_on'])) for x in sublet_rows()] + _sub_extra()
def _sub_extra():
    import datetime as _d
    r = rng('p2sub2'); out = []; n = 55
    for ten, room, rate in (('Rosa Fernandez', 'Willow Room', 22.0), ('Idris Okafor', 'Quiet Room', 21.0)):
        for k in range(5, -1, -1):
            m = month_start(k); hrs = round(r.uniform(5, 15), 2)
            row = dict(sublet_id='SL-%03d' % n, month=m.isoformat(), tenant=ten, room=key('room5', room), hours=hrs, rate=rate, amount=round(hrs * rate, 2)); n += 1
            if k >= 1:
                inv = add_months(m, 1); row['invoiced_on'] = inv.isoformat(); row['paid_on'] = (inv + _d.timedelta(days=r.randint(3, 12))).isoformat()
            out.append(nb(row))
    return out
def services_d(): return [dict(service=s['service'], minutes=s['minutes'], fee=s['fee']) for s in services]
def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', ROLE2.get(t['role'], t['role'])), team=t['team'], pay_type=t['pay_type'], phone=t['phone'], email=t['email'],
                    hours_week=t['hours_week'], monthly_salary=t['monthly_salary'], split_pct=t['split_pct'], session_rate=t['session_rate'], hourly_rate=t['hourly_rate'], session_cap=t['session_cap'],
                    session_target=t['session_target'], speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]
