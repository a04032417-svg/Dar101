"""Therapy private practice suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (one cached world is built on first use). The demo business is "Cedar Bridge Therapy Group"
(fictional): a small group practice of talking therapists and counsellors run by an owner-clinician (Amira Lindqvist, TH-01) with 2 employed clinicians (TH-02 Daniel Okoye,
TH-03 Sofia Marchetti, on salary), 2 contract clinicians paid a share of each session fee (TH-04 Kenji Watanabe 60%, TH-05 Priya Raman 65%, speech and behaviour therapy, joined
about 16 months ago), 1 supervised associate paid per session (TH-06 Lucas Moreau, joined about 10 months ago) and a front-desk and billing coordinator (TH-07 Grace Mensah, hourly),
plus 5 outside contacts (accountant, external clinical supervisor, IT support, landlord, cleaner; TH-08..TH-12). 5 therapy rooms (Garden, Willow, Family, Play and Quiet Room) plus
online sessions. Individual, couples, family and child sessions plus speech and behaviour therapy: about 450 sessions a month now (fewer two years ago), about 11,000 session rows over
~2 years (oldest first), ~1,500 enquiries, ~950 clients, ~2,500 third-party payer claims, ~3,000 monthly client invoices. One generic currency; every date is relative to the build day.

Money model: a session has a list fee by service (raised about 5% on 1 January of this year; Behaviour therapy was never raised). Fee types: Standard (the list fee), Sliding scale
(a share of the fee, 0.6 / 0.7 / 0.8), Package (6 or 10 prepaid sessions at 5% or 10% off, the session draws one credit), Third-party payer (the payer pays its share of the fee minus
a fixed client co-pay; 'Payer A'..'Payer D', never a real name). Late cancels (under 24 hours) and no-shows are charged LATE_FEE_PCT (50%) of the fee to the client, about a third of
them waived. charge = what the practice bills for the session (payer_amount + client_amount). Clinician pay per session: owner 0 (owner draw), salaried clinicians their monthly
salary plus employer costs (12%) spread over their attended sessions, contract clinicians split_pct x charge, the associate 45 per attended session. Pay for a month is paid on the 10th of the next month (the associate's on the 20th, after the supervision log is checked). room_cost (ROOM_COST_HOUR per
hour of room time, in person only) and other_cost (admin per booked session, materials, claim admin) are ALLOCATIONS used only for profit per service type and per clinician; the
monthly profit and loss uses pay rows and expenses instead. Client invoices: one per client per month for the client's share (not package sessions), issued on the 1st of the next
month, due INVOICE_DAYS (14) later; a new self-pay client pays a deposit of 50 that is applied to the first invoice. Payer claims: one per attended payer session, submitted 1-6 days
later, paid, partly paid, denied (then resubmitted or written off). Reporting month = month of the session for revenue, month of the payment for cash.

Story rows (ids from story(), never hard-coded): losing_service (Behaviour therapy loses money over the last 12 months after contractor pay, room time, materials and admin),
overdue_invoice (a self-pay client with three unpaid monthly invoices, the oldest 6+ weeks past due), denied_claim (four claims of one payer client denied 'Needs pre-approval' 6+ weeks
ago and never resubmitted), overbooked_clinician (Sofia Marchetti booked 31 sessions next week against a cap of 25), late_notes_clinician (the associate has 7+ session notes overdue),
renewal_due (a contract clinician's liability insurance ends in 12 days and is not renewed).

Exports
  constants: COMPANY SUITE OWNER COORDINATOR ASSOCIATE SUPERVISOR HISTORY_START HISTORY_DAYS ROOM_COST_HOUR ADMIN_COST CLAIM_ADMIN LATE_FEE_PCT LATE_CANCEL_HOURS NOTE_DUE_DAYS
             INVOICE_DAYS CARD_FEE_PCT EMPLOYER_COST_PCT OWNER_DRAW TAX_SET_ASIDE_PCT CE_TARGET_HOURS SUPERVISION_RATIO REVIEW_EVERY_DAYS DEPOSIT CASH_FLOOR ASSOCIATE_RATE
  dates: TODAY iso ago ahead to_date month_start add_months months14() week_start; helpers pairs first_name fake_phone fake_email rng
  lists: ROLES TEAMS PAY_TYPES YESNO CLIENT_TYPES SERVICES FORMATS SESSION_STATUS CANCEL_REASONS FREQUENCIES FEE_TYPES PAYERS CLAIM_STATUS DENIAL_REASONS CLIENT_STATUS
         ENQUIRY_STATUS ENQUIRY_REASONS REFERRAL_SOURCES CONTACT_METHODS REFERRER_KINDS WAIT_STATUS PRIORITIES ROOMS ROOM_KINDS PAYMENT_METHODS PAYMENT_KINDS INVOICE_STATUS
         PLAN_STATUS PACKAGE_KINDS PACKAGE_STATUS DEPOSIT_STATUS OUTCOME_POINTS DISCHARGE_REASONS REFERRED_TO SUPERVISION_KINDS CE_KINDS RENEWAL_KINDS GROUP_PROGRAMS GROUP_STATUS
         SIGNUP_STATUS MARKETING_KINDS EXPENSE_CATEGORIES PAY_STATUS TAX_STATUS SUBLET_STATUS WEEKDAYS HOLDERS
         WORKDAYS (Monday-Saturday) SESSION_SERVICES (the 9 session services) PAY_KINDS SLOT_STATUS ABSENCE_KINDS
  names: CLINICIANS (6, for a clinician list) STAFF_NAMES (7 staff) PAID_STAFF (6, pay rows) CONTRACTORS ROOM_NAMES (5 rooms, no Online)
  people and reference: staff (7), contacts (5), team (12), services (10), payers (4), rooms (5), referrers (24), tenants (3), programs (6)
  generators (fresh lists of dicts, oldest first; n= thins a long list but keeps the most recent rows; optional dates are '' when blank):
    slot_rows (diary: this week and the next 5) skill_rows (new-client matching rules) absence_rows client_rows enquiry_rows waitlist_rows session_rows claim_rows invoice_rows payment_rows package_rows deposit_rows payment_plan_rows client_statement_rows plan_review_rows
    outcome_rows discharge_rows supervision_rows ce_rows renewal_rows clinician_pay_rows clinician_month_rows service_month_rows room_month_rows group_rows group_signup_rows
    sublet_rows marketing_rows expense_rows tax_rows cash_rows
  helpers: service_profit(service, months=12) clinician_week_counts(week_iso) story()
Lesson: money cells are plain amounts; optional dates (note_done_on, paid_on, denied_on, resubmitted_on, discharge_date, reviewed_on, renewed_on) are '' when blank: wrap lookups with
IF(x=0,"",x). Links hold NAMES (client, clinician, service, room, payer) or ids (session SE-00001, client CL-0001, invoice IV-0001, claim PC-0001).
Words: no diagnosis, no note content, no treatment advice: notes are a done date and an on-time flag; the outcome score is a plain number (0-40, lower is better) at intake and review.
"""
import datetime as dt
import calendar
import random
import hashlib
import math

COMPANY = 'Cedar Bridge Therapy Group'
SUITE = 'fx-20261115-therapy-practice'
OWNER = 'Amira Lindqvist'
COORDINATOR = 'Grace Mensah'
ASSOCIATE = 'Lucas Moreau'
SUPERVISOR = 'Helena Novak'
TODAY = dt.date.today()
D = dt.date

ROOM_COST_HOUR = 12.0        # rent, cleaning and power per hour of room time used
ADMIN_COST = 6.0             # booking, reminders and billing per booked session
CLAIM_ADMIN = 4.0            # extra admin per payer claim
LATE_FEE_PCT = 0.5           # share of the fee charged for a late cancel or a no-show
LATE_CANCEL_HOURS = 24
NOTE_DUE_DAYS = 2            # practice rule: a session note is done within 2 days
INVOICE_DAYS = 14
CARD_FEE_PCT = 0.025
EMPLOYER_COST_PCT = 0.12
OWNER_DRAW = 7000.0
TAX_SET_ASIDE_PCT = 0.25
CE_TARGET_HOURS = 20         # continuing-education hours wanted per clinician per year (check your own local rules)
SUPERVISION_RATIO = 10       # client sessions per supervision hour wanted for the associate (practice rule)
REVIEW_EVERY_DAYS = 90       # treatment-plan review interval
DEPOSIT = 50.0
CASH_FLOOR = 20000.0
ASSOCIATE_RATE = 45.0
FUTURE_WEEKS = 6


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
def rng(tag=''): return random.Random('th-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


HISTORY_START = month_start(23)
HISTORY_DAYS = (TODAY - HISTORY_START).days

# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Owner clinician', 'Clinician', 'Contract clinician', 'Associate', 'Practice coordinator', 'Accountant', 'Clinical supervisor', 'IT support', 'Landlord', 'Cleaner']
TEAMS = ['Management', 'Clinical', 'Front desk', 'Outside']
PAY_TYPES = ['Owner draw', 'Salary', 'Percentage split', 'Per session', 'Hourly', 'Invoice']
YESNO = ['Yes', 'No']
CLIENT_TYPES = ['Adult', 'Couple', 'Family', 'Child', 'Young person']
SERVICES = ['Intake assessment', 'Individual session', 'Extended individual', 'Couples session', 'Family session', 'Child session', 'Speech therapy', 'Behaviour therapy',
            'Review session', 'Group program']
FORMATS = ['In person', 'Online', 'Phone']
SESSION_STATUS = ['Scheduled', 'Attended', 'Cancelled', 'Late cancel', 'No-show']
CANCEL_REASONS = ['Illness', 'Work clash', 'Travel', 'Childcare', 'Forgot', 'Transport', 'Clinician absence']
FREQUENCIES = ['Weekly', 'Fortnightly', 'Monthly']
FEE_TYPES = ['Standard', 'Sliding scale', 'Package', 'Third-party payer']
PAYERS = ['Payer A', 'Payer B', 'Payer C', 'Payer D']
CLAIM_STATUS = ['Submitted', 'Paid', 'Partly paid', 'Denied', 'Resubmitted', 'Written off']
DENIAL_REASONS = ['Missing details', 'Not covered', 'Limit reached', 'Late submission', 'Duplicate claim', 'Needs pre-approval']
CLIENT_STATUS = ['Booked', 'Active', 'On hold', 'Discharged', 'Referred out']
ENQUIRY_STATUS = ['New', 'Screening booked', 'Waiting list', 'Booked', 'Referred elsewhere', 'No reply', 'Declined']
ENQUIRY_REASONS = ['Not a fit', 'Service not offered', 'Fees', 'Timing', 'No reply', 'Waited too long', 'Went elsewhere']
REFERRAL_SOURCES = ['Doctor referral', 'School referral', 'Other clinician', 'Employer program', 'Past client', 'Friend or family', 'Online directory', 'Practice website',
                    'Workshop or talk']
CONTACT_METHODS = ['Phone', 'Email', 'Website form', 'Walk-in']
REFERRER_KINDS = ['Family doctor', 'School staff', 'Other clinician', 'Employer contact', 'Community worker']
WAIT_STATUS = ['Waiting', 'Offered', 'Started', 'Withdrawn']
PRIORITIES = ['High', 'Normal', 'Low']
ROOMS = ['Garden Room', 'Willow Room', 'Family Room', 'Play Room', 'Quiet Room', 'Online']
ROOM_KINDS = ['Adult room', 'Family room', 'Child room']
PAYMENT_METHODS = ['Card', 'Bank transfer', 'Cash']
PAYMENT_KINDS = ['Invoice', 'Package', 'Deposit', 'Plan instalment', 'Group fee']
INVOICE_STATUS = ['Paid', 'Part paid', 'Unpaid', 'On plan', 'Written off']
PLAN_STATUS = ['On track', 'Late', 'Completed']
PACKAGE_KINDS = ['6 sessions', '10 sessions']
PACKAGE_STATUS = ['Active', 'Used up', 'Expired']
DEPOSIT_STATUS = ['Held', 'Applied', 'Kept', 'Refunded']
OUTCOME_POINTS = ['Intake', 'Review', 'Discharge']
DISCHARGE_REASONS = ['Goals met', 'Client ended', 'Moved away', 'Referred out', 'No contact', 'Fees']
REFERRED_TO = ['Another practice', 'Specialist service', 'Family doctor', 'Group program', 'Community service']
SUPERVISION_KINDS = ['Individual', 'Group', 'Peer consultation']
CE_KINDS = ['Workshop', 'Online course', 'Conference', 'Training day', 'Reading group', 'Peer learning']
RENEWAL_KINDS = ['Registration', 'Liability insurance', 'Background check', 'First aid course', 'Membership fee', 'Practice insurance', 'Room lease', 'Privacy policy review']
GROUP_PROGRAMS = ['Parenting skills', 'Stress skills', 'Child social skills', 'Grief support', 'Teen confidence', 'Couples communication']
GROUP_STATUS = ['Planned', 'Open for sign-up', 'Running', 'Completed', 'Cancelled']
SIGNUP_STATUS = ['Signed up', 'Attending', 'Completed', 'Dropped out', 'Refunded']
MARKETING_KINDS = ['Online directory', 'Practice website', 'Workshop', 'Community talk', 'School talk', 'Referrer visit', 'Newsletter', 'Printed flyers']
EXPENSE_CATEGORIES = ['Rent', 'Utilities', 'Cleaning', 'Practice software', 'Phone and internet', 'Insurance', 'Marketing', 'Training', 'Supervision', 'Office supplies',
                      'Therapy materials', 'Accounting', 'Bank and card fees', 'Professional fees']
PAY_STATUS = ['Paid', 'Due', 'Accruing']
TAX_STATUS = ['Paid', 'Due', 'Upcoming']
SUBLET_STATUS = ['Paid', 'Invoiced', 'Accruing']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
WORKDAYS = WEEKDAYS[:6]                      # the practice is open Monday to Saturday
SESSION_SERVICES = SERVICES[:-1]             # the 9 services booked as sessions (groups are run as programs)
PAY_KINDS = ['Salary', 'Percentage split', 'Per session', 'Hourly']
SLOT_STATUS = ['Booked', 'Free', 'Away', 'Extra']
ABSENCE_KINDS = ['Holiday', 'Training', 'Personal leave']

# ------------------------------------------------------------------ people
# id, name, country, role, team, pay type, hours a week, monthly salary, split, session rate, hourly rate, session cap a week, session target a week, speciality, start days ago
_staff = [('TH-01', 'Amira Lindqvist', 'Sweden', 'Owner clinician', 'Management', 'Owner draw', 40, 0, 0, 0, 0, 14, 12, 'Individual and couples work, practice lead', 2600),
          ('TH-02', 'Daniel Okoye', 'Nigeria', 'Clinician', 'Clinical', 'Salary', 38, 4800, 0, 0, 0, 26, 24, 'Individual counselling and young people', 1650),
          ('TH-03', 'Sofia Marchetti', 'Italy', 'Clinician', 'Clinical', 'Salary', 37, 4500, 0, 0, 0, 25, 22, 'Couples and family sessions', 1200),
          ('TH-04', 'Kenji Watanabe', 'Japan', 'Contract clinician', 'Clinical', 'Percentage split', 30, 0, 0.60, 0, 0, 22, 20, 'Child and family sessions', 950),
          ('TH-05', 'Priya Raman', 'India', 'Contract clinician', 'Clinical', 'Percentage split', 28, 0, 0.65, 0, 0, 20, 18, 'Speech and behaviour therapy', 480),
          ('TH-06', 'Lucas Moreau', 'France', 'Associate', 'Clinical', 'Per session', 30, 0, 0, ASSOCIATE_RATE, 0, 16, 15, 'Supervised associate, adults and children', 300),
          ('TH-07', 'Grace Mensah', 'Ghana', 'Practice coordinator', 'Front desk', 'Hourly', 32, 0, 0, 0, 24, 0, 0, 'Front desk, scheduling and billing', 1100)]
staff = []
for i, (a, b, c, ro, te, pt, hw, sal, sp, sr_, hr, cap, tg, spec, st) in enumerate(_staff):
    staff.append(dict(staff_id=a, name=b, role=ro, team=te, pay_type=pt, phone=fake_phone(101 + i), email=fake_email(b), hours_week=hw, monthly_salary=float(sal), split_pct=sp,
                      session_rate=float(sr_), hourly_rate=float(hr), session_cap=cap, session_target=tg, speciality=spec, country=c, start=ago(st)))
_ctc = [('TH-08', 'Mateo Alvarez', 'Argentina', 'Accountant', 'Bookkeeping, payroll and yearly accounts'),
        ('TH-09', 'Helena Novak', 'Czechia', 'Clinical supervisor', 'External supervision for the owner and the monthly group'),
        ('TH-10', 'Samir Haddad', 'Lebanon', 'IT support', 'Computers, phones and secure records set-up'),
        ('TH-11', 'Ingrid Berg', 'Norway', 'Landlord', 'Practice suite lease and building repairs'),
        ('TH-12', 'Wanjiru Kamau', 'Kenya', 'Cleaner', 'Evening cleaning of rooms and the waiting area')]
contacts = [dict(staff_id=a, name=b, role=ro, team='Outside', pay_type='Invoice', phone=fake_phone(108 + i), email=fake_email(b), hours_week=0, monthly_salary=0.0, split_pct=0,
                 session_rate=0.0, hourly_rate=0.0, session_cap=0, session_target=0, speciality=sp, country=c, start=ago(2100 - 200 * i)) for i, (a, b, c, ro, sp) in enumerate(_ctc)]
team = staff + contacts
staff_by_name = {s['name']: s for s in team}
CLINICIANS = [s['name'] for s in staff[:6]]
STAFF_NAMES = [s['name'] for s in staff]
PAID_STAFF = STAFF_NAMES[1:]                 # the 6 people paid through pay rows (the owner takes a draw)
CONTRACTORS = [s['name'] for s in staff if s['pay_type'] == 'Percentage split']
HOLDERS = STAFF_NAMES + ['Practice']
SPLIT = {s['name']: s['split_pct'] for s in staff}

# service id, name, minutes, fee this year, materials per attended session, client type it serves
_SV = [('SV-01', 'Intake assessment', 75, 150, 2.0), ('SV-02', 'Individual session', 50, 125, 0.0), ('SV-03', 'Extended individual', 80, 180, 0.0),
       ('SV-04', 'Couples session', 75, 170, 0.0), ('SV-05', 'Family session', 75, 180, 1.0), ('SV-06', 'Child session', 50, 120, 4.0), ('SV-07', 'Speech therapy', 45, 110, 5.0),
       ('SV-08', 'Behaviour therapy', 60, 90, 12.0), ('SV-09', 'Review session', 30, 70, 0.0), ('SV-10', 'Group program', 90, 30, 0.0)]
def _old_fee(name, fee): return fee if name == 'Behaviour therapy' else int(round(fee / 1.05 / 5.0) * 5)
services = [dict(service_id=a, service=b, minutes=m, fee=float(f), last_year_fee=float(_old_fee(b, f)), materials=mt) for a, b, m, f, mt in _SV]
SV = {s['service']: s for s in services}
payers = [dict(payer='Payer A', fee_share=0.85, copay=20.0, days_lo=10, days_hi=25, deny=0.04),
          dict(payer='Payer B', fee_share=0.80, copay=15.0, days_lo=18, days_hi=42, deny=0.08),
          dict(payer='Payer C', fee_share=0.90, copay=0.0, days_lo=7, days_hi=18, deny=0.03),
          dict(payer='Payer D', fee_share=0.75, copay=25.0, days_lo=25, days_hi=58, deny=0.11)]
PY = {p['payer']: p for p in payers}
rooms = [dict(room_id='RM-01', room='Garden Room', kind='Adult room', seats=3, open_hours_week=55, sublet_rate=22.0),
         dict(room_id='RM-02', room='Willow Room', kind='Adult room', seats=3, open_hours_week=55, sublet_rate=22.0),
         dict(room_id='RM-03', room='Family Room', kind='Family room', seats=8, open_hours_week=59, sublet_rate=28.0),
         dict(room_id='RM-04', room='Play Room', kind='Child room', seats=4, open_hours_week=59, sublet_rate=24.0),
         dict(room_id='RM-05', room='Quiet Room', kind='Adult room', seats=2, open_hours_week=55, sublet_rate=20.0)]
ROOM_NAMES = [x['room'] for x in rooms]
HOME_ROOM = {'Amira Lindqvist': 'Garden Room', 'Daniel Okoye': 'Willow Room', 'Sofia Marchetti': 'Quiet Room', 'Kenji Watanabe': 'Quiet Room', 'Priya Raman': 'Play Room',
             'Lucas Moreau': 'Garden Room'}
# weekly session slots (weekday 0=Monday: hours) - the number of slots is the session cap
_GRID = {'Amira Lindqvist': {1: [9, 10, 11, 14, 15], 2: [9, 10, 11, 14], 3: [10, 11, 14, 15, 16]},
         'Daniel Okoye': {0: [9, 10, 11, 13, 14, 15], 1: [10, 11, 13, 14, 15, 16], 2: [12, 13, 14, 15, 16], 3: [9, 10, 11, 13, 14], 4: [9, 10, 11, 13]},
         'Sofia Marchetti': {0: [13, 14, 15, 16, 17, 18], 1: [14, 15, 16, 17, 18], 3: [15, 16, 17, 18], 4: [10, 11, 13, 14, 15, 16], 5: [9, 10, 11, 12]},
         'Kenji Watanabe': {0: [10, 11, 15, 16, 17, 18], 1: [15, 16, 17, 18], 2: [10, 11, 14, 15, 16, 17], 3: [14, 15, 16, 17, 18, 19]},
         'Priya Raman': {0: [9, 10, 11, 14, 15], 2: [9, 10, 13, 14, 15], 3: [9, 10, 11, 13, 14], 4: [9, 10, 11, 13, 14]},
         'Lucas Moreau': {0: [17, 18, 19], 1: [9, 10, 11], 2: [17, 18, 19], 3: [9, 10], 4: [14, 15, 16, 17, 18]}}
for _s in staff[:6]: assert sum(len(v) for v in _GRID[_s['name']].values()) == _s['session_cap'], _s['name']

_RF = [('Hannah Becker', 'Family doctor'), ('Rui Teixeira', 'Family doctor'), ('Amaka Eze', 'Family doctor'), ('Wei Zhang', 'Family doctor'), ('Elena Navarro', 'Family doctor'),
       ('Oliver Shaw', 'Family doctor'), ('Meera Iyer', 'Family doctor'), ('Daan Visser', 'Family doctor'), ('Clara Winter', 'School staff'), ('Mateus Rocha', 'School staff'),
       ('Zeynep Kaya', 'School staff'), ('Jamie Porter', 'School staff'), ('Bea Ocampo', 'School staff'), ('Anika Rao', 'School staff'), ('Lea Garnier', 'Other clinician'),
       ('Jun Park', 'Other clinician'), ('Ruby Kelly', 'Other clinician'), ('Kerem Demir', 'Other clinician'), ('Marek Nowak', 'Other clinician'), ('Paola Rios', 'Employer contact'),
       ('Harvey Lambert', 'Employer contact'), ('Funmi Bello', 'Employer contact'), ('Salma Khalil', 'Community worker'), ('Andres Salazar', 'Community worker')]
referrers = [dict(referrer_id='RF-%02d' % i, name=n, kind=k, phone=fake_phone(300 + i), email=fake_email(n)) for i, (n, k) in enumerate(_RF, 1)]
tenants = [dict(tenant_id='TN-01', name='Tomasz Wojcik', kind='Family mediator', room='Family Room', hours_week=7, rate=25.0, phone=fake_phone(401), start=ago(690)),
           dict(tenant_id='TN-02', name='Leila Benali', kind='Career coach', room='Garden Room', hours_week=4, rate=22.0, phone=fake_phone(402), start=ago(560)),
           dict(tenant_id='TN-03', name='Ming Chen', kind='Art tutor', room='Play Room', hours_week=3, rate=20.0, phone=fake_phone(403), start=ago(300))]
programs = [dict(program='Parenting skills', weeks=8, capacity=10, fee=240.0), dict(program='Stress skills', weeks=6, capacity=10, fee=210.0),
            dict(program='Child social skills', weeks=8, capacity=6, fee=320.0), dict(program='Grief support', weeks=6, capacity=8, fee=180.0),
            dict(program='Teen confidence', weeks=8, capacity=8, fee=240.0), dict(program='Couples communication', weeks=4, capacity=6, fee=360.0)]

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


def _fee(service, d):
    s = SV[service]
    return s['fee'] if to_date(d) >= D(TODAY.year, 1, 1) else s['last_year_fee']


# ------------------------------------------------------------------ world: enquiries, clients and sessions
_KINDS = [('Adult', 'Individual session', .44), ('Adult', 'Extended individual', .06), ('Couple', 'Couples session', .12), ('Family', 'Family session', .07),
          ('Child', 'Child session', .10), ('Child', 'Speech therapy', .07), ('Child', 'Behaviour therapy', .06), ('Young person', 'Individual session', .08)]
_SKILL = {'Individual session': {'Amira Lindqvist': 1.0, 'Daniel Okoye': 1.6, 'Sofia Marchetti': .5, 'Kenji Watanabe': .4, 'Lucas Moreau': 1.5},
          'Extended individual': {'Amira Lindqvist': 1.5, 'Daniel Okoye': 1.0, 'Sofia Marchetti': .4},
          'Couples session': {'Amira Lindqvist': 1.2, 'Sofia Marchetti': 1.6, 'Daniel Okoye': .5},
          'Family session': {'Sofia Marchetti': 1.5, 'Kenji Watanabe': 1.0},
          'Child session': {'Kenji Watanabe': 1.6, 'Sofia Marchetti': .5, 'Lucas Moreau': .9},
          'Speech therapy': {'Priya Raman': 1.0},
          'Behaviour therapy': {'Priya Raman': 1.0, 'Lucas Moreau': .1},
          'Young person': {'Daniel Okoye': .9, 'Kenji Watanabe': 1.3, 'Lucas Moreau': 1.0, 'Sofia Marchetti': .5}}
_LEN = {'Individual session': ([4, 6, 8, 10, 12, 16, 20, 26, 36, 50], [8, 12, 14, 14, 13, 12, 9, 7, 7, 4]), 'Extended individual': ([4, 6, 8, 10, 12, 16], [2, 3, 3, 2, 2, 1]),
        'Couples session': ([4, 6, 8, 10, 12], [3, 4, 4, 2, 1]), 'Family session': ([3, 4, 6, 8, 10], [2, 3, 3, 2, 1]), 'Child session': ([6, 8, 10, 12, 16, 20], [2, 3, 3, 3, 2, 1]),
        'Speech therapy': ([10, 12, 16, 20, 24, 30], [1, 2, 3, 3, 2, 1]), 'Behaviour therapy': ([8, 12, 16, 20, 24], [1, 2, 3, 2, 1])}
_FREQ = {'Individual session': [.5, .38, .12], 'Extended individual': [.4, .45, .15], 'Couples session': [.45, .5, .05], 'Family session': [.3, .6, .1], 'Child session': [.7, .3, 0],
         'Speech therapy': [.88, .12, 0], 'Behaviour therapy': [.9, .1, 0]}
_PHASES = {'Weekly': [(0, 1, 2, 3)], 'Fortnightly': [(0, 2), (1, 3)], 'Monthly': [(0,), (1,), (2,), (3,)]}
_LOAD = {'Weekly': 1.0, 'Fortnightly': .5, 'Monthly': .25}
_ENQ_SEAS = [0, 1.25, 1.2, 1.1, 1.0, .95, .85, .7, .65, 1.2, 1.2, 1.05, .75]


def _absences():
    out = set(); WN = week_start(TODAY)
    for nm in CLINICIANS:
        r = rng('abs-' + nm)
        for y in range(TODAY.year - 2, TODAY.year + 2):
            jul = week_start(D(y, 6, 15)) + day(7 * r.randint(0, 10)); apr = week_start(D(y, 4, 1)) + day(7 * r.randint(0, 3))
            oth = week_start(D(y, r.choice([2, 5, 10]), 1)) + day(7 * r.randint(0, 3))
            for w in (jul, jul + day(7), apr, oth):
                if not (WN - day(21) <= w <= WN + day(21)): out.add((nm, w))
    out.add(('Kenji Watanabe', WN + day(28))); out.add(('Amira Lindqvist', WN + day(35)))
    return out


def _closed(ws):
    for y in (ws.year - 1, ws.year, ws.year + 1):
        if ws <= D(y + 1, 1, 1) and ws + day(6) >= D(y, 12, 24): return True
    return False


def _status(r, service, d):
    m = d.month; summer = .03 if m in (7, 8) else 0
    if service == 'Behaviour therapy': ws = [.78 - summer, .07 + summer, .07, .08]
    elif service == 'Speech therapy': ws = [.86 - summer, .07 + summer, .04, .03]
    elif service == 'Intake assessment': ws = [.9, .05, .02, .03]
    else: ws = [.885 - summer, .06 + summer, .032, .023]
    return _wchoice(r, ['Attended', 'Cancelled', 'Late cancel', 'No-show'], ws)


def _world():
    r = rng('world'); rn = rng('names'); WN = week_start(TODAY)
    W0 = week_start(HISTORY_START)
    NW = (WN - W0).days // 7 + 1 + FUTURE_WEEKS
    weeks = [W0 + day(7 * i) for i in range(NW)]
    absent = _absences()
    CL = {}
    for s in staff[:6]:
        nm = s['name']; slots = [(wd, h) for wd in sorted(_GRID[nm]) for h in _GRID[nm][wd]]
        CL[nm] = dict(slots=slots, occ=[[None] * 4 for _ in slots], start=to_date(s['start']), cap=s['session_cap'], target=s['session_target'])
    used_names = set(staff_by_name)

    def person():
        fs, ls = _G[rn.randrange(len(_G))]
        return rn.choice(fs), rn.choice(ls)

    def new_name(ctype):
        for _ in range(60):
            f, l = person()
            if ctype == 'Couple':
                f2 = rn.choice(_G[rn.randrange(len(_G))][0])
                if f2 == f: continue
                nm = '%s and %s %s' % (f, f2, l); contact = '%s %s' % (f, l)
            elif ctype == 'Family': nm = '%s family' % l; contact = '%s %s' % (f, l)
            elif ctype in ('Child', 'Young person'):
                nm = '%s %s' % (f, l); contact = '%s %s' % (rn.choice(_G[rn.randrange(len(_G))][0]), l)
            else: nm = contact = '%s %s' % (f, l)
            if ctype == 'Family' and nm in used_names: nm = '%s %s family' % (f, l)
            if nm not in used_names: used_names.add(nm); return nm, contact
        raise RuntimeError('names')

    def load(nm): return sum(1 for s in CL[nm]['occ'] for p in s if p is not None) / 4.0

    clients = []; enquiries = []; queue = []; active = []

    def make_client(ctype, service, ref_date, enquiry=None):
        nm, contact = (enquiry['name'], enquiry['contact']) if enquiry else new_name(ctype)
        c = dict(client_type=ctype, service=service, client=nm, contact=contact, enquiry_id=enquiry['enquiry_id'] if enquiry else '',
                 source=enquiry['source'] if enquiry else _wchoice(r, REFERRAL_SOURCES, [15, 8, 10, 7, 9, 16, 18, 13, 4]), referrer=enquiry['referrer'] if enquiry else '')
        if not enquiry:
            kd = {'Doctor referral': 'Family doctor', 'School referral': 'School staff', 'Other clinician': 'Other clinician', 'Employer program': 'Employer contact'}.get(c['source'])
            if kd: c['referrer'] = r.choice([x['name'] for x in referrers if x['kind'] == kd])
        sv = service if service in _FREQ else 'Individual session'
        c['frequency'] = _wchoice(r, FREQUENCIES, _FREQ[sv])
        L_, W_ = _LEN[sv]; c['planned'] = _wchoice(r, L_, W_)
        if ctype == 'Young person': c['planned'] = min(c['planned'], 16)
        child = ctype in ('Child', 'Family') or service in ('Speech therapy', 'Behaviour therapy')
        fwt = [.38, .07, .05, .50] if child else [.52, .14, .10 if ctype in ('Adult', 'Couple') else 0, .24]
        c['fee_type'] = _wchoice(r, FEE_TYPES, fwt)
        c['payer'] = _wchoice(r, PAYERS, [.35, .3, .2, .15]) if c['fee_type'] == 'Third-party payer' else ''
        c['factor'] = r.choice([.6, .7, .8]) if c['fee_type'] == 'Sliding scale' else 1.0
        if service == 'Behaviour therapy' and c['fee_type'] == 'Standard' and r.random() < .3: c['fee_type'] = 'Sliding scale'; c['factor'] = r.choice([.6, .7])
        c['habit'] = _wchoice(r, ['Prompt', 'Normal', 'Slow', 'Very slow'], [58, 30, 9, 3])
        c['method'] = 'Card' if c['habit'] == 'Prompt' and r.random() < .93 else ('Cash' if c['habit'] == 'Prompt' else 'Bank transfer')
        c['claim_back'] = 'Yes' if c['fee_type'] == 'Standard' and r.random() < .15 else 'No'
        if child: c['format'] = _wchoice(r, FORMATS, [.92, .08, 0])
        elif ctype == 'Couple': c['format'] = _wchoice(r, FORMATS, [.7, .3, 0])
        else: c['format'] = _wchoice(r, FORMATS, [.58, .38, .04])
        c['intake_score'] = r.randint(15, 34); c['score'] = c['intake_score']
        c['sessions'] = []; c['attended_regular'] = 0; c['end'] = None; c['end_reason'] = ''; c['package'] = None; c['packages'] = []
        return c

    def phases_free(nm, idx, ph): return all(CL[nm]['occ'][idx][p] is None for p in ph)

    def try_assign(c, wi, ready):
        sv = 'Young person' if c['client_type'] == 'Young person' else c['service']
        cands = []
        for nm, w in _SKILL[sv].items():
            st = CL[nm]
            if st['start'] > weeks[wi]: continue
            ld = load(nm)
            if ld + _LOAD[c['frequency']] > st['target'] + 1: continue
            cands.append((w * (st['target'] + 1.5 - ld) / st['target'] * r.uniform(.8, 1.2), nm))
        cands.sort(reverse=True)
        for _, nm in cands:
            st = CL[nm]; idxs = list(range(len(st['slots']))); r.shuffle(idxs)
            if c['client_type'] in ('Child', 'Young person') or c['service'] in ('Couples session', 'Family session'):
                idxs.sort(key=lambda i: 0 if (st['slots'][i][1] >= 15 or st['slots'][i][0] == 5) else 1)
            for idx in idxs:
                pats = list(_PHASES[c['frequency']]); r.shuffle(pats)
                for ph in pats:
                    if not phases_free(nm, idx, ph): continue
                    wd, h = st['slots'][idx]
                    for w2 in range(wi, min(len(weeks), wi + 6)):
                        if w2 % 4 in ph and weeks[w2] + day(wd) > ready: break
                    else: continue
                    for p in ph: st['occ'][idx][p] = c
                    c.update(clinician=nm, slot=idx, phases=ph, start_wi=w2, weekday=wd, hour=h); return True
        return False

    # opening caseload: clients who started before the history window
    for nm in CLINICIANS:
        st = CL[nm]
        if st['start'] > weeks[0]: continue
        guard = 0
        while load(nm) < st['target'] - .5 and guard < 80:
            guard += 1
            opts = [(ct, sv) for ct, sv, w in _KINDS if nm in _SKILL['Young person' if ct == 'Young person' else sv]]
            ct, sv = r.choice(opts)
            c = make_client(ct, sv, weeks[0])
            if try_assign(c, 0, weeks[0] - day(1)):
                back = r.randint(2, 40); c['start_wi'] -= 4 * ((back + 3) // 4)
                c['first_session'] = iso(weeks[0] + day(7 * c['start_wi'] + c['weekday'])); c['booked_on'] = iso(to_date(c['first_session']) - day(r.randint(5, 20)))
                done = int(back * _LOAD[c['frequency']] * .85); c['planned'] = max(c['planned'], done + r.randint(2, 14)); c['attended_regular'] = done; c['pre'] = True
                clients.append(c); active.append(c)
    # weekly simulation
    eid = 0
    for wi, ws in enumerate(weeks):
        if ws <= TODAY:
            base = 15.0 * _ENQ_SEAS[(ws + day(3)).month] * (1 + .18 * (ws - weeks[0]).days / 700.0)
            n = max(4, int(round(r.gauss(base, 2.4))))
            for _ in range(n):
                d = ws + day(r.choice([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 6]))
                if d > TODAY: d = TODAY - day(r.randint(0, min(2, (TODAY - ws).days)))
                ct, sv, _w = _wchoice(r, _KINDS, [k[2] for k in _KINDS])
                eid += 1
                nm, contact = new_name(ct)
                child = ct in ('Child', 'Young person', 'Family')
                src = _wchoice(r, REFERRAL_SOURCES, [22, 30, 10, 2, 6, 12, 8, 8, 2] if child else [15, 1, 10, 9, 9, 15, 21, 15, 5])
                kind = {'Doctor referral': 'Family doctor', 'School referral': 'School staff', 'Other clinician': 'Other clinician' if r.random() < .75 else 'Community worker',
                        'Employer program': 'Employer contact'}.get(src)
                ref = r.choice([x['name'] for x in referrers if x['kind'] == kind]) if kind else ''
                e = dict(enquiry_id=eid, date=d, name=nm, contact=contact, client_type=ct, service=sv, source=src, referrer=ref,
                         method=_wchoice(r, CONTACT_METHODS, [40, 24, 31, 5]), screening='', screened_by='', status='', reason='', first_session='', client=None,
                         priority=_wchoice(r, PRIORITIES, [15, 70, 15]), clinician='')
                sd = d + day(r.choice([1, 1, 2, 2, 3, 4]))
                needs_priya = sv in ('Speech therapy', 'Behaviour therapy')
                if needs_priya and CL['Priya Raman']['start'] > d + day(14):
                    e['screening'] = sd; e['status'] = 'Referred elsewhere'; e['reason'] = 'Service not offered'
                else:
                    o = _wchoice(r, ['go', 'ref', 'noreply', 'decl'], [63, 10, 14, 13])
                    if o == 'noreply': e['status'] = 'No reply'; e['reason'] = 'No reply'
                    elif o == 'ref': e['screening'] = sd; e['status'] = 'Referred elsewhere'; e['reason'] = 'Not a fit'
                    elif o == 'decl': e['screening'] = sd; e['status'] = 'Declined'; e['reason'] = _wchoice(r, ['Fees', 'Timing', 'Went elsewhere'], [4, 4, 3])
                    else:
                        e['screening'] = sd; e['status'] = 'go'; e['ready'] = sd + day(r.randint(2, 6)); e['give_up'] = r.choice([28, 42, 56, 70, 90])
                        queue.append(e)
                if e['screening']: e['screened_by'] = COORDINATOR if r.random() < .7 else OWNER
                enquiries.append(e)
        # assignment of waiting enquiries
        if ws <= TODAY + day(14):
            keep = []
            for e in sorted(queue, key=lambda x: ({'High': 0, 'Normal': 1, 'Low': 2}[x['priority']], x['ready'])):
                if e['ready'] > min(ws + day(6), TODAY + day(3)): keep.append(e); continue
                c = make_client(e['client_type'], e['service'], ws, e)
                if try_assign(c, wi, max(e['ready'], TODAY if ws > TODAY else e['ready'])):
                    c['booked_on'] = iso(min(TODAY, max(e['ready'], weeks[c['start_wi']] - day(r.randint(3, 8)))))
                    c['first_session'] = iso(weeks[c['start_wi']] + day(c['weekday'])); c['pre'] = False
                    e['status'] = 'Booked'; e['client'] = c; e['first_session'] = c['first_session']; e['clinician'] = c['clinician']
                    clients.append(c); active.append(c)
                elif ws <= TODAY and (ws - e['ready']).days > e['give_up']:
                    e['status'] = 'Declined'; e['reason'] = 'Waited too long'; e['withdrawn'] = ws + day(r.randint(0, 4))
                else: keep.append(e)
            queue = keep
        # sessions this week
        closed = _closed(ws)
        for c in sorted(active, key=lambda x: (CLINICIANS.index(x['clinician']), x['slot'], x['client'])):
            if c['end'] is not None or wi < c['start_wi'] or wi % 4 not in c['phases']: continue
            if closed or (c['clinician'], ws) in absent: continue
            d = ws + day(c['weekday'])
            first = not c['pre'] and not c['sessions']
            service = 'Intake assessment' if first else c['service']
            last = (not first) and c['attended_regular'] + 1 >= c['planned']
            if last and c['client_type'] in ('Adult', 'Young person', 'Couple') and r.random() < .4: service = 'Review session'
            if d > TODAY: st = 'Scheduled'
            else: st = _status(r, service, d)
            s = dict(client=c, date=d, hour=c['hour'], service=service, status=st, clinician=c['clinician'])
            c['sessions'].append(s)
            if st in ('Attended', 'Scheduled') and not first: c['attended_regular'] += 1
            if d > TODAY:
                if c['attended_regular'] >= c['planned']: c['end'] = 'future'
                continue
            if first and st in ('No-show', 'Cancelled') and r.random() < .45: c['end'] = d; c['end_reason'] = 'No contact'
            elif st == 'Attended' and not first and r.random() < .028:
                c['end'] = d; c['end_reason'] = _wchoice(r, ['Client ended', 'No contact', 'Fees', 'Moved away'], [5, 3, 1, 1])
            elif c['attended_regular'] >= c['planned']:
                c['end'] = d; c['end_reason'] = _wchoice(r, ['Goals met', 'Referred out', 'Client ended'], [78, 9, 13])
            if c['end'] is not None and c['end'] != 'future':
                st_ = CL[c['clinician']]
                for p in c['phases']: st_['occ'][c['slot']][p] = None
        active = [c for c in active if c['end'] is None or c['end'] == 'future']
    for e in queue: e['status'] = 'Waiting list'
    return dict(clients=clients, enquiries=enquiries, weeks=weeks, absent=absent)


def _story_rows(W):
    """inject the story into the world: on hold clients, the over-booked week, late notes, overdue invoices, denied claims"""
    r = rng('story'); clients = W['clients']; WN = week_start(TODAY); over = WN + day(7)
    # over-booked clinician next week: extra sessions for existing clients outside the usual slots
    sofia = [c for c in clients if c['clinician'] == 'Sofia Marchetti' and c['end'] in (None, 'future') and c['first_session'] <= iso(TODAY)]
    cnt = sum(1 for c in clients for s in c['sessions'] if s['clinician'] == 'Sofia Marchetti' and week_start(s['date']) == over)
    extra = [(0, 12), (1, 13), (3, 13), (3, 14), (4, 17), (4, 18), (5, 13), (0, 19), (1, 19), (3, 19), (4, 9)]
    k = 0
    for c in sofia:
        if cnt >= 31: break
        if any(week_start(s['date']) == over for s in c['sessions']): continue
        wd, h = extra[k]; k += 1
        c['sessions'].append(dict(client=c, date=over + day(wd), hour=h, service=c['service'], status='Scheduled', clinician='Sofia Marchetti', extra=True)); cnt += 1
    W['over_week'] = over
    # on hold: a few active adult clients pause (sessions in the last 3 and next 6 weeks removed)
    cand = [c for c in clients if c['end'] in (None, 'future') and c['first_session'] < ago(120) and c['client_type'] == 'Adult' and c['clinician'] in ('Daniel Okoye', 'Amira Lindqvist')]
    for c in cand[:: max(1, len(cand) // 4)][:4]:
        c['sessions'] = [s for s in c['sessions'] if not (TODAY - day(21) <= s['date'] <= TODAY + day(45))]; c['on_hold'] = True


def _world_full():
    W = _world(); _story_rows(W); r = rng('money')
    clients = W['clients']
    clients.sort(key=lambda c: (c['first_session'], c['client']))
    for i, c in enumerate(clients, 1): c['client_id'] = 'CL-%04d' % i
    sessions = [s for c in clients for s in c['sessions']]
    sessions.sort(key=lambda s: (s['date'], s['hour'], CLINICIANS.index(s['clinician']), s['client']['client_id']))
    taken = set()
    for i, s in enumerate(sessions, 1):
        c = s['client']; s['session_id'] = 'SE-%05d' % i
        sv = SV[s['service']]; s['minutes'] = sv['minutes']
        fmt = c['format']
        if s['service'] == 'Intake assessment' and fmt != 'In person' and r.random() < .5: fmt = 'In person'
        s['format'] = fmt
        if fmt != 'In person': s['room'] = 'Online'
        else:
            if s['service'] in ('Couples session', 'Family session') or c['client_type'] in ('Couple', 'Family'): order = ['Family Room', 'Quiet Room', 'Willow Room']
            elif c['client_type'] == 'Child': order = ['Play Room', 'Family Room', 'Quiet Room']
            else:
                home = HOME_ROOM[s['clinician']]; order = [home] + [x for x in ('Garden Room', 'Willow Room', 'Quiet Room', 'Family Room') if x != home]
            s['room'] = 'Online'
            for rm in order:
                if (s['date'], s['hour'], rm) not in taken: taken.add((s['date'], s['hour'], rm)); s['room'] = rm; break
            if s['room'] == 'Online': s['format'] = 'Online'
        fee = _fee(s['service'], s['date']); s['fee'] = fee
        ft = c['fee_type']; s['fee_type'] = ft; s['payer'] = c['payer']; s['package_id'] = ''
        st = s['status']; s['cancel_reason'] = ''; s['fee_waived'] = 'No'
        if st in ('Attended', 'Scheduled'):
            if ft == 'Third-party payer':
                allowed = R2(fee * PY[c['payer']]['fee_share']); cp = min(PY[c['payer']]['copay'], allowed); s['payer_amount'] = R2(allowed - cp); s['client_amount'] = cp
            elif ft == 'Sliding scale': s['payer_amount'] = 0.0; s['client_amount'] = float(round(fee * c['factor'] / 5.0) * 5)
            elif ft == 'Package' and s['service'] != 'Intake assessment' and s['date'] > TODAY and (c['package'] is None or c['package']['used'] >= c['package']['sessions']):
                s['payer_amount'] = 0.0; s['client_amount'] = R2(fee * .9)
            elif ft == 'Package' and s['service'] != 'Intake assessment':
                pk = c['package']
                if pk is None or pk['used'] >= pk['sessions']:
                    n = r.choice([6, 10]); pk = dict(client=c, kind='%d sessions' % n, sessions=n, price=R2(fee * n * (.95 if n == 6 else .9)), bought_on=s['date'], used=0, used_past=0)
                    c['package'] = pk; c['packages'].append(pk)
                pk['used'] += 1
                if st == 'Attended': pk['used_past'] += 1
                s['_pk'] = pk; s['payer_amount'] = 0.0; s['client_amount'] = R2(pk['price'] / pk['sessions'])
            else: s['payer_amount'] = 0.0; s['client_amount'] = fee
        elif st in ('Late cancel', 'No-show'):
            waive = r.random() < (.5 if s['service'] == 'Behaviour therapy' else .33)
            s['fee_waived'] = 'Yes' if waive else 'No'; s['payer_amount'] = 0.0; s['client_amount'] = 0.0 if waive else float(round(fee * LATE_FEE_PCT))
            if st == 'Late cancel': s['cancel_reason'] = _wchoice(r, CANCEL_REASONS[:6], [30, 20, 8, 14, 18, 10])
        else:
            s['payer_amount'] = 0.0; s['client_amount'] = 0.0; s['cancel_reason'] = _wchoice(r, CANCEL_REASONS, [30, 22, 15, 12, 6, 6, 9])
        s['charge'] = R2(s['payer_amount'] + s['client_amount'])
        # notes (status only, never content)
        s['note_done_on'] = ''; s['note_on_time'] = ''
        if st == 'Attended':
            dl = _wchoice(r, [0, 1, 2, 3, 4, 6], [70, 18, 6, 3, 2, 1]) if s['clinician'] != ASSOCIATE else _wchoice(r, [0, 1, 2, 3, 4, 6], [55, 22, 10, 7, 4, 2])
            dl = min(dl, (TODAY - s['date']).days)
            if s['date'] + day(dl) <= TODAY and not (s['date'] >= TODAY - day(1) and r.random() < .5):
                s['note_done_on'] = iso(s['date'] + day(dl)); s['note_on_time'] = 'Yes' if dl <= NOTE_DUE_DAYS else 'No'
    # story: the associate's notes overdue in the last two weeks
    lucas = [s for s in sessions if s['clinician'] == ASSOCIATE and s['status'] == 'Attended' and TODAY - day(17) <= s['date'] <= TODAY - day(3)]
    for s in lucas[-9:]: s['note_done_on'] = ''; s['note_on_time'] = ''
    # clinician pay per session
    att = {}
    for s in sessions:
        if s['status'] == 'Attended': k = (s['clinician'], _ms(s['date'])); att[k] = att.get(k, 0) + s['minutes']
    for s in sessions:
        nm = s['clinician']; p = staff_by_name[nm]; st = s['status']
        if p['pay_type'] == 'Salary':
            if st == 'Attended': s['clinician_pay'] = R2(p['monthly_salary'] * (1 + EMPLOYER_COST_PCT) * s['minutes'] / att[(nm, _ms(s['date']))])
            elif st == 'Scheduled': s['clinician_pay'] = R2(p['monthly_salary'] * (1 + EMPLOYER_COST_PCT) * s['minutes'] / (p['session_target'] * 4.33 * .9 * 55))
            else: s['clinician_pay'] = 0.0
        elif p['pay_type'] == 'Percentage split': s['clinician_pay'] = R2(p['split_pct'] * s['charge'])
        elif p['pay_type'] == 'Per session': s['clinician_pay'] = ASSOCIATE_RATE if st in ('Attended', 'Scheduled') else 0.0
        else: s['clinician_pay'] = 0.0
        s['room_cost'] = R2(ROOM_COST_HOUR * (s['minutes'] + 15) / 60.0) if s['format'] == 'In person' and st != 'Cancelled' else 0.0
        if st in ('Attended', 'Scheduled'): s['other_cost'] = R2(ADMIN_COST + SV[s['service']]['materials'] + (CLAIM_ADMIN if s['fee_type'] == 'Third-party payer' else 0))
        elif st in ('Late cancel', 'No-show'): s['other_cost'] = ADMIN_COST
        else: s['other_cost'] = 0.0
    W['sessions'] = sessions
    return W


def _W(): return _raw('world', _world_full)


def _client_status(c):
    if c.get('on_hold'): return 'On hold'
    if c['end'] not in (None, 'future'): return 'Referred out' if c['end_reason'] == 'Referred out' else 'Discharged'
    return 'Booked' if c['first_session'] > iso(TODAY) else 'Active'


def _sess_pub(s):
    c = s['client']
    return dict(session_id=s['session_id'], date=iso(s['date']), week=iso(week_start(s['date'])), month=iso(_ms(s['date'])), time='%02d:00' % s['hour'],
                weekday=WEEKDAYS[s['date'].weekday()], client_id=c['client_id'], client=c['client'], client_type=c['client_type'], service=s['service'], clinician=s['clinician'],
                format=s['format'], room=s['room'], minutes=s['minutes'], status=s['status'], cancel_reason=s['cancel_reason'], fee_waived=s['fee_waived'], fee_type=s['fee_type'],
                payer=s['payer'], fee=s['fee'], charge=s['charge'], payer_amount=s['payer_amount'], client_amount=s['client_amount'], package_id=s['package_id'],
                clinician_pay=s['clinician_pay'], room_cost=s['room_cost'], other_cost=s['other_cost'], note_done_on=s['note_done_on'], note_on_time=s['note_on_time'])


def _packages():
    def f():
        W = _W(); pks = [pk for c in W['clients'] for pk in c['packages']]; pks.sort(key=lambda p: (p['bought_on'], p['client']['client_id']))
        for i, pk in enumerate(pks, 1): pk['package_id'] = 'PK-%03d' % i
        for s in W['sessions']:
            if '_pk' in s: s['package_id'] = s['_pk']['package_id']
        return pks
    return _raw('pk', f)


def session_rows(n=None):
    def f(): _packages(); return [_sess_pub(s) for s in _W()['sessions']]
    return _thin(_cached('sess', f), n)


def client_rows(n=None):
    def f():
        out = []; W = _W(); _packages(); revs = {}
        for x in _plan_reviews_raw():
            if x['score'] != '': revs.setdefault(x['client_id'], []).append(x)
        for c in W['clients']:
            past = [s for s in c['sessions'] if s['date'] <= TODAY]; fut = [s for s in c['sessions'] if s['date'] > TODAY]
            st = _client_status(c)
            dis = ''
            if st in ('Discharged', 'Referred out'): dis = iso(min(TODAY, c['end'] + day(rng('dis' + c['client_id']).randint(0, 10))))
            rev = revs.get(c['client_id'], [])
            out.append(dict(client_id=c['client_id'], client=c['client'], client_type=c['client_type'], contact=c['contact'], phone=fake_phone(1000 + int(c['client_id'][3:])),
                            email=fake_email(c['contact'], int(c['client_id'][3:]) % 7), service=c['service'], clinician=c['clinician'], frequency=c['frequency'], format=c['format'],
                            referral_source=c['source'], referrer=c['referrer'], enquiry_id=('EN-%04d' % c['enquiry_id']) if c['enquiry_id'] else '', booked_on=c['booked_on'],
                            first_session=c['first_session'], fee_type=c['fee_type'], payer=c['payer'], sliding_pct=c['factor'] if c['fee_type'] == 'Sliding scale' else 1.0,
                            pay_method=c['method'], claim_back=c['claim_back'], status=st, discharge_date=dis,
                            discharge_reason=c['end_reason'] if dis else '', sessions_attended=sum(1 for s in past if s['status'] == 'Attended'),
                            last_session=iso(max(s['date'] for s in past if s['status'] == 'Attended')) if any(s['status'] == 'Attended' for s in past) else '',
                            next_session=iso(min(s['date'] for s in fut)) if fut else '', intake_score=c['intake_score'], latest_score=rev[-1]['score'] if rev else c['intake_score']))
        return out
    return _thin(_cached('cl', f), n)


def enquiry_rows(n=None):
    def f():
        W = _W(); es = sorted(W['enquiries'], key=lambda e: (e['date'], e['enquiry_id'])); out = []
        # the last days always hold a few new enquiries and booked screening calls
        rec = [e for e in es if e['date'] >= TODAY - day(2) and e['status'] in ('No reply', 'Declined', 'Referred elsewhere')]
        for e in rec[:2]: e['status'] = 'New'; e['screening'] = ''; e['screened_by'] = ''; e['reason'] = ''
        rec2 = [e for e in es if TODAY - day(6) <= e['date'] < TODAY - day(2) and e['status'] in ('No reply', 'Declined')]
        for e in rec2[:2]: e['status'] = 'Screening booked'; e['screening'] = TODAY + day(1 + (e['enquiry_id'] % 3)); e['screened_by'] = COORDINATOR; e['reason'] = ''
        for e in es:
            if e['status'] == 'No reply' and e['date'] >= TODAY - day(3): e['status'] = 'New'; e['reason'] = ''
            if e['screening'] and e['screening'] > TODAY:
                if e['status'] == 'Booked': e['screening'] = TODAY
                else: e['status'] = 'Screening booked'; e['reason'] = ''; e['screened_by'] = e['screened_by'] or COORDINATOR
            c = e['client']
            out.append(dict(enquiry_id='EN-%04d' % e['enquiry_id'], date=iso(e['date']), name=e['name'], contact=e['contact'], phone=fake_phone(1000 + int(c['client_id'][3:])) if c else fake_phone(5000 + e['enquiry_id']),
                            client_type=e['client_type'], service=e['service'], source=e['source'], referrer=e['referrer'], contact_method=e['method'], priority=e['priority'],
                            screening_date=iso(e['screening']) if e['screening'] else '', screened_by=e['screened_by'], status=e['status'], reason=e['reason'],
                            clinician=e['clinician'], first_session=e['first_session'], client_id=c['client_id'] if c else ''))
        return out
    return _thin(_cached('enq', f), n)


def waitlist_rows(n=None):
    def f():
        out = []
        for e in enquiry_rows():
            if not e['screening_date']: continue
            fs = e['first_session']; ws = e['screening_date']
            if e['status'] == 'Waiting list': st = 'Waiting'; off = ''; started = ''
            elif e['status'] == 'Booked' and (to_date(fs) - to_date(ws)).days > 10:
                off = iso(min(TODAY, to_date(fs) - day(5 + int(e['enquiry_id'][3:]) % 5))); started = fs if fs <= iso(TODAY) else ''; st = 'Started' if started else 'Offered'
            elif e['status'] == 'Declined' and e['reason'] == 'Waited too long': st = 'Withdrawn'; off = ''; started = ''
            else: continue
            out.append(dict(added_on=ws, enquiry_id=e['enquiry_id'], name=e['name'], phone=e['phone'], client_type=e['client_type'], service=e['service'], priority=e['priority'],
                            source=e['source'], offered_on=off, started_on=started, clinician=e['clinician'] if st != 'Withdrawn' else '', status=st))
        out.sort(key=lambda x: (x['added_on'], x['enquiry_id']))
        for i, x in enumerate(out, 1): x['wait_id'] = 'WL-%03d' % i
        return [dict(wait_id=x.pop('wait_id'), **x) for x in out]
    return _thin(_cached('wl', f), n)


# ------------------------------------------------------------------ claims
def _claims_raw():
    def f():
        W = _W(); out = []
        st_cl = None
        cand = {}
        for s in W['sessions']:
            if s['fee_type'] == 'Third-party payer' and s['payer'] == 'Payer B' and s['status'] == 'Attended' and TODAY - day(84) <= s['date'] <= TODAY - day(57):
                cand.setdefault(s['client']['client_id'], []).append(s)
        good = sorted([k for k, v in cand.items() if len(v) >= 4]); st_cl = max(good, key=lambda k: sum(s['payer_amount'] for s in cand[k])) if good else None
        for s in W['sessions']:
            if s['fee_type'] != 'Third-party payer' or s['status'] != 'Attended' or s['payer_amount'] <= 0: continue
            r = rng('cl-' + s['session_id']); p = PY[s['payer']]; amt = s['payer_amount']
            sub = s['date'] + day(r.randint(1, 6))
            if sub > TODAY: continue
            x = dict(session_id=s['session_id'], date=iso(s['date']), client_id=s['client']['client_id'], client=s['client']['client'], payer=s['payer'], service=s['service'],
                     clinician=s['clinician'], amount=amt, submitted_on=iso(sub), status='Submitted', denial_reason='', denied_on='', resubmitted_on='', paid_on='', paid_amount=0.0,
                     written_off=0.0)
            story = st_cl and s['client']['client_id'] == st_cl and TODAY - day(84) <= s['date'] <= TODAY - day(57)
            if story:
                sub = s['date'] + day(2); den = sub + day(12)
                x.update(submitted_on=iso(sub), status='Denied', denial_reason='Needs pre-approval', denied_on=iso(den)); x['_story'] = True; out.append(x); continue
            u = r.random()
            if u < p['deny']:
                den = sub + day(r.randint(7, 18)); reason = _wchoice(r, DENIAL_REASONS, [30, 12, 10, 12, 8, 28])
                if den > TODAY: out.append(x); continue
                x.update(status='Denied', denial_reason=reason, denied_on=iso(den))
                if reason != 'Duplicate claim' and r.random() < .75:
                    rs = den + day(r.randint(3, 15))
                    if rs <= TODAY:
                        x['resubmitted_on'] = iso(rs); pd = rs + day(r.randint(p['days_lo'], p['days_hi']) // 2 + 5)
                        if pd <= TODAY:
                            if r.random() < .86: x.update(status='Paid', paid_on=iso(pd), paid_amount=amt)
                            else: x.update(status='Written off', written_off=amt)
                        else: x['status'] = 'Resubmitted'
                elif den + day(30) <= TODAY: x.update(status='Written off', written_off=amt)
            else:
                pd = sub + day(r.randint(p['days_lo'], p['days_hi']))
                if pd <= TODAY:
                    if u > .955: pa = R2(amt * r.choice([.6, .7, .8, .9])); x.update(status='Partly paid', paid_on=iso(pd), paid_amount=pa, written_off=R2(amt - pa))
                    else: x.update(status='Paid', paid_on=iso(pd), paid_amount=amt)
            out.append(x)
        out.sort(key=lambda x: (x['submitted_on'], x['session_id']))
        for i, x in enumerate(out, 1): x['claim_id'] = 'PC-%04d' % i
        cols = ['claim_id', 'session_id', 'date', 'client_id', 'client', 'payer', 'service', 'clinician', 'amount', 'submitted_on', 'status', 'denial_reason', 'denied_on',
                'resubmitted_on', 'paid_on', 'paid_amount', 'written_off', '_story']
        return [{k: x.get(k, False) if k == '_story' else x[k] for k in cols} for x in out]
    return _raw('claims', f)


def claim_rows(n=None): return _thin(_pub([dict(x) for x in _claims_raw()]), n)


# ------------------------------------------------------------------ client accounts: deposits, invoices, plans, packages, payments, statements
def _accounts():
    def f():
        W = _W(); _packages(); cur = _ms(TODAY)
        byc = {}
        for s in W['sessions']:
            if s['date'] > TODAY or s['status'] not in ('Attended', 'Late cancel', 'No-show') or s['client_amount'] <= 0: continue
            if '_pk' in s and s['status'] == 'Attended': continue
            if _ms(s['date']) >= cur: continue
            byc.setdefault((s['client']['client_id'], _ms(s['date'])), []).append(s)
        cl = {c['client_id']: c for c in W['clients']}
        # deposits
        deps = []
        for c in W['clients']:
            if c['pre'] or c['fee_type'] not in ('Standard', 'Sliding scale'): continue
            ss = c['sessions']; intake = ss[0] if ss else None
            if any(s['status'] == 'Attended' for s in ss if s['date'] <= TODAY): stt = 'Applied'
            elif intake is None or intake['date'] > TODAY: stt = 'Held'
            elif intake['status'] == 'Cancelled': stt = 'Refunded'
            else: stt = 'Kept'
            deps.append(dict(client=c, date=c['booked_on'], amount=DEPOSIT, status=stt))
        dep_by = {d['client']['client_id']: d for d in deps}
        # story: a couples client with three unpaid invoices
        cand = []
        for cid, c in cl.items():
            if c['fee_type'] != 'Standard' or c['end'] not in (None, 'future') or c.get('on_hold'): continue
            if all((cid, month_start(k)) in byc for k in (3, 2, 1)): cand.append(cid)
        if not cand:
            cand = [cid for cid, c in cl.items() if c['fee_type'] == 'Standard' and c['end'] in (None, 'future') and all((cid, month_start(k)) in byc for k in (3, 2, 1))]
        story_c = max(sorted(cand), key=lambda cid: sum(s['client_amount'] for k in (3, 2, 1) for s in byc[(cid, month_start(k))])) if cand else None
        invs = []
        for (cid, m), ss in sorted(byc.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            c = cl[cid]; amt = R2(sum(s['client_amount'] for s in ss)); r = rng('inv-%s-%s' % (cid, m))
            iss = add_months(m, 1); due = iss + day(INVOICE_DAYS)
            dep = dep_by.get(cid); dapp = 0.0
            if dep and dep['status'] == 'Applied' and not dep.get('used'): dapp = min(DEPOSIT, amt); dep['used'] = True; dep['applied_on'] = iso(iss)
            x = dict(client=c, month=m, sessions=len(ss), amount=amt, deposit_applied=dapp, issued_on=iss, due_date=due, payments=[], status='Unpaid', habit=c['habit'])
            x['_r'] = r; invs.append(x)
        for d in deps:
            if d['status'] == 'Applied' and not d.get('used'): d['status'] = 'Held'
        # payment timing
        for x in invs:
            r = x['_r']; c = x['client']; due_amt = R2(x['amount'] - x['deposit_applied'])
            if due_amt <= 0: x['status'] = 'Paid'; x['paid_on'] = iso(x['issued_on']); continue
            if story_c and c['client_id'] == story_c and x['month'] >= month_start(3): x['status'] = 'Unpaid'; x['_story'] = True; continue
            lo, hi = {'Prompt': (0, 3), 'Normal': (4, 14), 'Slow': (15, 35), 'Very slow': (28, 46)}[x['habit']]
            pd = x['issued_on'] + day(r.randint(lo, hi))
            if x['habit'] in ('Prompt', 'Normal') and r.random() < .05:
                p1 = x['issued_on'] + day(r.randint(lo, hi)); p2 = p1 + day(r.randint(10, 25)); half = R2(due_amt / 2)
                if p1 <= TODAY: x['payments'].append((p1, half))
                if p2 <= TODAY: x['payments'].append((p2, R2(due_amt - half)))
            elif pd <= TODAY: x['payments'].append((pd, due_amt))
            paid = R2(sum(a for _, a in x['payments']))
            x['status'] = 'Paid' if paid >= due_amt - .005 else ('Part paid' if paid > 0 else 'Unpaid')
        # payment plans: slow payers whose invoices were moved onto monthly instalments
        rp = rng('plans'); plans = []
        slow = sorted({x['client']['client_id'] for x in invs if x['habit'] in ('Slow', 'Very slow')})
        used = set([story_c])
        cands = []
        for cid in slow:
            xs = [x for x in invs if x['client']['client_id'] == cid]
            if len(xs) >= 4 and cid not in used and xs[0]['client']['fee_type'] in ('Standard', 'Sliding scale') and sum(x['amount'] for x in xs[-3:]) >= 300: cands.append((cid, xs))
        rp.shuffle(cands)
        for j, (cid, xs) in enumerate(cands[:12]):
            pick = xs[-3:] if j < 3 else xs[1:3]
            if j >= 3 and len(xs) >= 6: pick = xs[2:5]
            bal = R2(sum(x['amount'] - x['deposit_applied'] for x in pick))
            if bal <= 0: continue
            start = pick[-1]['due_date'] + day(7)
            if start > TODAY - day(10): start = TODAY - day(rp.randint(20, 40))
            ninst = max(3, int(math.ceil(bal / 160.0))); inst = R2(bal / ninst)
            dates = [add_months(start, k) for k in range(ninst)]
            late = j == 1
            paid_dates = [d for d in dates if d <= TODAY]
            if late and len(paid_dates) >= 2: paid_dates = paid_dates[:-1]
            for x in pick: x['payments'] = []; x['plan'] = True
            pl = dict(client=xs[0]['client'], start=start, balance=bal, instalments=ninst, instalment=inst, dates=dates, paid_dates=paid_dates, invoices=pick)
            pl['status'] = 'Completed' if len(paid_dates) == ninst else ('Late' if late else 'On track')
            for x in pick: x['status'] = 'Paid' if pl['status'] == 'Completed' else 'On plan'; x['paid_on'] = iso(paid_dates[-1]) if pl['status'] == 'Completed' else ''
            plans.append(pl)
        # written off: a few small last invoices of clients who stopped replying
        lastinv = {}
        for x in invs:
            c = x['client']
            if c['end_reason'] == 'No contact' and c['habit'] in ('Slow', 'Very slow', 'Normal') and not x.get('plan') and not x.get('_story') and x['issued_on'] < TODAY - day(60):
                lastinv[c['client_id']] = x
        for cid in sorted(lastinv)[:12]:
            x = lastinv[cid]; x['payments'] = []; x['status'] = 'Written off'; x['paid_on'] = ''
        for x in invs:
            if x['status'] in ('Paid', 'Part paid') and x['payments']: x['paid_on'] = iso(x['payments'][-1][0])
            x.setdefault('paid_on', '')
            if x['status'] in ('Unpaid', 'Written off', 'On plan'): x.setdefault('paid_on', '')
        invs.sort(key=lambda x: (x['issued_on'], x['client']['client_id']))
        for i, x in enumerate(invs, 1): x['invoice_id'] = 'IV-%04d' % i
        plans.sort(key=lambda p: (p['start'], p['client']['client_id']))
        for i, p in enumerate(plans, 1): p['plan_id'] = 'PP-%02d' % i
        deps.sort(key=lambda d: (d['date'], d['client']['client_id']))
        for i, d in enumerate(deps, 1): d['deposit_id'] = 'DP-%04d' % i
        return dict(invoices=invs, plans=plans, deposits=deps, story_client=story_c)
    return _raw('acc', f)


def invoice_rows(n=None):
    def f():
        out = []
        for x in _accounts()['invoices']:
            c = x['client']; paid = R2(sum(a for _, a in x['payments'])) if x['status'] != 'On plan' else 0.0
            if x['status'] == 'Paid' and not x['payments']: paid = R2(x['amount'] - x['deposit_applied'])
            out.append(dict(invoice_id=x['invoice_id'], month=iso(x['month']), client_id=c['client_id'], client=c['client'], fee_type=c['fee_type'], clinician=c['clinician'],
                            sessions=x['sessions'], amount=x['amount'], deposit_applied=x['deposit_applied'], amount_due=R2(x['amount'] - x['deposit_applied']), issued_on=iso(x['issued_on']),
                            due_date=iso(x['due_date']), paid_amount=paid, paid_on=x['paid_on'], method=c['method'], status=x['status'], _story=x.get('_story', False)))
        return out
    return _thin(_pub(_cached('inv', f)), n)


def payment_plan_rows(n=None):
    def f():
        out = []
        for p in _accounts()['plans']:
            nxt = [d for d in p['dates'] if d not in p['paid_dates']]
            out.append(dict(plan_id=p['plan_id'], client_id=p['client']['client_id'], client=p['client']['client'], start_date=iso(p['start']), balance=p['balance'],
                            instalments=p['instalments'], instalment=p['instalment'], paid_instalments=len(p['paid_dates']), paid_amount=R2(p['instalment'] * len(p['paid_dates'])),
                            next_due=iso(nxt[0]) if nxt else '', invoices=', '.join(x['invoice_id'] for x in p['invoices']), status=p['status']))
        return out
    return _thin(_cached('plans', f), n)


def deposit_rows(n=None):
    def f():
        return [dict(deposit_id=d['deposit_id'], date=d['date'], client_id=d['client']['client_id'], client=d['client']['client'], amount=d['amount'],
                     applied_on=d.get('applied_on', '') if d['status'] == 'Applied' else '', status=d['status'] if not (d['status'] == 'Applied' and not d.get('applied_on')) else 'Held')
                for d in _accounts()['deposits']]
    return _thin(_cached('dep', f), n)


def package_rows(n=None):
    def f():
        out = []
        for pk in _packages():
            exp = add_months(pk['bought_on'], 6)
            st = 'Used up' if pk['used_past'] >= pk['sessions'] else ('Expired' if exp < TODAY else 'Active')
            if st == 'Active' and pk['client']['end'] not in (None, 'future') and exp < TODAY: st = 'Expired'
            out.append(dict(package_id=pk['package_id'], client_id=pk['client']['client_id'], client=pk['client']['client'], kind=pk['kind'], sessions=pk['sessions'], price=pk['price'],
                            bought_on=iso(pk['bought_on']), used=pk['used_past'], expires_on=iso(exp), status=st))
        return [x for x in out if x['bought_on'] <= iso(TODAY)]
    return _thin(_cached('pkr', f), n)


def client_statement_rows(n=None):
    def f():
        out = []
        for x in invoice_rows():
            c = _clmap()[x['client_id']]
            if c['claim_back'] != 'Yes' or x['status'] not in ('Paid', 'Part paid'): continue
            out.append(dict(month=x['month'], client_id=x['client_id'], client=x['client'], sessions=x['sessions'], amount_paid=x['paid_amount'] or x['amount'],
                            issued_on=x['paid_on'] or x['issued_on'], invoice_id=x['invoice_id']))
        out.sort(key=lambda x: (x['issued_on'], x['client_id']))
        for i, x in enumerate(out, 1): x['statement_id'] = 'CS-%04d' % i
        return [dict(statement_id=x.pop('statement_id'), **x) for x in out]
    return _thin(_cached('cst', f), n)


def _clmap(): return _raw('clmap', lambda: {c['client_id']: c for c in _W()['clients']})


def group_rows(n=None): return _thin(_cached('grp', lambda: _groups()[0]), n)
def group_signup_rows(n=None): return _thin(_cached('gsu', lambda: _groups()[1]), n)


_GRUNS = [('Parenting skills', 'Sofia Marchetti', '', 'Family Room', 2, 18, -680), ('Couples communication', 'Amira Lindqvist', 'Sofia Marchetti', 'Family Room', 5, 14, -640),
          ('Stress skills', 'Daniel Okoye', '', 'Family Room', 0, 18, -600), ('Child social skills', 'Kenji Watanabe', '', 'Play Room', 5, 13, -560),
          ('Grief support', 'Amira Lindqvist', '', 'Family Room', 1, 18, -500), ('Couples communication', 'Amira Lindqvist', 'Sofia Marchetti', 'Family Room', 5, 14, -450),
          ('Parenting skills', 'Sofia Marchetti', 'Kenji Watanabe', 'Family Room', 2, 18, -420), ('Stress skills', 'Daniel Okoye', '', 'Family Room', 0, 18, -330),
          ('Child social skills', 'Kenji Watanabe', 'Priya Raman', 'Play Room', 5, 13, -300), ('Teen confidence', 'Lucas Moreau', 'Kenji Watanabe', 'Family Room', 4, 17, -270),
          ('Grief support', 'Amira Lindqvist', '', 'Family Room', 1, 18, -230), ('Couples communication', 'Amira Lindqvist', 'Sofia Marchetti', 'Family Room', 5, 14, -210),
          ('Parenting skills', 'Sofia Marchetti', 'Kenji Watanabe', 'Family Room', 2, 18, -180), ('Teen confidence', 'Lucas Moreau', '', 'Family Room', 4, 17, -110),
          ('Stress skills', 'Daniel Okoye', 'Lucas Moreau', 'Family Room', 0, 18, -100), ('Child social skills', 'Kenji Watanabe', 'Priya Raman', 'Play Room', 5, 13, -60),
          ('Couples communication', 'Amira Lindqvist', 'Sofia Marchetti', 'Family Room', 5, 14, -40), ('Stress skills', 'Daniel Okoye', '', 'Family Room', 0, 18, -24),
          ('Parenting skills', 'Sofia Marchetti', '', 'Family Room', 2, 18, 20), ('Grief support', 'Amira Lindqvist', '', 'Family Room', 1, 18, 55)]
_PROG = {p['program']: p for p in programs}


def _hour_cost(nm):
    p = staff_by_name[nm]
    if p['pay_type'] == 'Salary': return p['monthly_salary'] * (1 + EMPLOYER_COST_PCT) / (p['hours_week'] * 4.33)
    return 0.0


def _groups():
    def f():
        r = rng('groups'); out = []; sig = []
        for i, (prog, fac, co, room, wd, hr, off) in enumerate(_GRUNS, 1):
            P = _PROG[prog]; start = TODAY + day(off); start = start + day((wd - start.weekday()) % 7); end = start + day(7 * (P['weeks'] - 1))
            cancelled = off == -110
            if cancelled: st = 'Cancelled'
            elif end < TODAY: st = 'Completed'
            elif start <= TODAY: st = 'Running'
            else: st = 'Open for sign-up' if (start - TODAY).days <= 30 else 'Planned'
            met = P['weeks'] if st == 'Completed' else (((TODAY - start).days // 7 + 1) if st == 'Running' else 0)
            if cancelled: nsig = 2
            elif st == 'Planned': nsig = 2
            elif st == 'Open for sign-up': nsig = 5
            else: nsig = max(3, min(P['capacity'], int(round(P['capacity'] * r.uniform(.55, 1.0)))))
            gid = 'GR-%02d' % i; rev = 0.0
            for j in range(nsig):
                fs, ls = _G[r.randrange(len(_G))]; nm = '%s %s' % (r.choice(fs), r.choice(ls))
                if prog == 'Couples communication': nm = '%s and %s %s' % (r.choice(fs), r.choice(_G[r.randrange(len(_G))][0]), ls)
                so = start - day(r.randint(3, 40)); so = min(so, TODAY - day(r.randint(0, 6))) if start > TODAY else so
                paid = P['fee'] if r.random() > .15 else R2(P['fee'] * .7)
                if cancelled: sst = 'Refunded'; att = 0
                elif st in ('Planned', 'Open for sign-up'): sst = 'Signed up'; att = 0
                elif st == 'Running':
                    drop = r.random() < .1; sst = 'Dropped out' if drop else 'Attending'; att = min(met, 1 + r.randint(0, 1)) if drop else max(0, met - r.randint(0, 1))
                else:
                    drop = r.random() < .12; sst = 'Dropped out' if drop else 'Completed'; att = r.randint(1, 3) if drop else P['weeks'] - r.randint(0, 2)
                if sst != 'Refunded': rev += paid
                sig.append(dict(group_id=gid, program=prog, name=nm, phone=fake_phone(7000 + 20 * i + j), signed_on=iso(so), paid_amount=paid, paid_on=iso(so),
                                sessions_attended=att, status=sst))
            meet_cost = lambda nm_: 0.0 if not nm_ else (ASSOCIATE_RATE if nm_ == ASSOCIATE else _hour_cost(nm_) * 2)
            fpay = R2(P['weeks'] * (meet_cost(fac) + meet_cost(co)))
            if fac in CONTRACTORS: fpay = R2(fpay + rev * .4)
            if co in CONTRACTORS: fpay = R2(fpay + rev * .2)
            if cancelled: fpay = 0.0; rev = 0.0
            out.append(dict(group_id=gid, program=prog, facilitator=fac, co_facilitator=co, room=room, start_date=iso(start), weekday=WEEKDAYS[wd], start_time='%02d:00' % hr,
                            weeks=P['weeks'], capacity=P['capacity'], fee=P['fee'], signups=sum(1 for x in sig if x['group_id'] == gid and x['status'] != 'Refunded'),
                            revenue=R2(rev), facilitator_pay=fpay, materials=R2(r.choice([40, 60, 85, 110, 140])), marketing=R2(r.choice([0, 60, 90, 120, 160])),
                            room_cost=R2(ROOM_COST_HOUR * 2 * (met if st != 'Planned' else 0)) if not cancelled else 0.0, meetings_held=met if not cancelled else 0, status=st))
        sig.sort(key=lambda x: (x['signed_on'], x['group_id']))
        for i, x in enumerate(sig, 1): x['signup_id'] = 'GS-%04d' % i
        sig = [dict(signup_id=x.pop('signup_id'), **x) for x in sig]
        return out, sig
    return _raw('groups', f)


# ------------------------------------------------------------------ payments (client side money in)
def payment_rows(n=None):
    def f():
        A = _accounts(); out = []
        for x in A['invoices']:
            c = x['client']
            if x['status'] == 'On plan' or x.get('plan'): continue
            for d, a in x['payments']: out.append(dict(date=iso(d), client_id=c['client_id'], client=c['client'], kind='Invoice', ref=x['invoice_id'], method=c['method'], amount=a))
        for p in A['plans']:
            for d in p['paid_dates']: out.append(dict(date=iso(d), client_id=p['client']['client_id'], client=p['client']['client'], kind='Plan instalment', ref=p['plan_id'], method='Bank transfer', amount=p['instalment']))
        for d in A['deposits']:
            if to_date(d['date']) <= TODAY: out.append(dict(date=d['date'], client_id=d['client']['client_id'], client=d['client']['client'], kind='Deposit', ref=d['deposit_id'], method='Card', amount=d['amount']))
        for pk in _packages():
            if pk['bought_on'] <= TODAY: out.append(dict(date=iso(pk['bought_on']), client_id=pk['client']['client_id'], client=pk['client']['client'], kind='Package', ref=pk['package_id'],
                                                        method=pk['client']['method'] if pk['client']['method'] != 'Cash' else 'Card', amount=pk['price']))
        for g in group_signup_rows():
            if g['status'] != 'Refunded' and g['paid_on'] <= iso(TODAY): out.append(dict(date=g['paid_on'], client_id='', client=g['name'], kind='Group fee', ref=g['group_id'], method='Card', amount=g['paid_amount']))
        out.sort(key=lambda x: (x['date'], x['kind'], x['ref']))
        for i, x in enumerate(out, 1): x['payment_id'] = 'PM-%04d' % i; x['card_fee'] = R2(x['amount'] * CARD_FEE_PCT) if x['method'] == 'Card' else 0.0
        cols = ['payment_id', 'date', 'client_id', 'client', 'kind', 'ref', 'method', 'amount', 'card_fee']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('pay', f), n)


# ------------------------------------------------------------------ clinical admin: plan reviews, outcome scores, discharges
def _plan_reviews_raw():
    def f():
        W = _W(); out = []; r = rng('plans-rev')
        overdue_left = 5
        for c in sorted(W['clients'], key=lambda c: c['client_id']):
            att = [s for s in c['sessions'] if s['status'] == 'Attended' and s['date'] <= TODAY]
            if not att and c['pre'] is False: continue
            start = to_date(c['first_session']); endd = c['end'] if c['end'] not in (None, 'future') else None
            k = 1; score = c['intake_score']
            while True:
                due = start + day(REVIEW_EVERY_DAYS * k)
                if endd and due > endd: break
                if due > TODAY + day(60): break
                if due < HISTORY_START - day(30): k += 1; score = max(4, int(round(score * r.uniform(.8, .95)))); continue
                rec = dict(client_id=c['client_id'], client=c['client'], clinician=c['clinician'], review_no=k, due_date=iso(due), reviewed_on='', score='')
                if due <= TODAY:
                    lag = r.randint(-10, 12); rv = due + day(lag)
                    late_ok = c['end'] in (None, 'future') and not c.get('on_hold') and (TODAY - due).days > 10 and overdue_left > 0 and r.random() < .05
                    if late_ok: overdue_left -= 1
                    elif rv <= TODAY:
                        score = max(3, int(round(score * r.uniform(.72, .97)))); rec.update(reviewed_on=iso(rv), score=score)
                out.append(rec); k += 1
                if due > TODAY: break
            c['score'] = score
        out.sort(key=lambda x: (x['due_date'], x['client_id']))
        for i, x in enumerate(out, 1): x['review_id'] = 'PL-%04d' % i
        return [dict(review_id=x.pop('review_id'), **x) for x in out]
    return _raw('prev', f)


def plan_review_rows(n=None): return _thin([dict(x) for x in _plan_reviews_raw()], n)


def outcome_rows(n=None):
    def f():
        W = _W(); out = []
        for c in W['clients']:
            ss = [s for s in c['sessions'] if s['date'] <= TODAY and s['status'] == 'Attended']
            if not c['pre'] and ss and ss[0]['service'] == 'Intake assessment' and ss[0]['date'] >= HISTORY_START:
                out.append(dict(date=iso(ss[0]['date']), client_id=c['client_id'], client=c['client'], clinician=c['clinician'], point='Intake', score=c['intake_score']))
        for x in _plan_reviews_raw():
            if x['reviewed_on']: out.append(dict(date=x['reviewed_on'], client_id=x['client_id'], client=x['client'], clinician=x['clinician'], point='Review', score=x['score']))
        for d in discharge_rows():
            if d['final_score'] != '': out.append(dict(date=d['date'], client_id=d['client_id'], client=d['client'], clinician=d['clinician'], point='Discharge', score=d['final_score']))
        out.sort(key=lambda x: (x['date'], x['client_id'], OUTCOME_POINTS.index(x['point'])))
        for i, x in enumerate(out, 1): x['score_id'] = 'OS-%04d' % i
        return [dict(score_id=x.pop('score_id'), **x) for x in out]
    return _thin(_cached('out', f), n)


def discharge_rows(n=None):
    def f():
        out = []; cm = _clmap()
        for x in client_rows():
            if not x['discharge_date'] or x['discharge_date'] < iso(HISTORY_START): continue
            c = cm[x['client_id']]; r = rng('dc' + x['client_id'])
            ref = r.choice(REFERRED_TO) if x['discharge_reason'] == 'Referred out' else ''
            _plan_reviews_raw()
            fin = max(2, int(round(c['score'] * r.uniform(.75, .95)))) if x['discharge_reason'] == 'Goals met' else ''
            out.append(dict(date=x['discharge_date'], client_id=x['client_id'], client=x['client'], clinician=x['clinician'], service=x['service'], reason=x['discharge_reason'],
                            sessions=x['sessions_attended'], referred_to=ref, letter_sent='Yes' if r.random() < .82 or ref else 'No', final_score=fin))
        out.sort(key=lambda x: (x['date'], x['client_id']))
        for i, x in enumerate(out, 1): x['discharge_id'] = 'DC-%03d' % i
        return [dict(discharge_id=x.pop('discharge_id'), **x) for x in out]
    return _thin(_cached('dis', f), n)


# ------------------------------------------------------------------ supervision, continuing education, renewals
def supervision_rows(n=None):
    def f():
        W = _W(); r = rng('sup'); out = []; absent = W['absent']
        for ws in W['weeks']:
            if ws > TODAY or _closed(ws): continue
            if to_date(staff_by_name[ASSOCIATE]['start']) <= ws and (ASSOCIATE, ws) not in absent and (OWNER, ws) not in absent and ws + day(1) <= TODAY:
                out.append(dict(date=iso(ws + day(1)), supervisee=ASSOCIATE, supervisor=OWNER, kind='Individual', hours=1.0, cost=0.0))
        for k in range(23, -1, -1):
            m = month_start(k); wed = m + day((2 - m.weekday()) % 7)
            if wed <= TODAY:
                who = [nm for nm in CLINICIANS if to_date(staff_by_name[nm]['start']) <= wed]
                for nm in who: out.append(dict(date=iso(wed), supervisee=nm, supervisor=SUPERVISOR, kind='Group', hours=1.5, cost=R2(180.0 / len(who))))
            d1 = m + day(9 + r.randint(0, 6))
            if d1 <= TODAY:
                out.append(dict(date=iso(d1), supervisee=OWNER, supervisor=SUPERVISOR, kind='Individual', hours=1.5, cost=150.0))
                for nm in ('Daniel Okoye', 'Sofia Marchetti'): out.append(dict(date=iso(d1 + day(1)), supervisee=nm, supervisor=OWNER, kind='Individual', hours=1.0, cost=0.0))
                for nm in CONTRACTORS:
                    if to_date(staff_by_name[nm]['start']) <= d1: out.append(dict(date=iso(d1 + day(3)), supervisee=nm, supervisor='Peer group', kind='Peer consultation', hours=1.0, cost=0.0))
        out = [x for x in out if x['date'] <= iso(TODAY)]
        out.sort(key=lambda x: (x['date'], CLINICIANS.index(x['supervisee'])))
        for i, x in enumerate(out, 1): x['supervision_id'] = 'SU-%04d' % i
        return [dict(supervision_id=x.pop('supervision_id'), **x) for x in out]
    return _thin(_cached('supv', f), n)


_CE_TITLES = {'Amira Lindqvist': ['Working with couples', 'Supervision skills', 'Ethics refresher', 'Grief and loss', 'Group facilitation', 'Record keeping and privacy'],
              'Daniel Okoye': ['Working with young people', 'Online session skills', 'Ethics refresher', 'Brief work skills', 'Record keeping and privacy'],
              'Sofia Marchetti': ['Family sessions in practice', 'Working with couples', 'Parenting groups', 'Ethics refresher', 'Online session skills'],
              'Kenji Watanabe': ['Play-based skills', 'Family sessions in practice', 'Working with young people', 'Ethics refresher', 'School liaison'],
              'Priya Raman': ['Speech and language update', 'Behaviour support planning', 'Working with parents', 'Ethics refresher', 'Play-based skills'],
              'Lucas Moreau': ['Core counselling skills', 'Working with young people', 'Record keeping and privacy', 'Ethics refresher', 'Online session skills']}


def ce_rows(n=None):
    def f():
        r = rng('ce'); out = []
        for nm in CLINICIANS:
            st = max(to_date(staff_by_name[nm]['start']), HISTORY_START)
            d = st + day(r.randint(10, 40))
            while d <= TODAY:
                kind = _wchoice(r, CE_KINDS, [30, 30, 8, 14, 9, 9]); hrs = {'Workshop': r.choice([3, 4, 6]), 'Online course': r.choice([2, 3, 4, 5]), 'Conference': r.choice([8, 12]),
                                                                            'Training day': 6, 'Reading group': 1.5, 'Peer learning': 2}[kind]
                cost = {'Workshop': r.choice([90, 120, 160]), 'Online course': r.choice([45, 60, 85]), 'Conference': r.choice([280, 420]), 'Training day': r.choice([150, 190]),
                        'Reading group': 0, 'Peer learning': 0}[kind]
                out.append(dict(date=iso(d), clinician=nm, kind=kind, title=r.choice(_CE_TITLES[nm]), hours=float(hrs), cost=float(cost),
                                paid_by='Clinician' if nm in CONTRACTORS else 'Practice', certificate='Yes' if kind not in ('Reading group', 'Peer learning') else 'No'))
                d += day(r.randint(30, 75))
        rec = [x for x in out if x['date'] >= ago(30)]
        if not rec: out.append(dict(date=ago(6), clinician='Daniel Okoye', kind='Online course', title='Online session skills', hours=3.0, cost=60.0, paid_by='Practice', certificate='Yes'))
        out.sort(key=lambda x: (x['date'], x['clinician']))
        for i, x in enumerate(out, 1): x['ce_id'] = 'CE-%03d' % i
        return [dict(ce_id=x.pop('ce_id'), **x) for x in out]
    return _thin(_cached('ce', f), n)


def renewal_rows(n=None):
    def f():
        r = rng('ren'); out = []
        items = []
        for nm in CLINICIANS:
            items += [(nm, 'Registration', 12, r.choice([180, 220, 260, 310])), (nm, 'Liability insurance', 12, r.choice([240, 290, 340, 410])), (nm, 'Background check', 36, 60)]
            if nm != ASSOCIATE: items.append((nm, 'Membership fee', 12, r.choice([150, 190, 240])))
        items += [(COORDINATOR, 'First aid course', 24, 95), ('Practice', 'Practice insurance', 12, 2760), ('Practice', 'Room lease', 36, 0), ('Practice', 'Privacy policy review', 12, 0),
                  (COORDINATOR, 'Background check', 36, 60)]
        for holder, item, every, cost in items:
            nxt = TODAY + day(r.randint(20, 330))
            if holder == 'Kenji Watanabe' and item == 'Liability insurance': nxt = TODAY + day(12)
            if (TODAY - nxt).days > -45 and not (holder == 'Kenji Watanabe' and item == 'Liability insurance'): nxt = nxt + day(40)
            dues = [nxt]
            while True:
                p = add_months(dues[0], -every)
                if p < HISTORY_START - day(20): break
                dues.insert(0, p)
            for dd in dues:
                if dd <= TODAY: ren = dd - day(r.randint(3, 25))
                elif (dd - TODAY).days <= 60 and not (holder == 'Kenji Watanabe' and item == 'Liability insurance'): ren = min(TODAY - day(1), dd - day(r.randint(5, 20)))
                else: ren = None
                paid_by = 'Clinician' if holder in CONTRACTORS and item in ('Registration', 'Liability insurance', 'Membership fee') else 'Practice'
                out.append(dict(holder=holder, item=item, every_months=every, due_date=iso(dd), renewed_on=iso(ren) if ren else '', cost=float(cost), paid_by=paid_by))
        out.sort(key=lambda x: (x['due_date'], x['holder'], x['item']))
        for i, x in enumerate(out, 1): x['renewal_id'] = 'RN-%03d' % i
        return [dict(renewal_id=x.pop('renewal_id'), **x) for x in out]
    return _thin(_cached('ren', f), n)


# ------------------------------------------------------------------ pay, productivity, service and room months
def _months24(): return [month_start(k) for k in range(23, -1, -1)]


def _last_weekday(m):
    d = _eom(m)
    while d.weekday() > 4: d -= day(1)
    return d


def clinician_pay_rows(n=None):
    def f():
        W = _W(); agg = {}
        for s in W['sessions']:
            k = (s['clinician'], _ms(s['date'])); a = agg.setdefault(k, dict(att=0, hrs=0.0, fees=0.0, pay=0.0))
            if s['date'] > TODAY: continue
            if s['status'] == 'Attended': a['att'] += 1; a['hrs'] += s['minutes'] / 60.0
            a['fees'] += s['charge']; a['pay'] += s['clinician_pay']
        out = []
        for m in _months24():
            for p in staff[1:]:
                st = to_date(p['start'])
                if st > _eom(m): continue
                a = agg.get((p['name'], m), dict(att=0, hrs=0.0, fees=0.0, pay=0.0)); emp = 0.0
                if p['pay_type'] == 'Salary': amt = p['monthly_salary']; emp = R2(amt * EMPLOYER_COST_PCT); pd = add_months(m, 1) + day(9)
                elif p['pay_type'] == 'Percentage split': amt = R2(a['pay']); pd = add_months(m, 1) + day(9)
                elif p['pay_type'] == 'Per session': amt = R2(ASSOCIATE_RATE * a['att']); pd = add_months(m, 1) + day(19)
                else:
                    hrs = R2(p['hours_week'] * calendar.monthrange(m.year, m.month)[1] / 7.0); a = dict(a, hrs=hrs); amt = R2(hrs * p['hourly_rate']); emp = R2(amt * EMPLOYER_COST_PCT); pd = add_months(m, 1) + day(9)
                status = 'Paid' if pd <= TODAY else ('Accruing' if m == _ms(TODAY) else 'Due')
                if status == 'Accruing' and p['pay_type'] in ('Salary', 'Hourly'):       # accrued to date
                    f_ = TODAY.day / float(calendar.monthrange(m.year, m.month)[1]); amt = R2(amt * f_); emp = R2(emp * f_)
                    if p['pay_type'] == 'Hourly': a = dict(a, hrs=R2(a['hrs'] * f_))
                out.append(dict(month=iso(m), person=p['name'], pay_type=p['pay_type'], sessions=a['att'], hours=R2(a['hrs']), fees_charged=R2(a['fees']), split_pct=p['split_pct'],
                                amount=amt, employer_cost=emp, paid_on=iso(pd) if pd <= TODAY else '', status=status))
        for i, x in enumerate(out, 1): x['pay_id'] = 'PY-%03d' % i
        return [dict(pay_id=x.pop('pay_id'), **x) for x in out]
    return _thin(_cached('cpay', f), n)


def clinician_week_counts(week):
    """sessions booked (not cancelled) per clinician in the week starting on that Monday (iso)"""
    out = {nm: 0 for nm in CLINICIANS}
    for s in _W()['sessions']:
        if iso(week_start(s['date'])) == week and s['status'] != 'Cancelled': out[s['clinician']] += 1
    return out


def clinician_month_rows(n=None):
    def f():
        W = _W(); agg = {}
        for s in W['sessions']:
            k = (s['clinician'], _ms(s['date'])); a = agg.setdefault(k, dict(booked=0, attended=0, cancelled=0, late=0, noshow=0, hours=0.0, revenue=0.0, new=0, late_notes=0))
            a['booked'] += 1
            if s['status'] == 'Attended':
                a['attended'] += 1; a['hours'] += s['minutes'] / 60.0
                if s['service'] == 'Intake assessment': a['new'] += 1
                if s['note_on_time'] == 'No' or (s['note_done_on'] == '' and s['date'] <= TODAY - day(NOTE_DUE_DAYS + 1)): a['late_notes'] += 1
            elif s['status'] == 'Cancelled': a['cancelled'] += 1
            elif s['status'] == 'Late cancel': a['late'] += 1
            elif s['status'] == 'No-show': a['noshow'] += 1
            if s['date'] <= TODAY: a['revenue'] += s['charge']
        dis = {}
        for d in discharge_rows(): k = (d['clinician'], _ms(to_date(d['date']))); dis[k] = dis.get(k, 0) + 1
        out = []
        for m in _months24():
            for nm in CLINICIANS:
                p = staff_by_name[nm]
                if to_date(p['start']) > _eom(m): continue
                mon = [m + day(i) for i in range(calendar.monthrange(m.year, m.month)[1]) if (m + day(i)).weekday() == 0]
                wk = sum(1 for w in mon if (nm, w) not in W['absent'] and not _closed(w) and w >= week_start(to_date(p['start'])))
                a = agg.get((nm, m), dict(booked=0, attended=0, cancelled=0, late=0, noshow=0, hours=0.0, revenue=0.0, new=0, late_notes=0))
                out.append(dict(month=iso(m), clinician=nm, working_weeks=wk, capacity=wk * p['session_cap'], booked=a['booked'], attended=a['attended'], cancelled=a['cancelled'],
                                late_cancels=a['late'], no_shows=a['noshow'], clinical_hours=R2(a['hours']), revenue=R2(a['revenue']), new_clients=a['new'],
                                discharges=dis.get((nm, m), 0), late_notes=a['late_notes'], basis='Month to date' if m == _ms(TODAY) else 'Full month'))
        for i, x in enumerate(out, 1): x['row_id'] = 'CM-%04d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('cmon', f), n)


def service_month_rows(n=None):
    def f():
        W = _W(); agg = {}
        for s in W['sessions']:
            if s['date'] > TODAY: continue
            a = agg.setdefault((s['service'], _ms(s['date'])), dict(booked=0, sessions=0, revenue=0.0, pay=0.0, room=0.0, other=0.0))
            if s['status'] != 'Cancelled': a['booked'] += 1
            if s['status'] == 'Attended': a['sessions'] += 1
            a['revenue'] += s['charge']; a['pay'] += s['clinician_pay']; a['room'] += s['room_cost']; a['other'] += s['other_cost']
        for g in group_rows():
            if g['status'] in ('Planned', 'Open for sign-up', 'Cancelled'): continue
            a = agg.setdefault(('Group program', _ms(to_date(g['start_date']))), dict(booked=0, sessions=0, revenue=0.0, pay=0.0, room=0.0, other=0.0))
            a['booked'] += g['meetings_held']; a['sessions'] += g['meetings_held']; a['revenue'] += g['revenue']; a['pay'] += g['facilitator_pay']; a['room'] += g['room_cost']
            a['other'] += g['materials'] + g['marketing']
        out = []
        for m in _months24():
            for sv in SERVICES:
                a = agg.get((sv, m))
                if not a: continue
                out.append(dict(month=iso(m), service=sv, booked=a['booked'], sessions=a['sessions'], revenue=R2(a['revenue']), clinician_pay=R2(a['pay']), room_cost=R2(a['room']),
                                other_cost=R2(a['other'])))
        for i, x in enumerate(out, 1): x['row_id'] = 'SM-%04d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('smon', f), n)


def service_profit(service, months=12):
    """profit of one service over the last `months` complete months: revenue - clinician pay - room cost - other cost"""
    ms = {iso(month_start(k)) for k in range(1, months + 1)}; t = dict(revenue=0.0, clinician_pay=0.0, room_cost=0.0, other_cost=0.0, sessions=0)
    for x in service_month_rows():
        if x['service'] == service and x['month'] in ms:
            for k in t: t[k] += x[k]
    t['profit'] = R2(t['revenue'] - t['clinician_pay'] - t['room_cost'] - t['other_cost'])
    return t


def sublet_rows(n=None):
    def f():
        r = rng('sublet'); out = []
        for t in tenants:
            for m in _months24():
                if to_date(t['start']) > _eom(m): continue
                dim = calendar.monthrange(m.year, m.month)[1]
                frac = 1.0 if m < _ms(TODAY) else (TODAY.day / float(dim))
                hrs = R2(t['hours_week'] * dim / 7.0 * r.uniform(.85, 1.05) * frac)
                if (m.month == 12): hrs = R2(hrs * .75)
                inv = add_months(m, 1); pd = inv + day(r.randint(*{'TN-01': (3, 12), 'TN-02': (2, 8), 'TN-03': (19, 27)}[t['tenant_id']]))
                st = 'Accruing' if m == _ms(TODAY) else ('Paid' if pd <= TODAY else 'Invoiced')
                out.append(dict(month=iso(m), tenant=t['name'], kind=t['kind'], room=t['room'], hours=hrs, rate=t['rate'], amount=R2(hrs * t['rate']),
                                invoiced_on=iso(inv) if inv <= TODAY else '', paid_on=iso(pd) if st == 'Paid' else '', status=st))
        out.sort(key=lambda x: (x['month'], x['tenant']))
        for i, x in enumerate(out, 1): x['sublet_id'] = 'SL-%03d' % i
        return [dict(sublet_id=x.pop('sublet_id'), **x) for x in out]
    return _thin(_cached('sub', f), n)


def room_month_rows(n=None):
    def f():
        W = _W(); agg = {}
        for s in W['sessions']:
            if s['room'] == 'Online' or s['status'] == 'Cancelled' or s['date'] > TODAY: continue
            a = agg.setdefault((s['room'], _ms(s['date'])), [0.0, 0]); a[0] += s['minutes'] / 60.0; a[1] += 1
        grp = {}
        for g in group_rows():
            if g['status'] in ('Planned', 'Open for sign-up', 'Cancelled'): continue
            st = to_date(g['start_date'])
            for k in range(g['meetings_held']):
                d = st + day(7 * k); grp[(g['room'], _ms(d))] = grp.get((g['room'], _ms(d)), 0) + 1.5
        sub = {}
        for x in sublet_rows(): sub[(x['room'], x['month'])] = sub.get((x['room'], x['month']), 0) + x['hours']
        out = []
        for m in _months24():
            dim = calendar.monthrange(m.year, m.month)[1]; frac = 1.0 if m < _ms(TODAY) else TODAY.day / float(dim)
            for rm in rooms:
                a = agg.get((rm['room'], m), [0.0, 0])
                out.append(dict(month=iso(m), room=rm['room'], open_hours=R2(rm['open_hours_week'] * dim / 7.0 * frac * (.8 if m.month == 12 else 1)), session_hours=R2(a[0]),
                                sessions=a[1], group_hours=R2(grp.get((rm['room'], m), 0)), sublet_hours=R2(sub.get((rm['room'], iso(m)), 0))))
        for i, x in enumerate(out, 1): x['row_id'] = 'RU-%04d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('rmon', f), n)


# ------------------------------------------------------------------ marketing, expenses, tax, cash
def marketing_rows(n=None):
    def f():
        r = rng('mkt'); out = []; enq = enquiry_rows()
        cnt = {}
        for e in enq:
            k = (e['source'], e['date'][:7]); a = cnt.setdefault(k, [0, 0]); a[0] += 1; a[1] += 1 if e['status'] == 'Booked' else 0
        for m in _months24():
            ym = iso(m)[:7]
            de, dw = cnt.get(('Online directory', ym), [0, 0])
            for j, (desc, cost) in enumerate((('Directory listing 1', 45.0), ('Directory listing 2', 30.0))):
                d = m + day(1 + j)
                if d <= TODAY: out.append(dict(date=iso(d), kind='Online directory', description=desc, cost=cost, enquiries=(de + 1 - j) // 2 if j == 0 else de // 2, clients_won=(dw + 1 - j) // 2 if j == 0 else dw // 2))
            we, ww = cnt.get(('Practice website', ym), [0, 0])
            if m.month in (2, 5, 8, 11) and m + day(12) <= TODAY: out.append(dict(date=iso(m + day(12)), kind='Practice website', description='Website update and new photos', cost=R2(r.choice([150, 220, 380])), enquiries=we, clients_won=ww))
            ke, kw = cnt.get(('Workshop or talk', ym), [0, 0])
            if m.month not in (7, 8, 12):
                kind = ['Workshop', 'Community talk', 'School talk'][m.month % 3]
                d = m + day(r.randint(8, 22))
                if d <= TODAY: out.append(dict(date=iso(d), kind=kind, description={'Workshop': 'Evening workshop on stress at work', 'Community talk': 'Talk at the community centre',
                                                                                      'School talk': 'Talk for parents at a local school'}[kind], cost=R2(r.choice([0, 25, 40, 90, 150])), enquiries=ke, clients_won=kw))
            if m.month % 2 == 0 and m + day(16) <= TODAY:
                pe, pw = cnt.get(('Doctor referral', ym), [0, 0])
                out.append(dict(date=iso(m + day(16)), kind='Referrer visit', description='Visit to a family doctor practice', cost=R2(r.choice([0, 15, 30])), enquiries=r.randint(0, 2), clients_won=r.randint(0, 1)))
            ne, nw = cnt.get(('Past client', ym), [0, 0])
            if m + day(20) <= TODAY and m.month not in (8,): out.append(dict(date=iso(m + day(20)), kind='Newsletter', description='Practice news for referrers and past clients', cost=R2(r.choice([0, 10, 20])), enquiries=ne, clients_won=nw))
            if m.month in (3, 9) and m + day(5) <= TODAY: out.append(dict(date=iso(m + day(5)), kind='Printed flyers', description='Flyers for doctors and schools', cost=R2(r.choice([90, 140, 190])), enquiries=r.randint(1, 4), clients_won=r.randint(0, 2)))
        out.sort(key=lambda x: (x['date'], x['kind']))
        for i, x in enumerate(out, 1): x['campaign_id'] = 'MK-%03d' % i
        return [dict(campaign_id=x.pop('campaign_id'), **x) for x in out]
    return _thin(_cached('mkt', f), n)


def expense_rows(n=None):
    def f():
        r = rng('exp'); out = []
        def add(d, cat, desc, amt, to, method='Bank transfer'):
            if to_date(d) <= TODAY and to_date(d) >= HISTORY_START: out.append(dict(date=iso(d), month=iso(_ms(to_date(d))), category=cat, description=desc, amount=R2(amt), paid_to=to, method=method))
        cardfee = {}
        for p in payment_rows(): cardfee[p['date'][:7]] = cardfee.get(p['date'][:7], 0) + p['card_fee']
        nclin = lambda m: sum(1 for nm in CLINICIANS if to_date(staff_by_name[nm]['start']) <= _eom(m))
        for m in _months24():
            k = (TODAY.year - m.year) * 12 + TODAY.month - m.month
            add(m, 'Rent', 'Practice suite rent', 6600 if k >= 12 else 6800, 'Landlord')
            wf = 1.25 if m.month in (12, 1, 2) else (1.1 if m.month in (7, 8) else 1.0)
            add(m + day(7), 'Utilities', 'Power, water and heating', 380 * wf * r.uniform(.92, 1.08), 'Utility company')
            add(m + day(27), 'Cleaning', 'Evening cleaning, 5 days a week', 640, 'Cleaning service')
            add(m + day(2), 'Practice software', 'Scheduling, billing and records system', 190 + 14 * nclin(m), 'Software provider', 'Card')
            add(m + day(9), 'Phone and internet', 'Phone lines and fibre', 145, 'Phone provider')
            add(m + day(4), 'Insurance', 'Practice and building cover, monthly', 230, 'Insurer')
            add(m + day(14), 'Office supplies', 'Paper, printing and waiting room supplies', r.choice([60, 75, 90, 110, 140]), 'Office supplier', 'Card')
            add(m + day(17), 'Therapy materials', 'Toys, games, cards and worksheets', r.choice([80, 110, 150, 190]) + (60 if to_date(staff_by_name['Priya Raman']['start']) <= m else 0), 'Materials supplier', 'Card')
            add(m + day(19), 'Accounting', 'Bookkeeping and payroll', 380, 'Accountant')
            if m.month in (1, 4, 7, 10): add(m + day(11), 'Practice software', 'IT support visit', r.choice([120, 180, 260]), 'IT support')
            ym = iso(m)[:7]
            if m < _ms(TODAY) or _eom(m) <= TODAY: add(_eom(m), 'Bank and card fees', 'Card fees and account charges', cardfee.get(ym, 0) + 15, 'Payment provider')
        for x in marketing_rows():
            if x['cost'] > 0: add(to_date(x['date']), 'Marketing', x['description'], x['cost'], 'Print shop' if x['kind'] == 'Printed flyers' else ('Directory site' if x['kind'] == 'Online directory' else 'Marketing supplier'), 'Card')
        for x in ce_rows():
            if x['paid_by'] == 'Practice' and x['cost'] > 0: add(to_date(x['date']), 'Training', '%s for %s' % (x['title'], x['clinician']), x['cost'], 'Training provider', 'Card')
        for x in supervision_rows():
            if x['supervisor'] == SUPERVISOR and x['kind'] == 'Individual': add(to_date(x['date']), 'Supervision', 'External supervision for the owner', x['cost'], 'Clinical supervisor')
        seen = set()
        for x in supervision_rows():
            if x['kind'] == 'Group' and x['date'] not in seen: seen.add(x['date']); add(to_date(x['date']), 'Supervision', 'Monthly group supervision', 180, 'Clinical supervisor')
        for x in renewal_rows():
            if x['renewed_on'] and x['paid_by'] == 'Practice' and x['cost'] > 0 and x['item'] != 'Practice insurance':
                add(to_date(x['renewed_on']), 'Insurance' if x['item'] == 'Liability insurance' else 'Professional fees', '%s for %s' % (x['item'], x['holder']), x['cost'],
                    'Insurer' if x['item'] == 'Liability insurance' else 'Professional body')
        out.sort(key=lambda x: (x['date'], x['category'], x['description']))
        for i, x in enumerate(out, 1): x['expense_id'] = 'EX-%04d' % i
        return [dict(expense_id=x.pop('expense_id'), **x) for x in out]
    return _thin(_cached('exp', f), n)


def _pnl():
    def f():
        rev = {}; cost = {}
        for s in _W()['sessions']:
            if s['date'] <= TODAY: rev[_ms(s['date'])] = rev.get(_ms(s['date']), 0) + s['charge']
        for g in group_rows(): m = _ms(to_date(g['start_date'])); rev[m] = rev.get(m, 0) + g['revenue']
        for x in sublet_rows(): m = to_date(x['month']); rev[m] = rev.get(m, 0) + x['amount']
        for x in clinician_pay_rows(): m = to_date(x['month']); cost[m] = cost.get(m, 0) + x['amount'] + x['employer_cost']
        for x in expense_rows(): m = to_date(x['month']); cost[m] = cost.get(m, 0) + x['amount']
        for x in claim_rows():
            if x['written_off']: m = _ms(to_date(x['date'])); rev[m] = rev.get(m, 0) - x['written_off']
        return rev, cost
    return _raw('pnl', f)


def tax_rows(n=None):
    def f():
        rev, cost = _pnl(); out = []
        for m in _months24():
            p = R2(rev.get(m, 0) - cost.get(m, 0)); due = add_months(m, 1) + day(19)
            st = 'Upcoming' if m == _ms(TODAY) else ('Paid' if due <= TODAY else 'Due')
            out.append(dict(month=iso(m), revenue=R2(rev.get(m, 0)), costs=R2(cost.get(m, 0)), profit=p, set_aside_pct=TAX_SET_ASIDE_PCT, set_aside=R2(max(0, p) * TAX_SET_ASIDE_PCT),
                            due_date=iso(due), paid_on=iso(due - day(3)) if st == 'Paid' else '', status=st))
        for i, x in enumerate(out, 1): x['tax_id'] = 'TX-%03d' % i
        return [dict(tax_id=x.pop('tax_id'), **x) for x in out]
    return _thin(_cached('tax', f), n)


def cash_rows(n=None):
    def f():
        pos = {}
        def add(d, k, v):
            if not d or to_date(d) > TODAY: return
            ym = d[:7]; pos.setdefault(ym, {}).setdefault(k, 0.0); pos[ym][k] += v
        for p in payment_rows(): add(p['date'], 'client', p['amount'])
        for c in claim_rows(): add(c['paid_on'], 'payer', c['paid_amount'])
        for x in sublet_rows(): add(x['paid_on'], 'sublet', x['amount'])
        for x in clinician_pay_rows():
            k = 'staff' if x['pay_type'] in ('Salary', 'Hourly') else 'contractors'; add(x['paid_on'], k, x['amount'] + x['employer_cost'])
        for x in expense_rows(): add(x['date'], 'rent' if x['category'] == 'Rent' else 'expenses', x['amount'])
        for x in tax_rows(): add(x['paid_on'], 'tax', x['set_aside'])
        for m in months14():
            for d in (m + day(14), _eom(m)): add(iso(d), 'draw', OWNER_DRAW / 2)
        rows = []
        for m in months14():
            p = pos.get(iso(m)[:7], {})
            rows.append(dict(month=iso(m), opening=0.0, client_payments=R2(p.get('client', 0)), payer_payments=R2(p.get('payer', 0)), sublet_income=R2(p.get('sublet', 0)),
                             staff_pay=R2(p.get('staff', 0)), contractor_pay=R2(p.get('contractors', 0)), rent=R2(p.get('rent', 0)), other_expenses=R2(p.get('expenses', 0)),
                             tax_set_aside=R2(p.get('tax', 0)), owner_draw=R2(p.get('draw', 0)), closing=0.0))
        def net(x): return x['client_payments'] + x['payer_payments'] + x['sublet_income'] - x['staff_pay'] - x['contractor_pay'] - x['rent'] - x['other_expenses'] - x['tax_set_aside'] - x['owner_draw']
        run = 0.0; mn = 0.0
        for x in rows: run += net(x); mn = min(mn, run)
        bal = R2(26000 - mn)
        for x in rows: x['opening'] = R2(bal); bal += net(x); x['closing'] = R2(bal)
        return rows
    return _thin(_cached('cash', f), n)


# ------------------------------------------------------------------ diary slots, matching rules, absences
def slot_rows(n=None):
    """the weekly diary for this week and the next 5: every usual slot of every clinician (Booked, Free or Away) plus Extra sessions outside the usual slots"""
    def f():
        W = _W(); WN = week_start(TODAY); out = []
        bk = {}
        for s in W['sessions']:
            if s['date'] >= WN and s['status'] != 'Cancelled': bk[(s['clinician'], s['date'], s['hour'])] = s
        for k in range(FUTURE_WEEKS):
            ws = WN + day(7 * k)
            for nm in CLINICIANS:
                grid = [(wd, h) for wd in sorted(_GRID[nm]) for h in _GRID[nm][wd]]
                for wd, h in grid:
                    d = ws + day(wd); s = bk.pop((nm, d, h), None)
                    st = 'Booked' if s else ('Away' if (nm, ws) in W['absent'] or _closed(ws) else 'Free')
                    out.append(dict(week=iso(ws), date=iso(d), weekday=WEEKDAYS[wd], time='%02d:00' % h, clinician=nm, status=st, client=s['client']['client'] if s else '',
                                    service=s['service'] if s else '', room=s['room'] if s else ''))
        for (nm, d, h), s in bk.items():
            if d < WN + day(7 * FUTURE_WEEKS):
                out.append(dict(week=iso(week_start(d)), date=iso(d), weekday=WEEKDAYS[d.weekday()], time='%02d:00' % h, clinician=nm, status='Extra', client=s['client']['client'],
                                service=s['service'], room=s['room']))
        out.sort(key=lambda x: (x['date'], x['time'], CLINICIANS.index(x['clinician'])))
        for i, x in enumerate(out, 1): x['slot_id'] = 'DS-%04d' % i
        return [dict(slot_id=x.pop('slot_id'), **x) for x in out]
    return _thin(_cached('slots', f), n)


def skill_rows(n=None):
    """which clinician takes which kind of new client (preference 1 = first choice), and whether they can take one now (6+ free diary slots in the next 4 weeks)"""
    def f():
        W = _W(); free = {}; lim = iso(week_start(TODAY) + day(28))
        for x in slot_rows():
            if x['status'] == 'Free' and iso(TODAY) < x['date'] < lim: free[x['clinician']] = free.get(x['clinician'], 0) + 1
        out = []
        for sv, d in _SKILL.items():
            for nm, w in sorted(d.items(), key=lambda kv: -kv[1]):
                p = staff_by_name[nm]
                ct = 'Young person' if sv == 'Young person' else ('Couple' if sv == 'Couples session' else 'Family' if sv == 'Family session' else
                                                                  'Child' if sv in ('Child session', 'Speech therapy', 'Behaviour therapy') else 'Adult')
                out.append(dict(service='Individual session' if sv == 'Young person' else sv, client_type=ct, clinician=nm, preference=1 if w >= 1.2 else (2 if w >= .5 else 3),
                                takes_new='Yes' if free.get(nm, 0) >= 6 else 'No'))
        for i, x in enumerate(out, 1): x['rule_id'] = 'MR-%02d' % i
        return [dict(rule_id=x.pop('rule_id'), **x) for x in out]
    return _thin(_cached('skill', f), n)


def absence_rows(n=None):
    """clinician weeks away (holiday, training, personal leave) from the start of the history to 8 weeks ahead, with the sessions that had to move"""
    def f():
        W = _W(); r = rng('absence'); out = []; wi_of = {w: i for i, w in enumerate(W['weeks'])}
        for nm, w in sorted(W['absent'], key=lambda x: (x[1], CLINICIANS.index(x[0]))):
            if w < HISTORY_START or w > TODAY + day(56) or w < week_start(to_date(staff_by_name[nm]['start'])) or _closed(w): continue
            wi = wi_of.get(w)
            moved = 0 if wi is None else sum(1 for c in W['clients'] if c['clinician'] == nm and c.get('start_wi', 0) <= wi and wi % 4 in c['phases']
                                             and (c['end'] in (None, 'future') or c['end'] >= w) and to_date(c['first_session']) <= w + day(6))
            kind = 'Holiday' if w.month in (6, 7, 8, 9, 12) else _wchoice(r, ABSENCE_KINDS, [5, 3, 2])
            out.append(dict(week=iso(w), clinician=nm, kind=kind, days=5 if nm != OWNER else 3, sessions_moved=moved, cover_by='' if r.random() < .7 else r.choice([x for x in CLINICIANS if x != nm])))
        for i, x in enumerate(out, 1): x['absence_id'] = 'AB-%03d' % i
        return [dict(absence_id=x.pop('absence_id'), **x) for x in out]
    return _thin(_cached('abs', f), n)


# ------------------------------------------------------------------ story
# ------------------------------------------------------------------ gap-study additions (benefits, enrolment, ageing, cards, promises, collection gap, contractor fees, cover renewals)
AGE_BANDS = ['0-30', '31-60', '61-90', '90+']
BENEFIT_RESULTS = ['Covered', 'Needs pre-approval', 'Self-pay fallback']
ENROLMENT_STATUS = ['Enrolled', 'Applied', 'Renewal due']
PROMISE_OUTCOMES = ['Kept', 'Broken', 'Pending']
PROMISE_METHODS = ['Phone', 'Message', 'Email']
GAP_CAUSES = ['Sliding scale', 'Waived late fee', 'Written off', 'Unpaid']
EXTRA_RENEWAL_KINDS = ['Data protection registration', 'Associate cover']
RENEWAL_KINDS_ALL = RENEWAL_KINDS + EXTRA_RENEWAL_KINDS


def _band(days): return AGE_BANDS[0] if days <= 30 else AGE_BANDS[1] if days <= 60 else AGE_BANDS[2] if days <= 90 else AGE_BANDS[3]


def _asofs(): return [(m, TODAY if m == _ms(TODAY) else _eom(m)) for m in months14()]


def client_ageing_rows(n=None):
    """month-end money owed by clients, by age band (days since the invoice was issued); the current month is as of today"""
    def f():
        iv = [x for x in invoice_rows() if x['status'] != 'Written off']; out = []
        for m, asof in _asofs():
            a = iso(asof); acc = {b: [0, 0.0] for b in AGE_BANDS}
            for x in iv:
                if x['issued_on'] > a: continue
                paid = x['paid_amount'] if (x['paid_on'] == '' or x['paid_on'] <= a) else 0.0
                owed = R2(x['amount_due'] - paid)
                if owed <= 0.005: continue
                b = _band((asof - to_date(x['issued_on'])).days); acc[b][0] += 1; acc[b][1] += owed
            for b in AGE_BANDS: out.append(dict(month=iso(m), as_of=a, band=b, invoices=acc[b][0], balance=R2(acc[b][1])))
        for i, x in enumerate(out, 1): x['ageing_id'] = 'AG-%03d' % i
        return [dict(ageing_id=x.pop('ageing_id'), **x) for x in out]
    return _thin(_cached('cag', f), n)


def payer_ageing_rows(n=None):
    """month-end open claims by payer and age band (days since submission); the current month is as of today"""
    def f():
        cl = _pub([dict(x) for x in _claims_raw()]); out = []
        for m, asof in _asofs():
            a = iso(asof); acc = {(p, b): [0, 0.0] for p in PAYERS for b in AGE_BANDS}
            for x in cl:
                if x['submitted_on'] > a: continue
                if x['paid_on']: closed = x['paid_on']
                elif x['status'] == 'Written off': closed = iso(to_date(x['denied_on'] or x['submitted_on']) + day(45))
                else: closed = ''
                if closed and closed <= a: continue
                b = _band((asof - to_date(x['submitted_on'])).days); acc[(x['payer'], b)][0] += 1; acc[(x['payer'], b)][1] += x['amount']
            for p in PAYERS:
                for b in AGE_BANDS: out.append(dict(month=iso(m), as_of=a, payer=p, band=b, claims=acc[(p, b)][0], amount=R2(acc[(p, b)][1])))
        for i, x in enumerate(out, 1): x['ageing_id'] = 'AP-%03d' % i
        return [dict(ageing_id=x.pop('ageing_id'), **x) for x in out]
    return _thin(_cached('pag', f), n)


def benefit_check_rows(n=None):
    """benefits check before the first session (oldest first): session limit, pre-approval needed, client share, result and the self-pay fallback fee"""
    def f():
        out = []; st = story()['denied_client_id']
        for c in client_rows():
            if c['booked_on'] > iso(TODAY): continue
            r = rng('bc-' + c['client_id']); payer = c['fee_type'] == 'Third-party payer'
            if not payer and r.random() > .06: continue
            chk = to_date(c['booked_on']) - day(r.randint(0, 3)); chk = min(max(chk, HISTORY_START), TODAY)
            fee = SV[c['service']]['fee']
            if not payer:
                lim, pre, res, share = 0, 'No', 'Self-pay fallback', fee
            else:
                lim = r.choice([12, 20, 20, 24, 30]); pre = 'Yes' if (c['payer'] == 'Payer D' and r.random() < .5) or r.random() < .2 else 'No'
                res = 'Needs pre-approval' if pre == 'Yes' else 'Covered'; share = PY[c['payer']]['copay']
            if c['client_id'] == st: lim, pre, res, share = 20, 'Yes', 'Needs pre-approval', PY[c['payer']]['copay']
            out.append(dict(client_id=c['client_id'], client=c['client'], payer=c['payer'] if payer else '', service=c['service'], checked_on=iso(chk),
                            checked_by=COORDINATOR if r.random() < .85 else OWNER, session_limit=lim, pre_approval_needed=pre, client_share=share, result=res,
                            self_pay_fee=fee))
        out.sort(key=lambda x: (x['checked_on'], x['client_id']))
        for i, x in enumerate(out, 1): x['check_id'] = 'BC-%04d' % i
        return [dict(check_id=x.pop('check_id'), **x) for x in out]
    return _thin(_cached('bc', f), n)


def payer_enrolment_rows(n=None):
    """payer enrolment of each clinician: application sent, effective date (blank while applied), renewal due and status"""
    def f():
        out = []
        pend = {('Priya Raman', 'Payer D'): 38, ('Lucas Moreau', 'Payer C'): 22}
        for p in PAYERS:
            for nm in CLINICIANS:
                r = rng('en-%s-%s' % (p, nm)); sd = to_date(staff_by_name[nm]['start'])
                sent = sd + day(r.randint(-12, 25)) if nm != OWNER else sd - day(400 + 30 * PAYERS.index(p))
                eff = sent + day(PY[p]['days_hi'] + r.randint(25, 60))
                if (nm, p) in pend: sent = TODAY - day(pend[(nm, p)]); eff = None
                elif eff > TODAY: eff = TODAY - day(r.randint(8, 40)); sent = eff - day(PY[p]['days_hi'] + 30)
                if eff is None: ren = None; st = 'Applied'
                else:
                    ren = eff
                    while ren <= TODAY: ren = add_months(ren, 12)
                    st = 'Renewal due' if (ren - TODAY).days <= 90 else 'Enrolled'
                out.append(dict(payer=p, clinician=nm, application_sent=iso(sent), effective_date=iso(eff) if eff else '', renewal_due=iso(ren) if ren else '', status=st))
        out.sort(key=lambda x: (x['application_sent'], x['payer'], x['clinician']))
        for i, x in enumerate(out, 1): x['enrolment_id'] = 'EN-%02d' % i if False else 'PE-%02d' % i
        return [dict(enrolment_id=x.pop('enrolment_id'), **x) for x in out]
    return _thin(_cached('penr', f), n)


def card_on_file_rows(n=None):
    """card on file and auto-pay flags per client, plus whether the client pays by instalment (oldest first)"""
    def f():
        plans = {x['client_id'] for x in payment_plan_rows()}; out = []
        for c in client_rows():
            r = rng('cof-' + c['client_id']); card = r.random() < (.8 if c['pay_method'] == 'Card' else .25)
            if c['client_id'] == story()['overdue_client_id']: card = False
            auto = card and r.random() < .6
            out.append(dict(client_id=c['client_id'], client=c['client'], pay_method=c['pay_method'], card_on_file='Yes' if card else 'No', autopay='Yes' if auto else 'No',
                            pays_by_instalment='Yes' if c['client_id'] in plans else 'No', added_on=c['booked_on']))
        return out
    return _thin(_cached('cof', f), n)


def payment_promise_rows(n=None):
    """promised payment dates logged while chasing a late invoice (oldest first); outcome Kept, Broken or Pending"""
    def f():
        out = []; sty = story()
        for x in invoice_rows():
            if x['status'] == 'Written off' and x['invoice_id'] not in sty['overdue_invoices']: pass
            late = (x['paid_on'] and x['paid_on'] > x['due_date']) or (not x['paid_on'] and x['due_date'] < iso(TODAY - day(3)))
            if not late: continue
            r = rng('pp-' + x['invoice_id'])
            if r.random() > (.9 if not x['paid_on'] else .35) and x['invoice_id'] not in sty['overdue_invoices']: continue
            lg = to_date(x['due_date']) + day(r.randint(3, 9))
            if not x['paid_on'] and x['due_date'] >= iso(TODAY - day(45)): lg = max(lg, TODAY - day(r.randint(0, 6)))
            if lg > TODAY: continue
            pr = lg + day(r.randint(3, 12))
            if x['paid_on'] and x['paid_on'] <= iso(pr + day(2)): oc = 'Kept'
            elif pr > TODAY: oc = 'Pending'
            else: oc = 'Broken'
            out.append(dict(invoice_id=x['invoice_id'], client_id=x['client_id'], client=x['client'], logged_on=iso(lg), promised_on=iso(pr), method=r.choice(PROMISE_METHODS), outcome=oc))
            if x['invoice_id'] == sty['overdue_invoice']:
                out[-1].update(logged_on=ago(40), promised_on=ago(33), outcome='Broken', method='Phone')
                out.append(dict(invoice_id=x['invoice_id'], client_id=x['client_id'], client=x['client'], logged_on=ago(2), promised_on=ahead(4), method='Phone', outcome='Pending'))
        out.sort(key=lambda x: (x['logged_on'], x['invoice_id']))
        for i, x in enumerate(out, 1): x['promise_id'] = 'PR-%04d' % i
        return [dict(promise_id=x.pop('promise_id'), **x) for x in out]
    return _thin(_cached('prom', f), n)


def collection_gap_rows(n=None):
    """money not collected by month and cause: sliding-scale concessions, waived late fees, written-off invoices and unpaid balances"""
    def f():
        acc = {(iso(m), c): 0.0 for m in _months24() for c in GAP_CAUSES}
        for s in session_rows():
            if s['date'] > iso(TODAY): continue
            k = s['month']
            if (k, 'Sliding scale') not in acc: continue
            if s['status'] == 'Attended' and s['fee_type'] == 'Sliding scale': acc[(k, 'Sliding scale')] += s['fee'] - s['charge']
            if s['fee_waived'] == 'Yes': acc[(k, 'Waived late fee')] += s['fee'] * LATE_FEE_PCT
        for x in invoice_rows():
            k = x['month']
            if (k, 'Written off') not in acc: continue
            if x['status'] == 'Written off': acc[(k, 'Written off')] += x['amount_due']
            elif x['due_date'] <= iso(TODAY) and x['status'] != 'Paid': acc[(k, 'Unpaid')] += x['amount_due'] - x['paid_amount']
        out = [dict(month=m, cause=c, amount=R2(v)) for (m, c), v in acc.items()]
        out.sort(key=lambda x: (x['month'], GAP_CAUSES.index(x['cause'])))
        for i, x in enumerate(out, 1): x['gap_id'] = 'CG-%03d' % i
        return [dict(gap_id=x.pop('gap_id'), **x) for x in out]
    return _thin(_cached('cgap', f), n)


def card_share_month(month_iso):
    """share of client payment money paid by card in a month (1st of the month, iso)"""
    def f():
        t = {}; cd = {}
        for p in payment_rows():
            k = p['date'][:7]; t[k] = t.get(k, 0.0) + p['amount']
            if p['method'] == 'Card': cd[k] = cd.get(k, 0.0) + p['amount']
        return {k: (cd.get(k, 0.0) / v if v else 0.0) for k, v in t.items()}
    return _raw('cardshare', f).get(month_iso[:7], 0.0)


def contractor_fee_rows(n=None):
    """contractor months with the card fees on their sessions and the pay after those fees (effective split)"""
    def f():
        out = []
        for x in clinician_pay_rows():
            if x['pay_type'] != 'Percentage split': continue
            cf = R2(x['fees_charged'] * card_share_month(x['month']) * CARD_FEE_PCT)
            aft = R2(x['split_pct'] * (x['fees_charged'] - cf))
            out.append(dict(pay_id=x['pay_id'], month=x['month'], contractor=x['person'], fees_charged=x['fees_charged'], split_pct=x['split_pct'], amount=x['amount'],
                            card_fees=cf, amount_after_fees=aft))
        return out
    return _thin(_cached('cfee', f), n)


def extra_renewal_rows(n=None):
    """renewals the cover and registration items add to the 67 renewal rows (ids RN-101 on): data protection registration and the associate's cover"""
    def f():
        r = rng('xren'); out = []
        for holder, item, every, cost, nxt in (('Practice', 'Data protection registration', 12, 35.0, TODAY + day(210)), (ASSOCIATE, 'Associate cover', 12, 180.0, TODAY + day(95))):
            dues = [nxt]
            while True:
                p = add_months(dues[0], -every)
                if p < HISTORY_START - day(20) or (holder == ASSOCIATE and p < to_date(staff_by_name[ASSOCIATE]['start']) - day(30)): break
                dues.insert(0, p)
            for dd in dues:
                ren = dd - day(r.randint(3, 20)) if dd <= TODAY else None
                out.append(dict(holder=holder, item=item, every_months=every, due_date=iso(dd), renewed_on=iso(ren) if ren else '', cost=cost, paid_by='Practice'))
        out.sort(key=lambda x: (x['due_date'], x['holder'], x['item']))
        for i, x in enumerate(out, 1): x['renewal_id'] = 'RN-%03d' % (100 + i)
        return [dict(renewal_id=x.pop('renewal_id'), **x) for x in out]
    return _thin(_cached('xren', f), n)


_GENS_NEW = ['client_ageing_rows', 'payer_ageing_rows', 'benefit_check_rows', 'payer_enrolment_rows', 'card_on_file_rows', 'payment_promise_rows', 'collection_gap_rows',
             'contractor_fee_rows', 'extra_renewal_rows']


def story():
    """ids of the story rows: losing_service (+ losing_service_id, losing_profit, losing_sessions), overdue_invoice (+ overdue_client, overdue_client_id, overdue_balance,
    overdue_days, overdue_invoices), denied_claim (+ denied_claims, denied_client, denied_client_id, denied_amount, denied_days), overbooked_clinician (+ overbooked_week,
    overbooked_sessions, overbooked_cap), late_notes_clinician (+ late_notes, late_note_sessions), renewal_due (+ renewal_holder, renewal_item, renewal_date, renewal_days)"""
    out = {}
    sp = service_profit('Behaviour therapy'); out['losing_service'] = 'Behaviour therapy'; out['losing_service_id'] = SV['Behaviour therapy']['service_id']
    out['losing_profit'] = sp['profit']; out['losing_sessions'] = sp['sessions']
    inv = [x for x in invoice_rows() if x['_story']] if False else [x for x in _accounts()['invoices'] if x.get('_story')]
    out['overdue_invoice'] = inv[0]['invoice_id']; out['overdue_invoices'] = [x['invoice_id'] for x in inv]; out['overdue_client'] = inv[0]['client']['client']
    out['overdue_client_id'] = inv[0]['client']['client_id']; out['overdue_balance'] = R2(sum(x['amount'] - x['deposit_applied'] for x in inv)); out['overdue_days'] = (TODAY - inv[0]['due_date']).days
    cl = [x for x in _claims_raw() if x['_story']]
    out['denied_claim'] = cl[0]['claim_id']; out['denied_claims'] = [x['claim_id'] for x in cl]; out['denied_client'] = cl[0]['client']; out['denied_client_id'] = cl[0]['client_id']
    out['denied_amount'] = R2(sum(x['amount'] for x in cl)); out['denied_days'] = (TODAY - to_date(cl[-1]['denied_on'])).days
    wk = iso(_W()['over_week']); cnt = clinician_week_counts(wk)
    out['overbooked_clinician'] = 'Sofia Marchetti'; out['overbooked_week'] = wk; out['overbooked_sessions'] = cnt['Sofia Marchetti']; out['overbooked_cap'] = staff_by_name['Sofia Marchetti']['session_cap']
    ln = [s for s in session_rows() if s['clinician'] == ASSOCIATE and s['status'] == 'Attended' and s['note_done_on'] == '' and s['date'] <= ago(NOTE_DUE_DAYS + 1)]
    out['late_notes_clinician'] = ASSOCIATE; out['late_notes'] = len(ln); out['late_note_sessions'] = [s['session_id'] for s in ln]
    rn = [x for x in renewal_rows() if x['holder'] == 'Kenji Watanabe' and x['item'] == 'Liability insurance' and x['due_date'] > iso(TODAY)][0]
    out['renewal_due'] = rn['renewal_id']; out['renewal_holder'] = rn['holder']; out['renewal_item'] = rn['item']; out['renewal_date'] = rn['due_date']; out['renewal_days'] = (to_date(rn['due_date']) - TODAY).days
    return out


_GENS = ['slot_rows', 'skill_rows', 'absence_rows', 'client_rows', 'enquiry_rows', 'waitlist_rows', 'session_rows', 'claim_rows', 'invoice_rows', 'payment_rows', 'package_rows', 'deposit_rows', 'payment_plan_rows',
         'client_statement_rows', 'plan_review_rows', 'outcome_rows', 'discharge_rows', 'supervision_rows', 'ce_rows', 'renewal_rows', 'clinician_pay_rows', 'clinician_month_rows',
         'service_month_rows', 'room_month_rows', 'group_rows', 'group_signup_rows', 'sublet_rows', 'marketing_rows', 'expense_rows', 'tax_rows', 'cash_rows']


def _digest():
    h = hashlib.md5()
    for nm in _GENS: h.update(repr(globals()[nm]()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); S = story(); G = {nm: globals()[nm]() for nm in _GENS}; G['team'] = team
    print('team', len(team), 'services', len(services), 'rooms', len(rooms), 'referrers', len(referrers), 'tenants', len(tenants))
    print(' '.join('%s %d' % (nm.replace('_rows', ''), len(v)) for nm, v in G.items()))
    ids = {'client_rows': 'client_id', 'enquiry_rows': 'enquiry_id', 'waitlist_rows': 'wait_id', 'session_rows': 'session_id', 'claim_rows': 'claim_id', 'invoice_rows': 'invoice_id',
           'payment_rows': 'payment_id', 'package_rows': 'package_id', 'deposit_rows': 'deposit_id', 'payment_plan_rows': 'plan_id', 'client_statement_rows': 'statement_id',
           'plan_review_rows': 'review_id', 'outcome_rows': 'score_id', 'discharge_rows': 'discharge_id', 'supervision_rows': 'supervision_id', 'ce_rows': 'ce_id',
           'renewal_rows': 'renewal_id', 'clinician_pay_rows': 'pay_id', 'clinician_month_rows': 'row_id', 'service_month_rows': 'row_id', 'room_month_rows': 'row_id',
           'group_rows': 'group_id', 'group_signup_rows': 'signup_id', 'sublet_rows': 'sublet_id', 'marketing_rows': 'campaign_id', 'expense_rows': 'expense_id', 'tax_rows': 'tax_id'}
    for nm, k in ids.items(): assert len({x[k] for x in G[nm]}) == len(G[nm]), nm
    assert len({c['client'] for c in G['client_rows']}) == len(G['client_rows']), 'client names unique'
    # every list value used by the generator that carries it
    chk = [('client_rows', 'client_type', CLIENT_TYPES), ('session_rows', 'service', SERVICES[:-1]), ('service_month_rows', 'service', SERVICES), ('session_rows', 'format', FORMATS),
           ('session_rows', 'status', SESSION_STATUS), ('session_rows', 'cancel_reason', CANCEL_REASONS), ('client_rows', 'frequency', FREQUENCIES), ('session_rows', 'fee_type', FEE_TYPES),
           ('claim_rows', 'payer', PAYERS), ('claim_rows', 'status', CLAIM_STATUS), ('claim_rows', 'denial_reason', DENIAL_REASONS), ('client_rows', 'status', CLIENT_STATUS),
           ('enquiry_rows', 'status', ENQUIRY_STATUS), ('enquiry_rows', 'reason', ENQUIRY_REASONS), ('enquiry_rows', 'source', REFERRAL_SOURCES), ('enquiry_rows', 'contact_method', CONTACT_METHODS),
           ('waitlist_rows', 'status', WAIT_STATUS), ('enquiry_rows', 'priority', PRIORITIES), ('session_rows', 'room', ROOMS), ('payment_rows', 'method', PAYMENT_METHODS),
           ('payment_rows', 'kind', PAYMENT_KINDS), ('invoice_rows', 'status', INVOICE_STATUS), ('payment_plan_rows', 'status', PLAN_STATUS), ('package_rows', 'kind', PACKAGE_KINDS),
           ('package_rows', 'status', PACKAGE_STATUS), ('deposit_rows', 'status', DEPOSIT_STATUS), ('outcome_rows', 'point', OUTCOME_POINTS), ('discharge_rows', 'reason', DISCHARGE_REASONS),
           ('discharge_rows', 'referred_to', REFERRED_TO), ('supervision_rows', 'kind', SUPERVISION_KINDS), ('ce_rows', 'kind', CE_KINDS), ('renewal_rows', 'item', RENEWAL_KINDS),
           ('group_rows', 'program', GROUP_PROGRAMS), ('group_rows', 'status', GROUP_STATUS), ('group_signup_rows', 'status', SIGNUP_STATUS), ('marketing_rows', 'kind', MARKETING_KINDS),
           ('expense_rows', 'category', EXPENSE_CATEGORIES), ('clinician_pay_rows', 'status', PAY_STATUS), ('tax_rows', 'status', TAX_STATUS), ('sublet_rows', 'status', SUBLET_STATUS),
           ('session_rows', 'clinician', CLINICIANS), ('ce_rows', 'clinician', CLINICIANS), ('supervision_rows', 'supervisee', CLINICIANS), ('renewal_rows', 'holder', HOLDERS),
           ('clinician_pay_rows', 'pay_type', PAY_KINDS), ('session_rows', 'weekday', WORKDAYS), ('session_rows', 'service', SESSION_SERVICES), ('room_month_rows', 'room', ROOM_NAMES),
           ('clinician_pay_rows', 'person', PAID_STAFF), ('slot_rows', 'status', SLOT_STATUS), ('slot_rows', 'clinician', CLINICIANS), ('absence_rows', 'kind', ABSENCE_KINDS),
           ('absence_rows', 'clinician', CLINICIANS), ('skill_rows', 'clinician', CLINICIANS), ('skill_rows', 'client_type', CLIENT_TYPES), ('team', 'pay_type', PAY_TYPES),
           ('team', 'role', ROLES), ('team', 'team', TEAMS), ('skill_rows', 'takes_new', YESNO)]
    for nm, col, vals in chk:
        got = {x[col] for x in G[nm]}; miss = [v for v in vals if v not in got]
        assert not miss, (nm, col, miss)
        extra = {g for g in got if g not in vals and g != ''}; assert not extra, (nm, col, extra)
    for L in (ROLES, TEAMS, PAY_TYPES, CLIENT_TYPES, SERVICES, FORMATS, SESSION_STATUS, CANCEL_REASONS, FEE_TYPES, CLAIM_STATUS, DENIAL_REASONS, CLIENT_STATUS, ENQUIRY_STATUS,
              ENQUIRY_REASONS, REFERRAL_SOURCES, REFERRER_KINDS, ROOMS, PAYMENT_KINDS, INVOICE_STATUS, DISCHARGE_REASONS, REFERRED_TO, CE_KINDS, RENEWAL_KINDS, GROUP_PROGRAMS,
              GROUP_STATUS, SIGNUP_STATUS, MARKETING_KINDS, EXPENSE_CATEGORIES):
        for k, _ in pairs(L): assert len(k) <= 21, k
    ss = G['session_rows']; ms = iso(month_start(0)); t30 = ago(30); td = iso(TODAY)
    assert 9000 <= len(ss) <= 14000, len(ss)
    lm = [x for x in ss if x['month'] == iso(month_start(1)) and x['status'] == 'Attended']; print('attended last month', len(lm), 'booked last month', sum(1 for x in ss if x['month'] == iso(month_start(1)) and x['status'] != 'Cancelled'))
    assert 380 <= len(lm) <= 520, len(lm)
    def cur(nm, col, lo=1, t=ms): n_ = sum(1 for x in G[nm] if x[col] and t <= x[col] <= td); assert n_ >= lo, (nm, col, n_); return n_
    print('this month:', 'sessions', cur('session_rows', 'date', 100), 'enquiries', cur('enquiry_rows', 'date', 5), 'claims submitted', cur('claim_rows', 'submitted_on', 20),
          'claims paid', cur('claim_rows', 'paid_on', 20), 'invoices', cur('invoice_rows', 'issued_on', 50), 'payments', cur('payment_rows', 'date', 50), 'expenses', cur('expense_rows', 'date', 5),
          'supervision', cur('supervision_rows', 'date', 3), 'notes', cur('session_rows', 'note_done_on', 100))
    print('last 30 days:', 'enquiries', cur('enquiry_rows', 'date', 25, t30), 'payments', cur('payment_rows', 'date', 100, t30), 'ce', cur('ce_rows', 'date', 1, t30),
          'marketing', cur('marketing_rows', 'date', 2, t30), 'discharges', cur('discharge_rows', 'date', 3, t30), 'intakes', sum(1 for x in ss if x['service'] == 'Intake assessment' and t30 <= x['date'] <= td))
    assert all(x['date'] > td for x in ss if x['status'] == 'Scheduled') and all(x['date'] <= td for x in ss if x['status'] != 'Scheduled')
    wl = [x for x in G['waitlist_rows'] if x['status'] == 'Waiting']; print('waiting now', len(wl), 'by service', {s: sum(1 for x in wl if x['service'] == s) for s in SERVICES if any(x['service'] == s for x in wl)})
    print('clients by status', {s: sum(1 for x in G['client_rows'] if x['status'] == s) for s in CLIENT_STATUS})
    print('fee types', {f_: sum(1 for x in ss if x['fee_type'] == f_) for f_ in FEE_TYPES}, 'formats', {f_: sum(1 for x in ss if x['format'] == f_) for f_ in FORMATS})
    # capacity: no clinician-week above the cap except the story week
    wk = {}
    for x in ss:
        if x['status'] != 'Cancelled': wk[(x['clinician'], x['week'])] = wk.get((x['clinician'], x['week']), 0) + 1
    over = [(k, v) for k, v in wk.items() if v > staff_by_name[k[0]]['session_cap']]; assert over == [(('Sofia Marchetti', S['overbooked_week']), S['overbooked_sessions'])], over
    # profit per service: only the story service loses money
    sp = {sv: service_profit(sv)['profit'] for sv in SERVICES}; print('service profit 12m', {k: round(v) for k, v in sp.items()})
    assert sp['Behaviour therapy'] < 0 and all(v > 0 for k, v in sp.items() if k != 'Behaviour therapy'), sp
    # money and cash
    tx = G['tax_rows']; print('monthly revenue', [round(x['revenue']) for x in tx[-14:]]); print('monthly profit', [round(x['profit']) for x in tx[-14:]])
    cr = G['cash_rows']; print('cash closing', [round(x['closing']) for x in cr])
    assert min(x['closing'] for x in cr) > CASH_FLOOR and all(x['profit'] > 0 for x in tx[:-1])
    # story checks
    inv = G['invoice_rows']; late = [x for x in inv if x['status'] in ('Unpaid', 'Part paid') and to_date(x['due_date']) < TODAY - day(42)]
    assert {x['invoice_id'] for x in late} == {S['overdue_invoice']} and S['overdue_days'] >= 42 and len(S['overdue_invoices']) == 3 and S['overdue_balance'] > 800, (late, S)
    den = [x for x in G['claim_rows'] if x['status'] == 'Denied' and to_date(x['denied_on']) < TODAY - day(30)]
    assert sorted(x['claim_id'] for x in den) == sorted(S['denied_claims']) and len(den) >= 4 and S['denied_days'] >= 42, (den, S)
    ln = {}
    for x in ss:
        if x['status'] == 'Attended' and x['note_done_on'] == '' and x['date'] <= ago(NOTE_DUE_DAYS + 1): ln[x['clinician']] = ln.get(x['clinician'], 0) + 1
    print('overdue notes', ln); assert ln.get(ASSOCIATE, 0) >= 7 and all(v <= 1 for k, v in ln.items() if k != ASSOCIATE)
    rn = [x for x in G['renewal_rows'] if x['renewed_on'] == '' and x['due_date'] <= ahead(45)]; assert [x['renewal_id'] for x in rn] == [S['renewal_due']] and S['renewal_days'] == 12, rn
    assert S['losing_profit'] < 0
    print('story', S)
    d1 = _digest(); _CACHE.clear()
    for nm in reversed(_GENS): globals()[nm]()
    d2 = _digest(); assert d1 == d2, (d1, d2)
    print('digest', d1, 'secs', round(time.time() - t0, 1))
