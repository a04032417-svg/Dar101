"""Car rental suite part 1: demo rows from cr_core (thinned where large; aggregated tables built from the full generator output)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr1_lists import *
import cr_core as C

ST = story()
dd = to_date
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def mfirst(s): return iso(D(dd(s).year, dd(s).month, 1))

ENQ_ALL = enquiry_rows()
ENQ = enquiry_rows(n=600)
RN = renter_rows()
CLS = {c['class']: c for c in classes}
HANDLER_OK = set(HANDLERS)
OWNER_PHONE = [t for t in team if t['name'] == OWNER][0]['phone']
MANAGER_PHONE = [t for t in team if t['name'] == MANAGER][0]['phone']
ACCOUNTANT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
BOOKKEEPER_PHONE = [t for t in team if t['role'] == 'Bookkeeper'][0]['phone']
HOTEL_PHONE = fake_phone(41)
MARKET_PHONE = fake_phone(42)

# ---- enquiries (600 recent)
def _loc(eid):
    r = rng('cr1-loc' + eid).random()
    return 'Main lot' if r < 0.42 else 'Airport delivery' if r < 0.62 else 'Hotel district' if r < 0.74 else 'Hotel strip' if r < 0.82 else 'Home delivery'

def enquiries_d():
    out = []
    for x in ENQ:
        i = int(x['enquiry_id'][3:]); r = rng('cr1-nf' + x['enquiry_id'])
        nf = ''
        if x['status'] == 'Lost' and x['lost_reason'] == 'No car free': nf = iso(dd(x['pickup_date']) + C.day(r.randint(3, 7)))
        rn = RN[(i * 7) % len(RN)]
        out.append(nb(dict(enquiry_id=x['enquiry_id'], date=x['date'], month=x['month'], source=key('source', x['source']), contact=rn['renter'], phone=fake_phone(i),
            **{'class': key('class', x['class_wanted'])}, pickup_date=x['pickup_date'], days=x['days'], location=key('location', _loc(x['enquiry_id'])), season=key('season', C._season(x['pickup_date'])),
            quote_amount=x['quote_amount'] or '', first_reply_hours=(round(x['first_reply_hours'], 2) if x['status'] != 'Open' else ''), status=key('estatus', x['status']),
            lost_reason=(key('lostreason', x['lost_reason']) if x['lost_reason'] else ''), booking_id=x['booking_id'], staff=key('handler', x['staff']), next_free=nf)))
    k = max(j for j, r in enumerate(out) if r.get('lost_reason') == 'no_car_free' and r.get('next_free'))
    out.insert(0, out.pop(k))
    return out

# ---- rate card (18)
def rates_d():
    out = []; n = 0
    for c in classes:
        for plan, rate, ly, days in (('Daily', c['daily_rate'], c['last_year_daily'], 1), ('Weekly', c['weekly_rate'], round(c['weekly_rate'] / 1.04), 7), ('Monthly', c['monthly_rate'], round(c['monthly_rate'] / 1.04), 30)):
            n += 1
            out.append(dict(rate_id='RC-%02d' % n, **{'class': key('class', c['class'])}, plan=key('plan', plan), rate=rate, last_year_rate=ly, days=days, deposit=c['deposit'], buffer_min=c['buffer_min'],
                            seats=c['seats'], miles_day=c['included_miles_day']))
    return out

def classes_d(): return [dict(**{'class': key('class', c['class'])}, daily_rate=c['daily_rate'], deposit=c['deposit']) for c in classes]
def seasons_d(): return [dict(season=s['season'], multiplier=s['multiplier'], months=s['months']) for s in seasons] + [dict(season='Event weekend', multiplier=1.2, months='Event weekends and long weekends, see the season calendar')]
def events_d():
    out = [dict(event_id=e['event_id'], event=e['event'], kind=key('ekind', e['kind']), start=e['start'], end=e['end'], uplift=e['uplift']) for e in event_rows()]
    k = next(j for j, r in enumerate(out) if r['start'] >= iso(TODAY))
    out.insert(0, out.pop(k)); return out
def addons_d(): return [dict(addon=key('addon', a['addon']), price_day=a['price_day'], unit_cost_day=a['unit_cost_day']) for a in addons]
def zones_d(): return [dict(location=key('location', l['location']), fee_leg=l['fee_leg'], run_minutes=l['run_minutes']) for l in locations]
def channels_d(): return [dict(channel=key('channel', c['channel']), fee_pct=c['fee_pct'], payout_days=c['payout_days']) for c in channels]

# ---- add-on lines (about 13 months)
def addon_lines_d():
    rows = addon_rows(n=1100); seen = set(); out = []
    for x in rows:
        first = x['booking_id'] not in seen; seen.add(x['booking_id'])
        out.append(dict(line_id=x['line_id'], booking_id=x['booking_id'], start_date=x['start_date'], month=x['month'], channel=key('channel', x['channel']), addon=key('addon', x['addon']),
                        days=x['days'], amount=x['amount'], cost=x['cost'], first_line=first))
    return out

# ---- cost per rented day by class, last 12 months of vehicle months (financing, insurance, maintenance, cleaning, fuel or charge, depreciation)
def cost_floor_d():
    agg = {}
    for x in vehicle_month_rows():
        if x['month'] < iso(month_start(12)): continue
        a = agg.setdefault(x['class'], [0.0, 0])
        a[0] += sum(x[k] for k in ('financing', 'insurance', 'maintenance', 'cleaning', 'fuel_charge', 'depreciation')); a[1] += x['rented_days']
    return [dict(**{'class': key('class', c['class'])}, cost_day=round(agg[c['class']][0] / agg[c['class']][1], 2)) for c in classes]
COST_DAY = {r['class']: r['cost_day'] for r in cost_floor_d()}

# ---- quote log (40 quotes)
def quote_log_d():
    q = [x for x in ENQ if x['quote_amount'] > 0 and x['status'] in ('Booked', 'Lost', 'Quoted')]
    recent = [x for x in q if x['date'] >= ago(30)]; older = [x for x in q if ago(100) <= x['date'] < ago(30)]
    pick = recent[::max(1, len(recent) // 14)][:14] + older[::max(1, len(older) // 26)][:26]
    pick.sort(key=lambda x: x['date'])
    out = []
    for n, x in enumerate(pick, 1):
        i = int(x['enquiry_id'][3:]); rn = RN[(i * 7) % len(RN)]
        out.append(dict(quote_id='QL-%03d' % n, quote_date=x['date'], contact=rn['renter'], phone=fake_phone(i), **{'class': key('class', x['class_wanted'])}, pickup_date=x['pickup_date'],
                        days=x['days'], location=key('location', _loc(x['enquiry_id'])), season=key('season', C._season(x['pickup_date'])), quote_amount=x['quote_amount']))
    return out

# ---- funnel by month (24 months)
def funnel_d():
    bk = {}
    for b in booking_rows():
        if b['status'] in ('Cancelled', 'No-show'): continue
        bk[mfirst(b['start_date'])] = bk.get(mfirst(b['start_date']), 0) + 1
    out = []
    for k in range(23, -1, -1):
        m = iso(month_start(k)); rows = [x for x in ENQ_ALL if x['month'] == m]
        if not rows: continue
        rep = [x['first_reply_hours'] for x in rows if x['status'] != 'Open']; qs = [x['quote_amount'] for x in rows if x['quote_amount'] > 0]
        out.append(dict(month=m, enquiries=len(rows), quoted=len(qs), booked=sum(1 for x in rows if x['status'] == 'Booked'), lost=sum(1 for x in rows if x['status'] == 'Lost'),
                        avg_reply_hours=round(sum(rep) / len(rep), 2), avg_quote=round(sum(qs) / len(qs), 2), bookings_all=bk.get(m, 0)))
    return out

# ---- month seasonality (12)
def month_season_d():
    num, den = {}, {}
    for b in booking_rows():
        if b['status'] in ('Cancelled', 'No-show'): continue
        mth = dd(b['start_date']).month; num[mth] = num.get(mth, 0) + b['rental_amount']; den[mth] = den.get(mth, 0) + b['days']
    seas = ['Off-peak', 'Off-peak', 'Shoulder', 'Shoulder', 'Shoulder', 'Peak', 'Peak', 'Peak', 'Shoulder', 'Shoulder', 'Off-peak', 'Holiday']
    return [dict(moy=key('moy', MONTHS[i]), month_no=i + 1, season=key('season', seas[i]), avg_day_rate=round(num[i + 1] / den[i + 1], 2)) for i in range(12)]

def lost_reasons_d(): return [dict(reason=key('lostreason', r)) for r in LOST_REASONS]
def sources_d(): return [dict(source=key('channel', c)) for c in CHANNELS]
def bands_d(): return [dict(band=key('band', b)) for b in BANDS]
def weekday_d(): return [dict(weekday=key('wday', w)) for w in WEEKDAYS]
def open_quotes_d(): return [dict(enquiry=x['enquiry_id']) for x in ENQ if x['status'] == 'Quoted']
def discount_steps_d(): return [dict(rate_id=r['rate_id']) for r in rates_d()]
def addon_profit_d(): return [dict(addon=key('addon', a)) for a in ADDONS]

# values the tools and settings use as defaults
_next_months = [month_start(-k) for k in range(1, 13)]
_SEAS = ['Off-peak', 'Off-peak', 'Shoulder', 'Shoulder', 'Shoulder', 'Peak', 'Peak', 'Peak', 'Shoulder', 'Shoulder', 'Off-peak', 'Holiday']
SEASON_CHANGE = next(iso(m) for m in _next_months if _SEAS[m.month - 1] != _SEAS[TODAY.month - 1])
_y3 = [x for x in funnel_d()]
