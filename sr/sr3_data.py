"""Short-term rental host suite part 3: demo rows from sr_core (full generator output for aggregated tables, thinned rows elsewhere)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr3_lists import *
import sr_core as core
import collections, datetime as dtm

dd = to_date
R = rng('sr3')
BKF = booking_rows(); NCB = [b for b in BKF if b['status'] != 'Cancelled']
UNI = {u['unit_id']: u for u in units}; UNN = {u['name']: u for u in units}
OWNP = {o['name']: o['phone'] for o in owners}
OWNER_PHONE = team[0]['phone']; COHOST_PHONE = team[1]['phone']
ACCT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
HANDY_PHONE = [t for t in team if t['role'] == 'Handyperson'][0]['phone']
CITY_CLEANER = dict(zip(CITIES, CLEANERS))
ST = story()
SEASM = {s['month_no']: s for s in season_rows()}
UMF = unit_month_rows()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def sk(m): return key('season', SEASM[m]['season'])
def mdays(d): return (add_months(d, 1) - d).days
def ms(k): return month_start(k)
def nth(i, p='X', w=3): return '%s-%0*d' % (p, w, i)
def D(d, n): return (d + dtm.timedelta(days=n)).isoformat()

# ---------- units (12)
def units_d():
    return [nb(dict(unit_id=u['unit_id'], name=u['name'], unit_type=key('utype', u['unit_type']), city=key('city', u['city']), bedrooms=u['bedrooms'], owner=u['owner'], owner_phone=OWNP[u['owner']],
                    base_rate=u['base_rate'], since=u['since'], cleaner=CITY_CLEANER[u['city']])) for u in units]

# ---------- seasons (12) and cities (16)
def seasons_d():
    return [dict(month='%d-%02d-01' % (TODAY.year, s['month_no']), season=sk(s['month_no']), price_factor=s['price_factor']) for s in season_rows()]
def cities_d():
    r = rng('sr3-city'); out = []; adj = {'Lisbon': 1.0, 'Porto': 0.95, 'Cascais': 1.08, 'Sintra': 0.92}; sf = {'Low': .85, 'Shoulder': 1.0, 'High': 1.12, 'Peak': 1.25}
    for c in cities:
        for sn in SEASONS: out.append(dict(city=key('city', c['city']), season=key('season', sn), tax_pct=c['tax_pct'], demand_factor=round(adj[c['city']] * sf[sn] * r.uniform(.97, 1.03), 2)))
    return out
def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'], hourly_rate=t['hourly_rate'],
                    speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]

# ---------- unit months (251)
def unit_months_d():
    out = []
    for r in UMF:
        m = int(r['month'][5:7])
        out.append(nb(dict(um_id=r['row_id'], month=r['month'], unit=r['unit'], city=key('city', r['city']), unit_type=key('utype', UNI[r['unit_id']]['unit_type']), season=sk(m),
                           available_nights=r['available_nights'], booked_nights=r['booked_nights'], room_revenue=round(r['room_revenue']))))
    return out

# ---------- bookings (about 480)
def bookings_d():
    recent = [b for b in BKF if b['check_in'] >= ago(75)]; old = [b for b in BKF if b['check_in'] < ago(75)]
    step = max(1, round(len(old) / 300.0)); rows = sorted(old[::step] + recent, key=lambda b: b['check_in'])
    return [nb(dict(booking_id=b['booking_id'], guest=b['guest'], guest_country=b['guest_country'], unit=b['unit'], unit_type=key('utype', UNI[b['unit_id']]['unit_type']), city=key('city', b['city']),
                    channel=key('chan', b['channel']), check_in=b['check_in'], check_out=b['check_out'], booked_on=b['booked_on'], nights=b['nights'], nightly_rate=round(b['nightly_rate']),
                    room_revenue=round(b['room_revenue']), status=key('bstatus', b['status']))) for b in rows]

# ---------- aggregates from the full history
def _agg(keyf):
    a = collections.defaultdict(lambda: [0, 0, 0.0])
    for r in UMF:
        x = a[keyf(r)]; x[0] += r['available_nights']; x[1] += r['booked_nights']; x[2] += r['room_revenue']
    return a
def city_months_d():
    a = _agg(lambda r: (r['month'], r['city'])); out = []
    for i, ((m, c), (av, bk, rv)) in enumerate(sorted(a.items()), 1):
        out.append(dict(cm_id=nth(i, 'CM'), month=m, city=key('city', c), available_nights=av, booked_nights=bk, room_revenue=round(rv)))
    return out
def type_months_d():
    a = _agg(lambda r: (r['month'], UNI[r['unit_id']]['unit_type'])); out = []
    for i, ((m, t), (av, bk, rv)) in enumerate(sorted(a.items()), 1):
        out.append(dict(tm_id=nth(i, 'TM'), month=m, unit_type=key('utype', t), available_nights=av, booked_nights=bk, room_revenue=round(rv)))
    return out

# ---------- targets (12)
TOCC = {}
def _tocc():
    base = {'Lisbon': .70, 'Porto': .66, 'Cascais': .64, 'Sintra': .58}; adj = {'Apartment': 0, 'Loft': .02, 'Studio': .03, 'House': -.02, 'Cabin': -.04}
    for u in units: TOCC[u['unit_id']] = round(base[u['city']] + adj[u['unit_type']] + (R.uniform(-.015, .015)), 2)
    TOCC[ST['unit_losing']] = .62
_tocc()
TADR = {u['unit_id']: int(round(u['base_rate'] * 1.04 / 5.0) * 5) for u in units}
def targets_d():
    out = []
    for i, u in enumerate(units):
        goal = round(TADR[u['unit_id']] * TOCC[u['unit_id']] * 365 / 500.0) * 500
        out.append(dict(unit=u['name'], target_occ=TOCC[u['unit_id']], target_adr=TADR[u['unit_id']], goal_year=goal, set_on=ago(300 + i * 9)))
    return out

# ---------- pace rows (6 months x 12 units)
def pace_d():
    r = rng('sr3-pace'); out = []; bias = {u['unit_id']: r.uniform(-.10, .12) for u in units}
    bias[ST['unit_losing']] = -.16; bias[ST['low_review_unit']] = -.13; bias[ST['pricing_unit']] = .14
    real = {(x['month'], x['unit_id']): x for x in UMF}; i = 0
    for k in range(0, 6):
        m = add_months(ms(0), k); key_m = m.isoformat()
        for u in units:
            x = real.get((key_m, u['unit_id']))
            if x: av, now = x['available_nights'], x['booked_nights']
            else:
                av = mdays(m); now = int(round(av * 0.62 * core._OCC[m.month] * r.uniform(.25, .42) * (1 - 0.05 * (k - 3))))
            ago_n = int(round(now * (r.uniform(.78, .92) if k == 0 else r.uniform(.68, .86) if k == 1 else r.uniform(.58, .80))))
            f = 1.0 - bias[u['unit_id']] + r.uniform(-.05, .05)
            if k == 0 and u['unit_id'] in ('UN-02', 'UN-05'): f = 0.90
            target = max(1, int(round(now * f))); i += 1
            out.append(dict(pace_id=nth(i, 'PC'), month=key_m, unit=u['name'], available_nights=av, booked_ago=min(ago_n, now), booked_now=now, target_nights=target))
    return out

# ---------- blocked nights (about 70)
def blocked_d():
    r = rng('sr3-block'); out = []
    reasons = ['Owner stay', 'Repair', 'Deep clean', 'Renovation', 'Photo shoot', 'Personal use', 'Inspection']; w = [18, 22, 16, 5, 8, 14, 17]
    lens = {'Owner stay': (3, 9), 'Repair': (1, 4), 'Deep clean': (1, 2), 'Renovation': (8, 14), 'Photo shoot': (1, 1), 'Personal use': (2, 7), 'Inspection': (1, 1)}
    for d in sorted(set(int(r.uniform(20, 470)) for _ in range(62)), reverse=True):
        reason = r.choices(reasons, w)[0]; out.append(dict(unit=r.choice(units)['name'], from_date=ago(d), reason=reason, n=r.randint(*lens[reason])))
    for j, (uid, reason, n) in enumerate([('UN-03', 'Repair', 2), ('UN-08', 'Deep clean', 1), ('UN-05', 'Owner stay', 4)]):
        out.append(dict(unit=UNI[uid]['name'], from_date=D(ms(0), min(j, TODAY.day - 1)), reason=reason, n=n))
    out.append(dict(unit=UNI['UN-06']['name'], from_date=ago(6), reason='Renovation', n=10))
    out.append(dict(unit=UNI['UN-02']['name'], from_date=ahead(9), reason='Owner stay', n=5)); out.append(dict(unit=UNI['UN-04']['name'], from_date=ahead(20), reason='Repair', n=3))
    out.sort(key=lambda x: x['from_date'])
    return [dict(block_id=nth(i, 'BL'), unit=x['unit'], from_date=x['from_date'], to_date=D(dd(x['from_date']), x['n'] - 1), reason=key('breason', x['reason'])) for i, x in enumerate(out, 1)]

# ---------- weekday pattern (84)
def weekday_d():
    w0 = dd(ago(365)); cnt = collections.defaultdict(lambda: [0, 0.0])
    for b in NCB:
        rate = b['room_revenue'] / b['nights']; d0 = dd(b['check_in'])
        for n in range(b['nights']):
            d = d0 + dtm.timedelta(days=n)
            if w0 <= d < TODAY: x = cnt[(b['unit_id'], d.weekday())]; x[0] += 1; x[1] += rate
    out = []; i = 0
    for u in units:
        st = max(w0, dd(u['since']))
        for wd in range(7):
            av = sum(1 for n in range((TODAY - st).days) if (st + dtm.timedelta(days=n)).weekday() == wd)
            bk, rv = cnt[(u['unit_id'], wd)]; bk = min(bk, av); i += 1
            out.append(dict(wd_id=nth(i, 'WD'), unit=u['name'], weekday=key('wday', WDAY[wd]), available_nights=av, booked_nights=bk, room_revenue=round(rv)))
    return out

# ---------- lead time curve (60)
def lead_time_d():
    out = []; i = 0
    def bnd(l): return 'Same week' if l <= 6 else 'One to two weeks' if l <= 14 else 'Two to four weeks' if l <= 28 else 'One to three months' if l <= 90 else 'Over three months'
    for k in range(11, -1, -1):
        m = ms(k); a = {b: [0, 0, 0.0] for b in BAND}
        for b in NCB:
            if dd(b['check_in']).replace(day=1) == m: x = a[bnd(b['lead_days'])]; x[0] += 1; x[1] += b['nights']; x[2] += b['room_revenue']
        for b in BAND:
            i += 1; out.append(dict(lt_id=nth(i, 'LT'), month=m.isoformat(), lead_bucket=key('band', b), bookings=a[b][0], nights=a[b][1], revenue=round(a[b][2])))
    return out

# ---------- year on year (about 80)
def yoy_d():
    real = {(x['month'], x['unit_id']): x for x in UMF}; out = []; i = 0
    for k in range(1, 12):
        m = ms(k); m0 = ms(k + 12)
        for u in units:
            a = real.get((m.isoformat(), u['unit_id'])); b = real.get((m0.isoformat(), u['unit_id']))
            if a and b and b['booked_nights'] > 0:
                i += 1; out.append(dict(yy_id=nth(i, 'YY'), unit=u['name'], month=m.isoformat(), nights_this=a['booked_nights'], nights_last=b['booked_nights'], revenue_this=round(a['room_revenue']), revenue_last=round(b['room_revenue'])))
    return out

# ---------- orphan nights (about 55)
def orphan_d():
    r = rng('sr3-orph'); out = []
    for d in sorted(set(int(r.uniform(14, 420)) for _ in range(44)), reverse=True):
        u = r.choice(units); n = r.choices([1, 2, 3], [55, 30, 15])[0]; filled = r.random() < .66
        out.append(dict(date=ago(d), unit=u['name'], gap_length=n, filled=filled, revenue_recovered=round(n * u['base_rate'] * r.uniform(.78, .96)) if filled else 0))
    for j, (uid, n, f) in enumerate([('UN-01', 1, True), ('UN-04', 2, True), ('UN-09', 1, False)]):
        u = UNI[uid]; out.append(dict(date=D(ms(0), min(j, TODAY.day - 1)), unit=u['name'], gap_length=n, filled=f, revenue_recovered=round(n * u['base_rate'] * .88) if f else 0))
    for j, (uid, n) in enumerate([('UN-03', 1), ('UN-11', 2), ('UN-07', 1)]):
        out.append(dict(date=ahead(4 + 3 * j), unit=UNI[uid]['name'], gap_length=n, filled=False, revenue_recovered=0))
    out.sort(key=lambda x: x['date'])
    return [dict(orphan_id=nth(i, 'OR'), date=x['date'], unit=x['unit'], gap_length=x['gap_length'], filled=key('yn', 'Yes' if x['filled'] else 'No'), revenue_recovered=x['revenue_recovered']) for i, x in enumerate(out, 1)]

# ---------- review scores (60): rolling 90 days at the end of each month
def review_scores_d():
    rv = review_rows(); out = []; i = 0
    for k in range(4, -1, -1):
        end = TODAY if k == 0 else (add_months(ms(k), 1) - dtm.timedelta(days=1))
        for u in units:
            xs = [x['rating'] for x in rv if x['unit_id'] == u['unit_id'] and end - dtm.timedelta(days=90) < dd(x['date']) <= end]
            if not xs: xs = [x['rating'] for x in rv if x['unit_id'] == u['unit_id']][-6:] or [5]
            i += 1; out.append(dict(rs_id=nth(i, 'RS'), month=ms(k).isoformat(), unit=u['name'], reviews=len(xs), avg_rating=round(sum(xs) / len(xs), 2)))
    return out

# ---------- channel mix (about 48)
def channel_mix_d():
    a = collections.defaultdict(lambda: [0, 0.0]); w0 = ago(365)
    for b in NCB:
        if b['check_in'] >= w0: x = a[(b['unit_id'], b['channel'])]; x[0] += b['nights']; x[1] += b['room_revenue']
    out = []; i = 0
    for u in units:
        for c in CHANNELS:
            n, rv = a[(u['unit_id'], c)]
            if n > 0: i += 1; out.append(dict(cx_id=nth(i, 'CX'), unit=u['name'], channel=key('chan', c), nights=n, room_revenue=round(rv)))
    return out

# ---------- stay length mix (about 55)
def stay_mix_d():
    def bk(n): return 'One night' if n == 1 else 'Two nights' if n == 2 else 'Three to four nights' if n <= 4 else 'Five to seven nights' if n <= 7 else 'Over seven nights'
    a = collections.defaultdict(lambda: [0, 0, 0.0]); w0 = ago(365)
    for b in NCB:
        if b['check_in'] >= w0: x = a[(b['unit_id'], bk(b['nights']))]; x[0] += 1; x[1] += b['nights']; x[2] += b['room_revenue']
    out = []; i = 0
    for u in units:
        for s in STAY:
            c, n, rv = a[(u['unit_id'], s)]
            if c > 0: i += 1; out.append(dict(sx_id=nth(i, 'SX'), unit=u['name'], stay_bucket=key('stay', s), bookings=c, nights=n, revenue=round(rv)))
    return out

# ---------- performance reviews (about 36)
FINDS = [('Occupancy below target for three months', 'Cut weekday rates by 8 percent and shorten the minimum stay'), ('ADR below the base rate in shoulder months', 'Raise the weekend rate and stop deep discounts'),
         ('Cleanliness score under 4 in recent reviews', 'Retrain the cleaner and add a photo checklist to each turnover'), ('Many orphan nights between bookings', 'Allow one-night gaps and offer a gap discount'),
         ('Weekday nights empty while weekends sell out', 'Add a midweek offer and a longer weekend minimum stay'), ('Pace behind target for next month', 'Lower the rate 6 percent for three weeks and refresh the photos'),
         ('Strong ADR but low occupancy', 'Test a 5 percent price cut for two weeks'), ('Revenue down against last year', 'Review comparable listings and update the title and photos'),
         ('Occupancy far above target', 'Raise the base rate 7 percent for the next season'), ('Late bookings dominate', 'Open dates further ahead and set a lower last-minute floor')]
def perf_reviews_d():
    r = rng('sr3-pr')
    rows = [(d, r.choice(units)) for d in sorted(set(int(r.uniform(30, 380)) for _ in range(30)), reverse=True)]
    rows += [(40, UNI[ST['unit_losing']]), (34, UNI[ST['low_review_unit']]), (14, UNI[ST['low_review_unit']]), (11, UNI['UN-02']), (6, UNI[ST['unit_losing']]), (3, UNI['UN-05'])]
    rows.sort(key=lambda x: -x[0]); out = []
    for i, (d, u) in enumerate(rows, 1):
        fi = FINDS[2] if u['unit_id'] == ST['low_review_unit'] else FINDS[0] if u['unit_id'] == ST['unit_losing'] else r.choice(FINDS)
        by = COHOST if (u['cohost'] == 'Yes' and r.random() < .4) else OWNER
        due = D(dd(ago(d)), r.choice([14, 21, 30, 45]))
        row = dict(pr_id=nth(i, 'PR'), date=ago(d), unit=u['name'], finding=fi[0], action=fi[1], owner=by, due_date=due)
        if dd(due) < TODAY - dtm.timedelta(days=12) and r.random() < .9: row['done_on'] = D(dd(due), -r.randint(0, 9))
        out.append(row)
    out[-1]['due_date'] = ahead(4); out[-2]['due_date'] = ago(3); out[-3]['due_date'] = ahead(9); out[-4]['due_date'] = ago(8); out[-5]['due_date'] = ahead(30)
    for x in out[-5:]: x.pop('done_on', None)
    return out

# ---------- market comparison (48)
def market_d():
    r = rng('sr3-mk'); ob = {'Lisbon': .94, 'Porto': 1.0, 'Cascais': 1.05, 'Sintra': 1.10}; ab = {'Lisbon': .95, 'Porto': 1.03, 'Cascais': .97, 'Sintra': 1.06}; out = []; i = 0
    for k in range(11, -1, -1):
        m = ms(k).isoformat()
        for c in CITIES:
            rows = [y for y in UMF if y['month'] == m and y['city'] == c]
            av = sum(y['available_nights'] for y in rows); bk = sum(y['booked_nights'] for y in rows); rv = sum(y['room_revenue'] for y in rows)
            if not av: continue
            occ = bk / av; adr = rv / bk if bk else 100; i += 1
            out.append(dict(mk_id=nth(i, 'MK'), month=m, city=key('city', c), market_occupancy=round(min(.95, max(.3, occ * ob[c] * r.uniform(.96, 1.04))), 2), market_adr=round(adr * ab[c] * r.uniform(.96, 1.04))))
    return out

if __name__ == '__main__':
    for n in ['units', 'seasons', 'cities', 'team', 'unit_months', 'bookings', 'city_months', 'type_months', 'targets', 'pace', 'blocked', 'weekday', 'lead_time', 'yoy', 'orphan', 'review_scores', 'channel_mix', 'stay_mix', 'perf_reviews', 'market']:
        d = globals()[n + '_d'](); print(n, len(d))
    p = [x for x in pace_d() if x['month'] == ms(0).isoformat()]; print([(x['booked_now'], x['target_nights']) for x in p])
    w = weekday_d(); print(max(x['booked_nights'] / max(1, x['available_nights']) for x in w))
    print([ (x['unit'][:6], x['avg_rating']) for x in review_scores_d()[-12:]])
