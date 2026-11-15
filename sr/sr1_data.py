"""Short-term rental host suite part 1: demo rows from sr_core (full generator output for aggregated tables, thinned rows elsewhere)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr1_lists import *
import collections

dd = to_date
R = rng('sr1')
BKF = booking_rows(); BKD = {b['booking_id']: b for b in BKF}
UNI = {u['unit_id']: u for u in units}; UNN = {u['name']: u for u in units}
OWNP = {o['name']: o['phone'] for o in owners}
OWNER_PHONE = team[0]['phone']; COHOST_PHONE = team[1]['phone']
ACCT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
ST = story()
SEAS_F = {s['month_no']: s['price_factor'] for s in season_rows()}
SEAS_K = {s['month_no']: s['season'] for s in season_rows()}
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def sk(m): return key('season', SEAS_K[m])
def band(lead):
    return key('band', 'Same week' if lead <= 6 else 'One to two weeks' if lead <= 14 else 'Two to four weeks' if lead <= 28 else 'One to three months' if lead <= 90 else 'Over three months')
def lt(d1, d2): return d1 < d2

# ---------- units (12)
def units_d():
    return [nb(dict(unit_id=u['unit_id'], name=u['name'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), bedrooms=u['bedrooms'], max_guests=u['max_guests'], owner=u['owner'],
                    owner_phone=OWNP[u['owner']], base_rate=u['base_rate'], cleaning_fee=u['cleaning_fee'], mgmt_pct=u['mgmt_pct'], rent=u['rent'], utilities=u['utilities'], internet=u['internet'],
                    since=u['since'], cohost=key('yn', u['cohost']))) for u in units]

# ---------- pricing calendar (156)
def pricing_d():
    out = []
    for r in price_rows():
        out.append(nb(dict(price_id=r['row_id'], week=r['week'], unit=r['unit'], season_factor=r['season_factor'], demand_index=r['demand_index'],
                           event=r['event'], base_rate=r['base_rate'], listed_rate=r['listed_rate'], booked_nights=r['booked_nights'], free_nights=r['free_nights'],
                           avg_booked_rate=r['avg_booked_rate'], min_stay=r['min_stay'])))
    return out

# ---------- seasons (12)
def seasons_d():
    return [dict(month='%d-%02d-01' % (TODAY.year, s['month_no']), season=sk(s['month_no']), price_factor=s['price_factor']) for s in season_rows()]

# ---------- bookings (about 490: every recent and upcoming booking, older ones thinned)
def bookings_d():
    recent = [b for b in BKF if b['check_in'] >= ago(75)]
    old = [b for b in BKF if b['check_in'] < ago(75)]
    step = max(1, round(len(old) / 300.0)); keep = old[::step]
    rows = sorted(keep + recent, key=lambda b: b['check_in'])
    out = []
    for i, b in enumerate(rows):
        out.append(nb(dict(booking_id=b['booking_id'], guest=b['guest'], guest_phone=fake_phone(int(b['booking_id'][3:])), guest_country=b['guest_country'], unit=b['unit'],
                           unit_type=key('utype', UNI[b['unit_id']]['unit_type']), city=key('city', b['city']), channel=key('chan', b['channel']), check_in=b['check_in'], check_out=b['check_out'],
                           booked_on=b['booked_on'], nights=b['nights'], lead_band=band(b['lead_days']), nightly_rate=b['nightly_rate'], room_revenue=b['room_revenue'], cleaning_fee=b['cleaning_fee'],
                           gross=b['gross'], status=key('bstatus', b['status']))))
    return out

# ---------- unit months (251)
def unit_months_d():
    out = []
    for r in unit_month_rows():
        m = int(r['month'][5:7])
        out.append(nb(dict(um_id=r['row_id'], month=r['month'], unit=r['unit'], city=key('city', r['city']), season=sk(m), available_nights=r['available_nights'], booked_nights=r['booked_nights'],
                           room_revenue=r['room_revenue'])))
    return out

# ---------- rate changes (120)
def rate_changes_d():
    r = rng('sr1-rc'); out = []
    spec = {'Season change': (-.08, .14), 'Event week': (.25, .45), 'Low demand': (-.12, -.05), 'High demand': (.05, .11), 'Competitor rate': (-.08, -.03), 'Gap night fill': (-.15, -.07),
            'Last-minute fill': (-.18, -.09), 'Review score': (-.06, .06), 'Cost increase': (.03, .06), 'Weekend lift': (.10, .15)}
    reasons = list(spec); w = [18, 6, 16, 14, 14, 8, 10, 4, 4, 6]
    days = sorted(set([int(r.uniform(2, 440)) for _ in range(125)] + [1, 3, 6, 8, 9, 12, 5, 2]), reverse=True)
    for d in days:
        u = r.choice(units); dt_ = dd(ago(d)); reason = r.choices(reasons, w)[0]; lo, hi = spec[reason]
        old = round(u['base_rate'] * SEAS_F[dt_.month] * r.uniform(.96, 1.05)); new = round(old * (1 + r.uniform(lo, hi)))
        if new == old: new += 1
        by = COHOST if (u['cohost'] == 'Yes' and r.random() < .55) else OWNER
        out.append(dict(date=ago(d), unit=u['name'], old_rate=old, new_rate=new, reason=key('reason', reason), changed_by=by))
    for i, x in enumerate(out, 1): x['rc_id'] = 'RC-%03d' % i
    return [{**{'rc_id': x['rc_id']}, **{k: v for k, v in x.items() if k != 'rc_id'}} for x in out]

# ---------- local events (14)
def events_d():
    ev0 = ST['pricing_week']
    rows = [('Local festival week', 'Lisbon', ev0, 6, .50), ('Harbour jazz weekend', 'Porto', ahead(70), 2, .25), ('Spring food week', 'Lisbon', ago(230), 6, .30), ('City marathon weekend', 'Porto', ago(40), 2, .35),
            ('Summer music festival', 'Cascais', ago(120), 3, .40), ('Surf championship', 'Cascais', ago(95), 4, .30), ('Forest lights evening', 'Sintra', ahead(35), 2, .20), ('Old town book fair', 'Lisbon', ago(300), 4, .18),
            ('Wine harvest weekend', 'Porto', ago(60), 2, .28), ('Palace garden concerts', 'Sintra', ago(150), 5, .22), ('Film festival week', 'Lisbon', ahead(120), 6, .32), ('Sailing regatta', 'Cascais', ahead(150), 3, .26),
            ('Tech conference week', 'Lisbon', ago(18), 4, .35), ('Christmas lights week', 'Porto', ahead(20), 6, .22)]
    out = []
    for i, (n, c, s, ln, lift) in enumerate(rows, 1):
        out.append(dict(event_id='EV-%02d' % i, event=n, city=key('city', c), start_date=s, end_date=iso(dd(s) + day(ln)), demand_lift=lift))
    return sorted(out, key=lambda x: x['start_date'])

# ---------- comparable listings (36)
_ADJ = ['Bright', 'Quiet', 'Modern', 'Charming', 'Sunny', 'Cosy', 'Stylish', 'Spacious', 'Renovated', 'Classic']
_KIND = {'Apartment': 'apartment', 'Loft': 'loft', 'Studio': 'studio', 'House': 'house', 'Cabin': 'cabin'}
_NEAR = {'Lisbon': ['the old town', 'the river', 'the market', 'the castle'], 'Porto': ['the river', 'the bridge', 'the market', 'the old town'], 'Cascais': ['the beach', 'the marina', 'the station', 'the old town'],
         'Sintra': ['the palace', 'the forest', 'the village', 'the station']}
def comps_d():
    r = rng('sr1-comp'); out = []; n = 0
    for u in units:
        for k in range(3):
            n += 1; f = r.uniform(.88, 1.22) if u['unit_id'] != ST['pricing_unit'] else r.uniform(1.12, 1.3)
            wk = round(u['base_rate'] * f); we = round(wk * r.uniform(1.08, 1.2))
            out.append(dict(comp_id='CL-%02d' % n, unit=u['name'], comparable='%s %s near %s' % (r.choice(_ADJ), _KIND[u['unit_type']], r.choice(_NEAR[u['city']])), city=key('city', u['city']),
                            bedrooms=max(1, u['bedrooms'] + r.choice([0, 0, 0, 1, -1]) if u['bedrooms'] > 1 else 1), weekday_rate=wk, weekend_rate=we, review_score=round(r.uniform(4.25, 4.95), 2), checked_on=ago(int(r.uniform(3, 150)))))
    return out

# ---------- discount rules (14)
def discounts_d():
    rows = [('Gap night of one or two free nights', 'Gap night', 'All units', 14, .10, 1, 'Yes'), ('Last minute, check-in within 3 days', 'Last minute', 'All units', 3, .15, 1, 'Yes'),
            ('Last minute for studios and lofts', 'Last minute', 'Studios and lofts', 7, .10, 1, 'Yes'), ('Weekly stay of 7 nights or more', 'Weekly stay', 'All units', 0, .08, 7, 'Yes'),
            ('Monthly stay of 28 nights or more', 'Monthly stay', 'All units', 0, .20, 28, 'Yes'), ('Returning guest, second stay', 'Returning guest', 'All units', 0, .07, 2, 'Yes'),
            ('Direct booking, no platform fee', 'Direct booking', 'All units', 0, .08, 2, 'Yes'), ('Low season midweek stay', 'Low season', 'Cascais and Sintra', 0, .12, 3, 'Yes'),
            ('Early booking, 90 days ahead', 'Early booking', 'Peak season', 90, .05, 4, 'Yes'), ('Last minute for houses and cabin', 'Last minute', 'Houses and cabin', 2, .12, 2, 'No'),
            ('Long weekend gap in the city', 'Gap night', 'Lisbon units', 21, .12, 2, 'No'), ('Winter monthly stay', 'Monthly stay', 'All units', 0, .25, 30, 'Yes'),
            ('Third stay for a loyal guest', 'Returning guest', 'All units', 0, .12, 3, 'No'), ('Low season weekly stay in the city', 'Low season', 'Lisbon and Porto', 0, .10, 7, 'No')]
    return [dict(rule_id='DR-%02d' % i, rule=a, trigger=key('dtrig', b), unit_scope=c, trigger_days=d, discount_pct=e, min_nights=f, active=key('yn', g)) for i, (a, b, c, d, e, f, g) in enumerate(rows, 1)]

# ---------- minimum-stay rules (24: six units x four seasons)
def minstay_d():
    base = {'Low': (1, 2, 1), 'Shoulder': (2, 2, 1), 'High': (2, 3, 1), 'Peak': (3, 3, 2)}; out = []; n = 0
    for ui, uid in enumerate(['UN-01', 'UN-02', 'UN-05', 'UN-07', 'UN-09', 'UN-11']):
        u = UNI[uid]
        for s in SEASONS:
            n += 1; a, b, c = base[s]
            if u['unit_type'] == 'Studio': a, b = max(1, a - 1), max(1, b - 0 if s != 'Peak' else b - 1)
            if u['unit_type'] == 'House': a, b = a + (1 if s in ('High', 'Peak') else 0), b + 1
            out.append(dict(ms_id='MS-%02d' % n, unit=u['name'], season=key('season', s), weekday_min=a, weekend_min=max(a, b), gap_min=c, review_on=ago(int(R.uniform(5, 160)))))
    return out

# ---------- gap nights (about 90) and last-minute fills (about 60)
def _gaps_all():
    by = {}
    for b in BKF:
        if b['status'] != 'Cancelled': by.setdefault(b['unit_id'], []).append(b)
    gaps, fills = [], []
    for uid, l in by.items():
        l.sort(key=lambda b: b['check_in'])
        for i in range(1, len(l)):
            p, n = l[i - 1], l[i]; g = (dd(n['check_in']) - dd(p['check_out'])).days
            if 1 <= g <= 3: gaps.append((uid, p['check_out'], g, n))
            if g == 0 and l[i]['nights'] <= 3 and (i + 1 >= len(l) or l[i + 1]['check_in'] <= (dd(l[i]['check_out']) + day(1)).isoformat()): fills.append((uid, l[i]))
    return gaps, fills

def gaps_d():
    gaps, fills = _gaps_all(); r = rng('sr1-gap'); out = []
    fills = [f for f in fills if f[1]['check_in'] <= ago(0)]
    fills.sort(key=lambda x: x[1]['check_in']); fsel = fills[-26:] + fills[::max(1, len(fills) // 22)][:24]
    ms0 = iso(month_start(0)); fsel += [(b['unit_id'], b) for b in BKF if b['status'] != 'Cancelled' and b['nights'] <= 3 and ms0 <= b['check_in'] <= ago(0)][:5]
    seen = set()
    for uid, b in fsel:
        if b['booking_id'] in seen: continue
        seen.add(b['booking_id']); u = UNI[uid]; d = r.choice([.08, .10, .12, .15]); usual = round(b['nightly_rate'] / (1 - d))
        out.append(dict(date=b['check_in'], unit=u['name'], nights_free=b['nights'], usual_rate=usual, discount_pct=d, filled=key('yn', 'Yes')))
    open_ = [g for g in gaps if g[1] <= ago(0)]; open_.sort(key=lambda g: g[1])
    msel = open_[-30:] + open_[::max(1, len(open_) // 30)][:30]
    s2 = set()
    for uid, d_, g, n in msel:
        if (uid, d_) in s2: continue
        s2.add((uid, d_)); u = UNI[uid]
        out.append(dict(date=d_, unit=u['name'], nights_free=g, usual_rate=round(u['base_rate'] * SEAS_F[dd(d_).month]), discount_pct=r.choice([0, .10, .10, .12]), filled=key('yn', 'No')))
    upc = [g for g in gaps if g[1] > ago(0)][:6]
    for uid, d_, g, n in upc:
        u = UNI[uid]; out.append(dict(date=d_, unit=u['name'], nights_free=g, usual_rate=round(u['base_rate'] * SEAS_F[dd(d_).month]), discount_pct=.10, filled=key('yn', 'No')))
    out.sort(key=lambda x: (x['date'], x['unit']))
    for i, x in enumerate(out, 1): x['gap_id'] = 'GN-%03d' % i
    return [{**{'gap_id': x['gap_id']}, **{k: v for k, v in x.items() if k != 'gap_id'}} for x in out]

def lastmin_d():
    r = rng('sr1-lm'); c = [b for b in BKF if b['status'] != 'Cancelled' and b['lead_days'] <= 5 and b['check_in'] <= ahead(6)]
    c.sort(key=lambda b: b['check_in']); sel = c[-34:] + c[:-34][::max(1, (len(c) - 34) // 26)][:26]
    sel.sort(key=lambda b: b['check_in']); out = []
    for i, b in enumerate(sel, 1):
        d = r.choice([.05, .08, .10, .12, .15, .18]); usual = round(b['nightly_rate'] / (1 - d))
        out.append(dict(lm_id='LM-%03d' % i, unit=b['unit'], check_in=b['check_in'], days_before=b['lead_days'], nights=b['nights'], usual_rate=usual, rate=round(b['nightly_rate']), channel=key('chan', b['channel'])))
    return out

# ---------- cleaning fee review (12), break-even (12)
def clean_fee_d():
    r = rng('sr1-cf'); out = []
    for u in units:
        sup = round(r.uniform(4, 8.5), 2); lin = round(r.uniform(4, 9) + u['bedrooms'] * 1.5, 2)
        share = {'UN-07': 1.08, 'UN-03': 0.9, 'UN-10': 0.86}.get(u['unit_id'], r.uniform(.5, .76))
        h = round(max(0.8, (u['cleaning_fee'] * share - sup - lin) / 17.0), 1)
        out.append(dict(unit=u['name'], unit_type=key('utype', u['unit_type']), cleaner_hours=h, supplies=sup, linen_cost=lin, review_on=ago(int(r.uniform(10, 170)))))
    return out

def breakeven_d():
    r = rng('sr1-be'); out = []
    for u in units:
        p = unit_profit(u['unit_id']); nights = max(p['nights'], 1)
        out.append(dict(unit=u['name'], other_fixed=round((p['maintenance'] + p['supplies']) / 12.0 + r.uniform(40, 90) + (u['base_rate'] * r.uniform(7.5, 9.5) if u['rent'] == 0 else 0)), var_per_night=round(r.uniform(5, 12) + (p['supplies'] / nights), 1),
                        target_occ=round(r.uniform(.58, .72), 2), review_on=ago(int(r.uniform(15, 200)))))
    return out

# ---------- direct offers (40)
def direct_offers_d():
    r = rng('sr1-do'); dirb = [b for b in BKF if b['channel'] == 'Direct' and b['status'] != 'Cancelled']; out = []
    tags = ['STAY', 'WELCOME', 'RETURN', 'WEEK', 'SPRING', 'SUMMER', 'AUTUMN', 'WINTER', 'EARLY']
    for i in range(40):
        u = units[i % 12] if i < 24 else r.choice(units)
        vf = dd(ago(int(r.uniform(-45, 460)) if i % 9 else int(r.uniform(2, 20)))); ln = r.choice([14, 21, 30, 45, 60]); vu = vf + day(ln)
        d = r.choice([.05, .06, .08, .10, .12, .15])
        n = [b for b in dirb if b['unit_id'] == u['unit_id'] and iso(vf) <= b['booked_on'] <= iso(vu) and b['booked_on'] <= ago(0)]
        bk = len(n) if r.random() < .8 else max(0, len(n) - 1)
        out.append(dict(valid_from=iso(vf), valid_until=iso(vu), unit=u['name'], code='%s%d-%s' % (r.choice(tags), int(d * 100), u['name'].split()[0].upper()[:5]), discount_pct=d, bookings=bk,
                        revenue=round(sum(b['room_revenue'] for b in n[:bk]), 2)))
    out.sort(key=lambda x: x['valid_from'])
    for i, x in enumerate(out, 1): x['offer_id'] = 'DO-%03d' % i
    return [{**{'offer_id': x['offer_id']}, **{k: v for k, v in x.items() if k != 'offer_id'}} for x in out]

# ---------- price experiments (24)
def experiments_d():
    r = rng('sr1-ex'); out = []
    for i in range(24):
        u = units[(i * 5) % 12] if i < 12 else r.choice(units); wk = r.choice([2, 3, 4, 4, 6])
        run = i in (3, 9, 15, 21); start = int(r.uniform(3, wk * 7 - 3)) if run else int(r.uniform(wk * 7 + 5, 430))
        up = r.random() < .6; mult = r.uniform(1.06, 1.18) if up else r.uniform(.84, .94)
        before = round(u['base_rate'] * r.uniform(.95, 1.25)); test = round(before * mult)
        nights = int(r.uniform(.4, .85) * wk * 7) if up else int(r.uniform(.55, .92) * wk * 7)
        if run: res = 'Running'; nights = int(nights * (start / (wk * 7.0)))
        else:
            ratio = (test * nights) / max(1.0, before * 0.62 * wk * 7)
            res = 'Rate worked' if ratio > 1.04 else ('Rate too high' if up and nights < .5 * wk * 7 else 'Rate too low' if not up and ratio < .95 else 'No clear result')
        out.append(dict(unit=u['name'], start_date=ago(start), weeks=wk, rate_before=before, rate_tested=test, nights_booked=max(nights, 1), result=key('expres', res)))
    out.sort(key=lambda x: x['start_date'])
    for i, x in enumerate(out, 1): x['ex_id'] = 'PX-%02d' % i
    return [{**{'ex_id': x['ex_id']}, **{k: v for k, v in x.items() if k != 'ex_id'}} for x in out]

# ---------- weekday pattern (84): check-in weekday, last 12 months
def weekday_d():
    out = []; n = 0
    acc = {}
    for b in BKF:
        if b['status'] == 'Cancelled' or not (ago(365) <= b['check_in'] <= ago(0)): continue
        f = SEAS_F[dd(b['check_in']).month]
        k = (b['unit_id'], dd(b['check_in']).weekday()); a = acc.setdefault(k, [0, 0.0]); a[0] += b['nights']; a[1] += b['nightly_rate'] * b['nights'] / f
    for u in units:
        for w in range(7):
            n += 1; a = acc.get((u['unit_id'], w), [0, 0.0])
            out.append(dict(wd_id='WD-%02d' % n, unit=u['name'], weekday=key('wday', WDAY[w]), booked_nights=a[0], adr=round(a[1] / a[0], 2) if a[0] else float(u['base_rate'])))
    return out

def channels_d():
    out = [dict(channel=c['channel'], fee_pct=c['fee_pct'], payout_days=c['payout_days']) for c in channels]
    out.append(dict(channel='Direct by bank transfer', fee_pct=0.01, payout_days=-7)); return out
def cities_d():
    r = rng('sr1-city'); out = []; adj = {'Lisbon': 1.0, 'Porto': 0.95, 'Cascais': 1.08, 'Sintra': 0.92}
    sf = {'Low': .85, 'Shoulder': 1.0, 'High': 1.12, 'Peak': 1.25}
    for c in cities:
        for sn in SEASONS: out.append(dict(city=key('city', c['city']), season=key('season', sn), tax_pct=c['tax_pct'], demand_factor=round(adj[c['city']] * sf[sn] * r.uniform(.97, 1.03), 2)))
    return out
def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'], hourly_rate=t['hourly_rate'],
                    speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]

if __name__ == '__main__':
    for n in ['units', 'pricing', 'seasons', 'bookings', 'unit_months', 'rate_changes', 'events', 'comps', 'discounts', 'minstay', 'gaps', 'lastmin', 'clean_fee', 'breakeven', 'direct_offers', 'experiments', 'weekday', 'channels', 'cities', 'team']:
        d = globals()[n + '_d'](); print(n, len(d))
    g = gaps_d(); print(collections.Counter(x['filled'] for x in g), sum(1 for x in g if x['date'][:7] == ago(0)[:7] and x['filled'] == 'yes'))
    print(sum(1 for x in lastmin_d() if x['check_in'][:7] == ago(0)[:7]), sum(1 for x in rate_changes_d() if x['date'][:7] == ago(0)[:7]))
    print(collections.Counter(x['result'] for x in experiments_d()))
