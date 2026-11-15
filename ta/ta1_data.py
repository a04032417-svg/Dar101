"""Travel agent suite part 1: demo rows from ta_core (full generator output for aggregated tables, thinned rows elsewhere)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ta1_lists import *
import collections

dd = to_date
ENQ = enquiry_rows(); QUO = quote_rows(); TRP = trip_rows(); CLI = client_rows(); BKS = booking_rows(); MKT = marketing_rows()
CLID = {c['client_id']: c for c in CLI}; ENQD = {e['enquiry_id']: e for e in ENQ}; TRPD = {t['trip_id']: t for t in TRP}
SUPD = {s['name']: s for s in suppliers}
OWNER_PHONE = team[0]['phone']
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def mk1(d): return dt.date(d.year, d.month, 1)
def clip(s):
    """an iso date no later than today"""
    d = dd(s); return iso(d if d <= TODAY else TODAY)

# ---------- referral partners (14)
_PART = [('Orchid Lane Weddings', 'Wedding planner', 'Mei-Ling Tan', 'Singapore'), ('Silverleaf Celebrations', 'Wedding planner', 'Fatima Zahra El Idrissi', 'Morocco'),
         ('Golden Hour Events', 'Wedding planner', 'Rafael Montes', 'Mexico'), ('Petal and Pine Weddings', 'Wedding planner', 'Ingrid Solheim', 'Norway'),
         ('Lakeshore Occasions', 'Wedding planner', 'Chiamaka Eze', 'Nigeria'), ('Northwind Logistics Group', 'Corporate contact', 'Dmitri Volkov', 'Poland'),
         ('Brightpath Consulting', 'Corporate contact', 'Ananya Rao', 'India'), ('Harbour Point Engineering', 'Corporate contact', 'Callum Reid', 'United Kingdom'),
         ('Riverside Walking Club', 'Community leader', 'Helena Costa', 'Portugal'), ('Maple Court Retirement Club', 'Community leader', 'Walter Hughes', 'Canada'),
         ('Eastfield Parents Network', 'Community leader', 'Yuki Tanaka', 'Japan'), ('Blue Door Photography', 'Trade partner', 'Santiago Vega', 'Colombia'),
         ('Lark Lane Jewellers', 'Trade partner', 'Amara Nwosu', 'Nigeria'), ('Harvest Table Catering', 'Trade partner', 'Sven Larsson', 'Sweden')]
_PKIND_OF_SRC = {'Wedding planner referral': 'Wedding planner', 'Corporate contact': 'Corporate contact', 'Local community group': 'Community leader', 'Partner referral': 'Trade partner'}
PART_BY_KIND = collections.defaultdict(list)
for _p in _PART: PART_BY_KIND[_p[1]].append(_p[0])
def partners_d():
    R = rng('ta1partner'); out = []
    for i, (n, k, c, ct) in enumerate(_PART):
        out.append(dict(partner_id='RP-%02d' % (i + 1), name=n, kind=key('pkind', k), contact=c, phone=fake_phone(i + 50), email=fake_email(c, 0).replace('mail.example.com', 'partner.example.com'),
                        country=ct, since=ago(R.randint(300, 1000)), thank_you_date=ago(R.choice([12, 25, 40, 66, 85, 120, 150, 170, 20, 55, 95, 33, 110, 8]))))
    return out
def _partner_for(e, i):
    k = _PKIND_OF_SRC.get(e['source'])
    if not k: return ''
    pool = PART_BY_KIND[k]; return pool[(i * 5 + len(e['contact'])) % len(pool)]

# ---------- enquiries (160)
EPH = {}
def enquiries_d():
    R = rng('ta1enq'); out = []; quoted = [i for i, e in enumerate(ENQ) if e['status'] == 'Quoted']
    for i, e in enumerate(ENQ):
        c = CLID.get(e['client_id']); ph = c['phone'] if c else fake_phone(i + 3); EPH[e['enquiry_id']] = ph
        h = e['first_reply_hours']
        if R.random() < .14: h = R.choice([30, 41, 52, 75])
        fu = e['follow_up_date']
        if not fu and e['status'] != 'New': fu = iso(dd(e['date']) + dt.timedelta(days=R.randint(5, 12)))
        if quoted and i == quoted[1]: fu = ago(3)
        if quoted and i == quoted[4]: fu = ago(7)
        out.append(nb(dict(enquiry_id=e['enquiry_id'], date=e['date'], contact=e['contact'], phone=ph, client=c['name'] if c else '', trip_type=key('ttype', e['trip_type']), destination=e['destination'],
                           travellers=e['travellers'], budget=e['budget'], source=key('msrc', e['source']), advisor=e['advisor'], status=key('enqst', e['status']), follow_up_date=fu,
                           converted_trip=e['converted_trip'], first_reply_hours=h, partner=_partner_for(e, i))))
    return out

# ---------- quotes (152): the 13 open quotes had no supplier net in the generator, so a net of about 90% of the price is filled in
QFIX = {}
def quotes_d():
    R = rng('ta1quote'); out = []
    for q in QUO:
        net, com = q['supplier_net'], q['expected_commission']
        if not net:
            net = round(q['total_quote'] * R.uniform(0.89, 0.92), 2); com = round(q['total_quote'] * R.uniform(0.07, 0.115), 2)
        QFIX[q['quote_id']] = (net, com)
        out.append(nb(dict(quote_id=q['quote_id'], date_sent=q['date_sent'], enquiry_id=q['enquiry_id'], client=q['client'], trip_id=q['trip_id'], trip_type=key('ttype', q['trip_type']),
                           destination=q['destination'], travellers=q['travellers'], total_quote=q['total_quote'], supplier_net=net, service_fee=q['service_fee'], expected_commission=com,
                           valid_until=q['valid_until'], status=key('quotest', q['status']), advisor=q['advisor'])))
    return out

# ---------- quote lines (about 480)
_MIX = {'Honeymoon': [('Hotel and resort', .62), ('Airline', .26), ('Transfer and ground', .07), ('Activity and guide', .05)],
        'Family holiday': [('Hotel and resort', .55), ('Airline', .28), ('Activity and guide', .10), ('Travel insurance', .07)],
        'Cruise': [('Cruise line', .66), ('Airline', .22), ('Transfer and ground', .06), ('Travel insurance', .06)],
        'Escorted tour': [('Tour operator', .70), ('Airline', .24), ('Travel insurance', .06)],
        'Group trip': [('Hotel and resort', .54), ('Airline', .30), ('Transfer and ground', .09), ('Activity and guide', .07)],
        'Corporate travel': [('Airline', .50), ('Hotel and resort', .38), ('Transfer and ground', .12)],
        'Weekend break': [('Hotel and resort', .55), ('Rail and ferry', .30), ('Activity and guide', .15)],
        'Multi-destination': [('Hotel and resort', .46), ('Airline', .26), ('Rail and ferry', .14), ('Car rental', .08), ('Transfer and ground', .06)]}
_BK_SUP = collections.defaultdict(dict)
for _b in BKS: _BK_SUP[_b['trip_id']].setdefault(_b['category'], _b['supplier'])
_CAT_SUP = collections.defaultdict(list)
for _s in suppliers: _CAT_SUP[_s['category']].append(_s['name'])
def _desc(cat, dest, n, t):
    return {'Hotel and resort': '%d nights in a %s hotel, breakfast included' % (n, dest), 'Cruise line': '%d-night cruise, balcony cabin, %s' % (n, dest), 'Tour operator': '%d-day guided tour, %s' % (n + 1, dest),
            'Airline': 'Return flights for %d travellers' % t, 'Transfer and ground': 'Airport and hotel transfers, %s' % dest, 'Travel insurance': 'Travel insurance for %d travellers' % t,
            'Rail and ferry': 'Rail and ferry tickets, %s' % dest, 'Car rental': 'Car rental for %d days' % n, 'Activity and guide': 'Excursions and local guides, %s' % dest}[cat]
def quote_lines_d():
    R = rng('ta1lines'); out = []; k = 0
    for q in QUO:
        net_t, _ = QFIX[q['quote_id']]; tot = q['total_quote']; mix = _MIX[q['trip_type']]
        if q['trip_type'] == 'Cruise': n = R.choice([7, 10, 12, 14])
        elif q['trip_type'] == 'Weekend break': n = R.choice([2, 3, 4])
        elif q['trip_type'] == 'Escorted tour': n = R.choice([8, 10, 12, 14])
        else: n = R.choice([5, 7, 9, 10, 12])
        k0 = len(out); sh = [w * R.uniform(.85, 1.15) for _, w in mix]; ssum = sum(sh); gross = []; ps = 0
        for j in range(len(mix)):
            g = round(tot * sh[j] / ssum, 2) if j < len(mix) - 1 else round(tot - ps, 2); gross.append(g); ps += g
        raw = []
        for j, (cat, _) in enumerate(mix):
            sup = _BK_SUP.get(q['trip_id'], {}).get(cat) or _CAT_SUP[cat][(int(q['quote_id'][3:]) + j * 3) % len(_CAT_SUP[cat])]
            raw.append((cat, sup, gross[j] * (1 - SUPD[sup]['commission_pct'])))
        s = net_t / sum(r[2] for r in raw); pn = 0
        for j, (cat, sup, rn) in enumerate(raw):
            nt = round(rn * s, 2) if j < len(raw) - 1 else round(net_t - pn, 2); pn += nt; k += 1
            out.append(dict(line_id='QL-%04d' % k, quote_id=q['quote_id'], category=key('scat', cat), supplier=sup, description=_desc(cat, q['destination'], n, q['travellers']),
                            nights=n if cat in ('Hotel and resort', 'Cruise line', 'Tour operator', 'Car rental', 'Rail and ferry') else 0, supplier_net=nt, client_price=gross[j]))
    return out

# ---------- discovery calls (about 140)
_DISC_ENQ = [e for e in ENQ if e['status'] != 'No reply' and e['status'] != 'New']
def discovery_d():
    R = rng('ta1disc'); out = []
    for i, e in enumerate(_DISC_ENQ[:140]):
        d = dd(e['date']) + dt.timedelta(days=R.randint(1, 4)); d = d if d <= TODAY else TODAY
        won = e['status'] == 'Won'; st = e['status']
        oc = 'Will book' if won and R.random() < .35 else ('Ready for a quote' if won else {'Quoted': 'Wants options', 'Lost on price': 'Declined', 'Chose another advisor': 'Needs more time', 'Not travelling': 'Waiting for a partner'}.get(st, 'No answer'))
        nxt = '' if won else iso(d + dt.timedelta(days=R.randint(3, 9)))
        if st == 'Quoted': nxt = ahead(R.randint(2, 9)) if i % 3 else ago(R.randint(2, 6))
        if i == 0: nxt = iso(d + dt.timedelta(days=4))
        out.append(nb(dict(call_id='DV-%04d' % (i + 1), date=iso(d), enquiry_id=e['enquiry_id'], minutes=R.choice([20, 25, 30, 35, 40, 45, 50, 60, 75]), advisor=e['advisor'], outcome=key('outcome', oc), next_step_date=nxt)))
    return out

# ---------- trip briefs (about 90)
_MUST = {'Honeymoon': ['Private dinner on the beach', 'Late checkout', 'Spa day for two', 'Sunrise excursion'], 'Family holiday': ['Kids club', 'Rooms that connect', 'Short transfers', 'Pool with shade'],
         'Cruise': ['Balcony cabin', 'Late dining time', 'Shore excursions planned', 'Accessible cabin'], 'Escorted tour': ['Small group size', 'Local guide', 'Free afternoons', 'Luggage handled'],
         'Group trip': ['Group dinner night', 'One meeting room', 'Rooms on one floor', 'Easy airport pickup'], 'Corporate travel': ['Flexible tickets', 'Hotel near the office', 'Fast airport transfers', 'One invoice'],
         'Weekend break': ['Central hotel', 'Late checkout', 'Food tour', 'Train rather than plane'], 'Multi-destination': ['Few hotel changes', 'One rail pass', 'A rest day each week', 'Direct flights']}
_AVOID = ['Early flights', 'Long coach days', 'Crowded beaches', 'Shared bathrooms', 'Night flights', 'Many stairs', 'Shellfish menus', 'Loud nightlife', 'Hotel changes every night', 'No avoid list']
def briefs_d():
    R = rng('ta1brief'); out = []; k = 0
    cand = [e for e in ENQ if e['status'] in ('Won', 'Quoted')]
    for i, e in enumerate(cand[:90]):
        k += 1; d = dd(e['date']) + dt.timedelta(days=R.randint(2, 6)); d = d if d <= TODAY else TODAY
        t = dd(e['converted_trip'] and TRPD[e['converted_trip']]['start_date'] or iso(d + dt.timedelta(days=R.randint(120, 300))))
        nts = TRPD[e['converted_trip']]['nights'] if e['converted_trip'] else R.choice([5, 7, 8, 10, 14])
        ws = t - dt.timedelta(days=R.randint(3, 20)); we = t + dt.timedelta(days=nts + R.randint(2, 25))
        mh = _MUST[e['trip_type']]; mu = '%s; %s' % (mh[i % 4], mh[(i + 2) % 4])
        out.append(dict(brief_id='TB-%04d' % k, brief_date=iso(d), enquiry_id=e['enquiry_id'], travellers=e['travellers'], nights=nts, window_start=iso(ws), window_end=iso(we), budget=round(e['budget'] * R.uniform(.97, 1.08), 2),
                        must_haves=mu, avoid=_AVOID[(i * 3 + 1) % len(_AVOID)], pace=key('pace', R.choice(PACE))))
    return out

# ---------- clients (80) and trips (120)
def clients_d():
    return [nb(dict(client_id=c['client_id'], name=c['name'], kind=key('ckind', c['kind']), contact=c['contact'], phone=c['phone'], email=c['email'], country=c['country'], home_airport=c['home_airport'],
                    interest=c['interest'], since=c['since'], stage=key('stage', c['stage']), referred_by=c['referred_by'])) for c in CLI]
_DEP = collections.defaultdict(list)
for _b in BKS: _DEP[_b['trip_id']].append(_b)
_OPENQ = {q['trip_id']: q for q in QUO if q['status'] == 'Open'}
def trips_d():
    out = []
    for t in TRP:
        bs = _DEP.get(t['trip_id'], [])
        if t['status'] == 'Quoted':
            due = _OPENQ[t['trip_id']]['valid_until'] if t['trip_id'] in _OPENQ else ahead(7); paid = ''
        else:
            due = min(b['deposit_due'] for b in bs) if bs else ''
            pd = [b['deposit_paid_on'] for b in bs]; paid = max(pd) if pd and all(pd) else ''
        out.append(nb(dict(trip_id=t['trip_id'], client=t['client'], client_id=t['client_id'], trip_type=key('ttype', t['trip_type']), destination=t['destination'], start_date=t['start_date'], end_date=t['end_date'],
                           nights=t['nights'], travellers=t['travellers'], status=key('tstatus', t['status']), advisor=t['advisor'], booked_on=t['booked_on'], cancelled_on=t['cancelled_on'], group_id=t['group_id'],
                           total_price=t['total_price'], supplier_net=t['supplier_net'], commission_expected=t['commission_expected'], service_fee=t['service_fee'], host_pct=t['host_pct'],
                           enquiry_id=t['enquiry_id'], deposit_due=due, deposit_paid_on=paid)))
    return out

def suppliers_d():
    return [dict(supplier_id=s['supplier_id'], name=s['name'], category=key('scat', s['category']), country=s['country'], contact=s['contact'], phone=s['phone'], email=s['email'], commission_pct=s['commission_pct'],
                 deposit_pct=s['deposit_pct'], final_days=s['final_days'], collect=s['collect'], terms_days=s['terms_days'], rating=s['rating'], since=s['since']) for s in suppliers]
def team_d():
    return [dict(staff_id=m['staff_id'], name=m['name'], role=key('role', m['role']), team=key('team', m['team']), phone=m['phone'], email=m['email'], hours_week=m['hours_week'], advisor_pct=m['advisor_pct'],
                 speciality=m['speciality'], country=m['country'], start=m['start']) for m in team]

# ---------- service fee schedule (14)
FEES = [('Trip planning fee', 'Trip', 250, 'Yes'), ('Air ticket booking', 'Ticket', 35, 'No'), ('Change to a booked trip', 'Change', 60, 'Yes'), ('Cancellation handling', 'Booking', 90, 'No'),
        ('Rush booking, travel within 14 days', 'Trip', 150, 'No'), ('Multi-destination itinerary design', 'Trip', 400, 'Yes'), ('Cruise shore excursion planning', 'Trip', 120, 'Yes'),
        ('Group trip coordination', 'Traveller', 30, 'No'), ('Travel document check', 'Traveller', 25, 'Yes'), ('Corporate trip booking', 'Trip', 180, 'No'),
        ('Honeymoon and special occasion set-up', 'Trip', 200, 'Yes'), ('Entry document guidance', 'Traveller', 45, 'No'), ('Airport transfer arrangement', 'Transfer', 30, 'Yes'),
        ('Travel insurance advice and booking', 'Policy', 40, 'No')]
def fees_d():
    R = rng('ta1fee')
    return [dict(fee_id='FE-%02d' % (i + 1), service=s, unit=u, fee=f, waived_repeat=key('yn', w), review_on=ahead(R.randint(-20, 70))) for i, (s, u, f, w) in enumerate(FEES)]

# ---------- trip packages (12)
PACKAGES = [('Island honeymoon, 7 nights', 'Honeymoon', 7, 2, 5400, 'Beach resort, return flights, private transfers, one dinner for two'), ('City and countryside honeymoon, 8 nights', 'Honeymoon', 8, 2, 6100, 'Two hotels, rail pass, wine tasting, airport transfers'),
            ('Family beach week, 7 nights', 'Family holiday', 7, 4, 8900, 'Family room, flights, kids club, airport transfers'), ('Family adventure, 10 nights', 'Family holiday', 10, 4, 12600, 'Two bases, guided activities, flights, insurance'),
            ('Mediterranean cruise, 7 nights', 'Cruise', 7, 2, 4300, 'Balcony cabin, flights, pre-cruise hotel night, transfers'), ('River cruise, 8 nights', 'Cruise', 8, 2, 5200, 'Outside cabin, guided shore visits, flights, transfers'),
            ('Cultural tour, 12 days', 'Escorted tour', 11, 2, 6800, 'Small group, local guides, hotels, domestic transport'), ('Wildlife tour, 10 days', 'Escorted tour', 9, 2, 9900, 'Guided safari, lodges, domestic flights, park fees'),
            ('Group celebration weekend', 'Group trip', 3, 12, 14400, 'Shared rooms, group dinner, coach transfers, coordinator'), ('Team meeting trip, 3 nights', 'Corporate travel', 3, 6, 7600, 'Flights, central hotel, meeting room, transfers'),
            ('City break, 3 nights', 'Weekend break', 3, 2, 1250, 'Central hotel, rail tickets, one guided walk'), ('Two-country journey, 14 nights', 'Multi-destination', 14, 2, 8200, 'Three hotels, flights, rail pass, car for three days')]
def packages_d():
    return [dict(package_id='PK-%02d' % (i + 1), name=n, trip_type=key('ttype', t), nights=nt, travellers=tr, from_price=p, included=inc) for i, (n, t, nt, tr, p, inc) in enumerate(PACKAGES)]

# ---------- destination price guide (24): the 12 most asked destinations, peak and low season
def guide_d():
    R = rng('ta1guide'); cnt = collections.Counter(e['destination'] for e in ENQ); out = []; k = 0
    for dest, _ in cnt.most_common(8):
        base = R.randint(120, 330); air = R.randint(380, 1500); daily = R.randint(70, 190)
        for s, f in (('Peak', 1.35), ('Shoulder', 1.0), ('Low', 0.8)):
            k += 1; out.append(dict(guide_id='PG-%02d' % k, destination=dest, season=key('season', s), hotel_night=round(base * f * R.uniform(.95, 1.05)), daily_budget=round(daily * {'Peak': 1.1, 'Shoulder': 1.0, 'Low': .92}[s]), air_fare=round(air * {'Peak': 1.2, 'Shoulder': 1.0, 'Low': .85}[s])))
    return out

# ---------- lost enquiries (32)
_LOSTMAP = {'Lost on price': 'Price too high', 'Chose another advisor': 'Chose another advisor', 'Not travelling': 'Not travelling this year', 'No reply': 'No reply after the quote'}
_WONBY = {'Price too high': ['Online booking site', 'Another advisor', 'Cheaper package deal'], 'Chose another advisor': ['Another advisor', 'A friend who is an advisor'], 'Not travelling this year': ['Did not travel'],
          'No reply after the quote': ['Unknown', 'Booked direct with the supplier']}
_SAVED = {'Price too high': ['A lower hotel tier', 'Cheaper dates in the shoulder season', 'Two shorter stays', 'A price match with the service fee waived'], 'Chose another advisor': ['A faster first reply', 'A call within one day', 'A clearer price breakdown'],
          'Not travelling this year': ['A hold on the price until next year', 'A deposit-free reservation'], 'No reply after the quote': ['A follow-up call on day three', 'A shorter quote with two options']}
def lost_d():
    R = rng('ta1lost'); out = []; k = 0
    for e in ENQ:
        if e['status'] not in _LOSTMAP: continue
        k += 1; rs = _LOSTMAP[e['status']]; d = dd(e['date']) + dt.timedelta(days=R.randint(6, 25)); d = d if d <= TODAY else TODAY
        gap = round(e['budget'] * (R.uniform(.08, .2) if rs == 'Price too high' else R.uniform(.02, .07)), 2)
        out.append(dict(lost_id='LO-%02d' % k, enquiry_id=e['enquiry_id'], lost_on=iso(d), reason=key('lreason', rs), price_gap=gap, won_by=R.choice(_WONBY[rs]), saved_by=R.choice(_SAVED[rs])))
    return out

# ---------- follow-up log (about 200)
def followups_d():
    R = rng('ta1fu'); out = []; k = 0
    for q in QUO:
        e = ENQD[q['enquiry_id']]; n = {'Open': 3, 'Accepted': 1, 'Declined': 2, 'Expired': 2}[q['status']]; d = dd(q['date_sent'])
        for j in range(n):
            d = d + dt.timedelta(days=R.randint(2, 6))
            if d > TODAY: d = TODAY - dt.timedelta(days=R.randint(0, 2))
            last = j == n - 1; nxt = ''
            if q['status'] == 'Open' and last: nxt = iso(TODAY + dt.timedelta(days=R.randint(-5, 6)))
            oc = ['Wants options', 'Needs more time', 'No answer', 'Waiting for a partner'][R.randint(0, 3)] if q['status'] != 'Accepted' else 'Will book'
            if q['status'] == 'Declined' and last: oc = 'Declined'
            if k == 0: nxt = iso(d + dt.timedelta(days=4))
            k += 1; out.append(nb(dict(fu_id='FU-%04d' % k, enquiry_id=q['enquiry_id'], quote_id=q['quote_id'], date=iso(d), channel=key('channel', R.choice(CHANNEL)), outcome=key('outcome', oc), next_touch_date=nxt)))
    return out

# ---------- marketing (140), terms (12), capacity (65), seasonal (12), pipeline (calculated)
def marketing_d():
    return [dict(mk_id='MK-%03d' % (i + 1), month=m['month'], source=key('msrc', m['source']), spend=m['spend'], leads=m['leads'], enquiries=m['enquiries'], bookings=m['bookings'], revenue=m['revenue']) for i, m in enumerate(MKT)]
TERMS = [('Quote validity', 'This quote is valid until the date shown. After that date prices and availability may change.', 'All trips'), ('Price changes', 'Supplier prices can change before full payment. We tell you at once and you may accept or cancel.', 'All trips'),
         ('Deposit', 'The deposit secures the price and the booking. It is due on the date shown on your booking confirmation.', 'All trips'), ('Final payment', 'The balance due before travel must reach us by the final payment date. A late payment can cancel the booking.', 'All trips'),
         ('Cancellation', 'Cancellation charges depend on the supplier terms. We show them before you pay. Our service fee is not refunded.', 'All trips'), ('Passport and entry duty', 'You are responsible for valid travel documents. Check the destination current rules before you book and before you travel.', 'All trips'),
         ('Insurance advice', 'We advise travel insurance for every traveller. If you decline it, we note your choice in writing.', 'All trips'), ('Changes after booking', 'A change may carry a supplier charge and our change fee. We quote both before we act.', 'All trips'),
         ('Service fee', 'Our service fee covers planning and booking work. It is shown as its own line and is before any tax.', 'All trips'), ('Traveller details', 'Names must match the travel documents. A correction after booking can cost money.', 'All trips'),
         ('Group trips', 'A group has a rooming list deadline. Rooms not named by then may be released or charged.', 'Group trip'), ('Cruise payments', 'Cruise deposits and final payments follow the cruise terms. The final payment date is the strictest one.', 'Cruise')]
def terms_d():
    R = rng('ta1terms')
    return [dict(term_id='TM-%02d' % (i + 1), clause=c, wording=w, applies_to=a, review_on=ahead(R.randint(-30, 120))) for i, (c, w, a) in enumerate(TERMS)]
def capacity_d():
    R = rng('ta1cap'); out = []; k = 0; w0 = week_start(TODAY)
    for off in range(-5, 8):
        for m in team[:5]:
            k += 1; avail = round(m['hours_week'] * 0.7)
            busy = {-5: .78, -4: .8, -3: .74, -2: .82, -1: .85, 0: .88, 1: .9, 2: .86, 3: .7, 4: .62, 5: .55, 6: .5, 7: .45}[off]
            com = round(avail * busy * R.uniform(.82, 1.18))
            out.append(dict(cap_id='CW-%03d' % k, week=iso(w0 + dt.timedelta(days=7 * off)), advisor=m['name'], hours_avail=avail, hours_committed=com))
    return out
def seasonal_d():
    out = []
    for i, k in enumerate(range(11, -1, -1)):
        m = month_start(k)
        enq = sum(1 for e in ENQ if dd(e['date']).month == m.month); qu = sum(1 for q in QUO if dd(q['date_sent']).month == m.month)
        bo = sum(1 for t in TRP if t['status'] not in ('Quoted', 'Cancelled') and dd(t['booked_on']).month == m.month)
        out.append(dict(sea_id='SD-%02d' % (i + 1), month=iso(m), enquiries=enq, quotes=qu, bookings=bo))
    return out
def pipeline_d():
    return [dict(pl_id='PL-%02d' % (i + 1), month=iso(m)) for i, m in enumerate(months14())]
