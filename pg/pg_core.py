"""Pet grooming business suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (one cached world is built on first use). The demo business is "Willowbrook Pet Grooming"
(fictional): a grooming salon run by an owner-groomer (Rosa Delgado, PG-01) with 3 salon groomers (PG-02 Tomas Eriksen on 50% commission, PG-03 Mei Tanaka hourly plus a
small production bonus, PG-04 Chidi Adeyemi on a fixed 60% commission, part-time), 2 bathers (PG-06, PG-07, hourly), a front-desk coordinator (PG-08, hourly) and one mobile
grooming van with its own groomer (PG-05 Lucia Ferreira, 50% commission, route days Tuesday to Friday), plus 8 outside contacts (PG-09..PG-16: accountant, grooming-supply
wholesaler, clipper and dryer repair service, van mechanic, landlord, laundry service, insurance broker, print and sign shop). 4 grooming tables and the van, about 830 clients
(about 650 active in the last 90 days) with about 960 pets (mostly dogs, some cats), recurring clients rebooked every 4-8 weeks, walk-ins for nail trims. About 10,200 appointment rows over ~2 years (oldest
first, about 500 grooms a month now). One generic currency; every date is relative to the build day. A solo groomer (salon or mobile) can use most parts: hide the staff columns.

Money model: a groom is priced by service and size band (Small, Medium, Large, Giant) times a coat factor (Short coat 0.9 ... Curly coat 1.15), rounded to the whole unit; prices
rose about 5% on 1 January of this year. Add-ons are priced separately (attach rate about 60%, below the owner's 75% target), matting is charged per 10 minutes (about a third of
the matting due is given away), a handling fee applies to some pets (about 30% waived). Deposits: a new client pays DEPOSIT (20) when booking (some are never collected), applied to
the bill or kept on a no-show. Late cancels (under 24 hours) and no-shows are charged LATE_FEE_PCT (50%) of the base price; only about half of those fees are charged. Tips go to the
groomer who did the groom (individual). Pay: commission groomers share_pct x service price, hourly staff rate x hours, Mei Tanaka also 5% of her sales above 7,000 a month;
employer on-cost 13% on top; commission groomers have a monthly minimum top-up (guarantee). A groomer's real profit = sales - pay - on-cost - back-bar product - station cost
(STATION_COST_MONTH, rent and power share). Mobile route day: fuel per mile, water, generator hours, van wear per mile and a van fixed cost per day come off the day's takings.
Reporting month = month of the appointment for revenue, month of the payment for cash. Seasons: busy before the year-end holidays (mid-November to the third week of December),
spring to early summer (shedding season), quiet January and February.

Story rows (ids from story(), never hard-coded): commission_groomer (Chidi Adeyemi: fixed 60% commission, low sales, loses money after on-costs and station cost),
lapsed_client (a regular 6-week client with a Full groom, last visit about 105 days ago, no next booking), noshow_client (a new client's no-show, fee 50% never charged and deposit
not collected), vaccination_pet (a pet booked next week whose vaccination record date has passed), overdue_equipment (a clipper 20+ days past its service date, plus the van due
soon), renewal_due (liability insurance ends in 12 days, not renewed), losing_van_day (a recent route day with 2 grooms and a long drive that loses money).

Exports
  constants: COMPANY SUITE OWNER HISTORY_START HISTORY_DAYS LATE_FEE_PCT LATE_CANCEL_HOURS DEPOSIT STRIKES_MAX EMPLOYER_COST_PCT OWNER_DRAW TAX_SET_ASIDE_PCT STATION_COST_MONTH
             MIN_PRICE_HOUR REBOOK_TARGET ATTACH_TARGET UTIL_TARGET REV_STATION_TARGET FUEL_MILE WATER_DAY GEN_HOUR WEAR_MILE VAN_FIXED_DAY CASH_FLOOR CARD_FEE_PCT DAY_MINUTES
             LAPSE_FACTOR PRICE_STEP GUARANTEE RENEWAL_WARN_DAYS
  dates: TODAY iso ago ahead to_date month_start add_months months14() months24() week_start; helpers pairs first_name fake_phone fake_email rng R2
  lists: ROLES TEAMS PAY_TYPES SPECIES SIZES COATS SERVICES ADDON_NAMES SURCHARGE_NAMES STATUSES CHANNELS TEMPERAMENTS VACC_STATUS AREAS STATIONS SOURCES PAY_METHODS DEPOSIT_STATUS
         WAIT_STATUS WINBACK_RESULTS EQUIP_KINDS SERVICE_KINDS RENEWAL_KINDS INCIDENT_KINDS EXPENSE_CATEGORIES PAY_STATUS TAX_STATUS MARKETING_KINDS RETAIL_KINDS
         BACKBAR_NAMES TASKS WEEKDAYS WORKDAYS
  names: GROOMERS (5, grooms) STAFF_NAMES (8) PAID_STAFF (7, pay rows) BATHERS CONTRACTORS (commission groomers)
  people and reference: staff (8) contacts (8) team (16) services (8) price_list (32) coats (5) addons (8) surcharges (6) areas (6) stations (5) breeds (21) equipment (34)
             retail_products (14) backbar_products (10) vans (1)
  generators (fresh lists of dicts, oldest first; n= thins a long list but keeps the most recent rows; optional dates are '' when blank):
    client_rows pet_rows appointment_rows noshow_rows deposit_rows payment_rows tip_rows retail_sale_rows backbar_use_rows van_day_rows groomer_month_rows pay_rows hours_rows
    daily_take_rows service_month_rows breed_profit_rows equipment_rows equipment_service_rows incident_rows waitlist_rows slot_rows winback_rows rebook_rows review_rows
    marketing_rows expense_rows tax_rows cash_rows renewal_rows training_rows
  helpers: service_profit(service, months=12) groomer_profit(name, months=3) story()
Lesson: money cells are plain amounts; optional dates are '' when blank (wrap lookups with IF(x=0,"",x)). Links hold NAMES (client, groomer, service) or ids (client CL-0001,
pet PT-0001, appointment AP-00001). Words: no veterinary or medical claims; health notes are owner-reported observations; vaccination records are dates and status only.
"""
import datetime as dt
import calendar
import random
import hashlib

COMPANY = 'Willowbrook Pet Grooming'
SUITE = 'fx-20261115-pet-grooming'
OWNER = 'Rosa Delgado'
TODAY = dt.date.today()
D = dt.date

LATE_FEE_PCT = 0.5          # share of the base price charged for a late cancel or a no-show
LATE_CANCEL_HOURS = 24
DEPOSIT = 20.0              # new-client deposit
STRIKES_MAX = 2             # strikes before a client must prepay
EMPLOYER_COST_PCT = 0.13
OWNER_DRAW = 5000.0
TAX_SET_ASIDE_PCT = 0.25
STATION_COST_MONTH = 1500.0  # rent, power and laundry share per grooming table per month
MIN_PRICE_HOUR = 50.0       # the owner's minimum price per groomer hour (your number)
REBOOK_TARGET = 0.70        # rebook-at-checkout rate wanted (your number)
ATTACH_TARGET = 0.75        # share of grooms with an add-on wanted (your number)
UTIL_TARGET = 0.80          # share of open minutes booked (your number)
REV_STATION_TARGET = 120000.0  # revenue per table per year (your number)
FUEL_MILE = 0.30            # van fuel per mile
WATER_DAY = 12.0            # fresh water and waste per route day
GEN_HOUR = 3.5              # generator fuel per hour
WEAR_MILE = 0.18            # van wear per mile
VAN_FIXED_DAY = 22.0        # van insurance and loan share per route day
CASH_FLOOR = 10000.0
CARD_FEE_PCT = 0.026
DAY_MINUTES = 480           # groom minutes a groomer can book in a day
LAPSE_FACTOR = 1.5          # lapsed = no visit in 1.5 times the usual interval
PRICE_STEP = 1
GUARANTEE = 2400.0          # monthly minimum for commission groomers
RENEWAL_WARN_DAYS = 45
VAN_COST_BASE = 0.0


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
def months24(): return [month_start(k) for k in range(23, -1, -1)]
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
def fake_email(name, i=0): return name.lower().replace(' ', '.').replace("'", '') + (str(i) if i else '') + '@mail.example.com'
def rng(tag=''): return random.Random('pg-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


HISTORY_START = month_start(23)
HISTORY_DAYS = (TODAY - HISTORY_START).days

# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Owner groomer', 'Groomer', 'Mobile groomer', 'Bather', 'Front desk coordinator', 'Accountant', 'Grooming supply wholesaler', 'Clipper and dryer repair', 'Van mechanic',
         'Landlord', 'Laundry service', 'Insurance broker', 'Print and sign shop']
TEAMS = ['Management', 'Grooming', 'Front desk', 'Outside']
PAY_TYPES = ['Owner draw', 'Commission', 'Hourly plus bonus', 'Hourly', 'Invoice']
SPECIES = ['Dog', 'Cat']
SIZES = ['Small', 'Medium', 'Large', 'Giant']
COATS = ['Short coat', 'Double coat', 'Curly coat', 'Wire coat', 'Long silky coat']
SERVICES = ['Full groom', 'Bath and brush', 'Bath and tidy', 'De-shedding', 'Hand-strip', 'Puppy intro', 'Cat groom', 'Nail trim']
ADDON_NAMES = ['Teeth brushing', 'Ear cleaning', 'Nail grind', 'Face, feet and tail tidy', 'Sanitary trim', 'Conditioning treatment', 'Paw balm', 'Bow or bandana']
SURCHARGE_NAMES = ['Matting', 'Heavy matting', 'Handling fee', 'Extra time', 'Late pick-up', 'Travel fee']
STATUSES = ['Scheduled', 'Completed', 'Cancelled', 'Late cancel', 'No-show']
CHANNELS = ['Rebooked at checkout', 'Standing appointment', 'Phone or message', 'Online booking', 'Walk-in', 'New client']
TEMPERAMENTS = ['Calm', 'Nervous with the dryer', 'Wriggly on the table', 'Needs short breaks', 'Barks at clippers', 'Sensitive paws', 'Needs two people for nails', 'Shy with strangers']
VACC_STATUS = ['Current', 'Due soon', 'Expired']
AREAS = ['Northgate', 'Riverside', 'Hillcrest', 'Old Town', 'Lakeside', 'Eastfield']
STATIONS = ['Table 1', 'Table 2', 'Table 3', 'Table 4', 'Van']
SOURCES = ['Referral from a client', 'Online search', 'Social media page', 'Local pet shop', 'Passing the salon', 'Van sighting', 'Rescue shelter partner', 'Dog trainer']
PAY_METHODS = ['Card', 'Cash', 'Bank transfer']
DEPOSIT_STATUS = ['Held', 'Applied', 'Kept', 'Refunded', 'Not collected']
WAIT_STATUS = ['Waiting', 'Offered', 'Booked', 'Removed']
WINBACK_RESULTS = ['Pending', 'Returned', 'No reply', 'Declined']
EQUIP_KINDS = ['Clipper', 'Blade set', 'Dryer', 'Tub', 'Grooming table', 'Van equipment']
SERVICE_KINDS = ['Blade sharpening', 'Clipper service', 'Dryer filter and motor check', 'Tub drain and pump check', 'Van service', 'Generator service']
RENEWAL_KINDS = ['Business licence', 'Liability insurance', 'Van insurance', 'Van road licence', 'Pet first aid course', 'Premises lease', 'Business registration', 'Equipment warranty']
INCIDENT_KINDS = ['Scratch or bite to staff', 'Nick or small cut', 'Pet escaped the table', 'Skin redness noticed', 'Pet became stressed', 'Property damaged', 'Late pick-up']
EXPENSE_CATEGORIES = ['Rent', 'Utilities', 'Laundry', 'Back-bar products', 'Retail stock', 'Blades and equipment', 'Repairs', 'Insurance', 'Booking and phone', 'Marketing', 'Training',
                      'Accounting', 'Card fees', 'Van fuel and water', 'Van loan and licence']
PAY_STATUS = ['Paid', 'Due', 'Accruing']
TAX_STATUS = ['Paid', 'Due', 'Upcoming']
MARKETING_KINDS = ['Social media post', 'Local flyers', 'Van sign', 'Pet shop partner', 'Rescue shelter event', 'Referral reward', 'Holiday booking reminder', 'Review request']
RETAIL_KINDS = ['Shampoo', 'Conditioner', 'Brush or comb', 'Treats', 'Paw balm', 'Collar or lead', 'Bandana', 'Toy']
BACKBAR_NAMES = ['Shampoo', 'Conditioner', 'Coat spray', 'Ear wipes', 'Blade coolant', 'Towels and laundry', 'Cotton and wipes', 'Paw balm tub', 'Cleaning solution', 'Disposable aprons']
TASKS = ['Bathing a small dog', 'Bathing a large dog', 'Using the dryer safely', 'Brushing out a coat', 'Nail trimming', 'Ear and face care', 'Handling a nervous pet', 'Table safety',
         'Tub and station cleaning', 'Checking in a pet', 'Reading a handling note', 'Blade and clipper care', 'Sanitary trim', 'Pick-up and checkout']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
WORKDAYS = WEEKDAYS[:6]

# ------------------------------------------------------------------ people
# id, name, country, role, team, pay type, hours a week, commission share, hourly rate, bonus share, station, speciality, start days ago
_staff = [('PG-01', 'Rosa Delgado', 'Spain', 'Owner groomer', 'Management', 'Owner draw', 40, 0, 0, 0, 'Table 1', 'Owner, hand-strip and breed cuts', 2700),
          ('PG-02', 'Tomas Eriksen', 'Denmark', 'Groomer', 'Grooming', 'Commission', 40, 0.50, 0, 0, 'Table 2', 'Full grooms, doodle and curly coats', 1900),
          ('PG-03', 'Mei Tanaka', 'Japan', 'Groomer', 'Grooming', 'Hourly plus bonus', 32, 0, 20, 0.05, 'Table 3', 'Cats and small dogs, gentle handling', 1100),
          ('PG-04', 'Chidi Adeyemi', 'Nigeria', 'Groomer', 'Grooming', 'Commission', 24, 0.60, 0, 0, 'Table 4', 'Bath and brush, large dogs (part-time)', 520),
          ('PG-05', 'Lucia Ferreira', 'Brazil', 'Mobile groomer', 'Grooming', 'Commission', 32, 0.50, 0, 0, 'Van', 'Mobile van, route days Tuesday to Friday', 700),
          ('PG-06', 'Ana Popescu', 'Romania', 'Bather', 'Grooming', 'Hourly', 24, 0, 15.5, 0, '', 'Baths, drying and brush-out', 840),
          ('PG-07', 'Kwame Mensah', 'Ghana', 'Bather', 'Grooming', 'Hourly', 20, 0, 15, 0, '', 'Baths, drying and nail trims', 330),
          ('PG-08', 'Aisha Rahman', 'Pakistan', 'Front desk coordinator', 'Front desk', 'Hourly', 28, 0, 18, 0, '', 'Front desk, bookings, till and rebooking', 1500)]
staff = []
for i, (a, b, c, ro, te, pt, hw, cm, hr, bo, stn, spec, st) in enumerate(_staff):
    staff.append(dict(staff_id=a, name=b, role=ro, team=te, pay_type=pt, phone=fake_phone(101 + i), email=fake_email(b), hours_week=hw, share_pct=cm, hourly_rate=float(hr), bonus_pct=bo,
                      guarantee=GUARANTEE if pt == 'Commission' else 0.0, station=stn, speciality=spec, country=c, start=ago(st)))
_ctc = [('PG-09', 'Sofia Lindgren', 'Sweden', 'Accountant', 'Bookkeeping, payroll and yearly accounts'),
        ('PG-10', 'Hamid Karimi', 'Iran', 'Grooming supply wholesaler', 'Back-bar products, blades and retail stock'),
        ('PG-11', 'Oskar Nowak', 'Poland', 'Clipper and dryer repair', 'Blade sharpening, clipper and dryer repairs'),
        ('PG-12', 'Gwen Pritchard', 'Wales', 'Van mechanic', 'Van service, tyres and generator'),
        ('PG-13', 'Takumi Sato', 'Japan', 'Landlord', 'Salon lease and building repairs'),
        ('PG-14', 'Fatima Zahra', 'Morocco', 'Laundry service', 'Weekly towel and cloth laundry'),
        ('PG-15', 'Olivia Brandt', 'Germany', 'Insurance broker', 'Liability and van insurance renewals'),
        ('PG-16', 'Mario Conti', 'Italy', 'Print and sign shop', 'Flyers, price lists and van signs')]
contacts = [dict(staff_id=a, name=b, role=ro, team='Outside', pay_type='Invoice', phone=fake_phone(108 + i), email=fake_email(b), hours_week=0, share_pct=0, hourly_rate=0.0, bonus_pct=0,
                 guarantee=0.0, station='', speciality=sp, country=c, start=ago(2100 - 200 * i)) for i, (a, b, c, ro, sp) in enumerate(_ctc)]
team = staff + contacts
staff_by_name = {s['name']: s for s in team}
GROOMERS = [s['name'] for s in staff[:5]]
STAFF_NAMES = [s['name'] for s in staff]
PAID_STAFF = STAFF_NAMES[1:]
BATHERS = ['Ana Popescu', 'Kwame Mensah']
CONTRACTORS = [s['name'] for s in staff if s['pay_type'] == 'Commission']
VAN_GROOMER = 'Lucia Ferreira'
STORY_GROOMER = 'Chidi Adeyemi'

# services: base price by size band this year, groom minutes by size band
_BASE = {'Full groom': [72, 95, 122, 155], 'Bath and brush': [45, 58, 76, 100], 'Bath and tidy': [56, 72, 95, 122], 'De-shedding': [67, 87, 112, 143], 'Hand-strip': [95, 122, 157, 196],
         'Puppy intro': [38, 45, 54, 65], 'Cat groom': [78, 95, 112, 134], 'Nail trim': [15, 16, 19, 22]}
_MIN = {'Full groom': [60, 80, 100, 130], 'Bath and brush': [40, 55, 70, 90], 'Bath and tidy': [50, 65, 80, 105], 'De-shedding': [60, 75, 95, 120], 'Hand-strip': [90, 115, 140, 170],
        'Puppy intro': [35, 45, 55, 70], 'Cat groom': [60, 70, 80, 90], 'Nail trim': [15, 15, 15, 20]}
_COAT = {'Short coat': (0.90, 0.85), 'Double coat': (1.10, 1.15), 'Curly coat': (1.15, 1.15), 'Wire coat': (1.10, 1.10), 'Long silky coat': (1.05, 1.05)}   # price factor, time factor
_KIND_OF = {'Full groom': 'Groom', 'Bath and brush': 'Bath', 'Bath and tidy': 'Bath', 'De-shedding': 'Bath', 'Hand-strip': 'Groom', 'Puppy intro': 'Groom', 'Cat groom': 'Cat', 'Nail trim': 'Small'}
services = [dict(service_id='SV-%02d' % (i + 1), service=s, minutes=_MIN[s][1], price=float(_BASE[s][1]), kind=_KIND_OF[s]) for i, s in enumerate(SERVICES)]
SV = {s['service']: s for s in services}
price_list = [dict(price_id='PL-%02d' % (i * 4 + j + 1), service=s, size=z, price=float(_BASE[s][j]), minutes=_MIN[s][j]) for i, s in enumerate(SERVICES) for j, z in enumerate(SIZES)]
coats = [dict(coat=c, price_factor=v[0], time_factor=v[1]) for c, v in _COAT.items()]
_ADD = [('Teeth brushing', 8, 5, 0.6), ('Ear cleaning', 8, 5, 0.5), ('Nail grind', 9, 8, 0.3), ('Face, feet and tail tidy', 12, 10, 0.2), ('Sanitary trim', 10, 8, 0.2),
        ('Conditioning treatment', 14, 10, 1.8), ('Paw balm', 7, 4, 0.9), ('Bow or bandana', 4, 2, 0.5)]
addons = [dict(addon_id='AD-%02d' % (i + 1), addon=a, price=float(p), minutes=m, cost=c) for i, (a, p, m, c) in enumerate(_ADD)]
AD = {a['addon']: a for a in addons}
_SUR = [('Matting', 'per 10 minutes', 12.0), ('Heavy matting', 'per 10 minutes', 18.0), ('Handling fee', 'per groom', 15.0), ('Extra time', 'per groom', 10.0), ('Late pick-up', 'per 15 minutes', 8.0),
        ('Travel fee', 'per van visit', 8.0)]
surcharges = [dict(surcharge_id='SU-%02d' % (i + 1), surcharge=a, unit=u, amount=p) for i, (a, u, p) in enumerate(_SUR)]
MAT_RATE = 12.0
HANDLING_FEE = 15.0
areas = [dict(area=a, van_weekday=w, miles_round=m, travel_fee=f) for a, w, m, f in
         [('Northgate', 'Tuesday', 22, 0.0), ('Hillcrest', 'Tuesday', 30, 8.0), ('Riverside', 'Wednesday', 18, 0.0), ('Lakeside', 'Wednesday', 34, 8.0), ('Old Town', 'Thursday', 14, 0.0),
         ('Eastfield', 'Friday', 40, 8.0)]]
AREA = {a['area']: a for a in areas}
stations = [dict(station=s, kind='Van' if s == 'Van' else 'Grooming table', owner=[x['name'] for x in staff if x['station'] == s][0]) for s in STATIONS]
vans = [dict(van_id='VN-01', van='Willowbrook van', groomer=VAN_GROOMER, tank_litres=200, bought=ago(900), loan_month=650.0, insurance_month=210.0)]

# breeds: generic words, size band, coat type, species, weight
_BR = [('Toy poodle type', 'Small', 'Curly coat', 'Dog', 5), ('Small terrier mix', 'Small', 'Wire coat', 'Dog', 5), ('Small spaniel type', 'Small', 'Long silky coat', 'Dog', 5),
       ('Small long-haired companion dog', 'Small', 'Long silky coat', 'Dog', 5), ('Small short-coated dog', 'Small', 'Short coat', 'Dog', 4), ('Small doodle cross', 'Small', 'Curly coat', 'Dog', 5),
       ('Medium doodle cross', 'Medium', 'Curly coat', 'Dog', 8), ('Medium spaniel type', 'Medium', 'Long silky coat', 'Dog', 5), ('Medium herding dog', 'Medium', 'Double coat', 'Dog', 5),
       ('Medium wire-haired terrier', 'Medium', 'Wire coat', 'Dog', 3), ('Medium short-coated dog', 'Medium', 'Short coat', 'Dog', 5), ('Large doodle cross', 'Large', 'Curly coat', 'Dog', 6),
       ('Large retriever type', 'Large', 'Double coat', 'Dog', 6), ('Large shepherd type', 'Large', 'Double coat', 'Dog', 4), ('Large short-coated dog', 'Large', 'Short coat', 'Dog', 3),
       ('Large poodle type', 'Large', 'Curly coat', 'Dog', 2), ('Giant mountain dog', 'Giant', 'Double coat', 'Dog', 2), ('Giant curly water dog', 'Giant', 'Curly coat', 'Dog', 1.5),
       ('Giant short-coated dog', 'Giant', 'Short coat', 'Dog', 1.5), ('Short-haired cat', 'Small', 'Short coat', 'Cat', 5), ('Long-haired cat', 'Small', 'Long silky coat', 'Cat', 5)]
breeds = [dict(breed=b, size=z, coat=c, species=sp) for b, z, c, sp, w in _BR]
BREED = {b['breed']: b for b in breeds}

# retail and back-bar
_RP = [('RT-01', 'Everyday shampoo bottle', 'Shampoo', 6.5, 14.0, 24, 10), ('RT-02', 'Sensitive shampoo bottle', 'Shampoo', 7.5, 16.0, 18, 8), ('RT-03', 'Leave-in conditioner', 'Conditioner', 5.5, 13.0, 20, 8),
       ('RT-04', 'Slicker brush', 'Brush or comb', 7.0, 18.0, 14, 6), ('RT-05', 'Metal comb', 'Brush or comb', 4.0, 11.0, 16, 6), ('RT-06', 'Dental chew bag', 'Treats', 3.5, 9.0, 40, 15),
       ('RT-07', 'Training treat bag', 'Treats', 2.8, 7.0, 55, 20), ('RT-08', 'Paw balm tin', 'Paw balm', 4.5, 12.0, 22, 8), ('RT-09', 'Padded collar', 'Collar or lead', 8.0, 21.0, 12, 5),
       ('RT-10', 'Everyday lead', 'Collar or lead', 6.0, 16.0, 15, 6), ('RT-11', 'Cotton bandana', 'Bandana', 1.5, 6.0, 30, 10), ('RT-12', 'Rope toy', 'Toy', 2.2, 8.0, 3, 8),
       ('RT-13', 'Squeaky toy', 'Toy', 2.0, 7.5, 28, 10), ('RT-14', 'Cat brush', 'Brush or comb', 5.0, 13.0, 9, 4)]
retail_products = [dict(product_id=a, product=b, kind=c, cost=co, price=p, stock=s, reorder_point=rp) for a, b, c, co, p, s, rp in _RP]
RP = {x['product']: x for x in retail_products}
_BB = [('BB-01', 'Shampoo', 'litre', 7.5, 20, 6), ('BB-02', 'Conditioner', 'litre', 9.0, 15, 5), ('BB-03', 'Coat spray', 'bottle', 6.0, 16, 6), ('BB-04', 'Ear wipes', 'pack', 4.5, 12, 4),
       ('BB-05', 'Blade coolant', 'can', 5.5, 8, 3), ('BB-06', 'Towels and laundry', 'load', 4.0, 0, 0), ('BB-07', 'Cotton and wipes', 'pack', 3.2, 10, 4), ('BB-08', 'Paw balm tub', 'tub', 6.0, 6, 3),
       ('BB-09', 'Cleaning solution', 'litre', 3.0, 12, 5), ('BB-10', 'Disposable aprons', 'box', 8.5, 5, 2)]
backbar_products = [dict(backbar_id=a, product=b, unit=u, cost_per_unit=c, stock=s, reorder_point=rp) for a, b, u, c, s, rp in _BB]

# equipment: id, item, kind, location, bought days ago, cost, service every days, last service days ago, replacement cost, life years
_EQ = []
for i in range(1, 7): _EQ.append(('Clipper %d' % i, 'Clipper', 'Salon' if i < 6 else 'Van', 1500 - 150 * i, 290.0, 120, 70 + 12 * i, 340.0, 4))
for i, nm in enumerate(['Blade set 10', 'Blade set 7F', 'Blade set 5F', 'Blade set 4F', 'Blade set 30', 'Blade set 15', 'Blade set 3F', 'Blade set 9', 'Blade set 40', 'Blade set A', 'Blade set B', 'Blade set C']):
    _EQ.append((nm, 'Blade set', 'Salon' if i < 9 else 'Van', 400 - 22 * i, 48.0 + i, 60, 20 + 4 * i, 55.0 + i, 2))
for i in range(1, 5): _EQ.append(('High-velocity dryer %d' % i, 'Dryer', 'Salon' if i < 4 else 'Van', 1300 - 200 * i, 620.0, 180, 60 + 25 * i, 690.0, 6))
for i in range(1, 4): _EQ.append(('Tub %d' % i, 'Tub', 'Salon' if i < 3 else 'Van', 2000 - 300 * i, 1450.0, 365, 90 + 40 * i, 1600.0, 10))
for i in range(1, 6): _EQ.append(('Grooming table %d' % i, 'Grooming table', 'Salon' if i < 5 else 'Van', 1800 - 150 * i, 380.0, 365, 100 + 30 * i, 420.0, 8))
_EQ += [('Van water pump', 'Van equipment', 'Van', 700, 160.0, 180, 80, 180.0, 5), ('Van generator', 'Van equipment', 'Van', 880, 1250.0, 180, 120, 1400.0, 8), ('Grooming van', 'Van equipment', 'Van', 900, 38000.0, 180, 70, 38000.0, 10)]


def _eq_rows():
    out = []
    for i, (nm, kind, loc, bought, cost, every, last, repl, life) in enumerate(_EQ, 1):
        out.append(dict(equipment_id='EQ-%03d' % i, item=nm, kind=kind, location=loc, bought_on=ago(bought), cost=cost, service_every_days=every, last_service=ago(last),
                        next_service=iso(TODAY - day(last) + day(every)), replacement_cost=repl, life_years=life))
    return out


equipment = _eq_rows()
# story equipment: Clipper 3 is 24 days past its service date; the van is due in 6 days
for _e in equipment:
    if _e['item'] == 'Clipper 3': _e['last_service'] = ago(144); _e['next_service'] = ahead(-24)
    if _e['item'] == 'Grooming van': _e['last_service'] = ago(174); _e['next_service'] = ahead(6)
    if _e['item'] == 'Clipper 2' or _e['item'] == 'Blade set 7F': _e['last_service'] = ago(50); _e['next_service'] = iso(to_date(_e['last_service']) + day(_e['service_every_days']))
    if _e['next_service'] < ago(0) and _e['item'] not in ('Clipper 3',): _e['last_service'] = ago(40); _e['next_service'] = iso(to_date(_e['last_service']) + day(_e['service_every_days']))
for _e in equipment: _e['uses_since_service'] = max(5, (TODAY - to_date(_e['last_service'])).days * 2)

_G = [(['Ana', 'Rui', 'Marta', 'Tiago', 'Ines', 'Diogo', 'Sara', 'Nuno', 'Joana', 'Pedro'], ['Silva', 'Pereira', 'Costa', 'Ribeiro', 'Almeida', 'Moreira', 'Gomes', 'Lopes', 'Martins', 'Fonseca']),
      (['Jonas', 'Lena', 'Felix', 'Mira', 'Leon', 'Hanna', 'Emil', 'Nele', 'Paul', 'Greta'], ['Hoffmann', 'Schulz', 'Keller', 'Vogel', 'Brandt', 'Lorenz', 'Fuchs', 'Krause', 'Richter', 'Wolf']),
      (['Oliver', 'Ella', 'Harvey', 'Isla', 'Noah', 'Freya', 'Alfie', 'Poppy', 'George', 'Amelia'], ['Turner', 'Hughes', 'Walsh', 'Barker', 'Ellis', 'Pearce', 'Dawson', 'Fisher', 'Hale', 'Marsh']),
      (['Jordan', 'Taylor', 'Riley', 'Morgan', 'Casey', 'Avery', 'Quinn', 'Rowan', 'Jamie', 'Skyler'], ['Bennett', 'Carter', 'Brooks', 'Hayes', 'Foster', 'Reed', 'Gray', 'Webb', 'Sullivan', 'Nolan']),
      (['Camille', 'Louis', 'Chloe', 'Hugo', 'Manon', 'Theo', 'Lea', 'Jules', 'Elise', 'Arthur'], ['Laurent', 'Girard', 'Roux', 'Fournier', 'Mercier', 'Blanc', 'Dupont', 'Chevalier', 'Faure', 'Perrin']),
      (['Lucia', 'Pablo', 'Carmen', 'Hector', 'Elena', 'Alvaro', 'Noa', 'Iker', 'Irene', 'Sergio'], ['Ortega', 'Molina', 'Castro', 'Herrera', 'Vidal', 'Prieto', 'Cano', 'Romero', 'Delgado', 'Pascual']),
      (['Daan', 'Sanne', 'Bram', 'Fenna', 'Lars', 'Anouk', 'Joris', 'Femke', 'Ruben', 'Lotte'], ['de Vries', 'Smit', 'Bos', 'Mulder', 'Dekker', 'Peters', 'Hendriks', 'Jansen', 'Vos', 'Bakker']),
      (['Gabriel', 'Beatriz', 'Caio', 'Larissa', 'Thiago', 'Julia', 'Enzo', 'Livia', 'Rafael', 'Bianca'], ['Souza', 'Lima', 'Araujo', 'Barbosa', 'Cardoso', 'Nunes', 'Freitas', 'Campos', 'Monteiro', 'Pinto']),
      (['Kasia', 'Piotr', 'Zofia', 'Jakub', 'Ola', 'Antoni', 'Wiktoria', 'Michal', 'Hania', 'Tomek'], ['Kowal', 'Wisniewski', 'Zielinski', 'Lewandowski', 'Mazur', 'Kaczmarek', 'Pawlak', 'Wrona', 'Sikora', 'Baran']),
      (['Aarav', 'Diya', 'Kabir', 'Tara', 'Rohan', 'Isha', 'Vihaan', 'Neha', 'Ishaan', 'Kavya'], ['Sharma', 'Nair', 'Kapoor', 'Mehta', 'Joshi', 'Bose', 'Pillai', 'Gupta', 'Desai', 'Reddy']),
      (['Chidi', 'Ngozi', 'Tunde', 'Ada', 'Emeka', 'Yetunde', 'Kelechi', 'Bisi', 'Obinna', 'Ife'], ['Adebayo', 'Okafor', 'Balogun', 'Nwosu', 'Ogunleye', 'Afolabi', 'Chukwu', 'Onyeka', 'Ibe', 'Okoro']),
      (['Diego', 'Valeria', 'Mateo', 'Ximena', 'Santiago', 'Regina', 'Emilio', 'Renata', 'Luis', 'Camila'], ['Hernandez', 'Garcia', 'Ramirez', 'Torres', 'Flores', 'Vargas', 'Mendoza', 'Cruz', 'Ortiz', 'Aguilar']),
      (['Emre', 'Elif', 'Can', 'Defne', 'Mert', 'Ece', 'Baris', 'Selin', 'Deniz', 'Ayla'], ['Yilmaz', 'Sahin', 'Celik', 'Aydin', 'Ozturk', 'Arslan', 'Dogan', 'Kilic', 'Polat', 'Aksoy']),
      (['Hao', 'Mei', 'Jian', 'Xin', 'Yu', 'Lan', 'Tao', 'Ying', 'Bo', 'Rui'], ['Wang', 'Li', 'Liu', 'Yang', 'Huang', 'Zhou', 'Wu', 'Xu', 'Sun', 'Ma']),
      (['Minjun', 'Seoyeon', 'Jiho', 'Hayun', 'Doyun', 'Jiwoo', 'Siwoo', 'Yuna', 'Hyunwoo', 'Sora'], ['Kim', 'Lee', 'Choi', 'Jung', 'Kang', 'Cho', 'Yoon', 'Jang', 'Lim', 'Han']),
      (['Mia', 'Lachlan', 'Zara', 'Hamish', 'Sienna', 'Declan', 'Matilda', 'Archer', 'Ivy', 'Cooper'], ['Murray', 'Fraser', 'Hart', 'Doyle', 'Sutton', 'Blake', 'Lowe', 'Pratt', 'Burke', 'Quinlan']),
      (['Jose', 'Maria', 'Paolo', 'Andrea', 'Miguel', 'Bea', 'Carlo', 'Kristine', 'Marco', 'Jasmine'], ['Santos', 'Reyes', 'Bautista', 'Aquino', 'Villanueva', 'Ramos', 'Castillo', 'Dizon', 'Navarro', 'Soriano']),
      (['Youssef', 'Salma', 'Omar', 'Nour', 'Karim', 'Lina', 'Adam', 'Yasmin', 'Rami', 'Hana'], ['Mansour', 'Nasser', 'Farah', 'Saleh', 'Aziz', 'Karam', 'Rahman', 'Habib', 'Sabbagh', 'Toumi'])]
_PETS = ['Biscuit', 'Luna', 'Max', 'Bella', 'Charlie', 'Daisy', 'Milo', 'Poppy', 'Teddy', 'Ruby', 'Oscar', 'Coco', 'Rocky', 'Willow', 'Buddy', 'Lola', 'Finn', 'Millie', 'Archie', 'Rosie',
         'Bear', 'Pepper', 'Ziggy', 'Honey', 'Murphy', 'Penny', 'Louie', 'Maple', 'Jasper', 'Nala', 'Hazel', 'Toby', 'Olive', 'Gizmo', 'Sadie', 'Otis', 'Pixie', 'Walnut', 'Mochi', 'Ginger',
         'Rex', 'Cleo', 'Basil', 'Misty', 'Tank', 'Peanut', 'Juno', 'Waffles', 'Scout', 'Biscotti', 'Fig', 'Nugget', 'Koda', 'Pumpkin', 'Sunny', 'Remy', 'Clover', 'Bruno', 'Daphne', 'Pip']
_AREA_W = [4, 3, 3, 3, 2, 2]

# ------------------------------------------------------------------ world
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
def _wchoice(r, vals, ws):
    x, acc = r.random() * sum(ws), 0
    for v, w in zip(vals, ws):
        acc += w
        if x <= acc: return v
    return vals[-1]


def _price(service, size, coat, d):
    p = _BASE[service][SIZES.index(size)] * (_COAT[coat][0] if service != 'Nail trim' else 1.0)
    if to_date(d) < D(TODAY.year, 1, 1): p = p / 1.05
    return float(int(round(p / PRICE_STEP)) * PRICE_STEP)


def _minutes(service, size, coat): return int(round(_MIN[service][SIZES.index(size)] * (_COAT[coat][1] if service != 'Nail trim' else 1.0) / 5.0) * 5)


_SEASON_SKIP = {1: 0.28, 2: 0.22, 3: 0.08, 4: 0.04, 5: 0.04, 6: 0.05, 7: 0.07, 8: 0.1, 9: 0.05, 10: 0.05, 11: 0.03, 12: 0.04}
_GROOMER_W = {'Rosa Delgado': 0.24, 'Tomas Eriksen': 0.25, 'Mei Tanaka': 0.25, 'Chidi Adeyemi': 0.12, 'Lucia Ferreira': 0.20}
_WORKS = {'Rosa Delgado': (1, 2, 3, 4, 5), 'Tomas Eriksen': (0, 1, 2, 3, 4), 'Mei Tanaka': (1, 2, 3, 4, 5), 'Chidi Adeyemi': (0, 2, 4), 'Lucia Ferreira': (1, 2, 3, 4)}
_SCOMM = {'Tomas Eriksen': 0.50, 'Chidi Adeyemi': 0.60, 'Lucia Ferreira': 0.50}
_REBOOK_P = {'Rosa Delgado': 0.78, 'Tomas Eriksen': 0.74, 'Mei Tanaka': 0.66, 'Chidi Adeyemi': 0.46, 'Lucia Ferreira': 0.62}


def _world():
    r = rng('world')
    n_clients = 830
    clients, pets = [], []
    used = set()
    for ci in range(1, n_clients + 1):
        fs, ls = _G[r.randrange(len(_G))]
        while True:
            nm = r.choice(fs) + ' ' + r.choice(ls)
            if nm not in used: used.add(nm); break
        area = _wchoice(r, AREAS, _AREA_W)
        clients.append(dict(client_id='CL-%04d' % ci, client=nm, area=area, source=_wchoice(r, SOURCES, [26, 22, 14, 10, 9, 7, 5, 7]), pets=[]))
        npets = _wchoice(r, [1, 2, 3], [86, 12, 2])
        for k in range(npets):
            pi = len(pets) + 1
            br = _BR[_wchoice(r, list(range(len(_BR))), [b[4] for b in _BR])]
            mobile = (r.random() < 0.15)
            grm = VAN_GROOMER if mobile else _wchoice(r, GROOMERS[:4], [_GROOMER_W[g] for g in GROOMERS[:4]])
            if br[3] == 'Cat' and not mobile: grm = _wchoice(r, ['Mei Tanaka', 'Rosa Delgado', 'Tomas Eriksen'], [5, 2, 2])
            if br[2] == 'Wire coat' and not mobile: grm = _wchoice(r, ['Rosa Delgado', 'Tomas Eriksen'], [3, 1])
            if mobile and clients[-1]['area'] not in AREA: pass
            interval = _wchoice(r, [4, 5, 6, 8], [20, 12, 40, 28]) if br[3] == 'Dog' else _wchoice(r, [8, 10], [60, 40])
            if br[2] == 'Short coat' and br[3] == 'Dog': interval = _wchoice(r, [6, 8, 10], [30, 50, 20])
            pref = 'Cat groom' if br[3] == 'Cat' else (_wchoice(r, ['Full groom', 'Bath and brush', 'Bath and tidy', 'De-shedding'], [52, 22, 14, 12]) if br[2] != 'Wire coat'
                                                         else _wchoice(r, ['Hand-strip', 'Full groom', 'Bath and tidy'], [50, 30, 20]))
            if br[2] == 'Short coat' and br[3] == 'Dog': pref = _wchoice(r, ['Bath and brush', 'De-shedding', 'Bath and tidy'], [50, 35, 15])
            temp = _wchoice(r, TEMPERAMENTS, [48, 9, 9, 7, 7, 6, 6, 8])
            pet = dict(pet_id='PT-%04d' % pi, pet=r.choice(_PETS), client_id=clients[-1]['client_id'], client=nm, species=br[3], breed=br[0], size=br[1], coat=br[2], groomer=grm,
                       mobile=mobile, interval_weeks=interval, service=pref, temperament=temp, area=area, puppy=(br[3] == 'Dog' and br[1] in ('Small', 'Medium') and r.random() < 0.09),
                       ph=r.random())
            pets.append(pet); clients[-1]['pets'].append(pet)
    # mobile clients live in a van area (all areas are on the route)
    # start dates
    hs = HISTORY_START
    for p in pets:
        u = r.random()
        if u < 0.47: p['start'] = hs - day(r.randint(0, 140)) + day(r.randint(0, 40))
        else:
            t = r.random() ** 0.85
            p['start'] = hs + day(int(t * (HISTORY_DAYS - 12)))
    new_recent = 0
    for p in pets[::13]: p['start'] = TODAY - day(r.randint(2, 26)); new_recent += 1       # new pets in the last 4 weeks
    # lapse
    for p in pets:
        p['end'] = None
        if r.random() < 0.20:
            lo = hs + day(40); hi = TODAY - day(int(LAPSE_FACTOR * p['interval_weeks'] * 7) + 14 + r.randint(0, 50))
            if hi > p['start'] + day(60): p['end'] = p['start'] + day(r.randint(60, max(61, (hi - p['start']).days)))
    # story: regular 6-week client who left without rebooking, last visit ~105 days ago
    sp = [p for p in pets if p['species'] == 'Dog' and p['size'] in ('Medium', 'Large') and p['service'] == 'Full groom' and p['groomer'] == 'Tomas Eriksen'
          and not p['mobile']][3]
    sp['interval_weeks'] = 6; sp['start'] = hs + day(10); sp['end'] = TODAY - day(105); sp['story'] = 'lapsed'
    # visits
    visits = []
    for p in pets:
        d = p['start']; k = 0
        rr = rng('vis' + p['pet_id'])
        while d <= TODAY + day(21):
            if p['end'] and d > p['end']: break
            past = d <= TODAY
            skip = rr.random() < _SEASON_SKIP[d.month] and k > 0
            if past and not skip:
                visits.append(dict(pet=p, date=d, first=(k == 0), kind='regular'))
            elif not past and rr.random() < 0.62 and not skip:
                visits.append(dict(pet=p, date=d, first=(k == 0), kind='regular'))
            k += 1
            gap = p['interval_weeks'] * 7 + rr.randint(-3, 6)
            if rr.random() < 0.10: gap += rr.choice([7, 10, 14])
            d = d + day(gap)
        # peak extras: before the year-end holidays and shedding season
        for y in range(HISTORY_START.year, TODAY.year + 1):
            if rr.random() < 0.15:
                dd = D(y, 12, 1) + day(rr.randint(0, 19))
                if p['start'] < dd - day(30) and dd <= TODAY and not (p['end'] and dd > p['end']): visits.append(dict(pet=p, date=dd, first=False, kind='peak'))
            if rr.random() < 0.07:
                dd = D(y, 5, 1) + day(rr.randint(0, 40))
                if p['start'] < dd - day(30) and dd <= TODAY and not (p['end'] and dd > p['end']): visits.append(dict(pet=p, date=dd, first=False, kind='shed'))
    # walk-in nail trims: about 11 a week
    active = [p for p in pets if not p['mobile']]
    for w in range(0, HISTORY_DAYS // 7 + 1):
        base = hs + day(7 * w)
        for _ in range(r.choice([8, 10, 11, 12, 13, 14])):
            dd = base + day(r.randint(0, 5))
            if dd > TODAY: continue
            p = r.choice(active)
            if p['start'] < dd and not (p['end'] and dd > p['end']): visits.append(dict(pet=p, date=dd, first=False, kind='walkin'))
    visits.sort(key=lambda v: (v['date'], v['pet']['pet_id']))
    return dict(clients=clients, pets=pets, visits=visits)


_VAN_DAY = {'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4}


def _schedule(W):
    """assign groomer day, time, station, prices, status; returns appointment dicts"""
    r = rng('sched')
    load = {}; seen_first = {}; ap = []
    visits = W['visits']
    mob_day = {}
    for p in W['pets']:
        if p['mobile']: mob_day[p['pet_id']] = _VAN_DAY[AREA[p['area']]['van_weekday']]
    for v in visits:
        p = v['pet']; d = v['date']; g = p['groomer']
        service = p['service']
        if v['kind'] == 'walkin': service = 'Nail trim'
        elif v['first'] and p['puppy']: service = 'Puppy intro'
        elif v['kind'] == 'shed' and p['species'] == 'Dog': service = 'De-shedding'
        elif v['kind'] == 'peak' and p['species'] == 'Dog' and service == 'Bath and brush': service = 'Full groom'
        mins = _minutes(service, p['size'], p['coat'])
        gs = [g]
        if v['kind'] == 'walkin' or (not p['mobile'] and g == 'Chidi Adeyemi' and r.random() < 0.0): gs = ['Tomas Eriksen', 'Mei Tanaka', 'Rosa Delgado', 'Chidi Adeyemi']
        placed = None
        for off in range(0, 40):
            dd = d + day(off)
            if dd.weekday() == 6: continue
            for gg in gs:
                if p['mobile'] and v['kind'] != 'walkin':
                    if dd.weekday() != mob_day[p['pet_id']]: continue
                elif dd.weekday() not in _WORKS[gg] and v['kind'] != 'walkin': continue
                elif v['kind'] == 'walkin' and dd.weekday() not in _WORKS[gg]: continue
                cap = 400 if gg == VAN_GROOMER else DAY_MINUTES
                used = load.get((dd, gg), 0)
                if used + mins <= cap or (v['kind'] == 'walkin' and used + mins <= cap + 60):
                    placed = (dd, gg, used); break
            if placed: break
        if not placed:
            dd = d
            while dd.weekday() == 6 or (p['mobile'] and v['kind'] != 'walkin' and dd.weekday() != mob_day[p['pet_id']]) or (not p['mobile'] and dd.weekday() not in _WORKS[g]): dd = dd + day(1)
            placed = (dd, g, load.get((dd, g), 0))
        dd, gg, used = placed
        if gg == VAN_GROOMER and v['kind'] == 'walkin': gg = 'Tomas Eriksen'; used = load.get((dd, gg), 0)
        load[(dd, gg)] = used + mins + 5
        start = 8 * 60 + 30 + int(round(used / 15.0)) * 15
        if gg == VAN_GROOMER: start = 8 * 60 + 15 + int(round(used / 15.0)) * 15
        start = min(start, 16 * 60 + 30)
        if dd > TODAY + day(21): continue
        ap.append(dict(v=v, pet=p, date=dd, groomer=gg, service=service, start=start, minutes=mins))
    return ap


def _build():
    W = _raw('world', _world)
    r = rng('build')
    sched = _schedule(W)
    pets_by = {p['pet_id']: p for p in W['pets']}
    out = []
    first_seen = {}
    for a in sched:
        p = a['pet']
        a['_i'] = len(out)
        out.append(a)
    out.sort(key=lambda a: (a['date'], a['start'], a['pet']['pet_id']))
    rows = []
    first_by_pet = {}
    for i, a in enumerate(out, 1):
        p = a['pet']; d = a['date']; v = a['v']
        newc = a['pet']['pet_id'] not in first_by_pet
        first_by_pet.setdefault(p['pet_id'], a)
        first_client = None
        rr = rng('ap' + str(i))
        service = a['service']; mins = a['minutes']
        base = _price(service, p['size'], p['coat'], d)
        # status
        if d > TODAY: status = 'Scheduled'
        else:
            u = rr.random(); pn = 0.07 if newc else 0.025
            status = 'Completed'
            if u < pn: status = 'No-show'
            elif u < pn + 0.025: status = 'Late cancel'
            elif u < pn + 0.06: status = 'Cancelled'
            if v['kind'] == 'walkin': status = 'Completed' if rr.random() < 0.985 else 'Cancelled'
        # add-ons, surcharges
        done = status == 'Completed'
        add_names = []; add_price = 0.0; add_cost = 0.0; add_min = 0
        if service not in ('Nail trim', 'Puppy intro') and (done or status == 'Scheduled') and rr.random() < 0.60:
            for ad in rr.sample(ADDON_NAMES, 1 if rr.random() < 0.65 else 2):
                add_names.append(ad); add_price += AD[ad]['price']; add_cost += AD[ad]['cost']; add_min += AD[ad]['minutes']
        mat_min = 0
        if service in ('Full groom', 'Bath and tidy', 'De-shedding', 'Cat groom') and p['coat'] in ('Curly coat', 'Double coat', 'Long silky coat') and rr.random() < 0.20 and status != 'Cancelled':
            mat_min = rr.choice([10, 10, 20, 20, 30, 40])
        mat_due = R2(MAT_RATE * mat_min / 10.0)
        mat_charged = mat_due if rr.random() < 0.64 else 0.0
        hand_due = HANDLING_FEE if (p['temperament'] in ('Barks at clippers', 'Needs two people for nails', 'Wriggly on the table') and rr.random() < 0.7) else 0.0
        hand_charged = hand_due if rr.random() < 0.70 else 0.0
        travel = AREA[p['area']]['travel_fee'] if p['mobile'] else 0.0
        if p['mobile'] and v['kind'] == 'walkin': travel = 0.0
        disc = R2(0.1 * (base + add_price)) if rr.random() < 0.06 and done else 0.0
        mins_w = int(round((mins + add_min + mat_min * 1.0) * (0.88 + 0.35 * rr.random()) / 5.0) * 5)
        if status in ('Cancelled', 'Late cancel', 'No-show'): mins_w = 0
        if status == 'Scheduled': mins_w = 0
        price = R2(base + add_price + mat_charged + hand_charged + travel - disc) if done else 0.0
        fee_due = R2(base * LATE_FEE_PCT) if status in ('Late cancel', 'No-show') else 0.0
        fee_charged = fee_due if (fee_due and rr.random() < 0.52) else 0.0
        # deposit for a new client
        dep = 0.0; dep_status = ''
        if newc and v['kind'] != 'walkin':
            if rr.random() < 0.88:
                dep = DEPOSIT
                dep_status = 'Applied' if done else 'Kept' if status in ('No-show', 'Late cancel') else 'Refunded' if status == 'Cancelled' else 'Held'
            else: dep_status = 'Not collected'
        tip = 0.0
        if done and rr.random() < 0.46: tip = float(max(2, int(round(price * rr.choice([0.08, 0.1, 0.12, 0.15, 0.2]) / 1.0))))
        prod = R2([2.4, 3.6, 5.2, 7.4][SIZES.index(p['size'])] * (0.5 if service in ('Nail trim',) else 1.0) * (0.8 + 0.4 * rr.random()) + add_cost) if done else 0.0
        if service == 'Nail trim': prod = R2(0.4 + add_cost) if done else 0.0
        channel = 'Walk-in' if v['kind'] == 'walkin' else 'New client' if newc else _wchoice(rr, ['Rebooked at checkout', 'Standing appointment', 'Phone or message', 'Online booking'],
                                                                                          [_REBOOK_P[p['groomer']] * 100, 8, 14, 12])
        rebook = bool(done and v['kind'] != 'walkin' and rr.random() < _REBOOK_P[a['groomer']] and not (p['end'] and d >= p['end'] - day(3)))
        h, m = divmod(a['start'], 60)
        rows.append(dict(appt_id='AP-%05d' % i, date=iso(d), week=iso(week_start(d)), month=iso(_ms(d)), time='%02d:%02d' % (h, m), weekday=WEEKDAYS[d.weekday()], pet_id=p['pet_id'], pet=p['pet'],
                         client_id=p['client_id'], client=p['client'], species=p['species'], size=p['size'], coat=p['coat'], service=service, groomer=a['groomer'],
                         bather=BATHERS[(d.toordinal() + (1 if a['groomer'] in ('Chidi Adeyemi', 'Lucia Ferreira') else 0)) % 2] if service != 'Nail trim' else '',
                         station=staff_by_name[a['groomer']]['station'] if not (v['kind'] == 'walkin') else staff_by_name[a['groomer']]['station'], channel=channel, status=status,
                         booked_minutes=mins + add_min, worked_minutes=mins_w, base_price=base, addons=', '.join(add_names), addon_price=R2(add_price), matting_minutes=mat_min, matting_due=mat_due,
                         matting_charged=mat_charged if done else 0.0, handling_due=hand_due, handling_charged=hand_charged if done else 0.0, travel_fee=travel if done else 0.0, discount=disc,
                         price=price, fee_due=fee_due, fee_charged=fee_charged, deposit=dep, deposit_status=dep_status, tip=tip, product_cost=prod, first_visit=newc,
                         rebooked_at_checkout=rebook, mobile=p['mobile'], area=p['area'] if p['mobile'] else ''))
    return rows


def _apply_story(rows, W):
    r = rng('story')
    # no-show of a new client: fee not charged, deposit not collected
    cand = [x for x in rows if x['first_visit'] and x['date'] >= ago(24) and x['date'] <= ago(3) and not x['mobile']]
    ns = cand[0] if cand else [x for x in rows if x['first_visit'] and x['date'] <= ago(3)][-1]
    ns.update(status='No-show', worked_minutes=0, price=0.0, tip=0.0, product_cost=0.0, matting_charged=0.0, handling_charged=0.0, discount=0.0, travel_fee=0.0, addons='', addon_price=0.0,
              fee_due=R2(ns['base_price'] * LATE_FEE_PCT), fee_charged=0.0, deposit=0.0, deposit_status='Not collected', rebooked_at_checkout=False, matting_minutes=0, matting_due=0.0)
    # the pet booked next week with an expired vaccination record
    fut = [x for x in rows if x['status'] == 'Scheduled' and ago(-4) <= x['date'] <= ago(-8) or (x['status'] == 'Scheduled' and TODAY + day(3) <= to_date(x['date']) <= TODAY + day(8))]
    vp = fut[0]
    return dict(noshow=ns['appt_id'], noshow_client=ns['client'], noshow_client_id=ns['client_id'], noshow_pet=ns['pet'], noshow_fee=ns['fee_due'], vacc_pet_id=vp['pet_id'], vacc_appt=vp['appt_id'])


def _world_full():
    W = _raw('world', _world)
    rows = _build()
    st = _apply_story(rows, W)
    # first appointment of every pet to know new clients: done in _build. keep order
    return dict(W=W, rows=rows, story=st)


def _WF(): return _raw('wf', _world_full)
def _rows_raw(): return _WF()['rows']
def _pets_by(): return _raw('pets_by', lambda: {p['pet_id']: p for p in _WF()['W']['pets']})


def appointment_rows(n=None):
    def f(): return [dict(x) for x in _rows_raw()]
    return _thin(_cached('ap', f), n)


# ------------------------------------------------------------------ pets and clients
def _vacc(p):
    rr = rng('vac' + p['pet_id'])
    u = rr.random()
    lapsed = bool(p['end'] and p['end'] < TODAY - day(60))
    if lapsed: u = u * 0.7 + 0.3 if rr.random() < 0.6 else u
    exp = ahead(rr.randint(31, 330)) if u < 0.80 else ahead(rr.randint(1, 30)) if u < 0.93 else ago(rr.randint(1, 200))
    return exp


def _pet_vacc():
    def f():
        W = _WF()['W']; st = _WF()['story']; fut = {}
        for x in _rows_raw():
            if x['status'] == 'Scheduled' and to_date(x['date']) <= TODAY + day(8): fut[x['pet_id']] = x
        out = {}
        for p in W['pets']:
            e = _vacc(p)
            if p['pet_id'] in fut and e < iso(TODAY): e = ahead(rng('v2' + p['pet_id']).randint(5, 80))
            if p['pet_id'] == st['vacc_pet_id']: e = ago(9)
            out[p['pet_id']] = e
        return out
    return _raw('pvac', f)


def _vstatus(exp):
    e = to_date(exp)
    return 'Expired' if e < TODAY else 'Due soon' if e <= TODAY + day(30) else 'Current'


def pet_rows(n=None):
    def f():
        W = _WF()['W']; rows = _rows_raw(); vac = _pet_vacc(); agg = {}
        for x in rows:
            a = agg.setdefault(x['pet_id'], dict(last='', nxt='', visits=0, spent=0.0, noshows=0, lastprice=0.0))
            if x['status'] == 'Completed':
                a['visits'] += 1; a['spent'] += x['price']; a['last'] = x['date']; a['lastprice'] = x['price']
            if x['status'] in ('No-show', 'Late cancel'): a['noshows'] += 1
            if x['status'] == 'Scheduled' and not a['nxt']: a['nxt'] = x['date']
        out = []
        for p in W['pets']:
            a = agg.get(p['pet_id'], dict(last='', nxt='', visits=0, spent=0.0, noshows=0, lastprice=0.0)); e = vac[p['pet_id']]
            out.append(dict(pet_id=p['pet_id'], pet=p['pet'], client_id=p['client_id'], client=p['client'], species=p['species'], breed=p['breed'], size=p['size'], coat=p['coat'],
                            groomer=p['groomer'], temperament=p['temperament'], usual_service=p['service'], interval_weeks=p['interval_weeks'], vacc_record_date=iso(to_date(e) - day(365)),
                            vacc_valid_until=e, vacc_status=_vstatus(e), consent_signed_on=iso(max(HISTORY_START - day(200), p['start'] - day(rng('cs' + p['pet_id']).randint(0, 3)))),
                            mobile=p['mobile'], area=p['area'], first_visit=iso(p['start']), visits=a['visits'], last_visit=a['last'], next_visit=a['nxt'], last_price=a['lastprice'],
                            noshows=a['noshows'], total_spent=R2(a['spent'])))
        return out
    return _thin(_cached('pets', f), n)


def client_rows(n=None):
    def f():
        W = _WF()['W']; pets = {p['pet_id']: p for p in pet_rows()}; out = []
        for c in W['clients']:
            ps = [pets[p['pet_id']] for p in c['pets']]
            last = max((p['last_visit'] for p in ps if p['last_visit']), default=''); nxt = min((p['next_visit'] for p in ps if p['next_visit']), default='')
            iv = min(p['interval_weeks'] for p in ps)
            visits = sum(p['visits'] for p in ps)
            i = int(c['client_id'][3:])
            out.append(dict(client_id=c['client_id'], client=c['client'], phone=fake_phone(1000 + i), email=fake_email(c['client'], i % 7), area=c['area'], pets=len(ps),
                            pet_names=', '.join(p['pet'] for p in ps), source=c['source'], first_visit=min(p['first_visit'] for p in ps), visits=visits, last_visit=last, next_visit=nxt,
                            interval_weeks=iv, spent=R2(sum(p['total_spent'] for p in ps)), noshows=sum(p['noshows'] for p in ps),
                            strikes=min(STRIKES_MAX + 1, sum(1 for x in _rows_raw() if False)), card_on_file=(i % 5 != 0)))
        # strikes: count no-shows and late cancels in the last 180 days
        cut = ago(180); cnt = {}
        for x in _rows_raw():
            if x['status'] in ('No-show', 'Late cancel') and x['date'] >= cut: cnt[x['client_id']] = cnt.get(x['client_id'], 0) + 1
        for c in out: c['strikes'] = min(3, cnt.get(c['client_id'], 0))
        return out
    return _thin(_cached('clients', f), n)


# ------------------------------------------------------------------ appointment-derived tables
def noshow_rows(n=None):
    def f():
        out = []; cl = {c['client_id']: c for c in _WF()['W']['clients']}; k = 0; cnt = {}
        for x in _rows_raw():
            if x['status'] in ('Late cancel', 'No-show'):
                k += 1; cnt[x['client_id']] = cnt.get(x['client_id'], 0) + 1
                out.append(dict(noshow_id='NS-%04d' % k, date=x['date'], month=x['month'], weekday=x['weekday'], appt_id=x['appt_id'], client=x['client'], client_id=x['client_id'], pet=x['pet'],
                                kind=x['status'], new_client=x['first_visit'], groomer=x['groomer'], service=x['service'], base_price=x['base_price'], fee_due=x['fee_due'], fee_charged=x['fee_charged'],
                                deposit=x['deposit'], deposit_status=x['deposit_status'], strikes=cnt[x['client_id']], billed_on=iso(to_date(x['date']) + day(2)) if x['fee_charged'] else '',
                                slot_refilled=(k % 4 == 0)))
        return out
    return _thin(_cached('ns', f), n)


def deposit_rows(n=None):
    def f():
        out = []; k = 0
        for x in _rows_raw():
            if x['deposit_status']:
                k += 1
                out.append(dict(deposit_id='DP-%04d' % k, date=iso(to_date(x['date']) - day(rng('dp' + x['appt_id']).randint(2, 12))), appt_id=x['appt_id'], client=x['client'], client_id=x['client_id'],
                                pet=x['pet'], appt_date=x['date'], amount=x['deposit'] if x['deposit_status'] != 'Not collected' else DEPOSIT, status=x['deposit_status'],
                                applied_on=x['date'] if x['deposit_status'] == 'Applied' else '', kept_on=x['date'] if x['deposit_status'] == 'Kept' else '',
                                refunded_on=x['date'] if x['deposit_status'] == 'Refunded' else ''))
        for d in out:
            if d['date'] > iso(TODAY): d['date'] = iso(TODAY)
        return out
    return _thin(_cached('dep', f), n)


def payment_rows(n=None):
    def f():
        out = []; k = 0
        for x in _rows_raw():
            if x['status'] == 'Completed' or x['fee_charged']:
                k += 1; rr = rng('pm' + x['appt_id'])
                amt = x['price'] if x['status'] == 'Completed' else x['fee_charged']
                dep = x['deposit'] if x['deposit_status'] == 'Applied' else 0.0
                out.append(dict(payment_id='PM-%05d' % k, date=x['date'], month=x['month'], appt_id=x['appt_id'], client=x['client'], groomer=x['groomer'], method=_wchoice(rr, PAY_METHODS, [66, 24, 10]),
                                kind='Groom' if x['status'] == 'Completed' else 'No-show fee', amount=R2(amt - dep), deposit_applied=dep, tip=x['tip']))
        return out
    return _thin(_cached('paym', f), n)


def tip_rows(n=None):
    def f():
        out = []; k = 0
        for x in _rows_raw():
            if x['tip']:
                k += 1; rr = rng('tp' + x['appt_id'])
                out.append(dict(tip_id='TP-%05d' % k, date=x['date'], month=x['month'], appt_id=x['appt_id'], groomer=x['groomer'], client=x['client'], amount=x['tip'],
                                method='Cash' if rr.random() < 0.35 else 'Card', paid_out_on=iso(_eom(to_date(x['date'])) + day(10)) if to_date(x['date']) < _ms(TODAY) else ''))
        return out
    return _thin(_cached('tip', f), n)


def retail_sale_rows(n=None):
    def f():
        out = []; r = rng('retail'); k = 0; ap = [x for x in _rows_raw() if x['status'] == 'Completed']
        w = [3, 1, 2, 2, 1, 4, 5, 2, 1, 1, 1, 1, 2, 1]
        for x in ap:
            if r.random() < 0.095:
                for _ in range(1 if r.random() < 0.7 else 2):
                    p = retail_products[_wchoice(r, list(range(len(retail_products))), w)]; q = 1 if r.random() < 0.8 else 2; k += 1
                    out.append(dict(sale_id='RS-%05d' % k, date=x['date'], month=x['month'], appt_id=x['appt_id'], client=x['client'], product=p['product'], kind=p['kind'], qty=q,
                                    price=R2(p['price'] * q), cost=R2(p['cost'] * q), groomer=x['groomer']))
        return out
    return _thin(_cached('retail', f), n)


def backbar_use_rows(n=None):
    def f():
        out = []; k = 0; by = {}
        for x in _rows_raw():
            if x['status'] == 'Completed': by[x['week']] = by.get(x['week'], 0) + 1
        per = {'Shampoo': 0.045, 'Conditioner': 0.03, 'Coat spray': 0.06, 'Ear wipes': 0.04, 'Blade coolant': 0.012, 'Towels and laundry': 0.5, 'Cotton and wipes': 0.03, 'Paw balm tub': 0.008,
               'Cleaning solution': 0.03, 'Disposable aprons': 0.01}
        for w in sorted(by):
            if w > iso(TODAY): continue
            for b in backbar_products:
                rr = rng('bb' + w + b['product']); units = R2(by[w] * per[b['product']] * (0.85 + 0.3 * rr.random())); k += 1
                out.append(dict(use_id='BU-%04d' % k, week=w, month=iso(_ms(to_date(w))), product=b['product'], grooms=by[w], units=units, cost=R2(units * b['cost_per_unit'])))
        return out
    return _thin(_cached('bbu', f), n)


def daily_take_rows(n=None):
    def f():
        pm = {}; out = []; days = {}
        for p in payment_rows(): d = pm.setdefault(p['date'], dict(cash=0.0, card=0.0, bank=0.0, tips=0.0, dep=0.0))
        for p in payment_rows():
            d = pm[p['date']]; key = 'cash' if p['method'] == 'Cash' else 'card' if p['method'] == 'Card' else 'bank'
            d[key] += p['amount']; d['tips'] += p['tip']; d['dep'] += p['deposit_applied']
        rt = {}
        for s in retail_sale_rows(): rt[s['date']] = rt.get(s['date'], 0.0) + s['price']
        k = 0
        for dte in sorted(pm):
            d = pm[dte]; rr = rng('dt' + dte); k += 1
            exp = R2(d['cash'] + d['card'] + d['bank'] + rt.get(dte, 0.0))
            var = R2(rr.choice([0, 0, 0, 0, -2, 1.5, -4, 3, 0, 5]))
            out.append(dict(take_id='DT-%04d' % k, date=dte, month=iso(_ms(to_date(dte))), weekday=WEEKDAYS[to_date(dte).weekday()], cash=R2(d['cash'] + rt.get(dte, 0.0) * 0.3), card=R2(d['card'] + rt.get(dte, 0.0) * 0.7),
                            bank_transfer=R2(d['bank']), deposits_applied=R2(d['dep']), tips=R2(d['tips']), retail=R2(rt.get(dte, 0.0)), expected=exp, counted=R2(exp + var), closed_by=staff[7]['name']))
        return out
    return _thin(_cached('dtake', f), n)


# ------------------------------------------------------------------ van days
def _van_days():
    def f():
        days = {}
        for x in _rows_raw():
            if x['mobile'] and x['groomer'] == VAN_GROOMER:
                d = days.setdefault(x['date'], dict(grooms=0, rev=0.0, areas={}, mins=0, tips=0.0, prod=0.0))
                if x['status'] in ('Completed', 'Scheduled'): d['grooms'] += 1
                d['rev'] += x['price'] + x['fee_charged']; d['mins'] += x['worked_minutes']; d['tips'] += x['tip']; d['prod'] += x['product_cost']; d['areas'][x['area']] = d['areas'].get(x['area'], 0) + 1
        out = []; k = 0
        for dte in sorted(days):
            d = days[dte]; k += 1; rr = rng('vd' + dte); a = max(d['areas'], key=lambda z: d['areas'][z]); fut = to_date(dte) > TODAY
            miles = AREA[a]['miles_round'] + len(d['areas']) * 6 + rr.randint(0, 9)
            drive = int(miles * 2.1 + d['grooms'] * 6)
            gen = R2(d['mins'] / 60.0 * 0.85) if d['grooms'] else 0.0
            out.append(dict(van_day_id='VD-%04d' % k, date=dte, month=iso(_ms(to_date(dte))), weekday=WEEKDAYS[to_date(dte).weekday()], area=a, grooms=d['grooms'], miles=miles, drive_minutes=drive,
                            groom_minutes=d['mins'], generator_hours=gen, fuel_cost=R2(miles * FUEL_MILE), water_cost=WATER_DAY, wear_cost=R2(miles * WEAR_MILE), fixed_cost=VAN_FIXED_DAY,
                            revenue=R2(d['rev']), tips=R2(d['tips']), product_cost=R2(d['prod']), commission=R2(d['rev'] * _SCOMM[VAN_GROOMER]), scheduled=fut))
        # story: a recent route day with 2 grooms and a long drive
        cand = [x for x in out if not x['scheduled'] and ago(26) <= x['date'] <= ago(5)]
        s = cand[len(cand) // 2]
        s.update(area='Eastfield', grooms=2, miles=148, drive_minutes=330, groom_minutes=150, generator_hours=2.5, revenue=R2(min(s['revenue'], 185.0)) if s['revenue'] > 185 else s['revenue'])
        s['revenue'] = R2(min(s['revenue'], 190.0)); s['fuel_cost'] = R2(148 * FUEL_MILE); s['wear_cost'] = R2(148 * WEAR_MILE); s['commission'] = R2(s['revenue'] * 0.5)
        s['story'] = True
        cst = lambda x: x['fuel_cost'] + x['water_cost'] + x['wear_cost'] + x['fixed_cost'] + x['commission'] * (1 + EMPLOYER_COST_PCT) + x['product_cost'] + x['generator_hours'] * GEN_HOUR
        while s['revenue'] - cst(s) > -25: s['miles'] += 8; s['fuel_cost'] = R2(s['miles'] * FUEL_MILE); s['wear_cost'] = R2(s['miles'] * WEAR_MILE)
        s['drive_minutes'] = int(s['miles'] * 2.1 + 12)
        return out
    return _raw('vd', f)


def van_day_rows(n=None):
    def f():
        out = []
        for x in _van_days():
            x = dict(x); x.pop('story', None)
            c = x['fuel_cost'] + x['water_cost'] + x['wear_cost'] + x['fixed_cost'] + x['commission'] * (1 + EMPLOYER_COST_PCT) + x['product_cost'] + x['generator_hours'] * GEN_HOUR
            x['profit'] = R2(x['revenue'] - c)
            out.append(x)
        return out
    return _thin([dict(x) for x in f()], n)


# ------------------------------------------------------------------ groomer months, pay
def _gm():
    def f():
        agg = {}
        for x in _rows_raw():
            if x['status'] != 'Completed': continue
            a = agg.setdefault((x['month'], x['groomer']), dict(grooms=0, sales=0.0, mins=0, tips=0.0, prod=0.0, addon=0, surcharge=0.0, due=0.0))
            a['grooms'] += 1; a['sales'] += x['price']; a['mins'] += x['worked_minutes']; a['tips'] += x['tip']; a['prod'] += x['product_cost']; a['addon'] += 1 if x['addons'] else 0
            a['surcharge'] += x['matting_charged'] + x['handling_charged']; a['due'] += x['matting_due'] + x['handling_due']
        return agg
    return _raw('gmagg', f)


def _pay(person, month, sales):
    s = staff_by_name[person]; wk = 4.33
    if month == iso(_ms(TODAY)): wk = 4.33 * TODAY.day / float(calendar.monthrange(TODAY.year, TODAY.month)[1])
    if s['pay_type'] == 'Commission':
        base = R2(s['share_pct'] * sales); top = R2(max(0.0, s['guarantee'] - base)) if month != iso(_ms(TODAY)) else 0.0
        return base, top, 0.0
    if s['pay_type'] in ('Hourly plus bonus', 'Hourly'):
        base = R2(s['hourly_rate'] * s['hours_week'] * wk); bonus = R2(s['bonus_pct'] * max(0.0, sales - 7000.0)) if s['bonus_pct'] else 0.0
        return base, 0.0, bonus
    return 0.0, 0.0, 0.0


def groomer_month_rows(n=None):
    def f():
        agg = _gm(); out = []; k = 0
        for m in months24():
            for g in GROOMERS:
                a = agg.get((iso(m), g), dict(grooms=0, sales=0.0, mins=0, tips=0.0, prod=0.0, addon=0, surcharge=0.0, due=0.0))
                if g == VAN_GROOMER and False: pass
                k += 1; base, top, bonus = _pay(g, iso(m), a['sales']); pay = base + top + bonus
                if g == 'Rosa Delgado': pay = 0.0; top = 0.0
                oncost = R2(pay * EMPLOYER_COST_PCT)
                stn = STATION_COST_MONTH * ((TODAY.day / float(calendar.monthrange(TODAY.year, TODAY.month)[1])) if m == _ms(TODAY) else 1.0) if g != VAN_GROOMER else 0.0
                vcost = 0.0
                if g == VAN_GROOMER:
                    for v in van_day_rows():
                        if v['month'] == iso(m) and not v['scheduled']: vcost += v['fuel_cost'] + v['water_cost'] + v['wear_cost'] + v['fixed_cost'] + v['generator_hours'] * GEN_HOUR
                hours = R2(a['mins'] / 60.0)
                out.append(dict(row_id='GM-%04d' % k, month=iso(m), groomer=g, grooms=a['grooms'], sales=R2(a['sales']), worked_hours=hours, tips=R2(a['tips']), pay=R2(pay), top_up=R2(top), bonus=R2(bonus),
                                oncost=oncost, product_cost=R2(a['prod']), station_cost=R2(stn + vcost), with_addon=a['addon'], surcharges_charged=R2(a['surcharge']), surcharges_due=R2(a['due']),
                                profit=R2(a['sales'] - pay - oncost - a['prod'] - stn - vcost)))
        return out
    return _thin(_cached('gm', f), n)


def groomer_profit(name, months=3):
    ms = [iso(month_start(k)) for k in range(1, months + 1)]
    rows = [x for x in groomer_month_rows() if x['groomer'] == name and x['month'] in ms]
    return dict(sales=R2(sum(x['sales'] for x in rows)), profit=R2(sum(x['profit'] for x in rows)), grooms=sum(x['grooms'] for x in rows))


def pay_rows(n=None):
    def f():
        gm = {(x['month'], x['groomer']): x for x in groomer_month_rows()}; hs = _gm(); out = []; k = 0
        tipm = {}
        for x in _rows_raw():
            if x['status'] == 'Completed': tipm[(x['month'], x['groomer'])] = tipm.get((x['month'], x['groomer']), 0.0) + x['tip']
        for m in months24():
            for p in PAID_STAFF:
                s = staff_by_name[p]; k += 1
                if (iso(m), p) in gm: sales = gm[(iso(m), p)]['sales']
                else: sales = 0.0
                base, top, bonus = _pay(p, iso(m), sales)
                hours = R2(s['hours_week'] * 4.33)
                cur = (m == _ms(TODAY))
                due = _eom(m) + day(20)
                if s['pay_type'] == 'Commission': hours = R2(gm[(iso(m), p)]['worked_hours']) if (iso(m), p) in gm else 0.0
                out.append(dict(pay_id='PY-%03d' % k, month=iso(m), person=p, pay_type=s['pay_type'], grooms=gm[(iso(m), p)]['grooms'] if (iso(m), p) in gm else 0, hours=hours, sales=R2(sales),
                                share_pct=s['share_pct'], amount=R2(base + top + bonus), top_up=R2(top), bonus=R2(bonus), employer_cost=R2((base + top + bonus) * EMPLOYER_COST_PCT),
                                tips=R2(tipm.get((iso(m), p), 0.0)), paid_on='' if (cur or due > TODAY) else iso(due), status='Accruing' if cur else ('Due' if due > TODAY else 'Paid')))
        return out
    return _thin(_cached('pay', f), n)


def hours_rows(n=None):
    def f():
        out = []; k = 0
        for w in range(0, 104):
            wk = week_start(TODAY) - day(7 * (103 - w))
            if wk > TODAY: continue
            for p in ['Mei Tanaka', 'Ana Popescu', 'Kwame Mensah', 'Aisha Rahman']:
                rr = rng('hr' + p + iso(wk)); s = staff_by_name[p]; base = s['hours_week']; k += 1
                if iso(wk) < iso(to_date(s['start'])): continue
                hrs = R2(base + rr.choice([-4, -2, 0, 0, 0, 1, 2, 3])); ot = R2(max(0.0, hrs - base))
                out.append(dict(hours_id='HR-%04d' % k, week=iso(wk), month=iso(_ms(wk)), person=p, hours=hrs, overtime_hours=ot, pay=R2(hrs * s['hourly_rate'])))
        return out
    return _thin(_cached('hours', f), n)


def service_month_rows(n=None):
    def f():
        agg = {}
        for x in _rows_raw():
            if x['status'] != 'Completed': continue
            a = agg.setdefault((x['month'], x['service']), dict(grooms=0, revenue=0.0, mins=0, prod=0.0, labour=0.0))
            a['grooms'] += 1; a['revenue'] += x['price']; a['mins'] += x['worked_minutes']; a['prod'] += x['product_cost']
            s = staff_by_name[x['groomer']]
            a['labour'] += x['price'] * s['share_pct'] * (1 + EMPLOYER_COST_PCT) if s['pay_type'] == 'Commission' else x['worked_minutes'] / 60.0 * s['hourly_rate'] * (1 + EMPLOYER_COST_PCT)
        out = []; k = 0
        for m in months24():
            for sv in SERVICES:
                a = agg.get((iso(m), sv), dict(grooms=0, revenue=0.0, mins=0, prod=0.0, labour=0.0)); k += 1
                out.append(dict(row_id='SM-%04d' % k, month=iso(m), service=sv, grooms=a['grooms'], revenue=R2(a['revenue']), minutes=a['mins'], product_cost=R2(a['prod']), labour=R2(a['labour']),
                                margin=R2(a['revenue'] - a['prod'] - a['labour'])))
        return out
    return _thin(_cached('svm', f), n)


def service_profit(service, months=12):
    ms = {iso(month_start(k)) for k in range(1, months + 1)}
    rows = [x for x in service_month_rows() if x['service'] == service and x['month'] in ms]
    return dict(revenue=R2(sum(x['revenue'] for x in rows)), profit=R2(sum(x['margin'] for x in rows)), grooms=sum(x['grooms'] for x in rows))


def breed_profit_rows(n=None):
    def f():
        agg = {}; ms = {iso(month_start(k)) for k in range(1, 13)}
        pets = _pets_by()
        for x in _rows_raw():
            if x['status'] != 'Completed' or x['month'] not in ms: continue
            p = pets[x['pet_id']]; a = agg.setdefault(p['breed'], dict(grooms=0, revenue=0.0, mins=0, prod=0.0, labour=0.0))
            a['grooms'] += 1; a['revenue'] += x['price']; a['mins'] += x['worked_minutes']; a['prod'] += x['product_cost']
            s = staff_by_name[x['groomer']]
            a['labour'] += x['price'] * s['share_pct'] * (1 + EMPLOYER_COST_PCT) if s['pay_type'] == 'Commission' else x['worked_minutes'] / 60.0 * s['hourly_rate'] * (1 + EMPLOYER_COST_PCT)
        out = []
        for i, b in enumerate(breeds, 1):
            a = agg.get(b['breed'], dict(grooms=0, revenue=0.0, mins=0, prod=0.0, labour=0.0))
            out.append(dict(row_id='BP-%03d' % i, breed=b['breed'], size=b['size'], coat=b['coat'], species=b['species'], grooms=a['grooms'], revenue=R2(a['revenue']), minutes=a['mins'],
                            product_cost=R2(a['prod']), labour=R2(a['labour']), margin=R2(a['revenue'] - a['prod'] - a['labour'])))
        return out
    return _thin(_cached('bpr', f), n)


# ------------------------------------------------------------------ equipment, incidents, renewals, training
def equipment_rows(n=None): return _thin([dict(x) for x in equipment], n)


def equipment_service_rows(n=None):
    def f():
        out = []; k = 0
        for e in equipment:
            every = e['service_every_days']; last = to_date(e['last_service']); d = last; hist = []
            while d > HISTORY_START - day(200):
                hist.append(d); d = d - day(every + (len(hist) * 3) % 11 - 4)
            for d in reversed(hist[:6] if e['kind'] != 'Blade set' else hist[:8]):
                if d > TODAY: continue
                k += 1; rr = rng('es' + e['equipment_id'] + iso(d))
                kind = {'Clipper': 'Clipper service', 'Blade set': 'Blade sharpening', 'Dryer': 'Dryer filter and motor check', 'Tub': 'Tub drain and pump check', 'Grooming table': 'Tub drain and pump check',
                        'Van equipment': 'Van service' if e['item'] == 'Grooming van' else 'Generator service'}[e['kind']]
                out.append(dict(service_id='ES-%03d' % k, date=iso(d), equipment_id=e['equipment_id'], item=e['item'], kind=kind, vendor=staff_by_name['Gwen Pritchard' if e['kind'] == 'Van equipment' else 'Oskar Nowak']['name'],
                                cost=R2({'Clipper': 38, 'Blade set': 14, 'Dryer': 45, 'Tub': 30, 'Grooming table': 20, 'Van equipment': 120}[e['kind']] * (0.8 + 0.5 * rr.random())), downtime_days=rr.choice([0, 0, 1, 1, 2, 3])))
        out.sort(key=lambda x: (x['date'], x['service_id']))
        for i, x in enumerate(out, 1): x['service_id'] = 'ES-%03d' % i
        return out
    return _thin(_cached('eqs', f), n)


def incident_rows(n=None):
    def f():
        out = []; r = rng('inc'); aps = [x for x in _rows_raw() if x['status'] == 'Completed']
        for i in range(1, 46):
            x = aps[int((i / 46.0) ** 0.9 * (len(aps) - 1))]
            out.append(dict(incident_id='IN-%03d' % i, date=x['date'], month=x['month'], appt_id=x['appt_id'], pet=x['pet'], client=x['client'], groomer=x['groomer'], kind=r.choice(INCIDENT_KINDS),
                            owner_told_on=x['date'], follow_up_on=iso(to_date(x['date']) + day(r.choice([1, 2, 3]))), closed=(i < 44)))
        return out
    return _thin(_cached('inc', f), n)


def renewal_rows(n=None):
    def f():
        out = []; k = 0
        holders = {'Business licence': OWNER, 'Liability insurance': OWNER, 'Van insurance': VAN_GROOMER, 'Van road licence': 'Willowbrook van', 'Pet first aid course': None, 'Premises lease': 'Takumi Sato',
                   'Business registration': OWNER, 'Equipment warranty': 'Oskar Nowak'}
        cyc = {'Business licence': 365, 'Liability insurance': 365, 'Van insurance': 365, 'Van road licence': 365, 'Pet first aid course': 730, 'Premises lease': 1095, 'Business registration': 365, 'Equipment warranty': 365}
        off = {'Business licence': 140, 'Liability insurance': 12, 'Van insurance': 220, 'Van road licence': 95, 'Pet first aid course': 70, 'Premises lease': 380, 'Business registration': 260, 'Equipment warranty': 175}
        for kind in RENEWAL_KINDS:
            hs = [holders[kind]] if holders[kind] else ['Tomas Eriksen', 'Mei Tanaka', 'Chidi Adeyemi', 'Lucia Ferreira']
            for h in hs:
                cur = TODAY + day(off[kind] + (hs.index(h) * 37 if len(hs) > 1 else 0))
                d = cur
                while d > HISTORY_START - day(400): d = d - day(cyc[kind]); hist = d
                steps = []; d = cur - day(cyc[kind])
                while d > HISTORY_START - day(380):
                    steps.append(d); d = d - day(cyc[kind])
                for d in reversed(steps):
                    k += 1; out.append(dict(renewal_id='RN-%03d' % k, holder=h, item=kind, due_date=iso(d), renewed_on=iso(d - day(rng('rn%d' % k).randint(3, 25))), cost=R2(_ren_cost(kind) * 0.95), status='Done'))
                k += 1; out.append(dict(renewal_id='RN-%03d' % k, holder=h, item=kind, due_date=iso(cur), renewed_on='', cost=_ren_cost(kind), status='Due soon' if (cur - TODAY).days <= RENEWAL_WARN_DAYS else 'Upcoming'))
        out.sort(key=lambda x: (x['due_date'], x['renewal_id']))
        for i, x in enumerate(out, 1): x['renewal_id'] = 'RN-%03d' % i
        return out
    return _thin(_cached('ren', f), n)


def _ren_cost(kind): return {'Business licence': 180.0, 'Liability insurance': 640.0, 'Van insurance': 1150.0, 'Van road licence': 240.0, 'Pet first aid course': 95.0, 'Premises lease': 0.0, 'Business registration': 60.0, 'Equipment warranty': 210.0}[kind]


def training_rows(n=None):
    def f():
        out = []; k = 0
        for bi, b in enumerate(BATHERS):
            s = staff_by_name[b]; st = to_date(s['start'])
            for ti, t in enumerate(TASKS):
                rr = rng('tr' + b + t); shown = st + day(5 + ti * 9 + rr.randint(0, 6))
                if shown > TODAY: continue
                k += 1; signed = shown + day(rr.randint(7, 40))
                out.append(dict(training_id='TR-%03d' % k, bather=b, task=t, shown_on=iso(shown), signed_off_on=iso(signed) if signed <= TODAY else '', trainer=GROOMERS[(ti + bi) % 4],
                                hours=R2(1 + rr.random() * 3)))
        return out
    return _thin(_cached('trn', f), n)


# ------------------------------------------------------------------ waitlist, slots, win-back, rebooking, reviews, marketing
def waitlist_rows(n=None):
    def f():
        out = []; r = rng('wl'); ps = pet_rows(); act = [p for p in ps if p['last_visit'] and p['last_visit'] >= ago(60)]
        for i in range(1, 73):
            p = act[(i * 11) % len(act)]; added = TODAY - day(r.randint(0, 40)) if i > 8 else TODAY - day(r.randint(41, 150))
            st = _wchoice(r, WAIT_STATUS, [40, 15, 30, 15] if i > 8 else [0, 0, 60, 40])
            out.append(dict(wait_id='WL-%03d' % i, added_on=iso(added), pet=p['pet'], client=p['client'], phone=fake_phone(1000 + int(p['client_id'][3:])), service=p['usual_service'], size=p['size'], groomer=p['groomer'],
                            wanted_day=r.choice(WORKDAYS[:5]), status=st, offered_on=iso(added + day(r.randint(1, 6))) if st in ('Offered', 'Booked') else '', minutes=_minutes(p['usual_service'], p['size'], p['coat'])))
        out.sort(key=lambda x: x['added_on'])
        for i, x in enumerate(out, 1): x['wait_id'] = 'WL-%03d' % i
        return out
    return _thin(_cached('wl', f), n)


def slot_rows(n=None):
    def f():
        load = {}
        for x in _rows_raw():
            if x['status'] == 'Scheduled': load[(x['date'], x['groomer'])] = load.get((x['date'], x['groomer']), 0) + x['booked_minutes'] + 5
        out = []; k = 0
        for off in range(0, 22):
            dte = TODAY + day(off)
            if dte.weekday() == 6: continue
            for g in GROOMERS:
                if dte.weekday() not in _WORKS[g]: continue
                cap = 400 if g == VAN_GROOMER else DAY_MINUTES; used = load.get((iso(dte), g), 0); k += 1
                out.append(dict(slot_id='SL-%03d' % k, date=iso(dte), week=iso(week_start(dte)), weekday=WEEKDAYS[dte.weekday()], groomer=g, station=staff_by_name[g]['station'], capacity_minutes=cap,
                                booked_minutes=min(used, cap + 60), free_minutes=max(0, cap - used)))
        return out
    return _thin(_cached('slot', f), n)


def winback_rows(n=None):
    def f():
        out = []; r = rng('wb'); cl = client_rows(); k = 0
        lapsed = [c for c in cl if c['last_visit'] and c['next_visit'] == '' and (TODAY - to_date(c['last_visit'])).days > LAPSE_FACTOR * c['interval_weeks'] * 7]
        lapsed.sort(key=lambda c: c['last_visit'])
        for c in lapsed[:140]:
            k += 1; days = (TODAY - to_date(c['last_visit'])).days; sent = to_date(c['last_visit']) + day(int(LAPSE_FACTOR * c['interval_weeks'] * 7) + r.randint(2, 14))
            old = (TODAY - sent).days > 21
            res = _wchoice(r, WINBACK_RESULTS, [10, 28, 38, 24]) if old else 'Pending'
            if sent > TODAY: sent = TODAY - day(r.randint(1, 6)); res = 'Pending'
            avg = R2(c['spent'] / max(1, c['visits']))
            out.append(dict(winback_id='WB-%03d' % k, client=c['client'], client_id=c['client_id'], phone=c['phone'], last_visit=c['last_visit'], interval_weeks=c['interval_weeks'], days_since=days,
                            avg_ticket=avg, message_sent_on=iso(sent), result=res, returned_on=iso(sent + day(r.randint(3, 20))) if res == 'Returned' else ''))
        out.sort(key=lambda x: x['message_sent_on'])
        for i, x in enumerate(out, 1): x['winback_id'] = 'WB-%03d' % i
        return out
    return _thin(_cached('wb', f), n)


def rebook_rows(n=None):
    def f():
        out = []; k = 0
        for x in _rows_raw():
            if x['status'] == 'Completed' and x['channel'] != 'Walk-in' and x['date'] >= ago(180):
                k += 1
                out.append(dict(rebook_id='RB-%04d' % k, date=x['date'], month=x['month'], appt_id=x['appt_id'], client=x['client'], pet=x['pet'], groomer=x['groomer'], rebooked=x['rebooked_at_checkout'],
                                outcome='Rebooked' if x['rebooked_at_checkout'] else ('We will call you' if rng('rb' + x['appt_id']).random() < 0.6 else 'Declined'), front_desk=staff[7]['name']))
        return out
    return _thin(_cached('rb', f), n)


def review_rows(n=None):
    def f():
        out = []; r = rng('rev'); aps = [x for x in _rows_raw() if x['status'] == 'Completed']; k = 0
        for i in range(1, 231):
            x = aps[int((i / 231.0) * (len(aps) - 1))]; k += 1
            got = r.random() < 0.34
            out.append(dict(review_id='RV-%03d' % k, date=x['date'], month=x['month'], client=x['client'], groomer=x['groomer'], requested_on=x['date'], received=got,
                            rating=r.choice([5, 5, 5, 5, 4, 4, 3]) if got else 0, source=_wchoice(r, SOURCES, [26, 22, 14, 10, 9, 7, 5, 7])))
        return out
    return _thin(_cached('rev', f), n)


def marketing_rows(n=None):
    def f():
        out = []; r = rng('mk'); k = 0
        for m in months24():
            for kind in r.sample(MARKETING_KINDS, 3):
                k += 1
                spend = R2({'Social media post': 60, 'Local flyers': 180, 'Van sign': 90, 'Pet shop partner': 40, 'Rescue shelter event': 70, 'Referral reward': 100, 'Holiday booking reminder': 30, 'Review request': 0}[kind] * (0.7 + 0.7 * r.random()))
                out.append(dict(campaign_id='MK-%03d' % k, date=iso(m + day(r.randint(0, 24))), month=iso(m), kind=kind, spend=spend, new_clients=r.randint(1, 9) if spend else r.randint(0, 3),
                                source=_wchoice(r, SOURCES, [26, 22, 14, 10, 9, 7, 5, 7])))
        for x in out:
            if x['date'] > iso(TODAY): x['date'] = iso(TODAY)
        return out
    return _thin(_cached('mk', f), n)


# ------------------------------------------------------------------ money: expenses, tax, cash
def _season(m): return {1: 0.85, 2: 0.9}.get(m.month, 1.0)


def expense_rows(n=None):
    def f():
        out = []; k = 0; r = rng('exp')
        bb = {}
        for x in backbar_use_rows(): bb[x['month']] = bb.get(x['month'], 0.0) + x['cost']
        rt = {}
        for x in retail_sale_rows(): rt[x['month']] = rt.get(x['month'], 0.0) + x['cost']
        card = {}
        for x in payment_rows():
            if x['method'] == 'Card': card[x['month']] = card.get(x['month'], 0.0) + x['amount']
        vd = {}
        for x in van_day_rows():
            if not x['scheduled']: vd[x['month']] = vd.get(x['month'], 0.0) + x['fuel_cost'] + x['water_cost'] + x['generator_hours'] * GEN_HOUR
        fixed = {'Rent': (3000.0, 'Takumi Sato', 1), 'Utilities': (640.0, '', 5), 'Laundry': (360.0, 'Fatima Zahra', 28), 'Blades and equipment': (330.0, 'Hamid Karimi', 12), 'Repairs': (210.0, 'Oskar Nowak', 20),
                 'Insurance': (390.0, 'Olivia Brandt', 3), 'Booking and phone': (265.0, '', 7), 'Training': (110.0, '', 15), 'Accounting': (300.0, 'Sofia Lindgren', 25), 'Van loan and licence': (650.0 + 210.0, '', 2)}
        for m in months24():
            mi = iso(m); end = (TODAY if m == _ms(TODAY) else _eom(m))
            def add(cat, amt, sup, dd):
                nonlocal k
                dte = min(m + day(dd - 1), end); k += 1
                out.append(dict(expense_id='EX-%04d' % k, date=iso(dte), month=mi, category=cat, supplier=sup, amount=R2(amt), note=''))
            for cat, (amt, sup, dd) in fixed.items():
                v = amt * (0.93 + 0.14 * r.random()) if cat in ('Blades and equipment', 'Repairs', 'Utilities', 'Laundry', 'Training') else amt
                if cat == 'Rent' and m < add_months(TODAY, -11).replace(day=1): v = 2850.0
                add(cat, v, sup, dd)
            if mi in bb: add('Back-bar products', bb[mi] * 1.0, 'Hamid Karimi', 9)
            if mi in rt: add('Retail stock', rt[mi] * 1.1, 'Hamid Karimi', 10)
            if mi in card: add('Card fees', card[mi] * CARD_FEE_PCT, '', 27)
            if mi in vd: add('Van fuel and water', vd[mi], '', 26)
            add('Marketing', 250 * (0.7 + 0.8 * r.random()), 'Mario Conti', 18)
        return out
    return _thin(_cached('exp', f), n)


def _pnl():
    def f():
        rev = {};
        for x in _rows_raw():
            if x['status'] == 'Completed': rev[x['month']] = rev.get(x['month'], 0.0) + x['price']
            rev[x['month']] = rev.get(x['month'], 0.0) + x['fee_charged']
        for x in retail_sale_rows(): rev[x['month']] = rev.get(x['month'], 0.0) + x['price']
        for x in deposit_rows():
            if x['status'] == 'Kept': rev[iso(_ms(to_date(x['kept_on'])))] = rev.get(iso(_ms(to_date(x['kept_on']))), 0.0) + x['amount']
        pay = {}
        for x in pay_rows(): pay[x['month']] = pay.get(x['month'], 0.0) + x['amount'] + x['employer_cost']
        exp = {}
        for x in expense_rows(): exp[x['month']] = exp.get(x['month'], 0.0) + x['amount']
        out = {}
        for m in months24():
            mi = iso(m); out[mi] = dict(revenue=R2(rev.get(mi, 0.0)), pay=R2(pay.get(mi, 0.0)), expenses=R2(exp.get(mi, 0.0)))
            out[mi]['profit'] = R2(out[mi]['revenue'] - out[mi]['pay'] - out[mi]['expenses'])
        return out
    return _raw('pnl', f)


def tax_rows(n=None):
    def f():
        out = []; k = 0; p = _pnl()
        for m in months24():
            k += 1; pr = p[iso(m)]['profit']; sa = R2(max(0.0, pr) * TAX_SET_ASIDE_PCT)
            due = add_months(m, 1) + day(27)
            q = (m.month % 3 == 1)
            out.append(dict(tax_id='TX-%03d' % k, month=iso(m), profit=pr, set_aside_pct=TAX_SET_ASIDE_PCT, set_aside=sa, paid_on=iso(due) if q and due <= TODAY else '',
                            status='Paid' if (q and due <= TODAY) else 'Due' if (q and due > TODAY) else 'Upcoming'))
        return out
    return _thin(_cached('tax', f), n)


def cash_rows(n=None):
    def f():
        p = _pnl(); rows = []
        for m in months14():
            x = p[iso(m)]; tax = R2(max(0.0, x['profit']) * TAX_SET_ASIDE_PCT)
            rows.append(dict(month=iso(m), opening=0.0, takings=x['revenue'], pay=x['pay'], expenses=x['expenses'], tax_set_aside=tax, owner_draw=OWNER_DRAW, closing=0.0))
        run = 0.0; mn = 0.0
        for x in rows:
            run += x['takings'] - x['pay'] - x['expenses'] - x['tax_set_aside'] - x['owner_draw']; mn = min(mn, run)
        bal = R2(CASH_FLOOR + 6000 - mn)
        for x in rows:
            x['opening'] = R2(bal); bal += x['takings'] - x['pay'] - x['expenses'] - x['tax_set_aside'] - x['owner_draw']; x['closing'] = R2(bal)
        return rows
    return _thin(_cached('cash', f), n)


# ------------------------------------------------------------------ story
def story():
    """ids of the story rows: commission_groomer (+ commission_share, commission_profit_3m, commission_sales_3m), lapsed_client (+ lapsed_pet, lapsed_days, lapsed_interval), noshow_appt
    (+ noshow_client, noshow_client_id, noshow_pet, noshow_fee), vaccination_pet (+ vaccination_appt, vaccination_client, vaccination_valid_until, vaccination_days_past),
    overdue_equipment (+ overdue_item, overdue_days, van_service_days), renewal_due (+ renewal_item, renewal_date, renewal_days), losing_van_day (+ van_day_date, van_day_profit, van_day_grooms)"""
    out = {}; S = _WF()['story']
    gp = groomer_profit(STORY_GROOMER, 3)
    out['commission_groomer'] = STORY_GROOMER; out['commission_groomer_id'] = staff_by_name[STORY_GROOMER]['staff_id']; out['commission_share'] = staff_by_name[STORY_GROOMER]['share_pct']
    out['commission_profit_3m'] = gp['profit']; out['commission_sales_3m'] = gp['sales']
    lp = [p for p in _WF()['W']['pets'] if p.get('story') == 'lapsed'][0]
    last = [x for x in _rows_raw() if x['pet_id'] == lp['pet_id'] and x['status'] == 'Completed'][-1]
    out['lapsed_client'] = last['client']; out['lapsed_client_id'] = last['client_id']; out['lapsed_pet'] = last['pet']; out['lapsed_pet_id'] = last['pet_id']
    out['lapsed_days'] = (TODAY - to_date(last['date'])).days; out['lapsed_interval'] = lp['interval_weeks']; out['lapsed_last_visit'] = last['date']
    out['noshow_appt'] = S['noshow']; out['noshow_client'] = S['noshow_client']; out['noshow_client_id'] = S['noshow_client_id']; out['noshow_pet'] = S['noshow_pet']; out['noshow_fee'] = S['noshow_fee']
    vp = _pets_by()[S['vacc_pet_id']]
    out['vaccination_pet'] = vp['pet']; out['vaccination_pet_id'] = vp['pet_id']; out['vaccination_appt'] = S['vacc_appt']; out['vaccination_client'] = vp['client']
    out['vaccination_valid_until'] = _pet_vacc()[vp['pet_id']]; out['vaccination_days_past'] = (TODAY - to_date(out['vaccination_valid_until'])).days
    e = [x for x in equipment if x['item'] == 'Clipper 3'][0]; v = [x for x in equipment if x['item'] == 'Grooming van'][0]
    out['overdue_equipment'] = e['equipment_id']; out['overdue_item'] = e['item']; out['overdue_days'] = (TODAY - to_date(e['next_service'])).days
    out['van_equipment_id'] = v['equipment_id']; out['van_service_days'] = (to_date(v['next_service']) - TODAY).days
    rn = [x for x in renewal_rows() if x['item'] == 'Liability insurance' and x['renewed_on'] == ''][0]
    out['renewal_due'] = rn['renewal_id']; out['renewal_holder'] = rn['holder']; out['renewal_item'] = rn['item']; out['renewal_date'] = rn['due_date']; out['renewal_days'] = (to_date(rn['due_date']) - TODAY).days
    sv = [x for x in van_day_rows() if x['date'] >= ago(30) and not x['scheduled']]
    w = min(sv, key=lambda x: x['profit'])
    out['losing_van_day'] = w['van_day_id']; out['van_day_date'] = w['date']; out['van_day_profit'] = w['profit']; out['van_day_grooms'] = w['grooms']; out['van_day_area'] = w['area']
    return out


_GENS = ['client_rows', 'pet_rows', 'appointment_rows', 'noshow_rows', 'deposit_rows', 'payment_rows', 'tip_rows', 'retail_sale_rows', 'backbar_use_rows', 'daily_take_rows', 'van_day_rows',
         'groomer_month_rows', 'pay_rows', 'hours_rows', 'service_month_rows', 'breed_profit_rows', 'equipment_rows', 'equipment_service_rows', 'incident_rows', 'waitlist_rows', 'slot_rows',
         'winback_rows', 'rebook_rows', 'review_rows', 'marketing_rows', 'expense_rows', 'tax_rows', 'cash_rows', 'renewal_rows', 'training_rows']


def _digest():
    h = hashlib.md5()
    for nm in _GENS: h.update(repr(globals()[nm]()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); S = story(); G = {nm: globals()[nm]() for nm in _GENS}
    print('team', len(team), 'services', len(services), 'price_list', len(price_list), 'addons', len(addons), 'breeds', len(breeds), 'equipment', len(equipment), 'retail', len(retail_products))
    print(' '.join('%s %d' % (nm.replace('_rows', ''), len(v)) for nm, v in G.items()))
    print(S)
    print('seconds', round(time.time() - t0, 1))
