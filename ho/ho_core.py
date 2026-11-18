"""ho_core - shared demo data for the Home Management suite (Dar Templates, English edition).

Household: the Okafor-Lindqvist household. Adult 1 (office hours, two late days a week), adult 2 (shift work: Early, Late or Off, the pattern changes who cooks,
drives and cleans), two children (Child 1 about 12, Child 2 about 6), a grandparent who visits twice a month and helps with school pick-up, a babysitter on some
Friday evenings, a dog and a cat, an owned three-bedroom house with a small garden, a family car and an older second car. Renters use the same sheets:
"A trade" becomes "Landlord request". A single adult with no children or pets leaves those rows empty.
About 60 recipes with ingredients, 2 years of meal plans (and 2 weeks ahead), weekly grocery lists with items, pantry / fridge / chest freezer stock with use-by dates,
45 recurring chores with a 2-year chore log, 50 maintenance tasks with a log, repairs, 120 inventory items, a family calendar (terms, activities with carpools, birthdays,
visits, holidays), pets, vehicles, documents and renewals, 24 contacts, 4 projects with tasks, declutter and donation rows.
All rows are deterministic, oldest first; n= thins a list but keeps the most recent rows; optional dates are ''.
Dates are relative to TODAY (env HO_TODAY overrides); about 2 years of history, scheduled items up to 12 months ahead, rows in the last 30 days.
Money appears only as simple cost lines (one generic currency, no symbols); shares are 0..1 fractions. No brand, store, maker, service or company names.
Wording: gender-neutral, children as first names with school year and activity times only, no health or safety claims; every interval is "typical, check the manual".

Constants: HOUSEHOLD, SUITE, TODAY, Y, HISTORY_START, FUTURE_END, ADULT1, ADULT2, SOON_DAYS (due-soon window), USE_SOON_DAYS (use-by window), AGREED_SPLIT_A2 (0.5),
  WARRANTY_DAYS (90), DOC_LEAD_DAYS (60), REPLACE_RULE (0.5, "your rule"), POINT_VALUE (0.05 optional), WEEKLY_POINTS_GOAL, WEEK_START ('Monday'), CHILD_AGES,
  FOOD_DAYS_TYPICAL (fridge leftovers, "typical, check the label").
Date helpers: day, iso, ago, ahead, to_date, month_start, add_months, months14, months25, week_start, next_on, last_on; pairs, first_name, fake_phone, fake_email.
Lists (constants): PERSONS, EVENT_PEOPLE, DRIVERS, ROOMS, FREQS (FREQ_DAYS), MEAL_SLOTS, RECIPE_CATS, PREF_LABELS, STORAGE_PLACES, UNITS, SECTIONS, SHOPS,
  SEASONS, MAINT_AREAS, MAINT_WHO, TRADES, REPAIR_STATUS, ITEM_CATS, EVENT_KINDS, TERM_KINDS, SHIFTS, DOC_KINDS, DOC_STATUS, PROJECT_KINDS, PROJECT_STAGES,
  TASK_STATUS, DECISIONS, RSVP, GUEST_PREFS, GIFT_STATUS, PET_TASKS, VEH_KINDS, CONTACT_KINDS, ROLES, TEAM_GROUPS, WEEKDAYS, MONTH_NAMES.
People: team (16 rows HO-01..HO-16: 6 household incl. grandparent and babysitter, 10 outside contacts), household, outside.
Row generators (each takes n=None): recipe_rows (RC-01..RC-60), recipe_ingredient_rows (RI-), item_rows (IT-, the shared item catalog with pack size and shop),
  meal_plan_rows (MP-), grocery_list_rows (GL-), grocery_item_rows (GI-), stock_rows (ST-), leftover_rows (LO-), chore_rows (CH-01..CH-45), chore_log_rows (CL-),
  reward_rows (RW-), maintenance_rows (MT-01..MT-50), maintenance_log_rows (ML-), repair_rows (RP-), inventory_rows (IV-001..IV-120), term_rows (TM-), shift_rows (SH-,
  adult 2's shift and adult 1's late days per day), event_rows (EV-), gift_rows (GF-), guest_rows (GU-), pet_rows (PT-01..PT-02), pet_care_rows (PC-), vehicle_rows (VH-01..VH-02),
  vehicle_log_rows (VL-), document_rows (DC-), contact_rows (CT-), project_rows (PJ-01..PJ-04), project_task_rows (PK-), declutter_rows (DN-).
story(): dict of the story ids (asserted), see its docstring:
  food (a fridge item whose use-by is within 3 days and is not in this week's meal plan), chores (adult 2 about 65% of adult chore minutes in the last 30 days against an
  agreed 50/50), filter (furnace or boiler filter change about 3 weeks overdue) with alarm (smoke-alarm test due in about 5 days), washer (warranty ends in about 30 days with a
  fault logged in the repairs table), overlap (two children's activities overlap next week, only one adult free to drive), travel (a travel document expires before a trip about
  10 weeks away and the renewal lead time does not fit).
"""
import os
import datetime as dt
import calendar
import random

HOUSEHOLD = 'the Okafor-Lindqvist household'
SUITE = 'fx-20261118-home-management'
TODAY = dt.date.fromisoformat(os.environ['HO_TODAY']) if os.environ.get('HO_TODAY') else dt.date.today()
D = dt.date
Y = TODAY.year
ADULT1 = 'Adult 1'
ADULT2 = 'Adult 2'

SOON_DAYS = 14                  # "due soon" window for tasks and renewals, set your own
USE_SOON_DAYS = 3               # use-by window, typical, check the label
AGREED_SPLIT_A2 = 0.5           # adult 2's agreed share of adult chore minutes, your own agreement
WARRANTY_DAYS = 90
DOC_LEAD_DAYS = 60              # default "act this many days before the expiry date"
REPLACE_RULE = 0.5              # repairs over replacement price: "your rule", set your own
POINT_VALUE = 0.05              # optional value of one point, children never earn money by default
WEEKLY_POINTS_GOAL = 60
WEEK_START = 'Monday'
CHILD_AGES = (12, 6)
FOOD_DAYS_TYPICAL = 4           # cooked leftovers in the fridge, typical, check the label and your local rules

HISTORY_START = None
FUTURE_END = TODAY + dt.timedelta(days=365)


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
def months25(): return [month_start(k) for k in range(24, -1, -1)]
def week_start(d): return d - day(d.weekday())
HISTORY_START = month_start(24)


def pairs(labels):
    """(key, label) pairs; keys are lower-case with underscores and at most 21 characters"""
    out = []
    for s in labels:
        k = ''.join(ch if ch.isalnum() else '_' for ch in s.lower()).strip('_')
        while '__' in k: k = k.replace('__', '_')
        out.append((k[:21].rstrip('_'), s))
    return out


def first_name(name): return name.split()[0]
def fake_phone(i): return '+%d %d 555 %04d' % ([1, 44, 49, 61, 33, 34, 351, 31][i % 8], 20 + (i * 7) % 79, 3000 + (i * 37) % 6000)
def fake_email(name, i=0): return name.lower().replace(' ', '.').replace("'", '').replace('-', '') + (str(i) if i else '') + '@mail.example.com'
def rng(tag=''): return random.Random('ho-core-20261118-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _dim(y, m): return calendar.monthrange(y, m)[1]
def _dd(y, m, d): return D(y, m, min(d, _dim(y, m)))


def next_on(m, d, frm=None):
    """first date with this month and day on or after frm (default TODAY)"""
    frm = frm or TODAY
    x = _dd(frm.year, m, d)
    return x if x >= frm else _dd(frm.year + 1, m, d)


def last_on(m, d, frm=None):
    """last date with this month and day on or before frm (default TODAY)"""
    frm = frm or TODAY
    x = _dd(frm.year, m, d)
    return x if x <= frm else _dd(frm.year - 1, m, d)


# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
PERSONS = ['Adult 1', 'Adult 2', 'Child 1', 'Child 2']
EVENT_PEOPLE = ['Adult 1', 'Adult 2', 'Child 1', 'Child 2', 'Whole household']
DRIVERS = ['Adult 1', 'Adult 2', 'Grandparent', 'Carpool family', 'Walk or bike']
ROOMS = ['Kitchen', 'Living room', 'Bathroom', 'Main bedroom', 'Kids room', 'Hallway', 'Garden', 'Garage', 'Utility room', 'Whole home']
FREQS = ['Daily', 'Weekly', 'Fortnightly', 'Monthly', 'Quarterly', 'Twice a year', 'Yearly']
FREQ_DAYS = dict(zip(FREQS, (1, 7, 14, 30, 91, 182, 365)))
MEAL_SLOTS = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
RECIPE_CATS = ['Pasta and rice', 'Soups and stews', 'Oven bakes', 'Quick pan meals', 'Salads and cold', 'Breakfast dishes', 'Baking and sweets', 'Batch and freezer']
PREF_LABELS = ['Family favourite', 'Adult 1 prefers', 'Adult 2 prefers', 'Child 1 prefers', 'Child 2 avoids', 'Adult 2 avoids', 'No label']
STORAGE_PLACES = ['Pantry', 'Fridge', 'Chest freezer']
UNITS = ['g', 'kg', 'ml', 'l', 'pack', 'piece', 'tin', 'portion']
SECTIONS = ['Fruit and veg', 'Dairy and eggs', 'Meat and fish', 'Bakery', 'Dry goods and tins', 'Frozen', 'Drinks', 'Household', 'Pet']
SHOPS = ['Weekly shop', 'Top-up shop', 'Market', 'Online order']
SEASONS = ['Spring', 'Summer', 'Autumn', 'Winter', 'Any season']
MAINT_AREAS = ['Heating and air', 'Plumbing', 'Electrics and alarms', 'Appliances', 'Roof and gutters', 'Windows and doors', 'Garden and outdoors', 'Floors and walls',
               'Kitchen', 'Bathroom', 'Safety checks']
MAINT_WHO = ['Adult 1', 'Adult 2', 'A trade', 'Landlord request']
TRADES = ['Plumber', 'Electrician', 'Heating engineer', 'Appliance repairer', 'Handyman', 'Roofer', 'Locksmith', 'Pest controller', 'Landlord request', 'Self repair']
REPAIR_STATUS = ['Open', 'Waiting', 'Fixed']
ITEM_CATS = ['Appliance', 'Electronics', 'Furniture', 'Tools', 'Garden', 'Kitchenware', 'Sports and toys', 'Bedding and linen', 'Lighting', 'Other']
EVENT_KINDS = ['School', 'Activity', 'Birthday', 'Visit', 'Holiday', 'Appointment', 'Household', 'Trip']
TERM_KINDS = ['Term', 'Break']
SHIFTS = ['Early', 'Late', 'Off']
DOC_KINDS = ['Travel document', 'Licence', 'Policy', 'Contract', 'Warranty paper', 'School paper', 'Pet paper', 'Other']
DOC_STATUS = ['Valid', 'Renewal started', 'Renewed']
PROJECT_KINDS = ['Renovation', 'Garden', 'Hosting', 'Declutter']
PROJECT_STAGES = ['Idea', 'Planned', 'In progress', 'Waiting', 'Done']
TASK_STATUS = ['Not started', 'In progress', 'Blocked', 'Done']
DECISIONS = ['Keep', 'Donate', 'Sell', 'Bin']
RSVP = ['Yes', 'No', 'Maybe', 'No reply']
GUEST_PREFS = ['No label', 'Prefers fish', 'Avoids spicy food', 'Likes a vegetable main', 'Prefers a light dessert', 'Avoids very sweet dishes']
GIFT_STATUS = ['Idea', 'Bought', 'Wrapped', 'Given']
PET_TASKS = ['Grooming', 'Vet visit', 'Vaccination visit', 'Nail trim', 'Food bag bought', 'Bath']
VEH_KINDS = ['Service', 'Tyres', 'Annual test', 'Insurance renewal', 'Registration renewal', 'Repair', 'Mileage reading']
CONTACT_KINDS = ['Trade', 'School', 'Neighbour', 'Family', 'Pets', 'Vehicles']
ROLES = ['Adult 1', 'Adult 2', 'Child', 'Grandparent', 'Babysitter', 'Plumber', 'Electrician', 'Heating engineer', 'Vet clinic', 'Car mechanic', 'School office',
         'Carpool family', 'Neighbour', 'Landlord or agent', 'Dog walker']
TEAM_GROUPS = ['Household', 'Outside']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# ------------------------------------------------------------------ people
_house = [('HO-01', 'Sam Okafor', 'Adult 1', 'Office hours, two late days a week'),
          ('HO-02', 'Riley Lindqvist', 'Adult 2', 'Shift work, the pattern changes every week'),
          ('HO-03', 'Jo Okafor-Lindqvist', 'Child', 'Child 1, about 12, school year 7'),
          ('HO-04', 'Kit Okafor-Lindqvist', 'Child', 'Child 2, about 6, school year 1'),
          ('HO-05', 'Ada Okafor', 'Grandparent', 'Visits twice a month, helps with school pick-up'),
          ('HO-06', 'Mina Costa', 'Babysitter', 'Some Friday evenings')]
_out = [('HO-07', 'Tomas Reyes', 'Plumber', 'Taps, drains and the washing machine hook-up'), ('HO-08', 'Priya Nair', 'Electrician', 'Sockets, lights and alarm wiring'),
        ('HO-09', 'Ben Hughes', 'Heating engineer', 'Yearly boiler or furnace service'), ('HO-10', 'Elena Rossi', 'Vet clinic', 'Dates only: visits and vaccination visits'),
        ('HO-11', 'Pavel Ivanov', 'Car mechanic', 'Service and the yearly vehicle test'), ('HO-12', 'Ruth Mensah', 'School office', 'Absence notes, trips and forms'),
        ('HO-13', 'Lars Berg', 'Carpool family', 'Shares the Tuesday and Friday lifts'), ('HO-14', 'Chidi Eze', 'Neighbour', 'Holds a spare key'),
        ('HO-15', 'Marta Kowalski', 'Landlord or agent', 'For renters: maintenance requests'), ('HO-16', 'Sofia Lima', 'Dog walker', 'Weekday walks on late days')]
household = [dict(member_id=a, name=b, role=c, group='Household', phone=fake_phone(501 + i), email=fake_email(b), note=d, start=ago(3200 - 120 * i)) for i, (a, b, c, d) in enumerate(_house)]
outside = [dict(member_id=a, name=b, role=c, group='Outside', phone=fake_phone(521 + i), email=fake_email(b), note=d, start=ago(2300 - 130 * i)) for i, (a, b, c, d) in enumerate(_out)]
team = household + outside
MEMBER = {t['member_id']: t for t in team}

_CACHE = {}
_A0 = D(2024, 1, 1)             # a Monday: shift rotation anchor


def _thin(rows, n):
    if not n or n >= len(rows): return rows
    k = min(max(3, n // 5), n)
    if k >= n: return rows[-n:]
    recent = rows[-k:]; rest = rows[:-k]; m = n - k; step = len(rest) / float(m)
    return [rest[int(i * step)] for i in range(m)] + recent


# ------------------------------------------------------------------ school terms and shifts
def _terms(w):
    out = []
    for yy in (Y - 2, Y - 1, Y, Y + 1):
        bl = [('Winter break', D(yy - 1, 12, 20), D(yy, 1, 5), 'Break'), ('Spring term', D(yy, 1, 6), D(yy, 3, 28), 'Term'), ('Mid-term break', D(yy, 2, 16), D(yy, 2, 20), 'Break'),
              ('Spring break', D(yy, 3, 29), D(yy, 4, 13), 'Break'), ('Summer term', D(yy, 4, 14), D(yy, 7, 18), 'Term'), ('Mid-term break', D(yy, 5, 26), D(yy, 5, 30), 'Break'),
              ('Summer break', D(yy, 7, 19), D(yy, 9, 1), 'Break'), ('Autumn term', D(yy, 9, 2), D(yy, 12, 19), 'Term'), ('Mid-term break', D(yy, 10, 27), D(yy, 10, 31), 'Break')]
        out += [b for b in bl if b[2] >= HISTORY_START and b[1] <= FUTURE_END]
    out = sorted(set(out), key=lambda b: (b[1], b[2]))
    w['_terms'] = out
    w['terms'] = [dict(term_id='TM-%02d' % (i + 1), term=a, kind=k, start=iso(s), end=iso(e), days=(e - s).days + 1) for i, (a, s, e, k) in enumerate(out)]


def _in_break(d, w):
    return any(k == 'Break' and s <= d <= e for a, s, e, k in w['_terms'])


NEXT_MON = week_start(TODAY) + day(7)
OVERLAP_DAY = NEXT_MON + day(3)          # next Thursday: adult 1's late day
TRIP_START = TODAY + day(70)
_SHIFT_OVR = {OVERLAP_DAY: 'Off'}
_PAT = [['Early'] * 5 + ['Off'] * 2, ['Late'] * 4 + ['Off', 'Late', 'Off'], ['Off', 'Off', 'Early', 'Early', 'Early', 'Early', 'Off'], ['Late', 'Late', 'Off', 'Off', 'Early', 'Early', 'Off']]


def _shift(d):
    if d in _SHIFT_OVR: return _SHIFT_OVR[d]
    return _PAT[((d - _A0).days // 7) % 4][d.weekday()]


def _late1(d): return d.weekday() in (1, 3)
def _visit(d): return d.weekday() == 2 and (d.day - 1) // 7 in (1, 3)


def _shifts(w):
    rows = []; d = HISTORY_START
    while d <= FUTURE_END:
        l1 = _late1(d); s = _shift(d); free = (0 if l1 else 1) + (0 if s == 'Late' else 1)
        rows.append(dict(shift_id='SH-%04d' % (len(rows) + 1), date=iso(d), weekday=WEEKDAYS[d.weekday()], adult1_late=l1, adult2_shift=s, adults_free=free))
        d += day(1)
    w['shifts'] = rows


# ------------------------------------------------------------------ item catalog and recipes
# name|section|unit|place|per serving|pack size|shelf days|minimum stock|price per pack
_CAT = """pasta|Dry goods and tins|kg|Pantry|0.09|0.5|700|1|1.6
rice|Dry goods and tins|kg|Pantry|0.07|1|700|1|2.4
noodles|Dry goods and tins|pack|Pantry|0.25|1|500|2|1.4
couscous|Dry goods and tins|kg|Pantry|0.06|0.5|500|0.5|1.8
flour|Dry goods and tins|kg|Pantry|0.05|1.5|400|1|1.5
sugar|Dry goods and tins|kg|Pantry|0.03|1|700|0.5|1.3
oats|Dry goods and tins|kg|Pantry|0.04|1|365|0.5|1.9
lentils|Dry goods and tins|kg|Pantry|0.05|0.5|700|0.5|2.1
baking powder|Dry goods and tins|pack|Pantry|0.1|1|500|1|1.2
stock cubes|Dry goods and tins|pack|Pantry|0.25|1|600|1|1.5
tinned tomatoes|Dry goods and tins|tin|Pantry|0.5|1|700|4|0.8
beans|Dry goods and tins|tin|Pantry|0.25|1|700|3|0.9
chickpeas|Dry goods and tins|tin|Pantry|0.25|1|700|2|0.9
coconut milk|Dry goods and tins|tin|Pantry|0.25|1|600|2|1.4
sweetcorn|Dry goods and tins|tin|Pantry|0.25|1|700|2|0.9
tuna|Dry goods and tins|tin|Pantry|0.25|1|700|2|1.5
olive oil|Dry goods and tins|l|Pantry|0.02|0.5|500|0.5|5.5
soy sauce|Dry goods and tins|ml|Pantry|10|250|500|100|2.2
honey|Dry goods and tins|g|Pantry|10|340|700|100|3.4
tortillas|Bakery|pack|Pantry|0.25|1|30|1|1.7
breakfast cereal|Dry goods and tins|pack|Pantry|0|1|300|1|3.1
peanut butter|Dry goods and tins|pack|Pantry|0|1|365|1|2.6
jam|Dry goods and tins|pack|Pantry|0|1|365|1|2.0
tea|Drinks|pack|Pantry|0|1|365|1|2.8
coffee|Drinks|pack|Pantry|0|1|365|1|4.6
dish soap|Household|pack|Pantry|0|1|900|1|1.9
laundry detergent|Household|pack|Pantry|0|1|900|1|7.5
toilet paper|Household|pack|Pantry|0|1|900|2|6.2
bin bags|Household|pack|Pantry|0|1|900|1|2.9
kitchen roll|Household|pack|Pantry|0|1|900|1|3.2
dog food|Pet|kg|Pantry|0|7.5|300|2|15.0
cat food|Pet|kg|Pantry|0|2|300|0.5|8.5
potatoes|Fruit and veg|kg|Pantry|0.25|2.5|21|1|2.9
onion|Fruit and veg|kg|Pantry|0.08|1|30|1|1.4
garlic|Fruit and veg|piece|Pantry|0.5|1|30|1|0.6
bananas|Fruit and veg|piece|Pantry|1|6|5|4|1.5
bread|Bakery|piece|Pantry|0.15|1|4|1|1.6
bread rolls|Bakery|pack|Pantry|0.25|1|4|0|1.6
milk|Dairy and eggs|l|Fridge|0.1|2|10|2|1.9
eggs|Dairy and eggs|piece|Fridge|0.5|12|28|6|3.1
butter|Dairy and eggs|pack|Fridge|0.05|1|60|1|2.6
cheese|Dairy and eggs|kg|Fridge|0.03|0.3|30|0.2|3.2
yoghurt|Dairy and eggs|piece|Fridge|1|4|14|4|2.1
cream|Dairy and eggs|ml|Fridge|40|300|10|0|1.4
carrots|Fruit and veg|kg|Fridge|0.1|1|14|0.5|1.1
peppers|Fruit and veg|piece|Fridge|0.5|3|7|2|2.4
broccoli|Fruit and veg|piece|Fridge|0.25|1|6|1|1.2
spinach|Fruit and veg|pack|Fridge|0.25|1|5|1|1.6
lettuce|Fruit and veg|piece|Fridge|0.25|1|6|1|1.1
tomatoes|Fruit and veg|kg|Fridge|0.1|0.5|7|0.3|2.0
cucumber|Fruit and veg|piece|Fridge|0.25|1|8|1|0.9
mushrooms|Fruit and veg|pack|Fridge|0.25|1|6|1|1.8
leeks|Fruit and veg|piece|Fridge|0.5|1|10|0|0.8
lemons|Fruit and veg|piece|Fridge|0.25|1|20|2|0.5
apples|Fruit and veg|kg|Fridge|0.15|1|20|1|2.6
chicken breast|Meat and fish|pack|Fridge|0.25|1|3|0|5.6
chicken thighs|Meat and fish|pack|Fridge|0.25|1|3|0|4.4
mince|Meat and fish|kg|Fridge|0.1|0.5|3|0|3.9
beef|Meat and fish|kg|Fridge|0.12|0.5|3|0|6.5
sausages|Meat and fish|pack|Fridge|0.25|1|4|0|3.4
ham|Meat and fish|pack|Fridge|0.1|1|6|1|2.2
tofu|Meat and fish|pack|Fridge|0.25|1|12|0|1.9
berries|Fruit and veg|pack|Chest freezer|0.25|1|180|1|2.8
fish fillets|Meat and fish|pack|Chest freezer|0.25|1|120|0|5.2
pizza base|Bakery|pack|Chest freezer|0.5|1|120|0|1.8
peas|Frozen|pack|Chest freezer|0.1|1|300|1|1.4
fish fingers|Frozen|pack|Chest freezer|0.25|1|240|1|2.9
ice cream|Frozen|piece|Chest freezer|0|1|200|0|3.6
frozen veg mix|Frozen|pack|Chest freezer|0|1|300|1|1.7
pastry sheets|Frozen|pack|Chest freezer|0|1|200|0|2.4"""
CATALOG = []
for _i, _l in enumerate(_CAT.split('\n')):
    n_, s_, u_, p_, ps_, pk_, sh_, mn_, pr_ = _l.split('|')
    CATALOG.append(dict(item_id='IT-%03d' % (_i + 1), item=n_, section=s_, unit=u_, place=p_, per_serving=float(ps_), pack_size=float(pk_), shelf_days=int(sh_), min_stock=float(mn_),
                        pack_price=float(pr_), shop='Market' if n_ in ('apples', 'carrots', 'tomatoes', 'cucumber', 'lemons', 'leeks', 'spinach') else 'Weekly shop'))
CAT = {c['item']: c for c in CATALOG}
assert all(c['unit'] in UNITS and c['section'] in SECTIONS for c in CATALOG)

# name | category | prep min | servings | ingredients
_REC = """Spaghetti with tomato sauce|Pasta and rice|25|4|pasta,tinned tomatoes,onion,garlic,cheese
Mince and veg pasta|Pasta and rice|35|4|pasta,mince,onion,carrots,tinned tomatoes
Creamy mushroom pasta|Pasta and rice|30|4|pasta,mushrooms,cream,garlic,cheese
Vegetable fried rice|Pasta and rice|25|4|rice,eggs,peas,carrots,onion
Chicken and rice one pot|Pasta and rice|40|4|rice,chicken thighs,onion,peppers,stock cubes
Lentil and rice bowl|Pasta and rice|35|4|rice,lentils,onion,carrots,spinach
Noodle stir fry|Pasta and rice|20|4|noodles,peppers,broccoli,carrots,soy sauce
Risotto with peas|Pasta and rice|40|4|rice,peas,onion,stock cubes,cheese
Tomato soup|Soups and stews|30|4|tinned tomatoes,onion,carrots,stock cubes,cream
Chicken soup|Soups and stews|45|6|chicken breast,carrots,onion,potatoes,stock cubes
Lentil soup|Soups and stews|35|6|lentils,carrots,onion,tinned tomatoes,stock cubes
Vegetable soup|Soups and stews|35|6|carrots,potatoes,onion,broccoli,stock cubes
Beef stew|Soups and stews|90|6|beef,carrots,potatoes,onion,stock cubes
Bean chilli|Soups and stews|40|6|beans,tinned tomatoes,onion,peppers,rice
Chickpea curry|Soups and stews|35|4|chickpeas,coconut milk,onion,spinach,rice
Potato and leek soup|Soups and stews|40|4|potatoes,leeks,onion,stock cubes,milk
Roast chicken and potatoes|Oven bakes|75|6|chicken thighs,potatoes,carrots,onion,olive oil
Sausage and veg tray bake|Oven bakes|50|4|sausages,potatoes,peppers,onion,olive oil
Fish pie|Oven bakes|60|4|fish fillets,potatoes,milk,butter,peas
Cottage pie|Oven bakes|70|6|mince,potatoes,carrots,onion,peas
Cheese and broccoli bake|Oven bakes|40|4|cheese,broccoli,cream,pasta
Baked fish with veg|Oven bakes|45|4|fish fillets,broccoli,potatoes,lemons,olive oil
Stuffed peppers|Oven bakes|55|4|peppers,rice,mince,cheese,tinned tomatoes
Pizza night|Oven bakes|30|4|pizza base,tinned tomatoes,cheese,peppers,mushrooms
Omelette and salad|Quick pan meals|15|4|eggs,cheese,lettuce,tomatoes,butter
Chicken wraps|Quick pan meals|25|4|tortillas,chicken breast,lettuce,peppers,yoghurt
Bean quesadillas|Quick pan meals|20|4|tortillas,beans,cheese,peppers,onion
Sausage and mash|Quick pan meals|35|4|sausages,potatoes,peas,butter,milk
Fish fingers and peas|Quick pan meals|20|4|fish fingers,peas,potatoes,butter,tomatoes
Egg fried noodles|Quick pan meals|20|4|noodles,eggs,spinach,soy sauce,onion
Burger night|Quick pan meals|30|4|mince,bread rolls,lettuce,tomatoes,cheese
Tofu stir fry|Quick pan meals|25|4|tofu,broccoli,peppers,rice,soy sauce
Tuna pasta salad|Salads and cold|20|4|pasta,tuna,sweetcorn,cucumber,tomatoes
Simple salad plate|Salads and cold|15|4|cucumber,tomatoes,cheese,lettuce,olive oil
Chicken and rice salad|Salads and cold|30|4|chicken breast,rice,cucumber,peppers,lemons
Couscous and veg bowl|Salads and cold|20|4|couscous,peppers,cucumber,chickpeas,lemons
Sandwich lunch boxes|Salads and cold|15|4|bread,ham,cheese,lettuce,butter
Bean and corn salad|Salads and cold|15|4|beans,sweetcorn,peppers,onion,lemons
Porridge with fruit|Breakfast dishes|10|4|oats,milk,bananas,apples,honey
Pancakes|Breakfast dishes|25|4|flour,eggs,milk,butter,bananas
Scrambled eggs on toast|Breakfast dishes|10|4|eggs,bread,butter,milk,tomatoes
Yoghurt and fruit bowl|Breakfast dishes|5|4|yoghurt,bananas,berries,oats,honey
Cheese toasties|Breakfast dishes|10|4|bread,cheese,butter,ham,tomatoes
Weekend french toast|Breakfast dishes|20|4|bread,eggs,milk,butter,bananas
Banana bread|Baking and sweets|70|8|flour,bananas,eggs,butter,sugar
Apple crumble|Baking and sweets|55|6|apples,flour,butter,sugar,oats
Oat biscuits|Baking and sweets|35|12|oats,flour,butter,sugar,eggs
Sponge cake|Baking and sweets|60|8|flour,eggs,butter,sugar,baking powder
Muffins|Baking and sweets|40|12|flour,eggs,milk,sugar,baking powder
Lemon traybake|Baking and sweets|55|12|flour,lemons,eggs,butter,sugar
Big batch bolognese|Batch and freezer|75|8|mince,tinned tomatoes,onion,carrots,pasta
Batch vegetable curry|Batch and freezer|60|8|chickpeas,coconut milk,potatoes,spinach,onion
Freezer meatballs|Batch and freezer|60|8|mince,eggs,onion,tinned tomatoes,garlic
Batch chicken casserole|Batch and freezer|80|8|chicken thighs,carrots,potatoes,onion,stock cubes
Big batch chilli|Batch and freezer|60|8|beans,mince,tinned tomatoes,onion,rice
Lasagne|Batch and freezer|90|8|mince,pasta,tinned tomatoes,cheese,milk
Veggie burgers|Batch and freezer|50|8|beans,oats,onion,eggs,carrots
Soup for the freezer|Batch and freezer|50|8|carrots,potatoes,onion,leeks,stock cubes
Pasta sauce jars|Batch and freezer|45|8|tinned tomatoes,onion,garlic,olive oil,carrots
Leftovers night|Batch and freezer|5|4|"""
RECIPES = []
for _i, _l in enumerate(_REC.split('\n')):
    n_, c_, p_, s_, g_ = _l.split('|')
    ing = [x for x in g_.split(',') if x]
    assert all(x in CAT for x in ing), (n_, [x for x in ing if x not in CAT])
    pref = 'Child 2 avoids' if ('mushrooms' in ing or 'chickpeas' in ing or 'spinach' in ing) else 'Child 1 prefers' if 'noodles' in ing or 'fish fingers' in ing else \
        'Adult 1 prefers' if 'tofu' in ing or 'lentils' in ing else 'Adult 2 prefers' if 'fish fillets' in ing or 'beef' in ing else 'Adult 2 avoids' if 'tuna' in ing else \
        'Family favourite' if _i % 3 == 0 else 'No label'
    RECIPES.append(dict(recipe_id='RC-%02d' % (_i + 1), recipe=n_, category=c_, prep_min=int(p_), servings=int(s_), pref_label=pref, ingredients=ing))
RC = {r['recipe_id']: r for r in RECIPES}
SOUP_ID = 'RC-10'
assert RC[SOUP_ID]['recipe'] == 'Chicken soup' and len(RECIPES) == 60


def _ing_qty(item, servings):
    c = CAT[item]; q = c['per_serving'] * servings
    return round(q, 2) if q < 10 else round(q)


def _recipes(w):
    w['recipes'] = [dict(recipe_id=r['recipe_id'], recipe=r['recipe'], category=r['category'], prep_min=r['prep_min'], servings=r['servings'], pref_label=r['pref_label'],
                         ingredient_count=len(r['ingredients'])) for r in RECIPES]
    ri = []
    for r in RECIPES:
        for it in r['ingredients']:
            ri.append(dict(recipe_id=r['recipe_id'], recipe=r['recipe'], item=it, qty=_ing_qty(it, r['servings']), unit=CAT[it]['unit'], section=CAT[it]['section']))
    for i, x in enumerate(ri): x['ingredient_id'] = 'RI-%04d' % (i + 1)
    w['recipe_ingredients'] = ri
    w['items'] = [dict(c) for c in CATALOG]


# ------------------------------------------------------------------ meal plan
def _cook(d):
    s = _shift(d)
    if _late1(d): return ADULT2 if s != 'Late' else ADULT1
    if s == 'Late': return ADULT1
    return ADULT1 if (d.toordinal() // 7) % 2 == 0 else ADULT2


def _meal(w):
    r = rng('meal'); recent = []; rows = []
    cats = ['Pasta and rice', 'Soups and stews', 'Oven bakes', 'Quick pan meals', 'Salads and cold', 'Batch and freezer']
    pool = [x for x in RECIPES if x['category'] in cats and x['recipe_id'] not in ('RC-24', 'RC-60')]
    ex_lo, ex_hi = TODAY - day(4), TODAY + day(10)
    d = HISTORY_START; end = TODAY + day(14)
    while d <= end:
        wd = d.weekday(); win = ex_lo <= d <= ex_hi
        def pick(cs, avoid=()):
            c = [x for x in RECIPES if x['category'] in cs and x['recipe_id'] not in recent[-12:] and not (win and x['recipe_id'] == SOUP_ID) and x['recipe_id'] not in avoid]
            return r.choice(c)
        if wd == 4 and r.random() < .4: rec = RC['RC-24']
        elif wd == 0 and r.random() < .25: rec = RC['RC-60']
        elif wd == 6: rec = pick(['Oven bakes', 'Soups and stews'])
        elif _late1(d): rec = pick(['Quick pan meals', 'Pasta and rice', 'Batch and freezer'])
        else: rec = pick(cats)
        if rec['recipe_id'] == SOUP_ID and win: rec = RC['RC-11']
        recent.append(rec['recipe_id'])
        eat = 4 - (1 if _shift(d) == 'Late' and not _late1(d) else 0) + (1 if _visit(d) else 0)
        rows.append((d, 'Dinner', rec, eat))
        if wd >= 5:
            rows.append((d, 'Lunch', pick(['Salads and cold', 'Quick pan meals', 'Soups and stews']), 4))
            rows.append((d, 'Breakfast', pick(['Breakfast dishes']), 4))
            if wd == 6 and r.random() < .55: rows.append((d, 'Snack', pick(['Baking and sweets']), 4))
        d += day(1)
    w['_meal'] = rows
    out = []
    for i, (d, slot, rec, eat) in enumerate(rows):
        out.append(dict(plan_id='MP-%04d' % (i + 1), date=iso(d), slot=slot, recipe_id=rec['recipe_id'], recipe=rec['recipe'], servings=eat,
                        cook=_cook(d) if slot == 'Dinner' else (ADULT1 if (d.toordinal() + len(slot)) % 2 else ADULT2), prep_min=rec['prep_min'],
                        cooked=bool(d < TODAY and r.random() < .92)))
    w['meal_plan'] = out


# ------------------------------------------------------------------ groceries
STAPLES = ['milk', 'eggs', 'bread', 'bananas', 'yoghurt', 'butter', 'cheese', 'onion', 'potatoes']
EXTRAS = ['tea', 'coffee', 'breakfast cereal', 'peanut butter', 'jam', 'dish soap', 'laundry detergent', 'toilet paper', 'bin bags', 'kitchen roll', 'ice cream', 'frozen veg mix',
          'dog food', 'cat food', 'pastry sheets', 'honey']


def _price(c, qty):
    import math
    packs = max(1, int(math.ceil(qty / c['pack_size'] - 1e-9))); return packs, R2(packs * c['pack_price'] * (1.0 + 0.03 * max(0, (TODAY.year - HISTORY_START.year))))


def _grocery(w):
    r = rng('grocery'); lists = []; items = []
    plan = {}
    for d, slot, rec, eat in w['_meal']:
        if slot == 'Dinner': plan.setdefault(d, []).append((rec, eat))
    s = HISTORY_START + day((5 - HISTORY_START.weekday()) % 7)
    spec = []
    while s <= TODAY + day(7):
        spec.append((s, 'Weekly shop'))
        if (s.toordinal() // 7) % 2 == 0 and s + day(-3) >= HISTORY_START: spec.append((s - day(3), 'Top-up shop'))
        if s.day <= 7: spec.append((s + day(1), 'Market'))
        if (s.toordinal() // 7) % 5 == 0: spec.append((s + day(1), 'Online order'))
        s += day(7)
    spec = sorted(x for x in spec if x[0] <= TODAY + day(8))
    for d, shop in spec:
        need = {}
        if shop == 'Weekly shop':
            for k in range(0, 7):
                for rec, eat in plan.get(d + day(k), []):
                    for it in rec['ingredients']:
                        need[it] = need.get(it, 0) + CAT[it]['per_serving'] * eat
            for it in STAPLES: need[it] = need.get(it, 0) + CAT[it]['pack_size'] * (1 if r.random() < .8 else 0)
            for it in r.sample(EXTRAS, 4): need[it] = CAT[it]['pack_size']
            need = {k: v for k, v in need.items() if v > 0 and CAT[k]['section'] != 'Frozen' or r.random() < .6}
        elif shop == 'Top-up shop':
            for it in r.sample(STAPLES + ['lettuce', 'cucumber', 'tomatoes', 'peppers', 'cream'], 5): need[it] = CAT[it]['pack_size']
        elif shop == 'Market':
            for it in r.sample(['apples', 'carrots', 'tomatoes', 'cucumber', 'lemons', 'leeks', 'spinach', 'potatoes', 'onion', 'peppers'], 6): need[it] = CAT[it]['pack_size'] * 1
        else:
            for it in r.sample(['laundry detergent', 'toilet paper', 'dog food', 'cat food', 'coffee', 'tea', 'dish soap', 'bin bags'], 5): need[it] = CAT[it]['pack_size']
        lid = 'GL-%03d' % (len(lists) + 1); bought = d <= TODAY - day(1); tot = 0.0; cnt = 0
        for it, q in sorted(need.items(), key=lambda kv: (CAT[kv[0]]['section'], kv[0])):
            c = CAT[it]; packs, price = _price(c, q)
            items.append(dict(list_id=lid, item=it, qty=round(packs * c['pack_size'], 2), unit=c['unit'], section=c['section'], shop=shop, bought=bought, cost=price if bought else 0.0)); tot += price; cnt += 1
        actual = R2(tot * (1.1 if d.month == 12 else 1.0)) if bought else 0.0
        lists.append(dict(list_id=lid, date=iso(d), shop=shop, status='Bought' if bought else 'Open', items=cnt, est_cost=R2(tot * r.uniform(.92, 1.06)), actual_cost=actual))
    for i, x in enumerate(items): x['grocery_item_id'] = 'GI-%04d' % (i + 1)
    w['grocery_lists'] = lists; w['grocery_items'] = items


# ------------------------------------------------------------------ stock
def _stock(w):
    r = rng('stock'); rows = []
    for c in CATALOG:
        if c['item'] in ('dish soap', 'laundry detergent', 'toilet paper', 'bin bags', 'kitchen roll') and r.random() < .3: pass
        k = r.choice((1, 1, 2, 3)); qty = round(c['pack_size'] * k, 2)
        if c['unit'] in ('piece',) and c['pack_size'] >= 6: qty = float(int(c['pack_size'] * r.choice((.5, 1, 1.5))))
        added = TODAY - day(r.randint(2, 38))
        if c['place'] == 'Pantry': ub = added + day(int(c['shelf_days'] * r.uniform(.45, 1.0)))
        elif c['place'] == 'Fridge': ub = TODAY + day(r.randint(-2, max(2, c['shelf_days'] - 2)))
        else: ub = TODAY + day(r.randint(25, c['shelf_days'] - 20 if c['shelf_days'] > 60 else 40))
        if c['place'] == 'Fridge' and c['shelf_days'] <= 5 and ub < added: ub = added + day(2)
        if ub < added: ub = added + day(1)
        rows.append(dict(item=c['item'], place=c['place'], quantity=qty, unit=c['unit'], added=added, use_by=ub, min_qty=c['min_stock'], section=c['section'], recipe_id=''))
    # leftover dishes in fridge and freezer
    lo = [('Chicken soup portions', 'Fridge', 3, TODAY - day(4), TODAY + day(2), SOUP_ID), ('Bolognese portions', 'Chest freezer', 5, TODAY - day(46), TODAY + day(75), 'RC-51'),
          ('Vegetable curry portions', 'Chest freezer', 4, TODAY - day(30), TODAY + day(88), 'RC-52'), ('Meatballs portions', 'Chest freezer', 6, TODAY - day(61), TODAY + day(52), 'RC-53'),
          ('Chilli portions', 'Chest freezer', 3, TODAY - day(15), TODAY + day(100), 'RC-55'), ('Lasagne portions', 'Chest freezer', 2, TODAY - day(20), TODAY + day(94), 'RC-56'),
          ('Pasta sauce portions', 'Fridge', 2, TODAY - day(2), TODAY + day(5), 'RC-59')]
    for nm, pl, q, a, ub, rid in lo:
        rows.append(dict(item=nm, place=pl, quantity=float(q), unit='portion', added=a, use_by=ub, min_qty=0.0, section='Frozen' if pl == 'Chest freezer' else 'Dairy and eggs', recipe_id=rid))
    rows.sort(key=lambda x: (x['place'], x['item']))
    for i, x in enumerate(rows): x['stock_id'] = 'ST-%03d' % (i + 1); x['added'] = iso(x['added']); x['use_by'] = iso(x['use_by'])
    w['stock'] = rows
    # leftover log: Sunday batch cooking
    lg = []
    d = HISTORY_START + day((6 - HISTORY_START.weekday()) % 7)
    while d <= TODAY:
        if r.random() < .55 or TODAY - day(10) <= d <= TODAY - day(3):
            rec = r.choice([x for x in RECIPES if x['category'] in ('Batch and freezer', 'Soups and stews')])
            made = rec['servings']; left = r.randint(2, max(2, made - 3)); frz = r.random() < .6
            tf = d + day(1) if frz else ''
            eat = (d + day(r.randint(60, 100))) if frz else d + day(FOOD_DAYS_TYPICAL)
            lg.append(dict(date=iso(d), dish=rec['recipe'], recipe_id=rec['recipe_id'], portions_made=made, portions_left=left if eat >= TODAY - day(3) else 0, to_freezer=iso(tf) if tf else '', eat_by=iso(eat)))
        d += day(7)
    for i, x in enumerate(lg): x['leftover_id'] = 'LO-%03d' % (i + 1)
    w['leftovers'] = lg


# ------------------------------------------------------------------ chores
# chore | room | frequency | minutes | default owner | points | hidden (planning, booking, remembering)
_CH = [('Dinner dishes', 'Kitchen', 'Daily', 20, 'Child 1', 3, 0), ('Wipe kitchen surfaces', 'Kitchen', 'Daily', 10, 'Adult 2', 2, 0), ('Tidy the living room', 'Living room', 'Daily', 10, 'Child 2', 2, 0),
       ('Feed the pets', 'Kitchen', 'Daily', 5, 'Child 2', 2, 0),
       ('Vacuum the living areas', 'Living room', 'Weekly', 30, 'Adult 1', 5, 0), ('Mop the kitchen floor', 'Kitchen', 'Weekly', 20, 'Adult 2', 4, 0),
       ('Clean the bathroom', 'Bathroom', 'Weekly', 40, 'Adult 2', 6, 0), ('Clean the toilet', 'Bathroom', 'Weekly', 10, 'Child 1', 4, 0),
       ('Change the bed linen', 'Main bedroom', 'Weekly', 25, 'Adult 1', 4, 0), ('Laundry, colours', 'Utility room', 'Weekly', 15, 'Adult 2', 3, 0),
       ('Laundry, whites', 'Utility room', 'Weekly', 15, 'Adult 1', 3, 0), ('Wash the towels', 'Utility room', 'Weekly', 15, 'Adult 2', 3, 0),
       ('Take out rubbish and recycling', 'Whole home', 'Weekly', 10, 'Child 1', 3, 0), ('Water the plants', 'Living room', 'Weekly', 5, 'Child 2', 2, 0),
       ('Tidy the kids room', 'Kids room', 'Weekly', 20, 'Child 1', 3, 0), ('Dust the surfaces', 'Living room', 'Weekly', 20, 'Adult 1', 3, 0),
       ('Sweep the hallway', 'Hallway', 'Weekly', 10, 'Child 2', 2, 0), ('Mow the lawn in season', 'Garden', 'Weekly', 45, 'Adult 2', 6, 0),
       ('Plan the week of meals', 'Kitchen', 'Weekly', 30, 'Adult 1', 4, 1), ('Check the pantry and write the list', 'Kitchen', 'Weekly', 20, 'Adult 1', 3, 1),
       ('Do the weekly shop', 'Whole home', 'Weekly', 75, 'Adult 2', 6, 0),
       ('Change the kids bed linen', 'Kids room', 'Fortnightly', 25, 'Adult 2', 4, 0), ('Wipe the cupboard fronts', 'Kitchen', 'Fortnightly', 15, 'Child 1', 3, 0),
       ('Clean the fridge shelves', 'Kitchen', 'Fortnightly', 20, 'Adult 1', 4, 0), ('Vacuum the stairs', 'Hallway', 'Fortnightly', 15, 'Child 1', 3, 0),
       ('Clean the oven', 'Kitchen', 'Monthly', 40, 'Adult 1', 6, 0), ('Descale the kettle', 'Kitchen', 'Monthly', 10, 'Adult 2', 2, 0),
       ('Clean the washing machine drawer', 'Utility room', 'Monthly', 10, 'Adult 2', 2, 0), ('Scrub the bathroom grout', 'Bathroom', 'Monthly', 30, 'Adult 2', 5, 0),
       ('Wipe the skirting boards', 'Whole home', 'Monthly', 30, 'Adult 1', 4, 0), ('Vacuum under the furniture', 'Living room', 'Monthly', 25, 'Adult 1', 4, 0),
       ('Sort the post and paper pile', 'Hallway', 'Monthly', 15, 'Adult 1', 3, 1), ('Book appointments and school forms', 'Whole home', 'Monthly', 20, 'Adult 1', 4, 1),
       ('Check the kids clothes sizes', 'Kids room', 'Monthly', 20, 'Adult 1', 3, 1), ('Wash the pet bedding', 'Utility room', 'Monthly', 20, 'Adult 2', 3, 0),
       ('Clean the windows', 'Whole home', 'Quarterly', 60, 'Adult 1', 7, 0), ('Wash the curtains', 'Living room', 'Quarterly', 40, 'Adult 2', 5, 0),
       ('Deep clean the fridge freezer', 'Kitchen', 'Quarterly', 45, 'Adult 2', 6, 0), ('Tidy the garage', 'Garage', 'Quarterly', 60, 'Adult 1', 6, 0),
       ('Swap the seasonal wardrobe', 'Main bedroom', 'Twice a year', 60, 'Adult 1', 7, 0), ('Turn the mattresses', 'Main bedroom', 'Twice a year', 15, 'Adult 2', 3, 0),
       ('Sort the outgrown clothes', 'Kids room', 'Twice a year', 45, 'Adult 1', 5, 1),
       ('Deep clean the oven and extractor', 'Kitchen', 'Yearly', 90, 'Adult 2', 9, 0), ('Wash the outdoor furniture', 'Garden', 'Yearly', 45, 'Adult 1', 5, 0),
       ('Declutter the cupboards', 'Whole home', 'Yearly', 120, 'Adult 2', 9, 0)]
assert len(_CH) == 45


def _chores(w):
    r = rng('chores'); rows = []; occ = []
    for i, (nm, room, fq, mins, own, pts, hid) in enumerate(_CH):
        rows.append(dict(chore_id='CH-%02d' % (i + 1), chore=nm, room=room, frequency=fq, minutes=mins, owner=own, points=pts, hidden=bool(hid), last_done=''))
    for c in rows:
        step = FREQ_DAYS[c['frequency']]
        d = (TODAY - day(60) + day(r.randint(0, 3))) if step == 1 else HISTORY_START + day(r.randint(0, step - 1))
        while d <= TODAY:
            if not (c['chore'].startswith('Mow') and d.month not in (4, 5, 6, 7, 8, 9, 10)) and not (c['chore'].startswith('Wash the outdoor') and d.month not in (5, 6, 9)):
                occ.append([d, c])
            d += day(max(1, step + (r.randint(-1, 2) if step >= 7 else 0)))
    for i, (nm, room, fq, mins, own, pts, hid) in enumerate(_CH):
        c = rows[i]; mine = [o for o in occ if o[1] is c]
        if not mine: occ.append([TODAY - day(min(FREQ_DAYS[fq], 20)), c])
    occ.sort(key=lambda o: (o[0], o[1]['chore_id']))
    log = []
    for d, c in occ:
        o = c['owner']
        if c['hidden']: who = o if r.random() < .9 else ADULT2
        elif o.startswith('Child'): who = o if r.random() < .82 else (ADULT1 if r.random() < .5 else ADULT2)
        else:
            who = o
            if o == ADULT2 and _shift(d) == 'Late' and r.random() < .4: who = ADULT1
            elif o == ADULT1 and _late1(d) and r.random() < .5: who = ADULT2
        if d >= TODAY - day(50) and who in (ADULT1, ADULT2) and not c['hidden']:
            who = ADULT2 if r.random() < .72 else ADULT1
        log.append(dict(done=d, chore_id=c['chore_id'], chore=c['chore'], room=c['room'], who=who, minutes=int(round(c['minutes'] * r.uniform(.8, 1.2))), points=c['points'], _h=c['hidden']))

    def share():
        w30 = [x for x in log if x['done'] >= TODAY - day(29) and x['who'] in (ADULT1, ADULT2)]
        a2 = sum(x['minutes'] for x in w30 if x['who'] == ADULT2); a = sum(x['minutes'] for x in w30)
        return a2 / float(a) if a else 0.0
    cand = [x for x in log if x['done'] >= TODAY - day(29)]
    rf = rng('flip'); rf.shuffle(cand)
    for _ in range(600):
        s = share()
        if s < .64:
            f = [x for x in cand if x['who'] == ADULT1 and not x['_h']]
            if not f: break
            f[0]['who'] = ADULT2
        elif s > .66:
            f = [x for x in cand if x['who'] == ADULT2 and not x['_h']]
            if not f: break
            f[0]['who'] = ADULT1
        else: break
    last = {}
    for x in log: last[x['chore_id']] = x['done']
    for c in rows: c['last_done'] = iso(last[c['chore_id']])
    for i, x in enumerate(log):
        x['log_id'] = 'CL-%04d' % (i + 1); x['done'] = iso(x['done']); x.pop('_h')
    w['chores'] = rows; w['chore_log'] = log
    w['rewards'] = [dict(reward_id='RW-%02d' % (i + 1), reward=a, points=b) for i, (a, b) in enumerate(
        [('Choose the film for family night', 30), ('Pick the weekend breakfast', 45), ('Stay up 30 minutes later on a weekend', 60), ('Choose a day out', 90), ('Pick a small toy or book', 120),
         ('Invite a friend for a sleepover', 150)])]


# ------------------------------------------------------------------ maintenance
# task | area | interval days | season | assigned | typical cost | anchor (month, day) or None
_MT = [('Furnace or boiler filter change', 'Heating and air', 90, 'Any season', 'Adult 1', 18, None), ('Heating system service', 'Heating and air', 365, 'Autumn', 'A trade', 130, (10, 3)),
       ('Bleed radiators or clean the vents', 'Heating and air', 365, 'Autumn', 'Adult 2', 0, (10, 10)), ('Check the thermostat batteries', 'Heating and air', 365, 'Winter', 'Adult 1', 6, (11, 20)),
       ('Service the cooling units or fans', 'Heating and air', 365, 'Spring', 'A trade', 90, (4, 20)), ('Test the smoke alarms', 'Electrics and alarms', 30, 'Any season', 'Adult 1', 0, None),
       ('Change the alarm batteries', 'Electrics and alarms', 182, 'Any season', 'Adult 2', 12, None), ('Test the carbon monoxide alarm', 'Electrics and alarms', 30, 'Any season', 'Adult 2', 0, None),
       ('Test the fuse box switches', 'Electrics and alarms', 365, 'Winter', 'Adult 1', 0, (1, 15)), ('Check outdoor lights and bulbs', 'Electrics and alarms', 182, 'Any season', 'Adult 2', 10, None),
       ('Electrical safety check by a trade', 'Electrics and alarms', 1825, 'Any season', 'A trade', 180, None), ('Clean the gutters and downspouts', 'Roof and gutters', 182, 'Any season', 'Adult 2', 0, (10, 20)),
       ('Look over the roof from the ground', 'Roof and gutters', 365, 'Spring', 'Adult 2', 0, (4, 8)), ('Roof and chimney inspection by a trade', 'Roof and gutters', 730, 'Autumn', 'A trade', 160, (9, 25)),
       ('Clear moss from the paths', 'Garden and outdoors', 365, 'Spring', 'Adult 2', 0, (4, 25)), ('Service the lawn mower', 'Garden and outdoors', 365, 'Spring', 'Adult 2', 45, (3, 15)),
       ('Prune the shrubs and hedge', 'Garden and outdoors', 182, 'Any season', 'Adult 2', 0, None), ('Drain the outdoor taps for winter', 'Plumbing', 365, 'Autumn', 'Adult 1', 0, (11, 1)),
       ('Clean and store the outdoor furniture', 'Garden and outdoors', 365, 'Autumn', 'Adult 1', 0, (9, 20)), ('Weed and refresh the garden bed', 'Garden and outdoors', 365, 'Spring', 'Adult 2', 25, (5, 5)),
       ('Check the fence and gate', 'Garden and outdoors', 365, 'Spring', 'Adult 2', 0, (4, 15)), ('Clean the dishwasher filter', 'Appliances', 30, 'Any season', 'Adult 1', 0, None),
       ('Descale the washing machine and dishwasher', 'Appliances', 90, 'Any season', 'Adult 2', 6, None), ('Clean the washing machine drum and seal', 'Appliances', 30, 'Any season', 'Adult 2', 0, None),
       ('Clear the dryer vent', 'Appliances', 365, 'Spring', 'Adult 1', 0, (3, 10)), ('Vacuum the back of the fridge', 'Appliances', 182, 'Any season', 'Adult 1', 0, None),
       ('Replace the water filter cartridge', 'Kitchen', 90, 'Any season', 'Adult 2', 22, None), ('Deep clean the oven and hob', 'Kitchen', 182, 'Any season', 'Adult 1', 12, None),
       ('Replace the vacuum cleaner bag or filter', 'Appliances', 90, 'Any season', 'Adult 1', 9, None), ('Defrost and check the chest freezer seal', 'Appliances', 365, 'Spring', 'Adult 2', 0, (5, 2)),
       ('Service the water heater', 'Plumbing', 730, 'Any season', 'A trade', 110, None), ('Check under the sinks for leaks', 'Plumbing', 90, 'Any season', 'Adult 2', 0, None),
       ('Clear the drains and plugs', 'Plumbing', 182, 'Any season', 'Adult 1', 6, None), ('Check the outside drain and sump pump', 'Plumbing', 365, 'Autumn', 'Adult 2', 0, (10, 28)),
       ('Check the main water shut-off valve', 'Plumbing', 365, 'Winter', 'Adult 1', 0, (1, 8)), ('Re-seal the bathroom silicone', 'Bathroom', 730, 'Any season', 'Adult 2', 15, None),
       ('Check the bathroom extractor fan', 'Bathroom', 365, 'Any season', 'Adult 1', 0, None), ('Clean the grout and tiles', 'Bathroom', 182, 'Any season', 'Adult 2', 8, None),
       ('Oil the door hinges and locks', 'Windows and doors', 365, 'Autumn', 'Adult 1', 4, (9, 12)), ('Check the window seals', 'Windows and doors', 365, 'Autumn', 'Adult 2', 0, (10, 15)),
       ('Clean the window tracks', 'Windows and doors', 182, 'Any season', 'Adult 2', 0, None), ('Check the door and window locks', 'Windows and doors', 365, 'Winter', 'Adult 1', 0, (12, 5)),
       ('Touch up paint and fill small holes', 'Floors and walls', 365, 'Spring', 'Adult 1', 25, (4, 5)), ('Deep clean the carpets and rugs', 'Floors and walls', 365, 'Spring', 'A trade', 85, (4, 12)),
       ('Re-oil the wooden floors or worktops', 'Floors and walls', 365, 'Winter', 'Adult 2', 20, (2, 1)), ('Review the escape plan with the children', 'Safety checks', 365, 'Autumn', 'Adult 1', 0, (9, 5)),
       ('Check the torches and spare batteries', 'Safety checks', 182, 'Any season', 'Adult 2', 8, None), ('Check the loft insulation and storage', 'Roof and gutters', 365, 'Autumn', 'Adult 1', 0, (11, 10)),
       ('Test the garage door and its release', 'Windows and doors', 365, 'Spring', 'Adult 2', 0, (3, 28)), ('Chimney or flue sweep', 'Heating and air', 365, 'Autumn', 'A trade', 70, (9, 15))]
assert len(_MT) == 50
_TRADE_BY_AREA = {'Heating and air': 'Heating engineer', 'Electrics and alarms': 'Electrician', 'Plumbing': 'Plumber', 'Roof and gutters': 'Roofer', 'Appliances': 'Appliance repairer'}


def _maint(w):
    r = rng('maint'); rows = []; log = []
    for i, (nm, area, iv, se, who, cost, anc) in enumerate(_MT):
        if nm == 'Furnace or boiler filter change': off = -21
        elif nm == 'Test the smoke alarms': off = 5
        elif anc:
            nd = next_on(anc[0], anc[1]); off = (nd - TODAY).days; la = last_on(anc[0], anc[1])
            if 0 < (TODAY - la).days <= 16 and i % 2 == 0: off = -(TODAY - la).days
        else: off = int(-22 + ((i * 53) % 100) / 100.0 * (min(iv, 400) + 22))
        due = TODAY + day(off); last = due - day(iv)
        if last > TODAY - day(2): last = TODAY - day(2)
        rows.append(dict(task_id='MT-%02d' % (i + 1), task=nm, area=area, season=se, interval_days=iv, assigned=who, typical_cost=float(cost), trade=_TRADE_BY_AREA.get(area, 'Handyman') if who == 'A trade' else '',
                         last_done=iso(last), step=iv))
        d = last; k = 0
        while d >= HISTORY_START:
            dd = d if k == 0 else d + day(r.randint(-5, 5))
            if dd <= TODAY and dd >= HISTORY_START:
                log.append(dict(task_id='MT-%02d' % (i + 1), task=nm, done=dd, who=who if who != 'Landlord request' else 'A trade', cost=R2(cost * r.uniform(.9, 1.15)) if cost else 0.0,
                                note=r.choice(['Done as planned', 'Done as planned', 'Done, next one earlier', 'Done, part replaced', 'Done with the child helping']) if who != 'A trade' else 'Trade visit done'))
            d -= day(iv); k += 1
    log.sort(key=lambda x: (x['done'], x['task_id']))
    for i, x in enumerate(log): x['log_id'] = 'ML-%04d' % (i + 1); x['done'] = iso(x['done'])
    for x in rows: x.pop('step')
    w['maintenance'] = rows; w['maintenance_log'] = log


# ------------------------------------------------------------------ inventory
# room: name:price:warranty years;...
_INV = """Kitchen|Fridge freezer:780:2;Dishwasher:520:2;Oven:640:2;Induction hob:410:2;Microwave:110:1;Kettle:35:1;Toaster:40:1;Coffee maker:95:2;Blender:70:2;Stand mixer:260:2;Air fryer:120:2;Slow cooker:55:1;Food processor:130:2;Rice cooker:60:1;Extractor hood:230:2;Cookware set:240:5;Knife set:120:0;Dinner set:150:0;Water filter jug:30:0;Digital kitchen scales:25:1;Toastie maker:40:1;Juicer:65:1
Utility room|Washing machine:520:2;Tumble dryer:480:2;Iron and ironing board:90:2;Vacuum cleaner:260:3;Steam mop:80:2;Boiler or furnace:1900:5;Drying rack:35:0
Living room|Sofa:1150:3;Armchair:420:3;Television:690:3;Sound bar:210:2;Games console:360:1;Coffee table:190:1;Bookshelf:140:0;Rug:230:0;Floor lamp:75:1;Wi-Fi router:90:2;Electric fan:45:1;Space heater:70:2;Table lamp:45:1;Picture frames set:40:0;Games table:120:1
Main bedroom|Bed frame:480:2;Mattress:760:5;Wardrobe:520:2;Chest of drawers:260:2;Bedside lamps:60:1;Hairdryer:55:2;Laptop, Adult 1:1150:2;Tablet:340:1;Wall mirror:90:0;Bedside radio:40:1;Duvet and pillows set:120:0;Bedside table pair:150:1
Kids room|Bunk bed:540:3;Desk:150:1;Desk chair:95:1;Bookcase:110:0;Toy storage:70:0;Child 1 laptop for school:560:2;Headphones:60:1;Night light:20:1;Scooter:60:1;Craft box:35:0;Child 2 tablet:180:1;Beanbag:50:0;Board game shelf:45:0;Study lamp:30:1;Wall shelf:30:0
Bathroom|Heated towel rail:210:2;Electric toothbrush set:130:2;Bathroom scales:30:1;Mirror cabinet:150:2;Shower pump:260:3;Washing basket:25:0
Hallway|Shoe cabinet:130:0;Coat rack:60:0;Doorbell camera:110:1;Smart thermostat:190:2;Robot vacuum:320:2
Garden|Lawn mower:380:3;Grass trimmer:110:2;Garden table set:430:2;Barbecue:290:2;Hose reel:60:2;Pressure washer:190:2;Garden tool set:90:0;Hedge trimmer:130:2;Wheelbarrow:70:1;Greenhouse:340:5;Compost bin:45:0;Parasol:80:1;Trampoline:210:2;Garden lights set:50:1;Water butt:45:0
Garage|Cordless drill set:170:3;Toolbox:90:0;Ladder:140:2;Roof box:260:2;Bicycle, Adult 1:620:2;Bicycle, Adult 2:540:2;Bicycle, Child 1:210:1;Chest freezer:360:2;Workbench:150:1;Bike pump:25:0;Jump starter:70:1;Tyre pump:35:1
Whole home|Smoke alarm set:75:5;Printer:140:1;Sewing machine:160:2;Camping tent:280:2;Suitcase set:190:2;Vacuum flask set:35:0;Guitar:210:1;Keyboard piano:320:2;Football goal:60:0;Cordless handheld vacuum:110:2;Portable speaker:90:1"""
_WARR = {'Washing machine': 30, 'Dishwasher': 64, 'Television': 83, 'Tumble dryer': -22, 'Games console': 41, 'Coffee maker': 57, 'Laptop, Adult 1': -15, 'Air fryer': 665, 'Robot vacuum': 76,
         'Pressure washer': 7, 'Tablet': -40, 'Doorbell camera': 18, 'Stand mixer': 400}
_MANUAL = ['Kitchen drawer, manuals folder', 'Filing box A, folder 3', 'Shed shelf, blue box', 'Online, saved copy', 'Filing box B, folder 1', 'Utility room shelf', 'Garage, manual tray', 'With the item']


def _inventory(w):
    r = rng('inventory'); rows = []
    for ln in _INV.split('\n'):
        room, items = ln.split('|')
        for it in items.split(';'):
            nm, pr, wy = it.rsplit(':', 2); pr = float(pr); wy = int(wy)
            cat = ('Appliance' if room in ('Kitchen', 'Utility room') and wy >= 1 and pr > 90 else 'Kitchenware' if room == 'Kitchen' else 'Electronics' if any(k in nm for k in ('Laptop', 'Tablet', 'Television', 'Games', 'router', 'Printer', 'Headphones', 'Sound', 'camera', 'thermostat', 'toothbrush', 'radio')) else
                   'Furniture' if any(k in nm for k in ('Sofa', 'Armchair', 'table', 'bed', 'Bed', 'Wardrobe', 'drawers', 'Desk', 'Bookcase', 'Bookshelf', 'cabinet', 'rack', 'Beanbag', 'Workbench', 'storage', 'shelf')) else
                   'Garden' if room == 'Garden' else 'Tools' if room == 'Garage' and any(k in nm for k in ('drill', 'Toolbox', 'Ladder', 'pump')) else 'Sports and toys' if any(k in nm for k in ('Scooter', 'Bicycle', 'goal', 'tent', 'Board', 'Craft', 'Guitar', 'Keyboard', 'Trampoline')) else
                   'Lighting' if 'lamp' in nm or 'light' in nm.lower() else 'Bedding and linen' if 'Mattress' in nm or 'Rug' in nm else 'Other')
            if nm in _WARR:
                wend = TODAY + day(_WARR[nm]); pd = wend - day(365 * wy) if wy else TODAY - day(r.randint(100, 900))
            else:
                age = r.choice((r.randint(20, 400), r.randint(400, 1500), r.randint(1500, 3600)))
                pd = TODAY - day(age); wend = pd + day(365 * wy) if wy else None
            if nm == 'Air fryer': pd = TODAY - day(9); wend = pd + day(730)
            if nm == 'Pressure washer': pd = TODAY - day(2 * 365 - 7); wend = TODAY + day(7)
            if pd > TODAY: pd = TODAY - day(3)
            rows.append(dict(item=nm, room=room, category=cat, purchase_date=pd, price=pr, serial=('SN-%05d-%s' % (r.randint(10000, 99999), 'ABCDEFGH'[r.randint(0, 7)])) if wy and r.random() < .85 else '',
                             warranty_end=wend if wend else '', receipt_date=(pd + day(r.randint(0, 2))) if r.random() < .7 else '', manual_place=r.choice(_MANUAL) if wy else 'None kept'))
    rows.sort(key=lambda x: (x['purchase_date'], x['item']))
    for i, x in enumerate(rows):
        x['item_id'] = 'IV-%03d' % (i + 1); x['purchase_date'] = iso(x['purchase_date']); x['warranty_end'] = iso(x['warranty_end']) if x['warranty_end'] != '' else ''
        x['receipt_date'] = iso(x['receipt_date']) if x['receipt_date'] != '' else ''
    w['inventory'] = rows
    assert len(rows) == 120, len(rows)


# ------------------------------------------------------------------ repairs
_RP = [('Dripping kitchen tap', 'Kitchen', 'Plumber', 85), ('Blocked bathroom sink', 'Bathroom', 'Plumber', 70), ('Loose toilet seat fitting', 'Bathroom', 'Self repair', 8),
       ('Socket in the kids room stopped working', 'Kids room', 'Electrician', 95), ('Hallway light flickers', 'Hallway', 'Electrician', 60), ('Radiator not heating at the top', 'Living room', 'Heating engineer', 90),
       ('Dishwasher door seal leaks', 'Kitchen', 'Appliance repairer', 75), ('Garden gate latch broken', 'Garden', 'Handyman', 45), ('Gutter joint leaking', 'Garden', 'Roofer', 140),
       ('Bathroom extractor fan noisy', 'Bathroom', 'Electrician', 80), ('Shower leaks behind the tiles', 'Bathroom', 'Plumber', 260), ('Front door lock stiff', 'Hallway', 'Locksmith', 90),
       ('Oven fan stopped', 'Kitchen', 'Appliance repairer', 130), ('Squeaking bedroom door', 'Main bedroom', 'Self repair', 4), ('Mice in the garage', 'Garage', 'Pest controller', 120),
       ('Boiler or furnace pressure dropping', 'Utility room', 'Heating engineer', 150), ('Cracked window pane in the kids room', 'Kids room', 'Handyman', 110), ('Kitchen cabinet hinge broken', 'Kitchen', 'Self repair', 12),
       ('Overflow pipe dripping outside', 'Garden', 'Plumber', 95), ('Garage door sticks', 'Garage', 'Handyman', 70), ('Bathroom sink slow to drain again', 'Bathroom', 'Plumber', 65),
       ('Fridge door light out', 'Kitchen', 'Self repair', 6), ('Outdoor light needs a new fitting', 'Garden', 'Electrician', 85), ('Dishwasher pump noisy', 'Kitchen', 'Appliance repairer', 95)]


def _repairs(w):
    r = rng('repairs'); rows = []
    for i in range(36):
        t = _RP[(i * 7) % len(_RP)] if i >= len(_RP) else _RP[i]
        d = TODAY - day(int(715 - i * 19.3 + r.randint(-6, 6)))
        if d < HISTORY_START: d = HISTORY_START + day(i)
        cost = R2(t[3] * r.uniform(.8, 1.3)); fixed = d + day(r.randint(0, 9)) if t[2] != 'Landlord request' else d + day(14)
        rows.append(dict(date=d, room=t[1], issue=t[0], trade=t[2], quote=R2(cost * r.uniform(.9, 1.15)) if t[2] != 'Self repair' else 0.0, cost=cost, status='Fixed', fixed_on=fixed, warranty_used=bool(i % 11 == 7), item_id=''))
    # recent and open rows
    rows.append(dict(date=TODAY - day(20), room='Kitchen', issue='Cabinet hinge replaced', trade='Self repair', quote=0.0, cost=7.5, status='Fixed', fixed_on=TODAY - day(19), warranty_used=False, item_id=''))
    rows.append(dict(date=TODAY - day(9), room='Bathroom', issue='Bathroom tap dripping again', trade='Plumber', quote=75.0, cost=0.0, status='Open', fixed_on='', warranty_used=False, item_id=''))
    rows.append(dict(date=TODAY - day(35), room='Garden', issue='Fence panel loose after wind', trade='Handyman', quote=90.0, cost=0.0, status='Waiting', fixed_on='', warranty_used=False, item_id=''))
    wm = [x for x in w['inventory'] if x['item'] == 'Washing machine'][0]['item_id']
    rows.append(dict(date=TODAY - day(12), room='Utility room', issue='Washing machine does not drain', trade='Appliance repairer', quote=0.0, cost=0.0, status='Waiting', fixed_on='', warranty_used=False, item_id=wm))
    ink = {'Dishwasher door seal leaks': 'Dishwasher', 'Dishwasher pump noisy': 'Dishwasher', 'Oven fan stopped': 'Oven', 'Fridge door light out': 'Fridge freezer', 'Boiler or furnace pressure dropping': 'Boiler or furnace'}
    ids = {x['item']: x['item_id'] for x in w['inventory']}
    for x in rows:
        if x['issue'] in ink: x['item_id'] = ids[ink[x['issue']]]
    rows.sort(key=lambda x: x['date'])
    for i, x in enumerate(rows): x['repair_id'] = 'RP-%03d' % (i + 1); x['date'] = iso(x['date']); x['fixed_on'] = iso(x['fixed_on']) if x['fixed_on'] != '' else ''
    w['repairs'] = rows


# ------------------------------------------------------------------ calendar
def _drv(d, k, w):
    f = [a for a in (ADULT1, ADULT2) if not (a == ADULT1 and _late1(d)) and not (a == ADULT2 and _shift(d) == 'Late')]
    wk = d.toordinal() // 7
    if len(f) == 2: return (f[(wk + k) % 2], False)
    if len(f) == 1: return (f[0], False)
    if _visit(d): return ('Grandparent', False)
    return ('Carpool family', True)


BIRTHDAYS = [('Jo', 'Child 1', 3, 14, CHILD_AGES[0]), ('Kit', 'Child 2', 9, 9, CHILD_AGES[1]), ('Sam', 'Adult 1', 6, 2, 39), ('Riley', 'Adult 2', 11, 27, 37), ('Ada', 'Grandparent', 1, 21, 68),
             ('Cousin Mia', 'Family', 8, 18, 9), ('Aunt Lena', 'Family', 12, 9, 61), ('Friend Omar', 'Friend', 10, 4, 12), ('Friend Zoe', 'Friend', 2, 12, 6), ('Uncle Femi', 'Family', 5, 30, 64),
             ('Cousin Tobi', 'Family', 7, 11, 14), ('Neighbour Chidi', 'Neighbour', 4, 3, None)]


def _events(w):
    r = rng('events'); ev = []

    def add(d, person, kind, title, st, en, place, driver='', carpool=False, end=None):
        ev.append(dict(date=d, end_date=end or d, person=person, kind=kind, title=title, start=st, end=en, place=place, driver=driver, carpool=carpool))
    d = HISTORY_START
    while d <= FUTURE_END:
        wd = d.weekday(); term = not _in_break(d, w); wk = d.toordinal() // 7
        if term and wd < 5:
            if wd == 0: add(d, 'Child 2', 'Activity', 'Art club', '15:45', '16:45', 'School hall', *_drv(d, 0, w))
            if wd == 1:
                dr, cp = _drv(d, 1, w)
                if wk % 3 == 0: dr, cp = 'Carpool family', True
                add(d, 'Child 1', 'Activity', 'Football practice', '17:30', '18:30', 'Sports field', dr, cp)
            if wd == 2: add(d, 'Child 2', 'Activity', 'Swimming lesson', '16:30', '17:15', 'Leisure pool', *_drv(d, 0, w))
            if wd == 3: add(d, 'Child 1', 'Activity', 'Piano lesson', '16:30', '17:15', 'Music school', *_drv(d, 1, w))
        if _visit(d): add(d, 'Whole household', 'Visit', 'Grandparent visit and school pick-up', '14:30', '18:00', 'Home', 'Grandparent')
        if wd == 4 and (d.day - 1) // 7 == 2 and d != TODAY: add(d, 'Adult 1', 'Visit', 'Babysitter evening', '18:30', '23:00', 'Home', '')
        d += day(1)
    for yy in (Y - 2, Y - 1, Y, Y + 1):
        for nm, rel, m, dd, age in BIRTHDAYS:
            x = _dd(yy, m, dd)
            if HISTORY_START <= x <= FUTURE_END: add(x, 'Whole household', 'Birthday', 'Birthday: %s' % nm, '10:00', '11:00', 'Home' if rel in ('Child 1', 'Child 2') else 'Visit or call', '')
        for a, b, tt, pl in ((D(yy, 7, 26), D(yy, 8, 9), 'Summer holiday by the sea', 'Coast'), (D(yy, 12, 23), D(yy, 12, 28), 'Winter holiday with relatives', 'Relatives'),
                             (D(yy, 4, 2), D(yy, 4, 6), 'Spring break weekend away', 'Countryside'), (D(yy, 10, 28), D(yy, 10, 30), 'Mid-term days out', 'Local')):
            if HISTORY_START <= a <= FUTURE_END: add(a, 'Whole household', 'Holiday', tt, '08:00', '18:00', pl, '', False, b)
        for x, kind, tt, st, en, pl, pp in ((D(yy, 9, 2), 'School', 'First day of the autumn term', '08:30', '15:30', 'School', 'Whole household'), (D(yy, 1, 6), 'School', 'First day of the spring term', '08:30', '15:30', 'School', 'Whole household'),
                                           (D(yy, 4, 14), 'School', 'First day of the summer term', '08:30', '15:30', 'School', 'Whole household'), (D(yy, 3, 12), 'Appointment', 'Parent-teacher meeting', '17:00', '17:30', 'School', 'Adult 1'),
                                           (D(yy, 10, 15), 'Appointment', 'Parent-teacher meeting', '17:00', '17:30', 'School', 'Adult 2'), (D(yy, 6, 19), 'School', 'Sports day', '13:00', '15:30', 'School field', 'Child 2'),
                                           (D(yy, 12, 12), 'School', 'School concert', '18:00', '19:30', 'School hall', 'Child 1'), (D(yy, 10, 3), 'Household', 'Heating system service visit', '09:00', '11:00', 'Home', 'Adult 1'),
                                           (D(yy, 8, 24), 'Household', 'Back-to-school shopping', '10:00', '13:00', 'Town', 'Whole household'), (D(yy, 3, 22), 'Household', 'Spring clean weekend', '09:00', '15:00', 'Home', 'Whole household'),
                                           (D(yy, 4, 26), 'Household', 'Garden work day', '10:00', '15:00', 'Garden', 'Whole household'), (D(yy, 12, 18), 'Household', 'Deep clean before guests', '09:00', '13:00', 'Home', 'Whole household')):
            while x.weekday() >= 5 and kind in ('School', 'Appointment'): x += day(1) if x.weekday() == 5 else day(1)
            if HISTORY_START <= x <= FUTURE_END: add(x, pp, kind, tt, st, en, pl, '')
    # story: next Thursday two children's activities overlap, only adult 2 is free
    add(OVERLAP_DAY, 'Child 1', 'Activity', 'Football match', '17:30', '19:00', 'Sports ground', ADULT2)
    add(OVERLAP_DAY, 'Child 2', 'Appointment', 'Friend birthday party', '17:45', '19:15', 'Party venue', ADULT2)
    add(TRIP_START, 'Whole household', 'Trip', 'Family trip abroad', '06:00', '22:00', 'Airport', ADULT1, False, TRIP_START + day(7))
    ev.sort(key=lambda x: (x['date'], x['start'], x['title']))
    out = []
    for i, x in enumerate(ev):
        out.append(dict(event_id='EV-%04d' % (i + 1), date=iso(x['date']), end_date=iso(x['end_date']), person=x['person'], kind=x['kind'], title=x['title'], start=x['start'], end=x['end'], place=x['place'],
                        driver=x['driver'], carpool=x['carpool']))
    w['events'] = out
    gifts = []
    gi = [('Jo', 'a sports bag'), ('Kit', 'a building set'), ('Sam', 'a book on gardening'), ('Riley', 'a new scarf'), ('Ada', 'a framed family photo'), ('Cousin Mia', 'art supplies'), ('Aunt Lena', 'a plant'),
          ('Friend Omar', 'a board game'), ('Friend Zoe', 'a picture book'), ('Uncle Femi', 'a cookbook'), ('Cousin Tobi', 'a football'), ('Neighbour Chidi', 'a bottle of juice')]
    for i, (nm, rel, m, dd, age) in enumerate(BIRTHDAYS):
        nd = next_on(m, dd); left = (nd - TODAY).days
        st = 'Wrapped' if left <= 10 else 'Bought' if left <= 30 else 'Idea'
        by = nd.year - (Y - age) if age is not None else ''
        gifts.append(dict(name=nm, relation=rel, date=iso(nd), age_turning=(age + (1 if nd.year > Y else 0)) if age is not None else '', gift_idea=gi[i][1], status=st, cost=R2(10 + (i * 13) % 45)))
    for j, (nm, rel, m, dd, idea, cost) in enumerate((('Teacher A', 'Teacher', 12, 15, 'a thank-you card', 4.0), ('Teacher B', 'Teacher', 12, 15, 'a small plant', 9.0), ('Hosts of the dinner', 'Friend', 12, 21, 'a box of sweets', 12.0),
                                                     ('Grandparent', 'Family', 12, 24, 'a photo book', 25.0))):
        nd = next_on(m, dd); left = (nd - TODAY).days
        gifts.append(dict(name=nm, relation=rel, date=iso(nd), age_turning='', gift_idea=idea, status='Wrapped' if left <= 10 else 'Bought' if left <= 30 else 'Idea', cost=cost))
    for i, x in enumerate(gifts): x['gift_id'] = 'GF-%02d' % (i + 1)
    w['gifts'] = gifts


# ------------------------------------------------------------------ pets
def _pets(w):
    r = rng('pets')
    w['pets'] = [dict(pet_id='PT-01', pet='Bruno', species='Dog', birth_year=Y - 5, daily_food_g=320, bag_kg=7.5, food_stock_kg=0.0, vet_next=iso(TODAY + day(40)), groom_every_days=56, last_groom=''),
                 dict(pet_id='PT-02', pet='Pip', species='Cat', birth_year=Y - 8, daily_food_g=70, bag_kg=2.0, food_stock_kg=0.0, vet_next=iso(TODAY + day(75)), groom_every_days=0, last_groom='')]
    log = []

    def add(pid, d, task, qty=0.0, cost=0.0, booked=False):
        if HISTORY_START <= d <= FUTURE_END: log.append(dict(pet_id=pid, pet='Bruno' if pid == 'PT-01' else 'Pip', date=d, task=task, qty_kg=qty, cost=cost, booked=booked))
    for pid, every, last, bag in (('PT-01', 23, TODAY - day(9), 7.5), ('PT-02', 28, TODAY - day(18), 2.0)):
        d = last
        while d >= HISTORY_START: add(pid, d, 'Food bag bought', bag, R2(15.0 if bag > 5 else 8.5), False); d -= day(every + r.randint(-1, 2))
    d = TODAY - day(30)
    while d >= HISTORY_START: add('PT-01', d, 'Grooming', 0.0, R2(r.uniform(32, 42))); add('PT-01', d, 'Nail trim', 0.0, 8.0) if r.random() < .4 else None; d -= day(56 + r.randint(-3, 4))
    add('PT-01', TODAY + day(26), 'Grooming', 0.0, 0.0, True)
    d = TODAY - day(14)
    while d >= HISTORY_START: add('PT-01', d, 'Bath', 0.0, 0.0); d -= day(30 + r.randint(-3, 3))
    for pid, vv in (('PT-01', (TODAY - day(142), TODAY - day(322), TODAY - day(505), TODAY - day(690))), ('PT-02', (TODAY - day(107), TODAY - day(290), TODAY - day(470), TODAY - day(650)))):
        for k, d in enumerate(vv): add(pid, d, 'Vet visit', 0.0, R2(r.uniform(45, 85)))
    for pid, d in (('PT-01', TODAY - day(165)), ('PT-01', TODAY - day(530)), ('PT-02', TODAY - day(280)), ('PT-02', TODAY - day(645))): add(pid, d, 'Vaccination visit', 0.0, R2(r.uniform(35, 60)))
    add('PT-01', TODAY + day(40), 'Vet visit', 0.0, 0.0, True); add('PT-02', TODAY + day(75), 'Vet visit', 0.0, 0.0, True); add('PT-02', TODAY + day(85), 'Vaccination visit', 0.0, 0.0, True)
    d = TODAY - day(60)
    while d >= HISTORY_START: add('PT-02', d, 'Nail trim', 0.0, 0.0); d -= day(60)
    log.sort(key=lambda x: (x['date'], x['pet_id'], x['task']))
    for i, x in enumerate(log): x['care_id'] = 'PC-%04d' % (i + 1); x['date'] = iso(x['date'])
    for p in w['pets']:
        bags = [x for x in log if x['pet_id'] == p['pet_id'] and x['task'] == 'Food bag bought' and x['date'] <= iso(TODAY)]
        lastd = to_date(bags[-1]['date']); p['food_stock_kg'] = round(max(0.2, p['bag_kg'] - p['daily_food_g'] / 1000.0 * (TODAY - lastd).days), 2)
        gr = [x for x in log if x['pet_id'] == p['pet_id'] and x['task'] == 'Grooming' and x['date'] <= iso(TODAY)]
        p['last_groom'] = gr[-1]['date'] if gr else ''
    w['pet_care'] = log


# ------------------------------------------------------------------ vehicles
def _vehicles(w):
    r = rng('veh')
    V = [dict(vehicle_id='VH-01', vehicle='Family car', year=Y - 5, mileage_now=61800, monthly_km=950, service_km=12000, service_days=365, last_service=TODAY - day(170), last_service_km=0, tyres_changed=TODAY - day(420),
              insurance_renewal=TODAY + day(58), registration_renewal=TODAY + day(120), inspection_due=TODAY + day(33)),
         dict(vehicle_id='VH-02', vehicle='Older second car', year=Y - 14, mileage_now=148500, monthly_km=480, service_km=10000, service_days=365, last_service=TODAY - day(250), last_service_km=0, tyres_changed=TODAY - day(640),
              insurance_renewal=TODAY + day(201), registration_renewal=TODAY + day(260), inspection_due=TODAY + day(96))]
    log = []
    for v in V:
        v['last_service_km'] = int(v['mileage_now'] - v['monthly_km'] * 170 / 30.4) if v['vehicle_id'] == 'VH-01' else int(v['mileage_now'] - v['monthly_km'] * 250 / 30.4)

        def km_at(d): return int(v['mileage_now'] - v['monthly_km'] * (TODAY - d).days / 30.4 + r.randint(-60, 60))
        m = month_start(24)
        while m <= month_start(0):
            d = m + day(r.randint(0, 2))
            if d <= TODAY: log.append(dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], date=d, kind='Mileage reading', km=km_at(d), cost=0.0, who='Adult 1' if v['vehicle_id'] == 'VH-01' else 'Adult 2'))
            m = add_months(m, 1)
        log.append(dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], date=TODAY - day(3), kind='Mileage reading', km=km_at(TODAY - day(3)), cost=0.0, who='Adult 1' if v['vehicle_id'] == 'VH-01' else 'Adult 2'))
        mk = 'family' if v['vehicle_id'] == 'VH-01' else 'older'
        for k in range(0, 3):
            for kind, d0, cost in (('Service', v['last_service'], 240 if mk == 'family' else 165), ('Annual test', v['inspection_due'] - day(365), 55), ('Insurance renewal', v['insurance_renewal'] - day(365), 640 if mk == 'family' else 380),
                                   ('Registration renewal', v['registration_renewal'] - day(365), 190 if mk == 'family' else 120)):
                d = d0 - day(365 * k)
                if HISTORY_START <= d <= TODAY: log.append(dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], date=d, kind=kind, km=km_at(d), cost=R2(cost * r.uniform(.93, 1.08)), who='Car mechanic' if kind in ('Service', 'Annual test') else 'Adult 1'))
        if v['tyres_changed'] >= HISTORY_START: log.append(dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], date=v['tyres_changed'], kind='Tyres', km=km_at(v['tyres_changed']), cost=R2(480 if mk == 'family' else 260), who='Car mechanic'))
    log.append(dict(vehicle_id='VH-02', vehicle='Older second car', date=TODAY - day(95), kind='Repair', km=int(148500 - 480 * 95 / 30.4), cost=185.0, who='Car mechanic'))
    log.append(dict(vehicle_id='VH-01', vehicle='Family car', date=TODAY - day(310), kind='Repair', km=int(61800 - 950 * 310 / 30.4), cost=90.0, who='Car mechanic'))
    log.sort(key=lambda x: (x['date'], x['vehicle_id'], x['kind']))
    for i, x in enumerate(log): x['log_id'] = 'VL-%04d' % (i + 1); x['date'] = iso(x['date'])
    for v in V:
        for k in ('last_service', 'tyres_changed', 'insurance_renewal', 'registration_renewal', 'inspection_due'): v[k] = iso(v[k])
    w['vehicles'] = V; w['vehicle_log'] = log


# ------------------------------------------------------------------ documents and contacts
def _docs(w):
    v = {x['vehicle_id']: x for x in w['vehicles']}
    wm = [x for x in w['inventory'] if x['item'] == 'Washing machine'][0]; dw = [x for x in w['inventory'] if x['item'] == 'Dishwasher'][0]
    D_ = [('Travel document, Adult 1', 'Travel document', 'Adult 1', 420, 60), ('Travel document, Adult 2', 'Travel document', 'Adult 2', 880, 60),
          ('Travel document, Child 1', 'Travel document', 'Child 1', 55, 60), ('Travel document, Child 2', 'Travel document', 'Child 2', 1180, 60),
          ('Driving licence, Adult 1', 'Licence', 'Adult 1', 690, 45), ('Driving licence, Adult 2', 'Licence', 'Adult 2', 1520, 45),
          ('Car insurance policy, family car', 'Policy', 'Whole household', (to_date(v['VH-01']['insurance_renewal']) - TODAY).days, 30),
          ('Car insurance policy, older car', 'Policy', 'Whole household', (to_date(v['VH-02']['insurance_renewal']) - TODAY).days, 30),
          ('Home buildings and contents policy', 'Policy', 'Whole household', 133, 45), ('Pet insurance policy, dog', 'Policy', 'Whole household', 95, 30), ('Pet insurance policy, cat', 'Policy', 'Whole household', 242, 30),
          ('Travel insurance, yearly policy', 'Policy', 'Whole household', 310, 30), ('Breakdown cover', 'Policy', 'Whole household', 208, 30), ('Broadband contract', 'Contract', 'Whole household', 76, 30),
          ('Energy supply contract', 'Contract', 'Whole household', 162, 45), ('Mobile contract, Adult 1', 'Contract', 'Adult 1', 118, 30), ('Mobile contract, Adult 2', 'Contract', 'Adult 2', 191, 30),
          ('Garden waste collection', 'Contract', 'Whole household', 41, 14), ('Home alarm service contract', 'Contract', 'Whole household', 280, 30), ('Window cleaner agreement', 'Contract', 'Whole household', 150, 14),
          ('Heating system service plan', 'Contract', 'Whole household', 332, 45), ('Boiler guarantee paper', 'Warranty paper', 'Whole household', 410, 0), ('Roof guarantee paper', 'Warranty paper', 'Whole household', 1900, 0),
          ('Washing machine warranty paper', 'Warranty paper', 'Whole household', (to_date(wm['warranty_end']) - TODAY).days, 0), ('Dishwasher warranty paper', 'Warranty paper', 'Whole household', (to_date(dw['warranty_end']) - TODAY).days, 0),
          ('School consent forms, Child 1', 'School paper', 'Child 1', 25, 14), ('School consent forms, Child 2', 'School paper', 'Child 2', 25, 14), ('School emergency contact form', 'School paper', 'Whole household', 60, 14),
          ('Football club membership, Child 1', 'Other', 'Child 1', 86, 21), ('Swimming club membership, Child 2', 'Other', 'Child 2', 112, 21), ('Dog registration tag renewal', 'Pet paper', 'Whole household', 221, 30),
          ('Pet travel papers, dog', 'Pet paper', 'Whole household', 560, 60), ('School bus pass, Child 1', 'Other', 'Child 1', 140, 14), ('Parking permit, Adult 1', 'Other', 'Adult 1', 96, 30),
          ('Library cards, family', 'Other', 'Whole household', 365, 0),
          ('Travel insurance, last year', 'Policy', 'Whole household', -55, 30), ('Broadband contract, previous', 'Contract', 'Whole household', -300, 30), ('Car insurance policy, family car, previous year', 'Policy', 'Whole household', -307, 30),
          ('Mobile contract, Adult 1, previous', 'Contract', 'Adult 1', -242, 30), ('Dog registration tag, previous year', 'Pet paper', 'Whole household', -144, 30), ('Travel document, Adult 2, previous', 'Travel document', 'Adult 2', -390, 60)]
    kept = ['Document box, folder A', 'Document box, folder B', 'Filing cabinet, drawer 2', 'Online, saved copy', 'Desk tray', 'Fireproof box']
    rows = []
    for i, (nm, kind, who, off, lead) in enumerate(D_):
        rows.append(dict(doc=nm, kind=kind, holder=who, expiry=iso(TODAY + day(off)), renew_lead_days=lead, kept_where=kept[(i * 5) % len(kept)], status='Renewed' if off < 0 else ('Renewal started' if 0 <= off <= 40 and kind in ('Contract', 'School paper') else 'Valid'),
                         renewed_on=iso(TODAY + day(off) - day(5)) if off < 0 else ''))
    rows.sort(key=lambda x: (x['expiry'], x['doc']))
    for i, x in enumerate(rows): x['doc_id'] = 'DC-%02d' % (i + 1)
    w['documents'] = rows


def _contacts(w):
    r = rng('contacts'); rows = []
    ex = [('Joel Park', 'Trade', 'Roofer', 160), ('Amara Diallo', 'Trade', 'Locksmith', 90), ('Viktor Lund', 'Trade', 'Pest controller', 120), ('Mei Chen', 'Trade', 'Window cleaner', 35), ('Paulo Silva', 'Trade', 'Tree surgeon', 280),
          ('Dana Wright', 'Trade', 'Appliance repairer', 95), ('Omar Khalil', 'Trade', 'Carpenter', 220), ('Ines Moreau', 'Trade', 'Painter and decorator', 450), ('Greta Vogel', 'Trade', 'Cleaner', 60),
          ('Sven Aaltonen', 'Trade', 'Glazier', 140), ('Lucia Bianchi', 'Trade', 'Tiler', 520), ('Raj Mehta', 'Trade', 'Builder', 1400), ('Kofi Mensah', 'Trade', 'Gardener', 70), ('Hana Berg', 'Family', 'Cousin, spare key at hers', 0)]
    tm = [(t['name'], 'Trade' if t['role'] in ('Plumber', 'Electrician', 'Heating engineer') else 'School' if t['role'] == 'School office' else 'Pets' if t['role'] in ('Vet clinic', 'Dog walker') else
           'Vehicles' if t['role'] == 'Car mechanic' else 'Neighbour' if t['role'] in ('Neighbour', 'Carpool family') else 'Trade', t['role'], c, t) for t, c in zip(outside, (95, 70, 130, 55, 210, 0, 0, 0, 0, 25))]
    for i, (nm, kind, trade, cost, t) in enumerate(tm):
        rows.append(dict(name=nm, kind=kind, trade=trade, phone=t['phone'], email=t['email'], last_used=iso(TODAY - day(10 + (i * 29) % 330)), cost_last=float(cost), would_use_again=bool(i % 5 != 3), member_id=t['member_id']))
    for i, (nm, kind, trade, cost) in enumerate(ex):
        rows.append(dict(name=nm, kind=kind, trade=trade, phone=fake_phone(541 + i), email=fake_email(nm), last_used=iso(TODAY - day(25 + (i * 53) % 640)), cost_last=float(cost), would_use_again=bool(i % 6 != 4), member_id=''))
    rows[5]['last_used'] = iso(TODAY - day(12))       # the appliance repairer was called about the washing machine
    rows = [x for x in rows]
    for i, x in enumerate(rows): x['contact_id'] = 'CT-%02d' % (i + 1)
    w['contacts'] = rows


# ------------------------------------------------------------------ projects
def _projects(w):
    r = rng('projects'); proj = []; tasks = []

    def status(s, e):
        if e < TODAY: return 'Done'
        if s <= TODAY: return 'In progress'
        return 'Not started'

    def addp(pid, name, kind, start, end, owner, note):
        proj.append(dict(project_id=pid, project=name, kind=kind, start=start, end=end, owner=owner, note=note))

    def addt(pid, nm, s, e, own, est, dep=None, st=None):
        st = st or status(s, e); act = R2(est * r.uniform(.9, 1.15)) if st == 'Done' else (R2(est * .4) if st == 'In progress' and est else 0.0)
        tasks.append(dict(project_id=pid, task=nm, owner=own, start=s, due=e, status=st, depends_on=dep or '', est_cost=float(est), actual_cost=act, done_on=(e - day(r.randint(0, 2))) if st == 'Done' else ''))
    # PJ-01 bathroom refresh, in progress
    b0 = TODAY - day(110); B = [('Agree the plan and the budget', -110, -100, 'Adult 1', 0), ('Get three quotes from builders', -100, -80, 'Adult 2', 0), ('Choose the tiles and fittings', -98, -70, 'Adult 1', 1250),
                                ('Book the builder and plumber', -78, -70, 'Adult 2', 0), ('Order the bath, basin and taps', -70, -55, 'Adult 1', 980), ('Clear the room and cover the floors', -45, -44, 'Adult 2', 0),
                                ('Strip out the old suite', -44, -41, 'A trade', 400), ('First fix plumbing and electrics', -40, -30, 'A trade', 1400), ('Wall and floor tiling', -29, -14, 'A trade', 1800),
                                ('Paint the walls and ceiling', -13, -7, 'Adult 2', 120), ('Fit the new bath, basin and toilet', -6, 2, 'A trade', 900), ('Order the mirror and shelves', -8, -2, 'Adult 1', 210),
                                ('Final clean and snag list', 8, 12, 'Adult 2', 0), ('Pay the final invoice', 12, 20, 'Adult 1', 0), ('Hang the mirror and shelves', 14, 22, 'Adult 2', 0)]
    addp('PJ-01', 'Bathroom refresh', 'Renovation', iso(b0), iso(TODAY + day(22)), 'Adult 1', 'New suite, tiles and paint; trades called in generic words')
    for i, (nm, a, b, own, est) in enumerate(B):
        addt('PJ-01', nm, TODAY + day(a), TODAY + day(b), own, est, 'PK-%03d' % (i) if i in (1, 2, 3, 4, 7, 8, 9, 10, 12, 13, 14) and nm != 'Order the mirror and shelves' else '',
             'Blocked' if nm == 'Order the mirror and shelves' else None)
    # PJ-02 garden bed, last spring
    g0 = last_on(4, 8); G = [('Choose the spot and measure', 0, 3, 'Adult 2', 0), ('Mark out the bed', 4, 5, 'Adult 2', 0), ('Dig and clear the grass', 6, 12, 'Adult 2', 0), ('Order compost and edging', 8, 10, 'Adult 1', 85),
                             ('Build the edging', 13, 16, 'Adult 2', 60), ('Fill with compost', 17, 19, 'Adult 2', 70), ('Buy the plants and seeds', 20, 24, 'Adult 1', 55), ('Plant with the children', 25, 26, 'Child 1', 0),
                             ('Mulch and water', 27, 29, 'Adult 2', 20), ('Set a watering rota', 30, 31, 'Adult 1', 0), ('First tidy and weeding', 40, 41, 'Child 2', 0), ('Check and note what grew', 45, 46, 'Adult 1', 0)]
    addp('PJ-02', 'Garden bed', 'Garden', iso(g0), iso(g0 + day(46)), 'Adult 2', 'A raised vegetable and flower bed')
    base = len(tasks)
    for i, (nm, a, b, own, est) in enumerate(G): addt('PJ-02', nm, g0 + day(a), g0 + day(b), own, est, 'PK-%03d' % (base + i) if i in (1, 2, 4, 5, 7, 8) else '')
    # PJ-03 holiday dinner for 12
    h = next_on(12, 20); H = [('Set the guest list for 12', -50, 'Adult 1', 0), ('Send the invitations', -45, 'Adult 1', 0), ('Ask for RSVPs and preference notes', -30, 'Adult 2', 0), ('Plan the menu and drinks', -28, 'Adult 1', 0),
                              ('Borrow extra chairs and a second table', -21, 'Adult 2', 0), ('Order the main dish ingredients', -14, 'Adult 2', 85), ('Check plates, glasses and napkins for 12', -12, 'Child 1', 0),
                              ('Wash and iron the table linen', -9, 'Adult 1', 12), ('Shop for the dry goods and drinks', -8, 'Adult 2', 110), ('Deep clean the dining room', -5, 'Adult 1', 0),
                              ('Fresh food shop', -3, 'Adult 2', 160), ('Prepare and freeze the starters and dessert', -3, 'Adult 1', 20), ('Set the table and place cards', -1, 'Child 1', 0), ('Cook the main meal', 0, 'Adult 2', 0),
                              ('Welcome the guests and serve', 0, 'Adult 1', 0), ('Clear up and share the leftovers', 1, 'Adult 1', 0)]
    addp('PJ-03', 'Hosting a holiday dinner for 12', 'Hosting', iso(h - day(50)), iso(h + day(1)), 'Adult 1', 'Menu, shopping and a timeline counted back from the day')
    base = len(tasks)
    for i, (nm, a, own, est) in enumerate(H): addt('PJ-03', nm, h + day(a - 2), h + day(a), own, est, 'PK-%03d' % (base + i) if i in (1, 2, 3, 5, 8, 10, 12, 13, 14, 15) and False else '')
    # PJ-04 spring declutter
    s0 = last_on(3, 15); S = [('Pick the areas and set a date', 0, 2, 'Adult 1', 0), ('Kids room toys and books', 3, 8, 'Child 1', 0), ('Kids room outgrown clothes', 5, 10, 'Adult 1', 0), ('Kitchen cupboards', 9, 14, 'Adult 2', 0),
                             ('Main bedroom wardrobe', 12, 17, 'Adult 1', 0), ('Hallway shoes and coats', 15, 17, 'Adult 2', 0), ('Garage shelves', 18, 26, 'Adult 2', 0), ('Bookshelves and paperwork', 22, 28, 'Adult 1', 0),
                             ('Photograph items to sell online', 27, 30, 'Adult 2', 0), ('Drop off the donations', 31, 33, 'Adult 2', 25), ('Recycling centre run', 34, 36, 'Adult 2', 20), ('Final walk-through of every room', 40, 44, 'Adult 1', 0)]
    addp('PJ-04', 'Spring declutter', 'Declutter', iso(s0), iso(s0 + day(44)), 'Adult 1', 'Keep, donate, sell or bin by area; a donation log')
    base = len(tasks)
    for i, (nm, a, b, own, est) in enumerate(S): addt('PJ-04', nm, s0 + day(a), s0 + day(b), own, est, 'PK-%03d' % (base + i) if i in (1, 2, 6, 8) and False else '')
    # ids and dependency fix (dependencies point to the task id one or more steps before inside the same project)
    for i, x in enumerate(tasks): x['task_id'] = 'PK-%03d' % (i + 1)
    for x in tasks:
        if x['depends_on']:
            n = int(x['depends_on'].split('-')[1]); x['depends_on'] = 'PK-%03d' % n if 1 <= n <= len(tasks) else ''
    for x in tasks:
        x['start'] = iso(x['start']); x['due'] = iso(x['due']); x['done_on'] = iso(x['done_on']) if x['done_on'] != '' else ''
    for p in proj:
        ts = [t for t in tasks if t['project_id'] == p['project_id']]
        p['estimate'] = float(sum(t['est_cost'] for t in ts)); alld = all(t['status'] == 'Done' for t in ts); anyp = any(t['status'] in ('Done', 'In progress', 'Blocked') for t in ts)
        p['stage'] = 'Done' if alld else 'In progress' if anyp else 'Planned'
    w['projects'] = proj; w['project_tasks'] = tasks
    # declutter and donation log
    dn = []; areas = [('Kids room', 'Outgrown clothes'), ('Kids room', 'Toys'), ('Kids room', 'Books'), ('Kitchen', 'Gadgets'), ('Kitchen', 'Plastic boxes'), ('Main bedroom', 'Clothes'), ('Main bedroom', 'Shoes'),
                      ('Hallway', 'Coats'), ('Garage', 'Tools and spare parts'), ('Garage', 'Sports gear'), ('Living room', 'Books and games'), ('Utility room', 'Cleaning supplies'), ('Bathroom', 'Old towels')]
    for i in range(78):
        a, it = areas[i % len(areas)]; d = s0 + day(3 + (i * 41 % 41)); dec = DECISIONS[(i * 7 + (i // 3)) % 4] if i % 9 else 'Donate'
        dn.append(dict(date=d, area=a, item=it, decision=dec, count=r.randint(2, 18), project_id='PJ-04', destination={'Keep': 'Kept at home', 'Donate': 'Local charity shop', 'Sell': 'Online sale', 'Bin': 'Recycling centre'}[dec], value=R2(r.uniform(4, 40)) if dec == 'Sell' else 0.0))
    for i in range(18):
        a, it = areas[(i * 3 + 1) % len(areas)]; d = TODAY - day(2 + i * 2 % 28); dec = DECISIONS[(i * 5) % 4]
        dn.append(dict(date=d, area=a, item='%s, autumn wardrobe swap' % it if a in ('Main bedroom', 'Kids room') else it, decision=dec, count=r.randint(1, 12), project_id='',
                       destination={'Keep': 'Kept at home', 'Donate': 'Local charity shop', 'Sell': 'Online sale', 'Bin': 'Recycling centre'}[dec], value=R2(r.uniform(3, 25)) if dec == 'Sell' else 0.0))
    for i in range(14):
        a, it = areas[(i * 5 + 2) % len(areas)]; d = TODAY - day(120 + i * 9)
        dn.append(dict(date=d, area=a, item=it, decision=DECISIONS[(i * 3) % 4], count=r.randint(1, 10), project_id='', destination='Local charity shop', value=0.0))
    dn.sort(key=lambda x: (x['date'], x['area']))
    for i, x in enumerate(dn): x['declutter_id'] = 'DN-%03d' % (i + 1); x['date'] = iso(x['date'])
    for x in dn:
        x['destination'] = 'Kept at home' if x['decision'] == 'Keep' else 'Online sale' if x['decision'] == 'Sell' else 'Recycling centre' if x['decision'] == 'Bin' else 'Local charity shop'
        x['value'] = x['value'] if x['decision'] == 'Sell' else 0.0
    w['declutter'] = dn
    # guests for the holiday dinner
    names = ['Aunt Lena', 'Uncle Femi', 'Cousin Mia', 'Cousin Tobi', 'Ada', 'Friend Omar', 'Friend Zoe', 'Hana', 'Marcus', 'Elsa', 'Dev', 'Noor', 'Sven', 'Lucia', 'Kofi', 'Ines']
    g = []
    for i, nm in enumerate(names):
        rs = 'Yes' if i < 11 else ('Maybe' if i < 13 else 'No' if i < 15 else 'No reply')
        g.append(dict(guest_id='GU-%02d' % (i + 1), guest=nm, rsvp=rs, party_size=2 if i in (0, 3, 6) else 1, pref_label=GUEST_PREFS[(i * 5) % len(GUEST_PREFS)], project_id='PJ-03', invited_on=iso(h - day(45 - (i % 3)))))
    w['guests'] = g


# ------------------------------------------------------------------ build and exports
def _build():
    w = {}
    _terms(w); _shifts(w); _recipes(w); _meal(w); _grocery(w); _stock(w); _chores(w); _maint(w); _inventory(w); _repairs(w); _events(w); _pets(w); _vehicles(w); _docs(w); _contacts(w); _projects(w)
    return w


def w_cached():
    if 'w' not in _CACHE: _CACHE['w'] = _build()
    return _CACHE['w']


_MAP = dict(recipe_rows='recipes', recipe_ingredient_rows='recipe_ingredients', item_rows='items', meal_plan_rows='meal_plan', grocery_list_rows='grocery_lists', grocery_item_rows='grocery_items',
            stock_rows='stock', leftover_rows='leftovers', chore_rows='chores', chore_log_rows='chore_log', reward_rows='rewards', maintenance_rows='maintenance', maintenance_log_rows='maintenance_log',
            repair_rows='repairs', inventory_rows='inventory', term_rows='terms', shift_rows='shifts', event_rows='events', gift_rows='gifts', guest_rows='guests', pet_rows='pets', pet_care_rows='pet_care',
            vehicle_rows='vehicles', vehicle_log_rows='vehicle_log', document_rows='documents', contact_rows='contacts', project_rows='projects', project_task_rows='project_tasks', declutter_rows='declutter')


def _mk(key):
    def f(n=None): return _thin([dict(x) for x in w_cached()[key]], n)
    return f


for _nm, _k in _MAP.items():
    globals()[_nm] = _mk(_k); globals()[_nm].__name__ = _nm
_GENS = list(_MAP)


# ------------------------------------------------------------------ story
def story():
    """Ids of the story rows, with the values that make each one true (all asserted)."""
    w = w_cached(); R = {}
    # 1. a fridge item with use-by within 3 days that this week's meal plan does not use
    st = [x for x in w['stock'] if x['recipe_id'] == SOUP_ID][0]
    ub = (to_date(st['use_by']) - TODAY).days; assert 0 <= ub <= 3 and st['place'] == 'Fridge', st
    ws = week_start(TODAY)
    wk = [m for m in w['meal_plan'] if ws - day(1) <= to_date(m['date']) <= ws + day(7)]
    assert wk and all(m['recipe_id'] != SOUP_ID for m in wk)
    R['food'] = st['stock_id']; R['food_use_by_days'] = ub
    # 2. adult 2 about 65% of the adult chore minutes in the last 30 days against an agreed 50/50
    a = {ADULT1: 0, ADULT2: 0}
    for x in w['chore_log']:
        if x['who'] in a and TODAY - day(29) <= to_date(x['done']) <= TODAY: a[x['who']] += x['minutes']
    sh = a[ADULT2] / float(a[ADULT1] + a[ADULT2]); assert .62 <= sh <= .68, sh
    R['chores'] = dict(share_adult2=round(sh, 3), agreed=AGREED_SPLIT_A2, minutes_adult1=a[ADULT1], minutes_adult2=a[ADULT2])
    # 3. filter change overdue about 3 weeks, smoke alarm test due in about 5 days
    f = [x for x in w['maintenance'] if x['task'] == 'Furnace or boiler filter change'][0]; al = [x for x in w['maintenance'] if x['task'] == 'Test the smoke alarms'][0]
    fd = (TODAY - (to_date(f['last_done']) + day(f['interval_days']))).days; ad = (to_date(al['last_done']) + day(al['interval_days']) - TODAY).days
    assert fd == 21 and ad == 5, (fd, ad)
    R['filter'] = f['task_id']; R['filter_overdue_days'] = fd; R['alarm'] = al['task_id']; R['alarm_due_in_days'] = ad
    # 4. washing machine warranty ends in about 30 days with a fault in the repairs table
    wm = [x for x in w['inventory'] if x['item'] == 'Washing machine'][0]; rp = [x for x in w['repairs'] if x['item_id'] == wm['item_id']][0]
    wd = (to_date(wm['warranty_end']) - TODAY).days; assert wd == 30 and rp['status'] in ('Open', 'Waiting') and to_date(rp['date']) <= TODAY
    R['washer'] = wm['item_id']; R['washer_repair'] = rp['repair_id']; R['washer_warranty_days'] = wd
    # 5. next week two children's activities overlap on one evening with only one adult free to drive
    od = iso(OVERLAP_DAY); ov = [x for x in w['events'] if x['date'] == od and x['person'] in ('Child 1', 'Child 2') and x['start'] >= '17:30']
    assert len(ov) == 2 and ov[0]['person'] != ov[1]['person'] and ov[0]['start'] < ov[1]['end'] and ov[1]['start'] < ov[0]['end']
    sh_row = [x for x in w['shifts'] if x['date'] == od][0]; assert sh_row['adults_free'] == 1 and sh_row['adult1_late']
    assert 1 <= (OVERLAP_DAY - TODAY).days <= 10, (OVERLAP_DAY - TODAY).days
    R['overlap'] = [x['event_id'] for x in ov]; R['overlap_date'] = od; R['adults_free'] = 1
    # 6. a travel document expires before a trip about 10 weeks away and the renewal lead time does not fit
    td = [x for x in w['documents'] if x['doc'] == 'Travel document, Child 1'][0]; trip = [x for x in w['events'] if x['kind'] == 'Trip'][0]
    ex = to_date(td['expiry']); assert ex < to_date(trip['date']) and ex - day(td['renew_lead_days']) < TODAY and (ex - TODAY).days > 0
    R['travel'] = td['doc_id']; R['trip'] = trip['event_id']; R['trip_in_days'] = (to_date(trip['date']) - TODAY).days; R['doc_expires_in_days'] = (ex - TODAY).days; R['lead_days'] = td['renew_lead_days']
    return R


if __name__ == '__main__':
    for nm in _GENS: print(nm, len(globals()[nm]()))
    print(story())
