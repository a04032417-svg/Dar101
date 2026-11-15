"""Car rental business suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (one cached world is built on first use). The demo business is "Brightwater Car & Van Rental"
(fictional): a small independent car and van rental run by an owner-operator (Nadia Haddad, CR-01) with a manager who also does bookings and billing (Tomas Kowalski, CR-02), two
detailers (CR-03, CR-04), two part-time delivery drivers (CR-05, CR-06), a weekend booking assistant (CR-07), a part-time bookkeeper (CR-08) and 8 outside contacts (accountant CR-09,
insurance broker CR-10, mechanic workshop CR-11, tyre supplier CR-12, body repair shop CR-13, towing service CR-14, car-wash supplier CR-15, lender CR-16). A fleet of 33 vehicles over
two years (28 now, 5 sold, 13 bought during the history) in 6 classes (Economy, Compact, Midsize SUV, 7-seat Van, Premium, Electric) with generic names ("Economy 01 Silver") and fake
plates, 55% financed. One main lot plus airport, hotel and home delivery zones. Daily, weekly and monthly rentals booked direct (website, phone, corporate accounts, a hotel partner)
and through two car-sharing marketplaces (Marketplace A and B, generic words). Seasonal and weekend rates, deposits and card holds (direct bookings only), add-ons (child seat, extra
driver, navigation unit, two cover options, young-driver fee, roof box), fees (extra mileage, late return, cleaning, fuel or charge refill, toll and ticket admin), damage claims as status
and amounts only, maintenance by service interval (miles and months), registration, insurance and inspection renewals. A single-car host can use most parts. One generic currency
(plain amounts, no symbol), distance in miles (the demo unit: set your own), every date relative to the build day. Renters appear as a first name plus an initial, an age band, a status, a fake phone number (for messages) and
dates only (no addresses, licence or card numbers, no photos).

Money model: day rate = class daily rate x season multiplier (Off-peak 0.85, Shoulder 1.0, Peak 1.25, Holiday 1.35) x 1.08 for a Friday pickup of up to 3 days; weekly and monthly plans
use the class weekly (/7) and monthly (/30) rate with half and 30% of the season uplift; corporate accounts get 8% off; rates were about 4% lower last year (before 1 January). rental =
day rate x days; add-ons = price a day x min(days, cap days); delivery fee = 2 x the zone fee per leg; total = rental + add-ons + delivery; marketplace and hotel-partner fee = total x the
channel fee share (A 20%, B 25%, hotel 10%); net = total - channel fee. Deposit by class on direct bookings only (held, released 5 days after return, or part kept for fees and
damage). Fees: extra mileage 0.35 a mile over the allowance (150 a day, 1000 a week, 3000 a month), late return 12 an hour after 59 minutes, cleaning 45, fuel or charge refill 10 + 6 per 10
points below the agreed level, toll and ticket admin 12 per item passed on. Per vehicle and month: profit = revenue (booking days allocated by day + fees collected + damage recoveries +
toll admin) - channel fees - financing payment - insurance (yearly premium / 12) - maintenance - turnaround cleaning cost - fuel or charge - depreciation (1.8% of price a month for the
first 41 months, example, set your own). Profit and loss adds staff pay (payroll, owner draw excluded) and overhead (rent, utilities, software, accounting, marketing, card fees, cleaning
supplies, registration, absorbed tolls). Cash = payments received (marketplace payouts as they arrive) - all expenses - down payments + sale proceeds - owner draw - tax set-aside.

Story rows (ids from story(), never hard-coded): low_vehicle (a Premium car at about 21% utilisation that loses money every month of the last 12), overlap_a / overlap_b (two bookings on
the same vehicle next week, the second from a marketplace), claim_id (a damage claim open 52+ days, the only open claim past 45 days, deposit still held), service_vehicle (an SUV 3,000+
miles past its service interval with a booking starting tomorrow), renewal_id (a registration renewal due in 10 days, the only renewal due within 45 days), payout_id (a Marketplace A
payout short-paid by 78.50) and late_payout_id (a Marketplace B payout late, the only 'Late' one).

Exports
  constants: COMPANY SUITE OWNER MANAGER HISTORY_START DEPOSIT_RELEASE_DAYS LATE_GRACE_MIN LATE_FEE_HOUR EXTRA_MILE_FEE CLEANING_FEE REFILL_STEP_FEE REFILL_SERVICE_FEE TOLL_ADMIN_FEE
             WEEKEND_UPLIFT DEP_PCT DEP_FLOOR UTIL_RED UTIL_GREEN EMPLOYER_COST_PCT CARD_FEE_PCT TAX_SET_ASIDE_PCT OWNER_DRAW OWNER_EXTRA CASH_FLOOR FEE_COLLECT_DAYS HORIZON_DAYS
  dates: TODAY iso ago ahead to_date month_start add_months months14() week_start; helpers pairs first_name fake_phone fake_email rng
  lists: ROLES TEAMS PAY_TYPES PAY_ROLES CLASSES FUELS VEH_STATUS CHANNELS CHANNEL_KINDS BOOK_STATUS PLANS SEASONS LOCATIONS RUN_KINDS RUN_STATUS ADDONS FEE_KINDS FEE_STATUS CLAIM_KINDS
         CLAIM_STATUS OPEN_CLAIM DEPOSIT_STATUS PAY_METHODS PAY_KINDS PAYOUT_STATUS INVOICE_STATUS MAINT_KINDS TOLL_KINDS TOLL_STATUS RENEWAL_KINDS RENEWAL_STATUS LOST_REASONS ENQ_STATUS
         SHIFT_TASKS RENTER_STATUS AGE_BANDS EXPENSE_CATEGORIES MARKETING_KINDS PAY_STATUS WEEKDAYS (7 days) EVENT_KINDS AGE_BUCKETS STAFF_NAMES
  people and reference: team (16: staff 8 + contacts 8), staff (8), contacts (8), classes (6: class_id class daily_rate weekly_rate monthly_rate last_year_daily deposit seats
         included_miles_day buffer_min), seasons (4), addons (7), fees (7), locations (5: location_id location kind fee_leg run_minutes one_way_miles), channels (6: channel kind fee_pct
         payout_days), service_types (9: service_type interval_miles interval_months typical_cost downtime_days); lookups CLS SEASON_MULT ADD LOC CH SVT VENDOR
  generators (fresh lists of dicts, oldest first; n= thins a long list but keeps the most recent rows; optional dates are '' when blank, optional numbers are '' only in a handover of a car
  still out):
    vehicle_rows (33) renter_rows (about 1,800) booking_rows (about 2,650) addon_rows handover_rows (check-out and check-in, odometer and fuel or charge level) fee_rows claim_rows
    deposit_rows payment_rows (all money in, marketplace payouts included) payout_rows invoice_rows (corporate accounts) toll_rows maintenance_rows renewal_rows financing_rows
    delivery_rows (delivery and collection runs) turnaround_rows (cleaning between rentals) shift_rows pay_rows enquiry_rows marketing_rows expense_rows vehicle_month_rows pnl_rows
    cash_rows tax_rows event_rows
  helpers: vehicle_profit(vehicle_id, months=12) class_utilisation(months=3) story() ; module _W() returns the cached world
Lesson: money cells are plain amounts; shares are 0..1 fractions; optional dates (released_on, closed_on, paid_on, renewed_on, passed_on) are '' when blank: wrap lookups with IF(x=0,"",x).
Links hold ids (VH-001 vehicle, RN-0001 renter, BK-00001 booking) or names (vehicle, class, channel, staff). Words: no brand, law or insurance advice; claims are status and amounts only.
"""
import datetime as dt
import calendar
import random
import hashlib
import math

COMPANY = 'Brightwater Car & Van Rental'
SUITE = 'fx-20261115-car-rental'
OWNER = 'Nadia Haddad'
MANAGER = 'Tomas Kowalski'
TODAY = dt.date.today()
D = dt.date

# shared settings defaults (editable "your number" values, example defaults, never a standard)
DEPOSIT_RELEASE_DAYS = 5
LATE_GRACE_MIN = 59
LATE_FEE_HOUR = 12.0
EXTRA_MILE_FEE = 0.35
CLEANING_FEE = 45.0
REFILL_STEP_FEE = 6.0
REFILL_SERVICE_FEE = 10.0
TOLL_ADMIN_FEE = 12.0
WEEKEND_UPLIFT = 0.08
DEP_PCT = 0.018                # monthly depreciation as a share of purchase price (example, set your own)
DEP_FLOOR = 0.25               # a vehicle is never written down below this share of its price
UTIL_RED = 0.60
UTIL_GREEN = 0.80
EMPLOYER_COST_PCT = 0.10
CARD_FEE_PCT = 0.018
TAX_SET_ASIDE_PCT = 0.25
OWNER_DRAW = 4500.0
OWNER_EXTRA = 4000.0           # a quarterly extra draw taken from cash
CASH_FLOOR = 8000.0
FEE_COLLECT_DAYS = 14
HORIZON_DAYS = 50              # bookings exist up to about this many days ahead


def day(n): return dt.timedelta(days=n)
def iso(d): return d.isoformat() if hasattr(d, 'isoformat') else d
def ago(days): return iso(TODAY - dt.timedelta(days=days))
def ahead(days): return iso(TODAY + dt.timedelta(days=days))
def to_date(s): return D.fromisoformat(s) if isinstance(s, str) and s else s


def month_start(k):
    y, m = TODAY.year, TODAY.month - k
    while m <= 0: m += 12; y -= 1
    while m > 12: m -= 12; y += 1
    return dt.date(y, m, 1)


def add_months(d, n):
    y, m = d.year, d.month + n
    while m > 12: m -= 12; y += 1
    while m <= 0: m += 12; y -= 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def months14(): return [month_start(k) for k in range(13, -1, -1)]
def week_start(d): return d - day(d.weekday())


def pairs(labels):
    out = []
    for s in labels:
        k = ''.join(ch if ch.isalnum() else '_' for ch in s.lower()).strip('_')
        while '__' in k: k = k.replace('__', '_')
        out.append((k, s))
    return out


def first_name(name): return name.split()[0]
def fake_phone(i): return '+%d %d 555 %04d' % ([1, 44, 49, 61, 33, 34, 351, 31][i % 8], 20 + (i * 7) % 79, 3000 + (i * 37) % 6000)
def fake_email(name, i=0): return name.lower().replace(' ', '.').replace("'", '').replace('-', '') + (str(i) if i else '') + '@mail.example.com'
def rng(tag=''): return random.Random('cr-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
def _hm(mins): return '%02d:%02d' % (mins // 60, mins % 60)
def _mins(t): return int(t[:2]) * 60 + int(t[3:5])
def _r15(m): return int(round(m / 15.0)) * 15


HISTORY_START = month_start(23)

# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Owner-operator', 'Manager', 'Detailer', 'Delivery driver', 'Booking assistant', 'Bookkeeper', 'Accountant', 'Insurance broker', 'Mechanic', 'Tyre supplier',
         'Body repair shop', 'Towing service', 'Car-wash supplier', 'Lender']
TEAMS = ['Management', 'Operations', 'Outside']
PAY_TYPES = ['Owner draw', 'Salary', 'Hourly', 'Invoice']
PAY_ROLES = ROLES[:6]
CLASSES = ['Economy', 'Compact', 'Midsize SUV', '7-seat Van', 'Premium', 'Electric']
FUELS = ['Petrol', 'Diesel', 'Hybrid', 'Electric']
VEH_STATUS = ['Active', 'In workshop', 'Sold']
CHANNELS = ['Website', 'Phone', 'Corporate account', 'Hotel partner', 'Marketplace A', 'Marketplace B']
CHANNEL_KINDS = ['Direct', 'Partner', 'Marketplace']
BOOK_STATUS = ['Booked', 'Active', 'Completed', 'Cancelled', 'No-show']
PLANS = ['Daily', 'Weekly', 'Monthly']
SEASONS = ['Off-peak', 'Shoulder', 'Peak', 'Holiday']
LOCATIONS = ['Main lot', 'Airport delivery', 'Hotel district', 'Hotel strip', 'Home delivery']
RUN_KINDS = ['Delivery', 'Collection']
RUN_STATUS = ['Done', 'Planned']
ADDONS = ['Child seat', 'Extra driver', 'Navigation unit', 'Cover option basic', 'Cover option plus', 'Young-driver fee', 'Roof box']
FEE_KINDS = ['Extra mileage', 'Late return', 'Cleaning', 'Fuel or charge refill']
FEE_STATUS = ['Collected', 'Billed', 'Written off', 'Not billed']
CLAIM_KINDS = ['Scratch', 'Dent', 'Windscreen chip', 'Interior damage', 'Tyre damage', 'Other']
CLAIM_STATUS = ['Reported', 'Estimate', 'In repair', 'Deposit used', 'Claim paid', 'Written off']
OPEN_CLAIM = ['Reported', 'Estimate', 'In repair']
DEPOSIT_STATUS = ['Held', 'Released', 'Part kept', 'Kept']
PAY_METHODS = ['Card', 'Cash', 'Bank transfer', 'Marketplace payout']
PAY_KINDS = ['Rental payment', 'Balance and fees', 'Invoice payment', 'Payout']
PAYOUT_STATUS = ['Paid', 'Short-paid', 'Late', 'Expected']
INVOICE_STATUS = ['Paid', 'Part paid', 'Unpaid', 'Written off']
MAINT_KINDS = ['Minor service', 'Major service', 'Tyre set', 'Brake service', 'Inspection', 'Battery check', 'Repair', 'Body repair', 'Towing']
TOLL_KINDS = ['Toll', 'Parking ticket', 'Traffic ticket']
TOLL_STATUS = ['Passed on', 'Open', 'No rental found', 'Absorbed']
RENEWAL_KINDS = ['Registration renewal', 'Insurance renewal', 'Inspection due']
RENEWAL_STATUS = ['Done', 'Upcoming']
LOST_REASONS = ['No car free', 'Price', 'Dates', 'No reply', 'Other']
ENQ_STATUS = ['Open', 'Quoted', 'Booked', 'Lost']
SHIFT_TASKS = ['Cleaning and prep', 'Delivery runs', 'Counter and bookings', 'Bookkeeping']
RENTER_STATUS = ['Verified', 'Documents due', 'Restricted']
AGE_BANDS = ['Under 25', '25 and over']
EXPENSE_CATEGORIES = ['Vehicle financing', 'Insurance', 'Maintenance and repairs', 'Tyres', 'Fuel and charging', 'Cleaning supplies', 'Channel fees', 'Card fees', 'Staff pay',
                      'Rent and lot', 'Utilities', 'Booking software', 'Marketing', 'Accounting', 'Registration and inspection', 'Tolls and tickets absorbed']
MARKETING_KINDS = ['Website upkeep', 'Marketplace listing boost', 'Local flyers', 'Search ads', 'Referral reward']
PAY_STATUS = ['Paid', 'Accruing']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
EVENT_KINDS = ['Holiday period', 'Event weekend', 'School break', 'Long weekend']
AGE_BUCKETS = ['0-7', '8-30', '31-60', '60+']

# ------------------------------------------------------------------ people
# id, name, country, role, team, pay type, hours a week, monthly salary, hourly rate, area, start days ago
_staff = [('CR-01', 'Nadia Haddad', 'Lebanon', 'Owner-operator', 'Management', 'Owner draw', 45, 0, 0, 'All areas', 2300),
          ('CR-02', 'Tomas Kowalski', 'Poland', 'Manager', 'Management', 'Salary', 40, 3400, 0, 'Bookings and billing', 1500),
          ('CR-03', 'Lucia Fernandes', 'Portugal', 'Detailer', 'Operations', 'Hourly', 32, 0, 17.5, 'Cleaning and prep', 1100),
          ('CR-04', 'Kofi Mensah', 'Ghana', 'Detailer', 'Operations', 'Hourly', 20, 0, 16.5, 'Cleaning and prep', 520),
          ('CR-05', 'Jun Park', 'South Korea', 'Delivery driver', 'Operations', 'Hourly', 24, 0, 16.0, 'Airport and hotel runs', 640),
          ('CR-06', 'Ravi Chandran', 'India', 'Delivery driver', 'Operations', 'Hourly', 16, 0, 16.0, 'Relief runs', 260),
          ('CR-07', 'Sana Malik', 'Pakistan', 'Booking assistant', 'Operations', 'Hourly', 16, 0, 17.0, 'Weekend counter', 380),
          ('CR-08', 'Elsa Nordin', 'Sweden', 'Bookkeeper', 'Management', 'Hourly', 8, 0, 24.0, 'Bookkeeping', 900)]
staff = []
for i, (a, b, c, ro, te, pt, hw, sal, hr, ar, st) in enumerate(_staff):
    staff.append(dict(staff_id=a, name=b, role=ro, team=te, pay_type=pt, phone=fake_phone(201 + i), email=fake_email(b), hours_week=hw, monthly_salary=float(sal),
                      hourly_rate=float(hr), area=ar, country=c, start=ago(st)))
_ctc = [('CR-09', 'Ingrid Sorensen', 'Denmark', 'Accountant', 'Yearly accounts, tax set-aside and sales tax returns'),
        ('CR-10', 'Hassan Ali', 'Egypt', 'Insurance broker', 'Fleet insurance and renewal quotes'),
        ('CR-11', 'Diego Morales', 'Mexico', 'Mechanic', 'Services, repairs and inspections'),
        ('CR-12', 'Olga Petrenko', 'Ukraine', 'Tyre supplier', 'Tyre sets, fitting and season changes'),
        ('CR-13', 'Kwame Asante', 'Ghana', 'Body repair shop', 'Scratch, dent and glass repairs'),
        ('CR-14', 'Bruno Costa', 'Brazil', 'Towing service', 'Breakdown recovery, day and night'),
        ('CR-15', 'Mei Zhao', 'China', 'Car-wash supplier', 'Cleaning products and valet supplies'),
        ('CR-16', 'Anil Desai', 'India', 'Lender', 'Vehicle financing and loan statements')]
contacts = [dict(staff_id=a, name=b, role=ro, team='Outside', pay_type='Invoice', phone=fake_phone(213 + i), email=fake_email(b), hours_week=0, monthly_salary=0.0, hourly_rate=0.0,
                 area=sp, country=c, start=ago(2200 - 230 * i)) for i, (a, b, c, ro, sp) in enumerate(_ctc)]
team = staff + contacts
staff_by_name = {s['name']: s for s in team}
STAFF_NAMES = [s['name'] for s in staff]
VENDOR = {'Mechanic': 'Diego Morales', 'Tyre supplier': 'Olga Petrenko', 'Body repair shop': 'Kwame Asante', 'Towing service': 'Bruno Costa'}

# ------------------------------------------------------------------ reference tables
# class, daily, weekly, monthly, deposit, seats, included miles a day, turnaround buffer minutes, mean miles driven a day
_CL = [('Economy', 41.0, 245.0, 860.0, 200.0, 5, 85), ('Compact', 49.0, 295.0, 1030.0, 250.0, 5, 90), ('Midsize SUV', 78.0, 465.0, 1620.0, 350.0, 7 - 2, 100),
       ('7-seat Van', 99.0, 590.0, 2050.0, 400.0, 7, 120), ('Premium', 136.0, 820.0, 2850.0, 600.0, 5, 95), ('Electric', 90.0, 540.0, 1880.0, 400.0, 5, 80)]
_BUF = {'Economy': 90, 'Compact': 90, 'Midsize SUV': 120, '7-seat Van': 150, 'Premium': 120, 'Electric': 120}
classes = [dict(class_id='VC-%02d' % (i + 1), **{'class': c}, daily_rate=d_, weekly_rate=w, monthly_rate=m, last_year_daily=round(d_ / 1.04), deposit=dep, seats=s,
                included_miles_day=150, buffer_min=_BUF[c]) for i, (c, d_, w, m, dep, s, _mi) in enumerate(_CL)]
CLS = {c['class']: c for c in classes}
_MPD = {c: mi for c, _a, _b, _c, _d, _s, mi in _CL}
seasons = [dict(season_id='SN-01', season='Off-peak', multiplier=0.85, months='January, February, November'),
           dict(season_id='SN-02', season='Shoulder', multiplier=1.0, months='March to May, September, October'),
           dict(season_id='SN-03', season='Peak', multiplier=1.25, months='June to August'),
           dict(season_id='SN-04', season='Holiday', multiplier=1.35, months='Winter holiday period, spring and autumn school breaks')]
SEASON_MULT = {s['season']: s['multiplier'] for s in seasons}
# addon, price a day, days cap (weekly price), cost to us a day, uptake share
_AD = [('Child seat', 8.0, 7, 1.2, .12), ('Extra driver', 6.0, 7, 0.4, .14), ('Navigation unit', 7.0, 7, 0.9, .08), ('Cover option basic', 11.0, 30, 5.5, .35),
       ('Cover option plus', 17.0, 30, 9.5, .15), ('Young-driver fee', 15.0, 30, 0.0, .09), ('Roof box', 9.0, 7, 0.6, .03)]
addons = [dict(addon_id='AD-%02d' % (i + 1), addon=a, price_day=p, cap_days=cp, unit_cost_day=c, uptake=u) for i, (a, p, cp, c, u) in enumerate(_AD)]
ADD = {a['addon']: a for a in addons}
fees = [dict(fee_id='FE-01', fee='Extra mileage', amount=EXTRA_MILE_FEE, basis='per mile over the allowance'),
        dict(fee_id='FE-02', fee='Late return', amount=LATE_FEE_HOUR, basis='per started hour after %d minutes of grace' % LATE_GRACE_MIN),
        dict(fee_id='FE-03', fee='Cleaning', amount=CLEANING_FEE, basis='flat, when the car needs extra cleaning'),
        dict(fee_id='FE-04', fee='Fuel or charge refill', amount=REFILL_STEP_FEE, basis='per 10 points below the agreed level plus %d service charge' % REFILL_SERVICE_FEE),
        dict(fee_id='FE-05', fee='Toll and ticket admin', amount=TOLL_ADMIN_FEE, basis='per toll or ticket passed on'),
        dict(fee_id='FE-06', fee='Key replacement', amount=60.0, basis='flat, a lost key'),
        dict(fee_id='FE-07', fee='Late cancellation', amount=20.0, basis='flat, inside 24 hours of pickup')]
# location, kind, fee per leg, run minutes one way incl. handover, miles one way
_LC = [('Main lot', 'Lot', 0.0, 0, 0), ('Airport delivery', 'Delivery zone', 18.0, 42, 14), ('Hotel district', 'Delivery zone', 12.0, 26, 7),
       ('Hotel strip', 'Delivery zone', 15.0, 30, 9), ('Home delivery', 'Delivery zone', 20.0, 32, 10)]
locations = [dict(location_id='LC-%02d' % (i + 1), location=a, kind=k, fee_leg=f, run_minutes=m, one_way_miles=mi) for i, (a, k, f, m, mi) in enumerate(_LC)]
LOC = {x['location']: x for x in locations}
channels = [dict(channel_id='CH-01', channel='Website', kind='Direct', fee_pct=0.0, payout_days=0), dict(channel_id='CH-02', channel='Phone', kind='Direct', fee_pct=0.0, payout_days=0),
            dict(channel_id='CH-03', channel='Corporate account', kind='Direct', fee_pct=0.0, payout_days=30),
            dict(channel_id='CH-04', channel='Hotel partner', kind='Partner', fee_pct=0.10, payout_days=0),
            dict(channel_id='CH-05', channel='Marketplace A', kind='Marketplace', fee_pct=0.20, payout_days=3), dict(channel_id='CH-06', channel='Marketplace B', kind='Marketplace', fee_pct=0.25, payout_days=7)]
CH = {c['channel']: c for c in channels}
# service type, interval miles, interval months, typical cost, downtime days
_SV = [('Minor service', 7500, 6, 110.0, 1), ('Major service', 22500, 18, 280.0, 2), ('Tyre set', 30000, 36, 420.0, 1), ('Brake service', 24000, 24, 240.0, 1), ('Inspection', 0, 12, 95.0, 1),
       ('Battery check', 12000, 12, 100.0, 1), ('Repair', 0, 0, 240.0, 2), ('Body repair', 0, 0, 480.0, 3), ('Towing', 0, 0, 170.0, 0)]
service_types = [dict(service_id='SV-%02d' % (i + 1), service_type=a, interval_miles=m, interval_months=mo, typical_cost=c, downtime_days=dd) for i, (a, m, mo, c, dd) in enumerate(_SV)]
SVT = {s['service_type']: s for s in service_types}
_CLS_COST = {'Economy': .9, 'Compact': 1.0, 'Midsize SUV': 1.25, '7-seat Van': 1.4, 'Premium': 1.7, 'Electric': 1.15}
_INS_MONTH = {'Economy': 72.0, 'Compact': 84.0, 'Midsize SUV': 118.0, '7-seat Van': 135.0, 'Premium': 190.0, 'Electric': 128.0}
_REG_COST = {'Economy': 150.0, 'Compact': 160.0, 'Midsize SUV': 185.0, '7-seat Van': 195.0, 'Premium': 215.0, 'Electric': 120.0}
_PRICE = {'Economy': 13000, 'Compact': 15500, 'Midsize SUV': 25500, '7-seat Van': 28000, 'Premium': 38000, 'Electric': 31000}
_BASE_U = {'Economy': .78, 'Compact': .80, 'Midsize SUV': .84, '7-seat Van': .76, 'Premium': .66, 'Electric': .74}
_MF = {1: .85, 2: .85, 3: .92, 4: 1.0, 5: 1.0, 6: 1.1, 7: 1.18, 8: 1.18, 9: 1.0, 10: .95, 11: .88, 12: 1.08}

_CACHE = {}
def _raw(key, fn):
    if key not in _CACHE: _CACHE[key] = fn()
    return _CACHE[key]
def _cached(key, fn): return [dict(r) for r in _raw(key, fn)]
def _thin(rows, n):
    if not n or n >= len(rows): return rows
    k = min(max(3, n // 5), n)
    if k >= n: return rows[-n:]
    recent = rows[-k:]; rest = rows[:-k]; m = n - k; step = len(rest) / float(m)
    return [rest[int(i * step)] for i in range(m)] + recent
def _pub(rows): return [{k: v for k, v in x.items() if not k.startswith('_')} for x in rows]
def _wchoice(r, vals, ws):
    x, acc = r.random() * sum(ws), 0
    for v, w in zip(vals, ws):
        acc += w
        if x <= acc: return v
    return vals[-1]
def _wage(rate, d): return R2(rate * (1.03 if to_date(d) >= D(TODAY.year, 1, 1) else 1.0))
def _rate_factor(d): return 1.0 if to_date(d) >= D(TODAY.year, 1, 1) else 1 / 1.04
def _pmt(P, rate, n):
    r = rate / 12.0
    return P * r / (1 - (1 + r) ** -n) if r else P / n

# ------------------------------------------------------------------ calendar: seasons and events
def _season(d):
    d = to_date(d)
    md = (d.month, d.day)
    if md >= (12, 18) or md <= (1, 3): return 'Holiday'
    if (4, 6) <= md <= (4, 14) or (10, 24) <= md <= (11, 1): return 'Holiday'
    if d.month in (6, 7, 8): return 'Peak'
    if d.month in (1, 2, 11, 12): return 'Off-peak'
    return 'Shoulder'


def _events():
    out = []
    for y in range(TODAY.year - 2, TODAY.year + 2):
        out += [('Winter holiday period', 'Holiday period', D(y, 12, 18), D(y + 1, 1, 3), .30), ('Spring school break', 'School break', D(y, 4, 6), D(y, 4, 14), .22),
                ('Autumn school break', 'School break', D(y, 10, 24), D(y, 11, 1), .18), ('Spring long weekend', 'Long weekend', D(y, 5, 22), D(y, 5, 26), .25),
                ('Summer festival weekend', 'Event weekend', D(y, 7, 10), D(y, 7, 12), .35), ('Trade fair week', 'Event weekend', D(y, 9, 16), D(y, 9, 20), .20)]
    out = [x for x in sorted(out, key=lambda t: t[2]) if HISTORY_START - day(30) <= x[2] <= TODAY + day(200)]
    return [dict(event_id='EV-%02d' % (i + 1), event=a, kind=k, start=iso(s), end=iso(e), uplift=u) for i, (a, k, s, e, u) in enumerate(out)]


def event_rows(n=None): return _thin(_cached('events', _events), n)
def _event_days():
    out = {}
    for e in _raw('events', _events):
        d = to_date(e['start'])
        while d <= to_date(e['end']): out[d] = e['uplift']; d += day(1)
    return out
_EVD = _event_days()

# ------------------------------------------------------------------ names
_FIRST = ['Amara', 'Lucas', 'Priya', 'Mateo', 'Yuki', 'Fatima', 'Oliver', 'Chen', 'Ines', 'Kwame', 'Elena', 'Rafael', 'Mei', 'Omar', 'Sofia', 'Jonas', 'Aisha', 'Diego', 'Hannah', 'Ravi',
          'Noor', 'Tomasz', 'Leila', 'Gabriel', 'Ingrid', 'Samuel', 'Zainab', 'Pavel', 'Camila', 'Kenji', 'Anja', 'Idris', 'Maya', 'Stefan', 'Adaeze', 'Hugo', 'Sakura', 'Ahmed', 'Clara', 'Tariq',
          'Bianca', 'Nikolai', 'Esther', 'Mohamed', 'Greta', 'Joao', 'Fiona', 'Arjun', 'Lena', 'Emeka', 'Mina', 'Callum', 'Dalia', 'Marco', 'Yara', 'Felix', 'Thandi', 'Andre', 'Sunita', 'Liam',
          'Rosa', 'Hamza', 'Elif', 'Sven', 'Chiamaka', 'Pedro', 'Aiko', 'Daniel', 'Salma', 'Ivan', 'Nia', 'Rohan', 'Petra', 'Kofi', 'Lucia', 'Jin', 'Marta', 'Dev', 'Alina', 'Tunde']
_INIT = 'ABCDEFGHIJKLMNOPRSTVWYZ'
_COLOURS = ['White', 'Silver', 'Black', 'Grey', 'Blue', 'Red', 'Green', 'Orange']

# ------------------------------------------------------------------ fleet
_PRE = [(2000, 'Economy', None), (1950, 'Compact', None), (1880, 'Economy', 410), (1800, 'Midsize SUV', None), (1700, 'Compact', None), (1640, '7-seat Van', 560), (1580, 'Economy', None),
        (1500, 'Premium', 75), (1440, 'Midsize SUV', None), (1380, 'Compact', None), (1300, 'Economy', 120), (1240, '7-seat Van', None), (1150, 'Economy', None), (1080, 'Compact', 230),
        (1000, 'Midsize SUV', None), (940, 'Premium', None), (880, 'Economy', None), (840, 'Compact', None), (800, '7-seat Van', None), (770, 'Premium', None)]
_WITHIN = [(700, 'Economy'), (640, 'Compact'), (590, 'Midsize SUV'), (520, '7-seat Van'), (470, 'Electric'), (400, 'Premium'), (340, 'Compact'), (290, 'Electric'), (230, 'Midsize SUV'),
           (170, 'Economy'), (120, '7-seat Van'), (70, 'Electric'), (28, 'Electric')]
_KEY_LOW, _KEY_SVC, _KEY_REN, _KEY_DBL = (400, 'Premium'), (1000, 'Midsize SUV'), (1380, 'Compact'), (880, 'Economy')
_KEY_WS1, _KEY_WS2 = (1700, 'Compact'), (1580, 'Economy')
_IV_MILES = {'Economy': 7500, 'Compact': 7500, 'Midsize SUV': 9000, '7-seat Van': 7500, 'Premium': 9000, 'Electric': 12000}


def _vehicles():
    rows = [(a, b, c) for a, b, c in _PRE] + [(a, b, None) for a, b in _WITHIN]
    rows.sort(key=lambda x: -x[0])
    cnt, out = {}, []
    for i, (dago, cls, sold) in enumerate(rows):
        vid = 'VH-%03d' % (i + 1); rv = rng('veh' + vid)
        cnt[cls] = cnt.get(cls, 0) + 1
        colour = _COLOURS[(i * 3 + cnt[cls]) % len(_COLOURS)]
        fuel = {'Electric': 'Electric', 'Economy': rv.choice(['Petrol', 'Petrol', 'Hybrid']), 'Compact': rv.choice(['Petrol', 'Hybrid', 'Petrol']),
                'Midsize SUV': rv.choice(['Diesel', 'Petrol', 'Hybrid']), '7-seat Van': 'Diesel', 'Premium': rv.choice(['Petrol', 'Hybrid', 'Diesel'])}[cls]
        used = rv.random() < .35
        price = _PRICE[cls] * (0.88 + 0.04 * (2000 - dago) / 365.0) * rv.uniform(.97, 1.03) * (0.78 if used else 1.0)
        price = float(round(price / 50.0) * 50)
        buy = TODAY - day(dago)
        fin = rv.random() < (0.5 if sold else 0.55 if dago > 730 else 0.8) or (dago, cls) == _KEY_LOW
        share = 0.8 if dago < 900 else 0.75
        loan = float(round(price * share / 10.0) * 10) if fin else 0.0
        rate = round(rv.uniform(.062, .094), 4) if fin else 0.0
        months = 60 if fin else 0
        out.append(dict(vehicle_id=vid, vehicle='%s %02d %s' % (cls, cnt[cls], colour), plate='BW %04d %s' % (1000 + (i * 719) % 8900, 'KLMNPRSTVXZ'[(i * 5) % 11]), **{'class': cls}, fuel=fuel,
                        seats=CLS[cls]['seats'], year=buy.year - (1 if used else 0), colour=colour, purchase_date=iso(buy), purchase_price=price, financed=fin, loan_amount=loan,
                        loan_rate=rate, loan_months=months, monthly_payment=R2(_pmt(loan, rate, months)) if fin else 0.0,
                        odometer_at_purchase=rv.randint(9000, 38000) if used else rv.randint(5, 900), status='Sold' if sold else 'Active',
                        sold_date=ago(sold) if sold else '', sold_price=0.0, interval_miles=_IV_MILES[cls], interval_months=12 if cls == 'Electric' else 6,
                        insurance_year=float(round(_INS_MONTH[cls] * 12 * rv.uniform(.92, 1.08))), _buy=buy, _sold=(TODAY - day(sold)) if sold else None, _dago=dago, _key=(dago, cls)))
    return out


def _renewal_plan(veh):
    """per vehicle: registration, insurance and inspection due dates (past ones done, the next one upcoming, none within 45 days except the story vehicle)"""
    out = []
    for v in veh:
        rv = rng('ren' + v['vehicle_id'])
        end = v['_sold'] or (TODAY + day(400))
        for kind in RENEWAL_KINDS:
            nxt = TODAY + day(rv.randint(48, 355))
            if v['_key'] == _KEY_REN and kind == 'Registration renewal': nxt = TODAY + day(10)
            cost = {'Registration renewal': _REG_COST[v['class']], 'Insurance renewal': v['insurance_year'], 'Inspection due': 95.0}[kind]
            k = 0
            while True:
                due = nxt - day(365 * k)
                if due < max(HISTORY_START - day(20), v['_buy'] + day(20)): break
                if v['_sold'] and due > v['_sold']: k += 1; continue
                done = due <= TODAY
                out.append(dict(vehicle=v, kind=kind, due=due, renewed=(due - day(rv.randint(1, 10))) if done else None, cost=R2(cost * (1.04 ** -k)), status='Done' if done else 'Upcoming'))
                k += 1
                if k > 4: break
    return out


def _sim():
    veh = _vehicles(); ren = _renewal_plan(veh)
    by_key = {v['_key']: v for v in veh}
    bookings, maint, claims_in, extra = [], [], [], []
    for v in veh:
        rv = rng('sim' + v['vehicle_id']); cls = v['class']; low = v['_key'] == _KEY_LOW
        start = max(v['_buy'], HISTORY_START); end = (v['_sold'] - day(1)) if v['_sold'] else TODAY + day(HORIZON_DAYS + 10)
        odo = v['odometer_at_purchase'] + (int((HISTORY_START - v['_buy']).days * 36) if v['_buy'] < HISTORY_START else 0)
        v['_odo_start'] = odo
        ivm = v['interval_miles']
        last_sv_d = start - day(rv.randint(20, 150)); last_sv_o = odo - rv.randint(400, ivm - 900)
        next_tyre = odo + rv.randint(2000, 28000); next_brake = odo + rv.randint(3000, 22000); nsv = rv.randint(0, 2)
        forced_sv, forced_bk, occ = {}, {}, set()

        for r_ in ren:
            if r_['vehicle'] is v and r_['kind'] == 'Inspection due' and r_['renewed'] and start <= r_['renewed'] <= TODAY and r_['renewed'] not in occ:
                forced_sv[r_['renewed']] = ('Inspection', 1); occ.add(r_['renewed'])
        stop_svc = None
        if v['_key'] == _KEY_SVC:
            d0 = TODAY - day(150); forced_sv[d0] = ('Minor service', 1); occ.add(d0); stop_svc = d0
            forced_bk[TODAY + day(1)] = (4, 'Website'); [occ.add(TODAY + day(1 + k)) for k in range(4)]
        if v['_key'] == _KEY_DBL:
            forced_bk[TODAY + day(4)] = (5, 'Phone'); [occ.add(TODAY + day(4 + k)) for k in range(5)]
        if v['_key'] == _KEY_WS1:
            forced_sv[TODAY - day(1)] = ('Brake service', 3); [occ.add(TODAY - day(1) + day(k)) for k in range(3)]
        if v['_key'] == _KEY_WS2:
            forced_sv[TODAY] = ('Minor service', 1); occ.add(TODAY)
        forced_starts = sorted(set(forced_sv) | set(forced_bk))
        d = start; prev = None; sv_after = None

        def add_maint(dd, kind, cost, days_, odo_, note=''):
            maint.append(dict(vehicle=v, date=dd, kind=kind, odometer=odo_, cost=R2(cost), days_off=days_, vendor_role='Tyre supplier' if kind == 'Tyre set' else 'Body repair shop' if kind == 'Body repair'
                              else 'Towing service' if kind == 'Towing' else 'Mechanic', note=note))

        def svc(dd, kind):
            nonlocal last_sv_d, last_sv_o, next_tyre, next_brake, nsv
            c = _CLS_COST[cls]
            if kind in ('Minor service', 'Major service', 'Battery check'):
                add_maint(dd, kind, SVT[kind]['typical_cost'] * c * rv.uniform(.9, 1.15), SVT[kind]['downtime_days'], odo)
                last_sv_d, last_sv_o = dd, odo; nsv += 1
            elif kind == 'Inspection':
                add_maint(dd, 'Inspection', 95.0 * rv.uniform(.95, 1.1), 1, odo)
            elif kind == 'Brake service':
                add_maint(dd, kind, SVT[kind]['typical_cost'] * c * rv.uniform(.9, 1.15), 1, odo); next_brake = odo + 24000 + rv.randint(-2000, 2000)
            return SVT[kind]['downtime_days']

        while d <= end:
            if d in forced_sv:
                kind, nd = forced_sv[d]
                if kind in ('Minor service', 'Brake service', 'Inspection'):
                    svc(d, kind); maint[-1]['days_off'] = max(1, nd)
                d += day(max(1, nd)); continue
            if d in forced_bk:
                L, ch = forced_bk[d]
                b = _make_booking(v, rv, d, L, ch, odo, prev, forced=True)
                bookings.append(b); prev = b
                odo = b['_odo_after']
                d += day(L); continue
            # service due
            if d <= TODAY + day(3) and not (stop_svc and d > stop_svc):
                kind = 'Battery check' if cls == 'Electric' else ('Major service' if nsv % 3 == 2 else 'Minor service')
                due = odo - last_sv_o >= ivm or (d - last_sv_d).days >= 30.4 * v['interval_months']
                if due:
                    nd = SVT[kind]['downtime_days']
                    if not any((d + day(k)) in occ for k in range(max(1, nd))):
                        svc(d, kind)
                        if odo >= next_tyre:
                            add_maint(d, 'Tyre set', SVT['Tyre set']['typical_cost'] * _CLS_COST[cls] * rv.uniform(.9, 1.2), 1, odo); next_tyre = odo + 30000 + rv.randint(-3000, 3000)
                        if odo >= next_brake and kind != 'Brake service':
                            add_maint(d, 'Brake service', SVT['Brake service']['typical_cost'] * _CLS_COST[cls] * rv.uniform(.9, 1.15), 1, odo); next_brake = odo + 24000 + rv.randint(-2000, 2000)
                        for k in range(max(1, nd)): occ.add(d + day(k))
                        d += day(max(1, nd)); continue
            # random repair or towing in a gap
            if d <= TODAY - day(1) and d not in occ:
                x = rv.random()
                if x < .016:
                    add_maint(d, 'Repair', SVT['Repair']['typical_cost'] * _CLS_COST[cls] * rv.uniform(.3, 2.2), rv.randint(1, 3), odo); nd = maint[-1]['days_off']
                    if not any((d + day(k)) in occ for k in range(nd)): d += day(nd); continue
                elif x < .021:
                    add_maint(d, 'Towing', 170.0 * rv.uniform(.7, 1.6), 0, odo)
            # next booking
            u = _BASE_U[cls] * _MF[d.month] * (1 + _EVD.get(d, 0) * .25) * (1 + (int(v['vehicle_id'][3:]) * 7 % 13 - 6) / 100.0)
            if low: u = 0.24 * _MF[d.month]
            age = (d - v['_buy']).days
            if age < 40: u *= 0.5 + 0.5 * age / 40.0
            if d > TODAY: u *= max(0.04, 1 - ((d - TODAY).days / float(HORIZON_DAYS)) ** 1.2)
            u = max(0.06, min(0.93, u))
            gap = int(rv.expovariate(1.0 / max(0.25, (2.8 if low else 5.6) * (1 - u) / u)) + 0.5)
            s = d + day(gap)
            nxt = [k for k in forced_starts if d < k <= s]
            if nxt: d = nxt[0]; continue
            while s in occ: s += day(1)
            if s > end or s > TODAY + day(HORIZON_DAYS): break
            L = _length(rv, cls)
            if low: L = min(L, 4)
            while L > 1 and any((s + day(k)) in occ for k in range(L)): L -= 1
            if s + day(L - 1) > end: L = (end - s).days + 1
            if L < 1: break
            L = _fit_forced(s, L, forced_starts)
            b = _make_booking(v, rv, s, L, None, odo, prev)
            bookings.append(b); prev = b
            odo = b['_odo_after']
            e_ = s + day(L)
            # damage repair downtime right after the return
            if b.get('_claim') and b['_claim']['repair'] >= 300 and e_ <= TODAY and e_ not in occ and e_ not in forced_sv and e_ not in forced_bk:
                nd = 2 if b['_claim']['repair'] < 700 else 3
                add_maint(e_, 'Body repair' if b['_claim']['kind'] != 'Tyre damage' else 'Repair', b['_claim']['repair'], nd, odo, 'damage claim')
                maint[-1]['_booking'] = b; e_ += day(nd)
            d = e_
        v['_odo_now'] = odo
        v['_last_sv_d'], v['_last_sv_o'] = last_sv_d, last_sv_o
    return dict(veh=veh, ren=ren, bookings=bookings, maint=maint, by_key=by_key)


def _fit_forced(s, L, forced_starts):
    for k in forced_starts:
        if s < k < s + day(L): return (k - s).days
    return L


def _length(rv, cls):
    pm = {'Economy': .05, 'Compact': .05, 'Midsize SUV': .04, '7-seat Van': .03, 'Premium': .012, 'Electric': .02}[cls]
    x = rv.random()
    if x < pm: return rv.randint(28, 60)
    if x < pm + .14: return rv.choice([7, 7, 8, 9, 10, 14, 14, 21])
    return _wchoice(rv, [1, 2, 3, 4, 5, 6], [.14, .2, .22, .12, .1, .04])


_CHW = {'Daily': [.30, .18, .10, .14, .18, .10], 'Weekly': [.30, .20, .20, .0, .20, .10], 'Monthly': [.20, .25, .45, .0, .05, .05]}
_LOCW = {'Website': [.55, .2, .1, .0, .15], 'Phone': [.5, .15, .1, .05, .2], 'Corporate account': [.6, .15, .0, .0, .25], 'Hotel partner': [.0, .1, .5, .4, .0],
         'Marketplace A': [.3, .2, .0, .0, .5], 'Marketplace B': [.35, .15, .0, .0, .5]}


def _make_booking(v, rv, s, L, ch, odo, prev, forced=False):
    cls = v['class']; e = s + day(L - 1); c = CLS[cls]
    plan = 'Monthly' if L >= 28 else 'Weekly' if L >= 7 else 'Daily'
    if ch is None: ch = _wchoice(rv, CHANNELS, _CHW[plan])
    loc = _wchoice(rv, LOCATIONS, _LOCW[ch])
    x = rv.random()
    if forced: status = 'Active' if s <= TODAY else 'Booked'
    elif e < TODAY: status = 'Cancelled' if x < .05 else 'No-show' if x < .062 else 'Completed'
    elif s <= TODAY: status = 'Active'
    else: status = 'Cancelled' if x < .03 else 'Booked'
    pm = _r15(_wchoice(rv, [480, 540, 600, 660, 780, 900, 1020], [.16, .22, .2, .12, .1, .12, .08]) + rv.randint(-45, 45))
    if prev and prev['_e'] == s and prev['status'] in ('Completed', 'Active'):
        pm = min(1200, max(pm, _r15(prev['_agreed'] + c['buffer_min'] + rv.randint(-40, 75))))
    sm = SEASON_MULT[_season(s)]
    if plan == 'Daily': dr = c['daily_rate'] * sm * ((1 + WEEKEND_UPLIFT) if (s.weekday() == 4 and L <= 3) else 1.0)
    elif plan == 'Weekly': dr = c['weekly_rate'] / 7.0 * (1 + (sm - 1) * .5)
    else: dr = c['monthly_rate'] / 30.0 * (1 + (sm - 1) * .3)
    dr *= _rate_factor(s)
    if ch == 'Corporate account': dr *= .92
    dr = round(dr * 2) / 2.0
    rental = R2(dr * L)
    adds = []; young = False
    for a in addons:
        p = a['uptake'] * (0.3 if ch.startswith('Marketplace') else 1.0) * (0.5 if plan == 'Monthly' else 1.0)
        if a['addon'] == 'Young-driver fee': p = 0.09 if ch in ('Website', 'Phone', 'Hotel partner') else 0.0
        if rv.random() < p:
            q = min(L, a['cap_days']); adds.append((a['addon'], q, R2(a['price_day'] * q), R2(a['unit_cost_day'] * L)))
            if a['addon'] == 'Young-driver fee': young = True
    addon_amt = R2(sum(x_[2] for x_ in adds))
    dfee = R2(LOC[loc]['fee_leg'] * 2)
    total = R2(rental + addon_amt + dfee)
    fee_pct = CH[ch]['fee_pct']
    lead = {'Website': rv.randint(1, 30), 'Phone': rv.randint(0, 10), 'Corporate account': rv.randint(3, 35), 'Hotel partner': rv.randint(0, 5), 'Marketplace A': int(rv.expovariate(1 / 4.0)),
            'Marketplace B': int(rv.expovariate(1 / 6.0))}[ch]
    created = s - day(lead)
    if created > TODAY: created = TODAY - day(rv.randint(0, 6))
    if created > s: created = s
    inc = 150 * L if plan == 'Daily' else int(round(1000 * L / 7.0)) if plan == 'Weekly' else int(round(3000 * L / 30.0))
    b = dict(created_on=iso(created), start_date=iso(s), end_date=iso(e), days=L, pickup_time=_hm(pm), return_time=_hm(pm), vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], **{'class': cls},
             channel=ch, plan=plan, season=_season(s), day_rate=dr, rental_amount=rental, addon_amount=addon_amt, delivery_fee=dfee, total=total, fee_pct=fee_pct,
             channel_fee=R2(total * fee_pct), net_amount=R2(total * (1 - fee_pct)), pickup_location=loc, deposit=c['deposit'] if ch in ('Website', 'Phone', 'Hotel partner') else 0.0,
             miles_included=inc, young_driver=young, extended=rv.random() < .05, status=status, _s=s, _e=e, _agreed=pm, _adds=adds, _v=v, _fees=[], _claim=None, _odo_after=odo,
             out_odometer='', in_odometer='')
    if status in ('Completed', 'Active'):
        mpd = _MPD[cls] * (0.7 if plan != 'Daily' else 1.0) * rv.lognormvariate(0, .33)
        driven = max(8, int(mpd * L))
        late = 0
        if rv.random() < .20: late = int(rv.expovariate(1 / 70.0)) + 1
        elif rv.random() < .15: late = -rv.randint(5, 90)
        ret_min = max(0, min(1425, pm + late))
        out_lvl = rv.choice([90, 95, 100]) if cls == 'Electric' else 100
        sh = rv.randint(0, 9) if rv.random() < .80 else rv.randint(10, 60)
        dirty = rv.random() < .035
        dmg_p = .05 * (2.2 if young else 1.0) * (1.5 if ch == 'Marketplace B' else 1.0) * {'7-seat Van': 1.2, 'Premium': .8}.get(cls, 1.0) * (.5 if plan == 'Monthly' else 1.0)
        dmg = rv.random() < dmg_p and v['_key'] != _KEY_LOW
        b.update(out_odometer=odo, out_time=_hm(pm), out_level=out_lvl, photos_out=rv.random() < .96, keys=2 if rv.random() < .96 else 1, deposit_taken=b['deposit'] > 0,
                 handled_by=_wchoice(rv, ['Tomas Kowalski', 'Sana Malik', 'Jun Park', 'Nadia Haddad'], [.4, .2, .3, .1]), _driven=driven)
        if status == 'Completed':
            ex = max(0, driven - inc)
            b.update(in_odometer=odo + driven, in_time=_hm(ret_min), in_level=max(8, out_lvl - sh), photos_in=rv.random() < .9, damage_seen=dmg, miles_driven=driven, extra_miles=ex,
                     late_minutes=max(0, late), fuel_shortfall=sh if sh >= 10 else 0, dirty=dirty, _odo_after=odo + driven, _ret_min=ret_min)
            if ex > 0: b['_fees'].append(dict(kind='Extra mileage', due=R2(ex * EXTRA_MILE_FEE), cost=0.0))
            if late > LATE_GRACE_MIN: b['_fees'].append(dict(kind='Late return', due=R2(math.ceil((late - LATE_GRACE_MIN) / 60.0) * LATE_FEE_HOUR), cost=0.0))
            if dirty: b['_fees'].append(dict(kind='Cleaning', due=CLEANING_FEE, cost=0.0))
            if sh >= 10:
                steps = math.ceil(sh / 10.0)
                b['_fees'].append(dict(kind='Fuel or charge refill', due=R2(REFILL_SERVICE_FEE + REFILL_STEP_FEE * steps), cost=R2(steps * (2.0 if cls == 'Electric' else 3.2))))
            if dmg:
                kind = _wchoice(rv, CLAIM_KINDS, [.34, .22, .12, .14, .08, .10])
                lo, hi = {'Scratch': (120, 450), 'Dent': (250, 900), 'Windscreen chip': (90, 260), 'Interior damage': (100, 500), 'Tyre damage': (120, 400), 'Other': (80, 700)}[kind]
                rep = R2(rv.uniform(lo, hi) * (1.25 if cls == 'Premium' else 1.0))
                b['_claim'] = dict(kind=kind, repair=rep, estimate=R2(rep * rv.uniform(.9, 1.1)))
        else:
            b['_odo_after'] = odo + int(driven * ((TODAY - s).days + 1) / float(L))
    return b


# ------------------------------------------------------------------ world: everything derived from the simulation
def _world():
    w = _sim(); veh, bookings, maint = w['veh'], w['bookings'], w['maint']
    VBY = {v['vehicle_id']: v for v in veh}
    # the double booking story: a second booking on the same vehicle next week (created later, from a marketplace)
    dv = w['by_key'][_KEY_DBL]; ra = rng('dbl')
    for b in bookings:
        if b['vehicle_id'] == dv['vehicle_id'] and b['_s'] == TODAY + day(4): b['created_on'] = ago(12); story_a = b
    story_b = _make_booking(dv, ra, TODAY + day(6), 3, 'Marketplace B', dv['_odo_now'], None, forced=True)
    story_b['created_on'] = ago(2); story_b['status'] = 'Booked'; bookings.append(story_b)
    bookings.sort(key=lambda b: (b['created_on'], b['start_date'], b['vehicle_id']))
    for i, b in enumerate(bookings): b['booking_id'] = 'BK-%05d' % (i + 1)
    BK = {b['booking_id']: b for b in bookings}
    # ---- renters
    r = rng('renters'); renters, pool, corp, used = [], [], [], set()
    def new_renter(b, account='', under25=False):
        k = len(renters)
        while True:
            nm = '%s %s.' % (_FIRST[(k * 7 + len(used)) % len(_FIRST)], _INIT[((k * 7 + len(used)) // len(_FIRST) + k) % len(_INIT)])
            if nm not in used: break
            k += 1
        used.add(nm)
        x = dict(renter_id='RN-%04d' % (len(renters) + 1), renter=nm, age_band='Under 25' if under25 else '25 and over', status='Verified', documents_checked=True, account=account,
                 source=b['channel'], first_rental=b['start_date'], last_rental=b['start_date'], rentals=0, _n=0)
        renters.append(x); return x
    for b in bookings:
        if b['channel'] == 'Corporate account':
            if len(corp) < 14 or r.random() < .05:
                x = new_renter(b, 'Corporate account %d' % (len(corp) % 6 + 1)); corp.append(x)
            else: x = r.choice(corp)
        elif b['young_driver']: x = new_renter(b, under25=True)
        elif pool and r.random() < (.30 if b['channel'] in ('Website', 'Phone', 'Hotel partner') else .12):
            x = r.choice(pool[-250:])
        else:
            x = new_renter(b); pool.append(x)
        b['renter_id'] = x['renter_id']; b['renter'] = x['renter']
        if b['status'] not in ('Cancelled',): x['_n'] += 1; x['last_rental'] = max(x['last_rental'], b['start_date'])
    upcoming = [x for x in renters if any(b['renter_id'] == x['renter_id'] and b['status'] == 'Booked' for b in bookings)]
    for x in upcoming[:5]: x['status'] = 'Documents due'; x['documents_checked'] = False
    for x in [x for x in renters if to_date(x['last_rental']) < TODAY - day(120) and x['account'] == ''][3::40][:6]: x['status'] = 'Restricted'
    for x in renters: x['rentals'] = x['_n']
    # ---- fees
    r = rng('fees'); fees_rows = []
    for b in bookings:
        for f in b['_fees']:
            age = (TODAY - b['_e']).days
            billed = r.random() < {'Extra mileage': .85, 'Late return': .8, 'Cleaning': .9, 'Fuel or charge refill': .92}[f['kind']]
            if not billed: st, col = 'Not billed', 0.0
            elif age <= FEE_COLLECT_DAYS: st, col = ('Billed', 0.0) if r.random() < .5 else ('Collected', f['due'])
            else:
                y = r.random(); st, col = ('Collected', f['due']) if y < .9 else ('Billed', 0.0) if y < .95 else ('Written off', 0.0)
            fees_rows.append(dict(booking=b, kind=f['kind'], due=f['due'], billed=billed, collected=R2(col), status=st, cost=f['cost'], date=b['end_date']))
    fees_rows.sort(key=lambda x: (x['date'], x['booking']['booking_id']))
    for i, x in enumerate(fees_rows): x['fee_id'] = 'FD-%05d' % (i + 1); x['booking']['_fcol'] = R2(x['booking'].get('_fcol', 0) + x['collected'])
    # ---- claims
    r = rng('claims'); claims = []
    if not any(b['_claim'] and b['deposit'] > 0 and 48 <= (TODAY - b['_e']).days <= 58 for b in bookings):
        cb = [b for b in bookings if b['status'] == 'Completed' and b['deposit'] > 0 and 50 <= (TODAY - b['_e']).days <= 54 and not b['_claim']][0]
        cb['_claim'] = dict(kind='Dent', repair=1140.0, estimate=1180.0)
    for b in bookings:
        if b['_claim']:
            c = b['_claim']; age = (TODAY - b['_e']).days
            claims.append(dict(booking=b, kind=c['kind'], repair=c['repair'], estimate=c['estimate'], age=age, reported_on=b['end_date']))
    claims.sort(key=lambda x: (x['reported_on'], x['booking']['booking_id']))
    keyv = set(w['by_key'][k]['vehicle_id'] for k in (_KEY_LOW, _KEY_SVC, _KEY_REN, _KEY_DBL, _KEY_WS1, _KEY_WS2))
    cand = [c for c in claims if 48 <= c['age'] <= 58 and c['booking']['deposit'] > 0 and c['booking']['vehicle_id'] not in keyv]
    story_claim = (cand or [c for c in claims if 40 <= c['age'] <= 60])[0]
    for i, c in enumerate(claims):
        c['claim_id'] = 'DC-%04d' % (i + 1); b = c['booking']; age = c['age']
        pc = 0.0 if age < 8 else min(.97, (age - 8) / 45.0)
        is_open = (r.random() >= pc) and age < 45
        if c is story_claim: is_open = True
        if c is story_claim: c['estimate'] = R2(max(c['estimate'], 760.0))
        if is_open:
            c.update(status='Reported' if age < 4 else 'Estimate' if age < 15 or c is story_claim else 'In repair', repair_cost=0.0, deposit_used=0.0, claim_paid=0.0, written_off=0.0, closed_on='',
                     days_open=age)
        else:
            rep = c['repair']; dep = R2(min(b['deposit'], rep)); rest = R2(rep - dep)
            if rest > 0 and r.random() < .12: paid, wo = 0.0, rest
            elif rest > 0: paid = R2(rest * r.uniform(.7, 1.0)); wo = R2(rest - paid)
            else: paid, wo = 0.0, 0.0
            if b['deposit'] == 0: dep, paid = 0.0, R2(rep * r.uniform(.8, .95)); wo = R2(rep - paid)
            st = 'Deposit used' if (rest <= .05 * rep and dep > 0) else ('Claim paid' if paid > 0 else 'Written off')
            closed = min(b['_e'] + day(r.randint(12, 42)), TODAY - day(r.randint(0, 3)))
            if closed <= b['_e']: closed = b['_e'] + day(1)
            c.update(status=st, repair_cost=rep, deposit_used=dep, claim_paid=paid, written_off=wo, closed_on=iso(closed), days_open=(closed - b['_e']).days)
        b['_claim_row'] = c
    opn = sorted([c for c in claims if c['status'] in OPEN_CLAIM and c is not story_claim], key=lambda c: c['age'])
    if opn and not any(c['status'] == 'Reported' for c in claims): opn[0]['status'] = 'Reported'
    # maintenance rows from damage: replace the simulation ones by one row per repaired claim
    maint[:] = [m for m in maint if m.get('note') != 'damage claim']
    for c in claims:
        b = c['booking']
        if c['status'] in ('Reported', 'Estimate'): continue
        dt_ = b['_e'] + day(1)
        if dt_ > TODAY: continue
        nd = 0 if c['repair'] < 300 else (2 if c['repair'] < 700 else 3)
        maint.append(dict(vehicle=VBY[b['vehicle_id']], date=dt_, kind='Body repair' if c['kind'] != 'Tyre damage' else 'Repair', odometer=b['in_odometer'], cost=R2(c['repair']), days_off=nd,
                          vendor_role='Body repair shop', note='damage claim', _claim=c))
    maint.sort(key=lambda m: (m['date'], m['vehicle']['vehicle_id']))
    for i, m in enumerate(maint): m['maint_id'] = 'MT-%04d' % (i + 1)
    for v in veh:
        for m in maint:
            if m['vehicle'] is v and m['days_off'] >= 1 and m['date'] <= TODAY < m['date'] + day(m['days_off']) and v['status'] == 'Active': v['status'] = 'In workshop'
        sv = [m for m in maint if m['vehicle'] is v and m['kind'] in ('Minor service', 'Major service', 'Battery check')]
        v['last_service_date'] = iso(sv[-1]['date']) if sv else ''
        v['last_service_odometer'] = sv[-1]['odometer'] if sv else v['_odo_start']
    # ---- deposits
    r = rng('deposits'); deps = []
    held_late = [b for b in bookings if b['status'] == 'Completed' and b['deposit'] > 0 and not b['_claim'] and 8 <= (TODAY - b['_e']).days <= 22 and not b['_fees']]
    held_late = set(id(b) for b in held_late[1::len(held_late) // 4 or 1][:4])
    for b in bookings:
        if b['deposit'] <= 0 or b['status'] not in ('Completed', 'Active'): continue
        due = b['_e'] + day(DEPOSIT_RELEASE_DAYS); st, rel, kept, why = 'Held', '', 0.0, ''
        cr = b.get('_claim_row')
        if b['status'] == 'Completed':
            if cr is not None:
                if cr['closed_on'] == '': st = 'Held'
                else:
                    kept = cr['deposit_used']; why = 'Damage claim'
                    st = 'Kept' if kept >= b['deposit'] else 'Part kept' if kept > 0 else 'Released'
                    rel = iso(min(TODAY, to_date(cr['closed_on']) + day(r.randint(1, 3))))
            elif id(b) in held_late: st = 'Held'
            else:
                delay = r.randint(1, 5) if r.random() > .07 else r.randint(7, 14)
                relx = b['_e'] + day(delay)
                if relx <= TODAY:
                    kept = R2(min(b['deposit'], b.get('_fcol', 0.0))) if (b.get('_fcol', 0) > 0 and r.random() < .6) else 0.0
                    st = 'Part kept' if kept > 0 else 'Released'; why = 'Fees' if kept > 0 else ''; rel = iso(relx)
        deps.append(dict(booking=b, amount=b['deposit'], held_on=b['start_date'], release_due=iso(due), released_on=rel, status=st, kept_amount=kept, refunded_amount=R2(b['deposit'] - kept) if rel else 0.0,
                         reason=why))
    deps.sort(key=lambda x: (x['held_on'], x['booking']['booking_id']))
    for i, x in enumerate(deps): x['deposit_id'] = 'DP-%05d' % (i + 1)
    # ---- payments, invoices and payouts
    r = rng('pay'); pays, invoices, payouts = [], [], []
    for b in bookings:
        if b['status'] not in ('Completed', 'Active', 'Booked'): continue
        ch = b['channel']
        if ch in ('Website', 'Phone', 'Hotel partner'):
            lead = (b['_s'] - to_date(b['created_on'])).days; pre = R2(round(b['total'] * .3)) if lead >= 4 else 0.0
            meth = lambda: _wchoice(r, ['Card', 'Bank transfer', 'Cash'], [.78, .08, .14] if ch == 'Phone' else [.9, .1, 0.0])
            if pre > 0 and to_date(b['created_on']) <= TODAY: pays.append(dict(date=b['created_on'], booking=b, kind='Rental payment', method=meth(), amount=pre, payout_id=''))
            if b['_s'] <= TODAY: pays.append(dict(date=b['start_date'], booking=b, kind='Rental payment', method=meth(), amount=R2(b['total'] - pre), payout_id=''))
            if b['status'] == 'Completed' and b.get('_fcol', 0) > 0: pays.append(dict(date=b['end_date'], booking=b, kind='Balance and fees', method=meth(), amount=b['_fcol'], payout_id=''))
        elif ch == 'Corporate account' and b['status'] == 'Completed':
            amt = R2(b['total'] + b.get('_fcol', 0.0)); iss = b['_e']; due = iss + day(30)
            y = r.random(); delay = r.randint(22, 30) if y < .7 else r.randint(31, 55) if y < .92 else r.randint(56, 95)
            pd_ = iss + day(delay); paid, st, pon = 0.0, 'Unpaid', ''
            if pd_ <= TODAY:
                paid, st, pon = amt, 'Paid', iso(pd_)
                if r.random() < .03 and (TODAY - iss).days > 120: paid, st, pon = 0.0, 'Written off', ''
            elif r.random() < .25 and (TODAY - iss).days > 20: paid, st = R2(amt * .6), 'Part paid'
            invoices.append(dict(booking=b, issued_on=iso(iss), due_date=iso(due), amount=amt, paid_amount=paid, paid_on=pon, status=st))
            if paid > 0 and pon: pays.append(dict(date=pon, booking=b, kind='Invoice payment', method='Bank transfer', amount=paid, payout_id=''))
    invoices.sort(key=lambda x: (x['issued_on'], x['booking']['booking_id']))
    for i, x in enumerate(invoices): x['invoice_id'] = 'IV-%04d' % (i + 1)
    mk = [b for b in bookings if b['channel'].startswith('Marketplace') and b['status'] in ('Completed', 'Active', 'Booked')]
    for b in mk:
        pdte = b['_e'] + day(CH[b['channel']]['payout_days'] + (1 if b['_e'].weekday() >= 5 else 0))
        st = 'Paid' if pdte <= TODAY else 'Expected'
        payouts.append(dict(booking=b, channel=b['channel'], booking_value=b['total'], fee=b['channel_fee'], expected_payout=b['net_amount'], expected_on=iso(pdte), received=b['net_amount'] if st == 'Paid' else 0.0,
                            paid_on=iso(pdte) if st == 'Paid' else '', status=st))
    payouts.sort(key=lambda x: (x['expected_on'], x['booking']['booking_id']))
    pa = [p for p in payouts if p['channel'] == 'Marketplace A' and p['status'] == 'Paid' and 15 <= (TODAY - to_date(p['expected_on'])).days <= 24 and p['expected_payout'] >= 250]
    story_short = pa[len(pa) // 2]; story_short['received'] = R2(story_short['expected_payout'] - 78.5); story_short['status'] = 'Short-paid'
    pb = [p for p in payouts if p['channel'] == 'Marketplace B' and p['status'] == 'Paid' and 5 <= (TODAY - to_date(p['expected_on'])).days <= 12]
    story_late = pb[0]; story_late['received'] = 0.0; story_late['paid_on'] = ''; story_late['status'] = 'Late'
    for i, x in enumerate(payouts): x['payout_id'] = 'PO-%05d' % (i + 1)
    for p in payouts:
        if p['received'] > 0: pays.append(dict(date=p['paid_on'], booking=p['booking'], kind='Payout', method='Marketplace payout', amount=p['received'], payout_id=p['payout_id']))
    pays.sort(key=lambda x: (x['date'], x['booking']['booking_id'], x['kind']))
    for i, x in enumerate(pays): x['payment_id'] = 'PY-%05d' % (i + 1)
    # ---- tolls and tickets
    r = rng('tolls'); tolls = []
    by_v = {}
    for b in bookings:
        if b['status'] in ('Completed', 'Active'): by_v.setdefault(b['vehicle_id'], []).append(b)
    for b in bookings:
        if b['status'] not in ('Completed', 'Active') or r.random() >= .24: continue
        d = b['_s'] + day(r.randint(0, b['days'] - 1)); k = _wchoice(r, TOLL_KINDS, [.72, .18, .10])
        amt = R2(r.uniform(2, 14)) if k == 'Toll' else R2(r.uniform(35, 75)) if k == 'Parking ticket' else R2(r.uniform(60, 180))
        tolls.append(dict(date=iso(d), kind=k, amount=amt, booking=b, vehicle_id=b['vehicle_id']))
    for _ in range(int(len(tolls) * .03)):
        v = r.choice([v for v in veh if v['status'] != 'Sold']); d = TODAY - day(r.randint(5, 600))
        if d < max(HISTORY_START, v['_buy']) or any(x['_s'] <= d <= x['_e'] for x in by_v.get(v['vehicle_id'], [])): continue
        tolls.append(dict(date=iso(d), kind=_wchoice(r, TOLL_KINDS, [.6, .25, .15]), amount=R2(r.uniform(3, 90)), booking=None, vehicle_id=v['vehicle_id']))
    tolls.sort(key=lambda x: (x['date'], x['vehicle_id']))
    for i, x in enumerate(tolls):
        x['toll_id'] = 'TL-%04d' % (i + 1); age = (TODAY - to_date(x['date'])).days
        if x['booking'] is None: st = 'No rental found'
        elif age <= 14: st = 'Passed on' if r.random() < .15 else 'Open'
        else:
            y = r.random(); st = 'Passed on' if y < .83 else 'Absorbed' if y < .92 else 'Open'
        if st == 'Open' and age > 60: st = 'Absorbed'
        x['status'] = st; x['admin_fee'] = TOLL_ADMIN_FEE if st == 'Passed on' else 0.0
        x['recovered'] = R2(x['amount'] + TOLL_ADMIN_FEE) if st == 'Passed on' else 0.0
        x['passed_on'] = iso(to_date(x['date']) + day(r.randint(3, 12))) if st == 'Passed on' and to_date(x['date']) + day(12) <= TODAY else (x['date'] if st == 'Passed on' else '')
    # ---- delivery runs, turnarounds
    r = rng('runs'); runs = []
    for b in bookings:
        if b['status'] not in ('Completed', 'Active', 'Booked') or b['pickup_location'] == 'Main lot': continue
        lc = LOC[b['pickup_location']]
        for kind, dd, tm in (('Delivery', b['_s'], _mins(b['pickup_time'])), ('Collection', b['_e'], b['_ret_min'] if 'in_time' in b else _mins(b['return_time']))):
            mins = int(lc['run_minutes'] * r.uniform(.85, 1.3)); st = _r15(tm - (mins if kind == 'Delivery' else 0))
            runs.append(dict(date=iso(dd), booking=b, kind=kind, location=b['pickup_location'], start_min=max(360, st), minutes=mins, miles=lc['one_way_miles'] * 2, fee=lc['fee_leg'], _d=dd))
    runs.sort(key=lambda x: (x['date'], x['start_min'], x['booking']['booking_id']))
    load = {}
    for i, x in enumerate(runs):
        x['run_id'] = 'DR-%05d' % (i + 1)
        pref, oth = ('Ravi Chandran', 'Jun Park') if x['_d'].weekday() in (1, 3, 5) else ('Jun Park', 'Ravi Chandran')
        drv = pref if load.get((x['date'], pref), 0.0) < 5.5 else oth
        load[(x['date'], drv)] = load.get((x['date'], drv), 0.0) + (x['minutes'] + 5) / 60.0; x['driver'] = drv
        x['status'] = 'Done' if (x['_d'] < TODAY or (x['_d'] == TODAY and x['start_min'] <= 11 * 60)) else 'Planned'
        x['driver_cost'] = R2(x['minutes'] / 60.0 * _wage(16.0, x['date']) + x['miles'] * .20)
    allv = {}
    for b in bookings:
        if b['status'] in ('Completed', 'Active', 'Booked'): allv.setdefault(b['vehicle_id'], []).append(b)
    turns = []
    base_clean = {'Economy': 40, 'Compact': 45, 'Midsize SUV': 55, '7-seat Van': 70, 'Premium': 60, 'Electric': 45}
    for vid, lst in allv.items():
        lst.sort(key=lambda b: b['_s'])
        for i, b in enumerate(lst):
            if b['status'] != 'Completed': continue
            nx = lst[i + 1] if i + 1 < len(lst) else None
            ret = b['_ret_min']; mins = int(base_clean[b['class']] * r.uniform(.8, 1.3)) + (45 if b['dirty'] else 0)
            cs = ret + r.randint(5, 40)
            if cs > 1140: cs = 1440 + 480
            ce = cs + mins; wd = (b['_e'] + day(cs // 1440)).weekday()
            cleaner = 'Lucia Fernandes' if wd < 5 else 'Kofi Mensah'
            slack = ''; npd = ''; npt = ''
            if nx is not None:
                npd, npt = nx['start_date'], nx['pickup_time']
                gapd = (nx['_s'] - b['_e']).days
                if gapd <= 3: slack = gapd * 1440 + _mins(nx['pickup_time']) - ce
            turns.append(dict(booking=b, return_date=b['end_date'], returned_time=_hm(ret), clean_date=iso(b['_e'] + day(cs // 1440)), clean_start=_hm(cs % 1440), clean_end=_hm(ce % 1440), cleaner=cleaner,
                              clean_minutes=mins, clean_cost=R2(mins / 60.0 * _wage(17.5 if cleaner == 'Lucia Fernandes' else 16.5, b['end_date'])), next_pickup=npd, next_pickup_time=npt, slack_minutes=slack))
    turns.sort(key=lambda x: (x['return_date'], x['returned_time'], x['booking']['booking_id']))
    for i, x in enumerate(turns): x['turn_id'] = 'TN-%05d' % (i + 1)
    w.update(VBY=VBY, renters=renters, fees_rows=fees_rows, claims=claims, deps=deps, pays=pays, invoices=invoices, payouts=payouts, tolls=tolls, runs=runs, turns=turns,
             story=dict(a=story_a, b=story_b, claim=story_claim, short=story_short, late=story_late))
    _finance(w)
    return w


def _month_range(a, b):
    out = []; d = _ms(a)
    while d <= _ms(b): out.append(d); d = add_months(d, 1)
    return out


def _finance(w):
    veh, bookings, maint = w['veh'], w['bookings'], w['maint']
    # ---- financing
    fin = []
    for v in veh:
        v['_payoff'] = 0.0
        if v['_sold']:
            mo = (v['_sold'] - v['_buy']).days / 30.4
            v['sold_price'] = float(round(v['purchase_price'] * max(.30, 1 - .019 * mo) * rng('sale' + v['vehicle_id']).uniform(.96, 1.04) / 50.0) * 50)
        if not v['financed']: continue
        bal = v['loan_amount']; rt = v['loan_rate'] / 12.0; buy = v['_buy']
        for k in range(1, v['loan_months'] + 1):
            d = add_months(D(buy.year, buy.month, 5), k)
            if (v['_sold'] and d >= v['_sold']) or d > TODAY: break
            interest = R2(bal * rt); princ = R2(v['monthly_payment'] - interest); bal = R2(bal - princ)
            if d >= HISTORY_START: fin.append(dict(vehicle=v, date=iso(d), month=iso(_ms(d)), payment=v['monthly_payment'], interest=interest, principal=princ, balance_after=bal))
            v['_payoff'] = bal
    fin.sort(key=lambda x: (x['date'], x['vehicle']['vehicle_id']))
    for i, x in enumerate(fin): x['fin_id'] = 'FN-%04d' % (i + 1)
    # ---- shifts and pay
    shifts = []; hrs = {}
    for t in w['turns']: hrs[t['clean_date']] = hrs.get(t['clean_date'], 0.0) + t['clean_minutes'] / 60.0
    for b in bookings:
        if b['status'] in ('Completed', 'Active') and b['_s'] <= TODAY: hrs[b['start_date']] = hrs.get(b['start_date'], 0.0) + 0.2
    runs_by = {}
    for x in w['runs']:
        if x['_d'] <= TODAY: runs_by.setdefault((x['date'], x['driver']), []).append(x)
    def addsh(d, name, role, task, start, hours, rate):
        h = max(0.5, round(hours * 4) / 4.0); s_ = _r15(start); e_ = s_ + int(h * 60) + (30 if h > 6 else 0)
        shifts.append(dict(date=iso(d), staff=name, role=role, task=task, start=_hm(s_ % 1440), end=_hm(e_ % 1440), hours=h, rate=_wage(rate, d), cost=R2(h * _wage(rate, d))))
    d = HISTORY_START
    while d <= TODAY:
        iso_d = iso(d); H = hrs.get(iso_d, 0.0)
        if H > 0:
            H += 0.5
            if d.weekday() < 5:
                a = min(H, 8.0); addsh(d, 'Lucia Fernandes', 'Detailer', 'Cleaning and prep', 480, a, 17.5)
                if H - a >= .5: addsh(d, 'Kofi Mensah', 'Detailer', 'Cleaning and prep', 600, H - a, 16.5)
            else:
                a = min(H, 8.0); addsh(d, 'Kofi Mensah', 'Detailer', 'Cleaning and prep', 540, a, 16.5)
                if H - a >= .5: addsh(d, 'Lucia Fernandes', 'Detailer', 'Cleaning and prep', 600, H - a, 17.5)
        for nm in ('Jun Park', 'Ravi Chandran'):
            rr = runs_by.get((iso_d, nm))
            if rr: addsh(d, nm, 'Delivery driver', 'Delivery runs', min(x['start_min'] for x in rr) - 15, max(2.0, sum(x['minutes'] + 5 for x in rr) / 60.0 + .5), 16.0)
        if d.weekday() >= 5 or (d.weekday() == 4 and d.month in (6, 7, 8, 12)): addsh(d, 'Sana Malik', 'Booking assistant', 'Counter and bookings', 540, 4.0 if d.weekday() < 5 else 6.0, 17.0)
        if d.weekday() in (2, 4): addsh(d, 'Elsa Nordin', 'Bookkeeper', 'Bookkeeping', 570, 4.0, 24.0)
        d += day(1)
    shifts.sort(key=lambda x: (x['date'], x['staff']))
    for i, x in enumerate(shifts):
        dd = to_date(x['date']); x['shift_id'] = 'SH-%05d' % (i + 1); x['week'] = iso(week_start(dd)); x['month'] = iso(_ms(dd)); x['weekday'] = WEEKDAYS[dd.weekday()]
    pay = []
    months = _month_range(HISTORY_START, TODAY)
    sh_by = {}
    for x in shifts:
        k = (x['month'], x['staff']); a = sh_by.setdefault(k, [0.0, 0.0]); a[0] += x['hours']; a[1] += x['cost']
    for m in months:
        cur = (m == _ms(TODAY)); stt = 'Accruing' if cur else 'Paid'
        for s in staff:
            nm = s['name']
            if s['pay_type'] == 'Owner draw': pay.append(dict(month=iso(m), staff=nm, role=s['role'], pay_type='Owner draw', hours=0.0, gross=OWNER_DRAW, employer_cost=0.0, total=OWNER_DRAW, status=stt))
            elif s['pay_type'] == 'Salary':
                g = float(round(s['monthly_salary'] / (1.0 if m >= D(TODAY.year, 1, 1) else 1.03))); g = R2(g * (TODAY.day / float(_eom(m).day))) if cur else g
                pay.append(dict(month=iso(m), staff=nm, role=s['role'], pay_type='Salary', hours=0.0, gross=g, employer_cost=R2(g * EMPLOYER_COST_PCT), total=R2(g * (1 + EMPLOYER_COST_PCT)), status=stt))
            else:
                h, g = sh_by.get((iso(m), nm), [0.0, 0.0])
                if h > 0: pay.append(dict(month=iso(m), staff=nm, role=s['role'], pay_type='Hourly', hours=R2(h), gross=R2(g), employer_cost=R2(g * EMPLOYER_COST_PCT), total=R2(g * (1 + EMPLOYER_COST_PCT)), status=stt))
        if m.month % 3 == 0 and m < _ms(TODAY): pay.append(dict(month=iso(m), staff=OWNER, role='Owner-operator', pay_type='Owner draw', hours=0.0, gross=OWNER_EXTRA, employer_cost=0.0, total=OWNER_EXTRA, status='Paid'))
    for i, x in enumerate(pay): x['pay_id'] = 'PA-%04d' % (i + 1)
    # ---- renewals and sold prices done; per vehicle month
    vm = {}
    def cell(vid, m): return vm.setdefault((vid, m), dict(rented=0, rev=0.0, chfee=0.0, fin=0.0, maint=0.0, clean=0.0, fuel=0.0, down=0))
    for b in bookings:
        if b['status'] not in ('Completed', 'Active'): continue
        per = (b['rental_amount'] + b['addon_amount'] + b['delivery_fee']) / float(b['days'])
        for k in range(b['days']):
            dd = b['_s'] + day(k)
            if dd > TODAY: break
            c = cell(b['vehicle_id'], _ms(dd)); c['rented'] += 1; c['rev'] += per; c['chfee'] += b['channel_fee'] / float(b['days'])
        if b['status'] == 'Completed' and b['class'] == 'Electric': cell(b['vehicle_id'], _ms(b['_e']))['fuel'] += 6.0
    for f in w['fees_rows']:
        c = cell(f['booking']['vehicle_id'], _ms(to_date(f['date']))); c['rev'] += f['collected']
        if f['kind'] == 'Fuel or charge refill': c['fuel'] += f['cost']
    for cl in w['claims']:
        if cl['closed_on']: cell(cl['booking']['vehicle_id'], _ms(to_date(cl['closed_on'])))['rev'] += cl['deposit_used'] + cl['claim_paid']
    for t in w['tolls']:
        if t['status'] == 'Passed on': cell(t['vehicle_id'], _ms(to_date(t['date'])))['rev'] += t['admin_fee']
    for x in fin: cell(x['vehicle']['vehicle_id'], to_date(x['month']))['fin'] += x['payment']
    for m_ in maint:
        c = cell(m_['vehicle']['vehicle_id'], _ms(m_['date'])); c['maint'] += m_['cost']
        for k in range(m_['days_off']):
            dd = m_['date'] + day(k)
            if dd <= TODAY: cell(m_['vehicle']['vehicle_id'], _ms(dd))['down'] += 1
    for t in w['turns']: cell(t['booking']['vehicle_id'], _ms(to_date(t['return_date'])))['clean'] += t['clean_cost']
    vmrows = []
    for v in veh:
        first = _ms(max(v['_buy'], HISTORY_START)); last = _ms(min(v['_sold'] or TODAY, TODAY))
        for m in _month_range(first, last):
            lo = max(v['_buy'], m); hi = min(_eom(m), TODAY, (v['_sold'] - day(1)) if v['_sold'] else TODAY)
            owned = (hi - lo).days + 1
            if owned < 1: continue
            c = cell(v['vehicle_id'], m); avail = max(1, owned - c['down']); rented = min(c['rented'], avail)
            frac = owned / float(_eom(m).day)
            months_owned = (m.year - v['_buy'].year) * 12 + m.month - v['_buy'].month
            dep = R2(v['purchase_price'] * DEP_PCT * frac) if months_owned < int((1 - DEP_FLOOR) / DEP_PCT) else 0.0
            ins = R2(v['insurance_year'] / 12.0 * frac)
            row = dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], **{'class': v['class']}, month=iso(m), available_days=avail, rented_days=rented, utilisation=R2(rented / float(avail)), revenue=R2(c['rev']),
                       channel_fees=R2(c['chfee']), financing=R2(c['fin']), insurance=ins, maintenance=R2(c['maint']), cleaning=R2(c['clean']), fuel_charge=R2(c['fuel']), depreciation=dep)
            row['profit'] = R2(row['revenue'] - row['channel_fees'] - row['financing'] - ins - row['maintenance'] - row['cleaning'] - row['fuel_charge'] - dep)
            vmrows.append(row)
    vmrows.sort(key=lambda x: (x['month'], x['vehicle_id']))
    for i, x in enumerate(vmrows): x['row_id'] = 'VM-%05d' % (i + 1)
    # ---- expenses
    ex = []
    def add(d, cat, vendor, amount, vid='', note=''):
        if amount: ex.append(dict(date=iso(d), category=cat, vendor=vendor, vehicle_id=vid, amount=R2(amount), note=note))
    for x in fin: add(to_date(x['date']), 'Vehicle financing', 'Anil Desai', x['payment'], x['vehicle']['vehicle_id'], 'loan payment')
    for rn in w['ren']:
        if rn['renewed'] and rn['renewed'] >= HISTORY_START - day(20):
            if rn['kind'] == 'Insurance renewal': add(rn['renewed'], 'Insurance', 'Hassan Ali', rn['cost'], rn['vehicle']['vehicle_id'], 'yearly premium')
            elif rn['kind'] == 'Registration renewal': add(rn['renewed'], 'Registration and inspection', 'Registration office', rn['cost'], rn['vehicle']['vehicle_id'], 'registration renewal')
    for m_ in maint:
        add(m_['date'], 'Tyres' if m_['kind'] == 'Tyre set' else 'Maintenance and repairs', VENDOR[m_['vendor_role']], m_['cost'], m_['vehicle']['vehicle_id'], m_['kind'])
    ret_by = {}
    for t in w['turns']: ret_by[_ms(to_date(t['return_date']))] = ret_by.get(_ms(to_date(t['return_date'])), 0) + 1
    chm = {}
    for p in w['payouts']:
        if p['paid_on']: chm[(_ms(to_date(p['paid_on'])), p['channel'])] = chm.get((_ms(to_date(p['paid_on'])), p['channel']), 0.0) + p['fee']
    for b in bookings:
        if b['channel'] == 'Hotel partner' and b['status'] == 'Completed': chm[(_ms(b['_e']), 'Hotel partner')] = chm.get((_ms(b['_e']), 'Hotel partner'), 0.0) + b['channel_fee']
    card = {}
    for p in w['pays']:
        if p['method'] == 'Card': card[_ms(to_date(p['date']))] = card.get(_ms(to_date(p['date'])), 0.0) + p['amount']
    stf = {}
    for p in pay:
        if p['pay_type'] != 'Owner draw': stf[p['month']] = stf.get(p['month'], 0.0) + p['total']
    ref = {}
    for f in w['fees_rows']:
        if f['kind'] == 'Fuel or charge refill': ref[_ms(to_date(f['date']))] = ref.get(_ms(to_date(f['date'])), 0.0) + f['cost']
    r = rng('exp')
    mk = []
    for m in months:
        end = min(_eom(m), TODAY); mid = min(D(m.year, m.month, 15), TODAY); first = m
        add(first, 'Rent and lot', 'Property owner', 2100.0 * (1 if m >= D(TODAY.year, 1, 1) else .96), '', 'monthly')
        add(mid, 'Utilities', 'Utility company', 250 + r.uniform(-35, 45)); add(first, 'Booking software', 'Software subscription', 95.0); add(end, 'Accounting', 'Ingrid Sorensen', 190.0)
        add(end, 'Cleaning supplies', 'Mei Zhao', 95 + 2.6 * ret_by.get(m, 0))
        add(end, 'Fuel and charging', 'Fuel and charging', R2(ref.get(m, 0.0) + 30 + 1.3 * ret_by.get(m, 0)))
        for chn in ('Marketplace A', 'Marketplace B', 'Hotel partner'): add(end, 'Channel fees', chn, chm.get((m, chn), 0.0), '', chn)
        add(end, 'Card fees', 'Payment provider', card.get(m, 0.0) * CARD_FEE_PCT)
        add(end, 'Staff pay', 'Payroll', stf.get(iso(m), 0.0))
        pk = {'Website upkeep': 85.0, 'Marketplace listing boost': 70 + r.uniform(0, 70), 'Search ads': (190 + r.uniform(0, 120)) * (1.35 if m.month in (5, 6, 11) else 1.0),
              'Local flyers': 110.0 if m.month % 2 == 0 else 0.0, 'Referral reward': r.choice([0.0, 0.0, 25.0, 40.0, 60.0])}
        for k_, a_ in pk.items():
            if a_ > 0:
                mk.append(dict(month=iso(m), kind=k_, cost=R2(a_))); add(mid, 'Marketing', k_, a_)
    for t in w['tolls']:
        if t['status'] in ('Absorbed', 'No rental found'): add(to_date(t['date']), 'Tolls and tickets absorbed', 'Toll and ticket office', t['amount'], t['vehicle_id'], t['kind'])
    ex.sort(key=lambda x: (x['date'], x['category'], x['vendor']))
    for i, x in enumerate(ex): x['expense_id'] = 'EX-%05d' % (i + 1); x['month'] = iso(_ms(to_date(x['date'])))
    # ---- profit and loss, tax, cash
    exm = {}
    for x in ex: exm[(x['month'], x['category'])] = exm.get((x['month'], x['category']), 0.0) + x['amount']
    pnl = []
    for m in months:
        rows = [x for x in vmrows if x['month'] == iso(m)]; g = lambda k_: R2(sum(x[k_] for x in rows)); e = lambda *cats: R2(sum(exm.get((iso(m), c), 0.0) for c in cats))
        row = dict(month=iso(m), vehicles=len(rows), available_days=int(g('available_days')), rented_days=int(g('rented_days')), revenue=g('revenue'), channel_fees=g('channel_fees'), financing=g('financing'),
                   insurance=g('insurance'), maintenance=g('maintenance'), fuel_charging=R2(g('fuel_charge') + 0.0), staff=e('Staff pay'),
                   overhead=e('Rent and lot', 'Utilities', 'Booking software', 'Accounting', 'Cleaning supplies', 'Marketing', 'Card fees', 'Registration and inspection', 'Tolls and tickets absorbed'),
                   depreciation=g('depreciation'))
        row['utilisation'] = R2(row['rented_days'] / float(row['available_days'])) if row['available_days'] else 0.0
        row['profit'] = R2(row['revenue'] - row['channel_fees'] - row['financing'] - row['insurance'] - row['maintenance'] - row['fuel_charging'] - row['staff'] - row['overhead'] - row['depreciation'])
        pnl.append(row)
    for i, x in enumerate(pnl): x['row_id'] = 'PL-%03d' % (i + 1)
    tax, bal = [], 0.0
    for i, p in enumerate(pnl):
        sa = R2(max(0.0, p['profit']) * TAX_SET_ASIDE_PCT); bal = R2(bal + sa); pd_ = 0.0
        if to_date(p['month']).month in (1, 4, 7, 10) and i > 0 and to_date(p['month']) <= _ms(TODAY): pd_ = bal; bal = 0.0
        tax.append(dict(row_id='TX-%03d' % (i + 1), month=p['month'], profit=p['profit'], set_aside=sa, paid_to_tax=R2(pd_), balance=bal))
    cash = []; cl = 0.0; rows_ = []
    rec = {}
    for p in w['pays']: rec[_ms(to_date(p['date']))] = rec.get(_ms(to_date(p['date'])), 0.0) + p['amount']
    out_ = {}
    for x in ex: out_[to_date(x['month'])] = out_.get(to_date(x['month']), 0.0) + x['amount']
    buy_ = {}; sell_ = {}
    for v in veh:
        if v['_buy'] >= HISTORY_START: buy_[_ms(v['_buy'])] = buy_.get(_ms(v['_buy']), 0.0) + v['purchase_price'] - v['loan_amount']
        if v['_sold']: sell_[_ms(v['_sold'])] = sell_.get(_ms(v['_sold']), 0.0) + v['sold_price'] - v['_payoff']
    draw = {}
    for p in pay:
        if p['pay_type'] == 'Owner draw': draw[to_date(p['month'])] = draw.get(to_date(p['month']), 0.0) + p['total']
    for i, m in enumerate(months):
        t_ = tax[i]['set_aside']
        net = rec.get(m, 0.0) - out_.get(m, 0.0) - buy_.get(m, 0.0) + sell_.get(m, 0.0) - draw.get(m, 0.0) - t_
        rows_.append((m, rec.get(m, 0.0), out_.get(m, 0.0), buy_.get(m, 0.0), sell_.get(m, 0.0), draw.get(m, 0.0), t_, net))
    cum, lo = 0.0, 0.0
    for x in rows_: cum += x[7]; lo = min(lo, cum)
    opening = CASH_FLOOR * 1.45 - lo
    for i, (m, rc, ou, bu, se, dr_, ta, net) in enumerate(rows_):
        cash.append(dict(row_id='CF-%03d' % (i + 1), month=iso(m), opening=R2(opening), receipts=R2(rc), operating_costs=R2(ou), vehicle_purchases=R2(bu), vehicle_sales=R2(se), owner_draw=R2(dr_), tax_set_aside=R2(ta),
                         closing=R2(opening + net)))
        opening = opening + net
    w.update(fin=fin, shifts=shifts, pay=pay, vmrows=vmrows, ex=ex, pnl=pnl, tax=tax, cash=cash, mk=mk)
    _enquiries(w)


def _enquiries(w):
    r = rng('enq'); bookings = w['bookings']; rows = []
    direct = [b for b in bookings if b['channel'] in ('Website', 'Phone', 'Corporate account', 'Hotel partner')]
    for b in direct:
        d = to_date(b['created_on']) - day(r.choice([0, 0, 0, 1, 1, 2]))
        if d < HISTORY_START - day(10): d = to_date(b['created_on'])
        rows.append(dict(date=iso(d), source=b['channel'], class_wanted=b['class'], pickup_date=b['start_date'], days=b['days'], quote_amount=b['total'], reply=R2(r.choice([.25, .4, .6, .9, 1.4, 2.2, 3.5, 5.0, 8.0]) * r.uniform(.6, 1.4)),
                         status='Booked', lost_reason='', booking_id=b['booking_id'], staff=r.choice(['Tomas Kowalski', 'Tomas Kowalski', 'Sana Malik', 'Nadia Haddad'])))
    n_lost = int(len(direct) * .72); cls = [c['class'] for c in classes]
    for k in range(n_lost):
        b = r.choice(direct); d = to_date(b['created_on']) + day(r.randint(-3, 3))
        if d > TODAY - day(6) or d < HISTORY_START: d = to_date(b['created_on']) - day(r.randint(0, 2))
        if d > TODAY - day(6): continue
        reason = _wchoice(r, LOST_REASONS, [.26, .34, .16, .14, .10]); cl_ = r.choice(cls); L = _length(r, cl_); pick = d + day(r.randint(1, 28))
        pr = CLS[cl_]['daily_rate'] * _SEASON_MULT_AT(pick) * L * (1.05 if reason == 'Price' else 1.0) * (0.85 if L >= 7 else 1.0)
        rp = r.uniform(30, 70) if reason == 'No reply' else r.uniform(.3, 9.0)
        rows.append(dict(date=iso(d), source=_wchoice(r, ['Website', 'Phone', 'Corporate account', 'Hotel partner'], [.45, .3, .1, .15]), class_wanted=cl_, pickup_date=iso(pick), days=L, quote_amount=R2(pr),
                         reply=R2(rp), status='Lost', lost_reason=reason, booking_id='', staff=r.choice(['Tomas Kowalski', 'Sana Malik'])))
    for k in range(26):
        d = TODAY - day(r.randint(0, 5)); cl_ = r.choice(cls); L = _length(r, cl_); pick = d + day(r.randint(2, 25))
        st = 'Quoted' if k % 3 else 'Open'
        rows.append(dict(date=iso(d), source=_wchoice(r, ['Website', 'Phone', 'Corporate account', 'Hotel partner'], [.45, .3, .1, .15]), class_wanted=cl_, pickup_date=iso(pick), days=L,
                         quote_amount=R2(CLS[cl_]['daily_rate'] * _SEASON_MULT_AT(pick) * L) if st == 'Quoted' else 0.0, reply=R2(r.uniform(.3, 6)) if st == 'Quoted' else 0.0, status=st, lost_reason='', booking_id='',
                         staff=r.choice(['Tomas Kowalski', 'Sana Malik'])))
    rows.sort(key=lambda x: (x['date'], x['source'], x['class_wanted']))
    for i, x in enumerate(rows): x['enquiry_id'] = 'EQ-%04d' % (i + 1); x['month'] = iso(_ms(to_date(x['date'])))
    w['enq'] = rows


def _SEASON_MULT_AT(d): return SEASON_MULT[_season(d)] * _rate_factor(d)


# ------------------------------------------------------------------ public rows
def _W(): return _raw('world', _world)


def _public():
    w = _W(); P = {}
    veh = w['veh']
    P['vehicle_rows'] = [dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], plate=v['plate'], **{'class': v['class']}, fuel=v['fuel'], seats=v['seats'], year=v['year'], colour=v['colour'],
                              purchase_date=v['purchase_date'], purchase_price=v['purchase_price'], financed=v['financed'], loan_amount=v['loan_amount'], loan_rate=v['loan_rate'], loan_months=v['loan_months'],
                              monthly_payment=v['monthly_payment'], odometer_at_purchase=v['odometer_at_purchase'], odometer=v['_odo_now'], status=v['status'], sold_date=v['sold_date'],
                              sold_price=v['sold_price'], interval_miles=v['interval_miles'], interval_months=v['interval_months'], last_service_date=v['last_service_date'],
                              last_service_odometer=v['last_service_odometer'], insurance_year=v['insurance_year'],
                              resale_estimate=float(round(v['purchase_price'] * max(.28, 1 - .019 * ((TODAY - v['_buy']).days / 30.4)) / 50.0) * 50) if not v['_sold'] else v['sold_price']) for v in veh]
    P['renter_rows'] = [dict(renter_id=x['renter_id'], renter=x['renter'], age_band=x['age_band'], status=x['status'], documents_checked=x['documents_checked'], account=x['account'], source=x['source'],
                             first_rental=x['first_rental'], last_rental=x['last_rental'], rentals=x['rentals'], phone=fake_phone(1000 + i)) for i, x in enumerate(w['renters'])]
    keys = ['booking_id', 'created_on', 'start_date', 'end_date', 'days', 'pickup_time', 'return_time', 'vehicle_id', 'vehicle', 'class', 'renter_id', 'renter', 'channel', 'plan', 'season', 'day_rate',
            'rental_amount', 'addon_amount', 'delivery_fee', 'total', 'fee_pct', 'channel_fee', 'net_amount', 'pickup_location', 'deposit', 'miles_included', 'young_driver', 'extended', 'status']
    P['booking_rows'] = [{k: b[k] for k in keys} for b in w['bookings']]
    al = []
    for b in w['bookings']:
        for a, q, amt, cst in b['_adds']: al.append(dict(booking_id=b['booking_id'], start_date=b['start_date'], month=iso(_ms(b['_s'])), channel=b['channel'], addon=a, days=q, amount=amt, cost=cst, status=b['status']))
    al.sort(key=lambda x: (x['start_date'], x['booking_id']))
    for i, x in enumerate(al): x['line_id'] = 'AL-%05d' % (i + 1)
    P['addon_rows'] = [{k: x[k] for k in ['line_id', 'booking_id', 'start_date', 'month', 'channel', 'addon', 'days', 'amount', 'cost', 'status']} for x in al]
    ho = []
    for b in w['bookings']:
        if b['status'] not in ('Completed', 'Active'): continue
        done = b['status'] == 'Completed'
        ho.append(dict(booking_id=b['booking_id'], vehicle_id=b['vehicle_id'], vehicle=b['vehicle'], renter_id=b['renter_id'], out_date=b['start_date'], out_time=b['out_time'], out_odometer=b['out_odometer'],
                       out_level=b['out_level'], photos_out=b['photos_out'], keys=b['keys'], deposit_taken=b['deposit_taken'], handled_by=b['handled_by'], in_date=b['end_date'] if done else '',
                       in_time=b['in_time'] if done else '', in_odometer=b['in_odometer'] if done else '', in_level=b['in_level'] if done else '', photos_in=b['photos_in'] if done else False,
                       damage_seen=b['damage_seen'] if done else False, miles_driven=b['miles_driven'] if done else '', miles_included=b['miles_included'], extra_miles=b['extra_miles'] if done else '',
                       late_minutes=b['late_minutes'] if done else '', fuel_shortfall=b['fuel_shortfall'] if done else '', fee_due=R2(sum(f['due'] for f in b['_fees']))))
    ho.sort(key=lambda x: (x['out_date'], x['out_time'], x['vehicle_id']))
    for i, x in enumerate(ho): x['handover_id'] = 'HO-%05d' % (i + 1)
    P['handover_rows'] = [dict(handover_id=x['handover_id'], **{k: v_ for k, v_ in x.items() if k != 'handover_id'}) for x in ho]
    P['fee_rows'] = [dict(fee_id=f['fee_id'], booking_id=f['booking']['booking_id'], vehicle_id=f['booking']['vehicle_id'], date=f['date'], month=iso(_ms(to_date(f['date']))), kind=f['kind'], amount_due=f['due'],
                          billed=f['billed'], collected=f['collected'], status=f['status']) for f in w['fees_rows']]
    P['claim_rows'] = [dict(claim_id=c['claim_id'], booking_id=c['booking']['booking_id'], vehicle_id=c['booking']['vehicle_id'], vehicle=c['booking']['vehicle'], renter_id=c['booking']['renter_id'],
                            reported_on=c['reported_on'], month=iso(_ms(to_date(c['reported_on']))), kind=c['kind'], status=c['status'], estimate=c['estimate'], repair_cost=c['repair_cost'],
                            deposit_used=c['deposit_used'], claim_paid=c['claim_paid'], written_off=c['written_off'], closed_on=c['closed_on'], days_open=c['days_open']) for c in w['claims']]
    P['deposit_rows'] = [dict(deposit_id=x['deposit_id'], booking_id=x['booking']['booking_id'], vehicle_id=x['booking']['vehicle_id'], renter_id=x['booking']['renter_id'], amount=x['amount'], held_on=x['held_on'],
                              release_due=x['release_due'], released_on=x['released_on'], status=x['status'], kept_amount=x['kept_amount'], refunded_amount=x['refunded_amount'], reason=x['reason']) for x in w['deps']]
    P['payment_rows'] = [dict(payment_id=p['payment_id'], date=p['date'], month=iso(_ms(to_date(p['date']))), booking_id=p['booking']['booking_id'], renter_id=p['booking']['renter_id'],
                              channel=p['booking']['channel'], kind=p['kind'], method=p['method'], amount=p['amount'], payout_id=p['payout_id']) for p in w['pays']]
    P['payout_rows'] = [dict(payout_id=p['payout_id'], booking_id=p['booking']['booking_id'], channel=p['channel'], booking_value=p['booking_value'], fee=p['fee'], expected_payout=p['expected_payout'],
                             expected_on=p['expected_on'], month=iso(_ms(to_date(p['expected_on']))), received=p['received'], paid_on=p['paid_on'], status=p['status']) for p in w['payouts']]
    P['invoice_rows'] = [dict(invoice_id=x['invoice_id'], booking_id=x['booking']['booking_id'], renter_id=x['booking']['renter_id'], account=[r_['account'] for r_ in w['renters'] if r_['renter_id'] == x['booking']['renter_id']][0],
                              issued_on=x['issued_on'], due_date=x['due_date'], amount=x['amount'], paid_amount=x['paid_amount'], paid_on=x['paid_on'], status=x['status']) for x in w['invoices']]
    P['toll_rows'] = [dict(toll_id=t['toll_id'], date=t['date'], month=iso(_ms(to_date(t['date']))), vehicle_id=t['vehicle_id'], vehicle=w['VBY'][t['vehicle_id']]['vehicle'], kind=t['kind'], amount=t['amount'],
                           booking_id=t['booking']['booking_id'] if t['booking'] else '', renter_id=t['booking']['renter_id'] if t['booking'] else '', status=t['status'], admin_fee=t['admin_fee'],
                           recovered=t['recovered'], passed_on=t['passed_on']) for t in w['tolls']]
    P['maintenance_rows'] = [dict(maint_id=m['maint_id'], vehicle_id=m['vehicle']['vehicle_id'], vehicle=m['vehicle']['vehicle'], date=iso(m['date']), month=iso(_ms(m['date'])), kind=m['kind'], odometer=m['odometer'],
                                  cost=m['cost'], days_off_road=m['days_off'], vendor=VENDOR[m['vendor_role']]) for m in w['maint']]
    rn = sorted([r_ for r_ in w['ren']], key=lambda x: (x['due'], x['vehicle']['vehicle_id'], x['kind']))
    P['renewal_rows'] = [dict(renewal_id='RV-%03d' % (i + 1), vehicle_id=x['vehicle']['vehicle_id'], vehicle=x['vehicle']['vehicle'], kind=x['kind'], due_date=iso(x['due']), renewed_on=iso(x['renewed']) if x['renewed'] else '',
                              cost=x['cost'], status=x['status']) for i, x in enumerate(rn)]
    P['financing_rows'] = [dict(fin_id=x['fin_id'], date=x['date'], month=x['month'], vehicle_id=x['vehicle']['vehicle_id'], vehicle=x['vehicle']['vehicle'], payment=x['payment'], interest=x['interest'],
                                principal=x['principal'], balance_after=x['balance_after']) for x in w['fin']]
    P['delivery_rows'] = [dict(run_id=x['run_id'], date=x['date'], month=iso(_ms(x['_d'])), booking_id=x['booking']['booking_id'], vehicle_id=x['booking']['vehicle_id'], kind=x['kind'], location=x['location'],
                               driver=x['driver'], start_time=_hm(x['start_min']), minutes=x['minutes'], miles=x['miles'], fee_charged=x['fee'], driver_cost=x['driver_cost'], status=x['status']) for x in w['runs']]
    P['turnaround_rows'] = [dict(turn_id=t['turn_id'], booking_id=t['booking']['booking_id'], vehicle_id=t['booking']['vehicle_id'], vehicle=t['booking']['vehicle'], return_date=t['return_date'], returned_time=t['returned_time'],
                                 clean_date=t['clean_date'], clean_start=t['clean_start'], clean_end=t['clean_end'], cleaner=t['cleaner'], clean_minutes=t['clean_minutes'], clean_cost=t['clean_cost'],
                                 next_pickup=t['next_pickup'], next_pickup_time=t['next_pickup_time'], slack_minutes=t['slack_minutes']) for t in w['turns']]
    P['shift_rows'] = [{k: x[k] for k in ['shift_id', 'date', 'week', 'month', 'weekday', 'staff', 'role', 'task', 'start', 'end', 'hours', 'rate', 'cost']} for x in w['shifts']]
    P['pay_rows'] = [{k: x[k] for k in ['pay_id', 'month', 'staff', 'role', 'pay_type', 'hours', 'gross', 'employer_cost', 'total', 'status']} for x in w['pay']]
    P['enquiry_rows'] = [dict(enquiry_id=x['enquiry_id'], date=x['date'], month=x['month'], source=x['source'], class_wanted=x['class_wanted'], pickup_date=x['pickup_date'], days=x['days'],
                              quote_amount=x['quote_amount'], first_reply_hours=x['reply'], status=x['status'], lost_reason=x['lost_reason'], booking_id=x['booking_id'], staff=x['staff']) for x in w['enq']]
    cm = {'Website upkeep': 'Website', 'Marketplace listing boost': 'Marketplace A', 'Local flyers': 'Phone', 'Search ads': 'Website', 'Referral reward': 'Hotel partner'}
    enq_n, bk_n, cost_n = {}, {}, {}
    for e in P['enquiry_rows']: enq_n[(e['month'], e['source'])] = enq_n.get((e['month'], e['source']), 0) + 1
    for b in w['bookings']:
        if b['status'] not in ('Cancelled',): bk_n[(iso(_ms(to_date(b['created_on']))), b['channel'])] = bk_n.get((iso(_ms(to_date(b['created_on']))), b['channel']), 0) + 1
    for x in w['mk']: cost_n[(x['month'], cm[x['kind']])] = cost_n.get((x['month'], cm[x['kind']]), 0.0) + x['cost']
    mk = []
    for i, x in enumerate(w['mk']):
        ch = cm[x['kind']]; sh = x['cost'] / cost_n[(x['month'], ch)]
        mk.append(dict(campaign_id='MK-%03d' % (i + 1), month=x['month'], kind=x['kind'], channel=ch, cost=x['cost'], enquiries=int(round(enq_n.get((x['month'], ch), 0) * sh * .5)),
                       bookings=int(round(bk_n.get((x['month'], ch), 0) * sh * .5))))
    P['marketing_rows'] = mk
    P['expense_rows'] = [{k: x[k] for k in ['expense_id', 'date', 'month', 'category', 'vendor', 'vehicle_id', 'amount', 'note']} for x in w['ex']]
    P['vehicle_month_rows'] = [{k: x[k] for k in ['row_id', 'vehicle_id', 'vehicle', 'class', 'month', 'available_days', 'rented_days', 'utilisation', 'revenue', 'channel_fees', 'financing', 'insurance',
                                                  'maintenance', 'cleaning', 'fuel_charge', 'depreciation', 'profit']} for x in w['vmrows']]
    P['pnl_rows'] = w['pnl']; P['cash_rows'] = w['cash']; P['tax_rows'] = w['tax']
    return P


def _mk(name):
    def f(n=None): return _thin(_cached(name, lambda: _public()[name]), n)
    f.__name__ = name; return f
for _nm in ['vehicle_rows', 'renter_rows', 'booking_rows', 'addon_rows', 'handover_rows', 'fee_rows', 'claim_rows', 'deposit_rows', 'payment_rows', 'payout_rows', 'invoice_rows', 'toll_rows',
            'maintenance_rows', 'renewal_rows', 'financing_rows', 'delivery_rows', 'turnaround_rows', 'shift_rows', 'pay_rows', 'enquiry_rows', 'marketing_rows', 'expense_rows', 'vehicle_month_rows',
            'pnl_rows', 'cash_rows', 'tax_rows']:
    globals()[_nm] = _mk(_nm)


def vehicle_profit(vid, months=12):
    rows = [x for x in vehicle_month_rows() if x['vehicle_id'] == vid and to_date(x['month']) >= month_start(months) and to_date(x['month']) < _ms(TODAY)]
    return dict(profit=R2(sum(x['profit'] for x in rows)), revenue=R2(sum(x['revenue'] for x in rows)), months=len(rows), worst=max([x['profit'] for x in rows] or [0.0]))


def class_utilisation(months=3):
    out = {}
    for c in CLASSES:
        rows = [x for x in vehicle_month_rows() if x['class'] == c and to_date(x['month']) >= month_start(months) and to_date(x['month']) < _ms(TODAY)]
        a = sum(x['available_days'] for x in rows); out[c] = R2(sum(x['rented_days'] for x in rows) / float(a)) if a else 0.0
    return out


def story():
    """ids of the story rows: low_vehicle (+ low_vehicle_name, low_profit_12m, low_util_12m, low_months_loss); overlap_a, overlap_b, overlap_vehicle, overlap_start, overlap_end;
    claim_id (+ claim_days_open, claim_booking, claim_vehicle, claim_estimate, claim_deposit_id, claim_deposit_held); service_vehicle (+ service_miles_over, service_booking, service_start,
    service_odometer, service_interval); renewal_id (+ renewal_vehicle, renewal_kind, renewal_date, renewal_days); payout_id (short-paid; + payout_expected, payout_received, payout_gap,
    payout_booking, payout_channel, payout_days) and late_payout_id"""
    w = _W(); s = w['story']; out = {}
    lv = w['by_key'][_KEY_LOW]; vp = vehicle_profit(lv['vehicle_id'], 12); ms = [x for x in vehicle_month_rows() if x['vehicle_id'] == lv['vehicle_id'] and to_date(x['month']) >= month_start(12)]
    assert all(x['profit'] < 0 for x in ms) and len(ms) >= 12, [x['profit'] for x in ms]
    u12 = sum(x['rented_days'] for x in ms) / float(sum(x['available_days'] for x in ms))
    out.update(low_vehicle=lv['vehicle_id'], low_vehicle_name=lv['vehicle'], low_profit_12m=vp['profit'], low_util_12m=R2(u12), low_months_loss=len(ms))
    a, b = s['a'], s['b']
    assert a['vehicle_id'] == b['vehicle_id'] and b['_s'] <= a['_e'] and a['status'] in ('Booked', 'Active')
    out.update(overlap_a=a['booking_id'], overlap_b=b['booking_id'], overlap_vehicle=a['vehicle_id'], overlap_start=b['start_date'], overlap_end=a['end_date'])
    c = s['claim']; dp = [x for x in w['deps'] if x['booking'] is c['booking']]
    out.update(claim_id=c['claim_id'], claim_days_open=c['days_open'], claim_booking=c['booking']['booking_id'], claim_vehicle=c['booking']['vehicle_id'], claim_estimate=c['estimate'],
               claim_deposit_id=dp[0]['deposit_id'] if dp else '', claim_deposit_held=dp[0]['amount'] if dp else 0.0)
    sv = w['by_key'][_KEY_SVC]; over = sv['_odo_now'] - sv['last_service_odometer'] - sv['interval_miles']
    bk = [b_ for b_ in w['bookings'] if b_['vehicle_id'] == sv['vehicle_id'] and b_['status'] in ('Booked', 'Active') and TODAY <= b_['_s'] <= TODAY + day(7)]
    assert over > 300 and bk, (over, bk)
    out.update(service_vehicle=sv['vehicle_id'], service_miles_over=over, service_booking=bk[0]['booking_id'], service_start=bk[0]['start_date'], service_odometer=sv['_odo_now'], service_interval=sv['interval_miles'])
    rn = [x for x in renewal_rows() if x['status'] == 'Upcoming' and (to_date(x['due_date']) - TODAY).days <= 45]
    assert len(rn) == 1, rn
    out.update(renewal_id=rn[0]['renewal_id'], renewal_vehicle=rn[0]['vehicle_id'], renewal_kind=rn[0]['kind'], renewal_date=rn[0]['due_date'], renewal_days=(to_date(rn[0]['due_date']) - TODAY).days)
    p = s['short']; l = s['late']
    out.update(payout_id=p['payout_id'], payout_expected=p['expected_payout'], payout_received=p['received'], payout_gap=R2(p['expected_payout'] - p['received']), payout_booking=p['booking']['booking_id'],
               payout_channel=p['channel'], payout_days=(TODAY - to_date(p['expected_on'])).days, late_payout_id=l['payout_id'])
    assert sum(1 for x in payout_rows() if x['status'] == 'Short-paid') == 1 and sum(1 for x in payout_rows() if x['status'] == 'Late') == 1
    assert sum(1 for x in claim_rows() if x['status'] in OPEN_CLAIM and x['days_open'] >= 45) == 1
    return out


_GENS = ['vehicle_rows', 'renter_rows', 'booking_rows', 'addon_rows', 'handover_rows', 'fee_rows', 'claim_rows', 'deposit_rows', 'payment_rows', 'payout_rows', 'invoice_rows', 'toll_rows',
         'maintenance_rows', 'renewal_rows', 'financing_rows', 'delivery_rows', 'turnaround_rows', 'shift_rows', 'pay_rows', 'enquiry_rows', 'marketing_rows', 'expense_rows', 'vehicle_month_rows',
         'pnl_rows', 'cash_rows', 'tax_rows', 'event_rows']


def _digest():
    h = hashlib.md5()
    for nm in _GENS: h.update(repr(globals()[nm]()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); S = story(); G = {nm: globals()[nm]() for nm in _GENS}
    print('team', len(team), 'classes', len(classes), 'seasons', len(seasons), 'addons', len(addons), 'fees', len(fees), 'locations', len(locations), 'channels', len(channels), 'service_types', len(service_types))
    print(' '.join('%s %d' % (nm.replace('_rows', ''), len(v)) for nm, v in G.items()))
    print(S)
    print('seconds %.1f digest %s' % (time.time() - t0, _digest()))
