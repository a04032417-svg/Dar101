"""Short-term rental host suite part 2: demo rows from sr_core (full generator output for aggregated tables, rows of the chosen bookings elsewhere)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr2_lists import *
import collections

dd = to_date
R = rng('sr2')
BKF = booking_rows(); BKD = {b['booking_id']: b for b in BKF}
POF = payout_rows(); POB = {p['booking_id']: p for p in POF}
UNI = {u['unit_id']: u for u in units}
OWNP = {o['name']: o['phone'] for o in owners}
OWNER_PHONE = team[0]['phone']; COHOST_PHONE = team[1]['phone']
ACCT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def band(n):
    return key('band', 'Same week' if n <= 6 else 'One to two weeks' if n <= 14 else 'Two to four weeks' if n <= 28 else 'One to three months' if n <= 90 else 'Over three months')
def gphone(bid): return fake_phone(int(bid[3:]))

# ---------- same-day pairs (a check-out and a check-in on one day in one unit)
def _pairs():
    by = collections.defaultdict(list)
    for b in BKF:
        if b['status'] != 'Cancelled': by[b['unit_id']].append(b)
    out = []
    for u, l in by.items():
        l.sort(key=lambda x: x['check_in'])
        for a, c in zip(l, l[1:]):
            if a['check_out'] == c['check_in']: out.append((a, c))
    return sorted(out, key=lambda p: p[1]['check_in'])
SD_ALL = _pairs()
SD_PICK = [p for p in SD_ALL if p[1]['check_in'] >= ago(75)]
_old = [p for p in SD_ALL if p[1]['check_in'] < ago(75)]
_need = max(0, 72 - len(SD_PICK)); SD_PICK += _old[::max(1, len(_old) // max(1, _need))][:_need]
SD_PICK.sort(key=lambda p: p[1]['check_in'])

# ---------- chosen bookings (every recent, upcoming, cancelled and problem-payout booking, plus a thinned older sample)
PROBLEM = {p['booking_id'] for p in POF if p['status'] in ('Short paid', 'Missing')}
MUST = {b['booking_id'] for b in BKF if b['check_in'] >= ago(75) or b['booked_on'] >= ago(45) or b['status'] == 'Cancelled'} | PROBLEM
for a, c in SD_PICK: MUST |= {a['booking_id'], c['booking_id']}
_rest = [b for b in BKF if b['booking_id'] not in MUST]
_step = max(1, round(len(_rest) / max(1, 520 - len(MUST))))
CHOSEN = sorted(MUST | {b['booking_id'] for b in _rest[::_step]})
BK = [BKD[i] for i in sorted(CHOSEN, key=lambda i: (BKD[i]['check_in'], i))]
IDS = {b['booking_id'] for b in BK}
NONC = [b for b in BK if b['status'] != 'Cancelled']

def bookings_d():
    out = []
    for b in BK:
        out.append(nb(dict(booking_id=b['booking_id'], unit_id=b['unit_id'], unit=b['unit'], unit_type=key('utype', UNI[b['unit_id']]['unit_type']), city=key('city', b['city']), channel=key('chan', b['channel']),
                           guest=b['guest'], guest_phone=gphone(b['booking_id']), guest_country=b['guest_country'], guests=b['guests'], check_in=b['check_in'], check_out=b['check_out'], booked_on=b['booked_on'],
                           nights=b['nights'], nightly_rate=b['nightly_rate'], room_revenue=b['room_revenue'], cleaning_fee=b['cleaning_fee'], gross=b['gross'], earned=b['earned'],
                           tax_collected=b['tax_collected'], tax_by=key('taxby', b['tax_by']), status=key('bstatus', b['status']))))
    return out

def payouts_d():
    out = []
    for b in BK:
        p = POB.get(b['booking_id'])
        if not p: continue
        out.append(nb(dict(payout_id=p['payout_id'], booking_id=p['booking_id'], channel=key('chan', p['channel']), unit=p['unit'], expected_date=p['expected_date'], paid_on=p['paid_on'],
                           expected_amount=p['expected_amount'], received_amount=p['received_amount'], status=key('payst', p['status']))))
    return sorted(out, key=lambda x: (x['expected_date'], x['payout_id']))

def cancellations_d():
    r = rng('sr2-cancel'); out = []
    w = [30, 14, 18, 6, 6, 8, 8, 10]
    for i, b in enumerate([b for b in BK if b['status'] == 'Cancelled'], 1):
        days = (dd(b['check_in']) - dd(b['cancelled_on'])).days
        reason = r.choices(CREASON, w)[0]
        out.append(nb(dict(cancel_id='CN-%03d' % i, booking_id=b['booking_id'], guest=b['guest'], guest_phone=gphone(b['booking_id']), unit=b['unit'], channel=key('chan', b['channel']), check_in=b['check_in'],
                           cancelled_on=b['cancelled_on'], room_revenue=b['room_revenue'], kept_amount=b['kept_amount'], refund_amount=b['refund_amount'], reason=key('creason', reason), notice=band(max(0, days)))))
    return out

def channels_d():
    out = [dict(channel=c['channel'], fee_pct=c['fee_pct'], payout_days=c['payout_days']) for c in channels]
    out.append(dict(channel='Direct by bank transfer', fee_pct=0.01, payout_days=-7)); return out

def cities_d():
    out = []
    for c in cities:
        for who in TAXBY: out.append(dict(city=key('city', c['city']), collected_by=key('taxby', who), tax_pct=c['tax_pct']))
    return out

def units_d():
    return [dict(unit_id=u['unit_id'], name=u['name'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), owner=u['owner'], owner_phone=OWNP[u['owner']], base_rate=u['base_rate'],
                 cleaning_fee=u['cleaning_fee'], bedrooms=u['bedrooms']) for u in units]

def seasons_d():
    return [dict(month='%d-%02d-01' % (TODAY.year, s['month_no']), season=s['season'], price_factor=s['price_factor']) for s in season_rows()]

def channel_months_d():
    acc = collections.defaultdict(lambda: [0, 0, 0.0, 0.0, 0.0, 0.0, 0])
    for b in BKF:
        k = (b['check_in'][:7], b['channel']); a = acc[k]
        if b['status'] == 'Cancelled': a[6] += 1; continue
        a[0] += 1; a[1] += b['nights']; a[2] += b['gross']; a[3] += b['platform_fee']; a[4] += b['tax_collected']; a[5] += b['net_payout']
    months = sorted({k[0] for k in acc}); out = []; n = 0
    for m in months:
        for c in CHANNELS:
            a = acc.get((m, c), [0, 0, 0.0, 0.0, 0.0, 0.0, 0])
            if not a[0] and not a[6]: continue
            n += 1; out.append(dict(cm_id='CM-%03d' % n, month=m + '-01', channel=key('chan', c), bookings=a[0], nights=a[1], gross=round(a[2], 2), platform_fees=round(a[3], 2),
                                    tax_collected=round(a[4], 2), net_payouts=round(a[5], 2), cancellations=a[6]))
    return out

def guests_d():
    g = guest_rows(); rep = sorted([x for x in g if x['stays'] >= 2], key=lambda x: x['last_stay'], reverse=True)[:95]
    one = sorted([x for x in g if x['stays'] < 2], key=lambda x: x['last_stay'], reverse=True)[:110]
    rows = sorted(rep + one, key=lambda x: x['last_stay'])
    return [dict(guest_id=x['guest_id'], guest=x['guest'], guest_phone=fake_phone(int(x['guest_id'][3:]) + 40), guest_country=x['country'], channel=key('chan', x['channel']), stays=x['stays'], nights=x['nights'],
                 spend=x['spend'], first_stay=x['first_stay'], last_stay=x['last_stay']) for x in rows]

def calendar_d():
    r = rng('sr2-cal'); times = ['14:00', '15:00', '15:00', '16:00', '16:00', '17:00', '18:30', '20:00', '22:00']; out = []
    rows = [b for b in NONC if ago(35) <= b['check_in'] <= ahead(120)]
    for i, b in enumerate(rows, 1):
        out.append(dict(checkin_id='CI-%03d' % i, booking_id=b['booking_id'], check_in=b['check_in'], check_out=b['check_out'], unit=b['unit'], guest=b['guest'], guest_phone=gphone(b['booking_id']),
                        guests=b['guests'], nights=b['nights'], arrival_time=r.choice(times), channel=key('chan', b['channel']), status=key('bstatus', b['status'])))
    return out

def chase_d():
    r = rng('sr2-chase'); out = []; n = 0
    pl = [p for p in POF if p['booking_id'] in IDS]
    late = [p for p in pl if p['paid_on'] and p['status'] == 'Paid' and (dd(p['paid_on']) - dd(p['expected_date'])).days >= 2]
    odd = [p for p in pl if p['status'] in ('Short paid', 'Missing')]
    pick = odd + late[::max(1, len(late) // 48)][:48]
    for p in sorted(pick, key=lambda p: p['expected_date']):
        e = dd(p['expected_date']); reps = [(e + dt.timedelta(days=4), 'Waiting for the platform', None), (e + dt.timedelta(days=11), 'Claim opened', None)] if p['status'] == 'Missing' else None
        if p['status'] == 'Short paid':
            c = dd(p['paid_on']) + dt.timedelta(days=1); ans = r.choice(['Difference explained', 'Claim opened', 'Amount confirmed']); res = c + dt.timedelta(days=r.randint(2, 9))
            reps = [(c, ans, res)]
        elif p['status'] == 'Paid':
            c = e + dt.timedelta(days=1); reps = [(c, r.choice(['Payment released', 'Payment released', 'Waiting for the platform']), dd(p['paid_on']))]
        for c, ans, res in reps:
            if c > TODAY: continue
            n += 1; res_ = res.isoformat() if res and res <= TODAY else ''
            out.append(nb(dict(chase_id='PC-%03d' % n, payout_id=p['payout_id'], booking_id=p['booking_id'], channel=key('chan', p['channel']), chased_on=iso(c), answer=key('canswer', ans), resolved_on=res_)))
    return out

def deposits_d():
    r = rng('sr2-dep'); out = []
    dr = [b for b in NONC if b['channel'] == 'Direct']
    rows = dr[-72:]; fut = [b for b in rows if b['check_in'] >= ahead(10)]
    overdue = {fut[0]['booking_id']: ago(4), fut[len(fut) // 2]['booking_id']: ago(9)} if len(fut) > 1 else {}
    for i, b in enumerate(rows, 1):
        dep = round(b['gross'] * 0.30, 2); due = overdue.get(b['booking_id']) or iso(dd(b['check_in']) - dt.timedelta(days=7))
        paid = '' if (due >= iso(TODAY) or b['booking_id'] in overdue) else iso(min(TODAY, dd(due) - dt.timedelta(days=r.choice([0, 0, 1, 2, 3]))))
        out.append(nb(dict(deposit_id='DD-%03d' % i, booking_id=b['booking_id'], guest=b['guest'], guest_phone=gphone(b['booking_id']), unit=b['unit'], check_in=b['check_in'], date=b['booked_on'], total_amount=b['gross'],
                           amount=dep, method=r.choice(['Card payment', 'Bank transfer', 'Card payment', 'Payment link']), due_date=due, balance_paid_on=paid)))
    return out

SRC_DIRECT = ['Direct website', 'Returning guest', 'Referral', 'Phone call', 'Local partner', 'Message to the host']
def sources_d():
    r = rng('sr2-src'); out = []
    rows = [b for b in NONC if b['channel'] == 'Direct'][-62:] + [b for b in NONC if b['channel'] != 'Direct'][-28:]
    rows.sort(key=lambda b: b['booked_on'])
    for i, b in enumerate(rows, 1):
        src = r.choices(SRC_DIRECT, [28, 24, 18, 12, 8, 10])[0] if b['channel'] == 'Direct' else 'Platform search'
        fc = dd(b['booked_on']) - dt.timedelta(days=r.choice([0, 0, 1, 2, 3, 5]))
        out.append(dict(source_id='BS-%03d' % i, booking_id=b['booking_id'], source=key('bsrc', src), channel=key('chan', b['channel']), lead_days=b['lead_days'], first_contact=iso(fc)))
    return out

FEE_TYPES = [('Booking fee', 'Earned amount of the booking'), ('Payment processing', 'Card payments on the booking'), ('Cancellation penalty', 'Host cancellations'), ('Early payout fee', 'Payout before check-in'),
             ('Promotion fee', 'Promoted listing bookings'), ('Long stay fee', 'Stays of 28 nights or more')]
def fees_d():
    r = rng('sr2-fee'); out = []; n = 0
    for c in channels:
        for i, (t, ap) in enumerate(FEE_TYPES):
            p = {'Booking fee': c['fee_pct'] if c['channel'] != 'Direct' else 0.0, 'Payment processing': 0.03 if c['channel'] == 'Direct' else 0.0, 'Cancellation penalty': 0.10 if c['channel'] != 'Direct' else 0.0,
                 'Early payout fee': 0.01 if c['channel'] != 'Direct' else 0.0, 'Promotion fee': round(r.uniform(.02, .05), 2) if c['channel'] != 'Direct' else 0.01, 'Long stay fee': round(c['fee_pct'] * .8, 3) if c['channel'] != 'Direct' else 0.03}[t]
            n += 1; out.append(dict(fee_id='FS-%02d' % n, channel=key('chan', c['channel']), fee_type=t, pct=p, applies_to=ap, from_date=ago(60 + 37 * ((n * 7) % 19))))
    return out

def tax_lines_d():
    rec = [b for b in NONC if b['check_in'] >= ago(75)]; old = [b for b in NONC if b['check_in'] < ago(75)]
    rows = sorted(rec + old[::max(1, len(old) // max(1, 205 - len(rec)))], key=lambda b: b['check_in'])
    return [dict(tax_id='TX-%03d' % i, booking_id=b['booking_id'], city=key('city', b['city']), channel=key('chan', b['channel']), check_in=b['check_in'], room_revenue=b['room_revenue'], tax_pct=b['tax_pct'],
                 tax_collected=b['tax_collected'], collected_by=key('taxby', b['tax_by'])) for i, b in enumerate(rows, 1)]

def changes_d():
    r = rng('sr2-chg'); out = []
    cand = [b for b in NONC if b['check_in'] >= ago(240)]; rows = r.sample(cand, 92); rows.sort(key=lambda b: b['check_in'])
    for i, b in enumerate(rows, 1):
        kind = r.choices(CHKIND, [18, 18, 20, 14, 18, 12])[0]; ci, co = dd(b['check_in']), dd(b['check_out']); k = r.randint(1, 4); amt = 0.0
        oi, oo = ci, co
        if kind == 'Dates moved earlier': oi, oo = ci + dt.timedelta(days=k), co + dt.timedelta(days=k)
        elif kind == 'Dates moved later': oi, oo = ci - dt.timedelta(days=k), co - dt.timedelta(days=k)
        elif kind == 'Stay extended': oo = co - dt.timedelta(days=min(k, b['nights'] - 1) or 1); amt = round((co - oo).days * b['nightly_rate'], 2)
        elif kind == 'Stay shortened': oo = co + dt.timedelta(days=k); amt = -round(k * b['nightly_rate'], 2)
        elif kind == 'Guests added': amt = float(10 * b['nights'])
        else: amt = float(r.choice([-30, -20, 0, 20, 35]))
        d = min(TODAY, max(dd(b['booked_on']) + dt.timedelta(days=1), ci - dt.timedelta(days=r.randint(2, 30))))
        out.append(dict(change_id='BC-%03d' % i, booking_id=b['booking_id'], guest=b['guest'], date=iso(d), kind=key('chkind', kind), old_check_in=iso(oi), old_check_out=iso(oo), new_check_in=b['check_in'],
                        new_check_out=b['check_out'], amount_change=amt))
    return out

def sameday_d():
    r = rng('sr2-sd'); out = []
    for i, (a, c) in enumerate(SD_PICK, 1):
        co = r.choice(['10:00', '10:00', '11:00', '11:00', '12:00']); ci = r.choice(['14:00', '15:00', '15:00', '16:00', '13:00', '17:00'])
        h = int(ci[:2]) - int(co[:2])
        out.append(dict(sd_id='SD-%03d' % i, date=c['check_in'], unit=c['unit'], out_booking=a['booking_id'], in_booking=c['booking_id'], in_guest=c['guest'], checkout_time=co, checkin_time=ci, hours_between=float(h)))
    return out

def longstays_d():
    r = rng('sr2-ls'); cand = [b for b in NONC if b['nights'] >= 7]; rows = sorted(r.sample(cand, 42), key=lambda b: b['check_in']); out = []
    for i, b in enumerate(rows, 1):
        two = b['nights'] >= 14; disc = round((0.12 if two else 0.08) + r.uniform(-.02, .03), 2)
        out.append(dict(ls_id='LS-%02d' % i, booking_id=b['booking_id'], guest=b['guest'], unit=b['unit'], channel=key('chan', b['channel']), check_in=b['check_in'], nights=b['nights'],
                        plan='Two-week stay' if two else 'Weekly stay', list_rate=round(b['nightly_rate'] / (1 - disc)), discount_pct=disc, nightly_rate=b['nightly_rate'], room_revenue=b['room_revenue']))
    return out

NOTE_TXT = {'Guest request': ['Asked for a baby cot', 'Asked for extra towels', 'Asked about parking near the unit', 'Asked for a quiet room at the back'], 'Payment note': ['Guest pays the balance by bank transfer', 'Card payment retried and accepted', 'Receipt requested for a company'],
            'Late arrival': ['Flight delayed, arrives after midnight', 'Arrives after 22:00, self check-in agreed', 'Train delay, arrival after 21:00'], 'Early arrival': ['Asked to drop bags at 11:00', 'Early check-in asked, unit ready at 13:00'],
            'Price agreement': ['Agreed a small discount for extra nights', 'Agreed the weekly rate by message'], 'Change request': ['Asked to move the stay by one day', 'Asked to add one night after the stay'],
            'Platform message': ['Platform asked for a copy of the guest ID check', 'Platform reminded the host to confirm the booking'], 'Special occasion': ['Guest marks an anniversary, small welcome note left', 'Guest travels for a family event']}
def notes_d():
    r = rng('sr2-note'); rows = sorted(r.sample([b for b in NONC if b['check_in'] >= ago(300)], 62), key=lambda b: b['check_in']); out = []
    for i, b in enumerate(rows, 1):
        k = r.choices(NKIND, [22, 12, 14, 10, 8, 14, 8, 6])[0]; d = min(TODAY, dd(b['booked_on']) + dt.timedelta(days=r.randint(0, 6)))
        done = 'Yes' if b['check_out'] < iso(TODAY) or r.random() < .5 else 'No'
        out.append(dict(note_id='NT-%03d' % i, booking_id=b['booking_id'], date=iso(d), kind=key('nkind', k), note=r.choice(NOTE_TXT[k]), handled_by=COHOST if r.random() < .62 else OWNER, done=key('yn', done)))
    return out

def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'], hourly_rate=t['hourly_rate'],
                    speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]

if __name__ == '__main__':
    for n in ['bookings', 'payouts', 'cancellations', 'channels', 'cities', 'units', 'seasons', 'channel_months', 'guests', 'calendar', 'chase', 'deposits', 'sources', 'fees', 'tax_lines', 'changes', 'sameday', 'longstays', 'notes', 'team']:
        d = globals()[n + '_d'](); print(n, len(d))
    print(sum(1 for x in sameday_d() if ago(0) <= x['date'] <= ahead(14)), sum(1 for x in calendar_d() if x['check_in'] >= ago(0)), collections.Counter(x['status'] for x in payouts_d()))
