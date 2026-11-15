"""Doula business suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (one cached world is built on first use). The demo business is "Willowmere Doula Collective"
(fictional): a small doula agency run by an owner-doula (Amara Okonkwo, DU-01) who also takes clients, with 6 contracted doulas (DU-02..DU-07: birth, postpartum or both; paid per
client or per hour with an agency split), 2 backup doulas on a shared on-call rota (DU-08, DU-09), a part-time admin (DU-10) and 6 outside contacts (DU-11..DU-16: accountant, class
venue, photographer, a support professional for referrals, a care-provider office, an insurer). About 70 birth clients and 45 postpartum clients a year (about 250 clients over ~2
years plus the booked next 8 months) in 2 service areas (Northgate, Southbank). A solo doula can use most parts (one doula, no split, no backup rota). One generic currency; every date
is relative to the build day. STRICTLY NON-MEDICAL: dates, hours, packages, money and contact notes only; no medical data, no outcome promises.

Money model: a package (birth, postpartum hour pack, combined, add-on) has a list price; a contract price = list price less the client's discount (None, Community rate 15%,
Returning client 10%); deposit = price x the package deposit share; balance due `balance_weeks` (6) weeks before the estimated due date, in full or in 3-4 instalments that end before
the on-call window; postpartum hour packs are prepaid in full. Revenue is EARNED (recognised) when the work is done: the birth part of a package in the month of the birth, postpartum
hours as they are worked (unused hours when the pack expires), add-ons and class seats on the day, a kept deposit on the cancellation day; cash received before that is the unearned
balance. Doula pay: per-client doulas get (birth part of the price) x (1 - agency share); per-hour doulas get hours x their hourly pay; backup doulas get a weekly stipend plus a flat
call-out when they attend; mileage is paid at the area rate per mile. The agency also carries an overhead per client. On-call window = estimated due date - 14 days .. + 14 days
(editable). Capacity: at most `max_oncall_overlap` (2) windows of one doula at the same time and `cap_births_month` (3) due dates per doula per month.

Story rows (ids from story(), never hard-coded): overlap_* (a month next quarter where one doula has 3 overlapping on-call windows above the limit of 2 and no backup named),
low_package (a combined bundle priced so low that income per hour, all hours incl. on-call, is below the target), plan_* (a payment-plan client whose instalment is unpaid with the
due date in 4 days), prepaid_* (a 120-hour postpartum pack paid in full with most hours not yet delivered: unearned balance), split_* (a doula whose agency split leaves the agency
losing money on their births after costs), renewal_* (the agency liability insurance renewal due in 12 days).

Exports
  constants: COMPANY SUITE OWNER ADMIN HISTORY_START ONCALL_BEFORE ONCALL_AFTER MAX_OVERLAP CAP_BIRTHS BALANCE_WEEKS TARGET_INCOME_HOUR MIN_BOOKING_HOURS WEEKLY_HOURS_CAP
             AGENCY_COST_CLIENT BACKUP_FLAT_PAY BACKUP_STIPEND_WEEK REPLY_HOURS_TARGET CANCEL_RATE_MAX DECLINED_MAX CASH_FLOOR CASH_COVER_MONTHS OWNER_DRAW TAX_SET_ASIDE_PCT
             REVIEW_ASK_DAYS PACK_EXPIRY_DAYS RENEWAL_RED_DAYS RENEWAL_AMBER_DAYS CPD_TARGET_HOURS ALLOC ADMIN_HOURS_WEEK
  dates: TODAY iso ago ahead to_date month_start add_months months14() months24() week_start; helpers pairs first_name fake_phone fake_email rng
  lists: ROLES TEAMS SERVICES PAY_TYPES AREAS PACKAGE_KINDS CLIENT_KINDS CLIENT_STATUS DISCOUNTS PLAN_TYPES CONTRACT_STATUS INST_STATUS PAY_METHODS PAYMENT_KINDS SOURCES ENQUIRY_STATUS
         LOST_REASONS CONSULT_OUTCOMES VISIT_KINDS CANCEL_KINDS CANCEL_REASONS CLASS_TYPES MARKETING_KINDS EXPENSE_CATEGORIES RENEWAL_KINDS CPD_KINDS PAY_BASIS PAY_STATUS
         CHANNELS TIMEOFF_KINDS WEEKDAYS DOULA_NAMES BACKUP_NAMES CONTRACTED
  people and reference: team (16), doulas (7: owner + 6 with pay terms and caps), areas (2), packages (15), pp_rates (4), sources_ref (8), class_types (5), budget (10), renewal_items (7)
  generators (fresh lists of dicts, oldest first; n= thins a long list but keeps the most recent rows; optional dates are '' when blank):
    client_rows contract_rows plan_rows payment_rows addon_rows oncall_rows rota_rows birth_rows visit_rows pack_rows pay_rows enquiry_rows consult_rows class_session_rows
    class_attendee_rows referral_rows review_rows cancel_rows marketing_rows expense_rows renewal_rows training_rows timeoff_rows pnl_rows cash_rows tax_rows owner_time_rows
  helpers: client_summary(client_id) agency_margin() coverage(doula, d) story()
Lesson: money cells are plain amounts; optional dates (paid_on, received_on, thanked_on, attended_on) are '' when blank: wrap lookups with IF(x=0,"",x). Links hold NAMES (client,
doula, backup, area, package) or ids (client CL-0001, enquiry EN-0001, contract CT-0001). Words: no medical detail; no outcome promises.
"""
import datetime as dt
import calendar
import random
import hashlib
import math

COMPANY = 'Willowmere Doula Collective'
SUITE = 'fx-20261115-doula-business'
OWNER = 'Amara Okonkwo'
ADMIN = 'Henrik Solberg'
TODAY = dt.date.today()
D = dt.date

ONCALL_BEFORE = 14           # on-call window starts this many days before the estimated due date
ONCALL_AFTER = 14            # and ends this many days after it
MAX_OVERLAP = 2              # most on-call windows of one doula at the same time
CAP_BIRTHS = 3               # most due dates of one doula in one month
BALANCE_WEEKS = 6            # balance due this many weeks before the estimated due date
TARGET_INCOME_HOUR = 30.0    # owner's own target: package income per hour, all hours incl. on-call
MIN_BOOKING_HOURS = 4
WEEKLY_HOURS_CAP = 24        # postpartum plus birth hours per doula per week
AGENCY_COST_CLIENT = 85.0    # agency overhead per client (admin time, insurance share, tools)
BACKUP_FLAT_PAY = 420.0      # a backup doula who attends a birth
BACKUP_STIPEND_WEEK = 70.0   # a backup doula on the rota, per week
REPLY_HOURS_TARGET = 24
CANCEL_RATE_MAX = 0.12
DECLINED_MAX = 0.15
CASH_FLOOR = 15000.0
CASH_COVER_MONTHS = 3
OWNER_DRAW = 3600.0
TAX_SET_ASIDE_PCT = 0.25
REVIEW_ASK_DAYS = 14
PACK_EXPIRY_DAYS = 120       # an hour pack runs this many days after the estimated due date
RENEWAL_RED_DAYS = 30
RENEWAL_AMBER_DAYS = 60
CPD_TARGET_HOURS = 15
ALLOC = dict(prenatal=0.20, oncall=0.30, birth=0.35, postpartum=0.15)
ADMIN_HOURS_WEEK = 20
ADMIN_RATE = 21.0


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
def rng(tag=''): return random.Random('du-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def q(x): return round(x * 4) / 4.0
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
def _hm(mins):
    mins = int(mins) % 1440
    return '%02d:%02d' % (mins // 60, mins % 60)


HISTORY_START = month_start(23)

# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Owner-doula', 'Contracted doula', 'Backup doula', 'Admin', 'Accountant', 'Class venue', 'Photographer', 'Support professional', 'Care provider office', 'Insurer']
TEAMS = ['Doulas', 'Backup', 'Office', 'Outside']
SERVICES = ['Birth', 'Postpartum', 'Both']
PAY_TYPES = ['Owner draw', 'Per client', 'Per hour', 'Per client and hour', 'Backup rota', 'Part-time hourly', 'Invoice']
AREAS = ['Northgate', 'Southbank']
PACKAGE_KINDS = ['Birth', 'Postpartum', 'Combined', 'Add-on']
CLIENT_KINDS = ['Birth', 'Postpartum', 'Combined']
CLIENT_STATUS = ['Booked', 'On call', 'Postpartum care', 'Completed', 'Cancelled']
DISCOUNTS = ['None', 'Community rate', 'Returning client']
DISCOUNT_PCT = {'None': 0.0, 'Community rate': 0.15, 'Returning client': 0.10}
PLAN_TYPES = ['Pay in full', 'Instalments']
CONTRACT_STATUS = ['Signed', 'Completed', 'Cancelled']
INST_STATUS = ['Paid', 'Unpaid']
PAY_METHODS = ['Card payment', 'Bank transfer', 'Cash', 'Payment link']
PAYMENT_KINDS = ['Deposit', 'Balance', 'Instalment', 'Hours invoice', 'Add-on']
SOURCES = ['Care provider', 'Past client', 'Online search', 'Social media', 'Class or workshop', 'Support professional', 'Local event', 'Directory listing']
ENQUIRY_STATUS = ['New', 'Consultation booked', 'Consultation held', 'Contract sent', 'Signed', 'Lost']
LOST_REASONS = ['Price', 'Date full', 'No backup', 'Chose someone else', 'No reply']
CONSULT_OUTCOMES = ['Booked', 'Signed', 'Thinking', 'Declined', 'No-show']
VISIT_KINDS = ['Prenatal visit', 'Postpartum visit', 'Night shift', 'Debrief visit']
CANCEL_KINDS = ['Cancelled', 'Package changed', 'Hours reduced']
CANCEL_REASONS = ['Moved away', 'Changed provider', 'Price', 'Date changed', 'Chose other support', 'Other']
CLASS_TYPES = ['Education series', 'Newborn workshop', 'Partner workshop', 'Planning workshop', 'Infant care evening']
MARKETING_KINDS = ['Online listing', 'Website upkeep', 'Local flyers', 'Event stand', 'Social posts', 'Referral thank-yous']
EXPENSE_CATEGORIES = ['Insurance', 'Phone and software', 'Accounting', 'Supplies and printing', 'Class venue', 'Marketing', 'Training and renewals', 'Card and bank fees', 'Memberships', 'Other']
RENEWAL_KINDS = ['Certification renewal', 'Continuing education', 'First aid course', 'Background check', 'Liability insurance', 'Business registration', 'Contract review']
CPD_KINDS = ['Workshop', 'Online course', 'Training day', 'Peer circle', 'First aid course']
PAY_BASIS = ['Per client', 'Per hour', 'Mileage', 'Backup stipend', 'Backup call-out']
PAY_STATUS = ['Paid', 'Due']
CHANNELS = ['Own website', 'Online listing', 'Private note']
TIMEOFF_KINDS = ['Holiday', 'Training', 'Family time', 'Rest block']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# ------------------------------------------------------------------ people
# id, name, country, role, team, pay type, hours a week, hourly rate, service, start days ago
_staff = [('DU-01', 'Amara Okonkwo', 'Nigeria', 'Owner-doula', 'Doulas', 'Owner draw', 40, 0, 'Both', 2800),
          ('DU-02', 'Lucia Ferreira', 'Portugal', 'Contracted doula', 'Doulas', 'Per client', 24, 0, 'Birth', 1500),
          ('DU-03', 'Priya Raman', 'India', 'Contracted doula', 'Doulas', 'Per client', 24, 0, 'Birth', 1250),
          ('DU-04', 'Katarzyna Nowak', 'Poland', 'Contracted doula', 'Doulas', 'Per hour', 24, 27.0, 'Postpartum', 1100),
          ('DU-05', 'Mei-Ling Chen', 'Taiwan', 'Contracted doula', 'Doulas', 'Per client and hour', 28, 27.5, 'Both', 900),
          ('DU-06', 'Fatou Diop', 'Senegal', 'Contracted doula', 'Doulas', 'Per hour', 24, 26.0, 'Postpartum', 640),
          ('DU-07', 'Sven Lindqvist', 'Sweden', 'Contracted doula', 'Doulas', 'Per client and hour', 24, 28.0, 'Both', 520),
          ('DU-08', 'Yasmin Haddad', 'Jordan', 'Backup doula', 'Backup', 'Backup rota', 0, 0, 'Birth', 700),
          ('DU-09', 'Tomas Novak', 'Czechia', 'Backup doula', 'Backup', 'Backup rota', 0, 0, 'Birth', 430),
          ('DU-10', 'Henrik Solberg', 'Norway', 'Admin', 'Office', 'Part-time hourly', ADMIN_HOURS_WEEK, ADMIN_RATE, '', 1300)]
_ctc = [('DU-11', 'Rosa Delgado', 'Spain', 'Accountant', 'Bookkeeping, tax pack and yearly accounts'),
        ('DU-12', 'Kofi Mensah', 'Ghana', 'Class venue', 'Community hall hire for classes and workshops'),
        ('DU-13', 'Ingrid Sorensen', 'Denmark', 'Photographer', 'Photography referral for clients'),
        ('DU-14', 'Aiko Tanaka', 'Japan', 'Support professional', 'Referral for extra support, generic'),
        ('DU-15', 'Marta Silva', 'Brazil', 'Care provider office', 'Care-provider office that refers clients'),
        ('DU-16', 'Callum Reid', 'United Kingdom', 'Insurer', 'Liability insurance contact')]
team = []
for _i, (_a, _b, _c, _ro, _te, _pt, _hw, _hr, _sv, _st) in enumerate(_staff):
    team.append(dict(staff_id=_a, name=_b, role=_ro, team=_te, pay_type=_pt, phone=fake_phone(101 + _i), email=fake_email(_b), hours_week=_hw, hourly_rate=float(_hr), service=_sv,
                     country=_c, start=ago(_st)))
for _i, (_a, _b, _c, _ro, _sp) in enumerate(_ctc):
    team.append(dict(staff_id=_a, name=_b, role=_ro, team='Outside', pay_type='Invoice', phone=fake_phone(113 + _i), email=fake_email(_b), hours_week=0, hourly_rate=0.0, service='',
                     country=_c, start=ago(2000 - 250 * _i)))
TEAM = {t['name']: t for t in team}
DOULA_NAMES = [t['name'] for t in team if t['team'] == 'Doulas']          # owner + 6 contracted
CONTRACTED = [t['name'] for t in team if t['role'] == 'Contracted doula']
BACKUP_NAMES = [t['name'] for t in team if t['team'] == 'Backup']

# doulas: pay terms. agency_share is the share of the birth part of a package the agency keeps (per client); hourly_pay is paid per postpartum hour worked (per hour)
_dterms = {'Amara Okonkwo': (0.0, 0.0, 3, 24), 'Lucia Ferreira': (0.28, 0.0, 3, 0), 'Priya Raman': (0.08, 0.0, 3, 0), 'Katarzyna Nowak': (0.0, 27.0, 0, 24),
           'Mei-Ling Chen': (0.27, 27.5, 3, 24), 'Fatou Diop': (0.0, 26.0, 0, 20), 'Sven Lindqvist': (0.30, 28.0, 2, 20)}
doulas = [dict(doula=n, service=TEAM[n]['service'], pay_type=TEAM[n]['pay_type'], agency_share=_dterms[n][0], hourly_pay=_dterms[n][1], cap_births=_dterms[n][2],
               weekly_hours_cap=_dterms[n][3]) for n in DOULA_NAMES]
DT = {d['doula']: d for d in doulas}

areas = [dict(area='Northgate', mileage_rate=0.58, miles_one_way=12), dict(area='Southbank', mileage_rate=0.62, miles_one_way=16)]
AREA = {a['area']: a for a in areas}

# packages: price (list), birth part and postpartum part of the price, plan hours by phase, deposit share
# id, name, kind, price, birth_value, pp_value, prenatal visits (2 h each), postpartum visits (3 h each), birth hours, on-call contact hours, postpartum hours, deposit share
_pk = [('Birth Essential', 'Birth', 1400, 1400, 0, 2, 1, 18, 6, 0, 0.30),
       ('Birth Plus', 'Birth', 1900, 1900, 0, 3, 2, 20, 8, 0, 0.30),
       ('Birth Premier', 'Birth', 2400, 2400, 0, 4, 2, 24, 10, 0, 0.30),
       ('Postpartum 40 Hours', 'Postpartum', 1480, 0, 1480, 0, 0, 0, 0, 40, 1.0),
       ('Postpartum 80 Hours', 'Postpartum', 2880, 0, 2880, 0, 0, 0, 0, 80, 1.0),
       ('Postpartum 120 Hours', 'Postpartum', 4200, 0, 4200, 0, 0, 0, 0, 120, 1.0),
       ('Night Support 60 Hours', 'Postpartum', 2400, 0, 2400, 0, 0, 0, 0, 60, 0.50),
       ('Combined Essential', 'Combined', 2700, 1300, 1400, 2, 0, 18, 6, 40, 0.30),
       ('Combined Plus', 'Combined', 4400, 1750, 2650, 3, 0, 20, 8, 80, 0.30),
       ('Complete Care Bundle', 'Combined', 4400, 1700, 2700, 4, 0, 24, 10, 120, 0.30),
       ('Extra prenatal visit', 'Add-on', 95, 0, 95, 1, 0, 0, 0, 0, 1.0),
       ('Class seat (series)', 'Add-on', 160, 0, 160, 0, 0, 0, 0, 0, 1.0),
       ('Photography referral', 'Add-on', 60, 0, 60, 0, 0, 0, 0.5, 0, 1.0),
       ('Support referral note', 'Add-on', 30, 0, 30, 0, 0, 0, 0.5, 0, 1.0),
       ('Debrief visit', 'Add-on', 85, 0, 85, 0, 1, 0, 0, 0, 1.0)]
packages = []
for _i, (_n, _k, _p, _bv, _pv, _pv_, _pov, _bh, _oh, _ph, _dp) in enumerate(_pk):
    _pn = _pv_ * 2 + _pov * 3 + _bh + _oh + _ph
    packages.append(dict(package_id='PK-%02d' % (_i + 1), package=_n, kind=_k, price=float(_p), birth_value=float(_bv), pp_value=float(_pv), prenatal_visits=_pv_, postpartum_visits=_pov,
                         birth_hours=_bh, oncall_hours=_oh, postpartum_hours=_ph, plan_hours=float(_pn), deposit_pct=_dp))
PK = {p['package']: p for p in packages}

pp_rates = [dict(shift='Day shift', rate_hour=38.0, min_hours=4), dict(shift='Evening shift', rate_hour=40.0, min_hours=4), dict(shift='Night shift', rate_hour=45.0, min_hours=8),
            dict(shift='Weekend and holiday', rate_hour=48.0, min_hours=4)]
sources_ref = [dict(source='Care provider', kind='Referral', gift_value=22.0), dict(source='Past client', kind='Referral', gift_value=15.0),
               dict(source='Online search', kind='Online', gift_value=0.0), dict(source='Social media', kind='Online', gift_value=0.0),
               dict(source='Class or workshop', kind='Event', gift_value=0.0), dict(source='Support professional', kind='Referral', gift_value=22.0),
               dict(source='Local event', kind='Event', gift_value=0.0), dict(source='Directory listing', kind='Online', gift_value=0.0)]
# class: price per seat, seats, hours a session
class_types = [dict(**{'class': 'Education series'}, price=190.0, seats=8, hours=8.0), dict(**{'class': 'Newborn workshop'}, price=55.0, seats=12, hours=3.0),
               dict(**{'class': 'Partner workshop'}, price=45.0, seats=12, hours=2.5), dict(**{'class': 'Planning workshop'}, price=40.0, seats=14, hours=2.0),
               dict(**{'class': 'Infant care evening'}, price=35.0, seats=16, hours=2.0)]
CT = {c['class']: c for c in class_types}
budget = [dict(category='Insurance', monthly_budget=100.0), dict(category='Phone and software', monthly_budget=95.0), dict(category='Accounting', monthly_budget=120.0),
          dict(category='Supplies and printing', monthly_budget=90.0), dict(category='Class venue', monthly_budget=420.0), dict(category='Marketing', monthly_budget=330.0),
          dict(category='Training and renewals', monthly_budget=260.0), dict(category='Card and bank fees', monthly_budget=170.0), dict(category='Memberships', monthly_budget=15.0),
          dict(category='Other', monthly_budget=60.0)]
# renewal item: cycle days, cost
renewal_items = [dict(item='Certification renewal', cycle_days=1095, cost=180.0), dict(item='Continuing education', cycle_days=365, cost=150.0),
                 dict(item='First aid course', cycle_days=730, cost=95.0), dict(item='Background check', cycle_days=1095, cost=45.0),
                 dict(item='Liability insurance', cycle_days=365, cost=1150.0), dict(item='Business registration', cycle_days=365, cost=120.0),
                 dict(item='Contract review', cycle_days=365, cost=220.0)]
RI = {x['item']: x for x in renewal_items}

# names of clients: many countries, unique
_G = [(['Ana', 'Rui', 'Marta', 'Ines', 'Sara', 'Tiago', 'Livia', 'Bianca'], ['Silva', 'Costa', 'Ribeiro', 'Almeida', 'Lima', 'Souza', 'Pinto', 'Campos']),
      (['Lena', 'Mira', 'Hanna', 'Nele', 'Greta', 'Jonas', 'Julia', 'Katrin'], ['Hoffmann', 'Keller', 'Vogel', 'Brandt', 'Lorenz', 'Krause', 'Richter', 'Wolf']),
      (['Ella', 'Isla', 'Freya', 'Poppy', 'Amelia', 'Grace', 'Ruby', 'Alice'], ['Turner', 'Hughes', 'Walsh', 'Barker', 'Ellis', 'Pearce', 'Dawson', 'Hale']),
      (['Camille', 'Chloe', 'Manon', 'Lea', 'Elise', 'Margaux', 'Louis', 'Jade'], ['Laurent', 'Girard', 'Roux', 'Fournier', 'Mercier', 'Blanc', 'Dupont', 'Faure']),
      (['Lucia', 'Carmen', 'Elena', 'Noa', 'Irene', 'Paula', 'Marina', 'Alba'], ['Ortega', 'Molina', 'Castro', 'Herrera', 'Vidal', 'Prieto', 'Cano', 'Romero']),
      (['Sanne', 'Fenna', 'Anouk', 'Femke', 'Lotte', 'Eva', 'Daan', 'Mila'], ['de Vries', 'Smit', 'Bos', 'Mulder', 'Dekker', 'Peters', 'Jansen', 'Vos']),
      (['Kasia', 'Zofia', 'Ola', 'Wiktoria', 'Hania', 'Marek', 'Ewa', 'Agnieszka'], ['Zielinski', 'Lewandowski', 'Mazur', 'Kaczmarek', 'Pawlak', 'Wrona', 'Sikora', 'Baran']),
      (['Diya', 'Tara', 'Isha', 'Neha', 'Kavya', 'Anaya', 'Meera', 'Riya'], ['Sharma', 'Nair', 'Kapoor', 'Mehta', 'Joshi', 'Pillai', 'Gupta', 'Desai']),
      (['Ada', 'Ngozi', 'Yetunde', 'Bisi', 'Ife', 'Amaka', 'Chioma', 'Funmi'], ['Adebayo', 'Okafor', 'Balogun', 'Nwosu', 'Ogunleye', 'Afolabi', 'Chukwu', 'Okoro']),
      (['Valeria', 'Ximena', 'Regina', 'Renata', 'Camila', 'Daniela', 'Mateo', 'Fernanda'], ['Hernandez', 'Garcia', 'Ramirez', 'Torres', 'Flores', 'Vargas', 'Mendoza', 'Cruz']),
      (['Elif', 'Defne', 'Ece', 'Selin', 'Ayla', 'Zeynep', 'Melis', 'Derya'], ['Yilmaz', 'Sahin', 'Celik', 'Aydin', 'Ozturk', 'Arslan', 'Dogan', 'Kilic']),
      (['Mei', 'Xin', 'Lan', 'Ying', 'Yu', 'Jing', 'Hui', 'Wen'], ['Wang', 'Li', 'Liu', 'Yang', 'Huang', 'Zhou', 'Wu', 'Xu']),
      (['Seoyeon', 'Hayun', 'Jiwoo', 'Yuna', 'Sora', 'Minseo', 'Chaewon', 'Eunji'], ['Kim', 'Lee', 'Choi', 'Jung', 'Kang', 'Cho', 'Yoon', 'Lim']),
      (['Mia', 'Zara', 'Sienna', 'Matilda', 'Ivy', 'Willow', 'Harper', 'Archer'], ['Murray', 'Fraser', 'Hart', 'Doyle', 'Sutton', 'Blake', 'Lowe', 'Burke']),
      (['Salma', 'Nour', 'Lina', 'Yasmin', 'Hana', 'Dalia', 'Rania', 'Omar'], ['Mansour', 'Nasser', 'Farah', 'Saleh', 'Aziz', 'Karam', 'Habib', 'Toumi'])]

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
def _clip(x, a, b): return max(a, min(b, x))


# ------------------------------------------------------------------ the world: clients and everything that hangs on them
_SEAS = {1: .85, 2: .8, 3: .85, 4: .9, 5: .95, 6: 1.0, 7: 1.1, 8: 1.3, 9: 1.35, 10: 1.25, 11: 1.0, 12: .85}   # more due dates in late summer and early autumn
_SIM_TAG = '3'


def _person_gen(r):
    used = set()
    def person():
        while True:
            f, l = _G[r.randrange(len(_G))]
            nm = r.choice(f) + ' ' + r.choice(l)
            if nm not in used and nm not in TEAM:
                used.add(nm); return nm
    return person


def _miles(r, area): return float(round(2 * AREA[area]['miles_one_way'] * (0.6 + 0.8 * r.random())))


def _pp_visits(r, start, hours, night, cap=None):
    """weekly pattern of postpartum visits until `hours` are worked; returns [(date, hours)]"""
    out = []; t = start; used = 0.0
    target = hours if cap is None else min(hours, cap)
    while used < target - 0.01 and len(out) < 80:
        nv = _wchoice(r, [1, 2, 3], [.35, .45, .20])
        for dd in sorted(r.sample(range(7), nv)):
            h = r.choice([8, 8, 10]) if night else r.choice([4, 4, 4, 5, 6, 8])
            h = min(float(h), target - used)
            if h < 1.0: break
            out.append((t + day(dd), q(h))); used += h
            if used >= target - 0.01: break
        t += day(7)
    return out


def _world():
    r = rng('world' + _SIM_TAG)
    person = _person_gen(rng('names' + _SIM_TAG))
    specs = []

    def spec(edd, **kw):
        d = dict(edd=edd, kind=None, doula=None, package=None, backup=None, force_birth=None, tag='', signed=None, hours_cap=None, plan_dues=None, discount=None)
        d.update(kw); specs.append(d); return d
    for k in range(25, -9, -1):
        ms = month_start(k); j = -k
        ramp = 1.0 if k >= 0 else [.95, .9, .8, .7, .6, .5, .4, .3][j - 1]
        n = max(1, int(round(8.4 * _SEAS[ms.month] * ramp * (0.85 + 0.3 * r.random()))))
        nd = calendar.monthrange(ms.year, ms.month)[1]
        nb = int(round(.52 * n)); nc = int(round(.18 * n)); kinds = ['Birth'] * nb + ['Combined'] * nc + ['Postpartum'] * (n - nb - nc)
        r.shuffle(kinds)
        for kd in kinds: spec(ms + day(r.randrange(nd)), kind=kd)
    # ---- story and guaranteed rows
    M = month_start(-3)
    for dd in (5, 10, 15): spec(M + day(dd), kind='Birth', package='Birth Plus', doula='Mei-Ling Chen', backup='', tag='overlap', discount='None')
    spec(TODAY - day(82), kind='Postpartum', package='Postpartum 120 Hours', doula='Katarzyna Nowak', tag='prepaid', hours_cap=14.0, discount='None', signed=TODAY - day(150))
    spec(TODAY + day(62), kind='Birth', package='Birth Plus', doula='Lucia Ferreira', tag='plan', discount='None', signed=TODAY - day(88),
         plan_dues=[TODAY - day(52), TODAY - day(24), TODAY + day(4), TODAY + day(32)])
    for off, doula_, pk in ((205, 'Mei-Ling Chen', None), (120, 'Amara Okonkwo', None), (38, 'Mei-Ling Chen', None), (-45, 'Amara Okonkwo', None)):
        spec(TODAY - day(off), kind='Combined', package='Complete Care Bundle', doula=doula_, tag='bundle', discount='None')
    for off, kd in ((min(2, TODAY.day - 1), 'Birth'), (11, 'Combined'), (23, 'Birth')):
        bd = TODAY - day(off)
        spec(bd - day(r.randint(-3, 4)), kind=kd, force_birth=bd, tag='recent')

    wins = {n: [] for n in DOULA_NAMES}
    bwins = {n: [] for n in BACKUP_NAMES}

    def cover(lst, s, e):
        best, d = 0, s
        while d <= e:
            c = sum(1 for (a, b, _x) in lst if a <= d <= b)
            best = max(best, c); d += day(1)
        return best

    def mcount(n, edd): return sum(1 for (_a, _b, x) in wins[n] if x.year == edd.year and x.month == edd.month)
    cand = {'Birth': ['Amara Okonkwo', 'Lucia Ferreira', 'Priya Raman', 'Mei-Ling Chen', 'Sven Lindqvist'], 'Combined': ['Amara Okonkwo', 'Mei-Ling Chen', 'Sven Lindqvist'],
            'Postpartum': ['Amara Okonkwo', 'Katarzyna Nowak', 'Mei-Ling Chen', 'Fatou Diop', 'Sven Lindqvist']}
    wt = {'Birth': {'Amara Okonkwo': .22, 'Lucia Ferreira': .24, 'Priya Raman': .20, 'Mei-Ling Chen': .17, 'Sven Lindqvist': .17},
          'Combined': {'Amara Okonkwo': .30, 'Mei-Ling Chen': .35, 'Sven Lindqvist': .35},
          'Postpartum': {'Amara Okonkwo': .10, 'Katarzyna Nowak': .32, 'Mei-Ling Chen': .14, 'Fatou Diop': .32, 'Sven Lindqvist': .12}}

    def pick_package(kind, doula):
        if kind == 'Birth':
            if doula == 'Priya Raman': return _wchoice(r, ['Birth Essential', 'Birth Plus'], [.6, .4])
            return _wchoice(r, ['Birth Essential', 'Birth Plus', 'Birth Premier'], [.45, .38, .17])
        if kind == 'Postpartum': return _wchoice(r, ['Postpartum 40 Hours', 'Postpartum 80 Hours', 'Postpartum 120 Hours', 'Night Support 60 Hours'], [.35, .30, .15, .20])
        return _wchoice(r, ['Combined Essential', 'Combined Plus', 'Complete Care Bundle'], [.5, .42, .08])
    forced = [s for s in specs if s['doula']]
    recent = [s for s in specs if not s['doula'] and s['tag'] == 'recent']
    free = sorted([s for s in specs if not s['doula'] and s['tag'] != 'recent'], key=lambda s: s['edd'])
    drop = []
    for s in forced + recent + free:
        if not s['kind']: s['kind'] = _wchoice(r, CLIENT_KINDS, [.52, .30, .18])
        birth_service = s['kind'] != 'Postpartum'
        s['ws'] = s['edd'] - day(ONCALL_BEFORE); s['we'] = s['edd'] + day(ONCALL_AFTER)
        if not s['doula']:
            w = wt[s['kind']]
            order = sorted(cand[s['kind']], key=lambda n: -math.log(r.random()) / w[n])
            ok = [n for n in order if (not birth_service) or (cover(wins[n], s['ws'], s['we']) < MAX_OVERLAP and mcount(n, s['edd']) < DT[n]['cap_births'])]
            if ok: s['doula'] = ok[0]
            elif s['tag']: s['doula'] = min(order, key=lambda n: cover(wins[n], s['ws'], s['we']))
            else: drop.append(s); continue
        if not s['package']: s['package'] = pick_package(s['kind'], s['doula'])
        if birth_service:
            wins[s['doula']].append((s['ws'], s['we'], s['edd']))
            if s['backup'] is None:
                bk = sorted(BACKUP_NAMES, key=lambda n: (cover(bwins[n], s['ws'], s['we']), r.random()))[0]
                s['backup'] = bk
            if s['backup']: bwins[s['backup']].append((s['ws'], s['we'], s['edd']))
        else:
            s['backup'] = ''
    declined = [dict(edd=s['edd'], kind=s['kind']) for s in drop]
    specs[:] = [s for s in specs if s not in drop]
    # ---- dates, discount, source, area, cancel
    for s in specs:
        k = s['kind']; edd = s['edd']
        lead = r.randint(70, 200) if k != 'Postpartum' else r.randint(35, 150)
        s['signed'] = s['signed'] or min(edd - day(lead), TODAY - day(r.randint(1, 35)))
        s['birth'] = s['force_birth'] or (edd + day(int(_clip(round(r.gauss(-1, 6)), -12, 12))) if k != 'Postpartum' else None)
        s['care_start'] = (s['birth'] + day(r.randint(3, 8))) if k == 'Combined' else (edd + day(r.randint(2, 9)) if k == 'Postpartum' else None)
        s['discount'] = s['discount'] or _wchoice(r, DISCOUNTS, [.80, .12, .08])
        s['area'] = _wchoice(r, AREAS, [.55, .45])
        s['source'] = _wchoice(r, SOURCES, [.20, .22, .18, .10, .08, .08, .05, .09])
        s['cancel'] = None
        if not s['tag'] and r.random() < 0.075:
            lo = s['signed'] + day(12)
            hi = min(TODAY - day(1), (s['ws'] if k != 'Postpartum' else edd) - day(3))
            if hi > lo: s['cancel'] = lo + day(r.randint(0, (hi - lo).days))
    specs.sort(key=lambda s: (s['signed'], s['edd']))
    clients = []
    for i, s in enumerate(specs):
        s['client_id'] = 'CL-%04d' % (i + 1)
        s['client'] = person()
        s['phone'] = fake_phone(i); s['email'] = fake_email(s['client'], 0)
    # ---- visits, births, windows, packs, contracts, payments per client
    visits, births, packs, contracts, plans, pays, addons, windows, cancels, revs = [], [], [], [], [], [], [], [], [], []
    for s in specs:
        pk = PK[s['package']]; k = s['kind']; edd = s['edd']; cid, cn, dl, area = s['client_id'], s['client'], s['doula'], s['area']
        rate_m = AREA[area]['mileage_rate']
        cxl = s['cancel']
        end_day = cxl or (TODAY + day(400))     # nothing after a cancellation
        price = int(round(pk['price'] * (1 - DISCOUNT_PCT[s['discount']]) / 5.0)) * 5
        dep = round(price * pk['deposit_pct'])
        bal = price - dep
        if k == 'Postpartum' and pk['deposit_pct'] < 1: bal_due = edd
        elif k == 'Postpartum': bal_due = ''
        else: bal_due = max(edd - day(7 * BALANCE_WEEKS), s['signed'] + day(7))
        s['price'] = price; s['deposit'] = dep; s['balance'] = bal; s['bal_due'] = bal_due
        # visits
        vis = []
        if k != 'Postpartum':
            npre = pk['prenatal_visits']
            lo, hi = s['signed'] + day(10), s['ws'] - day(2)
            if hi <= lo: hi = lo + day(10)
            for j in range(npre):
                vd = lo + day(int((hi - lo).days * (j + 0.5) / npre))
                vis.append((vd, 'Prenatal visit', q(r.uniform(1.5, 2.5))))
            for j in range(pk['postpartum_visits']):
                vd = s['birth'] + day(r.randint(4, 8) + 6 * j)
                vis.append((vd, 'Debrief visit' if (j == 1) else 'Postpartum visit', q(r.uniform(2.5, 3.5))))
        extra_hours = 0.0; pp_target = 0.0
        if pk['postpartum_hours']:
            night = pk['package'].startswith('Night')
            ph = float(pk['postpartum_hours'])
            if s['hours_cap']: pp_target = s['hours_cap']
            else:
                pp_target = ph
                x = r.random()
                if x < 0.12: extra_hours = float(r.randint(4, 12)); pp_target = ph + extra_hours
                elif x < 0.27: pp_target = ph - float(r.randint(4, 10))
            start = s['care_start']
            for vd, h in _pp_visits(r, start, pp_target, night):
                vis.append((vd, 'Night shift' if night else 'Postpartum visit', h))
        s['_extra_hours'] = extra_hours
        vis = [v for v in vis if v[0] <= end_day]
        vis.sort()
        for vd, kd, h in vis:
            if vd <= TODAY:
                visits.append(dict(date=vd, client_id=cid, client=cn, doula=dl, kind=kd, hours=h, miles=_miles(r, area), area=area))
        s['_visits_all'] = vis
        # on-call window
        if k != 'Postpartum' and not cxl:
            bd = s['birth']
            windows.append(dict(client_id=cid, client=cn, doula=dl, backup=s['backup'], edd=edd, oncall_start=s['ws'], oncall_end=s['we'], area=area,
                                _birth=bd, _contact=round(pk['oncall_hours'] * r.uniform(0.6, 1.5), 1)))
        # births
        s['_backup_used'] = False
        if k != 'Postpartum' and not cxl and s['birth'] <= TODAY:
            bd = s['birth']
            bh = q(_clip(r.gauss(15.5, 6.0), 5, 34))
            call_h = _wchoice(r, list(range(24)), [3, 3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3])
            call_min = call_h * 60 + r.randint(0, 59)
            arrive = call_min + r.randint(40, 110)
            leave = arrive + int(bh * 60)
            used = bool(s['backup']) and s['tag'] == '' and r.random() < 0.07
            by = s['backup'] if used else dl
            s['_backup_used'] = used
            adate = bd + day(arrive // 1440)
            births.append(dict(date=adate, client_id=cid, client=cn, doula=by, assigned=dl, backup_used=used, call_time=_hm(call_min), arrive_time=_hm(arrive), leave_time=_hm(leave),
                               hours=bh, miles=_miles(r, area), area=area, on_call_day=(adate - s['ws']).days + 1))
            s['_birth_hours'] = bh
        # pack
        if pk['postpartum_hours']:
            used_h = sum(h for vd, kd, h in vis if vd <= TODAY and kd in ('Postpartum visit', 'Night shift'))
            all_h = sum(h for vd, kd, h in vis if kd in ('Postpartum visit', 'Night shift'))
            pexp = edd + day(PACK_EXPIRY_DAYS)
            ppv = pk['pp_value'] * (1 - DISCOUNT_PCT[s['discount']])
            packs.append(dict(client_id=cid, client=cn, doula=dl, package=s['package'], hours_bought=float(pk['postpartum_hours']), price=float(int(round(ppv / 5.0)) * 5),
                              bought_on=s['signed'], expires_on=pexp, hours_used=q(used_h), extra_hours=extra_hours if used_h > pk['postpartum_hours'] - 0.01 else 0.0,
                              _all=q(all_h), _cancel=cxl))
        # contract
        status = 'Cancelled' if cxl else 'Signed'
        contracts.append(dict(client_id=cid, client=cn, package=s['package'], kind=k, list_price=pk['price'], discount=s['discount'], price=float(price), deposit=float(dep),
                              signed_on=s['signed'], deposit_paid_on=min(s['signed'] + day(r.randint(0, 3)), TODAY), balance_due=bal_due, balance_paid_on='', plan='Pay in full',
                              instalments=0, status=status, _s=s))
    # contract plans and payments
    for c in contracts:
        s = c['_s']; k = c['kind']; pk = PK[c['package']]; cid, cn = c['client_id'], c['client']; cxl = s['cancel']
        c['status'] = 'Cancelled' if cxl else 'Signed'
        paid_items = []        # (date, kind, amount)
        paid_items.append((c['deposit_paid_on'], 'Deposit', c['deposit']))
        bal = s['balance']
        n_inst = 0
        if bal > 0 and k != 'Postpartum' and (s['plan_dues'] or (bal >= 600 and r.random() < 0.40)):
            if s['plan_dues']:
                dues = s['plan_dues']
            else:
                n = _wchoice(r, [3, 4], [.55, .45]); last = s['ws'] - day(1) - day(r.randint(0, 5))
                dues = [last - day(28 * (n - 1 - j)) for j in range(n)]
                while len(dues) > 1 and dues[0] < s['signed'] + day(10): dues = dues[1:]
            if len(dues) >= 2:
                n_inst = len(dues); c['plan'] = 'Instalments'; c['instalments'] = n_inst
                each = round(bal / n_inst, 2)
                for j, dd in enumerate(dues):
                    amt = each if j < n_inst - 1 else round(bal - each * (n_inst - 1), 2)
                    delay = _wchoice(r, [r.randint(-2, 0), r.randint(1, 3), r.randint(4, 12), r.randint(15, 30)], [.60, .25, .11, .04])
                    pdate = dd + day(delay)
                    if s['tag'] == 'plan': pdate = dd if dd <= TODAY - day(1) else None
                    if pdate is not None and (pdate > TODAY or (cxl and pdate > cxl)): pdate = None
                    if cxl and dd > cxl: continue
                    plans.append(dict(client_id=cid, client=cn, no=j + 1, of=n_inst, due_date=dd, amount=amt, paid_on=pdate if pdate else '', status='Paid' if pdate else 'Unpaid'))
                    if pdate: paid_items.append((pdate, 'Instalment', amt))
        if n_inst == 0 and bal > 0:
            due = c['balance_due']
            pdate = due + day(r.randint(-12, 5)); pdate = max(pdate, s['signed'] + day(1))
            ok = pdate <= TODAY and not (cxl and pdate > cxl)
            if ok:
                paid_items.append((pdate, 'Balance', float(bal))); c['balance_paid_on'] = pdate
        c['_paid_items'] = paid_items
        s['_paid_items'] = paid_items
    # a few old unpaid balances (ageing demo): pay-in-full birth/combined clients that have a balance due 10..70 days ago
    want = [12, 27, 41, 66]
    pool = [c for c in contracts if c['plan'] == 'Pay in full' and c['balance_paid_on'] and c['kind'] != 'Postpartum' and c['status'] == 'Signed' and not c['_s']['tag']
            and c['balance_due'] != '' and 8 <= (TODAY - c['balance_due']).days <= 75 and c['balance_paid_on'] > TODAY - day(60)]
    for w in want:
        if not pool: break
        c = min(pool, key=lambda x: abs((TODAY - x['balance_due']).days - w)); pool.remove(c)
        c['_paid_items'] = [x for x in c['_paid_items'] if x[1] != 'Balance']; c['balance_paid_on'] = ''
        c['_s']['_paid_items'] = c['_paid_items']
    # hours invoices (extra hours), add-ons
    for s in specs:
        cid, cn = s['client_id'], s['client']; cxl = s['cancel']; pk = PK[s['package']]
        if s['_extra_hours'] and not cxl:
            vs = [v for v in s['_visits_all'] if v[1] in ('Postpartum visit', 'Night shift')]
            if vs:
                ld = vs[-1][0] + day(7)
                if ld <= TODAY: s['_paid_items'].append((ld, 'Hours invoice', round(s['_extra_hours'] * 38.0, 2)))
        s['_addons'] = []
        if cxl: continue
        k = s['kind']
        if (k != 'Postpartum' and r.random() < 0.30) or (k == 'Postpartum' and r.random() < 0.12):
            for _ in range(_wchoice(r, [1, 2], [.75, .25])):
                nm = _wchoice(r, ['Extra prenatal visit', 'Class seat (series)', 'Photography referral', 'Support referral note', 'Debrief visit'], [.30, .35, .15, .10, .10]) if k != 'Postpartum' \
                    else _wchoice(r, ['Support referral note', 'Photography referral', 'Debrief visit'], [.4, .3, .3])
                a = PK[nm]
                if k == 'Postpartum': ad = s['care_start'] + day(r.randint(5, 30))
                elif nm == 'Debrief visit': ad = s['birth'] + day(r.randint(20, 40))
                else: ad = s['signed'] + day(r.randint(7, max(8, (s['ws'] - s['signed']).days - 5)))
                if ad > TODAY or any(x[0] == nm for x in s['_addons']): continue
                s['_addons'].append((nm, ad))
                addons.append(dict(date=ad, client_id=cid, client=cn, addon=nm, price=a['price'], hours=a['oncall_hours'] + 2.0 * (nm in ('Extra prenatal visit', 'Debrief visit')), doula=s['doula']))
                s['_paid_items'].append((ad, 'Add-on', a['price']))
                if nm == 'Extra prenatal visit': visits.append(dict(date=ad, client_id=cid, client=cn, doula=s['doula'], kind='Prenatal visit', hours=2.0, miles=_miles(r, s['area']), area=s['area']))
                if nm == 'Debrief visit': visits.append(dict(date=ad, client_id=cid, client=cn, doula=s['doula'], kind='Debrief visit', hours=2.0, miles=_miles(r, s['area']), area=s['area']))
        for (d_, kd, amt) in s['_paid_items']:
            pays.append(dict(date=d_, client_id=cid, client=cn, kind=kd, amount=float(amt), method=_wchoice(r, PAY_METHODS, [.45, .35, .05, .15])))
    # guaranteed recent add-ons (this month and the last 30 days)
    tgt = [s for s in specs if s['kind'] != 'Postpartum' and not s['cancel'] and s['birth'] > TODAY and s['signed'] < TODAY - day(14)]
    for s, (nm, off) in zip(tgt[:2], (('Class seat (series)', min(2, TODAY.day - 1)), ('Extra prenatal visit', 12))):
        if any(x[0] == nm for x in s['_addons']): continue
        a = PK[nm]; ad = TODAY - day(off)
        s['_addons'].append((nm, ad))
        addons.append(dict(date=ad, client_id=s['client_id'], client=s['client'], addon=nm, price=a['price'], hours=2.0 if nm == 'Extra prenatal visit' else 0.0, doula=s['doula']))
        pays.append(dict(date=ad, client_id=s['client_id'], client=s['client'], kind='Add-on', amount=float(a['price']), method=_wchoice(r, PAY_METHODS, [.45, .35, .05, .15])))
        if nm == 'Extra prenatal visit': visits.append(dict(date=ad, client_id=s['client_id'], client=s['client'], doula=s['doula'], kind='Prenatal visit', hours=2.0, miles=_miles(r, s['area']), area=s['area']))
    # cancellations and changes
    for c in contracts:
        s = c['_s']; cxl = s['cancel']
        if cxl:
            paid = round(sum(a for d_, kd, a in s['_paid_items'] if d_ <= cxl), 2)
            kept = round(min(paid, c['deposit']) if r.random() < 0.7 else paid * 0.5, 2)
            cancels.append(dict(date=cxl, client_id=c['client_id'], client=c['client'], kind='Cancelled', reason=_wchoice(r, CANCEL_REASONS, [.2, .15, .2, .15, .2, .1]), paid=paid, kept=kept,
                                refunded=round(paid - kept, 2)))
    chg_pool = [c for c in contracts if c['status'] == 'Signed' and c['kind'] != 'Postpartum' and (TODAY - c['signed_on']).days > 30 and not c['_s']['tag']]
    for c in r.sample(chg_pool, min(len(chg_pool), 22)):
        s = c['_s']
        cd = c['signed_on'] + day(r.randint(14, 45))
        if cd > TODAY: continue
        kind = _wchoice(r, ['Package changed', 'Hours reduced'], [.6, .4])
        paid = round(sum(a for d_, kd, a in s['_paid_items'] if d_ <= cd), 2)
        ref = float(r.choice([60, 90, 120, 150, 200, 250])) if kind == 'Package changed' else float(r.choice([100, 150, 200, 300]))
        cancels.append(dict(date=cd, client_id=c['client_id'], client=c['client'], kind=kind, reason=_wchoice(r, CANCEL_REASONS, [.1, .1, .3, .3, .1, .1]), paid=paid, kept=0.0, refunded=ref))
    cancels.sort(key=lambda x: x['date'])
    return dict(r=r, specs=specs, visits=visits, births=births, packs=packs, contracts=contracts, plans=plans, pays=pays, addons=addons, windows=windows, cancels=cancels,
                person=person, wins=wins, bwins=bwins, declined=declined)


# ------------------------------------------------------------------ finishing: status, enquiries, pay lines, classes, referrals, reviews, money
def _svc(kind): return {'Birth': 'Birth', 'Postpartum': 'Postpartum', 'Combined': 'Both'}[kind]


def _status(s):
    if s['cancel']: return 'Cancelled'
    k = s['kind']
    if k != 'Postpartum' and s['birth'] > TODAY: return 'On call' if s['ws'] <= TODAY else 'Booked'
    if k == 'Postpartum' and TODAY < s['care_start']: return 'Booked'
    pk = PK[s['package']]
    if k == 'Birth':
        last = max([v[0] for v in s['_visits_all'] if v[1] in ('Postpartum visit', 'Debrief visit')] + [s['birth']])
        return 'Postpartum care' if TODAY <= last else 'Completed'
    vs = [v for v in s['_visits_all'] if v[1] in ('Postpartum visit', 'Night shift')]
    if any(v[0] > TODAY for v in vs): return 'Postpartum care'
    used = sum(v[2] for v in vs if v[0] <= TODAY)
    if used < pk['postpartum_hours'] - 0.01 and TODAY <= s['edd'] + day(PACK_EXPIRY_DAYS): return 'Postpartum care'
    return 'Completed'


def _care_end(s):
    vs = [v[0] for v in s['_visits_all']]
    base = s['birth'] or s['care_start']
    return max(vs + [base])


def _final():
    W = _raw('world', _world); r = rng('final' + _SIM_TAG); specs = W['specs']; person = W['person']
    out = {}
    SP = {s['client_id']: s for s in specs}
    # ---- clients
    cl = []
    for s in specs:
        s['status'] = _status(s)
        k = s['kind']
        cl.append(dict(client_id=s['client_id'], client=s['client'], phone=s['phone'], email=s['email'], area=s['area'], kind=k, package=s['package'], edd=s['edd'],
                       due_month=_ms(s['edd']), doula=s['doula'], backup=s['backup'], source=s['source'], signed_on=s['signed'], status=s['status'],
                       oncall_start=s['ws'] if k != 'Postpartum' else '', oncall_end=s['we'] if k != 'Postpartum' else '',
                       attended_on=s['birth'] if (k != 'Postpartum' and not s['cancel'] and s['birth'] <= TODAY) else '', discount=s['discount']))
    out['clients'] = cl
    # ---- contracts
    ct = []
    for i, c in enumerate(sorted(W['contracts'], key=lambda c: (c['signed_on'], c['client_id']))):
        x = {k: v for k, v in c.items() if not k.startswith('_')}
        x['contract_id'] = 'CT-%04d' % (i + 1); ct.append(x)
    for x in ct:
        if SP[x['client_id']]['status'] == 'Completed': x['status'] = 'Completed'
    out['contracts'] = [dict(contract_id=x['contract_id'], **{k: v for k, v in x.items() if k != 'contract_id'}) for x in ct]
    pl = sorted(W['plans'], key=lambda p: (p['due_date'], p['client_id']))
    for i, p in enumerate(pl): p['inst_id'] = 'PI-%04d' % (i + 1)
    out['plans'] = [dict(inst_id=p['inst_id'], **{k: v for k, v in p.items() if k != 'inst_id'}) for p in pl]
    py = sorted(W['pays'], key=lambda p: (p['date'], p['client_id']))
    for i, p in enumerate(py): p['payment_id'] = 'PY-%05d' % (i + 1); p['month'] = _ms(p['date'])
    out['payments'] = [dict(payment_id=p['payment_id'], date=p['date'], month=p['month'], client_id=p['client_id'], client=p['client'], kind=p['kind'], amount=p['amount'], method=p['method']) for p in py]
    ad = sorted(W['addons'], key=lambda a: (a['date'], a['client_id']))
    out['addons'] = [dict(addon_id='AD-%04d' % (i + 1), date=a['date'], month=_ms(a['date']), client_id=a['client_id'], client=a['client'], addon=a['addon'], price=a['price'], hours=a['hours'],
                          doula=a['doula']) for i, a in enumerate(ad)]
    # ---- windows, births, visits, packs
    wl = sorted(W['windows'], key=lambda w: (w['oncall_start'], w['client_id']))
    out['oncall'] = []
    for i, w in enumerate(wl):
        done = w['_birth'] <= TODAY
        part = 1.0 if done else max(0.0, min(1.0, (TODAY - w['oncall_start']).days / float(ONCALL_BEFORE + 8)))
        out['oncall'].append(dict(window_id='OW-%04d' % (i + 1), client_id=w['client_id'], client=w['client'], doula=w['doula'], backup=w['backup'], edd=w['edd'], oncall_start=w['oncall_start'],
                                  oncall_end=w['oncall_end'], area=w['area'], attended_on=w['_birth'] if done else '',
                                  contact_hours=round(w['_contact'] * part, 1) if w['oncall_start'] <= TODAY else ''))
    bl = sorted(W['births'], key=lambda b: (b['date'], b['client_id']))
    out['births'] = [dict(birth_id='BT-%04d' % (i + 1), date=b['date'], month=_ms(b['date']), client_id=b['client_id'], client=b['client'], doula=b['doula'], assigned=b['assigned'],
                          backup_used=b['backup_used'], call_time=b['call_time'], arrive_time=b['arrive_time'], leave_time=b['leave_time'], hours=b['hours'], miles=b['miles'], area=b['area'],
                          on_call_day=b['on_call_day']) for i, b in enumerate(bl)]
    vl = sorted(W['visits'], key=lambda v: (v['date'], v['client_id']))
    out['visits'] = [dict(visit_id='VS-%05d' % (i + 1), date=v['date'], week=week_start(v['date']), month=_ms(v['date']), client_id=v['client_id'], client=v['client'], doula=v['doula'],
                          kind=v['kind'], hours=v['hours'], miles=v['miles'], area=v['area'], mileage_cost=R2(v['miles'] * AREA[v['area']]['mileage_rate'])) for i, v in enumerate(vl)]
    pk_ = sorted([p for p in W['packs'] if not p['_cancel']], key=lambda p: (p['bought_on'], p['client_id']))
    out['packs'] = [dict(pack_id='HP-%04d' % (i + 1), client_id=p['client_id'], client=p['client'], doula=p['doula'], package=p['package'], hours_bought=p['hours_bought'], price=p['price'],
                         bought_on=p['bought_on'], expires_on=p['expires_on'], hours_used=p['hours_used'], extra_hours=p['extra_hours']) for i, p in enumerate(pk_)]
    # ---- cancellations and changes
    out['cancels'] = [dict(cancel_id='CX-%03d' % (i + 1), date=c['date'], month=_ms(c['date']), client_id=c['client_id'], client=c['client'], kind=c['kind'], reason=c['reason'], paid=c['paid'],
                           kept=c['kept'], refunded=c['refunded']) for i, c in enumerate(W['cancels'])]
    # ---- rota
    rota = []; w0 = week_start(month_start(23)); cur = r.choice(BACKUP_NAMES); left = r.randint(1, 3); w = w0
    while w <= week_start(TODAY) + day(84):
        rota.append(dict(rota_id='RT-%03d' % (len(rota) + 1), week=w, backup=cur, stipend=BACKUP_STIPEND_WEEK))
        left -= 1; w += day(7)
        if left == 0: cur = [n for n in BACKUP_NAMES if n != cur][0]; left = r.randint(1, 3)
    out['rota'] = rota
    # ---- enquiries and consultations
    enq = []
    for s in specs:
        ed = s['signed'] - day(r.randint(4, 25))
        enq.append(dict(date=ed, name=s['client'], area=s['area'], service=_svc(s['kind']), edd_wanted=s['edd'], source=s['source'], status='Signed', reason='', signed_on=s['signed'],
                        client_id=s['client_id'], package_quoted=s['package'], quote=float(PK[s['package']]['price']), consult=ed + day(r.randint(1, max(1, min(7, (s['signed'] - ed).days - 1)))),
                        _doula=s['doula'], _outcome='Signed'))
    by_m = {}
    for e in enq: by_m[_ms(e['date'])] = by_m.get(_ms(e['date']), 0) + 1
    for m in sorted(by_m):
        nm = int(round(by_m[m] * 1.35 * (0.8 + 0.4 * r.random())))
        last = min(_eom(m), TODAY - day(1))
        if m == _ms(TODAY): nm = max(2, int(round(nm * (TODAY.day / 30.0))))
        for _ in range(nm):
            d_ = m + day(r.randint(0, max(0, (last - m).days)))
            if d_ > last: d_ = last
            kd = _wchoice(r, CLIENT_KINDS, [.52, .30, .18])
            reason = _wchoice(r, LOST_REASONS, [.30, .22, .08, .25, .15])
            pkg = _wchoice(r, [p['package'] for p in packages if p['kind'] == kd], {'Birth': [.45, .38, .17], 'Postpartum': [.35, .30, .15, .20], 'Combined': [.5, .42, .08]}[kd])
            cons = ''
            if reason != 'No reply' and (TODAY - d_).days >= 9 and r.random() < 0.62: cons = d_ + day(r.randint(1, 8))
            enq.append(dict(date=d_, name=person(), area=_wchoice(r, AREAS, [.55, .45]), service=_svc(kd), edd_wanted=d_ + day(r.randint(100, 240)),
                            source=_wchoice(r, SOURCES, [.20, .22, .18, .10, .08, .08, .05, .09]), status='Lost', reason=reason, signed_on='', client_id='',
                            package_quoted=pkg if (cons or reason == 'Price') else '', quote=float(PK[pkg]['price']) if (cons or reason == 'Price') else '', consult=cons,
                            _doula=r.choice(['Amara Okonkwo', 'Mei-Ling Chen', 'Lucia Ferreira']), _outcome=_wchoice(r, ['Declined', 'Thinking', 'No-show'], [.45, .40, .15])))
    for dc in W['declined']:
        d_ = dc['edd'] - day(r.randint(90, 200))
        if d_ > TODAY - day(1): d_ = TODAY - day(r.randint(3, 40))
        cons = d_ + day(r.randint(1, 8)) if r.random() < 0.7 else ''
        pkg = _wchoice(r, [p['package'] for p in packages if p['kind'] == dc['kind']], {'Birth': [.45, .38, .17], 'Postpartum': [.35, .30, .15, .20], 'Combined': [.5, .42, .08]}[dc['kind']])
        enq.append(dict(date=d_, name=person(), area=_wchoice(r, AREAS, [.55, .45]), service=_svc(dc['kind']), edd_wanted=dc['edd'], source=_wchoice(r, SOURCES, [.20, .22, .18, .10, .08, .08, .05, .09]),
                        status='Lost', reason='Date full', signed_on='', client_id='', package_quoted=pkg, quote=float(PK[pkg]['price']), consult=cons, _doula=r.choice(['Amara Okonkwo', 'Mei-Ling Chen', 'Lucia Ferreira']),
                        _outcome='Declined'))
    for age in (0, 0, 1, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13, 15, 18, 22):
        d_ = TODAY - day(age); kd = _wchoice(r, CLIENT_KINDS, [.52, .30, .18])
        pkg = _wchoice(r, [p['package'] for p in packages if p['kind'] == kd], {'Birth': [.45, .38, .17], 'Postpartum': [.35, .30, .15, .20], 'Combined': [.5, .42, .08]}[kd])
        if age <= 1: st, cons, oc = 'New', '', ''
        elif age <= 8: st, cons, oc = 'Consultation booked', TODAY + day(r.randint(0, 6)), 'Booked'
        elif age <= 14: st, cons, oc = 'Consultation held', d_ + day(r.randint(3, 7)), 'Thinking'
        else: st, cons, oc = 'Contract sent', d_ + day(r.randint(3, 8)), 'Thinking'
        enq.append(dict(date=d_, name=person(), area=_wchoice(r, AREAS, [.55, .45]), service=_svc(kd), edd_wanted=d_ + day(r.randint(100, 240)),
                        source=_wchoice(r, SOURCES, [.20, .22, .18, .10, .08, .08, .05, .09]), status=st, reason='', signed_on='', client_id='',
                        package_quoted=pkg if cons else '', quote=float(PK[pkg]['price']) if cons else '', consult=cons, _doula=r.choice(['Amara Okonkwo', 'Mei-Ling Chen', 'Lucia Ferreira']), _outcome=oc))
    enq.sort(key=lambda e: (e['date'], e['name']))
    for i, e in enumerate(enq):
        e['enquiry_id'] = 'EN-%04d' % (i + 1); e['month'] = _ms(e['date']); e['phone'] = fake_phone(300 + i); e['email'] = fake_email(e['name'], 0)
        slow = e['status'] == 'Lost' and e['reason'] == 'No reply'
        e['first_reply_hours'] = '' if (e['status'] == 'New' and (TODAY - e['date']).days == 0) else round(_clip(r.lognormvariate(1.7 + (0.8 if slow else 0.0), 0.9), 0.5, 96), 1)
    out['enquiries'] = [dict(enquiry_id=e['enquiry_id'], date=e['date'], month=e['month'], name=e['name'], phone=e['phone'], email=e['email'], area=e['area'], service=e['service'],
                             edd_wanted=e['edd_wanted'], source=e['source'], first_reply_hours=e['first_reply_hours'], status=e['status'], reason=e['reason'], package_quoted=e['package_quoted'],
                             quote=e['quote'], consult_date=e['consult'], signed_on=e['signed_on'], client_id=e['client_id']) for e in enq]
    cs = []
    for e in sorted([e for e in enq if e['consult'] != ''], key=lambda e: (e['consult'], e['enquiry_id'])):
        booked = e['consult'] >= TODAY
        oc = 'Booked' if booked else ('Signed' if e['status'] == 'Signed' else (e['_outcome'] or 'Thinking'))
        cs.append(dict(consult_id='CN-%04d' % (len(cs) + 1), enquiry_id=e['enquiry_id'], date=e['consult'], name=e['name'], doula=e['_doula'] if e['status'] != 'Signed' else (e['_doula'] if r.random() < 0.7 else OWNER),
                       minutes='' if booked else int(r.choice([20, 25, 30, 35, 40, 45, 60])), outcome=oc,
                       follow_up_on=(e['consult'] + day(5)) if oc == 'Thinking' else ''))
    out['consults'] = cs
    # ---- referrals
    ref_src = ['Care provider', 'Past client', 'Support professional', 'Class or workshop']
    offices = ['Birchwood Care Office', 'Harbour Care Office', 'Linden Care Office', 'Oakfield Care Office', 'Riverside Care Office']
    support = ['Aiko Tanaka', 'Nadia Ramos', 'Olu Bankole']
    gift = {x['source']: x['gift_value'] for x in sources_ref}
    past = [(s['signed'], s['client']) for s in specs if s['status'] in ('Completed', 'Postpartum care')]
    rf = []
    for e in enq:
        if e['source'] not in ref_src: continue
        if e['source'] == 'Care provider': who = _wchoice(r, offices, [.3, .25, .2, .15, .1])
        elif e['source'] == 'Support professional': who = _wchoice(r, support, [.5, .3, .2])
        elif e['source'] == 'Class or workshop': who = _wchoice(r, CLASS_TYPES, [.25, .25, .2, .15, .15])
        else:
            pc = [n for (sd, n) in past if sd < e['date'] and n != e['name']]
            who = r.choice(pc) if pc else 'Willow family'
        th = ''
        if e['status'] == 'Signed' and r.random() < 0.8:
            t_ = e['signed_on'] + day(r.randint(3, 20))
            if t_ <= TODAY: th = t_
        rf.append(dict(date=e['date'], month=e['month'], source=e['source'], referrer=who, enquiry_id=e['enquiry_id'], client_id=e['client_id'], thanked_on=th,
                       gift_cost=gift[e['source']] if th else 0.0))
    out['referrals'] = [dict(referral_id='RF-%04d' % (i + 1), **x) for i, x in enumerate(rf)]
    # ---- classes
    cls = []; cur_ct = list(CT)
    for k in range(23, -1, -1):
        ms = month_start(k)
        n = 1 if ms.month == 12 else r.randint(3, 5)
        last = _eom(ms) if k else TODAY
        span = max(1, (last - ms).days)
        ds = sorted(ms + day(r.randint(0, span)) for _ in range(n))
        if k == 0 and not ds: ds = [TODAY]
        for d_ in ds:
            if d_ > TODAY: d_ = TODAY
            t = _wchoice(r, cur_ct, [.20, .22, .20, .18, .20]); ct_ = CT[t]
            su = max(2, int(round(ct_['seats'] * r.uniform(0.45, 0.95)))); at = max(1, int(round(su * r.uniform(0.8, 1.0))))
            inst = r.choice(['Amara Okonkwo', 'Lucia Ferreira', 'Mei-Ling Chen']) if t == 'Education series' else r.choice(['Amara Okonkwo', 'Katarzyna Nowak', 'Fatou Diop', 'Sven Lindqvist', 'Mei-Ling Chen'])
            cls.append(dict(date=d_, month=_ms(d_), **{'class': t}, venue=r.choice(['Maple Hall', 'Cedar Room', 'Harbour Studio']), instructor=inst, seats=ct_['seats'], signed_up=su, attended=at,
                            price=ct_['price'], hours=ct_['hours'], venue_cost=float(round(40 * ct_['hours'] + r.randint(0, 25))), income=R2(su * ct_['price']), new_clients=0))
    cls.sort(key=lambda c: c['date'])
    for i, c in enumerate(cls): c['session_id'] = 'CS-%03d' % (i + 1)
    att = []
    pg = rng('att' + _SIM_TAG)
    def short(): f, l = _G[pg.randrange(len(_G))]; return pg.choice(f) + ' ' + pg.choice(l)[0] + '.'
    for c in cls:
        for j in range(c['signed_up']):
            att.append(dict(session_id=c['session_id'], date=c['date'], attendee=short(), client_id='', paid=c['price'], attended=j < c['attended']))
    for s in specs:
        if s['source'] != 'Class or workshop': continue
        ed = s['signed'] - day(10)
        cand = [i for i, a in enumerate(att) if ed - day(120) <= a['date'] <= ed and a['client_id'] == '' and a['attended']]
        if cand:
            a = att[cand[len(cand) // 2]]; a['client_id'] = s['client_id']
            a['attendee'] = s['client'].split()[0] + ' ' + s['client'].split()[-1][0] + '.'
    for a in att:
        if a['client_id']: [c for c in cls if c['session_id'] == a['session_id']][0]['new_clients'] += 1
    out['class_sessions'] = [dict(session_id=c['session_id'], **{k: v for k, v in c.items() if k != 'session_id'}) for c in cls]
    out['class_attendees'] = [dict(attendee_id='CA-%04d' % (i + 1), **a) for i, a in enumerate(att)]
    # ---- reviews
    rv = []
    for s in specs:
        if s['status'] != 'Completed': continue
        ce = _care_end(s); ask = ce + day(REVIEW_ASK_DAYS)
        if ask > TODAY or r.random() > 0.85: continue
        rec = ''
        if r.random() < 0.65:
            t_ = ask + day(r.randint(2, 25))
            if t_ <= TODAY: rec = t_
        rv.append(dict(client_id=s['client_id'], client=s['client'], doula=s['doula'], asked_on=ask, received_on=rec,
                       stars=_wchoice(r, [5, 4, 3, 2], [.68, .26, .05, .01]) if rec else '', channel=_wchoice(r, CHANNELS, [.40, .45, .15]) if rec else ''))
    rv.sort(key=lambda x: (x['asked_on'], x['client_id']))
    out['reviews'] = [dict(review_id='RV-%04d' % (i + 1), **x) for i, x in enumerate(rv)]
    # ---- pay lines
    lines = []
    miles_m = {}
    for v in W['visits']:
        key = (_ms(v['date']), v['doula']); miles_m[key] = miles_m.get(key, 0.0) + v['miles'] * AREA[v['area']]['mileage_rate']
    miles_n = {}
    for v in W['visits']: miles_n[(_ms(v['date']), v['doula'])] = miles_n.get((_ms(v['date']), v['doula']), 0.0) + v['miles']
    for b in W['births']:
        key = (_ms(b['date']), b['doula']); miles_m[key] = miles_m.get(key, 0.0) + b['miles'] * AREA[b['area']]['mileage_rate']; miles_n[key] = miles_n.get(key, 0.0) + b['miles']
    for s in specs:
        if s['cancel'] or s['doula'] == OWNER: continue
        dl = s['doula']; d = DT[dl]; pk = PK[s['package']]; f = s['price'] / pk['price']
        if s['kind'] != 'Postpartum' and s['birth'] <= TODAY:
            gross = R2(pk['birth_value'] * f); pay = R2(gross * (1 - d['agency_share']))
            hrs = sum(v[2] for v in s['_visits_all'] if v[0] <= TODAY and v[1] in ('Prenatal visit', 'Postpartum visit', 'Debrief visit')) + s.get('_birth_hours', 0.0)
            if s['_backup_used']:
                lines.append(dict(month=_ms(s['birth']), doula=s['backup'], client_id=s['client_id'], client=s['client'], basis='Backup call-out', hours=s.get('_birth_hours', 0.0), gross=0.0,
                                  agency_share=0.0, pay_due=BACKUP_FLAT_PAY, miles=0.0))
                pay = max(0.0, R2(pay - BACKUP_FLAT_PAY))
            lines.append(dict(month=_ms(s['birth']), doula=dl, client_id=s['client_id'], client=s['client'], basis='Per client', hours=q(hrs), gross=gross, agency_share=d['agency_share'],
                              pay_due=pay, miles=0.0))
        if pk['postpartum_hours'] and d['hourly_pay']:
            rate = pk['pp_value'] * f / pk['postpartum_hours']; bym = {}
            for vd, kd, h in s['_visits_all']:
                if kd in ('Postpartum visit', 'Night shift') and vd <= TODAY: bym[_ms(vd)] = bym.get(_ms(vd), 0.0) + h
            for m, h in sorted(bym.items()):
                gross = R2(h * rate); pay = R2(h * d['hourly_pay'])
                lines.append(dict(month=m, doula=dl, client_id=s['client_id'], client=s['client'], basis='Per hour', hours=q(h), gross=gross, agency_share=round(1 - pay / gross, 3) if gross else 0.0,
                                  pay_due=pay, miles=0.0))
    for (m, dl), amt in miles_m.items():
        if dl == OWNER: continue
        lines.append(dict(month=m, doula=dl, client_id='', client='', basis='Mileage', hours=0.0, gross=0.0, agency_share=0.0, pay_due=R2(amt), miles=round(miles_n[(m, dl)], 1)))
    stip = {}
    for rw in rota:
        if rw['week'] <= week_start(TODAY): stip[(_ms(rw['week']), rw['backup'])] = stip.get((_ms(rw['week']), rw['backup']), 0.0) + rw['stipend']
    for (m, bk), amt in stip.items():
        lines.append(dict(month=m, doula=bk, client_id='', client='', basis='Backup stipend', hours=0.0, gross=0.0, agency_share=0.0, pay_due=R2(amt), miles=0.0))
    lines.sort(key=lambda x: (x['month'], x['doula'], x['client_id'], x['basis']))
    cm = _ms(TODAY); odd = set(r.sample(range(len(lines)), 7))
    for i, x in enumerate(lines):
        pd_ = add_months(x['month'], 1).replace(day=8)
        if x['month'] < cm and pd_ <= TODAY:
            x['paid_on'] = pd_; x['status'] = 'Paid'
            x['paid_amount'] = R2(x['pay_due'] - (min(40.0, round(x['pay_due'] * 0.04, 2)) if (i in odd and x['pay_due'] > 100) else 0.0))
        else:
            x['paid_on'] = ''; x['status'] = 'Due'; x['paid_amount'] = 0.0
        x['pay_id'] = 'DP-%05d' % (i + 1)
    out['pay'] = [dict(pay_id=x['pay_id'], month=x['month'], doula=x['doula'], client_id=x['client_id'], client=x['client'], basis=x['basis'], hours=x['hours'], miles=x['miles'], gross=x['gross'],
                       agency_share=x['agency_share'], pay_due=x['pay_due'], paid_amount=x['paid_amount'], paid_on=x['paid_on'], status=x['status']) for x in lines]
    # ---- renewals, training, time off
    rn = []; rr = rng('renew' + _SIM_TAG)
    items = {OWNER: [x['item'] for x in renewal_items]}
    for n in CONTRACTED: items[n] = ['Certification renewal', 'Continuing education', 'First aid course', 'Background check']
    for n in BACKUP_NAMES: items[n] = ['Certification renewal', 'First aid course', 'Background check']
    for holder, its in items.items():
        for it in its:
            cyc = RI[it]['cycle_days']
            if holder == OWNER and it == 'Liability insurance': nxt = TODAY + day(12)
            else: nxt = TODAY + day(rr.randint(50, min(700, cyc + 40)))
            cur_ = nxt; first = True
            while cur_ > TODAY - day(780):
                if first: rn.append(dict(holder=holder, item=it, due_date=cur_, renewed_on='', cost=RI[it]['cost']))
                else: rn.append(dict(holder=holder, item=it, due_date=cur_, renewed_on=cur_ - day(rr.randint(3, 20)), cost=RI[it]['cost']))
                first = False; cur_ -= day(cyc)
    rn.sort(key=lambda x: (x['due_date'], x['holder'], x['item']))
    out['renewals'] = [dict(renewal_id='RN-%03d' % (i + 1), **x) for i, x in enumerate(rn)]
    tr = []; titles = {'Workshop': ['Client communication skills', 'Records and contracts'], 'Online course': ['Running a small business', 'Support-person coaching'],
                       'Training day': ['Postpartum support skills', 'Peer case discussion'], 'Peer circle': ['Peer case discussion'], 'First aid course': ['First aid refresher']}
    for holder in [OWNER] + CONTRACTED + BACKUP_NAMES:
        for yr in (0, 1):
            for _ in range(rr.randint(2, 4)):
                dd = TODAY - day(yr * 365 + rr.randint(5, 360))
                kd = _wchoice(rr, CPD_KINDS, [.25, .25, .2, .15, .15])
                tr.append(dict(holder=holder, kind=kd, title=rr.choice(titles[kd]), date=dd, hours=float(rr.choice([2, 3, 4, 6, 8, 12])), cost=float(rr.choice([0, 25, 60, 95, 150, 220]))))
    for holder in (OWNER, 'Mei-Ling Chen', 'Sven Lindqvist', 'Fatou Diop', 'Priya Raman'):
        tr.append(dict(holder=holder, kind='Training day', title='Postpartum support skills', date=TODAY + day(rr.randint(15, 120)), hours=8.0, cost=150.0))
    tr.sort(key=lambda x: (x['date'], x['holder']))
    out['training'] = [dict(training_id='TR-%03d' % (i + 1), **x) for i, x in enumerate(tr)]
    to = []; wl_by = {}
    for w in W['windows']: wl_by.setdefault(w['doula'], []).append((w['oncall_start'], w['oncall_end']))
    for holder in [OWNER] + CONTRACTED + BACKUP_NAMES:
        mine = wl_by.get(holder, [])
        for _ in range(rr.randint(3, 5)):
            for _try in range(40):
                kd = _wchoice(rr, TIMEOFF_KINDS, [.4, .2, .25, .15])
                ln = {'Holiday': rr.randint(7, 14), 'Training': rr.randint(2, 3), 'Family time': rr.randint(3, 5), 'Rest block': rr.randint(3, 7)}[kd]
                st = TODAY + day(rr.randint(-600, 200))
                if any(st <= b and a <= st + day(ln) for a, b in mine): continue
                if any(x['holder'] == holder and x['start'] <= st + day(ln) and st <= x['end'] for x in to): continue
                to.append(dict(holder=holder, start=st, end=st + day(ln), kind=kd)); break
    # one deliberate clash: the owner's family time falls on a booked client's on-call window
    fut = sorted([w for w in W['windows'] if w['doula'] == OWNER and w['oncall_start'] > TODAY + day(20)], key=lambda w: w['oncall_start'])
    if fut:
        w = fut[1] if len(fut) > 1 else fut[0]
        to = [x for x in to if not (x['holder'] == OWNER and x['start'] <= w['oncall_end'] and w['oncall_start'] <= x['end'])]
        to.append(dict(holder=OWNER, start=w['oncall_start'] + day(5), end=w['oncall_start'] + day(9), kind='Family time'))
    to.sort(key=lambda x: (x['start'], x['holder']))
    out['timeoff'] = [dict(timeoff_id='TO-%03d' % (i + 1), holder=x['holder'], start=x['start'], end=x['end'], kind=x['kind'], days=(x['end'] - x['start']).days + 1) for i, x in enumerate(to)]
    # ---- marketing
    mk = []; sg = {}
    for e in enq: sg[(e['month'], e['source'])] = sg.get((e['month'], e['source']), 0) + 1
    sg_signed = {}
    for e in enq:
        if e['status'] == 'Signed': sg_signed[(e['month'], e['source'])] = sg_signed.get((e['month'], e['source']), 0) + 1
    thanks = {}
    for x in rf:
        if x['thanked_on'] != '': thanks[_ms(x['thanked_on'])] = thanks.get(_ms(x['thanked_on']), 0.0) + x['gift_cost']
    mapping = {'Online listing': ['Directory listing'], 'Website upkeep': ['Online search'], 'Social posts': ['Social media'], 'Local flyers': ['Local event'], 'Event stand': ['Local event'],
               'Referral thank-yous': ref_src}
    for idx, m in enumerate(months24()):
        costs = {'Online listing': 60.0, 'Website upkeep': 35.0, 'Social posts': 40.0 + 10 * (idx % 3), 'Referral thank-yous': thanks.get(m, 0.0)}
        if idx % 2 == 0: costs['Local flyers'] = 45.0
        if idx % 3 == 1: costs['Event stand'] = 180.0 + 20 * (idx % 4)
        for kd in MARKETING_KINDS:
            if kd not in costs: continue
            en = sum(sg.get((m, s_), 0) for s_ in mapping[kd]); sn = sum(sg_signed.get((m, s_), 0) for s_ in mapping[kd])
            if kd in ('Local flyers', 'Event stand') and ('Local flyers' in costs and 'Event stand' in costs): en = (en + 1) // 2 if kd == 'Local flyers' else en // 2; sn = (sn + 1) // 2 if kd == 'Local flyers' else sn // 2
            mk.append(dict(month=m, kind=kd, source=mapping[kd][0], cost=R2(costs[kd]), enquiries=en, signed=sn))
    out['marketing'] = [dict(campaign_id='MK-%03d' % (i + 1), **x) for i, x in enumerate(mk)]
    # ---- expenses
    ex = []
    def add(d_, cat, desc, amt, to_):
        if d_ > TODAY: d_ = TODAY
        ex.append(dict(date=d_, month=_ms(d_), category=cat, description=desc, amount=R2(amt), paid_to=to_))
    card = {}
    for p in py:
        if p['method'] in ('Card payment', 'Payment link'): card[p['month']] = card.get(p['month'], 0.0) + p['amount']
    for idx, m in enumerate(months24()):
        add(m + day(4), 'Insurance', 'Monthly liability insurance instalment', 96.0, 'Callum Reid')
        add(m + day(2), 'Phone and software', 'Phone plan and online tools', 89.0, 'Phone and online tools')
        if m.month % 3 == 0: add(m + day(19), 'Accounting', 'Quarterly bookkeeping', 360.0, 'Rosa Delgado')
        for _ in range(r.randint(1, 3)): add(m + day(r.randint(0, 27)), 'Supplies and printing', r.choice(['Printing handouts', 'Welcome folders', 'Class materials', 'Postage and stationery']), r.randint(25, 95), 'Print and stationery shop')
        if m.month == 1: add(m + day(10), 'Memberships', 'Yearly professional membership', 120.0, 'Membership body')
        if r.random() < 0.5: add(m + day(r.randint(5, 25)), 'Other', r.choice(['Bank charge', 'Small repair', 'Sundries']), r.randint(20, 90), 'Various')
        add(_eom(m), 'Card and bank fees', 'Card and payment-link fees', 0.018 * card.get(m, 0.0), 'Payment provider')
    for c in cls: add(c['date'], 'Class venue', 'Hall hire, ' + c['class'], c['venue_cost'], 'Kofi Mensah')
    for x in mk: add(x['month'] + day(9), 'Marketing', x['kind'], x['cost'], 'Marketing suppliers' if x['kind'] != 'Referral thank-yous' else 'Thank-you gifts')
    for x in tr:
        if x['cost'] and x['date'] <= TODAY: add(x['date'], 'Training and renewals', x['title'], x['cost'], 'Training provider')
    for x in rn:
        if x['renewed_on'] != '' and x['renewed_on'] >= HISTORY_START: add(x['renewed_on'], 'Training and renewals' if x['item'] not in ('Liability insurance',) else 'Insurance', x['item'], x['cost'] if x['item'] != 'Liability insurance' else 0.0, 'Renewal fee')
    ex = [e for e in ex if e['amount'] > 0 and e['date'] >= HISTORY_START]
    ex.sort(key=lambda e: (e['date'], e['category']))
    out['expenses'] = [dict(expense_id='EX-%05d' % (i + 1), **e) for i, e in enumerate(ex)]
    # ---- profit and loss, tax, cash
    months = months24(); ix = {m: i for i, m in enumerate(months)}
    z = lambda: [0.0] * len(months)
    birth_inc, pp_inc, add_inc, cls_inc, adj, doula_pay, backup_pay, mil, other, births_n, vis_h, kept = z(), z(), z(), z(), z(), z(), z(), z(), z(), z(), z(), z()
    for s in specs:
        if s['cancel']: continue
        pk = PK[s['package']]; f = s['price'] / pk['price']
        if s['kind'] != 'Postpartum' and s['birth'] <= TODAY and _ms(s['birth']) in ix:
            birth_inc[ix[_ms(s['birth'])]] += pk['birth_value'] * f; births_n[ix[_ms(s['birth'])]] += 1
        if pk['postpartum_hours']:
            rate = pk['pp_value'] * f / pk['postpartum_hours']; used = 0.0
            for vd, kd, h in s['_visits_all']:
                if kd in ('Postpartum visit', 'Night shift') and vd <= TODAY:
                    used += h
                    if _ms(vd) in ix: pp_inc[ix[_ms(vd)]] += h * rate
            exp = s['edd'] + day(PACK_EXPIRY_DAYS)
            if exp <= TODAY and _ms(exp) in ix and used < pk['postpartum_hours']: pp_inc[ix[_ms(exp)]] += (pk['postpartum_hours'] - used) * rate
    for a in W['addons']:
        if _ms(a['date']) in ix: add_inc[ix[_ms(a['date'])]] += a['price']
    for p in py:
        if p['kind'] == 'Hours invoice' and p['month'] in ix: add_inc[ix[p['month']]] += p['amount']
    for c in cls:
        if c['month'] in ix: cls_inc[ix[c['month']]] += c['income']
    for c in W['cancels']:
        if _ms(c['date']) in ix:
            if c['kind'] == 'Cancelled': kept[ix[_ms(c['date'])]] += c['kept']
            else: adj[ix[_ms(c['date'])]] -= c['refunded']
    for x in lines:
        if x['month'] not in ix: continue
        i = ix[x['month']]
        if x['basis'] in ('Per client', 'Per hour'): doula_pay[i] += x['pay_due']
        elif x['basis'] in ('Backup stipend', 'Backup call-out'): backup_pay[i] += x['pay_due']
        else: mil[i] += x['pay_due']
    for e in ex:
        if e['month'] in ix: other[ix[e['month']]] += e['amount']
    for v in W['visits']:
        if _ms(v['date']) in ix: vis_h[ix[_ms(v['date'])]] += v['hours']
    admin = ADMIN_HOURS_WEEK * ADMIN_RATE * 52 / 12.0
    pnl = []
    for i, m in enumerate(months):
        rev = birth_inc[i] + pp_inc[i] + add_inc[i] + cls_inc[i] + kept[i] + adj[i]
        prof = rev - doula_pay[i] - backup_pay[i] - mil[i] - admin - other[i]
        pnl.append(dict(pnl_id='PL-%02d' % (i + 1), month=m, revenue=R2(rev), birth_income=R2(birth_inc[i]), postpartum_income=R2(pp_inc[i]), addon_income=R2(add_inc[i]), class_income=R2(cls_inc[i]),
                        other_income=R2(kept[i] + adj[i]), doula_pay=R2(doula_pay[i]), backup_pay=R2(backup_pay[i]), mileage=R2(mil[i]), admin_pay=R2(admin), other_costs=R2(other[i]), profit=R2(prof),
                        births=int(births_n[i]), visit_hours=R2(vis_h[i])))
    out['pnl'] = pnl
    tx = []
    for i, p in enumerate(pnl):
        mv = add_months(p['month'], 1).replace(day=5)
        sa = R2(max(0.0, p['profit']) * TAX_SET_ASIDE_PCT)
        tx.append(dict(tax_id='TX-%02d' % (i + 1), month=p['month'], profit=p['profit'], set_aside_pct=TAX_SET_ASIDE_PCT, set_aside=sa, moved_on=mv if mv <= TODAY else '',
                       status='Moved' if mv <= TODAY else 'Planned'))
    out['tax'] = tx
    cin = z(); pout = z(); eout = z(); rout = z()
    for p in py:
        if p['month'] in ix: cin[ix[p['month']]] += p['amount']
    for c in cls:
        if c['month'] in ix: cin[ix[c['month']]] += c['income']
    for x in lines:
        if x['paid_on'] != '' and _ms(x['paid_on']) in ix: pout[ix[_ms(x['paid_on'])]] += x['paid_amount']
    for i in range(len(months)): pout[i] += admin
    for e in ex:
        if e['month'] in ix: eout[ix[e['month']]] += e['amount']
    for c in W['cancels']:
        if _ms(c['date']) in ix: rout[ix[_ms(c['date'])]] += c['refunded']
    sa_m = z()
    for i in range(1, len(months)): sa_m[i] = tx[i - 1]['set_aside']
    cash = []; bal = 0.0; raw = []
    for i, m in enumerate(months):
        net = cin[i] - pout[i] - eout[i] - rout[i] - sa_m[i] - OWNER_DRAW
        raw.append(net)
    run = 0.0; mn = 1e9
    for net in raw: run += net; mn = min(mn, run)
    opening = max(0.0, 22000.0 - mn) if mn < 22000 else 0.0
    bal = round(opening, -2)
    for i, m in enumerate(months):
        o = bal; c_ = o + raw[i]
        cash.append(dict(cash_id='CF-%02d' % (i + 1), month=m, opening=R2(o), cash_in=R2(cin[i]), pay_out=R2(pout[i]), expenses_out=R2(eout[i]), refunds=R2(rout[i]), set_aside=R2(sa_m[i]), owner_draw=OWNER_DRAW,
                         closing=R2(c_)))
        bal = c_
    out['cash'] = cash
    W['out'] = out; W['SP'] = SP; W['lines'] = lines
    return W


# ------------------------------------------------------------------ public generators
def _F(): return _raw('final', _final)
def _out(name, n=None): return _thin([dict(x) for x in _F()['out'][name]], n)


def client_rows(n=None): return _out('clients', n)
def contract_rows(n=None): return _out('contracts', n)
def plan_rows(n=None): return _out('plans', n)
def payment_rows(n=None): return _out('payments', n)
def addon_rows(n=None): return _out('addons', n)
def oncall_rows(n=None): return _out('oncall', n)
def rota_rows(n=None): return _out('rota', n)
def birth_rows(n=None): return _out('births', n)
def visit_rows(n=None): return _out('visits', n)
def pack_rows(n=None): return _out('packs', n)
def pay_rows(n=None): return _out('pay', n)
def enquiry_rows(n=None): return _out('enquiries', n)
def consult_rows(n=None): return _out('consults', n)
def class_session_rows(n=None): return _out('class_sessions', n)
def class_attendee_rows(n=None): return _out('class_attendees', n)
def referral_rows(n=None): return _out('referrals', n)
def review_rows(n=None): return _out('reviews', n)
def cancel_rows(n=None): return _out('cancels', n)
def marketing_rows(n=None): return _out('marketing', n)
def expense_rows(n=None): return _out('expenses', n)
def renewal_rows(n=None): return _out('renewals', n)
def training_rows(n=None): return _out('training', n)
def timeoff_rows(n=None): return _out('timeoff', n)
def pnl_rows(n=None): return _out('pnl', n)
def cash_rows(n=None): return _out('cash', n)
def tax_rows(n=None): return _out('tax', n)



def owner_time_rows(n=None):
    """owner time log, one row per week for ~2 years: own-client hours (visits and births of the owner-doula), management hours and admin hours (office tasks the owner does)"""
    def build():
        r = rng('ownertime' + _SIM_TAG); W = _F(); rows = []
        w = week_start(month_start(23))
        own = {}
        for v in W['out']['visits']:
            if v['doula'] == OWNER: own[week_start(v['date'])] = own.get(week_start(v['date']), 0.0) + v['hours']
        for b in W['out']['births']:
            if b['doula'] == OWNER: own[week_start(b['date'])] = own.get(week_start(b['date']), 0.0) + b['hours']
        while w <= week_start(TODAY):
            rows.append(dict(log_id='OT-%03d' % (len(rows) + 1), week=w, own_client_hours=q(own.get(w, 0.0)), management_hours=q(r.uniform(5, 11)), admin_hours=q(r.uniform(3, 9))))
            w += day(7)
        return rows
    return _thin([dict(x) for x in _raw('ownertime', build)], n)


def coverage(doula, d):
    """number of on-call windows of one doula that cover the date d"""
    d = to_date(d)
    return sum(1 for w in oncall_rows() if w['doula'] == doula and to_date(w['oncall_start']) <= d <= to_date(w['oncall_end']))


def client_summary(client_id):
    """hours by phase, mileage cost, price and earned-to-date for one client (used by the story and the tests)"""
    W = _F(); s = W['SP'][client_id]; pk = PK[s['package']]
    pre = sum(v['hours'] for v in W['out']['visits'] if v['client_id'] == client_id and v['kind'] == 'Prenatal visit')
    pp = sum(v['hours'] for v in W['out']['visits'] if v['client_id'] == client_id and v['kind'] != 'Prenatal visit')
    birth = sum(b['hours'] for b in W['out']['births'] if b['client_id'] == client_id)
    oc = [w for w in W['out']['oncall'] if w['client_id'] == client_id]
    contact = (oc[0]['contact_hours'] if oc and oc[0]['contact_hours'] != '' else 0.0)
    mil = sum(v['mileage_cost'] for v in W['out']['visits'] if v['client_id'] == client_id) + sum(b['miles'] * AREA[b['area']]['mileage_rate'] for b in W['out']['births'] if b['client_id'] == client_id)
    paid = sum(p['amount'] for p in W['out']['payments'] if p['client_id'] == client_id)
    return dict(prenatal=pre, postpartum=pp, birth=birth, oncall=contact, hours=pre + pp + birth + contact, mileage=R2(mil), price=s['price'], paid=R2(paid), package=s['package'], doula=s['doula'])


def agency_margin():
    """per doula: agency revenue from their clients, doula pay, mileage, overhead and the margin after costs (history to date)"""
    W = _F(); res = {}
    for n in CONTRACTED:
        lines = [x for x in W['lines'] if x['doula'] == n and x['basis'] in ('Per client', 'Per hour')]
        cids = {x['client_id'] for x in lines}
        rev = sum(x['gross'] for x in lines); pay = sum(x['pay_due'] for x in lines)
        pay += sum(x['pay_due'] for x in W['lines'] if x['basis'] == 'Backup call-out' and x['client_id'] in cids and W['SP'][x['client_id']]['doula'] == n)
        mil = 0.0
        for c in cids: mil += client_summary(c)['mileage']
        ov = AGENCY_COST_CLIENT * len(cids)
        res[n] = dict(clients=len(cids), revenue=R2(rev), pay=R2(pay), mileage=R2(mil), overhead=R2(ov), margin=R2(rev - pay - mil - ov))
    return res


def story():
    """ids of the story rows (never hard-code): overlap_doula overlap_month overlap_clients overlap_count overlap_limit overlap_backups; low_package low_pph low_target low_clients;
    plan_client plan_client_id plan_balance plan_due plan_days plan_instalment; prepaid_client prepaid_client_id prepaid_package prepaid_paid prepaid_hours prepaid_used prepaid_unearned
    prepaid_expires; split_doula split_share split_births split_margin split_revenue; renewal_id renewal_holder renewal_item renewal_date renewal_days"""
    W = _F(); SP = W['SP']; out = {}
    ov = [s for s in W['specs'] if s['tag'] == 'overlap']
    M = month_start(-3)
    cov = max(coverage('Mei-Ling Chen', M + day(i)) for i in range(28))
    out.update(overlap_doula='Mei-Ling Chen', overlap_month=iso(M), overlap_clients=[s['client_id'] for s in ov], overlap_count=cov, overlap_limit=MAX_OVERLAP, overlap_backups=sum(1 for s in ov if s['backup']))
    bs = [s for s in W['specs'] if s['package'] == 'Complete Care Bundle' and not s['cancel']]
    inc = hrs = 0.0
    for s in bs:
        if s['status'] != 'Completed': continue
        cs = client_summary(s['client_id'])
        inc += cs['price'] - cs['mileage']; hrs += cs['hours']
    out.update(low_package='Complete Care Bundle', low_pph=R2(inc / hrs), low_target=TARGET_INCOME_HOUR, low_clients=[s['client_id'] for s in bs])
    ps = [s for s in W['specs'] if s['tag'] == 'plan'][0]
    pls = [p for p in W['out']['plans'] if p['client_id'] == ps['client_id']]
    un = [p for p in pls if p['status'] == 'Unpaid']
    out.update(plan_client=ps['client'], plan_client_id=ps['client_id'], plan_balance=R2(sum(p['amount'] for p in un)), plan_due=iso(un[0]['due_date']), plan_days=(un[0]['due_date'] - TODAY).days,
               plan_instalment=un[0]['amount'])
    pp = [s for s in W['specs'] if s['tag'] == 'prepaid'][0]
    pk = PK[pp['package']]; cs = client_summary(pp['client_id'])
    out.update(prepaid_client=pp['client'], prepaid_client_id=pp['client_id'], prepaid_package=pp['package'], prepaid_paid=cs['paid'], prepaid_hours=pk['postpartum_hours'], prepaid_used=cs['postpartum'],
               prepaid_unearned=R2(cs['paid'] * (1 - cs['postpartum'] / pk['postpartum_hours'])), prepaid_expires=iso(pp['edd'] + day(PACK_EXPIRY_DAYS)))
    am = agency_margin()['Priya Raman']
    out.update(split_doula='Priya Raman', split_share=DT['Priya Raman']['agency_share'], split_births=am['clients'], split_margin=am['margin'], split_revenue=am['revenue'])
    rn = [x for x in W['out']['renewals'] if x['holder'] == OWNER and x['item'] == 'Liability insurance' and x['renewed_on'] == ''][0]
    out.update(renewal_id=rn['renewal_id'], renewal_holder=rn['holder'], renewal_item=rn['item'], renewal_date=iso(rn['due_date']), renewal_days=(rn['due_date'] - TODAY).days)
    return out


_GENS = ['client_rows', 'contract_rows', 'plan_rows', 'payment_rows', 'addon_rows', 'oncall_rows', 'rota_rows', 'birth_rows', 'visit_rows', 'pack_rows', 'pay_rows', 'enquiry_rows', 'consult_rows',
         'class_session_rows', 'class_attendee_rows', 'referral_rows', 'review_rows', 'cancel_rows', 'marketing_rows', 'expense_rows', 'renewal_rows', 'training_rows', 'timeoff_rows', 'pnl_rows',
         'cash_rows', 'tax_rows', 'owner_time_rows']


def _digest():
    h = hashlib.md5()
    for nm in _GENS: h.update(repr(globals()[nm]()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); S = story(); G = {nm: globals()[nm]() for nm in _GENS}
    print('team', len(team), 'doulas', len(doulas), 'areas', len(areas), 'packages', len(packages), 'pp_rates', len(pp_rates), 'sources', len(sources_ref), 'class_types', len(class_types))
    print(' '.join('%s %d' % (nm.replace('_rows', ''), len(v)) for nm, v in G.items()))
    ids = {'client_rows': 'client_id', 'contract_rows': 'contract_id', 'plan_rows': 'inst_id', 'payment_rows': 'payment_id', 'addon_rows': 'addon_id', 'oncall_rows': 'window_id',
           'rota_rows': 'rota_id', 'birth_rows': 'birth_id', 'visit_rows': 'visit_id', 'pack_rows': 'pack_id', 'pay_rows': 'pay_id', 'enquiry_rows': 'enquiry_id', 'consult_rows': 'consult_id',
           'class_session_rows': 'session_id', 'class_attendee_rows': 'attendee_id', 'referral_rows': 'referral_id', 'review_rows': 'review_id', 'cancel_rows': 'cancel_id',
           'marketing_rows': 'campaign_id', 'expense_rows': 'expense_id', 'renewal_rows': 'renewal_id', 'training_rows': 'training_id', 'timeoff_rows': 'timeoff_id', 'pnl_rows': 'pnl_id',
           'cash_rows': 'cash_id', 'tax_rows': 'tax_id', 'owner_time_rows': 'log_id'}
    for nm, k in ids.items(): assert len({x[k] for x in G[nm]}) == len(G[nm]), nm
    assert len({c['client'] for c in G['client_rows']}) == len(G['client_rows']), 'client names unique'
    chk = [('client_rows', 'kind', CLIENT_KINDS), ('client_rows', 'status', CLIENT_STATUS), ('client_rows', 'area', AREAS), ('client_rows', 'source', SOURCES), ('client_rows', 'discount', DISCOUNTS),
           ('client_rows', 'doula', DOULA_NAMES), ('client_rows', 'backup', BACKUP_NAMES), ('contract_rows', 'plan', PLAN_TYPES), ('contract_rows', 'status', CONTRACT_STATUS),
           ('plan_rows', 'status', INST_STATUS), ('payment_rows', 'kind', PAYMENT_KINDS), ('payment_rows', 'method', PAY_METHODS), ('visit_rows', 'kind', VISIT_KINDS),
           ('visit_rows', 'doula', DOULA_NAMES), ('pay_rows', 'basis', PAY_BASIS), ('pay_rows', 'status', PAY_STATUS), ('enquiry_rows', 'status', ENQUIRY_STATUS),
           ('enquiry_rows', 'reason', LOST_REASONS), ('enquiry_rows', 'source', SOURCES), ('consult_rows', 'outcome', CONSULT_OUTCOMES), ('class_session_rows', 'class', CLASS_TYPES),
           ('cancel_rows', 'kind', CANCEL_KINDS), ('cancel_rows', 'reason', CANCEL_REASONS), ('marketing_rows', 'kind', MARKETING_KINDS), ('expense_rows', 'category', EXPENSE_CATEGORIES),
           ('renewal_rows', 'item', RENEWAL_KINDS), ('training_rows', 'kind', CPD_KINDS), ('timeoff_rows', 'kind', TIMEOFF_KINDS), ('review_rows', 'channel', CHANNELS + ['']),
           ('referral_rows', 'source', SOURCES)]
    for nm, col, vals in chk:
        got = {x[col] for x in G[nm]}; miss = [v for v in vals if v not in got]; extra = [v for v in got if v not in vals]
        if miss or extra: print('LIST CHECK', nm, col, 'unused', miss, 'not in list', extra)
    cur = _ms(TODAY); l30 = TODAY - day(30)
    for nm, col in [('birth_rows', 'date'), ('visit_rows', 'date'), ('payment_rows', 'date'), ('enquiry_rows', 'date'), ('consult_rows', 'date'), ('class_session_rows', 'date'),
                    ('expense_rows', 'date'), ('referral_rows', 'date'), ('addon_rows', 'date'), ('review_rows', 'received_on'), ('pay_rows', 'month'), ('client_rows', 'signed_on')]:
        v = [x[col] for x in G[nm] if x[col] != '']
        print('%-20s this month %3d  last 30 days %3d  oldest %s newest %s' % (nm, sum(1 for d in v if d >= cur and d <= TODAY or (col == 'month' and d == cur)), sum(1 for d in v if l30 <= d <= TODAY), min(v), max(v)))
    print('story', S)
    print('digest', _digest(), 'seconds %.1f' % (time.time() - t0))
