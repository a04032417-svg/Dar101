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

Money model: weekly rate by room and schedule (rate card, raised about 4% on 1 January of this year); invoice tuition = rate x weeks billed (a week or 52/12 of a week) for the
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
OWNER_DRAW = 3600.0
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
RENEWAL_KINDS = ['Background check', 'First aid course', 'Child protection course', 'Food hygiene course', 'Liability insurance', 'Building inspection', 'Licence renewal',
                 'Fire safety service']
CPD_KINDS = ['Workshop', 'Online course', 'Training day', 'Peer learning', 'First aid course']
PAY_STATUS = ['Paid', 'Due', 'Accruing']
OBS_KINDS = ['Observation', 'Portfolio entry']
CONF_STATUS = ['Held', 'Booked', 'No-show']
EVENT_KINDS = ['Newsletter', 'Parent conference week', 'Open day', 'Family event']
MSG_TOPICS = ['Billing', 'Schedule', 'Pickup', 'Health status', 'General']
MSG_STATUS = ['Replied', 'Awaiting reply']
PROGRAMS = ['Before and after school', 'Summer camp', 'Holiday camp']
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
          ('CC-03', 'Aaliyah Rahman', 'Bangladesh', 'Lead teacher', 'Classroom', 'Hourly', 40, 0, 21.0, 'Infants', 1500),
          ('CC-04', 'Mateusz Kowalczyk', 'Poland', 'Lead teacher', 'Classroom', 'Hourly', 40, 0, 21.0, 'Toddlers', 1250),
          ('CC-05', 'Ngozi Eze', 'Nigeria', 'Lead teacher', 'Classroom', 'Hourly', 40, 0, 21.0, 'Twos', 300),
          ('CC-06', 'Camille Fontaine', 'France', 'Lead teacher', 'Classroom', 'Hourly', 40, 0, 22.0, 'Preschool', 1100),
          ('CC-07', 'Luis Fernandez', 'Mexico', 'Assistant', 'Classroom', 'Hourly', 38, 0, 16.5, 'Infants', 800),
          ('CC-08', 'Hana Sato', 'Japan', 'Assistant', 'Classroom', 'Hourly', 38, 0, 16.5, 'Toddlers', 640),
          ('CC-09', 'Zainab Khalid', 'Pakistan', 'Assistant', 'Classroom', 'Hourly', 38, 0, 16.0, 'Twos and Preschool', 140),
          ('CC-10', 'Ibrahim Diallo', 'Senegal', 'Cook', 'Kitchen', 'Hourly', 30, 0, 18.0, 'Kitchen', 460),
          ('CC-11', 'Sofia Petrova', 'Bulgaria', 'Floater', 'Classroom', 'Hourly', 25, 0, 16.0, 'Relief and school-age', 700),
          ('CC-12', 'Joao Barbosa', 'Brazil', 'Floater', 'Classroom', 'Hourly', 25, 0, 16.0, 'Relief and school-age', 230)]
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
# Aisha left before the history window shows 24 months: she is kept so the exit list has 6 rows over about 20 months

# rooms: id, name, age from, age to (months, to is exclusive), capacity, children per staff, minimum staff when 3+ children
_RM = [('RM-01', 'Infants', 3, 15, 8, 4, 2), ('RM-02', 'Toddlers', 15, 27, 12, 6, 1), ('RM-03', 'Twos', 27, 39, 14, 8, 1), ('RM-04', 'Preschool', 39, 60, 20, 10, 1),
       ('RM-05', 'School-age', 60, 132, 16, 12, 1)]
rooms = [dict(room_id=a, room=b, age_from=lo, age_to=hi, age_band='%d-%d months' % (lo, hi - 1) if b != 'School-age' else '5 years and over', capacity=cap, ratio=rt, min_staff=ms)
         for a, b, lo, hi, cap, rt, ms in _RM]
RM = {r['room']: r for r in rooms}

# weekly rate by room for 5 full days (this year) and the factor of each schedule; School-age has its own card
_FULL = {'Infants': 372.0, 'Toddlers': 330.0, 'Twos': 302.0, 'Preschool': 275.0}
_FACT = {'5 full days': 1.0, '3 full days': 0.68, '2 full days': 0.46, '5 half days': 0.62, '3 half days': 0.40}
_SCH_RATE = {'5 full days': 235.0, '3 full days': 160.0, '2 full days': 112.0, '5 half days': 120.0, '3 half days': 78.0}
_SCH_DAYS = {'5 full days': 5, '3 full days': 3, '2 full days': 2, '5 half days': 5, '3 half days': 3}
_SCH_HRS = {'5 full days': 9.0, '3 full days': 9.0, '2 full days': 9.0, '5 half days': 5.0, '3 half days': 5.0}
rates = []
for _i, _r in enumerate(ROOMS):
    for _s in SCHEDULES:
        w = _SCH_RATE[_s] if _r == 'School-age' else round(_FULL[_r] * _FACT[_s] / 1.0)
        ly = round(w / 1.04)
        rates.append(dict(rate_id='RT-%02d' % (len(rates) + 1), room=_r, schedule=_s, weekly_rate=float(w), last_year_rate=float(ly), days=_SCH_DAYS[_s], hours_day=_SCH_HRS[_s],
                          day_rate=R2(w / _SCH_DAYS[_s])))
RATE = {(x['room'], x['schedule']): x for x in rates}
fees = [dict(fee='Registration fee', amount=REG_FEE, rule='Once at enrolment; last year 130'),
        dict(fee='Supply fee', amount=SUPPLY_FEE, rule='Each September per child; last year 80'),
        dict(fee='Late pickup fee', amount=LATE_FEE_PER_MIN, rule='Per minute after closing time plus the grace'),
        dict(fee='Drop-in surcharge', amount=DROP_IN_SURCHARGE, rule='Share added to the day rate of an extra day'),
        dict(fee='Deposit', amount=1.0, rule='One week of tuition, applied to the last month')]
programs = [dict(program='Before and after school', places=16, price_day=22.0), dict(program='Summer camp', places=18, price_day=46.0), dict(program='Holiday camp', places=16, price_day=42.0)]
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
        if r0.random() < .006: old_shorts.add(d)
    for d in opens:
        busy = {}                                    # name -> list of (start, end)
        hrs_day = {}
        def can(nm, a, b):
            p = POOL.get(nm)
            if not p or d < p['start'] or (p['end'] and d > p['end']) or _away(nm, d): return False
            if any(not (b <= x or a >= y) for x, y in busy.get(nm, [])): return False
            return hrs_day.get(nm, 0) + (b - a) <= (9.5 if nm in _MGMT else 10.5)
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
            if room != 'School-age' and (d == sd_pick and room == 'Toddlers' or d in old_shorts and room == r0.choice(['Toddlers', 'Twos', 'Preschool'])):
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
            rate = rate if x['date'] >= D(TODAY.year, 1, 1) else R2(rate / 1.04)
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
