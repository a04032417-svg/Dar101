"""Childcare center suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (one cached world is built on first use). The demo business is "Willow Lane Early Learning"
(fictional): a small licensed childcare center run by an owner-director (Marisol Vega, CC-01) with an assistant director who also does billing (Tobias Lindgren, CC-02), 4 lead
teachers (CC-03..CC-06, one per age room), 3 assistants (CC-07..CC-09), a cook (CC-10), 2 part-time floaters (CC-11, CC-12) and 4 outside contacts (accountant CC-13, food supplier
CC-14, cleaner CC-15, maintenance contact CC-16). Four age rooms (Infants, Toddlers, Twos, Preschool) plus a School-age group (before/after school and a summer camp, holiday camps):
about 52 children enrolled on full-time and part-time schedules (full or half days, 2/3/5 days a week), about 100 children over ~2 years, about 80 families. Tuition is billed weekly
(about a third of families, due Friday) or monthly (issued on the 1st, due 14 days later); sibling discount 10%, staff discount 25%, registration and supply fees, a deposit of one
week's tuition, late-pickup fees after closing time (17:30) beyond a grace, drop-in days at a surcharge; some families are paid partly by a government childcare payment (generic words);
meals are cooked on site (breakfast, lunch, afternoon snack) with a meal-program claim (generic words). A single home daycare provider can use most parts (one room, mixed ages,
a home-use share of the house is a Part 8 tool). One generic currency; every date is relative to the build day.

Money model: weekly rate by room and schedule (rate card, raised about 3% on 1 January of this year); invoice tuition = rate x weeks billed (a week or 52/12 of a week) for the
days enrolled in the period; discount = tuition x discount share; extras: registration (new children), supply fee (September), drop-in days (previous period), late-pickup fees (previous
period, a third waived), camp fees (school-age camp weeks replace the tuition of those weeks). amount = tuition - discount + extras; gov_expected = (tuition - discount) x the family's
government share; parent_due = amount - gov_expected. Staff pay per month: owner draw, assistant director salary, hourly staff = paid shift hours x rate x (1 + employer costs).
Staff-to-child ratio per room (children per staff, "check your local rules"): Infants 4, Toddlers 6, Twos 8, Preschool 10, School-age 12; the Infants room also keeps two staff while 3 or more
children are in. Shifts are built from the children present each hour so each room-hour is covered (a break cover shift at 12:00-14:00 gives every long shift a break slot),
except a few old room-hours and the story hour. Reporting month = month of the period for revenue, month of the payment for cash.

Story rows (ids from story(), never hard-coded): ratio_room/ratio_date/ratio_hour (a room one staff member short in one hour of one day last week), overdue_family
(three unpaid monthly invoices, the oldest 6+ weeks past due), gov_family (a government childcare payment short-paid last but one month), renewal_holder (a background check ends
in 12 days and is not renewed), losing_room (Infants room loses money over the last 12 months), health_child (an immunisation record past its due date, status only).

Exports
  constants: COMPANY SUITE OWNER ASSISTANT_DIRECTOR HISTORY_START CLOSING_TIME LATE_GRACE_MIN LATE_FEE_PER_MIN REG_FEE SUPPLY_FEE DROP_IN_SURCHARGE SIBLING_PCT STAFF_PCT NOTICE_DAYS
             INVOICE_DAYS WEEKLY_DUE_DAYS EMPLOYER_COST_PCT OWNER_DRAW TAX_SET_ASIDE_PCT CARD_FEE_PCT CPD_TARGET_HOURS CASH_FLOOR OCC_TARGET STAFF_SHARE_TARGET HOURS (7..17)
  dates: TODAY iso ago ahead to_date month_start add_months months14() week_start; helpers pairs first_name fake_phone fake_email rng
  lists: ROLES TEAMS PAY_TYPES ROOMS SCHEDULES CHILD_STATUS ATT_STATUS BILL_CYCLES PAY_METHODS DISCOUNTS INVOICE_STATUS PAYMENT_KINDS DEPOSIT_STATUS GOV_STATUS SOURCES ENQUIRY_STATUS
         LOST_REASONS TOUR_STATUS WAIT_STATUS PRIORITIES MEALS HEALTH_RECORDS HEALTH_STATUS INCIDENT_TYPES DRILL_KINDS CHECK_KINDS CHECK_STATUS RENEWAL_KINDS CPD_KINDS PAY_STATUS
         OBS_KINDS CONF_STATUS EVENT_KINDS MSG_TOPICS MSG_STATUS PROGRAMS MARKETING_KINDS EXPENSE_CATEGORIES SHIFT_KINDS WEEKDAYS AGE_BANDS PAY_ROLES
  people and reference: team (16), staff (12), contacts (4), rooms (5), rates (25), fees (5), programs (3), former_staff (6), closures
  generators (fresh lists of dicts, oldest first; n= thins a long list but keeps the most recent rows; optional dates are '' when blank):
    child_rows family_rows booking_rows attendance_rows late_fee_rows shift_rows ratio_hour_rows invoice_rows payment_rows gov_payment_rows deposit_rows statement_rows
    ageing_rows ageing_month_rows promise_rows plan_rows enquiry_rows tour_rows waitlist_rows marketing_rows meal_rows menu_rows health_rows incident_rows drill_rows check_rows
    renewal_rows training_rows exit_rows pay_rows observation_rows conference_rows report_rows parent_message_rows event_rows program_week_rows program_signup_rows
    room_month_rows pnl_rows expense_rows bill_rows cash_rows tax_rows closure_rows
  also: OWNER_EXTRA (quarterly extra owner draw, cash only) CLOSURES CAMP LAST_OPEN is_open staff_by_name RATE RM POOL PRG
  helpers: room_profit(room, months=12) ratio_short_hours(days=30) story()
Lesson: money cells are plain amounts; optional dates (paid_on, left_on, renewed_on, settled_on) are '' when blank: wrap lookups with IF(x=0,"",x). Links hold NAMES (child, family, room,
staff) or ids (child CH-001, family FM-001, invoice IV-00001). Words: no medical detail: health records are status and dates only; incidents are date, room, type and follow-up status.
"""
import datetime as dt
import calendar
import random
import hashlib
import math
import bisect

COMPANY = 'Willow Lane Early Learning'
SUITE = 'fx-20261115-childcare-center'
OWNER = 'Marisol Vega'
ASSISTANT_DIRECTOR = 'Tobias Lindgren'
TODAY = dt.date.today()
D = dt.date

CLOSING_TIME = '17:30'
LATE_GRACE_MIN = 5
LATE_FEE_PER_MIN = 2.0
REG_FEE = 150.0
SUPPLY_FEE = 90.0
DROP_IN_SURCHARGE = 0.15
SIBLING_PCT = 0.10
STAFF_PCT = 0.25
NOTICE_DAYS = 30
INVOICE_DAYS = 14
WEEKLY_DUE_DAYS = 4
EMPLOYER_COST_PCT = 0.10
OWNER_DRAW = 5500.0
OWNER_EXTRA = 15000.0          # a quarterly extra draw taken from cash (not a cost in the profit and loss)
TAX_SET_ASIDE_PCT = 0.25
CARD_FEE_PCT = 0.018
CPD_TARGET_HOURS = 15
CASH_FLOOR = 12000.0
OCC_TARGET = 0.90
STAFF_SHARE_TARGET = 0.70
HOURS = list(range(7, 18))


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
def rng(tag=''): return random.Random('cc-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
def _hm(mins): return '%02d:%02d' % (mins // 60, mins % 60)


HISTORY_START = month_start(23)

# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Owner-director', 'Assistant director', 'Lead teacher', 'Assistant', 'Cook', 'Floater', 'Accountant', 'Food supplier', 'Cleaner', 'Maintenance']
TEAMS = ['Management', 'Classroom', 'Kitchen', 'Outside']
PAY_TYPES = ['Owner draw', 'Salary', 'Hourly', 'Invoice']
PAY_ROLES = ['Owner-director', 'Assistant director', 'Lead teacher', 'Assistant', 'Cook', 'Floater']
ROOMS = ['Infants', 'Toddlers', 'Twos', 'Preschool', 'School-age']
SCHEDULES = ['5 full days', '3 full days', '2 full days', '5 half days', '3 half days']
CHILD_STATUS = ['Enrolled', 'Starting soon', 'Left']
ATT_STATUS = ['Present', 'Sick absence', 'Family holiday']
BILL_CYCLES = ['Weekly', 'Monthly']
PAY_METHODS = ['Autopay card', 'Autopay bank', 'Bank transfer', 'Cash']
DISCOUNTS = ['None', 'Sibling', 'Staff']
INVOICE_STATUS = ['Paid', 'Part paid', 'Unpaid', 'Written off']
PAYMENT_KINDS = ['Invoice', 'Deposit', 'Plan instalment']
DEPOSIT_STATUS = ['Held', 'Applied', 'Refunded', 'Kept']
GOV_STATUS = ['Paid', 'Short-paid', 'Expected']
SOURCES = ['Word of mouth', 'Online directory', 'Website', 'Roadside sign', 'Current family', 'Other settings', 'Local event']
ENQUIRY_STATUS = ['New', 'Tour booked', 'Tour held', 'Applied', 'Enrolled', 'Waitlist', 'Lost']
LOST_REASONS = ['No place', 'Price', 'Hours', 'Distance', 'Slow reply']
TOUR_STATUS = ['Held', 'No-show', 'Cancelled', 'Booked']
WAIT_STATUS = ['Waiting', 'Offered', 'Started', 'Withdrawn']
PRIORITIES = ['High', 'Normal', 'Low']
MEALS = ['Breakfast', 'Lunch', 'Afternoon snack']
HEALTH_RECORDS = ['Immunisation record', 'Medical permission', 'Allergy status', 'Emergency contacts']
HEALTH_STATUS = ['On file', 'Due', 'Missing']
INCIDENT_TYPES = ['Fall', 'Bite', 'Collision', 'Other']
DRILL_KINDS = ['Fire drill', 'Evacuation drill', 'Lockdown drill', 'Shelter drill']
CHECK_KINDS = ['Deep clean', 'Safety check', 'Equipment check']
CHECK_STATUS = ['Done', 'Missed']
RENEWAL_KINDS = ['Background check', 'First aid course', 'Safeguarding course', 'Food hygiene course', 'Liability insurance', 'Building inspection', 'Licence renewal',
                 'Fire safety service']
CPD_KINDS = ['Workshop', 'Online course', 'Training day', 'Peer learning', 'First aid course']
PAY_STATUS = ['Paid', 'Accruing']
OBS_KINDS = ['Observation', 'Portfolio entry']
CONF_STATUS = ['Held', 'Booked', 'No-show']
EVENT_KINDS = ['Newsletter', 'Family meeting week', 'Open day', 'Family event']
MSG_TOPICS = ['Billing', 'Schedule', 'Pickup', 'Health status', 'General']
MSG_STATUS = ['Replied', 'Awaiting reply']
PROGRAMS = ['Before-after school', 'Summer camp', 'Holiday camp']
MARKETING_KINDS = ['Online directory', 'Website upkeep', 'Roadside sign', 'Local flyers', 'Open day', 'Referral reward']
EXPENSE_CATEGORIES = ['Rent', 'Utilities', 'Food and groceries', 'Cleaning', 'Insurance', 'Supplies and toys', 'Training', 'Marketing', 'Management software', 'Maintenance',
                      'Accounting', 'Bank and card fees']
SHIFT_KINDS = ['Regular', 'Break cover', 'Relief']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
AGE_BANDS = ['0-30', '31-60', '61-90', '90+']

# ------------------------------------------------------------------ people
# id, name, country, role, team, pay type, hours a week, monthly salary, hourly rate, room, start days ago
_staff = [('CC-01', 'Marisol Vega', 'Spain', 'Owner-director', 'Management', 'Owner draw', 45, 0, 0, 'All rooms', 2900),
          ('CC-02', 'Tobias Lindgren', 'Sweden', 'Assistant director', 'Management', 'Salary', 40, 3600, 0, 'Office and billing', 1900),
          ('CC-03', 'Aaliyah Rahman', 'Bangladesh', 'Lead teacher', 'Classroom', 'Hourly', 40, 0, 20.5, 'Infants', 1500),
          ('CC-04', 'Mateusz Kowalczyk', 'Poland', 'Lead teacher', 'Classroom', 'Hourly', 40, 0, 20.5, 'Toddlers', 1250),
          ('CC-05', 'Ngozi Eze', 'Nigeria', 'Lead teacher', 'Classroom', 'Hourly', 40, 0, 20.5, 'Twos', 300),
          ('CC-06', 'Camille Fontaine', 'France', 'Lead teacher', 'Classroom', 'Hourly', 40, 0, 21.5, 'Preschool', 1100),
          ('CC-07', 'Luis Fernandez', 'Mexico', 'Assistant', 'Classroom', 'Hourly', 38, 0, 16.0, 'Infants', 800),
          ('CC-08', 'Hana Sato', 'Japan', 'Assistant', 'Classroom', 'Hourly', 38, 0, 16.0, 'Toddlers', 640),
          ('CC-09', 'Zainab Khalid', 'Pakistan', 'Assistant', 'Classroom', 'Hourly', 38, 0, 15.5, 'Twos and Preschool', 140),
          ('CC-10', 'Ibrahim Diallo', 'Senegal', 'Cook', 'Kitchen', 'Hourly', 30, 0, 17.5, 'Kitchen', 460),
          ('CC-11', 'Sofia Petrova', 'Bulgaria', 'Floater', 'Classroom', 'Hourly', 25, 0, 15.5, 'Relief and school-age', 700),
          ('CC-12', 'Joao Barbosa', 'Brazil', 'Floater', 'Classroom', 'Hourly', 25, 0, 15.5, 'Relief and school-age', 230)]
staff = []
for i, (a, b, c, ro, te, pt, hw, sal, hr, rm, st) in enumerate(_staff):
    staff.append(dict(staff_id=a, name=b, role=ro, team=te, pay_type=pt, phone=fake_phone(101 + i), email=fake_email(b), hours_week=hw, monthly_salary=float(sal),
                      hourly_rate=float(hr), room=rm, country=c, start=ago(st)))
_ctc = [('CC-13', 'Eleni Papadakis', 'Greece', 'Accountant', 'Bookkeeping, payroll and yearly accounts'),
        ('CC-14', 'Rajesh Menon', 'India', 'Food supplier', 'Weekly groceries and dairy delivery'),
        ('CC-15', 'Thandiwe Nkosi', 'South Africa', 'Cleaner', 'Evening cleaning of rooms and the kitchen'),
        ('CC-16', 'Dae-ho Park', 'South Korea', 'Maintenance', 'Repairs, playground and building checks')]
contacts = [dict(staff_id=a, name=b, role=ro, team='Outside', pay_type='Invoice', phone=fake_phone(113 + i), email=fake_email(b), hours_week=0, monthly_salary=0.0, hourly_rate=0.0,
                 room=sp, country=c, start=ago(2000 - 250 * i)) for i, (a, b, c, ro, sp) in enumerate(_ctc)]
team = staff + contacts
staff_by_name = {s['name']: s for s in team}
STAFF_NAMES = [s['name'] for s in staff]
CLASS_STAFF = [s['name'] for s in staff if s['team'] == 'Classroom']

# former staff (left during the history): name, role, hourly rate, room, start days ago, left days ago, days the place stayed empty, hiring and training cost
former_staff = [dict(name='Dmitri Volkov', role='Lead teacher', rate=20.5, room='Twos', start=ago(1800), left=ago(335), vacancy_days=34, replace_cost=1450.0),
                dict(name='Chiara Neri', role='Assistant', rate=16.0, room='Twos and Preschool', start=ago(900), left=ago(165), vacancy_days=26, replace_cost=820.0),
                dict(name='Tariq Anwar', role='Floater', rate=15.5, room='Relief and school-age', start=ago(1000), left=ago(260), vacancy_days=18, replace_cost=640.0),
                dict(name='Pablo Reyes', role='Cook', rate=17.5, room='Kitchen', start=ago(700), left=ago(470), vacancy_days=21, replace_cost=720.0),
                dict(name='Beatriz Lemos', role='Assistant', rate=15.5, room='Infants', start=ago(600), left=ago(520), vacancy_days=40, replace_cost=980.0),
                dict(name='Aisha Bello', role='Floater', rate=15.0, room='Relief and school-age', start=ago(500), left=ago(610), vacancy_days=15, replace_cost=520.0)]
# Aisha Bello left long ago; she is kept so the exit list has 6 rows over about 20 months

# rooms: id, name, age from, age to (months, to is exclusive), capacity, children per staff, minimum staff when 3+ children
_RM = [('RM-01', 'Infants', 3, 15, 8, 4, 2), ('RM-02', 'Toddlers', 15, 27, 12, 6, 1), ('RM-03', 'Twos', 27, 39, 14, 8, 1), ('RM-04', 'Preschool', 39, 60, 20, 10, 1),
       ('RM-05', 'School-age', 60, 132, 16, 12, 1)]
rooms = [dict(room_id=a, room=b, age_from=lo, age_to=hi, age_band='%d-%d months' % (lo, hi - 1) if b != 'School-age' else '5 years and over', capacity=cap, ratio=rt, min_staff=ms)
         for a, b, lo, hi, cap, rt, ms in _RM]
RM = {r['room']: r for r in rooms}

# weekly rate by room for 5 full days (this year) and the factor of each schedule; School-age has its own card
_FULL = {'Infants': 410.0, 'Toddlers': 366.0, 'Twos': 335.0, 'Preschool': 305.0}
_FACT = {'5 full days': 1.0, '3 full days': 0.68, '2 full days': 0.46, '5 half days': 0.62, '3 half days': 0.40}
_SCH_RATE = {'5 full days': 260.0, '3 full days': 177.0, '2 full days': 124.0, '5 half days': 133.0, '3 half days': 86.0}
_SCH_DAYS = {'5 full days': 5, '3 full days': 3, '2 full days': 2, '5 half days': 5, '3 half days': 3}
_SCH_HRS = {'5 full days': 9.0, '3 full days': 9.0, '2 full days': 9.0, '5 half days': 5.0, '3 half days': 5.0}
rates = []
for _i, _r in enumerate(ROOMS):
    for _s in SCHEDULES:
        w = _SCH_RATE[_s] if _r == 'School-age' else round(_FULL[_r] * _FACT[_s] / 1.0)
        ly = round(w / 1.03)
        rates.append(dict(rate_id='RT-%02d' % (len(rates) + 1), room=_r, schedule=_s, weekly_rate=float(w), last_year_rate=float(ly), days=_SCH_DAYS[_s], hours_day=_SCH_HRS[_s],
                          day_rate=R2(w / _SCH_DAYS[_s])))
RATE = {(x['room'], x['schedule']): x for x in rates}
fees = [dict(fee='Registration fee', amount=REG_FEE, rule='Once at enrolment; last year 130'),
        dict(fee='Supply fee', amount=SUPPLY_FEE, rule='Each September per child; last year 80'),
        dict(fee='Late pickup fee', amount=LATE_FEE_PER_MIN, rule='Per minute after closing time plus the grace'),
        dict(fee='Drop-in surcharge', amount=DROP_IN_SURCHARGE, rule='Share added to the day rate of an extra day'),
        dict(fee='Deposit', amount=1.0, rule='One week of tuition, applied to the last month')]
programs = [dict(program='Before-after school', places=16, price_day=22.0), dict(program='Summer camp', places=18, price_day=46.0), dict(program='Holiday camp', places=16, price_day=42.0)]
PRG = {p['program']: p for p in programs}


def _rate(room, sched, d):
    x = RATE[(room, sched)]
    return x['weekly_rate'] if to_date(d) >= D(TODAY.year, 1, 1) else x['last_year_rate']


def _wage(name, rate, d):
    return R2(rate * (1.03 if to_date(d) >= D(TODAY.year, 1, 1) else 1.0))


_G = [(['Ana', 'Rui', 'Marta', 'Tiago', 'Ines', 'Diogo', 'Sara', 'Nuno', 'Joana', 'Pedro'], ['Silva', 'Pereira', 'Costa', 'Ribeiro', 'Almeida', 'Moreira', 'Gomes', 'Lopes', 'Martins', 'Fonseca']),
      (['Jonas', 'Lena', 'Felix', 'Mira', 'Leon', 'Hanna', 'Emil', 'Nele', 'Paul', 'Greta'], ['Hoffmann', 'Schulz', 'Keller', 'Vogel', 'Brandt', 'Lorenz', 'Fuchs', 'Krause', 'Richter', 'Wolf']),
      (['Oliver', 'Ella', 'Harvey', 'Isla', 'Noah', 'Freya', 'Alfie', 'Poppy', 'George', 'Amelia'], ['Turner', 'Hughes', 'Walsh', 'Barker', 'Ellis', 'Pearce', 'Dawson', 'Fisher', 'Hale', 'Marsh']),
      (['Camille', 'Louis', 'Chloe', 'Hugo', 'Manon', 'Theo', 'Lea', 'Jules', 'Elise', 'Arthur'], ['Laurent', 'Girard', 'Roux', 'Fournier', 'Mercier', 'Blanc', 'Dupont', 'Chevalier', 'Faure', 'Perrin']),
      (['Lucia', 'Pablo', 'Carmen', 'Hector', 'Elena', 'Alvaro', 'Noa', 'Iker', 'Irene', 'Sergio'], ['Ortega', 'Molina', 'Castro', 'Herrera', 'Vidal', 'Prieto', 'Cano', 'Romero', 'Delgado', 'Pascual']),
      (['Daan', 'Sanne', 'Bram', 'Fenna', 'Lars', 'Anouk', 'Joris', 'Femke', 'Ruben', 'Lotte'], ['de Vries', 'Smit', 'Bos', 'Mulder', 'Dekker', 'Peters', 'Hendriks', 'Jansen', 'Vos', 'Bakker']),
      (['Gabriel', 'Beatriz', 'Caio', 'Larissa', 'Thiago', 'Julia', 'Enzo', 'Livia', 'Rafael', 'Bianca'], ['Souza', 'Lima', 'Araujo', 'Barbosa', 'Cardoso', 'Nunes', 'Freitas', 'Campos', 'Monteiro', 'Pinto']),
      (['Kasia', 'Piotr', 'Zofia', 'Jakub', 'Ola', 'Antoni', 'Wiktoria', 'Michal', 'Hania', 'Tomek'], ['Zielinski', 'Lewandowski', 'Mazur', 'Kaczmarek', 'Pawlak', 'Wrona', 'Sikora', 'Baran', 'Dudek', 'Jaworski']),
      (['Aarav', 'Diya', 'Kabir', 'Tara', 'Rohan', 'Isha', 'Vihaan', 'Neha', 'Ishaan', 'Kavya'], ['Sharma', 'Nair', 'Kapoor', 'Mehta', 'Joshi', 'Bose', 'Pillai', 'Gupta', 'Desai', 'Reddy']),
      (['Chidi', 'Ngozi', 'Tunde', 'Ada', 'Emeka', 'Yetunde', 'Kelechi', 'Bisi', 'Obinna', 'Ife'], ['Adebayo', 'Okafor', 'Balogun', 'Nwosu', 'Ogunleye', 'Afolabi', 'Chukwu', 'Onyeka', 'Ibe', 'Okoro']),
      (['Diego', 'Valeria', 'Mateo', 'Ximena', 'Santiago', 'Regina', 'Emilio', 'Renata', 'Luis', 'Camila'], ['Hernandez', 'Garcia', 'Ramirez', 'Torres', 'Flores', 'Vargas', 'Mendoza', 'Cruz', 'Ortiz', 'Aguilar']),
      (['Emre', 'Elif', 'Can', 'Defne', 'Mert', 'Ece', 'Baris', 'Selin', 'Deniz', 'Ayla'], ['Yilmaz', 'Sahin', 'Celik', 'Aydin', 'Ozturk', 'Arslan', 'Dogan', 'Kilic', 'Polat', 'Aksoy']),
      (['Hao', 'Mei', 'Jian', 'Xin', 'Yu', 'Lan', 'Tao', 'Ying', 'Bo', 'Rui'], ['Wang', 'Li', 'Liu', 'Yang', 'Huang', 'Zhou', 'Wu', 'Xu', 'Sun', 'Ma']),
      (['Minjun', 'Seoyeon', 'Jiho', 'Hayun', 'Doyun', 'Jiwoo', 'Siwoo', 'Yuna', 'Hyunwoo', 'Sora'], ['Kim', 'Lee', 'Choi', 'Jung', 'Kang', 'Cho', 'Yoon', 'Jang', 'Lim', 'Han']),
      (['Mia', 'Lachlan', 'Zara', 'Hamish', 'Sienna', 'Declan', 'Matilda', 'Archer', 'Ivy', 'Cooper'], ['Murray', 'Fraser', 'Hart', 'Doyle', 'Sutton', 'Blake', 'Lowe', 'Pratt', 'Burke', 'Quinlan']),
      (['Youssef', 'Salma', 'Omar', 'Nour', 'Karim', 'Lina', 'Adam', 'Yasmin', 'Rami', 'Hana'], ['Mansour', 'Nasser', 'Farah', 'Saleh', 'Aziz', 'Karam', 'Rahman', 'Habib', 'Sabbagh', 'Toumi'])]
_PARENT_FIRST = ['Elena', 'Marcus', 'Priya', 'Tomas', 'Amara', 'Nikolai', 'Sakura', 'Rafael', 'Leila', 'Declan', 'Fatima', 'Oskar', 'Ingrid', 'Kwame', 'Mei', 'Andre', 'Yara', 'Pavel',
                 'Noor', 'Callum', 'Ayesha', 'Jorge', 'Hilda', 'Ravi', 'Dalia', 'Stefan', 'Chiamaka', 'Lucas', 'Sofia', 'Idris']

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


# ------------------------------------------------------------------ calendar: closures and camp weeks
def _nth_weekday(y, m, wd, n):
    d = D(y, m, 1)
    while d.weekday() != wd: d += day(1)
    return d + day(7 * (n - 1))


def _last_weekday_of(y, m, wd):
    d = _eom(D(y, m, 1))
    while d.weekday() != wd: d -= day(1)
    return d


def _closure_map():
    out = {}
    for y in range(TODAY.year - 3, TODAY.year + 2):
        out[D(y, 1, 1)] = 'Public holiday'
        out[_nth_weekday(y, 5, 0, 1)] = 'Public holiday'
        out[_last_weekday_of(y, 8, 0)] = 'Public holiday'
        out[_nth_weekday(y, 9, 4, 1)] = 'Staff training day'
        d = D(y, 1, 2)
        while d.weekday() >= 5: d += day(1)
        out[d] = 'Staff training day'
        for k in range(24, 32):
            out[D(y, 12, k)] = 'Winter break'
    return {d: v for d, v in out.items() if d.weekday() < 5}


CLOSURES = _closure_map()


def is_open(d): return d.weekday() < 5 and d not in CLOSURES


def closure_rows(n=None):
    return _thin([dict(closure_id='CL-%02d' % (i + 1), date=iso(d), weekday=WEEKDAYS[d.weekday()], reason=v) for i, (d, v) in enumerate(sorted(CLOSURES.items()))
                  if HISTORY_START <= d <= TODAY + day(120)], n)


def _camp_weeks():
    out = {}
    for y in range(TODAY.year - 2, TODAY.year + 1):
        d = _nth_weekday(y, 7, 0, 1) + day(7)
        for k in range(8): out[d + day(7 * k)] = 'Summer camp'
        for m, dd in ((4, 6), (10, 26), (2, 16)):
            w = _nth_weekday(y, m, 0, 1)
            while w.day < dd - 6: w += day(7)
            out[w] = 'Holiday camp'
            if m == 4: out[w + day(7)] = 'Holiday camp'
    return out


CAMP = _camp_weeks()


def _camp_week(d): return CAMP.get(week_start(d))


def _last_open(d):
    while not is_open(d): d -= day(1)
    return d


LAST_OPEN = _last_open(TODAY)


# ------------------------------------------------------------------ world 1: children and families (monthly enrolment simulation)
_TARGET_NOW = {'Infants': 5, 'Toddlers': 11, 'Twos': 13, 'Preschool': 17, 'School-age': 6}
_SCH_W = {'Infants': [.55, .30, .15, 0, 0], 'Toddlers': [.50, .30, .12, .08, 0], 'Twos': [.42, .28, .10, .12, .08], 'Preschool': [.35, .22, .08, .22, .13],
          'School-age': [0, 0, 0, .6, .4]}
_DAYSETS = {5: [(0, 1, 2, 3, 4)], 3: [(0, 2, 4), (1, 3, 4), (0, 1, 3), (1, 2, 3), (0, 2, 3)], 2: [(0, 1), (2, 3), (3, 4), (0, 4), (1, 2)]}


def _age(dob, d): return (d.year - dob.year) * 12 + d.month - dob.month - (1 if d.day < dob.day else 0)


def _first_open(d):
    while not is_open(d): d += day(1)
    return d


def _room_at(c, d):
    i = bisect.bisect_right([m[0] for m in c['moves']], d) - 1
    return c['moves'][max(i, 0)][1]


def _sched_at(c, d):
    if c.get('sw') and d >= c['sw']: return c['sched2'], c['days2']
    return c['sched'], c['days']


_SIM_TAG = '8'


def _sim():
    r = rng('sim' + _SIM_TAG); rn = rng('names')
    HS = HISTORY_START
    months = [month_start(k) for k in range(23, -1, -1)]
    kids = []; used = set(); fam_of = {}
    famcount = {}

    def new_family():
        for _ in range(80):
            g = _G[rn.randrange(len(_G))]
            last = rn.choice(g[1])
            if last not in used: used.add(last); return last
        raise RuntimeError('names')

    def active(M1, nxt):
        return [c for c in kids if c['start'] < nxt and (c['end'] is None or c['end'] >= M1)]

    def count(room, M1, nxt): return sum(1 for c in active(M1, nxt) if _room_at(c, nxt - day(1)) == room)

    def make(room, M1, nxt, start, age_lo, age_hi, pre=False):
        g = _G[rn.randrange(len(_G))]
        first = rn.choice(g[0])
        last = None; fam = None
        if not pre and rn.random() < .16:
            cands = [c for c in active(M1, nxt) if famcount.get(c['last'], 0) == 1 and _room_at(c, nxt - day(1)) != room and c['end'] is None]
            if cands: fam = rn.choice(cands); last = fam['last']
        if last is None: last = new_family()
        famcount[last] = famcount.get(last, 0) + 1
        age = r.randint(age_lo, age_hi)
        dob = start - day(int(age * 30.4) + r.randint(0, 27))
        sched = _wchoice(r, SCHEDULES, _SCH_W[room])
        nd = _SCH_DAYS[sched]
        c = dict(first=first, last=last, dob=dob, start=start, end=None, sched=sched, days=r.choice(_DAYSETS[nd]), moves=[(start, room)], sw=None, sched2=None, days2=None,
                 notice_on=None, pre=pre, sibling=bool(fam), disc='Sibling' if fam else 'None', reason='')
        kids.append(c)
        return c

    for mi, M1 in enumerate(months):
        nxt = add_months(M1, 1)
        # school transition in September: age 57+ months in Preschool
        if M1.month == 9:
            for c in active(M1, nxt):
                if c['end'] is None and _room_at(c, M1) == 'Preschool' and _age(c['dob'], M1) >= 57:
                    if r.random() < .22:
                        sw = _first_open(M1); c['moves'].append((sw, 'School-age')); c['sw'] = sw; c['sched2'] = r.choice(['5 half days', '5 half days', '3 half days'])
                        c['days2'] = r.choice(_DAYSETS[_SCH_DAYS[c['sched2']]])
                    else:
                        c['end'] = _last_open(M1 - day(1)); c['notice_on'] = c['end'] - day(r.randint(35, 70)); c['reason'] = 'School'
        # random leavers
        for c in active(M1, nxt):
            if c['end'] is None and c['start'] < M1 and mi > 0:
                p = .03 if _room_at(c, M1) == 'Infants' else (.035 if _room_at(c, M1) == 'School-age' else .02)
                if r.random() < p:
                    e = _first_open(M1 + day(r.randint(1, 26)))
                    if e < nxt:
                        c['end'] = e; short = r.random() < .15
                        c['notice_on'] = e - day(r.randint(5, 25) if short else r.randint(32, 60)); c['reason'] = 'Moved' if r.random() < .5 else 'Other setting'
        # aging up: oldest destination first
        for src, dst in (('Twos', 'Preschool'), ('Toddlers', 'Twos'), ('Infants', 'Toddlers')):
            for c in active(M1, nxt):
                if c['end'] is None and _room_at(c, M1) == src and _age(c['dob'], M1) >= RM[src]['age_to'] and count(dst, M1, nxt) < RM[dst]['capacity']:
                    c['moves'].append((_first_open(M1), dst))
        # admissions to fill each room towards its target
        growth = .86 + .14 * mi / 23.0
        for room in ROOMS:
            tgt = int(round(_TARGET_NOW[room] * growth + (.4 if room == 'Infants' and mi > 12 else 0)))
            have = count(room, M1, nxt)
            pr = .9 if M1.month == 9 else (.4 if M1.month in (7, 8) else .7)
            if room == 'Infants': pr = .85
            while have < tgt and r.random() < pr:
                lo, hi = RM[room]['age_from'], RM[room]['age_to'] - 1
                if room == 'School-age': lo, hi = 62, 100
                if room == 'Preschool': lo, hi = 40, 54
                stt = _first_open(M1 + day(r.randint(0, 24)))
                if mi == 23 and stt > TODAY + day(21): break
                make(room, M1, nxt, stt, lo, hi); have += 1
        if mi == 0:   # initial population: enrolled before the history window
            for room in ROOMS:
                tgt = int(round(_TARGET_NOW[room] * .86))
                have = count(room, M1, nxt)
                while have < tgt:
                    lo, hi = RM[room]['age_from'], RM[room]['age_to'] - 1
                    if room == 'School-age': lo, hi = 62, 100
                    age = r.randint(lo, hi); stt = M1 - day(r.randint(40, 600))
                    c = make(room, M1, nxt, stt, age, age, pre=True)
                    c['dob'] = M1 - day(int(age * 30.4) + r.randint(0, 27)); c['start'] = max(stt, c['dob'] + day(95))
                    c['moves'] = [(c['start'], room)]; have += 1
    kids.sort(key=lambda c: (c['start'], c['dob']))
    return kids


def _kids(): return _raw('kids', _sim)


def _families():
    def build():
        r = rng('fam'); kids = _kids(); fams = {}
        for c in kids:
            if c['last'] not in fams:
                fams[c['last']] = dict(last=c['last'], first_start=c['start'], kids=[], disc_done=False)
            fams[c['last']]['kids'].append(c)
        # sibling discount: only the younger sibling (later start) while two are enrolled; others pay in full
        for f in fams.values():
            f['kids'].sort(key=lambda c: c['start'])
            for i, c in enumerate(f['kids']): c['disc'] = 'Sibling' if i > 0 else 'None'
        # staff children: two long-enrolled single-child families
        cand = [f for f in fams.values() if len(f['kids']) == 1 and f['kids'][0]['start'] < TODAY - day(400) and f['kids'][0]['end'] is None]
        for f, (last, guardian) in zip([cand[3], cand[8]], [('Diallo', 'Ibrahim Diallo'), ('Barbosa', 'Joao Barbosa')]):
            old = f['last']
            f['last'] = last; f['staff'] = guardian
            f['kids'][0]['last'] = last; f['kids'][0]['disc'] = 'Staff'
        out = []
        for f in sorted(fams.values(), key=lambda f: (f['first_start'], f['last'])):
            i = len(out) + 1
            guardian = f.get('staff') or '%s %s' % (r.choice(_PARENT_FIRST), f['last'])
            habit = _wchoice(r, ['Prompt', 'Normal', 'Slow', 'Very slow'], [60, 28, 9, 3])
            auto = habit == 'Prompt' and r.random() < .7
            method = (_wchoice(r, ['Autopay card', 'Autopay bank'], [.55, .45]) if auto else ('Cash' if r.random() < .05 else 'Bank transfer'))
            gov = r.choice([.25, .35, .5]) if r.random() < .30 else 0.0
            out.append(dict(family_id='FM-%03d' % i, family='%s family' % f['last'], guardian=guardian, phone=fake_phone(500 + i), email=fake_email(guardian, 0),
                            cycle='Weekly' if r.random() < .36 else 'Monthly', pay_method=method, autopay=auto, habit=habit, gov_share=gov, late_prone=False,
                            staff_family=bool(f.get('staff')), _last=f['last'], _kids=f['kids']))
        # a few families are often late at pickup
        for f in r.sample([x for x in out if x['_kids'][-1]['end'] is None], 6): f['late_prone'] = True
        # the story family: monthly billed, slow, no autopay, no government share, enrolled for a long time
        sc = [x for x in out if x['cycle'] == 'Monthly' and x['_kids'][-1]['end'] is None and x['_kids'][-1]['start'] < TODAY - day(250) and not x['gov_share'] and len(x['_kids']) == 1
              and x['_kids'][0]['sched'] == '5 full days' and not x['staff_family']]
        s = sc[2]; s['habit'] = 'Very slow'; s['autopay'] = False; s['pay_method'] = 'Bank transfer'; s['story'] = True
        for x in out:
            x.setdefault('story', False)
            for c in x['_kids']: c['family_id'] = x['family_id']; c['family'] = x['family']; c['guardian'] = x['guardian']
        # child ids by start
        for i, c in enumerate(kids, 1): c['child_id'] = 'CH-%03d' % i; c['child'] = '%s %s' % (c['first'], c['last'])
        return out
    return _raw('fams', build)


def _fam_map(): return _raw('fammap', lambda: {f['family_id']: f for f in _families()})


def _status(c):
    if c['start'] > TODAY: return 'Starting soon'
    if c['end'] is not None and c['end'] < TODAY: return 'Left'
    return 'Enrolled'


def child_rows(n=None):
    _families()
    out = []
    for c in _kids():
        d = TODAY if _status(c) != 'Left' else c['end']
        room = _room_at(c, max(c['start'], min(d, TODAY)))
        sc, dy = _sched_at(c, max(c['start'], min(d, TODAY)))
        out.append(dict(child_id=c['child_id'], child=c['child'], family=c['family'], family_id=c['family_id'], dob=iso(c['dob']), room=room, schedule=sc,
                        days=' '.join(WEEKDAYS[i][:3] for i in dy), start_date=iso(c['start']), end_date=iso(c['end']) if c['end'] else '', status=_status(c),
                        discount=c['disc'], discount_pct={'None': 0.0, 'Sibling': SIBLING_PCT, 'Staff': STAFF_PCT}[c['disc']], notice_on=iso(c['notice_on']) if c['notice_on'] else '',
                        leave_reason=c['reason'], guardian=c['guardian'], phone=_fam_map()[c['family_id']]['phone'], email=_fam_map()[c['family_id']]['email']))
    return _thin(out, n)


def family_rows(n=None):
    out = [{k: v for k, v in f.items() if not k.startswith('_') and k not in ('story',)} for f in _families()]
    for o, f in zip(out, _families()):
        o['children'] = sum(1 for c in f['_kids'] if _status(c) != 'Left'); o['first_start'] = iso(f['_kids'][0]['start'])
    return _thin(out, n)


def booking_rows(n=None):
    """the weekly booking pattern of every enrolled or starting-soon child: one row per child and weekday"""
    out = []
    for c in _kids():
        if _status(c) == 'Left': continue
        d = max(c['start'], TODAY); sc, dy = _sched_at(c, d); room = _room_at(c, d)
        for wd in dy:
            out.append(dict(booking_id='BK-%03d' % (len(out) + 1), child_id=c['child_id'], child=c['child'], room=room, weekday=WEEKDAYS[wd], schedule=sc,
                            day_type='Half day' if 'half' in sc else 'Full day', hours=_SCH_HRS[sc], from_date=iso(max(c['start'], HISTORY_START))))
    return _thin(out, n)


# ------------------------------------------------------------------ world 2: attendance (sign-in and sign-out)
_FAMLATE = {}
def _signed_up(c, week):
    return rng('camp-%s-%s' % (c['child_id'], week)).random() < (.82 if CAMP.get(week) == 'Summer camp' else .6)


def _attendance():
    r = rng('att'); fams = _fam_map(); kids = _kids(); out = []
    d0 = HISTORY_START
    days = []
    d = d0
    while d <= LAST_OPEN:
        if is_open(d): days.append(d)
        d += day(1)
    # holiday weeks per child (clusters) and sick spells
    for dd in days:
        wk = week_start(dd); camp = CAMP.get(wk)
        for c in kids:
            if c['start'] > dd or (c['end'] is not None and dd > c['end']): continue
            room = _room_at(c, dd); sched, dys = _sched_at(c, dd)
            if room == 'School-age' and camp:
                if not _signed_up(c, wk): continue
                full = True; booked = True; hrs = 9.0
            else:
                booked = dd.weekday() in dys; full = 'full' in sched; hrs = 2.5 if room == 'School-age' else _SCH_HRS[sched]
                if not booked:
                    if r.random() < .012 and room != 'School-age': booked = False
                    else: continue
            extra = not booked
            if extra:
                if r.random() > .5: continue
            rr = rng('a-%s-%s' % (c['child_id'], dd.toordinal()))
            hol = rng('h-%s-%s' % (c['child_id'], wk.toordinal())).random() < (.07 if dd.month in (7, 8, 12) else .035)
            if booked and hol: status = 'Family holiday'
            elif booked and rr.random() < .045 + (.02 if dd.month in (1, 2, 11) else 0): status = 'Sick absence'
            else: status = 'Present'
            row = dict(child_id=c['child_id'], child=c['child'], family_id=c['family_id'], room=room, date=dd, schedule=sched, booked=booked, booked_hours=hrs, status=status,
                       extra=extra, sign_in='', sign_out='', hours=0.0, late_minutes=0, _mi=0, _mo=0, camp=bool(room == 'School-age' and camp))
            if status == 'Present':
                late_p = .38 if fams[c['family_id']]['late_prone'] else .018
                if room == 'School-age' and not camp:
                    mi = rr.randint(15 * 60 + 10, 15 * 60 + 50); mo = rr.randint(16 * 60 + 40, 17 * 60 + 28)
                elif full:
                    mi = int(rr.triangular(7 * 60 + 25, 9 * 60 + 20, 8 * 60 + 5)); mo = rr.randint(15 * 60 + 40, 17 * 60 + 27)
                    if rr.random() < .55: mo = rr.randint(16 * 60 + 35, 17 * 60 + 27)
                elif rr.random() < .72:
                    mi = rr.randint(7 * 60 + 40, 9 * 60 + 10); mo = rr.randint(12 * 60, 13 * 60 + 15)
                else:
                    mi = rr.randint(12 * 60 + 40, 13 * 60 + 15); mo = rr.randint(16 * 60 + 30, 17 * 60 + 27)
                if (full or room == 'School-age' or mi > 12 * 60) and rr.random() < late_p: mo = rr.randint(17 * 60 + 31, 17 * 60 + 56)
                if extra: mi = rr.randint(8 * 60, 9 * 60); mo = rr.randint(15 * 60 + 30, 17 * 60)
                row['_mi'], row['_mo'] = mi, mo; row['sign_in'], row['sign_out'] = _hm(mi), _hm(mo)
                row['hours'] = R2((mo - mi) / 60.0); row['late_minutes'] = max(0, mo - (17 * 60 + 30))
            out.append(row)
    return out


def _att(): return _raw('att', _attendance)


def attendance_rows(n=None):
    out = []
    for i, x in enumerate(_att(), 1):
        out.append(dict(attendance_id='AT-%05d' % i, date=iso(x['date']), week=iso(week_start(x['date'])), month=iso(_ms(x['date'])), weekday=WEEKDAYS[x['date'].weekday()],
                        child_id=x['child_id'], child=x['child'], family_id=x['family_id'], room=x['room'], schedule=x['schedule'], booked=x['booked'], booked_hours=x['booked_hours'],
                        status=x['status'], sign_in=x['sign_in'], sign_out=x['sign_out'], hours=x['hours'], late_minutes=x['late_minutes'], extra_day=x['extra']))
    return _thin(out, n)


# ------------------------------------------------------------------ world 3: staff shifts built from the children present each hour, and the ratio check
def _pool():
    p = {}
    for s in staff:
        p[s['name']] = dict(name=s['name'], role=s['role'], rate=s['hourly_rate'], start=to_date(s['start']), end=None, pay_type=s['pay_type'])
    for f in former_staff:
        p[f['name']] = dict(name=f['name'], role=f['role'], rate=f['rate'], start=to_date(f['start']), end=to_date(f['left']), pay_type='Hourly')
    return p


POOL = _pool()
_PREF = {'Infants': ['Aaliyah Rahman', 'Luis Fernandez', 'Beatriz Lemos'], 'Toddlers': ['Mateusz Kowalczyk', 'Hana Sato'],
         'Twos': ['Dmitri Volkov', 'Ngozi Eze', 'Chiara Neri', 'Zainab Khalid'], 'Preschool': ['Camille Fontaine', 'Chiara Neri', 'Zainab Khalid', 'Dmitri Volkov'],
         'School-age': ['Sofia Petrova', 'Joao Barbosa', 'Tariq Anwar', 'Aisha Bello']}
_FLOAT = ['Sofia Petrova', 'Joao Barbosa', 'Tariq Anwar', 'Aisha Bello']
_ASSIST = ['Zainab Khalid', 'Luis Fernandez', 'Hana Sato', 'Chiara Neri', 'Beatriz Lemos']
_MGMT = ['Tobias Lindgren', 'Marisol Vega']
_BREAK_HOUR = {'Infants': 12, 'Toddlers': 13, 'Twos': 12, 'Preschool': 13}
_HOLW = {}


def _away(name, d):
    if name in ('Tobias Lindgren', 'Marisol Vega'): return False
    wk = week_start(d)
    if rng('hol-%s-%s' % (name, wk.toordinal())).random() < .05: return True
    return rng('sick-%s-%s' % (name, d.toordinal())).random() < .015


def _hourly_counts():
    cnt = {}
    for x in _att():
        if x['status'] != 'Present': continue
        a = cnt.setdefault((x['date'], x['room']), [0] * len(HOURS))
        for i, h in enumerate(HOURS):
            if x['_mi'] <= h * 60 + 30 < x['_mo']: a[i] += 1
    return cnt


def _need(room, n):
    if n <= 0: return 0
    k = int(math.ceil(n / float(RM[room]['ratio'])))
    if RM[room]['min_staff'] > 1 and n >= 3: k = max(k, RM[room]['min_staff'])
    return k


def _shifts():
    cnt = _hourly_counts(); out = []; ratio = []
    days = sorted({d for d, _ in cnt})
    story_day = None
    opens = [d for d in days]
    sd_pick = opens[-3]            # a day last week: the story hour is built here
    old_shorts = set()
    r0 = rng('shortdays')
    for d in opens[:-60]:
        if r0.random() < .02: old_shorts.add(d)
    for d in opens:
        busy = {}                                    # name -> list of (start, end)
        hrs_day = {}
        def can(nm, a, b):
            p = POOL.get(nm)
            if not p or d < p['start'] or (p['end'] and d > p['end']) or _away(nm, d): return False
            if any(not (b <= x or a >= y) for x, y in busy.get(nm, [])): return False
            return hrs_day.get(nm, 0) + (b - a) <= 9.5
        def take(nm, a, b): busy.setdefault(nm, []).append((a, b)); hrs_day[nm] = hrs_day.get(nm, 0) + (b - a)
        day_rows = []
        # kitchen
        for nm in ('Ibrahim Diallo', 'Pablo Reyes'):
            if can(nm, 7, 13): take(nm, 7, 13); day_rows.append(dict(staff=nm, room='Kitchen', start=7, end=13, kind='Regular', break_start='')); break
        plan = {}
        for room in ROOMS:
            c = cnt.get((d, room))
            if not c: continue
            need = [_need(room, n) for n in c]
            raw = list(need)
            if room != 'School-age':
                i = HOURS.index(_BREAK_HOUR[room])
                if need[i] >= 1: raw[i] += 1
            plan[room] = (c, need, raw)
        for room in ROOMS:
            if room not in plan: continue
            c, need, raw = plan[room]
            pieces = []
            for k in range(1, max(raw) + 1):
                runs = []; h0 = None
                for i, h in enumerate(HOURS + [99]):
                    on = i < len(HOURS) and raw[i] >= k
                    if on and h0 is None: h0 = h
                    if not on and h0 is not None: runs.append((h0, HOURS[i - 1] + 1)); h0 = None
                for a, b in runs:
                    hb = _BREAK_HOUR.get(room)
                    cover = (k > 1 and room != 'School-age' and (a, b) == (hb, hb + 1) and k == max(raw) and need[HOURS.index(hb)] < raw[HOURS.index(hb)])
                    if not cover and b - a > 9:
                        m = a + 8; pieces.append((a, m, False)); pieces.append((m, b, False))
                    else: pieces.append((a, b, cover))
            pieces.sort(key=lambda p: (p[2], p[0]))
            for a, b, cover in pieces:
                order = (_FLOAT + _MGMT) if cover else (_PREF[room] + _ASSIST + _FLOAT + _MGMT)
                nm = next((x for x in order if can(x, a, b)), None)
                kind = 'Break cover' if cover else ('Regular' if (nm in _PREF[room] or room == 'School-age') else 'Relief')
                if nm is None:
                    nm = 'Tobias Lindgren' if not any(x == nm for x in ()) else nm; kind = 'Relief'
                take(nm, a, b); day_rows.append(dict(staff=nm, room=room, start=a, end=b, kind=kind, break_start='', _cover=cover))
            # breaks: long shifts take a slot where the cover lane gives slack
            slack = {h: raw[HOURS.index(h)] - need[HOURS.index(h)] for h in HOURS}
            used = {h: 0 for h in HOURS}
            mine = [x for x in day_rows if x['room'] == room and x['end'] - x['start'] >= 7 and not x.get('_cover')]
            hb = _BREAK_HOUR.get(room)
            for x in mine:
                if hb and x['start'] <= hb and x['end'] >= hb + 1 and used[hb] < slack[hb]:
                    x['break_start'] = hb; used[hb] += 1
            if room != 'School-age' and (d == sd_pick and room == 'Toddlers' or d in old_shorts and room == ['Toddlers', 'Twos', 'Preschool'][d.toordinal() % 3]):
                cand = [x for x in day_rows if x['room'] == room and x['start'] <= hb and x['end'] >= hb + 1 and not x.get('_cover')]
                if len(cand) >= 2 and need[HOURS.index(hb)] >= 2:
                    for x in cand[:2]: x['break_start'] = hb
        for x in day_rows:
            x['date'] = d
            nm = x['staff']; p = POOL[nm]
            bm = 30 if x['break_start'] != '' else 0
            x['break_minutes'] = bm
            x['hours'] = R2(x['end'] - x['start'] - bm / 60.0)
            x['rate'] = _wage(nm, p['rate'], d) if p['pay_type'] == 'Hourly' else 0.0
            x['cost'] = R2(x['hours'] * x['rate'] * (1 + EMPLOYER_COST_PCT))
            out.append(x)
        # ratio rows for this day
        for room in ROOMS:
            if room not in plan: continue
            c, need, raw = plan[room]
            sh = [x for x in day_rows if x['room'] == room]
            for i, h in enumerate(HOURS):
                if c[i] <= 0: continue
                present = sum(1 for x in sh if x['start'] <= h < x['end']) - sum(1 for x in sh if x['break_start'] == h)
                ratio.append(dict(date=d, hour=h, room=room, children=c[i], ratio=RM[room]['ratio'], needed=need[i], present=present, gap=need[i] - present))
    return out, ratio


def _sh(): return _raw('shifts', _shifts)


def shift_rows(n=None):
    out = []
    for i, x in enumerate(_sh()[0], 1):
        d = x['date']
        out.append(dict(shift_id='SH-%05d' % i, date=iso(d), week=iso(week_start(d)), month=iso(_ms(d)), weekday=WEEKDAYS[d.weekday()], staff=x['staff'], role=POOL[x['staff']]['role'],
                        room=x['room'], start='%02d:00' % x['start'], end='%02d:00' % x['end'], break_start=('%02d:00' % x['break_start']) if x['break_start'] != '' else '',
                        break_minutes=x['break_minutes'], hours=x['hours'], kind=x['kind'], rate=x['rate'], cost=x['cost']))
    return _thin(out, n)


def ratio_hour_rows(n=None, days=None):
    rows = _sh()[1]
    if days: rows = [x for x in rows if x['date'] >= TODAY - day(days)]
    out = [dict(slot_id='RH-%05d' % i, date=iso(x['date']), week=iso(week_start(x['date'])), month=iso(_ms(x['date'])), weekday=WEEKDAYS[x['date'].weekday()], hour='%02d:00' % x['hour'],
                room=x['room'], children=x['children'], ratio=x['ratio'], needed=x['needed'], present=x['present'], gap=x['gap']) for i, x in enumerate(rows, 1)]
    return _thin(out, n)


def ratio_short_hours(days=30):
    return [x for x in _sh()[1] if x['gap'] > 0 and x['date'] >= TODAY - day(days)]


# ------------------------------------------------------------------ world 4: late fees, invoices, payments, government payments, deposits
_WD_CACHE = {}
def _weekdays(a, b):
    out = []; d = a
    while d <= b:
        if d.weekday() < 5: out.append(d)
        d += day(1)
    return out


def _late_fees():
    out = []; r = rng('late')
    for x in _att():
        if x['late_minutes'] > LATE_GRACE_MIN:
            fee = R2(x['late_minutes'] * LATE_FEE_PER_MIN)
            out.append(dict(date=x['date'], child_id=x['child_id'], child=x['child'], family_id=x['family_id'], late_minutes=x['late_minutes'], fee=fee, waived=r.random() < .33, invoice_id=''))
    for i, x in enumerate(out, 1): x['fee_id'] = 'LF-%04d' % i
    return out


def _price_day(prog, d): return PRG[prog]['price_day'] if to_date(d) >= D(TODAY.year, 1, 1) else R2(PRG[prog]['price_day'] - 2.0)


def _camp_fee(c, ps, pe, monthly):
    tot = 0.0; weeks = []
    for wk, prog in CAMP.items():
        inp = (ps <= wk <= pe) if not monthly else (_ms(wk) == ps)
        if not inp or c['start'] > wk + day(4) or (c['end'] is not None and c['end'] < wk): continue
        if _room_at(c, wk) != 'School-age' or not _signed_up(c, wk): continue
        nd = sum(1 for k in range(5) if is_open(wk + day(k)))
        tot += _price_day(prog, wk) * nd; weeks.append(wk)
    return R2(tot), weeks


def _accounts():
    r = rng('acct'); fams = _families(); lf = _late_fees(); att = _att()
    # extras by family: late fees and drop-in days
    lf_by = {}
    for x in lf: lf_by.setdefault(x['family_id'], []).append(x)
    dr_by = {}
    for x in att:
        if x['extra'] and x['status'] == 'Present':
            rate = RATE[(x['room'], x['schedule'])]['day_rate'] if x['room'] != 'School-age' else 22.0
            rate = rate if x['date'] >= D(TODAY.year, 1, 1) else R2(rate / 1.03)
            dr_by.setdefault(x['family_id'], []).append((x['date'], R2(rate * (1 + DROP_IN_SURCHARGE))))
    invoices = []; payments = []
    story_fam = next(f for f in fams if f['story'])
    for f in fams:
        kids = f['_kids']; first = min(c['start'] for c in kids); last = max((c['end'] or TODAY) for c in kids)
        monthly = f['cycle'] == 'Monthly'
        if monthly:
            ps_list = [m for m in (add_months(_ms(HISTORY_START), k) for k in range(0, 30)) if m <= _ms(TODAY) and _eom(m) >= first and m <= last]
        else:
            w = week_start(max(first, HISTORY_START)); ps_list = []
            while w <= week_start(TODAY) and w <= last: ps_list.append(w); w += day(7)
        prev = None
        for ps in ps_list:
            pe = _eom(ps) if monthly else ps + day(4)
            wds = _weekdays(ps, pe)
            tuition = disc = reg = sup = 0.0; nkids = 0; camp = 0.0; roomnet = {}; roomx = {}
            for c in kids:
                enr = [d for d in wds if c['start'] <= d and (c['end'] is None or d <= c['end'])]
                if not enr: continue
                nkids += 1
                d0 = enr[0]; room = _room_at(c, d0); sched, _ = _sched_at(c, d0)
                td = [d for d in enr if not (_room_at(c, d) == 'School-age' and _camp_week(d))]
                weeks = (52.0 / 12.0 if monthly else 1.0) * len(td) / float(len(wds))
                t = R2(_rate(room, sched, ps) * weeks)
                dc = R2(t * {'None': 0.0, 'Sibling': SIBLING_PCT, 'Staff': STAFF_PCT}[c['disc']])
                tuition += t; disc += dc; roomnet[room] = roomnet.get(room, 0.0) + t - dc; xr = 0.0
                if ps <= c['start'] <= pe and c['start'] >= HISTORY_START: reg += REG_FEE if c['start'] >= D(TODAY.year, 1, 1) else REG_FEE - 20; xr += REG_FEE
                sd = _first_open(D(ps.year, 9, 1))
                if ps <= sd <= pe and c['start'] <= sd and (c['end'] is None or c['end'] >= sd): sup += SUPPLY_FEE if sd.year == TODAY.year else SUPPLY_FEE - 10; xr += SUPPLY_FEE
                cf, _w = _camp_fee(c, ps, pe, monthly); camp += cf; roomnet['School-age'] = roomnet.get('School-age', 0.0) + cf
                roomx[room] = roomx.get(room, 0.0) + xr
            if nkids == 0: continue
            pprev = (ps - day(7)) if not monthly else add_months(ps, -1)
            pprev_end = (pprev + day(6)) if not monthly else _eom(pprev)
            late = 0.0; drop = 0.0
            for x in lf_by.get(f['family_id'], []):
                if pprev <= x['date'] <= pprev_end and not x['waived']: late += x['fee']; x['invoice_id'] = 'pending'
            for d_, v in dr_by.get(f['family_id'], []):
                if pprev <= d_ <= pprev_end: drop += v
            tuition, disc = R2(tuition), R2(disc)
            amount = R2(tuition - disc + reg + sup + camp + drop + late)
            gov = R2((tuition - disc) * f['gov_share'])
            inv = dict(family_id=f['family_id'], family=f['family'], cycle=f['cycle'], period_start=ps, period_end=pe, issued_on=ps, due_date=ps + day(INVOICE_DAYS if monthly else WEEKLY_DUE_DAYS),
                       children=nkids, tuition=tuition, discount=disc, registration=R2(reg), supply_fee=R2(sup), camp_fee=camp, drop_in=R2(drop), late_fees=R2(late), amount=amount,
                       gov_expected=gov, parent_due=R2(amount - gov), _f=f, _roomnet=roomnet, _roomx=roomx, _extra=R2(drop + late), _pay=[], _story=False, _plan=False, _pfrom=pprev, _pto=pprev_end)
            invoices.append(inv)
    invoices.sort(key=lambda x: (x['issued_on'], x['family_id']))
    for i, inv in enumerate(invoices, 1):
        inv['invoice_id'] = 'IV-%05d' % i
        for x in lf_by.get(inv['family_id'], []):
            if x['invoice_id'] == 'pending' and inv['_pfrom'] <= x['date'] <= inv['_pto']: x['invoice_id'] = inv['invoice_id']
    for x in lf:
        if x['invoice_id'] == 'pending': x['invoice_id'] = ''
    # payments
    pr_ = rng('pay'); plan_pool = []
    for inv in invoices:
        f = inv['_f']; rr = rng('p-' + inv['invoice_id']); due = inv['due_date']; amt = inv['parent_due']
        if amt <= 0.009: inv['_pay'] = [(due, 0.0)]; continue
        h = f['habit']
        dl = {'Prompt': (0, 0 if f['autopay'] else 3), 'Normal': (1, 7), 'Slow': (8, 24), 'Very slow': (22, 38)}[h]
        d1 = due + day(rr.randint(*dl))
        if f['pay_method'] == 'Cash': d1 += day(1)
        if rr.random() < .04 and amt > 150:
            a1 = R2(amt * rr.uniform(.45, .7)); inv['_pay'] = [(d1, a1), (d1 + day(rr.randint(10, 30)), R2(amt - a1))]
        else: inv['_pay'] = [(d1, amt)]
        if h in ('Slow', 'Very slow') and amt > 450 and inv['issued_on'] < TODAY - day(150) and len(plan_pool) < 3 and rr.random() < .35:
            n = 4; base = R2(amt / n); inv['_pay'] = [(d1 + day(30 * k), base if k < n - 1 else R2(amt - base * (n - 1))) for k in range(n)]; inv['_plan'] = True; plan_pool.append(inv)
    # story family: the last three monthly invoices stay unpaid
    sinv = [x for x in invoices if x['family_id'] == story_fam['family_id']]
    for x in sinv:
        if x['period_start'] >= month_start(2): x['_pay'] = []; x['_story'] = True
    # bad debt: two old invoices of a family that left are written off
    wo = [x for x in invoices if x['_f']['_kids'][-1]['end'] and x['_f']['_kids'][-1]['end'] < TODAY - day(200) and x['issued_on'] > x['_f']['_kids'][-1]['end'] - day(60)
          and x['parent_due'] > 300 and not x['_f']['story']]
    for x in wo[-2:]: x['_pay'] = [(x['due_date'] + day(20), R2(x['parent_due'] * .25))]; x['_wo'] = True
    for x in invoices:
        paid = [(d_, a) for d_, a in x['_pay'] if d_ <= TODAY]; tot = R2(sum(a for _, a in paid))
        x['paid_amount'] = tot if x['parent_due'] > 0 else 0.0
        if x.get('_wo'): x['status'] = 'Written off'; x['paid_on'] = ''
        elif x['parent_due'] <= 0.009 or tot >= x['parent_due'] - .005: x['status'] = 'Paid'; x['paid_on'] = iso(max([d_ for d_, _ in paid])) if paid else iso(x['due_date'])
        elif tot > 0: x['status'] = 'Part paid'; x['paid_on'] = ''
        else: x['status'] = 'Unpaid'; x['paid_on'] = ''
        if x['parent_due'] <= 0.009: x['paid_on'] = iso(x['due_date']) if x['due_date'] <= TODAY else ''; x['status'] = 'Paid' if x['due_date'] <= TODAY else 'Unpaid'
    for inv in invoices:
        f = inv['_f']
        for k, (d_, a) in enumerate(inv['_pay']):
            if d_ <= TODAY and a > 0:
                payments.append(dict(date=d_, family_id=f['family_id'], family=f['family'], invoice_id=inv['invoice_id'], amount=a, method=f['pay_method'], kind='Plan instalment' if inv['_plan'] else 'Invoice'))
    # deposits (one week of tuition, paid two weeks before the start)
    deposits = []
    for c in _kids():
        f = _fam_map()[c['family_id']]; sched, _ = _sched_at(c, c['start']); room = _room_at(c, c['start'])
        amt = float(round(_rate(room, sched, c['start'])))
        rec = c['start'] - day(14); st = 'Held'; settled = ''
        if c['end'] is not None and c['end'] < TODAY:
            notice = (c['end'] - c['notice_on']).days if c['notice_on'] else 99
            if notice < NOTICE_DAYS: st = 'Kept'
            else: st = 'Applied' if rng('dep-' + c['child_id']).random() < .8 else 'Refunded'
            settled = c['end'] + day(5)
        deposits.append(dict(child_id=c['child_id'], child=c['child'], family_id=c['family_id'], family=c['family'], amount=amt, received_on=rec, status=st, settled_on=settled,
                             notice_days=(c['end'] - c['notice_on']).days if c['end'] and c['notice_on'] else ''))
        if rec >= HISTORY_START: payments.append(dict(date=rec, family_id=c['family_id'], family=c['family'], invoice_id='', amount=amt, method=f['pay_method'] if f['pay_method'] != 'Cash' else 'Bank transfer', kind='Deposit'))
    payments.sort(key=lambda x: (x['date'], x['family_id']))
    for i, p in enumerate(payments, 1): p['payment_id'] = 'PM-%05d' % i
    for i, dp in enumerate(deposits, 1): dp['deposit_id'] = 'DP-%04d' % i
    # government payments per family and month
    gov = []
    for f in fams:
        if not f['gov_share']: continue
        by = {}
        for inv in invoices:
            if inv['family_id'] == f['family_id'] and inv['gov_expected'] > 0: by[_ms(inv['period_start'])] = by.get(_ms(inv['period_start']), 0) + inv['gov_expected']
        lag = rng('govlag-' + f['family_id']).randint(12, 26)
        for m, e in sorted(by.items()):
            e = R2(e); po = _eom(m) + day(lag); st = 'Paid' if po <= TODAY else 'Expected'
            gov.append(dict(month=m, family_id=f['family_id'], family=f['family'], expected=e, received=e if st == 'Paid' else 0.0, paid_on=po if st == 'Paid' else '', due_on=po, status=st))
    # story: the biggest government family is short-paid for September
    cur = month_start(2)
    cand = [g for g in gov if g['month'] == cur and g['status'] == 'Paid']
    sg = max(cand, key=lambda g: g['expected'])
    sg['received'] = R2(sg['expected'] * .7); sg['status'] = 'Short-paid'; sg['_story'] = True
    for g in gov: g.setdefault('_story', False)
    gov.sort(key=lambda g: (g['month'], g['family_id']))
    for i, g in enumerate(gov, 1): g['gov_id'] = 'GP-%04d' % i
    return dict(invoices=invoices, payments=payments, deposits=deposits, gov=gov, late=lf, plans=plan_pool, story_family=story_fam)


def _acc(): return _raw('acct', _accounts)


def late_fee_rows(n=None):
    return _thin([dict(fee_id=x['fee_id'], date=iso(x['date']), month=iso(_ms(x['date'])), child_id=x['child_id'], child=x['child'], family_id=x['family_id'], late_minutes=x['late_minutes'],
                       fee=x['fee'], waived=x['waived'], charged=0.0 if x['waived'] else x['fee'], invoice_id=x['invoice_id']) for x in _acc()['late']], n)


def invoice_rows(n=None):
    out = []
    for x in _acc()['invoices']:
        out.append(dict(invoice_id=x['invoice_id'], family_id=x['family_id'], family=x['family'], cycle=x['cycle'], month=iso(_ms(x['period_start'])), period_start=iso(x['period_start']),
                        period_end=iso(x['period_end']), issued_on=iso(x['issued_on']), due_date=iso(x['due_date']), children=x['children'], tuition=x['tuition'], discount=x['discount'],
                        registration=x['registration'], supply_fee=x['supply_fee'], camp_fee=x['camp_fee'], drop_in=x['drop_in'], late_fees=x['late_fees'], amount=x['amount'],
                        gov_expected=x['gov_expected'], parent_due=x['parent_due'], paid_amount=x['paid_amount'], paid_on=x['paid_on'], status=x['status']))
    return _thin(out, n)


def payment_rows(n=None):
    return _thin([dict(payment_id=x['payment_id'], date=iso(x['date']), month=iso(_ms(x['date'])), family_id=x['family_id'], family=x['family'], invoice_id=x['invoice_id'], amount=x['amount'],
                       method=x['method'], kind=x['kind']) for x in _acc()['payments']], n)


def gov_payment_rows(n=None):
    return _thin([dict(gov_id=x['gov_id'], month=iso(x['month']), family_id=x['family_id'], family=x['family'], expected=x['expected'], received=x['received'], due_on=iso(x['due_on']),
                       paid_on=iso(x['paid_on']) if x['paid_on'] else '', status=x['status']) for x in _acc()['gov']], n)


def deposit_rows(n=None):
    return _thin([dict(deposit_id=x['deposit_id'], child_id=x['child_id'], child=x['child'], family_id=x['family_id'], family=x['family'], amount=x['amount'], received_on=iso(x['received_on']),
                       status=x['status'], settled_on=iso(x['settled_on']) if x['settled_on'] else '', notice_days=x['notice_days']) for x in _acc()['deposits']], n)


# ------------------------------------------------------------------ statements, ageing, promises, plans
def _paid_by(inv, asof): return R2(sum(a for d_, a in inv['_pay'] if d_ <= asof))


def _open_balance(inv, asof):
    if inv['issued_on'] > asof or inv.get('_wo') and asof >= inv['due_date'] + day(200): return 0.0
    if inv.get('_wo'): return R2(inv['parent_due'] - _paid_by(inv, asof))
    return max(0.0, R2(inv['parent_due'] - _paid_by(inv, asof)))


def _band(days):
    return AGE_BANDS[0] if days <= 30 else AGE_BANDS[1] if days <= 60 else AGE_BANDS[2] if days <= 90 else AGE_BANDS[3]


def ageing_rows(n=None):
    """open balances per family today (days outstanding = today - due date, negative counts as 0)"""
    by = {}
    for inv in _acc()['invoices']:
        b = _open_balance(inv, TODAY)
        if b <= 0.009 or inv.get('_wo'): continue
        f = by.setdefault(inv['family_id'], dict(family_id=inv['family_id'], family=inv['family'], balance=0.0, b0=0.0, b31=0.0, b61=0.0, b90=0.0, oldest_days=0, invoices=0, cycle=inv['cycle']))
        dd = max(0, (TODAY - inv['due_date']).days); f['balance'] += b; f['invoices'] += 1; f['oldest_days'] = max(f['oldest_days'], dd)
        f[{AGE_BANDS[0]: 'b0', AGE_BANDS[1]: 'b31', AGE_BANDS[2]: 'b61', AGE_BANDS[3]: 'b90'}[_band(dd)]] += b
    out = []
    for i, f in enumerate(sorted(by.values(), key=lambda x: (-x['oldest_days'], x['family_id'])), 1):
        out.append(dict(ageing_id='AG-%03d' % i, as_of=iso(TODAY), family_id=f['family_id'], family=f['family'], cycle=f['cycle'], balance=R2(f['balance']), days_0_30=R2(f['b0']), days_31_60=R2(f['b31']),
                        days_61_90=R2(f['b61']), days_90_plus=R2(f['b90']), oldest_days=f['oldest_days'], open_invoices=f['invoices']))
    return _thin(out, n)


def ageing_month_rows(n=None):
    out = []
    for m in months14():
        asof = TODAY if m == _ms(TODAY) else _eom(m); tot = {b: 0.0 for b in AGE_BANDS}
        for inv in _acc()['invoices']:
            b = _open_balance(inv, asof)
            if b > .009 and not inv.get('_wo'): tot[_band(max(0, (asof - inv['due_date']).days))] += b
        for b in AGE_BANDS:
            out.append(dict(row_id='AM-%03d' % (len(out) + 1), month=iso(m), as_of=iso(asof), band=b, amount=R2(tot[b])))
    return _thin(out, n)


def promise_rows(n=None):
    out = []; r = rng('promise')
    for f in _families():
        if f['habit'] not in ('Slow', 'Very slow') and not f['story']: continue
        invs = [x for x in _acc()['invoices'] if x['family_id'] == f['family_id'] and x['parent_due'] > 200 and x['due_date'] < TODAY - day(10)]
        for inv in invs[-3:]:
            last = inv['_pay'][-1][0] if inv['_pay'] else None
            if inv['_story']:
                out.append(dict(promised_on=inv['due_date'] + day(21), family_id=f['family_id'], family=f['family'], invoice_id=inv['invoice_id'], promised_amount=inv['parent_due'], method='Phone', outcome='Broken'))
            elif last:
                out.append(dict(promised_on=last, family_id=f['family_id'], family=f['family'], invoice_id=inv['invoice_id'], promised_amount=inv['parent_due'], method=r.choice(['Phone', 'Message', 'Email']), outcome='Kept'))
    cur = [x for x in _acc()['invoices'] if x['status'] in ('Unpaid', 'Part paid') and x['due_date'] < TODAY - day(2) and not x['_story']]
    for inv in cur[:3]:
        out.append(dict(promised_on=TODAY + day(r.randint(2, 6)), family_id=inv['family_id'], family=inv['family'], invoice_id=inv['invoice_id'], promised_amount=R2(inv['parent_due'] - _paid_by(inv, TODAY)),
                        method='Phone', outcome='Pending'))
    sf = _acc()['story_family']; so = [x for x in _acc()['invoices'] if x['family_id'] == sf['family_id'] and x['_story']]
    out.append(dict(promised_on=TODAY + day(4), family_id=sf['family_id'], family=sf['family'], invoice_id=so[-1]['invoice_id'], promised_amount=R2(sum(x['parent_due'] for x in so)), method='Phone', outcome='Pending'))
    out.sort(key=lambda x: x['promised_on'])
    return _thin([dict(promise_id='PR-%03d' % i, promised_on=iso(x['promised_on']), **{k: v for k, v in x.items() if k != 'promised_on'}) for i, x in enumerate(out, 1)], n)


def plan_rows(n=None):
    out = []
    for i, inv in enumerate(_acc()['plans'], 1):
        pays = inv['_pay']; paid = sum(1 for d_, _ in pays if d_ <= TODAY)
        out.append(dict(plan_id='PP-%02d' % i, family_id=inv['family_id'], family=inv['family'], invoice_id=inv['invoice_id'], balance=inv['parent_due'], instalments=len(pays),
                        instalment=R2(inv['parent_due'] / len(pays)), first_due=iso(pays[0][0]), paid_instalments=paid, status='Completed' if paid >= len(pays) else 'On track'))
    return _thin(out, n)


def statement_rows(n=None):
    out = []
    for y in (TODAY.year - 1, TODAY.year):
        by = {}
        for p in _acc()['payments']:
            if p['date'].year == y and p['kind'] != 'Deposit': by.setdefault(p['family_id'], [p['family'], 0.0, 0.0, 0])[1:] = [by.get(p['family_id'], [0, 0, 0, 0])[1] + p['amount'], 0, by.get(p['family_id'], [0, 0, 0, 0])[3] + 1]
        for g in _acc()['gov']:
            if g['month'].year == y and g['status'] in ('Paid', 'Short-paid'):
                e = by.setdefault(g['family_id'], [g['family'], 0.0, 0.0, 0]); e[2] += g['received']
        for fid, (fam, par, gv, k) in sorted(by.items()):
            out.append(dict(family_id=fid, family=fam, year=y, parent_paid=R2(par), government_paid=R2(gv), total_paid=R2(par + gv), payments=k,
                            sent_on=iso(D(TODAY.year, 1, 20)) if y < TODAY.year else ''))
    return _thin([dict(statement_id='ST-%04d' % i, **x) for i, x in enumerate(out, 1)], n)


# ------------------------------------------------------------------ enquiries, tours, waiting list, marketing
_SEAS = [0, 1.25, 1.2, 1.1, 1.0, .95, .85, .7, 1.3, 1.3, 1.0, .9, .7]
_SRC_W = [.22, .20, .15, .10, .15, .08, .10]
_SRC_COST_MAP = {'Online directory': 'Online directory', 'Website upkeep': 'Website', 'Roadside sign': 'Roadside sign', 'Local flyers': 'Local event', 'Open day': 'Local event',
                 'Referral reward': 'Current family'}


def _enquiries():
    _families(); r = rng('enq'); rn = rng('enqnames'); out = []
    nameset = set()
    def person():
        g = _G[rn.randrange(len(_G))]
        return '%s %s' % (rn.choice(_PARENT_FIRST), rn.choice(g[1]))
    def base(d, source=None):
        nm = person()
        lag = r.choice([2, 4, 6, 12, 20, 26, 40, 60]) if r.random() < .4 else r.choice([1, 2, 3, 5, 8, 14, 22])
        return dict(date=d, name=nm, phone=fake_phone(900 + len(out)), email=fake_email(nm, 0), source=source or _wchoice(r, SOURCES, _SRC_W), first_reply_hours=lag,
                    child_age_months=0, want_room='', want_schedule='', want_start='', status='Lost', reason='', tour_date='', tour_status='', applied_on='', enrolled_on='', child_id='', _kind='')
    # enrolled children: one enquiry each
    for c in _kids():
        if c['pre'] or c['start'] < HISTORY_START + day(20): continue
        d = max(HISTORY_START, c['start'] - day(r.randint(25, 95)))
        e = base(d); e['name'] = c['guardian']; e['email'] = fake_email(c['guardian'], 0); e['phone'] = _fam_map()[c['family_id']]['phone']
        if c['sibling']: e['source'] = 'Current family'
        room = c['moves'][0][1]; e['status'] = 'Enrolled'; e['child_age_months'] = max(2, _age(c['dob'], d)); e['want_room'] = room; e['want_schedule'] = c['sched']; e['want_start'] = c['start']
        e['first_reply_hours'] = min(e['first_reply_hours'], 24)
        e['tour_date'] = min(c['start'] - day(10), d + day(r.randint(3, 14))); e['tour_date'] = max(e['tour_date'], d + day(1)); e['tour_status'] = 'Held'
        e['applied_on'] = e['tour_date'] + day(r.randint(1, 8)); e['enrolled_on'] = min(e['applied_on'] + day(r.randint(2, 12)), c['start'] - day(3)); e['child_id'] = c['child_id']; e['_kind'] = 'enrolled'
        out.append(e)
    # other enquiries month by month
    for m in range(24):
        M1 = month_start(23 - m); n_ = int(round(11.5 * _SEAS[M1.month] + r.uniform(-1.5, 1.5)))
        for _ in range(n_):
            d = M1 + day(r.randint(0, 27))
            if d > TODAY - day(36): continue
            e = base(d); e['_kind'] = 'lost'
            room = _wchoice(r, ROOMS, [.14, .2, .2, .3, .16]); e['want_room'] = room
            lo, hi = RM[room]['age_from'], RM[room]['age_to'] - 1
            if room == 'School-age': lo, hi = 62, 100
            e['child_age_months'] = r.randint(lo, hi); e['want_schedule'] = _wchoice(r, SCHEDULES, _SCH_W[room] if room != 'School-age' else [0, 0, 0, .6, .4]); e['want_start'] = d + day(r.randint(30, 120))
            e['first_reply_hours'] = r.choice([1, 2, 3, 5, 8, 12, 20, 28, 40, 52]) if r.random() < .75 else r.choice([3, 6, 10])
            p = r.random()
            if p < .36: pass
            elif p < .46: e['tour_date'] = d + day(r.randint(2, 12)); e['tour_status'] = r.choice(['No-show', 'Cancelled'])
            else: e['tour_date'] = d + day(r.randint(2, 12)); e['tour_status'] = 'Held'
            slow = e['first_reply_hours'] > 30
            e['reason'] = 'Slow reply' if slow and r.random() < .6 else _wchoice(r, LOST_REASONS, [.30, .22, .16, .18, .14])
            if e['tour_status'] == 'Held' and r.random() < .3: e['applied_on'] = e['tour_date'] + day(r.randint(1, 7)); e['reason'] = 'No place'
            if e['tour_status'] in ('No-show', 'Cancelled') and r.random() < .5: e['reason'] = 'Hours'
            out.append(e)
    # the pipeline today
    def pipe(status, ago_enq, tour=None, applied=None, room=None, start=None):
        e = base(TODAY - day(ago_enq)); e['status'] = status; e['_kind'] = 'pipeline'
        room = room or _wchoice(r, ROOMS, [.14, .2, .2, .3, .16]); e['want_room'] = room
        lo, hi = RM[room]['age_from'], RM[room]['age_to'] - 1
        if room == 'School-age': lo, hi = 62, 100
        e['child_age_months'] = r.randint(lo, hi); e['want_schedule'] = _wchoice(r, SCHEDULES, _SCH_W[room]); e['want_start'] = TODAY + day(start or r.randint(30, 110)); e['first_reply_hours'] = r.choice([1, 2, 3, 5, 8, 20])
        if tour is not None: e['tour_date'] = TODAY + day(tour); e['tour_status'] = 'Booked' if tour > 0 else 'Held'
        if applied is not None: e['applied_on'] = TODAY - day(applied)
        out.append(e); return e
    for k in (1, 1, 2, 3): pipe('New', k)
    for k, t in zip((4, 5, 6, 8, 11), (1, 2, 4, 6, 9)): pipe('Tour booked', k, tour=t)
    for k, t in zip((9, 12, 15, 19), (-1, -3, -6, -9)): pipe('Tour held', k, tour=t)
    for k, a, rm in ((22, 3, 'Twos'), (27, 6, 'Preschool')): pipe('Applied', k, tour=-(k - 6), applied=a, room=rm, start=35)
    for rm, k, st in (('Infants', 140, 'Waitlist'), ('Infants', 60, 'Waitlist'), ('Toddlers', 210, 'Waitlist'), ('Toddlers', 95, 'Waitlist'), ('Toddlers', 40, 'Waitlist'), ('Twos', 175, 'Waitlist'),
                      ('Twos', 70, 'Waitlist'), ('Preschool', 260, 'Waitlist'), ('Preschool', 180, 'Waitlist'), ('Preschool', 88, 'Waitlist'), ('Preschool', 33, 'Waitlist'),
                      ('School-age', 120, 'Waitlist'), ('School-age', 52, 'Waitlist')):
        e = pipe(st, k, tour=-(k - 8), room=rm, start=r.randint(20, 150)); e['_kind'] = 'waiting'
    out.sort(key=lambda e: (e['date'], e['name']))
    for i, e in enumerate(out, 1): e['enquiry_id'] = 'EN-%04d' % i
    # recent lost ones so the last 30 days have losses too
    return out


def _enq(): return _raw('enq', _enquiries)


def enquiry_rows(n=None):
    out = []
    for e in _enq():
        out.append(dict(enquiry_id=e['enquiry_id'], date=iso(e['date']), month=iso(_ms(e['date'])), name=e['name'], phone=e['phone'], email=e['email'], child_age_months=e['child_age_months'],
                        want_room=e['want_room'], want_schedule=e['want_schedule'], want_start=iso(e['want_start']) if e['want_start'] else '', source=e['source'],
                        first_reply_hours=e['first_reply_hours'], status=e['status'], reason=e['reason'], tour_date=iso(e['tour_date']) if e['tour_date'] else '', tour_status=e['tour_status'],
                        applied_on=iso(e['applied_on']) if e['applied_on'] else '', enrolled_on=iso(e['enrolled_on']) if e['enrolled_on'] else '', child_id=e['child_id']))
    return _thin(out, n)


def tour_rows(n=None):
    out = []; r = rng('tour')
    for e in _enq():
        if not e['tour_date']: continue
        out.append(dict(date=iso(e['tour_date']), month=iso(_ms(e['tour_date'])), enquiry_id=e['enquiry_id'], name=e['name'], phone=e['phone'], staff=r.choice([OWNER, ASSISTANT_DIRECTOR, OWNER]),
                        status=e['tour_status'], source=e['source'], applied=bool(e['applied_on']), room=e['want_room']))
    out.sort(key=lambda x: x['date'])
    return _thin([dict(tour_id='TR-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


def waitlist_rows(n=None):
    out = []; r = rng('wl')
    for e in _enq():
        if e['_kind'] == 'waiting':
            offered = e['name'] in () ; out.append(dict(enquiry_id=e['enquiry_id'], name=e['name'], phone=e['phone'], child_age_months=e['child_age_months'], room=e['want_room'], schedule=e['want_schedule'],
                                                         want_start=iso(e['want_start']), added_on=iso(e['date'] + day(r.randint(6, 12)) if e['date'] + day(12) <= TODAY else e['date']), offered_on='', started_on='',
                                                         priority=r.choice(PRIORITIES), status='Waiting', child_id=''))
        elif e['_kind'] == 'enrolled' and e['status'] == 'Enrolled' and r.random() < .38:
            out.append(dict(enquiry_id=e['enquiry_id'], name=e['name'], phone=e['phone'], child_age_months=e['child_age_months'], room=e['want_room'], schedule=e['want_schedule'], want_start=iso(e['want_start']),
                            added_on=iso(e['date'] + day(5)), offered_on=iso(max(e['date'] + day(10), e['want_start'] - day(r.randint(12, 40)))), started_on=iso(e['want_start']), priority=r.choice(PRIORITIES),
                            status='Started', child_id=e['child_id']))
        elif e['_kind'] == 'lost' and e['reason'] in ('No place',) and e['applied_on']:
            out.append(dict(enquiry_id=e['enquiry_id'], name=e['name'], phone=e['phone'], child_age_months=e['child_age_months'], room=e['want_room'], schedule=e['want_schedule'], want_start=iso(e['want_start']),
                            added_on=iso(e['date'] + day(8)), offered_on='', started_on='', priority=r.choice(PRIORITIES), status='Withdrawn', child_id=''))
    # two open offers
    w = [x for x in out if x['status'] == 'Waiting' and x['room'] in ('Toddlers', 'Preschool')]
    for x, k in zip(w[:2], (2, 5)): x['status'] = 'Offered'; x['offered_on'] = ago(k)
    out.sort(key=lambda x: (x['added_on'], x['name']))
    return _thin([dict(wait_id='WL-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


def marketing_rows(n=None):
    out = []; enq = _enq()
    for m in range(24):
        M1 = month_start(23 - m); yr = M1.year == TODAY.year
        lines = [('Online directory', 85.0 if yr else 80.0), ('Website upkeep', 40.0)]
        lines.append(('Roadside sign', 50.0))
        if M1.month in (1, 4, 7, 10): lines.append(('Local flyers', 180.0))
        if M1.month in (3, 9): lines.append(('Open day', 250.0))
        enr_ref = sum(1 for e in enq if e['status'] == 'Enrolled' and _ms(e['date']) == M1 and e['source'] == 'Current family')
        if enr_ref: lines.append(('Referral reward', 100.0 * enr_ref))
        for kind, cost in lines:
            src = _SRC_COST_MAP[kind]
            ne = sum(1 for e in enq if _ms(e['date']) == M1 and e['source'] == src); nn = sum(1 for e in enq if _ms(e['date']) == M1 and e['source'] == src and e['status'] == 'Enrolled')
            out.append(dict(month=iso(M1), kind=kind, source=src, cost=cost, enquiries=ne, enrolled=nn))
    return _thin([dict(campaign_id='MK-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


# ------------------------------------------------------------------ meals and menu
_MEAL_COST = {'Breakfast': .55, 'Lunch': 1.60, 'Afternoon snack': .50}


def _meals():
    out = []; r = rng('meals'); day_pres = {}
    for x in _att():
        if x['status'] == 'Present': day_pres[(x['date'], x['room'])] = day_pres.get((x['date'], x['room']), 0) + 1
    srv = {}
    for x in _att():
        if x['status'] != 'Present': continue
        k = (x['date'], x['room']); a = srv.setdefault(k, [0, 0, 0])
        if x['_mi'] <= 7 * 60 + 50 and x['_mo'] > 8 * 60: a[0] += 1
        if x['_mi'] <= 12 * 60 and x['_mo'] >= 12 * 60 + 30: a[1] += 1
        if x['_mi'] <= 15 * 60 + 30 < x['_mo']: a[2] += 1
    bad = set(); keys = sorted(srv)
    for i in r.sample(range(40, len(keys) - 600), 4): bad.add(keys[i])
    for k in keys:
        pres = day_pres[k]
        for mi, meal in enumerate(MEALS):
            n = srv[k][mi]
            if n <= 0: continue
            if k in bad and mi == 1: n = pres + r.randint(1, 2)
            uc = _MEAL_COST[meal] * (1.03 if k[0] >= D(TODAY.year, 1, 1) else 1.0)
            out.append(dict(date=k[0], meal=meal, room=k[1], present=pres, served=n, eligible=int(round(n * .72)), unit_cost=R2(uc), cost=R2(n * uc)))
    return out


def meal_rows(n=None):
    return _thin([dict(meal_id='ML-%05d' % i, date=iso(x['date']), month=iso(_ms(x['date'])), week=iso(week_start(x['date'])), meal=x['meal'], room=x['room'], children_present=x['present'],
                       served=x['served'], eligible=x['eligible'], unit_cost=x['unit_cost'], cost=x['cost']) for i, x in enumerate(_raw('meals', _meals), 1)], n)


_DISHES = {'Breakfast': ['Oat porridge with fruit', 'Toast and egg', 'Yoghurt and berries', 'Wholegrain cereal and milk', 'Banana pancakes'],
           'Lunch': ['Vegetable pasta bake', 'Rice, lentils and greens', 'Chicken and potato stew', 'Fish cakes and peas', 'Bean chili and rice', 'Cheese omelette and salad', 'Lentil soup and bread',
                     'Turkey meatballs and couscous', 'Veg curry and flatbread', 'Tomato pasta and sweetcorn'],
           'Afternoon snack': ['Apple slices and cheese', 'Hummus and carrot sticks', 'Fruit and crackers', 'Rice cakes and pear', 'Mini sandwiches']}


def menu_rows(n=None):
    out = []
    for wk in range(4):
        for wd in range(5):
            for meal in MEALS:
                dish = _DISHES[meal][(wk * 5 + wd) % len(_DISHES[meal])]
                cost = R2(_MEAL_COST[meal] * 1.03 * (0.9 + 0.05 * ((wk + wd) % 5)))
                out.append(dict(cycle_week=wk + 1, weekday=WEEKDAYS[wd], meal=meal, dish=dish, cost_child=cost, portions_per_kg=round(6 + (wk + wd) % 4 * .5, 1)))
    return _thin([dict(menu_id='MN-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


# ------------------------------------------------------------------ health status, incidents, drills, cleaning and safety checks
def health_rows(n=None):
    r = rng('health'); out = []
    kids = [c for c in _kids() if _status(c) != 'Left']
    story_child = next(c for c in kids if _room_at(c, TODAY) == 'Preschool' and c['start'] < TODAY - day(300))
    for c in kids:
        new = (TODAY - c['start']).days < 30
        for rec in HEALTH_RECORDS:
            if c is story_child and rec == 'Immunisation record':
                st, due, chk = 'Due', TODAY - day(18), TODAY - day(380)
            elif new and r.random() < .45:
                st, due, chk = 'Missing', max(c['start'], TODAY) + day(r.randint(7, 14)), ''
            elif r.random() < .09:
                st, due, chk = 'Due', TODAY + day(r.randint(4, 40)), TODAY - day(r.randint(300, 360))
            else:
                st, due, chk = 'On file', TODAY + day(r.randint(45, 330)), TODAY - day(r.randint(5, 300))
            out.append(dict(child_id=c['child_id'], child=c['child'], room=_room_at(c, max(c['start'], TODAY)), record=rec, status=st, due_date=iso(due), last_checked=iso(chk) if chk else ''))
    return _thin([dict(record_id='HR-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


def incident_rows(n=None):
    r = rng('inc'); out = []; byd = {}
    for x in _att():
        if x['status'] == 'Present': byd.setdefault(x['date'], []).append(x)
    days = sorted(byd)
    cnt = 130; picks = sorted(r.sample(range(len(days) - 40), cnt - 8)) + sorted(r.sample(range(len(days) - 20, len(days)), 8))
    for k in picks:
        d = days[k]; x = r.choice(byd[d])
        typ = _wchoice(r, INCIDENT_TYPES, [.5, .12 + (.12 if x['room'] in ('Toddlers', 'Twos') else 0), .2, .15])
        inf = r.random() > .02
        out.append(dict(date=d, time='%02d:%02d' % (r.randint(8, 16), r.choice([0, 10, 20, 30, 40, 50])), child_id=x['child_id'], child=x['child'], room=x['room'], type=typ, parent_informed=inf,
                        staff=r.choice(CLASS_STAFF), follow_up_done=(d < TODAY - day(5)) or r.random() < .35))
    return _thin([dict(incident_id='IN-%03d' % i, date=iso(x.pop('date')), **x) for i, x in enumerate(out, 1)], n)


_DRILL_EVERY = {'Fire drill': 30, 'Evacuation drill': 90, 'Lockdown drill': 120, 'Shelter drill': 120}
_DRILL_LAST = {'Fire drill': 9, 'Evacuation drill': 41, 'Lockdown drill': 77, 'Shelter drill': 101}


def drill_rows(n=None):
    r = rng('drill'); out = []; present = {}
    for x in _att():
        if x['status'] == 'Present': present[x['date']] = present.get(x['date'], 0) + 1
    for kind, every in _DRILL_EVERY.items():
        d = _last_open(TODAY - day(_DRILL_LAST[kind]))
        while d >= HISTORY_START:
            d = _last_open(d)
            if d in present:
                out.append(dict(date=d, kind=kind, minutes=r.choice([3, 4, 4, 5, 6]) if 'drill' in kind and kind != 'Shelter drill' else r.choice([5, 6, 8]), children_present=present[d],
                                staff=r.choice([OWNER, ASSISTANT_DIRECTOR, 'Camille Fontaine']), status='Done'))
            d -= day(every + r.randint(-4, 4))
    out.sort(key=lambda x: x['date'])
    return _thin([dict(drill_id='DR-%03d' % i, date=iso(x.pop('date')), **x) for i, x in enumerate(out, 1)], n)


def check_rows(n=None):
    r = rng('check'); out = []
    w = week_start(HISTORY_START) + day(7)
    while w <= week_start(TODAY):
        d = _last_open(w + day(4))
        if d <= TODAY:
            for room in ROOMS:
                for kind in CHECK_KINDS:
                    miss = d < TODAY - day(14) and r.random() < .025
                    by = 'Thandiwe Nkosi' if kind == 'Deep clean' else RM_LEAD[room]
                    out.append(dict(date=iso(d), week=iso(w), month=iso(_ms(d)), room=room, kind=kind, status='Missed' if miss else 'Done', done_by=by, minutes=0 if miss else r.randint(15, 70)))
        w += day(7)
    return _thin([dict(check_id='CK-%04d' % i, **x) for i, x in enumerate(out, 1)], n)


RM_LEAD = {'Infants': 'Aaliyah Rahman', 'Toddlers': 'Mateusz Kowalczyk', 'Twos': 'Ngozi Eze', 'Preschool': 'Camille Fontaine', 'School-age': 'Sofia Petrova'}


# ------------------------------------------------------------------ staff: renewals, training, exits, pay
_RENEW_CYCLE = {'Background check': 1095, 'First aid course': 1095, 'Safeguarding course': 730, 'Food hygiene course': 1095, 'Liability insurance': 365, 'Building inspection': 365,
                'Licence renewal': 730, 'Fire safety service': 365}
_RENEW_COST = {'Background check': 45.0, 'First aid course': 95.0, 'Safeguarding course': 60.0, 'Food hygiene course': 55.0, 'Liability insurance': 1480.0, 'Building inspection': 280.0,
               'Licence renewal': 320.0, 'Fire safety service': 210.0}


def renewal_rows(n=None):
    r = rng('renew'); out = []
    holders = [(s['name'], ['Background check', 'First aid course', 'Safeguarding course'] + (['Food hygiene course'] if s['role'] == 'Cook' else [])) for s in staff if s['role'] != 'Owner-director']
    holders.append((OWNER, ['Background check', 'First aid course', 'Safeguarding course']))
    for nm in ('Centre',):
        holders.append((nm, ['Liability insurance', 'Building inspection', 'Licence renewal', 'Fire safety service']))
    fixed = {('Camille Fontaine', 'Background check'): 12, ('Hana Sato', 'First aid course'): 52, ('Centre', 'Fire safety service'): 58}
    for nm, items in holders:
        for item in items:
            cyc = _RENEW_CYCLE[item]
            nxt = fixed.get((nm, item), r.randint(70, cyc - 40))
            due = TODAY + day(nxt)
            prev = due - day(cyc)
            while prev >= HISTORY_START - day(60):
                out.append(dict(holder=nm, item=item, due_date=prev, renewed_on=prev - day(r.randint(3, 25)), cost=_RENEW_COST[item]))
                prev -= day(cyc)
            out.append(dict(holder=nm, item=item, due_date=due, renewed_on='', cost=_RENEW_COST[item]))
    out.sort(key=lambda x: (x['due_date'], x['holder']))
    return _thin([dict(renewal_id='RN-%03d' % i, holder=x['holder'], item=x['item'], due_date=iso(x['due_date']), renewed_on=iso(x['renewed_on']) if x['renewed_on'] else '', cost=x['cost'])
                  for i, x in enumerate(out, 1)], n)


_TITLES = {'Workshop': ['Positive behaviour guidance', 'Sensory play ideas', 'Early language skills'], 'Online course': ['Child development basics', 'Nutrition for young children', 'Working with families'],
           'Training day': ['Infant care refresher', 'Outdoor learning day'], 'Peer learning': ['Room leaders meet-up', 'Observation sharing session'], 'First aid course': ['Paediatric first aid']}


def training_rows(n=None):
    r = rng('cpd'); out = []
    behind = {'Zainab Khalid': .3, 'Joao Barbosa': .4, 'Luis Fernandez': .55}
    for s in staff:
        if s['role'] in ('Owner-director',) or s['team'] == 'Outside': continue
        st = max(to_date(s['start']), HISTORY_START)
        d = st + day(r.randint(20, 60))
        while d <= TODAY:
            if d.year == TODAY.year and r.random() < behind.get(s['name'], 0): d += day(70); continue
            kind = r.choice(CPD_KINDS[:4] if d.year != TODAY.year or r.random() < .7 else CPD_KINDS)
            hrs = {'Workshop': 3, 'Online course': 2, 'Training day': 6, 'Peer learning': 1.5, 'First aid course': 6}[kind]
            out.append(dict(date=_first_open(d), staff=s['name'], kind=kind, title=r.choice(_TITLES[kind]), hours=float(hrs), cost=R2(hrs * r.choice([6, 8, 10]) if kind != 'Peer learning' else 0.0)))
            d += day(r.randint(55, 120))
    # the owner-director trains too
    for k in range(10):
        out.append(dict(date=_first_open(HISTORY_START + day(40 + k * 70)), staff=OWNER, kind='Workshop', title='Leading a small setting', hours=3.0, cost=45.0))
    out.sort(key=lambda x: x['date'])
    return _thin([dict(training_id='TD-%03d' % i, date=iso(x['date']), month=iso(_ms(x['date'])), staff=x['staff'], kind=x['kind'], title=x['title'], hours=x['hours'], cost=x['cost'])
                  for i, x in enumerate(out, 1)], n)


def exit_rows(n=None):
    return _thin([dict(exit_id='XT-%02d' % i, name=f['name'], role=f['role'], started_on=f['start'], left_on=f['left'], vacancy_days=f['vacancy_days'], replace_cost=f['replace_cost'])
                  for i, f in enumerate(sorted(former_staff, key=lambda f: f['left']), 1)], n)


def pay_rows(n=None):
    out = []; byk = {}
    for x in _sh()[0]: byk.setdefault((_ms(x['date']), x['staff']), []).append(x)
    for mi in range(24):
        M1 = month_start(23 - mi); paydate = D(add_months(M1, 1).year, add_months(M1, 1).month, 5)
        st = 'Paid' if paydate <= TODAY else ('Due' if M1 != _ms(TODAY) else 'Accruing')
        for nm, p in POOL.items():
            if p['start'] > _eom(M1) or (p['end'] and p['end'] < M1): continue
            role = p['role']; rows = byk.get((M1, nm), [])
            hrs = R2(sum(x['hours'] for x in rows if x['kind'] != 'Relief' or p['pay_type'] == 'Hourly'))
            if p['pay_type'] == 'Owner draw': gross, hrs, on, typ = OWNER_DRAW, 0.0, 0.0, 'Owner draw'
            elif p['pay_type'] == 'Salary': gross = staff_by_name[nm]['monthly_salary'] * (1.03 if M1 >= D(TODAY.year, 1, 1) else 1.0); on = R2(gross * EMPLOYER_COST_PCT); typ = 'Salary'; hrs = R2(sum(x['hours'] for x in rows))
            else:
                gross = R2(sum(x['hours'] * x['rate'] for x in rows)); on = R2(gross * EMPLOYER_COST_PCT); typ = 'Hourly'
            out.append(dict(month=iso(M1), person=nm, role=role, pay_type=typ, hours=hrs, gross=R2(gross), on_costs=on, total=R2(gross + on), pay_date=iso(paydate), status=st))
    return _thin([dict(pay_id='PY-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


# ------------------------------------------------------------------ families and programs: observations, conferences, reports, messages, events, camps
TERM_START = D(TODAY.year, 9, 1) if TODAY.month >= 9 else (D(TODAY.year, 5, 1) if TODAY.month >= 5 else D(TODAY.year, 1, 1))


def observation_rows(n=None):
    r = rng('obs'); out = []
    kids = _kids()
    none_now = {c['child_id'] for c in [c for c in kids if _status(c) == 'Enrolled' and _room_at(c, TODAY) in ('Toddlers', 'Twos', 'Preschool')][::17][:3]}
    for c in kids:
        a = max(c['start'] + day(10), HISTORY_START); b = min(c['end'] or TODAY, TODAY)
        d = a
        while d <= b:
            if not (c['child_id'] in none_now and d >= TERM_START - day(14)):
                out.append(dict(date=_first_open(d), child_id=c['child_id'], child=c['child'], room=_room_at(c, d), staff=RM_LEAD[_room_at(c, d)] if _room_at(c, d) in RM_LEAD else 'Sofia Petrova',
                                kind=r.choice(OBS_KINDS)))
            d += day(r.randint(22, 44))
    out = [x for x in out if x['date'] <= LAST_OPEN]
    out.sort(key=lambda x: x['date'])
    return _thin([dict(obs_id='OB-%04d' % i, date=iso(x['date']), month=iso(_ms(x['date'])), child_id=x['child_id'], child=x['child'], room=x['room'], staff=x['staff'], kind=x['kind'])
                  for i, x in enumerate(out, 1)], n)


def conference_rows(n=None):
    r = rng('conf'); out = []
    weeks = [D(y, m, 1) for y in (TODAY.year - 1, TODAY.year) for m in (4, 11)]
    for wk in weeks:
        wk = week_start(_nth_weekday(wk.year, wk.month, 0, 3))
        for f in _families():
            for c in f['_kids']:
                if c['start'] > wk or (c['end'] and c['end'] < wk): continue
                d = wk + day(r.randint(0, 4))
                if d < HISTORY_START: continue
                stt = 'Booked' if d > TODAY else ('No-show' if r.random() < .06 else 'Held')
                if d > TODAY and r.random() < .1: continue
                out.append(dict(date=iso(d), family_id=f['family_id'], family=f['family'], child_id=c['child_id'], child=c['child'], staff=RM_LEAD.get(_room_at(c, d), 'Sofia Petrova'), status=stt,
                                slot='%02d:%02d' % (r.choice([8, 9, 10, 13, 14, 15, 16, 17]), r.choice([0, 20, 40]))))
                break
    out.sort(key=lambda x: (x['date'], x['slot']))
    return _thin([dict(conference_id='CF-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


def report_rows(n=None):
    r = rng('rep'); out = []; seen = set()
    for x in _att():
        k = (x['date'], x['room'])
        if x['status'] != 'Present' or k in seen: continue
        seen.add(k)
        late = r.random() < .05; t = r.randint(15 * 60 + 40, 17 * 60 + 30) if not late else r.randint(18 * 60 + 5, 20 * 60 + 40)
        out.append(dict(date=x['date'], room=x['room'], staff=RM_LEAD[x['room']], sent_time=_hm(t), same_day=(t <= 20 * 60), sent_next_day=(t > 20 * 60)))
    return _thin([dict(report_id='DRP-%05d' % i, date=iso(x.pop('date')), **x) for i, x in enumerate(out, 1)], n)


def parent_message_rows(n=None):
    r = rng('pm'); out = []; days = [d for d in sorted({x['date'] for x in _att()})]
    for d in r.sample(days[:-8], 420) + days[-8:]:
        f = r.choice(_families())
        if not any(c['start'] <= d and (c['end'] is None or c['end'] >= d) for c in f['_kids']): continue
        hrs = r.choice([1, 2, 3, 4, 6, 8, 20, 26]) if r.random() < .9 else r.choice([30, 44])
        out.append(dict(date=d, family_id=f['family_id'], family=f['family'], topic=_wchoice(r, MSG_TOPICS, [.25, .3, .2, .1, .15]), status='Replied', reply_hours=hrs, replied_on=d))
    out.sort(key=lambda x: x['date'])
    aw = [x for x in out if x['date'] >= TODAY - day(6)]
    for x, k in zip(aw[:5], range(5)): x['status'] = 'Awaiting reply'; x['reply_hours'] = 0; x['replied_on'] = ''
    return _thin([dict(message_id='PM-%03d' % i, date=iso(x.pop('date')), replied_on=iso(x.pop('replied_on')) if x['replied_on'] else '', **{k: v for k, v in x.items() if k != 'replied_on'})
                  for i, x in enumerate(out, 1)], n)


def event_rows(n=None):
    r = rng('evt'); out = []
    for mi in range(24):
        M1 = month_start(23 - mi)
        d = _first_open(M1 + day(24))
        if d <= TODAY: out.append(dict(date=d, kind='Newsletter', room='All rooms', invited=len([c for c in _kids() if c['start'] <= d and (c['end'] is None or c['end'] >= d)]), attended=0))
        if M1.month in (4, 11):
            w = week_start(_nth_weekday(M1.year, M1.month, 0, 3)); out.append(dict(date=w, kind='Family meeting week', room='All rooms', invited=44, attended=int(40 + r.randint(0, 4))))
        if M1.month in (3, 9): out.append(dict(date=_first_open(M1 + day(12)), kind='Open day', room='All rooms', invited=r.randint(18, 30), attended=r.randint(9, 20)))
        if M1.month in (6, 12): out.append(dict(date=_first_open(M1 + day(8)), kind='Family event', room='All rooms', invited=50, attended=r.randint(28, 42)))
    out = [x for x in out if x['date'] >= HISTORY_START]
    out.sort(key=lambda x: x['date'])
    for x in out:
        if x['kind'] == 'Newsletter': x['attended'] = int(x['invited'] * r.uniform(.62, .84))
        if x['date'] > TODAY: x['attended'] = 0
    return _thin([dict(event_id='EV-%02d' % i, date=iso(x.pop('date')), **x) for i, x in enumerate(out, 1)], n)


def program_signup_rows(n=None):
    out = []
    for wk, prog in sorted(CAMP.items()):
        if wk < HISTORY_START or wk > TODAY: continue
        nd = sum(1 for k in range(5) if is_open(wk + day(k)))
        for c in _kids():
            if c['start'] > wk + day(4) or (c['end'] and c['end'] < wk) or _room_at(c, wk) != 'School-age' or not _signed_up(c, wk): continue
            out.append(dict(week=iso(wk), program=prog, child_id=c['child_id'], child=c['child'], family_id=c['family_id'], days=nd, price_day=_price_day(prog, wk), fee=R2(nd * _price_day(prog, wk))))
    return _thin([dict(signup_id='PS-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


def program_week_rows(n=None):
    out = []; byw = {}
    for x in _sh()[0]:
        if x['room'] == 'School-age': byw[week_start(x['date'])] = byw.get(week_start(x['date']), 0.0) + x['cost']
    sg = {}
    for x in program_signup_rows(): sg.setdefault(x['week'], []).append(x)
    w = week_start(HISTORY_START) + day(7)
    while w <= week_start(TODAY):
        prog = CAMP.get(w, 'Before-after school'); nd = sum(1 for k in range(5) if is_open(w + day(k)))
        if prog == 'Before-after school':
            ch = [c for c in _kids() if c['start'] <= w + day(4) and (c['end'] is None or c['end'] >= w) and _room_at(c, w) == 'School-age']
            rev = R2(sum(_rate('School-age', _sched_at(c, w)[0], w) for c in ch)); sign = len(ch); price = R2(rev / max(1, sign) / 5.0)
        else:
            s = sg.get(iso(w), []); sign = len(s); rev = R2(sum(x['fee'] for x in s)); price = _price_day(prog, w)
        if nd and sign:
            out.append(dict(week=iso(w), month=iso(_ms(w)), program=prog, places=PRG[prog]['places'], signups=sign, days=nd, price_day=price, revenue=rev, staff_cost=R2(byw.get(w, 0.0))))
        w += day(7)
    return _thin([dict(row_id='PW-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


# ------------------------------------------------------------------ expenses, profit and loss, rooms, cash
_IMPUTED = {'Tobias Lindgren': 20.8, 'Marisol Vega': 18.5}


def expense_rows(n=None):
    def build():
        r = rng('exp'); out = []
        def add(d, cat, desc, amt, to, method='Bank transfer'):
            if HISTORY_START <= d <= TODAY: out.append(dict(date=d, category=cat, description=desc, amount=R2(amt), paid_to=to, method=method))
        meals_wk = {}
        for x in _raw('meals', _meals): meals_wk[week_start(x['date'])] = meals_wk.get(week_start(x['date']), 0.0) + x['cost']
        for mi in range(24):
            M1 = month_start(23 - mi); yr = M1.year == TODAY.year
            add(M1, 'Rent', 'Monthly rent', 4700.0 if yr else 4500.0, 'Landlord')
            add(M1 + day(14), 'Utilities', 'Power, water and heating', 470 + (190 if M1.month in (12, 1, 2) else 70 if M1.month in (3, 11) else 0) + r.randint(-40, 60), 'Utility provider', 'Direct debit')
            add(M1 + day(2), 'Insurance', 'Liability and contents cover', 285.0, 'Insurer', 'Direct debit')
            add(_last_open(_eom(M1)), 'Cleaning', 'Evening cleaning, month', 440.0 + r.randint(-15, 25), 'Thandiwe Nkosi')
            add(M1 + day(7), 'Management software', 'Attendance and billing software', 110.0, 'Software provider', 'Card')
            add(_last_open(_eom(M1) - day(2)), 'Accounting', 'Bookkeeping and payroll run', 180.0, 'Eleni Papadakis')
            add(_first_open(M1), 'Supplies and toys', 'Art supplies, toys and paper', 120 + r.randint(0, 90), 'Toy and craft shop', 'Card')
            add(_first_open(M1 + day(14)), 'Supplies and toys', 'Cleaning and kitchen supplies', 80 + r.randint(0, 80), 'Supply shop', 'Card')
            if r.random() < .65: add(_first_open(M1 + day(r.randint(3, 24))), 'Maintenance', r.choice(['Repair of a play area fence', 'Boiler check', 'Door and lock repair', 'Playground surface repair']), r.randint(60, 480), 'Dae-ho Park')
        w = week_start(HISTORY_START) + day(7)
        while w <= week_start(TODAY):
            add(_last_open(w + day(4)), 'Food and groceries', 'Weekly groceries and dairy', meals_wk.get(w, 0.0) * 1.08 + r.uniform(-8, 8), 'Rajesh Menon')
            w += day(7)
        for x in training_rows(): add(to_date(x['date']), 'Training', x['title'], x['cost'], 'Course provider', 'Card') if x['cost'] > 0 else None
        for x in renewal_rows(): add(to_date(x['renewed_on']), 'Training', x['item'], x['cost'], 'Course provider', 'Card') if x['renewed_on'] and x['holder'] != 'Centre' else None
        for x in marketing_rows(): add(to_date(x['month']) + day(2), 'Marketing', x['kind'], x['cost'], 'Print shop' if x['kind'] in ('Local flyers', 'Roadside sign') else 'Online directory provider')
        pay = {}
        for p in _acc()['payments']:
            if p['method'] in ('Autopay card', 'Autopay bank') and p['kind'] == 'Invoice': pay[_ms(p['date'])] = pay.get(_ms(p['date']), 0.0) + p['amount']
        for m, v in pay.items(): add(_last_open(_eom(m)), 'Bank and card fees', 'Autopay and card fees', v * CARD_FEE_PCT, 'Bank', 'Direct debit')
        out.sort(key=lambda x: (x['date'], x['category']))
        return out
    return _thin([dict(expense_id='EX-%04d' % i, date=iso(x['date']), month=iso(_ms(x['date'])), category=x['category'], description=x['description'], amount=x['amount'], paid_to=x['paid_to'],
                       method=x['method']) for i, x in enumerate(_raw('expenses', build), 1)], n)


def _expense_by_month():
    by = {}
    for x in _raw('expenses', lambda: None) or []: pass
    return by


def _month_tables():
    expense_rows()
    ex = _raw('expenses', lambda: [])
    pay = pay_rows()
    inv = _acc()['invoices']
    m = {}
    for k in range(24):
        M1 = month_start(23 - k); m[M1] = dict(month=M1, tuition_revenue=0.0, fee_revenue=0.0, gov_part=0.0, staff_pay=0.0, owner_pay=0.0, food=0.0, rent=0.0, other=0.0, staff_hours=0.0)
    for x in inv:
        a = m.get(_ms(x['period_start']))
        if a is None: continue
        a['tuition_revenue'] += x['tuition'] - x['discount'] + x['camp_fee']; a['fee_revenue'] += x['registration'] + x['supply_fee'] + x['drop_in'] + x['late_fees']; a['gov_part'] += x['gov_expected']
    for x in pay:
        a = m.get(to_date(x['month']))
        if a is None: continue
        if x['pay_type'] == 'Owner draw': a['owner_pay'] += x['total']
        else: a['staff_pay'] += x['total']; a['staff_hours'] += x['hours']
    for x in ex:
        a = m.get(_ms(x['date']))
        if a is None: continue
        if x['category'] == 'Food and groceries': a['food'] += x['amount']
        elif x['category'] == 'Rent': a['rent'] += x['amount']
        else: a['other'] += x['amount']
    for a in m.values():
        a['revenue'] = a['tuition_revenue'] + a['fee_revenue']; a['profit'] = a['revenue'] - a['staff_pay'] - a['owner_pay'] - a['food'] - a['rent'] - a['other']
    return m


def pnl_rows(n=None):
    out = []
    for M1, a in sorted(_raw('mt', _month_tables).items()):
        out.append(dict(month=iso(M1), tuition_revenue=R2(a['tuition_revenue']), fee_revenue=R2(a['fee_revenue']), revenue=R2(a['revenue']), government_part=R2(a['gov_part']), staff_pay=R2(a['staff_pay']),
                        owner_pay=R2(a['owner_pay']), food=R2(a['food']), rent=R2(a['rent']), other_costs=R2(a['other']), profit=R2(a['profit']), staff_hours=R2(a['staff_hours'])))
    return _thin([dict(row_id='PL-%02d' % i, **x) for i, x in enumerate(out, 1)], n)


def tax_rows(n=None):
    out = []
    for x in pnl_rows():
        M1 = to_date(x['month']); q_end = D(M1.year, ((M1.month - 1) // 3 + 1) * 3, 1); due = add_months(q_end, 1).replace(day=15)
        sa = R2(max(0.0, x['profit']) * TAX_SET_ASIDE_PCT) if M1 < _ms(TODAY) else R2(max(0.0, x['profit']) * TAX_SET_ASIDE_PCT)
        out.append(dict(month=x['month'], revenue=x['revenue'], costs=R2(x['revenue'] - x['profit']), profit=x['profit'], set_aside_pct=TAX_SET_ASIDE_PCT, set_aside=sa, due_date=iso(due),
                        paid_on=iso(due) if due <= TODAY else '', status='Paid' if due <= TODAY else ('Due' if due <= TODAY + day(45) else 'Upcoming')))
    return _thin([dict(tax_id='TX-%02d' % i, **x) for i, x in enumerate(out, 1)], n)


def cash_rows(n=None):
    expense_rows()
    ex = _raw('expenses', lambda: []); flows = {}
    for k in range(24):
        M1 = month_start(23 - k); flows[M1] = dict(month=M1, parents=0.0, government=0.0, pay_out=0.0, expenses_out=0.0, tax_out=0.0, refunds=0.0, extra=(OWNER_EXTRA if M1.month in (3, 6, 9, 12) and M1 < _ms(TODAY) else 0.0))
    for p in _acc()['payments']:
        a = flows.get(_ms(p['date']));
        if a: a['parents'] += p['amount']
    for g in _acc()['gov']:
        if g['paid_on'] and g['status'] in ('Paid', 'Short-paid'):
            a = flows.get(_ms(g['paid_on']))
            if a: a['government'] += g['received']
    for p in pay_rows():
        pd = to_date(p['pay_date']); a = flows.get(_ms(pd))
        if a is not None and pd <= TODAY: a['pay_out'] += p['total']
    for x in ex:
        a = flows.get(_ms(x['date']))
        if a: a['expenses_out'] += x['amount']
    for t in tax_rows():
        if t['paid_on']:
            pass
    qsum = {}
    for t in tax_rows(): qsum[t['due_date']] = qsum.get(t['due_date'], 0.0) + t['set_aside']
    for dd, v in qsum.items():
        if to_date(dd) <= TODAY:
            a = flows.get(_ms(to_date(dd)))
            if a: a['tax_out'] += v
    for dp in _acc()['deposits']:
        if dp['status'] == 'Refunded' and dp['settled_on']:
            a = flows.get(_ms(dp['settled_on']))
            if a: a['refunds'] += dp['amount']
    cum = 0.0; mins = 0.0; rows = []
    for M1 in sorted(flows):
        a = flows[M1]; net = a['parents'] + a['government'] - a['pay_out'] - a['expenses_out'] - a['tax_out'] - a['refunds'] - a['extra']
        cum += net; mins = min(mins, cum); rows.append((a, net, cum))
    opening = CASH_FLOOR + 2400.0 - mins
    out = []; prev = opening
    for a, net, cum in rows:
        out.append(dict(month=iso(a['month']), opening=R2(prev), parent_payments=R2(a['parents']), government_payments=R2(a['government']), pay_out=R2(a['pay_out']), expenses_out=R2(a['expenses_out']),
                        tax_set_aside=R2(a['tax_out']), deposit_refunds=R2(a['refunds']), owner_extra=R2(a['extra']), closing=R2(prev + net)))
        prev = prev + net
    out = out[-14:]
    return _thin([dict(cash_id='CS-%02d' % i, **x) for i, x in enumerate(out, 1)], n)


def bill_rows(n=None):
    r = rng('bills'); out = []
    ex = _raw('expenses', lambda: [])
    expense_rows(); ex = _raw('expenses', lambda: [])
    last = {}
    for x in ex: last.setdefault(x['category'], []).append(x)
    base = {k: R2(sum(y['amount'] for y in v[-3:]) / 3.0) for k, v in last.items() if k not in ('Food and groceries', 'Training', 'Marketing', 'Maintenance', 'Bank and card fees')}
    wk_food = R2(sum(y['amount'] for y in last['Food and groceries'][-4:]) / 4.0)
    pay_est = R2(sum(p['total'] for p in pay_rows() if p['month'] == iso(month_start(1))))
    rows = []
    for k in range(-8, 14):
        M1 = add_months(_ms(TODAY), k // 4 if False else 0)
    for mi in range(-3, 5):
        M1 = add_months(_ms(TODAY), mi)
        sched = [(M1, 'Rent', 'Landlord', base['Rent']), (M1 + day(2), 'Insurance', 'Insurer', base['Insurance']), (M1 + day(7), 'Management software', 'Software provider', base['Management software']),
                 (M1 + day(14), 'Utilities', 'Utility provider', base['Utilities']), (_last_open(_eom(M1) - day(2)), 'Accounting', 'Eleni Papadakis', base['Accounting']),
                 (_last_open(_eom(M1)), 'Cleaning', 'Thandiwe Nkosi', base['Cleaning']), (M1 + day(4), 'Payroll', 'Staff', pay_est)]
        for d, cat, to, amt in sched: rows.append((d, cat, to, amt))
    w = week_start(TODAY) - day(56)
    while w <= week_start(TODAY) + day(91):
        rows.append((_last_open(w + day(4)), 'Food and groceries', 'Rajesh Menon', wk_food)); w += day(7)
    rows = [x for x in rows if TODAY - day(56) <= x[0] <= TODAY + day(91)]
    rows.sort(key=lambda x: (x[0], x[1]))
    return _thin([dict(bill_id='BL-%03d' % i, due_date=iso(d), category=c, paid_to=t, amount=R2(a), status='Paid' if d <= TODAY else 'Upcoming') for i, (d, c, t, a) in enumerate(rows, 1)], n)


def room_month_rows(n=None):
    mt = _raw('mt', _month_tables); inv = _acc()['invoices']
    meals = {}
    for x in _raw('meals', _meals): meals[(_ms(x['date']), x['room'])] = meals.get((_ms(x['date']), x['room']), 0.0) + x['cost']
    stc = {}; kit = {}
    for x in _sh()[0]:
        k = (_ms(x['date']), x['room'])
        cost = x['cost'] if x['staff'] not in _IMPUTED else R2(x['hours'] * _IMPUTED[x['staff']] * (1 + EMPLOYER_COST_PCT))
        if x['room'] == 'Kitchen': kit[_ms(x['date'])] = kit.get(_ms(x['date']), 0.0) + cost
        else: stc[k] = stc.get(k, 0.0) + cost
    rev = {}
    for x in inv:
        M1 = _ms(x['period_start'])
        for rm, v in x['_roomnet'].items(): rev[(M1, rm)] = rev.get((M1, rm), 0.0) + v
        for rm, v in x['_roomx'].items(): rev[(M1, rm)] = rev.get((M1, rm), 0.0) + v
        if x['_roomnet']: fr = next(iter(x['_roomnet'])); rev[(M1, fr)] = rev.get((M1, fr), 0.0) + x['drop_in'] + x['late_fees']
    _W = {'Infants': 10.5, 'Toddlers': 10.5, 'Twos': 10.5, 'Preschool': 10.5, 'School-age': 3.5}
    capsum = float(sum(r_['capacity'] * _W[r_['room']] for r_ in rooms)); out = []
    allmeal = {}
    for (m_, rm), v in meals.items(): allmeal[m_] = allmeal.get(m_, 0.0) + v
    imp_all = {}
    for x in _sh()[0]:
        if x['staff'] in _IMPUTED: imp_all[_ms(x['date'])] = imp_all.get(_ms(x['date']), 0.0) + x['hours'] * _IMPUTED[x['staff']] * (1 + EMPLOYER_COST_PCT)
    for M1, a in sorted(mt.items()):
        nxt = add_months(M1, 1)
        shared = a['staff_pay'] + a['owner_pay'] + a['rent'] + a['other'] - sum(stc.get((M1, r_['room']), 0.0) for r_ in rooms) - kit.get(M1, 0.0)
        for rm in rooms:
            r_ = rm['room']; en = sum(1 for c in _kids() if c['start'] < nxt and (c['end'] is None or c['end'] >= M1) and _room_at(c, nxt - day(1)) == r_ and c['start'] <= _eom(M1))
            share = (meals.get((M1, r_), 0.0) / allmeal[M1]) if allmeal.get(M1) else 0.0
            food = R2(meals.get((M1, r_), 0.0) * 1.08); kitchen = R2(kit.get(M1, 0.0) * share)
            direct = R2(stc.get((M1, r_), 0.0)); over = R2(shared * rm['capacity'] * _W[r_] / capsum)
            revenue = R2(rev.get((M1, r_), 0.0)); cost = R2(direct + food + kitchen + over)
            out.append(dict(month=iso(M1), room=r_, capacity=rm['capacity'], enrolled=en, occupancy=R2(en / float(rm['capacity'])), revenue=revenue, staff_cost=direct, food_cost=R2(food + kitchen),
                            overhead_share=over, cost=cost, profit=R2(revenue - cost)))
    return _thin([dict(row_id='RU-%03d' % i, **x) for i, x in enumerate(out, 1)], n)


def room_profit(room, months=12):
    rows = [x for x in room_month_rows() if x['room'] == room and to_date(x['month']) >= month_start(months) and to_date(x['month']) < _ms(TODAY)]
    return dict(profit=R2(sum(x['profit'] for x in rows)), revenue=R2(sum(x['revenue'] for x in rows)), cost=R2(sum(x['cost'] for x in rows)), months=len(rows))


# ------------------------------------------------------------------ story
def story():
    """ids of the story rows: ratio_room ratio_date ratio_hour ratio_gap ratio_children ratio_needed ratio_present (a room one staff member short in one hour of one day last week);
    overdue_family (+ overdue_family_id, overdue_invoice (the oldest), overdue_invoices, overdue_balance, overdue_days); gov_family (+ gov_family_id, gov_month, gov_expected, gov_received, gov_gap, gov_id);
    renewal_holder (+ renewal_id, renewal_item, renewal_date, renewal_days); losing_room (+ losing_profit, losing_occupancy, losing_enrolled); health_child (+ health_child_id, health_record,
    health_due, health_days_past)"""
    out = {}
    sh = ratio_short_hours(30); assert len(sh) == 1, sh
    x = sh[0]
    out.update(ratio_room=x['room'], ratio_date=iso(x['date']), ratio_hour='%02d:00' % x['hour'], ratio_gap=x['gap'], ratio_children=x['children'], ratio_needed=x['needed'], ratio_present=x['present'])
    inv = [x for x in _acc()['invoices'] if x['_story']]
    out['overdue_family'] = inv[0]['family']; out['overdue_family_id'] = inv[0]['family_id']; out['overdue_invoice'] = inv[0]['invoice_id']; out['overdue_invoices'] = [x['invoice_id'] for x in inv]
    out['overdue_balance'] = R2(sum(x['parent_due'] for x in inv)); out['overdue_days'] = (TODAY - inv[0]['due_date']).days
    g = [x for x in _acc()['gov'] if x['_story']][0]
    out.update(gov_family=g['family'], gov_family_id=g['family_id'], gov_month=iso(g['month']), gov_expected=g['expected'], gov_received=g['received'], gov_gap=R2(g['expected'] - g['received']), gov_id=g['gov_id'])
    rn = [x for x in renewal_rows() if x['holder'] == 'Camille Fontaine' and x['item'] == 'Background check' and x['renewed_on'] == ''][0]
    out.update(renewal_holder=rn['holder'], renewal_id=rn['renewal_id'], renewal_item=rn['item'], renewal_date=rn['due_date'], renewal_days=(to_date(rn['due_date']) - TODAY).days)
    rp = room_profit('Infants'); en = [x for x in room_month_rows() if x['room'] == 'Infants'][-2]
    out.update(losing_room='Infants', losing_profit=rp['profit'], losing_occupancy=en['occupancy'], losing_enrolled=en['enrolled'])
    h = [x for x in health_rows() if x['status'] == 'Due' and to_date(x['due_date']) < TODAY][0]
    out.update(health_child=h['child'], health_child_id=h['child_id'], health_record=h['record'], health_due=h['due_date'], health_days_past=(TODAY - to_date(h['due_date'])).days)
    return out


_GENS = ['child_rows', 'family_rows', 'booking_rows', 'attendance_rows', 'late_fee_rows', 'shift_rows', 'ratio_hour_rows', 'invoice_rows', 'payment_rows', 'gov_payment_rows', 'deposit_rows',
         'statement_rows', 'ageing_rows', 'ageing_month_rows', 'promise_rows', 'plan_rows', 'enquiry_rows', 'tour_rows', 'waitlist_rows', 'marketing_rows', 'meal_rows', 'menu_rows', 'health_rows',
         'incident_rows', 'drill_rows', 'check_rows', 'renewal_rows', 'training_rows', 'exit_rows', 'pay_rows', 'observation_rows', 'conference_rows', 'report_rows', 'parent_message_rows',
         'event_rows', 'program_week_rows', 'program_signup_rows', 'room_month_rows', 'pnl_rows', 'expense_rows', 'bill_rows', 'cash_rows', 'tax_rows', 'closure_rows']


def _digest():
    h = hashlib.md5()
    for nm in _GENS: h.update(repr(globals()[nm]()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); S = story(); G = {nm: globals()[nm]() for nm in _GENS}; G['team'] = team; G['rooms'] = rooms; G['rates'] = rates; G['fees'] = fees; G['programs'] = programs
    print('team', len(team), 'rooms', len(rooms), 'rates', len(rates), 'fees', len(fees), 'programs', len(programs))
    print(' '.join('%s %d' % (nm.replace('_rows', ''), len(v)) for nm, v in G.items()))
    ids = {'child_rows': 'child_id', 'family_rows': 'family_id', 'booking_rows': 'booking_id', 'attendance_rows': 'attendance_id', 'late_fee_rows': 'fee_id', 'shift_rows': 'shift_id',
           'ratio_hour_rows': 'slot_id', 'invoice_rows': 'invoice_id', 'payment_rows': 'payment_id', 'gov_payment_rows': 'gov_id', 'deposit_rows': 'deposit_id', 'statement_rows': 'statement_id',
           'ageing_rows': 'ageing_id', 'ageing_month_rows': 'row_id', 'promise_rows': 'promise_id', 'plan_rows': 'plan_id', 'enquiry_rows': 'enquiry_id', 'tour_rows': 'tour_id',
           'waitlist_rows': 'wait_id', 'marketing_rows': 'campaign_id', 'meal_rows': 'meal_id', 'menu_rows': 'menu_id', 'health_rows': 'record_id', 'incident_rows': 'incident_id',
           'drill_rows': 'drill_id', 'check_rows': 'check_id', 'renewal_rows': 'renewal_id', 'training_rows': 'training_id', 'exit_rows': 'exit_id', 'pay_rows': 'pay_id',
           'observation_rows': 'obs_id', 'conference_rows': 'conference_id', 'report_rows': 'report_id', 'parent_message_rows': 'message_id', 'event_rows': 'event_id',
           'program_week_rows': 'row_id', 'program_signup_rows': 'signup_id', 'room_month_rows': 'row_id', 'pnl_rows': 'row_id', 'expense_rows': 'expense_id', 'bill_rows': 'bill_id',
           'cash_rows': 'cash_id', 'tax_rows': 'tax_id', 'closure_rows': 'closure_id', 'team': 'staff_id', 'rooms': 'room_id', 'rates': 'rate_id'}
    for nm, k in ids.items(): assert len({x[k] for x in G[nm]}) == len(G[nm]), nm
    assert len({c['child'] for c in G['child_rows']}) == len(G['child_rows']), 'child names unique'
    chk = [('child_rows', 'room', ROOMS), ('child_rows', 'schedule', SCHEDULES), ('child_rows', 'status', CHILD_STATUS), ('child_rows', 'discount', DISCOUNTS), ('attendance_rows', 'status', ATT_STATUS),
           ('attendance_rows', 'room', ROOMS), ('attendance_rows', 'weekday', WEEKDAYS), ('family_rows', 'cycle', BILL_CYCLES), ('family_rows', 'pay_method', PAY_METHODS),
           ('invoice_rows', 'status', INVOICE_STATUS), ('invoice_rows', 'cycle', BILL_CYCLES), ('payment_rows', 'kind', PAYMENT_KINDS), ('payment_rows', 'method', PAY_METHODS),
           ('deposit_rows', 'status', DEPOSIT_STATUS), ('gov_payment_rows', 'status', GOV_STATUS), ('enquiry_rows', 'source', SOURCES), ('enquiry_rows', 'status', ENQUIRY_STATUS),
           ('enquiry_rows', 'reason', LOST_REASONS), ('tour_rows', 'status', TOUR_STATUS), ('waitlist_rows', 'status', WAIT_STATUS), ('waitlist_rows', 'priority', PRIORITIES),
           ('waitlist_rows', 'room', ROOMS), ('enquiry_rows', 'want_room', ROOMS), ('marketing_rows', 'kind', MARKETING_KINDS), ('meal_rows', 'meal', MEALS), ('meal_rows', 'room', ROOMS),
           ('health_rows', 'record', HEALTH_RECORDS), ('health_rows', 'status', HEALTH_STATUS), ('incident_rows', 'type', INCIDENT_TYPES), ('incident_rows', 'room', ROOMS),
           ('drill_rows', 'kind', DRILL_KINDS), ('check_rows', 'kind', CHECK_KINDS), ('check_rows', 'status', CHECK_STATUS), ('check_rows', 'room', ROOMS), ('renewal_rows', 'item', RENEWAL_KINDS),
           ('training_rows', 'kind', CPD_KINDS), ('pay_rows', 'status', PAY_STATUS), ('pay_rows', 'role', PAY_ROLES), ('pay_rows', 'pay_type', ['Owner draw', 'Salary', 'Hourly']),
           ('observation_rows', 'kind', OBS_KINDS), ('conference_rows', 'status', CONF_STATUS), ('parent_message_rows', 'topic', MSG_TOPICS), ('parent_message_rows', 'status', MSG_STATUS),
           ('event_rows', 'kind', EVENT_KINDS), ('program_week_rows', 'program', PROGRAMS), ('room_month_rows', 'room', ROOMS), ('shift_rows', 'kind', SHIFT_KINDS),
           ('expense_rows', 'category', EXPENSE_CATEGORIES), ('ratio_hour_rows', 'room', ROOMS), ('booking_rows', 'weekday', WEEKDAYS), ('team', 'role', ROLES), ('team', 'team', TEAMS),
           ('team', 'pay_type', PAY_TYPES)]
    for nm, col, vals in chk:
        got = {x[col] for x in G[nm]}; miss = [v for v in vals if v not in got]
        assert not miss, (nm, col, miss)
        extra = {g for g in got if g not in vals and g != ''}; assert not extra, (nm, col, extra)
    for L in (ROLES, TEAMS, ROOMS, SCHEDULES, CHILD_STATUS, ATT_STATUS, PAY_METHODS, INVOICE_STATUS, PAYMENT_KINDS, DEPOSIT_STATUS, GOV_STATUS, SOURCES, ENQUIRY_STATUS, LOST_REASONS, TOUR_STATUS,
              WAIT_STATUS, MEALS, HEALTH_RECORDS, HEALTH_STATUS, INCIDENT_TYPES, DRILL_KINDS, CHECK_KINDS, RENEWAL_KINDS, CPD_KINDS, OBS_KINDS, EVENT_KINDS, MSG_TOPICS, PROGRAMS, MARKETING_KINDS,
              EXPENSE_CATEGORIES, SHIFT_KINDS):
        for k, _ in pairs(L): assert len(k) <= 21, k
    ms = iso(month_start(0)); t30 = ago(30); td = iso(TODAY)
    def cur(nm, col, lo=1, t=ms):
        n_ = sum(1 for x in G[nm] if x[col] and t <= x[col] <= td); assert n_ >= lo, (nm, col, n_); return n_
    print('this month:', 'attendance', cur('attendance_rows', 'date', 100), 'shifts', cur('shift_rows', 'date', 50), 'invoices', cur('invoice_rows', 'issued_on', 20), 'payments', cur('payment_rows', 'date', 20),
          'enquiries', cur('enquiry_rows', 'date', 5), 'tours', cur('tour_rows', 'date', 3), 'meals', cur('meal_rows', 'date', 100), 'incidents', cur('incident_rows', 'date', 1),
          'expenses', cur('expense_rows', 'date', 5), 'observations', cur('observation_rows', 'date', 5), 'reports', cur('report_rows', 'date', 20), 'late fees', cur('late_fee_rows', 'date', 1),
          'messages', cur('parent_message_rows', 'date', 3), 'gov paid', cur('gov_payment_rows', 'paid_on', 1), 'training', cur('training_rows', 'date', 0))
    print('last 30 days:', 'incidents', cur('incident_rows', 'date', 3, t30), 'enquiries', cur('enquiry_rows', 'date', 8, t30), 'late fees', cur('late_fee_rows', 'date', 5, t30), 'training', cur('training_rows', 'date', 1, t30),
          'drills', cur('drill_rows', 'date', 1, t30), 'checks', cur('check_rows', 'date', 5, t30), 'deposits', cur('deposit_rows', 'received_on', 0, t30), 'payments', cur('payment_rows', 'date', 40, t30))
    en = [c for c in G['child_rows'] if c['status'] == 'Enrolled']; print('children', len(G['child_rows']), 'enrolled', len(en), {r: sum(1 for c in en if c['room'] == r) for r in ROOMS})
    print('statuses', {s: sum(1 for c in G['child_rows'] if c['status'] == s) for s in CHILD_STATUS}, 'families', len(G['family_rows']))
    ps = G['pnl_rows']; print('monthly profit', [round(x['profit']) for x in ps[:-1]]); assert all(x['profit'] > -100 for x in ps[:-1]), 'profit'
    cr = G['cash_rows']; print('cash closing', [round(x['closing']) for x in cr]); assert min(x['closing'] for x in cr) > CASH_FLOOR
    rp = {r: room_profit(r)['profit'] for r in ROOMS}; print('room profit 12m', {k: round(v) for k, v in rp.items()})
    assert rp['Infants'] < 0 and all(v > 0 for k, v in rp.items() if k != 'Infants'), rp
    late = [x for x in G['invoice_rows'] if x['status'] in ('Unpaid', 'Part paid') and to_date(x['due_date']) < TODAY - day(42)]
    assert [x['invoice_id'] for x in late] == [S['overdue_invoice']] and S['overdue_days'] >= 42 and len(S['overdue_invoices']) == 3, (late, S)
    gs = [x for x in G['gov_payment_rows'] if x['status'] == 'Short-paid']; assert [x['gov_id'] for x in gs] == [S['gov_id']]
    rn = [x for x in G['renewal_rows'] if x['renewed_on'] == '' and x['due_date'] <= ahead(45)]; assert [x['renewal_id'] for x in rn] == [S['renewal_id']] and S['renewal_days'] == 12, rn
    hp = [x for x in G['health_rows'] if x['status'] != 'On file' and x['due_date'] < td and x['status'] == 'Due']; assert len(hp) == 1, hp
    assert all(x['gap'] <= 0 for x in G['ratio_hour_rows'] if x['date'] >= ago(30) and x['room'] != S['ratio_room']) and len(ratio_short_hours(30)) == 1
    bad = [x for x in G['meal_rows'] if x['served'] > x['children_present']]; print('meal days failing', len(bad)); assert len(bad) >= 1 and all(x['date'] < ago(60) for x in bad), [x['date'] for x in bad]
    print('waiting', sum(1 for x in G['waitlist_rows'] if x['status'] in ('Waiting', 'Offered')), 'by room', {r: sum(1 for x in G['waitlist_rows'] if x['status'] in ('Waiting', 'Offered') and x['room'] == r) for r in ROOMS})
    print('story', S)
    d1 = _digest(); _CACHE.clear()
    for nm in reversed(_GENS): globals()[nm]()
    d2 = _digest(); assert d1 == d2, (d1, d2)
    print('digest', d1, 'secs', round(time.time() - t0, 1))
