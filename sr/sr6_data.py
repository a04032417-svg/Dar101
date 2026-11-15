"""Short-term rental host suite part 6: demo rows from sr_core. One chosen set of bookings keeps every table in step."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr6_lists import *
import collections

dd = to_date
R = rng('sr6')
BKF = booking_rows(); BKD = {b['booking_id']: b for b in BKF}
RVF = review_rows(); GMF = guest_message_rows(); GSF = guest_rows()
UNI = {u['unit_id']: u for u in units}
OWNP = {o['name']: o['phone'] for o in owners}
OWNER_PHONE = team[0]['phone']; COHOST_PHONE = team[1]['phone']
ST = story()
TODAY_S = iso(TODAY)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def phone_of(bid): return fake_phone(int(bid[3:]))
def hm(x): return '%02d:%02d' % (int(x) % 24, int(round((x - int(x)) * 60)) % 60)
def cap(d): return d if d <= TODAY_S else TODAY_S
def plus(s, n): return iso(dd(s) + day(n))
def wpick(vals, ws): return R.choices(vals, ws)[0]

# ---------- reviews (about 320): every review of the last 120 days, older ones thinned
def _pick_reviews():
    recent = [r for r in RVF if r['date'] >= ago(120)]
    old = [r for r in RVF if r['date'] < ago(120)]
    keep = []
    ya = na = 0
    for r in old:
        if r['replied'] == 'Yes':
            ya += 1
            if ya % 3 == 0: keep.append(r)
        else:
            na += 1
            if na % 6 == 0: keep.append(r)
    return sorted(recent + keep, key=lambda r: (r['date'], r['review_id']))
RV = _pick_reviews()
def _reply_on(r):
    if r['replied'] != 'Yes': return ''
    d = wpick([0, 1, 2, 3, 5, 8], [.28, .30, .20, .10, .08, .04])
    if r['rating'] <= 3: d = min(d, 2) if R.random() < .7 else d
    return cap(plus(r['date'], d))
REPLY_ON = {r['review_id']: _reply_on(r) for r in RV}

# ---------- chosen bookings: reviewed, complaint, recent, upcoming and a sample of the rest
CMP_MSG = [m for m in GMF if m['kind'] == 'Complaint']
SEL = set(r['booking_id'] for r in RV)
SEL |= set(m['booking_id'] for m in CMP_MSG)
SEL |= set(b['booking_id'] for b in BKF if ago(30) <= b['check_in'] <= ahead(45))
older = [b['booking_id'] for b in BKF if b['booking_id'] not in SEL and b['status'] == 'Completed']
SEL |= set(older[::14])
SELL = sorted((BKD[i] for i in SEL), key=lambda b: (b['check_in'], b['booking_id']))
SELD = {b['booking_id']: b for b in SELL}
DONE = [b for b in SELL if b['status'] in ('Completed', 'In stay') and b['check_in'] <= TODAY_S]
COMPLETED = [b for b in SELL if b['status'] == 'Completed' and b['check_out'] <= TODAY_S]
REVBK = {r['booking_id']: r for r in RV}

# ---------- guests (about 250)
SG = [g for i, g in enumerate(GSF) if i % 2 == 0]
SGN = {g['guest'] for g in SG}
GBK = collections.defaultdict(list)
for b in SELL: GBK[b['guest']].append(b)


def reviews_d():
    out = []
    for r in RV:
        u = UNI[r['unit_id']]
        out.append(nb(dict(review_id=r['review_id'], date=r['date'], booking_id=r['booking_id'], unit=r['unit'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), channel=key('chan', r['channel']),
                           guest=r['guest'], rating=r['rating'], stars=key('stars', STARS[r['rating'] - 1]), cleanliness=r['cleanliness'], communication=r['communication'],
                           location=r['location'], value=r['value'], topic=key('rtopic', r['topic']), replied=key('yn', r['replied']), reply_on=REPLY_ON[r['review_id']])))
    return out


def bookings_d():
    out = []
    for b in SELL:
        out.append(nb(dict(booking_id=b['booking_id'], guest=b['guest'], guest_phone=phone_of(b['booking_id']), unit=b['unit'], city=key('city', b['city']), channel=key('chan', b['channel']), booked_on=b['booked_on'],
                           check_in=b['check_in'], check_out=b['check_out'], guests=b['guests'], nightly_rate=b['nightly_rate'], gross=b['gross'], status=key('bstatus', b['status']))))
    return out


def units_d():
    return [nb(dict(unit_id=u['unit_id'], name=u['name'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), bedrooms=u['bedrooms'], owner=u['owner'], owner_phone=OWNP[u['owner']], since=u['since']))
            for u in units]


# ---------- guest messages (about 500): all but the routine check-in instruction messages, which are thinned
def gmsg_d():
    rows = [m for m in GMF if m['booking_id'] in SELD]
    keep, n = [], 0
    for m in rows:
        if m['kind'] == 'Check-in instructions':
            n += 1
            if n % 3 != 0: continue
        keep.append(m)
    step = 1
    while len(keep) > 560:
        step += 1
        keep = [m for i, m in enumerate(keep) if m['date'] >= ago(60) or i % step == 0]
    return [nb(dict(message_id=m['message_id'], date=m['date'], booking_id=m['booking_id'], unit=m['unit'], guest=m['guest'], kind=key('msgk', m['kind']), channel=key('chan', m['channel']),
                    handled_by=m['handled_by'], response_min=m['response_min'], resolved=key('yn', m['resolved']))) for m in keep]


def guests_d():
    return [nb(dict(guest_id=g['guest_id'], guest=g['guest'], country=key('country', g['country']), phone=fake_phone(int(g['guest_id'][3:])), stays=g['stays'], nights=g['nights'], spend=round(g['spend']),
                    first_stay=g['first_stay'], last_stay=g['last_stay'], channel=key('chan', g['channel']))) for g in SG]


# ---------- check-in records (about 150)
def checkins_d():
    out = []
    rows = [b for b in DONE if b['check_in'] >= ago(30)] + [b for b in DONE if b['check_in'] < ago(30)][::4]
    rows = sorted(rows, key=lambda b: b['check_in'])
    for i, b in enumerate(rows):
        u = UNI[b['unit_id']]
        planned = wpick([15, 15.5, 16], [.6, .2, .2])
        issue = wpick(CISSUE, [.86, .05, .03, .02, .02, .02])
        off = R.uniform(-.5, 1.5) if issue == 'No issue' else R.uniform(2.5, 7)
        if issue == 'Late arrival': off = R.uniform(5, 8)
        method = wpick(AMETHOD, [.55, .25, .15, .05])
        out.append(nb(dict(ci_id='CI-%04d' % (i + 1), date=b['check_in'], booking_id=b['booking_id'], unit=b['unit'], planned=hm(planned), arrival=hm(planned + off), method=key('amethod', method),
                           issue=key('cissue', issue), handled_by=COHOST if u['cohost'] == 'Yes' else OWNER)))
    return out


# ---------- complaints
TOPIC_W = [.22, .14, .16, .12, .08, .06, .14, .08]            # order of REVIEW_TOPICS: Cleanliness, Check-in, Noise, Comfort, Location, Value, Host communication, Amenities
def complaints_d():
    out = []
    msgs = sorted(CMP_MSG, key=lambda m: m['date'])
    recent = [m for m in msgs if m['date'] >= ago(60)]
    older_m = [m for m in msgs if m['date'] < ago(60)]
    pick = older_m[:max(0, 70 - len(recent))] if len(older_m) > 70 - len(recent) else older_m
    pick = sorted(pick + recent, key=lambda m: m['date'])
    extra = [b for b in DONE if b['check_in'] >= ago(12)][:3]
    for b in extra:
        pick.append(dict(date=cap(plus(b['check_in'], 1)), booking_id=b['booking_id'], unit=b['unit'], unit_id=b['unit_id'], guest=b['guest'], handled_by=COHOST))
    pick = sorted(pick, key=lambda m: m['date'])
    for i, m in enumerate(pick):
        b = BKD[m['booking_id']]
        topic = 'Cleanliness' if m['unit_id'] == ST['low_review_unit'] and m['date'] >= ago(120) and R.random() < .7 else wpick(REVIEW_TOPICS, TOPIC_W)
        sev = wpick(SEVERITY, [.5, .35, .15])
        comp = 0 if sev == 'Minor' and R.random() < .7 else round(b['gross'] * (.1 if sev == 'Minor' else .15 if sev == 'Moderate' else .35))
        act = wpick(['Apology', 'Fixed on site', 'No action'], [.5, .4, .1]) if sev == 'Minor' else (wpick(['Credit for next stay', 'Partial refund', 'Fixed on site'], [.4, .35, .25]) if sev == 'Moderate' else wpick(['Partial refund', 'Moved to another unit'], [.65, .35]))
        age = (TODAY - dd(m['date'])).days
        rd = wpick([0, 1, 2, 3, 5, 7], [.26, .30, .20, .10, .09, .05])
        resolved = cap(plus(m['date'], rd)) if not (age <= 6 and R.random() < .35) else ''
        if resolved and resolved > TODAY_S: resolved = ''
        out.append(dict(cp_id='CM-%03d' % (i + 1), date=m['date'], booking_id=m['booking_id'], unit=m['unit'], guest=m['guest'], topic=key('rtopic', topic), severity=key('sev', sev), action=key('cact', act),
                        compensation=comp, resolved_on=resolved, handled_by=m['handled_by']))
    # make sure the table shows an open complaint older than the target and two this month
    older_open = [o for o in out if o['date'] >= ago(12) and o['date'] <= ago(5)]
    if older_open: older_open[0]['resolved_on'] = ''
    thism = [o for o in out if o['date'] >= iso(month_start(0))]
    for o in out[-3:]:
        if o['date'] < iso(month_start(0)): o['date'] = cap(plus(iso(month_start(0)), 1 + out.index(o) % 3))
    return [nb(o) for o in out]


PREFS = ['Quiet room away from the street', 'Late checkout when possible', 'Extra pillows and blankets', 'Baby cot and high chair', 'Ground floor, no stairs', 'Early check-in if free', 'Parking space near the door',
         'Vegetarian welcome snack', 'Fast Wi-Fi for remote work', 'Allergy-free bedding', 'Sea view if available', 'Extra towels for the beach', 'Small dog travels along']
def prefs_d():
    rep = [g for g in SG if g['stays'] >= 2]
    chosen = rep[::2][:80]
    out = []
    for i, g in enumerate(chosen):
        bks = GBK.get(g['guest'])
        unit = bks[-1]['unit'] if bks else R.choice(units)['name']
        noted = cap(plus(g['first_stay'], R.randint(0, max(1, (dd(g['last_stay']) - dd(g['first_stay'])).days))))
        out.append(nb(dict(pf_id='PF-%03d' % (i + 1), guest=g['guest'], preference=PREFS[(i * 5 + int(g['guest_id'][3:])) % len(PREFS)], unit=unit, noted_on=noted)))
    return sorted(out, key=lambda r: r['noted_on'])


def replies_d():
    done = [r for r in RV if r['replied'] == 'Yes' and REPLY_ON[r['review_id']]]
    low = [r for r in done if r['rating'] <= 3]
    rest = [r for r in done if r['rating'] > 3]
    take = low + rest[::max(1, len(rest) // max(1, 150 - len(low)))]
    take = sorted(take, key=lambda r: r['review_id'])[:160]
    out = []
    for i, r in enumerate(take):
        tone = 'Warm thanks' if r['rating'] == 5 else 'Thanks and a tip' if r['rating'] == 4 else 'Honest apology and fix'
        words = R.randint(25, 60) if r['rating'] == 5 else R.randint(45, 90) if r['rating'] == 4 else R.randint(70, 130)
        out.append(nb(dict(rp_id='RP-%03d' % (i + 1), review_id=r['review_id'], replied_on=REPLY_ON[r['review_id']], replied_by=wpick([COHOST, OWNER], [.7, .3]), length=words, tone=tone)))
    return sorted(out, key=lambda r: r['replied_on'])


TPL = [('Booking confirmation', 'Booking question'), ('Pre-arrival questions', 'Booking question'), ('Cancellation answer', 'Booking question'), ('Extension offer', 'Booking question'),
       ('Check-in instructions', 'Check-in instructions'), ('Door code reminder', 'Check-in instructions'), ('Arrival time question', 'Check-in instructions'), ('Welcome message day one', 'Question during stay'),
       ('Mid-stay check', 'Question during stay'), ('House rules reminder', 'Question during stay'), ('Quiet hours reminder', 'Question during stay'), ('Lost item found', 'Question during stay'),
       ('Complaint apology', 'Complaint'), ('Compensation offer', 'Complaint'), ('Fixed and thank you', 'Complaint'), ('Special request answer', 'Special request'), ('Early check-in answer', 'Special request'),
       ('Late checkout answer', 'Special request'), ('Extra bed request', 'Special request'), ('Checkout reminder', 'Checkout reminder'), ('Checkout thanks', 'Checkout reminder'),
       ('Thank you and review request', 'Review request'), ('Review reminder', 'Review request'), ('Survey request', 'Review request')]
def templates_d():
    out = []
    for i, (n, k) in enumerate(TPL):
        lang = 'English' if i % 6 else ['Portuguese', 'Spanish', 'German', 'French'][(i // 6) % 4]
        out.append(nb(dict(tpl_id='TP-%02d' % (i + 1), template=n, kind=key('msgk', k), language=lang, uses=R.randint(8, 420) if k != 'Complaint' else R.randint(5, 60),
                           last_edited=ago(R.choice([9, 21, 40, 75, 120, 200, 260, 330, 410, 520])), edited_by=R.choice([COHOST, OWNER]))))
    return out


SECT = ['Wi-Fi and TV', 'Heating and hot water', 'Parking', 'Bins and recycling', 'Local food and coffee', 'Emergency numbers', 'Checkout steps', 'House rules', 'Transport and taxis', 'Appliance guide']
def welcome_d():
    out, n = [], 0
    for ui, u in enumerate(units):
        secs = [SECT[(ui + j * 3) % len(SECT)] for j in range(3)]
        for j, s in enumerate(secs):
            n += 1
            age = R.choice([12, 30, 55, 90, 140, 160, 220, 300, 410]) if not (ui == 8 and j == 0) else 480
            out.append(nb(dict(wb_id='WB-%02d' % n, unit=u['name'], section=s, updated_on=ago(age), maintained_by=COHOST if u['cohost'] == 'Yes' else OWNER)))
    return out


COMMENTS = {'hi': ['Lovely stay, everything worked.', 'Clean, quiet and easy to reach.', 'Great host messages and a smooth check-in.', 'We would book again.', 'Comfortable beds and a good kitchen.'],
            'mid': ['Good stay, the shower was slow to heat.', 'Nice place but the street was noisy at night.', 'Check-in took longer than expected.', 'Missing a few kitchen items.'],
            'lo': ['The unit was not clean on arrival.', 'Noise from the next flat kept us awake.', 'The code did not work at first.']}
def surveys_d():
    rows = COMPLETED[::2]
    rows = [b for b in rows if b['check_out'] >= ago(400)]
    step = max(1, len(rows) // 90)
    rows = rows[::step][:90] if len(rows) > 90 else rows
    recent = [b for b in COMPLETED if b['check_out'] >= ago(20)][:12]
    ids = {b['booking_id'] for b in rows}
    rows += [b for b in recent if b['booking_id'] not in ids]
    rows = sorted(rows, key=lambda b: b['check_out'])
    out = []
    for i, b in enumerate(rows):
        rv = REVBK.get(b['booking_id'])
        score = max(1, min(10, rv['rating'] * 2 + R.choice([-1, 0, 0, 0, 1]))) if rv else wpick([10, 9, 8, 7, 6, 4], [.3, .3, .2, .1, .06, .04])
        pool = COMMENTS['hi'] if score >= 8 else COMMENTS['mid'] if score >= 6 else COMMENTS['lo']
        ret = 'Yes' if (score >= 7 and R.random() < .92) or (score < 7 and R.random() < .15) else 'No'
        out.append(nb(dict(sv_id='SV-%03d' % (i + 1), date=cap(plus(b['check_out'], R.choice([1, 1, 2, 3]))), booking_id=b['booking_id'], unit=b['unit'], score=score, comment=R.choice(pool), would_return=key('yn', ret))))
    return out


def referrals_d():
    rep = [g for g in SG if g['stays'] >= 3]
    refd = [g for g in SG if g['stays'] == 1 and GBK.get(g['guest'])]
    out = []
    for i in range(30):
        a = rep[(i * 7) % len(rep)]
        pending = i % 6 == 5
        c = refd[(i * 11) % len(refd)]
        bks = GBK[c['guest']]
        bid = '' if pending else bks[0]['booking_id']
        date = cap(plus(c['first_stay'], -R.randint(10, 40)))
        paid = 'Yes' if (not pending and bks[0]['status'] == 'Completed' and R.random() < .8) else 'No'
        out.append(nb(dict(rf_id='RF-%02d' % (i + 1), date=date, guest=a['guest'], referred=c['guest'], booking_id=bid, reward=wpick([20, 25, 30], [.3, .4, .3]), reward_paid=key('yn', paid))))
    return sorted(out, key=lambda r: r['date'])


REQ = [('Extra bed', 12, 25), ('Baby cot', 5, 15), ('Airport pick-up', 28, 45), ('Groceries before arrival', 14, 22), ('Birthday decoration', 16, 35), ('Mid-stay cleaning', 22, 38), ('Parking permit', 9, 14), ('Luggage storage', 0, 10),
       ('Welcome flowers', 12, 24), ('Bike rental', 18, 30)]
def requests_d():
    rows = [b for b in SELL if b['status'] != 'Cancelled']
    rows = [b for b in rows if b['check_in'] >= ago(400)][::5][:60]
    out = []
    for i, b in enumerate(sorted(rows, key=lambda b: b['check_in'])):
        name, cost, fee = REQ[(i * 3 + int(b['booking_id'][3:])) % len(REQ)]
        cost = round(cost * R.uniform(.9, 1.2)); fee = round(fee * R.uniform(.9, 1.2))
        appr = 'No' if R.random() < .1 else 'Yes'
        done = '' if appr == 'No' or b['check_in'] > TODAY_S else cap(plus(b['check_in'], R.choice([0, 0, 1])))
        out.append(nb(dict(sq_id='SQ-%03d' % (i + 1), date=cap(plus(b['check_in'], -R.randint(1, 12))), booking_id=b['booking_id'], request=name, cost=cost, fee=fee, approved=key('yn', appr), done_on=done)))
    return out


def earlyout_d():
    rows = [b for b in COMPLETED if b['check_in'] >= ago(400)][3::5][:60]
    out = []
    for i, b in enumerate(rows):
        kind = 'Early check-in' if i % 2 == 0 else 'Late checkout'
        hours = wpick([1, 1.5, 2, 3, 4], [.25, .2, .3, .15, .1])
        rate = b['nightly_rate']
        sug = round(max(0, hours - 1) * rate * .08)
        appr = 'No' if R.random() < .1 else 'Yes'
        fee = 0 if appr == 'No' else (sug if R.random() > .15 else 0)
        out.append(nb(dict(eo_id='EL-%03d' % (i + 1), date=b['check_in'] if kind == 'Early check-in' else b['check_out'], booking_id=b['booking_id'], kind=key('eckind', kind), hours=hours, fee=fee, approved=key('yn', appr))))
    return sorted(out, key=lambda r: r['date'])


RULES = ['Quiet hours after 22:00', 'More guests than booked', 'No smoking indoors', 'No pets', 'No parties or events', 'Parking outside the marked place']
ACTS = ['Verbal warning', 'Written warning', 'Extra cleaning charged', 'Deposit kept in part', 'Reminder sent']
def breaches_d():
    rows = [b for b in DONE if b['check_in'] >= ago(400)]
    rec = [b for b in rows if b['check_in'] >= ago(45)][::4][:4]
    old = rows[::max(1, len(rows) // 28)][:26]
    ids = {b['booking_id'] for b in rec}
    sel = sorted(rec + [b for b in old if b['booking_id'] not in ids], key=lambda b: b['check_in'])
    out = []
    for i, b in enumerate(sel):
        rule = RULES[(i * 5 + int(b['booking_id'][3:])) % len(RULES)]
        out.append(nb(dict(hb_id='HB-%02d' % (i + 1), date=cap(plus(b['check_in'], R.randint(0, max(0, min(3, b['nights'] - 1))))), booking_id=b['booking_id'], unit=b['unit'], guest=b['guest'], rule=rule,
                           action=wpick(ACTS, [.3, .25, .2, .1, .15]), warning_sent=key('yn', 'Yes' if R.random() < .82 else 'No'))))
    return out


def revreq_d():
    done = [b for b in COMPLETED if b['check_out'] >= ago(420)]
    rows = [b for b in done if b['booking_id'] in REVBK] + [b for b in done if b['booking_id'] not in REVBK][::2]
    rows = sorted(rows, key=lambda b: b['check_out'])
    if len(rows) > 210: rows = [b for i, b in enumerate(rows) if b['check_out'] >= ago(60) or i % 2 == 0]
    out = []
    for i, b in enumerate(rows[-220:]):
        rv = REVBK.get(b['booking_id'])
        sent = cap(plus(b['check_out'], wpick([0, 1, 2, 4], [.4, .35, .15, .1])))
        rev_on = ''
        if rv:
            rev_on = rv['date']
            if rev_on < sent: sent = rev_on
        out.append(nb(dict(rq_id='RQ-%04d' % (i + 1), booking_id=b['booking_id'], sent_on=sent, reviewed_on=rev_on)))
    return out


def topicmo_d():
    ms = months14()[-12:]
    agg = collections.defaultdict(list)
    for r in RVF: agg[(r['date'][:7] + '-01', r['topic'])].append(r['rating'])
    out, n = [], 0
    for m in ms:
        for t in REVIEW_TOPICS:
            v = agg.get((iso(m), t))
            if v:
                n += 1
                out.append(dict(tm_id='TM-%03d' % n, month=iso(m), topic=key('rtopic', t), reviews=len(v), avg_rating=round(sum(v) / len(v), 2)))
    return out


OFFERS = ['10 percent off a direct booking', 'Free late checkout', 'A welcome gift on arrival', 'One night free on a 4 night stay', 'Free early check-in']
def winback_d():
    cand = [g for g in SG if g['stays'] >= 2 and g['last_stay'] <= ago(150) and g['last_stay'] >= ago(560)]
    cand = cand[::max(1, len(cand) // 40)][:40]
    out = []
    for i, g in enumerate(sorted(cand, key=lambda g: g['last_stay'])):
        sent = cap(plus(g['last_stay'], R.randint(150, 220)))
        booked = 'Yes' if R.random() < .27 else 'No'
        out.append(nb(dict(wn_id='WN-%02d' % (i + 1), guest=g['guest'], last_stay=g['last_stay'], nights=g['nights'], offer=OFFERS[i % len(OFFERS)], sent_on=sent, booked=key('yn', booked))))
    return out


def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'], hourly_rate=t['hourly_rate'],
                    speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]


if __name__ == '__main__':
    for n in ['reviews', 'bookings', 'units', 'gmsg', 'guests', 'checkins', 'complaints', 'prefs', 'replies', 'templates', 'welcome', 'surveys', 'referrals', 'requests', 'earlyout', 'breaches', 'revreq', 'topicmo', 'winback', 'team']:
        d = globals()[n + '_d'](); print(n, len(d))
