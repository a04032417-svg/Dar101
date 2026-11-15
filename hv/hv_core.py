"""HVAC and plumbing contractor suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (one cached world is built on first use). The demo business is "Northline Comfort & Plumbing"
(fictional): an owner-run residential and light-commercial service shop with 8 technicians (a lead HVAC tech, 2 HVAC technicians, 2 service plumbers, an install crew lead and 2
apprentices), an office manager who also dispatches, 6 vans, about 1,400 customer sites (homes, rentals managed for landlords, small shops and offices) with about 1,900 pieces of
installed equipment (furnaces, air conditioners, heat pumps, boilers, water heaters, mini-splits; make, model and serial as plain fields), a flat-rate price book with
good-better-best options, service calls with a diagnostic fee, repairs, replacements and installs, drain and repipe work, maintenance agreements with two seasonal tune-up visits a
year, permits and inspections in generic words, an equipment supplier and a parts counter in generic words, subcontracted electrical and sheet-metal work, deposits on installs,
financing offers in generic words, strong heating and cooling seasons and a slow spring and autumn. A one-person owner-operator with one van can use most parts. One generic currency;
every date is relative to the build day (TODAY). Ids: team HV-01..HV-16, price book PB-001.., parts PT-0001.., sites CS-0001..CS-1400, equipment EQ-0001.., vans VN-01..VN-06,
calls CL-00001.., jobs JB-00001.., estimates ES-00001.., invoices IV-00001.., payments PY-00001.., agreements AG-0001.., visits VT-00001.., permits PM-0001.., purchases PO-00001...

Money model: price book flat price (rises about 4% on 1 January of this year) = cost at the time the price was set / (1 - design margin); job price = flat price of the task (member
discount 10% on repairs, an add-on sale on about a quarter of replacements); job cost = lead hours x pay rate x (1 + 24% payroll extras) + assistant hours x apprentice rate x 1.24 +
parts at the cost on the job date (supplier price changes move the cost) + permit fee + disposal + subcontracted work + vehicle cost (9.5 per hour on the road); margin = price - cost.
Agreement visits are valued at plan price / visits per year; the plan fee itself is cash (payments of kind 'Agreement fee'). Callback and warranty jobs have price 0 and a cost.
Technician pay per month = clock hours x rate x 1.24 (+ commission on sold replacements). Overhead = office manager, rent and yard, insurance, software, accounting, marketing,
training, tools, bank and card fees; owner draw is taken from profit (not a cost); tax set-aside = 25% of profit ("confirm with your adviser").

Seasons (month -> demand): heating peak Dec-Feb, cooling peak Jun-Aug, slow spring (Apr, May) and autumn (Oct), shoulder otherwise; cold and hot spells add emergency calls. Tune-up
windows: spring cooling check 15 Feb-15 Jun, autumn heating check 15 Aug-15 Dec.

Story rows (ids from story(), never hard-coded): 1 margin_job_type (Water heater replacement: margin below its target after a supplier price rise, + margin_pb_id and the part ids);
2 callback_tech (a technician whose callback rate is about double the shop average, + the rates); 3 renewal_ids (maintenance agreements due for renewal this month, not yet renewed,
with the open tune-up window behind schedule: visit_done_share against visit_expected_share); 4 overdue_invoice (a landlord account's invoice unpaid for more than 60 days);
5 short_van (a van whose latest stock count shows parts missing against its minimum, + short_parts); 6 supplier_po (a supplier invoice for a large install due this week that would
push cash below the floor in the slow season, + cash_now, cash_after, cash_floor).

Exports
  constants: COMPANY SUITE OWNER OFFICE_MANAGER HISTORY_START DIAG_FEE BURDEN_PCT VEHICLE_HOUR DEPOSIT_PCT MEMBER_DISCOUNT REPEAT_DAYS TERMS_LANDLORD TERMS_HOME UTIL_TARGET
             CALLBACK_TARGET CLOSE_TARGET BOOKING_TARGET TAX_SET_ASIDE_PCT CASH_FLOOR OWNER_DRAW COVER_MONTHS_TARGET FINANCE_FACTOR SPIFF_AGREEMENT RENEWAL_WARN_DAYS HOURS (7..18)
  dates: TODAY iso ago ahead to_date month_start add_months months14() week_start; helpers pairs first_name fake_phone fake_email rng
  lists: ROLES TEAMS PAY_TYPES TRADES JOB_KINDS JOB_TYPES JOB_STATUS TIERS OPTION_CHOSEN EST_OUTCOME EST_LOST SOURCES CALL_TYPES CALL_OUTCOMES ANSWERED_BY SITE_TYPES AREAS EQUIP_TYPES
         FUELS PLAN_NAMES AGREEMENT_STATUS VISIT_SEASONS VISIT_STATUS PAY_METHODS INVOICE_STATUS PAYMENT_KINDS PERMIT_STATUS CALLBACK_REASONS PURCHASE_KINDS PO_STATUS PART_CATEGORIES
         EXPENSE_CATEGORIES RENEWAL_KINDS SEASONS WEEKDAYS WEEKDAYS7 MONTH_NAMES CHASE_METHODS CHASE_OUTCOMES BAND_NAMES TECH_NAMES VAN_NAMES
  people and reference (module lists): team (16), staff (10 paid), contacts (6), techs (8), vans (6), job_types (15), lead_sources (8), plans (5), cost_categories (14), seasons (12),
         call_outcomes (7), price_book (57 tasks PB-001..), parts (68, PT-0001..), plus PB PART TECH JT_OF PLAN LOADED VAN_OF staff_by_name AREA_DRIVE
  generators (fresh lists of dicts, oldest first; n= thins a long list but keeps the most recent rows; optional dates are '' when blank):
    site_rows equipment_rows call_rows job_rows estimate_rows invoice_rows payment_rows agreement_rows renewal_rows visit_rows permit_rows callback_rows parts_used_rows timesheet_rows
    pay_rows van_stock_rows stock_count_rows restock_rows purchase_rows price_change_rows marketing_rows review_rows expense_rows vehicle_cost_rows tool_rows licence_rows pnl_rows
    cash_rows bill_rows ageing_rows chase_rows tax_rows job_type_month_rows tech_month_rows
  helpers: cost_at(part, date) pb_price(task_row, date) callback_rate(tech=None, months=12) job_margin(job_type, from_date, to_date) story()
  test only: the environment variable HV_TODAY=YYYY-MM-DD moves TODAY (the story holds on any build date)
Lesson: money cells are plain amounts; optional dates (paid_on, approved_on, renewed_on) are '' when blank: wrap lookups with IF(x=0,"",x). Links hold NAMES (technician, van, source,
job_type) or ids (site CS-0001, job JB-00001, invoice IV-00001). Words: no brand, law, licence, refrigerant-rule or standard names; no safety claims; customer data is a site reference,
an area and a phone number only.
"""
import datetime as dt
import calendar
import random
import hashlib
import math

COMPANY = 'Northline Comfort & Plumbing'
SUITE = 'fx-20261115-hvac-plumbing'
OWNER = 'Marcus Delgado'
OFFICE_MANAGER = 'Priya Raman'
import os
TODAY = dt.date.fromisoformat(os.environ['HV_TODAY']) if os.environ.get('HV_TODAY') else dt.date.today()
D = dt.date

DIAG_FEE = 99.0              # call-out / diagnostic fee
BURDEN_PCT = 0.24            # employer extras on technician pay
VEHICLE_HOUR = 9.5           # vehicle cost per hour on the road (fuel, lease, insurance, repairs share)
DEPOSIT_PCT = 0.30           # deposit asked on an install
MEMBER_DISCOUNT = 0.10       # agreement members: share off repairs
REPEAT_DAYS = 30             # a second job at the same site within N days is a possible callback
TERMS_LANDLORD = 30          # invoice terms in days for landlord and business accounts
TERMS_HOME = 7
UTIL_TARGET = 0.70           # billed hours over clock hours ("a typical range, check your own numbers")
CALLBACK_TARGET = 0.04
CLOSE_TARGET = 0.55
BOOKING_TARGET = 0.80
TAX_SET_ASIDE_PCT = 0.25
CASH_FLOOR = 25000.0
OWNER_DRAW = 8500.0
COVER_MONTHS_TARGET = 3
FINANCE_FACTOR = 0.0212      # monthly payment as a share of the financed amount (owner-entered, generic)
SPIFF_AGREEMENT = 25.0
RENEWAL_WARN_DAYS = 30
HOURS = list(range(7, 19))


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
def fake_email(name, i=0): return name.lower().replace(' ', '.').replace("'", '') + (str(i) if i else '') + '@mail.example.com'
def rng(tag=''): return random.Random('hv-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
def _hm(h):
    m = int(round(h * 60)); return '%02d:%02d' % (m // 60, m % 60)


HISTORY_START = month_start(23)

# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Owner', 'Office manager', 'Lead HVAC tech', 'HVAC technician', 'Service plumber', 'Install crew lead', 'Apprentice', 'Equipment supplier', 'Parts counter', 'Subcontractor',
         'Accountant', 'Insurance agent']
TEAMS = ['Office', 'Service', 'Install', 'Outside']
PAY_TYPES = ['Owner draw', 'Salary', 'Hourly', 'Flat rate', 'Invoice']
TRADES = ['HVAC', 'Plumbing']
JOB_KINDS = ['Repair', 'Tune-up', 'Replacement', 'Install', 'Drain', 'Repipe', 'Diagnostic']
JOB_TYPES = ['Heating repair', 'Cooling repair', 'Diagnostic visit', 'Furnace tune-up', 'Air conditioner tune-up', 'Agreement visit', 'Furnace replacement', 'Air conditioner replacement',
             'Heat pump install', 'Boiler repair', 'Water heater replacement', 'Leak repair', 'Drain clearing', 'Fixture install', 'Repipe']
JOB_STATUS = ['Scheduled', 'In progress', 'Completed', 'Cancelled']
TIERS = ['Good', 'Better', 'Best']
OPTION_CHOSEN = ['Good', 'Better', 'Best', 'None']
EST_OUTCOME = ['Won', 'Lost', 'Open']
EST_LOST = ['Price', 'Went elsewhere', 'Repair instead', 'Financing declined', 'No decision']
SOURCES = ['Search ads', 'Local listing', 'Website', 'Referral', 'Repeat customer', 'Property manager', 'Van and yard signs', 'Mailers']
CALL_TYPES = ['No-heat', 'No-cool', 'Leak', 'Drain', 'Quote', 'Member', 'Warranty', 'Tune-up']
CALL_OUTCOMES = ['Booked', 'Estimate booked', 'Price shopper', 'No slot', 'Outside area', 'Missed call', 'Existing job']
ANSWERED_BY = ['Office manager', 'Owner', 'After-hours line']
SITE_TYPES = ['Home', 'Rental', 'Shop', 'Office']
AREAS = ['Northfield', 'Riverside', 'Old Town', 'Hillcrest', 'Lakeside', 'Eastgate', 'Westbrook', 'Southpark']
EQUIP_TYPES = ['Furnace', 'Air conditioner', 'Heat pump', 'Boiler', 'Water heater', 'Mini-split']
FUELS = ['Gas', 'Electric', 'Oil', 'Propane']
PLAN_NAMES = ['Basic comfort', 'Standard comfort', 'Premium comfort', 'Plumbing check', 'Extra system add-on']
AGREEMENT_STATUS = ['Active', 'Renewal due', 'Lapsed', 'Cancelled']
VISIT_SEASONS = ['Spring cooling check', 'Autumn heating check']
VISIT_STATUS = ['Done', 'Booked', 'Due', 'Missed']
PAY_METHODS = ['Card on site', 'Card online', 'Bank transfer', 'Cash or cheque', 'Financing offer']
INVOICE_STATUS = ['Paid', 'Part paid', 'Unpaid', 'Written off']
PAYMENT_KINDS = ['Invoice', 'Deposit', 'Agreement fee']
PERMIT_STATUS = ['Applied', 'Approved', 'Inspection booked', 'Passed']
CALLBACK_REASONS = ['Same fault returned', 'Part replaced', 'Incomplete visit', 'Wrong part', 'Customer not satisfied']
PURCHASE_KINDS = ['Equipment', 'Parts run', 'Subcontract']
PO_STATUS = ['Paid', 'Open']
PART_CATEGORIES = ['Heating', 'Cooling', 'Plumbing', 'Consumable', 'Equipment']
EXPENSE_CATEGORIES = ['Rent and yard', 'Utilities', 'Vehicle fuel', 'Vehicle repairs', 'Vehicle lease', 'Insurance', 'Tools and equipment', 'Marketing', 'Software', 'Accounting',
                      'Office supplies', 'Training', 'Bank and card fees', 'Permits and disposal']
RENEWAL_KINDS = ['Business licence', 'Trade licence', 'Vehicle registration', 'Vehicle inspection', 'Vehicle insurance', 'Liability insurance', 'Technician training', 'Tool calibration']
SEASONS = ['Heating season', 'Cooling season', 'Shoulder season']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
WEEKDAYS7 = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
CHASE_METHODS = ['Call', 'Text', 'Letter']
CHASE_OUTCOMES = ['Kept', 'Broken', 'Open']
BAND_NAMES = ['0-30', '31-60', '61-90', '90+']

# ------------------------------------------------------------------ people
# id, name, country, role, team, pay type, hours a week, monthly salary, hourly rate, assignment, trade, commission share, start days ago
_staff = [('HV-01', 'Marcus Delgado', 'Mexico', 'Owner', 'Office', 'Owner draw', 50, 0, 0, 'Whole business', '', 0.0, 3400),
          ('HV-02', 'Priya Raman', 'India', 'Office manager', 'Office', 'Salary', 40, 4300, 0, 'Office and dispatch', '', 0.0, 2300),
          ('HV-03', 'Tomasz Nowak', 'Poland', 'Lead HVAC tech', 'Service', 'Hourly', 40, 0, 38.5, 'Van 1', 'HVAC', 0.020, 2900),
          ('HV-04', 'Kofi Mensah', 'Ghana', 'HVAC technician', 'Service', 'Hourly', 40, 0, 33.5, 'Van 2', 'HVAC', 0.015, 1700),
          ('HV-05', 'Elena Rossi', 'Italy', 'HVAC technician', 'Service', 'Hourly', 40, 0, 32.0, 'Van 3', 'HVAC', 0.015, 1100),
          ('HV-06', 'Jamal Whitfield', 'USA', 'Service plumber', 'Service', 'Flat rate', 40, 0, 35.5, 'Van 4', 'Plumbing', 0.020, 2200),
          ('HV-07', 'Sven Andersson', 'Sweden', 'Service plumber', 'Service', 'Hourly', 40, 0, 32.5, 'Van 5', 'Plumbing', 0.015, 900),
          ('HV-08', 'Diego Morales', 'Colombia', 'Install crew lead', 'Install', 'Hourly', 40, 0, 36.5, 'Van 6', 'HVAC', 0.025, 2500),
          ('HV-09', 'Amira Haddad', 'Egypt', 'Apprentice', 'Install', 'Hourly', 40, 0, 20.5, 'Rides with Van 6', 'HVAC', 0.0, 520),
          ('HV-10', "Liam O'Connell", 'Ireland', 'Apprentice', 'Service', 'Hourly', 40, 0, 18.5, 'Rides with Van 4', 'Plumbing', 0.0, 260)]
staff = []
for _i, (a, b, c, ro, te, pt, hw, sal, hr, asg, trd, cm, st) in enumerate(_staff):
    staff.append(dict(staff_id=a, name=b, role=ro, team=te, pay_type=pt, phone=fake_phone(101 + _i), email=fake_email(b), hours_week=hw, monthly_salary=float(sal),
                      hourly_rate=float(hr), assignment=asg, trade=trd, commission_pct=cm, country=c, start=ago(st)))
_ctc = [('HV-11', 'Hiroshi Tanaka', 'Japan', 'Equipment supplier', 'Your equipment supplier'),
        ('HV-12', 'Beatrice Okafor', 'Nigeria', 'Parts counter', 'Your parts counter'),
        ('HV-13', 'Viktor Petrenko', 'Ukraine', 'Subcontractor', 'Electrical work'),
        ('HV-14', 'Ahmed Karim', 'Jordan', 'Subcontractor', 'Sheet-metal work'),
        ('HV-15', 'Grace Lindqvist', 'Norway', 'Accountant', 'Bookkeeping and year-end pack'),
        ('HV-16', 'Olu Adeyemi', 'Kenya', 'Insurance agent', 'Vehicle and liability cover')]
contacts = [dict(staff_id=a, name=b, role=ro, team='Outside', pay_type='Invoice', phone=fake_phone(113 + i), email=fake_email(b), hours_week=0, monthly_salary=0.0, hourly_rate=0.0,
                 assignment=sp, trade='', commission_pct=0.0, country=c, start=ago(2400 - 260 * i)) for i, (a, b, c, ro, sp) in enumerate(_ctc)]
team = staff + contacts
staff_by_name = {s['name']: s for s in team}
TECH_NAMES = [s['name'] for s in staff[2:]]
techs = [dict(tech_id=s['staff_id'], name=s['name'], role=s['role'], trade=s['trade'], pay_type=s['pay_type'], hourly_rate=s['hourly_rate'], commission_pct=s['commission_pct'],
              spiff=SPIFF_AGREEMENT if s['role'] != 'Apprentice' else 0.0, van=s['assignment'], start=s['start']) for s in staff[2:]]
TECH = {t['name']: t for t in techs}
VAN_NAMES = ['Van %d' % i for i in range(1, 7)]
_van_tech = ['Tomasz Nowak', 'Kofi Mensah', 'Elena Rossi', 'Jamal Whitfield', 'Sven Andersson', 'Diego Morales']
vans = [dict(van_id='VN-%02d' % (i + 1), van=VAN_NAMES[i], technician=_van_tech[i], trade=TECH[_van_tech[i]]['trade'], model_year=[2021, 2022, 2019, 2023, 2022, 2024][i],
             lease_monthly=[690.0, 640.0, 520.0, 780.0, 650.0, 860.0][i], role='Install truck' if i == 5 else 'Service van') for i in range(6)]
VAN_OF = {v['technician']: v['van'] for v in vans}
LOADED = {t['name']: R2(t['hourly_rate'] * (1 + BURDEN_PCT)) for t in techs}

# ------------------------------------------------------------------ reference tables
# job type: trade, kind, avg lead hours, target margin, demand per working day at weight 1, season weights, cold/hot spell boost, goes through an estimate
_H = [1.7, 1.5, 1.0, .55, .3, .2, .2, .2, .45, .8, 1.3, 1.6]
_C = [.2, .2, .3, .5, .9, 1.4, 1.9, 1.8, 1.0, .4, .2, .2]
_P = [1.1, 1.0, 1.0, 1.0, 1.0, .95, .9, .9, 1.0, 1.05, 1.05, 1.1]
_TC = [.1, .1, .8, 1.9, 2.2, 1.0, .3, .2, .1, .1, .1, .1]
_TH = [.4, .2, .1, .1, .1, .1, .1, .2, 1.6, 2.4, 1.6, .8]
_HC = [.9 * (a + b) / 1.0 for a, b in zip(_H, _C)]
_HP = [.8, .8, 1, 1, 1.1, 1.1, 1.1, 1, 1.1, 1.1, 1, .8]
_JT = {  # name: (trade, kind, hours, target, base per workday, weights, spell, estimate)
    'Heating repair': ('HVAC', 'Repair', 2.0, .58, 1.95, _H, 'cold', False),
    'Cooling repair': ('HVAC', 'Repair', 2.0, .58, 1.70, _C, 'hot', False),
    'Diagnostic visit': ('HVAC', 'Diagnostic', 0.9, .50, 1.15, _HC, 'both', False),
    'Furnace tune-up': ('HVAC', 'Tune-up', 1.2, .65, 0.85, _TH, '', False),
    'Air conditioner tune-up': ('HVAC', 'Tune-up', 1.2, .65, 0.85, _TC, '', False),
    'Agreement visit': ('HVAC', 'Tune-up', 1.2, .25, 0, _P, '', False),
    'Furnace replacement': ('HVAC', 'Replacement', 8.0, .38, 0.30, _H, 'cold', True),
    'Air conditioner replacement': ('HVAC', 'Replacement', 8.0, .38, 0.27, _C, 'hot', True),
    'Heat pump install': ('HVAC', 'Install', 14.0, .38, 0.17, _HP, '', True),
    'Boiler repair': ('HVAC', 'Repair', 2.2, .55, 0.28, _H, 'cold', False),
    'Water heater replacement': ('Plumbing', 'Replacement', 3.6, .43, 0.68, _P, '', True),
    'Leak repair': ('Plumbing', 'Repair', 1.7, .55, 2.00, _P, '', False),
    'Drain clearing': ('Plumbing', 'Drain', 1.1, .65, 1.95, _P, '', False),
    'Fixture install': ('Plumbing', 'Install', 1.4, .50, 1.15, _P, '', False),
    'Repipe': ('Plumbing', 'Repipe', 24.0, .40, 0.055, _P, '', True)}
job_types = [dict(job_type=k, trade=v[0], kind=v[1], avg_hours=v[2], target_margin=v[3]) for k, v in _JT.items()]
JT_OF = {x['job_type']: x for x in job_types}
lead_sources = [dict(source=s, monthly_cost=c, kind=k) for s, c, k in
                [('Search ads', 4300.0, 'Paid'), ('Local listing', 620.0, 'Paid'), ('Website', 340.0, 'Paid'), ('Referral', 450.0, 'Reward'), ('Repeat customer', 90.0, 'Own list'),
                 ('Property manager', 150.0, 'Own list'), ('Van and yard signs', 120.0, 'Paid'), ('Mailers', 300.0, 'Paid')]]
_SRC_W = [.27, .09, .11, .13, .17, .08, .06, .09]
_SRC_BOOK = [.62, .70, .72, .88, .93, .95, .78, .58]       # share of calls from that source that book
plans = [dict(plan=a, price=b, visits_per_year=c, note=d) for a, b, c, d in
         [('Basic comfort', 189.0, 2, 'One system, two tune-ups a year'), ('Standard comfort', 269.0, 2, 'Priority booking and 10% off repairs'),
          ('Premium comfort', 389.0, 2, 'No diagnostic fee and 15% off repairs'), ('Plumbing check', 149.0, 1, 'One yearly plumbing check'),
          ('Extra system add-on', 99.0, 2, 'A second system on the same site')]]
PLAN = {p['plan']: p for p in plans}
_PLAN_W = [.36, .30, .14, .12, .08]
cost_categories = [dict(category=c, grp=g, monthly_budget=b) for c, g, b in
                   [('Rent and yard', 'Overhead', 4800.0), ('Utilities', 'Overhead', 600.0), ('Vehicle fuel', 'Vehicle', 7200.0), ('Vehicle repairs', 'Vehicle', 1500.0),
                    ('Vehicle lease', 'Vehicle', 4140.0), ('Insurance', 'Overhead', 4100.0), ('Tools and equipment', 'Overhead', 700.0), ('Marketing', 'Marketing', 6300.0),
                    ('Software', 'Overhead', 890.0), ('Accounting', 'Overhead', 650.0), ('Office supplies', 'Overhead', 240.0), ('Training', 'Overhead', 500.0),
                    ('Bank and card fees', 'Overhead', 2900.0), ('Permits and disposal', 'Direct', 1500.0)]]
_SEAS = ['Heating season', 'Heating season', 'Shoulder season', 'Shoulder season', 'Shoulder season', 'Cooling season', 'Cooling season', 'Cooling season', 'Shoulder season',
         'Shoulder season', 'Shoulder season', 'Heating season']
_IDX = [1.30, 1.15, .85, .62, .75, 1.10, 1.40, 1.30, .85, .62, .85, 1.20]
seasons = [dict(month_no=i + 1, month_name=MONTH_NAMES[i], season=_SEAS[i], demand_index=_IDX[i]) for i in range(12)]
call_outcomes = [dict(outcome=o, booked=o in ('Booked', 'Estimate booked'), note=n) for o, n in
                 [('Booked', 'A job is booked'), ('Estimate booked', 'An estimate visit is booked'), ('Price shopper', 'Asked the price and did not book'),
                  ('No slot', 'No technician free in time'), ('Outside area', 'Outside the service territory'), ('Missed call', 'Nobody answered, no message'),
                  ('Existing job', 'About a job already booked or invoiced')]]
AREA_DRIVE = {'Northfield': .55, 'Riverside': .40, 'Old Town': .25, 'Hillcrest': .50, 'Lakeside': .60, 'Eastgate': .45, 'Westbrook': .55, 'Southpark': .35}

# ------------------------------------------------------------------ parts (name, category, cost, markup, van min, van max)
_PARTS = [
    ('Igniter', 'Heating', 48, .9, 3, 6), ('Flame sensor', 'Heating', 24, 1.1, 3, 6), ('Control board, furnace', 'Heating', 265, .55, 1, 2), ('Blower motor', 'Heating', 310, .55, 1, 2),
    ('Inducer motor', 'Heating', 255, .55, 1, 2), ('Burner valve', 'Heating', 185, .6, 1, 2), ('Pressure switch', 'Heating', 42, .9, 2, 4), ('Limit switch', 'Heating', 29, 1.0, 2, 4),
    ('Thermostat, basic', 'Heating', 38, 1.0, 3, 6), ('Thermostat, smart', 'Heating', 165, .6, 2, 4), ('Boiler circulator pump', 'Heating', 230, .55, 1, 2),
    ('Boiler control and sensor', 'Heating', 195, .6, 1, 2), ('Venting kit', 'Heating', 96, .6, 1, 3),
    ('Run capacitor', 'Cooling', 22, 1.4, 6, 12), ('Contactor', 'Cooling', 27, 1.2, 4, 8), ('Condenser fan motor', 'Cooling', 185, .6, 1, 3), ('Start kit', 'Cooling', 45, 1.0, 2, 4),
    ('Control board, air handler', 'Cooling', 210, .55, 1, 2), ('Line set kit', 'Cooling', 118, .5, 1, 3), ('Condensate pump', 'Cooling', 72, .8, 1, 3),
    ('Pad and disconnect kit', 'Cooling', 84, .6, 1, 3), ('Expansion valve', 'Cooling', 96, .7, 1, 2),
    ('Shut-off valve', 'Plumbing', 9.5, 2.0, 10, 24), ('Supply line', 'Plumbing', 7.5, 1.8, 12, 30), ('Faucet cartridge', 'Plumbing', 26, 1.2, 4, 10),
    ('Toilet fill valve kit', 'Plumbing', 16, 1.5, 6, 12), ('Wax ring kit', 'Plumbing', 9, 1.6, 6, 12), ('P-trap kit', 'Plumbing', 12, 1.6, 6, 12), ('Hose bib', 'Plumbing', 22, 1.2, 3, 6),
    ('Pressure regulator', 'Plumbing', 88, .7, 1, 3), ('Pipe fittings kit', 'Plumbing', 34, 1.2, 5, 10), ('Copper pipe, 10 ft', 'Plumbing', 42, .8, 6, 12),
    ('PEX pipe, 100 ft coil', 'Plumbing', 78, .7, 2, 4), ('PEX fittings kit', 'Plumbing', 52, .9, 3, 6), ('Expansion tank', 'Plumbing', 64, .8, 1, 3),
    ('Flex connectors', 'Plumbing', 14, 1.6, 6, 12), ('Relief valve', 'Plumbing', 23, 1.3, 3, 6), ('Water heater element', 'Plumbing', 18, 1.5, 4, 8), ('Anode rod', 'Plumbing', 31, 1.0, 2, 4),
    ('Garbage disposal', 'Plumbing', 96, .7, 1, 2), ('Faucet, kitchen', 'Plumbing', 112, .65, 1, 3), ('Faucet, bathroom', 'Plumbing', 74, .7, 2, 4), ('Toilet', 'Plumbing', 148, .6, 1, 2),
    ('Sump pump', 'Plumbing', 168, .6, 1, 2), ('Drain cleanout cap', 'Plumbing', 8, 1.8, 4, 8),
    ('Filter, 1 inch', 'Consumable', 7.5, 1.4, 24, 48), ('Filter, 4 inch', 'Consumable', 29, 1.0, 6, 12), ('Sealant and tape', 'Consumable', 6, 2.0, 10, 20),
    ('Wire and connectors kit', 'Consumable', 18, 1.2, 5, 10), ('Drain cable section', 'Consumable', 24, 1.0, 2, 4), ('Cleaning chemicals', 'Consumable', 15, 1.3, 4, 8),
    ('Pipe insulation', 'Consumable', 11, 1.2, 6, 12),
    ('Furnace, standard efficiency', 'Equipment', 1380, .55, 0, 0), ('Furnace, high efficiency', 'Equipment', 1960, .55, 0, 0), ('Furnace, variable speed', 'Equipment', 2540, .52, 0, 0),
    ('Air conditioner, standard', 'Equipment', 1490, .55, 0, 0), ('Air conditioner, high efficiency', 'Equipment', 2140, .52, 0, 0),
    ('Air conditioner, variable speed', 'Equipment', 2890, .5, 0, 0), ('Heat pump, standard', 'Equipment', 2380, .55, 0, 0), ('Heat pump, high efficiency', 'Equipment', 3150, .52, 0, 0),
    ('Heat pump, variable speed', 'Equipment', 3980, .5, 0, 0), ('Mini-split, single zone', 'Equipment', 1280, .6, 0, 0), ('Mini-split, two zone', 'Equipment', 2380, .55, 0, 0),
    ('Water heater, 40 gal tank', 'Equipment', 468, .6, 0, 0), ('Water heater, 50 gal tank', 'Equipment', 562, .6, 0, 0), ('Water heater, tankless', 'Equipment', 1090, .55, 0, 0),
    ('Air handler', 'Equipment', 980, .55, 0, 0), ('Evaporator coil', 'Equipment', 640, .55, 0, 0)]
_PART_ROW = {}
# price changes: (days ago, part name, share). The water heater units rise 20% about four months ago, so margins of that job type fall below target.
_PC = [(640, 'Igniter', .04), (610, 'Thermostat, smart', .05), (590, 'Furnace, standard efficiency', .045), (560, 'Run capacitor', .06), (540, 'Water heater, 40 gal tank', .05),
       (520, 'Copper pipe, 10 ft', .08), (480, 'Air conditioner, standard', .05), (455, 'Heat pump, standard', .04), (430, 'Shut-off valve', .06), (400, 'Contactor', .05),
       (372, 'Water heater, 50 gal tank', .05), (350, 'PEX pipe, 100 ft coil', .07), (330, 'Furnace, high efficiency', .05), (300, 'Condenser fan motor', .04),
       (285, 'Air conditioner, high efficiency', .05), (262, 'Blower motor', .045), (240, 'Control board, furnace', .05), (225, 'Heat pump, high efficiency', .045),
       (205, 'Faucet, kitchen', .06), (190, 'Expansion tank', .06), (168, 'Garbage disposal', .05), (150, 'Furnace, variable speed', .04), (141, 'Toilet', .05),
       (118, 'Water heater, 40 gal tank', .20), (118, 'Water heater, 50 gal tank', .20), (118, 'Water heater, tankless', .12), (117, 'Flex connectors', .08), (117, 'Relief valve', .07),
       (96, 'Heat pump, variable speed', .04), (80, 'Air conditioner, variable speed', .04), (63, 'Pipe fittings kit', .06), (41, 'Inducer motor', .05), (22, 'Igniter', .05)]
_PC = [(a, b, c) for a, b, c in _PC if a <= 23 * 30 + 15]
_PC_BY = {}
for _a, _b, _c in _PC: _PC_BY.setdefault(_b, []).append((TODAY - day(_a), _c))
parts = []
for _i, (_n, _cat, _cost, _mk, _mn, _mx) in enumerate(_PARTS, 1):
    parts.append(dict(part_id='PT-%04d' % _i, part=_n, category=_cat, unit_cost=float(_cost), markup=_mk, van_min=_mn, van_max=_mx,
                      supplier='Your equipment supplier' if _cat == 'Equipment' else 'Your parts counter'))
PART = {p['part']: p for p in parts}


def cost_at(part, d):
    """supplier cost of a part on date d (current cost divided by every later price rise)"""
    d = to_date(d); c = PART[part]['unit_cost']
    for pd_, sh in _PC_BY.get(part, []):
        if pd_ > d: c /= (1 + sh)
    return R2(c)


def price_change_rows(n=None):
    out = []
    for i, (a, b, c) in enumerate(sorted(_PC, key=lambda x: -x[0]), 1):
        new = cost_at(b, TODAY - day(a)); old = R2(new / (1 + c))
        out.append(dict(change_id='PC-%03d' % i, date=ago(a), part_id=PART[b]['part_id'], part=b, supplier=PART[b]['supplier'], old_cost=old, new_cost=new, rise=round(c, 3)))
    return _thin(out, n)


# ------------------------------------------------------------------ price book (task, tier, lead hours, parts, design margin, permit, disposal, expected subcontract)
_T = [
    ('Heating repair', 'Ignition part replacement', '', 1.6, [('Igniter', 1), ('Sealant and tape', 1)], .68, 0, 0, 0),
    ('Heating repair', 'Flame sensor and cleaning', '', 1.2, [('Flame sensor', 1)], .70, 0, 0, 0),
    ('Heating repair', 'Control board replacement', '', 2.0, [('Control board, furnace', 1), ('Wire and connectors kit', 1)], .62, 0, 0, 0),
    ('Heating repair', 'Blower motor replacement', '', 2.6, [('Blower motor', 1), ('Run capacitor', 1)], .60, 0, 0, 0),
    ('Heating repair', 'Inducer motor replacement', '', 2.4, [('Inducer motor', 1), ('Pressure switch', 1)], .60, 0, 0, 0),
    ('Heating repair', 'Burner valve replacement', '', 2.2, [('Burner valve', 1), ('Limit switch', 1)], .62, 0, 0, 0),
    ('Heating repair', 'Thermostat replacement', '', 1.0, [('Thermostat, smart', 1), ('Wire and connectors kit', 1)], .66, 0, 0, 0),
    ('Cooling repair', 'Capacitor replacement', '', 1.0, [('Run capacitor', 1), ('Sealant and tape', 1)], .72, 0, 0, 0),
    ('Cooling repair', 'Contactor replacement', '', 1.2, [('Contactor', 1), ('Wire and connectors kit', 1)], .70, 0, 0, 0),
    ('Cooling repair', 'Condenser fan motor replacement', '', 2.2, [('Condenser fan motor', 1), ('Run capacitor', 1)], .62, 0, 0, 0),
    ('Cooling repair', 'Start kit and electrical check', '', 1.4, [('Start kit', 1), ('Contactor', 1)], .66, 0, 0, 0),
    ('Cooling repair', 'Air handler board replacement', '', 2.0, [('Control board, air handler', 1)], .62, 0, 0, 0),
    ('Cooling repair', 'Condensate pump and drain line', '', 1.6, [('Condensate pump', 1), ('Cleaning chemicals', 1)], .66, 0, 0, 0),
    ('Cooling repair', 'Expansion valve replacement', '', 3.4, [('Expansion valve', 1), ('Line set kit', 1)], .58, 0, 0, 0),
    ('Diagnostic visit', 'Diagnostic visit, heating', '', .8, [], .62, 0, 0, 0),
    ('Diagnostic visit', 'Diagnostic visit, cooling', '', .8, [], .62, 0, 0, 0),
    ('Diagnostic visit', 'After-hours diagnostic visit', '', 1.0, [], .66, 0, 0, 0),
    ('Furnace tune-up', 'Furnace tune-up with filter', '', 1.1, [('Filter, 1 inch', 1)], .72, 0, 0, 0),
    ('Furnace tune-up', 'Furnace tune-up, premium', '', 1.5, [('Filter, 4 inch', 1), ('Cleaning chemicals', 1)], .72, 0, 0, 0),
    ('Air conditioner tune-up', 'Air conditioner tune-up with filter', '', 1.1, [('Filter, 1 inch', 1)], .72, 0, 0, 0),
    ('Air conditioner tune-up', 'Air conditioner tune-up, premium', '', 1.5, [('Filter, 4 inch', 1), ('Cleaning chemicals', 1)], .72, 0, 0, 0),
    ('Agreement visit', 'Agreement visit, cooling check', '', 1.2, [('Filter, 1 inch', 1)], .40, 0, 0, 0),
    ('Agreement visit', 'Agreement visit, heating check', '', 1.2, [('Filter, 1 inch', 1)], .40, 0, 0, 0),
    ('Furnace replacement', 'Furnace, standard efficiency', 'Good', 8.0, [('Furnace, standard efficiency', 1), ('Venting kit', 1), ('Thermostat, basic', 1), ('Filter, 1 inch', 2), ('Sealant and tape', 2)], .40, 110, 55, 90),
    ('Furnace replacement', 'Furnace, high efficiency', 'Better', 8.5, [('Furnace, high efficiency', 1), ('Venting kit', 1), ('Thermostat, smart', 1), ('Filter, 4 inch', 1), ('Sealant and tape', 2)], .44, 110, 55, 110),
    ('Furnace replacement', 'Furnace, variable speed', 'Best', 9.0, [('Furnace, variable speed', 1), ('Venting kit', 1), ('Thermostat, smart', 1), ('Filter, 4 inch', 1), ('Pipe insulation', 2)], .47, 110, 55, 140),
    ('Air conditioner replacement', 'Air conditioner, standard', 'Good', 8.0, [('Air conditioner, standard', 1), ('Pad and disconnect kit', 1), ('Line set kit', 1), ('Sealant and tape', 2)], .40, 110, 55, 120),
    ('Air conditioner replacement', 'Air conditioner, high efficiency', 'Better', 8.5, [('Air conditioner, high efficiency', 1), ('Pad and disconnect kit', 1), ('Line set kit', 1), ('Thermostat, smart', 1)], .44, 110, 55, 140),
    ('Air conditioner replacement', 'Air conditioner, variable speed', 'Best', 9.0, [('Air conditioner, variable speed', 1), ('Pad and disconnect kit', 1), ('Line set kit', 1), ('Thermostat, smart', 1), ('Condensate pump', 1)], .47, 110, 55, 160),
    ('Heat pump install', 'Heat pump, standard', 'Good', 14.0, [('Heat pump, standard', 1), ('Air handler', 1), ('Line set kit', 1), ('Pad and disconnect kit', 1), ('Thermostat, basic', 1)], .39, 130, 60, 320),
    ('Heat pump install', 'Heat pump, high efficiency', 'Better', 15.0, [('Heat pump, high efficiency', 1), ('Air handler', 1), ('Line set kit', 1), ('Pad and disconnect kit', 1), ('Thermostat, smart', 1)], .43, 130, 60, 340),
    ('Heat pump install', 'Heat pump, variable speed', 'Best', 16.0, [('Heat pump, variable speed', 1), ('Air handler', 1), ('Line set kit', 1), ('Pad and disconnect kit', 1), ('Thermostat, smart', 1), ('Condensate pump', 1)], .46, 130, 60, 380),
    ('Heat pump install', 'Mini-split, single zone', '', 7.0, [('Mini-split, single zone', 1), ('Line set kit', 1), ('Pad and disconnect kit', 1)], .45, 90, 0, 190),
    ('Heat pump install', 'Mini-split, two zone', '', 11.0, [('Mini-split, two zone', 1), ('Line set kit', 2), ('Pad and disconnect kit', 1)], .45, 90, 0, 260),
    ('Boiler repair', 'Circulator pump replacement', '', 2.4, [('Boiler circulator pump', 1), ('Pipe fittings kit', 1)], .62, 0, 0, 0),
    ('Boiler repair', 'Boiler control and sensor', '', 2.2, [('Boiler control and sensor', 1)], .62, 0, 0, 0),
    ('Boiler repair', 'Boiler service and bleed', '', 1.8, [('Cleaning chemicals', 1), ('Sealant and tape', 1)], .66, 0, 0, 0),
    ('Water heater replacement', 'Water heater, 40 gal tank', 'Good', 3.4, [('Water heater, 40 gal tank', 1), ('Flex connectors', 2), ('Relief valve', 1), ('Shut-off valve', 1), ('Sealant and tape', 1)], .43, 65, 35, 0),
    ('Water heater replacement', 'Water heater, 50 gal tank', 'Better', 3.6, [('Water heater, 50 gal tank', 1), ('Flex connectors', 2), ('Relief valve', 1), ('Expansion tank', 1), ('Shut-off valve', 1), ('Sealant and tape', 1)], .44, 65, 35, 0),
    ('Water heater replacement', 'Water heater, tankless', 'Best', 6.0, [('Water heater, tankless', 1), ('Flex connectors', 2), ('Relief valve', 1), ('Pipe fittings kit', 1), ('Shut-off valve', 2)], .45, 90, 35, 0),
    ('Leak repair', 'Supply line and shut-off valve', '', 1.0, [('Supply line', 2), ('Shut-off valve', 1)], .70, 0, 0, 0),
    ('Leak repair', 'Pipe section repair', '', 2.2, [('Copper pipe, 10 ft', 1), ('Pipe fittings kit', 1)], .62, 0, 0, 0),
    ('Leak repair', 'Faucet cartridge and fixture seal', '', 1.2, [('Faucet cartridge', 1), ('Sealant and tape', 1)], .68, 0, 0, 0),
    ('Leak repair', 'Toilet repair parts', '', 1.0, [('Toilet fill valve kit', 1), ('Wax ring kit', 1)], .70, 0, 0, 0),
    ('Leak repair', 'Hose bib replacement', '', 1.4, [('Hose bib', 1), ('Sealant and tape', 1)], .66, 0, 0, 0),
    ('Leak repair', 'Pressure regulator replacement', '', 2.4, [('Pressure regulator', 1), ('Pipe fittings kit', 1)], .60, 0, 0, 0),
    ('Drain clearing', 'Kitchen drain clearing', '', 1.0, [('Drain cable section', 1)], .76, 0, 0, 0),
    ('Drain clearing', 'Bathroom drain clearing', '', .9, [('Drain cable section', 1)], .76, 0, 0, 0),
    ('Drain clearing', 'Main line clearing', '', 2.0, [('Drain cable section', 1), ('Drain cleanout cap', 1)], .72, 0, 0, 0),
    ('Drain clearing', 'Drain clearing with camera', '', 2.4, [('Drain cable section', 1), ('Cleaning chemicals', 1)], .70, 0, 0, 0),
    ('Fixture install', 'Faucet installation', '', 1.3, [('Faucet, kitchen', 1), ('Supply line', 2)], .56, 0, 0, 0),
    ('Fixture install', 'Bathroom faucet installation', '', 1.1, [('Faucet, bathroom', 1), ('Supply line', 2)], .56, 0, 0, 0),
    ('Fixture install', 'Toilet installation', '', 1.6, [('Toilet', 1), ('Wax ring kit', 1), ('Supply line', 1)], .54, 0, 25, 0),
    ('Fixture install', 'Garbage disposal installation', '', 1.4, [('Garbage disposal', 1), ('P-trap kit', 1)], .54, 0, 0, 0),
    ('Fixture install', 'Sump pump installation', '', 2.6, [('Sump pump', 1), ('Pipe fittings kit', 1)], .52, 0, 0, 0),
    ('Repipe', 'Partial repipe, PEX', 'Good', 16.0, [('PEX pipe, 100 ft coil', 3), ('PEX fittings kit', 2), ('Shut-off valve', 4), ('Pipe insulation', 4)], .44, 140, 0, 0),
    ('Repipe', 'Whole-home repipe, PEX', 'Better', 26.0, [('PEX pipe, 100 ft coil', 6), ('PEX fittings kit', 4), ('Shut-off valve', 8), ('Pipe insulation', 8), ('Pressure regulator', 1)], .46, 220, 40, 0)]


# ------------------------------------------------------------------ caches and helpers
_CACHE = {}
def _raw(key, fn):
    if key not in _CACHE: _CACHE[key] = fn()
    return _CACHE[key]
def _thin(rows, n):
    if not n or n >= len(rows): return rows
    k = min(max(3, n // 5), n)
    if k >= n: return rows[-n:]
    recent = rows[-k:]; rest = rows[:-k]; m = n - k; step = len(rest) / float(m)
    return [rest[int(i * step)] for i in range(m)] + recent
def _out(rows, n=None): return _thin([{k: v for k, v in x.items() if not k.startswith('_')} for x in rows], n)
def _wchoice(r, vals, ws):
    x, acc = r.random() * sum(ws), 0
    for v, w in zip(vals, ws):
        acc += w
        if x <= acc: return v
    return vals[-1]
def _poisson(r, lam):
    if lam <= 0: return 0
    L_ = math.exp(-lam); k = 0; p = 1.0
    while True:
        p *= r.random()
        if p <= L_: return k
        k += 1
def _r5(x): return int(math.ceil(x / (5.0 if x < 1000 else 25.0))) * (5 if x < 1000 else 25)


# ------------------------------------------------------------------ price book
_DESIGN_DAY = TODAY - day(200)
_INSTALL_KINDS = ('Replacement', 'Install', 'Repipe')
_pbf = []
for _i, (_jt, _task, _tier, _hrs, _pl, _m0, _permit, _disp, _sub) in enumerate(_T, 1):
    _kind = JT_OF[_jt]['kind']
    _lab = 66.0 if _kind in _INSTALL_KINDS else 40.0
    _pc_now = sum(PART[p]['unit_cost'] * q for p, q in _pl)
    _pc_des = sum(cost_at(p, _DESIGN_DAY) * q for p, q in _pl)
    _veh = (_hrs + .45) * VEHICLE_HOUR
    _cost_des = _hrs * _lab + _pc_des + _permit + _disp + _sub + _veh
    _price = 94.5 if _jt == 'Agreement visit' else _r5(_cost_des / (1 - _m0))
    if _jt == 'Diagnostic visit': _price = {'Diagnostic visit, heating': DIAG_FEE, 'Diagnostic visit, cooling': DIAG_FEE, 'After-hours diagnostic visit': 149.0}[_task]
    _prev = _price if _jt == 'Agreement visit' else _r5(_price / 1.04) if _price > 100 else _price
    if _prev >= _price and _jt != 'Agreement visit': _prev = _price - 5
    _cost_now = _hrs * _lab + _pc_now + _permit + _disp + _sub + _veh
    _pbf.append(dict(pb_id='PB-%03d' % _i, job_type=_jt, task=_task, tier=_tier, labour_hours=_hrs, parts_cost=R2(_pc_now), permit_fee=float(_permit), disposal=float(_disp),
                           sub_cost=float(_sub), flat_price=float(_price), previous_price=float(_prev), cost=R2(_cost_now), margin=round((_price - _cost_now) / _price, 3),
                           target_margin=JT_OF[_jt]['target_margin'], _parts=_pl, _design=round(_m0, 3)))
PB = {p['pb_id']: p for p in _pbf}
PB_BY_TYPE = {}
for _p in _pbf: PB_BY_TYPE.setdefault(_p['job_type'], []).append(_p)
price_book = [{k: v for k, v in p.items() if not k.startswith('_')} for p in _pbf]


def pb_price(pb, d):
    return pb['flat_price'] if to_date(d) >= D(TODAY.year, 1, 1) else pb['previous_price']


# ------------------------------------------------------------------ customer sites and installed equipment (static)
def _sites_static():
    r = rng('sites'); out = []
    accounts = ['LA-%02d' % i for i in range(1, 15)]
    aw = [1.0 / (i + 1.4) for i in range(14)]
    for i in range(1, 1401):
        st = _wchoice(r, SITE_TYPES, [.62, .24, .09, .05])
        area = r.choice(AREAS)
        acct = ''
        if st == 'Rental' or (st in ('Shop', 'Office') and r.random() < .4): acct = _wchoice(r, accounts, aw)
        out.append(dict(site_id='CS-%04d' % i, site_ref='%s-%04d' % (area[:3].upper(), 1000 + i), area=area, site_type=st, landlord=bool(acct), account=acct if acct else 'CS-%04d' % i,
                        phone=fake_phone(1000 + i), member=False, _last='', _first=''))
    return out


def _equipment_static():
    r = rng('equip'); out = []; k = 1
    makes = ['Make A', 'Make B', 'Make C', 'Make D', 'Make E', 'Make F']
    for s in _raw('sites0', _sites_static):
        n_e = _wchoice(r, [0, 1, 2, 3], [.22, .36, .27, .15])
        for _ in range(n_e):
            et = _wchoice(r, EQUIP_TYPES, [.22, .21, .14, .08, .27, .08])
            age = {'Furnace': r.uniform(1, 24), 'Air conditioner': r.uniform(1, 21), 'Heat pump': r.uniform(.5, 12), 'Boiler': r.uniform(2, 30), 'Water heater': r.uniform(.5, 17),
                   'Mini-split': r.uniform(.5, 10)}[et]
            fuel = {'Furnace': _wchoice(r, FUELS, [.70, .10, .12, .08]), 'Boiler': _wchoice(r, FUELS, [.65, .0, .25, .10]),
                    'Water heater': _wchoice(r, FUELS, [.55, .40, .0, .05])}.get(et, 'Electric')
            inst = TODAY - day(int(age * 365))
            wyrs = 10 if et in ('Heat pump', 'Air conditioner', 'Furnace') and r.random() < .3 else 5 if et != 'Water heater' else 6
            out.append(dict(equipment_id='EQ-%04d' % k, site_id=s['site_id'], type=et, fuel=fuel, install_date=iso(inst), warranty_end=iso(inst + day(int(wyrs * 365))),
                            make=r.choice(makes), model='M%d-%03d' % (r.randint(1, 9), r.randint(100, 990)), serial='SN%07d' % r.randint(1000000, 9999999), _age=age))
            k += 1
    return out


# ------------------------------------------------------------------ maintenance agreements (members), renewals and the tune-up windows
def _windows():
    out = []
    for y in range(HISTORY_START.year, TODAY.year + 1):
        for season, (m1, d1, m2, d2) in zip(VISIT_SEASONS, [(2, 15, 6, 15), (8, 15, 12, 15)]):
            s, e = D(y, m1, d1), D(y, m2, d2)
            if s <= TODAY and e >= HISTORY_START: out.append(dict(season=season, start=s, end=e))
    return out


def _members():
    r = rng('members'); sites = _raw('sites0', _sites_static)
    cand = [s for s in sites if s['site_type'] in ('Home', 'Rental', 'Shop')]
    r.shuffle(cand)
    lo = max(month_start(0), TODAY - day(12)); hi = max(_eom(TODAY), TODAY + day(14)); span = (hi - lo).days
    out = []
    for i in range(430):
        s = cand[i]
        plan = _wchoice(r, PLAN_NAMES, _PLAN_W)
        story = i < 30
        if story:
            target = lo + day(int(span * (i + .5) / 30.0)) if i % 2 == 0 else lo + day(r.randint(0, span))
            if i < 16: target = max(target, TODAY + day(1 + i % 12))      # still open: the renewal date is ahead
            k0 = r.randint(1, 4); start = add_months(target, -12 * k0)
        else:
            start = TODAY - day(int(2100 * (r.random() ** 0.85)) + 10)
        m = dict(site_id=s['site_id'], plan=plan, start=start, billing='Annual' if r.random() < .68 else 'Monthly', story=story, soldby=r.choice(['Tomasz Nowak', 'Kofi Mensah', 'Elena Rossi',
                 'Jamal Whitfield', 'Sven Andersson', 'Diego Morales']), site_type=s['site_type'])
        out.append(m)
    # renewals
    renewals = []
    for i, m in enumerate(out):
        m['end'] = ''; m['renewals'] = 0; m['last_renewed'] = ''; m['open_date'] = ''; m['lapsed'] = False; k = 0
        while True:
            k += 1; a = add_months(m['start'], 12 * k)
            if a > TODAY + day(40): break
            force = m['story'] and a < TODAY - day(14)
            renews = force or r.random() < .86
            price = PLAN[m['plan']]['price'] if a >= D(TODAY.year, 1, 1) else R2(PLAN[m['plan']]['price'] / 1.04)
            ren = ''
            if renews and a <= TODAY + day(25):
                ren = a - day(r.randint(0, 24)) + day(r.randint(0, 4))
                if ren > TODAY: ren = ''
            if m['story'] and i < 16 and a >= TODAY: ren = ''; renews = True
            if ren == '':
                if a < TODAY - day(14) and not renews:
                    renewals.append(dict(_m=m, due_date=a, renewed_on='', outcome='Lapsed', price=price)); m['end'] = a; m['lapsed'] = True; break
                renewals.append(dict(_m=m, due_date=a, renewed_on='', outcome='Open', price=price)); m['open_date'] = a; break
            renewals.append(dict(_m=m, due_date=a, renewed_on=ren, outcome='Renewed', price=price)); m['renewals'] += 1; m['last_renewed'] = ren
            if r.random() < .02 and a < TODAY - day(120) and not m['story']:
                m['end'] = a + day(r.randint(60, 300)); break
    for i, m in enumerate(out):
        m['agreement_id'] = 'AG-%04d' % (i + 1)
        if m['end'] and m['end'] > TODAY: m['end'] = ''
        st = ('Lapsed' if m['lapsed'] else 'Cancelled') if m['end'] else 'Renewal due' if m['open_date'] else 'Active'
        m['status'] = st
        m['renewal_date'] = '' if st in ('Lapsed', 'Cancelled') else (m['open_date'] or add_months(m['start'], 12 * (m['renewals'] + 1)))
        m['price'] = PLAN[m['plan']]['price']
    return dict(members=out, renewals=renewals)


def _agreements(): return _raw('agr', _members)


def _member_periods():
    per = {}
    for m in _agreements()['members']:
        per.setdefault(m['site_id'], []).append((m['start'], m['end'] or TODAY + day(400), m))
    return per


# ------------------------------------------------------------------ the day-by-day simulation: jobs, calls, estimates, visits, callbacks
_TECH_CB = {'Tomasz Nowak': .030, 'Kofi Mensah': .165, 'Elena Rossi': .038, 'Jamal Whitfield': .046, 'Sven Andersson': .036, 'Diego Morales': .030}
_KIND_CB = {'Repair': 1.25, 'Replacement': .9, 'Install': 1.0, 'Drain': .8, 'Repipe': .6, 'Diagnostic': 0.0, 'Tune-up': .25}
_ELIG = {'HVAC': ['Tomasz Nowak', 'Kofi Mensah', 'Elena Rossi'], 'Plumbing': ['Jamal Whitfield', 'Sven Andersson']}
_ELIG_INST = {'HVAC': ['Diego Morales', 'Tomasz Nowak', 'Kofi Mensah'], 'Plumbing': ['Jamal Whitfield', 'Sven Andersson', 'Diego Morales']}
_EST_BY = {'HVAC': (['Tomasz Nowak', 'Kofi Mensah', 'Elena Rossi', 'Diego Morales'], [.40, .25, .15, .20]), 'Plumbing': (['Jamal Whitfield', 'Sven Andersson', 'Diego Morales'], [.5, .4, .1])}
_CLOSE = {'Tomasz Nowak': .60, 'Kofi Mensah': .42, 'Elena Rossi': .50, 'Jamal Whitfield': .54, 'Sven Andersson': .52, 'Diego Morales': .56}
_CALL_VAL = {'No-heat': 460, 'No-cool': 500, 'Leak': 360, 'Drain': 235, 'Quote': 4100, 'Member': 120, 'Tune-up': 140, 'Warranty': 0}
VOL = 1.12
_ASSIST = {'HVAC': 'Amira Haddad', 'Plumbing': "Liam O'Connell"}


def _call_type(jt, d, r):
    if jt in ('Heating repair', 'Boiler repair'): return 'No-heat'
    if jt == 'Cooling repair': return 'No-cool'
    if jt == 'Diagnostic visit': return 'No-heat' if d.month in (10, 11, 12, 1, 2, 3, 4) else 'No-cool'
    if jt in ('Furnace tune-up', 'Air conditioner tune-up'): return 'Tune-up'
    if jt == 'Agreement visit': return 'Member'
    if jt in ('Leak repair',): return 'Leak'
    if jt == 'Drain clearing': return 'Drain'
    if jt in ('Water heater replacement', 'Repipe'): return 'Leak' if r.random() < .35 else 'Quote'
    return 'Quote'


def _sim():
    r = rng('sim')
    sites = _raw('sites0', _sites_static); equip = _raw('equip0', _equipment_static); agr = _agreements()
    eq_by = {}
    for e in equip: eq_by.setdefault(e['site_id'], []).append(e)
    land_idx = [i for i, s in enumerate(sites) if s['landlord']]
    periods = _member_periods()
    end = TODAY + day(7)
    ndays = (end - HISTORY_START).days + 1
    spell = {}; i = 0
    while i < ndays:
        d = HISTORY_START + day(i)
        if d not in spell and d <= TODAY + day(2):
            if d.month in (12, 1, 2) and r.random() < .045: kind = 'cold'
            elif d.month in (6, 7, 8) and r.random() < .05: kind = 'hot'
            else: kind = ''
            if kind:
                for k in range(r.randint(3, 6)): spell[d + day(k)] = kind
                i += 6; continue
        i += 1
    budget = {}
    def rem(t, d):
        k = (t, d)
        if k not in budget:
            wd = d.weekday()
            if wd < 5: b = 8.5 + (2.0 if d in spell and TECH[t]['trade'] == 'HVAC' else 0)
            else:
                w = (d - HISTORY_START).days // 7
                hv = ['Tomasz Nowak', 'Kofi Mensah', 'Elena Rossi'][w % 3]; pl = ['Jamal Whitfield', 'Sven Andersson'][w % 2]
                b = (6.0 if wd == 5 else 4.0) if t in (hv, pl) else 0.0
            budget[k] = b
        return budget[k]
    members_by_site = periods
    planned = {}
    # tune-up visits
    visits = []
    wins = _windows()
    last_w = max(wins, key=lambda x: x['start'])
    for w in wins:
        cur = w is last_w
        for m in agr['members']:
            if PLAN[m['plan']]['visits_per_year'] == 1 and w['season'] == 'Spring cooling check': continue
            if m['start'] > w['end'] - day(30) or (m['end'] and m['end'] < w['start']): continue
            lo = max(w['start'], m['start'] + day(14))
            f = r.betavariate(1.5, 1.9)
            dt_ = lo + day(int((w['end'] - lo).days * f))
            v = dict(_m=m, season=w['season'], window_start=w['start'], window_end=w['end'], planned=dt_, done_on='', status='Due', _job=None)
            if dt_ <= TODAY:
                ok = r.random() < (.58 if cur else .93)
                if ok: planned.setdefault(dt_, []).append(dict(kind='visit', _v=v)); v['status'] = 'Done'
                else: v['status'] = 'Missed' if not cur else 'Due'
            else:
                if cur and r.random() < .30 and dt_ <= TODAY + day(14): planned.setdefault(dt_, []).append(dict(kind='visit', _v=v)); v['status'] = 'Booked'
                else: v['status'] = 'Due'
            visits.append(v)
    jobs = []; est_won = []; lost_calls = []; extra_calls = []
    sites_n = len(sites)

    def pick_site(jt, src):
        if src == 'Property manager' and land_idx: return sites[land_idx[int(len(land_idx) * r.random() ** 1.2)]]
        return sites[min(sites_n - 1, int(sites_n * r.random() ** 1.35))]

    def make_spec(jt, d):
        J = JT_OF[jt]; kind = J['kind']
        w = list(_SRC_W)
        if kind == 'Tune-up': w[4] *= 2.2; w[7] *= 2.0; w[0] *= .5
        if kind in ('Replacement', 'Install', 'Repipe'): w[3] *= 1.6; w[0] *= 1.2
        src = _wchoice(r, SOURCES, w)
        site = pick_site(jt, src)
        pbs = PB_BY_TYPE[jt]
        spec = dict(kind='new', job_type=jt, source=src, site=site, trade=J['trade'])
        if jt == 'Diagnostic visit':
            heat = d.month in (10, 11, 12, 1, 2, 3, 4)
            spec['pb'] = pbs[2] if (d.weekday() >= 5 or r.random() < .15) else pbs[0] if heat else pbs[1]
        elif kind == 'Tune-up': spec['pb'] = pbs[0] if r.random() < .7 else pbs[1]
        elif _JT[jt][7]:
            est = _wchoice(r, _EST_BY[J['trade']][0], _EST_BY[J['trade']][1]); spec['estimator'] = est
            tiered = [p for p in pbs if p['tier']]
            if jt == 'Heat pump install' and r.random() < .3: pb = r.choice([p for p in pbs if not p['tier']]); tier = 'Good'
            else:
                tw = [.26, .50, .24][:len(tiered)]
                pb = _wchoice(r, tiered, tw); tier = pb['tier']
            spec['pb'] = pb; spec['tier'] = tier
        else: spec['pb'] = r.choice(pbs)
        return spec

    def place(spec, d, tries=0):
        pb = spec['pb']; jt = spec['job_type']; J = JT_OF[jt]; kind = J['kind']; trade = spec['trade']
        site = spec['site']
        area = site['area']
        h = round(pb['labour_hours'] * r.uniform(.78, 1.32) * 4) / 4.0
        if spec['kind'] == 'cb': h = round(r.uniform(.8, 2.4) * 4) / 4.0
        dr = round(AREA_DRIVE[area] * r.uniform(.8, 1.3), 2)
        need = min(h + dr, 8.0)
        big = kind in ('Replacement', 'Install', 'Repipe')
        elig = list((_ELIG_INST if big else _ELIG)[trade])
        if jt == 'Boiler repair': elig = ['Tomasz Nowak', 'Elena Rossi', 'Kofi Mensah']
        pref = spec.get('prefer')
        if pref and pref in TECH and r.random() < .65: elig = [pref] + [t for t in elig if t != pref]
        elif (not big) or jt == 'Water heater replacement': elig.sort(key=lambda t: -rem(t, d) - r.random() * .5)
        pick = None
        for t in elig:
            if rem(t, d) + 1e-9 >= need: pick = t; break
        if not pick: return None
        used0 = cap_of(pick, d) - rem(pick, d)
        budget[(pick, d)] = max(0.0, rem(pick, d) - (h + dr))
        # assistant
        asst = ''; ah = 0.0
        if big or (kind == 'Tune-up' and trade == 'HVAC' and r.random() < .30) or r.random() < .06:
            a = _ASSIST[trade]
            if rem(a, d) + 1e-9 >= min(h, 8.0) * .8 and a != pick:
                asst = a; ah = round(h * .9 * 4) / 4.0; budget[(a, d)] = max(0.0, rem(a, d) - ah)
        start = min(7.5 + used0, 17.25)
        return pick, h, dr, asst, ah, start

    def cap_of(t, d):
        wd = d.weekday()
        if wd < 5: return 8.5 + (2.0 if d in spell and TECH[t]['trade'] == 'HVAC' else 0)
        return 6.0 if wd == 5 else 4.0

    def finish(spec, d, got):
        pick, h, dr, asst, ah, start = got
        pb = spec['pb']; jt = spec['job_type']; J = JT_OF[jt]; kind = J['kind']; site = spec['site']
        cb = spec['kind'] == 'cb'; vis = spec['kind'] == 'visit'
        area = site['area']; eqs = eq_by.get(site['site_id'], [])
        want = {'Furnace': ['Furnace'], 'Heating repair': ['Furnace', 'Boiler'], 'Cooling repair': ['Air conditioner', 'Heat pump', 'Mini-split'], 'Diagnostic visit': ['Furnace', 'Air conditioner', 'Heat pump'],
                'Furnace tune-up': ['Furnace'], 'Air conditioner tune-up': ['Air conditioner', 'Heat pump'], 'Agreement visit': ['Furnace', 'Air conditioner', 'Heat pump'],
                'Furnace replacement': ['Furnace'], 'Air conditioner replacement': ['Air conditioner'], 'Heat pump install': ['Heat pump', 'Mini-split', 'Furnace'], 'Boiler repair': ['Boiler'],
                'Water heater replacement': ['Water heater']}.get(jt, [])
        eq = [e for e in eqs if e['type'] in want]
        equipment_id = r.choice(eq)['equipment_id'] if eq else ''
        # price, parts
        mem = None
        for s_, e_, m_ in periods.get(site['site_id'], []):
            if s_ <= d <= e_: mem = m_; break
        units = spec.get('units', 1)
        price = pb_price(pb, d) * units; disc = 0.0
        if vis: price = R2(PLAN[spec['_v']['_m']['plan']]['price'] / PLAN[spec['_v']['_m']['plan']]['visits_per_year'])
        if mem and kind in ('Repair', 'Diagnostic') and not cb and not vis:
            disc = R2(price * MEMBER_DISCOUNT); price = R2(price - disc)
        lines = []
        for pn, q in pb['_parts']:
            lines.append((pn, q * units))
        if kind in ('Replacement', 'Install') and r.random() < .22:
            add = round(r.uniform(150, 620) / 5) * 5; price += add
            lines.append(('Filter, 4 inch', 1)); extra_cost = add * .40
        else: extra_cost = 0.0
        if kind in ('Repair', 'Drain', 'Tune-up') and r.random() < .3 and pb['_parts']:
            lines.append((r.choice(['Sealant and tape', 'Wire and connectors kit', 'Pipe insulation', 'Cleaning chemicals']), 1))
        if cb:
            price = 0.0; disc = 0.0
            lines = [(p, q) for p, q in pb['_parts'] if PART[p]['category'] != 'Equipment' and PART[p]['unit_cost'] < 300][:2] if r.random() < .55 else []
        pcost = R2(sum(cost_at(p, d) * q for p, q in lines) + extra_cost)
        permit = R2(pb['permit_fee'] * units * r.uniform(.9, 1.15)) if pb['permit_fee'] and not cb else 0.0
        disp = pb['disposal'] * units if not cb else 0.0
        sub = 0.0
        if pb['sub_cost'] and not cb and r.random() < .5: sub = R2(pb['sub_cost'] * units / .5 * r.uniform(.8, 1.2))
        lab = R2(h * LOADED[pick] + ah * LOADED.get(asst, 0))
        veh = R2((h + dr) * VEHICLE_HOUR)
        status = 'Scheduled' if d > TODAY else 'Completed'
        if d == TODAY: status = 'Completed' if start < 12.0 else 'In progress'
        if status == 'Completed' and r.random() < .02 and not cb and not vis:
            status = 'Cancelled'
        job = dict(date=d, start=_hm(start), site_id=site['site_id'], area=site['area'], site_type=site['site_type'], account=site['account'], equipment_id=equipment_id, job_type=jt,
                   trade=spec['trade'], kind=kind, reason='', technician=pick, assistant=asst, van=VAN_OF[pick], hours=h, assistant_hours=ah, drive_hours=dr, price=R2(price), discount=disc,
                   parts_cost=pcost, labour_cost=lab, permit_fee=permit, disposal=disp, sub_cost=sub, vehicle_cost=veh, task_id=pb['pb_id'], tier=spec.get('tier', pb['tier']),
                   source=spec.get('source', 'Repeat customer'), status=status, is_callback=cb, warranty=cb and r.random() < .72, agreement_id=(mem['agreement_id'] if mem else ''),
                   permit_needed=bool(pb['permit_fee']) and not cb, parts_ready=True, emergency=False, _lines=lines, _spec=spec, _est=None, _orig=spec.get('_orig'), _v=spec.get('_v'))
        if status == 'Cancelled':
            for k in ('price', 'discount', 'parts_cost', 'labour_cost', 'permit_fee', 'disposal', 'sub_cost', 'vehicle_cost', 'hours', 'assistant_hours'): job[k] = 0.0
            job['_lines'] = []
        if status in ('Scheduled', 'In progress'): job['parts_ready'] = r.random() < .88
        if d in spell and kind in ('Repair', 'Diagnostic') and r.random() < .5: job['emergency'] = True
        if d.weekday() >= 5: job['emergency'] = True
        tot = job['labour_cost'] + job['parts_cost'] + job['permit_fee'] + job['disposal'] + job['sub_cost'] + job['vehicle_cost']
        job['total_cost'] = R2(tot); job['margin'] = R2(job['price'] - tot)
        job['margin_pct'] = round((job['price'] - tot) / job['price'], 4) if job['price'] else 0.0
        if spec.get('estimator') and status != 'Cancelled': est_won.append((job, spec))
        # callbacks
        if not cb and not vis and status == 'Completed' and kind in _KIND_CB and _KIND_CB[kind] > 0 and d <= TODAY:
            if r.random() < _TECH_CB.get(pick, .03) * _KIND_CB[kind]:
                cd = d + day(r.randint(2, 20))
                if cd <= TODAY + day(5):
                    cbspec = dict(kind='cb', job_type=jt, source='Repeat customer', site=site, trade=spec['trade'], pb=pb, prefer=pick, _orig=job, tier=spec.get('tier', pb['tier']))
                    planned.setdefault(cd, []).append(cbspec)
        jobs.append(job)
        if vis: spec['_v']['_job'] = job; spec['_v']['done_on'] = d if d <= TODAY else ''
        return job

    # day loop
    for i in range(ndays):
        d = HISTORY_START + day(i)
        wd = d.weekday()
        wmul = [1, 1, 1, .98, .9, .30, .10][wd]
        sp = spell.get(d, '')
        fut = (d - TODAY).days
        fmul = 1.0 if fut <= 0 else max(.2, .85 - .09 * fut)
        fmul_big = 1.0
        if (TODAY - d).days in (1, 3, 5, 8, 11) and d <= TODAY:
            for jb in reversed(jobs):
                if jb['date'] < d - day(14): break
                if jb['date'] <= d - day(2) and jb['status'] == 'Completed' and not jb['is_callback'] and jb['_v'] is None and jb['kind'] in ('Repair', 'Drain', 'Replacement') and not jb.get('_forced'):
                    jb['_forced'] = True
                    planned.setdefault(d, []).append(dict(kind='cb', job_type=jb['job_type'], source='Repeat customer', site=jb['_spec']['site'], trade=jb['trade'], pb=jb['_spec']['pb'], prefer=jb['technician'],
                                                          _orig=jb, tier=jb['tier'])); break
        queue = planned.pop(d, [])
        demand = []
        for jt, (trade, kind, hrs, tgt, base, wts, spk, estf) in _JT.items():
            if base <= 0: continue
            lam = base * wmul * wts[d.month - 1] * (_IDX[d.month - 1] ** .6) * (fmul_big if kind in ('Replacement', 'Install', 'Repipe') and fut > 0 and wd < 5 else fmul)
            if spk == 'cold' and sp == 'cold': lam *= 1.8
            elif spk == 'hot' and sp == 'hot': lam *= 1.8
            elif spk == 'both' and sp: lam *= 1.6
            elif sp == 'cold' and trade == 'Plumbing' and jt == 'Leak repair': lam *= 1.5
            for _ in range(_poisson(r, lam * VOL)): demand.append(make_spec(jt, d))
        r.shuffle(demand)
        for spec in queue + demand:
            tries_left = 5 if spec['kind'] in ('visit', 'cb') else 0
            dd = d; got = None
            for step in range(tries_left + 1):
                if spec['kind'] == 'visit' and spec['_v']['window_end'] < dd: break
                if spec['kind'] == 'visit':
                    spec.setdefault('pb', PB_BY_TYPE['Agreement visit'][0 if spec['_v']['season'].startswith('Spring') else 1]); spec['job_type'] = 'Agreement visit'
                    spec['site'] = sites[int(spec['_v']['_m']['site_id'][3:]) - 1]; spec['trade'] = 'Plumbing' if spec['_v']['_m']['plan'] == 'Plumbing check' else 'HVAC'
                    spec['source'] = 'Repeat customer'
                if dd.weekday() >= 5 and spec['kind'] != 'new': dd += day(1); continue
                got = place(spec, dd)
                if got: break
                dd += day(1)
            if got:
                finish(spec, dd, got)
            elif spec['kind'] == 'new' and d <= TODAY:
                lost_calls.append(dict(date=d, spec=spec))
            elif spec['kind'] == 'visit':
                spec['_v']['status'] = 'Due'; spec['_v']['done_on'] = ''
    # story install: a two-system light-commercial heat pump job a few days ahead (its equipment invoice falls due this week)
    d = TODAY + day(5)
    while d.weekday() >= 5: d += day(1)
    office = [s for s in sites if s['site_type'] == 'Office'][3]
    sp = dict(kind='new', job_type='Heat pump install', source='Property manager', site=office, trade='HVAC', pb=[p for p in PB_BY_TYPE['Heat pump install'] if p['tier'] == 'Best'][0], tier='Best', units=2,
              estimator='Tomasz Nowak')
    finish(sp, d, ('Diego Morales', 20.0, .5, 'Amira Haddad', 20.0, 7.5))
    return dict(jobs=jobs, est_won=est_won, lost_calls=lost_calls, visits=visits, spell=spell, sites=sites)


# ------------------------------------------------------------------ the world: ids, calls, estimates, permits, invoices and payments
def _call_hour(r, urgent):
    if urgent: return _wchoice(r, list(range(17, 23)), [.3, .25, .2, .12, .08, .05]) + r.random() * .98
    return _wchoice(r, list(range(7, 21)), [.08, .14, .13, .10, .08, .09, .10, .09, .07, .05, .04, .03, .02, .01]) + r.random() * .98


def _world():
    r = rng('world'); S = _raw('sim', _sim); agr = _agreements()
    sites = _raw('sites0', _sites_static)
    jobs = sorted(S['jobs'], key=lambda j: (j['date'], j['start'], j['technician']))
    for i, j in enumerate(jobs, 1): j['job_id'] = 'JB-%05d' % i
    for j in jobs: j['original_job'] = j['_orig']['job_id'] if j['_orig'] else ''
    # ---- estimates
    ests = []
    for job, spec in S['est_won']:
        jt = job['job_type']; lag = r.randint(0, 3) if jt == 'Water heater replacement' else r.randint(2, 12)
        e = job['date'] - day(lag)
        if e < HISTORY_START: e = HISTORY_START
        if e > TODAY: e = TODAY - day(r.randint(0, 3)) if job['date'] > TODAY else e
        pbs = [p for p in PB_BY_TYPE[jt] if p['tier']]
        chosen = spec.get('tier', 'Good'); tiered = bool(PB[job['task_id']]['tier'])
        prices = {'Good': 0.0, 'Better': 0.0, 'Best': 0.0}
        if tiered:
            maxi = {'Repipe': 2}.get(jt, 3)
            ci = TIERS.index(chosen) + 1
            offered = ci if ci == maxi else r.randint(ci, maxi) if ci > 1 else r.randint(1, maxi)
            if ci == 1 and r.random() < .5: offered = maxi
            for p in pbs:
                if TIERS.index(p['tier']) < offered: prices[p['tier']] = pb_price(p, e)
        else:
            offered = 1; prices['Good'] = pb_price(PB[job['task_id']], e); chosen = 'Good'
        ests.append(dict(date=e, site_id=job['site_id'], job_type=jt, technician=spec['estimator'], options_offered=offered, good_price=prices['Good'], better_price=prices['Better'],
                         best_price=prices['Best'], option_chosen=chosen, outcome='Won', price_won=job['price'], lost_reason='', followup_date='', _job=job))
    won_by = {}
    for e in ests: won_by.setdefault(e['technician'], []).append(e)
    lost = []
    for t, lst in won_by.items():
        c = _CLOSE.get(t, .55)
        for e in lst:
            for _ in range(_poisson(r, 1.0 / c - 1)):
                d = e['date'] + day(r.randint(-6, 10)); d = min(max(d, HISTORY_START), TODAY)
                jt = e['job_type']; pbs = [p for p in PB_BY_TYPE[jt] if p['tier']] or PB_BY_TYPE[jt]
                maxi = min(len(pbs), 3); offered = r.randint(1, maxi)
                pr = {'Good': 0.0, 'Better': 0.0, 'Best': 0.0}
                if pbs[0]['tier']:
                    for p in pbs[:offered]: pr[p['tier']] = pb_price(p, d)
                else: pr['Good'] = pb_price(pbs[0], d); offered = 1
                site = sites[min(len(sites) - 1, int(len(sites) * r.random() ** 1.35))]
                outc, reason, fu = 'Lost', _wchoice(r, EST_LOST, [.45, .20, .15, .10, .10]), ''
                if d >= TODAY - day(40) and r.random() < .75: outc = 'Open'; reason = ''; fu = TODAY + day(r.randint(-3, 6))
                lost.append(dict(date=d, site_id=site['site_id'], job_type=jt, technician=t, options_offered=offered, good_price=pr['Good'], better_price=pr['Better'], best_price=pr['Best'],
                                 option_chosen='None', outcome=outc, price_won=0.0, lost_reason=reason, followup_date=fu, _job=None))
    ests = sorted(ests + lost, key=lambda e: (e['date'], e['technician']))
    for i, e in enumerate(ests, 1):
        e['estimate_id'] = 'ES-%05d' % i
        if e['_job']: e['_job']['estimate_id'] = e['estimate_id']; e['job_id'] = e['_job']['job_id']
        else: e['job_id'] = ''
    for j in jobs: j.setdefault('estimate_id', '')
    # ---- calls
    calls = []
    def add_call(date, urgent, source, ctype, outcome, site_id, value, job=None):
        date = min(max(date, HISTORY_START), TODAY)
        h = _call_hour(r, urgent or date.weekday() >= 5)
        after = h >= 17.5 or date.weekday() >= 5
        ans = 'After-hours line' if after else _wchoice(r, ANSWERED_BY[:2], [.84, .16])
        c = dict(date=date, time=_hm(min(h, 23.9)), source=source, call_type=ctype, outcome=outcome, answered_by=ans, site_id=site_id, est_value=float(round(value)), job_id=job['job_id'] if job else '',
                 emergency=bool(urgent or after), _job=job)
        calls.append(c); return c
    est_of = {e['_job']['job_id']: e for e in ests if e['_job']}
    for j in jobs:
        sp = j['_spec']; src = j['source']
        if j['is_callback']:
            c = add_call(j['date'] - day(r.randint(0, 1)), False, 'Repeat customer', 'Warranty', 'Booked', j['site_id'], 0, j); j['reason'] = 'Warranty'; continue
        ct = _call_type(j['job_type'], j['date'], r)
        if j['_v'] is not None:
            add_call(j['date'] - day(r.randint(3, 14)), False, 'Repeat customer', 'Member', 'Booked', j['site_id'], j['price'], j); j['reason'] = 'Member'; continue
        outc = 'Estimate booked' if j['job_id'] in est_of else 'Booked'
        if outc == 'Estimate booked': cd = est_of[j['job_id']]['date'] - day(r.randint(0, 3))
        elif j['kind'] == 'Tune-up': cd = j['date'] - day(r.randint(2, 18))
        else: cd = j['date'] - day(r.choice([0, 0, 0, 0, 1, 1, 2]))
        c = add_call(cd, j['emergency'], src, ct, outc, j['site_id'], j['price'] or _CALL_VAL[ct], j); j['reason'] = ct
        b = _SRC_BOOK[SOURCES.index(src)]
        for _ in range(_poisson(r, (1 - b) / b)):
            u = _wchoice(r, ['Price shopper', 'No slot', 'Outside area', 'Missed call', 'Existing job'], [.36, .06, .14, .34, .10])
            ct2 = _wchoice(r, CALL_TYPES[:5], [.30 if cd.month in (10, 11, 12, 1, 2, 3) else .08, .30 if cd.month in (5, 6, 7, 8, 9) else .08, .16, .14, .16])
            add_call(cd + day(r.choice([-1, 0, 0, 1])), False, src, ct2, u, '' if u != 'Existing job' else j['site_id'], _CALL_VAL[ct2] * r.uniform(.8, 1.25))
    for lc in S['lost_calls']:
        sp = lc['spec']; ct = _call_type(sp['job_type'], lc['date'], r)
        add_call(lc['date'], False, sp['source'], ct, 'No slot', '', _CALL_VAL[ct] * r.uniform(.85, 1.2))
    calls.sort(key=lambda c: (c['date'], c['time']))
    for i, c in enumerate(calls, 1):
        c['call_id'] = 'CL-%05d' % i
        if c['_job']: c['_job']['call_id'] = c['call_id']
    for j in jobs: j.setdefault('call_id', '')
    # ---- callbacks
    cbs = []
    for j in jobs:
        if j['is_callback']:
            o = j['_orig']
            cbs.append(dict(date=j['date'], original_job=o['job_id'], callback_job=j['job_id'], technician=o['technician'], job_type=j['job_type'], site_id=j['site_id'],
                            reason=_wchoice(r, CALLBACK_REASONS, [.32, .22, .18, .12, .16]), hours=j['hours'], drive_hours=j['drive_hours'], parts_cost=j['parts_cost'], cost=j['total_cost'],
                            warranty=j['warranty'], days_after=(j['date'] - o['date']).days))
    for i, c in enumerate(cbs, 1): c['callback_id'] = 'CB-%04d' % i
    # ---- permits
    permits = []
    sched_blocked = 0
    for j in jobs:
        if not j['permit_needed'] or j['status'] == 'Cancelled': continue
        d = j['date']; applied = max(HISTORY_START, d - day(r.randint(9, 28))); wait = r.randint(2, 15) if d <= TODAY else r.randint(2, 7)
        appr = applied + day(wait)
        if appr >= d: appr = d - day(r.randint(1, 3)); applied = min(applied, appr - day(2))
        if d > TODAY:
            applied = min(applied, TODAY - day(r.randint(0, 6)))
            if sched_blocked < 3 and d <= TODAY + day(6): applied = TODAY - day(r.randint(9, 17)); appr = ''; sched_blocked += 1
            else:
                appr = applied + day(wait)
                if appr > TODAY: appr = ''
        insp = (d + day(r.randint(1, 6)) if d < TODAY - day(7) else d + day(r.randint(2, 6))) if d <= TODAY else ''
        passed = insp if insp != '' and insp <= TODAY else ''
        if appr == '': st = 'Applied'
        elif passed != '': st = 'Passed'
        elif insp != '': st = 'Inspection booked'
        else: st = 'Approved'
        dw = ((appr or TODAY) - applied).days
        permits.append(dict(job_id=j['job_id'], site_id=j['site_id'], job_type=j['job_type'], technician=j['technician'], job_date=d, applied_on=applied, fee=j['permit_fee'], approved_on=appr,
                            inspection_on=insp, passed_on=passed, status=st, days_waiting=dw, _job=j))
        if appr == '' and d <= TODAY + day(6): j['parts_ready'] = j['parts_ready']
    recent_p = sorted([p for p in permits if p['job_date'] <= TODAY and (TODAY - p['job_date']).days <= 12], key=lambda p: p['job_date'])[-3:]
    for p in recent_p:
        p['inspection_on'] = TODAY + day(r.randint(1, 4)); p['passed_on'] = ''; p['status'] = 'Inspection booked'
    for i, p in enumerate(permits, 1): p['permit_id'] = 'PM-%04d' % i
    # ---- invoices and payments
    invoices = []; payments = []
    for j in jobs:
        if j['status'] in ('Cancelled', 'Scheduled', 'In progress') or j['_v'] is not None or j['price'] <= 0: continue
        age_ = (TODAY - j['date']).days
        if (3 <= age_ <= 12 and r.random() < .16) or (13 <= age_ <= 60 and r.random() < .006): continue       # finished but not invoiced yet
        big = j['kind'] in ('Replacement', 'Install', 'Repipe'); price = j['price']
        home = j['site_type'] == 'Home'; d = j['date']
        fin = big and price >= 4000 and home and r.random() < .22
        dep_ask = 0.0; dep_paid = 0.0; dep_date = ''
        if big and price >= 1500 and not fin:
            dep_ask = float(round(price * DEPOSIT_PCT / 10.0) * 10); dep_date = d - day(r.randint(3, 14))
            if dep_date <= TODAY and dep_date >= HISTORY_START - day(20): dep_paid = dep_ask
        inv = dict(job_id=j['job_id'], date=d, site_id=j['site_id'], account=j['account'], site_type=j['site_type'], job_type=j['job_type'], technician=j['technician'], amount=price,
                   deposit_asked=dep_ask, deposit_paid=dep_paid, financing=fin, terms_days=TERMS_HOME if home else TERMS_LANDLORD, _job=j, _dep_date=dep_date)
        invoices.append(inv)
    # deposits for scheduled installs (no invoice yet)
    for j in jobs:
        if j['date'] > TODAY and j['kind'] in ('Replacement', 'Install', 'Repipe') and j['price'] >= 1500 and j['status'] != 'Cancelled':
            dd = j['date'] - day(r.randint(3, 14))
            if dd <= TODAY:
                ask = float(round(j['price'] * DEPOSIT_PCT / 10.0) * 10)
                payments.append(dict(date=dd, invoice_id='', job_id=j['job_id'], account=j['account'], site_id=j['site_id'], amount=ask, method=_wchoice(r, ['Card online', 'Bank transfer'], [.7, .3]), kind='Deposit'))
    final = []
    for inv in invoices:
        if inv.get('_pending'): continue
        j = inv['_job']; d = inv['date']; home = inv['site_type'] == 'Home'; late_ok = True
        due_amt = R2(inv['amount'] - inv['deposit_paid'])
        if inv['financing']: lag = r.randint(3, 6); method = 'Financing offer'
        elif home:
            u = r.random()
            if u < .60: lag, method = 0, 'Card on site'
            elif u < .80: lag, method = r.randint(1, 5), 'Card online'
            elif u < .90: lag, method = r.randint(0, 2), 'Cash or cheque'
            elif u < .96: lag, method = r.randint(3, 12), 'Bank transfer'
            else: lag, method = r.randint(14, 45), 'Card online'
        else:
            lag = int(min(52, max(4, r.gauss(26, 10)))); method = _wchoice(r, ['Bank transfer', 'Cash or cheque'], [.7, .3])
            if r.random() < .10: lag = r.randint(55, 58)
            elif r.random() < .03: lag = r.randint(60, 95)
        pd_ = d + day(lag)
        age = (TODAY - d).days
        if pd_ > TODAY and age > 58: pd_ = TODAY - day(r.randint(1, 10))
        inv['_final_date'] = pd_; inv['_final_amt'] = due_amt; inv['method'] = method
    # write-offs: a few old small business invoices
    olds = [x for x in invoices if not x.get('_pending') and not x['site_type'] == 'Home' and (TODAY - x['date']).days > 220 and x['amount'] <= 650 and not x['deposit_asked']]
    for x in olds[::max(1, len(olds) // 6)][:6]: x['_writeoff'] = True
    for inv in invoices:
        if inv.get('_pending'):
            inv['method'] = ''; inv['paid_amount'] = inv['deposit_paid']; inv['paid_on'] = ''; continue
        pay = inv['deposit_paid']; po = ''
        if inv['deposit_paid']:
            payments.append(dict(date=inv['_dep_date'], invoice_id='', job_id=inv['job_id'], account=inv['account'], site_id=inv['site_id'], amount=inv['deposit_paid'],
                                 method=_wchoice(r, ['Card online', 'Bank transfer'], [.7, .3]), kind='Deposit', _inv=inv))
        if inv.get('_writeoff'):
            inv['paid_amount'] = pay; inv['paid_on'] = ''; inv['status'] = 'Written off'; inv['method'] = ''; continue
        if inv['_final_date'] <= TODAY:
            payments.append(dict(date=inv['_final_date'], invoice_id='', job_id=inv['job_id'], account=inv['account'], site_id=inv['site_id'], amount=inv['_final_amt'], method=inv['method'], kind='Invoice', _inv=inv))
            pay = R2(pay + inv['_final_amt']); po = inv['_final_date']
        else: inv['method'] = ''
        inv['paid_amount'] = R2(pay); inv['paid_on'] = po
    # story: a landlord invoice unpaid for more than 60 days
    cand = [x for x in invoices if x['account'].startswith('LA-') and not x.get('_pending') and 91 <= (TODAY - x['date']).days <= 115 and x['amount'] >= 1000 and not x['deposit_asked']]
    if not cand: cand = [x for x in invoices if x['account'].startswith('LA-') and not x.get('_pending') and 80 <= (TODAY - x['date']).days <= 110 and x['amount'] >= 900 and not x['deposit_asked']]
    st_inv = sorted(cand, key=lambda x: -x['amount'])[0]
    st_inv['_story'] = True; st_inv['method'] = ''; st_inv['paid_amount'] = 0.0; st_inv['paid_on'] = ''; st_inv['_writeoff'] = False
    st_inv['status'] = 'Unpaid'
    payments = [p for p in payments if p.get('_inv') is not st_inv]
    # agreement fee payments
    for m in agr['members']:
        site = sites[int(m['site_id'][3:]) - 1]
        def pr(dt_): return PLAN[m['plan']]['price'] if dt_ >= D(TODAY.year, 1, 1) else R2(PLAN[m['plan']]['price'] / 1.04)
        if m['billing'] == 'Annual':
            dates = [m['start']] + [x['renewed_on'] for x in agr['renewals'] if x['_m'] is m and x['renewed_on'] != '']
            for dd in dates:
                if HISTORY_START <= dd <= TODAY: payments.append(dict(date=dd, invoice_id='', job_id='', account=site['account'], site_id=m['site_id'], amount=pr(dd), method=_wchoice(r, ['Card online', 'Bank transfer'], [.75, .25]), kind='Agreement fee'))
        else:
            k = 0; stop = m['end'] or TODAY
            while True:
                dd = add_months(m['start'], k); k += 1
                if dd > min(stop, TODAY): break
                if dd >= HISTORY_START: payments.append(dict(date=dd, invoice_id='', job_id='', account=site['account'], site_id=m['site_id'], amount=R2(pr(dd) / 12.0), method='Card online', kind='Agreement fee'))
    payments.sort(key=lambda p: (p['date'], p['kind']))
    invoices.sort(key=lambda x: (x['date'], x['job_id']))
    for i, x in enumerate(invoices, 1):
        x['invoice_id'] = 'IV-%05d' % i; x['_job']['invoice_id'] = x['invoice_id']
        x['month'] = _ms(x['date']); x['due_date'] = x['date'] + day(x['terms_days'])
        if x.get('_pending'): x['status'] = 'Unpaid'
        elif x.get('_writeoff') or x.get('_story'): pass
        else:
            bal = R2(x['amount'] - x['paid_amount'])
            x['status'] = 'Paid' if bal <= 0.01 else 'Part paid' if x['paid_amount'] > 0 else 'Unpaid'
        x['balance'] = R2(x['amount'] - x['paid_amount']) if x['status'] != 'Written off' else 0.0
    for p in payments:
        if p.get('_inv'): p['invoice_id'] = p['_inv']['invoice_id']
    for i, p in enumerate(payments, 1): p['payment_id'] = 'PY-%05d' % i; p['month'] = _ms(p['date'])
    for j in jobs: j.setdefault('invoice_id', '')
    # visits
    vis = S['visits']
    for v in vis:
        jb = v['_job']
        if jb is not None and jb['status'] != 'Cancelled':
            v['status'] = 'Done' if jb['date'] <= TODAY else 'Booked'; v['done_on'] = jb['date'] if jb['date'] <= TODAY else ''; v['planned'] = jb['date']
        elif v['status'] == 'Done': v['status'] = 'Missed' if v['window_end'] < TODAY else 'Due'; v['done_on'] = ''
        if v['status'] == 'Due' and v['window_end'] < TODAY: v['status'] = 'Missed'
    vis.sort(key=lambda v: (v['window_start'], v['planned'], v['_m']['agreement_id']))
    for i, v in enumerate(vis, 1): v['visit_id'] = 'VT-%05d' % i
    return dict(jobs=jobs, ests=ests, calls=calls, cbs=cbs, permits=permits, invoices=invoices, payments=payments, visits=vis, sites=sites, members=agr['members'], renewals=agr['renewals'])


def _w(): return _raw('world', _world)


# ------------------------------------------------------------------ public generators (fresh lists of dicts, oldest first; n= thins but keeps the most recent rows)
def _dd(x): return iso(x) if x != '' else ''
def _pub_job(j):
    keys = ['job_id', 'date', 'start', 'site_id', 'area', 'site_type', 'account', 'equipment_id', 'job_type', 'trade', 'kind', 'reason', 'technician', 'assistant', 'van', 'hours', 'assistant_hours',
            'drive_hours', 'price', 'discount', 'parts_cost', 'labour_cost', 'permit_fee', 'disposal', 'sub_cost', 'vehicle_cost', 'total_cost', 'margin', 'margin_pct', 'task_id', 'tier', 'source',
            'status', 'is_callback', 'original_job', 'warranty', 'agreement_id', 'permit_needed', 'parts_ready', 'emergency', 'call_id', 'estimate_id', 'invoice_id']
    o = {k: j[k] for k in keys}; o['date'] = iso(j['date']); o['week'] = iso(week_start(j['date'])); o['month'] = iso(_ms(j['date'])); o['weekday'] = WEEKDAYS7[j['date'].weekday()]
    return o


def job_rows(n=None): return _thin([_pub_job(j) for j in _w()['jobs']], n)
def call_rows(n=None):
    return _thin([dict(call_id=c['call_id'], date=iso(c['date']), month=iso(_ms(c['date'])), weekday=WEEKDAYS7[c['date'].weekday()], time=c['time'], source=c['source'], call_type=c['call_type'],
                       outcome=c['outcome'], answered_by=c['answered_by'], site_id=c['site_id'], est_value=c['est_value'], job_id=c['job_id'], emergency=c['emergency']) for c in _w()['calls']], n)
def estimate_rows(n=None):
    return _thin([dict(estimate_id=e['estimate_id'], date=iso(e['date']), month=iso(_ms(e['date'])), site_id=e['site_id'], job_type=e['job_type'], technician=e['technician'],
                       options_offered=e['options_offered'], good_price=e['good_price'], better_price=e['better_price'], best_price=e['best_price'], option_chosen=e['option_chosen'],
                       outcome=e['outcome'], price_won=e['price_won'], lost_reason=e['lost_reason'], followup_date=_dd(e['followup_date']), job_id=e['job_id']) for e in _w()['ests']], n)
def invoice_rows(n=None):
    return _thin([dict(invoice_id=x['invoice_id'], job_id=x['job_id'], date=iso(x['date']), month=iso(x['month']), due_date=iso(x['due_date']), site_id=x['site_id'], account=x['account'],
                       site_type=x['site_type'], job_type=x['job_type'], technician=x['technician'], amount=x['amount'], deposit_asked=x['deposit_asked'], deposit_paid=x['deposit_paid'],
                       financing=x['financing'], method=x['method'], paid_amount=x['paid_amount'], paid_on=_dd(x['paid_on']), balance=x['balance'], terms_days=x['terms_days'],
                       status=x['status']) for x in _w()['invoices']], n)
def payment_rows(n=None):
    return _thin([dict(payment_id=p['payment_id'], date=iso(p['date']), month=iso(p['month']), invoice_id=p['invoice_id'], job_id=p['job_id'], account=p['account'], site_id=p['site_id'],
                       amount=p['amount'], method=p['method'], kind=p['kind']) for p in _w()['payments']], n)
def permit_rows(n=None):
    return _thin([dict(permit_id=p['permit_id'], job_id=p['job_id'], site_id=p['site_id'], job_type=p['job_type'], technician=p['technician'], job_date=iso(p['job_date']), applied_on=iso(p['applied_on']),
                       fee=p['fee'], approved_on=_dd(p['approved_on']), inspection_on=_dd(p['inspection_on']), passed_on=_dd(p['passed_on']), status=p['status'], days_waiting=p['days_waiting'])
                  for p in sorted(_w()['permits'], key=lambda p: p['applied_on'])], n)
def callback_rows(n=None):
    return _thin([dict(callback_id=c['callback_id'], date=iso(c['date']), month=iso(_ms(c['date'])), original_job=c['original_job'], callback_job=c['callback_job'], technician=c['technician'],
                       job_type=c['job_type'], site_id=c['site_id'], reason=c['reason'], hours=c['hours'], drive_hours=c['drive_hours'], parts_cost=c['parts_cost'], cost=c['cost'], warranty=c['warranty'],
                       days_after=c['days_after']) for c in _w()['cbs']], n)
def agreement_rows(n=None):
    out = []; w = _w()
    done = {}
    for v in w['visits']:
        if v['status'] == 'Done': done[v['_m']['agreement_id']] = done.get(v['_m']['agreement_id'], 0) + 1
    for m in w['members']:
        out.append(dict(agreement_id=m['agreement_id'], site_id=m['site_id'], site_type=m['site_type'], plan=m['plan'], price=PLAN[m['plan']]['price'], visits_per_year=PLAN[m['plan']]['visits_per_year'],
                        billing=m['billing'], start_date=iso(m['start']), end_date=_dd(m['end']), renewal_date=_dd(m['renewal_date']), last_renewed=_dd(m['last_renewed']), renewals=m['renewals'],
                        status=m['status'], sold_by=m['soldby'], visits_done=done.get(m['agreement_id'], 0)))
    return _thin(out, n)
def renewal_rows(n=None):
    rows = sorted(_w()['renewals'], key=lambda x: x['due_date'])
    return _thin([dict(renewal_id='RN-%04d' % i, agreement_id=x['_m']['agreement_id'], site_id=x['_m']['site_id'], plan=x['_m']['plan'], due_date=iso(x['due_date']), month=iso(_ms(x['due_date'])),
                       renewed_on=_dd(x['renewed_on']), outcome=x['outcome'], price=x['price']) for i, x in enumerate(rows, 1)], n)
def visit_rows(n=None):
    return _thin([dict(visit_id=v['visit_id'], agreement_id=v['_m']['agreement_id'], site_id=v['_m']['site_id'], plan=v['_m']['plan'], season=v['season'], window_start=iso(v['window_start']),
                       window_end=iso(v['window_end']), planned_date=iso(v['planned']), done_on=_dd(v['done_on']), technician=v['_job']['technician'] if v['_job'] else '',
                       job_id=v['_job']['job_id'] if v['_job'] else '', status=v['status']) for v in _w()['visits']], n)
def parts_used_rows(n=None):
    out = []
    for j in _w()['jobs']:
        if j['status'] not in ('Completed', 'In progress'): continue
        for pn, q in j['_lines']:
            p = PART[pn]; c = cost_at(pn, j['date'])
            out.append(dict(date=iso(j['date']), job_id=j['job_id'], van=j['van'], technician=j['technician'], part_id=p['part_id'], part=pn, category=p['category'], qty=q, unit_cost=c, cost=R2(c * q),
                            from_van=p['category'] != 'Equipment', billed=not (p['category'] != 'Equipment' and _unbilled(j, pn)), month=iso(_ms(j['date']))))
    for i, x in enumerate(out, 1): x['use_id'] = 'UP-%06d' % i
    return _thin(out, n)
def _unbilled(j, pn):
    h = int(hashlib.md5((j['job_id'] + pn).encode()).hexdigest()[:6], 16) % 1000
    return h < (65 if j['technician'] == 'Sven Andersson' else 22)


def site_rows(n=None):
    w = _w(); last = {}; first = {}; cnt = {}; rev = {}
    for j in w['jobs']:
        if j['status'] != 'Completed': continue
        s = j['site_id']; first.setdefault(s, j['date']); last[s] = j['date']; cnt[s] = cnt.get(s, 0) + 1; rev[s] = rev.get(s, 0.0) + j['price']
    mem = {m['site_id'] for m in w['members'] if m['status'] in ('Active', 'Renewal due')}
    neq = {}
    for e in _raw('equip0', _equipment_static): neq[e['site_id']] = neq.get(e['site_id'], 0) + 1
    return _thin([dict(site_id=s['site_id'], site_ref=s['site_ref'], area=s['area'], site_type=s['site_type'], landlord=s['landlord'], account=s['account'], phone=s['phone'],
                       member=s['site_id'] in mem, equipment=neq.get(s['site_id'], 0), jobs=cnt.get(s['site_id'], 0), first_job=_dd(first.get(s['site_id'], '')), last_job=_dd(last.get(s['site_id'], '')),
                       revenue=R2(rev.get(s['site_id'], 0.0))) for s in w['sites']], n)
def equipment_rows(n=None):
    last = {}
    for j in _w()['jobs']:
        if j['status'] == 'Completed' and j['equipment_id'] and j['kind'] in ('Tune-up', 'Repair', 'Replacement', 'Install'): last[j['equipment_id']] = j['date']
    return _thin([dict(equipment_id=e['equipment_id'], site_id=e['site_id'], type=e['type'], fuel=e['fuel'], install_date=e['install_date'], warranty_end=e['warranty_end'], make=e['make'], model=e['model'],
                       serial=e['serial'], last_service=_dd(last.get(e['equipment_id'], ''))) for e in _raw('equip0', _equipment_static)], n)


def _tech_weeks():
    jobs = [j for j in _w()['jobs'] if j['status'] in ('Completed', 'In progress')]
    billed = {}; drive = {}
    for j in jobs:
        k = (j['technician'], week_start(j['date'])); billed[k] = billed.get(k, 0.0) + j['hours']; drive[k] = drive.get(k, 0.0) + j['drive_hours']
        if j['assistant']:
            k2 = (j['assistant'], week_start(j['date'])); billed[k2] = billed.get(k2, 0.0) + j['assistant_hours']; drive[k2] = drive.get(k2, 0.0) + j['drive_hours'] * .5
    return billed, drive


def timesheet_rows(n=None):
    r = rng('ts'); billed, drive = _tech_weeks(); out = []
    w = week_start(HISTORY_START)
    while w <= week_start(TODAY):
        for t in techs:
            if to_date(t['start']) > w + day(6): continue
            b = round(billed.get((t['name'], w), 0.0), 2); dv = round(drive.get((t['name'], w), 0.0), 2)
            shop = round(r.uniform(1.5, 4.0) * 4) / 4.0
            need = b + dv + shop
            clock = max(40.0, round(need * 4) / 4.0)
            if w == week_start(TODAY): clock = max(round((TODAY.weekday() + 1) * 8.0), round(need * 4) / 4.0)
            idle = round(max(0.0, clock - need), 2); ot = round(max(0.0, clock - 40.0), 2) if w < week_start(TODAY) else 0.0
            rate = t['hourly_rate']; gross = R2(min(clock, 40) * rate + ot * rate * 1.5) if w < week_start(TODAY) else R2(clock * rate)
            out.append(dict(week=iso(w), month=iso(_ms(w)), technician=t['name'], role=t['role'], clock_hours=clock, billed_hours=b, drive_hours=dv, shop_hours=shop, idle_hours=idle,
                            overtime_hours=ot, paid_hours=clock, gross_pay=gross, loaded_cost=R2(gross * (1 + BURDEN_PCT))))
        w += day(7)
    for i, x in enumerate(out, 1): x['ts_id'] = 'TS-%05d' % i
    return _thin(out, n)


def _comm_by_month():
    c = {}
    for e in _w()['ests']:
        if e['outcome'] == 'Won':
            t = TECH.get(e['technician'])
            if t and t['commission_pct']: k = (e['technician'], _ms(e['date'])); c[k] = c.get(k, 0.0) + e['price_won'] * t['commission_pct']
    return c


def _last_weekday(d):
    d = _eom(d)
    while d.weekday() >= 5: d -= day(1)
    return d


def pay_rows(n=None):
    ts = timesheet_rows(); comm = _comm_by_month(); out = []; by = {}
    for x in ts: k = (x['technician'], to_date(x['month'])); by.setdefault(k, [0.0, 0.0]); by[k][0] += x['paid_hours']; by[k][1] += x['gross_pay']
    spiff = {}
    for m in _w()['members']:
        k = (m['soldby'], _ms(m['start'])); spiff[k] = spiff.get(k, 0.0) + SPIFF_AGREEMENT
    for mi in range(24):
        M = month_start(23 - mi)
        for s in staff:
            if to_date(s['start']) > _eom(M): continue
            nm = s['name']; pd_ = _last_weekday(M); cur = M == month_start(0)
            if s['role'] == 'Owner': hrs, gross, cm, burden, total = 0.0, OWNER_DRAW, 0.0, 0.0, OWNER_DRAW
            elif s['role'] == 'Office manager': hrs = 173.0; gross = s['monthly_salary']; cm = 0.0; burden = R2(gross * BURDEN_PCT); total = R2(gross + burden)
            else:
                hrs, gross = by.get((nm, M), [0.0, 0.0]); cm = R2(comm.get((nm, M), 0.0) + spiff.get((nm, M), 0.0)); burden = R2((gross + cm) * BURDEN_PCT); total = R2(gross + cm + burden)
                if hrs == 0: continue
            out.append(dict(month=iso(M), person=nm, role=s['role'], pay_type=s['pay_type'], hours=round(hrs, 2), gross=R2(gross), commission=cm, burden=burden, total=total, pay_date=iso(pd_),
                            status='Accruing' if cur else 'Paid'))
    for i, x in enumerate(out, 1): x['pay_id'] = 'PR-%04d' % i
    return _thin(out, n)


# ------------------------------------------------------------------ vans, stock, purchases, vehicles
_TRACK = ['Igniter', 'Flame sensor', 'Run capacitor', 'Contactor', 'Shut-off valve', 'Supply line', 'Faucet cartridge', 'Toilet fill valve kit', 'Wax ring kit', 'P-trap kit', 'Hose bib',
          'Pipe fittings kit', 'Filter, 1 inch', 'Sealant and tape']
_VAN_PARTS = {'HVAC': ['Heating', 'Cooling', 'Consumable'], 'Plumbing': ['Plumbing', 'Consumable']}
def _count_dates():
    ds = [_last_weekday(month_start(k)) for k in range(11, 1, -1)]
    return ds + [TODAY - day(3)]


def _stock_world():
    r = rng('stock'); out = []; cnt = []
    for v in vans:
        trade = v['trade']; pl = [p for p in parts if p['category'] in _VAN_PARTS[trade] and p['van_max'] > 0]
        if v['van'] == 'Van 6': pl = [p for p in parts if p['category'] in ('Heating', 'Cooling', 'Consumable') and p['van_max'] > 0][:22]
        for p in pl:
            out.append(dict(van=v['van'], part=p['part']))
    return out


def van_stock_rows(n=None):
    r = rng('vanstock'); out = []; recent = _count_dates()[-1]
    miss = {'Van 4': ['Shut-off valve', 'Supply line', 'Faucet cartridge', 'Toilet fill valve kit', 'Wax ring kit', 'P-trap kit', 'Hose bib', 'Pipe fittings kit']}
    for k, row in enumerate(_stock_world(), 1):
        p = PART[row['part']]; mn, mx = p['van_min'], p['van_max']
        on = r.randint(mn, mx) if r.random() > .10 else max(0, mn - r.randint(1, 2))
        short = row['part'] in miss.get(row['van'], [])
        if short: on = max(0, mn - r.randint(2, 4))
        out.append(dict(stock_id='ST-%04d' % k, van=row['van'], part_id=p['part_id'], part=row['part'], category=p['category'], van_min=mn, van_max=mx, on_hand=on, unit_cost=p['unit_cost'],
                        value=R2(on * p['unit_cost']), last_counted=iso(recent), supplier=p['supplier']))
    return _thin(out, n)


def stock_count_rows(n=None):
    r = rng('count'); out = []; dates = _count_dates()
    for di, d in enumerate(dates):
        last = di == len(dates) - 1
        for v in vans:
            trade = v['trade']
            tracked = [t for t in _TRACK if (PART[t]['category'] in _VAN_PARTS[trade])]
            for pn in tracked:
                p = PART[pn]; exp = r.randint(p['van_min'], p['van_max']); var = 0
                u = r.random()
                if u < .09: var = -1
                elif u < .12: var = -2
                elif u < .14: var = 1
                if last and v['van'] == 'Van 4' and pn in ('Shut-off valve', 'Supply line', 'Faucet cartridge', 'Toilet fill valve kit', 'Wax ring kit', 'P-trap kit', 'Hose bib', 'Pipe fittings kit'):
                    var = -r.randint(2, 5)
                elif last and v['van'] != 'Van 4' and var < -1: var = -1
                cnt = max(0, exp + var); var = cnt - exp
                out.append(dict(date=iso(d), van=v['van'], part_id=p['part_id'], part=pn, expected=exp, counted=cnt, variance=var, unit_cost=p['unit_cost'], variance_value=R2(var * p['unit_cost'])))
    for i, x in enumerate(out, 1): x['count_id'] = 'SC-%05d' % i
    return _thin(out, n)


def restock_rows(n=None):
    use = {}
    for j in _w()['jobs']:
        if j['status'] not in ('Completed',) or j['date'] < TODAY - day(430): continue
        for pn, q in j['_lines']:
            if PART[pn]['category'] == 'Equipment': continue
            k = (week_start(j['date']), j['van'], pn); use[k] = use.get(k, 0) + q
    out = []
    for (w, van, pn), q in sorted(use.items()):
        d = w + day(4)
        if d > TODAY: continue
        p = PART[pn]
        out.append(dict(date=iso(d), week=iso(w), van=van, part_id=p['part_id'], part=pn, qty=q, unit_cost=cost_at(pn, d), cost=R2(q * cost_at(pn, d)), supplier=p['supplier']))
    for i, x in enumerate(out, 1): x['restock_id'] = 'RS-%05d' % i
    return _thin(out, n)


def _po_world():
    r = rng('po'); W = _w(); out = []
    wk = {}
    for x in restock_rows(): wk[x['week']] = wk.get(x['week'], 0.0) + x['cost']
    for w, amt in sorted(wk.items()):
        d = to_date(w) + day(4); amt = R2(amt * r.uniform(1.0, 1.12))
        out.append(dict(date=d, supplier='Your parts counter', kind='Parts run', job_id='', amount=amt, terms=30))
    for j in W['jobs']:
        if j['status'] == 'Cancelled': continue
        eq = sum(cost_at(p, j['date']) * q for p, q in j['_lines'] if PART[p]['category'] == 'Equipment')
        if eq > 0:
            d = j['date'] - day(r.randint(3, 9))
            if d > TODAY: d = TODAY - day(r.randint(1, 6))
            if d <= TODAY: out.append(dict(date=d, supplier='Your equipment supplier', kind='Equipment', job_id=j['job_id'], amount=R2(eq * 1.03), terms=30))
        if j['sub_cost'] > 0 and j['date'] + day(4) <= TODAY:
            out.append(dict(date=j['date'] + day(r.randint(2, 6)), supplier='Electrical subcontractor' if j['job_type'] != 'Furnace replacement' or r.random() < .45 else 'Sheet-metal subcontractor',
                            kind='Subcontract', job_id=j['job_id'], amount=j['sub_cost'], terms=30))
    out.sort(key=lambda x: (x['date'], x['kind']))
    # story: a large install's equipment invoice falls due this week (the equipment order is brought forward to 27 days ago)
    fut = {j['job_id'] for j in W['jobs'] if j['date'] > TODAY and j['status'] == 'Scheduled'}
    sched = [x for x in out if x['kind'] == 'Equipment' and x['job_id'] in fut] or [x for x in out if x['kind'] == 'Equipment' and x['job_id'] and x['date'] > TODAY - day(25)]
    big = max(sched, key=lambda x: x['amount'])
    big['date'] = TODAY - day(27); big['terms'] = 30; big['_story'] = True
    for x in out:
        due = x['date'] + day(x['terms']); x['due_date'] = due
        if x.get('_story'): x['paid_on'] = ''; continue
        pd_ = due + day(r.randint(-4, 6))
        x['paid_on'] = pd_ if pd_ <= TODAY - day(1) else ''
    out.sort(key=lambda x: (x['date'], x['kind']))
    for i, x in enumerate(out, 1): x['po_id'] = 'PO-%05d' % i; x['status'] = 'Paid' if x['paid_on'] != '' else 'Open'
    return out


def purchase_rows(n=None):
    return _thin([dict(po_id=x['po_id'], date=iso(x['date']), month=iso(_ms(x['date'])), supplier=x['supplier'], kind=x['kind'], job_id=x['job_id'], amount=x['amount'], due_date=iso(x['due_date']),
                       paid_on=_dd(x['paid_on']), status=x['status']) for x in _raw('po', _po_world)], n)


def vehicle_cost_rows(n=None):
    r = rng('veh'); W = _w(); out = []
    days_ = {}; jobs_ = {}; hrs_ = {}
    for j in W['jobs']:
        if j['status'] != 'Completed': continue
        k = (j['van'], _ms(j['date'])); days_.setdefault(k, set()).add(j['date']); jobs_[k] = jobs_.get(k, 0) + 1; hrs_[k] = hrs_.get(k, 0.0) + j['hours'] + j['drive_hours']
    for mi in range(24):
        M = month_start(23 - mi)
        for v in vans:
            k = (v['van'], M); wd = len(days_.get(k, ())); hr = hrs_.get(k, 0.0)
            fuel = R2(hr * 3.55 + r.uniform(-60, 90) + 380); repairs = R2(r.choice([0, 0, 60, 120, 240, 420, 880]) * r.uniform(.8, 1.3)); tyres = 640.0 if r.random() < .08 else 0.0
            lease = v['lease_monthly']; ins = 210.0
            out.append(dict(month=iso(M), van=v['van'], fuel=fuel, repairs=repairs, tyres=tyres, lease=lease, insurance=ins, total=R2(fuel + repairs + tyres + lease + ins), working_days=wd, jobs=jobs_.get(k, 0)))
    for i, x in enumerate(out, 1): x['vc_id'] = 'VC-%04d' % i
    return _thin(out, n)


# ------------------------------------------------------------------ marketing, reviews, expenses, tools, renewals
def marketing_rows(n=None):
    r = rng('mkt'); W = _w(); calls = {}; booked = {}; rev = {}
    for c in W['calls']:
        k = (c['source'], _ms(c['date'])); calls[k] = calls.get(k, 0) + 1
        if c['outcome'] in ('Booked', 'Estimate booked'): booked[k] = booked.get(k, 0) + 1
        if c['_job'] is not None and c['_job']['status'] == 'Completed': rev[k] = rev.get(k, 0.0) + c['_job']['price']
    out = []
    for mi in range(24):
        M = month_start(23 - mi); idx = _IDX[M.month - 1]
        for s in lead_sources:
            base = s['monthly_cost']; src = s['source']
            if src == 'Search ads': c = base * (.82 + .3 * idx) * r.uniform(.95, 1.05)
            elif src == 'Mailers': c = 1800.0 if M.month in (3, 9) else 0.0
            else: c = base * r.uniform(.92, 1.08)
            k = (src, M)
            out.append(dict(month=iso(M), source=src, spend=R2(c), calls=calls.get(k, 0), booked=booked.get(k, 0), revenue=R2(rev.get(k, 0.0))))
    for i, x in enumerate(out, 1): x['row_id'] = 'MK-%04d' % i
    return _thin(out, n)


def review_rows(n=None):
    r = rng('rev'); out = []; cnt = {}
    for j in _w()['jobs']:
        if j['status'] == 'Completed' and not j['is_callback'] and j['_v'] is None: k = (j['technician'], _ms(j['date'])); cnt[k] = cnt.get(k, 0) + 1
    for mi in range(24):
        M = month_start(23 - mi)
        for t in techs:
            if t['role'] == 'Apprentice' or to_date(t['start']) > _eom(M): continue
            nj = cnt.get((t['name'], M), 0)
            req = int(round(nj * (.42 if t['name'] != 'Kofi Mensah' else .30) * r.uniform(.85, 1.15)))
            rv = int(round(req * r.uniform(.20, .32))); rf = _poisson(r, rv * .4 + .3)
            out.append(dict(month=iso(M), technician=t['name'], jobs=nj, requests_sent=req, reviews_received=rv, referrals=rf))
    for i, x in enumerate(out, 1): x['row_id'] = 'RV-%04d' % i
    return _thin(out, n)


_TOOLS = [('Gauge set', 'Heating and cooling gauges', 340, 6), ('Drain machine', 'Drain cleaning machine', 1250, 8), ('Pipe press tool', 'Press tool for pipe joints', 2100, 8), ('Leak detector', 'Electronic leak detector', 780, 5),
          ('Meter set', 'Electrical meter set', 260, 5), ('Vacuum pump', 'Vacuum pump', 520, 7), ('Cordless tool kit', 'Cordless drill and driver kit', 410, 4), ('Camera scope', 'Drain inspection camera', 1450, 6),
          ('Ladder set', 'Ladders and roof safety kit', 380, 8), ('Torch kit', 'Torch and brazing kit', 290, 6), ('Tablet and mount', 'Field tablet and van mount', 520, 3), ('Pipe threader', 'Pipe threading set', 880, 10)]
def tool_rows(n=None):
    r = rng('tools'); out = []
    for i in range(44):
        k = _TOOLS[i % len(_TOOLS)]; d = TODAY - day(int(r.uniform(5, 700)))
        t = r.choice([x for x in techs if x['role'] != 'Apprentice' or r.random() < .3])
        life = k[3]; cost = R2(k[2] * r.uniform(.85, 1.25))
        out.append(dict(date=iso(d), month=iso(_ms(d)), item=k[0], description=k[1], technician=t['name'], cost=cost, life_years=life, replace_year=d.year + life))
    out.sort(key=lambda x: x['date'])
    for i, x in enumerate(out, 1): x['tool_id'] = 'TL-%04d' % i
    return _thin(out, n)


def licence_rows(n=None):
    r = rng('lic'); out = []
    def add(kind, holder, off, cost, cycle=365):
        due = TODAY + day(off)
        out.append(dict(item=kind, holder=holder, due_date=iso(due - day(cycle)), renewed_on=iso(due - day(cycle) - day(r.randint(3, 14))), cost=cost, status='Renewed'))
        out.append(dict(item=kind, holder=holder, due_date=iso(due), renewed_on='', cost=cost, status='Open'))
    add('Business licence', 'Northline', 212, 380.0)
    add('Liability insurance', 'Northline', 143, 3480.0)
    for i, t in enumerate([x for x in techs if x['role'] != 'Apprentice']):
        add('Trade licence', t['name'], [21, 58, 97, 164, 241, 310][i], 215.0)
        add('Technician training', t['name'], [74, 120, 33, 190, 255, 330][i], 340.0, 730)
    for i, v in enumerate(vans):
        add('Vehicle registration', v['van'], [12, 47, 88, 134, 201, 279][i], 168.0)
        add('Vehicle inspection', v['van'], [40, 66, 105, 150, 222, 300][i], 85.0)
        add('Vehicle insurance', v['van'], [30, 52, 91, 129, 186, 250][i], 1240.0)
    for i, t in enumerate(['Tomasz Nowak', 'Elena Rossi', 'Jamal Whitfield']):
        add('Tool calibration', t, [36, 155, 270][i], 120.0)
    out.sort(key=lambda x: x['due_date'])
    for i, x in enumerate(out, 1): x['licence_id'] = 'LR-%03d' % i
    return _thin(out, n)


def expense_rows(n=None):
    r = rng('exp'); W = _w(); out = []
    def add(d, cat, desc, amt, to, method='Bank transfer'):
        if HISTORY_START <= d <= TODAY: out.append(dict(date=iso(d), month=iso(_ms(d)), category=cat, description=desc, amount=R2(amt), paid_to=to, method=method))
    perm = {}; card = {}
    for j in W['jobs']:
        if j['status'] == 'Completed': perm[_ms(j['date'])] = perm.get(_ms(j['date']), 0.0) + j['permit_fee'] + j['disposal']
    for p in W['payments']:
        if p['method'] in ('Card on site', 'Card online'): card[_ms(p['date'])] = card.get(_ms(p['date']), 0.0) + p['amount']
    veh = {}
    for x in vehicle_cost_rows(): veh.setdefault(to_date(x['month']), []).append(x)
    mk = {}
    for x in marketing_rows(): mk[to_date(x['month'])] = mk.get(to_date(x['month']), 0.0) + x['spend']
    tl = {}
    for x in tool_rows(): tl[to_date(x['month'])] = tl.get(to_date(x['month']), 0.0) + x['cost']
    for mi in range(24):
        M = month_start(23 - mi); yr = M.year == TODAY.year
        add(M, 'Rent and yard', 'Shop and yard rent', 4800.0 if yr else 4600.0, 'Landlord')
        add(M + day(13), 'Utilities', 'Power, water and heating', 560 + (170 if M.month in (12, 1, 2) else 70 if M.month in (7, 8) else 0) + r.randint(-30, 50), 'Utility provider', 'Direct debit')
        add(M + day(4), 'Insurance', 'Liability, vehicle and tools cover', 4100.0 if yr else 3900.0, 'Insurer', 'Direct debit')
        add(M + day(6), 'Software', 'Field-service and phone software', 890.0, 'Software provider', 'Card')
        add(_last_weekday(M), 'Accounting', 'Bookkeeping and payroll run', 650.0, 'Grace Lindqvist')
        add(M + day(8), 'Office supplies', 'Paper, printing and van supplies', 160 + r.randint(0, 120), 'Supply shop', 'Card')
        add(M + day(10), 'Marketing', 'Ads, listings, signs and mailers', mk.get(M, 0.0), 'Ad and print providers', 'Card')
        add(M + day(18), 'Permits and disposal', 'Permit fees and equipment disposal', perm.get(M, 0.0), 'Local office and disposal yard', 'Card')
        add(_last_weekday(M), 'Bank and card fees', 'Card processing and bank fees', card.get(M, 0.0) * .026, 'Bank', 'Direct debit')
        add(_last_weekday(M), 'Tools and equipment', 'Tools and equipment bought', tl.get(M, 0.0), 'Tool suppliers', 'Card')
        for x in veh.get(M, []):
            add(M + day(2), 'Vehicle fuel', x['van'] + ' fuel', x['fuel'], 'Fuel card', 'Card'); add(M + day(15), 'Vehicle lease', x['van'] + ' lease', x['lease'], 'Lease company', 'Direct debit')
            add(M + day(20), 'Vehicle repairs', x['van'] + ' repairs and tyres', x['repairs'] + x['tyres'], 'Garage', 'Card') if x['repairs'] + x['tyres'] > 0 else None
        if M.month in (2, 6, 10): add(M + day(11), 'Training', 'Technician training day', 780.0 * r.uniform(.8, 1.3), 'Training provider', 'Card')
    for x in licence_rows():
        if x['renewed_on'] and HISTORY_START <= to_date(x['renewed_on']) <= TODAY and x['item'] in ('Trade licence', 'Technician training'): add(to_date(x['renewed_on']), 'Training', x['item'], x['cost'], 'Course provider', 'Card')
    out.sort(key=lambda x: (x['date'], x['category']))
    for i, x in enumerate(out, 1): x['expense_id'] = 'EX-%05d' % i
    return _thin(out, n)


# ------------------------------------------------------------------ aggregates: job type and technician by month, profit and loss, tax, cash, bills
def job_type_month_rows(n=None):
    agg = {}
    for j in _w()['jobs']:
        if j['status'] != 'Completed': continue
        k = (_ms(j['date']), j['job_type']); a = agg.setdefault(k, [0, 0.0, 0.0, 0.0])
        a[0] += 1; a[1] += j['price']; a[2] += j['total_cost']; a[3] += j['hours']
    out = []
    for (M, jt), a in sorted(agg.items()):
        out.append(dict(month=iso(M), job_type=jt, jobs=a[0], revenue=R2(a[1]), cost=R2(a[2]), margin=R2(a[1] - a[2]), margin_pct=round((a[1] - a[2]) / a[1], 4) if a[1] else 0.0, hours=round(a[3], 2)))
    for i, x in enumerate(out, 1): x['row_id'] = 'JM-%04d' % i
    return _thin(out, n)


def tech_month_rows(n=None):
    agg = {}
    for j in _w()['jobs']:
        if j['status'] != 'Completed': continue
        k = (_ms(j['date']), j['technician']); a = agg.setdefault(k, [0, 0.0, 0.0, 0.0, 0])
        a[0] += 1; a[1] += j['price']; a[2] += j['total_cost']; a[3] += j['hours']; a[4] += 1 if j['is_callback'] else 0
    out = []
    for (M, t), a in sorted(agg.items()):
        out.append(dict(month=iso(M), technician=t, jobs=a[0], revenue=R2(a[1]), cost=R2(a[2]), margin=R2(a[1] - a[2]), billed_hours=round(a[3], 2), callbacks=a[4]))
    for i, x in enumerate(out, 1): x['row_id'] = 'TM-%04d' % i
    return _thin(out, n)


def pnl_rows(n=None):
    agg = {}
    for j in _w()['jobs']:
        if j['status'] != 'Completed': continue
        a = agg.setdefault(_ms(j['date']), dict(revenue=0.0, materials=0.0, sub=0.0, permits=0.0, jobs=0))
        a['revenue'] += j['price']; a['materials'] += j['parts_cost']; a['sub'] += j['sub_cost']; a['permits'] += j['permit_fee'] + j['disposal']; a['jobs'] += 1
    pay = {}; office = {}
    for x in pay_rows():
        M = to_date(x['month'])
        if x['role'] == 'Owner': continue
        if x['role'] == 'Office manager': office[M] = office.get(M, 0.0) + x['total']
        else: pay[M] = pay.get(M, 0.0) + x['total']
    veh = {}
    for x in vehicle_cost_rows(): veh[to_date(x['month'])] = veh.get(to_date(x['month']), 0.0) + x['total']
    oh = {}
    for x in expense_rows():
        if x['category'] in ('Vehicle fuel', 'Vehicle repairs', 'Vehicle lease', 'Permits and disposal'): continue
        oh[to_date(x['month'])] = oh.get(to_date(x['month']), 0.0) + x['amount']
    out = []
    for mi in range(24):
        M = month_start(23 - mi); a = agg.get(M, dict(revenue=0.0, materials=0.0, sub=0.0, permits=0.0, jobs=0))
        gp = a['revenue'] - a['materials'] - a['sub'] - a['permits'] - pay.get(M, 0.0)
        ov = oh.get(M, 0.0) + office.get(M, 0.0); net = gp - veh.get(M, 0.0) - ov
        out.append(dict(month=iso(M), season=_SEAS[M.month - 1], jobs=a['jobs'], revenue=R2(a['revenue']), materials=R2(a['materials']), subcontract=R2(a['sub']), permits_disposal=R2(a['permits']),
                        technician_pay=R2(pay.get(M, 0.0)), gross_profit=R2(gp), vehicles=R2(veh.get(M, 0.0)), overhead=R2(ov), net_profit=R2(net)))
    for i, x in enumerate(out, 1): x['row_id'] = 'PL-%03d' % i
    return _thin(out, n)


def tax_rows(n=None):
    out = []; ytd = {}
    for x in pnl_rows():
        M = to_date(x['month']); sa = R2(max(0.0, x['net_profit']) * TAX_SET_ASIDE_PCT); ytd[M.year] = R2(ytd.get(M.year, 0.0) + sa)
        out.append(dict(month=x['month'], profit=x['net_profit'], set_aside_pct=TAX_SET_ASIDE_PCT, set_aside=sa, ytd_set_aside=ytd[M.year]))
    for i, x in enumerate(out, 1): x['tax_id'] = 'TX-%03d' % i
    return _thin(out, n)


def _cash_world():
    W = _w(); pn = {to_date(x['month']): x for x in pnl_rows()}; po = _raw('po', _po_world)
    inflow = {}; payroll = {}; draw = {}; purch = {}; over = {}
    for p in W['payments']: inflow[_ms(p['date'])] = inflow.get(_ms(p['date']), 0.0) + p['amount']
    for x in pay_rows():
        M = to_date(x['month'])
        if x['role'] == 'Owner':
            if M <= TODAY: draw[M] = draw.get(M, 0.0) + x['total']
        else:
            half = x['total'] / 2.0
            if M + day(14) <= TODAY: payroll[M] = payroll.get(M, 0.0) + half
            if to_date(x['pay_date']) <= TODAY: payroll[M] = payroll.get(M, 0.0) + half
    for x in po:
        if x['paid_on'] != '': purch[_ms(x['paid_on'])] = purch.get(_ms(x['paid_on']), 0.0) + x['amount']
    for x in expense_rows(): over[to_date(x['month'])] = over.get(to_date(x['month']), 0.0) + x['amount']
    big = [x for x in po if x.get('_story')][0]
    target = float(round((CASH_FLOOR + big['amount'] * .45) / 100.0) * 100)
    RESM = [120000, 120000, 90000, 70000, 70000, 110000, 120000, 120000, 100000, 80000, 80000, 110000]
    mcur = month_start(0)
    net_cur = inflow.get(mcur, 0.0) - payroll.get(mcur, 0.0) - draw.get(mcur, 0.0) - sum(x['amount'] for x in po if x['paid_on'] != '' and _ms(x['paid_on']) == mcur) - over.get(mcur, 0.0)
    rows = []; tax_acc = 0.0; bal = 70000.0
    for mi in range(24):
        M = month_start(23 - mi)
        cin = inflow.get(M, 0.0); pay_ = payroll.get(M, 0.0); dr = draw.get(M, 0.0); pu = purch.get(M, 0.0); ov = over.get(M, 0.0)
        tax_paid = 0.0; bonus = 0.0
        if M.month in (1, 4, 7, 10) and mi > 0: tax_paid = R2(tax_acc); tax_acc = 0.0
        net = cin - pay_ - dr - pu - ov - tax_paid
        bal += net
        res = RESM[M.month - 1]
        if M == month_start(1): res = max(32000.0, target - net_cur)
        if M < mcur and bal > res: bonus = R2(bal - res); bal = res
        sa = max(0.0, pn[M]['net_profit']) * TAX_SET_ASIDE_PCT; tax_acc += sa
        rows.append(dict(month=M, cash_in=R2(cin), payroll=R2(pay_), owner_draw=R2(dr), purchases=R2(pu), overhead=R2(ov), tax_paid=tax_paid, owner_bonus=bonus, net=R2(net - bonus), closing_cash=R2(bal)))
    diff = rows[-1]['closing_cash'] - target
    if diff > 0:
        rows[-1]['owner_bonus'] = R2(rows[-1]['owner_bonus'] + diff); rows[-1]['net'] = R2(rows[-1]['net'] - diff); rows[-1]['closing_cash'] = target
    elif diff < 0:
        deficit = -diff
        for i in range(len(rows) - 2, -1, -1):
            if deficit <= 0: break
            take = min(rows[i]['owner_bonus'], deficit)
            if take <= 0: continue
            rows[i]['owner_bonus'] = R2(rows[i]['owner_bonus'] - take); rows[i]['net'] = R2(rows[i]['net'] + take); deficit -= take
            for x in rows[i:]: x['closing_cash'] = R2(x['closing_cash'] + take)
    return dict(rows=rows, cash_now=rows[-1]['closing_cash'], start=70000.0, po=big)


def cash_rows(n=None):
    cw = _raw('cash', _cash_world)
    out = [dict(month=iso(x['month']), cash_in=x['cash_in'], payroll=x['payroll'], owner_draw=x['owner_draw'], purchases=x['purchases'], overhead=x['overhead'], tax_paid=x['tax_paid'],
                owner_bonus=x['owner_bonus'], net=x['net'], closing_cash=x['closing_cash']) for x in cw['rows']]
    for i, x in enumerate(out, 1): x['cash_id'] = 'CA-%03d' % i
    return _thin(out, n)


def bill_rows(n=None):
    cw = _raw('cash', _cash_world); po = _raw('po', _po_world); out = []
    pr = pay_rows(); last3 = sorted({x['month'] for x in pr if to_date(x['month']) < month_start(0)})[-3:]
    pay_est = R2(sum(x['total'] for x in pr if x['month'] in last3 and x['role'] not in ('Owner',)) / max(1, len(last3)))
    runs = [x['amount'] for x in po if x['kind'] == 'Parts run'][-8:]; run_est = R2(sum(runs) / max(1, len(runs)))
    def add(d, payee, cat, amt, kind):
        if TODAY < d <= TODAY + day(91): out.append(dict(due_date=iso(d), payee=payee, category=cat, amount=R2(amt), kind=kind, status='Open'))
    for k in range(0, 5):
        M = add_months(month_start(0), k)
        add(M, 'Landlord', 'Rent and yard', 4800.0, 'Fixed'); add(M + day(4), 'Insurer', 'Insurance', 4100.0, 'Fixed'); add(M + day(6), 'Software provider', 'Software', 890.0, 'Fixed')
        add(M + day(13), 'Utility provider', 'Utilities', 540.0, 'Fixed'); add(M + day(14), 'Lease company', 'Vehicle lease', sum(v['lease_monthly'] for v in vans), 'Fixed')
        add(_last_weekday(M), 'Payroll run', 'Technician and office pay', pay_est, 'Payroll'); add(_last_weekday(M), 'Owner', 'Owner draw', OWNER_DRAW, 'Payroll')
        add(_last_weekday(M), 'Grace Lindqvist', 'Accounting', 650.0, 'Fixed')
        if M.month in (1, 4, 7, 10): add(M + day(14), 'Tax payment', 'Tax set-aside payment', R2(sum(max(0.0, x['net_profit']) for x in pnl_rows()[-3:]) * TAX_SET_ASIDE_PCT), 'Tax')
    d = TODAY + day(1)
    while d <= TODAY + day(91):
        if d.weekday() == 4: add(d, 'Your parts counter', 'Parts run', run_est, 'Supplier')
        d += day(1)
    for x in po:
        if x['status'] == 'Open' and x['due_date'] >= TODAY - day(2): out.append(dict(due_date=iso(x['due_date']), payee=x['supplier'], category=x['kind'], amount=x['amount'], kind='Supplier', status='Open'))
    out.sort(key=lambda x: x['due_date'])
    for i, x in enumerate(out, 1): x['bill_id'] = 'BL-%04d' % i
    return _thin(out, n)


def _open_invoices(): return [x for x in _w()['invoices'] if x['status'] in ('Unpaid', 'Part paid') and not x.get('_pending')]


def ageing_rows(n=None):
    acc = {}
    for x in _open_invoices():
        a = acc.setdefault(x['account'], dict(account=x['account'], site_type=x['site_type'], invoices=0, balance=0.0, b0=0.0, b31=0.0, b61=0.0, b90=0.0, oldest=0, promised=''))
        age = (TODAY - x['date']).days; a['invoices'] += 1; a['balance'] += x['balance']; a['oldest'] = max(a['oldest'], age)
        k = 'b0' if age <= 30 else 'b31' if age <= 60 else 'b61' if age <= 90 else 'b90'; a[k] += x['balance']
    out = []
    for i, a in enumerate(sorted(acc.values(), key=lambda a: -a['oldest']), 1):
        out.append(dict(ageing_id='AR-%03d' % i, as_of=iso(TODAY), account=a['account'], site_type=a['site_type'], open_invoices=a['invoices'], balance=R2(a['balance']), b0_30=R2(a['b0']), b31_60=R2(a['b31']),
                        b61_90=R2(a['b61']), b90_plus=R2(a['b90']), oldest_days=a['oldest']))
    return _thin(out, n)


def chase_rows(n=None):
    r = rng('chase'); out = []
    cands = [x for x in _w()['invoices'] if x['account'] != '' and x['site_type'] != 'Home' and not x.get('_pending')]
    for x in cands:
        late = (x['paid_on'] or TODAY) - x['due_date'] if x['status'] != 'Written off' else dt.timedelta(days=60)
        if late.days < 8: continue
        k = 1 + (late.days > 30) + (late.days > 55)
        for s in range(k):
            d = x['due_date'] + day(7 + 14 * s + r.randint(0, 3))
            if d > TODAY: break
            prom = d + day(r.randint(3, 12)); kept = (x['paid_on'] != '' and x['paid_on'] <= prom + day(2)) if x['paid_on'] != '' else False
            oc = 'Kept' if kept else ('Open' if prom > TODAY else 'Broken')
            out.append(dict(date=iso(d), invoice_id=x['invoice_id'], account=x['account'], method=r.choice(CHASE_METHODS), promised_on=iso(prom), promised_amount=x['balance'] if x['balance'] else x['amount'], outcome=oc))
    out.sort(key=lambda x: x['date'])
    for i, x in enumerate(out, 1): x['chase_id'] = 'CH-%04d' % i
    return _thin(out, n)


# ------------------------------------------------------------------ helpers and the story
def callback_rate(tech=None, months=12):
    lo = month_start(months) if months else HISTORY_START
    base = [j for j in _w()['jobs'] if j['status'] == 'Completed' and not j['is_callback'] and j['_v'] is None and j['kind'] in _KIND_CB and lo <= j['date'] <= TODAY and (tech is None or j['technician'] == tech)]
    cb = [j for j in _w()['jobs'] if j['status'] == 'Completed' and j['is_callback'] and lo <= j['date'] <= TODAY and (tech is None or j['_orig']['technician'] == tech)]
    return round(len(cb) / float(len(base)), 4) if base else 0.0


def job_margin(job_type, from_date, to_date_):
    a, b = to_date(from_date), to_date(to_date_)
    js = [j for j in _w()['jobs'] if j['status'] == 'Completed' and j['job_type'] == job_type and a <= j['date'] <= b and not j['is_callback']]
    pr = sum(j['price'] for j in js); co = sum(j['total_cost'] for j in js)
    return dict(jobs=len(js), price=R2(pr), cost=R2(co), margin_pct=round((pr - co) / pr, 4) if pr else 0.0)


def story():
    """ids of the story rows: margin_job_type (+ margin_pb_id, margin_part_ids, margin_recent, margin_before, margin_target, margin_rise_date); callback_tech (+ callback_tech_id, callback_rate,
    callback_shop_rate, callback_ratio); renewal_ids (+ renewal_count, renewal_value, visit_season, visit_done_share, visit_expected_share, visit_open); overdue_invoice (+ overdue_account,
    overdue_amount, overdue_days, overdue_days_past_due); short_van (+ short_parts, short_value); supplier_po (+ supplier_po_amount, supplier_po_due, cash_now, cash_after, cash_floor)"""
    out = {}; W = _w()
    rise = TODAY - day(118)
    rec = job_margin('Water heater replacement', rise + day(3), TODAY); bef = job_margin('Water heater replacement', month_start(12), rise - day(1))
    pb = [p for p in price_book if p['task'] == 'Water heater, 50 gal tank'][0]
    out.update(margin_job_type='Water heater replacement', margin_pb_id=pb['pb_id'], margin_part_ids=[PART[x]['part_id'] for x in ('Water heater, 40 gal tank', 'Water heater, 50 gal tank', 'Water heater, tankless')],
               margin_recent=rec['margin_pct'], margin_before=bef['margin_pct'], margin_target=JT_OF['Water heater replacement']['target_margin'], margin_rise_date=iso(rise))
    tk = 'Kofi Mensah'; tr = callback_rate(tk); sr = callback_rate(None)
    out.update(callback_tech=tk, callback_tech_id=TECH[tk]['tech_id'], callback_rate=tr, callback_shop_rate=sr, callback_ratio=round(tr / sr, 2) if sr else 0.0)
    rids = [m['agreement_id'] for m in W['members'] if m['status'] == 'Renewal due' and m['renewal_date'] != '' and month_start(0) <= m['renewal_date'] <= max(_eom(TODAY), TODAY + day(14))]
    rv = sum(PLAN[m['plan']]['price'] for m in W['members'] if m['agreement_id'] in rids)
    cur = [v for v in W['visits'] if v['window_start'] <= TODAY <= v['window_end']]
    if not cur:
        last = max(v['window_end'] for v in W['visits']); cur = [v for v in W['visits'] if v['window_end'] == last]
    done = sum(1 for v in cur if v['status'] == 'Done'); wlen = max(1, (cur[0]['window_end'] - cur[0]['window_start']).days); fr = min(1.0, (TODAY - cur[0]['window_start']).days / float(wlen))
    prev = [v for v in W['visits'] if v['season'] == cur[0]['season'] and v['window_start'].year == cur[0]['window_start'].year - 1]
    el = (TODAY - cur[0]['window_start']).days
    exp = round(sum(1 for v in prev if v['done_on'] != '' and (v['done_on'] - v['window_start']).days <= el) / float(len(prev)), 3) if prev else 0.0
    out.update(renewal_ids=rids, renewal_count=len(rids), renewal_value=R2(rv), visit_season=cur[0]['season'], visit_done_share=round(done / float(len(cur)), 3), visit_expected_share=exp,
               visit_open=sum(1 for v in cur if v['status'] in ('Due', 'Booked')))
    inv = [x for x in W['invoices'] if x.get('_story')][0]
    out.update(overdue_invoice=inv['invoice_id'], overdue_account=inv['account'], overdue_amount=inv['amount'], overdue_days=(TODAY - inv['date']).days, overdue_days_past_due=(TODAY - inv['due_date']).days)
    sc = [x for x in stock_count_rows() if x['van'] == 'Van 4' and x['date'] == max(y['date'] for y in stock_count_rows()) and x['variance'] < 0]
    out.update(short_van='Van 4', short_parts=[x['part_id'] for x in sc], short_value=R2(-sum(x['variance_value'] for x in sc)))
    cw = _raw('cash', _cash_world); po = cw['po']
    out.update(supplier_po=po['po_id'], supplier_po_amount=po['amount'], supplier_po_due=iso(po['due_date']), cash_now=cw['cash_now'], cash_after=R2(cw['cash_now'] - po['amount']), cash_floor=CASH_FLOOR)
    return out


_GENS = ['call_rows', 'job_rows', 'estimate_rows', 'invoice_rows', 'payment_rows', 'agreement_rows', 'renewal_rows', 'visit_rows', 'permit_rows', 'callback_rows', 'parts_used_rows',
         'timesheet_rows', 'pay_rows', 'van_stock_rows', 'stock_count_rows', 'restock_rows', 'purchase_rows', 'price_change_rows', 'marketing_rows', 'review_rows', 'expense_rows',
         'vehicle_cost_rows', 'tool_rows', 'licence_rows', 'pnl_rows', 'cash_rows', 'bill_rows', 'ageing_rows', 'chase_rows', 'tax_rows', 'job_type_month_rows', 'tech_month_rows',
         'site_rows', 'equipment_rows']


def _digest():
    h = hashlib.md5()
    for nm in _GENS: h.update(repr(globals()[nm]()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); S = story(); G = {nm: globals()[nm]() for nm in _GENS}
    print('team', len(team), 'techs', len(techs), 'vans', len(vans), 'job_types', len(job_types), 'sources', len(lead_sources), 'plans', len(plans), 'price_book', len(price_book), 'parts', len(parts))
    print(' '.join('%s %d' % (nm.replace('_rows', ''), len(v)) for nm, v in G.items()))
    ids = {'call_rows': 'call_id', 'job_rows': 'job_id', 'estimate_rows': 'estimate_id', 'invoice_rows': 'invoice_id', 'payment_rows': 'payment_id', 'agreement_rows': 'agreement_id', 'renewal_rows': 'renewal_id',
           'visit_rows': 'visit_id', 'permit_rows': 'permit_id', 'callback_rows': 'callback_id', 'parts_used_rows': 'use_id', 'timesheet_rows': 'ts_id', 'pay_rows': 'pay_id', 'van_stock_rows': 'stock_id',
           'stock_count_rows': 'count_id', 'restock_rows': 'restock_id', 'purchase_rows': 'po_id', 'price_change_rows': 'change_id', 'marketing_rows': 'row_id', 'review_rows': 'row_id', 'expense_rows': 'expense_id',
           'vehicle_cost_rows': 'vc_id', 'tool_rows': 'tool_id', 'licence_rows': 'licence_id', 'pnl_rows': 'row_id', 'cash_rows': 'cash_id', 'bill_rows': 'bill_id', 'ageing_rows': 'ageing_id', 'chase_rows': 'chase_id',
           'tax_rows': 'tax_id', 'job_type_month_rows': 'row_id', 'tech_month_rows': 'row_id', 'site_rows': 'site_id', 'equipment_rows': 'equipment_id'}
    for nm, k in ids.items(): assert len({x[k] for x in G[nm]}) == len(G[nm]), nm
    for lst, k in ((team, 'staff_id'), (parts, 'part_id'), (price_book, 'pb_id'), (vans, 'van_id')): assert len({x[k] for x in lst}) == len(lst), k
    chk = [('job_rows', 'job_type', JOB_TYPES), ('job_rows', 'technician', TECH_NAMES[:6]), ('job_rows', 'status', JOB_STATUS), ('job_rows', 'source', SOURCES), ('job_rows', 'van', VAN_NAMES), ('job_rows', 'site_type', SITE_TYPES),
           ('job_rows', 'area', AREAS), ('job_rows', 'kind', JOB_KINDS), ('call_rows', 'source', SOURCES), ('call_rows', 'call_type', CALL_TYPES), ('call_rows', 'outcome', CALL_OUTCOMES),
           ('call_rows', 'answered_by', ANSWERED_BY), ('estimate_rows', 'outcome', EST_OUTCOME), ('estimate_rows', 'option_chosen', OPTION_CHOSEN), ('estimate_rows', 'lost_reason', EST_LOST + ['']),
           ('invoice_rows', 'status', INVOICE_STATUS), ('invoice_rows', 'method', PAY_METHODS + ['']), ('payment_rows', 'kind', PAYMENT_KINDS), ('payment_rows', 'method', PAY_METHODS),
           ('agreement_rows', 'status', AGREEMENT_STATUS), ('agreement_rows', 'plan', PLAN_NAMES), ('visit_rows', 'status', VISIT_STATUS), ('visit_rows', 'season', VISIT_SEASONS), ('permit_rows', 'status', PERMIT_STATUS),
           ('callback_rows', 'reason', CALLBACK_REASONS), ('purchase_rows', 'kind', PURCHASE_KINDS), ('purchase_rows', 'status', PO_STATUS), ('expense_rows', 'category', EXPENSE_CATEGORIES),
           ('licence_rows', 'item', RENEWAL_KINDS), ('chase_rows', 'outcome', CHASE_OUTCOMES), ('chase_rows', 'method', CHASE_METHODS), ('marketing_rows', 'source', SOURCES), ('equipment_rows', 'type', EQUIP_TYPES),
           ('equipment_rows', 'fuel', FUELS), ('site_rows', 'area', AREAS), ('parts_used_rows', 'category', PART_CATEGORIES)]
    for nm, col, vals in chk:
        got = {x[col] for x in G[nm]}; miss = [v for v in vals if v not in got]
        if miss: print('UNUSED', nm, col, miss)
    for nm in ('call_rows', 'job_rows', 'invoice_rows', 'payment_rows', 'estimate_rows', 'expense_rows', 'purchase_rows', 'callback_rows', 'permit_rows'):
        rows = G[nm]; m0 = iso(month_start(0)); d30 = ago(30)
        key = 'date' if 'date' in rows[0] else 'applied_on'
        print(nm, 'this month', sum(1 for x in rows if x[key] >= m0 and x[key] <= iso(TODAY)), 'last 30 days', sum(1 for x in rows if d30 <= x[key] <= iso(TODAY)))
    print(S)
    print('seconds', round(time.time() - t0, 1), 'digest', _digest())
