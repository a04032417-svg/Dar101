"""Home care agency suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (one cached world is built on first use). The demo business is "Maple & Ash Home Care" (fictional),
a small NON-MEDICAL home care agency run by an owner-director (Marguerite Adeyemi, HC-01) with a scheduler and care coordinator (HC-02), an office manager who does billing and payroll
(HC-03), a part-time recruiter (HC-04), 2 field supervisors (HC-05, HC-06) and 10 outside contacts (accountant, payroll service, insurance broker, background-check provider, training
provider, supplies vendor, marketing helper, landlord, IT support, answering service; HC-07..HC-16). About 38 caregivers now (CG-001..CG-050 over two years including 12 leavers;
22 hourly, 12 part-time, 4 live-in) and 54 active clients (CL-001..CL-084 including 30 ended; about 75% private pay, the rest a care insurer or a third-party payer) in 6 areas
(North Hills, Riverside, Old Town, East Park, Lakeside, South Valley) with travel minutes between them. Services: companion care, personal care help, homemaking, respite care,
overnight care and live-in days; weekday, evening, weekend, night and holiday bands. About 900 care hours a week now (half of that two years ago), about 21,000 scheduled visits over
~2 years (oldest first, schedule posted 14 days ahead), ~890 call-offs, ~2,150 invoices, ~250 payer claims. One generic currency; every date is relative to the build day.
A one-person start-up agency uses the same tables with fewer rows. STRICTLY NON-MEDICAL: care needs are service types and hours only.

Money model: a visit has a bill rate = service base rate x band multiplier (weekday 1.0, evening 1.06, weekend 1.12, night 1.18, holiday 1.5) x the client's rate factor (private pay about 1.0,
care insurer 0.92, third-party payers 0.90 / 0.88; rates were about 4% lower before 1 January of this year, except a client whose rate was never raised). Billed hours = the longer of the
client's minimum visit and the actual hours (quarter-hour steps); overnight and live-in days bill their fixed shift. Caregiver pay = pay rate x band pay multiplier (holiday 1.5) x actual
hours; paid travel time (between two visits of the same day, at the pay rate) and mileage (MILEAGE_RATE per km); overtime premium (OVERTIME_MULT - 1) x pay rate on hours above OVERTIME_HOURS a
week, spread over the week's visits; cover premium (COVER_PREMIUM an hour) for cover found at short notice; payroll burden PAYROLL_BURDEN on pay (not on mileage) = loaded cost.
margin = charge - cost. Invoices: weekly, bi-weekly or monthly by client, issued on the Monday or the 1st after the period, due INVOICE_DAYS later; private pay clients pay in 3 to 55 days,
care insurer and third-party payer clients are billed by monthly claims (status and amounts only) paid in about 38 to 52 days; 8 private clients pay from a prepaid balance; other new private
clients pay a deposit of DEPOSIT_WEEKS weeks of hours. Pay runs are bi-weekly (paid 8 days after the period ends). Office payroll and supervisors are overhead rows in the expenses.

Story rows (ids from story(), never hard-coded): below_cost_client (billed below cost per hour once travel and overtime are counted), overdue_invoice (a private pay client with 3
unpaid monthly invoices, the oldest 6+ weeks past due; no other private pay invoice is more than 42 days past due and unpaid), overtime_caregiver (scheduled above the overtime line in the
coming week), credential_caregiver (a first aid course ends in 10 days; the caregiver is still on the schedule; the only credential due within 45 days), continuity_client (the highest
number of different caregivers in the last 30 days, 5+; every other client has at most 6), problem_area (South Valley: repeated late and missed visits in the last 75 days).

Exports
  constants: COMPANY SUITE OWNER SCHEDULER OFFICE_MANAGER RECRUITER TARGET_MARGIN PAYROLL_BURDEN OVERTIME_HOURS OVERTIME_MULT HOLIDAY_PAY_MULT HOLIDAY_BILL_MULT MILEAGE_RATE LATE_MINUTES
             MIN_VISIT_HOURS PAYROLL_RATIO_CEILING SCHEDULER_THRESHOLD_HOURS TURNOVER_FLAG CONTINUITY_LIMIT INVOICE_DAYS DEPOSIT_WEEKS TAX_SET_ASIDE_PCT OWNER_DRAW CASH_FLOOR COVER_PREMIUM
             RENEWAL_WARN_DAYS POST_SCHEDULE_DAYS HIRE_AD_COST BACKGROUND_CHECK_COST ONBOARD_HOURS HISTORY_START HISTORY_DAYS
  dates: TODAY iso ago ahead to_date month_start add_months months14() week_start; helpers pairs first_name fake_phone fake_email rng R2
  lists: ROLES TEAMS PAY_TYPES SERVICES BANDS AREAS ZONES PAYERS BILL_CYCLES EMPLOYMENT CAREGIVER_STATUS CLIENT_STATUS AVAILABILITY LANGUAGES VISIT_STATUS COVER_KINDS WEEKDAYS DELAY_REASONS
         MISS_REASONS CALLOFF_REASONS END_REASONS ENQUIRY_STATUS ENQ_SOURCES LOSS_REASONS CRED_TYPES CRED_STATUS REC_SOURCES APPLICANT_STATUS APPLICANT_REASONS LEAVE_REASONS TIMEOFF_KINDS
         INVOICE_STATUS PAYMENT_METHODS PAID_BY PAYMENT_KINDS CLAIM_STATUS CLAIM_REASONS DEPOSIT_KINDS DEPOSIT_STATUS PAY_STATUS TAX_STATUS EXPENSE_CATEGORIES MARKETING_KINDS AGREEMENT_KINDS
         AGREEMENT_STATUS
  maps: BASE_BILL BASE_PAY BILL_MULT PAY_MULT MIN_VISIT TRAVEL (area pairs -> minutes) FIELD_SUPERVISORS; functions travel_minutes(a, b) travel_km(a, b)
  reference (lists of dicts): team (16: HC-01..HC-16) areas (6) services (6) rate_card (30: service x band) payers (4) credential_types (6) shift_types (12) holidays (about 26)
  generators (fresh lists of dicts, oldest first; n= thins a long list but keeps the most recent rows; optional dates are '' when blank):
    caregiver_rows client_rows availability_rows time_off_rows visit_rows calloff_rows hours_rows (caregiver x week) week_rows (agency x week) mileage_rows payroll_rows enquiry_rows
    agreement_rows invoice_rows payment_rows deposit_rows claim_rows applicant_rows onboarding_rows credential_rows expense_rows pnl_rows tax_rows cash_rows marketing_rows client_month_rows
    service_month_rows area_month_rows growth_rows holiday_rows
  helpers: client_margin(client_id, days=90) caregiver_week_hours(week_iso) match_score(caregiver_id, client_id) story()
Lesson: money cells are plain amounts; optional dates (left_date, end_date, paid_on, resubmitted_on, first_shift_on, ...) are '' when blank: wrap lookups with IF(x=0,"",x). Links hold NAMES
(client, caregiver, area, service, payer) or ids (client CL-001, caregiver CG-001, visit VS-00001, invoice IV-0001, claim CP-0001).
Words: no diagnosis, no medication, no clinical note, no care advice: care needs are service types and hours only.
"""
import datetime as dt
import calendar
import random
import hashlib
import math
from collections import defaultdict

COMPANY = 'Maple & Ash Home Care'
SUITE = 'fx-20261115-home-care-agency'
OWNER = 'Marguerite Adeyemi'
SCHEDULER = 'Tomasz Kowalski'
OFFICE_MANAGER = 'Priyanka Nair'
RECRUITER = 'Camille Dubois'
TODAY = dt.date.today()
D = dt.date

TARGET_MARGIN = 0.35         # wanted gross margin per client hour
PAYROLL_BURDEN = 0.20        # payroll taxes, workers' insurance and benefits on top of pay (confirm with your adviser)
OVERTIME_HOURS = 40          # weekly hours after which overtime is paid
OVERTIME_MULT = 1.5
HOLIDAY_PAY_MULT = 1.5
HOLIDAY_BILL_MULT = 1.5
MILEAGE_RATE = 0.40          # per km
LATE_MINUTES = 15            # a check-in later than this is a late visit
MIN_VISIT_HOURS = 2
PAYROLL_RATIO_CEILING = 0.65 # pay cost as a share of revenue
SCHEDULER_THRESHOLD_HOURS = 1000
TURNOVER_FLAG = 0.30
CONTINUITY_LIMIT = 3         # different caregivers per client in 4 weeks
INVOICE_DAYS = 14
DEPOSIT_WEEKS = 1
TAX_SET_ASIDE_PCT = 0.25     # confirm with your adviser
OWNER_DRAW = 7500.0
CASH_FLOOR = 30000.0
COVER_PREMIUM = 3.0          # extra per hour paid for cover found at short notice
RENEWAL_WARN_DAYS = 60
POST_SCHEDULE_DAYS = 14      # schedule is posted this many days ahead
HIRE_AD_COST = 180.0
BACKGROUND_CHECK_COST = 45.0
ONBOARD_HOURS = 16


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
def rng(tag=''): return random.Random('hc-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
def _hhmm(m): m = int(round(m)); return '%02d:%02d' % ((m // 60) % 24, m % 60)


HISTORY_START = month_start(23)
HISTORY_DAYS = (TODAY - HISTORY_START).days

# ------------------------------------------------------------------ lists (keys from pairs() stay <= 21 characters)
ROLES = ['Owner-director', 'Care coordinator', 'Office manager', 'Recruiter', 'Field supervisor', 'Accountant', 'Payroll service', 'Insurance broker',
         'Background checks', 'Training provider', 'Supplies vendor', 'Marketing helper', 'Landlord', 'IT support', 'Answering service']
TEAMS = ['Management', 'Office', 'Field', 'Outside']
PAY_TYPES = ['Owner draw', 'Salary', 'Hourly', 'Invoice']
SERVICES = ['Companion care', 'Personal care help', 'Homemaking', 'Respite care', 'Overnight care', 'Live-in day']
BANDS = ['Weekday', 'Evening', 'Weekend', 'Night', 'Holiday']
AREAS = ['North Hills', 'Riverside', 'Old Town', 'East Park', 'Lakeside', 'South Valley']
ZONES = ['Zone 1', 'Zone 2', 'Zone 3']
PAYERS = ['Private pay', 'Care insurer', 'Third-party payer A', 'Third-party payer B']
BILL_CYCLES = ['Weekly', 'Bi-weekly', 'Monthly']
EMPLOYMENT = ['Hourly', 'Part-time', 'Live-in']
CAREGIVER_STATUS = ['Active', 'On leave', 'Left']
CLIENT_STATUS = ['Active', 'Ended']
AVAILABILITY = ['Any time', 'Weekdays', 'Weekdays and evenings', 'Weekends and evenings', 'Nights and weekends']
LANGUAGES = ['English', 'Spanish', 'Polish', 'Portuguese', 'Hindi', 'Arabic', 'French', 'Tagalog', 'Twi', 'Mandarin', 'Russian', 'Italian', 'Vietnamese']
VISIT_STATUS = ['Scheduled', 'Completed', 'Late', 'Missed', 'Cancelled', 'Open', 'No check-in']
COVER_KINDS = ['Planned', 'Cover', 'Uncovered']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DELAY_REASONS = ['Traffic', 'Public transport', 'Earlier visit overran', 'Car trouble', 'Wrong time given', 'Weather', 'No reason given']
MISS_REASONS = ['No cover found', 'Caregiver no-show', 'Client not home', 'Schedule error']
CALLOFF_REASONS = ['Illness', 'Family matter', 'Car trouble', 'Another job', 'Personal reason', 'No reason given']
END_REASONS = ['Needs changed', 'Moved away', 'Family took over', 'Price', 'Service issues', 'Funding ended', 'Went elsewhere', 'No longer needed']
ENQUIRY_STATUS = ['New', 'Assessment booked', 'Agreement sent', 'Started', 'Lost']
ENQ_SOURCES = ['Family or friend', 'Discharge planner', 'Online directory', 'Agency website', 'Community event', 'Past client', 'Local clinic']
LOSS_REASONS = ['Price', 'No cover available', 'Timing', 'Went elsewhere', 'No reply', 'Needs changed']
CRED_TYPES = ['Background re-check', 'Core skills refresher', 'First aid course', 'Driving licence check', 'Vehicle cover check', 'Eligibility document']
CRED_STATUS = ['Valid', 'Renewed', 'Lapsed']
REC_SOURCES = ['Online job board', 'Caregiver referral', 'Agency website', 'Community notice', 'Training school', 'Social media post', 'Walk-in']
APPLICANT_STATUS = ['Applied', 'Phone screen', 'Interview', 'Offer', 'Onboarding', 'Started', 'Withdrawn', 'Not selected']
LEAVE_REASONS = ['Better pay elsewhere', 'Not enough hours', 'Moved away', 'Schedule clash', 'Changed career', 'Ended by agency']
TIMEOFF_KINDS = ['Holiday', 'Sick day', 'Training day']
INVOICE_STATUS = ['Paid', 'Part paid', 'Unpaid', 'Written off']
PAYMENT_METHODS = ['Card', 'Bank transfer', 'Cheque']
PAID_BY = PAYMENT_METHODS + ['Prepaid balance', 'Payer payment']
PAYMENT_KINDS = ['Invoice payment', 'Payer payment', 'Deposit', 'Prepayment']
CLAIM_STATUS = ['Submitted', 'Accepted', 'Paid', 'Short-paid', 'Rejected', 'Resubmitted', 'Written off']
CLAIM_REASONS = ['Hours mismatch', 'Missing details', 'Authorisation missing', 'Late submission', 'Rate difference']
DEPOSIT_KINDS = ['Deposit', 'Prepayment']
DEPOSIT_STATUS = ['Held', 'Applied', 'Refunded']
PAY_STATUS = ['Paid', 'Due', 'Accruing']
TAX_STATUS = ['Moved', 'Due', 'Upcoming']
EXPENSE_CATEGORIES = ['Office rent', 'Office payroll', 'Field supervisor pay', 'Software and phones', 'Business insurance', 'Marketing', 'Recruiting ads', 'Background checks',
                      'Training courses', 'Office supplies', 'Accounting fees', 'Bank and card fees', 'Professional fees', 'Uniforms and supplies']
MARKETING_KINDS = ['Online job ad', 'Community flyers', 'Directory listing', 'Website', 'Partner visit', 'Referral bonus', 'Local event']
AGREEMENT_KINDS = ['Original', 'Rate update', 'Hours change']
AGREEMENT_STATUS = ['Signed', 'Sent', 'Ended']

# ------------------------------------------------------------------ people
_staff = [('HC-01', 'Marguerite Adeyemi', 'Nigeria', 'Owner-director', 'Management', 'Owner draw', 45, 0, 0, 'Runs the agency, assessments and key clients', 2400),
          ('HC-02', 'Tomasz Kowalski', 'Poland', 'Care coordinator', 'Office', 'Salary', 40, 4300, 0, 'Weekly schedule, cover and call-offs', 1500),
          ('HC-03', 'Priyanka Nair', 'India', 'Office manager', 'Office', 'Salary', 40, 4800, 0, 'Invoicing, payroll preparation and collections', 1300),
          ('HC-04', 'Camille Dubois', 'France', 'Recruiter', 'Office', 'Hourly', 20, 0, 26, 'Part-time recruiting and onboarding', 420),
          ('HC-05', 'Joaquin Ramirez', 'Mexico', 'Field supervisor', 'Field', 'Salary', 40, 3900, 0, 'Assessments, spot checks and caregiver support', 900),
          ('HC-06', 'Amara Diallo', 'Senegal', 'Field supervisor', 'Field', 'Salary', 40, 3800, 0, 'Assessments, spot checks and caregiver support', 270)]
_ctc = [('HC-07', 'Henrik Larsen', 'Denmark', 'Accountant', 'Bookkeeping, yearly accounts and tax planning'),
        ('HC-08', 'Fatuma Hassan', 'Kenya', 'Payroll service', 'Pay run processing and payroll reports'),
        ('HC-09', 'Rosa Bianchi', 'Italy', 'Insurance broker', 'Business insurance and workers insurance renewals'),
        ('HC-10', 'Dmitri Volkov', 'Russia', 'Background checks', 'Identity and background re-checks'),
        ('HC-11', 'Leila Haddad', 'Lebanon', 'Training provider', 'Core skills and first aid courses'),
        ('HC-12', 'Kwame Boateng', 'Ghana', 'Supplies vendor', 'Uniforms, gloves and office supplies'),
        ('HC-13', 'Yuki Tanaka', 'Japan', 'Marketing helper', 'Flyers, website and directory listing'),
        ('HC-14', 'Olumide Bakare', 'Nigeria', 'Landlord', 'Office lease and building repairs'),
        ('HC-15', 'Nadia Petrova', 'Bulgaria', 'IT support', 'Computers, phones and back-ups'),
        ('HC-16', 'Sven Eriksson', 'Sweden', 'Answering service', 'After-hours call answering')]
team = []
for i, (a, b, c, ro, te, pt, hw, sal, hr, spec, st) in enumerate(_staff):
    team.append(dict(staff_id=a, name=b, role=ro, team=te, pay_type=pt, phone=fake_phone(101 + i), email=fake_email(b), hours_week=hw, monthly_salary=float(sal),
                     hourly_rate=float(hr), speciality=spec, country=c, start=ago(st)))
for i, (a, b, c, ro, spec) in enumerate(_ctc):
    team.append(dict(staff_id=a, name=b, role=ro, team='Outside', pay_type='Invoice', phone=fake_phone(120 + i), email=fake_email(b), hours_week=0, monthly_salary=0.0,
                     hourly_rate=0.0, speciality=spec, country=c, start=ago(300 + i * 150)))
FIELD_SUPERVISORS = ['Joaquin Ramirez', 'Amara Diallo']

# ------------------------------------------------------------------ areas, travel, rates, holidays (reference)
_TRV = {('North Hills', 'Riverside'): 18, ('North Hills', 'Old Town'): 22, ('North Hills', 'East Park'): 28, ('North Hills', 'Lakeside'): 35, ('North Hills', 'South Valley'): 45,
        ('Riverside', 'Old Town'): 12, ('Riverside', 'East Park'): 20, ('Riverside', 'Lakeside'): 25, ('Riverside', 'South Valley'): 38,
        ('Old Town', 'East Park'): 15, ('Old Town', 'Lakeside'): 22, ('Old Town', 'South Valley'): 30,
        ('East Park', 'Lakeside'): 18, ('East Park', 'South Valley'): 32, ('Lakeside', 'South Valley'): 28}
TRAVEL = {}
for (a, b), m in _TRV.items(): TRAVEL[(a, b)] = m; TRAVEL[(b, a)] = m
for a in AREAS: TRAVEL[(a, a)] = 10
def travel_minutes(a, b): return TRAVEL[(a, b)]
def travel_km(a, b): return round(TRAVEL[(a, b)] * 0.55, 1)
_ZONE = {'Riverside': 'Zone 1', 'Old Town': 'Zone 1', 'East Park': 'Zone 2', 'North Hills': 'Zone 2', 'Lakeside': 'Zone 3', 'South Valley': 'Zone 3'}
areas = [dict(area_id='AR-%02d' % (i + 1), area=a, zone=_ZONE[a], avg_travel_min=round(sum(TRAVEL[(a, b)] for b in AREAS if b != a) / 5.0)) for i, a in enumerate(AREAS)]

BASE_BILL = {'Companion care': 34.0, 'Personal care help': 37.0, 'Homemaking': 32.0, 'Respite care': 36.0, 'Overnight care': 38.0, 'Live-in day': 26.0}
BASE_PAY = {'Companion care': 17.5, 'Personal care help': 19.0, 'Homemaking': 17.0, 'Respite care': 18.5, 'Overnight care': 18.0, 'Live-in day': 15.0}
BILL_MULT = {'Weekday': 1.0, 'Evening': 1.06, 'Weekend': 1.12, 'Night': 1.18, 'Holiday': HOLIDAY_BILL_MULT}
PAY_MULT = {'Weekday': 1.0, 'Evening': 1.04, 'Weekend': 1.05, 'Night': 1.10, 'Holiday': HOLIDAY_PAY_MULT}
MIN_VISIT = {'Companion care': 2, 'Personal care help': 2, 'Homemaking': 3, 'Respite care': 4, 'Overnight care': 10, 'Live-in day': 12}
services = [dict(service_id='SV-%02d' % (i + 1), service=s, min_visit_hours=MIN_VISIT[s], bill_rate=BASE_BILL[s]) for i, s in enumerate(SERVICES)]
rate_card = []
for s in SERVICES:
    for b in BANDS:
        rate_card.append(dict(rate_id='RC-%02d' % (len(rate_card) + 1), service=s, band=b, bill_rate=R2(BASE_BILL[s] * BILL_MULT[b]), pay_rate=R2(BASE_PAY[s] * PAY_MULT[b])))
payers = [dict(payer_id='PY-%02d' % (i + 1), payer=p, rate_share=sh, pay_days=pd) for i, (p, sh, pd) in
          enumerate(zip(PAYERS, [1.0, 0.92, 0.90, 0.88], [10, 38, 45, 52]))]
credential_types = [dict(type_id='CT-%02d' % (i + 1), credential=c, renew_months=m, required_for=f) for i, (c, m, f) in
                    enumerate(zip(CRED_TYPES, [36, 12, 24, 12, 12, 24], ['All caregivers', 'All caregivers', 'All caregivers', 'Drivers', 'Drivers', 'Some caregivers']))]
shift_types = [dict(shift_id='ST-%02d' % (i + 1), shift=n, start=s, hours=h) for i, (n, s, h) in enumerate(
    [('Morning visit', '08:00', 4), ('Midday visit', '12:00', 3), ('Afternoon visit', '14:00', 3), ('Evening visit', '17:00', 2), ('Split morning', '08:00', 2),
     ('Respite block', '09:00', 8), ('Overnight shift', '21:00', 10), ('Live-in day', '08:00', 12), ('Weekend visit', '10:00', 4), ('Holiday visit', '10:00', 4),
     ('Short evening visit', '18:00', 2), ('Long respite day', '08:00', 12)])]


def _holidays():
    base = [('New Year Day', 1, 1), ('Spring Holiday', 4, 14), ('Early Summer Holiday', 5, 26), ('Midsummer Holiday', 7, 7), ('Late Summer Holiday', 8, 25),
            ('Autumn Holiday', 10, 13), ('Harvest Holiday', 11, 27), ('Year-end Eve', 12, 24), ('Year-end Holiday', 12, 25), ('Year-end Day 2', 12, 26)]
    out = []
    for y in range(HISTORY_START.year, TODAY.year + 2):
        for n, m, d in base:
            x = dt.date(y, m, d)
            if HISTORY_START <= x <= TODAY + day(200): out.append((x, n))
    return sorted(out)
_HOL = _holidays()
HOLIDAY_DATES = {x for x, _ in _HOL}
holidays = [dict(holiday_id='HD-%02d' % (i + 1), date=iso(x), holiday=n, pay_mult=HOLIDAY_PAY_MULT, bill_mult=HOLIDAY_BILL_MULT, weekday=WEEKDAYS[x.weekday()])
            for i, (x, n) in enumerate(_HOL)]
def holiday_rows(n=None): return _thin([dict(x) for x in holidays], n)

# ------------------------------------------------------------------ helpers for generators
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

_CGN = [('Adaeze Nwosu', ''), ('Maria Santos', 'Tagalog'), ('Olga Petrova', 'Russian'), ('Kwabena Mensah', 'Twi'), ('Fatima Zahra', 'Arabic'), ('Li Wei', 'Mandarin'),
        ('Priya Nair', 'Hindi'), ('Carlos Mendoza', 'Spanish'), ('Amara Okonkwo', ''), ('Sofia Rossi', 'Italian'), ('Hana Kobayashi', ''), ('Tariq Hussain', 'Arabic'),
        ('Elena Popescu', ''), ('Joseph Mwangi', ''), ('Lucia Fernandez', 'Spanish'), ('Ahmed Salem', 'Arabic'), ('Grace Tembo', ''), ('Jan Kowalczyk', 'Polish'),
        ('Nadia Rahman', 'Hindi'), ('Diego Alvarez', 'Spanish'), ('Bao Tran', 'Vietnamese'), ('Ingrid Solberg', ''), ('Samuel Osei', 'Twi'), ('Mei Ling Chen', 'Mandarin'),
        ('Rafael Costa', 'Portuguese'), ('Zainab Bello', ''), ('Oksana Melnyk', 'Russian'), ('Kofi Asante', 'Twi'), ('Leila Karimi', 'Arabic'), ('Marcus Johnson', ''),
        ('Anika Sharma', 'Hindi'), ('Tomas Novak', 'Polish'), ('Esperanza Cruz', 'Spanish'), ('Yusuf Demir', ''), ('Rosa Moreno', 'Spanish'), ('Dmitri Sokolov', 'Russian'),
        ('Chiamaka Eze', ''), ('Paulo Ferreira', 'Portuguese'), ('Aiko Tanaka', ''), ('Mohammed Aziz', 'Arabic'), ('Beatriz Lima', 'Portuguese'), ('Sipho Dlamini', ''),
        ('Karina Larsen', ''), ('Nguyen Thi Hoa', 'Vietnamese'), ('Wanjiru Njeri', ''), ('Isabella Conti', 'Italian'), ('Hamza Qureshi', 'Hindi'),
        ('Svetlana Ivanova', 'Russian'), ('Joy Adeyemi', ''), ('Pedro Castillo', 'Spanish')]
_FIRST = ['Eleanor', 'Hiroshi', 'Fatou', 'Giovanni', 'Ingrid', 'Mohammed', 'Rosalind', 'Chidi', 'Anneliese', 'Vikram', 'Dolores', 'Tadeusz', 'Mei', 'Alejandro', 'Beatrice', 'Kwame',
          'Yolanda', 'Sven', 'Noor', 'Walter', 'Esther', 'Rashid', 'Margarita', 'Oluwaseun', 'Harold', 'Ayesha', 'Lucien', 'Priscilla', 'Stanislav', 'Imelda', 'Thabo', 'Genevieve',
          'Arjun', 'Dorothea', 'Emeka', 'Pilar', 'Reginald', 'Sakura', 'Ibrahim', 'Winifred', 'Konstantin', 'Lakshmi', 'Percival', 'Amparo', 'Desmond', 'Halima', 'Leopold',
          'Marisol', 'Cornelius', 'Zofia', 'Bernard', 'Nneka', 'Franz', 'Carmen', 'Albert', 'Yasmin', 'Teodor', 'Florence', 'Mustafa', 'Ottilie', 'Jorge', 'Constance', 'Hamid',
          'Gwendolyn', 'Raimundo', 'Agnieszka', 'Clarence', 'Soledad', 'Viktor', 'Philippa']
_LAST = ['Whitfield', 'Nakamura', 'Okafor', 'Rossi', 'Lindqvist', 'Haddad', 'Kowalski', 'Mensah', 'Fernandez', 'Patel', 'Dubois', 'Schneider', 'Abebe', 'Tanaka', 'Petrov', "O'Brien",
         'Silva', 'Nguyen', 'Hassan', 'Ferreira', 'Johansson', 'Mwangi', 'Castillo', 'Rahman', 'Novak', 'Moreau', 'Adeyemi', 'Kim', 'Bianchi', 'Demir', 'Olsen', 'Santos',
         'Chowdhury', 'Varga', 'Boateng', 'Ibarra', 'Hoffmann', 'Sokolov', 'Achterberg', 'Mbeki', 'Yamamoto', 'Costa', 'Farouk', 'Lambert', 'Park', 'Zielinski', 'Dlamini',
         'Aguilar', 'Reyes', 'Brennan', 'Sato', 'Cohen', 'Osei', 'Ward', 'Ruiz', 'Thompson', 'Ansah', 'Greco', 'Larsen', 'Kapoor', 'Bello', 'Fischer', 'Marques', 'Ito', 'Laurent',
         'Quaye', 'Ellis', 'Vargas', 'Hartmann']
_STREETS = ['Linden Road', 'Cedar Lane', 'Harbour Street', 'Mill Close', 'Orchard Way', 'Station Road', 'Elm Court', 'Park Avenue', 'Willow Drive', 'Chapel Street',
            'Maple Grove', 'Bridge Road', 'Hill View', 'Meadow Lane', 'Church Walk', 'Quarry Road']
_AREA_W_CG = [0.14, 0.22, 0.20, 0.16, 0.16, 0.12]
_AREA_W_CL = [0.17, 0.22, 0.20, 0.17, 0.12, 0.12]

CAP_PERM = {'Hourly': 36.0, 'Part-time': 20.0, 'Live-in': 36.0}
CAP_COVER = {'Hourly': 46.0, 'Part-time': 28.0, 'Live-in': 36.0}


def _people():
    r = rng('people')
    PRE, INW = 22, 28
    cgs = []
    hire_ago = []
    for i in range(PRE): hire_ago.append(HISTORY_DAYS + 10 + int(r.random() * 1490))
    hire_ago.sort(reverse=True)
    for i in range(INW):
        base = (HISTORY_DAYS - 12) * (1 - (i + 0.5) / INW)
        hire_ago.append(max(3, int(base + r.randint(-6, 6))))
    hire_ago[-1] = 6; hire_ago[-2] = 20
    hire_ago[PRE:] = sorted(hire_ago[PRE:], reverse=True)
    livein = {3, 9, PRE + 14, PRE + 19}
    pre_leave = {1, 6, 11, 15, 19}; in_leave = {PRE + k for k in (2, 5, 8, 12, 16, 22, 24)}
    first90 = {PRE + 2, PRE + 8, PRE + 16, PRE + 24}
    for idx in range(PRE + INW):
        name, lang = _CGN[idx]
        typ = 'Live-in' if idx in livein else ('Part-time' if idx % 3 == 1 else 'Hourly')
        area = _wchoice(r, AREAS, _AREA_W_CG)
        if typ == 'Live-in': avail = 'Any time'
        elif typ == 'Part-time': avail = _wchoice(r, AVAILABILITY, [0.1, 0.4, 0.15, 0.35, 0.0])
        else: avail = _wchoice(r, AVAILABILITY, [0.30, 0.22, 0.28, 0.10, 0.10])
        skills = ['Companion care', 'Homemaking']
        pers = r.random() < 0.65
        if pers: skills.append('Personal care help')
        if pers and r.random() < 0.7: skills.append('Respite care')
        if avail in ('Any time', 'Nights and weekends') and r.random() < 0.8: skills.append('Overnight care')
        if typ == 'Live-in': skills = ['Live-in day', 'Companion care']
        pay = (14.0 + 0.5 * r.randint(0, 3)) if typ == 'Live-in' else (16.5 + 0.5 * r.randint(0, 8) + (1.0 if pers else 0))
        h_ago = hire_ago[idx]
        left = None; reason = ''
        if idx in pre_leave:
            la = int(HISTORY_DAYS - 40 - r.random() * (HISTORY_DAYS - 140)); left = TODAY - day(la)
        if idx in in_leave:
            ten = r.randint(25, 85) if idx in first90 else r.randint(120, 300)
            ten = min(ten, h_ago - 5)
            if idx == PRE + 22: ten = h_ago - max(0, min(5, TODAY.day - 1))
            left = TODAY - day(h_ago - ten)
        if left:
            reason = _wchoice(r, LEAVE_REASONS, [0.28, 0.2, 0.1, 0.14, 0.1, 0.18] if idx not in first90 else [0.2, 0.3, 0.05, 0.25, 0.05, 0.15])
        cgs.append(dict(caregiver_id='CG-%03d' % (idx + 1), name=name, _hire=TODAY - day(h_ago), _left=left, employment=typ, pay_rate=pay, _skills=skills, languages=lang, area=area,
                        availability=avail, leave_reason=reason, _idx=idx, drives=r.random() < 0.72,
                        source=_wchoice(r, REC_SOURCES, [0.32, 0.18, 0.14, 0.1, 0.14, 0.07, 0.05]) if h_ago < HISTORY_DAYS else ''))
    # pinned caregivers for the story
    p = cgs[5]; p.update(employment='Hourly', pay_rate=21.5, area='Riverside', availability='Any time', _skills=['Companion care', 'Personal care help', 'Homemaking'], languages='')
    t = cgs[8]; t.update(employment='Hourly', pay_rate=19.0, area='Old Town', availability='Any time', _skills=['Companion care', 'Personal care help', 'Homemaking', 'Respite care'])
    for g in cgs:
        g['hire_date'] = iso(g['_hire']); g['left_date'] = iso(g['_left']) if g['_left'] else ''
        g['skills'] = '; '.join(g['_skills'])
        g['languages'] = ('English; ' + g['languages']) if g['languages'] else 'English'
        g['_langs'] = set(g['languages'].split('; '))
        g['hours_limit'] = {'Hourly': 40, 'Part-time': 20, 'Live-in': 36}[g['employment']]
        g['status'] = 'Left' if g['_left'] else 'Active'
        g['phone'] = fake_phone(200 + g['_idx']); g['email'] = fake_email(g['name'])
        g['pay_rate_old'] = R2(g['pay_rate'] / 1.03)
    [g for g in cgs if g['_left']][2]['leave_reason'] = 'Moved away'
    # two active caregivers on leave
    for k in (13, 31): cgs[k]['status'] = 'On leave'
    # ---------------- clients
    cls = []
    used = {g['name'] for g in cgs} | {t['name'] for t in team}
    combos = [(f, l) for f in _FIRST for l in _LAST]; r.shuffle(combos)
    names = []
    for f, l in combos:
        nm = f + ' ' + l
        if nm not in used: names.append(nm); used.add(nm)
        if len(names) >= 90: break
    def mk(start_ago, svc, hours, area, payer, special='', end_ago=None, cycle=None, lang='English', factor=None, locked=False, pin=None, slots=None, prepay=False):
        i = len(cls)
        if factor is None: factor = {'Private pay': r.choice([0.96, 1.0, 1.0, 1.04]), 'Care insurer': 0.92, 'Third-party payer A': 0.90, 'Third-party payer B': 0.88}[payer]
        sl = slots if slots is not None else _template(r, svc, hours)
        for s in sl: s.setdefault('cg', None)
        c = dict(_i=i, client=names[i], street='%d %s' % (r.randint(2, 98), r.choice(_STREETS)), area=area, payer=payer, service=svc, _start=TODAY - day(start_ago),
                 _end=(TODAY - day(end_ago)) if end_ago is not None else None, billing_cycle=cycle or (r.choice(BILL_CYCLES) if payer == 'Private pay' else 'Monthly'),
                 language=lang, rate_factor=factor, rate_locked=locked, _slots=sl, _special=special, prepay=prepay, min_visit_hours=MIN_VISIT[svc] if svc != 'Companion care' or r.random() < 0.8 else 3,
                 source=_wchoice(r, ENQ_SOURCES, [0.24, 0.2, 0.14, 0.14, 0.1, 0.1, 0.08]))
        c['weekly_hours'] = sum(s['hrs'] for s in sl)
        if pin:
            for s in sl: s['cg'] = pin; s['_pin'] = pin
        cls.append(c)
        return c
    def pick_area(): return _wchoice(r, AREAS, _AREA_W_CL)
    def hrs_for(svc):
        return {'Companion care': r.choice([6, 8, 10, 12, 12, 14, 16, 20, 24]), 'Personal care help': r.choice([8, 10, 12, 16, 16, 20, 24, 28]),
                'Homemaking': r.choice([6, 8, 9, 12]), 'Respite care': r.choice([8, 12, 16, 24]), 'Overnight care': r.choice([30, 40])}[svc]
    def rand_svc(): return _wchoice(r, SERVICES[:5], [0.38, 0.28, 0.12, 0.10, 0.12])
    def rand_lang(): return 'English' if r.random() < 0.88 else r.choice(['Spanish', 'Polish', 'Portuguese', 'Hindi', 'Arabic', 'Tagalog', 'Mandarin', 'Russian', 'Italian'])
    def rand_payer(): return _wchoice(r, PAYERS, [0.74, 0.13, 0.08, 0.05])
    # specials
    mk(HISTORY_DAYS + 120, 'Live-in day', 72, 'Old Town', 'Private pay', 'livein1', cycle='Weekly', factor=1.0)
    mk(520, 'Companion care', 16, 'North Hills', 'Private pay', 'feeder', factor=1.0, slots=[dict(wd=w, start=600, hrs=4, svc='Companion care') for w in range(4)], pin='CG-006', cycle='Monthly')
    mk(520, 'Personal care help', 12, 'South Valley', 'Private pay', 'belowcost', factor=0.81, locked=True, cycle='Monthly',
       slots=[dict(wd=w, start=960, hrs=3, svc='Personal care help') for w in range(4)], pin='CG-006')
    mk(330, 'Companion care', 16, 'Old Town', 'Private pay', 'overdue', cycle='Monthly', factor=1.0)
    mk(400, 'Companion care', 15, 'Riverside', 'Private pay', 'continuity', cycle='Weekly', factor=1.0,
       slots=[dict(wd=w, start=780, hrs=3, svc='Companion care') for w in range(5)])
    mk(200, 'Live-in day', 72, 'East Park', 'Private pay', 'livein2', cycle='Weekly', factor=1.0)
    nspec = len(cls)
    # randoms: 27 before the window (10 end), 51 inside (20 end)
    for k in range(27):
        svc = rand_svc(); pay = rand_payer()
        ended = k < 10
        e_ago = int(60 + r.random() * (HISTORY_DAYS - 100)) if ended else None
        mk(HISTORY_DAYS + 10 + int(r.random() * 700), svc, hrs_for(svc), pick_area(), pay, end_ago=e_ago, lang=rand_lang(), prepay=False)
    starts = sorted([int(HISTORY_DAYS * (1 - (k + 0.5) / 51) ** 1.0) + r.randint(-5, 5) for k in range(51)], reverse=True)
    starts = [max(2, s) for s in starts]; starts[-1] = 4; starts[-2] = 12; starts[-3] = 24; starts[-4] = 27; starts[-5] = 40
    ended_idx = set(r.sample(range(1, 46), 18)) | {44, 45, 46}
    for k in range(51):
        svc = rand_svc(); pay = rand_payer(); sa = starts[k]
        e_ago = None
        if k in ended_idx and sa > 45:
            e_ago = max(1, sa - r.randint(40, min(420, sa - 2)))
            if k == 44: e_ago = 1 if sa > 50 else e_ago
        mk(sa, svc, hrs_for(svc), pick_area(), pay, end_ago=e_ago, lang=rand_lang())
    # prepaid-balance clients: 8 private pay, not special
    cand = [c for c in cls[nspec:] if c['payer'] == 'Private pay' and not c['_end'] and c['billing_cycle'] != 'Weekly']
    for c in cand[:8]: c['prepay'] = True
    act = [c for c in cls[nspec:] if not c['_end'] and (TODAY - c['_start']).days > 200]
    while sum(1 for c in cls if not c['_end']) > 54 and act:
        c = act.pop(0); c['_end'] = TODAY - day(2 + len(act))
    # ids by start date
    cls.sort(key=lambda c: (c['_start'], c['_i']))
    for i, c in enumerate(cls, 1):
        c['client_id'] = 'CL-%03d' % i
        c['phone'] = fake_phone(300 + i); c['email'] = fake_email(c['client'])
        c['status'] = 'Ended' if c['_end'] else 'Active'
        c['start_date'] = iso(c['_start']); c['end_date'] = iso(c['_end']) if c['_end'] else ''
        c['end_reason'] = r.choice(END_REASONS) if c['_end'] else ''
        sv = c['service']
        c['bill_rate'] = _bill_rate(c, sv, 'Weekday', TODAY)
        c['deposit'] = 0.0 if c['payer'] != 'Private pay' else float(int(round(DEPOSIT_WEEKS * c['weekly_hours'] * c['bill_rate'] / 10.0) * 10))
        for s in c['_slots']:
            if s['cg'] and s['cg'].startswith('CG-') and not s.get('_pin'): s['cg'] = None
    for c in cls:
        if c['_special'] == 'belowcost': c['rate_factor'] = 0.81
    for c in cls:
        for s in c['_slots']:
            if s.get('_pin'): s['cg'] = next(g['caregiver_id'] for g in cgs if g['caregiver_id'] == s['_pin'])
    cmap = {g['caregiver_id']: g for g in cgs}
    return cgs, cls


def _band(d, start_min):
    if d in HOLIDAY_DATES: return 'Holiday'
    if d.weekday() >= 5: return 'Weekend'
    if start_min >= 21 * 60 or start_min < 6 * 60: return 'Night'
    if start_min >= 17 * 60: return 'Evening'
    return 'Weekday'


def _bill_rate(c, svc, band, d):
    f = c['rate_factor']
    if c['rate_locked'] or d >= D(TODAY.year, 1, 1): yr = 1.0
    else: yr = 1 / 1.04
    return R2(BASE_BILL[svc] * BILL_MULT[band] * f * yr)


def _template(r, svc, hours):
    if svc == 'Live-in day': return [dict(wd=w, start=480, hrs=12, svc=svc) for w in range(6)]
    if svc == 'Overnight care':
        nights = int(hours // 10)
        return [dict(wd=w, start=21 * 60, hrs=10, svc=svc) for w in sorted(r.sample(range(7), nights))]
    length = r.choice({'Companion care': [2, 3, 4], 'Personal care help': [2, 2, 3], 'Homemaking': [3, 4], 'Respite care': [4, 6, 8]}[svc])
    days = max(1, min(7, int(round(hours / float(length)))))
    wds = sorted(r.sample(range(5), min(days, 5)))
    if days > 5: wds += [5, 6][:days - 5]
    elif r.random() < 0.18 and len(wds) > 1: wds[-1] = r.choice([5, 6])
    wds = sorted(set(wds))
    start = _wchoice(r, [8 * 60, 9 * 60, 10 * 60, 12 * 60, 13 * 60, 14 * 60, 15 * 60, 17 * 60, 18 * 60], [0.2, 0.18, 0.12, 0.1, 0.1, 0.08, 0.05, 0.09, 0.08])
    sl = [dict(wd=w, start=start, hrs=length, svc=svc) for w in wds]
    if svc == 'Personal care help' and r.random() < 0.2 and start < 12 * 60:
        sl += [dict(wd=w, start=18 * 60, hrs=2, svc=svc) for w in wds[:3]]
    return sl

# ------------------------------------------------------------------ time off, matching helpers
def _timeoff(cgs):
    r = rng('timeoff'); out = []
    for g in cgs:
        if g['employment'] == 'Live-in': continue
        a = g['_hire'] + day(30); b = (g['_left'] or TODAY + day(120)) - day(3)
        span = (b - a).days
        if span < 40: continue
        n = max(1, int(span / 150))
        for _ in range(n):
            k = _wchoice(r, TIMEOFF_KINDS, [0.5, 0.35, 0.15]); ln = {'Holiday': r.randint(4, 9), 'Sick day': r.randint(1, 3), 'Training day': 1}[k]
            s = a + day(r.randint(0, max(0, span - ln)))
            if k == 'Holiday' and r.random() < 0.3:      # year-end peak
                y = s.year if s.month >= 6 else s.year - 1
                s = dt.date(y, 12, 20) + day(r.randint(0, 6))
                if s > TODAY + day(120) or s < a or s > b: continue
            out.append((g['caregiver_id'], k, s, s + day(ln - 1)))
    out.sort(key=lambda x: (x[2], x[0]))
    return out


def _match(g, c):
    s = 3.0 * (1 - min(travel_minutes(g['area'], c['area']), 45) / 45.0)
    if c['language'] != 'English' and c['language'] in g['_langs']: s += 4
    if g['name'] in c.get('_pref', ()): s += 3
    return s


def _can(g, svc, d, st, band):
    if svc not in g['_skills']: return False
    if g['employment'] == 'Live-in': return svc == 'Live-in day'
    if svc == 'Live-in day': return False
    a = g['availability']; wd = d.weekday(); h = st // 60
    if svc == 'Overnight care': return a in ('Any time', 'Nights and weekends')
    if a == 'Any time': return True
    if a == 'Weekdays': return wd < 5 and 7 <= h <= 15 and band != 'Holiday'
    if a == 'Weekdays and evenings': return wd < 5 and 7 <= h <= 19
    if a == 'Weekends and evenings': return wd >= 5 or h >= 16
    return wd >= 5 or band == 'Night'


def _conflict(lst, s, e, area):
    for (s2, e2, a2) in lst:
        gap = travel_minutes(a2, area) + 10
        if s < e2 + gap and s2 < e + gap: return True
    return False


def _simulate():
    r = rng('sim')
    cgs, cls = _raw('people', _people)
    cmap = {g['caregiver_id']: g for g in cgs}
    tos = _timeoff(cgs)
    off = {}
    for cid, k, a, b in tos:
        for i in range((b - a).days + 1): off[(cid, a + day(i))] = k
    W0 = week_start(HISTORY_START); END = TODAY + day(POST_SCHEDULE_DAYS)
    nweeks = (week_start(END) - W0).days // 7 + 1
    ot_week = week_start(TODAY + day(3))
    T = cgs[8]['caregiver_id']
    seen = defaultdict(dict)     # client_id -> {cgid: last week index}
    story_used = set()
    visits = []; calloffs = []; weeks = []
    for wi in range(nweeks):
        ws = W0 + day(7 * wi); we = ws + day(6)
        loads = defaultdict(float); busy = defaultdict(list); cw = defaultdict(set)
        act = [g for g in cgs if g['_hire'] <= we and (g['_left'] is None or g['_left'] >= ws)]
        def emp(g, d): return g['_hire'] <= d and (g['_left'] is None or g['_left'] >= d)
        def pick(c, d, st, hrs, svc, band, mode, exclude=()):
            best = None; bs = -1e9
            recent = {k for k, w in seen[c['client_id']].items() if wi - w < 4} | cw[c['client_id']]
            for g in act:
                gid = g['caregiver_id']
                if gid in exclude or not emp(g, d) or (gid, d) in off or g['status'] == 'On leave': continue
                if not _can(g, svc, d, st, band): continue
                if _conflict(busy[(gid, d)], st, st + hrs * 60, c['area']): continue
                cap = (CAP_PERM if mode == 'perm' else CAP_COVER)[g['employment']]
                if loads[gid] + hrs > cap: continue
                sc = _match(g, c) - 0.12 * loads[gid]
                if busy[(gid, d)]: sc += 1.5
                if gid in recent: sc += 5
                elif len(recent) >= CONTINUITY_LIMIT: sc -= 8
                if sc > bs: bs = sc; best = g
            return best
        def reg(v, gid):
            busy[(gid, v['_d'])].append((v['_st'], v['_st'] + v['_hrs'] * 60, v['_c']['area'])); loads[gid] += v['_hrs']; cw[v['_c']['client_id']].add(gid)
        def unreg(v, gid):
            busy[(gid, v['_d'])].remove((v['_st'], v['_st'] + v['_hrs'] * 60, v['_c']['area'])); loads[gid] -= v['_hrs']
        todo = []
        for c in cls:
            if c['_start'] > we or (c['_end'] and c['_end'] < ws): continue
            for s in c['_slots']:
                d = ws + day(s['wd'])
                if d < c['_start'] or (c['_end'] and d > c['_end']) or d > END: continue
                todo.append((d, s['start'], c, s))
        todo.sort(key=lambda x: (x[0], x[1], x[2]['client_id']))
        wv = []; pend = []
        for d, st, c, s in todo:
            band = _band(d, st)
            v = dict(_d=d, _st=st, _hrs=s['hrs'], _c=c, _s=s, service=s['svc'], band=band, planned='', actual='', cover_type='Planned', status='', reason='')
            wv.append(v)
            gid = s.get('cg'); g = cmap.get(gid) if gid else None
            forced = c['_special'] == 'continuity' and TODAY - day(29) <= d <= TODAY and len(story_used) < 7
            if g and emp(g, d) and (gid, d) not in off and g['status'] != 'On leave' and not forced and not _conflict(busy[(gid, d)], st, st + s['hrs'] * 60, c['area']):
                v['planned'] = gid; v['actual'] = gid; reg(v, gid)
            else: pend.append((v, g, forced))
        for v, g, forced in pend:
            c = v['_c']; s = v['_s']; d = v['_d']; st = v['_st']; hrs = v['_hrs']
            if forced:
                pk = pick(c, d, st, hrs, v['service'], v['band'], 'cover', exclude=story_used)
                if pk:
                    story_used.add(pk['caregiver_id']); v['planned'] = s['cg'] or pk['caregiver_id']; v['actual'] = pk['caregiver_id']; v['cover_type'] = 'Cover'; reg(v, pk['caregiver_id']); continue
            if g and emp(g, d) and ((g['caregiver_id'], d) in off or g['status'] == 'On leave'):
                v['planned'] = g['caregiver_id']
                pk = pick(c, d, st, hrs, v['service'], v['band'], 'cover', exclude=(g['caregiver_id'],))
                if pk: v['actual'] = pk['caregiver_id']; v['cover_type'] = 'Cover'; reg(v, pk['caregiver_id'])
                else: v['cover_type'] = 'Uncovered'
                continue
            pk = pick(c, d, st, hrs, v['service'], v['band'], 'perm') or pick(c, d, st, hrs, v['service'], v['band'], 'cover')
            if pk:
                s['cg'] = pk['caregiver_id']; v['planned'] = v['actual'] = pk['caregiver_id']; reg(v, pk['caregiver_id'])
            else: v['cover_type'] = 'Uncovered'
        # call-offs
        for v in wv:
            d = v['_d']; c = v['_c']
            if not v['actual'] or v['cover_type'] != 'Planned': continue
            if d > TODAY + day(1) or (d == TODAY and v['_st'] > 600): continue
            p = 0.035
            if any(abs((d - h).days) <= 3 for h in HOLIDAY_DATES): p *= 2
            if (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 3): p *= 1.8
            if d == TODAY + day(1): p = 0.14
            if r.random() >= p: continue
            gid = v['actual']; unreg(v, gid)
            pk = pick(c, d, v['_st'], v['_hrs'], v['service'], v['band'], 'cover', exclude=(gid,))
            notice = r.choice([2, 3, 4, 6, 8, 12, 24, 36, 48]) if d > TODAY else r.choice([1, 2, 3, 4, 6, 8, 12, 24])
            reason = _wchoice(r, CALLOFF_REASONS, [0.34, 0.2, 0.12, 0.08, 0.14, 0.12])
            co = dict(date=iso(d), _v=v, caregiver_id=gid, client_id=c['client_id'], reason=reason, notice_hours=notice, cover_id='', minutes_to_cover=0, premium=0.0, covered=False)
            if pk:
                v['actual'] = pk['caregiver_id']; v['cover_type'] = 'Cover'; reg(v, pk['caregiver_id'])
                co.update(cover_id=pk['caregiver_id'], minutes_to_cover=r.choice([10, 20, 30, 45, 60, 90, 120, 180, 240]), covered=True)
                if notice < 24: co['_prem'] = True
            else:
                v['actual'] = ''; v['cover_type'] = 'Uncovered'
            calloffs.append(co)
        # story: a caregiver scheduled into overtime in the overtime week
        if ws == ot_week:
            tg = cmap[T]
            for v in sorted(wv, key=lambda x: (x['_d'], x['_st'])):
                if loads[T] >= 45.5: break
                d = v['_d']
                if d <= TODAY or not v['actual'] or v['actual'] == T or not emp(tg, d) or (T, d) in off: continue
                if v['service'] in ('Live-in day', 'Overnight care') or v['_c']['_special'] in ('feeder', 'belowcost', 'continuity'): continue
                if not _can(tg, v['service'], d, v['_st'], v['band']) or _conflict(busy[(T, d)], v['_st'], v['_st'] + v['_hrs'] * 60, v['_c']['area']): continue
                unreg(v, v['actual']); v['actual'] = T; v['cover_type'] = 'Cover'; reg(v, T)
        # resolve status and times
        for v in wv:
            d = v['_d']; c = v['_c']; area = c['area']
            res = d < TODAY or (d == TODAY and v['_st'] <= 600)
            v['_res'] = res
            late_p, miss_p = 0.05, 0.008
            if d.month in (12, 1, 2): late_p = 0.065
            if area == 'South Valley' and d >= TODAY - day(75): late_p, miss_p = 0.24, 0.055
            if not res:
                v['status'] = 'Scheduled' if v['actual'] else 'Open'
                continue
            if not v['actual']:
                v['status'] = 'Missed'; v['reason'] = 'No cover found'; continue
            x = r.random()
            if x < 0.03 and c['_special'] not in ('livein1', 'livein2'): v['status'] = 'Cancelled'; v['reason'] = ''; v['_cancel_h'] = r.choice([4, 12, 24, 48, 72]); continue
            if x < 0.03 + miss_p: v['status'] = 'Missed'; v['reason'] = _wchoice(r, MISS_REASONS[1:], [0.55, 0.2, 0.25]); continue
            if d == TODAY and r.random() < 0.16: v['status'] = 'No check-in'; continue
            v['status'] = 'Late' if r.random() < late_p / (1 - 0.03 - miss_p) else 'Completed'
            if v['status'] == 'Late': v['reason'] = _wchoice(r, DELAY_REASONS, [0.3, 0.12, 0.2, 0.1, 0.08, 0.08, 0.12])
        # travel (paid between visits of the same day)
        by = defaultdict(list)
        for v in wv:
            if v['actual'] and v['status'] in ('Scheduled', 'Completed', 'Late', 'No check-in'): by[(v['actual'], v['_d'])].append(v)
        for k, lst in by.items():
            lst.sort(key=lambda x: x['_st']); prev = None
            for v in lst:
                if prev is not None and v['service'] not in ('Live-in day', 'Overnight care') and prev['service'] not in ('Live-in day', 'Overnight care'):
                    v['travel_min'] = travel_minutes(prev['_c']['area'], v['_c']['area']); v['distance_km'] = travel_km(prev['_c']['area'], v['_c']['area']); v['from_area'] = prev['_c']['area']
                prev = v
        # times and hours
        for v in wv:
            v.setdefault('travel_min', 0); v.setdefault('distance_km', 0.0); v.setdefault('from_area', '')
            v['check_in'] = v['check_out'] = ''; v['late_minutes'] = 0; v['actual_hours'] = 0.0
            if v['status'] in ('Completed', 'Late'):
                off_in = r.randint(16, 55) if v['status'] == 'Late' else r.randint(-6, 10)
                if v['status'] == 'Late' and r.random() < 0.3: off_in = r.randint(16, 25)
                tin = v['_st'] + off_in; tout = v['_st'] + v['_hrs'] * 60 + r.randint(-10, 14)
                if v['service'] == 'Live-in day': tin = v['_st'] + r.randint(-5, 8); tout = v['_st'] + 720 + r.randint(-8, 10)
                v['check_in'] = _hhmm(tin); v['check_out'] = _hhmm(tout); v['late_minutes'] = max(0, off_in)
                v['actual_hours'] = round((tout - tin) / 60.0, 2)
        # overtime allocation by caregiver for the week
        bycg = defaultdict(list)
        for v in wv:
            if v['actual'] and v['status'] in ('Scheduled', 'Completed', 'Late', 'No check-in'): bycg[v['actual']].append(v)
        for gid, lst in bycg.items():
            g = cmap[gid]
            basis = sum((v['actual_hours'] if v['actual_hours'] else v['_hrs']) + v['travel_min'] / 60.0 for v in lst)
            ot = max(0.0, basis - OVERTIME_HOURS) if g['employment'] != 'Live-in' else 0.0
            for v in lst: v['_ot_share'] = ((v['actual_hours'] or v['_hrs']) + v['travel_min'] / 60.0) / basis * ot
            weeks.append(dict(week=ws, gid=gid, scheduled=sum(v['_hrs'] for v in lst), worked=sum(v['actual_hours'] for v in lst if v['status'] in ('Completed', 'Late')),
                              travel=sum(v['travel_min'] for v in lst) / 60.0, ot=ot, km=sum(v['distance_km'] for v in lst), visits=len(lst)))
        for v in wv:
            if v['actual']: seen[v['_c']['client_id']][v['actual']] = wi
        visits.extend(wv)
    # money
    pre = {}
    for v in visits:
        c = v['_c']; d = v['_d']; st = v['status']; gid = v['actual']
        v.update(pay_rate_used=0.0, pay=0.0, holiday_premium=0.0, overtime_pay=0.0, travel_pay=0.0, mileage_pay=0.0, cover_premium=0.0, burden=0.0, cost=0.0, margin=0.0,
                 billed_hours=0.0, bill_rate=0.0, charge=0.0)
        rate = _bill_rate(c, v['service'], v['band'], d); v['bill_rate'] = rate
        if st in ('Completed', 'Late'):
            g = cmap[gid]; base = g['pay_rate'] if d >= D(TODAY.year, 1, 1) else g['pay_rate_old']
            pr = R2(base * PAY_MULT[v['band']]); h = v['actual_hours']
            v['pay_rate_used'] = pr; v['pay'] = R2(pr * h); v['holiday_premium'] = R2(base * 0.5 * h) if v['band'] == 'Holiday' else 0.0
            v['travel_pay'] = R2(base * v['travel_min'] / 60.0); v['mileage_pay'] = R2(v['distance_km'] * MILEAGE_RATE)
            v['overtime_pay'] = R2((OVERTIME_MULT - 1) * base * v.get('_ot_share', 0.0))
            co = [x for x in calloffs if x['_v'] is v]
            if co and co[0].get('_prem'): v['cover_premium'] = R2(COVER_PREMIUM * h); co[0]['premium'] = v['cover_premium']
            v['billed_hours'] = max(float(c['min_visit_hours']) if v['service'] not in ('Overnight care', 'Live-in day') else float(MIN_VISIT[v['service']]),
                                    round(min(h, v['_hrs'] + 0.5) * 4) / 4.0)
            if v['service'] in ('Live-in day', 'Overnight care'): v['billed_hours'] = float(MIN_VISIT[v['service']])
            v['charge'] = R2(v['billed_hours'] * rate)
            v['burden'] = R2(PAYROLL_BURDEN * (v['pay'] + v['travel_pay'] + v['overtime_pay'] + v['cover_premium']))
            v['cost'] = R2(v['pay'] + v['travel_pay'] + v['overtime_pay'] + v['cover_premium'] + v['burden'] + v['mileage_pay'])
            v['margin'] = R2(v['charge'] - v['cost'])
    visits.sort(key=lambda v: (v['_d'], v['_st'], v['_c']['client_id']))
    for i, v in enumerate(visits, 1): v['visit_id'] = 'VS-%05d' % i
    calloffs.sort(key=lambda x: x['date'])
    for i, x in enumerate(calloffs, 1): x['calloff_id'] = 'CO-%04d' % i
    return dict(cgs=cgs, cls=cls, visits=visits, calloffs=calloffs, weeks=weeks, timeoff=tos, nweeks=nweeks, ot_week=ot_week, W0=W0)


def _W(): return _raw('world', _simulate)

# ------------------------------------------------------------------ public generators: people, schedule, visits
def _cmap(): return _raw('cmap', lambda: {g['caregiver_id']: g for g in _W()['cgs']})
def _clmap(): return _raw('clmap', lambda: {c['client_id']: c for c in _W()['cls']})


def _prefs():
    def f():
        cnt = defaultdict(lambda: defaultdict(int)); cm = _cmap()
        for v in _W()['visits']:
            if v['actual'] and v['status'] in ('Completed', 'Late') and v['_d'] >= TODAY - day(120): cnt[v['_c']['client_id']][v['actual']] += 1
        out = {}
        for cid, d in cnt.items():
            top = sorted(d.items(), key=lambda kv: -kv[1])[:2]; out[cid] = [cm[k]['name'] for k, _ in top]
        return out
    return _raw('prefs', f)


def caregiver_rows(n=None):
    def f():
        out = []
        for g in _W()['cgs']:
            out.append(dict(caregiver_id=g['caregiver_id'], name=g['name'], hire_date=g['hire_date'], employment=g['employment'], pay_rate=g['pay_rate'], skills=g['skills'],
                            languages=g['languages'], area=g['area'], availability=g['availability'], hours_limit=g['hours_limit'], status=g['status'], left_date=g['left_date'],
                            leave_reason=g['leave_reason'], source=g['source'], phone=g['phone'], email=g['email']))
        return out
    return _thin(_cached('cg', f), n)


def client_rows(n=None):
    def f():
        pf = _prefs(); out = []
        for c in _W()['cls']:
            p = pf.get(c['client_id'], ['', ''])
            out.append(dict(client_id=c['client_id'], client=c['client'], street=c['street'], area=c['area'], phone=c['phone'], email=c['email'], payer=c['payer'], service=c['service'],
                            weekly_hours=float(c['weekly_hours']), bill_rate=c['bill_rate'], min_visit_hours=c['min_visit_hours'], billing_cycle=c['billing_cycle'],
                            language=c['language'], preferred=p[0] if p else '', preferred_2=p[1] if len(p) > 1 else '', source=c['source'], start_date=c['start_date'],
                            status=c['status'], end_date=c['end_date'], end_reason=c['end_reason'], deposit=c['deposit'], prepay=c['prepay']))
        return out
    return _thin(_cached('cl', f), n)


def availability_rows(n=None):
    def f():
        out = []
        for g in _W()['cgs']:
            if g['_left']: continue
            for wd in range(7):
                a = g['availability']
                if g['employment'] == 'Live-in': w = (480, 1200) if wd < 6 else None
                elif a == 'Any time': w = (360, 1380)
                elif a == 'Weekdays': w = (420, 960) if wd < 5 else None
                elif a == 'Weekdays and evenings': w = (420, 1200) if wd < 5 else None
                elif a == 'Weekends and evenings': w = (960, 1260) if wd < 5 else (480, 1200)
                else: w = (1260, 1800) if wd < 5 else (480, 1200)
                if w: out.append(dict(caregiver_id=g['caregiver_id'], caregiver=g['name'], weekday=WEEKDAYS[wd], from_time=_hhmm(w[0]), to_time=_hhmm(w[1]), max_hours=g['hours_limit']))
        for i, x in enumerate(out, 1): x['avail_id'] = 'AV-%03d' % i
        return [dict(avail_id=x.pop('avail_id'), **x) for x in out]
    return _thin(_cached('avail', f), n)


def time_off_rows(n=None):
    def f():
        cm = _cmap(); out = []
        for cid, k, a, b in _W()['timeoff']:
            out.append(dict(caregiver_id=cid, caregiver=cm[cid]['name'], kind=k, start_date=iso(a), end_date=iso(b), days=(b - a).days + 1,
                            approved=True))
        for i, x in enumerate(out, 1): x['timeoff_id'] = 'TO-%03d' % i
        return [dict(timeoff_id=x.pop('timeoff_id'), **x) for x in out]
    return _thin(_cached('toff', f), n)


def _vpub(v):
    cm = _cmap(); c = v['_c']; d = v['_d']
    g = cm.get(v['actual']); p = cm.get(v['planned'])
    return dict(visit_id=v['visit_id'], date=iso(d), week=iso(week_start(d)), month=iso(_ms(d)), weekday=WEEKDAYS[d.weekday()], start=_hhmm(v['_st']), sched_hours=float(v['_hrs']),
                client_id=c['client_id'], client=c['client'], area=c['area'], service=v['service'], band=v['band'], planned_id=v['planned'], planned=p['name'] if p else '',
                caregiver_id=v['actual'], caregiver=g['name'] if g else '', cover_type=v['cover_type'], status=v['status'], reason=v['reason'], check_in=v['check_in'],
                check_out=v['check_out'], late_minutes=v['late_minutes'], actual_hours=v['actual_hours'], billed_hours=v['billed_hours'], bill_rate=v['bill_rate'], charge=v['charge'],
                pay_rate=v['pay_rate_used'], pay=v['pay'], holiday_premium=v['holiday_premium'], overtime_pay=v['overtime_pay'], travel_min=v['travel_min'], distance_km=v['distance_km'],
                from_area=v['from_area'], travel_pay=v['travel_pay'], mileage_pay=v['mileage_pay'], cover_premium=v['cover_premium'], burden=v['burden'], cost=v['cost'], margin=v['margin'])


def _vall(): return _raw('vall', lambda: [_vpub(v) for v in _W()['visits']])
def visit_rows(n=None): return _thin([dict(x) for x in _vall()], n)


def calloff_rows(n=None):
    def f():
        cm = _cmap(); cl = _clmap(); out = []
        for x in _W()['calloffs']:
            v = x['_v']
            out.append(dict(calloff_id=x['calloff_id'], date=x['date'], visit_id=v['visit_id'], client_id=x['client_id'], client=cl[x['client_id']]['client'], area=cl[x['client_id']]['area'],
                            caregiver_id=x['caregiver_id'], caregiver=cm[x['caregiver_id']]['name'], reason=x['reason'], notice_hours=x['notice_hours'], hours=float(v['_hrs']),
                            cover_caregiver=cm[x['cover_id']]['name'] if x['cover_id'] else '', minutes_to_cover=x['minutes_to_cover'], premium=x['premium'], covered=x['covered']))
        return out
    return _thin(_cached('co', f), n)


def hours_rows(n=None):
    """one row per caregiver per week: scheduled, worked and travel hours, overtime hours, distance, visits"""
    def f():
        cm = _cmap(); out = []
        co = defaultdict(int); late = defaultdict(int)
        for x in _W()['calloffs']: co[(x['caregiver_id'], iso(week_start(to_date(x['date']))))] += 1
        for v in _W()['visits']:
            if v['actual'] and v['status'] == 'Late': late[(v['actual'], iso(week_start(v['_d'])))] += 1
        for w in sorted(_W()['weeks'], key=lambda w: (w['week'], w['gid'])):
            k = (w['gid'], iso(w['week']))
            out.append(dict(week=iso(w['week']), month=iso(_ms(w['week'])), caregiver_id=w['gid'], caregiver=cm[w['gid']]['name'], employment=cm[w['gid']]['employment'],
                            scheduled_hours=R2(w['scheduled']), worked_hours=R2(w['worked']), travel_hours=R2(w['travel']), overtime_hours=R2(w['ot']), distance_km=R2(w['km']),
                            visits=w['visits'], call_offs=co.get(k, 0), late_visits=late.get(k, 0)))
        for i, x in enumerate(out, 1): x['row_id'] = 'HW-%05d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('hw', f), n)


def week_rows(n=None):
    """one row per week for the whole agency: hours scheduled, covered by the planned caregiver, by cover, not covered, delivered, billed and paid"""
    def f():
        agg = {}
        for v in _W()['visits']:
            w = iso(week_start(v['_d'])); a = agg.setdefault(w, defaultdict(float))
            if v['status'] == 'Cancelled': continue
            h = v['_hrs']; a['sched'] += h
            if not v['actual']: a['unc'] += h
            elif v['cover_type'] == 'Cover': a['cov'] += h
            else: a['plan'] += h
            if v['status'] in ('Completed', 'Late'):
                a['deliv'] += v['actual_hours']; a['billed'] += v['billed_hours']; a['paid'] += v['actual_hours'] + v['travel_min'] / 60.0
            if v['status'] == 'Late': a['late'] += 1
            if v['status'] == 'Missed': a['missed'] += 1
            a['visits'] += 1
        out = []
        for w in sorted(agg):
            a = agg[w]
            out.append(dict(week=w, month=iso(_ms(to_date(w))), scheduled_hours=R2(a['sched']), planned_hours=R2(a['plan']), cover_hours=R2(a['cov']), uncovered_hours=R2(a['unc']),
                            delivered_hours=R2(a['deliv']), billed_hours=R2(a['billed']), paid_hours=R2(a['paid']), visits=int(a['visits']), late_visits=int(a['late']), missed_visits=int(a['missed'])))
        for i, x in enumerate(out, 1): x['row_id'] = 'WK-%03d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('wk', f), n)


def mileage_rows(n=None):
    def f():
        out = []
        for v in _vall():
            if v['distance_km'] > 0 and v['status'] in ('Completed', 'Late'):
                out.append(dict(date=v['date'], week=v['week'], month=v['month'], caregiver_id=v['caregiver_id'], caregiver=v['caregiver'], client_id=v['client_id'], client=v['client'],
                                from_area=v['from_area'], to_area=v['area'], distance_km=v['distance_km'], travel_min=v['travel_min'], travel_pay=v['travel_pay'], mileage_amount=v['mileage_pay']))
        for i, x in enumerate(out, 1): x['mileage_id'] = 'MG-%05d' % i
        return [dict(mileage_id=x.pop('mileage_id'), **x) for x in out]
    return _thin(_cached('mg', f), n)


# ------------------------------------------------------------------ payroll
def payroll_rows(n=None):
    def f():
        W = _W(); cm = _cmap(); r = rng('payroll'); W0 = week_start(TODAY) - day(14 * ((week_start(TODAY) - W['W0']).days // 14 + 1)); agg = {}
        for v in W['visits']:
            if v['status'] not in ('Completed', 'Late'): continue
            k = ((v['_d'] - W0).days // 14, v['actual']); a = agg.setdefault(k, defaultdict(float))
            h = v['actual_hours']; a['h'] += h; a['t'] += v['travel_min'] / 60.0; a['ot'] += v.get('_ot_share', 0.0)
            if v['band'] == 'Holiday': a['hh'] += h
            a['pay'] += v['pay']; a['hp'] += v['holiday_premium']; a['otp'] += v['overtime_pay']; a['tp'] += v['travel_pay']; a['mp'] += v['mileage_pay']; a['cp'] += v['cover_premium']
            a['km'] += v['distance_km']
        bonus = {}
        for g in W['cgs']:
            if g['source'] == 'Caregiver referral' and (g['_left'] is None or (g['_left'] - g['_hire']).days > 95) and (TODAY - g['_hire']).days > 100:
                bonus[(((g['_hire'] + day(91)) - W0).days // 14, g['caregiver_id'])] = 100.0
        out = []
        for (p, gid), a in sorted(agg.items()):
            ps = W0 + day(14 * p); pe = ps + day(13); pd = pe + day(8)
            status = 'Paid' if pd <= TODAY else ('Due' if pe < TODAY else 'Accruing')
            tot = a['h'] + a['t']; ot = min(a['ot'], tot)
            reg_pay = R2(a['pay'] - a['hp']); b = 0.0
            b = bonus.get((p, gid), 0.0)
            ded = float(r.choice([20, 30, 45])) if r.random() < 0.06 else 0.0
            gross = R2(reg_pay + a['otp'] + a['hp'] + a['tp'] + a['mp'] + a['cp'] + b)
            bur = R2(PAYROLL_BURDEN * (gross - a['mp']))
            out.append(dict(period_start=iso(ps), period_end=iso(pe), pay_date=iso(pd), month=iso(_ms(pe)), caregiver_id=gid, caregiver=cm[gid]['name'], employment=cm[gid]['employment'],
                            regular_hours=R2(tot - ot - a['hh']), overtime_hours=R2(ot), holiday_hours=R2(a['hh']), travel_hours=R2(a['t']), distance_km=R2(a['km']), regular_pay=reg_pay,
                            overtime_pay=R2(a['otp']), holiday_premium=R2(a['hp']), travel_pay=R2(a['tp']), mileage_pay=R2(a['mp']), cover_premium=R2(a['cp']), bonus=b, deductions=ded,
                            gross_pay=gross, net_pay=R2(gross - ded), burden=bur, total_cost=R2(gross + bur), status=status))
        for i, x in enumerate(out, 1): x['pay_id'] = 'PR-%04d' % i
        return [dict(pay_id=x.pop('pay_id'), **x) for x in out]
    return _thin(_cached('pr', f), n)


# ------------------------------------------------------------------ enquiries and agreements
def _enq():
    def f():
        W = _W(); r = rng('enq'); cm = _cmap(); out = []
        sup = FIELD_SUPERVISORS
        def base(recv, svc, area, hrs, src, nm, i):
            return dict(received_on=recv, first_reply_hours=r.choice([1, 1, 2, 2, 3, 4, 6, 8, 12, 20, 30, 48]), name=nm, phone=fake_phone(500 + i), source=src, area=area, service=svc,
                        hours_week=float(hrs), handled_by=r.choice([SCHEDULER, SCHEDULER, OFFICE_MANAGER, OWNER]), assessor='', assessment_on='', agreement_on='', first_visit_on='',
                        client_id='', status='', loss_reason='', quote_weekly=0.0)
        k = 0
        for c in W['cls']:
            if c['_start'] < HISTORY_START + day(26): continue
            k += 1; lead = r.randint(6, 24); recv = c['_start'] - day(lead)
            e = base(recv, c['service'], c['area'], c['weekly_hours'], c['source'], c['client'], k)
            asm = recv + day(r.randint(2, 5)); e.update(assessor=r.choice(sup), assessment_on=iso(asm), agreement_on=iso(min(c['_start'] - day(1), asm + day(r.randint(1, 4)))),
                                                         first_visit_on=iso(c['_start']), client_id=c['client_id'], status='Started', quote_weekly=R2(c['weekly_hours'] * c['bill_rate']))
            out.append(e)
        # lost enquiries, with a peak in January-March and September-October
        n_lost = 150; days = []
        while len(days) < n_lost:
            d = HISTORY_START + day(r.randint(0, HISTORY_DAYS - 12))
            w = 1.6 if d.month in (1, 2, 3, 9, 10) else 1.0
            if r.random() < w / 1.6: days.append(d)
        for d in days:
            k += 1; svc = _wchoice(r, SERVICES[:5], [0.38, 0.28, 0.12, 0.1, 0.12]); hrs = r.choice([6, 8, 10, 12, 16, 20, 24])
            e = base(d, svc, _wchoice(r, AREAS, _AREA_W_CL), hrs, _wchoice(r, ENQ_SOURCES, [0.24, 0.2, 0.14, 0.14, 0.1, 0.1, 0.08]), r.choice(_FIRST) + ' ' + r.choice(_LAST), k)
            rs = _wchoice(r, LOSS_REASONS, [0.26, 0.2, 0.16, 0.2, 0.12, 0.06])
            e.update(status='Lost', loss_reason=rs, quote_weekly=R2(hrs * BASE_BILL[svc]))
            if rs not in ('No reply',) and r.random() < 0.55: e.update(assessor=r.choice(sup), assessment_on=iso(d + day(r.randint(2, 6))))
            out.append(e)
        # open enquiries this fortnight
        for ago_d, st in [(0, 'New'), (3, 'New'), (5, 'New'), (2, 'Assessment booked'), (6, 'Assessment booked'), (9, 'Agreement sent'), (11, 'Agreement sent'), (13, 'Agreement sent')]:
            k += 1; svc = r.choice(SERVICES[:4]); hrs = r.choice([8, 12, 16, 20]); d = TODAY - day(ago_d)
            e = base(d, svc, _wchoice(r, AREAS, _AREA_W_CL), hrs, _wchoice(r, ENQ_SOURCES, [0.24, 0.2, 0.14, 0.14, 0.1, 0.1, 0.08]), r.choice(_FIRST) + ' ' + r.choice(_LAST), k)
            e.update(status=st, quote_weekly=R2(hrs * BASE_BILL[svc]))
            if st == 'New': e['first_reply_hours'] = 0 if ago_d == 0 else e['first_reply_hours']
            if st != 'New': e.update(assessor=r.choice(sup), assessment_on=iso(d + day(min(ago_d, 3))))
            if st == 'Agreement sent': e['agreement_on'] = ''
            out.append(e)
        out.sort(key=lambda e: (e['received_on'], e['name']))
        for i, e in enumerate(out, 1): e['enquiry_id'] = 'EN-%04d' % i; e['received_on'] = iso(e['received_on']); e['month'] = iso(_ms(to_date(e['received_on'])))
        return [dict(enquiry_id=e.pop('enquiry_id'), **e) for e in out]
    return _raw('enq', f)


def enquiry_rows(n=None): return _thin([dict(x) for x in _enq()], n)


def agreement_rows(n=None):
    def f():
        W = _W(); r = rng('agr'); out = []
        for c in W['cls']:
            out.append(dict(client_id=c['client_id'], client=c['client'], kind='Original', sent_on=iso(c['_start'] - day(3)), signed_on=iso(c['_start'] - day(1)), weekly_hours=float(c['weekly_hours']),
                            bill_rate=_bill_rate(c, c['service'], 'Weekday', c['_start']), min_visit_hours=c['min_visit_hours'], notice_days=2, deposit=c['deposit'],
                            status='Ended' if c['_end'] else 'Signed'))
            if not c['_end'] and not c['rate_locked'] and c['_start'] < D(TODAY.year - 1, 12, 1):
                sd = D(TODAY.year - 1, 12, 1) + day(r.randint(0, 18))
                out.append(dict(client_id=c['client_id'], client=c['client'], kind='Rate update', sent_on=iso(sd - day(30)), signed_on=iso(sd), weekly_hours=float(c['weekly_hours']),
                                bill_rate=c['bill_rate'], min_visit_hours=c['min_visit_hours'], notice_days=2, deposit=c['deposit'], status='Signed'))
        act = [c for c in W['cls'] if not c['_end'] and (TODAY - c['_start']).days > 120]
        for c in r.sample(act, 9):
            sd = TODAY - day(r.randint(20, 100))
            out.append(dict(client_id=c['client_id'], client=c['client'], kind='Hours change', sent_on=iso(sd - day(3)), signed_on=iso(sd), weekly_hours=float(c['weekly_hours']),
                            bill_rate=c['bill_rate'], min_visit_hours=c['min_visit_hours'], notice_days=2, deposit=c['deposit'], status='Signed'))
        for e in _enq():
            if e['status'] == 'Agreement sent':
                out.append(dict(client_id='', client=e['name'], kind='Original', sent_on=iso(to_date(e['received_on']) + day(3)), signed_on='', weekly_hours=e['hours_week'],
                                bill_rate=R2(BASE_BILL[e['service']]), min_visit_hours=MIN_VISIT[e['service']], notice_days=2, deposit=0.0, status='Sent'))
        out.sort(key=lambda x: (x['sent_on'], x['client']))
        for i, x in enumerate(out, 1): x['agreement_id'] = 'SA-%03d' % i
        return [dict(agreement_id=x.pop('agreement_id'), **x) for x in out]
    return _thin(_cached('agr', f), n)

# ------------------------------------------------------------------ invoices, payments, claims, deposits
def _accounts():
    def f():
        W = _W(); r = rng('acct'); W0 = W['W0']; cl = {c['client_id']: c for c in W['cls']}
        groups = {}
        for v in W['visits']:
            if v['status'] not in ('Completed', 'Late') or v['charge'] <= 0: continue
            c = v['_c']; d = v['_d']; cy = c['billing_cycle']
            if cy == 'Weekly': ps = week_start(d); pe = ps + day(6); iss = ps + day(7)
            elif cy == 'Bi-weekly': b = (d - W0).days // 14; ps = W0 + day(14 * b); pe = ps + day(13); iss = ps + day(14)
            else: ps = _ms(d); pe = _eom(d); iss = pe + day(1)
            if iss > TODAY: continue
            g = groups.setdefault((c['client_id'], ps), dict(c=c, ps=ps, pe=pe, iss=iss, hours=0.0, amount=0.0))
            g['hours'] += v['billed_hours']; g['amount'] += v['charge']
        invs = sorted(groups.values(), key=lambda g: (g['iss'], g['c']['client_id']))
        last_inv = {}
        for g in invs: last_inv[g['c']['client_id']] = g
        payments = []; claims = []; out = []
        wo_clients = [c for c in W['cls'] if c['_end'] and c['payer'] == 'Private pay' and not c['prepay'] and (TODAY - c['_end']).days > 150 and last_inv.get(c['client_id'])][:2]
        wo_ids = {id(last_inv[c['client_id']]) for c in wo_clients}
        bal = {}; topups = defaultdict(list)
        low_client = None
        pp = [c for c in W['cls'] if c['prepay'] and not c['_end']]
        if pp: low_client = pp[-1]['client_id']
        for g in invs:
            c = g['c']; amt = R2(g['amount']); cid = c['client_id']
            inv = dict(client_id=cid, client=c['client'], payer=c['payer'], cycle=c['billing_cycle'], period_start=iso(g['ps']), period_end=iso(g['pe']), issued_on=iso(g['iss']),
                       due_date=iso(g['iss'] + day(INVOICE_DAYS)), month=iso(_ms(g['iss'])), hours=R2(g['hours']), amount=amt, deposit_applied=0.0, paid_amount=0.0, paid_on='',
                       paid_by='', written_off=0.0, status='Unpaid', days_to_pay='')
            if c['payer'] != 'Private pay':
                pr = next(p for p in payers if p['payer'] == c['payer'])
                sub = g['iss'] + day(r.randint(1, 3)); delay = max(16, pr['pay_days'] + r.randint(-8, 10)); x = r.random()
                cl_ = dict(client_id=cid, client=c['client'], payer=c['payer'], month=iso(_ms(g['pe'])), hours=inv['hours'], billed_amount=amt, submitted_on=sub, paid_on=None,
                           paid_amount=0.0, short_amount=0.0, reason='', resubmitted_on=None, status='Submitted', _inv=inv)
                if x < 0.78: cl_.update(paid_on=sub + day(delay), paid_amount=amt)
                elif x < 0.90:
                    pa = R2(amt * r.uniform(0.86, 0.95)); cl_.update(paid_on=sub + day(delay), paid_amount=pa, short_amount=R2(amt - pa), reason=r.choice(['Hours mismatch', 'Rate difference']))
                elif x < 0.97:
                    rs = _wchoice(r, CLAIM_REASONS, [0.2, 0.3, 0.3, 0.1, 0.1]); rsub = sub + day(r.randint(6, 14))
                    cl_.update(reason=rs, resubmitted_on=rsub, paid_on=rsub + day(r.randint(28, 40)), paid_amount=amt)
                else:
                    if (TODAY - sub).days > 120: cl_.update(reason='Late submission', status='Written off')
                    else: cl_.update(paid_on=sub + day(delay), paid_amount=amt)
                claims.append(cl_)
                continue
            if id(g) in wo_ids:
                inv.update(written_off=amt, status='Written off'); out.append(inv); continue
            if c['prepay']:
                wk = c['weekly_hours'] * c['bill_rate']
                b0 = bal.get(cid, 0.0)
                if b0 < amt + wk:
                    need = (amt - b0 + 0.4 * wk) if cid == low_client else (amt + 3 * wk - b0)
                    tu = float(int((need + 49) // 50 * 50)); payments.append(dict(date=g['iss'] - day(2), client_id=cid, client=c['client'], kind='Prepayment', method=r.choice(PAYMENT_METHODS[:2]), amount=tu, invoice_id=''))
                    topups[cid].append((g['iss'] - day(2), tu)); b0 += tu
                bal[cid] = b0 - amt
                inv.update(paid_amount=amt, paid_on=iso(g['iss']), paid_by='Prepaid balance', status='Paid', days_to_pay=0); out.append(inv); continue
            dep = 0.0
            if c['_end'] and last_inv.get(cid) is g and c['deposit'] > 0: dep = min(c['deposit'], amt); inv['deposit_applied'] = dep
            due_amt = R2(amt - dep)
            story_unpaid = c['_special'] == 'overdue' and g['iss'] > TODAY - day(90)
            delay = r.choice([3, 5, 7, 8, 9, 11, 12, 14]) + (r.choice([0, 0, 0, 10, 20]) if (c['_i'] % 5 == 0) else 0)
            delay = min(delay, 55)
            if story_unpaid: delay = 400
            pd = g['iss'] + day(delay)
            if pd <= TODAY:
                m = r.choice(PAYMENT_METHODS)
                inv.update(paid_amount=due_amt, paid_on=iso(pd), paid_by=m, status='Paid', days_to_pay=delay)
                if due_amt > 0: payments.append(dict(date=pd, client_id=cid, client=c['client'], kind='Invoice payment', method=m, amount=due_amt, invoice_id=''))
            elif not story_unpaid and 10 <= (TODAY - g['iss']).days <= 40 and r.random() < 0.15:
                part = R2(due_amt * r.uniform(0.5, 0.7)); pd2 = g['iss'] + day(8); m = r.choice(PAYMENT_METHODS)
                inv.update(paid_amount=part, paid_on=iso(pd2), paid_by=m, status='Part paid')
                payments.append(dict(date=pd2, client_id=cid, client=c['client'], kind='Invoice payment', method=m, amount=part, invoice_id=''))
            out.append(inv)
        # claims: force two rejected and not yet resubmitted
        forced = 0
        for cl_ in claims:
            if forced < 2 and TODAY - day(45) <= cl_['submitted_on'] <= TODAY - day(20) and cl_['payer'] != 'Private pay':
                cl_.update(status='Rejected', reason=r.choice(['Missing details', 'Authorisation missing']), paid_on=None, paid_amount=0.0, short_amount=0.0, resubmitted_on=None); forced += 1
        for cl_ in claims:
            inv = cl_['_inv']
            if cl_['status'] == 'Written off': inv.update(written_off=cl_['billed_amount'], status='Written off'); out.append(inv); continue
            po = cl_['paid_on']
            if po is not None and po <= TODAY:
                cl_['status'] = 'Short-paid' if cl_['short_amount'] > 0 else 'Paid'
                if (TODAY - po).days > 45 and cl_['short_amount'] > 0:
                    inv.update(paid_amount=cl_['paid_amount'], paid_on=iso(po), paid_by='Payer payment', written_off=cl_['short_amount'], status='Paid', days_to_pay=(po - to_date(inv['issued_on'])).days)
                else:
                    inv.update(paid_amount=cl_['paid_amount'], paid_on=iso(po), paid_by='Payer payment', status='Paid' if cl_['short_amount'] == 0 else 'Part paid', days_to_pay=(po - to_date(inv['issued_on'])).days)
                payments.append(dict(date=po, client_id=cl_['client_id'], client=cl_['client'], kind='Payer payment', method='Bank transfer', amount=cl_['paid_amount'], invoice_id=''))
            else:
                cl_['paid_on'] = None; cl_['paid_amount'] = 0.0; cl_['short_amount'] = 0.0
                if cl_['status'] != 'Rejected':
                    ru = cl_['resubmitted_on']
                    if ru is not None and ru <= TODAY: cl_['status'] = 'Resubmitted'
                    elif ru is not None: cl_['status'] = 'Rejected'; cl_['resubmitted_on'] = None
                    else: cl_['status'] = 'Submitted' if (TODAY - cl_['submitted_on']).days <= 14 else 'Accepted'
                    if cl_['status'] != 'Resubmitted' and cl_['status'] not in ('Rejected',): cl_['reason'] = ''
                cl_['resubmitted_on'] = cl_['resubmitted_on'] if cl_['status'] == 'Resubmitted' else None
            out.append(inv)
        out.sort(key=lambda x: (x['issued_on'], x['client_id']))
        for i, x in enumerate(out, 1): x['invoice_id'] = 'IV-%04d' % i
        invmap = {(x['client_id'], x['period_start']): x['invoice_id'] for x in out}
        claims.sort(key=lambda x: (x['submitted_on'], x['client_id']))
        for i, x in enumerate(claims, 1):
            x['claim_id'] = 'CP-%04d' % i; x['invoice_id'] = x['_inv']['invoice_id']
        # deposits and prepaid balances
        deps = []
        for c in W['cls']:
            if c['payer'] != 'Private pay': continue
            cid = c['client_id']
            if c['prepay']:
                tl = topups.get(cid, [])
                if not tl: continue
                tot = sum(a for _, a in tl); b0 = bal.get(cid, 0.0)
                deps.append(dict(client_id=cid, client=c['client'], kind='Prepayment', received_on=iso(tl[0][0]), amount=tot, used=R2(tot - b0), balance=R2(b0), weekly_bill=R2(c['weekly_hours'] * c['bill_rate']),
                                 status='Refunded' if c['_end'] else 'Held'))
            elif c['deposit'] > 0:
                st = 'Held'
                if c['_end']: st = 'Applied' if last_inv.get(cid) and c['deposit'] <= R2(last_inv[cid]['amount']) else 'Refunded'
                deps.append(dict(client_id=cid, client=c['client'], kind='Deposit', received_on=iso(c['_start'] - day(2)), amount=c['deposit'], used=c['deposit'] if st == 'Applied' else 0.0,
                                 balance=c['deposit'] if st == 'Held' else 0.0, weekly_bill=R2(c['weekly_hours'] * c['bill_rate']), status=st))
                if c['_start'] - day(2) >= HISTORY_START:
                    payments.append(dict(date=c['_start'] - day(2), client_id=cid, client=c['client'], kind='Deposit', method=r.choice(PAYMENT_METHODS), amount=c['deposit'], invoice_id=''))
        deps.sort(key=lambda x: (x['received_on'], x['client_id']))
        for i, x in enumerate(deps, 1): x['deposit_id'] = 'DP-%03d' % i
        payments.sort(key=lambda x: (x['date'], x['client_id']))
        for i, x in enumerate(payments, 1): x['payment_id'] = 'PM-%05d' % i; x['date'] = iso(x['date'])
        return dict(invoices=out, claims=claims, payments=payments, deposits=deps)
    return _raw('acct', f)


def invoice_rows(n=None): return _thin([dict(x) for x in _accounts()['invoices']], n)
def payment_rows(n=None): return _thin([dict(x) for x in _accounts()['payments']], n)
def deposit_rows(n=None): return _thin([dict(x) for x in _accounts()['deposits']], n)


def claim_rows(n=None):
    def f():
        out = []
        for x in _accounts()['claims']:
            out.append(dict(claim_id=x['claim_id'], invoice_id=x['invoice_id'], client_id=x['client_id'], client=x['client'], payer=x['payer'], month=x['month'], hours=x['hours'],
                            billed_amount=x['billed_amount'], submitted_on=iso(x['submitted_on']), status=x['status'], reason=x['reason'],
                            resubmitted_on=iso(x['resubmitted_on']) if x['resubmitted_on'] else '', paid_on=iso(x['paid_on']) if x['paid_on'] else '', paid_amount=x['paid_amount'],
                            short_amount=x['short_amount'], days_to_pay=(x['paid_on'] - x['submitted_on']).days if x['paid_on'] else ''))
        return out
    return _thin(_cached('claims', f), n)


# ------------------------------------------------------------------ recruiting, onboarding, credentials
APPLICANT_REASONS = ['No reply', 'Hours do not fit', 'Pay too low', 'Check not passed', 'Took another job', 'Not a fit']


def applicant_rows(n=None):
    def f():
        W = _W(); r = rng('appl'); out = []; k = 0
        for g in W['cgs']:
            if (TODAY - g['_hire']).days > HISTORY_DAYS - 10: continue
            k += 1; h = g['_hire']; ap = h - day(r.randint(14, 35)); ps = ap + day(r.randint(1, 4)); iv = ps + day(r.randint(3, 8)); of = iv + day(r.randint(1, 3))
            out.append(dict(name=g['name'], phone=g['phone'], applied_on=ap, source=g['source'], phone_screen_on=ps, interview_on=iv, offer_on=of, start_on=h, status='Started',
                            reason='', caregiver_id=g['caregiver_id']))
        for sd, nm in [(5, 'Carmela Ortega'), (9, 'Gideon Afolabi')]:
            k += 1; h = TODAY + day(sd); ap = h - day(24)
            out.append(dict(name=nm, phone=fake_phone(700 + sd), applied_on=ap, source='Caregiver referral' if sd == 5 else 'Online job board', phone_screen_on=ap + day(3), interview_on=ap + day(9),
                            offer_on=ap + day(12), start_on=h, status='Onboarding', reason='', caregiver_id=''))
        names = [f + ' ' + l for f, l in zip(r.sample(_FIRST, 60), r.sample(_LAST, 60))]
        n_lost = 215
        for i in range(n_lost):
            d = HISTORY_START + day(r.randint(0, HISTORY_DAYS - 3))
            recent = i < 22
            if recent: d = TODAY - day(r.randint(0, 21))
            nm = names[i % 60] + (' ' if i >= 60 else '')
            if i >= 60: nm = r.choice(_FIRST) + ' ' + r.choice(_LAST)
            src = _wchoice(r, REC_SOURCES, [0.35, 0.15, 0.15, 0.1, 0.12, 0.08, 0.05])
            stage = _wchoice(r, [0, 1, 2, 3], [0.22, 0.42, 0.26, 0.10])
            e = dict(name=nm, phone=fake_phone(800 + i), applied_on=d, source=src, phone_screen_on='', interview_on='', offer_on='', start_on='', status='Applied', reason='', caregiver_id='')
            if recent:
                age = (TODAY - d).days; stage = 0 if age < 3 else (1 if age < 8 else (2 if age < 14 else 3))
                if stage >= 3 and r.random() < 0.7: stage = 2
            if stage >= 1: e['phone_screen_on'] = d + day(r.randint(1, 4))
            if stage >= 2: e['interview_on'] = e['phone_screen_on'] + day(r.randint(3, 8))
            if stage >= 3: e['offer_on'] = e['interview_on'] + day(r.randint(1, 3))
            names_ = ['Applied', 'Phone screen', 'Interview', 'Offer']
            if recent: e['status'] = names_[stage]
            else:
                e['status'] = 'Withdrawn' if (stage == 3 or r.random() < 0.3) else 'Not selected'
                e['reason'] = r.choice(APPLICANT_REASONS) if e['status'] == 'Not selected' else r.choice(['Hours do not fit', 'Pay too low', 'Took another job', 'No reply'])
            out.append(e)
        out.sort(key=lambda e: (e['applied_on'], e['name']))
        for i, e in enumerate(out, 1):
            e['applicant_id'] = 'AP-%04d' % i
            for kx in ('applied_on', 'phone_screen_on', 'interview_on', 'offer_on', 'start_on'): e[kx] = iso(e[kx]) if e[kx] != '' else ''
            e['month'] = iso(_ms(to_date(e['applied_on'])))
        return [dict(applicant_id=e.pop('applicant_id'), **e) for e in out]
    return _thin(_cached('appl', f), n)


def onboarding_rows(n=None):
    def f():
        W = _W(); r = rng('onb'); out = []
        for g in W['cgs']:
            ag = (TODAY - g['_hire']).days
            if ag > 365: continue
            h = g['_hire']
            def dd(k): x = h + day(k); return iso(x) if x <= TODAY else ''
            out.append(dict(person=g['name'], caregiver_id=g['caregiver_id'], start_date=iso(h), identity_check_on=dd(-r.randint(3, 10)), references_on=dd(-r.randint(2, 8)),
                            background_check_on=dd(-r.randint(1, 7)), training_on=dd(r.randint(-3, 3)), agreement_signed_on=dd(-r.randint(1, 3)), first_shift_on=dd(r.randint(4, 9)), owner=RECRUITER))
        for sd, nm, done in [(5, 'Carmela Ortega', 2), (9, 'Gideon Afolabi', 1)]:
            h = TODAY + day(sd)
            out.append(dict(person=nm, caregiver_id='', start_date=iso(h), identity_check_on=ago(4) if done >= 1 else '', references_on=ago(2) if done >= 2 else '', background_check_on='',
                            training_on='', agreement_signed_on='', first_shift_on='', owner=RECRUITER))
        out.sort(key=lambda x: x['start_date'])
        for i, x in enumerate(out, 1):
            x['onboarding_id'] = 'OB-%03d' % i
            x['steps_done'] = sum(1 for k in ('identity_check_on', 'references_on', 'background_check_on', 'training_on', 'agreement_signed_on') if x[k])
            x['ready'] = x['steps_done'] == 5
        return [dict(onboarding_id=x.pop('onboarding_id'), **x) for x in out]
    return _thin(_cached('onb', f), n)


def _cred_caregiver():
    """the active caregiver with the most scheduled hours in the next two weeks (not a pinned story caregiver), hired inside the window"""
    def f():
        cnt = defaultdict(float)
        for v in _W()['visits']:
            if v['_d'] > TODAY and v['actual']: cnt[v['actual']] += v['_hrs']
        cm = _cmap()
        c = [(h, gid) for gid, h in cnt.items() if cm[gid]['employment'] == 'Hourly' and not cm[gid]['_left'] and gid not in ('CG-006', 'CG-009') and (TODAY - cm[gid]['_hire']).days < HISTORY_DAYS]
        c.sort(reverse=True)
        return c[1][1] if len(c) > 1 else c[0][1]
    return _raw('credcg', f)


def credential_rows(n=None):
    def f():
        W = _W(); r = rng('cred'); cm = _cmap(); out = []; months = dict(zip(CRED_TYPES, [36, 12, 24, 12, 12, 24]))
        U = _cred_caregiver()
        amber = 0
        for g in W['cgs']:
            if g['_left']: continue
            types = CRED_TYPES[:3] + (CRED_TYPES[3:5] if g['drives'] else []) + ([CRED_TYPES[5]] if r.random() < 0.25 else [])
            for t in types:
                m = months[t]; exp_days = int(46 + r.random() * (m * 30 - 46))
                if g['caregiver_id'] == U and t == 'First aid course': exp_days = 10
                elif amber < 5 and r.random() < 0.06: exp_days = r.randint(47, 59); amber += 1
                exp = TODAY + day(exp_days); iss = exp - day(int(m * 30.4))
                out.append(dict(caregiver_id=g['caregiver_id'], caregiver=g['name'], credential=t, issued_on=iso(iss), expires_on=iso(exp), renewed_on='', status='Valid', reminder_sent=exp_days <= RENEWAL_WARN_DAYS))
                if iss - day(60) > g['_hire'] - day(400) and (iss - g['_hire']).days > 30:
                    pe = iss
                    out.append(dict(caregiver_id=g['caregiver_id'], caregiver=g['name'], credential=t, issued_on=iso(pe - day(int(m * 30.4))), expires_on=iso(pe), renewed_on=iso(pe - day(r.randint(5, 30))),
                                    status='Renewed', reminder_sent=True))
        out.sort(key=lambda x: (x['caregiver_id'], x['credential'], x['expires_on']))
        for i, x in enumerate(out, 1): x['credential_id'] = 'CR-%03d' % i
        return [dict(credential_id=x.pop('credential_id'), **x) for x in out]
    return _thin(_cached('cred', f), n)


# ------------------------------------------------------------------ expenses, profit and loss, cash, tax, marketing
def _months24(): return [month_start(k) for k in range(23, -1, -1)]


def expense_rows(n=None):
    def f():
        r = rng('exp'); out = []; hires = defaultdict(int)
        for g in _W()['cgs']: hires[_ms(g['_hire'])] += 1
        apps = defaultdict(int)
        for a in applicant_rows(): apps[to_date(a['month'])] += 1
        yrnew = D(TODAY.year, 1, 1)
        for m in _months24():
            eom = _eom(m); last = min(eom, TODAY)
            def add(cat, day_, amt, who):
                dd = m + day(day_ - 1)
                if dd > TODAY or amt <= 0: return
                out.append(dict(date=iso(dd), month=iso(m), category=cat, vendor=who, amount=R2(amt)))
            add('Office rent', 1, 3200 if m >= yrnew else 3000, 'Olumide Bakare')
            sal = 4300 + 4800
            if (TODAY - m).days < 420: sal += 26 * 86
            add('Office payroll', 28, sal * (1 + PAYROLL_BURDEN), 'Payroll')
            sup = 3900 + (3800 if (TODAY - m).days < 270 else 0)
            add('Field supervisor pay', 28, sup * (1 + PAYROLL_BURDEN), 'Payroll')
            add('Software and phones', 5, 900 + 12 * (23 - (TODAY.year * 12 + TODAY.month - m.year * 12 - m.month)) + r.randint(-40, 40), 'Nadia Petrova')
            add('Business insurance', 3, 1250 + r.randint(-30, 30) + (120 if m >= yrnew else 0), 'Rosa Bianchi')
            add('Marketing', 12, 500 + r.randint(0, 600), 'Yuki Tanaka')
            add('Recruiting ads', 9, HIRE_AD_COST * max(1, apps[m] // 6) + r.randint(0, 80), 'Online job board')
            add('Background checks', 14, BACKGROUND_CHECK_COST * max(1, hires[m] * 2), 'Dmitri Volkov')
            add('Training courses', 18, 350 + 300 * hires[m] + r.randint(0, 250), 'Leila Haddad')
            add('Office supplies', 20, 200 + r.randint(0, 220), 'Kwame Boateng')
            add('Accounting fees', 25, 700 + 12 * (23 - (TODAY.year * 12 + TODAY.month - m.year * 12 - m.month)) + r.randint(0, 120), 'Henrik Larsen')
            add('Bank and card fees', 26, 260 + r.randint(0, 220), 'Bank')
            add('Professional fees', 22, r.choice([0, 0, 150, 300, 450]), 'Henrik Larsen')
            add('Uniforms and supplies', 16, 150 + 110 * hires[m] + r.randint(0, 120), 'Kwame Boateng')
        for i, x in enumerate(out, 1): x['expense_id'] = 'EX-%04d' % i
        return [dict(expense_id=x.pop('expense_id'), **x) for x in out]
    return _thin(_cached('exp', f), n)


def pnl_rows(n=None):
    """one row per month (24): revenue and caregiver costs from the visits, office overhead from the expenses, profit before owner draw and tax"""
    def f():
        agg = {m: defaultdict(float) for m in _months24()}
        for v in _W()['visits']:
            m = _ms(v['_d'])
            if m not in agg or v['status'] not in ('Completed', 'Late'): continue
            a = agg[m]; a['rev'] += v['charge']; a['bh'] += v['billed_hours']; a['dh'] += v['actual_hours']; a['pay'] += v['pay'] + v['cover_premium']; a['ot'] += v['overtime_pay']
            a['tr'] += v['travel_pay']; a['mi'] += v['mileage_pay']; a['bu'] += v['burden']; a['cost'] += v['cost']; a['hp'] += v['holiday_premium']
        oh = defaultdict(float)
        for e in expense_rows(): oh[to_date(e['month'])] += e['amount']
        out = []
        for m in _months24():
            a = agg[m]; gm = a['rev'] - a['cost']
            out.append(dict(month=iso(m), revenue=R2(a['rev']), billed_hours=R2(a['bh']), caregiver_pay=R2(a['pay']), overtime_pay=R2(a['ot']), travel_pay=R2(a['tr']), mileage_pay=R2(a['mi']),
                            payroll_burden=R2(a['bu']), direct_cost=R2(a['cost']), gross_margin=R2(gm), gross_margin_pct=round(gm / a['rev'], 4) if a['rev'] else 0.0, overhead=R2(oh[m]),
                            profit=R2(gm - oh[m])))
        for i, x in enumerate(out, 1): x['row_id'] = 'PL-%02d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('pnl', f), n)


def tax_rows(n=None):
    def f():
        out = []
        for i, p in enumerate(pnl_rows()):
            m = to_date(p['month']); sa = R2(max(0.0, p['profit']) * TAX_SET_ASIDE_PCT)
            st = 'Moved' if m < month_start(1) else ('Due' if m == month_start(1) else 'Upcoming')
            out.append(dict(tax_id='TX-%02d' % (i + 1), month=p['month'], profit=p['profit'], set_aside_pct=TAX_SET_ASIDE_PCT, set_aside=sa, status=st,
                            moved_on=iso(add_months(m, 1) + day(9)) if st == 'Moved' else ''))
        return out
    return _thin(_cached('tax', f), n)


def cash_rows(n=None):
    """the last 14 months of cash: money in from payments, money out for pay runs, expenses, owner draw and tax set-aside"""
    def f():
        pin = defaultdict(float); pout = defaultdict(float); ex = defaultdict(float)
        for p in payment_rows(): pin[_ms(to_date(p['date']))] += p['amount']
        for p in payroll_rows():
            if to_date(p['pay_date']) <= TODAY: pout[_ms(to_date(p['pay_date']))] += p['total_cost']
        for e in expense_rows():
            if e['category'] in ('Office payroll', 'Field supervisor pay') or True: ex[to_date(e['month'])] += e['amount']
        tx = {to_date(t['month']): t['set_aside'] for t in tax_rows()}
        ms = _months24(); flows = []; cum = 0.0; cums = []
        for m in ms:
            cin = pin[m]; cout = pout[m] + ex[m] + OWNER_DRAW + tx.get(add_months(m, -1), 0.0)
            flows.append((m, cin, cout)); cum += cin - cout; cums.append(cum)
        opening = CASH_FLOOR * 1.3 - min(cums[-14:])
        out = []; bal = opening
        for i, (m, cin, cout) in enumerate(flows):
            op = bal; bal = op + cin - cout
            if m >= month_start(13): out.append(dict(month=iso(m), opening=R2(op), cash_in=R2(cin), pay_runs=R2(pout[m]), expenses=R2(ex[m]), owner_draw=OWNER_DRAW, tax_set_aside=R2(tx.get(add_months(m, -1), 0.0)),
                                                       cash_out=R2(cout), closing=R2(bal), cash_floor=CASH_FLOOR))
        for i, x in enumerate(out, 1): x['row_id'] = 'CF-%02d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('cash', f), n)


def marketing_rows(n=None):
    def f():
        r = rng('mk'); out = []
        tg = {'Online job ad': 'Caregivers', 'Community flyers': 'Clients', 'Directory listing': 'Clients', 'Website': 'Clients', 'Partner visit': 'Clients',
              'Referral bonus': 'Caregivers', 'Local event': 'Clients'}
        for m in _months24():
            for k in r.sample(MARKETING_KINDS, 3):
                cost = {'Online job ad': 280, 'Community flyers': 180, 'Directory listing': 240, 'Website': 150, 'Partner visit': 90, 'Referral bonus': 100, 'Local event': 350}[k]
                cost = R2(cost * r.uniform(0.7, 1.4)); res = max(0, int(cost / (45.0 if tg[k] == 'Clients' else 28.0) * r.uniform(0.5, 1.4)))
                out.append(dict(month=iso(m), kind=k, target=tg[k], cost=cost, results=res, started=int(res * (0.22 if tg[k] == 'Clients' else 0.12) + r.random())))
        for i, x in enumerate(out, 1): x['campaign_id'] = 'MK-%03d' % i
        return [dict(campaign_id=x.pop('campaign_id'), **x) for x in out]
    return _thin(_cached('mk', f), n)


def client_month_rows(n=None):
    def f():
        agg = {}
        for v in _W()['visits']:
            if v['status'] not in ('Completed', 'Late', 'Missed', 'Cancelled') or v['_d'] > TODAY: continue
            k = (v['_c']['client_id'], _ms(v['_d'])); a = agg.setdefault(k, defaultdict(float)); a['visits'] += 1
            if v['status'] == 'Late': a['late'] += 1
            if v['status'] == 'Missed': a['missed'] += 1
            if v['status'] in ('Completed', 'Late'):
                a['bh'] += v['billed_hours']; a['dh'] += v['actual_hours']; a['rev'] += v['charge']; a['cost'] += v['cost']; a['tr'] += v['travel_pay'] + v['mileage_pay']; a['ot'] += v['overtime_pay']
                a.setdefault('_cg', set()); a['_cg'].add(v['actual'])
        cl = _clmap(); out = []
        for (cid, m), a in sorted(agg.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            if m < HISTORY_START: continue
            out.append(dict(month=iso(m), client_id=cid, client=cl[cid]['client'], service=cl[cid]['service'], payer=cl[cid]['payer'], area=cl[cid]['area'], visits=int(a['visits']),
                            billed_hours=R2(a['bh']), delivered_hours=R2(a['dh']), revenue=R2(a['rev']), cost=R2(a['cost']), travel_cost=R2(a['tr']), overtime_cost=R2(a['ot']), margin=R2(a['rev'] - a['cost']),
                            margin_pct=round((a['rev'] - a['cost']) / a['rev'], 4) if a['rev'] else 0.0, late_visits=int(a['late']), missed_visits=int(a['missed']),
                            caregivers=len(a.get('_cg', ()))))
        for i, x in enumerate(out, 1): x['row_id'] = 'CM-%04d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('cmr', f), n)


def service_month_rows(n=None):
    def f():
        agg = defaultdict(lambda: defaultdict(float))
        for v in _W()['visits']:
            if v['status'] not in ('Completed', 'Late'): continue
            m = _ms(v['_d'])
            if m < HISTORY_START: continue
            a = agg[(m, v['service'])]; a['bh'] += v['billed_hours']; a['rev'] += v['charge']; a['cost'] += v['cost']; a['v'] += 1
        out = []
        for (m, s), a in sorted(agg.items(), key=lambda kv: (kv[0][0], SERVICES.index(kv[0][1]))):
            out.append(dict(month=iso(m), service=s, visits=int(a['v']), billed_hours=R2(a['bh']), revenue=R2(a['rev']), cost=R2(a['cost']), margin=R2(a['rev'] - a['cost']),
                            margin_pct=round((a['rev'] - a['cost']) / a['rev'], 4) if a['rev'] else 0.0))
        for i, x in enumerate(out, 1): x['row_id'] = 'SM-%04d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('smr', f), n)


def area_month_rows(n=None):
    def f():
        agg = defaultdict(lambda: defaultdict(float))
        for v in _W()['visits']:
            if v['_d'] > TODAY or v['status'] not in ('Completed', 'Late', 'Missed'): continue
            m = _ms(v['_d'])
            if m < HISTORY_START: continue
            a = agg[(m, v['_c']['area'])]; a['v'] += 1; a['late'] += v['status'] == 'Late'; a['miss'] += v['status'] == 'Missed'; a['h'] += v['actual_hours']; a['tm'] += v['travel_min']
        out = []
        for (m, ar), a in sorted(agg.items(), key=lambda kv: (kv[0][0], AREAS.index(kv[0][1]))):
            out.append(dict(month=iso(m), area=ar, visits=int(a['v']), late_visits=int(a['late']), missed_visits=int(a['miss']), delivered_hours=R2(a['h']), travel_min=int(a['tm']),
                            late_rate=round(a['late'] / a['v'], 4), missed_rate=round(a['miss'] / a['v'], 4)))
        for i, x in enumerate(out, 1): x['row_id'] = 'AM-%03d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('amr', f), n)


def growth_rows(n=None):
    def f():
        cls = _W()['cls']; out = []
        for m in _months24():
            e = _eom(m)
            st = [c for c in cls if m <= c['_start'] <= e]; en = [c for c in cls if c['_end'] and m <= c['_end'] <= e]
            act0 = [c for c in cls if c['_start'] < m and (not c['_end'] or c['_end'] >= m)]
            act1 = [c for c in cls if c['_start'] <= e and (not c['_end'] or c['_end'] > e)]
            hs = sum(c['weekly_hours'] for c in st); he = sum(c['weekly_hours'] for c in en)
            out.append(dict(month=iso(m), clients_started=len(st), clients_ended=len(en), hours_added=float(hs), hours_lost=float(he), net_hours=float(hs - he), active_clients=len(act1),
                            weekly_hours_end=float(sum(c['weekly_hours'] for c in act1)), churn_rate=round(len(en) / len(act0), 4) if act0 else 0.0))
        for i, x in enumerate(out, 1): x['row_id'] = 'GR-%02d' % i
        return [dict(row_id=x.pop('row_id'), **x) for x in out]
    return _thin(_cached('gr', f), n)


# ------------------------------------------------------------------ helpers and story
def client_margin(client_id, days=90):
    """revenue, loaded cost and margin of a client over the last `days` days, per hour and as a share of revenue"""
    rev = cost = hrs = tr = ot = 0.0
    lo = TODAY - day(days)
    for v in _W()['visits']:
        if v['_c']['client_id'] != client_id or v['status'] not in ('Completed', 'Late') or not (lo <= v['_d'] <= TODAY): continue
        rev += v['charge']; cost += v['cost']; hrs += v['billed_hours']; tr += v['travel_pay'] + v['mileage_pay']; ot += v['overtime_pay']
    return dict(revenue=R2(rev), cost=R2(cost), hours=R2(hrs), margin=R2(rev - cost), margin_pct=round((rev - cost) / rev, 4) if rev else 0.0, rate_per_hour=R2(rev / hrs) if hrs else 0.0,
                cost_per_hour=R2(cost / hrs) if hrs else 0.0, travel_cost=R2(tr), overtime_cost=R2(ot))


def caregiver_week_hours(week_iso):
    """scheduled hours of every caregiver in one week (name -> hours)"""
    out = defaultdict(float); cm = _cmap()
    for w in _W()['weeks']:
        if iso(w['week']) == week_iso: out[cm[w['gid']]['name']] += w['scheduled']
    return dict(out)


def match_score(caregiver_id, client_id):
    """base matching score of a caregiver for a client: area (0-3), language (4 when the client's language is spoken), preferred caregiver (3)"""
    g = _cmap()[caregiver_id]; c = _clmap()[client_id]; c = dict(c); c['_pref'] = _prefs().get(client_id, [])
    return R2(_match(g, c))


def story():
    """ids of the six story rows: below_cost_client, overdue_invoice (client balance unpaid 6+ weeks), overtime_caregiver, credential_caregiver, continuity_client, problem_area"""
    W = _W(); cm = _cmap(); cl = _clmap(); out = {}
    bc = next(c for c in W['cls'] if c['_special'] == 'belowcost'); m = client_margin(bc['client_id'], 90)
    out.update(below_cost_client=bc['client_id'], below_cost_name=bc['client'], below_cost_rate=m['rate_per_hour'], below_cost_cost_per_hour=m['cost_per_hour'], below_cost_margin_pct=m['margin_pct'])
    od = next(c for c in W['cls'] if c['_special'] == 'overdue')
    inv = [x for x in _accounts()['invoices'] if x['client_id'] == od['client_id'] and x['status'] == 'Unpaid']
    out.update(overdue_client_id=od['client_id'], overdue_client=od['client'], overdue_invoices=[x['invoice_id'] for x in inv], overdue_invoice=inv[0]['invoice_id'],
               overdue_balance=R2(sum(x['amount'] - x['deposit_applied'] for x in inv)), overdue_days=(TODAY - to_date(inv[0]['due_date'])).days)
    wk = W['ot_week']; hrs = caregiver_week_hours(iso(wk)); nm = max(hrs, key=hrs.get)
    out.update(overtime_caregiver=next(g['caregiver_id'] for g in W['cgs'] if g['name'] == nm), overtime_name=nm, overtime_week=iso(wk), overtime_hours=R2(hrs[nm]), overtime_line=OVERTIME_HOURS)
    u = _cred_caregiver(); cr = [x for x in credential_rows() if x['caregiver_id'] == u and x['credential'] == 'First aid course' and x['status'] == 'Valid'][0]
    nv = sum(1 for v in W['visits'] if v['actual'] == u and v['_d'] > to_date(cr['expires_on']) and v['status'] == 'Scheduled')
    out.update(credential_caregiver=u, credential_name=cm[u]['name'], credential_id=cr['credential_id'], credential_type=cr['credential'], credential_date=cr['expires_on'],
               credential_days=(to_date(cr['expires_on']) - TODAY).days, credential_visits_after=nv)
    co = next(c for c in W['cls'] if c['_special'] == 'continuity')
    cg30 = {v['actual'] for v in W['visits'] if v['_c'] is co and v['actual'] and TODAY - day(30) <= v['_d'] <= TODAY and v['status'] in ('Completed', 'Late')}
    out.update(continuity_client=co['client_id'], continuity_name=co['client'], continuity_caregivers=len(cg30))
    ar = [v for v in W['visits'] if v['_c']['area'] == 'South Valley' and TODAY - day(60) <= v['_d'] <= TODAY and v['status'] in ('Completed', 'Late', 'Missed')]
    out.update(problem_area='South Valley', problem_area_visits=len(ar), problem_area_late=sum(1 for v in ar if v['status'] == 'Late'), problem_area_missed=sum(1 for v in ar if v['status'] == 'Missed'))
    return out

_GENS = ['caregiver_rows', 'client_rows', 'availability_rows', 'time_off_rows', 'visit_rows', 'calloff_rows', 'hours_rows', 'week_rows', 'mileage_rows', 'payroll_rows', 'enquiry_rows',
         'agreement_rows', 'invoice_rows', 'payment_rows', 'deposit_rows', 'claim_rows', 'applicant_rows', 'onboarding_rows', 'credential_rows', 'expense_rows', 'pnl_rows', 'tax_rows',
         'cash_rows', 'marketing_rows', 'client_month_rows', 'service_month_rows', 'area_month_rows', 'growth_rows', 'holiday_rows']


def _digest():
    h = hashlib.md5()
    for nm in _GENS: h.update(repr(globals()[nm]()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); S = story(); G = {nm: globals()[nm]() for nm in _GENS}
    print('team', len(team), 'areas', len(areas), 'services', len(services), 'rate_card', len(rate_card), 'payers', len(payers), 'holidays', len(holidays))
    print(' '.join('%s %d' % (nm.replace('_rows', ''), len(v)) for nm, v in G.items()))
    ids = {'caregiver_rows': 'caregiver_id', 'client_rows': 'client_id', 'visit_rows': 'visit_id', 'calloff_rows': 'calloff_id', 'hours_rows': 'row_id', 'payroll_rows': 'pay_id',
           'enquiry_rows': 'enquiry_id', 'agreement_rows': 'agreement_id', 'invoice_rows': 'invoice_id', 'payment_rows': 'payment_id', 'deposit_rows': 'deposit_id', 'claim_rows': 'claim_id',
           'applicant_rows': 'applicant_id', 'onboarding_rows': 'onboarding_id', 'credential_rows': 'credential_id', 'expense_rows': 'expense_id', 'mileage_rows': 'mileage_id',
           'client_month_rows': 'row_id', 'marketing_rows': 'campaign_id', 'availability_rows': 'avail_id', 'time_off_rows': 'timeoff_id'}
    for nm, k in ids.items(): assert len({x[k] for x in G[nm]}) == len(G[nm]), nm
    assert len({c['client'] for c in G['client_rows']}) == len(G['client_rows']), 'client names unique'
    assert len({c['name'] for c in G['caregiver_rows']}) == len(G['caregiver_rows']), 'caregiver names unique'
    chk = [('client_rows', 'payer', PAYERS), ('client_rows', 'service', SERVICES), ('client_rows', 'area', AREAS), ('client_rows', 'billing_cycle', BILL_CYCLES), ('client_rows', 'status', CLIENT_STATUS),
           ('client_rows', 'end_reason', END_REASONS), ('client_rows', 'source', ENQ_SOURCES), ('caregiver_rows', 'employment', EMPLOYMENT), ('caregiver_rows', 'availability', AVAILABILITY),
           ('caregiver_rows', 'status', CAREGIVER_STATUS), ('caregiver_rows', 'area', AREAS), ('caregiver_rows', 'leave_reason', LEAVE_REASONS), ('caregiver_rows', 'source', REC_SOURCES),
           ('visit_rows', 'status', VISIT_STATUS), ('visit_rows', 'band', BANDS), ('visit_rows', 'service', SERVICES), ('visit_rows', 'cover_type', COVER_KINDS), ('visit_rows', 'area', AREAS),
           ('visit_rows', 'reason', DELAY_REASONS + MISS_REASONS), ('calloff_rows', 'reason', CALLOFF_REASONS), ('time_off_rows', 'kind', TIMEOFF_KINDS), ('enquiry_rows', 'status', ENQUIRY_STATUS),
           ('enquiry_rows', 'source', ENQ_SOURCES), ('enquiry_rows', 'loss_reason', LOSS_REASONS), ('enquiry_rows', 'service', SERVICES), ('enquiry_rows', 'area', AREAS),
           ('agreement_rows', 'kind', AGREEMENT_KINDS), ('agreement_rows', 'status', AGREEMENT_STATUS), ('invoice_rows', 'status', INVOICE_STATUS), ('invoice_rows', 'paid_by', PAID_BY),
           ('invoice_rows', 'cycle', BILL_CYCLES), ('payment_rows', 'kind', PAYMENT_KINDS), ('payment_rows', 'method', PAYMENT_METHODS), ('claim_rows', 'status', CLAIM_STATUS),
           ('claim_rows', 'reason', CLAIM_REASONS), ('claim_rows', 'payer', PAYERS[1:]), ('deposit_rows', 'kind', DEPOSIT_KINDS), ('deposit_rows', 'status', DEPOSIT_STATUS),
           ('applicant_rows', 'status', APPLICANT_STATUS), ('applicant_rows', 'source', REC_SOURCES), ('applicant_rows', 'reason', APPLICANT_REASONS), ('credential_rows', 'credential', CRED_TYPES),
           ('credential_rows', 'status', CRED_STATUS[:2]), ('payroll_rows', 'status', PAY_STATUS), ('payroll_rows', 'employment', EMPLOYMENT), ('expense_rows', 'category', EXPENSE_CATEGORIES),
           ('marketing_rows', 'kind', MARKETING_KINDS), ('tax_rows', 'status', TAX_STATUS), ('service_month_rows', 'service', SERVICES), ('area_month_rows', 'area', AREAS),
           ('hours_rows', 'employment', EMPLOYMENT), ('team', 'role', ROLES), ('team', 'team', TEAMS), ('team', 'pay_type', PAY_TYPES)]
    G['team'] = team
    for nm, col, vals in chk:
        got = {x[col] for x in G[nm]}; miss = [v for v in vals if v not in got]
        if miss: print('UNUSED', nm, col, miss)
        extra = {g for g in got if g not in vals and g != ''}; assert not extra, (nm, col, extra)
    for L in (ROLES, TEAMS, PAY_TYPES, SERVICES, BANDS, AREAS, PAYERS, BILL_CYCLES, EMPLOYMENT, CAREGIVER_STATUS, CLIENT_STATUS, AVAILABILITY, LANGUAGES, VISIT_STATUS, COVER_KINDS,
              DELAY_REASONS, MISS_REASONS, CALLOFF_REASONS, END_REASONS, ENQUIRY_STATUS, ENQ_SOURCES, LOSS_REASONS, CRED_TYPES, REC_SOURCES, APPLICANT_STATUS, LEAVE_REASONS, TIMEOFF_KINDS,
              INVOICE_STATUS, PAID_BY, PAYMENT_KINDS, CLAIM_STATUS, CLAIM_REASONS, DEPOSIT_KINDS, DEPOSIT_STATUS, PAY_STATUS, TAX_STATUS, EXPENSE_CATEGORIES, MARKETING_KINDS, APPLICANT_REASONS):
        for k, _ in pairs(L): assert len(k) <= 21, k
    ms = iso(month_start(0)); t30 = ago(30); td = iso(TODAY)
    def cur(nm, col, lo=1, t=ms): n_ = sum(1 for x in G[nm] if x[col] and t <= x[col] <= td); assert n_ >= lo, (nm, col, n_); return n_
    print('current month / last 30 days:', {(nm, col): (cur(nm, col), cur(nm, col, t=t30)) for nm, col in
          [('visit_rows', 'date'), ('enquiry_rows', 'received_on'), ('invoice_rows', 'issued_on'), ('payment_rows', 'date'), ('claim_rows', 'submitted_on'), ('expense_rows', 'date'), ('applicant_rows', 'applied_on'),
           ('calloff_rows', 'date'), ('caregiver_rows', 'hire_date'), ('caregiver_rows', 'left_date'), ('client_rows', 'start_date'), ('client_rows', 'end_date'), ('agreement_rows', 'signed_on')]})
    assert all(x['date'] <= td or x['status'] in ('Scheduled', 'Open') for x in G['visit_rows'])
    cmm = [x for x in G['claim_rows'] if x['paid_on']]; print('claims paid this month', sum(1 for x in cmm if x['paid_on'] >= ms))
    act = [c for c in G['client_rows'] if c['status'] == 'Active']; print('active clients', len(act), 'weekly hours', sum(c['weekly_hours'] for c in act), 'active caregivers', sum(1 for c in G['caregiver_rows'] if c['status'] != 'Left'))
    ls = [x for x in G['visit_rows'] if x['date'] >= ago(30) and x['status'] in ('Late', 'Completed', 'Missed')]
    print('late share 30d', round(sum(1 for x in ls if x['status'] == 'Late') / len(ls), 3), 'missed share', round(sum(1 for x in ls if x['status'] == 'Missed') / len(ls), 3))
    print('story', S); print('digest', _digest(), 'seconds', round(time.time() - t0, 1))
